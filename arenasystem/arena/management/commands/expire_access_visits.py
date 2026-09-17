from django.core.management.base import BaseCommand

from arena.access_services import expire_access_visits


class Command(BaseCommand):
    help = 'Expira solicitações de acesso e encerra visitas abertas após o expediente.'

    def handle(self, *args, **options):
        result = expire_access_visits()
        self.stdout.write(self.style.SUCCESS(
            f"Solicitações expiradas: {result['expired']}; visitas encerradas: {result['checked_out']}."
        ))
