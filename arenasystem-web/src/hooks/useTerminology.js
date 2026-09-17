import useArena from './useArena';

export const DEFAULT_TERMINOLOGY = {
  unidade_singular: 'arena',
  unidade_plural: 'arenas',
  pessoa_singular: 'aluno',
  pessoa_plural: 'alunos',
  espaco_singular: 'quadra',
  espaco_plural: 'quadras',
};

export function terminologyFor(arena = {}) {
  const fallback = arena.tipo_negocio === 'academia'
    ? {
        unidade_singular: 'unidade', unidade_plural: 'unidades',
        pessoa_singular: 'membro', pessoa_plural: 'membros',
        espaco_singular: 'espaço', espaco_plural: 'espaços',
      }
    : DEFAULT_TERMINOLOGY;
  return { ...fallback, ...(arena.terminologia || {}) };
}

export function featuresFor(arena = {}) {
  const settings = arena.operational_settings || {};
  return {
    classes: settings.classes_enabled ?? true,
    openAccess: settings.open_access_enabled ?? false,
    reservations: settings.reservations_enabled ?? true,
    store: settings.store_enabled ?? true,
  };
}

export default function useTerminology() {
  const arena = useArena();
  return { arena, terms: terminologyFor(arena), features: featuresFor(arena) };
}
