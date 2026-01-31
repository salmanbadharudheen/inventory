from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

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
