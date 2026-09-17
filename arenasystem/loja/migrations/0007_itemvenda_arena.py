import django.db.models.deletion
from django.db import migrations, models


def preencher_arena_itens(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    Venda = apps.get_model('loja', 'Venda')
    ItemVenda = apps.get_model('loja', 'ItemVenda')

    arena, _ = Arena.objects.get_or_create(
        slug='arenasystem-demo',
        defaults={'nome': 'ArenaFlow Demo'},
    )
    Venda.objects.filter(arena__isnull=True).update(arena=arena)
    for item in ItemVenda.objects.filter(arena__isnull=True).select_related('venda'):
        item.arena_id = item.venda.arena_id or arena.id
        item.save(update_fields=['arena'])


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0007_multi_tenant_hardening'),
        ('loja', '0006_alter_produto_imagem'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemvenda',
            name='arena',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='itens_venda', to='arena.arena'),
        ),
        migrations.RunPython(preencher_arena_itens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='itemvenda',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens_venda', to='arena.arena'),
        ),
    ]
