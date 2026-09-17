from celery import shared_task
from django.utils import timezone

from .checkin_services import expire_pending_checkins, generate_occurrences


@shared_task(name='aulas.tasks.generate_daily_occurrences')
def generate_daily_occurrences():
    return generate_occurrences(timezone.localdate())


@shared_task(name='aulas.tasks.expire_pending_checkins')
def expire_pending_checkins_task():
    return expire_pending_checkins(timezone.localdate())
