from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from hr.models import AnnualLeaveAllowance, AnnualLeaveDecision, AnnualLeaveSync
from hr.services.annual_leave import sync_annual_leave
from hr.access import scope_employee_records


class AnnualLeaveListView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = 'hr/annual_leave_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        current_year = timezone.localdate().year
        raw_year = self.request.GET.get('year', str(current_year))
        try:
            year = int(raw_year) if raw_year else None
            if year is not None and not 1900 <= year <= 2100:
                raise ValueError
        except ValueError:
            year = current_year
        query = self.request.GET.get('q', '').strip()
        include_withdrawn = self.request.GET.get('archive') == '1'
        allocations = scope_employee_records(AnnualLeaveAllowance.objects.select_related('employee'), self.request.user)
        decisions = scope_employee_records(AnnualLeaveDecision.objects.select_related('employee'), self.request.user)
        if year:
            allocations = allocations.filter(year=year)
            decisions = decisions.filter(year=year)
        if not include_withdrawn:
            allocations = allocations.filter(source_present=True)
            decisions = decisions.filter(source_present=True)
        if query:
            match = (Q(employee__first_name__icontains=query) | Q(employee__last_name__icontains=query)
                     | Q(employee__display_first_name_override__icontains=query) | Q(employee__display_last_name_override__icontains=query))
            if query.isdigit():
                match |= Q(employee_code=int(query))
            allocations = allocations.filter(match | Q(source_employee_name__icontains=query))
            decisions = decisions.filter(match)
        years = set(AnnualLeaveAllowance.objects.values_list('year', flat=True))
        years.update(AnnualLeaveDecision.objects.values_list('year', flat=True))
        years.add(current_year)
        ctx.update(
            title='Godišnji odmori', sidebar_template='sidebar_kadrovi.html',
            annual_allowances=allocations, annual_decisions=decisions,
            allocation_count=allocations.count(), decision_count=decisions.count(),
            unlinked_count=allocations.filter(employee__isnull=True).count()+decisions.filter(employee__isnull=True).count(),
            selected_year=year, available_years=sorted(years, reverse=True), query=query, include_withdrawn=include_withdrawn,
            last_annual_sync=AnnualLeaveSync.objects.first(),
            can_sync=user_has_role_permission(self.request.user, 'hr:annual_leave_sync'),
            can_view_employee=user_has_role_permission(self.request.user, 'employee_detail'),
        )
        return ctx


@login_required
@require_POST
@role_permission_required('hr:annual_leave_sync')
def annual_leave_sync_view(request):
    raw_year = request.POST.get('year', str(timezone.localdate().year))
    try:
        result = sync_annual_leave(year=raw_year or None, user=request.user)
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    except DatabaseError:
        messages.error(request, 'Izvor ili baza trenutno nije dostupan. Prethodno sinhronizovani podaci ostali su sačuvani.')
    else:
        allocations, decisions = result['allocations'], result['decisions']
        messages.success(request,
            f"Sinhronizacija završena. Dodele: {allocations['created']} novih, {allocations['updated']} ažuriranih. "
            f"Rešenja: {decisions['created']} novih, {decisions['updated']} ažuriranih. "
            f"Povučeno iz izvora: {allocations['withdrawn'] + decisions['withdrawn']}.")
        unlinked = allocations['unlinked'] + decisions['unlinked']
        if unlinked:
            messages.warning(request, f'{unlinked} izvornih zapisa nema povezanu osobu u lokalnom spisku zaposlenih. Zapisi su sačuvani pod izvornom šifrom.')
    if not user_has_role_permission(request.user, 'hr:annual_leave_list'):
        return redirect('my_employee_profile')
    year = raw_year if raw_year.isdigit() and 1900 <= int(raw_year) <= 2100 else ''
    return redirect(reverse('hr:annual_leave_list')+'?year='+year)
