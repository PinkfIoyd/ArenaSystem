import django.db.models.deletion
from django.db import migrations, models


def preencher_arena_notificacoes(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    Notificacao = apps.get_model('notificacoes', 'Notificacao')
    NotificacaoAdmin = apps.get_model('notificacoes', 'NotificacaoAdmin')

    arena, _ = Arena.objects.get_or_create(slug='arenasystem-demo', defaults={'nome': 'ArenaFlow Demo'})
    for notificacao in Notificacao.objects.filter(arena__isnull=True).select_related('destinatario'):
        notificacao.arena_id = notificacao.destinatario.arena_id or arena.id
        notificacao.save(update_fields=['arena'])
    NotificacaoAdmin.objects.filter(arena__isnull=True).update(arena=arena)


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0008_require_arena_on_core_models'),
        ('notificacoes', '0003_notificacao_arena_notificacaoadmin_arena'),
    ]

    operations = [
        migrations.RunPython(preencher_arena_notificacoes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='notificacao',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='notificacaoadmin',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes_admin_arena', to='arena.arena'),
        ),
    ]
