from datetime import date

from django.core.management.base import BaseCommand, CommandError

from aulas.checkin_services import generate_occurrences


class Command(BaseCommand):
    help = 'Gera de forma idempotente as ocorrencias de aula da data informada.'

    def add_arguments(self, parser):
        parser.add_argument('--date', dest='target_date')

    def handle(self, *args, **options):
        try:
            target_date = date.fromisoformat(options['target_date']) if options['target_date'] else None
        except ValueError as exc:
            raise CommandError('Use --date no formato AAAA-MM-DD.') from exc
        created = generate_occurrences(target_date)
        self.stdout.write(self.style.SUCCESS(f'{created} ocorrencia(s) criada(s).'))
