import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

function memoryStorage() {
  let values = {};
  return {
    getItem: (key) => values[key] ?? null,
    setItem: (key, value) => { values[key] = String(value); },
    removeItem: (key) => { delete values[key]; },
    clear: () => { values = {}; },
  };
}

Object.defineProperty(window, 'localStorage', { configurable: true, value: memoryStorage() });
Object.defineProperty(window, 'sessionStorage', { configurable: true, value: memoryStorage() });

afterEach(() => {
  cleanup();
  localStorage.clear();
  sessionStorage.clear();
});
