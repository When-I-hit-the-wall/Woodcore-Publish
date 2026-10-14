---
id: 2026-10-08-onglet-formule-domaines
titre: Nouvel onglet « Formule » (domaines de calcul écrits par blocs de commandes) ; retrait des onglets RFEM et Formules
status: completed
cree: 2026-10-08
mis_a_jour: 2026-10-08
source: transcription dictée
docs: [docs/typst/formulas.md, docs/ui/window.md, docs/domain/rfem.md, docs/domain/member-checks.md, docs/domain/documents.md, docs/architecture/layout.md, docs/architecture/principles.md]
---

# Onglet « Formule » et retrait de RFEM / Formules — Spécification

## 1. Objectif

Retirer définitivement de Woodcore les onglets *RFEM* et *Formules* (lignes à mots-clés), en gardant leur code dans un dossier d'archive. Les remplacer, dans le groupe *Référence*, par un onglet *Formule* d'un tout autre comportement : écrire un calcul sous forme de **blocs de commandes** remplis par formulaire (`domaine`, `var`, `eq`, `val`, `verify`…), validés au clavier, affichés sous leur forme lisible, et qui deviennent des commandes Typst. Tout calcul appartient désormais à un **domaine** (`#var-domain`), qu'on peut rappeler ailleurs dans le rapport.

## 2. Source

> **T1** — « Tu peux supprimer les onglets. RFEM. Ainsi que formule. Mets-les dans un dossier archive, mais retire définitivement le code de Woodcore. Je ne les utiliserai plus, mais laisse-les dans les archives au cas où on en a besoin. »
>
> **T2** — « Il faut un nouveau onglet en référence qui s'appelle formule. C'est donc un tout autre comportement que l'onglet que tu vas supprimer. »
>
> **T3** — « Son, sa fonction est de pouvoir écrire des calculs de manière simplifiée et que ça en fasse des commandes TYPST. »
>
> **T4** — « Dans le volet de gauche, On doit pouvoir naviguer entre les différents domaines de calcul et également ouvrir les domaines de calcul qui sont présents dans Tips. Les deux doivent être synchronisés. »
>
> **T5** — « Je veux maintenant qu'à chaque fois qu'il y ait des calculs, ils soient compris dans un domaine afin de pouvoir appeler ces domaines à d'autres endroits du rapport. »
>
> **T6** — « Dans le volet de droite, lorsque rien n'est sélectionné, l'on peut choisir les commandes que l'on décide d'utiliser. Ce sont toutes les commandes nécessaires pour un calcul ou pour un affichage de calcul. Donc j'imagine par exemple les commandes VAR, EQ, VAL, VERIFY. »
>
> **T7** — « Dans le volet de gauche, il est possible de créer de nouveaux domaines de calcul. » — *corrigé par T10.*
>
> **T8** — « Lorsque l'on sélectionne un domaine de calcul, enfin, lorsque l'on crée un nouveau domaine de calcul, dans le volet central, il doit y avoir une ligne en haut. mi-sélectionnable, mi-écriture, qui affiche le nom du domaine. Et dans le volet droit, on doit avoir accès aux différentes options TYPST pour ce domaine. »
>
> **T9** — « Ensuite, lorsque l'on fait un à la ligne, ou lorsque l'on quitte la ligne du domaine dessous, Eh bien, dans le volet de droite, on doit avoir accès aux différentes commandes que l'on peut ajouter. »
>
> **T10** — « Et d'ailleurs, la, la commande domaine est en fait dans le volet de droite et pas dans le volet de gauche. Je me suis trompé. Le volet de gauche permet uniquement de naviguer entre les différents domaines, de les ouvrir et de les fermer. »
>
> **T11** — « Et lorsqu'on les ouvre, on voit ce qu'il contient, donc euh, les différentes équations variables qu'il contient. »
>
> **T12** — « Lorsque je clique dans le volet de droite sur la commande VAR, dans le volet central, il y a des textes suivis de text box pour ce que je peux remplir comme variable. Donc par exemple, il y a la variable de calcul, la variable affichée. la valeur et l'unité. »
>
> **T13** — « Et dans le volet de droite, il y a toutes les autres options disponibles pour Tips. »
>
> **T14** — « Avec des tas, en appuyant sur la touche Tab, je peux naviguer d'une textbox à l'autre, et en appuyant sur Enter, je peux valider la commande. »
>
> **T15** — « Lorsqu'une commande est validée, Elle s'affiche ensuite sous forme visuelle de ce qui est le plus nécessaire. Donc, par exemple, dans une commande VAR, on aura uniquement affiché la variable, le nom affiché, la valeur et l'unité. »
>
> **T16** — « Il faut double-cliquer dessus pour re-rentrer dans le mode édition de la commande. »
>
> **T17** — « Lorsque je rentre uniquement la variable, le nom de la variable affichée et non pas le nom de la variable pour utiliser pour les calculs, eh bien, une variable de calcul doit, un nom de variable de calcul doit être généré automatiquement à partir du nom affiché. »
>
> **T18** — « Lorsque je crée une équation, Le bloc de commande éditable qui est affiché dans le volet central doit être variable est égal calcul. Dans variable, je peux mettre le nom de la variable affichée. Et ensuite, avec tab, je passe dans la partie calcul. »
>
> **T19** — « Et lorsque je suis là-dedans, je peux cliquer dans le volet de gauche en haut des variables qui sont déjà enregistrées pour ce domaine. Et ça écrira dans l'équation uniquement La, le, le nom de variable affiché pour cette variable enregistrée. »
>
> **T20** — « Je dois également pouvoir calculer avec des nombres et non pas que des variables. Donc, dans le bloc de commande équation, je dois pouvoir mettre par exemple M. Ensuite, il y a le égal, donc je clique sur table pour passer dans le calcul. Mais là, je dois pouvoir écrire 12 newtons divisé par 3 mètres. Et ces unités doivent être reconnues. Je devrais aussi pouvoir écrire un millimètre au lieu de mètre. Ça devrait être converti. »
>
> **T21** — « Dans le volet de droite également, alors je suis dans la commande, dans le bloc de commande EQ, je dois pouvoir choisir l'unité de sortie. Donc, par exemple, choisir si ce sont des kilonewtons ou des newtons, ou si ce sont des kilonewtons par mètre, ou des newtons par millimètre, ou que sais-je. »
>
> **T22** — « Également, lorsque je suis dans le bloc de commande, pardon, pardon, lorsque je suis dans le bloc de commande EQ et que j'ai tout écrit, ce qui était nécessaire, quand je clique sur Enter, il n'est affiché à l'écran sur deux lignes. que la formule avec les lettres, les variables, et dessous la formule avec les chiffres. »
>
> **T23** — « Dans le volet de droite, je dois donc voir tout, en tout temps, à droite en haut, le, les, toutes les variables qui sont enregistrées dans le domaine. »
>
> **T24** — « Lorsqu'une équation est créée, eh bien, il y a une variable. qui est également » — *phrase interrompue.*
>
> **T25** — « Et ensuite, ça c'est le mode calcul, donc tout en haut, il y aura le mode calcul ou le mode affichage, »
>
> **T26** — « et dans le mode affichage, il faut pouvoir copier les commandes pour TYPST. Pour, un, pour, pour tout un bloc de calcul avec un niveau pour le bloc de calcul. »
>
> **T27** — « Le niveau 1 cache les var (var level 0), le niveau 2 affiche tout au niveau 1 et le niveau 3 affiche tout au niveau 3. »

## 3. Exigences fonctionnelles

### REQ-001 — Retrait de l'onglet RFEM et de ce que lui seul sert
- **Exigence** : Woodcore ne doit plus contenir l'onglet *RFEM* ni le code que lui seul utilise ; ce code est déplacé, intact, dans le dossier d'archive (REQ-003). L'étendue exacte (onglet seul, ou aussi la lecture des exports `calc/rfem_import/`, `calc/domains/rfem.py`, `lib/rfem.typ`, les schémas `rfem*.schema.json`, la commande CLI `rfem-import`, les modèles statiques générés depuis RFEM) est fixée par **Q-001**.
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : `TABS` et `NAV_GROUPS` (`calc/tools/woodcore_gui.py`) ne nomment plus `tab_rfem` ; un test balaie `calc/`, `lib/`, `schemas/`, `packaging/`, `templates/` à la recherche de `rfem_import|rfem_tab|dsl_tab|rfem\.typ|rfem-|rfem_models|rfem_export` et ne trouve rien hors de la liste d'exceptions (RFEM nommé comme programme tiers : annexes, historique) — revue §13 ; la suite de tests passe.

