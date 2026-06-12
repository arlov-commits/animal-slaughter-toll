/* Service worker — makes the memorial installable and fully offline.

   The page is the whole site; it fetches data.json at runtime. We pre-cache
   that shell on install and serve it offline. The HTML is always loaded as a
   fresh navigation (from cache or network), so the inline script reruns and
   "since you opened this page" still resets every time the app is reopened.

   Caches are versioned: bump VERSION together with the page version on every
   change so installed clients pick up the new shell (old caches are purged on
   activate). Online visits also refresh the cached HTML and data, so network
   users are never stuck on a stale copy even if VERSION is unchanged. */

var VERSION = 'v3.3';
var SHELL = 'astc-shell-' + VERSION;
var RUNTIME = 'astc-runtime-' + VERSION;

var SHELL_ASSETS = [
  './', './index.html', './data.json', './manifest.webmanifest',
  './favicon.svg', './favicon-32.png', './apple-touch-icon.png',
  './icon-192.png', './icon-512.png', './icon-maskable-512.png'
];

self.addEventListener('install', function(e){
  e.waitUntil(
    caches.open(SHELL)
      .then(function(c){ return c.addAll(SHELL_ASSETS); })
      .then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.map(function(k){
        if(k !== SHELL && k !== RUNTIME) return caches.delete(k);
      }));
    }).then(function(){ return self.clients.claim(); })
  );
});

function cachePut(cacheName, req, res){
  if(res && (res.ok || res.type === 'opaque')){
    var copy = res.clone();
    caches.open(cacheName).then(function(c){ c.put(req, copy); });
  }
  return res;
}

function networkFirst(req, cacheName){
  return fetch(req)
    .then(function(res){ return cachePut(cacheName, req, res); })
    .catch(function(){
      return caches.match(req).then(function(m){ return m || Promise.reject(new Error('offline')); });
    });
}

function cacheFirst(req, cacheName){
  return caches.match(req).then(function(m){
    return m || fetch(req).then(function(res){ return cachePut(cacheName, req, res); });
  });
}

self.addEventListener('fetch', function(e){
  var req = e.request;
  if(req.method !== 'GET') return;
  var url = new URL(req.url);

  // App navigations: network-first, fall back to the cached page when offline.
  if(req.mode === 'navigate'){
    e.respondWith(
      fetch(req)
        .then(function(res){ return cachePut(SHELL, './index.html', res); })
        .catch(function(){
          return caches.match(req).then(function(m){ return m || caches.match('./index.html'); });
        })
    );
    return;
  }

  // Live data: prefer the network, fall back to the last cached copy offline.
  if(url.origin === self.location.origin && /(^|\/)data\.json$/.test(url.pathname)){
    e.respondWith(networkFirst(req, SHELL));
    return;
  }

  // Other same-origin shell assets (icons, manifest): cache-first.
  if(url.origin === self.location.origin){
    e.respondWith(cacheFirst(req, SHELL));
    return;
  }

  // Web font (Google Fonts): cache-first so the exact face works offline too.
  if(url.host === 'fonts.googleapis.com' || url.host === 'fonts.gstatic.com'){
    e.respondWith(cacheFirst(req, RUNTIME));
    return;
  }

  // Everything else: leave to the browser.
});
