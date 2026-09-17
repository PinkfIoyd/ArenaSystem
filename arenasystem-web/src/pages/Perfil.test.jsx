import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import api from '../api/client';
import Perfil from './Perfil';
import PerfilNotificacoes from './PerfilNotificacoes';

vi.mock('../api/client', () => ({ default: { get: vi.fn(), patch: vi.fn(), post: vi.fn() } }));
vi.mock('../components/Layout', () => ({ default: ({ children }) => <div>{children}</div> }));

describe('Perfil mobile', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('offers functional links for all four account areas', async () => {
    api.get.mockImplementation((url) => Promise.resolve({ data: url.includes('sessions') ? [] : { username: 'aluna', email: 'aluna@example.test' } }));
    render(<MemoryRouter><Perfil /></MemoryRouter>);
    expect(await screen.findByRole('link', { name: /Dados pessoais/ })).toHaveAttribute('href', '/app/perfil/dados');
    expect(screen.getByRole('link', { name: /^Notificações/ })).toHaveAttribute('href', '/app/perfil/notificacoes');
    expect(screen.getByRole('link', { name: /Privacidade e segurança/ })).toHaveAttribute('href', '/app/perfil/seguranca');
    expect(screen.getByRole('link', { name: /Sessões conectadas/ })).toHaveAttribute('href', '/app/perfil/sessoes');
  });

  it('loads and persists notification preferences', async () => {
    const preferences = {
      app_classes: true, app_checkins: true, app_financial: true, app_reservations: true,
      email_classes: true, email_checkins: true, email_financial: true, email_reservations: true,
    };
    api.get.mockResolvedValue({ data: preferences });
    api.patch.mockResolvedValue({ data: { ...preferences, app_checkins: false } });
    render(<MemoryRouter><PerfilNotificacoes /></MemoryRouter>);
    const toggles = await screen.findAllByRole('checkbox', { name: 'No aplicativo' });
    fireEvent.click(toggles[1]);
    fireEvent.click(screen.getByRole('button', { name: 'Salvar preferências' }));
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/auth/notification-preferences/', expect.objectContaining({ app_checkins: false })));
    expect(await screen.findByText('Preferências de notificações salvas.')).toBeInTheDocument();
  });
});
