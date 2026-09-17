import calendar

from django.core.management.base import BaseCommand
from django.utils import timezone

from arena.api_views import atualizar_mensalidades_atrasadas
from arena.models import Matricula, Mensalidade


class Command(BaseCommand):
    help = 'Gera mensalidades do mes para matriculas ativas e marca atrasos automaticamente.'

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        primeiro_dia_mes = hoje.replace(day=1)
        criadas = 0

        for matricula in Matricula.objects.filter(ativa=True).select_related('arena', 'plano', 'aluno'):
            ultimo_dia_mes = calendar.monthrange(hoje.year, hoje.month)[1]
            dia_vencimento = min(matricula.dia_vencimento, ultimo_dia_mes)
            vencimento = hoje.replace(day=dia_vencimento)

            _, criada = Mensalidade.objects.get_or_create(
                matricula=matricula,
                mes_referencia=primeiro_dia_mes,
                defaults={
                    'arena': matricula.arena,
                    'valor': matricula.plano.valor,
                    'vencimento': vencimento,
                    'status': 'pendente',
                },
            )
            if criada:
                criadas += 1

        atrasadas = atualizar_mensalidades_atrasadas()
        self.stdout.write(self.style.SUCCESS(
            f'Mensalidades criadas: {criadas}. Marcadas como atrasadas: {atrasadas}.'
        ))
