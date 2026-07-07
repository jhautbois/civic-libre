/* Enregistrement du service worker sur toutes les pages :
   installabilité PWA et page hors-ligne, indépendamment de
   l'abonnement aux notifications. */

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(function () {
    /* hors ligne ou navigateur restreint : sans conséquence */
  });
}
