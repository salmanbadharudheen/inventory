from django.core.management.base import BaseCommand
from apps.assets.models import Asset
from apps.assets.code_generators import generate_codes_for_asset


class Command(BaseCommand):
    help = 'Generate barcode and QR code for all assets that are missing them'

    def handle(self, *args, **options):
        assets = Asset.objects.filter(asset_tag__isnull=False).exclude(asset_tag='')
        missing = assets.filter(
            barcode_image='',
        ) | assets.filter(
            qr_code_image='',
        ) | assets.filter(
            barcode_image__isnull=True,
        ) | assets.filter(
            qr_code_image__isnull=True,
        )
        missing = missing.distinct()

        total = missing.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('All assets already have barcode and QR code.'))
            return

        self.stdout.write(f'Found {total} assets missing barcode/QR code. Generating...')

        success = 0
        for asset in missing.iterator():
            try:
                generate_codes_for_asset(asset)
                success += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Failed: {asset.asset_tag} - {e}'))

        self.stdout.write(self.style.SUCCESS(f'Done. Generated codes for {success}/{total} assets.'))
