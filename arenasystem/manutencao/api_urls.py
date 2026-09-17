from rest_framework.routers import DefaultRouter

from .api_views import AdminManutencaoViewSet

router = DefaultRouter()
router.register(r'admin/manutencoes', AdminManutencaoViewSet, basename='admin-manutencao')

urlpatterns = router.urls
