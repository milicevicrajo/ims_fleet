import ipaddress

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db import OperationalError, ProgrammingError
from django.dispatch import receiver

from core.models import ActivityLog


STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        ip_address = forwarded_for.split(",", 1)[0].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR")

    if not ip_address:
        return None
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return None
    return ip_address


def get_actor_values(user):
    if not user or not getattr(user, "is_authenticated", False):
        return {
            "user": None,
            "actor_username": "",
            "actor_display_name": "",
        }
    display_name = user.get_full_name() if hasattr(user, "get_full_name") else ""
    return {
        "user": user,
        "actor_username": getattr(user, "username", "") or "",
        "actor_display_name": display_name or str(user),
    }


def get_resolver_values(request):
    match = getattr(request, "resolver_match", None)
    view_name = ""
    app_label = ""
    if match:
        view_name = match.view_name or ""
        if match.namespace:
            app_label = match.namespace
        elif view_name:
            app_label = view_name.split(":", 1)[0] if ":" in view_name else "fleet"
    return view_name, app_label


def log_activity(
    *,
    request=None,
    user=None,
    action=ActivityLog.ACTION_MANUAL,
    description="",
    status_code=None,
    object_instance=None,
    object_model="",
    object_pk="",
    object_repr="",
    changes=None,
    method="",
    path="",
    view_name="",
    app_label="",
):
    if request is not None:
        user = user or getattr(request, "user", None)
        method = method or getattr(request, "method", "") or ""
        path = path or request.get_full_path()
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
        ip_address = get_client_ip(request)
        resolved_view_name, resolved_app_label = get_resolver_values(request)
        view_name = view_name or resolved_view_name
        app_label = app_label or resolved_app_label
    else:
        user_agent = ""
        ip_address = None

    if object_instance is not None:
        meta = getattr(object_instance, "_meta", None)
        if meta:
            object_model = object_model or f"{meta.app_label}.{meta.model_name}"
        object_pk = object_pk or str(getattr(object_instance, "pk", "") or "")
        object_repr = object_repr or str(object_instance)

    data = {
        **get_actor_values(user),
        "action": action,
        "description": description[:500],
        "app_label": app_label[:80],
        "view_name": view_name[:150],
        "method": method[:10],
        "path": path[:500],
        "status_code": status_code,
        "object_model": object_model[:150],
        "object_pk": str(object_pk or "")[:80],
        "object_repr": str(object_repr or "")[:255],
        "changes": changes or {},
        "ip_address": ip_address,
        "user_agent": user_agent,
    }

    try:
        return ActivityLog.objects.create(**data)
    except (OperationalError, ProgrammingError):
        return None


def log_request_activity(request, response):
    user = getattr(request, "user", None)
    view_name, _ = get_resolver_values(request)
    if (
        request.method not in STATE_CHANGING_METHODS
        or not user
        or not getattr(user, "is_authenticated", False)
        or view_name in {"login", "logout"}
    ):
        return None

    if getattr(request, "_skip_activity_log", False):
        return None

    description = f"{request.method} {request.path}"
    return log_activity(
        request=request,
        user=user,
        action=ActivityLog.ACTION_REQUEST,
        description=description,
        status_code=getattr(response, "status_code", None),
    )


@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    log_activity(
        request=request,
        user=user,
        action=ActivityLog.ACTION_LOGIN,
        description="Korisnik se prijavio u aplikaciju.",
    )


@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    log_activity(
        request=request,
        user=user,
        action=ActivityLog.ACTION_LOGOUT,
        description="Korisnik se odjavio iz aplikacije.",
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = (credentials or {}).get("username", "")
    log_activity(
        request=request,
        action=ActivityLog.ACTION_LOGIN_FAILED,
        description=f"Neuspesna prijava za korisnika: {username}",
        changes={"username": username},
    )
