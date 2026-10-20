from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

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
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.pk))
        log_acesso = UserAccessLog.objects.get(user=self.user)
        self.assertEqual(self.client.session.get("access_log_id"), log_acesso.pk)

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


class AuthAccessAndLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="regular-user",
            password="secure-test-password",
        )
        self.logs_url = reverse("user-logs")
        self.add_user_url = reverse("auth-add-user")
        self.logout_url = reverse("auth-logout")

    def test_anonymous_users_cannot_access_internal_pages(self):
        for url in (self.logs_url, self.add_user_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("auth-login-basic")))

    def test_regular_users_cannot_add_accounts(self):
        self.client.force_login(self.user)
        response = self.client.get(self.add_user_url)
        self.assertEqual(response.status_code, 403)

    def test_staff_users_can_open_account_creation_page(self):
        staff_user = User.objects.create_user(
            username="staff-user",
            password="secure-test-password",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        response = self.client.get(self.add_user_url)

        self.assertEqual(response.status_code, 200)

    def test_regular_users_only_see_their_own_access_logs(self):
        other_user = User.objects.create_user(
            username="other-user",
            password="another-secure-password",
        )
        own_log = UserAccessLog.objects.create(user=self.user, username=self.user.username)
        other_log = UserAccessLog.objects.create(user=other_user, username=other_user.username)
        self.client.force_login(self.user)

        response = self.client.get(self.logs_url)

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["logs"],
            [own_log],
        )
        self.assertNotContains(response, other_log.username)

    def test_get_does_not_log_out_and_post_does(self):
        log = UserAccessLog.objects.create(user=self.user, username=self.user.username)
        self.client.force_login(self.user)
        session = self.client.session
        session["access_log_id"] = log.pk
        session.save()

        get_response = self.client.get(self.logout_url)
        self.assertEqual(get_response.status_code, 405)
        self.assertTrue(self.client.session.get("_auth_user_id"))

        post_response = self.client.post(self.logout_url)
        self.assertRedirects(
            post_response,
            reverse("auth-login-basic"),
            fetch_redirect_response=False,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        log.refresh_from_db()
        self.assertIsNotNone(log.logout_time)
        self.assertGreaterEqual(log.duration, timedelta(0))

    def test_logout_post_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(self.logout_url)

        self.assertEqual(response.status_code, 403)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reset-user",
            email="reset@example.test",
            password="original-secure-password",
        )
        self.reset_url = reverse("auth-reset-password")

    def set_reset_session(self, expires_at):
        session = self.client.session
        session["reset_token"] = "012345"
        session["reset_user_id"] = self.user.pk
        session["reset_expires_at"] = expires_at
        session["reset_attempts"] = 0
        session.save()

    def test_expired_code_is_rejected_and_cleared(self):
        self.set_reset_session(int((timezone.now() - timedelta(seconds=1)).timestamp()))

        response = self.client.post(
            self.reset_url,
            {"codigo_reset": "012345", "password": "New-Password-987!"},
        )

        self.assertRedirects(
            response,
            reverse("auth-forgot-password-basic"),
            fetch_redirect_response=False,
        )
        self.assertNotIn("reset_token", self.client.session)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("original-secure-password"))

    def test_five_invalid_codes_invalidate_the_reset_session(self):
        self.set_reset_session(int((timezone.now() + timedelta(minutes=15)).timestamp()))

        for _ in range(5):
            self.client.post(
                self.reset_url,
                {"codigo_reset": "wrong", "password": "New-Password-987!"},
            )

        self.assertNotIn("reset_token", self.client.session)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("original-secure-password"))

    def test_non_ascii_code_is_rejected(self):
        self.set_reset_session(int((timezone.now() + timedelta(minutes=15)).timestamp()))

        response = self.client.post(
            self.reset_url,
            {"codigo_reset": "１２３４５６", "password": "N3w-Strong-Passphrase!"},
        )

        self.assertRedirects(response, self.reset_url, fetch_redirect_response=False)
        self.assertEqual(self.client.session["reset_attempts"], 1)

    def test_missing_new_password_is_rejected(self):
        self.set_reset_session(int((timezone.now() + timedelta(minutes=15)).timestamp()))

        response = self.client.post(
            self.reset_url,
            {"codigo_reset": "012345", "password": ""},
        )

        self.assertRedirects(response, self.reset_url, fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("original-secure-password"))

    def test_valid_code_updates_password_and_clears_reset_session(self):
        self.set_reset_session(int((timezone.now() + timedelta(minutes=15)).timestamp()))
        new_password = "N3w-Strong-Passphrase!"

        response = self.client.post(
            self.reset_url,
            {"codigo_reset": "012345", "password": new_password},
        )

        self.assertRedirects(
            response,
            reverse("auth-login-basic"),
            fetch_redirect_response=False,
        )
        self.assertNotIn("reset_token", self.client.session)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
