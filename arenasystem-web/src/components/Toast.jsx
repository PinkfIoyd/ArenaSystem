import { useEffect } from 'react';

function Toast({ mensagem, tipo = 'info', onClose }) {
  // Auto-fecha depois de 3 segundos
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const cores = {
    sucesso: 'bg-green-500',
    erro: 'bg-red-500',
    info: 'bg-blue-500',
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-slide-up">
      <div className={`${cores[tipo]} text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3`}>
        <span>{mensagem}</span>
        <button
          onClick={onClose}
          className="text-white hover:text-gray-200 text-xl leading-none"
        >
          ×
        </button>
      </div>
    </div>
  );
}

export default Toast;