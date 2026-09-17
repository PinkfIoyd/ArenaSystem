from django.conf import settings
from django.core.mail import send_mail


def enviar_email_simples(destinatario, assunto, mensagem, html=None):
    """Envia um e-mail. Em dev, aparece no terminal."""
    if isinstance(destinatario, str):
        destinatario = [destinatario]

    destinatario = [email for email in destinatario if email]
    if not destinatario:
        print('Nenhum destinatario valido. E-mail nao enviado.')
        return False

    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinatario,
            html_message=html,
            fail_silently=False,
        )
        return True
    except Exception as exc:
        print(f'Erro ao enviar e-mail: {exc}')
        return False


def template_html(titulo, mensagem, link=None, link_texto='Acessar'):
    """Gera um HTML simples para e-mails transacionais."""
    botao = ''
    if link:
        botao = f'''
        <a href="{link}" style="display:inline-block; padding:12px 24px;
                background:#0f766e; color:#fff; text-decoration:none;
                border-radius:8px; font-weight:bold; margin-top:16px;">
            {link_texto}
        </a>
        '''
    return f'''
    <html>
      <body style="font-family: Arial, sans-serif; background:#f9fafb; padding:20px;">
        <div style="max-width:600px; margin:0 auto; background:#fff;
                    border-radius:12px; padding:32px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
          <h1 style="color:#123B5D; margin-top:0;">ArenaFlow</h1>
          <h2 style="color:#333;">{titulo}</h2>
          <div style="color:#555; line-height:1.6;">
            {mensagem}
          </div>
          {botao}
          <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">
          <p style="color:#999; font-size:12px;">
            Este e um e-mail automatico. Nao responda.
          </p>
        </div>
      </body>
    </html>
    '''
