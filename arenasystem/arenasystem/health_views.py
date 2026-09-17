from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from usuarios.permissions import IsSaasSuperAdmin


def _components():
    result = {'database': False, 'redis': False, 'worker': False}
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            result['database'] = cursor.fetchone()[0] == 1
    except Exception:
        pass
    try:
        from redis import Redis
        client = Redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=1, socket_timeout=1)
        result['redis'] = bool(client.ping())
        result['worker'] = bool(client.get('arenaflow:worker-heartbeat'))
    except Exception:
        pass
    return result


def health(request):
    return JsonResponse({'status': 'ok'})


def readiness(request):
    ready = all(_components().values())
    return JsonResponse({'status': 'ok' if ready else 'degraded'}, status=200 if ready else 503)


@api_view(['GET'])
@permission_classes([IsSaasSuperAdmin])
def health_components(request):
    return Response(_components())

