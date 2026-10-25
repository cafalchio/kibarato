# Kibarato

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
