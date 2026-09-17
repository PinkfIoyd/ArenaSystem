import { describe, expect, it } from 'vitest';
import { checkinUi } from './checkinUi';

describe('checkinUi', () => {
  it.each([
    ['outside_window', 'Fora da janela', true],
    ['available', 'Fazer check-in', false],
    ['requesting', 'Solicitando...', true],
    ['pending', 'Aguardando validação', true],
    ['confirmed', 'Check-in confirmado', true],
    ['rejected', 'Check-in rejeitado', true],
    ['expired', 'Check-in expirado', true],
  ])('mapeia o estado %s', (state, label, disabled) => {
    expect(checkinUi(state)).toMatchObject({ label, disabled });
  });
});
