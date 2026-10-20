# Sistema de Autenticação — TCC

Aplicação web desenvolvida para a disciplina **Projeto Aplicado: Práticas de
Mercado**, da Pós-Graduação em Segurança da Informação e Análise Forense da
UNCISAL. O projeto demonstra autenticação, controle de acesso, auditoria de
sessões e implantação automatizada.

## Aplicação

- **Produção:** [https://ubirajarauncisal.duckdns.org](https://ubirajarauncisal.duckdns.org)
- **Tecnologias:** Python, Django, SQLite, Bootstrap Materio, Gunicorn e Nginx
- **Infraestrutura informada:** AWS EC2 com Ubuntu Server
- **Repositório:** [UbirajaraCastro87/Tcc-Pos-Uncisal](https://github.com/UbirajaraCastro87/Tcc-Pos-Uncisal)

Cada ambiente usa seu próprio banco SQLite. O banco local, arquivos `.env` e
chaves privadas não devem ser adicionados ao Git.

## Funcionalidades

- Login com usuário e senha.
- Página interna e histórico de acesso protegidos por autenticação.
- Usuários comuns consultam apenas os próprios logs; contas `staff` podem
  consultar todos os registros.
- Criação de usuários restrita a contas autenticadas com permissão `staff`.
- Logout por POST com proteção CSRF.
- Recuperação de senha por e-mail com código de seis dígitos, validade de
  15 minutos e limite de cinco tentativas.
- Senhas criadas ou redefinidas passam pelos validadores do Django e são
  armazenadas pelo mecanismo de hash do framework.

**A autenticação de dois fatores está desativada.** O login atualmente usa
apenas usuário e senha; portanto, o sistema não deve ser apresentado como MFA
ou 2FA.

## Controles relacionados ao OWASP Top 10:2025

Esta seção descreve controles presentes no código. Ela não substitui uma
auditoria de segurança nem comprova a configuração da infraestrutura.

### A01 — Broken Access Control

- O painel, o cadastro e os logs exigem autenticação.
- Apenas contas `staff` podem cadastrar usuários.
- Os logs mostrados a uma conta comum são filtrados pelo usuário autenticado.
- O logout altera o estado por POST e usa o middleware CSRF do Django.

**Código:** `apps/dashboards/views.py`,
`apps/authentication/views.py` e os templates de navegação.

### A04 — Cryptographic Failures

- As senhas são armazenadas com o hash de senhas do Django.
- Com `DEBUG=False`, cookies de sessão e CSRF usam o atributo `Secure`;
  o cookie de sessão também usa `HttpOnly` e `SameSite=Lax`.
- A aplicação habilita redirecionamento HTTPS e HSTS por padrão em produção.
- Gunicorn está configurado para escutar em `127.0.0.1:5005`; o proxy Nginx
  deve encaminhar corretamente o cabeçalho `X-Forwarded-Proto`.

**Código:** `config/settings.py` e `gunicorn-cfg.py`. Certificado, Nginx,
redirecionamento HTTP, renovação TLS e resultados de testes PQC precisam ser
verificados no servidor.

### A07 — Authentication Failures

- O login usa `authenticate()` e `login()` do Django.
- A recuperação de senha usa código gerado com `secrets`, expira após
  15 minutos e é invalidada após cinco tentativas incorretas.
- As solicitações de recuperação recebem uma resposta genérica, sem informar
  se o e-mail existe.
- A criação e a redefinição de senha aplicam os validadores do Django.
- O logout encerra a sessão do usuário.

**Código:** `apps/authentication/views.py` e `config/settings.py`.
O login não tem segundo fator nem limitação específica de tentativas; esses
riscos residuais devem ser considerados na avaliação.

## Configuração local

Requer Python compatível com Django 5.2. As dependências estão listadas em
`requirements.txt`.

### Windows PowerShell

```powershell
git clone https://github.com/UbirajaraCastro87/Tcc-Pos-Uncisal.git
Set-Location Tcc-Pos-Uncisal
py -m venv venv
.\venv\Scripts\Activate.ps1
Copy-Item .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Linux ou macOS

```bash
git clone https://github.com/UbirajaraCastro87/Tcc-Pos-Uncisal.git
cd Tcc-Pos-Uncisal
python3 -m venv venv
source venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/auth/login/`. O arquivo `.env.example` serve de
modelo e pode ser copiado para `.env`; não coloque valores secretos nele.
Em desenvolvimento, `DEBUG=True` permite usar o backend de e-mail de console
quando não há credenciais SMTP configuradas.

Em produção, configure no `.env` do servidor uma `SECRET_KEY` forte e
persistente, `DEBUG=False`, `ALLOWED_HOSTS`, credenciais SMTP
(`EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD`) e, se necessário,
`CSRF_TRUSTED_ORIGINS`. Sem chave secreta ou credenciais SMTP em modo de
produção, a aplicação interrompe a inicialização. Nunca publique `.env`,
senhas ou chaves privadas.

## Testes e verificações Django

```bash
python manage.py test apps.authentication.tests
python manage.py check
python manage.py check --deploy
```

`check --deploy` deve ser executado com as variáveis de produção configuradas.
Revise cada aviso considerando o proxy reverso e a configuração real do
servidor. HSTS para subdomínios e preload não são habilitados automaticamente;
ative-os somente após confirmar os requisitos para todos os subdomínios.

## Deploy com GitHub Actions

O workflow `.github/workflows/deploy.yml` é acionado por push para `master`.
Ele conecta à EC2 por SSH, atualiza o código, garante uma `SECRET_KEY` e
`DEBUG=False` no `.env`, instala dependências, aplica migrations, coleta
arquivos estáticos e reinicia Gunicorn e Nginx.

Configure os segredos `EC2_HOST`, `EC2_USER` e `EC2_SSH_KEY` em **Settings →
Secrets and variables → Actions**. Configure também as credenciais SMTP no
`.env` existente no servidor; o workflow não copia o `.env` local.
A chave SSH privada deve ser mantida em segredo e nunca commitada ou enviada
em mensagens.

O roteiro da disciplina menciona a branch `main`; este repositório configura o
deploy pela branch `master`. Confirme com o professor se essa diferença é
aceita.

## Evidências e itens de infraestrutura

Em uma verificação no servidor registrada em **20/10/2026**, foram observados
Ubuntu Server 26.04.1 LTS, serviços Nginx e Gunicorn ativos, jail `sshd` do
Fail2Ban ativo e resposta HTTPS do domínio. O Gunicorn estava escutando em
`127.0.0.1:8000`, endereço configurado pelo serviço systemd; a configuração
`gunicorn-cfg.py` do repositório usa `127.0.0.1:5005`, portanto os dois
valores precisam ser reconciliados antes de afirmar que a configuração do
arquivo é a usada em produção.

A captura abaixo e a saída de comandos coletadas no servidor são evidências
pontuais, não uma auditoria completa:

![Evidência de verificação do ambiente](https://github.com/user-attachments/assets/780caf36-85c0-41aa-89b8-e73582fd01b0)

Itens que ainda precisam de comprovação específica:

- [ x] Regras do firewall/Security Group: somente portas necessárias abertas.
- [ x] SSH por chave, autenticação SSH por senha desabilitada e configuração
  Fail2Ban com quatro tentativas e banimento de 24 horas.
- [ x] Redirecionamento automático de HTTP para HTTPS e renovação automática
  do certificado.
- [x ] Resultado exigido pelo professor nos verificadores TLS e PQC.
- [ x] Compatibilidade da branch `master` com a exigência de deploy pela `main`.
- [x ] Evidência do uso de Antigravity ou de ambiente de desenvolvimento com IA
  equivalente, conforme o roteiro da disciplina.
- [x ] Confirmação de que nenhum `.env`, segredo, chave privada ou banco local
  está versionado.

Não publique logs brutos de terminal que revelem endereços, nomes de usuários,
estado de segurança ou detalhes operacionais do servidor. Guarde as evidências
completas para apresentação privada ao professor.

## Autor

**Ubirajara Rodrigo Castro** — Pós-Graduação em Segurança da Informação e
Análise Forense, UNCISAL.
