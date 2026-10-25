---
id: 2026-10-23-onglets-types-et-services
titre: Les onglets construits à partir de types et de services (issue #95, variante F)
status: completed
cree: 2026-10-23
mis_a_jour: 2026-10-23
source: issue GitHub #95 ; messages écrits de l'ingénieur du 23.10.2026 ; ses réponses aux 17 questions de l'artefact « Onglets en briques » (https://claude.ai/artifact/Y4pdcDgf73qKdmHVdsJvyi, §11)
docs: [docs/ui/window.md, docs/ui/calc-tab.md, docs/ui/tab-snow.md, docs/architecture/principles.md, docs/architecture/layout.md, docs/decisions.md]
---

# Les onglets construits à partir de types et de services — Spécification

## 1. Objectif

Un onglet ne se copie plus : il se construit à partir d'un **type** (une base mince : Calcul, Dessin, Éditeur, Données, Document) qui assemble des **services**, chacun écrit une fois, testé seul, et qu'un onglet peut ajouter ou retirer. Modifier un comportement de tous les onglets (l'accordéon des modules, la liste des cas) se fait dans un seul service ; modifier ce qu'ont tous les onglets d'un type se fait dans sa base mince. Cette issue écrit le mécanisme et les services du type Calcul, et y fait passer la Neige et le Poids propre ; le Vent sera le premier onglet construit sur ce type, juste après, et les autres types suivent dans leurs propres issues.

## 2. Source

### Le premier message de l'ingénieur (23.10.2026)

> **T1** — « Je souhaite réfléchir à l'issue 95. Comment est-ce que cela pourrait être fait? Il y a différentes fonctionnalités qu'il a besoin dans les onglets. »
>
> **T2** — « L'idée, c'est de regrouper toutes les fonctionnalités, enfin de les regrouper dans des, comme dans des gros blocs, et ensuite on peut créer un nouvel onglet et le fabriquer en fonction des fonctionnalités que l'on souhaite. »
>
> **T3** — « Donc, par exemple, il y a la fonctionnalité moteur de dessin, il y a la fonctionnalité calcul, affichage, le système en accordéon, le système de PDF qui s'ouvre en l'onglet moteur de dessin, on clique dessus. Il y a plein de fonctionnalités. »
>
> **T4** — « J'imagine qu'on pourrait tout regrouper en sorte de fonction, de bloc, et que lorsqu'on crée un nouvel onglet, on va juste rechercher ces blocs-là. Comme ça, si on souhaite modifier un comportement des onglets, il suffit de modifier le bloc en question, par exemple le bloc d'ouverture en accordéon. »
>
> **T5** — « Mais réfléchis profondément à la question, fais-moi un artefact qui présente plusieurs variantes qui sont censées, afin que je puisse voir ce qui est le mieux, avant de pouvoir prendre une décision. »

### L'issue #95 (ouverte le 22.10.2026)

> **T6** — « L'ingénieur, 22.10.2026 : on ne copie plus des onglets. Un nouvel onglet se **construit à partir de paramètres de base**. »
>
> **T7** — « L'issue #68 (« Structure commune des onglets », close) a déjà posé une partie de cette base, en v0.120 : le registre unique `calc/tools/tab_registry.py` (`TabSpec`) ; la garde de lecture seule `tab_guard.py` ; `SourceEditorTab` et `CanvasEditorTab`, et le test de contrat `tests/test_tab_registry.py`. Le travail reste partiel. Sa propre vérification signalait des méthodes de liste encore redéfinies onglet par onglet : `confirm_leave`, `update_list_marker`, `reload_list`… Et la refonte de l'onglet Neige (#94) a montré tout ce qu'un onglet de calcul refait encore pour lui-même. »
>
> **T8** — « Cette issue demande que le principe soit **vraiment** appliqué, et d'abord réfléchi : quels types d'onglets Woodcore a besoin, et quelles fonctionnalités un onglet choisit. »
>
> **T9** — « Les onglets héritent d'un empilement de classes et de mixins. Le même genre d'onglet a donc plusieurs bases, et une fonctionnalité est parfois écrite deux fois. » (suivi du tableau des genres : Charges, Vérifications, Dessins, Éditeurs de sources, Autres)
>
> **T10** — « **Les types d'onglets.** Faire l'inventaire des onglets existants et à venir : vent, séisme, charges utiles, la suite des vérifications. En tirer un petit nombre de types : par exemple onglet de calcul (cas en liste, formulaire, volet de modules, Affichage), onglet de dessin, onglet de données (tableaux), onglet de document. Pour chacun, dire ce qu'il a par défaut. »
>
> **T11** — « **Les fonctionnalités, choisies comme des briques.** Un onglet est un type et une liste de fonctionnalités déclarées dans son `TabSpec`, chacune écrite une fois avec son test. Par exemple : liste des cas en dossiers, archives, identité ; formulaire déclaratif et ses genres de champs ; bulles de la norme (survol, épingle, Ctrl+clic au chapitre) ; volet de modules (état du calcul, résultats, extraits, dessins, graphiques ; glisser-déposer, réduire, fenêtre) ; vue Affichage d'un fichier `.typ` ligne par ligne ; vues Dessin, Import et Export ; liens vers une carte externe (261.sia.ch). »
>
> **T12** — « **Un contrat déclaratif** : ce qu'un domaine fournit (champs, calcul, messages, résultats, dessins, extraits de la norme, générateur `.typ`) et ce que la base fait de lui. Ajouter un onglet = écrire son `TabSpec` et ses fonctions de domaine, sans copier de widget. »
>
> **T13** — « **La migration**, lot par lot : les onglets existants passent sur les types et les briques. Les méthodes encore redéfinies par onglet disparaissent. »
>
> **T14** — « **La documentation** : « Ajouter un onglet » (`docs/ui/window.md`) devient le guide de construction par type et par briques, avec un exemple complet. La décision va dans `docs/decisions.md`. »
>
> **T15** — « Demandes : [ ] L'inventaire des onglets et la liste des types, avec ce que chacun a par défaut, soumis à l'ingénieur. [ ] Les briques de fonctionnalités, chacune écrite une fois, testée seule, et choisie dans le `TabSpec`. [ ] Le contrat déclaratif d'un onglet de calcul ; un test qui monte un onglet sur un domaine inventé. [ ] Les onglets existants migrés, sans méthode de base redéfinie ; un test qui le vérifie (étendre `tests/test_tab_registry.py`). [ ] Le guide « construire un onglet » et la décision. »
>
> **T16** — « **#94 (onglet Neige)** est le premier onglet de calcul à bâtir sur ce modèle. Sa section « Un onglet type » décrit la base des onglets de calcul. Les deux issues se cadrent ensemble, et cette issue-ci donne le cadre général. L'onglet Vent sera le deuxième consommateur. Substantielle, multi-modules : `/big-feature`. »

### Les retours de l'ingénieur sur l'artefact (23.10.2026)

> **T17** — « Tu m'as expliqué le contexte à garder en tête. J'avais choisi l'option B. Est-ce que tu vois d'autres options qui feraient plus de sens? Est-ce que l'option C, des services par composition, ça aurait en fait plus de sens? Explique-moi les différences. Qu'est-ce qu'on gagnerait? Qu'est-ce qu'on perdait avec l'une ou l'autre des solutions? Est-ce qu'il y aurait encore une autre solution? »
>
> **T18** — « Tu proposes 5 types qui suffisent pour les 39 onglets. Mais je vois des difficultés, par exemple, pour l'onglet. Poids propre. Et surcharge. Bien, il me semble que le moteur de dessin, que l'on va encore beaucoup améliorer pour afficher rapidement les couches que l'on choisit, va être un gros chantier et qu'il serait dommage que cela soit simplement un code propre à cet onglet et que l'on ne puisse pas tout d'un coup le réutiliser pour un autre onglet si le besoin s'en fait ressentir. »
>
> **T19** — « Tout à la fin de l'artifact pose toutes les questions nécessaires si je souhaite implémenter l'option F, car c'est sans doute l'option que je vais implémenter et je ne répondrai donc qu'à ces questions-là. »
>
> **T20** — « Précise-moi pour la question 9, quel est le coût de dire oui? Est-ce que je comprends bien qu'il y aura deux classes par service et donc ce sont deux choses à garder identiques […] »

### Les réponses de l'ingénieur aux 17 questions (23.10.2026), mot pour mot

> **T21** — « Q1 Que couvre l'issue #95 ? → a) Les services communs et le type Calcul (Neige, Vent, Poids propre). Les vérifications, les éditeurs, les données, les documents et les dessins viennent chacun dans une issue suivante. »
>
> **T22** — « Q2 Quel onglet prouve le modèle en premier ? → a) La Neige repassée sur CalcTab, sans changement visible, puis le Vent construit directement dessus. »
>
> **T23** — « Q3 Quand la session #96/#99 aura-t-elle la main sur les fichiers ? → a) Attendre que #96/#99 soit terminé et commité avant le premier lot d'implémentation ; la spec peut s'écrire dès maintenant. »
>
> **T24** — « Q4 Quels types d'onglets ? → a) Cinq : Calcul, Dessin, Éditeur, Données, Document. Une vérification est un Calcul avec une carte Position et un Verdict. »
>
> **T25** — « Q5 Comment les services se parlent-ils ? → a) Un TabContext par onglet porte le cas, le brouillon et des signaux Qt ; un service n'appelle jamais directement un autre service. »
>
> **T26** — « Q6 Qu'est-ce qu'un onglet a le droit d'écrire ? → a) Seulement ses paramètres (KEY, MODULE, SERVICES, ses mots) et les crochets que son type déclare. Un test de tests/test_tab_registry.py refuse toute autre méthode. »
>
> **T27** — « Q7 Où vit la garde de lecture seule ? → a) Les écritures passent dans les services (SourceStore.save, CaseList.move…) et sont gardées là, une fois pour tous ; SYNC_DOMAIN devient un paramètre du stockage. »
>
> **T28** — « Q8 Que deviennent les bases actuelles ? → a) Elles deviennent des façades sur les services pendant la migration, puis disparaissent quand plus aucun onglet n'en hérite. »
>
> **T29** — « Q9 Les services ont-ils une logique sans Qt (variante H) ? → a) Oui pour la liste des cas, le brouillon et l'Affichage seulement ; les toiles et les modules restent des widgets. »
>
> **T30** — « Q10 Un seul accordéon ? → a) ModulePane remplace FoldablePane partout. »
>
> **T31** — « Q11 Comment les services disent-ils le nom des objets ? → a) Chaque service a ses mots génériques ; l'onglet fournit les phrases qui nomment son objet, en entier, comme le fait WORDS aujourd'hui. »
>
> **T32** — « Q12 Jusqu'où redécouper les onglets de dessin ? → a) Une base mince DrawTab ; chaque toile reste un service entier, sans la redécouper dans cette refonte. »
>
> **T33** — « Q13 Dans quelle issue le moteur des couches ? → a) #95 fixe son contrat (le modèle de couches sans Qt, NEEDS = ("layers",)) et Poids propre passe sur CalcTab avec son image actuelle ; le moteur s'écrit dans une issue à part. »
>
> **T34** — « Q14 Où se montre le dessin des couches ? → a) Un module du volet de droite, comme la figure de la Neige, agrandissable en fenêtre ⧉. »
>
> **T35** — « Q15 Le rapport suit-il les couches masquées à l'écran ? → a) Non : c'est une aide à l'écran ; le rapport imprime toujours tout le complexe. »
>
> **T36** — « Q16 Le pas final vers D (un onglet = une ligne du TabSpec) ? → a) À décider plus tard, quand tous les onglets sont minces. »
>
> **T37** — « Q17 Comment publier ? → a) Une version publiée par type migré, chacune avec sa vérification indépendante. »

