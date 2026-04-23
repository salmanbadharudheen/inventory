from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from apps.core.models import Organization

User = get_user_model()

class LogoutTest(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'password123'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_logout_button_visibility(self):
        # Log in
        login_success = self.client.login(username=self.username, password=self.password)
        self.assertTrue(login_success)

        # Access dashboard (assuming 'dashboard' is the home or main view that uses base.html)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # Check for Logout text
        self.assertContains(response, 'Logout')
        # Check for logout URL in form action
        self.assertContains(response, 'action="/accounts/logout/"')

    def test_logout_functionality(self):
        self.client.login(username=self.username, password=self.password)
        
        # Post to logout (standard django logout uses POST by default if configured, or GET depending on view)
        # Using the standard url 'logout' which usually resolves to /accounts/logout/
        response = self.client.post(reverse('logout'))
        
        # Should redirect to login page (as per LOGOUT_REDIRECT_URL in settings)
        # LOGOUT_REDIRECT_URL = '/accounts/login/'
        self.assertRedirects(response, '/accounts/login/')
        
        # Verify user is logged out
        response = self.client.get(reverse('dashboard'))
        # If dashboard requires login, it might redirect. If not, we check for "Login" button.
        # Assuming dashboard might be public or at least accessible.
        # But 'base.html' check: if not user.is_authenticated -> Login button.
        
        # Let's check for Login button if we get a 200, or redirect if protected.
        if response.status_code == 200:
            self.assertContains(response, 'Login')
            self.assertNotContains(response, 'Logout')


class CreateOrganizationCommandTest(TestCase):
    def test_creates_organization_from_name(self):
        call_command('create_organization', 'Northwind Trading')

        organization = Organization.objects.get(name='Northwind Trading')
        self.assertEqual(organization.slug, 'northwind-trading')

    def test_assigns_existing_user_when_requested(self):
        user = User.objects.create_user(username='orgadmin', password='password123')

        call_command('create_organization', 'Contoso Ops', admin_username='orgadmin')

        user.refresh_from_db()
        self.assertIsNotNone(user.organization)
        self.assertEqual(user.organization.name, 'Contoso Ops')

    def test_rejects_duplicate_slug(self):
        Organization.objects.create(name='Existing Org', slug='existing-org')

        with self.assertRaises(CommandError):
            call_command('create_organization', 'Existing Org')
