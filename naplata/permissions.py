from core.permissions import collect_url_pattern_names
from . import urls as naplata_urls


def collect_naplata_permission_codes():
    return collect_url_pattern_names(naplata_urls.urlpatterns, prefix="naplata")
