---
id: 2026-10-24-type-document
titre: Le type « Document » — DocumentTab, « Projet » et « Structure du document » construits dessus
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-25
source: issue GitHub #107 (suite de l'issue #95)
docs: [docs/ui/building-a-tab.md, docs/ui/tab-project.md, docs/ui/tab-structure.md, docs/ui/window.md, docs/architecture/layout.md, docs/architecture/principles.md, docs/decisions.md]
---

# Le type « Document » — Spécification

## 1. Objectif

Écrire le quatrième type d'onglet de la décision D-05 de la spec `2026-10-23-onglets-types-et-services` : `DocumentTab`, une base mince qui monte des services, et y faire passer les deux onglets du groupe « Document » de la navigation, « Projet » (`project_tab.ProjectTab`) et « Structure du document » (`structure_tab.StructureTab`), chacun réduit à ses paramètres. Les deux `confirm_leave` propres que `tests/test_tab_overrides.py` tolère aujourd'hui (`PERMITTED`) deviennent le comportement du type ou disparaissent. Rien ne change pour l'ingénieur : même fenêtre, mêmes mots, mêmes fichiers.

## 2. Source

L'issue #107, mot pour mot, par points.

> **T1** — « Suite de l'issue #95. Le type « Document » est décrit dans `docs/ui/building-a-tab.md`, pas encore écrit (décision D-05 de la spec `docs/requirements/completed/2026-10-23-onglets-types-et-services.md`). »
>
> **T2** — « Une base mince `DocumentTab` sur `TabHost`, ses services par défaut : le formulaire du fichier du projet ou du document. »
>
> **T3** — « Migrer Projet et Structure du document, chacun en paramètres seulement ; leurs `confirm_leave` propres (`tests/test_tab_overrides.py`) deviennent des crochets du type ou disparaissent. »
>
> **T4** — « Tests, guide, décision, CHANGELOG, « Nouveautés ». »

## 3. Exigences fonctionnelles

