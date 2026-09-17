import re

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from .tenant import get_user_arena
from .models import (
    AccessVisit, Arena, ArenaOperationalSettings, Matricula, Mensalidade, PlanAccessWindow,
    Plano, Quadra,
)


def arena_atual_serializer(serializer):
    request = serializer.context.get('request')
    if not request or not request.user.is_authenticated:
        return None
    return get_user_arena(request.user)


class OperationalSettingsSerializer(serializers.ModelSerializer):
    access_mode = serializers.CharField(read_only=True)

    class Meta:
        model = ArenaOperationalSettings
        fields = [
            'classes_enabled', 'open_access_enabled', 'reservations_enabled',
            'store_enabled', 'open_access_validation', 'open_access_pending_minutes',
            'access_mode',
        ]

    def validate_open_access_pending_minutes(self, value):
        if not 1 <= value <= 60:
            raise serializers.ValidationError('Use um valor entre 1 e 60 minutos.')
        return value


class ArenaSerializer(serializers.ModelSerializer):
    operational_settings = serializers.SerializerMethodField()
    terminologia = serializers.JSONField(read_only=True)
    access_mode = serializers.SerializerMethodField()

    class Meta:
        model = Arena
        fields = [
            'id', 'nome', 'slug', 'tipo_negocio', 'logo', 'cor_primaria',
            'cor_secundaria', 'cor_fundo', 'cor_texto', 'dominio',
            'checkin_minutes_before', 'checkin_minutes_after',
            'delinquent_checkin_policy', 'operational_settings', 'access_mode', 'terminologia',
        ]

    def get_operational_settings(self, obj):
        return OperationalSettingsSerializer(obj.get_operational_settings()).data

    def get_access_mode(self, obj):
        return obj.get_operational_settings().access_mode


class SaasArenaSerializer(serializers.ModelSerializer):
    total_alunos = serializers.IntegerField(read_only=True, default=0)
    total_admins = serializers.IntegerField(read_only=True, default=0)
    total_quadras = serializers.IntegerField(read_only=True, default=0)
    operational_settings = OperationalSettingsSerializer(required=False)
    terminologia = serializers.JSONField(read_only=True)
    access_mode = serializers.SerializerMethodField()

    class Meta:
        model = Arena
        fields = [
            'id', 'nome', 'slug', 'tipo_negocio', 'logo', 'cor_primaria',
            'cor_secundaria', 'cor_fundo', 'cor_texto', 'dominio',
            'status_assinatura', 'plano_contratado', 'limite_alunos',
            'limite_quadras', 'limite_admins', 'documento',
            'email_contato', 'telefone_contato', 'endereco',
            'observacoes_comerciais', 'ativa', 'criada_em',
            'checkin_minutes_before', 'checkin_minutes_after',
            'delinquent_checkin_policy',
            'total_alunos', 'total_admins', 'total_quadras',
            'operational_settings', 'access_mode', 'terminologia',
        ]
        read_only_fields = ['id', 'criada_em', 'total_alunos', 'total_admins', 'total_quadras']

    def validate(self, attrs):
        for field in ('cor_primaria', 'cor_secundaria', 'cor_fundo', 'cor_texto'):
            value = attrs.get(field, getattr(self.instance, field, None))
            if value and not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
                raise serializers.ValidationError({field: 'Use uma cor hexadecimal no formato #RRGGBB.'})
        for field in ('limite_alunos', 'limite_quadras', 'limite_admins'):
            value = attrs.get(field, getattr(self.instance, field, None))
            if value is not None and value < 1:
                raise serializers.ValidationError({field: 'O limite deve ser maior que zero.'})
        return attrs

    def get_access_mode(self, obj):
        return obj.get_operational_settings().access_mode

    def _save_operational_settings(self, arena, values=None):
        defaults = ArenaOperationalSettings.defaults_for(arena.tipo_negocio)
        settings, _ = ArenaOperationalSettings.objects.get_or_create(arena=arena, defaults=defaults)
        for field, value in (values or {}).items():
            setattr(settings, field, value)
        settings.save()
        return settings

    def create(self, validated_data):
        operational = validated_data.pop('operational_settings', None)
        arena = super().create(validated_data)
        self._save_operational_settings(arena, operational)
        return arena

    def update(self, instance, validated_data):
        operational = validated_data.pop('operational_settings', None)
        previous_type = instance.tipo_negocio
        arena = super().update(instance, validated_data)
        if operational is not None:
            self._save_operational_settings(arena, operational)
        elif previous_type != arena.tipo_negocio and not hasattr(arena, 'operational_settings'):
            self._save_operational_settings(arena)
        return arena


