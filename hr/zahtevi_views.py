from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from core.models import OrganizationalUnit
from hr.access import visible_employees
from hr.models import Pismo, Resenje, VrstaZahteva, Zahtev, ZahtevDan
from hr.resenja_forms import predlog_teksta
from hr.services.resenja import dodatna_polja
from hr.services.zahtevi import (aktivna_resenja, dodeli_broj, dokument_zahteva_za_prikaz, napravi_resenje,
    podnesi_zahtev, pripremi_zahtev, storniraj_zahtev, visible_zahtevi)
from hr.zahtevi_forms import GrupniZahtevForm, ResenjaIzZahtevaForm, ZahtevDanFormSet, ZahtevForm

SIDEBAR = 'sidebar_kadrovi.html'


def _vrste_meta():
    """Podaci o vrstama koje forma koristi da sakrije polja koja se ne traže."""
    return {str(vrsta.pk): {'period': vrsta.trazi_period or vrsta.trazi_dane, 'dani': vrsta.trazi_dane,
        'radni_dani': vrsta.trazi_radne_dane, 'vreme': not vrsta.trazi_radne_dane, 'pismo': vrsta.podrazumevano_pismo,
        'polja': [oznaka for oznaka, _ in dodatna_polja(vrsta)]}
        for vrsta in VrstaZahteva.objects.filter(je_aktivna=True)}


def _dozvole(user):
    return {kod: user_has_role_permission(user, 'hr:' + kod) for kod in
            ('zahtev_create', 'zahtev_bulk_create', 'zahtev_podnesi', 'zahtev_storniraj', 'zahtev_resenje_create',
             'zahtev_bulk_resenja', 'resenje_catalog', 'resenje_list')}


def _zaposleni_u_obuhvatu(user):
    return visible_employees(user, unrestricted=user_has_role_permission(user, 'hr:resenje_view_all')).filter(is_active=True)


def _broj_dana(formset):
    return sum(1 for podaci in formset.cleaned_data if podaci and podaci.get('datum') and not podaci.get('DELETE'))


class ZahtevListView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/zahtev_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = visible_zahtevi(self.request.user).annotate(broj_resenja=Count('resenja', distinct=True))
        vrsta = self.request.GET.get('vrsta') or ''
        centar = self.request.GET.get('centar') or ''
        status = self.request.GET.get('status') or ''
        godina = self.request.GET.get('godina') or ''
        resenje = self.request.GET.get('resenje') or ''
        if vrsta.isdigit():
            qs = qs.filter(vrsta_id=int(vrsta))
        if centar:
            qs = qs.filter(centar=centar)
        if status:
            qs = qs.filter(status=status)
        if godina.isdigit():
            qs = qs.filter(godina=int(godina))
        if resenje == 'bez':
            qs = qs.filter(broj_resenja=0).exclude(status=Zahtev.Status.STORNIRAN)
        elif resenje == 'sa':
            qs = qs.filter(broj_resenja__gt=0)
        ctx.update(title='Zahtevi zaposlenih', sidebar_template=SIDEBAR, zahtevi=qs[:1000],
            vrste=VrstaZahteva.objects.all(), statusi=Zahtev.Status.choices,
            centri=sorted({kod for kod in OrganizationalUnit.objects.values_list('center', flat=True) if kod}),
            izabrana_vrsta=vrsta, izabran_centar=centar, izabran_status=status, izabrana_godina=godina,
            izabrano_resenje=resenje, resenja_form=ResenjaIzZahtevaForm(), **_dozvole(self.request.user))
        return ctx


class ZahtevFormView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/zahtev_form.html'

    def get_object(self):
        if 'pk' not in self.kwargs:
            return None
        zahtev = get_object_or_404(visible_zahtevi(self.request.user), pk=self.kwargs['pk'])
        if zahtev.je_zakljucan:
            raise Http404('Podnet zahtev se ne menja.')
        return zahtev

    def _form(self, data=None, instance=None):
        form = ZahtevForm(data, instance=instance, actor=self.request.user)
        if not form.fields['zaposleni'].disabled:
            form.fields['zaposleni'].queryset = _zaposleni_u_obuhvatu(self.request.user)
        return form

    def get_context_data(self, **kwargs):
        zahtev = kwargs.pop('instance', None) or self.get_object()
        form = kwargs.pop('form', None) or self._form(instance=zahtev)
        formset = kwargs.pop('formset', None) or ZahtevDanFormSet(instance=zahtev)
        ctx = super().get_context_data(**kwargs)
        ctx.update(title='Izmena zahteva' if zahtev else 'Novi zahtev', sidebar_template=SIDEBAR,
            form=form, formset=formset, zahtev=zahtev, vrste_meta=_vrste_meta())
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        zahtev = self.get_object()
        form = self._form(request.POST, instance=zahtev)
        formset = ZahtevDanFormSet(request.POST, instance=zahtev)
        if not form.is_valid():
            formset.is_valid()
            return self.render_to_response(self.get_context_data(form=form, formset=formset, instance=zahtev))
        novi = form.save(commit=False)
        if zahtev is None:
            novi.created_by = request.user
        pripremi_zahtev(novi)
        formset = ZahtevDanFormSet(request.POST, instance=novi)
        if formset.is_valid() and novi.vrsta.trazi_dane and not novi.datum_od and not _broj_dana(formset):
            form.add_error(None, 'Ova vrsta zahteva traži bar jedan dan ili period.')
        if not formset.is_valid() or form.errors:
            return self.render_to_response(self.get_context_data(form=form, formset=formset, instance=zahtev))
        if zahtev is None:
            dodeli_broj(novi)
        novi.save()
        formset.instance = novi
        formset.save()
        messages.success(request, f'Zahtev {novi.broj} je sačuvan kao nacrt.')
        return redirect('hr:zahtev_detail', pk=novi.pk)


