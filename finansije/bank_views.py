import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.mixins import role_permission_required, user_has_role_permission
from menice.models import Menica
from .access import can_view_all
from .bank_forms import BankPeriodForm, BankContactForm, BankAccountRuleForm, BankBillPlacementForm, BankaPartnerForm
from .models import BankaPartner, BankContact, BankAccountRule, BankBillPlacement, BankePreuzimanje, SyncRun
from .services import banke_nbs
from .services import banks as service

logger = logging.getLogger(__name__)
TABS = [("basic", "Osnovni podaci"), ("nbs", "Podaci sa NBS"), ("group", "Grupa i povezana lica"),
        ("contacts", "Kontakti"), ("turnover", "Promet po računima"),
        ("bills", "Menice"), ("guarantees", "Garancije"), ("deposits", "Oročena sredstva")]


def context_for(request):
    request.session["current_app"] = "finansije"
    form = BankPeriodForm(request.GET)
    # Sinhronizacija ide svakog sata (hiljade zapisa sa velikim JSON zbirovima) — ne učitavati ih cele.
    successful = SyncRun.objects.filter(company=service.company_id(), status="success")
    context = dict(form=form, valid=form.is_valid(), restricted=not can_view_all(request.user),
                   last_success=successful.only("finished_at", "latest_booking_date", "started_at").first())
    context["can_map"] = can_view_all(request.user) and user_has_role_permission(request.user, "finansije:bank_accounts")
    try:
        banks = service.fetch_banks(service.company_id())
    except (DatabaseError, ValueError):
        logger.exception("Bank partner source unavailable")
        context["source_error"] = "Šifarnik banaka trenutno nije dostupan. Pokušajte ponovo."
        banks = []
    context["source_banks"] = banke_nbs.razvrstaj(banks)
    context["can_bank_refresh"] = can_view_all(request.user) and user_has_role_permission(request.user, "finansije:bank_refresh")
    context["can_market"] = user_has_role_permission(request.user, "finansije:bank_market")
    context["last_runs"] = [run for run in (BankePreuzimanje.objects.filter(izvor=izvor).exclude(status="running").first()
                                            for izvor, _ in BankePreuzimanje.IZVORI) if run]
    if context["valid"]:
        context["period_params"] = urlencode({key: form.cleaned_data[key].isoformat() for key in ("date_from", "date_to")})
        year = form.cleaned_data["date_from"].year
        context["period_missing"] = not successful.filter(year_from__lte=year, year_to__gte=year).exists()
    return context


def find_bank(context, bank_code):
    if context.get("source_error"):
        return None
    return next((b for b in context["source_banks"] if b["code"] == bank_code), None)


def edit_access(request):
    if not can_view_all(request.user):
        raise PermissionDenied("Održavanje bankarskih podataka zahteva pristup celoj firmi.")


def bank_redirect(bank_code, tab):
    return redirect(reverse("finansije:bank_detail", args=[bank_code]) + "?tab=" + tab)


@require_GET
@login_required
@role_permission_required()
def bank_list(request):
    context = context_for(request)
    if context["valid"] and not context.get("source_error"):
        context.update(service.report_for(request.user, context["source_banks"], context["form"].cleaned_data["date_from"], context["form"].cleaned_data["date_to"]))
        context.update(razvrstane_banke(context["banks"]))
    # Najnovije promene svakog izvora (šifarnik, NBS), za proveru.
    context["change_runs"] = [run for run in (next((r for r in BankePreuzimanje.objects.filter(izvor=izvor, status="success")[:20] if r.promene), None)
                                              for izvor, _ in BankePreuzimanje.IZVORI) if run]
    return render(request, "finansije/banks/list.html", context)


