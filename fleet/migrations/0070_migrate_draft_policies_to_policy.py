from django.db import migrations


def migrate_draft_policies(apps, schema_editor):
    DraftPolicy = apps.get_model("fleet", "DraftPolicy")
    Policy = apps.get_model("fleet", "Policy")

    for draft in DraftPolicy.objects.all():
        if draft.invoice_id is not None:
            incoming = {
                "vehicle_id": draft.vehicle_id,
                "partner_pib": draft.partner_pib,
                "partner_name": draft.partner_name,
                "invoice_number": draft.invoice_number,
                "issue_date": draft.issue_date,
                "insurance_type": draft.insurance_type,
                "policy_number": draft.policy_number,
                "premium_amount": draft.premium_amount,
                "start_date": draft.start_date,
                "end_date": draft.end_date,
                "first_installment_amount": draft.first_installment_amount,
                "other_installments_amount": draft.other_installments_amount,
                "number_of_installments": draft.number_of_installments,
            }
            existing = Policy.objects.filter(invoice_id=draft.invoice_id).first()
            if existing:
                defaults = {
                    field: value if value is not None and value != "" else getattr(existing, field)
                    for field, value in incoming.items()
                }
            else:
                defaults = incoming
            Policy.objects.update_or_create(invoice_id=draft.invoice_id, defaults=defaults)
        draft.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0069_policy_direct_sync_nullable_fields"),
    ]

    operations = [
        migrations.RunPython(migrate_draft_policies, migrations.RunPython.noop),
    ]
