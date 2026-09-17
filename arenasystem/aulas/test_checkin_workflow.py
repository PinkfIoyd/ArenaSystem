from datetime import datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from arena.models import Arena, Matricula, Mensalidade, Plano, Quadra
from notificacoes.models import Notificacao
from usuarios.models import Usuario
from saas_billing.models import SaasPlan, SaasSubscription

from .checkin_services import CheckInDomainError, expire_pending_checkins, request_mobile_checkin
from .models import CheckIn, Turma


DAY_CODES = ['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom']


class MobileCheckInWorkflowTests(TestCase):
    def setUp(self):
        self.arena = Arena.objects.create(nome='Arena Teste', slug='arena-checkin', status_assinatura='ativa')
        self.other_arena = Arena.objects.create(nome='Outra Arena', slug='outra-checkin', status_assinatura='ativa')
        self.court = Quadra.objects.create(arena=self.arena, nome='Central')
        self.professor = Usuario.objects.create_user(
            username='prof-checkin', tipo='professor', papel='professor', arena=self.arena,
        )
        self.other_professor = Usuario.objects.create_user(
            username='other-prof-checkin', tipo='professor', papel='professor', arena=self.arena,
        )
        self.student = Usuario.objects.create_user(username='student-checkin', tipo='aluno', papel='aluno', arena=self.arena)
        self.other_student = Usuario.objects.create_user(username='other-student-checkin', tipo='aluno', papel='aluno', arena=self.other_arena)
        self.reception = Usuario.objects.create_user(username='reception-checkin', tipo='funcionario', papel='recepcao', arena=self.arena)
        self.admin = Usuario.objects.create_user(username='admin-checkin', tipo='admin_arena', papel='administrador', arena=self.arena)
        self.plan = Plano.objects.create(arena=self.arena, nome='Plano aluno', valor='100.00', frequencia_semanal=2)
        Matricula.objects.create(
            arena=self.arena, aluno=self.student, plano=self.plan,
            data_inicio=timezone.localdate() - timedelta(days=30), ativa=True,
        )
        local_now = timezone.localtime()
        self.starts_at = local_now.replace(second=0, microsecond=0) + timedelta(hours=1)
        self.turma = Turma.objects.create(
            arena=self.arena, professor=self.professor, quadra=self.court,
            nome='Treino do dia', dias_semana=DAY_CODES[local_now.weekday()],
            horario=self.starts_at.time().replace(tzinfo=None), vagas=20,
        )
        self.turma.alunos.add(self.student)
        self.client = APIClient()

    def aware_at(self, minutes):
        return self.starts_at + timedelta(minutes=minutes)

    def request_at(self, minutes):
        return request_mobile_checkin(self.turma, self.student, now=self.aware_at(minutes))

    def test_window_accepts_exact_boundaries(self):
        first = self.request_at(-20)
        self.assertEqual(first.status, 'pending')
        first.delete()
        second = self.request_at(10)
        self.assertEqual(second.status, 'pending')

    def test_window_rejects_outside_boundaries(self):
        for minutes in (-21, 11):
            with self.subTest(minutes=minutes), self.assertRaises(CheckInDomainError) as raised:
                self.request_at(minutes)
            self.assertEqual(raised.exception.code, 'checkin_window_closed')

    def test_duplicate_does_not_create_another_record(self):
        first = self.request_at(0)
        with self.assertRaises(CheckInDomainError) as raised:
            self.request_at(0)
        self.assertEqual(raised.exception.code, 'checkin_already_requested')
        self.assertEqual(CheckIn.objects.filter(aluno=self.student, turma=self.turma).count(), 1)
        self.assertEqual(raised.exception.extra['checkin_id'], first.id)

    def test_wrong_tenant_and_inactive_enrollment_are_rejected(self):
        self.turma.alunos.add(self.other_student)
        with self.assertRaises(CheckInDomainError) as tenant_error:
            request_mobile_checkin(self.turma, self.other_student, now=self.aware_at(0))
        self.assertEqual(tenant_error.exception.http_status, 403)
        Matricula.objects.filter(aluno=self.student).update(ativa=False)
        with self.assertRaises(CheckInDomainError) as enrollment_error:
            self.request_at(0)
        self.assertEqual(enrollment_error.exception.code, 'inactive_enrollment')

    def test_wrong_weekday_is_rejected(self):
        self.turma.dias_semana = DAY_CODES[(timezone.localdate().weekday() + 1) % 7]
        self.turma.save(update_fields=['dias_semana'])
        with self.assertRaises(CheckInDomainError) as raised:
            self.request_at(0)
        self.assertEqual(raised.exception.code, 'class_not_scheduled')

    def test_financial_policy_warns_or_blocks(self):
        enrollment = Matricula.objects.get(aluno=self.student)
        Mensalidade.objects.create(
            arena=self.arena, matricula=enrollment, mes_referencia=timezone.localdate().replace(day=1),
            valor='100.00', vencimento=timezone.localdate() - timedelta(days=10), status='atrasado',
        )
        allowed = self.request_at(0)
        self.assertTrue(allowed.inadimplente_no_momento)
        allowed.delete()
        self.arena.delinquent_checkin_policy = 'block'
        self.arena.save(update_fields=['delinquent_checkin_policy'])
        with self.assertRaises(CheckInDomainError) as blocked:
            self.request_at(0)
        self.assertEqual(blocked.exception.code, 'student_payment_overdue')

    def create_pending(self):
        return self.request_at(0)

    def test_reception_confirms_and_student_is_notified(self):
        checkin = self.create_pending()
        self.client.force_authenticate(self.reception)
        response = self.client.post(f'/api/admin/checkins/{checkin.id}/confirm/')
        self.assertEqual(response.status_code, 200)
        checkin.refresh_from_db()
        self.assertEqual(checkin.status, 'confirmed')
        self.assertEqual(checkin.validado_por, self.reception)
        self.assertTrue(Notificacao.objects.filter(destinatario=self.student, titulo='Check-in confirmado').exists())

    def test_other_professor_cannot_confirm(self):
        checkin = self.create_pending()
        self.client.force_authenticate(self.other_professor)
        response = self.client.post(f'/api/admin/checkins/{checkin.id}/confirm/')
        self.assertEqual(response.status_code, 404)
        checkin.refresh_from_db()
        self.assertEqual(checkin.status, 'pending')

    def test_bulk_confirmation_only_updates_allowed_pending_items(self):
        checkin = self.create_pending()
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/admin/checkins/bulk-confirm/', {'ids': [checkin.id]}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['confirmed'], 1)
        checkin.refresh_from_db()
        self.assertEqual(checkin.status, 'confirmed')

    def test_rejection_requires_reason(self):
        checkin = self.create_pending()
        self.client.force_authenticate(self.reception)
        missing = self.client.post(f'/api/admin/checkins/{checkin.id}/reject/', {}, format='json')
        self.assertEqual(missing.status_code, 400)
        accepted = self.client.post(
            f'/api/admin/checkins/{checkin.id}/reject/', {'reason': '  Turma incorreta\n  '}, format='json',
        )
        self.assertEqual(accepted.status_code, 200)
        checkin.refresh_from_db()
        self.assertEqual(checkin.status, 'rejected')
        self.assertNotIn('\n', checkin.motivo)

    def test_lazy_expiration_is_idempotent(self):
        old_date = timezone.localdate() - timedelta(days=1)
        checkin = CheckIn.objects.create(
            arena=self.arena, aluno=self.student, turma=self.turma, data=old_date,
            horario=time(10), presente=False, status='pending', origem='mobile',
        )
        self.assertEqual(expire_pending_checkins(), 1)
        self.assertEqual(expire_pending_checkins(), 0)
        checkin.refresh_from_db()
        self.assertEqual(checkin.status, 'expired')
        self.assertEqual(Notificacao.objects.filter(destinatario=self.student, titulo='Check-in expirado').count(), 1)

    def test_student_cannot_access_operational_queue(self):
        self.client.force_authenticate(self.student)
        response = self.client.get('/api/admin/checkins/today/')
        self.assertEqual(response.status_code, 403)

    def test_student_api_returns_202_then_duplicate_conflict(self):
        self.turma.horario = timezone.localtime().time().replace(second=0, microsecond=0, tzinfo=None)
        self.turma.save(update_fields=['horario'])
        self.client.force_authenticate(self.student)
        created = self.client.post(f'/api/turmas/{self.turma.id}/checkin/')
        duplicate = self.client.post(f'/api/turmas/{self.turma.id}/checkin/')
        self.assertEqual(created.status_code, 202)
        self.assertEqual(created.data['checkin']['status'], 'pending')
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.data['code'], 'checkin_already_requested')

    def test_manual_checkin_requires_reason(self):
        self.client.force_authenticate(self.reception)
        missing = self.client.post('/api/admin/checkins/manual/', {
            'turma': self.turma.id, 'aluno': self.student.id,
        }, format='json')
        accepted = self.client.post('/api/admin/checkins/manual/', {
            'turma': self.turma.id, 'aluno': self.student.id, 'reason': 'Contingencia na recepcao',
        }, format='json')
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(accepted.data['origem'], 'manual')

    def test_suspended_subscription_returns_402(self):
        saas_plan = SaasPlan.objects.create(code='checkin-plan', name='Check-in Plan')
        SaasSubscription.objects.create(arena=self.arena, plan=saas_plan, status='suspended')
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/api/turmas/{self.turma.id}/checkin/')
        self.assertEqual(response.status_code, 402)
        self.assertEqual(response.data['code'], 'subscription_inactive')
