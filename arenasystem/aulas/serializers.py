from django.utils import timezone
from rest_framework import serializers
from arena.tenant import get_user_arena
from .checkin_services import checkin_state_for
from .models import AulaOcorrencia, Turma, CheckIn


def arena_atual_serializer(serializer):
    request = serializer.context.get('request')
    if not request or not request.user.is_authenticated:
        return None
    return get_user_arena(request.user)


class TurmaSerializer(serializers.ModelSerializer):
    professor_nome = serializers.SerializerMethodField()
    quadra_nome = serializers.CharField(source='quadra.nome', read_only=True)
    vagas_disponiveis = serializers.IntegerField(read_only=True)
    matriculado = serializers.SerializerMethodField()
    checkin_hoje = serializers.SerializerMethodField()
    total_alunos = serializers.SerializerMethodField()
    checkin_state = serializers.SerializerMethodField()

    class Meta:
        model = Turma
        fields = [
            'id', 'nome', 'professor', 'professor_nome',
            'quadra', 'quadra_nome', 'dias_semana', 'horario',
            'vagas', 'vagas_disponiveis', 'ativa', 'matriculado',
            'checkin_hoje', 'total_alunos',
            'checkin_state',
        ]

    def get_professor_nome(self, obj):
        return obj.professor.get_full_name() or obj.professor.username

    def get_matriculado(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user in obj.alunos.all()
        return False

    def get_checkin_hoje(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return CheckIn.objects.filter(
            aluno=request.user,
            turma=obj,
            data=timezone.localdate(),
        ).exists()

    def get_checkin_state(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user.papel_efetivo != 'aluno':
            return None
        return checkin_state_for(obj, request.user)

    def get_total_alunos(self, obj):
        return obj.alunos.count()

    def validate(self, attrs):
        arena = arena_atual_serializer(self)
        professor = attrs.get('professor') or getattr(self.instance, 'professor', None)
        quadra = attrs.get('quadra') or getattr(self.instance, 'quadra', None)
        if arena:
            if professor and professor.arena_id != arena.id:
                raise serializers.ValidationError({'professor': 'Professor nao pertence a arena atual.'})
            if quadra and quadra.arena_id != arena.id:
                raise serializers.ValidationError({'quadra': 'Quadra nao pertence a arena atual.'})
        return attrs


class CheckInSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.SerializerMethodField()
    aluno_foto = serializers.SerializerMethodField()
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)
    professor_nome = serializers.SerializerMethodField()
    horario_previsto = serializers.TimeField(source='ocorrencia.horario_previsto', read_only=True)

    class Meta:
        model = CheckIn
        fields = [
            'id', 'aluno', 'aluno_nome', 'aluno_foto', 'turma', 'turma_nome',
            'professor_nome', 'ocorrencia', 'horario_previsto',
            'data', 'horario', 'presente', 'observacao', 'status', 'origem',
            'solicitado_em', 'validado_em', 'validado_por', 'motivo',
            'inadimplente_no_momento',
        ]
        read_only_fields = fields

    def get_aluno_nome(self, obj):
        return obj.aluno.get_full_name() or obj.aluno.username

    def get_aluno_foto(self, obj):
        if not obj.aluno.foto:
            return None
        request = self.context.get('request')
        url = obj.aluno.foto.url
        return request.build_absolute_uri(url) if request else url

    def get_professor_nome(self, obj):
        return obj.turma.professor.get_full_name() or obj.turma.professor.username


class AulaOcorrenciaSerializer(serializers.ModelSerializer):
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)
    professor_nome = serializers.SerializerMethodField()

    class Meta:
        model = AulaOcorrencia
        fields = ['public_id', 'turma', 'turma_nome', 'professor_nome', 'data', 'horario_previsto', 'status']

    def get_professor_nome(self, obj):
        return obj.turma.professor.get_full_name() or obj.turma.professor.username
from .models import SolicitacaoMatricula, FilaEspera


class SolicitacaoMatriculaSerializer(serializers.ModelSerializer):
    """Serializer completo (admin enxerga tudo)."""
    aluno_nome = serializers.SerializerMethodField()
    aluno_email = serializers.CharField(source='aluno.email', read_only=True)
    aluno_telefone = serializers.CharField(source='aluno.telefone', read_only=True)
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    respondido_por_nome = serializers.SerializerMethodField()

    class Meta:
        model = SolicitacaoMatricula
        fields = [
            'id', 'aluno', 'aluno_nome', 'aluno_email', 'aluno_telefone',
            'turma', 'turma_nome',
            'tipo', 'tipo_display',
            'status', 'status_display',
            'observacao_aluno', 'motivo_recusa',
            'data_solicitacao', 'data_resposta',
            'respondido_por', 'respondido_por_nome',
        ]
        read_only_fields = [
            'aluno', 'status', 'data_solicitacao', 'data_resposta',
            'respondido_por', 'motivo_recusa',
        ]

    def get_aluno_nome(self, obj):
        return obj.aluno.get_full_name() or obj.aluno.username

    def get_respondido_por_nome(self, obj):
        if obj.respondido_por:
            return obj.respondido_por.get_full_name() or obj.respondido_por.username
        return None


class FilaEsperaSerializer(serializers.ModelSerializer):
    """Item da fila de espera."""
    aluno_nome = serializers.SerializerMethodField()
    aluno_email = serializers.CharField(source='aluno.email', read_only=True)
    aluno_telefone = serializers.CharField(source='aluno.telefone', read_only=True)
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = FilaEspera
        fields = [
            'id', 'aluno', 'aluno_nome', 'aluno_email', 'aluno_telefone',
            'turma', 'turma_nome',
            'posicao', 'status', 'status_display',
            'data_entrada', 'data_chamada',
        ]

    def get_aluno_nome(self, obj):
        return obj.aluno.get_full_name() or obj.aluno.username
