---
id: 2026-10-24-onglet-materiaux
titre: Onglet Matériaux — la bibliothèque des matériaux de l'utilisateur pour tous les projets
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-24
source: issue GitHub #110 (texte de l'issue, validé par l'ingénieur le 24.10.2026) ; prototype docs/requirements/prototypes/2026-10-23-onglet-materiaux/
docs: [docs/architecture/principles.md, docs/ui/building-a-tab.md, docs/ui/window.md, docs/domain/loads.md, docs/decisions.md, docs/open-questions.md, docs/architecture/reference-library.md]
---

# Onglet Matériaux — Spécification

## 1. Objectif

Donner à Woodcore une bibliothèque de matériaux qui appartient à l'utilisateur et à son ordinateur et sert à tous ses projets, et un onglet « Matériaux », en bas de la navigation, pour la parcourir et y créer des matériaux (barre, panneau, autre) avec leurs valeurs caractéristiques et de dimensionnement, leur poids et leur source (site ou PDF copié). Les matériaux livrés (SIA 265, SIA 265/1, SIA 261, la bibliothèque livrée) y sont lisibles en lecture seule ; un projet qui utilise un matériau personnel en garde une copie et Woodcore avertit quand l'original a changé. L'onglet Poids propre ne crée plus de matériau.

## 2. Source

L'issue #110, mot pour mot, découpée en points. Le prototype (`index.html`, v2 validée) est la référence ; l'issue l'emporte là où les deux diffèrent (T0).

