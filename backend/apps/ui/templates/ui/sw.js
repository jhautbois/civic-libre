/* Service worker Civic Libre, version {{ version }}.
   Notifications push + hors-ligne de base (docs/design.md). */

var CACHE = "civic-v{{ version }}";
var PRECACHE = ["/", "/hors-ligne/"];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return cache.addAll(PRECACHE);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (key) {
        return key !== CACHE;
      }).map(function (key) {
        return caches.delete(key);
      }));
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener("push", function (event) {
  var data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { title: "Nouvelle information de la mairie" };
  }
  event.waitUntil(
    self.registration.showNotification(data.title || "Mairie", {
      body: data.body || "",
      data: { url: data.url || "/" },
      icon: "/icone-192.png",
      badge: "/icone-192.png",
      lang: "fr"
    })
  );
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  var url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(function (windows) {
      for (var i = 0; i < windows.length; i++) {
        if ("focus" in windows[i]) {
          windows[i].navigate(url);
          return windows[i].focus();
        }
      }
      return self.clients.openWindow(url);
    })
  );
});

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") {
    return;
  }
  var url = new URL(request.url);
  if (url.origin !== self.location.origin) {
    return;
  }

  /* Navigation : réseau d'abord, page hors-ligne en secours. */
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(function () {
        return caches.match(request).then(function (cached) {
          return cached || caches.match("/hors-ligne/");
        });
      })
    );
    return;
  }

  /* Statiques (empreintés) et icônes : cache d'abord. */
  if (url.pathname.indexOf("/static/") === 0 || url.pathname.indexOf("/icone-") === 0) {
    event.respondWith(
      caches.match(request).then(function (cached) {
        if (cached) {
          return cached;
        }
        return fetch(request).then(function (response) {
          if (response.ok) {
            var copy = response.clone();
            caches.open(CACHE).then(function (cache) {
              cache.put(request, copy);
            });
          }
          return response;
        });
      })
    );
  }
});
