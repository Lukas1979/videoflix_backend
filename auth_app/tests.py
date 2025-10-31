import os

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.test import APITestCase
from unittest.mock import patch

from .api.token_generators import AccountActivationTokenGenerator, PasswordResetTokenGenerator


class RegisterViewTests(APITestCase):
    """
    Test suite for /api/register/ endpoint.
    """

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('register')
        cls.valid_payload = {"email": "newuser@example.com", "password": "StrongPassword123", "confirmed_password": "StrongPassword123"}
        cls.invalid_payload_password_mismatch = {
            "email": "user2@example.com", "password": "password123", "confirmed_password": "differentpassword"
        }
        cls.invalid_payload_missing_fields = {"email": "", "password": "password123", "confirmed_password": "password123"}


    def test_register_with_valid_data(self):
        """POST /api/register/ with valid data → 201"""

        response = self.client.post(self.url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_with_password_mismatch(self):
        """POST /api/register/ with mismatched passwords → 400 + error message"""

        response = self.client.post(self.url, self.invalid_payload_password_mismatch, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirmed_password", response.data)

    def test_register_with_missing_email_value(self):
        """POST /api/register/ with missing email value → 400 + validation errors"""

        response = self.client.post(self.url, self.invalid_payload_missing_fields, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_without_email_field(self):
        """POST /api/register/ without email field → 400"""

        payload = {"password": "SomePassword123", "confirmed_password": "SomePassword123", "username": "newuser@example.com"}
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_existing_email(self):
        """POST /api/register/ with existing email → 400 + 'Email already exists' error"""
        
        User.objects.create_user(username="otheruser", password="SomePassword123", email="newuser@example.com")
        response = self.client.post(self.url, self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"][0], "Email already exists")


class LoginViewTests(APITestCase):
    """
    Test suite for /api/login/ endpoint with JWT cookie authentication.
    """

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('login')
        cls.user = User.objects.create_user(username="testuser@example.com", password="StrongPassword123", email="testuser@example.com")
        cls.valid_payload = {"password": "StrongPassword123", "email": "testuser@example.com"}
        cls.invalid_payload_wrong_password = {"email": "testuser@example.com", "password": "WrongPassword"}
        cls.invalid_payload_nonexistent_user = {"email": "nouser@example.com", "password": "password123"}


    def test_login_with_valid_credentials(self):
        """POST /api/login/ with valid credentials → 200 + JWT cookies"""

        response = self.client.post(self.url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_login_with_wrong_password(self):
        """POST /api/login/ with wrong password → 401 Unauthorized"""

        response = self.client.post(self.url, self.invalid_payload_wrong_password, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_with_nonexistent_user(self):
        """POST /api/login/ with non-existent user → 401 Unauthorized"""

        response = self.client.post(self.url, self.invalid_payload_nonexistent_user, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class LogoutViewTests(APITestCase):
    """
    Test suite for /api/logout/ endpoint with JWT cookie authentication.
    """

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('logout')
        cls.user = User.objects.create_user(username="testuser@example.com", password="StrongPassword123", email="testuser@example.com")

        refresh = RefreshToken.for_user(cls.user)
        cls.access_token = str(refresh.access_token)
        cls.refresh_token = str(refresh)


    def test_logout_with_authenticated_user(self):
        """POST /api/logout/ → 200 + success message + cookies deleted"""

        self.client.cookies['access_token'] = self.access_token
        self.client.cookies['refresh_token'] = self.refresh_token

        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid.")

        self._check_cookies(response)

    def _check_cookies(self, response):
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')


    def test_logout_without_tokens(self):
        """POST /api/logout/ without cookies → 400"""

        response = self.client.post(self.url, {}, format='json')
    
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_invalid_after_logout(self):
        """POST /api/logout/ → refresh token is blacklisted and cannot be used"""

        self.client.cookies['access_token'] = self.access_token
        self.client.cookies['refresh_token'] = self.refresh_token
    
        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, 200)
        with self.assertRaises(TokenError):
            RefreshToken(self.refresh_token).verify()


class TokenRefreshViewTests(APITestCase):
    """
    Test suite for /api/token/refresh/ endpoint with JWT cookie authentication.
    """

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('refresh')
        cls.user = User.objects.create_user(username="testuser@example.com", password="StrongPassword123", email="testuser@example.com")

        refresh = RefreshToken.for_user(cls.user)
        cls.refresh_token = str(refresh)
        cls.access_token = str(refresh.access_token)


    def test_refresh_with_valid_token(self):
        """POST /api/token/refresh/ with valid refresh token → 200 + new access_token cookie"""

        self.client.cookies['refresh_token'] = self.refresh_token
        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Token refreshed")
        self.assertIn("access", response.data)
        self.assertIn("access_token", response.cookies)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertNotEqual(response.cookies["access_token"].value, "")

    def test_refresh_with_missing_token(self):
        """POST /api/token/refresh/ without refresh token → 400"""

        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_refresh_with_invalid_token(self):
        """POST /api/token/refresh/ with invalid refresh token → 401 Unauthorized"""

        self.client.cookies['refresh_token'] = "invalidtoken123"
        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class ActivateAccountViewTests(APITestCase):
    """
    Test suite for /api/activate/<uidb64>/<token>/ endpoint with JWT cookie authentication.
    """
    
    @classmethod
    def setUpTestData(cls):
        cls.base_url = "/api/activate/"
        cls.user = User.objects.create_user(
            username="testuser@example.com", password="StrongPassword123", email="testuser@example.com", is_active=False
        )

        cls.token_generator = AccountActivationTokenGenerator()
        cls.valid_token = cls.token_generator.make_token(cls.user)
        cls.uidb64 = urlsafe_base64_encode(force_bytes(cls.user.pk))
    

    def test_activate_with_valid_token(self):
        """GET with valid uid and token → 200 + user gets activated"""

        url = f"{self.base_url}{self.uidb64}/{self.valid_token}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Account successfully activated.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_activate_with_invalid_token(self):
        """GET with invalid token → 400"""
        
        invalid_token = "invalid-token"
        url = f"{self.base_url}{self.uidb64}/{invalid_token}/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_activate_with_invalid_uid(self):
        """GET with invalid uidb64 → 400"""
        
        invalid_uid = "invaliduid"
        url = f"{self.base_url}{invalid_uid}/{self.valid_token}/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
    
    def test_activate_already_active_user(self):
        """GET for already active user → 200 with 'already active' message"""
        
        self.user.is_active = True
        self.user.save()
        url = f"{self.base_url}{self.uidb64}/{self.valid_token}/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Account is already active.")


class PasswordResetViewTests(APITestCase):
    """
    Test suite for /api/password_reset/ endpoint with JWT cookie authentication.
    """

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('password_reset')
        cls.user = User.objects.create_user(username="testuser@example.com", password="StrongPassword123", email="testuser@example.com")
        cls.valid_payload = {"email": "testuser@example.com"}
        cls.invalid_payload = {"email": "nouser@example.com"}

        os.environ["PASSWORD_RESET_LINK"] = "https://frontend.example.com/reset-password"
        global BACKEND_URL
        BACKEND_URL = "http://127.0.0.1:8000"
    

    @patch("auth_app.api.views.send_activation_email")
    def test_password_reset_with_valid_email(self, mock_send_email):
        """POST with valid email → 200 OK + email sent + correct links"""

        response = self.client.post(self.url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn("password_reset_backend", response.data)
        mock_send_email.assert_called_once()

        user = self.user
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        self.assertIn(uidb64, response.data["password_reset_backend"])
        self.assertIn(token, response.data["password_reset_backend"])

    def test_password_reset_with_nonexistent_email(self):
        """POST with non-existent email → 200 OK (for privacy reasons)"""

        response = self.client.post(self.url, self.invalid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_password_reset_without_email(self):
        """POST without email field → 400 BAD REQUEST"""

        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Email is required.")


class PasswordConfirmViewTests(APITestCase):
    """
    Test suite for /api/password_confirm/<uidb64>/<token>/ endpoint with JWT cookie authentication.
    """

    @classmethod
    def setUpTestData(cls):
        cls.base_url = "/api/password_confirm/"
        cls.user = User.objects.create_user(username="testuser@example.com", password="OldPassword123", email="testuser@example.com")

        cls.token_generator = PasswordResetTokenGenerator()
        cls.valid_token = cls.token_generator.make_token(cls.user)
        cls.uidb64 = urlsafe_base64_encode(force_bytes(cls.user.pk))


    def test_password_confirm_with_valid_data(self):
        """POST valid token + matching passwords → 200 OK and password changed"""

        url = f"{self.base_url}{self.uidb64}/{self.valid_token}/"
        payload = {"new_password": "NewStrongPassword123", "confirm_password": "NewStrongPassword123"}

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Your Password has been successfully reset.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPassword123"))

    def test_password_confirm_with_invalid_token(self):
        """POST with invalid token → 400"""

        url = f"{self.base_url}{self.uidb64}/invalid-token/"
        payload = {"new_password": "Something123", "confirm_password": "Something123"}

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_password_confirm_with_invalid_uid(self):
        """POST with invalid UID → 400"""

        url = f"{self.base_url}invaliduid/{self.valid_token}/"
        payload = {"new_password": "Something123", "confirm_password": "Something123"}

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_password_confirm_with_mismatched_passwords(self):
        """POST with non-matching passwords → 400"""

        url = f"{self.base_url}{self.uidb64}/{self.valid_token}/"
        payload = {"new_password": "Pass1234", "confirm_password": "Pass5678"}

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_password_confirm_with_missing_fields(self):
        """POST missing new_password or confirm_password → 400"""

        url = f"{self.base_url}{self.uidb64}/{self.valid_token}/"
        payload = {"new_password": "Pass1234"}

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
