import { useEffect, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';

export default function Notificacoes() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.get('/notificacoes/').then(({ data }) => setItems(Array.isArray(data) ? data : data.results || [])); }, []);
  async function read(item) {
    if (!item.lida) await api.post(`/notificacoes/${item.id}/marcar-lida/`);
    setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, lida: true } : entry));
  }
  return <Layout><div className="mx-auto max-w-3xl"><p className="page-kicker">Atualizações</p><h1 className="page-title">Notificações</h1><div className="mt-6 space-y-3">{items.length === 0 && <div className="app-surface p-8 text-center text-slate-500">Nenhuma notificação.</div>}{items.map((item) => <button type="button" key={item.id} onClick={() => read(item)} className={`app-surface w-full p-4 text-left ${item.lida ? 'opacity-70' : 'border-teal-200'}`}><div className="flex justify-between gap-3"><strong>{item.titulo}</strong>{!item.lida && <span className="h-2.5 w-2.5 rounded-full bg-teal-600" />}</div><p className="mt-1 text-sm text-slate-600">{item.mensagem}</p><p className="mt-2 text-xs text-slate-400">{new Date(item.criada_em).toLocaleString('pt-BR')}</p></button>)}</div></div></Layout>;
}
