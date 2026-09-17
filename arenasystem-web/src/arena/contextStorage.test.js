import { beforeEach, describe, expect, it } from 'vitest';
import { arenaContextHeaders, clearArenaContext, getArenaContext, migrateLegacyArenaContext, setArenaContext } from './contextStorage';

describe('superadmin arena context', () => {
  beforeEach(() => { localStorage.clear(); sessionStorage.clear(); window.history.pushState({}, '', '/admin/alunos'); });

  it('uses sessionStorage and sends tenant headers only to operational APIs', () => {
    setArenaContext({ arena: { id: 12, nome: 'Arena Teste' }, motivo: 'Suporte' });
    expect(getArenaContext().arena.id).toBe(12);
    expect(localStorage.getItem('arenaflow_superadmin_context')).toBeNull();
    expect(arenaContextHeaders('/admin/alunos/')).toEqual({
      'X-Arena-ID': '12', 'X-Arena-Access-Reason': 'Suporte', 'X-Frontend-Route': '/admin/alunos',
    });
    expect(arenaContextHeaders('/saas/operations/dashboard/')).toEqual({});
  });

  it('clears invalid JSON and legacy local storage keys', () => {
    sessionStorage.setItem('arenaflow_superadmin_context', '{invalid');
    localStorage.setItem('arena_context_id', '99');
    expect(getArenaContext()).toBeNull();
    migrateLegacyArenaContext();
    expect(localStorage.getItem('arena_context_id')).toBeNull();
    setArenaContext({ arena: { id: 1 } });
    clearArenaContext();
    expect(getArenaContext()).toBeNull();
  });
});

