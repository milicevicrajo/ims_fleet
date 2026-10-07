"""Kadrovi → Ugovori: ugovori zaposlenih po periodima rada iz kadrovske baze.

Spisak dolazi iz sinhronizovane tabele (`hr/services/ugovori.py`); Kadrovi unose broj ugovora,
broj aneksa (uz vezu na glavni ugovor), skeniran dokument i napomenu, a po potrebi ispravljaju
zabelezenu OJ i radno mesto i dodaju druga radna mesta (za BZR; izvestaji uzimaju prvo). Vidljivost prati obuhvat Kadrova (zaposleni u obuhvatu korisnika).
"""
import os

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.uploadedfile import UploadedFile
from django.db import DatabaseError
from django.db.models import Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from hr.access import scope_employee_records
from hr.models import DodatnoRadnoMesto, Employee, UgovoriSinhronizacija, UgovorZaposlenog
from hr.services import ugovori as servis

SIDEBAR = "sidebar_kadrovi.html"
DOZVOLJENI_FAJLOVI = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
NAJVECI_FAJL_MB = 20
POLJA_OJ = ("oj", "naziv_oj", "sifra_sistematizacije", "naziv_radnog_mesta")


def vidljivi(user):
    return scope_employee_records(UgovorZaposlenog.objects.select_related("employee", "glavni_ugovor"), user)


def _ime(red):
    return str(red.employee) if red.employee_id else (red.ime_prezime.title() or f"Radnik {red.employee_code}")


def _period(red):
    do = "na neodređeno" if red.na_neodredjeno else (red.datum_do.strftime("%d.%m.%Y.") if red.datum_do else "—")
    return f"{red.datum_od:%d.%m.%Y.} – {do}"


def _tekuci(danas):
    return Q(na_neodredjeno=True) | Q(datum_do__gte=danas)


def _filtriraj(request, qs):
    g = request.GET
    radnici = g.get("radnici", "aktivni")
    if radnici == "aktivni":
        qs = qs.filter(radnik_aktivan=True)
    elif radnici == "bivsi":
        qs = qs.filter(radnik_aktivan=False)
    if g.get("kategorija") in UgovorZaposlenog.Kategorija.values:
        qs = qs.filter(kategorija=g["kategorija"])
    unos = g.get("unos", "")
    if unos == "uneto":
        qs = qs.exclude(broj_ugovora="")
    elif unos == "nije":
        qs = qs.filter(broj_ugovora="")
    elif unos == "dokument":
        qs = qs.exclude(dokument="")
    elif unos == "bez_dokumenta":
        qs = qs.filter(dokument="")
    elif unos == "provera":
        qs = qs.filter(prethodni_datum_od__isnull=False)
    if g.get("tekuci") == "1":
        qs = qs.filter(_tekuci(timezone.localdate()))
    izvor = g.get("izvor", "")
    if izvor == "nema":
        qs = qs.filter(u_izvoru=False)
    elif izvor != "svi":
        qs = qs.filter(u_izvoru=True)
    pojam = (g.get("search[value]") or g.get("q") or "").strip()
    if pojam:
        uslov = (Q(ime_prezime__icontains=pojam) | Q(employee__first_name__icontains=pojam)
                 | Q(employee__last_name__icontains=pojam) | Q(broj_ugovora__icontains=pojam)
                 | Q(broj_aneksa__icontains=pojam) | Q(naziv_oj__icontains=pojam)
                 | Q(naziv_radnog_mesta__icontains=pojam) | Q(oj=pojam)
                 | Q(pk__in=DodatnoRadnoMesto.objects.filter(naziv_radnog_mesta__icontains=pojam).values("ugovor")))
        if pojam.isdigit():
            # Broj radnika nalazi ugovore cele osobe (i pod njenim ostalim brojevima).
            osobe = Employee.objects.filter(employee_code=int(pojam), osoba__isnull=False).values("osoba")
            uslov |= Q(employee_code=int(pojam)) | Q(employee__osoba__in=osobe)
        qs = qs.filter(uslov)
    return qs


def _periodi_osobe(qs, red):
    """Svi periodi rada osobe — pod svim njenim brojevima radnika (ponovni prijem, van radnog odnosa)."""
    uslov = Q(employee_code=red.employee_code)
    if red.employee_id and red.employee.osoba_id:
        uslov |= Q(employee__osoba_id=red.employee.osoba_id)
    return qs.filter(uslov).select_related("employee").order_by("-datum_od", "-redni_broj")


