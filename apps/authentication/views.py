import secrets

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, password_validation
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

from .models import UserAccessLog

RESET_CODE_TTL_SECONDS = 15 * 60
RESET_CODE_MAX_ATTEMPTS = 5
RESET_SESSION_KEYS = (
    "reset_token",
    "reset_user_id",
    "reset_expires_at",
    "reset_attempts",
)


def clear_password_reset_session(request):
    for key in RESET_SESSION_KEYS:
        request.session.pop(key, None)


# ==========================================
# 1. CLASSE DE LOGIN
# ==========================================
class AuthView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_blank.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        usuario = request.POST.get('username')
        senha = request.POST.get('password')

        user = authenticate(request, username=usuario, password=senha)

        if user is not None:
            login(request, user)

            log_acesso = UserAccessLog.objects.create(
                user=user,
                username=user.username,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            request.session['access_log_id'] = log_acesso.id

            return redirect('user-logs')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
            return redirect(request.path)


# ==========================================
# 2. CLASSE DE LOGOUT (Calcula o tempo ativo)
# ==========================================
class AuthLogoutView(TemplateView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Calcula o tempo ativo se houver um log registrado na sessão
        log_id = request.session.get('access_log_id')
        if log_id:
            try:
                log_acesso = UserAccessLog.objects.get(id=log_id)
                log_acesso.logout_time = timezone.now()
                log_acesso.duration = log_acesso.logout_time - log_acesso.login_time
                log_acesso.save()
            except UserAccessLog.DoesNotExist:
                pass

        # 1. Encerra a sessão oficial do Django
        logout(request)

        messages.success(request, "Você saiu do sistema com segurança.")

        return redirect('auth-login-basic')


# ==========================================
# 3. CLASSE DE DISPARO DE EMAIL RECUPERAÇÃO DE SENHA
# ==========================================
class AuthForgotPasswordView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_blank.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        email_digitado = (request.POST.get('email') or "").strip()
        user = User.objects.filter(email__iexact=email_digitado).first()
        clear_password_reset_session(request)

        if user:
            token_recuperacao = f"{secrets.randbelow(1_000_000):06d}"
            request.session['reset_token'] = token_recuperacao
            request.session['reset_user_id'] = user.id
            request.session['reset_expires_at'] = int(
                timezone.now().timestamp() + RESET_CODE_TTL_SECONDS
            )
            request.session['reset_attempts'] = 0

            assunto = "Recuperação de Senha - Sistema TCC"
            mensagem = (
                f"Olá,\n\n"
                f"Recebemos uma solicitação para redefinir a senha da sua conta.\n\n"
                f"👤 Seu login de acesso é: {user.username}\n"
                f"🔑 Seu código de recuperação é: {token_recuperacao}\n\n"
                f"Utilize este código na tela de redefinição para criar uma nova senha.\n\n"
                f"Se não foi você quem solicitou, por favor, ignore este e-mail."
            )

            send_mail(
                assunto,
                mensagem,
                None,
                [user.email],
                fail_silently=False,
            )

        messages.success(
            request,
            "Se o e-mail estiver cadastrado, você receberá instruções de recuperação.",
        )
        return redirect('auth-reset-password')


# ==========================================
# 4. CLASSE DE REDEFINIÇÃO DE SENHA
# ==========================================
class AuthResetPasswordView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_blank.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        codigo_digitado = str(request.POST.get('codigo_reset') or "").strip()
        nova_senha = request.POST.get('password')

        token_salvo = request.session.get('reset_token')
        user_id = request.session.get('reset_user_id')
        expires_at = request.session.get('reset_expires_at')
        attempts = request.session.get('reset_attempts', 0)

        if not user_id or not token_salvo or not expires_at:
            clear_password_reset_session(request)
            messages.error(request, "Sessão de recuperação expirada. Solicite novamente.")
            return redirect('auth-forgot-password-basic')

        if timezone.now().timestamp() >= expires_at or attempts >= RESET_CODE_MAX_ATTEMPTS:
            clear_password_reset_session(request)
            messages.error(request, "Código expirado. Solicite uma nova recuperação de senha.")
            return redirect('auth-forgot-password-basic')

        if (
            len(codigo_digitado) != 6
            or not codigo_digitado.isascii()
            or not codigo_digitado.isdigit()
            or not secrets.compare_digest(codigo_digitado, str(token_salvo))
        ):
            attempts += 1
            if attempts >= RESET_CODE_MAX_ATTEMPTS:
                clear_password_reset_session(request)
                messages.error(request, "Limite de tentativas excedido. Solicite um novo código.")
                return redirect(request.path)
            request.session['reset_attempts'] = attempts
            messages.error(request, "Código de recuperação incorreto. Verifique os números.")
            return redirect(request.path)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            clear_password_reset_session(request)
            messages.error(request, "Não foi possível localizar a conta. Solicite nova recuperação.")
            return redirect('auth-forgot-password-basic')

        if not nova_senha:
            messages.error(request, "Informe uma nova senha.")
            return redirect(request.path)

        try:
            password_validation.validate_password(nova_senha, user=user)
        except ValidationError as error:
            for validation_error in error.messages:
                messages.error(request, validation_error)
            return redirect(request.path)

        user.set_password(nova_senha)
        user.save(update_fields=["password"])
        clear_password_reset_session(request)
        messages.success(request, "Senha alterada com sucesso! Faça login com sua nova senha.")
        return redirect('auth-login-basic')


# ==========================================
# 5. CLASSE DE CADASTRO DE USUÁRIO (Restrita a Internos / Administradores)
# ==========================================
class AuthAddUserView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    login_url = '/auth/login/'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        # Mantém o layout vertical padrão do painel interno com o menu lateral
        context.update({"layout_path": TemplateHelper.set_layout("layout_vertical.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        username = (request.POST.get('username') or "").strip()
        email = (request.POST.get('email') or "").strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not username or not email or not password:
            messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            return redirect(request.path)

        if password != confirm_password:
            messages.error(request, "As senhas não coincidem. Tente novamente.")
            return redirect(request.path)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Este nome de usuário já está em uso.")
            return redirect(request.path)

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Este e-mail já está cadastrado.")
            return redirect(request.path)

        try:
            password_validation.validate_password(
                password,
                user=User(username=username, email=email),
            )
        except ValidationError as error:
            for validation_error in error.messages:
                messages.error(request, validation_error)
            return redirect(request.path)

        try:
            # Cria o usuário utilizando o método seguro do Django (hash automático)
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, f"Usuário '{username}' cadastrado com sucesso!")

            # Redireciona de volta para o dashboard ou para a própria tela de cadastro limpa
            return redirect('auth-add-user')
        except IntegrityError:
            messages.error(request, "Não foi possível criar a conta. Verifique os dados informados.")
            return redirect(request.path)


# ==========================================
# 6. CLASSE DE VISUALIZAÇÃO DE LOGS DE ACESSO
# ==========================================
class UserLogsView(LoginRequiredMixin, TemplateView):
    login_url = '/auth/login/'
    template_name = "user_logs.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_vertical.html", context)})

        logs = UserAccessLog.objects.all()
        if not self.request.user.is_staff:
            logs = logs.filter(user=self.request.user)
        context['logs'] = logs.order_by('-login_time')
        return context
