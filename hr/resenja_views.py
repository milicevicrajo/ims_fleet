from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from core.models import OrganizationalUnit
from hr.models import Employee, Pismo, Potpisnik, Resenje, ResenjeDan, VrstaResenja
from hr.resenja_forms import (GrupnoResenjeForm, PotpisnikForm, ResenjeDanFormSet, ResenjeForm,
    VrstaResenjaForm, predlog_teksta)
from hr.services.resenja import (dokument_za_prikaz, dozvoljeni_centri, izdaj_resenje,
    pripremi_resenje, storniraj_resenje, visible_resenja)

SIDEBAR = 'sidebar_kadrovi.html'


def _vrste_meta():
    """Podaci o vrstama koje forma koristi da sakrije polja koja se ne traže."""
    return {str(vrsta.pk): {'period': vrsta.trazi_period, 'dani': vrsta.trazi_dane,
        'radni_dani': vrsta.trazi_radne_dane, 'pismo': vrsta.podrazumevano_pismo}
        for vrsta in VrstaResenja.objects.filter(je_aktivna=True)}


def _broj_dana(formset):
    """Koliko dana ostaje posle brisanja, bez upita u bazu."""
    return sum(1 for podaci in formset.cleaned_data
               if podaci and podaci.get('datum') and not podaci.get('DELETE'))


def _dozvole(user):
    return {kod: user_has_role_permission(user, 'hr:' + kod) for kod in
            ('resenje_create', 'resenje_bulk_create', 'resenje_catalog', 'resenje_izdaj')}


class ResenjeListView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = visible_resenja(self.request.user).prefetch_related('dani')
        vrsta = self.request.GET.get('vrsta') or ''
        centar = self.request.GET.get('centar') or ''
        status = self.request.GET.get('status') or ''
        godina = self.request.GET.get('godina') or ''
        if vrsta.isdigit():
            qs = qs.filter(vrsta_id=int(vrsta))
        if centar:
            qs = qs.filter(centar=centar)
        if status:
            qs = qs.filter(status=status)
        if godina.isdigit():
            qs = qs.filter(datum_resenja__year=int(godina))
        ctx.update(title='Rešenja zaposlenih', sidebar_template=SIDEBAR, resenja=qs[:1000],
            vrste=VrstaResenja.objects.all(), statusi=Resenje.Status.choices,
            centri=sorted({kod for kod in OrganizationalUnit.objects.values_list('center', flat=True) if kod}),
            izabrana_vrsta=vrsta, izabran_centar=centar, izabran_status=status, izabrana_godina=godina,
            **_dozvole(self.request.user))
        return ctx


class ResenjeFormView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_form.html'

    def get_object(self):
        if 'pk' not in self.kwargs:
            return None
        resenje = get_object_or_404(visible_resenja(self.request.user), pk=self.kwargs['pk'])
        if resenje.je_zakljucano:
            raise Http404('Izdato rešenje se ne menja.')
        return resenje

    def get_context_data(self, **kwargs):
        resenje = kwargs.pop('instance', None) or self.get_object()
        form = kwargs.pop('form', None) or ResenjeForm(instance=resenje)
        formset = kwargs.pop('formset', None) or ResenjeDanFormSet(instance=resenje)
        ctx = super().get_context_data(**kwargs)
        ctx.update(title='Izmena rešenja' if resenje else 'Novo rešenje', sidebar_template=SIDEBAR,
            form=form, formset=formset, resenje=resenje, vrste_meta=_vrste_meta())
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        resenje = self.get_object()
        form = ResenjeForm(request.POST, instance=resenje)
        if not form.is_valid():
            formset = ResenjeDanFormSet(request.POST, instance=resenje)
            formset.is_valid()
            return self.render_to_response(self.get_context_data(form=form, formset=formset, instance=resenje))
        novo = form.save(commit=False)
        if resenje is None:
            novo.created_by = request.user
        pripremi_resenje(novo)
        formset = ResenjeDanFormSet(request.POST, instance=novo)
        # Broj dana se proverava pre snimanja: posle `set_rollback` nijedan upit ne bi prošao.
        if formset.is_valid() and novo.vrsta.trazi_dane and not _broj_dana(formset):
            form.add_error(None, 'Ova vrsta rešenja traži bar jedan dan.')
        if not formset.is_valid() or form.errors:
            return self.render_to_response(self.get_context_data(form=form, formset=formset, instance=resenje))
        novo.save()
        formset.instance = novo
        formset.save()
        messages.success(request, 'Rešenje je sačuvano kao nacrt.')
        return redirect('hr:resenje_detail', pk=novo.pk)


