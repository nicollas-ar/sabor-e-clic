# Sabor & Clic — Flask + SQL puro (MySQL)

Sistema integrado de cardápio, carrinho, pedidos, bancadas, cozinha, entregas e permissões.

## Tecnologias
Flask, PyMySQL, SQL explícito com parâmetros %s, HTML/CSS/JS. **Não utiliza SQLAlchemy**.

## Rodar localmente
1. Crie um banco MySQL 8 na nuvem.
2. Copie .env.example para .env, preencha DATABASE_URL, SECRET_KEY, ADMIN_EMAIL e ADMIN_PASSWORD.
3. Instale: `pip install -r requirements.txt`
4. Inicialize tabelas e dados: `flask --app app init-db`
5. Execute: `flask --app app run --debug`
6. Entre usando o e-mail e a senha do administrador definidos no .env.

## Vercel
Importe o repositório na Vercel e configure as mesmas variáveis de ambiente (COOKIE_SECURE=1). Rode o init-db localmente, apontando para o banco remoto, antes da publicação.

## Observações
MVP para testes: ainda não inclui cobrança, antifraude, proteção CSRF e demais controles necessários para operação comercial. Não compartilhe credenciais. O checkout registra pedidos sem processar pagamento. Evite usar em produção antes de auditoria de segurança.
