from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from gestao.models import AuditLog
from saas_billing.models import SaasPlan, SaasSubscription
from usuarios.models import Usuario

from .access_services import AccessDomainError, expire_access_visits, request_access_visit
from .models import (
    AccessIntegrationEvent, AccessVisit, Arena, ArenaBusinessHours, Matricula,
    Mensalidade, PlanAccessWindow, Plano,
)


class OpenAccessWorkflowTests(TestCase):
    def setUp(self):
        self.arena = Arena.objects.create(
            nome='Academia Teste', slug='academia-acesso', tipo_negocio='academia',
            status_assinatura='ativa',
        )
        self.other_arena = Arena.objects.create(nome='Outra Unidade', slug='outra-unidade')
        self.settings = self.arena.get_operational_settings()
        self.today = timezone.localdate()
        self.now = timezone.make_aware(datetime.combine(self.today, time(12, 0)))
        ArenaBusinessHours.objects.create(
            arena=self.arena, weekday=self.today.weekday(), opens_at=time(6), closes_at=time(22),
        )
        self.plan = Plano.objects.create(
            arena=self.arena, nome='Livre', valor='129.90', frequencia_semanal=0,
            tipo_acesso='open_access',
        )
        PlanAccessWindow.objects.create(
            plano=self.plan, weekday=self.today.weekday(), starts_at=time(7), ends_at=time(21),
        )
        self.member = Usuario.objects.create_user(
            username='member-access', tipo='aluno', papel='aluno', arena=self.arena,
        )
        self.reception = Usuario.objects.create_user(
            username='reception-access', tipo='funcionario', papel='recepcao', arena=self.arena,
        )
        self.professor = Usuario.objects.create_user(
            username='professor-access', tipo='professor', papel='professor', arena=self.arena,
        )
        self.membership = Matricula.objects.create(
            arena=self.arena, aluno=self.member, plano=self.plan,
            data_inicio=self.today - timedelta(days=10), ativa=True,
        )
        self.client = APIClient()

    def request_as(self, user, method, path, data=None):
        self.client.force_authenticate(user)
        with patch('arena.access_services.timezone.now', return_value=self.now):
            return getattr(self.client, method)(path, data or {}, format='json')

    def test_business_type_defaults_and_dynamic_vocabulary(self):
        self.assertTrue(self.settings.classes_enabled)
        self.assertTrue(self.settings.open_access_enabled)
        self.assertFalse(self.settings.reservations_enabled)
        self.assertFalse(self.settings.store_enabled)
        self.assertEqual(self.settings.access_mode, 'hybrid')
        response = self.request_as(self.member, 'get', '/api/arena/atual/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['terminologia']['pessoa_plural'], 'membros')
        self.assertEqual(response.data['operational_settings']['access_mode'], 'hybrid')

    def test_member_requests_reception_confirms_and_member_checks_out(self):
        requested = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(requested.status_code, 202)
        visit_id = requested.data['visit']['public_id']
        self.assertEqual(AccessVisit.objects.get(public_id=visit_id).status, 'pending')

        confirmed = self.request_as(self.reception, 'post', f'/api/admin/access-visits/{visit_id}/confirm/')
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.data['status'], 'confirmed')
        self.assertTrue(AccessIntegrationEvent.objects.filter(visit__public_id=visit_id, event_type='visit.confirmed').exists())

        checked_out = self.request_as(self.member, 'post', f'/api/access-visits/{visit_id}/check-out/')
        self.assertEqual(checked_out.status_code, 200)
        self.assertEqual(checked_out.data['status'], 'checked_out')
        self.assertEqual(checked_out.data['checkout_origem'], 'member')
        self.assertTrue(AuditLog.objects.filter(arena=self.arena, acao='access.checked_out').exists())

    def test_automatic_validation_returns_created(self):
        self.settings.open_access_validation = 'automatic'
        self.settings.save(update_fields=['open_access_validation'])
        response = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['visit']['status'], 'confirmed')

    def test_duplicate_and_tenant_isolation(self):
        first = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(first.status_code, 202)
        duplicate = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.data['code'], 'access_already_open')

        outsider = Usuario.objects.create_user(username='outsider-access', tipo='aluno', papel='aluno', arena=self.other_arena)
        response = self.request_as(outsider, 'post', '/api/access-visits/check-in/')
        self.assertNotEqual(response.status_code, 201)
        self.assertFalse(AccessVisit.objects.filter(aluno=outsider, arena=self.arena).exists())

    def test_plan_hours_feature_and_active_membership_are_backend_barriers(self):
        early = self.now.replace(hour=6, minute=59)
        with self.assertRaises(AccessDomainError) as outside:
            request_access_visit(self.member, self.arena, now=early)
        self.assertEqual(outside.exception.code, 'access_not_allowed_by_plan')

        self.settings.open_access_enabled = False
        self.settings.save(update_fields=['open_access_enabled'])
        disabled = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(disabled.status_code, 403)
        self.assertEqual(disabled.data['code'], 'feature_disabled')

        self.settings.open_access_enabled = True
        self.settings.save(update_fields=['open_access_enabled'])
        self.membership.ativa = False
        self.membership.save(update_fields=['ativa'])
        inactive = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(inactive.status_code, 403)
        self.assertEqual(inactive.data['code'], 'inactive_enrollment')

    def test_access_window_has_inclusive_start_and_exclusive_end(self):
        at_start = request_access_visit(self.member, self.arena, now=self.now.replace(hour=7))
        self.assertEqual(at_start.status, 'pending')
        at_start.delete()
        with self.assertRaises(AccessDomainError) as ended:
            request_access_visit(self.member, self.arena, now=self.now.replace(hour=21))
        self.assertEqual(ended.exception.code, 'access_not_allowed_by_plan')

    def test_delinquency_warns_or_blocks(self):
        Mensalidade.objects.create(
            arena=self.arena, matricula=self.membership, mes_referencia=self.today.replace(day=1),
            valor='129.90', vencimento=self.today - timedelta(days=10), status='atrasado',
        )
        allowed = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(allowed.status_code, 202)
        self.assertTrue(allowed.data['visit']['inadimplente_no_momento'])
        AccessVisit.objects.all().delete()
        self.arena.delinquent_checkin_policy = 'block'
        self.arena.save(update_fields=['delinquent_checkin_policy'])
        blocked = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.data['code'], 'student_payment_overdue')

    def test_confirmed_visits_consume_limit_and_rejections_do_not(self):
        self.plan.limite_acessos_dia = 1
        self.plan.save(update_fields=['limite_acessos_dia'])
        visit = request_access_visit(self.member, self.arena, now=self.now)
        self.request_as(self.reception, 'post', f'/api/admin/access-visits/{visit.public_id}/confirm/')
        self.request_as(self.member, 'post', f'/api/access-visits/{visit.public_id}/check-out/')
        with self.assertRaises(AccessDomainError) as reached:
            request_access_visit(self.member, self.arena, now=self.now + timedelta(minutes=2))
        self.assertEqual(reached.exception.code, 'access_limit_reached')

    def test_pending_expiration_and_automatic_closing_are_idempotent(self):
        pending = request_access_visit(self.member, self.arena, now=self.now)
        result = expire_access_visits(now=self.now + timedelta(minutes=11), arena=self.arena)
        pending.refresh_from_db()
        self.assertEqual(result['expired'], 1)
        self.assertEqual(pending.status, 'expired')
        self.assertEqual(expire_access_visits(now=self.now + timedelta(minutes=11), arena=self.arena)['expired'], 0)

        self.settings.open_access_validation = 'automatic'
        self.settings.save(update_fields=['open_access_validation'])
        confirmed = request_access_visit(self.member, self.arena, now=self.now + timedelta(minutes=12))
        result = expire_access_visits(now=self.now.replace(hour=22), arena=self.arena)
        confirmed.refresh_from_db()
        self.assertEqual(result['checked_out'], 1)
        self.assertEqual(confirmed.status, 'checked_out')
        self.assertEqual(confirmed.checkout_origem, 'automatic')

    def test_professor_cannot_manage_free_access(self):
        response = self.request_as(self.professor, 'get', '/api/admin/access-visits/today/')
        self.assertEqual(response.status_code, 403)

    def test_suspended_saas_subscription_returns_payment_required(self):
        saas_plan = SaasPlan.objects.create(code='test-access', name='Test', max_students=10, max_courts=2)
        SaasSubscription.objects.create(arena=self.arena, plan=saas_plan, status='suspended')
        response = self.request_as(self.member, 'post', '/api/access-visits/check-in/')
        self.assertEqual(response.status_code, 402)
        self.assertEqual(response.data['code'], 'subscription_inactive')


