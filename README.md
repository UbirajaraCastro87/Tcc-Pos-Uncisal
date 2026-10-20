# Sistema de autenticação — TCC

Aplicação web desenvolvida para a disciplina **Projeto Aplicado: Práticas de
Mercado** da Pós-Graduação em Segurança da Informação e Análise Forense da
UNCISAL. O projeto demonstra autenticação, autorização, auditoria de acesso e
implantação automatizada.

## Tecnologias

- Python e Django
- SQLite
- Templates Django e Bootstrap Materio
- Gunicorn e Nginx
- Ubuntu Server em AWS EC2
- GitHub e GitHub Actions
- HTTPS no domínio `https://ubirajarauncisal.duckdns.org`

O repositório não contém o banco de dados local, arquivos `.env`, nem chaves
privadas. Cada ambiente mantém seu próprio banco SQLite.

## Funcionalidades

- Login com usuário e senha do Django; a autenticação de dois fatores está
  desativada.
- Página interna e histórico de acessos protegidos por autenticação.
- Usuários comuns visualizam apenas os próprios registros de acesso; usuários
  `staff` podem consultar todos os registros.
- Cadastro de usuários restrito a usuários autenticados com permissão `staff`.
- Logout por requisição POST protegida por CSRF.
- Recuperação de senha por e-mail com código aleatório, validade de 15 minutos
  e limite de cinco tentativas.
- Senhas criadas ou redefinidas são verificadas pelos validadores do Django e
  armazenadas usando o hash de senha do framework.

> O login utiliza um único fator (usuário e senha). A aplicação não deve ser
> descrita como MFA/2FA enquanto o segundo fator estiver desativado.

## Controles documentados em relação ao OWASP Top 10:2025

### A01 — Broken Access Control

- `LoginRequiredMixin` protege o painel e os registros de acesso.
- O cadastro de usuários exige que a conta autenticada seja `staff`.
- O histórico de acessos de usuários comuns é filtrado pela conta atual.
- O logout usa POST e o middleware CSRF padrão do Django.

Implementação: `apps/dashboards/views.py` e
`apps/authentication/views.py`.

### A04 — Cryptographic Failures

- O Django armazena senhas como hashes, não como texto puro.
- Em modo de produção (`DEBUG=False`), cookies de sessão e CSRF são marcados
  como `Secure`; os cookies de sessão também são `HttpOnly` e `SameSite=Lax`.
- HSTS e redirecionamento HTTPS são habilitados por padrão em produção.
- A aplicação confia no cabeçalho `X-Forwarded-Proto` do proxy reverso. O Nginx
  deve enviar esse cabeçalho corretamente e a origem de Gunicorn não deve estar
  exposta diretamente à Internet.

Implementação: `config/settings.py`. A validade do certificado, a configuração
do Nginx e os resultados de testes externos de TLS/PQC são verificações de
infraestrutura; não são comprovados apenas pelo código.
O Gunicorn está configurado em `gunicorn-cfg.py` para escutar somente em
`127.0.0.1:5005`, atrás do Nginx.

### A07 — Authentication Failures

- O login utiliza `authenticate()` e `login()` do Django.
- As senhas definidas pela aplicação passam pelos validadores configurados.
- O código de recuperação é gerado com `secrets`, expira em 15 minutos e
  permite no máximo cinco tentativas.
- A resposta à solicitação de recuperação não informa se o endereço está
  cadastrado.
- O logout encerra a sessão do Django.

Implementação: `apps/authentication/views.py` e
`config/settings.py`. Como não há segundo fator nem limitação de tentativas no
login, esses riscos residuais devem ser considerados na apresentação.

## Configuração local

Requer Python compatível com Django 5.2 e as dependências em
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

### Linux/macOS

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

Abra `http://127.0.0.1:8000/auth/login/`. Em desenvolvimento, o exemplo ativa
`DEBUG=True`; sem credenciais SMTP, as mensagens de recuperação são escritas no
console. Não use esse modo em produção.

O `SECRET_KEY` é opcional apenas no modo local de depuração; nesse caso, uma
chave temporária é gerada ao iniciar o Django. Para produção, configure uma
chave aleatória e estável no `.env` do servidor, mantenha `DEBUG=False` e
configure `ALLOWED_HOSTS`, `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD`. Nunca
publique esses valores no Git.

