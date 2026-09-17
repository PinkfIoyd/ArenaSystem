import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import Toast from '../components/Toast';
import { checkinUi } from '../utils/checkinUi';
import { accessView } from '../utils/accessUi';

export default function Home() {
  const [home, setHome] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [classBusy, setClassBusy] = useState(false);
  const [accessBusy, setAccessBusy] = useState(false);
  const [toast, setToast] = useState(null);
  const [now, setNow] = useState(0);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/mobile/home/');
      setHome(data);
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível carregar o aplicativo.' });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const initial = setTimeout(load, 0);
    const polling = setInterval(load, 15000);
    return () => { clearTimeout(initial); clearInterval(polling); };
  }, [load]);
  useEffect(() => {
    const initial = setTimeout(() => api.get('/usuarios/me/').then(({ data }) => setUser(data)).catch(() => {}), 0);
    return () => clearTimeout(initial);
  }, []);
  useEffect(() => {
    const initial = setTimeout(() => setNow(Date.now()), 0);
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => { clearTimeout(initial); clearInterval(timer); };
  }, []);

  const next = home?.next_class;
  const classState = classBusy ? 'requesting' : next?.checkin?.state || 'outside_window';
  const classUi = checkinUi(classState);
  const firstName = (user?.first_name || user?.nome_completo || user?.username || 'Atleta').split(' ')[0];
  const features = home?.features || {};

  async function requestClassCheckin() {
    if (!next || classUi.disabled) return;
    setClassBusy(true);
    try {
      const { data } = await api.post(`/turmas/${next.turma.id}/checkin/`);
      setToast({ tipo: 'sucesso', mensagem: data.detail });
      await load();
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível solicitar o check-in.' });
      await load();
    } finally { setClassBusy(false); }
  }

  async function requestOpenAccess() {
    setAccessBusy(true);
    try {
      const { data } = await api.post('/access-visits/check-in/');
      setToast({ tipo: 'sucesso', mensagem: data.detail });
      await load();
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível solicitar o acesso.' });
      await load();
    } finally { setAccessBusy(false); }
  }

  async function checkoutOpenAccess() {
    const visit = home?.access?.visit;
    if (!visit?.public_id) return;
    setAccessBusy(true);
    try {
      await api.post(`/access-visits/${visit.public_id}/check-out/`);
      setToast({ tipo: 'sucesso', mensagem: 'Saída registrada com sucesso.' });
      await load();
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível registrar a saída.' });
    } finally { setAccessBusy(false); }
  }

  return <Layout>
    <div className="mx-auto max-w-5xl">
      <section className="mb-5 flex items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500">Olá, {firstName} 👋</p>
          <h1 className="mt-1 text-[1.7rem] font-black leading-tight tracking-[-0.03em] text-slate-950 sm:text-3xl">
            {features.open_access ? 'Pronto para treinar?' : 'Vamos para a próxima aula?'}
          </h1>
        </div>
        <span className="hidden rounded-full bg-white px-3 py-1.5 text-xs font-bold text-slate-600 shadow-sm sm:inline-flex">{home?.arena?.nome}</span>
      </section>

      {features.open_access ? <OpenAccessHero access={home?.access} loading={loading} busy={accessBusy} onRequest={requestOpenAccess} onCheckout={checkoutOpenAccess} />
        : <ClassHero next={next} loading={loading} state={classState} ui={classUi} now={now} onRequest={requestClassCheckin} />}

      {features.open_access && features.classes && <section className="mt-6">
        <SectionTitle title="Próxima aula" action="Ver turmas" to="/app/turmas" />
        <ClassCompactCard next={next} loading={loading} ui={classUi} now={now} onRequest={requestClassCheckin} />
      </section>}

      <section className="mt-7">
        <SectionTitle title="Acesso rápido" />
        <div className="grid grid-cols-4 gap-2.5">
          {features.open_access && <QuickAction to="/app/acessos" icon="check" label="Acessos" color="bg-emerald-100 text-emerald-700" />}
          {features.classes && <QuickAction to="/app/turmas" icon="court" label="Turmas" color="bg-violet-100 text-violet-700" />}
          {features.classes && <QuickAction to="/app/checkins" icon="check" label="Presenças" color="bg-emerald-100 text-emerald-700" />}
          <QuickAction to="/app/mensalidades" icon="money" label="Pagamentos" color="bg-amber-100 text-amber-700" />
          {features.reservations && <QuickAction to="/app/reservas" icon="calendar" label="Reservas" color="bg-sky-100 text-sky-700" />}
        </div>
      </section>

      <section className="mt-8">
        <SectionTitle title="Sua rotina" />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {features.classes && <RoutineCard to="/app/turmas" icon="court" eyebrow="Aulas" title="Explore suas turmas" text="Horários, professores e vagas em um só lugar." />}
          {features.reservations && <RoutineCard to="/app/reservas" icon="calendar" eyebrow="Agenda" title="Reserve seu horário" text="Consulte a disponibilidade dos espaços." />}
          <RoutineCard to="/app/mensalidades" icon="money" eyebrow="Financeiro" title="Mensalidades em dia" text="Acompanhe vencimentos e pagamentos." />
        </div>
      </section>
    </div>
    {toast && <Toast {...toast} onClose={() => setToast(null)} />}
  </Layout>;
}

