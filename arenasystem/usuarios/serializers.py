from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from arena.models import Arena
from arena.tenant import get_default_arena
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    nome_completo = serializers.SerializerMethodField()
    arena_nome = serializers.CharField(source='arena.nome', read_only=True)
    onboarding_completed = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'nome_completo',
            'email', 'tipo', 'telefone', 'data_nascimento', 'foto', 'cpf',
            'is_staff', 'arena', 'arena_nome', 'papel', 'papel_efetivo',
            'onboarding_completed',
        ]
        read_only_fields = ['id', 'tipo', 'arena', 'arena_nome', 'papel', 'papel_efetivo']

    def get_nome_completo(self, obj):
        return obj.get_full_name() or obj.username

    def get_onboarding_completed(self, obj):
        if not obj.arena_id:
            return True
        try:
            return bool(obj.arena.onboarding.completed_at)
        except Exception:
            return False


class CadastroAlunoSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    arena_slug = serializers.SlugField(write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = [
            'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'email',
            'telefone', 'data_nascimento', 'cpf', 'arena_slug',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'As senhas nao coincidem.'})
        arena_slug = attrs.get('arena_slug')
        arena = Arena.objects.filter(slug=arena_slug, ativa=True).first()
        if not arena:
            raise serializers.ValidationError({'arena_slug': 'Selecione uma arena ativa para continuar.'})
        attrs['arena'] = arena
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        validated_data.pop('arena_slug')
        password = validated_data.pop('password')
        arena = validated_data.pop('arena')
        user = Usuario(**validated_data)
        user.tipo = 'aluno'
        user.arena = arena
        user.set_password(password)
        user.save()
        return user


class AdminAlunoSerializer(serializers.ModelSerializer):
    nome_completo = serializers.SerializerMethodField()
    total_turmas = serializers.SerializerMethodField()
    mensalidades_em_aberto = serializers.SerializerMethodField()
    arena_nome = serializers.CharField(source='arena.nome', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'nome_completo', 'cpf', 'telefone', 'data_nascimento',
            'tipo', 'papel', 'is_active', 'date_joined', 'arena', 'arena_nome',
            'total_turmas', 'mensalidades_em_aberto',
        ]
        read_only_fields = ['id', 'date_joined', 'nome_completo', 'arena', 'arena_nome']

    def get_nome_completo(self, obj):
        nome = f'{obj.first_name} {obj.last_name}'.strip()
        return nome or obj.username

    def get_total_turmas(self, obj):
        return obj.turmas.filter(arena=obj.arena).count() if hasattr(obj, 'turmas') else 0

    def get_mensalidades_em_aberto(self, obj):
        from arena.models import Mensalidade
        return Mensalidade.objects.filter(
            arena=obj.arena,
            matricula__aluno=obj,
            status__in=['pendente', 'atrasado'],
        ).count()


class CriarAlunoSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'cpf', 'telefone', 'data_nascimento', 'senha',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'username': {'required': False, 'allow_blank': True},
        }

    def validate_email(self, value):
        arena = self._arena()
        if Usuario.objects.filter(email=value, arena=arena).exists():
            raise serializers.ValidationError('Ja existe um usuario com este e-mail nesta arena.')
        return value

    def validate_username(self, value):
        if not value:
            return value
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este username ja esta em uso.')
        return value

    def _arena(self):
        request = self.context.get('request')
        return getattr(request.user, 'arena', None) if request and request.user.is_authenticated else get_default_arena()

    def _gerar_username_unico(self, email):
        base = email.split('@')[0] or 'aluno'
        username = base
        contador = 1
        while Usuario.objects.filter(username=username).exists():
            contador += 1
            username = f'{base}{contador}'
        return username

    def create(self, validated_data):
        senha = validated_data.pop('senha', None)
        if not senha:
            import secrets
            senha = secrets.token_urlsafe(8)

        if not validated_data.get('username'):
            validated_data['username'] = self._gerar_username_unico(validated_data['email'])

        usuario = Usuario(**validated_data)
        usuario.tipo = 'aluno'
        usuario.arena = self._arena()
        usuario.set_password(senha)
        usuario.save()
        usuario._senha_temporaria = senha
        return usuario
