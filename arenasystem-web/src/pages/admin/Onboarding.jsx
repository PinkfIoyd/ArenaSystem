import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';

const STEPS = [
  ['identification', 'Identificação'], ['hours', 'Horários'], ['courts', 'Espaços'],
  ['modalities', 'Modalidades'], ['professors', 'Professores'], ['students', 'Pessoas'], ['review', 'Revisão'],
];
const WEEKDAYS = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo'];

function Onboarding() {
  const [data, setData] = useState(null);
  const [step, setStep] = useState('identification');
  const [form, setForm] = useState({});
  const [items, setItems] = useState([]);
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function load() {
    try {
      const response = await api.get('/onboarding/');
      setData(response.data);
      setStep(response.data.current_step || 'identification');
    } catch (err) { setError(err.response?.data?.detail || 'Nao foi possivel carregar o onboarding.'); }
  }
  useEffect(() => { const timer = setTimeout(() => { void load(); }, 0); return () => clearTimeout(timer); }, []);

  useEffect(() => {
    if (!data) return;
    const timer = setTimeout(() => {
      if (step === 'identification') setForm({ ...data.arena, operational_settings: data.operational_settings });
      if (step === 'hours') setItems(WEEKDAYS.map((_, weekday) => {
        const current = data.hours.find((item) => item.weekday === weekday);
        return current ? { ...current, opens_at: current.opens_at?.slice(0, 5), closes_at: current.closes_at?.slice(0, 5) } : { weekday, opens_at: '07:00', closes_at: '22:00', closed: false };
      }));
      if (step === 'courts') setItems(data.courts.length ? data.courts : [{ nome: '', tipo_espaco: data.tipo_negocio === 'academia' ? 'gym_floor' : 'court', tipo_areia: '', ativa: true }]);
      if (step === 'modalities') setItems(data.modalities.length ? data.modalities : [{ nome: '', cor: '#0F766E' }]);
      if (step === 'professors') setItems([{ email: '' }]);
    }, 0);
    return () => clearTimeout(timer);
  }, [data, step]);

  async function saveStep() {
    setBusy(true); setError('');
    try {
      const payload = step === 'identification' ? form : { items: items.filter((item) => step === 'hours' || item.nome || item.email) };
      const response = await api.post(`/onboarding/steps/${step}/`, payload);
      setData((previous) => ({ ...previous, ...response.data }));
      setStep(response.data.current_step);
    } catch (err) { setError(err.response?.data?.detail || 'Revise os dados da etapa.'); }
    finally { setBusy(false); }
  }

  async function runImport(commit = false) {
    if (!file) { setError('Selecione um arquivo CSV.'); return; }
    setBusy(true); setError('');
    const payload = new FormData(); payload.append('file', file); payload.append('dry_run', commit ? 'false' : 'true');
    try {
      const response = await api.post('/onboarding/import-students/', payload, { headers: { 'Content-Type': 'multipart/form-data' } });
      setReport(response.data);
      if (commit) await load();
    } catch (err) { setReport(err.response?.data); setError(err.response?.data?.detail || 'A importacao possui erros.'); }
    finally { setBusy(false); }
  }

  async function complete() {
    setBusy(true); setError('');
    try { await api.post('/onboarding/complete/'); navigate('/admin', { replace: true }); window.location.reload(); }
    catch (err) { setError(err.response?.data?.detail || 'Ainda existem etapas obrigatorias.'); }
    finally { setBusy(false); }
  }

  if (!data) return <div className="app-surface p-10 text-center">{error || 'Preparando configuracao...'}</div>;
  const currentIndex = STEPS.findIndex(([key]) => key === step);
  const terms = data.terminologia || { unidade_singular: 'arena', pessoa_plural: 'alunos', espaco_plural: 'quadras' };
  const labels = Object.fromEntries(STEPS.map(([key, label]) => [key, key === 'courts' ? capitalize(terms.espaco_plural) : key === 'students' ? capitalize(terms.pessoa_plural) : label]));
  return <div className="mx-auto max-w-5xl space-y-6"><header><p className="muted-label">Primeiros passos</p><h1 className="text-3xl font-bold">Configure sua {terms.unidade_singular}</h1><p className="mt-2 text-slate-600">Salve cada etapa e continue quando quiser.</p></header>
    <ol className="flex gap-2 overflow-x-auto pb-2">{STEPS.map(([key], index) => <li key={key}><button type="button" onClick={() => setStep(key)} className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-bold ${key === step ? 'bg-slate-950 text-white' : data.completed_steps.includes(key) ? 'bg-teal-100 text-teal-900' : 'bg-white text-slate-500'}`}>{index + 1}. {labels[key]}</button></li>)}</ol>
    {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{error}</div>}
    <section className="app-surface p-6">{step === 'identification' && <Identification form={form} setForm={setForm} />}{step === 'hours' && <Hours items={items} setItems={setItems} />}{step === 'courts' && <RepeatItems title={capitalize(terms.espaco_plural)} items={items} setItems={setItems} empty={{ nome: '', tipo_espaco: data.tipo_negocio === 'academia' ? 'gym_floor' : 'court', tipo_areia: '', ativa: true }} render={(item, update) => <div className="grid gap-3 sm:grid-cols-2"><Field label="Nome" value={item.nome} onChange={(value) => update('nome', value)} /><SelectField label="Tipo de espaço" value={item.tipo_espaco || 'court'} onChange={(value) => update('tipo_espaco', value)} options={SPACE_TYPES} />{item.tipo_espaco === 'court' && <Field label="Tipo de areia (opcional)" value={item.tipo_areia} onChange={(value) => update('tipo_areia', value)} />}</div>} />}{step === 'modalities' && <RepeatItems title="Modalidades" items={items} setItems={setItems} empty={{ nome: '', cor: '#0F766E' }} render={(item, update) => <div className="grid gap-3 sm:grid-cols-2"><Field label="Nome" value={item.nome} onChange={(value) => update('nome', value)} /><Field label="Cor" type="color" value={item.cor} onChange={(value) => update('cor', value)} /></div>} />}{step === 'professors' && <RepeatItems title="Convide professores" items={items} setItems={setItems} empty={{ email: '' }} render={(item, update) => <Field label="E-mail" type="email" value={item.email} onChange={(value) => update('email', value)} />} />}{step === 'students' && <StudentImport personPlural={terms.pessoa_plural} file={file} setFile={setFile} report={report} onValidate={() => runImport(false)} onCommit={() => runImport(true)} busy={busy} />}{step === 'review' && <Review data={data} />}
      {step !== 'students' && step !== 'review' && <div className="mt-6 flex justify-end"><button type="button" disabled={busy} onClick={saveStep} className="btn-primary">{busy ? 'Salvando...' : 'Salvar e continuar'}</button></div>}
      {step === 'students' && <div className="mt-5 flex justify-end"><button type="button" onClick={() => setStep('review')} className="btn-secondary">Fazer depois</button></div>}
      {step === 'review' && <div className="mt-6 flex justify-end"><button type="button" disabled={busy} onClick={complete} className="btn-primary">{busy ? 'Concluindo...' : 'Concluir configuracao'}</button></div>}
    </section><p className="text-center text-sm text-slate-500">Etapa {currentIndex + 1} de {STEPS.length}</p></div>;
}

function Identification({ form, setForm }) { const updateSetting = (field, value) => setForm({ ...form, operational_settings: { ...form.operational_settings, [field]: value } }); return <div><h2 className="text-xl font-bold">Identificação, marca e módulos</h2><div className="mt-5 grid gap-4 sm:grid-cols-2"><Field label="Nome" value={form.nome} onChange={(value) => setForm({ ...form, nome: value })} /><Field label="E-mail" type="email" value={form.email_contato} onChange={(value) => setForm({ ...form, email_contato: value })} /><Field label="Telefone" value={form.telefone_contato} onChange={(value) => setForm({ ...form, telefone_contato: value })} /><Field label="Endereço" value={form.endereco} onChange={(value) => setForm({ ...form, endereco: value })} /><Field label="Cor primária" type="color" value={form.cor_primaria} onChange={(value) => setForm({ ...form, cor_primaria: value })} /><Field label="Cor secundária" type="color" value={form.cor_secundaria} onChange={(value) => setForm({ ...form, cor_secundaria: value })} /></div><div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['classes_enabled', 'Aulas'], ['open_access_enabled', 'Acesso livre'], ['reservations_enabled', 'Reservas'], ['store_enabled', 'Loja']].map(([field, label]) => <label key={field} className="flex items-center gap-3 rounded-xl border p-3 text-sm font-bold"><input type="checkbox" className="h-5 w-5" checked={Boolean(form.operational_settings?.[field])} onChange={(e) => updateSetting(field, e.target.checked)} />{label}</label>)}</div></div>; }
function Hours({ items, setItems }) { return <div><h2 className="text-xl font-bold">Horarios de funcionamento</h2><div className="mt-5 space-y-3">{items.map((item, index) => <div key={item.weekday} className="grid items-center gap-3 rounded-lg border p-3 sm:grid-cols-[1fr_1fr_1fr_auto]"><strong>{WEEKDAYS[item.weekday]}</strong><input type="time" disabled={item.closed} value={item.opens_at || ''} onChange={(event) => updateList(setItems, index, 'opens_at', event.target.value)} className="input-field" /><input type="time" disabled={item.closed} value={item.closes_at || ''} onChange={(event) => updateList(setItems, index, 'closes_at', event.target.value)} className="input-field" /><label className="flex gap-2 text-sm"><input type="checkbox" checked={item.closed} onChange={(event) => updateList(setItems, index, 'closed', event.target.checked)} />Fechado</label></div>)}</div></div>; }
function RepeatItems({ title, items, setItems, empty, render }) { return <div><div className="flex justify-between"><h2 className="text-xl font-bold">{title}</h2><button type="button" onClick={() => setItems([...items, empty])} className="btn-secondary">Adicionar</button></div><div className="mt-5 space-y-3">{items.map((item, index) => <div key={index} className="rounded-lg border p-4">{render(item, (field, value) => updateList(setItems, index, field, value))}{items.length > 1 && <button type="button" onClick={() => setItems(items.filter((_, itemIndex) => itemIndex !== index))} className="mt-3 text-sm font-bold text-red-700">Remover</button>}</div>)}</div></div>; }
function StudentImport({ personPlural, file, setFile, report, onValidate, onCommit, busy }) { return <div><h2 className="text-xl font-bold">Importar {personPlural}</h2><p className="mt-2 text-slate-600">CSV UTF-8, até 5 MB e 5.000 linhas. Valide antes de confirmar.</p><a href={`${(import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '')}/onboarding/import-students/template/`} className="mt-3 inline-block font-bold text-teal-700">Baixar modelo</a><input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] || null)} className="mt-5 block w-full rounded-lg border p-3" /><div className="mt-4 flex gap-2"><button type="button" disabled={busy || !file} onClick={onValidate} className="btn-secondary">Validar arquivo</button>{report?.dry_run && report.rejected === 0 && <button type="button" disabled={busy} onClick={onCommit} className="btn-primary">Confirmar {report.valid} {personPlural}</button>}</div>{report && <div className="mt-5 rounded-lg bg-slate-50 p-4 text-sm"><p>Total: {report.total} · Válidos: {report.valid} · Rejeitados: {report.rejected}</p>{report.errors?.slice(0, 10).map((item) => <p key={`${item.line}-${item.email}`} className="mt-1 text-red-700">Linha {item.line}: {item.errors.join(', ')}</p>)}</div>}</div>; }
function Review({ data }) { return <div><h2 className="text-xl font-bold">Revise a configuracao</h2><div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">{Object.entries(data.summary).map(([key, value]) => <div key={key} className="rounded-lg bg-slate-50 p-4"><p className="text-sm capitalize text-slate-500">{key}</p><p className="text-2xl font-bold">{value}</p></div>)}</div><p className="mt-6 text-slate-600">Voce podera alterar essas informacoes depois no painel.</p></div>; }
function Field({ label, type = 'text', value = '', onChange }) { return <label className="block"><span className="mb-1 block text-sm font-bold text-slate-700">{label}</span><input type={type} value={value || ''} onChange={(event) => onChange(event.target.value)} className="input-field w-full" /></label>; }
function SelectField({ label, value, onChange, options }) { return <label className="block"><span className="mb-1 block text-sm font-bold text-slate-700">{label}</span><select className="input-field w-full" value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></label>; }
function updateList(setItems, index, field, value) { setItems((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item)); }
const SPACE_TYPES = [['court', 'Quadra'], ['gym_floor', 'Musculação'], ['martial_arts', 'Lutas'], ['spinning', 'Spinning'], ['pool', 'Piscina'], ['studio', 'Estúdio'], ['functional', 'Funcional'], ['other', 'Outro']];
function capitalize(value) { return value ? value.charAt(0).toUpperCase() + value.slice(1) : value; }
export default Onboarding;