class ZahtevDetailView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/zahtev_detail.html'

    def get_context_data(self, **kwargs):
        zahtev = get_object_or_404(visible_zahtevi(self.request.user).prefetch_related('dani'), pk=self.kwargs['pk'])
        ctx = super().get_context_data(**kwargs)
        ctx.update(title=f'Zahtev {zahtev.broj}', sidebar_template=SIDEBAR, zahtev=zahtev,
            dokument=dokument_zahteva_za_prikaz(zahtev),
            resenja=zahtev.resenja.select_related('vrsta').order_by('podbroj', 'pk'),
            ima_aktivno_resenje=aktivna_resenja(zahtev).exists(),
            resenje_form=ResenjaIzZahtevaForm(initial={'vrsta': zahtev.vrsta.vrsta_resenja_id}),
            **_dozvole(self.request.user))
        return ctx


class ZahtevPrintView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_print.html'

    def get_context_data(self, **kwargs):
        zahtev = get_object_or_404(visible_zahtevi(self.request.user).prefetch_related('dani'), pk=self.kwargs['pk'])
        ctx = super().get_context_data(**kwargs)
        ctx.update(dokumenti=[dokument_zahteva_za_prikaz(zahtev)], naslov=f'Zahtev {zahtev.broj}',
            dokument_sablon='hr/resenja/_zahtev_document.html')
        return ctx


class ZahtevBulkPrintView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_print.html'

    def get_context_data(self, **kwargs):
        oznake = [deo for deo in self.request.GET.getlist('zahtev') if deo.isdigit()]
        stavke = visible_zahtevi(self.request.user).filter(pk__in=oznake).prefetch_related('dani')
        ctx = super().get_context_data(**kwargs)
        ctx.update(dokumenti=[dokument_zahteva_za_prikaz(zahtev) for zahtev in stavke],
            naslov=f'Zahtevi ({len(oznake)})', dokument_sablon='hr/resenja/_zahtev_document.html')
        return ctx


@login_required
@role_permission_required()
@require_POST
def zahtev_podnesi(request, pk):
    zahtev = get_object_or_404(visible_zahtevi(request.user).prefetch_related('dani'), pk=pk)
    try:
        podnesi_zahtev(zahtev, request.user)
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, 'Zahtev je podnet i tekst je zaključan.')
    return redirect('hr:zahtev_detail', pk=pk)


@login_required
@role_permission_required()
@require_POST
def zahtev_storniraj(request, pk):
    zahtev = get_object_or_404(visible_zahtevi(request.user), pk=pk)
    try:
        storniraj_zahtev(zahtev, request.user)
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, 'Zahtev je storniran. Njegov broj se ne koristi ponovo.')
    return redirect('hr:zahtev_detail', pk=pk)


@login_required
@role_permission_required()
@require_POST
def zahtev_resenje_create(request, pk):
    """Nacrt rešenja iz jednog zahteva; posle toga se otvara izmena nacrta."""
    zahtev = get_object_or_404(visible_zahtevi(request.user), pk=pk)
    form = ResenjaIzZahtevaForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Proverite datum rešenja i potpisnika.')
        return redirect('hr:zahtev_detail', pk=pk)
    try:
        resenje = napravi_resenje(zahtev, request.user, vrsta=form.cleaned_data['vrsta'],
            datum_resenja=form.cleaned_data['datum_resenja'], potpisnik=form.cleaned_data['potpisnik'])
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
        return redirect('hr:zahtev_detail', pk=pk)
    messages.success(request, f'Napravljen je nacrt rešenja {resenje.broj}. Proverite tekst i izdajte rešenje.')
    return redirect('hr:resenje_detail', pk=resenje.pk)


