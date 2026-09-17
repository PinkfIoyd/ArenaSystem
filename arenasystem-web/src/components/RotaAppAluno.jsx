import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import api from '../api/client';
import { canUseStudentApp } from '../auth/permissions';

function RotaAppAluno({ children }) {
  const [state, setState] = useState(() => ({
    status: localStorage.getItem('access_token') ? 'loading' : 'unauthenticated',
    user: null,
  }));
  const location = useLocation();

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem('access_token');
    if (!token) return undefined;

    async function loadUser() {
      try {
        const { data } = await api.get('/usuarios/me/');
        if (active) {
          setState({ status: canUseStudentApp(data) ? 'ready' : 'denied', user: data });
        }
      } catch {
        if (active) setState({ status: 'unauthenticated', user: null });
      }
    }

    void loadUser();
    return () => {
      active = false;
    };
  }, []);

  if (state.status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-500">
        Carregando App aluno...
      </div>
    );
  }

  if (state.status === 'unauthenticated') return <Navigate to="/login" replace />;
  if (state.status === 'denied') return <Navigate to="/acesso-negado" replace />;
  if (state.user?.papel_efetivo === 'professor' && location.pathname === '/app') {
    return <Navigate to="/app/professor" replace />;
  }

  return children;
}

export default RotaAppAluno;
