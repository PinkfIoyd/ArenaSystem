import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import api from '../api/client';
import { apiErrorMessage } from '../utils/apiErrors';

export default function ConfirmarEmail() {
  const [params] = useSearchParams();
  const request = params.get('request'); const token = params.get('token');
  const [state, setState] = useState(() => request && token
    ? { loading: true, error: '', detail: '' }
    : { loading: false, error: 'Link de confirmação incompleto.', detail: '' });
  useEffect(() => {
    if (!request || !token) return;
    api.post('/auth/email-change/confirm/', { request, token })
      .then(({ data }) => setState({ loading: false, error: '', detail: data.detail }))
      .catch((error) => setState({ loading: false, error: apiErrorMessage(error), detail: '' }));
  }, [request, token]);
  return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6"><section className="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 text-center shadow-xl"><h1 className="text-2xl font-black text-slate-950">Confirmação de e-mail</h1>{state.loading ? <p className="mt-4 text-slate-500">Validando link...</p> : <><p role={state.error ? 'alert' : 'status'} className={`mt-4 text-sm leading-6 ${state.error ? 'text-red-700' : 'text-emerald-700'}`}>{state.error || state.detail}</p><Link to={localStorage.getItem('access_token') ? '/app/perfil/dados' : '/login'} className="btn-primary mt-6 inline-flex">Continuar</Link></>}</section></main>;
}
