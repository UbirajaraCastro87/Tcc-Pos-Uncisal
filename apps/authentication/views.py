import random
from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import logout


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

                print("✅ 2FA APROVADO COM SUCESSO! Redirecionando para o painel...")
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
