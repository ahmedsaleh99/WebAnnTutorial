from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from annotations.models import ProjectTemplate, UserSecurity


class AuthenticationEndpointTests(APITestCase):
    password = "CorrectHorseBattery9!"

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="annotator",
            email="annotator@example.com",
            password=self.password,
        )
        UserSecurity.objects.create(user=self.user, must_change_password=True)

    def authenticate_with_token(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    @override_settings(WEBANN_SECURE_COOKIES=True)
    def test_login_returns_token_safe_user_data_and_media_cookie(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": self.user.username, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertNotIn("password", response.data["user"])
        self.assertEqual(response.data["user"]["role"], "annotator")
        self.assertTrue(response.data["user"]["must_change_password"])

        media_cookie = response.cookies["webann_media_token"]
        self.assertTrue(media_cookie["httponly"])
        self.assertTrue(media_cookie["secure"])
        self.assertEqual(media_cookie["samesite"], "Strict")

    def test_invalid_password_and_inactive_user_have_same_error(self):
        wrong_password_response = self.client.post(
            "/api/auth/login/",
            {"username": self.user.username, "password": "wrong"},
            format="json",
        )
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        inactive_user_response = self.client.post(
            "/api/auth/login/",
            {"username": self.user.username, "password": self.password},
            format="json",
        )

        expected_error = {"detail": "Invalid username or password."}
        self.assertEqual(
            wrong_password_response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            inactive_user_response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(wrong_password_response.data, expected_error)
        self.assertEqual(inactive_user_response.data, expected_error)

    def test_current_user_requires_a_valid_token(self):
        anonymous_response = self.client.get("/api/auth/me/")
        token = Token.objects.create(user=self.user)
        self.authenticate_with_token(token)

        authenticated_response = self.client.get("/api/auth/me/")

        self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(authenticated_response.status_code, status.HTTP_200_OK)
        self.assertEqual(authenticated_response.data["username"], self.user.username)

    def test_password_change_rotates_token_and_clears_required_change(self):
        old_token = Token.objects.create(user=self.user)
        self.authenticate_with_token(old_token)

        response = self.client.post(
            "/api/auth/password-change/",
            {
                "current_password": self.password,
                "new_password": "EvenBetterPassword9!",
                "new_password_confirmation": "EvenBetterPassword9!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data["token"], old_token.key)
        self.assertFalse(Token.objects.filter(key=old_token.key).exists())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("EvenBetterPassword9!"))
        self.user.security_settings.refresh_from_db()
        self.assertFalse(self.user.security_settings.must_change_password)

    def test_password_change_rejects_wrong_mismatched_and_weak_passwords(self):
        token = Token.objects.create(user=self.user)
        self.authenticate_with_token(token)

        wrong_current_response = self.client.post(
            "/api/auth/password-change/",
            {
                "current_password": "wrong",
                "new_password": "EvenBetterPassword9!",
                "new_password_confirmation": "EvenBetterPassword9!",
            },
            format="json",
        )
        mismatch_response = self.client.post(
            "/api/auth/password-change/",
            {
                "current_password": self.password,
                "new_password": "EvenBetterPassword9!",
                "new_password_confirmation": "DifferentPassword9!",
            },
            format="json",
        )
        weak_password_response = self.client.post(
            "/api/auth/password-change/",
            {
                "current_password": self.password,
                "new_password": "short",
                "new_password_confirmation": "short",
            },
            format="json",
        )

        self.assertEqual(
            wrong_current_response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(mismatch_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            weak_password_response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertTrue(Token.objects.filter(key=token.key).exists())

    def test_logout_revokes_the_current_token(self):
        token = Token.objects.create(user=self.user)
        self.authenticate_with_token(token)

        logout_response = self.client.post("/api/auth/logout/")
        current_user_response = self.client.get("/api/auth/me/")

        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token.key).exists())
        self.assertEqual(
            current_user_response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_media_authorization_requires_cookie_for_an_active_user(self):
        token = Token.objects.create(user=self.user)
        missing_cookie_response = self.client.get("/api/auth/media/authorize/")
        self.client.cookies["webann_media_token"] = token.key

        valid_cookie_response = self.client.get("/api/auth/media/authorize/")
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        inactive_user_response = self.client.get("/api/auth/media/authorize/")

        self.assertEqual(
            missing_cookie_response.status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(valid_cookie_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            inactive_user_response.status_code, status.HTTP_401_UNAUTHORIZED
        )


class ConfigurationPermissionTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.annotator = user_model.objects.create_user(
            username="reader", password="ReaderPassword9!"
        )
        self.manager = user_model.objects.create_user(
            username="manager", password="ManagerPassword9!", is_staff=True
        )
        self.admin = user_model.objects.create_superuser(
            username="admin", password="AdminPassword9!"
        )
        ProjectTemplate.objects.create(
            name="Existing template", key="existing", version=1
        )

    def authenticate(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_anonymous_user_cannot_read_configuration(self):
        response = self.client.get("/api/templates/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_all_authenticated_roles_can_read_configuration(self):
        for user in (self.annotator, self.manager, self.admin):
            with self.subTest(username=user.username):
                self.authenticate(user)

                response = self.client.get("/api/templates/")

                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_admin_can_create_configuration(self):
        for user, expected_status in (
            (self.annotator, status.HTTP_403_FORBIDDEN),
            (self.manager, status.HTTP_403_FORBIDDEN),
            (self.admin, status.HTTP_201_CREATED),
        ):
            with self.subTest(username=user.username):
                self.authenticate(user)
                payload = {
                    "name": f"Template for {user.username}",
                    "key": f"template-{user.username}",
                    "version": 1,
                }

                response = self.client.post("/api/templates/", payload, format="json")

                self.assertEqual(response.status_code, expected_status)
