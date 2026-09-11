from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404,redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.http import Http404

from core.mixins import RolePermissionRequiredMixin,user_has_role_permission
from hr.models import RecipientType,WorkTimeCategory,WorkTimeElement


CATALOGS={
    'recipients':(RecipientType,['code','name','is_active'],'Vrsta primaoca'),
    'categories':(WorkTimeCategory,['code','name','employee_selectable','is_active','sort_order'],'Vrsta rada / odsustva'),
    'elements':(WorkTimeElement,['recipient_type','category','payroll_code','payroll_name','is_active'],'Element radne liste'),
}


class WorkTimeCatalogView(LoginRequiredMixin,RolePermissionRequiredMixin,TemplateView):
    template_name='hr/work_time_catalog.html'

    def get_context_data(self,**kwargs):
        ctx=super().get_context_data(**kwargs)
        ctx.update(title='Elementi radne liste',sidebar_template='sidebar_kadrovi.html',
            recipients=RecipientType.objects.all(),categories=WorkTimeCategory.objects.all(),
            elements=WorkTimeElement.objects.select_related('recipient_type','category').all(),
            can_create=user_has_role_permission(self.request.user,'hr:work_time_catalog_create'),
            can_edit=user_has_role_permission(self.request.user,'hr:work_time_catalog_edit'))
        return ctx


class WorkTimeCatalogEditView(LoginRequiredMixin,RolePermissionRequiredMixin,TemplateView):
    template_name='hr/work_time_catalog_form.html'

    def get_form(self,data=None):
        kind=self.kwargs['kind']
        if kind not in CATALOGS:raise Http404
        model,fields,label=CATALOGS[kind]
        instance=get_object_or_404(model,pk=self.kwargs['pk']) if 'pk' in self.kwargs else None
        form_type=forms.modelform_factory(model,fields=fields)
        form=form_type(data=data,instance=instance)
        for name,field in form.fields.items():
            if isinstance(field,forms.BooleanField):field.widget.attrs['class']='form-check-input'
            elif isinstance(field,forms.ModelChoiceField):field.widget.attrs['class']='form-select select2-method'
            else:field.widget.attrs['class']='form-control'
        if instance and 'code' in form.fields:form.fields['code'].disabled=True
        return form,label

    def get_context_data(self,**kwargs):
        form=kwargs.pop('form',None)
        ctx=super().get_context_data(**kwargs)
        if form is None:form,label=self.get_form()
        else:label=CATALOGS[self.kwargs['kind']][2]
        ctx.update(form=form,title=label,sidebar_template='sidebar_kadrovi.html')
        return ctx

    @transaction.atomic
    def post(self,request,*args,**kwargs):
        form,_=self.get_form(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'Šifrarnik je sačuvan.')
            return redirect(reverse('hr:work_time_catalog')+'#'+self.kwargs['kind'])
        return self.render_to_response(self.get_context_data(form=form))
