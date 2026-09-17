import { useEffect, useState } from 'react';

import api from '../api/client';
import ProfilePage, { InlineMessage } from '../components/profile/ProfilePage';
import { apiErrorMessage } from '../utils/apiErrors';

const groups = [
  { key: 'classes', title: 'Aulas', description: 'Agenda, alterações e lembretes de aula.' },
  { key: 'checkins', title: 'Check-ins', description: 'Confirmações, rejeições e expirações.' },
  { key: 'financial', title: 'Financeiro', description: 'Vencimentos e situação das mensalidades.' },
  { key: 'reservations', title: 'Reservas', description: 'Confirmações e cancelamentos de reservas.' },
];

export default function PerfilNotificacoes() {
  const [preferences, setPreferences] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    let active = true;
    api.get('/auth/notification-preferences/').then(({ data }) => active && setPreferences(data))
      .catch((error) => active && setMessage({ type: 'error', text: apiErrorMessage(error, 'Não foi possível carregar as preferências.') }));
    return () => { active = false; };
  }, []);

  const toggle = (field) => setPreferences((current) => ({ ...current, [field]: !current[field] }));
  async function save() {
    setSaving(true); setMessage(null);
    try {
      const { data } = await api.patch('/auth/notification-preferences/', preferences);
      setPreferences(data);
      setMessage({ type: 'success', text: 'Preferências de notificações salvas.' });
    } catch (error) { setMessage({ type: 'error', text: apiErrorMessage(error) }); }
    finally { setSaving(false); }
  }

  return (
    <ProfilePage title="Notificações" subtitle="Escolha como deseja receber cada tipo de aviso. A aba Alertas continua reunindo as mensagens recebidas.">
      {message && <div className="mb-4"><InlineMessage type={message.type}>{message.text}</InlineMessage></div>}
      {!preferences ? <div className="app-surface h-64 animate-pulse bg-slate-100" aria-label="Carregando preferências" /> : (
        <div className="space-y-4">
          {groups.map((group) => <section key={group.key} className="app-surface p-5"><h2 className="font-black text-slate-950">{group.title}</h2><p className="mt-1 text-xs leading-5 text-slate-500">{group.description}</p><div className="mt-4 grid gap-3 sm:grid-cols-2"><PreferenceToggle label="No aplicativo" checked={preferences[`app_${group.key}`]} onChange={() => toggle(`app_${group.key}`)} /><PreferenceToggle label="Por e-mail" checked={preferences[`email_${group.key}`]} onChange={() => toggle(`email_${group.key}`)} /></div></section>)}
          <button type="button" onClick={save} disabled={saving} className="btn-primary w-full disabled:cursor-wait disabled:opacity-60">{saving ? 'Salvando...' : 'Salvar preferências'}</button>
        </div>
      )}
    </ProfilePage>
  );
}

function PreferenceToggle({ label, checked, onChange }) {
  return <label className="flex cursor-pointer items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm font-bold text-slate-800"><span>{label}</span><input type="checkbox" checked={checked} onChange={onChange} className="h-5 w-5 accent-[var(--arena-primary)]" /></label>;
}
