import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../../api/client';
import Modal from '../../components/Modal';
import { formatJson, sanitizeObject } from '../../utils/security';

function Auditoria() {
  const [logs, setLogs] = useState([]);
  const [paginacao, setPaginacao] = useState({ count: 0, next: null, previous: null });
  const [pagina, setPagina] = useState(1);
  const [filtros, setFiltros] = useState({ acao: '', entidade: '', usuario: '', inicio: '', fim: '' });
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [selecionado, setSelecionado] = useState(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro('');
    try {
      const params = new URLSearchParams({ page: String(pagina) });
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) params.set(key, value);
      });
      const { data } = await api.get(`/admin/auditoria/?${params.toString()}`);
      setLogs(data.results || data || []);
      setPaginacao(Array.isArray(data) ? { count: data.length, next: null, previous: null } : {
        count: data.count || 0,
        next: data.next,
        previous: data.previous,
      });
    } catch (err) {
      const status = err.response?.status;
      if (status === 403) setErro('Seu perfil nao tem permissao para consultar auditoria.');
      else if (status === 401) setErro('Sua sessao expirou. Entre novamente.');
      else setErro('Nao foi possivel carregar os logs de auditoria.');
    } finally {
      setCarregando(false);
    }
  }, [filtros, pagina]);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const limparFiltros = () => {
    setPagina(1);
    setFiltros({ acao: '', entidade: '', usuario: '', inicio: '', fim: '' });
  };

  const resumo = useMemo(() => {
    const acoes = new Set(logs.map((log) => log.acao));
    const entidades = new Set(logs.map((log) => log.entidade_tipo));
    return { acoes: acoes.size, entidades: entidades.size };
  }, [logs]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">Seguranca</p>
          <h2 className="text-3xl font-bold text-gray-900">Auditoria</h2>
          <p className="text-sm text-gray-600">Consulte alteracoes criticas da sua arena com isolamento por tenant.</p>
        </div>
        <button type="button" onClick={carregar} className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50">
          Atualizar
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Resumo titulo="Eventos encontrados" valor={paginacao.count} />
        <Resumo titulo="Acoes nesta pagina" valor={resumo.acoes} />
        <Resumo titulo="Entidades nesta pagina" valor={resumo.entidades} />
      </div>

      <section className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
          <Input label="Acao" value={filtros.acao} onChange={(value) => setFiltrosAtualizando(setFiltros, setPagina, 'acao', value)} />
          <Input label="Entidade" value={filtros.entidade} onChange={(value) => setFiltrosAtualizando(setFiltros, setPagina, 'entidade', value)} />
          <Input label="Usuario ID" value={filtros.usuario} onChange={(value) => setFiltrosAtualizando(setFiltros, setPagina, 'usuario', value)} />
          <Input label="Inicio" type="date" value={filtros.inicio} onChange={(value) => setFiltrosAtualizando(setFiltros, setPagina, 'inicio', value)} />
          <Input label="Fim" type="date" value={filtros.fim} onChange={(value) => setFiltrosAtualizando(setFiltros, setPagina, 'fim', value)} />
        </div>
        <div className="mt-3 flex justify-end">
          <button type="button" onClick={limparFiltros} className="rounded-lg bg-gray-100 px-3 py-1.5 text-sm font-semibold text-gray-700 hover:bg-gray-200">
            Limpar filtros
          </button>
        </div>
      </section>

      {erro && <div className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm font-semibold text-red-700">{erro}</div>}

      {carregando ? (
        <Estado titulo="Carregando auditoria..." />
      ) : logs.length === 0 ? (
        <Estado titulo="Nenhum evento encontrado" detalhe="Ajuste os filtros ou aguarde novas acoes criticas." />
      ) : (
        <section className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm">
          <table className="w-full">
            <thead className="border-b border-gray-200 bg-gray-50">
              <tr>
                <Th>Data</Th>
                <Th>Acao</Th>
                <Th className="hidden md:table-cell">Usuario</Th>
                <Th>Arena / Entidade</Th>
                <Th className="hidden lg:table-cell">Resumo</Th>
                <Th className="text-right">Detalhes</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="p-3 text-sm text-gray-600">{formatDateTime(log.criado_em)}</td>
                  <td className="p-3">
                    <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-bold text-gray-700">{log.acao}</span>
                  </td>
                  <td className="hidden p-3 text-sm text-gray-600 md:table-cell">{log.usuario_nome || '-'}</td>
                  <td className="p-3 text-sm text-gray-700">
                    <p className="font-bold text-teal-700">{log.arena_nome || `Arena #${log.arena}`}</p>
                    <p className="font-semibold">{log.entidade_tipo}</p>
                    <p className="text-xs text-gray-400">#{log.entidade_id || '-'}</p>
                  </td>
                  <td className="hidden p-3 text-xs text-gray-500 lg:table-cell">{summarizeLog(log)}</td>
                  <td className="p-3 text-right">
                    <button type="button" onClick={() => setSelecionado(log)} className="rounded-lg bg-teal-700 px-3 py-1.5 text-sm font-bold text-white hover:bg-teal-800">
                      Ver
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 bg-gray-50 px-4 py-3">
            <p className="text-sm text-gray-500">Pagina {pagina} · {logs.length} de {paginacao.count}</p>
            <div className="flex gap-2">
              <button type="button" disabled={!paginacao.previous} onClick={() => setPagina((value) => Math.max(1, value - 1))} className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-40">
                Anterior
              </button>
              <button type="button" disabled={!paginacao.next} onClick={() => setPagina((value) => value + 1)} className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-40">
                Proxima
              </button>
            </div>
          </div>
        </section>
      )}

      <Modal aberto={Boolean(selecionado)} onFechar={() => setSelecionado(null)} titulo="Detalhes da auditoria" tamanho="xl">
        {selecionado && <AuditDetails log={selecionado} />}
      </Modal>
    </div>
  );
}

