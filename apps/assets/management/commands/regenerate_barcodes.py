from django.core.management.base import BaseCommand

from apps.assets.code_generators import AssetCodeGenerator
from apps.assets.models import Asset


class Command(BaseCommand):
    help = 'Regenerate barcode images for existing assets using the current barcode rule.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org',
            dest='org',
            default=None,
            help='Limit to a single organisation (slug or numeric id).',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Process at most N assets.',
        )

    def handle(self, *args, **options):
        org_filter = options['org']
        limit = options['limit']

        qs = (
            Asset.objects
            .filter(is_deleted=False)
            .exclude(asset_tag__isnull=True)
            .exclude(asset_tag='')
            .order_by('asset_tag')
        )

        if org_filter:
            if org_filter.isdigit():
                qs = qs.filter(organization_id=int(org_filter))
            else:
                qs = qs.filter(organization__slug=org_filter)

        if limit:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No assets found. Nothing to do.'))
            return

        self.stdout.write(f'Processing {total} asset(s)...')

        success = 0
        errors = 0
        for asset in qs.iterator(chunk_size=200):
            try:
                path = AssetCodeGenerator.save_barcode_to_file(asset.asset_tag)
                if path:
                    asset.barcode_image = path
                    asset.save(update_fields=['barcode_image'])
                success += 1
                if success % 50 == 0:
                    self.stdout.write(f'  {success}/{total} done...')
            except Exception as exc:
                errors += 1
                self.stdout.write(self.style.WARNING(f'  Failed: {asset.asset_tag} — {exc}'))

        self.stdout.write(
            self.style.SUCCESS(f'\nDone. {success} regenerated, {errors} errors out of {total} assets.')
        )