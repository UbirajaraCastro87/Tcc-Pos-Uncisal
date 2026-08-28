import random
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserAccessLog
from django.utils import timezone

# ==========================================
# 1. CLASSE DE LOGIN (Com Envio Real de E-mail 2FA)
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
            request.session['pre_2fa_user_id'] = user.id

            # Gera o código de 6 dígitos
            codigo_2fa = str(random.randint(100000, 999999))
            request.session['2fa_token'] = codigo_2fa

            # ENVIO REAL DE E-MAIL 2FA (Disparado pelo Django via SMTP)
            assunto = "Seu Código de Verificação 2FA"
            mensagem = f"Olá, {user.username}.\n\nSeu código de verificação de dois fatores é: {codigo_2fa}\n\nEste código expira em breve."
            remetente = 'noreply@tccseguranca.com'
            destinatario = [user.email]

            try:
                send_mail(assunto, mensagem, remetente, destinatario, fail_silently=False)
                print(f"📧 E-mail de 2FA disparado com sucesso para: {user.email}")
            except Exception as e:
                print(f"❌ Erro ao enviar e-mail: {e}")

            return redirect('auth-2fa-validacao')
        else:
            messages.error(request, "Credenciais inválidas. Verifique seu e-mail e senha.")
            return redirect(request.path)


