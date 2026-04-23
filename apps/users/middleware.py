from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
from django.urls import reverse


class OrganizationActiveSessionMiddleware:
    """Force logout for non-superusers whose organization has been deactivated."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or user.is_superuser:
            return self.get_response(request)

        organization = getattr(user, 'organization', None)
        if organization and not organization.is_active:
            auth_logout(request)
            messages.error(request, 'Your organization has been deactivated. Please contact the system owner.')
            return redirect(reverse('login'))

        return self.get_response(request)


class SuperuserOrganizationPortalMiddleware:
    """Keep software owner in the organization-control portal only."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not user.is_superuser:
            return self.get_response(request)

        org_mode = bool(request.session.get('superuser_org_mode') and user.organization_id)

        if org_mode:
            return self.get_response(request)

        path = request.path
        blocked_prefixes = (
            '/users/admin/users',
            '/users/add/',
            '/users/',
            '/assets/',
            '/locations/',
            '/api/',
            '/admin/',
        )

        if path.startswith('/users/admin/organizations') or path in ('/users/admin/', '/users/admin'):
            return self.get_response(request)

        if path.startswith('/users/owner/') or path.startswith('/accounts/logout/') or path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        if path.startswith(blocked_prefixes):
            messages.info(request, 'Owner account is limited to organization control pages only.')
            return redirect(reverse('admin-orgs'))

        if not (
            path.startswith('/users/admin/organizations')
            or path in ('/users/admin/', '/users/admin')
            or path.startswith('/users/owner/')
            or path.startswith('/accounts/logout/')
            or path.startswith('/static/')
            or path.startswith('/media/')
        ):
            messages.info(request, 'Owner account is limited to organization control pages only.')
            return redirect(reverse('admin-orgs'))

        return self.get_response(request)
