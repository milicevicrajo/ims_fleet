"""Dozvole rešenja zaposlenih, zajedničke redovnoj i ciljanoj sinhronizaciji."""

RESENJA_ADMIN_CODES = frozenset({
    'hr:resenje_catalog',
    'hr:resenje_catalog_create',
    'hr:resenje_catalog_edit',
    'hr:resenje_view_all',
})


def collect_resenja_permission_codes():
    from core.permissions import collect_url_pattern_names
    from hr.urls import urlpatterns

    return sorted({code for code in collect_url_pattern_names(urlpatterns, prefix='hr')
                   if code.startswith('hr:resenje_')} | RESENJA_ADMIN_CODES)
