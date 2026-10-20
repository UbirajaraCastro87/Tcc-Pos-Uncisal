from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import UserAccessLog


class AuthLoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="login-test",
            password="secure-test-password",
        )

    def test_valid_credentials_log_in_without_second_factor(self):
        response = self.client.post(
            reverse("auth-login-basic"),
            {"username": self.user.username, "password": "secure-test-password"},
        )

        self.assertRedirects(response, reverse("user-logs"), fetch_redirect_response=False)
        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(self.user.pk),
        )
        log_acesso = UserAccessLog.objects.get(user=self.user)
        self.assertEqual(
            self.client.session.get("access_log_id"),
            log_acesso.pk,
        )

    def test_invalid_credentials_do_not_log_in_or_create_access_log(self):
        response = self.client.post(
            reverse("auth-login-basic"),
            {"username": self.user.username, "password": "wrong-password"},
        )

        self.assertRedirects(
            response,
            reverse("auth-login-basic"),
            fetch_redirect_response=False,
        )
        self.assertNotIn("_auth_user_id", self.client.session)

        
        self.assertFalse(UserAccessLog.objects.exists()) 
