from rest_framework import serializers

from arena.tenant import get_user_arena
from .models import AuditLog, BloqueioQuadra, ContaFinanceira, ContratoMatricula, FaixaPrecoReserva, Lead, ReservaQuadra


def arena_atual_serializer(serializer):
    request = serializer.context.get('request')
    if not request or not request.user.is_authenticated:
        return None
    return get_user_arena(request.user)


class ReservaQuadraSerializer(serializers.ModelSerializer):
    quadra_nome = serializers.CharField(source='quadra.nome', read_only=True)
    aluno_nome = serializers.SerializerMethodField()

    class Meta:
        model = ReservaQuadra
        fields = [
            'id', 'arena', 'quadra', 'quadra_nome', 'aluno', 'aluno_nome',
            'cliente_nome', 'cliente_telefone', 'data', 'hora_inicio', 'hora_fim',
            'valor', 'status', 'observacoes', 'criado_em',
        ]
        read_only_fields = ['id', 'arena', 'aluno', 'aluno_nome', 'criado_em']
        extra_kwargs = {
            'cliente_nome': {'required': False, 'allow_blank': True},
            'cliente_telefone': {'required': False, 'allow_blank': True},
            'valor': {'required': False},
        }

    def get_aluno_nome(self, obj):
        if not obj.aluno:
            return ''
        return obj.aluno.get_full_name() or obj.aluno.username

    def validate(self, attrs):
        arena = arena_atual_serializer(self)
        quadra = attrs.get('quadra') or getattr(self.instance, 'quadra', None)
        if arena and quadra and quadra.arena_id != arena.id:
            raise serializers.ValidationError({'quadra': 'Quadra nao pertence a arena atual.'})
        return attrs


class BloqueioQuadraSerializer(serializers.ModelSerializer):
    quadra_nome = serializers.CharField(source='quadra.nome', read_only=True)

    class Meta:
        model = BloqueioQuadra
        fields = [
            'id', 'arena', 'quadra', 'quadra_nome', 'data', 'hora_inicio',
            'hora_fim', 'motivo', 'categoria', 'observacoes', 'criado_em',
        ]
        read_only_fields = ['id', 'arena', 'criado_em']

    def validate(self, attrs):
        arena = arena_atual_serializer(self)
        quadra = attrs.get('quadra') or getattr(self.instance, 'quadra', None)
        if arena and quadra and quadra.arena_id != arena.id:
            raise serializers.ValidationError({'quadra': 'Quadra nao pertence a arena atual.'})
        return attrs


class FaixaPrecoReservaSerializer(serializers.ModelSerializer):
    quadra_nome = serializers.CharField(source='quadra.nome', read_only=True)

    class Meta:
        model = FaixaPrecoReserva
        fields = [
            'id', 'arena', 'quadra', 'quadra_nome', 'dia_semana',
            'hora_inicio', 'hora_fim', 'valor', 'ativa',
        ]
        read_only_fields = ['id', 'arena']

    def validate(self, attrs):
        arena = arena_atual_serializer(self)
        quadra = attrs.get('quadra') or getattr(self.instance, 'quadra', None)
        if arena and quadra and quadra.arena_id != arena.id:
            raise serializers.ValidationError({'quadra': 'Quadra nao pertence a arena atual.'})
        return attrs


class LeadSerializer(serializers.ModelSerializer):
    responsavel_nome = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            'id', 'arena', 'nome', 'telefone', 'email', 'modalidade_interesse',
            'origem', 'etapa', 'valor_potencial', 'proximo_contato',
            'motivo_perda', 'observacoes', 'responsavel', 'responsavel_nome',
            'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['id', 'arena', 'responsavel_nome', 'criado_em', 'atualizado_em']

    def get_responsavel_nome(self, obj):
        if not obj.responsavel:
            return ''
        return obj.responsavel.get_full_name() or obj.responsavel.username


class ContaFinanceiraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContaFinanceira
        fields = [
            'id', 'arena', 'tipo', 'descricao', 'categoria', 'fornecedor',
            'valor', 'vencimento', 'data_pagamento', 'status', 'observacoes',
            'criado_em',
        ]
        read_only_fields = ['id', 'arena', 'criado_em']


class ContratoMatriculaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.SerializerMethodField()
    plano_nome = serializers.CharField(source='matricula.plano.nome', read_only=True)

    class Meta:
        model = ContratoMatricula
        fields = [
            'id', 'arena', 'matricula', 'aluno_nome', 'plano_nome', 'texto',
            'status', 'data_aceite', 'ip_aceite', 'criado_em',
        ]
        read_only_fields = ['id', 'arena', 'data_aceite', 'ip_aceite', 'criado_em']

    def validate(self, attrs):
        arena = arena_atual_serializer(self)
        matricula = attrs.get('matricula') or getattr(self.instance, 'matricula', None)
        if arena and matricula and matricula.arena_id != arena.id:
            raise serializers.ValidationError({'matricula': 'Matricula nao pertence a arena atual.'})
        return attrs

    def get_aluno_nome(self, obj):
        aluno = obj.matricula.aluno
        return aluno.get_full_name() or aluno.username


class AuditLogSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()
    arena_nome = serializers.CharField(source='arena.nome', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'arena', 'arena_nome', 'usuario', 'usuario_nome', 'acao', 'entidade_tipo',
            'entidade_id', 'valores_anteriores', 'valores_novos',
            'metadados', 'ip', 'criado_em',
        ]
        read_only_fields = fields

    def get_usuario_nome(self, obj):
        if not obj.usuario:
            return ''
        return obj.usuario.get_full_name() or obj.usuario.username
