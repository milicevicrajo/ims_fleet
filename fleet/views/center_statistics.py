"""Center analysis shares all calculations and methodology with fleet analysis."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods

from core.mixins import role_permission_required
from fleet.support.management_reports import allowed_centers
from .analytics import render_fleet_analysis


@login_required
@role_permission_required('center_statistics')
@require_http_methods(['GET'])
def center_statistics(request, center_code):
    centers = allowed_centers(request.user)
    if not request.user.is_superuser and center_code not in centers:
        return HttpResponseForbidden('Nemate pristup ovom centru.')
    return render_fleet_analysis(request, center_code=center_code)