# ==========================================
# 2. CLASSE DE VALIDAÇÃO 2FA & REGISTRO DE LOG
# ==========================================
class Auth2FAView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_blank.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        codigo_digitado = request.POST.get('codigo_2fa')

        codigo_salvo = request.session.get('2fa_token')
        user_id = request.session.get('pre_2fa_user_id')

        if not user_id or not codigo_salvo:
            messages.error(request, "Sessão expirada ou inválida. Faça login novamente.")
            return redirect('auth-login-basic')

        # Compara como string para evitar erros de tipo
        if str(codigo_digitado) == str(codigo_salvo):
            try:
                user = User.objects.get(id=user_id)

                # Efetiva o login oficial do Django
                login(request, user)

                # FORÇA A GRAVAÇÃO DA SESSÃO NO NAVEGADOR
                request.session.save()

                # Limpa os dados temporários de 2FA
                del request.session['2fa_token']
                del request.session['pre_2fa_user_id']

                print("✅ 2FA APROVADO COM SUCESSO! Redirecionando para o painel...")

                # CRIA O LOG DE AUDITORIA DE ACESSO NO BANCO DE DADOS
                log_acesso = UserAccessLog.objects.create(
                    user=user,
                    username=user.username,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                request.session['access_log_id'] = log_acesso.id

                return redirect('index')

            except User.DoesNotExist:
                messages.error(request, "Erro crítico. Usuário não encontrado.")
                return redirect('auth-login-basic')
        else:
            messages.error(request, "Código 2FA incorreto. Tente novamente.")
            return redirect(request.path)


# ==========================================
# 3. CLASSE DE LOGOUT (Calcula o tempo ativo)
# ==========================================
class AuthLogoutView(TemplateView):
    def get(self, request, *args, **kwargs):
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

        # 2. Limpa resíduos de sessão
        if '2fa_token' in request.session:
            del request.session['2fa_token']
        if 'pre_2fa_user_id' in request.session:
            del request.session['pre_2fa_user_id']
        if 'access_log_id' in request.session:
            del request.session['access_log_id']

        messages.success(request, "Você saiu do sistema com segurança.")
        print("🔒 LOGOUT REALIZADO: Sessão encerrada com sucesso.")

        return redirect('auth-login-basic')


# ==========================================
# 4. CLASSE DE DISPARO DE EMAIL RECUPERAÇÃO DE SENHA
# ==========================================
class AuthForgotPasswordView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_blank.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        email_digitado = request.POST.get('email')

        try:
            user = User.objects.get(email=email_digitado)

            # Gera um token de recuperação de 6 dígitos
            token_recuperacao = str(random.randint(100000, 999999))
            request.session['reset_token'] = token_recuperacao
            request.session['reset_user_id'] = user.id

            # Dispara o e-mail real de recuperação via SMTP
            assunto = "Recuperação de Senha - Sistema TCC"
            mensagem = (
                f"Olá,\n\n"
                f"Recebemos uma solicitação para redefinir a senha da sua conta.\n\n"
                f"👤 Seu login de acesso é: {user.username}\n"
                f"🔑 Seu código de recuperação é: {token_recuperacao}\n\n"
                f"Utilize este código na tela de redefinição para criar uma nova senha.\n\n"
                f"Se não foi você quem solicitou, por favor, ignore este e-mail."
            )

            send_mail(assunto, mensagem, 'noreply@tccseguranca.com', [user.email], fail_silently=False)
            print(f"📧 E-mail de recuperação enviado para: {user.email}")

            messages.success(request, "As instruções de recuperação foram enviadas para o seu e-mail.")
            return redirect('auth-reset-password')

        except User.DoesNotExist:
            # Segurança contra User Enumeration
            messages.success(request, "As instruções de recuperação foram enviadas para o seu e-mail.")
            return redirect('auth-reset-password')


# ==========================================
# 5. CLASSE DE REDEFINIÇÃO DE SENHA
# ==========================================
class AuthResetPasswordView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_blank.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        codigo_digitado = request.POST.get('codigo_reset')
        nova_senha = request.POST.get('password')

        token_salvo = request.session.get('reset_token')
        user_id = request.session.get('reset_user_id')

        if not user_id or not token_salvo:
            messages.error(request, "Sessão de recuperação expirada. Solicite novamente.")
            return redirect('auth-forgot-password-basic')

        if str(codigo_digitado).strip() == str(token_salvo).strip():
            try:
                user = User.objects.get(id=user_id)

                # Salva a senha com hash seguro do Django
                user.set_password(nova_senha)
                user.save()

                print(f"✅ SUCESSO: Senha alterada com segurança para o usuário {user.username}")

                del request.session['reset_token']
                del request.session['reset_user_id']

                messages.success(request, "Senha alterada com sucesso! Faça login com sua nova senha.")
                return redirect('auth-login-basic')

            except User.DoesNotExist:
                messages.error(request, "Erro ao encontrar o usuário.")
                return redirect('auth-forgot-password-basic')
        else:
            messages.error(request, "Código de recuperação incorreto. Verifique os números.")
            return redirect(request.path)


# ==========================================
# 6. CLASSE DE CADASTRO DE USUÁRIO (Restrita a Internos / Administradores)
# ==========================================
class AuthAddUserView(LoginRequiredMixin, TemplateView):
    login_url = '/auth/login/'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        # Mantém o layout vertical padrão do painel interno com o menu lateral
        context.update({"layout_path": TemplateHelper.set_layout("layout_vertical.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        email = request.POST.get('email')
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

        if User.objects.filter(email=email).exists():
            messages.error(request, "Este e-mail já está cadastrado.")
            return redirect(request.path)

        try:
            # Cria o usuário utilizando o método seguro do Django (hash automático)
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, f"Usuário '{username}' cadastrado com sucesso!")
            print(f"✅ SUCESSO: Novo usuário criado internamente -> {username} ({email})")

            # Redireciona de volta para o dashboard ou para a própria tela de cadastro limpa
            return redirect('auth-add-user')
        except Exception as e:
            messages.error(request, f"Erro ao criar usuário: {e}")
            return redirect(request.path)


from .models import UserAccessLog


# ==========================================
# 7. CLASSE DE VISUALIZAÇÃO DE LOGS DE ACESSO
# ==========================================
class UserLogsView(LoginRequiredMixin, TemplateView):
    login_url = '/auth/login/'
    template_name = "user_logs.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_vertical.html", context)})

        # Busca todos os logs cadastrados no banco, ordenados do mais recente para o mais antigo
        context['logs'] = UserAccessLog.objects.all().order_by('-login_time')
        return context
