from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from auth_app.api.views import RegisterView, ActivateAccountView, LoginView, LogoutView, TokenRefreshView \
    , PasswordResetView, PasswordConfirmView


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('api/password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path("api/password_confirm/<uidb64>/<token>/", PasswordConfirmView.as_view(), name="password_confirm"),

    path('api/video/', include('video_app.api.urls'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
