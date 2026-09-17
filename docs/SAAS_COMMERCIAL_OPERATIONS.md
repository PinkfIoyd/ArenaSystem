# ArenaFlow — operacao comercial SaaS

## Ciclo da assinatura

- Trial: 14 dias.
- Carencia: 7 dias apos falha ou fim do trial sem pagamento.
- Upgrade: imediato depois da confirmacao da cobranca proporcional.
- Downgrade: agendado para o proximo ciclo e bloqueado quando o consumo excede o novo plano.
- Cancelamento: acesso ate o fim do periodo; reativacao permitida antes do encerramento.
- Suspensao: bloqueia modulos operacionais, preservando assinatura, suporte e solicitacoes de dados.

## Rotinas

- Celery Beat dispara reconciliacao, avisos, snapshots e heartbeat.
- `reconcile_saas_subscriptions` permite reconciliacao manual idempotente.
- O painel Operacao SaaS mostra MRR, status, falhas, tickets e saude da conta.
- Todo acesso assistido permanece sob contexto explicito e auditoria cross-tenant.

## LGPD

- Termos, politica e DPA foram criados somente como rascunhos de infraestrutura.
- Nenhum rascunho pode ser publicado sem revisao juridica.
- Exclusao e anonimizacao exigem analise humana; nao existe hard-delete automatico.
- Exportacoes sao autorizadas por tenant e entregues com `Cache-Control: no-store`.
- Storage privado externo e URLs assinadas permanecem obrigatorios antes de exportacoes grandes em producao.

## Pendencias externas

- Precificacao comercial dos planos.
- Credenciais Mercado Pago SaaS e simulacao sandbox.
- Redis, worker e scheduler em homologacao.
- SMTP transacional.
- Sentry/alertas de uptime.
- Storage privado para anexos e exportacoes grandes.
- Politica juridica de retencao.
- Piloto real e teste de restauracao.
