# ArenaFlow Web

Interface React do ArenaFlow, incluindo painel administrativo, área SaaS e PWA para alunos, membros e professores.

## Desenvolvimento

```bash
npm install
copy .env.example .env
npm run dev
```

Por padrão, o frontend espera a API local indicada em `.env.example`.

## Validação

```bash
npm run lint
npm run test
npm run build
npm run test:e2e
```

## PWA

O service worker armazena apenas o shell e os arquivos públicos versionados. APIs e respostas autenticadas permanecem dependentes de rede e não são disponibilizadas no cache offline.

Consulte o [README principal](../README.md) e a [documentação de check-in](../docs/PWA_CHECKIN.md).
