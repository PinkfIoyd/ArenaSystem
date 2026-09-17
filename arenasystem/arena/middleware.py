from .tenant import _is_saas_superadmin, reset_current_request, set_current_request


class CurrentRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = set_current_request(request)
        try:
            response = self.get_response(request)
            self._audit_cross_tenant(request, response)
            return response
        finally:
            reset_current_request(token)

    @staticmethod
    def _audit_cross_tenant(request, response):
        arena_id = request.headers.get('X-Arena-ID')
        user = getattr(request, 'user', None)
        if not arena_id or not _is_saas_superadmin(user):
            return
        if request.path.startswith('/api/saas/'):
            return

        from arena.models import Arena
        from gestao.audit import registrar_auditoria, sanitize_audit_text

        arena = Arena.objects.filter(id=arena_id).first()
        if not arena or (user.arena_id and str(user.arena_id) == str(arena.id)):
            return

        view = getattr(response, 'renderer_context', {}).get('view') if hasattr(response, 'renderer_context') else None
        registrar_auditoria(
            request,
            arena,
            'superadmin.cross_tenant_access',
            arena,
            metadados={
                'status_code': response.status_code,
                'view': view.__class__.__name__ if view else '',
                'action': getattr(view, 'action', '') if view else '',
                'motivo': sanitize_audit_text(request.headers.get('X-Arena-Access-Reason')),
                'cross_tenant': True,
            },
        )
