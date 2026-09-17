# ArenaFlow

ArenaFlow é uma plataforma SaaS multi-tenant para a gestão de arenas esportivas e academias. O projeto reúne operação administrativa, experiência mobile instalável, cobrança, auditoria e isolamento de dados por unidade.

> Projeto de portfólio desenvolvido com apoio intensivo de inteligência artificial. As decisões de produto, revisão, testes e evolução do código fazem parte do trabalho apresentado neste repositório.

## Principais recursos

- Multi-tenancy por unidade, com suporte a arenas e academias.
- Painel administrativo responsivo com terminologia e identidade configuráveis.
- PWA para alunos e membros, instalável em Android e iPhone.
- Check-in de aulas com validação pela recepção ou professor.
- Acesso livre para academias, com confirmação, check-out e limites do plano.
- Turmas, reservas, mensalidades, estoque, usuários e permissões.
- Operação SaaS com planos, assinaturas, faturas, trial, carência e auditoria.
- Modo superadmin com acesso assistido e logs cross-tenant.
- Onboarding, convites, recuperação de senha, suporte e infraestrutura LGPD.
- Tarefas assíncronas com Celery e preparação para PostgreSQL, Redis e deploy.

## Tecnologias

**Backend:** Python, Django, Django REST Framework, Simple JWT, Celery, PostgreSQL/SQLite e Gunicorn.

**Frontend:** React, Vite, Tailwind CSS, Vitest e Playwright.

**Infraestrutura preparada:** Supabase/PostgreSQL, Render, Vercel, Redis, WhiteNoise e Sentry opcional.

## Estrutura

```text
arenasystem/       Backend Django e APIs
arenasystem-web/   Frontend React e PWA
docs/              Decisões, operação e roteiros de validação
render.yaml        Blueprint de infraestrutura sem segredos
```

## Execução local

### Backend

```bash
cd arenasystem
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd arenasystem-web
npm install
copy .env.example .env
npm run dev
```

As variáveis dos arquivos `.env.example` são apenas referências. Credenciais, senhas e chaves reais não devem ser versionadas.

## Qualidade

```bash
# Backend
cd arenasystem
python manage.py check
python manage.py test
python manage.py makemigrations --check

# Frontend
cd arenasystem-web
npm run lint
npm run test
npm run build
npm run test:e2e
```

## Estado do projeto

O núcleo multi-tenant, a PWA, o check-in de aulas e o acesso livre estão implementados. Antes de uso comercial ainda são necessários homologação de integrações externas, testes em dispositivos reais, validação jurídica e piloto controlado. A agenda de aulas abertas/avulsas é uma evolução planejada.

Consulte a pasta [`docs`](docs/) para detalhes operacionais e critérios de validação.
