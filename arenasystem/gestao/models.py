from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ReservaQuadra(models.Model):
    STATUS = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('concluida', 'Concluida'),
        ('cancelada', 'Cancelada'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='reservas_quadra')
    quadra = models.ForeignKey('arena.Quadra', on_delete=models.PROTECT, related_name='reservas')
    aluno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas_quadra')
    cliente_nome = models.CharField(max_length=120)
    cliente_telefone = models.CharField(max_length=30, blank=True)
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    valor = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS, default='pendente')
    observacoes = models.TextField(blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas_criadas')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data', 'hora_inicio']
        constraints = [
            models.UniqueConstraint(
                fields=['arena', 'quadra', 'data', 'hora_inicio', 'hora_fim'],
                name='uniq_reserva_horario_por_quadra',
            )
        ]

    def __str__(self):
        return f'{self.quadra} - {self.data:%d/%m/%Y} {self.hora_inicio:%H:%M}'


class BloqueioQuadra(models.Model):
    CATEGORIAS = [
        ('evento', 'Evento'),
        ('chuva', 'Chuva'),
        ('manutencao', 'Manutencao'),
        ('outro', 'Outro'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='bloqueios_quadra')
    quadra = models.ForeignKey('arena.Quadra', on_delete=models.CASCADE, related_name='bloqueios')
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    motivo = models.CharField(max_length=160)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='outro')
    observacoes = models.TextField(blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data', 'hora_inicio']

    def __str__(self):
        return f'{self.quadra} bloqueada em {self.data:%d/%m/%Y}'


class FaixaPrecoReserva(models.Model):
    DIAS_SEMANA = [
        (0, 'Segunda'),
        (1, 'Terca'),
        (2, 'Quarta'),
        (3, 'Quinta'),
        (4, 'Sexta'),
        (5, 'Sabado'),
        (6, 'Domingo'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='faixas_preco_reserva')
    quadra = models.ForeignKey('arena.Quadra', on_delete=models.CASCADE, null=True, blank=True, related_name='faixas_preco')
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        constraints = [
            models.CheckConstraint(check=Q(hora_inicio__lt=models.F('hora_fim')), name='faixa_preco_hora_inicio_lt_fim'),
        ]

    def __str__(self):
        alvo = self.quadra.nome if self.quadra else 'Todas as quadras'
        return f'{alvo} - {self.get_dia_semana_display()} {self.hora_inicio:%H:%M}'


class AuditLog(models.Model):
    arena = models.ForeignKey(
        'arena.Arena', on_delete=models.CASCADE, related_name='auditoria', null=True, blank=True,
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.CharField(max_length=80)
    entidade_tipo = models.CharField(max_length=80)
    entidade_id = models.CharField(max_length=80, blank=True)
    valores_anteriores = models.JSONField(default=dict, blank=True)
    valores_novos = models.JSONField(default=dict, blank=True)
    metadados = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.acao} {self.entidade_tipo}#{self.entidade_id}'


class Lead(models.Model):
    ETAPAS = [
        ('novo', 'Novo'),
        ('contato', 'Em contato'),
        ('experimental', 'Aula experimental'),
        ('negociacao', 'Negociacao'),
        ('ganho', 'Ganho'),
        ('perdido', 'Perdido'),
    ]
    ORIGENS = [
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('indicacao', 'Indicacao'),
        ('balcao', 'Balcao'),
        ('site', 'Site'),
        ('outro', 'Outro'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='leads')
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    modalidade_interesse = models.CharField(max_length=80, blank=True)
    origem = models.CharField(max_length=20, choices=ORIGENS, default='whatsapp')
    etapa = models.CharField(max_length=20, choices=ETAPAS, default='novo')
    valor_potencial = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    proximo_contato = models.DateField(null=True, blank=True)
    motivo_perda = models.CharField(max_length=200, blank=True)
    observacoes = models.TextField(blank=True)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads_responsavel')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['proximo_contato', '-criado_em']

    def __str__(self):
        return self.nome


class ContaFinanceira(models.Model):
    TIPOS = [
        ('receber', 'A receber'),
        ('pagar', 'A pagar'),
    ]
    STATUS = [
        ('aberta', 'Aberta'),
        ('paga', 'Paga'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='contas_financeiras')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descricao = models.CharField(max_length=160)
    categoria = models.CharField(max_length=80, blank=True)
    fornecedor = models.CharField(max_length=120, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='aberta')
    observacoes = models.TextField(blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vencimento', 'tipo']

    def atualizar_vencida(self, hoje=None, salvar=True):
        hoje = hoje or timezone.localdate()
        if self.status == 'aberta' and self.vencimento < hoje:
            self.status = 'vencida'
            if salvar:
                self.save(update_fields=['status'])
        return self.status

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.descricao}'


class ContratoMatricula(models.Model):
    STATUS = [
        ('pendente', 'Pendente'),
        ('aceito', 'Aceito'),
        ('cancelado', 'Cancelado'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='contratos')
    matricula = models.OneToOneField('arena.Matricula', on_delete=models.CASCADE, related_name='contrato')
    texto = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='pendente')
    data_aceite = models.DateTimeField(null=True, blank=True)
    ip_aceite = models.GenericIPAddressField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def aceitar(self, ip=None):
        self.status = 'aceito'
        self.data_aceite = timezone.now()
        self.ip_aceite = ip
        self.save(update_fields=['status', 'data_aceite', 'ip_aceite'])
