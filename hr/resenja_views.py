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
from hr.access import visible_employees
from hr.models import BrojacZahteva, Employee, Pismo, Potpisnik, Resenje, ResenjeDan, VrstaResenja, VrstaZahteva
from hr.resenja_forms import (PotpisnikForm, ResenjeDanFormSet, ResenjeForm,
    VrstaResenjaForm, predlog_teksta)
from hr.services.resenja import (dodatna_polja, dokument_za_prikaz, dozvoljeni_centri, izdaj_resenje,
    pripremi_resenje, storniraj_resenje, visible_resenja)
from hr.zahtevi_forms import BrojacZahtevaForm, VrstaZahtevaForm

SIDEBAR = 'sidebar_kadrovi.html'


def _potpisnici_meta():
    return [{'id': p.pk, 'ime': str(p), 'od': p.vazi_od.isoformat(),
             'do': p.vazi_do.isoformat() if p.vazi_do else ''}
            for p in Potpisnik.objects.select_related('zaposleni').order_by('-vazi_od', 'pk')]


def _vrste_meta():
    """Podaci o vrstama koje forma koristi da sakrije polja koja se ne traže."""
    return {str(vrsta.pk): {'period': True, 'dani': vrsta.trazi_dane, 'kod': vrsta.kod,
        'vreme': not vrsta.trazi_radne_dane,
        'radni_dani': vrsta.trazi_radne_dane, 'pismo': vrsta.podrazumevano_pismo,
        'polja': [oznaka for oznaka, _ in dodatna_polja(vrsta)]}
        for vrsta in VrstaResenja.objects.filter(je_aktivna=True)}


def _broj_dana(formset):
    """Koliko dana ostaje posle brisanja, bez upita u bazu."""
    return sum(1 for podaci in formset.cleaned_data
               if podaci and podaci.get('datum') and not podaci.get('DELETE'))


def _dozvole(user):
    return {kod: user_has_role_permission(user, 'hr:' + kod) for kod in
            ('resenje_create', 'resenje_bulk_create', 'resenje_catalog', 'resenje_izdaj', 'zahtev_resenje_create')}


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

    def get(self, request, *args, **kwargs):
        if 'pk' not in kwargs:
            return redirect(reverse('hr:zahtev_list') + '?resenje=bez')
        return super().get(request, *args, **kwargs)

    def get_object(self):
        if 'pk' not in self.kwargs:
            return None
        resenje = get_object_or_404(visible_resenja(self.request.user), pk=self.kwargs['pk'])
        if resenje.je_zakljucano:
            raise Http404('Izdato rešenje se ne menja.')
        return resenje

    def get_context_data(self, **kwargs):
        resenje = kwargs.pop('instance', None) or self.get_object()
        form = kwargs.pop('form', None) or ResenjeForm(instance=resenje, actor=self.request.user)
        form.fields['zaposleni'].queryset = visible_employees(self.request.user,
            unrestricted=user_has_role_permission(self.request.user, 'hr:resenje_view_all')).filter(is_active=True)
        formset = kwargs.pop('formset', None) or ResenjeDanFormSet(instance=resenje)
        ctx = super().get_context_data(**kwargs)
        ctx.update(title='Izmena rešenja' if resenje else 'Novo rešenje', sidebar_template=SIDEBAR,
            form=form, formset=formset, resenje=resenje, vrste_meta=_vrste_meta(),
            potpisnici_meta=_potpisnici_meta(), can_add_signer=form.can_add_signer,
            submit_button_label='Sačuvaj nacrt',
            cancel_url=reverse('hr:resenje_detail', args=[resenje.pk]) if resenje else reverse('hr:resenje_list'))
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if 'pk' not in kwargs:
            messages.info(request, 'Izaberite postojeći zahtev i kliknite „Dodaj rešenje“.')
            return redirect(reverse('hr:zahtev_list') + '?resenje=bez')
        resenje = self.get_object()
        form = ResenjeForm(request.POST, instance=resenje, actor=request.user)
        form.fields['zaposleni'].queryset = visible_employees(request.user,
            unrestricted=user_has_role_permission(request.user, 'hr:resenje_view_all')).filter(is_active=True)
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
        if formset.is_valid() and novo.vrsta.trazi_dane and not _broj_dana(formset) and (not novo.datum_od or novo.vrsta.kod == 'praznik'):
            form.add_error(None, 'Ova vrsta rešenja traži bar jedan dan.')
        if not formset.is_valid() or form.errors:
            return self.render_to_response(self.get_context_data(form=form, formset=formset, instance=resenje))
        form.postavi_potpisnika(novo)
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
    employee = visible_employees(request.user,
        unrestricted=user_has_role_permission(request.user, 'hr:resenje_view_all')).filter(pk=request.GET.get('zaposleni')).first()
    if employee is None:
        return JsonResponse({'zaposleni_tekst': '', 'oj_naziv': ''})
    pismo = request.GET.get('pismo') or Pismo.CIRILICA
    return JsonResponse(predlog_teksta(employee, pismo))


class ResenjeBulkCreateView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    """Stari link vodi na izbor postojećih zahteva za grupno pravljenje rešenja."""

    def get(self, request, *args, **kwargs):
        return redirect(reverse('hr:zahtev_list') + '?resenje=bez')

    def post(self, request, *args, **kwargs):
        messages.info(request, 'Označite postojeće zahteve za koje pravite rešenja.')
        return self.get(request, *args, **kwargs)


CATALOGS = {'vrste': (VrstaResenja, VrstaResenjaForm, 'Vrsta rešenja'),
            'potpisnici': (Potpisnik, PotpisnikForm, 'Potpisnik rešenja'),
            'vrste-zahteva': (VrstaZahteva, VrstaZahtevaForm, 'Vrsta zahteva'),
            'brojaci': (BrojacZahteva, BrojacZahtevaForm, 'Brojač zahteva')}


class ResenjeCatalogView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/resenja/resenje_catalog.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title='Šifrarnik rešenja', sidebar_template=SIDEBAR,
            vrste=VrstaResenja.objects.all(), potpisnici=Potpisnik.objects.select_related('zaposleni'),
            vrste_zahteva=VrstaZahteva.objects.select_related('vrsta_resenja'), brojaci=BrojacZahteva.objects.all())
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
        ctx.update(form=form, title=('Izmena · ' if form.instance.pk else 'Dodavanje · ') + label, section_title=label,
            submit_button_label='Sačuvaj', cancel_url=reverse('hr:resenje_catalog') + '#' + self.kwargs['kind'],
            sidebar_template=SIDEBAR, kind=self.kwargs['kind'])
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form, _ = self.get_form(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Šifrarnik je sačuvan.')
            return redirect(reverse('hr:resenje_catalog') + '#' + self.kwargs['kind'])
        return self.render_to_response(self.get_context_data(form=form))
