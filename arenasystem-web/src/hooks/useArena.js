import { useEffect, useState } from 'react';
import api from '../api/client';

const DEFAULT_ARENA = {
  nome: 'ArenaFlow',
  logo: null,
  cor_primaria: '#0F766E',
  cor_secundaria: '#A3E635',
  cor_fundo: '#ECFEFF',
  cor_texto: '#071B26',
};

const LEGACY_PRIMARY_COLORS = new Set(['#123b5d']);
const LEGACY_SECONDARY_COLORS = new Set(['#111827', '#1f2937', '#22c55e']);

function normalizeHex(value) {
  return String(value || '').trim().toLowerCase();
}

function hexToRgb(hexValue) {
  const hex = normalizeHex(hexValue);
  if (!/^#[0-9a-f]{6}$/.test(hex)) return null;
  return {
    red: Number.parseInt(hex.slice(1, 3), 16),
    green: Number.parseInt(hex.slice(3, 5), 16),
    blue: Number.parseInt(hex.slice(5, 7), 16),
  };
}

function contrastText(hexValue) {
  const rgb = hexToRgb(hexValue);
  if (!rgb) return '#FFFFFF';
  const yiq = (rgb.red * 299 + rgb.green * 587 + rgb.blue * 114) / 1000;
  return yiq >= 150 ? '#071B26' : '#FFFFFF';
}

function isRetiredWarmTone(value) {
  const hex = normalizeHex(value);
  if (!/^#[0-9a-f]{6}$/.test(hex)) return false;
  const red = Number.parseInt(hex.slice(1, 3), 16);
  const green = Number.parseInt(hex.slice(3, 5), 16);
  const blue = Number.parseInt(hex.slice(5, 7), 16);
  return red > 220 && green >= 80 && green <= 180 && blue < 80;
}

function normalizeArena(data = {}) {
  const nome = /arenasystem/i.test(data.nome || '') ? DEFAULT_ARENA.nome : data.nome;
  const primary = normalizeHex(data.cor_primaria);
  const secondary = normalizeHex(data.cor_secundaria);

  return {
    ...DEFAULT_ARENA,
    ...data,
    nome: nome || DEFAULT_ARENA.nome,
    cor_primaria: LEGACY_PRIMARY_COLORS.has(primary) || isRetiredWarmTone(primary) ? DEFAULT_ARENA.cor_primaria : (data.cor_primaria || DEFAULT_ARENA.cor_primaria),
    cor_secundaria: LEGACY_SECONDARY_COLORS.has(secondary) ? DEFAULT_ARENA.cor_secundaria : (data.cor_secundaria || DEFAULT_ARENA.cor_secundaria),
  };
}

function applyTheme(arena) {
  const root = document.documentElement;
  const primary = arena.cor_primaria || DEFAULT_ARENA.cor_primaria;
  const secondary = arena.cor_secundaria || DEFAULT_ARENA.cor_secundaria;
  const bg = arena.cor_fundo || DEFAULT_ARENA.cor_fundo;
  const text = arena.cor_texto || DEFAULT_ARENA.cor_texto;

  root.style.setProperty('--arena-primary', primary);
  root.style.setProperty('--arena-secondary', secondary);
  root.style.setProperty('--arena-bg', bg);
  root.style.setProperty('--arena-text', text);
  root.style.setProperty('--arena-on-primary', contrastText(primary));
  root.style.setProperty('--arena-on-secondary', contrastText(secondary));
  root.style.setProperty('--admin-accent', primary);
  root.style.setProperty('--admin-on-accent', contrastText(primary));
}

export function useArena() {
  const [arena, setArena] = useState(DEFAULT_ARENA);

  useEffect(() => {
    let mounted = true;

    function carregarArena() {
      api.get('/arena/atual/')
      .then(({ data }) => {
        if (!mounted) return;
        const nextArena = normalizeArena(data);
        setArena(nextArena);
        applyTheme(nextArena);
      })
      .catch(() => {
        if (mounted) setArena(DEFAULT_ARENA);
        applyTheme(DEFAULT_ARENA);
      });
    }

    carregarArena();
    window.addEventListener('arena-context-changed', carregarArena);

    return () => {
      mounted = false;
      window.removeEventListener('arena-context-changed', carregarArena);
    };
  }, []);

  return arena;
}

export default useArena;
