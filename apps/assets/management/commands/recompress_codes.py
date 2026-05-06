"""
Recompress existing QR/barcode/label PNG files in-place.

Converts each file to a smaller mode (1-bit for QR/barcode, palette for label)
and writes it back with maximum PNG compression. Skips files that are already
small. Safe to re-run; idempotent.

Usage:
    python manage.py recompress_codes
    python manage.py recompress_codes --dry-run
    python manage.py recompress_codes --org <org_id>
"""
from pathlib import Path

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from PIL import Image

from apps.assets.models import Asset


def _recompress_one(rel_path, mode, palette_colors=None):
    """Recompress a single file. Returns (old_size, new_size) or (None, None)."""
    if not rel_path:
        return None, None
    try:
        if not default_storage.exists(rel_path):
            return None, None
        with default_storage.open(rel_path, 'rb') as f:
            img = Image.open(f)
            img.load()

        # Read original size
        try:
            old_size = default_storage.size(rel_path)
        except Exception:
            old_size = 0

        if mode == '1':
            new_img = img.convert('1')
        elif mode == 'P':
            new_img = img.convert(
                'P',
                palette=Image.Palette.ADAPTIVE,
                colors=palette_colors or 64,
            )
        else:
            new_img = img

        # Save to a temp buffer, then write back via storage
        import io
        buf = io.BytesIO()
        new_img.save(buf, 'PNG', optimize=True, compress_level=9)
        new_bytes = buf.getvalue()
        new_size = len(new_bytes)

        # Only overwrite if the new file is actually smaller
        if old_size and new_size >= old_size:
            return old_size, old_size

        # Replace via storage API (delete + save) to support both local & remote
        default_storage.delete(rel_path)
        from django.core.files.base import ContentFile
        default_storage.save(rel_path, ContentFile(new_bytes))
        return old_size, new_size
    except Exception as e:
        print(f"  ! failed on {rel_path}: {e}")
        return None, None


class Command(BaseCommand):
    help = "Recompress existing QR/barcode/label PNGs to reduce storage."

    def add_arguments(self, parser):
        parser.add_argument('--org', type=int, help='Limit to a single organization id')
        parser.add_argument('--dry-run', action='store_true', help='Report potential savings without writing')
        parser.add_argument('--limit', type=int, help='Process at most N assets')

    def handle(self, *args, **opts):
        qs = Asset.objects.all()
        if opts.get('org'):
            qs = qs.filter(organization_id=opts['org'])
        if opts.get('limit'):
            qs = qs[: opts['limit']]

        total_before = 0
        total_after = 0
        processed = 0

        for asset in qs.iterator(chunk_size=200):
            for field, mode, colors in (
                ('barcode_image', '1', None),
                ('qr_code_image', '1', None),
                ('label_image', 'P', 64),
            ):
                f = getattr(asset, field, None)
                if not f:
                    continue
                rel_path = f.name
                if opts.get('dry_run'):
                    # Just report the current size
                    try:
                        if default_storage.exists(rel_path):
                            total_before += default_storage.size(rel_path)
                    except Exception:
                        pass
                    continue

                old_size, new_size = _recompress_one(rel_path, mode, colors)
                if old_size is not None:
                    total_before += old_size
                    total_after += new_size or old_size
                    processed += 1

        if opts.get('dry_run'):
            self.stdout.write(self.style.SUCCESS(
                f"Dry run: total existing code-file size = {total_before / 1024:.1f} KB"
            ))
            return

        saved = total_before - total_after
        self.stdout.write(self.style.SUCCESS(
            f"Recompressed {processed} files. "
            f"Before: {total_before/1024:.1f} KB, "
            f"After: {total_after/1024:.1f} KB, "
            f"Saved: {saved/1024:.1f} KB "
            f"({(saved/total_before*100) if total_before else 0:.1f}%)"
        ))
