import hashlib
import hmac
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from arena.models import Arena, Matricula, Plano
from usuarios.models import Usuario

from .models import SaasInvoice, SaasPlan, SaasSubscription, SaasWebhookEvent
from .services import (
    calculate_prorated_upgrade,
    reconcile_subscription_lifecycle,
    sanitize_provider_payload,
    verify_mercado_pago_signature,
)


class SaasBillingTests(TestCase):
    def setUp(self):
        self.arena = Arena.objects.create(nome='Arena A', slug='arena-a', status_assinatura='ativa')
        self.plan = SaasPlan.objects.create(
            code='pro-test', name='Pro Test', published=True,
            monthly_price=Decimal('200.00'), annual_price=Decimal('2000.00'),
            max_admins=5, max_professors=20, max_students=200, max_courts=8,
        )
        now = timezone.now()
        self.subscription = SaasSubscription.objects.create(
            arena=self.arena, plan=self.plan, status='active',
            current_period_start=now - timedelta(days=15),
            current_period_end=now + timedelta(days=15),
        )
        self.owner = Usuario.objects.create_user(
            username='owner', password='Password123!', email='owner@example.test',
            tipo='admin_arena', papel='dono', arena=self.arena,
        )
        self.finance = Usuario.objects.create_user(
            username='finance', password='Password123!', email='finance@example.test',
            tipo='funcionario', papel='financeiro', arena=self.arena,
        )
        self.client = APIClient()

    def test_public_catalog_only_returns_published_priced_plans(self):
        SaasPlan.objects.create(code='draft', name='Draft')
        response = self.client.get(reverse('saas-public-plans'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['code'] for item in response.data], ['pro-test'])
        self.assertEqual(response.data[0]['monthly_price'], '200.00')

    def test_current_subscription_is_tenant_scoped(self):
        other_arena = Arena.objects.create(nome='Arena B', slug='arena-b')
        SaasSubscription.objects.create(arena=other_arena, plan=self.plan)
        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse('current-subscription'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.subscription.id)

    def test_only_owner_can_change_plan(self):
        target = SaasPlan.objects.create(
            code='enterprise-test', name='Enterprise', published=True,
            monthly_price=Decimal('400.00'), annual_price=Decimal('4000.00'),
        )
        self.client.force_authenticate(self.finance)
        response = self.client.post(reverse('subscription-change-plan'), {'plan_id': target.id})
        self.assertEqual(response.status_code, 403)

    def test_downgrade_rejects_usage_above_limit(self):
        student_plan = Plano.objects.create(arena=self.arena, nome='Aluno', valor=100, frequencia_semanal=1)
        for index in range(2):
            student = Usuario.objects.create_user(username=f'student-{index}', tipo='aluno', arena=self.arena)
            Matricula.objects.create(
                arena=self.arena, aluno=student, plano=student_plan,
                data_inicio=timezone.localdate(), ativa=True,
            )
        target = SaasPlan.objects.create(
            code='small-test', name='Small', published=True,
            monthly_price=Decimal('100.00'), annual_price=Decimal('1000.00'), max_students=1,
        )
        self.client.force_authenticate(self.owner)
        response = self.client.post(reverse('subscription-change-plan'), {'plan_id': target.id})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'plan_usage_incompatible')
        self.assertEqual(response.data['resources']['students']['usage'], 2)

    def test_proration_uses_remaining_fraction(self):
        target = SaasPlan.objects.create(
            code='higher', name='Higher', monthly_price=Decimal('300.00'), annual_price=Decimal('3000.00'),
        )
        amount = calculate_prorated_upgrade(self.subscription, target, timezone.now())
        self.assertTrue(Decimal('49.90') <= amount <= Decimal('50.10'))

    def test_trial_moves_to_past_due_then_suspended(self):
        self.subscription.status = 'trialing'
        self.subscription.trial_ends_at = timezone.now() - timedelta(minutes=1)
        self.subscription.save(update_fields=['status', 'trial_ends_at'])
        changes = reconcile_subscription_lifecycle()
        self.subscription.refresh_from_db()
        self.assertEqual(changes['past_due'], 1)
        self.assertEqual(self.subscription.status, 'past_due')
        self.subscription.grace_ends_at = timezone.now() - timedelta(minutes=1)
        self.subscription.save(update_fields=['grace_ends_at'])
        reconcile_subscription_lifecycle()
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'suspended')
        self.assertFalse(self.subscription.arena.ativa)

    def test_suspended_subscription_blocks_operational_api_but_allows_billing(self):
        self.subscription.status = 'suspended'
        self.subscription.save(update_fields=['status'])
        token = str(RefreshToken.for_user(self.owner).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        blocked = self.client.get('/api/admin/alunos/')
        allowed = self.client.get(reverse('current-subscription'))
        self.assertEqual(blocked.status_code, 402)
        self.assertEqual(blocked.data['code'], 'subscription_inactive')
        self.assertEqual(allowed.status_code, 200)

    def test_signature_validation_matches_documented_manifest(self):
        secret = 'test-secret'
        timestamp = '1704908010'
        request_id = 'request-123'
        data_id = 'ABC123'
        manifest = f'id:{data_id.lower()};request-id:{request_id};ts:{timestamp};'
        signature = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
        header = f'ts={timestamp},v1={signature}'
        self.assertTrue(verify_mercado_pago_signature(header, request_id, data_id, secret))
        self.assertFalse(verify_mercado_pago_signature(header, request_id, 'different', secret))

    @override_settings(MERCADO_PAGO_SAAS_WEBHOOK_SECRET='webhook-secret')
    def test_invalid_webhook_is_rejected_and_payload_is_sanitized(self):
        response = self.client.post(
            '/api/saas/webhook/mercado-pago/?data.id=123&type=payment',
            {'id': 'evt-invalid', 'type': 'payment', 'data': {'id': '123'}, 'access_token': 'never-store'},
            format='json', HTTP_X_SIGNATURE='ts=1,v1=invalid', HTTP_X_REQUEST_ID='req-invalid',
        )
        self.assertEqual(response.status_code, 401)
        event = SaasWebhookEvent.objects.get(event_id='evt-invalid')
        self.assertEqual(event.payload['access_token'], '[mascarado]')
        self.assertNotIn('never-store', str(event.payload))

    @override_settings(MERCADO_PAGO_SAAS_WEBHOOK_SECRET='webhook-secret')
    @patch('saas_billing.api_views.provider_request')
    def test_valid_webhook_applies_paid_upgrade_once(self, provider_request_mock):
        target = SaasPlan.objects.create(
            code='upgrade-target', name='Upgrade', published=True,
            monthly_price=Decimal('400.00'), annual_price=Decimal('4000.00'),
        )
        invoice = SaasInvoice.objects.create(
            arena=self.arena, subscription=self.subscription, kind='upgrade', amount=Decimal('100.00'),
            metadata={'target_plan_id': target.id},
        )
        provider_request_mock.return_value = {
            'id': 'payment-123', 'status': 'approved', 'external_reference': invoice.external_reference,
        }
        timestamp = '1704908010'
        request_id = 'req-valid'
        manifest = f'id:payment-123;request-id:{request_id};ts:{timestamp};'
        signature = hmac.new(b'webhook-secret', manifest.encode(), hashlib.sha256).hexdigest()
        url = '/api/saas/webhook/mercado-pago/?data.id=payment-123&type=payment'
        payload = {'id': 'evt-valid', 'type': 'payment', 'data': {'id': 'payment-123'}}
        first = self.client.post(
            url, payload, format='json', HTTP_X_SIGNATURE=f'ts={timestamp},v1={signature}', HTTP_X_REQUEST_ID=request_id,
        )
        second = self.client.post(
            url, payload, format='json', HTTP_X_SIGNATURE=f'ts={timestamp},v1={signature}', HTTP_X_REQUEST_ID=request_id,
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        invoice.refresh_from_db()
        self.subscription.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(self.subscription.plan_id, target.id)
        self.assertEqual(SaasWebhookEvent.objects.filter(event_id='evt-valid').count(), 1)

    def test_sanitizer_redacts_nested_financial_secrets(self):
        sanitized = sanitize_provider_payload({'payer': {'card_token_id': 'secret'}, 'status': 'ok'})
        self.assertEqual(sanitized['payer']['card_token_id'], '[mascarado]')

