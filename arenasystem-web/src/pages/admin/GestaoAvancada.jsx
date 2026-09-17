import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../../api/client';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import Toast from '../../components/Toast';
import { formatarData, formatarMoeda } from '../../utils/format';

const etapas = ['novo', 'contato', 'experimental', 'negociacao', 'ganho', 'perdido'];
const etapaLabel = {
  novo: 'Novo',
  contato: 'Contato',
  experimental: 'Experimental',
  negociacao: 'Negociacao',
  ganho: 'Ganho',
  perdido: 'Perdido',
};

function GestaoAvancada() {
  const [resumo, setResumo] = useState(null);
  const [leads, setLeads] = useState([]);
  const [reservas, setReservas] = useState([]);
  const [contas, setContas] = useState([]);
  const [quadras, setQuadras] = useState([]);
  const [faixas, setFaixas] = useState([]);
  const [grade, setGrade] = useState({ horarios: [], quadras: [], reservas: [], bloqueios: [] });
  const [dataGrade, setDataGrade] = useState(new Date().toISOString().slice(0, 10));
  const [toast, setToast] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [leadForm, setLeadForm] = useState({ nome: '', telefone: '', modalidade_interesse: '', origem: 'whatsapp', etapa: 'novo', valor_potencial: '' });
  const [contaForm, setContaForm] = useState({ tipo: 'pagar', descricao: '', categoria: '', fornecedor: '', valor: '', vencimento: '' });
  const [reservaForm, setReservaForm] = useState({ quadra: '', cliente_nome: '', cliente_telefone: '', data: '', hora_inicio: '', hora_fim: '', valor: '' });
  const [bloqueioForm, setBloqueioForm] = useState({ quadra: '', data: '', hora_inicio: '', hora_fim: '', motivo: '', categoria: 'outro' });
  const [faixaForm, setFaixaForm] = useState({ quadra: '', dia_semana: '0', hora_inicio: '', hora_fim: '', valor: '' });
  const [recorrencia, setRecorrencia] = useState({ ativa: false, ocorrencias: 4 });
  const [reservaEditando, setReservaEditando] = useState(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const [rResumo, rLeads, rReservas, rContas, rQuadras, rGrade, rFaixas] = await Promise.all([
        api.get('/admin/resumo-executivo/'),
        api.get('/admin/leads/'),
        api.get('/reservas-quadra/'),
        api.get('/admin/contas-financeiras/'),
        api.get('/admin/quadras/'),
        api.get(`/reservas-quadra/grade/?data=${dataGrade}`),
        api.get('/admin/faixas-preco-reserva/'),
      ]);
      setResumo(rResumo.data);
      setLeads(rLeads.data.results || rLeads.data || []);
      setReservas(rReservas.data.results || rReservas.data || []);
      setContas(rContas.data.results || rContas.data || []);
      setQuadras(rQuadras.data.results || rQuadras.data || []);
      setGrade(rGrade.data);
      setFaixas(rFaixas.data.results || rFaixas.data || []);
    } catch (err) {
      setToast({ tipo: 'erro', mensagem: err.response?.data?.detail || 'Erro ao carregar gestao avancada.' });
    } finally {
      setCarregando(false);
    }
  }, [dataGrade]);

  useEffect(() => {
    const id = setTimeout(carregar, 0);
    return () => clearTimeout(id);
  }, [carregar]);

  const leadsPorEtapa = useMemo(() => {
    const map = Object.fromEntries(etapas.map((etapa) => [etapa, []]));
    leads.forEach((lead) => {
      if (map[lead.etapa]) map[lead.etapa].push(lead);
    });
    return map;
  }, [leads]);

  const salvarLead = async (e) => {
    e.preventDefault();
    try {
      await api.post('/admin/leads/', leadForm);
      setLeadForm({ nome: '', telefone: '', modalidade_interesse: '', origem: 'whatsapp', etapa: 'novo', valor_potencial: '' });
      setToast({ tipo: 'sucesso', mensagem: 'Lead cadastrado.' });
      await carregar();
    } catch {
      setToast({ tipo: 'erro', mensagem: 'Nao foi possivel cadastrar o lead.' });
    }
  };

  const salvarConta = async (e) => {
    e.preventDefault();
    try {
      await api.post('/admin/contas-financeiras/', contaForm);
      setContaForm({ tipo: 'pagar', descricao: '', categoria: '', fornecedor: '', valor: '', vencimento: '' });
      setToast({ tipo: 'sucesso', mensagem: 'Conta cadastrada.' });
      await carregar();
    } catch {
      setToast({ tipo: 'erro', mensagem: 'Nao foi possivel cadastrar a conta.' });
    }
  };

  const salvarReserva = async (e) => {
    e.preventDefault();
    setSalvando(true);
    try {
      if (recorrencia.ativa) {
        await api.post('/reservas-quadra/recorrente/', {
          quadra: reservaForm.quadra,
          cliente_nome: reservaForm.cliente_nome,
          cliente_telefone: reservaForm.cliente_telefone,
          data_inicial: reservaForm.data,
          hora_inicio: reservaForm.hora_inicio,
          hora_fim: reservaForm.hora_fim,
          ocorrencias: recorrencia.ocorrencias,
        });
      } else {
        await api.post('/reservas-quadra/', reservaForm);
      }
      setReservaForm({ quadra: '', cliente_nome: '', cliente_telefone: '', data: '', hora_inicio: '', hora_fim: '', valor: '' });
      setRecorrencia({ ativa: false, ocorrencias: 4 });
      setToast({ tipo: 'sucesso', mensagem: 'Reserva cadastrada.' });
      await carregar();
    } catch (err) {
      setToast({ tipo: 'erro', mensagem: formatarErroApi(err, 'Nao foi possivel cadastrar a reserva.') });
    } finally {
      setSalvando(false);
    }
  };

  const salvarBloqueio = async (e) => {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post('/admin/bloqueios-quadra/', bloqueioForm);
      setBloqueioForm({ quadra: '', data: '', hora_inicio: '', hora_fim: '', motivo: '', categoria: 'outro' });
      setToast({ tipo: 'sucesso', mensagem: 'Horario bloqueado.' });
      await carregar();
    } catch (err) {
      setToast({ tipo: 'erro', mensagem: formatarErroApi(err, 'Nao foi possivel bloquear o horario.') });
    } finally {
      setSalvando(false);
    }
  };

  const salvarFaixa = async (e) => {
    e.preventDefault();
    if (Number(faixaForm.valor) < 0 || faixaForm.hora_inicio >= faixaForm.hora_fim) {
      setToast({ tipo: 'erro', mensagem: 'Confira horario e preco da faixa.' });
      return;
    }
    try {
      await api.post('/admin/faixas-preco-reserva/', {
        ...faixaForm,
        quadra: faixaForm.quadra || null,
      });
      setFaixaForm({ quadra: '', dia_semana: '0', hora_inicio: '', hora_fim: '', valor: '' });
      setToast({ tipo: 'sucesso', mensagem: 'Faixa de preco criada.' });
      await carregar();
    } catch (err) {
      setToast({ tipo: 'erro', mensagem: formatarErroApi(err, 'Nao foi possivel criar a faixa.') });
    }
  };

  const excluirFaixa = async (faixa) => {
    if (!confirm('Excluir esta faixa de preco?')) return;
    await api.delete(`/admin/faixas-preco-reserva/${faixa.id}/`);
    setToast({ tipo: 'sucesso', mensagem: 'Faixa removida.' });
    await carregar();
  };

  const moverLead = async (lead, etapa) => {
    await api.post(`/admin/leads/${lead.id}/mover/`, { etapa });
    await carregar();
  };

  const pagarConta = async (conta) => {
    await api.post(`/admin/contas-financeiras/${conta.id}/pagar/`);
    setToast({ tipo: 'sucesso', mensagem: 'Conta marcada como paga.' });
    await carregar();
  };

  const confirmarReserva = async (reserva) => {
    await api.post(`/reservas-quadra/${reserva.id}/confirmar/`);
    setToast({ tipo: 'sucesso', mensagem: 'Reserva confirmada.' });
    await carregar();
  };

  const abrirBloqueioPeloSlot = (slot) => {
    setBloqueioForm({
      quadra: String(slot.quadra.id),
      data: dataGrade,
      hora_inicio: slot.hora,
      hora_fim: proximaHora(slot.hora),
      motivo: '',
      categoria: 'outro',
    });
    setToast({ tipo: 'sucesso', mensagem: 'Horario selecionado para bloqueio.' });
  };

  const salvarEdicaoReserva = async (dados) => {
    setSalvando(true);
    try {
      await api.patch(`/reservas-quadra/${dados.id}/`, dados);
      setReservaEditando(null);
      setToast({ tipo: 'sucesso', mensagem: 'Reserva atualizada.' });
      await carregar();
    } catch (err) {
      setToast({ tipo: 'erro', mensagem: formatarErroApi(err, 'Nao foi possivel atualizar a reserva.') });
    } finally {
      setSalvando(false);
    }
  };

  const cancelarReserva = async (reserva) => {
    if (!confirm('Cancelar esta reserva?')) return;
    await api.post(`/reservas-quadra/${reserva.id}/cancelar/`);
    setReservaEditando(null);
    setToast({ tipo: 'sucesso', mensagem: 'Reserva cancelada.' });
    await carregar();
  };

  if (carregando) {
    return <div className="rounded-xl bg-white p-10 text-center text-gray-500 shadow-sm">Carregando gestao...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">Operacao profissional</p>
          <h2 className="text-3xl font-bold text-gray-900">Gestao</h2>
          <p className="text-sm text-gray-600">CRM, reservas, contas e inteligencia operacional em uma so visao.</p>
        </div>
        <button onClick={carregar} className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50">
          Atualizar
        </button>
      </div>

      {resumo && (
        <>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
            <Resumo titulo="Resultado previsto" valor={formatarMoeda(resumo.financeiro.resultado_previsto)} icon="trend" />
            <Resumo titulo="Contas a pagar" valor={formatarMoeda(resumo.financeiro.contas_pagar)} icon="money" />
            <Resumo titulo="Ocupacao" valor={`${resumo.operacao.ocupacao_turmas}%`} icon="court" />
            <Resumo titulo="Leads abertos" valor={resumo.crm.leads_abertos} icon="users" />
          </div>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            {resumo.alertas.map((alerta) => (
              <div key={alerta.titulo} className="rounded-xl border border-cyan-100 bg-cyan-50 p-4">
                <p className="font-bold text-cyan-900">{alerta.titulo}</p>
                <p className="mt-1 text-sm text-cyan-800">{alerta.mensagem}</p>
              </div>
            ))}
          </div>
        </>
      )}

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        <Painel titulo="Novo lead">
          <form onSubmit={salvarLead} className="space-y-3">
            <Input placeholder="Nome" value={leadForm.nome} onChange={(v) => setLeadForm({ ...leadForm, nome: v })} required />
            <Input placeholder="Telefone" value={leadForm.telefone} onChange={(v) => setLeadForm({ ...leadForm, telefone: v })} />
            <Input placeholder="Modalidade" value={leadForm.modalidade_interesse} onChange={(v) => setLeadForm({ ...leadForm, modalidade_interesse: v })} />
            <Input placeholder="Valor potencial" type="number" value={leadForm.valor_potencial} onChange={(v) => setLeadForm({ ...leadForm, valor_potencial: v })} />
            <button className="w-full rounded-lg bg-teal-700 px-4 py-2 text-sm font-bold text-white hover:bg-teal-800">Adicionar ao CRM</button>
          </form>
        </Painel>

        <Painel titulo="Nova conta">
          <form onSubmit={salvarConta} className="space-y-3">
            <select className="w-full rounded-lg border border-gray-200 px-3 py-2" value={contaForm.tipo} onChange={(e) => setContaForm({ ...contaForm, tipo: e.target.value })}>
              <option value="pagar">A pagar</option>
              <option value="receber">A receber</option>
            </select>
            <Input placeholder="Descricao" value={contaForm.descricao} onChange={(v) => setContaForm({ ...contaForm, descricao: v })} required />
            <Input placeholder="Categoria" value={contaForm.categoria} onChange={(v) => setContaForm({ ...contaForm, categoria: v })} />
            <Input placeholder="Valor" type="number" value={contaForm.valor} onChange={(v) => setContaForm({ ...contaForm, valor: v })} required />
            <Input placeholder="Vencimento" type="date" value={contaForm.vencimento} onChange={(v) => setContaForm({ ...contaForm, vencimento: v })} required />
            <button className="w-full rounded-lg bg-gray-900 px-4 py-2 text-sm font-bold text-white hover:bg-gray-800">Cadastrar conta</button>
          </form>
        </Painel>

        <Painel titulo="Nova reserva">
          <form onSubmit={salvarReserva} className="space-y-3">
            <select className="w-full rounded-lg border border-gray-200 px-3 py-2" value={reservaForm.quadra} onChange={(e) => setReservaForm({ ...reservaForm, quadra: e.target.value })} required>
              <option value="">Selecione a quadra</option>
              {quadras.map((quadra) => <option key={quadra.id} value={quadra.id}>{quadra.nome}</option>)}
            </select>
            <Input placeholder="Cliente" value={reservaForm.cliente_nome} onChange={(v) => setReservaForm({ ...reservaForm, cliente_nome: v })} required />
            <Input placeholder="Data" type="date" value={reservaForm.data} onChange={(v) => setReservaForm({ ...reservaForm, data: v })} required />
            <div className="grid grid-cols-2 gap-2">
              <Input type="time" value={reservaForm.hora_inicio} onChange={(v) => setReservaForm({ ...reservaForm, hora_inicio: v })} required />
              <Input type="time" value={reservaForm.hora_fim} onChange={(v) => setReservaForm({ ...reservaForm, hora_fim: v })} required />
            </div>
            <Input placeholder="Valor" type="number" value={reservaForm.valor} onChange={(v) => setReservaForm({ ...reservaForm, valor: v })} />
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-700">
              <input type="checkbox" checked={recorrencia.ativa} onChange={(e) => setRecorrencia({ ...recorrencia, ativa: e.target.checked })} />
              Recorrencia semanal
            </label>
            {recorrencia.ativa && (
              <Input placeholder="Ocorrencias" type="number" min="1" max="52" value={recorrencia.ocorrencias} onChange={(v) => setRecorrencia({ ...recorrencia, ocorrencias: v })} />
            )}
            <button disabled={salvando} className="w-full rounded-lg bg-green-600 px-4 py-2 text-sm font-bold text-white hover:bg-green-700 disabled:opacity-50">Reservar</button>
          </form>
        </Painel>

        <Painel titulo="Bloquear horario">
          <form onSubmit={salvarBloqueio} className="space-y-3">
            <select className="w-full rounded-lg border border-gray-200 px-3 py-2" value={bloqueioForm.quadra} onChange={(e) => setBloqueioForm({ ...bloqueioForm, quadra: e.target.value })} required>
              <option value="">Selecione a quadra</option>
              {quadras.map((quadra) => <option key={quadra.id} value={quadra.id}>{quadra.nome}</option>)}
            </select>
            <Input placeholder="Data" type="date" value={bloqueioForm.data} onChange={(v) => setBloqueioForm({ ...bloqueioForm, data: v })} required />
            <div className="grid grid-cols-2 gap-2">
              <Input type="time" value={bloqueioForm.hora_inicio} onChange={(v) => setBloqueioForm({ ...bloqueioForm, hora_inicio: v })} required />
              <Input type="time" value={bloqueioForm.hora_fim} onChange={(v) => setBloqueioForm({ ...bloqueioForm, hora_fim: v })} required />
            </div>
            <select className="w-full rounded-lg border border-gray-200 px-3 py-2" value={bloqueioForm.categoria} onChange={(e) => setBloqueioForm({ ...bloqueioForm, categoria: e.target.value })}>
              <option value="evento">Evento</option>
              <option value="chuva">Chuva</option>
              <option value="manutencao">Manutencao</option>
              <option value="outro">Outro</option>
            </select>
            <Input placeholder="Motivo" value={bloqueioForm.motivo} onChange={(v) => setBloqueioForm({ ...bloqueioForm, motivo: v })} required />
            <button disabled={salvando} className="w-full rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700 disabled:opacity-50">Bloquear</button>
          </form>
        </Painel>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-[360px_1fr]">
        <Painel titulo="Preco por faixa">
          <form onSubmit={salvarFaixa} className="space-y-3">
            <select className="w-full rounded-lg border border-gray-200 px-3 py-2" value={faixaForm.quadra} onChange={(e) => setFaixaForm({ ...faixaForm, quadra: e.target.value })}>
              <option value="">Todas as quadras</option>
              {quadras.map((quadra) => <option key={quadra.id} value={quadra.id}>{quadra.nome}</option>)}
            </select>
            <select className="w-full rounded-lg border border-gray-200 px-3 py-2" value={faixaForm.dia_semana} onChange={(e) => setFaixaForm({ ...faixaForm, dia_semana: e.target.value })}>
              {['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo'].map((dia, index) => <option key={dia} value={index}>{dia}</option>)}
            </select>
            <div className="grid grid-cols-2 gap-2">
              <Input type="time" value={faixaForm.hora_inicio} onChange={(v) => setFaixaForm({ ...faixaForm, hora_inicio: v })} required />
              <Input type="time" value={faixaForm.hora_fim} onChange={(v) => setFaixaForm({ ...faixaForm, hora_fim: v })} required />
            </div>
            <Input placeholder="Preco" type="number" min="0" value={faixaForm.valor} onChange={(v) => setFaixaForm({ ...faixaForm, valor: v })} required />
            <button className="w-full rounded-lg bg-teal-700 px-4 py-2 text-sm font-bold text-white hover:bg-teal-800">Criar faixa</button>
          </form>
        </Painel>

        <Tabela titulo="Faixas cadastradas">
          {faixas.map((faixa) => (
            <Linha key={faixa.id} titulo={`${faixa.quadra_nome || 'Todas as quadras'} - ${diaSemana(faixa.dia_semana)}`} detalhe={`${faixa.hora_inicio?.slice(0, 5)}-${faixa.hora_fim?.slice(0, 5)}`} valor={formatarMoeda(faixa.valor)}>
              <button onClick={() => excluirFaixa(faixa)} className="rounded bg-red-50 px-2 py-1 text-xs font-bold text-red-700">Excluir</button>
            </Linha>
          ))}
        </Tabela>
      </section>

      <section className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-bold text-gray-900">Grade operacional</h3>
          <input type="date" className="rounded-lg border border-gray-200 px-3 py-2" value={dataGrade} onChange={(e) => setDataGrade(e.target.value)} />
        </div>
        <GradeOperacional grade={grade} onSlotClick={abrirBloqueioPeloSlot} onReservaClick={setReservaEditando} />
      </section>

      <section>
        <h3 className="mb-3 text-xl font-bold text-gray-900">Funil comercial</h3>
        <div className="grid grid-cols-1 gap-3 xl:grid-cols-6">
          {etapas.map((etapa) => (
            <div key={etapa} className="rounded-xl border border-gray-100 bg-white p-3 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <p className="font-bold text-gray-800">{etapaLabel[etapa]}</p>
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-bold text-gray-600">{leadsPorEtapa[etapa].length}</span>
              </div>
              <div className="space-y-2">
                {leadsPorEtapa[etapa].map((lead) => (
                  <div key={lead.id} className="rounded-lg border border-gray-100 p-3">
                    <p className="font-semibold text-gray-900">{lead.nome}</p>
                    <p className="text-xs text-gray-500">{lead.modalidade_interesse || 'Sem modalidade'}</p>
                    <p className="mt-1 text-xs font-semibold text-green-700">{formatarMoeda(lead.valor_potencial)}</p>
                    <select className="mt-2 w-full rounded border border-gray-200 px-2 py-1 text-xs" value={lead.etapa} onChange={(e) => moverLead(lead, e.target.value)}>
                      {etapas.map((opcao) => <option key={opcao} value={opcao}>{etapaLabel[opcao]}</option>)}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Tabela titulo="Reservas próximas">
          {reservas.slice(0, 8).map((reserva) => (
            <Linha key={reserva.id} titulo={`${reserva.quadra_nome} - ${reserva.cliente_nome}`} detalhe={`${formatarData(reserva.data)} ${reserva.hora_inicio?.slice(0, 5)}-${reserva.hora_fim?.slice(0, 5)}`} valor={formatarMoeda(reserva.valor)}>
              {reserva.status === 'pendente' && <button onClick={() => confirmarReserva(reserva)} className="rounded bg-green-50 px-2 py-1 text-xs font-bold text-green-700">Confirmar</button>}
            </Linha>
          ))}
        </Tabela>
        <Tabela titulo="Contas em aberto">
          {contas.filter((c) => c.status !== 'paga').slice(0, 8).map((conta) => (
            <Linha key={conta.id} titulo={conta.descricao} detalhe={`${conta.tipo === 'pagar' ? 'Pagar' : 'Receber'} - ${formatarData(conta.vencimento)}`} valor={formatarMoeda(conta.valor)}>
              <button onClick={() => pagarConta(conta)} className="rounded bg-gray-100 px-2 py-1 text-xs font-bold text-gray-700">Pagar</button>
            </Linha>
          ))}
        </Tabela>
      </section>

      {toast && <Toast mensagem={toast.mensagem} tipo={toast.tipo} onClose={() => setToast(null)} />}

      <Modal aberto={Boolean(reservaEditando)} onFechar={() => setReservaEditando(null)} titulo="Editar reserva" tamanho="lg">
        {reservaEditando && (
          <ReservaEditor
            reserva={reservaEditando}
            quadras={quadras}
            salvando={salvando}
            onSalvar={salvarEdicaoReserva}
            onCancelar={cancelarReserva}
          />
        )}
      </Modal>
    </div>
  );
}

function Resumo({ titulo, valor, icon }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{titulo}</p>
        <Icon name={icon} className="h-5 w-5 text-teal-700" />
      </div>
      <p className="mt-2 text-2xl font-bold text-gray-900">{valor}</p>
    </div>
  );
}

function Painel({ titulo, children }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
      <h3 className="mb-3 font-bold text-gray-900">{titulo}</h3>
      {children}
    </div>
  );
}

function Input({ value, onChange, ...props }) {
  return <input {...props} value={value} onChange={(e) => onChange(e.target.value)} className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-cyan-400" />;
}

function GradeOperacional({ grade, onSlotClick, onReservaClick }) {
  const celula = (quadra, hora) => {
    const inicio = `${hora}:00`;
    const fim = `${String(Number(hora.slice(0, 2)) + 1).padStart(2, '0')}:00`;
    const reserva = grade.reservas.find((item) => item.quadra === quadra.id && item.status !== 'cancelada' && item.hora_inicio < fim && item.hora_fim > inicio);
    if (reserva) return { tipo: 'reserva', reserva, texto: `Reserva: ${reserva.cliente_nome || 'Reservado'}`, classe: 'bg-green-50 text-green-800 border-green-200' };
    const bloqueio = grade.bloqueios.find((item) => item.quadra === quadra.id && item.hora_inicio < fim && item.hora_fim > inicio);
    if (bloqueio) return { tipo: 'bloqueio', texto: `Bloqueio: ${bloqueio.motivo || 'Bloqueado'}`, classe: 'bg-red-50 text-red-800 border-red-200' };
    return { tipo: 'livre', texto: 'Livre', classe: 'bg-gray-50 text-gray-500 border-gray-100 hover:bg-gray-100' };
  };

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        <div className="grid" style={{ gridTemplateColumns: `88px repeat(${grade.quadras.length || 1}, minmax(150px, 1fr))` }}>
          <div className="border-b border-gray-200 p-2 text-xs font-bold uppercase text-gray-400">Horario</div>
          {grade.quadras.map((quadra) => <div key={quadra.id} className="border-b border-gray-200 p-2 text-sm font-bold text-gray-800">{quadra.nome}</div>)}
          {grade.horarios.map((hora) => (
            <div key={hora} className="contents">
              <div className="border-b border-gray-100 p-2 text-sm font-semibold text-gray-500">{hora}</div>
              {grade.quadras.map((quadra) => {
                const status = celula(quadra, hora.slice(0, 5));
                return (
                  <button
                    type="button"
                    key={`${quadra.id}-${hora}`}
                    onClick={() => status.tipo === 'reserva' ? onReservaClick(status.reserva) : status.tipo === 'livre' ? onSlotClick({ quadra, hora: hora.slice(0, 5) }) : null}
                    className={`m-1 rounded border p-2 text-left text-xs font-semibold ${status.classe}`}
                  >
                    {status.texto}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ReservaEditor({ reserva, quadras, salvando, onSalvar, onCancelar }) {
  const [dados, setDados] = useState({
    id: reserva.id,
    quadra: reserva.quadra,
    cliente_nome: reserva.cliente_nome || '',
    cliente_telefone: reserva.cliente_telefone || '',
    data: reserva.data,
    hora_inicio: reserva.hora_inicio?.slice(0, 5) || '',
    hora_fim: reserva.hora_fim?.slice(0, 5) || '',
    status: reserva.status,
    observacoes: reserva.observacoes || '',
  });

  const salvar = (event) => {
    event.preventDefault();
    if (!dados.quadra || !dados.data || !dados.hora_inicio || !dados.hora_fim || dados.hora_inicio >= dados.hora_fim) return;
    onSalvar(dados);
  };

  return (
    <form onSubmit={salvar} className="space-y-3">
      <select className="w-full rounded-lg border border-gray-200 px-3 py-2" value={dados.quadra} onChange={(e) => setDados({ ...dados, quadra: e.target.value })} required>
        {quadras.map((quadra) => <option key={quadra.id} value={quadra.id}>{quadra.nome}</option>)}
      </select>
      <Input placeholder="Cliente" value={dados.cliente_nome} onChange={(v) => setDados({ ...dados, cliente_nome: v })} required />
      <Input placeholder="Telefone" value={dados.cliente_telefone} onChange={(v) => setDados({ ...dados, cliente_telefone: v })} />
      <Input type="date" value={dados.data} onChange={(v) => setDados({ ...dados, data: v })} required />
      <div className="grid grid-cols-2 gap-2">
        <Input type="time" value={dados.hora_inicio} onChange={(v) => setDados({ ...dados, hora_inicio: v })} required />
        <Input type="time" value={dados.hora_fim} onChange={(v) => setDados({ ...dados, hora_fim: v })} required />
      </div>
      <select className="w-full rounded-lg border border-gray-200 px-3 py-2" value={dados.status} onChange={(e) => setDados({ ...dados, status: e.target.value })}>
        <option value="pendente">Pendente</option>
        <option value="confirmada">Confirmada</option>
        <option value="concluida">Concluida</option>
        <option value="cancelada">Cancelada</option>
      </select>
      <textarea className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-cyan-400" rows="3" value={dados.observacoes} onChange={(e) => setDados({ ...dados, observacoes: e.target.value })} placeholder="Observacoes" />
      <p className="text-sm font-semibold text-green-700">Preco atual: {formatarMoeda(reserva.valor)}</p>
      <div className="flex justify-between gap-2">
        <button type="button" onClick={() => onCancelar(reserva)} className="rounded-lg border border-red-200 px-4 py-2 text-sm font-bold text-red-700 hover:bg-red-50">
          Cancelar reserva
        </button>
        <button disabled={salvando} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-bold text-white hover:bg-teal-800 disabled:opacity-50">
          Salvar alteracoes
        </button>
      </div>
    </form>
  );
}

function proximaHora(hora) {
  const [h] = hora.split(':').map(Number);
  return `${String(Math.min(h + 1, 23)).padStart(2, '0')}:00`;
}

function diaSemana(index) {
  return ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo'][Number(index)] || '-';
}

function formatarErroApi(err, fallback) {
  const data = err.response?.data;
  if (!data) return fallback;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.conflitos)) return `${data.detail || fallback}: ${data.conflitos.map((item) => item.data).join(', ')}`;
  if (typeof data === 'object') return Object.values(data).flat().join(' ') || fallback;
  return fallback;
}

function Tabela({ titulo, children }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
      <h3 className="mb-3 font-bold text-gray-900">{titulo}</h3>
      <div className="divide-y divide-gray-100">{children}</div>
    </div>
  );
}

function Linha({ titulo, detalhe, valor, children }) {
  return (
    <div className="flex items-center justify-between gap-3 py-3">
      <div>
        <p className="font-semibold text-gray-900">{titulo}</p>
        <p className="text-xs text-gray-500">{detalhe}</p>
      </div>
      <div className="flex items-center gap-2 text-right">
        <p className="font-bold text-gray-900">{valor}</p>
        {children}
      </div>
    </div>
  );
}

export default GestaoAvancada;
