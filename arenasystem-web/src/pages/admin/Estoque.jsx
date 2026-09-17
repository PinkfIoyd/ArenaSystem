import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../../api/client';
import Toast from '../../components/Toast';
import Icon from '../../components/Icon';
import { formatarData, formatarMoeda } from '../../utils/format';

function Estoque() {
  const [produtos, setProdutos] = useState([]);
  const [fornecedores, setFornecedores] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [processando, setProcessando] = useState(null);
  const [toast, setToast] = useState(null);
  const [busca, setBusca] = useState('');
  const [filtro, setFiltro] = useState('todos');

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const [respProdutos, respFornecedores] = await Promise.all([
        api.get('/admin/produtos/'),
        api.get('/admin/fornecedores/'),
      ]);
      setProdutos(Array.isArray(respProdutos.data) ? respProdutos.data : respProdutos.data.results || []);
      setFornecedores(Array.isArray(respFornecedores.data) ? respFornecedores.data : respFornecedores.data.results || []);
    } catch {
      setToast({ mensagem: 'Erro ao carregar estoque', tipo: 'erro' });
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const produtosBalcao = useMemo(
    () => produtos.filter((produto) => ['balcao', 'ambos'].includes(produto.canal)),
    [produtos],
  );

  const produtosFiltrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return produtosBalcao.filter((produto) => {
      if (filtro === 'baixo' && !produto.estoque_baixo) return false;
      if (filtro === 'validade' && !produto.vencimento_proximo && !produto.vencido) return false;
      if (filtro === 'vencido' && !produto.vencido) return false;
      if (!termo) return true;
      return [
        produto.nome,
        produto.sku,
        produto.codigo_barras,
        produto.categoria_nome,
        produto.fornecedor_nome,
      ].some((valor) => String(valor || '').toLowerCase().includes(termo));
    });
  }, [produtosBalcao, busca, filtro]);

  const resumo = useMemo(() => {
    const estoqueTotal = produtosBalcao.reduce((total, produto) => total + Number(produto.estoque || 0), 0);
    const valorVenda = produtosBalcao.reduce(
      (total, produto) => total + Number(produto.estoque || 0) * Number(produto.preco || 0),
      0,
    );
    const valorCusto = produtosBalcao.reduce(
      (total, produto) => total + Number(produto.estoque || 0) * Number(produto.custo_unitario || 0),
      0,
    );
    const baixos = produtosBalcao.filter((produto) => produto.estoque_baixo);
    const validade = produtosBalcao.filter((produto) => produto.vencimento_proximo || produto.vencido);

    return {
      estoqueTotal,
      valorVenda,
      valorCusto,
      lucroProjetado: valorVenda - valorCusto,
      baixos,
      validade,
      itensBalcao: produtosBalcao.length,
    };
  }, [produtosBalcao]);

  const movimentar = async (produto, acao, payload) => {
    setProcessando(`${acao}-${produto.id}`);
    try {
      const { data } = await api.post(`/admin/produtos/${produto.id}/${acao}/`, payload);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
      await carregar();
    } catch (err) {
      setToast({ mensagem: err.response?.data?.detail || 'Erro ao atualizar estoque', tipo: 'erro' });
    } finally {
      setProcessando(null);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">Operação de balcão</p>
          <h2 className="mb-1 text-3xl font-bold text-gray-900">Estoque</h2>
          <p className="text-sm text-gray-600">
            Controle de produtos, margem, fornecedores, lotes e validade.
          </p>
        </div>
        <button
          type="button"
          onClick={carregar}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50"
        >
          <Icon name="refresh" className="h-4 w-4" />
          Atualizar
        </button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <ResumoCard titulo="Itens" valor={resumo.itensBalcao} detalhe="Produtos de balcão" />
        <ResumoCard titulo="Unidades" valor={resumo.estoqueTotal} detalhe="Total físico" />
        <ResumoCard titulo="Valor venda" valor={formatarMoeda(resumo.valorVenda)} detalhe="Preço final" />
        <ResumoCard titulo="Custo" valor={formatarMoeda(resumo.valorCusto)} detalhe="Capital estimado" />
        <ResumoCard titulo="Lucro proj." valor={formatarMoeda(resumo.lucroProjetado)} detalhe="Venda - custo" destaque />
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <AlertaLista
          titulo="Reposição"
          vazio="Nenhum produto abaixo do mínimo."
          produtos={resumo.baixos}
          tom="red"
          detalhe={(produto) => `${produto.estoque} em estoque, mínimo ${produto.estoque_minimo}`}
        />
        <AlertaLista
          titulo="Validade"
          vazio="Nenhum lote vencido ou perto do vencimento."
          produtos={resumo.validade}
          tom="cyan"
          detalhe={(produto) => produto.validade_mais_proxima ? `Validade: ${formatarData(produto.validade_mais_proxima)}` : 'Sem validade informada'}
        />
      </div>

      <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
          <input
            type="text"
            value={busca}
            onChange={(event) => setBusca(event.target.value)}
            placeholder="Buscar por produto, SKU, fornecedor ou categoria..."
            className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <div className="flex rounded-lg bg-gray-100 p-1">
            <FiltroButton ativo={filtro === 'todos'} onClick={() => setFiltro('todos')}>Todos</FiltroButton>
            <FiltroButton ativo={filtro === 'baixo'} onClick={() => setFiltro('baixo')}>Baixo</FiltroButton>
            <FiltroButton ativo={filtro === 'validade'} onClick={() => setFiltro('validade')}>Validade</FiltroButton>
            <FiltroButton ativo={filtro === 'vencido'} onClick={() => setFiltro('vencido')}>Vencidos</FiltroButton>
          </div>
        </div>
      </div>

      {carregando ? (
        <div className="rounded-xl bg-white py-14 text-center text-gray-500 shadow-sm">
          Carregando estoque...
        </div>
      ) : produtosFiltrados.length === 0 ? (
        <div className="rounded-xl bg-white py-14 text-center shadow-sm">
          <p className="font-semibold text-gray-700">Nenhum produto encontrado</p>
          <p className="mt-1 text-sm text-gray-400">Ajuste a busca ou os filtros.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 2xl:grid-cols-3">
          {produtosFiltrados.map((produto) => (
            <ProdutoBalcao
              key={`${produto.id}-${produto.estoque}-${produto.custo_unitario}-${produto.fornecedor || ''}`}
              produto={produto}
              fornecedores={fornecedores}
              processando={processando}
              onVenda={(quantidade) => movimentar(produto, 'venda-balcao', { quantidade })}
              onEntrada={(payload) => movimentar(produto, 'entrada', payload)}
              onAjuste={(estoque) => movimentar(produto, 'ajuste', { estoque })}
            />
          ))}
        </div>
      )}

      {toast && <Toast mensagem={toast.mensagem} tipo={toast.tipo} onClose={() => setToast(null)} />}
    </div>
  );
}

