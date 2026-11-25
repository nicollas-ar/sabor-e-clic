# Neon e Render

1. Crie um projeto PostgreSQL no Neon e copie a URL de conexão direta (sem pooler), com SSL.
2. No Render, crie um Blueprint usando este repositório e a branch `main`.
3. Preencha `DATABASE_URL` com a URL do Neon, `ADMIN_EMAIL` com seu e-mail e `ADMIN_PASSWORD` com uma senha de pelo menos 12 caracteres. O Blueprint gera `SECRET_KEY` e configura `COOKIE_SECURE=1`.
4. Acompanhe os logs do deploy. O comando de inicialização cria as tabelas, os dados iniciais e a conta administrativa antes de iniciar o Gunicorn.
5. Teste `/saude`, `/cardapio`, `/espacos` e `/entrar`.

Se já existir um serviço Web no Render, altere as variáveis em Environment e use os comandos definidos em `render.yaml`.

O banco é inicializado do zero se estiver vazio. Dados de um MySQL anterior não são importados automaticamente. Não publique credenciais no GitHub.
