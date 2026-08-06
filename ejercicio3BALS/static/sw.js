const CACHE_NAME = 'hotelz-pwa-v1';
const OFFLINE_URL = '/offline/';

const PRECACHE_ASSETS = [
  '/',
  OFFLINE_URL,
  '/static/manifest.json',
  '/static/assets/vendor/bootstrap/css/bootstrap.min.css',
  '/static/assets/vendor/bootstrap-icons/bootstrap-icons.css',
  '/static/assets/css/main.css',
  '/static/assets/vendor/bootstrap/js/bootstrap.bundle.min.js',
  '/static/assets/js/main.js',
  '/static/assets/img/pwa/icon-192x192.png',
  '/static/assets/img/pwa/icon-512x512.png',
  '/static/assets/img/pwa/favicon-pwa.png'
];

// Instalación del Service Worker: Precachear recursos clave
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pre-caching offline fallback and key assets');
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[Service Worker] Some assets failed to precache:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activación del Service Worker: Limpiar cachés antiguos y reclamar clientes
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Estrategia de Fetch
self.addEventListener('fetch', (event) => {
  const request = event.request;

  // Solo manejar peticiones GET
  if (request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);

  // Peticiones de Navegación (HTML Pages): Network First, fallback to cache, fallback to offline.html
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return networkResponse;
        })
        .catch(async () => {
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            return cachedResponse;
          }
          const offlinePage = await caches.match(OFFLINE_URL);
          return offlinePage || new Response('Sin conexión a Internet', {
            status: 503,
            statusText: 'Offline',
            headers: { 'Content-Type': 'text/html; charset=utf-8' }
          });
        })
    );
    return;
  }

  // Peticiones estáticas (CSS, JS, imágenes, fuentes): Cache First con actualización en segundo plano
  if (
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'image' ||
    request.destination === 'font' ||
    url.pathname.startsWith('/static/')
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const fetchPromise = fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => cache.put(request, networkResponse.clone()));
          }
          return networkResponse;
        }).catch(() => {
          // Ignorar errores de red para elementos estáticos cuando se recuperan de caché
        });

        return cachedResponse || fetchPromise;
      })
    );
    return;
  }

  // Por defecto, intentar red y fallback a caché
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});
