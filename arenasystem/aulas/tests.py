from datetime import time

from django.test import TestCase
from rest_framework.test import APIClient

from arena.models import Arena, Quadra
from aulas.models import SolicitacaoMatricula, Turma
from usuarios.models import Usuario


class AulasTenantSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.arena_a = Arena.objects.create(nome='Arena A', slug='arena-a')
        self.arena_b = Arena.objects.create(nome='Arena B', slug='arena-b')
        self.quadra_a = Quadra.objects.create(arena=self.arena_a, nome='Quadra A')
        self.quadra_b = Quadra.objects.create(arena=self.arena_b, nome='Quadra B')
        self.admin_a = Usuario.objects.create_user(username='admin-a', password='x', tipo='admin', papel='dono', arena=self.arena_a, is_staff=True)
        self.prof_a = Usuario.objects.create_user(username='prof-a', password='x', tipo='professor', arena=self.arena_a)
        self.prof_b = Usuario.objects.create_user(username='prof-b', password='x', tipo='professor', arena=self.arena_b)
        self.aluno_a = Usuario.objects.create_user(username='aluno-a', password='x', tipo='aluno', arena=self.arena_a)
        self.aluno_b = Usuario.objects.create_user(username='aluno-b', password='x', tipo='aluno', arena=self.arena_b)
        self.turma_a = Turma.objects.create(arena=self.arena_a, professor=self.prof_a, quadra=self.quadra_a, nome='Turma A', dias_semana='seg', horario=time(8, 0), vagas=8)
        self.turma_b = Turma.objects.create(arena=self.arena_b, professor=self.prof_b, quadra=self.quadra_b, nome='Turma B', dias_semana='seg', horario=time(8, 0), vagas=8)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_admin_nao_ve_solicitacao_de_outra_arena(self):
        SolicitacaoMatricula.objects.create(arena=self.arena_b, aluno=self.aluno_b, turma=self.turma_b)
        self.auth(self.admin_a)

        response = self.client.get('/api/admin/solicitacoes/')
        payload = response.data.get('results', response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload, [])

    def test_admin_nao_cria_turma_com_quadra_de_outra_arena(self):
        self.auth(self.admin_a)
        response = self.client.post('/api/admin/turmas/', {
            'nome': 'Turma cruzada',
            'professor': self.prof_a.id,
            'quadra': self.quadra_b.id,
            'dias_semana': 'ter',
            'horario': '09:00',
            'vagas': 8,
            'ativa': True,
        }, format='json')

        self.assertEqual(response.status_code, 400)

    def test_aluno_nao_acessa_turma_de_outra_arena_por_id(self):
        self.auth(self.aluno_a)
        response = self.client.get(f'/api/turmas/{self.turma_b.id}/')

        self.assertEqual(response.status_code, 404)
