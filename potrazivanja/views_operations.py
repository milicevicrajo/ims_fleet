from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q, Max
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .access import check_access, can_view_all, can_edit, scoped
from .models import (CollectionState, FinancePartnerIdentity, CollectionContact, CollectionActivity, CollectionNotice,
                     CollectionProfile, CollectionLegalCase, CollectionLegalEvent, CollectionAudit, ContactPoint)
from .forms import (ContactForm, ActivityForm, NoticeForm, LegalCaseForm, LegalEventForm, ProfileForm,
                    ContactPointFormSet, NoticeItemFormSet)
from .services.source import payload
from core.mixins import user_has_role_permission as has

ENTITIES = {
    'contact': (CollectionContact, ContactForm, 'Kontakt', 'contacts'),
    'activity': (CollectionActivity, ActivityForm, 'Napomena / telefonski poziv', 'activities'),
    'notice': (CollectionNotice, NoticeForm, 'Opomena / pismo', 'notices'),
    'legal': (CollectionLegalCase, LegalCaseForm, 'Pravni postupak', 'legal'),
}


def writable(request, kind, action):
    check_access(request.user)
    if not can_edit(request.user, kind, action): raise PermissionDenied('Nemate dozvolu za ovu izmenu.')
    if not CollectionState.objects.filter(company=1, operations_independent_at__isnull=False).exists():
        raise PermissionDenied('Završni prenos operativnih podataka još nije završen.')


def record_snapshot(obj):
    data = model_to_dict(obj)
    if isinstance(obj, CollectionContact): data['points'] = list(obj.points.values('kind', 'value', 'label'))
    if isinstance(obj, CollectionNotice): data['items'] = list(obj.items.values('line_number', 'original_reference', 'job_code', 'due_date_snapshot', 'amount_snapshot'))
    return payload(data)


def audit(user, obj, action, before):
    CollectionAudit.objects.create(actor=user, entity=obj._meta.label_lower, entity_id=obj.pk,
                                  action=action, before=before, after=record_snapshot(obj))


def page_context(request, **extra):
    from .views import context, current_snapshot
    data = context(request, current_snapshot(request));data.update(extra)
    return data


def after_save(obj):
    if isinstance(obj, CollectionLegalCase): return redirect('potrazivanja:legal_detail', pk=obj.pk)
    return redirect('potrazivanja:partner_detail', pk=obj.identity_id) if obj.identity_id else redirect('potrazivanja:dashboard')


@never_cache
@require_http_methods(['GET', 'POST'])
def record_edit(request, kind, pk=None):
    if kind not in ENTITIES: raise PermissionDenied('Nepoznata evidencija.')
    writable(request, kind, 'update' if pk else 'create')
    model, form_class, label, section = ENTITIES[kind]
    with transaction.atomic():
        obj = get_object_or_404(model.objects.select_for_update(), pk=pk) if pk else model()
        before = record_snapshot(obj) if pk else {}
        initial = {}
        if not pk and request.GET.get('partner'):
            partner = get_object_or_404(FinancePartnerIdentity, pk=request.GET['partner'], company=1, partner_group=1)
            initial['identity'] = partner.pk
        if kind in ('activity', 'notice') and not pk and request.GET.get('type'):
            choices = dict(model._meta.get_field('kind').choices)
            if request.GET['type'] in choices: initial['kind'] = request.GET['type']
        form = form_class(request.POST if request.method == 'POST' else None, instance=obj, initial=initial)
        factory = ContactPointFormSet if kind == 'contact' else NoticeItemFormSet if kind == 'notice' else None
        formset = factory(request.POST if request.method == 'POST' else None, instance=obj, prefix='items') if factory else None
        if request.method == 'POST':
            valid = form.is_valid()
            if formset is not None: valid = formset.is_valid() and valid
            if valid and kind == 'notice':
                lines = [f.cleaned_data for f in formset.forms if f.cleaned_data and not f.cleaned_data.get('DELETE')]
                if lines:
                    total = sum((r['amount_snapshot'] for r in lines), Decimal(0))
                    if form.cleaned_data.get('total_amount') is not None and form.cleaned_data['total_amount'] != total:
                        form.add_error('total_amount', 'Ukupan iznos mora odgovarati zbiru stavki.');valid = False
                    else: form.instance.total_amount = total
                elif form.cleaned_data.get('total_amount') is None:
                    form.add_error('total_amount', 'Unesite iznos ili stavke dokumenta.');valid = False
            if valid:
                obj = form.save(commit=False)
                if not pk: obj.created_by = request.user
                obj.updated_by = request.user
                if kind == 'contact':
                    obj.name = ' '.join(x for x in (obj.first_name.strip(), obj.last_name.strip()) if x)
                    obj.normalized_at = timezone.now()
                elif kind == 'notice':
                    if not pk or before.get('identity') != obj.identity_id:
                        obj.partner_name_snapshot = obj.identity.source_name
                elif kind == 'legal':
                    obj.sifra_partnera = obj.identity.partner_code;obj.naziv_partnera = obj.identity.source_name
                obj.save()
                if formset is not None:
                    formset.instance = obj
                    children = formset.save(commit=False)
                    for deleted in formset.deleted_objects: deleted.delete()
                    next_line = (obj.items.aggregate(n=Max('line_number'))['n'] or 0) if kind == 'notice' else 0
                    for child in children:
                        if kind == 'notice' and not child.pk:
                            next_line += 1;child.line_number = next_line
                        child.save()
                    formset.save_m2m()
                if kind == 'contact':
                    obj.phone = next(iter(obj.points.filter(kind__in=['phone','mobile']).values_list('value',flat=True)), '')
                    obj.email = next(iter(obj.points.filter(kind='email').values_list('value',flat=True)), '')
                    obj.save(update_fields=['phone', 'email'])
                audit(request.user, obj, 'update' if pk else 'create', before)
                messages.success(request, f'{label}: podaci su sačuvani u Potraživanjima.')
                return after_save(obj)
    return render(request, 'potrazivanja/record_form.html', page_context(request, form=form, formset=formset,
        record=obj, kind=kind, title=('Izmena: ' if pk else 'Novi unos: ') + label, section='legal' if kind=='legal' else 'partners',
        can_archive=bool(pk and can_edit(request.user,kind,'archive'))))


