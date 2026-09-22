from collections import defaultdict
from .services.reports import AGING_TONES, BUCKET_TONES
from decimal import Decimal
import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_GET
from core.mixins import user_has_role_permission as has

from .access import can_sync, can_view_all, check_access, scoped, can_edit, _allowed_sif_pos_from_user, _allowed_centers_from_user
from .models import (BalanceSnapshot, CollectionState, CollectionSyncRun, FinancePartnerIdentity,
                     CollectionContact, CollectionActivity, CollectionNotice, SourceRow,
                     ReceivablePosting, ReceivablePosition, CollectionLegalCase, ImportIssue)
from .services.source import day, integer, money, text
from .services.sync import bucket, sync_collections
from .services.partner_detail import INVOICE_BUCKETS, BUCKET_LABELS, basic_fields, invoice_groups

logger = logging.getLogger(__name__)

TABLES = {
    "partners": ("Partner", "Šifra", "Oznake", "Nedospelo / bez datuma", "1–30 dana", "31–45 dana", "46–60 dana", "61–90 dana", "91–180 dana", "Preko 180 dana", "Dospelo", "Ukupno · RSD"),
    "positions": ("Partner", "Šifra posla", "Centar", "Dokument", "Konto", "Dospeće", "Kašnjenje / dani", "Duguje", "Potražuje", "Saldo · RSD"),
    "postings": ("Partner", "Šifra posla", "Konto", "Godina", "Vrsta", "Nalog", "Stavka", "Knjiženje", "Dokument", "Duguje", "Potražuje", "Saldo · RSD"),
    "ispravke": ("Partner", "Šifra posla", "Konto", "Godina", "Vrsta", "Nalog", "Stavka", "Knjiženje", "Dokument", "Duguje", "Potražuje", "Saldo · RSD"),
    "sef": ("Partner", "Godina", "Faktura", "Datum", "Status", "Vreme statusa", "Komentar"),
    "cases": ("Partner", "Godina", "Konto", "Naziv konta", "Datum", "Duguju", "Platili", "Saldo · RSD"),
    "contacts": ("Partner", "Ime i prezime / odeljenje", "Telefon", "E-pošta", "Napomena", "Stanje", "Radnje"),
    "activities": ("Partner", "Vrsta", "Datum", "Sadržaj", "Ishod", "Sledeći kontakt", "Stanje", "Radnje"),
    "notices": ("Partner", "Vrsta", "Godina", "Broj", "Datum", "Iznos", "Valuta", "Fakture", "Napomena", "Stanje", "Radnje"),
    "legal": ("Partner", "Vrsta postupka", "Predmet", "Sud", "Osnovni dug", "Valuta", "Stanje", "Radnje"),
    "directory": ("Partner", "Šifra", "PIB", "Mesto"),
}
TABLES['review'] = TABLES['partners']
TABLES['jobs'] = TABLES['partners']
TABLES['debts'] = ('Godina', 'OJ', 'Šifra posla', 'Vrsta', 'Datum', 'Veza', 'DPO', 'Valuta', 'Duguje', 'Potražuje')
TABLES['buckets'] = ('Opis', 'Baketi', 'Šifra posla', 'Veza', 'DPO', 'Duguje', 'Potražuje', 'Saldo', 'Akcija')
for code, title in INVOICE_BUCKETS:
    TABLES[f'invoices_{code}'] = ('Šifra partnera', 'Naziv', 'Veza', 'Šifra posla', 'Duguje', 'Potražuje', 'Saldo')
LABELS = {"partners": "Dugovanja po partnerima", "positions": "Otvorene stavke / šifre posla", "postings": "Knjiženja",
          "ispravke": "Ispravke vrednosti", "sef": "Neodobrene e-fakture", "cases": "Utužena potraživanja",
          "contacts": "Kontakti", "activities": "Napomene i pozivi", "notices": "Opomene i pisma",
          "review": "Spisak za proveru", "jobs": "Izveštaj po šiframa posla", "directory": "Svi partneri", "legal": "Utuženi klijenti / pravni postupci"}
