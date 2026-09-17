from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from arena.models import Arena, Matricula, Mensalidade, Plano
from arena.tenant import get_default_arena
from gestao.models import AuditLog
from usuarios.models import Usuario


class MensalidadeSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.arena = Arena.objects.create(nome='Arena A', slug='arena-a')
        self.outra_arena = Arena.objects.create(nome='Arena B', slug='arena-b')
        self.admin = Usuario.objects.create_user(
            username='admin',
            password='x',
            tipo='admin',
            papel='financeiro',
            arena=self.arena,
            is_staff=True,
        )
        self.aluno = Usuario.objects.create_user(username='aluno', password='x', tipo='aluno', papel='aluno', arena=self.arena)
        self.outro_aluno = Usuario.objects.create_user(username='outro', password='x', tipo='aluno', papel='aluno', arena=self.outra_arena)
        self.plano = Plano.objects.create(arena=self.arena, nome='Mensal', valor=Decimal('200.00'), frequencia_semanal=2)
        self.matricula = Matricula.objects.create(arena=self.arena, aluno=self.aluno, plano=self.plano, data_inicio=date(2026, 1, 10))
        self.mensalidade = Mensalidade.objects.create(
            arena=self.arena,
            matricula=self.matricula,
            mes_referencia=date(2026, 8, 1),
            valor=Decimal('200.00'),
            vencimento=date(2026, 8, 10),
            status='pendente',
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_cancelamento_manual_e_auditado(self):
        self.auth(self.admin)
        response = self.client.post(f'/api/admin/mensalidades/{self.mensalidade.id}/cancelar/')
        self.mensalidade.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.mensalidade.status, 'cancelada')
        self.assertIsNone(self.mensalidade.data_pagamento)
        self.assertTrue(AuditLog.objects.filter(arena=self.arena, acao='mensalidade.cancelada_manual').exists())

    def test_filtro_admin_inclui_canceladas(self):
        self.mensalidade.status = 'cancelada'
        self.mensalidade.save(update_fields=['status'])
        self.auth(self.admin)

        response = self.client.get('/api/admin/mensalidades/?status=cancelada')
        payload = response.data.get('results', response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['status'], 'cancelada')

    def test_patch_nao_altera_campos_financeiros_sensiveis(self):
        self.mensalidade.vencimento = timezone.localdate() + timedelta(days=1)
        self.mensalidade.save(update_fields=['vencimento'])
        self.auth(self.admin)
        response = self.client.patch(f'/api/admin/mensalidades/{self.mensalidade.id}/', {
            'valor': '1.00',
            'status': 'pago',
            'data_pagamento': timezone.localdate().isoformat(),
        }, format='json')
        self.mensalidade.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.mensalidade.valor, Decimal('200.00'))
        self.assertEqual(self.mensalidade.status, 'pendente')
        self.assertIsNone(self.mensalidade.data_pagamento)

    def test_aluno_nao_ve_mensalidade_de_outra_arena_por_id(self):
        plano_b = Plano.objects.create(arena=self.outra_arena, nome='Mensal B', valor=Decimal('180.00'), frequencia_semanal=2)
        matricula_b = Matricula.objects.create(arena=self.outra_arena, aluno=self.outro_aluno, plano=plano_b, data_inicio=date(2026, 1, 10))
        mensalidade_b = Mensalidade.objects.create(
            arena=self.outra_arena,
            matricula=matricula_b,
            mes_referencia=date(2026, 7, 1),
            valor=Decimal('180.00'),
            vencimento=date(2026, 7, 10),
        )

        self.auth(self.aluno)
        response = self.client.get(f'/api/mensalidades/{mensalidade_b.id}/')

        self.assertEqual(response.status_code, 404)


class SaasTenantContextTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.arena_a = Arena.objects.create(nome='Arena A', slug='saas-arena-a')
        self.arena_b = Arena.objects.create(nome='Arena B', slug='saas-arena-b')
        self.superadmin = Usuario.objects.create_user(
            username='saas-root', password='x', tipo='superadmin_saas', papel='superadmin_saas', is_staff=True,
        )
        self.admin_a = Usuario.objects.create_user(
            username='admin-a-saas', password='x', tipo='admin_arena', papel='dono', arena=self.arena_a, is_staff=True,
        )
        self.aluno_a = Usuario.objects.create_user(username='aluno-a-saas', password='x', tipo='aluno', arena=self.arena_a)
        self.plano_a = Plano.objects.create(arena=self.arena_a, nome='Plano A', valor=Decimal('250.00'), frequencia_semanal=2)
        self.matricula_a = Matricula.objects.create(
            arena=self.arena_a, aluno=self.aluno_a, plano=self.plano_a, data_inicio=date(2026, 1, 1), ativa=True,
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_usuario_comum_nao_seleciona_tenant_por_header(self):
        self.auth(self.admin_a)
        response = self.client.get('/api/arena/atual/', HTTP_X_ARENA_ID=str(self.arena_b.id))
        self.assertEqual(response.status_code, 403)

    def test_superadmin_sem_contexto_nao_recebe_demo(self):
        self.auth(self.superadmin)
        response = self.client.get('/api/arena/atual/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Selecione uma arena', str(response.data))

    @override_settings(DEMO_MODE=False, DEFAULT_ARENA_SLUG='tenant-inexistente')
    def test_ambiente_nao_demo_nao_cria_tenant_automaticamente(self):
        with self.assertRaises(ValidationError):
            get_default_arena()
        self.assertFalse(Arena.objects.filter(slug='tenant-inexistente').exists())

    def test_entrada_e_troca_de_contexto_sao_auditadas(self):
        self.auth(self.superadmin)
        response = self.client.post(
            f'/api/saas/arenas/{self.arena_a.id}/acessar/', {'motivo': ' Suporte\nsolicitado '}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        entrada = AuditLog.objects.get(acao='superadmin.context_entered')
        self.assertEqual(entrada.metadados['motivo'], 'Suporte solicitado')

        response = self.client.post(
            f'/api/saas/arenas/{self.arena_b.id}/acessar/', {'motivo': ''}, format='json',
            HTTP_X_ARENA_ID=str(self.arena_a.id),
        )
        self.assertEqual(response.status_code, 200)
        troca = AuditLog.objects.get(acao='superadmin.context_switched')
        self.assertEqual(troca.metadados['arena_anterior_id'], self.arena_a.id)
        self.assertEqual(troca.arena, self.arena_b)

    def test_requisicao_cross_tenant_grava_rota_status_e_motivo(self):
        self.auth(self.superadmin)
        response = self.client.get(
            '/api/arena/atual/',
            HTTP_X_ARENA_ID=str(self.arena_a.id),
            HTTP_X_ARENA_ACCESS_REASON='Auditoria\ninterna',
            HTTP_X_FRONTEND_ROUTE='/admin/alunos',
        )
        self.assertEqual(response.status_code, 200)
        log = AuditLog.objects.get(acao='superadmin.cross_tenant_access')
        self.assertEqual(log.arena, self.arena_a)
        self.assertEqual(log.metadados['status_code'], 200)
        self.assertEqual(log.metadados['frontend_route'], '/admin/alunos')
        self.assertEqual(log.metadados['motivo'], 'Auditoria interna')
        self.assertNotIn('authorization', str(log.metadados).lower())

    def test_motivo_mascara_segredos(self):
        self.auth(self.superadmin)
        self.client.get(
            '/api/arena/atual/', HTTP_X_ARENA_ID=str(self.arena_a.id),
            HTTP_X_ARENA_ACCESS_REASON='suporte senha=Segredo123 token:abc123',
        )
        log = AuditLog.objects.get(acao='superadmin.cross_tenant_access')
        self.assertNotIn('Segredo123', log.metadados['motivo'])
        self.assertNotIn('abc123', log.metadados['motivo'])
        self.assertIn('[mascarado]', log.metadados['motivo'])

    def test_resumo_isola_metricas_e_exige_superadmin(self):
        self.auth(self.superadmin)
        response = self.client.get(f'/api/saas/arenas/{self.arena_a.id}/resumo/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['alunos']['ativos'], 1)
        self.assertEqual(response.data['arena']['id'], self.arena_a.id)
        self.assertIn('inicio', response.data['periodos']['financeiro'])

        self.auth(self.admin_a)
        denied = self.client.get(f'/api/saas/arenas/{self.arena_a.id}/resumo/')
        self.assertEqual(denied.status_code, 403)

    def test_arena_suspensa_tem_resumo_mas_nao_contexto(self):
        self.arena_b.ativa = False
        self.arena_b.status_assinatura = 'suspensa'
        self.arena_b.save(update_fields=['ativa', 'status_assinatura'])
        self.auth(self.superadmin)
        resumo = self.client.get(f'/api/saas/arenas/{self.arena_b.id}/resumo/')
        acesso = self.client.post(f'/api/saas/arenas/{self.arena_b.id}/acessar/', {'motivo': ''}, format='json')
        self.assertEqual(resumo.status_code, 200)
        self.assertEqual(acesso.status_code, 409)

    def test_criacao_de_arena_admin_e_auditoria_sem_senha(self):
        self.auth(self.superadmin)
        payload = {
            'nome': 'Nova Arena', 'slug': 'nova-arena', 'plano_contratado': 'professional',
            'status_assinatura': 'trial', 'limite_alunos': 200, 'limite_quadras': 5, 'limite_admins': 4,
            'cor_primaria': '#112233', 'cor_secundaria': '#AABBCC', 'cor_fundo': '#FFFFFF', 'cor_texto': '#111111',
            'admin_nome': 'Maria', 'admin_sobrenome': 'Gestora', 'admin_email': 'maria@nova.demo',
            'admin_senha': 'Strong!Pass-2026-Demo', 'admin_senha_confirm': 'Strong!Pass-2026-Demo',
        }
        response = self.client.post('/api/saas/arenas/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        arena = Arena.objects.get(slug='nova-arena')
        self.assertTrue(Usuario.objects.filter(arena=arena, email='maria@nova.demo', papel='dono').exists())
        log = AuditLog.objects.get(arena=arena, acao='saas.arena_created')
        self.assertNotIn('senha', str(log.valores_novos).lower())
        self.assertNotIn('password', str(log.metadados).lower())

    def test_criacao_de_academia_com_modulos_iniciais(self):
        self.auth(self.superadmin)
        payload = {
            'nome': 'Academia Hibrida', 'slug': 'academia-hibrida', 'tipo_negocio': 'academia',
            'plano_contratado': 'starter', 'status_assinatura': 'trial',
            'limite_alunos': 150, 'limite_quadras': 4, 'limite_admins': 3,
            'admin_nome': 'Ana', 'admin_sobrenome': 'Gestora', 'admin_email': 'ana@academia.demo',
            'admin_senha': 'Strong!Pass-2026-Academia',
            'admin_senha_confirm': 'Strong!Pass-2026-Academia',
            'operational_settings': {
                'classes_enabled': True,
                'open_access_enabled': True,
                'reservations_enabled': False,
                'store_enabled': False,
                'open_access_validation': 'reception',
                'open_access_pending_minutes': 8,
            },
        }

        response = self.client.post('/api/saas/arenas/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        arena = Arena.objects.get(slug='academia-hibrida')
        self.assertEqual(arena.tipo_negocio, 'academia')
        self.assertEqual(arena.get_operational_settings().access_mode, 'hybrid')
        self.assertEqual(arena.get_operational_settings().open_access_pending_minutes, 8)
        self.assertEqual(response.data['arena']['terminologia']['pessoa_plural'], 'membros')

    def test_criacao_e_atomica_quando_dados_iniciais_falham(self):
        self.auth(self.superadmin)
        self.client.raise_request_exception = False
        payload = {
            'nome': 'Arena Rollback', 'slug': 'arena-rollback',
            'admin_nome': 'Admin', 'admin_sobrenome': '', 'admin_email': 'rollback@arena.demo',
            'admin_senha': 'Strong!Pass-2026-Demo', 'admin_senha_confirm': 'Strong!Pass-2026-Demo',
        }
        with patch('arena.api_views.criar_dados_iniciais_arena', side_effect=RuntimeError('falha controlada')):
            response = self.client.post('/api/saas/arenas/', payload, format='json')
        self.assertEqual(response.status_code, 500)
        self.assertFalse(Arena.objects.filter(slug='arena-rollback').exists())


class OnboardingTests(TestCase):
    def setUp(self):
        from saas_billing.models import SaasPlan, SaasSubscription

        self.arena = Arena.objects.create(
            nome='Arena Onboarding', slug='arena-onboarding', email_contato='contato@onboarding.test',
        )
        plan = SaasPlan.objects.create(
            code='onboarding-plan', name='Onboarding', max_students=10, max_courts=3,
        )
        SaasSubscription.objects.create(arena=self.arena, plan=plan, status='trialing')
        self.owner = Usuario.objects.create_user(
            username='owner-onboarding', password='Password123!', email='owner@onboarding.test',
            tipo='admin_arena', papel='dono', arena=self.arena,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def test_owner_can_save_required_steps_and_complete(self):
        identification = self.client.post('/api/onboarding/steps/identification/', {
            'nome': 'Arena Onboarding', 'email_contato': 'contato@onboarding.test',
            'cor_primaria': '#112233', 'cor_secundaria': '#AABBCC',
        }, format='json')
        hours = self.client.post('/api/onboarding/steps/hours/', {'items': [
            {'weekday': day, 'closed': day == 6, 'opens_at': '07:00', 'closes_at': '22:00'}
            for day in range(7)
        ]}, format='json')
        courts = self.client.post('/api/onboarding/steps/courts/', {
            'items': [{'nome': 'Quadra Principal', 'tipo_areia': 'Branca'}],
        }, format='json')
        modalities = self.client.post('/api/onboarding/steps/modalities/', {
            'items': [{'nome': 'Beach Tennis', 'cor': '#00AA99'}],
        }, format='json')
        completed = self.client.post('/api/onboarding/complete/', {}, format='json')
        self.assertEqual([identification.status_code, hours.status_code, courts.status_code, modalities.status_code], [200] * 4)
        self.assertEqual(completed.status_code, 200)
        self.assertIsNotNone(completed.data['completed_at'])

    def test_non_owner_cannot_change_onboarding(self):
        employee = Usuario.objects.create_user(
            username='employee-onboarding', tipo='funcionario', papel='recepcao', arena=self.arena,
        )
        self.client.force_authenticate(employee)
        response = self.client.post('/api/onboarding/steps/courts/', {'items': [{'nome': 'X'}]}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_csv_dry_run_then_atomic_import(self):
        content = b'first_name,last_name,email,telefone,cpf,data_nascimento,plano,turma\nAna,Silva,ana@csv.test,,,,,\nBruno,Souza,bruno@csv.test,,,,,\n'
        dry_run = self.client.post('/api/onboarding/import-students/', {
            'file': SimpleUploadedFile('students.csv', content, content_type='text/csv'), 'dry_run': 'true',
        }, format='multipart')
        self.assertEqual(dry_run.status_code, 200)
        self.assertEqual(dry_run.data['valid'], 2)
        self.assertFalse(Usuario.objects.filter(arena=self.arena, tipo='aluno').exists())
        with patch('arena.onboarding_views.create_password_reset'):
            committed = self.client.post('/api/onboarding/import-students/', {
                'file': SimpleUploadedFile('students.csv', content, content_type='text/csv'), 'dry_run': 'false',
            }, format='multipart')
        self.assertEqual(committed.status_code, 201)
        self.assertEqual(committed.data['imported'], 2)
        self.assertEqual(Usuario.objects.filter(arena=self.arena, tipo='aluno').count(), 2)
        self.assertTrue(all(not user.has_usable_password() for user in Usuario.objects.filter(arena=self.arena, tipo='aluno')))

    def test_csv_rejects_duplicates_without_partial_write(self):
        content = b'first_name,email\nAna,duplicate@csv.test\nOutra,duplicate@csv.test\n'
        response = self.client.post('/api/onboarding/import-students/', {
            'file': SimpleUploadedFile('duplicate.csv', content, content_type='text/csv'), 'dry_run': 'false',
        }, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Usuario.objects.filter(arena=self.arena, email='duplicate@csv.test').exists())
