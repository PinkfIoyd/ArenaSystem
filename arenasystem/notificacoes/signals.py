from django.db.models.signals import post_save
from django.dispatch import receiver

from arena.models import Mensalidade
from manutencao.models import Manutencao
from .services import criar_notificacao


@receiver(post_save, sender=Mensalidade)
def notificar_mensalidade(sender, instance, created, **kwargs):
    """Dispara quando uma mensalidade e criada ou paga."""
    if created:
        criar_notificacao(
            destinatario=instance.matricula.aluno,
            titulo="Nova mensalidade gerada",
            mensagem=(
                f"Ola! Sua mensalidade de {instance.mes_referencia.strftime('%m/%Y')} "
                f"no valor de R$ {instance.valor} foi gerada. "
                f"Vencimento: {instance.vencimento.strftime('%d/%m/%Y')}.\n\n"
                f"Qualquer duvida, fale conosco na recepcao!"
            ),
            tipo='mensalidade',
            arena=instance.matricula.arena,
        )
    elif instance.status == 'pago':
        criar_notificacao(
            destinatario=instance.matricula.aluno,
            titulo="Pagamento confirmado",
            mensagem=(
                f"Recebemos seu pagamento da mensalidade de "
                f"{instance.mes_referencia.strftime('%m/%Y')}. "
                f"Obrigado e bons treinos!"
            ),
            tipo='mensalidade',
            arena=instance.matricula.arena,
        )


@receiver(post_save, sender=Manutencao)
def notificar_manutencao(sender, instance, created, **kwargs):
    """Notifica todos os admins quando uma manutencao e agendada."""
    if created:
        from usuarios.models import Usuario

        admins = Usuario.objects.filter(tipo__in=['admin', 'admin_arena', 'funcionario'])
        if instance.arena_id:
            admins = admins.filter(arena=instance.arena)
        for admin in admins:
            criar_notificacao(
                destinatario=admin,
                titulo=f"Manutencao agendada - {instance.quadra.nome}",
                mensagem=(
                    f"Foi agendada uma manutencao {instance.get_tipo_display().lower()} "
                    f"para {instance.data_agendada.strftime('%d/%m/%Y')}.\n\n"
                    f"Quadra: {instance.quadra.nome}\n"
                    f"Descricao: {instance.descricao}\n"
                    f"Responsavel: {instance.responsavel or 'A definir'}"
                ),
                tipo='manutencao',
                arena=instance.arena,
            )
