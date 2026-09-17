# ArenaFlow Product Decisions

## Identidade visual

Nome: ArenaFlow

Paleta principal:

- Azul profundo: `#123B5D`
- Verde esportivo: `#22C55E`
- Branco: `#FFFFFF`

Uso:

- Azul profundo: navegacao, cabecalhos, identidade e acoes administrativas.
- Verde esportivo: sucesso, disponibilidade, destaques positivos e acao primaria quando apropriado.
- Branco: superficies e areas de leitura.

Cores semanticas funcionais continuam permitidas para erro, alerta, status financeiro e graficos, desde que nao substituam a marca.

## Contextos de produto

- Painel admin: `/admin/...`
- App aluno: `/app/...`
- Rotas antigas do app aluno redirecionam para `/app/...` para compatibilidade.
- Administradores elegiveis podem trocar explicitamente para App aluno, mas endpoints pessoais continuam filtrando por ownership.

## Financeiro

Estados preservados do backend:

- `pendente`: mensalidade aguardando pagamento.
- `pago`: mensalidade paga. Mantido por compatibilidade, exibido como "Pago".
- `atrasado`: calculado no backend quando `hoje >= vencimento + 5 dias`.
- `cancelada`: mensalidade cancelada manualmente por perfil autorizado.

Preparacao para pagamentos futuros:

- `external_reference`
- `payment_provider`
- `external_status`
- `processed_at`
- `idempotency_key`
- `PaymentWebhookEvent`

Mercado Pago real depende de credenciais, validacao de webhook e decisao de infraestrutura.

## Indicadores do dashboard

Periodo padrao: mes corrente ou proximos 30 dias, conforme o dado.

- Ocupacao por quadra: reservas confirmadas/concluidas sobre capacidade operacional do periodo.
- Inadimplencia: mensalidades `atrasado` ou pendentes vencidas apos carencia.
- Alunos ativos: matriculas `ativa=True`.
- Alunos inativos: usuarios/matriculas desativados ou matriculas encerradas.
- Receita prevista: soma de mensalidades no periodo.
- Receita recebida: mensalidades pagas + vendas pagas no periodo.
- Estoque baixo: produtos com `estoque <= estoque_minimo`.
- Reservas da semana: reservas entre hoje e hoje + 7 dias, exceto canceladas.

Todas as metricas devem ser agregadas no backend e filtradas pela arena ativa.
