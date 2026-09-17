export const CHECKIN_STATES = {
  outside_window: { label: 'Fora da janela', disabled: true, tone: 'slate' },
  available: { label: 'Fazer check-in', disabled: false, tone: 'primary' },
  requesting: { label: 'Solicitando...', disabled: true, tone: 'primary' },
  pending: { label: 'Aguardando validação', disabled: true, tone: 'amber' },
  confirmed: { label: 'Check-in confirmado', disabled: true, tone: 'green' },
  rejected: { label: 'Check-in rejeitado', disabled: true, tone: 'red' },
  expired: { label: 'Check-in expirado', disabled: true, tone: 'slate' },
};

export function checkinUi(state) {
  return CHECKIN_STATES[state] || CHECKIN_STATES.outside_window;
}

export function checkinButtonClass(state) {
  const tone = checkinUi(state).tone;
  if (tone === 'green') return 'bg-emerald-50 text-emerald-700';
  if (tone === 'amber') return 'bg-amber-50 text-amber-800';
  if (tone === 'red') return 'bg-red-50 text-red-700';
  if (tone === 'primary') return 'btn-primary';
  return 'bg-slate-100 text-slate-500';
}
