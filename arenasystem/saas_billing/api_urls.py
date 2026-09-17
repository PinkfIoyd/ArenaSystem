from django.urls import path
from rest_framework.routers import DefaultRouter

from .api_views import (
    SaasPlanAdminViewSet,
    cancel_subscription,
    change_plan,
    current_subscription,
    invoice_receipt,
    invoices,
    mercado_pago_saas_webhook,
    public_plans,
    reactivate_subscription,
    subscription_checkout,
)


router = DefaultRouter()
router.register(r'saas/catalog/plans', SaasPlanAdminViewSet, basename='saas-plan-admin')

urlpatterns = [
    path('saas/plans/', public_plans, name='saas-public-plans'),
    path('saas/webhook/mercado-pago/', mercado_pago_saas_webhook, name='saas-mercado-pago-webhook'),
    path('subscription/', current_subscription, name='current-subscription'),
    path('subscription/checkout/', subscription_checkout, name='subscription-checkout'),
    path('subscription/change-plan/', change_plan, name='subscription-change-plan'),
    path('subscription/cancel/', cancel_subscription, name='subscription-cancel'),
    path('subscription/reactivate/', reactivate_subscription, name='subscription-reactivate'),
    path('subscription/invoices/', invoices, name='subscription-invoices'),
    path('subscription/invoices/<int:invoice_id>/receipt/', invoice_receipt, name='subscription-invoice-receipt'),
] + router.urls