def razvrstane_banke(banks):
    """Banke po grupama; istorijske i partneri koji nisu banke posebno.

    Ručni status (`BankaPartner.status`) ima prednost. Bez njega: banka sa spiska NBS je aktivna;
    ostali partneri grupe 11 su istorijski ako nemaju ni stanja ni prometa u godini ili su obrisani
    u šifarniku, a inače „nije banka sa spiska NBS” (npr. Uprava za trezor).
    """
    grupe, van_nbs = {}, []
    for bank in banks:
        status = bank.get("status") or ""
        if status == "aktivna" or (not status and not bank["van_nbs"] and bank.get("u_izvoru", True)):
            grupa = bank["grupa"]
            kljuc = grupa.naziv if grupa else "Bez grupe"
            stavka = grupe.setdefault(kljuc, dict(naziv=kljuc, maticna=grupa.maticna_grupa if grupa else "", banke=[]))
            stavka["banke"].append(bank)
            continue
        totals = bank["totals"]
        bez_prometa = not (totals["count"] or totals["opening"] or totals["balance"])
        bank["istorijska"] = status == "istorijska" or (not status and (bez_prometa or not bank.get("u_izvoru", True)
                                                                         or bool(bank["nbs"] and not bank["nbs"].aktivna)))
        bank["nije_banka"] = status == "nije_banka"
        van_nbs.append(bank)
    poredak = sorted(grupe.values(), key=lambda g: (g["naziv"] == "Bez grupe", g["naziv"].lower()))
    for grupa in poredak:
        # Dodatna šifra (npr. račun za bolovanja) odmah ispod glavne šifre iste banke.
        grupa["banke"].sort(key=lambda b: ((b["nbs"].naziv if b["nbs"] else b["name"]).lower(), b.get("glavna_code") or b["code"],
                                           b.get("glavna_code") is not None, b["code"]))
    van_nbs.sort(key=lambda b: (b["istorijska"], b["name"].lower()))
    return dict(bank_groups=poredak, outside_nbs=van_nbs)


@require_GET
@login_required
@role_permission_required()
def bank_market(request):
    """Banke u Srbiji: sve banke sa spiska NBS i sve grupe sa povezanim licima; otvara se sa ekrana Banke."""
    from .services import banke_trziste, izvoz

    context = context_for(request)
    # Promet sa grupama samo uz pristup celoj firmi — delimičan obuhvat bi potcenio saradnju.
    sa_prometom = context["valid"] and can_view_all(request.user)
    start, end = (context["form"].cleaned_data["date_from"], context["form"].cleaned_data["date_to"]) if sa_prometom else (None, None)
    podaci = banke_trziste.pregled(context["source_banks"], request.user, start, end)
    if request.GET.get("izvoz") == "xlsx":
        period = izvoz.period_tekst(start, end) + " (promet sa grupama)" if sa_prometom else ""
        return izvoz.excel_odgovor(banke_trziste.dokument(podaci, sa_prometom, period), "banke_u_srbiji")
    context.update(podaci, sa_prometom=sa_prometom)
    return render(request, "finansije/banks/market.html", context)


@require_POST
@login_required
@role_permission_required()
def bank_refresh(request):
    """Šifarnik partnera (Stankov program), pa podaci sa NBS — isto kao noćni i mesečni posao."""
    edit_access(request)
    for osvezi in (banke_nbs.sinhronizuj_sifarnik, banke_nbs.osvezi):
        try:
            run = osvezi("manual", request.user)
        except banke_nbs.PreuzimanjeUToku as exc:
            messages.warning(request, str(exc))
        else:
            (messages.success if run.status == "success" else messages.error)(request, banke_nbs.poruka(run))
    nazad = request.POST.get("next", "")
    return redirect(nazad if nazad.startswith("/finansije/banke/") else reverse("finansije:bank_list"))


@require_POST
@login_required
@role_permission_required()
def bank_partner_edit(request, bank_code):
    """Naše oznake šifre banke: status, namena i glavna šifra; podaci partnera ostaju iz šifarnika."""
    edit_access(request)
    zapis = get_object_or_404(BankaPartner, company=service.company_id(), sifra=bank_code)
    form = BankaPartnerForm(request.POST, instance=zapis)
    if form.is_valid():
        zapis = form.save(commit=False)
        zapis.izmenio, zapis.izmenjeno = request.user, timezone.now()
        zapis.save()
        messages.success(request, "Oznake banke su sačuvane.")
    else:
        messages.error(request, "Oznake nisu sačuvane: " + " ".join(e for errors in form.errors.values() for e in errors))
    return bank_redirect(bank_code, "basic")