### REQ-002 — Retrait de l'onglet Formules (lignes à mots-clés)
- **Exigence** : Woodcore ne doit plus contenir l'onglet *Formules* de v0.100 (`calc/tools/dsl_tab.py`) ni sa grammaire (`calc/dsl.py`), déplacés dans l'archive. Les commandes `#member` et `#verify-*` de `lib/timber.typ` restent (écrites à la main et utilisées par les vérifications enregistrées).
- **Source** : T1, T2
- **Priorité** : doit
- **Critère d'acceptation** : `dsl.py` et `dsl_tab.py` absents de `calc/` ; clés `dsl_*` retirées des chaînes ; `tests/test_dsl.py` archivé ; `tests/test_timber.py` passe inchangé.

### REQ-003 — Le dossier d'archive
- **Exigence** : le code retiré doit être conservé dans un dossier d'archive (emplacement : **Q-002**), avec un `README.md` qui dit ce qu'il contient, depuis quelle version et quel commit il a été retiré, et comment le restaurer. Le code archivé n'est ni importé, ni testé, ni empaqueté, ni publié.
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : le dossier contient les modules, leurs tests, leurs fixtures et leurs pages de documentation ; `packaging/build.py`, `tests/run_tests.py` et la collecte de pytest ne le parcourent pas (test).

### REQ-004 — Un projet qui nomme encore RFEM s'ouvre
- **Exigence** : un fichier `.woodcore` qui porte encore `rfem_models` / `rfem_export` (Musterprojekt, `tests/projet-exemple/Exemple.woodcore`) doit s'ouvrir et s'exporter sans erreur ; la clé est ignorée avec un avertissement, jamais un arrêt. (Seulement si Q-001 retire la lecture RFEM.)
- **Source** : inféré (CLAUDE.md « A missing input warns, a malformed file stops » ; Musterprojekt.woodcore l. 8 et 27)
- **Priorité** : doit
- **Critère d'acceptation** : test : ouvrir et exporter le projet d'exemple avec ses clés RFEM ; un avertissement nomme la clé ; aucun `data/rfem*.json` n'est écrit.

### REQ-005 — Un domaine porte tout calcul
- **Exigence** : dans l'onglet *Formule*, toute commande de calcul (`var`, `eq`, `verify`, `val`, `var-unit`) doit appartenir à un domaine `#var-domain("<nom>")[…]` ; on ne peut pas écrire une commande hors domaine. Le nom du domaine est celui par lequel `#val(…, domain: "<nom>")` le rappelle ailleurs dans le rapport.
- **Source** : T5
- **Priorité** : doit
- **Critère d'acceptation** : le Typst produit par un domaine est un unique `#var-domain("…")[ … ]` ; un exemple compilé rappelle une variable du domaine par `#val(…, domain:)` hors du bloc (test).

