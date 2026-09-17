# ArenaFlow Deploy Runbook

## Build local validado

Backend:

```powershell
cd arenasystem
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test
venv\Scripts\python.exe manage.py migrate
```

Frontend:

```powershell
cd arenasystem-web
npm run lint
npm run build
```

## Variaveis obrigatorias em producao

Backend:

- `DEBUG=False`
- `SECRET_KEY`: segredo forte e exclusivo do ambiente
- `ALLOWED_HOSTS`: dominios reais, sem `*`
- `CORS_ALLOWED_ORIGINS`: frontend real, sem wildcard
- `CSRF_TRUSTED_ORIGINS`: origens HTTPS confiaveis
- `FRONTEND_URL` e `PUBLIC_BACKEND_URL`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_SSL_REDIRECT=True` quando houver HTTPS no Django/proxy
- `USE_X_FORWARDED_PROTO=True` quando houver proxy reverso HTTPS
- `REDIS_URL`: broker compartilhado por web, worker e scheduler
- `MERCADO_PAGO_SAAS_ACCESS_TOKEN` e `MERCADO_PAGO_SAAS_WEBHOOK_SECRET`
- SMTP: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- `SENTRY_DSN` opcional; PII permanece desabilitada

Frontend:

- `VITE_API_URL`: URL publica da API terminando em `/api`
- `VITE_BASE_PATH`: `/` salvo deploy em subpasta

## Banco

Desenvolvimento usa SQLite. Producao deve usar PostgreSQL ou banco provisionado pelo provedor. Antes de migrar:

1. Fazer backup do SQLite atual, se tiver dados reais.
2. Provisionar banco.
3. Adicionar adapter/config de banco ao backend.
4. Rodar migrações em ambiente de staging.
5. Validar rollback e restore.

### Demonstracao: Supabase + Render + Vercel

- Crie um projeto Supabase exclusivo para demo e use a connection string PostgreSQL do session pooler em `DATABASE_URL`.
- No Render, use o Blueprint `render.yaml` da raiz e preencha apenas as variaveis marcadas como `sync: false`.
- No Vercel, publique `arenasystem-web` com `VITE_API_URL=https://<servico-render>/api`, `VITE_DEMO_LOGIN_ENABLED=true` e somente usernames demo publicos.
- Execute `seed_demo`, `seed_gestao` e `seed_estoque` somente com `DEMO_MODE=True`; a senha vem de `DEMO_ADMIN_PASSWORD` e nunca deve entrar no bundle React.
- O filesystem do Render e efemero. Nao use uploads locais como fonte persistente no ambiente demo.

## HTTPS, dominio e proxy

Configurar:

- DNS do frontend.
- DNS/API do backend.
- Certificado HTTPS.
- Proxy reverso encaminhando `X-Forwarded-Proto`.
- `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS` coerentes.

## Logs

Requisitos antes de producao:

- logs de erro do backend;
- logs de acesso do proxy;
- sem senhas/tokens em logs;
- retencao e rotacao definidas;
- monitoramento de 5xx e latencia.

O backend emite JSON estruturado e `X-Request-ID`. `/api/health/` e minimo; `/api/health/ready/` exige banco, Redis e heartbeat do worker. Detalhes dos componentes ficam restritos ao superadmin.

## Backup

Estrategia sugerida:

- backup automatico diario do banco;
- backup de midias enviadas;
- retencao minima de 7 diarios e 4 semanais;
- armazenamento externo criptografado;
- teste mensal de restauracao;
- RPO sugerido: 24h;
- RTO sugerido MVP: 4h.

## Assinatura SaaS e tarefas

- Web, Celery worker, Celery Beat e Redis devem usar o mesmo `SECRET_KEY`, `DATABASE_URL` e `REDIS_URL`.
- O webhook SaaS valida `x-signature`/`x-request-id`, consulta o recurso no Mercado Pago e usa idempotencia local.
- Planos nascem como rascunho sem preco. O superadmin precisa precificar e publicar antes do checkout.
- Execute `python manage.py reconcile_saas_subscriptions` como reconciliacao manual segura.
- Nao confunda `MERCADO_PAGO_ACCESS_TOKEN` (mensalidades dos alunos) com `MERCADO_PAGO_SAAS_ACCESS_TOKEN` (assinaturas das arenas).

## Restauracao

1. Criar um banco temporario isolado.
2. Restaurar o backup sem apontar a aplicacao de producao.
3. Rodar `manage.py migrate --plan` e `manage.py check`.
4. Conferir arenas, usuarios, assinaturas, faturas e auditoria por contagem e amostragem.
5. Executar smoke tests tenant A/tenant B.
6. Registrar data, RPO observado, tempo total e responsavel.
7. Promover o banco restaurado somente com autorizacao formal.

O teste real de restauracao continua pendente ate existirem projeto Supabase, backup e autorizacao.