function OpenAccessHero({ access, loading, busy, onRequest, onCheckout }) {
  const state = busy ? 'requesting' : access?.state || 'blocked';
  const view = accessView(state, access?.detail);
  const visit = access?.visit;
  return <section className="wellness-hero relative overflow-hidden bg-slate-950 p-5 text-white sm:p-7" aria-live="polite">
    <div className="pointer-events-none absolute -right-16 -top-20 h-52 w-52 rounded-full bg-[var(--arena-secondary)]/25 blur-2xl" />
    <div className="pointer-events-none absolute -bottom-24 -left-14 h-52 w-52 rounded-full bg-[var(--arena-primary)]/60 blur-3xl" />
    <div className="relative">
      <span className="rounded-full bg-white/10 px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.13em] text-white/90">Acesso livre</span>
      {loading ? <HeroLoading /> : <>
        <h2 className="mt-5 text-2xl font-black tracking-[-0.03em] sm:text-3xl">{view.title}</h2>
        <p className="mt-2 max-w-xl text-sm leading-6 text-white/65">{view.text}</p>
        {visit?.inadimplente_no_momento && <p className="mt-3 rounded-xl bg-amber-300/15 p-3 text-xs font-bold text-amber-100">Há uma pendência financeira. A entrada depende da política da unidade.</p>}
        {state === 'confirmed' ? <button type="button" disabled={busy} onClick={onCheckout} className="wellness-action mt-6 min-h-14 w-full rounded-2xl bg-white px-5 py-3.5 text-sm font-black text-slate-950">Fazer check-out</button>
          : <button type="button" disabled={busy || state !== 'available'} onClick={onRequest} className={`wellness-action mt-6 min-h-14 w-full rounded-2xl px-5 py-3.5 text-sm font-black ${state === 'available' ? 'bg-white text-slate-950' : 'bg-white/10 text-white/60'}`}>{view.button}</button>}
      </>}
    </div>
  </section>;
}

