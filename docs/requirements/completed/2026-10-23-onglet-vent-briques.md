---
id: 2026-10-23-onglet-vent-briques
titre: Onglet Vent repensé, bâti sur le type «Calcul» et les briques de #95
status: completed
cree: 2026-10-23
mis_a_jour: 2026-10-24
source: issue GitHub #100 ; messages de l'ingénieur du 23.10.2026
docs: [docs/ui/building-a-tab.md, docs/ui/calc-tab.md, docs/domain/loads.md, docs/ui/window.md]
---

# Onglet Vent repensé, bâti sur le type «Calcul» — Spécification

## 1. Objectif

L'ingénieur veut refaire l'onglet Vent (SIA 261:2020, chapitre 6 et annexes C et E) tel que décrit par l'issue #100 (prototype HTML, cinquième version) : un formulaire en quatre sections, la norme au survol, un modèle 3D du bâtiment, deux Résultats 3D, un volet droit de modules, une vue Affichage du fichier `.typ`, et un fichier/rapport corrigés des défauts de la 0.122.

L'onglet est le deuxième onglet de calcul : il est une classe de paramètres sur `calc_tab.CalcTab` et utilise les services de #95. Toute brique qui manque est complétée dans la brique, pour tous les onglets, jamais en version locale ; le modèle 3D devient lui-même une brique réutilisable. Cette spec absorbe #103 (migration du Vent sur le type) : #103 en est un sous-ensemble.

## 2. Source

La source, mot pour mot et numérotée `T1` à `T173`, est dans [`2026-10-23-onglet-vent-briques-source.md`](2026-10-23-onglet-vent-briques-source.md) : l'issue #100 (parties A), la question de l'ingénieur (B), le corps de l'issue #103 (C), l'analyse rendue (D), les réponses de l'ingénieur (E) et la vérification dans le code (F). Les réponses aux questions de cette spécification sont citées en §10.

## 3. Exigences fonctionnelles

### Domaine du vent (calc/domains/, sans Qt)

### REQ-001 — Pression dynamique de pointe
- **Exigence** : Woodcore doit calculer q<sub>p</sub> au point le plus haut, constant sur la hauteur, avec z = h par défaut et z saisissable ; c<sub>h</sub> = 1,6·[(z/z<sub>g</sub>)<sup>α<sub>r</sub></sup> + 0,375]² ; z au moins 5 m, 10 m en catégorie IV ; au-dessus de 30 m la catégorie IV prend le profil de la catégorie III.
- **Source** : T29, T30, T31, T23
- **Priorité** : doit
- **Critère d'acceptation** : tests de domaine : z = h par défaut ; z = 3 m relevé à 5 m ; catégorie IV et z = 6 m relevé à 10 m ; catégorie IV à h = 40 m donne le profil III ; c<sub>h</sub> et q<sub>p</sub> égaux aux valeurs de `compute()` du prototype.

### REQ-002 — Forces globales
- **Exigence** : Woodcore doit calculer Q<sub>k</sub> = c<sub>red</sub> · c<sub>d</sub> · c<sub>f</sub> · q<sub>p</sub> · A<sub>ref</sub> (15), avec c<sub>red</sub> de la figure 9 pour b·h et d·h (chacun valable à moins de 15° de sa direction, le plus défavorable des deux ailleurs, 6.3.3), c<sub>red</sub> = 1,0 pour la toiture (6.3.2), Q<sub>1</sub> sur A (b·h), Q<sub>2</sub> sur C (d·h), Q<sub>3</sub> vertical sur d·b, et le facteur des en-têtes compris dans A<sub>ref</sub>.
- **Source** : T32, T33, T34, T35, T23
- **Priorité** : doit
- **Critère d'acceptation** : test sur la halle du tableau 36 : Q<sub>k,1–3</sub> par φ égaux à ceux de `compute()` du prototype ; à φ = 10° c<sub>red</sub> est celui de b·h, à φ = 50° le plus défavorable des deux ; toiture c<sub>red</sub> = 1,0.
- **Amendé après la revue** : Les variables `qk_max_cf*`/`qk_min_cf*` (kN/m²), que les sections citent et que `loads_names` compare, gardent leur nom et leur unité ; les Q<sub>k</sub> en kN s'ajoutent (additif). A<sub>ref</sub> se calcule d'une table fermée du fichier de norme (coefficient et puissances de b, d, h) — jamais d'`eval` des libellés —, et un libellé à cotes absentes (h₁, d₁, hs, π·d²/8…) donne q<sub>k</sub> par m² seulement et le message orange de T46 (revue, ARCH-RISK-008).

### REQ-003 — Pressions locales avec c<sub>d</sub>
- **Exigence** : Woodcore doit calculer q<sub>k</sub> = q<sub>p</sub> · (c<sub>d</sub> · c<sub>pe</sub> − c<sub>pi</sub>) selon (13), (14), (17), (18), sans c<sub>red</sub> (6.3.1), pression positive vers la surface, succion négative, une valeur ±0,1 comptée avec ses deux signes. `wind_source.local_pressures` doit recevoir c<sub>d</sub>.
- **Source** : T36, T37, T38, T39, T125, T131, T134
- **Priorité** : doit
- **Critère d'acceptation** : test à c<sub>d</sub> = 1,0 (résultat inchangé) et à c<sub>d</sub> ≠ 1 (q<sub>k</sub> = q<sub>p</sub>·(c<sub>d</sub>·c<sub>pe</sub> − c<sub>pi</sub>), vérifié à la main pour une surface) ; une surface à ±0,1 donne les deux signes ; aucun c<sub>red</sub> dans le résultat.

### REQ-004 — Extrêmes par surface avec provenance
- **Exigence** : Woodcore doit garder, pour chaque surface, la plus grande pression et la plus grande succion sur les directions du tableau, avec la direction φ, le c<sub>pe</sub> et le c<sub>pi</sub> qui les ont données, et rendre q<sub>k</sub> par surface et par φ (détail).
- **Source** : T40, T135, T67
- **Priorité** : doit
- **Critère d'acceptation** : test : pour chaque surface de la halle du tableau 36, `max`/`min` portent φ, c<sub>pe</sub>, c<sub>pi</sub> ; recalculer q<sub>k</sub> avec ces trois valeurs redonne l'extrême ; le détail contient une valeur pour chaque couple (surface, φ) du tableau.

### REQ-005 — Clés de provenance de chaque nombre
- **Exigence** : Woodcore doit rendre, pour chaque nombre affiché (extrême, cellule du détail), les clés des cellules du tableau qui l'ont produit (φ, colonne c<sub>pe</sub>, colonne c<sub>pi</sub>).
- **Source** : T159, T109, T110, T166
- **Priorité** : doit
- **Critère d'acceptation** : test de domaine : la clé rendue pour un extrême désigne la cellule c<sub>pe</sub> et la colonne c<sub>pi</sub> utilisées dans REQ-004 ; le format des clés est celui de ARCH-004 (pas de clé propre au vent dans la brique).

### REQ-006 — Choix des ouvertures
- **Exigence** : Woodcore doit donner, selon le cas d'ouvertures choisi dans l'onglet (réparties de façon homogène, ou ouverture dominante A, B, C ou D), la colonne c<sub>pi</sub> du tableau, et enregistrer ce choix dans la source du cas.
- **Source** : T41, T136, T68, T153
- **Priorité** : doit
- **Critère d'acceptation** : test : changer le cas change la colonne c<sub>pi</sub> et les q<sub>k</sub> ; le choix est relu à la réouverture du cas ; `schemas/wind-source` valide la source (voir CON-002).
- **Amendé après la revue** : Le champ ne s'offre que pour un tableau qui a des colonnes d'ouverture ; pour les tableaux 46-50 (c<sub>pi</sub> propre à chaque surface) et 57a-d, 63, 64 (aucun c<sub>pi</sub>), il est caché (`visible_fields`) et ignoré, et une valeur gardée d'un autre tableau n'est pas refusée. Schéma `wind-source` 1.2, qui contient 1.1 (`links`) ; 1.0 et 1.1 restent lus (revue, ARCH-RISK-007 ; D-24).

### REQ-007 — Surfaces localisées m, n, o
- **Exigence** : Woodcore doit montrer les surfaces localisées m, n, o à part, sans les superposer aux grandes surfaces (figure 22), et rappeler la phrase de la norme.
- **Source** : T42, T70
- **Priorité** : doit
- **Critère d'acceptation** : dans les résultats, m, n, o sont dans le tableau Surfaces localisées, pas dans Murs ni Toiture ; aucune somme ne mêle ces surfaces aux grandes.

### REQ-008 — ĉ<sub>pe</sub>
- **Exigence** : Woodcore doit donner une note ĉ<sub>pe</sub> · q<sub>p</sub> pour les pressions de courte durée sur les zones sensibles, sous les coefficients de pression.
- **Source** : T43, T66
- **Priorité** : doit
- **Critère d'acceptation** : la note existe en section 4, avec la valeur ĉ<sub>pe</sub> · q<sub>p</sub> du tableau choisi ; aucune mention de ĉ<sub>pe</sub> en section 2.

### REQ-009 — Messages du calcul
- **Exigence** : Woodcore doit produire (`messages(src)`), chacun lié à son champ, les messages rouges (ID manquant ; q<sub>p0</sub> manquant ou nul ; b, d ou h ≤ 0 ; h > 200 m (6.1.2) ; z ≤ 0 ; aucun bâtiment choisi), les messages orange (z relevé au minimum de 6.2.1.2 ; catégorie IV au-dessus de 30 m ; c<sub>d</sub> = 1,0 hors des cas de 6.3.5 ; β hors de la figure 9 ; proportions saisies à plus de 1,5 fois celles du tableau ; c<sub>f1</sub> marqué « * » ; surfaces de référence à cotes (h₁, d₁…) avec q<sub>k</sub> par m² seulement) et le message vert « Toutes les entrées sont là, le calcul est fait. ». Rouge empêche le calcul ; orange informe et le calcul se fait.
- **Source** : T44, T45, T46, T47, T137
- **Priorité** : doit
- **Critère d'acceptation** : un test par message : l'entrée qui le provoque, sa couleur, le champ désigné, et le calcul bloqué (rouge) ou fait (orange) ; avec toutes les entrées valides, seul le vert apparaît.
- **Amendé après la revue** : Les erreurs rouges sont rendues par `messages(src)` avant `check_source`, comme la neige, pour qu'un même défaut ne soit pas dit deux fois (revue, ARCH-RISK-015).

### REQ-010 — Géométrie des 37 bâtiments
- **Exigence** : Woodcore doit porter, pour les 37 bâtiments de l'annexe C, la géométrie relevée sur la figure de chaque tableau (forme du toit, pente, proportions h : b : d, place de A à H, de m, n, o et des forces), les six du prototype (tableaux 31, 32, 36, 40, 59a, 59b) étant repris de `DRAWN`.
- **Source** : T16, T24, T85, T138, T169
- **Priorité** : doit
- **Critère d'acceptation** : un test charge la géométrie des 37 tableaux et refuse un tableau sans géométrie ; chaque surface du tableau de coefficients (A à H, m, n, o…) a sa place dans la géométrie de son bâtiment ; les six de `DRAWN` donnent les mêmes valeurs que le prototype.

### REQ-011 — Extraits de la norme
- **Exigence** : Woodcore doit porter l'emplacement de chaque extrait (page et rectangle en points PDF, par édition FR et DE) et son texte mot pour mot, à côté des `norm_ref`, pour 6.2.1.1 à 6.3.5, le tableau 4, les figures 9 et 22, l'annexe E et les tableaux 31 à 64, et la correspondance champ → clause (`FIELD_NORM`).
- **Source** : T21, T22, T139, T164
- **Priorité** : doit
- **Critère d'acceptation** : un test tient chaque extrait au PDF livré (texte attendu dans le rectangle, par édition) ; tout champ du formulaire a sa clause ; aucun extrait n'est recopié hors de `calc/norms/`.

### REQ-012 — Figure de la norme pour tous les bâtiments
- **Exigence** : Woodcore doit offrir, pour les 37 tableaux, la figure de la norme (vue « figure de la norme » de la section Bâtiment, module Bâtiment, et figure du fichier).
- **Source** : T59, T101, T116, T169
- **Priorité** : doit
- **Critère d'acceptation** : pour chacun des 37 tableaux, un extrait de figure est défini et tenu au PDF par un test (REQ-011).

### Fichier et rapport

### REQ-013 — Tableau des forces globales dans le fichier
- **Exigence** : Woodcore doit écrire le tableau des forces globales comme la fenêtre le montre : Q<sub>k</sub> en kN, avec les nombres (pas le nom des variables), une force n'étant pas imprimée comme une charge ; les lignes q<sub>k</sub> par m² sont gardées.
- **Source** : T121, T127, T128, T146
- **Priorité** : doit
- **Critère d'acceptation** : sur la halle du tableau 36, `WL-01.typ` contient les nombres de la fenêtre pour Q<sub>k,1–3</sub>, aucune chaîne `qk_max_cf1`, aucun libellé « Force globale du vent » avec l'unité kN/m² ; les lignes q<sub>k</sub> par m² sont présentes.

