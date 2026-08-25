from django.db import migrations


def normalize_negative_salvage_values(apps, schema_editor):
    AssetDisposal = apps.get_model('assets', 'AssetDisposal')
    AssetDisposal.objects.filter(estimated_salvage_value__lt=0).update(
        estimated_salvage_value=0
    )


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0044_alter_assetdisposal_estimated_salvage_value'),
    ]

    operations = [
        migrations.RunPython(
            normalize_negative_salvage_values,
            migrations.RunPython.noop,
        ),
    ]