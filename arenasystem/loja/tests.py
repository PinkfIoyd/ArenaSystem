from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from arena.models import Arena
from loja.models import Categoria, Produto, Venda
from usuarios.models import Usuario


class LojaTenantSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.arena_a = Arena.objects.create(nome='Arena A', slug='arena-a')
        self.arena_b = Arena.objects.create(nome='Arena B', slug='arena-b')
        self.aluno_a = Usuario.objects.create_user(username='aluno-a', password='x', tipo='aluno', arena=self.arena_a)
        self.aluno_b = Usuario.objects.create_user(username='aluno-b', password='x', tipo='aluno', arena=self.arena_b)
        self.admin_a = Usuario.objects.create_user(username='admin-a', password='x', tipo='admin', papel='estoque', arena=self.arena_a, is_staff=True)
        self.categoria_a = Categoria.objects.create(arena=self.arena_a, nome='Uniforme')
        self.categoria_b = Categoria.objects.create(arena=self.arena_b, nome='Uniforme B')
        self.produto_a = Produto.objects.create(
            arena=self.arena_a,
            categoria=self.categoria_a,
            nome='Camisa A',
            preco=Decimal('59.90'),
            estoque=5,
            canal='app',
            ativo=True,
        )
        self.produto_b = Produto.objects.create(
            arena=self.arena_b,
            categoria=self.categoria_b,
            nome='Camisa B',
            preco=Decimal('69.90'),
            estoque=5,
            canal='app',
            ativo=True,
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_aluno_nao_compra_produto_de_outra_arena(self):
        self.auth(self.aluno_a)
        response = self.client.post('/api/vendas/', {
            'observacoes': '',
            'itens': [{'produto': self.produto_b.id, 'quantidade': 1}],
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Venda.objects.filter(arena=self.arena_a, itens__produto=self.produto_b).exists())

    def test_admin_nao_cria_produto_com_categoria_de_outra_arena(self):
        self.auth(self.admin_a)
        response = self.client.post('/api/admin/produtos/', {
            'categoria': self.categoria_b.id,
            'nome': 'Produto cruzado',
            'preco': '10.00',
            'estoque': 1,
            'canal': 'app',
        }, format='json')

        self.assertEqual(response.status_code, 400)

    def test_aluno_lista_apenas_produtos_da_propria_arena(self):
        self.auth(self.aluno_a)
        response = self.client.get('/api/produtos/')
        payload = response.data.get('results', response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in payload], [self.produto_a.id])
