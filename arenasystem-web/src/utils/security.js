const SENSITIVE_KEYS = ['password', 'senha', 'token', 'secret', 'authorization', 'cookie', 'access', 'refresh', 'credential'];

export function isSensitiveKey(key) {
  const normalized = String(key).toLowerCase();
  return SENSITIVE_KEYS.some((sensitive) => normalized.includes(sensitive));
}

export function sanitizeObject(value) {
  if (Array.isArray(value)) return value.map((item) => sanitizeObject(item));
  if (!value || typeof value !== 'object') return value;

  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [
      key,
      isSensitiveKey(key) ? '[mascarado]' : sanitizeObject(item),
    ]),
  );
}

export function formatJson(value) {
  return JSON.stringify(sanitizeObject(value || {}), null, 2);
}