LABELS.update(debts='Dugovanja', buckets='Dugovanja - Baketi')
LABELS.update({f'invoices_{code}': title for code, title in INVOICE_BUCKETS})
OPERATIONS = ('contacts', 'activities', 'notices', 'legal', 'directory')
SPLIT_OPERATIONS = {
    'calls': ('activities', 'phone', 'Telefonski pozivi'),
    'notes': ('activities', 'note', 'Napomene'),
    'reminders': ('notices', 'reminder', 'Opomene'),
    'letters': ('notices', 'letter', 'Pisma'),
    'claims': ('notices', 'legacy_claim', 'Evidencija tužbi'),
}
for key, (base_kind, record_type, title) in SPLIT_OPERATIONS.items():
    TABLES[key] = TABLES[base_kind]
    LABELS[key] = title
OPERATIONS += tuple(SPLIT_OPERATIONS)


def current_snapshot(request):
    raw = request.GET.get("snapshot")
    if raw:
        try:
            pk = int(raw)
        except ValueError:
            raise PermissionDenied("Neispravan snimak.")
        return get_object_or_404(BalanceSnapshot.objects.select_related("run"), pk=pk, status="published", company=1)
    state = CollectionState.objects.select_related("current_snapshot__run").filter(company=1).first()
    return state.current_snapshot if state else None


def context(request, snapshot):
    request.session["current_app"] = "potrazivanja"
    all_access = can_view_all(request.user)
    centers = []
    if snapshot:
        centers = sorted(set(scoped(snapshot.positions.all(), request.user).exclude(center_code="").values_list("center_code", flat=True)))
    return {"snapshot": snapshot, "can_sync": can_sync(request.user), "all_access": all_access,
            "centers": centers, "selected_center": request.GET.get("center", ""),
            "selected_job": request.GET.get("job", ""),
            "write_rights": {kind: can_edit(request.user, kind, 'create') for kind in ('contact', 'activity', 'notice', 'legal')},
            "can_review": can_edit(request.user, 'review'),
            "can_export": has(request.user, 'potrazivanja:export'),
            "can_import": has(request.user, 'potrazivanja:notice_import') and can_edit(request.user, 'notice', 'create'),
            "tables": TABLES, "labels": LABELS, "section": "overview"}


def filtered_positions(request, snapshot):
    qs = scoped(snapshot.positions.all() if snapshot else ReceivablePosition.objects.none(), request.user)
    center = request.GET.get("center", "").strip()
    if center:
        qs = qs.filter(center_code=center)
    if request.GET.get('job'):
        qs = qs.filter(job_code=request.GET['job'].strip())
    if request.GET.get('view', request.GET.get('kind')) == 'review':
        qs = qs.filter(identity__collection_profile__needs_review=True)
    if request.GET.get("partner"):
        try:
            qs = qs.filter(identity_id=int(request.GET["partner"]))
        except ValueError:
            raise PermissionDenied("Neispravan partner.")
    return qs


