import copy
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, user_has_role_permission
from hr.evaluation_forms import EvaluationHeaderForm, EvaluationValuesForm, EvaluationApprovalForm, CoefficientField, style_form
from hr.models import (Employee, EvaluationGroup, EvaluationCriterion, EvaluationScale, EvaluationUnitSetup,
    EvaluationEmployeeSetup, EmployeeEvaluation)
from hr.services.evaluations import (visible_evaluations, editable_employees, build_snapshot, sign_snapshot,
    read_snapshot, save_evaluation, approval_state, approve_evaluation, STAGES, MONTHS)


def decorate_evaluation(item):
    approvals, coefficient = approval_state(item)
    item.final_coefficient = coefficient
    item.approval_rows = [{'stage':stage,'name':item.snapshot['reviewers'][stage]['name'],'approval':approvals.get(stage)} for stage in STAGES]
    item.is_final = all(stage in approvals for stage in STAGES)
    item.month_name = MONTHS[item.month-1]
    return item


class EvaluationListView(LoginRequiredMixin, TemplateView):
    template_name = 'hr/evaluation_list.html'

    def get_context_data(self,**kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.localdate()
        try:
            year, month = int(self.request.GET.get('year',now.year)), int(self.request.GET.get('month',now.month))
            if not 2000 <= year <= 2100 or not 1 <= month <= 12:
                raise ValueError
        except ValueError:
            year, month = now.year, now.month
        qs = visible_evaluations(self.request.user).filter(year=year,month=month)
        unit = self.request.GET.get('unit','').strip()
        if unit:
            qs = qs.filter(unit_code=unit)
        history = self.request.GET.get('history') == '1'
        items = list(qs)
        # Keep latest revision for each employee, independent of submission/approval status.
        latest = {row['employee_id']:row['last'] for row in EmployeeEvaluation.objects.filter(employee_id__in=[item.employee_id for item in items],year=year,month=month).values('employee_id').annotate(last=Max('revision'))}
        items = [decorate_evaluation(item) for item in items if history or item.revision == latest.get(item.employee_id)]
        ctx.update(title='Ocenjivanje zaposlenih',sidebar_template='sidebar_kadrovi.html',evaluations=items,
            year=year,month=month,months=list(enumerate(MONTHS,1)),history=history,selected_unit=unit,
            units=visible_evaluations(self.request.user).order_by('unit_code').values_list('unit_code',flat=True).distinct(),
            can_create=user_has_role_permission(self.request.user,'hr:evaluation_create'),
            can_catalog=user_has_role_permission(self.request.user,'hr:evaluation_catalog'),
            can_approve=user_has_role_permission(self.request.user,'hr:evaluation_approve'))
        bulk_form = EvaluationApprovalForm()
        bulk_form.fields['stage'].choices = [(key,label) for key,label in bulk_form.fields['stage'].choices if key!='supervisor']
        ctx['bulk_form'] = bulk_form
        return ctx


class EvaluationCreateView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    required_permission_code = 'hr:evaluation_create'
    template_name = 'hr/evaluation_form.html'

    def get_context_data(self,**kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title='Novi obrazac ocenjivanja',sidebar_template='sidebar_kadrovi.html')
        return ctx

    def get(self, request, *args, **kwargs):
        ctx = self.get_context_data()
        if request.GET.get('source'):
            source = get_object_or_404(visible_evaluations(request.user),pk=request.GET['source'])
            if not editable_employees(request.user).filter(pk=source.employee_id).exists():
                raise PermissionDenied
            snapshot = copy.deepcopy(source.snapshot)
            token = sign_snapshot(snapshot,request.user,source.pk)
            ctx.update(snapshot=snapshot,source=source,values_form=EvaluationValuesForm(snapshot=snapshot,token=token))
        else:
            today = timezone.localdate()
            initial = {'year':today.year,'month':today.month,**request.GET.dict()}
            selected = editable_employees(request.user).filter(pk=initial.get('employee')).first() if str(initial.get('employee','')).isdigit() else None
            if selected:
                setup = EvaluationEmployeeSetup.objects.filter(employee=selected).first()
                if setup and not initial.get('group'):
                    initial['group'] = setup.group_id
                unit = EvaluationUnitSetup.objects.filter(unit_code=str(selected.org_unit_code or selected.department_code),is_active=True).first()
                if unit:
                    for key in STAGES:
                        if not initial.get(key): initial[key] = getattr(unit,key+'_id')
            form = EvaluationHeaderForm(initial if 'prepare' in request.GET else None,initial=initial,user=request.user)
            ctx['header_form'] = form
            if 'prepare' in request.GET and form.is_valid():
                try:
                    snapshot = build_snapshot(**form.cleaned_data)
                except ValidationError as exc:
                    form.add_error(None,exc)
                else:
                    ctx.pop('header_form')
                    ctx.update(snapshot=snapshot,values_form=EvaluationValuesForm(snapshot=snapshot,token=sign_snapshot(snapshot,request.user)))
        return self.render_to_response(ctx)

    def post(self,request,*args,**kwargs):
        try:
            envelope = read_snapshot(request.POST.get('snapshot_token',''),request.user)
        except ValidationError as exc:
            messages.error(request,'; '.join(exc.messages))
            return redirect('hr:evaluation_create')
        form = EvaluationValuesForm(request.POST,snapshot=envelope['snapshot'])
        if form.is_valid():
            try:
                item = save_evaluation(envelope=envelope,values=form.cleaned_data,user=request.user)
            except ValidationError as exc:
                form.add_error(None,exc)
            else:
                messages.success(request,'Sačuvana je nova verzija obrasca sa snimkom svih podataka i merila.')
                return redirect('hr:evaluation_detail',pk=item.pk)
        return self.render_to_response(self.get_context_data(snapshot=envelope['snapshot'],values_form=form))


class EvaluationDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'hr/evaluation_detail.html'

    def get_context_data(self,**kwargs):
        ctx = super().get_context_data(**kwargs)
        item = decorate_evaluation(get_object_or_404(visible_evaluations(self.request.user),pk=self.kwargs['pk']))
        form = EvaluationApprovalForm()
        eligible = [stage for stage in STAGES if getattr(item,stage+'_id') == self.request.user.employee_id]
        form.fields['stage'].choices = [(key,label) for key,label in form.fields['stage'].choices if key in eligible]
        ctx.update(title='Sačuvano ocenjivanje',sidebar_template='sidebar_kadrovi.html',evaluation=item,snapshot=item.snapshot,
            approval_form=form,can_approve=bool(eligible) and user_has_role_permission(self.request.user,'hr:evaluation_approve'),
            can_revise=editable_employees(self.request.user).filter(pk=item.employee_id).exists(),
            versions=visible_evaluations(self.request.user).filter(employee=item.employee,year=item.year,month=item.month).order_by('-revision'))
        return ctx


class EvaluationPrintView(EvaluationDetailView):
    template_name = 'hr/evaluation_print.html'


@login_required
@require_POST
def evaluation_approve_view(request,pk):
    item = get_object_or_404(visible_evaluations(request.user),pk=pk)
    form = EvaluationApprovalForm(request.POST)
    if form.is_valid():
        try:
            approve_evaluation(evaluation=item,user=request.user,**{key:value for key,value in form.cleaned_data.items() if key!='confirm'})
        except ValidationError as exc:
            messages.error(request,'; '.join(exc.messages))
        else:
            messages.success(request,'Saglasnost je sačuvana uz vaš nalog i vreme potvrde.')
    else:
        messages.error(request,'Proverite saglasnost, datum i koeficijent. '+ ' '.join(' '.join(errors) for errors in form.errors.values()))
    return redirect('hr:evaluation_detail',pk=pk)


@login_required
@require_POST
@transaction.atomic
def evaluation_bulk_approve_view(request):
    form = EvaluationApprovalForm(request.POST)
    identifiers = request.POST.getlist('evaluations')
    if not form.is_valid() or not identifiers or any(not key.isdigit() for key in identifiers):
        messages.error(request,'Izaberite obrasce i popunite podatke saglasnosti.')
        return redirect('hr:evaluation_list')
    items = list(visible_evaluations(request.user).filter(pk__in=identifiers).order_by('employee_id','pk'))
    if len(items) != len(set(identifiers)):
        raise PermissionDenied
    if form.cleaned_data['stage'] == 'supervisor':
        raise PermissionDenied('Zbirna saglasnost predviđena je za direktora centra i generalnog direktora.')
    try:
        with transaction.atomic():
            for item in items:
                approve_evaluation(evaluation=item,user=request.user,**{key:value for key,value in form.cleaned_data.items() if key!='confirm'})
    except ValidationError as exc:
        messages.error(request,'Nijedna saglasnost nije sačuvana: '+'; '.join(exc.messages))
    else:
        messages.success(request,f'Sačuvane su saglasnosti za {len(items)} obrazaca.')
    return redirect(reverse('hr:evaluation_list')+f'?year={items[0].year}&month={items[0].month}')


CATALOGS = {
    'groups':(EvaluationGroup,['code','name','is_active'],'Grupe zaposlenih'),
    'criteria':(EvaluationCriterion,['code','name','sort_order','is_active'],'Merila ocenjivanja'),
    'scales':(EvaluationScale,['group','criterion','points','coefficient','description','is_active'],'Skale i vrednosti'),
    'units':(EvaluationUnitSetup,['unit_code','supervisor','director','general_director','is_active'],'Ocenjivači po OJ'),
    'employees':(EvaluationEmployeeSetup,['employee','group'],'Grupe zaposlenih — povezivanje'),
}


def catalog_value(value):
    if isinstance(value, bool):
        return 'Da' if value else 'Ne'
    if isinstance(value, Decimal):
        return format(value, '.5f').replace('.', ',')
    return value


class EvaluationCatalogView(LoginRequiredMixin,RolePermissionRequiredMixin,TemplateView):
    required_permission_code = 'hr:evaluation_catalog'
    template_name = 'hr/evaluation_catalog.html'

    def get_context_data(self,**kwargs):
        ctx = super().get_context_data(**kwargs)
        kind = self.request.GET.get('kind','scales')
        if kind not in CATALOGS: raise Http404
        model,fields,label = CATALOGS[kind]
        queryset = model.objects.all()
        if kind == 'scales': queryset = queryset.select_related('group','criterion')
        if kind == 'units': queryset = queryset.select_related('supervisor','director','general_director')
        if kind == 'employees': queryset = queryset.select_related('employee','group')
        ctx.update(title=label,sidebar_template='sidebar_kadrovi.html',kind=kind,
            tabs=[{'key':key,'label':value[2]} for key,value in CATALOGS.items()],
            headings=[model._meta.get_field(field).verbose_name for field in fields],
            rows=[{'pk':item.pk,'values':[catalog_value(getattr(item,field)) for field in fields]} for item in queryset])
        return ctx


class EvaluationCatalogEditView(LoginRequiredMixin,RolePermissionRequiredMixin,TemplateView):
    required_permission_code = 'hr:evaluation_catalog'
    template_name = 'hr/evaluation_catalog_form.html'

    def get_form(self,data=None):
        kind = self.kwargs['kind']
        if kind not in CATALOGS: raise Http404
        model,fields,label = CATALOGS[kind]
        instance = get_object_or_404(model,pk=self.kwargs['pk']) if 'pk' in self.kwargs else None
        form_type = forms.modelform_factory(model,fields=fields)
        form = form_type(data=data,instance=instance)
        if 'coefficient' in fields:
            form.fields['coefficient'] = CoefficientField(max_digits=8,decimal_places=5,label='Koeficijent stimulacije',widget=forms.TextInput(attrs={'inputmode':'decimal'}))
        style_form(form)
        return form,label

    def get_context_data(self,**kwargs):
        ctx = super().get_context_data(**kwargs)
        form,label = self.get_form(self.request.POST if self.request.method=='POST' else None)
        ctx.update(form=form,title=label,kind=self.kwargs['kind'],sidebar_template='sidebar_kadrovi.html')
        return ctx

    @transaction.atomic
    def post(self,request,*args,**kwargs):
        ctx = self.get_context_data()
        if ctx['form'].is_valid():
            ctx['form'].save()
            messages.success(request,'Šifrarnik je sačuvan. Postojeći snimci ocenjivanja zadržavaju ranije podatke.')
            return redirect(reverse('hr:evaluation_catalog')+'?kind='+self.kwargs['kind'])
        return self.render_to_response(ctx)
