from django.db import migrations, models
from django.db.models import Count


def normalize_and_deduplicate_asset_codes(apps, schema_editor):
    Asset = apps.get_model('assets', 'Asset')

    # Normalize empty strings to NULL so blank values are excluded by the conditional constraint.
    Asset.objects.filter(asset_code='').update(asset_code=None)

    duplicate_groups = (
        Asset.objects
        .filter(asset_code__isnull=False)
        .exclude(asset_code='')
        .values('organization', 'asset_code')
        .annotate(cnt=Count('id'))
        .filter(cnt__gt=1)
    )

    for group in duplicate_groups:
        org_id = group['organization']
        duplicated_code = group['asset_code']

        org_existing_codes = set(
            Asset.objects
            .filter(organization_id=org_id, asset_code__isnull=False)
            .exclude(asset_code='')
            .values_list('asset_code', flat=True)
        )

        assets = list(
            Asset.objects
            .filter(organization_id=org_id, asset_code=duplicated_code)
            .order_by('created_at', 'id')
        )

        # Keep the first asset with the original code, rename the rest.
        for index, asset in enumerate(assets[1:], start=2):
            counter = index
            while True:
                suffix = f"-{counter}"
                base_len = max(1, 100 - len(suffix))
                candidate = f"{duplicated_code[:base_len]}{suffix}"
                if candidate not in org_existing_codes:
                    break
                counter += 1

            asset.asset_code = candidate
            asset.save(update_fields=['asset_code'])
            org_existing_codes.add(candidate)


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0041_asset_rfid_tag_asset_assets_asse_rfid_ta_1b672e_idx'),
    ]

    operations = [
        migrations.RunPython(normalize_and_deduplicate_asset_codes, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='asset',
            constraint=models.UniqueConstraint(
                condition=models.Q(asset_code__isnull=False) & ~models.Q(asset_code=''),
                fields=('organization', 'asset_code'),
                name='unique_asset_code_per_org_non_blank',
            ),
        ),
    ]