class UgovorListView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = "hr/ugovori/ugovor_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        tekuci = vidljivi(user).filter(u_izvoru=True, radnik_aktivan=True).filter(_tekuci(timezone.localdate()))
        brojevi = tekuci.aggregate(ukupno=Count("pk"), uneto=Count("pk", filter=~Q(broj_ugovora="")),
                                   dokument=Count("pk", filter=~Q(dokument="")))
        g = self.request.GET
        ctx.update(
            title="Ugovori zaposlenih", sidebar_template=SIDEBAR, brojevi=brojevi,
            za_proveru=vidljivi(user).filter(prethodni_datum_od__isnull=False).count(),
            poslednja=UgovoriSinhronizacija.objects.select_related("created_by").first(),
            kategorije=UgovorZaposlenog.Kategorija.choices,
            filteri={"radnici": g.get("radnici", "aktivni"), "kategorija": g.get("kategorija", ""),
                     "unos": g.get("unos", ""), "tekuci": g.get("tekuci", ""), "izvor": g.get("izvor", "")},
            can_sync=user_has_role_permission(user, "hr:ugovor_sync"),
        )
        return ctx


class UgovorDataView(LoginRequiredMixin, RolePermissionRequiredMixin, View):
    KOLONE = {"0": "ime_prezime", "1": "datum_od", "2": "kategorija", "3": "oj", "4": "naziv_radnog_mesta",
              "5": "broj_ugovora", "6": "broj_aneksa", "7": "dokument"}

    def get(self, request):
        sve = vidljivi(request.user)
        qs = _filtriraj(request, sve)
        polje = self.KOLONE.get(request.GET.get("order[0][column]", "1"), "datum_od")
        smer = "-" if request.GET.get("order[0][dir]", "desc") == "desc" else ""
        qs = qs.order_by(f"{smer}{polje}", "employee_code", "-redni_broj")
        try:
            start = max(int(request.GET.get("start", 0)), 0)
            duzina = min(max(int(request.GET.get("length", 50)), 1), 200)
            draw = int(request.GET.get("draw", 0))
        except (TypeError, ValueError):
            start, duzina, draw = 0, 50, 0
        moze_dokument = user_has_role_permission(request.user, "hr:ugovor_dokument")
        redovi = [self._red(r, moze_dokument) for r in qs.prefetch_related("dodatna_radna_mesta")[start:start + duzina]]
        return JsonResponse({"draw": draw, "recordsTotal": sve.count(), "recordsFiltered": qs.count(), "data": redovi})

    @staticmethod
    def _red(r, moze_dokument):
        detalj = reverse("hr:ugovor_detail", kwargs={"pk": r.pk})
        oznake = []
        if r.prethodni_datum_od:
            oznake.append('<span class="ugovor-badge warn" title="Datum početka se promenio u kadrovskoj bazi '
                          f'(ranije {r.prethodni_datum_od:%d.%m.%Y.})"><i class="mdi mdi-alert"></i> Proveriti</span>')
        if not r.u_izvoru:
            oznake.append('<span class="ugovor-badge muted">Nema u kadrovskoj bazi</span>')
        if r.kategorija == UgovorZaposlenog.Kategorija.VAN_RADNOG_ODNOSA:
            kategorija = '<span class="ugovor-badge info">Van radnog odnosa</span>'
        else:
            kategorija = '<span class="ugovor-badge ok">Radni odnos</span>'
        aneks = "—"
        if r.broj_aneksa:
            aneks = escape(r.broj_aneksa)
            if r.glavni_ugovor_id:
                aneks += f'<div class="ugovor-small">uz {escape(r.glavni_ugovor.broj_ugovora or _period(r.glavni_ugovor))}</div>'
        dokument = '<span class="text-muted">—</span>'
        if r.dokument and moze_dokument:
            url = reverse("hr:ugovor_dokument", kwargs={"pk": r.pk})
            dokument = (f'<a class="btn btn-outline-secondary btn-sm" href="{url}" target="_blank" rel="noopener" '
                        f'title="{escape(r.dokument_naziv)}"><i class="mdi mdi-file-pdf-box"></i></a>')
        elif r.dokument:
            dokument = '<i class="mdi mdi-paperclip" title="Dokument je priložen"></i>'
        return {
            "radnik": (f'<a class="ugovor-radnik" href="{detalj}">{escape(_ime(r))}</a>'
                       f'<div class="ugovor-small">{r.employee_code}{"" if r.radnik_aktivan else " · bivši radnik"}</div>'),
            "period": (f'<span class="text-nowrap">{_period(r)}</span>'
                       + (f'<div class="ugovor-small">{escape(r.opis)}</div>' if r.opis else "") + "".join(oznake)),
            "kategorija": kategorija,
            "oj": (f'<strong>{escape(r.oj)}</strong><div class="ugovor-small">{escape(r.naziv_oj)}</div>' if r.oj else "—"),
            "radno_mesto": (f'<strong>{escape(r.sifra_sistematizacije)}</strong>'
                            f'<div class="ugovor-small">{escape(r.naziv_radnog_mesta)}</div>' if r.sifra_sistematizacije else "—")
                           + "".join(f'<div class="ugovor-small" title="{n}. radno mesto">{n}. {escape(str(m))}</div>'
                                     for n, m in enumerate(r.dodatna_radna_mesta.all(), start=2)),
            "broj_ugovora": ((escape(r.broj_ugovora) or '<span class="ugovor-badge muted">Nije uneto</span>')
                             + (f'<div class="ugovor-small">od {r.datum_ugovora:%d.%m.%Y.}</div>' if r.datum_ugovora else "")),
            "aneks": aneks,
            "dokument": dokument,
            "akcije": f'<a class="btn btn-outline-primary btn-sm" href="{detalj}"><i class="mdi mdi-pencil"></i> Unos</a>',
        }


