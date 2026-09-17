import { useEffect, useState } from 'react';
import api from '../../api/client';

function Privacidade() {
  const [requests, setRequests] = useState([]); const [error, setError] = useState(''); const [busy, setBusy] = useState('');
  async function load() { try { const response = await api.get('/privacy/requests/'); setRequests(response.data.results || response.data); } catch (err) { setError(err.response?.data?.detail || 'Nao foi possivel carregar as solicitacoes.'); } }
  useEffect(() => { const timer = setTimeout(() => { void load(); }, 0); return () => clearTimeout(timer); }, []);
  async function create(kind) { const description = kind === 'export' ? '' : window.prompt('Descreva a solicitacao e os dados envolvidos:'); if (description === null) return; setBusy(kind); try { await api.post('/privacy/requests/', { kind, description }); await load(); } catch (err) { setError(err.response?.data?.detail || 'Nao foi possivel registrar a solicitacao.'); } finally { setBusy(''); } }
  async function download(item) { try { const response = await api.get(`/privacy/requests/${item.id}/download/`, { responseType: 'blob' }); const url = URL.createObjectURL(response.data); const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'arenaflow-export.zip'; anchor.click(); URL.revokeObjectURL(url); } catch { setError('A exportacao ainda nao esta disponivel.'); } }
  return <div className="mx-auto max-w-5xl space-y-6"><header><p className="muted-label">Dados e LGPD</p><h1 className="text-3xl font-bold">Privacidade</h1><p className="mt-2 text-slate-600">A infraestrutura abaixo apoia o atendimento de direitos. A politica de retencao depende de aprovacao juridica.</p></header>{error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{error}</div>}
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[['export', 'Exportar dados'], ['correction', 'Solicitar correcao'], ['deletion', 'Solicitar exclusao'], ['anonymization', 'Solicitar anonimizacao']].map(([kind, label]) => <button key={kind} disabled={busy} onClick={() => create(kind)} className="app-surface p-5 text-left font-bold hover:ring-2 hover:ring-teal-600">{label}</button>)}</section>
    <section className="app-surface overflow-hidden"><div className="border-b p-5"><h2 className="text-xl font-bold">Solicitacoes</h2></div>{requests.length === 0 ? <p className="p-8 text-center text-slate-500">Nenhuma solicitacao registrada.</p> : <div className="divide-y">{requests.map((item) => <div key={item.id} className="flex flex-wrap items-center justify-between gap-4 p-5"><div><strong className="capitalize">{item.kind}</strong><p className="text-sm text-slate-500">{item.status} · {new Date(item.created_at).toLocaleString('pt-BR')}</p></div>{item.kind === 'export' && item.export_ready && <button onClick={() => download(item)} className="btn-secondary">Baixar ZIP privado</button>}</div>)}</div>}</section>
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Os documentos legais permanecem como rascunho marcado “revisao juridica pendente” ate publicacao pelo superadmin.</div>
  </div>;
}
export default Privacidade;

