import django.db.models.deletion
from django.db import migrations, models


def preencher_arena_loja(apps, schema_editor):
    Arena = apps.get_model('arena', 'Arena')
    Categoria = apps.get_model('loja', 'Categoria')
    Fornecedor = apps.get_model('loja', 'Fornecedor')
    Produto = apps.get_model('loja', 'Produto')
    LoteEstoque = apps.get_model('loja', 'LoteEstoque')
    MovimentacaoEstoque = apps.get_model('loja', 'MovimentacaoEstoque')
    Venda = apps.get_model('loja', 'Venda')

    arena, _ = Arena.objects.get_or_create(slug='arenasystem-demo', defaults={'nome': 'ArenaFlow Demo'})
    Categoria.objects.filter(arena__isnull=True).update(arena=arena)
    Fornecedor.objects.filter(arena__isnull=True).update(arena=arena)
    Produto.objects.filter(arena__isnull=True).update(arena=arena)
    Venda.objects.filter(arena__isnull=True).update(arena=arena)
    for lote in LoteEstoque.objects.filter(arena__isnull=True).select_related('produto'):
        lote.arena_id = lote.produto.arena_id or arena.id
        lote.save(update_fields=['arena'])
    for mov in MovimentacaoEstoque.objects.filter(arena__isnull=True).select_related('produto'):
        mov.arena_id = mov.produto.arena_id or arena.id
        mov.save(update_fields=['arena'])


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0007_itemvenda_arena'),
    ]

    operations = [
        migrations.RunPython(preencher_arena_loja, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='categoria',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categorias_loja', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='fornecedor',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fornecedores', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='produtos', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='loteestoque',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lotes_estoque', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='movimentacaoestoque',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimentacoes_estoque', to='arena.arena'),
        ),
        migrations.AlterField(
            model_name='venda',
            name='arena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendas', to='arena.arena'),
        ),
    ]
