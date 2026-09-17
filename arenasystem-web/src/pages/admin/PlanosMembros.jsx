import { useCallback, useEffect, useState } from 'react';
import api from '../../api/client';
import Modal from '../../components/Modal';
import Toast from '../../components/Toast';
import useTerminology from '../../hooks/useTerminology';

const DAYS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'];
const emptyPlan = () => ({ nome: '', valor: '', frequencia_semanal: 0, tipo_acesso: 'classes_only', limite_acessos_dia: '', limite_acessos_semana: '', limite_acessos_mes: '', descricao: '', ativo: true, janelas_acesso: [] });

export default function PlanosMembros() {
  const { terms } = useTerminology();
  const [plans, setPlans] = useState([]);
  const [editing, setEditing] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(emptyPlan);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    try { const { data } = await api.get('/admin/planos/'); setPlans(Array.isArray(data) ? data : data.results || []); }
    catch { setToast({ tipo: 'erro', mensagem: 'Não foi possível carregar os planos.' }); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const timer = setTimeout(load, 0); return () => clearTimeout(timer); }, [load]);

  function open(plan = null) {
    setModalOpen(true);
    setEditing(plan);
    setErrors({});
    setForm(plan ? { ...plan, limite_acessos_dia: plan.limite_acessos_dia ?? '', limite_acessos_semana: plan.limite_acessos_semana ?? '', limite_acessos_mes: plan.limite_acessos_mes ?? '', janelas_acesso: plan.janelas_acesso || [] } : emptyPlan());
  }

  function change(field, value) { setForm((current) => ({ ...current, [field]: value })); }
  function addWindow() { change('janelas_acesso', [...form.janelas_acesso, { weekday: 0, starts_at: '06:00', ends_at: '22:00' }]); }
  function updateWindow(index, field, value) { change('janelas_acesso', form.janelas_acesso.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item)); }

  async function submit(event) {
    event.preventDefault(); setBusy(true); setErrors({});
    const payload = { ...form, valor: String(form.valor).replace(',', '.'), frequencia_semanal: Number(form.frequencia_semanal || 0), ...Object.fromEntries(['limite_acessos_dia', 'limite_acessos_semana', 'limite_acessos_mes'].map((field) => [field, form[field] === '' ? null : Number(form[field])])) };
    try {
      if (editing) await api.patch(`/admin/planos/${editing.id}/`, payload); else await api.post('/admin/planos/', payload);
      setModalOpen(false); setEditing(null); setForm(emptyPlan()); setToast({ tipo: 'sucesso', mensagem: 'Plano salvo com sucesso.' }); await load();
    } catch (error) { setErrors(error.response?.data || {}); }
    finally { setBusy(false); }
  }

  return <div><header className="flex flex-wrap items-start justify-between gap-3"><div><p className="page-kicker">Cadastros</p><h1 className="page-title">Planos dos {terms.pessoa_plural}</h1><p className="page-subtitle">Defina aulas, acesso livre, horários e limites de entrada.</p></div><button type="button" className="btn-primary" onClick={() => open()}>Novo plano</button></header>
    <div className="mt-6 grid gap-4 lg:grid-cols-2">{loading ? <Empty text="Carregando planos…" /> : plans.length === 0 ? <Empty text="Nenhum plano cadastrado." /> : plans.map((plan) => <article key={plan.id} className="app-surface p-5"><div className="flex items-start justify-between gap-3"><div><span className="rounded-full bg-teal-50 px-2.5 py-1 text-[10px] font-black uppercase text-teal-800">{accessLabel(plan.tipo_acesso)}</span><h2 className="mt-3 text-xl font-black text-slate-950">{plan.nome}</h2><p className="mt-1 text-sm text-slate-500">R$ {Number(plan.valor).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p></div><button type="button" className="btn-secondary" onClick={() => open(plan)}>Editar</button></div><div className="mt-4 grid grid-cols-3 gap-2 text-center">{[['Dia', plan.limite_acessos_dia], ['Semana', plan.limite_acessos_semana], ['Mês', plan.limite_acessos_mes]].map(([label, value]) => <div key={label} className="rounded-xl bg-slate-50 p-3"><p className="text-[10px] font-bold uppercase text-slate-400">{label}</p><strong>{value ?? 'Livre'}</strong></div>)}</div><p className="mt-4 text-xs text-slate-500">{plan.janelas_acesso?.length || 0} faixa(s) de acesso configurada(s)</p></article>)}</div>

    <Modal aberto={modalOpen} onFechar={() => { if (!busy) { setModalOpen(false); setEditing(null); setForm(emptyPlan()); } }} titulo={editing ? 'Editar plano' : 'Novo plano'} tamanho="xl"><form onSubmit={submit} className="space-y-5"><div className="grid gap-4 sm:grid-cols-2"><Field label="Nome" error={errors.nome}><input autoFocus required className="input-field" value={form.nome} onChange={(e) => change('nome', e.target.value)} /></Field><Field label="Valor mensal" error={errors.valor}><input required inputMode="decimal" className="input-field" value={form.valor} onChange={(e) => change('valor', e.target.value)} /></Field><Field label="Tipo de acesso" error={errors.tipo_acesso}><select className="input-field" value={form.tipo_acesso} onChange={(e) => change('tipo_acesso', e.target.value)}><option value="classes_only">Somente aulas</option><option value="open_access">Somente acesso livre</option><option value="hybrid">Acesso livre + aulas</option></select></Field><Field label="Aulas por semana"><input type="number" min="0" className="input-field" value={form.frequencia_semanal} onChange={(e) => change('frequencia_semanal', e.target.value)} /></Field></div>
      {form.tipo_acesso !== 'classes_only' && <><div className="grid gap-4 sm:grid-cols-3">{[['limite_acessos_dia', 'Limite diário'], ['limite_acessos_semana', 'Limite semanal'], ['limite_acessos_mes', 'Limite mensal']].map(([field, label]) => <Field key={field} label={label} error={errors[field]}><input type="number" min="1" placeholder="Sem limite" className="input-field" value={form[field]} onChange={(e) => change(field, e.target.value)} /></Field>)}</div><section><div className="flex items-center justify-between"><div><h3 className="font-black text-slate-950">Faixas de acesso</h3><p className="text-xs text-slate-500">Faixas não podem atravessar a meia-noite.</p></div><button type="button" className="btn-secondary" onClick={addWindow}>Adicionar faixa</button></div>{errors.janelas_acesso && <p className="mt-2 text-sm font-bold text-red-600">{String(errors.janelas_acesso)}</p>}<div className="mt-3 space-y-3">{form.janelas_acesso.map((window, index) => <div className="grid gap-3 rounded-xl border p-3 sm:grid-cols-[1fr_1fr_1fr_auto]" key={`${index}-${window.weekday}`}><select className="input-field" value={window.weekday} onChange={(e) => updateWindow(index, 'weekday', Number(e.target.value))}>{DAYS.map((day, dayIndex) => <option value={dayIndex} key={day}>{day}</option>)}</select><input type="time" className="input-field" value={window.starts_at?.slice(0, 5)} onChange={(e) => updateWindow(index, 'starts_at', e.target.value)} /><input type="time" className="input-field" value={window.ends_at?.slice(0, 5)} onChange={(e) => updateWindow(index, 'ends_at', e.target.value)} /><button type="button" className="text-sm font-bold text-red-700" onClick={() => change('janelas_acesso', form.janelas_acesso.filter((_, itemIndex) => itemIndex !== index))}>Remover</button></div>)}</div></section></>}
      <Field label="Descrição"><textarea className="input-field min-h-24" value={form.descricao} onChange={(e) => change('descricao', e.target.value)} /></Field><label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={form.ativo} onChange={(e) => change('ativo', e.target.checked)} />Plano ativo</label>{errors.non_field_errors && <p className="text-sm font-bold text-red-600">{String(errors.non_field_errors)}</p>}<div className="flex justify-end gap-2 border-t pt-4"><button type="button" className="btn-secondary" onClick={() => { setModalOpen(false); setEditing(null); setForm(emptyPlan()); }}>Cancelar</button><button className="btn-primary" disabled={busy}>{busy ? 'Salvando…' : 'Salvar plano'}</button></div></form></Modal>
    {toast && <Toast {...toast} onClose={() => setToast(null)} />}
  </div>;
}

function Field({ label, error, children }) { return <label className="block"><span className="mb-1 block text-sm font-bold text-slate-700">{label}</span>{children}{error && <span className="mt-1 block text-xs font-bold text-red-600">{Array.isArray(error) ? error.join(' ') : String(error)}</span>}</label>; }
function Empty({ text }) { return <div className="app-surface col-span-full p-10 text-center text-slate-500">{text}</div>; }
function accessLabel(value) { return { classes_only: 'Aulas', open_access: 'Acesso livre', hybrid: 'Híbrido' }[value] || value; }