@never_cache
@require_GET
def dashboard(request):
    check_access(request.user)
    snapshot = current_snapshot(request)
    ctx = context(request, snapshot)
    kind = request.GET.get("view", "partners")
    if kind == 'notices':
        kind = {'letter':'letters', 'legacy_claim':'claims'}.get(request.GET.get('type'), 'reminders')
    elif kind == 'activities':
        kind = 'notes' if request.GET.get('type') == 'note' else 'calls'
    if kind not in TABLES or (kind in ("sef", "cases", "review") + OPERATIONS and not ctx["all_access"]):
        raise PermissionDenied("Ovaj izveštaj zahteva pristup svim partnerima.")
    totals = defaultdict(Decimal)
    partners = set()
    if snapshot and kind in ('partners', 'positions', 'review', 'jobs'):
        for row in filtered_positions(request, snapshot).values("identity_id", "balance", "due_date"):
            totals["balance"] += row["balance"]
            partners.add(row["identity_id"])
            if row["due_date"] is None:
                totals["unknown"] += row["balance"]
            elif row["due_date"] < snapshot.as_of_date:
                totals["overdue"] += row["balance"]
            else:
                totals["not_due"] += row["balance"]
    list_entity = SPLIT_OPERATIONS[kind][0] if kind in SPLIT_OPERATIONS else kind
    ctx.update(kind=kind, list_entity=list_entity, columns=TABLES[kind], title=LABELS[kind], section=list_entity, totals=dict(totals), partner_count=len(partners))
    if kind in ('partners', 'jobs', 'review'):
        ctx['legacy_partner_rows'] = [
            {'code': row[1]['sort'], 'name': row[0]['display'], 'url': row[0]['url'],
             'amounts': [Decimal(item['sort']) for item in row[3:]],
             'important': row[2]['important'], 'foreign': row[2]['foreign'],
             'review': row[2].get('review')}
            for row in rows_for(request, snapshot, kind)
        ]
    return render(request, "potrazivanja/dashboard.html", ctx)


@never_cache
@require_GET
def partner_detail(request, pk):
    check_access(request.user)
    snapshot = current_snapshot(request)
    partner = get_object_or_404(FinancePartnerIdentity, pk=pk, company=1, partner_group=1)
    if not can_view_all(request.user) and (not snapshot or not scoped(snapshot.positions.filter(identity=partner), request.user).exists()):
        raise PermissionDenied("Partner nije u dodeljenom obuhvatu.")
    ctx = context(request, snapshot)
    kinds = ['basic']
    if ctx["all_access"]:
        kinds += ['contacts', 'notes', 'reminders', 'calls', 'letters', 'claims']
    kinds += ['debts', 'buckets', 'invoices', 'ispravke', 'positions', 'postings']
    if ctx['all_access']:
        kinds += ['sef', 'cases', 'legal']
    tab_labels = {'basic': 'Osnovni podaci', 'invoices': 'Dugovanja po fakturama',
                  'calls': 'Pozivi', 'letters': 'Pozivi/pisma', 'claims': 'Tužbe',
                  'positions': 'Stavke po poslovima', 'ispravke': 'Otpisana potraživanja',
                  'sef': 'Neodobrene IF', 'cases': 'Utužene stavke', 'legal': 'Pravni postupci'}
    raw_partner = {}
    if snapshot:
        for raw in dataset_rows(snapshot, 'partneri').filter(partner_code=partner.partner_code).values_list('raw_data', flat=True):
            if integer(raw.get('sif_pred')) == partner.company and integer(raw.get('grupa')) == partner.partner_group:
                raw_partner = raw
                break
    ctx.update(partner=partner, title=partner.source_name, section='partners',
               basic_fields=basic_fields(partner, raw_partner),
               invoice_tables=[{'kind': f'invoices_{code}', 'title': title, 'columns': TABLES[f'invoices_{code}']}
                               for code, title in INVOICE_BUCKETS],
               tabs=[{'kind': k, 'title': tab_labels.get(k, LABELS.get(k)), 'columns': TABLES.get(k)} for k in kinds])
    return render(request, "potrazivanja/partner.html", ctx)


def cell(value, kind="text", url=None):
    if value is None:
        return {"display": "—", "sort": "", "kind": kind}
    if kind == "money":
        value = money(value)
        return {"display": f"{value:,.2f}", "sort": str(value), "kind": kind}
    if kind == "date":
        parsed = day(value)
        return {"display": parsed.strftime("%d.%m.%Y.") if parsed else "—", "sort": str(parsed or ""), "kind": kind}
    return {"display": str(value), "sort": value, "kind": kind, "url": url}


