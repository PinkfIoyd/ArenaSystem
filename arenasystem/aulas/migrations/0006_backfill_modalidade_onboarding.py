from django.db import migrations
from django.utils import timezone


def backfill(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    ArenaOnboarding = apps.get_model('arena', 'ArenaOnboarding')
    Modalidade = apps.get_model('arena', 'Modalidade')
    Turma = apps.get_model('aulas', 'Turma')
    completed = ['identification', 'hours', 'courts', 'modalities', 'professors', 'students', 'review']
    now = timezone.now()
    for arena in Arena.objects.all().iterator():
        modalidade, _ = Modalidade.objects.get_or_create(
            arena=arena, nome='Geral', defaults={'cor': arena.cor_primaria, 'ativa': True},
        )
        Turma.objects.filter(arena=arena, modalidade__isnull=True).update(modalidade=modalidade)
        ArenaOnboarding.objects.get_or_create(
            arena=arena,
            defaults={'current_step': 'review', 'completed_steps': completed, 'completed_at': now},
        )


class Migration(migrations.Migration):
    dependencies = [
        ('arena', '0010_arenaonboarding_arenabusinesshours_modalidade'),
        ('aulas', '0005_turma_modalidade'),
    ]

    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]

