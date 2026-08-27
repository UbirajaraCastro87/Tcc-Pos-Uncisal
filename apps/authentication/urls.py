from django.urls import path
from .views import AuthView,Auth2FAView,AuthLogoutView


urlpatterns = [
    path(
        "auth/login/",
        AuthView.as_view(template_name="auth_login_basic.html"),
        name="auth-login-basic",
    ),
# --- NOVA ROTA DE 2FA AQUI ---
    path(
        "auth/2fa/",
        Auth2FAView.as_view(template_name="auth_two_steps_basic.html"),
        name="auth-2fa-validacao",
    ),
    path("auth/logout/",AuthLogoutView.as_view(),name="auth-logout",

        ),
    path(
        "auth/register/",
        AuthView.as_view(template_name="auth_register_basic.html"),
        name="auth-register-basic",
    ),
    path(
        "auth/forgot_password/",
        AuthView.as_view(template_name="auth_forgot_password_basic.html"),
        name="auth-forgot-password-basic",
    ),
]
