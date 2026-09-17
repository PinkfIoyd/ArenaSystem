from calendar import monthrange
from datetime import datetime, time, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from aulas.checkin_services import is_student_delinquent
from notificacoes.models import Notificacao

from .models import (
    AccessIntegrationEvent, AccessVisit, ArenaBusinessHours, Matricula,
)


class AccessDomainError(Exception):
    def __init__(self, code, detail, http_status=409, **extra):
        self.code = code
        self.detail = detail
        self.http_status = http_status
        self.extra = extra
        super().__init__(detail)

    def payload(self):
        return {'code': self.code, 'detail': self.detail, **self.extra}


def _aware(target_date, target_time):
    return timezone.make_aware(datetime.combine(target_date, target_time), timezone.get_current_timezone())


def _active_membership(student, arena, target_date, lock=False):
    queryset = Matricula.objects.select_related('plano').filter(
        arena=arena, aluno=student, ativa=True, data_inicio__lte=target_date,
    ).filter(Q(data_fim__isnull=True) | Q(data_fim__gte=target_date)).order_by('-data_inicio', '-id')
    if lock:
        queryset = queryset.select_for_update()
    return queryset.first()


def _subscription_is_operational(arena):
    try:
        return arena.saas_subscription.status not in {'suspended', 'canceled'}
    except Exception:
        return True


def _business_window(arena, local_now):
    hours = ArenaBusinessHours.objects.filter(arena=arena, weekday=local_now.weekday()).first()
    if not hours or hours.closed or not hours.opens_at or not hours.closes_at:
        raise AccessDomainError('access_outside_hours', 'A unidade está fechada neste horário.')
    opens_at = _aware(local_now.date(), hours.opens_at)
    closes_at = _aware(local_now.date(), hours.closes_at)
    if not opens_at <= local_now < closes_at:
        raise AccessDomainError(
            'access_outside_hours', 'O acesso está fora do horário de funcionamento.',
            opens_at=opens_at.isoformat(), closes_at=closes_at.isoformat(),
        )
    return opens_at, closes_at


def _plan_window(plan, local_now):
    windows = plan.janelas_acesso.filter(
        weekday=local_now.weekday(), starts_at__lte=local_now.time().replace(tzinfo=None),
        ends_at__gt=local_now.time().replace(tzinfo=None),
    ).order_by('ends_at')
    window = windows.first()
    if not window:
        raise AccessDomainError('access_not_allowed_by_plan', 'Seu plano não permite acesso neste dia ou horário.')
    return _aware(local_now.date(), window.starts_at), _aware(local_now.date(), window.ends_at)


def _period_bounds(local_now, period):
    if period == 'day':
        start_date, end_date = local_now.date(), local_now.date() + timedelta(days=1)
    elif period == 'week':
        start_date = local_now.date() - timedelta(days=local_now.weekday())
        end_date = start_date + timedelta(days=7)
    else:
        start_date = local_now.date().replace(day=1)
        days = monthrange(start_date.year, start_date.month)[1]
        end_date = start_date + timedelta(days=days)
    return _aware(start_date, time.min), _aware(end_date, time.min)


def _assert_limits(membership, local_now):
    plan = membership.plano
    limits = {
        'day': plan.limite_acessos_dia,
        'week': plan.limite_acessos_semana,
        'month': plan.limite_acessos_mes,
    }
    for period, limit in limits.items():
        if limit is None:
            continue
        starts_at, ends_at = _period_bounds(local_now, period)
        usage = AccessVisit.objects.filter(
            matricula=membership, status__in=['confirmed', 'checked_out'],
            entrada_em__gte=starts_at, entrada_em__lt=ends_at,
        ).count()
        if usage >= limit:
            raise AccessDomainError(
                'access_limit_reached', 'O limite de acessos do seu plano foi atingido.',
                period=period, usage=usage, limit=limit,
            )