function ResumoCard({ titulo, valor, detalhe, alerta = false, destaque = false }) {
  return (
    <div className={`rounded-xl border bg-white p-4 shadow-sm ${alerta ? 'border-red-100' : 'border-gray-100'}`}>
      <p className="text-xs font-bold uppercase tracking-wide text-gray-500">{titulo}</p>
      <p className={`mt-1 text-2xl font-bold ${alerta ? 'text-red-700' : destaque ? 'text-green-700' : 'text-gray-900'}`}>{valor}</p>
      <p className="mt-1 text-xs text-gray-500">{detalhe}</p>
    </div>
  );
}

function AlertaLista({ titulo, vazio, produtos, detalhe, tom }) {
  const cores = tom === 'red'
    ? 'border-red-100 bg-red-50 text-red-800'
    : 'border-cyan-100 bg-cyan-50 text-cyan-800';
  return (
    <div className={`rounded-xl border p-4 text-sm ${cores}`}>
      <div className="mb-2 font-bold">{titulo}</div>
      {produtos.length === 0 ? (
        <p className="opacity-75">{vazio}</p>
      ) : (
        <div className="space-y-1">
          {produtos.slice(0, 5).map((produto) => (
            <div key={produto.id} className="flex justify-between gap-3">
              <span className="font-semibold">{produto.nome}</span>
              <span className="text-right opacity-80">{detalhe(produto)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FiltroButton({ ativo, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-2 text-xs font-bold transition ${
        ativo ? 'bg-white text-teal-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
      }`}
    >
      {children}
    </button>
  );
}

function ProdutoBalcao({ produto, fornecedores, processando, onVenda, onEntrada, onAjuste }) {
  const [quantidade, setQuantidade] = useState(1);
  const [entrada, setEntrada] = useState({
    quantidade: 12,
    codigo_lote: '',
    validade: '',
    custo_unitario: produto.custo_unitario || 0,
    fornecedor: produto.fornecedor || '',
  });
  const [estoqueAjuste, setEstoqueAjuste] = useState(produto.estoque);

  const ocupado = processando?.endsWith(`-${produto.id}`);
  const semEstoque = produto.estoque <= 0;
  const canalLabel = produto.canal === 'ambos' ? 'App e balcão' : 'Balcão';

  const vendaRapida = (qtd) => {
    setQuantidade(qtd);
    onVenda(qtd);
  };

  const atualizarEntrada = (campo, valor) => {
    setEntrada((atual) => ({ ...atual, [campo]: valor }));
  };

  return (
    <section className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm">
      <div className="border-b border-gray-100 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap gap-2">
              <Tag>{produto.categoria_nome}</Tag>
              <Tag>{canalLabel}</Tag>
              {produto.sku && <Tag>SKU {produto.sku}</Tag>}
            </div>
            <h3 className="truncate text-xl font-bold text-gray-900">{produto.nome}</h3>
            <p className="mt-1 text-sm text-gray-500">
              {formatarMoeda(produto.preco)} venda · {formatarMoeda(produto.custo_unitario)} custo · {produto.margem_percentual}% margem
            </p>
            {produto.fornecedor_nome && (
              <p className="mt-1 text-xs text-gray-500">Fornecedor: {produto.fornecedor_nome}</p>
            )}
          </div>
          <div className="text-right">
            <span className={`inline-flex min-w-16 justify-center rounded-lg px-3 py-1 text-lg font-bold ${
              produto.estoque_baixo ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
            }`}>
              {produto.estoque}
            </span>
            <p className="mt-1 text-xs text-gray-500">min. {produto.estoque_minimo}</p>
          </div>
        </div>
      </div>

      <div className="space-y-4 p-4">
        <LotesResumo produto={produto} />

        <div>
          <p className="mb-2 text-xs font-bold uppercase tracking-wide text-gray-500">Venda rápida</p>
          <div className="grid grid-cols-3 gap-2">
            {[1, 2, 3].map((qtd) => (
              <button
                key={qtd}
                type="button"
                disabled={ocupado || semEstoque || produto.estoque < qtd}
                onClick={() => vendaRapida(qtd)}
                className="rounded-lg bg-teal-700 px-3 py-3 text-sm font-bold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-400"
              >
                Vender {qtd}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-lg bg-gray-50 p-3">
          <label className="text-xs font-bold uppercase tracking-wide text-gray-500">Quantidade personalizada</label>
          <div className="mt-2 flex gap-2">
            <input
              type="number"
              min="1"
              value={quantidade}
              onChange={(event) => setQuantidade(Number(event.target.value))}
              className="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-cyan-500"
            />
            <button
              type="button"
              disabled={ocupado || semEstoque}
              onClick={() => onVenda(quantidade)}
              className="flex-1 rounded-lg bg-gray-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-gray-800 disabled:opacity-50"
            >
              Registrar venda
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 p-3">
          <p className="mb-3 text-xs font-bold uppercase tracking-wide text-gray-500">Entrada com lote</p>
          <div className="grid grid-cols-2 gap-2">
            <CampoEntrada label="Qtd." type="number" value={entrada.quantidade} onChange={(valor) => atualizarEntrada('quantidade', Number(valor))} />
            <CampoEntrada label="Custo" type="number" value={entrada.custo_unitario} onChange={(valor) => atualizarEntrada('custo_unitario', valor)} />
            <CampoEntrada label="Lote" value={entrada.codigo_lote} onChange={(valor) => atualizarEntrada('codigo_lote', valor)} />
            <CampoEntrada label="Validade" type="date" value={entrada.validade} onChange={(valor) => atualizarEntrada('validade', valor)} />
          </div>
          <select
            value={entrada.fornecedor}
            onChange={(event) => atualizarEntrada('fornecedor', event.target.value)}
            className="mt-2 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <option value="">Fornecedor do produto</option>
            {fornecedores.map((fornecedor) => (
              <option key={fornecedor.id} value={fornecedor.id}>{fornecedor.nome}</option>
            ))}
          </select>
          <button
            type="button"
            disabled={ocupado || Number(entrada.quantidade) <= 0}
            onClick={() => onEntrada(entrada)}
            className="mt-2 w-full rounded-lg bg-gray-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-gray-800 disabled:opacity-50"
          >
            Registrar entrada
          </button>
        </div>

        <ControleEstoque
          label="Ajustar inventário para"
          value={estoqueAjuste}
          min="0"
          onChange={setEstoqueAjuste}
          onConfirm={() => onAjuste(estoqueAjuste)}
          disabled={ocupado}
        />
      </div>
    </section>
  );
}

function LotesResumo({ produto }) {
  const lotes = produto.lotes_abertos || [];
  if (lotes.length === 0) {
    return <p className="rounded-lg bg-gray-50 p-3 text-xs text-gray-500">Sem lotes abertos cadastrados.</p>;
  }
  return (
    <div className="rounded-lg bg-gray-50 p-3">
      <p className="mb-2 text-xs font-bold uppercase tracking-wide text-gray-500">Lotes abertos</p>
      <div className="space-y-1">
        {lotes.map((lote) => (
          <div key={lote.id} className="flex justify-between gap-2 text-xs text-gray-600">
            <span className="font-semibold">{lote.codigo_lote || `Lote #${lote.id}`}</span>
            <span>{lote.quantidade_atual} un.</span>
            <span>{lote.validade ? formatarData(lote.validade) : 'Sem validade'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Tag({ children }) {
  return (
    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-600">
      {children}
    </span>
  );
}

function CampoEntrada({ label, value, onChange, type = 'text' }) {
  return (
    <label className="text-xs font-bold uppercase tracking-wide text-gray-500">
      {label}
      <input
        type={type}
        value={value}
        min={type === 'number' ? '0' : undefined}
        step={type === 'number' ? '0.01' : undefined}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-normal normal-case tracking-normal outline-none focus:ring-2 focus:ring-cyan-500"
      />
    </label>
  );
}

function ControleEstoque({ label, value, min, onChange, onConfirm, disabled }) {
  return (
    <div>
      <label className="text-xs font-bold uppercase tracking-wide text-gray-500">{label}</label>
      <div className="mt-1 flex gap-2">
        <input
          type="number"
          min={min}
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
          className="min-w-0 flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-cyan-500"
        />
        <button
          type="button"
          disabled={disabled}
          onClick={onConfirm}
          className="rounded-lg bg-gray-100 px-3 py-2 text-xs font-bold text-gray-700 transition hover:bg-gray-200 disabled:opacity-50"
        >
          OK
        </button>
      </div>
    </div>
  );
}

export default Estoque;
