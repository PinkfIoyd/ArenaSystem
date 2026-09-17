import django.db.models.deletion
from django.db import migrations, models


def preencher_arena_webhooks(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    PaymentWebhookEvent = apps.get_model('arena', 'PaymentWebhookEvent')

    arena, _ = Arena.objects.get_or_create(slug='arenasystem-demo', defaults={'nome': 'ArenaFlow Demo'})
    PaymentWebhookEvent.objects.filter(arena__isnull=True).update(arena=arena)


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0008_require_arena_on_core_models'),
    ]

    operations = [
        migrations.RunPython(preencher_arena_webhooks, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='paymentwebhookevent',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_webhook_events', to='arena.arena'),
        ),
    ]
