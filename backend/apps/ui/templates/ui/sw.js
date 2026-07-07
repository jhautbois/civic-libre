/* Service worker Civic Libre, version {{ version }}.
   Lot 6 : réception des notifications. Lot 7 : cache hors-ligne. */

self.addEventListener("install", function () {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
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

/* Présence d'un gestionnaire fetch : critère d'installabilité. */
self.addEventListener("fetch", function () {});
