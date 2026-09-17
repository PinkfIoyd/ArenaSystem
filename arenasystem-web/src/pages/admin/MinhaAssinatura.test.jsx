import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import MinhaAssinatura from './MinhaAssinatura';

vi.mock('../../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }));
import api from '../../api/client';

const subscription = {
  id: 1, status: 'active', billing_cycle: 'monthly', trial_ends_at: null,
  current_period_end: '2026-09-06T12:00:00Z', grace_ends_at: null,
  plan: { id: 1, code: 'pro', name: 'Professional', description: 'Plano profissional' },
  pending_plan: null, usage: { admins: 2, professors: 3, students: 50, courts: 2, storage_mb: 0 },
  limits: { admins: 5, professors: 10, students: 100, courts: 4, storage_mb: 512 },
};

describe('Minha assinatura', () => {
  beforeEach(() => {
    api.get.mockImplementation((url) => {
      if (url === '/subscription/') return Promise.resolve({ data: subscription });
      if (url === '/saas/plans/') return Promise.resolve({ data: [] });
      return Promise.resolve({ data: [] });
    });
  });

  it('shows plan, usage and empty billing history', async () => {
    render(<MinhaAssinatura />);
    expect(await screen.findByText('Professional')).toBeInTheDocument();
    expect(screen.getByText('50/100')).toBeInTheDocument();
    expect(screen.getByText('Nenhuma cobranca registrada.')).toBeInTheDocument();
  });
});

