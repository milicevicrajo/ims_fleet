from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import FormView, ListView

from core.mixins import RolePermissionRequiredMixin, user_has_role_permission
from hr.access import scope_employee_records
from .models import SickLeave, SickLeaveImport
from .services.sick_leave import import_rfzo_workbook


class SickLeaveImportForm(forms.Form):
    source_date = forms.DateField(label='Datum RFZO izvoza', initial=timezone.localdate,
        input_formats=['%Y-%m-%d','%d.%m.%Y'],
        widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date','class':'form-control'}))
    file = forms.FileField(label='RFZO Excel datoteka',
        widget=forms.FileInput(attrs={'accept':'.xlsx','class':'form-control'}))

    def clean_source_date(self):
        value=self.cleaned_data['source_date']
        if value>timezone.localdate():
            raise forms.ValidationError('Datum izvoza ne može biti u budućnosti.')
        return value

    def clean_file(self):
        file=self.cleaned_data['file']
        if not file.name.lower().endswith('.xlsx'):
            raise forms.ValidationError('Izaberite RFZO Excel u .xlsx formatu.')
        if file.size>10*1024*1024:
            raise forms.ValidationError('Datoteka može imati najviše 10 MB.')
        return file


class SickLeaveListView(LoginRequiredMixin, RolePermissionRequiredMixin, ListView):
    model=SickLeave
    template_name='hr/sick_leave_list.html'
    context_object_name='sick_leaves'

    def get_queryset(self):
        qs=scope_employee_records(SickLeave.objects.select_related('employee'), self.request.user)
        q=self.request.GET.get('q','').strip()
        if q:
            qs=qs.filter(Q(employee__first_name__icontains=q)|Q(employee__last_name__icontains=q)|Q(rfzo_id__icontains=q))
        if self.request.GET.get('unlinked')=='1': qs=qs.filter(employee__isnull=True)
        year=self.request.GET.get('year','')
        if year.isdigit() and 1900<=int(year)<=2100:
            qs=qs.filter(start_date__year__lte=int(year)).filter(Q(end_date__year__gte=int(year))|Q(end_date__isnull=True))
        return qs

    def get_context_data(self, **kwargs):
        ctx=super().get_context_data(**kwargs)
        ctx.update(title='Bolovanja',sidebar_template='sidebar_kadrovi.html',
            total_count=scope_employee_records(SickLeave.objects.all(), self.request.user).count(),
            unlinked_count=scope_employee_records(SickLeave.objects.all(), self.request.user).filter(employee__isnull=True).count(),
            last_batch=SickLeaveImport.objects.first(),query=self.request.GET.get('q',''),
            selected_year=self.request.GET.get('year',''),
            can_view_employee=user_has_role_permission(self.request.user,'employee_detail'),
            can_import=user_has_role_permission(self.request.user,'hr:sick_leave_import'))
        return ctx


class SickLeaveImportView(LoginRequiredMixin, RolePermissionRequiredMixin, FormView):
    template_name='hr/sick_leave_import.html'
    form_class=SickLeaveImportForm

    def get_context_data(self, **kwargs):
        ctx=super().get_context_data(**kwargs)
        ctx.update(title='Uvoz bolovanja iz RFZO',sidebar_template='sidebar_kadrovi.html')
        return ctx

    def form_valid(self, form):
        file=form.cleaned_data['file']
        try:
            batch=import_rfzo_workbook(file.read(),filename=file.name,
                source_date=form.cleaned_data['source_date'],user=self.request.user)
        except ValidationError as exc:
            form.add_error(None,exc)
            return self.form_invalid(form)
        except IntegrityError:
            form.add_error(None,'Istovremeno je izvršen drugi uvoz. Ponovite uvoz datoteke.')
            return self.form_invalid(form)
        messages.success(self.request,f'Uvoz završen: {batch.created_count} novih, {batch.updated_count} ažuriranih, {batch.unchanged_count} bez promene.')
        if batch.unlinked_count:
            messages.warning(self.request,f'{batch.unlinked_count} bolovanja nije povezano sa zaposlenim. Proverite JMBG u kadrovskoj evidenciji i ponovite uvoz; podaci su sačuvani.')
        if user_has_role_permission(self.request.user,'hr:sick_leave_list'):
            return redirect('hr:sick_leave_list')
        return redirect('hr:sick_leave_import')