### REQ-014 — Tableau des forces locales dans le fichier
- **Exigence** : Woodcore doit écrire seulement le cas d'ouvertures choisi ; le tableau est transposé (une colonne par surface, une ligne max, une ligne min ; `columns: (auto,) + (1fr,) * n`), sa note dit que m, n et o sont des surfaces localisées ; au-delà de douze surfaces il est coupé en deux blocs l'un sous l'autre.
- **Source** : T122, T123, T124, T129, T146
- **Priorité** : doit
- **Critère d'acceptation** : test sur le tableau 36 (un cas, pas six colonnes de cas) ; test sur le tableau 60a (29 surfaces : blocs de ≤ 12 surfaces, un titre/une note) ; test sur un tableau de 12 surfaces (un bloc) et de 13 (deux blocs) ; fichier compilé par Typst sans erreur.
- **Amendé après la revue** : « Coupé en deux blocs » se lit : des blocs de douze surfaces au plus, n = ⌈surfaces/12⌉, équilibrés (le tableau 60a, 29 surfaces, en trois). Les tableaux transposés et coupés sont émis par le domaine dans `instance["tables"]`, que le fichier et la fenêtre lisent tous deux ; `_table_lines` et `tables_html` restent génériques, une fonction Qt-free commune résout les cellules qui nomment une variable (revue, ARCH-RISK-009).

### REQ-015 — c<sub>d</sub> dans le fichier
- **Exigence** : Woodcore doit écrire des q<sub>k</sub> locaux qui contiennent c<sub>d</sub> (REQ-003) et dire c<sub>d</sub> dans les entrées du fichier.
- **Source** : T125, T131 (« dire c<sub>d</sub> dans les entrées » est déduit : la source ne le demande pas ; à retirer si la revue juge le tableau suffisant)
- **Priorité** : devrait
- **Critère d'acceptation** : à c<sub>d</sub> ≠ 1, les nombres du fichier égalent ceux de la fenêtre.

### REQ-016 — Fichier français sans mot allemand
- **Exigence** : Woodcore doit n'écrire dans le fichier français aucun mot allemand : « Geländekategorie », « Tabelle », « Anhang E », « Anhang C », « Figur 9 » remplacés par les mots et clauses du français (via `calc/i18n/` et les clauses par langue).
- **Source** : T126, T130, T148
- **Priorité** : doit
- **Critère d'acceptation** : test : `WL-01.typ` généré en français ne contient aucun des cinq termes ni aucun mot d'une liste de mots allemands de contrôle ; les fichiers en de et en ont leurs mots dans leur langue.

### REQ-017 — Figure de la norme découpée à l'enregistrement
- **Exigence** : Woodcore doit découper la figure de la norme du bâtiment dans le PDF de la SIA à l'enregistrement du cas (pas à l'export), et la ranger avec les exports du vent ; la figure est recadrée, avec la légende de Woodcore dessous.
- **Source** : T116, T156, T170, T173
- **Priorité** : doit
- **Critère d'acceptation** : après « Enregistrer » d'un cas au niveau 3, le fichier image existe dans le dossier convenu (voir Q-001) ; un export ou une compilation ne demande aucune fenêtre ni bibliothèque PDF.
- **Amendé après la revue** : La découpe se fait **dans l'export**, qui tourne à chaque enregistrement (D-28) : `calc/domains/annex.py` `crop` (pypdf, vectoriel, sans Qt), une image par édition, rangée dans `Variable-loads/Wind/Exports/Figures/` par `_files` comme toute figure de domaine, jamais supprimée par l'export suivant, la même avec ou sans fenêtre. `wind-load` entre dans `project.FIGURE_KINDS` et `LOAD_FIGURE_KINDS` (et leurs lecteurs : `registry.write_files`, `validation`, `stamps`, `project_migrate_folders`, `archive_export`). Le schéma `calculations` passe en 1.9 si l'entrée de figure porte ses éditions. La boîte de découpe exclut le tampon du titulaire de la norme.

### REQ-018 — Figure écrite au niveau 3 seulement
- **Exigence** : Woodcore doit écrire la figure dans `<id>.typ` quand le domaine est au niveau 3 et ne pas l'écrire aux niveaux 1 et 2 ; la figure n'a pas de niveau propre ; elle se règle par sa largeur, sa légende, son label et la case « Afficher » qui garde le choix de l'ingénieur.
- **Source** : T117, T118, T147, T157
- **Priorité** : doit
- **Critère d'acceptation** : générer `WL-01.typ` aux niveaux 1, 2, 3 : la figure n'est présente qu'au 3 ; `width`, `caption`, `label` se règlent ; « Afficher » décoché la masque au niveau 3.
- **Amendé après la revue** : La ligne de la figure est **toujours écrite**, avec un niveau 3 que **Typst** résout à la compilation (D-29) : elle n'est imprimée qu'au niveau 3, en « auto » comme dans les variantes, et ses réglages (largeur, légende, label, « Afficher ») restent sur la ligne. Remplace D-22.

### REQ-019 — Le rapport n'imprime aucun 3D
- **Exigence** : Woodcore ne doit imprimer aucun Résultat 3D ni le modèle 3D dans le fichier ni dans le rapport.
- **Source** : T116, T120
- **Priorité** : doit
- **Critère d'acceptation** : `WL-01.typ` ne contient aucune image issue du rendu 3D ; la figure écrite est celle de la norme.

### REQ-020 — Tableaux trapus
- **Exigence** : Woodcore doit, pour le vent, écrire les tableaux plutôt larges que hauts (le tableau des forces locales transposé).
- **Source** : T172, T171, T123
- **Priorité** : doit
- **Critère d'acceptation** : voir REQ-014 (aucun tableau du fichier du vent n'a plus de 12 colonnes de surfaces ni plus de lignes que de colonnes de surfaces, déduit de « trapu plutôt que haut » ; la revue peut préciser le seuil).
- **Amendé après la revue** : « Trapu » se vérifie par le seuil de REQ-014 : douze colonnes de surfaces au plus par bloc (revue, ARCH-RISK-016).

### Défauts de la 0.122

Les cinq défauts sont couverts par REQ-013 (T127, T128), REQ-014 (T129), REQ-003 (T131) et REQ-016 (T130). Chaque case de T127 à T131 doit être cochée par le test nommé dans le critère de l'exigence correspondante.

## 4. Exigences d'interface (fenêtre, rapport, site)

Pour tout UI : **Langues** fr / de / en (toute chaîne visible existe dans les trois, y compris les boutons, notes, messages et en-têtes de colonnes ; `tests/test_i18n.py`). Source de T149.

### UI-001 — Deux vues
- **Exigence** : Woodcore doit donner à l'onglet Vent deux vues, Calcul (formulaire en quatre sections, norme au survol, modèle 3D, volet droit de modules) et Affichage (fichier `.typ` compilé, réglage de chaque élément), comme la neige.
- **Source** : T3, T4, T5
- **Priorité** : doit
- **Critère d'acceptation** : l'onglet Vent montre les deux vues et se bâtit sur `CalcTab` (ARCH-001).

### UI-002 — Standards de la neige
- **Exigence** : Woodcore doit reprendre tous les standards de la neige : la bulle (texte de la norme mot pour mot, puis l'image de l'extrait dessous, sans onglets, placée là où elle ne couvre rien) ; le clic qui épingle l'extrait sous le module Résultats, un second clic qui le retire ; le Ctrl+clic qui ouvre la norme dans le lecteur PDF de Woodcore à la page, la clause encadrée (chapitre 6 : FR p. 30–35, DE p. 29–34 ; annexe C p. 81–114 pour un tableau ou une figure de bâtiment) ; la langue de la norme qui suit la fenêtre, l'allemand à défaut ; la carte de l'annexe E sur `https://261.sia.ch/?lang=fr&layer=wind`, avec `lang=de` quand la fenêtre est en allemand ou en anglais.
- **Source** : T49–T54, T144, T11, T12, T161, T162
- **Priorité** : doit
- **Critère d'acceptation** : tests de l'onglet : bulle sur un champ de chaque section ; clic puis second clic ; Ctrl+clic ouvre la page attendue (FR 30, DE 29 pour 6.2.1.1, à confirmer sur le PDF) ; fenêtre en anglais donne le texte allemand ; l'URL de la carte pour fr, de, en.

### UI-003 — Formulaire en quatre sections
- **Exigence** : Woodcore doit présenter le formulaire en quatre sections dans cet ordre : 1 Données de base, 2 Bâtiment (annexe C), 3 Coefficients de réduction et de force, 4 Coefficients de pression.
- **Source** : T55, T140
- **Priorité** : doit
- **Critère d'acceptation** : `tab.service("form")` donne quatre sections dans cet ordre.

### UI-004 — Section 1, données de base
- **Exigence** : Woodcore doit y montrer q<sub>p0</sub>, la catégorie de terrain, b · d · h, z (« z = h » coché par défaut) et c<sub>d</sub>.
- **Source** : T56, T29
- **Priorité** : doit
- **Critère d'acceptation** : champs présents ; la case « z = h » est cochée à la création d'un cas ; décochée elle laisse saisir z.

### UI-005 — Section 2, bâtiment
- **Exigence** : Woodcore doit y offrir le choix du tableau, puis, au-dessus de l'image, le tableau, son titre, h : b : d du tableau, la toiture et les proportions saisies (sans ĉ<sub>pe</sub>, c<sub>fr</sub> ni étiquettes « Q₁ sur A (b·h)… »), puis deux vues, la figure de la norme ou le modèle 3D, seul endroit du centre où se trouve le bâtiment.
- **Source** : T57, T58, T59, T70
- **Priorité** : doit
- **Critère d'acceptation** : la section contient exactement ces éléments dans cet ordre ; une bascule choisit figure de la norme ou modèle 3D ; aucun autre widget du centre ne dessine le bâtiment.

### UI-006 — Section 3, réduction et force
- **Exigence** : Woodcore doit y montrer, dans cet ordre : les facteurs de réduction (figure 9) avec b·h, d·h, oblique et d·b ; les coefficients de force du tableau, cellules colorées selon leur valeur ; le tableau des forces globales Q<sub>k,1–3</sub> en kN avec c<sub>red</sub> par φ, les extrêmes marqués et A<sub>ref</sub> ; la formule (15) ; le Résultat 3D · forces globales.
- **Source** : T60–T64
- **Priorité** : doit
- **Critère d'acceptation** : les cinq éléments dans l'ordre ; les extrêmes marqués correspondent à REQ-002 ; la couleur d'une cellule suit sa valeur (même valeur, même couleur).

### UI-007 — Section 4, pression
- **Exigence** : Woodcore doit y montrer, dans cet ordre : les coefficients c<sub>pe</sub> et c<sub>pi</sub> du tableau, colorés, avec la colonne c<sub>pi</sub> des ouvertures choisies marquée, la légende et la note ĉ<sub>pe</sub> ; le détail par φ (q<sub>k</sub> de chaque surface à chaque direction, coloré), toujours affiché, sans bouton pour le replier, sur toute la largeur du volet, avec une largeur minimale puis un défilement horizontal ; les ouvertures en liste déroulante sur la ligne du mot, et la formule de q<sub>k</sub> ; le Résultat 3D · charges de surface. Le bâtiment n'y est plus ; les tableaux Murs, Toiture et Surfaces localisées ne sont plus au centre.
- **Source** : T65–T70
- **Priorité** : doit
- **Critère d'acceptation** : les quatre éléments dans l'ordre ; aucun widget de repli sur le détail ; un volet étroit donne un défilement horizontal, non une troncature ; aucun tableau Murs/Toiture/Localisées dans le centre.

### UI-008 — Modèle 3D, contenu
- **Exigence** : Woodcore doit montrer un modèle qu'on tourne à la souris (sans sélection de texte au glisser), qui dessine : le bâtiment du tableau dans les proportions du tableau (pas celles saisies) ; A à H, m, n, o là où la figure du tableau les place ; b, d, h, et h<sub>e</sub> à l'égout pour un toit à deux pans avec le h du faîte ; α ; Q₁ à Q₃ en noir ; la direction φ en bleu. Aucune vue fixe ni vue « pression par φ ».
- **Source** : T71, T72
- **Priorité** : doit
- **Critère d'acceptation** : un bâtiment de proportions saisies très différentes se dessine aux proportions du tableau ; glisser ne sélectionne aucun texte ; chaque élément listé est présent (SVG du module sans Qt, testé).

### UI-009 — Modèle 3D, vues et zoom
- **Exigence** : Woodcore doit offrir les boutons Face A, Face C (exactement de face), Iso, Dessus ; le zoom à la molette ou par − / + et « Ajuster » (100 %), du quart de la largeur du dessin à cinq fois sa largeur, toujours centré sur le bâtiment (la vue ne se déplace pas) ; l'échelle ne change pas quand on tourne, calculée une fois sur la sphère qui contient le bâtiment, ses forces et la flèche φ.
- **Source** : T73, T74, T75, T76
- **Priorité** : doit
- **Critère d'acceptation** : test sans Qt : l'échelle est identique pour deux rotations du même bâtiment ; zoom borné à [0,25 ; 5] ; Face A et Face C : l'axe de visée est exactement perpendiculaire à la face ; aucune commande de déplacement.

### UI-010 — Faces cachées
- **Exigence** : Woodcore ne doit pas dessiner une face vue de côté ou de dos, ni sa lettre, ni les surfaces posées dessus ; ni une force ou la flèche φ vue dans son axe, ni une cote vue de bout.
- **Source** : T77, T78
- **Priorité** : doit
- **Critère d'acceptation** : tableau 32 en Face A : le rendu ne contient que la lettre A, ni E, F, G, H, m, n, ni Q₁, ni φ = 0°.

