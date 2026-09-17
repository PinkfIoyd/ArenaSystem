import secrets

from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from arena.tenant import get_user_arena
from gestao.audit import registrar_auditoria

from .account_serializers import (
    EmailChangeConfirmSerializer,
    EmailChangeRequestSerializer,
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    NotificationPreferenceSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PermissionOverrideSerializer,
    TeamUserSerializer,
    UserSessionSerializer,
)
from .account_services import (
    accept_invitation, create_email_change, create_invitation, create_password_reset, token_digest,
)
from .models import (
    EmailChangeRequest, NotificationPreference, PasswordResetRequest, UserInvitation,
    UserPermissionOverride, UserSession, Usuario,
)
from .permissions import papel_usuario, require_permission
from .throttles import AccountSecurityRateThrottle


class TeamUserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeamUserSerializer
    permission_classes = [require_permission('usuarios.view')]

    def get_queryset(self):
        return Usuario.objects.filter(arena=get_user_arena(self.request.user)).exclude(tipo='aluno').prefetch_related('permission_overrides')

    @action(detail=True, methods=['post'], permission_classes=[require_permission('usuarios.manage')])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        if papel_usuario(user) == 'dono':
            return Response({'detail': 'Transfira a propriedade antes de desativar o proprietario.'}, status=status.HTTP_409_CONFLICT)
        previous = user.is_active
        user.is_active = False
        user.token_version += 1
        user.save(update_fields=['is_active', 'token_version'])
        UserSession.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())
        registrar_auditoria(request, user.arena, 'user.deactivated', user, anteriores={'is_active': previous}, novos={'is_active': False})
        return Response({'detail': 'Usuario desativado.'})

    @action(detail=True, methods=['post'], permission_classes=[require_permission('ownership.transfer')])
    def transfer_ownership(self, request, pk=None):
        if papel_usuario(request.user) != 'dono':
            return Response({'detail': 'Somente o proprietario atual pode transferir a propriedade.'}, status=status.HTTP_403_FORBIDDEN)
        target = self.get_object()
        if target.id == request.user.id or not target.is_active:
            return Response({'detail': 'Escolha outro usuario ativo da arena.'}, status=status.HTTP_409_CONFLICT)
        with transaction.atomic():
            current = Usuario.objects.select_for_update().get(id=request.user.id)
            target = Usuario.objects.select_for_update().get(id=target.id)
            current.papel = 'administrador'
            target.papel = 'dono'
            target.tipo = 'admin_arena'
            target.is_staff = True
            current.save(update_fields=['papel'])
            target.save(update_fields=['papel', 'tipo', 'is_staff'])
            registrar_auditoria(
                request, current.arena, 'ownership.transferred', target,
                anteriores={'owner_id': current.id}, novos={'owner_id': target.id},
            )
        return Response({'detail': 'Propriedade transferida.', 'owner': TeamUserSerializer(target).data})

    @action(detail=True, methods=['post'], permission_classes=[require_permission('usuarios.manage')])
    def permissions(self, request, pk=None):
        user = self.get_object()
        serializer = PermissionOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission = serializer.validated_data['permission']
        effect = serializer.validated_data['effect']
        if papel_usuario(user) == 'dono' and permission in {'usuarios.manage', 'subscription.manage', 'ownership.transfer'} and effect == 'deny':
            return Response({'detail': 'Permissao essencial do proprietario nao pode ser negada.'}, status=status.HTTP_409_CONFLICT)
        if effect is None:
            UserPermissionOverride.objects.filter(user=user, permission=permission).delete()
        else:
            UserPermissionOverride.objects.update_or_create(
                user=user, permission=permission, defaults={'effect': effect},
            )
        registrar_auditoria(
            request, user.arena, 'user.permission_override_changed', user,
            novos={'permission': permission, 'effect': effect or 'default'},
        )
        return Response(TeamUserSerializer(user).data)


class InvitationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = InvitationSerializer
    permission_classes = [require_permission('usuarios.manage')]
    lookup_field = 'public_id'

    def get_queryset(self):
        return UserInvitation.objects.filter(arena=get_user_arena(self.request.user)).select_related('invited_by')

    def create(self, request, *args, **kwargs):
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        arena = get_user_arena(request.user)
        try:
            invitation = create_invitation(arena, invited_by=request.user, **serializer.validated_data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
        registrar_auditoria(request, arena, 'user.invitation_created', invitation, novos={'email': invitation.email, 'role': invitation.role})
        return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, public_id=None):
        invitation = self.get_object()
        if invitation.accepted_at:
            return Response({'detail': 'Convite ja utilizado.'}, status=status.HTTP_409_CONFLICT)
        invitation.canceled_at = timezone.now()
        invitation.save(update_fields=['canceled_at'])
        registrar_auditoria(request, invitation.arena, 'user.invitation_canceled', invitation)
        return Response(InvitationSerializer(invitation).data)

    @action(detail=True, methods=['post'])
    def resend(self, request, public_id=None):
        invitation = self.get_object()
        if invitation.accepted_at:
            return Response({'detail': 'Convite ja utilizado.'}, status=status.HTTP_409_CONFLICT)
        invitation.canceled_at = timezone.now()
        invitation.save(update_fields=['canceled_at'])
        try:
            new_invitation = create_invitation(invitation.arena, invitation.email, invitation.role, request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(InvitationSerializer(new_invitation).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def accept_user_invitation(request):
    serializer = InvitationAcceptSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    invitation = UserInvitation.objects.filter(public_id=serializer.validated_data['invitation']).first()
    if not invitation:
        return Response({'detail': 'Convite invalido.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = accept_invitation(
            invitation, serializer.validated_data['token'], serializer.validated_data['first_name'],
            serializer.validated_data.get('last_name', ''), serializer.validated_data['password'],
        )
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Convite aceito.', 'username': user.username}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_password_reset(request):
    email = str(request.data.get('email', '')).strip().lower()
    if email:
        for user in Usuario.objects.filter(email__iexact=email, is_active=True):
            create_password_reset(user)
    return Response({'detail': 'Se houver uma conta ativa, enviaremos as instrucoes.'}, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def confirm_password_reset(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reset = PasswordResetRequest.objects.select_related('user').filter(public_id=serializer.validated_data['request']).first()
    valid = bool(
        reset and not reset.used_at and reset.expires_at > timezone.now()
        and secrets.compare_digest(reset.token_hash, token_digest(serializer.validated_data['token']))
    )
    if not valid:
        return Response({'detail': 'Solicitacao invalida ou expirada.'}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        reset = PasswordResetRequest.objects.select_for_update().get(id=reset.id)
        user = Usuario.objects.select_for_update().get(id=reset.user_id)
        user.set_password(serializer.validated_data['password'])
        user.token_version += 1
        user.save(update_fields=['password', 'token_version'])
        reset.used_at = timezone.now()
        reset.save(update_fields=['used_at'])
        UserSession.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())
        registrar_auditoria(
            request, user.arena, 'account.password_reset_completed', user, usuario=user,
        )
    return Response({'detail': 'Senha redefinida. Entre novamente.'})


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def notification_preferences(request):
    preference, _ = NotificationPreference.objects.get_or_create(user=request.user)
    if request.method == 'PATCH':
        before = NotificationPreferenceSerializer(preference).data
        serializer = NotificationPreferenceSerializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        preference = serializer.save()
        registrar_auditoria(
            request, request.user.arena, 'account.notification_preferences_updated', preference,
            anteriores=before, novos=NotificationPreferenceSerializer(preference).data,
        )
    return Response(NotificationPreferenceSerializer(preference).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        user = Usuario.objects.select_for_update().get(id=request.user.id)
        user.set_password(serializer.validated_data['password'])
        user.save(update_fields=['password'])
        session_id = request.auth.get('session_id') if request.auth else None
        other_sessions = UserSession.objects.filter(user=user, revoked_at__isnull=True)
        if session_id:
            other_sessions = other_sessions.exclude(session_id=session_id)
        revoked = other_sessions.update(revoked_at=timezone.now())
        registrar_auditoria(
            request, user.arena, 'account.password_changed', user,
            metadados={'other_sessions_revoked': revoked},
        )
    return Response({'detail': 'Senha alterada com sucesso.', 'other_sessions_revoked': revoked})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_email_change(request):
    serializer = EmailChangeRequestSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    change = create_email_change(request.user, serializer.validated_data['email'])
    registrar_auditoria(
        request, request.user.arena, 'account.email_change_requested', change,
        novos={'new_email': change.new_email, 'expires_at': change.expires_at.isoformat()},
    )
    return Response(
        {'detail': 'Enviamos um link de confirmacao para o novo e-mail.', 'expires_at': change.expires_at},
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def confirm_email_change(request):
    serializer = EmailChangeConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    change = EmailChangeRequest.objects.select_related('user').filter(
        public_id=serializer.validated_data['request'],
    ).first()
    valid = bool(
        change and not change.used_at and change.expires_at > timezone.now()
        and secrets.compare_digest(change.token_hash, token_digest(serializer.validated_data['token']))
    )
    if not valid:
        return Response({'detail': 'Solicitacao invalida ou expirada.'}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        change = EmailChangeRequest.objects.select_for_update().get(id=change.id)
        if change.used_at or change.expires_at <= timezone.now():
            return Response({'detail': 'Solicitacao invalida ou expirada.'}, status=status.HTTP_400_BAD_REQUEST)
        if Usuario.objects.filter(email__iexact=change.new_email).exclude(id=change.user_id).exists():
            return Response({'detail': 'Este e-mail ja esta em uso.'}, status=status.HTTP_409_CONFLICT)
        user = Usuario.objects.select_for_update().get(id=change.user_id)
        previous_email = user.email
        user.email = change.new_email
        user.save(update_fields=['email'])
        change.used_at = timezone.now()
        change.save(update_fields=['used_at'])
        EmailChangeRequest.objects.filter(user=user, used_at__isnull=True).exclude(id=change.id).update(used_at=timezone.now())
        registrar_auditoria(
            request, user.arena, 'account.email_changed', user,
            anteriores={'email': previous_email}, novos={'email': user.email},
            usuario=user,
        )
    return Response({'detail': 'E-mail confirmado e atualizado com sucesso.'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sessions(request):
    queryset = UserSession.objects.filter(user=request.user, revoked_at__isnull=True)
    return Response(UserSessionSerializer(queryset, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def revoke_session(request, public_id):
    session = UserSession.objects.filter(user=request.user, public_id=public_id).first()
    if not session:
        return Response({'detail': 'Sessao nao encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    session.revoked_at = timezone.now()
    session.save(update_fields=['revoked_at'])
    current_session_id = request.auth.get('session_id') if request.auth else None
    is_current = bool(current_session_id and str(session.session_id) == str(current_session_id))
    registrar_auditoria(
        request, request.user.arena, 'account.session_revoked', session,
        metadados={
            'session_public_id': str(session.public_id),
            'device': UserSessionSerializer(session).data['device'],
            'current': is_current,
        },
    )
    return Response({'detail': 'Sessao encerrada.', 'current': is_current})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_others(request):
    session_id = request.auth.get('session_id') if request.auth else None
    queryset = UserSession.objects.filter(user=request.user, revoked_at__isnull=True)
    if session_id:
        queryset = queryset.exclude(session_id=session_id)
    revoked = queryset.update(revoked_at=timezone.now())
    registrar_auditoria(
        request, request.user.arena, 'account.other_sessions_revoked', request.user,
        metadados={'sessions_revoked': revoked},
    )
    return Response({'detail': 'Outras sessoes encerradas.', 'sessions_revoked': revoked})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_current(request):
    session_id = request.auth.get('session_id') if request.auth else None
    if session_id:
        UserSession.objects.filter(user=request.user, session_id=session_id).update(revoked_at=timezone.now())
    refresh = request.data.get('refresh')
    if refresh:
        try:
            RefreshToken(refresh).blacklist()
        except Exception:
            pass
    registrar_auditoria(request, request.user.arena, 'account.logged_out', request.user)
    return Response({'detail': 'Sessao encerrada.'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_all(request):
    user = Usuario.objects.get(id=request.user.id)
    user.token_version += 1
    user.save(update_fields=['token_version'])
    UserSession.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())
    registrar_auditoria(request, user.arena, 'account.all_sessions_revoked', user)
    return Response({'detail': 'Todas as sessoes foram encerradas.'})


change_password.cls.throttle_classes = [AccountSecurityRateThrottle]
request_email_change.cls.throttle_classes = [AccountSecurityRateThrottle]
