import { describe, expect, it } from 'vitest';
import { accessView } from './accessUi';

describe('accessView', () => {
  it.each([
    ['available', 'Fazer check-in'],
    ['requesting', 'Solicitando…'],
    ['pending', 'Aguardando recepção'],
    ['confirmed', 'Confirmado'],
    ['expired', 'Expirado'],
  ])('maps %s to an actionable label', (state, label) => {
    expect(accessView(state).button).toBe(label);
  });

  it('preserves the backend reason for blocked access', () => {
    expect(accessView('access_limit_reached', 'Limite mensal atingido.').text).toBe('Limite mensal atingido.');
  });
});