@require_POST
def record_archive(request, kind, pk):
    if kind not in ENTITIES: raise PermissionDenied('Nepoznata evidencija.')
    writable(request, kind, 'archive')
    model = ENTITIES[kind][0]
    with transaction.atomic():
        obj = get_object_or_404(model.objects.select_for_update(), pk=pk)
        if request.POST.get('version') != obj.updated_at.isoformat():
            return HttpResponse('Zapis je promenjen. Osvežite stranicu.', status=409)
        before = record_snapshot(obj)
        archived = request.POST.get('archived') == '1'
        if kind == 'contact': obj.active = not archived
        elif kind == 'legal': obj.arhivirano = archived
        else: obj.archived = archived
        obj.updated_by = request.user;obj.save()
        audit(request.user,obj,'archive' if archived else 'restore',before)
    messages.success(request, 'Zapis je arhiviran.' if archived else 'Zapis je ponovo aktivan.')
    return after_save(obj)


@never_cache
@require_http_methods(['GET','POST'])
def profile_edit(request, pk):
    writable(request,'review','update')
    identity = get_object_or_404(FinancePartnerIdentity,pk=pk,company=1,partner_group=1)
    with transaction.atomic():
        FinancePartnerIdentity.objects.select_for_update().get(pk=identity.pk)
        obj = CollectionProfile.objects.select_for_update().filter(identity=identity).first() or CollectionProfile(identity=identity)
        before = record_snapshot(obj) if obj.pk else {}
        form = ProfileForm(request.POST if request.method=='POST' else None,instance=obj)
        if request.method=='POST' and form.is_valid():
            obj=form.save(commit=False)
            if not obj.pk:obj.created_by=request.user
            obj.updated_by=request.user;obj.save();audit(request.user,obj,'profile',before)
            return redirect('potrazivanja:partner_detail',pk=identity.pk)
    return render(request,'potrazivanja/record_form.html',page_context(request,form=form,record=obj,title=f'Oznake kupca · {identity.source_name}',section='review'))


@require_POST
def review_toggle(request, pk):
    writable(request,'review','update')
    identity=get_object_or_404(FinancePartnerIdentity,pk=pk,company=1,partner_group=1)
    if request.POST.get('value') not in ('0','1'):return JsonResponse({'error':'Neispravna oznaka.'},status=400)
    with transaction.atomic():
        # Lock identity as well, so creating the first profile is serialized.
        FinancePartnerIdentity.objects.select_for_update().get(pk=identity.pk)
        obj=CollectionProfile.objects.filter(identity=identity).first()
        version=obj.updated_at.isoformat() if obj else ''
        if request.POST.get('version','') != version:
            return JsonResponse({'error':'Oznaka je u međuvremenu promenjena. Lista je osvežena.'},status=409)
        before=record_snapshot(obj) if obj else {}
        if obj is None:obj=CollectionProfile(identity=identity,created_by=request.user)
        obj.needs_review=request.POST['value']=='1';obj.updated_by=request.user;obj.save()
        audit(request.user,obj,'review',before)
    return JsonResponse({'ok':True,'version':obj.updated_at.isoformat()})


