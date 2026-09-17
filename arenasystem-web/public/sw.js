const VERSION = 'arenaflow-shell-v2';
const SHELL = ['/offline.html', '/manifest.webmanifest', '/pwa-icon.svg', '/pwa-icon-192.png', '/pwa-icon-512.png', '/favicon.svg'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(VERSION).then((cache) => cache.addAll(SHELL)));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== VERSION).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.pathname.startsWith('/api/') || request.headers.has('authorization')) return;

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/offline.html')));
    return;
  }

  const versionedAsset = url.origin === self.location.origin
    && url.pathname.startsWith('/assets/')
    && ['script', 'style', 'image', 'font'].includes(request.destination);
  if (versionedAsset) {
    event.respondWith(caches.match(request).then((cached) => cached || fetch(request).then((response) => {
      if (response.ok) caches.open(VERSION).then((cache) => cache.put(request, response.clone()));
      return response;
    })));
  }
});
