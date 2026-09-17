from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Turma(models.Model):
    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='turmas')
    nome = models.CharField(max_length=100)
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='turmas_lecionadas',
        limit_choices_to={'tipo': 'professor'}
    )
    quadra = models.ForeignKey('arena.Quadra', on_delete=models.PROTECT)
    modalidade = models.ForeignKey(
        'arena.Modalidade', on_delete=models.PROTECT, related_name='turmas', null=True, blank=True,
    )
    dias_semana = models.CharField(max_length=50, help_text="Ex: seg,qua,sex")
    horario = models.TimeField()
    vagas = models.PositiveSmallIntegerField(default=8)
    alunos = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='turmas',
        limit_choices_to={'tipo': 'aluno'},
        blank=True
    )
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} - {self.horario.strftime('%H:%M')}"
    @property
    def vagas_disponiveis(self):
        return self.vagas - self.alunos.count()


class AulaOcorrencia(models.Model):
    STATUS = [('scheduled', 'Agendada'), ('canceled', 'Cancelada')]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='aulas_ocorrencias')
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='ocorrencias')
    data = models.DateField(db_index=True)
    horario_previsto = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS, default='scheduled', db_index=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data', 'horario_previsto']
        constraints = [
            models.UniqueConstraint(fields=['turma', 'data'], name='unique_aula_ocorrencia_turma_data'),
        ]

    def __str__(self):
        return f'{self.turma} - {self.data:%d/%m/%Y}'


class CheckIn(models.Model):
    STATUS = [
        ('pending', 'Aguardando validacao'),
        ('confirmed', 'Confirmado'),
        ('rejected', 'Rejeitado'),
        ('expired', 'Expirado'),
        ('absent', 'Ausente'),
    ]
    ORIGINS = [
        ('mobile', 'Aplicativo mobile'),
        ('manual', 'Registro manual'),
        ('legacy', 'Registro legado'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='checkins')
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo': 'aluno'}
    )
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='checkins')
    ocorrencia = models.ForeignKey(
        AulaOcorrencia, on_delete=models.PROTECT, related_name='checkins', null=True, blank=True,
    )
    data = models.DateField(default=timezone.now)
    horario = models.TimeField(default=timezone.now)
    presente = models.BooleanField(default=True)
    observacao = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='confirmed', db_index=True)
    origem = models.CharField(max_length=20, choices=ORIGINS, default='legacy')
    solicitado_em = models.DateTimeField(null=True, blank=True)
    validado_em = models.DateTimeField(null=True, blank=True)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='checkins_validados',
    )
    motivo = models.CharField(max_length=300, blank=True)
    inadimplente_no_momento = models.BooleanField(default=False)

    class Meta:
        ordering = ['-data', '-horario']
        unique_together = ('aluno', 'turma', 'data')

    def __str__(self):
        status = "✓" if self.presente else "✗"
        return f"{status} {self.aluno} - {self.turma} - {self.data.strftime('%d/%m/%Y')}"
# ─────────────────────────────────────────────
#   SOLICITAÇÕES DE MATRÍCULA
# ─────────────────────────────────────────────

class SolicitacaoMatricula(models.Model):
    """Solicitação de um aluno para entrar em uma turma."""
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('recusada', 'Recusada'),
        ('cancelada', 'Cancelada pelo aluno'),
    ]

    TIPO_CHOICES = [
        ('matricula', 'Solicitação de Matrícula'),
        ('cancelamento', 'Solicitação de Cancelamento'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='solicitacoes_matricula')
    aluno = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='solicitacoes',
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='solicitacoes',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='matricula')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    respondido_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='solicitacoes_respondidas',
    )
    motivo_recusa = models.TextField(blank=True)
    observacao_aluno = models.TextField(blank=True)

    class Meta:
        ordering = ['-data_solicitacao']
        verbose_name = 'Solicitação de Matrícula'
        verbose_name_plural = 'Solicitações de Matrícula'

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.aluno} → {self.turma} ({self.get_status_display()})"


# ─────────────────────────────────────────────
#   FILA DE ESPERA
# ─────────────────────────────────────────────

class FilaEspera(models.Model):
    """Aluno aguardando vaga em uma turma cheia."""
    
    STATUS_CHOICES = [
        ('aguardando', 'Aguardando'),
        ('chamado', 'Chamado'),
        ('matriculado', 'Matriculado (saiu da fila)'),
        ('desistiu', 'Desistiu'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='filas_espera')
    aluno = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='filas_espera',
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='fila_espera',
    )
    posicao = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aguardando')

    data_entrada = models.DateTimeField(auto_now_add=True)
    data_chamada = models.DateTimeField(null=True, blank=True)
    chamado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='fila_chamadas',
    )

    class Meta:
        ordering = ['turma', 'posicao']
        unique_together = ('aluno', 'turma')
        verbose_name = 'Fila de Espera'
        verbose_name_plural = 'Filas de Espera'

    def __str__(self):
        return f"{self.aluno} → {self.turma} (posição {self.posicao})"
