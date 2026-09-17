import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';
import CardProduto from '../components/CardProduto';
import Icon from '../components/Icon';

function Loja() {
  const [produtos, setProdutos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [filtroCategoria, setFiltroCategoria] = useState('todas');
  const [filtroTipo, setFiltroTipo] = useState('todos');
  const [busca, setBusca] = useState('');
  const [erro, setErro] = useState('');

  const carregarDados = useCallback(async () => {
    setCarregando(true);
    setErro('');
    try {
      const [respProdutos, respCategorias] = await Promise.all([
        api.get('/produtos/'),
        api.get('/categorias/'),
      ]);
      setProdutos(Array.isArray(respProdutos.data) ? respProdutos.data : respProdutos.data.results || []);
      setCategorias(Array.isArray(respCategorias.data) ? respCategorias.data : respCategorias.data.results || []);
    } catch (err) {
      console.error('Erro ao carregar loja:', err);
      setErro('Nao foi possivel carregar a loja agora.');
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    const id = setTimeout(carregarDados, 0);
    return () => clearTimeout(id);
  }, [carregarDados]);

  const produtosFiltrados = useMemo(() => produtos.filter((p) => {
    if (filtroCategoria !== 'todas' && p.categoria !== Number(filtroCategoria)) return false;
    if (filtroTipo === 'venda' && p.is_aluguel) return false;
    if (filtroTipo === 'aluguel' && !p.is_aluguel) return false;
    if (busca && !p.nome.toLowerCase().includes(busca.toLowerCase())) return false;
    return true;
  }), [produtos, filtroCategoria, filtroTipo, busca]);

  const totalDisponivel = produtos.filter((p) => p.estoque > 0).length;

  return (
    <Layout>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="page-kicker">Loja do aluno</p>
          <h2 className="page-title">Produtos disponiveis</h2>
          <p className="page-subtitle">Uniformes e itens liberados para compra pelo app.</p>
        </div>
        <div className="grid min-w-[260px] grid-cols-2 gap-3">
          <MiniResumo label="Produtos" valor={produtos.length} />
          <MiniResumo label="Disponiveis" valor={totalDisponivel} />
        </div>
      </div>

      <div className="app-surface mb-6 p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
          <div className="relative">
            <Icon name="stock" className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar produto..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              className="field-control pl-10"
            />
          </div>

          <div className="segmented-control">
            <FiltroButton ativo={filtroTipo === 'todos'} onClick={() => setFiltroTipo('todos')}>Todos</FiltroButton>
            <FiltroButton ativo={filtroTipo === 'venda'} onClick={() => setFiltroTipo('venda')}>Venda</FiltroButton>
            <FiltroButton ativo={filtroTipo === 'aluguel'} onClick={() => setFiltroTipo('aluguel')}>Aluguel</FiltroButton>
          </div>
        </div>

        {categorias.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            <CategoriaButton ativo={filtroCategoria === 'todas'} onClick={() => setFiltroCategoria('todas')}>
              Todas as categorias
            </CategoriaButton>
            {categorias.map((categoria) => (
              <CategoriaButton
                key={categoria.id}
                ativo={filtroCategoria === String(categoria.id)}
                onClick={() => setFiltroCategoria(String(categoria.id))}
              >
                {categoria.nome}
              </CategoriaButton>
            ))}
          </div>
        )}
      </div>

      {erro && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {erro}
        </div>
      )}

      {carregando ? (
        <EstadoVazio icon="queue" titulo="Carregando produtos..." />
      ) : produtosFiltrados.length === 0 ? (
        <EstadoVazio
          icon="box"
          titulo="Nenhum produto encontrado"
          texto="Tente ajustar os filtros ou a busca."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {produtosFiltrados.map((produto) => (
            <CardProduto key={produto.id} produto={produto} />
          ))}
        </div>
      )}
    </Layout>
  );
}

function MiniResumo({ label, valor }) {
  return (
    <div className="metric-card">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="text-2xl font-bold text-slate-950">{valor}</p>
    </div>
  );
}

function FiltroButton({ ativo, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`segmented-option ${ativo ? 'segmented-option-active' : ''}`}
    >
      {children}
    </button>
  );
}

function CategoriaButton({ ativo, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
        ativo ? 'accent-gradient shadow-md' : 'bg-slate-100 text-slate-600 hover:bg-[var(--arena-primary-soft)] hover:text-[var(--arena-primary)]'
      }`}
    >
      {children}
    </button>
  );
}

function EstadoVazio({ icon, titulo, texto }) {
  return (
    <div className="app-surface py-12 text-center">
      <div className="tenant-icon mx-auto mb-3 h-12 w-12 rounded-full">
        <Icon name={icon} className="h-6 w-6" />
      </div>
      <p className="font-semibold text-slate-700">{titulo}</p>
      {texto && <p className="mt-1 text-sm text-slate-400">{texto}</p>}
    </div>
  );
}

export default Loja;
