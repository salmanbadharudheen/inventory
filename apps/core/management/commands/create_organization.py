from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.core.models import Organization


class Command(BaseCommand):
    help = "Create a new organization and optionally assign an existing user to it"

    def add_arguments(self, parser):
        parser.add_argument("name", help="Organization name")
        parser.add_argument(
            "--slug",
            dest="slug",
            help="Explicit slug to use. Defaults to a slugified version of the name.",
        )
        parser.add_argument(
            "--admin-username",
            dest="admin_username",
            help="Existing username to assign to the new organization.",
        )

    def handle(self, *args, **options):
        name = options["name"].strip()
        if not name:
            raise CommandError("Organization name cannot be empty.")

        requested_slug = (options.get("slug") or slugify(name)).strip()
        if not requested_slug:
            raise CommandError("Unable to generate a valid slug. Pass --slug explicitly.")

        if Organization.objects.filter(slug=requested_slug).exists():
            raise CommandError(f'Organization slug "{requested_slug}" already exists.')

        organization = Organization.objects.create(name=name, slug=requested_slug)
        self.stdout.write(
            self.style.SUCCESS(
                f'Created organization "{organization.name}" with slug "{organization.slug}".'
            )
        )

        admin_username = options.get("admin_username")
        if not admin_username:
            return

        User = get_user_model()
        try:
            user = User.objects.get(username=admin_username)
        except User.DoesNotExist as exc:
            organization.delete()
            raise CommandError(f'User "{admin_username}" does not exist. Rolled back organization creation.') from exc

        user.organization = organization
        user.save(update_fields=["organization"])
        self.stdout.write(
            self.style.SUCCESS(
                f'Assigned user "{user.username}" to organization "{organization.name}".'
            )
        )