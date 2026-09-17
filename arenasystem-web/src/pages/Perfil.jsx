import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { clearArenaContext } from '../arena/contextStorage';
import Layout from '../components/Layout';
import Icon from '../components/Icon';

export default function Perfil() {
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const initial = setTimeout(() => Promise.all([api.get('/usuarios/me/'), api.get('/auth/sessions/')])
      .then(([me, active]) => {
        setUser(me.data);
        setSessions(active.data.results || active.data || []);
      }).catch(() => {}), 0);
    return () => clearTimeout(initial);
  }, []);

  async function logout() {
    try {
      await api.post('/auth/logout/', { refresh: localStorage.getItem('refresh_token') });
    } catch {
      // A limpeza local continua mesmo se a API estiver indisponível.
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    clearArenaContext();
    navigate('/login');
  }

  const name = user?.nome_completo || user?.username || 'Carregando...';
  const initials = name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();

  return <Layout>
    <div className="mx-auto max-w-2xl">
      <header className="mb-5"><p className="text-sm font-semibold text-slate-500">Sua conta</p><h1 className="mt-1 text-[1.7rem] font-black tracking-[-0.03em] text-slate-950">Perfil</h1></header>

      <section className="relative overflow-hidden rounded-[1.75rem] bg-slate-950 p-5 text-white shadow-[0_18px_38px_rgba(15,23,42,0.16)]">
        <div className="absolute -right-14 -top-16 h-40 w-40 rounded-full bg-[var(--arena-secondary)]/20 blur-2xl" />
        <div className="relative flex items-center gap-4">
          <span className="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-full border-2 border-white/20 bg-[var(--arena-primary)] text-lg font-black">
            {user?.foto ? <img src={user.foto} alt="" className="h-full w-full object-cover" /> : initials}
          </span>
          <div className="min-w-0"><h2 className="truncate text-xl font-black">{name}</h2><p className="mt-1 truncate text-sm text-white/60">{user?.email || 'E-mail não informado'}</p><span className="mt-2 inline-flex rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide">{roleLabel(user)}</span></div>
        </div>
      </section>

      <section className="mt-6">
        <h2 className="mb-3 text-lg font-black text-slate-950">Conta e preferências</h2>
        <div className="app-surface overflow-hidden">
          <ProfileRow to="/app/perfil/dados" icon="users" title="Dados pessoais" text="Nome, e-mail e informações da conta" />
          <ProfileRow to="/app/perfil/notificacoes" icon="inbox" title="Notificações" text="Preferências de aulas, check-ins e cobranças" />
          <ProfileRow to="/app/perfil/seguranca" icon="shield" title="Privacidade e segurança" text="Senha e proteção da conta" />
          <ProfileRow to="/app/perfil/sessoes" icon="refresh" title="Sessões conectadas" text={`${sessions.length} sessão(ões) ativa(s)`} />
        </div>
      </section>

      <section className="mt-6 app-surface p-4">
        <div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-full bg-emerald-100 text-emerald-700"><Icon name="shield" className="h-5 w-5" /></span><div><h2 className="text-sm font-black text-slate-950">Conta protegida</h2><p className="mt-0.5 text-xs leading-5 text-slate-500">Se não reconhecer uma sessão, encerre seus acessos e altere a senha.</p></div></div>
      </section>

      <button type="button" onClick={logout} className="mt-6 w-full rounded-2xl border border-red-100 bg-white px-4 py-3.5 text-sm font-black text-red-600 shadow-sm transition hover:bg-red-50">Sair da conta</button>
      <p className="mt-5 text-center text-[11px] font-semibold text-slate-400">ArenaFlow • Experiência mobile segura</p>
    </div>
  </Layout>;
}

function ProfileRow({ to, icon, title, text }) {
  return <Link to={to} className="wellness-action flex w-full items-center gap-3 border-b border-slate-100 p-4 text-left transition last:border-0 hover:bg-slate-50"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[var(--arena-primary-soft)] text-[var(--arena-primary)]"><Icon name={icon} className="h-5 w-5" /></span><span className="min-w-0 flex-1"><strong className="block text-sm text-slate-900">{title}</strong><span className="mt-0.5 block text-xs text-slate-500">{text}</span></span><Icon name="chevronRight" className="h-5 w-5 text-slate-300" /></Link>;
}

function roleLabel(user) {
  const labels = { aluno: 'Aluno', professor: 'Professor', recepcao: 'Recepção', administrador: 'Administrador', dono: 'Proprietário' };
  return labels[user?.papel_efetivo] || 'Membro';
}
