import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import api from '../../api/client';
import { adminMenuFor, defaultAdminPath } from '../../auth/permissions';
import SidebarAdmin from './SidebarAdmin';
import HeaderAdmin from './HeaderAdmin';
import MenuMobileAdmin from './MenuMobileAdmin';
import { useArenaContext } from '../../contexts/arenaContextStore';
import { getRole } from '../../auth/permissions';
import useTerminology from '../../hooks/useTerminology';

function LayoutAdmin() {
  const [state, setState] = useState({ status: 'loading', usuario: null });
  const location = useLocation();
  const navigate = useNavigate();
  const { contexto, sairDaArena } = useArenaContext();
  const { terms } = useTerminology();

  useEffect(() => {
    let active = true;

    async function verificarAcesso() {
      const token = localStorage.getItem('access_token');
      if (!token) {
        if (active) setState({ status: 'unauthenticated', usuario: null });
        return;
      }

      try {
        const { data } = await api.get('/usuarios/me/');
        const itens = adminMenuFor(data);
        if (active) {
          setState({ status: itens.length > 0 ? 'ready' : 'denied', usuario: data });
        }
      } catch {
        if (active) setState({ status: 'unauthenticated', usuario: null });
      }
    }

    void verificarAcesso();

    return () => {
      active = false;
    };
  }, []);

  if (state.status === 'loading') {
    return (
      <div className="admin-shell-bg flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">...</div>
          <p className="text-slate-500">Verificando acesso...</p>
        </div>
      </div>
    );
  }

  if (state.status === 'unauthenticated') return <Navigate to="/login" replace />;

  if (state.status === 'denied') {
    return (
      <div className="admin-shell-bg flex min-h-screen items-center justify-center p-6">
        <div className="app-surface max-w-md p-8 text-center">
          <h1 className="mb-2 text-2xl font-bold text-slate-950">Acesso restrito</h1>
          <p className="mb-6 text-slate-600">Seu perfil nao possui area administrativa habilitada.</p>
          <Navigate to="/" replace />
        </div>
      </div>
    );
  }

  if (getRole(state.usuario) === 'superadmin_saas' && !contexto && !location.pathname.startsWith('/admin/saas/')) {
    return <Navigate to="/admin/saas/arenas" replace />;
  }

  if (getRole(state.usuario) === 'dono' && !state.usuario.onboarding_completed && location.pathname !== '/admin/onboarding') {
    return <Navigate to="/admin/onboarding" replace />;
  }

  if (location.pathname === '/admin') {
    if (getRole(state.usuario) === 'superadmin_saas' && contexto) {
      // Contexto explicito libera a visao operacional da arena selecionada.
    } else {
    const destino = defaultAdminPath(state.usuario);
    if (destino !== '/admin') return <Navigate to={destino} replace />;
    }
  }

  return (
    <div className="admin-shell-bg flex min-h-screen">
      <SidebarAdmin />

      <div className="flex-1 flex flex-col min-w-0">
        <HeaderAdmin />
        {getRole(state.usuario) === 'superadmin_saas' && contexto && !location.pathname.startsWith('/admin/saas/') && (
          <div className="sticky top-0 z-40 flex flex-wrap items-center justify-between gap-3 border-b border-amber-300 bg-amber-100 px-6 py-3 text-amber-950 shadow-sm" role="status">
            <div>
              <p className="font-bold">Superadmin visualizando: {contexto.arena.nome}</p>
              {contexto.motivo && <p className="text-xs">Motivo: {contexto.motivo}</p>}
            </div>
            <button type="button" className="rounded-lg border border-amber-400 bg-white px-3 py-1.5 text-sm font-bold" onClick={() => { sairDaArena(); navigate('/admin/saas/arenas'); }}>
              Sair da {terms.unidade_singular}
            </button>
          </div>
        )}
        <MenuMobileAdmin />

        <main className="flex-1 overflow-x-hidden p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default LayoutAdmin;