class MemberPlanApiTests(TestCase):
    def setUp(self):
        self.arena = Arena.objects.create(nome='Academia Plano', slug='academia-plano', tipo_negocio='academia')
        self.owner = Usuario.objects.create_user(username='owner-plan', tipo='admin_arena', papel='dono', arena=self.arena)
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def test_create_hybrid_plan_with_non_overlapping_windows(self):
        response = self.client.post('/api/admin/planos/', {
            'nome': 'Completo', 'valor': '199.90', 'frequencia_semanal': 3, 'tipo_acesso': 'hybrid',
            'limite_acessos_dia': 1,
            'janelas_acesso': [
                {'weekday': 0, 'starts_at': '06:00', 'ends_at': '12:00'},
                {'weekday': 0, 'starts_at': '13:00', 'ends_at': '22:00'},
            ],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Plano.objects.get().janelas_acesso.count(), 2)

    def test_overlapping_windows_are_rejected_atomically(self):
        response = self.client.post('/api/admin/planos/', {
            'nome': 'Invalido', 'valor': '99.90', 'frequencia_semanal': 0, 'tipo_acesso': 'open_access',
            'janelas_acesso': [
                {'weekday': 0, 'starts_at': '06:00', 'ends_at': '12:00'},
                {'weekday': 0, 'starts_at': '11:00', 'ends_at': '18:00'},
            ],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Plano.objects.exists())
