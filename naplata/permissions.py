from django.urls import URLPattern, URLResolver

from . import urls as naplata_urls


def _collect_names(patterns, acc):
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            if pattern.name:
                acc.add(pattern.name)
        elif isinstance(pattern, URLResolver):
            _collect_names(pattern.url_patterns, acc)
    return acc


def collect_naplata_permission_codes():
    names = set()
    _collect_names(naplata_urls.urlpatterns, names)
    return sorted({f"naplata:{name}" for name in names})