class UgovorForm(forms.ModelForm):
    class Meta:
        model = UgovorZaposlenog
        fields = ["broj_ugovora", "datum_ugovora", "broj_aneksa", "glavni_ugovor", "dokument", "napomena", *POLJA_OJ]
        widgets = {
            "broj_ugovora": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "datum_ugovora": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "broj_aneksa": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off",
                                                  "placeholder": "Samo ako je period aneks"}),
            "glavni_ugovor": forms.Select(attrs={"class": "form-select"}),
            "dokument": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ",".join(sorted(DOZVOLJENI_FAJLOVI))}),
            "napomena": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "oj": forms.TextInput(attrs={"class": "form-control"}),
            "naziv_oj": forms.TextInput(attrs={"class": "form-control"}),
            "sifra_sistematizacije": forms.TextInput(attrs={"class": "form-control"}),
            "naziv_radnog_mesta": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        red = self.instance
        self.fields["broj_ugovora"].required = True
        self.fields["broj_ugovora"].error_messages["required"] = "Unesite broj ugovora."
        polje = self.fields["glavni_ugovor"]
        polje.required = False
        polje.empty_label = "— bez veze sa glavnim ugovorom —"
        # Glavni ugovor je raniji period istog radnika koji nije i sam aneks.
        polje.queryset = (UgovorZaposlenog.objects.filter(employee_code=red.employee_code, broj_aneksa="",
                                                          datum_od__lte=red.datum_od)
                          .exclude(pk=red.pk).order_by("-datum_od"))
        polje.label_from_instance = lambda u: f"{u.broj_ugovora or 'bez broja'} · {_period(u)}"

    def clean_dokument(self):
        fajl = self.cleaned_data.get("dokument")
        if isinstance(fajl, UploadedFile):
            if os.path.splitext(fajl.name)[1].lower() not in DOZVOLJENI_FAJLOVI:
                raise forms.ValidationError("Dozvoljeni su PDF i slike (JPG, PNG, TIFF).")
            if fajl.size > NAJVECI_FAJL_MB * 1024 * 1024:
                raise forms.ValidationError(f"Fajl je veći od {NAJVECI_FAJL_MB} MB.")
        return fajl

    def clean(self):
        data = super().clean()
        if not data.get("broj_aneksa"):
            data["glavni_ugovor"] = None
        return data


class DodatnoRadnoMestoForm(forms.ModelForm):
    class Meta:
        model = DodatnoRadnoMesto
        fields = list(POLJA_OJ)
        widgets = {polje: forms.TextInput(attrs={"class": "form-control"}) for polje in POLJA_OJ}

    def clean(self):
        data = super().clean()
        if not self.cleaned_data.get("DELETE") and not (data.get("sifra_sistematizacije") or data.get("naziv_radnog_mesta")):
            raise forms.ValidationError("Unesite šifru ili naziv radnog mesta.")
        return data


DodatnaRadnaMestaFormSet = forms.inlineformset_factory(UgovorZaposlenog, DodatnoRadnoMesto, form=DodatnoRadnoMestoForm,
                                                       extra=0, can_delete=True)


def _radna_mesta(data=None, instance=None):
    return DodatnaRadnaMestaFormSet(data, instance=instance, prefix="rm")


