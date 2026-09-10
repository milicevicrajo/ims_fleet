import datetime
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError
from django.http import HttpResponseBadRequest, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, UpdateView

from core.mixins import RolePermissionRequiredMixin
from ..forms.onboarding import VehicleIdentityForm, VehicleBasisForm, VehicleTechnicalForm, OnboardingTrafficCardForm, VehicleAssignmentForm, VehicleHoldingForm
from ..models import Vehicle, VehicleHolding
from ..services.vehicle_onboarding import create_vehicle_from_steps


STEPS = [
    ('Identifikacija', VehicleIdentityForm),
    ('Osnov korišćenja', VehicleBasisForm),
    ('Tehnički podaci', VehicleTechnicalForm),
    ('Saobraćajna', OnboardingTrafficCardForm),
    ('Raspoređivanje', VehicleAssignmentForm),
]
STORAGE = FileSystemStorage(location=Path(tempfile.gettempdir()) / 'ims_fleet_vehicle_wizard')
TTL = 2 * 60 * 60
FILE_FIELDS_BY_STEP = {0: ['photo'], 3: ['traffic_card_pdf', 'traffic_card_front_image', 'traffic_card_back_image']}
logger = logging.getLogger(__name__)


def clear_draft_files(draft):
    for item in draft.get('files', {}).values():
        try:
            STORAGE.delete(item['path'])
        except OSError:
            logger.warning('Privremeni prilog će biti uklonjen naknadnim čišćenjem.', exc_info=True)


