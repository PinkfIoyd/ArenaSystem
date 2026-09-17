import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';

const money = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value));

function Precos() {
  const [plans, setPlans] = useState([]);
  const [cycle, setCycle] = useState('monthly');
  const [state, setState] = useState('loading');

  useEffect(() => {
    api.get('/saas/plans/').then(({ data }) => { setPlans(data); setState('ready'); }).catch(() => setState('error'));
  }, []);

  return <main className="min-h-screen bg-slate-50 px-6 py-12"><div className="mx-auto max-w-6xl">
    <header className="text-center"><p className="muted-label">ArenaFlow SaaS</p><h1 className="mt-2 text-4xl font-black text-slate-950">Planos para operar sua arena</h1><p className="mx-auto mt-4 max-w-2xl text-slate-600">Teste por 14 dias. Escolha o plano de acordo com sua equipe, alunos e quadras.</p><div className="mt-6 inline-flex rounded-lg border bg-white p-1">{['monthly', 'annual'].map((value) => <button key={value} type="button" onClick={() => setCycle(value)} className={`rounded-md px-5 py-2 font-bold ${cycle === value ? 'bg-slate-950 text-white' : 'text-slate-600'}`}>{value === 'monthly' ? 'Mensal' : 'Anual'}</button>)}</div></header>
    {state === 'loading' && <p className="mt-12 text-center text-slate-500">Carregando planos...</p>}
    {state === 'error' && <p className="mt-12 text-center text-red-700">Nao foi possivel carregar os planos.</p>}
    {state === 'ready' && plans.length === 0 && <div className="mx-auto mt-12 max-w-xl rounded-xl border bg-white p-8 text-center"><h2 className="text-xl font-bold">Catalogo em preparacao</h2><p className="mt-2 text-slate-600">Os precos comerciais ainda nao foram publicados.</p></div>}
    <section className="mt-10 grid gap-5 lg:grid-cols-3">{plans.map((plan) => <article key={plan.id} className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm"><p className="text-sm font-bold uppercase tracking-wide text-teal-700">{plan.code}</p><h2 className="mt-2 text-2xl font-bold">{plan.name}</h2><p className="mt-3 min-h-12 text-slate-600">{plan.description}</p><p className="mt-6 text-3xl font-black">{money(cycle === 'annual' ? plan.annual_price : plan.monthly_price)}<span className="text-sm font-normal text-slate-500">/{cycle === 'annual' ? 'ano' : 'mes'}</span></p><ul className="mt-6 space-y-2 text-sm text-slate-600"><li>{plan.max_students} alunos ativos</li><li>{plan.max_courts} quadras</li><li>{plan.max_professors} professores</li><li>{plan.max_admins} administradores</li><li>{plan.storage_mb} MB de armazenamento</li></ul><Link to="/login" className="btn-primary mt-7 flex justify-center">Comecar teste</Link></article>)}</section>
    <section className="mx-auto mt-16 max-w-3xl"><h2 className="text-center text-2xl font-bold">Perguntas frequentes</h2><div className="mt-6 space-y-3"><Faq title="Quando ocorre a primeira cobranca?">Depois do periodo de teste de 14 dias, conforme o plano contratado.</Faq><Faq title="Posso mudar de plano?">Sim. Upgrades sao imediatos apos pagamento; downgrades entram no proximo ciclo.</Faq><Faq title="O que acontece em caso de atraso?">A arena recebe avisos e uma carencia de sete dias antes da suspensao operacional.</Faq></div></section>
  </div></main>;
}

function Faq({ title, children }) { return <details className="rounded-xl border bg-white p-5"><summary className="cursor-pointer font-bold">{title}</summary><p className="mt-3 text-slate-600">{children}</p></details>; }
export default Precos;

