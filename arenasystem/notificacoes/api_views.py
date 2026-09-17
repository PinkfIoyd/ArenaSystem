from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Q

from .models import Notificacao, NotificacaoAdmin
from .serializers import NotificacaoAdminSerializer, NotificacaoSerializer
from arena.tenant import get_user_arena
from usuarios.permissions import require_permission


class MinhasNotificacoesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificacaoSerializer

    def get_queryset(self):
        return Notificacao.objects.filter(
            arena=get_user_arena(self.request.user), destinatario=self.request.user,
        )

    @action(detail=True, methods=['post'], url_path='marcar-lida')
    def marcar_lida(self, request, pk=None):
        notificacao = self.get_object()
        notificacao.lida = True
        notificacao.save(update_fields=['lida'])
        return Response({'detail': 'Marcada como lida.'})

    @action(detail=False, methods=['post'], url_path='marcar-todas-lidas')
    def marcar_todas_lidas(self, request):
        self.get_queryset().filter(lida=False).update(lida=True)
        return Response({'detail': 'Todas marcadas como lidas.'})


class AdminNotificacoesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin vê suas notificações.
    GET  /api/admin/notificacoes/
    GET  /api/admin/notificacoes/contador/   ← total não lidas
    POST /api/admin/notificacoes/{id}/marcar-lida/
    POST /api/admin/notificacoes/marcar-todas-lidas/
    """
    serializer_class = NotificacaoAdminSerializer
    permission_classes = [require_permission('dashboard.view')]

    def get_queryset(self):
        # Mostra notificações destinadas ao admin atual OU para todos (destinatario null)
        return NotificacaoAdmin.objects.filter(
            arena=get_user_arena(self.request.user)
        ).filter(
            Q(destinatario=self.request.user) | Q(destinatario__isnull=True)
        )

    @action(detail=False, methods=['get'])
    def contador(self, request):
        """Retorna apenas o número de não lidas (para badge)."""
        total = self.get_queryset().filter(lida=False).count()
        return Response({'nao_lidas': total})

    @action(detail=True, methods=['post'], url_path='marcar-lida')
    def marcar_lida(self, request, pk=None):
        notif = self.get_object()
        notif.marcar_como_lida()
        return Response({'detail': 'Marcada como lida.'})

    @action(detail=False, methods=['post'], url_path='marcar-todas-lidas')
    def marcar_todas_lidas(self, request):
        qs = self.get_queryset().filter(lida=False)
        qs.update(lida=True, lida_em=timezone.now())
        return Response({'detail': 'Todas marcadas como lidas.'})
