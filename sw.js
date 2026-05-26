const APP_CACHE = 'turkey-2026-app-v2';
const TILE_CACHE = 'turkey-2026-tiles-v2';
const APP_SHELL = [
  './',
  './turkey_map.html',
  './manifest.webmanifest',
  './vendor/leaflet/leaflet.css',
  './vendor/leaflet/leaflet.js',
  './vendor/leaflet/images/layers.png',
  './vendor/leaflet/images/layers-2x.png',
  './vendor/leaflet/images/marker-icon.png',
  './vendor/leaflet/images/marker-icon-2x.png',
  './vendor/leaflet/images/marker-shadow.png',
  './turkey-route-2026.gpx',
  './turkey-route-2026.kml',
];

const TILE_HOSTS = [
  'tile.openstreetmap.org',
  'basemaps.cartocdn.com',
  'arcgisonline.com',
];

const EMPTY_TILE = '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#1e293b"/></svg>';

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(APP_CACHE)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key !== APP_CACHE && key !== TILE_CACHE)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

function isTileRequest(request) {
  const url = new URL(request.url);
  return TILE_HOSTS.some(host => url.hostname.includes(host));
}

async function handleTileRequest(event) {
  const cache = await caches.open(TILE_CACHE);
  const cached = await cache.match(event.request);
  if(cached) return cached;

  try {
    const response = await fetch(event.request);
    if(response.ok || response.type === 'opaque') {
      cache.put(event.request, response.clone());
    }
    return response;
  } catch {
    return new Response(EMPTY_TILE, {
      status: 200,
      headers: {'Content-Type': 'image/svg+xml', 'Cache-Control': 'no-store'},
    });
  }
}

async function handleAppRequest(event) {
  const cached = await caches.match(event.request);
  if(cached) return cached;

  try {
    const response = await fetch(event.request);
    if(response.ok) {
      const cache = await caches.open(APP_CACHE);
      cache.put(event.request, response.clone());
    }
    return response;
  } catch {
    if(event.request.mode === 'navigate') {
      return await caches.match('./turkey_map.html') ||
        new Response('Offline app shell is not cached yet.', {status: 503});
    }

    return new Response('Offline', {status: 503});
  }
}

self.addEventListener('fetch', event => {
  if(event.request.method !== 'GET') return;

  if(isTileRequest(event.request)) {
    event.respondWith(handleTileRequest(event));
    return;
  }

  event.respondWith(handleAppRequest(event));
});
