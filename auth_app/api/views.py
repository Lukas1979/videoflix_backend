import os

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.utils import send_activation_email
from .serializers import RegistrationSerializer


User = get_user_model()
USER_NAME = "new user of Videoflix, the video streaming platform"


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

            link, activation_token = self._create_activation_link(user)
            send_activation_email(user_email=user.email, user_name=USER_NAME, activation_link=link)

            return Response({"user": {"id": user.id, "email": user.email}, "token": activation_token}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_activation_link(self, user):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        base_url = os.getenv("ACTIVATE_ACCOUNT_LINK")
        activation_link = f"{base_url}?uid={uidb64}&token={token}"

        return activation_link, token


class ActivateAccountView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except:
            return Response({"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Prüfe Token
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        # Falls schon aktiviert
        if user.is_active:
            return Response({"message": "Account is already active."}, status=status.HTTP_200_OK)

        # ✅ User aktivieren
        user.is_active = True
        user.save()

        return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)
