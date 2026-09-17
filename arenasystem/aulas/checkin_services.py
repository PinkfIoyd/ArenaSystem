import unicodedata
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from arena.models import Matricula, Mensalidade
from notificacoes.models import Notificacao

from .models import AulaOcorrencia, CheckIn, Turma


WEEKDAY_ALIASES = {
    0: {'seg', 'segunda', 'segunda-feira'},
    1: {'ter', 'terca', 'terça', 'terca-feira', 'terça-feira'},
    2: {'qua', 'quarta', 'quarta-feira'},
    3: {'qui', 'quinta', 'quinta-feira'},
    4: {'sex', 'sexta', 'sexta-feira'},
    5: {'sab', 'sábado', 'sabado'},
    6: {'dom', 'domingo'},
}


class CheckInDomainError(Exception):
    def __init__(self, code, detail, http_status=409, **extra):
        self.code = code
        self.detail = detail
        self.http_status = http_status
        self.extra = extra
        super().__init__(detail)

    def payload(self):
        return {'code': self.code, 'detail': self.detail, **self.extra}


def _normalize(value):
    value = unicodedata.normalize('NFKD', str(value or '').lower())
    return ''.join(char for char in value if not unicodedata.combining(char)).strip()


def turma_occurs_on(turma, target_date):
    tokens = {_normalize(item) for item in str(turma.dias_semana or '').replace(';', ',').split(',') if item.strip()}
    aliases = {_normalize(item) for item in WEEKDAY_ALIASES[target_date.weekday()]}
    return bool(tokens & aliases)


def ensure_occurrence(turma, target_date):
    if not turma.ativa or not turma_occurs_on(turma, target_date):
        raise CheckInDomainError('class_not_scheduled', 'Esta turma nao possui aula agendada para esta data.')
    occurrence, _ = AulaOcorrencia.objects.get_or_create(
        turma=turma,
        data=target_date,
        defaults={'arena': turma.arena, 'horario_previsto': turma.horario},
    )
    return occurrence


def generate_occurrences(target_date=None, arena=None):
    target_date = target_date or timezone.localdate()
    queryset = Turma.objects.filter(ativa=True).select_related('arena')
    if arena is not None:
        queryset = queryset.filter(arena=arena)
    created = 0
    for turma in queryset:
        if turma_occurs_on(turma, target_date):
            _, was_created = AulaOcorrencia.objects.get_or_create(
                turma=turma,
                data=target_date,
                defaults={'arena': turma.arena, 'horario_previsto': turma.horario},
            )
            created += int(was_created)
    return created


def occurrence_window(occurrence):
    tz = timezone.get_current_timezone()
    starts_at = timezone.make_aware(datetime.combine(occurrence.data, occurrence.horario_previsto), tz)
    return (
        starts_at - timedelta(minutes=occurrence.arena.checkin_minutes_before),
        starts_at + timedelta(minutes=occurrence.arena.checkin_minutes_after),
        starts_at,
    )


def is_student_delinquent(student, arena, target_date=None):
    target_date = target_date or timezone.localdate()
    return Mensalidade.objects.filter(arena=arena, matricula__aluno=student).filter(
        Q(status='atrasado') | Q(status='pendente', vencimento__lte=target_date - timedelta(days=5))
    ).exists()


def active_enrollment_exists(student, arena, target_date=None):
    target_date = target_date or timezone.localdate()
    return Matricula.objects.filter(arena=arena, aluno=student, ativa=True, data_inicio__lte=target_date).filter(
        Q(data_fim__isnull=True) | Q(data_fim__gte=target_date)
    ).exists()


