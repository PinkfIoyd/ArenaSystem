from django.contrib import admin
from .models import Categoria, Fornecedor, ItemVenda, LoteEstoque, Produto, Venda


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'fornecedor', 'preco', 'custo_unitario', 'estoque', 'estoque_minimo', 'canal', 'ativo')
    list_filter = ('categoria', 'fornecedor', 'canal', 'ativo', 'is_aluguel')
    search_fields = ('nome', 'descricao', 'sku', 'codigo_barras')
    list_editable = ('preco', 'custo_unitario', 'estoque_minimo', 'ativo')


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'contato', 'telefone', 'email', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'contato', 'telefone', 'email')


@admin.register(LoteEstoque)
class LoteEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'codigo_lote', 'quantidade_atual', 'quantidade_inicial', 'validade', 'fornecedor')
    list_filter = ('validade', 'fornecedor')
    search_fields = ('produto__nome', 'codigo_lote')


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 1
    fields = ('produto', 'quantidade', 'preco_unitario')


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'data', 'total', 'status')
    list_filter = ('status', 'data')
    search_fields = ('cliente__username', 'cliente__first_name')
    date_hierarchy = 'data'
    inlines = [ItemVendaInline]
    readonly_fields = ('total', 'data')

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Recalcula o total automaticamente após salvar os itens
        form.instance.calcular_total()
