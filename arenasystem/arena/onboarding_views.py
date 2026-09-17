import csv
import io
import re
from datetime import date

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from aulas.models import Turma
from gestao.audit import registrar_auditoria
from saas_billing.services import effective_limits, subscription_usage
from usuarios.account_services import create_invitation, create_password_reset, generate_unique_username
from usuarios.models import Usuario
from usuarios.permissions import papel_usuario

from .models import (
    ArenaBusinessHours, ArenaOnboarding, Matricula,
    Modalidade, Plano, Quadra,
)
from .tenant import get_user_arena


STEPS = ['identification', 'hours', 'courts', 'modalities', 'professors', 'students', 'review']


def _owner_guard(request):
    if papel_usuario(request.user) != 'dono':
        return Response({'detail': 'Somente o proprietario pode concluir o onboarding.'}, status=status.HTTP_403_FORBIDDEN)
    return None


def _progress(arena):
    return ArenaOnboarding.objects.get_or_create(arena=arena)[0]


def _payload(arena):
    progress = _progress(arena)
    operational = arena.get_operational_settings()
    return {
        'current_step': progress.current_step,
        'completed_steps': progress.completed_steps,
        'completed_at': progress.completed_at,
        'steps': STEPS,
        'tipo_negocio': arena.tipo_negocio,
        'terminologia': arena.terminologia,
        'operational_settings': {
            'classes_enabled': operational.classes_enabled,
            'open_access_enabled': operational.open_access_enabled,
            'reservations_enabled': operational.reservations_enabled,
            'store_enabled': operational.store_enabled,
            'open_access_validation': operational.open_access_validation,
            'open_access_pending_minutes': operational.open_access_pending_minutes,
            'access_mode': operational.access_mode,
        },
        'summary': {
            'hours': arena.business_hours.count(),
            'courts': arena.quadras.filter(ativa=True).count(),
            'modalities': arena.modalidades.filter(ativa=True).count(),
            'professors': arena.usuarios.filter(tipo='professor', is_active=True).count(),
            'students': arena.usuarios.filter(tipo='aluno', is_active=True).count(),
        },
    }


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def onboarding_status(request):
    arena = get_user_arena(request.user)
    return Response({
        **_payload(arena),
        'arena': {
            'nome': arena.nome, 'email_contato': arena.email_contato,
            'telefone_contato': arena.telefone_contato, 'endereco': arena.endereco,
            'cor_primaria': arena.cor_primaria, 'cor_secundaria': arena.cor_secundaria,
            'tipo_negocio': arena.tipo_negocio,
        },
        'hours': list(arena.business_hours.values('weekday', 'opens_at', 'closes_at', 'closed')),
        'courts': list(arena.quadras.values('id', 'nome', 'tipo_espaco', 'tipo_areia', 'ativa')),
        'modalities': list(arena.modalidades.values('id', 'nome', 'cor', 'ativa')),
    })


def _save_identification(arena, data):
    fields = ['nome', 'email_contato', 'telefone_contato', 'endereco', 'cor_primaria', 'cor_secundaria', 'cor_fundo', 'cor_texto']
    for field in fields:
        if field in data:
            value = str(data[field]).strip()
            if field.startswith('cor_') and not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
                raise ValueError(f'{field}: use o formato #RRGGBB.')
            setattr(arena, field, value)
    if not arena.nome or not arena.email_contato:
        raise ValueError('Nome e e-mail de contato sao obrigatorios.')
    arena.save(update_fields=[field for field in fields if field in data])


def _save_modules(arena, data):
    allowed = {
        'classes_enabled', 'open_access_enabled', 'reservations_enabled',
        'store_enabled', 'open_access_validation', 'open_access_pending_minutes',
    }
    payload = data.get('operational_settings', data)
    settings = arena.get_operational_settings()
    for field in allowed:
        if field in payload:
            setattr(settings, field, payload[field])
    if settings.open_access_validation not in {'reception', 'automatic'}:
        raise ValueError('Selecione uma forma valida de validacao do acesso livre.')
    if not 1 <= int(settings.open_access_pending_minutes) <= 60:
        raise ValueError('A validade da solicitacao deve ficar entre 1 e 60 minutos.')
    if not any((settings.classes_enabled, settings.open_access_enabled)):
        raise ValueError('Habilite aulas ou acesso livre para continuar.')
    settings.save()


