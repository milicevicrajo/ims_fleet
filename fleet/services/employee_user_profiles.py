import re
import unicodedata

from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import OrganizationalUnit, Role
from fleet.models import Employee


def clean(value):
    return str(value or "").strip()


def ascii_slug(value):
    value = clean(value).casefold().replace("\u0111", "dj")
    value = "".join(
        ch for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", ".", value).strip(".")


def strip_name_titles(value):
    text = clean(value)
    return re.sub(
        r"^(mr|dr|prof|dipl|ing|in\u017e|inz)(?:\.|\s+)",
        "",
        text,
        flags=re.IGNORECASE,
    )


def username_base(employee):
    return ".".join(
        part for part in [
            ascii_slug(strip_name_titles(employee.first_name)),
            ascii_slug(employee.last_name),
        ]
        if part
    )


def unique_username(base, employee_code, existing_usernames):
    username = base
    if username.casefold() not in existing_usernames:
        return username
    username = f"{base}.{employee_code}"
    if username.casefold() not in existing_usernames:
        return username
    suffix = 2
    while f"{username}.{suffix}".casefold() in existing_usernames:
        suffix += 1
    return f"{username}.{suffix}"


def infer_center(org_unit_code, centers=None, overrides=None):
    overrides = overrides or {}
    centers = centers if centers is not None else available_centers()
    org_unit = clean(org_unit_code)
    if org_unit in overrides:
        return overrides[org_unit], f"override {org_unit}->{overrides[org_unit]}"
    if not org_unit:
        return "", "nema HR OJ"
    if org_unit in centers:
        return org_unit, "ista sifra centra"
    matches = [center for center in centers if org_unit.startswith(center)]
    if matches:
        max_length = max(len(center) for center in matches)
        best = sorted(center for center in matches if len(center) == max_length)
        if len(best) == 1:
            return best[0], f"prefiks {org_unit}->{best[0]}"
        return "", f"vise kandidata: {', '.join(best)}"
    return "", "nema mapiranja"


def available_centers():
    return sorted(
        {
            clean(center)
            for center in OrganizationalUnit.objects.values_list("center", flat=True)
            if clean(center)
        },
        key=lambda value: (len(value), value),
    )


def get_or_create_role(slug="zaposleni"):
    slug = clean(slug)
    if not slug:
        return None
    role, _created = Role.objects.get_or_create(
        slug=slug,
        defaults={
            "name": slug.replace("_", " ").title(),
            "description": "Obican zaposleni: pristup sopstvenom profilu.",
            "is_active": True,
        },
    )
    return role


def initial_password_for_employee(employee, *, default_password="", password_from_code=False):
    if default_password:
        return default_password
    if password_from_code or not clean(employee.personal_number):
        return f"ims{employee.employee_code}"
    return clean(employee.personal_number)


@transaction.atomic
def create_user_profile_for_employee(
    employee,
    *,
    role_slug="zaposleni",
    default_password="",
    password_from_code=False,
    include_unmapped=True,
    centers=None,
):
    User = get_user_model()
    if User.objects.filter(employee=employee).exists():
        raise ValueError("Zaposleni vec ima korisnicki profil.")

    center, reason = infer_center(employee.org_unit_code, centers=centers)
    if not center and not include_unmapped:
        raise ValueError(reason)

    existing_usernames = {
        clean(username).casefold()
        for username in User.objects.values_list("username", flat=True)
    }
    base = username_base(employee) or f"zaposleni.{employee.employee_code}"
    username = unique_username(base, employee.employee_code, existing_usernames)

    user = User(
        username=username,
        first_name=employee.first_name or "",
        last_name=employee.last_name or "",
        employee=employee,
        allowed_center_codes=center or None,
        is_active=True,
    )
    user.set_password(
        initial_password_for_employee(
            employee,
            default_password=default_password,
            password_from_code=password_from_code,
        )
    )
    user.must_change_password = True
    user.save()

    role = get_or_create_role(role_slug)
    if role is not None:
        user.roles.add(role)

    return user, center, reason


def create_user_profiles_for_missing_employees(queryset=None, **kwargs):
    employees = queryset or Employee.objects.filter(is_active=True, user_account__isnull=True).order_by("employee_code")
    centers = available_centers()
    created = []
    skipped = []
    for employee in employees:
        try:
            user, center, reason = create_user_profile_for_employee(employee, centers=centers, **kwargs)
        except Exception as exc:
            skipped.append((employee, str(exc)))
        else:
            created.append((employee, user, center, reason))
    return created, skipped
