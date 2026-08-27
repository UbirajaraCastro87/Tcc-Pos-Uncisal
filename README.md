

## 1. Arquivo `README.md` (Para a raiz do projeto)

```markdown
# Sistema de Autenticação Segura com MFA (TCC)

Este repositório contém o desenvolvimento do sistema web desenvolvido para Trabalho de Conclusão de Curso (TCC), focado em arquitetura de segurança de aplicações web com múltiplos fatores de autenticação (MFA/2FA).

## 🚀 Tecnologias Utilizadas
* **Backend:** Python / Django (Framework Web)
* **Frontend:** Template Bootstrap Materio (Material Design)
* **Banco de Dados:** SQLite (Desenvolvimento Local) / PostgreSQL (Preparado)
* **Segurança:** Hashing de senhas nativo do Django, Tokens Dinâmicos baseados em Sessão Segura e Proteção CSRF.

## 🛡️ Funcionalidades Implementadas
1. **Autenticação Baseada em Credenciais:** Validação segura de hash de senha (`authenticate()`).
2. **Autenticação em Duas Etapas (2FA):** 
   - Geração de token aleatório numérico de 6 dígitos.
   - Envio simulado de segurança via terminal (pronto para integração SMTP).
   - Isolamento estrito de sessão pré-2FA para evitar ataques de bypass.
3. **Gerenciamento de Sessão e Logoff:** 
   - Persistência segura de sessão (`request.session.save()`).
   - Destruição limpa de tokens e encerramento de sessão via `logout()`.
4. **Contexto de Perfil Dinâmico:** Integração de dados do usuário autenticado diretamente na interface do painel administrativo.

## ⚙️ Como Executar o Projeto Localmente

1. Clone o repositório e acesse a pasta do projeto:
   ```bash
   cd tcc

```

2. Ative o ambiente virtual (`venv`):
```bash
venv\Scripts\activate  # No Windows

```


3. Instale as dependências:
```bash
pip install -r requirements.txt

```


4. Execute as migrações do banco de dados:
```bash
python manage.py makemigrations
python manage.py migrate

```


5. Inicie o servidor de desenvolvimento:
```bash
python manage.py runserver

```


6. Acesse no navegador: `http://127.0.0.1:8000/auth/login/`

```

---

## 2. Documentação Técnica do Módulo (Para o documento do TCC)

### Capítulo: Implementação do Mecanismo de Autenticação Multifator (MFA/2FA)

#### 1. Introdução e Objetivo
O módulo de autenticação foi projetado sob o princípio de **Defesa em Profundidade (*Defense in Depth*)**, visando mitigar vulnerabilidades comuns associadas a credenciais vazadas, como ataques de força bruta e roubo de senhas em texto plano. O sistema exige que o usuário valide sua identidade em duas barreiras distintas antes de ter acesso aos recursos protegidos do painel administrativo.

#### 2. Arquitetura do Fluxo de Autenticação

O fluxo foi dividido em duas etapas sequenciais e isoladas no backend (`views.py`):

* **Etapa 1: Validação de Credenciais Primárias (`AuthView`)**
  * O usuário submete suas credenciais (e-mail/username e senha) via método HTTP `POST`.
  * O Django executa a função de hash e comparação segura comparando a entrada com o banco de dados através do método `authenticate()`.
  * Em caso de sucesso, o sistema **não** autentica o usuário imediatamente na sessão principal. Em vez disso, gera-se um token numérico aleatório de 6 dígitos utilizando o módulo criptográfico/estatístico do Python (`random.randint`), armazena-se o ID do usuário de forma temporária na sessão (`pre_2fa_user_id`) e o token de validação (`2fa_token`), disparando o envio simulado via console para fins de auditoria de desenvolvimento.
  * O usuário é redirecionado para a rota restrita de segunda etapa (`/auth/2fa/`).

* **Etapa 2: Validação do Segundo Fator (`Auth2FAView`)**
  * O usuário insere o código de 6 dígitos recebido.
  * O sistema valida se o token inserido coincide estritamente com o token salvo na sessão e assegura que a sessão pré-2FA é válida.
  * Sendo o código correto, a função `login(request, user)` é acionada, seguida pelo comando de persistência forçada (`request.session.save()`) para garantir que o cookie de sessão seja gravado corretamente pelo navegador.
  * Por fim, os dados temporários de 2FA são destruídos da sessão (`del`) e o usuário é redirecionado ao Dashboard principal (`index`).

#### 3. Controle de Sessão e Logoff Seguro
Para garantir que o ciclo de vida da sessão seja encerrado de forma íntegra, implementou-se a classe `AuthLogoutView`, que executa:
1. Revogação do estado de autenticação via `logout(request)`.
2. Limpeza manual de quaisquer variáveis residuais de tokens na sessão.
3. Redirecionamento forçado para a tela de login, invalidando o acesso por histórico de navegação do navegador.

---

Guarde esses textos para o seu documento de TCC! Quando quiser retomar do ponto em que paramos (seja para configurar banco PostgreSQL, e-mails reais via SMTP ou novas telas), é só me chamar. Bom descanso por hoje!

```