> **T0** — « Le prototype sert de référence, mais **cette issue l'emporte là où les deux diffèrent**. »
>
> **T1** — « un onglet nouveau, tout en bas, « Matériaux » »
>
> **T2** — « on y crée un matériau : son nom, ses valeurs de résistance, barre ou panneau, pour un panneau ses valeurs par direction (flexion dans le sens des fibres, perpendiculaire aux fibres…), une épaisseur facultative, la charge volumique ou surfacique, un commentaire, une source »
>
> **T3** — « la source est un site internet ou un PDF ; le PDF se choisit dans une fenêtre de fichiers et est **copié** dans un dossier de la bibliothèque »
>
> **T4** — « le matériau est proposé dans **tous les onglets** où l'on choisit un matériau »
>
> **T5** — « la bibliothèque est **par utilisateur et par ordinateur, pour tous les projets** »
>
> **T6** — « l'onglet des charges permanentes **ne crée plus** de matériau. »
>
> **T7** — Réponse 1 : « **A** : la liste à gauche, la fiche au centre, la source dans le volet de droite. Les dispositions B (tableur) et C (source à côté) sont écartées. »
>
> **T8** — Réponse 2 : « **Matériaux** (de *Materialien*, en *Materials*). Le dossier s'appelle **`materials`**, pas `library`. »
>
> **T9** — Réponse 3 : « **Barre, panneau, autre.** « Autre » ne porte rien : isolants, lés, couvertures ; seulement un poids. »
>
> **T10** — Réponse 4 : « **On peut saisir les deux** : valeurs caractéristiques et valeurs de dimensionnement. « Valeurs de calcul » se dit **« valeurs de dimensionnement »**. Si seules les valeurs caractéristiques sont données, les valeurs de dimensionnement **en sont déduites**. »
>
> **T11** — Réponse 5 : « **Dans le dossier de l'utilisateur** : `%APPDATA%\Woodcore\materials\`, les PDF dans `%APPDATA%\Woodcore\materials\sources\`. Elle survit aux mises à jour. »
>
> **T12** — Réponse 6 : « le projet en garde une copie (nom, valeurs, source), et Woodcore avertit si la bibliothèque a changé depuis. »
>
> **T13** — Réponse 7 : « elle devient cette copie ; on n'y écrit plus directement. »
>
> **T14** — Réponse 8 : « pas maintenant (pas d'annexe). »
>
> **T15** — « **Le dernier onglet de la navigation**, dans un groupe « Autres » (*Weitere*, *Others*). Ce groupe n'existe pas aujourd'hui dans `calc/tools/tab_registry.py` : la spec le crée, ou propose un autre emplacement en bas. »
>
> **T16** — « **C'est le premier onglet qui ne dépend pas du projet ouvert** : il ne lit ni n'écrit le dossier du projet. La spec dit comment le registre le déclare (`documents=`, `mode_bound`, la garde de lecture seule `tab_guard.py`) et s'il reste disponible sans projet ouvert. »
>
> **T17** — « **Les matériaux par catégorie**, repliables, chacune avec son nombre : bois, panneaux, isolation, couverture, étanchéité et lés, plâtres et enduits, béton et maçonnerie, acier, métaux et verre, revêtements de sol, granulats et lestage, charges saisies (11 catégories, les mêmes que dans l'onglet des charges permanentes). »
>
> **T18** — « **La recherche** trouve par nom, par catégorie (« isolation », « étanchéité », « béton », « acier ») et par type (« panneau »), en fr, de et en. Chaque mot tapé doit se trouver (ET). »
>
> **T19** — « **Les filtres** : la source (Toutes, Woodcore, Personnel) et le type (Barre, Panneau, Autre). »
>
> **T20** — « **Chaque ligne** : l'icône du type, le nom, et l'étiquette de la source à droite (« SIA 265 », « SIA 265/1 », « SIA 261 », « Externe », « Personnel »). »
>
> **T21** — « **Sous la liste** : « + Nouveau », « Dupliquer », et « Supprimer » pour un matériau personnel. »
>
> **T22** — « **Ce que Woodcore livre, en lecture seule** : les classes de résistance de la SIA 265:2021, tableaux 8 et 9 (C16 à D30, GL20h à GL32h), lues dans `calc/norms/` ; les panneaux de la SIA 265/1:2018 ; les poids de la SIA 261:2020, tableaux 28, 29 et 30 ; le reste de la bibliothèque livrée (« Externe »), fusionnée par nom et par poids comme dans le prototype des charges permanentes. »
>
> **T23** — « **La bibliothèque de l'utilisateur** (« Personnel »), modifiable. »
>
> **T24** — « **« Dupliquer dans ma bibliothèque »**, sur un matériau livré, en fait une copie personnelle modifiable. Le commentaire note d'où elle vient (« ← SIA 265 »). »
>
> **T25** — « Un matériau livré montre un bandeau « Livré avec Woodcore : en lecture seule. Pour le modifier, dupliquez-le dans votre bibliothèque. » »
>
> **T26** — La fiche en accordéons : « 1. **En-tête** : le nom, modifiable pour un matériau personnel, et l'**étiquette de la source**, cliquable. 2. **Identité** : le type (Barre · Panneau · Autre), la catégorie, et « + noms en allemand et en anglais » (un nom par langue ; la fenêtre montre celui de sa langue). 3. **Poids** : volumique (kN/m³) ou surfacique (kN/m²), avec sa conversion en kg (g = 10 m/s², `materials.KG_TO_KN`) et sa référence. 4. **Résistances**, selon le type. Le résumé de l'accordéon dit « ✓ » ou le nombre de valeurs manquantes. 5. **Commentaire.** 6. **Source** : « Site internet » (une URL) ou « Fichier PDF » (« Importer un PDF… »). Pour un matériau livré : la norme et sa page. 7. **« Annuler » / « Enregistrer »** pour un matériau personnel. »
>
> **T27** — « « + Nouveau » ouvre un choix en trois cartes avant toute saisie : **barre** : bois massif, lamellé-collé, LVL ; résistances de la SIA 265 ; **panneau** : OSB, contreplaqué, trois plis ; résistances de la SIA 265/1, par direction ; **autre** : rien de porteur ; seulement un poids. Le nouveau matériau est sélectionné, son nom prêt à être tapé. »
>
> **T28** — Une barre : « **La famille** : bois massif résineux, bois massif feuillus, bois lamellé-collé. Elle donne γ<sub>M</sub>/η<sub>M</sub> (SIA 265, tableau 1 : 1,7 et 1,5, déjà dans `calc/norms/sia265-2021-tab01-gamma-m.json`, `sia265.gamma_m`). **Six résistances**, chacune avec sa valeur caractéristique et sa valeur de dimensionnement côte à côte : f<sub>m</sub>, f<sub>t,0</sub>, f<sub>c,0</sub>, f<sub>t,90</sub>, f<sub>c,90</sub>, f<sub>v</sub>. En N/mm². **Rigidité et densité** : E<sub>0,mean</sub>, E<sub>90,mean</sub>, G<sub>mean</sub> (N/mm²), ρ<sub>k</sub> (kg/m³). Elles ne sont jamais déduites. »
>
> **T29** — Un panneau : « **Le dérivé du bois**, qui donne γ<sub>M</sub> (SIA 265/1, tableau 6) et η<sub>mod</sub> (tableau 9, classe d'humidité 1, durée moyenne). [tableau du prototype, 12 dérivés] ⚠️ **Ces valeurs sont à relire sur l'édition de la SIA 265/1** et à écrire dans `calc/norms/`, une table par fichier, comme le veut `CLAUDE.md` (jamais de mémoire). »
>
> **T30** — « **L'épaisseur**, facultative. Vide, les valeurs valent pour toute épaisseur, et l'état le dit en information. Un produit de la norme a ses plages, par exemple 6–10, 10–18 et 18–25 mm pour l'OSB/3 : une colonne par plage. **ρ<sub>k</sub>** (kg/m³). »
>
> **T31** — « **La grille de la norme** (tableau 19a de la SIA 265/1), chaque valeur ∥ et ⊥ au fil des couches extérieures, une colonne par épaisseur ou par plage : en plaque : f<sub>m</sub>, f<sub>c,90</sub>, f<sub>v</sub>, E<sub>m,mean</sub>, G<sub>mean</sub> ; en voile : f<sub>m</sub>, f<sub>v</sub>, E<sub>m,mean</sub>, G<sub>mean</sub> ; en traction et compression : f<sub>t</sub>, f<sub>c</sub>, E<sub>t/c,mean</sub>. **Un bouton « caractéristiques | de dimensionnement »** passe de l'une à l'autre grille. **Une case vide est colorée** et comptée dans l'état. »
>
> **T32** — « **Une valeur de dimensionnement saisie l'emporte toujours.** **Une valeur laissée vide est déduite**, si sa valeur caractéristique est là. Elle s'écrit **en italique** dans sa case, et le survol donne sa règle et ses nombres. »
>
> **T33** — « **Barre, en général** : f<sub>d</sub> = f<sub>k</sub> / (γ<sub>M</sub>/η<sub>M</sub>), SIA 265, équation (3) et tableau 1, avec η<sub>t</sub> = η<sub>w</sub> = 1. Arrondie à 0,1 N/mm², comme les tableaux 8 et 9 l'impriment. Contrôles : C24, 24 / 1,7 = 14,1 (tableau 8) ; f<sub>c,0,k</sub> 21 / 1,7 = 12,4 (tableau 8) ; GL24h, 24 / 1,5 = 16,0 (tableau 9). »
>
> **T34** — « **Barre, cisaillement et traction ⊥** : ces valeurs ne se déduisent pas. Elles sont celles que la norme fixe : SIA 265 3.3.2.2, bois massif : f<sub>v,d</sub> = 1,5 (résineux), 1,8 (feuillus) ; f<sub>t,90,d</sub> = 0,1 (résineux), 0,2 (feuillus) ; SIA 265 3.4.2.4, lamellé-collé : f<sub>v,d</sub> = 1,8 ; f<sub>t,90,d</sub> = 0,15. »
>
> **T35** — « **Panneau** : f<sub>d</sub> = η<sub>mod</sub> · f<sub>k</sub> / γ<sub>M</sub>, SIA 265/1, tableaux 6 et 9, classe d'humidité 1, durée moyenne. Contrôle : OSB/3, 0,70 · 18 / 1,2 = 10,5 (tableau 19b) ; f<sub>c,90</sub> 5,83 → 5,8 ; f<sub>v</sub> 0,58 → 0,6. »
>
> **T36** — « **Une limite, montrée par le prototype** : […] f<sub>c,90,k</sub> = 2,5 N/mm² (SN EN 338) donne 2,5 / 1,7 = 1,5, quand le tableau 8 porte 1,8 pour le C24. C'est pourtant ce que demande 3.3.2.2 (« selon le chiffre 2.2.2 »). Woodcore applique la norme et le dit au survol. »
>
> **T37** — « **η<sub>w</sub> et η<sub>t</sub>** ne sont pas dans la bibliothèque : la vérification qui lit le matériau les applique, comme elle le fait pour les tableaux 8 et 9. »
>
> **T38** — « **L'étiquette de la source** (à côté du nom, dans la fiche et dans chaque ligne de la liste) est cliquable. Un clic sélectionne le matériau si besoin et **met en évidence le module « La source »** du volet droit : il clignote, et le volet défile jusqu'à lui. »
>
> **T39** — « **Le module « La source »** montre : pour une norme, l'extrait de la page (les tableaux 8 et 9 de la SIA 265, 19a et 19b de la SIA 265/1) ; pour un PDF importé, le PDF ; pour un site, le lien, avec « ouvrir dans le navigateur » ; pour un matériau personnel sans source, une zone « Déposez un PDF ici, ou importez-le ». »
>
> **T40** — « **Son bouton ⤢ ouvre la source en grand**, par-dessus la fenêtre. Échap ou × la referme. »
>
> **T41** — « **Un PDF** se choisit dans la fenêtre de fichiers du système. Woodcore le **copie** dans `materials\sources\`, sous un nom nettoyé, et la source pointe sur la copie, jamais sur le fichier d'origine. »
>
> **T42** — Le volet droit, 1. État : « **vert** « Complet. » ; **orange** : exemple non vérifié ; pas de poids (le matériau manque alors au choix de l'onglet Poids propre) ; n valeurs de résistance manquantes (il n'est pas proposé là où elles servent) ; pas de source (matériau personnel) ; **rouge** : un autre matériau porte ce nom ; **information** : sans épaisseur (les valeurs valent pour toutes les épaisseurs) ; n valeurs de dimensionnement déduites. **Règle de comptage** : une résistance manque quand ni sa valeur caractéristique ni sa valeur de dimensionnement (saisie, fixée ou déduite) n'est là ; une rigidité et ρ<sub>k</sub> manquent quand elles sont vides. »
>
> **T43** — « 2. **La source** (ci-dessus). »
>
> **T44** — « 3. **Disponible dans** — une proposition, à confirmer dans la spec : Poids propre et surcharge : il faut un poids ; Vérifications d'éléments : une barre complète ; Assemblages : il faut ρ<sub>k</sub> ; Plaques et voiles : à venir. Ce qui manque est dit à côté. »
>
> **T45** — « 4. **Où il est enregistré** : le fichier : `%APPDATA%\Woodcore\materials\materials.json` pour un matériau personnel, le fichier de `calc/norms/` ou de `calc/libraries/` pour un matériau livré ; le PDF copié ; pour un matériau personnel, « et une copie dans chaque projet qui l'utilise : `<projet>/materials.json` ». »
>
> **T46** — « L'OSB/3 a deux nombres, et la fiche les montre séparément, chacun avec son rôle et sa source : ρ<sub>k</sub> = 550 kg/m³ (SIA 265/1), pour les résistances et les assemblages ; 680 kg/m³ (Kronospan, dans la bibliothèque livrée), pour les charges. La SIA 261 ne le donne pas. »
>
> **T47** — « **Un projet qui utilise un matériau personnel en garde une copie** : son nom, ses valeurs et sa source. Il se calcule donc à l'identique sur un autre ordinateur. »
>
> **T48** — « **Woodcore avertit si la bibliothèque a changé depuis** : le matériau du même identifiant n'a plus les mêmes valeurs. L'avertissement dit lesquelles. La spec dit ce qu'il propose (reprendre la nouvelle version, garder la copie). »
>
> **T49** — « **`Woodcore-Datei/materials.json` devient cette copie.** On n'y écrit plus directement : le service `project_materials.py` et sa carte « Ajouter un matériau » / « Enregistrer les matériaux » disparaissent de l'onglet Poids propre. »
>
> **T50** — « **Migration** : un projet dont `materials.json` (schéma 1.0) a des matériaux écrits à la main. La spec dit s'ils passent dans la bibliothèque de l'utilisateur à l'ouverture, avec un message, ou restent la copie telle quelle. »
>
> **T51** — Le dossier de l'utilisateur : « Une fonction `materials_dir()` à côté de `templates_dir()` : `%APPDATA%\Woodcore\materials\`, sa variable d'environnement pour les tests (comme `WOODCORE_TEMPLATES`), et le dossier à côté des réglages quand seul `WOODCORE_SETTINGS` est posé. Ainsi, un test n'écrit jamais dans la bibliothèque de l'ingénieur. »
>
> **T52** — La bibliothèque de l'utilisateur : « Un schéma nouveau dans `schemas/` (`schema_version`), validé avant chaque écriture, et un identifiant stable par matériau. »
>
> **T53** — La copie dans le projet : « Une version 2.0 : le type, les résistances, la source, l'identifiant et de quoi savoir si l'original a changé. La lecture de la 1.0. »
>
> **T54** — Le domaine : « `calc/domains/materials.py` (sans Qt) : Les types, les catégories, les noms en trois langues ; la déduction des valeurs de dimensionnement ; l'état ; la recherche par nom et par catégorie, partagée avec l'onglet Poids propre ; la copie d'un PDF. Aujourd'hui `LIBRARIES = ("sia261", "belastungsannahmen", "project")` : ce choix de bibliothèque disparaît pour l'utilisateur, qui ne voit qu'une liste. »
>
> **T55** — La SIA 265/1 : « Un fichier par tableau, lus sur l'édition 2018 : le tableau 6 (γ<sub>M</sub>), le tableau 9 (η<sub>mod</sub>), le tableau 19a/b (OSB/3, déjà relu pour le prototype, p. 42). Puis, au choix de la spec, les autres panneaux : contreplaqués (tableaux 11, 12), panneaux de particules (13 à 17), OSB/2 et OSB/4 (18, 20), panneaux de fibres (21 à 23). »
>
> **T56** — Les extraits des normes : « La page et le rectangle de chaque tableau montré comme source, par édition, comme pour les bulles de la neige et du vent. »
>
> **T57** — L'onglet : « `calc/tools/` (un module pour l'onglet, ses mots dans un `STRINGS` en de, fr, en) : Son type parmi ceux de `docs/ui/building-a-tab.md` (Éditeur ou Données, #105, #106 ; la spec choisit) ; son `TabSpec` dans `calc/tools/tab_registry.py`, son icône dans `chrome.ICONS`. »
>
> **T58** — Les autres onglets : « Poids propre et surcharge (#111) ; plus tard les vérifications d'éléments (`member_check_tab_form.py` lit `sia265.grades()`) et les assemblages (`connector.py` lit `sia265.rho_k(grade)`). Cette issue livre la bibliothèque et l'onglet Poids propre qui la lit. Qu'une vérification ou un assemblage lise une barre personnelle comme une classe de la norme est une suite, à décider dans la spec (portée). »
>
> **T59** — Partout : « Les mots en de, fr et en (`tests/test_i18n.py`), les tests du domaine et de l'onglet, une ligne au catalogue des tests. »
>
> **T60** — « La documentation : une page `docs/domain/` pour les matériaux et `docs/ui/tab-materials.md` ; `docs/ui/window.md` ; `docs/decisions.md`, où D-07 (« les matériaux d'une composition viennent de la SIA 261, de la bibliothèque Belastungsannahmen et du projet ») est remplacée ; `docs/open-questions.md` (la SIA 265/1) ; `CHANGELOG.md` ; « Nouveautés » en trois langues. »
>
> **T61** — Points à étudier : « **L'identifiant d'un matériau**, stable entre les versions de Woodcore et entre la bibliothèque et la copie d'un projet. » ; « **« La bibliothèque a changé »** : comment le constater (valeurs comparées, version par matériau, empreinte), et ce que Woodcore propose. »
>
> **T62** — « **Les extraits des normes** montrés comme source : leur découpe et leur place. La décision prise pour la neige (#94) s'applique : l'ingénieur autorise sans limite à découper la norme et à l'imprimer. »
>
> **T63** — « **#109 (D-33)** : le classeur de charges ne sera plus lu. La bibliothèque livrée `calc/libraries/materials-library.json` en est une lecture faite une fois, livrée avec Woodcore : elle reste une source de matériaux, sauf décision contraire de l'ingénieur, à confirmer. »

## 3. Exigences fonctionnelles

### REQ-001 — Le dossier de la bibliothèque de l'utilisateur
- **Exigence** : Woodcore doit placer la bibliothèque de l'utilisateur dans `usersettings.materials_dir()` : `%APPDATA%\Woodcore\materials\` (fichier `materials.json`, PDF dans `sources\`) ; `WOODCORE_MATERIALS` le désigne ailleurs ; quand seul `WOODCORE_SETTINGS` est posé (une suite de tests), un dossier à côté du fichier des réglages. Hors du dossier d'installation : il survit aux mises à jour.
- **Source** : T5, T8, T11, T51
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_materials_library.py` : les trois cas de `materials_dir()` ; la suite entière ne crée rien sous le vrai `%APPDATA%\Woodcore\materials\`.

### REQ-002 — Le fichier de la bibliothèque, son schéma, son écriture validée
- **Exigence** : Woodcore doit écrire la bibliothèque dans `materials.json` selon un schéma nouveau `schemas/user-materials.schema.json` (`schema_version` "1.0"), validé (structure et règles : identifiant unique, type connu, catégorie connue, poids > 0 s'il est donné, unités) avant chaque écriture ; un fichier malformé n'est jamais écrasé : il arrête la lecture en nommant le fichier et le champ, et l'onglet le dit.
- **Source** : T52 ; principes 8, 9, 10 ; CLAUDE.md « un fichier malformé arrête »
- **Priorité** : doit
- **Critère d'acceptation** : test : une écriture d'un matériau invalide est refusée et le fichier sur disque n'a pas changé ; un fichier corrompu donne une `ValidationError` qui nomme `materials.json` et le champ.

### REQ-003 — L'identifiant stable d'un matériau
- **Exigence** : chaque matériau doit avoir un identifiant stable : personnel `u-<8 hex>` tiré au hasard à la création, jamais réutilisé ni changé par un renommage ; livré, dérivé de sa source (`sia265:C24`, `sia265-1:osb3`, `sia261:<id de ligne>`, `ext:<ligne du classeur>`), le même d'une version de Woodcore à l'autre. La copie d'un projet porte le même identifiant.
- **Source** : T52, T61
- **Priorité** : doit
- **Critère d'acceptation** : test : renommer un matériau personnel garde son id ; les ids livrés de la version courante sont figés dans un test (une liste témoin) qui échoue si l'un disparaît.

### REQ-004 — Les trois types et leurs données
- **Exigence** : un matériau doit être d'un type `member` (barre), `panel` (panneau) ou `other` (autre). Tous ont : noms fr/de/en (au moins un), catégorie (11, celles de T17), poids facultatif (valeur, unité kN/m³ ou kN/m², référence), commentaire, source. Une barre a sa famille (`softwood`, `hardwood`, `glulam`), six résistances (f_m, f_t,0, f_c,0, f_t,90, f_c,90, f_v) chacune en `_k` et `_d`, E_0,mean, E_90,mean, G_mean, ρ_k. Un panneau a son dérivé (12, T29), ρ_k, une épaisseur facultative ou des plages d'épaisseur, et la grille du tableau 19a (plaque, voile, traction/compression ; ∥ et ⊥ ; une colonne par plage) en `_k` et `_d`. « Autre » n'a qu'un poids.
- **Source** : T2, T9, T28, T29, T30, T31
- **Priorité** : doit
- **Critère d'acceptation** : test : un matériau de chaque type passe la validation ; une barre avec une clé de grille de panneau est refusée.

### REQ-005 — Les matériaux livrés, en lecture seule
- **Exigence** : Woodcore doit proposer, sans les copier, lus à leur source : les 11 classes de SIA 265:2021 tableaux 8 et 9 (`sia265.grades()`), tous les panneaux de SIA 265/1:2018 (tableaux 11 à 23, Q-001 réponse B), les lignes avec valeur de SIA 261:2020 tableaux 28, 29 et 30, et la bibliothèque livrée (`calc/libraries/materials-library.json`, « Externe ») fusionnée par nom et poids comme `data.py` du prototype (une entrée dont le nom et le poids égalent une autre n'est listée qu'une fois). Chacun avec type, catégorie, noms fr/de/en, source (norme et page, ou « Quellen » du classeur). Ils ne s'éditent pas.
- **Source** : T22, T25, T63
- **Priorité** : doit
- **Critère d'acceptation** : test : `catalogue()` contient C24 (f_m,d 14,1 lu dans le tableau 8), GL24h, l'OSB/3 et une ligne du tableau 30 ; aucun ne peut être enregistré par `save_user()` (refus nommé).

### REQ-006 — « Dupliquer » et « Dupliquer dans ma bibliothèque »
- **Exigence** : dupliquer un matériau (livré ou personnel) doit créer un matériau personnel nouveau (nouvel id) aux mêmes valeurs, dont le commentaire note la provenance (« ← SIA 265 », « ← <nom> ») ; pour un livré, sa source devient la référence de la norme (texte), son extrait restant montré.
- **Source** : T21, T24
- **Priorité** : doit
- **Critère d'acceptation** : test du domaine : `duplicate(C24)` → type `member`, valeurs égales, `src` personnel, commentaire commençant par « ← SIA 265 ».

### REQ-007 — Créer, enregistrer, supprimer un matériau personnel
- **Exigence** : « + Nouveau » doit demander le type (trois cartes) puis créer un matériau personnel de ce type, sélectionné, son nom en saisie ; « Enregistrer » l'écrit (REQ-002) ; « Annuler » revient à la version enregistrée ; « Supprimer » (personnel seulement, après confirmation) le retire du fichier et efface son PDF copié s'il n'est plus nommé par aucun autre matériau. Les copies des projets ne sont pas touchées.
- **Source** : T21, T26 (7), T27
- **Priorité** : doit
- **Critère d'acceptation** : test de l'onglet : nouveau → panneau → enregistrer → relu depuis le disque ; supprimer → absent du fichier, PDF effacé.

### REQ-008 — La déduction des valeurs de dimensionnement
- **Exigence** : `calc/domains/materials.py` doit donner, pour chaque valeur de dimensionnement, `(valeur, déduite?, règle, nombres)` : saisie → elle-même ; barre f_v,d et f_t,90,d → la valeur fixée par SIA 265 3.3.2.2 (bois massif résineux 1,5 / 0,1 ; feuillus 1,8 / 0,2) ou 3.4.2.4 (lamellé-collé 1,8 / 0,15), lue dans `calc/norms/` ; autre résistance de barre → f_k / (γ_M/η_M) (SIA 265 (3), tableau 1, `sia265.gamma_m`), arrondie à 0,1 ; panneau → η_mod · f_k / γ_M (SIA 265/1 tableaux 6 et 9, classe d'humidité 1, durée moyenne), arrondie à 0,1 ; sinon rien. η_t et η_w ne sont pas appliqués (T37). Chaque règle cite sa norme et sa clause.
- **Source** : T10, T32–T37
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_materials_domain.py` : C24 f_m,k 24 → 14,1 ; f_c,0,k 21 → 12,4 ; GL24h 24 → 16,0 ; OSB/3 18 → 10,5 ; 10 → 5,8 ; 1,0 → 0,6 ; f_c,90,k 2,5 en résineux → 1,5 (la limite, avec sa règle) ; f_v,d résineux → 1,5 « fixée » ; une valeur saisie l'emporte.

### REQ-009 — L'état d'un matériau
- **Exigence** : le domaine doit donner la liste des états d'un matériau selon T42 : vert « Complet. » quand aucun orange/rouge ; orange : exemple non vérifié (drapeau `example` du matériau, non plus un mot du nom), pas de poids, n résistances manquantes (règle de comptage de T42), pas de source (personnel) ; rouge : un autre matériau du catalogue porte le même nom dans la langue montrée ; info : panneau sans épaisseur ni plages, n valeurs déduites. Messages `contracts.Message` ou équivalent sans Qt, les mots dans les trois langues.
- **Source** : T42
- **Priorité** : doit
- **Critère d'acceptation** : test : la barre « c24k » du prototype donne orange « 3 valeurs manquent » (f_t,0, f_c,0, f_c,90) et info « 3 déduites » ; C24 livré : vert ; deux personnels du même nom : rouge.

### REQ-010 — « Disponible dans »
- **Exigence** : le domaine doit dire, pour un matériau, dans quels onglets il est proposé et ce qui lui manque ailleurs : Poids propre et surcharge (il faut un poids) ; pour une barre, Vérifications d'éléments (une barre complète) et Assemblages (il faut ρ_k) ; pour un panneau, Plaques et voiles (à venir) et Assemblages (ρ_k). La portée réelle de ce lot (Q-004, réponse A) y est dite telle quelle : les vérifications et les assemblages ne lisent pas encore une barre personnelle, qui y est marquée « à venir » ; une classe livrée de la SIA 265 y est « disponible ».
- **Source** : T4, T44, T58
- **Priorité** : doit
- **Critère d'acceptation** : test : une « autre » sans poids → Poids propre ✗ « il faut un poids » ; C24 livré → les trois ✓ ; une barre personnelle complète → Vérifications et Assemblages « à venir ».

### REQ-011 — La recherche et les filtres
- **Exigence** : une fonction du domaine, partagée avec l'onglet Poids propre, doit trouver un matériau quand chaque mot tapé (ET, sans casse, sans accents) se trouve dans ses noms fr/de/en, sa catégorie (nom en trois langues et synonymes : `SYN` du prototype) ou son type en trois langues ; filtres source (toutes / Woodcore / personnel) et type.
- **Source** : T18, T19, T54
- **Priorité** : doit
- **Critère d'acceptation** : test : « isolation » et « Dämmung » trouvent les mêmes matériaux ; « panneau osb » trouve l'OSB/3 ; « beton » (sans accent) trouve la catégorie béton ; filtre personnel + type panneau.

### REQ-012 — Le PDF d'une source copié
- **Exigence** : importer un PDF doit le copier dans `materials\sources\` sous un nom nettoyé (ASCII, sans espace ni caractère réservé, suffixé `-2`, `-3` s'il existe déjà avec un autre contenu ; réutilisé s'il a le même contenu) ; la source du matériau nomme la copie relative au dossier, jamais l'original. Un glisser-déposer d'un PDF sur la zone de la source fait de même.
- **Source** : T3, T39, T41
- **Priorité** : doit
- **Critère d'acceptation** : test : `import_pdf("Fiche technique (v2).pdf")` → `sources/fiche-technique-v2.pdf`, contenu égal ; un second fichier de même nom et autre contenu → `-2` ; l'original supprimé, la source se lit toujours.

### REQ-013 — La copie dans le projet (schéma `materials` 2.0)
- **Exigence** : quand un cas d'un projet (aujourd'hui une composition de Poids propre) nomme un matériau personnel, Woodcore doit en écrire une copie complète (id, noms, type, valeurs, poids, source — le PDF copié dans le projet sous `Woodcore-Datei/materials/` —) dans `Woodcore-Datei/materials.json`, schéma `materials` 2.0, à l'enregistrement du cas. Le calcul du projet lit la copie, jamais la bibliothèque de l'utilisateur : il se calcule à l'identique sur un autre ordinateur. Un matériau livré n'est pas copié (il est lu à sa source, dans la version de Woodcore). Une copie que plus aucun cas ne nomme est retirée à l'enregistrement.
- **Source** : T12, T13, T47, T49, T53
- **Priorité** : doit
- **Critère d'acceptation** : test : une composition qui nomme `u-…` enregistrée → `materials.json` 2.0 contient sa copie ; la bibliothèque de l'utilisateur effacée, l'export du projet calcule la même charge.

### REQ-014 — « La bibliothèque a changé »
- **Exigence** : Woodcore doit comparer, champ par champ, la copie du projet au matériau du même id dans la bibliothèque de l'utilisateur ; s'ils diffèrent, un avertissement (orange, dans l'état de l'onglet qui l'utilise) nomme le matériau et les champs changés (« f_m,k 24 → 26 ; poids 5,0 → 5,2 ») et propose « Reprendre la nouvelle version » (la copie remplacée, le cas recalculé) ou « Garder la copie » (l'avertissement se tait pour cette différence-là, mémorisée dans la copie). Un id absent de la bibliothèque (autre ordinateur) donne une information et propose « Ajouter à ma bibliothèque ».
- **Source** : T12, T48, T61
- **Priorité** : doit
- **Critère d'acceptation** : test du domaine : `diff(copie, original)` liste les champs ; « Garder » enregistre l'empreinte de l'original refusé et l'avertissement disparaît jusqu'au prochain changement.

### REQ-015 — Lecture et migration de `materials.json` 1.0
- **Exigence** : Woodcore doit lire un `materials.json` 1.0 (id, name, value, unit, source) comme des matériaux de type `other` (le poids converti en kN si en kg). À l'ouverture du projet (Q-003, réponse B), chaque entrée est **versée dans la bibliothèque de l'utilisateur** : réutilisée si un matériau personnel de même nom et même poids existe déjà, sinon ajoutée avec un id nouveau `u-…` ; le projet passe en 2.0 (sa copie porte les ids de la bibliothèque) et les couches qui nommaient l'ancien id sont réécrites, une fois, comme les autres migrations à l'ouverture ; un message dit combien de matériaux ont été versés. Un projet ouvert en lecture seule : la bibliothèque reçoit les matériaux, le projet n'est pas réécrit (il est lu en 1.0 comme avant).
- **Source** : T50, T53, Q-003
- **Priorité** : doit
- **Critère d'acceptation** : test : une copie de `tests/projet-exemple/` avec un 1.0 de deux matériaux → après l'ouverture, la bibliothèque (dossier de test) les contient, le projet est en 2.0, ses couches nomment les nouveaux ids, la composition se calcule à l'identique ; une seconde ouverture ne verse rien de plus.

### REQ-016 — L'onglet Poids propre lit la bibliothèque et ne crée plus de matériau
- **Exigence** : la carte « Bibliothèque du projet » (`project_materials.ProjectMaterials`, « Ajouter un matériau », « Enregistrer les matériaux ») doit disparaître de l'onglet Poids propre ; le choix du matériau d'une couche doit proposer une seule liste (livrés et personnels qui ont un poids), avec la recherche de REQ-011, au lieu du choix de bibliothèque `sia261 / belastungsannahmen / project` ; une couche existante qui nomme `library`+`material` continue de se calculer (lecture des anciennes clés). La refonte complète du tableau des couches reste à #111.
- **Source** : T4, T6, T49, T54, T58
- **Priorité** : doit (périmètre à confirmer, Q-002)
- **Critère d'acceptation** : test : `DeadLoadTab.SERVICES` ne contient plus `ProjectMaterials` ; une composition du projet d'exemple écrite avant se calcule à l'identique ; une couche peut nommer un matériau personnel.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — La place de l'onglet
- **Exigence** : l'onglet « Matériaux » (*Materialien*, *Materials*) est le dernier de la navigation, seul dans un groupe nouveau « Autres » (*Weitere*, *Others*), avec son icône ; montré dans les trois documents (`documents=ALL`), non lié à un document (`mode_bound=False`).
- **Source** : T1, T8, T15, T16
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_tab_registry.py` : dernier `TabSpec` = `tab_materials`, groupe `nav_others` ; titre et groupe dans les trois langues.

### UI-002 — Un onglet indépendant du projet
- **Exigence** : l'onglet ne lit ni n'écrit le dossier du projet ; il reste modifiable dans un projet ouvert en lecture seule (la bibliothèque est celle de l'utilisateur), ce que la garde (`tab_guard`) sait par une déclaration de l'onglet ; changer de document ne lui demande rien.
- **Source** : T16
- **Langues** : —
- **Critère d'acceptation** : test : dans un projet ouvert en lecture seule, l'enregistrement d'un matériau personnel réussit ; aucun fichier du projet n'est modifié par l'onglet.

### UI-003 — La liste (gauche)
- **Exigence** : la recherche, les filtres source et type (puces), le nombre de matériaux trouvés, les 11 catégories repliables avec leur nombre (ouvertes quand une recherche ou un filtre est actif, ou quand elles contiennent la sélection) ; chaque ligne : icône du type, nom dans la langue de la fenêtre, étiquette de la source cliquable (SIA 265, SIA 265/1, SIA 261, Externe, Personnel) ; sous la liste « + Nouveau », « Dupliquer », « Supprimer » (actif pour un personnel seulement).
- **Source** : T17–T21
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de l'onglet : taper « isolation » réduit la liste, ouvre la catégorie ; « Supprimer » désactivé sur C24.

### UI-004 — La fiche (centre), en accordéons
- **Exigence** : bandeau lecture seule + « Dupliquer dans ma bibliothèque » pour un livré ; en-tête (nom, étiquette cliquable) ; Identité (type en segments, catégorie, noms de/en/fr) ; Poids (volumique/surfacique, valeur, conversion en kg, référence) ; Résistances (selon le type ; résumé « ✓ » ou « n ✕ ») ; Commentaire ; Source (site ou PDF, « Importer un PDF… » ; pour un livré la norme et sa page) ; « Annuler » / « Enregistrer » pour un personnel. Pour l'OSB/3, ρ_k (SIA 265/1, résistances et assemblages) et le poids (680 kg/m³ Kronospan, charges) sont montrés séparément, chacun avec son rôle et sa source.
- **Source** : T24–T26, T46
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : une fiche de C24 a ses champs désactivés et le bandeau ; d'un personnel, éditables ; l'OSB/3 montre 550 kg/m³ et 6,8 kN/m³ dans deux rangées distinctes.

### UI-005 — Les résistances d'une barre
- **Exigence** : famille (3 choix, γ_M/η_M affiché) ; une grille de six lignes (nom, symbole, `_k`, `_d` côte à côte, N/mm²) ; rigidité et densité (E_0,mean, E_90,mean, G_mean, ρ_k) ; une valeur de dimensionnement déduite est en italique et son infobulle donne sa règle et ses nombres ; une case qui compte comme manquante est colorée.
- **Source** : T28, T32
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : une barre avec f_m,k 24 seul montre « 14.1 » en italique, l'infobulle contient « 24 / 1.7 » et « SIA 265 (3) ».

### UI-006 — Les résistances d'un panneau
- **Exigence** : dérivé du bois (12 choix, γ_M et η_mod affichés) ; épaisseur facultative ; ρ_k ; la grille du tableau 19a en trois blocs (plaque, voile, traction/compression), lignes ∥ et ⊥, une colonne par épaisseur ou par plage (« t [mm] » 6–10, 10–18, 18–25 pour l'OSB/3) ; un bouton « caractéristiques | de dimensionnement » bascule la grille ; italique et infobulle pour les déduites ; case vide colorée.
- **Source** : T29–T31
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : l'OSB/3 en « dimensionnement » montre 10.5 / 9.6 / 8.6 (f_m ∥ plaque) ; en « caractéristiques » 18.0 / 16.4 / 14.8.

### UI-007 — Le volet droit
- **Exigence** : dans cet ordre, des modules : État (pastilles vert/orange/rouge/info) ; La source (extrait de la norme, PDF, lien + « ouvrir dans le navigateur », ou zone de dépôt) avec ⤢ qui l'ouvre en grand par-dessus la fenêtre (Échap ou × ferme) ; Disponible dans (✓/✗ et ce qui manque) ; Où il est enregistré (le fichier, le PDF copié, « et une copie dans chaque projet qui l'utilise »). Un clic sur une étiquette de source sélectionne le matériau et fait défiler et clignoter le module « La source ».
- **Source** : T38–T45
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : un clic sur l'étiquette d'une ligne non sélectionnée la sélectionne et appelle le clignotement ; pour C24, le module montre l'extrait du tableau 8 découpé du PDF livré.

### UI-008 — Les extraits des normes
- **Exigence** : les extraits montrés comme source (SIA 265:2021 tableaux 8 et 9, SIA 265/1:2018 tableaux 11 à 23, chacun pour son panneau, SIA 261:2020 tableaux 28–30) sont découpés du PDF livré de `norm-library/` par leur page et leur rectangle, déclarés dans le fichier de la norme comme pour la neige et le vent (`calc/norms/excerpts.py`), jamais une image copiée à la main.
- **Source** : T39, T56, T62
- **Langues** : l'édition montrée est celle que le fichier nomme (FR pour 265/1, la seule livrée)
- **Critère d'acceptation** : test : chaque extrait déclaré se découpe sans erreur et son texte contient le numéro du tableau (tenu au PDF, comme pour le vent).

## 5. Exigences d'architecture

### ARCH-001 — Le domaine sans Qt
- **Exigence** : types, catégories, noms, catalogue des livrés, déduction, état, « Disponible dans », recherche, copie de PDF, lecture/écriture validée de la bibliothèque et de la copie du projet vivent dans `calc/domains/` (`materials.py` et, si sa taille le demande, un module voisin) sans Qt ; l'onglet ne fait que montrer et appeler.
- **Source** : T54 ; CLAUDE.md « Domain logic is independent of the UI »
- **Critère d'acceptation** : test qui importe le domaine sans PySide6 ; `tests/test_tab_services.py` et le test de la logique hors UI passent.

### ARCH-002 — Les valeurs de la SIA 265/1 dans `calc/norms/`
- **Exigence** : les tableaux 6 (γ_M), 9 (η_mod) et 11 à 23 (tous les panneaux, Q-001 réponse B ; 19a/19b pour l'OSB/3) sont transcrits de `norm-library/SIA265-1-2018-FR.pdf`, un fichier par tableau `sia265-1-2018-tabNN-<désignation>.json` avec `_source` (édition, page), lus par un lecteur `calc/norms/sia265_1.py` qui les vérifie ; les valeurs fixées de 3.3.2.2 et 3.4.2.4 (f_v,d, f_t,90,d) sont lues dans les fichiers SIA 265 existants ou ajoutées à un fichier de clause. Aucune valeur de norme dans le code.
- **Source** : T29, T34, T55 ; CLAUDE.md « No hardcoding », principe 13
- **Critère d'acceptation** : test : chaque valeur du tableau du prototype (T29) est comparée au fichier transcrit, et toute différence est signalée à l'ingénieur avant implémentation (le fichier l'emporte sur le prototype) ; les extraits des tableaux sont tenus au PDF par un test.

### ARCH-003 — Le type et les services de l'onglet
- **Exigence** : l'onglet se construit sur un type et des services au sens de `docs/ui/building-a-tab.md` (aucun service n'en appelle un autre ; mots dans un `STRINGS` de `calc/tools/materials_tab_words.py`). Le choix du type (Q-005) est fixé à la revue d'architecture.
- **Source** : T57 ; D-06, D-19
- **Critère d'acceptation** : `tests/test_tab_overrides.py` et `tests/test_tab_services.py` passent avec l'onglet.

### ARCH-004 — Une seule source des noms et catégories des matériaux livrés
- **Exigence** : les noms fr/de/en et la catégorie de chaque matériau livré (SIA 261 lignes 28–30, classeur) vivent dans un seul fichier de données (`calc/libraries/materials-catalogue.json`, repris du `lib.json` du prototype des charges permanentes, les noms français de la SIA 261 relevés sur l'édition FR p. 77–78), indexé par l'id stable ; les valeurs, elles, restent lues à leur source (`calc/norms/`, `materials-library.json`), jamais recopiées.
- **Source** : T22, T54 ; principe 1
- **Critère d'acceptation** : test : chaque ligne avec valeur des tableaux 28–30 et chaque entrée du classeur a ses trois noms et sa catégorie ; aucun nombre dans `materials-catalogue.json`.

### ARCH-005 — L'onglet indépendant du projet dans le registre et la garde
- **Exigence** : `TabSpec` gagne une déclaration (`project=False` ou équivalent) lue par la garde de lecture seule pour ne pas refuser les écritures de l'onglet, et par la fenêtre pour ne rien lui demander au changement de document ; documentée dans `docs/ui/window.md` et `docs/decisions.md`.
- **Source** : T16
- **Critère d'acceptation** : test de `tab_guard` : un service de l'onglet Matériaux n'est pas refusé en lecture seule ; tous les autres le restent.

## 6. Contraintes

- **CON-001** — Valeurs de norme lues sur `norm-library/SIA265-1-2018-FR.pdf` (édition 2018), `SIA265-2021-FR/DE.pdf`, `SIA261-2020-FR/DE.pdf` ; jamais de mémoire ni du prototype. Source : T29, CLAUDE.md, principe 13.
- **CON-002** — « Valeurs de dimensionnement », jamais « valeurs de calcul », dans la fenêtre (fr) ; *Bemessungswerte*, *design values*. Source : T10.
- **CON-003** — Les projets existants (`materials.json` 1.0, couches `library`/`material`) se calculent à l'identique. Source : T50, T53 (inféré : compatibilité).
- **CON-004** — Les tests n'écrivent jamais dans la bibliothèque de l'ingénieur. Source : T51.
- **CON-005** — Les mots de la fenêtre en de, fr, en (`tests/test_i18n.py`). Source : T59.
- **CON-006** — Fichiers de `docs/` ≤ 100 KB, prose non coupée, LF. Source : CLAUDE.md (inféré).
- **CON-007** — Aucune annexe au rapport sur les matériaux. Source : T14.

## 7. Décisions prises

- **D-1** — Disposition A (liste / fiche / source à droite) ; B et C écartées. (T7, ingénieur 24.10.2026)
- **D-2** — Nom « Matériaux » / *Materialien* / *Materials* ; dossier `materials`. (T8)
- **D-3** — Trois types : barre, panneau, autre ; « autre » ne porte qu'un poids. (T9)
- **D-4** — Valeurs caractéristiques et de dimensionnement saisissables ; les dimensionnement vides déduites ; la saisie l'emporte. (T10, T32)
- **D-5** — La bibliothèque dans `%APPDATA%\Woodcore\materials\`, PDF dans `sources\`. (T11)
- **D-6** — Le projet garde une copie du matériau personnel ; avertissement si l'original change. (T12)
- **D-7** — `materials.json` du projet devient la copie ; on n'y écrit plus directement. (T13)
- **D-8** — Pas d'annexe des matériaux dans le rapport pour l'instant. (T14)
- **D-9** — Le module « La source » et l'étiquette cliquable ; la source en grand par ⤢. (T38–T40, réponse 1)
- **D-10** — La décision de #94 s'applique : découper et imprimer la norme sans limite. (T62)
- **D-11** *(proposée par la spec, à approuver)* — « La bibliothèque a changé » se constate par comparaison champ par champ (pas de numéro de version par matériau), ce qui permet de dire quelles valeurs ; « Garder la copie » mémorise l'empreinte de l'original refusé. (T48, T61)
- **D-12** *(proposée par la spec, à approuver)* — Un matériau livré n'est pas copié dans le projet : il est lu dans la version de Woodcore qui calcule, comme une classe de la SIA 265 aujourd'hui. (T47 dit « matériau personnel »)
- **D-14** — Tous les panneaux de la SIA 265/1 (tableaux 11 à 23) dans ce lot. (Q-001, 24.10.2026)
- **D-15** — Les matériaux d'un `materials.json` 1.0 sont versés dans la bibliothèque de l'utilisateur à l'ouverture. (Q-003, 24.10.2026)
- **D-16** — Une barre personnelle n'entre ni dans les vérifications ni dans les assemblages dans ce lot. (Q-004, 24.10.2026)
- **D-17** — #111 est réalisée dans la même session, dans sa propre spec, après celle-ci. (Q-002, 24.10.2026)
- **D-13** *(proposée)* — Le drapeau « exemple » est un champ du matériau, pas un mot de son nom (le prototype cherchait « exemple » dans le nom). Aucun exemple n'est livré dans la bibliothèque de l'utilisateur.

## 8. Hors périmètre

- Une annexe ou un chapitre du rapport sur les matériaux (T14).
- La refonte du tableau des couches, la coupe, la valeur retenue et le volet droit de Poids propre : #111, dans sa propre spec, réalisée juste après celle-ci dans la même session (Q-002).
- Une barre personnelle proposée dans les vérifications d'éléments et les assemblages (Q-004, réponse A) : une issue suivante.
- Les dispositions B et C (T7).
- Un onglet « Plaques et voiles » (seulement « à venir » dans « Disponible dans »).
- La fin de la lecture du classeur de charges (#109) : hors de cette spec, la bibliothèque livrée restant une source (Q-006).

## 9. Idées non retenues comme exigences

- La comparaison de trois dispositions (version 1 de l'artefact) : réglée par D-1.
- Le libellé « needs_d » du prototype (« il faut les valeurs de calcul ») : remplacé par « valeurs de dimensionnement » (CON-002).
- Les quatre exemples « Personnel » de `libdata.json` : des exemples du prototype, non livrés (D-13) ; ils servent de cas de test.

## 10. Questions

### Q-001 — La portée de la SIA 265/1 dans ce lot
- **Pourquoi elle compte** : chaque tableau de panneaux est une transcription à relire sur le PDF (13 tableaux de plus), avec ses extraits et ses tests ; le choix fixe la taille du lot.
- **Options** : A (recommandée) les tableaux 6 et 9 en entier (les 12 dérivés, pour la déduction d'un panneau personnel) et l'OSB/3 (19a/19b) seul comme panneau livré ; les autres panneaux dans une issue suivante. B : tous les panneaux (11 à 23). C : OSB/2, OSB/3, OSB/4 (18 à 20).
- **Réponse** : **B, tous les panneaux** (ingénieur, 24.10.2026) : tableaux 6 et 9, et 11 à 23 (contreplaqués, particules, OSB/2, OSB/3, OSB/4, fibres), chacun transcrit, livré, avec son extrait.

### Q-002 — L'onglet Poids propre dans ce lot
- **Pourquoi elle compte** : la copie dans le projet (REQ-013) et l'avertissement (REQ-014) n'existent que si un onglet nomme un matériau personnel ; #111 refait cet onglet.
- **Options** : A (recommandée) ce lot retire la carte « Bibliothèque du projet » et branche le choix du matériau d'une couche sur la liste unique (livrés + personnels), avec copie et avertissement ; le reste de l'onglet à #111. B : ce lot ne touche pas Poids propre ; la copie et l'avertissement sont écrits et testés dans le domaine, branchés par #111.
- **Réponse** : « implémente également l'issue 111 pour le poids propre » (ingénieur, 24.10.2026). → #111 est réalisée dans la même session, **dans sa propre spec** (`docs/requirements/completed/2026-10-24-poids-propre-repense.md`, écrite et approuvée à son tour), juste après celle-ci. Cette spec-ci garde REQ-016 (la carte retirée, le choix du matériau d'une couche sur la liste unique, la copie, l'avertissement) : c'est le point où les deux se rejoignent, et #111 refait le reste du tableau des couches sur cette base.

### Q-003 — Les matériaux écrits à la main dans un `materials.json` 1.0
- **Pourquoi elle compte** : les verser dans la bibliothèque de l'utilisateur à l'ouverture la remplirait des matériaux de chaque projet ouvert, y compris ceux d'un collègue.
- **Options** : A (recommandée) ils restent la copie du projet (lue telle quelle, écrite en 2.0 au prochain enregistrement), avec « Ajouter à ma bibliothèque » proposé dans l'avertissement. B : versés dans la bibliothèque à l'ouverture, avec un message.
- **Réponse** : **B, versés dans ma bibliothèque** (ingénieur, 24.10.2026). Détail dans REQ-015 (un matériau déjà présent sous le même nom et le même poids est réutilisé, non dupliqué).

### Q-004 — Les vérifications d'éléments et les assemblages lisent-ils une barre personnelle ?
- **Pourquoi elle compte** : aujourd'hui ils lisent `sia265.grades()` et `sia265.rho_k(grade)` ; lire une barre personnelle change leur formulaire, leur export et le rapport.
- **Options** : A (recommandée) pas dans ce lot : « Disponible dans » dit « à venir » pour une barre personnelle ; une issue suivante. B : dans ce lot, la barre personnelle complète proposée comme une classe.
- **Réponse** : **A, pas dans ce lot** (ingénieur, 24.10.2026, après un schéma des deux options). Une issue suivante est à ouvrir.

### Q-005 — Le type de l'onglet *(tranché à la revue d'architecture, sauf avis de l'ingénieur)*
- **Pourquoi elle compte** : #105 (Éditeur) et #106 (Données) ne sont pas encore construits ; l'onglet ne suit ni l'un ni l'autre (liste + fiche + volet de modules, sans fichier du projet).
- **Options** : A (recommandée) un type « Bibliothèque » mince sur `TabHost`, avec ses services (liste groupée, fiche, volet de modules) écrits pour resservir ; B attendre #105.
- **Réponse** : **A**, approuvée avec la spec (ingénieur, 24.10.2026).

### Q-006 — La bibliothèque livrée tirée du classeur reste-t-elle une source (« Externe ») ?
- **Pourquoi elle compte** : #109 retire la lecture du classeur ; l'issue la garde « sauf décision contraire, à confirmer ».
- **Options** : A (recommandée) oui, livrée avec Woodcore, en lecture seule ; B non.
- **Réponse** : **A**, approuvée avec la spec (ingénieur, 24.10.2026).

## 11. Critères d'acceptation

- [x] REQ-001 — `materials_dir()` et ses trois cas ; la suite n'écrit pas dans `%APPDATA%`.
- [x] REQ-002 — schéma `user-materials` 1.0 ; écriture invalide refusée ; fichier corrompu nommé.
- [x] REQ-003 — ids stables, liste témoin des ids livrés.
- [x] REQ-004 — trois types validés.
- [x] REQ-005 — catalogue des livrés lu à leur source, en lecture seule.
- [x] REQ-006 — duplication avec provenance.
- [x] REQ-007 — nouveau / enregistrer / annuler / supprimer.
- [x] REQ-008 — déduction : C24, GL24h, OSB/3, limite f_c,90, valeurs fixées.
- [x] REQ-009 — états.
- [x] REQ-010 — « Disponible dans ».
- [x] REQ-011 — recherche ET, trois langues, filtres.
- [x] REQ-012 — PDF copié, nom nettoyé, dédoublonné.
- [x] REQ-013 — copie 2.0 dans le projet, calcul identique sans la bibliothèque.
- [x] REQ-014 — avertissement « a changé », reprendre / garder / ajouter.
- [x] REQ-015 — lecture du 1.0, calcul identique.
- [x] REQ-016 — Poids propre sans `ProjectMaterials`, liste unique (selon Q-002).
- [x] UI-001 … UI-008 — la place, l'indépendance du projet, la liste, la fiche, les grilles, le volet, les extraits.
- [x] ARCH-001 … ARCH-005 — domaine sans Qt, SIA 265/1 dans `calc/norms/`, type et services, une seule source des noms, registre et garde.
- [x] Documentation : `docs/domain/materials.md`, `docs/ui/tab-materials.md`, `docs/ui/window.md`, `docs/ui/building-a-tab.md` (le type), `docs/decisions.md` (D-07 remplacée), `docs/open-questions.md`, `docs/README.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en.
- [x] Tests : `tests/test_materials_domain.py`, `tests/test_materials_library.py`, `tests/test_materials_tab.py`, extensions de `test_tab_registry.py`, `test_dead_load_source.py`, `test_i18n.py` ; une ligne au catalogue des tests ; la suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T0 | §2 (règle de lecture) | capturé |
| T1 | UI-001 | capturé |
| T2 | REQ-004, UI-004 | capturé |
| T3 | REQ-012 | capturé |
| T4 | REQ-010, REQ-016, Q-004 | capturé, portée → question |
| T5 | REQ-001 | capturé |
| T6 | REQ-016 | capturé |
| T7 | D-1 | décision |
| T8 | D-2, UI-001, REQ-001 | décision |
| T9 | D-3, REQ-004 | décision |
| T10 | D-4, REQ-008, CON-002 | décision |
| T11 | D-5, REQ-001 | décision |
| T12 | D-6, REQ-013, REQ-014 | décision |
| T13 | D-7, REQ-013 | décision |
| T14 | D-8, CON-007, §8 | décision |
| T15 | UI-001 | capturé |
| T16 | UI-002, ARCH-005 | capturé |
| T17 | UI-003, REQ-004 | capturé |
| T18 | REQ-011 | capturé |
| T19 | REQ-011, UI-003 | capturé |
| T20 | UI-003 | capturé |
| T21 | UI-003, REQ-006, REQ-007 | capturé |
| T22 | REQ-005, ARCH-004 | capturé |
| T23 | REQ-007 | capturé |
| T24 | REQ-006, UI-004 | capturé |
| T25 | UI-004, REQ-005 | capturé |
| T26 | UI-004 | capturé |
| T27 | REQ-007 | capturé |
| T28 | REQ-004, UI-005 | capturé |
| T29 | REQ-004, UI-006, ARCH-002, CON-001 | capturé |
| T30 | REQ-004, UI-006 | capturé |
| T31 | UI-006 | capturé |
| T32 | REQ-008, UI-005 | capturé |
| T33 | REQ-008 | capturé |
| T34 | REQ-008, ARCH-002 | capturé |
| T35 | REQ-008 | capturé |
| T36 | REQ-008 | capturé |
| T37 | REQ-008 | capturé |
| T38 | UI-007, D-9 | capturé |
| T39 | UI-007, UI-008 | capturé |
| T40 | UI-007 | capturé |
| T41 | REQ-012 | capturé |
| T42 | REQ-009 | capturé |
| T43 | UI-007 | capturé |
| T44 | REQ-010, Q-004 | capturé, proposition → question |
| T45 | UI-007 | capturé |
| T46 | UI-004 | capturé |
| T47 | REQ-013, D-12 | capturé |
| T48 | REQ-014, D-11 | capturé |
| T49 | REQ-013, REQ-016 | capturé |
| T50 | REQ-015, Q-003 | ambigu → question |
| T51 | REQ-001, CON-004 | capturé |
| T52 | REQ-002, REQ-003 | capturé |
| T53 | REQ-013, REQ-015 | capturé |
| T54 | ARCH-001, REQ-011, REQ-016 | capturé |
| T55 | ARCH-002, Q-001 | capturé, portée → question |
| T56 | UI-008 | capturé |
| T57 | ARCH-003, Q-005 | capturé, type → question |
| T58 | REQ-016, Q-002, Q-004 | portée → questions |
| T59 | CON-005, §11 | capturé |
| T60 | §11 Documentation | capturé |
| T61 | REQ-003, REQ-014, D-11 | capturé |
| T62 | D-10, UI-008 | décision |
| T63 | REQ-005, Q-006 | à confirmer → question |

### Points de la source non résolus

Aucun qui bloque : Q-001 à Q-004 répondues le 24.10.2026 ; Q-005 (type de l'onglet) et Q-006 (la bibliothèque livrée reste « Externe ») sont tranchées par la recommandation et soumises à l'approbation.

## 13. Revue d'architecture

Deux relecteurs `architecture-reviewer` en parallèle, le 24.10.2026 : le domaine et les données (D), l'onglet et la fenêtre (U). Verdict des deux : **APPROUVER AVEC RÉSERVES**. Chaque réserve est levée ci-dessous ; ce qui change la spec devient une exigence `ARCH-006…` (source « revue »).

### Modules concernés
- Domaine : `calc/domains/materials.py` (poids d'une couche, 1.0 du projet, `weight(layer)`), `dead_load_source.py:95,155,178,210` (`LIBRARIES`, `layer_rows`), `schemas/dead-load-source.schema.json:65` (enum fermé `library`), `schemas/materials.schema.json` (`const "1.0"`), `calc/norms/sia265.py` (`grades()` l.823, `gamma_m` l.913, `CHARACTERISTIC_OF` l.596), `calc/norms/excerpts.py` (`FALLBACK="de"`), `calc/usersettings.py:34` (`templates_dir`), `calc/domains/annex.py:98-124` (`copy_pdf`), `calc/validation.py` (ni `oneOf` ni `$ref`), `woodcore_gui.py:1019-1048` (migrations à l'ouverture, sous `if not read_only`).
- Fenêtre : `tab_registry.py:45` (`TabSpec`), `:130-139` (garde), `tab_guard.py:12-77` (`WRITERS`, `refused_when_read_only`), `tab_host.py` (suppose `MODULE`, `SourceStore`, `LinkSet`, Affichage, Ctrl+S, cas : l.137, 397, 406, 414, 443, 657), `woodcore_gui.py:353` (`available`), `:709` (`refresh_lightly`), `autosave.py:136-174` (`leave`), `module_pane.py:125` (`ModulePane`, `Module`), `grouped_list.py` (dossiers = champs du projet), `norm_bubble.ExcerptView`, `excerpt_image.py`, `pdf_pane.ZoomablePdfView`, `calc_fields.py:25,284` (le seul clignotement), `chrome.SegmentedSwitch`, `woodcore_gui_words.py:764`.

### Risques et décision prise pour chacun

| Risque | Gravité | Ce que la spec et le plan en font |
|---|---|---|
| U01 — `TabHost` suppose un domaine à cas (`SourceStore`, Affichage, Ctrl+S) | bloquant | **ARCH-006** : un type léger `library_tab.LibraryTab(QWidget)`, hors de `TabHost`, qui monte des `tab_host.Service` (réutilisés, sans `TabContext`) dans les trois zones, avec un `LibraryContext` minimal (le brouillon d'un matériau, `dirty`, `loading`, un seul `touch`), et répond au `TAB_API` que la fenêtre appelle. Q-005 répondue ainsi, soumise à l'approbation ; un rapprochement avec `TabHost` (une base `TabFrame` commune) est une suite, à noter dans `building-a-tab.md`. |
| U02 — déclarer un onglet indépendant du projet | bloquant | **ARCH-005 précisé** : `TabSpec.project: bool = True`, `False` pour Matériaux, lu en un seul endroit chacun : la garde (les services de l'onglet ne déclarent aucun `WRITERS` et ses écrivains s'appellent `save_material`, `delete_material`, hors de `tab_guard.WRITERS`), `woodcore_gui.available()` (jamais grisé), `refresh_lightly` (jamais « stale » après un export), `autosave.leave` (ni refus en lecture seule ni report ; un brouillon non enregistré n'est **jamais** écrit en silence : `confirm_leave` demande). Test : tout autre écrivain reste refusé en lecture seule ; le module de l'onglet n'appelle jamais `project.current()` (test AST). |
| U03 — groupe « Autres », mots | important | `TabSpec("tab_materials", …, "nav_others", documents=ALL, project=False)` en dernier ; `nav_others`, `tab_materials`, `mat_*` dans `calc/tools/materials_tab_words.py`, fusionné par `woodcore_gui_words.py` ; icône dans `chrome.ICONS` ; icônes des trois types en SVG (`svg_icons`), jamais d'emoji. |
| U04, U06 — brouillon et comptes | important | Le brouillon est un dict du domaine ; toute pastille, tout résumé « ✓ / n ✕ » et tout filtre lisent `materials_derive.status()` et `materials_search.search()`, jamais un recomptage dans un widget. |
| U05, U08, U09 — `ModulePane` et ses mots `ct_*`, le ⤢, `test_tab_overrides` | important / mineur | `ModulePane` réutilisé tel quel, plus `reveal(module_id)` (défile et clignote, le clignotement extrait de `calc_fields` en un helper partagé, pas recopié) ; l'accordéon de la fiche est `module_pane.Module` extrait en `Fold` partagé ; le ⤢ (T40, « par-dessus la fenêtre ») est un overlay `big_view.BigView` (enfant plein-fenêtre, Échap / ×) dans le seul module « La source » ; `test_tab_overrides` étendu au type nouveau. |
| U07 — grilles en Qt | mineur | `QTableWidget` + `QStyledItemDelegate` (italique par `FontRole`, fond `theme.json` clé nouvelle `missing`, `ToolTipRole`) ; bascule k\|d par `chrome.SegmentedSwitch` ; colonnes données par le domaine. |
| U10 — sans projet | mineur | La page d'accueil n'a pas d'onglets : la bibliothèque n'y est pas ; une ligne dans `window.md`. |
| D01 — clés d'une couche, enum fermé | bloquant | **ARCH-007** : `dead-load-source` 1.2 ajoute `library: "catalogue"` dont `material` est l'id unifié (`sia265:C24`, `sia265-1:osb3-…`, `sia261:<id>`, `ext:<row>`, `u-…`). Les couches `sia261`, `belastungsannahmen`, `project` restent lues à vie (CON-003) ; une couche écrite par la fenêtre l'est en `catalogue` ; la version 1.2 n'est écrite que quand une couche la demande (`stamp_version`). |
| D02 — ids livrés | bloquant | `sia261:<id de ligne>` (94 ids uniques sur les trois tableaux, vérifié) ; `ext:<row>` (236 `row` uniques) ; `sia265:<classe>` ; `sia265-1:<produit>`. La liste fusionnée est une **vue** : `weight()` lit toujours le fichier complet, une ligne écartée par la fusion reste calculable. Liste témoin de **tous** les ids livrés (`tests/test_materials_catalogue.py`). |
| D03 — le poids d'une classe SIA 265 | important | **ARCH-008** : `calc/libraries/materials-catalogue.json` déclare, pour chaque famille (résineux, feuillus, lamellé-collé) et pour chaque panneau, l'id de la ligne SIA 261 ou du classeur qui donne son poids ; aucun nombre dans le catalogue ni le code ; ρ_k (résistance) et poids (charge) restent deux champs, deux sources (T46). |
| D04 — f_v,d, f_t,90,d déjà dans tab08/tab09 | important | **ARCH-002 précisé** : deux fichiers de clause `sia265-2021-3.3.2.2-valeurs-fixees.json` et `sia265-2021-3.4.2.4-valeurs-fixees.json`, lus par `sia265.fixed_design_value(family, key)` et tenus égaux aux classes des tableaux 8 et 9 par un test (patron de `CHARACTERISTIC_OF`). Une classe livrée n'a que ses `_d` (les tableaux 8/9 n'impriment pas f_t,0,k…) : une résistance est complète par sa `_d`. `f_c_90_d` de la fiche = la valeur `generell` ; les deux autres cas restent ceux de la vérification. |
| D05 — SIA 265/1 | important | `calc/norms/sia265_1.py` (sur `_loader`, ses `FILES` et ses contrôles), un fichier par tableau `sia265-1-2018-tabNN-<désignation>.json` (6, 9, 11a/b … 23a/b), une forme de colonne de panneau définie une fois et partagée avec le schéma des matériaux ; un fichier d'extraits par norme (`sia265-2021-excerpts.json`, `sia265-1-2018-excerpts.json`, `sia261-2020-materials-excerpts.json`) ; **ARCH-009** : `excerpts.FALLBACK` cède à la seule édition livrée quand une norme n'en a qu'une (265/1 en FR). Les tableaux b de la norme sont les valeurs de dimensionnement des panneaux livrés : lus, jamais déduits. |
| D06 — forme commune d'un matériau | important | **ARCH-010** : un seul contrat d'un matériau (`materials_contract.py` : les champs, leurs unités, la forme d'un panneau), deux enveloppes : `schemas/user-materials.schema.json` 1.0 et `schemas/materials.schema.json` passé à l'enum `["1.0","2.0"]` (règles par version dans `check_project`, comme `dead-load-source`) ; la définition des `items` des deux schémas tenue égale par un test (le validateur n'a pas `$ref`). |
| D07 — écrire hors du projet ; la copie | important | La bibliothèque : `engine.write_json` (atomique), relue avant chaque écriture (deux fenêtres) ; un fichier malformé n'est jamais écrasé et l'onglet s'ouvre en lecture seule avec le message. La copie dans le projet est écrite par l'écrivain gardé du cas (Poids propre). Dans un projet en lecture seule, une couche qui nomme `u-…` sans copie arrête le calcul en nommant la couche (REQ-013 complété). |
| D08 — la migration 1.0 | important | `calc/domains/materials_migrate.py`, appelée par `woodcore_gui.py` dans un bloc à elle (la bibliothèque est écrite même en lecture seule, le projet seulement hors lecture seule) ; bibliothèque d'abord, puis le projet ; l'ancien fichier archivé avant (comme `loads_migrate`) ; l'identité « même nom et même poids » sur le poids converti en kN ; le message nomme les matériaux versés. |
| D09 — « a changé », « Garder la copie » | important | Diff à deux niveaux : un champ de calcul (valeur, poids, type, famille, dérivé) → orange ; un mot (nom, commentaire, source) → info ; nombres comparés avec une tolérance relative de 1e-9. « Garder » écrit dans la copie `kept_fingerprint` = SHA-256 de la forme canonique (`engine.source_bytes`) des champs de calcul de l'original refusé : l'export reste reproductible. |
| D10 — PDF dans le projet | important | Copié à l'enregistrement du cas dans `Woodcore-Datei/materials/`, dossier créé à la demande (pas ajouté à `SOURCE_FOLDERS`), chemin relatif ; retiré quand plus aucune copie ne le nomme. `import_pdf` part de `annex.copy_pdf` / `appendix_name` (nom nettoyé), généralisé plutôt que recopié. |
| D11 — taille de `materials.py` | mineur | Scindé (§14) : `materials.py` (unités, `weight`, compat), `materials_contract.py`, `materials_catalogue.py`, `materials_user.py`, `materials_derive.py`, `materials_search.py`, `materials_project.py`, `materials_migrate.py`. |
| D12 — catégories en un seul lieu | mineur | Une table des 11 catégories (code, synonymes de recherche) dans le domaine ; leurs mots visibles dans `STRINGS` ; test « pas d'id orphelin » et « chaque livré a son entrée au catalogue ». |
| D13 — arrondi | mineur | `materials_derive.round_tenth` en `decimal` `ROUND_HALF_UP`, testé sur des demis. |
| D14, D15 — D-07 et `ProjectMaterials` | mineur | D-07 marquée remplacée par renvoi (non supprimée) ; `project_materials.py`, `save_project_library` de `tab_guard.WRITERS`, ses mots `ld_*` et la ligne de `DeadLoadTab.SERVICES` retirés, attestés par `test_tab_services.py`. |

### Exigences ajoutées par la revue

- **ARCH-006** — Le type `LibraryTab` hors de `TabHost`, ses services (`MaterialList` gauche, `MaterialSheet` centre, `MaterialModules` droite) et son `LibraryContext` ; aucun service n'en appelle un autre. Source : revue U01. Critère : `test_materials_tab.py` monte chaque service seul ; `test_tab_services.py` étendu.
- **ARCH-007** — `dead-load-source` 1.2 et la clé `library: "catalogue"` ; les anciennes clés lues à vie. Source : revue D01. Critère : `test_dead_load_source.py` : les compositions du projet d'exemple se calculent à l'identique ; une couche `catalogue` nomme `sia261:…`, `ext:…`, `sia265-1:…`, `u-…`.
- **ARCH-008** — Le poids d'un matériau livré de résistance pris d'une ligne déclarée de la SIA 261 ou du classeur. Source : revue D03. Critère : test : C24 pèse ce que dit la ligne SIA 261 qu'il déclare.
- **ARCH-009** — `excerpts` accepte une norme d'une seule édition. Source : revue D05. Critère : `test_norm_excerpts.py` découpe les extraits de la SIA 265/1 (FR) en fenêtre allemande et anglaise.
- **ARCH-010** — Un contrat d'un matériau, deux enveloppes de schéma tenues égales. Source : revue D06. Critère : test d'égalité des `items`.

### Tests à ajouter ou étendre
Nouveaux : `test_materials_library.py`, `test_materials_domain.py`, `test_materials_catalogue.py`, `test_sia265_1.py`, `test_materials_migrate.py`, `test_materials_tab.py`. Étendus : `test_norm_excerpts.py`, `test_dead_load_source.py`, `test_schema*.py`, `test_tab_registry.py`, `test_tab_services.py`, `test_tab_overrides.py`, `test_module_pane.py`, `test_autosave*.py`, `test_i18n.py`, un test d'import du domaine sans PySide6 ; le catalogue des tests.

### Verdict
**APPROUVER AVEC RÉSERVES**, toutes levées par les décisions ci-dessus et le plan ; deux choix restent à l'ingénieur à l'approbation : le type `LibraryTab` hors de `TabHost` (Q-005) et la bibliothèque livrée gardée comme source « Externe » (Q-006).

## 14. Plan d'implémentation

Chaque étape finit par ses tests verts et une ligne au §16. Les étapes 3 et 4 (la transcription) sont les plus longues : chaque tableau est lu sur la page du PDF, pas sur le prototype ; une différence avec le prototype est notée et dite à l'ingénieur.

1. **Le dossier et les contrats** — `usersettings.materials_dir()` (`WOODCORE_MATERIALS`, frère `<stem>-materials` sous `WOODCORE_SETTINGS`) ; `materials_contract.py` (types, familles, dérivés, catégories, forme d'un panneau) ; `schemas/user-materials.schema.json` 1.0 ; `schemas/materials.schema.json` → enum 1.0/2.0. *REQ-001, 002, 004, ARCH-010.* Tests : `test_materials_library.py` (trois cas du dossier, garde-fou « jamais sous `%APPDATA%` »), test d'égalité des `items`.
2. **La bibliothèque de l'utilisateur** — `materials_user.py` : lire (malformé → `ValidationError` nommée), écrire validé et atomique (relu avant), ids `u-<8 hex>`, `import_pdf` (sur `annex.copy_pdf` généralisé : nom nettoyé, `-2`, même contenu réutilisé), suppression du PDF orphelin, `duplicate()`. *REQ-002, 003, 006, 007 (domaine), 012.*
3. **SIA 265 : les valeurs fixées et le poids** — fichiers de clause 3.3.2.2 et 3.4.2.4, `sia265.fixed_design_value`, test d'égalité aux tableaux 8/9 ; extraits des tableaux 8 et 9 (`sia265-2021-excerpts.json`) ; extraits de la SIA 261 tableaux 28–30 ; `excerpts` à une seule édition. *ARCH-002, ARCH-009, UI-008.*
4. **SIA 265/1** — `calc/norms/sia265_1.py` ; tableaux 6 et 9 ; puis 19a/19b (OSB/3, contrôlé contre le prototype) ; puis 11a/b … 23a/b, un tableau à la fois, chacun avec son extrait (`sia265-1-2018-excerpts.json`) et son test tenu au PDF. *ARCH-002, REQ-005, UI-008, D-14.* Tests : `test_sia265_1.py`, `test_norm_excerpts.py`.
5. **Le catalogue des livrés** — `calc/libraries/materials-catalogue.json` (noms fr/de/en et catégorie par id, repris de `lib.json` du prototype des charges permanentes ; le poids de chaque famille et panneau par l'id de sa ligne) ; `materials_catalogue.py` : SIA 265, SIA 265/1, SIA 261 (28–30), classeur fusionné en vue. *REQ-003, 005, ARCH-004, ARCH-008.* Tests : `test_materials_catalogue.py` (liste témoin, pas d'orphelin, aucun nombre).
6. **Déduction, état, disponibilité, recherche** — `materials_derive.py` (`design_value`, `round_tenth`, `status`, `available_in`) ; `materials_search.py`. *REQ-008, 009, 010, 011.* Tests : `test_materials_domain.py` (C24, GL24h, OSB/3, limite f_c,90, valeurs fixées, états, ET en trois langues sans accents) ; import sans PySide6.
7. **La copie du projet, le diff, la migration, le poids d'une couche** — `materials_project.py` (copie 2.0, PDF dans `Woodcore-Datei/materials/`, diff à deux niveaux, `kept_fingerprint`) ; `materials.weight()` accepte `catalogue` ; `dead-load-source` 1.2 ; `materials_migrate.py` et son appel à l'ouverture dans un bloc à lui. *REQ-013, 014, 015, ARCH-007, D-15.* Tests : `test_materials_migrate.py`, `test_dead_load_source.py`.
8. **Poids propre branché** — `ProjectMaterials` retiré (`project_materials.py`, `save_project_library`, mots `ld_*`) ; le choix du matériau d'une couche sur la liste unique avec la recherche ; la copie écrite à l'enregistrement du cas ; l'avertissement « a changé » dans l'état du cas avec « Reprendre » / « Garder » / « Ajouter à ma bibliothèque ». *REQ-016, REQ-014 (fenêtre).* Ce strict minimum ; le reste du tableau des couches est la spec de #111.
9. **Le type `LibraryTab` et le registre** — `library_tab.py` (`LibraryTab`, `LibraryContext`) ; `TabSpec.project` et ses cinq lectures (garde, `available`, `refresh_lightly`, `autosave.leave`, tests) ; `nav_others` ; `Fold` extrait de `module_pane.Module` ; helper de clignotement extrait de `calc_fields` ; `ModulePane.reveal`. *ARCH-005, ARCH-006, UI-001, UI-002.* Tests : `test_tab_registry.py`, `test_tab_overrides.py`, `test_module_pane.py`, `test_autosave*.py`.
10. **Les services de l'onglet Matériaux** — `materials_tab.py`, `materials_tab_words.py` (de/fr/en) ; `MaterialList` (catégories repliables comptées, recherche, puces, étiquettes cliquables, + Nouveau / Dupliquer / Supprimer) ; `MaterialSheet` (accordéons, grilles barre et panneau en `QTableWidget` + délégué, italique et infobulle, case manquante colorée, k\|d) ; `MaterialModules` (État, La source avec `ExcerptView` / `ZoomablePdfView` / lien / zone de dépôt, ⤢ par `big_view.BigView`, Disponible dans, Où il est enregistré) ; `theme.json` clé `missing` ; icônes. *UI-003 … UI-008, REQ-007.* Tests : `test_materials_tab.py`, `test_i18n.py`.
11. **Documentation** — `docs/domain/materials.md` (nouveau), `docs/ui/tab-materials.md` (nouveau), `docs/ui/window.md`, `docs/ui/building-a-tab.md` (le type Bibliothèque), `docs/domain/loads.md` §3.3ter, `docs/decisions.md` (décision nouvelle, D-07 marquée remplacée), `docs/open-questions.md` (SIA 265/1 transcrite ; barre personnelle dans les vérifications : suite), `docs/README.md`, catalogue des tests, `CHANGELOG.md`, « Nouveautés » fr/de/en.
12. **Vérifier dans la fenêtre** — lancer Woodcore sur une copie du projet d'exemple, parcourir l'onglet, faire une capture ; puis la vérification indépendante et `finish`.

## 15. Vérification

Vérificateur indépendant (`requirements-verifier`, 24.10.2026), sur le diff de l'arbre de travail contre `5bbd30d` ; 15 fichiers de tests lancés un à un, tous verts. Points de norme relus sur les PDF : SIA 265/1 p. 42 (tableaux 19a/b), SIA 265 FR p. 25 (tableau 8).

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `usersettings.materials_dir()` ; `test_materials_library.test_the_folder_is_…`, `test_this_suites_library_is_never_the_engineers` |
| REQ-002 | ✅ | `test_an_invalid_material_is_refused_and_the_file_left_as_it_was`, `test_a_file_that_cannot_be_read_…` |
| REQ-003 | ✅ | `test_an_id_is_drawn_once_…`, `test_materials_catalogue.test_the_ids_of_this_version_are_still_shipped` |
| REQ-004 | ✅ (2e tour) | ⚠️ au 1er tour (refus d'une barre à grille non testé) → `test_materials_domain.test_each_type_is_checked_and_a_member_carries_no_panel_grid` |
| REQ-005 | ✅ | `test_materials_catalogue` (243 livrés, 94 lignes SIA 261, 20 panneaux), `test_a_shipped_material_is_read_only` |
| REQ-006 | ✅ | `test_duplicating_a_shipped_class_makes_a_material_of_ones_own` |
| REQ-007 | ✅ (2e tour) | ⚠️ au 1er tour (panneau et PDF non testés dans l'onglet) → `test_materials_tab.test_a_new_panel_with_its_pdf_is_saved_read_back_and_deleted_with_its_pdf` ; il a révélé deux défauts corrigés : un panneau sans dérivé ne s'enregistrait pas (produit rendu facultatif, schémas et contrat), et le PDF montré à droite restait verrouillé sous Windows (chargé désormais depuis ses octets, `materials_pane._pdf`) |
| REQ-008 | ✅ | `test_materials_domain.test_a_design_value_typed_set_or_deduced`, `test_the_set_values_are_tabelle_8_and_9s`, `test_rounding_is_half_up` |
| REQ-009 | ✅ | `test_the_state_of_a_material` |
| REQ-010 | ✅ | `test_where_a_material_is_offered` |
| REQ-011 | ✅ | `test_every_word_is_found_in_three_languages` |
| REQ-012 | ✅ | `test_a_pdf_is_copied_under_a_clean_name_…` |
| REQ-013 | ✅ | `test_materials_migrate.test_a_copy_is_taken_at_a_save_…` ; `test_load_tab` (copie prise à l'enregistrement) |
| REQ-014 | ✅ | `test_a_change_in_the_library_is_said_and_kept_or_taken`, `test_a_material_another_computer_lacks_…` |
| REQ-015 | ✅ | `test_a_project_of_before_is_poured_into_the_library_once`, `…not_poured_twice`, `…read_only…` |
| REQ-016 | ✅ (2e tour) | `project_materials.py` supprimé ; assertion nommée ajoutée (`test_load_tab` : `ProjectMaterials` absent de `DeadLoadTab.SERVICES`) |
| UI-001 à UI-008 | ✅ | `test_materials_tab` (9), `test_tab_registry`, `test_norm_excerpts` |
| ARCH-001 à ARCH-010 | ✅ | `test_the_domain_imports_no_qt`, `test_sia265_1`, `test_tab_overrides`, `test_tab_services`, `test_materials_catalogue`, `test_dead_load_source`, `test_norm_excerpts`, `test_the_two_schemas_of_a_material_hold_one_shape` ; ARCH-002 complété au 2e tour par `test_every_value_transcribed_is_on_its_page` (chaque valeur des tableaux 11 à 23 lue dans la couche texte de sa page) |
| CON-001 à CON-007 | ✅ | PDF relus ; CON-002 tenu par `test_the_window_says_valeurs_de_dimensionnement` (2e tour) ; CON-005 `test_i18n` ; CON-006 `test_docs_coherence` ; §8 non fait |
| Documentation | ✅ (2e tour) | ⚠️ au 1er tour : `docs/ui/calc-tab.md` et `docs/architecture/layout.md` nommaient encore `ProjectMaterials` et pas les modules nouveaux — corrigés |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #110 et du prototype ; 6 questions ouvertes (Q-001 à Q-006) |
| 2026-10-24 | specified | Q-001 B (tous les panneaux), Q-002 (#111 aussi, dans sa propre spec), Q-003 B (versés dans la bibliothèque), Q-004 A (hors lot) ; Q-005 et Q-006 à l'approbation |
| 2026-10-24 | reviewed | deux revues d'architecture (domaine, fenêtre) : approuver avec réserves, toutes levées au §13 (ARCH-006 à ARCH-010 ajoutées) ; plan en 12 étapes au §14 |
| 2026-10-24 | approved | approuvée par l'ingénieur ; Q-005 A (type `LibraryTab` à part) et Q-006 A (classeur gardé comme « Externe ») avec elle |
| 2026-10-24 | implementation | étapes 1 à 4 : `usersettings.materials_dir()` (+ nettoyage dans `tests/conftest.py`), `materials_contract.py`, schémas `user-materials` 1.0 et `materials` 1.0/2.0, `materials_user.py` ; SIA 265/1 : tableaux 6, 9 et 11 à 23 transcrits (20 panneaux, chaque valeur b tenue à η_mod·f_k/γ_M de son a), `norms/sia265_1.py` ; valeurs fixées 3.3.2.2 et 3.4.2.2 (et non 3.4.2.4 comme l'issue : 3.4.2.4 les reprend pour les BLC à joints universels), `sia265.set_design_value` ; extraits SIA 265 tab. 8–9, SIA 261 tab. 28–30, SIA 265/1 tab. 6, 9, 11–23 tenus aux PDF ; `excerpts` à une seule édition (ARCH-009). Reste : 5 à 12 |
| 2026-10-24 | implementation | étapes 5 et 6 : `calc/libraries/materials-catalogue.json` (noms fr/en, catégories, poids par id, aucun nombre), `materials_catalogue.py` (243 livrés : 11 classes, 20 panneaux, 94 lignes SIA 261, 118 du classeur fusionnés, chaque ligne gardée comme id), `materials_derive.py`, `materials_search.py` ; tests `test_materials_library`, `test_sia265_1`, `test_materials_catalogue`, `test_materials_domain` verts ; `test_norms` accepte une norme à partie (`sia265-1`) |
| 2026-10-24 | implementation | étape 7 : `materials.py` (copie 2.0, 1.0 lue, `library: "catalogue"`), `dead-load-source` 1.2 (`stamp_version`, `used_materials`), `materials_project.py` (copie, PDF, `sync`, `diff` à deux niveaux, `fingerprint`, `keep`/`take`/`add_to_library`), `materials_migrate.py` (bibliothèque d'abord, projet ensuite, archives, lecture seule), appelée à l'ouverture dans un bloc à elle avec l'avis `notice_materials_moved` (fr/de/en) ; `test_materials_migrate` vert (7) |
| 2026-10-24 | implementation | étape 8 : Poids propre sans `ProjectMaterials` (supprimé, `save_project_library` retiré de la garde) ; `LayerTable` : « Matériau » ou « Charge saisie », la liste unique cherchée par le domaine (`MaterialCombo`), les anciennes bibliothèques montrées pour une couche d'avant ; `material_copies.MaterialCopies` (Reprendre / Garder / Ajouter, écrivains gardés) ; `dead_load_source.messages` dit un matériau changé ; `SourceStore.save` appelle le `before_export` du domaine (copie prise avant l'export) ; `test_load_tab`, `test_tab_services`, `test_dead_load_source` verts |
| 2026-10-24 | implementation | étapes 9 et 10 : `TabSpec.project` (`PROJECT_FREE` : garde, `available`, `refresh_lightly`), groupe « Autres », icône ; type `library_tab.LibraryTab` + `LibraryContext` ; `module_pane.Fold` extrait de `Module`, `blink.Blinker` extrait de `calc_fields`, `ModulePane.reveal` ; services `materials_list`, `materials_sheet`, `materials_pane` (⤢ `BigView`, dépôt d'un PDF), `material_marks`, `materials_tab`, mots `materials_tab_words` (fr/de/en), `theme.json` `missing` ; `domains/materials_library.py` ; tests `test_materials_tab` (7), `test_tab_registry`, `test_tab_overrides`, `test_i18n` verts |
| 2026-10-24 | testing | étapes 11 et 12 : `docs/domain/materials.md` (§3.3sexvicies), `docs/ui/tab-materials.md`, `loads.md`, `window.md`, `building-a-tab.md`, `decisions.md` (+ index, D-07 remplacée), `open-questions.md`, `README.md`, catalogue `testing-catalogue-materials.md` (le catalogue principal étant à la limite de 100 Ko), `CHANGELOG.md`, « Nouveautés » 0.125 fr/de/en ; contrôle visuel de l'onglet hors écran (deux défauts corrigés : boutons du type sans texte, hauteur figée des modules du volet droit) |
| 2026-10-24 | verification | 1er tour : aucun ❌, ⚠️ sur REQ-004, REQ-007, REQ-016, ARCH-002 (fidélité au PDF), CON-002 et deux docs périmées ; tous levés (tests ajoutés, deux défauts réels corrigés : panneau sans dérivé, PDF verrouillé) |
| 2026-10-24 | completed | §11 coché ; spec déplacée dans completed/ ; reste le skill finish (suite complète, commit, question de la poussée) |
