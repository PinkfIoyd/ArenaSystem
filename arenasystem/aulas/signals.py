from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import FilaEspera, SolicitacaoMatricula, Turma
from notificacoes.utils.email import template_html
from notificacoes.utils.notificar import notificar_admins, notificar_aluno


@receiver(post_save, sender=SolicitacaoMatricula)
def ao_criar_solicitacao(sender, instance, created, **kwargs):
    if not created:
        return

    aluno_nome = instance.aluno.get_full_name() or instance.aluno.username

    if instance.tipo == 'matricula':
        titulo = f'Nova solicitacao de matricula: {aluno_nome}'
        mensagem = (
            f'{aluno_nome} solicitou matricula na turma "{instance.turma.nome}". '
            f'Acesse o painel para aprovar ou recusar.'
        )
        tipo_notif = 'nova_solicitacao_matricula'
    elif instance.tipo == 'cancelamento':
        titulo = f'Solicitacao de cancelamento: {aluno_nome}'
        mensagem = (
            f'{aluno_nome} pediu para sair da turma "{instance.turma.nome}". '
            f'Verifique os detalhes no painel.'
        )
        tipo_notif = 'nova_solicitacao_cancelamento'
    else:
        return

    notificar_admins(
        tipo=tipo_notif,
        titulo=titulo,
        mensagem=mensagem,
        url=f'/admin/solicitacoes/{instance.id}',
        enviar_email=True,
        arena=instance.arena,
    )


@receiver(post_save, sender=SolicitacaoMatricula)
def ao_responder_solicitacao(sender, instance, created, **kwargs):
    if created:
        return

    aluno_nome = instance.aluno.first_name or instance.aluno.username

    if instance.status == 'aprovada':
        titulo = 'Sua solicitacao foi aprovada'
        if instance.tipo == 'matricula':
            corpo = f'''
                <p>Ola, <strong>{aluno_nome}</strong>!</p>
                <p>Sua solicitacao de matricula na turma
                <strong>"{instance.turma.nome}"</strong> foi <strong style="color:green;">aprovada</strong>.</p>
                <p>Voce ja pode fazer check-in nas proximas aulas. Bem-vindo a arena!</p>
            '''
        else:
            corpo = f'''
                <p>Ola, <strong>{aluno_nome}</strong>.</p>
                <p>Seu pedido de cancelamento da turma <strong>"{instance.turma.nome}"</strong>
                foi processado.</p>
                <p>Sentiremos sua falta! Volte quando quiser.</p>
            '''

        html = template_html(
            titulo=titulo,
            mensagem=corpo,
            link='http://localhost:5173/turmas',
            link_texto='Ver minhas turmas',
        )
        notificar_aluno(instance.aluno, titulo, html)

    elif instance.status == 'recusada':
        titulo = 'Sobre sua solicitacao'
        corpo = f'''
            <p>Ola, <strong>{aluno_nome}</strong>.</p>
            <p>Sua solicitacao para a turma <strong>"{instance.turma.nome}"</strong>
            nao pode ser atendida no momento.</p>
            {f'<p><strong>Motivo:</strong> {instance.motivo_recusa}</p>' if instance.motivo_recusa else ''}
            <p>Entre em contato com a recepcao para mais informacoes.</p>
        '''

        html = template_html(titulo=titulo, mensagem=corpo)
        notificar_aluno(instance.aluno, titulo, html)


@receiver(m2m_changed, sender=Turma.alunos.through)
def ao_alterar_alunos_turma(sender, instance, action, pk_set, **kwargs):
    if action != 'post_remove':
        return

    fila = FilaEspera.objects.filter(turma=instance, status='aguardando').order_by('posicao')
    if not fila.exists():
        return

    proximo = fila.first()
    proximo_nome = proximo.aluno.get_full_name() or proximo.aluno.username
    vagas = instance.vagas_disponiveis()

    titulo = f'Vaga aberta na turma "{instance.nome}"'
    mensagem = (
        f'Uma vaga foi liberada na turma "{instance.nome}". '
        f'Ha {fila.count()} aluno(s) na fila. '
        f'O proximo e {proximo_nome}. '
        f'Vagas disponiveis: {vagas}.'
    )

    notificar_admins(
        tipo='vaga_aberta_com_fila',
        titulo=titulo,
        mensagem=mensagem,
        url=f'/admin/fila-espera?turma={instance.id}',
        enviar_email=True,
        arena=instance.arena,
    )


@receiver(post_save, sender=FilaEspera)
def ao_entrar_fila(sender, instance, created, **kwargs):
    if not created:
        return

    aluno_nome = instance.aluno.get_full_name() or instance.aluno.username
    titulo = f'Novo na fila: {aluno_nome}'
    mensagem = (
        f'{aluno_nome} entrou na fila de espera da turma '
        f'"{instance.turma.nome}" (posicao {instance.posicao}).'
    )

    notificar_admins(
        tipo='aluno_entrou_fila',
        titulo=titulo,
        mensagem=mensagem,
        url=f'/admin/fila-espera?turma={instance.turma.id}',
        enviar_email=False,
        arena=instance.arena,
    )
