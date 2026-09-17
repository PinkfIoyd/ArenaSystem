import json
import logging
import time
import uuid


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('arenaflow.request')

    def __call__(self, request):
        request_id = str(request.headers.get('X-Request-ID', '')).strip()[:100] or str(uuid.uuid4())
        request.request_id = request_id
        started = time.monotonic()
        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        self.logger.info('request_completed', extra={
            'request_id': request_id, 'method': request.method, 'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round((time.monotonic() - started) * 1000, 2),
            'arena_id': request.headers.get('X-Arena-ID', ''),
        })
        return response


class JSONFormatter(logging.Formatter):
    SAFE_FIELDS = ('request_id', 'method', 'path', 'status_code', 'duration_ms', 'arena_id', 'task_id')

    def format(self, record):
        payload = {
            'timestamp': self.formatTime(record, self.datefmt), 'level': record.levelname,
            'logger': record.name, 'message': record.getMessage(),
        }
        for field in self.SAFE_FIELDS:
            value = getattr(record, field, None)
            if value not in (None, ''):
                payload[field] = value
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)[:2000]
        return json.dumps(payload, ensure_ascii=False)