def validate_open_access(student, arena, now=None, lock=False, check_limits=True):
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    settings = arena.get_operational_settings()
    if not settings.open_access_enabled:
        raise AccessDomainError('feature_disabled', 'O acesso livre não está habilitado nesta unidade.', 403)
    if student.arena_id != arena.id or student.papel_efetivo != 'aluno':
        raise AccessDomainError('invalid_tenant', 'Usuário e unidade não pertencem ao mesmo contexto.', 403)
    if not _subscription_is_operational(arena):
        raise AccessDomainError('subscription_inactive', 'A assinatura da unidade está inativa.', 402)
    membership = _active_membership(student, arena, local_now.date(), lock=lock)
    if not membership:
        raise AccessDomainError('inactive_enrollment', 'Sua matrícula não está ativa.', 403)
    if not membership.plano.permite_acesso_livre:
        raise AccessDomainError('access_not_allowed_by_plan', 'Seu plano não inclui acesso livre.', 403)
    _, business_closes = _business_window(arena, local_now)
    _, plan_closes = _plan_window(membership.plano, local_now)
    delinquent = is_student_delinquent(student, arena, local_now.date())
    if delinquent and arena.delinquent_checkin_policy == 'block':
        raise AccessDomainError('student_payment_overdue', 'Regularize sua situação financeira antes do acesso.')
    if check_limits:
        _assert_limits(membership, local_now)
    return {
        'membership': membership,
        'delinquent': delinquent,
        'closes_at': min(business_closes, plan_closes),
        'settings': settings,
    }


@transaction.atomic
def request_access_visit(student, arena, now=None, origin='mobile'):
    now = now or timezone.now()
    expire_access_visits(now=now, arena=arena)
    context = validate_open_access(student, arena, now=now, lock=True)
    existing = AccessVisit.objects.select_for_update().filter(
        arena=arena, aluno=student, status__in=['pending', 'confirmed'],
    ).first()
    if existing:
        raise AccessDomainError(
            'access_already_open', 'Já existe uma solicitação ou visita aberta.',
            visit_id=str(existing.public_id), visit_status=existing.status,
        )
    expires_at = min(
        now + timedelta(minutes=context['settings'].open_access_pending_minutes),
        context['closes_at'],
    )
    automatic = context['settings'].open_access_validation == 'automatic'
    try:
        visit = AccessVisit.objects.create(
            arena=arena, aluno=student, matricula=context['membership'], plano=context['membership'].plano,
            status='confirmed' if automatic else 'pending', origem=origin,
            solicitado_em=now, expira_em=None if automatic else expires_at,
            validado_em=now if automatic else None, entrada_em=now if automatic else None,
            inadimplente_no_momento=context['delinquent'],
        )
    except IntegrityError as exc:
        raise AccessDomainError('access_already_open', 'Já existe uma solicitação ou visita aberta.') from exc
    if automatic:
        publish_access_event(visit, 'visit.confirmed')
        notify_access(visit, 'Acesso confirmado', 'Seu acesso à unidade foi confirmado automaticamente.')
    return visit


@transaction.atomic
def confirm_access_visit(visit, operator, now=None, override_limits=False, reason=''):
    now = now or timezone.now()
    visit = AccessVisit.objects.select_for_update().select_related('arena', 'aluno').get(pk=visit.pk)
    if visit.status != 'pending':
        raise AccessDomainError('access_request_expired', 'A solicitação não está mais pendente.')
    if visit.expira_em and now > visit.expira_em:
        visit.status = 'expired'
        visit.save(update_fields=['status', 'atualizado_em'])
        raise AccessDomainError('access_request_expired', 'A solicitação expirou. Peça ao membro para tentar novamente.')
    try:
        context = validate_open_access(visit.aluno, visit.arena, now=now, lock=True, check_limits=not override_limits)
    except AccessDomainError:
        raise
    visit.matricula = context['membership']
    visit.plano = context['membership'].plano
    visit.status = 'confirmed'
    visit.validado_em = now
    visit.entrada_em = now
    visit.validado_por = operator
    visit.motivo = reason if override_limits else visit.motivo
    visit.inadimplente_no_momento = context['delinquent']
    visit.save(update_fields=[
        'matricula', 'plano', 'status', 'validado_em', 'entrada_em', 'validado_por',
        'motivo', 'inadimplente_no_momento', 'atualizado_em',
    ])
    publish_access_event(visit, 'visit.confirmed')
    notify_access(visit, 'Acesso confirmado', 'Sua entrada foi confirmada pela recepção.')
    return visit


@transaction.atomic
def reject_access_visit(visit, operator, reason, now=None):
    now = now or timezone.now()
    visit = AccessVisit.objects.select_for_update().get(pk=visit.pk)
    if visit.status != 'pending':
        raise AccessDomainError('access_request_expired', 'A solicitação não está mais pendente.')
    visit.status = 'rejected'
    visit.validado_em = now
    visit.validado_por = operator
    visit.motivo = reason
    visit.save(update_fields=['status', 'validado_em', 'validado_por', 'motivo', 'atualizado_em'])
    publish_access_event(visit, 'visit.rejected')
    notify_access(visit, 'Acesso não confirmado', f'Sua solicitação foi rejeitada: {reason}')
    return visit