function setFiltrosAtualizando(setFiltros, setPagina, key, value) {
  setPagina(1);
  setFiltros((current) => ({ ...current, [key]: value }));
}

function AuditDetails({ log }) {
  const before = sanitizeObject(log.valores_anteriores || {});
  const after = sanitizeObject(log.valores_novos || {});
  const diff = buildDiff(before, after);

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <Detail label="Acao" value={log.acao} />
        <Detail label="Arena" value={log.arena_nome || `#${log.arena}`} />
        <Detail label="IP" value={log.ip || '-'} />
      </div>
      {log.acao.startsWith('superadmin.') && <div className="grid grid-cols-1 gap-3 md:grid-cols-3"><Detail label="Rota" value={log.metadados?.frontend_route || log.metadados?.path || '-'} /><Detail label="Status HTTP" value={log.metadados?.status_code || '-'} /><Detail label="Motivo" value={log.metadados?.motivo || 'Nao informado'} /></div>}

      <div>
        <h3 className="mb-2 font-bold text-gray-900">Campos alterados</h3>
        {diff.length === 0 ? (
          <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">Evento sem diferenca estruturada registrada.</p>
        ) : (
          <div className="space-y-2">
            {diff.map((item) => (
              <div key={item.key} className={`rounded-lg border p-3 text-sm ${item.type === 'added' ? 'border-green-100 bg-green-50' : item.type === 'removed' ? 'border-red-100 bg-red-50' : 'border-cyan-100 bg-cyan-50'}`}>
                <p className="font-bold text-gray-800">{item.key}</p>
                <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
                  <CodeBlock label="Antes" value={item.before} />
                  <CodeBlock label="Depois" value={item.after} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <CodePanel title="Valores anteriores" value={before} />
        <CodePanel title="Valores posteriores" value={after} />
      </div>
      <CodePanel title="Metadados" value={log.metadados || {}} />
    </div>
  );
}

function buildDiff(before, after, prefix = '') {
  const keys = new Set([...Object.keys(before || {}), ...Object.keys(after || {})]);
  return Array.from(keys).flatMap((key) => {
    const path = prefix ? `${prefix}.${key}` : key;
    const beforeValue = before?.[key];
    const afterValue = after?.[key];
    if (isPlainObject(beforeValue) && isPlainObject(afterValue)) return buildDiff(beforeValue, afterValue, path);
    if (JSON.stringify(beforeValue) === JSON.stringify(afterValue)) return [];
    const type = beforeValue === undefined ? 'added' : afterValue === undefined ? 'removed' : 'changed';
    return [{ key: path, before: beforeValue, after: afterValue, type }];
  });
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function summarizeLog(log) {
  if (log.acao.startsWith('superadmin.')) {
    const metadata = log.metadados || {};
    return `${metadata.method || ''} ${metadata.frontend_route || metadata.path || ''} · HTTP ${metadata.status_code || '-'}`.trim();
  }
  const afterKeys = Object.keys(log.valores_novos || {});
  const beforeKeys = Object.keys(log.valores_anteriores || {});
  const total = new Set([...afterKeys, ...beforeKeys]).size;
  return total ? `${total} campo(s) registrado(s)` : 'Sem estado detalhado';
}

function formatDateTime(value) {
  if (!value) return '-';
  return new Date(value).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

function Resumo({ titulo, valor }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase text-gray-500">{titulo}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{valor}</p>
    </div>
  );
}

function Input({ label, value, onChange, type = 'text' }) {
  return (
    <label className="text-xs font-semibold uppercase text-gray-500">
      {label}
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-normal normal-case text-gray-800 outline-none focus:ring-2 focus:ring-cyan-500" />
    </label>
  );
}

function Th({ children, className = '' }) {
  return <th className={`p-3 text-left text-xs font-bold uppercase text-gray-600 ${className}`}>{children}</th>;
}

function Estado({ titulo, detalhe }) {
  return (
    <div className="rounded-xl bg-white py-14 text-center shadow-sm">
      <p className="text-lg font-semibold text-gray-700">{titulo}</p>
      {detalhe && <p className="mt-1 text-sm text-gray-400">{detalhe}</p>}
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div className="rounded-lg bg-gray-50 p-3">
      <p className="text-xs font-semibold uppercase text-gray-500">{label}</p>
      <p className="mt-1 break-words text-sm font-bold text-gray-900">{value}</p>
    </div>
  );
}

function CodeBlock({ label, value }) {
  return (
    <div>
      <p className="mb-1 text-xs font-bold uppercase text-gray-500">{label}</p>
      <pre className="max-h-36 overflow-auto rounded bg-white p-2 text-xs text-gray-700">{formatJson(value)}</pre>
    </div>
  );
}

function CodePanel({ title, value }) {
  return (
    <div>
      <h3 className="mb-2 font-bold text-gray-900">{title}</h3>
      <pre className="max-h-80 overflow-auto rounded-lg bg-gray-950 p-4 text-xs text-gray-100">{formatJson(value)}</pre>
    </div>
  );
}

export default Auditoria;
