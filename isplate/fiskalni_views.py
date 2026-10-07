"""Isplate → Putni nalozi – Fiskalni računi (od 02.10.2026.) i Ostali fiskalni računi (od 05.10.2026.).

Isplate vide fiskalne račune učitane na putnim nalozima (`nabavka.FiskalniRacun` sa `putni_nalog`) i ostale
račune za gotovinski obračun, otvaraju njihov detalj (šifra posla; za ostale i interni broj) i šalju ih na knjiženje.
Od 07.10.2026. knjiži modul Knjiženje (`knjizenje`, uloga Knjiženje): Isplate račun samo šalju — poslat račun se
ne menja dok ga Knjiženje ne vrati na doradu. „Ostali fiskalni računi” su isti računi za gotovinski
obračun koji se ne vezuju za putni nalog (`evidencija = gotovina`); učitavaju se ovde, čitačem QR koda.
Tabela je zajednička sa Nabavkom, ali se prikazi ne mešaju: Nabavka ne vidi ove račune i obrnuto. Proknjižen račun se
u Nabavci i na putnom nalogu više ne menja.
Isplate još rade po starim pravima: ekran pokazuje sve račune sa putnih naloga.
"""
from urllib.parse import quote

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import escape, format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.exporting import rows_to_xlsx_response
from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from fleet.models import OrganizationalUnit
from knjizenje import services as knjizenje
from knjizenje.models import KnjizenjeRacuna
from nabavka.models import FiskalniRacun
from nabavka.services import fiskalni
from nabavka.views.fiskalni import _iznos

from . import tabela


def racuni_putnih_naloga():
    return (FiskalniRacun.objects.filter(putni_nalog__isnull=False)
            .select_related("putni_nalog", "putni_nalog__employee", "putni_nalog__job_code", "job_code",
                            "created_by", "proknjizio", "knjizenje"))


def ostali_racuni():
    """Gotovinski obračun: računi Isplata koji nisu na putnom nalogu."""
    return (FiskalniRacun.objects.filter(putni_nalog__isnull=True, evidencija=FiskalniRacun.Evidencija.GOTOVINA)
            .select_related("job_code", "created_by", "proknjizio", "knjizenje"))


