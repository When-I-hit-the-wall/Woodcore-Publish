---
id: 2026-10-08-plan-positions-cotes-numerotation-sections
titre: Plan de positions — règle et cotes, numérotation incrémentale, section d'une position, métrés, barre d'échelle
status: completed
cree: 2026-10-08
mis_a_jour: 2026-10-08
source: issue GitHub #9 «Plan de positions» (corps et deux commentaires du 2026-10-08)
docs: [docs/ui/window.md, docs/domain/position-plans.md, docs/domain/positions.md, docs/typst/api-conventions.md, docs/typst/command-docs.md, docs/architecture/data-contracts.md]
---

# Plan de positions — règle et cotes, numérotation incrémentale, section d'une position, métrés, barre d'échelle — Spécification

## 1. Objectif

Compléter l'onglet *Plan de positions* (suite de l'issue #4, fermée) : corriger l'erreur de compilation de la « Barre d'échelle » dans les vues *Affichage* et *Export* ; donner au plan une règle et des outils de cotation dont l'affichage se règle vue par vue ; faire tourner un poteau avec un cercle à la sélection ; afficher les options d'un objet dès l'activation de son outil ; numéroter les positions de façon incrémentale (par préfixe et par étage) et renuméroter en cascade, partout, quand l'une est supprimée ; choisir ou définir la section d'une position depuis le volet de droite ; afficher sur le plan, et dans son export PDF, les longueurs des éléments et le résumé des métrés (même présentation et même périmètre que dans l'onglet *Positions*, issue #14).

## 2. Source

La demande telle qu'elle a été donnée, **mot pour mot** (issue #9 : corps, puis commentaire 1 et commentaire 2 du 2026-10-08), découpée en points.

> **T0** — « Onglet *Plan de positions*. Suite de #4 (fermée). » (contexte du corps)
>
> **T1** — « Ajouter un outil règle. »
>
> **T2** — « Ajouter des outils de cotation pour pouvoir coter les plans. »
>
> **T3** — « Permettre d'activer ou de désactiver l'affichage des cotes dans chacun des 4 modes d'affichage, indépendamment des autres. »
>
> **T4** — « Bug : une erreur survient lorsqu'on clique sur « Barre d'échelle » dans les vues *Affichage* et *Export*. — observé : la feuille ne compile pas, la dernière page compilée reste affichée (message ci-dessous) — pour reproduire : cliquer sur « Barre d'échelle » dans *Affichage* ou *Export* »
>
> **T4b** — Message de l'erreur (capture d'écran de l'ingénieur, transcrite) : « La feuille ne compile pas — la dernière page compilée reste affichée : error: can only be used when context is known — lib/calc-engine.typ:1149:47 — `let marks = box(width: parts * part, height: measure[0].height, {` — hint: try wrapping this in a `context` expression — while calling `plan-scale-bar` at lib/sheet.typ:262:27 `plan-scale-bar(p.scale.units_per_m * size.s, p.crop.w * size.s)` — while calling `sheet-viewport` at Plans/B02.typ:33:1 »
>
> **T5** — « Permettre de tourner les poteaux avec le cercle qui apparaît à la sélection, et non plus seulement par l'angle saisi en texte. »
>
> **T6** — « À l'activation d'un outil de dessin (par exemple S pour un poteau), afficher tout de suite dans le volet de droite les options de l'objet, comme si un objet déjà dessiné du même type était sélectionné. Vaut pour tous les outils de dessin. »
>
> **T7** — « Numéroter les positions de façon incrémentale : chaque nouvel objet dessiné augmente le numéro de 1. Les préfixes déjà en place dans l'onglet ne changent pas (S, T, …) ; seule la numérotation change, et elle vaut pour tous les types d'objets. — 1er étage : S101, S102, S103, … ; T101, T102, T103, … — 2e étage : S201, S202, … Le compteur est propre à chaque préfixe et à chaque étage. »
>
> **T8** — « Quand une position est supprimée, renuméroter en cascade toutes celles qui la suivent : supprimer S110 fait de S111 un S110, de S130 un S129, etc. »
>
> **T8b** — « La renumérotation est reportée partout : remplacement dans tous les documents Typst du projet (rapport, annexes, feuilles exportées) qui citent ces positions. »
>
> **T9** — « Ajouter dans le volet de droite, au-dessus de la position, un champ *Section*. On y choisit le numéro d'une autre position, dont la section est alors reprise. — La section est reprise par copie uniquement, sans lien : elle ne suit pas la position source si celle-ci change. »
>
> **T10** — « Par défaut, la section proposée est celle du dernier objet du même type dessiné (en dessinant un poteau : celle du dernier poteau dessiné). »
>
> **T11** — « Permettre de définir soi-même la section : choisir un type de section, puis saisir ses dimensions dans des champs séparés. Tous les types de section existants sont repris (4 types bois et familles du SZS C5, voir `calc/domains/section.py`). Champs de dimension proposés, d'après `STEEL_NUMBERS` / `STEEL_FORMS` (tenus égaux à SZS C5 par `tests/test_section.py`) : `rec` : b, h ; `cir` : d ; `pla` : t (existent déjà) — `clt` : épaisseurs de couches t₁ / t₂ / … — IPE, IPEA, IPN, UPE, UPN, HEA, HEB, HEM, IPET, HEAT, HEBT : la taille (un champ, par exemple IPE 200) — HD, HL : h, et m en option — T : h, ou h × b × t — L : a × t, ou a × b × t — RND, VKT, ZNP : un champ (diamètre ou côté) — ROR : d × t — RRK, RRW : a × t, ou h × b × t — FLA, FLB : b × t — BLE : t, ou b × t, ou b × l × t »
>
> **T12** — « Ne pas ajouter les types de SZS C4 (poutre à âme pleine soudée, caisson) ni de SZS C1 (poteau mixte, poutre mixte) : ce sont des ensembles et non des profils de catalogue. »
>
> **T13** — « Seules les tables des matières de SZS C5 ont été relues ; les tables de profils (pages 30 à 88) n'ont pas été rouvertes pour ces champs. »
>
> **T14** — « Afficher la longueur des éléments (longueur de barre ou de mur) sur le plan, avec la même présentation que dans l'onglet *Positions* (voir la nouvelle issue « Positions »). »
>
> **T15** — « Afficher le résumé (les métrés) sur le plan : par matériau et par section, longueurs et volumes, avec le même périmètre au choix que dans *Positions* (tout ce qui est dessiné dans le document, un seul plan, ou des positions choisies). »
>
> **T16** — « Reprendre ces deux options (longueurs des éléments, résumé) dans l'export PDF du plan de positions. »
>
> **T17** — « Remarque : « Longueurs des éléments » existe déjà dans la carte de l'échelle (v0.117, `docs/ui/window.md`). Le besoin porte donc surtout sur le résumé, sur l'export PDF et sur l'alignement avec l'onglet *Positions*. »

## 3. Exigences fonctionnelles

### REQ-001 — La barre d'échelle compile dans les feuilles (et dans *Affichage*)
- **Exigence** : Woodcore doit compiler une feuille dont un `sheet-viewport` ou un `sheet-fire-viewport` porte `scale-bar: true`, et `show-plan(scale-bar: true)` / `show-fire-plan(scale-bar: true)`, sans erreur : `plan-scale-bar` ne dépend plus d'un `context` fourni par son appelant. **Cause établie** (lecture du code, revue B) : `lib/calc-engine.typ:1076-1082` appelle `measure[…]` ; `plan-scale-bar` est appelée sans `context` par `sheet-viewport` (`lib/sheet.typ:262`) **et par `sheet-fire-viewport`** (`lib/sheet.typ:452`), alors que `show-plan` et `show-fire-plan` (`lib/calc-engine.typ:1233`, `:1331`) l'appellent dans un `layout`. Le correctif est fait en un seul endroit : `plan-scale-bar` enveloppe son corps dans `context`. La capture de l'ingénieur est une feuille (vue Export) ; pour la vue Affichage, le défaut est reproduit avant d'être affirmé, et le test de `show-plan(scale-bar: true)` reste.
- **Source** : T4, T4b
- **Priorité** : doit
- **Critère d'acceptation** : un test compile une feuille avec `sheet-viewport(plan: …, scale-bar: true)` et une avec `sheet-fire-viewport(plan: …, scale-bar: true)` sur des plans calibrés de `tests/projet-exemple/` (échec avant, succès après) ; la barre est présente dans la sortie ; `show-plan(scale-bar: true)` et `show-fire-plan(scale-bar: true)` compilent comme avant ; la boîte `<woodcore-sheet-box>` d'un viewport est inchangée.

### REQ-002 — Rotation d'un poteau avec un cercle à la sélection
- **Exigence** : à la sélection d'un élément tournable (`plan.ROTATABLE` : poteau S, et appui ponctuel M à un point), une poignée ronde de rotation apparaît sur le canevas, à distance constante à l'écran quel que soit le zoom ; la faire glisser règle l'`angle` de l'élément (sens horaire, comme le dessin), Maj par pas de 15° (D-015), en un seul pas d'« Annuler », et seulement si l'angle a changé. Le champ d'angle et le bouton « Tourner de 90° » restent et suivent le glisser. Une seule normalisation d'angle (`plan.set_element_angle`).
- **Source** : T5 (étendu au type M, même champ `angle` de `plan-source` 1.4 — *inféré*)
- **Priorité** : doit
- **Critère d'acceptation** : test de canevas (hors écran) : sélectionner un poteau → une poignée ronde existe ; la glisser vers un point donne l'angle attendu dans la source ; Maj arrondit à 15° ; un clic sans mouvement ne pousse aucun pas d'historique ; un pas d'« Annuler » rétablit l'angle précédent ; le champ d'angle affiche la valeur.

### REQ-003 — Numérotation incrémentale par préfixe et par étage ; dessiner crée la position
- **Exigence** : un objet dessiné qui porte une position (pas Ö, B, ni les charges PL / LL) reçoit le numéro `préfixe + caractère d'étage + deux chiffres au moins`, le compteur étant propre à chaque préfixe et à chaque étage et augmentant de 1 à chaque objet (S101, S102, … ; T101, … ; S201, …) — `positions_store.propose_id`, calculé sur les positions du projet **et** les numéros déjà dessinés et non enregistrés. **Un numéro désigne un objet** (D-007) : le dessin ne réutilise plus le numéro d'un autre objet. Le numéro est **proposé sans rien écrire** ; « Enregistrer » le plan crée, en une opération, les positions nouvelles avec leur section (D-009). Dessiner, annuler, redessiner ne laisse aucun trou.
- **Source** : T7, Q-004, Q-007
- **Priorité** : doit
- **Critère d'acceptation** : test de domaine : trois S dessinés au 1er étage donnent S101, S102, S103 ; un T donne T101 ; un S au 2e étage donne S201 ; dessiner S103, annuler, redessiner redonne S103. Test de fenêtre : avant « Enregistrer », `positions.json` est inchangé ; après, il porte S101–S103 avec leur section ; le numéro n'est demandé qu'une fois par objet.

### REQ-004 — Une position sans objet : suppression et renumérotation en cascade
- **Exigence** : à l'enregistrement d'un plan, une position dont plus aucun objet n'est dessiné (sur aucun plan) est proposée à la suppression ; la suppression depuis l'onglet *Positions* suit le même chemin. Supprimer une position renumérote, d'un cran, toutes celles du même préfixe et du même étage qui la suivent (S110 supprimée : S111 devient S110, S130 devient S129), dans **toutes** les données du projet qui portent le numéro : `positions.json`, `plans/*.json` (hors charges), `checks/*.json`, `details/*.json` (schémas). Avant d'écrire, Woodcore montre un aperçu (numéros changés, fichiers, occurrences) et demande une confirmation ; l'opération est tout-ou-rien, précédée d'une sauvegarde dans les archives du projet, **et ne s'annule pas par « Annuler »** (la sauvegarde la restaure). Après elle, les piles d'annulation sont vidées et les onglets relisent les fichiers.
- **Source** : T8, Q-004, Q-007
- **Priorité** : doit
- **Critère d'acceptation** : test sur une copie de `tests/projet-exemple/` : après suppression de X, chaque numéro suivant diminue de 1 dans les quatre magasins ; aucun numéro ne manque ni n'est dupliqué ; S111→S110 alors que S110 existe encore est fait sans collision (une table injective, un seul passage) ; un échec simulé en cours d'écriture ne laisse aucun fichier modifié ; un fichier changé entre l'aperçu et l'écriture arrête tout ; les charges `L101` ne sont pas touchées ; un plan dessiné avant ce changement dont des éléments partagent un numéro se relit comme avant, et la renumérotation déplace tous les éléments qui portent le numéro (CON-006).

