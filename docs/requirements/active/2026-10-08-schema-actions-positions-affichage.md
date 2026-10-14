---
id: 2026-10-08-schema-actions-positions-affichage
titre: Surfacique à largeur fixe, deux sections d'Actions, dimensions d'une position et tableau des positions
status: verification
cree: 2026-10-08
mis_a_jour: 2026-10-08
source: message écrit (conversation du 08.10.2026)
docs: [docs/ui/window.md, docs/domain/positions.md, docs/domain/detail-schemas.md, docs/domain/position-plans.md, docs/typst/api-conventions.md, docs/typst/command-docs.md]
---

# Surfacique à largeur fixe, deux sections d'Actions, dimensions d'une position et tableau des positions — Spécification

## 1. Objectif

Quatre demandes de l'ingénieur, qui touchent l'onglet Schéma, le volet de gauche, l'onglet Position et le mode Affichage : (1) dessiner dans le Schéma, avec l'outil « Surfacique », un élément dont une dimension vient d'une position ; (2) préparer dans « Actions » les deux sections d'action permanente et variable avec leurs onglets (vides pour l'instant) ; (3) saisir la dimension d'une position par des champs propres à son type de section, et comprendre puis réduire la lenteur du premier enregistrement ; (4) corriger et compléter le tableau des positions du mode Affichage (aucun plan coché, titre et légende, colonnes choisies et leur largeur, marge de droite, plusieurs pages).

## 2. Source

La demande telle qu'elle a été donnée, **mot pour mot**, découpée en points.

> **T1** — « Dans l'onglet schéma, lorsque je sélectionne l'outil "Surfacique", dans le volet de droite, je dois déjà voir les options pour cet outil. »
>
> **T2** — « Je dois pouvoir indiquer la position, »
>
> **T3** — « et, lorsque cela est fait, je dois pouvoir choisir si je dessine la largeur ou la hauteur de la position. »
>
> **T4** — « Ensuite, je dessine l'élément qui possède dont une largeur fixe »
>
> **T5** — « Dans woodcore, Dans le volet de gauche, dans "Actions", il faut deux sections différentes: (1) Actions permanentes, (2) Actions variables. »
>
> **T6** — « Dans actions permamentes, il y a les onglets disponibles (vides pour l'instant) suivants: Poids propre, Surcharge »
>
> **T7** — « Dans actions variables, il y a les onglets disponibles (vides pour l'instant) suivants: Charge utile, Neige, Vent, Séisme »
>
> **T8** — « Dans l'onglet position, » (l'en-tête du bloc qui suit ; les points T11 à T16 concernent le mode Affichage)
>
> **T9** — « Dans le volet de droite, lorsque le type de section est donné, il doit y avoir une section "Dimension" qui apparait avec des textbox différentes à remplir en fonction du type de section: e.g. "rec" => Dimension: largeur ____ hauteur ____. "plaque" => Dimension: épaisseur ____ »
>
> **T10** — « Lorsque les valeurs d'une position sont remplies (e.g. Matériaux, Classe de résisatnce) et enregistrées pour la première fois, cela prend beaucoup de temps pour enregistrer. Pourquoi ? Est-il possible d'optimiser cela ? »
>
> **T11** — « En mode Affichage: il y a une erreur lorsque Positions listées: Celles des plans cochées et qu'il n'y a aucun plan coché. À la place, il ne doit y avoir aucun affichage. »
>
> **T12** — « Légende du tableau => Renommer "Titre" (volet de droite) »
>
> **T13** — « Ajouter: Légende (volet de droite) »
>
> **T14** — « les colonnes à afficher peuvent être choisies (à cocher ou décocher), il est également possible de fixer une largeur de colonne (valeur fixe ou en % »
>
> **T15** — « le tableau ne doit pas dépasser dans la marge de droite »
>
> **T16** — « le tableau doit pouvoir s'étendre sur plusieurs pages »

## 3. Exigences fonctionnelles

### REQ-001 — Surfacique : la position fournit la dimension fixe
- **Exigence** : avec l'outil « Surfacique », Woodcore doit pouvoir lier l'élément à une position du projet : la dimension de la position qui n'est pas dessinée devient la **dimension fixe** de l'élément. Pour une section « rec » (b/h), l'ingénieur choisit si l'on dessine la **largeur** (la hauteur est alors fixée par la position) ou la **hauteur** (la largeur est fixée) ; pour une section à une seule dimension (« pla », l'épaisseur), l'épaisseur est fixée et l'on dessine l'autre étendue, sans choix.
- **Source** : T2, T3, T4 ; interprétation à confirmer (voir §7, D-002)
- **Priorité** : doit
- **Critère d'acceptation** : test d'un module de domaine (sans Qt) : pour « rec 100/200 » dessinée en largeur, l'élément a la hauteur fixe 200 mm ; dessinée en hauteur, la largeur fixe 100 mm ; pour « pla 40 », l'épaisseur fixe 40 mm.

### REQ-002 — Surfacique : dessiner l'élément à dimension fixe
- **Exigence** : une fois la position et la dimension dessinée choisies, l'élément se dessine en une opération (le côté libre tiré à la souris, l'autre dimension imposée), à l'échelle du schéma, et il garde le lien avec la position (son identifiant) dans les données du schéma.
- **Source** : T4
- **Priorité** : doit
- **Critère d'acceptation** : un élément ainsi dessiné est enregistré avec l'identifiant de la position, ses dimensions en mm, et s'exporte dans `data/schemas.json` ; le test lit le fichier d'export.

### REQ-003 — Dimension d'une position : la valeur reste celle d'aujourd'hui
- **Exigence** : les champs de l'interface (UI-005) composent et lisent la valeur existante `dimension` de la position (par exemple « 100/200 »), validée par `domains/section.py` ; aucun nouveau champ de données, aucun changement de `schema_version` de la position ; une position déjà enregistrée s'ouvre avec ses champs remplis.
- **Source** : T9 ; principe « un fichier existant se relit toujours »
- **Priorité** : doit
- **Critère d'acceptation** : test : une position « rec / 100/200 » enregistrée avant le changement s'ouvre avec largeur 100 et hauteur 200, et un enregistrement fait avec les champs écrit « 100/200 ».

### REQ-004 — Premier enregistrement d'une position : comprendre et réduire le temps
- **Exigence** : Woodcore doit **mesurer** où va le temps du premier enregistrement des valeurs d'une position (Matériau, Classe de résistance…), l'expliquer à l'ingénieur avec les chiffres, corriger ce qui se corrige localement sans perdre l'exactitude des exports, et **proposer** (sans le faire) tout changement d'architecture (D-008).
- **Source** : T10
- **Priorité** : doit
- **Critère d'acceptation** : un profil (temps par étape, avant et après) sur `tests/projet-exemple/` est consigné dans la spec avec la cause établie ; le temps baisse là où une correction locale le permet, et le gain restant avec ses options est présenté à l'ingénieur ; l'export est inchangé octet pour octet (`test_the_export_is_reproducible`).

### REQ-005 — Aucun plan coché : aucun affichage et aucune erreur
- **Exigence** : en mode Affichage, avec « Positions listées : Celles des plans cochés » et aucun plan coché, Woodcore n'imprime **rien** (ni tableau, ni message, ni titre) et ne signale aucune erreur. **Cause établie par la revue** : la fenêtre écrit `#show-position-list(scope: "plans")` (l'option `plans` est omise quand rien n'est coché) et `lib/positions.typ:155-157` refuse cet appel exprès (`panicked with: …`) ; `tests/test_position_list.py:168` fige ce refus. `scope: "storey"` sans position garde son message « Keine Position. » ; `sheet-position-list` est inchangée.
- **Source** : T11
- **Priorité** : doit
- **Critère d'acceptation** : le test `no-plans` de `tests/test_position_list.py` est **renversé** (l'appel compile, sans sortie) ; `tests/test_display_view.py` écrit l'appel que la fenêtre produit sans plan coché et le compile.

### REQ-006 — Colonnes du tableau choisies
- **Exigence** : le tableau des positions imprime seulement les colonnes cochées dans le volet de droite (argument `columns:`) ; l'ordre des colonnes reste celui d'aujourd'hui ; la sélection est retenue tant que la fenêtre est ouverte (D-012) ; le cochage n'est pas un ordre (la liste n'a pas de réordonnancement : `columns:` accepte un ordre, la fenêtre ne le change pas).
- **Source** : T14
- **Priorité** : doit
- **Critère d'acceptation** : test : avec deux colonnes décochées, le tableau compilé n'a pas ces colonnes ; la sélection survit à la reconstruction des onglets après un export.

### REQ-007 — Largeur de colonne
- **Exigence** : pour chaque colonne, l'ingénieur peut fixer une largeur, soit une **valeur fixe** (mm), soit un **pourcentage** de la largeur utile (argument `widths:`, `30mm` ou `20%`) ; sans valeur, la colonne s'adapte à son contenu.
- **Source** : T14
- **Priorité** : doit
- **Critère d'acceptation** : test : une colonne à 30 mm et une à 20 % ont ces largeurs dans le tableau compilé ; une valeur invalide ou une colonne inconnue arrête la compilation en nommant la colonne et les clés valides (D-010).

### REQ-008 — Le tableau reste dans la marge de droite
- **Exigence** (**limite connue, établie à la vérification : le cadre du tableau, c'est-à-dire la somme de ses colonnes, ne dépasse jamais la marge ; un mot que rien ne permet de couper — une adresse, un identifiant de trente caractères, une légende sans espace — plus long que sa colonne en sort encore, car Typst ne coupe pas un mot sans point de césure**) : **défaut existant, mesuré par la revue** (59 positions aux valeurs longues : la colonne « Description » commence à 529 pt, la zone de texte s'arrête vers 524 pt, parce que les colonnes `auto` gardent leur largeur minimale insécable et que la colonne `1fr` ne reçoit plus rien) : la largeur totale du tableau ne dépasse jamais la largeur utile de la page, avec ou sans `widths:` ; `render-table` calcule un budget (valeurs fixes en mm, pourcentages de la zone, un plancher pour la colonne souple) ; le texte des cellules passe à la ligne ; si des largeurs valides dépassent la largeur utile, une note orange visible le dit dans le rapport et les colonnes sans largeur fixée sont réduites (puis, à défaut, toutes proportionnellement) ; un titre de colonne long dans une colonne fixée passe à la ligne au lieu de garder sa largeur de 8 em.
- **Source** : T15
- **Priorité** : doit
- **Critère d'acceptation** : test de mise en page sur un projet de 59 positions aux valeurs longues : le bord droit du texte du PDF compilé est dans la marge, avec et sans largeurs ; la note orange est présente quand le budget est dépassé.

### REQ-009 — Le tableau s'étend sur plusieurs pages
- **Exigence** : un tableau trop long pour une page se poursuit sur la suivante, la ligne d'en-tête étant répétée en haut de chaque page ; une ligne ne se coupe pas entre deux pages (la revue a constaté que l'en-tête se répète déjà, mais que les lignes se coupent : les cellules du corps deviennent insécables pour ce tableau seulement).
- **Source** : T16 ; la répétition de l'en-tête et l'intégrité des lignes sont inférées (usage ordinaire d'un tableau de rapport)
- **Priorité** : doit
- **Critère d'acceptation** : test : avec assez de positions, le PDF compilé a deux pages ou plus pour le tableau, l'en-tête sur chacune.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Schéma : les options de Surfacique sont visibles dès la sélection de l'outil
- **Exigence** : dès que « Surfacique » est choisi, le volet de droite affiche ses options, avant tout tracé : le mode de dessin (aujourd'hui trois modes dans la barre d'outils), la position, la dimension dessinée.
- **Source** : T1
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : choisir l'outil fait apparaître le groupe d'options dans le volet de droite, sans élément sélectionné.

### UI-002 — Surfacique : champ « Position » puis choix « Largeur / Hauteur »
- **Exigence** : le volet de droite offre une liste des positions du projet ; quand une position est choisie, un choix « Dessiner : largeur / hauteur » apparaît (seulement pour une section à deux dimensions, avec la dimension fixe affichée) ; sans position, l'outil dessine comme aujourd'hui.
- **Source** : T2, T3
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : choisir « T001 » (rec 100/200) montre le choix ; choisir une position « pla » ne le montre pas et affiche l'épaisseur fixe ; aucune position : l'outil garde ses trois modes.

### UI-003 — Volet de gauche : deux sections dans « Actions »
- **Exigence** : le groupe « Actions » du volet de gauche contient deux sections visibles, « Actions permanentes » et « Actions variables », puis, **dessous**, « Charges » et « Combinaisons de charges » comme aujourd'hui (D-005).
- **Source** : T5
- **Langues** : fr / de / en (les trois mots dans le glossaire, jamais en dur)
- **Critère d'acceptation** : test hors écran sur `NAV_GROUPS` : les deux sections existent, avec leurs libellés dans les trois langues.

### UI-004 — Onglets de ces sections
- **Exigence** : « Actions permanentes » contient **Poids propre** et **Surcharge** ; « Actions variables » contient **Charge utile**, **Neige**, **Vent**, **Séisme** ; chaque onglet s'ouvre, vide (une phrase dit ce qu'il contiendra, comme les onglets de vérification d'élément qui ne sont pas encore construits).
- **Source** : T6, T7
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : les six onglets s'ouvrent et affichent leur texte dans les trois langues ; aucun calcul n'est branché.

### UI-005 — Position : section « Dimension » selon le type de section
- **Exigence** : dans le volet de droite de l'onglet Position, quand le type de section est choisi, une section « Dimension » affiche les champs de ce type : « rec » → largeur, hauteur ; « pla » → épaisseur ; par analogie « cir » → diamètre ; les types dont la dimension n'est pas un nombre (« clt » : les couches ; les profilés d'acier) gardent leur saisie actuelle (voir D-003).
- **Source** : T9
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : changer le type change les champs ; une valeur invalide est signalée sous son champ, comme le fait la validation actuelle.

### UI-006 — Tableau des positions : « Titre » et « Légende »
- **Exigence** : dans le volet de droite du mode Affichage, l'option « Légende du tableau » est renommée « Titre » (de : « Titel », en : « Title » — à confirmer), et une nouvelle option « Légende » s'ajoute : un texte libre imprimé **sous** le tableau (D-006).
- **Source** : T12, T13
- **Langues** : fr / de / en
- **Critère d'acceptation** : les trois mots sont dans les trois langues ; le titre imprimé est celui d'avant ; la légende saisie est imprimée sous le tableau, et absente quand elle est vide.

### UI-007 — Tableau des positions : choix des colonnes et de leur largeur
- **Exigence** : le volet de droite offre, pour chaque colonne, une case à cocher et un champ de largeur (mm ou %).
- **Source** : T14
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : les neuf colonnes sont listées avec leur case ; le champ de largeur accepte « 30 », « 30mm », « 20% » et refuse le reste avec une explication.

## 5. Exigences d'architecture

### ARCH-001 — Pas de calcul dans l'interface, pas de mot en dur
- **Exigence** : la composition et la lecture d'une dimension (REQ-003) et la dimension fixe d'un élément (REQ-001) vivent dans `calc/domains/` sans Qt ; les mots de l'interface sont dans les glossaires (fr, de, en) ; les largeurs sont des options de la vue, imprimées par Typst sans recalcul.
- **Source** : principes 2 et 3 de `docs/architecture/principles.md`
- **Critère d'acceptation** : les tests de domaine n'importent pas Qt ; le test des glossaires (trois langues) passe.

### ARCH-002 — La surface de commande est celle que l'ingénieur a choisie
- **Exigence** : les nouveaux arguments de `show-position-list` — `columns:`, `widths:`, `legend:`, la forme que l'ingénieur a choisie (D-007) — pour chacun : bloc `///`, deux exemples qui compilent, traduction dans `calc/i18n/commands.json`, ligne dans `build_reference` ; les anciens appels gardent leur sens.
- **Source** : CLAUDE.md (« l'ingénieur dessine la surface de commande ») ; `docs/typst/command-docs.md`
- **Critère d'acceptation** : `tests/test_site.py` (référence du site) et le test de documentation des commandes passent.

### ARCH-003 — Les données d'une vue et d'un schéma restent lisibles
- **Exigence** : aucun contrat de données ne change : les options d'affichage ne sont pas un fichier (D-012), l'élément de schéma porte déjà `position`, `at` en mm, `b`, `h` (`schema_version` 1.1 inchangée, D-011), la dimension d'une position reste la chaîne `dimension` (REQ-003) ; un fichier existant se relit à l'identique et l'export reste reproductible.
- **Source** : principe « modèles de données explicites et versionnés »
- **Critère d'acceptation** : `tests` de schéma et `test_the_export_is_reproducible` passent ; un projet d'exemple d'avant s'ouvre.

### ARCH-004 — Largeur de colonne : une règle écrite est amendée, une seule fois
- **Exigence** : `lib/calc-engine.typ:2061` et `docs/domain/calculation-domains.md:24` disent qu'une colonne « dit ce qu'elle contient et jamais sa largeur ». Seule `position-list-table` pose une clé `width` **optionnelle** sur ses colonnes ; aucune table de données ne la porte ; `render-table` la lit et ne construit pas un second `table(...)` (le style à trois filets, l'en-tête et le saut de page restent à un seul endroit). La décision est écrite dans `docs/decisions.md` et la phrase amendée dans les deux fichiers.
- **Source** : revue (ARCH-RISK-002) ; CON-002
- **Critère d'acceptation** : aucun test de table de données ne change ; `grep` ne trouve plus la règle sans son amendement.

### ARCH-005 — Volet de gauche : un module à part, des tableaux qui n'ont pas changé de forme
- **Exigence** : les six onglets vivent dans un petit module (`calc/tools/action_tabs.py`) avec ses mots (`STRINGS`, préfixe `ac_`, trois langues, fusionnés comme ceux de `member_check_tab`), une classe d'onglet à venir généralisée (pas une troisième classe à côté de `FutureTab` et `SoonTab`) et leurs icônes dans `chrome.ICONS` ; ils s'inscrivent dans `TABS` **à côté** de `tab_loads` (pas entre `tab_polar` et `tab_mc_tension`, que `tests/test_member_check_tab.py:143` épingle) ; `NAV_GROUPS` garde sa forme (D-009). Les raccourcis Ctrl+1 à 9 des onglets suivants se décalent : c'est dit dans les « Nouveautés ».
- **Source** : revue (ARCH-RISK-015, -016)
- **Critère d'acceptation** : `tests/test_chrome.py`, `test_member_check_tab.py`, `test_structure_tab.py`, `test_variables.py`, `test_annex.py`, `test_fire_tab.py`, `test_journal.py`, `test_positions_tab.py` passent sans changer leur manière de lire `NAV_GROUPS` ; un test neuf couvre les deux sous-titres et les six onglets.

### ARCH-006 — Dimension : une valeur que l'ingénieur n'a pas touchée n'est jamais réécrite
- **Exigence** : les fonctions de découpe et d'assemblage d'une dimension par type (les champs d'un type, la découpe de « 100/200 » ou « 100 x 200 » ou « 100,5/200 », l'assemblage) sont dans `calc/domains/section.py`, à côté de `parse`, sans Qt ; l'onglet n'assemble que si un champ a changé, sinon il garde le texte enregistré ; un texte qui ne se lit pas comme son type (descriptif, type vide, `clt`, acier) reste éditable en texte libre dans le champ actuel ; `section_problem` reste le seul juge et lit la chaîne assemblée.
- **Source** : revue (ARCH-RISK-018) ; leçon « réécrire textuellement, ne jamais resérialiser »
- **Critère d'acceptation** : `tests/test_section.py` : aller-retour par type, virgule, texte intact sans modification ; `tests/test_positions_tab.py` : une position ouverte puis enregistrée sans retouche garde son texte octet pour octet.

### ARCH-007 — Une seule liste de colonnes, un seul endroit où l'appel s'écrit
- **Exigence** : la liste des neuf colonnes est un tuple Python unique (dans `display_options.py`) tenu égal par un test à celle de `lib/positions.typ` (même méthode que `test_the_id_colours_are_plan_svgs_own`) ; la valeur par défaut de `columns:` est lue de la signature, pas écrite en Python ; `build_reference.typst_value` gagne le cas du dictionnaire (`widths: (id: 30mm, type: 20%)`) et `call_show_position_list` reçoit `columns`, `widths`, `legend` (pas un second assistant) ; `legend:` est du **contenu** (`[#legend]`, comme `title:`), jamais une chaîne qui passerait par le glossaire.
- **Source** : revue (ARCH-RISK-006, -007, -008) ; principe 1
- **Critère d'acceptation** : `tests/test_position_list.py`, `test_display_view.py`, `test_call_command.py` passent avec les cas neufs.

## 6. Contraintes

- **CON-001** — Plusieurs sessions modifient ce dépôt : aucun `checkout --`/`stash`/`reset`/`clean` ; modifications ciblées. Source : CLAUDE.md.
- **CON-002** — Le tableau est un `render-table` (trois filets, pas de grille, une colonne alignée selon son contenu) : tout changement de mise en page garde ce style. Source : style de tableau de l'ingénieur.
- **CON-003** — Rien n'est commité ni poussé sans demande de l'ingénieur ; la documentation (§ de `docs/`, `CHANGELOG.md`, « Nouveautés » fr/de/en) fait partie du travail. Source : CLAUDE.md.

## 7. Décisions prises

- **D-001** — (inférée de la demande) T11 à T16 portent sur le mode Affichage et le tableau des positions (`show-position-list`) seulement, pas sur les autres tableaux.
- **D-002** — (interprétation, à confirmer à l'approbation) « dessiner la largeur ou la hauteur de la position » : la dimension **dessinée** est libre, l'**autre** est imposée par la position (« largeur fixe »). Pour une section à une dimension, cette dimension est la dimension fixe.
- **D-003** — (extension par analogie, à confirmer) « cir » → un champ diamètre ; « clt » (couches) et les profilés d'acier gardent leur saisie actuelle.
- **D-004** — (inférée) un tableau sur plusieurs pages répète sa ligne d'en-tête.
- **D-005** — Q-001 A : « Charges » et « Combinaisons de charges » restent dans le groupe « Actions », **sous** les deux nouvelles sections ; rien n'est perdu tant que les six nouveaux onglets sont vides.
  - *Note du 2026-10-08 (spec `2026-10-08-onglet-variables-trois-colonnes`, issue 13)* : « Charges » est retiré au profit de « Variables », qui liste chacune de ses valeurs avec sa provenance ; la ligne fine de `NAV_SECTIONS` se place désormais avant « Combinaisons de charges ».
- **D-006** — Q-002 A : « Légende » est un **texte libre** que l'ingénieur écrit, imprimé **sous** le tableau ; « Titre » est l'actuelle « Légende du tableau », imprimée au-dessus.
- **D-007** — Q-003 A : `show-position-list` reçoit `columns:` (choisit et ordonne les colonnes), `widths:` (largeurs par colonne, `30mm` ou `20%`) et `legend:` ; tous optionnels, l'ancien appel garde son sens.
- **D-008** — Q-004 A : le temps du premier enregistrement est d'abord **mesuré et expliqué** ; une correction locale (un réglage, un appel évité) se fait ; tout changement d'architecture (export partiel, fil séparé) est **proposé** à l'ingénieur avec son coût avant d'être fait.
- **D-014** — (08.10.2026, l'ingénieur, après la mesure) il choisit le **remède 1** de §13 — « rafraîchir que les onglets qui les lisent » — et **refuse** la césure forcée de REQ-008. Réalisé comme une reconstruction **à la demande** de chaque onglet (`stale_tabs`, `refresh_tab`, `refresh_if_stale`), non comme une liste d'onglets lecteurs de positions, qui aurait vieilli sans le dire ; l'onglet Positions, qui tient ce qu'il vient d'écrire, n'est pas reconstruit ; « Import données », un PDF, un rechargement et un changement de langue restent des reconstructions complètes.

- **D-009** — Q-005 A : « Actions » reste **un** groupe ; deux sous-titres (une nouvelle sorte de ligne du volet : `SideNav`) y séparent Actions permanentes et Actions variables. `NAV_GROUPS`, lu par une dizaine de tests, **ne change pas de forme** : un tableau à part (`NAV_SECTIONS`, onglet → sous-titre qui le précède) est lu par la construction du volet.
- **D-010** — Q-006 A : dans `show-position-list`, une largeur invalide ou une colonne inconnue **arrête** la compilation en nommant la colonne et les clés valides (comme les autres arguments) ; un budget de largeur dépassé avec des valeurs valides donne une **note orange** visible dans le rapport ; la fenêtre valide « 30 », « 30mm », « 20% » à la saisie.
- **D-011** — Q-007 A : avec une position, les trois modes de Surfacique restent ; la dimension fixe est imposée. « Largeur » = l'étendue horizontale dessinée, « hauteur » = la verticale (mode diagonale) ; en mode arête et arête + largeur, la première arête est la dimension dessinée. Le réglage du mode est dans le volet de droite **et** dans la barre, une seule valeur derrière. On n'enregistre pas quelle dimension était fixée (`schema_version` inchangée) ; l'écart possible si la dimension de la position change plus tard est connu et accepté.
- **D-012** — Q-008 A : les options du mode Affichage sont gardées tant que la fenêtre est ouverte (mécanisme `view_state` / `restore` de `DisplayTab`) ; pas de fichier, pas de contrat.
- **D-013** — (inférée de la revue) « Surcharge » est la charge permanente non structurelle (le glossaire dit « Poids propre non-structural » pour *Auflast*) : ses noms allemand et anglais sont lus dans le glossaire et dans SIA 261, pas écrits de mémoire ; les six onglets et l'onglet « Charges » listeront plus tard les mêmes domaines : `docs/decisions.md` le dit pour qu'ils ne deviennent pas des doublons.

## 8. Hors périmètre

- Les calculs des actions (poids propre, surcharge, charge utile, neige, vent, séisme) : les onglets restent vides.
- Les modes de dessin « diagonal » et « arête + largeur saisie » de Surfacique : inchangés.
- Les tableaux d'autres commandes que la liste des positions.

## 9. Idées non retenues comme exigences

- Aucune.

## 10. Questions

### Q-001 — Que deviennent « Charges » et « Combinaisons de charges » ?
- **Pourquoi elle compte** : le groupe « Actions » contient aujourd'hui ces deux onglets ; ta demande décrit deux sections, sans dire où ils vont.
- **Options** : A (recommandée) — ils restent dans « Actions », sous les deux sections, jusqu'à ce que les nouveaux onglets aient leur contenu ; B — ils disparaissent du volet (les données restent) ; C — ils entrent dans une section de ton choix.
- **Réponse** : A — ils restent dans « Actions », sous les deux sections (08.10.2026, D-005)

### Q-002 — Que veut dire « Légende » pour le tableau ?
- **Pourquoi elle compte** : change ce qui est imprimé et la forme de l'option.
- **Options** : A (recommandée) — un texte libre imprimé **sous** le tableau (notes, abréviations), comme la légende d'une figure ; B — une légende générée (les couleurs de l'identifiant et les abréviations des colonnes) ; C — les deux.
- **Réponse** : A — un texte libre imprimé sous le tableau (08.10.2026, D-006)

### Q-003 — Forme des nouveaux arguments de `show-position-list` (colonnes, largeurs)
- **Pourquoi elle compte** : c'est la surface de commande de Typst, que tu dessines.
- **Options** : A (recommandée) — `columns: ("id", "type", …)` pour choisir et ordonner, `widths: (id: 30mm, type: 20%)` pour les largeurs ; B — un seul argument `columns: (("id", 30mm), ("type", 20%))`, où une colonne absente n'est pas imprimée ; C — un argument par colonne (`show-id: false`, `width-id: 30mm`…).
- **Réponse** : A — `columns:` et `widths:` (08.10.2026, D-007)

### Q-004 — Quel gain attends-tu au premier enregistrement ?
- **Pourquoi elle compte** : la cause n'est pas connue avant la mesure ; la réponse fixe jusqu'où optimiser (réglage, ou export partiel de la seule position).
- **Options** : A (recommandée) — je mesure d'abord, puis je te propose le gain atteignable et ses options, avant de les implémenter ; B — viser une seconde au plus, quoi qu'il en coûte à l'architecture.
- **Réponse** : A — mesurer d'abord, proposer ensuite (08.10.2026, D-008)

### Q-005 — Volet de gauche : comment montrer les deux sections ? (soulevée par la revue)
- **Pourquoi elle compte** : le volet ne connaît que des groupes et des entrées ; deux sections dans un groupe demandent une nouvelle sorte de ligne.
- **Options** : A (recommandée) — deux sous-titres dans le groupe « Actions » ; B — trois groupes plats.
- **Réponse** : A (08.10.2026, D-009)

### Q-006 — Largeur de colonne invalide ou colonne inconnue (soulevée par la revue)
- **Pourquoi elle compte** : Typst n'a pas d'avertissement ; chaque argument invalide de la commande arrête aujourd'hui le rapport en disant quoi écrire.
- **Options** : A (recommandée) — le rapport s'arrête en nommant la colonne ; B — une note orange sans arrêt.
- **Réponse** : A (08.10.2026, D-010)

### Q-007 — Surfacique avec une position : le geste (soulevée par la revue)
- **Pourquoi elle compte** : « largeur » et « hauteur » n'ont de sens que sur un rectangle aligné aux axes ; les modes « arête » dessinent dans n'importe quelle direction.
- **Options** : A (recommandée) — les trois modes restent, avec la dimension imposée ; B — un quatrième mode.
- **Réponse** : A (08.10.2026, D-011)

### Q-008 — Mémoire des options du mode Affichage (soulevée par la revue)
- **Pourquoi elle compte** : aucune option n'est mémorisée aujourd'hui ; chaque export reconstruit les onglets.
- **Options** : A (recommandée) — gardées tant que la fenêtre est ouverte ; B — dans les réglages de l'utilisateur ; C — dans le projet (nouveau contrat).
- **Réponse** : A (08.10.2026, D-012)

## 11. Critères d'acceptation

- [x] REQ-001 — dimension fixe d'une position (rec en largeur et en hauteur, pla)
- [x] REQ-002 — élément dessiné, lié à la position, exporté
- [x] REQ-003 — la dimension composée et relue, anciennes positions intactes
- [x] REQ-004 — mesure consignée, remède 1 réalisé (D-014) : la fenêtre n'est plus reconstruite après un enregistrement de position
- [x] REQ-005 — aucun plan coché : rien, sans erreur
- [x] REQ-006 — colonnes choisies et retenues
- [x] REQ-007 — largeurs fixes et en %
- [x] REQ-008 — tableau dans la marge, avertissement si dépassement
- [x] REQ-009 — tableau sur plusieurs pages, en-tête répété
- [x] UI-001 — options de Surfacique dès la sélection
- [x] UI-002 — Position, puis Largeur / Hauteur
- [x] UI-003 — deux sections dans « Actions »
- [x] UI-004 — six onglets vides, trois langues
- [x] UI-005 — section « Dimension » selon le type
- [x] UI-006 — « Titre » et « Légende »
- [x] UI-007 — colonnes et largeurs dans le volet de droite
- [x] ARCH-001 — domaine sans Qt, glossaires
- [x] ARCH-002 — arguments documentés, exemples, traductions
- [x] ARCH-003 — données additives et reproductibles
- [x] ARCH-004 — l'exception à la règle d'une colonne qui ne dit jamais sa largeur, amendée une fois (`calc-engine.typ`, `calculation-domains.md`, `decisions.md`)
- [x] ARCH-005 — les six onglets dans un module à part, `NAV_GROUPS` inchangé, raccourcis dits dans les Nouveautés
- [x] ARCH-006 — une dimension que l'ingénieur n'a pas touchée n'est jamais réécrite
- [x] ARCH-007 — une seule liste de colonnes, le défaut de `columns:` lu de la signature
- [x] Documentation : sections de `docs/` mises à jour, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en, `///` + exemples + traductions pour toute commande Typst.
- [x] Tests : fichiers `tests/test_*.py` ajoutés ou étendus, et passent (suite complète : 2 660 passés ; trois échecs examinés, un corrigé, deux tests de threads qui passent seuls).

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | UI-001 | capturé |
| T2 | REQ-001, UI-002 | capturé |
| T3 | REQ-001, UI-002, D-002 | capturé |
| T4 | REQ-001, REQ-002, D-002 | capturé |
| T5 | UI-003, D-005 | capturé (Q-001 répondue) |
| T6 | UI-004 | capturé |
| T7 | UI-004 | capturé |
| T8 | — | en-tête du bloc (contexte) |
| T9 | UI-005, REQ-003, D-003 | capturé |
| T10 | REQ-004, D-008 | capturé (Q-004 répondue : mesurer d'abord) |
| T11 | REQ-005, D-001 | capturé |
| T12 | UI-006 | capturé |
| T13 | UI-006, D-006 | capturé (Q-002 répondue) |
| T14 | REQ-006, REQ-007, UI-007, D-007 | capturé (Q-003 répondue) |
| T15 | REQ-008 | capturé |
| T16 | REQ-009, D-004 | capturé |
| revue | ARCH-004 à ARCH-007, D-009 à D-013, Q-005 à Q-008 | ajouté par la revue d'architecture |

### Points de la source non résolus

- T10 — la **cause** du temps n'est pas isolée : la revue a mesuré (§13) ; REQ-004 livre la mesure, les corrections locales et les propositions (D-008).

## 13. Revue d'architecture

**Verdict : APPROUVER AVEC RÉSERVES** (revue indépendante, `architecture-reviewer`, 08.10.2026). Rien de bloquant : aucun Qt dans un domaine, aucune valeur de norme, aucun chemin en dur, aucun changement de contrat de données. Deux affirmations de la première version de la spec étaient fausses et sont corrigées : l'erreur « aucun plan coché » **existe** (un refus volontaire de `lib/positions.typ`, figé par un test), et les options d'affichage **ne sont pas mémorisées**.

**Modules concernés.** Schéma : `schema_tab.py` (`TOOL_GROUPS` 67-88, `choose_tool` 813, les trois modes dans la barre 889, `build_properties` 1013, la carte de sélection et la liste des positions 1047, `fill_positions` 1238), `schema_canvas.py` (`AREA_MODES` 64, `area_points` 762, `add_area` 774 qui **ignore** `element_position`, `element_position` 213), `domains/schema.py` (`element_section` 557, `rectangle_from_edge` 965, contrat 1.1) et `domains/section.py` (`sides` 212). Volet : `woodcore_gui.py` (`NAV_GROUPS` 2813, `TABS`, `nav_widget` 3231), `chrome.py` (`SideNav` : seulement « groupe » et « entrée »), `member_check_tab.py` (`SoonTab`), `FutureTab`. Position : `positions_tab.py` (la combo du type et le seul champ `dimension` 470-482, `section_problem` 761, `save` 926), `section.py` (`parse`). Affichage et tableau : `display_options.py` (la spécification de `show-position-list` 98-103, `TITLE`, `KINDS`), `display_view.py` (`ids`, `values()` 252-255), `lib/positions.typ`, `lib/calc-engine.typ` (`render-table` 2184, `column-width` 2064, `table.header` 2230, la `note` 2244), `build_reference.py` (`typst_value`, `call_show_position_list` 680).

**À réutiliser.** `schema.element_section` et `section.sides` pour la dimension d'une position (pas de second lecteur) ; la combo et `fill_positions` du Schéma ; `canvas.element_position` (déjà testé) ; `cards.card` / `cards.form` ; `SoonTab` généralisée ; la `note` de `render-table` pour la légende ; `ds_opt_title` (Titre / Titel / Title existe déjà) ; le motif de refus `position-list-refuse` et l'assistant de test `_refusal`.

**Risques retenus** (tous repris dans les exigences ou le plan) : 001 REQ-005 (cause, test à renverser) ; 002 règle « une colonne ne dit jamais sa largeur » amendée une fois (ARCH-004) ; 003 dépassement de marge **mesuré** (REQ-008) ; 004 lignes qui se coupent (REQ-009) ; 005 refus ou note (D-010) ; 006 liste de colonnes en double (ARCH-007) ; 007 dictionnaire absent de `typst_value` (ARCH-007) ; 008 légende et glossaire (ARCH-007) ; 009 options non mémorisées (D-012) ; 010 ordre des colonnes (REQ-006) ; 011 banc de test du panneau (`test_display_view.py:35`, `:81`, `:196-215`) ; 012 écart polygone et position (D-011) ; 013 geste et orientation (D-011) ; 014 mode en double (D-011) ; 015 volet (D-009, ARCH-005) ; 016 module à part (ARCH-005) ; 017 « Surcharge » (D-013) ; 018 dimension non réécrite (ARCH-006) ; 019 `TITLE()` et `ds_opt_caption_table` à supprimer ; 020 coût de `reload()` (REQ-004).

**REQ-004, mesuré** (copie de `tests/projet-exemple`, Qt hors écran) : export `--data-only` 7,5 s la première fois, 5 à 5,7 s ensuite, dont ~4 s d'imports (openpyxl 1,3 s, pypdf 0,7 s) ; puis le **`reload()` de la fenêtre reconstruit les vingt-cinq onglets en ~10 s sur le fil de la fenêtre**, qui est ce qui la fige. Aucune étape propre au premier enregistrement n'est isolée (+2 s environ : cache froid et antivirus du dossier NextCloud, première copie du moteur, première reconstruction de `typst-reference.xlsx` 1,7 s contre 0,6 s). Corrections locales, sans changer l'export : imports tardifs d'openpyxl et de pypdf. À **proposer** (D-008) : rafraîchir seulement les onglets qui lisent les positions au lieu de `reload()` (le plus gros gain, ~10 s), garder un processus d'export vivant, mémoriser la lecture RFEM, exporter seulement la position changée, ne pas reconstruire `typst-reference.xlsx` sur `--data-only`.

**Les deux moitiés sont indépendantes** (le tableau Typst et Surfacique ne partagent que les fichiers de mots) ; le volet de gauche et la dimension d'une position le sont aussi.

**REQ-004 — résultat de la mesure (08.10.2026, copie de `tests/projet-exemple` hors du dépôt, deux sessions de mesure).** *Pourquoi l'enregistrement d'une position est long :* un enregistrement ne se contente pas d'écrire la position, il ré-exporte **tout le projet** (`woodcore-cli export --data-only`, `export_all.run`), puis la fenêtre **reconstruit ses 32 onglets** sur son propre fil (`MainWindow.rebuild`), qui reste figée sous une carte « chargement ». Chiffres : l'export prend 4,1 à 5,5 s (profil : lecture du modèle RFEM 1,28 s, dont 1,25 s à lire deux classeurs avec openpyxl ; lecture des PDF de fond de plan 0,58 s ; reconstruction de `typst-reference.xlsx` 0,46 s ; un processus fils de script 0,38 s ; version de Git et de Typst 0,18 s ; une grande part du reste est l'import d'openpyxl, 1,65 s, et de pypdf, 0,70 s, qui sont **déjà** importés à la demande mais dont l'export a réellement besoin, ce projet ayant des classeurs et des PDF) ; la reconstruction de la fenêtre prend 7,4 à 10,2 s (construction à froid 8,8 s). Soit **12 à 15 s par enregistrement**, dont les deux tiers sont la fenêtre. *Pourquoi « la première fois » :* aucune étape propre au premier enregistrement n'a été isolée (un export sans dossier `data/` n'est pas plus lent que le suivant sur cette machine) ; le surcoût de la première fois est celui d'un cache froid (Python, openpyxl, antivirus et synchronisation du dossier NextCloud) et de la première copie du moteur (`_woodcore/`), de l'ordre de 1 à 2 s. *Corrections locales :* aucune n'est sûre et utile à la fois (les imports sont déjà tardifs, le lecteur de PDF est déjà mis en cache) ; rien n'a été changé dans l'export, qui reste identique octet pour octet. **Propositions, à décider (D-008), par gain décroissant :** (1) après un enregistrement de position, ne rafraîchir que les onglets qui lisent les positions au lieu de reconstruire les 32 : environ 7 à 10 s gagnées, la fenêtre ne se fige plus ; (2) ne pas reconstruire `docs/typst-reference.xlsx` pour `--data-only` : 0,46 s, mais ce classeur ne se rafraîchirait plus à un enregistrement ; (3) mémoriser la lecture du modèle RFEM par l'empreinte des classeurs : jusqu'à 1,3 s quand ils n'ont pas changé ; (4) un processus d'export qui reste vivant : ~1,5 s d'imports, au prix d'un processus de plus à gérer ; (5) n'exporter que la position changée : le plus gros gain en principe, le plus gros changement de contrat (l'export est aujourd'hui tout ou rien et reproductible). La recommandation est (1), seule à rendre la fenêtre à l'ingénieur, puis (3).

## 14. Plan d'implémentation

Ordre : le plus petit et le plus isolé d'abord. Chaque étape tient dans des modifications ciblées (d'autres sessions éditent le dépôt ; `woodcore_gui.py` et `schema_tab.py` en particulier).

1. **REQ-005, aucun plan coché** — `lib/positions.typ` : supprimer le refus, ne rien imprimer pour `scope: "plans"` sans plan ; `tests/test_position_list.py` : renverser `no-plans` ; `tests/test_display_view.py` : compiler l'appel que la fenêtre écrit. Preuve : `-k position_list`, `-k display_view`.
2. **Le tableau (REQ-006 à REQ-009, ARCH-004)** — `lib/calc-engine.typ` : clé `width` optionnelle des colonnes, budget de largeur (valeurs fixes, pourcentages, plancher, réduction), note orange de dépassement, cellules insécables pour les tables qui le demandent, titre de colonne fixée qui passe à la ligne ; `lib/positions.typ` : `columns:`, `widths:`, `legend:` avec leurs refus nommant la colonne (D-010) ; amender `calculation-domains.md` et le commentaire de `calc-engine.typ` ; bloc `///`, deux exemples qui compilent, `calc/i18n/commands.json` fr/de ; tests : colonnes, largeurs, légende, **projet de 59 positions aux valeurs longues dans la marge**, deux pages et en-tête répété, `sheet-position-list` inchangée, commandes, site.
3. **Le panneau d'Affichage (UI-006, UI-007, ARCH-007, D-012)** — `display_options.py` : sorte « colonnes » (cases + champ de largeur validé à la saisie), `TITLE()` pour le titre, `ds_opt_legend`, suppression de `ds_opt_caption_table`, tuple unique des colonnes ; `display_view.py` : le widget, `view_state` ; `build_reference.py` : cas du dictionnaire, `call_show_position_list` étendu ; tests : `test_display_view`, `test_call_command`, `test_i18n`, égalité avec la liste de Typst.
4. **Le volet de gauche (UI-003, UI-004, ARCH-005, D-009, D-013)** — `chrome.py` : une ligne « sous-titre » dans `SideNav` (construction, délégué, repli) ; `woodcore_gui.py` : `NAV_SECTIONS`, six entrées de `TABS` à côté de `tab_loads`, `nav_widget` ; `calc/tools/action_tabs.py` : mots (`ac_`, trois langues, noms lus dans le glossaire et SIA 261), onglet « à venir » généralisé ; icônes ; `docs/decisions.md` : pas de doublon avec « Charges ». Tests : un fichier neuf, plus les huit fichiers qui lisent `NAV_GROUPS` sans changer.
5. **La dimension d'une position (UI-005, REQ-003, ARCH-006)** — `calc/domains/section.py` : champs d'un type, découpe, assemblage ; `positions_tab.py` : la carte « Dimension » (champs par type, champ libre de repli, assemblage seulement si un champ a changé). Tests : `test_section`, `test_positions_tab`.
6. **Surfacique (UI-001, UI-002, REQ-001, REQ-002, D-011)** — `domains/schema.py` : côté fixé d'une position et son imposition à `rectangle_from_edge` ; `schema_canvas.py` : `area_points` l'impose et `add_area` applique `element_position` ; `schema_tab.py` : carte « options de l'outil » affichée par `choose_tool` (mode reflété dans la barre, position depuis la même liste, dimension dessinée seulement pour une section à deux dimensions). Tests : `test_schema`, `test_schema_tab`, `test_toolbar`, lecture de `data/schemas.json`.
7. **REQ-004** — imports tardifs d'openpyxl et de pypdf (export inchangé octet pour octet : `test_the_export_is_reproducible`), mesure avant et après consignée dans la spec, propositions écrites pour l'ingénieur.
8. **Documentation** — `docs/ui/window.md` (Schéma, Position, Affichage, volet), `docs/domain/positions.md`, `detail-schemas.md`, `docs/typst/*`, `docs/decisions.md`, `docs/open-questions.md`, `CHANGELOG.md`, page « Nouveautés » de la prochaine version (0.117.0, pas encore publiée) en trois langues.
9. **Essai complet et vérification indépendante.**

**Ce que le plan ne fait pas** : aucun calcul d'action, aucun changement d'architecture de l'enregistrement (proposé seulement), aucun contrat de données, aucun commit ni push sans ta demande.

## 15. Vérification

_(Vérificateur indépendant `requirements-verifier`, 08.10.2026, tests lancés un `-k` à la fois, puis la suite complète : 2 660 passés, 17 ignorés, 3 échecs — deux tests de threads qui passent seuls, `test_tasks` et `test_typst_check`, et un test de thème qui visait une couleur écrite en dur par ce travail, corrigée, `test_theme` 10 ✓ ; première ronde, ses huit points repris.)_

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `schema.area_fixed` (lit `section.sides`) ; `test_a_position_fixes_one_side_of_an_area_and_the_other_is_drawn` : rec 100/200 → h fixe 200 en largeur, b fixe 100 en hauteur ; pla, cir, clt une dimension ; acier et sans section : None |
| REQ-002 | ✅ après correction | le test du Schéma lit maintenant `schema.build_record` (l'enregistrement de `data/schemas.json`) : trois éléments `area` de la position T001, polygones de côté fixé 200 et 300 mm |
| REQ-003 | ✅ | « 100 x 200 » rouvert puis enregistré reste « 100 x 200 » ; les champs saisis donnent « 100/240 » ; `test_positions_tab` 11 ✓ |
| REQ-004 | ⚠️ attendu | mesure, cause et cinq propositions chiffrées en §13 ; aucun code d'export changé (le vérificateur : seuls des ajouts à `schema.py` et `section.py`) ; `test_the_export_is_reproducible` est ignoré sans le vrai projet (`WOODCORE_REAL_PROJECT`) ; **les propositions attendent la décision de l'ingénieur (D-008)** |
| REQ-005 | ✅ | `lib/positions.typ` ne renvoie rien pour `scope: "plans"` sans plan ; le refus et son test sont renversés ; `test_no_plan_named_or_ticked_prints_nothing…` compile trois appels ; le panneau écrit `#show-position-list(scope: "plans")` (test) |
| REQ-006 | ✅ | `columns:` testé, ordre respecté ; la sélection survit à `MainWindow.rebuild()` (le vérificateur sur une vraie fenêtre), aucun fichier écrit |
| REQ-007 | ✅ | 30 mm et 20 % mesurés dans le PDF ; dix cas refusés en nommant la colonne ; `0%`, `-5mm` refusés |
| REQ-008 | ✅ avec limite écrite | 59 positions aux valeurs longues : bord droit ≤ 524 pt, avec et sans largeurs, note orange présente ; **limite connue** : un mot sans point de césure plus long que sa colonne sort de sa cellule (spec REQ-008, `open-questions.md`) |
| REQ-009 | ✅ | ≥ 3 pages, en-tête sur chacune, chaque ligne et la fin de sa description sur la même page |
| UI-001 à UI-007 | ✅ | `test_schema_tab` 42 ✓, `test_action_tabs` 4 ✓, `test_positions_tab` 11 ✓, `test_display_view` 13 ✓ ; trois langues, aucun « ß » |
| ARCH-001 à ARCH-007 | ✅ | domaine sans Qt ; commentaire du moteur amendé ; raccourcis Ctrl dans les Nouveautés ; défaut de `columns:` lu de la signature ; tuple de colonnes tenu égal à Typst par un test ; seul `test_the_export_is_reproducible` reste ignoré |
| Tables de données du moteur | ✅ | le rapport complet de 18 pages est identique page pour page avec l'ancien et le nouveau moteur (le vérificateur) |

**Restent, pour l'ingénieur** : décider des cinq remèdes à la lenteur (D-008), surtout le premier — ne rafraîchir que les onglets qui lisent les positions — ; dire s'il veut des césures forcées pour les mots sans point de césure (REQ-008) ; lancer `test_the_export_is_reproducible` sur son projet.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-08 | draft | spécification extraite de la demande (16 points) ; 4 questions ouvertes (Q-001 à Q-004) |
| 2026-10-08 | specified | Q-001 A, Q-002 A, Q-003 A, Q-004 A (toutes les options recommandées) ; D-005 à D-008 ; REQ-004, UI-003, UI-006, ARCH-002 reformulés |
| 2026-10-08 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES ; erreur « aucun plan » reproduite (refus volontaire), dépassement de marge mesuré, lenteur mesurée ; Q-005 à Q-008 (A) ; ARCH-004 à ARCH-007, D-009 à D-013 ; plan §14 écrit ; en attente de l'approbation unique |
| 2026-10-08 | approved | plan §14 approuvé par l'ingénieur (une approbation) ; implémentation à venir |
| 2026-10-08 | implementation | étapes 1 à 3 faites : REQ-005 (aucun plan : rien, test renversé) ; tableau (REQ-006 à 009, ARCH-004) avec columns:, widths: et legend:, budget de largeur, cellules insécables, césure ; panneau d Affichage (UI-006, UI-007, ARCH-007, D-012) : colonnes cochées avec largeurs, Titre et Légende, options gardées en mémoire à la reconstruction ; tests : test_position_list 18 ✓, test_display_view 12 ✓ ; reste : exemples gelés à régénérer, volet de gauche, dimension d une position, Surfacique, lenteur, documentation |
| 2026-10-08 | implementation | étapes 4 et 5 faites : volet de gauche (UI-003, UI-004, ARCH-005, D-009) : ligne de sous-titre dans SideNav, NAV_SECTIONS, six onglets (action_tabs.py, FutureTab généralisé, icônes), test_action_tabs 4 ✓ ; dimension d une position (UI-005, REQ-003, ARCH-006) : section.py (dimension_fields, split_dimension, join_dimension), carte Dimension dans positions_tab, texte jamais réécrit sans retouche ; test_section 13 ✓, test_positions_tab 10 ✓ ; reste : Surfacique, lenteur, exemples gelés, documentation, essai complet |
| 2026-10-08 | implementation | étape 6 faite : Surfacique (UI-001, UI-002, REQ-001, REQ-002, D-011) : schema.area_fixed, rectangle_with_fixed_side, rectangle_with_fixed_width ; canvas : area_fixed, tool_changed, add_area porte la position ; carte Options de l outil dans le volet de droite (mode reflété dans la barre, position depuis la même liste, dimension dessinée) ; test_schema_tab 42 ✓, test_schema, test_toolbar 16 ✓, test_schema_edit 33 ✓ ; reste : lenteur (REQ-004), exemples gelés, documentation, essai complet |
| 2026-10-08 | implementation | étape 7 faite (REQ-004, D-008) : mesure et explication dans la spec §13 (export 4 à 5 s, reconstruction de la fenêtre 7 à 10 s sur son propre fil, 12 à 15 s par enregistrement), aucune correction locale sûre (imports déjà tardifs), cinq propositions chiffrées pour l ingénieur, export inchangé ; reste : exemples gelés à régénérer, documentation, essai complet, vérification |
| 2026-10-08 | testing | étape 8 faite : window.md (Surfacique, Actions, Dimension, tableau en Affichage), calculation-domains.md (l exception à une colonne ne dit jamais sa largeur), api-conventions.md, positions.md, detail-schemas.md, decisions.md (deux entrées), open-questions.md, layout.md, CHANGELOG, Nouveautés 0.117.0 fr/de/en ; exemples gelés régénérés, test_commands 34 ✓, test_site 37 ✓ ; étape 9 : suite complète et vérification indépendante lancées |
| 2026-10-08 | testing | corrections après la vérification indépendante : commentaire du moteur amendé (ARCH-004), raccourcis Ctrl dans les Nouveautés (ARCH-005), test lisant l export du Schéma (REQ-002), appel sans plan coché (REQ-005), défaut de columns lu de la signature (ARCH-007), étiquette v0.117 harmonisée, limite connue de REQ-008 écrite ; exemples gelés régénérés ; suite complète relancée |
| 2026-10-08 | verification | vérification indépendante faite (§15) : tout ✅ sauf REQ-004 (propositions D-008 à décider, test d export reproductible ignoré sans le vrai projet) ; suite complète 2660 passés, 17 ignorés, 3 échecs (deux tests de threads qui passent seuls, un test de thème que ce travail causait : corrigé) ; spec laissée dans active/ en attente de la décision de l ingénieur |
