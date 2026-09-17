from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Usuario
from .serializers import UsuarioSerializer, CadastroAlunoSerializer
from .account_serializers import ProfileUpdateSerializer
from arena.tenant import get_user_arena
from gestao.audit import registrar_auditoria
from .permissions import require_permission
from .throttles import RegisterRateThrottle


class CadastroAlunoView(generics.CreateAPIView):
    """
    Endpoint público para o aluno se cadastrar pelo app.
    POST /api/auth/register/
    """
    queryset = Usuario.objects.none()
    serializer_class = CadastroAlunoSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterRateThrottle]


class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Listar usuários (apenas para staff).
    GET /api/usuarios/
    GET /api/usuarios/me/  ← retorna os dados do usuário logado
    """
    serializer_class = UsuarioSerializer

    def get_queryset(self):
        return Usuario.objects.filter(arena=get_user_arena(self.request.user))

    def get_permissions(self):
        # Endpoint /me/ é acessível por qualquer usuário autenticado
        if self.action == 'me':
            return [permissions.IsAuthenticated()]
        return [require_permission('alunos.view')()]

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Retorna os dados do usuário autenticado."""
        if request.method == 'PATCH':
            previous = {
                field: getattr(request.user, field)
                for field in ('first_name', 'last_name', 'telefone', 'data_nascimento')
            }
            update = ProfileUpdateSerializer(
                request.user, data=request.data, partial=True, context={'request': request},
            )
            update.is_valid(raise_exception=True)
            user = update.save()
            changed = {
                field: getattr(user, field)
                for field in update.validated_data
                if field != 'foto' and previous.get(field) != getattr(user, field)
            }
            if 'foto' in update.validated_data:
                changed['foto'] = 'atualizada' if user.foto else 'removida'
            if changed:
                registrar_auditoria(
                    request, user.arena, 'account.profile_updated', user,
                    anteriores={key: previous.get(key) for key in changed if key != 'foto'},
                    novos=changed,
                )
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
class AdminAlunoViewSet(viewsets.ModelViewSet):
    """
    Admin gerencia alunos.
    GET    /api/admin/alunos/?search=X&status=ativos
    POST   /api/admin/alunos/
    GET    /api/admin/alunos/{id}/
    PATCH  /api/admin/alunos/{id}/
    DELETE /api/admin/alunos/{id}/         → desativa (soft delete)
    POST   /api/admin/alunos/{id}/ativar/  → reativa
    """
    permission_classes = [require_permission('alunos.manage')]

    def get_queryset(self):
        qs = Usuario.objects.filter(tipo='aluno', arena=get_user_arena(self.request.user))

        # Filtro de status
        status_filtro = self.request.query_params.get('status', 'ativos')
        if status_filtro == 'ativos':
            qs = qs.filter(is_active=True)
        elif status_filtro == 'inativos':
            qs = qs.filter(is_active=False)
        # 'todos' não filtra

        # Busca por texto
        search = self.request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(cpf__icontains=search) |
                Q(telefone__icontains=search)
            )

        return qs.order_by('-date_joined')

    def get_serializer_class(self):
        from .serializers import AdminAlunoSerializer, CriarAlunoSerializer
        if self.action == 'create':
            return CriarAlunoSerializer
        return AdminAlunoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        aluno = serializer.save()

        # Retorna info do aluno + senha temporária (se aplicável)
        from .serializers import AdminAlunoSerializer
        response_serializer = AdminAlunoSerializer(aluno)
        response_data = response_serializer.data
        response_data['senha_temporaria'] = getattr(aluno, '_senha_temporaria', None)

        return Response(response_data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Em vez de deletar, desativa."""
        aluno = self.get_object()
        aluno.is_active = False
        aluno.save()
        return Response(
            {'detail': f'Aluno {aluno.username} desativado.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def ativar(self, request, pk=None):
        aluno = self.get_object()
        aluno.is_active = True
        aluno.save()
        return Response({'detail': f'Aluno {aluno.username} reativado.'})
