import { describe, expect, it } from 'vitest';
import { featuresFor, terminologyFor } from './useTerminology';

describe('multi-segment terminology', () => {
  it('keeps legacy arena labels and modules', () => {
    expect(terminologyFor({ tipo_negocio: 'arena' }).pessoa_plural).toBe('alunos');
    expect(featuresFor({})).toEqual({ classes: true, openAccess: false, reservations: true, store: true });
  });

  it('uses academy labels and server feature flags', () => {
    const academy = {
      tipo_negocio: 'academia',
      operational_settings: {
        classes_enabled: true, open_access_enabled: true,
        reservations_enabled: false, store_enabled: false,
      },
    };
    expect(terminologyFor(academy)).toMatchObject({ pessoa_plural: 'membros', espaco_plural: 'espaços' });
    expect(featuresFor(academy)).toEqual({ classes: true, openAccess: true, reservations: false, store: false });
  });
});
