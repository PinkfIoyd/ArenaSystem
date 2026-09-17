import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';

function RecuperarSenha({ confirm = false }) {
  const [params] = useSearchParams(); const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [confirmation, setConfirmation] = useState(''); const [state, setState] = useState({ busy: false, error: '', done: false });
  async function submit(event) { event.preventDefault(); setState({ busy: true, error: '', done: false }); try { if (confirm) await api.post('/auth/password-reset/confirm/', { request: params.get('request'), token: params.get('token'), password, password_confirm: confirmation }); else await api.post('/auth/password-reset/request/', { email }); setState({ busy: false, error: '', done: true }); } catch (err) { const data = err.response?.data; setState({ busy: false, error: data?.detail || data?.password?.[0] || 'Nao foi possivel concluir.', done: false }); } }
  return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6"><div className="w-full max-w-md rounded-2xl border bg-white p-8 shadow-sm"><h1 className="text-2xl font-bold">{confirm ? 'Crie uma nova senha' : 'Recuperar senha'}</h1>{state.done ? <div className="mt-5"><p className="text-slate-600">{confirm ? 'Senha atualizada com sucesso.' : 'Se houver uma conta ativa, enviaremos as instrucoes por e-mail.'}</p><Link to="/login" className="btn-primary mt-5 inline-flex">Voltar ao login</Link></div> : <form onSubmit={submit} className="mt-6 space-y-4">{confirm ? <><Field label="Nova senha" type="password" value={password} onChange={setPassword} /><Field label="Confirmar senha" type="password" value={confirmation} onChange={setConfirmation} /></> : <Field label="E-mail" type="email" value={email} onChange={setEmail} />}{state.error && <p className="text-sm text-red-700">{state.error}</p>}<button disabled={state.busy} className="btn-primary w-full">{state.busy ? 'Enviando...' : 'Continuar'}</button></form>}</div></main>;
}
function Field({ label, type, value, onChange }) { return <label className="block"><span className="mb-1 block text-sm font-bold">{label}</span><input required type={type} value={value} onChange={(event) => onChange(event.target.value)} className="input-field w-full" /></label>; }
export default RecuperarSenha;