@login_required
@role_permission_required()
@require_POST
def zahtev_bulk_resenja(request):
    """Nacrti rešenja za označene zahteve. Zahtev koji već ima rešenje se preskače."""
    form = ResenjaIzZahtevaForm(request.POST)
    oznake = [deo for deo in request.POST.getlist('zahtev') if deo.isdigit()]
    if not oznake:
        messages.error(request, 'Označite bar jedan zahtev.')
        return redirect('hr:zahtev_list')
    if not form.is_valid():
        messages.error(request, 'Proverite datum rešenja i potpisnika.')
        return redirect('hr:zahtev_list')
    napravljeno, preskoceno = [], []
    with transaction.atomic():
        for zahtev in visible_zahtevi(request.user).filter(pk__in=oznake).order_by('redni_broj'):
            if zahtev.status == Zahtev.Status.STORNIRAN or zahtev.resenja.exists():
                preskoceno.append(zahtev.broj)
                continue
            try:
                napravljeno.append(napravi_resenje(zahtev, request.user, vrsta=form.cleaned_data['vrsta'],
                    datum_resenja=form.cleaned_data['datum_resenja'], potpisnik=form.cleaned_data['potpisnik']))
            except ValidationError:
                preskoceno.append(zahtev.broj)
    if napravljeno:
        messages.success(request, f'Napravljeno {len(napravljeno)} nacrta rešenja.')
    if preskoceno:
        messages.warning(request, 'Preskočeni zahtevi (storniran, već ima rešenje ili nema vrstu rešenja): '
                         + ', '.join(preskoceno))
    return redirect(reverse('hr:resenje_list') + f'?status={Resenje.Status.NACRT}')


@login_required
@role_permission_required('hr:zahtev_create')
def zahtev_predlog(request):
    """Predlog imena, OJ i radnog mesta za izabranog zaposlenog i pismo."""
    employee = _zaposleni_u_obuhvatu(request.user).filter(pk=request.GET.get('zaposleni')).first()
    if employee is None:
        return JsonResponse({'zaposleni_tekst': '', 'oj_naziv': ''})
    return JsonResponse(predlog_teksta(employee, request.GET.get('pismo') or Pismo.CIRILICA))


class ZahtevBulkCreateView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/zahtev_bulk.html'

    def zaposleni(self):
        centar = self.request.GET.get('centar') or self.request.POST.get('centar') or ''
        qs = _zaposleni_u_obuhvatu(self.request.user).order_by('last_name', 'first_name')
        if centar:
            qs = qs.filter(pk__in=visible_employees(self.request.user, extra_centers=[centar]))
        return centar, qs

    def get_context_data(self, **kwargs):
        centar, zaposleni = self.zaposleni()
        form = kwargs.pop('form', None) or GrupniZahtevForm(initial={'pismo': Pismo.CIRILICA})
        ctx = super().get_context_data(**kwargs)
        selected = set(self.request.POST.getlist('zaposleni'))
        ctx.update(title='Grupni unos zahteva', sidebar_template=SIDEBAR, form=form, zaposleni=zaposleni,
            employee_rows=[{'employee': employee, 'selected': str(employee.pk) in selected} for employee in zaposleni],
            izabran_centar=centar, vrste_meta=_vrste_meta(),
            centri=sorted({kod for kod in OrganizationalUnit.objects.values_list('center', flat=True) if kod}))
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = GrupniZahtevForm(request.POST)
        oznake = [deo for deo in request.POST.getlist('zaposleni') if deo.isdigit()]
        if not form.is_valid() or not oznake:
            if not oznake:
                messages.error(request, 'Izaberi bar jednog zaposlenog.')
            return self.render_to_response(self.get_context_data(form=form))
        data = form.cleaned_data
        _, dostupni = self.zaposleni()
        izabrani = list(dostupni.filter(pk__in=oznake))
        if len(izabrani) != len(set(oznake)):
            messages.error(request, 'Izbor sadrži zaposlene van dozvoljenog obuhvata.')
            return self.render_to_response(self.get_context_data(form=form))
        napravljeno = []
        for employee in izabrani:
            zahtev = Zahtev(vrsta=data['vrsta'], zaposleni=employee, datum_zahteva=data['datum_zahteva'],
                pismo=data['pismo'], datum_od=data['datum_od'], datum_do=data['datum_do'],
                vreme_od=data['vreme_od'], vreme_do=data['vreme_do'], do_zavrsetka_posla=data['do_zavrsetka_posla'],
                broj_radnih_dana=data['broj_radnih_dana'], datum_povratka=data['datum_povratka'],
                razlog=data['razlog'], dodatni_podaci=data['dodatni_podaci'], podnosilac=data['podnosilac'],
                podnosilac_funkcija=data['podnosilac_funkcija'], odobrava=data['odobrava'],
                odobrava_funkcija=data['odobrava_funkcija'] or '', created_by=request.user)
            pripremi_zahtev(zahtev)
            dodeli_broj(zahtev)
            zahtev.save()
            ZahtevDan.objects.bulk_create([ZahtevDan(zahtev=zahtev, datum=dan,
                vrsta_dana=data['vrsta_dana'] or ZahtevDan._meta.get_field('vrsta_dana').default) for dan in data['dani']])
            napravljeno.append(zahtev)
        prvi, poslednji = napravljeno[0].broj, napravljeno[-1].broj
        messages.success(request, f'Napravljeno {len(napravljeno)} zahteva ({prvi}' +
                         (f' – {poslednji})' if len(napravljeno) > 1 else ')') + '.')
        return redirect(reverse('hr:zahtev_list') + f'?status={Zahtev.Status.NACRT}')
