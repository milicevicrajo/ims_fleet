from django.urls import URLPattern, URLResolver

from . import urls as fleet_urls


def _collect_names(patterns, acc):
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            if pattern.name:
                acc.add(pattern.name)
        elif isinstance(pattern, URLResolver):
            _collect_names(pattern.url_patterns, acc)
    return acc


def collect_fleet_permission_codes():
    names = set()
    _collect_names(fleet_urls.urlpatterns, names)
    return sorted(names)
