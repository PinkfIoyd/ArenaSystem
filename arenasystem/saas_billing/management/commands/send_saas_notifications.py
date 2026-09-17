from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from notificacoes.services import criar_notificacao
from saas_billing.models import SaasSubscription


class Command(BaseCommand):
    help = 'Envia avisos idempotentes do ciclo de assinatura SaaS.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        sent = 0
        subscriptions = SaasSubscription.objects.select_related('arena').prefetch_related('arena__usuarios')
        for subscription in subscriptions:
            owner = subscription.arena.usuarios.filter(papel='dono', is_active=True).first()
            if not owner:
                continue
            event = None
            when = None
            if subscription.status == 'trialing' and subscription.trial_ends_at:
                when = subscription.trial_ends_at.date()
                if when - today in {timedelta(days=7), timedelta(days=3), timedelta(days=1)}:
                    event = 'Seu periodo de teste esta terminando'
            elif subscription.status == 'past_due' and subscription.grace_ends_at:
                when = subscription.grace_ends_at.date()
                event = 'Regularize a assinatura para evitar a suspensao'
            if not event:
                continue
            dedupe = f'[saas:{subscription.id}:{subscription.status}:{when.isoformat()}]'
            if owner.notificacoes.filter(mensagem__contains=dedupe).exists():
                continue
            criar_notificacao(
                owner, event,
                f'{dedupe} Consulte a pagina Minha assinatura para revisar o plano e as cobrancas.',
                tipo='financeiro', enviar_email=True, arena=subscription.arena,
            )
            sent += 1
        self.stdout.write(self.style.SUCCESS(f'{sent} notificacoes criadas.'))

