import random
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import messages


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
            request.session['pre_2fa_user_id'] = user.id

            codigo_2fa = str(random.randint(100000, 999999))
            request.session['2fa_token'] = codigo_2fa

            print("\n" + "=" * 50)
            print(f"📧 E-MAIL ENVIADO PARA: {user.email}")
            print(f"🔒 SEU CÓDIGO DE ATIVAÇÃO 2FA É: {codigo_2fa}")
            print("=" * 50 + "\n")

            return redirect('auth-2fa-validacao')
        else:
            messages.error(request, "Credenciais inválidas. Verifique seu e-mail e senha.")
            return redirect(request.path)


# ==========================================
# 2. CLASSE DE VALIDAÇÃO 2FA
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

                # FORÇA A GRAVAÇÃO DA SESSÃO NO NAVEGADOR (Correção do loop)
                request.session.save()

                # Limpa os dados temporários de 2FA
                del request.session['2fa_token']
                del request.session['pre_2fa_user_id']

                print(" 2FA APROVADO COM SUCESSO! Redirecionando para o painel...")
                return redirect('index')

            except User.DoesNotExist:
                messages.error(request, "Erro crítico. Usuário não encontrado.")
                return redirect('auth-login-basic')
        else:
            messages.error(request, "Código 2FA incorreto. Tente novamente.")
            return redirect(request.path)

# ==========================================
# 3. CLASSE DE LOGOUT
# ==========================================

class AuthLogoutView(TemplateView):
    def get(self, request, *args, **kwargs):
        # 1. Encerra a sessão oficial do Django
        logout(request)

        # 2. Limpa qualquer resíduo de sessão personalizada que tenhamos criado
        if '2fa_token' in request.session:
            del request.session['2fa_token']
        if 'pre_2fa_user_id' in request.session:
            del request.session['pre_2fa_user_id']

        # 3. Dispara uma mensagem informativa de sucesso
        messages.success(request, "Você saiu do sistema com segurança.")

        print("🔒 LOGOUT REALIZADO: Sessão encerrada com sucesso.")

        # 4. Redireciona estritamente de volta para a tela de login
        return redirect('auth-login-basic')
# ==========================================
# 4. CLASSE DE DISPARO DE EMAIL 2FA
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

            # ENVIO REAL DE E-MAIL (Disparado pelo Django)
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
# 5. CLASSE DE DISPARO DE EMAIL RECUPERAÇÃO DE SENHA
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
            mensagem = f"Olá,\n\nRecebemos uma solicitação para redefinir sua senha.\nSeu código de recuperação é: {token_recuperacao}\n\nSe não foi você, ignore este e-mail."

            send_mail(assunto, mensagem, None, [user.email], fail_silently=False)
            print(f"📧 E-mail de recuperação enviado para: {user.email}")

            messages.success(request, "As instruções de recuperação foram enviadas para o seu e-mail.")

            # 👇 CORREÇÃO: Redireciona para a tela onde ele insere o código e a nova senha
            return redirect('auth-reset-password')

        except User.DoesNotExist:
            # Segurança contra User Enumeration (exibe a mesma mensagem mas não quebra)
            messages.success(request, "As instruções de recuperação foram enviadas para o seu e-mail.")
            return redirect('auth-reset-password')
# ==========================================
# 6. CLASSE DE REDEFINIÇÃO DE SENHA
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

        print(f"🔍 DEBUG RESET - Código digitado: {codigo_digitado} | Token salvo na sessão: {token_salvo}")
        print(f"🔍 DEBUG RESET - User ID na sessão: {user_id}")

        if not user_id or not token_salvo:
            messages.error(request, "Sessão de recuperação expirada. Solicite novamente.")
            return redirect('auth-forgot-password-basic')

        if str(codigo_digitado).strip() == str(token_salvo).strip():
            try:
                user = User.objects.get(id=user_id)

                # O Django exige que a senha seja salva usando hash seguro (set_password)
                user.set_password(nova_senha)
                user.save()

                print(f"✅ SUCESSO: Senha alterada com segurança para o usuário {user.username}")

                # Limpa os dados temporários da sessão por segurança
                del request.session['reset_token']
                del request.session['reset_user_id']

                messages.success(request, "Senha alterada com sucesso! Faça login com sua nova senha.")
                return redirect('auth-login-basic')

            except User.DoesNotExist:
                messages.error(request, "Erro ao encontrar o usuário.")
                return redirect('auth-forgot-password-basic')
        else:
            print("❌ ERRO: O código de recuperação digitado não confere com o da sessão.")
            messages.error(request, "Código de recuperação incorreto. Verifique os números.")
            return redirect(request.path)





class AuthAddUserView(LoginRequiredMixin, TemplateView):
    login_url = '/auth/login/'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"layout_path": TemplateHelper.set_layout("layout_vertical.html", context)})
        return context

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validação básica
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
            # Cria o usuário utilizando o método seguro do Django (gera hash de senha automático)
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, f"Usuário '{username}' cadastrado com sucesso!")
            print(f"✅ SUCESSO: Novo usuário criado -> {username} ({email})")

            # Redireciona para o painel ou para a lista de usuários
            return redirect('index')
        except Exception as e:
            messages.error(request, f"Erro ao criar usuário: {e}")
            return redirect(request.path)
