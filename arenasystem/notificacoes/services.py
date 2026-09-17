from django.conf import settings
from django.core.mail import send_mail

from arena.tenant import get_default_arena
from .models import Notificacao
from .preferences import notification_allowed


def criar_notificacao(destinatario, titulo, mensagem, tipo='geral', enviar_email=True, arena=None):
    """
    Cria uma notificacao no sistema e opcionalmente envia e-mail.
    Mantem assunto/mensagem sem emoji para evitar falhas de encoding em consoles Windows.
    """
    tenant = arena or getattr(destinatario, 'arena', None) or get_default_arena()
    category = 'financial' if tipo == 'mensalidade' else 'classes' if tipo == 'aula' else None
    app_allowed = not category or notification_allowed(destinatario, category, 'app')
    email_allowed = not category or notification_allowed(destinatario, category, 'email')
    notif = None
    if app_allowed:
        notif = Notificacao.objects.create(
            arena=tenant,
            destinatario=destinatario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
        )

    if enviar_email and email_allowed and destinatario.email:
        try:
            send_mail(
                subject=f"[ArenaFlow] {titulo}",
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario.email],
                fail_silently=False,
            )
            if notif:
                notif.enviada_email = True
                notif.save(update_fields=['enviada_email'])
        except Exception as exc:
            print(f"Erro ao enviar e-mail para {destinatario.email}: {exc}")

    return notif
