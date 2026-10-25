---
id: 2026-10-24-onglet-commandes-pages
titre: Onglet Commandes — pages condensées pour les 54 commandes, ligne de la commande à bulles, rendu pré-compilé de chaque valeur
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-25
source: issue GitHub #115 (prototype validé par l'ingénieur le 24.10.2026, « Commandes, deuxième version », version « Bulle des valeurs avec rendus »)
docs: [docs/ui/tab-commands.md, docs/typst/command-docs.md, docs/typst/api-conventions.md, docs/architecture/principles.md, docs/architecture/layout.md, docs/decisions.md, docs/conventions/testing.md]
---

# Onglet Commandes — pages condensées — Spécification

## 1. Objectif

Refaire les pages de l'onglet « Commandes » (groupe Référence, `tab_commands`) d'après le prototype validé : en tête la ligne de la commande avec tous ses arguments et leurs valeurs par défaut, des bulles au survol (une phrase par argument ; pour chaque valeur, l'appel Typst et son rendu pré-compilé), un tableau des arguments avec statut et exemples, quatre cartes « L'essentiel ». Les textes courts quittent les blocs `///` pour un fichier nouveau, `calc/i18n/command-pages.json`, en trois langues ; le bloc `///` reste la référence longue que Tinymist montre. Le site (`website/build.py`) montre la même page. Cette spécification livre la mécanique **et la page condensée de chacune des 54 commandes publiques** de `CATEGORIES` (9 « Calculer dans le rapport », 11 « Imprimer un dessin ou un objet », 8 « Lire les données du projet », 20 « Le document et ses citations », 6 « Écrire un modèle » ; le prototype comptait « 44 autres », le code en compte 45), écrites à la main en français, allemand et anglais, catégorie par catégorie, chacune aussi soignée que celle de `var` (réponse à Q-002, 24.10.2026). Aucune page longue de repli ne survit à la fin.

## 2. Source

La source, mot pour mot et coupée en points T, est dans [docs/history/2026-10-24-onglet-commandes-pages-source.md](../../history/2026-10-24-onglet-commandes-pages-source.md) (déplacée le 24.10.2026 pour tenir la spec sous 100 KB ; rien n'y est changé).

## 3. Exigences fonctionnelles

État actuel relevé dans le code (master `a9cae26`) : `calc/tools/commands_tab.py` (arbre des catégories, panneau de la commande, deux appels à copier, exemples derrière une flèche avec boutons de niveau, `RenderJob` pour le français et l'anglais compilés à la demande) ; `command_docs.py` (`localise`, `arguments`, `signature`, `calls`, `example_levels`, `category_label`, `word`) ; `build_reference_lib.CATEGORIES` (formula, display, data, format, document, Internes) ; `LEVELS_CONFOUNDED` (niveaux égaux, déclarés à la main) ; `build_examples.LANG = "de"` (exemples committés en allemand, `examples/out/`, 4,9 Mo, 200 fichiers). Il n'y a **aucune vue Affichage** ni aucun module d'état dans l'onglet aujourd'hui (les occurrences de « Affichage » du prototype v1 n'ont pas été livrées) : T6 et T13 s'y traduisent par « ne pas les ajouter ». Le module « Dans ce projet » n'existe pas : il est **nouveau**. `command-pages.json`, son schéma, les rendus de valeurs, la mention « mêmes niveaux » et les bulles sont **nouveaux**.

### REQ-001 — `calc/i18n/command-pages.json`, son schéma et sa lecture
- **Exigence** : Woodcore doit lire un fichier `calc/i18n/command-pages.json` (champ `schema_version`, schéma `schemas/command-pages.schema.json`) qui porte, en fr, de, en : par commande `lead` et `keys` (titre, texte) ; par argument `group`, `status` (obligatoire / optionnel), `text`, `examples` (code, ce qu'il montre), `values` ; `named`. Un fichier défectueux arrête la construction en nommant le fichier et le champ ; une langue manquante pour une commande qui a une entrée est une erreur de test, pas un repli silencieux.
- **Source** : T4, T17, T36
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_commands.py` (ou un fichier voisin) valide le fichier contre le schéma ; un champ retiré ou une langue absente fait échouer le test en nommant la commande, l'argument et la langue ; la lecture d'un fichier malformé lève une erreur qui cite le fichier et le champ.

### REQ-002 — Contenu de la catégorie « Calculer dans le rapport »
- **Exigence** : `command-pages.json` doit contenir l'entrée complète des neuf commandes `var`, `eq`, `unit`, `verify`, `calc-defaults`, `domain`, `from-level`, `var-table`, `distance`, reprise du premier jet du prototype (huit commandes) et complétée pour `from-level`, chaque argument de la signature ayant sa phrase, son statut, son groupe et deux ou trois exemples, chaque argument à valeurs ayant ses valeurs et leurs phrases, chaque argument sa **propre** description.
- **Source** : T3, T4, T19, T26
- **Priorité** : doit
- **Critère d'acceptation** : pour ces neuf commandes, chaque nom de la signature de `lib/` (`command_docs.arguments`) a une entrée, en trois langues ; `label` et `label-position` (et tout couple jusqu'ici partagé) ont des textes différents ; aucun texte ne contient « spec », « REQ-» ou « (v0. ».

### REQ-003 — Source de vérité : le `///` pour la structure, le JSON pour les textes courts
- **Exigence** : la signature, l'ordre des arguments, les valeurs par défaut, les types et la référence longue restent lus du bloc `///` et de la signature de `lib/` ; `command-pages.json` ne les répète pas. Woodcore doit refuser (test) tout désaccord entre les deux : un argument nommé dans le JSON que la signature n'a plus, un argument de la signature sans entrée (pour une commande déjà récrite), une valeur fine du JSON absente de `lib/display-presets.json` (`fine-values`) ou l'inverse.
- **Source** : T38, principe « une seule source » (CLAUDE.md, règle 1)
- **Priorité** : doit
- **Critère d'acceptation** : renommer un argument dans `lib/formula.typ` sans toucher au JSON fait échouer `tests/test_commands.py` en nommant la commande et l'argument ; idem pour une valeur fine ajoutée dans `display-presets.json` sans phrase ni rendu.

### REQ-004 — Repli pour les commandes pas encore récrites
- **Exigence** : la réponse à Q-002 supprime le repli : à la fin de cette spécification, **toute commande publique a une entrée** dans `command-pages.json` et **aucune page longue ne subsiste** (ni dans l'onglet, ni sur le site, ni le code qui la composait : `argument_table` d'aujourd'hui, `fill_detail` long, `types_html`, le résumé tiré du bloc `///`). Pendant les pas intermédiaires seulement (inféré : les catégories arrivent l'une après l'autre dans des sessions séparées), une commande sans entrée garde la page d'aujourd'hui, afin que chaque pas laisse une fenêtre et un site qui fonctionnent ; ce repli est une dette déclarée, retirée au dernier pas, et un test final (activé à ce pas) refuse toute commande publique sans entrée.
- **Source** : T19, T36, T38, réponse à Q-002 (24.10.2026)
- **Priorité** : doit
- **Critère d'acceptation** : un test ouvre la page de chaque commande du catalogue sans exception, à chaque pas ; au dernier pas `tests/test_command_pages.py` échoue pour toute commande publique sans entrée (planté : retirer `find` du JSON), et `grep` ne trouve plus ni `argument_table` ni la composition longue dans `commands_tab.py` ni `website/build.py`.

### REQ-005 — Rendus pré-compilés des valeurs
- **Exigence** : `calc/tools/build_examples.py` doit écrire et compiler, comme les exemples (même copie du moteur, mêmes données figées `examples/data/`), un document par commande × argument à valeurs × valeur (y compris `auto` pour chaque valeur fine, au niveau 2 du rapport) dans chaque langue retenue (Q-001) ; l'appel et ses lignes de mise en place viennent de `command-pages.json` (écrits à la main, texte de l'appel traduit) ; un appel par paragraphe ; rognage à l'encre ; détection des rendus identiques d'un même argument (`same`) et des rendus vides (`blank`) ; résultat rangé sous `examples/out/values/` avec une carte JSON (appel, mise en place, image, `same`, `blank`). Un appel qui ne compile pas fait échouer la construction en nommant commande, argument, valeur et langue.
- **Source** : T22, T33, T34
- **Priorité** : doit
- **Critère d'acceptation** : après `build_examples` sur la catégorie « Calculer dans le rapport », la carte compte 203 valeurs pour les huit commandes du prototype (+ celles de `from-level`, s'il en prend), dans chacune des trois langues ; `display: "none"` et `level: 0` sont `blank` ; `level: auto` et `level: 2` sont `same` l'un de l'autre. La carte garde le condensat de chaque appel (comme `source_hash` des exemples) : un appel changé sans régénération est `stale`, nommé par un test. Le poids des PNG est mesuré après chaque catégorie et reporté au §16 (CON-004).

### REQ-006 — Écriture des valeurs fines
- **Exigence** : tout appel montré (bulle, tableau, appels à copier issus de `command-pages.json`) doit écrire les valeurs fines entre guillemets, `"none"` compris, `auto` sans guillemets, `none` sans guillemets pour les arguments qui le prennent.
- **Source** : T31
- **Priorité** : doit
- **Critère d'acceptation** : un test lit chaque appel de `command-pages.json`, retient les arguments de `fine-values` et vérifie la règle ; le même appel passe `check-fine` à la compilation.

### REQ-007 — Complétude des valeurs et des rendus
- **Exigence** : Woodcore doit tenir complets (test) : chaque valeur de chaque argument à valeurs d'une commande récrite a sa phrase (trois langues), son appel et son rendu dans chaque langue retenue ; les arguments à texte libre n'ont ni rendu ni valeur énumérée mais un exemple de texte.
- **Source** : T22, T34
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_commands.py` énumère commande × argument × valeur × langue et nomme le premier manquant ; il compile aussi chaque exemple d'argument (T36).

### REQ-008 — Un seul niveau pour un exemple identique
- **Exigence** : le générateur doit comparer les pages des niveaux 1, 2 et 3 d'un exemple, n'en garder qu'une quand elles sont identiques et conserver le résultat (« same12 », « same23 », « same123 ») pour l'onglet et le site, qui disent « Les trois niveaux impriment la même page. » ou « Les niveaux 1 et 2 impriment la même page. ». La déclaration à la main `LEVELS_CONFOUNDED` reste la référence de `tests/test_command_levels.py` ; le résultat mesuré s'y ajoute et un désaccord entre les deux est signalé par un test.
- **Source** : T10, T27, T36
- **Priorité** : doit
- **Critère d'acceptation** : pour un exemple de `show-annexes` (niveaux 2 et 3 égaux) un seul PNG existe pour 2 et 3 et la mention est lisible dans l'onglet ; un exemple aux trois pages différentes garde 1 · 2 · 3.

### REQ-009 — Catégories par tâche
- **Exigence** : `build_reference_lib.CATEGORIES` et `calc/i18n/reference.json` (nom et introduction de chaque catégorie, en trois langues) doivent suivre l'ordre par tâche de T24, « Écrire un modèle » en dernier avant « Internes » ; chaque commande publique est dans une seule catégorie. Réponse à Q-003 (A) : les noms de l'issue sont gardés (1. Calculer dans le rapport, 2. Imprimer un dessin ou un objet, 3. Lire les données du projet, 4. Le document et ses citations, 5. Écrire un modèle, 6. Internes) ; les huit commandes de traduction `t*`, `report-level`, `uniform-level` et `show-masked` restent dans « Le document et ses citations » ; la catégorie 5 ne contient que les six `fmt-*` et `render-*`. Les clés de `CATEGORIES` restent `formula`, `display`, `data`, `document`, `format`, `internal` (aucun fichier à renommer) : seul l'ordre change (`document` avant `format`) et `reference.json` reçoit les nouveaux noms et introductions en fr, de, en. L'arbre de l'onglet, la navigation du site et la palette de commandes (#83) lisent le même ordre.
- **Source** : T7, T24
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_commands.py` (CATEGORIES dans les deux sens) passe ; l'arbre de l'onglet et la barre latérale du site listent les mêmes catégories dans le même ordre, avec le nombre de commandes ; `from-level` figure dans « Calculer dans le rapport ».

### REQ-010 — Références internes sorties des blocs `///`
- **Exigence** : les renvois « spec …, REQ-… », « (v0.87) » et semblables des blocs `///` de `lib/` doivent passer en commentaires `//` au-dessus du bloc, sans changer la signature ni les fences d'exemple.
- **Source** : T11, T16
- **Priorité** : doit
- **Critère d'acceptation** : un test refuse dans un bloc `///` (et dans sa traduction de `commands.json`) un motif `spec 20`, `REQ-`, `ARCH-`, `Q-0`, `D-` ; les exemples compilent comme avant (`tests/test_commands.py`).

### REQ-011 — Recherche
- **Exigence** : le champ « Chercher une commande… » doit chercher dans le nom de la commande et sa phrase d'introduction (`lead`), dans la langue de la fenêtre ; pas dans les arguments ni les valeurs. (Pendant les pas intermédiaires, une commande sans entrée se cherche par son nom et la première phrase de son bloc `///` localisé.)
- **Source** : T18, T24
- **Priorité** : doit
- **Critère d'acceptation** : test sur `commands_tab.matches` : « moment » en français trouve une commande dont le `lead` français le contient ; un nom d'argument seul ne trouve rien.

### REQ-012 — Rien ne se compile à l'ouverture d'une page
- **Exigence** : ouvrir une page ou survoler une valeur ne doit lancer aucune compilation Typst pour la catégorie récrite ; seule la voie B de Q-001, si elle est retenue, et les exemples hors de l'allemand (v0.94, existants) compilent à la demande.
- **Source** : T5, T35
- **Priorité** : doit
- **Critère d'acceptation** : test avec Typst absent du PATH : la page de `var` s'ouvre, la bulle d'une valeur donne l'appel et l'image (Q-001 A) ; un message le dit quand une image manque (carte absente ou périmée : jamais de compilation silencieuse). Les exemples hors de l'allemand gardent leur compilation à la demande (v0.94), inchangée.

### REQ-013 — Les 54 commandes publiques ont leur page condensée, écrite à la main
- **Exigence** : chaque commande publique de `build_reference_lib.CATEGORIES` doit avoir, dans `command-pages.json`, une entrée de la qualité de celle de `var` (réponse à Q-002), écrite **à la main** en fr, de, en à partir de son bloc `///` et de `commands.json` (jamais déduite par un script, jamais copiée telle quelle d'un bloc), **sans** renvoi interne (« spec », « REQ- », « (v0.xx) »). Par catégorie, avec les arguments à écrire (puces des blocs `///`, relevées le 24.10.2026) : **« Calculer dans le rapport » 9 commandes, 89 puces** (`var`, `eq`, `unit`, `verify`, `calc-defaults`, `domain`, `from-level`, `var-table`, `distance`) ; **« Imprimer un dessin ou un objet » 11 commandes, 62 puces** (`image-positions-plan`, `image-fire-plan`, `image-static-model`, `image-schema`, `image-extract`, `image-polar-moment`, `image-section`, `image-legend`, `image-titleblock`, `show-annexes`, `position`) ; **« Lire les données du projet » 8 commandes, 13 puces** (`find`, `sync`, `domain-file`, `ids`, `project-info`, `plans-of`, `journal-entries`, `get`) ; **« Le document et ses citations » 20 commandes, 29 puces** (`show-bibliography`, `cite-norm`, `show-norm-list`, `set-report-language`, `report-language`, `report-lang`, `woodcore-document`, `caption-rules`, `doc-tables`, les huit `t*`, `report-level`, `uniform-level`, `show-masked`) ; **« Écrire un modèle » 6 commandes, 8 puces** (`fmt-number`, `fmt-value`, `fmt-decimals`, `render-symbol`, `render-formula`, `render-prose`). Pour chaque entrée : un `lead` d'une phrase, 3 ou 4 `keys`, pour chaque argument de la signature un groupe, un statut, sa **propre** phrase et 2 ou 3 exemples, pour chaque argument à valeurs finies toutes ses valeurs (phrase, appel, rendu), et `named` pour l'écriture nommée d'un argument de la ligne. Une commande dont l'appel n'imprime rien (accesseur : `find`, `ids`, `get`, `project-info`, `plans-of`, `journal-entries`, `domain-file`, les `t*` et `fmt-*` qui rendent une valeur) montre dans ses exemples et ses rendus un appel entouré d'une impression explicite (`#repr(…)`, `#raw(…)`), écrit à la main ; une commande qui ne règle qu'un état (`set-report-language`, `calc-defaults`, `caption-rules`) montre ce que la ligne qui la suit imprime.
- **Source** : réponse à Q-002 (24.10.2026), T3, T19, T24, T33
- **Priorité** : doit
- **Critère d'acceptation** : pour chacune des cinq catégories, `tests/test_command_pages.py` énumère commande × argument × langue et nomme le premier manquant ; chaque argument de chaque signature a sa phrase propre (aucun texte identique pour deux arguments d'une commande) ; aucune entrée ne contient `spec `, `REQ-`, `(v0.` ; `keys` compte 3 ou 4 entrées ; chaque argument a 2 ou 3 exemples (hors ceux de `named`) ; les 54 commandes figurent dans la carte des rendus pour leurs arguments à valeurs ; l'ingénieur relit une page par catégorie dans l'onglet avant la clôture de la catégorie (§14).

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Une seule vue, trois volets, ni module d'état ni bulle de norme
- **Exigence** : l'onglet n'a que la documentation : à gauche la liste, au centre la page, à droite les lignes à copier ; il n'a ni vue « Affichage », ni module « État de la commande », ni bulle de norme. Le sélecteur de langue de la fenêtre change tous les textes de la page et les rendus des valeurs (selon Q-001).
- **Source** : T6, T12, T13, T23
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_window.py` : l'onglet n'a pas de sélecteur de vues ; aucun ⓘ de norme n'y paraît ; changer la langue change le `lead` et les phrases.

### UI-002 — Volet de gauche
- **Exigence** : champ de recherche (REQ-011), catégories par tâche (REQ-009), nom en chasse fixe et phrase d'introduction coupée par « … » sur la ligne, nombre de commandes à droite du titre de catégorie ; « Internes » repliée, inchangée.
- **Source** : T24
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de l'arbre (catégories, nombre, ligne à deux niveaux de texte) ; capture visuelle à comparer au prototype.

### UI-003 — En-tête et ligne de la commande
- **Exigence** : l'en-tête montre `#nom`, l'étiquette de la catégorie et le `lead` ; la ligne de la commande est un bloc de code sur plusieurs lignes, arguments groupés comme le tableau (ceux de la ligne d'abord, puis par groupe), argument obligatoire en gras, nom d'argument souligné en pointillé, chaque valeur par défaut dans une petite boîte avec ▾, et la ligne d'aide « Survolez un argument : … Un clic garde la bulle ouverte. ».
- **Source** : T14, T25
- **Langues** : fr / de / en (l'aide, l'étiquette ; le code est invariant)
- **Critère d'acceptation** : la ligne produite pour `var` est celle de T25 (ordre, groupes, défauts lus de la signature) ; test sur le texte généré indépendant de Qt.

### UI-004 — « L'essentiel »
- **Exigence** : trois ou quatre cartes (titre en gras, deux lignes) par commande récrite, venues de `keys` ; ce qui ne sert qu'à un cas rare n'y est pas.
- **Source** : T25
- **Langues** : fr / de / en
- **Critère d'acceptation** : `keys` de chaque commande récrite compte 3 ou 4 entrées (test).

### UI-005 — Tableau des arguments
- **Exigence** : tableau à trois colonnes (Argument · Statut · Ce qu'il fait, et des exemples), en groupes (« Les arguments de la ligne », « Ce qui est imprimé », « Libellé et description », « Citation », « Autres ») ; statut « obligatoire » (pastille rouge) ou « optionnel » avec la valeur par défaut dans une boîte ▾ qui ouvre la même bulle que dans la ligne ; une phrase puis deux ou trois exemples, un par ligne (code à gauche, ce qu'il montre à droite) ; dernière ligne « Écrits par leur nom » (`name-calc`, `name-visible`, `value`, `equation`, `norm-ref`, `..rest` quand ils ne sont que l'écriture nommée d'un argument de la ligne ; `name-calc` et `name-visible` de `verify` gardent leur ligne).
- **Source** : T15, T26
- **Langues** : fr / de / en
- **Critère d'acceptation** : test sur le modèle du tableau de `var` et de `verify` (groupes, statut, 2 à 3 exemples par argument, ligne « Écrits par leur nom » avec les bons membres).

### UI-006 — Bulle d'un argument
- **Exigence** : survoler un nom d'argument (ligne ou tableau) ouvre une bulle étroite (380 px) : en-tête sur une ligne (nom seul dans sa boîte, puis « optionnel · par défaut auto » ou « obligatoire » en petit et gris, sans cadre autour de l'en-tête), puis sa phrase.
- **Source** : T21, T28, T30
- **Langues** : fr / de / en
- **Critère d'acceptation** : test du contenu de la bulle (texte, langue) ; vérification visuelle de l'en-tête.

### UI-007 — Bulle des valeurs
- **Exigence** : survoler une valeur ouvre une bulle large (jusqu'à 860 px) : le même en-tête ; deux colonnes — la liste des valeurs avec leur phrase, la valeur courante en surbrillance, puis pour la valeur survolée l'appel Typst (mise en place en gris, appel en noir) et « Ce qu'il imprime » avec le rendu ; survoler une autre ligne change l'aperçu sans délai ; messages « Imprime la même chose que N. » (`same`), « Le rôle ne change pas la ligne : il dit à #var-table où la ranger. » (`role`, sauf dans `var-table`), « Rien n'est imprimé. » (`blank`), « Un texte libre, par exemple : … » (argument libre, sans rendu) ; pied « Compilé une fois par le moteur de Woodcore, sur les données figées des exemples. ».
- **Source** : T22, T29, T33
- **Langues** : fr / de / en
- **Critère d'acceptation** : test du modèle de la bulle pour `var.display`, `var.level`, `var.role`, `var-table.role`, `var.label` (cinq cas) ; vérification visuelle du survol.

### UI-008 — Tenue de la bulle
- **Exigence** : ouverte au survol, elle reste ouverte quand la souris y entre (fermeture 300 ms après la sortie) ; un clic la garde ouverte ; Échap, un clic ailleurs ou le défilement la ferment ; elle s'ouvre sous l'élément, au-dessus faute de place, sans sortir de l'écran. Au clavier : le nom et la valeur sont atteignables au Tab et la bulle s'ouvre au focus (inféré, accessibilité).
- **Source** : T30
- **Langues** : sans objet
- **Critère d'acceptation** : test Qt (pytest-qt si le projet l'emploie) : entrer dans la bulle annule la fermeture, Échap la ferme, le clic la fixe.

### UI-009 — Exemples
- **Exigence** : les exemples restent ceux d'aujourd'hui (fences `///` inchangées), code et page compilée ; boutons 1 · 2 · 3 là où les niveaux diffèrent ; sinon une page et la mention de REQ-008.
- **Source** : T9, T16, T27
- **Langues** : fr / de / en
- **Critère d'acceptation** : voir REQ-008 ; aucune fence de `lib/` modifiée (diff).

### UI-010 — Volet de droite
- **Exigence** : « Lignes à copier » (appel minimal et appel complet de `command_docs.calls`, chacun avec « Copier ») ; « Exemples » (liste numérotée de leur première ligne ; un clic mène à l'exemple et le fait clignoter) ; « Dans ce projet » (appels de la commande dans le projet d'exemple, `fichier:ligne` et code, douze au plus). Pas de module d'état.
- **Source** : T13, T32
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : les deux appels sont ceux de `command_docs.calls` ; « Dans ce projet » pour `var` rend au plus douze entrées lues de `tests/projet-exemple/` (jamais d'un projet de l'ingénieur) ; le clic sur un exemple appelle le défilement.

### UI-011 — Le site montre la même page
- **Exigence** : `website/build.py` doit lire `command-pages.json` et les rendus des valeurs et produire la même page condensée : ligne de la commande, cartes, tableau, bulles au survol du pointeur et au toucher sur mobile, rendus des valeurs, catégories par tâche, recherche par nom et `lead`. Une commande non récrite garde sa page actuelle (REQ-004).
- **Source** : T20, T36
- **Langues** : fr / de / en (site en trois langues)
- **Critère d'acceptation** : `python website/build.py` construit sans erreur ; la page `var` de chaque langue contient la ligne de la commande, les cartes et les bulles ; le test du site existant passe et vérifie que chaque image référencée existe.

## 5. Exigences d'architecture

### ARCH-001 — Logique hors de Qt
- **Exigence** : la composition de la page (ligne de la commande, groupes, statut, cartes, contenu des bulles, résolution `same`/`blank`/`role`/texte libre, repli, recherche) doit vivre dans `calc/tools/command_docs.py` (ou un module voisin sans Qt), lue par l'onglet et par `website/build.py` ; l'onglet n'affiche que. Une seule source pour l'onglet et le site.
- **Source** : principe « domain logic is independent of the UI », docs/architecture/principles.md ; CLAUDE.md « Une seule source »
- **Critère d'acceptation** : les tests du contenu de page (UI-003 à UI-007) s'exécutent sans Qt ; `website/build.py` n'importe pas Qt.

### ARCH-002 — Brique de bulle partagée
- **Exigence** : la bulle (ouverte au survol, qui reste ouverte sous la souris, clic pour la fixer, Échap, placement) doit être une brique commune réutilisable par l'onglet Domaines (#113) et l'onglet Variables (#114), sur le modèle de `norm_bubble.BubbleController` (fenêtre outil qui ne prend pas le focus) et non d'un `QToolTip`, qui ne reste pas ouvert. Le choix du widget de la ligne de la commande (`QTextBrowser` à ancres ou widget dessiné) est tranché par la revue d'architecture.
- **Source** : T36, T38, T39
- **Critère d'acceptation** : la brique n'importe rien de `commands_tab` ; un second usage de test l'emploie sans le contenu des commandes.

### ARCH-003 — Rendus des valeurs dans le dispositif des exemples
- **Exigence** : une seule chaîne produit exemples et rendus de valeurs (`build_examples.py`, `command_preview.document`, copie du moteur, `examples/data/`) ; aucun second dispositif de compilation. Le script du prototype (`gen_vals.py`) sert de modèle, non de code livré : ses textes de traduction du `T` vivent dans `command-pages.json`, pas dans le script.
- **Source** : T33, T34 ; règle « No hardcoding »
- **Critère d'acceptation** : `build_examples.py` expose une fonction de rendu des valeurs appelée par `main()` ; aucun texte d'appel en dur dans `calc/tools/*.py` (revue).

### ARCH-004 — Contrat versionné
- **Exigence** : `command-pages.json` porte `schema_version` et un schéma dans `schemas/` ; la carte des rendus (`examples/out/values/`) en porte un aussi (inféré, règle « every exported JSON follows a schema »).
- **Source** : CLAUDE.md « Explicit, versioned data models »
- **Critère d'acceptation** : deux schémas, validés par le test de complétude.

### ARCH-005 — Mots de la fenêtre
- **Exigence** : les mots nouveaux de l'onglet (aide de la ligne, en-têtes de groupe, statuts, messages de la bulle, mentions de niveaux) vont dans le `STRINGS` de l'onglet, en fr, de, en (`tests/test_i18n.py`) ; les mots de page partagés avec le site vont dans `calc/i18n/reference.json` (`command_docs.word`). Les mots qui ne servent plus sont retirés.
- **Source** : T37 ; CLAUDE.md « No hardcoding »
- **Critère d'acceptation** : `tests/test_i18n.py` passe ; pas de clé orpheline.

### ARCH-006 — Palette de commandes
- **Exigence** : la palette (#83, `command_palette.py` navigue déjà vers `tab_commands` par nom) reste valide ; elle peut lire le `lead` de `command-pages.json`, sans le recopier.
- **Source** : T39
- **Critère d'acceptation** : `tests/test_command_palette.py` passe.

### ARCH-007 — Un onglet de composants simples, prêt pour `DataTab` (#106)
- **Exigence** : `CommandsTab` doit rester un `QWidget` mince qui assemble trois composants sans classe de base commune, chacun construit sur un petit contexte (`app`, `t`, `lang`, police, enregistrements, échantillons) et offrant `state()`, `restore(state)`, `shown()`, `hidden()` : la liste (recherche et arbre), la page (ligne de la commande, cartes, tableau, exemples) et le volet de droite (lignes à copier, liste des exemples, « Dans ce projet »). Ils se parlent par des signaux (commande choisie, exemple choisi), jamais par référence ; aucun n'importe `tab_host`, ni `woodcore_gui`. #106 en fera trois `tab_host.Service` dont `mount(ctx)` rend ces widgets, sans les réécrire ; `commands_tab.py` ne définit ni `dirty` ni méthode de phase propre à l'onglet. La compilation à la demande des exemples (`RenderJob`, `QTimer`) vit dans la page et s'arrête dans `hidden()`.
- **Source** : revue d'architecture ; consigne de #106 (spec `2026-10-24-type-donnees`, REQ-005, CON-004)
- **Critère d'acceptation** : un test construit chaque composant seul, sans `CommandsTab` ; `grep tab_host` sur `calc/tools/command_*.py` et `commands_tab.py` ne trouve rien ; `view_state` de l'onglet est la réunion des `state()`.

### ARCH-008 — Modèle de page unique pour la fenêtre et le site
- **Exigence** : la ligne de la commande, les groupes et lignes du tableau, les cartes, le contenu des bulles (en-tête, valeurs, appel, rendu, messages `same` / `blank` / `role` / texte libre) et le résultat de recherche doivent être produits par des fonctions pures, sans Qt, de `calc/tools/command_page.py` (modèle) et `calc/tools/command_pages.py` (lecture, validation, accord avec `lib/`), sous forme de données (listes, dicts) que l'onglet transforme en widgets et `website/build.py` en HTML. Tous les mots du modèle (messages, en-têtes de groupe, statuts) sont dans `reference.json` (`command_docs.word`), une seule fois pour les deux sorties ; `STRINGS` de l'onglet ne garde que le décor propre à la fenêtre.
- **Source** : revue d'architecture ; principe « une seule source » ; ARCH-001, ARCH-005
- **Critère d'acceptation** : les tests du modèle tournent sans PySide6 importé (`'PySide6' not in sys.modules`) ; `website/build.py` consomme le même modèle ; aucun mot du modèle n'est dans `STRINGS`.

### ARCH-009 — Rendus en planches par commande et par langue
- **Exigence** : les rendus des valeurs sont gardés **en une planche PNG par commande et par langue** (`examples/out/values/<langue>-<commande>.png`, 32 couleurs, rognée à l'encre, une ligne par appel) et une carte `examples/out/values/index.json` (rectangle de chaque valeur dans la planche, condensat de l'appel, `same`, `blank`) ; ni PNG par valeur, ni nom de fichier calculé à la main. L'onglet découpe la planche (`QPixmap.copy`), le site la découpe par CSS ; ni l'un ni l'autre ne recompose un chemin. Un changement d'un seul appel ne recompile que la planche de sa commande et de sa langue (condensat par planche).
- **Source** : revue d'architecture ; §9 (sprite contre un PNG par valeur) ; CON-004
- **Critère d'acceptation** : le nombre de fichiers de `examples/out/values/` est de 3 × (nombre de commandes à valeurs) + la carte ; un test relit la carte et recoupe chaque rectangle avec la taille réelle de la planche ; Pillow (déjà dans `requirements.txt`) fait la quantification, sans nouvelle dépendance.

### ARCH-010 — Isolation des appels d'une planche
- **Exigence** : les appels d'une planche, rendus dans un même document (un paragraphe chacun), ne doivent pas se contaminer (`calc-defaults` est un réglage d'état ; deux `#var("S", …)` du même nom ; compteurs). Chaque appel est donc écrit à la main avec ses lignes de mise en place **dans un bloc de contenu isolé**, avec des noms uniques par appel ; une commande dont l'état fuit malgré cela est compilée un document par appel (`"isolate": true` dans son entrée), cas à déterminer dès `calc-defaults` et `var`. Le dispositif reste celui de ARCH-003.
- **Source** : revue d'architecture
- **Critère d'acceptation** : un test de contamination plante un appel `calc-defaults` avant un appel `var` et vérifie que ce dernier imprime comme seul ; la carte dit pour chaque planche si elle est isolée par appel.

### ARCH-011 — Niveaux égaux : mesuré, comparé à la déclaration
- **Exigence** : `build_examples` mesure l'égalité des pages d'un exemple (condensat du PNG, `same12`, `same23`, `same123`) et l'écrit dans `index.json` des exemples (champ additif, `schema_version` relevé) ; `tests/test_command_levels.py` recoupe ce résultat avec `LEVELS_CONFOUNDED` (la déclaration à la main reste, REQ-008) et signale tout désaccord dans les deux sens.
- **Source** : revue d'architecture ; REQ-008
- **Critère d'acceptation** : planté : un exemple de `show-annexes` mesuré différent de sa déclaration fait échouer le test en nommant la commande.

## 6. Contraintes

- **CON-001** — Les exemples et leurs fences ne changent pas ; les pages des exemples restent celles du générateur. Source : T16, T27.
- **CON-002** — Tous les rendus sont compilés sur les données figées `examples/data/`, jamais sur un projet de l'ingénieur. Source : T8, T22, T34.
- **CON-003** — Les rendus des valeurs, comme les exemples, sont produits avec la copie du moteur de `examples/` (`refresh_engine`) ; un changement du moteur oblige à les régénérer, comme aujourd'hui. Source : T33 (inféré de §10sexies).
- **CON-004** — Poids du dépôt (réponse à Q-001, A : trois langues committées) : les PNG committés (aujourd'hui 4,9 Mo pour les exemples) croissent de ≈ 4,6 Mo pour la première catégorie (prototype, 203 valeurs × 3 langues) et, par extrapolation à 54 commandes, de **10 à 25 Mo en tout** (estimation, non mesurée : les commandes `image-*` rendent des dessins plus lourds). Le projet vit dans OneDrive et est cloné par les développeurs : une **butée de 30 Mo** pour `examples/out/values/` est posée, mesurée après chaque catégorie (§14) ; si elle est franchie, le pas suivant s'arrête et l'ingénieur choisit (moindre définition, option C de Q-001). Source : T35, revue.
- **CON-005** — Fichiers en LF, prose sur une ligne, anglais dans le code et les docs ; aucun fichier de `docs/` au-dessus de 100 Ko (hors `decisions.md`, `CHANGELOG.md`). Source : CLAUDE.md.
- **CON-006** — Un test de complétude doit pouvoir distinguer « commande récrite » de « pas encore » (REQ-004) : la présence d'une entrée dans `command-pages.json` fait foi. Inféré de T19.
- **CON-007** — Les tests travaillent sur `tests/projet-exemple/` ; aucune écriture dans `../Musterprojekt/`. Source : CLAUDE.md.
- **CON-008** — Sur le plan d'exécution : l'issue touche un contrat de données, le générateur, l'onglet et le site, et revient sur deux décisions de §10sexies : `/big-feature`. Source : T38.

## 7. Décisions prises

Toutes sont de l'ingénieur (issue #115, 23–24.10.2026) ; aucune n'est reposée.

- **D-1** — Pages **pré-compilées** : rien ne se compile à l'ouverture d'une page (v1, point 1 / question 1, B réponse 2). Prix : des PNG committés.
- **D-2** — **Pas de vue Affichage**, pas de module d'état, pas de bulle de norme (« trop lourd pour son utilité »).
- **D-3** — **Catégories par tâche**, commandes de modèle en dernier, pour l'onglet et pour le site (v1, point 3 / question 3, B réponse 1). Les noms 2 à 5 sont provisoires (Q-003).
- **D-4** — **Données figées partout** (v1, point 4 / question 2, A réponse 2).
- **D-5** — **Boutons 1 · 2 · 3** là où les niveaux diffèrent (v1, point 5, A) ; **un seul niveau avec mention** quand les pages sont identiques (question 6, réponse 1).
- **D-6** — **Références internes** retirées des blocs `///`, gardées en commentaires `//` (question 5, réponse 1). Prix : l'information reste dans le code, plus dans Tinymist.
- **D-7** — **Appel minimal et appel complet gardés**, à droite, avec les exemples et les appels du projet.
- **D-8** — Pages **condensées** pour **toutes** les commandes et **tous** les arguments ; tableau avec statut, phrase courte, deux ou trois exemples par ligne.
- **D-9** — **Exemples tels quels** (fences des blocs `///` inchangées).
- **D-10** — **Textes courts dans un fichier nouveau `calc/i18n/command-pages.json`** ; le bloc `///` reste la référence longue (v2, question 1, réponse 1). Prix : deux endroits parlent d'un argument ; REQ-003 les tient d'accord par un test.
- **D-11** — **Recherche par nom et phrase d'introduction** seulement (v2, question 2, réponse 1).
- **D-12** — **Les 45 autres commandes** récrites de la même façon, catégorie par catégorie (v2, question 3, réponse 1). **Modifiée le 24.10.2026** (réponse à Q-002) : elles sont **dans cette spécification**, comme pas séparés du plan, et non plus dans des lots à part ; aucun repli par une page longue ne reste à la fin.
- **D-13** — **Le site montre la même page condensée** (v2, question 4, réponse 1).
- **D-14** — **Chaque valeur de chaque argument a son appel et son rendu pré-compilé**, l'en-tête de bulle sur une ligne (mise à jour du 24.10.2026).
- **D-15** — **Les appels des valeurs vivent dans `command-pages.json`** (proposé par l'issue, jamais contesté), non comme des fences `///` d'un genre nouveau : ce sont des contenus écrits à la main, traduits, qui n'ont rien à faire dans le hover de Tinymist. Marqué « à confirmer à l'approbation » dans la revue d'architecture.
- **D-16** — Écriture des valeurs fines entre guillemets (REQ-006).
- **D-17** — **Q-001 : A, les trois langues committées** (ingénieur, 24.10.2026). Rien ne se compile à l'ouverture ni sans Typst ; `RenderJob` ne sert plus qu'aux exemples hors de l'allemand. Prix : le poids des PNG (CON-004) ; §10sexies « Rendered in German, once » ne vaut plus que pour les exemples.
- **D-18** — **Q-002 : pas de repli, une page condensée soignée pour chacune des commandes** (ingénieur, 24.10.2026) : « page condensée bien pensée, comme pour la commande var (prends le temps de faire ce travail) ». Étend le périmètre aux 54 commandes (REQ-013) ; la page longue disparaît (REQ-004).
- **D-19** — **Q-003 : A** (ingénieur, 24.10.2026) : les noms de l'issue sont gardés ; `t*`, `report-level`, `uniform-level`, `show-masked` restent dans « Le document et ses citations » ; « Écrire un modèle » ne contient que `fmt-*` et `render-*`.
- **D-20** — (revue d'architecture) Le widget de la ligne de la commande est un **`QTextBrowser` en lecture seule à ancres**, la bulle un **`QFrame` outil sans focus** de la nouvelle brique `hover_bubble.py`, jamais un `QToolTip` (ARCH-002) ; planches PNG par commande et par langue (ARCH-009).

À reporter dans `docs/decisions.md` §13 à la fin : vue Affichage non livrée, textes courts hors des blocs `///`, catégories par tâche, rendus pré-compilés en trois langues committées (D-17), pas de page de repli (D-18), brique de bulle et planches (D-20).

## 8. Hors périmètre

- L'onglet **Domaines (#113)**, l'onglet **Variables (#114)**, les **contrôles d'éléments (#112)** et la migration des onglets de données vers une base commune (**#106**) : cette spécification ne les modifie pas ; elle ne fait que fournir la brique de bulle (ARCH-002) et le fichier de rendus, que #113 pourra réutiliser.
- La **palette de commandes (#83)** : seulement sa lecture éventuelle du `lead` (ARCH-006) ; son contenu et son comportement ne changent pas.
- Une vue « Affichage » ou « Données » de l'onglet, un module d'état, une bulle de norme (D-2).
- Une recherche dans les arguments ou les valeurs (D-11).
- Un changement de la sémantique des commandes Typst, de leur signature ou de leurs exemples.
- La migration de l'onglet sur `DataTab` (#106) et le cadre sans cas de `TabHost` (#107) : ici seulement la forme qui la rend triviale (ARCH-007).

## 9. Idées non retenues comme exigences

- Le **sprite par commande et par langue** (une image, une carte de positions) du prototype, contre **un PNG par valeur** : tranché par la revue d'architecture en faveur des planches (ARCH-009, ARCH-RISK-002) ; le prototype montre 24 sprites pour 4,6 Mo en 32 couleurs.
- La **palette de commandes** montrant le `lead` (issue #83, « pourrait ») : idée, non exigence.
- Réutilisation de la bulle des valeurs par le **formulaire de l'onglet Domaines** (#113, « pourrait réutiliser ») : idée ; seule la brique commune est exigée (ARCH-002).
- Le **chemin d'accès au prototype** (copie dans `docs/requirements/prototypes/2026-10-24-onglet-commandes/`) est une tâche de documentation (§11), pas une exigence du produit.

## 10. Questions

### Q-001 — Rendus des valeurs : trois langues committées, ou l'allemand seul committé et le reste compilé à la demande ?
- **Contexte** : aujourd'hui les pages des exemples sont committées en allemand seulement ; dans une fenêtre française ou anglaise, Woodcore les compile à la demande avec Typst et les garde dans un cache (v0.94). Pour les rendus des valeurs de la bulle, on peut soit committer les trois langues (≈ 4,6 Mo pour cette catégorie, peut-être 25 Mo pour tout le catalogue), soit committer l'allemand et compiler le français et l'anglais au premier survol.
- **Pourquoi elle compte** : elle fixe la taille du dépôt, la règle « rien ne se compile à l'ouverture » (D-1) et le comportement sans Typst installé ; elle change `build_examples.py`, `RenderJob` (qui disparaît ou reste), le test de complétude (REQ-007) et §10sexies (« Rendered in German, once »).
- **Options** :
  - **A (recommandée)** — les trois langues committées, rangées en images par commande et par langue : rien ne se compile jamais, la bulle répond sans délai, Typst peut être absent ; le dépôt grossit (≈ 5 Mo pour cette catégorie, jusqu'à ≈ 25 Mo pour toutes) et `RenderJob` reste seulement pour les exemples.
  - **B** — l'allemand committé, le français et l'anglais compilés à la demande et mis en cache comme les exemples : le dépôt ne grossit que d'un tiers ; le premier survol d'une valeur en français attend une compilation (une demi-seconde à une seconde) et exige Typst, ce qui contredit D-1.
  - **C** — les trois langues committées mais en moindre définition ou en plus peu de couleurs (déjà 32 dans le prototype) : mêmes avantages que A, poids réduit ; le texte des rendus peut devenir moins net.
- **Réponse : A — les trois langues committées (ingénieur, 24.10.2026)** : rien ne se compile à l'ouverture, la bulle répond sans délai, Typst peut être absent.

### Q-002 — Que montrer pour une commande pas encore récrite ?
- **Contexte** : tant que les 44 autres commandes n'ont pas d'entrée dans `command-pages.json`, leur page doit exister (REQ-004). Deux formes sont possibles : l'ancienne page longue (résumé, arguments et valeurs tirés du bloc `///`), ou une page condensée de même mise en forme dont on déduit les textes du bloc `///`.
- **Pourquoi elle compte** : elle fixe le travail de `command_docs.py` et du site, et ce que l'ingénieur voit pendant plusieurs lots : deux mises en page côte à côte, ou une seule avec des textes de qualité inégale.
- **Options** :
  - **A (recommandée)** — l'ancienne page longue, inchangée : aucun risque de texte mal déduit, pas de code jetable, le contraste signale ce qui reste à récrire ; l'onglet a deux présentations pendant la transition.
  - **B** — la page condensée avec la ligne de la commande et le tableau (signature, types, défauts) et le texte long des blocs `///` en phrase d'argument : une seule présentation ; des phrases longues et des renvois internes mal découpés, et du code qui disparaît à la fin.
- **Réponse : ni A ni B (ingénieur, 24.10.2026)** : « page condensée bien pensée, comme pour la commande var (prends le temps de faire ce travail) ». Chaque commande de chaque catégorie reçoit une page condensée écrite à la main, en fr, de, en, aussi soignée que `var` ; aucune page longue de repli ne reste. Le périmètre s'élargit à 54 commandes : REQ-013, D-18 et les pas séparés du §14.

### Q-003 — Noms et composition des catégories 2 à 5, et place des commandes de traduction
- **Contexte** : l'issue donne l'ordre et un contenu provisoire : 1. Calculer dans le rapport, 2. Imprimer un dessin ou un objet, 3. Lire les données du projet, 4. Le document et ses citations, 5. Écrire un modèle, 6. Internes. Aujourd'hui les huit commandes de traduction (`t`, `tl`, `t-str`, `tl-str`, `t-label`, `t-pattern`, `t-of`, `tl-of`) sont dans la catégorie « document », avec `report-level` et `uniform-level` ; `show-masked`, `report-level`, `uniform-level` n'ont pas de place dans la liste de l'issue.
- **Pourquoi elle compte** : elle fixe `CATEGORIES`, `reference.json` (trois langues), l'arbre et le site ; chaque commande doit avoir une seule place, et le prochain lot hérite du découpage.
- **Options** :
  - **A (recommandée)** — garder les noms de l'issue ; les commandes de traduction, `report-level`, `uniform-level` et `show-masked` restent avec « Le document et ses citations » (où elles sont aujourd'hui) et la catégorie 5 ne contient que les six commandes `fmt-*` et `render-*` : le moins de déplacements.
  - **B** — mettre les commandes de traduction en catégorie 5 « Écrire un modèle », puisqu'un modèle les emploie pour ses mots : regroupement par usage, mais `t` et `tl` quittent le document où on les cherche aujourd'hui.
  - **C** — une catégorie propre « Les mots et les langues » pour `t*`, `*-language` et `report-lang` : lisible, mais une catégorie de plus (sept) dans l'arbre.
- **Réponse : A — les noms de l'issue ; les commandes de traduction restent avec « Le document et ses citations », la catégorie 5 ne contient que `fmt-*` et `render-*` (ingénieur, 24.10.2026).**

## 11. Critères d'acceptation

- [x] REQ-001 — `command-pages.json` validé contre son schéma ; champ et langue manquants nommés.
- [x] REQ-002 — neuf commandes de « Calculer dans le rapport » complètes en fr, de, en ; descriptions d'arguments distinctes ; aucun renvoi interne.
- [x] REQ-003 — un désaccord entre `lib/` et le JSON (argument, valeur fine) fait échouer un test.
- [x] REQ-004 — chaque commande du catalogue ouvre une page à chaque pas ; au dernier pas aucune page longue ne subsiste et toute commande publique a son entrée.
- [x] REQ-005 — rendus des valeurs générés en trois langues, carte avec condensat, `same` et `blank` ; 203 valeurs pour les huit commandes du prototype ; poids mesuré par catégorie.
- [x] REQ-006 — valeurs fines entre guillemets dans tous les appels (test + compilation).
- [x] REQ-007 — chaque valeur de chaque argument à valeurs : phrase, appel, rendu dans chaque langue retenue.
- [x] ⚠️ REQ-008 — un exemple aux niveaux identiques : une page et la mention ; sinon 1 · 2 · 3.
- [x] REQ-009 — catégories par tâche dans l'arbre, le site et `reference.json`.
- [x] REQ-010 — plus de `spec …`/`REQ-` dans les blocs `///` ni leurs traductions ; exemples inchangés et compilant.
- [x] REQ-011 — recherche par nom et `lead`.
- [x] REQ-012 — aucune compilation à l'ouverture de la page d'une commande (Typst absent du PATH).
- [x] ⚠️ REQ-013 — les 54 commandes, par catégorie (9 · 11 · 8 · 20 · 6), ont leur page à la main en trois langues, sans renvoi interne, relue par l'ingénieur.
- [x] UI-001 — une vue, trois volets, ni état ni norme.
- [x] UI-002 — volet de gauche.
- [x] UI-003 — ligne de la commande de `var` conforme à T25.
- [x] UI-004 — trois ou quatre cartes par commande récrite.
- [x] UI-005 — tableau : groupes, statut, exemples, « Écrits par leur nom ».
- [x] UI-006 — bulle d'un argument.
- [x] UI-007 — bulle des valeurs (liste, aperçu, `same`, `role`, `blank`, texte libre, pied).
- [x] ⚠️ UI-008 — tenue de la bulle (survol, clic, Échap, placement).
- [x] UI-009 — exemples et niveaux.
- [x] UI-010 — volet de droite, « Dans ce projet » (douze au plus).
- [x] UI-011 — le site montre la même page, bulles au pointeur et au toucher.
- [x] ARCH-001 — composition de la page hors Qt, partagée avec le site.
- [x] ARCH-002 — brique de bulle partagée, sans dépendance à `commands_tab`.
- [x] ARCH-003 — un seul dispositif de compilation (exemples et valeurs).
- [x] ARCH-004 — schémas versionnés pour le JSON des pages et la carte des rendus.
- [x] ARCH-005 — mots de la fenêtre en trois langues (`tests/test_i18n.py`).
- [x] ARCH-006 — palette de commandes intacte (`tests/test_command_palette.py`).
- [x] ARCH-007 — trois composants sans base commune, prêts pour `DataTab`.
- [x] ARCH-008 — modèle de page sans Qt, partagé avec le site ; mots dans `reference.json`.
- [x] ARCH-009 — planches par commande et par langue, carte recoupée.
- [x] ARCH-010 — isolation des appels d'une planche prouvée.
- [x] ARCH-011 — niveaux égaux mesurés et recoupés avec `LEVELS_CONFOUNDED`.
- [x] Documentation : `docs/typst/command-docs.md` §10sexies (la phrase « Every word of it is read out of the `///` blocks » ne tient plus ; « Rendered in German, once » ne vaut que pour les exemples ; les rendus des valeurs en trois langues), `docs/ui/tab-commands.md`, `docs/typst/api-conventions.md` si la règle 14 du §2 change, `docs/decisions.md` §13, ligne au catalogue des tests pour tout fichier de test nouveau, entrée `CHANGELOG.md`, page « Nouveautés » de la prochaine version en fr/de/en, copie du prototype dans `docs/requirements/prototypes/2026-10-24-onglet-commandes/` ; aucune commande Typst nouvelle (donc pas de `///` ni de `commands.json` à ajouter, sauf `from-level` si ses phrases changent).
- [x] Tests : `tests/test_command_pages.py` nouveau (schéma, complétude des 54 commandes, accord avec `lib/`, valeurs fines, renvois internes), `tests/test_command_page.py` nouveau (modèle de page sans Qt), `tests/test_command_values.py` nouveau (carte, planches, condensats, contamination), `tests/test_hover_bubble.py` nouveau, `tests/test_commands.py` adapté, `tests/test_command_levels.py`, `tests/test_window.py`, `tests/test_i18n.py`, test du site, test de la bulle ; tous passent.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | D-14, UI-001 | capturé |
| T2 | REQ-002, REQ-010, D-10 | capturé |
| T3 | REQ-002, §8 | capturé |
| T4 | REQ-001, REQ-002 | capturé |
| T5 | D-1, REQ-012 | capturé |
| T6 | D-2, UI-001 | capturé (rien à retirer : l'onglet n'a pas cette vue) |
| T7 | D-3, REQ-009 | capturé |
| T8 | D-4, CON-002 | capturé |
| T9 | D-5, UI-009 | capturé |
| T10 | D-5, REQ-008 | capturé |
| T11 | D-6, REQ-010 | capturé |
| T12 | D-2, UI-001 | capturé |
| T13 | D-7, UI-010 | capturé |
| T14 | D-8, UI-003 | capturé |
| T15 | D-8, UI-005 | capturé |
| T16 | D-9, CON-001, UI-009 | capturé |
| T17 | D-10, REQ-001 | capturé |
| T18 | D-11, REQ-011 | capturé |
| T19 | D-12, D-18, REQ-004, REQ-013 | capturé ; élargi par Q-002 |
| T20 | D-13, UI-011 | capturé |
| T21 | D-14, UI-006 | capturé |
| T22 | D-14, REQ-005, REQ-007, UI-007 | capturé |
| T23 | UI-001 | capturé |
| T24 | UI-002, REQ-009, Q-003 | capturé ; noms 2 à 5 → question |
| T25 | UI-003, UI-004 | capturé |
| T26 | UI-005, REQ-002 | capturé |
| T27 | UI-009, REQ-008 | capturé |
| T28 | UI-006 | capturé |
| T29 | UI-007 | capturé |
| T30 | UI-006, UI-008 | capturé |
| T31 | REQ-006, D-16 | capturé |
| T32 | UI-010 | capturé |
| T33 | REQ-005, ARCH-003 | capturé |
| T34 | REQ-005, REQ-007, ARCH-003 | capturé |
| T35 | Q-001 (A), D-17, CON-004 | résolu : A |
| T36 | REQ-001, REQ-004, REQ-008, REQ-009, ARCH-002, UI-011 | capturé |
| T37 | ARCH-005, §11 | capturé |
| T38 | REQ-003, D-15, D-17, D-18, D-19, D-20, ARCH-002 | capturé ; repli supprimé (Q-002) ; widget tranché (D-20) |
| T39 | §8, §9, ARCH-006 | hors périmètre / idée |

### Points de la source non résolus

Aucun. T35 → Q-001 A (D-17) ; T38 (repli) → Q-002 (D-18, REQ-013) ; T24 → Q-003 A (D-19, REQ-009) ; T38 (widget) → revue d'architecture (D-20, ARCH-002). Reste hors de l'issue : l'URL de l'artefact du prototype (§14 pas 18).

## 13. Revue d'architecture

Revue du 24.10.2026, faite contre le code de master `be5b85f` (le code décide, les docs retardent) et contre les spécifications voisines `2026-10-24-type-donnees` (#106), `2026-10-24-type-document` (#107) et `2026-10-24-onglet-variables-groupes` (#114).

**Verdict : APPROUVER AVEC RÉSERVES.** L'architecture demandée est saine (un fichier de textes courts, un modèle de page, des rendus compilés par le dispositif des exemples) et ne contredit aucune décision réglée. Les réserves sont onze risques, tous repris dans le plan (§14) ; trois pèsent le plus : l'ampleur écrite à la main (54 commandes en trois langues), le poids des PNG committés dans un dossier OneDrive, et la bulle qui doit rester ouverte sous la souris (ce que `QToolTip` ne fait pas).

### Modules concernés

- `calc/tools/commands_tab.py` (850 lignes) : `CommandsTab(QWidget)` ligne 375, sans classe de base ; `CATEGORY_ORDER` ligne 100 ; `matches` ligne 503 (cherche dans la signature, les puces et les deux langues : à réduire au nom et au `lead`) ; `fill_detail` ligne 643 et `argument_table` ligne 704 (la page longue, qui disparaît) ; `RenderJob` ligne 233 et `ExampleBox` ligne 259 (les exemples, qui restent) ; `view_state` ligne 843 (aucun `dirty`, aucune phase : c'est ce qui rend la migration sur `DataTab` simple) ; `STRINGS` ligne 40. Trouvé par `tab_registry.py:110` (`TabSpec("tab_commands", CommandsTab, "nav_reference")`), par classe dans `tests/test_window.py:172` (`type(t).__name__ == "CommandsTab"`) et `tests/test_richtext.py:196`, par nom d'onglet dans `command_palette.py:666`.
- `calc/tools/command_docs.py` (240 lignes) : `LANGUAGES = ("fr", "de")` ligne 27 (l'anglais y est le bloc `///` lui-même) contre `REFERENCE_LANGUAGES` ligne 28 (les trois) ; `example_levels` ligne 168 (la règle des niveaux, commune à l'onglet, au générateur et au site) ; `arguments` ligne 189 et `calls` ligne 196 ; `category_label` ligne 224 et `word` ligne 236 (les mots partagés avec le site, lus de `reference.json`).
- `calc/build_reference_lib.py` : `CATEGORIES` ligne 67 (formula 9, display 11, data 8, format 6, document 20 = **54** commandes publiques, relevé le 24.10.2026 ; ordre actuel formula, display, data, **format, document**) ; `LEVELS_CONFOUNDED` ligne 138 (quatre commandes, déclarées à la main) ; `NO_LEVEL` ligne 120.
- `calc/tools/build_examples.py` (357 lignes) : `LANG = "de"` ligne 53, `write_sources` ligne 179, `render` ligne 197, `load_manifest` ligne 286 (`index.json`, `schema_version` "1.0", **aucun schéma dans `schemas/`**), `page` ligne 299 (fresh / stale / missing par `source_hash`, ligne 83) ; `calc/tools/command_preview.py` : `document` ligne 83, `PPI = 192` ligne 33, `render_localised` ligne 243.
- `calc/tools/norm_bubble.py` (289 lignes) : `place` ligne 24 (fonction pure, déjà testée), `NormBubble` ligne 100 (fenêtre outil sans focus, largeur fixe 460), `BubbleController` ligne 158 (attache un ⓘ à des extraits de norme : ni générique ni réutilisable tel quel), `_BubbleHover` ligne 277 (le maintien sous la souris).
- `website/build.py` (1265 lignes) : `_commands` ligne 415, `render_examples` ligne 532 (compile les exemples dans les trois langues en SVG au moment de la construction), `sidebar_docs` ligne 798, `page_command` ligne 1027 (la page longue du site, qui doit lire le même modèle) ; `website/assets/site.js` et `site.css` ; `tests/test_site.py`.
- `lib/display-presets.json` : `fine-values`, `fine-keys` (lus par Typst et par `calc/line_display.py` : la source des valeurs fines que REQ-003 recoupe). `calc/i18n/commands.json` (204 Ko) : le français et l'allemand des blocs `///`, appariés à l'anglais courant ; 106 renvois internes (« spec 20… », « REQ- », « (v0.xx) ») y figurent et 33 lignes `///` de six fichiers de `lib/`.
- `calc/tools/theme.json` : `danger` (la pastille « obligatoire »), `muted`, `card`, `line`, `accent` : toute couleur de la page et de la bulle vient de là (le site a sa feuille `site.css`, sa propre palette, déjà ainsi).

### Existant à réutiliser

- `norm_bubble.place` (positionnement sous / au-dessus / défilement) et le principe de `_BubbleHover` : à extraire dans la brique, non à recopier.
- `command_docs.example_levels`, `arguments`, `calls`, `word`, `category_label` : le modèle de page les appelle, ne les redit pas.
- `build_examples.imports_for`, `refresh_engine`, `source_hash`, `OUT`, `command_preview.document` : le dispositif de compilation des rendus de valeurs (ARCH-003) ; Pillow est déjà dans `requirements.txt` (quantification en 32 couleurs, rognage à l'encre).
- `richtext.copy_button`, `plain_label`, `prose_label`, `CodeBlock`, `PreviewLabel`, `ExampleBox` : gardés pour les exemples et les lignes à copier.
- `reference.json` (`words`, `categories`) : tous les mots du modèle de page ; `tests/test_i18n.py` les tient aux trois langues.
- Le patron « service » de `tab_host.Service` (`mount`, `state`, `restore`) : imité par les composants (ARCH-007) sans l'importer.

### Risques

**ARCH-RISK-001 — important — la bulle ne peut pas être un `QToolTip` (ARCH-002).** `QToolTip` ferme la bulle quand la souris y entre et ne contient pas d'images cliquables ; la bulle des valeurs (860 px, deux colonnes, rendu) doit rester ouverte sous la souris, fixée par un clic, fermée par Échap, un clic ailleurs ou le défilement. `NormBubble` / `BubbleController` ne conviennent pas non plus : largeur et pied figés, un contrôleur lié à des extraits de norme (`norm_excerpts`). Correctif : une brique `calc/tools/hover_bubble.py` (`HoverBubble`, cadre outil sans focus à largeur par appel ; `HoverController`, qui reçoit une fonction `content(clé) -> QWidget`, les délais 0 / 300 ms, le clic qui fixe, un filtre d'événements d'application tant que la bulle est ouverte pour Échap et le clic extérieur, le branchement sur la barre de défilement de la page), qui n'importe rien de `commands_tab` ni de `norms/`. `place` et `GAP` y migrent ; `norm_bubble` les réimporte (nom conservé, ses tests passent inchangés). Le widget de la ligne : **`QTextBrowser` en lecture seule à ancres** (`arg:nom`, `val:nom`), dont le signal `highlighted(QUrl)` désigne l'ancre survolée ; la bulle s'ouvre sous le curseur (position du pointeur, non le rectangle exact de l'ancre, que Qt ne donne pas simplement) ; il donne gratuitement le Tab entre ancres (UI-008) et le texte sélectionnable. À vérifier au pas 10, par capture : le soulignement en pointillé (`text-decoration` Qt est plein ; sinon un `QTextCharFormat.UnderlineStyle.DotLine` posé par programme), l'ouverture au focus clavier (sinon Entrée sur l'ancre). Un widget peint à la main est écarté : il redirait la sélection, le Tab, le retour à la ligne et l'accessibilité.

**ARCH-RISK-002 — important — poids du dépôt et des planches (CON-004, ARCH-009).** Trois langues committées : ≈ 4,6 Mo pour la première catégorie (prototype), 10 à 25 Mo estimés pour les 54 commandes, plus pour les `image-*` (dessins). Le dossier du projet est dans OneDrive et cloné. Correctifs : une **planche par commande et par langue** plutôt qu'un PNG par valeur (≈ 3 × 40 fichiers au lieu de ≈ 2 000 ; une lecture, un `copy`), 32 couleurs, rognage à l'encre, condensat par planche (ne recompile que ce qui change, comme `source_hash`), butée de 30 Mo mesurée après chaque catégorie avec arrêt du pas suivant. Limite connue : une planche change tout entière au moindre appel modifié, ce qui alourdit l'historique git ; acceptable pour des commandes « figées ».

**ARCH-RISK-003 — important — appels d'une même planche qui se contaminent (ARCH-010).** Un seul document par commande et par langue, un paragraphe par appel, est rapide (≈ 3 × 40 compilations au lieu de ≈ 2 000) mais `calc-defaults` pose un état, deux `#var("S", …)` se heurtent, les compteurs avancent. Correctif : mise en place dans un bloc isolé, noms uniques par appel, indicateur `isolate` par commande (un document par appel) pour celles qui fuient, et un test de contamination planté. À décider dès `calc-defaults` et `var` (pas 5 et 7).

**ARCH-RISK-004 — important — deux sources parlent d'un argument (D-10, REQ-003).** Le bloc `///` (anglais, source de `commands.json`) et `command-pages.json` (trois langues) disent chacun ce qu'un argument fait. Les noms, l'ordre, les défauts, les types et les valeurs fines sont tenus d'accord par test (REQ-003) ; **la prose ne peut pas l'être** (un `lead` anglais et le résumé du bloc peuvent diverger). Décision d'écriture à reporter dans `command-docs.md` §10sexies : `///` fait foi pour la signature, les types, la référence longue et ce que Tinymist montre ; `command-pages.json` pour tout ce que l'onglet et le site montrent en texte ; aucun des deux n'est dérivé de l'autre. Le test borne le risque aux noms ; un désaccord de prose est une affaire de relecture (une page relue par catégorie).

**ARCH-RISK-005 — important — l'ampleur de REQ-013 (54 commandes, 112 puces, trois langues, rendus).** La qualité de `var` sur 54 commandes est un travail de rédaction long, séquentiel (un seul fichier `command-pages.json` de 150 à 250 Ko, édité par des Edit ciblés, clés dans l'ordre de `CATEGORIES`), exposé à une dérive de qualité d'une session à l'autre et à un oubli de langue. Correctifs : un pas par catégorie (le document en deux), chacun fermé par le test de complétude de sa catégorie, la mesure du poids et la relecture d'une page par l'ingénieur ; la catégorie 1 (la plus riche, `var` du prototype) sert de patron écrit au §16 : longueur d'un `lead`, nombre de `keys`, forme d'un exemple ; la liste des commandes de chaque catégorie vit en tête du pas, rien n'est laissé « en chemin » ; ni script de déduction, ni copie d'un bloc `///`.

**ARCH-RISK-006 — important — retirer les renvois internes sans casser `commands.json` (REQ-010).** `commands.json` apparie chaque traduction à l'**anglais courant** du bloc : changer une ligne `///` sans la traduction casse `tests/test_commands.py` (« nothing left that no longer matches »). Correctif : un seul pas (3), une seule opération sur les deux fichiers (33 lignes de six fichiers de `lib/`, 106 occurrences dans `commands.json`), les renvois passés en `//` au-dessus du bloc, les fences d'exemples comparées avant / après par condensat, le motif interdit ajouté au test.

**ARCH-RISK-007 — important — les tests de l'onglet sont liés à la mise en page actuelle.** `tests/test_commands.py` (34 tests, 770 lignes) lit les parties de la page par nom (`parts`), compare `CATEGORY_ORDER` et le tableau d'arguments d'aujourd'hui ; `test_window.py:172` et `test_richtext.py:196` trouvent l'onglet par sa classe. Correctif : le modèle de page (sans Qt) porte la majorité des assertions ; les tests d'onglet se réécrivent contre les trois composants ; `CommandsTab` garde son nom, son module, sa clé et son `TabSpec`. Le nombre de tests ne baisse pas sans être dit au §16.

**ARCH-RISK-008 — important — le site (`website/build.py`, 1265 lignes) est la plus grande surface non testée visuellement.** La bulle y est du JavaScript (`site.js`) : survol au pointeur, toucher sur mobile, même contenu que la fenêtre. Correctif : le contenu de chaque bulle est du HTML produit par le **même modèle** (ARCH-008) et placé dans la page ; `site.js` ne fait qu'ouvrir, positionner et fixer ; le test du site vérifie la présence des bulles, des planches et des images référencées ; une vérification visuelle dans le volet navigateur (survol, toucher à 375 px) est une étape du pas 11. Les images : les planches PNG committées (le site n'a pas à compiler les rendus de valeurs, contrairement à ses exemples, `render_examples` ligne 532).

**ARCH-RISK-009 — important — « Dans ce projet » (UI-010) : quel projet ?** T32 dit « le projet d'exemple » ; dans une installation de Woodcore, `tests/projet-exemple/` n'est pas livré, et CLAUDE.md interdit de lire les projets de l'ingénieur pour les tests, non pour la fenêtre. Choix retenu : la fenêtre lit, en lecture seule, **le projet ouvert** (`project.current()`) ; les tests lisent `tests/projet-exemple/` ; le balayage est une fonction sans Qt (`command_usage.py`), plafonnée à douze entrées. À confirmer par l'ingénieur à l'approbation (voir §14, décision à rappeler) : s'il veut seulement le projet d'exemple, c'est une ligne dans le module.

**ARCH-RISK-010 — mineur — l'anglais n'est plus « le bloc `///` ».** `docs.localise` traite fr et de comme des traductions de l'anglais du bloc ; `command-pages.json` porte trois langues égales. Le chargeur utilise `REFERENCE_LANGUAGES`, jamais `LANGUAGES` (ligne 27) ; la recherche lit le `lead` de la langue de la fenêtre ; `matches` cesse de chercher dans le bloc anglais (pas de recherche croisée de langue, D-11).

**ARCH-RISK-011 — mineur — contrats : deux schémas, l'index des exemples relevé.** `command-pages.json` (`schemas/command-pages.schema.json`, `schema_version` "1.0"), `examples/out/values/index.json` (`schemas/command-values.schema.json`) ; `examples/out/index.json` n'a aujourd'hui aucun schéma : il en reçoit un (`command-examples.schema.json`) en même temps que ses champs `same12` / `same23` / `same123` (additifs, version relevée à "1.1" ; les anciens fichiers restent lus). Lecture d'un fichier malformé : l'erreur cite le fichier et le champ (principe « a malformed file stops »), et la fenêtre l'affiche au lieu de planter. Pas d'écriture des fichiers committés au chargement (`WRITERS` n'est pas concerné : aucune source de projet n'est touchée).

### Autres points relevés (sans risque propre)

- Aucune importation Qt dans `calc/domains/` n'est en jeu ; `command_page.py` et `command_pages.py` restent hors Qt, importables par `website/build.py` (qui n'importe pas Qt aujourd'hui, ligne 50 à 51).
- Aucune nouvelle commande Typst : pas de `///` ni de `commands.json` à ajouter (CLAUDE.md), seulement les retraits du pas 3.
- La règle 14 du §2 (« l'exemple s'écrit une fois, dans le `///` ») est inchangée : les exemples restent des fences ; les *appels de valeurs* sont d'une autre nature (écrits à la main, traduits) et vivent dans le JSON (D-15, confirmé par la revue : les mettre en fences obligerait Tinymist à les montrer et `commands.json` à les traduire). `api-conventions.md` est relue, non modifiée, sauf si la relecture dit autrement.
- Les mots de la fenêtre déjà dans `STRINGS` sans emploi après la refonte (`ref_col_*`, `ref_no_doc`…) sont retirés au pas 17 ; `tests/test_i18n.py` tient les trois langues.
- Préparation de #106 : voir ARCH-007. Un `DataTab` y verra trois `Service` (liste = zone gauche, page = centre, volet = droite) dont `mount(ctx)` renvoie le composant, `state` / `restore` ceux du composant, `hidden` l'arrêt de la file de compilation ; `CommandsTab` n'y garde que ses paramètres. Rien à épaissir : pas de classe de base commune, pas de `Service` importé ici.

### Approche recommandée

Contrat d'abord (schéma, lecture, accord avec `lib/`), puis catégories et retrait des renvois, puis le modèle de page sans Qt, puis le générateur de planches, puis la catégorie « Calculer dans le rapport » écrite en entier (elle prouve contrat, modèle, générateur et poids), puis la brique de bulle, puis l'onglet en deux pas (composants et exemples déplacés, puis la page), puis le site, **puis un arrêt de relecture par l'ingénieur** (une page `var` dans la fenêtre et sur le site, le poids mesuré), puis les quatre autres catégories une à une, puis le retrait du repli et du code mort, puis la documentation.

### Tests à ajouter ou étendre

Nouveaux (une ligne chacun au catalogue) : `tests/test_command_pages.py` (schéma, accord avec `lib/`, valeurs fines, renvois internes, complétude par catégorie), `tests/test_command_page.py` (modèle : ligne de la commande, tableau, cartes, cinq cas de bulle, recherche, « Dans ce projet », sans Qt), `tests/test_command_values.py` (carte, planches, condensats, `same` / `blank`, contamination, une compilation réelle), `tests/test_hover_bubble.py` (tenue, Échap, clic, placement, second usage). Étendus : `tests/test_commands.py` (catégories, renvois, onglet réécrit), `tests/test_command_levels.py` (recoupe mesuré / déclaré), `tests/test_window.py` (une vue, ni module d'état ni bulle de norme), `tests/test_i18n.py`, `tests/test_site.py`, `tests/test_command_palette.py` (inchangé, doit passer), `tests/test_calc_tab_base.py` et `tests/test_materials_tab.py` (qui emploient `norm_bubble` : `place` réimporté).

**Décisions à rappeler à l'ingénieur** : (1) « Dans ce projet » lit le projet ouvert (ARCH-RISK-009) ; (2) la butée de 30 Mo (CON-004) ; (3) l'URL de l'artefact du prototype, absente de l'issue, pour la copie du pas 18.

## 14. Plan d'implémentation

Règles du plan : chaque pas laisse la fenêtre et le site en état de marche (le repli de REQ-004 tient jusqu'au pas 17) ; un test le prouve avant le pas suivant ; les tests voisins se lancent par `python tests/run_tests.py --related <fichiers>`, la suite entière une fois au pas 19 ; documentation et commit à la fin (CLAUDE.md : `finish`). Les pas 13 à 16 se suivent dans l'ordre de risque décroissant (les dessins d'abord, pour que la butée de poids se mesure tôt). Un pas n'ouvre pas le suivant tant que son test ne passe pas ; le pas 12 est un arrêt de relecture, non un blocage de code.

| # | Pas | Fichiers | Exigences | Test qui le prouve |
|---|---|---|---|---|
| 1 | **Le contrat et sa lecture.** `schemas/command-pages.schema.json` (`schema_version` "1.0" ; par commande `lead`, `keys`, `arguments` avec `group`, `status`, `text`, `examples`, `values` {valeur, phrase, appel, mise en place, `isolate`}, `named` ; chaque texte `{fr, de, en}` ; l'appel soit une chaîne, soit trois). `calc/i18n/command-pages.json` créé avec `var` seule, du premier jet du prototype. `calc/tools/command_pages.py` (sans Qt) : lecture, validation avec une erreur qui cite fichier et champ, accord avec `lib/` (arguments de `command_docs.arguments`, valeurs fines de `display-presets.json`), règle des guillemets, motifs interdits. | `schemas/command-pages.schema.json`, `calc/i18n/command-pages.json`, `calc/tools/command_pages.py`, `calc/tools/command_docs.py` (langues) | REQ-001, REQ-003, REQ-006, ARCH-004, ARCH-010 (champ `isolate`) | `tests/test_command_pages.py` : fichier malformé nomme fichier et champ ; langue ou argument retiré nommé ; argument renommé dans `lib/` plante ; valeur fine sans phrase plante ; `display: none` sans guillemets plante |
| 2 | **Catégories par tâche.** `CATEGORIES` : `document` avant `format` ; `reference.json` : noms et introductions des cinq catégories en fr, de, en (« Calculer dans le rapport », « Imprimer un dessin ou un objet », « Lire les données du projet », « Le document et ses citations », « Écrire un modèle ») ; `from-level` vérifié dans la première ; l'arbre et la barre latérale du site suivent. | `calc/build_reference_lib.py`, `calc/i18n/reference.json`, `calc/tools/commands_tab.py` (`CATEGORY_ORDER` suit déjà) | REQ-009, D-19, UI-002 (ordre) | `tests/test_commands.py` (catégories dans les deux sens, noms en trois langues), `tests/test_site.py` |
| 3 | **Renvois internes hors des blocs `///`.** Les 33 lignes de six fichiers de `lib/` passent en commentaires `//` au-dessus du bloc ; les 106 occurrences de `commands.json` et leur anglais apparié suivent dans la même opération ; condensat des fences avant / après identique. | `lib/*.typ`, `calc/i18n/commands.json` | REQ-010, CON-001, D-6 | `tests/test_commands.py` : motif `spec 20`, `REQ-`, `ARCH-`, `Q-0`, `D-` refusé ; tous les exemples compilent ; appariement anglais intact ; planté : un renvoi remis dans un bloc échoue |
| 4 | **Le modèle de page, sans Qt.** `command_page.py` : la ligne de la commande (groupes, gras, défauts), cartes, groupes et lignes du tableau (dont « Écrits par leur nom »), modèle des bulles (en-tête, valeurs, `same` / `blank` / `role` / texte libre / pied, rendu par rectangle de planche), recherche par nom et `lead`, repli temporaire pour une commande sans entrée. Les mots nouveaux dans `reference.json` en trois langues. `command_usage.py` : balayage des appels d'une commande dans un projet (douze au plus). | `calc/tools/command_page.py`, `calc/tools/command_usage.py`, `calc/i18n/reference.json`, `calc/tools/command_docs.py` | REQ-011, UI-003, UI-004, UI-005, UI-006, UI-007 (contenu), UI-010 (appels du projet), ARCH-001, ARCH-005, ARCH-008 | `tests/test_command_page.py` : ligne de `var` conforme à T25 ; tableau de `var` et `verify` ; cinq cas de bulle ; recherche (« moment » trouve par `lead`, un nom d'argument seul ne trouve rien) ; `PySide6` absent de `sys.modules` |
| 5 | **Le générateur des rendus de valeurs.** `build_examples.render_values` (appelée par `main()`) : un document par commande et par langue (ou par appel si `isolate`), `commands.typ` frais, `document_language=True`, un paragraphe par appel, `#set-report-language` et `#set text(lang:)` ; rognage à l'encre, quantification Pillow en 32 couleurs, planche `examples/out/values/<langue>-<commande>.png`, carte `index.json` (rectangle, condensat, `same`, `blank`, `isolate`) ; `auto` rendu pour chaque valeur fine au niveau 2 ; un appel qui ne compile pas fait échouer en nommant commande, argument, valeur, langue ; saute ce dont le condensat n'a pas changé ; décision d'isolation prise sur `calc-defaults` et `var`. `schemas/command-values.schema.json`. | `calc/tools/build_examples.py`, `schemas/command-values.schema.json`, `examples/out/values/` | REQ-005, REQ-012, ARCH-003, ARCH-004, ARCH-009, ARCH-010, CON-002, CON-003 | `tests/test_command_values.py` : une compilation réelle de `var.level` ; `level: auto` et `level: 2` `same` ; `display: "none"` et `level: 0` `blank` ; carte recoupée avec la taille de chaque planche ; condensat périmé nommé ; contamination plantée (`calc-defaults` avant `var`) |
| 6 | **Niveaux égaux mesurés.** `build_examples` compare les pages des niveaux 1, 2, 3 (condensat du PNG), n'en garde qu'une quand elles sont identiques, écrit `same12` / `same23` / `same123` dans `index.json` (version relevée, schéma `command-examples.schema.json`) ; `page()` et `example_levels` le servent à l'onglet et au site ; recoupement avec `LEVELS_CONFOUNDED`. | `calc/tools/build_examples.py`, `calc/tools/command_docs.py`, `schemas/command-examples.schema.json`, `examples/out/` | REQ-008, UI-009, ARCH-011, ARCH-004 | `tests/test_command_levels.py` (désaccord mesuré / déclaré nommé), `tests/test_commands.py` (`show-annexes` : une page + mention) |
| 7 | **Catégorie 1 écrite en entier : « Calculer dans le rapport » (9 commandes, 89 puces).** `var` (patron), `eq`, `unit`, `verify`, `calc-defaults`, `domain`, `from-level`, `var-table`, `distance` : lead, 3 ou 4 cartes, groupe / statut / phrase propre / 2 ou 3 exemples par argument, valeurs et appels de chaque argument à valeurs, `named`, en fr, de, en, à la main d'après le `///` et `commands.json`, sans renvoi ; régénération des planches ; poids mesuré et noté au §16. Le patron (longueur du `lead`, forme d'un exemple) est écrit au §16. | `calc/i18n/command-pages.json`, `examples/out/values/` | REQ-002, REQ-005 (203 valeurs), REQ-007, REQ-013, CON-004 | `tests/test_command_pages.py` (complétude de la catégorie, aucune phrase d'argument en double, `label` ≠ `label-position`) ; `tests/test_command_values.py` (203 valeurs ×3) |
| 8 | **La brique de bulle.** `calc/tools/hover_bubble.py` (`HoverBubble`, `HoverController`) ; `place` et `GAP` migrés, `norm_bubble` les réimporte. | `calc/tools/hover_bubble.py`, `calc/tools/norm_bubble.py` | ARCH-002, UI-008 | `tests/test_hover_bubble.py` : entrer dans la bulle annule la fermeture (300 ms), Échap ferme, le clic fixe, le défilement ferme, placement au-dessus faute de place, second usage sans commandes ; les tests de `norm_bubble` passent inchangés |
| 9 | **L'onglet, 1re partie : composants et déplacements.** `commands_tab.py` ne garde que l'assemblage et `view_state` ; `command_list.py` (recherche, arbre : catégories, nom en chasse fixe, `lead` coupé par « … », nombre), `command_side.py` (lignes à copier, liste des exemples, « Dans ce projet »), `command_examples.py` (`RenderJob`, `ExampleBox`, `PreviewLabel`, `CodeBlock`, la file de compilation, `hidden()` l'arrête) ; contexte commun ; signaux entre composants. La page d'une commande garde provisoirement le repli. | `calc/tools/commands_tab.py`, `calc/tools/command_list.py`, `calc/tools/command_side.py`, `calc/tools/command_examples.py` | UI-001, UI-002, UI-010, UI-009, ARCH-007, REQ-011 | `tests/test_commands.py` adapté (34 tests, aucune assertion de comportement retirée), `tests/test_window.py:172`, `tests/test_richtext.py:196` ; un test construit chaque composant seul ; `grep tab_host` vide |
| 10 | **L'onglet, 2e partie : la page condensée.** `command_page_view.py` : en-tête, ligne de la commande (`QTextBrowser` à ancres, soulignement pointillé, boîtes ▾, ligne d'aide), cartes, tableau en groupes (statut avec pastille `danger`), exemples avec niveaux et mention de REQ-008, bulles branchées sur `hover_bubble` (largeurs 380 / 860, rendus découpés de la planche) ; mots nouveaux dans `reference.json` ; couleurs de `theme.json` ; vérification par capture : pointillé, focus clavier, survol d'une valeur, bulle sous la souris. | `calc/tools/command_page_view.py`, `calc/tools/commands_tab.py` | UI-003 à UI-009, REQ-012, ARCH-005 | `tests/test_commands.py` (page de `var` : parties, bulles, langue qui change les phrases, Typst absent du PATH : la page s'ouvre et la bulle répond), `tests/test_i18n.py`, `tests/test_window.py` (ni vue, ni module d'état, ni ⓘ de norme) |
| 11 | **Le site.** `website/build.py` lit `command-pages.json`, le modèle de page et les planches (copiées en ressources) ; `page_command` produit la ligne, les cartes, le tableau et les bulles en HTML ; `site.js` ouvre, positionne, fixe (survol et toucher) ; `site.css` ; catégories par tâche et recherche par nom et `lead` ; repli temporaire inchangé ; vérification visuelle dans le volet navigateur (survol, toucher à 375 px, trois langues). | `website/build.py`, `website/assets/site.js`, `website/assets/site.css` | UI-011, REQ-009, REQ-011, ARCH-008 | `tests/test_site.py` : la page `var` de chaque langue contient ligne, cartes, bulles, planches référencées existantes ; `python website/build.py` sans erreur |
| 12 | **Arrêt de relecture.** L'ingénieur regarde `var` et `distance` dans la fenêtre et sur le site (qualité des textes, bulle, pointillé, poids mesuré). Une remarque devient une correction avant le pas 13. Sans réponse, le pas 13 se poursuit sur le patron du §16. | — | REQ-013 (patron) | relecture écrite au §16 |
| 13 | **Catégorie 2 écrite : « Imprimer un dessin ou un objet » (11 commandes, 62 puces).** Les six `image-*` du dessin, `image-section`, `image-legend`, `image-titleblock`, `show-annexes`, `position` ; appels sur les ids des données figées ; les rendus de dessins sont les plus lourds : poids mesuré, butée de 30 Mo. | `calc/i18n/command-pages.json`, `examples/out/values/` | REQ-013, REQ-005, REQ-007, CON-004 | complétude de la catégorie ; carte à jour ; poids au §16 |
| 14 | **Catégorie 3 écrite : « Lire les données du projet » (8 commandes, 13 puces).** `find`, `sync`, `domain-file`, `ids`, `project-info`, `plans-of`, `journal-entries`, `get` ; appels entourés d'une impression explicite ; poids. | idem | idem | idem |
| 15 | **Catégorie 5 écrite : « Écrire un modèle » (6 commandes, 8 puces).** `fmt-number`, `fmt-value`, `fmt-decimals`, `render-symbol`, `render-formula`, `render-prose`. | idem | idem | idem |
| 16 | **Catégorie 4 écrite : « Le document et ses citations » (20 commandes, 29 puces), en deux lots.** (a) `show-bibliography`, `cite-norm`, `show-norm-list`, `set-report-language`, `report-language`, `report-lang`, `woodcore-document`, `caption-rules`, `doc-tables` ; (b) `t`, `tl`, `t-str`, `tl-str`, `t-label`, `t-pattern`, `t-of`, `tl-of`, `report-level`, `uniform-level`, `show-masked`. Les commandes qui règlent un état montrent ce que la ligne suivante imprime. | idem | idem | idem |
| 17 | **Le repli et le code mort retirés.** `fill_detail` long, `argument_table`, `types_html`, le résumé tiré du bloc `///`, `matches` ancien, le repli du modèle et du site, les mots devenus sans emploi dans `STRINGS` et `reference.json` ; le test final : toute commande publique a une entrée. | `calc/tools/commands_tab.py`, `calc/tools/command_page.py`, `website/build.py`, `calc/i18n/reference.json` | REQ-004, ARCH-005 | `tests/test_command_pages.py` (54 commandes ; planté : `find` retiré), `tests/test_i18n.py`, `grep` du code long vide |
| 18 | **La documentation.** `docs/ui/tab-commands.md` (une vue, trois volets, ligne, bulles, tableau, exemples, « Dans ce projet »), `docs/typst/command-docs.md` §10sexies (la phrase « Every word of it is read out of the `///` blocks » remplacée par la répartition `///` / `command-pages.json` ; « Rendered in German, once » limitée aux exemples ; rendus des valeurs, planches, isolation), `docs/architecture/layout.md` (modules nouveaux), `docs/typst/api-conventions.md` (règle 14 relue : inchangée, dit-on), `docs/decisions.md` §13 (D-1, D-2, D-3, D-6, D-10, D-17 à D-20, par édition ciblée, fins de ligne LF), `docs/conventions/testing-catalogue*.md` (quatre lignes nouvelles : `test_command_pages.py`, `test_command_page.py`, `test_command_values.py`, `test_hover_bubble.py` ; les lignes de `test_commands.py`, `test_command_levels.py`, `test_site.py` mises à jour), `CHANGELOG.md` (une entrée, version en cours), les pages « Nouveautés » `website/content/{fr,de,en}/changes/<version>.md` (la version en cours : dernier fichier de ce dossier + celui qui suit), copie du prototype dans `docs/requirements/prototypes/2026-10-24-onglet-commandes/` (`index.html`, `vals/`, `ex/`, un `README.md`) lue par `Artifact action: "read"` **dès que l'ingénieur donne l'URL de l'artefact**. | `docs/`, `CHANGELOG.md`, `website/content/*/changes/` | §11 « Documentation » | `tests/test_docs_coherence.py` (taille, liens, une ligne par fichier de test) |
| 19 | **Suite entière et clôture.** Suite complète en arrière-plan, boucle de réparation, mesure finale du poids, remplissage du §15 par `verify-requirements`, commit par la compétence `finish`. | — | tout | `python tests/run_tests.py` vert |

### Risques de la revue et pas qui les traitent

| Risque | Traité par |
|---|---|
| ARCH-RISK-001 (bulle, widget) | pas 8 (brique), pas 10 (`QTextBrowser`, captures) |
| ARCH-RISK-002 (poids) | pas 5 (planches, 32 couleurs, condensat), pas 7 et 13 à 16 (mesure, butée de 30 Mo) |
| ARCH-RISK-003 (contamination) | pas 5 (décision d'isolation, test planté), pas 7 |
| ARCH-RISK-004 (deux sources) | pas 1 (accord des noms et des valeurs), pas 18 (répartition écrite) ; la prose reste à la relecture, dit |
| ARCH-RISK-005 (ampleur) | pas 7, 13 à 16 (un par catégorie, test de complétude, relecture), pas 12 (patron validé) |
| ARCH-RISK-006 (`commands.json`) | pas 3 (une seule opération sur les deux fichiers) |
| ARCH-RISK-007 (tests liés à la page) | pas 4 (assertions portées par le modèle), pas 9 et 10 |
| ARCH-RISK-008 (site) | pas 11 (même modèle, `site.js` mince, vérification visuelle) |
| ARCH-RISK-009 (« Dans ce projet ») | pas 4 (`command_usage.py`), pas 9 ; à confirmer par l'ingénieur |
| ARCH-RISK-010 (langues) | pas 1 (`REFERENCE_LANGUAGES`), pas 4 (recherche) |
| ARCH-RISK-011 (contrats) | pas 1, 5, 6 (trois schémas) |

## 15. Vérification

Vérification indépendante du 25.10.2026 (agent `requirements-verifier`, sur `e4d9eb0..HEAD`, quatorze fichiers de tests relancés, tous verts) : REQ-001 à REQ-007, REQ-009 à REQ-013, UI-001 à UI-007, UI-009 à UI-011, ARCH-001 à ARCH-011 ✅ ; trois réserves, toutes déclarées :

- **REQ-008** ⚠️ — le critère nomme `show-annexes`, dont les exemples sont `typ-dry` (jamais rendus) : la règle est prouvée sur `distance` (niveaux 2 et 3 égaux, une seule image, la mention), écart noté au §16 et à l'ingénieur.
- **UI-008** ⚠️ — survol, maintien sous la souris, clic, Échap, clic ailleurs et défilement sont testés (`test_hover_bubble`) ; l'ouverture au focus clavier, « inférée » par la spec, n'est pas prouvée par un test (le `QTextBrowser` donne le Tab entre ancres ; voir §16).
- **CON-004** ⚠️ — 4,4 Mo de planches (4,7 Mo sur le disque), sous la butée de 30 Mo ; mesuré après chaque catégorie (§16).

La relecture d'une page par catégorie par l'ingénieur (REQ-013, pas 12 retiré à l'approbation) reste à faire : il la fera à la clôture ; les captures sont dans le scratchpad de la session.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #115 (39 points) ; trois questions ouvertes (langues des rendus, repli, catégories) |
| 2026-10-24 | specified | réponses de l'ingénieur enregistrées au §10 : Q-001 A (trois langues committées), Q-002 hors options (une page condensée soignée pour les 54 commandes, plus de repli : REQ-013, D-18), Q-003 A ; D-17 à D-19 ; compte réel 9 · 11 · 8 · 20 · 6 = 54 commandes (45 autres, non 44) |
| 2026-10-24 | reviewed | revue d'architecture (§13) : APPROUVER AVEC RÉSERVES, onze risques ; ARCH-007 à ARCH-011 et D-20 ajoutés ; plan en 19 pas (§14), catégories par pas séparés ; en attente de l'approbation de l'ingénieur ; à lui rappeler : « Dans ce projet » lit le projet ouvert, la butée de 30 Mo, l'URL de l'artefact du prototype |
| 2026-10-24 | approved | approbation unique des huit specs du 24.10.2026 par l'ingénieur (AskUserQuestion) : plan approuvé tel quel ; toutes les propositions « à confirmer » des revues acceptées comme recommandées ; ordre d'implémentation #108 → #115 → #114 → #113 → #112 → #109 → #107 → #106, un agent par issue ; commits et push autorisés au fil du travail ; écarts et questions notés en §16 et posés à la fin |
| 2026-10-25 | implementation | pas 1 fait : `schemas/command-pages.schema.json`, `calc/tools/command_pages.py` (lecture, validation nommant fichier et champ, accord avec `lib/`, guillemets des valeurs fines, renvois internes, complétude), `calc/i18n/command-pages.json` avec `var` du prototype (2 ou 3 exemples par argument complétés), `tests/test_command_pages.py` (REQ-001, REQ-003, REQ-006, ARCH-004). Les exemples d'arguments portent un `context` facultatif (lignes supposées au-dessus, compilées par le test, non montrées) ; les textes acceptent le code entre accents graves ; le français suit `reference.json` (espace fine insécable avant « : ; ? ! » et dans les guillemets). Écart : pas de champ `isolate` (voir pas 5) |
| 2026-10-25 | implementation | pas 2 fait : `CATEGORIES` par tâche (`document` avant `format`), noms et introductions des cinq catégories dans `reference.json` en fr, de, en (REQ-009, D-19) ; `default`, `required`, `examples` du site lus de `reference.json` (retirés de `website/strings.json`, règle « écrit une fois ») ; les mots du modèle de page ajoutés à `reference.json` (pas 4) |
| 2026-10-25 | implementation | pas 3 fait : les renvois internes des blocs `///` publics (30 lignes de sept fichiers de `lib/`) passés en un commentaire `//` au-dessus de chaque bloc, leurs traductions de `commands.json` (88 occurrences) suivies dans la même opération ; condensat des fences identique avant et après ; `test_commands.test_no_doc_block_carries_an_internal_reference` (REQ-010, D-6) |
| 2026-10-25 | implementation | pas 4 fait : `calc/tools/command_page.py` (ligne de la commande, vue de la page, bulles d'argument et de valeurs avec `same` / `blank` / rôle / texte libre / périmé, recherche par nom et `lead`, niveaux à montrer) et `calc/tools/command_usage.py` (appels d'une commande sous la racine Typst du projet, douze au plus) ; mots du modèle dans `reference.json` ; `tests/test_command_page.py` sans Qt (ARCH-001, ARCH-008, REQ-011, UI-003 à UI-007, UI-010) |
| 2026-10-25 | implementation | pas 5 fait : `build_examples.render_values` (appelée par `build`, et seule par `--values`) : un document par valeur (ARCH-010 : isolement partout, décidé sur `calc-defaults` et `var` — un réglage `scope: "document"` changerait l'impression d'une valeur suivante, test planté), rognage à l'encre, planche quantifiée en 32 couleurs par commande et par langue, carte `examples/out/values/index.json` (rectangle, condensat de l'appel, encre, `same`, `blank`, `isolate`), recompilation seulement des planches dont les appels ont changé ; `schemas/command-values.schema.json` ; `tests/test_command_values.py`. `var` : 37 valeurs × 3 langues, 129 Ko |
| 2026-10-25 | implementation | pas 6 fait : `build_examples.measure_levels` compare les pages des niveaux 1, 2, 3 (condensat du PNG), écrit `same` et `page` dans `examples/out/index.json` (1.1, `schemas/command-examples.schema.json`), et ne garde qu'un PNG pour deux niveaux égaux (40 fichiers retirés) ; `page()` lit `page` ; `command_page.levels_note` / `shown_levels` (une page et la mention pour « 123 », les boutons et la mention pour « 12 » / « 23 », comme le prototype) ; `test_command_levels.test_the_levels_measured_on_the_pages_agree_with_the_declaration` (ARCH-011). `show-annexes` n'a aucun exemple rendu (fences `typ-dry`) : le critère de REQ-008 est prouvé sur `distance` (2 et 3 égaux) |
| 2026-10-25 | implementation | pas 7 fait : « Calculer dans le rapport » écrite en entier (9 commandes) ; 221 valeurs × 3 langues compilées (218 pour les huit du prototype : `display-formula` et `display-equation` de `calc-defaults` et `unit` de `var-table` en plus), aucune en rouge ; **poids des planches : 2,64 Mo** (butée 30 Mo). Patron retenu pour les catégories suivantes : `lead` d'une phrase (≈ 15 à 25 mots), 3 ou 4 cartes (titre de 1 à 4 mots, texte d'une ligne), une phrase propre par argument (≤ 20 mots), 2 ou 3 exemples par argument (code à gauche, ce qu'il montre en ≤ 10 mots), code entre accents graves, valeurs `auto` décrites pour la commande (« décidé par le niveau : … ») ; un exemple d'appel entier compile (`context` s'il suppose une ligne au-dessus), un fragment est tenu par la règle des guillemets |
| 2026-10-25 | implementation | pas 8 fait : `calc/tools/hover_bubble.py` (`HoverBubble`, `HoverController`, `place` et `GAP` venus de `norm_bubble`, qui les réimporte) ; `tests/test_hover_bubble.py` (ARCH-002, UI-008). **Ordre changé** : les catégories 2 à 5 (pas 13 à 16) sont écrites avant l'onglet (pas 9, 10) et le site (pas 11) — l'onglet actuel reste en service entre-temps, et la page condensée n'a jamais besoin du repli de REQ-004 (aucun code jetable) |
| 2026-10-25 | implementation | pas 13 fait : « Imprimer un dessin ou un objet » écrite (11 commandes) ; valeurs des `detail-figure`, `detail-legend`, `frame`, `title`, `kind`, `plans`, `logo`, `category-show` compilées en trois langues sur les données figées ; `show-annexes` : valeurs de `heading` et `level` décrites sans rendu (`unrendered` : chaque page d'annexe est une page entière ; ses exemples sont déjà `typ-dry`) ; une planche dont une valeur ne compile pas n'est plus tenue pour à jour. **Poids : 3,13 Mo** |
| 2026-10-25 | implementation | pas 14 fait : « Lire les données du projet » écrite (8 commandes) ; les accesseurs montrent ce qu'ils rendent (`repr`, `raw`, `join`), valeurs de `object`, `type`, `kind` (13 sortes et un domaine), `document` et `field` compilées ; `project-info` sans argument a sa ligne écrite (`line`). **Poids : 3,82 Mo** |
| 2026-10-25 | implementation | pas 15 fait : « Écrire un modèle » écrite (6 commandes) ; seul `digits` de `fmt-decimals` prend une liste de valeurs (0 à 3), compilée. **Poids : 3,82 Mo** |
| 2026-10-25 | implementation | pas 16 fait : « Le document et ses citations » écrite (20 commandes) ; les états `report-language`, `report-level`, `uniform-level`, `show-masked` et `report-lang` sans argument ont leur ligne écrite ; `woodcore-document.document` décrit sans rendu (il règle les métadonnées du PDF) ; valeurs de `data`, `blocks`, `heading`, `level`, `lang` compilées. **Les 54 commandes publiques ont leur page** ; test final actif (REQ-004 : planté, `find` retiré est nommé). `command-pages.json` : 366 Ko. **Poids des planches : 4,37 Mo** |
| 2026-10-25 | implementation | pas 9 et 10 faits : `commands_tab.py` réduit à l'assemblage de trois composants sur un contexte (`command_list.py`, `command_page_view.py`, `command_side.py`, chacun `state` / `restore` / `shown` / `hidden`, signaux `chosen`, `example_chosen`) ; `command_examples.py` (exemples et file de compilation, arrêtée dans `hidden()`) ; la page condensée (ligne `QTextBrowser`, noms soulignés en pointillé par `QTextCharFormat.DotLine`, boîtes ▾, cartes, tableau en groupes, « Écrits par leur nom », exemples avec niveaux et mention) ; bulles `hover_bubble` 380 / 860 px, rendus découpés de la planche (`QPixmap.copy`, échelle 0,6 par le rapport de pixels) ; « Dans ce projet » lu du projet ouvert (`command_usage.UsageIndex`) ; tests de l'onglet réécrits dans `test_commands.py` (11 tests : arbre, recherche, une vue, page de `var`, bulles sans Typst, volet droit, composants seuls, niveaux, compilation fr/en, repli allemand) ; `test_window`, `test_richtext` adaptés ; `import_label` retiré de `woodcore_gui_words.py` (n'était lu que par l'ancienne page). Captures dans le scratchpad |
| 2026-10-25 | implementation | pas 11 fait : `website/build.py` — `page_command` lit le modèle (ligne, cartes, tableau, appels, exemples), bulles en `<template>` ouvertes par `site.js` (survol, toucher, clic qui fixe, Échap, défilement), planches publiées sous `values/` sauf `distance` (tables de norme masquées), recherche par nom et `lead`, cartes de l'index par `lead` ; `site.css` ; `test_site.test_a_command_s_page_is_the_condensed_page_with_its_bubbles` ; vérification dans le volet navigateur (bulle des valeurs de `label-position` en français, sombre) |
| 2026-10-25 | implementation | pas 17 fait : aucun repli n'a été écrit (ordre changé, voir pas 8) ; l'ancienne page longue (`fill_detail`, `argument_table`, `types_html`, l'entrée longue du site, `localised` du site) supprimée ; test final actif. Pas 18 fait : §10sexies, `ui/tab-commands.md`, `architecture/layout.md`, `decisions.md` §13 (+ index, la décision v0.99 « Le rapport et sa langue » en partie remplacée), catalogue des tests, `CHANGELOG.md`, « Nouveautés » 0.125 en fr/de/en, copie du prototype dans `docs/requirements/prototypes/2026-10-24-onglet-commandes/` |
| 2026-10-25 | verification | suite entière : 3282 réussis, 10 sautés, 2 échecs réparés (`except` large dit sur sa ligne dans `commands_tab.context` ; `duplicates-baseline.json` : la copie de `plain_label` déplacée de `commands_tab.py` vers `command_examples.py`, le groupe inchangé), relancés verts ; `test_calc_tab_base` a échoué une fois sous charge et passe seul (indépendant). Vérification indépendante au §15 |
| 2026-10-25 | completed | spec close ; la relecture d'une page par catégorie par l'ingénieur reste à faire (pas 12 retiré à l'approbation) |
