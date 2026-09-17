import { useEffect, useState } from 'react';
import api from '../../api/client';

const money = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value || 0));
const STATUS = { trialing: 'Em teste', active: 'Ativas', past_due: 'Inadimplentes', suspended: 'Suspensas', cancel_at_period_end: 'Cancelando', canceled: 'Canceladas' };

function SaasOperacao() {
  const [data, setData] = useState(null); const [health, setHealth] = useState([]); const [error, setError] = useState('');
  async function load() { try { const [dashboard, healthResponse] = await Promise.all([api.get('/saas/operations/dashboard/'), api.get('/saas/operations/health/')]); setData(dashboard.data); setHealth(healthResponse.data); } catch (err) { setError(err.response?.data?.detail || 'Nao foi possivel carregar a operacao SaaS.'); } }
  useEffect(() => { const timer = setTimeout(() => { void load(); }, 0); return () => clearTimeout(timer); }, []);
  if (!data) return <div className="app-surface p-10 text-center">{error || 'Calculando indicadores...'}</div>;
  return <div className="mx-auto max-w-7xl space-y-6"><header><p className="muted-label">Visao executiva</p><h1 className="text-3xl font-bold">Operacao SaaS</h1><p className="mt-2 text-slate-600">Indicadores do mes corrente e saude das contas.</p></header>
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Card label="MRR" value={money(data.mrr)} /><Card label="Receita recebida" value={money(data.revenue_received)} /><Card label="Churn" value={data.churn_percent === null ? 'Sem historico' : `${data.churn_percent}%`} /><Card label="Novas arenas" value={data.new_arenas} /></section>
    <section className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6">{Object.entries(data.statuses).map(([key, value]) => <Card key={key} label={STATUS[key] || key} value={value} compact />)}</section>
    <section className="grid gap-4 lg:grid-cols-2"><div className="app-surface p-6"><h2 className="text-xl font-bold">Atencao operacional</h2><dl className="mt-5 grid grid-cols-2 gap-4"><Metric label="Trials terminando em 7 dias" value={data.trials_ending_7d} /><Metric label="Falhas de pagamento" value={data.payment_failures} /><Metric label="Falhas de webhook" value={data.webhook_failures} /><Metric label="Tickets abertos" value={data.open_tickets} /></dl></div><div className="app-surface p-6"><h2 className="text-xl font-bold">Distribuicao por plano</h2><div className="mt-5 space-y-3">{data.plan_distribution.map((item) => <div key={item.plan__code} className="flex justify-between rounded-lg bg-slate-50 p-3"><span>{item.plan__name}</span><strong>{item.total}</strong></div>)}</div></div></section>
    <section className="app-surface overflow-hidden"><div className="border-b p-6"><h2 className="text-xl font-bold">Saude das arenas</h2></div><div className="divide-y">{health.map((item) => <div key={item.arena.id} className="grid items-center gap-4 p-5 sm:grid-cols-[1fr_auto_2fr]"><strong>{item.arena.nome}</strong><span className={`rounded-full px-3 py-1 text-sm font-bold ${item.score >= 80 ? 'bg-emerald-100 text-emerald-800' : item.score >= 50 ? 'bg-amber-100 text-amber-900' : 'bg-red-100 text-red-800'}`}>{item.score}/100</span><p className="text-sm text-slate-500">Assinatura: {item.components.subscription.status} · Uso maximo: {item.components.usage.max_percentage}% · Tickets urgentes: {item.components.urgent_tickets.count}</p></div>)}</div></section>
  </div>;
}
function Card({ label, value, compact }) { return <div className={`app-surface ${compact ? 'p-4' : 'p-6'}`}><p className="text-sm text-slate-500">{label}</p><p className={`${compact ? 'text-2xl' : 'text-3xl'} mt-2 font-black text-slate-950`}>{value}</p></div>; }
function Metric({ label, value }) { return <div><dt className="text-sm text-slate-500">{label}</dt><dd className="mt-1 text-2xl font-bold">{value}</dd></div>; }
export default SaasOperacao;