### REQ-005 — La renumérotation est reportée dans les documents Typst
- **Exigence** : la même opération remplace les numéros cités dans tous les `.typ` des trois documents et de `Plans/` — jamais `_woodcore/`, les archives, `Template/` ni le journal (D-010) —, sur le mot entier (`S11` ne touche ni `S110` ni `S1100` ; ni `rgb("#D101")`, ni `Images/S101.png`). L'aperçu liste **chaque occurrence avec sa ligne** et chacune peut être décochée (une nuance d'acier `S355` quand une position S355 existe). Les octets hors des numéros remplacés sont inchangés, fins de ligne comprises.
- **Source** : T8b, Q-008
- **Priorité** : doit
- **Critère d'acceptation** : test : un `.typ` qui cite `"S111"` cite `"S110"` après la suppression de S110 ; `S1110`, `#D101`, un chemin et une occurrence décochée ne sont pas touchés ; tout octet hors d'un numéro remplacé est identique (CRLF et LF) ; aucun fichier de `_woodcore/` n'est lu ni écrit.

### REQ-006 — Champ *Section* : reprendre la section d'une autre position
- **Exigence** : le volet de droite offre, au-dessus de la position, un champ *Section* où l'on choisit le numéro d'une autre position ; son type de section, sa dimension **et ses unités** sont alors **copiés**, sans lien (la suite n'est pas suivie). La copie est gardée avec le dessin et écrite par « Enregistrer » (D-011) ; « Annuler » la défait.
- **Source** : T9, Q-009
- **Priorité** : doit
- **Critère d'acceptation** : test : copier la section de S101 (rec 10/20 cm) dans S102 puis enregistrer écrit `section_type`, `dimension`, `units` de S102 ; modifier ensuite S101 laisse S102 inchangée ; annuler avant l'enregistrement ne laisse rien dans `positions.json`.

### REQ-007 — Section proposée par défaut : celle du dernier objet du même type
- **Exigence** : un objet nouveau reçoit la section de la dernière position du même `type` (pour un poteau : le dernier poteau), prise dans l'ordre des positions du projet puis des objets dessinés et non enregistrés ; s'il n'y en a pas, aucune section (D-003). Fonction Qt-free.
- **Source** : T10
- **Priorité** : doit
- **Critère d'acceptation** : test de domaine : S101 créée avec « rec 100/200 », S102 dessinée ensuite reçoit « rec 100/200 » ; un T sans T antérieur n'en reçoit aucune.

### REQ-008 — Définir soi-même la section : un type, des champs séparés
- **Exigence** : choisir un type de section puis saisir ses dimensions dans des champs séparés, pour **tous** les codes de `section.CODES` (4 types bois et les 24 familles de SZS C5). Une seule table de **formes** par code dans `calc/domains/section.py`, dont `STEEL_NUMBERS` et `STEEL_FORMS` sont dérivés : `rec` (b, h) ; `cir` (d) ; `pla` (t) ; `clt` des couches t₁, t₂, … en nombre libre (D-004) ; IPE, IPEA, IPN, UPE, UPN, HEA, HEB, HEM, IPET, HEAT, HEBT (la taille) ; HD, HL (h ; h, m) ; T (h ; h, b, t) ; L (a, t ; a, b, t) ; RND, VKT, ZNP (un champ) ; ROR (d, t) ; RRK, RRW (a, t ; h, b, t) ; FLA, FLB (b, t) ; BLE (t ; b, t ; b, l, t). Où un code a plusieurs formes, un sélecteur de forme précède les champs. Les champs composent et lisent le champ `dimension` existant : aucun nouveau champ de données, aucune `schema_version` ne bouge ; une valeur non touchée n'est jamais réécrite. Le widget est **un seul**, partagé par l'onglet *Positions* et le plan (`calc/tools/section_fields.py`).
- **Source** : T11, T13
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_section.py` : l'ensemble des codes à formes égale `CODES` ; pour chaque forme `join ∘ split` rend le texte ; les bornes de `STEEL_NUMBERS` sont celles des formes ; un texte que `parse` lit sans forme (un T à deux nombres) reste en texte ; une position enregistrée avant s'ouvre avec ses champs remplis ; `tests/test_positions_tab.py` : la règle « non touché, jamais réécrit » tient avec le widget partagé.

### REQ-009 — Outil règle (plan de positions et plan d'incendie)
- **Exigence** : les deux plans offrent un outil « règle » : deux clics (accrochés comme la calibration) donnent la distance, en mètres si le plan est calibré, sinon en unités de la feuille (dites comme telles, jamais « m »), affichée à l'écran ; **rien n'est enregistré, annulé ni exporté** (D-005, D-012). Un nouveau clic la remplace ; Échap l'efface. La distance vient de `plan.distance_m`, la même fonction que les cotes et les longueurs.
- **Source** : T1, Q-002, Q-013
- **Priorité** : doit
- **Critère d'acceptation** : test de domaine : la distance de deux points d'un plan calibré est `plan.distance_m` ; test de fenêtre (plan de positions et plan d'incendie) : après la règle, la source du plan est identique octet pour octet, l'historique est vide, Échap efface la mesure.

### REQ-010 — Quatre sortes de cotes, sur un noyau commun
- **Exigence** : le plan de positions offre les cotes **alignée** (deux points, parallèle à eux), **horizontale / verticale**, **chaîne de cotes** (bout à bout sur une ligne) et **d'angle** (Q-003 ; rayon / diamètre abandonnés, Q-011). Ce sont les sortes de la statique et des schémas (`horizontal|vertical|parallel|angle`) plus la chaîne. Chacune est une donnée du plan (ARCH-003) placée par des clics accrochés, se déplace et se supprime comme une entrée, porte une valeur **calculée** de la géométrie (jamais saisie) et se règle avec les facteurs `line` et `text`. Géométrie et dessin viennent d'un noyau commun (ARCH-004), avec les **mêmes icônes d'outil** dans la statique, les schémas et le plan (UI-004). Sur un plan sans échelle, une cote n'a pas de valeur en mètres : l'export **avertit** et ne l'imprime pas (D-016).
- **Source** : T2, Q-003, Q-010, Q-011
- **Priorité** : doit
- **Critère d'acceptation** : test de domaine par sorte : une cote entre deux points connus d'un plan calibré porte la valeur juste en mètres (en degrés pour l'angle) ; son SVG est le même dans Woodcore et dans l'export ; un plan sans cote se dessine octet pour octet comme avant (hash `FROZEN` et `FROZEN_EXAMPLE` inchangés) ; une cote sur un plan sans échelle donne un avertissement nommant le plan.

### REQ-011 — Les cotes s'affichent ou non dans les vues Dessin, Affichage et Export
- **Exigence** : l'affichage des cotes s'active et se désactive dans les vues **Dessin, Affichage et Export**, indépendamment (Q-001 puis Q-012 : la vue Import montre le document, pas le dessin). Dessin : un réglage de la fenêtre gardé dans les réglages de l'ingénieur (`settings.json`), forcé visible pendant qu'un outil de cote est actif. Affichage et Export : l'argument `dimensions:` des commandes (`show-plan`, `doc-plan`, `sheet-viewport`), vrai par défaut comme `axes:`, faux dans les détails de `calc-block`.
- **Source** : T3, Q-001, Q-012
- **Priorité** : doit
- **Critère d'acceptation** : test par vue : cocher les cotes dans une vue ne change pas les deux autres ; `dimensions: false` imprime le plan sans aucune cote ; un `.typ` déjà écrit garde sa forme canonique (l'argument n'est écrit que s'il diffère du défaut).

### REQ-012 — Longueurs des éléments : une seule mesure, et un réglage par commande
- **Exigence** : la longueur d'un élément (barre, mur, côté de dalle) est calculée par **une** fonction de `plan.py` (`plan.distance_m` / `plan.element_length_m`), que lisent le dessin, l'export, les métrés, la règle et les cotes — les quatre calculs d'aujourd'hui (`quantities`, `build_record`, `plan_svg._length`, `_side_lengths`) en deviennent des appels. Elle s'imprime comme aujourd'hui (m, deux décimales) et c'est cette présentation que reprendra l'onglet *Positions* (#14). Les commandes `show-plan` et `sheet-viewport` gagnent `lengths:` (Q-016) pour les montrer ou les cacher sortie par sortie : un booléen comme `axes:`, vrai par défaut (ce que le plan dessine, `show_lengths` / `show_length`), faux ne les imprimant pas (mis en œuvre ainsi : Typst ne peut dessiner ce que le plan n'a pas dessiné).
- **Source** : T14, T16, T17, Q-016
- **Priorité** : doit
- **Critère d'acceptation** : test : longueur du record = longueur du SVG = celle des métrés, pour chaque élément de l'exemple ; `lengths: false` n'imprime aucune longueur, `lengths: true` imprime exactement ce que le plan montre ; le hash `FROZEN` n'est repris qu'une fois, la raison écrite en tête du test ; `FROZEN_EXAMPLE` est inchangé.

### REQ-013 — Résumé des métrés
- **Exigence** : Woodcore calcule le résumé des métrés : par **matériau** puis par **section**, le nombre de pièces, la longueur [m] et le volume [m³], avec une ligne de total par matériau (Q-014), sur un périmètre au choix : **tout ce qui est dessiné** (tous les plans de positions), **un ou plusieurs plans**, ou **des positions choisies** (T15). Volume : `rec` longueur × b × h ; `cir` longueur × π d²/4 ; `pla` et `clt` aire de la dalle (D) × épaisseur, « — » sur une ligne (un mur n'a pas de hauteur dans le plan) ; acier « — » (D-008) ; une position sans section est comptée en longueur, volume « — », avec un avertissement. Ö, B et les charges n'y entrent pas ; un numéro partagé d'un ancien plan compte chaque élément. Le calcul est une fonction pure de `calc/domains/quantities.py`.
- **Source** : T15, Q-005, Q-014
- **Priorité** : doit
- **Critère d'acceptation** : test de domaine : sur des plans d'essai, le résumé de tout, d'un plan et de deux positions choisies donne des totaux justes à la main (dont une dalle CLT : aire × t, un mur CLT : « — », un IPE : longueur et « — ») ; la présentation (colonnes, tri, décimales m 2 / m³ 3) est figée par le test.

### REQ-014 — Le résumé et les longueurs dans l'export PDF
- **Exigence** : le résumé s'imprime par deux commandes (Q-015) : `show-plan-quantities(scope: …)` dans un document et `sheet-quantities(scope: …)` sur une feuille, `scope` valant `all`, `plans` (avec `plans:`) ou `positions` (avec `positions:`), sur le modèle de `show-position-list` / `sheet-position-list` ; Typst imprime ce que Python a calculé (`data/quantities.json`, ARCH-005), il ne recalcule rien, sauf la somme des lignes d'un périmètre `positions`, tenue égale à `quantities.summary` par un test. Les longueurs suivent REQ-012. Le bloc `sheet-quantities` se place et se déplace sur la feuille comme `sheet-position-list` (vue Export).
- **Source** : T15, T16, Q-015
- **Priorité** : doit
- **Critère d'acceptation** : test : une feuille exportée en PDF avec `sheet-quantities(scope: "plans", plans: (…))` contient les totaux attendus ; `show-plan-quantities(scope: "positions", positions: (…))` imprime les mêmes nombres que `quantities.summary` ; chaque commande a son `///`, deux exemples qui compilent et sa traduction.

### REQ-015 — Options d'un objet dès l'activation de son outil
- **Exigence** : activer un outil de dessin d'objet (les types de `plan.TYPES`, les charges, les axes) affiche aussitôt dans le volet de droite les options de l'objet, comme si un objet du même type était sélectionné ; ce qui y est réglé (sous-type, angle, longueur affichée, portée, section…) s'applique aux objets dessinés ensuite (*défauts d'outil*). Tant qu'un outil de dessin est actif, le volet suit l'outil ; il suit la sélection avec l'outil Sélection (D-014). Les champs qui n'ont de sens qu'avec un objet (son numéro — remplacé par « prochain : S104 » —, la remise du numéro, l'avertissement, Supprimer, les facteurs propres) n'y sont pas. Une fonction Qt-free (`plan.apply_defaults`) ne recopie que les champs valides pour le type et le nombre de points (un M à deux points ne reçoit pas d'angle).
- **Source** : T6
- **Priorité** : doit
- **Critère d'acceptation** : test de fenêtre : pour chaque outil de `plan.TYPES`, le volet montre les mêmes champs d'objet que la sélection d'un élément du type ; un angle de 45° réglé avant de dessiner donne un poteau à 45° ; un M à deux points n'a pas d'`angle` ; les défauts survivent à un changement de langue ; le plan d'incendie est inchangé.

