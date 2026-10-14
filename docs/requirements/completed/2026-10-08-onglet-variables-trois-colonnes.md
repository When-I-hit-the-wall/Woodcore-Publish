---
id: 2026-10-08-onglet-variables-trois-colonnes
titre: Onglet « Variables » en trois colonnes (domaines | variables | détail), toutes les variables avec leur provenance, retrait de l'onglet « Charges »
status: completed
cree: 2026-10-08
mis_a_jour: 2026-10-08
source: message écrit (issue GitHub When-I-hit-the-wall/Woodcore#13, « Variables »)
docs: [docs/ui/window.md, docs/typst/formulas.md, docs/domain/loads.md, docs/domain/calculation-domains.md, docs/architecture/principles.md, docs/architecture/layout.md, docs/architecture/data-contracts.md, docs/decisions.md]
---

# Onglet « Variables » en trois colonnes et retrait de « Charges » — Spécification

## 1. Objectif

Faire de l'onglet *Variables* (v0.100, `calc/tools/variables_tab.py`) **le** lieu où l'on voit toute valeur du projet : trois colonnes — domaines | variables du domaine choisi (liste plate) | détail (nom, symbole, valeur, appels à copier) —, un filtre qui peut porter sur toutes les variables et pas seulement sur le domaine choisi, et, pour chaque variable, sa **provenance** : les classeurs Excel, Woodcore lui-même (charges, connecteurs, moments polaires…), ou l'export JSON des variables calculées dans Typst. Une fois prouvé qu'aucune variable de l'onglet *Charges* (`LoadsTab`) ne manque dans *Variables*, *Charges* est supprimé : il n'y a plus qu'un endroit où chercher une valeur.

## 2. Source

L'issue 13 telle qu'elle est écrite (lue par `gh issue view 13`, le 2026-10-08, sans commentaire) :

> **T0** — « Onglet *Variables* (v0.100, `calc/tools/variables_tab.py`, `docs/ui/window.md`). Il a aujourd'hui un arbre à gauche (domaine, puis variables) et des cartes de détail à droite. Il ne liste que ce que le rapport calcule en Typst. » *(contexte)*
>
> **T1** — « Organiser l'onglet en trois colonnes : domaines | variables | détail (nom, symbole, valeur, appels à copier). »
>
> **T2** — « Faire remplacer l'arbre actuel par ce volet de domaines. Le volet principal devient une liste plate des variables du domaine choisi. »
>
> **T3** — « Permettre de choisir, quand on filtre, de filtrer toutes les variables et pas seulement celles du domaine sélectionné. »
>
> **T4** — « Présenter toutes les variables, avec leur provenance affichée. Elles viennent de trois sources : les Excel, Woodcore (charges, connecteurs, moments polaires, etc.) et l'export JSON des variables calculées dans Typst. »
>
> **T5** — « Supprimer l'onglet *Charges* (`LoadsTab`) une fois vérifié qu'aucune de ses variables ne manque dans *Variables*. Ce point dépend du précédent. »

## 2bis. Ce qui existe déjà (vérifié dans le code, 2026-10-08)

- `VariablesTab` (`calc/tools/variables_tab.py`, 858 l.) liste **déjà** deux familles : les registres Typst des trois documents (`variables.best(here, mode=…)`, lus dans le PDF — pièce jointe `woodcore-variables.json`, v0.110 — ou par une compilation) et **toute variable de `data/calculations.json`** (`export_registry`, source `EXPORT`). La colonne « Document » (Export · CU · BP · RS) dit déjà d'où vient une ligne, mais **pas** si la valeur vient d'Excel ou de Python.
- Un `QTreeWidget` à six colonnes (domaine → variables) ; la recherche et deux combos (unité, document) filtrent ; à droite une carte d'identité, une note « non tracé » et, depuis v0.117, la vue *Affichage* (`display_view.DisplayTab`, `install_display("tab_variables", centre=1, right=None)`).
- La provenance d'une variable de l'export est **déjà dans sa donnée** : le champ `source` (`excel:<classeur>!<feuille>!<cellule>`, `python:<module>`, `norm:<table>` ; `parse_source`, `woodcore_gui.py:962`). `variables.Variable` la porte (`source`) mais l'onglet ne l'affiche que dans la carte de détail.
- Cinq fichiers de `data/` portent des `vars` selon leur schéma : `calculations.json`, `connections.json` (moments polaires), `connectors.json`, `scripts.json` et `positions/<id>.json` (`schemas/*.schema.json`). **Seul le premier est lu par l'onglet** : connecteurs, moments polaires, scripts et domaines de position n'y figurent pas (sauf ce que `show-polar-moment` ou un `verify-*` publie dans le registre Typst).
- `LoadsTab` (`woodcore_gui.py:1240`, ≈ 430 l.) montre, par action → domaine → cas → variable : nom, symbole, valeur, unité, désignation, **niveau**, **source** (cellule Excel), **norme** ; `★` pour les résultats ; « résultats seulement » ; le détail (classeur, feuille, cellule, formule de l'étape, choix, tableaux d'un cas) ; « Ouvrir le classeur » ; en *Affichage* : `val`, `var`, `show-input`, `var-of`, `value-of`, `show-calc`, `show-live-load`, `show-check`, la boucle d'un domaine et les deux tableaux de synthèse. Il est dans `TABS` (`woodcore_gui.py:2791`), `NAV_GROUPS["nav_actions"]` (2820), `NAV_SECTIONS` (2833), `refresh_tab` (3331) et `rebuild` (3540), `chrome.ICONS`, `STRINGS` (trois langues), et nommé par plusieurs tests (`test_action_tabs`, `test_modes_window`, `test_views`, `test_richtext`, `test_layout_store`, `test_chrome`).

## 3. Exigences fonctionnelles

### REQ-001 — Trois colonnes : domaines | variables | détail
- **Exigence** : Woodcore doit organiser l'onglet *Variables* en trois volets côte à côte : à gauche les domaines, au centre la liste des variables, à droite le détail de la variable choisie.
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : en vue *Données*, trois volets visibles (domaines, variables, détail) ; le séparateur a quatre enfants, le quatrième étant le volet d'options de la vue *Affichage*, caché en *Données* (`install_display("tab_variables", centre=2, right=None)`, D-011) ; en *Affichage*, domaines et variables restent visibles et l'aperçu remplace le détail. `restore` n'applique `view_state["splitter"]` que si sa longueur égale `splitter.count()` : l'ancien état à trois largeurs `[liste, détail, 0]` est ignoré, jamais appliqué de travers (test).

### REQ-002 — Le volet de domaines remplace l'arbre
- **Exigence** : Woodcore doit retirer le `QTreeWidget` actuel (domaine → variables) ; le volet de gauche liste **les domaines** — un par domaine de chaque source (domaine nommé, `Rapport`, nachweis, calcul de l'export… comme `fill_tree` les nomme aujourd'hui) — avec, pour chacun, le nombre de variables et sa provenance ; choisir un domaine remplit le volet central.
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : aucune ligne de la liste des variables n'a d'enfant (une liste plate ; un `QTreeWidget` sans décoration est permis, `test_richtext` y vérifie le `MathDelegate`) ; le nombre affiché par domaine est son total, il ne suit pas le filtre (D-015) ; un test sur le projet exemple compte les lignes du volet de domaines = nombre de domaines des sources lues, et pour chacune le nombre affiché = nombre de variables du domaine.

### REQ-003 — Le volet principal : liste plate des variables du domaine choisi
- **Exigence** : Woodcore doit afficher au centre une liste **plate** (sans niveau d'arbre) des variables du domaine choisi, avec les colonnes que l'arbre avait : nom (précédé de ★ pour un résultat du cas, D-007), symbole (composé, `richtext.MathDelegate`), valeur (alignée à droite pour un nombre), unité, désignation, provenance — et, quand « Tous les domaines » est cochée, le domaine de chaque ligne. Une case « Résultats seulement », décochée par défaut, ne garde que les résultats (D-007).
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : choisir le domaine `snow-load · SL` du projet exemple donne exactement les variables de cette instance dans l'ordre de l'export ; aucune ligne n'a d'enfant.

### REQ-004 — Portée du filtre : le domaine choisi ou toutes les variables
- **Exigence** : Woodcore doit laisser l'ingénieur choisir, quand il filtre (recherche, unité, provenance), si le filtre porte sur le domaine sélectionné seulement ou sur **toutes** les variables de toutes les sources. La forme du choix : case « Tous les domaines » (D-005).
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : un test pose une recherche qui ne trouve rien dans le domaine A mais une variable dans le domaine B : portée « domaine » → liste vide et message `vr_filtered` ; portée « toutes » → la variable du domaine B est listée avec son domaine nommé ; le choix de portée survit à une reconstruction de la fenêtre (`view_state`).

### REQ-005 — Les trois sources, toutes lues
- **Exigence** : Woodcore doit présenter toutes les variables des trois sources : (a) **Excel** — les variables des classeurs, telles que l'export les a lues ; (b) **Woodcore** — ce que Woodcore calcule lui-même (domaines Python et tables de norme, charges, connecteurs, moments polaires…) ; (c) **Typst** — les variables que les documents calculent, lues dans l'export JSON des variables (la pièce jointe `woodcore-variables.json` du PDF, ou la compilation qui la remplace ; D-001 confirmée, D-010). Les fichiers couverts par « Woodcore » : D-003 amendée par D-009 — `calculations.json`, `connections.json`, `connectors.json`, `scripts.json`, lus sur disque par le module (D-014).
- **Source** : T4
- **Priorité** : doit
- **Critère d'acceptation** : sur le projet exemple exporté, chaque variable de chacun des fichiers retenus par Q-001 est dans le modèle de l'onglet (test d'exhaustivité, REQ-008) ; une variable de `connections.json` (`I_p`) et une de `connectors.json` y figurent, ce qu'aucune ne faisait avant.

### REQ-006 — La provenance de chaque variable est affichée
- **Exigence** : Woodcore doit afficher, pour chaque variable, sa provenance — *Excel*, *Woodcore* ou *Typst* — dans la liste (colonne) et dans le détail, avec le détail de la source (classeur · feuille · cellule pour Excel, module ou table de norme pour Woodcore, document CU/BP/RS pour Typst). La provenance se déduit de la donnée (`source`, fichier d'origine, registre), jamais d'un nom. La forme : une colonne Provenance (D-004).
- **Source** : T4
- **Priorité** : doit
- **Critère d'acceptation** : un test donne les provenances attendues pour une variable `excel:…`, une `python:…`, une `norm:…`, une `woodcore:…` (entrées des connecteurs), une de `connections.json` et une du registre d'un document — y compris une variable Typst copiée de l'export par `#var(…, domain: (…))`, qui porte une `source` `excel:` et reste **Typst** (précédence, D-012) ; un second test balaie toutes les `source` des fichiers du projet exemple et échoue sur un préfixe que la table ne connaît pas ; la colonne et le détail les affichent dans les trois langues ; une variable dont la `source` est vide ou inconnue est affichée « inconnue » et non attribuée à tort.

### REQ-007 — Le détail : nom, symbole, valeur, appels à copier
- **Exigence** : Woodcore doit afficher à droite le nom (celui qu'on tape dans un appel), le symbole (composé comme la page l'imprime), la valeur avec son unité, et les appels à copier (vue *Affichage* : `val`, `var`, `find`, `show-calc`… comme aujourd'hui, `display_entries`). Ce que *Charges* montrait en plus d'une variable (niveau, norme, cellule Excel, formule, choix, classeur à ouvrir, commandes de cas et de domaine) est repris selon D-006 : variable → détail (traçabilité) et *Affichage* ; cas et domaine → *Affichage*.
- **Source** : T1, T5
- **Priorité** : doit
- **Critère d'acceptation** : un test compare aux appels qu'offrait `LoadsTab.display_entries` : ligne variable de l'export → `val`, `var`, `show-input`, `var-of`, `value-of` (nombre seulement) ; ligne domaine de l'export → `show-calc`, `show-live-load` (si `ref.LIVE_LOAD_DOMAIN` et `q_k`), un `show-check` par check, la boucle sur les cas du calcul (D-013) et, pour un cas de charges, les deux synthèses ; ligne Typst → `val`, `var` (domaine nommé), `find` comme aujourd'hui. Le détail d'une variable de l'export montre niveau, norme, classeur · feuille · cellule (ou module, ou table de norme), formule de l'étape, choix ; *Ouvrir le classeur* est actif quand le classeur existe. Aucun geste de copie dans la liste (D-008).

### REQ-008 — Vérifier qu'aucune variable de « Charges » ne manque
- **Exigence** : Woodcore doit apporter la preuve, **avant** la suppression de *Charges*, que toute variable que *Charges* listait (chaque variable de chaque instance de `data/calculations.json`, résultats ou non) est listée par *Variables* avec les mêmes nom, symbole, valeur, unité, désignation.
- **Source** : T5
- **Priorité** : doit
- **Critère d'acceptation** : un test (`tests/test_variables_tab.py` ou équivalent) sur le projet exemple parcourt `calculations.json` et vérifie l'appartenance de chaque `(domaine, instance, nom)` au modèle de l'onglet, avec ses cinq champs ; il échoue en nommant la variable manquante. Il est écrit et vert **avant** l'étape de suppression du plan.

### REQ-009 — Suppression de l'onglet « Charges »
- **Exigence** : Woodcore doit supprimer l'onglet *Charges* : la classe `LoadsTab` et ce que seul elle utilise, son entrée de `TABS`, de `NAV_GROUPS["nav_actions"]` et de `NAV_SECTIONS`, ses mots (`tab_loads` et les clés qu'elle seule porte), son icône, ses cas particuliers dans `refresh_tab` et `rebuild` (`self.view`), et les tests qui le nomment (adaptés, pas retirés sans remplaçant).
- **Source** : T5
- **Priorité** : doit
- **Critère d'acceptation** : les aides mortes partent avec la classe (`Details`, `esc`, `load_groups`, `table_text`, `value_with_unit`, `is_number`, `var_commands`, `instance_commands`, `domain_commands`, `ACTIONS` de `woodcore_gui`, `self.view`/`app.view`), les partagées restent (`instance_workbook` déplacée dans le module sans Qt et réimportée, `fmt_value`, `one_line`, `plain_label`, `data_file`/`load_data`) ; la fine ligne de `NAV_SECTIONS` passe à `tab_combinations` ; les textes d'`action_tabs.py` qui renvoient à « Charges » renvoient à « Variables » ; les clés de mots que seul `LoadsTab` portait partent des trois langues (`tests/test_i18n.py`) ; `grep -rn "LoadsTab\|tab_loads" calc/ tests/` ne trouve rien hors d'une liste d'exceptions justifiées (réglages d'utilisateur anciens ignorés sans erreur) ; la suite de tests passe ; la fenêtre ouverte sur un projet dont les réglages d'utilisateur ou la disposition nomment `tab_loads` s'ouvre sans erreur ni onglet fantôme.

### REQ-010 — Dans les trois documents
- **Exigence** : Woodcore doit garder *Variables* dans la convention d'utilisation, la base de projet et le rapport (`DOCUMENT_TABS`), la source Excel et Woodcore étant la même pour les trois (c'est l'export du projet).
- **Source** : inférée (état actuel : `DOCUMENT_TABS` contient `tab_variables`)
- **Priorité** : doit
- **Critère d'acceptation** : `MODE_TABS` de `cu` et `bp` contient toujours `tab_variables` ; un test construit l'onglet dans les trois modes.

## 4. Exigences d'interface (fenêtre)

### UI-001 — Mots en trois langues
- **Exigence** : toute chaîne nouvelle (titres des volets, colonne et valeurs de provenance, portée du filtre, domaines, messages) est dans `variables_tab.STRINGS` sous le préfixe `vr_`, en fr, de et en ; aucun mot en dur.
- **Source** : CON-002
- **Langues** : fr / de / en
- **Critère d'acceptation** : le test de clés existant (`tests/test_variables.py`, comparaison des trois langues) passe, étendu aux nouvelles clés.

### UI-002 — Les états de la liste
- **Exigence** : liste vide (aucun domaine choisi, filtre sans résultat, aucune lecture encore) dit pourquoi, comme `vr_empty` / `vr_filtered` aujourd'hui ; la bannière (lecture périmée, échec) et le bouton *Relire les documents* restent.
- **Source** : T2 (conservation)
- **Priorité** : doit
- **Critère d'acceptation** : les tests de bannière et de lecture de `tests/test_variables.py` passent sans changement d'intention.

### UI-003 — Largeurs et mémoire de la vue
- **Exigence** : domaine choisi, variable choisie, portée du filtre, recherche, unité, provenance et largeurs des trois volets survivent à une reconstruction de la fenêtre (`view_state` / `restore`) ; une clé d'état d'une version antérieure est acceptée.
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : test aller-retour `view_state` → `restore` sur l'état actuel et sur un état de l'ancienne forme.

## 5. Exigences d'architecture

### ARCH-001 — L'assemblage des sources est du domaine, sans Qt
- **Exigence** : la lecture des fichiers de `data/` qui portent des `vars` vit dans un module neuf sans Qt, `calc/variable_sources.py`, piloté par une table `FILE_SOURCES` (fichier, clé racine, mot de domaine) qui accueillera la source *Formules* de la spec soeur ; `parse_source`, la table des provenances et les champs `level`/`choices` de `Variable` vont dans `calc/variables.py` à côté de `Variable.citation`. L'onglet montre, ne lit aucun fichier et ne recalcule rien.
- **Source** : principes « Domain logic is independent of the UI » (CLAUDE.md), `docs/architecture/principles.md`
- **Critère d'acceptation** : le module s'importe et se teste sans PySide6 ; `export_registry` y migre sans alias laissé dans l'onglet ; `connection.py` et `script.py` reçoivent un `EXPORT_FILE` comme `connector.EXPORT_FILE`, et le module les lit de là (aucun nom de fichier écrit deux fois) ; `build_reference.iter_sources` n'est pas touché (classeur de référence reproductible) ; l'onglet ne contient aucune lecture de `data/*.json`.

### ARCH-002 — Aucun fichier nouveau, aucune valeur copiée
- **Exigence** : rien n'est écrit dans `data/` ni dans le projet (`data/` est l'entrée de Typst, pas sa sortie ; avertissement de `calc/variables.py`) ; aucun schéma nouveau : l'onglet lit les fichiers que l'export a déjà écrits et validés ; le cache reste hors du projet.
- **Source** : « One source of truth », `calc/variables.py` (« It is read, never written »)
- **Critère d'acceptation** : un test compare l'arbre des fichiers du projet avant et après la construction de l'onglet : identique.

### ARCH-003 — Un fichier absent avertit, un fichier malformé nomme sa cause
- **Exigence** : un `data/connections.json` ou `connectors.json` absent (projet jamais exporté) donne une source vide et le mot `no_data` (« importer les données »), pas une erreur ; un fichier présent mais malformé est dit avec son nom et le champ en cause (« A missing input warns, a malformed file stops »), sans effacer ce qui a été lu des autres sources.
- **Source** : CLAUDE.md (principe 7)
- **Critère d'acceptation** : deux tests : projet sans `data/` → onglet vide avec `vr_empty` ; `connections.json` tronqué → bannière nommant le fichier, les autres sources listées.

### ARCH-004 — Version de contrat
- **Exigence** : les champs ajoutés à `Variable` ont une valeur par défaut et ne sont pas sérialisés dans le cache (seuls les registres Typst sont en cache) : `CACHE_VERSION` ne change pas ; si un champ sérialisé change un jour, le changement est rétrocompatible avec le cache disque des lectures (`variables.save`/`cached`, `stamp`) ou la version du cache est incrémentée pour qu'une lecture ancienne soit relue plutôt que mal interprétée.
- **Source** : principe « Explicit, versioned data models »
- **Critère d'acceptation** : un test lit un cache de l'ancienne forme et obtient soit la lecture complétée, soit un « à relire » ; jamais une exception.

## 6. Contraintes

- **CON-001** — Plusieurs sessions Claude éditent ce dépôt en même temps ; au moment de la rédaction `calc/tools/variables_tab.py`, `calc/tools/woodcore_gui.py` et `calc/tools/chrome.py` portent des modifications non commitées d'une autre session. Ni `git checkout --`, ni `stash`, ni `reset`, ni `clean` ; éditions ciblées ; relire le fichier juste avant de l'éditer ; coordonner avec le pair avant d'y toucher (CLAUDE.md, mémoire « Concurrent sessions »). `woodcore_gui.py` est un gros fichier CRLF : `Edit` ciblé.
- **CON-002** — Trois langues (de, fr, en) ; pas de prose coupée à la main ; code, docs et commentaires en anglais ; la spécification en français.
- **CON-003** — Les tests tournent par `python tests/run_tests.py [-k nom]` depuis `Woodcore/`, sur `tests/projet-exemple/` ; on n'écrit jamais dans les projets de l'ingénieur (`../Musterprojekt/`).
- **CON-004** — Une lecture du registre Typst coûte une compilation (8–10 s) : la règle de `on_shown` (une lecture au premier affichage, ensuite seulement ce qui est gratuit) et `WOODCORE_VARIABLES_READ=0` des tests restent.
- **CON-005** — La spec soeur `2026-10-08-schema-actions-positions-affichage.md` (D-005) garde « Charges » dans le groupe *Actions* « tant que les six nouveaux onglets sont vides » ; sa suppression ici est la décision plus récente de l'ingénieur : la spec soeur, son test (`tests/test_action_tabs.py`) et `docs/ui/window.md` sont mis en accord, pas contredits en silence.
- **CON-006** — Terminé = documentation (sections de `docs/ui/window.md`, `docs/typst/formulas.md` §10quinquies si touché, `docs/domain/loads.md` pour ce qui renvoie à l'onglet, `docs/decisions.md` — la suppression de *Charges* tranche ce que `decisions.md` laissait « à ce jour-là » —, `docs/architecture/layout.md` pour le module neuf, `docs/architecture/data-contracts.md` §3.1 pour la table des préfixes de `source`), `CHANGELOG.md`, page « Nouveautés » de la prochaine version en trois langues (CLAUDE.md). Aucune commande Typst nouvelle : pas de `///` à écrire.

## 7. Décisions prises

- **D-001** *(inférée de T4, à confirmer à la relecture de la spec)* — « l'export JSON des variables calculées dans Typst » est le mécanisme qui existe : `woodcore-variables.json`, pièce jointe du PDF de chaque document (v0.110), relue par `variables.best` ou, à défaut, par la compilation. Aucun nouveau fichier n'est écrit dans `data/` (ARCH-002). Prix accepté : la source Typst reste périmée tant qu'un document n'a pas été exporté ou relu.
- **D-002** *(inférée)* — La provenance est une propriété de la **variable** (champ `source`, fichier d'origine), pas du domaine : une même instance de l'export peut mêler cellules Excel et valeurs Python. D'où : la provenance est une colonne et un filtre, pas un regroupement du volet de domaines.

- **D-003** — Q-001 A : la source « Woodcore » couvre cinq fichiers de `data/` (`calculations.json` pour ses variables `python:`/`norm:`, `connections.json`, `connectors.json`, `scripts.json`, `positions/<id>.json`). Prix : cinq lectures à garder en phase avec leurs schémas ; gain : une seule liste.
- **D-004** — Q-002 A : une colonne **Provenance** (Excel · Woodcore · Typst, Typst précisant son document CU/BP/RS) remplace « Document » et son filtre. Prix : l'axe « export / CU / BP / RS » seul disparaît comme colonne ; il reste dit par la provenance Typst et par le domaine.
- **D-005** — Q-003 A : le filtre agit sur le domaine choisi ; la case « Tous les domaines » l'étend à toutes les variables et ajoute alors le domaine de chaque ligne.
- **D-006** — Q-004 A : *Variables* reprend la traçabilité d'une variable (niveau, norme, classeur · feuille · cellule, formule de l'étape, choix, marque des résultats, *Ouvrir le classeur*) et les appels de cas, de domaine et de synthèse de *Charges* en vue *Affichage*. Prix : seuls les tableaux d'un cas ne sont plus montrés dans la fenêtre (ils restent dans le rapport par `show-calc`).

- **D-007** — Q-005 A : les résultats d'un cas sont marqués ★ dans la liste ; une case « Résultats seulement », **décochée** par défaut, les isole.
- **D-008** — Q-006 B : pas de geste de copie dans la liste (ni double-clic, ni Ctrl+C, ni clic droit) ; on copie depuis la vue *Affichage*. Prix accepté : un clic de plus qu'avec *Charges*.
- **D-009** — Q-007 A : les domaines de `positions/<id>.json` (vides aujourd'hui, `export_all.py:71`) sont retirés de cette version ; D-003 se lit « quatre fichiers ». Ils s'ajouteront à `FILE_SOURCES` le jour où l'export en remplira.
- **D-010** — Q-008 A : D-001 est confirmée par l'ingénieur.
- **D-011** *(revue, ARCH-RISK-001)* — le séparateur a quatre enfants `[domaines | variables | détail⇄aperçu | options]`, `install_display(centre=2, right=None)` : trois volets de travail en *Données*, l'aperçu prenant la place du détail en *Affichage*, les deux premiers volets restant visibles pour choisir une autre variable. Un état mémorisé de longueur différente est ignoré.
- **D-012** *(revue, ARCH-RISK-002/004)* — la provenance se calcule à l'assemblage, jamais stockée : une variable venue d'un registre Typst est **Typst · CU/BP/RS**, quelle que soit sa `source` ; sinon `excel:` → Excel, `python:` / `norm:` / `woodcore:` → Woodcore, vide → inconnue. La `source` brute reste le détail (ligne « Source », l'ancienne clé `vr_source` qui disait « Provenance » étant renommée, ARCH-RISK-012).
- **D-013** *(revue, ARCH-RISK-009)* — la boucle sur les cas d'un calcul est offerte sur chaque ligne de domaine (instance) de ce calcul, le volet de domaines n'ayant pas de ligne « calcul » ; les deux synthèses sont offertes sur toute ligne de domaine **de charges** de l'export (un cas de `calculations.json`) — *précision du 2026-10-08, à l'implémentation : `show-load-summary` et `show-line-load-summary` résument les charges, et *Charges* ne les offrait que sur des lignes de charges ; un moment polaire, un connecteur ou un script n'en a pas (relevé ⚠️ de la vérification, tranché ainsi et signalé à l'ingénieur)*.
- **D-014** *(revue, ARCH-RISK-013)* — le module lit les quatre fichiers sur disque (quelques dizaines de Ko, sans thread) à la construction et à chaque `on_shown`, `calculations.json` compris : les sources ne divergent pas après un enregistrement partiel ; l'onglet ne lit plus `app.data`.
- **D-015** *(revue, remarque REQ-004)* — le nombre affiché par domaine est son total ; il ne suit pas le filtre.

## 8. Hors périmètre

- Les six onglets d'*Actions* encore vides (`action_tabs.py`) et la reprise par eux du rôle de *Charges*.
- L'onglet *Formule* de la spec `2026-10-08-onglet-formule-domaines` (son lien avec la liste des variables d'un domaine).
- Modifier une variable depuis l'onglet (il reste un navigateur, sans `dirty`) ; la commande `eq` (reportée, `docs/open-questions.md`).
- Écrire les variables Typst dans `data/` (ARCH-002).
- Les domaines de `positions/<id>.json` (D-009) ; les gestes de copie dans la liste (D-008).
- Une procédure d'import depuis Excel ou une nouvelle commande de la CLI.

## 9. Idées non retenues comme exigences

- Aucune dans l'issue.

## 10. Questions

### Q-001 — Quels fichiers font la source « Woodcore » ?
- **Pourquoi elle compte** : l'issue nomme « charges, connecteurs, moments polaires, etc. » ; cinq fichiers de `data/` portent des `vars`, un seul est lu aujourd'hui. Le périmètre fixe le travail de lecture, de schéma et de tests.
- **Options** : **A (recommandée)** tout ce que Woodcore calcule hors d'Excel : les variables `python:`/`norm:` de `calculations.json`, plus `connections.json` (moments polaires), `connectors.json`, `scripts.json` et les domaines de `positions/<id>.json` ; **B** seulement ce que l'issue nomme : charges (python/norm), connecteurs, moments polaires — ni scripts ni domaines de position (ajoutables plus tard).
- **Réponse** : **A** (2026-10-08) — tout ce que Woodcore calcule hors d'Excel : `python:`/`norm:` de `calculations.json`, `connections.json`, `connectors.json`, `scripts.json`, domaines de `positions/<id>.json`.

### Q-002 — Comment la provenance est-elle affichée ?
- **Pourquoi elle compte** : la colonne « Document » dit déjà Export · CU · BP · RS ; la provenance demandée (Excel · Woodcore · Typst) est un autre axe, et les deux se recoupent pour Typst.
- **Options** : **A (recommandée)** une colonne **Provenance** (Excel · Woodcore · Typst) qui remplace « Document » ; pour une variable Typst elle précise le document (« Typst · RS »), et le filtre par document devient un filtre par provenance ; **B** garder « Document » et ajouter « Provenance » à côté (une colonne de plus, des deux axes visibles).
- **Réponse** : **A** (2026-10-08) — une colonne **Provenance** qui remplace « Document » ; le filtre par document devient un filtre par provenance.

### Q-003 — Comment choisit-on de filtrer toutes les variables ?
- **Pourquoi elle compte** : c'est la commande de T3, donc le geste de l'ingénieur.
- **Options** : **A (recommandée)** une case « Tous les domaines » à côté de la recherche, décochée par défaut (le filtre agit sur le domaine choisi) ; cochée, la liste montre aussi le domaine de chaque ligne ; **B** automatique : dès qu'on tape une recherche, elle porte sur toutes les variables, sans case (perd : filtrer dans un seul domaine) ; **C** une ligne « Toutes les variables » en tête du volet de domaines (perd : on ne voit plus d'un coup d'œil que la portée a changé quand on tape).
- **Réponse** : **A** (2026-10-08) — case « Tous les domaines » à côté de la recherche, décochée par défaut.

### Q-004 — Que reprend « Variables » de « Charges » avant sa suppression ?
- **Pourquoi elle compte** : l'issue ne parle que des *variables* ; *Charges* montre aussi autre chose — qui disparaît avec lui si rien ne le reprend.
- **Options** : **A (recommandée)** les variables **et leur traçabilité** (niveau, norme, classeur · feuille · cellule, formule de l'étape, choix, marque des résultats, bouton *Ouvrir le classeur*) dans le détail, et les appels de cas et de domaine (`show-calc`, `show-check`, `show-live-load`, boucle, tableaux de synthèse) en *Affichage* sur la ligne du domaine ; seuls les tableaux d'un cas restent au rapport (`show-calc`) ; **B** les variables seules, comme l'issue le dit : niveau, formule, choix, classeur à ouvrir, `show-calc` et résumés disparaissent avec l'onglet (les six onglets d'*Actions* les reprendront peut-être).
- **Réponse** : **A** (2026-10-08) — variables, traçabilité (niveau, norme, classeur · feuille · cellule, formule, choix, ★, *Ouvrir le classeur*) et appels de cas et de domaine en *Affichage* ; seuls les tableaux d'un cas restent au rapport.

### Q-005 — « Résultats seulement » (revue, ARCH-RISK-009 i)
- **Pourquoi elle compte** : *Charges* ouvrait sur les seuls résultats ; la liste plate les mêle aux entrées.
- **Options** : **A (recommandée)** marque ★ + case décochée ; B case cochée par défaut ; C rien.
- **Réponse** : **A** (2026-10-08) → D-007.

### Q-006 — Gestes de copie (revue, ARCH-RISK-009 ii)
- **Pourquoi elle compte** : double-clic / Ctrl+C / clic droit copiaient un appel dans *Charges*.
- **Options** : A (recommandée) les rétablir ; **B** accepter la perte.
- **Réponse** : **B** (2026-10-08) → D-008.

### Q-007 — Domaines de `positions/<id>.json` (revue, ARCH-RISK-003)
- **Pourquoi elle compte** : le fichier est vide par construction ; son lecteur ne serait prouvé que sur une donnée synthétique.
- **Options** : **A (recommandée)** le retirer de cette version ; B le garder.
- **Réponse** : **A** (2026-10-08) → D-009.

### Q-008 — Confirmer D-001 (revue)
- **Pourquoi elle compte** : l'autre lecture écrirait dans `data/`, contre `decisions.md`.
- **Options** : **A (recommandée)** la pièce jointe du PDF ; B un fichier dans `data/`.
- **Réponse** : **A** (2026-10-08) → D-010.

## 11. Critères d'acceptation

- [x] REQ-001 — trois volets de travail + volet d'options d'Affichage (D-011) ; état de séparateur d'une autre longueur ignoré
- [x] REQ-002 — plus d'arbre ; un volet de domaines avec nombre et provenance
- [x] REQ-003 — liste plate des variables du domaine choisi
- [x] REQ-004 — case « Tous les domaines », mémorisée
- [x] REQ-005 — les quatre fichiers (D-003/D-009) sont tous dans le modèle, lus sur disque
- [x] REQ-006 — provenance déduite à l'assemblage (précédence Typst, `woodcore:`), affichée ; préfixe inconnu = test rouge
- [x] REQ-007 — nom, symbole, valeur, appels ; traçabilité et appels de Charges repris (D-006, D-013) ; ★ et « Résultats seulement » (D-007)
- [x] REQ-008 — test d'exhaustivité vs `calculations.json`, vert avant la suppression
- [x] REQ-009 — `LoadsTab` et `tab_loads` disparus, suite verte, anciens réglages tolérés
- [x] REQ-010 — onglet présent dans CU, BP et RS
- [x] UI-001 — chaînes en trois langues
- [x] UI-002 — états vide / filtré / périmé / échec
- [x] UI-003 — vue mémorisée, ancienne forme lue
- [x] ARCH-001 — assemblage sans Qt, hors de l'onglet
- [x] ARCH-002 — rien écrit dans le projet
- [x] ARCH-003 — fichier absent avertit, malformé nomme sa cause
- [x] ARCH-004 — cache ancien lu sans exception
- [x] Documentation : `docs/ui/window.md` (onglet Variables, retrait de Charges, navigation Actions), `docs/domain/loads.md` si renvoi, spec soeur `2026-10-08-schema-actions-positions-affichage.md`, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en.
- [x] Tests : `tests/test_variables.py` étendu (+ fichier du test d'exhaustivité), `tests/test_action_tabs.py`, `test_modes_window.py`, `test_views.py`, `test_richtext.py`, `test_layout_store.py`, `test_chrome.py` adaptés ; la suite passe.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T0 | §3 (contexte) | contexte |
| T1 | REQ-001, REQ-007, UI-003 | capturé |
| T2 | REQ-002, REQ-003, UI-002 | capturé |
| T3 | REQ-004 | capturé (Q-003 → D-005) |
| T4 | REQ-005, REQ-006, D-001 à D-004 | capturé (Q-001, Q-002 répondues) |
| T5 | REQ-008, REQ-009, REQ-007 (Q-004 → D-006) | capturé, dépend de T4 |
| — | REQ-010, ARCH-001 à ARCH-004, CON-001 à CON-006 | inférés (marqués) |

### Points de la source non résolus

Aucun : Q-001 à Q-004 sont répondues (2026-10-08, toutes option A).

## 13. Revue d'architecture

Agent `architecture-reviewer`, 2026-10-08, sur la copie de travail (des pairs éditent `variables_tab.py`, `woodcore_gui.py`, `chrome.py`, `display_view.py` — commentaires RFEM/DSL seulement pour ce qui nous concerne).

**Verdict : APPROUVER AVEC RÉSERVES** — domaine sans Qt, rien écrit, version de cache existante, aucun schéma nouveau. Réserves levées par Q-005 à Q-008 et D-011 à D-015.

**Modules concernés.** `calc/variables.py` (`Variable` :128 gelée, `Registry` :165, `best`/`from_pdf`/`read`, cache `save`/`cached`, `CACHE_VERSION = 1` :77, écrit dans le fichier, vérifié à la lecture et en tête du `stamp` ; `_from_json` ignore les champs inconnus). `calc/tools/variables_tab.py` (`export_registry` :228 nomme `"{calcul} · {instance}"` et ne lit que `app.data` ; le séparateur a **déjà trois enfants** `[liste, détail⇄aperçu, options caché]` :306-310 ; `display_entries` :779). `calc/tools/woodcore_gui.py` (`LoadsTab` :1240-1664 et ses aides `parse_source` :962, `instance_workbook` :972, `load_groups` :977, `table_text` :1007, `var_commands`/`instance_commands`/`domain_commands` :1043-1081, `Details`/`esc` :1169-1203 ; `TABS` :2791, `NAV_GROUPS` :2820, `NAV_SECTIONS` :2833, `self.view` :2959, `refresh_tab` :3331, `rebuild` :3540 ; mots `tab_loads` :171/400/629). `calc/tools/chrome.py:29`, `calc/tools/action_tabs.py`, `calc/tools/layout_store.py`.

**Les fichiers de `vars`** (projet exemple, `_woodcore/data`) : `calculations.json` 1.4 — `domains.<calc>.instances.<inst>.vars`, `source` `excel:` (74), `python:` (12), `norm:` (58) ; `connections.json` 4.1 — `connections.<id>.vars`, `python:domains/connection.py`, domaine `connection · <id>` ; `connectors.json` 3.0 — `connectors.<id>.vars`, `woodcore:connectors/<id>.json` (11), `norm:` (6), `python:` (31), domaine `connector · <id>` ; `scripts.json` 1.0 — `scripts.<id>.vars`, `python:scripts/<id>.py`, domaine `script · <id>` ; `positions/<id>.json` — `domains: {}` toujours (retiré, D-009). Les mots `connection`/`connector`/`script` sont ceux de `calc-engine.typ` : `call_val(clé, "connection", id)` reste valide.

**À réutiliser.** `display_view.ViewPanes`/`install_display` (paramètre `centre=`), `cards`, `richtext.MathDelegate`, `views.DATA_VIEWS` ; de `LoadsTab` : la mise en forme de la source (`add_var` :1442), `details_var` :1554, `display_entries` :1593, `open_workbook` :1651 ; `validation.validate_structure` pour nommer le champ d'un fichier malformé ; le motif `VariablesError(message, code, **detail)`. `connector.EXPORT_FILE` existe ; `connection.py:644` et `script.py:191` écrivent le nom en dur.

**Risques et suite donnée.**
- ARCH-RISK-001 (important) — l'« ancien état à deux largeurs » n'existe pas ; garder 3 enfants écraserait le détail, `centre=1` cacherait la liste en *Affichage* → D-011, critère de REQ-001 réécrit.
- ARCH-RISK-002 (important) — un 4e préfixe `woodcore:` (`dowel.py:609`), aucun schéma n'énumère les préfixes → D-012, test de balayage, table documentée dans `data-contracts.md` §3.1.
- ARCH-RISK-003 (important) — `positions/<id>.json` vide par construction → Q-007, D-009.
- ARCH-RISK-004 (important) — une variable Typst peut porter une `source` `excel:` (`formula.typ:1070`) → précédence D-012.
- ARCH-RISK-005 (important) — `Variable` n'a ni `level` ni `choices` ; rien ne porte `results`, `steps[].formula`, `checks`, `workbook`, `sheet` → `Variable.level=None`, `choices=()` ; un `Domain` sans Qt (adresse `(calc, inst)`, origine, résultats, checks, classeur, feuille, formules) ; pas de bump de cache (ARCH-004 réécrite).
- ARCH-RISK-006 (important) — l'assemblage dans `calc/variable_sources.py`, table `FILE_SOURCES` → ARCH-001 réécrite.
- ARCH-RISK-007 (important) — mort / partagé / persistant de `LoadsTab`, clés de mots, `no_data` (`test_pdf_button.py:181`), textes d'`action_tabs`, ligne fine de `NAV_SECTIONS` → critères de REQ-009 ; `no_data` repris par *Variables* (ARCH-003).
- ARCH-RISK-008 (mineur) — réglages qui nomment `tab_loads` : lecteurs tolérants, pas de migration ; un test l'atteste.
- ARCH-RISK-009 (important) — « Résultats seulement », gestes de copie, boucle de domaine, synthèses → Q-005, Q-006, D-013.
- ARCH-RISK-010 (important) — la spec soeur `onglet-formule-domaines` (en implémentation) bâtit sur `selected_key()` / `variable(key)` et ajoute une source *Formules* → contrat figé : la clé `(source, domaine, nom)` et l'adresse `(calcul, instance)` gardent leur forme ; coordination avec la session paire avant d'éditer `variables_tab.py` (plan, étape 0). La spec soeur `schema-actions-positions-affichage` (D-005) et `decisions.md:198` sont mises en accord (CON-005, CON-006).
- ARCH-RISK-011 (mineur) — pas de collision exacte de noms, mais un même moment polaire a deux noms (registre / export) et trois « Rapport » (CU/BP/RS) → l'identité reste `(origine, domaine, nom)`, le libellé de provenance porte le document.
- ARCH-RISK-012 (mineur) — `vr_source` dit déjà « Provenance » pour la chaîne brute → renommée « Source » / « Quelle » / « Source » ; `vr_col_document`, `vr_any_document`, `SOURCE_CODES` supprimés avec la colonne.
- ARCH-RISK-013 (mineur) — erreurs indexées par document ; `calculations.json` venait de `app.data` → code `bad_file` (fichier, champ), D-014.

**Approche.** (1) modèle sans Qt et ses tests, exhaustivité verte ; (2) onglet ; (3) suppression de `LoadsTab` une fois (1) et (2) verts ; (4) documentation.

## 14. Plan d'implémentation

0. **Coordination** — `ListAgents` ; prévenir la session de la spec `onglet-formule-domaines` (et toute session qui édite `variables_tab.py`, `woodcore_gui.py`, `chrome.py`, `action_tabs.py`) : fichiers touchés, contrat figé `(source, domaine, nom)` / `(calcul, instance)`, ordre. Relire chaque fichier juste avant de l'éditer. *(CON-001, ARCH-RISK-010)*
1. **Provenance dans `calc/variables.py`** — `parse_source(source) -> (kind, workbook, sheet, cell)` (déplacée de `woodcore_gui`), `PROVENANCE` (`excel` → excel ; `python`/`norm`/`woodcore` → woodcore), `provenance_of(source)` ; `Variable.level=None`, `Variable.choices=()`. Tests (`tests/test_variables.py`) : table de provenance, cache de l'ancienne forme lu. *(REQ-006, ARCH-004, D-012)*
2. **`calc/variable_sources.py`** (nouveau, sans Qt) — `FILE_SOURCES` (calculations, connections, connectors, scripts ; noms de fichier lus des modules : `connection.EXPORT_FILE`, `script.EXPORT_FILE` ajoutés, `connector.EXPORT_FILE`), `Domain` (nom affiché, origine, adresse, variables, résultats, checks, classeur, feuille, formules par résultat), `instance_workbook` (déplacée), lecture de l'export → (domaines, avertissements, erreurs), domaines d'un registre Typst, provenance avec la précédence de D-012, erreurs `VariablesError("bad_file", path=, field=)` et absence → `no_data`. Tests (`tests/test_variable_sources.py`) : **exhaustivité REQ-008** (chaque `(calc, inst, nom)` de `calculations.json` avec nom, symbole, valeur, unité, désignation), `I_p` d'une connexion et une variable de connecteur présents, tous les préfixes de `source` de l'exemple connus, fichier absent, fichier tronqué nommé, arbre du projet inchangé (ARCH-002), import sans PySide6. *(REQ-005, REQ-008, ARCH-001 à ARCH-003, D-009, D-014)*
3. **Onglet `calc/tools/variables_tab.py`** — séparateur à 4 enfants (`centre=2, right=None`) ; volet de domaines (liste plate, nombre total, provenance, `no_data` si rien) ; liste plate (★, colonnes, colonne domaine si « Tous les domaines ») ; barre de filtre : recherche, « Tous les domaines », « Résultats seulement », unité, **provenance** (remplace le filtre de document) ; carte de détail : nom, symbole, valeur, unité, désignation, description, provenance, source, niveau, norme, classeur · feuille · cellule, formule, choix, bouton *Ouvrir le classeur* ; `display_entries` par type de ligne (D-013) ; `view_state`/`restore` avec garde de longueur et clés anciennes tolérées ; mots `vr_` fr/de/en (`vr_source` renommé, clés de la colonne Document retirées). Tests : `tests/test_variables.py` (arbre → domaines + liste, portée du filtre, ★, provenance, parité des appels avec `LoadsTab`, état ancien), `tests/test_modes_window.py:302-332`, `tests/test_richtext.py` (délégué de la liste plate). *(REQ-001 à REQ-004, REQ-006, REQ-007, REQ-010, UI-001 à UI-003, D-004 à D-008, D-011, D-015)*
4. **Suppression de *Charges*** (seulement après 1–3 verts, exhaustivité comprise) — `LoadsTab` et ses aides mortes, `TABS`, `NAV_GROUPS`, `NAV_SECTIONS` (ligne fine → `tab_combinations`), `chrome.ICONS["tab_loads"]`, `self.view`/`app.view` dans `refresh_tab`/`rebuild`, clés de mots propres à `LoadsTab` (trois langues), imports devenus inutiles ; `action_tabs.py` renvoie à *Variables*. Tests : `test_action_tabs.py`, `test_views.py`, `test_modes_window.py:123-207`, `test_richtext.py:159-194`, `test_chrome.py:89`, `test_layout_store.py:87`, `test_pdf_button.py:181`, `test_variables.py:747`, `test_i18n.py` ; un test de réglages anciens (`views`, `layouts` nommant `tab_loads`). *(REQ-009, ARCH-RISK-007/008)*
5. **Documentation** — `docs/ui/window.md` (onglet Variables, retrait de Charges, groupe Actions), `docs/decisions.md` (nouvelle entrée : *Charges* supprimé au profit de *Variables*, ce qui tranche la réserve de `:198`), `docs/architecture/layout.md` (module neuf), `docs/architecture/data-contracts.md` §3.1 (préfixes de `source` et provenance), `docs/domain/loads.md` (renvois à l'onglet), spec soeur `2026-10-08-schema-actions-positions-affichage.md` (note sous D-005), `CHANGELOG.md`, page « Nouveautés » fr/de/en. *(CON-005, CON-006)*
6. **Suite complète** — `python tests/run_tests.py` sans tampon dans un fichier, noms des échecs relevés ; `test_the_export_is_reproducible` peut rougir une fois à cause de l'arbre git sale. *(CON-003)*

## 15. Vérification

Agent `requirements-verifier` (Sonnet), deux tours, le 2026-10-08, sur l'arbre de travail contre `b462466` ; les modifications non commitées des autres sessions (onglet *Formule*) sont hors de cette spec.

**Tour 1** — 0 ❌, 5 ⚠️ : synthèses de charges limitées aux cas de charges (D-013 précisée, signalé à l'ingénieur) ; huit clés `col_*` orphelines et un commentaire de `NAV_SECTIONS` périmé ; pas de test de disposition mémorisée nommant `tab_loads` ; lien `completed/` du CHANGELOG avant le déplacement ; cinq comportements observés par sonde mais tenus par aucun test. Tous corrigés.
**Tour 2** — 1 ✅, 4 ⚠️ mineurs : trois clés orphelines de plus (`results_only`, `details`, `hint`), le décompte du CHANGELOG, trois phrases de doc nommant *Charges* comme existant (`window.md` ×2, `command-docs.md`), `SL-01` → `SL` au critère de REQ-003, deux assertions plus strictes (une ligne par domaine lu ; aucun onglet fantôme avec d'anciens réglages). Tous corrigés après le second tour, tests relancés verts (ci-dessous) ; pas de troisième tour (la skill en limite le nombre à deux).

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `variables_tab.py` `__init__` : trois volets + `install_display("tab_variables", centre=2, right=None)` ; `test_the_tab_has_three_panes_and_the_display_a_fourth`, `test_in_affichage_the_domains_and_the_variables_stay`, `test_a_view_of_the_tree_s_time_is_read_without_harm` |
| REQ-002 | ✅ | `build_domains` (arbre plat), `fill_domains` ; `test_the_domains_are_a_pane_of_their_own`, `test_the_real_export_is_listed_domain_by_domain_in_its_own_order` (une ligne par domaine lu, compte total) |
| REQ-003 | ✅ | `fill_list` ; `_rows` exige `childCount() == 0` ; ordre de `snow-load · SL` = `calculations.json` (même test) ; `test_richtext.test_the_symbols_of_the_loads_are_set_as_mathematics` |
| REQ-004 | ✅ | `all_domains_box` ; `test_the_filter_reaches_the_domain_chosen_or_every_domain`, `test_the_tab_carries_its_view_through_a_rebuild` |
| REQ-005 | ✅ | `variable_sources.FILE_SOURCES`, `read_export` ; `test_the_polar_moments_the_connectors_and_the_scripts_are_listed`, `test_the_export_is_read_again_at_every_showing` |
| REQ-006 | ✅ | `variables.PROVENANCE`/`provenance_of`, `variable_sources.provenance` ; `test_a_source_prefix_means_one_provenance`, `test_a_registry_variable_is_typst_whatever_its_source_says`, `test_every_source_of_the_example_has_a_known_provenance`, `test_every_source_is_listed_with_its_provenance` |
| REQ-007 | ✅ | `show_selected`, `display_entries` ; `test_the_detail_carries_what_the_loads_tab_showed`, `test_the_export_offers_the_calls_the_loads_tab_offered`, `test_views.test_the_loads_offer_each_rows_commands_a_value_a_case_and_a_category` ; synthèses sur les cas de charges seulement (D-013 précisée) |
| REQ-008 | ✅ | `test_variable_sources.test_no_variable_of_the_loads_tab_is_missing` (>100 variables, cinq champs + niveau + résultats), vert avant la suppression |
| REQ-009 | ✅ | `LoadsTab` et ses aides, 57 clés ×3 langues, icône, `app.view` retirés ; `grep LoadsTab\|tab_loads calc tests` → seulement `test_views.py` (réglages anciens, voulu) ; `test_views.test_a_view_that_compiles_compiles_nothing_while_the_window_is_built` (vues et disposition nommant `tab_loads`, aucun onglet fantôme) ; `test_action_tabs`, `test_chrome`, `test_layout_store`, `test_pdf_button`, `test_i18n` verts |
| REQ-010 | ✅ | `DOCUMENT_TABS` ; `test_modes_window.test_each_document_shows_its_own_modules` |
| UI-001 | ✅ | `variables_tab.STRINGS` fr/de/en ; `test_the_tab_speaks_the_window_three_languages`, `test_every_refusal_the_module_can_raise_has_a_sentence_in_three_languages` |
| UI-002 | ✅ | `empty_text`, bannière ; `test_a_project_not_exported_says_so`, `test_a_file_of_the_export_that_cannot_be_read_is_named_in_the_banner`, `test_the_tab_keeps_what_it_had_when_a_reading_fails`, `test_a_first_reading_that_fails_leaves_the_bar_saying_so` |
| UI-003 | ✅ | `view_state`/`restore` ; tests de vue ci-dessus |
| ARCH-001 | ✅ | `calc/variable_sources.py` ; `test_the_module_is_qt_free`, `test_the_export_file_names_are_the_modules_own` ; aucun `export_registry` restant |
| ARCH-002 | ✅ | `test_reading_writes_nothing_into_the_project`, `test_building_and_showing_the_tab_writes_nothing` |
| ARCH-003 | ✅ | `test_a_project_not_exported_is_missing_and_never_an_error`, `test_a_broken_file_is_named_and_the_others_are_read_all_the_same`, `test_a_file_against_its_schema_names_the_field` |
| ARCH-004 | ✅ | `CACHE_VERSION = 1` inchangé ; `test_the_new_fields_do_not_reach_the_cache` |
| CON-001 à CON-006 | ✅ | éditions ciblées, coordination avec la session *Formule* (contrat respecté, sa ligne `FILE_SOURCES` gardée) ; documentation : `window.md`, `decisions.md`, `layout.md`, `data-contracts.md`, `open-questions.md`, `command-docs.md`, spec soeur, `CHANGELOG.md`, « Nouveautés » 0.117.0 fr/de/en |
| §8 Hors périmètre | ✅ | ni onglets *Actions*, ni *Formule*, ni écriture dans `data/`, ni `positions/<id>.json`, ni geste de copie |

**Suite complète** : lancée deux fois le 2026-10-08, en environnement partagé avec d'autres sessions. Fichiers de cette spec tous verts : test_variable_sources 16, test_variables 56, test_views 9, test_i18n 21, test_modes_window 18, test_richtext 9, test_action_tabs 4, test_chrome 9, test_layout_store 4, test_pdf_button 9. Échecs étrangers à cette spec, nommés : test_window ×4 (FormulaTab, spec Formule), test_commands.test_the_frozen_examples_run_against_the_current_engine (examples/lib/ ≠ lib/calc-engine.typ, timber.typ, modifiés par d'autres sessions), test_engine_check ×2 (avertissement « rfem_models / rfem_export ignored » de la spec Formule/RFEM), test_fire_tab.test_what_the_delimiting_had_is_gone… et test_panes.test_the_bar_wraps_and_loses_no_tool (fire_tab.py, plan_tab.py modifiés par d'autres sessions), test_position_list ×13 (EngineDecision) ; test_editor dépasse 15 min (tinymist). À 19:38 un moteur a été synchronisé dans le projet exemple committé (tests/projet-exemple/_woodcore/calc, lib, VERSION — hors de cette session) : conftest copie calc/ sans VERSION et tout fichier lancé ensuite (test_project … test_window, 31 fichiers) s'arrête à l'import sur EngineDecision ; ces fichiers n'ont donc pas pu être rejoués en fin de suite (test_window et test_views l'avaient été plus tôt).

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-08 | draft | spécification extraite de l'issue 13 (T0–T5) ; 10 REQ, 3 UI, 4 ARCH, 6 CON, 4 questions |
| 2026-10-08 | specified | Q-001 à Q-004 répondues (toutes option A) ; D-003 à D-006 ; aucune question ouverte |
| 2026-10-08 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (13 risques) ; Q-005 à Q-008 répondues (A, B, A, A) → D-007 à D-010 ; D-011 à D-015 prises sur la revue ; REQ-001/005/006/007/009, ARCH-001/003/004, CON-006 précisées ; plan en 7 étapes (0–6) |
| 2026-10-08 | approved | approuvée par l'ingénieur ; implémentation lancée (étape 0) |
| 2026-10-08 | implementation | étape 0 : sessions « Onglet formule » (préserver ses éditions de woodcore_gui/chrome/variables_tab ; elle ajoute mode choix et source Formules APRÈS la réécriture, contrat selected_key/variable/address/select_key) et « issue #9 » (pas de recouvrement) prévenues. Étapes 1–2 faites : variables.py (PROVENANCE, parse_source, provenance_of, Variable.level/choices), variable_sources.py (FILE_SOURCES, Domain, read_export, registry_domains, provenance, instance_workbook), EXPORT_FILE dans connection.py et script.py ; tests/test_variable_sources.py 16/16 vert (exhaustivité REQ-008 comprise). Reste : étapes 3–6 |
| 2026-10-08 | implementation | étape 3 faite : variables_tab.py réécrit (4 enfants centre=2, volet de domaines plat, liste plate ★, filtres recherche/unité/provenance, « Tous les domaines », « Résultats seulement », détail avec traçabilité et « Ouvrir le classeur », display_entries par type de ligne, view_state tolérant) — REQ-001 à 004, 006, 007, 010, UI-001 à 003. Tests : test_variables 53/53, test_modes_window (test réécrit), test_views 9/9, test_richtext, test_autosave verts. Environnement : PySide6_Essentials/shiboken6 6.12.0 installés par un tiers à 16:44, remis à 6.11.2 (requirements.txt) avec l'accord de l'ingénieur. Reste : étapes 4–6 |
| 2026-10-08 | implementation | étape 4 faite : LoadsTab et ses aides mortes retirés de woodcore_gui.py (value_with_unit, is_number, parse_source, instance_workbook → variable_sources, load_groups, ACTIONS, table_text, *_commands, esc, Details, import html, 4 imports Qt), tab_loads de TABS/NAV_GROUPS/NAV_SECTIONS (ligne fine → tab_combinations), self.view/app.view, 46 clés de mots ×3 langues, chrome.ICONS[tab_loads] ; action_tabs.py renvoie à « Variables » ; tests adaptés (action_tabs, chrome, layout_store, pdf_button, richtext, views — le test « Affichage » des charges porté sur Variables —, modes_window, variables) : tous verts ; réglages anciens nommant tab_loads tolérés (test_views). Échecs restants dans test_i18n (fm_cmd_var) et test_window (FormulaTab) : ceux de la spec soeur Formule, en cours dans une autre session. Reste : étapes 5–6 |
| 2026-10-08 | testing | étape 5 faite : docs/ui/window.md (onglet Charges devenu « ce qu'il montrait jusqu'à v0.117 », table des appels retirée, groupe Actions, trois documents, paragraphe « Three panes and every source »), docs/decisions.md (nouvelle entrée + réserve de l'entrée « Actions » tranchée), docs/architecture/layout.md, data-contracts.md (préfixes de source), open-questions.md (question close), spec soeur (note sous D-005), CHANGELOG.md, « Nouveautés » 0.117.0 fr/de/en ; « v0.118 » corrigé en v0.117 (la prochaine version est 0.117.0). Étape 6 : suite complète lancée |
| 2026-10-08 | verification | tour 1 : 0 ❌, 5 ⚠️ corrigés ; tour 2 : 4 ⚠️ mineurs corrigés ; test_variables, test_views, test_i18n relancés verts |
| 2026-10-08 | completed | §11 coché ; spec déplacée dans docs/requirements/completed/ ; rien n'est commité |
