from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def backfill_subscriptions(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    SaasPlan = apps.get_model('saas_billing', 'SaasPlan')
    SaasSubscription = apps.get_model('saas_billing', 'SaasSubscription')

    catalog = {}
    for code, name in (
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ):
        plan, _ = SaasPlan.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': 'Catalogo comercial pendente de precificacao.',
                'published': False,
                'trial_days': 14,
                'grace_days': 7,
            },
        )
        catalog[code] = plan

    status_map = {
        'trial': 'trialing',
        'ativa': 'active',
        'suspensa': 'suspended',
        'cancelada': 'canceled',
    }
    now = timezone.now()
    for arena in Arena.objects.all().iterator():
        plan = catalog.get(arena.plano_contratado, catalog['starter'])
        plan.max_admins = max(plan.max_admins, arena.limite_admins)
        plan.max_students = max(plan.max_students, arena.limite_alunos)
        plan.max_courts = max(plan.max_courts, arena.limite_quadras)
        plan.save(update_fields=['max_admins', 'max_students', 'max_courts'])
        status = status_map.get(arena.status_assinatura, 'trialing')
        trial_start = arena.criada_em or now
        SaasSubscription.objects.get_or_create(
            arena=arena,
            defaults={
                'plan': plan,
                'status': status,
                'trial_started_at': trial_start if status == 'trialing' else None,
                'trial_ends_at': trial_start + timedelta(days=14) if status == 'trialing' else None,
                'canceled_at': now if status == 'canceled' else None,
            },
        )


class Migration(migrations.Migration):
    dependencies = [('saas_billing', '0001_initial')]

    operations = [
        migrations.RunPython(backfill_subscriptions, migrations.RunPython.noop),
    ]