### Les réponses de l'ingénieur aux questions de la spec (23.10.2026)

> **T38** — (Q-001, jusqu'où va le Vent) « le vent ne sera pas construit aujourd'hui, car je l'implémenterai après l'implémentation de cette issue avec l'aide de l'artifacte que ton autre session m'a donné. À moins que cela fasse sens de d'abord implémenter maintenant le vent, puis de crééer ces briques, mais je ne le pense pas »
>
> **T39** — (Q-002, un seul accordéon) « Rien ne change (Recommandé) »

## 3. Exigences fonctionnelles

### REQ-001 — La Neige sur la base mince du type Calcul, sans changement visible
- **Exigence** : Woodcore doit construire l'onglet « Neige » sur `CalcTab` et ses services ; ce que l'ingénieur voit et fait dans l'onglet (la liste, le formulaire, les bulles, le volet de modules, « Affichage », les mots dans les trois langues, l'ordre et le pliage gardés des modules) reste ce qu'il est en v0.124 augmentée des correctifs #96/#99.
- **Source** : T22, T16
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_calc_tab_base.py`, `tests/test_snow_source.py` et les tests de fenêtre de la Neige passent sans qu'une assertion de comportement change ; l'accès aux widgets passe par l'accesseur unique `tab.service(nom)` (revue, ARCH-RISK-005) — tests adaptés : `test_calc_tab_base.py`, `test_load_tab.py`, `test_linkable_spin.py`, `test_domain_file_display.py`, `test_action_tabs.py` ; l'ordre et le pliage des modules déjà gardés sur une machine sont relus sous la même clé (`ModulePane(t, "tab_ac_snow")`, ARCH-RISK-017) ; `snow_tab.py` ne définit que des paramètres (REQ-005).

### REQ-002 — Le Vent reste tel qu'il est, prêt à être construit sur le type Calcul
- **Exigence** : Woodcore doit garder l'onglet « Vent » tel qu'en v0.124 (sur `LoadTab`, devenu façade pour lui seul) ; le guide « construire un onglet » (§11 Documentation) dit comment le Vent passera sur `CalcTab` dans son issue, ce qu'il devra fournir (`declaration`, `visible_fields`, `messages`, `results`) et ce que le type lui donnera.
- **Source** : T38, T22 (corrigé par T38), T16
- **Priorité** : doit
- **Critère d'acceptation** : `WindTab` et ses tests (`tests/test_wind_source.py`, `tests/test_load_tab.py`) passent sans changement de comportement ; le guide de `docs/ui/window.md` nomme le Vent comme prochain onglet du type Calcul, avec la liste de ce que son domaine doit fournir.

### REQ-003 — Le Poids propre sur le type Calcul, avec son tableau de couches et son image actuelle
- **Exigence** : Woodcore doit construire « Poids propre et surcharge » sur `CalcTab`, le formulaire déclaré remplacé par le service `LayerTable` (le tableau des couches actuel) ; la carte des matériaux du projet devient le service `ProjectMaterials` ; le dessin du complexe reste l'image actuelle (`dead_load_svg`), montré comme un module du volet de droite agrandissable en fenêtre ⧉ ; l'état du calcul et les résultats sont des modules. Son domaine gagne ce que le type demande (revue, ARCH-RISK-007) : `messages(src)` (ce que disent aujourd'hui `layer_rows` et `warnings`), `results(instance)`, `figure_svg(src)` tiré de `layers(src)` (une seule fois par frappe : pas de second rendu à côté de `build_instance`), `layers(src, here)` (ARCH-007). Le préfixe des mots est un paramètre de l'onglet, pas une `declaration()` vide. Le module « Résultats » rend, en plus des valeurs de `results`, les tables de l'instance (`instance["tables"]`) — un rendu générique écrit une fois, que le Vent reprendra.
- **Source** : T18, T33, T34, T21 ; revue (ARCH-RISK-007)
- **Priorité** : doit
- **Critère d'acceptation** : `DeadLoadTab` hérite de `CalcTab` et déclare `LayerTable` à la place du formulaire ; le module « Résultats » montre le tableau des couches que l'onglet montre en v0.124 ; le module du dessin se déplace, se plie et s'ouvre en fenêtre comme la figure de la Neige ; un cas existant s'ouvre, s'enregistre et s'exporte comme en v0.124 (`tests/test_dead_load*.py`, `tests/test_load_tab.py`) ; `tests/test_domain_contracts.py` tient `dead_load_source` à `messages`, `results`, `figure_svg`, `layers`.

### REQ-004 — Ajouter un onglet de calcul = une classe mince et des fonctions de domaine
- **Exigence** : Woodcore doit permettre d'ajouter un onglet de calcul en écrivant seulement son `TabSpec`, une classe mince qui nomme son domaine, ses mots et, s'il en diffère, ses services, et les fonctions de son domaine — sans écrire de widget.
- **Source** : T12, T15, T6
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_calc_tab_base.py` monte un `CalcTab` sur le domaine inventé (`tests/fake_domain.py`) par une classe qui ne contient que des paramètres, et y trouve chaque service du type.

### REQ-005 — Plus aucune méthode de base redéfinie dans un onglet du type Calcul
- **Exigence** : Woodcore doit refuser, par un test, qu'une classe d'onglet bâtie sur un type définisse autre chose que ses paramètres (`KEY`, `MODULE`, `SERVICES`, `ID_PREFIX`, ses mots…) et les crochets que son type déclare (`HOOKS`).
- **Source** : T26, T7, T13, T15
- **Priorité** : doit
- **Critère d'acceptation** : la règle vit dans `tests/test_tab_overrides.py`, étendu (revue, ARCH-RISK-012 : pas de second mécanisme à côté de `PERMITTED`) : il parcourt toutes les classes d'onglet dont un ancêtre est un type et échoue en nommant la classe et le nom pour toute méthode **ou attribut de classe** hors paramètres déclarés et `HOOKS` (une `lambda` assignée ne passe pas) ; `HOOKS` de `CalcTab` est vide au départ ; il passe pour Neige et Poids propre ; un onglet de test qui redéfinit `confirm_leave` le fait échouer ; `_tab_classes` s'arrête au type comme il s'arrête aujourd'hui à `SourceEditorTab`.

### REQ-006 — Un service se refuse sur un domaine qui ne lui fournit pas ce qu'il demande
- **Exigence** : Woodcore doit, à la construction d'un onglet, vérifier que son domaine fournit chaque fonction que ses services demandent (`NEEDS`) et, sinon, s'arrêter en nommant l'onglet, le service et la fonction manquante (« un fichier malformé arrête »).
- **Source** : T12 ; inféré de CLAUDE.md (« A missing input warns, a malformed file stops ») et de T33 (`NEEDS = ("layers",)`)
- **Priorité** : doit
- **Critère d'acceptation** : un test monte `Chart` sur un domaine sans `chart()` et reçoit une erreur qui nomme `Chart` et `chart` ; aucun onglet réel ne la déclenche (`tests/test_tab_registry.py`).

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Le Poids propre prend l'aspect du type Calcul
- **Exigence** : le volet de droite du Poids propre devient le volet de modules (déplacer, plier, ⧉, ordre gardé par onglet sur cette machine) ; « Affichage » montre le fichier du cas ligne par ligne comme pour la Neige.
- **Source** : T21, T34, T11
- **Langues** : fr / de / en — les mots génériques des services existent dans les trois ; les phrases qui nomment l'objet de l'onglet aussi (T31).
- **Critère d'acceptation** : capture de l'onglet dans ses deux vues jointe à la vérification ; `tests/test_i18n.py` passe.

### UI-002 — Le rapport n'est pas touché
- **Exigence** : aucun document compilé ne change : le rapport imprime ce que l'export contient, et le complexe de couches toujours en entier (T35).
- **Source** : T35 ; inféré (cette issue est une refonte de la fenêtre)
- **Langues** : —
- **Critère d'acceptation** : `tests/projet-exemple/` compile avant et après ; les fichiers `data/` exportés et les fichiers de domaine écrits pour les cas de neige et de poids propre sont identiques octet pour octet, pour un cas que l'ingénieur n'a pas modifié à la main dans son fichier `.typ` (un fichier modifié à la main est réécrit, D-21).

