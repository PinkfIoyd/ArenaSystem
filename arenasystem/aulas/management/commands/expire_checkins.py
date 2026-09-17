from datetime import date

from django.core.management.base import BaseCommand, CommandError

from aulas.checkin_services import expire_pending_checkins


class Command(BaseCommand):
    help = 'Expira, sem duplicar notificacoes, check-ins pendentes de dias anteriores.'

    def add_arguments(self, parser):
        parser.add_argument('--reference-date')

    def handle(self, *args, **options):
        try:
            reference = date.fromisoformat(options['reference_date']) if options['reference_date'] else None
        except ValueError as exc:
            raise CommandError('Use --reference-date no formato AAAA-MM-DD.') from exc
        expired = expire_pending_checkins(reference)
        self.stdout.write(self.style.SUCCESS(f'{expired} check-in(s) expirado(s).'))
