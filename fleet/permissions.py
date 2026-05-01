from core.permissions import collect_url_pattern_names
from . import urls as fleet_urls


def collect_fleet_permission_codes():
    return collect_url_pattern_names(fleet_urls.urlpatterns)
