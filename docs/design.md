# Système de design

Livrable de la phase 3, appliqué progressivement à partir du lot 1 (tokens minimaux) et consolidé au lot 7. Direction posée dans docs/spec.md : « l'affichage municipal, réinventé en mieux », sobre, institutionnel et chaleureux, mobile d'abord, RGAA par conception. Référence de finition : PanneauPocket et IntraMuros, sans rien copier.

## Parti pris

Le sujet est un panneau d'affichage de mairie devenu vivant : de l'information posée calmement, hiérarchisée, sans bruit. Pas de réseau social, pas de gamification, pas de dégradés décoratifs. La personnalité passe par la typographie (les dates comme objets graphiques) et par une retenue stricte partout ailleurs. Un seul geste de caractère : la tuile date. Tout le reste est discipliné.

## Tokens

### Couleurs (thème clair par défaut, thème sombre dérivé)

| Token | Valeur | Usage |
|---|---|---|
| `--paper` | `#F7F6F2` | fond de page (papier chaud, pas de blanc pur) |
| `--card` | `#FFFFFF` | fond des cartes |
| `--ink` | `#1D2129` | texte principal |
| `--ink-soft` | `#4B5563` | texte secondaire (4,5:1 minimum sur `--card`) |
| `--line` | `#E4E2DB` | filets, séparateurs |
| `--accent` | dérivé | teinte communale, jamais utilisée brute (voir dérivation) |
| `--accent-ink` | dérivé | variante texte de l'accent, ≥ 4,5:1 sur `--paper` et `--card` |
| `--accent-surface` | dérivé | fond léger teinté pour les zones actives |

Couleurs fonctionnelles fixes (verrouillées par tests de contraste automatisés) :

| Token | Valeur | Usage |
|---|---|---|
| `--status-new` | `#8A4B08` | pastille « à traiter » (texte sur fond clair assorti) |
| `--status-progress` | `#1D4ED8` | pastille « en cours » |
| `--status-resolved` | `#166534` | pastille « résolu » |
| `--status-rejected` | `#57534E` | pastille « rejeté » |
| `--alert` | `#B42318` | bandeau et pastille alerte |

Règles : jamais d'information portée par la seule couleur (chaque pastille a son libellé), contrastes texte ≥ 4,5:1, composants et focus ≥ 3:1.

### Dérivation de l'accent communal

La commune fournit une teinte (`CIVIC_ACCENT_COLOR`). Le système en dérive, à la construction du CSS :
1. `--accent-ink` : la teinte est assombrie ou éclaircie pas à pas jusqu'à atteindre 4,5:1 sur `--paper` et `--card`.
2. `--accent` (boutons, barres) : ajustée jusqu'à 3:1 minimum contre les fonds adjacents, texte des boutons imposé (blanc ou `--ink`, selon le meilleur contraste, ≥ 4,5:1).
3. `--accent-surface` : mélange à ~10 % avec `--paper`.
La teinte brute n'est jamais employée pour du texte ni pour un composant porteur d'information. Défaut livré : `#31597F` (bleu ardoise institutionnel).

### Typographie

Deux fontes libres (SIL OFL), auto-hébergées en woff2, aucune requête externe :

- **Bricolage Grotesque** : titres, tuiles date, chiffres de référence. Une grotesque à caractère, dessinée en France, qui donne le ton sans pastiche administratif.
- **Source Sans 3** : texte courant, formulaires, back-office. Neutre, très lisible, éprouvée.

Échelle fluide (clamp) : corps 16 à 18 px, `h1` 28 à 36 px, `h2` 22 à 26 px, tuile date jour 40 à 48 px. Interligne 1,6 pour le corps. Zoom texte 200 % sans perte (testé). Unités relatives partout.

### Espacement et formes

Base 4 px. Cartes : rayon 12 px, ombre unique très douce (`0 1px 3px rgb(0 0 0 / 8%)`). Pastilles : rayon complet. Cibles tactiles ≥ 44 px. Une seule largeur de contenu : 640 px max sur mobile étendu, deux colonnes à partir de 960 px (fil + panneau latéral agenda).

### Mouvement

Transitions 150 ms sur les états interactifs uniquement. Aucune animation décorative. `prefers-reduced-motion: reduce` supprime tout.

## Composants

- **Tuile date** (signature) : bloc carré, jour en Bricolage Grotesque corps 40+, mois en petites capitales espacées, bord `--line`, jamais de fond accent. Utilisée dans le fil, l'agenda et le détail d'événement.
- **Carte de fil** : image facultative (ratio 16:9, alt obligatoire), surtitre (catégorie ou « Alerte »), titre, date, une ligne de résumé. L'alerte utilise un bandeau plein `--alert` avec icône et texte, pas seulement une couleur.
- **Pastille de statut** : point coloré + libellé texte (« à traiter », « en cours », « résolu », « rejeté »), fond teinté clair, texte foncé assorti.
- **Bouton primaire** : fond `--accent`, texte contrasté imposé, hauteur 48 px. Secondaire : bord `--line`, texte `--ink`. Le bouton « Signaler un problème » est le seul élément proéminent de l'accueil.
- **Navigation basse** (mobile) : 4 entrées, icônes + libellés toujours visibles, état actif par `--accent-ink` et barre, `aria-current`.
- **Formulaire par étapes** : une question par écran, barre de progression textuelle (« Étape 2 sur 3 »), boutons « Continuer » et « Passer cette étape » au même rang visuel, erreurs sous le champ avec rappel en haut.
- **Carte (géographie)** : conteneur à hauteur fixe, placement par simple appui, bouton « Utiliser ma position », alternative permanente « Saisir une adresse » au même niveau, adresse résolue toujours affichée en texte.
- **Bandeau hors-ligne / info** : pleine largeur, `--accent-surface`, texte `--ink`, jamais bloquant.

## Écriture d'interface

Français simple, niveau de lecture large, verbes d'action (« Signaler un problème », « S'abonner au calendrier », « Voir plus »). Un libellé garde le même nom du bouton à la confirmation (« Publier » produit « Publié »). Les erreurs disent quoi faire (« La photo dépasse 8 Mo. Choisissez une photo plus légère ou passez cette étape. »). Les états vides invitent (« Aucun événement à venir. Le prochain apparaîtra ici. »). Pas de jargon technique côté citoyen ; « notification » plutôt que « push », « calendrier » plutôt que « iCal » (le sigle entre parenthèses pour les initiés).

## Accessibilité (rappels de conception)

HTML sémantique d'abord (landmarks, titres hiérarchisés, listes réelles), focus visible épais (3 px, ≥ 3:1), navigation clavier complète, formulaires étiquetés avec autocomplete, ARIA parcimonieux, alternatives sur toute image informative, pagination explicite (jamais de défilement infini), aucune dépendance au survol ni au glisser-déposer. axe-core en CI dès le lot 1 ; grille RGAA 4.1.2 auto-évaluée tenue à jour (voir docs/spec.md).

## Thème sombre

Dérivé des mêmes tokens (`prefers-color-scheme`), papier `#15171B`, cartes `#1E2126`, encre `#E7E5E0`, accents re-dérivés pour tenir les mêmes ratios. Livré au lot 7, non bloquant avant.
