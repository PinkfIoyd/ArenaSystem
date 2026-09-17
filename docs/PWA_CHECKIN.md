# PWA e check-in validado pela arena

## Fluxo

1. O aluno abre `/app` e solicita o check-in entre os limites configurados na arena (padrão: 20 minutos antes e 10 minutos depois do início).
2. O backend valida arena, usuário, matrícula, turma, data, janela, assinatura SaaS, inadimplência e duplicidade.
3. A solicitação fica `pending` até recepção, administrador ou professor da turma confirmar ou rejeitar.
4. A fila operacional em `/admin/checkins` atualiza a cada cinco segundos e permite confirmação individual ou em lote.
5. Confirmação, rejeição, registro manual e correção são auditados. Rejeição, manual e correção exigem motivo.

## Rotinas idempotentes

```powershell
python manage.py generate_class_occurrences --date 2026-08-10
python manage.py expire_checkins --reference-date 2026-08-11
```

O Celery Beat também executa a geração de ocorrências e a expiração. A consulta às telas aplica expiração preguiçosa quando necessário.

## PWA e cache

- O manifesto inicia em `/app` e usa modo `standalone`.
- O service worker armazena somente a página offline, ícones públicos e arquivos versionados de `/assets/`.
- Chamadas `/api/`, requisições com `Authorization`, mídias de usuários e dados financeiros não entram no cache.
- Navegação sem rede abre uma página informando que check-in exige internet.
- QR Code, câmera, geolocalização, push e check-in offline não fazem parte desta versão.

## Validação antes do piloto

- Executar testes Django, Vitest, build Vite e Playwright.
- Validar instalação e atualização em dispositivos físicos Android/Chrome e iPhone/Safari.
- Conferir fuso horário e janelas em uma arena piloto.
- Confirmar que worker e Beat estão ativos no ambiente publicado.
