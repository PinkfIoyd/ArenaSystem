export function registerPwa() {
  if (!('serviceWorker' in navigator) || !import.meta.env.PROD) return;
  window.addEventListener('load', async () => {
    const registration = await navigator.serviceWorker.register('/sw.js');
    registration.addEventListener('updatefound', () => {
      const worker = registration.installing;
      worker?.addEventListener('statechange', () => {
        if (worker.state === 'installed' && navigator.serviceWorker.controller) {
          window.dispatchEvent(new CustomEvent('arenaflow:pwa-update', { detail: registration }));
        }
      });
    });
    navigator.serviceWorker.addEventListener('controllerchange', () => window.location.reload());
  });
}
