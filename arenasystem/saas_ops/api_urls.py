from django.urls import path
from rest_framework.routers import DefaultRouter

from .api_views import (
    DataSubjectRequestViewSet, FeatureBlockViewSet, LegalDocumentViewSet,
    OperationalTaskViewSet, SupportTicketViewSet, accept_legal_document,
    account_health_list, saas_operations_dashboard,
)

router = DefaultRouter()
router.register(r'support/tickets', SupportTicketViewSet, basename='support-ticket')
router.register(r'privacy/requests', DataSubjectRequestViewSet, basename='privacy-request')
router.register(r'legal/documents', LegalDocumentViewSet, basename='legal-document')
router.register(r'saas/operations/feature-blocks', FeatureBlockViewSet, basename='feature-block')
router.register(r'saas/operations/tasks', OperationalTaskViewSet, basename='operational-task')

urlpatterns = [
    path('legal/consents/', accept_legal_document, name='legal-consent'),
    path('saas/operations/dashboard/', saas_operations_dashboard, name='saas-operations-dashboard'),
    path('saas/operations/health/', account_health_list, name='saas-account-health'),
] + router.urls

