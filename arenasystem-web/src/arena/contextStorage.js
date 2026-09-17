const STORAGE_KEY = 'arenaflow_superadmin_context';
const LEGACY_KEYS = ['arena_context_id', 'arena_context_nome', 'arena_context_slug', 'arena_context_motivo'];

function browserStorage() {
  return typeof window === 'undefined' ? null : window.sessionStorage;
}

export function migrateLegacyArenaContext() {
  if (typeof window === 'undefined') return;
  LEGACY_KEYS.forEach((key) => window.localStorage.removeItem(key));
}

export function getArenaContext() {
  const storage = browserStorage();
  if (!storage) return null;
  try {
    const value = JSON.parse(storage.getItem(STORAGE_KEY));
    return value?.arena?.id ? value : null;
  } catch {
    storage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function setArenaContext(context) {
  const storage = browserStorage();
  if (!storage) return;
  storage.setItem(STORAGE_KEY, JSON.stringify(context));
  window.dispatchEvent(new CustomEvent('arena-context-changed', { detail: context }));
}

export function clearArenaContext() {
  const storage = browserStorage();
  if (storage) storage.removeItem(STORAGE_KEY);
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('arena-context-changed', { detail: null }));
  }
}

export function arenaContextHeaders(url = '') {
  const context = getArenaContext();
  if (!context) return {};
  const isControlPlane = url.startsWith('/saas/');
  const isAccessAction = /^\/saas\/arenas\/\d+\/acessar\//.test(url);
  if (isControlPlane && !isAccessAction) return {};
  return {
    'X-Arena-ID': String(context.arena.id),
    'X-Arena-Access-Reason': context.motivo || '',
    'X-Frontend-Route': typeof window !== 'undefined' ? window.location.pathname : '',
  };
}
