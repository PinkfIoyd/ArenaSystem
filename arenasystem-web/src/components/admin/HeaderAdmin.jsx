import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import SinoNotificacoes from '../SinoNotificacoes';
import useTerminology from '../../hooks/useTerminology';
import { clearArenaContext } from '../../arena/contextStorage';

function HeaderAdmin() {
  const [usuario, setUsuario] = useState(null);
  const navigate = useNavigate();
  const { arena, terms } = useTerminology();

  useEffect(() => {
    api.get('/usuarios/me/')
      .then(({ data }) => setUsuario(data))
      .catch(() => navigate('/login'));
  }, [navigate]);

  const sair = async () => {
    const refresh = localStorage.getItem('refresh_token');
    try {
      await api.post('/auth/logout/', { refresh });
    } catch {
      // A limpeza local deve ocorrer mesmo se a API estiver indisponivel.
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    clearArenaContext();
    navigate('/login');
  };

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white/95 px-6 py-3 shadow-sm backdrop-blur">
      <div>
        <p className="muted-label">Painel administrativo</p>
        <p className="mt-0.5 font-semibold text-slate-950">
          {arena.nome} / {usuario?.nome_completo || usuario?.username || 'Carregando...'}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => navigate('/app')}
          className="btn-secondary px-3 py-2"
        >
          App do {terms.pessoa_singular}
        </button>

        <SinoNotificacoes />

        <button
          type="button"
          onClick={() => { void sair(); }}
          className="rounded-md bg-red-500 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-red-600"
        >
          Sair
        </button>
      </div>
    </header>
  );
}

export default HeaderAdmin;
