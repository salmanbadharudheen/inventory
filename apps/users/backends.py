from django.contrib.auth.backends import ModelBackend


class OrganizationAwareModelBackend(ModelBackend):
    """Block non-superuser authentication for users in inactive organizations."""

    def user_can_authenticate(self, user):
        base_allowed = super().user_can_authenticate(user)
        if not base_allowed:
            return False

        if user.is_superuser:
            return True

        organization = getattr(user, 'organization', None)
        if organization is None:
            return True

        return bool(organization.is_active)
