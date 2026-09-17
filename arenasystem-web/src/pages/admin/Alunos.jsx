import { useCallback, useEffect, useState } from 'react';
import api from '../../api/client';
import Modal from '../../components/Modal';
import Toast from '../../components/Toast';
import useDebounce from '../../hooks/useDebounce';
import { formatarData } from '../../utils/format';
import useTerminology from '../../hooks/useTerminology';

const alunoVazio = {
  first_name: '',
  last_name: '',
  email: '',
  telefone: '',
  cpf: '',
  data_nascimento: '',
  username: '',
};

function Alunos() {
  const { terms } = useTerminology();
  const [alunos, setAlunos] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [busca, setBusca] = useState('');
  const [statusFiltro, setStatusFiltro] = useState('ativos');
  const [toast, setToast] = useState(null);
  const [alunoSelecionado, setAlunoSelecionado] = useState(null);
  const [modalNovoAluno, setModalNovoAluno] = useState(false);

  const buscaDebounce = useDebounce(busca, 400);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const params = new URLSearchParams({ status: statusFiltro });
      if (buscaDebounce) params.set('search', buscaDebounce);

      const { data } = await api.get(`/admin/alunos/?${params.toString()}`);
      setAlunos(Array.isArray(data) ? data : data.results || []);
    } catch {
      setToast({ mensagem: `Erro ao carregar ${terms.pessoa_plural}`, tipo: 'erro' });
    } finally {
      setCarregando(false);
    }
  }, [buscaDebounce, statusFiltro, terms.pessoa_plural]);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const desativar = async (aluno) => {
    if (!confirm(`Desativar o ${terms.pessoa_singular} "${aluno.nome_completo}"?`)) return;

    try {
      const { data } = await api.delete(`/admin/alunos/${aluno.id}/`);
      setToast({ mensagem: data.detail, tipo: 'info' });
      await carregar();
    } catch (err) {
      setToast({ mensagem: err.response?.data?.detail || `Erro ao desativar ${terms.pessoa_singular}`, tipo: 'erro' });
    }
  };

  const ativar = async (aluno) => {
    try {
      const { data } = await api.post(`/admin/alunos/${aluno.id}/ativar/`);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
      await carregar();
    } catch (err) {
      setToast({ mensagem: err.response?.data?.detail || `Erro ao ativar ${terms.pessoa_singular}`, tipo: 'erro' });
    }
  };

  const filtros = [
    { key: 'ativos', label: 'Ativos' },
    { key: 'inativos', label: 'Inativos' },
    { key: 'todos', label: 'Todos' },
  ];

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="mb-1 text-3xl font-bold text-gray-800">{capitalize(terms.pessoa_plural)}</h2>
          <p className="text-sm text-gray-600">Gerencie os cadastros dos {terms.pessoa_plural} da {terms.unidade_singular}.</p>
        </div>
        <button
          type="button"
          onClick={() => setModalNovoAluno(true)}
          className="rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-teal-800"
        >
          Novo {terms.pessoa_singular}
        </button>
      </div>

      <div className="mb-4 space-y-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <input
          type="text"
          value={busca}
          onChange={(event) => setBusca(event.target.value)}
          placeholder="Buscar por nome, email, CPF ou telefone..."
          className="w-full rounded-lg border border-gray-300 px-3 py-2 outline-none focus:ring-2 focus:ring-cyan-500"
        />

        <div className="flex flex-wrap gap-2">
          {filtros.map((filtro) => (
            <button
              key={filtro.key}
              type="button"
              onClick={() => setStatusFiltro(filtro.key)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                statusFiltro === filtro.key
                  ? 'bg-teal-700 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {filtro.label}
            </button>
          ))}
        </div>
      </div>

      {carregando ? (
        <EstadoLista titulo="Carregando..." />
      ) : alunos.length === 0 ? (
        <EstadoLista
          titulo={`Nenhum ${terms.pessoa_singular} encontrado`}
          detalhe={busca ? `Sem resultados para "${busca}"` : `Cadastre o primeiro ${terms.pessoa_singular}.`}
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm">
          <table className="w-full">
            <thead className="border-b border-gray-200 bg-gray-50">
              <tr>
                <Th>Nome</Th>
                <Th className="hidden md:table-cell">Contato</Th>
                <Th className="hidden text-center lg:table-cell">Turmas</Th>
                <Th className="hidden text-center lg:table-cell">Pendencias</Th>
                <Th>Status</Th>
                <Th className="text-right">Acoes</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {alunos.map((aluno) => (
                <tr key={aluno.id} className="transition hover:bg-gray-50">
                  <td className="p-3">
                    <p className="font-semibold text-gray-800">{aluno.nome_completo}</p>
                    <p className="text-xs text-gray-500">@{aluno.username}</p>
                  </td>
                  <td className="hidden p-3 md:table-cell">
                    {aluno.email && <p className="text-xs text-gray-600">{aluno.email}</p>}
                    {aluno.telefone && <p className="text-xs text-gray-600">{aluno.telefone}</p>}
                  </td>
                  <td className="hidden p-3 text-center lg:table-cell">
                    <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                      {aluno.total_turmas}
                    </span>
                  </td>
                  <td className="hidden p-3 text-center lg:table-cell">
                    {aluno.mensalidades_em_aberto > 0 ? (
                      <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700">
                        {aluno.mensalidades_em_aberto}
                      </span>
                    ) : (
                      <span className="text-gray-300">-</span>
                    )}
                  </td>
                  <td className="p-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      aluno.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
                    }`}>
                      {aluno.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => setAlunoSelecionado(aluno)}
                        className="rounded bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700 transition hover:bg-gray-200"
                      >
                        Ver
                      </button>
                      {aluno.is_active ? (
                        <button
                          type="button"
                          onClick={() => desativar(aluno)}
                          className="rounded border border-red-300 px-3 py-1 text-xs font-semibold text-red-600 transition hover:bg-red-50"
                        >
                          Desativar
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => ativar(aluno)}
                          className="rounded bg-green-500 px-3 py-1 text-xs font-semibold text-white transition hover:bg-green-600"
                        >
                          Ativar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {alunoSelecionado && (
        <ModalAluno
          aluno={alunoSelecionado}
          onFechar={() => setAlunoSelecionado(null)}
          onSalvar={() => {
            setAlunoSelecionado(null);
            carregar();
          }}
          setToast={setToast}
        />
      )}

      {modalNovoAluno && (
        <ModalNovoAluno
          onFechar={() => setModalNovoAluno(false)}
          onSalvar={() => {
            setModalNovoAluno(false);
            carregar();
          }}
          setToast={setToast}
        />
      )}

      {toast && <Toast mensagem={toast.mensagem} tipo={toast.tipo} onClose={() => setToast(null)} />}
    </div>
  );
}

function Th({ children, className = '' }) {
  return (
    <th className={`p-3 text-left text-xs font-bold uppercase text-gray-600 ${className}`}>
      {children}
    </th>
  );
}

function EstadoLista({ titulo, detalhe }) {
  return (
    <div className="rounded-xl bg-white py-14 text-center shadow-sm">
      <p className="text-lg font-semibold text-gray-700">{titulo}</p>
      {detalhe && <p className="mt-1 text-sm text-gray-400">{detalhe}</p>}
    </div>
  );
}

function ModalAluno({ aluno, onFechar, onSalvar, setToast }) {
  const [dados, setDados] = useState({
    first_name: aluno.first_name || '',
    last_name: aluno.last_name || '',
    email: aluno.email || '',
    telefone: aluno.telefone || '',
    cpf: aluno.cpf || '',
    data_nascimento: aluno.data_nascimento || '',
  });
  const [salvando, setSalvando] = useState(false);

  const salvar = async () => {
    setSalvando(true);
    try {
      await api.patch(`/admin/alunos/${aluno.id}/`, dados);
      setToast({ mensagem: 'Aluno atualizado', tipo: 'sucesso' });
      onSalvar();
    } catch (err) {
      const erros = err.response?.data;
      setToast({ mensagem: erros?.detail || erros?.email?.[0] || 'Erro ao salvar aluno', tipo: 'erro' });
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Modal aberto onFechar={onFechar} titulo={aluno.nome_completo} tamanho="lg">
      <div className="space-y-4">
        <div className="space-y-1 rounded-lg bg-gray-50 p-3 text-xs text-gray-600">
          <p><strong>Username:</strong> @{aluno.username}</p>
          <p><strong>Cadastrado em:</strong> {formatarData(aluno.date_joined?.slice(0, 10))}</p>
          <p><strong>Turmas:</strong> {aluno.total_turmas}</p>
          <p><strong>Mensalidades em aberto:</strong> {aluno.mensalidades_em_aberto}</p>
        </div>

        <FormularioAluno dados={dados} setDados={setDados} />

        <div className="flex justify-end gap-2 border-t border-gray-200 pt-3">
          <button type="button" onClick={onFechar} className="rounded bg-gray-200 px-4 py-2 font-medium text-gray-700 transition hover:bg-gray-300">
            Cancelar
          </button>
          <button type="button" onClick={salvar} disabled={salvando} className="rounded bg-teal-700 px-4 py-2 font-semibold text-white transition hover:bg-teal-800 disabled:opacity-50">
            {salvando ? 'Salvando...' : 'Salvar alteracoes'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

function ModalNovoAluno({ onFechar, onSalvar, setToast }) {
  const [dados, setDados] = useState(alunoVazio);
  const [salvando, setSalvando] = useState(false);
  const [senhaTemporaria, setSenhaTemporaria] = useState(null);

  const salvar = async () => {
    if (!dados.first_name || !dados.email) {
      setToast({ mensagem: 'Nome e email sao obrigatorios', tipo: 'erro' });
      return;
    }

    setSalvando(true);
    try {
      const { data } = await api.post('/admin/alunos/', dados);
      setSenhaTemporaria(data.senha_temporaria || null);
      setToast({ mensagem: 'Aluno cadastrado', tipo: 'sucesso' });
    } catch (err) {
      const erros = err.response?.data;
      setToast({ mensagem: erros?.detail || erros?.email?.[0] || erros?.username?.[0] || 'Erro ao cadastrar aluno', tipo: 'erro' });
    } finally {
      setSalvando(false);
    }
  };

  if (senhaTemporaria) {
    return (
      <Modal aberto onFechar={onSalvar} titulo="Aluno cadastrado" tamanho="md">
        <div className="space-y-4 text-center">
          <p className="text-gray-700">Guarde a senha temporaria abaixo para passar ao aluno.</p>
          <div className="rounded-lg border-2 border-cyan-300 bg-cyan-50 p-4">
            <p className="mb-1 text-xs text-gray-600">Senha temporaria</p>
            <p className="select-all font-mono text-2xl font-bold text-gray-800">{senhaTemporaria}</p>
          </div>
          <button type="button" onClick={onSalvar} className="rounded bg-teal-700 px-6 py-2 font-semibold text-white transition hover:bg-teal-800">
            Fechar
          </button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal aberto onFechar={onFechar} titulo="Novo aluno" tamanho="md">
      <div className="space-y-4">
        <FormularioAluno dados={dados} setDados={setDados} incluirUsername />
        <div className="rounded border-l-4 border-blue-400 bg-blue-50 p-3 text-sm text-blue-700">
          Uma senha temporaria sera gerada automaticamente.
        </div>
        <div className="flex justify-end gap-2 border-t border-gray-200 pt-3">
          <button type="button" onClick={onFechar} className="rounded bg-gray-200 px-4 py-2 font-medium text-gray-700 transition hover:bg-gray-300">
            Cancelar
          </button>
          <button type="button" onClick={salvar} disabled={salvando} className="rounded bg-teal-700 px-4 py-2 font-semibold text-white transition hover:bg-teal-800 disabled:opacity-50">
            {salvando ? 'Cadastrando...' : 'Cadastrar aluno'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

function FormularioAluno({ dados, setDados, incluirUsername = false }) {
  const atualizar = (campo, valor) => setDados({ ...dados, [campo]: valor });

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      <Campo label="Nome *" value={dados.first_name} onChange={(valor) => atualizar('first_name', valor)} />
      <Campo label="Sobrenome" value={dados.last_name} onChange={(valor) => atualizar('last_name', valor)} />
      <Campo className="md:col-span-2" label="Email *" type="email" value={dados.email} onChange={(valor) => atualizar('email', valor)} />
      <Campo label="Telefone" value={dados.telefone} onChange={(valor) => atualizar('telefone', valor)} />
      <Campo label="CPF" value={dados.cpf} onChange={(valor) => atualizar('cpf', valor)} />
      <Campo label="Nascimento" type="date" value={dados.data_nascimento || ''} onChange={(valor) => atualizar('data_nascimento', valor)} />
      {incluirUsername && (
        <Campo className="md:col-span-2" label="Username opcional" value={dados.username} onChange={(valor) => atualizar('username', valor)} />
      )}
    </div>
  );
}

function Campo({ label, value, onChange, type = 'text', className = '' }) {
  return (
    <label className={`block ${className}`}>
      <span className="text-xs font-semibold text-gray-700">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded border border-gray-300 p-2 outline-none focus:ring-2 focus:ring-cyan-500"
      />
    </label>
  );
}

export default Alunos;

function capitalize(value) { return value ? value.charAt(0).toUpperCase() + value.slice(1) : value; }
