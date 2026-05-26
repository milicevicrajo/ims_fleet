from django.db import migrations


def backfill_invoice_control_fields(apps, schema_editor):
    ProcurementInvoice = apps.get_model("nabavka", "ProcurementInvoice")
    for invoice in ProcurementInvoice.objects.all().iterator():
        update_fields = []
        if not invoice.center_name and invoice.center:
            invoice.center_name = invoice.center
            update_fields.append("center_name")
        should_go_to_warehouse = bool((invoice.warehouse or "").strip())
        if invoice.goes_to_warehouse != should_go_to_warehouse:
            invoice.goes_to_warehouse = should_go_to_warehouse
            update_fields.append("goes_to_warehouse")
        if update_fields:
            invoice.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("nabavka", "0005_procurementinvoice_center_name_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_invoice_control_fields, migrations.RunPython.noop),
    ]