### REQ-016 — « Copier les valeurs » : supprimer une position encore citée
- **Exigence** : une position citée ailleurs (une vérification, un élément de schéma, un `.typ`) **n'est pas supprimée** : Woodcore liste ce qui la cite (fichier, ligne) et refuse (Q-006). Il offre cependant **« Copier les valeurs »** : la position est supprimée et renumérotée comme en REQ-004, mais ses valeurs sont gardées sous le nom **`<numéro>-old`** (`S110-old`, puis `-old2` si le nom est pris) dans `Woodcore-Datei/positions-archive.json`, hors des listes de positions, et toutes ses citations sont réécrites vers ce nom dans la même opération (Q-006b, D-013). Partout où une ancienne position est appelée, le rapport imprime un **message orange** : « Calcul sur les valeurs de l'ancienne position S110 » (dans la langue du document), et la fenêtre le signale dans ses avertissements.
- **Source** : Q-006, Q-006b (réponses de l'ingénieur, 2026-10-08)
- **Priorité** : doit
- **Critère d'acceptation** : test : supprimer S110 citée par `checks/BI-01.json` et par `#member("S110")` est refusé, avec la liste des citations ; « Copier les valeurs » écrit `S110-old` dans `positions-archive.json`, réécrit les deux citations en `S110-old`, renumérote S111→S110 ; le document compile, imprime les valeurs de l'ancienne S110 et le message orange ; une seconde suppression du même numéro donne `S110-old2`.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Chaînes de l'interface
- **Exigence** : toute chaîne nouvelle existe en fr, de et en, jamais en dur : les mots de la **fenêtre** dans les `STRINGS` de leur module (tenus par `tests/test_i18n.py`), ceux que le **rapport** imprime dans `calc/i18n/strings.json`, les `///` traduits dans `calc/i18n/commands.json`. Dans la fenêtre, une cote se dit « Cote » (de « Maß », en « Dimension »), jamais « Dimension » en français, qui désigne la section.
- **Source** : CLAUDE.md (trois langues, no hardcoding) ; revues B et C
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_i18n.py` et `tests/test_commands.py` passent avec les nouvelles clés.

### UI-002 — Le champ *Section* est au-dessus de la position
- **Exigence** : dans le volet de droite d'un objet (ou d'un outil, REQ-015), *Section* — copier d'une position, ou type + forme + champs (REQ-008) — est placé au-dessus du champ de la position.
- **Source** : T9, T11
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre hors écran : ordre des widgets ; la liste de copie propose les autres positions.

### UI-003 — Rapport : cotes, longueurs et résumé imprimés
- **Exigence** : les cotes (si `dimensions:` le permet), les longueurs (selon `lengths:`) et le résumé (tableau booktabs : trois filets, sans grille, chaque colonne alignée selon ce qu'elle tient) s'impriment dans la langue du document ; « — » pour un volume non calculé.
- **Source** : T3, T14, T15, T16 ; mémoire « Table style »
- **Langues** : fr / de / en
- **Critère d'acceptation** : les exemples des commandes compilent en trois langues ; un test lit le texte du tableau.

### UI-004 — Mêmes icônes d'outils de cote dans les trois onglets
- **Exigence** : la statique, les schémas et le plan de positions montrent les mêmes icônes pour les mêmes sortes de cote (alignée, horizontale / verticale, angle ; la chaîne a la sienne), tirées d'une seule source ; les nouveaux boutons ont la hauteur des autres.
- **Source** : Q-010 (réponse de l'ingénieur : « utiliser les mêmes logos d'outils pour les 3 »)
- **Langues** : fr / de / en (infobulles)
- **Critère d'acceptation** : test : l'icône d'une sorte est la même clé dans les trois onglets ; `tests/test_toolbar.py` passe.

## 5. Exigences d'architecture

### ARCH-001 — Une seule renumérotation, sans Qt, textuelle et tout-ou-rien
- **Exigence** : `calc/renumbering.py` (Qt-free, à côté de `positions_store.py`) calcule un **aperçu** sans écrire — la table `{ancien: nouveau}`, les citations des numéros supprimés, les fichiers et les occurrences — puis l'**applique** : sauvegarde des octets dans les archives, fichier d'intention, écriture par un `commit` public tiré de `sharing._commit` (pas un sixième écrivain), `positions.json` en dernier. Les JSON sont réécrits **textuellement** (seuls les jetons de numéro changent), les `.typ` par un seul `re.sub` par fichier. La même fonction sert au renommage d'une position (`renamed_from`). Les transformations par magasin vivent dans leurs domaines (`plan.renumber_labels`, qui exclut les charges). Le périmètre des fichiers vient de `project.py`. Toute méthode de fenêtre qui écrit est dans `WRITERS`.
- **Source** : T8, T8b ; principes 1 et 2 ; revue A
- **Critère d'acceptation** : test « le module n'importe aucun module Qt » ; test de restauration depuis la sauvegarde ; le renommage passe par la même fonction ; `test_every_writer…is_guarded` étendu.

### ARCH-002 — Métrés : un module de domaine partagé
- **Exigence** : `calc/domains/quantities.py` (fonction pure `summary(plan_sources, position_rows, scope)`, sans `project.current()`) et `section.area_mm2` ; aucune longueur, aire ni volume recalculé dans la fenêtre ; Typst n'additionne que les lignes d'un périmètre `positions`. L'onglet *Positions* (#14) reprendra ce module.
- **Source** : T14, T15 ; principe « une seule source » ; revue B
- **Critère d'acceptation** : test hors Qt ; `plan.quantities` (légende) appelle la même fonction de longueur ; test de parité Python / Typst.

### ARCH-003 — Cotes du plan : une collection de la source, versionnée
- **Exigence** : les cotes sont une collection `dimensions` de `plan-source` (`{kind, points, offset?, style?}`, coordonnées de feuille, pas des renvois aux éléments : une cote ne suit pas un élément déplacé), **pas** un type de `TYPES` ; `plan-source` passe à **1.5** (un Woodcore plus ancien dit « fichier plus récent ») ; `check_source` refuse une cote mal formée en nommant le fichier et le champ ; ligne `("plan", "dimensions"): ("line", "text")` de `figure_style` ; marqueur `<!-- dimensions -->` écrit **seulement** si la collection existe ; champ additif `dimensions` de `plans.json` (valeur et unité calculées, l'export reste 1.3), décrit dans `schemas/plans.schema.json`.
- **Source** : T2, T3 ; revue B
- **Critère d'acceptation** : source 1.4 relue ; 1.5 avec cotes relue et validée ; plan sans cote octet pour octet identique ; fichier mal formé = arrêt de l'export nommant fichier et champ.

### ARCH-004 — Un noyau de cotes pour la statique, les schémas et le plan
- **Exigence** : `calc/domains/dimension.py` porte la géométrie des cotes sur des points résolus (extrémités, direction, ligne, valeur, coin, angle ; unité passée en paramètre) et leur dessin SVG Tiny ; `statics.py`, `schema.py` et `plan` le lisent ; les constantes de sortes et d'unités ne sont écrites qu'une fois (`validation.py` les lit). Le comportement de la statique et des schémas est inchangé (Q-010).
- **Source** : Q-010 ; revues B et C (risque de troisième copie)
- **Critère d'acceptation** : `tests/test_statics.py`, `tests/test_schema.py` et leurs empreintes inchangés ; `tests/test_constants.py` : une seule définition des sortes.

### ARCH-005 — `data/quantities.json`, un contrat versionné
- **Exigence** : `export_all.py` écrit `data/quantities.json` (`schemas/quantities.schema.json`, `schema_version` 1.0 : lignes par position et par plan avec matériau, section, longueur, volume et unités, et les totaux « tout » et « par plan »), validé avant écriture ; `lib/positions.typ` le lit (`load-quantities()`), hors de la chaîne `calc-engine → bibliography → distance → formula`.
- **Source** : T15, T16 ; revue B ; principe « contrats versionnés »
- **Critère d'acceptation** : le fichier valide son schéma ; l'export reste reproductible octet pour octet.

### ARCH-006 — Le volet sur une cible, et des modules plus petits
- **Exigence** : le volet d'un objet se construit sur une **cible** — un élément ou les défauts d'un outil (`ToolDefaults`, qui généralise `canvas.subtypes`) — dans `calc/tools/plan_properties.py` ; la règle, les cotes et la rotation vivent dans `calc/tools/plan_canvas_tools.py`, appelés par une table plutôt que par de nouvelles branches de `press_select` / `mouseMoveEvent` ; `plan_tab.py` et `plan_canvas.py` ne grossissent pas.
- **Source** : revue C (RISK-012, -014)
- **Critère d'acceptation** : `plan_tab.py` et `plan_canvas.py` ne gagnent pas plus d'une centaine de lignes chacun ; les tests de fenêtre existants passent.

## 6. Contraintes

- **CON-001** — Aucun type de SZS C4 (poutre à âme pleine soudée, caisson) ni de SZS C1 (poteau mixte, poutre mixte) : ce sont des ensembles et non des profils de catalogue. Source : T12.
- **CON-002** — Les noms et l'ordre des champs des familles d'acier sont confirmés sur les tables de profils de SZS C5 (pages 30 à 88, édition de `ExternalFiles/000-Normes/`) avant d'être figés ; tant qu'une famille n'est pas relue, ses champs portent des clés neutres et des libellés de glossaire. Source : T11, T13 ; CLAUDE.md.
- **CON-003** — Un plan, une position ou un document existant se relit toujours ; `plan-source` 1.4 est relu par 1.5 ; aucune autre `schema_version` existante ne bouge. Source : `docs/architecture/data-contracts.md`.
- **CON-004** — Plusieurs sessions éditent ce dépôt : `lib/calc-engine.typ`, `calc/domains/statics.py`, `calc/tools/statics_tab.py`, `calc/tools/woodcore_gui.py`, `calc/tools/chrome.py` et `tests/test_views.py` sont modifiés par des pairs (la session de l'issue 13 a annoncé `woodcore_gui.py`, `chrome.py`, `test_views.py`) : édition ciblée, message au pair avant d'y toucher. Source : CLAUDE.md.
- **CON-005** — `docs/decisions.md`, `docs/ui/window.md`, `docs/conventions/testing.md` et `CHANGELOG.md` sont édités, jamais réécrits, en gardant les fins de ligne CRLF. Source : CLAUDE.md.
- **CON-006** — Un plan dessiné avant ce changement, dont des éléments partagent un numéro, se relit et se dessine comme avant ; le partage n'est plus créé, il n'est pas supprimé. Le partage voulu des **schémas** (v0.73, pièce coupée) reste. Source : CON-003, Q-004, revue A.
- **CON-007** — L'export reste reproductible octet pour octet (`test_the_export_is_reproducible`), et un plan sans cote ni option nouvelle se dessine comme avant. Source : `docs/conventions/testing.md`.

## 7. Décisions prises

- **D-001** — L'issue #9 est la source de ce travail ; l'issue #14 (onglet *Positions* : longueurs et résumé) est hors de cette spécification mais en reprend le module (ARCH-002) et la présentation (Q-014). *Prix : #14 reste à faire.*
- **D-002** — La suppression d'une position montre un aperçu (numéros, fichiers, occurrences à cocher) et demande une confirmation ; l'opération est tout-ou-rien, sauvegardée avant, non annulable par « Annuler ».
- **D-003** — « Le dernier objet du même type » est la dernière position du même `type` dans l'ordre des positions du projet, puis des objets dessinés et non enregistrés, tous plans confondus.
- **D-004** — Les champs d'une section `clt` sont des rangées d'épaisseurs (ajouter / retirer une couche), en nombre libre.
- **D-005** (Q-002) — La règle est une **mesure éphémère** : rien n'est enregistré ni exporté. *Prix : pour garder une mesure, il faut une cote.*
- **D-006** (Q-003, Q-011) — Quatre sortes de cotes : alignée, horizontale / verticale, chaîne, angle ; rayon et diamètre abandonnés (un plan n'a ni cercle ni arc). *Prix : quatre formes de données et deux commandes d'argument à documenter.*
- **D-007** (Q-004) — Dessiner crée la position et un numéro désigne un objet **d'un plan**. *Prix : disparaissent, pour les plans, le partage d'un numéro entre éléments identiques (v0.44), la règle « un plan ne dessine que les positions de la feuille » (v0.45) et l'alerte « position à ajouter » (v0.47) ; la règle « un numéro supprimé n'est jamais réattribué » (`propose_id`) devient « les numéros restent continus, par cascade ». Les schémas gardent leur partage (v0.73). À consigner dans `docs/decisions.md`.*
- **D-008** (Q-005) — Volumes du bois seul ; l'acier est compté en longueurs, volume « — ». *Prix : résumé incomplet pour l'acier jusqu'à la saisie des aires des profils, inscrite dans `docs/open-questions.md`.*
- **D-009** (Q-007) — Une position est écrite à l'**enregistrement** du plan : le dessin propose le numéro sans écrire ; « Enregistrer » crée les positions nouvelles et ouvre la suppression des positions sans objet. *Prix : une position n'existe dans l'onglet *Positions* qu'après l'enregistrement du plan.*
- **D-010** (Q-008) — Tous les `.typ` des trois documents et de `Plans/`, sur le mot entier, chaque occurrence listée et décochable ; jamais `_woodcore/`, archives, `Template/`, journal. *Prix : la prose est réécrite elle aussi, ce que la liste permet de refuser cas par cas.*
- **D-011** (Q-009) — La section choisie dans le volet du plan est écrite à l'enregistrement du plan, avec la position. *Prix : idem D-009.*
- **D-012** (Q-013) — Règle sur les deux plans ; cotes sur le plan de positions seul pour cette fois (le plan d'incendie a ses propres mesures). Raison écrite dans `docs/domain/fire-plans.md`.
- **D-013** (Q-006, Q-006b) — Une position citée n'est pas supprimée, sauf par « Copier les valeurs » : ses valeurs sont gardées sous `<numéro>-old` dans `positions-archive.json`, ses citations réécrites vers ce nom, et chaque appel imprime un message orange. *Prix : un nouveau fichier de données (contrat, schéma, `schema_version` 1.0) et un repli de lecture dans les commandes qui lisent une position.*
- **D-014** — *Par défaut, à confirmer à l'approbation* : tant qu'un outil de dessin est actif, le volet montre ses défauts ; il suit la sélection avec l'outil Sélection. *Prix : régler l'objet qu'on vient de dessiner demande de revenir à Sélection.*
- **D-015** — *Par défaut, à confirmer* : Maj fait tourner par pas de 15° ; la règle et les cotes n'ont pas de raccourci clavier (R est déjà pris par « Tourner de 90° ») ; `dimensions:` vaut vrai par défaut (faux dans `calc-block`) ; `lengths:` vaut vrai.
- **D-016** — *Par défaut, à confirmer* : une cote sur un plan sans échelle est un **avertissement** à l'export et n'est pas imprimée (« une entrée manquante avertit »).

## 8. Hors périmètre

- L'onglet *Positions* lui-même (issue #14) : seuls le module de métrés et sa présentation sont livrés ici.
- Les types de section de SZS C4 et de SZS C1 (CON-001).
- Les aires des profils d'acier et donc leurs volumes (D-008).
- Les cotes de rayon et de diamètre (Q-011) ; les cotes sur le plan d'incendie (D-012) ; des cotes qui suivent un élément déplacé.
- Les cotes dans la vue Import (Q-012).
- Toute charge ou tout calcul de résistance sur un plan (§3.3sexies, §8).
- La vitesse d'enregistrement des positions (autre spécification).

## 9. Idées non retenues comme exigences

- Aucune idée à part dans la source : les exemples de numérotation (S101…, S110 supprimée) et de section (IPE 200) illustrent les règles.

## 10. Questions

### Q-001 — Que sont les « 4 modes d'affichage » où les cotes se règlent ? (T3)
- **Réponse** : les quatre vues de l'onglet (Import, Dessin, Affichage, Export), 2026-10-08 ; précisé par Q-012.

### Q-002 — Que produit l'outil règle ? (T1)
- **Réponse** : mesure éphémère (D-005), 2026-10-08.

### Q-003 — Quelles sortes de cotes ? (T2)
- **Réponse** : alignée, horizontale / verticale, chaîne, angle · rayon · diamètre (D-006), 2026-10-08 ; rayon / diamètre retirés par Q-011.

### Q-004 — Dessiner crée-t-il la position, et un numéro peut-il être partagé ? (T7, T8)
- **Réponse** : dessiner crée la position, un numéro = un objet, supprimer l'objet supprime la position avec confirmation (D-007), 2026-10-08.

### Q-005 — Volumes de l'acier dans le résumé (T15)
- **Réponse** : volumes du bois seul, l'acier en longueurs (D-008), 2026-10-08.

### Q-006 — Que deviennent les références à la position supprimée ? (revue A, RISK-001)
- **Réponse** : « Refuser tant qu'elle est citée. Il est cependant possible de choisir "Copier les valeurs de la positions" (ou quelque chose de similaire mais plus court) afin que, partout où la position est appelée, un message orange apparaît et indique que les calculs portent sur les valeurs d'une ancienne position (en citant laquelle) » — 2026-10-08 (REQ-016, D-013).

### Q-006b — Quel nom porte l'ancienne position dans les fichiers qui la citent ?
- **Réponse** : `S110-old` (puis `-old2`), 2026-10-08 (D-013).

### Q-007 — Quand la position est-elle écrite dans `positions.json` ? (revues A et C)
- **Réponse** : à l'enregistrement du plan (D-009), 2026-10-08.

### Q-008 — Quels `.typ` la renumérotation réécrit-elle, et comment ? (revue A, RISK-006)
- **Réponse** : tous (trois documents et `Plans/`), avec la liste à cocher (D-010), 2026-10-08.

### Q-009 — Quand écrire la section choisie dans le volet du plan ?
- **Réponse** : à l'enregistrement du plan (D-011), 2026-10-08.

### Q-010 — Un noyau de cotes commun ?
- **Réponse** : « noyau commun. Utiliser les mêmes logos d'outils pour les 3 », 2026-10-08 (ARCH-004, UI-004).

### Q-011 — Cote de rayon / diamètre : que mesure-t-elle ?
- **Réponse** : abandonner rayon / diamètre, 2026-10-08 (D-006).

### Q-012 — La vue Import ne montre pas le dessin : y régler les cotes ?
- **Réponse** : cotes réglables dans trois vues (Dessin, Affichage, Export), 2026-10-08 (REQ-011).

### Q-013 — Règle et cotes sur le plan d'incendie ?
- **Réponse** : règle oui, cotes non (D-012), 2026-10-08.

### Q-014 — Présentation du résumé ?
- **Réponse** : totaux par matériau et section — Matériau · Section · Pièces · Longueur [m] · Volume [m³], tri par matériau puis section, total par matériau, m à 2 décimales, m³ à 3, booktabs —, 2026-10-08 (REQ-013).

### Q-015 — Commande du résumé ?
- **Réponse** : deux commandes à périmètre, `show-plan-quantities` et `sheet-quantities`, `scope: all | plans | positions`, 2026-10-08 (REQ-014).

### Q-016 — Longueurs : un réglage par sortie ?
- **Réponse** : argument `lengths:` par commande, 2026-10-08 (REQ-012).

### Q-017 — Préséance du volet entre l'outil actif et la sélection ; pas de rotation ; raccourcis ; cote sans échelle
- **Réponse** : non posée ; défauts D-014, D-015, D-016 soumis à l'approbation.

## 11. Critères d'acceptation

- [x] REQ-001 — les deux viewports compilent avec `scale-bar: true` ; `show-plan` / `show-fire-plan` inchangés.
- [ ] REQ-002 — poignée ronde, glisser = un pas d'« Annuler », Maj 15°, champ d'angle synchronisé.
- [ ] REQ-003 — S101, S102, S103 ; T101 ; S201 ; positions écrites à l'enregistrement, sans trou.
- [x] REQ-004 — cascade juste dans les quatre magasins, sans collision, tout-ou-rien, sauvegarde, onglets relus.
- [x] REQ-005 — `.typ` réécrits sur le mot entier, occurrences décochables, octets alentour inchangés.
- [x] REQ-006 — section (type, dimension, unités) copiée sans lien, écrite à l'enregistrement.
- [x] REQ-007 — section par défaut du dernier du même type.
- [x] REQ-008 — formes de dimension pour tous les codes, widget partagé, aller-retour exact.
- [x] REQ-009 — règle sur les deux plans, rien d'enregistré.
- [x] REQ-010 — quatre sortes de cotes, valeur calculée, noyau commun.
- [x] REQ-011 — cotes réglables dans Dessin, Affichage, Export, indépendamment.
- [x] REQ-012 — une seule mesure de longueur ; `lengths:`.
- [x] REQ-013 — résumé juste sur trois périmètres, présentation figée.
- [x] REQ-014 — `show-plan-quantities` / `sheet-quantities` imprimés dans le PDF.
- [ ] REQ-015 — options d'un objet dès l'activation de l'outil, défauts appliqués.
- [x] REQ-016 — position citée refusée ; « Copier les valeurs » → `-old`, citations réécrites, message orange.
- [x] UI-001 — chaînes en fr / de / en, au bon endroit.
- [x] UI-002 — *Section* au-dessus de la position.
- [x] UI-003 — cotes, longueurs et résumé imprimés en trois langues, booktabs.
- [x] UI-004 — mêmes icônes de cote dans les trois onglets.
- [ ] ARCH-001 — renumérotation unique, Qt-free, textuelle, tout-ou-rien, aussi pour le renommage.
- [x] ARCH-002 — module de métrés partagé, parité Python / Typst.
- [x] ARCH-003 — `dimensions` dans `plan-source` 1.5, plan sans cote inchangé.
- [ ] ARCH-004 — noyau de cotes lu par la statique, les schémas et le plan, comportements inchangés.
- [ ] ARCH-005 — `data/quantities.json` versionné et validé.
- [ ] ARCH-006 — volet sur une cible ; nouveaux modules plutôt que `plan_tab.py` / `plan_canvas.py` plus longs.
- [ ] Documentation : `docs/domain/position-plans.md`, `docs/domain/positions.md`, `docs/domain/fire-plans.md`, `docs/domain/static-models.md` et `docs/domain/detail-schemas.md` (noyau des cotes), `docs/architecture/figure-style.md`, `docs/ui/window.md`, `docs/decisions.md` (D-007, D-009, D-010, D-013 et la forme des cotes), `docs/open-questions.md` (aires d'acier, cotes du plan d'incendie), `docs/conventions/testing.md`, `CHANGELOG.md`, page « Nouveautés » fr / de / en, `///` + deux exemples + `calc/i18n/commands.json` pour `show-plan-quantities`, `sheet-quantities` et les arguments `dimensions:` / `lengths:`.
- [ ] Tests : fichiers du §14 ajoutés ou étendus, et passent ; la suite complète ne régresse pas.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T0 | — | contexte (suite de #4) |
| T1 | REQ-009, D-005, D-012 | capturé |
| T2 | REQ-010, ARCH-003, ARCH-004, D-006 | capturé |
| T3 | REQ-011, UI-003 | capturé |
| T4, T4b | REQ-001 | capturé (cause établie) |
| T5 | REQ-002 | capturé |
| T6 | REQ-015, ARCH-006, D-014 | capturé |
| T7 | REQ-003, D-007, D-009 | capturé |
| T8 | REQ-004, REQ-016, ARCH-001, D-002, D-013 | capturé |
| T8b | REQ-005, ARCH-001, D-010 | capturé |
| T9 | REQ-006, UI-002, D-011 | capturé |
| T10 | REQ-007, D-003 | capturé |
| T11 | REQ-008, UI-002, D-004 | capturé |
| T12 | CON-001, §8 | contrainte |
| T13 | CON-002 | contrainte |
| T14 | REQ-012, ARCH-002 | capturé |
| T15 | REQ-013, REQ-014, ARCH-002, ARCH-005, D-008 | capturé |
| T16 | REQ-012, REQ-014 | capturé |
| T17 | REQ-012 (déjà en place : seul le reste est demandé) | remarque |
| Q-006, Q-006b | REQ-016, D-013 | réponse de l'ingénieur → exigence |
| Q-010 | ARCH-004, UI-004 | réponse de l'ingénieur → exigence |

### Points de la source non résolus

Aucun. Trois réglages par défaut (D-014, D-015, D-016) sont soumis à l'approbation.

## 13. Revue d'architecture

Trois revues indépendantes (agent `architecture-reviewer`, 2026-10-08), une par zone : (A) numérotation, renumérotation et section ; (B) dessin, export et Typst : barre d'échelle, règle, cotes, métrés ; (C) l'onglet Qt. Le code a été lu, pas seulement `docs/`.

### Modules concernés

- **Domaine** : `calc/positions_store.py` (`propose_id` :229, déjà un compteur par symbole et par étage, sans trou ; `create_blank` :328 ; `update` :203 renvoie `renamed_from` ; `delete` :214) ; `calc/domains/plan.py` (`TYPES` :78, `next_load_label` :152, `auto_label` :1035, `plan_labels`/`unknown_labels`/`warnings` :1270-1310, `ROTATABLE` :751, `shows_length` :756, `quantities` :782, `polyline_length` :807, `build_record` :1327 ; source 1.4, export 1.3) ; `calc/domains/plan_svg.py` (marqueurs `axes`/`storeys`/`levels` écrits seulement si la collection existe ; longueurs en dur `:606`, `:631`) ; `calc/domains/section.py` (`STEEL_NUMBERS`, `STEEL_FORMS`, `DIMENSION_FIELDS` :95, `parse`, `sides`) ; `calc/domains/statics.py:849-1032` et `calc/domains/schema.py:748-908` (cotes : deux copies quasi identiques) ; `calc/domains/figure_style.py:51-70` (`ENTRY_KEYS`) ; `calc/validation.py` (`PLAN_KINDS` :622, `*_DIMENSION_*` :743, :850) ; `calc/sharing.py:93-135` (`_put`/`_commit`, écriture tout-ou-rien avec retour arrière) ; `calc/typst_paths.py` (`read_text`/`write_text` gardent les octets et le CRLF ; `_Lexer`) ; `calc/typst_objects.py` (`parse_call`, `ViewportModel` :2008, signatures :51-66).
- **Typst** : `lib/calc-engine.typ` (`plan-scale-bar` :1068, `plan-legend` :1088, `plan-figure` :1137, `show-plan` :1189, `show-fire-plan` :1314, `show-static-model(dimensions:)` :1437 — fichier modifié par un pair, CON-004) ; `lib/sheet.typ` (`sheet-viewport` :235, `sheet-legend` :367 qui additionne déjà en Typst, `sheet-fire-viewport` :430, `sheet-position-list` :538) ; `lib/positions.typ` (`position-list-ids(scope: all|plans|storey)` :42).
- **Fenêtre** : `calc/tools/plan_tab.py` (2245 l. : `init_shortcuts` :833, R déjà pris par `turn_quarter` ; `choose_tool` :1557 ne touche pas le volet ; `create_blank_position` :1593 ; `propose_label` :1628 ; `refresh_selection` :1779 ; `element_properties` :1857 et ses setters :2042-2135, tous liés à l'élément sélectionné ; `save` :2186 refuse un numéro inconnu) ; `calc/tools/plan_canvas.py` (2389 l. : `SELECTION_LISTS` :72, `_left_click` :1760 qui appelle `propose_label` en garde, puis `add_element` :1652 une seconde fois ; `press_select` :1842 ; `mouseMoveEvent` :1914 ; `update_helpers` :2192 et l'anneau de sélection :2204 ; `_add_handle` :2324) ; `calc/tools/drawing_tab.py` (`VIEW_KIND` :67 : la vue Import montre le document, pas le dessin ; historique = copie de la source seule :1821) ; `calc/tools/fire_tab.py` / `fire_canvas.py` (ont leurs propres `choose_tool`, `refresh_selection`, `update_helpers` : pas d'effet de bord) ; `calc/tools/positions_tab.py` (carte Dimension figée sur b/h/d/t :480-502 ; `references` :305, fonction de domaine logée dans un module Qt ; `delete` :1009 sans cascade) ; `calc/tools/sheet_editor.py:1614`, `plan_command_builder.py:154-372`, `build_reference.call_show_plan` :584 ; `calc/tools/woodcore_gui.py` (`WRITERS` :2871, garde par nom de méthode ; réglages dans `settings.json` :3030, :3437).

### Ce qui porte un numéro de position (revue A)

`positions.json` (`position`) ; `plans/*.json` (`elements[].label`, hors charges PL/LL dont les `L101` ont la forme d'une position L) ; `details/*.json`, schémas (`elements[].position`, partage voulu par la v0.73 : une pièce coupée garde son numéro) ; `checks/*.json` (`position`) ; `Plans/*.typ` (`sheet-viewport(highlight:)`) ; documents `.typ` (`#member("S101")`, `calc-block(positions:)`, `show-plan(highlight:)`, `position:`, la prose, les `<label>`/`@ref`) ; `journal.json` et les scripts (texte libre). Jamais : `_woodcore/` (le moteur copié cite `"T001"` dans ses exemples), archives, `Template/`. Le projet d'exemple n'a aucun `.typ` qui cite une position ; il a `S355`/`S235` (nuances d'acier) dans `2_Projektbasis/Sections/structural-steel.typ`.

### Existant à réutiliser

- `positions_store.propose_id` tel quel pour REQ-003 (après une cascade il n'y a plus de trou : max+1 donne S101, S102…) ; `create_blank_position` et `add_missing_positions` (`plan_tab.py:1593`, `:1695`) : créer au dessin automatise un chemin qui existe (v0.114).
- `sharing._commit` à rendre public (tout-ou-rien, contrôle « changé entre-temps ») au lieu d'un sixième écrivain atomique ; `project.archives_dir` pour la sauvegarde avant écriture.
- `typst_paths.read_text`/`write_text` et `_Lexer` ; `typst_objects.parse_call` pour réécrire `highlight:` et `positions:`.
- Cotes : la géométrie de `statics.py`/`schema.py` (sortes `horizontal|vertical|parallel|angle`), leurs outils à trois clics, leur dessin SVG Tiny, le nom et le mécanisme `dimensions: true` + marqueur `<!-- dims -->` de `show-static-model`.
- Le motif « une collection de la source, un outil à deux ou trois clics, une cible d'accrochage, un pas d'Annuler » de `storey_lines` / `load_levels`.
- `canvas.subtypes` + `subtype_combo` : l'amorce de « défauts d'outil » (REQ-015) ; le fire tab a déjà `zone_kind`, `wall_class`, `door_kind`.
- Le patron de glisser des sommets (`begin_change` au premier mouvement, `end_change` au relâchement = un pas d'Annuler) pour la rotation ; `plan.normalize_angle`, `plan.constrain`.
- Le geste de `calibrate` (deux clics accrochés), `PlanCanvas.per_m()`, `plan_tracking.distance_text` pour la règle.
- `position-list-ids(scope:)` : le vocabulaire de périmètre du résumé ; `sheet-position-list` comme modèle de commande de feuille.

### Risques

- **ARCH-RISK-001 — bloquant (A)** — Les références à la position supprimée (vérifications, éléments de schéma, `#member("S110")`) seraient redirigées en silence vers l'ancienne S111. → Les lister avant la cascade et laisser l'ingénieur trancher (Q-006).
- **ARCH-RISK-002 — bloquant (A, C)** — Un geste annulable (supprimer un objet, dessiner) déclencherait une écriture multi-fichiers que « Annuler » ne défait pas ; `propose_label` est appelé deux fois par objet et écrirait deux lignes ; Échap après le premier clic laisserait une position orpheline. → Le dessin propose le numéro sans écrire ; l'écriture a lieu une fois (Q-007).
- **ARCH-RISK-003 — bloquant (B, C)** — Une troisième copie de la géométrie et du dessin des cotes à côté de `statics.py` et `schema.py`. → Un noyau `calc/domains/dimension.py` (Q-010).
- **ARCH-RISK-004 — bloquant (B)** — « Rayon / diamètre » ne mesure rien dans un plan : ni cercle ni arc dans `TYPES`. → Définir ce qui est mesuré (Q-011).
- **ARCH-RISK-005 — bloquant (B, C)** — La vue Import ne montre pas le dessin du plan : une case « Cotes » n'y aurait rien à éteindre (Q-012).
- **ARCH-RISK-006 — bloquant (B)** — La « présentation de l'onglet *Positions* » n'existe pas (#14 n'est pas fait) : elle est inventée ici (Q-014) ; le critère de REQ-012 cite `plan.length_m`, qui n'est pas une fonction.
- **ARCH-RISK-007 — important (B)** — La formule de volume est fausse pour `pla` et `clt` : il n'y a qu'une épaisseur ; volume = aire du polygone × t sur une dalle, inconnu sur un mur (pas de hauteur). Ne pas utiliser `section.sides()` (d × d pour un cercle) ; ajouter `section.area_mm2`.
- **ARCH-RISK-008 — important (B)** — Les longueurs sont **déjà** dans le PDF (dans le SVG dès que `show_lengths` le dit) ; une option par feuille demande un marqueur `<!-- lengths -->`, qui change le hash `FROZEN` de `tests/test_plan_style.py` (pas `FROZEN_EXAMPLE`) (Q-016).
- **ARCH-RISK-009 — important (A)** — Remplacement dans les `.typ` : bornes `(?<![\w#])…(?![\w]|\.\w)` (S11 ≠ S110, `rgb("#D101")`, `Images/S101.png`) ; une table `M` injective appliquée en **un seul** `re.sub` (S111→S110 ne retouche pas un S110 d'origine, pas de phase temporaire) ; faux positifs `S355` si la position S355 existe → la confirmation liste chaque occurrence (Q-008).
- **ARCH-RISK-010 — important (A)** — Atomicité sur Windows et NextCloud : `os.replace` est atomique par fichier seulement. → Sauvegarde des octets dans `archives_dir/<date>-renumerotation/`, fichier d'intention, `positions.json` écrit en dernier, onglets rechargés et piles d'annulation vidées après la cascade.
- **ARCH-RISK-011 — important (A)** — JSON réécrits **textuellement** (jetons de chaîne repérés par le parseur, autres octets identiques) ; ne pas copier `schema_tab.rename_references`, qui réserialise. La même fonction sert au renommage (`renamed_from`) : une seule mécanique `{ancien: nouveau}`.
- **ARCH-RISK-012 — important (A, C)** — Le champ *Section* écrit `positions.json` depuis le volet du plan, hors « Enregistrer » et « Annuler » ; il faut copier aussi `units` ; une seule porte d'écriture ajoutée à `WRITERS` (Q-009).
- **ARCH-RISK-013 — important (A, C)** — `DIMENSION_FIELDS` ne peut pas porter les formes alternatives (T : h ou h×b×t ; L : a×t ou a×b×t, le 2e nombre change de sens). → Une seule table de **formes** par code dans `section.py`, dont `STEEL_NUMBERS` et `STEEL_FORMS` sont dérivés ; un sélecteur de forme ; clés neutres tant que SZS C5 pp. 30-88 n'est pas relu (CON-002). Le widget de dimension est extrait de `positions_tab.py` en `calc/tools/section_fields.py`, partagé, en gardant « une valeur non touchée n'est jamais réécrite ».
- **ARCH-RISK-014 — important (C)** — `element_properties` et ses setters exigent un élément sélectionné. → Un objet `ToolDefaults` par outil (généralise `subtypes`), le volet construit sur une « cible » (élément ou défauts) ; `plan.apply_defaults` (Qt-free) ne recopie que les champs valides pour le type et le nombre de points (un M à deux points refuse `angle`) ; préséance outil / sélection (D-014, Q-017).
- **ARCH-RISK-015 — important (C)** — Rotation : la poignée est testée avant `nearest_vertex`, son rayon est en pixels d'écran (`zoom_at` doit appeler `update_helpers`), une seule normalisation d'angle (`plan.normalize_angle` ]-180,180] contre `set_angle` [-180,180[), `begin_change` seulement si l'angle change, le champ d'angle suit pendant le glisser.
- **ARCH-RISK-016 — important (B)** — Principe 16 : plan de position et plan d'incendie partagent `DrawingTab` / `PlanCanvas` ; ce qui ne vaut que pour l'un doit dire pourquoi (Q-013).
- **ARCH-RISK-017 — important (A)** — Décisions réglées contredites par D-007 : `docs/decisions.md` (v0.45 « un plan ne dessine que les positions de la feuille », v0.44 numéros partagés, `propose_id`), `docs/domain/positions.md`, `docs/domain/position-plans.md:22`, `docs/ui/window.md` ; tests qui figent l'ancien comportement : `test_plan_tab_rework.py::test_a_tool_with_no_position_creates_a_blank_one_and_draws_with_it`, `test_positions_tab.py::test_a_position_is_added_changed_renamed_and_deleted_and_each_write_is_imported`, `test_plan_tracking.py` (signature de `propose_label`). Le partage des **schémas** (v0.73) reste : D-007 vaut pour les objets d'un plan.
- **ARCH-RISK-018 — mineur** — `plan_tab.py` et `plan_canvas.py` sont trop longs : le nouveau code va dans `calc/tools/plan_properties.py` (volet sur une cible) et `calc/tools/plan_canvas_tools.py` (règle, cotes, rotation) ; une seule fonction de longueur `plan.distance_m` remplace les quatre calculs d'aujourd'hui ; aucune couleur nouvelle en dur ; `dimensions` (cotes) ≠ `dimension` (section) : le dire dans la doc ; nouveaux boutons de même hauteur (`test_toolbar.py`) ; code mort à retirer (`auto_label`, `tool_labels`, l'alerte v0.47, le refus de `save`).

### Approche recommandée

1. REQ-001 seul et d'abord : `plan-scale-bar` enveloppe son corps dans `context` ; tests sur les deux viewports.
2. Domaine Qt-free : `plan.distance_m`, `plan.apply_defaults`, `plan.is_rotatable`, `plan.set_element_angle`, `dimension.py`, les formes de `section.py` + `area_mm2`, `quantities.py` (fonction pure), `calc/renumbering.py` (aperçu sans écriture, puis application par un `_commit` public).
3. Données : collection `dimensions` dans `plan-source` (pas un type de `TYPES`), marqueur conditionnel, ligne `("plan","dimensions")` de `figure_style`, champ additif de `plans.json` (export 1.3), `data/quantities.json` (schéma 1.0) lu par `lib/positions.typ`.
4. Fenêtre : `ToolDefaults`, volet sur une cible, poignée ronde, règle éphémère, outils de cote, widget de section partagé, porte d'écriture des positions dans `WRITERS`.
5. Typst : `dimensions:` aux cinq surfaces (`plan-figure`, `show-plan`, `doc-plan`, `sheet-viewport`, builders) ; commandes du résumé ; `///`, deux exemples, `commands.json`.

### Verdicts

- (A) numérotation : **REVOIR** — RISK-001, 002, 009 sont des choix de l'ingénieur.
- (B) dessin, export, Typst : **APPROUVER AVEC RÉSERVES** pour REQ-001, REQ-009 et la collection `dimensions` ; **REVOIR** sur RISK-003 à 008.
- (C) fenêtre : **APPROUVER AVEC RÉSERVES** — RISK-002 et 003 bloquants ; préséance du volet, Import, raccourci et pas de rotation à trancher.

→ Retour à l'ingénieur avant le plan : Q-006 à Q-016 répondues le 2026-10-08 ; D-014 à D-016 soumis à l'approbation. Chaque risque est traité par une étape du §14 (RISK-001 → étape 6 et REQ-016 ; RISK-002/003 → étape 8 ; RISK-003 cotes → étape 13 ; RISK-004 → D-006 ; RISK-005 → REQ-011 ; RISK-006 → Q-014 ; RISK-007 → REQ-013 ; RISK-008 → étape 16 ; RISK-009 → étape 6 ; RISK-010 → étapes 5-6 ; RISK-011 → étape 6 ; RISK-012 → étapes 8-9 ; RISK-013 → étape 3 ; RISK-014 → étape 10 ; RISK-015 → étape 11 ; RISK-016 → D-012 ; RISK-017 → étapes 8, 18 ; RISK-018 → étapes 2, 10-14).

## 14. Plan d'implémentation

Quatre lots, livrés dans cet ordre ; chaque étape se termine par ses tests verts et une ligne au §16. Les fichiers marqués ⚑ sont modifiés par un pair (CON-004) : message avant d'y toucher, édition ciblée.

**Lot 1 — correctif et fondations (Qt-free)**

1. **Barre d'échelle** (REQ-001). `lib/calc-engine.typ` ⚑ : `plan-scale-bar` enveloppe son corps dans `context`. Tests : `tests/test_sheets.py` (compiler `sheet-viewport` et `sheet-fire-viewport` avec `scale-bar: true` ; boîte inchangée), `tests/test_fire_print.py` (`show-fire-plan(scale-bar: true)`). Reproduire d'abord l'échec dans la vue Affichage ou établir qu'il n'y existe pas.
2. **Une mesure de longueur** (REQ-012, ARCH-002, RISK-018). `calc/domains/plan.py` : `distance_m(source, a, b)` et `element_length_m(source, element)` ; `quantities`, `build_record`, `plan_svg._length` / `_side_lengths` les appellent. Tests : nouveau `tests/test_plan_metres.py` (parité record / SVG / métrés), `tests/test_plan_style.py` (`FROZEN` et `FROZEN_EXAMPLE` inchangés).
3. **Formes de section** (REQ-008, CON-001, CON-002, RISK-013). Relire SZS C5 pp. 30-88 (`ExternalFiles/000-Normes/`) pour les noms des champs. `calc/domains/section.py` : table `FORMS` (une source), `STEEL_NUMBERS` / `STEEL_FORMS` dérivés, `dimension_forms`, `split_dimension → (forme, valeurs)`, `join_dimension(…, forme)`, couches `clt`, `area_mm2`. Tests : `tests/test_section.py`.
4. **Fonctions d'objet** (REQ-002, REQ-007, REQ-015, RISK-004). `plan.py` : `is_rotatable`, `set_element_angle`, `snap_angle` (15°), `apply_defaults` ; `positions_store.py` : `last_section_of_type`, `propose_id` sur positions + numéros non enregistrés. Tests : `tests/test_plan_metres.py` ou nouveau `tests/test_plan_objects.py`, `tests/test_positions_store.py`.

**Lot 2 — numérotation, renumérotation, section dans le plan**

5. **Écriture tout-ou-rien publique** (ARCH-001, RISK-012). `calc/sharing.py` : `_put` / `_commit` exposés (`commit`), sans changer leur comportement. Tests : `tests/test_sharing.py` inchangé.
6. **Renumérotation** (REQ-004, REQ-005, REQ-016, ARCH-001). Nouveau `calc/renumbering.py` : `preview(here, deleted_ids, keep_values=False)` → table, citations, occurrences ; `apply(preview, unchecked)` → sauvegarde dans les archives, fichier d'intention, `commit`. `plan.renumber_labels` (hors charges), réécriture textuelle des JSON (`checks`, `details`, `plans`, `positions.json` en dernier), `re.sub` à un passage sur les `.typ` (périmètre par `project.py`). « Copier les valeurs » : `positions-archive.json` (`schemas/positions-archive.schema.json` 1.0, `-old`, `-old2`). Le renommage d'une position passe par la même fonction. Tests : nouveau `tests/test_renumbering.py` (liste de la revue A : cascade, injectivité, citations refusées, charges, mot entier, `S355`, octets CRLF / LF, JSON textuels, échec simulé, fichier changé, restauration, pas de Qt, `_woodcore/` jamais lu).
7. **L'ancienne position dans le rapport** (REQ-016). `lib/positions.typ` (et le lecteur de position de `lib/timber.typ` / `#member`) : repli sur `positions-archive` exporté, message orange dans la langue du document (`calc/i18n/strings.json`) ; `export_all.py` exporte l'archive. Tests : compilation d'un document qui appelle `S110-old`.
8. **Flux du plan** (REQ-003, REQ-004, REQ-006, REQ-007, D-009, D-011, RISK-002/003). `plan_tab.py` / `plan_canvas.py` : le numéro est proposé une fois, sans écrire ; « Enregistrer » crée les positions et leur section en une opération, puis ouvre l'aperçu de suppression des positions sans objet (dialogue : occurrences à cocher, refus si citée, « Copier les valeurs ») ; vidage des piles d'annulation, relecture des onglets (`MainWindow.reexport` + signal) ; `positions_tab.py` supprime par le même chemin ; code mort retiré (`auto_label`, `tool_labels`, alerte v0.47, refus de `save`) ; `WRITERS` ⚑ complété. Tests : `tests/test_plan_tab_rework.py` (réécriture du test de position vierge, `test_every_writer…`), `tests/test_positions_tab.py`, `tests/test_plan_tracking.py` inchangé.
9. **Widget de section partagé** (REQ-008, UI-002). Nouveau `calc/tools/section_fields.py` (type, forme, champs, copie depuis une position) ; `positions_tab.py` le prend ; ses mots en `STRINGS` fusionnés ⚑ `woodcore_gui.py`. Tests : `tests/test_positions_tab.py` (« non touché, jamais réécrit »).

**Lot 3 — volet, rotation, règle, cotes**

10. **Volet sur une cible et défauts d'outil** (REQ-015, ARCH-006, D-014). Nouveau `calc/tools/plan_properties.py` (déplace `element_properties` et ses setters) ; `ToolDefaults` dans le canevas (généralise `subtypes`) ; `choose_tool` rafraîchit le volet ; *Section* au-dessus de la position. Tests : nouveau `tests/test_plan_tool_defaults.py`.
11. **Rotation** (REQ-002). Nouveau `calc/tools/plan_canvas_tools.py` : poignée ronde (`ItemIgnoresTransformations`), glisser `rotate`, Maj 15°, `zoom_at` → `update_helpers`. Tests : nouveau `tests/test_plan_rotation.py`, `tests/test_plan_tabs_v0117.py`.
12. **Règle** (REQ-009, D-012). `plan_canvas_tools.py` : état éphémère hors source ; outil ajouté au plan d'incendie (`fire_canvas.py` délégation). Tests : règle sur les deux plans, source identique, historique vide.
13. **Noyau des cotes** (ARCH-004, UI-004). Nouveau `calc/domains/dimension.py` (géométrie + SVG) ; `statics.py` ⚑, `schema.py`, `statics_svg.py`, `schema_svg.py` rebranchés ; sortes et unités définies une fois (`validation.py`) ; icônes de cote d'une seule source pour `statics_canvas.py`, `schema_canvas.py` et le plan. Tests : `tests/test_statics.py`, `tests/test_schema.py` (empreintes inchangées), `tests/test_constants.py`, `tests/test_toolbar.py`.
14. **Cotes du plan** (REQ-010, ARCH-003, D-016). `plan.py` : collection `dimensions`, `plan-source` 1.5, `check_source` ; `figure_style.py` ; `plan_svg.py` : marqueur conditionnel ; `build_record` : champ additif ; `schemas/plan-source.schema.json`, `schemas/plans.schema.json` ; avertissement sans échelle ; outils de cote (`plan_canvas_tools.py`, accrochage, un pas d'« Annuler »). Tests : `tests/test_plan_style.py`, `tests/test_figure_style.py`, `tests/test_export.py`, `tests/test_plan_canvas_rework.py`.
15. **Cotes par vue** (REQ-011). Dessin : réglage dans `settings.json`, appliqué par `drawn_source()` ; Affichage / Export : `dimensions:` dans `plan-figure`, `show-plan`, `doc-plan`, `sheet-viewport`, `typst_objects.py`, `plan_command_builder.py`, `sheet_editor.py`, `build_reference.call_show_plan`, `calc/i18n/commands.json`. Tests : `tests/test_typst_objects.py`, `tests/test_call_command.py`, `tests/test_plan_command_builder.py`, `tests/test_sheet_editor.py`, `tests/test_views.py` ⚑.

**Lot 4 — longueurs et métrés en sortie**

16. **`lengths:`** (REQ-012). Marqueur `<!-- lengths -->` écrit seulement si une longueur est dessinée ; `show-plan`, `sheet-viewport` et les mêmes surfaces qu'à l'étape 15 ; hash `FROZEN` repris une fois avec la raison. Tests : idem étape 15 + `tests/test_plan_style.py`.
17. **Métrés** (REQ-013, REQ-014, ARCH-002, ARCH-005). Nouveau `calc/domains/quantities.py` ; `export_all.py` écrit `data/quantities.json` (`schemas/quantities.schema.json` 1.0) ; `lib/positions.typ` : `load-quantities`, `show-plan-quantities` ; `lib/sheet.typ` : `sheet-quantities` ; `typst_objects.py`, carte de `sheet_editor.py`, `build_reference.py` ; mots dans `calc/i18n/strings.json` ; `///`, deux exemples, `commands.json`. Tests : nouveau `tests/test_quantities.py` (trois périmètres, volumes, présentation, parité Python / Typst), `tests/test_commands.py`, `tests/test_export.py` (reproductible).

**Fin**

18. **Documentation** : les fichiers du §11 ; nouvelle décision dans `docs/decisions.md` (D-007, D-009, D-010, D-013, forme des cotes, noyau commun) ; `docs/open-questions.md` (aires d'acier, cotes du plan d'incendie) ; `CHANGELOG.md` ; « Nouveautés » de la prochaine version en fr / de / en.
19. **Suite complète** : `python tests/run_tests.py`, sortie non tamponnée dans un fichier, noms des échecs relevés ; puis vérification indépendante (étape 6 de big-feature).

## 15. Vérification

Vérificateur indépendant (`requirements-verifier`), deux tours le 2026-10-08, sur l'arbre de travail contre `b462466`. Premier tour : 0 ❌, 14 ⚠️ ; corrigés entre les deux tours : le mot allemand de la règle (« Lineal »), les énoncés périmés de `docs/domain/position-plans.md` et `docs/ui/window.md`, les défauts d'outil gardés au changement de langue (`plan_tab.drawing_view_state`), la forme HD h × b × m (SZS C5 p. 51 du PDF), et les tests manquants (`test_plan_tab_rework` : numérotation S501…S601 / T591 et copie de section sans lien ; rotation = un pas d'« Annuler », champ d'angle suivi ; défauts après changement de langue — `test_renumbering` : schémas `details/*.json` et plan ancien à numéro partagé — `test_plan_rotation_ruler` : règle du plan d'incendie sans écriture ni historique, Échap).

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `lib/calc-engine.typ` `plan-scale-bar` dans `context` ; `test_sheets.test_a_plan_on_a_sheet_carries_its_scale_bar_when_asked`, `test_fire_print.test_a_fire_plan_on_a_sheet_carries_its_scale_bar_when_asked` |
| REQ-002 | ⚠️ | cercle, un pas d'« Annuler », champ d'angle suivi : `test_plan_rotation_ruler`, `test_plan_tab_rework.test_a_column_turned_by_its_circle_is_one_step_of_annuler_and_its_field_follows` ; Maj 15° prouvé par `angle_at` seulement, pas par un glisser réel |
| REQ-003 | ⚠️ | `test_plan_tab_rework.test_numbers_follow_one_another_by_letter_and_storey_…` (S501, S502, S503, T591, S601) et `test_a_new_element_is_numbered_on_…` (rien d'écrit avant « Enregistrer », pas de trou) ; « un seul appel par objet » non compté |
| REQ-004 | ✅ | `calc/renumbering.py` ; `test_renumbering` (15), dont `test_a_schema_s_elements_and_a_plan_drawn_before_with_a_shared_number_follow_the_cascade` ; fenêtre : `test_an_element_taken_off_offers_its_position_s_deletion_…` |
| REQ-005 | ✅ | `test_renumbering.test_an_id_is_replaced_whole_…`, `test_an_occurrence_unticked_…`, `test_the_engine_s_copy_…` |
| REQ-006 | ✅ | `plan_properties.section_rows` ; copie, indépendance, « Annuler », écriture : `test_numbers_follow_one_another_…_section_is_copied_without_a_link` |
| REQ-007 | ✅ | `positions_store.last_section_of_type` ; `test_a_new_element_is_numbered_on_…`, `test_positions_store` |
| REQ-008 | ✅ | `section.FORMS` (HD h, h×m, h×b×m), `section_fields.py` ; `test_section`, `test_section_fields`, `test_positions_tab` |
| REQ-009 | ✅ | `plan_canvas_tools.ruler_*` ; `test_plan_rotation_ruler` (les deux plans : rien écrit, aucun pas, Échap) |
| REQ-010 | ✅ | `plan.check_dimensions`, `dimension_parts`, `plan_svg._dimensions` ; `test_plan_dimensions` (5), `test_plan_dimension_tools` (4) |
| REQ-011 | ✅ | `dimensions:` dans `plan-figure`, `show-plan`, `doc-plan`, `sheet-viewport`, faux dans `calc-block` ; réglage Dessin ; `test_sheets.test_a_plan_on_a_sheet_shows_its_dimensions_and_lengths_unless_told_not_to` |
| REQ-012 | ✅ | `plan.distance_m`, `element_length_m`, `metres_text` ; `test_plan_metres` ; `lengths:` booléen (écart voulu, §16) ; `FROZEN` repris une fois, `FROZEN_EXAMPLE` inchangé |
| REQ-013 | ✅ | `calc/domains/quantities.py` ; `test_quantities` (5) |
| REQ-014 | ✅ | `show-plan-quantities`, `sheet-quantities` ; parité Python / Typst en trois langues ; exemples compilés (`test_commands`) |
| REQ-015 | ⚠️ | `tool_rows`, `apply_defaults` ; `test_a_drawing_tool_shows_its_elements_options_at_once_…`, `test_a_tool_s_defaults_survive_a_language_switch` ; « mêmes champs que la sélection » non comparé outil par outil |
| REQ-016 | ✅ | `renumbering.preview(keep_values=True)`, `positions-archive.json` ; `test_a_position_still_cited_is_refused_…`, `test_an_old_position_is_exported_apart_…_in_orange` |
| UI-001 | ✅ | `test_i18n` ; « Lineal » pour la règle allemande (`plan_tab.py`, page Nouveautés de) |
| UI-002 | ✅ | ordre Section / Numéro et contenu de la liste de copie testés (`test_plan_tab_rework`) |
| UI-003 | ✅ | `test_quantities` compile en fr / de / en, booktabs |
| UI-004 | ✅ | `dimension_icons.py` ; `test_a_dimension_tool_shows_the_same_symbol_in_the_three_tabs` |
| ARCH-001 | ⚠️ | Qt-free, textuel, tout-ou-rien, restaurable, renommage par `rename_preview` ; la règle « hors charges » vit dans `renumbering.json_stores` et non dans un `plan.renumber_labels`, le périmètre des `.typ` dans `renumbering.typst_files` |
| ARCH-002 | ✅ | `quantities.py` pur, parité testée |
| ARCH-003 | ✅ | `plan-source` 1.5, `plans` additif ; 1.4 relue (`test_plan_metres`) |
| ARCH-004 | ⚠️ | géométrie partagée (`calc/domains/dimension.py`, lue par statique, schémas, plan ; `test_statics`, `test_schema*` verts) ; le dessin SVG reste propre à chaque domaine, et `validation.py` / `statics.DIMENSION_UNITS` gardent leurs constantes, tenues égales par `test_constants` |
| ARCH-005 | ⚠️ | `quantities.json` validé avant écriture, `test_quantities` ; reproductibilité non prouvée : `test_export.test_the_export_is_reproducible` SKIP sans projet de l'ingénieur |
| ARCH-006 | ⚠️ | `plan_properties.py`, `plan_canvas_tools.py`, `section_fields.py`, `renumber_dialog.py` nouveaux ; `plan_canvas.py` +49 ; `plan_tab.py` +189, dont ~89 de chaînes fr / de / en, au-delà de la centaine visée |
| Documentation | ⚠️ | docs, `CHANGELOG.md`, Nouveautés fr / de / en, `///` + exemples + `commands.json` présents ; énoncés périmés corrigés ; aucun exemple existant de `show-plan` / `sheet-viewport` ne montre `dimensions:` / `lengths:` |
| Tests | ⚠️ | tous les fichiers du §14 verts ; suite complète : seuls des échecs d'autres sessions (`test_commands.test_a_translation_keeps_the_code_it_quotes`, traduction `var-domain` de la session « Formule » ; `test_engine_check` ×2, clé RFEM retirée, corrigé par cette session) |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-08 | draft | spécification extraite de l'issue GitHub #9 (corps et deux commentaires) ; cause du bug de la barre d'échelle établie ; 5 questions à poser |
| 2026-10-08 | specified | Q-001 à Q-005 répondues (vues, règle éphémère, quatre sortes de cotes, dessin = position, bois seul pour les volumes) ; D-005 à D-008 ; revue d'architecture à lancer |
| 2026-10-08 | specified | revue d'architecture faite (3 revues) : REVOIR sur la numérotation et les cotes / métrés ; REQ-001 corrigé (les deux viewports) ; questions Q-006 à Q-017 à poser avant le plan |
| 2026-10-08 | reviewed | Q-006 à Q-016 répondues (refus si citée + « Copier les valeurs » → `-old` ; écriture à l'enregistrement ; tous les `.typ` avec liste à cocher ; noyau de cotes commun et mêmes icônes ; rayon / diamètre abandonnés ; 3 vues ; règle aussi sur le plan d'incendie ; résumé par matériau et section ; deux commandes à périmètre ; `lengths:`) ; REQ-016, UI-004, ARCH-004 à 006, CON-007 ajoutés ; plan d'implémentation en 4 lots, 19 étapes ; approbation à demander |
| 2026-10-08 | approved | approuvée par l'ingénieur telle quelle, avec D-014, D-015, D-016 ; implémentation lot 1 |
| 2026-10-08 | implementation | base `b462466`. Étape 1 faite (REQ-001) : `plan-scale-bar` porte son `context` (`lib/calc-engine.typ`) ; tests `test_sheets.test_a_plan_on_a_sheet_carries_its_scale_bar_when_asked` et `test_fire_print.test_a_fire_plan_on_a_sheet_carries_its_scale_bar_when_asked` (rouges avant avec l'erreur de l'ingénieur, verts après) ; `test_sheets`, `test_fire_print`, `test_plan_style` : 51 verts |
| 2026-10-08 | implementation | Étape 2 faite (REQ-012, part « une mesure ») : `plan.distance_m`, `plan.element_length_m`, `plan.metres_text` ; `quantities`, `build_record`, `plan_svg._length`, `_side_lengths` les lisent ; test `test_plan_metres.test_one_measure_of_a_length_is_read_by_the_drawing_the_export_and_the_quantities` ; `test_plan_style` (FROZEN inchangé), `test_plan_types`, `test_plan_sections` verts |
| 2026-10-08 | implementation | Étape 3 faite (REQ-008 côté domaine, CON-001, CON-002) : SZS C5 2018 relu pp. 47-78 (PDF 51-82) ; `section.FORMS` source unique, `STEEL_NUMBERS`/`STEEL_FORMS` dérivés (ROR et RND en **D** comme la norme, RRK/RRW h·b·t d'abord puis a·t), `dimension_forms`, `form_of`, `is_layered`, `split_dimension`/`join_dimension` pour tous les codes, `area_mm2` ; onglet Positions : garde `box_fields` jusqu'à l'étape 9 ; `test_section` (3 tests nouveaux), `test_positions_tab` (« D×t »), `test_schema_section` verts |
| 2026-10-08 | implementation | Étape 4 faite (REQ-002, REQ-003, REQ-007, REQ-015 côté domaine) : `plan.is_rotatable`, `snap_angle` (15°), `set_element_angle` (une seule normalisation, lue par `check_source` et par l'onglet), `TOOL_DEFAULT_KEYS`, `apply_defaults` ; `positions_store.section_of`, `last_section_of_type` ; `propose_id` sert tel quel (positions + numéros non enregistrés) ; tests `test_plan_metres` (2 nouveaux), `test_positions_store` (2 nouveaux), `test_plan_tab*`, `test_plan_tabs_v0117` verts. **Lot 1 terminé.** |
| 2026-10-08 | implementation | Étape 5 faite : `sharing.commit` et `sharing.put` publics ; `positions_store.encode` (la seule forme d'écriture de positions.json). Étape 6 faite (REQ-004, REQ-005, REQ-016 côté domaine, ARCH-001) : `calc/renumbering.py` — `cascade`, `preview` (aucune écriture), `apply` (sauvegarde + intention + `sharing.commit`, positions.json en dernier), `restore`, `unfinished`, `rename_preview` ; JSON réécrits jeton par jeton ; `.typ` en un passage, bornes `(?<![\w#])…(?![\w]\|\.\w\|-old)` ; `schemas/positions-archive.schema.json` 1.0. Choix d'implémentation : une position encore **dessinée** sur un plan est refusée même avec « Copier les valeurs » (l'objet s'efface d'abord) ; le périmètre des `.typ` est dans `renumbering.typst_files` et non dans `project.py`, que modifie un pair. `tests/test_renumbering.py` : 13 verts |
| 2026-10-08 | implementation | Étape 7 faite (REQ-016 côté rapport) : `export_all` exporte l'archive (`data/positions/<id>-old.json` avec `archived: {was, deleted}`, index `archived` additif, un avertissement par ancienne position) ; schémas `position` et `positions-index` (champs additifs, aucune version ne bouge) ; Typst : `archived-position-ids`, `known-position-ids` (appels acceptés : `#member`, `calc-block`, `moisture-class-of`, `show-check-member`, domaines), `position-archived-note` en orange dans `position-line` et sous `show-check-member(member-level: none)` ; glossaire `position.archived`, `position.archived_on` (fr/de/en) ; test `test_renumbering.test_an_old_position_is_exported_apart_and_the_report_prints_its_values_saying_so_in_orange` (export réel + compilation en 3 langues) vert |
| 2026-10-08 | implementation | Étape 8 faite (REQ-003, REQ-004, REQ-006 plomberie, D-009) : `propose_label` propose sans écrire (positions + numéros du plan) ; `PlanCanvas.new_element` (même pas d'« Annuler ») ; brouillon `PENDING` (`_pending_positions`, retiré avant l'écriture) avec la section du dernier du même type ; `save` écrit plan + positions nouvelles par `sharing.commit`, puis propose la suppression des positions qu'aucun plan ne dessine plus (`orphaned`, `offer_deletion` → `renumber_dialog.ask`, plan relu, historique vidé) ; nouveau `calc/tools/renumber_dialog.py` (aperçu, liste à cocher, « Copier les valeurs », refus si dessinée ou si un autre onglet n'est pas enregistré, notices) ; onglet Positions : supprimer passe par le dialogue, renommer par `renumbering.rename_preview` (citations réécrites) ; code mort retiré (`tool_labels`, `create_blank_position`, `on_refused`, `no_position_text`, 3 chaînes) ; tests `test_plan_tab_rework` (2 nouveaux, l'ancien de v0.114 remplacé), `test_plan_tracking`, `test_positions_tab`, `test_no_message_boxes`, `test_plan_types`, `test_plan_tabs_v0117`, `test_plan_canvas_rework` : 71 verts |
| 2026-10-08 | implementation | Étape 9 faite (REQ-008 côté fenêtre) : `calc/tools/section_fields.py` (`DimensionFields` : formes, sélecteur de forme, couches CLT ±, `fill_types`) ; l'onglet Positions le prend (`dim_fields` tenu à jour en place, 4 libellés `po_dim_*` retirés) ; tests `test_section_fields` (nouveau), `test_positions_tab` (CLT en couches, libellés du widget). Étape 10 faite (REQ-006, REQ-007, REQ-015, UI-002, D-011, D-014) : `calc/tools/plan_properties.py` (`tool_rows`, `section_rows` avec « Reprendre de » par copie, `element_section_rows`) ; `PlanCanvas.tool_defaults` ; le volet suit l'outil de dessin (`drawing_tool`, `refresh_selection` depuis `choose_tool`) ; *Section* au-dessus de la position ; une section choisie pour une position existante écrite à l'enregistrement ; 8 chaînes fr/de/en ; test `test_plan_tab_rework.test_a_drawing_tool_shows_its_elements_options_at_once_and_they_are_the_next_elements` vert |
| 2026-10-08 | implementation | Étapes 11 et 12 faites (REQ-002, REQ-009, D-005, D-012, D-015) : `calc/tools/plan_canvas_tools.py` — cercle de rotation (distance fixe à l'écran, avant la poignée du sommet, un pas d'« Annuler » seulement si l'angle change, Maj 15°, signal `angle_dragged` suivi par le champ d'angle) ; règle éphémère (deux clics accrochés, m ou unités de la feuille, Échap efface, rien d'écrit) sur le plan de positions et le plan d'incendie ; `zoom_at` redessine les poignées ; chaînes `plan_tool_ruler`, `plan_hint_ruler` (fr/de/en). Tests `test_plan_rotation_ruler` (3, nouveau), `test_plan_canvas_rework`, `test_plan_types` (le test de la charge passe à « Sélection » avant de sélectionner : D-014), `test_toolbar`, `test_plan_tabs_v0117` verts ; `test_fire_tab` (50) vert avant l'étape 11, à relancer dans la suite complète |
| 2026-10-08 | implementation | Étape 13 faite (ARCH-004, partie géométrie) : `calc/domains/dimension.py` (direction, ligne, valeur linéaire, croisement, rayons par l'azimut du clic, arc, `show`, `text` ; tolérances passées par chaque domaine) ; `statics.py` et `schema.py` le lisent (sortes `DIMENSION_KINDS = dimension.KINDS`), comportement inchangé : `test_statics` 27, `test_schema*` 167, `test_constants` 23 verts. Le dessin SVG de la statique et des schémas reste le leur (primitives propres à chaque `*_svg`, empreintes figées) : seul le plan dessine avec le nouveau code — écart signalé à la vérification. `validation.py` (modifié par un pair) garde ses constantes, tenues égales par `test_constants` |
| 2026-10-08 | implementation | Étape 14 faite (REQ-010, ARCH-003, UI-004, D-006, D-016) : `plan-source` 1.5, collection `dimensions` (`horizontal`, `vertical`, `parallel`, `chain` + `axis`, `angle`), `plan.check_dimensions`, `dimension_parts` (valeurs calculées, rien sans échelle pour une longueur), `dimension_value_text`, avertissement `plan_dimensions_no_scale`, champ additif `dimensions` du record (export 1.3) ; `figure_style` `(plan, dimensions)` + tableau de docs/architecture/figure-style.md ; `plan_svg._dimensions` entre `<!-- dimensions -->` écrits seulement s'il y en a (FROZEN inchangé) ; `dimension.onto` (projection commune, chaînes) ; schémas `plan-source` et `plans` ; outils de cote sur le canevas (`plan_canvas_tools` : clics, aperçu, Entrée/double-clic pour la chaîne, choix sur la ligne, glisser de la ligne, suppression, Échap) ; boutons, aides, volet (`plan_properties.dimension_rows`), 18 chaînes fr/de/en ; `calc/tools/dimension_icons.py` : mêmes symboles dans la statique, les schémas (`schema_tab.tool_icon`) et le plan, la chaîne a le sien. Tests `test_plan_dimensions` (5), `test_plan_dimension_tools` (3), `test_plan_style`, `test_plan_metres`, `test_figure_style`, `test_plan_sections`, `test_plan_types` (versions 1.5) verts |
| 2026-10-08 | implementation | Étape 15 faite (REQ-011) : `dimensions:` dans `plan-figure`, `show-plan`, `doc-plan`, `sheet-viewport` (marqueur `<!-- dimensions -->` retiré), faux dans les détails de `calc-block` ; `build_reference.call_show_plan`, `plan_command_builder` (cases « Cotes », « Longueurs des éléments »), `typst_objects` (signatures, `set_dimensions`/`set_lengths` des modèles `doc-plan` et `sheet-viewport`), `sheet_editor` (cases de la feuille), `object_panes` (volet de `doc-plan`) ; vue Dessin : case « Cotes » dans le module de l'échelle, réglage de l'ingénieur (`usersettings`, clé `plan_draw_dimensions`), `PlanCanvas.show_dimensions` + `drawn_source` (montrées pendant qu'on cote) ; vue Import : sans cotes (Q-012). `commands.json` : 12 traductions. Tests `test_typst_objects` 56, `test_call_command`, `test_plan_command_builder` 13, `test_sheet_editor` 23, `test_object_panes` 56, `test_plan_dimension_tools` (vue Dessin), `test_sheets.test_a_plan_on_a_sheet_shows_its_dimensions_and_lengths_unless_told_not_to` verts. |
| 2026-10-08 | implementation | Étape 16 faite (REQ-012) : longueurs dessinées après les numéros entre `<!-- lengths -->` (écrits seulement s'il y en a) ; `lengths:` est un **booléen** comme `axes:` (vrai : ce que le plan dessine ; faux : rien) — écart avec « `lengths: auto` » de REQ-012/D-015, Typst ne pouvant dessiner ce que le plan n'a pas dessiné ; empreinte `FROZEN` reprise une fois, preuve dans le test : le dessin de `b462466` donnait l'ancienne, les lignes sont les mêmes plus les deux marqueurs. |
| 2026-10-08 | implementation | Étape 17 faite (REQ-013, REQ-014, ARCH-002, ARCH-005, Q-014, Q-015) : `calc/domains/quantities.py` (`rows`, `summary`, `document`, volumes du bois seul) ; `schemas/quantities.schema.json` 1.0 ; `export_all` écrit `data/quantities.json` (et le sème vide pour un projet neuf), ses notes rejoignent les avertissements ; Typst : `lib/positions.typ` `load-quantities`, `quantity-sum` (somme d'un périmètre `positions`), `quantity-table` (booktabs, total par matériau, décimales fixes), `show-plan-quantities` ; `lib/sheet.typ` `sheet-quantities` ; `lib/formula.typ` les réexporte (accord du pair) ; `structure.OBJECT_TYPES`, `typst_objects.QuantitiesModel`, `sheets.add_quantities`, `sheet_editor` (bouton « Ajouter les métrés », volet largeur/titre) ; glossaire `quantities.*` (8 clés, 3 langues) ; catégories de `build_reference`, traductions de `commands.json`. Tests `test_quantities` (5, dont la parité Python/Typst en 3 langues et la feuille), traductions vertes. Reste : `build_examples.py` (exemples gelés de `examples/lib/`), à faire avec le pair qui modifie aussi `lib/`. |
| 2026-10-08 | implementation | Étape 18 faite (documentation) : `docs/domain/position-plans.md`, `positions.md`, `fire-plans.md`, `static-models.md`, `detail-schemas.md`, `docs/architecture/figure-style.md`, `docs/ui/window.md` (onglet plan de positions), `docs/typst/api-conventions.md` (2 commandes), `docs/conventions/testing.md` (6 fichiers de tests), `docs/decisions.md` (1 décision : numéros, cascade, cotes, métrés), `docs/open-questions.md` (aires d'acier, volumes des murs et poteaux, cotes du plan d'incendie, cote qui suit un élément, lettre de série HL, reprise d'une renumérotation inachevée), `CHANGELOG.md`, « Nouveautés » 0.117 fr/de/en. Un réexport du projet d'exemple pour `quantities.json` a perdu ses charges (son classeur n'est pas dans le dossier) : les fichiers suivis ont été remis au contenu de `b462466` (`git show`, contenu identique), seul `quantities.json` est nouveau. `build_examples.py --freeze` lancé (accord du pair). |
| 2026-10-08 | implementation | Étape 19 faite (tests) : suite complète 2555 verts, 9 SKIP, 10 rouges, dont 5 listes épinglées mises à jour, 3 verts à la relance, 2 `test_engine_check` venant de la clé RFEM retirée (session « Formule », corrigé par elle) |
| 2026-10-08 | verification | Tour 1 du vérificateur : 0 ❌, 14 ⚠️. Corrigés : « Lineal », docs périmées (`position-plans.md:22`, `window.md:51/66/81`), défauts d'outil gardés au changement de langue, HD h × b × m (SZS C5 p. 51), 6 tests ajoutés ou étendus. Tour 2 : REQ-004, REQ-006, REQ-009, UI-001, UI-002, CON-002 et les docs ✅ ; restent ⚠️ REQ-002 (Maj en glisser réel), REQ-003 (un appel par objet), REQ-015 (champs comparés outil par outil) |
| 2026-10-08 | completed | écarts gardés et dits à l'ingénieur : dessin SVG des cotes non partagé (ARCH-004), `lengths:` booléen, constantes de `validation.py` tenues égales par test, reprise de `renumbering.unfinished` non branchée dans la fenêtre, position dessinée refusée même avec « Copier les valeurs », lettre de série HL non représentable, `plan_tab.py` +189 lignes ; reproductibilité de l'export à prouver sur un projet de l'ingénieur ; spécification déplacée dans `docs/requirements/completed/` |
| 2026-10-09 | completed | `test_panes.test_the_bar_wraps_and_loses_no_tool` rouge dans la suite : un outil de dessin choisi (D-014) montrait la liste des types de section à sa pleine largeur (~750 px), le volet de droite passait à 815 px et écrasait le dessin ; `section_fields.fill_types` et la liste « Reprendre de » ne fixent plus la largeur (comme la liste des échelles) ; test `test_panes.test_a_drawing_tool_s_options_do_not_widen_the_right_pane` |
