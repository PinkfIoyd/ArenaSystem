import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/client';
import {
  clearArenaContext,
  getArenaContext,
  migrateLegacyArenaContext,
  setArenaContext,
} from '../arena/contextStorage';
import { ArenaContextStore } from './arenaContextStore';

export function ArenaContextProvider({ children }) {
  const [contexto, setContexto] = useState(() => getArenaContext());

  useEffect(() => {
    migrateLegacyArenaContext();
    const sync = (event) => setContexto(event.detail ?? getArenaContext());
    window.addEventListener('arena-context-changed', sync);
    return () => window.removeEventListener('arena-context-changed', sync);
  }, []);

  const acessarArena = useCallback(async (arenaId, motivo = '') => {
    const { data } = await api.post(`/saas/arenas/${arenaId}/acessar/`, { motivo });
    const proximo = { arena: data.arena, motivo: data.motivo || '' };
    setArenaContext(proximo);
    setContexto(proximo);
    return proximo;
  }, []);

  const sairDaArena = useCallback(() => {
    clearArenaContext();
    setContexto(null);
  }, []);

  const value = useMemo(() => ({ contexto, acessarArena, sairDaArena }), [contexto, acessarArena, sairDaArena]);
  return <ArenaContextStore.Provider value={value}>{children}</ArenaContextStore.Provider>;
}
