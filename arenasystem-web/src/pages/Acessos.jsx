import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';
import Toast from '../components/Toast';

const LABELS = {
  pending: 'Aguardando validação', confirmed: 'Dentro da unidade', rejected: 'Rejeitado',
  checked_out: 'Encerrado', expired: 'Expirado',
};

export default function Acessos() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/access-visits/me/');
      setItems(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível carregar seus acessos.' });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const initial = setTimeout(load, 0);
    const polling = setInterval(load, 15000);
    return () => { clearTimeout(initial); clearInterval(polling); };
  }, [load]);

  async function checkout(item) {
    setBusy(item.public_id);
    try {
      await api.post(`/access-visits/${item.public_id}/check-out/`);
      setToast({ tipo: 'sucesso', mensagem: 'Saída registrada.' });
      await load();
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível registrar a saída.' });
    } finally { setBusy(''); }
  }

  return <Layout><div className="mx-auto max-w-3xl">
    <p className="page-kicker">Acesso livre</p>
    <h1 className="page-title">Meus acessos</h1>
    <p className="page-subtitle">Acompanhe solicitações, entradas e saídas da unidade.</p>
    <div className="mt-6 space-y-3">
      {loading && <Empty text="Carregando histórico…" />}
      {!loading && items.length === 0 && <Empty text="Você ainda não possui visitas registradas." />}
      {items.map((item) => <article key={item.public_id} className="app-surface flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2"><h2 className="font-bold text-slate-950">{item.plano_nome}</h2><Status status={item.status} /></div>
          <p className="mt-1 text-sm text-slate-500">Solicitado em {formatDate(item.solicitado_em)}</p>
          {item.entrada_em && <p className="mt-1 text-sm text-slate-500">Entrada: {formatDate(item.entrada_em)}{item.saida_em ? ` · Saída: ${formatDate(item.saida_em)}` : ''}</p>}
          {item.motivo && <p className="mt-2 text-sm text-slate-600">{item.motivo}</p>}
        </div>
        {item.status === 'confirmed' && <button type="button" className="btn-secondary" disabled={busy === item.public_id} onClick={() => checkout(item)}>{busy === item.public_id ? 'Registrando…' : 'Fazer check-out'}</button>}
      </article>)}
    </div>
    {toast && <Toast {...toast} onClose={() => setToast(null)} />}
  </div></Layout>;
}

function Status({ status }) {
  const color = status === 'confirmed' ? 'bg-emerald-100 text-emerald-700' : status === 'pending' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600';
  return <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-wide ${color}`}>{LABELS[status] || status}</span>;
}
function Empty({ text }) { return <div className="app-surface p-8 text-center text-sm text-slate-500">{text}</div>; }
function formatDate(value) { return value ? new Date(value).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '—'; }
