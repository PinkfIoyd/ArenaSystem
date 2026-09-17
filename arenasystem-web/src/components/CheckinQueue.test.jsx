import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import CheckinQueue from './CheckinQueue';
import api from '../api/client';

vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() } }));

describe('CheckinQueue', () => {
  it('confirma selecionados sem recarregar a página', async () => {
    api.get.mockResolvedValue({ data: [{ id: 7, aluno_nome: 'Aluno Teste', aluno_foto: null, turma: 3, turma_nome: 'Turma A', professor_nome: 'Prof A', horario_previsto: '18:00:00', solicitado_em: '2026-08-10T20:40:00Z', status: 'pending', inadimplente_no_momento: false }] });
    api.post.mockResolvedValue({ data: { confirmed: 1, requested: 1 } });
    render(<CheckinQueue />);
    expect(await screen.findByText('Aluno Teste')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar selecionados' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/checkins/bulk-confirm/', { ids: [7] }));
    expect(window.location.pathname).toBe('/');
  });
});
