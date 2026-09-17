import { Link } from 'react-router-dom';

import Layout from '../Layout';
import Icon from '../Icon';

export default function ProfilePage({ title, subtitle, children }) {
  return (
    <Layout>
      <div className="mx-auto max-w-2xl">
        <header className="mb-5">
          <Link to="/app/perfil" className="mb-4 inline-flex items-center gap-2 text-sm font-bold text-[var(--arena-primary)]">
            <Icon name="chevronLeft" className="h-4 w-4" />
            Voltar ao perfil
          </Link>
          <h1 className="text-[1.7rem] font-black tracking-[-0.03em] text-slate-950">{title}</h1>
          {subtitle && <p className="mt-1 text-sm leading-6 text-slate-500">{subtitle}</p>}
        </header>
        {children}
      </div>
    </Layout>
  );
}

export function InlineMessage({ type = 'success', children }) {
  const styles = type === 'error'
    ? 'border-red-200 bg-red-50 text-red-700'
    : 'border-emerald-200 bg-emerald-50 text-emerald-800';
  return <div role={type === 'error' ? 'alert' : 'status'} className={`rounded-2xl border px-4 py-3 text-sm font-semibold ${styles}`}>{children}</div>;
}

export function Field({ label, hint, error, ...props }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-bold text-slate-800">{label}</span>
      <input {...props} className={`input-field w-full ${error ? 'border-red-400' : ''}`} aria-invalid={Boolean(error)} />
      {error ? <span className="mt-1 block text-xs font-semibold text-red-600">{error}</span> : hint ? <span className="mt-1 block text-xs text-slate-500">{hint}</span> : null}
    </label>
  );
}
