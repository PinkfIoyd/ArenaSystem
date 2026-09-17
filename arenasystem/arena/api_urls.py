from django.urls import path
from rest_framework.routers import DefaultRouter
from .api_views import (
    AdminMensalidadeViewSet,
    AdminPlanoViewSet,
    AdminQuadraViewSet,
    QuadraViewSet,
    PlanoViewSet,
    MatriculaViewSet,
    MensalidadeViewSet,
    SaasArenaViewSet,
    arena_atual,
    arenas_publicas,
    mercado_pago_webhook,
)
from .onboarding_views import (
    complete_onboarding, import_students, onboarding_status, save_onboarding_step,
    student_import_template,
)
from .access_api import AccessVisitViewSet, AdminAccessVisitViewSet, access_settings, current_access_state

router = DefaultRouter()
router.register(r'quadras', QuadraViewSet, basename='quadra')
router.register(r'planos', PlanoViewSet, basename='plano')
router.register(r'matriculas', MatriculaViewSet, basename='matricula')
router.register(r'mensalidades', MensalidadeViewSet, basename='mensalidade')
router.register(r'admin/mensalidades', AdminMensalidadeViewSet, basename='admin-mensalidade')
router.register(r'admin/planos', AdminPlanoViewSet, basename='admin-plano')
router.register(r'admin/quadras', AdminQuadraViewSet, basename='admin-quadra')
router.register(r'saas/arenas', SaasArenaViewSet, basename='saas-arena')
router.register(r'access-visits', AccessVisitViewSet, basename='access-visit')
router.register(r'admin/access-visits', AdminAccessVisitViewSet, basename='admin-access-visit')

urlpatterns = [
    path('arena/atual/', arena_atual, name='arena-atual'),
    path('access/state/', current_access_state, name='access-state'),
    path('admin/access/settings/', access_settings, name='access-settings'),
    path('arenas/publicas/', arenas_publicas, name='arenas-publicas'),
    path('mercado-pago/webhook/', mercado_pago_webhook, name='mercado-pago-webhook'),
    path('onboarding/', onboarding_status, name='onboarding-status'),
    path('onboarding/steps/<slug:step>/', save_onboarding_step, name='onboarding-save-step'),
    path('onboarding/complete/', complete_onboarding, name='onboarding-complete'),
    path('onboarding/import-students/template/', student_import_template, name='student-import-template'),
    path('onboarding/import-students/', import_students, name='student-import'),
] + router.urls