def checkin_state_for(turma, student, now=None):
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    try:
        occurrence = ensure_occurrence(turma, local_now.date())
    except CheckInDomainError:
        return {'state': 'outside_window', 'occurrence_id': None}
    checkin = CheckIn.objects.filter(arena=turma.arena, aluno=student, turma=turma, data=occurrence.data).first()
    opens_at, closes_at, starts_at = occurrence_window(occurrence)
    if checkin:
        state_map = {
            'pending': 'pending', 'confirmed': 'confirmed', 'rejected': 'rejected',
            'expired': 'expired', 'absent': 'expired',
        }
        state = state_map[checkin.status]
    elif now < opens_at or now > closes_at:
        state = 'outside_window'
    else:
        state = 'available'
    return {
        'state': state,
        'occurrence_id': str(occurrence.public_id),
        'starts_at': starts_at.isoformat(),
        'opens_at': opens_at.isoformat(),
        'closes_at': closes_at.isoformat(),
        'checkin_id': checkin.id if checkin else None,
    }


@transaction.atomic
def request_mobile_checkin(turma, student, now=None):
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    arena = turma.arena
    if not arena.get_operational_settings().classes_enabled:
        raise CheckInDomainError('feature_disabled', 'O módulo de aulas está desabilitado nesta unidade.', 403)
    if student.arena_id != arena.id or student.tipo != 'aluno':
        raise CheckInDomainError('invalid_tenant', 'Usuario e turma nao pertencem a mesma arena.', 403)
    if not turma.alunos.filter(pk=student.pk).exists():
        raise CheckInDomainError('student_not_in_class', 'Voce nao esta matriculado nesta turma.', 403)
    if not active_enrollment_exists(student, arena, local_now.date()):
        raise CheckInDomainError('inactive_enrollment', 'Sua matricula nao esta ativa.', 403)
    occurrence = ensure_occurrence(turma, local_now.date())
    if occurrence.status != 'scheduled':
        raise CheckInDomainError('class_canceled', 'Esta aula foi cancelada.')
    opens_at, closes_at, starts_at = occurrence_window(occurrence)
    if now < opens_at or now > closes_at:
        raise CheckInDomainError(
            'checkin_window_closed', 'O check-in esta fora da janela permitida.',
            opens_at=opens_at.isoformat(), closes_at=closes_at.isoformat(), starts_at=starts_at.isoformat(),
        )
    delinquent = is_student_delinquent(student, arena, local_now.date())
    if delinquent and arena.delinquent_checkin_policy == 'block':
        raise CheckInDomainError(
            'student_payment_overdue', 'Regularize sua situacao financeira antes de solicitar o check-in.',
        )
    existing = CheckIn.objects.select_for_update().filter(
        arena=arena, aluno=student, turma=turma, data=occurrence.data,
    ).first()
    if existing:
        raise CheckInDomainError(
            'checkin_already_requested', 'Ja existe um check-in para esta aula.',
            checkin_id=existing.id, checkin_status=existing.status,
        )
    try:
        return CheckIn.objects.create(
            arena=arena, aluno=student, turma=turma, ocorrencia=occurrence,
            data=occurrence.data, horario=local_now.time().replace(tzinfo=None), presente=False,
            status='pending', origem='mobile', solicitado_em=now,
            inadimplente_no_momento=delinquent,
        )
    except IntegrityError as exc:
        raise CheckInDomainError('checkin_already_requested', 'Ja existe um check-in para esta aula.') from exc


def notify_checkin(checkin, title, message):
    from notificacoes.preferences import notification_allowed
    if not notification_allowed(checkin.aluno, 'checkins', 'app'):
        return
    Notificacao.objects.create(
        arena=checkin.arena, destinatario=checkin.aluno, tipo='aula', titulo=title, mensagem=message,
    )


def expire_pending_checkins(reference_date=None):
    reference_date = reference_date or timezone.localdate()
    queryset = CheckIn.objects.filter(status='pending', data__lt=reference_date).select_related('aluno', 'arena', 'turma')
    expired = list(queryset)
    if expired:
        CheckIn.objects.filter(pk__in=[item.pk for item in expired]).update(status='expired', presente=False)
        from notificacoes.preferences import notification_allowed
        Notificacao.objects.bulk_create([
            Notificacao(
                arena=item.arena, destinatario=item.aluno, tipo='aula',
                titulo='Check-in expirado', mensagem=f'Sua solicitacao para {item.turma.nome} expirou sem validacao.',
            ) for item in expired if notification_allowed(item.aluno, 'checkins', 'app')
        ])
    return len(expired)