## 5. Exigences d'architecture

### ARCH-001 — Un service par fonctionnalité, avec un contrat
- **Exigence** : chaque fonctionnalité visible du type Calcul est un service : une classe Python simple (ni `ABC`, ni base commune avec `QWidget` : ARCH-RISK-016) qui déclare sa zone (`ZONE` : gauche, centre, droite, barre), les vues où elle se montre (`IN_VIEWS`, pour ne pas se confondre avec le `VIEWS` de l'onglet que lit `views.declared` : ARCH-RISK-004), ce qu'elle demande au domaine (`NEEDS`), ses écrivains (`WRITERS`), dont les mots sont au niveau de son module (`STRINGS`, ARCH-010), qui rend son widget par `mount(ctx)` et garde son état de session par `state()` / `restore(state)` (le `view_state` d'un onglet reconstruit ; `layout_store` ne garde que l'ordre et le pliage des modules, sous la clé de l'onglet : ARCH-RISK-017). **Services montés du type Calcul** (revue, ARCH-RISK-020) : la liste des cas (`CaseList`), l'identité (`Identity`), le formulaire déclaré (`DeclaredForm`) ou le tableau de couches (`LayerTable`), les matériaux du projet (`ProjectMaterials`), le volet de modules (`Modules`, un seul service qui reçoit ses `ModuleSpec` : état du calcul, résultats avec tables, figure, graphique, extraits), les bulles de la norme (`Bubbles`) et « Affichage » (`DomainDisplay`). **Objets sans Qt que le contexte possède**, qui ne sont pas des services montés : le stockage des sources (`SourceStore`), la logique de la liste (`case_list_logic`) et celle du brouillon (`draft_logic`).
- **Source** : T2, T4, T11, T15 ; revue (ARCH-RISK-016, -017, -020)
- **Critère d'acceptation** : chaque service a un test qui le monte seul sur un faux contexte (`tests/test_tab_services.py`, nouveau, une ligne dans `docs/conventions/testing-catalogue*.md`).

### ARCH-002 — Un contexte par onglet, et aucun service n'appelle un autre service
- **Exigence** : un `TabContext` (un `QObject`) par onglet porte le domaine, le cas tel qu'enregistré, l'id courant, le projet, la langue, l'état `loading`, le `SourceStore` et la logique de la liste et du brouillon ; un service ne connaît que le contexte. Le contexte offre trois choses, et rien d'autre ne relie deux services (revue, ARCH-RISK-002, -003, -006, -015) :
  - **le brouillon par contributions** : chaque service de la zone centre déclare `fill(src)` et `collect(src)` ; `ctx.fill(src)` et `ctx.draft()` les appellent dans un ordre fixe (identité, formulaire ou tableau, liens), sans nommer un service ;
  - **des phases ordonnées** pour les enchaînements critiques, menées par `TabHost` dans un ordre écrit : `shown`, `case_loaded`, `saved`, `before_display` (qui fait enregistrer le cas avant d'afficher son fichier) ; les signaux Qt (champ changé, vue changée, langue changée, champ à mettre en évidence) ne servent qu'aux notifications dont l'ordre ne compte pas ; `loading` est testé par l'émetteur (`ctx.touch`), jamais par chaque abonné ;
  - **des capacités partagées sans zone** : les liens d'un nombre vers une variable de l'export (`ctx.link_spin(...)`, sur `linkable_spin` et `links`, refus des boucles compris), collectés par `ctx.draft()`.
- **Source** : T25 ; revue (ARCH-RISK-002, -003, -006, -015)
- **Critère d'acceptation** : un test lit les imports des modules de services et n'y trouve aucun autre module de service ; aucun service ne tient un autre service ; sur `fake_domain`, le cycle nouveau → saisie → enregistrer → autre cas compte un `refresh` par changement et le point « non enregistré » ne bouge pas pendant `ctx.fill`.

### ARCH-003 — Des bases minces par type ; le type Calcul écrit, les quatre autres décrits
- **Exigence** : `TabHost(QWidget)` monte les services d'une classe dans ses zones, réutilise `display_view.ViewPanes` pour les vues (pas un second mécanisme zone × vue : revue §2), vérifie les `NEEDS` (REQ-006), fournit `splitter` (la liste en `widget(0)`, pour `fold_left_pane`), le raccourci Ctrl+S par onglet, et porte l'interface fixe que la fenêtre appelle (ARCH-009) ; `CalcTab` **est** un `TabHost` (une classe, pas un niveau de plus : ARCH-RISK-020) avec ses `SERVICES` par défaut et ses `HOOKS` ; une vérification sera `CalcTab` avec une carte Position et un Verdict. Dessin, Éditeur, Données et Document sont décrits dans la documentation (leurs services par défaut, la toile restant un service entier pour Dessin) et écrits dans leurs propres issues.
- **Source** : T10, T24, T32, T21 ; revue
- **Critère d'acceptation** : `CalcTab(TabHost)` existe ; `docs/ui/window.md` décrit les cinq types et leurs services par défaut.

### ARCH-004 — La garde de lecture seule dans les services
- **Exigence** : les écritures passent par les services et le stockage (`SourceStore.save`, `SourceStore.delete`, `CaseList.move`, les écritures d'« Affichage »…) ; `tab_guard` les garde **par classe de service, d'après son `WRITERS`**, là où elles sont définies, une fois (les onglets non migrés gardent la liste globale par nom) ; `_app_of` trouve l'application par `holder.ctx.app` ; `source_archive.Actions` travaille sur le contexte et non plus sur `tab.list`, `tab.current_id`, `tab.dirty` ; `SYNC_DOMAIN` devient le paramètre `sync_domain` de `SourceStore`, lu par la garde ; un enregistrement suit l'ordre écrit `écrire → export → unfold → sync`, une seule fois (revue, ARCH-RISK-001, -014).
- **Source** : T27, T7 ; revue (ARCH-RISK-001 bloquant, -014)
- **Critère d'acceptation** : `test_every_writer_a_tab_reaches_is_guarded_where_it_is_defined_and_once` couvre les services ; un test **négatif** monte un service écrivain sur une fenêtre factice en lecture seule : l'écriture renvoie `False` et n'écrit rien, et le test échoue si `_app_of` rend `None` ; dans un projet ouvert en lecture seule, « Enregistrer » de la Neige, du Poids propre et (par sa façade) du Vent est refusé ; après un enregistrement, le fichier de domaine est resynchronisé une fois ; `test_the_tabs_that_make_domains_say_so_on_their_class` lit le paramètre du stockage pour les onglets sur un type.

### ARCH-005 — Une logique sans Qt pour la liste, le brouillon et « Affichage »
- **Exigence** : `CaseList`, `Draft` et `DomainDisplay` ont chacun une partie sans Qt (l'état et les règles : dossiers, ordre, marqueur « non enregistré », prochain id libre, question avant de quitter ; les lignes du fichier et leurs niveaux) et un widget qui affiche cet état et ne décide rien ; les toiles et les modules restent des widgets.
- **Source** : T29, T20
- **Critère d'acceptation** : les modules de logique n'importent pas PySide6 (test) ; leurs règles sont testées sans `QApplication`.

### ARCH-006 — Les bases actuelles deviennent des façades, puis disparaissent
- **Exigence** : `SourceEditorTab` délègue **à la logique sans Qt** extraite (`case_list_logic`, `draft_logic`, `source_store`), et non aux services widgets, pour la trentaine d'onglets qui n'ont pas encore migré (éditeurs, dessins, vérifications) : même résultat (« aucune règle écrite deux fois ») sans toucher leurs widgets (revue, ARCH-RISK-010) ; `LoadTab` garde le strict nécessaire au Vent, son ancien cadre de résultats, de figure et de rafraîchissement supprimé avec la migration du Poids propre (ARCH-RISK-019), et disparaît avec l'issue du Vent ; `DeclaredTabMixin` (et son crochet `custom_field`, jamais utilisé) est supprimé ; `MemberCheckTab` reste jusqu'à l'issue des vérifications.
- **Source** : T28, T38 ; revue (ARCH-RISK-010, -019)
- **Précisé à l'implémentation** : `LoadTab` garde son cadre de résultats (`results_label`, ses tables), que le Vent lit encore ; seuls la carte de figure et le `sketch`, qui ne servaient qu'au Poids propre et à l'ancienne Neige, partent avec lui.
- **Critère d'acceptation** : `DeclaredTabMixin` n'existe plus ; seul `WindTab` hérite de `LoadTab` ; aucun comportement de liste n'est écrit deux fois (une seule implémentation du marqueur, de la question avant de quitter, du rechargement de la liste, entre `SourceEditorTab`, `LoadTab` et `CaseList`).

### ARCH-007 — Le contrat du modèle de couches
- **Exigence** : `calc/domains/contracts.py` définit `Layer` avec ce que le dessin lit aujourd'hui (revue, ARCH-RISK-008) : un `id` stable, `kind`, l'épaisseur, la largeur et l'entraxe en mm, `beside`, `label`, `ebene` ; ni hachure (la couleur vient aujourd'hui du rang et du mot-clé isolation ; une hachure viendra avec le moteur, D-14) ni visibilité (un état d'écran, D-16) ; `dead_load_source.layers(src, here)` le fournit sans Qt, résout les matériaux (bibliothèque et projet) et refuse un matériau absent en nommant `layers[i]` comme `layer_rows` ; `dead_load_svg` dessine à partir de `layers(...)` ; un futur service de dessin des couches le demandera par `NEEDS = ("layers",)`.
- **Source** : T33, T35, T18 ; revue (ARCH-RISK-008)
- **Critère d'acceptation** : `tests/test_domain_contracts.py` tient `dead_load_source` au contrat `layers` ; le SVG de `render(layers(...))` est identique octet pour octet à celui de `render(layer_rows(...))` pour les cas de `tests/projet-exemple/`.

### ARCH-008 — Les mots des services
- **Exigence** : chaque service a ses mots génériques dans les trois langues, dans un `STRINGS` **au niveau de son module** (pas un attribut de classe, que la fusion ne verrait pas), préfixés par service ; `woodcore_gui_words.py` les fusionne en bouclant sur le registre des services ; l'onglet fournit les phrases entières qui nomment son objet (« Nouveau cas de neige »), comme `WORDS` aujourd'hui, sur `WORD_SUFFIXES` (revue, ARCH-RISK-013).
- **Source** : T31 ; revue (ARCH-RISK-013)
- **Critère d'acceptation** : `tests/test_i18n.py` passe, compte les mots des services et refuse une clé partagée par deux modules de services (`test_the_words_of_a_calculation_tab_take_no_key_of_another_module` étendu au registre).

### ARCH-009 — L'interface fixe que la fenêtre appelle sur un onglet
- **Exigence** : `TabHost` porte, une fois, ce que la fenêtre et ses voisins appellent sur un onglet (`TAB_API`), puisqu'un onglet sur un type ne définit plus de méthode : `view` et `view_state`, `set_view`, `splitter`, `display` (`snapshot`, `restore`), `dirty`, `current_id`, `save` (avec `quiet`, lu par `autosave`), `confirm_leave` (onglets `MODE_BOUND`), `on_shown`, `update_list_marker`, `lists_object`, `open_object`, `GRAPH_KIND`, `flush_pending`, et l'accesseur `service(nom)`.
- **Source** : revue (ARCH-RISK-004)
- **Critère d'acceptation** : un test de `tests/test_tab_registry.py` vérifie `TAB_API` sur `TabHost` et l'étend à `test_every_tab_class_keeps_its_view_through_a_rebuild`.

### ARCH-010 — Le type Calcul remplace la décision D-25
- **Exigence** : la décision écrite dans `docs/decisions.md` dit qu'elle **remplace** D-25 (« no third base beside LoadTab and MemberCheckTab, which will mix the base in ») : le type Calcul est `CalcTab`, et les vérifications de membres restent sur `SourceEditorTab` jusqu'à leur issue, où elles passeront sur `CalcTab` ; `docs/ui/calc-tab.md`, `docs/ui/tab-snow.md` et `docs/open-questions.md` ne promettent plus que les vérifications « mixeront `DeclaredTabMixin` ».
- **Source** : revue (ARCH-RISK-011)
- **Critère d'acceptation** : `docs/decisions.md` et `docs/decisions-index.md` marquent D-25 remplacée ; `test_every_editor_tab_has_the_one_structure_of_its_kind` accepte `CalcTab` comme structure de son genre.

## 6. Contraintes

- **CON-001** — Aucune ligne de code de cette issue avant que la session « Charge de neige dysfonctionnelle » (issues #96 et #99) ait commité : elle modifie `calc_tab.py`, `calc_fields.py`, `module_pane.py`, `norm_bubble.py`, `layout_store.py`, `domain_file_display.py`, `norm_reader.py`, `contracts.py`, `unfold.py`, `snow_source.py`. Source : T23.
- **CON-002** — Une version publiée par type migré, chacune avec sa vérification indépendante : pour cette issue, une version pour les services et la Neige, puis une pour le Poids propre. Source : T37, T22, T38.
- **CON-003** — *(inféré)* Les fichiers sources des cas (`Woodcore-Datei/loads/<kind>/<id>.json`) et leurs schémas ne changent pas ; un projet de v0.124 s'ouvre sans migration. Source : principes 8 et 10 (`docs/architecture/principles.md`).
- **CON-004** — *(inféré)* Plusieurs sessions modifient le dépôt : jamais `git checkout --`, `stash`, `reset`, `clean`. Source : CLAUDE.md.
- **CON-005** — *(inféré)* La fenêtre construit tous les onglets à son ouverture : le temps d'ouverture est mesuré avant et après et rapporté ; une hausse visible est un défaut à corriger. Source : `docs/ui/window.md` (`live`, review A10).
- **CON-006** — *(inféré)* Le calcul reste dans `calc/domains/`, sans Qt ; un service affiche et appelle, il ne calcule pas. Source : CLAUDE.md, principes.

## 7. Décisions prises

- **D-01** — Variante F : des services composés, assemblés par des bases minces par type ; le choix B du 19.10.2026 (Q-001 de `2026-10-19-base-saine-nettoyage`) est gardé comme forme (une base par famille) et change de contenu (des services, et non plus des méthodes héritées). Raison : B répondait à « la même liste copiée sept fois » ; #95 demande qu'un onglet *choisisse* ses fonctionnalités, ce qui est une composition. Prix : la forme de `SourceEditorTab` (v0.120) est redécoupée ; `tab_guard` est réécrit pour les services ; deux styles cohabitent jusqu'à la fin de la migration. (T17, T19, artefact §9)
- **D-02** — Périmètre : les services communs et le type Calcul, avec la Neige et le Poids propre ; le Vent juste après, dans son issue, construit sur le type ; vérifications, éditeurs, données, documents et dessins chacun dans une issue suivante. (T21, T38)
- **D-03** — Ordre : la Neige d'abord, sans changement visible, puis le Poids propre. Le Vent n'est pas construit avant les services : le construire d'abord sur l'ancienne base obligerait à le migrer deux fois. (T22, T38)
- **D-04** — La spec s'écrit maintenant ; l'implémentation attend le commit de #96/#99. (T23)
- **D-05** — Cinq types : Calcul, Dessin, Éditeur, Données, Document ; une vérification est un Calcul avec une carte Position et un Verdict. Un type est une recette par défaut, il n'enferme pas un onglet (le Poids propre est un calcul qui dessine). (T24, T18)
- **D-06** — Un `TabContext` par onglet, avec des signaux Qt ; un service n'appelle jamais un autre service. (T25)
- **D-07** — Un onglet n'écrit que ses paramètres et les crochets de son type ; un test refuse le reste. (T26)
- **D-08** — Les écritures et leur garde vivent dans les services ; `SYNC_DOMAIN` est un paramètre du stockage. (T27)
- **D-09** — Les bases actuelles deviennent des façades, puis disparaissent. (T28)
- **D-10** — Une logique sans Qt pour la liste des cas, le brouillon et « Affichage » ; pas pour les toiles ni les modules. Ce n'est pas une duplication : la logique décide, le widget affiche. (T29, T20)
- **D-11** — Un seul accordéon, `ModulePane`, volet de droite du type Calcul et des types qui le prendront ; `chrome.FoldablePane`, le repli du volet de gauche (issue #10), reste un service de la fenêtre, inchangé. La réponse à Q10 reposait sur une erreur de l'artefact, corrigée par Q-002. (T30, T39)
- **D-12** — Chaque service a ses mots génériques ; l'onglet fournit les phrases entières qui nomment son objet. (T31)
- **D-13** — Le type Dessin aura une base mince `DrawTab`, chaque toile restant un service entier. (T32)
- **D-14** — Cette issue fixe le contrat du modèle de couches et fait passer le Poids propre avec son image actuelle ; le moteur de dessin des couches s'écrit dans une issue à part. (T33, T18)
- **D-15** — Le dessin des couches est un module du volet de droite, agrandissable en fenêtre ⧉. (T34)
- **D-16** — Masquer une couche est une aide à l'écran : le rapport imprime toujours tout le complexe, et la visibilité n'est pas une donnée du cas. (T35)
- **D-17** — Le pas vers la variante D (un onglet = une ligne du `TabSpec`) sera décidé quand tous les onglets seront minces. (T36)
- **D-18** — Une version publiée par type migré, chacune vérifiée indépendamment. (T37)
- **D-19** — Règle de conception : une fonctionnalité **visible** qui pourrait servir à un deuxième onglet est un service, même si un seul onglet l'utilise aujourd'hui ; un morceau d'état (le stockage, la logique de la liste ou du brouillon) est un objet sans Qt du contexte, pas un service monté. (T18, artefact §10 ; resserrée par la revue, ARCH-RISK-020)
- **D-20** — Les réserves de la revue d'architecture sont reprises dans les exigences (§3–§5) : la garde par classe de service, le brouillon par contributions, les phases ordonnées, les liens comme capacité du contexte, l'interface fixe de `TabHost`, sept services montés au lieu de onze, `SourceEditorTab` qui ne délègue qu'à la logique sans Qt, D-25 remplacée. La règle « un service n'appelle jamais un autre service » (D-06) est gardée : ces liaisons passent toutes par le contexte. (revue §13)
- **D-22** — Trois écarts de la version 1 acceptés par l'ingénieur (23.10.2026, « J'accepte les trois écarts ») : `source_archive.Actions` travaille par le service de liste, dont l'état est celui du contexte (ARCH-004) ; UI-002 est prouvé par le périmètre du diff, le code d'export, de compilation et `lib/` n'étant pas touché ; un module de mots par type (`calc_tab_words`, `ct_`) plutôt qu'un par service (ARCH-008).
- **D-21** — Le fichier `.typ` d'un cas de poids propre suit son cas sans demander, comme celui de la Neige : `dead-load` entre dans `unfold.AUTO_REGENERATE`. Précisé à l'implémentation (la règle de #96/#99, `unfold.status`) : une valeur changée met à jour les lignes en place, une retouche à la main d'une ligne est gardée ; quand la forme du calcul change (une valeur choisie à côté de la somme, une variable de plus), le fichier est réécrit dans la nouvelle forme à l'enregistrement ou à l'export, et ce qui y avait été retouché à la main disparaît. C'est la règle de tout le type Calcul. Prix : une retouche à la main ne survit pas à un changement de forme. (Q-003, ARCH-RISK-009)

## 8. Hors périmètre

- Le Vent sur le type Calcul (sa déclaration, ses résultats, ses extraits de SIA 261) : l'issue qui suit celle-ci, que l'ingénieur mène avec son propre artefact (T38).
- Les types Dessin, Éditeur, Données et Document écrits en code, et la migration de leurs onglets (Plan, Plan feu, Schémas, Statique ; Formules, Journal, Positions, Annexes, Python, Profils ; Variables, Métrés, Dépendances, Commandes ; Projet, Structure) : une issue par type (D-02).
- Les vérifications de membres bois, acier et feu sur le type Calcul (`MemberCheckTab`, `SteelCheckTab`, `FireCheckTab`) : leur propre issue (D-02).
- Le moteur de dessin des couches lui-même (`BuildUpView`) : son issue (D-14).
- Les onglets réservés (Charges utiles, Séisme, Combinaisons, Torsion, États de service) : ils deviendront des onglets de calcul quand leur domaine existera.
- Le passage à la variante D (D-17).
- Tout changement des documents compilés (UI-002).

## 9. Idées non retenues comme exigences

- T3 — « le système de PDF qui s'ouvre en l'onglet moteur de dessin » : un service du type Dessin (documents importés), pour l'issue de ce type.
- La variante D (un onglet = une ligne du `TabSpec`), E (onglets en JSON), G (stratégies au lieu de redéfinitions) de l'artefact : écartées ou reportées (D-01, D-17).
- Les usages futurs du moteur des couches : la rigidité d'une paroi calculée sur son complexe (`docs/open-questions.md`, issue #54, Lignatec 32/2020), la vérification au feu d'un complexe, une vérification thermique ou acoustique (artefact §10).
- Des services réutilisés hors des onglets (liste des projets récents, dialogues, page d'accueil) : possible, non demandé.
- T5 — l'artefact de réflexion lui-même : fait (https://claude.ai/artifact/Y4pdcDgf73qKdmHVdsJvyi).

## 10. Questions

### Q-001 — Le Vent : formulaire déclaré par son domaine dans cette issue, ou formulaire actuel gardé ?
- **Pourquoi elle compte** : « le Vent construit directement dessus » (T22) peut vouloir dire deux choses. Le Vent n'a pas encore de `declaration()`, `visible_fields()` ni `results()` (`calc/domains/wind_source.py`) ; le déclarer, c'est écrire le choix parmi les ~50 tables de l'Annexe C (`select`), `z` « = h », des résultats en tableaux, et les extraits de SIA 261 chapitre 6 sous chaque ⓘ (pages et cadres relevés dans `norm-library/`, mots tenus au PDF par un test). Cela double à peu près le travail de l'issue et la fait passer d'une refonte de la fenêtre à un travail de domaine et de norme.
- **Options** : A (recommandée) le Vent déclaré par son domaine (champs, messages, résultats, « Affichage »), ses extraits de la norme sous les ⓘ dans une issue suivante — l'aspect du type Calcul est atteint, le travail de norme est séparé ; B le Vent déclaré complètement, extraits compris ; C le formulaire actuel du Vent gardé tel quel comme service à lui, sur `CalcTab`, sa déclaration dans une issue à part.
- **Réponse** : aucune des trois — le Vent n'est pas construit dans cette issue ; l'ingénieur l'implémentera juste après, sur le type Calcul (T38, 23.10.2026). Construire le Vent d'abord sur l'ancienne base puis écrire les services l'obligerait à migrer deux fois : l'ordre services → Vent est retenu (D-03).

### Q-002 — Q10 corrigée : il n'y a qu'un accordéon
- **Pourquoi elle compte** : l'artefact disait « deux accordéons : `chrome.FoldablePane` et `ModulePane` ». C'est faux : `FoldablePane` est la flèche qui replie le volet de gauche d'un onglet (issue #10), déjà écrite une fois et posée par la fenêtre autour de tous les onglets (`woodcore_gui.fold_left_pane`) ; il n'empile aucun module. Le seul accordéon est `ModulePane`. La réponse « ModulePane remplace FoldablePane partout » n'a donc pas d'objet.
- **Options** : A (recommandée) `ModulePane` est le volet de droite du type Calcul (et des types qui le prendront) ; `FoldablePane` reste le repli du volet de gauche, un service de la fenêtre, inchangé ; B autre chose (à dire).
- **Réponse** : A, « Rien ne change » (T39, 23.10.2026) → D-11.

### Q-003 — Le fichier `.typ` d'un cas de poids propre suit-il son cas sans demander, comme la Neige ?
- **Pourquoi elle compte** (revue, ARCH-RISK-009) : depuis #96/#99 (D-4 de la spec `2026-10-23-neige-correctifs-issues-96-99`), le fichier d'un cas de neige est réécrit à chaque enregistrement et export dès que son formulaire a changé, sans question (`unfold.AUTO_REGENERATE = {"snow-load"}`) : c'est la règle des fichiers d'un onglet de calcul. Le Poids propre n'y est pas : un fichier qu'il a écrit et que l'ingénieur a modifié à la main garde ses lignes, et « Affichage » ligne par ligne, que le type Calcul lui donne, afficherait en rouge « ne peut pas être régénéré », sans bouton pour en sortir.
- **Options** : A (recommandée) le Poids propre suit la règle du type : `dead-load` entre dans `AUTO_REGENERATE` ; une modification à la main de son fichier est écrasée au prochain enregistrement ou export, comme pour la Neige ; UI-002 vaut pour un cas non modifié à la main. B le Poids propre garde son fichier tel quel : « Affichage » ligne par ligne ne s'ouvre que tant que le fichier correspond à son cas, et dit sinon pourquoi.
- **Réponse** : A, « Suit son cas » (l'ingénieur, 23.10.2026) → D-21.

## 11. Critères d'acceptation

- [x] REQ-001 — La Neige sur `CalcTab`, les tests de la Neige inchangés et verts.
- [x] REQ-002 — Le Vent inchangé sur `LoadTab` façade ; le guide dit ce que son issue devra fournir.
- [x] REQ-003 — Le Poids propre sur `CalcTab` avec `LayerTable`, la carte des matériaux et l'image en module ⧉.
- [x] REQ-004 — Un `CalcTab` monté sur le domaine inventé par une classe de paramètres seuls.
- [x] REQ-005 — Le test qui refuse toute méthode hors `HOOKS` dans un onglet sur un type.
- [x] REQ-006 — Un service sur un domaine qui ne fournit pas son `NEEDS` arrête la construction en nommant l'onglet, le service et la fonction.
- [x] UI-001 — Poids propre avec le volet de modules et « Affichage » ligne par ligne, en trois langues.
- [x] UI-002 — Exports, fichiers de domaine et PDF du projet exemple identiques avant et après.
- [x] ARCH-001 — Chaque service testé seul sur un faux contexte (`tests/test_tab_services.py`).
- [x] ARCH-002 — Aucun service n'importe ni ne tient un autre service.
- [x] ARCH-003 — `TabHost`, `CalcTab` ; les cinq types décrits dans `docs/ui/window.md`.
- [x] ARCH-004 — Les écrivains des services gardés une fois ; lecture seule refusée ; resynchronisation après enregistrement.
- [x] ARCH-005 — Logique de la liste, du brouillon et d'« Affichage » sans PySide6, testée sans `QApplication`.
- [x] ARCH-006 — `DeclaredTabMixin` supprimé, `LoadTab` façade pour le Vent seul ; aucune règle de liste écrite deux fois.
- [x] ARCH-007 — `Layer` dans `contracts.py`, `dead_load_source.layers`, `dead_load_svg` qui le lit, image identique.
- [x] ARCH-008 — Mots des services en trois langues au niveau de leur module, fusionnés par le registre, collision refusée.
- [x] ARCH-009 — `TAB_API` sur `TabHost`, vérifiée par un test.
- [x] ARCH-010 — D-25 marquée remplacée ; docs qui la promettaient corrigées.
- [x] CON-002 — Deux versions publiées (services + Neige, puis Poids propre), chacune vérifiée.
- [x] CON-005 — Temps d'ouverture de la fenêtre mesuré avant et après, rapporté.
- [x] Documentation : `docs/ui/window.md` « Ajouter un onglet » devient le guide de construction par type et par services avec un exemple complet ; `docs/ui/calc-tab.md` devient la page du type Calcul ; `docs/ui/tab-snow.md` et la page du Poids propre à jour ; `docs/architecture/layout.md` (les nouveaux modules) ; la décision dans `docs/decisions.md` (§13) et `docs/decisions-index.md` ; entrée `CHANGELOG.md` ; page « Nouveautés » fr/de/en de chaque version.
- [x] Tests : `tests/test_tab_services.py` (nouveau, sa ligne au catalogue), `tests/test_tab_registry.py` et `tests/test_calc_tab_base.py` étendus, `tests/test_domain_contracts.py` (`layers`), suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1 | contexte |
| T2 | ARCH-001 | capturé |
| T3 | §9 ; ARCH-001 (accordéon = `ModulePane`, Affichage = `DomainDisplay`) | capturé en partie ; PDF → type Dessin (§8) |
| T4 | ARCH-001, D-19 | capturé |
| T5 | §9 | fait (artefact) |
| T6 | REQ-004 | capturé |
| T7 | REQ-005, ARCH-004 | capturé |
| T8 | ARCH-003 | capturé |
| T9 | D-01 | décision |
| T10 | ARCH-003, D-05 | capturé |
| T11 | ARCH-001, UI-001 | capturé ; vues Dessin, Import, Export et lien de carte → types suivants (§8) |
| T12 | REQ-004, REQ-006 | capturé |
| T13 | REQ-005, ARCH-006, CON-002 | capturé |
| T14 | §11 Documentation | capturé |
| T15 | REQ-004, REQ-005, ARCH-001 | capturé |
| T16 | REQ-001, REQ-002 | capturé |
| T17 | D-01 | décision |
| T18 | REQ-003, ARCH-007, D-05, D-19 | capturé |
| T19 | §10 | fait (questions de l'artefact) |
| T20 | ARCH-005, D-10 | capturé |
| T21 | D-02, §8 | décision |
| T22 | REQ-001, D-03 ; Q-001 | décision ; le Vent → question, tranchée par T38 |
| T23 | CON-001, D-04 | contrainte |
| T24 | ARCH-003, D-05 | décision |
| T25 | ARCH-002, D-06 | décision |
| T26 | REQ-005, D-07 | décision |
| T27 | ARCH-004, D-08 | décision |
| T28 | ARCH-006, D-09 | décision |
| T29 | ARCH-005, D-10 | décision |
| T30 | Q-002, D-11 | prémisse fausse → question, tranchée par T39 |
| T31 | ARCH-008, D-12 | décision |
| T32 | ARCH-003, D-13 | décision |
| T33 | REQ-003, ARCH-007, D-14 | décision |
| T34 | REQ-003, UI-001, D-15 | décision |
| T35 | UI-002, ARCH-007, D-16 | décision |
| T36 | D-17, §8 | décision |
| T37 | CON-002, D-18 | décision |
| T38 | REQ-002, D-02, D-03, §8, Q-001 | décision |
| T39 | D-11, Q-002 | décision |

### Points de la source non résolus

Aucun.

## 13. Revue d'architecture

Revue du 23.10.2026 par l'agent `architecture-reviewer`, sur le code tel qu'il est ce jour-là ; les fichiers de #96/#99 (`calc_tab.py`, `calc_fields.py`, `domain_file_display.py`, `contracts.py`, `unfold.py`, `norm_bubble.py`) étaient modifiés et non commités : leurs numéros de ligne sont à relire après leur commit (CON-001).

### Modules concernés

- **Registre et garde** : `tab_registry.py` (`SPECS`, listes dérivées ; `GUARDED_TABS` ne retient une classe que si un nom de `WRITERS` est dans `dir(cls)`) ; `tab_guard.py` (`WRITERS` par nom, `_app_of` par `holder.app` ou `holder.tab.app`, `_makes_domains` lit `type(tab).SYNC_DOMAIN`, `guard` parcourt le MRO, `guard_actions`).
- **Base des éditeurs** : `source_editor.py` `SourceEditorTab` (état, transitions `new`/`duplicate`/`revert`/`delete`/`load`, liste, `confirm_leave`, Ctrl+S) ; `source_archive.py` `Actions` (lit et écrit `tab.list`, `tab.current_id`, `tab.dirty`).
- **Type Calcul actuel** : `load_tab.py` `LoadTab` (construction, liens vers une variable, formulaire, ancien cadre de résultats et de figure, `save`, `view_state`) ; `DeadLoadTab` (tableau de couches, carte des matériaux, mots `ld_*`, sans `DeclaredTabMixin`) ; `WindTab` ; `calc_tab.py` `DeclaredTabMixin` et ses corps de modules, qui lisent tous `tab.*` ; `calc_fields.py` `FieldWidget` (appelle `tab.bubbles`, `tab.touch`, `tab.linked`…) ; `module_pane.py` (`ModuleSpec`, état par `layout_store.get_state/put_state(tab_key)`) ; `domain_file_display.py` (lit `tab.current_id`, appelle `tab.write_*`).
- **Fenêtre** : `display_view.py` (`ViewPanes`, `DisplayTab`) ; `views.py` (`declared(tab)` lit `tab.VIEWS`) ; `woodcore_gui.py` (construit les 39 onglets, `fold_left_pane`, `refresh_tab`, `apply_views`/`reset_view`, `rebuild`, `confirm_leave` des `MODE_BOUND`, `on_shown`) ; `autosave.py` (lit `current_id`, `dirty`, `save(quiet)`, appelle `update_list_marker`) ; `woodcore_gui_menus.py` (lit `tab.dirty`).
- **Domaines** : `contracts.py` `CalcTabDomain` ; `dead_load_source.py` (`layer_rows` résout les matériaux et lève, `build_instance` rend déjà le SVG) ; `dead_load_svg.py` (`render` lit épaisseur, largeur, entraxe, `beside`, `label`, `ebene` ; pas de hachure) ; `unfold.py` (`GENERATORS` contient déjà `dead-load` ; `AUTO_REGENERATE = {"snow-load"}`).
- **Tests qui lisent la forme actuelle** : `test_tab_overrides.py` (`PERMITTED`), `test_tab_registry.py`, `test_calc_tab_base.py` (`FakeTab(DeclaredTabMixin, LoadTab)`), `test_load_tab.py` (`tab.table`, `tab.fields`, `tab.pane.modules`…), `test_i18n.py` (fusion des mots par regex).

### Code existant à réutiliser

- Un tiers de `SourceEditorTab` est déjà sans Qt (`next_free_id`, `NEW_ROW`, `make_source`/`duplicate_id`, `_group_of`, `listed`, `draft_group`, `take_group`, l'écriture du groupe de `on_moved`, la table de décision de `on_list_change`) ; `source_archive` est déjà un module de fonctions ; la validation et l'écriture de `LoadTab.save` sont sans Qt : `SourceStore.save` en sort directement.
- `DeclaredTabMixin` se découpe sans reste : `build_inputs`/`update_rows`/`focus_field` → `DeclaredForm` ; `build_result` et les corps de modules → `Modules` (déjà décrits par `ModuleSpec`) ; épingles et lecteur → `Bubbles` ; `install_display`/`prepare_display`/`write_*` → `DomainDisplay` ; `export_sources` → `SourceStore`.
- `display_view.ViewPanes` fait déjà « zone × vue » ; `autosave.confirm` reste la seule file de questions ; `linkable_spin` et `links` pour les liens.
- `layout_store` ne garde que l'ordre et le pliage des modules ; l'état d'un onglet reconstruit est `view_state`, en mémoire : deux persistances distinctes.

### Risques

| Risque | Gravité | Ce qui est fait |
|---|---|---|
| ARCH-RISK-001 — la garde de lecture seule échoue ouverte pour un service (`_app_of` rend `None`, `GUARDED_TABS` ignore une classe sans écrivain, `Actions` lit `tab.*`) | bloquant | ARCH-004 amendée : garde par classe de service, `ctx.app`, `Actions` sur le contexte, test négatif |
| ARCH-RISK-002 — personne ne rassemble le brouillon (identité, formulaire, liens) sans qu'un service en appelle un autre | bloquant | ARCH-002 amendée : `fill`/`collect`, ordre fixe, mené par le contexte |
| ARCH-RISK-003 — ordre des signaux et ré-entrance (`refresh` avant le `fill` complet, boucle brouillon → marqueur) | important | ARCH-002 : phases ordonnées, `loading` testé par l'émetteur, test du cycle |
| ARCH-RISK-004 — l'interface que la fenêtre appelle sur un onglet n'est pas listée ; `VIEWS` en double sens | important | ARCH-009 (`TAB_API`) ; `IN_VIEWS` pour les services (ARCH-001) |
| ARCH-RISK-005 — le critère de REQ-001 était faux : les tests lisent `tab.fields`, `tab.pane`… | important | REQ-001 amendée : `tab.service(nom)`, tests à adapter listés |
| ARCH-RISK-006 — les liens vers une variable ne sont dans aucun service | important | ARCH-002 : capacité du contexte `ctx.link_spin` |
| ARCH-RISK-007 — le domaine du Poids propre n'a ni `messages`, ni `results`, ni `figure_svg` ; ses résultats en tables seraient perdus | important | REQ-003 amendée : quatre fonctions, rendu générique des tables |
| ARCH-RISK-008 — `Layer` ne couvrait pas ce que `dead_load_svg` lit ; la hachure n'existe pas | important | ARCH-007 amendée |
| ARCH-RISK-009 — « Affichage » ligne par ligne du Poids propre et `AUTO_REGENERATE` | important | Q-003, posée à l'approbation |
| ARCH-RISK-010 — `SourceEditorTab` en façade de services widgets toucherait 30 onglets | important | ARCH-006 amendée : délégation à la logique sans Qt seulement |
| ARCH-RISK-011 — `CalcTab` contredit D-25 et deux tests | important | ARCH-010 |
| ARCH-RISK-012 — REQ-005 doublait `test_tab_overrides.py` | important | REQ-005 amendée |
| ARCH-RISK-013 — des `STRINGS` de classe échapperaient à la fusion et au garde-fou des collisions | important | ARCH-008 amendée |
| ARCH-RISK-014 — `SYNC_DOMAIN` déplacé, ordre `écrire → export → unfold → sync` | important | ARCH-004 amendée |
| ARCH-RISK-015 — `prepare_display` fait enregistrer le cas, un appel entre services | important | phase `before_display` (ARCH-002) |
| ARCH-RISK-016 — métaclasse de `QWidget` : pas d'`ABC`, pas de base `Service` commune avec un widget | mineur | ARCH-001 ; `mount(ctx)` rend un widget |
| ARCH-RISK-017 — garder la clé de `ModulePane` de la Neige ; ne pas généraliser `layout_store` | mineur | REQ-001, ARCH-001 |
| ARCH-RISK-018 — temps d'ouverture | mineur | CON-005, mesurer aussi `refresh_tab` |
| ARCH-RISK-019 — code mort de `LoadTab` et `custom_field` | mineur | ARCH-006 amendée |
| ARCH-RISK-020 — trop d'abstraction (onze services, trois niveaux de base) | important | ARCH-001/-003 resserrées : sept services montés, `CalcTab` est un `TabHost`, D-19 précisée |
| ARCH-RISK-021 — dépendance de forme envers #96/#99 | mineur | CON-001 ; étape 0 du plan |
| ARCH-RISK-022 — où vivent la barre « Enregistrer / Annuler » et Ctrl+S | mineur | `TabHost` (ARCH-003) ; la barre est dans la zone barre |

### Approche recommandée

Fichiers à plat dans `calc/tools/` comme le reste (un paquet casserait la convention d'import et `packaging/`) : `tab_host.py` (`TabContext`, `TabHost`, la forme d'un service), `calc_tab.py` (devient `CalcTab`, renommé après le commit de #96/#99), `case_list.py` et `case_list_logic.py`, `draft_logic.py`, `source_store.py`, `calc_modules.py` (les corps d'état, de résultats avec tables, de figure, de graphique), `layer_table.py`, `project_materials.py`, `domain_display.py` (renommage de `domain_file_display.py`) et `domain_display_logic.py` ; les mots dans des `*_words.py` fusionnés par le registre des services. Chaque commit garde la suite verte (§14).

### Verdict

**APPROUVER AVEC RÉSERVES** — l'idée est cohérente avec les principes (une source de vérité, la logique hors de l'interface, la garde une seule fois) et prolonge `SourceEditorTab` et `ModulePane`. Réserves : les deux bloquants (garde des services, brouillon par contributions) et les points importants ci-dessus, tous repris dans les exigences (D-20) sauf ARCH-RISK-009, posée en Q-003. Rien ne contredit une décision réglée sauf D-25, remplacée explicitement (ARCH-010).

## 14. Plan d'implémentation

Chaque étape laisse la suite verte et finit par un commit ; aucune ne commence avant l'étape 0.

0. **Attendre et relire** (CON-001, ARCH-RISK-021) — après le commit de #96/#99 : relire `calc_tab.py`, `calc_fields.py` (signature de `FieldWidget`), `norm_bubble.py` (`BubbleController`), `domain_file_display.py`, `contracts.py` (`Field`), `unfold.py` (`AUTO_REGENERATE`) ; corriger les numéros de ligne de §13 et ajuster les noms de §14 si leur forme a changé. Mesurer le temps d'ouverture de la fenêtre et de `refresh_tab` (référence de CON-005). Prouvé par : la suite complète verte au point de départ.
1. **La logique sans Qt** (ARCH-005, ARCH-006) — extraire `case_list_logic.py`, `draft_logic.py`, `source_store.py` (lecture, validation, écriture, puis `export → unfold → sync` dans cet ordre, paramètre `sync_domain`) de `source_editor.py` et `load_tab.py` ; `SourceEditorTab` et `LoadTab` leur délèguent ; aucun comportement ne change. Prouvé par : `tests/test_tab_services.py` (nouveau) pour les règles sans `QApplication` et sans PySide6 importé ; `test_tab_overrides.py` et toute la suite inchangés.
2. **La garde des services** (ARCH-004) — `tab_guard` : garde par classe d'après `WRITERS`, `_app_of` par `ctx.app`, `_makes_domains` par `sync_domain` du stockage ; `source_archive.Actions` sur un contexte. Aucune classe d'onglet ne change encore. Prouvé par : le test négatif de lecture seule, `test_every_writer_…` étendu.
3. **Le contexte et l'hôte** (ARCH-002, ARCH-003, ARCH-009, REQ-006) — `tab_host.py` : `TabContext` (cas, id courant, `loading`, stockage, logique, `fill`/`collect`, phases `shown`/`case_loaded`/`saved`/`before_display`, `link_spin`, `service(nom)`), `TabHost` (zones par `ViewPanes`, `splitter`, Ctrl+S, `TAB_API`, vérification des `NEEDS`). Testés sur `fake_domain` seul. Prouvé par : `TAB_API`, `NEEDS` manquant nommé, cycle nouveau → saisie → enregistrer → autre cas avec compteur de `refresh`.
4. **Les services du type Calcul** (ARCH-001, ARCH-008, REQ-004) — `CaseList`, `Identity`, `DeclaredForm`, `Modules` (avec `calc_modules.py` et le rendu générique des tables), `Bubbles`, `DomainDisplay` (+ `domain_display_logic.py`), chacun extrait de `DeclaredTabMixin`/`calc_fields`/`domain_file_display` et testé seul ; `CalcTab(TabHost)` monté sur `fake_domain` par une classe de paramètres seuls ; mots au niveau des modules, fusionnés par le registre. La Neige reste encore sur `DeclaredTabMixin`. Prouvé par : `test_tab_services.py`, `test_calc_tab_base.py` étendu, `test_i18n.py`.
5. **La Neige sur `CalcTab` — version 1** (REQ-001, REQ-005, ARCH-010, CON-002) — `SnowTab(CalcTab)`, paramètres seuls ; suppression de `DeclaredTabMixin` et de `custom_field` ; `test_tab_overrides.py`, `test_tab_registry.py` adaptés ; accès des tests par `tab.service(...)` ; décision qui remplace D-25 ; doc de la Neige. Prouvé par : tests de la Neige au comportement inchangé, clé de `ModulePane` gardée, exports identiques, mesure CON-005 ; vérification indépendante, puis `finish`.
6. **Le domaine du Poids propre** (ARCH-007, REQ-003 côté domaine, Q-003) — `Layer` dans `contracts.py`, `dead_load_source.layers`, `messages`, `results`, `figure_svg` ; `dead_load_svg` sur `layers` ; `dead-load` dans `AUTO_REGENERATE` (D-21), avec un test d'un fichier modifié à la main qui est réécrit. Aucun changement dans la fenêtre. Prouvé par : SVG identique octet pour octet, `test_domain_contracts.py`, exports et fichiers de domaine identiques.
7. **Le Poids propre sur `CalcTab` — version 2** (REQ-003, UI-001, ARCH-006, CON-002) — `DeadLoadTab(CalcTab)` avec `LayerTable` et `ProjectMaterials` ; le dessin en module ⧉ ; suppression de l'ancien cadre de `LoadTab` (gardé le strict nécessaire au Vent, REQ-002). Prouvé par : `test_load_tab.py` adapté, tables dans « Résultats », captures des deux vues, Vent inchangé ; vérification indépendante, puis `finish`.
8. **La documentation** (§11) — au fil des étapes 5 et 7, pour la version qu'elles publient : `docs/ui/window.md` (guide « construire un onglet » par type et services, exemple complet, les cinq types, ce que le Vent devra fournir), `docs/ui/calc-tab.md` (page du type Calcul), `docs/ui/tab-snow.md`, la page du Poids propre, `docs/architecture/layout.md`, `docs/decisions.md` + index, `docs/open-questions.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en ; ligne de `tests/test_tab_services.py` au catalogue.

## 15. Vérification

### Version 1 (services + Neige) — tour 1, 23.10.2026 (agent `requirements-verifier`, sur l'arbre non commité contre 0c8a935)

Tous les tests demandés verts (test_tab_services 9, test_calc_tab_base 14, test_load_tab 7, test_tab_registry 8, test_tab_overrides 4, test_domain_file_display 10, test_linkable_spin 11, test_i18n 23, test_docs_coherence 7, test_views 11, test_window 9 ; et test_wind_source 11, test_action_tabs 4, test_snow_source 21). Hors de cette version : REQ-003, UI-001, ARCH-007, la partie de ARCH-006 qui rogne `LoadTab`, la seconde version de CON-002.

| Élément | Tour 1 | Correction faite après le tour 1 |
|---|---|---|
| REQ-001, REQ-002, REQ-004, REQ-005, ARCH-002, ARCH-003, ARCH-010, CON-001, CON-003, CON-004, CON-006 | ✅ | — |
| REQ-006 | ⚠️ pas de test « aucun onglet réel ne la déclenche » ; le critère nomme `Chart`/`chart()` | `test_no_tab_built_on_a_type_lacks_what_its_services_need` (`tests/test_tab_registry.py`). Écart d'énoncé assumé : les modules sont un seul service (`Modules`, ARCH-RISK-020), le test le monte sur un domaine sans `results()`. |
| UI-002 | ⚠️ aucune preuve octet pour octet | Le code de l'export, de la compilation et `lib/` n'est pas dans le diff (`git diff --stat HEAD -- calc/*.py calc/domains calc/norms calc/i18n lib schemas templates` : seulement `contracts.FIELD_KINDS` et `unfold_display.case_file`, tous deux de la fenêtre) ; la source d'un cas est écrite par le même `engine.write_json` (`source_store.write`), ses champs tenus par `test_load_tab`. |
| ARCH-001 | ⚠️ pas de test de chaque service seul | `test_each_service_mounts_alone_on_a_context_of_its_own` : `Identity`, `DeclaredForm`, `Modules`, `Bubbles`, `DomainDisplay`, `CaseList` montés chacun sur un contexte dont l'hôte ne tient que lui. |
| ARCH-004 | ⚠️ pas de test « Enregistrer » de la Neige en lecture seule ni de resynchronisation unique ; `Actions` pas « sur le contexte » | `test_the_snow_s_save_is_refused_read_only_and_followed_by_the_domains_files_once` (`tests/test_load_tab.py`) ; `test_the_store_of_a_tab_on_a_type_says_its_domains_follow`. `source_archive.Actions` reçoit pour porteur le service de liste, dont `list`, `current_id` et `dirty` sont ceux du contexte : réalisé par équivalence, sans réécrire `Actions` que trente onglets partagent. |
| ARCH-005 | ⚠️ pas de partie sans Qt pour « Affichage » | Les règles d'« Affichage » sont `calc/domains/unfold_display.py` (sans Qt : `elements`, `set_display`, `set_domain_level`, `set_figure`) ; la seule restée dans le widget, le fichier du cas, y passe (`case_file`) ; `test_the_file_affichage_shows_is_found_without_qt`. |
| ARCH-006 | ⚠️ `custom_field` subsiste ; commentaires périmés | Le genre `custom` et son crochet retirés (`contracts.FIELD_KINDS`, `calc_fields.py`, `calc_form.py`) ; `load_tab.py` et `tab_guard.py` réécrits. |
| ARCH-008 | ❌ pas de registre des mots des services | `Service.WORDS_MODULE`, `woodcore_gui_words.SERVICE_WORDS` (le registre fusionné), `test_every_service_names_its_words_module_and_the_window_merges_it`, `test_the_words_of_a_calculation_tab_take_no_key_of_another_module` étendu au registre. Écart assumé : un module de mots pour l'ensemble des services de « Calcul » (`calc_tab_words`, `ct_`), et non un par service — leurs mots existaient déjà là, et les découper n'aurait rien changé à l'écran. |
| ARCH-009 | ⚠️ test de reconstruction non étendu | `test_every_tab_class_keeps_its_view_through_a_rebuild` vérifie, pour un onglet sur un type, que les appels de la fenêtre sont ceux de l'hôte. |
| CON-005 | ⚠️ pas de mesure | Mesuré (§16, CHANGELOG) : fenêtre 9,0 s avant, 7,6 s après (médianes de cinq) ; onglet Neige 188 ms avant, 186 ms après. |
| Documentation | ⚠️ « Nouveautés » 0.125 contre « v0.126 » | Le numéro est celui de l'installateur à venir : 0.125 n'est pas publié, son entrée reste v0.125 comme les commits de #96/#99 ; « v0.126 » renommé dans la doc. |
| Phases (remarque) | noms `computed`, `saved`, `before_display`, `hidden` au lieu de `shown`, `case_loaded` | Écart assumé, dit dans `docs/ui/building-a-tab.md`. |

### Version 1 — tour 2, 23.10.2026

Tous verts : test_tab_services 13, test_tab_registry 9, test_tab_overrides 4, test_load_tab 8 (9 après le test du Vent), test_calc_tab_base 14, test_i18n 23, test_domain_file_display 10, test_snow_source 21, test_docs_coherence 7, test_domain_contracts 10, test_startup et test_startup_imports (`--perf`) 3. ✅ : REQ-006, ARCH-001, ARCH-005, ARCH-009, CON-005, CHANGELOG et numéro de version, `building-a-tab.md`, catalogue, D-25 remplacée.

| Élément | Tour 2 | Suite |
|---|---|---|
| ARCH-006 | ⚠️ `custom` encore cité dans `layout.md` et `calc-tab.md` | corrigé après le tour 2 → ✅ |
| ARCH-004 | ⚠️ `Actions` par équivalence, pas « sur le contexte » ; pas de test du Vent en lecture seule | test ajouté (`test_the_wind_s_save_on_its_former_frame_is_refused_read_only`) ; l'équivalence d'`Actions` reste un écart au texte, soumis à l'ingénieur |
| UI-002 | ⚠️ preuve par le périmètre du diff, pas de comparaison octet pour octet | soumis à l'ingénieur : le code d'export, de compilation et `lib/` n'est pas touché ; la source est assemblée dans le même ordre (identité, champs, liens) et écrite par le même `engine.write_json` |
| ARCH-008 | ⚠️ un module de mots pour les services de « Calcul » (`calc_tab_words`), pas un par service | soumis à l'ingénieur |

Deux tours faits : ce qui reste est l'acceptation par l'ingénieur de trois écarts déclarés (ARCH-004 `Actions`, UI-002 preuve par périmètre, ARCH-008 un module de mots par type) — acceptés (D-22).

### Version 2 (Poids propre) — tour 1, 23.10.2026 (agent `requirements-verifier`, sur l'arbre non commité contre 65f63ad)

Tous verts : test_load_tab 10, test_dead_load_source 12, test_dead_load 22 (+1 ignoré), test_figure_golden 1, test_domain_contracts 11, test_linkable_spin 11, test_tab_registry 9, test_tab_overrides 4, test_tab_services 13, test_i18n 23, test_wind_source 11, test_unfold 23, test_docs_coherence 7, test_no_duplicates 1. ✅ : REQ-003 (les quatre parties), ARCH-001 (`LayerTable`, `ProjectMaterials`, writer gardé), ARCH-006 (seul `WindTab` sur `LoadTab`), ARCH-007 (le vérificateur a aussi comparé l'ancien `dead_load_svg` tiré de HEAD au nouveau : identiques), D-15, D-16, D-21 (`AUTO_REGENERATE`), REQ-002, REQ-005, UI-002, CON-002, CON-003, la documentation.

| Élément | Tour 1 | Correction faite |
|---|---|---|
| ARCH-001 | ⚠️ `LayerTable` et `ProjectMaterials` non montés seuls | ajoutés à `test_each_service_mounts_alone_on_a_context_of_its_own` |
| D-21 | ⚠️ pas de test d'un fichier retouché à la main | `test_the_permanent_load_s_file_follows_its_case_without_a_question` : une valeur changée met à jour en place et garde la retouche ; une forme changée (valeur choisie) réécrit le fichier et la retouche disparaît. La règle réelle (celle de #96/#99) est plus étroite que ce que D-21, le CHANGELOG et « Nouveautés » disaient : textes corrigés. |
| UI-001 | ⚠️ captures partielles, bandeau sur « Calculation » | refaites plus larges, la vue changée par la fenêtre (`on_view_chosen`) : bandeau « Display », tableau entier. Restent dans la carte d'« Affichage » deux artefacts de `DomainFileDisplay` (un trait sous le chemin, un « Copy » égaré), classe que cette issue ne change pas. |
| ARCH-006 | ⚠️ `LoadTab` garde son cadre de résultats | précisé dans l'exigence : le Vent le lit encore |
| `docs/decisions.md` | ⚠️ `DeclaredTabMixin.prepare_display` cité | remplacé par la phase `before_display` | Écart assumé, dit dans `docs/ui/building-a-tab.md` : `on_shown` et le chargement d'un cas passent par l'hôte, qui appelle `fill` puis la phase `computed`. |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-23 | draft | spécification extraite de l'issue #95, des messages de l'ingénieur et de ses 17 réponses ; Q-001 (étendue du Vent) ouverte, Q-002 (prémisse de Q10) proposée |
| 2026-10-23 | specified | Q-001 : le Vent sort de l'issue, construit juste après sur le type Calcul (T38) ; Q-002 : un seul accordéon, rien ne change (T39) ; plus aucun point non résolu |
| 2026-10-23 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (2 bloquants, 13 importants) ; réserves reprises dans REQ-001/-003/-005, UI-002, ARCH-001 à -010 (D-20) ; Q-003 (`AUTO_REGENERATE` du Poids propre) ouverte pour l'approbation ; plan §14 en 9 étapes |
| 2026-10-23 | approved | approuvée par l'ingénieur (« Approuver et implémenter ») ; Q-003 → A, D-21 ; l'implémentation attend le commit de #96/#99 (CON-001, étape 0) |
| 2026-10-23 | implementation | étape 0 : #96/#99 commité (0c8a935), fichiers relus — `calc_tab.py` porte `Section` (accordéon), `_ResultsBody` par ligne, `hover_*`, `prepare_display` qui enregistre ; `layout_store` fusionne `sections` ; `AUTO_REGENERATE` |
| 2026-10-23 | implementation | étape 1 : `case_list_logic.py`, `draft_logic.py`, `source_store.py`, `field_links.py` ; `SourceEditorTab` et `LoadTab` leur délèguent (ARCH-005, ARCH-006) ; tests liés verts |
| 2026-10-23 | implementation | étape 2 : `tab_guard.guard_service`, `_app_of` par `ctx.app`, `_makes_domains` lit `sync_domain` du stockage ; `tab_registry.GUARDED_SERVICES` (ARCH-004) |
| 2026-10-23 | implementation | étapes 3-4 : `tab_host.py` (`TabContext`, `Service`, `TabHost`, `TAB_API`, `PARAMS`, vérification des `NEEDS`), services `case_list.py` (`CaseList`, `Identity`), `calc_bubbles.py`, `calc_form.py`, `calc_modules.py` (tables génériques), `calc_display.py` ; `calc_tab.CalcTab` (ARCH-001 à -003, -009, REQ-004, REQ-006) ; `DomainFileDisplay.path` sans dossier de domaine → pas de fichier |
| 2026-10-23 | implementation | étape 5 : `SnowTab(CalcTab)`, paramètres seuls ; `DeclaredTabMixin` supprimé ; tests adaptés par `tab.service(nom)` (test_load_tab, test_calc_tab_base, test_domain_file_display, test_linkable_spin), `test_tab_overrides` (REQ-005), `test_tab_registry` (ARCH-004, -009, -010), `tests/test_tab_services.py` nouveau |
| 2026-10-23 | testing | doc de la version 1 (`docs/ui/building-a-tab.md` nouveau, calc-tab, window, tab-snow, layout, decisions + index, open-questions, CHANGELOG, « Nouveautés » 0.125 fr/de/en, catalogue des tests, README) ; CON-005 mesuré (fenêtre 9,0 → 7,6 s, onglet Neige 188 → 186 ms, médianes) |
| 2026-10-23 | verification | tour 1 de la version 1 : 1 ❌ (ARCH-008), 9 ⚠️ ; corrections faites (§15) ; tour 2 à suivre |
| 2026-10-23 | verification | tour 2 de la version 1 : aucun test rouge, 4 ⚠️ dont 2 corrigés (ARCH-006 doc, test du Vent en lecture seule) ; 3 écarts soumis à l'ingénieur avant le commit de la version 1 ; reste ensuite la version 2 (étapes 6-7, Poids propre) |
| 2026-10-23 | implementation | version 1 : écarts acceptés (D-22) ; suite complète 3096 passés, 10 ignorés, 1 échec réparé (`on_shown` écrit deux fois → `draft_logic.shown` ; la liste des doublons mise à jour, `profile_tab.revert` n'étant plus un doublon) ; commit 65f63ad poussé, issue #95 commentée (ouverte) |
| 2026-10-23 | implementation | étape 6 : `contracts.Layer`, `dead_load_source.layers`/`layers_of`/`figure_svg`/`messages`/`results`, `dead_load_svg` sur le modèle ; dessin identique octet pour octet (trois compositions comparées avant/après, empreinte de `test_figure_golden` inchangée) ; `dead-load` dans `AUTO_REGENERATE` (D-21) |
| 2026-10-23 | implementation | étape 7 : `dead_load_tab.DeadLoadTab(CalcTab)`, services `layer_table.LayerTable` et `project_materials.ProjectMaterials` ; signal `projectDataChanged` ; `load_tab.py` ne garde que le Vent (carte de figure et `sketch` retirés) ; `ld_figure` → `ld_module_drawing` ; tests adaptés et étendus (D-21, ⧉, tableau dans « Résultats ») ; captures des deux vues (UI-001) ; doc de la version 2 |
| 2026-10-23 | completed | version 2 : tour 1 de vérification, 5 ⚠️ corrigés (§15) ; suite complète 3099 passés, 10 ignorés, en 17 min ; spécification déplacée dans `completed/` |
