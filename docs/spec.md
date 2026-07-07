# Civic Libre : spécification

Statut : spécification v2, VALIDÉE le 7 juillet 2026. Issue de la phase 0 (état de l'art sourcé), de la phase 1 (rédaction) et de la phase 2 (revue adverse par 7 agents indépendants, 61 constats, corrections intégrées). Voir aussi docs/etat-de-l-art.md, docs/architecture.md, docs/design.md et docs/adr/.

## Contexte

Projet personnel de R&D en logiciel libre, hors mandat électif. Objectif : une application citoyenne municipale libre, clé en main, pour une commune française d'environ 7 000 habitants sans service informatique, avec le maximum de réutilisation de briques libres existantes.

Trois besoins : agenda communal avec notifications, signalement de problèmes (photo, géolocalisation, catégorie), back-office léger pour les agents (saisie unique multicanal, signalements triés et routés, statuts).

Standards imposés : iCal, RSS, Open311 GeoReport v2, Web Push avec VAPID. Contraintes : AGPL-3.0 par défaut, auto-hébergeable en UE, RGPD, RGAA, français, `docker compose up` suffisant pour une démo, PWA mobile d'abord.

## Phase 0 : état de l'art sourcé (7 juillet 2026)

Méthode : 9 recherches web parallèles (une par candidat ou domaine) puis vérification adverse par des agents indépendants chargés de réfuter chaque affirmation décisive aux sources primaires (dépôts Git, RFC, CNIL, sites officiels) ; environ 580 consultations de sources, complétées en phase 2 par 7 relectures adverses de la présente spec. Les fiches complètes et leurs URL seront versées au dépôt (docs/etat-de-l-art.md) en phase 3.

### Verdicts par candidat

| Candidat | Licence | État vérifié | Verdict |
|---|---|---|---|
| Communecter (Open Atlas) | Apache-2.0 | Vivant sur GitLab Adullact (commit 06/07/2026) mais stack en fin de vie (PHP 7, Yii 1, MongoDB 3.6), iCal jamais implémenté (fichier vide), aucun Open311, aucun Web Push, mobile abandonné depuis 2018, déploiement en ~15 dépôts couplés | Écarter |
| DirectMairie (ADULLACT) | AGPL-3.0 | Gel fonctionnel depuis 09/2023 (activité restante : bots), instance mutualisée hors ligne au 07/07/2026, retiré de la liste des services ADULLACT ; signalement sans Open311, sans statut « en cours », sans routage par service | Écarter comme base, garder comme référence UX et modèle de données |
| FixMyStreet (mySociety) | AGPL-3.0 | Très actif (commit 06/07/2026), référence mondiale du signalement, Open311 client complet et serveur partiel ; mais Perl/Catalyst (compétences rares en France), traduction française figée en 2021 (~70 %), aucun agenda, aucun Web Push, dépendance MapIt | Écarter comme base (coût de maintenance), reprendre ses extensions Open311 (updates, statuts étendus) |
| Mark-a-Spot (Civic Patches) | GPL-2.0+ | Très actif (release 11.9.0 du 26/06/2026), serveur Open311 GeoReport v2 libre complet, vivant et distribué comme produit signalement, back-office avec routage et statuts ; mais Drupal 11 + frontend Nuxt à opérer, quasi mono-mainteneur en open core, hors politique de sécurité drupal.org, aucune référence française, ni agenda ni Web Push confirmé | Non retenu, documenté comme plan B sérieux |
| CitéLibre / Lutece / DansMaRue (Ville de Paris) | BSD-3-Clause (Lutece) | Lutece actif (push 30/06/2026), DansMaRue publié mais back-office sans push depuis 04/2024 et sans licence détectée sur les plugins ; stack Java/Tomcat multi-dépôts dimensionnée grande ville, pas d'Open311, pas de Web Push, pas d'agenda événementiel packagé, copyleft faible | Écarter (charge d'exploitation disproportionnée, standards absents) |
| Publik (Entr'ouvert) | AGPL-3.0 | Plateforme GRC libre la plus déployée en France (21 collectivités au Comptoir du Libre), portail citoyen et agents ; mais architecture multi-services (plusieurs briques Django interconnectées) pensée pour un opérateur ou une mutualisation, pas d'Open311, pas de Web Push grand public, agenda orienté rendez-vous et non événements publics | Écarter pour une commune isolée de 7 000 habitants ; pertinent si un opérateur mutualisé s'en saisit |
| uReport (City of Bloomington) | AGPL-3.0 | Vivant (release 2.3.1 du 04/06/2026), CRM avec endpoint GeoReport v2 visant les petites villes ; PHP + MySQL + Solr, anglophone, ni agenda ni push, communauté quasi nulle hors Bloomington | Écarter (localisation et maintenance), il retire toutefois à Mark-a-Spot l'exclusivité du serveur Open311 vivant |
| Decidim / CONSUL | AGPL-3.0 | Très actifs (v0.32.0 et 2.5.1, 2026) mais centrés participation ; aucun Open311 ; charge Rails disproportionnée (breaking changes, migration documentée en 6 mois) ; écosystème français Decidim en recomposition (rachat d'OSP par Go Vocal, 03/2026) | Écarter pour ce périmètre (Decidim possible plus tard, en SaaS, pour un budget participatif) |
| Gancio (underscore hacklab) | AGPL-3.0 | Actif : v1.28.2 du 14/12/2025 (dernière stable 1.x, vérifiée à la source le 07/07/2026 sur l'API Framagit), v2 en alpha/bêta ; agenda local pensé pour une ville : iCal et RSS natifs vérifiés en production, saisie anonyme modérée (associations), récurrences, français complet, image docker officielle, SQLite | Adopter tel quel pour la saisie et la modération de l'agenda |
| 6aika/issue-reporting (Helsinki) | MIT | Serveur GeoReport v2 en Django, mort depuis 2020 ; preuve que l'écart Open311 en Django existe et n'est plus couvert | Écarter (abandonné), conforte l'écriture du cœur |
| Briques notifications | MIT/MPL/AGPL | Web Push VAPID : standard IETF réel (RFC 8030, 8291, 8292), pywebpush actif (2.3.0, 02/2026, mono-mainteneur) ; django-push-notifications (Jazzband) évalué : modèle WebPushDevice sans sujets ni purge 404/410, apport insuffisant pour justifier la dépendance ; ntfy et Gotify inadaptés au grand public ; listmonk (AGPL, UI française) pertinent pour le courriel en masse, hors MVP | Web Push intégré au cœur via pywebpush ; listmonk documenté en option |

### Benchmark des applications propriétaires (parité à égaler)

PanneauPocket (~14 500 collectivités), IntraMuros (~8 000), Illiwap (~3 000), CityAll, Mon Village. Socle commun : actualités avec push, alertes urgentes, agenda, signalement photo + géolocalisation avec suivi, annuaire. Qualité perçue : zéro friction (pas de compte, anonymat, gratuité), push fiable maîtrisé par abonnement, simplicité radicale (fil unique de cartes, pastilles de statut), back-office « mairie sans informaticien », hébergement France affiché. Budget à 7 000 habitants : environ 700 à 1 500 €/an, opaque au delà de 3 000 habitants.

Failles exploitables par une alternative libre : accessibilité RGAA quasi absente (seul IntraMuros publie une déclaration, 98,18 % RGAA 4.1), aucun standard ouvert (ni iCal, ni Open311), pas de PWA installable (dépendance totale aux stores), verrouillage des données.

### Standards et obligations (contraintes de la spec)

- Open311 GeoReport v2 : standard figé (wiki inactif depuis 2022) mais interopérabilité de fait ; XML obligatoire, JSON optionnel ; statuts limités à `open` et `closed` ; un fichier de service discovery est requis par le standard. Les statuts riches viennent de deux extensions FixMyStreet distinctes : `GET servicerequestupdates` (historique horodaté) et « Additional states » (statuts étendus dont IN_PROGRESS et FIXED).
- iCal : RFC 5545 (UID stables obligatoires ; VTIMEZONE requis seulement si TZID est utilisé ; pliage à 75 octets recommandé) plus RFC 7986 (NAME, SOURCE, REFRESH-INTERVAL, souhaitables pour un calendrier public).
- RSS 2.0 : Best Practices Profile (guid permalien stable, pubDate RFC 822).
- Web Push : TTL obligatoire (RFC 8030), VAPID ES256 sans compte tiers (RFC 8292), chiffrement aes128gcm ~4 Ko (RFC 8291), HTTPS requis ; sur iOS (≥ 16.4) uniquement PWA installée sur l'écran d'accueil, permission sur geste utilisateur explicite.
- RGAA 4.1.2 en vigueur (v5 attendue fin 2026), applicable sans seuil de taille : conformité, déclaration d'accessibilité, schéma pluriannuel, mention en page d'accueil ; contrôle Arcom, jusqu'à 50 000 € par service renouvelables. La mention « partiellement conforme » exige un audit effectif (auto-évaluation admise) établissant au moins 50 % des critères ; sans audit, la seule mention légale est « non conforme ».
- RGPD : mission d'intérêt public (art. 6.1.e) pour le signalement, consentement (6.1.a) pour le push ; l'intérêt légitime (6.1.f) est indisponible pour une autorité publique ; DPO obligatoire même à 7 000 habitants (mutualisable) ; LCEN art. 6 : conservation 1 an des données d'identification des auteurs de contenus publiés (décret 2021-1362) ; précédent DansMaRue : effacement après 1 an.
- Géocodage : l'API Adresse historique (api-adresse.data.gouv.fr) est décommissionnée depuis début 2026 ; le géocodage BAN est repris par l'IGN sur la Géoplateforme (data.geopf.fr/geocodage, 50 req/s/IP).
- Hébergement : France/UE, contrat art. 28, SecNumCloud non obligatoire pour une commune de cette taille (vérifié, y compris l'amendement de 02/2026 qui ne vise que les plus de 30 000 habitants).

### Décision d'architecture (application de la règle d'or)

1. **Adopter tel quel** : Gancio pour la saisie, la modération et la publication des événements (v1.28.2, dernière stable, épinglée par digest ; migration v2 planifiée à sa sortie stable, protégée par des tests de contrat), Caddy pour le HTTPS automatique et le proxy, le géocodage Géoplateforme IGN (BAN), Leaflet 1.9.4 auto-hébergée, pywebpush.
2. **Étendre** : rien. Aucune base existante saine ne couvre le reste du besoin (11 candidats examinés ci-dessus, dont les plateformes françaises CitéLibre et Publik).
3. **Assembler** : un `docker compose` de 4 services (Caddy, cœur applicatif, worker, Gancio). Gancio est servi sur un sous-domaine dédié (ex. agenda.commune.fr, gancio.localhost en démo) : le déploiement en sous-chemin n'est pas supporté par Gancio (documentation officielle), constat de la revue adverse qui a corrigé l'architecture initiale.
4. **Écrire (l'écart irréductible)** : le cœur applicatif, à savoir la PWA citoyenne unifiée (fil, agenda, signalement, annonces), le serveur Open311 GeoReport v2 avec extensions, la génération des flux iCal et RSS des événements (à partir du miroir local, pour maîtriser liens, UID et conformité, les exports natifs de Gancio servant de repli), le back-office signalements (files, statuts, routage, modération), les annonces multicanal et l'envoi Web Push. Le module annonces natif de Gancio a été évalué et écarté (pas de niveau d'alerte, pas d'expiration, pas de déclencheur push, interface distincte de celle des agents).

Pourquoi écrire ce cœur plutôt qu'étendre Mark-a-Spot (le plan B le plus crédible) : Mark-a-Spot apporterait le serveur Open311 tout fait, mais au prix d'opérer Drupal 11 plus un frontend Nuxt (deux écosystèmes, mises à jour de sécurité Drupal fréquentes, distribution hors politique de sécurité drupal.org), d'un back-office générique peu adapté à des agents non formés, d'une licence GPL-2.0+ sans clause réseau, d'un projet quasi mono-mainteneur en open core, et il faudrait de toute façon développer l'agenda, le Web Push et la PWA unifiée en modules Drupal. Le cœur à écrire est petit et borné, dans une pile généraliste répandue, donc plus maintenable par des tiers qu'une distribution Drupal spécialisée.

**Licence recommandée : AGPL-3.0** (norme du secteur : Decidim, CONSUL, FixMyStreet, Gancio, listmonk, Publik, DirectMairie ; protège contre la réappropriation SaaS sans contribution).

## Spécification produit

Nom de travail : Civic Libre (le nom définitif pourra changer sans impact technique).

### Périmètre du MVP

Inclus :
1. Agenda communal : consultation publique, fiche événement, flux iCal et RSS générés par le cœur, saisie et modération via Gancio (mairie et associations), notification push des nouveaux événements.
2. Annonces : actualités et alertes de la mairie (titre, texte, image avec alternative obligatoire, niveau information ou alerte, expiration), publiées en une saisie vers le fil, le flux RSS annonces et le push.
3. Signalement : parcours citoyen en 3 étapes, suivi public par référence, modération avant publication, API Open311 GeoReport v2 avec extensions.
4. Back-office agents : file par service, statuts (à traiter, en cours, résolu, rejeté avec motif), commentaire public par transition, file de modération (photos et descriptions), notification courriel du déclarant, configuration via l'admin Django (catégories, services, comptes ; seule la file de traitement des agents est une interface sur mesure).
5. Notifications Web Push : opt-in par centres d'intérêt (événements, actualités, alertes), envoi prioritaire des alertes, désabonnement en un geste.
6. PWA installable, mobile d'abord, français, accessibilité RGAA travaillée dès le premier écran.
7. Supervision minimale intégrée : endpoint `/sante` agrégé, heartbeat du worker, alerte courriel à l'exploitant en cas d'échec répété (sauvegarde, SMTP, push, synchronisation).

Exclus du MVP (non-objectifs, notés pour plus tard) : annuaire local, sondages, comptes citoyens, applications natives et stores, multi-commune et EPCI, courriel de masse (listmonk documenté en exemple de compose complémentaire, hors compose livré), rediffusion automatique Mastodon, SMS, panneaux lumineux, démarches administratives, SSO entre le cœur et Gancio.

### Personas

**Habitante ou habitant.** Sur mobile, sans compétence technique, souvent pressé. Consulte l'agenda sans créer de compte, s'abonne aux notifications s'il le souhaite, signale un trou dans la chaussée en trois gestes. Veut savoir ce que devient son signalement sans relancer la mairie.

**Agent municipal.** Services techniques ou accueil. Peu de temps, pas de formation longue. Reçoit les signalements déjà routés vers son service, met à jour le statut avec un commentaire, modère les photos avant publication. Publie annonces et événements ; la spec assume que les événements se saisissent dans Gancio et le reste dans le back-office du cœur (deux outils, un guide agent unique, liens croisés visibles ; critère du pilote : un agent forme un autre agent sans aide).

**Administratrice ou administrateur.** Secrétaire général, élu délégué ou prestataire. Configure catégories, services, comptes via l'admin Django. Un exploitant technique identifié (prestataire, service mutualisé ou bénévole compétent) assume les tâches du modèle d'exploitation ci-dessous : sans lui, l'instance n'est pas viable, la spec le dit sans détour.

### Parcours clés

1. Consulter l'agenda : page publique sans compte, filtrable par période, liens « S'abonner (calendrier) » (iCal) et « Flux RSS », ajout d'un événement au calendrier du téléphone.
2. S'abonner aux notifications : invitation discrète et non bloquante, activation sur geste explicite, choix des centres d'intérêt, désabonnement en un geste. Sur iPhone, tutoriel d'installation de la PWA en version illustrée ET texte étape par étape (accessible au lecteur d'écran, cas Safari et autres navigateurs).
3. Signaler : bouton central visible dès l'accueil. Étapes : catégorie, position (géolocalisation proposée, placement par simple appui sur la carte, jamais de glisser-déposer ; alternative à la carte par saisie d'adresse avec autocomplétion BAN accessible, plus champ libre « précision sur l'emplacement »), puis photo facultative (champ fichier natif, bouton « Passer cette étape » au même rang). Description, courriel facultatif. Confirmation immédiate avec référence et lien de suivi. L'ordre exact des étapes sera confirmé en phase 3 (test du parcours).
4. Traiter : l'agent ouvre la file de son service, voit carte, photo, description, modère ce qui sera public, passe le statut à « en cours » puis « résolu » avec commentaire public facultatif ; le déclarant est notifié par courriel s'il l'a demandé ; l'historique public est mis à jour.
5. Publier une fois, diffuser partout : un événement saisi dans Gancio apparaît dans la PWA, l'iCal, le RSS et déclenche un push « événements » ; une annonce saisie dans le back-office apparaît dans le fil, le RSS annonces et déclenche un push « actualités » ou « alertes » selon le niveau.

### Modèle de données (cœur applicatif)

- `Categorie` (service Open311) : code stable, nom, description, pictogramme, service destinataire, active.
- `ServiceMunicipal` : nom, courriel de notification, agents membres. Les courriels de notification aux services ne contiennent que la référence, la catégorie et un lien vers le back-office, jamais les données du déclarant.
- `Signalement` : référence publique courte, catégorie, description (max 4 000 caractères), latitude, longitude, adresse (géocodage inverse Géoplateforme), statut (`nouveau`, `en_cours`, `resolu`, `rejete`), motif de rejet, courriel du déclarant (facultatif, jamais publié, purgé à l'anonymisation), IP et user-agent de création (obligation LCEN, conservés 12 mois, base art. 6.1.c), jeton privé de suivi, état de publication (en attente de modération, publié, masqué), horodatages.
- `PhotoSignalement` : fichier ré-encodé (EXIF supprimé à l'upload), miniature, état de modération, texte alternatif normalisé (« photo jointe au signalement », enrichissable par le modérateur).
- `MiseAJourSignalement` (update Open311) : signalement, transition de statut, commentaire public, media_url facultative, auteur, horodatage.
- `Annonce` : titre, corps, niveau (`information`, `alerte`), image facultative avec choix obligatoire à la saisie (décorative ou informative avec texte alternatif requis), épinglage, dates de publication et d'expiration.
- `AbonnementPush` : endpoint, clés p256dh et auth, sujets, date de création, dernier succès, compteur d'échecs.
- `NotificationSortante` (outbox) : type, sujet, priorité (les alertes passent devant), charge utile, état, tentatives ; garantit l'idempotence (au plus un envoi par couple notification et abonnement) et la reprise après crash.
- `EvenementMiroir` : copie de lecture des événements Gancio (identifiant, titre, dates, lieu, tags, image et son alternative si fournie par l'API, URL), rafraîchie sur fenêtre glissante (passé 1 mois, futur 6 mois) ; source des flux iCal et RSS du cœur, du fil unifié et du déclenchement push.
- Utilisateurs : `django.contrib.auth`, rôles `agent`, `gestionnaire`, `admin` ; le persona administrateur est servi par l'admin Django personnalisé a minima.

Gancio reste la source de vérité des événements (pas de double saisie, pas d'écriture côté cœur ; si l'audit d'accessibilité de Gancio l'exige, un formulaire de saisie simple côté cœur postant via l'API Gancio est le repli documenté).

### API et formats standards

Open311 GeoReport v2, en JSON et XML (XML obligatoire dans le standard) :

| Endpoint | Rôle |
|---|---|
| `GET /open311/v2/discovery.[json\|xml]` | Service discovery (requis par le standard) |
| `GET /open311/v2/services.[json\|xml]` | Liste des catégories |
| `GET /open311/v2/services/{code}.[json\|xml]` | Définition (MVP : `metadata=false`, pas d'attributs personnalisés) |
| `POST /open311/v2/requests.[json\|xml]` | Création ; mode temps réel : renvoie toujours `service_request_id`, jamais de token |
| `GET /open311/v2/tokens/{token}.[json\|xml]` | Implémentation triviale (résolution immédiate), complétude du standard |
| `GET /open311/v2/requests.[json\|xml]` | Liste publique (contenus à l'état publié uniquement, champs minimisés, fenêtre 90 jours par défaut) |
| `GET /open311/v2/requests/{id}.[json\|xml]` | Détail public |
| `GET /open311/v2/servicerequestupdates.[json\|xml]` | Extension FixMyStreet exacte (paramètres start_date, end_date ; champs update_id, service_request_id, status, updated_datetime, description, media_url) |

Statuts : champ `status` standard limité à `open` (`nouveau`, `en_cours`) et `closed` (`resolu`, `rejete`) ; les statuts détaillés sont exposés dans les updates via l'extension FixMyStreet « Additional states » (`en_cours` : IN_PROGRESS, `resolu` : FIXED, `rejete` : NO_FURTHER_ACTION ou NOT_COUNCILS_RESPONSIBILITY). `jurisdiction_id` accepté et ignoré. `media_url` entrante stockée comme référence, jamais téléchargée (SSRF), jamais publiée sans modération. Une couche service unique valide les créations, que la source soit le formulaire PWA ou le POST Open311 (deux adaptateurs, une validation). Si le lot Open311 déborde, la coupe admissible est le POST en XML (les GET restent complets).

Flux sortants, générés par le cœur depuis `EvenementMiroir` (liens vers la PWA, maîtrise des UID et de la conformité ; décision issue de la revue adverse, les exports natifs Gancio contenant des URL absolues vers son sous-domaine et aucune propriété RFC 7986) :
- `/flux/evenements.ics` : UID stables, TZID Europe/Paris avec VTIMEZONE, NAME, SOURCE, REFRESH-INTERVAL (RFC 7986), fenêtre glissante.
- `/flux/evenements.rss` et `/flux/annonces.rss` : framework de syndication Django, guid permaliens stables, validation « sans erreur » (W3C Feed Validator, icalendar.org) en CI.

API internes : création de signalement (multipart), page de suivi (référence plus jeton), abonnement push. Pas d'autre écriture publique.

### Architecture cible

```
[Caddy, HTTPS auto]
   ├── commune.fr           → cœur (Django) : PWA, back-office, Open311, flux, push
   ├── agenda.commune.fr    → Gancio (saisie, modération, UI publique facultative)
   └── /tuiles/*            → proxy cache vers le fournisseur de tuiles configuré

[worker] = même image que le cœur :
   boucle courte (~10 s) : envoi de l'outbox par priorité, pool borné, backoff sur 429/5xx,
     purge des abonnements sur 404/410, heartbeat
   boucle lente (5 min) : synchronisation Gancio, anonymisation planifiée, alertes exploitant

Volumes : données cœur (SQLite WAL + médias), données Gancio, certificats Caddy
Externes : relais SMTP (sous-traitant art. 28), Géoplateforme IGN (géocodage), fournisseur de tuiles
```

- Cœur : Python 3.12, Django 5.2 LTS (support de sécurité jusqu'en avril 2028 ; jalon de migration vers la LTS suivante inscrit au guide d'exploitation, fenêtre avril 2027 à avril 2028), SQLite en `journal_mode=WAL` avec `busy_timeout` et transactions immédiates (deux processus écrivains, configuration explicite obligatoire ; volume sur disque local, jamais de NFS), PostgreSQL documenté en option, gunicorn, whitenoise, Pillow, pywebpush.
- Frontend : gabarits Django rendus serveur, CSS sur mesure léger, JavaScript progressif sans framework (Leaflet 1.9.4 épinglée et auto-hébergée, géolocalisation, service worker) ; consultation et signalement fonctionnent sans JavaScript (la carte devient une saisie d'adresse).
- Tuiles cartographiques proxifiées et mises en cache par Caddy (l'IP des habitants ne part jamais chez le fournisseur) ; fournisseur configurable, défaut France/UE (OSM France ou Géoplateforme IGN), attribution affichée, politique d'usage respectée, auto-hébergement documenté.
- Géocodage : Géoplateforme IGN (data.geopf.fr), URL configurable, limite 50 req/s documentée.
- `docker compose up` lance une démo complète avec données d'exemple (domaines *.localhost, TLS interne Caddy). Clés VAPID générées automatiquement au premier démarrage.
- Configuration commune : variables d'environnement plus admin Django (nom, logo, coordonnées, périmètre géographique de signalement). Couleur d'accent communale par dérivation automatique : la commune choisit une teinte, le système génère les variantes conformes (4,5:1 texte, 3:1 composants et focus), la teinte brute n'est jamais employée directement.
- Instance mono-commune par conception (la mutualisation se fait en déployant N instances).

### Intentions d'ergonomie et de design

Direction : « l'affichage municipal, réinventé en mieux », sobre, institutionnel et chaleureux ; ni réseau social, ni administration froide. Niveau de finition visé : PanneauPocket et IntraMuros, sans rien copier.

- Mobile d'abord : fil vertical unique de cartes (alertes, annonces épinglées, prochains événements), pagination explicite (bouton « Voir plus », jamais de défilement infini), navigation basse à 4 entrées (Accueil, Agenda, Signaler, Infos), bouton Signaler proéminent.
- Signature visuelle : la « tuile date » typographique des événements (grand numéro du jour, mois en petites capitales) ; pastilles de statut au vocabulaire clair (à traiter, en cours, résolu).
- Palette : base neutre et calme, accent communal par dérivation contrôlée (voir architecture), couleurs fonctionnelles fixes testées RGAA.
- Typographie : deux fontes libres (OFL) auto-hébergées, une de caractère pour titres et dates, une très lisible pour le texte ; corps généreux, zoom texte 200 % sans perte (critère RGAA), cibles tactiles 44 px minimum.
- Écriture d'interface : français simple et direct, verbes d'action, libellés constants, erreurs qui disent quoi faire ; lisible par des publics seniors.
- Mouvement : discret, `prefers-reduced-motion` respecté.
- Les tokens minimaux (palette neutre, typographie, tuile date) sont livrés dès le premier lot ; le système complet est consolidé en phase 3 avec le skill de design frontend et consigné dans un document de design.

### Exigences RGPD

- Registre : modèles fournis pour 5 traitements avec base légale explicite : signalements (6.1.e), notifications push (6.1.a, transfert hors UE au sens du chapitre V documenté par opérateur de push avec son outil de transfert), journaux techniques (6.1.e et 6.1.c pour le volet conservation légale ; l'intérêt légitime est indisponible pour une autorité publique), comptes et journal d'administration du back-office (6.1.e), agenda Gancio (comptes mairie et associations ; ce que Gancio journalise et stocke sera vérifié à l'assemblage et consigné).
- AIPD : analyse de seuil documentée et fournie ; non requise au sens de la liste CNIL (délibération 2018-327 : les entrées alertes et signalements visent les matières sociale, sanitaire et professionnelle ; pas de large échelle à 7 000 habitants), un seul critère CEPD rempli.
- Minimisation : aucun compte citoyen, courriel facultatif jamais affiché ni transmis aux services, EXIF supprimé à l'upload, publication après modération uniquement, géolocalisation du problème uniquement, pas de collecte d'âge (service non destiné spécifiquement aux mineurs, mention au registre et à la page confidentialité).
- Charte de modération opposable (modèle fourni) : rejet ou floutage des visages et plaques avant publication, non-publication ou généralisation de la localisation des signalements visant une propriété privée ou une personne, masquage des descriptions mentionnant des tiers ; les endpoints publics n'exposent que l'état « publié » ; lien de demande de retrait sur chaque contenu publié ; la responsabilité éditoriale de la commune est explicitée dans la documentation.
- Obligation LCEN (art. 6, décret 2021-1362) : IP et user-agent de création des contenus publiés conservés 12 mois (base 6.1.c) puis purgés ; adresses IP tronquées partout ailleurs dans les journaux.
- Durées (configurables, défauts) : anonymisation 12 mois après clôture ET butoir absolu 24 mois après création quel que soit le statut (exécutée par le worker, alerte back-office sur les signalements dormants) ; abonnements push purgés sur 404/410 et après 6 mois d'échecs ; journaux 12 mois ; rotation des sauvegardes bornée (90 jours) pour que l'effacement soit effectif, stockage des sauvegardes traité comme sous-traitance s'il est externalisé.
- Information : page confidentialité en français simple nommant le fournisseur de tuiles actif et les opérateurs de push, mention art. 13 sur le formulaire, pas de cookies tiers ni traceurs (cookie de session back-office exempté).
- Sous-traitants : hébergeur ET relais SMTP sous contrat art. 28 (localisation UE recommandée), listés au registre.
- Rappels commune : DPO obligatoire et mutualisable, délibération ou décision formalisant le téléservice.

### Exigences RGAA

- Cible : RGAA 4.1.2 sur les parcours citoyens ET le back-office (écrans agents nommés dans l'échantillon : file, changement de statut, rédaction d'annonce avec image, configuration), ET les pages Gancio réellement exposées (formulaire d'ajout public, connexion, modération), incluses dans la grille, les tests et la déclaration (non-conformités listées, inscrites au schéma pluriannuel ; repli documenté si l'audit est mauvais : formulaire de saisie côté cœur via l'API Gancio).
- Conception : HTML sémantique rendu serveur, formulaires étiquetés, contrastes conformes par dérivation automatique, focus visible, navigation clavier complète, zoom texte 200 % sans perte, alternatives à toute image informative (champs dédiés dans le modèle de données), interactions cartographiques sans glisser-déposer et toujours doublées d'une alternative textuelle, ARIA parcimonieux.
- Outillage : axe-core automatisé en CI dès le premier écran livré (filet anti-régression, pas un audit), grille d'audit RGAA officielle auto-évaluée (méthodologie et échantillon RGAA, taux calculé) tenue à jour.
- Cadrage juridique honnête : le projet livre la grille auto-évaluée et les modèles ; la déclaration est publiée sous la responsabilité de la commune ; « partiellement conforme » n'est possible que si l'audit établit au moins 50 % des critères, sinon la mention légale est « non conforme ». Une session d'observation avec 3 à 5 habitants dont des seniors est prévue en recette (critère : parcours accomplis sans aide).

### Sécurité

HTTPS partout (Caddy), HSTS, CSP stricte sans script externe, CSRF Django, limitation de débit sur formulaires publics et API (IP complètes conservées le temps strictement nécessaire au rate limiting, documenté), pot de miel, uploads validés et ré-encodés, mots de passe Argon2, sessions durcies, journal d'administration, secrets hors dépôt, images épinglées par digest, dépendances suivies (renovate sur le dépôt ; les instances se mettent à jour via le script d'exploitation), sauvegardes chiffrées avec restauration testée.

### Modèle d'exploitation (qui fait tourner l'instance)

La spec l'affirme sans détour : sans exploitant technique identifié (prestataire, structure de mutualisation, service intercommunal ou bénévole compétent), l'instance n'est pas viable. Le projet fournit les outils pour que ce rôle soit léger et transférable :

| Tâche récurrente | Fréquence | Durée estimée |
|---|---|---|
| Mise à jour applicative (script en une commande : sauvegarde préalable, pull des versions taguées, migrations, contrôle `/sante`, procédure de retour arrière) | mensuelle et sur alerte de sécurité | 15 min |
| Mise à jour de l'OS du VPS | mensuelle | 10 min |
| Vérification des sauvegardes (alerte automatique si échec ou plus vieille que 48 h) | mensuelle (automatisée en continu) | 5 min |
| Renouvellement domaine, contrôle DNS et certificats | annuelle (alertes automatiques) | 15 min |
| Suivi du canal d'annonces de sécurité du projet (flux RSS des versions) | continu | négligeable |

Budget temps : 30 à 60 minutes par mois par une personne à l'aise avec SSH. Supervision intégrée : `/sante` agrégé (synchro, push, courriel, disque, âge de la dernière sauvegarde), heartbeat du worker, alertes courriel à l'exploitant, rotation des journaux et nettoyage docker scriptés ; la surveillance externe du `/sante` (sonde distante) est recommandée et documentée, en assumant qu'elle peut introduire un service tiers.

Sauvegardes : méthode sûre spécifiée (`sqlite3 .backup` ou `VACUUM INTO` pour les deux bases, cœur et Gancio), périmètre exhaustif (bases, médias, `.env` incluant les clés VAPID dont la perte invaliderait tous les abonnements push, configurations Caddy et Gancio), copie chiffrée hors du VPS, rotation 90 jours, restauration testée en CI et exercée au dernier lot.

Réversibilité (dossier fourni) : domaine enregistré au nom de la commune, jamais du prestataire ; inventaire des accès et secrets déposé en mairie et tenu à jour ; exercice de reprise au dernier lot : reconstruire une instance fonctionnelle sur un VPS neuf à partir des seules sauvegardes et du dépôt public.

Coût total annuel honnête (à mettre en regard des 700 à 1 500 €/an du marché propriétaire) :

| Poste | Fourchette annuelle |
|---|---|
| VPS 2 Go France/UE | 60 à 180 € |
| Nom de domaine | 10 à 20 € |
| Relais SMTP transactionnel FR/UE (la délivrabilité depuis un VPS nu n'est pas réaliste : SPF, DKIM, réputation d'IP) | 0 à 120 € |
| Stockage des sauvegardes hors site | 10 à 60 € |
| Exploitation humaine (30 à 60 min/mois : de 0 € en interne ou bénévole à 600 à 1 000 € en prestataire) | 0 à 1 000 € |

Le logiciel est gratuit et sans verrou ; le service, lui, a un coût de fonctionnement qui doit entrer au budget de la commune. L'intérêt du libre est ailleurs : réversibilité, standards, mutualisation possible, pas de péage par habitant.

### Maintenance par des tiers

- Technologies volontairement banales : Django LTS, SQLite, Caddy, un seul langage serveur, pas de file de messages, pas de framework JS.
- Documentation en français, écrite au fil de l'eau (chaque lot livre sa section) : installation, exploitation, guide agent unique (couvrant back-office et Gancio, copies d'écran), guide administrateur, contribution (CONTRIBUTING, ADR pour chaque décision structurante, dont l'état de Leaflet 1.x et le chantier de migration Gancio v2).
- Tests de contrat sur la surface Gancio consommée (API événements, flux) exécutés en CI contre l'image épinglée ; repli documenté : la synchronisation peut basculer sur le parsing du flux iCal seul.
- Code : identifiants en anglais, interface et documentation en français ; tests exigés pour toute contribution ; CHANGELOG, versions sémantiques, canal d'annonces de sécurité (flux RSS des releases).

## Plan d'implémentation incrémental (après validation)

Chaque lot est mené en TDD, se conclut par une revue de code et une vérification de fonctionnement réel, livre sa part de documentation, et laisse `docker compose up` démontrable. axe-core tourne en CI dès le lot 1.

| Lot | Contenu | Critère « terminé » |
|---|---|---|
| 0. Fondations | Dépôt, LICENSE AGPL-3.0, README, compose (Caddy, cœur minimal, Gancio sur sous-domaine, worker avec heartbeat), SQLite WAL configuré, CI (ruff, pytest), pre-commit, génération VAPID au premier démarrage | `docker compose up` sert l'accueil sur commune.localhost et Gancio sur agenda.localhost |
| 1. Agenda | Synchronisation Gancio avec tests de contrat, fil et pages agenda, tokens de design minimaux (palette neutre, typo, tuile date), flux iCal et RSS événements générés par le cœur, axe-core en CI, données de démonstration | Un événement créé dans Gancio apparaît dans la PWA ; les flux valident sans erreur et les récurrences s'affichent juste aux changements d'heure |
| 2. Annonces | CRUD back-office avec alternative d'image obligatoire, fil, épinglage, expiration, RSS annonces | Une annonce saisie apparaît dans le fil et le RSS valide sans erreur |
| 3. Signalement citoyen | Formulaire par étapes accessible (avec et sans JavaScript), photo en champ natif, placement par appui sur carte plus alternative adresse (Géoplateforme), EXIF supprimé, référence et page de suivi, rate limit et pot de miel | Parcours complet réussi sur mobile, y compris sans JavaScript et au clavier |
| 4. Back-office | Files par service, transitions avec commentaire public, file de modération (photos, descriptions), courriels (déclarant, service, sans données personnelles du déclarant vers les services), admin Django configuré, test de délivrabilité SMTP | Cycle nouveau, en cours, résolu joué de bout en bout, modération comprise, courriels reçus |
| 5. Open311 | 8 endpoints JSON et XML (discovery et tokens compris), extension servicerequestupdates au format FixMyStreet exact, statuts étendus, couche service partagée avec le formulaire, doc API, tests de contrat | Suite de contrat verte en XML et JSON, démonstration par curl |
| 6. Push et PWA de base | Manifest, service worker minimal (réception push), abonnements VAPID par sujets, outbox prioritaire avec idempotence et backoff, purge 404/410, page réglages, tutoriel iOS accessible, test de concurrence SQLite sous envoi | Push reçu en démo sur Android et iOS (PWA installée) ; une alerte part avant les envois en file |
| 7. Design final et RGAA | Système de design complet appliqué, hors-ligne de base, grille d'audit RGAA auto-évaluée complète (échantillon officiel, back-office et pages Gancio incluses), modèles de déclaration et de schéma pluriannuel, session d'observation habitants | Installable, axe-core sans erreur, grille remplie avec taux calculé, observations menées |
| 8. Packaging et exploitation | Compose durci (healthchecks, restart), sauvegardes scriptées (méthode sûre, deux bases, secrets, hors site, rotation), script de mise à jour en une commande, `/sante` complet et alertes exploitant, guides finalisés, dossier de réversibilité, note honnête « ce qui manque pour la production », exercice de reprise sur VPS neuf | Installation technique en 30 minutes par une personne sachant utiliser SSH, prérequis préparés via la checklist fournie (DNS, SMTP) ; reprise depuis les seules sauvegardes réussie |

Ampleur estimée du cœur : 5 000 à 15 000 lignes tests compris (estimation honnête après revue, tracée en ADR).

## Vérification de bout en bout (phase 5)

Scénarios exécutés réellement : abonnement iCal depuis un téléphone (calendriers Apple, Google, Thunderbird), flux RSS dans un lecteur, signalement complet avec photo depuis mobile, modération puis traitement par un agent et courriels reçus, création et interrogation Open311 par curl (XML et JSON), push reçu Android et iOS, alerte prioritaire, parcours clavier et lecteur d'écran (pages citoyennes, back-office, pages Gancio exposées, tutoriel iOS), session d'observation avec habitants dont seniors, `docker compose up` sur machine vierge, restauration depuis sauvegarde.

## Risques assumés et incertitudes (honnêteté)

- Gancio : facteur bus proche de 1, v1.28.2 stable mais branche v2 en alpha/bêta ; migration à prévoir, traitée par l'amont comme une réinstallation. Mitigations : version épinglée par digest, tests de contrat en CI, couplage limité à l'API et aux flux (les flux publics sont générés par le cœur), repli documenté (parsing iCal seul, ou module événements interne minimal).
- Push iOS : friction réelle (installation écran d'accueil) et fiabilité à surveiller ; tutoriel accessible, courriel et flux en repli.
- Deux back-offices (cœur et Gancio), deux comptes, pas de SSO : coût de formation assumé, guide agent unique, comptes Gancio limités au minimum, liens croisés ; critère du pilote : un agent en forme un autre sans aide.
- Web Push : transport chiffré de bout en bout mais transitant par les serveurs de Google, Apple, Mozilla et Microsoft (métadonnées visibles) ; structurel au standard, qualifié au registre comme transfert hors UE avec l'outil de transfert par opérateur.
- Open311 : standard figé ; assumé, sa stabilité vaut interopérabilité ; extensions FixMyStreet documentées.
- RGAA : sans audit atteignant 50 % des critères, la mention légale reste « non conforme » ; le projet livre la grille auto-évaluée et vise mieux, sans le garantir.
- Aucun retour d'expérience de mairie française sur ce montage : prototype à éprouver en pilote ; la note « ce qui manque pour la production » l'assumera (astreinte, support utilisateur, DPO, audit de sécurité et d'accessibilité externes).
- Le cœur écrit reste du code à maintenir (5 000 à 15 000 lignes tests compris) : c'est l'écart irréductible après réutilisation maximale, tracé par ADR.

## Phase 2 : revue adverse de la spec (réalisée)

7 relecteurs adverses indépendants (réinvention, sur-ingénierie, dépendances, RGPD, accessibilité, réalisme opérationnel, exactitude des standards) ont produit 61 constats : 3 bloquants, 30 majeurs, 28 mineurs. Tous les bloquants et majeurs sont intégrés à la présente v2, notamment :

- Architecture corrigée : Gancio en sous-domaine (le sous-chemin n'est pas supporté), flux publics générés par le cœur plutôt que proxifiés, tuiles proxifiées avec défaut France/UE au lieu des serveurs bénévoles OSMF.
- Fait corrigé : géocodage basculé de l'API Adresse (décommissionnée début 2026) vers la Géoplateforme IGN.
- État de l'art complété : CitéLibre/Lutece/DansMaRue, Publik, uReport et 6aika ajoutés aux verdicts ; l'affirmation d'exclusivité de Mark-a-Spot reformulée ; rejets de Gancio announcements et django-push-notifications documentés.
- Open311 rendu exact : discovery et tokens ajoutés, endpoint et format `servicerequestupdates` corrigés, statuts étendus rattachés à la bonne extension.
- Plan réordonné : annonces avancées (lot 2), service worker déplacé avec le push (lot 6), modération explicitement au lot 4, axe-core et tokens de design dès le lot 1, documentation au fil de l'eau.
- RGPD renforcé : 5 traitements au registre avec bases légales, obligation LCEN (IP de création conservée 12 mois), charte de modération, butoir d'anonymisation à 24 mois, analyse de seuil AIPD, SMTP en sous-traitant, transferts push qualifiés, mineurs traités.
- Accessibilité renforcée : pages Gancio dans le périmètre d'audit, dérivation automatique des couleurs au lieu d'une simple vérification, alternatives d'images dans le modèle de données, carte sans glisser-déposer, cadrage juridique exact de « partiellement conforme ».
- Réalisme opérationnel : section « Modèle d'exploitation » ajoutée (tâches, temps, supervision, sauvegardes sûres pour SQLite, réversibilité, coût total honnête), promesse « aucun service payant » corrigée (SMTP), critère d'installation reformulé.

Arbitrages contre l'avis d'un relecteur (documentés) : la version Gancio v1.28.2 existe bien (vérifiée sur l'API Framagit le 07/07/2026, release du 14/12/2025), le constat « version inexistante » était erroné ; la spec retient la dernière stable 1.x plutôt qu'une bêta 2.x, avec migration planifiée et tests de contrat. Le POST Open311 est conservé au MVP (exigence du brief), avec coupe admissible documentée.

## Décisions soumises à validation (avec recommandation)

1. Périmètre MVP incluant les annonces et alertes (recommandé : fonction la plus valorisée du marché, désormais lot autonome précoce) ou strictement agenda plus signalement.
2. Base : assemblage Gancio plus cœur Django minimal (recommandé) ou plan B extension de Mark-a-Spot (réutilisation maximale du serveur Open311 au prix de la charge Drupal).
3. Licence AGPL-3.0 (recommandée, norme du secteur).
4. Nom de travail « Civic Libre » (indifférent techniquement).

Après validation écrite : phase 3 (architecture détaillée et système de design), puis implémentation TDD par lots, revue interne, packaging. La spec et l'état de l'art sourcé seront versés au dépôt en tête de phase 3.
