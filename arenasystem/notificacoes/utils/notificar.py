from django.contrib.auth import get_user_model

from arena.tenant import get_default_arena
from notificacoes.models import NotificacaoAdmin
from .email import enviar_email_simples, template_html


Usuario = get_user_model()


def notificar_admins(tipo, titulo, mensagem, url='', enviar_email=False, arena=None):
    """Cria notificacao para administradores e opcionalmente envia e-mail."""
    arena = arena or get_default_arena()
    NotificacaoAdmin.objects.create(
        arena=arena,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        url=url,
        destinatario=None,
    )
    print(f'Notificacao criada para admins: {titulo}')

    if enviar_email:
        admins = Usuario.objects.filter(is_staff=True, is_active=True).exclude(email='')
        if arena:
            admins = admins.filter(arena=arena)
        emails = [admin.email for admin in admins]
        if emails:
            html = template_html(
                titulo=titulo,
                mensagem=f'<p>{mensagem}</p>',
                link='http://localhost:5173/admin' if not url else f'http://localhost:5173{url}',
                link_texto='Acessar painel',
            )
            enviar_email_simples(
                destinatario=emails,
                assunto=titulo,
                mensagem=mensagem,
                html=html,
            )


def notificar_aluno(aluno, assunto, mensagem_html):
    """Envia e-mail para um aluno especifico."""
    if not aluno.email:
        print(f'Aluno {aluno.username} nao tem e-mail cadastrado.')
        return

    enviar_email_simples(
        destinatario=aluno.email,
        assunto=assunto,
        mensagem=mensagem_html,
        html=mensagem_html,
    )
    print(f'E-mail enviado para {aluno.email}')
