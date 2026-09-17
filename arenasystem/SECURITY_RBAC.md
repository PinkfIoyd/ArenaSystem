# Matriz de permissoes RBAC

O backend usa o campo `Usuario.papel` e a funcao `tem_permissao` em
`usuarios.permissions` como fonte de verdade. Quando `papel` estiver vazio,
o sistema preserva compatibilidade:

- `superuser`, `tipo=admin` ou `is_staff`: `dono`
- `tipo=professor`: `professor`
- demais usuarios: `aluno`

## Papeis

| Papel | Acesso |
| --- | --- |
| Dono | Acesso completo aos dados da propria arena. |
| Recepcao | Alunos, solicitacoes, fila, turmas, reservas, pedidos e check-in operacional. |
| Financeiro | Mensalidades, contas financeiras e visao executiva financeira. |
| Professor | Suas proprias turmas, alunos dessas turmas e presenca dessas turmas. |
| Estoque | Produtos, lotes e movimentacoes de estoque. |
| Aluno | Dados proprios: turmas, reservas, mensalidades, pedidos e check-in. |

## Permissoes tecnicas

| Permissao | Dono | Recepcao | Financeiro | Professor | Estoque | Aluno |
| --- | --- | --- | --- | --- | --- | --- |
| `alunos.view` / `alunos.manage` | Sim | Sim | Nao | Apenas escopo proprio de turma | Nao | Nao |
| `reservas.view` / `reservas.manage` | Sim | Sim | Ver | Nao | Nao | Apenas proprias |
| `mensalidades.view` / `mensalidades.manage` | Sim | Nao | Sim | Nao | Nao | Apenas proprias |
| `financeiro.view` / `financeiro.manage` | Sim | Nao | Sim | Nao | Nao | Nao |
| `estoque.view` / `estoque.manage` | Sim | Nao | Nao | Nao | Sim | Nao |
| `pedidos.view` / `pedidos.manage` | Sim | Sim | Nao | Nao | Ver | Apenas proprios |
| `turmas.manage` | Sim | Sim | Nao | Nao | Nao | Nao |
| `auditoria.view` | Sim | Nao | Nao | Nao | Nao | Nao |
| `dashboard.view` | Sim | Nao | Sim | Nao | Nao | Nao |

## Regras de tenant

- A arena efetiva vem do usuario autenticado no backend.
- O frontend nao e fonte de verdade para tenant, usuario responsavel ou ownership.
- Recursos por ID sao buscados em querysets ja filtrados por arena.
- Relacionamentos enviados no payload, como quadra em reservas, devem pertencer a arena atual.
- Auditoria sempre e filtrada pela arena do usuario.

## Auditoria

Eventos persistidos em `gestao.AuditLog` nao devem conter senhas, tokens,
segredos ou credenciais. A leitura da auditoria e restrita ao papel `dono`.
