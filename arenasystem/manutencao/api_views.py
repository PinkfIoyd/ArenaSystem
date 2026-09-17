from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Manutencao
from .serializers import ManutencaoSerializer
from arena.tenant import get_user_arena
from usuarios.permissions import require_permission


class AdminManutencaoViewSet(viewsets.ModelViewSet):
    serializer_class = ManutencaoSerializer
    permission_classes = [require_permission('reservas.manage')]

    def get_queryset(self):
        qs = Manutencao.objects.filter(arena=get_user_arena(self.request.user)).select_related('quadra')
        quadra_id = self.request.query_params.get('quadra')
        status_filtro = self.request.query_params.get('status')
        if quadra_id:
            qs = qs.filter(quadra_id=quadra_id)
        if status_filtro:
            qs = qs.filter(status=status_filtro)
        return qs

    def perform_create(self, serializer):
        arena = get_user_arena(self.request.user)
        quadra = serializer.validated_data['quadra']
        if quadra.arena_id != arena.id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Quadra nao pertence a arena atual.'})
        serializer.save(arena=arena)

    @action(detail=True, methods=['post'])
    def concluir(self, request, pk=None):
        manutencao = self.get_object()
        manutencao.status = 'concluida'
        manutencao.data_conclusao = timezone.localdate()
        manutencao.save(update_fields=['status', 'data_conclusao'])
        return Response({'detail': 'Manutencao marcada como concluida.'})
