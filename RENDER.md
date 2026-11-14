# Publicação no Render

Este projeto usa **SQL puro com PyMySQL**. O banco MySQL fica em um provedor externo.

## Publicação
1. No Render, escolha **New > Blueprint** e conecte o GitHub `nicollas-ar/sabor-e-clic` na branch `main`.
2. O arquivo `render.yaml` define o serviço web, o Gunicorn e a rota de saúde `/saude`.
3. Configure as variáveis solicitadas: `DATABASE_URL` (URL MySQL), `ADMIN_EMAIL`, `ADMIN_PASSWORD` (12+ caracteres). A chave `SECRET_KEY` é gerada pelo Render.
4. Confirme a criação do serviço e acompanhe **Logs**.
5. Na inicialização, o comando `flask --app app init-db` cria as tabelas caso não existam e insere dados de demonstração. Em seguida, o Gunicorn inicia o site.
6. Abra `/saude`, `/cardapio` e `/espacos` para testar.

## Observações
- Não inclua senhas no GitHub ou em capturas de tela.
- A URL deve começar com `mysql://` ou `mysql+pymysql://`. Para provedores que exigem TLS, use `?ssl=true` na URL.
- Se o MySQL gratuito dormir ou bloquear conexões externas, o site poderá falhar nas páginas que consultam o banco.
- Não é necessário executar `init-db` no Shell do Render, pois ele faz parte do comando de inicialização.
- A aplicação é um MVP e ainda precisa de proteção CSRF, limites de requisições, recuperação de senha e revisão de segurança antes de uso comercial.
