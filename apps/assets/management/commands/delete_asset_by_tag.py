from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.assets.models import Asset
from apps.core.models import Organization


class Command(BaseCommand):
    help = "Soft-delete an asset by UUID or by org+tag."

    def add_arguments(self, parser):
        parser.add_argument("--id", help="Asset UUID, e.g. 0c6dedc3-e9e2-4d7e-b108-4bb495fefbb8")
        parser.add_argument("--org", help="Organization name (case-insensitive)")
        parser.add_argument("--tag", help="Asset tag, e.g. XX-VIS-0001-26")
        parser.add_argument(
            "--any-org",
            action="store_true",
            help="Allow tag-based delete across all orgs (blocked by default if org is omitted).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply deletion. Without this flag, command runs in dry-run mode.",
        )

    def handle(self, *args, **options):
        asset_id = (options.get("id") or "").strip()
        org_name = (options.get("org") or "").strip()
        tag = (options.get("tag") or "").strip()
        any_org = bool(options.get("any_org"))
        apply_delete = bool(options.get("apply"))

        if not asset_id and not tag:
            raise CommandError("Provide either --id or --tag")

        org = None
        if org_name:
            org = Organization.objects.filter(name__iexact=org_name).first()
            if not org:
                candidates = Organization.objects.filter(name__icontains=org_name).values_list("name", flat=True)[:5]
                hint = ", ".join(candidates) if candidates else "no similar organizations found"
                raise CommandError(f"Organization not found: {org_name}. Suggestions: {hint}")

        qs = Asset.objects.all()
        if asset_id:
            qs = qs.filter(pk=asset_id)
        else:
            qs = qs.filter(asset_tag=tag)

        if org is not None:
            qs = qs.filter(organization=org)
        elif tag and not any_org:
            raise CommandError("For tag deletion, provide --org, or use --any-org intentionally.")

        if not qs.exists():
            self.stdout.write(self.style.WARNING("No asset found for the provided filters."))
            return

        active_qs = qs.filter(is_deleted=False)
        already_deleted = qs.filter(is_deleted=True).count()

        sample = list(
            qs.select_related("organization").values_list("id", "asset_tag", "organization__name", "is_deleted")[:5]
        )
        for row in sample:
            self.stdout.write(
                f"Match: id={row[0]} | tag={row[1]} | org={row[2]} | deleted={row[3]}"
            )

        if asset_id:
            self.stdout.write(f"Asset id: {asset_id}")
        if tag:
            self.stdout.write(f"Asset tag: {tag}")
        if org is not None:
            self.stdout.write(f"Organization: {org.name} (id={org.id})")

        self.stdout.write(f"Matches: {qs.count()} | Active: {active_qs.count()} | Already deleted: {already_deleted}")

        if not apply_delete:
            self.stdout.write(self.style.WARNING("Dry-run only. Re-run with --apply to perform deletion."))
            return

        updated = active_qs.update(is_deleted=True, deleted_at=timezone.now())
        self.stdout.write(self.style.SUCCESS(f"Soft-deleted assets: {updated}"))
