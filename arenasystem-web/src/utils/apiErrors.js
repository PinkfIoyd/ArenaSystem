function firstErrorMessage(value) {
  if (typeof value === 'string' && value.trim()) return value;
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstErrorMessage(item);
      if (message) return message;
    }
  }
  if (value && typeof value === 'object') {
    for (const item of Object.values(value)) {
      const message = firstErrorMessage(item);
      if (message) return message;
    }
  }
  return '';
}

export function apiErrorMessage(error, fallback = 'Não foi possível concluir. Tente novamente.') {
  const data = error?.response?.data;
  if (!data) return fallback;
  return firstErrorMessage(data) || fallback;
}

export function apiFieldErrors(error) {
  const data = error?.response?.data;
  if (!data || typeof data !== 'object' || Array.isArray(data)) return {};
  return Object.fromEntries(Object.entries(data).map(([key, value]) => [
    key,
    firstErrorMessage(value),
  ]));
}
