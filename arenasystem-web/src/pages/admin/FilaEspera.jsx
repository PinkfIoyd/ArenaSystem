import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../../api/client';
import Toast from '../../components/Toast';
import Icon from '../../components/Icon';
import { formatarData } from '../../utils/format';

function FilaEspera() {
  const [searchParams] = useSearchParams();
  const [fila, setFila] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [turmaFiltro, setTurmaFiltro] = useState(() => searchParams.get('turma') || '');
  const [toast, setToast] = useState(null);
  const [processando, setProcessando] = useState(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const url = turmaFiltro
        ? `/admin/fila-espera/?turma=${turmaFiltro}`
        : '/admin/fila-espera/';
      const { data } = await api.get(url);
      setFila(Array.isArray(data) ? data : data.results || []);
    } catch {
      setToast({ mensagem: 'Erro ao carregar fila', tipo: 'erro' });
    } finally {
      setCarregando(false);
    }
  }, [turmaFiltro]);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const chamar = async (item) => {
    if (!confirm(`Chamar ${item.aluno_nome} para entrar em "${item.turma_nome}"?`)) return;
    setProcessando(item.id);
    try {
      const { data } = await api.post(`/admin/fila-espera/${item.id}/chamar/`);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
      await carregar();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao chamar';
      setToast({ mensagem: msg, tipo: 'erro' });
    } finally {
      setProcessando(null);
    }
  };

  const remover = async (item) => {
    if (!confirm(`Remover ${item.aluno_nome} da fila de "${item.turma_nome}"?`)) return;
    setProcessando(item.id);
    try {
      const { data } = await api.post(`/admin/fila-espera/${item.id}/remover/`);
      setToast({ mensagem: data.detail, tipo: 'info' });
      await carregar();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao remover';
      setToast({ mensagem: msg, tipo: 'erro' });
    } finally {
      setProcessando(null);
    }
  };

  const filaAgrupada = fila.reduce((acc, item) => {
    const chave = item.turma;
    if (!acc[chave]) {
      acc[chave] = {
        turma_id: item.turma,
        turma_nome: item.turma_nome,
        itens: [],
      };
    }
    acc[chave].itens.push(item);
    return acc;
  }, {});

  Object.values(filaAgrupada).forEach((grupo) => {
    grupo.itens.sort((a, b) => a.posicao - b.posicao);
  });

  const turmasUnicas = [...new Set(fila.map((f) => `${f.turma}|${f.turma_nome}`))]
    .map((s) => {
      const [id, nome] = s.split('|');
      return { id, nome };
    });

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="page-kicker">Atendimento</p>
          <h2 className="page-title">Fila de Espera</h2>
          <p className="page-subtitle">Gerencie alunos aguardando vagas nas turmas cheias.</p>
        </div>
        <button onClick={carregar} className="btn-secondary self-start">
          <Icon name="refresh" className="h-4 w-4" />
          Atualizar
        </button>
      </div>

      <div className="app-surface mb-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm font-semibold text-slate-700">
            Filtrar por turma
          </label>
          <select
            value={turmaFiltro}
            onChange={(e) => setTurmaFiltro(e.target.value)}
            className="field-control max-w-sm"
          >
            <option value="">Todas as turmas</option>
            {turmasUnicas.map((t) => (
              <option key={t.id} value={t.id}>{t.nome}</option>
            ))}
          </select>
          <span className="ml-auto rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
            {fila.length} aluno(s)
          </span>
        </div>
      </div>

      {carregando ? (
        <EstadoVazio icon="queue" titulo="Carregando fila..." />
      ) : Object.keys(filaAgrupada).length === 0 ? (
        <EstadoVazio
          icon="check"
          titulo="Nenhum aluno na fila"
          texto="Quando uma turma encher, os interessados aparecerao aqui."
        />
      ) : (
        <div className="space-y-4">
          {Object.values(filaAgrupada).map((grupo) => (
            <section key={grupo.turma_id} className="app-surface overflow-hidden">
              <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-slate-950">{grupo.turma_nome}</h3>
                    <p className="mt-1 text-xs text-slate-500">{grupo.itens.length} aluno(s) aguardando vaga</p>
                  </div>
                  <span className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-bold text-teal-800">
                    Turma #{grupo.turma_id}
                  </span>
                </div>
              </div>

              <div className="divide-y divide-slate-100">
                {grupo.itens.map((item, idx) => (
                  <div
                    key={item.id}
                    className={`flex flex-wrap items-center gap-3 p-4 transition ${
                      idx === 0 ? 'bg-emerald-50/50' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-full text-sm font-bold ${
                      idx === 0 ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-700'
                    }`}>
                      {item.posicao}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-bold text-slate-950">{item.aluno_nome}</p>
                        {idx === 0 && (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-700">
                            Proximo
                          </span>
                        )}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
                        {item.aluno_email && <span>{item.aluno_email}</span>}
                        {item.aluno_telefone && <span>{item.aluno_telefone}</span>}
                        <span>Entrada: {formatarData(item.data_entrada?.slice(0, 10))}</span>
                      </div>
                    </div>

                    <div className="flex shrink-0 gap-2">
                      <button
                        onClick={() => chamar(item)}
                        disabled={processando === item.id}
                        className="btn-success px-3 py-2"
                        title="Chamar este aluno"
                      >
                        Chamar
                      </button>
                      <button
                        onClick={() => remover(item)}
                        disabled={processando === item.id}
                        className="btn-danger-soft px-3 py-2"
                        title="Remover da fila"
                      >
                        Remover
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
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

function EstadoVazio({ icon, titulo, texto }) {
  return (
    <div className="app-surface py-14 text-center">
      <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-lg bg-cyan-50 text-teal-800">
        <Icon name={icon} className="h-6 w-6" />
      </div>
      <p className="font-semibold text-slate-700">{titulo}</p>
      {texto && <p className="mt-1 text-sm text-slate-400">{texto}</p>}
    </div>
  );
}

export default FilaEspera;