function ClassHero({ next, loading, state, ui, now, onRequest }) {
  return <section className="wellness-hero relative overflow-hidden bg-slate-950 p-5 text-white sm:p-7" aria-live="polite">
    <div className="relative"><div className="mb-5 flex items-center justify-between gap-3"><span className="rounded-full bg-white/10 px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.13em]">Próxima aula</span>{next && <span className="text-xs font-bold text-white/70">{getCountdown(next.starts_at, now)}</span>}</div>
      {loading ? <HeroLoading /> : !next ? <EmptyHero /> : <><h2 className="text-2xl font-black">{next.turma.nome}</h2><div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold text-white/80"><span className="rounded-full bg-white/10 px-3 py-2">{formatClassDate(next.starts_at)}</span><span className="rounded-full bg-white/10 px-3 py-2">{next.turma.quadra_nome}</span></div><button type="button" onClick={onRequest} disabled={ui.disabled} className={`wellness-action mt-6 min-h-14 w-full rounded-2xl px-5 py-3.5 text-sm font-black ${heroButtonClass(state)}`}>{ui.label}</button><p className="mt-3 text-center text-[11px] text-white/55">Disponível 20 min antes até 10 min depois do início</p></>}
    </div>
  </section>;
}

function ClassCompactCard({ next, loading, ui, now, onRequest }) {
  if (loading) return <div className="app-surface h-32 animate-pulse" />;
  if (!next) return <div className="app-surface p-5 text-sm text-slate-500">Nenhuma aula próxima.</div>;
  return <article className="app-surface flex flex-col gap-4 p-5 sm:flex-row sm:items-center"><div className="min-w-0 flex-1"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">{getCountdown(next.starts_at, now)}</p><h3 className="mt-1 truncate text-lg font-black text-slate-950">{next.turma.nome}</h3><p className="mt-1 text-sm text-slate-500">{formatClassDate(next.starts_at)} · {next.turma.quadra_nome}</p></div><button type="button" onClick={onRequest} disabled={ui.disabled} className="btn-primary min-h-11 px-5">{ui.label}</button></article>;
}

function SectionTitle({ title, action, to }) { return <div className="mb-3 flex items-center justify-between"><h2 className="text-lg font-black text-slate-950">{title}</h2>{action && <Link to={to} className="text-xs font-black text-[var(--arena-primary)]">{action}</Link>}</div>; }
function QuickAction({ to, icon, label, color }) { return <Link to={to} className="wellness-action flex min-w-0 flex-col items-center gap-2 rounded-2xl bg-white p-2.5 text-center shadow-sm"><span className={`grid h-11 w-11 place-items-center rounded-full ${color}`}><Icon name={icon} className="h-5 w-5" /></span><span className="w-full truncate text-[10px] font-bold text-slate-700 sm:text-xs">{label}</span></Link>; }
function RoutineCard({ to, icon, eyebrow, title, text }) { return <Link to={to} className="wellness-action app-surface-hover flex items-center gap-4 p-4"><span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[var(--arena-primary-soft)] text-[var(--arena-primary)]"><Icon name={icon} className="h-6 w-6" /></span><span className="min-w-0 flex-1"><span className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-400">{eyebrow}</span><strong className="block text-sm text-slate-950">{title}</strong><span className="mt-1 block text-xs text-slate-500">{text}</span></span></Link>; }
function HeroLoading() { return <div className="mt-5 animate-pulse"><div className="h-7 w-2/3 rounded-lg bg-white/10" /><div className="mt-4 h-14 rounded-2xl bg-white/10" /></div>; }
function EmptyHero() { return <div className="py-4"><h2 className="text-2xl font-black">Agenda livre por enquanto</h2><Link to="/app/turmas" className="mt-5 inline-flex rounded-xl bg-white px-4 py-3 text-sm font-black text-slate-950">Ver minhas turmas</Link></div>; }
function getCountdown(startsAt, now) { if (!startsAt || !now) return ''; const seconds = Math.round((new Date(startsAt).getTime() - now) / 1000); if (seconds <= 0) return `Começou há ${Math.ceil(Math.abs(seconds) / 60)} min`; const hours = Math.floor(seconds / 3600); const minutes = Math.floor((seconds % 3600) / 60); return hours ? `${hours}h ${minutes}min` : `${Math.max(minutes, 1)} min`; }
function formatClassDate(value) { return new Date(value).toLocaleString('pt-BR', { weekday: 'short', hour: '2-digit', minute: '2-digit' }).replace('.', ''); }
function heroButtonClass(state) { if (state === 'available') return 'bg-white text-slate-950'; if (state === 'pending') return 'bg-amber-300 text-amber-950'; if (state === 'confirmed') return 'bg-emerald-300 text-emerald-950'; if (state === 'rejected') return 'bg-red-300 text-red-950'; return 'bg-white/10 text-white/60'; }
