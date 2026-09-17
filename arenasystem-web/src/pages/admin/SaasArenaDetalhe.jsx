import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api from '../../api/client';
import Modal from '../../components/Modal';
import Toast from '../../components/Toast';
import { useArenaContext } from '../../contexts/arenaContextStore';

const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

function SaasArenaDetalhe() {
  const { arenaId } = useParams();
  const navigate = useNavigate();
  const { acessarArena } = useArenaContext();
  const [resumo, setResumo] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [modalAcesso, setModalAcesso] = useState(false);
  const [motivo, setMotivo] = useState('');
  const [acessando, setAcessando] = useState(false);
  const [toast, setToast] = useState(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro('');
    try {
      const { data } = await api.get(`/saas/arenas/${arenaId}/resumo/`);
      setResumo(data);
    } catch (error) {
      setErro(error.response?.data?.detail || 'Nao foi possivel carregar o resumo da arena.');
    } finally {
      setCarregando(false);
    }
  }, [arenaId]);

  useEffect(() => { const id = setTimeout(carregar, 0); return () => clearTimeout(id); }, [carregar]);

  async function confirmarAcesso(event) {
    event.preventDefault();
    setAcessando(true);
    try {
      await acessarArena(arenaId, motivo);
      navigate('/admin');
    } catch (error) {
      setToast({ mensagem: error.response?.data?.detail || 'Nao foi possivel acessar a arena.', tipo: 'erro' });
    } finally {
      setAcessando(false);
    }
  }

  if (carregando) return <Estado titulo="Carregando visao SaaS..." />;
  if (erro) return <Estado titulo={erro}><button type="button" onClick={carregar} className="btn-primary mt-4">Tentar novamente</button></Estado>;
  if (!resumo) return null;

  const { arena, financeiro, alunos, inadimplencia, reservas, estoque, assinatura, admins, periodos } = resumo;
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div><Link to="/admin/saas/arenas" className="text-sm font-bold text-teal-700">← Voltar para arenas</Link><p className="page-kicker mt-3">Visao SaaS</p><h2 className="text-3xl font-bold text-slate-950">{arena.nome}</h2><p className="text-sm text-slate-500">{arena.slug}{arena.dominio ? ` · ${arena.dominio}` : ''}</p></div>
        <button type="button" disabled={!assinatura.ativa || ['suspensa', 'cancelada'].includes(assinatura.status)} onClick={() => setModalAcesso(true)} className="btn-primary disabled:cursor-not-allowed disabled:opacity-50">Acessar arena</button>
      </div>

      {!assinatura.ativa && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">Esta arena pode ser consultada, mas nao usada como contexto operacional enquanto estiver inativa.</div>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card title="Receita prevista" value={moeda.format(Number(financeiro.receita_prevista))} detail={`${formatDate(periodos.financeiro.inicio)} a ${formatDate(periodos.financeiro.fim)}`} />
        <Card title="Receita recebida" value={moeda.format(Number(financeiro.receita_recebida))} detail="Mensalidades e vendas no periodo" tone="success" />
        <Card title="Valores vencidos" value={moeda.format(Number(financeiro.valores_vencidos))} detail={`${inadimplencia.quantidade} mensalidades`} tone="danger" />
        <Card title="Contas a pagar" value={moeda.format(Number(financeiro.contas_pagar_abertas))} detail="Abertas ou vencidas" />
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card title="Alunos ativos" value={`${alunos.ativos}/${alunos.limite}`} detail="Matriculas ativas" />
        <Card title="Inadimplencia" value={`${inadimplencia.taxa_percentual}%`} detail={moeda.format(Number(inadimplencia.valor))} tone="danger" />
        <Card title="Reservas" value={reservas.proximos_30_dias} detail={`${reservas.hoje} hoje · proximos 30 dias`} />
        <Card title="Estoque" value={estoque.produtos_ativos} detail={`${estoque.estoque_baixo} baixos · ${estoque.estoque_zerado} zerados`} />
      </section>

      <div className="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
        <section className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><h3 className="text-lg font-bold text-slate-900">Assinatura</h3><dl className="mt-4 space-y-3 text-sm"><Row label="Status" value={assinatura.status} /><Row label="Plano" value={assinatura.plano} /><Row label="Alunos" value={assinatura.limites.alunos} /><Row label="Quadras" value={assinatura.limites.quadras} /><Row label="Administradores" value={assinatura.limites.admins} /></dl></section>
        <section className="overflow-hidden rounded-xl border border-slate-100 bg-white shadow-sm"><div className="border-b p-5"><h3 className="text-lg font-bold text-slate-900">Administradores</h3></div>{admins.length === 0 ? <p className="p-6 text-sm text-slate-500">Nenhum administrador cadastrado.</p> : <div className="divide-y">{admins.map((admin) => <div key={admin.id} className="flex items-center justify-between gap-3 p-4"><div><p className="font-bold text-slate-900">{admin.nome}</p><p className="text-sm text-slate-500">{admin.email || 'Sem e-mail'} · {admin.papel}</p></div><span className={`rounded-full px-2 py-1 text-xs font-bold ${admin.ativo ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{admin.ativo ? 'Ativo' : 'Inativo'}</span></div>)}</div>}</section>
      </div>

      <Modal aberto={modalAcesso} onFechar={() => !acessando && setModalAcesso(false)} titulo="Confirmar acesso">
        <form onSubmit={confirmarAcesso} className="space-y-4"><p className="text-sm text-slate-600">Cada acesso aos dados de <strong>{arena.nome}</strong> sera auditado.</p><label className="block"><span className="mb-1 block text-sm font-semibold">Motivo (opcional)</span><textarea autoFocus maxLength="240" value={motivo} onChange={(e) => setMotivo(e.target.value)} className="input-field min-h-24" /></label><div className="flex justify-end gap-2"><button type="button" className="btn-secondary" onClick={() => setModalAcesso(false)}>Cancelar</button><button disabled={acessando} className="btn-primary">{acessando ? 'Acessando...' : 'Acessar arena'}</button></div></form>
      </Modal>
      {toast && <Toast mensagem={toast.mensagem} tipo={toast.tipo} onClose={() => setToast(null)} />}
    </div>
  );
}

function Card({ title, value, detail, tone = 'default' }) { const tones = { default: 'text-slate-950', success: 'text-emerald-700', danger: 'text-red-700' }; return <div className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">{title}</p><p className={`mt-2 text-2xl font-bold ${tones[tone]}`}>{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></div>; }
function Row({ label, value }) { return <div className="flex justify-between gap-4"><dt className="text-slate-500">{label}</dt><dd className="font-bold text-slate-900">{value}</dd></div>; }
function Estado({ titulo, children }) { return <div className="rounded-xl border border-slate-100 bg-white p-10 text-center text-slate-600 shadow-sm"><p className="font-semibold">{titulo}</p>{children}</div>; }
function formatDate(value) { if (!value) return '-'; return new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)); }

export default SaasArenaDetalhe;