### REQ-006 — Où vivent les domaines, et la synchronisation
- **Exigence** : les domaines édités dans l'onglet et ceux présents dans les fichiers Typst du projet doivent être **les mêmes objets** : un domaine modifié dans l'onglet est réécrit dans son fichier, un domaine modifié dans VS Code est relu par l'onglet à son affichage. La source de vérité est **un fichier `.typ` par domaine** dans `<racine Typst>/Formules/<id>.typ` (D-09, D-11) ; l'onglet liste ces fichiers.
- **Source** : T4, T5 ; principe 15 (`docs/architecture/principles.md` : le `.typ` est la source de vérité, Woodcore suit ce que l'ingénieur écrit)
- **Priorité** : doit
- **Critère d'acceptation** : test aller-retour : écrire un domaine depuis le modèle, le relire → modèle identique ; modifier le fichier à la main (une valeur) → l'onglet relu la montre ; un fichier écrit à la main de forme non canonique est signalé (« écrit à la main ») et n'est réécrit qu'après avertissement, comme les objets de `typst_objects`.

### REQ-014 — La commande `#show-formula`
- **Exigence** : une nouvelle commande Typst `#show-formula("<nom>", level: auto)` doit imprimer le domaine écrit dans son fichier (D-09) en appliquant la règle des niveaux D-02 au niveau donné (ou au niveau du rapport) ; au niveau 0 elle n'imprime rien mais enregistre les variables, pour qu'un `#val(…, domain:)` placé plus loin les lise. Un nom de domaine qu'aucun fichier ne porte arrête la compilation en nommant les domaines connus (*a defect stops*). En mode *Affichage*, *Copier* donne cet appel, ou au choix le Typst développé au niveau choisi (REQ-013).
- **Source** : T5, T26, T27, Q-003
- **Priorité** : doit
- **Critère d'acceptation** : `///` complet, deux exemples qui compilent, catégorie dans `build_reference.CATEGORIES`, traduction dans `calc/i18n/commands.json` (`tests/test_commands.py`) ; test : le même domaine imprimé aux niveaux 1, 2, 3 donne les mêmes niveaux par commande que le Typst développé de REQ-013.

### REQ-015 — Importer une variable dans un domaine
- **Exigence** : depuis la liste des variables en haut à droite, une action *Importer* doit basculer dans l'onglet *Variables*, **tous les autres onglets étant indisponibles** jusqu'au choix ou à l'annulation ; la variable choisie — une valeur de l'export (une charge : `s_k` de `("snow-load", "SL")`), une variable d'un autre domaine de formules, ou d'un domaine d'un document — revient dans le domaine comme une `var` importée : `#var("<clé>", var-of(…))` pour l'export, `#var("<clé>", domain: "<domaine>")` pour un domaine nommé (`build_reference.call_var` / `call_var_registry`). Le calcul Python lit sa valeur à la source (export, domaine de formules calculé, registre du document lu par `variables.best`) ; une valeur introuvable s'affiche « — » et les équations qui en dépendent disent pourquoi elles ne sont pas calculées. L'onglet *Variables* liste aussi les domaines de formules comme une source.
- **Source** : réponse de l'ingénieur du 2026-10-08 (« dans le tableau des variables en haut à droite, il doit être possible d'importer des variables. On switch alors dans l'onglet variables avec tous les autres onglets indisponibles »)
- **Priorité** : doit
- **Critère d'acceptation** : test d'interface : *Importer* montre *Variables* en mode choix, les autres onglets désactivés ; choisir `s_k` ajoute `#var("s_k", var-of("snow-load", "SL", "s_k"))` au domaine avec sa valeur de l'export ; *Annuler* rend les onglets sans rien changer ; un cycle entre deux domaines de formules est refusé en le nommant.

### REQ-007 — Commande VAR
- **Exigence** : la commande `var` doit se remplir par quatre champs — **variable de calcul** (la clé du registre), **variable affichée** (le symbole), **valeur**, **unité** — et ses autres arguments (`label`, `descr`, `norm`, `norm-ref`, `note`, `style`, `level`, `summary`) dans le volet de droite. Elle produit `#var("<clé>", "<symbole>", <valeur>, "<unité>", …)`, en n'écrivant que ce qui diffère des valeurs par défaut de la signature (`build_reference.call_command`).
- **Source** : T12, T13
- **Priorité** : doit
- **Critère d'acceptation** : test : un modèle var rempli donne l'appel attendu ; chaque argument nommé de `var` dans `lib/formula.typ` est offert ou écarté avec sa raison (comme `display_options.DISMISSED`).

### REQ-008 — Clé de calcul générée depuis le nom affiché
- **Exigence** : si seule la variable affichée est saisie, Woodcore doit générer la clé de calcul : lettres, chiffres et `_` seulement (règle des clés, `docs/typst/formulas.md` « The names »), jamais de `-`, unique dans le domaine (suffixe `_2`, `_3` en cas de collision), et telle que `key-symbol(clé)` redonne si possible le même symbole (alors le symbole n'est pas écrit).
- **Source** : T17
- **Priorité** : doit
- **Critère d'acceptation** : tests : `M_(y,d)` → `M_y_d` ; `gamma_M` → `gamma_M` ; `σ_(m,d)` → `sigma_m_d` ; `F_Ed` puis encore `F_Ed` → `F_Ed`, `F_Ed_2` ; `l_(k,y)` → `l_k_y`.

### REQ-009 — Commande EQ
- **Exigence** : la commande `eq` doit se présenter comme `variable = calcul` : la variable (nom affiché, clé générée comme REQ-008), Tab, puis le calcul. Le calcul accepte les variables du domaine (par leur nom affiché), des nombres, et des **nombres suivis d'une unité** (`12 N / 3 m`, `12 N / 3000 mm`), qui deviennent des littéraux unités de Typst (`12 "N" / 3 "m"`). L'unité de sortie (`unit:`) se choisit dans le volet de droite parmi les unités de la dimension du résultat (kN, N ; kN/m, N/mm ; …). Une équation crée une variable du domaine.
- **Source** : T18, T20, T21, T24
- **Priorité** : doit
- **Critère d'acceptation** : tests : `M = 12 N / 3 m` donne `#eq("M", `(12 "N") / (3 "m")`)` — chaque nombre avec unité entre parenthèses, sans quoi la ligne en lettres compose 12 · (N/3) · m (D-17, revue §15) — qui compile et vaut 4 N/m ; avec `3000 mm` la même valeur ; l'unité de sortie `N/mm` produit `unit: "N/mm"` ; une unité inconnue (`12 Zork`) est refusée dans le bloc avec un message, jamais écrite ; la variable `M` apparaît dans la liste des variables du domaine.

### REQ-010 — Insérer une variable enregistrée dans le calcul
- **Exigence** : quand le curseur est dans le calcul d'un `eq` (ou dans une relation `verify`), un clic sur une variable du domaine — dans la liste en haut du volet de droite (T23) et dans l'arbre du volet de gauche (T19) — doit insérer **son nom affiché** à la position du curseur ; la clé de calcul correspondante est retrouvée à l'écriture du Typst.
- **Source** : T19, T23
- **Priorité** : doit
- **Critère d'acceptation** : test d'interface : curseur dans le calcul, clic sur `F_Ed` → le texte contient `F_Ed` à la position du curseur ; l'appel Typst écrit la clé.

### REQ-011 — Commandes VERIFY, VAL et VAR-UNIT
- **Exigence** : `verify` (une relation `a <= b` entre variables, nombres et nombres avec unité), `val` (une variable du domaine, son `type:` et ses options) et `var-unit` (une variable et sa nouvelle unité) doivent être offertes de la même façon : champs principaux au centre, autres arguments à droite, Tab / Enter. La liste exacte des commandes du volet de droite est arrêtée au §7 (D-04) après Q-004 éventuelle.
- **Source** : T6
- **Priorité** : doit
- **Critère d'acceptation** : test : chaque commande offerte produit un appel qui compile dans un domaine d'exemple.

### REQ-012 — Calcul immédiat d'une commande validée
- **Exigence** : à la validation (Enter), l'onglet doit connaître la valeur de chaque `var` et de chaque `eq` et le résultat de chaque `verify`, en tenant compte des unités et de leur conversion, pour afficher la forme visuelle (UI-005). Le calcul est fait en Python à l'instant (D-10).
- **Source** : T15, T20, T22
- **Priorité** : doit
- **Critère d'acceptation** : sur un jeu d'au moins 20 formules d'essai (unités, conversions, puissances, `sqrt`, Greek, littéraux unités), la valeur affichée par l'onglet est égale à celle du registre Typst compilé à 1e-9 près (test).

### REQ-013 — Copier un bloc de calcul avec un niveau
- **Exigence** : en mode *Affichage*, l'onglet doit copier dans le presse-papiers le Typst de **tout un domaine** à un niveau choisi 1, 2 ou 3, selon la règle : **niveau 1** → chaque `var` à `level: 0`, les autres commandes à `level: 1` ; **niveau 2** → toutes les commandes à `level: 1` ; **niveau 3** → toutes à `level: 3`. Le niveau du domaine est le **défaut général** : une commande dont l'argument `level:` est indiqué garde son niveau, au rapport comme dans la copie (D-12). *Copier* offre l'appel `#show-formula("<nom>", level: n)` (par défaut) ou le Typst développé (D-15).
- **Source** : T26, T27
- **Priorité** : doit
- **Critère d'acceptation** : test : un domaine de deux `var`, un `eq`, un `verify` et un `var` à `level: 3` explicite, copié aux niveaux 1, 2, 3, donne les trois textes attendus (le `var` explicite reste à 3), chacun compile, et la page de `#show-formula` au même niveau est identique (SVG) à celle du texte développé.

## 4. Exigences d'interface

### UI-001 — L'onglet et sa place
- **Exigence** : un onglet *Formule* (FR) / *Formel* (DE) / *Formula* (EN), dans le groupe *Référence* à la place de l'ancien *Formules* (avant *Variables*), avec les trois volets habituels : navigation à gauche, édition au centre, options à droite.
- **Source** : T2
- **Langues** : fr / de / en
- **Critère d'acceptation** : `NAV_GROUPS["nav_reference"]` = (onglet formule, `tab_variables`, `tab_commands`) ; `tests/test_chrome.py` passe ; le titre existe dans les trois langues.

### UI-002 — Volet de gauche : naviguer, ouvrir, fermer
- **Exigence** : le volet de gauche liste les domaines du projet ; un domaine s'ouvre (son contenu s'affiche au centre) et se ferme ; déplié dans l'arbre, il montre ses variables et ses équations. Il ne crée **pas** de domaine (la commande domaine est à droite).
- **Source** : T4, T10, T11 (T7 corrigé par T10)
- **Langues** : fr / de / en
- **Critère d'acceptation** : test d'interface : l'arbre du projet d'exemple montre ses domaines et, sous chacun, ses variables et équations ; aucune action « nouveau domaine » dans le volet de gauche.

### UI-003 — Volet de droite selon la sélection
- **Exigence** : rien de sélectionné → la palette des commandes (dont *Domaine*) ; la ligne du domaine active → les options Typst du domaine ; après Enter ou flèche bas depuis la ligne du domaine → la palette des commandes ajoutables ; une commande en édition → ses arguments autres que ceux du centre. **En haut du volet, en tout temps**, la liste des variables du domaine ouvert (nom affiché, valeur, unité).
- **Source** : T6, T8, T9, T10, T13, T23
- **Langues** : fr / de / en
- **Critère d'acceptation** : test d'interface sur chacun des quatre états ; la liste des variables est visible dans chacun.

### UI-004 — Ligne du domaine
- **Exigence** : au centre, en haut, une ligne qui affiche le nom du domaine, **éditable** (renommer) et **sélectionnable** (la sélectionner donne ses options à droite). Créer un domaine (commande *Domaine* de la palette) place le curseur dans cette ligne.
- **Source** : T8
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : créer un domaine → la ligne a le focus ; renommer → l'arbre de gauche et le Typst suivent ; un nom déjà pris est refusé avec un message.

### UI-005 — Bloc de commande : édition au clavier, forme visuelle, double-clic
- **Exigence** : un bloc en édition montre des libellés suivis de champs ; **Tab** passe au champ suivant (Maj+Tab au précédent), **Enter** valide. Validé, le bloc s'affiche sous sa forme lisible : `var` → nom affiché = valeur unité ; `eq` → **deux lignes**, la formule en lettres puis la formule en chiffres (avec le résultat) ; `verify` → la relation et ✔/✘ ; `val` → la valeur. Un **double-clic** rouvre l'édition. Les symboles s'affichent en mathématiques (`richtext.MathDelegate` ou équivalent).
- **Source** : T14, T15, T16, T22
- **Langues** : fr / de / en (libellés des champs)
- **Critère d'acceptation** : test d'interface : Tab parcourt les champs dans l'ordre ; Enter valide et remplace l'éditeur par la forme lisible ; double-clic la rouvre ; une commande invalide (clé en double, unité inconnue, variable absente du domaine) ne se valide pas et dit pourquoi.

### UI-006 — Mode calcul / mode affichage
- **Exigence** : en haut, *Calcul · Affichage* — le commutateur de vues existant (`views.py`, `VIEWS`), comme Traction et Compression. *Calcul* est l'édition décrite ci-dessus ; *Affichage* montre la page que le domaine imprime au niveau choisi (snippet compilé, `PdfPane.request_snippet`), le choix du niveau 1/2/3 et **Copier** (REQ-013). Aucun code Typst n'est montré à l'écran (principe 15) : il est copié.
- **Source** : T25, T26
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : la vue *Affichage* demande un snippet contenant le domaine au niveau choisi ; *Copier* met dans le presse-papiers le texte de REQ-013.

### UI-007 — Le mode choix de l'onglet Variables
- **Exigence** : ouvert depuis l'onglet *Formule*, l'onglet *Variables* montre un bandeau « Choisir une variable à importer dans <domaine> » avec *Importer* et *Annuler* ; la navigation latérale et les autres onglets sont indisponibles (grisés) jusqu'à la fin ; Échap annule.
- **Source** : réponse de l'ingénieur du 2026-10-08
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : pendant le choix, la navigation latérale et les raccourcis Ctrl+1 … Ctrl+9 sont désactivés — la barre d'onglets étant cachée, c'est par eux seuls qu'on change d'onglet — et *Variables* est devant ; après *Importer* ou *Annuler*, l'onglet *Formule* revient au premier plan et tout est réactivé.

## 5. Exigences d'architecture

### ARCH-001 — Le modèle et la génération hors de l'interface
- **Exigence** : le modèle d'un domaine (ses commandes et leurs arguments), la génération de la clé, la lecture du calcul tapé (nombres, unités, variables), l'écriture du Typst et la règle des niveaux vivent dans un module sans Qt (`calc/domains/formula_domain.py` ou nom fixé en revue) ; l'onglet montre, édite et appelle, ne calcule pas.
- **Source** : CLAUDE.md « Domain logic is independent of the UI »
- **Critère d'acceptation** : le module s'importe sans PySide6 (test) ; l'onglet n'a pas d'arithmétique d'unités.

### ARCH-002 — Une seule source pour les unités
- **Exigence** : si Python calcule (Q-004 A), la table des unités (bases, préfixes, unités par dimension) ne doit exister qu'**une fois**, lue par Typst et par Python (par ex. un JSON sous `lib/` que `lib/formula.typ` lit), et un test doit tenir les résultats Python égaux à ceux de Typst.
- **Source** : principe 1, CLAUDE.md « No hardcoding »
- **Critère d'acceptation** : grep : aucune table d'unités écrite deux fois ; test d'égalité Python/Typst (REQ-012).

### ARCH-003 — Les arguments lus sur la signature
- **Exigence** : les options offertes à droite et leurs valeurs par défaut sont lues sur les signatures de `lib/` (`build_reference.signature_defaults`), jamais recopiées ; l'appel est écrit par `build_reference.call_command`.
- **Source** : principe 14, `docs/ui/window.md` (v0.117, « No default is written in a panel »)
- **Critère d'acceptation** : test : chaque argument nommé de chaque commande offerte est offert ou écarté avec raison.

### ARCH-004 — Le format de fichier d'un domaine
- **Exigence** : selon Q-003 : soit un nouveau type d'objet balisé lu et écrit par `calc/typst_objects.py` (forme canonique, `canonical`/`hand_edited`/`unreadable`, archivage avant suppression), soit un fichier par domaine avec le même lecteur. Pas de second lecteur de balises.
- **Source** : principe 15 ; `docs/domain/documents.md` §3.3octodecies
- **Critère d'acceptation** : `structure.scan_tags` reste le seul lecteur de balises (grep) ; tests aller-retour REQ-006.

### ARCH-005 — Une table des unités, lue par Typst et Python
- **Exigence** : `lib/units.json` (préfixes, bases avec facteur et dimensions, exposants, unité par défaut par dimension, **unités offertes par dimension**) remplace les tables écrites dans `lib/formula.typ` ; `calc/units.py` (sans Qt) la lit ; le fichier est dans `project.ENGINE_FILES` et copié par `build_examples.refresh_engine`.
- **Source** : revue ARCH-RISK-105, ARCH-RISK-106 ; D-10
- **Critère d'acceptation** : grep : aucune table d'unités dans `formula.typ` ; `tests/test_units.py` tient Python = Typst (valeur et unité) sur ≥ 20 formules et vérifie que Python refuse tout ce que Typst refuse (somme de dimensions, `sqrt` impair, puissance fractionnaire, unité inconnue).

### ARCH-006 — Le niveau du domaine, sans toucher aux signatures
- **Exigence** : un état `formula-block` posé par `#show-formula` autour de l'`include` est lu par `line-level` (`lib/formula.typ`), seul point d'accroche des cinq commandes ; une commande à `level:` explicite le garde ; `--input uniform=N` reste prioritaire ; aucune signature de commande ne change.
- **Source** : revue ARCH-RISK-103/104 (prototype compilé) ; D-12
- **Critère d'acceptation** : `tests/test_formula.py` passe sans modification de ses cas existants ; nouveaux cas : bloc 0/1/2/3, explicite gardé, `uniform` prioritaire.

## 6. Contraintes

- **CON-001** — Trois langues pour toute chaîne visible (onglet, libellés, messages). Source : inféré (CLAUDE.md).
- **CON-002** — Ne jamais écrire dans les projets de l'ingénieur (Musterprojekt) ; les tests travaillent sur `tests/projet-exemple/`. Source : inféré (CLAUDE.md).
- **CON-003** — Le Typst produit doit compiler avec le moteur actuel (`lib/formula.typ`) sans le modifier pour les commandes existantes ; un littéral unité s'écrit `12 "N"` (`docs/typst/formulas.md` l. 223). Source : inféré.
- **CON-004** — Une clé ne contient jamais de `-` (refusée par le moteur). Source : inféré (`docs/typst/formulas.md` « Never a `-` in a key »).
- **CON-005** — Documentation : `docs/ui/window.md` (nouvel onglet, onglets retirés), `docs/typst/formulas.md` (si un format de domaine est ajouté), `docs/architecture/layout.md`, `docs/README.md` (ligne de `rfem.md`), `docs/decisions.md` (retrait de RFEM et des lignes à mots-clés, avec le prix), `docs/open-questions.md` (questions RFEM devenues sans objet), `CHANGELOG.md`, page « Nouveautés » de la prochaine version en fr/de/en. Source : inféré (CLAUDE.md « A change is finished when its documentation is »).
- **CON-006** — Plusieurs sessions modifient le dépôt (fichiers déjà modifiés : `woodcore_gui.py`, `strings.json`, `docs/ui/window.md`…) : modifications ciblées, jamais de `git checkout/stash/reset/clean`. Source : inféré (CLAUDE.md).

## 7. Décisions prises

- **D-01** — La commande *Domaine* est dans la palette de droite ; le volet de gauche ne fait que naviguer, ouvrir et fermer (T10, qui corrige T7).
- **D-02** — Règle des niveaux de la copie : 1 → `var` à 0, le reste à 1 ; 2 → tout à 1 ; 3 → tout à 3 (T27).
- **D-03** — Le nouvel onglet reprend le nom *Formule* et la place de l'ancien dans *Référence* (T2).
- **D-04** — *(proposée, à confirmer à l'approbation)* Palette initiale : *Domaine*, `var`, `eq`, `verify`, `val`, `var-unit`. `var-line`, `#unit` et les `verify-*` du bois viendront plus tard si demandés.
- **D-05** — *(proposée)* Mode calcul / mode affichage = le commutateur de vues *Calcul · Affichage* déjà construit en v0.117, pas un second commutateur.
- **D-07** — RFEM est retiré **entièrement** : onglet, lecture des exports, domaine, commandes `#rfem-*`, schémas, CLI, modèles statiques générés depuis RFEM, tests (Q-001). Prix accepté : Woodcore ne lit plus d'export RFEM ; un projet qui en nomme un s'ouvre avec un avertissement.
- **D-08** — Le code retiré va dans `Woodcore/archive/<fonctionnalité>/`, versionné, avec un README, exclu des tests, de l'installateur et du site (Q-002).
- **D-09** — Un domaine vit dans **un fichier `.typ` à lui** dans le projet, source de vérité écrite par l'onglet et modifiable dans VS Code ; le rapport l'imprime par une nouvelle commande `#show-formula("<nom>", level:)` qui applique la règle des niveaux D-02 ; une valeur se rappelle ailleurs par `#val(…, domain:)` (Q-003).
- **D-10** — L'onglet calcule en Python à l'instant ; la table des unités n'existe qu'une fois, lue par Python et par `lib/formula.typ` ; un test tient les deux égaux (Q-004). Prix accepté : deux implémentations de l'algèbre des unités.
- **D-11** — Le fichier d'un domaine est `<racine Typst>/Formules/<id>.typ` (comme les feuilles `Plans/<id>.typ`), lu directement par Typst : une modification dans VS Code se voit tout de suite ; Woodcore tient l'index nom → fichier `_woodcore/data/formulas.json` (schéma versionné) à chaque enregistrement et à chaque export (réponse du 2026-10-08). Prix : la migration ancien projet → trois documents doit déplacer `Formules/`.
- **D-12** — Le niveau du domaine (règle D-02) est le défaut général ; une commande dont `level:` est indiqué l'écrase (réponse du 2026-10-08). L'onglet offre `level` dans les options de chaque commande, vide = « celui du domaine ». `var-unit` suit la règle de `var`, `val` celle des autres commandes.
- **D-13** — L'import de variables est dans la v1, par le mode choix de l'onglet *Variables* (REQ-015, UI-007 ; réponse du 2026-10-08).
- **D-14** — La chaîne `diagram` des modèles statiques (`show-static-model(diagram:)`, son option d'affichage, ses champs de schéma, `statics_view.py`), que seul RFEM alimentait, est retirée aussi, en dernier (réponse du 2026-10-08). Prix : un futur import FEM devra la recréer.
- **D-15** — *(prise par l'assistant, sur la revue)* *Copier* offre l'appel `#show-formula` (par défaut) et le Typst développé ; `#show-formula` prend le **nom** du domaine, celui que `#val(domain:)` reçoit.
- **D-16** — *(prise par l'assistant)* L'onglet *Formule* est dans les trois documents : `Formules/` est à la racine Typst, commune aux trois.
- **D-17** — *(prise par l'assistant)* Lecture du calcul tapé : un mot d'unité connu qui suit directement un nombre est une unité (`12 N`, `3000 mm`), écrit `(12 "N")` — entre parenthèses pour que la ligne en lettres compose la fraction juste ; une clé générée qui se lirait comme une unité (`m`, `l`, `N`) prend `_1`, le moteur substituant les noms jusque dans les unités entre guillemets (docs/open-questions.md) ; tout autre mot est une variable du domaine, et un mot inconnu est refusé à la validation. Typst n'a pas de multiplication implicite, donc `2 l` ne peut pas vouloir dire 2·l.
- **D-18** — *(prise par l'assistant, revue ARCH-RISK-002)* Un projet qui porte encore `rfem_models` / `rfem_export` reçoit un avertissement à **chaque** export, nommant la clé ; le fichier n'est jamais réécrit par Woodcore. Les projets neufs n'écrivent plus `rfem_export` (passage à sens unique, sans changement de `schema_version`) ; la clé reste décrite « retirée, ignorée » dans les schémas.
- **D-19** — *(prise par l'assistant, revue ARCH-RISK-004/005)* L'export balaie `data/rfem.json` et `data/rfem/` avec un message ; `project_migrate` ne suit plus les chemins RFEM (le dossier `RFEM-Export/` suit le dossier du rapport comme un autre).
- **D-20** — *(prise par l'assistant, revue ARCH-RISK-102)* Un fichier de domaine porte **une** balise `// woodcore:object formula-domain domain` autour de son `#var-domain` ; il est lu par `structure.pair_tags` (seul lecteur de balises) et un analyseur d'appels positionnels (option du `_Parser` de `typst_objects`, désactivée pour les dix commandes de document) ; les états `canonical` / `hand_edited` / `unreadable` ont le sens de `typst_objects`. Un fichier illisible arrête l'export en le nommant ; un fichier écrit à la main est exporté tel quel avec un avertissement.
- **D-06** — *(proposée)* T19 dit « volet de gauche » et T23 « à droite en haut » : un clic sur une variable l'insère depuis les deux endroits.

## 8. Hors périmètre

- La modification des commandes Typst existantes (`var`, `eq`, `verify`, `val`, `var-domain`) : l'onglet écrit ce qu'elles acceptent déjà.
- L'écriture d'appels `verify-*` du bois (`#member`…) depuis l'onglet.
- La restauration de RFEM ou des lignes à mots-clés : l'archive les garde, rien de plus.

## 9. Idées non retenues comme exigences

- T6 « j'imagine par exemple » : la liste VAR, EQ, VAL, VERIFY est un exemple ; la palette arrêtée est D-04.
- T20 « 12 newtons divisé par 3 mètres » : exemple d'un calcul avec unités, repris comme critère de REQ-009.

## 10. Questions

### Q-001 — Jusqu'où retirer RFEM ?
- **Pourquoi elle compte** : l'onglet n'est que la vitrine. Derrière lui : la lecture des exports (`calc/rfem_import/`, 11 modules), le domaine `calc/domains/rfem.py`, les commandes `#rfem-max`, `#show-rfem-forces`, `#show-rfem-combination` (`lib/rfem.typ`) et leurs aiguillages dans `lib/calc-engine.typ`, deux schémas, la commande `woodcore-cli rfem-import`, les modèles statiques générés depuis RFEM, environ 140 tests. Musterprojekt nomme encore un modèle RFEM.
- **Options** : **A (recommandée)** tout retirer et archiver (onglet, lecture, domaine, commandes Typst, schémas, CLI, tests) — un projet qui nomme RFEM s'ouvre avec un avertissement (REQ-004) ; **B** retirer seulement l'onglet, garder la lecture à l'« Import données » et les commandes `#rfem-*`.
- **Réponse** : **A — tout retirer et archiver** (l'ingénieur, 2026-10-08).

### Q-002 — Où mettre l'archive ?
- **Pourquoi elle compte** : dans le dépôt elle reste versionnée et facile à restaurer, mais il faut l'exclure des tests et de l'installateur ; hors du dépôt elle n'est plus versionnée.
- **Options** : **A (recommandée)** `Woodcore/archive/<rfem|formules-dsl>/` dans le dépôt, avec un README (version, commit, restauration), exclu des tests, de l'installateur et du site ; **B** un dossier hors du dépôt, à côté de Woodcore (`../ExternalFiles/archive/`) ; **C** pas de copie : un tag git suffit.
- **Réponse** : **A — `Woodcore/archive/`** dans le dépôt (l'ingénieur, 2026-10-08).

### Q-003 — Où vit un domaine (la source de vérité) ?
- **Pourquoi elle compte** : c'est le contrat de données de la fonctionnalité ; il décide ce que « synchronisé avec Typst » et « appeler ailleurs dans le rapport » veulent dire.
- **Options** : **A (recommandée)** **un fichier `.typ` par domaine** dans le projet (`Woodcore-Datei/formulas/<id>.typ`, écrit par l'onglet, lisible et modifiable dans VS Code), source de vérité ; le rapport l'imprime où il veut avec une commande `#show-formula("<nom>", level: 2)` qui applique la règle des niveaux, et en lit une valeur ailleurs par `#val(…, domain:)` ; *Copier* donne cet appel, ou le Typst développé. **B** le domaine est un **objet balisé dans les sections** des documents (`// woodcore:object formula <id>`), lu et réécrit en place comme les tableaux ; un nouveau domaine est ajouté à une section choisie ; le rappeler ailleurs = `#val(domain:)` ou coller une copie. **C** un JSON par domaine + export + commande Typst qui calcule depuis le JSON (le Typst n'est plus la source).
- **Réponse** : **A — un `.typ` par domaine**, imprimé par une nouvelle commande `#show-formula` (l'ingénieur, 2026-10-08).

### Q-004 — Comment l'onglet obtient-il les valeurs (forme visuelle) ?
- **Pourquoi elle compte** : la forme lisible d'un `eq` (formule en chiffres et résultat) demande l'algèbre des unités, qui n'existe aujourd'hui qu'en Typst.
- **Options** : **A (recommandée)** un calcul Python instantané (comme Traction / Compression en v0.117) : un petit module d'algèbre d'unités, la table des unités sortie dans un JSON lu aussi par `lib/formula.typ`, et un test qui tient Python égal à Typst ; **B** à chaque Enter, compiler le domaine avec Typst et relire le registre (une seule algèbre, mais ~1 s d'attente par validation) ; **C** pas de valeur dans l'onglet : la forme lisible montre lettres et unités, les chiffres seulement en mode *Affichage*.
- **Réponse** : **A — calcul Python instantané**, table des unités unique, test d'égalité avec Typst (l'ingénieur, 2026-10-08).

## 11. Critères d'acceptation

- [x] REQ-001 — `tab_rfem` absent, rien n'importe le code archivé, suite verte.
- [x] REQ-002 — `dsl.py`, `dsl_tab.py` archivés ; `test_timber.py` vert.
- [x] REQ-003 — archive avec README, exclue des tests et de l'installateur.
- [x] REQ-004 — le projet d'exemple avec clés RFEM s'ouvre et s'exporte, avec un avertissement.
- [x] REQ-005 — un domaine = un `#var-domain` ; rappel par `#val(domain:)` compilé.
- [x] REQ-006 — aller-retour onglet ↔ fichier ; édition à la main relue et signalée.
- [x] REQ-007 — appel `var` correct ; arguments offerts ou écartés.
- [x] REQ-008 — génération de clé : les cinq cas.
- [x] REQ-009 — `12 N / 3 m` et `/ 3000 mm` = 4 N/m ; unité de sortie ; unité inconnue refusée.
- [x] REQ-010 — clic sur une variable insère son nom affiché au curseur.
- [x] REQ-011 — `verify`, `val`, `var-unit` produisent des appels qui compilent.
- [x] REQ-012 — valeurs de l'onglet = registre Typst sur ≥ 20 formules.
- [x] REQ-013 — copie aux niveaux 1/2/3 conforme à D-02, et compile.
- [x] REQ-014 — `#show-formula` documentée, exemplifiée, traduite ; mêmes niveaux que le Typst développé.
- [x] REQ-015 — import depuis *Variables* en mode choix ; valeur lue à la source ; cycle refusé.
- [x] UI-007 — mode choix : autres onglets désactivés, Importer/Annuler/Échap.
- [x] ARCH-005 — `units.json` unique ; Python = Typst sur ≥ 20 formules ; refus identiques.
- [x] ARCH-006 — `formula-block` dans `line-level` ; `test_formula.py` inchangé.
- [x] UI-001 — onglet *Formule* dans *Référence*, trois langues.
- [x] UI-002 — arbre des domaines, ouvrir/fermer, contenu, pas de création à gauche.
- [x] UI-003 — volet de droite dans ses quatre états, variables toujours en haut.
- [x] UI-004 — ligne du domaine éditable et sélectionnable ; nom en double refusé.
- [x] UI-005 — Tab / Enter / forme lisible / double-clic ; commande invalide refusée avec raison.
- [x] UI-006 — *Calcul · Affichage* ; aperçu au niveau choisi ; *Copier*.
- [x] ARCH-001 — module sans Qt.
- [x] ARCH-002 — une seule table d'unités ; égalité Python/Typst.
- [x] ARCH-003 — options lues sur les signatures.
- [x] ARCH-004 — un seul lecteur de balises ; aller-retour.
- [x] Documentation : `docs/` (CON-005), `CHANGELOG.md`, « Nouveautés » fr/de/en ; `///` + deux exemples + traduction pour toute nouvelle commande Typst (`#show-formula` si Q-003 A).
- [x] Tests : nouveaux `tests/test_formula_domain.py`, `tests/test_formula_tab.py` ; tests RFEM/DSL archivés ; `python tests/run_tests.py` vert.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-002, REQ-003, Q-001, Q-002 | capturé / questions |
| T2 | UI-001, REQ-002, D-03 | capturé |
| T3 | §1, ARCH-001 | capturé |
| T4 | REQ-006, UI-002, Q-003 | capturé / question |
| T5 | REQ-005, REQ-006, REQ-014, D-09 | capturé |
| T6 | UI-003, REQ-011, D-04, §9 | capturé |
| T7 | — | corrigé par T10 (D-01) |
| T8 | UI-004, UI-003 | capturé |
| T9 | UI-003 | capturé |
| T10 | D-01, UI-002 | décision |
| T11 | UI-002 | capturé |
| T12 | REQ-007 | capturé |
| T13 | REQ-007, UI-003 | capturé |
| T14 | UI-005 | capturé |
| T15 | UI-005, REQ-012 | capturé |
| T16 | UI-005 | capturé |
| T17 | REQ-008 | capturé |
| T18 | REQ-009 | capturé |
| T19 | REQ-010, D-06 | capturé (gauche/droite : D-06) |
| T20 | REQ-009, REQ-012, §9 | capturé |
| T21 | REQ-009 | capturé |
| T22 | UI-005, REQ-012 | capturé |
| T23 | UI-003, REQ-010 | capturé |
| T24 | REQ-009 (une équation crée une variable) | inféré d'une phrase interrompue |
| T25 | UI-006, D-05 | capturé |
| T26 | REQ-013, UI-006 | capturé |
| T27 | REQ-013, D-02 | décision |

### Points de la source non résolus

- Aucun : Q-001 à Q-004 répondues le 2026-10-08.

## 13. Revue d'architecture

Deux revues indépendantes (`architecture-reviewer`, 2026-10-08), l'une sur le retrait, l'autre sur l'onglet ; prototype Typst compilé hors du dépôt (inclusion à chemin calculé, niveau de bloc par `line-level`, rappel par `#val(domain:)`). **Verdict des deux : APPROUVER AVEC RÉSERVES** — réserves levées par D-11 à D-20 et par le plan.

**Retrait (REQ-001 à REQ-004).** Propriétaires uniques : `rfem_tab.py`, `calc/rfem_import/` (lu aussi par `cli.py:289`, `export_all.py:23`), `calc/domains/rfem.py`, `lib/rfem.typ` (réexporté par `formula.typ:25-27`), `dsl.py`, `dsl_tab.py`. Orphelins découverts : `calc/domains/statics_view.py`, `schemas/statics-view.schema.json`, `test_statics_view.py`, le paramètre `generated=` de `statics.prepare/export`, la chaîne `diagram` (D-14). Couplages à couper : `project.py` (`MODE_KEYS`, `LAYOUT_ORDER`, `RFEM_EXPORT_FOLDER`, `rfem_models*`, `rfem_export_dir`, `set_rfem_models`, `ENGINE_FILES`), `export_all.py` (6 points), `cli.py` (sous-commande `import`), `documents.py:130`, `project_template.py`, `templates.py:945`, `archive_export.py:145`, deux schémas de projet, `project_migrate.py` (14 points), `migrate_dialog.py`, `chrome.py` (icônes), `woodcore_gui.py`, `calc-engine.typ:335-388,422-515`, `build_reference.py` (`LIB_FILES`, `CATEGORIES`, `REQUIRED_NAMED`), `commands.json` (6 entrées), `strings.json` (7 clés `rfem.*`), 18 exemples et leurs PNG.
- ARCH-RISK-001 (bloquant) — fichiers modifiés non commités par d'autres sessions : coordination, éditions ciblées, clé neuve `tab_formula`.
- ARCH-RISK-002 (bloquant) — aucun canal d'avertissement pour une clé inconnue du projet : `RETIRED_KEYS` + `Project.retired_keys()` (D-18).
- ARCH-RISK-003 — orphelins (D-14). ARCH-RISK-004 — `data/rfem*` sans balayeur ; `test_the_export_is_reproducible` rouge une fois (D-19). ARCH-RISK-005 — `project_migrate` (D-19). ARCH-RISK-006 — `MODE_KEYS` 7 → 6, sens unique (D-18). ARCH-RISK-007 — Typst et catalogue à retirer en un seul pas (`test_commands` tient les deux sens). ARCH-RISK-008 — archive : `run_tests.py` non récursif, `woodcore.spec` hors `archive/` ; ajouter `archive/conftest.py` (`collect_ignore_glob`), `paths-ignore` du site, `git mv` en gardant l'arbre d'origine. ARCH-RISK-009/010 — icônes, docstrings, documentation et décision §13.

**Onglet (REQ-005 à REQ-015).** À réutiliser : `member_check.py` comme gabarit (`prepare/write/empty/draft_typst/compute`, test d'égalité Python = Typst `test_member_check.py:546`), `structure.pair_tags`, les littéraux de `typst_objects._Parser`, `build_reference.call_command/typst_value/Raw/signature_defaults`, `display_options.SPECS["var"/"val"]` + `DISMISSED` + `SpecPanel`, `DisplayView`/`Entry` (`snippet_fn`, `call_fn`), `views.CALC_VIEWS`, `autosave`, `identity`, `cards`, `grouped_list`, `variables.fmt_value`, `richtext.math_html/MathDelegate`, `sheets.archive`, `export_all.seed`.
- ARCH-RISK-101 (bloquant) — Typst ne lit pas `Woodcore-Datei/` : levé par D-11 (`Formules/` dans la racine).
- ARCH-RISK-102 — `typst_objects` refuse les arguments positionnels : D-20.
- ARCH-RISK-103/104 — niveau par commande vs bloc ; règle des niveaux en Python et en Typst : D-12, ARCH-006, test SVG identique.
- ARCH-RISK-105 — seconde algèbre d'unités, contre `decisions.md:92` (v0.100) et dans la ligne de `:483` (v0.117) : décision à écrire ; grammaire Python sous-ensemble strict de Typst ; liste des unités offertes = donnée nouvelle de `units.json` ; le choix d'unité de sortie est un contrôle dynamique (dimension du résultat). ARCH-RISK-106 — `units.json` dans `ENGINE_FILES` et `refresh_engine`.
- ARCH-RISK-107 — `key-symbol` non reproductible exactement en Python : le symbole n'est omis que si le texte tapé est la clé ; noms grecs sortis dans un module sans Qt lu aussi par `richtext`, tenu égal à `formula.typ`.
- ARCH-RISK-108 — domaines en îlots : levé par D-13 (REQ-015) ; un nom de domaine en double est refusé à l'export.
- ARCH-RISK-109 — ne pas ajouter de sixième écrivain de valeurs, formateur de nombres, ligne d'import ou archiveur. ARCH-RISK-110 — `WRITERS`, `STRINGS` propre à l'onglet, icône. ARCH-RISK-111 — `seed`, exemples gelés, `ids_by_kind`, `docs/typst-reference.xlsx`, `SOURCE_FOLDERS`/`Project.formulas_dir`. ARCH-RISK-112 — `test_formula.py` (≈70 cas) inchangé.

## 14. Plan d'implémentation

Deux phases, chacune verte avant la suivante ; la phase A peut faire l'objet d'un commit séparé si l'ingénieur le demande. Avant chaque étape qui touche un fichier modifié par une autre session (`woodcore_gui.py`, `strings.json`, `commands.json`, `build_reference.py`, `chrome.py`, `display_options.py`, `lib/calc-engine.typ`, `docs/*`), coordination par SendMessage ; éditions ciblées seulement.

**Phase A — retrait**
1. `archive/` : `archive/README.md`, `archive/conftest.py` (`collect_ignore_glob = ["*"]`), `archive/rfem/README.md`, `archive/formules-dsl/README.md` ; `archive/**` dans `paths-ignore` de `.github/workflows/site.yml`. (REQ-003)
2. `project.py` : `RETIRED_KEYS`, `Project.retired_keys()` ; avertissement à chaque export (`export_all`) et à l'ouverture (notifications). Test d'abord. (REQ-004, D-18)
3. Typst et catalogue, en un pas : `lib/rfem.typ`, les fonctions RFEM de `calc-engine.typ`, la réexportation de `formula.typ`, `ENGINE_FILES`, `LIB_FILES`/`CATEGORIES`/`REQUIRED_NAMED`, 6 entrées de `commands.json`, 7 clés `rfem.*` de `strings.json` (et sa copie `examples/calc/i18n/`), exemples `examples/*rfem*` et PNG, `examples/out/index.json`, `examples/data/rfem*`. Tests : `test_commands`, `test_doc_comments`, `test_documents`, `test_timber`. (REQ-001)
4. Chaîne d'export : `statics.prepare/export` sans `generated`, `export_all` sans RFEM, balayage de `data/rfem*` (D-19), `seed` sans `rfem.json`, `cli.py` sans `import`. Tests : `test_export`, `test_statics`, `test_cli`. (REQ-001, REQ-004)
5. Disposition du projet : `MODE_KEYS`, `LAYOUT_ORDER`, `documents.py`, `project_template.py`, `templates.py`, `archive_export.py`, schémas (clé décrite « retirée ») ; `project_migrate.py`, `migrate_dialog.py`, `reexport_what`. Tests : `test_project`, `test_new_project`, `test_templates`, `test_archive`, `test_migrate` entier. (REQ-001, D-18, D-19)
6. Fenêtre : imports, `TABS`, `NAV_GROUPS` (`nav_structure` = statics, schema ; `nav_reference` = variables, commandes), fusions `rf_`/`dsl_`, icônes ; docstrings orphelines ; tests de fenêtre (`test_chrome`, `test_views`, `test_variables`, `test_modes_window`). (REQ-001, REQ-002)
7. `git mv` vers `archive/` en gardant l'arbre d'origine : code, `statics_view.py`, schémas, tests, fixtures, `conftest.real_rfem_export`, `docs/domain/rfem.md`, la section §3.3septdecies de `member-checks.md` (un pointeur reste) ; retrait des `data/rfem*` versionnés de `tests/projet-exemple/_woodcore/` (le `.woodcore` garde ses clés : c'est le banc de REQ-004). Nouveau `tests/test_retired_features.py`. (REQ-001 à REQ-004)
8. Chaîne `diagram` (D-14) : `show-static-model(diagram:)`, `calc-engine.typ:1506-1540`, `statics.py`, `display_options.py:75` et ses clés, `statics_tab.py:2266`, deux schémas, `test_display_view.py:200-209` — après le commit des sessions qui tiennent ces fichiers.
9. Documentation du retrait : `docs/README.md`, `layout.md`, `principles.md`, `performance.md`, `window.md`, `api-conventions.md`, `testing.md`, `build-and-release.md`, `open-questions.md` §14, `decisions.md` (entrée « Retrait de RFEM et des lignes à mots-clés », avec son prix). Suite complète.

**Phase B — onglet Formule**
10. Unités : `lib/units.json` lu par `formula.typ` (remplace `unit-prefixes`, `unit-bases`, `unit-exponents`, `default-units`) ; `calc/units.py` (analyse d'unité, quantités, évaluateur sous-ensemble de `parse-expr`, présentation, unité naturelle) ; noms grecs dans un module sans Qt, lu par `richtext` ; `ENGINE_FILES`, `refresh_engine`. `tests/test_units.py`. (ARCH-002, ARCH-005, REQ-012)
11. Typst : état `formula-block`, `line-level(st, level, kind:)`, `kind: "var"` pour `var` et `var-unit` ; `#show-formula(name, level: auto)` (index `../data/formulas.json`, `panic` listant les domaines connus, `include` de `/Formules/<id>.typ`) ; `///`, deux exemples, `CATEGORIES`, `commands.json` fr/de. `tests/test_formula.py` étendu. (REQ-014, ARCH-006)
12. Domaine : `calc/domains/formula_domain.py` — modèle (domaine, commandes), lecture/écriture du fichier (D-20 ; option positionnelle du `_Parser`), clé générée (REQ-008), calcul tapé → formule Typst (D-17), `compute` (avec les variables importées et la détection de cycle), `draft_typst(domain, level)`, `prepare/write/empty`, `EXPORT_FILE = "formulas.json"` ; `schemas/formulas.schema.json` ; `Project.formulas_dir` (`<racine>/Formules`), `SOURCE_FOLDERS` ; `export_all` + `seed` ; doublon de nom refusé ; migration qui déplace `Formules/`. Domaine d'exemple dans `tests/projet-exemple`, gel des exemples. `tests/test_formula_domain.py`. (REQ-005 à REQ-009, REQ-011 à REQ-014, ARCH-001, ARCH-004)
13. Onglet : `calc/tools/formula_tab.py` (+ `STRINGS` fr/de/en, préfixe `fm_`) — gauche : arbre des domaines et de leur contenu ; centre : ligne du domaine, blocs (édition Tab/Maj+Tab/Enter, forme lisible, double-clic) ; droite : variables du domaine toujours en haut (clic = insertion, *Importer*), palette ou options (`SpecPanel`, `SPECS` de `eq`, `verify`, `var-unit`, `show-formula` ; unité de sortie dynamique) ; *Calcul · Affichage* (`CALC_VIEWS`, `DisplayView`, niveau, *Copier* appel ou développé) ; `autosave`, `confirm_leave`, `WRITERS` ; `TABS`, `NAV_GROUPS["nav_reference"]`, icône, trois documents. `tests/test_formula_tab.py`. (UI-001 à UI-006, REQ-010)
14. Import : mode choix de `VariablesTab` (bandeau, *Importer*/*Annuler*, Échap ; navigation et autres onglets désactivés) ; source « Formules » dans *Variables* ; retour de la variable dans le domaine. Tests dans `test_formula_tab.py` et `test_variables.py`. (REQ-015, UI-007)
15. Documentation : `window.md` (onglet *Formule*, mode choix de *Variables*), `formulas.md` (`show-formula`, `units.json`, niveau de bloc), `layout.md`, `decisions.md` (D-09 à D-20 ; seconde algèbre d'unités : prolonge `:483`, borne `:92`), `CHANGELOG.md`, `website/content/{fr,de,en}/changes/0.117.0.md`. Suite complète, puis vérification indépendante.

## 15. Vérification

Vérificateur indépendant (`requirements-verifier`), 2026-10-08, arbre de travail contre `b462466`. **Premier tour : aucun ❌ ; des ⚠️ de preuve manquante**, corrigés dans la foulée par des tests ajoutés (colonne « Après correction ») ; trois défauts réels trouvés par ces tests et corrigés : le message « clé déjà prise » (argument `key` en conflit avec `MainWindow.t`), l'onglet hors des conventions d'éditeur de la fenêtre (marque de non-enregistré en icône, bouton désactivé sans raison), un mot de la palette identique en fr et en en.

| Élément | Verdict | Preuve (fichier:ligne, test, sortie) |
|---|---|---|
| REQ-001 | ✅ | `test_retired_features` (balayage, onglets, icônes) ✓ ; `test_chrome` ✓ |
| REQ-002 | ✅ | `archive/formules-dsl/` ; `test_timber` 38 ✓ inchangé |
| REQ-003 | ✅ | `archive/README.md` + deux README ; `archive/conftest.py` ; `site.yml` ; `test_the_archive_holds_both_features_and_stays_out_of_the_way` ✓ |
| REQ-004 | ✅ | `test_a_project_still_naming_rfem_exports_with_a_warning_and_no_rfem_file` ✓ ; avertissement aussi à l'ouverture (`woodcore_gui.open_project`) |
| REQ-005 | ✅ | `formula_domain.body_of` ; `test_show_formula_registers_at_level_zero_…` ✓ |
| REQ-006 | ✅ (après tour 2) | aller-retour octet pour octet, `hand_edited`, `unreadable`, CRLF : `test_formula_domain` ✓ ; une valeur changée dans le fichier relue par l'onglet à son affichage : `test_a_value_changed_by_hand_is_read_again_and_affichage_compiles_…` ✓ |
| REQ-007 | ✅ | `to_call` ; `test_every_named_argument_is_offered_or_dismissed_with_its_reason` ✓ ; quatre champs testés |
| REQ-008 | ✅ | `test_a_key_is_made_from_the_shown_variable` ✓ (+ clés d'unité → `_1`) |
| REQ-009 | ✅ (après) | 4 N/m à 3 m et 3000 mm, sortie N/mm, `12 Zork` refusé ; écriture entre parenthèses consignée au critère et à D-17 |
| REQ-010 | ✅ (après) | clic dans la liste et dans l'arbre de gauche, au curseur : `test_the_right_pane_s_four_states_…` ✓ |
| REQ-011 | ✅ (après) | `test_val_and_var_unit_are_computed_and_compile_in_a_domain` ✓ |
| REQ-012 | ✅ | `test_python_and_typst_give_one_value_and_one_unit` : 31 formules, dont des clés grecques ✓ |
| REQ-013 | ✅ (après) | `test_a_command_stating_its_own_level_keeps_it_on_the_page_at_every_domain_level` : SVG `#show-formula` = Typst développé aux niveaux 1-3 avec un `level: 3` explicite ✓ |
| REQ-014 | ✅ | `lib/formula.typ` `show-formula`, `///`, 2 exemples rendus, catégorie, fr/de ; `test_commands` ✓ hors le rouge des exemples figés (sessions concurrentes sur `lib/`) |
| REQ-015 | ✅ (après tour 2) | `test_a_variable_is_imported_through_the_variables_tab_…` (Importer, Annuler, Échap) ✓ ; cercle refusé **à l'import**, rien d'écrit, et variable d'un domaine de document lue là où *Variables* l'a lue : `test_a_circle_is_refused_at_the_import_and_a_document_s_variable_is_read_…` ✓ (défaut corrigé : l'onglet résolvait avec la version sur disque du domaine ouvert) |
| UI-001 | ✅ | `test_the_tab_is_first_in_reference_in_three_languages_with_its_icon` ✓ (et dans cu/bp/rs) |
| UI-002 | ✅ | `test_the_left_pane_lists_the_domains_…` ✓ |
| UI-003 | ✅ (après) | quatre états 0/1/0/2, variables au-dessus : `test_the_right_pane_s_four_states_…` ✓ |
| UI-004 | ✅ (après) | nom sélectionné à la création, renommage suivi par l'arbre et le fichier, nom pris refusé ✓ |
| UI-005 | ✅ (après) | Tab / Maj+Tab sur la chaîne de focus, clé en double et nom inconnu refusés, double-clic, Échap ✓ |
| UI-006 | ✅ (après tour 2) | la vue *Affichage* demande l'en-tête du snippet et l'appel au niveau choisi, *Copier* copie exactement l'appel, et le Typst développé au niveau 1 : `test_a_value_changed_by_hand_is_read_again_and_affichage_compiles_and_copies_what_it_shows` ✓ |
| UI-007 | ✅ (après) | navigation et raccourcis désactivés, bandeau, Importer/Annuler/Échap ✓ (critère précisé) |
| ARCH-001 | ✅ (après) | `test_the_domain_modules_import_without_qt` ✓ |
| ARCH-002, ARCH-005 | ✅ | `test_the_units_are_written_once_and_copied_with_the_engine`, `test_python_refuses_what_typst_refuses` ✓ |
| ARCH-003 | ✅ | SPECS/DISMISSED ; `test_display_view` 13 ✓ |
| ARCH-004 | ✅ | `structure.pair_tags` ; `test_a_document_command_still_refuses_a_positional_argument` ✓ |
| ARCH-006 | ✅ (après) | `formula-block`, `line-level` ; `test_formula` inchangé ✓ ; `test_a_uniform_level_wins_over_the_domain_s` ✓ |
| CON-001 à CON-005 | ✅ | trois langues (test de clés) ; projet d'exemple seul ; signatures inchangées ; pas de `-` ; docs, CHANGELOG, Nouveautés fr/de/en |
| §8 hors périmètre | ✅ | signatures existantes inchangées ; pas de `verify-*` du bois ; archive non restaurée |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-08 | draft | spécification extraite de la transcription (T1–T27) ; 13 REQ, 6 UI, 4 ARCH, 6 CON, 4 questions |
| 2026-10-08 | specified | Q-001 à Q-004 répondues (toutes option A) ; D-07 à D-10 ; REQ-006, REQ-012, REQ-013 et la nouvelle REQ-014 précisées |
| 2026-10-08 | reviewed | deux revues d'architecture (APPROUVER AVEC RÉSERVES) ; 4 questions de plus à l'ingénieur → D-11 à D-14 ; D-15 à D-20 prises sur la revue ; REQ-015, UI-007, ARCH-005, ARCH-006 ajoutées ; plan en 15 étapes |
| 2026-10-08 | approved | approuvée par l'ingénieur ; implémentation lancée (phase A) |
| 2026-10-08 | implementation | phase A, étapes 1 à 8 faites : `archive/` (README, conftest, site.yml) ; `RETIRED_KEYS` + `Project.retired_keys()` + avertissement à l'export ; Typst et catalogue (rfem.typ, calc-engine, formula.typ, build_reference, commands.json, strings.json, 18 exemples) ; export (statics sans `generated`, `_sweep_retired`, seed, CLI `import`) ; disposition et migration (MODE_KEYS 6, schémas, project_migrate sans chemins RFEM) ; fenêtre (onglets, icônes, chaînes) ; `git mv` vers `archive/rfem` et `archive/formules-dsl` ; chaîne `diagram` retirée ; `tests/test_retired_features.py` (4 ✓). Reste : étape 9 (documentation du retrait), tests de garde en cours, puis phase B |
| 2026-10-08 | testing | étape 9 faite (docs du retrait, décision « Retrait de RFEM »). Phase B, étapes 10 à 15 faites : `lib/units.json` + `calc/units.py` (+ `calc/greek.py`, lu par richtext) ; `formula.typ` (tables lues dans units.json, `formula-block`/`line-level`, `#show-formula` avec `///`, 2 exemples, catégorie, fr/de) ; `calc/domains/formula_domain.py`, `typst_objects._Parser.call(positional=)`, `schemas/formulas.schema.json`, export + seed, `Project.formulas_dir`, migration/archives/modèles ; domaine d'exemple « Poutre P1 » dans `tests/projet-exemple` et `examples/` ; `calc/tools/formula_tab.py`, `display_options` (eq, verify, var-unit, show-formula), fenêtre (TABS, *Référence*, icône, garde lecture seule, `begin_variable_pick`) ; mode choix de *Variables* et source « Formules » (`variable_sources.FILE_SOURCES`) après la réécriture de la session « Issue 13 » ; docs (formulas.md, window.md, layout.md, principles.md, testing.md, decisions.md, open-questions.md), CHANGELOG, Nouveautés 0.117 fr/de/en ; exemples régénérés. Tests : test_units 6 ✓, test_formula_domain 12 ✓, test_formula_tab 5 ✓, test_retired_features 4 ✓, test_formula (≈90) ✓ ; reprises des fichiers touchés en cours. Écart : une clé qui se lit comme une unité prend `_1` (le moteur substitue dans les unités entre guillemets, noté dans open-questions) |
| 2026-10-08 | verification | tour 1 du vérificateur : 0 ❌, des ⚠️ de preuve ; tests ajoutés (uniform, val/var-unit, niveau explicite compilé, quatre états, focus et renommage, Tab, refus, Échap, clic dans l'arbre, import sans Qt, formules grecques) ; défauts réels corrigés (`fm_key_taken`, conventions d'éditeur de la fenêtre, mot fr = en) ; critères REQ-009 et UI-007 précisés, D-17 complétée |
| 2026-10-08 | verification | tour 2 du vérificateur : 13 des 17 ⚠️ levés, 0 ❌ ; restaient REQ-006, REQ-015, UI-006 (preuves) — trois tests ajoutés et un défaut corrigé (cercle à l'import : l'onglet résolvait avec la version sur disque du domaine ouvert, hors de la pile) ; `test_formula_tab` 8 ✓. Ces trois lignes sont prouvées par les tests, non revues par un troisième tour (deux au plus) |
| 2026-10-08 | completed | tous les critères ✅ ; fichiers de tests de garde verts (test_units, test_formula*, test_retired_features, test_window, test_i18n, test_variables, test_project, test_export, test_migrate, test_new_project, test_templates, test_typst_objects, test_typst_paths, test_display_view, test_chrome, test_views, test_modes_window, test_member_check, test_report…) ; **suite complète reportée à la demande de l'ingénieur** (arrêtée à ~270 tests) ; à refaire : `python calc/tools/build_examples.py` une fois les sessions concurrentes finies sur `lib/` (seul rouge connu : `test_commands.test_the_frozen_examples_run_against_the_current_engine`) |
