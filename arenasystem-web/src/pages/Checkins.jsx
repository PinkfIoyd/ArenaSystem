import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';
import { checkinUi } from '../utils/checkinUi';

export default function Checkins() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/checkins/me/');
      setItems(Array.isArray(data) ? data : data.results || []);
      setError('');
    } catch { setError('Não foi possível carregar seu histórico.'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const initial = setTimeout(load, 0); return () => clearTimeout(initial); }, [load]);

  return <Layout><div className="mx-auto max-w-3xl"><p className="page-kicker">Presenças</p><h1 className="page-title">Meus check-ins</h1><p className="page-subtitle">Acompanhe solicitações e validações da arena.</p>
    <div className="mt-6 space-y-3">
      {loading && <Empty text="Carregando histórico..." />}
      {error && <Empty text={error} />}
      {!loading && !error && items.length === 0 && <Empty text="Você ainda não possui check-ins." />}
      {items.map((item) => <article key={item.id} className="app-surface flex items-center justify-between gap-4 p-4"><div><h2 className="font-bold text-slate-950">{item.turma_nome}</h2><p className="mt-1 text-sm text-slate-500">{new Date(`${item.data}T12:00:00`).toLocaleDateString('pt-BR')} • {String(item.horario_previsto || item.horario).slice(0, 5)}</p>{item.motivo && <p className="mt-2 text-sm text-slate-600">{item.motivo}</p>}</div><span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700">{checkinUi(item.status).label}</span></article>)}
    </div>
  </div></Layout>;
}

function Empty({ text }) { return <div className="app-surface p-8 text-center text-sm text-slate-500">{text}</div>; }
