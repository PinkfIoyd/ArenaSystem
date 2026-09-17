// Formata número como moeda brasileira: 200 → "R$ 200,00"
export function formatarMoeda(valor) {
  const numero = Number(valor) || 0;
  return numero.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

// Formata data ISO para "DD/MM/YYYY": "2025-01-15" → "15/01/2025"
export function formatarData(dataIso) {
  if (!dataIso) return '-';
  const [ano, mes, dia] = dataIso.split('-');
  return `${dia}/${mes}/${ano}`;
}

// Formata data para "Janeiro/2025"
export function formatarMesAno(dataIso) {
  if (!dataIso) return '-';
  const data = new Date(dataIso + 'T00:00:00');
  return data.toLocaleDateString('pt-BR', {
    month: 'long',
    year: 'numeric',
  }).replace(' de ', '/');
}

// Verifica se uma data está no passado
export function estaVencida(dataIso) {
  if (!dataIso) return false;
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const data = new Date(dataIso + 'T00:00:00');
  return data < hoje;
}

// Calcula dias até o vencimento (negativo = atrasado)
export function diasAteVencimento(dataIso) {
  if (!dataIso) return null;
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const data = new Date(dataIso + 'T00:00:00');
  const diff = data - hoje;
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}