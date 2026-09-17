import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';

function AceitarConvite() {
  const [params] = useSearchParams(); const [form, setForm] = useState({ first_name: '', last_name: '', password: '', password_confirm: '' });
  const [state, setState] = useState({ busy: false, error: '', done: false });
  async function submit(event) { event.preventDefault(); setState({ busy: true, error: '', done: false }); try { await api.post('/auth/invitations/accept/', { ...form, invitation: params.get('invitation'), token: params.get('token') }); setState({ busy: false, error: '', done: true }); } catch (err) { setState({ busy: false, error: err.response?.data?.detail || 'Convite invalido ou expirado.', done: false }); } }
  if (state.done) return <AuthCard title="Acesso ativado"><p className="text-slate-600">Sua senha foi criada. Entre para continuar.</p><Link to="/login" className="btn-primary mt-5 inline-flex">Ir para o login</Link></AuthCard>;
  return <AuthCard title="Aceitar convite"><form onSubmit={submit} className="space-y-4"><Field label="Nome" value={form.first_name} onChange={(value) => setForm({ ...form, first_name: value })} /><Field label="Sobrenome" value={form.last_name} onChange={(value) => setForm({ ...form, last_name: value })} /><Field label="Senha" type="password" value={form.password} onChange={(value) => setForm({ ...form, password: value })} /><Field label="Confirmar senha" type="password" value={form.password_confirm} onChange={(value) => setForm({ ...form, password_confirm: value })} />{state.error && <p className="text-sm text-red-700">{state.error}</p>}<button disabled={state.busy} className="btn-primary w-full">{state.busy ? 'Ativando...' : 'Ativar acesso'}</button></form></AuthCard>;
}
function AuthCard({ title, children }) { return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6"><div className="w-full max-w-md rounded-2xl border bg-white p-8 shadow-sm"><h1 className="mb-6 text-2xl font-bold">{title}</h1>{children}</div></main>; }
function Field({ label, type = 'text', value, onChange }) { return <label className="block"><span className="mb-1 block text-sm font-bold">{label}</span><input required type={type} value={value} onChange={(event) => onChange(event.target.value)} className="input-field w-full" /></label>; }
export default AceitarConvite;

