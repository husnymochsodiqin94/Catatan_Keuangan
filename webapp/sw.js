/* Service worker: cache app shell (offline-capable shell), network-first untuk /api. */
const CACHE = "ck-shell-v1";
const SHELL = ["./", "./index.html", "./styles.css", "./app.js", "./manifest.webmanifest", "./icon.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // API: selalu jaringan (data tak boleh basi); jangan cache.
  if (url.pathname.startsWith("/api/")) return;
  // Shell: cache-first, fallback jaringan; navigasi fallback ke index.
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).catch(() => caches.match("./index.html")))
  );
});
