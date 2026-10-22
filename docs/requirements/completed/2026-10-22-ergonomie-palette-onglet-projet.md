---
id: 2026-10-22-ergonomie-palette-onglet-projet
titre: Ergonomie — palette Ctrl+K, zoom, vues, onglet Projet, aperçu des templates, aperçus Typst, nouveau projet minimal, volet replié (issues #83 à #91)
status: completed
cree: 2026-10-22
mis_a_jour: 2026-10-22
source: issues GitHub #83, #84 (mère), #85, #86, #87, #88, #89, #90, #91 et les commentaires du 21.10.2026 sur #87 et #88 ; demande de l'ingénieur du 22.10.2026 « implémente les issues 83, 84, 85, 86, 87, 88, 89, 90 et 91 »
docs: [docs/ui/window.md, docs/ui/tab-structure.md, docs/domain/documents.md, docs/domain/dependencies.md, docs/architecture/layout.md, docs/architecture/principles.md, docs/conventions/build-and-release.md, docs/decisions.md]
---

# Ergonomie de la fenêtre — palette Ctrl+K, onglet Projet et nouveau projet minimal — Spécification

## 1. Objectif

L'ingénieur, le 07.10.2026 : « il y a pour l'instant trop d'informations dans les onglets. On se perd un peu ». Neuf issues y répondent ensemble :
- retrouver n'importe quoi en tapant quelques lettres (palette Ctrl+K, #83) ;
- ne plus attendre une compilation Typst inutile en arrivant sur un onglet ou en changeant de document (#86, #87) ;
- réunir les données de base du projet et le choix des templates dans un onglet **Projet**, avec un aperçu des templates (#87, #88) ;
- créer un projet en ne donnant que son nom et son emplacement, le reste se décidant ensuite dans l'onglet Projet (#90) ;
- agrandir l'interface (#85), zoomer les aperçus Typst comme dans VS Code (#89), et corriger le volet gauche replié (#91).

Les issues #84 à #90 ont déjà été clarifiées le 21.10.2026 et revues sur le code (#85 à #89). Les décisions de l'ingénieur qu'elles contiennent sont reprises en §7 ; les notes des revues, en §13.

## 2. Source

Le texte complet est celui des issues (corps et commentaires), qui reste la référence. Ci-dessous, chaque demande mot pour mot, découpée en points.

**#83 — Palette de commandes (Ctrl+K)**

> **T1** — « Une **palette de commandes** ouverte par **Ctrl+K** permet de retrouver n'importe quel onglet, objet, variable, norme, action ou avertissement en tapant quelques lettres, sans parcourir la navigation. »
>
> **T2** — (dictée du 21.10.2026) « J'aime beaucoup sur l'image 1 et 3 le fait que juste sous la barre de recherche il y a des catégories que l'on peut sélectionner. […] Je trouve les raccourcis qui sont indiqués en bas pour les flèches Enter, Tab et Échappe pas nécessaires. On ne va pas naviguer avec les flèches, on va naviguer en scrollant avec la souris. […] Lorsque l'on clique une fois dessus, ça doit simplement l'activer. Et lorsqu'on double-clique dessus, ça doit l'ouvrir. La touche échappe doit permettre de sortir de ce panneau de navigation, mais il doit également y avoir en haut à droite une croix qui permet d'en sortir. Tab ne doit pas faire quoi que ce soit. […] j'aime beaucoup dans l'image 2 et 4 le panneau de droite qui apparaît et qui permet de faire des actions. Je trouve que ce panneau devrait tout le temps être ouvert dès que l'on sélectionne quelque chose à gauche. »
>
> **T3** — « **Image 1, palette vide** : les éléments récents et les actions fréquentes ; les raccourcis existants affichés en regard (Ctrl+1…, Ctrl+,). »
>
> **T4** — « **Image 2, recherche libre** (« flex ») : les résultats sont groupés par genre (onglets, vérifications avec leur η coloré, clause de norme, variables, commandes Typst). Les lettres trouvées sont soulignées. »
>
> **T5** — « **Image 3, catégorie Actions** : les actions des menus (*Exporter PDF*, *Exporter les trois*, langue forcée du PDF, ouvrir le dossier, vue *Affichage*, langue de la fenêtre, VS Code…). »
>
> **T6** — « **Image 4, catégorie Objets** (`@T001`) : une position et tout ce qui l'utilise (vérifications, plan de position, modèle statique), avec dans le panneau de droite un résumé (« 3 vérifications, η max 0.91 ») et les actions. »
>
> **T7** — « **Image 5, catégorie Avertissements** : les vérifications non satisfaites (η > 1), les données manquantes et les fichiers introuvables ; le double-clic ouvre le champ en cause. »
>
> **T8** — « Les textes de la palette en trois langues (de, fr, en) dans les glossaires de la fenêtre. Le contenu suit le document affiché (convention d'utilisation, base de projet, rapport de statique). »
>
> **T9** — « Les tests de la palette et une ligne dans `docs/conventions/testing-catalogue-window.md`. La section de `docs/ui/` qui la décrit, l'entrée du `CHANGELOG.md` et la page « Nouveautés ». »
>
> **T10** — « **D'où vient l'index** : ce que la palette cherche […] et sa source de vérité […]. Sa mise à jour après une modification. » · « **« Utilisée par »** (image 4) : comment on sait qu'une vérification ou un plan cite une position, sans recopier l'information. » · « **Avertissements** (image 5) : où l'export les rassemble aujourd'hui, et s'il faut les recueillir en un seul endroit. » · « **Ordre en trois phases possible** : (1) la palette avec les onglets et les actions, (2) les objets et les variables, (3) les avertissements. »

**#84 — Ergonomie (mère)**

> **T11** — « Ordre conseillé : #86, puis #89, puis #85, puis #87, #88 et #90 ensemble (#88 et #90 dépendent de #87). »
>
> **T12** — « Documentation attendue à la fin de chaque sous-issue : Les sections de `docs/` touchées, `docs/decisions.md` quand une décision change, une entrée dans `CHANGELOG.md`, la page « Nouveautés » en fr, de et en, et une ligne au catalogue des tests pour tout nouveau fichier de test. »

**#85 — Zoom de l'interface**

> **T13** — « Ctrl+ / Ctrl+= / pavé +, Ctrl− / pavé −, Ctrl+0, dans la fenêtre et sur la page d'accueil. »
>
> **T14** — « Bornes 70–200 %, pas de 10 %, gardées dans les réglages de l'utilisateur. »
>
> **T15** — « Ctrl+molette sur un formulaire, une liste ou la navigation zoome l'interface ; les dessins, les éditeurs et les pages Typst gardent leur zoom. »
>
> **T16** — « Le zoom en cours dans la barre d'état ; le menu « Affichage » avec Zoom avant, Zoom arrière, Taille réelle et Apparence, en fr, de et en. »
>
> **T17** — « Le cadre (navigation, lignes, badge, boutons) suit le zoom. »

**#86 — Vue de travail**

> **T18** — « Arriver sur un onglet le montre dans `VIEWS[0]`, sans compilation (*Flexion* en *Calcul*, *Plan de position* en *Dessin*…). »
>
> **T19** — « La vue choisie tient tant qu'on reste dans l'onglet, y compris après un enregistrement, un export, un changement de langue ou une reconstruction de la fenêtre. »
>
> **T20** — « Le réglage `views` n'est plus lu ni écrit ; une clé `views` déjà présente dans les réglages est laissée telle quelle. »

**#87 — Onglet Projet** (corps, modifié par le commentaire du 21.10.2026)

> **T21** — « L'onglet Projet, première ligne de la navigation en CU, en BP et en RS ; Ctrl+1 l'ouvre ; son icône ; ses mots en fr, de et en. »
>
> **T22** — « Le groupe « Projet » renommé « Données » / « Daten » / « Data » (la clé `nav_project` est gardée) ; aucun autre libellé « Projet » ne reste dans la navigation. »
>
> **T23** — « Ouverture d'un projet et changement de document : l'onglet Projet au premier plan, et aucune compilation de *Structure du document*. »
>
> **T24** — « La vue « Informations » avec tout le contenu ci-dessus, lu et écrit là où le projet le tient déjà. » (page de titre modifiable, langue, template de forme, template de fond de chaque document, version épinglée, dossiers des trois documents avec « Ouvrir le dossier », dernier export, « Ouvrir dans VS Code »)
>
> **T25** — « Une donnée de page de titre modifiée est reportée tout de suite dans `data/project.json`. »
>
> **T26** — « *Fichier → Propriétés du projet* ouvre l'onglet ; le dialogue reste pour « Nouveau projet ». »
>
> **T27** — « Un projet ouvert en lecture seule montre l'onglet sans permettre d'écrire. »
>
> **T28** — « Enregistrement : Comme les autres onglets : enregistré sans question quand on quitte l'onglet, change de document ou passe à une autre fenêtre (règle v0.117), avec aussi Ctrl+S et « Annuler les modifications ». »

**#88 — Aperçu des templates** (corps, modifié par le commentaire du 21.10.2026)

> **T29** — « La vue « Templates » : volet gauche (document, template de fond, template de forme, « Appliquer au projet… ») et aperçu au centre, en fr, de et en. »
>
> **T30** — « L'aperçu compile le document choisi avec les deux templates choisis et les seules données de base du projet, dans le cache de Woodcore. **Rien n'est écrit dans le dossier du projet.** »
>
> **T31** — « « Appliquer au projet… » pour la forme : confirmation, puis `forms.apply` (archive), valable pour les trois documents. »
>
> **T32** — (commentaire) « Pour le template de fond, le bouton devient **« Créer le document »**. Il n'est possible que tant que le document n'existe pas. »
>
> **T33** — « L'application est désactivée en lecture seule […] »
>
> **T34** — (commentaire) « **Clé `content_templates`** du `.woodcore` : elle est écrite à la **création du document** […]. Elle reste additive, sans changement de `schema_version`. »
>
> **T35** — « Un template personnel qui exige des données du projet peut ne pas compiler ; un bandeau le dit. » · « Il est compilé dans la **langue du projet**. » · (commentaire) « Un document déjà créé peut toujours être prévisualisé avec une autre forme. »

**#89 — Aperçus Typst**

> **T36** — « Vérifier, avec un test pour chacun, que chaque volet Typst suit sa largeur. […] Corriger ceux qui ne suivent pas. »
>
> **T37** — « Ctrl+molette zoome la page dans tous ces volets ; la molette seule défile. »
>
> **T38** — « Bouton « Ajuster à la largeur » en fr, de et en, visible seulement quand la page est zoomée. »
>
> **T39** — « Le zoom tient à travers les recompilations, et revient à la largeur sur le bouton ou en quittant l'onglet. »

**#90 — Nouveau projet minimal**

> **T40** — « Le dialogue « Nouveau projet » : nom (qui donne le nom du dossier) et emplacement, rien d'autre ; le dossier montré avant de créer, comme aujourd'hui. »
>
> **T41** — « La création fait un projet **sans langue et sans document**, avec la forme par défaut et la page de titre préremplie. Puis la fenêtre s'ouvre en mode RS, sur l'onglet Projet. »
>
> **T42** — « Onglet Projet : choisir la langue (avec confirmation, définitive) ; tant qu'elle manque, tous les autres onglets sont grisés. »
>
> **T43** — « Onglet Projet, pour chaque document : choisir un template de fond (avec l'aperçu de #88), puis « Créer le document » avec confirmation. Le document est créé dans son dossier au nom standard, et le template de fond est ensuite affiché, non modifiable. »
>
> **T44** — « Dans un mode sans document, tout est grisé sauf l'onglet Projet ; on ne compile pas et on n'exporte pas ce document. »
>
> **T45** — « « Changer de template de fond… » retiré, avec son code, ses mots et ses tests. »
>
> **T46** — « Les projets existants, qui ont déjà langue et documents, ne changent pas : leur langue et leurs templates de fond s'affichent, non modifiables. »

**#91 — Volet gauche replié**

> **T47** — « Le volet central occupe toute la place libérée dès que le volet gauche est replié, et de même quand il est déplié. »

**Demande du 22.10.2026**

> **T48** — « implémente les issues 83, 84, 85, 86, 87, 88, 89, 90 et 91. Un autre agent est toujours en cours de travail. […] regarde avec lui et attends la fin de son travail s'il y a un risque de conflit »

**Réponse à l'approbation (22.10.2026)**

> **T49** — « le choix de la langue se fait lors de la création du projet. Cette option est visible, mais grisé (donc pas modifiable) ensuite dans l'onglet projet »

## 3. Exigences fonctionnelles

### REQ-001 — Palette : ouverture et fermeture (#83)
- **Exigence** : Woodcore doit ouvrir la palette par Ctrl+K et par un clic sur le champ « Rechercher… Ctrl K » de la barre du haut, et la fermer par Échap ou par la croix en haut à droite. Tab ne fait rien ; les flèches ne déplacent pas la sélection.
- **Source** : T1, T2
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_command_palette.py` — Ctrl+K ouvre la palette ; Échap et la croix la ferment ; Tab et ↓ laissent la sélection inchangée.

### REQ-002 — Palette : catégories et préfixes (#83)
- **Exigence** : sous la barre de recherche, les catégories *Tout*, *Actions* (`>`), *Objets du projet* (`@`), *Variables* (`#`), *Normes* (`§`), *Avertissements* (`!`) se choisissent d'un clic ; taper le préfixe choisit la catégorie.
- **Source** : T2, décisions de #83
- **Priorité** : doit
- **Critère d'acceptation** : taper `@T0` choisit *Objets* et ne montre que des objets ; cliquer *Normes* ne montre que des normes.

### REQ-003 — Palette : clic, double-clic, Entrée (#83)
- **Exigence** : un clic sélectionne un élément et remplit le panneau de droite ; un double-clic l'ouvre dans son onglet et ferme la palette ; Entrée pendant la frappe ouvre le premier résultat et ferme la palette. La molette fait défiler sans sélectionner ; le survol est marqué.
- **Source** : T2, décisions de #83
- **Priorité** : doit
- **Critère d'acceptation** : test — un clic ne change pas d'onglet ; un double-clic sur l'onglet *Flexion* le met au premier plan et ferme la palette ; Entrée sur « flex » ouvre le premier résultat.

### REQ-004 — Palette : index et sources de vérité (#83)
- **Exigence** : la palette cherche dans des éléments lus à leur source, sans rien recopier :
  - **onglets** : `tab_registry.SPECS` et leurs titres traduits, limités aux onglets du document affiché ;
  - **actions** : les `QAction` que la fenêtre a déjà (barre de menus, menu du bouton PDF, vues, langue), leur texte et leur raccourci, déclenchées telles quelles (Q-002) ;
  - **objets** : les positions (`positions_store.read`) et les nœuds du graphe des dépendances (`data/dependencies.json`, `dependency_graph.read`) ;
  - **η d'une vérification** : bois par `member_check.utilisations` (calculé par `compute` sur `data/checks.json`, ARCH-015), acier lu dans `data/steel.json` (`eta`, `ok`) ;
  - **variables** : `variable_sources.read_export(here)` (sans compilation Typst) ;
  - **normes** : `calc/norms/norms.json` (`norms.references`) et les clauses que l'export cite déjà (`clause` des lignes de `checks`, `steel`, `calculations`) ;
  - **commandes Typst** : `command_docs.reference` ;
  - **avertissements** : REQ-007.
  L'index est reconstruit à chaque ouverture de la palette (rien n'est gardé entre deux ouvertures), hors du fil de l'interface s'il dépasse ~100 ms.
- **Source** : T1, T4, T10
- **Priorité** : doit
- **Critère d'acceptation** : test — une position ajoutée à `positions.json` est trouvée à la prochaine ouverture ; aucun module de la palette ne contient de liste d'onglets, d'actions ou de normes écrite en dur (`tests/test_command_palette.py`).

### REQ-005 — Palette : recherche libre (#83)
- **Exigence** : la recherche libre fait une correspondance approximative (lettres dans l'ordre) sur le nom et l'identifiant ; les résultats sont groupés par genre (onglets, vérifications avec η coloré, clauses, variables, commandes Typst), et les lettres trouvées sont soulignées.
- **Source** : T4
- **Priorité** : doit
- **Critère d'acceptation** : test du module sans Qt `calc/palette_index.py` — « flex » trouve l'onglet *Flexion* et les vérifications de flexion, avec les positions des lettres trouvées ; l'η est coloré par `theme.json` (ok / dépassé).

### REQ-006 — Palette : objets et « utilisé par » (#83)
- **Exigence** : dans *Objets*, une position montre tout ce qui l'utilise, lu dans les arêtes du graphe (`dependency_graph.downstream`) ; le panneau de droite résume (« 3 vérifications, η max 0.91 ») et propose les actions (ouvrir dans l'onglet par `MainWindow.open_object`, copier l'appel Typst, montrer sur le plan, nouvelle vérification). Le graphe est celui du dernier export ; s'il n'existe pas, la palette le dit.
- **Source** : T6, T10
- **Priorité** : doit
- **Critère d'acceptation** : test sur `tests/projet-exemple/` — `@T001` (ou une position du projet d'exemple) liste ses vérifications et ses plans tels que les donne `dependency_graph.downstream` ; le résumé donne leur nombre et l'η max (ARCH-015, `steel.json`).

### REQ-007 — Palette : avertissements (#83)
- **Exigence** : *Avertissements* liste, sans recueil nouveau, les vérifications non satisfaites (η > 1 du bois et de l'acier), les avertissements du magasin de notifications (`notifications.STORE`), les `warnings` et les vérifications non calculables (`calculable: false`, `reason`) de `checks.json`/`steel.json`, et les fichiers introuvables de `variable_sources.read_export` ; le double-clic ouvre l'objet en cause quand il en nomme un.
- **Source** : T7, T10
- **Priorité** : doit
- **Critère d'acceptation** : test — une vérification d'η 1.2 (bois calculé, acier lu) apparaît dans *Avertissements* ; une notice émise dans le magasin y apparaît aussi.

### REQ-008 — Palette vide (#83)
- **Exigence** : palette vide → les éléments ouverts récemment (dans la session) et les actions fréquentes, avec les raccourcis existants affichés en regard (lus des `QShortcut`/`QAction` eux-mêmes).
- **Source** : T3
- **Priorité** : devrait
- **Critère d'acceptation** : test — après l'ouverture de *Flexion* par la palette, elle figure en tête des récents ; Ctrl+, figure en regard de *Paramètres*.

### REQ-009 — Zoom de l'interface (#85)
- **Exigence** : Ctrl+ / Ctrl+= / pavé +, Ctrl− / pavé −, Ctrl+0 zooment l'interface de 70 à 200 % par pas de 10 %, dans la fenêtre et sur la page d'accueil ; le zoom est gardé dans les réglages de l'utilisateur (`ui_zoom`) et retrouvé au démarrage ; il survit à un changement de thème.
- **Source** : T13, T14
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_theme.py` — pas, bornes, Ctrl+0, persistance, zoom après passage clair/sombre.

### REQ-010 — Ctrl+molette (#85)
- **Exigence** : Ctrl+molette sur un formulaire, une liste ou la navigation zoome l'interface ; un dessin, un éditeur de code ou une page Typst garde son propre zoom.
- **Source** : T15
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_wheel.py` — Ctrl+molette sur un formulaire change `theme.zoom()` ; sur un `PlanCanvas` et sur un `ZoomablePdfView`, non.

### REQ-011 — Vue de travail à l'arrivée (#86)
- **Exigence** : à chaque arrivée sur un onglet, il est dans `VIEWS[0]`, sans compilation ; la vue choisie tient tant qu'on reste dans l'onglet, y compris après enregistrement, export, changement de langue ou reconstruction ; le réglage `views` n'est plus lu ni écrit, une clé `views` existante est laissée telle quelle.
- **Source** : T18, T19, T20
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_views.py` réécrit, fenêtre affichée — arriver sur *Flexion* et sur *Plan de position* ne lance aucun `request`/`request_snippet` ; un plan en *Export* le reste après `rebuild()`.

### REQ-012 — Onglet Projet : ouverture et changement de document (#87)
- **Exigence** : l'onglet Projet est la première ligne de la navigation en CU, BP et RS ; Ctrl+1 l'ouvre ; à l'ouverture d'un projet et à **chaque** changement de document, il est au premier plan, et *Structure du document* ne compile rien tant qu'il n'est pas visible.
- **Source** : T21, T23
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_modes_window.py` et `tests/test_structure_tab.py` — après avoir affiché *Structure* puis changé de document depuis *Projet*, aucun `request_preview` n'est lancé.

### REQ-013 — Onglet Projet : vue « Informations » (#87, #90)
- **Exigence** : la vue « Informations » (par défaut, ne compile rien) montre en cartes :
  - la page de titre, modifiable (nom, numéro, client, adresse, bureau, auteur, vérificateur), lue par `Project.detail` et écrite par `project.update` ; un nom vide est refusé ;
  - la langue du projet : affichée, grisée, non modifiable (REQ-019) ;
  - le template de forme en usage (`forms.current`), avec « Appliquer au projet… » (REQ-016) ;
  - pour chaque document, son template de fond (`content_templates`, « inconnu » pour un projet plus ancien, « introuvable » s'il n'existe plus sur la machine), ou « pas encore créé » avec le choix et « Créer le document » (REQ-020) ;
  - la version de Woodcore épinglée, modifiable ;
  - les dossiers des trois documents en lecture seule, avec « Ouvrir le dossier » ;
  - le dernier export : sa date et la version du moteur qui l'a écrit ;
  - « Ouvrir dans VS Code ».
  L'onglet s'enregistre comme les autres (quitter l'onglet, changer de document, autre fenêtre, Ctrl+S, « Annuler les modifications »).
- **Source** : T24, T28, T46
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_project_tab.py` — chaque carte lit sa valeur à la source nommée ; une modification du client est écrite dans le `.woodcore` en quittant l'onglet ; un nom vide est refusé.

### REQ-014 — Report immédiat de la page de titre (#87)
- **Exigence** : une donnée de page de titre enregistrée réécrit tout de suite `data/project.json` seul, par la fonction de l'export qui l'écrit et validé contre son schéma, sans toucher aux tampons d'export (Q-003), sans faire croire que tout l'export est à jour.
- **Source** : T25
- **Priorité** : doit
- **Critère d'acceptation** : test — après l'enregistrement du client, `data/project.json` le porte et reste valide contre son schéma ; l'état d'export de la fenêtre n'est pas déclaré à jour.

### REQ-015 — Propriétés du projet et lecture seule (#87)
- **Exigence** : *Fichier → Propriétés du projet* ouvre l'onglet Projet (après `autosave_all`) ; le dialogue ne sert plus qu'à « Nouveau projet » ; en lecture seule, l'onglet est affiché sans rien permettre d'écrire (`GUARDED_TABS`, `WRITERS`).
- **Source** : T26, T27
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_project_tab.py` — le menu met l'onglet au premier plan ; en lecture seule les champs et boutons sont désactivés et `tab_guard` refuse chaque méthode qui écrit.

### REQ-016 — Vue « Templates » : aperçu et forme (#88)
- **Exigence** : la vue « Templates » a un volet gauche (document CU · BP · RS ; template de fond limité à la langue du projet ; template de forme ; « Appliquer au projet… » pour la forme ; « Créer le document » pour le fond tant que le document n'existe pas) et l'aperçu au centre. Choisir dans une liste ne change que l'aperçu. L'aperçu compile le document entier avec les deux templates et les seules données de base du projet, dans la langue du projet, dans un projet jetable du cache (`usersettings.cache_dir("template-preview")`) ; **rien n'est écrit dans le dossier du projet**. Un template qui ne compile pas sans données le dit par un bandeau. La construction est hors du fil de l'interface, seule la dernière demande comptant. Appliquer la forme demande confirmation puis appelle `forms.apply` (archive), pour les trois documents. Un document déjà créé se prévisualise avec une autre forme.
- **Source** : T29, T30, T31, T35
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_template_preview.py` — importable sans PySide6 ; projet identique (fichiers et dates) avant et après ; formes neutre et BFH compilées ; effacement avec moteur en lecture seule ; codes d'erreur traduits.

### REQ-017 — Lecture seule et rapport seul (#88)
- **Exigence** : « Appliquer au projet… » et « Créer le document » sont désactivés en lecture seule ; « Créer le document » n'existe pas pour un projet en rapport seul (sans `typst_root`).
- **Source** : T33
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_project_tab.py`.

### REQ-018 — Nouveau projet : nom et emplacement (#90)
- **Exigence** : le dialogue « Nouveau projet » ne demande que le nom (qui est le nom du dossier), l'emplacement et la **langue** (proposée : `templates.defaults(settings)["report_language"]`), et montre le dossier avant de créer. La création fait un projet **dans cette langue et sans document**, avec la forme par défaut des réglages et la page de titre préremplie (auteur, bureau, vérificateur des réglages) ; la fenêtre s'ouvre en mode RS, sur l'onglet Projet.
- **Source** : T40, T41, T49
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_new_project.py`, `tests/test_project_dialog.py` — le dialogue a trois champs (nom, emplacement, langue) ; le projet créé porte `doc-lang` dans `config.typ`, s'ouvre sans erreur, sans document, en RS sur *Projet*.

### REQ-019 — Langue choisie à la création, définitive (#90)
- **Exigence** : la langue est choisie dans le dialogue « Nouveau projet » (REQ-018) et écrite une fois à la création (`config.typ`, `doc-lang`) ; tout document créé ensuite la reçoit (`templates.write_project_languages`). Dans l'onglet Projet, elle est visible mais grisée, jamais modifiable, pour un projet neuf comme pour un projet existant.
- **Source** : T42 (modifié par T49), T46
- **Priorité** : doit
- **Critère d'acceptation** : test — projet créé en français : `config.typ` porte `doc-lang = "fr"` ; le champ de langue de l'onglet Projet est désactivé ; un RS créé ensuite est en français.

### REQ-020 — Créer un document (#88, #90)
- **Exigence** : pour un document pas encore créé, l'onglet Projet propose un template de fond (avec l'aperçu de REQ-016) puis « Créer le document » avec confirmation. Le document est créé dans son dossier au nom standard (`documents.MODE_FOLDERS`), son template est inscrit dans `content_templates`, le partage avec les documents déjà là est réglé (`settle_sharing`), puis le template de fond est affiché, non modifiable.
- **Source** : T32, T34, T43
- **Priorité** : doit
- **Critère d'acceptation** : test — créer le RS seul : `300-Statical report/Statischer Rapport.typ` existe, `content_templates.rs` est écrit, la CU reste « pas encore créé ».

### REQ-021 — Mode sans document (#90)
- **Exigence** : dans un mode dont le document n'existe pas, tout est grisé sauf l'onglet Projet ; ce document ne se compile pas et ne s'exporte pas (« Exporter les trois » l'omet, l'export PDF du mode est désactivé avec une raison).
- **Source** : T44
- **Priorité** : doit
- **Critère d'acceptation** : test — projet avec RS seul, mode CU : la navigation n'a que *Projet* actif ; `export_pdf` ne lance pas de compilation de la CU.

### REQ-022 — Retrait de « Changer de template de fond… » (#90)
- **Exigence** : `calc/content_switch.py`, `calc/tools/content_switch_dialog.py`, leur appel (`structure_tab_share.py`), leurs mots et leurs tests (`tests/test_content_switch*.py`, `test_broad_excepts.py`) sont retirés ; les docs qui les décrivent le disent ; `docs/decisions.md` consigne que la décision v0.114 est remplacée.
- **Source** : T45
- **Priorité** : doit
- **Critère d'acceptation** : `grep -r content_switch calc tests` ne trouve rien hors de l'historique ; la suite passe.

### REQ-023 — Projets existants inchangés (#90)
- **Exigence** : un projet qui a déjà langue et documents s'ouvre comme aujourd'hui ; sa langue et ses templates de fond s'affichent, non modifiables ; aucun fichier du projet n'est réécrit à l'ouverture pour cela. Un projet en rapport seul reste un projet en rapport seul.
- **Source** : T46
- **Priorité** : doit
- **Critère d'acceptation** : test sur `tests/projet-exemple/` — ouverture, export et octets de `data/project.json` identiques avant et après la version.

### REQ-024 — Aperçus Typst : largeur et Ctrl+molette (#89)
- **Exigence** : chaque volet Typst (*Structure du document*, vue *Affichage* des onglets, vue *Affichage* des plans, dossiers d'export, aperçu de la vue « Templates ») suit la largeur de son volet ; Ctrl+molette zoome la page centrée sous le pointeur, par pas de 10 % ; la molette seule défile ; le zoom tient à travers les recompilations ; un bouton « Ajuster à la largeur », visible seulement quand la page est zoomée, remet la largeur, et quitter l'onglet aussi.
- **Source** : T36, T37, T38, T39
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_pdf_pane.py` — 800 → 400 px divise la largeur de page par deux ; Ctrl+molette donne ×1,1 et `Custom` ; la molette seule ne zoome pas ; le bouton rétablit `FitToWidth` ; un cas par volet hôte.

### REQ-025 — Volet gauche replié (#91)
- **Exigence** : replier ou déplier le volet gauche d'un onglet donne tout de suite la place libérée au volet voisin, sans redimensionnement.
- **Source** : T47
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_chrome.py` — juste après `set_folded(True)`, la largeur du volet central vaut la largeur du séparateur moins la flèche et les autres volets ; et à l'inverse au dépli.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Aspect de la palette (#83)
- **Exigence** : fenêtre flottante centrée en haut de la fenêtre principale, toujours large : liste à gauche, panneau de détail à droite toujours en place (« Cliquez sur un élément pour voir son détail et ses actions » sans sélection), rien ne se décale au premier clic ; pas de bas de palette rappelant les touches ; couleurs de `theme.json`.
- **Source** : T2, décisions de #83
- **Langues** : fr / de / en (mots de la palette dans un `STRINGS` à côté de son module, fusionné par `woodcore_gui_words.py`)
- **Critère d'acceptation** : test — la largeur du panneau de droite est la même avant et après le premier clic ; `tests/test_i18n.py` couvre les mots.

### UI-002 — Menu « Affichage » et barre d'état (#85)
- **Exigence** : un menu « Affichage » / « Ansicht » / « View » avec *Zoom avant*, *Zoom arrière*, *Taille réelle* et leurs raccourcis, et le sous-menu *Apparence* déplacé depuis *Fichier* ; « Zoom 120 % » dans la barre d'état quand le zoom n'est pas 100 %.
- **Source** : T16
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_i18n.py`, test du menu.

### UI-003 — Le cadre suit le zoom (#85)
- **Exigence** : largeur de la navigation, hauteur de ses lignes, badge, bouton de mode et marques suivent le zoom par une seule aide `theme.scaled(px)` ; le nom du projet dans la barre du haut aussi. Les autres tailles fixes des onglets restent : limite documentée.
- **Source** : T17
- **Langues** : —
- **Critère d'acceptation** : `tests/test_chrome.py` — à 150 %, `ENTRY_HEIGHT` affiché vaut 48 px.

### UI-004 — Onglet Projet dans la navigation (#87)
- **Exigence** : « Projet » / « Projekt » / « Project », icône propre, première ligne de la navigation ; le groupe « Projet » devient « Données » / « Daten » / « Data » (clé `nav_project` gardée) ; vues « Informations » / « Angaben » / « Details » et « Templates » / « Vorlagen » / « Templates », à clés propres dans `views.py`.
- **Source** : T21, T22
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_chrome.py` — aucun libellé « Projet » ne reste dans les groupes ; `tests/test_i18n.py`.

### UI-005 — Onglets grisés (#90)
- **Exigence** : un onglet indisponible (document du mode affiché pas encore créé) est grisé dans la navigation, avec en info-bulle le mot qui renvoie à l'onglet Projet ; Ctrl+n ne l'ouvre pas.
- **Source** : T44
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de la navigation (`tests/test_chrome.py`).

### UI-006 — Bouton « Ajuster à la largeur » (#89)
- **Exigence** : le bouton, en fr / de / en, n'est visible que quand la page est zoomée.
- **Source** : T38
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_pdf_pane.py`.

## 5. Exigences d'architecture

### ARCH-001 — Index de la palette sans Qt
- **Exigence** : l'index et la recherche vivent dans un module sans Qt (`calc/palette_index.py` : les éléments, leur genre, leurs sources, la correspondance approximative, le résumé « utilisé par ») ; la fenêtre (`calc/tools/command_palette.py`) affiche et appelle. Aucune liste recopiée : onglets, actions, normes, commandes et objets sont lus à leur source (REQ-004).
- **Source** : principes 1 et « Domain logic is independent of the UI » (CLAUDE.md), T10
- **Critère d'acceptation** : `calc/palette_index.py` s'importe sans PySide6 (test).

### ARCH-002 — Zoom dans `theme.py`
- **Exigence** : `theme.zoom()` / `theme.set_zoom()` / `theme.scaled(px)`, sur le modèle de `appearance()` ; jamais par `theme.apply` (qui s'arrête tôt et remet la taille de police) ; polices de la fenêtre recalculées par `MainWindow.take_fonts()` ; reconstructions regroupées (~300 ms).
- **Source** : revue d'architecture de #85
- **Critère d'acceptation** : `tests/test_theme.py`.

### ARCH-003 — Vue remise au départ d'un onglet
- **Exigence** : `VIEWS[0]` est remise comme simple état (`set_view(first, enter=False)`) sur l'onglet **quitté** (à côté de `leave_tab`), à la construction et dans `apply_mode` ; la vue de l'onglet affiché est gardée en mémoire à travers `rebuild()`/`refresh_tab()` ; `remembered`/`with_view` remplacés par `views.default(tab)` ; pendant `begin_variable_pick`, l'onglet qui a demandé n'est pas remis (`self.picking`).
- **Source** : revue d'architecture de #86
- **Critère d'acceptation** : `tests/test_views.py`, `test_formula_tab.py`, `test_linkable_spin.py`.

### ARCH-004 — Une classe `ZoomablePdfView`
- **Exigence** : une seule sous-classe de `QPdfView` dans `pdf_pane.py`, utilisée par `PdfPane` et `BundlePages`, avec `fit()` et Ctrl+molette ; un seul pas de zoom de 1,1 pour elle (le pas 1,25 de `SheetCanvas`, dessin vectoriel, reste et sa raison est écrite).
- **Source** : revue d'architecture de #89
- **Critère d'acceptation** : `tests/test_pdf_pane.py`.

### ARCH-005 — Création en deux temps
- **Exigence** : `project_template.create` est scindé en `create_skeleton(..., language)` (`.woodcore`, plan complet des trois dossiers aux noms `MODE_FOLDERS` et entrées aux noms de la langue (Q-004, T49), configuration, moteur, forme, page de titre) et `create_document(here, mode, template)` (`doc_templates.instantiate` au dossier standard, `content_templates`, `settle_sharing`, `write_project_languages` pour ce document), réutilisant les fonctions existantes sans les recopier ; la langue est écrite par le squelette. `create(...)` reste disponible (CLI, tests) comme le squelette suivi des trois documents.
- **Source** : #90 « Points à étudier »
- **Critère d'acceptation** : `tests/test_new_project.py` — `create(...)` produit les mêmes fichiers qu'avant ; squelette + RS produit un projet qui s'exporte.

### ARCH-006 — `content_templates` additive
- **Exigence** : clé `content_templates` (`{cu, bp, rs}`, référence du template de fond) dans le `.woodcore` et son schéma, **sans** changer `schema_version` ; lue par `Project.content_template(mode)`, écrite par `project.set_content_template(...)` qui relit le fichier ; `data/project.json` identique octet pour octet.
- **Source** : T34, revue de #88
- **Critère d'acceptation** : `tests/test_project.py` — un ancien fichier se lit ; la clé s'écrit ; l'export est identique.

### ARCH-007 — Aperçu des templates sans Qt
- **Exigence** : `calc/template_preview.py` (`prepare`, `clean`, `TemplatePreviewError` avec codes traduits) construit le projet jetable par `create_skeleton`/`create_document` et `export_all.seed`, ne lit du vrai projet que le nom, la page de titre et la langue, et efface par `project_template.remove_tree` (l'actuel `_undo` rendu public).
- **Source** : revue de #88
- **Critère d'acceptation** : `tests/test_template_preview.py`.

### ARCH-008 — Une source pour les détails du projet
- **Exigence** : `project.details_of(here)` ; (le widget partagé `project_details.py` prévu par la revue n'a plus lieu d'être depuis T49 : le dialogue « Nouveau projet » ne montre plus la page de titre, l'onglet Projet est seul à la montrer) ; la fin de l'enregistrement des propriétés est extraite dans `properties_written()` ; `apply_form()` extrait de `home_page.py` sert l'onglet ; une seule fonction pour le libellé « nom — emplacement » (aujourd'hui trois copies) ; le nom du projet de la barre du haut est rafraîchi après écriture.
- **Source** : revue de #87 et #88
- **Critère d'acceptation** : `tests/test_no_duplicates.py` (garde existante) passe ; test du rafraîchissement du nom.

### ARCH-009 — Griser par la navigation
- **Exigence** : la disponibilité d'un onglet est décidée une fois (`MainWindow.available(tab)` d'après la langue et l'existence du document) et appliquée par `chrome.SideNav`, `apply_mode`, les raccourcis et les boutons d'export, jamais onglet par onglet.
- **Source** : #90 « Points à étudier »
- **Critère d'acceptation** : test de la fenêtre.

## 6. Contraintes

- **CON-001** — Trois langues pour tout mot nouveau, dans les `STRINGS` des modules, tenues par `tests/test_i18n.py`. Source : CLAUDE.md (inférée).
- **CON-002** — `schema_version` du `.woodcore` inchangée (1.1) : un Woodcore plus ancien du bureau ouvre toujours le projet. Source : T34.
- **CON-003** — Un projet existant (langue et documents) ne change ni à l'ouverture ni à l'export ; `data/project.json` identique octet pour octet. Source : T46, revue de #88.
- **CON-004** — Rien n'est écrit dans le dossier du projet par l'aperçu des templates. Source : T30.
- **CON-005** — Les tests ne touchent que `tests/projet-exemple/` et des dossiers temporaires, jamais un projet de l'ingénieur. Source : CLAUDE.md (inférée).
- **CON-006** — Plusieurs sessions éditent le dépôt : pas de `git checkout --`, `stash`, `reset`, `clean` ; `CHANGELOG.md`, la page « Nouveautés » et `docs/decisions.md` édités par Edit ciblé, après le commit de la session « Typst commands standardization ». Source : T48, CLAUDE.md.
- **CON-007** — Aucun fichier de `docs/` hormis `decisions.md` ne dépasse 100 KB (`docs/ui/window.md` fait 73 KB : la palette va dans `docs/ui/command-palette.md`, l'onglet dans `docs/ui/tab-project.md`). Source : CLAUDE.md (inférée).

## 7. Décisions prises

Toutes du 21.10.2026 (issues), sauf mention.

- **#83** : Ctrl+K ; catégories sous la barre (Tout, `>`, `@`, `#`, `§`, `!`) ; navigation à la souris, Tab et flèches sans effet ; clic = sélectionner, double-clic = ouvrir et fermer ; Entrée = premier résultat ; Échap ou croix ; pas de bas de palette ; panneau de droite toujours en place.
- **#85** : 70–200 %, pas 10 %, réglage utilisateur ; Ctrl+molette selon la cible ; « Zoom 120 % » dans la barre d'état ; nouveau menu « Affichage » avec *Apparence* déplacé ; le cadre suit, les autres tailles fixes non (limite documentée) ; la page d'accueil suit.
- **#86** : `VIEWS[0]` à chaque arrivée ; abandon du réglage `views` (décision v0.117 « en partie remplacée »).
- **#87** : onglet « Projet » premier ; groupe « Projet » renommé « Données » ; ouverture et chaque changement de document sur l'onglet Projet ; vues « Informations » et « Templates » ; report immédiat de la page de titre dans `data/project.json` ; *Propriétés du projet* ouvre l'onglet.
- **#88 / #90** : le template de fond se choisit une fois, à la création du document (« Créer le document ») ; la forme reste modifiable à tout moment et vaut pour les trois documents ; `content_templates` additive, sans changement de version de schéma ; « Changer de template de fond… » retiré.
- **#89** : Ctrl+molette ×1,1 centré sous le pointeur ; retour à la largeur seulement sur demande (bouton) ou en quittant l'onglet.
- **#90** : dialogue nom + emplacement ; langue choisie en premier, définitive ; autres onglets grisés tant qu'elle manque ; dossier au nom standard sans question.
- **Q-001 → A** (22.10.2026) : la palette en entier (onglets, actions, objets, variables, normes, commandes, avertissements) dans cette série.
- **Q-002 → A** : les actions de la palette sont les `QAction` de la fenêtre, lues et déclenchées ; aucune table d'actions nouvelle.
- **Q-003 → A** : la page de titre enregistrée réécrit `data/project.json` seul, par la fonction de l'export, validé, tampons inchangés.
- **Q-004 → A** : un document « pas encore créé » est un document dont le fichier d'entrée n'existe pas ; le plan des trois dossiers est écrit à la création ; aucune clé nouvelle.
- **Q-005 → A** : un commit par lot, une version 0.122.0 à la fin.
- **Q-006 → A** : vues, langue de la fenêtre et « nouvelle vérification » construites à leur source dans la palette.
- **Q-007 → langue à la création (T49)** : la langue se choisit dans le dialogue « Nouveau projet », puis reste visible et grisée dans l'onglet Projet. Cela remplace la décision de #90 « la langue se choisit dans l'onglet Projet, en premier » et l'exigence « tant qu'elle manque, tous les autres onglets sont grisés » : l'état « projet sans langue » n'existe pas. Prix accepté : aucun.
- **Nom standard des dossiers** (déduit du code, confirmé par Q-004 le 22.10.2026) : depuis la 0.119, le nom standard est `documents.MODE_FOLDERS` (« 100-Service criteria agreement », « 200-Basis of design », « 300-Statical report »), le même dans toutes les langues. L'exemple « 3_Rapport de statique » de #90 est l'ancien nommage (`LEGACY_MODE_FOLDERS`) ; c'est `MODE_FOLDERS` qui est appliqué.

## 8. Hors périmètre

- Créer ou modifier un template de fond ou de forme (reste dans *Fichier → Paramètres… → Modèles de document*).
- Changer la langue ou le template de fond d'un projet après les avoir choisis.
- Une forme différente par document.
- Les SVG faits par Python (charges, connecteurs, moments polaires) : ce ne sont pas des pages Typst (#89).
- Les ~40 tailles fixes propres aux onglets ne suivent pas le zoom (#85).
- La navigation au clavier dans la palette (flèches, Tab).
- Un projet sans langue (T49) : la langue est toujours connue dès la création.

## 9. Idées non retenues comme exigences

- Modèles de palette cités (VS Code, Linear, Figma, Raycast) : inspiration, pas exigence.
- Les η, efforts et ID des maquettes (SC-01, KI-01, KN-02, T004) sont inventés pour l'exemple.
- « Ordre en trois phases possible » (#83) : ordre de livraison, tranché par Q-001.

## 10. Questions

### Q-001 — La palette en entier maintenant, ou par phases ?
- **Pourquoi elle compte** : la phase 3 (avertissements) dépend de ce que le magasin de notifications garde ; la livrer maintenant allonge le travail.
- **Options** : A (recommandée) les trois phases dans cette série ; B la phase 1 (onglets, actions) seule, le reste dans une issue de suite.
- **Réponse** : A — les trois phases (ingénieur, 22.10.2026).

### Q-002 — D'où viennent les actions de la palette ?
- **Pourquoi elle compte** : aucune liste d'actions n'existe ; chaque `QAction` est construite dans son menu ou dans le bouton PDF.
- **Options** : A (recommandée) la palette lit les `QAction` que la fenêtre a déjà (barre de menus, menu du bouton PDF, commutateur de vue, langue), leur texte et leur raccourci, et les déclenche : rien n'est recopié, une action ajoutée à un menu apparaît seule ; B une table d'actions nouvelle d'où les menus et la palette sont construits : plus propre, mais tous les menus sont réécrits.
- **Réponse** : A — lire les `QAction` existantes (ingénieur, 22.10.2026).

### Q-003 — Comment reporter tout de suite la page de titre dans `data/project.json` ?
- **Pourquoi elle compte** : `data/` n'est écrit que par l'export, validé, et les tampons d'export disent ce qui est à jour.
- **Options** : A (recommandée) réécrire `data/project.json` seul par la fonction même de l'export qui l'écrit (`project.record`, validé contre son schéma), sans toucher aux tampons : le prochain export le refera de toute façon ; B attendre le prochain export (abandonne la décision du 21.10.2026).
- **Réponse** : A — réécrire `data/project.json` seul, validé, sans toucher aux tampons (ingénieur, 22.10.2026).

### Q-004 — Comment noter qu'un document n'est pas encore créé ?
- **Pourquoi elle compte** : c'est une forme de données du `.woodcore` ; aujourd'hui les six clés de dossiers des documents vont toutes ensemble, et un projet sans elles est lu comme un « rapport seul ».
- **Options** : A (recommandée) le plan des trois dossiers est écrit dès la création (noms standard, sans langue) ; un document « pas encore créé » est un document dont le fichier d'entrée n'existe pas ; aucune clé nouvelle ; B une clé `documents: ["rs", …]` dans le `.woodcore`, additive : explicite, mais une seconde vérité à côté des fichiers.
- **Réponse** : A — plan des trois dossiers écrit à la création, document « pas encore créé » = fichier d'entrée absent ; noms `MODE_FOLDERS` (ingénieur, 22.10.2026).

### Q-005 — Livraison
- **Pourquoi elle compte** : neuf issues, des dizaines de fichiers.
- **Options** : A (recommandée) un commit par lot (#91 ; #86 ; #89 ; #85 ; #87 + #88 + #90 ; #83), une version 0.122.0 et une page « Nouveautés » à la fin ; B un seul commit.
- **Réponse** : A — un commit par lot, une version 0.122.0 à la fin (ingénieur, 22.10.2026).

### Q-006 — Palette : vues, langue et « nouvelle vérification »
- **Pourquoi elle compte** : ce ne sont pas des `QAction` (Q-002 ne les couvre pas) ; « nouvelle vérification » suppose de choisir quel onglet de vérification.
- **Options** : A (recommandée) la palette les construit à partir de leurs sources (`views.declared(tab)` et ses mots pour les vues de l'onglet affiché, `LANGUAGES` pour la langue) et appelle les méthodes de la fenêtre ; « nouvelle vérification » propose les onglets de vérification (ceux dont `GRAPH_KIND` est `check` ou `steel`, lus dans le registre) et ouvre une vérification neuve sur la position ; B les retirer de la palette.
- **Réponse** : A — construits à leur source, méthodes de la fenêtre appelées (ingénieur, 22.10.2026).

### Q-007 — Nom du fichier d'entrée d'un document créé avant la langue
- **Pourquoi elle compte** : la CU et la BP ont un nom de fichier par langue (`Nutzungsvereinbarung.typ`, `Convention d'utilisation.typ`…), et le `.woodcore` doit nommer les trois entrées dès la création (Q-004).
- **Options** : A (recommandée) le squelette écrit des noms provisoires, remplacés par ceux de la langue au moment où elle est choisie (aucun fichier n'existe encore) : les projets gardent les noms d'aujourd'hui ; B des noms d'entrée fixes et sans langue, comme les dossiers depuis la 0.119 : plus simple, mais tout nouveau projet change de nommage.
- **Réponse** : ni A ni B — l'ingénieur, 22.10.2026, telle quelle : « le choix de la langue se fait lors de la création du projet. Cette option est visible, mais grisé (donc pas modifiable) ensuite dans l'onglet projet ». La langue est donc connue dès la création : les noms d'entrée sont ceux d'aujourd'hui, et l'état « projet sans langue » n'existe plus (T49).

## 11. Critères d'acceptation

- [x] REQ-001 — Ctrl+K / champ ouvrent ; Échap / croix ferment ; Tab et flèches sans effet.
- [x] REQ-002 — catégories cliquables et préfixes `> @ # § !`.
- [x] REQ-003 — clic sélectionne, double-clic ouvre et ferme, Entrée ouvre le premier.
- [x] REQ-004 — index lu aux sources, reconstruit à l'ouverture, rien en dur.
- [x] REQ-005 — recherche approximative groupée, lettres soulignées, η coloré.
- [x] REQ-006 — « utilisé par » du graphe, résumé et actions.
- [x] REQ-007 — avertissements : η > 1, notices, fichiers introuvables.
- [x] REQ-008 — palette vide : récents, actions fréquentes, raccourcis.
- [x] REQ-009 — zoom 70–200 %, pas 10 %, persistant, survit au thème.
- [x] REQ-010 — Ctrl+molette selon la cible.
- [x] REQ-011 — `VIEWS[0]` à l'arrivée, sans compilation ; vue gardée dans l'onglet ; `views` ignoré.
- [x] REQ-012 — Projet premier, Ctrl+1, ouverture et changement de document sans compilation de *Structure*.
- [x] REQ-013 — vue « Informations » complète, lue et écrite aux sources.
- [x] REQ-014 — `data/project.json` reporté tout de suite, valide.
- [x] REQ-015 — *Propriétés du projet* ouvre l'onglet ; lecture seule.
- [x] REQ-016 — vue « Templates » : aperçu sans écrire dans le projet ; forme appliquée aux trois.
- [x] REQ-017 — application désactivée en lecture seule / rapport seul.
- [x] REQ-018 — dialogue nom + emplacement + langue ; projet vide ouvert en RS sur *Projet*.
- [x] REQ-019 — langue écrite à la création, grisée dans l'onglet Projet.
- [x] REQ-020 — « Créer le document » au dossier standard, `content_templates` écrit.
- [x] REQ-021 — mode sans document : grisé, ni compilé ni exporté.
- [x] REQ-022 — `content_switch` retiré avec mots, tests, docs ; décision consignée.
- [x] REQ-023 — projets existants inchangés, export identique.
- [x] REQ-024 — volets Typst à la largeur, Ctrl+molette, bouton, zoom tenu.
- [x] REQ-025 — volet gauche replié : place rendue tout de suite.
- [x] UI-001 à UI-006 — palette large, menu « Affichage », cadre zoomé, onglet Projet et groupe « Données », onglets grisés, bouton « Ajuster à la largeur », en fr/de/en.
- [x] ARCH-001 à ARCH-009 — modules sans Qt, une source par donnée, `schema_version` inchangée.
- [x] Documentation : `docs/ui/window.md`, `docs/ui/command-palette.md` (nouveau), `docs/ui/tab-project.md` (nouveau), `docs/ui/tab-structure.md`, `docs/domain/documents.md`, `docs/architecture/layout.md`, `docs/README.md`, `docs/decisions.md`, `docs/decisions-index.md`, `CHANGELOG.md`, « Nouveautés » 0.122.0 fr/de/en.
- [x] Tests : `test_command_palette.py`, `test_palette_index.py`, `test_project_tab.py`, `test_template_preview.py` (nouveaux) ; `test_theme`, `test_wheel`, `test_views`, `test_chrome`, `test_pdf_pane`, `test_structure_tab`, `test_modes_window`, `test_project`, `test_new_project`, `test_project_dialog`, `test_home`, `test_i18n` étendus ; lignes au catalogue ; suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-004 | capturé |
| T2 | REQ-001, REQ-002, REQ-003, UI-001 | capturé |
| T3 | REQ-008 | capturé |
| T4 | REQ-004, REQ-005 | capturé |
| T5 | REQ-004 (actions) | capturé (Q-002 → A) |
| T6 | REQ-006 | capturé |
| T7 | REQ-007 | capturé |
| T8 | UI-001, REQ-004 (document affiché), CON-001 | capturé |
| T9 | §11 documentation et tests | capturé |
| T10 | REQ-004, REQ-006, REQ-007, ARCH-001 | capturé (Q-001 → A) |
| T11 | §14 ordre | capturé |
| T12 | §11 documentation | capturé |
| T13 | REQ-009 | capturé |
| T14 | REQ-009 | capturé |
| T15 | REQ-010 | capturé |
| T16 | UI-002 | capturé |
| T17 | UI-003, ARCH-002 | capturé |
| T18 | REQ-011, ARCH-003 | capturé |
| T19 | REQ-011 | capturé |
| T20 | REQ-011 | capturé |
| T21 | REQ-012, UI-004 | capturé |
| T22 | UI-004 | capturé |
| T23 | REQ-012 | capturé |
| T24 | REQ-013, ARCH-008 | capturé |
| T25 | REQ-014 | capturé (Q-003 → A) |
| T26 | REQ-015 | capturé |
| T27 | REQ-015 | capturé |
| T28 | REQ-013 | capturé |
| T29 | REQ-016 | capturé |
| T30 | REQ-016, CON-004, ARCH-007 | capturé |
| T31 | REQ-016 | capturé |
| T32 | REQ-020 | capturé |
| T33 | REQ-017 | capturé |
| T34 | ARCH-006, CON-002 | capturé |
| T35 | REQ-016 | capturé |
| T36 | REQ-024 | capturé |
| T37 | REQ-024, ARCH-004 | capturé |
| T38 | REQ-024, UI-006 | capturé |
| T39 | REQ-024 | capturé |
| T40 | REQ-018 | capturé |
| T41 | REQ-018, ARCH-005 | capturé (Q-004 → A) |
| T42 | REQ-019 | capturé, modifié par T49 |
| T43 | REQ-020 | capturé |
| T44 | REQ-021, UI-005, ARCH-009 | capturé |
| T45 | REQ-022 | capturé |
| T46 | REQ-023, CON-003 | capturé |
| T47 | REQ-025 | capturé |
| T48 | CON-006 | capturé |
| T49 | REQ-018, REQ-019, §7 (Q-007) | capturé |

### Points de la source non résolus

Aucun : Q-001 à Q-004 tranchées le 22.10.2026 ; Q-005 (livraison) posée à l'approbation.

## 13. Revue d'architecture

Trois revues `architecture-reviewer` (Sonnet) le 22.10.2026, en parallèle : palette (#83) ; onglet Projet, aperçu, nouveau projet (#87, #88, #90) ; zoom, vues, aperçus Typst, volet replié (#85, #86, #89, #91 : les notes des issues revérifiées sur le code de la v0.121, numéros de ligne périmés corrigés). **Verdict des trois : APPROUVER AVEC RÉSERVES.**

### 13.1 Palette (#83)

- **ARCH-RISK-101 (bloquant)** — l'η du bois n'est **pas** dans `data/checks.json` (ni `eta` ni `ok` : `vars`, `calculable`, `reason`, `warnings`). Il est calculé par `member_check.compute(record)` (`member_check.py:687`) ; l'acier écrit `eta`/`ok` dans `data/steel.json`. → `member_check.utilisations(...)` (ARCH-015) et lecture de `steel.json`, appelées par l'index ; tolérance 1e-9 du domaine ; couleurs `theme.colour("ok"|"danger")`.
- **ARCH-RISK-102 (bloquant)** — `tests/projet-exemple/` n'a pas de `data/dependencies.json` : les tests de REQ-006 exportent dans un dossier temporaire (ou fabriquent un graphe minimal) ; « pas de graphe » a son mot.
- **ARCH-RISK-103 (important)** — lire les `QAction` : parcours récursif de la barre de menus **et** du menu du bouton PDF (`pdf_button.menu()`), séparateurs et actions sans texte ignorés, `&` retiré, chemin du menu gardé, actions désactivées grisées et non déclenchées, état lu à chaque ouverture (`build_menu` fait `bar.clear()`) ; la palette se ferme avant de déclencher. Les vues (`SegmentedSwitch`) et la langue (`LanguageSwitch`) ne sont pas des `QAction` → Q-006.
- **ARCH-RISK-104** — Ctrl+1…9 sont des `QShortcut` (`window.shortcuts`), lus pour être affichés ; la palette est inerte pendant `begin_variable_pick`.
- **ARCH-RISK-105** — le champ « Rechercher… Ctrl K » de la barre du haut n'existe pas : il est créé (UI-001).
- **ARCH-RISK-106/107** — l'index suit le document affiché (`current_document()`, `MODE_TABS`, sections `section:<mode>/`) ; un onglet indisponible (#90) n'est pas ouvert. Avertissements de quatre sources, sans recueil nouveau : `notifications.STORE.items()` (textes par `notifications.message`), `warnings` des enregistrements de `checks.json`/`steel.json`, `calculable: false` + `reason` (données manquantes), `read_export().missing`/`errors` (fichiers introuvables). Le magasin vit dans le processus : ce qu'un export a dit y arrive à la fin de l'export.
- **ARCH-RISK-108 (important)** — aucun onglet n'a `GRAPH_KIND = "position"` : `PositionsTab` reçoit le contrat `GRAPH_KIND`/`lists_object`/`open_object` des autres onglets (ARCH-013) ; « Ouvrir » est grisé pour un nœud sans onglet.
- **ARCH-RISK-109** — le « utilisé par » transitif est dans le widget `dependencies_tab.lines` : la boucle est extraite vers `dependency_graph.reachable(...)` (ARCH-014).
- **ARCH-RISK-110** — normes : seuls 28 des 106 fichiers de `calc/norms/` ont une clé `clause` ; on n'indexe pas les fichiers mais `norms.references()` et les clauses que l'export cite déjà (`clause` des lignes de `checks`, `steel`, `calculations`).
- **ARCH-RISK-111 à 116 (mineurs)** — lectures en dizaines de ms, `member_check.compute` à mesurer (fil séparé si > 100 ms) ; « copier l'appel Typst » par `command_docs.calls` et `dependency_graph.COMMAND_REFERENCES` ; « montrer sur le plan » par les arêtes `plan → position` puis `open_object("plan:…")` ; « nouvelle vérification » → Q-006 ; table catégories ↔ préfixes déclarée une fois dans `palette_index` ; `palette_index` reçoit onglets et actions en paramètres (`Entry`) sans importer `calc/tools/` ; un fichier illisible est dit par une ligne, jamais avalé ; récents en mémoire pour la session.

### 13.2 Onglet Projet, aperçu, nouveau projet (#87, #88, #90)

- **ARCH-RISK-201 (bloquant)** — le nom du fichier d'entrée de la CU et de la BP dépend de la langue (`documents.ENTRY_NAMES`), et les clés de dossiers vont toutes ensemble (`project.py:201`) : le squelette sans langue doit les nommer → **Q-007 → résolu par T49** : la langue est connue à la création, les entrées prennent les noms d'aujourd'hui.
- **ARCH-RISK-202 (bloquant → sans objet depuis T49 ; reste le seul lecteur de langue)** — « pas de langue » est indétectable : `forms.apply` écrit `doc-lang = "de"` par défaut (`forms.py:355`). → `forms.apply(here, form, language=None)` ; un seul prédicat `templates.language_missing(here)` = aucun document créé **et** pas de `doc-lang` (un ancien projet sans `doc-lang` n'est jamais grisé, REQ-023) ; un seul lecteur de langue (`positions_store.project_language` déplacé dans `templates`). `set_language` refuse s'il y a déjà une langue ou un document. Langue proposée : `templates.defaults(settings)["report_language"]` (ARCH-012).
- **ARCH-RISK-203 (important)** — Q-003 : `project.record` construit, l'écriture est en ligne à `export_all.py:358`. → `export_all.write_project_info(here, info)` (validé, utilisé aussi par `run`) et `refresh_project_info(here)`, qui fusionne le `project.json` précédent avec le nom et les champs de page de titre seuls (moteur, révision et classeurs non recalculés). La page d'accueil prend l'heure de `data/project.json` pour « dernier export » → `project.last_export(here)` (heure de `calculations.json`, version de `ENGINE_STAMP`), pour la page d'accueil et l'onglet (ARCH-011). Les tampons restent honnêtes : `project.json` est une entrée, le document se voit donc changé.
- **ARCH-RISK-204 (important)** — `modes` décrit le plan, pas l'existence ; ~15 endroits supposent le fichier d'entrée présent (CLI `requested_documents`, file d'export PDF, « Exporter les trois », `open_vscode`, `sharing`, `sync`, `variables_tab`, `migrate_dialog`, `archive_export`). → `Project.created_modes` / `is_created(mode)` (ARCH-010) ; `modes` inchangé pour `seed`.
- **ARCH-RISK-205** — mode d'ouverture : le premier document **créé** dans l'ordre CU, BP, RS, sinon RS ; `setCurrentIndex(Projet)` après `apply_mode` dans `on_mode_changed`.
- **ARCH-RISK-206** — `create_document` : `siblings` = documents créés, `settle_sharing` s'il y en a au moins deux, entrée au nom du projet, `content_templates` écrit après les fichiers ; le squelette fait toujours `_drop_report`. `create()` = squelette + langue + trois documents : mêmes fichiers qu'avant (`test_new_project.py`, 41 usages, filet de non-régression). La page de titre est préremplie par l'appelant de la fenêtre (`templates.people_for`), pas par `create`.
- **ARCH-RISK-207 (important)** — griser une fois (document du mode non créé ; plus de langue manquante depuis T49) : `MainWindow.available(key)`, `SideNav` (ensemble indisponible, couleur `muted`, exclu de `order()` donc de Ctrl+n), et un renvoi vers Projet dans `on_tab_changed` pour les autres portes (`open_object`, palette) ; `rebuild()` après la création d'un document ; aucun onglet ne charge un document non créé (`StructureTab.on_mode`).
- **ARCH-RISK-208** — aperçu : construit hors du fil sans `project.using` (variable globale), dans un dossier unique par construction effacé ensuite (`remove_tree`, extrait pur de `_undo`) ; squelette mis en cache par (langue, forme) si la mesure le demande ;  CON-004 prouvée par un instantané du vrai projet, un autre projet étant courant.
- **ARCH-RISK-209** — retrait de `content_switch` : les deux modules, `structure_tab_share.py:139-177` et son bouton, `structure_tab.py:9`, leurs mots, `tests/test_content_switch*.py`, la moitié `content_switch` de `test_broad_excepts.py`, le catalogue, `documents.md`, `open-questions.md`, `decisions.md`, les docstrings de `doc_templates.py`, et les aides devenues inutiles.
- **ARCH-RISK-210 (mineurs)** — la garde des doublons est `tests/test_no_duplicates.py` (pas `test_duplicates.py`) ; noms uniques dans `WRITERS` (`write_language`, `write_create_document`, `write_apply_form`, `write_project_titles`) ; `woodcore_gui.py:969-975` importe `domains.unfold_migrate`, retiré (trace à chaque ouverture) : enlevé au passage ; `_make` (`home_page.py:615`) supprimé avec la branche « new » du dialogue ; `content_templates` additive, schéma sans `additionalProperties`.

### 13.3 Zoom, vues, aperçus Typst, volet replié (#85, #86, #89, #91)

- **ARCH-RISK-301 (important)** — la remise à `VIEWS[0]` sans `view_changed` saute `layout_store.Binding.restore()` : l'aide de remise appelle aussi `layout_bindings[key].restore()`.
- **ARCH-RISK-302 (important)** — `apply_views` est appelé à chaque `build` : `rebuild`/`refresh_tab` portent `{key: tab.view}` et `apply_views(carried)` applique `carried.get(key) or views.default(tab)` ; tout onglet non affiché est déjà en `VIEWS[0]`. Pas de nouvelle mémoire, et pas le nom `views` (module et clé de réglage). `apply_mode` n'a rien à remettre : `setCurrentIndex` passe par `on_tab_changed`.
- **ARCH-RISK-303** — `picking` remis à faux avant `setCurrentIndex(back)` et sur toute sortie de `begin_variable_pick`.
- **ARCH-RISK-304 (important)** — un `rebuild()` coûte ~5 s : `app.setFont(base*zoom)` tout de suite (peu coûteux), feuille de style **non** réappliquée (le 13 pt de `#brand` sort de la QSS vers la police du libellé), reconstruction regroupée par un seul `QTimer` (~300 ms, relancé à chaque pas) pour les onglets qui ont copié `bold_font`/`title_font`/`mono_font`. `theme.apply` multiplie `base_size` par le zoom (le passage clair/sombre le garde).
- **ARCH-RISK-305 (important)** — Ctrl+molette : branche ajoutée au filtre d'application unique `nowheel.WheelGuard`, avant sa garde, en remontant les parents (le `viewport()` d'une zone défilante) ; laissent passer `OWN_ZOOM = (QGraphicsView, QPlainTextEdit, QTextEdit, QPdfView)` et toute classe portant `ZOOMS_ITSELF = True` (`CanvasBase`, `PageAreaInputMixin`, `_Page`, `ZoomablePdfView`) ; `angleDelta` cumulé par 120.
- **ARCH-RISK-306** — raccourcis explicites `Ctrl++` et `Ctrl+=` (le pavé suit), `Ctrl+-`, `Ctrl+0`, déclarés une fois (aide partagée par le menu et la page d'accueil) ; vérification manuelle sur clavier suisse.
- **ARCH-RISK-307 (important)** — `ZoomablePdfView` reprend la mise en place de `PdfPane` (`FitToWidth`, `ScrollBarAlwaysOn`) : `BundlePages` n'avait pas `ScrollBarAlwaysOn`, probable volet « qui ne suit pas » ; facteur borné, `ZOOM_STEP = 1.1` ; bouton « Ajuster à la largeur » en surimpression dans la vue (mots dans `pdf_pane.STRINGS`) ; retour à la largeur dans l'aide de remise de l'onglet quitté (pas `hideEvent`, qu'un changement de vue déclenche).
- **ARCH-RISK-308** — `theme.scaled(px)` appelé à l'usage, les constantes de `chrome.py` inchangées ; la largeur gardée par `layout_store` reste en pixels non agrandis. Le badge 36 px est celui des cartes de la page d'accueil, pas du cadre.
- **ARCH-RISK-309** — le texte « Zoom 120 % » vit avec `self.status` (construit une fois), mots fusionnés par `woodcore_gui_words.py`.
- **#91** — dans `FoldablePane.set_folded` : au repli, la place libérée va au volet central (`[flèche, centre + libéré, *reste]`) ; au dépli, la largeur gardée est reprise au centre (pas l'ancienne liste entière, périmée si la fenêtre a changé de taille), bornée à zéro.
- Décision v0.117 sur les vues : `docs/decisions.md:527` (pas 511).

### 13.4 Exigences ajoutées par la revue

- **ARCH-010** — `Project.created_modes` / `is_created(mode)` ; tout ce qui compile, exporte, partage ou ouvre un document les utilise. Source : revue (ARCH-RISK-204). Critère : `woodcore-cli export` sur un projet au RS seul réussit ; fenêtre construite sur un squelette nu.
- **ARCH-011** — `export_all.write_project_info` / `refresh_project_info` et `project.last_export(here)`. Source : revue (ARCH-RISK-203). Critère : `test_export_all.py` (moteur, révision, classeurs gardés) ; date de dernier export inchangée après une modification du client.
- **ARCH-012** — un seul lecteur de la langue du projet (`positions_store.project_language` déplacé dans `templates`, `structure_nodes.document_language` et `forms._project_languages` l'appellent) ; pas de `language_missing` (T49). Source : revue (ARCH-RISK-202). Critère : `test_forms.py`, `test_structure_*` inchangés ; un ancien projet sans `doc-lang` s'ouvre comme aujourd'hui.
- **ARCH-013** — `PositionsTab` : `GRAPH_KIND = "position"`, `lists_object`, `open_object`. Source : revue (ARCH-RISK-108). Critère : `open_object("position:<id>")` vrai.
- **ARCH-014** — `dependency_graph.reachable(...)` extrait de `dependencies_tab.lines`, appelé par les deux. Source : revue (ARCH-RISK-109). Critère : `test_dependency_graph.py`, `test_dependency_tab.py`.
- **ARCH-015** — `member_check.utilisations(...)` : l'η de chaque vérification bois calculable, par `compute`, une seule vérité avec l'onglet. Source : revue (ARCH-RISK-101). Critère : `test_palette_index.py`.

## 14. Plan d'implémentation

L'ordre suit #84 (T11) : #91 d'abord parce qu'il est isolé, la palette en dernier parce qu'elle s'appuie sur l'onglet Projet, la disponibilité des onglets et les vues. Un commit par lot (Q-005), §16 mis à jour après chaque lot. Chaque lot lance les tests des fichiers qu'il touche ; la suite complète une fois à la fin.

1. **Lot 1 — #91 volet replié.** `calc/tools/chrome.py` (`FoldablePane.set_folded`). → REQ-025. Test : `tests/test_chrome.py` (largeur du centre juste après repli et dépli, sans redimensionnement).
2. **Lot 2 — #86 vue de travail.** `calc/tools/views.py` (`default`, fin de `remembered`/`with_view`, docstring), `calc/tools/woodcore_gui.py` (aide de remise sur l'onglet quitté avec `restore()` du layout, `apply_views(carried)` dans `build`/`rebuild`/`refresh_tab`, plus d'écriture du réglage dans `view_changed`, `picking`). → REQ-011, ARCH-003. Tests : `tests/test_views.py` réécrit fenêtre affichée ; `test_formula_tab.py`, `test_linkable_spin.py`.
3. **Lot 3 — #89 aperçus Typst.** `calc/tools/pdf_pane.py` (`ZoomablePdfView`, bouton, mots), `calc/tools/bundle_view.py` ; remise à la largeur dans l'aide du lot 2 ; raison du pas 1,25 écrite dans `sheet_editor_canvas.py`. → REQ-024, UI-006, ARCH-004. Tests : `tests/test_pdf_pane.py` (largeur, Ctrl+molette, bouton, recompilation, un cas par volet hôte).
4. **Lot 4 — #85 zoom.** `calc/tools/theme.py` (`zoom`, `set_zoom`, `scaled`, `ui_zoom`, `apply` × zoom, `#brand` hors QSS, minuterie de reconstruction), `calc/tools/woodcore_gui.py` (`take_fonts`, barre d'état), `calc/tools/woodcore_gui_menus.py` (menu « Affichage », *Apparence* déplacé), aide de raccourcis partagée, `calc/tools/home_page.py` (raccourcis), `calc/tools/chrome.py` (`theme.scaled` à l'usage), `calc/tools/nowheel.py` (branche Ctrl+molette, `OWN_ZOOM`, `ZOOMS_ITSELF`), les classes qui zooment elles-mêmes. → REQ-009, REQ-010, UI-002, UI-003, ARCH-002. Tests : `test_theme.py` (en processus propre), `test_chrome.py`, `test_wheel.py`, `test_i18n.py`.
5. **Lot 5 — domaine du projet, sans Qt (#87, #88, #90).** `calc/project.py` (`created_modes`, `is_created`, `content_template`, `set_content_template`, `last_export`, `details_of`), `schemas/woodcore-project.schema.json` (`content_templates`, version inchangée), `calc/templates.py` (lecteur de langue unique), `calc/project_template.py` (`create_skeleton` avec la langue, `create_document`, `create` recomposé, `remove_tree`), `calc/export_all.py` (`write_project_info`, `refresh_project_info`), `calc/cli.py` et les sites de ARCH-RISK-204 vers `created_modes`, `calc/template_preview.py`. → ARCH-005, ARCH-006, ARCH-007, ARCH-010, ARCH-011, ARCH-012, REQ-014 (domaine), REQ-020, REQ-023, CON-002, CON-003, CON-004. Tests : `test_new_project.py` (`create` identique ; squelette nu ; squelette + RS ; CU ajoutée ensuite), `test_project.py`, `test_forms.py`, `test_export_all.py`, `test_cli_documents.py`, `test_template_preview.py` (nouveau).
6. **Lot 6 — fenêtre : onglet Projet, disponibilité, nouveau projet (#87, #88, #90).** `calc/tools/tab_registry.py` (`tab_project` en premier), `calc/tools/project_tab.py` + `project_tab_templates.py` (vues « Informations » et « Templates », `STRINGS`), `calc/tools/project_details.py` (widget partagé), `calc/tools/views.py` (deux clés de vue), `calc/tools/chrome.py` (icône, ensemble indisponible, `order()`), `calc/tools/woodcore_gui.py` (`available`, renvoi dans `on_tab_changed`, `remembered_mode`, Projet au changement de document, `rebuild` après création d'un document, retrait de l'import `unfold_migrate`), `calc/tools/structure_tab*.py` (aucune compilation hors visibilité ni pour un document non créé), `calc/tools/woodcore_gui_menus.py` (*Propriétés* → onglet, `properties_written`, `apply_form` partagé), `calc/tools/woodcore_gui_export.py` (`created_modes`), `calc/tools/home_page.py` (dialogue nom + emplacement + langue, `_make` supprimé, `last_export`, libellé « nom — emplacement » unique), `woodcore_gui_words.py` (groupe « Données »). → REQ-012, REQ-013, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-019, REQ-021, UI-004, UI-005, ARCH-008, ARCH-009. Tests : `test_project_tab.py` (nouveau), `test_modes_window.py`, `test_structure_tab.py`, `test_chrome.py`, `test_project_dialog.py`, `test_home.py`, `test_i18n.py`, fenêtre construite sur un squelette nu en RS et en CU.
7. **Lot 7 — retrait de « Changer de template de fond… » (#90).** Voir ARCH-RISK-209. → REQ-022. Tests : la suite sans `test_content_switch*.py` ; `test_broad_excepts.py` gardé pour `sync` ; `test_no_duplicates.py`.
8. **Lot 8 — palette Ctrl+K (#83).** `calc/palette_index.py` (sans Qt : `Entry`, catégories et préfixes, `build`, `match`, `used_by`, `summary`, avertissements de quatre sources), `calc/domains/member_check.py` (`utilisations`), `calc/domains/dependency_graph.py` (`reachable`), `calc/tools/dependencies_tab.py` (l'appelle), `calc/tools/positions_tab.py` (contrat `GRAPH_KIND`), `calc/tools/command_palette.py` (fenêtre, `STRINGS`, lecture des `QAction`), `calc/tools/woodcore_gui.py` (Ctrl+K, champ de la barre du haut, `palette_actions`, vues, langue et nouvelle vérification selon Q-006). → REQ-001 à REQ-008, UI-001, ARCH-001, ARCH-013, ARCH-014, ARCH-015. Tests : `test_palette_index.py`, `test_command_palette.py` (nouveaux ; graphe obtenu par un export temporaire), `test_dependency_graph.py`, `test_dependency_tab.py`, `test_modes_window.py`, `test_i18n.py`.
9. **Lot 9 — documentation et version.** `docs/ui/command-palette.md` et `docs/ui/tab-project.md` (nouveaux, indexés dans `docs/README.md` et `window.md`), `docs/ui/window.md` (navigation, zoom, vues, page d'accueil, Nouveau projet, aperçus), `docs/ui/tab-structure.md`, `docs/domain/documents.md`, `docs/domain/dependencies.md`, `docs/architecture/layout.md` (clés du `.woodcore`), `docs/open-questions.md`, `docs/decisions.md` + `decisions-index.md` (zoom et menu « Affichage » ; vues v0.117 en partie remplacée ; `content_templates` sans version ; v0.114 remplacée ; nouveau projet minimal ; report de `project.json`), catalogue des tests, `CHANGELOG.md` et « Nouveautés » 0.122.0 fr/de/en (après le commit de l'autre session, CON-006). Puis vérification indépendante et `finish`.

Vérification manuelle ajoutée (ARCH-RISK-306) : Ctrl++ / Ctrl+= sur un clavier suisse, dans la fenêtre réelle.

## 15. Vérification

Vérification indépendante (`requirements-verifier`, Sonnet) le 22.10.2026 sur a103276..HEAD et l'arbre de travail : 18 fichiers de tests lancés, tous verts ; **aucun ❌**. Ses ⚠️ étaient des preuves manquantes, le code étant là ; la première reprise en a ajouté les tests nommés ci-dessous.

| Élément | Verdict | Preuve (fichier:ligne, test, sortie) |
|---|---|---|
| REQ-001 | ✅ | `test_command_palette` : Ctrl+K, le champ, la croix, Échap ; Tab et flèches sans effet |
| REQ-002 | ✅ | `test_a_category_is_chosen_by_a_click_or_its_character` ; `test_palette_index.test_a_prefix_chooses_the_category_…` |
| REQ-003 | ✅ | clic sans changer d'onglet ; double-clic qui ouvre et ferme ; Entrée par la touche (`test_enter_opens_the_first_entry_…`, reprise 1). Molette et survol : comportement de Qt, liste sans focus (`command_palette.py`) |
| REQ-004 | ✅ | `test_the_entries_are_read_at_their_sources_each_time`, `test_the_module_imports_no_qt_…`, `test_the_actions_are_the_window_s_menus_…` ; lecture dans `_Read` (fil séparé) |
| REQ-005 | ✅ | `match` et positions des lettres (`test_a_prefix_chooses_…`) ; regroupement par genre (`search`, GENRES) ; η coloré par `theme.colour("ok"/"danger")` |
| REQ-006 | ✅ | `test_used_by_is_the_graph_s_…` et, sur les fichiers du projet, `test_a_check_above_one_is_a_warning_and_used_by_reads_the_project_s_own_graph` (reprise 1) ; `typst_call` testé |
| REQ-007 | ✅ | `test_the_warnings_gather_their_four_sources_…` ; η 1,2 d'une vérification acier parmi les avertissements, ouvrant sa vérification (reprise 1) |
| REQ-008 | ✅ | `test_the_entries_opened_lately_come_first_…` ; Ctrl+, en regard de *Paramètres* (reprise 1) |
| REQ-009 | ✅ | `test_theme` (pas, bornes, Ctrl+0, `ui_zoom`, clair/sombre, page d'accueil) |
| REQ-010 | ✅ | `test_wheel` (formulaire → zoom ; `QGraphicsView`, `QPlainTextEdit`, `ZoomablePdfView` et `ZOOMS_ITSELF` → non) |
| REQ-011 | ✅ | `test_views` (3 tests réécrits, fenêtre affichée) |
| REQ-012 | ✅ | `test_project_tab` (ouverture, Ctrl+1, changement de document sans compilation de *Structure*) ; `test_structure_tab` |
| REQ-013 | ✅ | `test_each_card_reads_…`, `test_a_title_page_saved_…` |
| REQ-014 | ✅ | `test_a_title_page_saved_…` ; `test_project.test_the_title_page_is_reported_into_the_export_alone_…` |
| REQ-015 | ✅ | `edit_properties` ouvre l'onglet (`test_structure_tab`) ; lecture seule (`test_read_only_…`, et « Créer le document » refusé, reprise 1) |
| REQ-016 | ✅ | `test_template_preview` (5) ; `test_the_templates_view_previews_…` ; liste limitée à la langue par `doc_templates.list_templates(mode, language=…)` (`project_tab.py`) ; forme appliquée aux trois par `home_page.apply_form` (`test_project_dialog`) |
| REQ-017 | ✅ | lecture seule : boutons désactivés et écriture refusée (reprise 1) ; rapport seul : `create_document` refuse (`project_template.py`) et la ligne est cachée (`has_modes`) |
| REQ-018 | ✅ | `test_project_dialog` (3 champs ; squelette) ; `test_a_skeleton_has_its_language_…` |
| REQ-019 | ✅ | `doc-lang` écrit ; champ de langue désactivé |
| REQ-020 | ✅ | `test_a_document_not_made_greys_…` ; `300-Statical report/Statischer Rapport.typ` et CU « pas encore créé » (reprise 1) ; `test_each_document_made_later_…` |
| REQ-021 | ✅ | mode CU avec le RS seul : seul *Projet*, PDF désactivé, pas d'« Exporter les trois » (reprise 1) ; CLI (`test_the_command_line_exports_only_…`) |
| REQ-022 | ✅ | modules, mots et tests retirés ; décision v0.114 « superseded » |
| REQ-023 | ✅ | `test_an_existing_project_is_written_nothing_by_opening_and_by_the_tab` (reprise 1 : `.woodcore`, `data/project.json`, `config.typ` aux mêmes octets) ; `create` identique au squelette + documents |
| REQ-024 | ✅ | `test_pdf_pane` (largeur, ×1,1, `Custom`, bouton, recompilation, dossiers d'export, une seule vue) ; `test_views.test_a_page_zoomed_goes_back_…` |
| REQ-025 | ✅ | `test_left_pane_fold.test_the_centre_takes_the_freed_width_at_once` (échoue sur l'ancien code) |
| UI-001 à UI-006 | ✅ | palette de largeur fixe, panneau stable ; menu « Affichage » ; cadre à 150 % ; onglet et groupe « Données » en trois langues ; info-bulle des onglets grisés (reprise 1) ; bouton « Ajuster à la largeur » |
| ARCH-001 à ARCH-015 | ✅ | voir le rapport du vérificateur ; ARCH-008 révisée (T49) ; `test_dependency*` verts après `reachable` |
| CON-001 à CON-007 | ✅ | `test_i18n`, `schema_version` inchangée, projet existant inchangé, aperçu sans écriture, `project_copy`/`tmpdir`, éditions ciblées, `window.md` 90 Ko |

Restent hors des tests : la vérification manuelle de Ctrl++ / Ctrl+= sur un clavier suisse (ARCH-RISK-306), et les tailles fixes propres aux onglets qui ne suivent pas le zoom (§8, documenté).

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-22 | draft | spécification extraite des issues #83 à #91 et de leurs commentaires ; la session « Typst commands standardization » consultée : aucun fichier de code commun, `CHANGELOG.md` et « Nouveautés » édités après son commit (CON-006) |
| 2026-10-22 | specified | Q-001 à Q-004 tranchées (options A) ; REQ-004, REQ-014, ARCH-005 et §7 mis à jour |
| 2026-10-22 | reviewed | trois revues d'architecture (APPROUVER AVEC RÉSERVES) en §13 ; ARCH-010 à ARCH-015 ajoutées ; plan en neuf lots en §14 ; Q-006 et Q-007 posées à l'approbation |
| 2026-10-22 | approved | approuvée par l'ingénieur ; Q-005 → A, Q-006 → A ; Q-007 remplacée par T49 (langue choisie à la création, grisée ensuite dans l'onglet Projet) : REQ-018, REQ-019, UI-005, ARCH-005, ARCH-012, §7, §13, §14 mis à jour ; lot 1 à suivre |
| 2026-10-22 | implementation | lot 1 (#91) fait et commité : REQ-025 (`FoldablePane._share`, `test_left_pane_fold.test_the_centre_takes_the_freed_width_at_once`, qui échoue sur l'ancien code) |
| 2026-10-22 | implementation | lot 2 (#86) fait : REQ-011, ARCH-003 — `views.default`, `MainWindow.reset_view` (onglet quitté, `restore()` du layout), `kept_views` à travers `rebuild`, vue gardée par `refresh_tab`, `picking`, plus d'écriture du réglage `views` ; `test_views` réécrit (fenêtre affichée), `test_autosave`, `test_linkable_spin`, `test_formula_tab`, `test_plan_panes_v0116`, `test_layout` verts |
| 2026-10-22 | implementation | lot 3 (#89) fait : REQ-024, UI-006, ARCH-004 — `pdf_pane.ZoomablePdfView` (largeur, Ctrl+molette ×1,1 sous le pointeur, bornes, bouton « Ajuster à la largeur » fr/de/en, zoom gardé à la recompilation) utilisée par `PdfPane` et `BundlePages` (qui gagne la barre toujours visible), remise à la largeur dans `reset_view` ; raison du pas 1,25 de `SheetCanvas` écrite ; `test_pdf_pane` (+4), `test_views` (+1), `test_i18n`, `test_structure_tab`, `test_display*`, `test_plan_command*`, `test_wheel`, `test_sheet_editor` verts |
| 2026-10-22 | implementation | lot 4 (#85) fait : REQ-009, REQ-010, UI-002, UI-003, ARCH-002 — `theme.zoom/set_zoom/scaled/brand_font/clamp_zoom`, réglage `ui_zoom`, police de l''application tout de suite et fenêtres reconstruites une fois 300 ms après (`rezoom`), `apply` garde le zoom, `#brand` hors QSS ; menu « Affichage » (zoom + Apparence déplacée), `chrome.zoom_actions`/`ZOOM_KEYS` partagés avec la page d''accueil, « Zoom 120 % » en barre d''état, `MainWindow.take_fonts` ; navigation, lignes, poignée, bouton de mode à `theme.scaled`, largeur gardée à 100 % ; Ctrl+molette dans `nowheel.WheelGuard` (`OWN_ZOOM`, `ZOOMS_ITSELF`) ; tests `test_theme` (+4), `test_wheel` (+2), `test_chrome` (+1), `test_i18n`, `test_home`, `test_legal`, `test_settings_dialog`, `test_layout_store`, `test_action_tabs`, `test_document_view`, `test_sheet_editor` et les gardes verts. Reste la vérification manuelle Ctrl++ sur clavier suisse |
| 2026-10-22 | implementation | lots 5 à 7 faits et commités (8ad487a) : ARCH-005 à ARCH-012, REQ-012 à REQ-023, UI-004, UI-005 — `create_skeleton`/`create_document`/`remove_tree`, `created_modes`, `content_templates`, `last_export`, `refresh_project_info`, `template_preview.py`, `project_tab.py`, onglets grisés et renvoi vers Projet, dialogue « Nouveau projet » réduit (nom, emplacement, langue — T49), *Structure* cachée ne compilant plus au changement de document, `content_switch` retiré ; `conftest.project_copy` copie les fichiers d'entrée ; ARCH-008 : pas de widget partagé `project_details.py` — le dialogue ne montre plus la page de titre (T49), l'onglet est seul à la montrer |
| 2026-10-22 | implementation | lot 8 fait et commité (7ef6be7) : REQ-001 à REQ-008, UI-001, ARCH-001, ARCH-013 à ARCH-015 — `palette_index.py`, `command_palette.py` (+ `PaletteWindowMixin`), `member_check.utilisations`, `dependency_graph.reachable`, contrat `GRAPH_KIND` de *Positions* ; `test_palette_index` (7), `test_command_palette` (7) |
| 2026-10-22 | testing | lot 9 : docs (tab-project.md, command-palette.md, window.md, tab-structure.md, documents.md, dependencies.md, layout.md, open-questions.md, README, decisions + index, catalogues), CHANGELOG, « Nouveautés » 0.122.0 fr/de/en, VERSION 0.122.0 ; tests liés : 2708 réussis, 9 échecs corrigés depuis (test_variables, test_i18n, test_startup_imports, test_window ×4, test_left_pane_fold ×2) |
| 2026-10-22 | verification | vérification indépendante lancée (requirements-verifier) |
| 2026-10-22 | verification | rapport du vérificateur : 18 fichiers verts, aucun ❌, des ⚠️ de preuve ; reprise 1 : 5 tests ajoutés (palette, onglet Projet, projet existant inchangé, mode sans document, lecture seule), ARCH-008 révisée |
| 2026-10-22 | completed | spec déplacée dans completed/ |
