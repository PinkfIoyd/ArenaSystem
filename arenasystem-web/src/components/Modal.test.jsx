import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import Modal from './Modal';

describe('Modal', () => {
  it('exposes dialog semantics and closes with Escape', () => {
    const close = vi.fn();
    render(<Modal aberto onFechar={close} titulo="Confirmar acesso"><input aria-label="Motivo" /></Modal>);
    expect(screen.getByRole('dialog', { name: 'Confirmar acesso' })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(close).toHaveBeenCalledOnce();
  });
});

