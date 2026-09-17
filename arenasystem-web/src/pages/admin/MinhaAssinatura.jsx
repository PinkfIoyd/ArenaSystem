import { useEffect, useMemo, useState } from 'react';
import api from '../../api/client';


const STATUS_LABELS = {
  trialing: 'Periodo de teste', active: 'Ativa', past_due: 'Em atraso',
  suspended: 'Suspensa', cancel_at_period_end: 'Cancelamento agendado', canceled: 'Cancelada',
};

const money = (value) => new Intl.NumberFormat('pt-BR', {
  style: 'currency', currency: 'BRL',
}).format(Number(value || 0));

const date = (value) => value
  ? new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
  : 'Nao informado';

function MinhaAssinatura() {
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [cycle, setCycle] = useState('monthly');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [subscriptionResponse, plansResponse, invoicesResponse] = await Promise.all([
        api.get('/subscription/'), api.get('/saas/plans/'), api.get('/subscription/invoices/'),
      ]);
      setSubscription(subscriptionResponse.data);
      setCycle(subscriptionResponse.data.billing_cycle);
      setPlans(plansResponse.data);
      setInvoices(invoicesResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Nao foi possivel carregar a assinatura.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const percentages = useMemo(() => {
    if (!subscription) return {};
    return Object.fromEntries(Object.entries(subscription.limits).map(([key, limit]) => [
      key, Math.min(100, Math.round(((subscription.usage[key] || 0) / Math.max(limit, 1)) * 100)),
    ]));
  }, [subscription]);

  async function checkout(planId) {
    setBusy(`plan-${planId}`);
    setError('');
    try {
      const endpoint = subscription.status === 'trialing' || ['suspended', 'canceled'].includes(subscription.status)
        ? '/subscription/checkout/' : '/subscription/change-plan/';
      const payload = endpoint.includes('checkout') ? { plan_id: planId, billing_cycle: cycle } : { plan_id: planId, billing_cycle: cycle };
      const { data } = await api.post(endpoint, payload);
      if (data.checkout_url) {
        window.location.assign(data.checkout_url);
        return;
      }
      setNotice(data.pending_plan ? 'Alteracao agendada para o proximo ciclo.' : 'Assinatura atualizada.');
      await load();
    } catch (err) {
      const data = err.response?.data;
      if (data?.resources) {
        const resources = Object.entries(data.resources).map(([key, value]) => `${key}: ${value.usage}/${value.limit}`).join(', ');
        setError(`${data.detail} ${resources}`);
      } else {
        setError(data?.detail || 'Nao foi possivel alterar o plano.');
      }
    } finally {
      setBusy('');
    }
  }

  async function cancel() {
    if (!window.confirm('O acesso continuara ate o fim do periodo pago. Confirmar cancelamento?')) return;
    setBusy('cancel');
    try {
      await api.post('/subscription/cancel/');
      setNotice('Cancelamento agendado para o fim do ciclo.');
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Nao foi possivel cancelar.');
    } finally { setBusy(''); }
  }

  async function reactivate() {
    setBusy('reactivate');
    try {
      const { data } = await api.post('/subscription/reactivate/', { billing_cycle: cycle });
      if (data.checkout_url) window.location.assign(data.checkout_url);
      else { setNotice('Cancelamento removido.'); await load(); }
    } catch (err) {
      setError(err.response?.data?.detail || 'Nao foi possivel reativar.');
    } finally { setBusy(''); }
  }

  if (loading) return <div className="app-surface p-10 text-center text-slate-500">Carregando assinatura...</div>;
  if (error && !subscription) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div><p className="muted-label">Conta e cobranca</p><h1 className="text-3xl font-bold text-slate-950">Minha assinatura</h1></div>
        <div className="rounded-lg border border-slate-200 bg-white p-1" aria-label="Periodicidade">
          {['monthly', 'annual'].map((value) => <button key={value} type="button" onClick={() => setCycle(value)} className={`rounded-md px-4 py-2 text-sm font-bold ${cycle === value ? 'bg-slate-950 text-white' : 'text-slate-600'}`}>{value === 'monthly' ? 'Mensal' : 'Anual'}</button>)}
        </div>
      </header>

      {error && <Alert tone="error">{error}</Alert>}
      {notice && <Alert tone="success">{notice}</Alert>}
      {subscription.status === 'past_due' && <Alert tone="warning">Pagamento pendente. A carencia termina em {date(subscription.grace_ends_at)}.</Alert>}
      {subscription.status === 'suspended' && <Alert tone="error">A operacao da arena esta suspensa. Regularize a assinatura para reativar os modulos.</Alert>}

      <section className="grid gap-4 lg:grid-cols-[1.3fr_2fr]">
        <div className="app-surface p-6">
          <p className="muted-label">Plano atual</p>
          <div className="mt-2 flex items-start justify-between gap-3"><h2 className="text-2xl font-bold">{subscription.plan.name}</h2><span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-bold text-teal-800">{STATUS_LABELS[subscription.status] || subscription.status}</span></div>
          <p className="mt-3 text-slate-600">{subscription.plan.description || 'Plano ArenaFlow'}</p>
          <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
            <Metric label="Ciclo" value={subscription.billing_cycle === 'annual' ? 'Anual' : 'Mensal'} />
            <Metric label="Proxima renovacao" value={date(subscription.current_period_end || subscription.trial_ends_at)} />
          </dl>
          <div className="mt-6 flex flex-wrap gap-2">
            {subscription.status === 'cancel_at_period_end' || ['suspended', 'canceled'].includes(subscription.status)
              ? <button type="button" disabled={busy} onClick={reactivate} className="btn-primary">{busy === 'reactivate' ? 'Processando...' : 'Reativar assinatura'}</button>
              : <button type="button" disabled={busy} onClick={cancel} className="btn-secondary text-red-700">{busy === 'cancel' ? 'Processando...' : 'Cancelar no fim do ciclo'}</button>}
          </div>
        </div>

        <div className="app-surface p-6"><h2 className="text-xl font-bold">Consumo do plano</h2><div className="mt-5 grid gap-4 sm:grid-cols-2">
          {Object.entries(subscription.limits).map(([key, limit]) => <Usage key={key} label={RESOURCE_LABELS[key] || key} used={subscription.usage[key] || 0} limit={limit} percentage={percentages[key]} />)}
        </div></div>
      </section>

      <section><h2 className="mb-4 text-xl font-bold">Planos disponiveis</h2>{plans.length === 0 ? <div className="app-surface p-8 text-center text-slate-500">Os planos ainda estao sendo preparados pelo time comercial.</div> : <div className="grid gap-4 lg:grid-cols-3">{plans.map((plan) => <PlanCard key={plan.id} plan={plan} cycle={cycle} current={subscription.plan.id === plan.id && subscription.billing_cycle === cycle} busy={busy === `plan-${plan.id}`} onSelect={() => checkout(plan.id)} />)}</div>}</section>

      <section className="app-surface overflow-hidden"><div className="border-b border-slate-100 p-6"><h2 className="text-xl font-bold">Historico de cobrancas</h2></div>{invoices.length === 0 ? <p className="p-8 text-center text-slate-500">Nenhuma cobranca registrada.</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-600"><tr><th className="p-4">Data</th><th className="p-4">Tipo</th><th className="p-4">Valor</th><th className="p-4">Status</th><th className="p-4">Comprovante</th></tr></thead><tbody>{invoices.map((invoice) => <tr key={invoice.id} className="border-t border-slate-100"><td className="p-4">{date(invoice.created_at)}</td><td className="p-4 capitalize">{invoice.kind}</td><td className="p-4 font-bold">{money(invoice.amount)}</td><td className="p-4 capitalize">{invoice.status}</td><td className="p-4">{invoice.receipt_url ? <a className="font-bold text-teal-700" href={invoice.receipt_url} target="_blank" rel="noreferrer">Abrir</a> : '-'}</td></tr>)}</tbody></table></div>}</section>
    </div>
  );
}

const RESOURCE_LABELS = { admins: 'Administradores', professors: 'Professores', students: 'Alunos ativos', courts: 'Quadras', storage_mb: 'Armazenamento (MB)' };
function Metric({ label, value }) { return <div><dt className="text-slate-500">{label}</dt><dd className="mt-1 font-bold text-slate-950">{value}</dd></div>; }
function Usage({ label, used, limit, percentage }) { const tone = percentage >= 100 ? 'bg-red-500' : percentage >= 80 ? 'bg-amber-500' : 'bg-teal-600'; return <div><div className="flex justify-between text-sm"><span>{label}</span><strong>{used}/{limit}</strong></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className={`h-full ${tone}`} style={{ width: `${percentage}%` }} /></div></div>; }
function PlanCard({ plan, cycle, current, busy, onSelect }) { const price = cycle === 'annual' ? plan.annual_price : plan.monthly_price; return <article className={`app-surface p-6 ${current ? 'ring-2 ring-teal-600' : ''}`}><p className="muted-label">{plan.code}</p><h3 className="mt-1 text-xl font-bold">{plan.name}</h3><p className="mt-3 min-h-12 text-sm text-slate-600">{plan.description}</p><p className="mt-5 text-3xl font-bold">{money(price)}<span className="text-sm font-normal text-slate-500">/{cycle === 'annual' ? 'ano' : 'mes'}</span></p><ul className="mt-5 space-y-2 text-sm text-slate-600"><li>{plan.max_students} alunos</li><li>{plan.max_courts} quadras</li><li>{plan.max_admins} administradores</li><li>{plan.max_professors} professores</li></ul><button type="button" disabled={current || busy} onClick={onSelect} className="btn-primary mt-6 w-full">{current ? 'Plano atual' : busy ? 'Processando...' : 'Escolher plano'}</button></article>; }
function Alert({ tone, children }) { const colors = tone === 'error' ? 'border-red-200 bg-red-50 text-red-800' : tone === 'warning' ? 'border-amber-200 bg-amber-50 text-amber-900' : 'border-emerald-200 bg-emerald-50 text-emerald-800'; return <div className={`rounded-lg border p-4 text-sm font-semibold ${colors}`}>{children}</div>; }
function ErrorState({ message, onRetry }) { return <div className="app-surface p-10 text-center"><p className="text-red-700">{message}</p><button type="button" onClick={onRetry} className="btn-primary mt-4">Tentar novamente</button></div>; }

export default MinhaAssinatura;
