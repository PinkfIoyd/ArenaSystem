import { useCallback, useEffect, useState } from 'react';
import api from '../../api/client';
import Badge from '../../components/Badge';
import Toast from '../../components/Toast';
import { formatarData } from '../../utils/format';

function AdminSolicitacoes() {
  const [solicitacoes, setSolicitacoes] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [filtro, setFiltro] = useState('pendente');
  const [toast, setToast] = useState(null);
  const [recusando, setRecusando] = useState(null);
  const [motivo, setMotivo] = useState('');

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const url = filtro === 'todas'
        ? '/admin/solicitacoes/'
        : `/admin/solicitacoes/?status=${filtro}`;
      const { data } = await api.get(url);
      setSolicitacoes(Array.isArray(data) ? data : data.results || []);
    } catch {
      setToast({ mensagem: 'Erro ao carregar', tipo: 'erro' });
    } finally {
      setCarregando(false);
    }
  }, [filtro]);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const aprovar = async (id) => {
    if (!confirm('Aprovar esta solicitação?')) return;
    try {
      const { data } = await api.post(`/admin/solicitacoes/${id}/aprovar/`);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
      await carregar();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao aprovar';
      setToast({ mensagem: msg, tipo: 'erro' });
    }
  };

  const recusar = async (id) => {
    try {
      const { data } = await api.post(`/admin/solicitacoes/${id}/recusar/`, {
        motivo: motivo || 'Sem motivo informado',
      });
      setToast({ mensagem: data.detail, tipo: 'info' });
      setRecusando(null);
      setMotivo('');
      await carregar();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao recusar';
      setToast({ mensagem: msg, tipo: 'erro' });
    }
  };

  const cancelarRecusa = () => {
    setRecusando(null);
    setMotivo('');
  };

  const corStatus = {
    pendente: 'pendente',
    aprovada: 'pago',
    recusada: 'atrasado',
    cancelada: 'cancelada',
  };

  const filtros = [
    { key: 'pendente', label: '⏳ Pendentes' },
    { key: 'aprovada', label: '✓ Aprovadas' },
    { key: 'recusada', label: '✕ Recusadas' },
    { key: 'todas', label: 'Todas' },
  ];

  const totalPendentes = solicitacoes.filter((s) => s.status === 'pendente').length;

  return (
    <div>
      {/* Cabeçalho */}
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-800 mb-1">📥 Solicitações</h2>
        <p className="text-gray-600 text-sm">
          Aprove ou recuse solicitações de matrícula e cancelamento dos alunos
        </p>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl p-4 mb-4 shadow-sm border border-gray-100">
        <div className="flex flex-wrap gap-2">
          {filtros.map((f) => (
            <button
              key={f.key}
              onClick={() => setFiltro(f.key)}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition ${
                filtro === f.key
                  ? 'bg-teal-700 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f.label}
              {f.key === 'pendente' && totalPendentes > 0 && (
                <span className="ml-2 bg-white/30 px-2 py-0.5 rounded-full text-xs">
                  {totalPendentes}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Lista de solicitações */}
      {carregando ? (
        <div className="text-center py-12 bg-white rounded-xl">
          <div className="text-4xl mb-2">⏳</div>
          <p className="text-gray-500">Carregando...</p>
        </div>
      ) : solicitacoes.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl shadow-sm">
          <div className="text-6xl mb-4">✨</div>
          <p className="text-gray-700 font-semibold text-lg">
            Nenhuma solicitação encontrada
          </p>
          <p className="text-gray-400 text-sm mt-1">
            {filtro === 'pendente' ? 'Tudo em dia por aqui!' : 'Mude o filtro para ver outras.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {solicitacoes.map((s) => (
            <div
              key={s.id}
              className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition"
            >
              <div className="flex flex-wrap justify-between items-start gap-3 mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">
                      {s.tipo_display}
                    </p>
                    <span className="text-gray-300">•</span>
                    <p className="text-xs text-gray-400">#{s.id}</p>
                  </div>
                  <h3 className="font-bold text-lg text-gray-800">{s.aluno_nome}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    📚 Turma: <strong>{s.turma_nome}</strong>
                  </p>
                  <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-xs text-gray-500">
                    {s.aluno_email && <span>📧 {s.aluno_email}</span>}
                    {s.aluno_telefone && <span>📱 {s.aluno_telefone}</span>}
                  </div>
                </div>
                <Badge status={corStatus[s.status]} texto={s.status_display} />
              </div>

              <div className="text-xs text-gray-500 mb-3">
                Solicitado em {formatarData(s.data_solicitacao?.slice(0, 10))}
                {s.respondido_por_nome && (
                  <> · Respondido por <strong>{s.respondido_por_nome}</strong></>
                )}
              </div>

              {s.observacao_aluno && (
                <div className="bg-blue-50 border-l-4 border-blue-400 p-3 rounded mb-3 text-sm">
                  💬 <em>"{s.observacao_aluno}"</em>
                </div>
              )}

              {s.motivo_recusa && (
                <div className="bg-red-50 border-l-4 border-red-400 p-3 rounded mb-3 text-sm text-red-700">
                  ⚠️ <strong>Motivo da recusa:</strong> {s.motivo_recusa}
                </div>
              )}

              {/* Formulário de recusa */}
              {s.status === 'pendente' && recusando === s.id && (
                <div className="bg-gray-50 p-3 rounded-lg space-y-2 border border-gray-200">
                  <label className="text-sm font-medium text-gray-700 block">
                    Motivo da recusa (opcional):
                  </label>
                  <textarea
                    value={motivo}
                    onChange={(e) => setMotivo(e.target.value)}
                    placeholder="Ex: Turma cheia, idade incompatível..."
                    className="w-full p-2 border border-gray-300 rounded text-sm outline-none focus:ring-2 focus:ring-cyan-500"
                    rows={2}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => recusar(s.id)}
                      className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded text-sm font-semibold transition"
                    >
                      Confirmar recusa
                    </button>
                    <button
                      onClick={cancelarRecusa}
                      className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded text-sm transition"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}

              {/* Botões aprovar/recusar */}
              {s.status === 'pendente' && recusando !== s.id && (
                <div className="flex gap-2 pt-2 border-t border-gray-100">
                  <button
                    onClick={() => aprovar(s.id)}
                    className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-semibold transition"
                  >
                    ✓ Aprovar
                  </button>
                  <button
                    onClick={() => setRecusando(s.id)}
                    className="bg-white border border-red-300 text-red-600 hover:bg-red-50 px-4 py-2 rounded-lg text-sm font-semibold transition"
                  >
                    ✕ Recusar
                  </button>
                </div>
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
    </div>
  );
}

export default AdminSolicitacoes;
