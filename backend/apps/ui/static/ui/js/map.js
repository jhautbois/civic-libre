/* Carte du formulaire de signalement : amélioration progressive.
   Sans JavaScript, le formulaire fonctionne par adresse (RGAA).
   Placement par simple appui, jamais de glisser-déposer (docs/design.md). */

(function () {
  "use strict";

  var bloc = document.getElementById("carte-bloc");
  var config = document.getElementById("map-config");
  if (!bloc || !config || typeof L === "undefined") {
    return;
  }

  var latInput = document.querySelector('input[name="latitude"]');
  var lonInput = document.querySelector('input[name="longitude"]');
  var resolved = document.getElementById("adresse-resolue");
  var addressInput = document.querySelector('input[name="address"]');

  bloc.hidden = false;

  var map = L.map("carte", { zoomControl: true }).setView(
    [parseFloat(config.dataset.lat), parseFloat(config.dataset.lon)],
    parseInt(config.dataset.zoom, 10)
  );

  L.tileLayer("/tuiles/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  var marker = null;

  function setPoint(latlng) {
    if (marker) {
      marker.setLatLng(latlng);
    } else {
      marker = L.marker(latlng).addTo(map);
    }
    latInput.value = latlng.lat.toFixed(6);
    lonInput.value = latlng.lng.toFixed(6);
    resolved.textContent = "Recherche de l'adresse…";
    fetch("/api/adresse-inverse?lat=" + latlng.lat + "&lon=" + latlng.lng)
      .then(function (r) { return r.ok ? r.json() : { label: "" }; })
      .then(function (data) {
        if (data.label) {
          resolved.textContent = "Adresse repérée : " + data.label;
          if (addressInput && !addressInput.value) {
            addressInput.value = data.label;
          }
        } else {
          resolved.textContent = "Point placé (adresse non trouvée, précisez si besoin).";
        }
      })
      .catch(function () {
        resolved.textContent = "Point placé.";
      });
  }

  map.on("click", function (event) {
    setPoint(event.latlng);
  });

  var locate = document.getElementById("ma-position");
  if (locate && "geolocation" in navigator) {
    locate.addEventListener("click", function () {
      locate.disabled = true;
      locate.textContent = "Recherche de votre position…";
      navigator.geolocation.getCurrentPosition(
        function (position) {
          var latlng = L.latLng(position.coords.latitude, position.coords.longitude);
          map.setView(latlng, 17);
          setPoint(latlng);
          locate.disabled = false;
          locate.textContent = "ou utilisez ma position";
        },
        function () {
          locate.disabled = false;
          locate.textContent = "Position indisponible, touchez la carte";
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    });
  } else if (locate) {
    locate.hidden = true;
  }
})();
