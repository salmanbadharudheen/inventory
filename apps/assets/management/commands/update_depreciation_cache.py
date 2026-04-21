from django.core.management.base import BaseCommand
from apps.assets.models import Asset
from decimal import Decimal


class Command(BaseCommand):
    help = 'Recalculate and update cached_accumulated_depreciation and cached_nbv for all assets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Number of assets to process per batch (default: 500)',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']

        qs = Asset.objects.filter(
            is_deleted=False,
            purchase_price__isnull=False,
            purchase_price__gt=0,
        ).only(
            'id', 'purchase_price', 'purchase_date', 'useful_life_years',
            'salvage_value', 'depreciation_method', 'expected_units',
            'units_consumed', 'cached_accumulated_depreciation', 'cached_nbv',
        )

        total = qs.count()
        self.stdout.write(f'Found {total} assets to update...')

        updated = 0
        skipped = 0

        for offset in range(0, total, batch_size):
            batch = list(qs[offset:offset + batch_size])
            to_update = []

            for asset in batch:
                try:
                    acc_dep = asset.accumulated_depreciation
                    nbv = (asset.purchase_price or Decimal('0')) - acc_dep

                    # Only update if values differ (avoid unnecessary writes)
                    if asset.cached_accumulated_depreciation != acc_dep or asset.cached_nbv != nbv:
                        asset.cached_accumulated_depreciation = acc_dep
                        asset.cached_nbv = nbv
                        to_update.append(asset)
                except Exception as e:
                    self.stderr.write(f'  Error on asset id={asset.id}: {e}')
                    skipped += 1
                    continue

            if to_update:
                Asset.objects.bulk_update(
                    to_update,
                    ['cached_accumulated_depreciation', 'cached_nbv'],
                    batch_size=batch_size,
                )
                updated += len(to_update)

            done = min(offset + batch_size, total)
            self.stdout.write(f'  Processed {done}/{total}...')

        self.stdout.write(self.style.SUCCESS(
            f'Done. Updated: {updated}, Skipped (errors): {skipped}, Unchanged: {total - updated - skipped}'
        ))
