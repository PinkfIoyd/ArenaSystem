import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import api from '../api/client';
import { clearArenaContext } from '../arena/contextStorage';
import { useCarrinho } from '../contexts/useCarrinho';
import useTerminology from '../hooks/useTerminology';
import Carrinho from './Carrinho';
import Icon from './Icon';
import Toast from './Toast';
import PwaControls from './PwaControls';

function Layout({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [carrinhoAberto, setCarrinhoAberto] = useState(false);
  const [sidebarRecolhida, setSidebarRecolhida] = useState(() => localStorage.getItem('arena_sidebar_collapsed') === '1');
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { totalItens } = useCarrinho();
  const { arena, terms, features } = useTerminology();

  useEffect(() => {
    let active = true;
    async function carregarUsuario() {
      try {
        const { data } = await api.get('/usuarios/me/');
        if (active) setUsuario(data);
      } catch {
        if (active) navigate('/login');
      }
    }
    void carregarUsuario();
    return () => {
      active = false;
    };
  }, [navigate]);

  const sair = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    clearArenaContext();
    navigate('/login');
  };

  const alternarSidebar = () => {
    setSidebarRecolhida((valorAtual) => {
      const proximoValor = !valorAtual;
      localStorage.setItem('arena_sidebar_collapsed', proximoValor ? '1' : '0');
      return proximoValor;
    });
  };

  const handlePedidoCriado = (resultado) => {
    if (resultado.erro) {
      setToast({ mensagem: resultado.erro, tipo: 'erro' });
      return;
    }
    setToast({ mensagem: `Pedido #${resultado.id} criado com sucesso.`, tipo: 'sucesso' });
  };

  const ehAdmin = usuario?.tipo === 'admin' || usuario?.is_staff;
  const ehProfessor = usuario?.papel_efetivo === 'professor';
  const menuItensProfessor = [
    { path: '/app/professor', label: 'Aulas', icon: 'calendar', exact: true },
    { path: '/app/turmas', label: 'Turmas', icon: 'court' },
    { path: '/app/notificacoes', label: 'Alertas', icon: 'inbox' },
    { path: '/app/perfil', label: 'Perfil', icon: 'users' },
  ];
  const menuItensAluno = [
    { path: '/app', label: 'Início', icon: 'home', exact: true },
    ...(features.classes ? [{ path: '/app/turmas', label: 'Turmas', icon: 'court' }] : []),
    ...(features.openAccess
      ? [{ path: '/app/acessos', label: 'Acessos', icon: 'check' }]
      : features.classes ? [{ path: '/app/checkins', label: 'Presenças', icon: 'check' }] : []),
    { path: '/app/notificacoes', label: 'Alertas', icon: 'inbox' },
    { path: '/app/perfil', label: 'Perfil', icon: 'users' },
  ];
  const menuItens = ehProfessor
    ? menuItensProfessor.filter((item) => features.classes || !['/app/professor', '/app/turmas'].includes(item.path))
    : menuItensAluno;

  const itemAtivo = (item) => item.exact
    ? location.pathname === item.path
    : location.pathname.startsWith(item.path);

  return (
    <div className="app-shell-bg min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-[1600px]">
        <aside className={`sticky top-0 hidden h-screen shrink-0 border-r border-white/70 bg-white/70 px-4 py-4 shadow-xl backdrop-blur-xl transition-all duration-300 lg:flex lg:flex-col ${sidebarRecolhida ? 'w-20' : 'w-64'}`} style={{ boxShadow: '0 18px 44px var(--arena-shadow)' }}>
          <div className={`mb-6 flex items-center ${sidebarRecolhida ? 'justify-center' : 'justify-between gap-2'}`}>
            <Link to="/app" className={`flex min-w-0 flex-1 items-center gap-3 font-bold ${sidebarRecolhida ? 'justify-center' : ''}`}>
              <BrandMark arena={arena} />
              {!sidebarRecolhida && <span className="sidebar-brand-name">{arena.nome}</span>}
            </Link>
            {!sidebarRecolhida && (
              <button
                type="button"
                onClick={alternarSidebar}
                className="btn-secondary px-2 py-2 text-slate-500"
                aria-label="Recolher barra lateral"
                title="Recolher barra lateral"
              >
                <Icon name="chevronLeft" className="h-4 w-4" />
              </button>
            )}
          </div>

          {sidebarRecolhida && (
            <button
              type="button"
              onClick={alternarSidebar}
              className="btn-secondary mb-4 px-2 py-2 text-slate-500"
              aria-label="Expandir barra lateral"
              title="Expandir barra lateral"
            >
              <Icon name="chevronRight" className="mx-auto h-4 w-4" />
            </button>
          )}

          <div className={`mb-3 px-3 text-[11px] font-bold uppercase tracking-wide text-slate-400 ${sidebarRecolhida ? 'sr-only' : ''}`}>
            App do aluno
          </div>
          <nav className="space-y-1" aria-label="App aluno">
            {menuItens.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                title={sidebarRecolhida ? item.label : undefined}
                className={`nav-item ${sidebarRecolhida ? 'justify-center px-2' : ''} ${itemAtivo(item) ? 'nav-item-active' : 'nav-item-idle'}`}
              >
                <Icon name={item.icon} className="h-4 w-4" />
                {!sidebarRecolhida && <span>{item.label}</span>}
              </Link>
            ))}
          </nav>

          {sidebarRecolhida ? (
            <div className="mt-auto space-y-2">
              {ehAdmin && (
                <Link to="/admin" className="btn-secondary w-full px-2 py-2" title="Painel admin">
                  <Icon name="settings" className="h-4 w-4" />
                </Link>
              )}
            </div>
          ) : (
            <div className="glass-panel mt-auto p-3">
              <p className="muted-label">Conta</p>
              <p className="mt-1 truncate text-sm font-bold text-slate-900">
                {usuario?.nome_completo || usuario?.username || 'Carregando...'}
              </p>
              {ehAdmin && (
                <Link to="/admin" className="btn-secondary mt-3 w-full justify-start px-3 py-2">
                  <Icon name="settings" className="h-4 w-4" />
                  Painel admin
                </Link>
              )}
            </div>
          )}
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="mobile-app-header sticky top-0 z-30 border-b border-white/70 bg-white/80 backdrop-blur-xl lg:shadow-lg" style={{ boxShadow: '0 8px 28px rgba(15, 23, 42, 0.06)' }}>
            <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between gap-3 px-4 py-3 lg:px-8">
              <Link to="/app" className="flex min-w-0 items-center gap-3 lg:hidden">
                <BrandMark arena={arena} />
                <span className="min-w-0 leading-tight">
                  <span className="block text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">ArenaFlow</span>
                  <span className="block truncate text-sm font-black text-slate-950">{arena.nome}</span>
                </span>
              </Link>

              <div className="hidden lg:block">
                <p className="muted-label">ArenaFlow</p>
                <p className="text-sm font-semibold text-slate-700">Rotina da {terms.unidade_singular} em tempo real</p>
              </div>

              <div className="ml-auto flex shrink-0 items-center gap-2">
                {ehAdmin && (
                  <Link
                    to="/admin"
                    className="btn-primary hidden px-3 py-2 md:inline-flex"
                    title="Acessar Painel admin"
                  >
                    <Icon name="settings" className="h-4 w-4" />
                    Painel admin
                  </Link>
                )}

                {features.store && <button
                  type="button"
                  onClick={() => setCarrinhoAberto(true)}
                  className="mobile-header-action relative grid h-10 w-10 place-items-center rounded-full border border-slate-100 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50"
                  aria-label="Abrir carrinho"
                >
                  <Icon name="cart" className="h-5 w-5" />
                  {totalItens > 0 && (
                    <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-xs font-bold text-white">
                      {totalItens}
                    </span>
                  )}
                </button>}

                <Link
                  to="/app/notificacoes"
                  className="mobile-header-action relative grid h-10 w-10 place-items-center rounded-full border border-slate-100 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 lg:hidden"
                  aria-label="Abrir notificacoes"
                >
                  <Icon name="inbox" className="h-5 w-5" />
                </Link>

                <Link
                  to="/app/perfil"
                  className="grid h-10 w-10 place-items-center overflow-hidden rounded-full text-xs font-black text-white shadow-sm lg:hidden"
                  style={{ background: 'linear-gradient(135deg, var(--arena-primary), color-mix(in srgb, var(--arena-primary) 62%, var(--arena-secondary)))' }}
                  aria-label="Abrir perfil"
                >
                  {usuario?.foto ? <img src={usuario.foto} alt="" className="h-full w-full object-cover" /> : getInitials(usuario)}
                </Link>

                <span className="hidden max-w-[160px] truncate text-sm font-medium text-slate-700 md:block">
                  {usuario?.nome_completo || usuario?.username || '...'}
                </span>
                <button
                  type="button"
                  onClick={sair}
                  className="hidden rounded-lg bg-red-500 px-3 py-2 text-sm font-semibold text-white shadow-sm transition duration-300 hover:-translate-y-0.5 hover:bg-red-600 lg:inline-flex"
                >
                  Sair
                </button>
              </div>
            </div>

          </header>

            <nav className="mobile-bottom-nav fixed inset-x-0 bottom-0 z-50 mx-auto flex max-w-[560px] justify-around border-t border-slate-100 bg-white/95 px-2 pb-[max(0.55rem,env(safe-area-inset-bottom))] pt-2 shadow-[0_-10px_28px_rgba(15,23,42,0.08)] backdrop-blur-xl lg:hidden" aria-label="Navegação principal mobile">
              {menuItens.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  aria-current={itemAtivo(item) ? 'page' : undefined}
                  className={`mobile-nav-link flex min-w-0 flex-1 flex-col items-center gap-1 px-1 py-1 text-[10px] font-bold transition ${
                    itemAtivo(item) ? 'text-[var(--arena-primary)]' : 'text-slate-400'
                  }`}
                >
                  <span className={`grid h-8 w-11 place-items-center rounded-full transition ${itemAtivo(item) ? 'bg-[var(--arena-primary-soft)]' : ''}`}>
                    <Icon name={item.icon} className="h-5 w-5" strokeWidth={itemAtivo(item) ? 2.3 : 1.8} />
                  </span>
                  <span className="whitespace-nowrap">{item.label}</span>
                </Link>
              ))}
            </nav>
          <main className="mobile-app-main mx-auto w-full max-w-[560px] px-4 pb-28 pt-5 lg:max-w-none lg:px-8 lg:py-8">{children}</main>
        </div>
      </div>

      {features.store && <Carrinho
        aberto={carrinhoAberto}
        onFechar={() => setCarrinhoAberto(false)}
        onPedidoCriado={handlePedidoCriado}
      />}

      {toast && <Toast mensagem={toast.mensagem} tipo={toast.tipo} onClose={() => setToast(null)} />}
      <PwaControls />
    </div>
  );
}

function BrandMark({ arena }) {
  return (
    <span className="brand-mark h-10 w-10">
      {arena.logo ? (
        <img src={arena.logo} alt={arena.nome} className="h-full w-full object-cover" />
      ) : (
        <Icon name="court" className="h-5 w-5" />
      )}
    </span>
  );
}

function getInitials(usuario) {
  const name = usuario?.nome_completo || usuario?.username || 'AF';
  return name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
}

export default Layout;
