import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { formatarData } from '../utils/format';

function SinoNotificacoes() {
  const [contador, setContador] = useState(0);
  const [aberto, setAberto] = useState(false);
  const [notificacoes, setNotificacoes] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    void Promise.resolve().then(atualizarContador);
    // Atualiza a cada 30 segundos
    const interval = setInterval(atualizarContador, 30000);
    return () => clearInterval(interval);
  }, []);

  async function atualizarContador() {
    try {
      const { data } = await api.get('/admin/notificacoes/contador/');
      setContador(data.nao_lidas);
    } catch {
      // silencia erro (talvez não seja admin)
    }
  }

  const abrir = async () => {
    if (!aberto) {
      try {
        const { data } = await api.get('/admin/notificacoes/');
        const lista = Array.isArray(data) ? data : data.results || [];
        setNotificacoes(lista.slice(0, 10));
      } catch {
        // ignora
      }
    }
    setAberto(!aberto);
  };

  const marcarTodasLidas = async () => {
    try {
      await api.post('/admin/notificacoes/marcar-todas-lidas/');
      setContador(0);
      setNotificacoes((atual) => atual.map((n) => ({ ...n, lida: true })));
    } catch {
      // ignora erro momentaneo de rede
    }
  };

  const irPara = async (notif) => {
    // Marca como lida
    try {
      await api.post(`/admin/notificacoes/${notif.id}/marcar-lida/`);
      atualizarContador();
    } catch {
      // ignora erro momentaneo de rede
    }

    // Navega se tem URL
    if (notif.url) {
      setAberto(false);
      navigate(notif.url);
    }
  };

  return (
    <div className="relative z-[10000]">
      <button
        onClick={abrir}
        className="relative bg-gray-100 hover:bg-gray-200 p-2 rounded-lg transition"
        title="Notificações"
      >
        <span className="text-xl">🔔</span>
        {contador > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full min-w-[20px] h-5 px-1 flex items-center justify-center">
            {contador > 9 ? '9+' : contador}
          </span>
        )}
      </button>

      {aberto && (
        <>
          {/* Overlay para fechar ao clicar fora */}
          <div
            className="fixed inset-0 z-[9998]"
            onClick={() => setAberto(false)}
          />

          {/* Dropdown */}
          <div className="fixed right-6 top-20 z-[9999] max-h-[min(28rem,calc(100vh-6rem))] w-[min(24rem,calc(100vw-2rem))] overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-2xl animate-fade-in sm:right-8">
            <div className="p-3 border-b flex justify-between items-center bg-gray-50 rounded-t-xl">
              <h3 className="font-bold text-gray-800">Notificações</h3>
              {contador > 0 && (
                <button
                  onClick={marcarTodasLidas}
                  className="text-xs text-teal-700 hover:underline"
                >
                  Marcar todas como lidas
                </button>
              )}
            </div>

            {notificacoes.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                <div className="text-3xl mb-2">📭</div>
                <p className="text-sm">Nenhuma notificação</p>
              </div>
            ) : (
              <div className="divide-y">
                {notificacoes.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => irPara(n)}
                    className={`w-full text-left p-3 hover:bg-gray-50 transition ${
                      !n.lida ? 'bg-blue-50' : ''
                    }`}
                  >
                    <p className="font-semibold text-sm text-gray-800">
                      {n.titulo}
                    </p>
                    <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                      {n.mensagem}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatarData(n.criada_em?.slice(0, 10))}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default SinoNotificacoes;