def _save_hours(arena, data):
    items = data.get('items', [])
    if not isinstance(items, list) or len(items) != 7:
        raise ValueError('Informe os sete dias da semana.')
    weekdays = {item.get('weekday') for item in items}
    if weekdays != set(range(7)):
        raise ValueError('Cada dia da semana deve aparecer uma unica vez.')
    with transaction.atomic():
        for item in items:
            closed = bool(item.get('closed'))
            opens_at = item.get('opens_at') or None
            closes_at = item.get('closes_at') or None
            if not closed and (not opens_at or not closes_at or opens_at >= closes_at):
                raise ValueError('Em dias abertos, o fechamento deve ser posterior a abertura.')
            ArenaBusinessHours.objects.update_or_create(
                arena=arena, weekday=item['weekday'],
                defaults={'closed': closed, 'opens_at': None if closed else opens_at, 'closes_at': None if closed else closes_at},
            )


def _save_courts(arena, data):
    items = data.get('items', [])
    if not items:
        raise ValueError(f"Cadastre pelo menos um(a) {arena.terminologia['espaco_singular']}.")
    subscription = getattr(arena, 'saas_subscription', None)
    if subscription and len(items) > effective_limits(subscription)['courts']:
        raise ValueError(f"A quantidade de {arena.terminologia['espaco_plural']} ultrapassa o limite do plano.")
    with transaction.atomic():
        for item in items:
            name = str(item.get('nome', '')).strip()
            if not name:
                raise ValueError(f"Todo(a) {arena.terminologia['espaco_singular']} precisa de nome.")
            space_type = str(item.get('tipo_espaco') or ('court' if arena.tipo_negocio == 'arena' else 'other')).strip()
            if space_type not in dict(Quadra.SPACE_TYPES):
                raise ValueError('Selecione um tipo de espaco valido.')
            Quadra.objects.update_or_create(
                arena=arena, nome=name,
                defaults={
                    'tipo_espaco': space_type,
                    'tipo_areia': str(item.get('tipo_areia', '')).strip(),
                    'ativa': bool(item.get('ativa', True)),
                },
            )


def _save_modalities(arena, data):
    items = data.get('items', [])
    if not items:
        raise ValueError('Cadastre pelo menos uma modalidade.')
    with transaction.atomic():
        for item in items:
            name = str(item.get('nome', '')).strip()
            color = str(item.get('cor', '#0F766E')).strip()
            if not name or not re.fullmatch(r'#[0-9A-Fa-f]{6}', color):
                raise ValueError('Informe nome e cor hexadecimal valida para cada modalidade.')
            Modalidade.objects.update_or_create(arena=arena, nome=name, defaults={'cor': color, 'ativa': True})


def _save_professors(arena, data, user):
    items = data.get('items', [])
    for item in items:
        email = str(item.get('email', '')).strip()
        if not email:
            raise ValueError('Informe o e-mail de cada professor.')
        create_invitation(arena, email, 'professor', user)


SAVE_HANDLERS = {
    'identification': _save_identification,
    'hours': _save_hours,
    'courts': _save_courts,
    'modalities': _save_modalities,
}


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_onboarding_step(request, step):
    denied = _owner_guard(request)
    if denied:
        return denied
    if step not in STEPS:
        return Response({'detail': 'Etapa desconhecida.'}, status=status.HTTP_404_NOT_FOUND)
    arena = get_user_arena(request.user)
    try:
        if step == 'professors':
            _save_professors(arena, request.data, request.user)
        elif step in SAVE_HANDLERS:
            SAVE_HANDLERS[step](arena, request.data)
            if step == 'identification' and 'operational_settings' in request.data:
                _save_modules(arena, request.data)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    progress = _progress(arena)
    completed = list(progress.completed_steps)
    if step not in completed:
        completed.append(step)
    progress.completed_steps = completed
    current_index = STEPS.index(step)
    progress.current_step = STEPS[min(current_index + 1, len(STEPS) - 1)]
    progress.save(update_fields=['completed_steps', 'current_step', 'updated_at'])
    registrar_auditoria(request, arena, 'onboarding.step_completed', progress, novos={'step': step})
    return Response(_payload(arena))


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_onboarding(request):
    denied = _owner_guard(request)
    if denied:
        return denied
    arena = get_user_arena(request.user)
    progress = _progress(arena)
    required = {'identification', 'hours', 'courts', 'modalities'}
    missing = sorted(required.difference(progress.completed_steps))
    if missing:
        return Response({'detail': 'Conclua as etapas obrigatorias.', 'missing_steps': missing}, status=status.HTTP_409_CONFLICT)
    progress.completed_at = timezone.now()
    progress.current_step = 'review'
    progress.save(update_fields=['completed_at', 'current_step', 'updated_at'])
    registrar_auditoria(request, arena, 'onboarding.completed', progress)
    return Response(_payload(arena))