**État actuel relevé dans le code** (master `be5b85f`). `ProjectTab(QWidget)` (598 lignes) et `StructureTab(StructureTabShareMixin, StructureTabWriteMixin, StructureTabViewMixin, QWidget)` (577 lignes, plus trois mixins de 479, 461 et 559 lignes) ne descendent ni de `TabHost` ni de `SourceEditorTab`. Le guide (`docs/ui/building-a-tab.md`) décrit le type ainsi : « Projet, Structure — le formulaire du fichier du projet ou du document ». Or seul « Projet » est un formulaire (la page de titre, la version épinglée, la langue, le formulaire de mise en page, les trois documents ; vue « Informations » et vue « Templates » avec aperçu compilé hors du fil de la fenêtre). « Structure du document » est un arbre (chapitres › sections › objets), un aperçu Typst de ce qui est choisi, des options par genre d'objet, un guetteur de fichiers, l'état de synchronisation entre documents : il écrit à chaque geste, sans brouillon (`StructureTab` n'a pas de `dirty`).

Ce que chacun définit aujourd'hui hors de ses paramètres :

| | « Projet » | « Structure du document » |
|---|---|---|
| construction | `__init__` (deux pages dans un `QStackedWidget`), `_details_page`, `_templates_page` | `__init__`, `build_tree_panel`, `build_pane_panel`, `build_options_panel` |
| avec le document | `on_mode` (relit si rien n'est non enregistré) | `on_mode` (relit l'arbre, remet la page) |
| à l'affichage | `on_shown`, `showEvent` (aperçu des templates) | `on_shown`, `showEvent`, `hideEvent` (guetteur de fichiers) |
| brouillon | `dirty`, `mark_dirty`, `load`, `discard`, `save` | aucun : `confirm_leave` vide `host.flush()` et rend `True` |
| quitter | `confirm_leave` → `autosave.confirm(…, discard=self.discard)` | `confirm_leave` (PERMITTED), `flush_pending` |
| reconstruction de la fenêtre | `view_state`, `restore` | `view_state`, `restore` |
| lecture seule | `lock` ; écrivains `write_apply_form`, `write_create_document` (liste par nom de `tab_guard`) | `writable`, `set_button` ; ses écritures passent par les modules de `calc/` et le mixin d'écriture |
| vues | `VIEWS = ("details", "templates")`, `set_view` | aucune |

### REQ-001 — `DocumentTab`, base mince et services par défaut
- **Exigence** : Woodcore doit offrir `DocumentTab` (`calc/tools/document_tab.py`), une classe mince sur le cadre `TabFrame` (D-04, ARCH-001) qui nomme ses `SERVICES`, ses `VIEWS` et ses `HOOKS`, monte des `tab_host.Service` en pages, garde un contexte `DocumentContext` (le brouillon, la lecture seule, les phases) et répond une fois à ce que la fenêtre appelle (REQ-004, REQ-005). **Amendé par la revue (D-07, à confirmer)** : le type ne nomme aucun service par défaut (`SERVICES = ()`), faute d'une fonction commune à « Projet » et « Structure » ; T2 (« ses services par défaut : le formulaire du fichier ») est tenu par le contexte et le type, et par « Projet » dont le service « Informations » est ce formulaire.
- **Source** : T2, T1
- **Priorité** : doit
- **Critère d'acceptation** : `calc/tools/document_tab.py` existe ; un `DocumentTab` monté, par une classe qui ne contient que des paramètres, sur deux faux services (l'un à brouillon, l'autre à écriture immédiate) y trouve chacun par `tab.service(nom)` ; `tests/test_document_tab.py` (nouveau, une ligne au catalogue des tests).

### REQ-002 — « Projet » en paramètres seulement
- **Exigence** : `ProjectTab` doit être une classe de paramètres sur `DocumentTab` ; ses deux vues deviennent des services (« Informations » : `ProjectDetails`, « Templates » : `ProjectTemplates`, chacun avec son propre état) et ses deux actes (« Appliquer au projet… », « Créer le document… »), que les deux pages déclenchent, un troisième service sans volet, `ProjectActions` (ARCH-006 de la revue) ; la page de titre, la langue, la version épinglée, le formulaire de mise en page, la création d'un document, l'aperçu des templates compilé hors du fil de la fenêtre et « Ouvrir le dossier » se comportent exactement comme aujourd'hui.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : les 10 tests de `tests/test_project_tab.py` passent, leur accès aux widgets adapté à `tab.service(…)` sans qu'une assertion de comportement change ; `ProjectTab` ne définit aucun nom hors `tab_host.PARAMS` et `DocumentTab.HOOKS`.

### REQ-003 — « Structure du document » en paramètres seulement
- **Exigence** : `StructureTab` doit être une classe de paramètres sur `DocumentTab`, son arbre, son aperçu, ses options, son guetteur de fichiers, sa synchronisation et ses écritures (`calc/structure.py`, `calc/typst_objects.py`, `calc/doc_import.py`, `calc/sync.py`, `calc/sharing.py`) servis par **un seul service entier**, `DocumentStructure` (D-05), qui monte le widget `StructureView` (ancienne classe de l'onglet, ses trois mixins gardés : ARCH-006), sans changer une ligne de ce que ces modules de `calc/` font.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : les 71 tests de `tests/test_structure_tab.py` passent, adaptés à l'accès par le service (un assistant de test rend `tab.service("structure").view`) et les appels non liés `StructureTab.ask_import(tab)`, `ask_template`, `ask_choice` (`tests/test_structure_tab.py:1252, 1520, 1860`) devenus `StructureView.ask_import(view)`…, sans qu'une assertion de comportement change ; `StructureTab` ne définit que des paramètres.

### REQ-004 — `confirm_leave` : un comportement du type, plus de redéfinition
- **Exigence** : `DocumentTab` doit répondre une fois à `confirm_leave` pour tout onglet du type, d'après ce que ses services déclarent : un service qui garde un brouillon (« Projet ») le dit au contexte (`ctx.touch()` : **le drapeau `dirty` est celui du contexte**, un par onglet, comme `TabContext`, et non un par service — amendé par la revue, ARCH-RISK-006) et sait l'abandonner (phase `discard`), et la question d'`autosave.confirm` est posée avec les mots `UNSAVED_WORDS` de l'onglet (« Projet » : `("tab_project", "pj_title_card")`, ceux d'aujourd'hui) ; un service qui écrit à chaque geste (« Structure ») dit seulement ce qu'il a en attente (phases `leave` et `flush`), qui est écrit avant de répondre `True`. Aucune des deux classes ne redéfinit `confirm_leave`.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : dans `tests/test_tab_overrides.py`, les entrées `("StructureTab", "confirm_leave")` et `("ProjectTab", "confirm_leave")` de `PERMITTED` sont retirées (le test des entrées périmées l'exige) ; un test de `tests/test_document_tab.py` vérifie les deux comportements sur un faux service à brouillon et un faux service à écriture immédiate : le premier pose la question quand il est modifié et la saute sinon, le second écrit son attente et ne demande rien.

### REQ-005 — Ce que la fenêtre appelle sur ces deux onglets
- **Exigence** : la fenêtre appelle sur un onglet `on_mode(mode)` (changement de document, `woodcore_gui.py:330`), `on_shown`, `set_view`, `view_state` et `restore` (reconstruction), `flush_pending`, `confirm_leave`, `dirty`, `save`. `DocumentTab` doit répondre à chacun une fois, en les faisant suivre aux services par des phases dans l'ordre de `SERVICES` (celles du cadre : `shown`, `mode_changed`, `revealed`, `hidden`, `flush`, `leave` ; celles du type : `loaded`, `lock`, `discard`, `view_set`), de sorte que ni « Projet » ni « Structure » n'ait à les définir ; `TAB_API` se coupe en `FRAME_API` (ce que tout onglet sur le cadre répond) et la suite de `TabHost`, et le test de `TAB_API` couvre les deux.
- **Source** : T3 ; inféré de ARCH-009 de la spec #95
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_tab_registry.py` étendu : chaque nom de `TAB_API` du type existe sur `DocumentTab` ; changer de document dans la fenêtre relit « Projet » et « Structure » comme aujourd'hui (`tests/test_project_tab.py`, `tests/test_structure_tab.py:280–301`) ; `MODE_BOUND` reste `("tab_structure", "tab_journal")` (`tests/test_tab_registry.py:32`).

### REQ-006 — Lecture seule : les écrivains gardés là où ils sont définis
- **Exigence** : les écritures des deux onglets passent par des services qui déclarent leurs `WRITERS` (`tab_guard.guard_service`), comme ceux du type Calcul ; `write_apply_form` et `write_create_document` quittent la liste globale par nom de `tab_guard` quand ils sont gardés par leur service ; dans un projet ouvert en lecture seule, chaque champ, bouton et écriture reste refusé comme aujourd'hui.
- **Source** : T3 ; inféré de ARCH-004 de la spec #95
- **Priorité** : doit
- **Critère d'acceptation** : un test négatif monte un service écrivain de chaque onglet sur une fenêtre factice en lecture seule : l'écriture renvoie `False` et n'écrit rien ; `test_every_writer_a_tab_reaches_is_guarded_where_it_is_defined_and_once` couvre les nouveaux services.

### REQ-007 — Survivre à la reconstruction de la fenêtre
- **Exigence** : ce que chaque onglet garde à travers une reconstruction (« Projet » : la page de titre tapée et non enregistrée, la version, le document regardé, les tailles ; « Structure » : les tailles, l'état de l'arbre, une compilation en attente, les liens grisés des partages arrêtés) doit passer par `state()` / `restore(state)` des services et le `view_state` du type, sous les clés d'aujourd'hui où le format est relu.
- **Source** : T3 ; inféré de `TAB_API`
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_structure_tab.py:1640, 2342` et le test équivalent de « Projet » (reconstruction avec brouillon) passent ; `test_every_tab_class_keeps_its_view_through_a_rebuild` couvre les deux onglets.

### REQ-008 — Un test refuse toute redéfinition dans un onglet du type
- **Exigence** : Woodcore doit refuser par un test qu'une classe d'onglet sur `DocumentTab` définisse autre chose que ses paramètres et les `HOOKS` du type ; `HOOKS` de `DocumentTab` est vide au départ.
- **Source** : T3 ; D-07 de la spec #95
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_tab_overrides.py` : `_types()` rend `(CalcTab, DocumentTab)` ; `_unauthorised` échoue sur un onglet de test qui redéfinit `confirm_leave` ou assigne une `lambda` ; `ProjectTab` et `StructureTab` passent ; `_tab_classes` s'arrête au type.

### REQ-009 — Un service se refuse sur un document qui ne lui donne pas ce qu'il demande
- **Exigence** : les `NEEDS` d'un service du type (le module d'écriture qu'il appelle, le dossier du document) sont vérifiés à la construction de l'onglet, avec le message de `missing_needs` qui nomme l'onglet, le service et la fonction.
- **Source** : REQ-006 de la spec #95 (règle « un fichier malformé arrête »), inféré
- **Priorité** : devrait
- **Critère d'acceptation** : un test monte un service du type sur un module sans la fonction demandée et reçoit l'erreur nommée.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Aucun changement visible
- **Exigence** : la fenêtre, la navigation (groupe « Document », Ctrl+1 / Ctrl+2), le gris d'un document pas encore créé (`available`), l'ouverture sur « Projet », le retour sur « Projet » à chaque changement de document, les mots, les icônes, les bulles et l'ordre des panneaux sont ceux de v0.125.
- **Source** : T3 ; inféré (refonte de structure, comme UI-002 de la spec #95)
- **Langues** : fr / de / en
- **Critère d'acceptation** : captures de « Projet » (deux vues) et de « Structure » avant et après jointes à la vérification ; `tests/test_i18n.py` passe sans clé ajoutée ni retirée dans les trois langues, sauf mots génériques propres au type.

### UI-002 — Les documents compilés ne changent pas
- **Exigence** : aucun fichier de projet écrit (`.woodcore`, `data/project.json`, `Template/`, `structure.json`, les `.typ` des sections) ni aucun rapport compilé ne change : octet pour octet, pour les mêmes gestes, sur `tests/projet-exemple/`.
- **Source** : inféré
- **Langues** : —
- **Critère d'acceptation** : `tests/test_project_tab.py`, `tests/test_structure_tab.py`, `tests/test_export_all.py` passent ; le diff ne touche ni `calc/structure.py`, ni `calc/typst_objects.py`, ni `calc/sync.py`, ni `calc/sharing.py`, ni `calc/doc_import.py`, ni `lib/`.

## 5. Exigences d'architecture

### ARCH-001 — Sur quoi `DocumentTab` repose
- **Exigence** : `TabHost` construit aujourd'hui, pour tout onglet, un `SourceStore` du domaine `MODULE`, une source de cas (`make_source`), exige un service nommé `display` (`install_display`), pose la barre « Annuler / Enregistrer » d'un cas au centre et recharge une liste dans `restore` (`calc/tools/tab_host.py:420–448, 464–493, 658–662, 695–718`). Un document n'a ni cas ni « Affichage » ni liste. `DocumentTab` ne peut donc pas être « sur `TabHost` » sans qu'on le dise : Q-001 a choisi (A) d'extraire la partie commune. `TabFrame` porte donc : la construction des services dans l'ordre de `SERVICES`, le contrôle des `NEEDS`, un contexte, `service(nom)`, `phase`, les phases communes, `view_state` / `restore` des services et ce que la fenêtre appelle sans parler de cas. `Service`, `run_phase`, `service_named` et `missing_needs` y sont **déplacés** (et ré-exportés par `tab_host`, dont une vingtaine de modules les importent), sans second mécanisme de services.
- **Source** : T2 ; principe « une seule source » (CLAUDE.md), ARCH-003 de la spec #95
- **Critère d'acceptation** : aucune fonction de `tab_host.py` recopiée dans `document_tab.py` (`tests/test_no_duplicates.py`) ; les tests de `CalcTab` (`tests/test_calc_tab_base.py`, `tests/test_tab_services.py`, `tests/test_snow_source.py`, `tests/test_load_tab.py`) passent sans qu'une assertion change.

### ARCH-002 — Aucun service n'appelle un autre service
- **Exigence** : D-06 vaut pour ce type. Ce qui relie les deux vues de « Projet » (le formulaire de mise en page choisi, les trois lignes de documents, ce qui est non enregistré, la lecture seule) et les parties de « Structure » (l'arbre qui dit quel nœud est choisi, l'aperçu qui le montre, les options qui l'éditent) passe par un contexte du type (`DocumentContext`) et ses phases, jamais par un service qui tient un autre service.
- **Source** : D-06 de la spec #95
- **Critère d'acceptation** : `tests/test_tab_services.py` (imports des modules de services, aucun service n'en tient un autre) couvre les services du type.

### ARCH-003 — Les mots restent à leur place
- **Exigence** : les mots de « Projet » (`pj_`, `tpv_why_`, et les `proj_` de la page de départ qu'il réutilise) et de « Structure » (`st_…` dans `structure_words.py`, `STRINGS` de `structure_tab_view.py`) restent où ils sont, fusionnés comme aujourd'hui par `woodcore_gui_words.py` : ce sont les mots d'un onglet et non des mots génériques d'un service (`Service.WORDS_MODULE = None`). Si le type a des mots génériques (la question avant de quitter), ils vont dans un `STRINGS` au niveau d'un module du type, listé dans `SERVICE_WORDS`.
- **Source** : ARCH-008 de la spec #95 ; CLAUDE.md « No hardcoding »
- **Critère d'acceptation** : `tests/test_i18n.py` passe, y compris le contrôle des clés partagées par deux modules de services.

### ARCH-004 — Les fichiers de `calc/` ne bougent pas
- **Exigence** : seuls `calc/tools/` (l'onglet, ses mixins devenus services, le registre, la garde) et `tests/` changent ; la logique d'un document (structure, objets, partage, synchronisation, templates, projet) reste dans `calc/` sans Qt. Les trois mixins de « Structure » (`structure_tab_share.py`, `structure_tab_view.py`, `structure_tab_write.py`) ne gagnent aucune règle métier en changeant d'hôte.
- **Source** : principe « la logique du domaine est indépendante de l'interface » (CLAUDE.md)
- **Critère d'acceptation** : revue du diff : aucun fichier de `calc/*.py` hors `calc/tools/` modifié ; `git diff --stat` joint à la vérification.

### ARCH-005 — Le cadre sert aussi `DataTab` et, plus tard, `LibraryTab` (revue)
- **Exigence** : `TabFrame` est écrit pour ses trois preneurs, pas pour le seul `DocumentTab`. Il ne construit **aucune mise en page** : chaque type pose son corps par `frame_body(widgets)` (`TabHost` : le séparateur à trois volets, la colonne qui défile, « Annuler / Enregistrer », « Affichage » ; `DocumentTab` : des pages ; `DataTab` : une zone haute et un séparateur facultatif) ; le cadre ne connaît ni `STRETCH`, ni la barre, ni « Affichage ». Il offre trois crochets de type, `frame_prepare` (avant le montage des services), `frame_body` et `frame_finish` (après), et une fabrique de contexte (`CONTEXT`). Le cadre ne définit **ni `dirty`, ni `save`, ni `current_id`, ni `id_edit`, ni `list`** (ARCH-007). Le contexte d'un type est une sous-classe de `FrameContext` ; la signature `(hôte, app)` est celle que `LibraryContext` prendra.
- **Source** : revue (Q-001 A) ; spec #106 ARCH-001 (zone haute, séparateur facultatif, centre sans barre)
- **Critère d'acceptation** : `tests/test_tab_frame.py` (nouveau) monte un cadre nu sur des faux services ; `TabHost.frame_body` est le seul code de mise en page de `tab_host.py` ; la revue de #106 le relit sans modifier `tab_frame.py` hors ajout d'un nom.

### ARCH-006 — « Structure » enveloppée, « Projet » en trois services (revue)
- **Exigence** : **« Structure »** : le service `DocumentStructure` (`NAME = "structure"`, `ZONE = "page"`) monte le widget `StructureView`, l'ancienne `StructureTab` renommée, qui garde ses trois mixins et ne perd que ce qui parlait de l'onglet (`on_mode`, `on_shown`, `confirm_leave`, `flush_pending`, `view_state`, `restore`, l'appel de `restore` en fin d'`__init__`) ; le service les fait suivre par ses phases. Les mixins emploient `self` comme `QObject` (`QFileSystemWatcher(self)`, `shiboken6.isValid(self)`, parent des boîtes, `isVisible`, `showEvent`) : un service ordinaire (sans base Qt, ARCH-RISK-016 de la spec #95) ne peut pas les porter sans réécrire la classe. **« Projet »** : `ProjectDetails` (page « Informations »), `ProjectTemplates` (page « Templates ») et `ProjectActions` (sans volet : `write_apply_form`, `write_create_document`, `open_folder`, la liste des formes), reliés par le contexte seul (ARCH-002).
- **Source** : revue (Q-002 A précisée) ; REQ-002, REQ-003, ARCH-002
- **Critère d'acceptation** : `StructureView` et `DocumentStructure` n'importent aucun autre service ; `tests/test_tab_services.py` couvre les modules de services du type ; les écrivains de `StructureView` (`write_*`) sont gardés une fois là où ils sont définis (ARCH-008).

### ARCH-007 — La fenêtre et l'autosave décident par la présence d'un nom (revue)
- **Exigence** : la fenêtre et `autosave` classent un onglet par les noms qu'il porte : `dirty` (`update_tab_marks`, `update_title`), `save`, `current_id` / `current` (`autosave.is_new`), `id_edit`, `flush_pending`, `on_mode`, `on_shown`, `splitter`, `list` (`tests/test_window.py:39` : un éditeur a `dirty` **et** `list`). `DocumentTab` définit `dirty` et `save` (le brouillon de « Projet » ; faux et sans effet pour « Structure », qui n'a pas de brouillon) ; il ne définit **ni `current_id`, ni `current`, ni `id_edit`, ni `list`** : « Projet » est aujourd'hui traité par `autosave` comme un brouillon « jamais enregistré » (`is_new` vrai faute de `current_id`), et ce comportement-là doit rester le sien. `TabFrame` ne définit aucun de ces noms.
- **Source** : revue ; `calc/tools/autosave.py:104–108, 139–171`, `calc/tools/woodcore_gui_menus.py:318–333`, `tests/test_window.py:39`
- **Critère d'acceptation** : un test de `tests/test_document_tab.py` liste les noms que le cadre et le type ne portent pas ; `tests/test_project_tab.py` gagne un test de `autosave.leave` sur « Projet » avec brouillon (raisons `tab`, `focus`, `replace`) qui donne les mêmes réponses qu'avant la migration (relevées avant le premier changement).

### ARCH-008 — Le registre et la garde suivent le cadre, et les widgets enveloppés (revue)
- **Exigence** : `tab_registry.GUARDED_SERVICES` retient les services de toute classe `TabFrame` (et plus seulement `TabHost`) ; `Service.WIDGET` (défaut `None`) nomme la classe d'un widget qu'un service enveloppe, et le registre l'ajoute à une liste `GUARDED_WIDGETS` gardée par nom (`tab_guard.guard`, les `write_*` de `tab_guard.WRITERS`), de sorte que `test_every_writer_a_tab_reaches_is_guarded_where_it_is_defined_and_once` les couvre. `write_apply_form` et `write_create_document` quittent `tab_guard.WRITERS` : `ProjectActions.WRITERS` les déclare (`guard_service`). `GUARDED_TABS` ne retient plus que les classes qui définissent encore un écrivain de la liste (`DocumentTab.save`, déjà gardé là où il est défini).
- **Source** : revue ; `tab_registry.py:137–146`, `tab_guard.py:12–39, 96–115`
- **Critère d'acceptation** : un test négatif en lecture seule pour `ProjectActions` et pour un écrivain de `StructureView` ; le test des écrivains parcourt `GUARDED_WIDGETS` ; la liste ne garde aucun nom sans définition.

### ARCH-009 — Les fils de l'aperçu de « Projet » gardent leur destinataire (revue)
- **Exigence** : les signaux `done` / `failed` du fil `_Preview` sont aujourd'hui reliés à des méthodes d'un `QWidget` (l'onglet), donc livrés dans le fil de la fenêtre. Un service est un objet ordinaire : relier un signal à sa méthode ne garantit plus le fil du destinataire. `ProjectTemplates` relie le fil à un `QObject` récepteur qu'il possède (la page qu'il monte).
- **Source** : revue ; `calc/tools/project_tab.py:148–168, 577–582`
- **Critère d'acceptation** : un test émet `done` depuis un fil et vérifie que le gestionnaire s'exécute dans le fil principal et que la génération périmée est ignorée.

### ARCH-010 — Ce que #106 reprend (revue)
- **Exigence** : la mise en page de `DataTab`, ses services, son `EXPOSES` et ses tests sont ceux de #106 ; ce lot lui laisse un cadre qui n'exige d'elle que : un `frame_body`, une sous-classe de `FrameContext`, l'ajout de `"EXPOSES"` à `tab_host.PARAMS` et au test de `tests/test_tab_overrides.py` (les méthodes que `DataTab` fabrique pour `EXPOSES` apparaissent dans `vars(classe)` : le test les admet par les clés de `EXPOSES`). `on_mode` et `on_shown` sont déjà ceux du cadre.
- **Source** : revue ; spec #106 ARCH-001, ARCH-005, Q-001
- **Critère d'acceptation** : relevé dans la note de passation du §13 ; vérifié par la revue de #106.

## 6. Contraintes

- **CON-001** — Les fichiers du projet (`.woodcore`, `structure.json`, sections, templates) et leurs formats ne changent pas ; un projet de v0.125 s'ouvre sans migration. Source : principes 8 et 10 (`docs/architecture/principles.md`), inféré.
- **CON-002** — Une version publiée par type migré, vérifiée indépendamment : ce type a sa version. Source : D-18 de la spec #95.
- **CON-003** — Plusieurs sessions modifient le dépôt : jamais `git checkout --`, `stash`, `reset`, `clean` ; `tab_registry.py`, `tab_guard.py`, `tab_host.py` et `test_tab_overrides.py` sont partagés avec d'autres issues (#106 le type « Données », #112, #113, #114, #115) : édition ciblée, coordination par message. Source : CLAUDE.md.
- **CON-004** — Le temps d'ouverture de la fenêtre est mesuré avant et après (la fenêtre construit tous les onglets à l'ouverture) ; « Structure » ne compile rien avant d'être affichée (docstring de `structure_tab.py`, issue #87) et « Projet » non plus (sa première vue ne compile rien). Source : CON-005 de la spec #95 ; docs/ui/tab-project.md.
- **CON-005** — Fichiers en LF, prose sur une ligne, anglais dans le code et les docs ; aucun fichier de `docs/` hors `decisions.md` et `CHANGELOG.md` au-dessus de 100 Ko. Source : CLAUDE.md.
- **CON-006** — Les tests travaillent sur `tests/projet-exemple/` ; aucune écriture dans `../Musterprojekt/`. Source : CLAUDE.md.
- **CON-007** — Plan d'exécution : nouveau type d'onglet, plusieurs modules, une base du type à trancher : `/big-feature`. Source : CLAUDE.md.

## 7. Décisions prises

- **D-01** — Les cinq types sont ceux de D-05 de la spec #95 (Calcul, Dessin, Éditeur, Données, Document) ; ce type s'appelle `DocumentTab` et contient « Projet » et « Structure du document ». Un type est une recette par défaut, il n'enferme pas un onglet. (T1, D-05 de la spec #95)
- **D-02** — Un onglet sur un type n'écrit que ses paramètres et les crochets du type : D-07 de la spec #95 s'applique tel quel. (T3)
- **D-03** — Aucun changement visible, aucun fichier écrit différemment : c'est une refonte de structure (UI-001, UI-002). Inféré de la nature de l'issue ; l'ingénieur ne l'a pas contredit.
- **D-04** — (Q-001 A, ingénieur, 24.10.2026) La base est **un cadre extrait de `TabHost`**, sans cas, sans stockage, sans « Affichage » ni barre d'enregistrement : `TabFrame`. `TabHost`, `DocumentTab`, plus tard `DataTab` (#106, implémentée juste après) et `LibraryTab` reposent dessus. `DocumentTab` n'est donc pas « sur `TabHost` » à la lettre mais sur son cadre : prix vu et accepté.
- **D-05** — (Q-002 A, ingénieur, 24.10.2026) « Structure du document » est **un seul service entier** (`DocumentStructure`) ; son découpage en arbre, aperçu et options est une issue à part.
- **D-06** — (revue, **à confirmer**) `LibraryTab` (#110, construite à côté de `TabHost`) **ne passe pas sur le cadre dans ce lot** : §8 la met hors périmètre et la réponse A de Q-001 dit « dans leurs issues ». Le lot garde le cadre compatible (ARCH-005) et ouvre l'issue de suivi.
- **D-07** — (revue, **à confirmer**) `DocumentTab` ne nomme **aucun service par défaut** (`SERVICES = ()`) : aucune fonction n'est commune à « Projet » et « Structure » ; ce qu'ils partagent (le brouillon, la lecture seule, les phases, la question avant de quitter) est le contexte et le type. Un service devient le défaut du type quand un troisième onglet de document le demande (D-19 de la spec #95). Cela corrige REQ-001, qui demandait « au minimum un service de formulaire du fichier » d'après T2.

## 8. Hors périmètre

- Le type « Données » (`DataTab` : Variables, Métrés, Dépendances, Commandes), issue #106 ; les contenus des onglets Variables (#114) et Commandes (#115), qui changent ce que ces onglets montrent et non leur base.
- Les types « Dessin » et « Éditeur », les onglets de calcul, l'onglet Journal (MODE_BOUND aussi, sur `SourceEditorTab`), l'onglet « Matériaux » (`LibraryTab`).
- Tout changement de ce que « Projet » ou « Structure » font : pas de nouveau champ, bouton ou règle ; pas de découpage de `calc/structure.py` ou de `calc/sync.py`.
- La variante D (un onglet = une ligne du `TabSpec`) : décidée plus tard (D-17 de la spec #95).
- L'extraction d'une logique sans Qt pour la page de titre de « Projet » (le calcul des changements de `save`) : voir §9.

## 9. Idées non retenues comme exigences

- Sortir de `ProjectTab.save` le calcul de « ce qui a changé » (page de titre, version épinglée) en un module sans Qt testé sans `QApplication`, sur le modèle de `draft_logic` : possible, non demandé ; à voir à la revue d'architecture.
- Un service « Document actif » commun (nom du document, dossier, `has_modes`, `is_created`) que « Projet », « Structure » et les onglets qui suivent le document (Journal, Variables) liraient : les trois tabs recalculent aujourd'hui `document_name()` et `doc_dir()` chacun. Non demandé.
- Remplacer la liste `MODE_BOUND` (`woodcore_gui.py`, `tab_registry.TabSpec.mode_bound`) par un paramètre du type : non demandé.

**Sur le partage avec le type « Données » (#106).** `DocumentTab` et `DataTab` ne doivent pas se partager un niveau de classe l'un entre l'autre : un onglet de données ne lit que l'export, n'a ni brouillon, ni écrivain, ni `save`, et sa `confirm_leave` est toujours vraie (« Variables », `PERMITTED`) ; un onglet de document écrit et demande. Ce qu'ils partagent est **le cadre** que `TabHost` ne sait pas encore donner sans cas ni « Affichage » : monter des services dans trois zones, courir des phases dans l'ordre, répondre `service(nom)`, vérifier les `NEEDS`, garder `view_state` / `restore`. C'est exactement la question Q-001 : si la partie commune est extraite, `DataTab`, `DocumentTab` et un jour `LibraryTab` reposent sur elle ; la première des deux issues #106 et #107 qui s'implémente l'extrait, la seconde la reprend. Les specs #114 (Variables) et #115 (Commandes) changent le contenu de deux onglets de données, pas leur base, et n'ont pas à attendre ce type.

## 10. Questions

### Q-001 — Sur quoi `DocumentTab` repose : `TabHost` tel qu'il est, une partie commune extraite, ou à côté comme `LibraryTab` ?
- **Contexte** : l'issue dit « une base mince `DocumentTab` sur `TabHost` ». `TabHost` est bâti autour d'un domaine de cas enregistrés dans le projet : il crée un stockage de cas, une liste, exige le service « Affichage », pose « Annuler / Enregistrer » d'un cas et recharge une liste. « Projet » et « Structure » n'ont rien de cela. Pour le même défaut, l'onglet « Matériaux » a reçu un type à côté de `TabHost` (`LibraryTab`, spec #110, Q-005 réponse A, « un seul socle pour les deux est un pas plus tard »), qui recopie en petit le montage des zones, les phases et `service(nom)`. Le type « Données » (#106) aura le même besoin.
- **Pourquoi elle compte** : elle fixe si `tab_host.py` est refactoré (risque pour le Calcul, la Neige, le Poids propre et le Vent), si une troisième base à peu près jumelle apparaît (la duplication que le projet craint le plus) et ce que #106 réutilise.
- **Options** :
  - **A (recommandée)** — extraire de `TabHost` un cadre sans cas (montage des services en zones, phases, `service`, `NEEDS`, `view_state` des services, partie de `TAB_API` qui ne parle pas de cas) ; `TabHost(cadre)` garde le stockage, la liste, l'« Affichage », la barre d'un cas ; `DocumentTab(cadre)` le prend sans eux ; `DataTab` et `LibraryTab` le prendront dans leurs issues. Prix : on touche `tab_host.py` et on garde les tests de Calcul verts sans changer une assertion ; `DocumentTab` n'est pas, à la lettre, « sur `TabHost` » mais sur son cadre.
  - **B** — garder `DocumentTab` sur `TabHost` à la lettre et rendre facultatif dans `TabHost` ce qu'un document n'a pas (pas de `MODULE`, pas de stockage, pas de service `display`, pas de barre de cas) : une seule classe de base, mais `TabHost` se remplit de `si ce n'est pas un document` et devient le tronc commun de tout.
  - **C** — `DocumentTab` à côté de `TabHost` sur le modèle de `LibraryTab`, ne réutilisant que `Service`, `run_phase` et `service_named` : le moins de risque pour le Calcul, mais un montage de zones, des phases et un `view_state` écrits une troisième fois, puis une quatrième avec `DataTab`.
- **Réponse** : A — extraire de `TabHost` un cadre sans cas, sur lequel reposent `TabHost`, `DocumentTab` et, plus tard, `DataTab` et `LibraryTab` (ingénieur, 24.10.2026). Conséquences relevées à la revue (§13) : le cadre est `TabFrame` (`calc/tools/tab_frame.py`) ; il sert aussi `DataTab` (#106) ; `LibraryTab` le prend dans une issue à part (« à confirmer », D-06).

### Q-002 — « Structure du document » n'est pas un formulaire : un service entier, ou plusieurs ?
- **Contexte** : le guide décrit le type comme « le formulaire du fichier du projet ou du document » (T2), vrai de « Projet » ; « Structure » est un arbre, un aperçu compilé, des options par genre d'objet, un guetteur de fichiers et la synchronisation entre documents, soit environ 3 300 lignes en quatre modules, qui écrivent à chaque geste, sans brouillon. Pour les onglets de dessin, la spec #95 a décidé qu'une toile reste « un service entier, sans la redécouper dans cette refonte » (D-13).
- **Pourquoi elle compte** : elle fixe la taille de l'issue (un déplacement contre une refonte de l'onglet le plus complexe de la fenêtre), l'adaptation des 71 tests de `test_structure_tab.py` et ce que l'onglet « Structure » gagne ou non du type.
- **Options** :
  - **A (recommandée)** — « Structure » devient un seul service entier (`DocumentStructure`, qui garde ses trois mixins) monté par `DocumentTab` : l'onglet est en paramètres seulement, `confirm_leave`, `on_mode`, `on_shown`, `view_state` et `restore` sortent de la classe de l'onglet vers les phases du type, et le découpage de l'arbre, de l'aperçu et des options en services est une issue à part. Prix : le gros du code ne change que d'hôte ; la classe de l'onglet maigrit sans que l'onglet devienne « composé ».
  - **B** — migrer seulement « Projet » maintenant ; « Structure » garde sa classe et son `confirm_leave` (`PERMITTED`) jusqu'à une issue qui le coupe en services. Prix : le type n'est prouvé que par un onglet, l'issue ne remplit qu'à moitié T3, et l'entrée `PERMITTED` de « Structure » reste.
  - **C** — couper « Structure » en services dans cette issue (arbre, aperçu, options, guetteur, synchronisation), liés par le contexte. Prix : la refonte la plus grosse, des signaux à poser pour ce que les mixins s'appellent aujourd'hui directement, un risque réel sur l'écriture des fichiers de l'ingénieur.
- **Réponse** : A — « Structure du document » devient un seul service entier, le découpage de l'arbre, de l'aperçu et des options en services étant une issue à part (ingénieur, 24.10.2026). Précision de la revue (§13, ARCH-006) : le service entier **enveloppe** le widget `StructureView` (l'ancienne classe de l'onglet, qui garde ses trois mixins) au lieu de les porter lui-même, car les mixins emploient `self` comme `QObject` en une vingtaine d'endroits.

## 11. Critères d'acceptation

- [x] REQ-001 — `DocumentTab` existe ; un onglet de paramètres seuls y trouve ses services (`tests/test_document_tab.py`) ; le type n'a aucun service par défaut (D-07, à confirmer).
- [x] REQ-002 — « Projet » en paramètres seulement ; `tests/test_project_tab.py` vert, comportement inchangé.
- [x] REQ-003 — « Structure » en paramètres seulement ; `tests/test_structure_tab.py` vert, comportement inchangé.
- [x] REQ-004 — plus de `confirm_leave` propre ; `PERMITTED` sans `StructureTab` ni `ProjectTab` ; les deux comportements prouvés.
- [x] REQ-005 — `on_mode`, `on_shown`, `flush_pending`, `set_view` répondus par le type ; `TAB_API` étendue et testée.
- [x] REQ-006 — écrivains gardés par service ; test négatif en lecture seule.
- [x] REQ-007 — reconstruction de la fenêtre : brouillon de « Projet », arbre et attente de « Structure » conservés.
- [x] REQ-008 — `test_tab_overrides.py` couvre `DocumentTab` ; `HOOKS` vide.
- [x] REQ-009 — un `NEEDS` manquant arrête la construction en nommant onglet, service et fonction.
- [x] UI-001 — captures avant et après identiques ; `tests/test_i18n.py` vert.
- [x] UI-002 — fichiers de projet et PDF identiques ; aucun fichier de `calc/` hors `calc/tools/` modifié.
- [x] ARCH-001 — base choisie en Q-001 ; aucune fonction de `tab_host.py` recopiée ; tests de Calcul inchangés et verts.
- [x] ARCH-002 — aucun service n'en tient un autre.
- [x] ARCH-003 — mots à leur place, trois langues.
- [x] ARCH-004 — logique de document inchangée dans `calc/`.
- [x] ARCH-005 — le cadre ne construit aucune mise en page ; `tests/test_tab_frame.py`.
- [x] ARCH-006 — « Structure » : `DocumentStructure` enveloppe `StructureView` ; « Projet » : trois services reliés par le contexte.
- [x] ARCH-007 — le cadre et le type ne portent ni `current_id`, ni `id_edit`, ni `list` ; `autosave.leave` sur « Projet » inchangé.
- [x] ARCH-008 — `GUARDED_SERVICES` sur `TabFrame`, `GUARDED_WIDGETS` ; `write_apply_form` et `write_create_document` hors de `tab_guard.WRITERS`.
- [x] ARCH-009 — les fils de l'aperçu livrent dans le fil de la fenêtre.
- [x] ARCH-010 — note de passation pour #106 faite.
- [x] Suivi : issue ouverte pour `LibraryTab` sur le cadre (D-06) ; réponse de l'ingénieur à D-06 et D-07.
- [x] Documentation : `docs/ui/building-a-tab.md` (le type « Document » passe de « décrit » à « écrit », ses services par défaut, un exemple complet avec « Projet »), `docs/ui/tab-project.md` et `docs/ui/tab-structure.md`, `docs/ui/window.md` si le tableau des types y figure, `docs/architecture/layout.md` (les nouveaux modules), `docs/decisions.md` §13 et `docs/decisions-index.md` (le type « Document », la base choisie en Q-001, le découpage de Q-002), entrée `CHANGELOG.md`, page « Nouveautés » de la prochaine version en fr / de / en.
- [x] Tests : `tests/test_document_tab.py` (nouveau, sa ligne dans `docs/conventions/testing-catalogue*.md`), `tests/test_tab_overrides.py`, `tests/test_tab_registry.py`, `tests/test_tab_services.py`, `tests/test_project_tab.py`, `tests/test_structure_tab.py` adaptés ; suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1, D-01, REQ-001 | capturé |
| T2 | REQ-001, ARCH-001, Q-001, Q-002 | capturé ; « sur `TabHost` » → Q-001 (réponse A, D-04), « formulaire » pour Structure → Q-002 (réponse A, D-05) ; « services par défaut » → D-07 (à confirmer) |
| T3 | REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, D-02 | capturé |
| T4 | §11 (documentation, tests), CON-002 | capturé |

### Points de la source non résolus

- T2 — « sur `TabHost` » : résolu par Q-001 A (cadre extrait, D-04).
- T2 / T3 — « le formulaire du fichier du projet ou du document » ne décrit pas « Structure » : résolu par Q-002 A (service entier, D-05) ; « ses services par défaut » reste à confirmer (D-07).

## 13. Revue d'architecture

Revue faite le 24.10.2026 par une lecture du code (`tab_host.py`, `calc_tab.py`, `library_tab.py`, `project_tab.py`, `structure_tab*.py`, `tab_registry.py`, `tab_guard.py`, `autosave.py`, `woodcore_gui.py`, `tests/test_tab_overrides.py`, `test_tab_registry.py`, `test_tab_services.py`, `test_window.py`) et des specs #106 et #110 ; elle ne s'appuie pas sur les docs seules.

**Verdict : APPROUVER AVEC RÉSERVES.** L'architecture choisie (cadre extrait, « Structure » en un service entier) tient, à quatre conditions : le cadre ne pose aucune mise en page (ARCH-005) ; les noms que la fenêtre lit restent absents là où ils changeraient un comportement (ARCH-007) ; le registre et la garde suivent le cadre et les widgets enveloppés (ARCH-008) ; deux points de la spec sont corrigés et **à confirmer par l'ingénieur** (D-06 : `LibraryTab` plus tard ; D-07 : pas de service par défaut).

### Modules touchés (ce que chacun possède aujourd'hui)

| Module | Ce qu'il possède | Ce qui change |
|---|---|---|
| `calc/tools/tab_host.py` (722 l.) | `Service` 48–75, `service_named` / `run_phase` / `missing_needs` 114–132, `TabContext` 135–398, `TabHost` 400–722 (`__init__` 420–448, `_zone` 452, `_centre` 464, `service` 495, `phase` 502, `view_state` 691, `restore` 695, `hideEvent` 720), `TAB_API` 38, `PARAMS` 44 | `Service` et les trois fonctions déménagent dans `tab_frame.py` et sont ré-exportées ; `TabContext(FrameContext)` ; `TabHost(DisplayTab, TabFrame)` ne garde que le cas, le séparateur, la barre, « Affichage » ; `TAB_API = FRAME_API + …` |
| `calc/tools/tab_frame.py` (nouveau) | — | `Service`, les trois fonctions, `FrameContext`, `TabFrame`, `FRAME_API` |
| `calc/tools/document_tab.py` (nouveau) | — | `DocumentContext`, `DocumentTab` |
| `calc/tools/project_tab.py` (598 l.) | `STRINGS` 36–145, `_Preview` 148, `ProjectTab` 171–598 | ne garde que `STRINGS` et `ProjectTab` (paramètres) |
| `calc/tools/project_services.py` (nouveau) | — | `ProjectDetails`, `ProjectTemplates`, `ProjectActions`, `_Preview`, les aides communes aux deux pages (la liste de formes, les modèles d'un document, le nom d'un template de fond) |
| `calc/tools/structure_tab.py` (577 l.) | `StructureTab` 86–577 | `StructureView` (la classe renommée, amincie), `DocumentStructure`, `StructureTab` (paramètres) ; `structure_tab_share/view/write.py` inchangés |
| `calc/tools/tab_registry.py` | `GUARDED_TABS` 137, `GUARDED_SERVICES` 143 | `TabFrame` à la place de `TabHost` ; `GUARDED_WIDGETS` |
| `calc/tools/tab_guard.py` | `WRITERS` 12–39 | deux noms en moins ; aucun changement de code |
| `calc/tools/library_tab.py` | `LibraryTab` 171, `service` 212, `phase` 215, `_zone` 199 | **rien dans ce lot** (D-06) |
| `tests/` | `test_tab_overrides.py` (`PERMITTED` 41, 43 ; `_types` 65 ; `_tab_classes` 47), `test_tab_registry.py`, `test_tab_services.py`, `test_project_tab.py`, `test_structure_tab.py` | adaptés ; `test_tab_frame.py` et `test_document_tab.py` nouveaux |

Aucun fichier de `calc/` hors `calc/tools/` n'est touché (ARCH-004). La fenêtre (`woodcore_gui.py:319, 330, 606, 647`) n'est pas modifiée : elle appelle `confirm_leave`, `on_mode`, `splitter`, `on_shown` par leur nom, et le type les répond.

### Code à réutiliser (et ce qui serait un doublon)

* `Service`, `run_phase`, `service_named`, `missing_needs` : **déplacés**, pas recopiés ; `LibraryTab` les importe de `tab_host` et continue (ré-export).
* `autosave.confirm(app, tab, title, text, discard=…)` et `autosave.leave` : la question avant de quitter est posée par eux, pour « Projet », avec les mots d'aujourd'hui (`UNSAVED_WORDS`). `DocumentTab` ne réécrit pas la question.
* `source_editor.save_shortcut(tab)` : Ctrl+S de « Projet », posé par `DocumentTab.frame_finish` seulement si un service a `save`.
* `cards.column`, `cards.card`, `cards.note`, `pdf_pane.PdfPane`, `template_preview`, `home_page.apply_form`, `project_template.create_document`, `forms`, `doc_templates` : repris tels quels par les services de « Projet » ; `object_panes`, `structure_tree`, `import_dialog` par `StructureView`.
* `TabContext.new` trouve le service qui sait `pick_new` : le même geste (« le service qui sait faire ») sert à `DocumentContext.provide(nom)`  : un service déclare `PROVIDES = (noms…)` et le contexte rend le seul qui l'offre ; **`TabContext.new` ne passe pas dessus dans ce lot** (changer du code de Calcul sans nécessité).
* À ne **pas** créer : un service « formulaire du fichier » générique (un seul preneur, ARCH-RISK-005), un service « document actif » commun (§9 de la spec, non demandé).

### Le cadre : ce qu'il possède, ce qu'il laisse

| | `TabFrame` (tous) | `TabHost` (cas) | `DocumentTab` | `DataTab` (#106) |
|---|---|---|---|---|
| construction | services dans l'ordre de `SERVICES`, `NEEDS` contrôlés (le message de `TabHost` est repris à l'identique), contexte par `CONTEXT`, crochets `frame_prepare` / `frame_body` / `frame_finish`, puis `restore(app.views.get(KEY))` | `TabContext` (stockage, liens), `make_source` en `frame_prepare`, séparateur à trois volets + colonne + barre + « Affichage » en `frame_body`, minuteur et Ctrl+S en `frame_finish` | pages (une ou, par `VIEWS`, une pile), marges nulles | zone haute, séparateur facultatif |
| nom d'un service | `service(nom)`, `has_service`, `phase(nom, …)` | — | — | — |
| phases | `shown`, `mode_changed(mode)`, `revealed` (`showEvent`), `hidden` (`hideEvent`), `flush`, `leave` | `computed`, `saved`, `before_display`, `reload_list`, `update_marks`, `select_row` | `loaded`, `lock`, `discard`, `view_set` | `export_read`… (#106) |
| ce que la fenêtre appelle | `on_shown` (phase `shown`), `on_mode`, `view_state`, `restore`, `splitter`, `view`, `VIEWS`, `service`, `confirm_leave` (défaut : phase `leave`, puis `True`) | la suite de `TAB_API` (cas, brouillon) ; `on_shown` et `confirm_leave` à lui | `dirty`, `save`, `discard`, `flush_pending`, `set_view`, `confirm_leave` (la question) | — |

`view_state` du cadre : `{"splitter": tailles ou None, "services": {nom: état}}` ; `TabHost` y ajoute le brouillon, l'id, le point. `restore` du cadre rend à chaque service son état (`{}` s'il n'en a pas, comme `LibraryTab`), puis le séparateur.

### Le type « Document » en détail

* **`DocumentContext(FrameContext)`** : `dirty` (un drapeau par onglet), `touch()` (pose le drapeau et `app.update_tab_marks()` une fois), `read_only()` / `writable()` (ce que `StructureTab.writable` fait aujourd'hui, mais sans le toucher), `reload()` (lance la phase `loaded` puis `lock`, puis efface `dirty`), `provide(nom)` (le seul service qui offre ce nom ; une erreur nomme l'onglet s'il y en a zéro ou deux : un service ne tient jamais un autre, le contexte les relie).
* **`DocumentTab(TabFrame)`** : `CONTEXT = DocumentContext`, `HOOKS = ()`, `VIEWS = ()`, `SERVICES = ()`, `dirty` (propriété sur le contexte, avec son écriture, `autosave._discard` assigne), `save()` (chaque service qui a `save`, dans l'ordre ; faux au premier refus ; **gardé** comme écrivain de `tab_guard.WRITERS`), `discard()` (phase `discard`), `flush_pending()` (phase `flush`), `confirm_leave()` (phase `leave`, puis, si `dirty`, `autosave.confirm(app, self, t(UNSAVED_WORDS[0]), t(UNSAVED_WORDS[1]), discard=self.discard)`, sinon `True`), `set_view(key, enter)` (change la page de la pile, pose `view`, phase `view_set`), `frame_body` (la page seule, ou la pile ordonnée par `VIEWS` ; `splitter` = celui du premier widget qui en porte un), `frame_finish` (Ctrl+S si un service a `save`).
* **« Structure »** : `DocumentStructure.mount(ctx)` rend `StructureView(app)` ; `shown` → `view.on_shown()`, `mode_changed` → `view.on_mode(mode)`, `flush` → `view.host.flush()`, `leave` → `view._in_tree_signal = False` puis `flush`, `state()` → l'ancien `view_state` du widget (ses effets de bord : écrire l'attente, arrêter la compilation, lâcher le guetteur ; la fenêtre ne le demande que pour reconstruire), `restore(état)` → l'ancien `restore`. `showEvent` / `hideEvent` restent au widget (guetteur, première répartition des volets, première compilation) : aucune phase de plus.
* **« Projet »** : `ProjectDetails` (`ZONE = "page"`, `IN_VIEWS = ("details",)`) : les cartes, la page de titre, `save()` / `discard`, la phase `loaded` (remplir tout depuis le projet), `lock`, `shown` et `mode_changed` (relire si rien n'est non enregistré), son état (brouillon, version). `ProjectTemplates` (`IN_VIEWS = ("templates",)`) : les trois listes, l'aperçu compilé hors du fil, `loaded` / `lock` / `view_set` / `revealed`, son état (document regardé, tailles) et **le séparateur** que la fenêtre lie. `ProjectActions` (sans volet) : `WRITERS = ("write_apply_form", "write_create_document")`, `open_folder`, la liste des formes et des modèles d'un document, lue une fois, le tout offert par `PROVIDES`. Les boutons des deux pages appellent `ctx.provide("write_apply_form")(ref)`.

### Risques

Chacun a une sévérité (bloquant / important / mineur), un lieu et un remède ; la section 14 dit où chacun est traité.

* **ARCH-RISK-001 — Toucher `TabHost` met en jeu tous les onglets de calcul (important).** `TabHost` porte la Neige, le Poids propre, le Vent et, après #112, les quatre vérifications d'éléments. Une extraction « par morceaux » ferait bouger l'ordre de construction (le contexte, puis `make_source`, puis le montage, puis « Affichage », puis le minuteur et Ctrl+S, puis `restore`). *Remède* : un déplacement pur d'abord (P01), l'ordre d'aujourd'hui figé en trois crochets, aucun nom public de `TabHost` renommé (`ctx`, `form`, `splitter`, `display`, `panes`, `refresh_timer`, `live`, `view`) ; la suite de Calcul (et celle de #112) tourne après P01 sans qu'une assertion change ; si une seule assertion doit changer, on s'arrête et on le dit.
* **ARCH-RISK-002 — Le cadre devient un second `TabHost` sous un autre nom (important).** La tentation est d'y mettre le séparateur, la barre ou `STRETCH` « puisque tout le monde en a un ». Ce serait l'option B de Q-001. *Remède* : ARCH-005, le cadre ne pose aucune mise en page ; `tests/test_tab_frame.py` monte un cadre sans séparateur.
* **ARCH-RISK-003 — Les mixins de « Structure » ne se laissent pas porter par un service (important).** 1 499 lignes de mixins emploient `self` comme `QObject` (`QFileSystemWatcher(self)`, `shiboken6.isValid(self)`, `QTimer.singleShot(0, partial(self.deferred, …))`, parent des boîtes). Les faire porter par un `Service` oblige à tenir un widget à côté et à réécrire ces appels : c'est la refonte que Q-002 a écartée. *Remède* : ARCH-006, le service enveloppe `StructureView`. Prix : le service est mince (un `mount` et des renvois de phases) ; les tests accèdent au widget par `tab.service("structure").view`.
* **ARCH-RISK-004 — La garde ne voit plus les écrivains de « Structure » (important).** `GUARDED_TABS` retient les classes qui *portent* un nom de `tab_guard.WRITERS` ; `StructureTab` n'en porte plus (ils sont sur `StructureView`) et `guard_service` ne regarde que des classes de `Service`. Les écritures du document de l'ingénieur seraient permises dans un projet ouvert en lecture seule, sans bruit. *Remède* : ARCH-008 (`Service.WIDGET`, `GUARDED_WIDGETS`) et un test négatif par écrivain ; `test_every_writer_a_tab_reaches…` parcourt la nouvelle liste.
* **ARCH-RISK-005 — Un « service par défaut » du type n'a qu'un preneur (mineur, à confirmer).** REQ-001 demandait « au minimum un service de formulaire du fichier » : un formulaire générique (champs déclarés, « Enregistrer », « Annuler », lecture seule) n'a que « Projet » (la page de titre) comme utilisateur, et le calcul de « ce qui a changé » de `save` y est propre. C'est l'abstraction sans second preneur que la revue refuse (D-19 de la spec #95 demande l'inverse : un service dès qu'un second onglet pourrait le servir). *Remède* : D-07, aucun service par défaut ; `ProjectDetails` est ce formulaire, nommé `SERVICES` de « Projet » ; l'ingénieur confirme.
* **ARCH-RISK-006 — Un drapeau `dirty` par service ferait deux vérités (important).** REQ-004 disait « chaque service dit s'il est modifié ». Deux services d'une même page de titre (« Informations » et le bouton « Appliquer » de « Templates », qui doit enregistrer d'abord si `dirty`) liraient deux drapeaux. *Remède* : un seul drapeau dans `DocumentContext` (`touch`) ; `ProjectActions` lit `ctx.dirty` ; REQ-004 est amendé en ce sens (même mécanisme que `TabContext.touch`, ARCH-RISK-003 de la spec #95).
* **ARCH-RISK-007 — Les noms que la fenêtre lit (important).** Voir ARCH-007. Trois cas : `current_id` absent fait de « Projet » un « brouillon jamais enregistré » pour `autosave.leave` (il n'est donc pas enregistré à la simple sortie de l'onglet, seulement au remplacement ou à la fermeture : à garder) ; `dirty` + `list` fait un éditeur pour `tests/test_window.py` (le type ne doit pas définir `list`) ; `save` présent sur « Structure » est sans effet tant que `dirty` est faux. *Remède* : un test des noms absents, un test d'`autosave.leave` relevé avant le premier changement.
* **ARCH-RISK-008 — `on_mode` et `flush_pending` sur tout onglet du cadre (mineur).** La fenêtre appelle `on_mode` sur tout onglet qui l'a (`woodcore_gui.py:330`) : `TabHost` l'aurait aussi, sans service qui l'écoute ; un tour de plus de `busy.pump()` par changement de document. *Remède* : `on_mode` est au cadre (#106 en a besoin), `flush_pending` au seul `DocumentTab` ; le coût est mesuré par `tests/test_startup.py` et une mesure d'un changement de document avant / après (CON-004).
* **ARCH-RISK-009 — Fils et parents de boîtes (important).** Voir ARCH-009 pour le fil de l'aperçu. Les boîtes de « Projet » (`QMessageBox.question(self, …)`, `home_page.apply_form(self, …)`) prennent comme parent l'onglet (`ctx.host`), pas le service (un service n'est pas un widget). `busy.run_in_thread(self.app, …)` est inchangé.
* **ARCH-RISK-010 — Le temps d'ouverture (mineur).** La fenêtre construit tous les onglets : trois objets de plus pour « Projet », un pour « Structure ». *Remède* : mesure avant / après (P00, P08) ; « Structure » ne compile rien avant d'être affichée, « Projet » non plus (le premier affichage de `ProjectTemplates` reste conditionné par la vue).
* **ARCH-RISK-011 — Plusieurs sessions sur les mêmes fichiers (important, CON-003).** `tab_host.py`, `tab_registry.py`, `tab_guard.py`, `test_tab_overrides.py` sont partagés avec #106 (implémentée juste après), #112 (quatre onglets de vérification déjà sur `CalcTab`), #113, #114, #115. *Remède* : éditions ciblées ; `git status` avant chaque fichier partagé ; message à la session de #106 à la fin de P03 (le cadre est prêt) ; P01 d'un seul tenant, committée (par `finish`) avant que P04 ne commence.
* **ARCH-RISK-012 — Le nom `restore` de « Structure » à la construction (mineur).** `StructureTab.__init__` appelait `self.restore(...)` en dernier ; le cadre le fera : le widget ne doit plus le faire (double lecture de l'arbre). *Remède* : P04 retire l'appel et un test compte une seule lecture à la construction.
* **ARCH-RISK-013 — `LibraryTab` reste une troisième base (mineur, à confirmer).** Elle recopie `service`, `phase`, `_zone` et le montage (≈ 25 lignes, `library_tab.py:181–217`) et n'a pas le contrôle des `NEEDS`. *Remède* : D-06 la laisse à son issue ; le cadre est compatible (`LibraryContext.__init__(tab)` deviendra `(hôte, app)`, ses `view_state` / `restore` / `confirm_leave` restent les siens) ; une issue de suivi est ouverte à la fin du lot, et `docs/open-questions.md` la note. Raison de ne pas la faire ici : §8 de la spec la met hors périmètre, la réponse A dit « dans leurs issues », et le gain est faible (≈ 25 lignes) pour un risque sur un onglet livré la veille (#110).

### Pour #106 (note de passation)

`DataTab` s'écrit sur `TabFrame` sans le modifier : (1) `CONTEXT` = une sous-classe de `FrameContext` ; (2) `frame_body` pose la zone haute (service `ZONE = "top"`), un séparateur facultatif (aucun pour « Métrés ») et le centre sans barre ; (3) `confirm_leave` est celui du cadre (phase `leave`, `True`) : **le type ne définit ni `dirty` ni `save`** ; (4) `EXPOSES` : `__init_subclass__` du type fabrique les renvois ; ajouter `"EXPOSES"` à `tab_host.PARAMS` et faire admettre à `_unauthorised` les noms fabriqués ; (5) `GUARDED_SERVICES` retient déjà les services de toute classe `TabFrame` ; (6) `Service.WIDGET` existe pour un navigateur entier qui garderait ses écrivains sur son widget (la carte du fichier de « Métrés » est, elle, un service à `WRITERS`). `on_mode`, `on_shown`, `hidden` sont du cadre.

### Tests à ajouter ou étendre

* **Nouveaux** : `tests/test_tab_frame.py` (cadre nu : ordre des phases, `service`, `NEEDS` nommant onglet / service / fonction, `view_state` / `restore`, aucun des noms de ARCH-007, aucune mise en page) ; `tests/test_document_tab.py` (`confirm_leave` sur un faux service à brouillon et un faux service à écriture immédiate, `save` dans l'ordre et au premier refus, `provide` à zéro / un / deux fournisseurs, pile des pages et `set_view`, `HOOKS` vide, `NEEDS`, écrivain refusé en lecture seule).
* **Étendus** : `test_tab_overrides.py` (`_types()` rend `(CalcTab, DocumentTab)`, `_tab_classes` s'arrête à `TabFrame`, deux entrées de `PERMITTED` retirées, `DocumentTab.HOOKS == ()`) ; `test_tab_registry.py` (`GUARDED_SERVICES` sur `TabFrame`, `GUARDED_WIDGETS`, `FRAME_API` pour `DocumentTab`, `test_every_tab_class_keeps_its_view_through_a_rebuild`) ; `test_tab_services.py` (modules de services de « Projet » dans `SERVICES`, aucun ne tient un autre) ; `test_project_tab.py` (accès par `tab.service(...)`, `autosave.leave`, fil de l'aperçu) ; `test_structure_tab.py` (assistant d'accès, `StructureView.ask_*`, une seule lecture à la construction) ; `test_window.py` et `test_i18n.py` sans modification attendue.

### Exigences nées de la revue

ARCH-005 à ARCH-010 (§5), D-04 à D-07 (§7). REQ-001, REQ-002, REQ-003, REQ-004 et REQ-005 sont amendés à l'endroit où elles sont écrites.

## 14. Plan d'implémentation

Neuf pas, dans cet ordre ; chacun laisse la suite de tests verte avant le suivant. Le cadre (P01–P03) est prêt pour #106 avant que « Structure » et « Projet » ne bougent ; P01 est committée seule (skill `finish`). Aucun pas ne touche `calc/` hors `calc/tools/`.

| Pas | Quoi | Fichiers | REQ / ARCH | Preuve |
|---|---|---|---|---|
| **P00** | Relevés avant tout changement : captures de « Projet » (deux vues) et de « Structure » (fr), temps d'ouverture de la fenêtre et d'un changement de document, réponses d'`autosave.leave` sur « Projet » propre / modifié (raisons `tab`, `focus`, `replace`), liste des écrivains gardés ; suites de Calcul, de « Projet » et de « Structure » vertes | aucun fichier du dépôt (relevés joints à §15) | UI-001, UI-002, CON-004, ARCH-RISK-007, ARCH-RISK-010 | les relevés existent ; `python tests/run_tests.py --related calc/tools/tab_host.py` vert |
| **P01** | **Le cadre**, déplacement pur : `Service` (+ `PROVIDES = ()`, `WIDGET = None`), `service_named`, `run_phase`, `missing_needs` vont dans `tab_frame.py` et sont ré-exportés par `tab_host` ; `FrameContext` ; `TabFrame` (construction, `NEEDS`, `service`, `has_service`, `phase`, phases `shown` / `mode_changed` / `revealed` / `hidden` / `flush` / `leave`, `on_shown`, `on_mode`, `view_state`, `restore`, `confirm_leave` par défaut, `FRAME_API`) ; `TabContext(FrameContext)` ; `TabHost(DisplayTab, TabFrame)` par `frame_prepare` (`live`, `make_source`), `frame_body` (séparateur, colonne, barre, « Affichage »), `frame_finish` (minuteur, Ctrl+S) ; `TAB_API = FRAME_API + …` | `calc/tools/tab_frame.py` (nouveau), `calc/tools/tab_host.py` | ARCH-001, ARCH-005, ARCH-RISK-001, 002, 008, 011 | `test_calc_tab_base`, `test_tab_services`, `test_snow_source`, `test_load_tab`, `test_tab_registry`, `test_tab_overrides`, `test_dead_load*`, `test_wind*` et les tests de #112 : **aucune assertion modifiée** ; `tests/test_tab_frame.py` (nouveau) ; `test_no_duplicates` |
| **P02** | Le registre, la garde et le test des redéfinitions suivent le cadre : `GUARDED_SERVICES` sur `TabFrame`, `GUARDED_WIDGETS` (de `Service.WIDGET`), `_tab_classes` s'arrête à `TabFrame` | `calc/tools/tab_registry.py`, `tests/test_tab_overrides.py`, `tests/test_tab_registry.py` | ARCH-008, ARCH-RISK-004 | `test_every_writer_a_tab_reaches_is_guarded_where_it_is_defined_and_once` (étendu), `test_tab_overrides` |
| **P03** | **`DocumentTab`** et `DocumentContext` (`dirty`, `touch`, `reload`, `provide`, `read_only`, `writable`) ; pile de pages, `set_view`, `save`, `discard`, `flush_pending`, `confirm_leave`, Ctrl+S, `HOOKS = ()` ; `_types()` rend `(CalcTab, DocumentTab)` ; message à la session de #106 (le cadre est prêt, note de §13) | `calc/tools/document_tab.py` (nouveau), `tests/test_document_tab.py` (nouveau), `tests/test_tab_overrides.py` | REQ-001, 004, 005, 008, 009, ARCH-002, 007, 010 | `tests/test_document_tab.py` : faux service à brouillon et faux service à écriture immédiate, ordre des phases, `provide`, noms absents, écrivain refusé en lecture seule, `NEEDS` manquant |
| **P04** | **« Structure »** : `StructureTab` → `StructureView` (retire `on_mode`, `on_shown`, `confirm_leave`, `flush_pending`, `view_state`, `restore` et l'appel final de `restore` ; ces corps deviennent les renvois de `DocumentStructure`) ; `StructureTab(DocumentTab)` en paramètres ; `("StructureTab", "confirm_leave")` retiré de `PERMITTED` ; les mots restent où ils sont | `calc/tools/structure_tab.py`, `tests/test_structure_tab.py`, `tests/test_tab_overrides.py`, `tests/test_project_tab.py` (le passage par la fenêtre, ligne 220) | REQ-003, 004, 005, 006, 007, ARCH-003, 004, 006, ARCH-RISK-003, 004, 012 | les 71 tests de `test_structure_tab.py` (accès par `tab.service("structure").view`, `StructureView.ask_*`), `test_tab_overrides`, `test_tab_registry` ; test négatif en lecture seule sur un `write_*` ; une lecture à la construction |
| **P05** | **« Projet »** : `project_services.py` (`ProjectDetails`, `ProjectTemplates`, `ProjectActions`, `_Preview` relié à un `QObject` récepteur) ; `ProjectTab(DocumentTab)` en paramètres (`KEY`, `VIEWS`, `SERVICES`, `UNSAVED_WORDS`) ; `write_apply_form` et `write_create_document` retirés de `tab_guard.WRITERS` ; `("ProjectTab", "confirm_leave")` retiré de `PERMITTED` ; les boîtes prennent `ctx.host` pour parent | `calc/tools/project_services.py` (nouveau), `calc/tools/project_tab.py`, `calc/tools/tab_guard.py`, `tests/test_project_tab.py`, `tests/test_tab_overrides.py`, `tests/test_tab_services.py` | REQ-002, 004, 005, 006, 007, ARCH-002, 003, 006, 008, 009, ARCH-RISK-005, 006, 007, 009 | les 10 tests de `test_project_tab.py` (accès par `tab.service(...)`) ; `autosave.leave` identique au relevé de P00 ; test du fil de l'aperçu ; test négatif en lecture seule de `ProjectActions` ; `test_every_writer…` |
| **P06** | Passages de fenêtre : reconstruction (`test_every_tab_class_keeps_its_view_through_a_rebuild` étendu aux deux onglets : brouillon de « Projet », arbre et attente de « Structure »), changement de document, `MODE_BOUND` inchangé, mots, démarrage | `tests/test_tab_registry.py`, `tests/test_window.py`, `tests/test_i18n.py`, `tests/test_startup*.py` (lecture) | REQ-005, 007, UI-001, CON-004, ARCH-RISK-008, 010 | ces tests ; captures et mesures de P00 refaites et jointes |
| **P07** | Documentation : `docs/ui/building-a-tab.md` (le cadre et ses preneurs, le type « Document » de « décrit » à « écrit », l'exemple complet « Projet » en paramètres, la phrase « Projet, Structure — le formulaire » corrigée), `docs/ui/tab-project.md` (ses trois services), `docs/ui/tab-structure.md` (le service entier et `StructureView`), `docs/ui/window.md` (le renvoi vers le guide), `docs/architecture/layout.md` (`tab_frame.py`, `document_tab.py`, `project_services.py`), `docs/decisions.md` §13 et `docs/decisions-index.md` (le cadre, le type « Document », l'enveloppe de « Structure », D-06 et D-07), `docs/open-questions.md` (`LibraryTab` sur le cadre ; un service par défaut du type quand un troisième onglet de document existe), `CHANGELOG.md`, `VERSION` et la page « Nouveautés » de la version en fr / de / en (une ligne : les deux onglets du groupe Document reposent sur le nouveau type, rien ne change à l'écran ni dans les rapports), lignes du catalogue des tests (`test_tab_frame.py` et `test_document_tab.py` dans `testing-catalogue-window.md`, les lignes de `test_tab_overrides`, `test_tab_registry`, `test_tab_services`, `test_project_tab`, `test_structure_tab` mises à jour) | les fichiers cités | CON-002, CON-005, ARCH-010, §11 « Documentation » | `tests/test_docs_coherence.py` (aucun fichier de `docs/` hors `decisions.md` et `CHANGELOG.md` au-dessus de 100 Ko, LF, prose sur une ligne) ; `tests/test_i18n.py` ; le catalogue complet |
| **P08** | Suite complète (en arrière-plan), vérification indépendante (`verify-requirements`), `git diff --stat` joint (ARCH-004), puis `finish` : un commit, la question « Pousser ? » ; l'issue de suivi `LibraryTab` sur le cadre est ouverte avec le push ; la publication (installateur, site) attend la parole de l'ingénieur | — | tous | suite verte ; §15 écrite par le vérificateur |

**Les risques de la revue, un à un.** ARCH-RISK-001, 002, 008, 011 → P01 et P02 (déplacement pur, cadre sans mise en page, suite de Calcul inchangée, commit seul). 003 → P04 (enveloppe, pas de réécriture des mixins). 004 → P02 et P04 (`GUARDED_WIDGETS`, test négatif). 005 → **non appliqué comme demandé** : aucun service par défaut (D-07, à confirmer). 006 → P03 et P05 (un drapeau dans le contexte). 007 → P00, P03, P05 (relevé avant, test des noms absents). 009 → P05 (récepteur `QObject`, parent des boîtes). 010 → P00 et P06 (mesures). 012 → P04. 013 → **non appliqué** : `LibraryTab` reste à son issue (D-06, à confirmer), l'issue de suivi est ouverte en P08.

**Ce que l'ingénieur doit encore trancher** : D-06 (`LibraryTab` sur le cadre dans une issue à part, comme recommandé, ou dans ce lot en P09) ; D-07 (aucun service par défaut pour `DocumentTab`, comme recommandé, ou un « formulaire du fichier » générique malgré son seul preneur).

## 15. Vérification

_(écrite par `verify-requirements`, agent indépendant, base `75e7f421`, implémentation `d0224835`, le 25.10.2026 ; complétée par l'implémenteur pour les réserves levées)_

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `calc/tools/document_tab.py` : `DocumentTab(TabFrame)`, `SERVICES = ()`, `HOOKS = ()`, `DocumentContext` ; `test_a_tab_of_parameters_alone_finds_its_services_and_the_type_names_none` ; ligne au catalogue. |
| REQ-002 | ✅ | `ProjectTab` : `KEY`, `VIEWS`, `SERVICES`, `UNSAVED_WORDS` seuls ; `test_project_tab` : les 10 tests d'avant + `autosave.leave` + reconstruction, accès par `tab.service(…)`, aucune assertion de comportement retirée. |
| REQ-003 | ✅ | `StructureTab(DocumentTab)`, `SERVICES = (DocumentStructure,)`, `WIDGET = StructureView` ; `test_structure_tab` : 72 (71 + une lecture de l'arbre) ; `StructureView.ask_*`. |
| REQ-004 | ✅ | `DocumentTab.confirm_leave` ; deux entrées de `PERMITTED` retirées ; `test_confirm_leave_asks_for_a_draft_changed_and_writes_what_is_pending_at_once`. |
| REQ-005 | ✅ | `FRAME_API`, `TAB_API = FRAME_API + …` ; `test_every_tab_class_keeps_its_view_through_a_rebuild` étendu ; `MODE_BOUND` inchangé. `on_properties_changed` ajouté (appelé par la fenêtre, absent de la liste de la spec : divergence notée). |
| REQ-006 | ✅ | `ProjectActions.WRITERS` gardés ; `test_a_writer_of_projet_and_one_of_structure_are_refused_read_only` ; sur un onglet réel : `test_read_only_shows_the_tab_and_writes_nothing` (fenêtre en lecture seule, `save` et `write_apply_form` refusés) et les tests de lecture seule de `test_structure_tab` (`FakeApp(read_only=True)` sur un `StructureTab` réel). Réserve du vérificateur (faux contexte) levée par ces tests existants. |
| REQ-007 | ✅ | `DocumentStructure.state/restore` ; tests de reconstruction de `test_structure_tab` ; `test_a_title_page_typed_and_not_saved_survives_a_rebuilt_window` ajouté après la vérification (réserve levée). |
| REQ-008 | ✅ | `_types()` = `(CalcTab, DocumentTab)` ; `test_a_tab_of_a_document_writes_only_its_parameters`. |
| REQ-009 | ✅ | `TabFrame.check_needs` (`NEEDS_MODULE` ou `MODULE`) ; `test_a_service_of_a_document_that_lacks_what_it_needs_stops_the_tab`, `test_a_service_that_lacks_what_it_needs_stops_the_tab_naming_tab_service_and_function`. |
| UI-001 | ✅ | Captures avant / après (`107-before-*`, `107-after-*`) : « Projet » identique au pixel ; « Structure » ne diffère que par le chemin temporaire dans l'erreur de compilation de l'aperçu (même erreur avant et après). `test_i18n` vert, aucune clé ajoutée. |
| UI-002 | ⚠️ | Diff sans `calc/*.py` hors `calc/tools/`, ni `lib/`. `tests/test_export_all.py` cité par le critère n'existe pas (critère mal écrit) ; les écritures sont tenues par `test_project_tab` (seul ce qui a changé est écrit ; rien à l'ouverture) et `test_structure_tab` (octets hors balises inchangés). Pas de comparaison octet pour octet d'un PDF. |
| ARCH-001 | ✅ | Déplacement pur, ré-export (`test_what_moved_out_of_the_host_is_the_object_it_re_exports`), `test_no_duplicates`, tests de Calcul verts sans assertion changée. |
| ARCH-002 | ✅ | `test_the_services_of_a_document_import_no_other_service_and_hold_none` ; liens par `ctx.provide`. |
| ARCH-003 | ✅ | Aucun fichier de mots touché ; `test_i18n` vert. |
| ARCH-004 | ✅ | `git diff --stat` : `calc/tools/`, tests, docs, site seulement ; mixins de « Structure » inchangés. |
| ARCH-005 | ✅ | `TabFrame` sans layout ni noms d'éditeur ; `test_the_frame_lays_nothing_out_and_names_nothing_of_an_editor`. |
| ARCH-006 | ✅ | `DocumentStructure` enveloppe `StructureView` ; « Projet » en trois services. |
| ARCH-007 | ✅ | `test_the_type_carries_no_name_of_an_editor_of_cases` ; `test_the_autosave_leaves_a_draft_of_projet_as_before_the_type` (réponses de P00). |
| ARCH-008 | ✅ | `GUARDED_SERVICES` sur `TabFrame`, `GUARDED_WIDGETS` ; `write_apply_form` / `write_create_document` hors de `tab_guard.WRITERS` ; test des écrivains étendu (widgets, aucun nom sans définition). |
| ARCH-009 | ✅ | `_Receiver(QObject)` ; `test_the_preview_of_templates_is_delivered_in_the_window_s_thread_and_a_stale_one_ignored`. |
| ARCH-010 | ✅ | Note de passation en §13 ; `tab_frame.py` n'a pas à changer pour `DataTab`. |
| CON-004 | ✅ | Ouverture de la fenêtre 6,55 s avant, 5,69 s après ; changement de document 0,11 s avant et après (même script, scratchpad `p107/shots.py`). |
| Suivi | ✅ | Issues ouvertes : #119 (`LibraryTab` sur le cadre, D-06), #120 (découpage de « Structure », D-05) ; D-06 et D-07 acceptés à l'approbation du 24.10.2026. |
| Documentation | ✅ | building-a-tab, tab-project, tab-structure, window, layout, decisions §13 et index, open-questions, CHANGELOG, Nouveautés 0.125 fr/de/en, catalogue ; spec déplacée dans `completed/` (liens justes). |
| Tests | ✅ | Suite complète en fin de lot (voir §16). |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #107 (4 points) et du code de `ProjectTab`, `StructureTab` et `TabHost` ; deux questions ouvertes (socle du type, découpage de « Structure ») |
| 2026-10-24 | specified | réponses de l'ingénieur : Q-001 A (cadre extrait de `TabHost`), Q-002 A (« Structure » un service entier) ; D-04, D-05 ; REQ et critères alignés |
| 2026-10-24 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (13 risques, ARCH-005 à 010 ajoutées, REQ-001 à 005 amendées) ; plan en 9 pas (§14) ; **à confirmer par l'ingénieur** : D-06 (`LibraryTab` plus tard) et D-07 (aucun service par défaut) ; aucune approbation encore, rien n'est implémenté |
| 2026-10-24 | approved | approbation unique des huit specs du 24.10.2026 par l'ingénieur (AskUserQuestion) : plan approuvé tel quel ; toutes les propositions « à confirmer » des revues acceptées comme recommandées ; ordre d'implémentation #108 → #115 → #114 → #113 → #112 → #109 → #107 → #106, un agent par issue ; commits et push autorisés au fil du travail ; écarts et questions notés en §16 et posés à la fin |
| 2026-10-25 | implementation | P00 : relevés faits avant tout changement — captures `107-before-01/02/03` (Projet Informations, Projet Templates, Structure ; scratchpad `screens/`), ouverture de la fenêtre 6,55 s, changement de document 0,11 s, réponses d'`autosave.leave` sur « Projet » (propre : vrai partout sans enregistrer ; modifié : `tab` faux, `focus` faux, `replace` vrai et enregistré), liste des classes gardées ; 295 tests liés verts |
| 2026-10-25 | implementation | P01 : `calc/tools/tab_frame.py` (`Service` + `PROVIDES`, `WIDGET`, `NEEDS_MODULE` ; `service_named`, `run_phase`, `missing_needs` déplacés et ré-exportés ; `FrameContext` ; `TabFrame` sans mise en page, crochets `frame_prepare` / `frame_body` / `frame_finish`, `FRAME_API`) ; `TabHost(DisplayTab, TabFrame)`, `TabContext(FrameContext)`, `TAB_API = FRAME_API + …` ; `tests/test_tab_frame.py` ; tests de Calcul verts sans assertion changée (ARCH-001, ARCH-005) |
| 2026-10-25 | implementation | P02 : `GUARDED_SERVICES` sur `TabFrame`, `GUARDED_WIDGETS` ; `_tab_classes` s'arrête au cadre ; test des écrivains étendu aux widgets et aux noms sans définition (`create_plans` retiré de `tab_guard.WRITERS`) (ARCH-008) |
| 2026-10-25 | implementation | P03 : `calc/tools/document_tab.py` (`DocumentContext`, `DocumentTab`, `on_properties_changed` en plus : la fenêtre l'appelle) ; `tests/test_document_tab.py` ; `_types()` = `(CalcTab, DocumentTab)` (REQ-001, 004, 005, 008, 009, ARCH-002, 007) |
| 2026-10-25 | implementation | P04 : `StructureView` + `DocumentStructure` + `StructureTab` en paramètres ; une lecture de l'arbre à la construction ; tests adaptés (`_view`, `_host`) (REQ-003, ARCH-006, ARCH-RISK-012) |
| 2026-10-25 | implementation | P05 : `calc/tools/project_services.py` (`ProjectDetails`, `ProjectTemplates` avec récepteur `QObject`, `ProjectActions`) ; `ProjectTab` en paramètres ; `write_apply_form` / `write_create_document` hors de `tab_guard.WRITERS` ; deux entrées de `PERMITTED` retirées ; test `autosave.leave` identique au relevé P00 (REQ-002, 004, 006, 007, ARCH-009) |
| 2026-10-25 | testing | P06–P07 : passages de fenêtre (captures « after » identiques à l'œil aux « before »), documentation (building-a-tab, tab-project, tab-structure, window, layout, decisions §13 et index, open-questions, CHANGELOG, Nouveautés 0.125 fr/de/en, catalogue) ; suite complète : 3401 passés, 8 sautés, 2 échecs corrigés ensuite (`writable` en double → `document_tab.writable` ; lignes du catalogue) |
| 2026-10-25 | completed | vérification indépendante (requirements-verifier) : aucun ❌ ; réserves levées — test de reconstruction de « Projet » avec brouillon, mesures après (5,69 s / 0,11 s), issues #119 et #120 ouvertes ; UI-002 reste ⚠️ (critère citant un test inexistant) ; spec déplacée dans `completed/` |
