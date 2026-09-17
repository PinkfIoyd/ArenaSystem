from django.core.management.base import BaseCommand

from saas_billing.services import reconcile_subscription_lifecycle, take_daily_snapshot


class Command(BaseCommand):
    help = 'Reconcilia estados locais das assinaturas SaaS de forma idempotente.'

    def handle(self, *args, **options):
        changes = reconcile_subscription_lifecycle()
        snapshot = take_daily_snapshot()
        self.stdout.write(self.style.SUCCESS(f'Reconciliacao concluida: {changes}; snapshot={snapshot.date}'))

