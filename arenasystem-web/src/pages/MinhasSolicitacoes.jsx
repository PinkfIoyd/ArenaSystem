import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';
import Badge from '../components/Badge';
import Toast from '../components/Toast';
import { formatarData } from '../utils/format';

function MinhasSolicitacoes() {
  const [solicitacoes, setSolicitacoes] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [toast, setToast] = useState(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const { data } = await api.get('/minhas-solicitacoes/');
      setSolicitacoes(Array.isArray(data) ? data : data.results || []);
    } catch {
      setToast({ mensagem: 'Erro ao carregar solicitações', tipo: 'erro' });
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const cancelar = async (id) => {
    if (!confirm('Cancelar esta solicitação?')) return;
    try {
      await api.delete(`/minhas-solicitacoes/${id}/`);
      setToast({ mensagem: 'Solicitação cancelada', tipo: 'sucesso' });
      await carregar();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao cancelar';
      setToast({ mensagem: msg, tipo: 'erro' });
    }
  };

  // Badge por status
  const corStatus = {
    pendente: 'pendente',
    aprovada: 'pago',
    recusada: 'atrasado',
    cancelada: 'cancelada',
  };

  return (
    <Layout>
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">📋 Minhas Solicitações</h2>
        <p className="text-gray-600">Acompanhe o status das suas solicitações</p>
      </div>

      {carregando ? (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-2">⏳</div>
          Carregando...
        </div>
      ) : solicitacoes.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl">
          <div className="text-5xl mb-3">📭</div>
          <p className="text-gray-600 font-medium">Nenhuma solicitação encontrada</p>
          <p className="text-gray-400 text-sm mt-1">
            Vá em "Turmas" para solicitar uma matrícula!
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {solicitacoes.map((s) => (
            <div key={s.id} className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">
                    {s.tipo_display}
                  </p>
                  <h3 className="font-bold text-lg text-gray-800">
                    {s.turma_nome}
                  </h3>
                </div>
                <Badge status={corStatus[s.status]} texto={s.status_display} />
              </div>

              <div className="text-sm text-gray-600 space-y-1">
                <p>📅 Solicitado em: {formatarData(s.data_solicitacao?.slice(0, 10))}</p>
                {s.data_resposta && (
                  <p>✓ Respondido em: {formatarData(s.data_resposta?.slice(0, 10))}</p>
                )}
                {s.observacao_aluno && (
                  <p className="bg-gray-50 p-2 rounded mt-2">
                    💬 <em>"{s.observacao_aluno}"</em>
                  </p>
                )}
                {s.motivo_recusa && (
                  <p className="bg-red-50 p-2 rounded mt-2 text-red-700">
                    ⚠️ <strong>Motivo:</strong> {s.motivo_recusa}
                  </p>
                )}
              </div>

              {s.status === 'pendente' && (
                <button
                  onClick={() => cancelar(s.id)}
                  className="mt-3 text-sm text-red-600 hover:underline"
                >
                  Cancelar solicitação
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {toast && (
        <Toast
          mensagem={toast.mensagem}
          tipo={toast.tipo}
          onClose={() => setToast(null)}
        />
      )}
    </Layout>
  );
}

export default MinhasSolicitacoes;
