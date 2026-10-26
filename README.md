# Kibarato

## Desenvolvimento local

Execute `make setup` na primeira vez e `make dev` para iniciar o site.
Abra **http://127.0.0.1:8000** (HTTP, sem HTTPS).
O modo local usa explicitamente `config.settings_dev`, serve CSS e imagens,
habilita recarga automática e utiliza o banco separado `db.dev.sqlite3`.
`config.settings` continua sendo a configuração padrão de produção.
Use `make check` para verificar o ambiente local.

## Arquivos estáticos em produção

Execute `make collectstatic` no VPS após cada atualização do site. Esse comando
reúne CSS e JavaScript de `static/` e imagens de `assets/` em `staticfiles/`.
Essa pasta é gerada no servidor e não é versionada no Git.

Configure o Nginx para servir `/static/` a partir de `staticfiles/`, não de
`static/` (que não contém as imagens). No bloco `server` do site, use o caminho
absoluto real do projeto no VPS:

```nginx
location /static/ {
    alias /caminho/absoluto/kibarato/staticfiles/;
}
```

Se houver regras por extensão para imagens, verifique se elas não substituem
esse mapeamento. Após alterar a configuração, execute `sudo nginx -t` e
`sudo systemctl reload nginx`.

Verifique se `/static/Widekibarato.png` e `/static/carousel/images.jpeg`
retornam HTTP 200. Se continuarem retornando 404, confira o caminho do `alias`
e as regras de localização no Nginx. O servidor de desenvolvimento serve os
arquivos automaticamente e não precisa dessa configuração.

## Search indexing

The site serves `/robots.txt` and `/sitemap.xml` through Django. The sitemap
lists the public home page using `https://www.tecidoskibarato.com.br`, the
production hostname in the project settings. When adding public pages, add
their canonical HTTPS URLs to `templates/sitemap.xml`. If the production
domain changes, update both indexing templates.

After deployment, submit `https://www.tecidoskibarato.com.br/sitemap.xml` in
Google Search Console. These files help discovery but do not guarantee
indexing or ranking. The robots rule discourages crawling `/admin/`; it does
not replace authentication or prevent access.

Run Django's deployment checks:

```sh
.venv/bin/python manage.py check --deploy
```

The settings require HTTPS, use secure session and CSRF cookies, and set an
initial HSTS lifetime of one hour, including subdomains. Serve the application
and all its subdomains over HTTPS. The preload directive is enabled but does not
automatically register the domain in a browser preload list. If a trusted
reverse proxy terminates TLS, configure Django's proxy SSL header to match that
proxy's configuration before deploying; the proxy must strip spoofed headers.

Email uses SMTP with STARTTLS. Set `SMTP_HOST`, `SMTP_PORT` (default `587`),
`SMTP_USERNAME`, `SMTP_PASSWORD`, and `DEFAULT_FROM_EMAIL` in the server's
environment. The default host is `localhost`; mail delivery requires a working
SMTP server and a sender address accepted by that server.

## Promoções no painel administrativo

As promoções da página inicial são registros do modelo `Promotion`. Acesse
`/admin/` para adicionar, editar ou excluir foto, descrição e preço. Fotos aceitam
JPG, PNG e WebP de até 10 MB. O preço é em reais; vazio exibe “Preço sob consulta”.
No campo foto, escolha um arquivo ou use “tirar foto com a câmera” no celular.
A abertura da câmera depende do navegador; no computador pode aparecer o seletor
de arquivos. Se preencher as duas opções, a foto da câmera tem prioridade.
Selecione a unidade de venda: metro, unidade ou quilograma. Por exemplo,
`29,90` com metro aparece como “R$ 29,90 / m”. “Sem unidade” mantém apenas o preço.
A galeria mostra as promoções mais recentes primeiro e começa vazia até cadastrar
os produtos reais. As imagens de exemplo anteriores não são ofertas cadastradas.

Após atualizar o código no servidor:

```sh
uv sync --locked
.venv/bin/python manage.py migrate
.venv/bin/python manage.py create_promotions_user promocoes
make collectstatic
```

O comando solicita a senha sem exibi-la. Ele cria um usuário de equipe com acesso
somente para visualizar, adicionar, editar e excluir promoções, sem acesso a
usuários, grupos ou permissões. Não altera contas existentes. Para redefinir a
senha, use `manage.py changepassword promocoes`. Reinicie o serviço da aplicação
após atualizar o código.

No ambiente local, acrescente `--settings=config.settings_dev` aos comandos.
O banco e as fotos locais ficam separados dos de produção. A opção
`--password-file .local/promocoes-login.txt` gera uma senha e grava um arquivo novo
com acesso restrito; `.local/` não é versionada. Não envie esse arquivo ao Git.

Em produção, configure o Nginx para servir as fotos enviadas (elas não fazem parte
do `collectstatic`). Use o caminho real do projeto:

```nginx
location ^~ /media/ {
    alias /caminho/absoluto/kibarato/media/;
    add_header X-Content-Type-Options nosniff always;
}
```

Garanta que o usuário da aplicação possa gravar em `media/` e que o Nginx possa
ler os arquivos. Para permitir as fotos de até 10 MB, configure
`client_max_body_size 12m;` no bloco `server`. Faça backup do banco e de `media/`.
A exclusão de uma promoção retira o item da galeria; os arquivos antigos são
mantidos em disco, seguindo o comportamento padrão do Django.
