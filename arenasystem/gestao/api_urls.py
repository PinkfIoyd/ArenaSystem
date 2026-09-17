from django.urls import path
from rest_framework.routers import DefaultRouter

from .api_views import (
    AuditLogViewSet,
    BloqueioQuadraViewSet,
    ContaFinanceiraViewSet,
    ContratoMatriculaViewSet,
    FaixaPrecoReservaViewSet,
    LeadViewSet,
    ReservaQuadraViewSet,
    resumo_executivo,
)

router = DefaultRouter()
router.register('reservas-quadra', ReservaQuadraViewSet, basename='reservas-quadra')
router.register('admin/bloqueios-quadra', BloqueioQuadraViewSet, basename='admin-bloqueios-quadra')
router.register('admin/faixas-preco-reserva', FaixaPrecoReservaViewSet, basename='admin-faixas-preco-reserva')
router.register('admin/auditoria', AuditLogViewSet, basename='admin-auditoria')
router.register('admin/leads', LeadViewSet, basename='admin-leads')
router.register('admin/contas-financeiras', ContaFinanceiraViewSet, basename='admin-contas-financeiras')
router.register('admin/contratos', ContratoMatriculaViewSet, basename='admin-contratos')

urlpatterns = [
    path('admin/resumo-executivo/', resumo_executivo, name='resumo-executivo'),
]

urlpatterns += router.urls
