from django.db import migrations, models
from django.db.models import F


def copy_keys(apps, schema_editor):
    apps.get_model('potrazivanja', 'LegalCaseLink').objects.using(schema_editor.connection.alias).update(legacy_case_id=F('case_id'))


class Migration(migrations.Migration):
    dependencies = [('potrazivanja', '0004_collectionactivity_contact_and_more')]
    operations = [
        migrations.AddField(model_name='legalcaselink', name='legacy_case_id', field=models.PositiveBigIntegerField(null=True)),
        migrations.RunPython(copy_keys, migrations.RunPython.noop),
        migrations.RemoveField(model_name='legalcaselink', name='case'),
        migrations.AlterField(model_name='legalcaselink', name='legacy_case_id', field=models.PositiveBigIntegerField(unique=True)),
    ]