class OstaliRacunForm(forms.Form):
    """Učitavanje računa za gotovinski obračun: šifra posla, link sa QR koda i napomena (za šta je račun)."""
    job_code = forms.ModelChoiceField(queryset=OrganizationalUnit.objects.none(), label="Šifra posla", required=False,
                                      empty_label="— bez šifre posla —",
                                      widget=forms.Select(attrs={"class": "form-select select2-method"}))
    link = forms.CharField(label="Link sa QR koda računa", widget=forms.Textarea(attrs={
        "class": "form-control font-monospace", "rows": 4, "autocomplete": "off", "spellcheck": "false",
        "placeholder": "Očitajte QR kod računa čitačem…"}))
    napomena = forms.CharField(label="Napomena", required=False, max_length=500,
                               widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Za šta je račun"}))
    interni_broj = forms.CharField(label="Interni broj računa", required=False, max_length=50,
                                   widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _sifre_posla(self.fields["job_code"])


class RacunNalogaForm(forms.Form):
    """Prozor „Dodaj račun” putnog naloga (od 07.10.2026.): šifra posla (predlog prema vozilu, menja se),
    interni broj i napomena; link stiže sa čitača QR koda."""
    job_code = forms.ModelChoiceField(queryset=OrganizationalUnit.objects.none(), label="Šifra posla", required=False,
                                      empty_label="— prema vozilu / nalogu —",
                                      widget=forms.Select(attrs={"class": "form-select select2-method"}))
    interni_broj = forms.CharField(label="Interni broj računa", required=False, max_length=50,
                                   widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    napomena = forms.CharField(label="Napomena", required=False, max_length=500,
                               widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "npr. gorivo, putarina, parking"}))

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("auto_id", "ispRacun_%s")
        super().__init__(*args, **kwargs)
        _sifre_posla(self.fields["job_code"])


def _sifre_posla(polje, zadrzi=None):
    from fleet.support.registar import ogranici_izbor

    # Isplate rade po starim pravima: nude se sve aktivne šifre posla iz registra.
    polje.queryset = OrganizationalUnit.objects.order_by("code")
    ogranici_izbor(polje, zadrzi)


class RacunIsplataForm(forms.ModelForm):
    """Detalj računa u Isplatama: šifra posla, interni broj i napomena. Bez garaže, magacina i dodatnih šifara."""

    class Meta:
        model = FiskalniRacun
        fields = ["job_code", "interni_broj", "napomena"]
        labels = {"job_code": "Šifra posla", "interni_broj": "Interni broj računa", "napomena": "Napomena"}
        widgets = {"job_code": forms.Select(attrs={"class": "form-select select2-method"}),
                   "interni_broj": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
                   "napomena": forms.TextInput(attrs={"class": "form-control", "placeholder": "Za šta je račun"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _sifre_posla(self.fields["job_code"], self.instance.job_code_id)
        self.fields["job_code"].required = False
        self.fields["job_code"].empty_label = "— bez šifre posla —"


STATUS = KnjizenjeRacuna.Status


def filtriraj(qs, g):
    izbor = g.get("knjizenje", "ne")
    if izbor == "ne":
        qs = qs.filter(proknjizeno=False)
    elif izbor == "neposlato":  # nije poslat ili je vraćen na doradu
        qs = qs.filter(Q(knjizenje__isnull=True) | Q(knjizenje__status=STATUS.VRACENO), proknjizeno=False)
    elif izbor == "vraceno":
        qs = qs.filter(knjizenje__status=STATUS.VRACENO, proknjizeno=False)
    elif izbor == "poslato":
        qs = qs.filter(knjizenje__status=STATUS.POSLATO, proknjizeno=False)
    elif izbor == "da":
        qs = qs.filter(proknjizeno=True)
    od, do = parse_date(g.get("od") or ""), parse_date(g.get("do") or "")
    if od:
        qs = qs.filter(pfr_vreme__date__gte=od)
    if do:
        qs = qs.filter(pfr_vreme__date__lte=do)
    if g.get("kupac") == "ims":
        qs = qs.filter(na_ims=True)
    elif g.get("kupac") == "drugi":
        qs = qs.filter(na_ims=False)
    for rec in tabela.reci(g):
        qs = qs.filter(Q(broj_racuna__icontains=rec) | Q(naziv_prodavca__icontains=rec) | Q(pib_prodavca=rec)
                       | Q(napomena__icontains=rec) | Q(interni_broj__icontains=rec)
                       | Q(putni_nalog__order_number__icontains=rec) | Q(putni_nalog__employee__last_name__icontains=rec)
                       | Q(putni_nalog__employee__first_name__icontains=rec) | Q(job_code__code__icontains=rec))
    return qs


def _zbir(qs):
    zbir = qs.aggregate(broj=Count("pk"), iznos=Sum("iznos"), pdv=Sum("pdv_ukupno"))
    return {"broj": zbir["broj"], "iznos": _iznos(zbir["iznos"] or 0), "pdv": _iznos(zbir["pdv"] or 0)}


def _ko(korisnik):
    return (korisnik.get_full_name() or korisnik.get_username()) if korisnik else ""


def status_knjizenja(r):
    """Tekst za izvoz: nije poslato / čeka knjiženje / vraćeno na doradu / proknjiženo."""
    st = knjizenje.stanje(r)
    return str(STATUS(st).label) if st else "Nije poslato"


def kolona_knjizenja(r, salje):
    """Kolona „Knjiženje”: dugme „Pošalji” dok račun nije poslat (ili je vraćen), posle toga samo status."""
    st = knjizenje.stanje(r)
    if st == STATUS.PROKNJIZENO:
        return format_html('<span class="isp-badge ok"><i class="mdi mdi-check-decagram" aria-hidden="true"></i> Proknjiženo</span>')
    if st == STATUS.POSLATO:
        z = knjizenje.zapis(r)
        return format_html('<span class="isp-badge info"><i class="mdi mdi-send-check" aria-hidden="true"></i> Poslato</span>'
                           '<div class="isp-small">{}</div>', f"{timezone.localtime(z.poslato_at):%d.%m.%Y.}" if z.poslato_at else "")
    vraceno = ""
    if st == STATUS.VRACENO:
        vraceno = format_html('<span class="isp-badge warn" title="{}"><i class="mdi mdi-undo" aria-hidden="true"></i> Vraćeno</span>'
                              '<div class="isp-small mb-1">{}</div>', knjizenje.zapis(r).razlog_vracanja, knjizenje.zapis(r).razlog_vracanja)
    if not salje:
        return vraceno or format_html('<span class="isp-badge muted">Nije poslato</span>')
    return vraceno + format_html(
        '<button type="button" class="btn btn-sm btn-success isp-posalji" data-url="{}" data-racun="{}">'
        '<i class="mdi mdi-send" aria-hidden="true"></i> Pošalji</button>',
        reverse("isplate:fiskalni_posalji", args=[r.pk]), r.broj_racuna)


class FiskalniPutniNaloziView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "isplate/fiskalni_putni_nalozi.html"
    KOLONE = {"0": "pfr_vreme", "1": "naziv_prodavca", "2": "broj_racuna", "3": "iznos", "5": "putni_nalog__order_number",
              "6": "job_code__code", "7": "created_at", "8": "proknjizeno"}
    OSTALI = False
    NASLOV = "Putni nalozi – Fiskalni računi"
    RUTA, IZVOZ = "isplate:fiskalni_putni_nalozi", "isplate:fiskalni_izvoz"
    PODRAZUMEVANO = "ne"

    @staticmethod
    def racuni():
        return racuni_putnih_naloga()

    def get(self, request, *args, **kwargs):
        if tabela.je_zahtev_tabele(request):
            return self.podaci(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        ctx.update(
            title=self.NASLOV, sidebar_template="sidebar_isplate.html", ostali=self.OSTALI,
            tabela_url=reverse(self.RUTA), izvoz_url=reverse(self.IZVOZ),
            zbir=_zbir(filtriraj(self.racuni(), {**g.dict(), "knjizenje": g.get("knjizenje", self.PODRAZUMEVANO)})),
            filteri={k: g.get(k, "") for k in ("q", "od", "do", "kupac")} | {"knjizenje": g.get("knjizenje", self.PODRAZUMEVANO)},
            moze_izvoz=user_has_role_permission(self.request.user, self.IZVOZ),
        )
        if self.OSTALI and user_has_role_permission(self.request.user, "isplate:fiskalni_ostali_ucitaj"):
            ctx["forma"] = OstaliRacunForm()
        return ctx

    def podaci(self, request):
        g, user = request.GET, request.user
        sve = self.racuni()
        qs = filtriraj(sve, {**g.dict(), "knjizenje": g.get("knjizenje", self.PODRAZUMEVANO)})
        start, duzina, draw = tabela.strana(g)
        strana = list(qs.order_by(tabela.redosled(g, self.KOLONE, "pfr_vreme"), "-pk")[start:start + duzina])
        prava = {"salje": user_has_role_permission(user, "isplate:fiskalni_posalji"),
                 "detalj": user_has_role_permission(user, "isplate:fiskalni_detail"),
                 "nalog": user_has_role_permission(user, "isplate:putni_nalozi_pravdanje")}
        return tabela.odgovor(draw, sve.count(), qs.count(), [self._red(r, prava) for r in strana], zbir=_zbir(qs))

    @staticmethod
    def _veza(r, prava):
        """Kolona „Putni nalog”: broj naloga, zaposleni i putovanje."""
        pn = r.putni_nalog
        nalog = escape(pn.order_number)
        if prava["nalog"]:
            nalog = format_html('<a href="{}?status=svi&amp;q={}">{}</a>', reverse("isplate:putni_nalozi_pravdanje"),
                                quote(pn.order_number), pn.order_number)
        detalji = " · ".join(d for d in (str(pn.employee or pn.other_employee_name or ""), pn.travel_location or "",
                                         f"{pn.travel_date:%d.%m.%Y.}" if pn.travel_date else "") if d)
        nalog += f'<div class="isp-small">{escape(detalji)}</div>'
        if pn.storniran:
            nalog += '<span class="isp-badge warn"><i class="mdi mdi-alert" aria-hidden="true"></i> Nalog storniran</span>'
        return nalog

    def _red(self, r, prava):
        broj = escape(r.broj_racuna)
        if prava["detalj"]:
            broj = format_html('<a href="{}">{}</a>', reverse("isplate:fiskalni_detail", args=[r.pk]), r.broj_racuna)
        if r.interni_broj:
            broj += f'<div class="isp-small">interni br. {escape(r.interni_broj)}</div>'
        if r.status != r.Status.POTVRDJEN:
            broj += ('<div><span class="isp-badge muted" title="Stavke još nisu preuzete sa stranice Poreske uprave">'
                     'Čeka proveru</span></div>')
        if r.na_ims:
            kupac = '<span class="isp-badge ok">IMS</span>'
        else:
            kupac = (f'<span class="isp-badge warn" title="Račun nije izdat na PIB Instituta">'
                     f'{"Drugi kupac" if r.id_kupca else "Fizičko lice"}</span>')
        pdv = f'<div class="isp-small">PDV {_iznos(r.pdv_ukupno)}</div>' if r.pdv_ukupno is not None else ""
        return {
            "DT_RowClass": "isp-proknjizen" if r.proknjizeno else "",
            "vreme": f"{timezone.localtime(r.pfr_vreme):%d.%m.%Y.}<div class=\"isp-small\">{timezone.localtime(r.pfr_vreme):%H:%M}</div>",
            "prodavac": (f'<span title="{escape(r.naziv_prodavca or "")}">{escape(r.naziv_prodavca or "—")}</span>'
                         f'<div class="isp-small">PIB {escape(r.pib_prodavca or "—")}</div>'),
            "broj": broj,
            "iznos": f"<strong>{_iznos(r.iznos)}</strong>{pdv}",
            "kupac": kupac,
            "veza": self._veza(r, prava),
            "sifra": escape(r.job_code.code if r.job_code_id else "—"),
            "ucitao": (f'{escape(r.created_by.get_username() if r.created_by_id else "—")}'
                       f'<div class="isp-small">{timezone.localtime(r.created_at):%d.%m.%Y.}</div>'),
            "knjizenje": kolona_knjizenja(r, prava["salje"]),
        }


@login_required
@role_permission_required()
def fiskalni_izvoz(request):
    qs = filtriraj(racuni_putnih_naloga(), request.GET).order_by("pfr_vreme", "pk")
    zaglavlje = ["Vreme računa", "Prodavac", "PIB prodavca", "Broj računa", "Iznos", "PDV", "Kupac", "Putni nalog",
                 "Zaposleni", "Mesto putovanja", "Datum putovanja", "Šifra posla", "Status", "Knjiženje", "Proknjižio",
                 "Proknjiženo dana", "Učitao"]
    redovi = []
    for r in qs:
        pn = r.putni_nalog
        redovi.append([
            timezone.localtime(r.pfr_vreme).strftime("%d.%m.%Y %H:%M"), r.naziv_prodavca, r.pib_prodavca, r.broj_racuna,
            float(r.iznos), float(r.pdv_ukupno) if r.pdv_ukupno is not None else None,
            "IMS" if r.na_ims else ("Drugi kupac" if r.id_kupca else "Fizičko lice"),
            pn.order_number, str(pn.employee or pn.other_employee_name or ""), pn.travel_location,
            pn.travel_date.strftime("%d.%m.%Y") if pn.travel_date else "", r.job_code.code if r.job_code_id else "",
            r.get_status_display(), status_knjizenja(r), _ko(r.proknjizio),
            timezone.localtime(r.proknjizeno_at).strftime("%d.%m.%Y %H:%M") if r.proknjizeno_at else "",
            r.created_by.get_username() if r.created_by_id else "",
        ])
    return rows_to_xlsx_response(f"Fiskalni-racuni-putnih-naloga-{timezone.localdate():%Y%m%d}.xlsx",
                                 "Fiskalni računi", zaglavlje, redovi, bold_header=True, auto_width=True)


class FiskalniOstaliView(FiskalniPutniNaloziView):
    """Ostali fiskalni računi: isti prikaz, bez putnog naloga; umesto naloga kolona „Napomena”."""
    KOLONE = {**FiskalniPutniNaloziView.KOLONE, "5": "napomena"}
    OSTALI = True
    NASLOV = "Ostali fiskalni računi"
    RUTA, IZVOZ = "isplate:fiskalni_ostali", "isplate:fiskalni_ostali_izvoz"

    @staticmethod
    def racuni():
        return ostali_racuni()

    @staticmethod
    def _veza(r, prava):
        return escape(r.napomena or "—")


@login_required
@require_POST
@role_permission_required()
def fiskalni_ostali_ucitaj(request):
    """Novi račun za gotovinski obračun (čitač QR koda, prozor „Učitaj račun”); ne vezuje se za putni nalog i
    ne vidi se u Nabavci. Kod oštećenog QR koda uz link stižu i ručno uneti podaci sa računa."""
    ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    forma = OstaliRacunForm(request.POST)
    try:
        if not forma.is_valid():
            raise fiskalni.GreskaOcitavanja(" ".join(e for greske in forma.errors.values() for e in greske) or "Proverite unos.")
        racun, upozorenja = fiskalni.upisi(forma.cleaned_data["link"], forma.cleaned_data["job_code"], request.user,
                                           forma.cleaned_data["napomena"], evidencija=FiskalniRacun.Evidencija.GOTOVINA,
                                           ocekivano=fiskalni.ocekivano_iz_zahteva(request.POST))
        if forma.cleaned_data["interni_broj"]:
            racun.interni_broj = forma.cleaned_data["interni_broj"].strip()
            racun.save(update_fields=["interni_broj"])
    except fiskalni.GreskaOcitavanja as exc:
        if ajax:
            return JsonResponse({"ok": False, "poruka": str(exc)}, status=400)
        messages.error(request, str(exc))
        return redirect("isplate:fiskalni_ostali")
    poruka = (f"Račun {racun.broj_racuna} ({racun.naziv_prodavca or racun.pib_prodavca}, "
              f"{_iznos(racun.iznos)} din) je učitan u ostale fiskalne račune.")
    # Posle učitavanja odmah se otvara detalj računa (šifra posla, interni broj, slanje na knjiženje).
    detalj = reverse("isplate:fiskalni_detail", args=[racun.pk])
    messages.success(request, poruka)
    for upozorenje in upozorenja:
        messages.warning(request, upozorenje)
    if ajax:
        return JsonResponse({"ok": True, "poruka": poruka, "upozorenja": list(upozorenja), "broj": racun.broj_racuna,
                             "prodavac": racun.naziv_prodavca or racun.pib_prodavca, "iznos": _iznos(racun.iznos),
                             "detalj": detalj})
    return redirect(detalj)


@login_required
@role_permission_required()
def fiskalni_ostali_izvoz(request):
    qs = filtriraj(ostali_racuni(), request.GET).order_by("pfr_vreme", "pk")
    zaglavlje = ["Vreme računa", "Prodavac", "PIB prodavca", "Broj računa", "Interni broj", "Iznos", "PDV", "Kupac",
                 "Napomena", "Šifra posla", "Status", "Knjiženje", "Proknjižio", "Proknjiženo dana", "Učitao"]
    redovi = [[
        timezone.localtime(r.pfr_vreme).strftime("%d.%m.%Y %H:%M"), r.naziv_prodavca, r.pib_prodavca, r.broj_racuna,
        r.interni_broj, float(r.iznos), float(r.pdv_ukupno) if r.pdv_ukupno is not None else None,
        "IMS" if r.na_ims else ("Drugi kupac" if r.id_kupca else "Fizičko lice"), r.napomena, r.job_code.code if r.job_code_id else "",
        r.get_status_display(), status_knjizenja(r), _ko(r.proknjizio),
        timezone.localtime(r.proknjizeno_at).strftime("%d.%m.%Y %H:%M") if r.proknjizeno_at else "",
        r.created_by.get_username() if r.created_by_id else "",
    ] for r in qs]
    return rows_to_xlsx_response(f"Ostali-fiskalni-racuni-{timezone.localdate():%Y%m%d}.xlsx",
                                 "Ostali fiskalni računi", zaglavlje, redovi, bold_header=True, auto_width=True)


def _racun_isplata(pk):
    return get_object_or_404(knjizenje.racuni_isplata().select_related(
        "putni_nalog", "putni_nalog__employee", "putni_nalog__vehicle", "putni_nalog__job_code", "job_code", "created_by", "proknjizio",
        "knjizenje", "knjizenje__poslao", "knjizenje__vratio").prefetch_related("stavke"), pk=pk)


def _nazad(request, racun):
    """Povratak na stranu sa koje je detalj otvoren (`?nazad=`, npr. putni nalozi posle očitavanja), inače spisak."""
    nazad = request.GET.get("nazad") or ""
    if nazad.startswith("/") and url_has_allowed_host_and_scheme(nazad, allowed_hosts={request.get_host()}):
        return nazad
    return reverse("isplate:fiskalni_putni_nalozi" if racun.putni_nalog_id else "isplate:fiskalni_ostali")


def _na_detalj(request, racun):
    nazad = request.GET.get("nazad")
    return redirect(reverse("isplate:fiskalni_detail", args=[racun.pk]) + (f"?nazad={quote(nazad)}" if nazad else ""))


@login_required
@role_permission_required()
def fiskalni_detail(request, pk, forma=None):
    """Detalj računa u Isplatama — izgled kao u Nabavci (pregled, podaci, stavke, tekst računa). Menjaju se samo šifra
    posla, interni broj i napomena; garaža, magacin i dodatne šifre su samo u Nabavci."""
    racun = _racun_isplata(pk)
    user = request.user
    moze_menjati = user_has_role_permission(user, "isplate:fiskalni_izmena") and not knjizenje.zakljucan_u_isplatama(racun)
    pn = racun.putni_nalog
    moze_skinuti = bool(pn) and not pn.opravdan and not knjizenje.zakljucan_u_isplatama(racun) and \
        user_has_role_permission(user, "isplate:putni_nalog_racun_ukloni")
    return render(request, "isplate/fiskalni_detail.html", {
        "upozorenja": fiskalni.upozorenja(racun), "moze_skinuti": moze_skinuti,
        "skini_url": reverse("isplate:putni_nalog_racun_ukloni", args=[pn.pk, racun.pk]) if moze_skinuti else "",
        "title": f"Fiskalni račun {racun.broj_racuna}", "sidebar_template": "sidebar_isplate.html", "racun": racun,
        "forma": forma or (RacunIsplataForm(instance=racun) if moze_menjati else None), "moze_menjati": moze_menjati,
        "stanje": knjizenje.stanje(racun), "z": knjizenje.zapis(racun),
        "moze_slati": user_has_role_permission(user, "isplate:fiskalni_posalji") and knjizenje.moze_se_poslati(racun),
        "moze_nalog": user_has_role_permission(user, "isplate:putni_nalozi_pravdanje"),
        "nazad": _nazad(request, racun),
    }, status=400 if forma is not None else 200)


@login_required
@require_POST
@role_permission_required()
def fiskalni_izmena(request, pk):
    racun = _racun_isplata(pk)
    if knjizenje.zakljucan_u_isplatama(racun):
        messages.error(request, "Račun je poslat na knjiženje ili proknjižen i ne menja se. Ispravka je moguća tek kad ga "
                                "Knjiženje vrati na doradu.")
        return _na_detalj(request, racun)
    forma = RacunIsplataForm(request.POST, instance=racun)
    if not forma.is_valid():
        return fiskalni_detail(request, pk, forma=forma)
    racun = forma.save()
    racun.uskladi_glavnu_sifru(request.user)
    messages.success(request, "Račun je sačuvan.")
    return _na_detalj(request, racun)


@login_required
@require_POST
@role_permission_required()
def fiskalni_posalji(request, pk):
    """Slanje na knjiženje — sa detalja ili sa spiska (fetch). Povlačenja nema: poslat račun vraća samo Knjiženje."""
    racun = _racun_isplata(pk)
    ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    try:
        knjizenje.posalji(racun, request.user)
    except knjizenje.GreskaKnjizenja as exc:
        if ajax:
            return JsonResponse({"ok": False, "poruka": str(exc)}, status=400)
        messages.error(request, str(exc))
        return _na_detalj(request, racun)
    if ajax:
        return JsonResponse({"ok": True, "kolona": kolona_knjizenja(racun, True)})
    messages.success(request, f"Račun {racun.broj_racuna} je poslat na knjiženje.")
    return _na_detalj(request, racun)