def partner_cell(identity, snapshot):
    return cell(f"{identity.source_name or 'Partner'}", url=reverse("potrazivanja:partner_detail", args=[identity.pk]) + (f"?snapshot={snapshot.pk}" if snapshot else ''))


def dataset_rows(snapshot, code):
    step = snapshot.run.steps.filter(code=code).only("details").first()
    return SourceRow.objects.filter(dataset_id=step.details["dataset_id"]) if step else SourceRow.objects.none()


def job_centers(snapshot):
    return {text(r["sif_pos"]): text(r.get("blok")) for r in dataset_rows(snapshot, "posao").values_list("raw_data", flat=True)}


def rows_for(request, snapshot, kind):
    if kind in OPERATIONS:
        from .views_operations import operational_rows
        return operational_rows(request, snapshot, kind)
    if not snapshot:
        return []
    qs = filtered_positions(request, snapshot).select_related("identity", "identity__collection_profile").only(
        "snapshot_id", "identity_id", "account_family", "due_date", "balance", "job_code", "center_code", "reference", "debit", "credit",
        "identity__id", "identity__source_name", "identity__partner_code",
        "identity__collection_profile__id", "identity__collection_profile__important_customer", "identity__collection_profile__needs_review", "identity__collection_profile__updated_at")
    partner_id = request.GET.get("partner")
    if partner_id:
        partner_id = int(partner_id)
        if not can_view_all(request.user) and not qs.exists():
            raise PermissionDenied("Partner nije u dodeljenom obuhvatu.")
    if kind in ('partners', 'review', 'jobs'):
        if kind == 'review' and not can_view_all(request.user):
            raise PermissionDenied
        may_review = can_edit(request.user, 'review')
        groups = {}
        for p in qs:
            key = (p.identity_id, p.account_family)
            group = groups.setdefault(key, {"identity": p.identity, "amounts": defaultdict(Decimal)})
            group["amounts"][bucket(p.due_date, snapshot.as_of_date)] += p.balance
        if kind == 'review' and not request.GET.get('center') and not request.GET.get('job'):
            marked = FinancePartnerIdentity.objects.filter(company=1, partner_group=1, collection_profile__needs_review=True).exclude(
                pk__in=[key[0] for key in groups]).select_related('collection_profile')
            if partner_id: marked = marked.filter(pk=partner_id)
            for identity in marked:
                groups[(identity.pk, '')] = {'identity':identity, 'amounts':defaultdict(Decimal)}
        rows = []
        for (_, family), group in groups.items():
            identity, amounts = group["identity"], group["amounts"]
            profile = getattr(identity, "collection_profile", None)
            flags = ["Domaći" if family == "204" else "Inostrani" if family == "205" else "Bez otvorenih stavki"]
            if profile and profile.important_customer:
                flags.append("Važan kupac")
            if profile and profile.needs_review:
                flags.append("Za proveru")
            values = [amounts[b] for b in ("0.1", "30", "45", "60", "90", "180", "181")]
            flags_cell = cell(" · ".join(flags))
            flags_cell.update(important=bool(profile and profile.important_customer), foreign=family == '205')
            if may_review:
                flags_cell['review'] = {'url': reverse('potrazivanja:review_toggle', args=[identity.pk]),
                    'checked': bool(profile and profile.needs_review), 'version': profile.updated_at.isoformat() if profile else ''}
            rows.append([partner_cell(identity, snapshot), cell(identity.partner_code), flags_cell]
                        + [dict(cell(v, "money"), tone=tone) for v, tone in
                           zip(values + [sum(values[1:]), sum(values)], AGING_TONES)])
        return rows
    if kind == "positions":
        return [[partner_cell(p.identity, snapshot), cell(p.job_code), cell(p.center_code or "Neraspoređeno"),
                 cell(p.reference), cell(p.account_family), cell(p.due_date, "date"),
                 cell((snapshot.as_of_date-p.due_date).days if p.due_date else None),
                 cell(p.debit, "money"), cell(p.credit, "money"),
                 dict(cell(p.balance, "money"), tone=BUCKET_TONES[bucket(p.due_date, snapshot.as_of_date)])] for p in qs]
    if kind == 'buckets':
        rules = {Decimal(str(r['baket'])): r for r in dataset_rows(snapshot, 'sif_baket').values_list('raw_data', flat=True)}
        result = []
        for p in qs:
            code = bucket(p.due_date, snapshot.as_of_date)
            rule = rules.get(Decimal(code), {})
            result.append([cell(rule.get('opis') or BUCKET_LABELS[code]), dict(cell(code), sort=float(code)),
                           cell(p.job_code), cell(p.reference), cell(p.due_date, 'date'),
                           cell(p.debit, 'money'), cell(p.credit, 'money'),
                           dict(cell(p.balance, 'money'), tone=BUCKET_TONES[code]), cell(rule.get('akcija'))])
        return result
    if kind.startswith('invoices_'):
        return [[cell(group['identity'].partner_code), partner_cell(group['identity'], snapshot),
                 cell(group['reference']), cell(group['job_code'])]
                + [cell(group['amounts'][field], 'money') for field in ('debit', 'credit', 'balance')]
                for group in invoice_groups(qs, snapshot.as_of_date, kind.removeprefix('invoices_'))]
    selected_code = None
    selected = None
    if partner_id and kind in ("debts", "postings", "ispravke", "sef", "cases"):
        selected = get_object_or_404(FinancePartnerIdentity.objects.only("id", "source_name", "partner_code"), pk=partner_id, company=1, partner_group=1)
        selected_code = selected.partner_code
    if kind in ("debts", "postings", "ispravke", "sef", "cases"):
        table = {"debts": "baza", "postings": "baza", "ispravke": "ispravke", "sef": "v_neodobreneIF", "cases": "v_tuzeni"}[kind]
        records = dataset_rows(snapshot, table)
        if selected_code is not None:
            records = records.filter(partner_code=selected_code)
        if not can_view_all(request.user):
            if kind in ("sef", "cases"):
                raise PermissionDenied("Izveštaj nema raspodelu po šiframa posla.")
            allowed_centers = set(_allowed_centers_from_user(request.user))
            jobs = set(_allowed_sif_pos_from_user(request.user))
            jobs.update(code for code, center in job_centers(snapshot).items() if center in allowed_centers)
            records = records.filter(job_code__in=jobs)
        if request.GET.get("center"):
            jobs = [code for code, center in job_centers(snapshot).items() if center == request.GET["center"]]
            records = records.filter(job_code__in=jobs)
        if request.GET.get('job'):
            records = records.filter(job_code=request.GET['job'].strip())
        # Resolve only partners actually present in this local capture. In a partner
        # detail, reuse the selected identity; never fetch the entire directory per tab.
        identities = {selected.partner_code: selected} if selected else {
            i.partner_code: i for i in FinancePartnerIdentity.objects.filter(
                company=1, partner_group=1, partner_code__in=records.order_by().values("partner_code")
            ).only("id", "source_name", "partner_code")
        }
        result = []
        for partner_code, r in records.values_list("partner_code", "raw_data"):
            identity = identities.get(partner_code)
            label = partner_cell(identity, snapshot) if identity else cell(text(r.get("naz_par", r.get("naziv partnera"))))
            if kind == 'debts':
                result.append([cell(integer(r.get('god'))), cell(r.get('oj')), cell(r.get('sif_pos')),
                               cell(r.get('sif_vrs')), cell(r.get('datum'), 'date'), cell(r.get('vez_dok')),
                               cell(r.get('dpo'), 'date'), cell(r.get('skr_naz')),
                               cell(r.get('dug'), 'money'), cell(r.get('pot'), 'money')])
            elif kind in ("postings", "ispravke"):
                result.append([label, cell(r.get("sif_pos")), cell(r.get("knt")), cell(integer(r.get("god"))),
                    cell(r.get("sif_vrs")), cell(r.get("br_naloga")), cell(r.get("stavka")), cell(r.get("dat_naloga"), "date"),
                    cell(r.get("vez_dok")), cell(r.get("dug"), "money"), cell(r.get("pot"), "money"), cell(money(r.get("dug"))-money(r.get("pot")), "money")])
            elif kind == "sef":
                result.append([label, cell(integer(r.get("god"))), cell(r.get("faktura")), cell(r.get("datum"), "date"),
                               cell(r.get("status na sefu")), cell(r.get("vreme statusa")), cell(r.get("komentar"))])
            else:
                result.append([label, cell(integer(r.get("god"))), cell(r.get("knt")), cell(r.get("naz_knt")),
                    cell(r.get("datum"), "date"), cell(r.get("duguju"), "money"), cell(r.get("platili"), "money"),
                    cell(money(r.get("duguju"))-money(r.get("platili")), "money")])
        return result
    return []


