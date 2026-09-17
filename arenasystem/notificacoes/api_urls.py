from rest_framework.routers import DefaultRouter
from .api_views import AdminNotificacoesViewSet, MinhasNotificacoesViewSet

router = DefaultRouter()
router.register(r'admin/notificacoes', AdminNotificacoesViewSet, basename='admin-notificacao')
router.register(r'notificacoes', MinhasNotificacoesViewSet, basename='minha-notificacao')

urlpatterns = router.urls
