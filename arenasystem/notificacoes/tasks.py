from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def send_transactional_email(self, subject, text, recipients, html=''):
    message = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, recipients)
    if html:
        message.attach_alternative(html, 'text/html')
    return message.send(fail_silently=False)

