import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/client';
import Toast from './Toast';

const STATUS = { pending: 'Pendente', confirmed: 'Dentro', rejected: 'Rejeitado', checked_out: 'Encerrado', expired: 'Expirado' };

export default function AccessQueue() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [settings, setSettings] = useState(null);
  const [members, setMembers] = useState([]);
  const [manual, setManual] = useState({ open: false, aluno: '', motivo: '' });
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const { data } = await api.get('/admin/access-visits/today/');
      const rows = Array.isArray(data) ? data : data.results || [];
      setItems(rows);
      setSelected((current) => current.filter((id) => rows.some((row) => row.public_id === id && row.status === 'pending')));
    } catch (error) {
      if (!silent) setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível atualizar a fila de acesso.' });
    } finally { if (!silent) setLoading(false); }
  }, []);

  useEffect(() => {
    const initial = setTimeout(load, 0);
    const polling = setInterval(() => load(true), 5000);
    api.get('/admin/access/settings/').then(({ data }) => setSettings(data)).catch(() => {});
    return () => { clearTimeout(initial); clearInterval(polling); };
  }, [load]);

  const visible = useMemo(() => items.filter((item) => !filter || item.status === filter), [items, filter]);

  async function act(item, action, payload = {}) {
    setBusy(true);
    try {
      const { data } = await api.post(`/admin/access-visits/${item.public_id}/${action}/`, payload);
      setItems((rows) => rows.map((row) => row.public_id === item.public_id ? data : row));
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível concluir a operação.' });
    } finally { setBusy(false); }
  }

  async function reject(item) {
    const motivo = window.prompt('Informe o motivo da rejeição:');
    if (!motivo?.trim()) return;
    await act(item, 'reject', { motivo });
  }

  async function bulkConfirm() {
    if (!selected.length) return;
    setBusy(true);
    try {
      const { data } = await api.post('/admin/access-visits/bulk-confirm/', { visits: selected });
      setToast({ tipo: data.errors?.length ? 'info' : 'sucesso', mensagem: `${data.confirmed.length} acesso(s) confirmado(s)${data.errors?.length ? `; ${data.errors.length} não confirmado(s)` : ''}.` });
      setSelected([]);
      await load(true);
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Falha na confirmação em lote.' });
    } finally { setBusy(false); }
  }

  async function saveSettings(event) {
    event.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.patch('/admin/access/settings/', settings);
      setSettings(data);
      setToast({ tipo: 'sucesso', mensagem: 'Política de acesso atualizada.' });
    } catch (error) {
      setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível salvar a política.' });
    } finally { setBusy(false); }
  }

  async function openManual() {
    try {
      const { data } = await api.get('/admin/alunos/', { params: { status: 'ativos' } });
      setMembers(Array.isArray(data) ? data : data.results || []);
      setManual({ open: true, aluno: '', motivo: '' });
    } catch { setToast({ tipo: 'erro', mensagem: 'Não foi possível carregar os membros.' }); }
  }

  async function submitManual(event) {
    event.preventDefault();
    setBusy(true);
    try {
      await api.post('/admin/access-visits/manual/', manual);
      setManual({ open: false, aluno: '', motivo: '' });
      setToast({ tipo: 'sucesso', mensagem: 'Entrada manual registrada e auditada.' });
      await load(true);
    } catch (error) { setToast({ tipo: 'erro', mensagem: error.response?.data?.detail || 'Não foi possível registrar a entrada.' }); }
    finally { setBusy(false); }
  }

  return <>
    {settings && <form onSubmit={saveSettings} className="app-surface mb-5 grid gap-3 p-4 sm:grid-cols-3 sm:items-end">
      <label className="text-sm font-bold text-slate-700">Validação<select className="input-field mt-1" value={settings.open_access_validation} onChange={(e) => setSettings({ ...settings, open_access_validation: e.target.value })}><option value="reception">Pela recepção</option><option value="automatic">Automática</option></select></label>
      <label className="text-sm font-bold text-slate-700">Solicitação válida por<input type="number" min="1" max="60" className="input-field mt-1" value={settings.open_access_pending_minutes} onChange={(e) => setSettings({ ...settings, open_access_pending_minutes: Number(e.target.value) })} /></label>
      <button className="btn-primary" disabled={busy}>Salvar política</button>
    </form>}
    <div className="app-surface mb-4 flex flex-wrap items-center gap-3 p-4"><select className="input-field max-w-xs" value={filter} onChange={(e) => setFilter(e.target.value)}><option value="">Todos os estados</option>{Object.entries(STATUS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><button type="button" className="btn-secondary ml-auto" onClick={openManual}>Entrada manual</button><button type="button" className="btn-primary" disabled={!selected.length || busy} onClick={bulkConfirm}>Confirmar selecionados ({selected.length})</button></div>
    {manual.open && <form onSubmit={submitManual} className="app-surface mb-4 grid gap-3 p-4 sm:grid-cols-3 sm:items-end"><label className="text-sm font-bold">Membro<select required className="input-field mt-1" value={manual.aluno} onChange={(e) => setManual({ ...manual, aluno: e.target.value })}><option value="">Selecione</option>{members.map((member) => <option value={member.id} key={member.id}>{member.nome_completo || member.username}</option>)}</select></label><label className="text-sm font-bold">Motivo<input required maxLength="300" className="input-field mt-1" value={manual.motivo} onChange={(e) => setManual({ ...manual, motivo: e.target.value })} /></label><div className="flex gap-2"><button type="button" className="btn-secondary" onClick={() => setManual({ ...manual, open: false })}>Cancelar</button><button className="btn-primary" disabled={busy}>Registrar</button></div></form>}
    {loading ? <Empty text="Carregando fila…" /> : visible.length === 0 ? <Empty text="Nenhum acesso encontrado para este filtro." /> : <div className="app-surface divide-y divide-slate-100 overflow-hidden">{visible.map((item) => <article key={item.public_id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center"><label className="flex min-w-0 flex-1 items-center gap-3"><input type="checkbox" className="h-5 w-5" disabled={item.status !== 'pending'} checked={selected.includes(item.public_id)} onChange={(e) => setSelected((current) => e.target.checked ? [...current, item.public_id] : current.filter((id) => id !== item.public_id))} />{item.aluno_foto ? <img src={item.aluno_foto} alt="" className="h-11 w-11 rounded-full object-cover" /> : <span className="grid h-11 w-11 place-items-center rounded-full bg-teal-50 font-black text-teal-800">{item.aluno_nome?.slice(0, 2).toUpperCase()}</span>}<span className="min-w-0"><strong className="block truncate text-slate-950">{item.aluno_nome}</strong><span className="text-xs text-slate-500">{item.plano_nome} · {formatTime(item.solicitado_em)} · {STATUS[item.status]}</span>{item.inadimplente_no_momento && <span className="block text-xs font-bold text-amber-700">Alerta financeiro</span>}</span></label><div className="flex gap-2">{item.status === 'pending' && <><button type="button" className="btn-danger-soft" disabled={busy} onClick={() => reject(item)}>Rejeitar</button><button type="button" className="btn-primary" disabled={busy} onClick={() => act(item, 'confirm')}>Confirmar</button></>}{item.status === 'confirmed' && <button type="button" className="btn-secondary" disabled={busy} onClick={() => act(item, 'checkout')}>Check-out</button>}</div></article>)}</div>}
    {toast && <Toast {...toast} onClose={() => setToast(null)} />}
  </>;
}

function Empty({ text }) { return <div className="app-surface p-10 text-center text-slate-500">{text}</div>; }
function formatTime(value) { return new Date(value).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }); }