## Testes e verificações

```bash
python manage.py test apps.authentication.tests
python manage.py check
python manage.py check --deploy
```

O último comando verifica configurações de produção; revise cada aviso no
contexto do proxy reverso e do servidor antes da publicação. Os avisos atuais
de HSTS para subdomínios e preload permanecem intencionais até que todos os
subdomínios e a inscrição na lista de preload sejam validados.

## Deploy por GitHub Actions

O workflow `.github/workflows/deploy.yml` é acionado por push na branch
`master`. Ele atualiza o código na EC2, garante uma `SECRET_KEY` persistente
caso ainda não exista, força `DEBUG=False`, instala as dependências, aplica
migrations, coleta arquivos estáticos e reinicia Gunicorn e Nginx.

Configure em **Settings → Secrets and variables → Actions** os segredos
`EC2_HOST`, `EC2_USER` e `EC2_SSH_KEY`. O servidor também precisa ter as
credenciais SMTP em seu `.env`; o workflow não envia esse arquivo ao GitHub.
A chave SSH privada deve permanecer somente nos GitHub Secrets e não pode ser
commitada ou compartilhada.

> O escopo acadêmico cita um push para `main`; este repositório usa `master`.
> Confirme com o professor se essa diferença de nome é aceita ou se ele exige
> literalmente a branch `main`.

## Evidências de infraestrutura a validar para a entrega

Os itens abaixo dependem de acesso à conta de nuvem e ao servidor e precisam
ser comprovados separadamente:

- [x] Ubuntu Server ou Debian em versão estável.
- [x] Apenas as portas necessárias liberadas; SSH por chave e autenticação SSH
  por senha desabilitada.
- [x] Fail2Ban na porta 22 com quatro tentativas e banimento de 24 horas.
- [x] Nginx redireciona HTTP para HTTPS; certificado e renovação automática
  verificados.
- [x] Resultado exigido pelo professor nos verificadores TLS e PQC.
- [x] Execução de deploy do GitHub Actions concluída com sucesso.
- [x] Evidências de uso do VSCode ou de ambiente de desenvolvimento com IA equivalente.
- [x] Nenhum `.env`, segredo, chave privada ou banco de dados local versionado.

## Autor

**Ubirajara Rodrigo Castro** — projeto acadêmico da Pós-Graduação em Segurança da
Informação e Análise Forense da UNCISAL.


#### Comando para verificação 


echo "===== SERVIDOR =====" && \
hostname && \
echo "" && \
echo "===== SISTEMA OPERACIONAL =====" && \
cat /etc/os-release | head -5 && \
echo "" && \
echo "===== NGINX =====" && \
sudo systemctl status nginx --no-pager | head -10 && \
echo "" && \
echo "===== GUNICORN =====" && \
sudo systemctl status gunicorn --no-pager | head -15 && \
echo "" && \
echo "===== FAIL2BAN =====" && \
sudo fail2ban-client status sshd && \
echo "" && \
echo "===== DOMINIO =====" && \
curl -I https://ubirajarauncisal.duckdns.org 2>/dev/null | head -5 && \
echo "" && \
echo "===== PORTA 8000 =====" && \
sudo ss -tulpn | grep 8000 && \
echo "" && \
echo "===== GUNICORN PROCESSOS =====" && \
ps aux | grep gunicorn | grep -v grep && \
echo "" && \
echo "===== GIT ULTIMOS COMMITS =====" && \
cd ~/Tcc-Pos-Uncisal && git log --oneline -5 && \
echo "" && \
echo "===== WORKFLOW CI/CD =====" && \
cat .github/workflows/deploy.yml && \
echo "" && \
echo "===== PYTHON =====" && \
source .venv/bin/activate && python --version && \
echo "" && \
echo "===== MIGRATIONS =====" && \
python manage.py showmigrations | tail -20 && \
echo "" && \
echo "===== USUARIOS =====" && \
python manage.py shell -c "from django.contrib.auth.models import User; print('TOTAL DE USUARIOS:', User.objects.count())" && \
echo "" && \
echo "===== BANCO SQLITE =====" && \
sqlite3 db.sqlite3 "select count(*) from auth_user;" && \
echo "" && \
echo "===== LOGS GUNICORN =====" && \
sudo journalctl -u gunicorn -n 20 --no-pager