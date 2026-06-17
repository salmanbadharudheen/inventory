from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.assets.models import Asset
from apps.assets.code_generators import generate_codes_for_asset


class Command(BaseCommand):
    help = 'Generate barcode / QR code / label for all assets that are missing them.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org',
            dest='org',
            default=None,
            help='Limit to a single organisation (slug or numeric id).',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help='Regenerate codes even for assets that already have them.',
        )
        parser.add_argument(
            '--payload-prefix',
            dest='payload_prefix',
            default=None,
            help='Optional two-letter payload prefix to force in generated barcodes (e.g. TC).',
        )

    def handle(self, *args, **options):
        org_filter = options['org']
        force = options['force']

        qs = (
            Asset.objects
            .filter(is_deleted=False)
            .exclude(asset_tag__isnull=True)
            .exclude(asset_tag='')
        )

        if org_filter:
            if org_filter.isdigit():
                qs = qs.filter(organization_id=int(org_filter))
            else:
                qs = qs.filter(organization__slug=org_filter)

        if not force:
            qs = qs.filter(
                Q(barcode_image='') | Q(barcode_image__isnull=True) |
                Q(qr_code_image='') | Q(qr_code_image__isnull=True) |
                Q(label_image='') | Q(label_image__isnull=True)
            )

        qs = qs.distinct()
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('All assets already have barcode, QR code and label. Nothing to do.'))
            return

        self.stdout.write(f'Processing {total} asset(s)...')

        success = 0
        errors = 0
        for asset in qs.iterator(chunk_size=200):
            try:
                generate_codes_for_asset(asset, payload_prefix=options.get('payload_prefix'))
                success += 1
                if success % 50 == 0:
                    self.stdout.write(f'  {success}/{total} done...')
            except Exception as exc:
                errors += 1
                self.stdout.write(self.style.WARNING(f'  Failed: {asset.asset_tag} — {exc}'))

        self.stdout.write(
            self.style.SUCCESS(f'\nDone. {success} generated, {errors} errors out of {total} assets.')
        )