@transaction.atomic
def manual_access_visit(student, arena, operator, reason, now=None, override_limits=False):
    now = now or timezone.now()
    expire_access_visits(now=now, arena=arena)
    context = validate_open_access(student, arena, now=now, lock=True, check_limits=not override_limits)
    if AccessVisit.objects.select_for_update().filter(
        arena=arena, aluno=student, status__in=['pending', 'confirmed'],
    ).exists():
        raise AccessDomainError('access_already_open', 'Já existe uma solicitação ou visita aberta.')
    visit = AccessVisit.objects.create(
        arena=arena, aluno=student, matricula=context['membership'], plano=context['membership'].plano,
        status='confirmed', origem='manual', solicitado_em=now, validado_em=now, entrada_em=now,
        validado_por=operator, motivo=reason, inadimplente_no_momento=context['delinquent'],
    )
    publish_access_event(visit, 'visit.confirmed')
    notify_access(visit, 'Acesso registrado', 'Sua entrada foi registrada manualmente pela recepção.')
    return visit


@transaction.atomic
def checkout_access_visit(visit, actor=None, origin='member', now=None, reason=''):
    now = now or timezone.now()
    visit = AccessVisit.objects.select_for_update().get(pk=visit.pk)
    if visit.status != 'confirmed':
        raise AccessDomainError('access_not_open', 'Esta visita não está aberta.')
    visit.status = 'checked_out'
    visit.saida_em = now
    visit.checkout_por = actor
    visit.checkout_origem = origin
    if reason:
        visit.motivo = reason
    visit.save(update_fields=['status', 'saida_em', 'checkout_por', 'checkout_origem', 'motivo', 'atualizado_em'])
    return visit


def access_state(student, arena, now=None):
    now = now or timezone.now()
    expire_access_visits(now=now, arena=arena)
    current = AccessVisit.objects.filter(arena=arena, aluno=student, status__in=['pending', 'confirmed']).first()
    if current:
        return {'state': current.status, 'visit': current}
    try:
        context = validate_open_access(student, arena, now=now, lock=False)
        return {'state': 'available', 'visit': None, 'closes_at': context['closes_at']}
    except AccessDomainError as exc:
        return {'state': exc.code, 'visit': None, 'detail': exc.detail, **exc.extra}


def expire_access_visits(now=None, arena=None):
    now = now or timezone.now()
    queryset = AccessVisit.objects.filter(status='pending', expira_em__lte=now)
    if arena:
        queryset = queryset.filter(arena=arena)
    expired_visits = list(queryset.select_related('arena', 'aluno'))
    for visit in expired_visits:
        visit.status = 'expired'
        visit.save(update_fields=['status', 'atualizado_em'])
        notify_access(visit, 'Solicitação expirada', 'Sua solicitação de acesso expirou antes da validação.')
        from gestao.audit import registrar_auditoria
        registrar_auditoria(
            None, visit.arena, 'access.expired', visit,
            anteriores={'status': 'pending'}, novos={'status': 'expired'},
            metadados={'source': 'access_expiration'}, usuario=visit.aluno,
        )
    open_visits = AccessVisit.objects.filter(status='confirmed').select_related('arena')
    if arena:
        open_visits = open_visits.filter(arena=arena)
    checked_out = 0
    for visit in open_visits:
        entry_local = timezone.localtime(visit.entrada_em or visit.solicitado_em)
        hours = ArenaBusinessHours.objects.filter(arena=visit.arena, weekday=entry_local.weekday()).first()
        closing_time = hours.closes_at if hours and hours.closes_at else time.max
        closes_at = _aware(entry_local.date(), closing_time)
        if now >= closes_at:
            checkout_access_visit(visit, origin='automatic', now=now, reason='Encerramento automático no fim do expediente.')
            from gestao.audit import registrar_auditoria
            registrar_auditoria(
                None, visit.arena, 'access.checked_out', visit,
                anteriores={'status': 'confirmed'},
                novos={'status': 'checked_out', 'origem': 'automatic'},
                metadados={'source': 'business_hours_close'},
            )
            checked_out += 1
    return {'expired': len(expired_visits), 'checked_out': checked_out}


def notify_access(visit, title, message):
    Notificacao.objects.create(
        arena=visit.arena, destinatario=visit.aluno, tipo='geral', titulo=title, mensagem=message,
    )


def publish_access_event(visit, event_type):
    event, created = AccessIntegrationEvent.objects.get_or_create(
        idempotency_key=f'{event_type}:{visit.public_id}',
        defaults={'visit': visit, 'event_type': event_type},
    )
    if created:
        from .tasks import process_access_integration_event
        process_access_integration_event.delay(event.id)
    return event
