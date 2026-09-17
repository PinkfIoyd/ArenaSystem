import django.db.models.deletion
from django.db import migrations, models


def preencher_arena_aulas(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    Turma = apps.get_model('aulas', 'Turma')
    CheckIn = apps.get_model('aulas', 'CheckIn')
    SolicitacaoMatricula = apps.get_model('aulas', 'SolicitacaoMatricula')
    FilaEspera = apps.get_model('aulas', 'FilaEspera')

    arena, _ = Arena.objects.get_or_create(slug='arenasystem-demo', defaults={'nome': 'ArenaFlow Demo'})
    Turma.objects.filter(arena__isnull=True).update(arena=arena)
    for checkin in CheckIn.objects.filter(arena__isnull=True).select_related('turma'):
        checkin.arena_id = checkin.turma.arena_id or arena.id
        checkin.save(update_fields=['arena'])
    for solicitacao in SolicitacaoMatricula.objects.filter(arena__isnull=True).select_related('turma'):
        solicitacao.arena_id = solicitacao.turma.arena_id or arena.id
        solicitacao.save(update_fields=['arena'])
    for fila in FilaEspera.objects.filter(arena__isnull=True).select_related('turma'):
        fila.arena_id = fila.turma.arena_id or arena.id
        fila.save(update_fields=['arena'])


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0008_require_arena_on_core_models'),
        ('aulas', '0003_checkin_arena_filaespera_arena_and_more'),
    ]

    operations = [
        migrations.RunPython(preencher_arena_aulas, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='turma',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='turmas', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='checkin',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkins', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='solicitacaomatricula',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitacoes_matricula', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='filaespera',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filas_espera', to='arena.arena'),
        ),
    ]
