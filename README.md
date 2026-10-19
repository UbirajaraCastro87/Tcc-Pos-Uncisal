# Sistema de Autenticação Segura com MFA (TCC)

Este repositório contém o desenvolvimento de um sistema web seguro para autenticação de usuários, desenvolvido como requisito da disciplina **Projeto Aplicado: Práticas de Mercado** da Pós-Graduação em Segurança da Informação e Análise Forense da UNCISAL.

O projeto foi construído seguindo os princípios de **Secure by Design** e **Defense in Depth**, implementando autenticação multifator (MFA/2FA), controle de acesso, criptografia de comunicação e boas práticas de infraestrutura em nuvem.

---

# 🚀 Tecnologias Utilizadas

- **Backend:** Python 3 / Django
- **Frontend:** Bootstrap Materio (Material Design)
- **Banco de Dados:** SQLite
- **Servidor Web:** Nginx
- **Servidor de Aplicação:** Gunicorn
- **Hospedagem:** AWS EC2 (Ubuntu Server)
- **DNS:** DuckDNS
- **Certificado SSL/TLS:** Let's Encrypt
- **Controle de Versão:** Git e GitHub
- **CI/CD:** GitHub Actions

---

# 🌐 Ambiente de Produção

A aplicação encontra-se publicada em ambiente de nuvem pública utilizando:

- AWS EC2 Free Tier
- Ubuntu Server
- Nginx Reverse Proxy
- Gunicorn
- HTTPS com Let's Encrypt
- Fail2Ban para proteção contra força bruta
- Acesso administrativo via SSH com chave criptográfica

URL da aplicação:

```text
https://ubirajarauncisal.duckdns.org
```

---

# 🛡️ Funcionalidades Implementadas

## 1. Autenticação Baseada em Credenciais

- Login utilizando usuário/e-mail e senha.
- Validação segura utilizando o método `authenticate()`.
- Armazenamento seguro das senhas através do mecanismo de hash do Django.

## 2. Autenticação em Duas Etapas (2FA)

- Geração de token numérico aleatório de 6 dígitos.
- Validação do token antes da autenticação final.
- Isolamento da sessão temporária pré-autenticação.
- Estrutura preparada para integração futura com SMTP.

## 3. Gerenciamento de Sessão

- Persistência segura da sessão.
- Controle de autenticação utilizando recursos nativos do Django.
- Limpeza de credenciais temporárias após autenticação.

## 4. Logout Seguro

- Encerramento da sessão utilizando `logout()`.
- Remoção de variáveis temporárias.
- Redirecionamento para a tela de login.

## 5. Painel Administrativo Protegido

- Área acessível apenas após autenticação.
- Dados do usuário autenticado disponíveis em toda a aplicação.

---

# ✅ Mitigações OWASP Top 10

Este projeto implementa controles para mitigar vulnerabilidades presentes no OWASP Top 10.

## A01 - Broken Access Control

### Mitigação

- Áreas internas protegidas por autenticação.
- Usuários não autenticados são redirecionados para a tela de login.
- Controle de sessão realizado pelo Django.

### Implementação

```python
@login_required
```

e validações de autenticação em views protegidas.

---

## A02 - Cryptographic Failures

### Mitigação

- Comunicação protegida por HTTPS.
- Certificado SSL/TLS emitido via Let's Encrypt.
- Redirecionamento automático HTTP → HTTPS.
- Cookies de sessão protegidos.

### Implementação

```python
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## A07 - Identification and Authentication Failures

### Mitigação

- Autenticação baseada em credenciais.
- Implementação de MFA / 2FA.
- Logout seguro.
- Senhas armazenadas com hash seguro do Django.

### Implementação

```python
authenticate()
login()
logout()
```

e fluxo de validação por segundo fator.

---

# 🔒 Medidas de Segurança da Infraestrutura

## Acesso Seguro

- SSH utilizando chave criptográfica.
- Autenticação por senha desabilitada.

## Proteção Contra Força Bruta

Fail2Ban configurado para:

```text
Max Retry: 4
Ban Time: 24 horas
```

## Comunicação Segura

- HTTPS obrigatório.
- Certificado SSL/TLS válido.
- Renovação automática de certificados.

---

# ⚙️ Como Executar o Projeto Localmente

## 1. Clonar o repositório

```bash
git clone https://github.com/UbirajaraCastro87/Tcc-Pos-Uncisal.git
cd Tcc-Pos-Uncisal
```

## 2. Criar ambiente virtual

Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

## 3. Instalar dependências

```bash
pip install -r requirements.txt
```

## 4. Aplicar migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

## 5. Criar usuário administrador

```bash
python manage.py createsuperuser
```

## 6. Executar o projeto

```bash
python manage.py runserver
```

## 7. Acessar

```text
http://127.0.0.1:8000/auth/login/
```

---

# 🔄 CI/CD com GitHub Actions

O projeto utiliza GitHub Actions para automação de deploy.

Fluxo:

```text
Desenvolvimento
        ↓
Git Push
        ↓
GitHub
        ↓
GitHub Actions
        ↓
Servidor AWS
        ↓
Deploy Automático
```

A pipeline realiza:

- Atualização do código
- Instalação de dependências
- Migrações do banco
- Coleta de arquivos estáticos
- Reinicialização dos serviços

---

# 📂 Estrutura do Projeto

```text
Tcc-Pos-Uncisal/
│
├── apps/
├── config/
├── src/
├── templates/
├── staticfiles/
├── web_project/
├── manage.py
├── requirements.txt
├── README.md
└── gunicorn-cfg.py
```

---

# 👨‍💻 Autor

**Ubirajara Castro**

Projeto desenvolvido para fins acadêmicos como requisito parcial para conclusão da Pós-Graduação em Segurança da Informação e Análise Forense - UNCISAL.

---

