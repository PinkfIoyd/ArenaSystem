import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';
import CardTurma from '../components/CardTurma';
import Toast from '../components/Toast';
import Icon from '../components/Icon';

function Turmas() {
  const [turmas, setTurmas] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [filtro, setFiltro] = useState('minhas');
  const [fazendoCheckin, setFazendoCheckin] = useState(null);
  const [processando, setProcessando] = useState(null);
  const [toast, setToast] = useState(null);

  const carregarTurmas = useCallback(async () => {
    setCarregando(true);
    try {
      const url = filtro === 'minhas' ? '/turmas/minhas/' : '/turmas/';
      const { data } = await api.get(url);
      setTurmas(Array.isArray(data) ? data : data.results || []);
    } catch {
      setToast({ mensagem: 'Erro ao carregar turmas', tipo: 'erro' });
    } finally {
      setCarregando(false);
    }
  }, [filtro]);

  useEffect(() => {
    const id = setTimeout(carregarTurmas, 0);
    return () => clearTimeout(id);
  }, [carregarTurmas]);

  const fazerCheckin = async (turmaId) => {
    setFazendoCheckin(turmaId);
    try {
      const { data } = await api.post(`/turmas/${turmaId}/checkin/`);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
      setTurmas((turmasAtuais) =>
        turmasAtuais.map((turma) =>
          turma.id === turmaId ? { ...turma, checkin_state: { ...(turma.checkin_state || {}), state: 'pending', checkin_id: data.checkin_id } } : turma
        )
      );
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao fazer check-in';
      setToast({ mensagem: msg, tipo: 'erro' });
      if (err.response?.data?.code === 'checkin_already_requested') {
        setTurmas((turmasAtuais) =>
          turmasAtuais.map((turma) =>
            turma.id === turmaId ? { ...turma, checkin_state: { ...(turma.checkin_state || {}), state: err.response.data.checkin_status || 'pending' } } : turma
          )
        );
      }
    } finally {
      setFazendoCheckin(null);
    }
  };

  const solicitarMatricula = async (turma) => {
    if (!confirm(`Solicitar matricula em "${turma.nome}"?`)) return;
    setProcessando(turma.id);
    try {
      const { data } = await api.post(`/turmas/${turma.id}/solicitar-matricula/`);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao solicitar';
      setToast({ mensagem: msg, tipo: 'erro' });
    } finally {
      setProcessando(null);
    }
  };

  const entrarFila = async (turma) => {
    if (!confirm(`Entrar na fila de espera de "${turma.nome}"?`)) return;
    setProcessando(turma.id);
    try {
      const { data } = await api.post(`/turmas/${turma.id}/entrar-fila/`);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao entrar na fila';
      setToast({ mensagem: msg, tipo: 'erro' });
    } finally {
      setProcessando(null);
    }
  };

  const solicitarCancelamento = async (turma) => {
    if (!confirm(`Solicitar cancelamento da matricula em "${turma.nome}"?`)) return;
    setProcessando(turma.id);
    try {
      const { data } = await api.post(`/turmas/${turma.id}/solicitar-cancelamento/`);
      setToast({ mensagem: data.detail, tipo: 'sucesso' });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao cancelar';
      setToast({ mensagem: msg, tipo: 'erro' });
    } finally {
      setProcessando(null);
    }
  };

  return (
    <Layout>
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="page-kicker">Aulas e modalidades</p>
          <h2 className="page-title">Turmas</h2>
          <p className="page-subtitle">Acompanhe suas turmas e explore novas opcoes.</p>
        </div>

        <div className="segmented-control">
          <FiltroButton ativo={filtro === 'minhas'} onClick={() => setFiltro('minhas')}>
            Minhas turmas
          </FiltroButton>
          <FiltroButton ativo={filtro === 'todas'} onClick={() => setFiltro('todas')}>
            Todas as turmas
          </FiltroButton>
        </div>
      </div>

      {carregando ? (
        <EstadoVazio icon="queue" titulo="Carregando turmas..." />
      ) : turmas.length === 0 ? (
        <EstadoVazio
          icon="court"
          titulo="Nenhuma turma encontrada"
          texto={filtro === 'minhas'
            ? 'Voce ainda nao esta matriculado em nenhuma turma.'
            : 'Nao ha turmas disponiveis no momento.'}
        />
      ) : (
        <div className="grid grid-cols-1 items-stretch gap-5 md:grid-cols-2 lg:grid-cols-3">
          {turmas.map((turma) => (
            <CardTurma
              key={turma.id}
              turma={turma}
              onCheckin={fazerCheckin}
              onSolicitarMatricula={solicitarMatricula}
              onEntrarFila={entrarFila}
              onSolicitarCancelamento={solicitarCancelamento}
              fazendoCheckin={fazendoCheckin === turma.id}
              processando={processando === turma.id}
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

function FiltroButton({ ativo, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`segmented-option ${ativo ? 'segmented-option-active' : ''}`}
    >
      {children}
    </button>
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

export default Turmas;
