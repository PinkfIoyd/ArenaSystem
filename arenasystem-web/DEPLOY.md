# Deploy do ArenaSystem Web

Antes de gerar o build de producao, configure:

```env
VITE_API_URL=https://seu-backend.com/api
VITE_BASE_PATH=/
```

Se o frontend for publicado em uma subpasta, como GitHub Pages, use o caminho da subpasta:

```env
VITE_BASE_PATH=/nome-do-repositorio/
```

No backend, libere o dominio publicado do frontend:

```env
CORS_ALLOWED_ORIGINS=https://seu-frontend.com
CSRF_TRUSTED_ORIGINS=https://seu-frontend.com
FRONTEND_URL=https://seu-frontend.com
PUBLIC_BACKEND_URL=https://seu-backend.com
```

O arquivo `public/_redirects` cobre deploys estaticos como Netlify/Render Static. O
`vercel.json` cobre rotas diretas no Vercel, como `/admin`, `/turmas` e `/login`.
