/* Abonnement Web Push : opt-in explicite, sujets choisis, désabonnement
   en un geste. Amélioration progressive : sans support, un message
   oriente vers l'installation PWA (iOS) ou les flux. */

(function () {
  "use strict";

  var ui = document.getElementById("push-ui");
  var unsupported = document.getElementById("push-non-supporte");
  if (!ui) {
    return;
  }

  var supported = "serviceWorker" in navigator && "PushManager" in window &&
    "Notification" in window;
  if (!supported) {
    if (unsupported) unsupported.hidden = false;
    return;
  }
  ui.hidden = false;

  var stateLine = document.getElementById("push-etat");
  var subscribeBtn = document.getElementById("push-abonner");
  var unsubscribeBtn = document.getElementById("push-desabonner");

  function csrfToken() {
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? match[1] : "";
  }

  function topics() {
    return Array.prototype.slice
      .call(document.querySelectorAll('input[name="sujet"]:checked'))
      .map(function (input) { return input.value; });
  }

  function b64ToUint8(base64) {
    var padding = "=".repeat((4 - (base64.length % 4)) % 4);
    var raw = atob((base64 + padding).replace(/-/g, "+").replace(/_/g, "/"));
    var output = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; ++i) output[i] = raw.charCodeAt(i);
    return output;
  }

  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: JSON.stringify(body)
    });
  }

  function setState(message, subscribed) {
    stateLine.textContent = message;
    subscribeBtn.textContent = subscribed ? "Mettre à jour mes choix" : "Activer les notifications";
    unsubscribeBtn.hidden = !subscribed;
  }

  function refresh() {
    navigator.serviceWorker.register("/sw.js").then(function (registration) {
      return registration.pushManager.getSubscription();
    }).then(function (subscription) {
      if (subscription) {
        setState("Notifications activées sur cet appareil.", true);
      } else {
        setState("Notifications non activées sur cet appareil.", false);
      }
    });
  }

  subscribeBtn.addEventListener("click", function () {
    Notification.requestPermission().then(function (permission) {
      if (permission !== "granted") {
        setState("Vous avez refusé les notifications. Vous pouvez changer d'avis dans les réglages du navigateur.", false);
        return;
      }
      navigator.serviceWorker.register("/sw.js").then(function (registration) {
        return fetch("/api/push/cle").then(function (r) { return r.json(); }).then(function (data) {
          return registration.pushManager.getSubscription().then(function (existing) {
            return existing || registration.pushManager.subscribe({
              userVisibleOnly: true,
              applicationServerKey: b64ToUint8(data.cle_publique)
            });
          });
        });
      }).then(function (subscription) {
        var json = subscription.toJSON();
        return post("/api/push/abonnement", {
          endpoint: subscription.endpoint,
          keys: json.keys,
          topics: topics()
        });
      }).then(function (response) {
        if (response.ok) {
          setState("C'est fait : vous recevrez les notifications choisies.", true);
        } else {
          setState("L'abonnement a échoué. Réessayez dans un instant.", false);
        }
      }).catch(function () {
        setState("L'abonnement a échoué. Réessayez dans un instant.", false);
      });
    });
  });

  unsubscribeBtn.addEventListener("click", function () {
    navigator.serviceWorker.ready.then(function (registration) {
      return registration.pushManager.getSubscription();
    }).then(function (subscription) {
      if (!subscription) return null;
      var endpoint = subscription.endpoint;
      return subscription.unsubscribe().then(function () {
        return post("/api/push/desabonnement", { endpoint: endpoint });
      });
    }).then(function () {
      setState("Notifications désactivées sur cet appareil.", false);
    });
  });

  refresh();
})();
