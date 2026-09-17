from rest_framework.routers import DefaultRouter
from django.urls import path
from .api_views import (
    TurmaViewSet, CheckInViewSet,
    MinhasSolicitacoesViewSet,
    AdminSolicitacoesViewSet,
    AdminFilaEsperaViewSet,
    AdminTurmaViewSet, AdminCheckInViewSet, MobileHomeView,
)

router = DefaultRouter()
router.register(r'turmas', TurmaViewSet, basename='turma')
router.register(r'checkins', CheckInViewSet, basename='checkin')
router.register(r'minhas-solicitacoes', MinhasSolicitacoesViewSet, basename='minha-solicitacao')

# Endpoints administrativos
router.register(r'admin/solicitacoes', AdminSolicitacoesViewSet, basename='admin-solicitacao')
router.register(r'admin/fila-espera', AdminFilaEsperaViewSet, basename='admin-fila')
router.register(r'admin/turmas', AdminTurmaViewSet, basename='admin-turma')
router.register(r'admin/checkins', AdminCheckInViewSet, basename='admin-checkin')

urlpatterns = [path('mobile/home/', MobileHomeView.as_view(), name='mobile-home')] + router.urls
