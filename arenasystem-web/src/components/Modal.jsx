import { useEffect, useId, useRef } from 'react';

function Modal({ aberto, onFechar, titulo, children, tamanho = 'md' }) {
  const titleId = useId();
  const panelRef = useRef(null);
  useEffect(() => {
    if (!aberto) return undefined;

    const handleEsc = (event) => {
      if (event.key === 'Escape') onFechar();
    };

    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [aberto, onFechar]);

  useEffect(() => {
    if (!aberto) return undefined;

    const previousFocus = document.activeElement;
    const focusTimer = window.setTimeout(() => panelRef.current?.querySelector('input, textarea, select, button')?.focus(), 0);
    const overflowAnterior = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.clearTimeout(focusTimer);
      document.body.style.overflow = overflowAnterior;
      previousFocus?.focus?.();
    };
  }, [aberto]);

  if (!aberto) return null;

  const tamanhos = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-fade-in">
      <button
        type="button"
        className="fixed inset-0 cursor-default"
        onClick={onFechar}
        aria-label="Fechar modal"
      />

      <div
        ref={panelRef}
        className={`relative z-10 flex max-h-[90vh] w-full ${tamanhos[tamanho] || tamanhos.md} flex-col rounded-xl bg-white shadow-2xl animate-slide-up`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titulo ? titleId : undefined}
      >
        {titulo && (
          <div className="flex items-center justify-between border-b border-gray-200 p-5">
            <h2 id={titleId} className="text-xl font-bold text-gray-800">{titulo}</h2>
            <button
              type="button"
              onClick={onFechar}
              className="text-2xl leading-none text-gray-400 transition hover:text-gray-700"
              title="Fechar"
            >
              x
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-5">{children}</div>
      </div>
    </div>
  );
}

export default Modal;
