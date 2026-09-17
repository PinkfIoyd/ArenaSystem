import django.db.models.deletion
from django.db import migrations, models


def preencher_arena_mensalidades(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    Matricula = apps.get_model('arena', 'Matricula')
    Mensalidade = apps.get_model('arena', 'Mensalidade')

    arena, _ = Arena.objects.get_or_create(
        slug='arenasystem-demo',
        defaults={
            'nome': 'ArenaFlow Demo',
            'cor_primaria': '#0F766E',
            'cor_secundaria': '#A3E635',
            'cor_fundo': '#ECFEFF',
            'cor_texto': '#071B26',
        },
    )
    Matricula.objects.filter(arena__isnull=True).update(arena=arena)
    for mensalidade in Mensalidade.objects.filter(arena__isnull=True).select_related('matricula'):
        mensalidade.arena_id = mensalidade.matricula.arena_id or arena.id
        mensalidade.save(update_fields=['arena'])


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0006_alter_arena_theme_defaults'),
    ]

    operations = [
        migrations.AddField(
            model_name='arena',
            name='documento',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='arena',
            name='email_contato',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='arena',
            name='endereco',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='arena',
            name='limite_admins',
            field=models.PositiveIntegerField(default=3),
        ),
        migrations.AddField(
            model_name='arena',
            name='limite_alunos',
            field=models.PositiveIntegerField(default=150),
        ),
        migrations.AddField(
            model_name='arena',
            name='limite_quadras',
            field=models.PositiveIntegerField(default=4),
        ),
        migrations.AddField(
            model_name='arena',
            name='observacoes_comerciais',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='arena',
            name='plano_contratado',
            field=models.CharField(choices=[('starter', 'Starter'), ('professional', 'Professional'), ('enterprise', 'Enterprise')], default='starter', max_length=30),
        ),
        migrations.AddField(
            model_name='arena',
            name='status_assinatura',
            field=models.CharField(choices=[('ativa', 'Ativa'), ('suspensa', 'Suspensa'), ('trial', 'Trial'), ('cancelada', 'Cancelada')], default='trial', max_length=20),
        ),
        migrations.AddField(
            model_name='arena',
            name='telefone_contato',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='paymentwebhookevent',
            name='arena',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payment_webhook_events', to='arena.arena'),
        ),
        migrations.AddField(
            model_name='mensalidade',
            name='arena',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mensalidades', to='arena.arena'),
        ),
        migrations.RunPython(preencher_arena_mensalidades, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='mensalidade',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensalidades', to='arena.arena'),
        ),
    ]
