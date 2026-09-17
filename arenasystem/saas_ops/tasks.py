from celery import shared_task

from .models import DataSubjectRequest


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def prepare_data_export(self, request_id):
    request = DataSubjectRequest.objects.get(id=request_id, kind='export')
    request.export_ready = True
    request.save(update_fields=['export_ready'])
    return {'request_id': request.id, 'ready': True}

