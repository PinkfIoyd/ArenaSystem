# ArenaFlow Endpoint Security Matrix

Fonte de verdade: Django REST Framework + `usuarios.permissions.require_permission`.

| Endpoint | Metodo | Autenticacao | Perfis | Escopo/ownership | Teste |
|---|---|---|---|---|---|
| `/api/auth/login/` | POST | Publico com throttle | Publico | Sem tenant antes do login | Throttle configurado |
| `/api/auth/refresh/` | POST | Refresh token | Usuario autenticado por refresh | Sessao do token | Manual |
| `/api/usuarios/me/` | GET | JWT | Todos | Proprio usuario | Fluxos frontend |
| `/api/usuarios/` | GET | JWT | `alunos.view` | Arena do usuario | Revisao |
| `/api/admin/alunos/` | GET/POST/PATCH/DELETE | JWT | `alunos.manage` | Arena do admin | Revisao |
| `/api/turmas/` | GET | JWT | Todos autenticados | Arena do usuario | Revisao |
| `/api/turmas/minhas/` | GET | JWT | Aluno | Turmas do aluno | Revisao |
| `/api/turmas/{id}/checkin/` | POST | JWT | Aluno matriculado | Turma da arena e aluno vinculado | Revisao |
| `/api/minhas-solicitacoes/` | GET/POST/DELETE | JWT | Aluno | `aluno=request.user` | Revisao |
| `/api/admin/solicitacoes/` | GET/actions | JWT | `alunos.manage` | Arena do admin | Revisao |
| `/api/admin/fila-espera/` | GET/actions | JWT | `alunos.manage` | Arena do admin | Revisao |
| `/api/mensalidades/` | GET | JWT | Aluno | `matricula.aluno=request.user` e arena | `arena.tests` |
| `/api/mensalidades/{id}/pagar/` | POST | JWT | Aluno owner | Propria mensalidade | Revisao |
| `/api/admin/mensalidades/` | GET | JWT | `mensalidades.manage` | Arena do admin | `arena.tests` |
| `/api/admin/mensalidades/{id}/pagar/` | POST | JWT | `mensalidades.manage` | Arena do admin | `arena.tests` |
| `/api/admin/mensalidades/{id}/pendente/` | POST | JWT | `mensalidades.manage` | Arena do admin | `arena.tests` |
| `/api/admin/mensalidades/{id}/atrasar/` | POST | JWT | `mensalidades.manage` | Arena do admin | `arena.tests` |
| `/api/admin/mensalidades/{id}/cancelar/` | POST | JWT | `mensalidades.manage` | Arena do admin | `arena.tests` |
| `/api/reservas-quadra/` | GET/POST | JWT | Aluno ou admin | Admin ve arena; aluno/proprio com `?minhas=1` | `gestao.tests` |
| `/api/reservas-quadra/{id}/cancelar/` | POST | JWT | Owner ou `reservas.manage` | Owner ou arena admin | `gestao.tests` |
| `/api/reservas-quadra/recorrente/` | POST | JWT | `reservas.manage` | Arena do admin | `gestao.tests` |
| `/api/admin/bloqueios-quadra/` | CRUD | JWT | `reservas.manage` | Arena do admin e quadra da arena | `gestao.tests` |
| `/api/admin/faixas-preco-reserva/` | CRUD | JWT | `reservas.manage` | Arena do admin | Revisao |
| `/api/produtos/` | GET | JWT | Todos autenticados | Arena e canal app/ambos | Revisao |
| `/api/vendas/` | GET/POST | JWT | Aluno | `cliente=request.user` e arena | Revisao |
| `/api/admin/vendas/` | GET | JWT | `pedidos.view` | Arena do admin | Revisao |
| `/api/admin/produtos/` | CRUD/actions | JWT | `estoque.manage` | Arena do admin; produto da arena | `gestao.tests` |
| `/api/admin/estoque/lotes/` | GET | JWT | `estoque.view` | Arena do admin | Revisao |
| `/api/admin/estoque/movimentacoes/` | GET | JWT | `estoque.view` | Arena do admin | Revisao |
| `/api/admin/auditoria/` | GET | JWT | `auditoria.view` | Arena do dono | `gestao.tests` |
| `/api/admin/resumo-executivo/` | GET | JWT | `dashboard.view` | Arena do admin | Revisao |
| `/api/schema/`, `/api/docs/` | GET | JWT/public conforme config | Documentacao | Sem dados de negocio | `manage.py check` |

## Regras gerais

- O cliente nunca define a arena efetiva.
- IDs de relacionamento precisam pertencer a arena do usuario autenticado.
- Campos financeiros sensiveis sao alterados por actions auditadas, nao por PATCH direto.
- Ocultar botao no frontend nao substitui permissao no backend.
