import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import Modal from '../../components/Modal';
import Toast from '../../components/Toast';
import { useArenaContext } from '../../contexts/arenaContextStore';
import { apiErrorMessage, apiFieldErrors } from '../../utils/apiErrors';

const settingsFor = (type) => type === 'academia'
  ? { classes_enabled: true, open_access_enabled: true, reservations_enabled: false, store_enabled: false, open_access_validation: 'reception', open_access_pending_minutes: 10 }
  : { classes_enabled: true, open_access_enabled: false, reservations_enabled: true, store_enabled: true, open_access_validation: 'reception', open_access_pending_minutes: 10 };

const initialForm = () => ({
  nome: '', slug: '', tipo_negocio: 'arena', documento: '', email_contato: '', telefone_contato: '', endereco: '',
  plano_contratado: 'starter', status_assinatura: 'trial', limite_alunos: 150, limite_quadras: 4, limite_admins: 3,
  cor_primaria: '#0F766E', cor_secundaria: '#A3E635', cor_fundo: '#ECFEFF', cor_texto: '#071B26',
  admin_nome: '', admin_sobrenome: '', admin_email: '', admin_senha: '', admin_senha_confirm: '',
  operational_settings: settingsFor('arena'),
});

export default function SaasArenas() {
  const [arenas, setArenas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [accessTarget, setAccessTarget] = useState(null);
  const [reason, setReason] = useState('');
  const [accessing, setAccessing] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();
  const { contexto, acessarArena, sairDaArena } = useArenaContext();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/saas/arenas/');
      setArenas(Array.isArray(data) ? data : data.results || []);
    } catch { setToast({ mensagem: 'Erro ao carregar unidades.', tipo: 'erro' }); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const id = setTimeout(load, 0); return () => clearTimeout(id); }, [load]);

  async function changeStatus(arena, action) {
    if (!window.confirm(`${action === 'suspender' ? 'Suspender' : 'Reativar'} ${arena.nome}?`)) return;
    try { const { data } = await api.post(`/saas/arenas/${arena.id}/${action}/`); setToast({ mensagem: data.detail, tipo: 'sucesso' }); await load(); }
    catch { setToast({ mensagem: 'Erro ao alterar a unidade.', tipo: 'erro' }); }
  }

  async function confirmAccess(event) {
    event.preventDefault();
    setAccessing(true);
    try { await acessarArena(accessTarget.id, reason); setAccessTarget(null); setReason(''); navigate('/admin'); }
    catch (error) { setToast({ mensagem: error.response?.data?.detail || 'Não foi possível acessar a unidade.', tipo: 'erro' }); }
    finally { setAccessing(false); }
  }

  async function createUnit(event) {
    event.preventDefault(); setErrors({}); setSaving(true);
    try {
      const { data } = await api.post('/saas/arenas/', form);
      setCreateOpen(false); setForm(initialForm());
      setToast({ mensagem: `Unidade ${data.arena.nome} criada com administrador inicial.`, tipo: 'sucesso' });
      await load(); navigate(`/admin/saas/arenas/${data.arena.id}`);
    } catch (error) {
      setErrors(apiFieldErrors(error));
      setToast({
        mensagem: apiErrorMessage(error, 'Não foi possível criar a unidade. Verifique se a API está disponível.'),
        tipo: 'erro',
      });
    } finally { setSaving(false); }
  }

  const change = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const changeOperational = (field, value) => setForm((current) => ({ ...current, operational_settings: { ...current.operational_settings, [field]: value } }));
  const changeType = (value) => setForm((current) => ({ ...current, tipo_negocio: value, operational_settings: settingsFor(value) }));
  const changeName = (value) => setForm((current) => ({ ...current, nome: value, slug: current.slug || value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') }));

  return <div className="space-y-5">
    <header className="flex flex-wrap items-start justify-between gap-3"><div><p className="page-kicker">Superadmin SaaS</p><h1 className="page-title">Unidades contratantes</h1><p className="page-subtitle">Arenas e academias em um único painel operacional.</p>{contexto && <p className="mt-2 text-sm font-semibold text-slate-600">Contexto ativo: <span className="tenant-link">{contexto.arena.nome}</span></p>}</div><div className="flex flex-wrap gap-2">{contexto && <button type="button" onClick={sairDaArena} className="btn-secondary">Limpar contexto</button>}<button type="button" onClick={load} className="btn-secondary">Atualizar</button><button type="button" onClick={() => setCreateOpen(true)} className="btn-primary">Nova unidade</button></div></header>

    <div className="overflow-x-auto rounded-xl border border-gray-100 bg-white shadow-sm"><table className="w-full min-w-[900px]"><thead className="border-b bg-gray-50"><tr><Th>Unidade</Th><Th>Plano</Th><Th>Status</Th><Th>Uso</Th><Th className="text-right">Ações</Th></tr></thead><tbody className="divide-y divide-gray-100">{loading ? <RowMessage text="Carregando unidades…" /> : arenas.length === 0 ? <RowMessage text="Nenhuma unidade cadastrada." /> : arenas.map((arena) => {
      const selected = String(arena.id) === String(contexto?.arena?.id);
      return <tr key={arena.id} onClick={() => navigate(`/admin/saas/arenas/${arena.id}`)} className={`cursor-pointer hover:bg-gray-50 ${selected ? 'bg-[var(--arena-primary-soft)]' : ''}`}><td className="p-4"><p className="font-bold text-gray-900">{arena.nome}{selected && <span className="tenant-chip ml-2 rounded-full px-2 py-1 text-xs">em uso</span>}</p><p className="mt-1 flex items-center gap-2 text-xs text-gray-500"><span className="rounded-full bg-slate-100 px-2 py-0.5 font-bold">{arena.tipo_negocio === 'academia' ? 'Academia' : 'Arena'}</span>{arena.slug}</p></td><td className="p-4 text-sm">{arena.plano_contratado}</td><td className="p-4"><span className={`rounded-full px-2 py-1 text-xs font-bold ${arena.ativa ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{arena.status_assinatura}</span></td><td className="p-4 text-sm text-gray-600">{arena.total_alunos}/{arena.limite_alunos} {arena.terminologia?.pessoa_plural || 'alunos'} · {arena.total_quadras}/{arena.limite_quadras} {arena.terminologia?.espaco_plural || 'quadras'} · {arena.total_admins}/{arena.limite_admins} admins</td><td className="p-4"><div className="flex justify-end gap-2"><button type="button" onClick={(e) => { e.stopPropagation(); navigate(`/admin/saas/arenas/${arena.id}`); }} className="btn-secondary">Detalhes</button>{arena.ativa ? <><button type="button" onClick={(e) => { e.stopPropagation(); setAccessTarget(arena); setReason(''); }} className="btn-primary">Acessar</button><button type="button" onClick={(e) => { e.stopPropagation(); changeStatus(arena, 'suspender'); }} className="btn-danger-soft">Suspender</button></> : <button type="button" onClick={(e) => { e.stopPropagation(); changeStatus(arena, 'reativar'); }} className="btn-secondary text-emerald-700">Reativar</button>}</div></td></tr>;
    })}</tbody></table></div>

    <Modal aberto={Boolean(accessTarget)} onFechar={() => !accessing && setAccessTarget(null)} titulo="Acessar unidade"><form onSubmit={confirmAccess} className="space-y-4"><p className="text-sm text-slate-600">Você passará a operar <strong>{accessTarget?.nome}</strong>. Toda requisição cross-tenant será auditada.</p><Field label="Motivo (opcional)"><textarea autoFocus maxLength="240" value={reason} onChange={(e) => setReason(e.target.value)} className="input-field min-h-24" /></Field><Actions onCancel={() => setAccessTarget(null)} busy={accessing} submit="Confirmar acesso" /></form></Modal>

    <Modal aberto={createOpen} onFechar={() => !saving && setCreateOpen(false)} titulo="Cadastrar nova unidade" tamanho="xl"><form onSubmit={createUnit} className="space-y-6">
      <Section title="Identificação e contato"><div className="grid gap-4 md:grid-cols-2"><Select label="Tipo de negócio" value={form.tipo_negocio} onChange={changeType} options={[['arena', 'Arena esportiva'], ['academia', 'Academia']]} /><Input label="Nome" value={form.nome} onChange={changeName} error={errors.nome} required autoFocus /><Input label="Slug" value={form.slug} onChange={(v) => change('slug', v)} error={errors.slug} required /><Input label="Documento" value={form.documento} onChange={(v) => change('documento', v)} error={errors.documento} /><Input label="E-mail" type="email" value={form.email_contato} onChange={(v) => change('email_contato', v)} error={errors.email_contato} /><Input label="Telefone" value={form.telefone_contato} onChange={(v) => change('telefone_contato', v)} /><Input label="Endereço" value={form.endereco} onChange={(v) => change('endereco', v)} /></div></Section>
      <Section title="Módulos iniciais"><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['classes_enabled', 'Aulas'], ['open_access_enabled', 'Acesso livre'], ['reservations_enabled', 'Reservas'], ['store_enabled', 'Loja']].map(([field, label]) => <label key={field} className="flex items-center gap-3 rounded-xl border p-3 text-sm font-bold"><input type="checkbox" className="h-5 w-5" checked={form.operational_settings[field]} onChange={(e) => changeOperational(field, e.target.checked)} />{label}</label>)}</div>{form.operational_settings.open_access_enabled && <div className="mt-4 grid gap-4 sm:grid-cols-2"><Select label="Validação do acesso" value={form.operational_settings.open_access_validation} onChange={(v) => changeOperational('open_access_validation', v)} options={[['reception', 'Pela recepção'], ['automatic', 'Automática']]} /><Input label="Validade da solicitação (min)" type="number" min="1" max="60" value={form.operational_settings.open_access_pending_minutes} onChange={(v) => changeOperational('open_access_pending_minutes', Number(v))} error={errors.operational_settings} /></div>}</Section>
      <Section title="Plano e limites"><div className="grid gap-4 md:grid-cols-3"><Select label="Plano" value={form.plano_contratado} onChange={(v) => change('plano_contratado', v)} options={['starter', 'professional', 'enterprise']} /><Select label="Status" value={form.status_assinatura} onChange={(v) => change('status_assinatura', v)} options={['trial', 'ativa', 'suspensa', 'cancelada']} /><Input label="Limite de pessoas" type="number" min="1" value={form.limite_alunos} onChange={(v) => change('limite_alunos', Number(v))} error={errors.limite_alunos} /><Input label="Limite de espaços" type="number" min="1" value={form.limite_quadras} onChange={(v) => change('limite_quadras', Number(v))} error={errors.limite_quadras} /><Input label="Limite de admins" type="number" min="1" value={form.limite_admins} onChange={(v) => change('limite_admins', Number(v))} error={errors.limite_admins} /></div></Section>
      <Section title="Identidade visual"><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{['cor_primaria', 'cor_secundaria', 'cor_fundo', 'cor_texto'].map((field) => <ColorInput key={field} label={field.replace('cor_', 'Cor ')} value={form[field]} onChange={(v) => change(field, v)} error={errors[field]} />)}</div><div className="mt-4 rounded-xl p-4 font-bold" style={{ background: form.cor_fundo, color: form.cor_texto, borderLeft: `12px solid ${form.cor_primaria}` }}>Preview da unidade <span style={{ color: form.cor_secundaria }}>ArenaFlow</span></div></Section>
      <Section title="Administrador inicial"><div className="grid gap-4 md:grid-cols-2"><Input label="Nome" value={form.admin_nome} onChange={(v) => change('admin_nome', v)} error={errors.admin_nome} required /><Input label="Sobrenome" value={form.admin_sobrenome} onChange={(v) => change('admin_sobrenome', v)} /><Input label="E-mail" type="email" value={form.admin_email} onChange={(v) => change('admin_email', v)} error={errors.admin_email} required /><div /><Input label="Senha temporária" type="password" value={form.admin_senha} onChange={(v) => change('admin_senha', v)} error={errors.admin_senha} required /><Input label="Confirmar senha" type="password" value={form.admin_senha_confirm} onChange={(v) => change('admin_senha_confirm', v)} error={errors.admin_senha_confirm} required /></div></Section>
      {errors.non_field_errors && <p className="text-sm font-semibold text-red-600">{String(errors.non_field_errors)}</p>}<Actions onCancel={() => setCreateOpen(false)} busy={saving} submit="Criar unidade" />
    </form></Modal>
    {toast && <Toast {...toast} onClose={() => setToast(null)} />}
  </div>;
}

function Section({ title, children }) { return <section><h3 className="mb-3 text-lg font-bold text-slate-900">{title}</h3>{children}</section>; }
function Field({ label, error, children }) { return <label className="block"><span className="mb-1 block text-sm font-semibold text-slate-700">{label}</span>{children}{error && <span className="mt-1 block text-xs font-semibold text-red-600">{Array.isArray(error) ? error.join(' ') : String(error)}</span>}</label>; }
function Input({ label, value, onChange, error, ...props }) { return <Field label={label} error={error}><input {...props} value={value} onChange={(e) => onChange(e.target.value)} className="input-field" /></Field>; }
function Select({ label, value, onChange, options }) { return <Field label={label}><select value={value} onChange={(e) => onChange(e.target.value)} className="input-field">{options.map((item) => { const [option, text] = Array.isArray(item) ? item : [item, item]; return <option value={option} key={option}>{text}</option>; })}</select></Field>; }
function ColorInput({ label, value, onChange, error }) { return <Field label={label} error={error}><div className="flex gap-2"><input type="color" value={value} onChange={(e) => onChange(e.target.value)} className="h-11 w-12 rounded border" /><input value={value} onChange={(e) => onChange(e.target.value)} pattern="#[0-9A-Fa-f]{6}" className="input-field" /></div></Field>; }
function Actions({ onCancel, busy, submit }) { return <div className="flex justify-end gap-2 border-t pt-4"><button type="button" className="btn-secondary" onClick={onCancel}>Cancelar</button><button disabled={busy} className="btn-primary">{busy ? 'Processando…' : submit}</button></div>; }
function Th({ children, className = '' }) { return <th className={`p-4 text-left text-xs font-bold uppercase text-gray-600 ${className}`}>{children}</th>; }
function RowMessage({ text }) { return <tr><td colSpan="5" className="p-8 text-center text-gray-500">{text}</td></tr>; }