### UI-011 — Surfaces m, n, o dans le modèle
- **Exigence** : Woodcore doit poser les surfaces m, n, o contre leur face (pas au-dessus) et couper en deux une surface qui traverse le faîte, une partie sur chaque versant.
- **Source** : T79
- **Priorité** : doit
- **Critère d'acceptation** : test géométrique : toutes les arêtes de m, n, o sont dans le plan de leur face ; une surface à cheval sur le faîte donne deux polygones, un par versant.

### UI-012 — Curseur φ
- **Exigence** : Woodcore doit offrir un curseur φ libre de 0° à 360° ; la flèche tourne autour du bâtiment, le vise toujours, avec un arc depuis φ = 0° ; φ = 0° souffle sur A dans le sens de Q₁, φ = 90° sur C dans le sens de Q₂ ; sur une forme ronde la flèche reste perpendiculaire à la surface.
- **Source** : T80, T81, T82
- **Priorité** : doit (la forme ronde : devrait, déduit de ce que T82 est au conditionnel et que les 37 tableaux sont à relever)
- **Critère d'acceptation** : φ = 0° et 90° : direction de la flèche = sens de Q₁ et Q₂ ; φ = 360° équivaut à 0° ; arc dessiné entre 0° et φ.

### UI-013 — Survols dans le modèle
- **Exigence** : Woodcore doit allumer une surface survolée (dans un tableau ou sur le bâtiment) et la montrer à travers le bâtiment sur toute sa longueur, même derrière ; b·h, d·h et d·b allument leur surface de référence sur le bâtiment, au centre comme dans le module Bâtiment, et rien d'autre.
- **Source** : T83, T84
- **Priorité** : doit
- **Critère d'acceptation** : survol d'une surface cachée : elle est dessinée complètement, par-dessus le reste ; survol de b·h : seule la surface b·h s'allume.

### UI-014 — Deux Résultats 3D et leurs commandes
- **Exigence** : Woodcore doit offrir deux dessins sur le même modèle (Résultat 3D · forces globales en section 3, Résultat 3D · charges de surface en section 4), chacun tourné et zoomé à part, avec ses commandes : un bouton par direction du tableau et « Max, toutes directions » ; max (+) ou min (−) pour les forces, pression max (+) ou succion max (−) pour les charges.
- **Source** : T87, T88, T89, T142
- **Priorité** : doit
- **Critère d'acceptation** : tourner l'un ne tourne pas l'autre ; les boutons de direction correspondent aux directions du tableau choisi ; « Max, toutes directions » donne le même résultat que REQ-004 / REQ-002.

### UI-015 — Résultat 3D · forces globales
- **Exigence** : Woodcore doit dessiner Q<sub>k,1</sub>, Q<sub>k,2</sub>, Q<sub>k,3</sub> dans leur direction avec leur valeur en kN, les flèches à l'échelle de la plus grande force.
- **Source** : T90
- **Priorité** : doit
- **Critère d'acceptation** : la longueur de la plus grande flèche est le maximum, les autres proportionnelles ; chaque valeur en kN est celle du volet Résultats.

### UI-016 — Résultat 3D · charges de surface
- **Exigence** : Woodcore doit garder les faces neutres (ni rouges ni bleues) ; dessiner, sur chaque face vue, sa charge q<sub>k</sub> en plan de charge tenu par des flèches (comme dans RFEM), à l'échelle de la plus grande valeur, avec sa valeur en kN/m² ; déplacer avec un trait une valeur qui couvrirait une lettre ou une autre valeur ; dessiner les charges de m, n, o en plus de celle de leur face.
- **Source** : T91, T92, T93, T94
- **Priorité** : doit
- **Critère d'acceptation** : aucune face colorée ; deux valeurs ne se recouvrent pas dans un cas de test (rendu SVG) ; pour une face portant m : deux plans de charge ; échelle commune à toutes les faces.

