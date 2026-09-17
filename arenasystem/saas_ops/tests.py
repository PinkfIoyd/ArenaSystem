from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from arena.models import Arena
from saas_billing.models import SaasPlan, SaasSubscription
from usuarios.models import Usuario

from .models import DataSubjectRequest, LegalDocumentVersion, SupportMessage, SupportTicket


class SaasOperationsTests(TestCase):
    def setUp(self):
        self.arena_a = Arena.objects.create(nome='Arena Ops A', slug='arena-ops-a')
        self.arena_b = Arena.objects.create(nome='Arena Ops B', slug='arena-ops-b')
        plan = SaasPlan.objects.create(
            code='ops', name='Ops', monthly_price=Decimal('100.00'), annual_price=Decimal('1000.00'),
        )
        SaasSubscription.objects.create(arena=self.arena_a, plan=plan, status='active')
        SaasSubscription.objects.create(arena=self.arena_b, plan=plan, status='active')
        self.owner_a = Usuario.objects.create_user(username='ops-owner-a', tipo='admin_arena', papel='dono', arena=self.arena_a)
        self.owner_b = Usuario.objects.create_user(username='ops-owner-b', tipo='admin_arena', papel='dono', arena=self.arena_b)
        self.superadmin = Usuario.objects.create_user(username='ops-super', tipo='superadmin_saas', papel='superadmin_saas', is_superuser=True)
        self.client = APIClient()

    def test_support_tickets_are_tenant_scoped(self):
        SupportTicket.objects.create(arena=self.arena_b, subject='B only', created_by=self.owner_b)
        self.client.force_authenticate(self.owner_a)
        created = self.client.post('/api/support/tickets/', {'subject': 'A only', 'category': 'technical', 'priority': 'high'}, format='json')
        listed = self.client.get('/api/support/tickets/')
        self.assertEqual(created.status_code, 201)
        subjects = [item['subject'] for item in listed.data['results']]
        self.assertEqual(subjects, ['A only'])

    def test_internal_support_notes_are_hidden_from_tenant(self):
        ticket = SupportTicket.objects.create(arena=self.arena_a, subject='Ticket', created_by=self.owner_a)
        SupportMessage.objects.create(ticket=ticket, author=self.superadmin, body='Nota interna', internal=True)
        SupportMessage.objects.create(ticket=ticket, author=self.superadmin, body='Resposta publica', internal=False)
        self.client.force_authenticate(self.owner_a)
        response = self.client.get(f'/api/support/tickets/{ticket.id}/')
        self.assertEqual([message['body'] for message in response.data['messages']], ['Resposta publica'])

    def test_superadmin_can_view_global_ticket_queue(self):
        SupportTicket.objects.create(arena=self.arena_a, subject='A', created_by=self.owner_a)
        SupportTicket.objects.create(arena=self.arena_b, subject='B', created_by=self.owner_b)
        self.client.force_authenticate(self.superadmin)
        response = self.client.get('/api/support/tickets/')
        self.assertEqual(response.data['count'], 2)

    def test_export_request_is_private_and_downloadable(self):
        self.client.force_authenticate(self.owner_a)
        created = self.client.post('/api/privacy/requests/', {'kind': 'export', 'description': ''}, format='json')
        self.assertEqual(created.status_code, 201)
        data_request = DataSubjectRequest.objects.get(id=created.data['id'])
        self.assertTrue(data_request.export_ready)
        response = self.client.get(f'/api/privacy/requests/{data_request.id}/download/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertEqual(response['Cache-Control'], 'no-store, private')
        self.client.force_authenticate(self.owner_b)
        denied = self.client.get(f'/api/privacy/requests/{data_request.id}/download/')
        self.assertEqual(denied.status_code, 404)

    def test_public_legal_api_only_exposes_published_effective_documents(self):
        LegalDocumentVersion.objects.create(
            document_type='privacy', version='published-1', title='Privacidade', content='Conteudo',
            status='published', effective_at=timezone.now(),
        )
        self.client.force_authenticate(None)
        response = self.client.get('/api/legal/documents/')
        titles = [item['title'] for item in response.data['results']]
        self.assertEqual(titles, ['Privacidade'])

    def test_saas_dashboard_returns_decimal_strings(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.get('/api/saas/operations/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['mrr'], '200.00')
        self.assertIsInstance(response.data['revenue_received'], str)

