import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import api from '../../api/client';
import { can, defaultAdminPath } from '../../auth/permissions';

function RotaAdminPermissao({ permission, children }) {
  const [state, setState] = useState({ status: 'loading', user: null });

  useEffect(() => {
    let active = true;

    async function loadUser() {
      const token = localStorage.getItem('access_token');
      if (!token) {
        if (active) setState({ status: 'unauthenticated', user: null });
        return;
      }

      try {
        const { data } = await api.get('/usuarios/me/');
        if (active) setState({ status: 'ready', user: data });
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
    return <div className="rounded-xl bg-white p-10 text-center text-gray-500 shadow-sm">Verificando permissao...</div>;
  }

  if (state.status === 'unauthenticated') {
    return <Navigate to="/login" replace />;
  }

  if (!can(state.user, permission)) {
    return <Navigate to={defaultAdminPath(state.user)} replace />;
  }

  return children;
}

export default RotaAdminPermissao;
