import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from notificacoes.tasks import send_transactional_email
from saas_billing.services import assert_plan_capacity

from .models import EmailChangeRequest, PasswordResetRequest, UserInvitation, Usuario


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def generate_secret():
    return secrets.token_urlsafe(32)


def generate_unique_username(email, arena):
    local = slugify(email.split('@')[0]) or 'usuario'
    base = f'{arena.slug}-{local}'[:140]
    username = base
    index = 1
    while Usuario.objects.filter(username=username).exists():
        index += 1
        username = f'{base[:145 - len(str(index))]}-{index}'
    return username


def create_invitation(arena, email, role, invited_by):
    if role in {'dono', 'superadmin_saas', 'aluno'}:
        raise ValueError('Use a transferencia de propriedade para definir um proprietario.')
    resource = 'professors' if role == 'professor' else 'admins'
    assert_plan_capacity(arena, resource)
    if Usuario.objects.filter(arena=arena, email__iexact=email, is_active=True).exists():
        raise ValueError('Ja existe um usuario ativo com este e-mail na arena.')
    secret = generate_secret()
    invitation = UserInvitation.objects.create(
        arena=arena,
        email=email.lower().strip(),
        role=role,
        token_hash=token_digest(secret),
        invited_by=invited_by,
        expires_at=timezone.now() + timedelta(hours=72),
    )
    url = f'{settings.FRONTEND_URL}/aceitar-convite?invitation={invitation.public_id}&token={secret}'
    send_transactional_email.delay(
        f'Convite para {arena.nome}',
        f'Voce foi convidado para acessar {arena.nome}. O link expira em 72 horas: {url}',
        [invitation.email],
    )
    invitation._raw_token = secret
    return invitation


@transaction.atomic
def accept_invitation(invitation, token, first_name, last_name, password):
    invitation = UserInvitation.objects.select_for_update().select_related('arena').get(pk=invitation.pk)
    if invitation.accepted_at or invitation.canceled_at or invitation.expires_at <= timezone.now():
        raise ValueError('Convite expirado, cancelado ou ja utilizado.')
    if not secrets.compare_digest(invitation.token_hash, token_digest(token)):
        raise ValueError('Convite invalido.')
    resource = 'professors' if invitation.role == 'professor' else 'admins'
    assert_plan_capacity(invitation.arena, resource)
    user = Usuario.objects.filter(arena=invitation.arena, email__iexact=invitation.email).first()
    if user and user.is_active:
        raise ValueError('Ja existe um usuario ativo com este e-mail.')
    if not user:
        user = Usuario(
            username=generate_unique_username(invitation.email, invitation.arena),
            email=invitation.email,
            arena=invitation.arena,
        )
    user.first_name = first_name
    user.last_name = last_name
    user.papel = invitation.role
    user.tipo = 'professor' if invitation.role == 'professor' else 'admin_arena'
    user.is_staff = invitation.role != 'professor'
    user.is_active = True
    user.set_password(password)
    user.save()
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=['accepted_at'])
    return user


def create_password_reset(user):
    secret = generate_secret()
    reset = PasswordResetRequest.objects.create(
        user=user,
        token_hash=token_digest(secret),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    url = f'{settings.FRONTEND_URL}/redefinir-senha?request={reset.public_id}&token={secret}'
    send_transactional_email.delay(
        'Redefinicao de senha ArenaFlow',
        f'Use este link em ate uma hora para redefinir sua senha: {url}',
        [user.email],
    )
    reset._raw_token = secret
    return reset


def create_email_change(user, new_email):
    EmailChangeRequest.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    secret = generate_secret()
    change = EmailChangeRequest.objects.create(
        user=user,
        new_email=new_email.strip().lower(),
        token_hash=token_digest(secret),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    url = f'{settings.FRONTEND_URL}/confirmar-email?request={change.public_id}&token={secret}'
    send_transactional_email.delay(
        'Confirme seu novo e-mail no ArenaFlow',
        f'Use este link em ate uma hora para confirmar seu novo e-mail: {url}',
        [change.new_email],
    )
    change._raw_token = secret
    return change
