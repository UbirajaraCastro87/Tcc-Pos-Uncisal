# Sistema de Autenticação — TCC

Aplicação web acadêmica desenvolvida para a disciplina **Projeto Aplicado:
Práticas de Mercado**, da Pós-Graduação em Segurança da Informação e Análise
Forense da UNCISAL. O projeto demonstra autenticação, autorização, auditoria
de sessões e implantação automatizada.

## Aplicação

- **Produção:** [https://ubirajarauncisal.duckdns.org](https://ubirajarauncisal.duckdns.org)
- **Tecnologias:** Python, Django, SQLite, Bootstrap Materio, Gunicorn e Nginx
- **Infraestrutura:** AWS EC2 com Ubuntu Server
- **Código-fonte:** [UbirajaraCastro87/Tcc-Pos-Uncisal](https://github.com/UbirajaraCastro87/Tcc-Pos-Uncisal)

O banco SQLite local, arquivos `.env` e chaves privadas não são versionados.
Desenvolvimento e produção mantêm seus próprios bancos e usuários.

## Funcionalidades

- Login com usuário e senha.
- Dashboard e histórico de acessos protegidos por autenticação.
- Usuários comuns visualizam apenas seus próprios logs; contas `staff` podem
  consultar todos os registros.
- Criação de usuários restrita a contas autenticadas com permissão `staff`.
- Logout via POST com proteção CSRF.
- Recuperação de senha por e-mail com código aleatório de seis dígitos,
  validade de 15 minutos e limite de cinco tentativas.
- Senhas criadas e redefinidas validadas pelo Django e armazenadas usando o
  hash de senhas do framework.

> **Autenticação de dois fatores está desativada.** O login usa somente
> usuário e senha; não descreva o sistema como MFA/2FA.

## Controles relacionados ao OWASP Top 10:2025

Os controles abaixo são implementados no código. Esta descrição não substitui
auditoria independente nem comprova controles da infraestrutura.

### A01 — Broken Access Control

- O dashboard, a tela de cadastro e o histórico de logs exigem autenticação.
- Apenas usuários `staff` podem cadastrar contas.
- Usuários comuns só recebem seus próprios registros de acesso.
- Logout é feito por POST e protegido pelo middleware CSRF do Django.

**Implementação:** `apps/dashboards/views.py`,
`apps/authentication/views.py` e templates de navegação.

### A04 — Cryptographic Failures

- As senhas são armazenadas usando o mecanismo de hash do Django.
- Com `DEBUG=False`, cookies de sessão e CSRF usam o atributo `Secure`.
  O cookie de sessão também usa `HttpOnly` e `SameSite=Lax`.
- Redirecionamento HTTPS e HSTS são habilitados por padrão em produção.
- Gunicorn deve escutar somente em loopback, atrás do Nginx.

**Implementação:** `config/settings.py` e `gunicorn-cfg.py`. A validade do
certificado, a configuração efetiva do Nginx e testes TLS/PQC precisam ser
verificados no ambiente publicado.

### A07 — Authentication Failures

- O login usa `authenticate()` e `login()` do Django.
- Códigos de recuperação são gerados por `secrets`, expiram em 15 minutos e
  são invalidados após cinco tentativas incorretas.
- A resposta ao pedido de recuperação não informa se o e-mail está cadastrado.
- Cadastro e redefinição de senha aplicam os validadores do Django.
- O logout encerra a sessão autenticada.

**Implementação:** `apps/authentication/views.py` e `config/settings.py`.
O login não possui segundo fator nem limitação específica de tentativas.

## Executar localmente

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

Acesse `http://127.0.0.1:8000/auth/login/`. `.env.example` é apenas um
modelo; copie-o para `.env` e não preencha o modelo com segredos. Em
desenvolvimento, `DEBUG=True` permite usar o backend de e-mail de console
quando não há credenciais SMTP.

Em produção, configure no `.env` privado do servidor uma `SECRET_KEY` forte e
persistente, `DEBUG=False`, `ALLOWED_HOSTS` e credenciais SMTP
(`EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD`). Configure também
`CSRF_TRUSTED_ORIGINS` se necessário. O servidor exige chave secreta e
credenciais SMTP em modo de produção. Nunca publique `.env`, senhas ou chaves
privadas.

## Testes e verificações

```bash
python manage.py test apps.authentication.tests
python manage.py check
python manage.py check --deploy
```

Execute `check --deploy` com as variáveis de produção. Analise os avisos
considerando a configuração real do proxy e do servidor. HSTS para
subdomínios e preload não são ativados automaticamente: habilite-os somente
depois de verificar os requisitos de todos os subdomínios e da política de
preload.

## Deploy — GitHub Actions

`.github/workflows/deploy.yml` inicia o deploy após push para `master`. O
workflow conecta à EC2 por SSH, atualiza o código, garante uma `SECRET_KEY`
persistente e `DEBUG=False` no `.env`, instala dependências, aplica migrations,
coleta estáticos e reinicia Gunicorn e Nginx.

Configure os GitHub Actions Secrets `EC2_HOST`, `EC2_USER` e `EC2_SSH_KEY`.
As credenciais SMTP devem existir no `.env` privado do servidor; o workflow
não copia o `.env` local. A chave privada SSH deve ficar apenas no GitHub
Secrets e nunca ser commitada ou compartilhada.

O roteiro da disciplina menciona a branch `main`, enquanto este workflow usa
`master`. Confirme com o professor se essa diferença é aceita.

## Evidências anexadas

As imagens abaixo foram fornecidas para documentar o ambiente em **20/10/2026**.
Elas comprovam apenas o que está visível nas capturas, não todos os controles
de segurança descritos no roteiro acadêmico.

### Acesso SSH ao servidor

A captura registra uma conexão SSH bem-sucedida com a instância Ubuntu
26.04.1 LTS usando uma chave. Ela não comprova, por si só, que a autenticação
SSH por senha esteja desabilitada ou que as regras de firewall estejam
restritas.

![Sessão SSH conectada ao servidor Ubuntu](Documenta%C3%A7%C3%A3o/evidencias/acesso-ssh-ubuntu.png)

### GitHub Actions Secrets

A captura confirma que existem entradas chamadas `EC2_HOST`, `EC2_SSH_KEY` e
`EC2_USER` nos Secrets do repositório. O GitHub oculta os valores; a imagem não
comprova sua validade nem o sucesso de uma execução do deploy.

![Nomes dos GitHub Actions Secrets configurados](Documenta%C3%A7%C3%A3o/evidencias/secrets-github-actions.png)

## Verificações pendentes para a entrega

Os itens seguintes precisam de evidência adicional antes de serem marcados
como concluídos:

- [ ] Security Group/firewall libera somente as portas necessárias.
- [ ] SSH por chave, login SSH por senha desabilitado e Fail2Ban configurado
  com quatro tentativas e banimento por 24 horas.
- [ ] Redirecionamento HTTP para HTTPS e renovação automática do certificado.
- [ ] Testes TLS exigidos pelo professor e verificação de PQC.
- [ ] Execução do GitHub Actions concluída com sucesso para a versão final.
- [ ] Professor confirma que `master` atende ao requisito de deploy pela `main`.
- [ ] Evidência do uso do Antigravity ou de IDE equivalente com IA.
- [ ] Conferência final confirma que não há banco SQLite local, `.env`,
  credenciais ou chaves privadas no repositório.

Uma saída de comandos compartilhada durante a conversa também registrou
serviços Nginx e Gunicorn ativos e a jail `sshd` do Fail2Ban ativa. Naquela
verificação, o serviço systemd iniciava o Gunicorn em `127.0.0.1:8000`,
enquanto `gunicorn-cfg.py` neste repositório define `127.0.0.1:5005`.
Confirme qual configuração é usada pelo serviço de produção antes de apresentar
essa parte como evidência final. A consulta HTTPS retornou HTTP 302, mas não
foi uma prova do redirecionamento de HTTP para HTTPS.

Evite publicar logs brutos de terminal: eles podem expor endereços, nomes de
usuário, dados operacionais ou outras informações desnecessárias. As capturas
de evidência foram copiadas para `Documentação/evidencias/`; os anexos
originais não foram alterados.

## Autor

**Ubirajara Rodrigo Castro** — Pós-Graduação em Segurança da Informação e
Análise Forense, UNCISAL.
