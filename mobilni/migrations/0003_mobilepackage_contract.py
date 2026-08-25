import django.db.models.deletion
from django.db import migrations, models


def link_existing_mobile_packages(apps, schema_editor):
    MobilePackage = apps.get_model("mobilni", "MobilePackage")
    Contract = apps.get_model("ugovori", "Contract")

    contract_2024 = Contract.objects.filter(contract_number="20-183").first()
    contract_2026 = Contract.objects.filter(contract_number="20-965").first()
    if contract_2024:
        MobilePackage.objects.filter(valid_from__year=2024).update(contract=contract_2024)
    if contract_2026:
        MobilePackage.objects.filter(valid_from__year=2026).update(contract=contract_2026)


def unlink_mobile_packages(apps, schema_editor):
    MobilePackage = apps.get_model("mobilni", "MobilePackage")
    MobilePackage.objects.update(contract=None)


class Migration(migrations.Migration):
    dependencies = [
        ("mobilni", "0002_mobileassignment_employee_mobileusage_employee_and_more"),
        ("ugovori", "0008_businessrequest_offer_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="mobilepackage",
            name="contract",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="mobile_packages",
                to="ugovori.contract",
                verbose_name="Ugovor",
            ),
        ),
        migrations.RunPython(link_existing_mobile_packages, unlink_mobile_packages),
    ]

