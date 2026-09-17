from django.db import models
from django.conf import settings


class Notificacao(models.Model):
    TIPOS = [
        ('mensalidade', 'Mensalidade'),
        ('aula', 'Aula'),
        ('manutencao', 'Manutenção'),
        ('geral', 'Geral'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='notificacoes')
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificacoes'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default='geral')
    titulo = models.CharField(max_length=150)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)
    enviada_email = models.BooleanField(default=False)

    class Meta:
        ordering = ['-criada_em']
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"

    def __str__(self):
        status = "📧" if self.enviada_email else "📭"
        return f"{status} {self.destinatario} - {self.titulo}"
class NotificacaoAdmin(models.Model):
    """Notificações destinadas aos administradores da arena."""

    TIPO_CHOICES = [
        ('nova_solicitacao_matricula', '📥 Nova solicitação de matrícula'),
        ('nova_solicitacao_cancelamento', '⚠️ Nova solicitação de cancelamento'),
        ('aluno_entrou_fila', '⏳ Aluno entrou na fila de espera'),
        ('vaga_aberta_com_fila', '🎯 Vaga aberta — chamar fila'),
        ('aluno_pagou', '💰 Pagamento recebido'),
        ('estoque_baixo', '📦 Estoque baixo'),
        ('outros', '🔔 Outros'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='notificacoes_admin_arena')
    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()

    # Link contextual (ex: '/admin/solicitacoes/15')
    url = models.CharField(max_length=300, blank=True)

    # Para quem é a notificação (vazio = todos os admins)
    destinatario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notificacoes_admin',
        help_text='Se vazio, vai para todos os admins',
    )

    lida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criada_em']
        verbose_name = 'Notificação de Admin'
        verbose_name_plural = 'Notificações de Admin'

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo}"

    def marcar_como_lida(self):
        from django.utils import timezone
        self.lida = True
        self.lida_em = timezone.now()
        self.save()
