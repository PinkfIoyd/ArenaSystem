import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';
import CardMensalidade from '../components/CardMensalidade';
import ResumoCard from '../components/ResumoCard';
import Toast from '../components/Toast';
import Icon from '../components/Icon';
import { formatarMoeda } from '../utils/format';

function Mensalidades() {
  const [mensalidades, setMensalidades] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [filtro, setFiltro] = useState('todas');
  const [toast, setToast] = useState(null);

  const carregarMensalidades = useCallback(async () => {
    setCarregando(true);
    try {
      const { data } = await api.get('/mensalidades/');
      const lista = Array.isArray(data) ? data : data.results || [];
      setMensalidades(lista);
    } catch {
      setToast({ mensagem: 'Erro ao carregar mensalidades', tipo: 'erro' });
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    const id = setTimeout(carregarMensalidades, 0);
    return () => clearTimeout(id);
  }, [carregarMensalidades]);

  const totais = mensalidades.reduce(
    (acc, m) => {
      const valor = Number(m.valor);
      if (m.status === 'pago') acc.pago += valor;
      else if (m.status === 'pendente') acc.pendente += valor;
      else if (m.status === 'atrasado') acc.atrasado += valor;
      return acc;
    },
    { pago: 0, pendente: 0, atrasado: 0 }
  );

  const mensalidadesFiltradas = filtro === 'todas'
    ? mensalidades
    : mensalidades.filter((m) => m.status === filtro);

  const pagarMensalidade = async (mensalidade) => {
    try {
      const { data } = await api.post(`/mensalidades/${mensalidade.id}/pagar/`);
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      setToast({ mensagem: data.detail || 'Link de pagamento criado', tipo: 'sucesso' });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao iniciar pagamento';
      setToast({ mensagem: msg, tipo: 'erro' });
    }
  };

  const filtros = [
    { key: 'todas', label: 'Todas' },
    { key: 'pendente', label: 'Pendentes' },
    { key: 'atrasado', label: 'Atrasadas' },
    { key: 'pago', label: 'Pagas' },
  ];

  return (
    <Layout>
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="page-kicker">Financeiro</p>
          <h2 className="page-title">Mensalidades</h2>
          <p className="page-subtitle">Acompanhe vencimentos, pagamentos e pendencias.</p>
        </div>

        <div className="segmented-control">
          {filtros.map((f) => (
            <button
              key={f.key}
              type="button"
              onClick={() => setFiltro(f.key)}
              className={`segmented-option ${filtro === f.key ? 'segmented-option-active' : ''}`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <ResumoCard titulo="Total pago" valor={formatarMoeda(totais.pago)} cor="green" icone={<Icon name="check" className="h-5 w-5" />} />
        <ResumoCard titulo="A pagar" valor={formatarMoeda(totais.pendente)} cor="cyan" icone={<Icon name="money" className="h-5 w-5" />} />
        <ResumoCard titulo="Em atraso" valor={formatarMoeda(totais.atrasado)} cor="red" icone={<Icon name="alert" className="h-5 w-5" />} />
      </div>

      {carregando ? (
        <EstadoVazio icon="queue" titulo="Carregando mensalidades..." />
      ) : mensalidadesFiltradas.length === 0 ? (
        <EstadoVazio
          icon="money"
          titulo="Nenhuma mensalidade encontrada"
          texto={filtro === 'todas'
            ? 'Voce ainda nao possui mensalidades.'
            : `Nenhuma mensalidade com status "${filtro}".`}
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {mensalidadesFiltradas.map((m) => (
            <CardMensalidade
              key={m.id}
              mensalidade={m}
              onPagar={pagarMensalidade}
            />
          ))}
        </div>
      )}

      {toast && (
        <Toast
          mensagem={toast.mensagem}
          tipo={toast.tipo}
          onClose={() => setToast(null)}
        />
      )}
    </Layout>
  );
}

function EstadoVazio({ icon, titulo, texto }) {
  return (
    <div className="app-surface py-12 text-center">
      <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-cyan-50 text-teal-800">
        <Icon name={icon} className="h-6 w-6" />
      </div>
      <p className="font-semibold text-slate-700">{titulo}</p>
      {texto && <p className="mt-1 text-sm text-slate-400">{texto}</p>}
    </div>
  );
}

export default Mensalidades;
