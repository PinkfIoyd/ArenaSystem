import { useCallback, useEffect, useState } from 'react';
import api from '../../api/client';
import Modal from '../../components/Modal';
import Toast from '../../components/Toast';
import { formatarData } from '../../utils/format';
import useTerminology from '../../hooks/useTerminology';

function TurmasQuadras() {
  const { terms } = useTerminology();
  const [turmas, setTurmas] = useState([]);
  const [quadras, setQuadras] = useState([]);
  const [manutencoes, setManutencoes] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [modalQuadra, setModalQuadra] = useState(null);
  const [toast, setToast] = useState(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const [respTurmas, respQuadras, respManutencoes] = await Promise.all([
        api.get('/admin/turmas/'),
        api.get('/admin/quadras/'),
        api.get('/admin/manutencoes/'),
      ]);
      setTurmas(Array.isArray(respTurmas.data) ? respTurmas.data : respTurmas.data.results || []);
      setQuadras(Array.isArray(respQuadras.data) ? respQuadras.data : respQuadras.data.results || []);
      setManutencoes(Array.isArray(respManutencoes.data) ? respManutencoes.data : respManutencoes.data.results || []);
    } catch {
      setToast({ mensagem: `Erro ao carregar turmas e ${terms.espaco_plural}`, tipo: 'erro' });
    } finally {
      setCarregando(false);
    }
  }, [terms.espaco_plural]);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const concluir = async (manutencao) => {
    try {
      const { data } = await api.post(`/admin/manutencoes/${manutencao.id}/concluir/`);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
      await carregar();
    } catch (err) {
      setToast({ mensagem: err.response?.data?.detail || 'Erro ao concluir manutencao', tipo: 'erro' });
    }
  };

  const abertasPorQuadra = (quadraId) =>
    manutencoes.filter((m) => m.quadra === quadraId && !['concluida', 'cancelada'].includes(m.status));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="mb-1 text-3xl font-bold text-gray-900">Turmas & {capitalize(terms.espaco_plural)}</h2>
          <p className="text-sm text-gray-600">Acompanhe ocupação, capacidade e manutenções dos {terms.espaco_plural}.</p>
        </div>
        <button type="button" onClick={carregar} className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50">
          Atualizar
        </button>
      </div>

      {carregando ? (
        <div className="rounded-xl bg-white py-14 text-center text-gray-500 shadow-sm">Carregando...</div>
      ) : (
        <>
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-800">{capitalize(terms.espaco_plural)}</h3>
              <span className="text-sm text-gray-500">{quadras.length} {terms.espaco_plural}</span>
            </div>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {quadras.map((quadra) => {
                const abertas = abertasPorQuadra(quadra.id);
                return (
                  <div key={quadra.id} className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="text-xl font-bold text-gray-900">{quadra.nome}</h4>
                        <p className="text-sm text-gray-500">{quadra.tipo_areia || 'Sem tipo informado'}</p>
                      </div>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${quadra.ativa ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'}`}>
                        {quadra.ativa ? 'Ativa' : 'Inativa'}
                      </span>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <Info label="Ultima manutencao" value={formatarData(quadra.ultima_manutencao)} />
                      <Info label="Proxima manutencao" value={formatarData(quadra.proxima_manutencao)} />
                    </div>

                    {abertas.length > 0 && (
                      <div className="mt-4 space-y-2 rounded-lg bg-cyan-50 p-3">
                        {abertas.map((manutencao) => (
                          <div key={manutencao.id} className="flex items-center justify-between gap-2 text-sm">
                            <span className="text-cyan-900">
                              {manutencao.tipo_display} em {formatarData(manutencao.data_agendada)}
                            </span>
                            <button type="button" onClick={() => concluir(manutencao)} className="rounded bg-white px-2 py-1 text-xs font-bold text-cyan-800 shadow-sm hover:bg-cyan-100">
                              Concluir
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="mt-4 flex justify-end">
                      <button type="button" onClick={() => setModalQuadra(quadra)} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800">
                        Agendar manutencao
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-800">Turmas</h3>
              <span className="text-sm text-gray-500">{turmas.length} turma(s)</span>
            </div>
            <div className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm">
              <table className="w-full">
                <thead className="border-b border-gray-200 bg-gray-50">
                  <tr>
                    <Th>Turma</Th>
                    <Th>Quadra</Th>
                    <Th className="hidden md:table-cell">Horario</Th>
                    <Th className="text-center">{capitalize(terms.pessoa_plural)}</Th>
                    <Th>Status</Th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {turmas.map((turma) => (
                    <tr key={turma.id} className="hover:bg-gray-50">
                      <td className="p-3">
                        <p className="font-semibold text-gray-800">{turma.nome}</p>
                        <p className="text-xs text-gray-500">Prof. {turma.professor_nome}</p>
                      </td>
                      <td className="p-3 text-sm text-gray-600">{turma.quadra_nome}</td>
                      <td className="hidden p-3 text-sm text-gray-600 md:table-cell">
                        {turma.dias_semana} - {turma.horario?.slice(0, 5)}
                      </td>
                      <td className="p-3 text-center text-sm font-bold text-gray-800">
                        {turma.total_alunos}/{turma.vagas}
                      </td>
                      <td className="p-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${turma.ativa ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'}`}>
                          {turma.ativa ? 'Ativa' : 'Inativa'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {modalQuadra && (
        <ModalManutencao
          quadra={modalQuadra}
          onFechar={() => setModalQuadra(null)}
          onSalvar={async () => {
            setModalQuadra(null);
            await carregar();
          }}
          setToast={setToast}
        />
      )}

      {toast && <Toast mensagem={toast.mensagem} tipo={toast.tipo} onClose={() => setToast(null)} />}
    </div>
  );
}

function ModalManutencao({ quadra, onFechar, onSalvar, setToast }) {
  const [dados, setDados] = useState({
    quadra: quadra.id,
    tipo: 'preventiva',
    descricao: '',
    data_agendada: '',
    responsavel: '',
    custo: '',
  });
  const [salvando, setSalvando] = useState(false);

  const salvar = async () => {
    if (!dados.data_agendada || !dados.descricao) {
      setToast({ mensagem: 'Informe data e descricao', tipo: 'erro' });
      return;
    }
    setSalvando(true);
    try {
      await api.post('/admin/manutencoes/', dados);
      setToast({ mensagem: 'Manutencao agendada', tipo: 'sucesso' });
      await onSalvar();
    } catch (err) {
      setToast({ mensagem: err.response?.data?.detail || 'Erro ao agendar manutencao', tipo: 'erro' });
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Modal aberto onFechar={onFechar} titulo={`Manutencao - ${quadra.nome}`} tamanho="md">
      <div className="space-y-3">
        <label className="block">
          <span className="text-xs font-semibold text-gray-700">Tipo</span>
          <select value={dados.tipo} onChange={(e) => setDados({ ...dados, tipo: e.target.value })} className="mt-1 w-full rounded border border-gray-300 p-2">
            <option value="preventiva">Preventiva</option>
            <option value="corretiva">Corretiva</option>
          </select>
        </label>
        <Campo label="Data agendada" type="date" value={dados.data_agendada} onChange={(valor) => setDados({ ...dados, data_agendada: valor })} />
        <Campo label="Responsavel" value={dados.responsavel} onChange={(valor) => setDados({ ...dados, responsavel: valor })} />
        <Campo label="Custo previsto" type="number" value={dados.custo} onChange={(valor) => setDados({ ...dados, custo: valor })} />
        <label className="block">
          <span className="text-xs font-semibold text-gray-700">Descricao</span>
          <textarea value={dados.descricao} onChange={(e) => setDados({ ...dados, descricao: e.target.value })} className="mt-1 min-h-24 w-full rounded border border-gray-300 p-2" />
        </label>
        <div className="flex justify-end gap-2 border-t border-gray-200 pt-3">
          <button type="button" onClick={onFechar} className="rounded bg-gray-200 px-4 py-2 font-medium text-gray-700 hover:bg-gray-300">Cancelar</button>
          <button type="button" onClick={salvar} disabled={salvando} className="rounded bg-teal-700 px-4 py-2 font-semibold text-white hover:bg-teal-800 disabled:opacity-50">
            {salvando ? 'Salvando...' : 'Agendar'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

function Campo({ label, value, onChange, type = 'text' }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold text-gray-700">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded border border-gray-300 p-2" />
    </label>
  );
}

function Info({ label, value }) {
  return (
    <div className="rounded-lg bg-gray-50 p-3">
      <p className="text-xs font-semibold uppercase text-gray-500">{label}</p>
      <p className="mt-1 font-semibold text-gray-800">{value}</p>
    </div>
  );
}

function Th({ children, className = '' }) {
  return <th className={`p-3 text-left text-xs font-bold uppercase text-gray-600 ${className}`}>{children}</th>;
}

export default TurmasQuadras;

function capitalize(value) { return value ? value.charAt(0).toUpperCase() + value.slice(1) : value; }
