import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import api from '../api/client';

function RotaAdmin({ children }) {
  const [status, setStatus] = useState(() =>
    localStorage.getItem('access_token') ? 'verificando' : 'sem-token'
  ); // verificando | ok | negado | sem-token

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return;
    }

    api.get('/usuarios/me/')
      .then(({ data }) => {
        // Permitir se for staff/admin do Django OU se o tipo for 'admin'
        if (data.tipo === 'admin') {
          setStatus('ok');
        } else {
          // Tenta acessar endpoint de admin para confirmar
          api.get('/dashboard/metricas/')
            .then(() => setStatus('ok'))
            .catch(() => setStatus('negado'));
        }
      })
      .catch(() => setStatus('sem-token'));
  }, []);

  if (status === 'verificando') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">⏳</div>
          <p className="text-gray-500">Verificando permissões...</p>
        </div>
      </div>
    );
  }

  if (status === 'sem-token') {
    return <Navigate to="/login" replace />;
  }

  if (status === 'negado') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="bg-white rounded-2xl p-8 max-w-md text-center shadow-lg">
          <div className="text-6xl mb-4">🚫</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            Acesso restrito
          </h1>
          <p className="text-gray-600 mb-6">
            Apenas administradores podem acessar essa página.
          </p>
          <a
            href="/"
            className="inline-block bg-teal-700 hover:bg-teal-800 text-white font-semibold px-6 py-2 rounded-lg transition"
          >
            Voltar ao início
          </a>
        </div>
      </div>
    );
  }

  return children;
}

export default RotaAdmin;
