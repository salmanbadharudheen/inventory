from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.assets.models import Asset
from apps.core.models import Organization


class Command(BaseCommand):
    help = "Soft-delete an asset by organization and asset tag."

    def add_arguments(self, parser):
        parser.add_argument("--org", required=True, help="Organization name (case-insensitive exact match)")
        parser.add_argument("--tag", required=True, help="Asset tag, e.g. XX-VIS-0001-26")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply deletion. Without this flag, command runs in dry-run mode.",
        )

    def handle(self, *args, **options):
        org_name = (options.get("org") or "").strip()
        tag = (options.get("tag") or "").strip()
        apply_delete = bool(options.get("apply"))

        if not org_name:
            raise CommandError("--org is required")
        if not tag:
            raise CommandError("--tag is required")

        org = Organization.objects.filter(name__iexact=org_name).first()
        if not org:
            raise CommandError(f"Organization not found: {org_name}")

        qs = Asset.objects.filter(organization=org, asset_tag=tag)
        if not qs.exists():
            self.stdout.write(self.style.WARNING("No asset found for the provided org+tag."))
            return

        active_qs = qs.filter(is_deleted=False)
        already_deleted = qs.filter(is_deleted=True).count()

        self.stdout.write(f"Organization: {org.name} (id={org.id})")
        self.stdout.write(f"Asset tag: {tag}")
        self.stdout.write(f"Matches: {qs.count()} | Active: {active_qs.count()} | Already deleted: {already_deleted}")

        if not apply_delete:
            self.stdout.write(self.style.WARNING("Dry-run only. Re-run with --apply to perform deletion."))
            return

        updated = active_qs.update(is_deleted=True, deleted_at=timezone.now())
        self.stdout.write(self.style.SUCCESS(f"Soft-deleted assets: {updated}"))
