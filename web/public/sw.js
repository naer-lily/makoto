/*
 * makoto PWA service worker.
 *
 * Strategy summary:
 * - `/api/` is network-only: never read from, never written to a cache.
 * - Navigations are network-first and fall back to the cached index.html.
 * - The app shell (index.html, all hashed CSS/JS from build's sw-assets.json,
 *   manifest, icons) is precached during install and served cache-first.
 *
 * Bump CACHE_VERSION whenever the shell behaviour or static shell list changes.
 */
const CACHE_VERSION = 'v1'
const CACHE_PREFIX = 'makoto-shell-'
const CACHE_NAME = `${CACHE_PREFIX}${CACHE_VERSION}`

const APP_SHELL = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/maskable-192.png',
  '/icons/maskable-512.png',
  '/icons/apple-touch-icon-180.png',
]

function isApiRequest(url) {
  return url.pathname.startsWith('/api/')
}

function isCacheableAsset(url) {
  return (
    url.pathname.startsWith('/assets/') ||
    url.pathname.startsWith('/icons/') ||
    url.pathname === '/manifest.webmanifest'
  )
}

async function cacheBuildAssets() {
  const cache = await caches.open(CACHE_NAME)
  try {
    // The Vite build emits every hashed JS/CSS chunk (including lazy routes).
    const manifestResponse = await fetch('/sw-assets.json', { cache: 'no-cache' })
    if (manifestResponse.ok) {
      const assets = await manifestResponse.json()
      await Promise.allSettled(assets.map((asset) => cache.add(asset)))
      return
    }
  } catch {
    // Fall through to discovering the entry assets from index.html.
  }

  try {
    const response = await fetch('/index.html', { cache: 'no-cache' })
    if (!response.ok) return
    const html = await response.text()
    const assets = new Set()
    const attrPattern = /(?:src|href)="(\/assets\/[^"]+)"/g
    let match
    while ((match = attrPattern.exec(html)) !== null) {
      assets.add(match[1])
    }
    await Promise.allSettled([...assets].map((asset) => cache.add(asset)))
  } catch {
    // Build assets are an optimization; the shell still works if this fails.
  }
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME)
      await Promise.allSettled(APP_SHELL.map((url) => cache.add(url)))
      await cacheBuildAssets()
      await self.skipWaiting()
    })(),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys()
      await Promise.all(
        keys
          .filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
          .map((key) => caches.delete(key)),
      )
      await self.clients.claim()
    })(),
  )
})

async function matchIgnoringVary(cache, request) {
  const cached = await cache.match(request, { ignoreVary: true })
  if (cached) return cached
  // Requests with a crossorigin attribute carry an Origin header while the
  // precached copy may not. Fall back to a pathname-only match.
  const url = typeof request === 'string' ? request : new URL(request.url).pathname
  return cache.match(url, { ignoreVary: true })
}

async function networkFirstNavigation(event) {
  const cache = await caches.open(CACHE_NAME)
  try {
    const response = await fetch(event.request)
    if (response.ok) {
      cache.put(event.request, response.clone())
    }
    return response
  } catch {
    const cached =
      (await matchIgnoringVary(cache, event.request)) ||
      (await cache.match('/index.html', { ignoreVary: true })) ||
      (await cache.match('/', { ignoreVary: true }))
    return (
      cached ||
      new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } })
    )
  }
}

async function cacheFirstAsset(event) {
  const cache = await caches.open(CACHE_NAME)
  const cached = await matchIgnoringVary(cache, event.request)
  if (cached) return cached
  const response = await fetch(event.request)
  if (response.ok) {
    cache.put(event.request, response.clone())
  }
  return response
}

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return

  // API traffic must always hit the network. Do not call respondWith().
  if (isApiRequest(url)) return

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(event))
    return
  }

  if (isCacheableAsset(url)) {
    event.respondWith(cacheFirstAsset(event))
  }
})