@never_cache
@require_GET
def table_data(request):
    check_access(request.user)
    kind = request.GET.get("kind", "partners")
    if kind not in TABLES:
        return JsonResponse({"error": "Nepoznata tabela."}, status=400)
    try:
        draw = max(0, int(request.GET.get("draw", 0)))
        start = max(0, int(request.GET.get("start", 0)))
        length = min(500, max(1, int(request.GET.get("length", 100))))
        column = int(request.GET.get("order[0][column]", len(TABLES[kind])-1))
        if not 0 <= column < len(TABLES[kind]):
            raise ValueError
        if request.GET.get("partner"):
            int(request.GET["partner"])
    except ValueError:
        return JsonResponse({"error": "Neispravni parametri tabele."}, status=400)
    snapshot = current_snapshot(request)
    rows = rows_for(request, snapshot, kind)
    total = len(rows)
    search = request.GET.get("search[value]", "").casefold()
    if search:
        rows = [r for r in rows if any(search in str(c["display"]).casefold() for c in r)]
    def order(row):
        if row[column]["kind"] == "money" and row[column]["sort"] != "":
            return (1, Decimal(row[column]["sort"]))
        value = row[column]["sort"]
        return (0, "") if value is None or value == "" else ((1, value) if isinstance(value, (int, float)) else (2, str(value).casefold()))
    rows.sort(key=order, reverse=request.GET.get("order[0][dir]", "desc") == "desc")
    return JsonResponse({"draw": draw, "recordsTotal": total, "recordsFiltered": len(rows), "data": rows[start:start+length]})


