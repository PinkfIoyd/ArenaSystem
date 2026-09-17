# ArenaFlow QA Matrix

Data: 2026-07-30

| Fluxo | Perfil | Cenario | Resultado esperado | Resultado encontrado | Severidade | Correcao | Teste |
|---|---|---|---|---|---|---|---|
| Login | Aluno | Login demo aluno | Redireciona para App aluno | Redirecionava para `/` | Medio | Rotas pessoais movidas para `/app` e destino centralizado | Lint/build |
| Login | Admin | Login demo admin | Redireciona para Painel admin | Funcionava, mas logica estava espalhada | Baixo | `initialPathFor(user)` centraliza destino | Lint/build |
| App aluno vs Admin | Admin | Trocar para app pessoal | Troca explicita e visivel | Link apontava para `/` | Medio | Links agora apontam para `/app` | Lint |
| Reservas | Admin no App aluno | Ver "Minhas reservas" | Lista somente reservas do usuario | Listava reservas da arena | Alto | Endpoint aceita `?minhas=1` e frontend usa esse escopo | `gestao.tests` |
| Reservas | Admin no App aluno | Criar reserva pessoal | Reserva vinculada ao usuario | Podia virar reserva avulsa admin | Alto | `?minhas=1` vincula `aluno=request.user` | `gestao.tests` |
| Reservas | Aluno Arena A | Acessar reserva Arena B por ID | 404 | Protegido | Critico | Mantido queryset por arena/ownership | `gestao.tests` |
| Mensalidades | Financeiro | Cancelar mensalidade | Status cancelada auditado | Status inexistente | Medio | Novo status e action `cancelar` | `arena.tests` |
| Mensalidades | Financeiro | PATCH direto de valor/status | Campos protegidos nao mudam | Serializer permitia mass assignment | Alto | Campos financeiros read-only; transicoes por actions | `arena.tests` |
| Mensalidades | Aluno Arena A | Acessar mensalidade Arena B | 404 | Protegido | Critico | Mantido queryset por aluno/arena | `arena.tests` |
| Pedidos | Aluno | Listar pedidos | Apenas proprios | Protegido em `VendaViewSet` | Alto | Confirmado em revisao | Matriz endpoint |
| Estoque | Perfil financeiro | Acessar produtos admin | 403 | Protegido | Alto | Mantido `estoque.manage` | `gestao.tests` |
| Auditoria | Recepcao | Acessar logs | 403 | Protegido | Alto | Mantido `auditoria.view` dono | `gestao.tests` |
| Uploads | Usuario | Enviar falso JPG | Rejeita conteudo invalido | Protegido | Alto | Validador backend por MIME/extensao/conteudo | `usuarios.tests` |
| Deploy | Producao | `DEBUG=False` sem SECRET/hosts | Falha ao iniciar | Protegido parcialmente | Critico | Guards de SECRET, hosts, CORS e flags HTTPS configuraveis | `manage.py check` |

## Pendencias documentadas

| Item | Motivo | Proximo passo |
|---|---|---|
| E2E automatizado | Nao existe infraestrutura E2E no projeto | Criar Playwright/Cypress em etapa propria |
| Mercado Pago real | Depende de credenciais e conta | Implementar webhook assinado/idempotente com ambiente real |
| PostgreSQL producao | Dependente de provisionamento | Adicionar adapter/config depois da escolha da infra |
| Observabilidade externa | Dependente de provedor | Definir logs/alertas no deploy |
