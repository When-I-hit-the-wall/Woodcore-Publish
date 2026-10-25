---
id: 2026-10-24-type-donnees
titre: Le type « Données » — DataTab, Variables, Métrés, Dépendances et Commandes construits dessus
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-25
source: issue GitHub #106 (suite de l'issue #95)
docs: [docs/ui/building-a-tab.md, docs/ui/tab-variables.md, docs/ui/tab-dependencies.md, docs/ui/tab-commands.md, docs/ui/window.md, docs/architecture/layout.md, docs/architecture/principles.md, docs/decisions.md]
---

# Le type « Données » — Spécification

## 1. Objectif

Écrire le cinquième type d'onglet de la décision D-05 de la spec `2026-10-23-onglets-types-et-services` : `DataTab`, une base mince qui monte des `tab_host.Service` dans les zones de l'onglet, et y faire passer les quatre navigateurs en lecture : « Variables » (`variables_tab.VariablesTab`), « Métrés » (`metre_tab.MetreTab`), « Dépendances » (`dependencies_tab.DependenciesTab`) et « Commandes » (`commands_tab.CommandsTab`), chacun réduit à ses paramètres (ils n'éditent aucune source : ni liste de cas, ni brouillon, ni « Enregistrer »). Rien ne change pour l'ingénieur : même fenêtre, mêmes mots, mêmes fichiers, hormis ce que #114 (Variables) et #115 (Commandes) ont déjà changé avant elle.

**Cette issue vient après #115 et #114** (ordre d'implémentation prévu : #115, #114, puis #106). Elle migre donc les onglets **réécrits** par ces deux issues, pas ceux d'aujourd'hui : « Commandes » avec ses pages condensées et sa brique de bulle, « Variables » sans vue « Affichage ». §3 dit ce que cela implique ; §7 D-02 le décide ; la base commune avec #107 est le cadre sans cas que celle-ci extrait (réponse A à sa Q-001, D-06 ci-dessous).

## 2. Source

L'issue #106, mot pour mot, par points.

> **T1** — « Suite de l'issue #95. Le type « Données » est décrit dans `docs/ui/building-a-tab.md`, pas encore écrit (décision D-05 de la spec `docs/requirements/completed/2026-10-23-onglets-types-et-services.md`). »
>
> **T2** — « Une base mince `DataTab` sur `TabHost`, son service par défaut : le tableau de ce que contient l'export, « Affichage » au choix. »
>
> **T3** — « Migrer Variables, Métrés, Dépendances et Commandes, chacun en paramètres seulement (ils n'éditent aucune source : pas de liste de cas). »
>
> **T4** — « Tests, guide, décision, CHANGELOG, « Nouveautés ». »

## 3. Exigences fonctionnelles

**État actuel relevé dans le code** (master `be5b85f`, avant #114 et #115). Aucun des quatre onglets ne descend de `TabHost` ni de `SourceEditorTab`. Ce que chacun définit :

| | « Variables » | « Métrés » | « Dépendances » | « Commandes » |
|---|---|---|---|---|
| classe, taille | `VariablesTab(display_view.DisplayTab, QWidget)`, 1193 lignes | `MetreTab(QWidget)`, 229 lignes | `DependenciesTab(QWidget)`, 237 lignes | `CommandsTab(QWidget)`, 850 lignes |
| ce qu'il lit | l'export (`sources.read_export`) et les registres des trois documents compilés (`variables`, lecture dans un `QThread` `Read`, cache) | `data/quantities.json` (`read_export`), les plans enregistrés après lui (`stale_plans`) | le graphe de l'export (`graph_model.read`, `newer_sources`) | `lib/` et ses blocs `///` (`command_docs`), les pages des exemples (`examples`), compilation à la demande (`RenderJob`, `QTimer`) hors de l'allemand |
| vues | `VIEWS = views.DATA_VIEWS` (« Données », « Affichage »), `install_display`, `display_entries` | aucune | aucune | aucune |
| mise en page | barre, bandeau, barre de choix, `QSplitter` à trois volets | bandeau, une carte (portée, plan, positions, tableau), carte du fichier (`ListFileCard`) ; **pas de `QSplitter`** | filtre, bandeau, `QSplitter` à deux volets | champ de recherche, `QSplitter` à deux volets |
| à l'affichage | `on_shown` (relit l'export, lit les documents libres), `on_mode` | `on_shown` (relit l'export) | `on_shown` (relit le graphe) | rien (lit tout à la construction) |
| quitter | `confirm_leave` : attend la lecture en cours, rend `True` (`PERMITTED`) | aucun | aucun | aucun |
| reconstruction | `view_state`, `restore` | `view_state`, `restore` | `view_state`, `restore` | `view_state` ; l'état est relu dans `__init__` |
| contrat lu par d'autres | `begin_pick`, `end_pick`, `selected_key`, `variable`, `address`, `select_key` ; la fenêtre le trouve par `isinstance(t, VariablesTab)` (`woodcore_gui.py:806`) | — | `open` ; le graphe lit `GRAPH_KIND` des autres | — |
| tests | `tests/test_variables.py` (56) | `tests/test_metre_tab.py` (2) | `tests/test_dependency_tab.py` (3) | `tests/test_commands.py` (34) |

Aucun n'a `dirty`, et ce n'est pas un oubli : `VariablesTab` l'explique (commentaire de `__init__`) — la fenêtre prend tout onglet qui a un `dirty` pour un éditeur et lui demande `update_list_marker()`. Un `DataTab` ne doit donc jamais définir `dirty` (REQ-006).

**Ce que « Affichage au choix » devient.** Seul « Variables » a une vue « Affichage » aujourd'hui ; « Commandes » n'en a pas (la v1 du prototype de #115 en avait une, jamais livrée, et #115 D-2 la retire de toute façon). #114 D-4 retire la vue « Affichage » de « Variables » (`VIEWS`, `install_display`, `display_entries`, `chosen`). Après #115 et #114, **aucun onglet de données n'a de vue « Affichage »** : le « Affichage » que T2 laisse « au choix » n'a plus d'utilisateur parmi les quatre. Réponse de l'ingénieur (Q-002, A) : D-07.

**Ce que « le tableau de ce que contient l'export » devient.** La phrase décrit « Métrés » (un tableau des quantités de l'export). « Variables » est un arbre de domaines, une liste et une fiche, lus aussi de documents compilés ; « Dépendances » deux listes d'un graphe ; « Commandes » ne lit pas l'export du tout (elle lit `lib/`). Ce qui est vraiment commun aux quatre est mince : `view_state` / `restore`, `on_shown`, une fenêtre qui les prend pour des navigateurs sans brouillon. Ce que trois partagent est un **bandeau d'état de l'export** (« pas encore exporté », « plus ancien que ses sources »). Le service par défaut est le bandeau seul (D-07).

**Ce que l'ordre #115, #114, #106 implique.**
- #115 réécrit `commands_tab.py` (pages condensées, ligne de la commande à bulles, rendus pré-compilés, brique de bulle partagée dans un module à part) et ne touche pas à la base : « Commandes » est un `QWidget` à `view_state` avant et après. #106 y passe un navigateur dont le contenu a déjà changé ; si #106 passait avant, elle migrerait 850 lignes que #115 va réécrire et les deux issues se disputeraient `commands_tab.py` et `tests/test_commands.py`.
- #114 réécrit `variables_tab.py` et retire `VIEWS`, `install_display`, `display_entries` ; son ARCH-004 le laisse un `QWidget` navigateur « à contrat » (`KEY`, `on_shown`, `confirm_leave`, `view_state` / `restore`, `set_language`, `on_mode`) pour que #106 ne change que sa classe de base, et sans toucher `display_view.py` ni `views.py`. Si #106 passait avant, elle écrirait un service « Affichage » pour « Variables » que #114 supprime aussitôt. C'est aussi #114 qui ajoute `selected_keys()` au contrat (REQ-007 de #114) : #106 migre un contrat à deux fonctions de sélection.
- « Métrés » et « Dépendances » ne dépendent ni de #114 ni de #115 et pourraient passer avant, mais D-18 de la spec #95 veut une version publiée par type migré, vérifiée en bloc (CON-002) : le type n'est prouvé que par ses quatre navigateurs, dont les deux gros.
- #106 vient après #107 (ordre arrêté par l'ingénieur le 24.10.2026 : #108, #115, #114, #113, #112, #109, #107, #106) : le cadre sans cas (`tab_frame.TabFrame`) est donc écrit quand cette issue commence ; voir ARCH-001 et ARCH-009.

### REQ-001 — `DataTab`, base mince, services et phases
- **Exigence** : Woodcore doit offrir `DataTab` (`calc/tools/data_tab.py`), une classe mince qui nomme ses `SERVICES` par défaut, ses `VIEWS` (vide par défaut) et ses `HOOKS` (vide), et qui monte des `tab_host.Service` dans deux zones, « top » (le bandeau) et « body » (le navigateur, qui garde son propre séparateur : D-08), sur le cadre de #107. Il fait courir les phases dans l'ordre de `SERVICES` (au minimum `shown`, `mode_changed`, `leave`, `hidden`), répond `service(nom)` et refuse à la construction un service dont un `NEEDS` manque au domaine (`missing_needs`, message nommant l'onglet, le service et la fonction). Son seul service par défaut est le bandeau de l'état de l'export (D-07).
- **Source** : T2, T1
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_data_tab.py` (nouveau, une ligne au catalogue des tests) monte un `DataTab` par une classe qui ne contient que des paramètres, sur un faux service de lecture, et y trouve chaque service par `tab.service(nom)` ; une phase court dans l'ordre ; un `NEEDS` manquant lève l'erreur nommée.

### REQ-002 — « Variables » (celle de #114) en paramètres seulement
- **Exigence** : `VariablesTab` doit être une classe de paramètres sur `DataTab` ; ce que #114 en a fait — le menu des onglets, la source, la liste groupée par domaine, la barre à étiquettes, le choix multiple, la fiche, la barre de choix pour un champ, le bandeau, « Relire les documents » et sa lecture dans un fil — se comporte exactement comme à la fin de #114. Le contenu du navigateur est **un service entier** (D-03), avec le bandeau en service à part (REQ-009).
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : les tests de `tests/test_variables.py` (56 aujourd'hui, à recompter après #114, qui les réécrit) passent, leur accès aux widgets adapté à `tab.service("browser")` sans qu'une assertion de comportement change ; `VariablesTab` ne définit aucun nom hors `tab_host.PARAMS` et `DataTab.HOOKS`.

### REQ-003 — « Métrés » en paramètres seulement
- **Exigence** : `MetreTab` doit être une classe de paramètres sur `DataTab` : la portée, le plan, les positions, le tableau des quantités de l'export (`quantities.summary`, jamais mesuré dans la fenêtre), la date de l'export, le bandeau des plans enregistrés depuis, et la carte du fichier (REQ-010) se comportent exactement comme aujourd'hui.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : les 2 tests de `tests/test_metre_tab.py` passent, adaptés à `tab.service(…)` sans qu'une assertion change ; `MetreTab` ne définit que des paramètres.

### REQ-004 — « Dépendances » en paramètres seulement
- **Exigence** : `DependenciesTab` doit être une classe de paramètres sur `DataTab` : le filtre, la liste des objets par genre, les deux listes « dépend de » et « utilisé par », le bandeau, le double-clic qui ouvre l'objet dans son onglet (`MainWindow.open_object`), l'état gardé à travers une reconstruction (séparateur, filtre, nœud choisi).
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : les 3 tests de `tests/test_dependency_tab.py` passent sans qu'une assertion change ; `DependenciesTab` ne définit que des paramètres.

### REQ-005 — « Commandes » (celle de #115) en paramètres seulement
- **Exigence** : `CommandsTab` doit être une classe de paramètres sur `DataTab` ; ce que #115 en a fait — le champ de recherche, l'arbre par catégories, la page condensée, la ligne de la commande à bulles, le volet de droite, les exemples et leurs niveaux, la compilation à la demande des exemples hors de l'allemand — se comporte exactement comme à la fin de #115. La compilation en tâche (`RenderJob`, `QTimer`) s'arrête quand l'onglet est caché ou quitté (phase `hidden`), sans en faire une règle nouvelle si #115 ne l'a pas.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : les tests de `tests/test_commands.py` (34 aujourd'hui, étendu par #115) passent, adaptés à `tab.service(…)` sans qu'une assertion de comportement change ; `tests/test_richtext.py:196` retrouve encore l'onglet par sa classe ; `CommandsTab` ne définit que des paramètres.

### REQ-006 — Un onglet de données ne garde rien : ni `dirty`, ni `save`, une seule `confirm_leave`
- **Exigence** : `DataTab` ne doit définir ni `dirty`, ni `save`, ni `current_id`, ni `source` : un navigateur n'est pas un éditeur (la fenêtre le distingue par `dirty`). Il répond une fois à `confirm_leave` : il court la phase `leave` (un service qui tient un fil — la lecture des documents de « Variables », qui ne se coupe pas — l'attend) puis rend toujours `True`. Aucune des quatre classes ne redéfinit `confirm_leave`.
- **Source** : T3 ; commentaire de `VariablesTab.__init__` et `tests/test_tab_overrides.py`
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_tab_overrides.py` : l'entrée `("VariablesTab", "confirm_leave")` de `PERMITTED` est retirée (le test des entrées périmées l'exige) ; `tests/test_data_tab.py` vérifie `not hasattr(DataTab, "dirty")` et `confirm_leave()` : attend un faux service à fil puis rend `True` ; `tests/test_window.py` traite les quatre onglets comme des navigateurs (aucun marqueur, aucun `update_list_marker`).

### REQ-007 — Ce que la fenêtre appelle sur ces onglets
- **Exigence** : la fenêtre appelle sur un onglet `on_shown` (affichage), `on_mode(mode)` (changement de document, `woodcore_gui.py:330` ; aujourd'hui « Variables » seule), `view_state` et `restore` (reconstruction), `confirm_leave`, et lit `splitter` (liaison des tailles, `woodcore_gui.py:606`, `getattr` tolérant) et `view` / `VIEWS` (le sélecteur de vues, caché pour un onglet sans vues). `DataTab` doit répondre à chacun une fois, en les faisant suivre aux services par des phases ; l'état de chaque service passe par `state()` / `restore(state)` et le `view_state` du type, le séparateur étant celui du type. « Métrés », qui n'a pas de séparateur aujourd'hui, n'en gagne pas de visible. `set_language` de « Variables » n'a pas d'appelant trouvé dans la fenêtre (un changement de langue reconstruit l'onglet) : repris seulement s'il en a un à l'implémentation, retiré sinon.
- **Source** : T3 ; inféré de ARCH-009 de la spec #95
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_tab_registry.py` étendu : chaque nom de l'interface du type existe sur `DataTab` ; changer de document relit « Variables » comme aujourd'hui (`tests/test_modes_window.py:305`) ; reconstruire la fenêtre garde le séparateur, la recherche, le filtre et le choix de chaque onglet (un test par onglet, sous les clés qui ne sont lues que dans la session).

### REQ-008 — Le contrat de « Variables » lu par d'autres reste appelable
- **Exigence** : `begin_pick`, `end_pick`, `selected_key`, `selected_keys` (#114), `variable`, `address` et `select_key` — lus par `MainWindow.begin_variable_pick`, `linkable_spin`, l'onglet « Formule », `statics_tab_properties`, `text_pane` et au moins sept fichiers de tests — doivent rester appelables avec le sens que #114 leur donne, depuis un `VariablesTab` qui ne définit que des paramètres. La façon est la réponse A de l'ingénieur à Q-001 (D-06, ARCH-007) : une redirection déclarée par `EXPOSES`.
- **Source** : T3 ; contrat de #114 (REQ-007 de #114, ARCH-004)
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_variables.py`, `tests/test_linkable_spin.py`, `tests/test_formula_tab.py`, `tests/test_editor_buttons.py`, `tests/test_text_tool.py` passent ; aucun de leurs appels n'est modifié (D-06) ; `isinstance(t, variables_tab.VariablesTab)` trouve encore l'onglet.

### REQ-009 — Un service « bandeau de l'état de l'export », commun
- **Exigence** : ce que trois onglets disent chacun à leur façon — l'export n'est pas fait, ou il est plus ancien que ses sources (`dg_not_exported` / `dg_stale` de « Dépendances », le bandeau de « Métrés », celui de « Variables ») — doit être un service du type (D-19 de la spec #95 : une fonctionnalité visible que plusieurs onglets emploient), et que le navigateur de l'onglet alimente par le contexte (`ctx.say(texte, genre)`, D-10) : le service n'est qu'une étiquette d'avertissement (genre « warning » ou « danger », celui de « Variables » en a deux) ; il ne lit ni ne recalcule rien : la date et la liste des sources plus récentes viennent de `graph_model.newer_sources`, `stale_plans` et de ce que lit « Variables », dans le navigateur. Les textes de chaque onglet restent les siens.
- **Source** : T2 ; D-19 de la spec #95 ; inféré
- **Priorité** : devrait
- **Critère d'acceptation** : `tests/test_data_tab.py` monte le service avec un faux navigateur qui dit un avertissement, un danger puis rien, et lit texte, genre et visibilité ; les trois tests de bandeau existants passent sans qu'une assertion change ; aucune fonction de lecture de l'export recopiée dans le service (`tests/test_no_duplicates.py`).

### REQ-010 — La carte du fichier de « Métrés » : ses écrivains gardés à leur définition
- **Exigence** (amendée par la revue, D-09) : la carte « Fichier de la liste » (`list_file_card.ListFileCard`, qui écrit `Positions/quantities.typ` : « Écrire le fichier », « Ajouter », « Copier l'inclusion ») reste un objet que le navigateur de « Métrés » construit dans sa page — elle sert aussi « Journal » et « Positions », qui ne bougent pas, et ses boutons sont reliés à ses propres méthodes. Ses écrivains `write` et `add` sont gardés **à leur définition, une fois** : `ListFileCard.WRITERS = ("write", "add")` et `tab_guard.guard_service(ListFileCard)` dans `tab_registry.py`, comme `guard_actions(source_archive.Actions)`. Ce garde **corrige un manque relevé** : ni `ListFileCard.write` ni `list_files.write` ne refusent aujourd'hui un projet ouvert en lecture seule ; dans ce projet, les deux boutons de **chacun des trois onglets** (« Métrés », « Journal », « Positions ») sont désormais refusés avec le message habituel (`app.refuse_read_only`). `list_files.write` n'est pas touchée : l'export (`export_all.py:464`, `sheets.py:354`) l'appelle. Le contenu écrit, le chemin et le texte ne changent pas. Aucun nom n'entre dans `tab_guard.WRITERS` : `write` et `add` sont des noms trop courants, le garde par nom les poserait sur toute méthode homonyme d'une classe d'onglet.
- **Source** : T3 (« ils n'éditent aucune source » — mais « Métrés » écrit un fichier) ; ARCH-004 de la spec #95 ; revue (ARCH-RISK-005)
- **Priorité** : devrait
- **Critère d'acceptation** : le test existant d'écriture du fichier (`tests/test_metre_tab.py`) passe tel quel ; un test négatif construit la carte sur une fenêtre factice en lecture seule : `write()` et `add()` renvoient `False` et n'écrivent rien, pour « Métrés » et pour « Journal » ; `test_every_writer_a_tab_reaches_is_guarded_where_it_is_defined_and_once` couvre `ListFileCard`.

### REQ-011 — Un test refuse toute redéfinition dans un onglet du type
- **Exigence** : Woodcore doit refuser par un test qu'une classe d'onglet sur `DataTab` définisse autre chose que ses paramètres et les `HOOKS` du type (vide au départ).
- **Source** : T3 ; D-07 de la spec #95
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_tab_overrides.py` : `_types()` rend `(CalcTab, DataTab, …)` (avec ce que #107 y ajoute) ; `_unauthorised` échoue sur un onglet de test qui redéfinit `on_shown` ou assigne une `lambda` ; les quatre onglets passent ; `_tab_classes` s'arrête au type.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Aucun changement visible
- **Exigence** : la fenêtre, la navigation (« Métrés » dans le groupe « Données » de la navigation, les trois autres dans « Référence »), les mots, les icônes, les bulles, l'ordre des panneaux, les tailles gardées et la disposition de chaque onglet sont ceux de la fin de #114 et de #115. L'onglet ne gagne ni ne perd de vue : le sélecteur de vues reste caché pour les quatre.
- **Source** : T3 ; inféré (refonte de structure, comme UI-002 de la spec #95)
- **Langues** : fr / de / en
- **Critère d'acceptation** : captures des quatre onglets avant et après, prises **après** #114 et #115, jointes à la vérification ; `tests/test_i18n.py` passe sans clé ajoutée ni retirée dans les trois langues, sauf mots génériques propres au type.

### UI-002 — Aucun fichier de projet ni rapport ne change, hors le garde de lecture seule
- **Exigence** : aucun fichier de projet écrit (`Positions/quantities.typ`, `data/`) ni aucun rapport compilé ne change, octet pour octet, pour les mêmes gestes, sur `tests/projet-exemple/` ; les seules différences sont le refus des deux boutons de la carte du fichier dans un projet ouvert en lecture seule (REQ-010) et, si l'ingénieur le confirme, l'aspect du bandeau de « Métrés » (D-10).
- **Source** : inféré
- **Langues** : —
- **Critère d'acceptation** : les tests des quatre onglets et `tests/test_export_all.py` passent ; le diff ne touche aucun fichier de `calc/` hors `calc/tools/` et ni `lib/`.

### UI-003 — Les navigateurs restent des navigateurs dans la fenêtre
- **Exigence** : aucune pastille « non enregistré », aucune question à la fermeture d'un onglet de données (sauf la lecture en cours de « Variables », attendue comme aujourd'hui), aucun enregistrement automatique n'est appelé sur eux.
- **Source** : REQ-006 ; `woodcore_gui.py` (`update_tab_marks`, `leave_tab`)
- **Langues** : —
- **Critère d'acceptation** : `tests/test_window.py` : les quatre onglets n'ont pas de marqueur ; l'autosave n'appelle sur eux ni `save` ni `dirty`.

## 5. Exigences d'architecture

### ARCH-001 — `DataTab` repose sur le cadre de #107
- **Exigence** : `TabHost` suppose des cas ; l'ingénieur a répondu (Q-001 de #107, A) qu'on en extrait un cadre sans cas, `tab_frame.TabFrame` (`calc/tools/tab_frame.py`, écrit par #107 avant cette issue), sur lequel reposent `TabHost`, `DocumentTab` et, ici, `DataTab`. `DataTab(TabFrame)` n'écrit **que** : son contexte (`DataContext(FrameContext)` : `say`, `kept`), les crochets `frame_body` (la zone « top » au-dessus de la zone « body ») et la fabrication d'`EXPOSES`. Il emploie `Service`, `run_phase`, `service_named`, `missing_needs`, les phases `shown`, `mode_changed`, `hidden`, `leave`, `view_state` / `restore` et `confirm_leave` du cadre, sans second mécanisme. Contrairement à la note de passation de #107, il ne demande au cadre **ni séparateur facultatif ni colonne sans barre** (D-08) : chaque navigateur garde son séparateur, et `DataTab.splitter` est celui du premier service qui en déclare un.
- **Source** : T2 ; Q-001 de #107 (réponse A) ; ARCH-003 de la spec #95
- **Critère d'acceptation** : aucune fonction de `tab_frame.py` ni de `tab_host.py` recopiée dans `data_tab.py` (`tests/test_no_duplicates.py`) ; les tests de `CalcTab` (`tests/test_calc_tab_base.py`, `tests/test_tab_services.py`, `tests/test_snow_source.py`, `tests/test_load_tab.py`) et ceux de `DocumentTab` passent sans qu'une assertion change.

### ARCH-002 — Aucun service n'appelle un autre service
- **Exigence** : D-06 vaut pour ce type. Ce qui relie le navigateur au bandeau passe par le contexte du type (`ctx.say`, qui trouve le service qui offre `"banner"`), jamais par un service qui tient un autre. Les parties internes d'un navigateur (la barre de choix de « Variables », sa liste et sa fiche) restent dans son service entier.
- **Source** : D-06 de la spec #95
- **Critère d'acceptation** : `tests/test_tab_services.py` (imports des modules de services, aucun service n'en tient un autre) couvre les services du type.

### ARCH-003 — La lecture et le calcul restent dans `calc/`
- **Exigence** : seuls `calc/tools/` (les onglets, leurs services, le registre, la garde) et `tests/` changent ; `calc/variable_sources.py`, `calc/variables.py`, `calc/domains/quantities.py`, `calc/domains/list_files.py`, `graph_model`, `command_docs` et `command-pages.json` ne gagnent ni ne perdent une règle en changeant d'hôte. Un service montre et appelle ; il ne recalcule rien.
- **Source** : principe « la logique du domaine est indépendante de l'interface » (CLAUDE.md)
- **Critère d'acceptation** : revue du diff : aucun fichier de `calc/*.py` hors `calc/tools/` modifié ; `git diff --stat` joint à la vérification.

### ARCH-004 — Les mots restent à leur place
- **Exigence** : les mots de chaque navigateur (`vr_`, `mt_`, `dg_`, ceux de « Commandes ») restent dans le `STRINGS` de son module, fusionnés comme aujourd'hui par `woodcore_gui_words.py` ; le service est sans mots propres (`Service.WORDS_MODULE = None`), l'onglet lui donne les clés de ses textes (bandeau). Si le type a des mots génériques, ils vont dans un `STRINGS` au niveau d'un module du type, listé dans `SERVICE_WORDS`.
- **Source** : ARCH-008 de la spec #95 ; CLAUDE.md « No hardcoding »
- **Critère d'acceptation** : `tests/test_i18n.py` passe, y compris le contrôle des clés partagées par deux modules de services.

### ARCH-005 — Le registre et la garde ne se limitent plus à `TabHost`
- **Exigence** : `tab_registry.GUARDED_SERVICES` ne retient aujourd'hui que les services des classes `issubclass(spec.factory, tab_host.TabHost)` ; une classe sur `DataTab` doit y entrer sans que chaque type ajoute sa condition. #107 (P02) fait entrer toute classe de `TabFrame` : #106 n'y ajoute que la garde de la carte du fichier (REQ-010) ; `tab_registry.py`, `tab_guard.py`, `tab_host.py` et `tests/test_tab_overrides.py` sont partagés avec #107, #112, #113, #114, #115 (CON-003).
- **Source** : ARCH-004 de la spec #95 ; inféré du code (`tab_registry.py`, `GUARDED_SERVICES`)
- **Critère d'acceptation** : les services d'un `DataTab` entrent dans `GUARDED_SERVICES` (un faux service écrivain de test le prouve) ; `ListFileCard` est gardée (REQ-010) ; `test_every_writer_a_tab_reaches_is_guarded_where_it_is_defined_and_once` passe et la couvre ; `GUARDED_TABS` ne retient aucun onglet de données (aucun écrivain de `tab_guard.WRITERS`).

### ARCH-006 — La classe de chaque onglet garde son nom et son module
- **Exigence** : `VariablesTab` reste dans `variables_tab.py`, `CommandsTab` dans `commands_tab.py`, `MetreTab` dans `metre_tab.py`, `DependenciesTab` dans `dependencies_tab.py`, et leurs `TabSpec` ne changent pas : la fenêtre, la palette de commandes (`command_palette.py`) et les tests les trouvent par classe ou par clé (`isinstance(t, variables_tab.VariablesTab)`, `type(t).__name__ == "CommandsTab"`).
- **Source** : inféré (`woodcore_gui.py:806`, `tests/test_window.py:172`, `tests/test_richtext.py:196`)
- **Critère d'acceptation** : les tests ci-dessus passent sans changer leur recherche d'onglet ; `tab_registry.SPECS` n'est pas modifié pour ces quatre lignes.

### ARCH-007 — `EXPOSES` : une redirection déclarée, pour des méthodes et des attributs
- **Exigence** (revue ; réponse A à Q-001) : `EXPOSES = {nom: service}` est un paramètre de l'onglet (il entre dans `tab_host.PARAMS`) ; `DataTab.__init_subclass__` pose sur la classe, pour chaque nom, un descripteur `Exposed` qui rend `getattr(tab.service(service), nom)` — une méthode liée ou la valeur d'un attribut (« Variables » expose aussi `search`, #114) —, et dont `__set__` écrit sur le service. Le descripteur n'est pas une méthode écrite dans la classe : `_unauthorised` admet les noms de `EXPOSES` dont la valeur de la classe est un `Exposed` et refuse tout autre (une `lambda` assignée sous un nom exposé échoue). Un nom absent du service lève `AttributeError` (donc `getattr(tab, nom, None)` et `hasattr` de la fenêtre restent justes), un service absent lève la `KeyError` de `service_named`. `EXPOSES` ne sert qu'au contrat que d'autres appellent (REQ-008) ; les tests de l'onglet lui-même passent par `tab.service(...)`.
- **Source** : réponse A à Q-001 ; note de passation de §13 de #107 ; revue
- **Critère d'acceptation** : `tests/test_data_tab.py` : un faux onglet expose une méthode et un attribut ; `hasattr(Classe, nom)` est vrai sur la classe (le test des noms de `TAB_API`) ; l'écriture passe au service ; un nom ou un service absent donne l'erreur nommée ; `tests/test_tab_overrides.py` accepte les noms exposés et refuse une `lambda` homonyme.

### ARCH-008 — Un navigateur se construit une fois, avec l'état que la fenêtre lui rend
- **Exigence** (revue) : « Commandes » relit `app.views` dans son `__init__` pour ne remplir son arbre qu'une fois (`first_fill`, lignes ouvertes, niveaux) ; le cadre appelle `restore` **après** le montage des services. Le contexte offre donc `ctx.kept(service)` (l'état que la fenêtre a gardé pour ce service, ou `{}`), que le service lit dans `mount` ; `restore(état)` du service reste appelé par le cadre et ne refait rien de ce que `mount` a déjà fait avec le même état. Aucun navigateur ne se remplit deux fois à la construction (CON-005). La forme de `view_state` change (`{"splitter", "services": {nom: état}}`) : elle ne vit qu'en mémoire (CON-001).
- **Source** : revue (`commands_tab.py:402-407`)
- **Critère d'acceptation** : `tests/test_data_tab.py` : un faux service compte ses remplissages (un seul à la construction avec un état gardé, un seul sans) ; `tests/test_commands.py` et `tests/test_variables.py` : la reconstruction garde la recherche, les lignes ouvertes, le séparateur et le choix.

### ARCH-009 — Les formes de #107, #114 et #115 sont relues avant le premier pas
- **Exigence** (revue) : cette spec est écrite contre le **plan** de #107 (cadre), #114 (`VariablesBrowser`, `can_open_tab`, `show_tab`) et #115 (trois composants), non contre leur code, qui n'existe pas encore. Le pas 0 du plan relit `tab_frame.py`, `document_tab.py`, `variables_browser.py`, `variables_tab.py`, `commands_tab.py` et ses composants, et s'arrête, avec un message à l'ingénieur, si une forme diffère de §13 au point de changer un REQ.
- **Source** : CON-004 ; revue
- **Critère d'acceptation** : le relevé du pas 0 est joint à §15 ; chaque écart y est dit et les REQ touchés amendés avant le pas 1.

## 6. Contraintes

- **CON-001** — Les états gardés à travers une reconstruction (`app.views`) ne vivent qu'en mémoire dans la session ; aucun fichier de projet ni réglage de l'utilisateur ne change de format. Un projet de la version précédente s'ouvre sans migration. Source : principes 8 et 10 (`docs/architecture/principles.md`), inféré.
- **CON-002** — Une version publiée par type migré, vérifiée indépendamment : les quatre onglets sortent dans la même version. Source : D-18 de la spec #95.
- **CON-003** — Plusieurs sessions modifient le dépôt : jamais `git checkout --`, `stash`, `reset`, `clean` ; `tab_registry.py`, `tab_guard.py`, `tab_host.py`, `woodcore_gui_words.py` et `tests/test_tab_overrides.py` sont partagés avec #107, #112, #113, #114, #115 : édition ciblée, coordination par message. Source : CLAUDE.md.
- **CON-004** — **Ordre** : #106 s'implémente après #115 et #114 (D-02) ; avant de commencer, relire `variables_tab.py` et `commands_tab.py` tels que ces deux issues les laissent, recompter leurs tests, et reprendre les captures de UI-001 à partir de là. Source : ordre d'implémentation prévu.
- **CON-005** — Le temps d'ouverture de la fenêtre est mesuré avant et après (la fenêtre construit tous les onglets à l'ouverture) : « Commandes » lit `lib/` et construit ses enregistrements à la construction, « Variables » lit l'export et le cache des documents ; le type n'ajoute aucune lecture, aucune compilation et aucun fil à la construction. Source : CON-005 de la spec #95.
- **CON-006** — Fichiers en LF, prose sur une ligne, anglais dans le code et les docs ; aucun fichier de `docs/` hors `decisions.md` et `CHANGELOG.md` au-dessus de 100 Ko. Source : CLAUDE.md.
- **CON-007** — Les tests travaillent sur `tests/projet-exemple/` ; aucune écriture dans `../Musterprojekt/`. Source : CLAUDE.md.
- **CON-008** — Plan d'exécution : nouveau type d'onglet, plusieurs modules, une base à trancher : `/big-feature`. Source : CLAUDE.md.

## 7. Décisions prises

- **D-01** — Les cinq types sont ceux de D-05 de la spec #95 ; ce type s'appelle `DataTab` et contient « Variables », « Métrés », « Dépendances » et « Commandes ». Un type est une recette par défaut, il n'enferme pas un onglet. (T1, T3)
- **D-02** — (inférée de l'ordre d'implémentation prévu et de l'état du code) **#106 migre les onglets réécrits par #115 et #114** et vient après eux. Raison : migrer avant, c'est écrire un service « Affichage » que #114 supprime et déplacer 850 lignes que #115 réécrit, sur les mêmes fichiers. Prix : le type « Données » n'existe pas avant ; « Métrés » et « Dépendances » attendent, parce qu'une version porte un type entier (CON-002).
- **D-03** — (inférée de D-13 de la spec #95, « la toile reste un service entier ») **chaque navigateur est un service entier** monté par son onglet, sans le redécouper en liste, filtre, fiche… dans cette issue ; ne deviennent des services à part que les deux morceaux visibles que plusieurs onglets emploient (REQ-009, REQ-010, D-19). Raison : « Variables » et « Commandes » viennent d'être réécrits en bloc ; les recouper ici serait une troisième refonte. Prix : la classe de l'onglet maigrit sans que l'onglet devienne « composé » ; la recherche à étiquettes de #114 et la barre de recherche de #115 ne deviennent pas un service commun (§9).
- **D-04** — (inférée de `VariablesTab.__init__` et de la fenêtre) **un onglet de données n'a ni `dirty`, ni `save`, ni cas, ni brouillon** : REQ-006.
- **D-05** — (relevé) **la phrase de T2 ne décrit pas les quatre onglets** : « le tableau de ce que contient l'export » est « Métrés » ; « Commandes » ne lit pas l'export. Elle n'est pas contredite : D-07 la rapporte à ce que le type contient réellement.
- **D-06** — (ingénieur, 24.10.2026, Q-001 A) **`EXPOSES = {nom: service}`** : l'onglet déclare les noms que d'autres appellent, `DataTab` fabrique les renvois ; la fenêtre, les tests et #114 ne changent pas. Il avait demandé d'abord les inconvénients de l'option B (la fenêtre et les lecteurs passent par le service), puis a choisi A. Mécanisme et limites : ARCH-007.
- **D-07** — (ingénieur, 24.10.2026, Q-002 A) **le service par défaut du type est le bandeau de l'état de l'export** ; chaque onglet apporte son propre navigateur comme service entier (D-03). Pas de tableau générique de l'export, **pas de service « Affichage »** : un onglet de données qui en voudra un l'ajoutera par `SERVICES + (…,)`. `views.DATA_VIEWS` est retiré avec son dernier utilisateur (#114 retire `VIEWS` de « Variables » et laisse la constante avec un commentaire ; #106 retire la constante, ses tests et la ligne du catalogue).
- **D-08** — (revue) **le type n'a que deux zones, « top » et « body », et pas de séparateur** : un navigateur est un service entier (D-03), il monte son propre `QSplitter` (trois volets pour « Variables », deux pour « Dépendances » et « Commandes », aucun pour « Métrés »). La fenêtre lie les tailles par `tab.splitter` et enveloppe son premier volet dans un `FoldablePane` (`woodcore_gui.py:618`) : monter un séparateur de plus autour d'un séparateur fausserait le nombre de volets sous lequel `layout_store` garde les tailles. `DataTab.splitter` rend celui du premier service qui en déclare un, sinon `None`. Cela remplace les trois demandes de la note de passation de #107 (zone haute, séparateur facultatif, centre sans barre) par une seule : la zone haute.
- **D-09** — (revue) **la carte du fichier n'est pas un service mais une classe gardée** (REQ-010) : trois onglets l'emploient et ses boutons sont reliés à ses méthodes ; la garder à sa définition règle les trois, sans second chemin.
- **D-10** — (revue, **à confirmer par l'ingénieur**) **le bandeau est une étiquette d'avertissement commune** (`ctx.say(texte, genre)`, genres « warning » et « danger », propriété `callout`) ; « Dépendances » et « Variables » l'ont déjà ainsi, « Métrés » a une étiquette de style direct (couleur « warning » en gras). Défaut proposé : « Métrés » prend le bandeau `callout` des deux autres, un écart visible d'une ligne, annoncé dans les « Nouveautés » ; à défaut, le service reçoit un paramètre de style pour garder l'ancien aspect.

À reporter dans `docs/decisions.md` §13 à la fin : le type « Données », son ordre après #115 et #114, le service entier par navigateur et sans séparateur de type (D-08), `EXPOSES` (D-06), le bandeau seul par défaut et le retrait de `DATA_VIEWS` (D-07), le garde de la carte du fichier à sa définition (D-09), la base de #107.

## 8. Hors périmètre

- Le contenu des onglets « Variables » (#114) et « Commandes » (#115), l'onglet « Domaines » (#113), les vérifications d'éléments (#112), le contenu de « Dépendances » (#71) : #106 ne change pas ce qu'ils montrent, seulement leur base.
- Les types « Calcul » (écrit), « Dessin », « Éditeur », « Document » (#107), « Bibliothèque » (`LibraryTab`, écrit).
- La lecture et le calcul de `calc/` (registre, graphe, quantités, pages de commandes) et la carte du fichier de « Journal » et de « Positions » (elles gardent `ListFileCard` tel quel ; seule celle de « Métrés » passe par le service).
- La variante D (un onglet = une ligne du `TabSpec`) : D-17 de la spec #95.
- Une nouvelle vue, un nouveau champ ou un nouveau bouton dans un des quatre onglets.

## 9. Idées non retenues comme exigences

- Un service de **barre de recherche / de filtre** commun : « Variables » (barre à étiquettes de #114, qui la veut réutilisable), « Commandes » (champ de recherche, #115), « Dépendances » (filtre) et « Métrés » (portée) cherchent ou filtrent chacun à sa façon. Non demandé ; les trois ne font pas la même recherche.
- Un service **tableau de l'export** générique (colonnes déclarées, une portée, un lecteur de `data/*.json`), que seul « Métrés » emploierait aujourd'hui : écarté par D-07.
- Un service **« Affichage » des données** (`display_view.DisplayView` derrière `display_entries`) : écarté par D-07 (aucun preneur après #114).
- La carte du fichier de « Journal » et de « Positions » passant par le même service quand leurs onglets seront sur le type « Éditeur ».
- Remplacer `isinstance(t, VariablesTab)` de la fenêtre par une capacité déclarée (`CAN_PICK`) : possible avec `EXPOSES` (D-06), non demandé.

## 10. Questions

### Q-001 — Le contrat de « Variables » que d'autres appellent par son nom : où le mettre quand la classe ne définit que des paramètres ?
- **Contexte** : la fenêtre (`begin_variable_pick`), l'onglet « Formule », `linkable_spin` et une dizaine de fichiers de tests appellent sur l'onglet `begin_pick`, `end_pick`, `selected_key`, `selected_keys` (#114), `variable`, `address`, `select_key`. D-07 de la spec #95 interdit à une classe sur un type d'écrire autre chose que ses paramètres et les `HOOKS` du type. Ces fonctions ne sont pas des paramètres : elles vivent donc dans le service du navigateur, et l'on choisit comment l'extérieur les atteint. #114 (REQ-007 et ARCH-004) a promis qu'aucun lecteur de ce contrat ne serait modifié.
- **Pourquoi elle compte** : elle fixe si la fenêtre et les tests changent ou non, si le type a une petite mécanique de plus, et si l'onglet peut être un type « pur ».
- **Options** :
  - **A (recommandée)** — l'onglet **déclare** ces noms (un paramètre, `EXPOSES = {"begin_pick": "browser", …}`) et `DataTab` fabrique à la définition de la classe des méthodes qui renvoient au service nommé : la fenêtre, les tests et #114 n'ont rien à changer, `isinstance(t, VariablesTab)` reste vrai, et `tests/test_tab_overrides.py` voit un paramètre, pas une méthode. Prix : une redirection déclarée dans le type, qui se laisse tester une fois mais cache l'endroit où la fonction est définie.
  - **B** — la fenêtre et les lecteurs passent par le service : `tab.service("browser").begin_pick(...)`. Pas de mécanique, la forme du reste du projet ; mais on modifie `woodcore_gui.py`, `linkable_spin`, l'onglet « Formule » et les tests, c'est-à-dire ce que #114 a juré de ne pas toucher, et #113 (qui lit le même contrat) l'apprend.
  - **C** — `DataTab.HOOKS` énumère ces noms et « Variables » les écrit sur sa classe, comme `PERMITTED` le tolère aujourd'hui pour `confirm_leave`. Prix : « Variables » reste une classe épaisse sur un type « mince », et l'exception rejoint la règle de D-07 qu'on voulait sans exception.
- **Réponse** : A — `EXPOSES = {nom: service}`, `DataTab` fabrique les méthodes de renvoi ; aucun appelant ne change (ingénieur, 24.10.2026 ; il avait d'abord demandé les inconvénients de l'option B, puis choisi A). Reporté en D-06 et ARCH-007.

### Q-002 — Que contient le type « Données » par défaut, puisque « Affichage » n'a plus d'utilisateur après #114 ?
- **Contexte** : l'issue veut pour service par défaut « le tableau de ce que contient l'export, « Affichage » au choix ». Or (§3) ce tableau est celui de « Métrés » seul ; « Variables » est un arbre à trois volets, « Dépendances » deux listes, « Commandes » ne lit pas l'export. Et aucun onglet n'aura plus de vue « Affichage » : #114 la retire de « Variables », « Commandes » n'en a jamais eu. Le service « Affichage » qui existe, `calc_display.DomainDisplay`, est celui du fichier d'un cas et suppose un cas ; l'autre pièce, `display_view.DisplayView`, est un widget que `views.DATA_VIEWS` ne servira plus.
- **Pourquoi elle compte** : elle fixe ce que le type écrit (une bannière et des navigateurs entiers, ou aussi un tableau générique et un « Affichage » sans utilisateur), le travail de cette issue et le code mort ou non qu'elle laisse.
- **Options** :
  - **A (recommandée)** — le type monte par défaut le **bandeau de l'état de l'export** (REQ-009, qu'un onglet retire par `swap` : « Commandes » n'en a pas) et laisse chaque onglet y mettre **son navigateur** comme service entier (D-03) ; pas de tableau générique (un seul utilisateur) ; « Affichage » **n'est pas écrit** : « au choix » veut dire qu'un onglet de données qui en voudra un ajoutera le sien par `SERVICES + (…,)` quand il existera ; `views.DATA_VIEWS` est retiré avec son dernier utilisateur. Prix : on ne livre pas ce que T2 nomme, faute de preneur.
  - **B** — le type monte aussi par défaut un **tableau générique de l'export** (colonnes et lecteur déclarés par l'onglet ; « Métrés » le prend, les trois autres le retirent) et un **service « Affichage » des données** (`DisplayView` derrière `display_entries`), prouvé sur un faux onglet. Prix : deux services écrits pour un seul utilisateur réel et un autre inexistant, du code que rien n'appelle.
  - **C** — comme A, mais le service « Affichage » des données est écrit et testé sur un faux onglet pour tenir « au choix », sans tableau générique. Prix : un service sans appelant, qu'une issue future devra rouvrir pour de vrai.
- **Réponse** : A — le service par défaut est le bandeau de l'état de l'export ; chaque onglet apporte son propre service ; `views.DATA_VIEWS` part avec son dernier utilisateur (ingénieur, 24.10.2026). Reporté en D-07.

## 11. Critères d'acceptation

- [x] REQ-001 — `DataTab` existe ; une classe de paramètres seuls y trouve ses services, ses phases et son contrôle des `NEEDS` (`tests/test_data_tab.py`).
- [x] REQ-002 — « Variables » (de #114) en paramètres seulement ; `tests/test_variables.py` vert, comportement inchangé.
- [x] REQ-003 — « Métrés » en paramètres seulement ; `tests/test_metre_tab.py` vert.
- [x] REQ-004 — « Dépendances » en paramètres seulement ; `tests/test_dependency_tab.py` vert.
- [x] REQ-005 — « Commandes » (de #115) en paramètres seulement ; `tests/test_commands.py` vert.
- [x] REQ-006 — ni `dirty` ni `save` sur le type ; une seule `confirm_leave` ; `PERMITTED` sans `VariablesTab`.
- [x] REQ-007 — `on_shown`, `on_mode`, `view_state` / `restore`, `splitter` répondus par le type ; reconstruction de la fenêtre gardée pour les quatre.
- [x] REQ-008 — le contrat de « Variables » appelable par `EXPOSES`, aucun appelant modifié.
- [x] REQ-009 — service « bandeau de l'état de l'export » commun, trois bandeaux inchangés.
- [x] REQ-010 — `ListFileCard` gardée à sa définition, test négatif en lecture seule pour « Métrés » et « Journal ».
- [x] REQ-011 — `test_tab_overrides.py` couvre `DataTab` ; `HOOKS` vide.
- [x] UI-001 — captures avant et après identiques (prises après #114 et #115) ; `tests/test_i18n.py` vert.
- [x] UI-002 — fichiers de projet et rapports identiques ; seul écart : lecture seule (REQ-010).
- [x] UI-003 — les quatre onglets restent des navigateurs sans marqueur ni question.
- [x] ARCH-001 — `DataTab` sur le cadre de #107 ; deux zones, pas de séparateur de type ; aucune fonction du cadre recopiée ; tests de Calcul et de Document inchangés et verts.
- [x] ARCH-002 — aucun service n'en tient un autre.
- [x] ARCH-003 — lecture et calcul inchangés dans `calc/`.
- [x] ARCH-004 — mots à leur place, trois langues.
- [x] ARCH-005 — registre et garde couvrent le type.
- [x] ARCH-006 — classes, modules et `TabSpec` des quatre onglets inchangés.
- [x] ARCH-007 — `EXPOSES` : méthodes et attributs, noms admis par le test des redéfinitions.
- [x] ARCH-008 — un seul remplissage à la construction, état rendu par `ctx.kept`.
- [x] ARCH-009 — formes de #107, #114, #115 relevées au pas 0.
- [x] `views.DATA_VIEWS` retiré avec ses tests (D-07).
- [x] Documentation : `docs/ui/building-a-tab.md` (le type « Données » passe de « décrit » à « écrit » : son service par défaut, le bandeau (D-07), la phrase « a table of what the export holds » corrigée, `EXPOSES`, un exemple complet avec un navigateur, la ligne du tableau des types et « Where the tabs stand »), `docs/ui/tab-variables.md`, `docs/ui/tab-dependencies.md`, `docs/ui/tab-commands.md` (leur base), `docs/ui/window.md` si la liste des vues y parle de « Variables », `docs/architecture/layout.md` (les nouveaux modules), `docs/decisions.md` §13 et `docs/decisions-index.md`, entrée `CHANGELOG.md`, page « Nouveautés » de la prochaine version en fr / de / en.
- [x] Tests : `tests/test_data_tab.py` (nouveau, sa ligne dans `docs/conventions/testing-catalogue*.md`), `tests/test_tab_overrides.py`, `tests/test_tab_registry.py`, `tests/test_tab_services.py`, `tests/test_variables.py`, `tests/test_metre_tab.py`, `tests/test_dependency_tab.py`, `tests/test_commands.py`, `tests/test_window.py` adaptés ; suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1, D-01, REQ-001 | capturé |
| T2 | REQ-001, REQ-009, ARCH-001, D-05, D-07, D-08 | capturé ; « sur `TabHost` » → cadre de #107 ; « tableau de l'export » et « Affichage au choix » → D-07 (réponse A à Q-002) |
| T3 | REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-010, REQ-011, D-03, D-04, D-06, ARCH-007 | capturé |
| T4 | §11 (documentation, tests), CON-002 | capturé |

### Points de la source non résolus

Aucun : les trois points ouverts du brouillon sont tranchés — « sur `TabHost` » par le cadre de #107 (ARCH-001), « le tableau de l'export, Affichage au choix » par D-07, « en paramètres seulement » pour « Variables » par D-06. Reste à confirmer à l'approbation : D-10 (aspect du bandeau de « Métrés »).

## 13. Revue d'architecture

Revue faite le 24.10.2026 par une lecture du code d'aujourd'hui (`tab_host.py`, `tab_registry.py`, `tab_guard.py`, `library_tab.py`, `variables_tab.py`, `metre_tab.py`, `dependencies_tab.py`, `commands_tab.py`, `list_file_card.py`, `woodcore_gui.py` aux lignes de la fenêtre qui lisent un onglet, `tests/test_tab_overrides.py`, `tests/test_tab_registry.py`) et des plans de #107 (§13 et §14 : le cadre, sa note de passation), #114 et #115. **Le cadre de #107 (`tab_frame.py`), `VariablesBrowser` (#114) et les trois composants de « Commandes » (#115) n'existent pas encore dans le dépôt** : ce qui les concerne est lu dans leurs specs et doit être relu dans le code au pas 0 (ARCH-009).

**Verdict : APPROUVER AVEC RÉSERVES.** Le type tient, mince, à quatre conditions déjà portées dans les REQ et ARCH amendés : le type ne pose ni séparateur ni colonne (D-08) ; `EXPOSES` couvre les attributs autant que les méthodes et reste vérifié par le test des redéfinitions (ARCH-007) ; l'état gardé est rendu au montage, pas après (ARCH-008) ; la garde de lecture seule se pose sur la carte du fichier à sa définition, non sur un service (D-09). Deux points sont **à confirmer par l'ingénieur** : l'aspect du bandeau de « Métrés » (D-10) et le corrigé de REQ-010 (D-09, qui fait aussi refuser « Journal » et « Positions » en lecture seule).

### Modules touchés (ce que chacun possède aujourd'hui)

| Module | Ce qu'il possède | Ce qui change |
|---|---|---|
| `calc/tools/tab_frame.py` (#107) | `Service`, `run_phase`, `service_named`, `missing_needs`, `FrameContext`, `TabFrame` | **rien** (relu au pas 0) ; `provide(nom)` : s'il est sur `DocumentContext` seulement, il passe à `FrameContext` par une édition ciblée (pas 3), les tests de #107 inchangés |
| `calc/tools/data_tab.py` | — | nouveau : `DataContext`, `DataTab`, `Exposed`, `ExportBanner` (le bandeau est un service du type, il vit à côté : un seul fichier, ≈ 150 lignes) |
| `calc/tools/tab_host.py` (722 l.) | `PARAMS` 44 | `"EXPOSES"` ajouté à `PARAMS` (une ligne) |
| `calc/tools/dependencies_tab.py` (237 l.) | `STRINGS`, `DependenciesTab(QWidget)` 64–237 | `STRINGS` et `DependenciesTab` (paramètres) ; `DependenciesBrowser(Service)` reprend le corps (`__init__` → `mount`, `view_state` / `restore` → `state` / `restore`, `on_shown` → `shown`) |
| `calc/tools/metre_tab.py` (229 l.) | `read_export`, `stale_plans`, `MetreTab(QWidget)` 84–229 | idem : `MetreBrowser(Service)` ; `read_export` et `stale_plans` restent des fonctions du module |
| `calc/tools/commands_tab.py` (850 l. aujourd'hui, réécrit par #115) | `CommandsTab(QWidget)` | `CommandsTab` (paramètres) ; un service `CommandsBrowser` qui monte les trois composants de #115 et branche leurs signaux (D-03) |
| `calc/tools/variables_tab.py` (1193 l. aujourd'hui, réécrit par #114) | `VariablesTab(DisplayTab, QWidget)` | `VariablesTab` (paramètres, `EXPOSES`) ; `variables_browser.VariablesBrowser` (#114) devient le service `browser` |
| `calc/tools/list_file_card.py` | `ListFileCard` 59 : `write` 108, `add` 118 | `WRITERS = ("write", "add")` |
| `calc/tools/tab_registry.py` | `GUARDED_TABS` 137, `GUARDED_SERVICES` 143, `guard_actions` 139 | `tab_guard.guard_service(list_file_card.ListFileCard)` ; rien d'autre si #107 a fait suivre `GUARDED_SERVICES` à `TabFrame` |
| `calc/tools/views.py` | `DATA_VIEWS` 34 | retiré (D-07) |
| `tests/` | voir « Tests » | nouveaux : `test_data_tab.py` ; adaptés : cinq fichiers d'onglets, `test_tab_overrides.py`, `test_tab_registry.py`, `test_tab_services.py`, `test_views.py` |

Aucun fichier de `calc/` hors `calc/tools/` n'est touché (ARCH-003). La fenêtre n'est pas modifiée : elle lit `on_shown` (`woodcore_gui.py:647`), `on_mode` (330), `splitter` (606), `view_state` (872), `confirm_leave`, et `variables_tab.VariablesTab` (806) ; le cadre et `EXPOSES` les répondent.

### Code à réutiliser

* `Service`, `run_phase`, `service_named`, `missing_needs`, `FrameContext.provide` (s'il existe) : du cadre ; **aucun second mécanisme**. `ctx.say` trouve le bandeau comme `DocumentContext.provide` trouve un écrivain.
* `chrome.FoldablePane`, `layout_store` : la fenêtre les pose sur `tab.splitter` ; le navigateur n'y touche pas.
* `cards`, `theme.colour`, la propriété `callout` (`dependencies_tab.py:76`, `variables_tab.py:380`) : le bandeau reprend ce que « Dépendances » et « Variables » font déjà ; la danse `unpolish` / `polish` (`variables_tab.py:738`) y est écrite une fois, retirée de « Variables ».
* `tab_guard.guard_service` et le motif de `guard_actions(source_archive.Actions)` pour la carte (`tab_registry.py:139`).
* `graph_model.read` / `newer_sources`, `quantities.summary`, `metre_tab.stale_plans`, `command_docs`, `examples` : appelés par les navigateurs, jamais recopiés dans le service du bandeau.
* À ne **pas** créer : un service « tableau de l'export », un service « Affichage », un service « barre de recherche », un service pour la carte du fichier (§9, D-07, D-09).

### Le type en détail

* **`DataContext(FrameContext)`** : `say(texte, genre=None)` (appelle le service qui offre `"banner"`, `texte` vide efface ; une `KeyError` nomme l'onglet s'il n'y en a pas — « Commandes » n'en monte pas et n'appelle jamais `say`) ; `kept(service)` (l'état gardé, ARCH-008).
* **`DataTab(TabFrame)`** : `CONTEXT = DataContext`, `SERVICES = (ExportBanner,)`, `VIEWS = ()`, `HOOKS = ()`, `EXPOSES = {}`. `frame_body` : une colonne, la zone `top` (le bandeau), la zone `body` (le ou les widgets des services, avec étirement). `splitter` : celui du premier service qui en déclare un (un attribut `splitter` du service). `confirm_leave` : celui du cadre (phase `leave`, puis `True`). Pas de `dirty`, de `save`, de `current_id`, de `source`. `EXPOSES` : `Exposed` fabriqués par `__init_subclass__`.
* **Les quatre onglets** : `SERVICES = (ExportBanner, XBrowser)` pour « Variables », « Dépendances » et « Métrés » ; `SERVICES = (CommandsBrowser,)` pour « Commandes » (la tuple remplace celle du type, comme `swap` / `+` le font pour Calcul). `MODULE = graph_model` pour « Dépendances » (`NEEDS = ("read", "newer_sources", "upstream")`), `quantities` pour « Métrés » ; aucun pour les deux autres.
* **« Métrés »** : la carte du fichier est construite par `MetreBrowser` dans sa page, comme aujourd'hui, mais sa classe est gardée (D-09).

### Risques

Chacun a une sévérité, un lieu et un remède ; §14 dit où chacun est traité.

* **ARCH-RISK-001 — Le séparateur : la fenêtre en lit un, `layout_store` en garde les tailles par nombre de volets (important).** `bind_layout` lit `tab.splitter` (`woodcore_gui.py:606`), enveloppe le premier volet dans une `FoldablePane` (618) et lie `layout_store` sous `(clé, vue, "panes")`. La note de passation de #107 faisait poser par le type « un séparateur facultatif » : autour de navigateurs qui ont chacun le leur, cela donne deux séparateurs imbriqués ou des tailles gardées pour un nombre de volets qui change. *Remède* : D-08, aucun séparateur de type ; `DataTab.splitter` désigne celui du navigateur ; le nombre et l'ordre des volets de chaque onglet sont relevés au pas 0 et comparés à la fin (UI-001).
* **ARCH-RISK-002 — Trois formes à venir et un cadre à venir (important).** Voir ARCH-009. Les cas qui changeraient la spec : #115 livre trois composants sans service (alors `CommandsBrowser` les monte comme D-03 le dit, rien d'autre) ; #114 laisse `VariablesBrowser` sans `mount` (alors le pas 6 en ajoute un, sans réécrire) ; #107 place `provide` ou `hidden` ailleurs que prévu (alors `DataContext.say` s'adapte). *Remède* : pas 0 avec arrêt si un REQ change ; le pas 0 est la porte, rien n'est écrit avant.
* **ARCH-RISK-003 — `EXPOSES` : attributs, `hasattr`, métaclasse Qt (important).** #114 fait rediriger par sa coque l'**attribut** `search` autant que des méthodes ; une méthode fabriquée ne le couvre pas. De plus `__init_subclass__` sur une sous-classe de `QWidget` (métaclasse Shiboken) n'est écrit nulle part dans le dépôt (`grep` : aucune occurrence). *Remède* : ARCH-007 (descripteur, lecture et écriture) ; un essai jetable au pas 0 le prouve avant d'écrire le type ; si la métaclasse l'interdit, le descripteur est posé par un décorateur de classe, la déclaration d'`EXPOSES` ne change pas.
* **ARCH-RISK-004 — Le test des redéfinitions voit des méthodes que personne n'a écrites (important).** `_unauthorised` liste tout nom de `vars(klass)` hors `PARAMS` et `HOOKS` : les `Exposed` fabriqués y paraîtraient. Le test ne doit pas non plus laisser passer une `lambda` sous un nom exposé. *Remède* : ARCH-007, un test à deux faux onglets.
* **ARCH-RISK-005 — La carte du fichier : le service de REQ-010 ne garderait pas les boutons (important).** Les boutons de `ListFileCard` sont reliés à ses propres `write` et `add` (`list_file_card.py:66-70`) ; un service qui les enveloppe garderait ses propres méthodes, pas celles que le bouton appelle. Et `write` / `add` ne peuvent pas entrer dans `tab_guard.WRITERS` : `guard(cls)` pose les noms de cette liste sur **toute** méthode homonyme de n'importe quelle classe d'onglet. De plus la carte sert « Journal » et « Positions » (`journal_tab.py`, `positions_tab.py`), laissés sans garde. *Remède* : D-09, REQ-010 amendé ; `WRITERS` sur la classe, `guard_service` au registre ; `list_files.write` n'est pas touchée (`export_all.py:464` et `sheets.py:354` l'appellent).
* **ARCH-RISK-006 — Un bandeau commun cache trois états et deux aspects (important).** Le bandeau de « Variables » dit des **échecs** (`danger`) avant une péremption (`warning`) (`variables_tab.py:717-739`) ; celui de « Dépendances » a deux textes ; celui de « Métrés » est une étiquette à style direct (`metre_tab.py:93-95`), pas un `callout`. Un service « état de l'export » qui lirait l'export lui-même relirait le graphe une deuxième fois et ne saurait pas dire les échecs. *Remède* : REQ-009 amendé et D-10 : le service n'est que l'étiquette, le navigateur lui dit (`ctx.say`) ce qu'il a lu ; l'écart d'aspect de « Métrés » est annoncé et à confirmer.
* **ARCH-RISK-007 — Remplissage double à la construction (important, CON-005).** Voir ARCH-008 (`commands_tab.py:402-407`, `first_fill`). *Remède* : `ctx.kept`.
* **ARCH-RISK-008 — Réécrire « Dépendances » et « Métrés » en services est un vrai travail, pas un déplacement (important).** Leur `self` est un `QWidget` (`self.fontMetrics()`, parent des boîtes, `QTimer(self)` à venir) et leurs signaux sont reliés à ses méthodes. En passant à un `Service` (classe simple, sans base Qt, comme le dit `Service`), les widgets deviennent des attributs, `fontMetrics()` se lit sur le widget monté, les signaux restent reliés à des méthodes liées d'un objet gardé par `tab.services`. *Remède* : 466 lignes seulement, un pas chacun, tests existants adaptés par l'accès `tab.service("browser")`, aucune assertion de comportement changée ; « Variables » et « Commandes » arrivent déjà en forme de service (ARCH-009).
* **ARCH-RISK-009 — La lecture dans un fil de « Variables » et la compilation de « Commandes » à travers `leave` et `hidden` (important).** `Read` (`QThread`) doit être attendu avant de rendre `True` (`variables_tab.py`, `confirm_leave`) ; la compilation de « Commandes » ne s'arrête aujourd'hui nulle part (aucun `hideEvent`). *Remède* : `leave` du service de « Variables » (attente, test à fil factice) ; pour « Commandes », `hidden` arrête le minuteur seulement si #115 l'a prévu (REQ-005) ; pas de règle nouvelle.
* **ARCH-RISK-010 — Le temps d'ouverture (mineur, CON-005).** Quatre onglets construits à l'ouverture : « Commandes » lit `lib/`, « Variables » le cache. Le type n'ajoute que deux objets légers. *Remède* : mesure avant / après (pas 0, pas 7) ; `tests/test_startup.py`.
* **ARCH-RISK-011 — Plusieurs sessions sur les mêmes fichiers (important, CON-003).** `tab_host.py`, `tab_registry.py`, `tab_guard.py`, `test_tab_overrides.py`, `test_tab_registry.py` ; et #114 / #115 viennent de réécrire `variables_tab.py` et `commands_tab.py`. *Remède* : édition ciblée ; `git status` avant chaque fichier partagé ; les quatre onglets sortent dans une seule version (CON-002), pas committés à mi-chemin sans suite verte.
* **ARCH-RISK-012 — Code et docs qui restent (mineur).** `views.DATA_VIEWS` et ses tests ; les `PERMITTED` de `VariablesTab` ; les redirections d'une ligne de la coque de #114 (remplacées par `EXPOSES`) ; la phrase « a table of what the export holds » de `building-a-tab.md` et la ligne « Données » de son tableau. *Remède* : pas 7 et pas 8, par `grep` avant chaque retrait.
* **ARCH-RISK-013 — `IN_VIEWS` et `on_mode` (mineur).** `Service.IN_VIEWS = ("calc",)` par défaut ; un type sans vues ne doit pas cacher ses services pour cela. `on_mode` appartient désormais aux quatre onglets (un tour de `busy.pump()` de plus par changement de document, déjà noté par #107, ARCH-RISK-008). *Remède* : `frame_body` de `DataTab` ignore `IN_VIEWS` ; une mesure d'un changement de document avant / après.

### Approche recommandée

`DataTab` est le cadre de #107 plus une zone haute et `EXPOSES` : environ 150 lignes. Chaque onglet est une classe de paramètres ; chaque navigateur est un service entier qui monte son séparateur, garde son état par `state()` / `restore()` et dit son bandeau par `ctx.say`. On commence par « Dépendances » (le plus petit, sans contrat), puis « Métrés » (la garde de la carte), « Commandes » (les trois composants), et enfin « Variables » (le contrat, le fil), pour que chaque pas prouve un morceau du type sur un vrai onglet.

### Tests à ajouter ou étendre

* **Nouveau** : `tests/test_data_tab.py` (faux services : ordre des phases ; `NEEDS` nommant onglet, service et fonction ; `dirty`, `save`, `current_id`, `source` absents ; `confirm_leave` attend un faux service à fil puis rend `True` ; `say` à zéro, un bandeau, genres et effacement ; `EXPOSES` méthode, attribut, écriture, erreurs ; `splitter` ; `kept` ; un seul remplissage ; un faux écrivain de service entre dans `GUARDED_SERVICES`).
* **Étendus** : `test_tab_overrides.py` (`_types()` ajoute `DataTab`, `_unauthorised` admet les `Exposed`, entrée `("VariablesTab", "confirm_leave")` retirée de `PERMITTED`) ; `test_tab_registry.py` (la carte gardée, noms de l'interface, reconstruction par onglet) ; `test_tab_services.py` (modules de services des quatre onglets) ; `test_variables.py`, `test_metre_tab.py` (+ écriture refusée en lecture seule), `test_dependency_tab.py`, `test_commands.py`, `test_journal_tab.py` / `test_positions_tab.py` (carte refusée en lecture seule) ; `test_window.py`, `test_modes_window.py`, `test_richtext.py`, `test_i18n.py`, `test_startup.py` sans assertion modifiée ; `test_views.py` (la constante en moins).

### Exigences nées de la revue

ARCH-007 à ARCH-009 (§5), D-08 à D-10 (§7) ; REQ-001, REQ-009 et REQ-010 amendés à l'endroit où ils sont écrits.

## 14. Plan d'implémentation

Onze pas (0 à 10), dans cet ordre ; chacun laisse la suite des fichiers concernés verte avant le suivant. **Rien n'est écrit avant que le pas 0 ne soit passé.** Les quatre onglets sortent dans une seule version (CON-002). Aucun pas ne touche `calc/` hors `calc/tools/`.

| Pas | Quoi | Fichiers | REQ / ARCH | Preuve |
|---|---|---|---|---|
| **0** | **Porte et relevés.** Vérifier que #107 est livrée (`tab_frame.py`, `document_tab.py`, `test_tab_frame.py` verts), que #114 l'est (`variables_browser.py`, forme de service, `selected_keys`) et #115 aussi (trois composants) ; relire ces fichiers, recompter les tests de `test_variables.py` et `test_commands.py`, relever pour chaque onglet le nombre et l'ordre de ses volets, les clés de `layout_store`, le temps d'ouverture de la fenêtre et d'un changement de document, des captures fr des quatre onglets ; essai jetable (hors dépôt) d'un descripteur posé par `__init_subclass__` sur une sous-classe de `QWidget` ; dire si `provide` est sur `FrameContext`. Un écart qui change un REQ : s'arrêter, le dire à l'ingénieur | aucun fichier du dépôt (relevés joints à §15) | CON-004, ARCH-009, ARCH-RISK-001, 002, 003, 010 | les relevés existent ; l'essai passe ; `python tests/run_tests.py --related calc/tools/tab_host.py` vert |
| **1** | **La carte du fichier gardée** (indépendante du type, committée avec le pas 2 ou seule) : `ListFileCard.WRITERS`, `tab_guard.guard_service(ListFileCard)` au registre, test négatif en lecture seule pour « Métrés » et « Journal » | `calc/tools/list_file_card.py`, `calc/tools/tab_registry.py`, `tests/test_metre_tab.py`, `tests/test_journal_tab.py`, `tests/test_tab_registry.py` | REQ-010, ARCH-005, D-09, ARCH-RISK-005 | `test_every_writer_a_tab_reaches…` étendu ; l'écriture en projet normal inchangée (tests des trois onglets) |
| **2** | **Le type.** `DataContext` (`say`, `kept`, et `provide` si #107 l'a laissé sur `DocumentContext` : édition ciblée, tests de #107 inchangés), `DataTab`, `Exposed`, `ExportBanner` ; `"EXPOSES"` dans `tab_host.PARAMS` ; `_types()` et `_unauthorised` du test des redéfinitions | `calc/tools/data_tab.py` (nouveau), `calc/tools/tab_host.py` (une ligne), `tests/test_data_tab.py` (nouveau), `tests/test_tab_overrides.py` | REQ-001, 006, 007, 009, 011, ARCH-001, 002, 005, 007, 008, ARCH-RISK-003, 004, 013 | `tests/test_data_tab.py` sur faux services ; `test_tab_overrides` ; les tests de Calcul et de Document inchangés ; `test_no_duplicates` |
| **3** | **« Dépendances »** : `DependenciesBrowser(Service)` (`NEEDS` de `graph_model`, bandeau par `ctx.say`), `DependenciesTab(DataTab)` en paramètres ; l'état (séparateur, filtre, nœud) par `state()` / `restore()` | `calc/tools/dependencies_tab.py`, `tests/test_dependency_tab.py`, `tests/test_tab_services.py` | REQ-004, 009, UI-001, ARCH-006, ARCH-RISK-008 | les 3 tests, accès par `tab.service("browser")`, aucune assertion changée ; nombre de volets comme au pas 0 |
| **4** | **« Métrés »** : `MetreBrowser(Service)`, `MetreTab(DataTab)` ; la carte du fichier construite dans la page ; le bandeau selon la réponse à D-10 | `calc/tools/metre_tab.py`, `tests/test_metre_tab.py` | REQ-003, 009, 010, D-10 | les 2 tests ; la carte refusée en lecture seule (pas 1) |
| **5** | **« Commandes »** : `CommandsBrowser(Service)` qui monte les trois composants de #115, branche leurs signaux, lit son état par `ctx.kept` ; `CommandsTab(DataTab)` en paramètres sans bandeau ; `hidden` arrête la compilation si #115 l'a prévu | `calc/tools/commands_tab.py`, `tests/test_commands.py`, `tests/test_richtext.py` (recherche de l'onglet, lecture seule) | REQ-005, 007, ARCH-008, ARCH-RISK-007, 009 | les tests de #115, accès par le service ; `type(t).__name__ == "CommandsTab"` ; un seul remplissage à la construction |
| **6** | **« Variables »** : `VariablesBrowser` (#114) devient le service `browser` (ajout de `mount` / `state` / `restore` / `shown` / `mode_changed` / `leave` si #114 les a nommés autrement), `VariablesTab(DataTab)` avec `EXPOSES`, les redirections d'une ligne de #114 retirées ; l'entrée `("VariablesTab", "confirm_leave")` retirée de `PERMITTED` | `calc/tools/variables_tab.py`, `calc/tools/variables_browser.py`, `tests/test_variables.py`, `tests/test_tab_overrides.py` | REQ-002, 006, 007, 008, ARCH-006, 007, ARCH-RISK-003, 009 | `test_variables`, `test_linkable_spin`, `test_formula_tab`, `test_editor_buttons`, `test_text_tool` **sans appel modifié** ; `isinstance(t, VariablesTab)` ; `leave` attend un fil factice |
| **7** | **Passages de fenêtre** : reconstruction (séparateur, recherche, filtre, choix, un test par onglet), changement de document, absence de marqueur (`test_window`), palette, mots, démarrage ; `views.DATA_VIEWS` retiré par `grep` d'abord, avec ses tests | `tests/test_tab_registry.py`, `tests/test_window.py`, `tests/test_modes_window.py`, `tests/test_views.py`, `tests/test_i18n.py`, `tests/test_startup.py` (lecture), `calc/tools/views.py` | REQ-007, UI-001, 003, D-07, CON-005, ARCH-RISK-001, 010, 012, 013 | ces tests ; captures et mesures du pas 0 refaites et jointes |
| **8** | **Documentation** : `docs/ui/building-a-tab.md` (le type « Données » de « décrit » à « écrit », la phrase du tableau corrigée, `EXPOSES`, le bandeau, un exemple complet avec un navigateur, « Where the tabs stand »), `docs/ui/tab-variables.md`, `docs/ui/tab-dependencies.md`, `docs/ui/tab-commands.md`, `docs/ui/tab-positions.md` (« Métrés » et la garde de la carte), `docs/ui/window.md` si les vues y parlent de « Variables », `docs/architecture/layout.md` (`data_tab.py`), `docs/decisions.md` §13 et `docs/decisions-index.md` (D-06 à D-10), `docs/open-questions.md` (`LibraryTab` sur le cadre ; un service « Affichage » de données quand un onglet en voudra), `CHANGELOG.md`, la page « Nouveautés » de la version en fr / de / en (une ligne : les quatre onglets reposent sur le nouveau type ; deux écarts visibles : les boutons de la carte du fichier refusés en lecture seule, et l'aspect du bandeau de « Métrés » si D-10 le confirme), lignes du catalogue (`test_data_tab.py` dans `testing-catalogue-window.md`, lignes des fichiers adaptés) | les fichiers cités | CON-002, CON-006, ARCH-004, §11 « Documentation » | `tests/test_docs_coherence.py` ; `tests/test_i18n.py` |
| **9** | Suite complète en arrière-plan, `git diff --stat` joint (ARCH-003), vérification indépendante (`verify-requirements`) | — | tous | suite verte ; §15 |
| **10** | `finish` : un commit, la question « Pousser ? » ; la publication (installateur, site) attend la parole de l'ingénieur | — | CON-002 | commit |

**Les risques de la revue, un à un.** 001 → pas 0 (relevé), 2 (aucun séparateur de type), 7 (comparaison). 002 → pas 0. 003 → pas 0 (essai), 2 (descripteur), 6. 004 → pas 2 et 6. 005 → pas 1, **REQ-010 amendé** (non appliqué comme spécifié : pas de service, D-09). 006 → pas 2, 3, 4, 6 (REQ-009 amendé ; D-10 à confirmer). 007 → pas 2 et 5. 008 → pas 3 et 4. 009 → pas 5 et 6. 010 → pas 0 et 7. 011 → tous (édition ciblée, un seul commit au pas 10). 012 → pas 7 et 8. 013 → pas 2 et 7. Aucun risque n'est laissé sans pas.

**Ce que l'ingénieur doit encore trancher** : D-10 (le bandeau de « Métrés » prend l'aspect `callout` des deux autres, recommandé, ou garde l'ancien par un paramètre de style) ; et il confirme D-09 : « Journal » et « Positions » refusent aussi leurs boutons de fichier en lecture seule (le corrigé de REQ-010 ne se limite pas à « Métrés »).

## 15. Vérification

Vérification indépendante (agent `requirements-verifier`, 25.10.2026) sur le diff depuis `7b41c3e6` (commit `80391070` et l'arbre de travail), les tests et les docs ; il n'a pas lancé la suite complète.

**Relevé du pas 0** (ARCH-009) : #107, #114 et #115 livrées sous la forme de §13 ; `provide` était sur `DocumentContext` seul (déplacé à `FrameContext`) ; le cadre appelle `restore({})` de chaque service même sans état ; « Commandes » lisait son état dans `__init__` (ARCH-008 confirmé) ; volets : Variables 3, Dépendances 2, Commandes 3, Métré aucun séparateur ; `VIEWS` vide pour les quatre ; ouverture 5,57–6,27 s, changement de document 0,10–0,11 s ; le descripteur posé par `__init_subclass__` sur une sous-classe de `QWidget` marche. Aucun écart ne changeait un REQ.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `data_tab.py` ; `test_data_tab` (services, phases, `NEEDS` nommé) |
| REQ-002 | ✅ | `VariablesTab` = `KEY`, `SERVICES`, `EXPOSES` ; `test_variables` vert |
| REQ-003 | ✅ | `MetreBrowser`, `MetreTab` ; `test_metre_tab` (4) |
| REQ-004 | ✅ | `DependenciesBrowser`, `DependenciesTab` ; `test_dependency_tab` (filtre et nœud gardés après correction) |
| REQ-005 | ✅ | `CommandsBrowser`, `CommandsTab` ; `test_commands`, `test_richtext` |
| REQ-006 | ✅ (après correction) | `test_data_tab`, `test_tab_overrides` (`PERMITTED` sans `VariablesTab`), `test_variables` (`leave` attend un fil factice), `test_window.test_the_tabs_of_data_are_browsers_and_never_marked` ajouté sur la remarque du vérificateur |
| REQ-007 | ✅ (réserve) | `test_tab_registry` (`FRAME_API`), `test_modes_window`, reconstruction par onglet : Variables, Commandes, Métré, Dépendances (filtre ajouté). Les tailles du séparateur à travers une reconstruction ne sont prouvées que sur un faux onglet (`test_data_tab`) : hors écran, un séparateur jamais disposé n'a pas de tailles à garder |
| REQ-008 | ✅ | `EXPOSES` (12 noms) ; aucun appel du contrat modifié dans les tests d'autres onglets |
| REQ-009 | ✅ | `ExportBanner` ; `test_data_tab` ; trois bandeaux identiques en texte, genre, visibilité (captures, mesures) |
| REQ-010 | ✅ | `ListFileCard.WRITERS`, `guard_service` ; test négatif « Métré » et « Journal » |
| REQ-011 | ✅ | `test_tab_overrides.test_a_data_tab_writes_only_its_parameters` |
| UI-001 | ✅ | captures avant / après des quatre onglets identiques au pixel ; écarts voulus : bandeau `callout` de « Métré » (D-10), bandeau de « Variables » au-dessus de sa barre |
| UI-002 | ✅ | aucun fichier de `calc/` hors `calc/tools/`, rien dans `lib/` |
| UI-003 | ✅ (après correction) | voir REQ-006 |
| ARCH-001 à 009 | ✅ | ARCH-002 prouvé sur les onglets réels après correction (`test_tab_services`) |

Corrigé après la vérification : `docs/ui/window.md` (vue « Données » des variables), `docs/architecture/layout.md` (lignes de `variables_tab.py`, `variables_browser.py`, `dependencies_tab.py`, `commands_tab.py`), `docs/ui/tab-positions.md` et `tab-journal.md` (la carte refusée en lecture seule), tests ARCH-002, UI-003 et reconstruction de « Dépendances ». Note : `test_metre_tab` a échoué une fois chez le vérificateur sur un `PermissionError` de OneDrive (`quantities.json.part` → `quantities.json`), vert au second passage — indépendant de cette issue.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #106 (4 points) et du code des quatre onglets, de `TabHost`, de `LibraryTab` et des specs #107, #114, #115 ; deux questions ouvertes (contrat de « Variables », contenu par défaut du type) ; dépend de Q-001 de #107 et de l'ordre #115, #114, #106 |
| 2026-10-24 | specified | réponses de l'ingénieur reportées : Q-001 A (`EXPOSES`, D-06), Q-002 A (bandeau par défaut, `DATA_VIEWS` retiré, D-07) ; plus de question ouverte |
| 2026-10-24 | reviewed | revue d'architecture (§13) : APPROUVER AVEC RÉSERVES ; REQ-001, 009, 010 amendés, ARCH-007 à 009 et D-08 à D-10 nés de la revue ; plan en 11 pas (§14), porte au pas 0 (ARCH-009) ; à confirmer : D-09 et D-10 |
| 2026-10-24 | approved | approbation unique des huit specs du 24.10.2026 par l'ingénieur (AskUserQuestion) : plan approuvé tel quel ; toutes les propositions « à confirmer » des revues acceptées comme recommandées ; ordre d'implémentation #108 → #115 → #114 → #113 → #112 → #109 → #107 → #106, un agent par issue ; commits et push autorisés au fil du travail ; écarts et questions notés en §16 et posés à la fin |
| 2026-10-25 | implementation | pas 0 : #107 (`tab_frame.py`, `document_tab.py`), #114 (`variables_browser.VariablesBrowser`, forme de service, `selected_keys`, coque à renvois) et #115 (`command_list`, `command_page_view`, `command_side`, chacun `state`/`restore`/`shown`/`hidden`) livrées ; `provide` sur `DocumentContext` seul (passé à `FrameContext`, pas 2) ; le cadre appelle `restore({})` de chaque service même sans état gardé ; « Commandes » n'a pas de `restore` et lit son état dans `__init__` (ARCH-008 confirmé) ; volets : Variables 3, Dépendances 2, Commandes 3, Métré aucun séparateur ; aucune vue (`VIEWS` vide) pour les quatre ; ouverture de la fenêtre 5,57 s, changement de document 0,11 s ; captures fr « avant » (`scratchpad/screens/106-before-*`) ; essai d'un descripteur posé par `__init_subclass__` sur une sous-classe de `QWidget` : passe. Aucun écart qui change un REQ |
| 2026-10-25 | implementation | pas 1 : `ListFileCard.WRITERS = ("write", "add")`, `tab_guard.guard_service(ListFileCard)` au registre ; test négatif en lecture seule (« Métré », « Journal ») dans `tests/test_metre_tab.py`, garde vérifiée dans `tests/test_tab_registry.py` — REQ-010 |
| 2026-10-25 | implementation | pas 2 : `calc/tools/data_tab.py` (`DataContext` : `say`, `kept` ; `ExportBanner` ; `Exposed` ; `DataTab`) ; `provide` déplacé de `DocumentContext` à `FrameContext` ; `"EXPOSES"` dans `tab_host.PARAMS` ; `tests/test_data_tab.py` ; `test_tab_overrides` (`_types`, `_unauthorised`, test du type) — REQ-001, 006, 007, 009, 011, ARCH-001, 002, 005, 007, 008 |
| 2026-10-25 | implementation | pas 3 : « Dépendances » : `DependenciesBrowser(Service)`, `DependenciesTab(DataTab)` en paramètres ; `tests/test_dependency_tab.py` adapté (accès par `tab.service(...)`) — REQ-004 |
| 2026-10-25 | implementation | pas 4 : « Métré » : `MetreBrowser(Service)`, `MetreTab(DataTab)` (`MODULE = quantities`) ; bandeau `callout` (D-10) ; test de reconstruction (portée gardée) — REQ-003, 009, 010 |
| 2026-10-25 | implementation | pas 5 : « Commandes » : `CommandsBrowser(Service)` monte les trois composants de #115 avec `ctx.kept`, `restore` sans effet, phases `revealed` / `hidden` passées aux volets ; `CommandsTab(DataTab)` sans bandeau, `EXPOSES = {"search": "browser"}` ; test : une reconstruction remplit l'arbre une fois — REQ-005, ARCH-008 |
| 2026-10-25 | implementation | pas 6 : « Variables » : `VariablesBrowser` devient un `Service` nommé `browser` (monté sur le contexte, `say` au bandeau du type ; monté seul il ne dit rien), `VariablesTab(DataTab)` avec `EXPOSES` (12 noms) ; la coque à renvois retirée ; `("VariablesTab", "confirm_leave")` retiré de `PERMITTED` ; tests adaptés (`tab.service("browser")`), test de `leave` sur un fil factice — REQ-002, 006, 008 |
| 2026-10-25 | testing | pas 7 : `views.DATA_VIEWS`, la vue « data » et `view_data` / `view_data_tip` retirés ; `test_tab_registry` (noms de l'interface, aucun nom d'éditeur, aucun onglet gardé) ; captures « après » identiques au pixel près aux « avant » pour les quatre onglets (bandeaux cachés) ; bandeaux dans les trois états identiques en texte, genre et visibilité, sauf l'aspect `callout` de « Métré » ; ouverture 5,95 s (5,57–6,27 s avant), changement de document 0,12 s (0,10–0,11 s avant) — REQ-007, UI-001, D-07 |
| 2026-10-25 | verification | pas 8 : documentation (`building-a-tab.md`, `tab-variables.md`, `tab-dependencies.md`, `tab-commands.md`, `layout.md`, décisions §13 et index, open-questions, CHANGELOG, « Nouveautés » 0.125 fr/de/en, catalogue des tests) |
| 2026-10-25 | completed | pas 9 : suite complète 3416 passés, 8 sautés (1025 s) ; vérification indépendante (§15) : réserves levées — `window.md`, `layout.md`, `tab-positions.md`, `tab-journal.md` corrigés, tests ARCH-002 (`test_tab_services`), UI-003 (`test_window`) et reconstruction de « Dépendances » (filtre) ajoutés ; spec déplacée dans `docs/requirements/completed/` |
