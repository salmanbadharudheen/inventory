from django.test import TestCase
from django.urls import reverse

class SignUpTest(TestCase):
    def test_signup_page_status_code(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_signup_page_template(self):
        response = self.client.get(reverse('signup'))
        self.assertTemplateUsed(response, 'registration/signup.html')
        self.assertTemplateUsed(response, 'base_auth.html')
