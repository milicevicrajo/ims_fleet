import calendar
import datetime

from django.db import migrations


def clean_text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value != value:
        return ""
    value = str(value).strip()
    return value[:-2] if value.endswith(".0") else value


def clean_int(value):
    value = clean_text(value)
    if not value:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def package_matches_period(package, year, month):
    if not year or not month:
        return False
    period_start = datetime.date(year, month, 1)
    period_end = datetime.date(year, month, calendar.monthrange(year, month)[1])
    if package.valid_from and package.valid_from > period_end:
        return False
    if package.valid_to and package.valid_to < period_start:
        return False
    return True


def package_candidates_by_name(MobilePackage):
    packages = {}
    for package in MobilePackage.objects.order_by("name", "-valid_from", "-id"):
        packages.setdefault(clean_text(package.name).lower(), []).append(package)
    return packages


def find_package(package_name, packages_by_name, *, valid_from=None, year=None, month=None):
    candidates = packages_by_name.get(clean_text(package_name).lower(), [])
    if not candidates:
        return None
    if valid_from:
        for package in candidates:
            if package.valid_from == valid_from:
                return package
    for package in candidates:
        if package_matches_period(package, year, month):
            return package
    return candidates[0]


def link_assignment_relations(apps, schema_editor):
    MobileAssignment = apps.get_model("mobilni", "MobileAssignment")
    MobilePackage = apps.get_model("mobilni", "MobilePackage")
    MobileUser = apps.get_model("mobilni", "MobileUser")
    Employee = apps.get_model("fleet", "Employee")

    packages_by_name = package_candidates_by_name(MobilePackage)
    employees_by_code = {
        clean_int(employee.employee_code): employee
        for employee in Employee.objects.all()
        if clean_int(employee.employee_code) is not None
    }
    mobile_users_by_id = {
        mobile_user.pk: mobile_user
        for mobile_user in MobileUser.objects.select_related("employee")
    }

    assignments = MobileAssignment.objects.select_related("package", "employee", "mobile_user", "mobile_user__employee")
    for assignment in assignments.iterator():
        update_fields = []

        if not assignment.package_id:
            package = find_package(
                assignment.package_name,
                packages_by_name,
                valid_from=assignment.valid_from,
                year=assignment.year,
                month=assignment.month,
            )
            if package:
                assignment.package = package
                update_fields.append("package")

        if not assignment.employee_id:
            employee_code = clean_int(assignment.employee_code)
            mobile_user = mobile_users_by_id.get(assignment.mobile_user_id)
            if not employee_code and mobile_user:
                employee_code = clean_int(mobile_user.employee_code)

            employee = employees_by_code.get(employee_code)
            if not employee and mobile_user and mobile_user.employee_id:
                employee = mobile_user.employee
            if employee:
                assignment.employee = employee
                update_fields.append("employee")

        if update_fields:
            assignment.save(update_fields=[*update_fields, "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("mobilni", "0005_mobile_parking_exemptions"),
    ]

    operations = [
        migrations.RunPython(link_assignment_relations, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="mobileassignment",
            name="mobilni_mob_employe_159bf4_idx",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="employee_active",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="employee_code",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="employee_name",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="mobile_user",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="note",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="package_name",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="package_net_amount",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="personal_number",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="valid_from",
        ),
        migrations.RemoveField(
            model_name="mobileassignment",
            name="valid_to",
        ),
    ]
