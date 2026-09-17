from django.db import models


class Manutencao(models.Model):
    TIPOS = [
        ('preventiva', 'Preventiva'),
        ('corretiva', 'Corretiva'),
    ]
    STATUS = [
        ('agendada', 'Agendada'),
        ('em_andamento', 'Em andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    arena = models.ForeignKey('arena.Arena', on_delete=models.CASCADE, related_name='manutencoes')
    quadra = models.ForeignKey(
        'arena.Quadra',
        on_delete=models.CASCADE,
        related_name='manutencoes'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descricao = models.TextField()
    data_agendada = models.DateField()
    data_conclusao = models.DateField(null=True, blank=True)
    custo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='agendada')
    responsavel = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-data_agendada']
        verbose_name = "Manutenção"
        verbose_name_plural = "Manutenções"

    def __str__(self):
        return f"{self.quadra.nome} - {self.get_tipo_display()} - {self.data_agendada.strftime('%d/%m/%Y')}"
