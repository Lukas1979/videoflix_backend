from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.utils import send_activation_email
from .serializers import RegistrationSerializer


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
            send_activation_email(user_email=user.email, user_name="new user of Videoflix, the video streaming platform")

            return Response({"user": {"id": user.id, "email": user.email}}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
