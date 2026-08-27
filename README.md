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
