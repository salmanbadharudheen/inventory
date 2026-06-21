from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0042_asset_code_unique_per_org_non_blank'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='barcode_payload_value',
            field=models.CharField(
                blank=True,
                db_index=True,
                editable=False,
                help_text='Stored barcode payload used for scanning/printing. New assets can use a compact numeric value.',
                max_length=64,
                null=True,
                verbose_name='Barcode Payload',
            ),
        ),
    ]