class SaasArenaCreateSerializer(SaasArenaSerializer):
    admin_nome = serializers.CharField(write_only=True, max_length=150)
    admin_sobrenome = serializers.CharField(write_only=True, max_length=150, required=False, allow_blank=True)
    admin_email = serializers.EmailField(write_only=True)
    admin_senha = serializers.CharField(write_only=True, validators=[validate_password], trim_whitespace=False)
    admin_senha_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta(SaasArenaSerializer.Meta):
        fields = SaasArenaSerializer.Meta.fields + [
            'admin_nome', 'admin_sobrenome', 'admin_email',
            'admin_senha', 'admin_senha_confirm',
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('admin_senha') != attrs.get('admin_senha_confirm'):
            raise serializers.ValidationError({'admin_senha_confirm': 'As senhas nao coincidem.'})
        attrs['ativa'] = attrs.get('status_assinatura', 'trial') not in {'suspensa', 'cancelada'}
        return attrs

    def create(self, validated_data):
        self.admin_data = {
            key: validated_data.pop(key, '')
            for key in ('admin_nome', 'admin_sobrenome', 'admin_email', 'admin_senha')
        }
        validated_data.pop('admin_senha_confirm', None)
        return super().create(validated_data)


class QuadraSerializer(serializers.ModelSerializer):
    ultima_manutencao = serializers.SerializerMethodField()
    proxima_manutencao = serializers.SerializerMethodField()

    class Meta:
        model = Quadra
        fields = [
            'id', 'nome', 'tipo_espaco', 'tipo_areia', 'ativa', 'observacoes',
            'ultima_manutencao', 'proxima_manutencao',
        ]

    def get_ultima_manutencao(self, obj):
        manutencao = obj.manutencoes.filter(status='concluida').order_by('-data_conclusao').first()
        return manutencao.data_conclusao if manutencao else None

    def get_proxima_manutencao(self, obj):
        manutencao = obj.manutencoes.exclude(status__in=['concluida', 'cancelada']).order_by('data_agendada').first()
        return manutencao.data_agendada if manutencao else None


class PlanAccessWindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanAccessWindow
        fields = ['id', 'weekday', 'starts_at', 'ends_at']
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['starts_at'] >= attrs['ends_at']:
            raise serializers.ValidationError('O início deve ser anterior ao fim.')
        return attrs


class PlanoSerializer(serializers.ModelSerializer):
    janelas_acesso = PlanAccessWindowSerializer(many=True, required=False)

    class Meta:
        model = Plano
        fields = [
            'id', 'nome', 'valor', 'frequencia_semanal', 'tipo_acesso',
            'limite_acessos_dia', 'limite_acessos_semana', 'limite_acessos_mes',
            'janelas_acesso', 'descricao', 'ativo',
        ]

    def validate(self, attrs):
        windows = attrs.get('janelas_acesso')
        access_type = attrs.get('tipo_acesso', getattr(self.instance, 'tipo_acesso', 'classes_only'))
        existing_windows = self.instance.janelas_acesso.exists() if self.instance else False
        if access_type in {'open_access', 'hybrid'} and windows is None and not existing_windows:
            raise serializers.ValidationError({'janelas_acesso': 'Informe ao menos uma faixa para planos com acesso livre.'})
        if access_type in {'open_access', 'hybrid'} and windows == []:
            raise serializers.ValidationError({'janelas_acesso': 'Informe ao menos uma faixa para planos com acesso livre.'})
        if access_type == 'classes_only' and windows:
            raise serializers.ValidationError({'janelas_acesso': 'Planos exclusivos de aulas nao utilizam faixas de acesso livre.'})
        frequency = attrs.get('frequencia_semanal', getattr(self.instance, 'frequencia_semanal', 0))
        if access_type in {'classes_only', 'hybrid'} and frequency < 1:
            raise serializers.ValidationError({'frequencia_semanal': 'Informe ao menos uma aula por semana.'})
        for field in ('limite_acessos_dia', 'limite_acessos_semana', 'limite_acessos_mes'):
            value = attrs.get(field, getattr(self.instance, field, None))
            if value is not None and value < 1:
                raise serializers.ValidationError({field: 'O limite deve ser maior que zero ou vazio.'})
        if windows is not None:
            grouped = {}
            for item in sorted(windows, key=lambda row: (row['weekday'], row['starts_at'])):
                previous = grouped.get(item['weekday'])
                if previous and item['starts_at'] < previous['ends_at']:
                    raise serializers.ValidationError({'janelas_acesso': 'As faixas de um mesmo dia não podem se sobrepor.'})
                grouped[item['weekday']] = item
        return attrs

    def _replace_windows(self, plan, windows):
        if windows is None:
            return
        plan.janelas_acesso.all().delete()
        PlanAccessWindow.objects.bulk_create([PlanAccessWindow(plano=plan, **item) for item in windows])

    @transaction.atomic
    def create(self, validated_data):
        windows = validated_data.pop('janelas_acesso', [])
        plan = super().create(validated_data)
        self._replace_windows(plan, windows)
        return plan

    @transaction.atomic
    def update(self, instance, validated_data):
        windows = validated_data.pop('janelas_acesso', None)
        plan = super().update(instance, validated_data)
        self._replace_windows(plan, windows)
        return plan


class MatriculaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.SerializerMethodField()
    plano_nome = serializers.CharField(source='plano.nome', read_only=True)

    class Meta:
        model = Matricula
        fields = ['id', 'aluno', 'aluno_nome', 'plano', 'plano_nome',
                  'data_inicio', 'data_fim', 'ativa']

    def get_aluno_nome(self, obj):
        return obj.aluno.get_full_name() or obj.aluno.username

    def validate(self, attrs):
        arena = arena_atual_serializer(self)
        aluno = attrs.get('aluno') or getattr(self.instance, 'aluno', None)
        plano = attrs.get('plano') or getattr(self.instance, 'plano', None)
        if arena:
            if aluno and aluno.arena_id != arena.id:
                raise serializers.ValidationError({'aluno': 'Aluno nao pertence a arena atual.'})
            if plano and plano.arena_id != arena.id:
                raise serializers.ValidationError({'plano': 'Plano nao pertence a arena atual.'})
        return attrs


class AccessVisitSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.SerializerMethodField()
    aluno_foto = serializers.SerializerMethodField()
    plano_nome = serializers.CharField(source='plano.nome', read_only=True)
    validado_por_nome = serializers.SerializerMethodField()
    checkout_por_nome = serializers.SerializerMethodField()

    class Meta:
        model = AccessVisit
        fields = [
            'id', 'public_id', 'aluno', 'aluno_nome', 'aluno_foto', 'matricula',
            'plano', 'plano_nome', 'status', 'origem', 'solicitado_em', 'expira_em',
            'validado_em', 'entrada_em', 'saida_em', 'validado_por', 'validado_por_nome',
            'checkout_por', 'checkout_por_nome', 'checkout_origem', 'motivo',
            'inadimplente_no_momento',
        ]
        read_only_fields = fields

    def get_aluno_nome(self, obj):
        return obj.aluno.get_full_name() or obj.aluno.username

    def get_aluno_foto(self, obj):
        if not obj.aluno.foto:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.aluno.foto.url) if request else obj.aluno.foto.url

    def get_validado_por_nome(self, obj):
        if not obj.validado_por:
            return ''
        return obj.validado_por.get_full_name() or obj.validado_por.username

    def get_checkout_por_nome(self, obj):
        if not obj.checkout_por:
            return ''
        return obj.checkout_por.get_full_name() or obj.checkout_por.username


class MensalidadeSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.SerializerMethodField()
    plano_nome = serializers.CharField(source='matricula.plano.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    data_atraso = serializers.DateField(read_only=True)
    checkout_url = serializers.CharField(source='mercado_pago_checkout_url', read_only=True)

    class Meta:
        model = Mensalidade
        fields = [
            'id', 'matricula', 'aluno_nome', 'plano_nome',
            'mes_referencia', 'valor', 'vencimento',
            'data_pagamento', 'status', 'status_display',
            'data_atraso', 'checkout_url',
        ]
        read_only_fields = [
            'id', 'matricula', 'aluno_nome', 'plano_nome',
            'mes_referencia', 'valor', 'vencimento',
            'data_pagamento', 'status', 'status_display',
            'data_atraso', 'checkout_url',
        ]

    def get_aluno_nome(self, obj):
        return obj.matricula.aluno.get_full_name() or obj.matricula.aluno.username
