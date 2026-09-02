import django.db.models.deletion
from django.db import migrations, models


AUTO = "auto"
MANUAL = "manual"
UNMATCHED = "unmatched"


def employee_display(employee):
    if not employee:
        return ""
    last_name = getattr(employee, "display_last_name_override", "") or getattr(employee, "last_name", "") or ""
    first_name = getattr(employee, "display_first_name_override", "") or getattr(employee, "first_name", "") or ""
    display = f"{last_name} {first_name}".strip()
    return display or getattr(employee, "original_full_name", "") or ""


def user_link_status(mobile_user):
    if not mobile_user.employee_id:
        return UNMATCHED
    employee = mobile_user.employee
    return AUTO if employee and employee.employee_code == mobile_user.employee_code else MANUAL


def choose_assignment_mobile_user(assignment, users_by_employee_id):
    if not assignment.employee_id:
        return None
    candidates = users_by_employee_id.get(assignment.employee_id, [])
    if len(candidates) == 1:
        return candidates[0]

    employee_code = assignment.employee.employee_code if assignment.employee_id else None
    matching_code = [item for item in candidates if item.employee_code == employee_code]
    if len(matching_code) == 1:
        return matching_code[0]

    manual_links = [item for item in candidates if item.link_status == MANUAL]
    if len(manual_links) == 1:
        return manual_links[0]

    active_links = [item for item in candidates if item.is_active]
    if len(active_links) == 1:
        return active_links[0]

    return None


def backfill_mobile_links(apps, schema_editor):
    MobileAssignment = apps.get_model("mobilni", "MobileAssignment")
    MobileUser = apps.get_model("mobilni", "MobileUser")

    for mobile_user in MobileUser.objects.select_related("employee").iterator():
        status = user_link_status(mobile_user)
        if mobile_user.link_status != status:
            mobile_user.link_status = status
            mobile_user.save(update_fields=["link_status", "updated_at"])

    users_by_employee_id = {}
    for mobile_user in MobileUser.objects.select_related("employee").order_by("id"):
        if mobile_user.employee_id:
            users_by_employee_id.setdefault(mobile_user.employee_id, []).append(mobile_user)

    assignments = MobileAssignment.objects.select_related("employee", "mobile_user", "mobile_user__employee")
    for assignment in assignments.iterator():
        mobile_user = assignment.mobile_user or choose_assignment_mobile_user(assignment, users_by_employee_id)
        source_employee_code = assignment.source_employee_code
        source_full_name = assignment.source_full_name
        employee = assignment.employee

        if mobile_user:
            source_employee_code = source_employee_code or mobile_user.employee_code
            source_full_name = source_full_name or mobile_user.full_name
            employee = mobile_user.employee if mobile_user.employee_id else None
        elif assignment.employee_id:
            source_employee_code = source_employee_code or assignment.employee.employee_code
            source_full_name = source_full_name or employee_display(assignment.employee)

        update_fields = []
        if assignment.mobile_user_id != (mobile_user.pk if mobile_user else None):
            assignment.mobile_user = mobile_user
            update_fields.append("mobile_user")
        if assignment.source_employee_code != source_employee_code:
            assignment.source_employee_code = source_employee_code
            update_fields.append("source_employee_code")
        if assignment.source_full_name != source_full_name:
            assignment.source_full_name = source_full_name
            update_fields.append("source_full_name")
        if assignment.employee_id != (employee.pk if employee else None):
            assignment.employee = employee
            update_fields.append("employee")
        if update_fields:
            assignment.save(update_fields=[*update_fields, "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("mobilni", "0006_simplify_mobile_assignments"),
    ]

    operations = [
        migrations.AddField(
            model_name="mobileuser",
            name="link_status",
            field=models.CharField(
                choices=[
                    ("auto", "Automatski"),
                    ("manual", "Rucno povezano"),
                    ("unmatched", "Nepovezano"),
                    ("non_employee", "Nezaposleni"),
                    ("ambiguous", "Nejasno"),
                ],
                default="unmatched",
                max_length=20,
                verbose_name="Status veze",
            ),
        ),
        migrations.AddField(
            model_name="mobileassignment",
            name="mobile_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assignments",
                to="mobilni.mobileuser",
                verbose_name="Korisnik mobilnog",
            ),
        ),
        migrations.AddField(
            model_name="mobileassignment",
            name="source_employee_code",
            field=models.IntegerField(blank=True, null=True, verbose_name="Sifra iz dodele"),
        ),
        migrations.AddField(
            model_name="mobileassignment",
            name="source_full_name",
            field=models.CharField(blank=True, default="", max_length=150, verbose_name="Ime iz dodele"),
        ),
        migrations.AddIndex(
            model_name="mobileassignment",
            index=models.Index(fields=["mobile_user"], name="mobilni_mob_mobile__46c47a_idx"),
        ),
        migrations.AddIndex(
            model_name="mobileassignment",
            index=models.Index(fields=["source_employee_code"], name="mobilni_mob_source__f47b0e_idx"),
        ),
        migrations.RunPython(backfill_mobile_links, migrations.RunPython.noop),
    ]
