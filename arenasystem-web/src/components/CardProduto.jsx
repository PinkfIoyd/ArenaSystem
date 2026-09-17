import { useCarrinho } from '../contexts/useCarrinho';
import { formatarMoeda } from '../utils/format';
import Icon from './Icon';

function CardProduto({ produto }) {
  const { itens, adicionar, alterarQuantidade } = useCarrinho();
  const itemNoCarrinho = itens.find((i) => i.produto.id === produto.id);
  const quantidadeAtual = itemNoCarrinho?.quantidade || 0;
  const semEstoque = produto.estoque === 0;

  return (
    <div className="app-surface-hover overflow-hidden">
      <div className="relative flex h-40 items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--arena-primary-soft), white, var(--arena-secondary-soft))' }}>
        {produto.imagem ? (
          <img
            src={`http://127.0.0.1:8000${produto.imagem}`}
            alt={produto.nome}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="tenant-icon h-16 w-16 rounded-2xl bg-white shadow-sm">
            <Icon name={produto.is_aluguel ? 'court' : 'cart'} className="h-8 w-8" />
          </div>
        )}

        <div className="absolute left-2 top-2">
          {produto.is_aluguel ? (
            <span className="rounded bg-violet-50 px-2 py-1 text-xs font-semibold text-violet-700">
              Aluguel
            </span>
          ) : (
            <span className="rounded bg-sky-50 px-2 py-1 text-xs font-semibold text-sky-700">
              Venda
            </span>
          )}
        </div>

        {!semEstoque && produto.estoque <= 3 && (
          <div className="absolute right-2 top-2">
            <span className="rounded bg-red-50 px-2 py-1 text-xs font-semibold text-red-700">
              Ultimas {produto.estoque}
            </span>
          </div>
        )}
      </div>

      <div className="p-4">
        <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
          {produto.categoria_nome}
        </p>
        <h3 className="mb-2 mt-1 line-clamp-1 font-bold text-slate-950">
          {produto.nome}
        </h3>
        {produto.descricao && (
          <p className="mb-3 line-clamp-2 text-sm text-slate-500">
            {produto.descricao}
          </p>
        )}

        <div className="mb-3 flex items-baseline justify-between">
          <span className="tenant-link text-2xl font-bold">
            {formatarMoeda(produto.preco)}
          </span>
          <span className="text-xs text-slate-500">
            Estoque: {produto.estoque}
          </span>
        </div>

        {semEstoque ? (
          <button
            disabled
            className="w-full cursor-not-allowed rounded-lg bg-slate-100 py-2 font-semibold text-slate-400"
          >
            Sem estoque
          </button>
        ) : quantidadeAtual === 0 ? (
          <button
            onClick={() => adicionar(produto)}
            className="btn-primary w-full py-2"
          >
            <span>+</span> Adicionar
          </button>
        ) : (
          <div className="flex items-center justify-between rounded-lg p-1" style={{ background: 'var(--arena-primary-soft)' }}>
            <button
              onClick={() => alterarQuantidade(produto.id, quantidadeAtual - 1)}
              className="tenant-link h-8 w-8 rounded-md bg-white font-bold transition hover:opacity-80"
            >
              -
            </button>
            <span className="tenant-link font-bold">{quantidadeAtual}</span>
            <button
              onClick={() => alterarQuantidade(produto.id, quantidadeAtual + 1)}
              disabled={quantidadeAtual >= produto.estoque}
              className="tenant-link h-8 w-8 rounded-md bg-white font-bold transition hover:opacity-80 disabled:opacity-30"
            >
              +
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default CardProduto;
