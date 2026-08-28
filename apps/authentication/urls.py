from django.urls import path
from .views import AuthView, Auth2FAView, AuthLogoutView, AuthForgotPasswordView, AuthResetPasswordView,AuthAddUserView

urlpatterns = [
    path("auth/login/", AuthView.as_view(template_name="auth_login_basic.html"), name="auth-login-basic"),
    path("auth/2fa/", Auth2FAView.as_view(template_name="auth_two_steps_basic.html"), name="auth-2fa-validacao"),
    path("auth/logout/", AuthLogoutView.as_view(), name="auth-logout"),
    path("auth/register/", AuthView.as_view(template_name="auth_register_basic.html"), name="auth-register-basic"),

    # Rota 1: Abre a tela que PEDE O E-MAIL
    path(
        "auth/forgot_password/",
        AuthForgotPasswordView.as_view(template_name="auth_forgot_password_basic.html"),
        name="auth-forgot-password-basic",
    ),

    # Rota 2: Abre a tela que PEDE O CÓDIGO E A NOVA SENHA
    path(
        "auth/reset_password/",
        AuthResetPasswordView.as_view(template_name="auth_reset_password_basic.html"),
        name="auth-reset-password",
    ),
# Rota para Adicionar Novo Usuário
    path(
        "auth/add_user/",
        AuthAddUserView.as_view(template_name="auth_add_user.html"),
        name="auth-add-user",
    ),
]
