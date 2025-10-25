from django.contrib import admin
from django.urls import path

from auth_app.api.views import RegisterView, ActivateAccountView


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
]
