import os
from contextlib import suppress

from django.contrib.auth import get_user_model, authenticate
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenRefreshView

from auth_app.utils import send_activation_email
from .serializers import RegistrationSerializer
from .token_generators import AccountActivationTokenGenerator, PasswordResetTokenGenerator


User = get_user_model()
USER_NAME = "new user of Videoflix, the video streaming platform"
SECURE = False
SAME_SITE = "Lax"
LOGOUT_RESPONSE_TEXT = "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
PASSWORD_RESET_200_RESPONSE_TEXT = "If an account with this email exists, a password reset link has been sent."
BACKEND_URL = "http://127.0.0.1:8000"


class RegisterView(APIView):
    """
    POST /api/register/
    Registers a new user in the system. After successful registration, an activation email will be sent.
    """
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
    
        if serializer.is_valid():
            user = serializer.save()

            link, link_backend = self._create_activation_link(user)
            send_activation_email(user_email=user.email, user_name=USER_NAME, activation_link=link, email_type="ACTIVATION_EMAIL")

            return Response({"user": {"id": user.id, "email": user.email}, "activation_backend": link_backend}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_activation_link(self, user):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token_generator = AccountActivationTokenGenerator()
        token = token_generator.make_token(user)

        base_url = os.getenv("ACTIVATE_ACCOUNT_LINK")
        activation_link = f"{base_url}?uid={uidb64}&token={token}"
        link_backend = f"{BACKEND_URL}/api/activate/{uidb64}/{token}/"

        return activation_link, link_backend


class ActivateAccountView(APIView):
    """
    GET /api/activate/<uidb64>/<token>/
    Activates the user account using the token sent via email.
    """

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except:
            return Response({"error": "Activation failed."}, status=status.HTTP_400_BAD_REQUEST)
        
        return self._activation_process(user, token)

    def _activation_process(self, user, token):
        if user.is_active:
            return Response({"message": "Account is already active."}, status=status.HTTP_200_OK)
        
        token_generator = AccountActivationTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({"error": "Activation failed."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()

        return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    POST /api/login/
    The account must be activated before the first login. Logs in the user and sets auth cookies. 
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials or inactive user account."}, status=status.HTTP_401_UNAUTHORIZED)

        return self._finalize_login(user)
    
    def _finalize_login(self, user):
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        response = Response({"detail": "Login successfully!", "user": {"id": user.id, "email": user.email}})

        response.set_cookie("access_token", str(access), httponly=True, secure=SECURE, samesite=SAME_SITE)
        response.set_cookie("refresh_token", str(refresh), httponly=True, secure=SECURE, samesite=SAME_SITE)
        return response


class LogoutView(APIView):
    """
    POST /api/logout/
    Logs out the user, deletes all auth cookies and invalidates the refresh token.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_400_BAD_REQUEST)
        
        with suppress(TokenError):
            RefreshToken(refresh_token).blacklist()

        response = Response({"detail": LOGOUT_RESPONSE_TEXT})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class TokenRefreshView(TokenRefreshView):
    """
    POST /api/token/refresh/
    Renews the access token using the refresh token.
    """
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({"detail": "Refresh token invalid!"}, status=status.HTTP_401_UNAUTHORIZED)

        return self._create_response(serializer)

    def _create_response(self, serializer):
        access_token = serializer.validated_data.get("access")

        response = Response({"detail": "Token refreshed", "access": "new token created"})
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=SECURE, samesite=SAME_SITE)

        return response


class PasswordResetView(APIView):
    """
    POST /api/password_reset/
    Sends a password reset link to the user's email.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": PASSWORD_RESET_200_RESPONSE_TEXT}, status=status.HTTP_200_OK)
        
        return self._finalize_password_reset(user)

    def _finalize_password_reset(self, user):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        base_url = os.getenv("PASSWORD_RESET_LINK")
        password_reset_link = f"{base_url}?uid={uidb64}&token={token}"
        link_backend = f"{BACKEND_URL}/api/password_confirm/{uidb64}/{token}/"

        send_activation_email(user_email=user.email, user_name="", activation_link=password_reset_link, email_type="RESET_PASSWORD_EMAIL")

        return Response({"detail": PASSWORD_RESET_200_RESPONSE_TEXT, "password_reset_backend": link_backend}, status=status.HTTP_200_OK)


class PasswordConfirmView(APIView):
    """
    POST /api/password_confirm/<uidb64>/<token>/
    Confirm the password change with the token included in the email.
    """

    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Password confirm failed."}, status=status.HTTP_400_BAD_REQUEST)
        
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({"error": "Password confirm failed."}, status=status.HTTP_400_BAD_REQUEST)
        
        return self._save_new_password(request, user)
    
    def _save_new_password(self, request, user):
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not new_password or not confirm_password or new_password != confirm_password:
            return Response({"error": "Password confirm failed."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Your Password has been successfully reset."})
