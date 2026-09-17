from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from arena.models import Matricula, Mensalidade, Plano, Quadra
from arena.tenant import get_default_arena
from aulas.models import CheckIn, FilaEspera, SolicitacaoMatricula, Turma
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Cria dados ficticios para demonstrar turmas, alunos, check-ins e mensalidades.'

    def handle(self, *args, **options):
        if not settings.DEMO_MODE:
            raise CommandError('seed_demo exige DEMO_MODE=True.')
        self.demo_password = settings.DEMO_ADMIN_PASSWORD
        try:
            validate_password(self.demo_password)
        except ValidationError as exc:
            raise CommandError(f'DEMO_ADMIN_PASSWORD insegura: {" ".join(exc.messages)}') from exc
        hoje = timezone.localdate()
        self.arena = get_default_arena()
        primeiro_dia_mes = hoje.replace(day=1)
        mes_passado = (primeiro_dia_mes - timedelta(days=1)).replace(day=1)
        dois_meses_atras = (mes_passado - timedelta(days=1)).replace(day=1)

        quadras = {
            'areia_1': self._quadra('Quadra Areia 1', 'Areia fina'),
            'areia_2': self._quadra('Quadra Areia 2', 'Areia compacta'),
            'funcional': self._quadra('Espaco Funcional', 'Piso emborrachado'),
        }

        planos = {
            'mensal_1x': self._plano('Demo Mensal 1x semana', Decimal('180.00'), 1),
            'mensal_2x': self._plano('Demo Mensal 2x semana', Decimal('290.00'), 2),
            'livre': self._plano('Demo Livre modalidades', Decimal('420.00'), 4),
        }

        self._usuario('demo.admin', 'Admin', 'Arena', 'admin', '2199001-1000')

        professores = {
            'lara': self._usuario('demo.prof.lara', 'Lara', 'Menezes', 'professor'),
            'rafa': self._usuario('demo.prof.rafa', 'Rafa', 'Oliveira', 'professor'),
            'bia': self._usuario('demo.prof.bia', 'Bia', 'Campos', 'professor'),
            'thiago': self._usuario('demo.prof.thiago', 'Thiago', 'Rocha', 'professor'),
        }

        alunos = {
            'ana': self._usuario('demo.ana', 'Ana', 'Costa', 'aluno', '2199001-1001'),
            'bruno': self._usuario('demo.bruno', 'Bruno', 'Lima', 'aluno', '2199001-1002'),
            'carla': self._usuario('demo.carla', 'Carla', 'Nunes', 'aluno', '2199001-1003'),
            'diego': self._usuario('demo.diego', 'Diego', 'Santos', 'aluno', '2199001-1004'),
            'elisa': self._usuario('demo.elisa', 'Elisa', 'Martins', 'aluno', '2199001-1005'),
            'fabio': self._usuario('demo.fabio', 'Fabio', 'Pereira', 'aluno', '2199001-1006'),
            'gi': self._usuario('demo.gi', 'Giovana', 'Barros', 'aluno', '2199001-1007'),
            'hugo': self._usuario('demo.hugo', 'Hugo', 'Ramos', 'aluno', '2199001-1008'),
            'ines': self._usuario('demo.ines', 'Ines', 'Almeida', 'aluno', '2199001-1009'),
            'joao': self._usuario('demo.joao', 'Joao', 'Ferreira', 'aluno', '2199001-1010'),
            'kelly': self._usuario('demo.kelly', 'Kelly', 'Moura', 'aluno', '2199001-1011'),
            'leo': self._usuario('demo.leo', 'Leo', 'Azevedo', 'aluno', '2199001-1012'),
            'maria': self._usuario('demo.maria', 'Maria', 'Teixeira', 'aluno', '2199001-1013'),
            'nando': self._usuario('demo.nando', 'Nando', 'Reis', 'aluno', '2199001-1014'),
            'olivia': self._usuario('demo.olivia', 'Olivia', 'Dias', 'aluno', '2199001-1015'),
            'paulo': self._usuario('demo.paulo', 'Paulo', 'Viana', 'aluno', '2199001-1016'),
        }

        turmas = {
            'volei_manha': self._turma('Demo Volei de Praia - Manha', professores['lara'], quadras['areia_1'], 'seg,qua', time(7, 0), 8),
            'volei_noite': self._turma('Demo Volei de Praia - Noite', professores['lara'], quadras['areia_2'], 'ter,qui', time(19, 0), 8),
            'funcional': self._turma('Demo Funcional na Areia', professores['rafa'], quadras['funcional'], 'seg,qua,sex', time(6, 30), 10),
            'futevolei': self._turma('Demo Futevolei Intermediario', professores['thiago'], quadras['areia_1'], 'ter,qui', time(20, 0), 8),
            'beachtennis': self._turma('Demo Beach Tennis Iniciantes', professores['bia'], quadras['areia_2'], 'sab', time(9, 0), 6),
        }

        matriculados = {
            'volei_manha': ['ana', 'bruno', 'carla', 'diego', 'elisa'],
            'volei_noite': ['fabio', 'gi', 'hugo', 'ines', 'joao'],
            'funcional': ['ana', 'kelly', 'leo', 'maria', 'nando', 'olivia'],
            'futevolei': ['bruno', 'diego', 'fabio', 'hugo', 'paulo'],
            'beachtennis': ['carla', 'elisa', 'gi', 'joao', 'maria', 'leo'],
        }

        for turma_key, aluno_keys in matriculados.items():
            turma = turmas[turma_key]
            turma.alunos.set([alunos[key] for key in aluno_keys])

        plano_por_aluno = {
            'ana': 'livre',
            'bruno': 'mensal_2x',
            'carla': 'mensal_2x',
            'diego': 'mensal_2x',
            'elisa': 'mensal_2x',
            'fabio': 'mensal_2x',
            'gi': 'mensal_2x',
            'hugo': 'mensal_2x',
            'ines': 'mensal_1x',
            'joao': 'mensal_2x',
            'kelly': 'mensal_1x',
            'leo': 'mensal_2x',
            'maria': 'mensal_2x',
            'nando': 'mensal_1x',
            'olivia': 'mensal_1x',
            'paulo': 'mensal_1x',
        }

        matriculas = {}
        for aluno_key, plano_key in plano_por_aluno.items():
            matriculas[aluno_key], _ = Matricula.objects.update_or_create(
                arena=self.arena,
                aluno=alunos[aluno_key],
                defaults={
                    'plano': planos[plano_key],
                    'data_inicio': hoje - timedelta(days=75),
                    'data_fim': None,
                    'ativa': True,
                },
            )

        status_por_aluno = {
            'ana': ['pago', 'pago', 'pendente'],
            'bruno': ['pago', 'atrasado', 'pendente'],
            'carla': ['pago', 'pago', 'pago'],
            'diego': ['atrasado', 'atrasado', 'pendente'],
            'elisa': ['pago', 'pendente', 'pendente'],
            'fabio': ['pago', 'pago', 'atrasado'],
            'gi': ['pago', 'pago', 'pendente'],
            'hugo': ['atrasado', 'pendente', 'pendente'],
            'ines': ['pago', 'pago', 'pago'],
            'joao': ['pago', 'atrasado', 'atrasado'],
            'kelly': ['pago', 'pendente', 'pendente'],
            'leo': ['pago', 'pago', 'pendente'],
            'maria': ['pago', 'pago', 'atrasado'],
            'nando': ['pendente', 'pendente', 'pendente'],
            'olivia': ['pago', 'pago', 'pago'],
            'paulo': ['atrasado', 'atrasado', 'pendente'],
        }

        meses = [dois_meses_atras, mes_passado, primeiro_dia_mes]
        for aluno_key, status_lista in status_por_aluno.items():
            matricula = matriculas[aluno_key]
            for mes, mensalidade_status in zip(meses, status_lista):
                data_pagamento = None
                if mensalidade_status == 'pago':
                    data_pagamento = mes.replace(day=5)
                Mensalidade.objects.update_or_create(
                    matricula=matricula,
                    mes_referencia=mes,
                    defaults={
                        'arena': self.arena,
                        'valor': matricula.plano.valor,
                        'vencimento': mes.replace(day=10),
                        'data_pagamento': data_pagamento,
                        'status': mensalidade_status,
                    },
                )

        self._checkin(alunos['ana'], turmas['volei_manha'], hoje, True)
        self._checkin(alunos['bruno'], turmas['volei_manha'], hoje, True)
        self._checkin(alunos['carla'], turmas['volei_manha'], hoje, False, 'Avisou que chegaria atrasada e nao veio.')
        self._checkin(alunos['ana'], turmas['funcional'], hoje, True)
        self._checkin(alunos['kelly'], turmas['funcional'], hoje, False, 'Faltou sem aviso.')
        self._checkin(alunos['fabio'], turmas['futevolei'], hoje - timedelta(days=1), False, 'Faltou na ultima aula.')
        self._checkin(alunos['hugo'], turmas['futevolei'], hoje - timedelta(days=1), True)
        self._checkin(alunos['maria'], turmas['beachtennis'], hoje - timedelta(days=2), False, 'Falta recorrente.')
        self._checkin(alunos['leo'], turmas['beachtennis'], hoje - timedelta(days=2), True)

        solicitacoes = [
            ('olivia', 'volei_noite', 'matricula', 'pendente', 'Quero trocar do funcional para uma turma a noite.'),
            ('nando', 'futevolei', 'matricula', 'pendente', 'Tenho experiencia e posso fazer teste.'),
            ('paulo', 'beachtennis', 'matricula', 'recusada', 'Queria entrar mesmo com mensalidade em atraso.'),
            ('gi', 'volei_noite', 'cancelamento', 'pendente', 'Horario ficou ruim por causa do trabalho.'),
            ('diego', 'futevolei', 'cancelamento', 'pendente', 'Vou viajar por algumas semanas.'),
            ('ines', 'funcional', 'matricula', 'aprovada', 'Quero complementar o treino.'),
        ]
        for aluno_key, turma_key, tipo, status_solicitacao, observacao in solicitacoes:
            SolicitacaoMatricula.objects.update_or_create(
                arena=self.arena,
                aluno=alunos[aluno_key],
                turma=turmas[turma_key],
                tipo=tipo,
                defaults={
                    'status': status_solicitacao,
                    'observacao_aluno': observacao,
                    'motivo_recusa': 'Mensalidades atrasadas no momento.' if status_solicitacao == 'recusada' else '',
                },
            )

        fila = [
            ('olivia', 'beachtennis', 1),
            ('nando', 'beachtennis', 2),
            ('paulo', 'volei_manha', 1),
        ]
        for aluno_key, turma_key, posicao in fila:
            FilaEspera.objects.update_or_create(
                arena=self.arena,
                aluno=alunos[aluno_key],
                turma=turmas[turma_key],
                defaults={'posicao': posicao, 'status': 'aguardando'},
            )

        self.stdout.write(self.style.SUCCESS('Dados ficticios criados/atualizados com sucesso.'))
        self.stdout.write('Senha demo carregada com seguranca a partir do ambiente.')
        self.stdout.write('Exemplo de aluno multi-turma: demo.ana')

    def _usuario(self, username, first_name, last_name, tipo, telefone=''):
        user, created = Usuario.objects.update_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': f'{username}@arena.demo',
                'tipo': tipo,
                'telefone': telefone,
                'arena': self.arena,
                'is_active': True,
                'is_staff': tipo == 'admin',
            },
        )
        user.set_password(self.demo_password)
        user.save(update_fields=['password'])
        return user

    def _quadra(self, nome, tipo_areia):
        quadra, _ = Quadra.objects.update_or_create(
            arena=self.arena,
            nome=nome,
            defaults={
                'tipo_areia': tipo_areia,
                'ativa': True,
                'observacoes': 'Criada para demonstracao do sistema.',
            },
        )
        return quadra

    def _plano(self, nome, valor, frequencia):
        plano, _ = Plano.objects.update_or_create(
            arena=self.arena,
            nome=nome,
            defaults={
                'valor': valor,
                'frequencia_semanal': frequencia,
                'descricao': 'Plano ficticio para testes visuais e operacionais.',
                'ativo': True,
            },
        )
        return plano

    def _turma(self, nome, professor, quadra, dias_semana, horario, vagas):
        turma, _ = Turma.objects.update_or_create(
            arena=self.arena,
            nome=nome,
            defaults={
                'professor': professor,
                'quadra': quadra,
                'dias_semana': dias_semana,
                'horario': horario,
                'vagas': vagas,
                'ativa': True,
            },
        )
        return turma

    def _checkin(self, aluno, turma, data_checkin, presente, observacao=''):
        CheckIn.objects.update_or_create(
            arena=self.arena,
            aluno=aluno,
            turma=turma,
            data=data_checkin,
            defaults={
                'presente': presente,
                'observacao': observacao,
            },
        )
