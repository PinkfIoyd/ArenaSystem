from django.db import transaction
from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from gestao.audit import registrar_auditoria, sanitize_audit_text
from usuarios.models import Usuario
from usuarios.permissions import require_permission, tem_permissao

from .access_services import (
    AccessDomainError, access_state, checkout_access_visit, confirm_access_visit,
    expire_access_visits, manual_access_visit, reject_access_visit, request_access_visit,
)
from .models import AccessVisit
from .serializers import AccessVisitSerializer, OperationalSettingsSerializer
from .tenant import get_user_arena


def _domain_error(exc):
    return Response(exc.payload(), status=exc.http_status)


def _required_reason(request):
    reason = sanitize_audit_text(request.data.get('motivo'), 300)
    if not reason:
        return None, Response({'detail': 'Informe o motivo desta operação.'}, status=400)
    return reason, None


class AccessVisitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccessVisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'public_id'

    def get_queryset(self):
        return AccessVisit.objects.filter(
            arena=get_user_arena(self.request.user), aluno=self.request.user,
        ).select_related('aluno', 'matricula', 'plano', 'validado_por', 'checkout_por')

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        expire_access_visits(arena=get_user_arena(request.user))
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        arena = get_user_arena(request.user)
        try:
            visit = request_access_visit(request.user, arena)
        except AccessDomainError as exc:
            return _domain_error(exc)
        registrar_auditoria(
            request, arena, 'access.requested' if visit.status == 'pending' else 'access.confirmed', visit,
            novos={'status': visit.status, 'origem': visit.origem, 'plan_id': visit.plano_id},
        )
        payload = AccessVisitSerializer(visit, context={'request': request}).data
        return Response(
            {'detail': 'Acesso confirmado.' if visit.status == 'confirmed' else 'Solicitação enviada para a recepção.', 'visit': payload},
            status=status.HTTP_201_CREATED if visit.status == 'confirmed' else status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['post'], url_path='check-out')
    def check_out(self, request, public_id=None):
        visit = self.get_object()
        try:
            visit = checkout_access_visit(visit, actor=request.user, origin='member')
        except AccessDomainError as exc:
            return _domain_error(exc)
        registrar_auditoria(
            request, visit.arena, 'access.checked_out', visit,
            anteriores={'status': 'confirmed'}, novos={'status': visit.status, 'origem': 'member'},
        )
        return Response(self.get_serializer(visit).data)


class AdminAccessVisitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccessVisitSerializer
    permission_classes = [require_permission('access.manage')]
    lookup_field = 'public_id'

    def get_queryset(self):
        return AccessVisit.objects.filter(arena=get_user_arena(self.request.user)).select_related(
            'aluno', 'matricula', 'plano', 'validado_por', 'checkout_por',
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        arena = get_user_arena(request.user)
        expire_access_visits(arena=arena)
        today = timezone.localdate()
        starts_at = timezone.make_aware(datetime.combine(today, time.min), timezone.get_current_timezone())
        ends_at = starts_at + timedelta(days=1)
        queryset = self.get_queryset().filter(solicitado_em__gte=starts_at, solicitado_em__lt=ends_at)
        return Response(self.get_serializer(queryset, many=True).data)

    def _override(self, request):
        requested = bool(request.data.get('override_limits', False))
        if requested and not tem_permissao(request.user, 'access.override'):
            return False, Response({'detail': 'Você não possui permissão para ultrapassar limites.'}, status=403)
        return requested, None

    @action(detail=True, methods=['post'])
    def confirm(self, request, public_id=None):
        visit = self.get_object()
        override, error = self._override(request)
        if error:
            return error
        reason = sanitize_audit_text(request.data.get('motivo'), 300)
        if override and not reason:
            return Response({'detail': 'Informe o motivo para ultrapassar o limite.'}, status=400)
        try:
            visit = confirm_access_visit(visit, request.user, override_limits=override, reason=reason)
        except AccessDomainError as exc:
            return _domain_error(exc)
        registrar_auditoria(
            request, visit.arena, 'access.confirmed', visit,
            anteriores={'status': 'pending'}, novos={'status': 'confirmed', 'override_limits': override, 'motivo': reason},
        )
        return Response(self.get_serializer(visit).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, public_id=None):
        reason, error = _required_reason(request)
        if error:
            return error
        visit = self.get_object()
        try:
            visit = reject_access_visit(visit, request.user, reason)
        except AccessDomainError as exc:
            return _domain_error(exc)
        registrar_auditoria(
            request, visit.arena, 'access.rejected', visit,
            anteriores={'status': 'pending'}, novos={'status': 'rejected', 'motivo': reason},
        )
        return Response(self.get_serializer(visit).data)

    @action(detail=False, methods=['post'], url_path='bulk-confirm')
    def bulk_confirm(self, request):
        ids = request.data.get('visits') or []
        if not isinstance(ids, list) or not ids:
            return Response({'detail': 'Selecione ao menos uma solicitação.'}, status=400)
        confirmed, errors = [], []
        for public_id in ids[:100]:
            visit = self.get_queryset().filter(public_id=public_id).first()
            if not visit:
                errors.append({'id': str(public_id), 'code': 'not_found'})
                continue
            try:
                visit = confirm_access_visit(visit, request.user)
                confirmed.append(AccessVisitSerializer(visit, context={'request': request}).data)
                registrar_auditoria(request, visit.arena, 'access.confirmed', visit, novos={'status': 'confirmed', 'bulk': True})
            except AccessDomainError as exc:
                errors.append({'id': str(public_id), **exc.payload()})
        return Response({'confirmed': confirmed, 'errors': errors})

    @action(detail=False, methods=['post'])
    def manual(self, request):
        reason, error = _required_reason(request)
        if error:
            return error
        arena = get_user_arena(request.user)
        student = Usuario.objects.filter(id=request.data.get('aluno'), arena=arena, tipo='aluno').first()
        if not student:
            return Response({'detail': 'Membro não encontrado nesta unidade.'}, status=404)
        override, error = self._override(request)
        if error:
            return error
        try:
            visit = manual_access_visit(student, arena, request.user, reason, override_limits=override)
        except AccessDomainError as exc:
            return _domain_error(exc)
        registrar_auditoria(
            request, arena, 'access.manual', visit,
            novos={'status': 'confirmed', 'motivo': reason, 'override_limits': override},
        )
        return Response(self.get_serializer(visit).data, status=201)

    @action(detail=True, methods=['post'])
    def checkout(self, request, public_id=None):
        visit = self.get_object()
        try:
            visit = checkout_access_visit(visit, actor=request.user, origin='reception')
        except AccessDomainError as exc:
            return _domain_error(exc)
        registrar_auditoria(request, visit.arena, 'access.checked_out', visit, novos={'status': 'checked_out', 'origem': 'reception'})
        return Response(self.get_serializer(visit).data)

    @action(detail=True, methods=['post'])
    def correct(self, request, public_id=None):
        reason, error = _required_reason(request)
        if error:
            return error
        target = request.data.get('status')
        if target not in {'confirmed', 'checked_out'}:
            return Response({'detail': 'Status de correção inválido.'}, status=400)
        visit = self.get_object()
        previous = visit.status
        try:
            if target == 'checked_out':
                visit = checkout_access_visit(visit, actor=request.user, origin='reception', reason=reason)
            else:
                from .access_services import publish_access_event, validate_open_access
                with transaction.atomic():
                    locked = AccessVisit.objects.select_for_update().get(pk=visit.pk)
                    if AccessVisit.objects.filter(arena=locked.arena, aluno=locked.aluno, status__in=['pending', 'confirmed']).exclude(pk=locked.pk).exists():
                        raise AccessDomainError('access_already_open', 'Já existe outra visita aberta para este membro.')
                    context = validate_open_access(locked.aluno, locked.arena, lock=True)
                    locked.status = 'confirmed'
                    locked.matricula = context['membership']
                    locked.plano = context['membership'].plano
                    locked.entrada_em = locked.entrada_em or timezone.now()
                    locked.saida_em = None
                    locked.checkout_origem = ''
                    locked.motivo = reason
                    locked.validado_por = request.user
                    locked.inadimplente_no_momento = context['delinquent']
                    locked.save(update_fields=[
                        'status', 'matricula', 'plano', 'entrada_em', 'saida_em',
                        'checkout_origem', 'motivo', 'validado_por',
                        'inadimplente_no_momento', 'atualizado_em',
                    ])
                    visit = locked
                    publish_access_event(visit, 'visit.confirmed')
        except AccessDomainError as exc:
            return _domain_error(exc)
        registrar_auditoria(
            request, visit.arena, 'access.corrected', visit,
            anteriores={'status': previous}, novos={'status': target, 'motivo': reason},
        )
        return Response(self.get_serializer(visit).data)


@api_view(['GET', 'PATCH'])
@permission_classes([require_permission('access.manage')])
def access_settings(request):
    arena = get_user_arena(request.user)
    settings = arena.get_operational_settings()
    if request.method == 'PATCH':
        before = OperationalSettingsSerializer(settings).data
        serializer = OperationalSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        settings = serializer.save()
        registrar_auditoria(
            request, arena, 'access.settings_updated', settings,
            anteriores=before, novos=OperationalSettingsSerializer(settings).data,
        )
    return Response(OperationalSettingsSerializer(settings).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_access_state(request):
    arena = get_user_arena(request.user)
    state = access_state(request.user, arena)
    visit = state.pop('visit', None)
    return Response({
        **state,
        'visit': AccessVisitSerializer(visit, context={'request': request}).data if visit else None,
    })
