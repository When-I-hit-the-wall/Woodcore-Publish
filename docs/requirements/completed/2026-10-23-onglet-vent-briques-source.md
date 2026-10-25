# Onglet Vent repensé — la source numérotée de la spécification

> La source de [`2026-10-23-onglet-vent-briques.md`](2026-10-23-onglet-vent-briques.md), mot pour mot, découpée en points `T1`… : l'issue #100, les messages de l'ingénieur et ses réponses du 23.10.2026. Mise à part pour que la spécification reste sous le seuil de 100 Ko des fichiers de `docs/` ; elle ne change plus.

## 2. Source

Les parties A à F sont numérotées dans l'ordre. La partie D est l'analyse que Claude a rendue à l'ingénieur (propositions, pas décisions de l'ingénieur) ; la partie E contient les réponses de l'ingénieur ; la partie F est une vérification dans le code.

### Partie A — issue #100

> **T1** — « L'ingénieur a revu l'ergonomie de l'onglet Vent (SIA 261:2020, chapitre 6 et annexes C et E) sur des prototypes HTML, en cinq tours, le 22 et le 23.10.2026. La cinquième version l'a satisfait. Ce qui suit est ce qu'il a retenu. »
>
> **T2** — « Le prototype final sert de référence, mais **cette issue l'emporte là où les deux diffèrent**. »
>
> **T3** — « L'onglet a deux vues, comme la neige (#94) : »
>
> **T4** — « **Calcul** : le formulaire en quatre sections, la norme au survol, le modèle 3D du bâtiment et le volet droit fait de modules ; »
>
> **T5** — « **Affichage** : le fichier `.typ` du cas compilé, et le réglage de chacun de ses éléments. »
>
> **T6** — « L'onglet Vent est le **deuxième onglet de calcul** après la neige. Il doit être bâti **sur les types d'onglets et les briques de fonctionnalités de l'issue #95**, en cours d'implémentation. Il ne recopie aucun widget de l'onglet Neige et n'écrit pas sa propre version d'une brique. »
>
> **T7** — « **Avant de commencer**, lire où en est #95 : ses briques, son contrat déclaratif, son guide « construire un onglet ». Le vent s'appuie sur ce qui y a été finalement écrit, pas sur ce que cette issue en imagine. »
>
> **T8** — « **Si une brique manque** ou ne suffit pas au vent, on la complète dans la brique elle-même, avec son test, pour tous les onglets. On ne fait pas de version locale. Un manque de #95 qui bloque se signale dans #95. »
>
> **T9** — « la liste des cas (dossiers, archives, identité Nom · Description · ID) ; » (brique utilisée par le vent)
>
> **T10** — « le formulaire déclaratif en sections, avec ses genres de champs ; » (brique utilisée par le vent)
>
> **T11** — « la bulle de la norme : survol, clic qui épingle, un second clic qui retire (#96), Ctrl+clic au chapitre ; » (brique utilisée par le vent)
>
> **T12** — « le lecteur PDF de Woodcore et la carte externe 261.sia.ch ; » (brique utilisée par le vent)
>
> **T13** — « le volet de modules : état du calcul, résultats, extraits épinglés, dessins ; glisser-déposer, réduire, fenêtre ; » (brique utilisée par le vent)
>
> **T14** — « les survols liés ; » (brique utilisée par le vent)
>
> **T15** — « la vue Affichage d'un fichier `.typ` élément par élément. » (brique utilisée par le vent)
>
> **T16** — « **Ce qui est propre au vent**, dans `calc/domains/` et `calc/norms/`, sans Qt : le calcul ; les 37 bâtiments de l'annexe C, avec leur géométrie ; le modèle 3D et ses vues ; les tableaux de coefficients colorés ; le détail par φ ; le choix des ouvertures ; le générateur du fichier. »
>
> **T17** — « **Ce qui est propre au vent et devra être réutilisable** : le widget du modèle 3D (rotation, zoom, faces cachées, surfaces lumineuses). Le séisme ou les charges permanentes pourraient en avoir besoin. Il devient lui aussi une brique, à proposer dans #95. »
>
> **T18** — « **Copie complète dans le dépôt**, au commit `8e88677` de la branche `ccr-ce2d3d0c-6gi9hg` (non fusionnée) : `docs/requirements/prototypes/2026-10-23-onglet-vent/`. »
>
> **T19** — « Ouvrir `index.html` dans un navigateur, depuis ce dossier : il ne demande ni serveur ni réseau. Le README dit ce qu'est chaque fichier. »
>
> **T20** — « Pour reprendre le dossier dans la branche de travail : `git checkout 8e88677 -- docs/requirements/prototypes/2026-10-23-onglet-vent`. »
>
> **T21** — « `N` : l'emplacement de chaque extrait de la SIA 261:2020 en FR et en DE (page et rectangle en points PDF) et son texte mot pour mot. Cela couvre 6.2.1.1 à 6.3.5, le tableau 4, les figures 9 et 22, l'annexe E et les tableaux 31 à 64. »
>
> **T22** — « `FIELD_NORM` : quel champ montre quelle clause. »
>
> **T23** — « `compute()` : le calcul complet, décrit plus bas. »
>
> **T24** — « `DRAWN` : la géométrie relevée des six bâtiments déjà dessinés, les tableaux 31, 32, 36, 40, 59a et 59b. On y trouve la forme du toit, la pente, les proportions h : b : d du dessin et la place des surfaces m, n, o. »
>
> **T25** — « `model3d`, `project`, `view3d` : le modèle 3D, sa projection et son dessin. »
>
> **T26** — « `loadsAt`, `forcesAt` : ce que montrent les Résultats 3D. »
>
> **T27** — « Les mots de la fenêtre en fr, de et en. » (T21 à T27 : ce que le script de `index.html` contient, « à reprendre dans l'implémentation (en Python, sans Qt, pour ce qui est du domaine) »)
>
> **T28** — « **Les versions successives**, artefacts claude.ai du compte de l'ingénieur. Une session Claude du même compte les lit avec l'outil Artifact, `action: "read"` : [...] [Vent, cinquième version] : la version retenue, celle copiée dans le dépôt. »
>
> **T29** — « **q<sub>p</sub>** est pris au point le plus haut et reste constant sur la hauteur (6.2.2.3). Par défaut z = h, avec une case pour saisir un autre z. »
>
> **T30** — « c<sub>h</sub> = 1,6·[(z/z<sub>g</sub>)<sup>α<sub>r</sub></sup> + 0,375]². »
>
> **T31** — « z vaut au moins 5 m, et 10 m en catégorie IV. Au-dessus de 30 m, la catégorie IV prend le profil de la catégorie III (6.2.1.2). »
>
> **T32** — « **Forces globales** (15) : Q<sub>k</sub> = c<sub>red</sub> · c<sub>d</sub> · c<sub>f</sub> · q<sub>p</sub> · A<sub>ref</sub>. »
>
> **T33** — « c<sub>red</sub> vient de la figure 9, pour b·h et pour d·h. Chacun vaut pour les directions à moins de 15° de la sienne ; pour les autres directions, on prend le plus défavorable des deux (6.3.3). Pour la toiture, c<sub>red</sub> = 1,0 (6.3.2). »
>
> **T34** — « Q<sub>1</sub> agit sur A (b·h), Q<sub>2</sub> sur C (d·h), Q<sub>3</sub> verticalement sur d·b (figure 22). »
>
> **T35** — « Le facteur des en-têtes (0,71·d·h…) fait partie de A<sub>ref</sub>. »
>
> **T36** — « **Pressions locales** : q<sub>k</sub> = q<sub>p</sub> · (c<sub>d</sub> · c<sub>pe</sub> − c<sub>pi</sub>), selon (13), (14), (17) et (18). »
>
> **T37** — « Une pression est positive, vers la surface ; une succion est négative (6.2.2.5, figure 7). »
>
> **T38** — « c<sub>red</sub> ne s'y applique pas (6.3.1). »
>
> **T39** — « Une valeur ±0,1 compte ses deux signes. »
>
> **T40** — « **Pour chaque surface, on garde la plus grande pression et la plus grande succion sur les directions du tableau**, avec la direction φ, le c<sub>pe</sub> et le c<sub>pi</sub> qui les ont données : la fenêtre et le rapport disent d'où vient chaque nombre. »
>
> **T41** — « **Les ouvertures** : le cas choisi dans l'onglet (réparties de façon homogène, ou une ouverture dominante A, B, C ou D) donne la colonne c<sub>pi</sub> du tableau. »
>
> **T42** — « **Les surfaces localisées m, n, o** (figure 22) : « Les forces agissant sur elles ne doivent pas être superposées aux forces agissant sur les grandes surfaces. » Elles sont montrées à part. »
>
> **T43** — « **ĉ<sub>pe</sub>** sert aux pressions de courte durée sur les zones sensibles (vitres, tuiles et leur fixation). Une note donne ĉ<sub>pe</sub> · q<sub>p</sub>. »
>
> **T44** — « **Messages** (le module État du calcul) : »
>
> **T45** — « en **rouge**, ce qui empêche le calcul : ID manquant, q<sub>p0</sub> manquant ou nul, b, d ou h ≤ 0, h > 200 m (6.1.2), z ≤ 0, aucun bâtiment choisi ; »
>
> **T46** — « en **orange**, ce qui informe, et le calcul se fait : z relevé à la valeur minimale de la norme (6.2.1.2) ; la catégorie IV au-dessus de 30 m ; c<sub>d</sub> = 1,0 hors des cas de 6.3.5 ; β hors de la figure 9 (c<sub>red</sub> lu au bout de la courbe) ; les proportions h : b : d saisies, plus de 1,5 fois loin de celles du tableau (décision de l'ingénieur) ; c<sub>f1</sub> marqué « * », force à calculer directement ; les surfaces de référence à cotes du tableau (h₁, d₁…), q<sub>k</sub> par m² seulement ; »
>
> **T47** — « en **vert**, ✓ « Toutes les entrées sont là, le calcul est fait. ». »
>
> **T48** — « Un clic sur un message mène au champ, qui clignote. »
>
> **T49** — « **Les standards de la neige** (#94) sont tous repris : »
>
> **T50** — « **la bulle** : le texte de la norme mot pour mot d'abord, l'image de l'extrait dessous, sans onglets, placée là où elle ne couvre rien ; »
>
> **T51** — « **le clic** épingle l'extrait sous le module Résultats, et un second clic le retire (#96) ; »
>
> **T52** — « **le Ctrl+clic** ouvre toute la partie de la norme dans le lecteur PDF de Woodcore, à la page, la clause encadrée : le chapitre 6 (FR p. 30–35, DE p. 29–34), ou l'annexe C (p. 81–114) pour un tableau ou une figure de bâtiment ; »
>
> **T53** — « **la langue** de la norme suit la fenêtre ; à défaut, c'est l'allemand ; »
>
> **T54** — « **la carte de l'annexe E** s'ouvre sur `https://261.sia.ch/?lang=fr&layer=wind`, avec `lang=de` quand la fenêtre est en allemand ou en anglais. »
>
> **T55** — « **Le formulaire, en quatre sections** » (données de base ; bâtiment (annexe C) ; coefficients de réduction et de force ; coefficients de pression, dans cet ordre)
>
> **T56** — « **Données de base** : q<sub>p0</sub>, la catégorie de terrain, b · d · h, z (« z = h » coché par défaut), c<sub>d</sub>. »
>
> **T57** — « **Bâtiment (annexe C)** : le choix du tableau ; »
>
> **T58** — « au-dessus de l'image, le tableau, son titre, h : b : d du tableau, la toiture et les proportions saisies. Il n'y a plus de ĉ<sub>pe</sub>, de c<sub>fr</sub>, ni d'étiquettes « Q₁ sur A (b·h)… » ; »
>
> **T59** — « deux vues : **la figure de la norme**, ou **le modèle 3D**. C'est le seul endroit du centre où se trouve le bâtiment. »
>
> **T60** — « **Coefficients de réduction et de force** : les facteurs de réduction (figure 9) avec b·h, d·h, oblique et d·b ; »
>
> **T61** — « les **coefficients de force** du tableau, chaque cellule colorée selon sa valeur ; »
>
> **T62** — « le tableau des **forces globales** Q<sub>k,1–3</sub> en kN, avec c<sub>red</sub> par φ, les extrêmes marqués et A<sub>ref</sub> ; »
>
> **T63** — « la formule (15) ; »
>
> **T64** — « le **Résultat 3D · forces globales**. »
>
> **T65** — « **Coefficients de pression**, dans cet ordre : »
>
> **T66** — « les **coefficients de pression** c<sub>pe</sub> et c<sub>pi</sub> du tableau, colorés, avec la colonne c<sub>pi</sub> des ouvertures choisies marquée, la légende et la note ĉ<sub>pe</sub> ; »
>
> **T67** — « le **détail par φ** : q<sub>k</sub> de chaque surface à chaque direction, coloré. Il est **toujours affiché, sans bouton pour le replier**, sur toute la largeur du volet, avec une largeur minimale puis un défilement horizontal ; »
>
> **T68** — « les **ouvertures**, en liste déroulante sur la ligne du mot, et la formule de q<sub>k</sub> ; »
>
> **T69** — « le **Résultat 3D · charges de surface**. »
>
> **T70** — « Le bâtiment n'est plus dans cette section. Les tableaux Murs, Toiture et Surfaces localisées sont **retirés du centre** : ils sont au volet droit, et le détail par φ donne le reste. »
>
> **T71** — « **Une seule façon de le voir** : un modèle que l'on tourne à la souris. Les vues fixes et la vue « pression par φ » ont été essayées puis écartées. Glisser ne sélectionne aucun texte. »
>
> **T72** — « **Ce qu'il dessine** : le bâtiment du tableau, dans **les proportions du tableau** et non dans celles saisies ; A à H, m, n, o là où la figure du tableau les place ; b, d, h, et h<sub>e</sub> à l'égout pour un toit à deux pans, avec le h du faîte ; α ; Q₁ à Q₃ en noir ; la direction φ en bleu. »
>
> **T73** — « **Les boutons de vue** : Face A, Face C, Iso et Dessus. Face A et Face C regardent exactement de face. »
>
> **T74** — « **Le zoom**, à la molette, ou par − / + et « Ajuster » (100 %) : il va du bâtiment au quart de la largeur du dessin jusqu'à cinq fois sa largeur ; »
>
> **T75** — « il est **toujours centré** sur le bâtiment : on ne peut pas déplacer la vue ; »
>
> **T76** — « **l'échelle ne change pas quand on tourne**. Elle est calculée une fois, sur la sphère qui contient le bâtiment, ses forces et la flèche φ ; l'effet de zoom selon la longueur et la largeur est supprimé. »
>
> **T77** — « **Les faces cachées** : une face vue de côté ou de dos n'est pas dessinée, ni sa lettre, ni les surfaces posées dessus. Une force ou la flèche φ vue dans son axe, et une cote vue de bout, ne le sont pas non plus. »
>
> **T78** — « Exemple : en Face A sur le tableau 32, il ne reste que A, sans E, F, G, H, m, n, sans Q₁ ni φ = 0°. »
>
> **T79** — « **Les surfaces localisées m, n, o** sont posées contre leur face, pas au-dessus. Une surface qui traverse le faîte est coupée en deux, une partie sur chaque versant. »
>
> **T80** — « **Le curseur φ**, de 0° à 360° librement : la flèche tourne autour du bâtiment et le vise toujours, avec un arc depuis la référence φ = 0° ; »
>
> **T81** — « φ = 0° souffle sur A, dans le sens de Q₁ ; φ = 90° souffle sur C, dans le sens de Q₂ ; »
>
> **T82** — « sur une forme ronde, la flèche resterait perpendiculaire à la surface. »
>
> **T83** — « **Les survols** : une surface survolée, dans un tableau ou sur le bâtiment, s'allume et **se voit à travers le bâtiment** sur toute sa longueur, même quand elle est derrière ; »
>
> **T84** — « b·h, d·h et d·b allument leur surface de référence sur le bâtiment, au centre comme dans le module Bâtiment, et rien d'autre. »
>
> **T85** — « Les **37 bâtiments** de l'annexe C sont dessinés avant la mise en service. Six sont relevés dans le prototype ; pour chacun des autres, la géométrie est à relever sur la figure de son tableau. »
>
> **T86** — « Tant qu'un bâtiment n'est pas dessiné, l'onglet montre la figure de la norme. »
>
> **T87** — « **Les Résultats 3D** : deux dessins sur le même modèle, chacun tourné et zoomé à part. »
>
> **T88** — « **Les commandes de chacun** : un bouton par direction du tableau (0°, 15°, 45°, 90°…) et « Max, toutes directions » ; »
>
> **T89** — « max (+) ou min (−) pour les forces, pression max (+) ou succion max (−) pour les charges. »
>
> **T90** — « **Résultat 3D · forces globales**, en section 3 : Q<sub>k,1</sub>, Q<sub>k,2</sub> et Q<sub>k,3</sub> dans leur direction, avec leur valeur en kN. Les flèches sont à l'échelle de la plus grande force. »
>
> **T91** — « **Résultat 3D · charges de surface**, en section 4 : les faces restent neutres, ni rouges ni bleues ; »
>
> **T92** — « sur chaque face vue, sa charge q<sub>k</sub> est un **plan de charge tenu par des flèches, comme dans RFEM**, à l'échelle de la plus grande valeur, avec sa valeur en kN/m² ; »
>
> **T93** — « une valeur qui couvrirait une lettre ou une autre valeur se déplace, avec un trait ; »
>
> **T94** — « les charges de m, n, o sont dessinées **en plus** de celle de leur face : on garde les deux. »
>
> **T95** — « **Les couleurs** : **une pression est rouge**, vers la surface ; **une succion est bleue**, en s'éloignant de la surface. La valeur prend la couleur de sa flèche, et le texte n'est **jamais écrit sur la flèche**. »
>
> **T96** — « **Chaque Résultat 3D s'épingle** au volet droit, sous les résultats, et s'ouvre dans une fenêtre. »
>
> **T97** — « **Dans une fenêtre**, le dessin prend la largeur de la fenêtre et la suit quand on la redimensionne. Les boutons et les notes du dessous passent à la ligne. »
>
> **T98** — « **Le volet droit** — **Les modules** : »
>
> **T99** — « État du calcul ; »
>
> **T100** — « Résultats : pression dynamique c<sub>h</sub>, q<sub>p</sub> et c<sub>red</sub> ; les forces globales Q<sub>k,1–3</sub> max et min avec leur φ ; les tableaux Murs, Toiture et Surfaces localisées, en pression max et succion max q<sub>k</sub> [kN/m²], chacune avec son φ ; »
>
> **T101** — « Bâtiment : la figure de la norme ou le modèle 3D, avec le curseur φ ; »
>
> **T102** — « Figure 9 · c<sub>red</sub>, interactive ; »
>
> **T103** — « les extraits épinglés ; »
>
> **T104** — « les Résultats 3D épinglés. »
>
> **T105** — « **Les colonnes ont des en-têtes** : pression max, succion max, q<sub>k</sub> [kN/m²]. »
>
> **T106** — « **La casse est respectée** : Q, une force en kN ; q, une charge par surface en kN/m² ; jamais « KN/M² ». Aucun titre n'est en capitales. »
>
> **T107** — « **Survols liés**, vrais seulement, dans les deux sens : »
>
> **T108** — « **Le tableau des forces globales** et Q<sub>k,1–3</sub> des résultats s'allument ensemble. »
>
> **T109** — « **Une ligne du volet droit** (A, B…) allume sa surface sur le bâtiment. Elle met aussi en **sur-évidence**, dans le tableau des coefficients, le c<sub>pe</sub> et le c<sub>pi</sub> qui ont donné sa valeur : un cadre orange, par-dessus la colonne c<sub>pi</sub> déjà marquée. »
>
> **T110** — « **Une cellule du détail par φ** allume le c<sub>pe</sub> et le c<sub>pi</sub> qui l'ont donnée. »
>
> **T111** — « **c<sub>red</sub>** (b·h, d·h, d·b) n'allume rien dans les résultats. »
>
> **T112** — « **La couleur de survol** n'est pas le jaune safran, mal lisible : c'est un bleu lisible, en clair comme en sombre. »
>
> **T113** — « Comme pour la neige (#94) : **au centre**, le fichier du cas `Variable-loads/Wind/<id>.typ`, compilé élément par élément, les éléments masqués en pâle, non cliquable, sans cadre bleu, les notes en bas de page ; »
>
> **T114** — « **à droite**, la commande à copier `#include domain-file("wind-load", "WL-01")`, le niveau 1, 2 ou 3 du domaine, puis « Éléments du fichier » avec 0 1 2 3 par ligne et les arguments de `#var`, `#eq` et de la figure. »
>
> **T115** — « **Les tableaux** (forces globales, forces locales) sont des éléments du fichier. On les affiche ou non, avec ou sans leur titre et leur note. **Un tableau n'a pas de niveau.** »
>
> **T116** — « **La figure du fichier est celle de la norme, en 2D** : le dessin du tableau du bâtiment, recadré, avec la légende de Woodcore dessous. Ce n'est pas le modèle 3D. »
>
> **T117** — « Elle n'a pas de niveau. **Woodcore l'écrit dans le fichier quand le domaine est au niveau 3**, et ne l'écrit pas aux niveaux 1 et 2. »
>
> **T118** — « On règle sa largeur, sa légende et son label ; la case « Afficher » garde le choix de l'ingénieur. »
>
> **T119** — « Elle se règle partout de la même façon, pour la neige comme pour le vent. »
>
> **T120** — « **Les Résultats 3D restent dans la fenêtre** : le rapport n'imprime aucun 3D. »
>
> **T121** — « **Les forces globales** sont écrites comme la fenêtre les montre : le tableau en Q<sub>k</sub> [kN], avec les **nombres**. Les lignes q<sub>k</sub> par m² sont gardées. »
>
> **T122** — « **Les forces locales** : seul le **cas d'ouvertures choisi** dans l'onglet est écrit : le fichier ne contient que ce qui calcule ce que la fenêtre affiche ; »
>
> **T123** — « le tableau est **transposé**, large et bas : une colonne par surface, une ligne max et une ligne min. La première colonne a sa largeur propre (`columns: (auto,) + (1fr,) * n`), et la note dit que m, n et o sont des surfaces localisées ; »
>
> **T124** — « **au-delà de douze surfaces**, le tableau est coupé en deux blocs l'un sous l'autre. Sur les 37 tableaux, 9 ont plus de 12 surfaces, et jusqu'à 29 pour le tableau 60a. »
>
> **T125** — « **c<sub>d</sub>** entre dans les pressions locales, selon (17). »
>
> **T126** — « **Le fichier français ne garde aucun mot allemand.** »
>
> **T127** — « [ ] Le tableau des forces globales imprime le **nom des variables** (« qk_max_cf1 ») et non leurs valeurs. » (défaut de la 0.122, visible dans `WL-01.typ` écrit par `unfold._generate_load` pour la halle du tableau 36)
>
> **T128** — « [ ] Une **force est imprimée comme une charge** : q<sub>k</sub> en kN/m², avec le libellé « Force globale du vent ». »
>
> **T129** — « [ ] Le tableau des forces locales écrit **les six cas d'ouvertures** côte à côte (extérieur, réparti, A à D). »
>
> **T130** — « [ ] Il y a **de l'allemand dans le fichier français** : les symboles « Geländekategorie » et « Tabelle », et les clauses « Anhang E », « Anhang C », « Figur 9 ». »
>
> **T131** — « [ ] **c<sub>d</sub> manque** dans les pressions locales : `wind_source.local_pressures(table, qp)` calcule q<sub>p</sub> · (c<sub>pe</sub> − c<sub>pi</sub>). Le nombre est le même tant que c<sub>d</sub> = 1,0, mais (17) demande c<sub>d</sub> · c<sub>pe</sub>. Il faut un test à c<sub>d</sub> ≠ 1. »
>
> **T132** — « [ ] L'onglet bâti sur les types et les briques de #95, sans widget recopié. Une brique qui manque se complète dans #95. »
>
> **T133** — « [ ] Le modèle 3D en brique réutilisable : un module de projection et de dessin sans Qt, et son widget. »
>
> **T134** — « [ ] c<sub>d</sub> dans les pressions locales, avec son test. »
>
> **T135** — « [ ] Pour chaque surface, les extrêmes avec leur φ, leur c<sub>pe</sub> et leur c<sub>pi</sub>, et q<sub>k</sub> par surface et par φ pour le détail. »
>
> **T136** — « [ ] Le choix des ouvertures, enregistré dans la source du cas. »
>
> **T137** — « [ ] Les messages rouges et orange ci-dessus, avec leur champ. »
>
> **T138** — « [ ] La géométrie des 37 bâtiments de l'annexe C, relevée sur la figure de chaque tableau (forme du toit, pente, proportions, place de A à H, m, n, o et des forces). »
>
> **T139** — « [ ] L'emplacement de chaque extrait (page et rectangle par édition) et son texte, à côté des `norm_ref`, depuis la table `N` du prototype. »
>
> **T140** — « [ ] Les quatre sections, dans l'ordre décrit, avec les tableaux de coefficients colorés et le détail par φ toujours affiché. »
>
> **T141** — « [ ] Le modèle 3D : rotation, zoom centré à échelle fixe (¼ à 5 fois la largeur), faces cachées, m, n, o posées et coupées au faîte, curseur φ de 0° à 360°, surfaces vues à travers le bâtiment. »
>
> **T142** — « [ ] Les deux Résultats 3D, avec leurs commandes, leurs couleurs, les plans de charge, l'épingle et la fenêtre qui suit sa largeur. »
>
> **T143** — « [ ] Le volet droit et ses modules, les survols liés et la sur-évidence des c<sub>pe</sub> et c<sub>pi</sub>. »
>
> **T144** — « [ ] Les bulles de la norme, le Ctrl+clic au chapitre 6 ou à l'annexe C, et 261.sia.ch pour l'annexe E. »
>
> **T145** — « [ ] L'aperçu du fichier, avec ses tableaux et sa figure en éléments. »
>
> **T146** — « [ ] Le tableau des forces globales en Q<sub>k</sub> [kN] avec les nombres ; les forces locales du cas choisi seul, transposées, coupées au-delà de douze surfaces. »
>
> **T147** — « [ ] La figure de la norme du tableau, écrite au niveau 3 seulement, avec width, caption, label et « Afficher ». »
>
> **T148** — « [ ] Les mots allemands du fichier français remplacés. »
>
> **T149** — « [ ] Les mots en de, fr et en, et les tests. »
>
> **T150** — « [ ] La documentation : `docs/ui/`, `docs/domain/loads.md`, `docs/decisions.md`, `CHANGELOG.md`, Nouveautés. »
>
> **T151** — « Ce travail est substantiel et multi-modules : il passe par `/big-feature`, avec sa revue d'architecture. »
>
> **T152** — « **#95 d'abord.** La spec part de ce que #95 a écrit, et dit brique par brique ce que le vent prend et ce qu'il y ajoute. »
>
> **T153** — « **Le contrat de données.** Le choix des ouvertures entre dans la source du cas, ce qui fait une nouvelle version de schéma (`schemas/wind-source`). L'export ne donne plus que le cas choisi. »
>
> **T154** — « **La géométrie des bâtiments.** Une table par tableau à côté de `calc/norms/sia261-2020-tabNN-wind.json`, ou une seule table pour les 37 : la spec choisit. Le dessin suit les proportions du tableau, pas les dimensions saisies. »
>
> **T155** — « **Le modèle 3D.** Un module Python sans Qt (par exemple `wind_model3d.py`) projette et rend le SVG : faces vues, ordre, lettres, forces, cotes, plans de charge. Un widget Qt le redessine quand on glisse ou qu'on zoome ; c'est environ 350 lignes de `QPainter`, sans nouvelle dépendance. Le prototype donne la projection (`project`), l'échelle fixe, les limites du zoom et le placement des étiquettes. »
>
> **T156** — « **La figure de la norme dans le rapport.** Elle est découpée dans le PDF de la SIA, comme les extraits des bulles. La décision de la bibliothèque de référence prise pour la neige (#94) s'applique : l'ingénieur autorise sans limite à découper la norme et à l'imprimer. La spec dit comment Woodcore écrit l'image à l'export, et ce qu'il fait quand la bibliothèque des normes manque sur le poste. »
>
> **T157** — « **La figure écrite au niveau 3 seulement.** Le générateur décide au moment où il écrit le fichier, selon le niveau du domaine ; la case « Afficher » garde le choix de l'ingénieur. La spec dit ce que devient la figure quand le niveau change après l'écriture. »
>
> **T158** — « **Le tableau transposé.** `unfold._table_lines`, ou le générateur du vent, écrit les surfaces en colonnes et coupe au-delà de douze. La spec dit si la transposition devient une option générale des tableaux de domaine. »
>
> **T159** — « **Les survols vers les cellules** des tableaux de coefficients demandent que le domaine rende, pour chaque nombre, les clés des cellules qui l'ont produit (φ, colonne c<sub>pe</sub>, colonne c<sub>pi</sub>). »
>
> **T160** — « **#95** : la base paramétrée, en cours. Le vent en est le deuxième consommateur, et il complète ses briques plutôt que de les recopier. »
>
> **T161** — « **#94** : l'onglet Neige, premier onglet de calcul, dont le vent reprend tous les standards. »
>
> **T162** — « **#96** : le second clic qui désépingle. »

### Partie B — la question de l'ingénieur du 23.10.2026

> **T163** — « Je souhaite implémenter l'issue du vent pour le numéro 103, mais fais bien attention. J'ai entre-temps fait le issue 100 qui décrit très exactement à quoi doit ressembler l'onglet du vent, et c'est une grosse refonte. Donc regarde si tu n'as pas plus intérêt de faire un mélange des deux, en fait de prendre exactement issue 100 pour à quoi ça doit ressembler et de l'implémenter avec des briques. Fais-moi un petit retour avant de commencer à implémenter ça. Regarde profondément le issue numéro 100. »

### Partie C — corps de l'issue #103 (ouverte par Claude, suite de #95)

> **T164** — « Le domaine `calc/domains/wind_source.py` fournit ce que les services du type demandent : `declaration()` (le choix parmi les tables de l'Annexe C en `select`, `z` « = h », les sections et les champs), `visible_fields(src)`, `messages(src)` (existe déjà), `results(instance)`. Les extraits de SIA 261 chapitre 6 et de l'Annexe C sous chaque ⓘ, dans leurs fichiers de norme, tenus au PDF par un test ; la carte `layer=wind`. `WindTab(CalcTab)` : des paramètres seulement ; `wind-load` dans `unfold.AUTO_REGENERATE`. `load_tab.LoadTab` supprimé (plus aucun onglet n'en hérite), ses mots `ld_` gardés là où les onglets de charges les lisent. Tests, guide, CHANGELOG, « Nouveautés ». »

### Partie D — l'analyse rendue à l'ingénieur (propositions de Claude, non décisions)

> **T165** — « #100 est l'issue du Vent ; #103 en est un sous-ensemble ; proposition : fermer #103 comme couverte par #100. »
>
> **T166** — « Il leur manque, à compléter dans les briques pour tous les onglets : (1) du contenu non-champ dans les sections du formulaire ; (2) des survols liés à clés générales, le domaine rendant la provenance de chaque nombre ; (3) épingler n'importe quel module et l'ouvrir en fenêtre ; (4) un tableau de coefficients coloré ; (5) le modèle 3D en brique (projection et rendu sans Qt, et son widget) ; (6) « Affichage » et générateur : tableaux sans niveau à titre/note réglables, figure au niveau 3 seulement, tableau transposé coupé au-delà de douze surfaces. »
>
> **T167** — « Découpage proposé : (1) domaine et fichier, (2) briques complétées et onglet sur CalcTab sans 3D, (3) brique 3D avec les 6 bâtiments relevés, (4) les 31 autres bâtiments. »
>
> **T168** — « Trois points à trancher : la contradiction sur les 37 bâtiments ; la figure de la norme dans le rapport (découpage QtPdf, export sans fenêtre, bibliothèque des normes absente) ; le tableau transposé, option générale ou particularité du vent. »
>
> (Le reste de la partie D, ce que les briques de #95 donnent déjà — liste des cas, identité, bulles, volet de modules, figure 9 interactive `chart(src)`, « Affichage » ligne par ligne, `AUTO_REGENERATE`, `theme.json` `hover` = #cfe3fb — est un état des lieux, non une demande ; il n'est pas numéroté.)

### Partie E — les réponses de l'ingénieur du 23.10.2026

> **T169** — « Je vais répondre à tes questions, tes 3 points tranchés dans la spec, afin que tu puisses lancer la spec. Dessine tous les bâtiments et affiche également l'onglet qui montre la figure de la norme. Donc tu livres tous les bâtiments et tu livres la norme également pour tous les bâtiments. »
>
> **T170** — « Ensuite, pour la figure de la norme dans le rapport, il faut découper à l'enregistrement et donc le découpage se trouve dans le dossier variable loads wind. Ici se trouvera les exports .typ ainsi que les découpages. Redis-moi si je me trompe. »
>
> **T171** — « Et ensuite le tableau transposé, pour l'instant c'est une particularité du vent. »
>
> **T172** — « Ce qui est le plus important, c'est que les tableaux soient trapus plutôt que hauts. C'est ce qui est le plus important. Donc, ce n'est pas tout à fait une particularité du vent, mais ici, particulièrement pour le vent, c'était nécessaire de transposer le tableau. »

### Partie F — précision vérifiée dans le code (à rendre à l'ingénieur)

> **T173** — « Le fichier du cas est `Variable-loads/Wind/<id>.typ` (`project.DOMAIN_FOLDERS`), et les figures d'un domaine vont dans `<son dossier>/Exports/Figures/` (`project.figures_folder`), comme `Permanent-loads/Exports/Figures/` pour le poids propre : la découpe irait dans `Variable-loads/Wind/Exports/Figures/` ; `wind-load` n'est pas encore dans `project.FIGURE_KINDS`. »
