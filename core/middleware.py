from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from core.activity import log_request_activity


class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        log_request_activity(request, response)
        return response


class LoginRedirectMiddleware:
    """Neprijavljen korisnik ide na prijavu umesto na stranicu 403.

    Dozvole se u ovom sistemu proveravaju na više mesta (mixin, dekorator i
    provere u samim view-ovima), pa se odluka donosi na jednom mestu — kada
    PermissionDenied stigne do middleware-a. Prijavljen korisnik bez dozvole i
    dalje dobija 403, jer njemu prijava ništa ne menja.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, PermissionDenied):
            return None
        if getattr(request.user, "is_authenticated", False):
            return None
        # Admin ima sopstvenu prijavu; ne preusmeravamo ga na prijavu aplikacije.
        if request.path.startswith("/admin/"):
            return None
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
