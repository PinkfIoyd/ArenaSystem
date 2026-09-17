import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arenasystem.settings')

app = Celery('arenasystem')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

