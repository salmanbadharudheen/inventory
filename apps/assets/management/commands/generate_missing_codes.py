from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from apps.assets.models import Asset
from apps.assets.code_generators import generate_codes_for_asset


class Command(BaseCommand):
    help = 'Generate barcode and QR code for all assets that are missing them'

    @staticmethod
    def _file_missing(file_field):
        if not file_field:
            return True
        try:
            return not default_storage.exists(file_field.name)
        except Exception:
            return True

    @classmethod
    def _asset_needs_codes(cls, asset):
        return cls._file_missing(asset.barcode_image) or cls._file_missing(asset.qr_code_image)

    def handle(self, *args, **options):
        assets = Asset.objects.filter(asset_tag__isnull=False).exclude(asset_tag='')

        # We check both DB fields and actual file existence in storage.
        missing_ids = []
        for asset in assets.iterator(chunk_size=500):
            if self._asset_needs_codes(asset):
                missing_ids.append(asset.id)

        total = len(missing_ids)
        if total == 0:
            self.stdout.write(self.style.SUCCESS('All assets already have barcode and QR code.'))
            return

        self.stdout.write(f'Found {total} assets missing barcode/QR code. Generating...')

        success = 0
        for asset in Asset.objects.filter(id__in=missing_ids).iterator(chunk_size=200):
            try:
                generate_codes_for_asset(asset)
                success += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Failed: {asset.asset_tag} - {e}'))

        self.stdout.write(self.style.SUCCESS(f'Done. Generated codes for {success}/{total} assets.'))
