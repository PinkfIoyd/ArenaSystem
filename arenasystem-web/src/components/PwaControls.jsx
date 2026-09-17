import { useEffect, useState } from 'react';

export default function PwaControls() {
  const [installPrompt, setInstallPrompt] = useState(null);
  const [updateRegistration, setUpdateRegistration] = useState(null);
  const [showIosHelp, setShowIosHelp] = useState(false);

  useEffect(() => {
    const onInstall = (event) => {
      event.preventDefault();
      setInstallPrompt(event);
    };
    const onUpdate = (event) => setUpdateRegistration(event.detail);
    window.addEventListener('beforeinstallprompt', onInstall);
    window.addEventListener('arenaflow:pwa-update', onUpdate);
    return () => {
      window.removeEventListener('beforeinstallprompt', onInstall);
      window.removeEventListener('arenaflow:pwa-update', onUpdate);
    };
  }, []);

  const standalone = window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone;
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
  if (standalone && !updateRegistration) return null;

  return (
    <>
      {updateRegistration && (
        <div className="fixed inset-x-3 bottom-24 z-[70] mx-auto flex max-w-md items-center justify-between gap-3 rounded-2xl bg-slate-950 p-4 text-sm text-white shadow-2xl">
          <span>Uma atualização do ArenaFlow está pronta.</span>
          <button type="button" className="rounded-lg bg-white px-3 py-2 font-bold text-slate-950" onClick={() => updateRegistration.waiting?.postMessage({ type: 'SKIP_WAITING' })}>Atualizar</button>
        </div>
      )}
      {!standalone && (installPrompt || ios) && (
        <div className="fixed bottom-24 right-3 z-50">
          <button
            type="button"
            className="rounded-full bg-teal-800 px-4 py-3 text-sm font-bold text-white shadow-xl"
            onClick={async () => {
              if (installPrompt) {
                await installPrompt.prompt();
                setInstallPrompt(null);
              } else setShowIosHelp(true);
            }}
          >
            Instalar app
          </button>
        </div>
      )}
      {showIosHelp && (
        <div className="fixed inset-0 z-[80] grid place-items-end bg-slate-950/50 p-4 sm:place-items-center" role="dialog" aria-modal="true" aria-label="Instalar no iPhone">
          <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-2xl">
            <h2 className="text-xl font-black text-slate-950">Instalar no iPhone</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">No Safari, toque em Compartilhar e depois em “Adicionar à Tela de Início”.</p>
            <button type="button" className="btn-primary mt-5 w-full" onClick={() => setShowIosHelp(false)}>Entendi</button>
          </div>
        </div>
      )}
    </>
  );
}
