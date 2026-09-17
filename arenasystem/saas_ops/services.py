from decimal import Decimal

from django.utils import timezone
from django.db import models

from saas_billing.models import SaasWebhookEvent
from saas_billing.services import effective_limits, subscription_usage

from .models import FeatureBlock, SupportTicket


def is_feature_available(arena, feature):
    now = timezone.now()
    blocked = FeatureBlock.objects.filter(arena=arena, feature=feature, active=True).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    ).exists()
    if blocked:
        return False
    subscription = getattr(arena, 'saas_subscription', None)
    if not subscription:
        return True
    return bool(subscription.plan.features.get(feature, False))


def account_health(arena):
    score = 100
    components = {}
    subscription = getattr(arena, 'saas_subscription', None)
    status_penalty = {'trialing': 0, 'active': 0, 'cancel_at_period_end': 15, 'past_due': 30, 'suspended': 60, 'canceled': 80}
    subscription_status = subscription.status if subscription else 'missing'
    penalty = status_penalty.get(subscription_status, 20)
    score -= penalty
    components['subscription'] = {'status': subscription_status, 'penalty': penalty}

    max_usage = 0
    if subscription:
        usage = subscription_usage(arena)
        limits = effective_limits(subscription)
        max_usage = max((Decimal(usage[key]) / Decimal(max(limit, 1)) * 100 for key, limit in limits.items()), default=Decimal('0'))
    usage_penalty = 15 if max_usage >= 100 else 8 if max_usage >= 90 else 3 if max_usage >= 80 else 0
    score -= usage_penalty
    components['usage'] = {'max_percentage': str(max_usage.quantize(Decimal('0.01'))), 'penalty': usage_penalty}

    urgent = SupportTicket.objects.filter(arena=arena, priority='urgent', status__in=['open', 'in_progress']).count()
    ticket_penalty = min(urgent * 10, 20)
    score -= ticket_penalty
    components['urgent_tickets'] = {'count': urgent, 'penalty': ticket_penalty}

    webhook_errors = SaasWebhookEvent.objects.filter(arena=arena, processed=False).exclude(processing_error='').count()
    integration_penalty = min(webhook_errors * 5, 15)
    score -= integration_penalty
    components['integration_errors'] = {'count': webhook_errors, 'penalty': integration_penalty}
    return {'score': max(score, 0), 'components': components}
