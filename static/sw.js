const CACHE_NAME = 'iris-v7-cache-v2';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/css/iris-theme.css',
  '/static/js/iris-app.js',
  '/static/favicon_io/android-chrome-192x192.png',
  '/static/favicon_io/android-chrome-512x512.png',
  '/static/favicon_io/favicon.ico',
  '/static/favicon_io/apple-touch-icon.png',
  '/static/favicon_io/favicon-16x16.png',
  '/static/favicon_io/favicon-32x32.png',
  // ... existing entries ...
  '/static/css/fonts.css',
  '/static/fonts/inter-v20-latin/inter-v20-latin-300.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-300italic.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-500.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-500italic.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-600.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-600italic.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-700.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-700italic.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-regular.woff2',
  '/static/fonts/inter-v20-latin/inter-v20-latin-italic.woff2',
  '/static/fonts/fira-code-v27-latin/fira-code-v27-latin-300.woff2',
  '/static/fonts/fira-code-v27-latin/fira-code-v27-latin-regular.woff2',
  '/static/fonts/fira-code-v27-latin/fira-code-v27-latin-500.woff2',
  '/static/fonts/fira-code-v27-latin/fira-code-v27-latin-600.woff2',
  '/static/fonts/fira-code-v27-latin/fira-code-v27-latin-700.woff2'
];
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;

  // For API requests: network first, fallback to cache
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // For all other requests: cache first, fallback to network
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then(networkResponse => {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(request, responseClone);
          });
          return networkResponse;
        });
      })
  );
});