class VehicleOnboardingView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = 'vehicle_create'

    def dispatch(self, request, *args, **kwargs):
        self.open_files = []
        try:
            return super().dispatch(request, *args, **kwargs)
        finally:
            for handle in self.open_files:
                handle.close()

    def drafts(self):
        drafts = self.request.session.get('vehicle_onboarding', {})
        for key, value in list(drafts.items()):
            if time.time() - value.get('updated', 0) > TTL:
                clear_draft_files(value)
                drafts.pop(key)
        self.request.session['vehicle_onboarding'] = drafts
        return drafts

    def save_draft(self, token, draft):
        draft['updated'] = time.time()
        drafts = self.request.session.get('vehicle_onboarding', {})
        drafts[token] = draft
        self.request.session['vehicle_onboarding'] = drafts
        folder = Path(STORAGE.location) / token
        if folder.is_dir():
            os.utime(folder, None)

    def close_uploads(self):
        for handle in self.open_files:
            handle.close()
        self.open_files = []

    def get(self, request):
        drafts = self.drafts()
        token = request.GET.get('draft')
        if not token:
            token = uuid.uuid4().hex
            # Keep bounded session storage and clean abandoned files.
            while len(drafts) >= 5:
                key = min(drafts, key=lambda key: drafts[key]['updated'])
                clear_draft_files(drafts.pop(key))
            request.session['vehicle_onboarding'] = drafts
            self.save_draft(token, {'steps': {}, 'files': {}, 'step': 0})
            return redirect(f'{reverse("vehicle_create")}?draft={token}')
        draft = drafts.get(token)
        if not draft:
            messages.info(request, 'Privremeni unos je istekao. Pokrenite novi unos vozila.')
            return redirect('vehicle_create')
        if draft.get('vehicle_id'):
            return redirect('vehicle_detail', pk=draft['vehicle_id'])
        return self.show(token, draft)

    def form(self, index, draft, data=None, files=None):
        if data is None and str(index) in draft['steps']:
            data = QueryDict('', mutable=True)
            for key, values in draft['steps'][str(index)].items():
                data.setlist(key, values)
        kwargs = {'data': data}
        if index == 2:
            kwargs['category'] = draft['steps'].get('0', {}).get('category', [''])[0]
        if index in FILE_FIELDS_BY_STEP:
            previous_files = {}
            missing_files = []
            for key, item in draft.get('files', {}).items():
                if key not in FILE_FIELDS_BY_STEP[index]:
                    continue
                if STORAGE.exists(item['path']):
                    handle = STORAGE.open(item['path'])
                    self.open_files.append(handle)
                    from django.core.files.uploadedfile import UploadedFile
                    previous_files[key] = UploadedFile(handle, name=item['name'], size=STORAGE.size(item['path']))
                elif not files or key not in files:
                    missing_files.append(key)
            previous_files.update({key: files[key] for key in files} if files else {})
            kwargs['files'] = previous_files or None
        form = STEPS[index][1](**kwargs)
        if data is not None and ((index == 3 and data.get('add_document')) or (index == 0 and not data.get('remove_photo'))):
            for key in missing_files:
                form.add_error(key, 'Privremeni prilog više nije dostupan. Izaberite datoteku ponovo.')
        if index == 4 and self.request.user.allowed_centers.exists():
            form.fields['organizational_unit'].queryset = form.fields['organizational_unit'].queryset.filter(center__in=self.request.user.allowed_centers.values_list('center', flat=True))
            form.fields['organizational_unit'].required = True
            form.fields['organizational_unit'].help_text = 'Vozilo mora biti raspoređeno u jedan od centara kojima imate pristup.'
        return form

    def show(self, token, draft, form=None, error=None):
        index = draft['step']
        summaries = []
        warnings = []
        if index == 5:
            forms = [self.form(i, draft) for i in range(5)]
            for i, item in enumerate(forms):
                if not item.is_valid():
                    draft['step'] = i
                    self.save_draft(token, draft)
                    return self.show(token, draft, item)
                values = []
                for name, field in item.fields.items():
                    value = item.cleaned_data.get(name)
                    if value is None or value == '':
                        continue
                    if isinstance(value, bool):
                        value = 'Da' if value else 'Ne'
                    elif isinstance(value, datetime.date):
                        value = value.strftime('%d.%m.%Y')
                    elif hasattr(field, 'choices'):
                        value = dict(field.choices).get(value, value)
                    values.append((field.label, str(value)))
                summaries.append((i, STEPS[i][0], values))
            if not forms[3].cleaned_data.get('add_document'):
                warnings.append('Saobraćajna nije uneta; dokumentaciju dodajte na kartici vozila.')
            if not forms[4].cleaned_data.get('organizational_unit'):
                warnings.append('Šifra posla nije dodeljena; troškovi mogu ostati neraspoređeni.')
            if not forms[2].cleaned_data.get('maximum_permissible_weight'):
                warnings.append('Maksimalna masa nije uneta; prag troška po klasi vozila neće biti određen.')
            if forms[1].cleaned_data.get('basis') == 'owned' and forms[1].cleaned_data.get('purchase_value') is None:
                warnings.append('Nabavna vrednost nije uneta; obračun troškova vlasništva nije potpun.')
            if forms[1].cleaned_data.get('financing') == 'credit' and not forms[1].cleaned_data.get('financing_contract'):
                warnings.append('Kredit je označen, ali ugovor o finansiranju još nije povezan.')
        elif form is None:
            form = self.form(index, draft)
        return render(self.request, 'fleet/vehicle_onboarding.html', {'title': 'Dodavanje vozila', 'step': index, 'steps': [s[0] for s in STEPS] + ['Potvrda'], 'draft_token': token, 'form': form, 'summaries': summaries, 'warnings': warnings, 'error': error, 'retained_files': [item['name'] for key, item in draft.get('files', {}).items() if key in FILE_FIELDS_BY_STEP.get(index, [])]})

    def post(self, request):
        token = request.POST.get('draft_token', '')
        draft = self.drafts().get(token)
        if not draft:
            return HttpResponseBadRequest('Unos je istekao. Ponovo otvorite Dodavanje vozila.')
        if draft.get('vehicle_id'):
            return redirect('vehicle_detail', pk=draft['vehicle_id'])
        action = request.POST.get('action', 'next')
        if action == 'cancel':
            clear_draft_files(draft)
            drafts = request.session['vehicle_onboarding']
            drafts.pop(token)
            request.session['vehicle_onboarding'] = drafts
            return redirect('vehicle_list')
        if action.startswith('edit:'):
            try:
                index = int(action.split(':')[1])
            except ValueError:
                return HttpResponseBadRequest()
            if not 0 <= index <= draft['step'] or index >= 5:
                return HttpResponseBadRequest()
            draft['step'] = index
            self.save_draft(token, draft)
            return self.show(token, draft)
        if action == 'back':
            draft['step'] = max(0, draft['step'] - 1)
            self.save_draft(token, draft)
            return self.show(token, draft)
        if str(draft['step']) != request.POST.get('step'):
            return self.show(token, draft, error='Korak je promenjen u drugom prozoru. Proverite prikazani korak.')
        if draft['step'] == 5:
            forms = [self.form(i, draft) for i in range(5)]
            for i, form in enumerate(forms):
                if not form.is_valid():
                    draft['step'] = i
                    self.save_draft(token, draft)
                    return self.show(token, draft, form)
            try:
                vehicle = create_vehicle_from_steps(forms, request.user)
            except (ValidationError, IntegrityError) as exc:
                error = '; '.join(exc.messages) if isinstance(exc, ValidationError) else 'Podaci su u međuvremenu promenjeni ili vozilo već postoji. Proverite šasiju, inventarski broj i zaduženje.'
                return self.show(token, draft, error=error)
            self.close_uploads()
            self.save_draft(token, {'vehicle_id': vehicle.pk, 'files': {}})
            clear_draft_files(draft)
            messages.success(request, 'Vozilo i povezane evidencije su sačuvani. Proverite dokumentaciju pre upotrebe vozila.')
            return redirect('vehicle_detail', pk=vehicle.pk)
        index = draft['step']
        form = self.form(index, draft, request.POST, request.FILES)
        if not form.is_valid():
            return self.show(token, draft, form)
        draft['steps'][str(index)] = {key: request.POST.getlist(key) for key in form.fields if key not in request.FILES}
        if index in FILE_FIELDS_BY_STEP:
            self.close_uploads()
            remove = (index == 3 and not form.cleaned_data.get('add_document')) or (index == 0 and form.cleaned_data.get('remove_photo'))
            if remove:
                for key in FILE_FIELDS_BY_STEP[index]:
                    old = draft['files'].pop(key, None)
                    if old:
                        STORAGE.delete(old['path'])
            else:
                for key in FILE_FIELDS_BY_STEP[index]:
                    if key in request.FILES:
                        old = draft['files'].get(key)
                        if old:
                            STORAGE.delete(old['path'])
                        upload = request.FILES[key]
                        upload.seek(0)
                        path = STORAGE.save(f'{token}/{uuid.uuid4().hex}', upload)
                        draft['files'][key] = {'path': path, 'name': Path(upload.name).name}
            if index == 0:
                draft['steps']['0'].pop('remove_photo', None)
        draft['step'] += 1
        self.save_draft(token, draft)
        return redirect(f'{reverse("vehicle_create")}?draft={token}')


