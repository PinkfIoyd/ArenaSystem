from datetime import time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from arena.models import Matricula, Quadra
from arena.tenant import get_default_arena
from gestao.models import ContaFinanceira, ContratoMatricula, Lead, ReservaQuadra
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Cria dados demo para CRM, reservas, financeiro e contratos.'

    def handle(self, *args, **options):
        if not settings.DEMO_MODE:
            raise CommandError('seed_gestao exige DEMO_MODE=True.')
        arena = get_default_arena()
        hoje = timezone.localdate()
        admin = Usuario.objects.filter(arena=arena, tipo='admin').first()
        quadras = list(Quadra.objects.filter(arena=arena, ativa=True))
        alunos = list(Usuario.objects.filter(arena=arena, tipo='aluno')[:6])

        leads = [
            ('Marina Duarte', 'Beach Tennis', 'instagram', 'novo', Decimal('290.00'), hoje),
            ('Rafael Pontes', 'Futevolei', 'whatsapp', 'contato', Decimal('290.00'), hoje + timedelta(days=1)),
            ('Luiza Brandao', 'Volei de Praia', 'indicacao', 'experimental', Decimal('420.00'), hoje + timedelta(days=2)),
            ('Pedro Nascimento', 'Funcional', 'balcao', 'negociacao', Decimal('180.00'), hoje + timedelta(days=3)),
            ('Camila Farias', 'Beach Tennis', 'site', 'perdido', Decimal('290.00'), None),
            ('Andre Lopes', 'Volei de Praia', 'instagram', 'ganho', Decimal('420.00'), None),
        ]
        for nome, modalidade, origem, etapa, valor, contato in leads:
            Lead.objects.update_or_create(
                arena=arena,
                nome=nome,
                defaults={
                    'telefone': '(21) 99999-0000',
                    'email': f'{nome.lower().replace(" ", ".")}@demo.com',
                    'modalidade_interesse': modalidade,
                    'origem': origem,
                    'etapa': etapa,
                    'valor_potencial': valor,
                    'proximo_contato': contato,
                    'motivo_perda': 'Achou caro no momento.' if etapa == 'perdido' else '',
                    'observacoes': 'Lead ficticio para demonstracao comercial.',
                    'responsavel': admin,
                },
            )

        contas = [
            ('pagar', 'Conta de luz da arena', 'Infraestrutura', 'Concessionaria', Decimal('1840.00'), hoje + timedelta(days=4), 'aberta'),
            ('pagar', 'Reposicao de areia', 'Manutencao', 'Fornecedor de areia', Decimal('3200.00'), hoje + timedelta(days=12), 'aberta'),
            ('pagar', 'Compra de bebidas', 'Estoque', 'Distribuidora Costa Verde', Decimal('980.00'), hoje - timedelta(days=2), 'vencida'),
            ('receber', 'Pacote empresarial - turma funcional', 'Planos especiais', 'Empresa parceira', Decimal('2400.00'), hoje + timedelta(days=8), 'aberta'),
            ('receber', 'Locacao fixa de quadra', 'Reserva', 'Grupo Noturno', Decimal('1200.00'), hoje + timedelta(days=5), 'aberta'),
        ]
        for tipo, descricao, categoria, fornecedor, valor, vencimento, status in contas:
            ContaFinanceira.objects.update_or_create(
                arena=arena,
                tipo=tipo,
                descricao=descricao,
                defaults={
                    'categoria': categoria,
                    'fornecedor': fornecedor,
                    'valor': valor,
                    'vencimento': vencimento,
                    'status': status,
                    'criado_por': admin,
                },
            )

        if quadras:
            reservas = [
                (quadras[0], alunos[0] if alunos else None, hoje + timedelta(days=1), time(18, 0), time(19, 0), Decimal('120.00'), 'confirmada'),
                (quadras[0], alunos[1] if len(alunos) > 1 else None, hoje + timedelta(days=2), time(20, 0), time(21, 30), Decimal('180.00'), 'pendente'),
                (quadras[-1], alunos[2] if len(alunos) > 2 else None, hoje + timedelta(days=3), time(9, 0), time(10, 0), Decimal('100.00'), 'confirmada'),
            ]
            for quadra, aluno, data, inicio, fim, valor, status in reservas:
                ReservaQuadra.objects.update_or_create(
                    arena=arena,
                    quadra=quadra,
                    data=data,
                    hora_inicio=inicio,
                    hora_fim=fim,
                    defaults={
                        'aluno': aluno,
                        'cliente_nome': aluno.get_full_name() or aluno.username if aluno else 'Cliente avulso',
                        'cliente_telefone': getattr(aluno, 'telefone', '') if aluno else '',
                        'valor': valor,
                        'status': status,
                        'observacoes': 'Reserva demo.',
                        'criado_por': admin,
                    },
                )

        texto_base = (
            'Contrato de prestacao de servicos esportivos. O aluno declara ciencia '
            'das regras de frequencia, pagamentos, reposicoes e cancelamento da arena.'
        )
        for matricula in Matricula.objects.filter(arena=arena, ativa=True)[:8]:
            ContratoMatricula.objects.update_or_create(
                arena=arena,
                matricula=matricula,
                defaults={'texto': texto_base, 'status': 'aceito' if matricula.aluno.username.endswith(('ana', 'carla')) else 'pendente'},
            )

        self.stdout.write(self.style.SUCCESS('Dados avancados de gestao criados/atualizados.'))
