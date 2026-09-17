import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import api from '../api/client';
import { clearArenaContext } from '../arena/contextStorage';
import Modal from '../components/Modal';
import ProfilePage, { InlineMessage } from '../components/profile/ProfilePage';
import { apiErrorMessage } from '../utils/apiErrors';

export default function PerfilSessoes() {
  const [sessions, setSessions] = useState(null);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);
  const navigate = useNavigate();

  async function load() {
    try { const { data } = await api.get('/auth/sessions/'); setSessions(data.results || data); }
    catch (error) { setMessage({ type: 'error', text: apiErrorMessage(error, 'Não foi possível carregar as sessões.') }); }
  }
  useEffect(() => {
    let active = true;
    api.get('/auth/sessions/').then(({ data }) => {
      if (active) setSessions(data.results || data);
    }).catch((error) => {
      if (active) setMessage({ type: 'error', text: apiErrorMessage(error, 'Não foi possível carregar as sessões.') });
    });
    return () => { active = false; };
  }, []);

  async function revoke() {
    if (!selected) return;
    setBusy(true); setMessage(null);
    try {
      const { data } = await api.post(`/auth/sessions/${selected.public_id}/revoke/`);
      if (data.current) {
        localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); clearArenaContext(); navigate('/login'); return;
      }
      setSelected(null);
      setMessage({ type: 'success', text: 'Sessão encerrada com sucesso.' });
      await load();
    } catch (error) { setMessage({ type: 'error', text: apiErrorMessage(error) }); }
    finally { setBusy(false); }
  }

  return (
    <ProfilePage title="Sessões conectadas" subtitle="Confira onde sua conta está aberta. O endereço IP é exibido apenas para ajudar a reconhecer o acesso.">
      {message && <div className="mb-4"><InlineMessage type={message.type}>{message.text}</InlineMessage></div>}
      {!sessions ? <div className="app-surface h-52 animate-pulse bg-slate-100" aria-label="Carregando sessões" /> : sessions.length === 0 ? <div className="app-surface p-8 text-center text-sm text-slate-500">Nenhuma sessão ativa encontrada.</div> : <div className="space-y-3">{sessions.map((session) => <SessionCard key={session.public_id} session={session} onRevoke={() => setSelected(session)} />)}</div>}
      <Modal aberto={Boolean(selected)} onFechar={() => !busy && setSelected(null)} titulo="Encerrar esta sessão?" tamanho="sm">
        <p className="text-sm leading-6 text-slate-600">O dispositivo <strong>{selected?.device}</strong> perderá o acesso imediatamente.{selected?.current ? ' Como esta é a sessão atual, você voltará para o login.' : ''}</p>
        <div className="mt-5 flex gap-3"><button type="button" onClick={() => setSelected(null)} disabled={busy} className="btn-secondary flex-1">Cancelar</button><button type="button" onClick={revoke} disabled={busy} className="flex-1 rounded-xl bg-red-600 px-4 py-3 text-sm font-black text-white disabled:opacity-60">{busy ? 'Encerrando...' : 'Encerrar sessão'}</button></div>
      </Modal>
    </ProfilePage>
  );
}

function SessionCard({ session, onRevoke }) {
  const lastSeen = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(session.last_seen_at));
  return <article className="app-surface p-5"><div className="flex items-start justify-between gap-4"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 className="font-black text-slate-950">{session.device}</h2>{session.current && <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-black uppercase text-emerald-700">Este dispositivo</span>}</div><p className="mt-2 text-xs text-slate-500">Última atividade: {lastSeen}</p><p className="mt-1 text-xs text-slate-500">IP: {session.ip_address || 'Não identificado'}</p></div><button type="button" onClick={onRevoke} className="shrink-0 text-xs font-black text-red-600">Encerrar</button></div></article>;
}
