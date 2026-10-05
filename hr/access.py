"""Obuhvat kadrovskih podataka.

Od 28.09.2026. (plan prelaska na registar, korak 7) Kadrovi su **na registru**
(`settings.PRAVA_PO_REGISTRU["kadrovi"]`): obuhvat daju odobrene dodele uloga sa bilo kojom
dozvolom Kadrova (`hr:…`, `employee_…`), a zaposleni pripada cvoru registra zapisanom na kartici
(`Employee.org_node`). Dodeljen centar daje sve njegove jedinice; dodeljena sifra posla ne daje ljude.
Prazan obuhvat — nista (osim sopstvenih podataka, kao i dosad). Iskljucen prekidac vraca stara
pravila (centri i OJ korisnika).
"""
from core.mixins import user_has_role_permission
from core.models import OrganizationalUnit
from fleet.services.employee_user_profiles import infer_center
from hr.models import Employee


def na_registru():
    from organizacija.services.prava import modul_na_registru

    return modul_na_registru("kadrovi")


# Zahtev za sebe (uloga Zaposleni): ove dozvole otvaraju ekrane, ali ne daju obuhvat Kadrova.
# Uloga Zaposleni ima dodelu na ceo svoj centar (zbog Flote); bez izuzetka bi videla sve kolege.
DOZVOLE_ZAHTEVA_ZA_SEBE = frozenset("hr:" + kod for kod in (
    "zahtev_list", "zahtev_detail", "zahtev_create", "zahtev_edit", "zahtev_predlog", "zahtev_print",
    "zahtev_podnesi"))


def dozvole_kadrova():
    from django.db.models import Q

    from core.models import PermissionCode

    return frozenset(PermissionCode.objects.filter(Q(code__startswith="hr:") | Q(code__startswith="employee_"))
                     .exclude(code__in=DOZVOLE_ZAHTEVA_ZA_SEBE).values_list("code", flat=True))


def obuhvat(user):
    from organizacija.services.prava import Obuhvat, obuhvat_zahteva

    if not getattr(user, "is_authenticated", False):
        return Obuhvat()
    kes = user.__dict__.setdefault("_obuhvat_kadrova", {})
    if "o" not in kes:
        kes["o"] = obuhvat_zahteva(user, dozvole_kadrova())
    return kes["o"]


def cvorovi(user):
    """Cvorovi zaposlenih u obuhvatu korisnika; None znaci cela firma."""
    from organizacija.services.zaposleni import cvorovi_obuhvata

    return cvorovi_obuhvata(obuhvat(user))


def cela_firma(user):
    return user.is_superuser or (na_registru() and obuhvat(user).cela_firma)


def scope_values(user):
    if na_registru():
        return _scope_values_registar(user)
    centers = {x.strip() for x in (user.allowed_center_codes or '').replace(';', ',').split(',') if x.strip()}
    legacy = list(user.allowed_centers.values_list('code', 'center'))
    centers.update(str(center).strip() for _,center in legacy if center and str(center).strip())
    units = set()
    units.update(str(code).strip() for code,_ in legacy if code and str(code).strip())
    return centers, units


def _scope_values_registar(user):
    """Centri (oznake iz registra i iz kadrovske baze, npr. `2` i `20`) i OJ zaposlenih u obuhvatu."""
    from organizacija.models import OrgNodeVersion
    from organizacija.services.classification import OZNAKA_CENTRA_IZ_KNJIZENJA

    o = obuhvat(user)
    centri = set(OrgNodeVersion.objects.filter(node_id__in=o.centri, valid_to__isnull=True).values_list("full_code", flat=True))
    centri.update(stara for stara, nova in OZNAKA_CENTRA_IZ_KNJIZENJA.items() if nova in centri)
    return centri, set()


def has_restricted_scope(user):
    if user.is_superuser:
        return False
    if na_registru():
        return not obuhvat(user).cela_firma
    centers, units = scope_values(user)
    return bool(centers or units or user_has_role_permission(user, 'hr:kadrovi_manage'))


def allowed_unit_codes(user, *, extra_centers=None):
    if na_registru() and extra_centers is None:
        # OJ zaposlenih cija je organizaciona jedinica u obuhvatu (i za snimljene OJ na rešenjima).
        return {str(code or department or '').strip()
                for code, department in visible_employees(user).values_list('org_unit_code', 'department_code')}
    centers, units = scope_values(user)
    if extra_centers is not None:
        centers, units = set(extra_centers), set()
    registry = {str(code).strip():str(center).strip() for code,center in OrganizationalUnit.objects.values_list('code','center')}
    all_centers = set(registry.values()) - {''}
    result = set(units)
    for code,department in Employee.objects.values_list('org_unit_code','department_code').distinct():
        code = str(code or department or '').strip()
        center = registry.get(code) or infer_center(code, centers=all_centers)[0]
        if center in centers:
            result.add(code)
    return result


def visible_employees(user, *, unrestricted=False, extra_centers=None):
    qs = Employee.objects.all()
    if not user.is_authenticated:
        return qs.none()
    if na_registru() and extra_centers is None:
        if unrestricted or user.is_superuser:
            return qs
        ids = cvorovi(user)
        return qs if ids is None else qs.filter(org_node_id__in=ids)
    if extra_centers is None and (unrestricted or not has_restricted_scope(user)):
        return qs
    codes = allowed_unit_codes(user, extra_centers=extra_centers)
    ids = [pk for pk,code,department in qs.values_list('pk','org_unit_code','department_code')
           if str(code or department or '').strip() in codes]
    return qs.filter(pk__in=ids)


def scope_employee_records(qs, user, field='employee'):
    if not has_restricted_scope(user):
        return qs
    return qs.filter(**{f'{field}__in':visible_employees(user)})
