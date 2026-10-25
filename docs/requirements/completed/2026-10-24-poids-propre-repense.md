---
id: 2026-10-24-poids-propre-repense
titre: Onglet Poids propre et surcharge repensé — tableau au clavier, poses, lignes liées, valeur retenue automatique, coupe à l'échelle, modèles, Affichage
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-24
source: issue GitHub #111 (texte validé par l'ingénieur le 24.10.2026) ; prototype docs/requirements/prototypes/2026-10-23-charges-permanentes/ (v3)
docs: [docs/domain/loads.md, docs/domain/materials.md, docs/ui/building-a-tab.md, docs/ui/calc-tab.md, docs/ui/window.md, docs/decisions.md]
---

# Onglet Poids propre et surcharge repensé — Spécification

## 1. Objectif

Refaire l'onglet « Poids propre et surcharge » d'après le prototype validé en trois tours (21, 23, 24.10.2026) : un tableau des couches compact, au clavier ; quatre poses de couche (continue, à entraxe, par surface, charge saisie) ; des lignes liées au même niveau qui remplissent le vide entre les pièces ; une charge de couche remplaçable ; une valeur retenue automatique au dixième supérieur ou égal ; une coupe à sa vraie proportion, la même dans la fenêtre et dans le rapport ; un volet droit ordonné ; des modèles (Lignum, « Mes modèles ») ; une vue d'ensemble ; la vue Affichage par niveau. Les matériaux viennent de l'onglet Matériaux (#110, fait) : l'onglet n'en crée plus.

## 2. Source

L'issue #111, mot pour mot, par points (le fichier complet de l'issue est cité ; les tableaux de réponses sont gardés ligne par ligne). L'issue l'emporte sur le prototype (T2).

