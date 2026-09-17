from rest_framework.routers import DefaultRouter
from .api_views import (
    AdminFornecedorViewSet,
    AdminLoteEstoqueViewSet,
    AdminMovimentacaoEstoqueViewSet,
    AdminProdutoViewSet,
    AdminVendaViewSet,
    CategoriaViewSet,
    ProdutoViewSet,
    VendaViewSet,
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'produtos', ProdutoViewSet, basename='produto')
router.register(r'vendas', VendaViewSet, basename='venda')
router.register(r'admin/vendas', AdminVendaViewSet, basename='admin-venda')
router.register(r'admin/fornecedores', AdminFornecedorViewSet, basename='admin-fornecedor')
router.register(r'admin/estoque/lotes', AdminLoteEstoqueViewSet, basename='admin-lote-estoque')
router.register(r'admin/produtos', AdminProdutoViewSet, basename='admin-produto')
router.register(r'admin/estoque/movimentacoes', AdminMovimentacaoEstoqueViewSet, basename='admin-movimentacao-estoque')

urlpatterns = router.urls
