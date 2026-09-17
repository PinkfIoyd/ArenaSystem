import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PwaControls from './PwaControls';

describe('PwaControls', () => {
  beforeEach(() => {
    window.matchMedia = vi.fn(() => ({ matches: false }));
    Object.defineProperty(window.navigator, 'standalone', { configurable: true, value: false });
  });

  it('oferece a instalação quando o navegador disponibiliza o prompt', async () => {
    const prompt = vi.fn().mockResolvedValue(undefined);
    render(<PwaControls />);
    const event = new Event('beforeinstallprompt');
    Object.defineProperty(event, 'prompt', { value: prompt });
    fireEvent(window, event);
    fireEvent.click(await screen.findByRole('button', { name: 'Instalar app' }));
    expect(prompt).toHaveBeenCalledOnce();
  });
});
