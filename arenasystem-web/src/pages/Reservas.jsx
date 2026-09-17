import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';
import Toast from '../components/Toast';
import Icon from '../components/Icon';
import { formatarData, formatarMoeda } from '../utils/format';

function Reservas() {
  const [quadras, setQuadras] = useState([]);
  const [reservas, setReservas] = useState([]);
  const [grade, setGrade] = useState({ horarios: [], quadras: [], reservas: [], bloqueios: [] });
  const [dataGrade, setDataGrade] = useState(new Date().toISOString().slice(0, 10));
  const [toast, setToast] = useState(null);
  const [form, setForm] = useState({ quadra: '', data: '', hora_inicio: '', hora_fim: '', valor: '0' });

  const carregar = useCallback(async () => {
    const [rQuadras, rReservas, rGrade] = await Promise.all([
      api.get('/quadras/'),
      api.get('/reservas-quadra/?minhas=1'),
      api.get(`/reservas-quadra/grade/?data=${dataGrade}`),
    ]);
    setQuadras(rQuadras.data.results || rQuadras.data || []);
    setReservas(rReservas.data.results || rReservas.data || []);
    setGrade(rGrade.data);
  }, [dataGrade]);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const solicitar = async (e) => {
    e.preventDefault();
    try {
      await api.post('/reservas-quadra/?minhas=1', form);
      setForm({ quadra: '', data: '', hora_inicio: '', hora_fim: '', valor: '0' });
      setToast({ tipo: 'sucesso', mensagem: 'Reserva solicitada. Aguarde confirmacao da arena.' });
      await carregar();
    } catch (err) {
      setToast({ tipo: 'erro', mensagem: err.response?.data?.detail || 'Nao foi possivel solicitar a reserva.' });
    }
  };

  const cancelar = async (reserva) => {
    await api.post(`/reservas-quadra/${reserva.id}/cancelar/`);
    setToast({ tipo: 'sucesso', mensagem: 'Reserva cancelada.' });
    await carregar();
  };

  return (
    <Layout>
      <div className="mb-6">
        <p className="page-kicker">Quadras avulsas</p>
        <h2 className="page-title">Reservas</h2>
        <p className="page-subtitle">Solicite horarios livres e acompanhe suas reservas.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[360px_1fr]">
        <form onSubmit={solicitar} className="app-surface p-5">
          <h3 className="mb-4 flex items-center gap-2 font-bold text-slate-950">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-cyan-50 text-teal-800">
              <Icon name="court" className="h-5 w-5" />
            </span>
            Nova reserva
          </h3>
          <div className="space-y-3">
            <select className="field-control" value={form.quadra} onChange={(e) => setForm({ ...form, quadra: e.target.value })} required>
              <option value="">Selecione a quadra</option>
              {quadras.map((quadra) => <option key={quadra.id} value={quadra.id}>{quadra.nome}</option>)}
            </select>
            <input type="date" className="field-control" value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value })} required />
            <div className="grid grid-cols-2 gap-2">
              <input type="time" className="field-control" value={form.hora_inicio} onChange={(e) => setForm({ ...form, hora_inicio: e.target.value })} required />
              <input type="time" className="field-control" value={form.hora_fim} onChange={(e) => setForm({ ...form, hora_fim: e.target.value })} required />
            </div>
            <button className="btn-primary w-full">
              Solicitar reserva
            </button>
          </div>
        </form>

        <section className="app-surface p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-bold text-slate-950">Minhas reservas</h3>
            <span className="text-sm text-slate-500">{reservas.length} registro(s)</span>
          </div>
          <div className="space-y-3">
            {reservas.length === 0 && <p className="rounded-lg bg-slate-50 p-6 text-center text-slate-500">Voce ainda nao tem reservas.</p>}
            {reservas.map((reserva) => (
              <div key={reserva.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 p-4">
                <div>
                  <p className="font-bold text-slate-950">{reserva.quadra_nome}</p>
                  <p className="text-sm text-slate-600">{formatarData(reserva.data)} das {reserva.hora_inicio?.slice(0, 5)} as {reserva.hora_fim?.slice(0, 5)}</p>
                  <p className="mt-1 text-sm font-semibold text-emerald-700">{formatarMoeda(reserva.valor)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={reserva.status} />
                  {reserva.status !== 'cancelada' && (
                    <button onClick={() => cancelar(reserva)} className="btn-danger-soft px-3 py-1.5">
                      Cancelar
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="app-surface mt-6 p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-bold text-slate-950">Grade do dia</h3>
            <p className="text-sm text-slate-500">Horarios ocupados aparecem bloqueados automaticamente.</p>
          </div>
          <input type="date" className="field-control max-w-[180px]" value={dataGrade} onChange={(e) => setDataGrade(e.target.value)} />
        </div>
        <GradeReservas grade={grade} />
      </section>

      {toast && <Toast mensagem={toast.mensagem} tipo={toast.tipo} onClose={() => setToast(null)} />}
    </Layout>
  );
}

function StatusBadge({ status }) {
  const classe = status === 'confirmada'
    ? 'bg-emerald-50 text-emerald-700'
    : status === 'cancelada'
      ? 'bg-red-50 text-red-700'
      : 'bg-cyan-50 text-cyan-700';
  return <span className={`rounded-full px-3 py-1 text-xs font-bold ${classe}`}>{status}</span>;
}

function GradeReservas({ grade }) {
  const statusCelula = (quadra, hora) => {
    const inicio = `${hora}:00`;
    const fim = `${String(Number(hora.slice(0, 2)) + 1).padStart(2, '0')}:00`;
    const reserva = grade.reservas.find((item) => item.quadra === quadra.id && item.status !== 'cancelada' && item.hora_inicio < fim && item.hora_fim > inicio);
    if (reserva) return { texto: reserva.cliente_nome || 'Reservado', classe: 'border-emerald-200 bg-emerald-50 text-emerald-800' };
    const bloqueio = grade.bloqueios.find((item) => item.quadra === quadra.id && item.hora_inicio < fim && item.hora_fim > inicio);
    if (bloqueio) return { texto: bloqueio.motivo || 'Bloqueado', classe: 'border-red-200 bg-red-50 text-red-800' };
    return { texto: 'Livre', classe: 'border-slate-100 bg-slate-50 text-slate-400' };
  };

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[720px]">
        <div className="grid" style={{ gridTemplateColumns: `88px repeat(${grade.quadras.length || 1}, minmax(150px, 1fr))` }}>
          <div className="border-b border-slate-200 p-2 text-xs font-bold uppercase text-slate-400">Horario</div>
          {grade.quadras.map((quadra) => <div key={quadra.id} className="border-b border-slate-200 p-2 text-sm font-bold text-slate-800">{quadra.nome}</div>)}
          {grade.horarios.map((hora) => (
            <div key={hora} className="contents">
              <div className="border-b border-slate-100 p-2 text-sm font-semibold text-slate-500">{hora}</div>
              {grade.quadras.map((quadra) => {
                const status = statusCelula(quadra, hora.slice(0, 5));
                return <div key={`${quadra.id}-${hora}`} className={`m-1 rounded-lg border p-2 text-xs font-semibold ${status.classe}`}>{status.texto}</div>;
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Reservas;
