import re


SENSITIVE_KEYS = {'password', 'senha', 'token', 'access', 'refresh', 'secret', 'authorization'}


def sanitize_audit_text(value, max_length=240):
    text = ' '.join(str(value or '').split())
    text = re.sub(
        r'(?i)\b(password|senha|token|authorization|secret)\s*[:=]\s*[^\s,;]+',
        lambda match: f'{match.group(1)}=[mascarado]',
        text,
    )
    return text[:max_length]


def _clean(value):
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if not isinstance(value, dict):
        return value
    cleaned = {}
    for key, item in value.items():
        lowered = str(key).lower()
        if any(secret in lowered for secret in SENSITIVE_KEYS):
            cleaned[key] = '[mascarado]'
            continue
        cleaned[key] = _clean(item)
    return cleaned


def request_metadata(request):
    return {
        'method': request.method,
        'path': request.path,
        'frontend_route': sanitize_audit_text(request.headers.get('X-Frontend-Route'), 300),
        'user_agent': sanitize_audit_text(request.headers.get('User-Agent'), 500),
    }


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def registrar_auditoria(request, arena, acao, entidade, anteriores=None, novos=None, metadados=None, usuario=None):
    from .models import AuditLog

    AuditLog.objects.create(
        arena=arena,
        usuario=usuario if usuario is not None else request.user if request and request.user.is_authenticated else None,
        acao=acao,
        entidade_tipo=entidade.__class__.__name__ if entidade else '',
        entidade_id=str(getattr(entidade, 'id', '') or ''),
        valores_anteriores=_clean(anteriores or {}),
        valores_novos=_clean(novos or {}),
        metadados=_clean({**request_metadata(request), **(metadados or {})}) if request else _clean(metadados or {}),
        ip=client_ip(request) if request else None,
    )
