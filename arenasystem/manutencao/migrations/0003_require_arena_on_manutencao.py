import django.db.models.deletion
from django.db import migrations, models


def preencher_arena_manutencao(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    Manutencao = apps.get_model('manutencao', 'Manutencao')

    arena, _ = Arena.objects.get_or_create(slug='arenasystem-demo', defaults={'nome': 'ArenaFlow Demo'})
    for manutencao in Manutencao.objects.filter(arena__isnull=True).select_related('quadra'):
        manutencao.arena_id = manutencao.quadra.arena_id or arena.id
        manutencao.save(update_fields=['arena'])


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0008_require_arena_on_core_models'),
        ('manutencao', '0002_manutencao_arena'),
    ]

    operations = [
        migrations.RunPython(preencher_arena_manutencao, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='manutencao',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='manutencoes', to='arena.arena'),
        ),
    ]
