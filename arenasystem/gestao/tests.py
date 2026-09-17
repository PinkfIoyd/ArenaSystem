from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from arena.models import Arena, Quadra
from gestao.audit import registrar_auditoria
from gestao.models import AuditLog, BloqueioQuadra, FaixaPrecoReserva, ReservaQuadra
from usuarios.models import Usuario


class GestaoSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.arena_a = Arena.objects.create(nome='Arena A', slug='arena-a')
        self.arena_b = Arena.objects.create(nome='Arena B', slug='arena-b')
        self.quadra_a = Quadra.objects.create(arena=self.arena_a, nome='Quadra A', ativa=True)
        self.quadra_b = Quadra.objects.create(arena=self.arena_b, nome='Quadra B', ativa=True)
        self.dono = Usuario.objects.create_user(username='dono', password='x', tipo='admin', papel='dono', arena=self.arena_a, is_staff=True)
        self.recepcao = Usuario.objects.create_user(username='recepcao', password='x', tipo='admin', papel='recepcao', arena=self.arena_a, is_staff=True)
        self.financeiro = Usuario.objects.create_user(username='financeiro', password='x', tipo='admin', papel='financeiro', arena=self.arena_a, is_staff=True)
        self.aluno = Usuario.objects.create_user(username='aluno', password='x', tipo='aluno', papel='aluno', arena=self.arena_a)
        self.outro_aluno = Usuario.objects.create_user(username='aluno-b', password='x', tipo='aluno', papel='aluno', arena=self.arena_b)
        self.data = date.today() + timedelta(days=1)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_recepcao_nao_acessa_auditoria(self):
        self.auth(self.recepcao)
        response = self.client.get('/api/admin/auditoria/')
        self.assertEqual(response.status_code, 403)

    def test_dono_acessa_auditoria_da_propria_arena(self):
        AuditLog.objects.create(arena=self.arena_a, usuario=self.dono, acao='teste', entidade_tipo='ReservaQuadra')
        AuditLog.objects.create(arena=self.arena_b, usuario=self.outro_aluno, acao='teste', entidade_tipo='ReservaQuadra')
        self.auth(self.dono)
        response = self.client.get('/api/admin/auditoria/')
        self.assertEqual(response.status_code, 200)
        payload = response.data.get('results', response.data)
        self.assertEqual(len(payload), 1)

    def test_financeiro_pode_contas_mas_nao_estoque(self):
        self.auth(self.financeiro)
        conta = self.client.post('/api/admin/contas-financeiras/', {
            'tipo': 'pagar',
            'descricao': 'Conta teste',
            'valor': '100.00',
            'vencimento': self.data.isoformat(),
        }, format='json')
        self.assertEqual(conta.status_code, 201)
        estoque = self.client.get('/api/admin/produtos/')
        self.assertEqual(estoque.status_code, 403)

    def test_nao_cria_reserva_com_quadra_de_outra_arena(self):
        self.auth(self.aluno)
        response = self.client.post('/api/reservas-quadra/', {
            'quadra': self.quadra_b.id,
            'data': self.data.isoformat(),
            'hora_inicio': '10:00',
            'hora_fim': '11:00',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_acesso_direto_reserva_outra_arena_retorna_404(self):
        reserva = ReservaQuadra.objects.create(
            arena=self.arena_b,
            quadra=self.quadra_b,
            aluno=self.outro_aluno,
            cliente_nome='Aluno B',
            data=self.data,
            hora_inicio=time(10, 0),
            hora_fim=time(11, 0),
        )
        self.auth(self.aluno)
        response = self.client.get(f'/api/reservas-quadra/{reserva.id}/')
        self.assertEqual(response.status_code, 404)

    def test_admin_pode_filtrar_apenas_proprias_reservas_na_area_publica(self):
        ReservaQuadra.objects.create(
            arena=self.arena_a,
            quadra=self.quadra_a,
            aluno=self.dono,
            cliente_nome='Dono',
            data=self.data,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
        )
        ReservaQuadra.objects.create(
            arena=self.arena_a,
            quadra=self.quadra_a,
            aluno=self.aluno,
            cliente_nome='Aluno',
            data=self.data,
            hora_inicio=time(10, 0),
            hora_fim=time(11, 0),
        )

        self.auth(self.dono)
        todas = self.client.get('/api/reservas-quadra/')
        minhas = self.client.get('/api/reservas-quadra/?minhas=1')

        payload_todas = todas.data.get('results', todas.data)
        payload_minhas = minhas.data.get('results', minhas.data)

        self.assertEqual(todas.status_code, 200)
        self.assertEqual(minhas.status_code, 200)
        self.assertEqual(len(payload_todas), 2)
        self.assertEqual(len(payload_minhas), 1)
        self.assertEqual(payload_minhas[0]['aluno'], self.dono.id)

    def test_admin_criando_reserva_publica_vincula_ao_proprio_usuario(self):
        self.auth(self.dono)
        response = self.client.post('/api/reservas-quadra/?minhas=1', {
            'quadra': self.quadra_a.id,
            'data': self.data.isoformat(),
            'hora_inicio': '12:00',
            'hora_fim': '13:00',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['aluno'], self.dono.id)

    def test_reserva_conflito_e_adjacente(self):
        self.auth(self.aluno)
        payload = {
            'quadra': self.quadra_a.id,
            'data': self.data.isoformat(),
            'hora_inicio': '10:00',
            'hora_fim': '11:00',
        }
        primeira = self.client.post('/api/reservas-quadra/', payload, format='json')
        self.assertEqual(primeira.status_code, 201)

        conflito = self.client.post('/api/reservas-quadra/', {
            **payload,
            'hora_inicio': '10:30',
            'hora_fim': '11:30',
        }, format='json')
        self.assertEqual(conflito.status_code, 400)

        adjacente = self.client.post('/api/reservas-quadra/', {
            **payload,
            'hora_inicio': '11:00',
            'hora_fim': '12:00',
        }, format='json')
        self.assertEqual(adjacente.status_code, 201)

    def test_bloqueio_impede_reserva_e_audita(self):
        self.auth(self.recepcao)
        bloqueio = self.client.post('/api/admin/bloqueios-quadra/', {
            'quadra': self.quadra_a.id,
            'data': self.data.isoformat(),
            'hora_inicio': '14:00',
            'hora_fim': '15:00',
            'motivo': 'Chuva',
            'categoria': 'chuva',
        }, format='json')
        self.assertEqual(bloqueio.status_code, 201)
        self.assertTrue(AuditLog.objects.filter(arena=self.arena_a, acao='bloqueio.criado').exists())

        self.auth(self.aluno)
        reserva = self.client.post('/api/reservas-quadra/', {
            'quadra': self.quadra_a.id,
            'data': self.data.isoformat(),
            'hora_inicio': '14:30',
            'hora_fim': '15:30',
        }, format='json')
        self.assertEqual(reserva.status_code, 400)

    def test_recorrencia_rollback_em_conflito(self):
        ReservaQuadra.objects.create(
            arena=self.arena_a,
            quadra=self.quadra_a,
            cliente_nome='Existente',
            data=self.data + timedelta(days=7),
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
        )
        self.auth(self.recepcao)
        response = self.client.post('/api/reservas-quadra/recorrente/', {
            'quadra': self.quadra_a.id,
            'cliente_nome': 'Recorrente',
            'data_inicial': self.data.isoformat(),
            'hora_inicio': '08:00',
            'hora_fim': '09:00',
            'ocorrencias': 3,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ReservaQuadra.objects.filter(arena=self.arena_a, cliente_nome='Recorrente').count(), 0)

    def test_preco_por_faixa_calculado_no_backend(self):
        FaixaPrecoReserva.objects.create(
            arena=self.arena_a,
            quadra=self.quadra_a,
            dia_semana=self.data.weekday(),
            hora_inicio=time(18, 0),
            hora_fim=time(22, 0),
            valor=Decimal('180.00'),
        )
        self.auth(self.aluno)
        response = self.client.post('/api/reservas-quadra/', {
            'quadra': self.quadra_a.id,
            'data': self.data.isoformat(),
            'hora_inicio': '18:00',
            'hora_fim': '19:00',
            'valor': '1.00',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['valor'], '180.00')

    def test_auditoria_mascara_dados_sensiveis_aninhados(self):
        registrar_auditoria(
            None,
            self.arena_a,
            'seguranca.teste',
            self.quadra_a,
            novos={
                'nome': 'Teste',
                'senha': 'segredo',
                'perfil': {'access_token': 'abc123'},
                'eventos': [{'authorization': 'Bearer segredo'}],
            },
            metadados={'refresh': 'xyz'},
        )

        log = AuditLog.objects.get(acao='seguranca.teste')
        self.assertEqual(log.valores_novos['senha'], '[mascarado]')
        self.assertEqual(log.valores_novos['perfil']['access_token'], '[mascarado]')
        self.assertEqual(log.valores_novos['eventos'][0]['authorization'], '[mascarado]')
        self.assertEqual(log.metadados['refresh'], '[mascarado]')
