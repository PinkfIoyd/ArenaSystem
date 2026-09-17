export function accessView(state, detail = '') {
  const states = {
    available: { title: 'Entrada disponível', text: 'Solicite sua entrada e aguarde a validação da recepção.', button: 'Fazer check-in' },
    requesting: { title: 'Enviando solicitação', text: 'Só um instante enquanto validamos seus dados.', button: 'Solicitando…' },
    pending: { title: 'Aguardando validação', text: 'Sua solicitação já está na fila da recepção.', button: 'Aguardando recepção' },
    confirmed: { title: 'Acesso confirmado', text: 'Boa atividade! Registre sua saída quando terminar.', button: 'Confirmado' },
    expired: { title: 'Solicitação expirada', text: 'Envie uma nova solicitação se ainda estiver no horário permitido.', button: 'Expirado' },
  };
  return states[state] || { title: 'Acesso indisponível', text: detail || 'Consulte a recepção para verificar as regras do seu plano.', button: 'Indisponível' };
}
