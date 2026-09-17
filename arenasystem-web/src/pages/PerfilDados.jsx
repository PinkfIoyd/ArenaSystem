import { useEffect, useState } from 'react';

import api from '../api/client';
import ProfilePage, { Field, InlineMessage } from '../components/profile/ProfilePage';
import { apiErrorMessage, apiFieldErrors } from '../utils/apiErrors';

const emptyProfile = { first_name: '', last_name: '', telefone: '', data_nascimento: '', email: '', foto: '' };

export default function PerfilDados() {
  const [profile, setProfile] = useState(emptyProfile);
  const [photo, setPhoto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [errors, setErrors] = useState({});
  const [emailForm, setEmailForm] = useState({ email: '', current_password: '' });
  const [emailBusy, setEmailBusy] = useState(false);

  useEffect(() => {
    let active = true;
    api.get('/usuarios/me/').then(({ data }) => {
      if (!active) return;
      setProfile({ ...emptyProfile, ...data, data_nascimento: data.data_nascimento || '' });
      setEmailForm((current) => ({ ...current, email: data.email || '' }));
    }).catch((error) => active && setMessage({ type: 'error', text: apiErrorMessage(error, 'Não foi possível carregar seus dados.') }))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const update = (field) => (event) => setProfile((current) => ({ ...current, [field]: event.target.value }));

  async function saveProfile(event) {
    event.preventDefault();
    setSaving(true); setErrors({}); setMessage(null);
    const payload = new FormData();
    ['first_name', 'last_name', 'telefone'].forEach((field) => payload.append(field, profile[field] || ''));
    if (profile.data_nascimento) payload.append('data_nascimento', profile.data_nascimento);
    if (photo) payload.append('foto', photo);
    try {
      const { data } = await api.patch('/usuarios/me/', payload, { headers: { 'Content-Type': 'multipart/form-data' } });
      setProfile((current) => ({ ...current, ...data, data_nascimento: data.data_nascimento || '' }));
      setPhoto(null);
      setMessage({ type: 'success', text: 'Dados pessoais atualizados.' });
    } catch (error) {
      setErrors(apiFieldErrors(error));
      setMessage({ type: 'error', text: apiErrorMessage(error) });
    } finally { setSaving(false); }
  }

  async function requestEmailChange(event) {
    event.preventDefault();
    setEmailBusy(true); setErrors({}); setMessage(null);
    try {
      const { data } = await api.post('/auth/email-change/request/', emailForm);
      setEmailForm((current) => ({ ...current, current_password: '' }));
      setMessage({ type: 'success', text: data.detail });
    } catch (error) {
      setErrors(apiFieldErrors(error));
      setMessage({ type: 'error', text: apiErrorMessage(error) });
    } finally { setEmailBusy(false); }
  }

  return (
    <ProfilePage title="Dados pessoais" subtitle="Mantenha suas informações atualizadas. A arena e o seu perfil de acesso não podem ser alterados aqui.">
      {message && <div className="mb-4"><InlineMessage type={message.type}>{message.text}</InlineMessage></div>}
      {loading ? <ProfileSkeleton /> : (
        <div className="space-y-5">
          <form onSubmit={saveProfile} className="app-surface space-y-4 p-5">
            <div className="flex items-center gap-4">
              <span className="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-full bg-[var(--arena-primary-soft)] text-lg font-black text-[var(--arena-primary)]">
                {profile.foto ? <img src={profile.foto} alt="Foto de perfil" className="h-full w-full object-cover" /> : (profile.first_name?.[0] || profile.username?.[0] || 'A').toUpperCase()}
              </span>
              <label className="min-w-0 flex-1 text-sm font-bold text-slate-800">Foto de perfil
                <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setPhoto(event.target.files?.[0] || null)} className="mt-2 block w-full text-xs text-slate-500 file:mr-3 file:rounded-xl file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:font-bold" />
                {errors.foto && <span className="mt-1 block text-xs text-red-600">{errors.foto}</span>}
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Nome" value={profile.first_name} onChange={update('first_name')} autoComplete="given-name" error={errors.first_name} />
              <Field label="Sobrenome" value={profile.last_name} onChange={update('last_name')} autoComplete="family-name" error={errors.last_name} />
            </div>
            <Field label="Telefone" type="tel" inputMode="tel" value={profile.telefone} onChange={update('telefone')} autoComplete="tel" error={errors.telefone} />
            <Field label="Data de nascimento" type="date" value={profile.data_nascimento} onChange={update('data_nascimento')} error={errors.data_nascimento} />
            <button disabled={saving} className="btn-primary w-full disabled:cursor-wait disabled:opacity-60">{saving ? 'Salvando...' : 'Salvar dados pessoais'}</button>
          </form>

          <form onSubmit={requestEmailChange} className="app-surface space-y-4 p-5">
            <div><h2 className="text-base font-black text-slate-950">Alterar e-mail</h2><p className="mt-1 text-xs leading-5 text-slate-500">A alteração só será aplicada depois da confirmação enviada ao novo endereço.</p></div>
            <Field label="Novo e-mail" type="email" value={emailForm.email} onChange={(event) => setEmailForm((current) => ({ ...current, email: event.target.value }))} autoComplete="email" required error={errors.email} />
            <Field label="Senha atual" type="password" value={emailForm.current_password} onChange={(event) => setEmailForm((current) => ({ ...current, current_password: event.target.value }))} autoComplete="current-password" required error={errors.current_password} />
            <button disabled={emailBusy} className="btn-secondary w-full disabled:cursor-wait disabled:opacity-60">{emailBusy ? 'Enviando...' : 'Enviar confirmação'}</button>
          </form>
        </div>
      )}
    </ProfilePage>
  );
}

function ProfileSkeleton() {
  return <div aria-label="Carregando dados" className="app-surface animate-pulse space-y-4 p-5"><div className="h-16 w-16 rounded-full bg-slate-200" /><div className="h-12 rounded-xl bg-slate-100" /><div className="h-12 rounded-xl bg-slate-100" /><div className="h-12 rounded-xl bg-slate-100" /></div>;
}