CSV_COLUMNS = ['first_name', 'last_name', 'email', 'telefone', 'cpf', 'data_nascimento', 'plano', 'turma']


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def student_import_template(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="modelo-importacao-alunos.csv"'
    response.write('\ufeff' + ','.join(CSV_COLUMNS) + '\r\n')
    return response


def _parse_student_csv(file, arena):
    if file.size > 5 * 1024 * 1024:
        raise ValueError('O arquivo deve ter no maximo 5 MB.')
    try:
        text = file.read().decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('Envie um CSV UTF-8.') from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not {'first_name', 'email'}.issubset(reader.fieldnames):
        raise ValueError('O CSV precisa conter first_name e email.')
    rows = list(reader)
    if len(rows) > 5000:
        raise ValueError('O arquivo deve ter no maximo 5.000 linhas.')
    seen = set()
    valid = []
    errors = []
    for number, row in enumerate(rows, start=2):
        email = str(row.get('email', '')).strip().lower()
        first_name = str(row.get('first_name', '')).strip()
        row_errors = []
        if not first_name:
            row_errors.append('first_name obrigatorio')
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            row_errors.append('email invalido')
        if email in seen:
            row_errors.append('email duplicado no arquivo')
        seen.add(email)
        if Usuario.objects.filter(arena=arena, email__iexact=email).exists():
            row_errors.append('email ja cadastrado na arena')
        birth = str(row.get('data_nascimento', '')).strip()
        if birth:
            try:
                date.fromisoformat(birth)
            except ValueError:
                row_errors.append('data_nascimento deve usar AAAA-MM-DD')
        plan = None
        class_group = None
        if row.get('plano'):
            plan = Plano.objects.filter(arena=arena, nome__iexact=row['plano'].strip(), ativo=True).first()
            if not plan:
                row_errors.append('plano nao encontrado')
        if row.get('turma'):
            class_group = Turma.objects.filter(arena=arena, nome__iexact=row['turma'].strip(), ativa=True).first()
            if not class_group:
                row_errors.append('turma nao encontrada')
        if row_errors:
            errors.append({'line': number, 'email': email, 'errors': row_errors})
        else:
            valid.append({'line': number, 'data': row, 'email': email, 'plan': plan, 'class_group': class_group})
    return rows, valid, errors


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def import_students(request):
    denied = _owner_guard(request)
    if denied:
        return denied
    file = request.FILES.get('file')
    if not file:
        return Response({'detail': 'Envie o arquivo no campo file.'}, status=status.HTTP_400_BAD_REQUEST)
    arena = get_user_arena(request.user)
    try:
        rows, valid, errors = _parse_student_csv(file, arena)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    dry_run = str(request.data.get('dry_run', 'true')).lower() not in {'false', '0', 'no'}
    subscription = getattr(arena, 'saas_subscription', None)
    active_new = len({item['email'] for item in valid if item['plan']})
    if subscription:
        usage = subscription_usage(arena)['students']
        limit = effective_limits(subscription)['students']
        if usage + active_new > limit:
            errors.append({'line': 0, 'email': '', 'errors': [f'importacao excede o limite de alunos ativos ({usage}/{limit})']})
    report = {'total': len(rows), 'valid': len(valid), 'rejected': len(errors), 'errors': errors[:500], 'dry_run': dry_run}
    if dry_run or errors:
        return Response(report, status=status.HTTP_200_OK if dry_run else status.HTTP_400_BAD_REQUEST)

    created_users = []
    with transaction.atomic():
        for item in valid:
            row = item['data']
            user = Usuario(
                username=generate_unique_username(item['email'], arena), email=item['email'],
                first_name=str(row.get('first_name', '')).strip(), last_name=str(row.get('last_name', '')).strip(),
                telefone=str(row.get('telefone', '')).strip(), cpf=str(row.get('cpf', '')).strip(),
                data_nascimento=date.fromisoformat(row['data_nascimento'].strip()) if row.get('data_nascimento', '').strip() else None,
                tipo='aluno', papel='aluno', arena=arena,
            )
            user.set_unusable_password()
            user.save()
            if item['plan']:
                enrollment = Matricula.objects.create(
                    arena=arena, aluno=user, plano=item['plan'], data_inicio=timezone.localdate(), ativa=True,
                )
                if item['class_group']:
                    item['class_group'].alunos.add(user)
            created_users.append(user)
    for user in created_users:
        try:
            create_password_reset(user)
        except Exception:
            pass
    progress = _progress(arena)
    if 'students' not in progress.completed_steps:
        progress.completed_steps = [*progress.completed_steps, 'students']
        progress.save(update_fields=['completed_steps', 'updated_at'])
    registrar_auditoria(request, arena, 'onboarding.students_imported', progress, novos={'count': len(created_users)})
    return Response({**report, 'imported': len(created_users), 'dry_run': False}, status=status.HTTP_201_CREATED)
