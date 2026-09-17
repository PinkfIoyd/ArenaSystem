from django.db import migrations


def backfill_checkins(apps, schema_editor):
    CheckIn = apps.get_model('aulas', 'CheckIn')
    AulaOcorrencia = apps.get_model('aulas', 'AulaOcorrencia')

    for checkin in CheckIn.objects.select_related('turma').iterator():
        occurrence, _ = AulaOcorrencia.objects.get_or_create(
            turma_id=checkin.turma_id,
            data=checkin.data,
            defaults={
                'arena_id': checkin.arena_id,
                'horario_previsto': checkin.turma.horario,
            },
        )
        CheckIn.objects.filter(pk=checkin.pk).update(
            ocorrencia_id=occurrence.pk,
            origem='legacy',
            status='confirmed' if checkin.presente else 'absent',
        )


class Migration(migrations.Migration):
    dependencies = [('aulas', '0007_checkin_inadimplente_no_momento_checkin_motivo_and_more')]

    operations = [migrations.RunPython(backfill_checkins, migrations.RunPython.noop)]