@never_cache
@require_GET
def partner_options(request):
    check_access(request.user)
    qs=FinancePartnerIdentity.objects.filter(company=1,partner_group=1)
    if not can_view_all(request.user):
        from .views import current_snapshot
        snapshot=current_snapshot(request)
        qs=qs.filter(pk__in=scoped(snapshot.positions.all(),request.user).values('identity_id')) if snapshot else qs.none()
    query=request.GET.get('q','').strip()
    condition=Q(source_name__icontains=query) | Q(source_tax_id__icontains=query)
    if query.isdigit():condition |= Q(partner_code=int(query))
    qs=qs.filter(condition).order_by('source_name')[:40]
    return JsonResponse({'results':[{'id':x.pk,'text':f'{x.partner_code} · {x.source_name}'} for x in qs]})


@never_cache
@require_GET
def contact_options(request):
    check_access(request.user)
    if not can_view_all(request.user):raise PermissionDenied
    if not request.GET.get('partner', '').isdigit(): return JsonResponse({'results':[]})
    identity=get_object_or_404(FinancePartnerIdentity,pk=request.GET['partner'],company=1,partner_group=1)
    return JsonResponse({'results':[{'id':x.pk,'text':x.name or x.position or f'Kontakt #{x.pk}'} for x in identity.contacts.filter(active=True)]})


@never_cache
@require_GET
def legal_detail(request, pk):
    check_access(request.user)
    if not can_view_all(request.user):raise PermissionDenied
    obj=get_object_or_404(CollectionLegalCase,pk=pk)
    fields=[(field.verbose_name,getattr(obj,field.name)) for field in CollectionLegalCase._meta.fields
            if field.name not in ('id','identity','legacy_id','original_data','created_by','updated_by','created_at','updated_at','arhivirano') and getattr(obj,field.name) not in (None,'')]
    return render(request,'potrazivanja/legal_detail.html',page_context(request,record=obj,title=f'Postupak · {obj.broj_predmeta or obj.pk}',
        fields=fields,events=obj.events.all(),section='legal',can_change=can_edit(request.user,'legal'),can_archive_event=can_edit(request.user,'legal','archive'),
        can_add_event=can_edit(request.user,'legal','create')))


@never_cache
@require_http_methods(['GET','POST'])
def legal_event_edit(request, case_pk, pk=None):
    writable(request,'legal','update' if pk else 'create')
    case=get_object_or_404(CollectionLegalCase,pk=case_pk)
    with transaction.atomic():
        obj=get_object_or_404(CollectionLegalEvent.objects.select_for_update(),pk=pk,case=case) if pk else CollectionLegalEvent(case=case)
        before=record_snapshot(obj) if pk else {}
        form=LegalEventForm(request.POST if request.method=='POST' else None,instance=obj)
        if request.method=='POST' and form.is_valid():
            obj=form.save(commit=False)
            if not pk:obj.created_by=request.user
            obj.updated_by=request.user;obj.save();audit(request.user,obj,'event',before)
            return redirect('potrazivanja:legal_detail',pk=case.pk)
    return render(request,'potrazivanja/record_form.html',page_context(request,record=obj,form=form,title='Promena postupka',section='legal'))


@never_cache
@require_GET
def notice_print(request, pk):
    check_access(request.user)
    if not can_view_all(request.user) or not has(request.user,'potrazivanja:print'):raise PermissionDenied
    obj=get_object_or_404(CollectionNotice.objects.select_related('identity'),pk=pk)
    return render(request,'potrazivanja/notice_print.html',{'record':obj,'items':obj.items.order_by('line_number')})


@require_POST
def legal_event_archive(request, case_pk, pk):
    writable(request, 'legal', 'archive')
    with transaction.atomic():
        obj = get_object_or_404(CollectionLegalEvent.objects.select_for_update(), pk=pk, case_id=case_pk)
        if request.POST.get('version') != obj.updated_at.isoformat():
            return HttpResponse('Zapis je promenjen. Osvežite stranicu.', status=409)
        before = record_snapshot(obj)
        obj.archived = request.POST.get('archived') == '1'
        obj.updated_by = request.user
        obj.save()
        audit(request.user, obj, 'archive' if obj.archived else 'restore', before)
    return redirect('potrazivanja:legal_detail', pk=case_pk)


