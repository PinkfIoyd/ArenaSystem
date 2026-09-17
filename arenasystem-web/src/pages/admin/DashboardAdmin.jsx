import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import api from '../../api/client';
import KpiCard from '../../components/KpiCard';
import GraficoCard from '../../components/GraficoCard';
import Icon from '../../components/Icon';
import { formatarMoeda } from '../../utils/format';
import useTerminology from '../../hooks/useTerminology';

const CORES_PIE = ['#22c55e', '#06b6d4', '#ef4444', '#64748b'];

function DashboardAdmin() {
  const { terms, features } = useTerminology();
  const [metricas, setMetricas] = useState(null);
  const [receitaMensal, setReceitaMensal] = useState({ mensalidades: [], loja: [] });
  const [ranking, setRanking] = useState([]);
  const [statusMens, setStatusMens] = useState([]);
  const [ocupacaoQuadras, setOcupacaoQuadras] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState(null);

  const carregarTudo = useCallback(async () => {
    try {
      setErro('');
      const [respMetricas, respReceita, respRanking, respStatus, respOcupacao] = await Promise.all([
        api.get('/dashboard/metricas/'),
        api.get('/dashboard/receita-mensal/'),
        api.get('/dashboard/ranking-frequencia/'),
        api.get('/dashboard/status-mensalidades/'),
        api.get('/dashboard/ocupacao-quadras/'),
      ]);

      setMetricas(respMetricas.data);
      setReceitaMensal(respReceita.data);
      setRanking(respRanking.data || []);
      setStatusMens(respStatus.data || []);
      setOcupacaoQuadras(respOcupacao.data || []);
      setUltimaAtualizacao(new Date());
    } catch (err) {
      console.error('Erro ao carregar dashboard:', err);
      setErro('Nao foi possivel carregar os indicadores agora.');
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    const id = setTimeout(carregarTudo, 0);
    const interval = setInterval(carregarTudo, 30000);
    const aoVoltarAba = () => {
      if (!document.hidden) void carregarTudo();
    };
    document.addEventListener('visibilitychange', aoVoltarAba);

    return () => {
      clearTimeout(id);
      clearInterval(interval);
      document.removeEventListener('visibilitychange', aoVoltarAba);
    };
  }, [carregarTudo]);

  const dadosReceita = useMemo(() => {
    const map = new Map();
    receitaMensal.mensalidades?.forEach((m) => {
      map.set(m.mes, { mes: m.mes, mensalidades: m.total, loja: 0 });
    });
    receitaMensal.loja?.forEach((l) => {
      if (map.has(l.mes)) {
        map.get(l.mes).loja = l.total;
      } else {
        map.set(l.mes, { mes: l.mes, mensalidades: 0, loja: l.total });
      }
    });
    return Array.from(map.values());
  }, [receitaMensal]);

  const dadosStatus = statusMens.map((s) => ({
    name: s.status === 'pago' ? 'Pago' : s.status === 'pendente' ? 'Pendente' : s.status === 'atrasado' ? 'Atrasado' : 'Cancelado',
    value: s.total,
  }));

  const statusPorNome = Object.fromEntries(statusMens.map((s) => [s.status, s.total]));

  if (carregando) {
    return (
      <div className="app-surface py-14 text-center">
        <div className="admin-accent-icon mx-auto mb-3 grid h-12 w-12 place-items-center rounded-lg">
          <Icon name="queue" className="h-6 w-6" />
        </div>
        <p className="font-semibold text-slate-600">Carregando visao geral...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="page-kicker">Painel administrativo</p>
          <h2 className="page-title">Visao Geral</h2>
          <p className="page-subtitle">
            Indicadores financeiros, operacionais e de atendimento desta {terms.unidade_singular}.
            {ultimaAtualizacao && (
              <span className="ml-2 text-slate-400">
                Atualizado as {ultimaAtualizacao.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </p>
        </div>
        <button onClick={carregarTudo} className="btn-secondary self-start">
          <Icon name="refresh" className="h-4 w-4" />
          Atualizar
        </button>
      </div>

      {erro && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">
          {erro}
        </div>
      )}

      <section className="mb-6 grid grid-cols-1 gap-4 xl:grid-cols-[1.4fr_1fr]">
        <div className="admin-brand-panel rounded-lg border bg-slate-950 p-5 text-white shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--admin-accent)]">Saúde do negócio</p>
          <h3 className="mt-2 text-2xl font-bold">Controle central da operacao</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-200">
            Acompanhe receita, inadimplência, {terms.pessoa_plural} ativos, check-ins{features.store ? ', estoque' : ''} e {terms.espaco_plural} em uma leitura única para tomada de decisão.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 xl:grid-cols-1">
          <AlertaOperacao
            titulo="Mensalidades atrasadas"
            texto={`${statusPorNome.atrasado || 0} cobranca(s) exigem acompanhamento.`}
            to="/admin/mensalidades"
            nivel={(statusPorNome.atrasado || 0) > 0 ? 'alto' : 'ok'}
          />
          {features.classes && <AlertaOperacao
            titulo="Solicitações e fila"
            texto="Revise matrículas, cancelamentos e lista de espera."
            to="/admin/solicitacoes"
            nivel="medio"
          />}
          <AlertaOperacao
            titulo={capitalize(terms.espaco_plural)}
            texto={`${ocupacaoQuadras.length || 0} ${countLabel(ocupacaoQuadras.length, terms.espaco_singular, terms.espaco_plural)} com leitura recente.`}
            to="/admin/turmas"
            nivel="ok"
          />
        </div>
      </section>

      <div className={`mb-6 grid grid-cols-2 gap-3 ${features.store ? 'lg:grid-cols-4' : 'lg:grid-cols-3'}`}>
        <AtalhoAdmin to="/admin/turmas" icon="court" titulo={capitalize(terms.espaco_plural)} descricao="Turmas e manutenção" />
        <AtalhoAdmin to="/admin/alunos" icon="users" titulo={capitalize(terms.pessoa_plural)} descricao="Cadastro e histórico" />
        <AtalhoAdmin to="/admin/mensalidades" icon="money" titulo="Mensalidades" descricao="Pagamentos e atrasos" />
        {features.store && <AtalhoAdmin to="/admin/estoque" icon="stock" titulo="Estoque" descricao="Produtos de balcão" />}
      </div>

      {metricas && (
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            titulo="Receita do mes"
            valor={formatarMoeda(metricas.receita_total)}
            icone={<Icon name="money" className="h-6 w-6" />}
            cor="green"
            subtitulo={`Mensalidades: ${formatarMoeda(metricas.receita_mensalidades)}`}
          />
          <KpiCard
            titulo="Inadimplencia"
            valor={formatarMoeda(metricas.inadimplencia)}
            icone={<Icon name="alert" className="h-6 w-6" />}
            cor="red"
          />
          <KpiCard
            titulo={`${capitalize(terms.pessoa_plural)} ativos`}
            valor={metricas.alunos_ativos}
            icone={<Icon name="users" className="h-6 w-6" />}
            cor="blue"
            subtitulo={`+${metricas.novos_alunos_mes} novos este mês`}
          />
          <KpiCard
            titulo="Check-ins 30d"
            valor={metricas.checkins_30d}
            icone={<Icon name="check" className="h-6 w-6" />}
            cor="arena"
            subtitulo={`${metricas.turmas_ativas} turmas ativas`}
          />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <GraficoCard titulo={<TituloGrafico icon="trend" texto="Receita dos ultimos 12 meses" />}>
          {dadosReceita.length === 0 ? (
            <p className="py-12 text-center text-slate-400">Sem dados ainda</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dadosReceita}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v) => formatarMoeda(v)} labelStyle={{ fontWeight: 'bold' }} />
                <Legend />
                <Line type="monotone" dataKey="mensalidades" stroke="#22c55e" strokeWidth={2.5} name="Mensalidades" />
                <Line type="monotone" dataKey="loja" stroke="#123b5d" strokeWidth={2.5} name="Loja" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </GraficoCard>

        <GraficoCard titulo={<TituloGrafico icon="overview" texto="Status das mensalidades" />}>
          {dadosStatus.length === 0 ? (
            <p className="py-12 text-center text-slate-400">Sem dados ainda</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={dadosStatus} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={(entry) => `${entry.name}: ${entry.value}`}>
                  {dadosStatus.map((entry, index) => (
                    <Cell key={`cell-${entry.name}`} fill={CORES_PIE[index % CORES_PIE.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </GraficoCard>

        <GraficoCard titulo={<TituloGrafico icon="trophy" texto={`Top ${terms.pessoa_plural} mais frequentes`} />}>
          {ranking.length === 0 ? (
            <p className="py-12 text-center text-slate-400">Sem check-ins ainda</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ranking} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="nome" tick={{ fontSize: 12 }} width={120} />
                <Tooltip />
                <Bar dataKey="total" fill="var(--admin-accent)" name="Check-ins" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </GraficoCard>

        <GraficoCard titulo={<TituloGrafico icon="pin" texto={`Ocupação por ${terms.espaco_singular}`} />}>
          {ocupacaoQuadras.length === 0 ? (
            <p className="py-12 text-center text-slate-400">Sem dados ainda</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ocupacaoQuadras}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="quadra" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="total" fill="var(--admin-accent)" name="Check-ins" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </GraficoCard>
      </div>
    </div>
  );
}

function AlertaOperacao({ titulo, texto, to, nivel }) {
  const estilos = {
    alto: 'border-red-200 bg-red-50 text-red-700',
    medio: 'border-cyan-200 bg-cyan-50 text-cyan-800',
    ok: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  };

  return (
    <Link to={to} className={`rounded-lg border p-4 transition hover:shadow-sm ${estilos[nivel]}`}>
      <div className="flex items-start gap-3">
        <Icon name={nivel === 'alto' ? 'alert' : 'check'} className="mt-0.5 h-5 w-5" />
        <div>
          <p className="font-bold">{titulo}</p>
          <p className="mt-1 text-sm opacity-80">{texto}</p>
        </div>
      </div>
    </Link>
  );
}

function AtalhoAdmin({ to, icon, titulo, descricao }) {
  return (
    <Link
      to={to}
      className="app-surface-hover p-4"
    >
      <div className="flex items-center gap-3">
        <span className="admin-accent-icon grid h-10 w-10 place-items-center rounded-md">
          <Icon name={icon} className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <p className="truncate font-bold text-slate-950">{titulo}</p>
          <p className="truncate text-xs text-slate-500">{descricao}</p>
        </div>
      </div>
    </Link>
  );
}

function TituloGrafico({ icon, texto }) {
  return (
    <span className="flex items-center gap-2">
      <Icon name={icon} className="h-5 w-5 text-[var(--admin-accent)]" />
      {texto}
    </span>
  );
}

export default DashboardAdmin;

function capitalize(value) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}

function countLabel(count, singular, plural) {
  return count === 1 ? singular : plural;
}
