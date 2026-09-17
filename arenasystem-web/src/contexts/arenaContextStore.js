import { createContext, useContext } from 'react';

export const ArenaContextStore = createContext(null);

export function useArenaContext() {
  const value = useContext(ArenaContextStore);
  if (!value) throw new Error('useArenaContext deve ser usado dentro de ArenaContextProvider.');
  return value;
}