def operational_rows(request, snapshot, kind):
    from .views import cell, partner_cell, SPLIT_OPERATIONS
    check_access(request.user)
    if not can_view_all(request.user): raise PermissionDenied
    fixed_type = None
    if kind in SPLIT_OPERATIONS:
        kind, fixed_type, _ = SPLIT_OPERATIONS[kind]
    if kind == 'directory':
        return [[partner_cell(p, snapshot), cell(p.partner_code), cell(p.source_tax_id), cell(p.source_city)]
                for p in FinancePartnerIdentity.objects.filter(company=1, partner_group=1).only('id','source_name','partner_code','source_tax_id','source_city')]
    entity = {'contacts':'contact', 'activities':'activity', 'notices':'notice', 'legal':'legal'}[kind]
    model = ENTITIES[entity][0]
    qs = model.objects.select_related('identity')
    if request.GET.get('partner'): qs = qs.filter(identity_id=request.GET['partner'])
    # Detail keeps archived history visible; the list defaults to active records.
    archived = request.GET.get('archived', 'all' if request.GET.get('partner') else '0')
    if archived in ('0','1'):
        field = 'active' if kind=='contacts' else 'arhivirano' if kind=='legal' else 'archived'
        qs = qs.filter(**{field: archived=='0' if kind=='contacts' else archived=='1'})
    if fixed_type:
        qs = qs.filter(kind=fixed_type)
    elif request.GET.get('type'):
        qs = qs.filter(**{'tip' if kind=='legal' else 'kind': request.GET['type']}) if kind!='contacts' else qs
    if kind=='contacts':
        qs = qs.prefetch_related('points')
        if request.GET.get('review')=='1': qs=qs.filter(needs_review=True)
    if kind=='notices' and request.GET.get('year','').isdigit(): qs=qs.filter(year=int(request.GET['year']))
    may_edit = can_edit(request.user,entity)
    may_print = has(request.user,'potrazivanja:print')
    result=[]
    for obj in qs:
        label = partner_cell(obj.identity,snapshot) if obj.identity else cell((getattr(obj,'legacy_partner_name','') or getattr(obj,'partner_name_snapshot','') or getattr(obj,'naziv_partnera',''))+' · Nepovezano')
        actions=[]
        if may_edit: actions.append({'label':'Izmeni','url':reverse('potrazivanja:record_update',args=[entity,obj.pk])})
        if kind=='notices' and may_print: actions.append({'label':'Štampa','url':reverse('potrazivanja:notice_print',args=[obj.pk])})
        if kind=='legal': actions.insert(0,{'label':'Otvori','url':reverse('potrazivanja:legal_detail',args=[obj.pk])})
        action_cell=cell('');action_cell['actions']=actions
        if kind=='contacts':
            points=list(obj.points.all())
            phones=' · '.join(p.value for p in points if p.kind in ('phone','mobile')) or obj.phone
            emails=' · '.join(p.value for p in points if p.kind=='email') or obj.email
            name=' '.join(x for x in (obj.first_name,obj.last_name) if x) or obj.position or 'Opšti kontakt'
            status=('Aktivan' if obj.active else 'Arhiva')+(' · Proveriti kontakt' if obj.needs_review else '')
            row=[label,cell(name),cell(phones),cell(emails),cell(obj.note),cell(status)]
        elif kind=='activities':
            row=[label,cell(obj.get_kind_display()),cell(obj.occurred_at,'date'),cell(obj.text),cell(obj.outcome),cell(obj.next_action_date,'date'),cell('Arhiva' if obj.archived else 'Aktivno')]
        elif kind=='notices':
            row=[label,cell(obj.get_kind_display()),cell(obj.year),cell(obj.number),cell(obj.issued_on,'date'),cell(obj.total_amount,'money'),cell(obj.currency),cell(obj.original_invoice_text),cell(obj.note),cell('Arhiva' if obj.archived else 'Aktivno')]
        else:
            row=[label,cell(obj.get_tip_display()),cell(obj.broj_predmeta),cell(obj.sud),cell(obj.osnovni_dug,'money'),cell(obj.valuta),cell('Arhiva' if obj.arhivirano else 'Aktivno')]
        result.append(row+[action_cell])
    return result
