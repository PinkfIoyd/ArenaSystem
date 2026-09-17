from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from loja.models import Categoria, Fornecedor, LoteEstoque, Produto
from arena.tenant import get_default_arena


class Command(BaseCommand):
    help = 'Cria produtos padrao de estoque para balcao e loja.'

    def handle(self, *args, **options):
        if not settings.DEMO_MODE:
            raise CommandError('seed_estoque exige DEMO_MODE=True.')
        hoje = timezone.localdate()
        arena = get_default_arena()
        vestuario, _ = Categoria.objects.get_or_create(arena=arena, nome='Vestuario')
        bebidas, _ = Categoria.objects.get_or_create(arena=arena, nome='Bebidas')
        comidas, _ = Categoria.objects.get_or_create(arena=arena, nome='Comidas')

        fornecedores = {
            'distribuidora': Fornecedor.objects.update_or_create(
            nome='Distribuidora Costa Verde',
            arena=arena,
                defaults={'contato': 'Marcos', 'telefone': '(21) 99999-0101', 'ativo': True},
            )[0],
            'padaria': Fornecedor.objects.update_or_create(
            nome='Padaria Parceira da Arena',
            arena=arena,
                defaults={'contato': 'Renata', 'telefone': '(21) 99999-0202', 'ativo': True},
            )[0],
            'uniformes': Fornecedor.objects.update_or_create(
            nome='Confecção Sport Prime',
            arena=arena,
                defaults={'contato': 'Juliana', 'telefone': '(21) 99999-0303', 'ativo': True},
            )[0],
        }

        produtos = [
            {
                'categoria': vestuario,
                'fornecedor': fornecedores['uniformes'],
                'nome': 'Uniforme oficial ArenaSystem',
                'descricao': 'Uniforme para alunos e atletas da arena.',
                'sku': 'UNI-OFICIAL',
                'preco': Decimal('120.00'),
                'custo': Decimal('62.00'),
                'estoque': 20,
                'minimo': 3,
                'canal': 'ambos',
                'lote': 'UNI-2026-01',
                'validade': None,
            },
            {
                'categoria': bebidas,
                'fornecedor': fornecedores['distribuidora'],
                'nome': 'Cerveja long neck',
                'descricao': 'Venda exclusiva no balcao.',
                'sku': 'BEB-CERV-LN',
                'preco': Decimal('10.00'),
                'custo': Decimal('5.20'),
                'estoque': 48,
                'minimo': 12,
                'canal': 'balcao',
                'lote': 'CERV-LN-0726',
                'validade': hoje + timedelta(days=70),
            },
            {
                'categoria': bebidas,
                'fornecedor': fornecedores['distribuidora'],
                'nome': 'Cerveja lata',
                'descricao': 'Venda exclusiva no balcao.',
                'sku': 'BEB-CERV-LT',
                'preco': Decimal('8.00'),
                'custo': Decimal('4.10'),
                'estoque': 60,
                'minimo': 12,
                'canal': 'balcao',
                'lote': 'CERV-LT-0726',
                'validade': hoje + timedelta(days=55),
            },
            {
                'categoria': bebidas,
                'fornecedor': fornecedores['distribuidora'],
                'nome': 'Refrigerante lata',
                'descricao': 'Venda exclusiva no balcao.',
                'sku': 'BEB-REFRI-LT',
                'preco': Decimal('6.00'),
                'custo': Decimal('2.80'),
                'estoque': 72,
                'minimo': 18,
                'canal': 'balcao',
                'lote': 'REFRI-LT-0726',
                'validade': hoje + timedelta(days=25),
            },
            {
                'categoria': bebidas,
                'fornecedor': fornecedores['distribuidora'],
                'nome': 'Refrigerante 600ml',
                'descricao': 'Venda exclusiva no balcao.',
                'sku': 'BEB-REFRI-600',
                'preco': Decimal('8.00'),
                'custo': Decimal('3.90'),
                'estoque': 36,
                'minimo': 8,
                'canal': 'balcao',
                'lote': 'REFRI-600-0726',
                'validade': hoje + timedelta(days=42),
            },
            {
                'categoria': comidas,
                'fornecedor': fornecedores['padaria'],
                'nome': 'Salgado',
                'descricao': 'Salgados variados com preco unico.',
                'sku': 'COM-SALGADO',
                'preco': Decimal('7.00'),
                'custo': Decimal('3.20'),
                'estoque': 30,
                'minimo': 8,
                'canal': 'balcao',
                'lote': 'SALG-SEMANA',
                'validade': hoje + timedelta(days=3),
            },
        ]

        for dados in produtos:
            produto, _ = Produto.objects.update_or_create(
                arena=arena,
                nome=dados['nome'],
                defaults={
                    'categoria': dados['categoria'],
                    'fornecedor': dados['fornecedor'],
                    'descricao': dados['descricao'],
                    'sku': dados['sku'],
                    'preco': dados['preco'],
                    'custo_unitario': dados['custo'],
                    'estoque': dados['estoque'],
                    'estoque_minimo': dados['minimo'],
                    'canal': dados['canal'],
                    'ativo': True,
                    'is_aluguel': False,
                },
            )
            LoteEstoque.objects.update_or_create(
                produto=produto,
                arena=arena,
                codigo_lote=dados['lote'],
                defaults={
                    'quantidade_inicial': dados['estoque'],
                    'quantidade_atual': dados['estoque'],
                    'custo_unitario': dados['custo'],
                    'validade': dados['validade'],
                    'fornecedor': dados['fornecedor'],
                },
            )

        self.stdout.write(self.style.SUCCESS('Produtos, fornecedores e lotes de estoque criados/atualizados.'))
