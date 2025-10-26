from django.contrib import admin
from django.urls import path

from auth_app.api.views import RegisterView, ActivateAccountView, LoginView, LogoutView, TokenRefreshView, PasswordResetView


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('api/password_reset/', PasswordResetView.as_view(), name='password-reset'),
]
