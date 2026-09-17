import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/client';
import Toast from './Toast';

const STATUS_LABELS = { pending: 'Pendente', confirmed: 'Confirmado', rejected: 'Rejeitado', expired: 'Expirado', absent: 'Ausente' };

export default function CheckinQueue({ showSettings = false }) {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState([]);
  const [filters, setFilters] = useState({ status: 'pending', turma: '', professor: '', hour: '' });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState(null);
  const [settings, setSettings] = useState(null);
  const [manual, setManual] = useState({ open: false, turmas: [], turma: '', students: [], aluno: '', reason: '' });

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.turma) params.turma = filters.turma;
      const { data } = await api.get('/admin/checkins/today/', { params });
      setItems(Array.isArray(data) ? data : data.results || []);
      setSelected((current) => current.filter((id) => (Array.isArray(data) ? data : data.results || []).some((item) => item.id === id && item.status === 'pending')));
    } catch (error) {
      if (!silent) setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível atualizar a fila.' });
    } finally { if (!silent) setLoading(false); }
  }, [filters.status, filters.turma]);

  useEffect(() => { const initial = setTimeout(load, 0); const poll = setInterval(() => load(true), 5000); return () => { clearTimeout(initial); clearInterval(poll); }; }, [load]);
  useEffect(() => { if (showSettings) api.get('/admin/checkins/settings/').then(({ data }) => setSettings(data)).catch(() => {}); }, [showSettings]);

  const options = useMemo(() => ({
    turmas: [...new Map(items.map((item) => [item.turma, item.turma_nome])).entries()],
    professores: [...new Set(items.map((item) => item.professor_nome))],
  }), [items]);
  const visible = items.filter((item) =>
    (!filters.hour || String(item.horario_previsto || '').startsWith(filters.hour))
    && (!filters.professor || item.professor_nome === filters.professor));
  const groups = Object.entries(visible.reduce((acc, item) => {
    const key = `${String(item.horario_previsto || '').slice(0, 5)} • ${item.turma_nome}`;
    (acc[key] ||= []).push(item); return acc;
  }, {}));

  async function confirmOne(id) {
    setBusy(true);
    try { const { data } = await api.post(`/admin/checkins/${id}/confirm/`); setItems((current) => current.map((item) => item.id === id ? data : item)); }
    catch (error) { setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível confirmar.' }); }
    finally { setBusy(false); }
  }
  async function rejectOne(id) {
    const reason = window.prompt('Informe o motivo da rejeição:');
    if (!reason?.trim()) return;
    setBusy(true);
    try { const { data } = await api.post(`/admin/checkins/${id}/reject/`, { reason }); setItems((current) => current.map((item) => item.id === id ? data : item)); }
    catch (error) { setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível rejeitar.' }); }
    finally { setBusy(false); }
  }
  async function confirmSelected() {
    if (!selected.length) return;
    setBusy(true);
    try {
      const { data } = await api.post('/admin/checkins/bulk-confirm/', { ids: selected });
      setToast({ tipo: 'sucesso', mensagem: `${data.confirmed} check-in(s) confirmado(s).` });
      setSelected([]); await load(true);
    } catch (error) { setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Falha na confirmação em lote.' }); }
    finally { setBusy(false); }
  }
  async function saveSettings(event) {
    event.preventDefault();
    try { const { data } = await api.patch('/admin/checkins/settings/', settings); setSettings(data); setToast({ tipo: 'sucesso', mensagem: 'Configuração salva.' }); }
    catch (error) { setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível salvar.' }); }
  }

  async function openManual() {
    try {
      const { data } = await api.get('/turmas/');
      setManual({ open: true, turmas: Array.isArray(data) ? data : data.results || [], turma: '', students: [], aluno: '', reason: '' });
    } catch { setToast({ tipo: 'erro', mensagem: 'Nao foi possivel carregar as turmas.' }); }
  }

  async function chooseManualClass(turma) {
    setManual((current) => ({ ...current, turma, aluno: '', students: [] }));
    if (!turma) return;
    try {
      const { data } = await api.get(`/turmas/${turma}/roster/`);
      setManual((current) => ({ ...current, students: data.students || [] }));
    } catch (error) { setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Nao foi possivel carregar os alunos.' }); }
  }

  async function submitManual(event) {
    event.preventDefault();
    if (!manual.turma || !manual.aluno || !manual.reason.trim()) return;
    setBusy(true);
    try {
      await api.post('/admin/checkins/manual/', { turma: manual.turma, aluno: manual.aluno, reason: manual.reason });
      setManual((current) => ({ ...current, open: false }));
      setToast({ tipo: 'sucesso', mensagem: 'Presenca manual registrada e auditada.' });
      await load(true);
    } catch (error) { setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Nao foi possivel registrar.' }); }
    finally { setBusy(false); }
  }

  async function correctOne(item) {
    const target = item.status === 'confirmed' ? 'absent' : 'confirmed';
    const reason = window.prompt(`Informe o motivo para corrigir como ${target === 'confirmed' ? 'presente' : 'ausente'}:`);
    if (!reason?.trim()) return;
    setBusy(true);
    try {
      const { data } = await api.post(`/admin/checkins/${item.id}/correct/`, { status: target, reason });
      setItems((current) => current.map((entry) => entry.id === item.id ? data : entry));
      setToast({ tipo: 'sucesso', mensagem: 'Presenca corrigida e auditada.' });
    } catch (error) { setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Nao foi possivel corrigir.' }); }
    finally { setBusy(false); }
  }

  return <>
    {showSettings && settings && <form onSubmit={saveSettings} className="app-surface mb-5 grid gap-3 p-4 sm:grid-cols-4 sm:items-end"><label className="text-sm font-bold text-slate-700">Minutos antes<input type="number" min="0" max="180" className="input-field mt-1" value={settings.checkin_minutes_before} onChange={(e) => setSettings({ ...settings, checkin_minutes_before: e.target.value })} /></label><label className="text-sm font-bold text-slate-700">Minutos depois<input type="number" min="0" max="180" className="input-field mt-1" value={settings.checkin_minutes_after} onChange={(e) => setSettings({ ...settings, checkin_minutes_after: e.target.value })} /></label><label className="text-sm font-bold text-slate-700">Inadimplência<select className="input-field mt-1" value={settings.delinquent_checkin_policy} onChange={(e) => setSettings({ ...settings, delinquent_checkin_policy: e.target.value })}><option value="allow_with_warning">Permitir com alerta</option><option value="block">Bloquear</option></select></label><button className="btn-primary" disabled={busy}>Salvar política</button></form>}
    <div className="app-surface mb-5 grid gap-3 p-4 sm:grid-cols-4"><select className="input-field" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}><option value="">Todos os estados</option>{Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select className="input-field" value={filters.turma} onChange={(e) => setFilters({ ...filters, turma: e.target.value })}><option value="">Todas as turmas</option>{options.turmas.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select><select className="input-field" value={filters.professor} onChange={(e) => setFilters({ ...filters, professor: e.target.value })}><option value="">Todos os professores</option>{options.professores.map((name) => <option key={name} value={name}>{name}</option>)}</select><input className="input-field" type="time" aria-label="Filtrar horário" value={filters.hour} onChange={(e) => setFilters({ ...filters, hour: e.target.value })} /></div>
    <div className="sticky top-20 z-20 mb-4 flex items-center justify-between gap-3 rounded-2xl bg-slate-950 p-3 text-white shadow-xl"><button type="button" onClick={openManual} className="rounded-xl border border-white/20 px-3 py-2 text-sm font-bold">Check-in manual</button><span className="hidden text-sm font-bold sm:block">{selected.length} selecionado(s)</span><button type="button" onClick={confirmSelected} disabled={!selected.length || busy} className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-black disabled:opacity-40">Confirmar selecionados</button></div>
    {manual.open && <form onSubmit={submitManual} className="app-surface mb-5 grid gap-3 p-4 sm:grid-cols-4 sm:items-end"><label className="text-sm font-bold text-slate-700">Turma<select className="input-field mt-1" value={manual.turma} onChange={(e) => chooseManualClass(e.target.value)} required><option value="">Selecione</option>{manual.turmas.map((turma) => <option key={turma.id} value={turma.id}>{turma.nome}</option>)}</select></label><label className="text-sm font-bold text-slate-700">Aluno<select className="input-field mt-1" value={manual.aluno} onChange={(e) => setManual({ ...manual, aluno: e.target.value })} required><option value="">Selecione</option>{manual.students.filter((student) => !student.checkin_id && student.active_enrollment).map((student) => <option key={student.id} value={student.id}>{student.name}</option>)}</select></label><label className="text-sm font-bold text-slate-700">Motivo<input className="input-field mt-1" maxLength="300" value={manual.reason} onChange={(e) => setManual({ ...manual, reason: e.target.value })} required /></label><div className="flex gap-2"><button type="button" className="btn-secondary" onClick={() => setManual({ ...manual, open: false })}>Cancelar</button><button className="btn-primary" disabled={busy}>Registrar</button></div></form>}
    {loading ? <Empty text="Carregando fila..." /> : groups.length === 0 ? <Empty text="Nenhum check-in encontrado para os filtros de hoje." /> : <div className="space-y-5">{groups.map(([group, entries]) => <section key={group} className="app-surface overflow-hidden"><header className="border-b border-slate-100 bg-slate-50 px-4 py-3"><h2 className="font-black text-slate-900">{group}</h2><p className="text-xs text-slate-500">Prof. {entries[0].professor_nome}</p></header><div className="divide-y divide-slate-100">{entries.map((item) => <article key={item.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center"><label className="flex min-w-0 flex-1 items-center gap-3"><input type="checkbox" className="h-5 w-5" disabled={item.status !== 'pending'} checked={selected.includes(item.id)} onChange={(e) => setSelected((current) => e.target.checked ? [...current, item.id] : current.filter((id) => id !== item.id))} />{item.aluno_foto ? <img src={item.aluno_foto} alt="" className="h-11 w-11 rounded-full object-cover" /> : <span className="grid h-11 w-11 rounded-full bg-teal-50 text-sm font-black text-teal-800 place-items-center">{item.aluno_nome?.slice(0, 2).toUpperCase()}</span>}<span className="min-w-0"><strong className="block truncate text-slate-950">{item.aluno_nome}</strong><span className="text-xs text-slate-500">Solicitado {item.solicitado_em ? new Date(item.solicitado_em).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : 'manualmente'} • {STATUS_LABELS[item.status]}</span>{item.inadimplente_no_momento && <span className="mt-1 block text-xs font-bold text-amber-700">Alerta financeiro</span>}</span></label>{item.status === 'pending' && <div className="flex gap-2"><button type="button" disabled={busy} onClick={() => rejectOne(item.id)} className="btn-danger-soft flex-1 px-3 py-2">Rejeitar</button><button type="button" disabled={busy} onClick={() => confirmOne(item.id)} className="btn-primary flex-1 px-3 py-2">Confirmar</button></div>}</article>)}</div></section>)}</div>}
    {visible.some((item) => item.status !== 'pending') && <section className="app-surface mt-5 p-4"><h2 className="font-black text-slate-950">Correcoes do dia</h2><p className="mt-1 text-sm text-slate-500">Toda alteracao exige motivo e fica registrada na auditoria.</p><div className="mt-3 flex flex-wrap gap-2">{visible.filter((item) => item.status !== 'pending').map((item) => <button type="button" key={item.id} disabled={busy} onClick={() => correctOne(item)} className="btn-secondary px-3 py-2">Corrigir {item.aluno_nome}</button>)}</div></section>}
    {toast && <Toast {...toast} onClose={() => setToast(null)} />}
  </>;
}

function Empty({ text }) { return <div className="app-surface p-10 text-center text-slate-500">{text}</div>; }
