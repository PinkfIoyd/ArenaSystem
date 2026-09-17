from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Categoria, Fornecedor, LoteEstoque, MovimentacaoEstoque, Produto, Venda
from .serializers import (
    CategoriaSerializer,
    FornecedorSerializer,
    LoteEstoqueSerializer,
    MovimentacaoEstoqueSerializer,
    ProdutoSerializer,
    VendaSerializer,
)
from arena.tenant import get_user_arena
from arena.features import FeatureEnabledMixin
from gestao.audit import registrar_auditoria
from usuarios.permissions import require_permission


class CategoriaViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'store'
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Categoria.objects.filter(arena=get_user_arena(self.request.user))


class ProdutoViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'store'
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        arena = get_user_arena(self.request.user)
        return Produto.objects.filter(
            arena=arena,
            ativo=True,
            canal__in=['app', 'ambos'],
        ).select_related('categoria')


class AdminProdutoViewSet(FeatureEnabledMixin, viewsets.ModelViewSet):
    feature_key = 'store'
    serializer_class = ProdutoSerializer
    permission_classes = [require_permission('estoque.manage')]

    def get_queryset(self):
        qs = Produto.objects.filter(arena=get_user_arena(self.request.user)).select_related('categoria', 'fornecedor').prefetch_related('lotes')
        canal = self.request.query_params.get('canal')
        if canal in ['app', 'balcao', 'ambos']:
            qs = qs.filter(canal=canal)
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(nome__icontains=search) |
                Q(sku__icontains=search) |
                Q(codigo_barras__icontains=search) |
                Q(categoria__nome__icontains=search) |
                Q(fornecedor__nome__icontains=search)
            )
        return qs.order_by('categoria__nome', 'nome')

    def perform_create(self, serializer):
        serializer.save(arena=get_user_arena(self.request.user))

    def _registrar_movimentacao(self, produto, tipo, quantidade, observacao='', lote=None, custo_unitario=None):
        estoque_antes = produto.estoque
        estoque_depois = estoque_antes + quantidade
        if estoque_depois < 0:
            raise ValueError('Estoque insuficiente.')
        produto.estoque = estoque_depois
        produto.save(update_fields=['estoque'])
        mov = MovimentacaoEstoque.objects.create(
            arena=get_user_arena(self.request.user),
            produto=produto,
            lote=lote,
            tipo=tipo,
            quantidade=quantidade,
            estoque_antes=estoque_antes,
            estoque_depois=estoque_depois,
            valor_unitario=produto.preco,
            custo_unitario=custo_unitario if custo_unitario is not None else produto.custo_unitario,
            observacao=observacao,
            criado_por=self.request.user,
        )
        registrar_auditoria(
            self.request,
            get_user_arena(self.request.user),
            'estoque.movimentacao',
            mov,
            anteriores={'estoque': estoque_antes},
            novos={'estoque': estoque_depois, 'quantidade': quantidade, 'tipo': tipo},
        )

    def _baixar_lotes(self, produto, quantidade):
        restante = quantidade
        lotes = produto.lotes.filter(quantidade_atual__gt=0).order_by('validade', 'criado_em')
        ultimo_lote = None
        for lote in lotes:
            if restante <= 0:
                break
            baixa = min(lote.quantidade_atual, restante)
            lote.quantidade_atual -= baixa
            lote.save(update_fields=['quantidade_atual'])
            restante -= baixa
            ultimo_lote = lote
        return ultimo_lote

    @action(detail=True, methods=['post'])
    def entrada(self, request, pk=None):
        produto = self.get_object()
        quantidade = int(request.data.get('quantidade', 0))
        if quantidade <= 0:
            return Response({'detail': 'Quantidade deve ser maior que zero.'}, status=status.HTTP_400_BAD_REQUEST)
        custo_unitario = request.data.get('custo_unitario') or produto.custo_unitario
        fornecedor_id = request.data.get('fornecedor') or produto.fornecedor_id
        arena = get_user_arena(self.request.user)
        if fornecedor_id and not Fornecedor.objects.filter(arena=arena, id=fornecedor_id).exists():
            return Response({'detail': 'Fornecedor nao pertence a arena atual.'}, status=status.HTTP_400_BAD_REQUEST)
        lote = LoteEstoque.objects.create(
            arena=arena,
            produto=produto,
            codigo_lote=request.data.get('codigo_lote', ''),
            quantidade_inicial=quantidade,
            quantidade_atual=quantidade,
            custo_unitario=custo_unitario,
            validade=request.data.get('validade') or None,
            fornecedor_id=fornecedor_id or None,
        )
        self._registrar_movimentacao(
            produto,
            'entrada',
            quantidade,
            request.data.get('observacao', 'Entrada de estoque'),
            lote=lote,
            custo_unitario=custo_unitario,
        )
        return Response({'detail': 'Entrada registrada.', 'estoque': produto.estoque})

    @action(detail=True, methods=['post'])
    def ajuste(self, request, pk=None):
        produto = self.get_object()
        novo_estoque = int(request.data.get('estoque', produto.estoque))
        quantidade = novo_estoque - produto.estoque
        self._registrar_movimentacao(produto, 'ajuste', quantidade, request.data.get('observacao', 'Ajuste manual'))
        return Response({'detail': 'Estoque ajustado.', 'estoque': produto.estoque})

    @action(detail=True, methods=['post'], url_path='venda-balcao')
    @transaction.atomic
    def venda_balcao(self, request, pk=None):
        produto = self.get_object()
        if produto.canal == 'app':
            return Response({'detail': 'Produto exclusivo do app.'}, status=status.HTTP_400_BAD_REQUEST)
        quantidade = int(request.data.get('quantidade', 1))
        if quantidade <= 0:
            return Response({'detail': 'Quantidade deve ser maior que zero.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            lote = self._baixar_lotes(produto, quantidade)
            self._registrar_movimentacao(produto, 'venda_balcao', -quantidade, 'Venda no balcao', lote=lote)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Venda de balcao registrada.', 'estoque': produto.estoque})


class AdminFornecedorViewSet(FeatureEnabledMixin, viewsets.ModelViewSet):
    feature_key = 'store'
    serializer_class = FornecedorSerializer
    permission_classes = [require_permission('estoque.manage')]

    def get_queryset(self):
        return Fornecedor.objects.filter(arena=get_user_arena(self.request.user))

    def perform_create(self, serializer):
        serializer.save(arena=get_user_arena(self.request.user))


class AdminLoteEstoqueViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'store'
    serializer_class = LoteEstoqueSerializer
    permission_classes = [require_permission('estoque.view')]

    def get_queryset(self):
        qs = LoteEstoque.objects.filter(arena=get_user_arena(self.request.user)).select_related('produto', 'fornecedor')
        produto_id = self.request.query_params.get('produto')
        if produto_id:
            qs = qs.filter(produto_id=produto_id)
        return qs


class AdminMovimentacaoEstoqueViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'store'
    serializer_class = MovimentacaoEstoqueSerializer
    permission_classes = [require_permission('estoque.view')]

    def get_queryset(self):
        qs = MovimentacaoEstoque.objects.filter(arena=get_user_arena(self.request.user)).select_related('produto', 'criado_por')
        produto_id = self.request.query_params.get('produto')
        if produto_id:
            qs = qs.filter(produto_id=produto_id)
        return qs


class VendaViewSet(FeatureEnabledMixin, viewsets.ModelViewSet):
    feature_key = 'store'
    """
    POST /api/vendas/  ← cliente cria pedido
    GET /api/vendas/   ← lista os meus pedidos
    """
    serializer_class = VendaSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # bloqueia PUT/DELETE

    def get_queryset(self):
        return (
            Venda.objects
            .filter(arena=get_user_arena(self.request.user))
            .filter(cliente=self.request.user)
            .select_related('cliente')
            .prefetch_related('itens__produto')
        )

    def perform_create(self, serializer):
        # Cliente é sempre o usuário logado (segurança)
        serializer.save(cliente=self.request.user, arena=get_user_arena(self.request.user))


class AdminVendaViewSet(FeatureEnabledMixin, viewsets.ReadOnlyModelViewSet):
    feature_key = 'store'
    serializer_class = VendaSerializer
    permission_classes = [require_permission('pedidos.view')]

    def get_queryset(self):
        qs = (
            Venda.objects
            .filter(arena=get_user_arena(self.request.user))
            .select_related('cliente')
            .prefetch_related('itens__produto')
        )
        status_filtro = self.request.query_params.get('status')
        if status_filtro in ['aberta', 'paga', 'cancelada']:
            qs = qs.filter(status=status_filtro)
        return qs