class UgovorDetailView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = "hr/ugovori/ugovor_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        red = kwargs.get("red") or get_object_or_404(vidljivi(self.request.user), pk=self.kwargs["pk"])
        user = self.request.user
        ctx.update(
            title=f"Ugovor — {_ime(red)}", sidebar_template=SIDEBAR, red=red, ime=_ime(red), period=_period(red),
            form=kwargs.get("form") or UgovorForm(instance=red),
            radna_mesta=kwargs.get("radna_mesta") or _radna_mesta(instance=red),
            dodatna_radna_mesta=red.dodatna_radna_mesta.all(),
            periodi=_periodi_osobe(vidljivi(user), red),
            aneksi=red.aneksi.order_by("datum_od"),
            can_update=user_has_role_permission(user, "hr:ugovor_update"),
            can_document=user_has_role_permission(user, "hr:ugovor_dokument"),
            can_view_employee=bool(red.employee_id) and user_has_role_permission(user, "employee_detail"),
        )
        return ctx


@login_required
@require_POST
@role_permission_required("hr:ugovor_update")
def ugovor_update(request, pk):
    red = get_object_or_404(vidljivi(request.user), pk=pk)
    detalj = reverse("hr:ugovor_detail", kwargs={"pk": red.pk})
    akcija = request.POST.get("akcija", "sacuvaj")
    if akcija == "preuzmi_trenutno":
        try:
            trenutno = servis.trenutno_za_radnika(red.employee_code, kategorija=red.kategorija)
        except DatabaseError:
            messages.error(request, "Kadrovska baza trenutno nije dostupna. Zabeleženi podaci nisu menjani.")
            return redirect(detalj)
        if not trenutno:
            messages.warning(request, "Radnik nije pronađen u kadrovskoj bazi.")
            return redirect(detalj)
        for polje in POLJA_OJ:
            setattr(red, polje, trenutno[polje])
        red.podaci_poreklo, red.podaci_zabelezeni = UgovorZaposlenog.Poreklo.SINHRONIZACIJA, timezone.localdate()
        red.izmenio, red.izmenjeno = request.user, timezone.now()
        red.save()
        messages.success(request, "Upisane su trenutna OJ i radno mesto iz kadrovske baze.")
        return redirect(detalj)
    if akcija == "potvrdi_period":
        red.prethodni_datum_od = None
        red.izmenio, red.izmenjeno = request.user, timezone.now()
        red.save(update_fields=["prethodni_datum_od", "izmenio", "izmenjeno"])
        messages.success(request, "Promena perioda je potvrđena.")
        return redirect(detalj)

    pre = {polje: getattr(red, polje) for polje in POLJA_OJ}
    form = UgovorForm(request.POST, request.FILES, instance=red)
    radna_mesta = _radna_mesta(request.POST, instance=red)
    form_ok = form.is_valid()  # obe forme se proveravaju, da se vide sve greške odjednom
    if not (radna_mesta.is_valid() and form_ok):
        view = UgovorDetailView()
        view.setup(request, pk=pk)
        return view.render_to_response(view.get_context_data(red=red, form=form, radna_mesta=radna_mesta), status=400)
    red = form.save(commit=False)
    if any(getattr(red, polje) != pre[polje] for polje in POLJA_OJ):
        red.podaci_poreklo, red.podaci_zabelezeni = UgovorZaposlenog.Poreklo.RUCNO, timezone.localdate()
    if "dokument" in request.FILES:
        red.dokument_naziv = request.FILES["dokument"].name[:255]
    elif not red.dokument:
        red.dokument_naziv = ""
    red.izmenio, red.izmenjeno = request.user, timezone.now()
    red.save()
    radna_mesta.save()
    messages.success(request, "Ugovor je sačuvan.")
    return redirect(detalj)


@login_required
@role_permission_required("hr:ugovor_dokument")
def ugovor_dokument(request, pk):
    """Skeniran ugovor — samo za korisnika koji vidi tog zaposlenog (lični podaci)."""
    red = get_object_or_404(vidljivi(request.user), pk=pk)
    if not red.dokument:
        raise Http404("Dokument nije priložen.")
    try:
        fajl = red.dokument.open("rb")
    except FileNotFoundError:
        raise Http404("Fajl dokumenta nije pronađen.")
    return FileResponse(fajl, filename=red.dokument_naziv or os.path.basename(red.dokument.name))


@login_required
@require_POST
@role_permission_required("hr:ugovor_sync")
def ugovor_sync(request):
    try:
        rezultat = servis.sinhronizuj(korisnik=request.user)
    except servis.PrazanIzvor as exc:
        messages.error(request, f"{exc} Postojeći podaci su ostali nepromenjeni.")
    except DatabaseError:
        messages.error(request, "Kadrovska baza trenutno nije dostupna. Postojeći podaci su ostali nepromenjeni.")
    else:
        messages.success(request, f"Sinhronizacija završena: {rezultat['novih']} novih, {rezultat['azurirano']} ažuriranih, "
                                  f"{rezultat['nema_u_izvoru']} više nema u kadrovskoj bazi (ukupno {rezultat['ukupno']}).")
    return redirect("hr:ugovor_list")
