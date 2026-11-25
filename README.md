# Sabor & Clic

Projeto de um sistema de pedidos e reservas de espaços gastronômicos. Possui cardápio, carrinho, painel administrativo e áreas para cozinha e entregas.

## Tecnologias

Python, Flask, PostgreSQL (Neon), HTML, CSS e JavaScript. O acesso ao banco é feito com SQL e Psycopg.

## Como executar

Configure as variáveis de ambiente conforme o arquivo `.env.example`.

```sh
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```

O sistema cria as tabelas e os dados iniciais com o comando `init-db`. Os pedidos não possuem pagamento integrado.

Para publicar no Render, consulte [RENDER.md](RENDER.md).