class HoldingViewMixin(RolePermissionRequiredMixin, LoginRequiredMixin):
    required_permission_code = 'vehicle_update'
    model = VehicleHolding
    form_class = VehicleHoldingForm
    template_name = 'fleet/generic_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        vehicle = get_object_or_404(Vehicle, pk=self.kwargs['vehicle_id'])
        assignment = vehicle.job_codes.filter(assigned_date__lte=timezone.localdate()).select_related('organizational_unit').order_by('-assigned_date', '-id').first()
        if self.request.user.allowed_centers.exists() and assignment and assignment.organizational_unit and not self.request.user.allowed_centers.filter(center=assignment.organizational_unit.center).exists():
            raise PermissionDenied('Nemate pristup ovom vozilu.')
        kwargs['vehicle'] = vehicle
        return kwargs

    def get_queryset(self):
        return super().get_queryset().filter(vehicle_id=self.kwargs['vehicle_id'])

    def form_valid(self, form):
        try:
            self.object = form.save()
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect('vehicle_detail', pk=self.object.vehicle_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(title='Osnov raspolaganja vozilom', form_help='Za promenu osnova najpre završite prethodni period, zatim dodajte novi. Istek ugovora ne znači prelazak u vlasništvo IMS.')
        return context


class VehicleHoldingCreateView(HoldingViewMixin, CreateView):
    pass


class VehicleHoldingUpdateView(HoldingViewMixin, UpdateView):
    pass
