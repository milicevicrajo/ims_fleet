from django.db import migrations


def move_contract_files_to_documents(apps, schema_editor):
    Contract = apps.get_model("ugovori", "Contract")
    ContractDocument = apps.get_model("ugovori", "ContractDocument")

    contracts = Contract.objects.exclude(file__isnull=True).exclude(file="")
    for contract in contracts.iterator():
        file_name = str(contract.file)
        if ContractDocument.objects.filter(
            contract_id=contract.pk,
            file=file_name,
        ).exists():
            continue

        original_filename = file_name.replace("\\", "/").rsplit("/", 1)[-1]
        document = ContractDocument.objects.create(
            contract_id=contract.pk,
            document_type="contract",
            description=f"Dokument ugovora {contract.contract_number}",
            file=file_name,
            original_filename=original_filename[:255],
            uploaded_by_id=contract.created_by_id,
        )
        ContractDocument.objects.filter(pk=document.pk).update(
            uploaded_at=contract.created_at,
        )


def restore_contract_files(apps, schema_editor):
    Contract = apps.get_model("ugovori", "Contract")
    ContractDocument = apps.get_model("ugovori", "ContractDocument")

    for contract in Contract.objects.all().iterator():
        document = (
            ContractDocument.objects.filter(
                contract_id=contract.pk,
                document_type="contract",
            )
            .order_by("uploaded_at", "pk")
            .first()
        )
        if document:
            Contract.objects.filter(pk=contract.pk).update(file=str(document.file))


class Migration(migrations.Migration):

    dependencies = [
        ("ugovori", "0009_contractdocument"),
    ]

    operations = [
        migrations.RunPython(
            move_contract_files_to_documents,
            restore_contract_files,
        ),
        migrations.RemoveField(
            model_name="contract",
            name="file",
        ),
    ]