class ResenjeDetailView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_detail.html'

    def get_context_data(self, **kwargs):
        resenje = get_object_or_404(visible_resenja(self.request.user).prefetch_related('dani'), pk=self.kwargs['pk'])
        ctx = super().get_context_data(**kwargs)
        ctx.update(title=f'Rešenje {resenje.broj}', sidebar_template=SIDEBAR, resenje=resenje,
            dokument=dokument_za_prikaz(resenje), **_dozvole(self.request.user))
        return ctx


class ResenjePrintView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_print.html'

    def get_context_data(self, **kwargs):
        resenje = get_object_or_404(visible_resenja(self.request.user).prefetch_related('dani'), pk=self.kwargs['pk'])
        ctx = super().get_context_data(**kwargs)
        ctx.update(dokumenti=[dokument_za_prikaz(resenje)], naslov=f'Rešenje {resenje.broj}')
        return ctx


class ResenjeBulkPrintView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_print.html'

    def get_context_data(self, **kwargs):
        oznake = [deo for deo in self.request.GET.getlist('resenje') if deo.isdigit()]
        stavke = visible_resenja(self.request.user).filter(pk__in=oznake).prefetch_related('dani')
        ctx = super().get_context_data(**kwargs)
        ctx.update(dokumenti=[dokument_za_prikaz(resenje) for resenje in stavke],
            naslov=f'Rešenja ({len(oznake)})')
        return ctx


@login_required
@role_permission_required()
@require_POST
def resenje_izdaj(request, pk):
    resenje = get_object_or_404(visible_resenja(request.user).prefetch_related('dani'), pk=pk)
    try:
        izdaj_resenje(resenje, request.user)
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, 'Rešenje je izdato i tekst je zaključan.')
    return redirect('hr:resenje_detail', pk=pk)


@login_required
@role_permission_required()
@require_POST
def resenje_storniraj(request, pk):
    resenje = get_object_or_404(visible_resenja(request.user), pk=pk)
    try:
        storniraj_resenje(resenje, request.user)
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, 'Rešenje je stornirano.')
    return redirect('hr:resenje_detail', pk=pk)


@login_required
@role_permission_required()
@require_POST
def resenje_obrisi(request, pk):
    resenje = get_object_or_404(visible_resenja(request.user), pk=pk)
    if resenje.je_zakljucano:
        messages.error(request, 'Izdato rešenje se ne briše, nego stornira.')
        return redirect('hr:resenje_detail', pk=pk)
    resenje.delete()
    messages.success(request, 'Nacrt rešenja je obrisan.')
    return redirect('hr:resenje_list')


@login_required
@role_permission_required('hr:resenje_create')
def resenje_predlog(request):
    """Predlog imena i organizacione jedinice za izabranog zaposlenog i pismo."""
    employee = Employee.objects.filter(pk=request.GET.get('zaposleni')).first()
    if employee is None:
        return JsonResponse({'zaposleni_tekst': '', 'oj_naziv': ''})
    pismo = request.GET.get('pismo') or Pismo.CIRILICA
    return JsonResponse(predlog_teksta(employee, pismo))