@require_GET
@login_required
@role_permission_required()
def bank_detail(request, bank_code):
    context = context_for(request)
    bank = find_bank(context, bank_code)
    if not bank:
        if context.get("source_error"):
            return render(request, "finansije/banks/list.html", context, status=503)
        raise Http404("Partner nije banka grupe 11.")
    tab = request.GET.get("tab", "basic")
    if tab not in dict(TABS):
        raise Http404("Nepostojeća kartica.")
    context.update(bank=bank, tab=tab, tabs=[dict(code=code, label=label) for code, label in TABS])
    context["can_contact_edit"] = can_view_all(request.user) and user_has_role_permission(request.user, "finansije:bank_contact_edit")
    context["can_contact_delete"] = can_view_all(request.user) and user_has_role_permission(request.user, "finansije:bank_contact_delete")
    if tab == "contacts":
        context["contacts"] = BankContact.objects.filter(company=service.company_id(), bank_code=bank_code)
    if tab == "basic" and bank.get("zapis"):
        context["can_partner_edit"] = can_view_all(request.user) and user_has_role_permission(request.user, "finansije:bank_partner_edit")
        context["partner_form"] = BankaPartnerForm(instance=bank.get("zapis"))
        context["related_codes"] = [b for b in context["source_banks"] if b.get("glavna_code") == bank_code]
    if tab == "nbs":
        context["differences"] = banke_nbs.razlike(bank)
    if tab == "group" and bank["grupa"]:
        context["group_banks"] = [b for b in context["source_banks"] if b["grupa"] == bank["grupa"]]
        if context["valid"]:
            try:
                context["group_members"] = banke_nbs.lica_grupe(request.user, bank["grupa"], context["form"].cleaned_data["date_from"],
                                                                 context["form"].cleaned_data["date_to"])
            except DatabaseError:
                logger.exception("Partneri povezanih lica nisu dostupni")
                context["source_error"] = "Šifarnik partnera trenutno nije dostupan. Pokušajte ponovo."
    if tab in ("turnover", "guarantees", "deposits") and context["valid"]:
        report = service.report_for(request.user, context["source_banks"], context["form"].cleaned_data["date_from"], context["form"].cleaned_data["date_to"])
        selected = next(row for row in report["banks"] if row["code"] == bank_code)
        segments = {"dinar", "foreign", "other"} if tab == "turnover" else {"guarantee"} if tab == "guarantees" else {"deposit"}
        context.update(accounts=[row for row in selected["accounts"] if row["segment"] in segments],
                       ytd_end=report["ytd_end"], unresolved_count=len(report["unmapped"]))
    if tab == "bills":
        context["can_view_bills"] = can_view_all(request.user) and user_has_role_permission(request.user, "menice:menica_list")
        context["can_view_incoming"] = can_view_all(request.user) and user_has_role_permission(request.user, "menice:ulazna_menica_list")
        context["can_bill_edit"] = (context["can_view_bills"] and context["can_view_incoming"] and
                                    user_has_role_permission(request.user, "finansije:bank_bill_edit"))
        placements = BankBillPlacement.objects.filter(company=service.company_id(), bank_code=bank_code).select_related("bill", "incoming_bill")
        if not context["can_view_bills"]:
            placements = placements.filter(bill__isnull=True)
        if not context["can_view_incoming"]:
            placements = placements.filter(incoming_bill__isnull=True)
        context["placements"] = placements
        # Registration is shown separately; it is never inferred to be physical custody.
        if context["can_view_bills"]:
            context["registered_bills"] = Menica.objects.filter(naziv_banke__iexact=bank["name"])
    return render(request, "finansije/banks/detail.html", context)


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def bank_contact_edit(request, bank_code, pk=None):
    edit_access(request)
    context = context_for(request)
    bank = find_bank(context, bank_code)
    if not bank:
        if context.get("source_error"):
            return render(request, "finansije/banks/list.html", context, status=503)
        raise Http404
    instance = get_object_or_404(BankContact, pk=pk, company=service.company_id(), bank_code=bank_code) if pk else BankContact(company=service.company_id(), bank_code=bank_code)
    form = BankContactForm(request.POST if request.method == "POST" else None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Kontakt je sačuvan.")
        return bank_redirect(bank_code, "contacts")
    context.update(bank=bank, edit_form=form, edit_title="Kontakt banke", cancel_url=reverse("finansije:bank_detail", args=[bank_code]) + "?tab=contacts")
    return render(request, "finansije/banks/form.html", context)


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def bank_contact_delete(request, bank_code, pk):
    edit_access(request)
    contact = get_object_or_404(BankContact, pk=pk, company=service.company_id(), bank_code=bank_code)
    if request.method == "POST":
        contact.delete()
        messages.success(request, "Kontakt je obrisan.")
        return bank_redirect(bank_code, "contacts")
    request.session["current_app"] = "finansije"
    return render(request, "finansije/banks/form.html", dict(edit_title="Brisanje kontakta", delete_label=f"{contact.segment} — {contact.name or contact.shared_emails}",
        cancel_url=reverse("finansije:bank_detail", args=[bank_code]) + "?tab=contacts"))


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def bank_accounts(request):
    edit_access(request)
    context = context_for(request)
    if context.get("source_error"):
        return render(request, "finansije/banks/list.html", context, status=503)
    catalog = service.account_catalog()
    # One current label per account; historical names must not duplicate choices.
    catalog = list(dict(catalog).items())
    code = request.POST.get("account") if request.method == "POST" else request.GET.get("account")
    instance = BankAccountRule.objects.filter(company=service.company_id(), account=code).first() or BankAccountRule(company=service.company_id())
    name = dict(catalog).get(code, "")
    initial = {"account": code, "segment": service.suggested_segment(code or "", name), "bank_code": service.suggested_bank(name, context["source_banks"])} if not instance.pk else None
    form = BankAccountRuleForm(request.POST if request.method == "POST" else None, instance=instance, initial=initial, banks=context["source_banks"], accounts=catalog)
    if request.method == "POST" and form.is_valid():
        rule = form.save(commit=False)
        rule.updated_by = request.user
        rule.save()
        messages.success(request, "Veza konta je sačuvana.")
        return redirect("finansije:bank_accounts")
    saved = {r.account: r for r in BankAccountRule.objects.filter(company=service.company_id())}
    names = {b["code"]: b["name"] for b in context["source_banks"]}
    rows, values = [], {}
    for c, n in catalog:
        rule = saved.get(c)
        suggestion = None if rule else service.suggested_bank(n, context["source_banks"])
        segment = rule.segment if rule else service.suggested_segment(c, n)
        rows.append(dict(code=c, name=n, rule=rule, bank=names.get(rule.bank_code, "Bez veze sa jednom bankom") if rule else "",
                         suggestion=names.get(suggestion, ""), suggestion_code=suggestion,
                         segment_label=dict(BankAccountRule.SEGMENTS)[segment]))
        # Izbor konta u formi popunjava sačuvanu vezu ili predlog, bez ponovnog učitavanja strane.
        values[c] = dict(bank_code=rule.bank_code if rule else suggestion, segment=segment, note=rule.note if rule else "",
                         saved=bool(rule))
    context.update(edit_form=form, catalog=rows, account_values=values,
                   linked_count=sum(1 for r in rows if r["rule"]), suggested_count=sum(1 for r in rows if r["suggestion_code"]))
    return render(request, "finansije/banks/accounts.html", context)


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def bank_bill_edit(request, bank_code, pk=None):
    edit_access(request)
    if not all(user_has_role_permission(request.user, code) for code in ("menice:menica_list", "menice:ulazna_menica_list")):
        raise PermissionDenied
    context = context_for(request)
    bank = find_bank(context, bank_code)
    if not bank:
        if context.get("source_error"):
            return render(request, "finansije/banks/list.html", context, status=503)
        raise Http404
    instance = get_object_or_404(BankBillPlacement, pk=pk, company=service.company_id(), bank_code=bank_code) if pk else BankBillPlacement(company=service.company_id(), bank_code=bank_code)
    form = BankBillPlacementForm(request.POST if request.method == "POST" else None, instance=instance, initial={"delivered_on": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(None, "Ova menica već ima evidentiranu predaju. Prvo evidentirajte vraćanje.")
        else:
            messages.success(request, "Predaja menice je sačuvana.")
            return bank_redirect(bank_code, "bills")
    context.update(bank=bank, edit_form=form, edit_title="Predaja menice banci", cancel_url=reverse("finansije:bank_detail", args=[bank_code]) + "?tab=bills")
    return render(request, "finansije/banks/form.html", context)