> **T1** — « L'ingénieur a revu l'ergonomie de l'onglet « Poids propre et surcharge » sur des prototypes HTML, en trois tours, le 21 et le 23.10.2026. Il a validé la troisième version **entièrement** le 24.10.2026, avec ses réponses aux six questions qu'elle posait. »
>
> **T2** — « Le prototype sert de référence, mais **cette issue l'emporte là où les deux diffèrent**. »
>
> **T3** — « **Cette issue part de là.** Elle refait le tableau des couches, le calcul d'une couche, la valeur retenue, la coupe et le volet droit. Les matériaux viennent du nouvel onglet **Matériaux (#110)**, et cet onglet n'en crée plus. »
>
> **T4** — « l'onglet reste une classe de paramètres sur `CalcTab`, sans méthode (`tests/test_tab_overrides.py`) ; ce qui lui manque devient un **service**, écrit une fois et testé seul […] ; le calcul, les messages et les résultats sont dans `calc/domains/`, sans Qt. »
>
> **T5** — « Deux services sont propres aux couches et serviront ailleurs : **le tableau des couches au clavier** ; **la coupe d'une composition**. `docs/ui/building-a-tab.md` (D-19) l'annonce déjà comme un service qui lit `contracts.Layer` (`NEEDS = ("layers",)`). »
>
> **T6** — Le prototype : « `calcLoad`, `isFiller`, `fillerWidth` […] ; `sums` […] ; `autoRet` […] ; `formulaOf` […] ; `warnings` […] ; `SYN`, `hay`, `search`, `rank` […] ; `nextCell` […] `keydown` ; `sectionSVG` […] mode légende sous 560 px ; `contribHTML` ; `renderPage`, `renderDispRight`, `typFile` ; `renderTpl` ; `lib.py`, `lib.json` […] ; `comps.py` et `comps.json` : les 8 modèles Lignum et les 3 compositions du projet d'exemple. »
>
> Premier tour (21.10.2026) :
>
> **T7** — « Une couche, une ligne : Oui, mais compacte : une ligne de tableau d'environ 25 px. »
>
> **T8** — « La bibliothèque des matériaux : À la manière d'Ubakus […] Cela est devenu l'onglet Matériaux (#110). »
>
> **T9** — « La couche mixte : Oui, par « lier à la ligne du dessous », sans case « à côté » ni ligne double. »
>
> **T10** — « La coupe : Lisible et cliquable, à droite, avec le choix coupe ou contributions, et agrandie dans une fenêtre qui suit sa largeur. »
>
> **T11** — « Ce qui pèse : Les contributions en trois listes : g_k seul, a_k seul, les deux. »
>
> **T12** — « La valeur retenue et l'état : L'état du calcul. La valeur retenue se calcule toute seule, au dixième au-dessus de la somme, et peut s'écrire. »
>
> **T13** — « Les modèles de composition : Tirés du livre Lignum « Holzbau mit System » : paroi, plancher, toiture, ossature, lamellé-croisé… »
>
> **T14** — « Toutes les compositions : Une vue d'ensemble. »
>
> **T15** — « La disposition : A, avec un centre plus compact, entre A et C, sans perdre d'option. »
>
> **T16** — « Le matériau et son rôle : Séparés : le rôle (« Ebene ») est une liste à part, facultative. »
>
> **T17** — « Les noms : Dans la langue de la fenêtre, fr, de, en. Le nom du fabricant d'un produit est gardé. »
>
> **T18** — « L'isolation entre les chevrons : Elle peut être plus mince que les chevrons ; elle est dessinée depuis le bas, avec de l'air au-dessus. »
>
> **T19** — « Une charge remplacée : À la main ou par une variable ; orange dans Woodcore, rien dans l'export. »
>
> **T20** — « Le volet droit : Dans cet ordre : les avertissements, les options de la ligne, la coupe ou les contributions, et les résultats en bas, sur une ligne, sans pastilles. »
>
> Deuxième tour (23.10.2026) :
>
> **T21** — « Un onglet **Matériaux** à part, en bas de la navigation (#110). L'onglet Poids propre **n'en crée plus**. »
>
> **T22** — « **Le dessin est à l'échelle** : 1 m de large, à la même échelle que la hauteur. »
>
> **T23** — « **Échap**, ou un clic dans le vide du centre, ferme la ligne sans quitter la composition. »
>
> **T24** — « **La vue d'ensemble** doit se trouver. »
>
> **T25** — « **La recherche** trouve aussi par catégorie. »
>
> **T26** — « **Un clic sur une ligne** sélectionne tout le nom du matériau. »
>
> **T27** — « **Le volet droit ne propose pas « charge saisie »** comme pose. »
>
> **T28** — « **Le clavier** : Tab va du matériau à l'épaisseur, l'entraxe, la largeur, g/a (↑ ↓), puis aux kN/m². Les kN/m² se remplacent ; la valeur remplacée est orange, et l'avertissement, avec son bouton « Rétablir », est en haut à droite. »
>
> **T29** — « **« Lier » sur la dernière ligne** crée la ligne suivante, le curseur dans son matériau. »
>
> **T30** — « **La ligne liée a « Remplir »**, coché par défaut : sur 1 m, elle remplit le vide autour des pièces. Décochée, on écrit sa largeur. »
>
> **T31** — « **Le mode Affichage** manquait. »
>
> Troisième tour (24.10.2026) — « tout est validé, et **la réponse 1 à chacune des six questions** » :
>
> **T32** — « 1. Les compositions d'aujourd'hui, écrites avec `beside` (pleine largeur) : Elles se lisent avec « Remplir » **décoché** et une largeur de **1000 mm** : leur somme ne change pas. »
>
> **T33** — « 2. Les types de pose : **Continue, à entraxe, par surface, plus la charge saisie** au centre. Ni « ponctuelle », ni « élément du fabricant ». »
>
> **T34** — « 3. Le lattis compté deux fois sous des tuiles « lattis compris » : **Un avertissement, sans rien changer.** »
>
> **T35** — « 4. La coupe imprimée dans le rapport : **La même que dans la fenêtre**, à sa vraie proportion. »
>
> **T36** — « 5. Une somme qui tombe juste sur un dixième (0,900) : **Retenir 0,9** : le dixième supérieur **ou égal**. »
>
> **T37** — « 6. Les lignes liées : **Autant qu'il faut** sur un niveau ; la plus épaisse donne la hauteur, et les lignes qui remplissent partagent la largeur restante. »
>
> Le calcul :
>
> **T38** — « Une composition a ses couches de haut en bas, chacune g_k (Eigenlast) ou a_k (Auflast). Le poids γ d'un matériau vient de la bibliothèque (kN/m³ ou kN/m²). »
>
> **T39** — Les poses : « **Continue** — panneau, chape, isolation pleine — γ · t ; **À entraxe** — lattes, chevrons, solives : des pièces de largeur b toutes les e — γ · t · b / e ; **Par surface** — tuiles, lés, tôles : un poids par m² déjà connu (SIA 261, tableau 29) — γ [kN/m²] ; l'épaisseur ne sert qu'au dessin ; **Charge saisie** — installations, cloisons : sans matériau — la valeur tapée. »
>
> **T40** — « **Le choix d'un matériau en kN/m²** met la ligne « par surface » ; un matériau en kN/m³ sur une ligne « par surface » la remet « continue ». **La charge saisie** ne se crée qu'au centre, par « + Charge saisie », jamais par le choix de la pose à droite. »
>
> **T41** — Les lignes liées : « « Lier à la ligne du dessous » met deux lignes, ou plus (réponse 6), **au même niveau**. La plus épaisse donne la hauteur du niveau. **Une ligne continue liée à des lignes à entraxe remplit**, par défaut, la largeur que laissent les pièces sur 1 m : w = 1000 · (1 − Σ b/e) mm. Deux carrelets de 100 tous les 500 laissent 800 mm. Son poids est γ · t · w / 1000. **« Remplir » décoché** : on écrit sa largeur w sur 1 m ; vide, 1000 mm. **Exemple, AU-01** : la laine de roche entre les chevrons 60/200 e = 625 passe de 0,076 à 0,069 kN/m². La somme passe de 0,916 à 0,909 kN/m². La valeur retenue reste 1,0. »
>
> **T42** — La valeur retenue : « **Sans saisie**, elle est **le dixième supérieur ou égal à la somme** (réponse 5) : 0,909 → 1,0 ; 0,900 → 0,9. Elle s'écrit avec une décimale (« 1,0 », pas « 1 »). **Écrite à la main, ou liée à une variable en kN/m²**, elle est orange, avec un avertissement et « Rétablir ». **Plus basse que la somme**, elle est rouge et l'export s'arrête, comme aujourd'hui. »
>
> **T43** — Une charge de couche remplacée : « la cellule kN/m² d'une ligne s'écrit à la main, ou se lie à une variable du projet en kN/m² ; la valeur remplacée remplace le calcul de la couche dans la somme ; elle est **orange au centre**, avec un avertissement orange et « Rétablir » ; **l'export et le rapport impriment la valeur sans marque**. Les variables offertes sont celles du projet en kN/m² et la valeur retenue des autres compositions. Une composition qui reviendrait à elle-même par ses variables est refusée. L'épaisseur, la largeur et l'entraxe se lient aussi à une variable. »
>
> Vue Calcul — la liste :
>
> **T44** — « **Les compositions**, puis les archives, comme les autres onglets de calcul. »
>
> **T45** — « **« ⊞ Vue d'ensemble »**, en tête de la liste, et montrée quand aucune composition n'est ouverte. C'est un tableau de toutes les compositions : une petite coupe ; l'identifiant et le nom ; le nombre de couches ; g_k, a_k et g_k + a_k ; la valeur retenue, en gras, orange si elle est remplacée ; l'état, « complète » ou « n à corriger ». À droite, les avertissements rouges de toutes les compositions, chacun avec son identifiant. »
>
> **T46** — « **« Nouveau… »** ouvre le choix d'un modèle : « Modèles Lignum », « Mes modèles », « Composition vide ». »
>
> Vue Calcul — le tableau des couches :
>
> **T47** — « **Une ligne par couche**, compacte (environ 25 px), avec ces colonnes : n°, Matériau, Ép. [mm], Entraxe [mm], Largeur [mm], g/a, kN/m². »
>
> **T48** — « **Le matériau se tape dans sa cellule** : la liste propose les matériaux de la bibliothèque (#110) au fur et à mesure ; elle cherche par nom et par catégorie, en fr, de et en : « isolation », « étanchéité », « béton », « acier », « bois » listent toute la catégorie, **en tête** ; chaque proposition dit sa catégorie, son poids et sa source (SIA 261, Externe, Personnel) ; ↑ ↓ parcourent la liste ; **Entrée ou Tab** choisissent et passent à l'épaisseur. Un nom inconnu reste écrit et l'avertissement le dit. »
>
> **T49** — « **Un clic sur une ligne** l'ouvre (ses options à droite) et **sélectionne tout le nom du matériau** : ce qu'on tape le remplace. Un second clic la ferme. »
>
> **T50** — « **Tab** va du matériau à l'épaisseur, l'entraxe, la largeur, g/a, puis les kN/m². Une cellule qui ne sert pas à la pose de la ligne est grisée, et Tab la saute. Après la dernière cellule, Tab va au matériau de la ligne suivante. **g/a** bascule avec ↑, ↓ ou Espace. **Entrée** dans une cellule de nombre la valide. »
>
> **T51** — « **La largeur calculée d'une ligne qui remplit** s'écrit en italique dans sa colonne ; décochée, la cellule s'écrit. **Les kN/m²** se remplacent dans leur cellule. **Échap, ou un clic dans le vide du centre**, ferme la ligne. »
>
> **T52** — « **Sous le tableau** : « + Couche », « + Charge saisie », et la somme. **Aucun matériau ne se crée ici.** Un lien « Les matériaux se créent dans l'onglet Matériaux » ouvre l'onglet Matériaux. **« Lier à la ligne du dessous » sur la dernière ligne** crée la ligne suivante, le curseur dans son matériau. »
>
> Vue Calcul — le volet droit, dans cet ordre :
>
> **T53** — « 1. **Avertissements**. Un clic sur l'un mène à sa ligne. **Rouge** : choisissez un matériau ; « … » n'est dans aucune bibliothèque ; … pèse 0 dans la bibliothèque ; il manque l'épaisseur ; il manque la largeur ou l'entraxe ; la valeur retenue est inférieure à la somme : l'export s'arrête. **Orange**, chacun avec « Rétablir » s'il s'agit d'une valeur remplacée : charge remplacée, v kN/m² au lieu de c ; valeur retenue remplacée, v kN/m² (au dixième supérieur : c) ; une ligne qui remplit, plus épaisse que les pièces auxquelles elle est liée ; **les tuiles comprennent déjà leur lattis** (SIA 261, tableau 29), **et la couche k le compte une seconde fois** (+d kN/m², du côté de la sécurité). […] Le prototype marque les tuiles « lattis compris » du tableau 29 (`battens`) et reconnaît la ligne de lattes par son rôle. **Information** : n mm d'air au-dessus d'une ligne qui remplit, plus mince que les pièces ; … vient de votre bibliothèque personnelle, et le projet en garde une copie ; modifié, pas enregistré : le rapport imprime le dernier export. **Vert** : « Toutes les couches ont leur poids. » »
>
> **T54** — « 2. **Couche n**, les options de la ligne ouverte : le matériau : sa carte (catégorie, poids, source, référence), la recherche, les filtres par source (Toutes, SIA 261, Externe, Personnel) et par catégorie, la liste, et le lien vers l'onglet Matériaux ; la pose : continue, à entraxe, par surface, avec leur pictogramme ; l'épaisseur, la largeur et l'entraxe, selon la pose, chacun avec son bouton de variable ; « Remplir » et la largeur sur 1 m, pour une ligne qui remplit ; compte en g_k | a_k ; le rôle, une liste facultative : structure, isolation, couverture, sous-toiture, contre-lattes, lattes de toiture, lattage, lambris, pare-vapeur, étanchéité, couche de protection, lestage, chape, isolation phonique, revêtement de sol, panneau de contreventement, revêtement intérieur, façade, lé de façade, lé de sous-toiture ; « Lier à la ligne du dessous : même niveau » ; la charge de la couche : sa valeur, sa formule en nombres (par exemple « 5 kN/m³ × 0,2 m × 60/625 = 0,096 kN/m² »), et « Remplacer », à la main ou par une variable. »
>
> **T55** — « 3. **Coupe | Contributions**, avec ⤢ : **La coupe à sa vraie proportion** : 1 m de large, coté « 1000 » sous le dessin, et les hauteurs à la même échelle. AU-01 (311,5 mm) est trois fois plus large que haut. Le plancher de 7 unités par bande disparaît (`dead_load_svg.MIN_BAND`). Une couche sans épaisseur (tuiles en kN/m², lés) reste visible par un trait. Les pièces sont à leur entraxe vrai, et une ligne qui remplit est dessinée entre elles, depuis le bas, avec l'air au-dessus. Chaque bande est découpée à sa largeur : rien ne déborde. Les noms sont dans une colonne à droite, un par ligne, reliés à leur couche par un trait ; comme le dessin est bas, les traits s'ouvrent en éventail. Un nom trop long est coupé par « … », le nom entier au survol. Les cotes de gauche ne s'écrivent que là où elles tiennent ; l'épaisseur est aussi dans le nom. **Sous 560 px de large, le mode légende** : un numéro à côté de chaque couche, et les noms en liste sous le dessin. **Un clic sur une couche l'ouvre.** **Les contributions** : trois listes, g_k seul, a_k seul, g_k + a_k, chaque couche avec sa part. **⤢ ouvre une fenêtre** que l'on tire par son coin : le dessin se refait à sa largeur, à chaque redimensionnement, en gardant sa proportion. On y a aussi Coupe | Contributions. »
>
> **T56** — « 4. **Résultats**, en bas, sur une ligne, sans pastilles : g_k, a_k, g_k + a_k, et la valeur retenue dans sa cellule (écrite, ou liée par x à une variable) avec « au dixième supérieur » quand elle n'est pas écrite. »
>
> Les modèles :
>
> **T57** — « **« Modèles Lignum »** : huit modèles tirés de Lignum, *Holzbau mit System* (2023), chacun avec sa référence dans le livre. Le livre ne donne pas toujours les entraxes ; le modèle dit ce qu'il suppose. Quand le livre donne le poids total, il est montré à côté du calcul, comme contrôle » — tableau : toiture inclinée isolée entre chevrons (C4 tab. 6) ; isolée sur chevrons (C4 tab. 10) ; toit plat compact sur bois massif (C5 tab. 13, « verre cellulaire 200 (matériau personnel), bois massif 100 mm ») ; paroi à ossature, façade ventilée (A2 fig. 24) ; paroi CLT isolation crépie (A2 fig. 24) ; plancher à solives, sable entre lattes (C7 fig. 13 ex. 2 p. 415 ; « 127 kg/m² (calcul : 1,258 kN/m² avec le sable qui remplit, 1,333 sur toute la largeur) ») ; plancher à solives, chape ciment (C7 fig. 11 ex. 2 p. 415 ; « 150 kg/m² (calcul : 1,475 kN/m²) ») ; plancher caisson, gravillon entre nervures (A2 fig. 19).
>
> **T58** — « Chaque carte montre une petite coupe, le nombre de couches, la somme en kN/m² et en kg/m², la référence, les hypothèses et le poids du livre. « Créer depuis ce modèle » copie le modèle dans le projet. **« Mes modèles »** : une composition enregistrée comme modèle vient ici, sur cet ordinateur. **« Composition vide ».** »
>
> La bibliothèque vue de cet onglet :
>
> **T59** — « **Une seule liste**, celle de l'onglet Matériaux (#110), avec trois sources écrites sur chaque matériau : SIA 261 […] Externe […] **fusionné par nom et par poids** […] Personnel […]. **Chaque matériau a une catégorie** […]. **Le gravillon du tableau 29** (0,20 kN/m² par 10 mm) devient 20 kN/m³. »
>
> Vue Affichage :
>
> **T60** — « Le bouton **Calcul | Affichage** est au-dessus de la fenêtre, comme pour la neige et le vent. **Au centre, la page telle que le rapport l'imprime** : niveau 1 : la valeur retenue, en gras ; niveau 2 : g_k, a_k, leur somme et la valeur retenue, ainsi que **la coupe**, la même que dans la fenêtre, à sa vraie proportion (réponse 4) ; niveau 3 : en plus, au-dessus, le tableau des couches (matériau, poids, épaisseur, largeur, entraxe, kN/m²), ses deux totaux et la note « Charge par couche = poids · épaisseur · largeur / entraxe ; une charge par surface sans l'épaisseur ; kg → kN avec g = 10 m/s² ». **Une valeur remplacée s'imprime sans marque.** »
>
> **T61** — « **À droite** : le niveau 1, 2, 3 ; les éléments — le tableau des couches, la figure de la coupe, g_k, a_k et g_k + a_k —, chacun **auto** (il suit le niveau), **toujours** ou **jamais** ; la valeur retenue toujours ; le fichier écrit pour Typst. […] la vue Affichage part de ce fichier et y ajoute ce qui manque (la coupe à l'échelle, les éléments). »
>
> Constats du prototype :
>
> **T62** — « **Le lattis compté deux fois** : la SIA 261 (tableau 29) pèse les tuiles « lattis compris », 0,47 kN/m². Le classeur pèse « Pfannenziegel » 47 kg/m², la même valeur. La composition AU-01 ajoute pourtant ses lattes (+0,018 kN/m²). D'où l'avertissement de la réponse 3. »
>
> **T63** — « **Des défauts de la bibliothèque livrée** : le verre à 5000 kg/m³ (la SIA 261 donne 25 kN/m³ pour les briques de verre pleines) ; le Scobalit à 0 kg/m³ comme façade : l'avertissement rouge « pèse 0 ». À corriger dans `calc/libraries/materials-library.json`, avec leur source. »
>
> **T64** — « **Une couche qui perd son « Ebene » à l'ouverture** : la bibliothèque fusionnée (un matériau, son rôle à part) le rend impossible. »
>
> Ce qui change dans Woodcore :
>
> **T65** — « La source d'une composition […] Une version nouvelle. Par couche : `pose` ; `link` (liée à la ligne **du dessous**) à la place de `beside` ; `fill` (vrai par défaut) et `width` quand il est faux ; `role` ; le matériau par son identifiant dans la bibliothèque (#110) ; la charge remplacée (`override` : une valeur ou une variable). `chosen` vide = automatique. »
>
> **T66** — « La lecture des anciennes sources : `beside` sur la couche i devient `link` sur la couche i − 1, avec `fill: false` et `width: 1000` (réponse 1) : la somme ne change pas, et `tests/test_dead_load_source.py` (« Flachdach », 0,804 kN/m²) reste juste. La pose se déduit de la largeur, de l'entraxe et de l'unité. `library: "direct"` devient la pose « saisie ». »
>
> **T67** — « La coupe : […] Le rapport imprime la même (réponse 4). Le test de la figure (`tests/test_figure_golden.py`) est à refaire. »
>
> **T68** — « Les modèles : `calc/libraries/` (Lignum) ; un dossier de l'utilisateur pour « Mes modèles ». Un modèle est une composition avec sa référence et ses hypothèses. Il est copié dans le projet à la création. »
>
> **T69** — Points à étudier : « **Plusieurs lignes qui remplissent sur un niveau** […] le prototype donne à chacune toute la largeur restante, ce qui la compte deux fois. La spec dit comment elle se partage […] ; **Les deux services** […] et ce que `contracts.Layer` doit porter de plus ; **Le contrat de la source** : sa nouvelle version, la lecture des anciennes […] ; **Les variables** : quelles variables une charge ou une valeur retenue peut suivre (D-06, `links`), et le refus d'une boucle entre compositions ; **La vue Affichage** : […] comment « auto / toujours / jamais » s'y écrit ; **« Mes modèles »** : leur dossier de l'utilisateur […] et leur format ; **#109 (D-33)** : le classeur ne sera plus lu […]. »

## 3. Exigences fonctionnelles

### REQ-001 — La source 2.0 d'une composition
- **Exigence** : `dead-load-source` 2.0 : par couche `pose` (`continuous`, `spaced`, `surface`, `typed`), `material` (l'id du catalogue de #110, absent pour `typed`), `thickness`, `width`, `spacing`, `kind` (gk/ak), `link` (liée à la ligne du dessous), `fill` (défaut vrai) et `width` quand `fill` est faux, `role` (facultatif, une des 20 valeurs de T54), `override` (une valeur kN/m² ou un lien) ; `chosen` vide = automatique. Écrite à 2.0 ; 1.0, 1.1, 1.2 lues.
- **Source** : T65, T33, T16 ; **Priorité** : doit
- **Critère** : test : une source 2.0 valide ; chaque défaut refusé en nommant le champ.

### REQ-002 — La lecture des sources d'avant
- **Exigence** : `beside` sur la couche i devient `link` sur la couche i − 1 avec `fill: false`, `width: 1000` ; la pose se déduit (entraxe si largeur et entraxe, par surface si le poids est en kN/m² ou kg/m², continue sinon) ; `library: "direct"` → `typed` ; `sia261`/`belastungsannahmen`/`project` → l'id du catalogue (`ext_id`, `sia261:`) ; la somme ne change pas.
- **Source** : T32, T66 ; **Priorité** : doit
- **Critère** : `test_dead_load_source` « Flachdach » 0,804 kN/m² inchangé ; chaque composition du projet d'exemple donne la même somme avant et après lecture.

### REQ-003 — Le poids de chaque pose
- **Exigence** : continue γ·t ; à entraxe γ·t·b/e ; par surface γ (l'épaisseur pour le dessin seulement) ; saisie = la valeur ; kg → kN par g = 10 m/s². Un matériau en kN/m² met la ligne « par surface », un matériau en kN/m³ sur une ligne « par surface » la remet « continue ».
- **Source** : T39, T40 ; **Priorité** : doit
- **Critère** : test de la formule « 5 kN/m³ × 0,2 m × 60/625 = 0,096 kN/m² ».

### REQ-004 — Les lignes liées et la largeur qui remplit
- **Exigence** : deux lignes liées par `link` forment un niveau, **jamais plus de deux** (Q-001, l'ingénieur le 24.10.2026, revenant sur « autant qu'il faut ») : une à entraxe et une qui remplit, tout le vide par défaut ; « Lier » est refusé sur une ligne déjà liée, et un niveau de plus de deux lignes lu d'une source est refusé en nommant la couche ; la plus épaisse donne la hauteur ; la ligne `fill` remplit w = 1000·(1 − b/e) mm, son poids γ·t·w/1000 ; `fill` faux : la largeur écrite, 1000 vide. b/e ≥ 1 : largeur 0 et avertissement rouge (déduit).
- **Source** : T30, T37, T41 ; **Priorité** : doit
- **Critère** : des carrelets 100/500 laissent 800 mm ; AU-01 : laine 0,076 → 0,069 kN/m², somme 0,916 → 0,909, largeur 904 mm ; une troisième ligne liée refusée.

### REQ-005 — La valeur retenue automatique
- **Exigence** : sans saisie, le dixième supérieur ou égal à la somme (tolérance flottante : 0,900 donne 0,9), écrite avec une décimale ; écrite ou liée (kN/m²) : orange, « Rétablir » ; sous la somme : rouge, l'export s'arrête.
- **Source** : T12, T36, T42 ; **Priorité** : doit
- **Critère** : 0,909 → 1,0 ; 0,900 → 0,9 ; 0,901 → 1,0 ; une valeur sous la somme refusée à l'export en nommant le fichier.

### REQ-006 — La charge de couche remplacée
- **Exigence** : `override` (valeur ou lien vers une variable du projet en kN/m², ou la valeur retenue d'une autre composition) remplace le calcul de la couche dans la somme ; l'épaisseur, la largeur et l'entraxe se lient aussi ; une composition qui reviendrait à elle-même est refusée ; l'export imprime la valeur sans marque.
- **Source** : T19, T43 ; **Priorité** : doit
- **Critère** : test : override 0,2 → somme changée de (0,2 − c) ; une boucle AU-01 → AU-02 → AU-01 refusée ; le fichier Typst ne porte aucune marque.

### REQ-007 — Les messages
- **Exigence** : `dead_load_source.messages(src)` donne, chacun avec sa ligne (`field`) : rouges (pas de matériau, matériau inconnu, pèse 0, épaisseur manquante, largeur ou entraxe manquant, retenue sous la somme, Σ b/e ≥ 1) ; orange (charge remplacée v au lieu de c, retenue remplacée v (auto c), ligne qui remplit plus épaisse que ses pièces, lattis compté deux fois sous des tuiles « lattis compris » +d kN/m²) ; information (n mm d'air, matériau personnel copié, modifié non enregistré) ; vert quand toutes les couches ont leur poids. Mots fr/de/en (`ld_msg_*`).
- **Source** : T53, T34, T62 ; **Priorité** : doit
- **Critère** : test de chaque message sur une composition qui le provoque ; AU-01 donne l'avertissement du lattis (+0,018 kN/m²) sans changer la somme.

### REQ-008 — Les contributions
- **Exigence** : trois listes, g_k seul, a_k seul, g_k + a_k, chaque couche avec sa part (valeur et %), données par le domaine.
- **Source** : T11, T55 ; **Priorité** : doit
- **Critère** : test : la somme des parts = la somme.

### REQ-009 — La coupe à sa vraie proportion
- **Exigence** : `dead_load_svg` dessine 1 m de large, coté « 1000 », hauteurs à la même échelle, sans `MIN_BAND` ; une couche sans épaisseur par un trait ; pièces à leur entraxe vrai ; ligne qui remplit dessinée entre elles depuis le bas, l'air au-dessus ; bandes découpées à leur largeur ; noms en colonne à droite reliés par des traits en éventail, coupés par « … » (le nom entier en `<title>`) ; cotes seulement où elles tiennent ; sous 560 px de large le mode légende (numéros, noms en liste dessous) ; la largeur donnée par l'appelant. Le rapport imprime la même figure.
- **Source** : T22, T35, T55, T67 ; **Priorité** : doit
- **Critère** : le dessin de AU-01 a un rapport largeur/hauteur de 1000/311,5 (au pixel près) ; `test_figure_golden` refait ; la figure de l'export est celle de l'onglet.

### REQ-010 — Les modèles
- **Exigence** : huit modèles Lignum livrés (`calc/libraries/dead-load-templates.json`), chacun avec ses noms fr/de/en, sa référence, ses hypothèses et le poids du livre (où il le donne) ; « Mes modèles » dans le dossier de l'utilisateur (Q-003) ; « Créer depuis ce modèle » copie dans le projet ; « Enregistrer comme modèle ».
- **Source** : T13, T46, T57, T58, T68 ; **Priorité** : doit
- **Critère** : plancher à solives sable : 1,258 kN/m² (sable qui remplit), 1,333 (pleine largeur) ; chape ciment 1,475 kN/m².

### REQ-011 — La vue d'ensemble
- **Exigence** : le domaine donne, pour chaque composition : id, nom, nombre de couches, g_k, a_k, somme, retenue (et si elle est remplacée), état (complète / n à corriger, Q-010), ses messages rouges.
- **Source** : T14, T24, T45 ; **Priorité** : doit
- **Critère** : test sur le projet d'exemple.

### REQ-012 — Les défauts de la bibliothèque livrée
- **Exigence** : « Glas » (lignes 150, 234 : 5000 kg/m³) porte la valeur de la SIA 261 tableau 28 « Glasbausteine, voll », la valeur du classeur gardée dans `info` (comme l'aluminium, D-05 de 2026-10-12) ; « Scobalit » façade (ligne 235 : 0) porte 500 kg/m³, la valeur de la ligne 151 du même classeur, 0 gardé dans `info` (Q-004).
- **Source** : T63 ; **Priorité** : doit
- **Critère** : `test_dead_load_source` tient le verre égal au fichier de norme.

### REQ-013 — Le fichier du cas et la vue Affichage
- **Exigence** : `Permanent-loads/<id>.typ` imprime au niveau 1 la retenue, au niveau 2 g_k, a_k, la somme, la retenue et la coupe, au niveau 3 en plus le tableau des couches, ses totaux et la note ; chaque élément (tableau, coupe, g_k, a_k, somme) auto / toujours / jamais (Q-002), la retenue toujours ; une valeur remplacée sans marque.
- **Source** : T31, T60, T61 ; **Priorité** : doit
- **Critère** : test du fichier à chaque niveau ; un élément « jamais » absent du PDF compilé.

### REQ-014 — Les matériaux de Lignum dans la bibliothèque livrée
- **Exigence** : les matériaux que nomment les huit modèles Lignum et que la bibliothèque livrée n'a pas (le verre cellulaire du toit plat compact, et les autres que la relecture trouvera) entrent dans les matériaux livrés de Woodcore, origine nouvelle « Lignum » (`lignum:<id>`), chacun avec ses noms fr/de/en, sa catégorie, son poids et sa référence (*Holzbau mit System*, page), relevés sur le livre (`02_Normen und Bibliothek/Normen-Florian/Litteratur/Lignum-HolzbauMitSystem.pdf`), jamais de mémoire ; le livre n'est pas livré avec Woodcore (il n'est pas une norme de `norm-library/`) : la source montre la référence et la page.
- **Source** : T57, Q-005 (l'ingénieur, 24.10.2026 : « ajouter les matériaux de Lignum à la bibliothèque de base de Woodcore ») ; **Priorité** : doit
- **Critère** : test : chaque matériau d'un modèle Lignum est un matériau livré ; le toit plat compact se calcule sans matériau personnel ; chaque `lignum:` a sa page.

## 4. Exigences d'interface

### UI-001 — Le tableau des couches au clavier (service)
- **Exigence** : une ligne compacte (22–28 px) par couche, colonnes n°, Matériau, Ép., Entraxe, Largeur, g/a, kN/m² ; le matériau tapé dans sa cellule avec une liste de propositions (domaine : nom, catégorie en tête, trois langues), chaque proposition avec catégorie, poids, source ; ↑ ↓ parcourent, Entrée ou Tab choisissent et passent à l'épaisseur ; un nom inconnu reste écrit ; un clic ouvre la ligne et sélectionne tout le nom, un second la ferme ; Tab dans l'ordre de T50, les cellules inutiles grisées et sautées, après la dernière le matériau de la ligne suivante ; g/a par ↑ ↓ Espace ; Entrée valide un nombre ; la largeur calculée en italique ; kN/m² remplaçable, orange ; Échap ou un clic dans le vide ferme la ligne ; sous le tableau « + Couche », « + Charge saisie », la somme, le lien vers l'onglet Matériaux ; « Lier » sur la dernière ligne crée la suivante, le curseur dans son matériau.
- **Source** : T7, T23, T26, T28, T29, T47–T52 ; **Langues** : fr/de/en
- **Critère** : test du clavier : Tab de bout en bout sur une ligne à entraxe et une ligne par surface ; la recherche « isolation » met la catégorie en tête.

### UI-002 — Le volet droit, dans l'ordre
- **Exigence** : 1. avertissements (un clic mène à la ligne, « Rétablir ») ; 2. « Couche n » (carte du matériau, recherche et filtres, pose sans « charge saisie », épaisseur/largeur/entraxe avec bouton de variable, Remplir, g_k|a_k, rôle, Lier, la charge et sa formule, Remplacer) ; 3. Coupe | Contributions avec ⤢ (fenêtre qui suit sa largeur) ; 4. résultats sur une ligne, sans pastilles, la retenue dans sa cellule.
- **Source** : T10, T20, T27, T53–T56 ; **Langues** : fr/de/en
- **Critère** : test : l'ordre des modules ; un clic sur un avertissement ouvre sa ligne.

### UI-003 — La coupe (service)
- **Exigence** : un service qui lit `contracts.Layer` (`NEEDS = ("layers",)`), redessine à sa largeur, mode légende sous 560 px, un clic sur une couche l'ouvre.
- **Source** : T5, T55 ; **Critère** : test : un clic sur une bande ouvre la ligne ; à 500 px les noms sont sous le dessin.

### UI-004 — La liste, la vue d'ensemble, « Nouveau… »
- **Exigence** : « ⊞ Vue d'ensemble » en tête de liste et montrée sans composition ouverte (tableau de REQ-011, petite coupe, avertissements rouges à droite) ; « Nouveau… » : « Modèles Lignum » (cartes : coupe, couches, somme kN/m² et kg/m², référence, hypothèses, poids du livre), « Mes modèles », « Composition vide ».
- **Source** : T44–T46, T57, T58 ; **Langues** : fr/de/en
- **Critère** : test : sans composition ouverte, la vue d'ensemble est montrée ; « Créer depuis ce modèle » crée une composition du projet.

### UI-005 — La vue Affichage
- **Exigence** : le bouton Calcul | Affichage comme neige et vent ; au centre la page par niveau ; à droite le niveau, les éléments auto/toujours/jamais, le fichier écrit.
- **Source** : T31, T60, T61 ; **Critère** : test : changer un élément réécrit sa ligne du fichier.

## 5. Exigences d'architecture

- **ARCH-001** — Le calcul (poses, remplissage, retenue, messages, contributions, vue d'ensemble, modèles) dans `calc/domains/` sans Qt. Source : T4. Critère : import sans PySide6.
- **ARCH-002** — Deux services nouveaux, écrits une fois : le tableau des couches au clavier et la coupe ; `DeadLoadTab` reste une classe de paramètres (`test_tab_overrides`). Source : T4, T5. Critère : `test_tab_services`, `test_tab_overrides`.
- **ARCH-003** — `contracts.Layer` porte en plus : pose, remplissage (largeur calculée), air au-dessus, rôle, numéro. Source : T69. Critère : `dead_load_svg` ne lit que `Layer`.
- **ARCH-004** — `dead-load-source` 2.0, lecture de 1.0 à 1.2 (D-05 proposée). Source : T65, T66.
- **ARCH-005** — Les liens (`links`, D-06) pour l'override, l'épaisseur, la largeur, l'entraxe et la retenue ; la boucle refusée par le contrôle existant (`links.LOADS`). Source : T43, T69.

## 6. Contraintes

- **CON-001** — Les compositions existantes donnent la même somme (réponse 1). Source : T32, T66.
- **CON-002** — Les mots en fr/de/en (`test_i18n`). Source : T17 (inféré).
- **CON-003** — Aucun matériau ne se crée dans cet onglet. Source : T3, T21, T52.
- **CON-004** — Le classeur n'est pas lu (#109) : les modèles et la bibliothèque viennent de `calc/libraries/`. Source : T69.

## 7. Décisions prises

- **D-01** — v3 validée entière, les six « réponse 1 » (T32–T37), ingénieur 24.10.2026.
- **D-02** — Disposition A, centre compact (T15).
- **D-03** — Les matériaux et leur liste unique sont faits par #110 (T8, T21, T25, T59, T64 : réalisés dans a9cae26 ; le rôle séparé du matériau le rend durable).
- **D-04** — Ordre : #110 d'abord (fait), puis #111 (Q-002 de la spec de #110, 24.10.2026).
- **D-05** *(proposée)* — `dead-load-source` 2.0 : `beside` devient `link` dans l'autre sens, un changement que la 1.x ne peut porter.
- **D-07** — Un niveau porte au plus deux lignes : une à entraxe, une qui remplit (Q-001, 24.10.2026), revenant sur « autant qu'il faut » de la réponse 6.
- **D-08** — « Mes modèles » dans `%APPDATA%\Woodcore\dead-load-templates`, un JSON par modèle (Q-003).
- **D-09** — Le Scobalit de façade à 500 kg/m³, la valeur de la ligne 151 (Q-004).
- **D-10** — Les matériaux de Lignum entrent dans la bibliothèque livrée, origine « Lignum », relevés sur le livre (Q-005).
- **D-06** *(proposée)* — Le verre corrigé à la valeur de la SIA 261 tableau 28 « Glasbausteine, voll », la valeur du classeur gardée dans `info`.

## 8. Hors périmètre

- Les poses « ponctuelle » et « élément du fabricant » (T33).
- La création d'un matériau dans cet onglet (T3).
- La lecture du classeur de charges (#109).

## 9. Idées non retenues comme exigences

Aucune : l'issue est entièrement validée.

## 10. Questions

### Q-001 — Plusieurs lignes qui remplissent sur un niveau
- **Pourquoi** : le prototype donne à chacune toute la largeur restante (compte deux fois).
- **Exemple** : chevrons 60/625 laissent 904 mm ; laine 0,076 et fibre 0,100 kN/m² à pleine largeur ; prototype 0,159 ; parts égales 0,080.
- **Options** : A (recommandée) le restant partagé à parts égales entre les lignes qui remplissent, une ligne « Remplir » décoché retirant d'abord sa largeur écrite ; B le restant partagé au prorata des épaisseurs ; C chaque ligne remplit tout (le prototype).
- **Réponse** : « il ne peut y avoir que deux matériaux sur une même couche, donc un avec écart et l'autre qui remplit tout par défaut. Il ne doit jamais y en avoir plus de 2, donc pas de soucis » (ingénieur, 24.10.2026). → REQ-004 : deux lignes au plus par niveau.

### Q-002 — Auto / toujours / jamais dans le fichier
- **Options** : A (recommandée) un `level:` par élément dans `Permanent-loads/<id>.typ`, comme les lignes de « Affichage » de la neige (`calc_display.DomainDisplay`), gardé par la réécriture ; B un réglage dans la source.
- **Réponse** : _(à l'approbation)_

### Q-003 — « Mes modèles »
- **Options** : A (recommandée) `%APPDATA%\Woodcore\dead-load-templates`, un fichier JSON par modèle, la forme d'une source 2.0 plus référence et hypothèses ; B dans la bibliothèque des matériaux.
- **Réponse** : **A** (ingénieur, 24.10.2026).

### Q-004 — Le Scobalit de façade (0 kg/m³)
- **Options** : A (recommandée) 500 kg/m³, la valeur de la ligne « Dachhaut » du même classeur (ligne 151), la ligne 235 gardée dans `info` ; B laissé à 0, l'avertissement rouge.
- **Réponse** : **A, 500 kg/m³** (ingénieur, 24.10.2026).

### Q-005 — Le modèle « toit plat compact » et son verre cellulaire « personnel »
- **Options** : A (recommandée) le modèle laisse la couche sans matériau, avec l'hypothèse « verre cellulaire 200 mm, 115 kg/m³ à vérifier » : avertissement rouge « choisissez un matériau » jusqu'au choix ; B le modèle est retiré.
- **Réponse** : « ajouter les matériaux de lignum à la bibliothèque de base de woodcore » (ingénieur, 24.10.2026). → REQ-014.

### Q-006 — Les rôles qui déclenchent l'avertissement du lattis
- **Options** : A (recommandée) « lattes de toiture » et « contre-lattes » sous une couverture « lattis compris » ; B « lattes de toiture » seul.
- **Réponse** : _(à l'approbation)_

### Q-007 — « n à corriger » dans la vue d'ensemble
- **Options** : A (recommandée) le nombre de messages rouges ; B le nombre de lignes en défaut.
- **Réponse** : _(à l'approbation)_

## 11. Critères d'acceptation

- [x] REQ-001 à REQ-014 — leurs critères ci-dessus (REQ-013 : le niveau 1 imprime aussi g_k, a_k et la somme, noté dans `open-questions.md` ; REQ-014 : le Foamglas remplacé, décision de l'ingénieur).
- [x] UI-001 à UI-005 — leurs critères ci-dessus (UI-002 : « Couche n » sans recherche ni filtres propres, résultats pas encore sur une ligne, notés dans `open-questions.md`).
- [x] ARCH-001 à ARCH-007.
- [x] Documentation : `docs/domain/loads.md` §3.3ter, `docs/ui/tab-dead-load.md` (nouveau), `docs/ui/calc-tab.md`, `docs/decisions.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en.
- [x] Tests : `test_dead_load_source`, `test_dead_load`, `test_load_tab`, `test_tab_overrides`, `test_figure_golden`, nouveaux tests du clavier et de la coupe ; catalogue.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1, T2 | §7 D-01 | décision |
| T3 | CON-003 | capturé |
| T4 | ARCH-001, ARCH-002 | capturé |
| T5 | ARCH-002, UI-003 | capturé |
| T6 | REQ-003–REQ-009, UI-001, REQ-010 | capturé (inventaire du prototype) |
| T7 | UI-001 | capturé |
| T8 | D-03 | fait par #110 |
| T9 | REQ-004 | capturé |
| T10 | UI-002, UI-003 | capturé |
| T11 | REQ-008 | capturé |
| T12 | REQ-005 | capturé |
| T13 | REQ-010 | capturé |
| T14 | REQ-011, UI-004 | capturé |
| T15 | D-02 | décision |
| T16 | REQ-001 (rôle) | capturé |
| T17 | CON-002 | capturé |
| T18 | REQ-004, REQ-009 | capturé |
| T19 | REQ-006 | capturé |
| T20 | UI-002 | capturé |
| T21 | D-03, CON-003 | fait par #110 |
| T22 | REQ-009 | capturé |
| T23 | UI-001 | capturé |
| T24 | UI-004 | capturé |
| T25 | UI-001 | capturé (recherche du domaine de #110) |
| T26 | UI-001 | capturé |
| T27 | UI-002 | capturé |
| T28 | UI-001, REQ-006 | capturé |
| T29 | UI-001 | capturé |
| T30 | REQ-004 | capturé |
| T31 | REQ-013, UI-005 | capturé |
| T32 | REQ-002, CON-001 | décision → capturé |
| T33 | REQ-001, REQ-003, §8 | décision → capturé |
| T34 | REQ-007 | décision → capturé |
| T35 | REQ-009 | décision → capturé |
| T36 | REQ-005 | décision → capturé |
| T37 | REQ-004, Q-001 | décision → question (partage) |
| T38, T39, T40 | REQ-003 | capturé |
| T41 | REQ-004 | capturé |
| T42 | REQ-005 | capturé |
| T43 | REQ-006, ARCH-005 | capturé |
| T44, T45, T46 | UI-004, REQ-011 | capturé |
| T47–T52 | UI-001, CON-003 | capturé |
| T53 | REQ-007, UI-002, Q-006 | capturé |
| T54 | UI-002, REQ-001 | capturé |
| T55 | REQ-008, REQ-009, UI-002, UI-003 | capturé |
| T56 | UI-002 | capturé |
| T57, T58 | REQ-010, UI-004, Q-005 | capturé |
| T59 | D-03 | fait par #110 |
| T60, T61 | REQ-013, UI-005, Q-002 | capturé |
| T62 | REQ-007 | capturé |
| T63 | REQ-012, Q-004 | capturé |
| T64 | D-03 | fait par #110 |
| T65 | REQ-001, ARCH-004 | capturé |
| T66 | REQ-002 | capturé |
| T67 | REQ-009 | capturé |
| T68 | REQ-010, Q-003 | capturé |
| T69 | Q-001, Q-002, Q-003, ARCH-003, ARCH-005, CON-004 | questions |

### Points de la source non résolus

Aucun qui bloque : Q-001, Q-003, Q-004, Q-005 répondues le 24.10.2026 ; Q-002, Q-006, Q-007 tranchées par la recommandation, soumises à l'approbation.

## 13. Revue d'architecture

Relecteur `architecture-reviewer`, 24.10.2026 : **APPROUVER AVEC RÉSERVES**, levées ainsi :

| Risque | Gravité | Ce qu'en font la spec et le plan |
|---|---|---|
| P01 — la retenue automatique change l'export et le rapport de chaque composition sans saisie (0,916 imprimé devient 1,0, `gk_ak_gew` toujours présent) | bloquant | Soumis à l'approbation (choix A : appliquer, décision écrite, différences du projet d'exemple listées). Une seule fonction `retained(total)` dans `dead_load.py`. |
| P02 — `override` doublerait `load` + `links.load`, qui existent déjà (1.1) | bloquant | **ARCH-006** : pas de champ `override` ; `load` devient la charge remplaçante de toute pose (et la charge de `typed`), `links.load` son lien ; REQ-001 et REQ-006 lus ainsi. |
| P03 — schéma 2.0 non additif, 1.2 vient d'être livré | bloquant | **ARCH-007** : `dead_load_migrate.upgrade(src)` pur, appelé par `read_source` en mémoire, jamais de réécriture à la lecture ; l'onglet écrit 2.0 ; `materials_migrate` passe par lui ; schéma `enum` 1.0…2.0 ; une ligne `beside` portant largeur et entraxe (deux lignes à entraxe au même niveau, contraire à D-07) est refusée en nommant la couche, le projet d'exemple vérifié d'abord. |
| P04 — `SEVERITIES` sans orange ni vert ; règles rouges en double (export et messages) | important | `SEVERITIES` + `warning`, `ok` ; une fonction `problems(src)` lue par `layer_rows` (qui lève) et par `messages` (qui dit). |
| P05 — « auto/toujours/jamais » existe déjà (`calc_display`, `level` par ligne, figure, tableau) | important | Q-002 = A sans mécanique nouvelle : la coupe en figure `from_level` 2, le tableau au niveau 3 ; les réglages faits à la main dans un `.typ` réécrit sont dits au CHANGELOG. |
| P06 — pas d'état « aucune composition ouverte » | important | Un état explicite `overview` dans le contexte, une entrée « ⊞ Vue d'ensemble » de la liste, `dead_load_overview.overview(here)` pur. |
| P07 — « Nouveau… » et modèles | important | `new_source(cid, template=None)`, `dead_load_templates.py` pur, `calc/libraries/dead-load-templates.json`, `schemas/dead-load-template.schema.json`, « Mes modèles » par `usersettings` comme `materials_dir`, un dialogue `TemplatePicker` d'un service. |
| P08 — le clavier dans un service ; `LayerTable` déjà 264 lignes | important | `layer_table.py` (service), `layer_cells.py` (délégué, filtre d'événements), `next_cell(...)` pur testé sans Qt, `layer_options.py` (volet « Couche n ») ; aucune méthode sur `DeadLoadTab`. |
| P09 — une coupe, un dessin | important | `render(layers, width=None, legend=None)` (None = la largeur de l'export, octets stables) ; `hit_boxes(layers, width)` pur pour le clic ; `Layer` + `pose`, `fill_width`, `air`, `role`, `number` (ARCH-003) ; golden DA-01 refait. |
| P10 — taille de `dead_load_source` | important | Découpe : `dead_load_source`, `dead_load_migrate`, `dead_load_layers`, `dead_load_messages`, `dead_load_overview`, `dead_load_templates`, `dead_load_svg` (+ `dead_load_section`). |
| P11 — le lattis sans drapeau déclaré | important | `includes_battens` dans le fichier de la tab. 29, relu sur le PDF, propagé par `materials_catalogue`, tenu aux groupes « inkl. Lattung » ; `ROLES` une fois dans `dead_load_layers`. |
| P12 — origine « Lignum » d'un livre hors dépôt | important | Soumis à l'approbation (choix A : accepté avec référence + page dans `calc/libraries/`, relevé daté, contrôlé par les poids du livre recalculés). |
| P13 — Glas, Scobalit | mineur | Valeur du verre tenue au fichier de norme par un test ; fusions `ext` vérifiées. |
| P14, P15 | mineur | `fill_width(level)` une fois ; mots fr/de/en, noms des modèles testés à part. |

- **ARCH-006** — Une seule charge remplaçante : `load` + `links.load` (revue P02).
- **ARCH-007** — Un migrateur pur 1.x → 2.0, en mémoire (revue P03).

## 14. Plan d'implémentation

1. **Domaine des couches** : `dead_load_layers.py` (poses, `fill_width`, charge et formule, `retained`, `ROLES`), `contracts` (`Layer` étendu, `SEVERITIES`), `dead_load_migrate.py`, schéma 2.0, `dead_load_source` lisant par le migrateur et écrivant 2.0, `dead_load.instance_from_layers` avec la retenue toujours. REQ-001–006, ARCH-003/006/007. Tests : `test_dead_load_layers`, `test_dead_load_source` (0,804, AU-01, 0,909/0,900/0,901, lecture 1.x).
2. **Messages** : `dead_load_messages.py` (`problems`, `messages`, lattis), `includes_battens` (tab. 29). REQ-007. Tests.
3. **Contributions et vue d'ensemble** : `contributions`, `dead_load_overview.py`. REQ-008, REQ-011.
4. **Bibliothèque** : Glas, Scobalit ; matériaux Lignum relevés sur le livre (`calc/libraries/`, origine `lignum` aux cinq lieux). REQ-012, REQ-014.
5. **Modèles** : `dead-load-templates.json` (8), schéma, `dead_load_templates.py`, « Mes modèles ». REQ-010 (1,258 / 1,333 / 1,475).
6. **Coupe** : `dead_load_svg` à l'échelle, légende, `hit_boxes`, golden. REQ-009.
7. **Affichage** : `from_level`, tableau au niveau 3, fichier régénéré. REQ-013.
8. **Fenêtre** : `layer_cells`, `layer_table`, `layer_options`, service de la coupe et des contributions (⤢), vue d'ensemble, `TemplatePicker`, ordre du volet, mots. UI-001–005.
9. **Docs**, catalogue, CHANGELOG, Nouveautés ; vérification indépendante ; `finish`.

## 15. Vérification

Vérificateur indépendant (`requirements-verifier`), 24.10.2026, sur l'arbre non commité (base a9cae26), tests ciblés verts.

| ID | Verdict | Preuve / reste |
|---|---|---|
| REQ-001 à REQ-005, REQ-007, REQ-008, REQ-010 à REQ-012 | ✅ | `test_dead_load_layers`, `test_dead_load_messages`, `test_dead_load_overview`, `test_dead_load_templates`, `test_dead_load_source` |
| REQ-006, ARCH-005 | ✅ (après correction) | boucle AU-81 → AU-82 → AU-81 refusée et charge remplacée sans marque dans le fichier : `test_load_tab.test_a_build_up_following_another…` ajouté |
| REQ-009 | ✅ (après correction) | rapport 1000/311,5 de AU-01 tenu (`test_the_section_is_drawn_at_its_true_proportion`) |
| REQ-013, UI-005 | ⚠️ | coupe au niveau 2, tableau au niveau 3, un tableau masqué commenté dans le fichier (testé) ; le niveau 1 imprime encore g_k, a_k et la somme (ouvert) |
| REQ-014 | ✅ (décision de l'ingénieur) | le livre ne pèse pas le Foamglas (Tab. 13, p. 389 : λ seul) ; tous les autres matériaux des modèles étaient déjà livrés ; l'ingénieur (24.10.2026) : « remplace alors l'isolation foamglas par une autre isolation de la bibliothèque » → Flumroc prima (ext:59) ; aucune origine `lignum` nécessaire ; `test_every_material_a_template_names_is_shipped_and_every_template_computes` |
| UI-001, UI-003, UI-004, ARCH-001 à ARCH-004, ARCH-006, ARCH-007, CON-001 à CON-004 | ✅ | `test_load_tab` (13), `test_tab_overrides`, `test_tab_services`, `test_i18n` |
| UI-002 | ⚠️ | ordre du volet et clic d'un message testés ; « Couche n » sans recherche ni filtres propres, résultats pas encore sur une ligne (T56) — ouverts |
| Docs | ✅ (après correction) | `docs/ui/tab-dead-load.md` ajouté |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #111 ; 7 questions (Q-001 à Q-007), dont 4 à poser maintenant et 3 à trancher à l'approbation |
| 2026-10-24 | specified | Q-001 (deux lignes au plus par niveau), Q-003 A, Q-004 A, Q-005 (matériaux de Lignum livrés, REQ-014) ; Q-002, Q-006, Q-007 à l'approbation |
| 2026-10-24 | reviewed | revue : approuver avec réserves (P01–P15) ; ARCH-006, ARCH-007 ajoutées ; plan en 9 étapes ; P01 et P12 à l'approbation |
| 2026-10-24 | approved | approuvée ; P01 : retenue automatique partout ; P12 : Lignum accepté avec référence + page ; Q-002 A, Q-006 A, Q-007 A |
| 2026-10-24 | implementation | étape 1 faite : `dead_load_layers`, `dead_load_migrate` (l'Ebene du classeur devient le rôle, `EBENE_ROLES`), `contracts.Layer` étendu, `SEVERITIES` + warning/ok, schéma 1.0–2.0, `dead_load_source` en 2.0 (retenue toujours), `materials.weight_of`, `materials_migrate` par le migrateur, `LayerTable` adapté a minima (pose, lien) ; tests `test_dead_load_layers` (10), `test_dead_load_source`, `test_materials_migrate`, `test_load_tab` verts |
| 2026-10-24 | implementation | étape 2 faite : `dead_load_messages` (`evaluate` une fois, lu par `layer_rows` qui lève et par `messages` qui dit ; rouge, orange, information, vert), `includes_battens` sur les quatre lignes « inkl. Lattung » de la tab. 29 (tenu au titre par `sia261.py`) et sur les tuiles du classeur qui pèsent comme elles (`materials-catalogue.json` `includes_battens`), mots fr/de/en, `calc_modules` lit `warning` et `ok`, clic sur un message → sa ligne ; `test_dead_load_messages` (4) |
| 2026-10-24 | implementation | étape 3 faite : `dead_load_layers.contributions`, `dead_load_overview.overview` (Q-007 A : nombre de messages rouges) ; `test_dead_load_overview` (2) |
| 2026-10-24 | implementation | étape 4 en partie : Glas (lignes 150, 234) à 25 kN/m³ de la SIA 261 tab. 28 « Glasbausteine, voll », Scobalit façade (235) à 500 kg/m³ de la ligne 151, chacun gardant la valeur du classeur dans `info` ; les matériaux de Lignum : **le livre ne pèse pas le verre cellulaire** (Tab. 13, p. 389 : λ seul ; aucun poids non plus dans la SIA 261 ni le classeur) — question à l'ingénieur ; tous les autres matériaux des modèles sont déjà livrés |
| 2026-10-24 | implementation | étape 5 faite (sauf le verre cellulaire) : les huit modèles relus sur le livre (p. 33, 35, 377, 379, 389, 415) — corrections : chape ciment = Abb. **12** ex. 2 (non 11) ; ossature 100/240 e = 625 (part de bois 16 % du livre, non 60/625) ; tab. 10 isolée en **fibre de bois** (Pavatherm, non laine de roche) ; tab. 6 chevrons 100/200 (15 % du livre) ; 1,258 / 1,333 / 1,475 kN/m² tenus ; `dead_load_templates.py`, schéma `dead-load-template`, « Mes modèles » (`usersettings.dead_load_templates_dir`) ; `test_dead_load_templates` (6) |
| 2026-10-24 | implementation | étape 6 faite : `dead_load_svg` réécrit (1 m à l'échelle des hauteurs, sans `MIN_BAND`, pièces à leur entraxe, ligne qui remplit depuis le bas et l'air au-dessus, noms en colonne et traits en éventail coupés par « … », mode légende sous 560, `hit_boxes`), golden DA-01 refait (raison dans `CHANGES`) |
| 2026-10-24 | implementation | étape 7 faite : la coupe `from_level` 2, le tableau `from_level` 3 (`unfold._table_lines` enveloppe ses lignes de `#from-level`) ; g_k, a_k, somme et retenue à tous les niveaux (P05 : sans mécanique nouvelle pour les `#var`) |
| 2026-10-24 | implementation | étape 8 faite : `layer_table` réécrit, `layer_cells` (`next_cell` pur), `layer_options` (« Couche n »), `layer_section` (« Coupe \| Contributions », ⤢), `case_overview` (« ⊞ Vue d'ensemble »), `template_picker` (« Nouveau… ») ; accroches du type : `ctx.pane_modules`, `overview_widget`/`show_overview`, `pick_new`/`new_from`, `calc_tab.before` ; une charge saisie sans valeur dite en rouge (une entrée qui manque avertit) ; mots fr/de/en ; `test_load_tab` (12) |
| 2026-10-24 | testing | étape 9 : docs (`loads.md` §3.3ter, `calc-tab.md`, `layout.md`, `decisions.md` + index, `open-questions.md`, catalogues des tests), CHANGELOG, « Nouveautés » fr/de/en ; reste ouvert : le verre cellulaire (le livre ne le pèse pas), la recherche et les filtres propres à « Couche n », les résultats sur une ligne (T56), le niveau 1 qui imprime aussi g_k, a_k et la somme |
| 2026-10-24 | verification | vérification indépendante : un ❌ (REQ-014, le verre cellulaire), trois ⚠️ déclarés ; corrigé : tests de la boucle, de la charge sans marque, du tableau masqué, du rapport 311,5 ; page `docs/ui/tab-dead-load.md` |
| 2026-10-24 | verification | REQ-014 tranché : le Foamglas du toit plat compact remplacé par Flumroc prima de la bibliothèque (l'ingénieur) ; suite complète verte (3224 passés ; les 4 échecs corrigés et rejoués) |
| 2026-10-24 | completed | critères cochés ; spécification déplacée dans `completed/` |