class ResenjeBulkCreateView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_bulk.html'

    def zaposleni(self):
        centar = self.request.GET.get('centar') or self.request.POST.get('centar') or ''
        qs = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        dozvoljeni = dozvoljeni_centri(self.request.user)
        centri = [centar] if centar else dozvoljeni
        if not self.request.user.is_superuser and dozvoljeni:
            centri = [kod for kod in centri if kod in dozvoljeni] or dozvoljeni
        if centri:
            kodovi = OrganizationalUnit.objects.filter(center__in=centri).values_list('code', flat=True)
            qs = qs.filter(org_unit_code__in=list(kodovi))
        return centar, qs

    def get_context_data(self, **kwargs):
        centar, zaposleni = self.zaposleni()
        form = kwargs.pop('form', None) or GrupnoResenjeForm(initial={'pismo': Pismo.CIRILICA})
        ctx = super().get_context_data(**kwargs)
        selected = set(self.request.POST.getlist('zaposleni'))
        employee_rows = [{'employee': employee, 'selected': str(employee.pk) in selected,
                          'broj': self.request.POST.get(f'broj_{employee.pk}', '')}
                         for employee in zaposleni]
        ctx.update(title='Grupno izdavanje rešenja', sidebar_template=SIDEBAR, form=form, zaposleni=zaposleni,
            employee_rows=employee_rows,
            izabran_centar=centar, vrste_meta=_vrste_meta(),
            centri=sorted({kod for kod in OrganizationalUnit.objects.values_list('center', flat=True) if kod}))
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = GrupnoResenjeForm(request.POST)
        oznake = [deo for deo in request.POST.getlist('zaposleni') if deo.isdigit()]
        if not form.is_valid() or not oznake:
            if not oznake:
                messages.error(request, 'Izaberi bar jednog zaposlenog.')
            return self.render_to_response(self.get_context_data(form=form))
        data = form.cleaned_data
        _, dostupni = self.zaposleni()
        izabrani = list(dostupni.filter(pk__in=oznake))
        # Samo `broj_<pk>`; polje forme `broj_radnih_dana` ima isti početak i ne sme da uđe ovde.
        brojevi = {kljuc[len('broj_'):]: vrednost.strip() for kljuc, vrednost in request.POST.items()
                   if kljuc.startswith('broj_') and kljuc[len('broj_'):].isdigit() and vrednost.strip()}
        bez_broja = [str(employee) for employee in izabrani if not brojevi.get(str(employee.pk))]
        if bez_broja:
            messages.error(request, 'Unesi broj iz delovodnika za: ' + ', '.join(bez_broja))
            return self.render_to_response(self.get_context_data(form=form))
        napravljeno = []
        for employee in izabrani:
            resenje = Resenje(zaposleni=employee, vrsta=data['vrsta'], broj=brojevi[str(employee.pk)],
                datum_resenja=data['datum_resenja'], pismo=data['pismo'], datum_od=data['datum_od'],
                datum_do=data['datum_do'], do_zavrsetka_posla=data['do_zavrsetka_posla'],
                broj_radnih_dana=data['broj_radnih_dana'], datum_povratka=data['datum_povratka'],
                zahtev_broj=data['zahtev_broj'], zahtev_datum=data['zahtev_datum'],
                napomena=data['napomena'], created_by=request.user)
            pripremi_resenje(resenje)
            resenje.save()
            for dan in data['dani']:
                ResenjeDan.objects.create(resenje=resenje, datum=dan,
                    vrsta_dana=data['vrsta_dana'] or ResenjeDan.VrstaDana.PREKOVREMENI)
            napravljeno.append(resenje)
        messages.success(request, f'Napravljeno {len(napravljeno)} nacrta rešenja.')
        return redirect(reverse('hr:resenje_list') + f'?status={Resenje.Status.NACRT}')


CATALOGS = {'vrste': (VrstaResenja, VrstaResenjaForm, 'Vrsta rešenja'),
            'potpisnici': (Potpisnik, PotpisnikForm, 'Potpisnik rešenja')}


class ResenjeCatalogView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_catalog.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title='Šifrarnik rešenja', sidebar_template=SIDEBAR,
            vrste=VrstaResenja.objects.all(), potpisnici=Potpisnik.objects.select_related('zaposleni'))
        return ctx


class ResenjeCatalogEditView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_catalog_form.html'

    def get_form(self, data=None):
        kind = self.kwargs['kind']
        if kind not in CATALOGS:
            raise Http404
        model, form_type, label = CATALOGS[kind]
        instance = get_object_or_404(model, pk=self.kwargs['pk']) if 'pk' in self.kwargs else None
        return form_type(data=data, instance=instance), label

    def get_context_data(self, **kwargs):
        form = kwargs.pop('form', None)
        ctx = super().get_context_data(**kwargs)
        if form is None:
            form, label = self.get_form()
        else:
            label = CATALOGS[self.kwargs['kind']][2]
        ctx.update(form=form, title=label, sidebar_template=SIDEBAR, kind=self.kwargs['kind'])
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form, _ = self.get_form(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Šifrarnik je sačuvan.')
            return redirect(reverse('hr:resenje_catalog') + '#' + self.kwargs['kind'])
        return self.render_to_response(self.get_context_data(form=form))
