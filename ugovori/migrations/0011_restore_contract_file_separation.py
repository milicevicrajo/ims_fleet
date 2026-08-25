from django.db import migrations, models


def restore_contract_files(apps, schema_editor):
    Contract = apps.get_model("ugovori", "Contract")
    ContractDocument = apps.get_model("ugovori", "ContractDocument")

    migrated_documents = ContractDocument.objects.filter(
        file__startswith="ugovori/files/",
    ).order_by("contract_id", "uploaded_at", "pk")

    document_ids = []
    restored_contract_ids = set()
    for document in migrated_documents.iterator():
        if document.contract_id not in restored_contract_ids:
            Contract.objects.filter(pk=document.contract_id).update(
                file=str(document.file),
            )
            restored_contract_ids.add(document.contract_id)
        document_ids.append(document.pk)

    if document_ids:
        ContractDocument.objects.filter(pk__in=document_ids).delete()


def move_contract_files_back_to_documents(apps, schema_editor):
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
        ContractDocument.objects.create(
            contract_id=contract.pk,
            document_type="contract",
            description=f"Dokument ugovora {contract.contract_number}",
            file=file_name,
            original_filename=original_filename[:255],
            uploaded_by_id=contract.created_by_id,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("ugovori", "0010_unify_contract_documents"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="ugovori/files/%Y/%m/",
                verbose_name="Fajl ugovora",
            ),
        ),
        migrations.RunPython(
            restore_contract_files,
            move_contract_files_back_to_documents,
        ),
    ]