### UI-017 — Couleurs et texte
- **Exigence** : Woodcore doit colorer une pression en rouge (vers la surface) et une succion en bleu (en s'éloignant) ; la valeur prend la couleur de sa flèche ; le texte n'est jamais écrit sur la flèche. Les couleurs sont lues dans `calc/tools/theme.json` (déduit de CLAUDE.md, « no hardcoding »).
- **Source** : T95
- **Priorité** : doit
- **Critère d'acceptation** : test : sens de la flèche et couleur selon le signe ; la boîte du texte ne recoupe pas le segment de la flèche.

### UI-018 — Épingler et fenêtre
- **Exigence** : Woodcore doit permettre d'épingler chaque Résultat 3D au volet droit, sous les résultats, et de l'ouvrir dans une fenêtre où le dessin prend la largeur de la fenêtre et la suit quand on la redimensionne, les boutons et notes du dessous passant à la ligne.
- **Source** : T96, T97, T104
- **Priorité** : doit
- **Critère d'acceptation** : épingle présente sur les deux dessins ; redimensionner la fenêtre redimensionne le dessin ; boutons à la ligne à largeur étroite.

### UI-019 — Volet droit
- **Exigence** : Woodcore doit montrer les modules : État du calcul ; Résultats (pression dynamique c<sub>h</sub>, q<sub>p</sub> et c<sub>red</sub> ; forces globales Q<sub>k,1–3</sub> max et min avec leur φ ; tableaux Murs, Toiture et Surfaces localisées en pression max et succion max q<sub>k</sub> [kN/m²], chacune avec son φ) ; Bâtiment (figure de la norme ou modèle 3D, avec le curseur φ) ; Figure 9 · c<sub>red</sub> interactive ; extraits épinglés ; Résultats 3D épinglés.
- **Source** : T98–T104, T143
- **Priorité** : doit
- **Critère d'acceptation** : `tab.service("modules")` liste ces modules ; glisser-déposer, réduire et fenêtre fonctionnent comme sur la neige (brique) ; chaque ligne de tableau porte son φ.

### UI-020 — En-têtes et casse
- **Exigence** : Woodcore doit donner aux colonnes les en-têtes « pression max », « succion max », « q<sub>k</sub> [kN/m²] » ; respecter la casse (Q une force en kN, q une charge par surface en kN/m², jamais « KN/M² ») ; n'avoir aucun titre en capitales.
- **Source** : T105, T106
- **Priorité** : doit
- **Critère d'acceptation** : test : aucune chaîne de la fenêtre du vent ne contient « KN/M² » ; aucun titre n'est en majuscules intégrales ; les unités sont kN et kN/m² dans les trois langues.

### UI-021 — Survols liés
- **Exigence** : Woodcore doit offrir, dans les deux sens et seulement quand le lien est vrai : le tableau des forces globales et Q<sub>k,1–3</sub> des résultats s'allument ensemble ; une ligne du volet droit allume sa surface sur le bâtiment et met en sur-évidence (cadre orange, par-dessus la colonne c<sub>pi</sub> déjà marquée) le c<sub>pe</sub> et le c<sub>pi</sub> qui ont donné sa valeur ; une cellule du détail par φ allume le c<sub>pe</sub> et le c<sub>pi</sub> qui l'ont donnée ; c<sub>red</sub> (b·h, d·h, d·b) n'allume rien dans les résultats.
- **Source** : T107–T111, T143
- **Priorité** : doit
- **Critère d'acceptation** : tests par paire de survols, sens aller et retour ; survol de c<sub>red</sub> : aucun élément des résultats allumé ; le cadre orange désigne les cellules des clés de REQ-005.

### UI-022 — Couleur de survol
- **Exigence** : Woodcore doit utiliser pour le survol un bleu lisible, en clair comme en sombre, et non le jaune safran.
- **Source** : T112
- **Priorité** : doit
- **Critère d'acceptation** : la couleur vient de `theme.json` (`hover`), contraste lisible en thème clair et sombre.

### UI-023 — Vue Affichage
- **Exigence** : Woodcore doit montrer au centre le fichier `Variable-loads/Wind/<id>.typ` compilé élément par élément (éléments masqués en pâle, non cliquables, sans cadre bleu, notes en bas de page) et à droite la commande `#include domain-file("wind-load", "WL-01")`, le niveau 1, 2 ou 3 du domaine, puis « Éléments du fichier » avec 0 1 2 3 par ligne et les arguments de `#var`, `#eq` et de la figure.
- **Source** : T113, T114, T145, T15
- **Priorité** : doit
- **Critère d'acceptation** : comme sur la neige (brique `display_view`) ; la commande affichée pour le cas WL-01 est celle indiquée.

### UI-024 — Tableaux comme éléments du fichier
- **Exigence** : Woodcore doit traiter les tableaux (forces globales, forces locales) comme des éléments du fichier : affichés ou non, avec ou sans titre et note ; un tableau n'a pas de niveau.
- **Source** : T115, T145
- **Priorité** : doit
- **Critère d'acceptation** : dans « Éléments du fichier », chaque tableau a « Afficher », « Titre », « Note » et aucune colonne 0 1 2 3.

### UI-025 — Figure du fichier comme élément
- **Exigence** : Woodcore doit offrir la figure comme un élément réglable (largeur, légende, label, « Afficher ») de la même façon pour la neige et pour le vent.
- **Source** : T118, T119, T147
- **Priorité** : doit
- **Critère d'acceptation** : la figure de la neige et celle du vent partagent le même réglage (brique) ; test de la brique.

### UI-026 — Bâtiments non encore relevés
- **Exigence** : Woodcore doit, pour un bâtiment dont la géométrie manquerait, montrer la figure de la norme à la place du modèle 3D (filet de sécurité).
- **Source** : T86 (déduit : la décision T169 livre les 37 bâtiments, ce cas ne doit plus se produire en livraison finale ; il reste utile en cours de développement et si une géométrie est refusée)
- **Priorité** : pourrait
- **Critère d'acceptation** : un bâtiment dont la géométrie est retirée dans un test montre la figure de la norme, sans erreur.
- **Amendé après la revue** : Utile pendant le développement seulement : à la mise en service, les 37 bâtiments sont dessinés (D-16, D-25).

### UI-027 — Mots
- **Exigence** : Woodcore doit fournir tous les mots de l'onglet en de, fr, en (prototype : fenêtre en fr, de, en), dans le `STRINGS` de l'onglet et les fichiers de mots de la brique, sans clé en double.
- **Source** : T27, T149
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_i18n.py` passe ; aucun texte visible en dur dans le code de l'onglet ou des briques.

## 5. Exigences d'architecture

### Base : l'onglet sur le type

### ARCH-001 — Onglet = paramètres sur CalcTab
- **Exigence** : Woodcore doit bâtir l'onglet Vent comme une classe de paramètres sur `calc_tab.CalcTab` (`KEY`, `MODULE`, `ID_PREFIX`, `LIST_KEY`, `EMPTY_KEY`…), sans copier un widget de l'onglet Neige ni écrire sa propre version d'une brique.
- **Source** : T6, T132, T160, T164
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_tab_overrides.py` et `tests/test_tab_services.py` passent ; la classe du vent ne définit que des paramètres ; aucun import de `snow_tab`.

### ARCH-002 — Briques d'abord, complétées pour tous
- **Exigence** : Woodcore doit lire d'abord ce que #95 a écrit (briques, contrat déclaratif, guide `docs/ui/building-a-tab.md`) ; toute brique qui manque ou ne suffit pas se complète dans la brique, avec son test, pour tous les onglets ; aucune version locale ; un manque bloquant se signale dans #95.
- **Source** : T7, T8, T152, T160
- **Priorité** : doit
- **Critère d'acceptation** : revue d'architecture : chaque brique prise par le vent est nommée et ce qu'il y ajoute est dit (T152) ; aucun code de brique dans le fichier de l'onglet Vent ; chaque ajout de brique a un test qui monte la brique sur `tests/fake_domain.py`, sans mot du domaine du vent.

### ARCH-003 — Contenu non-champ dans une section du formulaire
- **Exigence** : Woodcore doit permettre à une section du formulaire déclaratif de contenir autre chose que des champs (image, tableau, formule, 3D, liste déroulante sur la ligne d'un mot), déclaré par le domaine.
- **Source** : T166 (1), T58, T60–T69 (déduit : les sections 2 à 4 contiennent figures, tableaux, formules)
- **Priorité** : doit
- **Critère d'acceptation** : la brique `DeclaredForm` accepte un élément non-champ déclaré par le domaine factice ; la neige et le poids propre restent inchangés (leurs tests passent).
- **Amendé après la revue** : Réalisée par la déclaration : `contracts.Block(key, kind, …)` à genres fermés (`text`, `svg`, `heat_table`, `formula`, `model3d`, `row_select`), une section contenant des clés de champs ou de blocs ; les données d'un bloc viennent d'une fonction optionnelle du domaine `blocks(src, instance)`, stockée par `ctx.compute` dans `ctx.blocks` comme `ctx.drawing` ; les widgets des blocs dans un module partagé qui n'est pas un service (`calc_blocks.py`), que `DeclaredForm` et `Modules` instancient sans s'importer (revue, ARCH-RISK-001).

### ARCH-004 — Survols liés à clés générales
- **Exigence** : Woodcore doit offrir, dans la brique des survols liés, des clés générales : le domaine rend la provenance de chaque nombre (REQ-005) et la brique allume/met en sur-évidence les éléments qui portent ces clés, sans connaître le vent.
- **Source** : T14, T159, T166 (2)
- **Priorité** : doit
- **Critère d'acceptation** : test de la brique sur le domaine factice : un survol d'une clé allume les éléments de même clé ; aucun terme « cpe », « cpi », « φ » dans la brique.
- **Amendé après la revue** : Un signal `litKeys(lit, emphasis)` à côté de `lit`, un `ctx.hover_element(id)` qui lit `links(src, instance)` du domaine, des clés opaques portées par chaque widget ; la provenance calculée une seule fois par `wind_source.analysis(src)` (extrêmes, φ, colonnes, et lequel des deux signes d'une paire), lue par `build_instance` et par `blocks`/`links`, hors de `calculations.json` ; les corps des fenêtres ⧉ ne suivent pas les survols (revue, ARCH-RISK-002).

### ARCH-005 — Épingler n'importe quel module, ouvrir en fenêtre
- **Exigence** : Woodcore doit permettre, dans le volet de modules, d'épingler n'importe quel module (pas seulement un extrait) et de l'ouvrir dans une fenêtre qui suit le redimensionnement.
- **Source** : T13, T96, T97, T166 (3)
- **Priorité** : doit
- **Critère d'acceptation** : test de la brique : un module de test s'épingle sous les résultats et s'ouvre en fenêtre ; les extraits épinglés de la neige continuent d'agir comme avant.
- **Amendé après la revue** : `ModuleSpec` gagne `pinnable` et `fills_window` ; l'état de vue d'un module (rotation, zoom, direction) est tenu par le contexte et rendu à sa fabrique, chaque dessin ayant le sien (T87) ; `ModuleWindow` a un mode qui suit le redimensionnement ; `Modules.restore` reconnaît un module épinglé par le préfixe de son id (`x:` les extraits) (revue, ARCH-RISK-003).

### ARCH-006 — Tableau de coefficients coloré
- **Exigence** : Woodcore doit offrir un tableau de coefficients coloré (colonne marquée, légende, sur-évidence de cellules, cellules survolables) comme brique, la couleur d'une cellule suivant sa valeur et venant de `theme.json`.
- **Source** : T61, T66, T67, T166 (4)
- **Priorité** : doit
- **Critère d'acceptation** : test de la brique sur des valeurs de test ; palette lue de `theme.json` ; utilisable par un autre domaine sans modification.

### ARCH-007 — Modèle 3D en brique
- **Exigence** : Woodcore doit offrir le modèle 3D comme une brique réutilisable : un module Python sans Qt (projection, ordre des faces, faces vues, lettres, forces, cotes, plans de charge, rendu SVG) et son widget Qt (glisser, molette, boutons, curseur), à proposer dans #95 comme service ; le séisme ou les charges permanentes pourraient s'en servir.
- **Source** : T17, T25, T133, T155, T166 (5)
- **Priorité** : doit
- **Critère d'acceptation** : le module sans Qt n'importe pas Qt (test) ; ses tests couvrent T73–T82 ; le widget est monté par un test avec un modèle de test, sans mot du vent ; aucune nouvelle dépendance.
- **Amendé après la revue** : Un seul rendu : `calc/domains/model3d.py`, générique et sans Qt, construit une **scène** de primitives (polygone, ligne, flèche, texte), chacune avec un rôle, une clé de survol et un rôle de couleur (des jetons de `theme.json`, dans les deux schémas) ; `to_svg(scene)` pour les tests et un widget `QPainter` mince (≈ 80 lignes) qui la dessine, `pick(scene, x, y)` pour le survol ; aucune scène construite pour un widget caché ; les mots (« Face A », « Iso »…) viennent du consommateur. Le tri en profondeur par polygone suffit ; le rendu d'un bâtiment non convexe est approché, ce qu'un test par famille fixe (revue, ARCH-RISK-004).

### ARCH-008 — « Affichage » et générateur : tableaux sans niveau, figure au niveau 3, tableau transposé
- **Exigence** : Woodcore doit compléter la brique « Affichage » et les générateurs pour tous les onglets : des tableaux sans niveau à titre et note réglables ; une figure sans niveau écrite seulement au niveau 3 du domaine ; un tableau transposé coupé au-delà de douze surfaces. Selon la décision de l'ingénieur, la transposition reste, pour l'instant, une particularité du vent (le générateur du vent la déclare) et ne devient pas une option générale (déduit).
- **Source** : T115, T117, T123, T124, T158, T166 (6), T171
- **Priorité** : doit
- **Critère d'acceptation** : les tests de `unfold` (ou du générateur) couvrent un tableau sans niveau, la figure aux niveaux 1/2/3, le tableau transposé de 12 et 13 surfaces ; la neige continue de passer ses tests.
- **Amendé après la revue** : Voir REQ-014 et REQ-018 ; le code du vent quitte `unfold.py` (1401 lignes pour un plafond de 1500) pour un module à côté ; les tableaux deviennent des éléments d'« Affichage » (`table:<i>`, Afficher, Titre, Note) et le masquage, aujourd'hui propre à la figure, est généralisé (revue, ARCH-RISK-009).

### Domaine et données du vent

### ARCH-009 — Le propre du vent dans calc/domains/ et calc/norms/, sans Qt
- **Exigence** : Woodcore doit placer dans `calc/domains/` et `calc/norms/`, sans Qt, le calcul, les 37 bâtiments, le modèle 3D et ses vues, les tableaux colorés, le détail par φ, le choix des ouvertures et le générateur du fichier ; les valeurs de norme restent dans les JSON de `calc/norms/`.
- **Source** : T16, T23
- **Priorité** : doit
- **Critère d'acceptation** : aucun import Qt dans `calc/domains/` (test existant) ; aucune valeur de norme en dur dans le code de l'onglet ; l'onglet ne recalcule rien.

### ARCH-010 — Domaine du vent selon le contrat déclaratif
- **Exigence** : Woodcore doit faire fournir par `wind_source.py` ce que les services du type demandent : `declaration()` (choix du tableau en `select`, z « = h », sections et champs), `visible_fields(src)`, `messages(src)`, `results(instance)`, `chart(src)` (figure 9 interactive) ; `wind-load` dans `unfold.AUTO_REGENERATE` pour que le fichier suive son cas.
- **Source** : T164, T102, T9, T10
- **Priorité** : doit
- **Critère d'acceptation** : l'onglet se construit sans erreur de `NEEDS` ; enregistrer un cas réécrit `WL-xx.typ`.

### ARCH-011 — Géométrie des bâtiments : une structure à choisir
- **Exigence** : Woodcore doit ranger la géométrie des 37 bâtiments dans `calc/norms/` selon la structure choisie par la spec (voir Q-004), de sorte que le dessin suive les proportions du tableau, pas les dimensions saisies.
- **Source** : T154, T72
- **Priorité** : doit
- **Critère d'acceptation** : structure choisie documentée dans `docs/domain/loads.md` ; test de couverture des 37 tableaux (REQ-010).
- **Amendé après la revue** : Tranchée par D-23 : `calc/norms/sia261-2020-annexC-geometry.json`, des **données numériques** seulement (famille, proportions, pentes, faces nommées, zones en fractions de leur face, surfaces de référence, ancres des forces), un constructeur Python par **famille** — sept : prismes plats et à pans (31-41, 58-60b), sheds/pans coupés/aération (42-45), bâtiments ouverts (46-49), tribune (50), marquises et convoi (51-56), avant-toits (57a-d), formes courbes (63, 64). Un test refuse une surface du fichier `tabNN` absente de la géométrie, et inversement ; les libellés `ratio`/`roof` des tableaux ne sont pas recopiés (revue, ARCH-RISK-004).

### ARCH-012 — Extraits à côté des `norm_ref`
- **Exigence** : Woodcore doit tenir l'emplacement et le texte de chaque extrait à côté des `norm_ref` de `calc/norms/`, tenus au PDF par un test, et lire une édition nommée de `ExternalFiles/000-Normes/`.
- **Source** : T139, T164, CLAUDE.md (SIA traçables)
- **Priorité** : doit
- **Critère d'acceptation** : voir REQ-011.
- **Amendé après la revue** : Un fichier d'extraits dédié, `calc/norms/sia261-2020-wind-excerpts.json` (éditions FR et DE, chapitre 6, annexe C, annexe E avec sa carte), plutôt que 38 fichiers modifiés ; **deux boîtes** par tableau et par édition : le tableau entier (bulle) et le dessin seul (figure) ; `FIELD_NORM` va dans `declaration()` ; tenu au PDF par `tests/test_norm_excerpts.py` (revue, ARCH-RISK-011).

### ARCH-013 — Suppression de `load_tab.LoadTab`
- **Exigence** : Woodcore devrait supprimer `load_tab.LoadTab` quand plus aucun onglet n'en hérite, en gardant les mots `ld_` là où les onglets de charges les lisent.
- **Source** : T164 (issue #103, proposition de Claude, non de l'ingénieur ; déduit)
- **Priorité** : devrait
- **Critère d'acceptation** : aucun import de `load_tab` dans le code ; `tests/test_i18n.py` passe ; les onglets de charges gardent leurs mots.
- **Amendé après la revue** : Le nouvel onglet n'a pas de `TabSpec` avant la dernière version (D-25, D-31) : les tests le montent directement ; la mise en service est la ligne de `tab_registry.py` et la suppression de `LoadTab`. Les mots `ld_` quittent `load_tab.py` pour un module à eux avant la suppression, leurs cinq importeurs corrigés. `local_pressures` prend `c_d` sans valeur par défaut. Les fichiers `Variable-loads/Wind/*.typ` existants sont réécrits au premier enregistrement (`AUTO_REGENERATE`), à dire dans les « Nouveautés » (revue, ARCH-RISK-010).

### ARCH-014 — Figure découpée à l'enregistrement, stockée avec les exports du vent
- **Exigence** : Woodcore doit découper la figure à l'enregistrement via la bibliothèque de référence de la norme (décision de la neige #94 : découpe et impression sans limite autorisées), sans fenêtre à l'export, et stocker l'image avec les exports du vent (emplacement : Q-001) ; `wind-load` entre dans `project.FIGURE_KINDS`.
- **Source** : T156, T170, T173
- **Priorité** : doit
- **Critère d'acceptation** : après enregistrement, l'image est dans le dossier convenu ; `project.FIGURE_KINDS` contient `wind-load` ; la découpe se fait sans fenêtre (test).
- **Amendé après la revue** : Voir REQ-017 (D-28).

### ARCH-015 — Tests et documentation
- **Exigence** : Woodcore doit joindre ses tests (domaine, onglet via `tab.service(...)`, briques complétées) et sa documentation : `docs/ui/`, `docs/domain/loads.md`, `docs/decisions.md` (§13), `CHANGELOG.md`, page « Nouveautés » fr/de/en, ligne dans `docs/conventions/testing-catalogue*.md`.
- **Source** : T150, T149, CLAUDE.md
- **Priorité** : doit
- **Critère d'acceptation** : voir §11.

## 6. Contraintes

- **CON-001** — Le prototype (`docs/requirements/prototypes/2026-10-23-onglet-vent/`, commit `8e88677`) est la référence, mais l'issue l'emporte là où les deux diffèrent. Source : T2, T18–T20. (La copie du dossier se reprend avec la commande de T20.) — **Amendé après la revue** : le dossier du prototype n'est pas dans le dépôt (branche non fusionnée) ; il est extrait du commit `8e88677` par `git archive` (jamais `git checkout --`, CLAUDE.md) et commité avant l'implémentation, et ses valeurs de `compute()` deviennent des valeurs d'or dans `tests/` (revue, ARCH-RISK-017).
- **CON-002** — Le choix des ouvertures entre dans la source du cas : nouvelle version de `schemas/wind-source`, avec `schema_version` ; l'export ne donne plus que le cas choisi. Source : T153, T136. (Voir Q-005 pour les cas déjà enregistrés.)
- **CON-003** — Toute valeur de norme est lue de `calc/norms/*.json` d'une édition nommée de `ExternalFiles/000-Normes/` (SIA 261:2020, ch. 6, annexes C et E) ; chaque étape cite sa clause. Source : T21, T22, CLAUDE.md.
- **CON-004** — Les mots en de, fr et en (fenêtre, rapport) ; la langue de la norme suit la fenêtre, allemand par défaut. Source : T53, T149.
- **CON-005** — Dépendances : le modèle 3D n'introduit aucune nouvelle dépendance (≈ 350 lignes de `QPainter`). Source : T155. — **Amendé après la revue** : un widget `QPainter` mince sur la scène de `model3d` (ARCH-007), sans nouvelle dépendance.
- **CON-006** — L'ingénieur autorise sans limite à découper la norme (PDF de la SIA) et à l'imprimer. Source : T156.
- **CON-007** — Le fichier du cas est `Variable-loads/Wind/<id>.typ` (`project.DOMAIN_FOLDERS`). Source : T113, T173.
- **CON-008** — Une valeur de norme ne se recopie jamais à la main : texte et emplacement des extraits sont tenus au PDF par un test. Source : T21, T164, principes (« une source de vérité »).
- **CON-009** — Les travaux de l'issue passent par `/big-feature` (spec, revue, une approbation). Source : T151.

## 7. Décisions prises

Décisions de l'ingénieur dans l'issue (à reporter dans `docs/decisions.md`) :

- **D-1** — « L'onglet Vent est le deuxième onglet de calcul après la neige. Il doit être bâti sur les types d'onglets et les briques de fonctionnalités de l'issue #95 » ; une brique qui manque se complète dans la brique « pour tous les onglets. On ne fait pas de version locale. » (T6, T8). Prix : le vent attend, ou complète, des briques de #95.
- **D-2** — Le widget du modèle 3D « devient lui aussi une brique » (T17).
- **D-3** — « Une seule façon de le voir : un modèle que l'on tourne à la souris. Les vues fixes et la vue « pression par φ » ont été essayées puis écartées. » (T71).
- **D-4** — Le modèle 3D suit « les proportions du tableau et non celles saisies » ; le zoom est toujours centré, à échelle fixe (T72, T75, T76). Prix : on ne peut pas déplacer la vue.
- **D-5** — Le détail par φ est « toujours affiché, sans bouton pour le replier » (T67). Prix : la section 4 est longue.
- **D-6** — Les tableaux Murs, Toiture et Surfaces localisées sont retirés du centre, au volet droit (T70).
- **D-7** — Les charges de m, n, o sont dessinées « en plus de celle de leur face : on garde les deux » (T94).
- **D-8** — Seuil orange des proportions saisies : « plus de 1,5 fois loin de celles du tableau (décision de l'ingénieur) » (T46).
- **D-9** — Le survol est un bleu lisible, pas le jaune safran (T112).
- **D-10** — Les survols liés sont « vrais seulement » ; c<sub>red</sub> n'allume rien dans les résultats (T107, T111).
- **D-11** — Les Résultats 3D restent dans la fenêtre ; le rapport n'imprime aucun 3D (T120).
- **D-12** — La figure du fichier est celle de la norme en 2D, sans niveau, écrite au niveau 3 seulement ; « Afficher » garde le choix (T116–T118).
- **D-13** — Un tableau n'a pas de niveau (T115).
- **D-14** — Forces locales du fichier : seul le cas d'ouvertures choisi, tableau transposé, coupé au-delà de douze surfaces (T122–T124). Les forces globales avec nombres (T121).
- **D-15** — c<sub>d</sub> entre dans les pressions locales selon (17) (T125).
- **D-16** — Part E, point 1 (la contradiction sur les 37 bâtiments, tranchée) : « Dessine tous les bâtiments et affiche également l'onglet qui montre la figure de la norme. Donc tu livres tous les bâtiments et tu livres la norme également pour tous les bâtiments. » (T169). Prix accepté : le relevé de 31 bâtiments supplémentaires fait partie de la livraison, non d'une suite.
- **D-17** — Part E, point 2 (figure de la norme dans le rapport) : « il faut découper à l'enregistrement et donc le découpage se trouve dans le dossier variable loads wind. Ici se trouvera les exports .typ ainsi que les découpages. » (T170). Précision à confirmer : voir Q-001.
- **D-18** — Part E, point 3 (tableau transposé) : « pour l'instant c'est une particularité du vent. Ce qui est le plus important, c'est que les tableaux soient trapus plutôt que hauts. [...] ce n'est pas tout à fait une particularité du vent, mais ici, particulièrement pour le vent, c'était nécessaire de transposer le tableau. » (T171, T172). Interprétation : l'objectif général est le tableau trapu ; la transposition est, pour l'instant, une mise en œuvre propre au vent, non une option générale des tableaux de domaine. Prix : un autre domaine à tableau haut devra demander sa propre mise en forme.
- **D-19** (déduit de D-16 et T167) — Le découpage en versions de la livraison (T167) est une proposition de Claude, non encore approuvée ; voir Q-006.

- **D-20** — La figure de la norme découpée va dans `Variable-loads/Wind/Exports/Figures/`, la règle des figures de domaine (`project.figures_folder`) ; `wind-load` entre dans `project.FIGURE_KINDS`. (Q-001, l'ingénieur)
- **D-21** — La bibliothèque des normes absente du poste : l'enregistrement réussit, un message orange le dit, le `.typ` n'écrit pas la figure, une image déjà découpée est gardée. (Q-002, principe de CLAUDE.md)
- **D-22** *(remplacée par D-29)* — Le niveau du domaine changé après l'écriture : le fichier suit le niveau à chaque réécriture ; l'image découpée reste sur le disque ; « Afficher », largeur, légende et label sont gardés pour un retour au niveau 3. (Q-003)
- **D-23** — La géométrie des 37 bâtiments dans une table à part, `calc/norms/sia261-2020-annexC-geometry.json`, indexée par numéro de tableau. (Q-004, choix laissé à la spec par T154)
- **D-24** — Un cas existant sans choix d'ouvertures est lu avec « réparties de façon homogène », et un message orange le dit jusqu'à ce que l'ingénieur choisisse. (Q-005, l'ingénieur)
- **D-25** — Livraison par étapes, chacune une version publiable ; le nouvel onglet Vent ne remplace l'ancien que lorsque les 37 bâtiments sont dessinés (« Par étapes, onglet à la fin », l'ingénieur ; T85). (Q-006)
- **D-26** — Le réglage de la figure (largeur, légende, label, « Afficher ») est commun à toutes les figures de domaine ; la règle « écrite au niveau 3 seulement » est celle du vent, la neige gardant la sienne. (Q-007, l'ingénieur)
- **D-27** — La figure de la norme découpée suit la langue du rapport, l'allemand pour un rapport anglais ; la légende de Woodcore est dans la langue du rapport. (Q-008, règle des extraits T53)

- **D-28** — La figure de la norme est découpée **dans l'export**, qui tourne à chaque enregistrement : `annex.crop` (pypdf), vectorielle, sans Qt, la même avec ou sans fenêtre, rangée dans `Variable-loads/Wind/Exports/Figures/` (D-20). Pour l'ingénieur rien ne change : elle est faite à l'enregistrement, au même endroit. Prix : le schéma `calculations` passe en 1.9 si l'entrée de figure porte ses éditions. (Q-009)
- **D-29** — La ligne de la figure est toujours écrite, avec un niveau 3 que Typst résout : imprimée au niveau 3 seulement, en « auto » comme dans les variantes, ses réglages gardés sur la ligne. **Remplace D-22.** Prix : une option de niveau sur la ligne `#figure`, que la lecture d'« Affichage » doit connaître. (Q-010)
- **D-30** — Une spec, cinq versions publiables, chacune vérifiée : (1) domaine et fichier ; (2) briques complétées ; (3) brique 3D et bâtiments, famille par famille ; (4) extraits de la norme ; (5) mise en service. (Q-011)
- **D-31** — Le nouvel onglet n'a pas de `TabSpec` avant la cinquième version : les versions 1 à 4 n'ajoutent aucun onglet visible, l'ancien Vent reste en service et compatible avec le domaine (D-25, revue ARCH-RISK-010).
- **D-32** — Les réserves non bloquantes de la revue sont reprises dans les exigences (« Amendé après la revue ») : la géométrie par familles (ARCH-011), le rendu unique par scène (ARCH-007), les blocs de section (ARCH-003), les survols à clés (ARCH-004), l'épinglage général (ARCH-005), les extraits dans un fichier dédié à deux boîtes (ARCH-012), les blocs de douze surfaces au plus (REQ-014), les ouvertures des tableaux sans choix (REQ-006), le prototype extrait du commit et des valeurs d'or (CON-001).
- **D-33** — Le chemin du classeur pour les charges disparaîtra : « il n'y aura plus jamais de feuille excel à lire pour le vent, ni pour la neige, ni pour les charges permanentes » (l'ingénieur, 24.10.2026, à la question de l'écart G86). La cellule G86 n'est donc pas lue ; une feuille WL-* imprime « rep » jusqu'au retrait du chemin, qui est un travail à part.
- **D-34** — Le volet de droite se déclare : `Declaration.modules = ((id, clés de blocs), …)`, vide par défaut (la neige et le poids propre ne changent pas). L'id « results » met ses blocs sous les valeurs de « Résultats », à la place des tableaux de l'instance ; un autre id fait un module permanent titré `<préfixe>m_<id>`, déplaçable, repliable, en fenêtre. Les blocs sont ceux des sections (contrat `Block`), leurs survols par clés compris. Le vent y met les forces globales Q<sub>k</sub> max et min à leur φ, les tableaux Murs, Toiture, Points de mesure et Surfaces localisées en pression max et succion max à leur φ, et le module « Bâtiment ». (UI-019, « Declaration.modules », l'ingénieur, 24.10.2026 ; ni crochets propres au domaine, ni tableaux « écran seulement » dans l'export)
- **D-35** — La bascule « Norme / Modèle 3D » est un genre de bloc général, `views` : `Block.children` nomme les blocs qu'il montre l'un à la fois sous un bouton segmenté, la vue choisie gardée par l'onglet (`ctx.view_state`). Le même bloc sert en section 2 et dans le module « Bâtiment ». Les faits du tableau disent aussi son titre, dans la langue de l'édition, et la toiture. (UI-005, « Bloc vues général », l'ingénieur, 24.10.2026)
- **D-36** — Une fenêtre ⧉ ou un module épinglé colore ce qu'un survol allume, mais sa vue ne bouge pas : ni rotation, ni zoom, ni défilement. (Q4 de la fin de nuit, l'ingénieur, 24.10.2026)
- **D-37** — Réponses de l'ingénieur du 24.10.2026 aux questions de la nuit : le seuil 1,5 reste (D-8) ; un bâtiment dessine toutes les lettres de sa figure de la norme, et seulement elles (Q8, la tribune du tableau 50 à contrôler) ; la figure découpée reste un PDF vectoriel, l'export devant surtout rester rapide (Q18 : la découpe est faite une fois par édition et gardée) ; la ligne oblique de c<sub>red</sub> est nommée « oblique » (Q23) ; les autres écarts de la nuit acceptés tels quels.

## 8. Hors périmètre

- Les autres tableaux de domaine (neige, poids propre) ne sont pas transposés ni modifiés pour être « trapus » : T172 énonce l'objectif général, mais seule la mise en forme du vent est demandée (déduit de T171).
- Les autres onglets (Séisme, Charges utiles, vérifications de membres) ne sont pas portés sur le type par cette spec ; le 3D en brique leur est seulement ouvert (T17).
- Les vues fixes et la vue « pression par φ » du modèle 3D (essayées, écartées : T71).
- Le rapport n'imprime aucun 3D (T120).
- Les versions successives du prototype hors dépôt (T28) : informatives.
- Publication (installateur, site, push) : attend la parole de l'ingénieur (CLAUDE.md).
- Modifier un projet de l'ingénieur hors `tests/projet-exemple/` (CLAUDE.md).
- La proposition de fermer #103 comme couverte (T165) est une opération de suivi, non une exigence logicielle.

## 9. Idées non retenues comme exigences

- T78 « Exemple : en Face A sur le tableau 32… » : illustration, reprise comme cas de test d'UI-010, non comme exigence propre.
- T82 « sur une forme ronde, la flèche resterait perpendiculaire à la surface » : au conditionnel ; repris en « devrait » dans UI-012 faute de forme ronde certaine dans les 37 tableaux (à vérifier au relevé).
- T155 « environ 350 lignes de `QPainter` », « par exemple `wind_model3d.py` » : ordre de grandeur et nom d'exemple, non des exigences.
- T164 (corps de #103) : proposition de Claude, reprise en ARCH-010 et ARCH-013 sans valeur de décision de l'ingénieur pour ARCH-013.
- T165, T167 : propositions de Claude ; voir Q-006.
- T28 : liens vers les versions du prototype, informatifs.

## 10. Questions

### Q-001 — Où va la figure découpée de la norme ?
- **Pourquoi elle compte** : l'ingénieur dit (T170) que le découpage se trouve dans le dossier « variable loads wind », avec les exports `.typ`, et demande « Redis-moi si je me trompe ». D'après le code (T173), le `.typ` est dans `Variable-loads/Wind/<id>.typ`, mais les figures d'un domaine vont dans `<dossier>/Exports/Figures/` (comme `Permanent-loads/Exports/Figures/`). Le chemin décide du test d'ARCH-014 et de ce que le `.typ` référence.
- **Options** : A (recommandée) `Variable-loads/Wind/Exports/Figures/` : même règle que le poids propre, `project.figures_folder` ne change pas, `wind-load` s'ajoute à `FIGURE_KINDS`. B `Variable-loads/Wind/` directement à côté du `.typ` : plus proche de ce que dit l'ingénieur mais crée une exception à `figures_folder`.
- **Réponse** : A, `Variable-loads/Wind/Exports/Figures/` (l'ingénieur, 23.10.2026) → D-20.

### Q-002 — Que fait Woodcore quand la bibliothèque des normes manque sur le poste ?
- **Pourquoi elle compte** : la découpe se fait à l'enregistrement dans le PDF de la SIA (T156) ; sans PDF la figure ne peut pas être produite. Une entrée manquante avertit, un fichier malformé arrête (CLAUDE.md).
- **Options** : A (recommandée) l'enregistrement réussit ; avertissement (orange, avec la raison) ; la figure n'est pas écrite dans le `.typ` et le rapport compile sans ; une image déjà découpée est conservée. B enregistrement refusé : plus strict, mais bloque un poste sans la bibliothèque.
- **Réponse** : A, résolue par le principe de CLAUDE.md « une entrée manquante avertit, un fichier malformé arrête » : l'enregistrement réussit, un message orange dit pourquoi la figure manque, le `.typ` ne l'écrit pas, une image déjà découpée est gardée → D-21.

### Q-003 — Que devient la figure quand le niveau du domaine change après l'écriture ?
- **Pourquoi elle compte** : T157 demande de le dire ; le générateur décide à l'écriture (REQ-018).
- **Options** : A (recommandée) le fichier suit le niveau à chaque réécriture (`AUTO_REGENERATE`) : de 3 à 1 ou 2 la figure disparaît du `.typ`, l'image découpée reste sur le disque, la case « Afficher » et la largeur/légende/label sont gardés pour le retour au niveau 3 ; de 1 ou 2 à 3 la figure est écrite et l'image découpée. B supprimer aussi l'image au retour à 1 ou 2 : moins de fichiers qui vieillissent, mais perd le réglage.
- **Réponse** : A, résolue par la règle des fichiers de calcul (`AUTO_REGENERATE`, D-21 de la spec 2026-10-23-onglets-types-et-services) : le fichier suit le niveau à chaque réécriture, l'image reste sur le disque, les réglages de la figure sont gardés → D-22.

### Q-004 — Une table par tableau ou une seule table pour les 37 géométries ?
- **Pourquoi elle compte** : T154 laisse choisir à la spec ; touche `calc/norms/` et ses tests.
- **Options** : A (recommandée) une table à part `calc/norms/sia261-2020-annexC-geometry.json` pour les 37, indexée par numéro de tableau : le relevé d'un bâtiment est un diff isolé, les coefficients ne sont pas mélangés à la géométrie. B un champ `geometry` dans chaque `sia261-2020-tabNN-wind.json` : une seule lecture par tableau, mais fichiers plus longs et géométrie répétée pour 59a/59b.
- **Réponse** : A, l'issue laissant le choix à la spec (T154) : une table à part `calc/norms/sia261-2020-annexC-geometry.json` pour les 37, le relevé d'un bâtiment étant un diff isolé des coefficients → D-23.

### Q-005 — Que devient une source de cas existante sans choix d'ouvertures ?
- **Pourquoi elle compte** : le choix entre dans la source (CON-002) ; les cas déjà écrits en 0.122 n'ont pas ce champ ; un fichier malformé arrête, une entrée absente avertit (CLAUDE.md).
- **Options** : A (recommandée) migration par `stamp_version` : le champ est ajouté avec le cas « réparties de façon homogène » et un message orange le dit ; B refuser la lecture : ne laisse aucune valeur implicite mais casse les cas existants.
- **Réponse** : A, « Réparties, et le dire » (l'ingénieur, 23.10.2026) → D-24.

### Q-006 — Découpage de la livraison en versions
- **Pourquoi elle compte** : D (T167) propose : (1) domaine et fichier, (2) briques complétées et onglet sans 3D, (3) brique 3D avec 6 bâtiments, (4) les 31 autres bâtiments. L'ingénieur a répondu « tu livres tous les bâtiments » (T169) sans dire si c'est en une seule version. Cela change le plan (§14) et ce qui est visible au fil des versions.
- **Options** : A (recommandée) le découpage proposé, la mise en service de l'onglet Vent (remplaçant l'ancien) n'ayant lieu qu'à la dernière version, quand les 37 bâtiments sont dessinés (cohérent avec T85 « dessinés avant la mise en service »). B une seule livraison. C livrer l'onglet à la version 3 avec le repli sur la figure de la norme (UI-026) pour les 31 restants : contredit T85 et T169.
- **Réponse** : A, « Par étapes, onglet à la fin » (l'ingénieur, 23.10.2026) : plusieurs versions publiables, le nouvel onglet ne remplace l'ancien que lorsque les 37 bâtiments sont dessinés → D-25.

### Q-007 — La règle « figure au niveau 3 seulement » vaut-elle aussi pour la neige ?
- **Pourquoi elle compte** : T119 dit que la figure « se règle partout de la même façon, pour la neige comme pour le vent » ; le réglage (largeur, légende, label, « Afficher ») est donc partagé, mais T117 ne dit pas si le niveau 3 conditionne aussi la figure de la neige (qui a peut-être son propre comportement depuis #94). Cela change la brique (ARCH-008) et les tests de la neige.
- **Options** : A (recommandée) seul le réglage est partagé ; la neige garde sa règle d'écriture actuelle jusqu'à demande contraire ; B la règle du niveau 3 devient commune à toutes les figures de domaine.
- **Réponse** : A, « Réglage commun seulement » (l'ingénieur, 23.10.2026) → D-26.

### Q-008 — Langue de l'image découpée pour le rapport
- **Pourquoi elle compte** : la norme n'existe qu'en FR et DE (T53). Pour un fichier en anglais, la figure découpée vient de laquelle ? Le fichier français ne doit garder aucun mot allemand (T126), mais l'image est un extrait de la norme.
- **Options** : A (recommandée) la figure suit la langue du rapport, avec l'allemand pour l'anglais (règle de T53) ; la légende de Woodcore est dans la langue du rapport ; B toujours l'allemand.
- **Réponse** : A, résolue par la règle déjà en vigueur des extraits (T53) : la langue du rapport, l'allemand pour un rapport anglais ; la légende de Woodcore dans la langue du rapport → D-27.

### Q-009 — Où découper la figure de la norme : dans l'export ou dans la fenêtre ? (revue, ARCH-RISK-005, bloquant)
- **Pourquoi elle compte** : découpée par la fenêtre (QtPdf), l'image est supprimée par l'export suivant, qui nettoie ce qu'il n'a pas écrit, et un export sans fenêtre n'a pas de figure ; or l'export tourne à chaque enregistrement.
- **Options** : A (recommandée) dans l'export, par `annex.crop` (pypdf) ; B dans la fenêtre, par QtPdf.
- **Réponse** : A, « Dans l'export » (l'ingénieur, 23.10.2026) → D-28.

### Q-010 — Comment la figure n'est-elle imprimée qu'au niveau 3 ? (revue, ARCH-RISK-006, bloquant)
- **Pourquoi elle compte** : le niveau est résolu par Typst à la compilation (« auto », les variantes) ; les réglages de la figure sont sur sa ligne, que la retirer perdrait.
- **Options** : A (recommandée) la ligne toujours écrite, avec un niveau 3 que Typst résout ; B Python écrit ou retire la ligne selon l'en-tête, les réglages gardés à part.
- **Réponse** : A, « Typst la montre au niveau 3 » (l'ingénieur, 23.10.2026) → D-29, remplace D-22.

### Q-011 — Une spec en cinq versions, ou quatre issues ? (revue, §4)
- **Pourquoi elle compte** : le travail est très gros (une vingtaine d'exigences de domaine, six briques, sept familles de géométrie, 37 × 2 extraits).
- **Options** : A (recommandée) cette spec, un plan en cinq versions publiables, chacune vérifiée ; B quatre issues et quatre specs.
- **Réponse** : A, « Une spec, cinq versions » (l'ingénieur, 23.10.2026) → D-30.

## 11. Critères d'acceptation

- [x] REQ-001 — q<sub>p</sub>, c<sub>h</sub>, z minimal et profil de catégorie IV vérifiés par tests de domaine.
- [x] REQ-002 — Q<sub>k,1–3</sub> par φ de la halle du tableau 36 égaux au prototype ; c<sub>red</sub> selon 6.3.3.
- [x] REQ-003 — test à c<sub>d</sub> ≠ 1 ; ±0,1 compte deux signes ; pas de c<sub>red</sub>.
- [x] REQ-004 — extrêmes avec φ, c<sub>pe</sub>, c<sub>pi</sub> ; détail par surface et par φ.
- [x] REQ-005 — clés de provenance rendues par le domaine.
- [x] REQ-006 — cas d'ouvertures choisi et enregistré dans la source.
- [x] REQ-007 — m, n, o à part.
- [x] REQ-008 — note ĉ<sub>pe</sub> · q<sub>p</sub>.
- [x] REQ-009 — un test par message rouge, orange et vert, avec son champ.
- [x] REQ-010 — géométrie des 37 bâtiments présente et testée.
- [x] REQ-011 — extraits tenus au PDF par édition FR et DE.
- [x] REQ-012 — figure de la norme pour les 37 tableaux.
- [x] REQ-013 — forces globales en nombres, Q<sub>k</sub> [kN], lignes q<sub>k</sub> par m² gardées.
- [x] REQ-014 — forces locales du cas choisi, transposées, coupées au-delà de douze.
- [x] REQ-015 — c<sub>d</sub> dans les nombres du fichier.
- [x] REQ-016 — aucun mot allemand dans le fichier français.
- [x] REQ-017 — figure découpée à l'enregistrement, au dossier convenu.
- [x] REQ-018 — figure écrite au niveau 3 seulement, réglable.
- [x] REQ-019 — aucun 3D imprimé.
- [x] REQ-020 — tableaux trapus.
- [x] Défauts de la 0.122 (T127 à T131) — chacun couvert par un test, voir REQ-013, 014, 003, 016.
- [x] UI-001 à UI-027 — chacun vérifié par le critère de sa fiche ; i18n de, fr, en.
- [x] ARCH-001 à ARCH-015 — chacun vérifié ; la neige et le poids propre gardent leurs tests verts après chaque brique complétée.
- [x] Documentation : sections de `docs/` mises à jour (`docs/ui/`, `docs/domain/loads.md`, `docs/decisions.md`), entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en, `///` + exemples + traductions pour toute commande Typst.
- [x] Tests : fichiers `tests/test_*.py` ajoutés ou étendus (domaine, onglet, briques, module 3D, générateur), ligne dans le catalogue des tests, et passent (suite complète à la fin).

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1 | capturé (contexte) |
| T2 | CON-001 | capturé |
| T3, T4, T5 | UI-001 | capturé |
| T6 | ARCH-001, D-1 | capturé |
| T7 | ARCH-002 | capturé |
| T8 | ARCH-002, D-1 | capturé |
| T9 | ARCH-001, ARCH-010 | capturé |
| T10 | ARCH-010, ARCH-003 | capturé |
| T11 | UI-002 | capturé |
| T12 | UI-002 | capturé |
| T13 | UI-019, ARCH-005 | capturé |
| T14 | UI-021, ARCH-004 | capturé |
| T15 | UI-023 | capturé |
| T16 | ARCH-009 | capturé |
| T17 | ARCH-007, D-2 | capturé |
| T18, T19, T20 | CON-001 | capturé |
| T21 | REQ-011, CON-003, CON-008 | capturé |
| T22 | REQ-011 | capturé |
| T23 | REQ-001, REQ-002, ARCH-009 | capturé |
| T24 | REQ-010 | capturé |
| T25 | ARCH-007 | capturé |
| T26 | UI-014 | capturé (reprise de la logique des Résultats 3D) |
| T27 | UI-027 | capturé |
| T28 | — | information (§8, §9) |
| T29, T30, T31 | REQ-001, UI-004 | capturé |
| T32, T33, T34, T35 | REQ-002 | capturé |
| T36 | REQ-003 | capturé |
| T37, T38, T39 | REQ-003 | capturé |
| T40 | REQ-004 | capturé |
| T41 | REQ-006 | capturé |
| T42 | REQ-007 | capturé |
| T43 | REQ-008 | capturé |
| T44, T45, T46, T47 | REQ-009 | capturé |
| T48 | REQ-009 (clic mène au champ qui clignote) | capturé |
| T49–T54 | UI-002 | capturé |
| T55 | UI-003 | capturé |
| T56 | UI-004 | capturé |
| T57, T58, T59 | UI-005 | capturé |
| T60–T64 | UI-006 | capturé |
| T65–T69 | UI-007 | capturé |
| T70 | UI-007, UI-019, D-6 | capturé |
| T71, T72 | UI-008, D-3, D-4 | capturé |
| T73, T74, T75, T76 | UI-009 | capturé |
| T77 | UI-010 | capturé |
| T78 | UI-010 (cas de test), §9 | idée/illustration (§9) |
| T79 | UI-011 | capturé |
| T80, T81 | UI-012 | capturé |
| T82 | UI-012 (devrait), §9 | conditionnel (§9) |
| T83, T84 | UI-013 | capturé |
| T85 | REQ-010, D-16 | capturé |
| T86 | UI-026 | capturé (repli, déduit) |
| T87, T88, T89 | UI-014 | capturé |
| T90 | UI-015 | capturé |
| T91, T92, T93, T94 | UI-016, D-7 | capturé |
| T95 | UI-017 | capturé |
| T96, T97 | UI-018, ARCH-005 | capturé |
| T98–T104 | UI-019 | capturé |
| T105, T106 | UI-020 | capturé |
| T107–T111 | UI-021, D-10 | capturé |
| T112 | UI-022, D-9 | capturé |
| T113, T114 | UI-023 | capturé |
| T115 | UI-024, ARCH-008, D-13 | capturé |
| T116 | REQ-017, REQ-019, UI-025, D-12 | capturé |
| T117, T118 | REQ-018, UI-025, ARCH-008, D-12 | capturé |
| T119 | UI-025, Q-007 | capturé / question |
| T120 | REQ-019, D-11 | capturé |
| T121 | REQ-013 | capturé |
| T122, T123, T124 | REQ-014, ARCH-008, D-14 | capturé |
| T125 | REQ-003, REQ-015, D-15 | capturé |
| T126 | REQ-016 | capturé |
| T127, T128 | REQ-013 | capturé |
| T129 | REQ-014 | capturé |
| T130 | REQ-016 | capturé |
| T131 | REQ-003 | capturé |
| T132 | ARCH-001, ARCH-002 | capturé |
| T133 | ARCH-007 | capturé |
| T134 | REQ-003 | capturé |
| T135 | REQ-004 | capturé |
| T136 | REQ-006, CON-002 | capturé |
| T137 | REQ-009 | capturé |
| T138 | REQ-010 | capturé |
| T139 | REQ-011, ARCH-012 | capturé |
| T140 | UI-003, UI-007 | capturé |
| T141 | UI-008 à UI-013 | capturé |
| T142 | UI-014 à UI-018 | capturé |
| T143 | UI-019, UI-021 | capturé |
| T144 | UI-002 | capturé |
| T145 | UI-023, UI-024 | capturé |
| T146 | REQ-013, REQ-014 | capturé |
| T147 | REQ-018, UI-025 | capturé |
| T148 | REQ-016 | capturé |
| T149 | UI-027 (et de, fr, en pour tout UI) | capturé |
| T150 | ARCH-015, §11 | capturé |
| T151 | CON-009 | capturé |
| T152 | ARCH-002 | capturé |
| T153 | CON-002, REQ-006, Q-005 | capturé / question |
| T154 | ARCH-011, Q-004 | question |
| T155 | ARCH-007, CON-005 | capturé |
| T156 | REQ-017, ARCH-014, CON-006, Q-002 | capturé / question |
| T157 | REQ-018, Q-003 | capturé / question |
| T158 | ARCH-008, D-18 | tranché par T171, T172 |
| T159 | REQ-005, ARCH-004 | capturé |
| T160 | ARCH-001, ARCH-002 | capturé |
| T161 | UI-002 | capturé |
| T162 | UI-002 | capturé |
| T163 | §1, D-1 | contexte |
| T164 | ARCH-010, ARCH-013, REQ-011 | capturé (proposition de Claude pour la suppression de `LoadTab`) |
| T165 | §8 | hors périmètre (suivi) |
| T166 | ARCH-003 à ARCH-008 | capturé (proposition de Claude, reprise) |
| T167 | Q-006, D-19 | question |
| T168 | D-16, D-17, D-18 | tranché par la partie E |
| T169 | REQ-010, REQ-012, UI-026, D-16 | capturé / décision |
| T170 | REQ-017, ARCH-014, D-17, Q-001 | capturé / question |
| T171 | ARCH-008, D-18 | décision |
| T172 | REQ-020, D-18, §8 | décision (interprétée) |
| T173 | CON-007, ARCH-014, Q-001 | information vérifiée |

### Points de la source non résolus

Aucun : Q-001 à Q-008 sont tranchées (D-20 à D-27).

## 13. Revue d'architecture

Revue du 23.10.2026 par l'agent `architecture-reviewer`, sur le code à 2b4f130 (les briques de #95 et le vent d'aujourd'hui) et le prototype.

**Ce que les briques donnent** : `TabHost`, `CalcTab` (le vent sera `WindTab(CalcTab)`), la liste, l'identité, `DeclaredForm` (accordéon, ⓘ, résumés), les bulles et le lecteur, `Modules` (état, résultats et `tables_html`, graphique de la figure 9, extraits, ⧉), « Affichage » et `set_figure`, `AUTO_REGENERATE`, le précédent `swap` du poids propre. **Ce qui manque** : une section ne contient que des champs ; les survols sont au niveau des variables ; l'épinglage et `restore` ne connaissent que les extraits, et la fenêtre ⧉ ne suit pas sa taille ; les tableaux ne sont pas des éléments d'« Affichage » ; un seul fichier de norme par déclaration, et les fichiers du vent n'ont pas de bloc d'extraits ; `excerpt_image` dépend de Qt. **Le vent d'aujourd'hui** : `local_pressures` sans `c_d` (T131 confirmé), des noms de variables dans le tableau des forces (T127 confirmé, `unfold._table_lines`), des `qk_*` en kN/m², des mots allemands dans l'instance, aucun `openings`. **À réutiliser** : `annex.crop` (pypdf) pour la découpe, le patron des figures de `snow_source`, les versions de schéma de `snow_source`, `excerpts.py`, `fake_domain`, `Hover`.

| Risque | Gravité | Ce qui est fait |
|---|---|---|
| ARCH-RISK-001 — contenu non-champ dans une section | important | ARCH-003 amendée : `contracts.Block`, `blocks(src, instance)`, `ctx.blocks`, widgets partagés hors services |
| ARCH-RISK-002 — survols à clés générales, provenance | important | ARCH-004 amendée : `litKeys`, `links`, `analysis(src)` une fois |
| ARCH-RISK-003 — épingler tout module, fenêtre qui suit | important | ARCH-005 amendée |
| ARCH-RISK-004 — deux rendus pour un dessin ; les 37 bâtiments (7 familles, non convexes, courbes) | bloquant pour le chiffrage | ARCH-007 et ARCH-011 amendées : une scène, deux consommateurs minces ; géométrie numérique par famille |
| ARCH-RISK-005 — découpe QtPdf à l'enregistrement supprimée par l'export, dépendante de la fenêtre | **bloquant** | Q-009 → D-28 : découpe dans l'export par `annex.crop` |
| ARCH-RISK-006 — « niveau 3 seulement » décidé par Python et réglages perdus | **bloquant** | Q-010 → D-29 : niveau résolu par Typst |
| ARCH-RISK-007 — schéma des ouvertures, tableaux sans choix | important | REQ-006 amendée : schéma 1.2, champ caché pour 46-50, 57, 63, 64 |
| ARCH-RISK-008 — Q<sub>k</sub> en kN, A<sub>ref</sub>, noms publics | important | REQ-002 amendée : additif, table fermée des surfaces |
| ARCH-RISK-009 — tableau transposé et coupé ; `unfold.py` à 1401/1500 lignes ; tableaux éléments ; fichiers réécrits | important | REQ-014, ARCH-008, ARCH-013 amendées |
| ARCH-RISK-010 — deux onglets Vent, fin de `LoadTab`, mots `ld_` | important | D-31, ARCH-013 amendée |
| ARCH-RISK-011 — extraits : un fichier par déclaration, deux boîtes par tableau | important | ARCH-012 amendée |
| ARCH-RISK-012 — mots en trois langues | mineur | `wind_tab_words.py`, mots des briques dans `calc_tab_words.py`, test « pas de KN/M², pas de capitales » |
| ARCH-RISK-013 — taille des modules | mineur | `wind_source.py`, `wind_forces.py`, `wind_geometry.py`, `wind_blocks.py`, `model3d.py`, ≤ 1000 lignes chacun |
| ARCH-RISK-014 — « z = h », ligne b · d · h, menu sur la ligne d'un mot | mineur | `Field.special_word` (valeur `null`), champs sur une ligne dans `Section`, bloc `row_select` |
| ARCH-RISK-015 — messages rouges et `check_source` | mineur | REQ-009 amendée |
| ARCH-RISK-016 — la spec elle-même (REQ-014, REQ-020, UI-026) | mineur à important | amendées |
| ARCH-RISK-017 — prototype hors du dépôt | important | CON-001 amendée |

**Verdict** : APPROUVER AVEC RÉSERVES — les réserves sont toutes reprises (D-28 à D-32, « Amendé après la revue »).

## 14. Plan d'implémentation

Cinq versions publiables (D-30), chacune finie par sa vérification indépendante et `finish` ; chaque commit laisse la suite verte, l'ancien onglet Vent en service jusqu'à la cinquième (D-31).

**Version 1 — le domaine et le fichier du vent** (sans Qt, rien de nouveau à l'écran)
1. Le prototype extrait de `8e88677` dans `docs/requirements/prototypes/2026-10-23-onglet-vent/` (`git archive`), et les valeurs d'or de `compute()` pour les tableaux 31, 32, 36, 40, 59a, 59b dans `tests/fixtures/` (CON-001).
2. `wind_forces.py` : `analysis(src)` — q<sub>p</sub>, c<sub>red</sub> par φ, Q<sub>k</sub> en kN par φ et leurs extrêmes, pressions locales avec `c_d` (REQ-003), extrêmes par surface avec φ, c<sub>pe</sub>, c<sub>pi</sub> et le signe d'une paire (REQ-004, REQ-005), le détail par φ, ĉ<sub>pe</sub>, m n o à part (REQ-007, REQ-008) ; A<sub>ref</sub> par une table fermée (REQ-002). Tests : `tests/test_wind_source.py` (valeurs d'or, `c_d` ≠ 1, z minimal, catégorie IV).
3. Les ouvertures : schéma `wind-source` 1.2, `openings`, lecture de 1.0 et 1.1, message orange (REQ-006, D-24).
4. `messages(src)` : rouges et orange, chacun sur son champ (REQ-009).
5. `build_instance` sur `analysis` : Q<sub>k</sub> en kN ajoutés, noms existants gardés ; les tableaux du cas choisi seul, transposés, en blocs de douze surfaces au plus (REQ-013, REQ-014, REQ-020) ; les mots par le glossaire (REQ-016) ; une fonction commune qui résout les cellules nommant une variable, pour le fichier et la fenêtre (T127). Le code du vent dans un module à côté de `unfold.py`. `wind-load` dans `AUTO_REGENERATE`. Tests : `tests/test_unfold.py` (tableau 36 et un de la famille des marquises : nombres, cas choisi, blocs, aucun mot allemand dans le fichier français, compilation).
6. Documentation, « Nouveautés » (les fichiers du vent réécrits au premier enregistrement), vérification, `finish`.

**Version 2 — les briques complétées pour tous** (sur `fake_domain`, aucun changement visible de la neige ni du poids propre)
1. Les blocs de section : `contracts.Block`, `blocks(src, instance)`, `ctx.blocks`, `calc_blocks.py` (texte, SVG, formule, tableau coloré, `row_select`) ; `DeclaredForm` tolère les blocs ; `Field.special_word` et les champs sur une ligne (ARCH-003, ARCH-006, ARCH-RISK-014).
2. Les survols à clés : `litKeys`, `ctx.hover_element`, `links(src, instance)` (ARCH-004).
3. L'épinglage de tout module, l'état de vue tenu par le contexte, la fenêtre qui suit sa taille (ARCH-005).
4. « Affichage » : les tableaux comme éléments (Afficher, Titre, Note), le masquage généralisé, la figure à niveau 3 résolu par Typst (D-29), son réglage commun (UI-024, UI-025, ARCH-008, D-26).
5. Tests : `tests/test_calc_tab_base.py`, `tests/test_tab_services.py`, `tests/test_domain_file_display.py`, `tests/test_unfold.py` ; documentation, vérification, `finish`.

**Version 3 — la brique 3D et les 37 bâtiments**
1. `calc/domains/model3d.py` (scène, projection, échelle fixe, faces cachées, tri en profondeur, étiquettes) et son widget, sur un modèle de test, sans mot du vent ; jetons de couleur dans `theme.json` (ARCH-007, UI-008 à UI-018).
2. `wind_geometry.py` et `calc/norms/sia261-2020-annexC-geometry.json`, famille par famille — prismes (19 tableaux, dont les six du prototype), sheds/pans coupés/aération, ouverts, tribune, marquises, avant-toits, formes courbes —, chacune un commit vert avec son test (REQ-010, ARCH-011).
3. Les Résultats 3D (forces globales, charges de surface) sur la scène, `loadsAt`/`forcesAt` du prototype en Python (UI-014 à UI-017).
4. Tests : `tests/test_model3d.py`, `tests/test_model3d_widget.py`, `tests/test_wind_geometry.py` ; documentation, vérification, `finish`.

**Version 4 — les extraits de la norme**
1. `calc/norms/sia261-2020-wind-excerpts.json` : chapitre 6, annexe C (37 tableaux × 2 éditions × 2 boîtes), annexe E et sa carte, depuis la table `N` du prototype ; `FIELD_NORM` dans la déclaration (REQ-011, REQ-012, ARCH-012). Tests : `tests/test_norm_excerpts.py`. Documentation, vérification, `finish`.

**Version 5 — la mise en service**
1. La figure de la norme dans l'export par `annex.crop`, une image par édition dans `Variable-loads/Wind/Exports/Figures/`, `FIGURE_KINDS` et ses lecteurs, schéma `calculations` 1.9 s'il le faut, message orange sans la bibliothèque (REQ-017, D-28, D-21).
2. `wind_tab.py` : `WindTab(CalcTab)`, paramètres seulement, sa déclaration en quatre sections avec ses blocs, le volet droit et ses modules, « Affichage » (UI-001 à UI-027) ; ses mots (`wind_tab_words.py`).
3. La mise en service : `tab_registry.py`, les mots `ld_` déplacés, `LoadTab` supprimé, les tests de l'ancien onglet migrés (ARCH-013, #103).
4. Tests : `tests/test_wind_tab.py`, `tests/test_tab_overrides.py`, `tests/test_tab_registry.py`, `tests/test_figure_exports.py` ; captures des deux vues ; documentation complète (`docs/ui/tab-wind.md`, `docs/domain/loads.md`, `docs/decisions.md`, guide), vérification, `finish` qui ferme #100 et #103.

## 15. Vérification

_(à écrire par `verify-requirements`)_

**Version 1 (vérificateur indépendant, 24.10.2026)** : ✅ REQ-001 à REQ-008, REQ-013, REQ-015, REQ-020, CON-002, ARCH-004/008/013 pour V1 ; ⚠️ CON-001 (prototype à commiter — fait au commit de V1), REQ-009 (l'ID manquant est dit par la brique d'identité et le vert est `ct_complete` de la brique, non par `messages`), REQ-014 et REQ-016 (tests complétés : les 37 tableaux en blocs de ≤ 12, la marquise 51 en français sans mot allemand, z = 3 → 5, q<sub>p0</sub> absent) ; aucune régression. Déviations jugées : π·d²/8 et π·d²/4 calculés, acceptable ; le chemin du classeur n'imprime plus que « rep » (G86 non lu), à trancher par l'ingénieur.

**Version 2 (vérificateur indépendant, 24.10.2026)** : ✅ ARCH-003, ARCH-005, ARCH-006, ARCH-008 (tableaux éléments, masquage généralisé, figure niveau 3 par Typst), UI-024, UI-025, D-26, D-29, ARCH-RISK-014, la commande `#from-level` ; ⚠️ ARCH-004 : les corps des fenêtres ⧉ et des modules épinglés suivent eux aussi les survols, alors que l'amendement dit qu'ils ne les suivent pas (à trancher) ; `ctx.view_state` sans usage avant V3. Aucune régression ; neuf fichiers de tests verts.

**Version 3 (vérificateur indépendant, 24.10.2026)** : ✅ ARCH-007, UI-008, UI-009, UI-010, UI-011, UI-012, UI-015, UI-017 ; ⚠️ ARCH-011 et REQ-010 (six familles, positions des bandes de `DRAWN` non comparées une à une, géométrie hors prototype lue par Woodcore), UI-013, UI-014, UI-016, UI-018, UI-026 à prouver en V5 sur l'onglet (liens du vent, deux Résultats 3D, repli sur la figure). Aucune régression.

**Versions 4 et 5 (vérificateur indépendant, 24.10.2026)** : ✅ REQ-011, REQ-012, REQ-016 à REQ-019, UI-001, UI-003, UI-004, UI-006, UI-008 à UI-014, UI-018, UI-021, UI-022, UI-024 à UI-026, ARCH-001, ARCH-002, ARCH-009, ARCH-010, ARCH-012 à ARCH-014 ; aucune régression sur les dix fichiers lancés. ⚠️ UI-002, UI-007, UI-015 à UI-017, UI-020 : tenus par les briques et le domaine factice, pas tous par un test de l'onglet du vent. ⚠️ UI-005 : la figure et le modèle l'un sous l'autre, sans bascule ; la toiture et le titre du tableau absents des faits. ❌ UI-019 : le volet de droite a l'état, les résultats (c_h, q_p, c_red, Q_k, puis les deux tableaux du fichier) et la figure 9 ; il n'a ni le module « Bâtiment » ni les tableaux Murs / Toiture / Surfaces localisées du prototype (le modèle et les résultats 3D s'y épinglent). ⚠️ UI-027 (« rép. » codé en dur) et ARCH-015 (`wind-load` dans test_figure_exports, commande d'« Affichage » du vent) : corrigés après la vérification (terme `c_pi glm.` du glossaire, tests ajoutés). UI-005 et UI-019 restent des écarts, soumis à l'ingénieur.

**Écarts UI-005 et UI-019 repris (24.10.2026)** : l'ingénieur a demandé les tableaux du prototype et la bascule. `Declaration.modules` (D-34) et le bloc `views` (D-35) ; « Résultats » liste c_h, q_p, c_red, puis Q_k max et min à leur φ et les tableaux Murs, Toiture, Points de mesure, Surfaces localisées (pression max et succion max à leur φ, survols vers la surface et ses c_pe/c_pi) ; module « Bâtiment » ; « Norme | Modèle 3D » en section 2 et dans le module, le même choix ; titre du tableau et toiture dans les faits. Tenus par `test_the_right_pane_has_the_results_at_their_phi_and_the_building` et `test_the_figure_and_the_model_are_one_view_at_a_time_the_same_in_the_section_and_the_module`. UI-005 et UI-019 : ✅. Q8 : m et o de la tribune dessinés (D-37).

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-23 | draft | spécification extraite de la source (issue #100, messages de l'ingénieur) |
| 2026-10-23 | specified | Q-001, Q-005, Q-006, Q-007 tranchées par l'ingénieur (les recommandations) ; Q-002, Q-003, Q-004, Q-008 résolues par les principes, les règles en vigueur et le choix laissé à la spec (D-20 à D-27) ; plus aucun point non résolu |
| 2026-10-23 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (2 bloquants : la découpe de la figure, le niveau 3) ; Q-009 à Q-011 tranchées par l'ingénieur (D-28 à D-30) ; réserves reprises (D-31, D-32, « Amendé après la revue ») ; plan §14 en cinq versions |
| 2026-10-23 | approved | approuvée par l'ingénieur (« Approuver et implémenter ») ; implémentation de la version 1 (domaine et fichier) |
| 2026-10-23 | implementation | V1.1 fait : prototype extrait de `8e88677` par `git archive`, valeurs d'or de `compute()` pour huit tableaux (31, 32, 36, 40, 46, 57a, 59a, 59b) dans `tests/fixtures/wind-prototype-golden.json`. V1.2 fait : `calc/domains/wind_forces.py` `analysis(src)` (q<sub>p</sub>, c<sub>red</sub> par φ, Q<sub>k</sub> en kN, pressions locales avec c<sub>d</sub>, extrêmes avec φ, c<sub>pe</sub>, c<sub>pi</sub> et clés de cellules `cell:<colonne>:<ligne>[:<côté>]`, m n o à part, ĉ<sub>pe</sub>·q<sub>p</sub>) ; A<sub>ref</sub> par la table fermée `forces.areas` de `sia261-2020-6.2-wind.json` et `sia261_wind.area` — π·d²/8 et π·d²/4 calculés, comme le prototype (seuls h₁, d₁, hs restent par m²) ; six tests dans `tests/test_wind_source.py`, verts. Reste V1.3 à V1.6 |
| 2026-10-23 | implementation | V1.3 fait : schéma `wind-source` 1.2 (`openings` : rep, A-D ; `OPENINGS_SCHEMA_VERSION`), `new_source` en 1.2 avec « rep », 1.0 et 1.1 lus avec « rep », `openings` hors 1.2 refusé ; `analysis` lit `openings`. V1.4 fait : `wind_source._problems` (les rouges, un seul endroit, comme la neige) et `messages(src)` — rouges seuls s'il y en a, sinon les oranges `z_min`, `iv_as_iii`, `c_d_default`, `c_red_outside`, `ratio` (seuil `RATIO_SPREAD` = 1,5, propre à Woodcore), `direct`, `no_area`, `openings_default` (D-24), chacun sur son champ ; le vert est `ct_complete` de la brique ; l'ID manquant est dit par la brique d'identité. `warnings` (l'export) ne dit que `c_red_outside`, comme avant. Les mots des messages viendront avec l'onglet (V2). Tests : les oranges des huit cas d'or égaux à ceux du prototype, champ pour champ ; une sonde par message. Reste V1.5, V1.6 |
| 2026-10-23 | implementation | V1.5 fait : `build_instance` lit `analysis` ; forces globales en Q<sub>k</sub> [kN] avec les nombres (`Qk_max_cf*`, `Qk_min_cf*` ajoutés après les `qk_*` gardés, relibellés « globale Windlast je m² ») ; pressions locales du cas choisi seul, transposées, `widths: "first-auto"`, en ⌈n/12⌉ blocs équilibrés (`wind_source.surface_blocks`), la note nommant les surfaces localisées présentes ; `contracts.table_cell` résout une cellule qui nomme une variable pour le fichier (`unfold._table_lines`) et la fenêtre (`calc_modules.tables_html`), avec `decimals` ; mots par le glossaire (six gabarits et six termes, trois langues) ; `wind-load` dans `AUTO_REGENERATE`. Aucun code du vent n'entre dans `unfold.py` : le domaine émet ses tableaux, le générateur reste générique (ARCH-008 tenu sans module à côté). ⚠️ Écart à signaler : une feuille du classeur (chemin `wind.py`) passe aussi par `build_instance` et n'imprime plus que « rep » ; sa sélection `G86` n'est pas lue. ⚠️ π·d²/8 et π·d²/4 calculés (le prototype les calcule ; l'amendement de REQ-002 les citait parmi les cotes absentes). Tests : `tests/test_unfold.py` (fichier fr, de, en, compilé ; blocs). Docs : `loads.md` §3.3quater, `variable-links.md`, `calc-tab.md`, catalogue des tests, CHANGELOG, « Nouveautés » 0.125 en trois langues |
| 2026-10-24 | implementation | V1 vérifiée (§15) ; tests complétés après la vérification ; `title` vide sur un bloc de suite (le schéma `calculations` le demande), `results` du classeur avec les Q<sub>k</sub>. Reste : `finish` de V1, puis V2 |
| 2026-10-24 | implementation | V1 commitée (`6a18d7c`), poussée ; écart du classeur tranché par l'ingénieur (D-33). Suite complète : 3094 passés, 10 ignorés ; `test_updates` bloqué hors de ce travail, issue #108. Prochaine étape : V2 (les briques complétées) |
| 2026-10-24 | implementation | V2 faite (les briques complétées, sur `tests/fake_domain.py`) : V2.1 `contracts.Block`, `BLOCK_KINDS`, `Declaration.blocks`, lignes de champs (tuple de clés), `Field.special_word`, `calc/tools/calc_blocks.py` (texte, SVG, formule, tableau coloré `HeatTable` aux jetons `heat-*` de `theme.json`, `row_select`), `ctx.blocks` ; V2.2 `litKeys`, `ctx.hover_element`, `links(src, instance)` lu une fois (`ctx.element_links` — `ctx.links` était déjà le `LinkSet`) ; V2.3 📌 d'un bloc `pinnable` (`ctx.pin_block`, module `b:<key>`, restauré), `ModuleSpec.fills_window` et `FillingWindow`, `ctx.view_state` — écart : `pinnable` est porté par le bloc, la chose épinglée, non par `ModuleSpec` ; V2.4 tableaux éléments d'« Affichage » (`table:<i>`, `set_table`, `write_table`), masquage généralisé aux lignes étiquetées, nombres d'un tableau masqué repris par l'export, commande Typst `#from-level(n)[…]` et `figure_line(level=3)` (D-29). `model3d` reste sans widget jusqu'à V3. Docs : `calc-tab.md`, `report-engine.md` §4, catalogues, CHANGELOG, « Nouveautés » (les tableaux dans « Affichage »). Reste : vérification, `finish` |
| 2026-10-24 | implementation | V3 faite : `calc/domains/model3d.py` (scène, projection à échelle fixe, faces vues, tri, étiquettes écartées, SVG, pick, sans Qt) et son widget `calc_blocks.Model3D` ; `calc/norms/sia261-2020-annexc-wind-geometry.json` (renommé selon la règle du dossier) et `calc/domains/wind_geometry.py` : 37 bâtiments, six familles de constructeurs (les sheds, pans coupés et l'aération dans les prismes, au lieu de sept familles) ; `wind_forces.forces_at`, `loads_at`. Écarts à signaler : géométrie des familles 42-45, 50-57 et zones m, n hors du prototype lues par Woodcore sur les figures (approchées) ; marquises dessinées sur b = 2,5 d (la moitié du tableau, comme la figure) ; m et o de la tribune 50 non dessinés (le tableau ne les chiffre pas). Tests : `test_model3d`, `test_wind_geometry`, `test_model3d_widget` |
| 2026-10-24 | implementation | V2 et V3 commitées ensemble (`66c1dc6`, les mêmes fichiers portent les deux), fusionnées avec les prototypes de l'ingénieur et poussées (`fe62a94`). V4 faite : `calc/norms/sia261-2020-wind-excerpts.json` (90 extraits : chapitre 6, annexe E et sa carte, 37 tableaux × table et figure, FR et DE), tiré de la table `N` du prototype ; `excerpts.py` lit un `chapter` propre à un extrait (l'annexe C s'ouvre aux p. 81-114) ; textes tenus au PDF (`test_norm_excerpts`, trois corrections : « von den » de la figure 9 allemande, ĉ<sub>pe</sub> sur sa ligne dans la figure 22). `FIELD_NORM` passe dans la déclaration avec l'onglet (V5) |
| 2026-10-24 | verification | V5 faite : l'onglet en service sur le type « Calcul » (`calc/tools/wind_tab.py`, une classe de paramètres ; `calc/domains/wind_view.py` : déclaration en quatre sections, 14 blocs, liens de survol `key_links`, figure 9), la figure de la norme découpée à l'enregistrement dans `Variable-loads/Wind/Exports/Figures/<id>-fig-{fr,de}.pdf` et écrite dès le niveau 3, `load_tab.py` retiré (mots `ld_` encore composés par la base dans `load_words.py`). Corrigés en route : la hauteur d'un tableau large qui défile, les cellules retirées encore peintes, une liste déroulante qui ne recalculait pas, les mots composés que le test des traductions ne voyait pas. Vérifiée (§15), écarts UI-005 et UI-019 soumis à l'ingénieur |
| 2026-10-24 | completed | Écarts UI-005 et UI-019 repris à la demande de l'ingénieur (D-34 à D-37 : `Declaration.modules`, bloc `views`, fenêtres qui s'allument sans bouger, réponses aux questions de la nuit, m et o de la tribune) ; critères cochés, spec rangée dans `completed/` |
