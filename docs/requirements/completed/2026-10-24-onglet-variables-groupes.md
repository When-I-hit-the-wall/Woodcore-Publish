---
id: 2026-10-24-onglet-variables-groupes
titre: Onglet Variables — menu des onglets, filtre dans la recherche, liste groupée par domaine, choix multiple
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-25
source: issue GitHub #114 (prototype validé par l'ingénieur le 24.10.2026, « Onglet Variables », version 2)
docs: [docs/ui/tab-variables.md, docs/architecture/principles.md, docs/architecture/layout.md, docs/ui/building-a-tab.md, docs/domain/variable-links.md, docs/decisions.md]
---

# Onglet Variables — menu des onglets, liste groupée par domaine, choix multiple — Spécification

## 1. Objectif

Refaire l'onglet « Variables » (groupe Référence, `tab_variables`) d'après le prototype validé : à gauche un menu des onglets de Woodcore, la source et les domaines du filtre rangés sous le titre de leur onglet ; au centre une barre de recherche qui porte le filtre en étiquettes amovibles et une liste toujours groupée par domaine, le symbole seul, des largeurs réglables et gardées, l'encadré des résultats et le choix multiple « comme dans Windows » avec « Copier les n commandes » ; à droite une fiche qui ouvre l'onglet où la valeur a été calculée, donne la commande à copier et dit où le même calcul se trouve ailleurs. La vue « Affichage » disparaît. L'onglet sert à trouver une valeur que le projet a calculée, pour l'imprimer ailleurs dans le rapport ou pour qu'un champ d'un autre onglet la suive (issue #42).

## 2. Source

La source, mot pour mot et coupée en points T, est dans [docs/history/2026-10-24-onglet-variables-groupes-source.md](../../history/2026-10-24-onglet-variables-groupes-source.md) (déplacée le 24.10.2026 pour tenir la spec sous 100 KB ; rien n'y est changé).

## 3. Exigences fonctionnelles

État actuel relevé dans le code (master `a9cae26`) : `variable_sources.Domain` (`name`, `origin`, `variables`, `kind`, `address`, `label`, `results`, `checks`, `workbook`, `sheet`, `formulas`, `file`) n'a **ni onglet, ni lien d'un domaine à ses sources sœurs** ; `registry_domains` liste le domaine vide (`variables.REPORT_DOMAIN`) de chaque document ; les « fichiers » du prototype sont les domaines d'origine `formulas` (`formula_domain.variable_domains`, qui connaît le fichier de chaque domaine, `domain.path`) ; `VariablesTab` est un `display_view.DisplayTab` à `VIEWS = views.DATA_VIEWS`, sa liste est un `QTreeWidget` plat à `SingleSelection`, le ★ de `RESULT_MARK` marque un résultat, les colonnes sont `ResizeToContents`, et `view_state` garde le splitter, la recherche, l'unité, la provenance, « Tous les domaines », « Résultats seulement » et le choix. Le graphe de dépendances (issue #71) offre déjà `MainWindow.open_object("<kind>:<ident>")` : l'onglet dont la classe porte `GRAPH_KIND` et dont `lists_object(ident)` vaut vrai passe devant et ouvre le cas (`tab_host.open_object`) ; `GRAPH_KIND` existe pour `load` (`calc_tab.CalcTab` : neige, vent, poids propre, charge utile), `connector`, `connection`, `check` (vérifications bois), `steel`, `fire`, `plan`, `position`, `schema`, `statics`, et **n'existe pas** pour l'onglet Python ni pour l'onglet Formule/Domaines (tous deux `source_editor`, `GRAPH_KIND = None`) ni pour les onglets réservés (Séisme, Charge utile quand elle est « réservée »). `begin_pick`/`end_pick`, `selected_key`, `variable`, `address`, `select_key` sont le contrat que `MainWindow.begin_variable_pick` et les onglets à champs liés lisent ; aucun autre onglet ne lit `tree` ni `domain_list`.

### REQ-001 — `Domain.tab` : l'onglet qui calcule un domaine
- **Exigence** : chaque `variable_sources.Domain` doit porter la clé de l'onglet de Woodcore qui le calcule (`tab`, une clé de `tab_registry.SPECS`), remplie sans heuristique : pour un domaine de l'export, par la sorte de son calcul (`snow-load` → Neige, `wind-load` → Vent, `dead-load` → Poids propre et surcharge, `live-load` → Charge utile, `connector` → Moyens d'assemblage, `connection` → Moments polaires, `script` → Python) ; pour un domaine de la source « fichier » (origine `formulas`), par **le calcul dont il est le fichier** : la paire (sorte, identifiant) que `data/domain-files.json` associe au chemin de son fichier (`formulas.json`), puis, pour une vérification, la **sorte** (`kind`) de son enregistrement de `data/checks.json` ou de `data/steel.json` et la présence de `fire` (une vérification au feu → Résistance au feu) — **jamais le nom du dossier** : il ne dit pas le feu (FE-01 et FE-02 de l'exemple sont écrites sous `Timber-checks/Bending/` et `Buckling/`) et il suivra la fusion des onglets de #112 —, et un domaine de l'onglet Domaines (dans `formulas.json`, absent de `domain-files.json`) → Référence › Domaines ; pour un domaine d'un document compilé, par REQ-002. Les tables « sorte de calcul → clé d'onglet » et « sorte de vérification → clé d'onglet » sont déclarées **une fois**, sans Qt (`calc/variable_calc.py`, ARCH-008) ; un test (Qt, car `tab_registry` importe tous les onglets) tient chacune de leurs clés à une `TabSpec` existante, et un autre tient le `tab` d'un domaine à l'onglet dont le `lists_object` répond de son nœud (REQ-009). Un domaine d'export ou de fichier dont le calcul n'est pas trouvé garde `tab = None` et est rangé sous une entrée « Sans onglet » du menu, jamais écarté en silence.
- **Source** : T42, T46, T47, T50, revue (ARCH-RISK-001) ; principes « une seule source », « pas de valeur codée en dur » (CLAUDE.md)
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_variable_sources.py` et `tests/test_variable_calc.py` lisent les domaines du projet d'exemple (export et fichiers) et affirment que chacun a un `tab` connu de `tab_registry` (FE-01 et FE-02 → `tab_mc_fire`, ZT-01 → `tab_mc_tension`, `poutre-p1` → `tab_formula`, `snow-load · SL` → `tab_ac_snow`) ; une clé inconnue dans une table fait échouer le test en nommant la sorte ; aucun domaine d'export ou de fichier de l'exemple n'a `tab = None`.

### REQ-002 — Rapprocher un domaine de document de son calcul, sans heuristique de nom
- **Exigence** : un domaine d'un document compilé doit être rattaché à son calcul — et donc à son onglet, à sa source qui calcule et aux sources sœurs — par une donnée que Woodcore a écrite, jamais en devinant par la ressemblance de son nom avec celui d'un cas ; un domaine du document qu'aucune donnée ne rattache (« S10 - 1 kN Mitte ») est un domaine que le document déclare lui-même (rangé sous « Document › <le document> » du menu, UI-002). **La donnée retenue (Q-001, A) est `data/domain-files.json`** : le nom d'un domaine de document est rattaché au calcul dont l'identifiant est ce nom **dans la table que Woodcore a écrite** — (sorte, identifiant) de `domain-files.json`, complétée, pour un domaine de l'onglet Domaines que cette table ne porte pas, par les identifiants de `formulas.json` (même nature : un index de fichiers que l'export écrit et valide) — ; un nom présent dans deux sortes, ou dans aucune table, reste sans calcul et un test le signale. Rien n'est changé dans `lib/`, dans le cache de lecture ni dans la pièce jointe du PDF. Le rapprochement se fait à l'assemblage (`variable_calc.assemble`), après la lecture, jamais en lisant la ressemblance de deux noms ; il reste un appariement par identifiant (le coût accepté par l'ingénieur) : un domaine que le rapport déclare à la main sous le nom d'un fichier de Woodcore serait pris pour lui.
- **Source** : T42, T43, T50, Q-001, revue (ARCH-RISK-004)
- **Priorité** : doit
- **Critère d'acceptation** : un test sur le projet d'exemple : chaque domaine de document de `SL`, `A1`, `BI-01`… a le `tab` et les sœurs que la table dit ; `S10 - 1 kN Mitte`, déclaré à la main, n'en a pas ; un identifiant mis dans deux sortes d'une table fabriquée reste sans calcul et le test le nomme ; renommer un cas dans l'export sans toucher au document ne rattache plus le domaine (aucun appariement par ressemblance de nom).

### REQ-003 — Une ligne par source, la source qui calcule et celles qui rappellent
- **Exigence** : Woodcore doit garder une ligne (un domaine) par source — export, fichier, document — et savoir, pour tout domaine, les autres domaines qui portent le même calcul. La **source qui calcule** est l'export s'il a la valeur, sinon le fichier, sinon le document ; les autres la rappellent. Un domaine « imprimé » est un domaine du calcul dont un document compilé et lu a un domaine sœur ; tant qu'aucun document n'est lu, l'impression est **inconnue** et n'est pas dite absente. Le calcul de chaque domaine est identifié par une paire (sorte, identifiant) (`CalcRef`), la même pour ses trois sources, et le nœud du graphe de dépendances qu'elle nomme est celui de `dependency_graph.target` (aucune seconde table de nœuds).
- **Source** : T7, T23, T39, revue (ARCH-RISK-005)
- **Priorité** : doit
- **Critère d'acceptation** : test sans Qt : pour `SL` du projet d'exemple, la source qui calcule est l'export, les sœurs sont le fichier et le document, `imprimé` est vrai ; pour un domaine d'export sans sœur dans un document lu, `imprimé` est faux ; documents non lus, `imprimé` est inconnu.

### REQ-004 — Un résultat est marqué dans chaque source qui rappelle le calcul
- **Exigence** : une variable d'un domaine qui rappelle un calcul doit être un résultat si le calcul qui la porte la déclare comme telle (`results` de l'export ; η d'une vérification), quelle que soit la source dans laquelle elle est listée ; le q<sub>k</sub> du fichier « A1 » est marqué comme celui de l'export. **Les clés de résultat d'un calcul sont déclarées une fois** : celles que l'export déclare (`results` de l'instance) quand le calcul y a un domaine, et, pour une vérification (bois ou acier), qui n'en déclare aucune dans `checks.json` ni `steel.json`, la clé `eta` que tous ses modules écrivent en dernière ligne (`member_check`, `steel_check`) — une constante nommée, tenue par un test à chaque fichier de vérification de l'exemple (ARCH-012). Un domaine qui rappelle le calcul reçoit ces clés dans son `results` à l'assemblage.
- **Source** : T32, T44 (défaut 5), revue (ARCH-RISK-003)
- **Priorité** : doit
- **Critère d'acceptation** : test : pour `A1`, la variable `q_k` est un résultat dans le domaine d'export, dans celui du fichier et dans celui du document ; « Résultats seulement » les garde tous trois.

### REQ-005 — Les domaines racines des documents ne sont plus listés
- **Exigence** : `variable_sources.registry_domains` ne doit plus rendre le domaine vide (`variables.REPORT_DOMAIN`) d'un document ; ses variables ne sont plus listées ni comptées.
- **Source** : T10, T44 (défaut 3), T46
- **Priorité** : doit
- **Critère d'acceptation** : test : un registre à domaine vide et à domaine nommé ne rend que le domaine nommé ; sur le projet d'exemple, après lecture des trois documents, l'onglet compte **918 variables dans 75 domaines** (chiffres de l'issue, à remesurer à l'implémentation).

### REQ-006 — La commande d'une variable selon sa source, et ce qu'il faut inclure
- **Exigence** : Woodcore doit composer, dans un module sans Qt (`calc/variable_card.py`, qui appelle les `call_*` de `build_reference_calls` et `formula_domain.include_call`, sans en écrire un second : voir ARCH-001), la commande à copier et la phrase « ce qu'il faut inclure avant » d'une variable selon la source du domaine : export `#var(clé, domain: (calcul, cas))`, rien à inclure ; fichier `#var(clé, domain: "id")` avec `#include domain-file(sorte, id)` (une charge : `domain-file("snow-load", "SL")` ; un domaine de l'onglet Domaines : `#include "/Domains/<id>.typ"`) ; document `#var(clé, domain: "nom")`, « la ligne doit être plus bas que le domaine ». Le domaine entier d'un domaine choisi seul donne `#include domain-file(…)` quand il y en a un. La copie de plusieurs variables met **une ligne `#var` par variable, dans l'ordre de la liste affichée**, sans les lignes « à inclure ».
- **Source** : T34, T37, T40
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_variable_card.py` pour les trois sources et pour un domaine entier (et `tests/test_call_command.py` inchangé) ; la copie de trois variables d'ordre mélangé rend trois lignes dans l'ordre de la liste ; aucune variable sans nom de domaine ne reçoit de commande (comme `call_var_registry` aujourd'hui).

### REQ-007 — Le contrat lu par les autres onglets, avec un choix multiple
- **Exigence** : `selected_key()` doit rendre la **dernière variable cliquée** (la clé `(origine, domaine, nom)`, `nom` à `None` pour un domaine choisi seul), comme avant ; une méthode nouvelle `selected_keys()` rend toutes les variables cochées dans l'ordre affiché ; `variable`, `address` et `select_key` gardent leur sens ; aucun lecteur existant (`MainWindow.begin_variable_pick`, `linkable_spin`, `formula_tab_blocks`, `statics_tab_properties`, `text_pane`) n'est modifié. Le lecteur caché de la palette de commandes (`command_palette._palette_show_in`) lit l'attribut `search` de l'onglet et, s'il est un `QLineEdit`, y met le texte : `search` reste un `QLineEdit` — celui de la barre à étiquettes — et le texte ajouté se cherche **dans** le filtre déjà posé. (Décision inférée de T50, la réponse la plus sûre : voir §7, D-8.)
- **Source** : T33, T34, T50, revue (ARCH-RISK-007)
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_variables.py` et `tests/test_linkable_spin.py` passent sans modification de leurs appels ; un test choisit trois variables avec Ctrl+clic et lit `selected_key()` = la dernière, `selected_keys()` = les trois dans l'ordre de la liste ; `tests/test_command_palette.py` (inchangé) passe et un test y voit le texte d'une variable de la palette arriver dans `search`.

### REQ-008 — « Choisir pour un champ » : une valeur, seulement les valeurs acceptées
- **Exigence** : pendant `begin_pick`, le choix multiple doit être coupé (un champ suit une valeur) : pas de cases, pas de barre « Copier les n commandes », un clic choisit une variable ; le menu des onglets, la source, la liste des domaines, les nombres et la liste ne comptent et n'offrent que les variables que `accept(var, domain)` (`variable_sources.linkable`) accepte, donc jamais celles d'un document compilé ; la fiche porte l'encadré « <champ> de <vérification> · suivra <variable> de <cas> · **Importer** », et une valeur refusée dit pourquoi ; le choix terminé (importé ou abandonné, Échap), tout est de nouveau offert et les cases reviennent. Pendant le choix, la fenêtre a mis la navigation hors service (`MainWindow.begin_variable_pick`) : « Ouvrir l'onglet » est donc inactif, son infobulle le disant, et la sélection multiple d'avant le choix est gardée mais ne se voit pas (elle revient avec les cases).
- **Source** : T41, T50, revue (ARCH-RISK-006)
- **Priorité** : doit
- **Critère d'acceptation** : test : pendant le choix d'un champ en kN, un domaine d'un document n'est pas listé, le menu n'a que des nombres de la bonne dimension, Ctrl+clic ne choisit pas deux variables, « Ouvrir l'onglet » est inactif avec son infobulle, « Importer » rend la clé choisie ; le choix terminé, la liste est complète et la sélection d'avant revenue.

### REQ-009 — « Ouvrir l'onglet » : l'onglet qui calcule, ouvert sur le cas
- **Exigence** : Woodcore doit, sur « Ouvrir l'onglet … ↗ » (fiche d'une variable ou d'un domaine), amener devant l'onglet de `Domain.tab` de la **source qui calcule** (même si la variable a été choisie dans le document qui la rappelle) et y ouvrir le cas, en réutilisant `MainWindow.open_object` et `GRAPH_KIND`/`lists_object`/`open_object` des onglets (aucun second mécanisme de navigation). Le cas se choisit ; la **ligne** précise du cas n'est choisie que là où l'onglet sait le faire. **Q-002 (A)** : pour Python et Formule/Domaines, qui n'ont pas de `GRAPH_KIND` (`source_editor`), le bouton amène l'onglet devant sans ouvrir de cas (#113 pourra leur donner un `open_object`) ; pour un domaine que le document déclare lui-même, ou un onglet réservé (Séisme, Charge utile tant qu'elle l'est, Combinaisons, Torsion, Aptitude au service), il reste **inactif** et son infobulle dit pourquoi (règle v0.47). Il est aussi inactif quand l'onglet n'est pas dans le document montré (`MODE_TABS` : Neige n'est pas dans la convention d'utilisation), quand le document n'est pas encore fait (`available`) et pendant « Choisir pour un champ » (REQ-008). Le nœud du cas est celui de `dependency_graph.target` (REQ-003) ; le bouton passe par deux méthodes publiques nouvelles de la fenêtre, `can_open_tab(key)` (rend la raison de l'inactivité) et `show_tab(key, node=None)`, et jamais par `app.tabs` (ARCH-010).
- **Source** : T16, T36, T40, T46, T50, Q-002, revue (ARCH-RISK-006)
- **Priorité** : doit
- **Critère d'acceptation** : test : le bouton d'une variable de `snow-load · SL` met l'onglet Neige devant avec le cas `SL` ouvert ; pour une variable de `BI-01`, l'onglet Flexion ouvre `BI-01` ; pour `FE-01`, l'onglet Résistance au feu ; choisie dans le document, la même variable ouvre toujours l'onglet de l'export ; Python et Domaines passent devant sans cas ; un domaine du document, un onglet réservé, un onglet absent du document montré, un document non fait et le choix d'un champ donnent un bouton inactif dont l'infobulle dit pourquoi ; pour tout domaine de l'exemple qui a un nœud, l'onglet de `Domain.tab` est celui dont `lists_object(nœud)` répond.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Trois volets, une seule vue, bandeau et lecture inchangés
- **Exigence** : l'onglet doit avoir trois volets (`QSplitter`) — domaines à gauche, variables au centre, fiche à droite — et **une seule vue** : plus de « Données · Affichage », plus de `VIEWS = views.DATA_VIEWS`, de `install_display`, de `display_entries` ni de `chosen`. Le bandeau, « Relire les documents », le cache, la pièce jointe du PDF, la lecture dans un fil et le message d'une lecture qui échoue ne changent pas ; l'onglet reste un navigateur sans `dirty`.
- **Source** : T9, T19, T44 (défaut 8)
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_window.py` traite l'onglet comme un onglet sans vues (aucun sélecteur de vues) ; `tests/test_variables.py` garde « no dirty », la lecture une seule fois, l'automatique éteinte pour la suite et la lecture qui échoue ; le bouton « Relire » dit son coût.

### UI-002 — Le menu des onglets
- **Exigence** : le volet de gauche doit commencer par un bouton qui ouvre une liste en arbre « Tous les onglets » (par défaut) de la navigation de Woodcore — groupes, sections, onglets, dans leur ordre et leurs mots, **lus de `tab_registry.NAV_GROUPS` et `NAV_SECTIONS` et des mots de la fenêtre au moment de l'ouverture**, sans en recopier la liste — plus, dans le groupe « Document », **une entrée par document fait du projet** (« Rapport de statique », « Base de projet », « Convention d'utilisation », leurs noms par `documents.mode_name`) pour les domaines que ce document déclare lui-même (une seule entrée « Rapport de statique » rangerait sous un faux nom ceux d'un autre document), et « Sans onglet » pour un domaine dont le calcul n'est pas trouvé (REQ-001). Le modèle du menu (sans Qt) **reçoit** la navigation — groupes, sections, onglets, titres — de l'onglet, qui la lit de `tab_registry` : il n'importe pas `tab_registry`, qui importe tous les onglets, donc Qt. La règle des sections (un `NAV_SECTIONS[clé]` ouvre une section jusqu'à la clé suivante qui en a une, `""` ne dit qu'un trait) est écrite une fois dans le modèle et tenue égale à celle que la fenêtre applique à sa navigation par un test (ARCH-RISK-002). Un onglet qui n'est pas dans le document montré garde son entrée et ses nombres : seul « Ouvrir l'onglet » le sait (REQ-009). Choisir un groupe ou une section prend tous ses onglets. Chaque entrée dit son nombre de variables **dans la source choisie** ; une entrée à zéro est grisée et ne se choisit pas. Échap ou un clic ailleurs ferme le menu. Un onglet réservé ou qui n'existe pas encore n'a pas d'entrée utile (zéro, grisée). **La forme (revue, ARCH-007)** : une liste en arbre dans un popup (`Qt.Popup`, comme le fait `notices_ui`), tout visible d'un coup comme le prototype, placée sous le bouton par `place` (`norm_bubble`, puis `hover_bubble` quand #115 l'y a migrée) ; pas de `QMenu` à sous-menus, qui cache les nombres derrière un survol.
- **Source** : T12, T20, T21, T46, T50, revue
- **Langues** : fr / de / en (les mots viennent de la fenêtre ; « Cisaillement » suit `tab_mc_shear`, voir CON-003)
- **Critère d'acceptation** : test sur le modèle du menu (sans Qt, la navigation donnée en argument) : les entrées sont celles qu'on lui donne, dans leur ordre, sections comprises ; un test Qt donne à ce modèle `tab_registry.NAV_GROUPS` et `NAV_SECTIONS` et y retrouve chaque `TabSpec`, ajouter une `TabSpec` fait apparaître son entrée sans autre changement, et les sous-titres sont ceux de `woodcore_gui` pour sa navigation ; le nombre d'un groupe est la somme de ses onglets ; une entrée à zéro est inactive ; vérification visuelle de l'ouverture, d'Échap et du clic ailleurs.

### UI-003 — La source et les domaines du filtre
- **Exigence** : sous le menu, un segment « Toutes · Export · Fichiers · Rapport » (il remplace le filtre de provenance, `provenance_box`) ; dessous, les domaines du filtre **rangés sous le titre de leur onglet, dans l'ordre de la navigation** : le cas (`SL`, `A1`, `BI-01`), une étiquette de sa source (**export**, **fichier**, **RS** / BP / CU), son nombre de variables ; un domaine qu'aucun document n'imprime est en gris, infobulle « aucun document ne l'imprime » (jamais en gris tant que l'impression est inconnue, REQ-003). Un clic choisit un domaine, un second le relâche. Une légende des étiquettes en bas. Le volet est assez large pour les noms (260 px au départ) et se règle au séparateur.
- **Source** : T7, T22, T23, T24, T44 (défauts 1 et 2)
- **Langues** : fr / de / en
- **Critère d'acceptation** : test du modèle : les domaines sont groupés par onglet dans l'ordre de la navigation ; le segment « Export » ne laisse que les domaines d'export ; un domaine non imprimé est marqué ; un second clic relâche ; vérification visuelle des noms entiers à 260 px.

### UI-004 — La barre de recherche à étiquettes
- **Exigence** : la barre de recherche du volet central doit porter le filtre en étiquettes devant le texte tapé : l'entrée du menu (« Actions › Actions variables »), la source (« source : export »), le domaine choisi (« Charge utile · A1 [export] ») ; le × d'une étiquette l'enlève ; ⌫ dans une barre vide enlève la dernière, dans l'ordre domaine, source, menu ; la recherche cherche dans ce filtre. Le widget est une brique sans connaissance des variables, réutilisable (ARCH-002).
- **Source** : T13, T25, T46
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de la brique : trois étiquettes, ⌫ dans une barre vide les enlève dans l'ordre, le × en enlève une, le texte tapé n'est pas touché ; test du lien : enlever l'étiquette du domaine relâche le domaine à gauche et inversement.

### UI-005 — Recherche, unité, « Résultats seulement », compte
- **Exigence** : la recherche doit trouver par nom, symbole, désignation, description, unité, clause, valeur, cas et onglet, **chaque mot tapé devant se trouver** (« kn neige »), dans le filtre en étiquettes ; à côté, le filtre d'unité (les unités du projet, les plus fréquentes d'abord), « Résultats seulement » et le compte (« 49 variable(s) dans 26 domaine(s) »).
- **Source** : T26, T27
- **Langues** : fr / de / en
- **Critère d'acceptation** : test (sans Qt, ARCH-001) : « kn neige » sur le projet d'exemple ne garde que des variables en kN dont le cas ou l'onglet dit neige ; « Résultats seulement » ne garde que des résultats (REQ-004) ; le compte est celui de la liste.

### UI-006 — La liste toujours groupée par domaine
- **Exigence** : la liste doit toujours être groupée par domaine, avec ou sans recherche : une ligne de titre par domaine (son cas, son étiquette de source, son onglet, sa désignation, « pas imprimé » s'il y a lieu, son nombre), ses variables dessous, dans l'ordre de la navigation puis celui où le domaine les déclare. Un domaine sans variable gardée par le filtre n'a pas de ligne de titre.
- **Source** : T14, T28, T44 (défaut 4)
- **Langues** : fr / de / en
- **Critère d'acceptation** : test du modèle : les variables d'un même domaine sont contiguës sous une ligne de titre ; `q_k` du projet d'exemple (plus de 60 lignes à plat avant) apparaît sous un titre par domaine ; aucun titre sans variable.

### UI-007 — Colonnes : le symbole seul, une ligne, des largeurs gardées
- **Exigence** : les colonnes sont la case, **le symbole** composé comme le rapport l'imprime (`richtext.MathDelegate`, le nom à écrire en infobulle), la valeur (à droite, chiffres tabulaires), l'unité, la désignation ; ni nom, ni provenance, ni domaine en colonne. Une variable tient sur **une ligne**, un texte trop long coupé par « … » et entier en infobulle. Largeurs au départ : symbole 120 px, valeur 120 px, unité 76 px, la désignation prend le reste ; **elles ne changent jamais avec une recherche** (pas de `ResizeToContents`) ; elles se règlent en glissant le bord droit d'un en-tête, un double-clic sur ce bord rend la largeur d'origine, et `view_state`/`restore` les gardent ; une vue gardée par une version d'avant reprend les largeurs par défaut. **Les clés de `view_state` ne reprennent aucun nom d'avant avec un autre sens** : `source`, `domain` et `name` restent la sélection (`select_key` les lit), le segment de la source s'appelle `origin_filter`, et les nouvelles sont `menu`, `tags`, `widths`, `selection` ; la fenêtre garde en outre les tailles des volets sous (`tab_variables`, vue, `panes`) (`layout_store`) : la vue « Données » disparaissant, la clé change et les 110 px d'avant ne reviennent pas (ARCH-RISK-006).
- **Source** : T15, T29, T30, T31, T46, revue
- **Langues** : fr / de / en (en-têtes)
- **Critère d'acceptation** : test : les largeurs lues après deux recherches différentes sont égales ; glisser un en-tête change la largeur, `view_state` la rend, `restore` la reprend ; un état sans largeurs ne lève rien et rend celles par défaut ; un état d'avant (avec `provenance`, `all_domains`, `source` d'une origine comme `rs`) est lu sans erreur et ne pose aucun filtre de source par accident ; avec la vue « Données » retirée, les tailles des volets ne sont plus lues sous l'ancienne clé de `layout_store`.

### UI-008 — L'encadré des résultats, plus d'étoile
- **Exigence** : la valeur d'un résultat doit être dans un cadre fin de la couleur d'accent du thème (`calc/tools/theme.json`), le texte en accent et en gras ; `RESULT_MARK` (★) disparaît de la liste et de la fiche ; la couleur vient du thème, pas du code.
- **Source** : T11, T18, T32
- **Langues** : sans objet
- **Critère d'acceptation** : test du délégué (le cadre est dessiné pour un résultat et pas pour une autre variable, l'encadré suit le thème clair et sombre) ; plus aucun ★ dans le code de l'onglet ; vérification visuelle.

### UI-009 — Le choix multiple « comme dans Windows »
- **Exigence** : clic = cette variable seule (sa fiche à droite) ; Ctrl+clic ou clic sur la case = l'ajouter ou la retirer, et devient la dernière cliquée ; Maj+clic = la plage depuis la dernière cliquée dans l'ordre affiché, **à travers les domaines**, Ctrl+Maj l'ajoutant à ce qui est choisi ; la case de l'en-tête prend toutes les variables affichées ou les relâche ; les cases suivent la sélection et la sélection suit les cases (une seule notion) ; une ligne de titre de domaine n'est pas une variable, n'est jamais choisie par une plage et un clic sur elle ne fait rien (le prototype). **Comme le prototype** : Maj+clic sans Ctrl remplace la sélection par la plage, la dernière cliquée restant le point de départ de la plage suivante ; la case d'en-tête, décochée, relâche toute la sélection ; la sélection **survit à un changement de filtre** (une variable choisie puis masquée reste choisie : « Copier » met d'abord les variables affichées, dans l'ordre de la liste, puis les masquées, dans l'ordre de la liste entière, et la barre dit « dont k masquée(s) »). Le clavier suit le geste de la souris (flèches = clic, Maj+flèche = Maj+clic, Espace = case, Ctrl+A = tout l'affiché) : la vue n'emploie pas la sélection native de Qt (ARCH-007).
- **Source** : T17, T33, prototype (`pick`, `copySel`), revue
- **Langues** : fr / de / en (infobulles)
- **Critère d'acceptation** : tests sur la logique de sélection (sans Qt) : clic, Ctrl+clic, Maj+clic à travers deux domaines (les titres sautés), Ctrl+Maj, case d'en-tête, relâchement, un filtre qui masque une variable choisie (elle reste, la copie l'ordonne après les affichées), le clavier ; et un test Qt qui lit les cases après chaque geste.

### UI-010 — La barre de sélection et « Copier les n commandes »
- **Exigence** : une barre au-dessus de la liste, visible quand au moins une variable est choisie : « 3 choisie(s) · Copier les 3 commandes · Tout désélectionner » ; « Copier » met dans le presse-papier une ligne `#var` par variable, dans l'ordre de la liste (REQ-006, UI-009 pour les variables masquées par un filtre, que la barre compte à part).
- **Source** : T34
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : trois variables choisies, le presse-papier contient trois lignes dans l'ordre affiché ; « Tout désélectionner » vide les cases ; la barre est cachée à zéro.

### UI-011 — La fiche d'une variable
- **Exigence** : la fiche doit montrer, en tête, symbole = **valeur** unité (la valeur encadrée si c'est un résultat, « Résultat du calcul » dessous), la désignation, le chemin « Actions › Actions variables › Neige · SL [export] » ; le bouton « Ouvrir l'onglet Neige ↗ » (REQ-009) ; la commande à copier avec « Copier » et la phrase de ce qu'il faut inclure (REQ-006) ; les champs nom à écrire, description, clause, calcul (la formule de l'étape), choix (la valeur courante en gras), niveau, **« Vient de »** en mots (le classeur et sa feuille, Woodcore, la norme, le rapport) au lieu de la source brute, une ligne vide cachée ; « Le même calcul ailleurs » (REQ-003) : « Calculé dans **export** ; celle-ci le rappelle. » puis un bouton par autre source du même calcul (« [RS] SL · 1.115 · rappelle ») qui y mène. La fiche montre la dernière variable cliquée.
- **Source** : T16, T35, T36, T37, T38, T39, T44 (défaut 7)
- **Langues** : fr / de / en (« Vient de », les phrases d'inclusion, « Calculé dans… », « rappelle »)
- **Critère d'acceptation** : test du modèle de la fiche (sans Qt) pour une variable d'export, de fichier et de document : en-tête, commande, phrase, « Vient de » en mots, sœurs ; un bouton de sœur choisit la variable dans l'autre source ; la désignation allemande du classeur est montrée telle qu'écrite (D-3) ; vérification visuelle.

### UI-012 — La fiche d'un domaine choisi seul
- **Exigence** : un domaine choisi sans variable doit montrer son nom et sa source, son chemin, « Ouvrir l'onglet … » (REQ-009), le domaine entier à copier (REQ-006), le nombre de ses variables et de ses résultats ; le nombre n'est plus sous « Valeur », ni la sorte sous « Désignation ».
- **Source** : T40, T44 (défaut 6)
- **Langues** : fr / de / en
- **Critère d'acceptation** : test du modèle : le domaine `snow-load · SL` donne le nombre de variables et de résultats, la commande `#include domain-file("snow-load", "SL")` ; aucune ligne « Valeur » ni « Désignation » pour un domaine.

## 5. Exigences d'architecture

### ARCH-001 — Logique hors de Qt
- **Exigence** : le filtre du menu, de la source, du domaine, de la recherche, de l'unité et de « Résultats seulement », l'ordre de la navigation, le groupement par domaine, `imprimé`/sœurs/source qui calcule, la commande à copier, la logique de sélection et les comptes doivent vivre dans des modules sans Qt de `calc/`, lus par l'onglet (la liste et le découpage sont en ARCH-008) ; l'onglet n'affiche, ne recalcule rien. **Pas dans `build_reference_calls.py`** : ce module épelle des appels Typst et n'a pas à connaître `variable_sources.Domain` ; `formula_domain` l'importe (`import build_reference as ref`) et `variable_sources` importe `formula_domain` : lui faire importer `variable_sources` ferait un cycle. Les modèles de `calc/` hors `calc/domains/` ne sont pas gardés Qt-free par `tests/test_module_imports.py` : un test des nouveaux modèles le fait (ARCH-008). Le script de l'artefact (`inScope`, `match`, `ordered`, `printed`, `siblings`, `origin`, `cmdOf`, `pick`) sert de modèle de comportement, non de code livré.
- **Source** : principes « domain logic is independent of the UI » (docs/architecture/principles.md) ; T5
- **Critère d'acceptation** : les tests UI-002 à UI-012 qui portent sur le modèle s'exécutent sans importer PySide6.

### ARCH-002 — Briques réutilisables
- **Exigence** : la barre de recherche à étiquettes (UI-004) et le menu d'arbre à entrées grisées (UI-002) doivent être des widgets sans connaissance des variables (étiquettes et entrées données par l'appelant), pour que d'autres onglets les prennent ; **l'onglet n'a pas besoin de la brique de bulle de l'issue #115** (ses infobulles sont des `QToolTip`) et ne dépend d'aucune des deux issues. Ils réemploient ce qui existe : le segment de la source est un `chrome.SegmentedSwitch` (déjà employé pour la langue et les vues), le popup se place par `place` (`norm_bubble`, que #115 migre vers `hover_bubble` en le réimportant : l'import de `norm_bubble` reste valable avant et après), les couleurs sont celles de `theme.json` (`accent`, `accent-soft`) et le style des étiquettes est une propriété de la feuille de style de `theme.py`, comme `segment` et `callout`.
- **Source** : T46 (« une brique commune si d'autres onglets la veulent ») ; chevauchements #115, #113 ; revue
- **Critère d'acceptation** : les deux widgets n'importent rien de `variables_tab` ni de `variable_*` ; un test les emploie sans variables.

### ARCH-003 — Le contrat `variable_sources.Domain`
- **Exigence** : `Domain` s'étend de `tab` (REQ-001) et de ce qui rattache un domaine à son calcul (REQ-002, REQ-003) ; le contrat reste en mémoire — aucun fichier de `data/` ne change, donc **aucun schéma ni `schema_version`** — ; le cache de lecture des documents (`calc/variables.py`) est inchangé, le rapprochement étant fait à l'assemblage (`variable_calc.assemble`), après la lecture. Les nouveaux champs de `Domain` (`tab`, `calc`) ont des valeurs par défaut (`formula_domain.variable_domains` construit un `Domain` sans eux, `palette_index` lit ceux de `read_export`). `read_export` lit en plus, sans les compter parmi les fichiers de variables, `domain-files.json`, `checks.json` et `steel.json` (schémas existants) dans un champ `index` de `Export` : l'égalité `len(export.missing) == len(FILE_SOURCES)` qui dit « pas encore exporté » reste vraie, un index absent ou illisible n'arrête rien (ses domaines n'ont pas de calcul, et l'erreur de lecture est celle des autres fichiers, `bad_file`).
- **Source** : T46, T50 ; principe « explicit, versioned data models » (aucun fichier exporté ne change) ; revue
- **Critère d'acceptation** : `data/` et le cache sont identiques octet pour octet avant et après (test d'export reproductible inchangé) ; les anciens appels `Domain(name=…, origin=…)` construisent encore un domaine ; un projet jamais exporté se dit toujours « pas encore exporté » ; `tests/test_palette_index.py` passe.

### ARCH-004 — Compatibilité avec la future base d'onglets de données (#106)
- **Exigence** : l'onglet ne doit pas créer de couplage avec la base de la fenêtre que #106 remplacera (`display_view.DisplayTab`, `views.DATA_VIEWS`) : en les retirant, il reste un `QWidget` navigateur à contrat (`KEY`, `on_shown`, `confirm_leave`, `view_state`/`restore`, `set_language`, `on_mode`), de sorte que la migration vers une base `DataTab` sur `TabHost` ne change que sa classe de base ; les autres onglets qui emploient `DisplayTab` (Formule, vérifications, etc.) ne sont pas touchés. **La forme (revue, ARCH-009)** : le contenu de l'onglet est une classe simple, `VariablesBrowser` (`calc/tools/variables_browser.py`), de la forme d'un `tab_host.Service` (un `NAME`, un `mount()` qui rend le widget, `state()` / `restore(state)`, les phases `shown`, `mode_changed`, `leave`), sans base Qt commune ni appel d'un autre service ; `VariablesTab` n'est que la coque `QWidget` qui la monte et qui redirige, une ligne chacune, `begin_pick`, `end_pick`, `selected_key`, `selected_keys`, `variable`, `address`, `select_key`, `view_state`, `restore`, `on_shown`, `on_mode`, `confirm_leave` et l'attribut `search` : #106 les remplace par `EXPOSES` en ne changeant que la base.
- **Source** : T19 ; chevauchement #106 ; docs/ui/building-a-tab.md ; revue
- **Critère d'acceptation** : `tests/test_window.py`, `tests/test_views.py`, `tests/test_tab_registry.py` passent ; `display_view.py` et `views.py` ne sont pas modifiés ; `VariablesTab` ne définit que ces redirections (un test les énumère) et toute la logique de l'onglet se trouve sur `VariablesBrowser`.

### ARCH-005 — La navigation, une seule fois
- **Exigence** : le menu doit lire `tab_registry` à l'exécution (`NAV_GROUPS`, `NAV_SECTIONS`) ; la `NAV` codée en dur du prototype n'est pas recopiée ; « Ouvrir l'onglet » réutilise `MainWindow.open_object` et `GRAPH_KIND` (REQ-009). Un onglet reste affiché même si l'Acier ou un onglet réservé n'ont pas de variable (entrée grisée). La seule liste de clés d'onglet hors `tab_registry` est la table de REQ-001, et la seule clé de groupe écrite hors de lui est celle du groupe « Document » où se rangent les entrées des documents (une constante, tenue à un groupe de `NAV_GROUPS` par le test Qt de UI-002).
- **Source** : principe « une seule source de vérité » ; T20, T46
- **Critère d'acceptation** : revue (aucune liste d'onglets dans `variables_tab.py` ni dans le module du modèle, hors la table de REQ-001) ; test UI-002.

### ARCH-006 — Mots de la fenêtre
- **Exigence** : les mots nouveaux (menu, source, légende, « pas imprimé », barre de sélection, fiche, phrases d'inclusion) vont dans le `STRINGS` de `calc/tools/variables_words.py` (le tableau actuel fait déjà 220 lignes dans un module de 1193 ; la convention `*_words.py` des onglets voisins), fusionné par `woodcore_gui_words.py` à la place de celui de `variables_tab`, en fr, de et en (`tests/test_i18n.py`) ; les widgets réutilisables (ARCH-002) ne portent aucun mot, l'appelant leur donne les siens ; les mots `vr_*` qui ne servent plus (`vr_col_name`, `vr_col_provenance`, `vr_col_domain`, `vr_all_domains*`, les mots d'Affichage et de provenance) sont retirés.
- **Source** : T49 ; CLAUDE.md « No hardcoding »
- **Critère d'acceptation** : `tests/test_i18n.py` passe ; aucune clé `vr_*` orpheline ni manquante.

### ARCH-007 — Le widget de la liste
- **Exigence** : la liste groupée est un **`QTableView` sur un `QAbstractTableModel` plat** à lignes de titre (une ligne `titre` qui occupe toute la largeur par `setSpan`, puis ses lignes `variable`), des largeurs `Interactive`, **sans la sélection native de Qt** (`NoSelection`) : la sélection est celle du modèle sans Qt de UI-009 (`variable_select`), que la vue peint (fond, case) et à qui elle donne les clics, les modificateurs et les touches. Raisons (§13, ARCH-RISK-009) : un `QTreeView` se laisserait replier au clavier (la liste est « toujours dépliée »), la plage native de Qt prend les lignes de titre et ne sait pas « la dernière cliquée » ni la sélection qui survit à un filtre ; un modèle plat garde « une variable, une ligne » et un seul ordre affiché, celui des plages, des copies et de `selected_keys()`. Ni la fiche, ni `selected_key`, ni REQ-007 ne dépendent du widget.
- **Source** : T46, revue
- **Critère d'acceptation** : REQ-007 et UI-009 sont vérifiés par le modèle, non par le widget ; un test Qt (`tests/test_variables_list.py`) lit les cases, le fond et les largeurs après chaque geste et ne trouve ni repli, ni ligne de titre choisie.

### ARCH-008 — Les modules, et leur taille
- **Exigence** (revue) : `variables_tab.py` fait 1193 lignes et `layout.md` (§11) vise 1000 et refuse 1500 : l'onglet réécrit est coupé d'emblée, par responsabilité. **Sans Qt, sous `calc/`** : `variable_calc.py` (l'identité d'un calcul `CalcRef`, les tables sorte → onglet, l'assemblage `assemble`, le rapprochement des documents, les sœurs, la source qui calcule, `imprimé`, les clés de résultat), `variable_query.py` (l'arbre de navigation reçu en argument, les nombres, le filtre, le groupement par domaine, les unités, les comptes, les étiquettes du filtre), `variable_select.py` (la sélection : clic, Ctrl, Maj, case d'en-tête, clavier, ordre de copie), `variable_card.py` (le modèle de la fiche : en-tête, chemin, commande et phrase d'inclusion, « Vient de », sœurs, fiche d'un domaine, lignes de la copie multiple). **Avec Qt, sous `calc/tools/`** : `tag_search_bar.py`, `tree_menu.py` (ARCH-002), `variables_list.py` (modèle de table, délégués, en-tête, ARCH-007), `variables_detail.py` (la fiche), `variables_words.py` (ARCH-006), `variables_browser.py` (le contenu, ARCH-004) et `variables_tab.py` (la coque et la lecture en fil `Read`). Aucun ne passe 1000 lignes ; `tests/test_module_size.py` le tient. Un test importe les quatre modèles avec PySide6 hors d'atteinte, comme `tests/test_module_imports.py` le fait pour `calc/domains/`.
- **Source** : revue ; `docs/architecture/layout.md` §11
- **Critère d'acceptation** : `tests/test_module_size.py` passe sans exception nouvelle ; `tests/test_module_imports.py` (étendu : les quatre modèles s'importent seuls, sans Qt) passe ; `layout.md` liste les modules.

### ARCH-009 — La coque et le contenu séparés, pour #106
- **Exigence** (revue) : voir ARCH-004. Le contenu (`VariablesBrowser`) tient ses widgets et son état ; il ne lit pas `app.tabs` ni ne nomme une autre classe d'onglet ; ce dont il a besoin de la fenêtre passe par des méthodes publiques de `MainWindow` (`current_document`, `t`, `set_status`, `busy`, `process`, et les deux de ARCH-010) que #106 retrouvera sur son contexte. L'attribut `search` est une propriété de la coque qui rend le `QLineEdit` du contenu.
- **Source** : #106 (Q-001 A : `EXPOSES = {nom: service}`), revue
- **Critère d'acceptation** : un test construit `VariablesBrowser` seul, sans coque, et lui fait lire, filtrer, choisir et copier.

### ARCH-010 — Ce que la fenêtre offre à « Ouvrir l'onglet »
- **Exigence** (revue) : `MainWindow` gagne `can_open_tab(key)` — `(vrai, None)` ou `(faux, clé de mot de la raison)` : l'onglet n'est pas dans le document montré (`mode_tabs`), le document n'est pas fait (`available`), l'onglet est réservé (`reserved_tab.ReservedTab`), un choix pour un champ est en cours (`picking`) — et `show_tab(key, node=None)` : l'onglet devant (par le même chemin que la navigation, qui en suit l'indice), puis `open_object(node)` quand un nœud est donné et que l'onglet le liste. Les mots des raisons sont ceux de la fenêtre. La palette de commandes, qui amène un onglet devant par `tab_widget.setCurrentIndex` dans `_palette_show_in`, n'est pas modifiée ici (hors périmètre) ; elle pourra prendre `show_tab`.
- **Source** : REQ-009, revue
- **Critère d'acceptation** : `tests/test_window.py` (ou `tests/test_modes_window.py`) : chacune des raisons donne un refus nommé ; `show_tab("tab_ac_snow", "load:snow-load/SL")` met l'onglet devant avec le cas ouvert ; `MainWindow.open_object` est inchangée.

### ARCH-011 — L'ordre de #115, #114, #112, #106
- **Exigence** (revue) : l'onglet s'écrit sur le code que #115 laisse (`hover_bubble.py`, `place` migré : l'import de `norm_bubble` ne change pas) ; la table « sorte de vérification → onglet » de REQ-001 porte, avant #112, `buckling` → `tab_mc_buckling` et `lateral-torsional` → `tab_mc_ltb` ; **#112 (qui replie ces deux onglets dans Compression et Flexion et renomme `tab_mc_shear`) change ces deux lignes**, ce que le test « chaque clé est une `TabSpec` » lui fait voir en échouant, et elle ne touche à aucun autre fichier de cet onglet ; le menu lit les titres de la fenêtre (CON-003) et suit le renommage sans changement.
- **Source** : ordre d'implémentation de l'ingénieur (#115, #114, #113, #112, #106) ; revue
- **Critère d'acceptation** : le test des clés d'onglet de la table est dans `tests/test_variable_calc.py` côté Qt et nomme la sorte et la clé qui manquent ; §14 le signale à la session de #112.

### ARCH-012 — Les clés de résultat d'une vérification, une fois
- **Exigence** (revue) : la clé `eta` que `member_check` et `steel_check` écrivent en dernière ligne d'une vérification est déclarée une fois comme constante nommée du module de calcul (`RESULT_KEY`), lue par `variable_calc` ; un test tient la constante au fichier de chaque vérification de l'exemple (le dernier `#eq` d'un fichier de vérification a cette clé). Rien n'est écrit dans `checks.json`, `steel.json` ni les schémas (aucune `schema_version` ne change).
- **Source** : REQ-004, revue (ARCH-RISK-003)
- **Critère d'acceptation** : `tests/test_variable_calc.py` : pour chaque vérification de l'exemple, `eta` est dans les résultats de son domaine « fichier » et de son domaine de document.

## 6. Contraintes

- **CON-001** — La lecture des documents, le cache, la pièce jointe du PDF, le bandeau et le message d'une lecture qui échoue ne changent pas. Source : T19.
- **CON-002** — Aucun fichier exporté (`data/`) ne change, et la valeur n'est jamais recalculée par l'onglet : il montre ce que `calc/` lit. Source : principes ; T47 (inféré).
- **CON-003** — Le nom « Cisaillement » du menu vient des mots de la fenêtre pour `tab_mc_shear` : il suit la décision de #112 et le registre dit encore « Effort tranchant » aujourd'hui ; aucune chaîne n'est écrite dans l'onglet. Source : T20, T50.
- **CON-004** — Les désignations écrites en allemand dans le classeur sont montrées telles quelles. Source : T8.
- **CON-005** — Les tests travaillent sur `tests/projet-exemple/` ; aucune écriture dans `../Musterprojekt/` ; les chiffres de l'issue (935/78, 918/75) sont à remesurer et non à figer sans contrôle. Source : CLAUDE.md ; T3, T4.
- **CON-006** — Le menu et la table de REQ-001 doivent suivre l'arrivée de l'onglet Domaines (#113) et les onglets réservés qui deviennent des calculs sans changement de l'onglet Variables. Source : T20, T51 (inféré).
- **CON-007** — Fichiers en LF, prose sur une ligne, anglais dans le code et les docs ; aucun fichier de `docs/` au-dessus de 100 Ko (hors `decisions.md`, `CHANGELOG.md`) ; `docs/ui/tab-variables.md` (16 Ko) est réécrit, il ne grossit pas au-delà. Source : CLAUDE.md.
- **CON-008** — Passe par `/big-feature` : contrat `Domain`, plusieurs modules, décision de la v0.117 renversée. Source : T50.

## 7. Décisions prises

D-1 à D-7, D-10 et D-11 sont de l'ingénieur (issue #114 et ses réponses, 24.10.2026) ; D-8 et D-9 sont des inférences marquées ; D-12 à D-18 sont de la revue d'architecture. Aucune n'est reposée.

- **D-1** — **Proposition A** : trois volets, rangés ; B, C, D écartées (question 1).
- **D-2** — **Une ligne par source** (export, fichier, document), avec un filtre par source ; « un calcul n'est porté normalement que par une seule source, et toutes les autres ne font que la rappeler » (question 2, réponse 2). Prix : trois lignes pour un même calcul, reliées par « Le même calcul ailleurs ».
- **D-3** — **Désignations du classeur telles qu'écrites** (question 3, réponse 1) : « À l'avenir, il n'y aura plus de classeurs » (#109).
- **D-4** — **Vue Affichage retirée**, la fiche suffit (question 4, réponse 2). Renverse la v0.117 (§13) ; `#find` et les aperçus ne sont plus offerts dans cet onglet.
- **D-5** — **Racines des documents cachées** (question 5, réponse 2).
- **D-6** — **Un encadré autour de la valeur**, plus d'étoile (question 6, réponse 2 ; retour sur les résultats).
- **D-7** — **Les retours de la version 1, appliqués** : menu déroulant « Tous » par défaut à gauche ; filtre dans la barre de recherche, amovible ; recherche triée par domaine sous une ligne de titre ; symbole seul, largeurs réglables et fixes, une ligne par variable ; « Ouvrir directement l'onglet » ; cases, Ctrl+clic, Maj+clic, copie de toutes les commandes.
- **D-8** — (inférée, T50 posait la question) **`selected_key()` rend la dernière variable cliquée**, `selected_keys()` rend toutes les variables choisies ; **le choix multiple est coupé pendant « Choisir pour un champ »**, un champ ne suivant qu'une valeur. Raison : les lecteurs existants attendent une clé ; coût : aucun.
- **D-9** — (inférée de T36, T43 et du code) **« Ouvrir l'onglet » réutilise le graphe de dépendances** (`open_object`, `GRAPH_KIND`) plutôt qu'un second mécanisme ; ce qu'un onglet sans `GRAPH_KIND` fait est D-11.
- **D-10** — **Q-001, A** (ingénieur, 24.10.2026) : un domaine de document est rattaché à son calcul par `domain-files.json` ; un nom non trouvé ou ambigu va sous « Rapport de statique » (devenu, par la revue, « Document › <le document> »). Prix : un appariement par identifiant, que le rapport peut tromper en déclarant à la main un domaine du nom d'un fichier de Woodcore.
- **D-11** — **Q-002, A** (ingénieur, 24.10.2026) : « Ouvrir l'onglet » amène l'onglet devant ; le cas s'ouvre là où l'onglet sait le faire (`GRAPH_KIND`) ; Python et Formule/Domaines passent devant sans cas ; bouton inactif, infobulle à l'appui, pour un domaine du rapport et un onglet réservé. Prix : Python et Domaines n'ouvrent pas le cas tant que #113 ne leur donne pas un `open_object`.
- **D-12** — (revue d'architecture) **Le `tab` d'un domaine de vérification est lu de l'enregistrement de la vérification** (`kind`, `fire`), non du dossier de son fichier : FE-01 et FE-02, vérifications au feu, sont écrites dans `Timber-checks/Bending/` et `Buckling/`. Raison : le dossier est une conséquence du calcul, et #112 replie des onglets sans changer les dossiers. Coût : la lecture de `checks.json` et `steel.json` (déjà validés par leurs schémas) à chaque `read_export`.
- **D-13** — (revue) **Le menu des onglets reçoit sa navigation en argument** : `tab_registry` importe tous les onglets, donc Qt ; les modèles sans Qt n'en importent rien. Coût : la règle des sections (qui ouvre une section jusqu'à la suivante) est écrite une fois dans le modèle et une fois dans la fenêtre ; un test les tient égales.
- **D-14** — (revue) **Une entrée du groupe « Document » par document fait** plutôt qu'une seule « Rapport de statique » : les domaines qu'un autre document déclare lui-même n'ont pas à porter le nom du rapport. À confirmer à l'approbation (le prototype n'a que « Rapport de statique »).
- **D-15** — (revue, prototype) **La sélection survit à un filtre**, comme dans le prototype ; « Copier » met les affichées d'abord, les masquées ensuite ; la barre compte les masquées.
- **D-16** — (revue) **La liste est un `QTableView` plat à sélection du modèle** (ARCH-007), pas un `QTreeView` à sélection native.
- **D-17** — (revue) **Le contenu est une classe simple de la forme d'un service, la coque de l'onglet n'est que redirections** (ARCH-004, ARCH-009), pour que #106 ne change que la base.
- **D-18** — (revue) **La commande à copier n'est pas écrite dans `build_reference_calls.py`** : un cycle d'imports et un module qui épelle du Typst sans connaître les domaines (ARCH-001).

À reporter dans `docs/decisions.md` §13 : la vue Affichage retirée de cet onglet (et avec elle l'aperçu de `#find` et les deux copies `#var-table`, qui n'ont plus d'endroit dans cet onglet), une ligne par source, les racines des documents cachées, l'encadré à la place du ★, la source qui calcule (export, puis fichier, puis document), le filtre et la colonne de provenance (Excel · Woodcore · Typst) remplacés par la source et par « Vient de » (la règle 5 — la provenance systématique — est tenue par la fiche), le `tab` lu de l'enregistrement et non du dossier (D-12), la coque et le contenu (D-17).

## 8. Hors périmètre

- L'arrondi à six décimales des valeurs d'entrée des fichiers dépliés (`calc/domains/unfold.py`, k<sub>β</sub> de SD-10 ; R<sub>d</sub> à 2·10<sup>-7</sup> près) : « à trancher à part » (T45).
- L'onglet **Domaines (#113)** et sa fenêtre « Lier une variable… », les **vérifications d'éléments (#112)** (seul le nom du menu en dépend, CON-003), la migration des onglets Variables/Métrés/Dépendances/Commandes sur une base `DataTab` (**#106**), l'onglet **Commandes (#115)** : non modifiés ici ; seul REQ-009 peut demander une méthode à un onglet de calcul.
- La fin de la lecture du classeur (**#109**) ; l'onglet **Dépendances (#71)**.
- Une vue « Affichage », `#find`, un aperçu de la commande dans cet onglet (D-4).
- Les quatre autres propositions du prototype v1 (B, C, D, D-1).
- Un changement des commandes Typst (`#var`, `domain-file`, `#include`), de la lecture des registres ou du cache.

## 9. Idées non retenues comme exigences

- La copie du prototype dans `docs/requirements/prototypes/2026-10-24-onglet-variables/` (la page, lue par `action: "read"` sur l'artefact) est une tâche de documentation (§11), pas une exigence du produit.
- Une brique de bulle partagée avec l'onglet Commandes (#115) pour les infobulles riches de cet onglet : pas nécessaire (`QToolTip` suffit), idée seulement.
- Réutiliser la barre à étiquettes et le menu d'arbre dans l'onglet Dépendances (#71) ou Domaines (#113) : suggéré par « une brique commune si d'autres onglets la veulent » (T46), non exigé ; seule la réutilisabilité l'est (ARCH-002).

## 10. Questions

### Q-001 — De quelle donnée rattacher un domaine d'un document à son calcul ?
- **Contexte** : le document compilé (le rapport) liste des domaines comme `SL`, `A1` ou `BI-01`, que Woodcore a écrits dans des fichiers `.typ` à partir d'un calcul (une charge, une vérification). Pour dire de quel onglet vient la valeur, ouvrir cet onglet et relier « le même calcul » dans les trois sources, il faut savoir de quel calcul est chaque domaine du document. Le prototype le devine par la ressemblance du nom (le domaine `A1` ressemble au cas `A1`) ; l'issue demande une donnée et propose le `gen:` du fichier, `domain-files.json` ou le registre. `domain-files.json` (écrit par l'export) donne, pour chaque sorte et chaque identifiant, le fichier que Woodcore a écrit ; les fichiers récents n'ont plus de `gen:` (v2 du générateur) ; le registre du document ne porte aujourd'hui que le nom du domaine.
- **Pourquoi elle compte** : elle fixe REQ-002, la précision de « Ouvrir l'onglet » et du « même calcul ailleurs », et décide si l'on touche à `lib/` (Typst) ou seulement à Python.
- **Options** :
  - **A (recommandée)** — appairer par `domain-files.json` : le nom d'un domaine du document est l'identifiant d'un fichier que Woodcore a écrit (sorte + identifiant, avec le chemin du fichier) ; un identifiant présent dans deux sortes, ou dans aucun fichier, reste sans calcul (Document › Rapport de statique) et un test le signale. Rien à changer dans `lib/` ni dans le cache ; c'est encore un appariement par identifiant, mais par une table que Woodcore écrit et que l'export valide, non par ressemblance.
  - **B** — faire écrire la sorte et l'identifiant du calcul dans le registre par `#domain(...)` (un champ de plus dans l'état Typst `var-registry`) : l'appariement est certain, même pour un identifiant en double ; il touche `lib/`, `REGISTRY_DEFAULT`, le schéma de la pièce jointe du PDF et le cache, et invalide tous les caches existants.
  - **C** — garder le rapprochement par le nom du cas, comme le prototype : le moins de travail, mais une heuristique que l'issue refuse (un domaine du rapport nommé « A1 » serait pris pour la charge A1).
- **Réponse** : A — appairer par `domain-files.json` ; ce qui n'est pas trouvé ou est ambigu va sous « Rapport de statique » (ingénieur, 24.10.2026). Reporté en D-10 et REQ-002.

### Q-002 — « Ouvrir l'onglet » : que faire pour un onglet qui ne sait pas ouvrir un cas ?
- **Contexte** : le bouton de la fiche amène devant l'onglet qui calcule la valeur et y ouvre le cas, par le mécanisme du graphe de dépendances (`MainWindow.open_object`) que les onglets de calcul, les vérifications, les assemblages et les moments polaires ont déjà. Deux onglets n'ont pas ce mécanisme : Python (où naissent les domaines `script`) et Formule/Domaines (les domaines de `Domains/*.typ`, que l'issue #113 refait) ; les onglets Séisme et Combinaisons sont réservés. Le domaine « Document › Rapport de statique » n'a pas d'onglet à ouvrir.
- **Pourquoi elle compte** : elle fixe l'étendue du travail (deux onglets de plus à modifier ou non), le texte du bouton pour ces domaines et le critère de REQ-009.
- **Options** :
  - **A (recommandée)** — le bouton amène l'onglet devant sans ouvrir de cas pour Python et Formule/Domaines (et reste inactif, avec son infobulle, pour un domaine de rapport ou un onglet réservé) ; le cas se choisit pour tous les autres : aucun onglet de calcul n'est modifié, #113 pourra donner à Domaines son `open_object` quand il refera l'onglet.
  - **B** — donner à Python et à Formule/Domaines un `GRAPH_KIND` et un `open_object` dans ce lot : le bouton ouvre toujours le cas ; deux onglets de plus à toucher, dont celui que #113 va refaire (travail à reprendre).
  - **C** — pas d'ouverture d'onglet du tout pour les sources sans cas ouvrable, le bouton étant absent : la fiche plus courte, mais le bouton apparaît et disparaît selon le domaine, ce qui surprend.
- **Réponse** : A — « Ouvrir l'onglet » amène l'onglet devant sans ouvrir de cas là où l'onglet n'en sait pas ouvrir ; inactif, avec son infobulle, pour un domaine de rapport et un onglet réservé (ingénieur, 24.10.2026). Reporté en D-11 et REQ-009, tel que l'option A l'écrit : le cas s'ouvre pour les onglets qui ont déjà `open_object` (la revue relève que le compte rendu de la réponse peut aussi se lire « jamais de cas » : à confirmer à l'approbation, l'écart tenant en un appel dans `show_tab`).

## 11. Critères d'acceptation

- [x] REQ-001 — chaque domaine d'export et de fichier a un `tab` de `tab_registry`, lu de l'enregistrement de la vérification et non du dossier (FE-01 → feu) ; les tables sont déclarées une fois.
- [x] REQ-002 — le rapprochement d'un domaine de document se fait par `domain-files.json` (Q-001, A), sans ressemblance de nom ; un nom ambigu ou absent reste sans calcul.
- [x] REQ-003 — une ligne par source, la source qui calcule, les sœurs, `imprimé`/inconnu (test sans Qt).
- [x] REQ-004 — `q_k` de `A1` est un résultat dans les trois sources.
- [x] REQ-005 — la racine des documents n'est plus listée ; 918 variables dans 75 domaines à remesurer.
- [x] REQ-006 — la commande et la phrase d'inclusion des trois sources, d'un domaine entier, et la copie de plusieurs dans l'ordre.
- [x] REQ-007 — `selected_key()` = la dernière cliquée, `selected_keys()` = toutes ; aucun lecteur existant modifié.
- [x] REQ-008 — pendant « Choisir pour un champ » : une valeur, seulement les valeurs acceptées, partout.
- [x] REQ-009 — « Ouvrir l'onglet » ouvre l'onglet de la source qui calcule, sur le cas là où l'onglet le sait ; Python et Domaines sans cas ; inactif et expliqué pour un domaine de document, un onglet réservé ou absent du document, et pendant un choix (Q-002, A).
- [x] UI-001 — trois volets, une vue, plus de `DATA_VIEWS` ni d'`install_display` ; bandeau et lecture inchangés.
- [x] UI-002 — menu des onglets lu de `tab_registry`, nombres, entrées grisées, Échap.
- [x] UI-003 — source, domaines rangés sous leur onglet, étiquette de source, gris « pas imprimé », légende, 260 px.
- [x] UI-004 — barre à étiquettes, ×, ⌫, liens avec le volet de gauche.
- [x] UI-005 — recherche par tous les mots, unité, « Résultats seulement », compte.
- [x] UI-006 — liste toujours groupée par domaine, une ligne de titre par domaine.
- [x] UI-007 — symbole seul, une ligne, largeurs fixes réglables, double-clic, gardées, ancien état lu.
- [x] UI-008 — encadré à la couleur du thème, plus de ★.
- [x] UI-009 — clic, Ctrl, Maj à travers les domaines, Ctrl+Maj, case d'en-tête.
- [x] UI-010 — barre « n choisie(s) · Copier les n commandes · Tout désélectionner ».
- [x] UI-011 — la fiche d'une variable : en-tête, ouvrir, commande, « Vient de », même calcul ailleurs.
- [x] UI-012 — la fiche d'un domaine seul.
- [x] ARCH-001 — la logique sans Qt, testée sans PySide6.
- [x] ARCH-002 — barre à étiquettes et menu d'arbre sans connaissance des variables.
- [x] ARCH-003 — `Domain` étendu, aucun fichier ni schéma changé, cache intact.
- [x] ARCH-004 — `display_view.py` et `views.py` intacts ; l'onglet prêt pour la base `DataTab` (#106).
- [x] ARCH-005 — une seule navigation (`tab_registry`), `open_object` réutilisé.
- [x] ARCH-006 — mots en fr/de/en, `vr_*` inutiles retirés.
- [x] ARCH-007 — liste en `QTableView` plat à sélection du modèle (tranché en §13), la logique n'en dépendant pas.
- [x] ARCH-008 — modules découpés (quatre modèles sans Qt, widgets, mots, contenu, coque), aucun au-delà de 1000 lignes, modèles importables sans Qt.
- [x] ARCH-009 — `VariablesBrowser` construit seul ; la coque ne fait que rediriger.
- [x] ARCH-010 — `can_open_tab` et `show_tab` de la fenêtre, `open_object` inchangée.
- [x] ARCH-011 — la table des sortes de vérification suit #112 (deux lignes) ; l'ordre #115, #114, #112, #106 tenu.
- [x] ARCH-012 — la clé `eta` des vérifications déclarée une fois, tenue aux fichiers de l'exemple.
- [x] Documentation : `docs/ui/tab-variables.md` réécrit (la vue Affichage et la provenance ne sont plus décrites que comme historique) ; `docs/decisions.md` §13 et `docs/decisions-index.md` ; `docs/architecture/layout.md` si un module est ajouté ; ligne au catalogue des tests pour tout fichier de test nouveau ; entrée `CHANGELOG.md` ; page « Nouveautés » de la prochaine version en fr/de/en ; copie du prototype dans `docs/requirements/prototypes/2026-10-24-onglet-variables/` ; aucune commande Typst nouvelle (donc pas de `///` ni de `commands.json`).
- [x] Tests : `tests/test_variable_sources.py`, `tests/test_variables.py`, `tests/test_window.py`, `tests/test_modes_window.py`, `tests/test_i18n.py`, `tests/test_linkable_spin.py`, `tests/test_command_palette.py`, `tests/test_palette_index.py`, `tests/test_views.py`, `tests/test_tab_registry.py`, `tests/test_tab_overrides.py`, `tests/test_module_size.py`, `tests/test_module_imports.py`, `tests/test_call_command.py` étendus ou inchangés et verts ; fichiers nouveaux, une ligne chacun au catalogue : `tests/test_variable_calc.py`, `tests/test_variable_query.py`, `tests/test_variable_select.py`, `tests/test_variable_card.py`, `tests/test_tag_search_bar.py`, `tests/test_tree_menu.py`, `tests/test_variables_list.py`.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1, D-1 | capturé |
| T2 | §1, REQ-008 | capturé |
| T3 | état actuel (§3), CON-005 | capturé |
| T4 | CON-005, REQ-005 | capturé |
| T5 | ARCH-001, ARCH-005 | capturé (le script est un modèle de comportement, non du code livré) |
| T6 | D-1 | capturé |
| T7 | D-2, REQ-003, UI-003 | capturé |
| T8 | D-3, CON-004 | capturé |
| T9 | D-4, UI-001 | capturé |
| T10 | D-5, REQ-005 | capturé |
| T11 | D-6, UI-008 | capturé |
| T12 | D-7, UI-002 | capturé |
| T13 | D-7, UI-004 | capturé |
| T14 | D-7, UI-006 | capturé |
| T15 | D-7, UI-007 | capturé |
| T16 | D-7, REQ-009, UI-011 | capturé |
| T17 | D-7, UI-009 | capturé |
| T18 | D-6, UI-008 | capturé |
| T19 | UI-001, CON-001, ARCH-004 | capturé |
| T20 | UI-002, CON-003, ARCH-005 | capturé |
| T21 | UI-002 | capturé |
| T22 | UI-003 | capturé |
| T23 | UI-003, REQ-003 | capturé |
| T24 | UI-003 | capturé |
| T25 | UI-004 | capturé |
| T26 | UI-005 | capturé |
| T27 | UI-005 | capturé |
| T28 | UI-006 | capturé |
| T29 | UI-007 | capturé |
| T30 | UI-007 | capturé |
| T31 | UI-007 | capturé |
| T32 | REQ-004, UI-008 | capturé |
| T33 | UI-009, REQ-007 | capturé |
| T34 | UI-010, REQ-006, REQ-007 | capturé |
| T35 | UI-011 | capturé |
| T36 | REQ-009, UI-011 | capturé |
| T37 | REQ-006, UI-011 | capturé |
| T38 | UI-011 | capturé |
| T39 | REQ-003, UI-011 | capturé |
| T40 | UI-012, REQ-006, REQ-009 | capturé |
| T41 | REQ-008 | capturé |
| T42 | REQ-001, REQ-002 | capturé |
| T43 | REQ-002, D-10 | capturé ; tranché par Q-001 (A, `domain-files.json`) |
| T44 | UI-003, UI-006, UI-008, UI-011, UI-012, REQ-004, REQ-005, D-4 | capturé |
| T45 | §8 | hors périmètre |
| T46 | REQ-001 à REQ-009, UI-002 à UI-012, ARCH-002, ARCH-003, ARCH-007 | capturé |
| T47 | REQ-001 à REQ-006 | capturé |
| T48 | UI-002 à UI-012, REQ-008 | capturé |
| T49 | ARCH-006, §11 | capturé |
| T50 | REQ-002, REQ-007, REQ-008, REQ-009, D-8, D-9, D-10, D-11, CON-003, CON-008, ARCH-007 | capturé ; réponses inférées marquées D-8, D-9 ; données et ouverture d'un onglet sans cas tranchées (D-10, D-11) ; menu et liste tranchés par la revue (UI-002, ARCH-007) |
| T51 | §8, ARCH-002, CON-006 | hors périmètre / lien |

### Points de la source non résolus

Aucun. T43 (la donnée du rapprochement) : Q-001, A. T50 « Ouvrir l'onglet » : Q-002, A. T50 menu et T46 liste : tranchés par la revue (arbre dans un popup ; `QTableView` plat, ARCH-007). Restent à confirmer à l'approbation : D-14 (une entrée « Document » par document) et la lecture de Q-002 (le cas s'ouvre-t-il là où l'onglet sait le faire ?).

## 13. Revue d'architecture

Revue du 24.10.2026, faite contre le code de master (`be5b85f`) : **APPROUVER AVEC RÉSERVES**, les quinze risques (ARCH-RISK-001 à 015) reportés dans la spec et dans le plan (§14). Le texte entier — modules concernés, ce que disent les données, existant à réutiliser, risques, approche, tests, verdict — est dans [docs/history/2026-10-24-onglet-variables-groupes-revue.md](../../history/2026-10-24-onglet-variables-groupes-revue.md) (déplacé le 25.10.2026 pour tenir la spec sous 100 Ko ; rien n'y est changé).

## 14. Plan d'implémentation

Ordre de la session : #115 (déjà implémentée : `hover_bubble.py` existe, `place` y est ou dans `norm_bubble` selon ce qu'elle a laissé), puis cette issue, puis #113, #112, #109, #107, #106. Avant l'étape 1, relire `variables_tab.py`, `tab_registry.py`, `woodcore_gui.py` et `woodcore_gui_words.py` tels que #115 les laisse (fichiers partagés : seule la ligne qui fusionne `variables_tab.STRINGS` est à toucher). Chaque étape se termine par les tests de sa colonne (`python tests/run_tests.py -k nom` ou `--related`), la suite complète une fois à la fin (étape 15). Les modèles (étapes 3 à 6) se testent sans Qt avant tout widget : ce sont eux qui prouvent le comportement, les widgets ne font que l'afficher.

| # | Étape | Fichiers | REQ / UI / ARCH | Le test qui la prouve |
|---|---|---|---|---|
| 1 | **Mesures et prototype.** Remesurer sur le code d'alors le nombre de variables et de domaines (issue : 935/78 ; sans les racines des documents : 918/75), lire le prototype par `Artifact read` (et `path` pour ses fichiers de script) et en copier la page et un `README.md` (les mesures, la date, l'URL) dans `docs/requirements/prototypes/2026-10-24-onglet-variables/`. Aucun code. | `docs/requirements/prototypes/2026-10-24-onglet-variables/` | CON-005, §11 « Documentation » | les chiffres relevés sont ceux que les tests des étapes 2 et 3 affirment ; `tests/test_docs_coherence.py` |
| 2 | **Le contrat de lecture.** `Domain` gagne `tab` et `calc` (défauts `None`) ; `Export.index` : `read_export` lit `domain-files.json`, `checks.json` et `steel.json` (schémas existants, erreur `bad_file` nommant le fichier et le champ, hors de `missing`) ; `registry_domains` ne rend plus le domaine vide de chaque document. | `calc/variable_sources.py` | REQ-005, ARCH-003, ARCH-RISK-007 | `tests/test_variable_sources.py` : un registre à domaine vide et nommé ne rend que le nommé ; `Domain(name=…, origin=…)` s'appelle comme avant ; un projet jamais exporté a toujours `len(missing) == len(FILE_SOURCES)` ; un `checks.json` illisible est dit avec son nom et ne vide pas les charges ; `tests/test_palette_index.py` passe |
| 3 | **L'identité d'un calcul.** `calc/variable_calc.py` : `CalcRef`, les tables sorte de calcul → onglet et sorte de vérification → onglet (`kind` et `fire` de l'enregistrement, ARCH-RISK-001), `assemble(domaines, index, lectures)` qui pose `tab`, `calc` et `results` (les `results` de l'export, la clé `eta` des vérifications), rapproche les domaines de document par `domain-files.json` complété de `formulas.json` (REQ-002), puis `Family` : les sœurs, la source qui calcule (export, puis fichier, puis document), `imprimé` (vrai, faux, inconnu), le nœud (`dependency_graph.target`). La constante `RESULT_KEY` est ajoutée à `member_check` et `steel_check`. | `calc/variable_calc.py`, `calc/domains/member_check.py`, `calc/domains/steel_check.py` | REQ-001 à REQ-004, ARCH-008, ARCH-011, ARCH-012 | `tests/test_variable_calc.py` (sans Qt) : chaque domaine d'export et de fichier de l'exemple a un `tab` (FE-01 et FE-02 → feu, ZT-01 → traction, `poutre-p1` → Domaines) ; `SL` : calcule l'export, sœurs fichier et document, imprimé ; documents non lus : inconnu ; `A1.q_k` est un résultat dans les trois sources ; `S10 - 1 kN Mitte` sans calcul ; un identifiant en double sans calcul et nommé ; renommer un cas ne rattache plus le document ; `eta` au dernier `#eq` de chaque vérification de l'exemple ; le module s'importe sans PySide6 |
| 4 | **Le menu, le filtre, le groupement.** `calc/variable_query.py` : l'arbre de navigation à partir d'une navigation donnée (groupes, sections par la règle de la fenêtre, onglets, entrées « Document » par document, « Sans onglet »), les nombres dans la source choisie, le filtre (chaque mot, unité, résultats seulement, étiquettes menu / source / domaine), le groupement par domaine dans l'ordre de la navigation, les domaines rangés sous leur onglet, le gris « pas imprimé », les unités les plus fréquentes d'abord, le compte, les textes de liste vide. | `calc/variable_query.py` | UI-002, UI-003, UI-005, UI-006, ARCH-001, ARCH-005, ARCH-RISK-002 | `tests/test_variable_query.py` (sans Qt) : « kn neige » ne garde que des kN dont le cas ou l'onglet dit neige ; `q_k` sous un titre par domaine, aucun titre sans variable ; un groupe vaut la somme de ses onglets, une entrée à zéro est inactive ; la source « Export » ne laisse que l'export ; un second clic relâche le domaine ; pendant le choix d'un champ, seuls les nombres acceptés sont comptés |
| 5 | **La sélection.** `calc/variable_select.py` : clic, Ctrl+clic et case, Maj+clic à travers les domaines (titres sautés), Ctrl+Maj, case d'en-tête, clavier, la dernière cliquée et le point de départ, la sélection qui survit au filtre, l'ordre de la copie, le mode d'une seule valeur. | `calc/variable_select.py` | UI-009, UI-010, REQ-007, REQ-008, D-15 | `tests/test_variable_select.py` (sans Qt) : chaque geste de UI-009 ; une variable choisie puis masquée reste choisie et la copie l'ordonne après les affichées ; en mode d'une valeur, Ctrl+clic n'en prend pas deux |
| 6 | **La fiche et la commande.** `calc/variable_card.py` : en-tête, chemin, commande et phrase d'inclusion des trois sources par les `call_*` existants et `formula_domain.include_call`, « Vient de » en clés de mots (`variables.parse_source`), calcul, choix, niveau, « Le même calcul ailleurs » (un bouton par sœur), fiche d'un domaine seul (nombres de variables et de résultats, `#include`), lignes de la copie multiple. | `calc/variable_card.py` | REQ-006, UI-010 (lignes), UI-011, UI-012, ARCH-RISK-010 | `tests/test_variable_card.py` (sans Qt) : la commande et la phrase d'une variable d'export, de fichier (une charge, une vérification, un domaine de l'onglet Domaines) et de document ; aucune commande pour une variable sans nom de domaine ; trois variables mélangées → trois lignes dans l'ordre de la liste ; la désignation allemande telle qu'écrite ; le domaine `snow-load · SL` ; un bouton de sœur choisit l'autre source |
| 7 | **Les deux widgets réutilisables.** `TagSearchBar` (étiquettes amovibles, × , ⌫ dans une barre vide dans l'ordre domaine / source / menu, le `QLineEdit` exposé) et `TreeMenu` (bouton + popup `Qt.Popup` en arbre, entrées grisées, Échap et clic ailleurs, placé par `place`) ; un style d'étiquette dans la feuille de style de `theme.py`, couleurs de `theme.json`. Aucun mot : l'appelant les donne. | `calc/tools/tag_search_bar.py`, `calc/tools/tree_menu.py`, `calc/tools/theme.py` | UI-004, UI-002, ARCH-002 | `tests/test_tag_search_bar.py`, `tests/test_tree_menu.py` : trois étiquettes, ⌫ puis ×, le texte tapé intact ; une entrée grisée ne se choisit pas, Échap ferme ; les deux s'emploient sans variables ni import de `variables_tab` |
| 8 | **La liste.** `variables_list.py` : `QAbstractTableModel` plat (titres et variables), `QTableView` en `NoSelection` qui donne clics, modificateurs et touches à `variable_select` et peint fond et cases, symbole par `richtext.MathDelegate`, valeur à droite en chiffres tabulaires, encadré du résultat à la couleur d'accent du thème (clair et sombre), texte coupé par « … » avec l'infobulle entière, largeurs `Interactive` de 120 / 120 / 76 px que ni une recherche ni un redimensionnement de la fenêtre ne changent, double-clic sur un bord = la largeur d'origine, case d'en-tête, lignes de titre en `setSpan`. | `calc/tools/variables_list.py` | UI-007, UI-008, UI-009, ARCH-007, ARCH-RISK-009 | `tests/test_variables_list.py` : largeurs égales après deux recherches ; glisser un bord, `widths()` / `set_widths()` ; un résultat est encadré et pas une autre variable, aux deux thèmes ; aucun ★ ; les cases suivent chaque geste ; un titre ne se choisit ni au clic ni par une plage ; la liste ne se replie pas |
| 9 | **Les mots.** `variables_words.py` : `STRINGS` fr / de / en de l'onglet (menu, source, légende, « pas imprimé », barre de sélection, fiche, « Vient de », phrases d'inclusion, « Calculé dans… », « rappelle », en-têtes), les clés `vr_*` qui ne servent plus retirées (nom, provenance, domaine, tous les domaines, Affichage), la ligne de `woodcore_gui_words.py` qui fusionne les mots changée de module ; les raisons d'inactivité de « Ouvrir l'onglet » dans les mots de la fenêtre. | `calc/tools/variables_words.py`, `calc/tools/woodcore_gui_words.py` | ARCH-006 | `tests/test_i18n.py` : aucune clé orpheline ni manquante, trois langues, pas de ß ; les clés se trouvent par le code qui les nomme (littéraux) |
| 10 | **La fenêtre.** `MainWindow.can_open_tab(key)` (document montré, document fait, onglet réservé, choix en cours → la raison en clé de mot) et `show_tab(key, node=None)` (l'onglet devant par le chemin de la navigation, puis `open_object(node)` s'il le liste) ; `open_object` et `begin_variable_pick` inchangés. | `calc/tools/woodcore_gui.py` | REQ-009, REQ-008, ARCH-010, ARCH-RISK-006 | `tests/test_window.py`, `tests/test_modes_window.py` : chaque raison donne un refus nommé ; `show_tab("tab_ac_snow", "load:snow-load/SL")` ouvre `SL` ; Python passe devant sans cas ; **pour chaque domaine de l'exemple qui a un nœud, l'onglet de `Domain.tab` est celui dont `lists_object(nœud)` répond** (la table de l'étape 3 tenue aux onglets réels) ; chaque clé des tables est une `TabSpec` de `tab_registry` |
| 11 | **Le contenu.** `VariablesBrowser` (la forme d'un service : `NAME`, `mount`, `state` / `restore`, phases `shown`, `mode_changed`, `leave`) qui tient les trois volets (`QSplitter`, 260 px au départ à gauche), le menu, le segment de la source (`chrome.SegmentedSwitch`), la liste des domaines rangés sous leur onglet et sa légende, la barre à étiquettes, le filtre d'unité, « Résultats seulement », le compte, la barre de sélection et « Copier », la liste, la fiche (`variables_detail.py`), « Ouvrir l'onglet » (par `can_open_tab` / `show_tab`), le mode « Choisir pour un champ » (`begin_pick`, `end_pick`, l'encadré « Importer », la valeur refusée dite), la lecture en fil, le bandeau et « Relire les documents » inchangés. | `calc/tools/variables_browser.py`, `calc/tools/variables_detail.py` | UI-001 à UI-012, REQ-007 à REQ-009, ARCH-009 | `tests/test_variables.py` réécrit : le navigateur construit **sans coque** lit, filtre, choisit, copie (ARCH-009) ; les comportements gardés d'avant (une seule lecture, l'automatique éteinte pour la suite, la lecture qui échoue garde les valeurs, le bouton grisé dit pourquoi, trois langues sans ß) ; le choix pour un champ en kN (REQ-008) ; `selected_key()` / `selected_keys()` (REQ-007) |
| 12 | **La coque et le retrait de l'ancien.** `VariablesTab(QWidget)` ne fait que monter le contenu et rediriger (`begin_pick`, `end_pick`, `selected_key`, `selected_keys`, `variable`, `address`, `select_key`, `view_state`, `restore`, `on_shown`, `on_mode`, `confirm_leave`, `search`) ; `VIEWS`, `install_display`, `display_entries`, `chosen`, `RESULT_MARK`, la liste `QTreeWidget` d'avant et la fabrique de bulles de provenance disparaissent ; `view_state` aux nouveaux noms, l'ancien état lu sans erreur. | `calc/tools/variables_tab.py` | UI-001, UI-007, REQ-007, ARCH-004, ARCH-RISK-006, ARCH-RISK-007, ARCH-RISK-011 | `tests/test_variables.py` (état d'avant lu, aucun ★, aucun `dirty`), `tests/test_linkable_spin.py`, `tests/test_formula_tab.py`, `tests/test_editor_buttons.py`, `tests/test_text_tool.py`, `tests/test_command_palette.py` (le texte arrive dans `search`), `tests/test_tab_overrides.py` (l'entrée `confirm_leave` de `VariablesTab` ne change pas), `tests/test_window.py` (un onglet sans vues), `tests/test_views.py`, `tests/test_tab_registry.py` |
| 13 | **Le code mort.** Par grep avant chaque retrait : `call_find` (`build_reference_calls.py`, `build_reference.py`) et ses tests, `ds_note_document_variable` et `ds_note_whole_document` de `display_options.py` s'ils n'ont plus d'utilisateur ; `views.DATA_VIEWS` reste avec un commentaire (il part avec #106). | `calc/build_reference_calls.py`, `calc/build_reference.py`, `calc/tools/display_options.py`, `calc/tools/views.py` | ARCH-RISK-013, ARCH-004 | `tests/test_call_command.py`, `tests/test_display_options.py` (s'il existe), `tests/test_i18n.py`, `tests/test_views.py` |
| 14 | **Vérification visuelle et mesures** (la compétence `run`) : l'onglet sur une copie de l'exemple, aux trois langues et aux deux thèmes — les noms entiers à 260 px, le menu (ouverture, Échap, clic ailleurs, entrées grisées), les étiquettes (×, ⌫), la liste groupée, l'encadré, les largeurs glissées, gardées et rendues par le double-clic, Ctrl / Maj / cases / case d'en-tête, « Copier les n commandes » collé dans un éditeur, la fiche d'une variable et d'un domaine, « Ouvrir l'onglet » pour Neige, Flexion, Résistance au feu, Python, un domaine de document et un onglet réservé, le choix pour un champ depuis « Traction » ; le temps d'une frappe (< 50 ms) et l'ouverture de la fenêtre (CON-005 de #106). Dire à la session de #112 (`SendMessage`) les deux lignes de la table qu'elle change (ARCH-011). | — | tous UI, ARCH-RISK-014 | captures consignées dans le journal (§16) ; les mesures y sont écrites |
| 15 | **La documentation, le catalogue, la suite et la vérification indépendante.** `docs/ui/tab-variables.md` réécrit (16 Ko au plus ; ce qui est histoire — la vue Affichage, la provenance en colonne — déplacé verbatim dans `docs/history/`) ; `docs/decisions.md` §13 (D-4, D-5, D-6, D-10 à D-18, par édition ciblée, LF) et `docs/decisions-index.md` ; `docs/architecture/layout.md` (les modules) ; `docs/domain/variable-links.md` (la fiche porte l'encadré « Importer ») ; `docs/open-questions.md` (l'arrondi à six décimales des fichiers dépliés, T45, s'il n'y est pas) ; `docs/conventions/testing-catalogue-window.md` (les lignes de `test_variables.py` et `test_variable_sources.py` mises à jour, sept lignes nouvelles) ; `CHANGELOG.md` (une entrée) ; les pages « Nouveautés » de la version en cours dans `website/content/{fr,de,en}/changes/` (une section ajoutée à celle que #115 a laissée, ou la suivante si la version a changé) ; la suite complète en arrière-plan (`python tests/run_tests.py`), les échecs rapportés avec leur sortie ; `verify-requirements` par un agent indépendant. | `docs/`, `CHANGELOG.md`, `website/content/*/changes/` | §11 « Documentation » | `tests/test_docs_coherence.py` (taille, liens, une ligne par fichier de test), `tests/test_module_size.py`, `tests/test_module_imports.py`, `tests/test_site.py` ; la suite complète verte ; §15 rempli |

**Les risques de la revue dans le plan** : ARCH-RISK-001 → étape 3 (tables lues de l'enregistrement) et étape 10 (test de concordance avec `lists_object`) ; 002 → 4 et 7 ; 003 → 3 ; 004 → 3 ; 005 → 3 ; 006 → 10, 12 ; 007 → 2, 12 ; 008 → 7 à 12 (le découpage) ; 009 → 8 ; 010 → 6 ; 011 → 11, 12 ; 012 → 3 et 14 (le message à #112) ; 013 → 13 ; 014 → 14 ; 015 → rien à faire que ne pas toucher aux fichiers de #115 (les deux fichiers partagés sont relus avant l'étape 1, comme le préambule le dit). Aucun risque n'est écarté.

## 15. Vérification

Vérification indépendante du 25.10.2026 (agent `requirements-verifier`, contre `209b965` et l'arbre de travail ; 26 fichiers de tests relancés par lui, tous verts). **Verdict : conforme, aucun ❌ ; cinq ⚠️, traités ou consignés ci-dessous.**

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `variable_calc.tab_of` lit `kind` et `fire` ; `test_variable_calc` (onglet de chaque domaine, FE-01/FE-02 → feu, clés = `TabSpec`) ; `test_variables::test_the_tab_of_each_domain_is_the_one_whose_lists_object_answers` |
| REQ-002 | ✅ | `variable_calc._calculation` (`domain-files.json` + `formulas.json`) ; nom en double, cas renommé, domaine déclaré à la main testés |
| REQ-003 | ✅ | `Assembly.computing/siblings/printed/node` ; imprimé vrai, faux, inconnu testés |
| REQ-004 | ✅ | `assemble` pose les résultats ; `q_k` de A1/H dans chaque source ; `RESULT_KEY` tenu aux fichiers de vérification |
| REQ-005 | ✅ | `registry_domains` sans racine ; 918/75 mesuré par un test qui compile les trois documents |
| REQ-006 | ✅ | `test_variable_card` (trois sources, domaine entier, ordre de copie) |
| REQ-007 | ✅ | Ctrl+clic ×3 : `selected_key` = dernière, `selected_keys` dans l'ordre ; palette → `search` ; appels des onglets à champs liés inchangés |
| REQ-008 | ✅ | `test_choosing_for_a_field_offers_one_value_of_what_the_field_takes` |
| REQ-009 | ✅ ⚠️ | BI-01 et FE-01 ouverts sur leur cas ; `show_tab` route vers `open_object("snow-load/SL")` (`test_show_tab_opens_the_case_where_the_tab_lists_it`, ajouté après la vérification, par des doublures de `lists_object`/`open_object`) ; le cas SL de l'exemple, lu du classeur, n'est listé par aucun onglet : l'onglet vient devant sans cas (consigné, `open-questions.md`) |
| UI-001 à UI-012 | ✅ | tests des modèles, `test_variables_list`, `test_tag_search_bar`, `test_tree_menu`, `test_variables` ; captures FR clair, DE, FR sombre ; menu fermé par Échap (test) et par un clic ailleurs (popup `Qt.Popup`, vérifié hors écran) |
| ARCH-001 à ARCH-003, 005 à 009, 012 | ✅ | `test_module_imports` (quatre modèles sans Qt), `test_module_size` (plus grand : `variables_browser.py`, < 1000 lignes), `test_palette_index`, `test_the_browser_alone…`, `test_variables_list` |
| ARCH-004 | ⚠️ | coque de redirections ; cinq attributs de plus que la liste (`pick_chosen`, `splitter`, `domains`, `pick_bar`, `pick_label`) pour la fenêtre et les tests des onglets à champs liés — écart justifié, énuméré par `test_the_shell_only_forwards…` ; `views.py` : une ligne de commentaire |
| ARCH-010 | ✅ | `can_open_tab` (quatre refus nommés, `test_modes_window`), `show_tab` (test ci-dessus), `open_object` inchangée |
| ARCH-011 | ⚠️ | les deux lignes de #112 sont dans `CHECK_TABS` ; la session de #112 n'existait pas encore : le message est écrit dans le docstring de `variable_calc`, `decisions.md` et le journal des écarts |
| CON-001 à CON-008 | ✅ | cache, `lib/`, `data/`, schémas inchangés ; LF ; `tab-variables.md` 16,3 Ko ; spec < 100 Ko (revue déplacée) |
| Documentation | ✅ | `tab-variables.md`, histoire, `decisions.md` + index, `layout.md`, `variable-links.md`, `open-questions.md`, catalogue (7 lignes), `CHANGELOG.md`, Nouveautés fr/de/en, prototype copié |

Mesures (étape 14) : une frappe dans la recherche refait la liste en 16 à 20 ms hors écran (< 50 ms) ; captures dans le dossier de travail de la session (`114-01` à `114-07`). Tests adaptés (lisaient des widgets retirés) : `test_linkable_spin` (aide `_listed_domains`), `test_richtext`, `test_modes_window`, `test_views`, `test_i18n`.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #114 (51 points) ; deux questions ouvertes (donnée du rapprochement document ↔ calcul, onglets sans ouverture de cas) |
| 2026-10-24 | specified | réponses de l'ingénieur reportées : Q-001 A (`domain-files.json`), Q-002 A (l'onglet devant, le cas là où l'onglet sait) → D-10, D-11, REQ-002, REQ-009 ; aucune question ouverte |
| 2026-10-24 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (15 risques, dont ARCH-RISK-001 bloquant et corrigé : l'onglet d'une vérification lu de son enregistrement et non du dossier) ; REQ-001, REQ-002, REQ-004, REQ-006 à REQ-009, UI-002, UI-007, UI-009 amendés, ARCH-008 à ARCH-012 et D-12 à D-18 ajoutés ; plan en 15 étapes (§14) ; à confirmer à l'approbation : D-14 (une entrée « Document » par document) et la lecture de Q-002 ; en attente de l'approbation de l'ingénieur |
| 2026-10-24 | approved | approbation unique des huit specs du 24.10.2026 par l'ingénieur (AskUserQuestion) : plan approuvé tel quel ; toutes les propositions « à confirmer » des revues acceptées comme recommandées ; ordre d'implémentation #108 → #115 → #114 → #113 → #112 → #109 → #107 → #106, un agent par issue ; commits et push autorisés au fil du travail ; écarts et questions notés en §16 et posés à la fin |
| 2026-10-25 | implementation | étape 1 : mesures sur master `209b965` — 935 variables dans 78 domaines avec les racines des documents, **918 dans 75** sans elles (les chiffres de l'issue, confirmés), 723 dans 61 pour l'export et les fichiers ; prototype copié dans `docs/requirements/prototypes/2026-10-24-onglet-variables/` (page, images, README avec les mesures) |
| 2026-10-25 | implementation | étape 2 : `variable_sources` — `Domain.tab`, `Domain.calc` (défauts `None`), `Export.index` (`domain-files.json`, `checks.json`, `steel.json`, les identifiants de `formulas.json` ; hors de `missing`, `bad_file` si illisible), la racine des documents plus lue (REQ-005, ARCH-003) ; `tests/test_variable_sources.py` (+3) |
| 2026-10-25 | implementation | étape 3 : `calc/variable_calc.py` (`CalcRef`, tables sorte → onglet, `assemble`, familles, source qui calcule, imprimé, résultats, nœud), `RESULT_KEY` dans `domains/_common.py` relu par `member_check` et `steel_check` (REQ-001 à REQ-004, ARCH-011, ARCH-012) ; `tests/test_variable_calc.py` (16) |
| 2026-10-25 | implementation | étapes 4 à 6 : `calc/variable_query.py`, `calc/variable_select.py`, `calc/variable_card.py` (UI-002 à UI-012 côté modèle, REQ-006, REQ-007) ; `tests/test_variable_query.py` (14, dont un Qt sur `tab_registry` et la fenêtre), `tests/test_variable_select.py` (9), `tests/test_variable_card.py` (10) |
| 2026-10-25 | implementation | étapes 7 à 9 : `tag_search_bar.py`, `tree_menu.py`, style des étiquettes dans `theme.py` ; `variables_list.py` (QTableView plat, NoSelection, encadré à l'accent, largeurs gardées) ; `variables_words.py` (fr/de/en), fusion dans `woodcore_gui_words.py`, raisons de « Ouvrir l'onglet » dans les mots de la fenêtre ; `tests/test_tag_search_bar.py`, `tests/test_tree_menu.py`, `tests/test_variables_list.py` |
| 2026-10-25 | implementation | étapes 10 à 12 : `MainWindow.can_open_tab` / `show_tab` ; `variables_browser.py`, `variables_detail.py` ; `variables_tab.py` réécrit en coque (redirections, `Read`) ; `tests/test_variables.py` (partie onglet réécrite, 60 tests), `test_modes_window.py` (entrée par document, raisons), `test_command_palette.py` (texte dans `search`), `test_views.py`, `test_richtext.py`, `test_linkable_spin.py` (aide `_listed_domains`), `test_i18n.py` adaptés |
| 2026-10-25 | implementation | étape 13 : `call_find` retiré (`build_reference_calls`, `build_reference`, `test_call_command`), `ds_note_document_variable` / `ds_note_whole_document` retirés de `display_options`, `views.DATA_VIEWS` gardé avec un commentaire |
| 2026-10-25 | testing | étape 14 : captures hors écran en français (menu ouvert, étiquettes du filtre, liste groupée et choix multiple, fiche d'un résultat, choix pour un champ) dans le dossier de travail ; le volet de gauche ramené à 120 px au plancher (`test_left_pane_fold`) ; mesure : 918/75 tenus par un test |
| 2026-10-25 | testing | étape 15 : `docs/ui/tab-variables.md` réécrit (16 Ko ; l'ancien dans `docs/history/2026-10-25-tab-variables-before-114.md`), `decisions.md` §13 et index, `layout.md`, `variable-links.md`, `open-questions.md`, catalogue des tests (7 lignes), `CHANGELOG.md`, « Nouveautés » 0.125 fr/de/en |
| 2026-10-25 | completed | vérification indépendante : conforme, cinq ⚠️ traités ou consignés (§15) ; test de `show_tab` sur la neige ajouté ; captures DE et thème sombre, mesure de la frappe ; spec déplacée dans `completed/` |