@never_cache
@require_http_methods(["GET", "POST"])
def sync_status(request):
    check_access(request.user)
    if not can_sync(request.user):
        raise PermissionDenied("Nemate dozvolu za sinhronizaciju.")
    if request.method == "POST":
        try:
            run = sync_collections(requested_by=request.user)
            messages.success(request, f"Sinhronizacija #{run.pk} završena. Kontrole salda i dospeća su prošle.")
        except Exception:
            logger.exception("Manual collections sync failed")
            messages.error(request, "Sinhronizacija nije objavljena. Prethodno stanje je sačuvano; pogledajte zapis pokretanja.")
        return redirect("potrazivanja:sync_status")
    ctx = context(request, current_snapshot(request))
    latest = CollectionSyncRun.objects.filter(status="success").first()
    legacy = CollectionSyncRun.objects.filter(status='success', steps__code='kontakti').order_by('-pk').first()
    ctx.update(section="sync", runs=CollectionSyncRun.objects.all()[:30],
               controls=latest.control_totals if latest else {},
               steps=latest.steps.all() if latest else [],
               issues=ImportIssue.objects.filter(run_id__in={x.pk for x in (latest, legacy) if x}).order_by("source_table", "pk"))
    return render(request, "potrazivanja/sync.html", ctx)
