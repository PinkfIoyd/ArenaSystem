from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import NotificationPreference, UserInvitation, UserPermissionOverride, UserSession, Usuario


class TeamUserSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()
    overrides = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'nome', 'first_name', 'last_name', 'email', 'tipo', 'papel', 'is_active', 'date_joined', 'overrides']

    def get_nome(self, obj):
        return obj.get_full_name() or obj.username

    def get_overrides(self, obj):
        return {item.permission: item.effect for item in obj.permission_overrides.all()}


class InvitationSerializer(serializers.ModelSerializer):
    invited_by_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = UserInvitation
        fields = ['public_id', 'email', 'role', 'status', 'expires_at', 'created_at', 'invited_by_name']

    def get_invited_by_name(self, obj):
        return obj.invited_by.get_full_name() or obj.invited_by.username if obj.invited_by else ''

    def get_status(self, obj):
        from django.utils import timezone
        if obj.accepted_at:
            return 'accepted'
        if obj.canceled_at:
            return 'canceled'
        if obj.expires_at <= timezone.now():
            return 'expired'
        return 'pending'


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=[
        ('administrador', 'Administrador'), ('recepcao', 'Recepcao'),
        ('financeiro', 'Financeiro'), ('professor', 'Professor'), ('estoque', 'Estoque'),
    ])


class InvitationAcceptSerializer(serializers.Serializer):
    invitation = serializers.UUIDField()
    token = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'As senhas nao coincidem.'})
        return attrs


class PermissionOverrideSerializer(serializers.Serializer):
    permission = serializers.CharField(max_length=100)
    effect = serializers.ChoiceField(choices=UserPermissionOverride.EFFECTS, allow_null=True)

    def validate_permission(self, value):
        from .permissions import PERMISSOES_POR_PAPEL
        known = {item for permissions in PERMISSOES_POR_PAPEL.values() for item in permissions if item != '*'}
        known.update({
            'usuarios.view', 'usuarios.manage', 'subscription.view', 'subscription.manage',
            'ownership.transfer', 'access.view', 'access.manage', 'access.override',
        })
        if value not in known:
            raise serializers.ValidationError('Permissao desconhecida.')
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    request = serializers.UUIDField()
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'As senhas nao coincidem.'})
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'telefone', 'data_nascimento', 'foto']
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True, 'max_length': 150},
            'last_name': {'required': False, 'allow_blank': True, 'max_length': 150},
            'telefone': {'required': False, 'allow_blank': True, 'max_length': 20},
            'data_nascimento': {'required': False, 'allow_null': True},
            'foto': {'required': False, 'allow_null': True},
        }

    def validate_telefone(self, value):
        normalized = ' '.join(str(value or '').split())
        allowed = set('0123456789()+- ')
        if normalized and any(char not in allowed for char in normalized):
            raise serializers.ValidationError('Informe um telefone valido.')
        return normalized


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'app_classes', 'app_checkins', 'app_financial', 'app_reservations',
            'email_classes', 'email_checkins', 'email_financial', 'email_reservations',
            'updated_at',
        ]
        read_only_fields = ['updated_at']


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    password = serializers.CharField(write_only=True, validators=[validate_password], trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('A senha atual esta incorreta.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'As senhas nao coincidem.'})
        if attrs['current_password'] == attrs['password']:
            raise serializers.ValidationError({'password': 'A nova senha deve ser diferente da atual.'})
        return attrs


class EmailChangeRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        normalized = value.strip().lower()
        user = self.context['request'].user
        if normalized == user.email.lower():
            raise serializers.ValidationError('Este ja e o e-mail atual da conta.')
        if Usuario.objects.filter(email__iexact=normalized).exclude(id=user.id).exists():
            raise serializers.ValidationError('Este e-mail ja esta em uso.')
        return normalized

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('A senha atual esta incorreta.')
        return value


class EmailChangeConfirmSerializer(serializers.Serializer):
    request = serializers.UUIDField()
    token = serializers.CharField(write_only=True)


class UserSessionSerializer(serializers.ModelSerializer):
    current = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()
    active = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            'public_id', 'device', 'user_agent', 'ip_address', 'last_seen_at',
            'created_at', 'revoked_at', 'current', 'active',
        ]

    def get_current(self, obj):
        request = self.context.get('request')
        session_id = request.auth.get('session_id') if request and request.auth else None
        return bool(session_id and str(obj.session_id) == str(session_id))

    def get_active(self, obj):
        return obj.revoked_at is None

    def get_device(self, obj):
        agent = (obj.user_agent or '').lower()
        if 'iphone' in agent or 'ipad' in agent:
            platform = 'iPhone/iPad'
        elif 'android' in agent:
            platform = 'Android'
        elif 'windows' in agent:
            platform = 'Windows'
        elif 'macintosh' in agent or 'mac os' in agent:
            platform = 'Mac'
        elif 'linux' in agent:
            platform = 'Linux'
        else:
            platform = 'Dispositivo'
        if 'edg/' in agent:
            browser = 'Edge'
        elif 'firefox/' in agent:
            browser = 'Firefox'
        elif 'chrome/' in agent and 'edg/' not in agent:
            browser = 'Chrome'
        elif 'safari/' in agent and 'chrome/' not in agent:
            browser = 'Safari'
        else:
            browser = 'Navegador'
        return f'{platform} - {browser}'
