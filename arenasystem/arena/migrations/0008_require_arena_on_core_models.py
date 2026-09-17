import django.db.models.deletion
from django.db import migrations, models


def preencher_arena_core(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    Quadra = apps.get_model('arena', 'Quadra')
    Plano = apps.get_model('arena', 'Plano')
    Matricula = apps.get_model('arena', 'Matricula')

    arena, _ = Arena.objects.get_or_create(slug='arenasystem-demo', defaults={'nome': 'ArenaFlow Demo'})
    Quadra.objects.filter(arena__isnull=True).update(arena=arena)
    Plano.objects.filter(arena__isnull=True).update(arena=arena)
    Matricula.objects.filter(arena__isnull=True).update(arena=arena)


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0007_multi_tenant_hardening'),
    ]

    operations = [
        migrations.RunPython(preencher_arena_core, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='quadra',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quadras', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='plano',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planos', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='matricula',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matriculas', to='arena.arena'),
        ),
    ]
