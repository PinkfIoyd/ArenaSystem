from celery import shared_task
from django.core.management import call_command

from .services import reconcile_subscription_lifecycle, take_daily_snapshot


@shared_task
def worker_heartbeat():
    from django.conf import settings
    from redis import Redis
    Redis.from_url(settings.CELERY_BROKER_URL).setex('arenaflow:worker-heartbeat', 180, 'ok')
    return {'status': 'ok'}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def reconcile_saas_subscriptions(self):
    return reconcile_subscription_lifecycle()


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def snapshot_saas_metrics(self):
    snapshot = take_daily_snapshot()
    return {'date': snapshot.date.isoformat(), **snapshot.metrics}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def send_saas_lifecycle_notifications(self):
    call_command('send_saas_notifications')
    return {'status': 'ok'}
