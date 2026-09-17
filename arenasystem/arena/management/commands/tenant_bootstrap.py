from django.core.management.base import BaseCommand

from arena.models import Matricula, Mensalidade, PaymentWebhookEvent, Plano, Quadra
from arena.tenant import get_default_arena
from aulas.models import CheckIn, FilaEspera, SolicitacaoMatricula, Turma
from loja.models import Categoria, Fornecedor, ItemVenda, LoteEstoque, MovimentacaoEstoque, Produto, Venda
from manutencao.models import Manutencao
from notificacoes.models import Notificacao, NotificacaoAdmin
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Cria arena padrao e vincula dados legados ao tenant demo.'

    def handle(self, *args, **options):
        arena = get_default_arena()

        modelos = [
            Usuario,
            Quadra,
            Plano,
            Matricula,
            Mensalidade,
            Turma,
            CheckIn,
            SolicitacaoMatricula,
            FilaEspera,
            Categoria,
            Fornecedor,
            Produto,
            LoteEstoque,
            MovimentacaoEstoque,
            Venda,
            ItemVenda,
            Manutencao,
            Notificacao,
            NotificacaoAdmin,
            PaymentWebhookEvent,
        ]

        for modelo in modelos:
            atualizados = modelo.objects.filter(arena__isnull=True).update(arena=arena)
            if atualizados:
                self.stdout.write(f'{modelo.__name__}: {atualizados} registro(s) vinculados.')

        self.stdout.write(self.style.SUCCESS(f'Tenant padrao pronto: {arena.nome} ({arena.slug})'))
