---
id: 2026-10-22-onglet-neige-type
titre: Onglet Neige repensé, premier onglet type des calculs
status: completed
cree: 2026-10-22
mis_a_jour: 2026-10-22
source: issue GitHub #94 (When-I-hit-the-wall/Woodcore), prototype au commit 5f2b2dc
docs: [docs/ui/window.md, docs/domain/loads.md, docs/decisions.md, docs/architecture/reference-library.md, docs/architecture/principles.md]
---

# Onglet Neige repensé, premier onglet type des calculs — Spécification

## 1. Objectif

L'ingénieur veut refaire l'onglet Neige (vues Calcul et Affichage) d'après le prototype HTML validé en quatre tours : la norme montrée au survol des données (bulle, épingle, lecteur PDF, carte externe), un volet droit fait de modules, et une vue Affichage qui règle le fichier `.typ` du cas ligne par ligne. L'onglet Neige doit être bâti sur une base commune et déclarative, afin que le vent, le séisme, les charges permanentes, les charges utiles et les vérifications repartent de cette base sans copier de code de widget. Le fichier et le rapport sont corrigés en passant (figure du cas, s_k en `#eq`, corniche, défauts du français).

## 2. Source

L'issue GitHub #94, mot pour mot, découpée en points. Les titres de l'issue sont gardés comme séparateurs.

**Titre de l'issue**

> **T0** — « Onglet Neige repensé, premier onglet type des calculs : la norme au survol, les modules du volet droit et l'Affichage ligne par ligne du fichier » *(titre, non classé : repris dans §1)*

**## Contexte**

> **T1** — « L'ingénieur a revu l'ergonomie de l'onglet Neige sur des prototypes HTML, en quatre tours, le 21 et le 22.10.2026. Ce qui suit est ce qu'il a retenu. Le prototype final sert de référence, mais **cette issue l'emporte là où les deux diffèrent** : quelques décisions ont été prises après la version 4. »
>
> **T2** — « L'onglet a deux vues : - **Calcul** : le formulaire, des bulles qui montrent la norme et un volet droit fait de modules ; »
>
> **T3** — « - **Affichage** : le fichier `.typ` du cas compilé, et le réglage de chacune de ses lignes. »
>
> **T4** — « **L'onglet Neige est le premier onglet type** des calculs, la base de ceux qui suivront (voir la section suivante). »

**## Un onglet type, base des onglets de calcul à venir**

> **T5** — « L'ingénieur, 22.10.2026 : la façon dont l'onglet Neige est construit doit être **un onglet type**. Le vent, le séisme, les charges permanentes, les charges utiles et les vérifications en reprendront le fonctionnement. Un futur onglet ne doit pas réinventer sa base : il **repart d'une base saine**, déjà écrite et documentée, et n'apporte que ce qui est propre à son domaine. »

*Ce que la base fait une fois, pour tous les onglets de calcul*

> **T6** — « Le cadre des deux vues, Calcul et Affichage, et la liste des cas à gauche (Nouveau, Dupliquer, Archives). »
>
> **T7** — « Le formulaire en sections, avec un ⓘ par donnée, et les genres de champs : nombre avec unité ; choix à boutons qui disent ce qu'ils valent, avec une valeur libre en plus (comme C_e) ; tuiles dessinées (comme les toitures) ; case à cocher. »
>
> **T8** — « La bulle de la norme : survol, clic qui épingle, Ctrl+clic, langue et repli sur l'allemand, texte puis image, placement. »
>
> **T9** — « L'ouverture de la norme dans le lecteur PDF de Woodcore (chapitre, page, rectangle encadré) et d'une carte externe (261.sia.ch, `layer=snow`, `layer=wind`…). »
>
> **T10** — « Le volet de modules : glisser-déposer, réduire, désépingler, fenêtre minimale avec Ctrl+molette, ordre et état retenus par onglet. Il a ses genres de modules : l'état du calcul (rouge, orange, vert, un clic qui mène au champ), les résultats (ce qui est calculé, compact), l'extrait épinglé, le dessin, le graphique interactif. »
>
> **T11** — « Toute la vue Affichage : l'aperçu du fichier du cas, le niveau du domaine, les éléments et leurs arguments lus dans `lib/formula.typ`, leur écriture dans le fichier, gardée à l'export suivant. »

*Ce qu'un domaine apporte, sans Qt, dans `calc/domains/` et `calc/norms/`*

> **T12** — « La déclaration de ses champs : clé, unité, genre de champ, valeurs et mots des choix, clause(s) de la norme. »
>
> **T13** — « Son calcul, ses messages (champ, genre, mots), la liste de ses résultats. »
>
> **T14** — « Ses dessins en SVG, utilisés par l'onglet et par le rapport. »
>
> **T15** — « L'emplacement de ses extraits dans la norme, et le chapitre à ouvrir. »
>
> **T16** — « Sa carte externe s'il en a une, et le générateur de son fichier `.typ`. »

*Ce que cela demande*

> **T17** — « Un **contrat déclaratif** : un onglet de calcul se décrit, il ne se recopie pas. Ajouter le vent, c'est écrire sa description et ses fonctions de domaine, sans copier de code de widget. »
>
> **T18** — « Une **page de documentation** « construire un onglet de calcul », avec l'onglet Neige comme exemple complet, et le contrat écrit dans `docs/decisions.md`. »
>
> **T19** — « Un **test qui monte la base sur un domaine minimal inventé**, pour prouver qu'elle ne dépend pas de la neige. »
>
> **T20** — « La revue d'architecture vérifie la base contre le vent (6.2 et ses tableaux), les charges permanentes, les vérifications d'éléments et un futur séisme (il n'existe pas encore de domaine), **sans les implémenter ici**. Le vent sera le deuxième onglet bâti sur la base, dans une issue à part. »

**## Le prototype**

> **T21** — « **Copie complète dans le dépôt**, au commit `5f2b2dc` de la branche `ccr-ce2d3d0c-6gi9hg` (non fusionnée) : `docs/requirements/prototypes/2026-10-22-onglet-neige/`. - Ouvrir `index.html` dans un navigateur, depuis ce dossier : il ne demande ni serveur ni réseau. - Le README dit ce qu'est chaque fichier. - Pour reprendre le dossier dans la branche de travail : `git checkout 5f2b2dc -- docs/requirements/prototypes/2026-10-22-onglet-neige`. »
>
> **T22** — « Le script de `index.html` contient déjà ce que l'implémentation devra reprendre, par fonction : - `N` : l'emplacement de chaque extrait de la SIA 261:2020 en FR et en DE (page et rectangle en points PDF) et son texte mot pour mot ; - `FIELD_NORM` : quel champ montre quelle clause ; - `compute()` : le calcul de la neige ; - `geometry()` et `fig3()` : les dessins de la figure 3 ; - les mots de la fenêtre en fr, de et en. »
>
> **T23** — « **Les versions successives**, artefacts claude.ai du compte de l'ingénieur. Une session Claude du même compte les lit avec l'outil Artifact, `action: "read"` : Onglet Neige repensé (dix propositions, et des inspirations venues d'autres outils) ; Prototype de l'onglet Neige (v1) ; Neige, calcul et affichage (v2) ; Neige, troisième version (v3) ; Neige, quatrième version (v4, la copie du dépôt). » *(liens d'artefacts omis ici ; voir l'issue)*

**## Décisions de l'ingénieur — vue Calcul / La norme au survol**

> **T24** — « Un ⓘ est placé à côté de chaque donnée. »
>
> **T25** — « Au survol (environ 350 ms), une bulle montre la clause : la norme, l'édition, la clause et la page. Dessous viennent **le texte de la norme mot pour mot, d'abord, puis l'image de l'extrait** découpée dans le PDF. Il n'y a pas d'onglets dans la bulle. »
>
> **T26** — « La bulle reste ouverte tant que la souris est sur le ⓘ ou sur la bulle. »
>
> **T27** — « Si la place manque dessous, la bulle s'ouvre au-dessus et défile à l'intérieur. Elle ne couvre jamais ce qu'elle explique. »
>
> *Cas particuliers :*
>
> **T28** — « **Toitures** : la bulle d'une forme de toit ne montre que l'extrait. Pour le toit à deux pans, la toiture en sheds et le toit cylindrique, c'est la figure 3 entière ; pour le toit à un pan, 5.3.2 et la figure 3 ; pour le toit plat, 5.3.5 et la figure 4. »
>
> **T29** — « **Décrochement** : le texte de 5.3.6 et la figure 5. »
>
> **T30** — « **Longueur et largeur du bâtiment** : 5.3.5 et la figure 4. »
>
> **T31** — « **Δh** : l'extrait de la carte de l'annexe D. »
>
> **T32** — « **Figure 2 interactive** : au survol, elle montre α, μ₁, μ₂ et μ₃. »
>
> **T33** — « **Langue de la norme** : celle de la fenêtre. Si l'édition manque (l'anglais), c'est l'allemand. »
>
> **T34** — « **Clic** : la bulle devient un module du volet droit. Elle se place **sous le module Résultats**, après les autres épingles, dans l'ordre où elles ont été faites. Un même extrait n'est jamais épinglé deux fois. »
>
> **T35** — « **Ctrl+clic** : - la norme s'ouvre dans le **lecteur PDF de Woodcore**, sur **tout le chapitre 5**, à faire défiler (FR p. 26–29, DE p. 25–28). La vue est à la page, la clause encadrée ; - pour Δh, c'est la carte de la neige de 261.sia.ch qui s'ouvre : `https://261.sia.ch/?lang=fr&layer=snow`, avec `lang=de` si la fenêtre est en allemand ou en anglais ; - pour le vent, plus tard : `https://261.sia.ch/?lang=fr&layer=wind`. »
>
> **T36** — « **Droits** : l'ingénieur autorise sans limite à découper la norme, à l'afficher dans Woodcore et à l'imprimer dans les rapports. »

**### Les données**

> **T37** — « **Section « Bâtiment »**, en tête : la longueur et la largeur, avec la figure 4 au survol. - Elles sont toujours saisies. - Pour un toit plat, elles donnent μ₁ selon la figure 4 : la majoration pour les grands bâtiments, sur le maximum de L et B, quand les deux dépassent 20 m (5.3.5). `snow_source` le fait déjà. »
>
> **T38** — « **C_e** : trois boutons qui disent ce qu'ils valent (abrité 1.2, normal 1.0, exposé 0.8), et un quatrième champ pour une valeur libre. La valeur libre est **acceptée sans message**. »
>
> **T39** — « **Toitures** : cinq formes, toit plat, à un pan, à deux pans, toiture en sheds et toit cylindrique (les mots du glossaire). - Elles sont dessinées en SVG, **en noir et blanc, dans le style de la figure 3 de la SIA 261**, avec α₁ et α₂, ou α et α₀ = 60°, et le petit rectangle de la structure dessous. »
>
> **T40** — « - Le calcul donne **toujours les modèles de charge 1 et 2**, et un seul modèle pour le toit plat. »
>
> **T41** — « - Les modèles sont dessinés comme dans la norme, avec leurs valeurs écrites « μ₁₁ = 0.80 » et « α₁ = 30° ». »
>
> **T42** — « **Pas de reprise automatique de l'altitude** de l'onglet Projet pour l'instant. »

**### Les modules du volet droit**

> **T43** — « Chaque bloc du volet droit est un module : l'état du calcul, les résultats, la disposition (la figure 3), la figure 2 interactive et les extraits épinglés. »
>
> **T44** — « **On réordonne par glisser-déposer**, plus facile quand les modules sont réduits. Il n'y a **pas de boutons à flèches**. »
>
> **T45** — « **▾ / ▸** réduit un module à son en-tête, avec un résumé (« ✓ complet · 1 info », « q_k,11 = 2.21 kN/m² »). »
>
> **T46** — « **×** désépingle un extrait. L'état, les résultats et la disposition se réduisent mais ne se ferment pas. »
>
> **T47** — « **⧉** ouvre le module dans une **fenêtre Woodcore minimale** : on y zoome par Ctrl+molette, et le module reste aussi dans le volet. C'est utile surtout pour un graphique interactif. »
>
> **T48** — « L'**ordre** et l'**état réduit** sont retenus **par onglet, sur ce poste**, comme la largeur des volets. »
>
> **T49** — « **Premier module : l'état du calcul.** - En rouge, ce qui empêche le calcul. - En orange, une information : le calcul est fait. - En vert, ✓ « Toutes les entrées sont là, le calcul est fait. » - Un clic sur un message mène au champ, qui clignote. »
>
> **T50** — « - Les messages : - au-dessus de 2000 m : « Altitude h₀ = 2050 m : la norme n'autorise pas ce calcul au-dessus de 2000 m (5.1.4). », **sans** « calculé quand même » ; »
>
> **T51** — « - au-dessus de 800 m, en orange : « Altitude h₀ = 850 m : au-dessus de 800 m, une corniche est à prendre en considération pour les porte-à-faux (5.3.7). ». »
>
> **T52** — « **Module Résultats** : seulement ce qui est calculé (h_ref, s_k, les μ, les q_k), jamais une saisie (h₀, Δh). Il est compact, sans les grandes tuiles. »

**## Décisions de l'ingénieur — vue Affichage**

> **T53** — « **Ce qui ne change pas** : la section du rapport appelle le cas par `#include domain-file("snow-load", "SN-01")`, qui est la commande à copier. Le cas est écrit dans `Variable-loads/Snow/<id>.typ`, et `show-calc` n'existe plus. »
>
> **T54** — « **Au centre**, le fichier compilé, chaque élément à sa place : le titre du domaine, la figure, puis les lignes `#var` et `#eq` ; »
>
> **T55** — « **les éléments masqués restent visibles en pâle**, marqués « masquée » ; »
>
> **T56** — « l'aperçu **n'est pas cliquable** et n'a **pas de cadre bleu** ; »
>
> **T57** — « Ctrl+molette zoome, et la page suit la largeur du volet ; »
>
> **T58** — « les notes vont **en bas de la page**, comme dans le PDF (dans le prototype, une ligne compilée seule a sa note juste dessous : c'est une limite du prototype seulement). »
>
> **T59** — « **À droite, en haut** : le fichier, la commande à copier, et le **niveau de détail 1, 2 ou 3**, qui est le niveau du domaine (`#domain(…, level: n)`). »
>
> **T60** — « **À droite, en dessous**, une **section** de la même carte (pas un autre module), « Éléments du fichier ». - Elle liste tous les éléments du fichier, chacun avec sa commande, son symbole, son libellé et ses niveaux **0 1 2 3**. - Le niveau du domaine est en pointillé tant que la ligne suit le domaine. Un clic fixe le niveau de la ligne (`level:`), un second clic le lui rend. »
>
> **T61** — « **Un clic sur une ligne** ouvre ses arguments dessous : listes déroulantes, et champs pour ce qui s'écrit. Dessous, la ligne telle qu'elle sera écrite dans le fichier ; « Voir le fichier entier » montre tout le fichier. »
>
> **T62** — « - `#var` : display, style, label-position, descr-position, norm-position, level. **Pas** name-calc, name-visible, value ni unit, qui sont ceux de l'export. »
>
> **T63** — « - `#eq` : equation, unit, as-unit, display-formula, display-equation, style, role, label, label-position, descr, descr-position, norm-position, level. »
>
> **T64** — « - `#verify`, pour les onglets des vérifications : display, role, label, label-position, descr-position, norm-position, level. »
>
> **T65** — « - **La figure** : width, caption, label, et l'afficher ou non. **Pas de niveau** : `#figure` n'en connaît pas. »
>
> **T66** — « **À l'export suivant**, une ligne réglée **garde ses arguments**, et Woodcore n'en rafraîchit que la valeur. »

**## Décisions de l'ingénieur — le fichier et le rapport**

> **T67** — « **La figure du cas dans le rapport** : une seule colonne de la figure 3, celle du toit du cas, avec le toit, sa structure et les modèles de charge 1 et 2. Elle est écrite en tête du fichier `.typ` du cas, comme les dessins d'une charge permanente (`#figure(image(…), width: …, caption: […]) <id-figure-1>`). Son SVG est dessiné à l'export par le même code que l'onglet. »
>
> **T68** — « **s_k est écrit en `#eq` avec l'équation (10)** de 5.2.6, pour que le niveau 3 la montre de nouveau. Aujourd'hui, `_calc_body` l'écrit comme une simple valeur, `#var("s_k", 2.759184, …)`. »
>
> **T69** — « **La corniche sort du rapport.** La ligne `schneeueberhang` n'est plus écrite. Le message orange reste dans l'onglet. »

**## Défauts trouvés dans le fichier français**

> **T70** — « `norm-section: "Figur 3"`, `"Figur 2"`, `"Anhang D"` : mots allemands dans un document français (et « §Figur » dans les anciennes commandes) ; »
>
> **T71** — « les symboles « Dachform » et « Abgleiten des Schnees » sont imprimés en allemand ; »
>
> **T72** — « la description du glissement écrit « mu_1 » en lettres au lieu de μ₁. »

**## Demandes**

*Onglet type*

> **T73** — « La base commune des onglets de calcul : les deux vues, la liste des cas, le formulaire et ses genres de champs, la bulle de la norme, le lecteur PDF et la carte externe, le volet de modules et ses genres, la vue Affichage. »
>
> **T74** — « Le contrat déclaratif qu'un domaine remplit ; l'onglet Neige bâti entièrement dessus, sans code propre à la neige dans la base. »
>
> **T75** — « Un test de la base avec un domaine minimal inventé. »
>
> **T76** — « La page « construire un onglet de calcul » (`docs/ui/`), avec la neige comme exemple, et la décision dans `docs/decisions.md`. »

*Vue Calcul*

> **T77** — « Les bulles de la norme : survol, clic qui épingle, Ctrl+clic, langue avec repli sur l'allemand, texte puis image, placement qui ne couvre pas le déclencheur. »
>
> **T78** — « L'emplacement de chaque extrait (fichier, page, rectangle par édition) et son texte, à côté de chaque `norm_ref` du domaine, depuis la table `N` du prototype. »
>
> **T79** — « Le lecteur PDF de Woodcore : ouvrir le chapitre, aller à la page, encadrer un rectangle. »
>
> **T80** — « 261.sia.ch : la carte de la neige pour Δh. »
>
> **T81** — « Le volet de modules : glisser-déposer, réduire, désépingler, fenêtre minimale avec Ctrl+molette, ordre et état retenus par onglet. »
>
> **T82** — « L'état du calcul en rouge, orange et vert, avec les messages ci-dessus ; le module Résultats compact. »
>
> **T83** — « La section Bâtiment (L, B) ; C_e et sa valeur libre ; les cinq toitures et la disposition dessinées comme la figure 3, en noir et blanc ; la figure 2 interactive. »

*Vue Affichage*

> **T84** — « L'aperçu du fichier du cas, éléments masqués en pâle, non cliquable, notes en bas de page. »
>
> **T85** — « Niveau 1, 2 ou 3 du domaine ; la section « Éléments du fichier » avec 0 1 2 3 par ligne ; les arguments de `#var`, `#eq`, `#verify` et de la figure ; la ligne et le fichier montrés. »
>
> **T86** — « Les réglages d'une ligne écrits dans le fichier, et gardés à l'export suivant (seule la valeur est rafraîchie). »

*Fichier et rapport*

> **T87** — « La colonne de la figure 3 du cas en tête du fichier, son SVG écrit à l'export, width, caption, label et affichage réglables. »
>
> **T88** — « s_k en `#eq` avec l'équation (10) ; la corniche retirée du fichier ; les trois défauts du français. »

*Partout*

> **T89** — « Les mots en de, fr et en ; tests ; documentation (`docs/ui/`, `docs/domain/loads.md`, `docs/decisions.md`, `CHANGELOG.md`, Nouveautés). »

**## Points à étudier dans la spec**

> **T90** — « Il n'y a pas encore eu de revue d'architecture : `/big-feature` la fera. Le travail touche plusieurs modules et un contrat de données. Ce que le code de la 0.122 montre déjà : **La base existe en partie.** `calc/tools/load_tab.py` a déjà une base, `LoadTab`, avec une sous-classe par domaine (charges permanentes, neige, vent). Elle fournit la liste en dossiers, les archives, Nom · Description · ID, les cartes, et les deux vues par `display_view`. Elle suit la disposition des vérifications d'éléments (`member_check_tab.MemberCheckTab`). - L'onglet type doit **partir de là**, sans écrire une troisième base à côté. - La spec dit ce qui monte dans la base commune et ce qui devient la déclaration d'un domaine. - Elle dit aussi comment les vérifications d'éléments la rejoindront. »
>
> **T91** — « **La bibliothèque de référence** (`docs/architecture/reference-library.md`, §11bis) : aujourd'hui, rien dans `calc/` n'ouvre un PDF de norme. Montrer et découper la norme change cette règle. - Il faut une décision dans `docs/decisions.md`, avec l'autorisation de l'ingénieur. - Il faut dire comment Woodcore trouve les PDF : le dépôt `When-I-hit-the-wall/norms` de l'ingénieur, par un réglage du poste par exemple, jamais par un chemin écrit dans le dépôt. - Sans bibliothèque, la bulle montre la clause et le texte sans image, sans erreur. »
>
> **T92** — « **Une seule source** : l'emplacement des extraits va dans `calc/norms/sia261-2020-5.2-schnee.json`, à côté des `norm_ref` qui existent. Ce sera la même forme pour le vent (`sia261-2020-6.2-wind.json` et ses tableaux). Pour le texte mot pour mot, deux voies : - le lire dans le PDF à la volée (pypdf) : il ne vieillit pas, mais les μ de la police de symboles se perdent ; - le recopier une fois dans le fichier : il est exact, mais c'est une copie. »
>
> **T93** — « **Le volet de modules et la fenêtre minimale** : un composant de `calc/tools/`, commun aux onglets de calcul. »
>
> **T94** — « **Le lecteur PDF** : `calc/tools/pdf_pane.py` sait aller à une page (`jump`) ; encadrer un rectangle est à ajouter. »
>
> **T95** — « **Les dessins** : - `calc/domains/snow_svg.py` (sans Qt) fait aujourd'hui le croquis de l'onglet (`snow_source.sketch`). Il dessinera la figure 3 pour l'onglet et pour le rapport, d'un seul code ; - les mots des dessins (« Modèle de charge 1 ») viennent du glossaire ; - le prototype en donne la géométrie (`geometry`, `fig3`). »
>
> **T96** — « **Le fichier du cas** : `calc/domains/unfold.py` (`_generate_load`, `_calc_body`) écrit les lignes. Garder les arguments d'une ligne réglée à l'export suivant passe par la base et les empreintes des lignes (`line_digests`, `refresh`, `_replace_line`). La spec doit dire comment un argument écrit survit à la réécriture de la valeur. Le mécanisme vaut pour tous les domaines écrits dans leur fichier. »
>
> **T97** — « **La vue Affichage** : `calc/tools/display_view.py` et `display_options.py`. Les arguments et leurs valeurs viennent des signatures de `lib/formula.typ` (`var`, `eq`, `verify`) : les lire, ne pas les recopier. »
>
> **T98** — « **La figure sans niveau** : afficher ou non. Il faut choisir entre écrire la ligne ou non, et une option du cas dans sa source `loads/snow/<id>.json`. Si la source change, il faut une version de schéma. »
>
> **T99** — « **Les messages de l'état** : `snow_source.warnings` donne le champ et le genre de chaque message ; leurs mots sont dans les tables de l'onglet. »

## 3. Exigences fonctionnelles

### REQ-001 — Ctrl+clic : la norme dans le lecteur PDF de Woodcore
- **Exigence** : Woodcore doit, sur Ctrl+clic d'un ⓘ (ou d'une bulle) de norme, ouvrir le lecteur PDF de Woodcore sur tout le chapitre 5 de la SIA 261:2020 (FR p. 26–29, DE p. 25–28), défilable, la vue placée à la page de la clause et la clause encadrée d'un rectangle ; le rectangle et la page viennent de l'emplacement déclaré de l'extrait.
- **Source** : T9, T35, T79, T94
- **Priorité** : doit
- **Critère d'acceptation** : un test sur un extrait de la table des emplacements appelle l'ouverture et obtient (fichier, page, rectangle) de l'édition de la langue de la fenêtre ; `pdf_pane` expose une méthode qui encadre un rectangle et un test vérifie que le rectangle demandé est celui peint.

### REQ-002 — Ctrl+clic sur Δh : la carte 261.sia.ch
- **Exigence** : Woodcore doit, sur Ctrl+clic de l'ⓘ de Δh, ouvrir `https://261.sia.ch/?lang=fr&layer=snow` (avec `lang=de` si la fenêtre est en allemand ou en anglais) ; l'URL se déclare dans le domaine (carte externe), la base ne connaît que `lang` et `layer`.
- **Source** : T9, T16, T35, T80
- **Priorité** : doit
- **Critère d'acceptation** : un test donne les trois URL attendues pour fr, de, en ; aucune chaîne `261.sia.ch` dans la base commune.

### REQ-003 — Épinglage des extraits
- **Exigence** : Woodcore doit, sur un clic d'ⓘ, transformer la bulle en module épinglé du volet droit, placé sous le module Résultats après les épingles existantes (ordre de création), et ne jamais épingler deux fois le même extrait.
- **Source** : T34, T77
- **Priorité** : doit
- **Critère d'acceptation** : deux clics sur le même ⓘ donnent un seul module ; deux extraits différents donnent deux modules dans l'ordre des clics, sous Résultats.

### REQ-004 — Sans bibliothèque de référence : clause et texte sans image
- **Exigence** : les PDF étant livrés (D-24), Woodcore doit tout de même, si un PDF manque (un clone partiel, une édition non livrée — l'anglais), montrer la clause et le texte sans image, sans exception ; le Ctrl+clic le dit dans la ligne d'état.
- **Source** : T91
- **Priorité** : doit
- **Critère d'acceptation** : un test sans bibliothèque configurée construit la bulle (clause + texte, pas d'image) sans lever d'erreur.

### REQ-005 — Section « Bâtiment » (L, B) et μ₁ du toit plat
- **Exigence** : Woodcore doit placer en tête du formulaire une section « Bâtiment » avec la longueur et la largeur, toujours saisies ; pour un toit plat, elles donnent μ₁ selon la figure 4 (majoration pour grands bâtiments, sur max(L, B), quand les deux dépassent 20 m, 5.3.5), comme `snow_source` le fait déjà.
- **Source** : T37, T83
- **Priorité** : doit
- **Critère d'acceptation** : test avec toit plat, L et B > 20 m : μ₁ majoré selon la figure 4 ; avec L ou B ≤ 20 m : pas de majoration ; la section est la première du formulaire.

### REQ-006 — C_e : trois boutons et valeur libre
- **Exigence** : Woodcore doit offrir pour C_e trois boutons qui disent leur valeur (abrité 1.2, normal 1.0, exposé 0.8) et un quatrième champ de valeur libre, acceptée sans message.
- **Source** : T38, T83
- **Priorité** : doit
- **Critère d'acceptation** : une valeur libre (ex. 0.95) est utilisée dans le calcul et ne produit aucun avertissement ; chaque bouton porte son libellé et sa valeur.

### REQ-007 — Cinq toitures et modèles de charge 1 et 2
- **Exigence** : Woodcore doit proposer cinq formes de toit (plat, un pan, deux pans, sheds, cylindrique, avec les mots du glossaire) ; le calcul doit toujours donner les modèles de charge 1 et 2, et un seul modèle pour le toit plat.
- **Source** : T39, T40
- **Priorité** : doit
- **Critère d'acceptation** : pour chaque forme, la liste des résultats compte 2 modèles (1 pour le toit plat) ; les noms des formes viennent du glossaire (de/fr/en).

### REQ-008 — Module « État du calcul » et ses messages
- **Exigence** : Woodcore doit offrir un premier module « État du calcul » qui montre en rouge ce qui empêche le calcul, en orange une information (calcul fait), en vert « ✓ Toutes les entrées sont là, le calcul est fait. » ; un clic sur un message mène au champ, qui clignote. Les messages viennent du domaine, chacun avec son code, son champ et son genre (`error` | `info`) et ses paramètres (`snow_source.warnings` ne rend aujourd'hui que `(code, params)` : il gagne le champ et le genre) ; leurs mots sont dans les tables de l'onglet. Altitude > 2000 m : **orange** (le calcul est fait, comme aujourd'hui et comme dans le prototype, `k:"warn"`), « Altitude h₀ = 2050 m : la norme n'autorise pas ce calcul au-dessus de 2000 m (5.1.4). », sans « calculé quand même » ni « le rapport n'en dit rien » ; sinon altitude > 800 m : orange, corniche (5.3.7). Une saisie invalide (h₀ < 0, C_e libre ≤ 0, C_T hors ]0, 1], α hors [0, 90], L ou B ≤ 0 d'un toit plat) est rouge, nommant le champ, et le calcul ne se fait pas.
- **Source** : T49, T50, T51, T82, T99 ; prototype `compute()` (couleur du message des 2000 m, liste des erreurs)
- **Priorité** : doit
- **Critère d'acceptation** : h₀ = 2050 m donne le message orange exact (fr/de/en) et des résultats ; h₀ = 850 m donne le message de la corniche ; entrées complètes et h₀ ≤ 800 m donnent le vert ; C_T = 0 donne un message rouge sur le champ C_T et aucun résultat ; le clic sur un message donne le focus au champ qu'il nomme (test hors écran).

### REQ-008b — Les autres informations du prototype
- **Exigence** : Woodcore devrait dire aussi, en orange, ce que le prototype dit : C_T < 1 (5.2.5), une pente ≥ 60° quand le glissement est possible (5.3.3), un toit plat dont L et B dépassent 20 m (5.3.5, figure 4 appliquée), un décrochement coché (5.3.6, non calculé).
- **Source** : T22 (le prototype est la référence), CON-001 (l'issue ne les retire pas) — inféré
- **Priorité** : devrait
- **Critère d'acceptation** : un test par message : le cas qui le déclenche le rend, avec son champ.

### REQ-021 — La source de la neige : C_e libre (schéma 1.3), L et B pour tout toit
- **Exigence** : `loads/snow/<id>.json` doit pouvoir porter une valeur libre de C_e (`exposure: "custom"` et `c_e`, nombre > 0) (c'est la nouvelle `schema_version` 1.3, écrite seulement par une source qui s'en sert, au plus haut plancher exigé : C_e libre 1.3, décrochement 1.2, liens 1.1, sinon 1.0 ; contrôles `≥` sur des tuples), et la longueur et la largeur quel que soit le toit (déjà permis en 1.0 : `number|null`, sans changement de version) (comme 1.1 et 1.2 aujourd'hui, `stamp_version`), une source 1.0–1.2 restant lue telle quelle. L et B ne sont lus par le calcul que pour le toit plat ; ils ne sont imprimés que là où le calcul les lit.
- **Source** : T37, T38 ; principe 8 (schéma versionné) ; CON-006 — inféré pour la forme
- **Priorité** : doit
- **Critère d'acceptation** : `schemas/snow-source.schema.json` décrit 1.3 ; une source 1.0 de SN-01 est lue, et réécrite sans changement elle reste identique à l'octet (son **export** change, lui : REQ-016 à REQ-019, dit au CHANGELOG) ; une source 1.2 avec `links` et `height_step` reste acceptée ; une source avec C_e = 0.95 est écrite en 1.3 et calcule q_k avec 0.95 ; un toit à deux pans garde L et B à l'enregistrement.

### REQ-009 — Module « Résultats » : seulement le calculé
- **Exigence** : Woodcore doit montrer dans le module Résultats uniquement ce qui est calculé (h_ref, s_k, les μ, les q_k), jamais une saisie (h₀, Δh), sous forme compacte sans grandes tuiles ; la liste vient de la déclaration du domaine.
- **Source** : T52, T13, T82
- **Priorité** : doit
- **Critère d'acceptation** : le module ne contient aucune clé d'entrée ; la liste des résultats est celle déclarée par le domaine.

### REQ-010 — Ordre et état réduit retenus par onglet et par poste
- **Exigence** : Woodcore doit retenir l'ordre des modules et leur état réduit par onglet, sur ce poste, comme la largeur des volets.
- **Source** : T48, T10, T81
- **Priorité** : doit
- **Critère d'acceptation** : réordonner, réduire, fermer et rouvrir l'onglet (ou relancer) retrouve l'ordre et l'état ; deux onglets ont des états indépendants ; rien n'est écrit dans le projet (inféré : « sur ce poste »).

### REQ-011 — Niveau de détail du domaine (1, 2, 3)
- **Exigence** : Woodcore doit permettre de choisir le niveau 1, 2 ou 3 du domaine, écrit comme `#domain(…, level: n)`.
- **Source** : T59, T85
- **Priorité** : doit
- **Critère d'acceptation** : choisir 2 écrit `level: 2` dans le fichier du cas et l'aperçu se recompile à ce niveau.

### REQ-012 — Niveaux par ligne : 0 1 2 3
- **Exigence** : Woodcore doit lister, dans la section « Éléments du fichier », tous les éléments du fichier avec leur commande, symbole, libellé et niveaux 0 1 2 3 ; le niveau du domaine est en pointillé tant que la ligne le suit ; un clic fixe `level:` sur la ligne, un second clic le rend au domaine.
- **Source** : T60, T85
- **Priorité** : doit
- **Critère d'acceptation** : test : clic sur 2 écrit `level: 2` sur la ligne, second clic sur 2 retire `level:` ; l'indication pointillée suit le niveau du domaine.

### REQ-013 — Arguments d'une ligne, lus dans `lib/formula.typ`
- **Exigence** : Woodcore doit ouvrir, au clic sur une ligne, ses arguments (listes déroulantes, champs), la ligne telle qu'elle sera écrite, et « Voir le fichier entier ». Les arguments sont : `#var` (display, style, label-position, descr-position, norm-position, level ; pas name-calc, name-visible, value, unit) ; `#eq` (equation, unit, as-unit, display-formula, display-equation, style, role, label, label-position, descr, descr-position, norm-position, level) ; `#verify` (display, role, label, label-position, descr-position, norm-position, level) ; la figure (width, caption, label, affichage ; pas de niveau). Les noms et valeurs viennent des signatures de `lib/formula.typ`.
- **Source** : T11, T61, T62, T63, T64, T65, T85, T97
- **Priorité** : doit
- **Critère d'acceptation** : un test lit les signatures de `lib/formula.typ` et vérifie que les listes de la vue sont celles-là moins les exclus ; aucun nom d'argument copié en dur ; régler un argument change la ligne montrée et écrite.

### REQ-014 — Les arguments réglés survivent à l'export suivant
- **Exigence** : Woodcore doit, à l'export suivant, garder les arguments d'une ligne réglée et ne rafraîchir que sa valeur ; le mécanisme (base + empreintes de lignes) vaut pour tous les domaines écrits dans leur fichier.
- **Source** : T11, T66, T86, T96
- **Priorité** : doit
- **Critère d'acceptation** : test : régler `style`, changer h₀, exporter : la valeur est nouvelle, `style` est conservé ; même test sur un autre domaine écrit dans son fichier.

### REQ-015 — Commande à copier et emplacement du cas inchangés
- **Exigence** : Woodcore doit continuer d'appeler le cas par `#include domain-file("snow-load", "SN-01")`, écrit dans `Variable-loads/Snow/<id>.typ` ; `show-calc` n'existe plus.
- **Source** : T53
- **Priorité** : doit
- **Critère d'acceptation** : la commande affichée en haut à droite est exactement cette forme ; le fichier est à l'emplacement indiqué ; aucune référence à `show-calc`.

### REQ-016 — Figure du cas en tête du fichier `.typ`
- **Exigence** : Woodcore doit écrire en tête du fichier du cas une seule colonne de la figure 3 (le toit du cas, sa structure, modèles 1 et 2), sous la forme `#figure(image(…), width: …, caption: […]) <id-figure-1>`, son SVG (sans mots, D-31) étant dessiné à l'export par le même code que l'onglet et écrit sous `Variable-loads/Snow/Exports/Figures/<id>-fig3.svg` (D-32) ; width, caption, label sont réglables, et la figure se masque en commentant sa ligne (D-23).
- **Source** : T67, T65, T87, T98
- **Priorité** : doit
- **Critère d'acceptation** : l'export produit le SVG et la ligne `#figure` en première position ; le fichier compile ; le SVG est identique à celui de l'onglet pour les mêmes entrées.

### REQ-017 — s_k en `#eq` avec l'équation (10)
- **Exigence** : Woodcore doit écrire s_k en `#eq` avec l'équation (10) de 5.2.6, pour que le niveau 3 la montre.
- **Source** : T68, T88
- **Priorité** : doit
- **Critère d'acceptation** : `_calc_body` ne produit plus `#var("s_k", …)` mais un `#eq` de l'équation (10) ; au niveau 3 la compilation affiche l'équation.

### REQ-018 — La corniche sort du rapport
- **Exigence** : Woodcore doit ne plus écrire la ligne `schneeueberhang` dans le fichier ; le message orange reste dans l'onglet.
- **Source** : T69, T88
- **Priorité** : doit
- **Critère d'acceptation** : un fichier généré pour h₀ = 850 m ne contient pas `schneeueberhang` ; le message orange de REQ-008 apparaît.

### REQ-019 — Défauts du fichier français
- **Exigence** : Woodcore doit corriger dans le fichier français : les `norm-section` « Figur 3 », « Figur 2 », « Anhang D » (et « §Figur » dans les anciennes commandes) en français ; les symboles « Dachform » et « Abgleiten des Schnees » traduits ; « mu_1 » écrit μ₁ dans la description du glissement.
- **Source** : T70, T71, T72, T88
- **Priorité** : doit
- **Critère d'acceptation** : un export français de SN-01 ne contient aucun de ces mots allemands ni « mu_1 » ; mêmes sorties de/en cohérentes avec leur langue.

### REQ-020 — Revue d'architecture de la base contre d'autres domaines
- **Exigence** : La revue d'architecture doit vérifier la base contre le vent (6.2 et tableaux), les charges permanentes, les vérifications d'éléments et un futur séisme, sans les implémenter ; le vent est une issue à part.
- **Source** : T20
- **Priorité** : doit
- **Critère d'acceptation** : §13 de la spec contient un verdict par domaine (vent, charges permanentes, vérifications, séisme) ; aucun code de vent livré.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Cadre commun : deux vues et liste des cas
- **Exigence** : chaque onglet de calcul doit avoir les vues Calcul et Affichage et, à gauche, la liste des cas (Nouveau, Dupliquer, Archives).
- **Source** : T2, T3, T6, T73
- **Langues** : fr / de / en
- **Critère d'acceptation** : l'onglet Neige et l'onglet du test de base (domaine minimal) montrent ces éléments sans code propre.

### UI-002 — Formulaire en sections et genres de champs
- **Exigence** : le formulaire doit être en sections, avec un ⓘ par donnée, et gérer les genres : nombre avec unité ; choix à boutons disant leur valeur avec valeur libre en plus ; tuiles dessinées ; case à cocher.
- **Source** : T7, T73
- **Langues** : fr / de / en
- **Critère d'acceptation** : un domaine minimal déclarant un champ de chaque genre est rendu par la base ; chaque champ a son ⓘ.

### UI-003 — Bulle de la norme : contenu, délai, tenue, placement
- **Exigence** : au survol de l'ⓘ (~350 ms), une bulle doit montrer norme, édition, clause et page ; dessous, le texte mot pour mot d'abord, puis l'image de l'extrait (pas d'onglets). Elle reste ouverte tant que la souris est sur l'ⓘ ou sur la bulle ; si la place manque dessous, elle s'ouvre au-dessus et défile à l'intérieur ; elle ne couvre jamais ce qu'elle explique.
- **Source** : T24, T25, T26, T27, T77
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de géométrie : bulle ne chevauche pas le déclencheur, au-dessus quand la place manque ; délai ≈ 350 ms ; ordre texte puis image ; pas de widget d'onglets.

### UI-004 — Bulle : cas particuliers
- **Exigence** : la bulle d'une forme de toit ne montre que l'extrait (deux pans, sheds, cylindrique : figure 3 entière ; un pan : 5.3.2 et figure 3 ; plat : 5.3.5 et figure 4) ; Décrochement : texte de 5.3.6 et figure 5 ; Longueur et largeur : 5.3.5 et figure 4 ; Δh : extrait de la carte de l'annexe D ; la figure 2 interactive montre α, μ₁, μ₂, μ₃ au survol.
- **Source** : T28, T29, T30, T31, T32
- **Langues** : fr / de / en
- **Critère d'acceptation** : le `FIELD_NORM` du domaine donne ces associations champ → extrait ; un test les vérifie une à une.

### UI-005 — Langue de la norme et repli sur l'allemand
- **Exigence** : la bulle et le lecteur doivent utiliser la langue de la fenêtre ; si l'édition manque (anglais), l'allemand.
- **Source** : T33, T77
- **Langues** : fr / de / en
- **Critère d'acceptation** : fenêtre en, fr, de donnent respectivement extraits DE, FR, DE.

### UI-006 — Volet de modules : glisser-déposer, réduire, désépingler
- **Exigence** : le volet droit doit réordonner les modules par glisser-déposer (sans boutons à flèches) ; ▾ / ▸ réduit un module à son en-tête avec un résumé (« ✓ complet · 1 info », « q_k,11 = 2.21 kN/m² ») ; × désépingle un extrait ; état, résultats et disposition se réduisent mais ne se ferment pas.
- **Source** : T10, T43, T44, T45, T46, T81
- **Langues** : fr / de / en
- **Critère d'acceptation** : un glisser change l'ordre ; aucun bouton ↑/↓ ; × absent des modules état, résultats, disposition ; résumé réduit conforme.

### UI-007 — Fenêtre minimale d'un module (⧉)
- **Exigence** : ⧉ doit ouvrir le module dans une fenêtre Woodcore minimale zoomable par Ctrl+molette, le module restant aussi dans le volet.
- **Source** : T47, T10, T81, T93
- **Langues** : fr / de / en
- **Critère d'acceptation** : après ⧉, le module existe dans la fenêtre et dans le volet ; Ctrl+molette change le zoom.

### UI-008 — Genres de modules
- **Exigence** : la base doit fournir les genres de modules : état du calcul, résultats, extrait épinglé, dessin, graphique interactif ; les blocs du volet de Neige (état, résultats, disposition figure 3, figure 2 interactive, extraits épinglés) sont tous des modules.
- **Source** : T10, T43, T73
- **Langues** : fr / de / en
- **Critère d'acceptation** : le volet de Neige ne contient que des modules de ces genres.

### UI-009 — Dessin SVG des toitures et de la disposition
- **Exigence** : les cinq toitures et la disposition doivent être dessinées en SVG, en noir et blanc, dans le style de la figure 3 de la SIA 261, avec α₁ et α₂ (ou α et α₀ = 60°) et le petit rectangle de la structure ; les modèles de charge sont dessinés comme dans la norme, avec valeurs écrites (« μ₁₁ = 0.80 », « α₁ = 30° ») ; les mots des dessins viennent du glossaire.
- **Source** : T39, T41, T83, T95
- **Langues** : fr / de / en
- **Critère d'acceptation** : SVG sans couleur (noir/blanc) ; textes présents en fr/de/en ; valeurs écrites égales aux résultats du calcul.

### UI-010 — Figure 2 interactive
- **Exigence** : le volet doit offrir la figure 2 interactive comme module graphique ; au survol, elle montre α, μ₁, μ₂ et μ₃.
- **Source** : T32, T43, T83
- **Langues** : fr / de / en
- **Critère d'acceptation** : le survol affiche les quatre grandeurs avec les valeurs du cas.

### UI-011 — Vue Affichage : aperçu du fichier
- **Exigence** : l'aperçu central doit montrer le fichier compilé, chaque élément à sa place (titre du domaine, figure, lignes `#var` et `#eq`) ; les éléments masqués restent visibles en pâle, marqués « masquée » ; l'aperçu n'est ni cliquable ni encadré en bleu ; Ctrl+molette zoome, la page suit la largeur du volet ; les notes sont en bas de la page comme dans le PDF.
- **Source** : T54, T55, T56, T57, T58, T84
- **Langues** : fr / de / en
- **Critère d'acceptation** : un élément masqué est rendu pâle avec l'étiquette « masquée » ; clic sur l'aperçu sans effet ; notes placées en pied de page.

### UI-012 — Vue Affichage : colonne de droite
- **Exigence** : à droite, en haut, le fichier, la commande à copier et le niveau 1, 2 ou 3 du domaine ; en dessous, dans la même carte (pas un autre module), la section « Éléments du fichier ».
- **Source** : T59, T60
- **Langues** : fr / de / en
- **Critère d'acceptation** : « Éléments du fichier » est dans la même carte que le niveau et la commande.

## 5. Exigences d'architecture

### ARCH-001 — Une seule base, partie de `LoadTab`
- **Exigence** : la base commune doit partir de `calc/tools/load_tab.py` (`LoadTab`) sans écrire une troisième base à côté de `LoadTab` et `MemberCheckTab` ; la spec dit ce qui monte dans la base (cadre, formulaire, bulle, lecteur, volet, vue Affichage) et ce qui devient la déclaration d'un domaine.
- **Source** : T4, T5, T73, T90
- **Critère d'acceptation** : un seul module de base ; les trois sous-classes actuelles (charges permanentes, neige, vent) en héritent ; §13 contient le tableau « monte dans la base / reste au domaine ».

### ARCH-002 — Contrat déclaratif d'un domaine
- **Exigence** : un domaine doit remplir un contrat déclaratif, sans Qt, dans `calc/domains/` et `calc/norms/` : champs (clé, unité, genre, valeurs et mots des choix, clauses) ; calcul, messages (champ, genre, mots), liste des résultats ; dessins SVG ; emplacement des extraits et chapitre à ouvrir ; carte externe éventuelle ; générateur du `.typ`. Ajouter un domaine ne copie aucun code de widget.
- **Source** : T12, T13, T14, T15, T16, T17, T74
- **Critère d'acceptation** : l'onglet Neige ne contient aucun code propre à la neige dans la base ; `grep` de « snow/neige » dans le module de base ne trouve rien ; le contrat est décrit par un schéma/type vérifié.

### ARCH-003 — Test de la base sur un domaine minimal inventé
- **Exigence** : un test doit monter la base sur un domaine minimal inventé (non neige) pour prouver qu'elle ne dépend pas de la neige.
- **Source** : T19, T75
- **Critère d'acceptation** : `tests/test_*.py` monte l'onglet sur un domaine fictif et vérifie vues, formulaire, bulle, volet, vue Affichage ; ligne ajoutée à `docs/conventions/testing-catalogue*.md`.

### ARCH-004 — Documentation et décision
- **Exigence** : une page `docs/ui/` « construire un onglet de calcul » avec l'onglet Neige comme exemple complet, et le contrat écrit dans `docs/decisions.md` (avec la décision sur la bibliothèque de référence, voir ARCH-007).
- **Source** : T18, T76, T89
- **Critère d'acceptation** : la page existe, est listée dans `docs/ui/window.md` et `docs/README.md` ; entrée dans `docs/decisions.md` et `docs/decisions-index.md`.

### ARCH-005 — Volet de modules : composant commun de `calc/tools/`
- **Exigence** : le volet de modules et la fenêtre minimale doivent être un composant de `calc/tools/` commun aux onglets de calcul.
- **Source** : T10, T93
- **Critère d'acceptation** : le composant n'importe rien de `calc/domains/snow*` ; réutilisé par le test du domaine minimal.

### ARCH-006 — Une seule source pour les extraits de la norme
- **Exigence** : l'emplacement de chaque extrait (fichier, page, rectangle par édition FR/DE) et le chapitre à ouvrir doivent vivre dans `calc/norms/sia261-2020-5.2-schnee.json`, à côté des `norm_ref` existants, de même forme pour le vent plus tard ; repris de la table `N` du prototype ; aucun emplacement codé dans les widgets ; chaque valeur lue d'une édition nommée.
- **Source** : T15, T22, T78, T92
- **Critère d'acceptation** : chaque `norm_ref` cité par un champ a un extrait avec page et rectangle pour FR et DE ; un test échoue si un champ du `FIELD_NORM` pointe vers un extrait absent ; aucun numéro de page dans `calc/tools/`.

### ARCH-007 — Décision sur la bibliothèque de référence
- **Exigence** : une décision dans `docs/decisions.md` doit lever la règle « rien dans `calc/` n'ouvre un PDF de norme » et « jamais un paragraphe de son texte » (`docs/architecture/reference-library.md`, §11bis) : les normes sont livrées (D-22, D-24), `reference-library.md` réécrit en conséquence, `principles.md` (règle 13, et le paragraphe « The reference library sits beside the pipeline ») mis à jour.
- **Source** : T36, T91
- **Critère d'acceptation** : la décision existe avec l'autorisation de l'ingénieur (T36) et le coût ; `reference-library.md` est mis à jour ; aucun chemin absolu de PDF dans le dépôt.

### ARCH-008 — Dessins : un seul code pour l'onglet et le rapport
- **Exigence** : `calc/domains/snow_svg.py` (sans Qt) doit dessiner la figure 3 pour l'onglet et pour le rapport, d'un seul code, à partir de la géométrie du prototype (`geometry`, `fig3`).
- **Source** : T14, T67, T95
- **Critère d'acceptation** : l'onglet et l'export appellent la même fonction ; `snow_svg.py` n'importe pas PySide6.

### ARCH-009 — Domaine sans Qt, onglet sans calcul
- **Exigence** : le calcul de la neige (`compute()` du prototype) doit vivre dans `calc/domains/` sans Qt ; l'onglet ne le recalcule pas (principes du projet, déduit de CLAUDE.md).
- **Source** : T13, T22, principe « Domain logic is independent of the UI »
- **Critère d'acceptation** : aucune formule neige dans `calc/tools/` ; un test du calcul sans Qt reproduit les valeurs du prototype (ex. q_k,11 = 2.21 kN/m²).

### ARCH-010 — Mots en trois langues, hors du code
- **Exigence** : tous les mots de la fenêtre (prototype : fr, de, en) et des dessins doivent être dans les tables de langues (`STRINGS`, glossaire), pas dans le code, et tenus par `tests/test_i18n.py`.
- **Source** : T22, T89, T95
- **Critère d'acceptation** : `tests/test_i18n.py` passe ; chaque chaîne nouvelle existe en de, fr, en.

### ARCH-011 — Arrivée des vérifications d'éléments
- **Exigence** : la spec doit dire comment les vérifications d'éléments (`MemberCheckTab`) rejoindront la base ; la vue Affichage doit déjà gérer `#verify`.
- **Source** : T64, T90
- **Critère d'acceptation** : §13 décrit la jonction (étapes, ce qui reste propre) ; aucune migration livrée ici (voir §8).

### ARCH-012 — Mécanisme de conservation des arguments, commun à tous les domaines
- **Exigence** : le mécanisme qui garde les arguments d'une ligne réglée (`line_digests`, `refresh`, `_replace_line`, via la base) doit valoir pour tous les domaines écrits dans leur fichier, et la spec doit dire comment un argument écrit survit à la réécriture de la valeur (voir Q-005).
- **Source** : T96, T66, T86
- **Critère d'acceptation** : un test sur un domaine autre que la neige (charges permanentes) garde un argument réglé.

### ARCH-013 — Lire la bibliothèque de normes : un module sans Qt, un découpage dans `calc/tools/`
- **Exigence** : où est le PDF d'une édition (le dossier livré, D-24) et quel extrait montrer (fichier, page, rectangle, langue avec repli DE) sont dits par un module sans Qt (`calc/norms/`) ; le rendu de l'image découpée (QtPdf, déjà utilisé par `pdf_pane`) est fait dans `calc/tools/`, mis en cache dans `%LOCALAPPDATA%\Woodcore\` (`usersettings.cache_dir`), jamais dans le projet ni dans le dépôt. Aucune image de norme n'est versionnée (le dossier `norm/` du prototype ne passe pas dans le code).
- **Source** : T91, T92, T94 ; `docs/architecture/reference-library.md` §11bis (aucun chemin de poste dans le dépôt) — inféré pour la forme
- **Critère d'acceptation** : aucun chemin de poste dans `calc/` ; le dossier des PDF est trouvé à côté du programme, depuis les sources comme installé ; un test découpe 5.3.4 FR et obtient une image non vide ; un test qui retire un PDF obtient « pas d'image » sans exception.

### ARCH-014 — Les normes livrées : copiées dans le dépôt, installées avec le programme
- **Exigence** : les PDF de la racine du dépôt `When-I-hit-the-wall/norms` (pas `Litteratur/`) sont copiés dans un dossier du dépôt Woodcore distinct de `calc/norms/` (qui part dans chaque projet), en binaire (`.gitattributes`), et l'installateur les livre ; les fichiers que `norms` garde en Git LFS sont pris dans leur contenu réel. `calc/norms/norms.json` (les éditions que le moteur nomme) dit le fichier de chacune ; un test dit qu'un PDF qu'un extrait cite est là.
- **Source** : réponses à Q-001 et Q-003 (22.10.2026)
- **Critère d'acceptation** : le dossier existe avec les PDF ; `packaging/woodcore.spec` (ou `build.py`) le prend ; un test du spec PyInstaller le nomme ; aucun PDF n'est copié dans un projet à l'export.

## 6. Contraintes

- **CON-001** — L'issue l'emporte sur le prototype là où les deux diffèrent (décisions après la v4). Source : T1.
- **CON-002** — Le prototype (commit `5f2b2dc`, branche `ccr-ce2d3d0c-6gi9hg`, non fusionnée) est la référence : `N`, `FIELD_NORM`, `compute()`, `geometry()`, `fig3()`, mots. Son dossier doit d'abord être repris dans la branche de travail. Source : T21, T22.
- **CON-003** — Texte de norme : édition nommée SIA 261:2020 (FR et DE). Source : T22, T92.
- **CON-004** — La fenêtre et le rapport parlent de, fr, en. Source : T22, T89.
- **CON-005** — Le vent n'est pas implémenté ici ; l'URL `layer=wind` est seulement possible plus tard. Source : T20, T35.
- **CON-006** — Si la source `loads/snow/<id>.json` change, une version de schéma est obligatoire ; les cas existants (SN-01) doivent rester lisibles (déduit : règle « schema_version » du projet). Source : T98.
- **CON-007** — Documentation obligatoire : `docs/ui/`, `docs/domain/loads.md`, `docs/decisions.md`, `CHANGELOG.md`, Nouveautés fr/de/en. Source : T89.
- **CON-008** — Un fichier `.typ` de cas déjà exporté ne doit pas perdre ce que l'ingénieur y a écrit en migrant vers le nouveau format de lignes (inféré, de T66 et T68 : s_k change de `#var` en `#eq`).
- **CON-009** — Les PDF de normes sont des copies sous licence ; l'installateur est public. L'ingénieur a décidé de les livrer (D-22, D-24). Source : T36, réponses du 22.10.2026.
- **CON-010** — Plusieurs sessions modifient le dépôt : `load_tab.py`, `display_view.py`, `unfold.py` sont partagés avec d'autres onglets ; les onglets Poids propre et Vent doivent continuer de marcher à chaque étape (tests `test_load_tabs*`, `test_display_view`, `test_unfold`). Source : CLAUDE.md — inféré.
- **CON-011** — Le prototype est lu au commit `5f2b2dc` (`git show`) ; rien de Woodcore ne lit son dossier (son README le dit), et ses images `norm/` et `pages/` ne servent pas de source aux bulles : elles sont découpées du PDF (ARCH-013). Source : T21 — inféré.

## 7. Décisions prises

- **D-1** — Nature de l'onglet : l'onglet Neige est le premier onglet type, bâti sur une base déclarative ; le vent sera le deuxième, dans une issue à part. Raison : ne pas réinventer la base. Source : T4, T5, T17, T20.
- **D-2** — La base part de `LoadTab`, sans troisième base. Source : T90.
- **D-3** — Droits : découper la norme, l'afficher dans Woodcore et l'imprimer dans les rapports sont autorisés sans limite. Raison : permet la décision de ARCH-007. Source : T36.
- **D-4** — Bulle : texte d'abord puis image, sans onglets ; langue de la fenêtre avec repli allemand. Source : T25, T33.
- **D-5** — Ctrl+clic ouvre le chapitre 5 entier dans le lecteur de Woodcore (non la clause seule). Source : T35.
- **D-6** — Réordonner par glisser-déposer seulement, pas de boutons à flèches. Source : T44.
- **D-7** — « Éléments du fichier » est une section de la même carte, pas un autre module. Source : T60.
- **D-8** — Aperçu non cliquable, sans cadre bleu. Source : T56.
- **D-9** — Les arguments de l'export (name-calc, name-visible, value, unit) ne sont pas réglables. Source : T62.
- **D-10** — La valeur libre de C_e est acceptée sans message. Source : T38.
- **D-11** — Le calcul donne toujours les modèles 1 et 2 (un seul pour le toit plat). Source : T40.
- **D-12** — Pas de message « calculé quand même » au-dessus de 2000 m. Source : T50.
- **D-13** — La corniche sort du rapport, le message orange reste dans l'onglet. Source : T69.
- **D-14** — Seule la valeur d'une ligne réglée est rafraîchie à l'export. Source : T66.
- **D-15** — Les cinq toitures en SVG noir et blanc, style figure 3. Source : T39.
- **D-16** — Les noms des clauses et les μ sont les mots du glossaire. Source : T39, T95.

- **D-17** (proposée, Q-005, précisée par la revue C) — Les arguments d'affichage d'une ligne — `fine-keys` de la commande + `style` + `role` + `level`, lus de `lib/display-vocabulary.json` que Typst lit aussi — sont à l'ingénieur : une seule fonction `comparable_text` les ôte de toute comparaison, et la réécriture d'une ligne (rafraîchir, régénérer) garde ceux du fichier. `equation`, `unit`, `as-unit`, `label`, `descr` restent réglables dans l'Affichage, mais une ligne ainsi changée devient « locale » (gardée, jamais gelée en silence).
- **D-18** (proposée, Q-006, précisée par la revue C) — Un fichier de cas neige à l'ancienne forme se régénère sur demande, jamais en silence : un suffixe de forme propre à `snow-load` (le `GENERATOR_VERSION` commun ne change pas) ; l'alias var↔eq ne prend pas pour ligne de l'ingénieur une ligne que Woodcore a écrite ; s_k s'écrit en `#eq` par une formule `max` qui s'évalue. Coût : tous les cas neige disent « forme changée » jusqu'au « Régénérer » ; l'export ne s'arrête pas.
- **D-26** (revue A, W03) — L'ordre et l'état réduit des modules sont retenus par poste (`layout_store.get_state/put_state`), pas par signature d'écrans.
- **D-27** (revue A, W04) — Les épingles sont de session, gardées à travers une reconstruction de la fenêtre ; l'ordre retenu ne nomme que les modules fixes.
- **D-28** (revue A, W09) — La règle 15 est précisée : l'Affichage montre, en lecture seule, la ligne qu'il écrit et le fichier entier, comme il montre déjà la commande à copier (T61).
- **D-29** (revue C, F08) — La ligne de la figure est retrouvée par son fichier d'image, non par son label : le label est réglable sans détacher la ligne.
- **D-30** (revue C, F13) — Le niveau du domaine a quatre états : auto (suit le rapport, montré en pointillé), 1, 2, 3 ; les niveaux 0–3 d'une ligne sont les préréglages de `display-presets.json`.
- **D-31** (Q-007) — Le SVG de la figure du rapport n'a pas de mots (symboles et valeurs) ; les mots sont dans la légende Typst ; l'onglet dessine par le même code et ajoute les siens.
- **D-32** (revue B, D03) — Les décisions « le rapport n'imprime pas de dessin de la neige » (issue #56, spec 2026-10-14, D-02/D-03) sont remplacées : la figure 3 du cas est exportée sous `Variable-loads/Snow/Exports/Figures/<id>-fig3.svg` (`FIGURE_KINDS`).
- **D-19** (inférée du prototype) — Au-dessus de 2000 m, le message est orange : le calcul est fait (REQ-008).
- **D-20** (inférée) — Les images des extraits sont découpées du PDF au moment de les montrer, mises en cache sur le poste, jamais versionnées (ARCH-013).

- **D-21** (Q-001) — Le texte des extraits est recopié une fois dans `calc/norms/<norme>.json` à côté du `norm_ref`, en FR et DE, et tenu au PDF livré par un test.
- **D-22** (Q-001) — §11bis change : les PDF de normes sont livrés avec Woodcore, `calc/` peut les ouvrir, les découper, les montrer, et leurs extraits peuvent être recopiés et imprimés. L'ingénieur en porte la décision (T36 et réponse du 22.10.2026).
- **D-23** (Q-008, remplace la réponse de Q-002) — Masquer la figure **commente sa ligne** dans le `.typ` (`// #figure(…) <id-figure-1>`) ; l'état de la ligne est « masquée », ni « missing » ni « own » ; l'export ne la décommente pas ; « Afficher » la décommente. Aucun champ dans la source. width, caption et label sont des arguments de la ligne, gardés à l'export.
- **D-24** (Q-003) — Toutes les normes du dépôt `norms`, sans `Litteratur/` et sans les tables SZS C4 et C5 (353 et 245 Mo, refusées par GitHub hors LFS ; l'ingénieur, 22.10.2026 : « Sans C4 et C5 »), sont copiées dans le dépôt Woodcore (un dossier à part de `calc/norms/`, qui est copié dans chaque projet) et livrées par l'installateur ; aucun réglage de poste ; `WOODCORE_NORMS_LIBRARY` cède la place au dossier livré.
- **D-25** (Q-004) — Poids propre et Vent gardent leur aspect ; la base choisit le nouveau cadre pour un onglet qui déclare un domaine.

À reporter dans `docs/decisions.md` : D-1, D-2, D-3 (avec ARCH-007), D-14, D-17, D-18, D-21 à D-32.

## 8. Hors périmètre

- Onglet du vent (issue à part, deuxième onglet sur la base) ; la carte `layer=wind` n'est pas câblée. Source : T20, T35.
- Reprise automatique de l'altitude depuis l'onglet Projet « pour l'instant ». Source : T42.
- Implémentation du séisme, des charges utiles, des vérifications d'éléments sur la base : seulement vérifiées par la revue d'architecture. Source : T5, T20, T90.
- Port du prototype HTML tel quel : il sert de référence, pas de livrable. Source : T21 (inféré).
- Limite du prototype sur les notes d'une ligne compilée seule : non reprise. Source : T58.

## 9. Idées non retenues comme exigences

- Inspirations venues d'autres outils, et les dix propositions de la première version (« Onglet Neige repensé »). Source : T23.
- Le vent plus tard avec `layer=wind` (annoncé, pas demandé ici). Source : T35.
- « Un clic ... une fenêtre ... utile surtout pour un graphique interactif » : explication de l'usage de ⧉, pas une exigence séparée. Source : T47.

## 10. Questions

### Q-001 — Le texte mot pour mot de la norme : recopié une fois ou lu dans le PDF ?
- **Pourquoi elle compte** : l'issue veut que, sans bibliothèque, la bulle montre « la clause et le texte sans image » (T91) : seul un texte recopié le permet. Mais une copie est ce que la règle 1 craint, et le texte recopié part avec le dépôt et l'installateur, qui sont partagés (aujourd'hui §11bis : « jamais un paragraphe de son texte »).
- **Options** : A (recommandée) recopié une fois, depuis la table `N` du prototype, dans `calc/norms/sia261-2020-5.2-schnee.json` à côté de chaque `norm_ref` (FR et DE, μ justes) ; un test le compare au PDF là où la bibliothèque est présente (`WOODCORE_NORMS_LIBRARY`), de sorte que la copie ne vieillit pas sans le dire ; B lu dans le PDF à la volée (pypdf) : aucune copie, mais les μ de la police de symboles se perdent et sans PDF la bulle n'a que la clause ; C le texte recopié, mais dans le dépôt `norms` de l'ingénieur à côté des PDF, lu comme eux : rien dans le dépôt du code, mais pas de texte sans bibliothèque.
- **Réponse** (22.10.2026) : « change la règle 11bis. Il est tout à fait acceptable d'avoir des extraits de norme ou des normes complètes livrées avec woodcore ». → Le texte est **recopié une fois** depuis la table `N` du prototype dans `calc/norms/sia261-2020-5.2-schnee.json` (FR et DE, μ justes) ; un test le compare au PDF livré (D-21). §11bis est réécrit (D-22).

### Q-002 — La figure du cas : où est dit « l'afficher ou non » ?
- **Pourquoi elle compte** : `#figure` n'a pas de `level:` (T65), donc « masquée » ne peut pas s'écrire sur sa ligne comme pour `#var`/`#eq`. Le choix dit où vit ce réglage et s'il faut une version du schéma de la source.
- **Options** : A (recommandée) une option du cas dans sa source, `loads/snow/<id>.json` (`figure: false`), écrite seulement quand la figure est retirée, dans la même version 1.3 que C_e libre (REQ-021) : l'export n'écrit alors pas la ligne, l'aperçu la montre pâle « masquée » ; width, caption et label restent des arguments de la ligne dans le fichier, gardés à l'export comme ceux de `#var` ; B la ligne retirée du fichier à la main ou par l'onglet, et l'export ne la remet pas (aucun schéma, mais une ligne de Woodcore absente est aujourd'hui l'état « missing », à changer pour la figure) ; C une nouvelle commande Typst de figure avec `level:` (une commande de plus, avec sa doc, ses exemples, ses traductions).
- **Réponse** (22.10.2026) : A, une option dans la source (`figure: false`, schéma 1.3) (D-23). *Remplacée le même jour par la réponse à Q-008 : masquer la figure commente sa ligne dans le `.typ`.*

### Q-003 — Comment Woodcore trouve-t-il les PDF des normes ?
- **Pourquoi elle compte** : jamais un chemin écrit dans le dépôt (§11bis) ; c'est une nouvelle commande de la fenêtre (un réglage).
- **Options** : A (recommandée) un réglage du poste dans la boîte « Réglages » : « Bibliothèque des normes », un dossier (la copie locale du dépôt `When-I-hit-the-wall/norms`), vide par défaut ; la variable `WOODCORE_NORMS_LIBRARY` des tests le remplace quand elle est posée ; vide, les bulles n'ont pas d'image et Ctrl+clic dit qu'il faut le régler ; B la variable d'environnement seule (rien à cliquer, mais à poser à la main sur chaque poste) ; C le dossier cherché à côté de Woodcore (`../ExternalFiles/000-Normes/`) sans réglage.
- **Réponse** (22.10.2026) : « les normes sont livrées avec woodcore. Tu les trouveras https://github.com/When-I-hit-the-wall/norms ». Précisé ensuite : **toutes les normes, sans la littérature** (les PDF de la racine du dépôt `norms`, ~170 Mo, pas `Litteratur/`), **copiées dans le dépôt Woodcore** (D-24). Rappel fait à l'ingénieur : l'installateur est publié sur `woodcore-releases`, qui est public ; il a maintenu le choix.

### Q-004 — Les onglets Poids propre et Vent, et les vérifications d'éléments
- **Pourquoi elle compte** : ils sont bâtis sur la même base `LoadTab` (Poids propre, Vent) ou à côté (`MemberCheckTab`). Si la base change, il faut dire ce qu'ils deviennent dans cette issue.
- **Options** : A (recommandée) Poids propre et Vent passent sur la nouvelle base pour ce qui est générique — le volet de modules (état, résultats, dessin) et la vue Affichage ligne par ligne — sans bulles de norme tant que leur domaine ne déclare pas d'extraits ; les vérifications d'éléments la rejoindront dans une issue à part, la spec ne disant que comment (et `#verify` déjà géré par l'Affichage) ; B Poids propre et Vent gardent leur aspect actuel jusqu'à leur propre issue (deux chemins dans la base en attendant) ; C les vérifications d'éléments passent aussi sur la base dans cette issue.
- **Réponse** (22.10.2026) : B, « Ils gardent leur aspect ». Poids propre et Vent restent tels quels jusqu'à leur propre issue ; la base a deux chemins en attendant : un onglet qui déclare un domaine (la neige) prend le nouveau cadre, les autres gardent l'actuel (D-25). Les vérifications d'éléments : une issue à part, la spec dit comment.

### Q-005 — Comment un argument écrit survit-il à la réécriture de la valeur ? (résolue dans la spec, à approuver)
- **Pourquoi elle compte** : REQ-014, pour tous les domaines écrits dans leur fichier.
- **Proposition (D-17)** : le réglage reste dans le `.typ` (règle 15 : le fichier est la source). Les **arguments d'affichage** d'une ligne — ceux que la vue Affichage offre, lus dans les signatures de `lib/formula.typ` — sont à l'ingénieur : `line_digests` les ôte de l'empreinte de la ligne, et `_replace_line` garde ceux du fichier en écrivant la ligne de l'export. Une ligne dont seuls ces arguments ont changé reste donc « en accord », et l'export n'y rafraîchit que la valeur. Une ligne changée ailleurs (valeur, formule) garde le comportement d'aujourd'hui (« local », « conflit »).
- **Réponse** : _(à approuver à l'étape 4)_

### Q-006 — Les fichiers de cas déjà écrits (inférée ; résolue dans la spec, à approuver)
- **Pourquoi elle compte** : s_k passe de `#var` à `#eq`, la figure arrive en tête, la corniche disparaît : un `Variable-loads/Snow/<id>.typ` existant n'a plus la forme de l'export.
- **Proposition (D-18)** : la forme écrite du domaine de la neige change (`form_of`), si bien qu'un fichier existant dit qu'il ne correspond plus et l'onglet propose « Régénérer », comme aujourd'hui pour une vérification dont la forme a changé ; rien n'est réécrit en silence, l'export ne s'arrête pas.
- **Réponse** : _(à approuver à l'étape 4)_

### Q-007 — Des mots dans le SVG de la figure du rapport ? (revue B, D02)
- **Pourquoi elle compte** : le SVG est écrit par Python à l'export, la langue du rapport n'est fixée qu'à la compilation ; aujourd'hui un SVG de Woodcore sert les trois langues.
- **Options** : A (recommandée) sans mots, symboles et valeurs seulement, les mots dans la légende Typst ; B trois SVG, un par langue.
- **Réponse** (22.10.2026) : A, « Sans mots, légende Typst ».

### Q-008 — Masquer la figure : la source ou le fichier ? (revue C, F09)
- **Pourquoi elle compte** : l'export ne supprime jamais une ligne du fichier ; une option dans la source demandait deux écritures non atomiques.
- **Options** : A (recommandée) le fichier décide, la base note la ligne retirée ; B l'option dans la source (réponse de Q-002).
- **Réponse** (22.10.2026) : « masquer la figure commente sa ligne dans le fichier .typ ». Remplace la réponse de Q-002 (D-23 remplacée).

## 11. Critères d'acceptation

- [x] REQ-001 à REQ-021 (et REQ-008b) — voir §3 (un test par exigence).
- [x] UI-001 à UI-012 — voir §4.
- [x] ARCH-001 à ARCH-014 — voir §5 ; les risques W01–W16, D01–D10, F01–F16 traités comme §13.3 le dit.
- [x] Documentation : `docs/ui/` (page « construire un onglet de calcul »), `docs/domain/loads.md`, `docs/decisions.md`, `docs/architecture/reference-library.md`, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en ; `///` + exemples + traductions pour toute commande Typst touchée.
- [x] Tests : fichiers `tests/test_*.py` ajoutés ou étendus (base sur domaine minimal, bulles, volet, vue Affichage, export), passent ; ligne dans le catalogue de tests ; `tests/test_i18n.py` passe.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T0 | §1 | titre |
| T1 | CON-001 | contrainte |
| T2 | UI-001 | capturé |
| T3 | UI-001, UI-011 | capturé |
| T4 | ARCH-001, D-1 | capturé |
| T5 | ARCH-001, D-1, §8 | capturé |
| T6 | UI-001 | capturé |
| T7 | UI-002 | capturé |
| T8 | UI-003, UI-005, REQ-003 | capturé |
| T9 | REQ-001, REQ-002 | capturé |
| T10 | UI-006, UI-007, UI-008, ARCH-005, REQ-010 | capturé |
| T11 | REQ-013, REQ-014 | capturé |
| T12 | ARCH-002 | capturé |
| T13 | ARCH-002, REQ-009, ARCH-009 | capturé |
| T14 | ARCH-002, ARCH-008, UI-009 | capturé |
| T15 | ARCH-002, ARCH-006 | capturé |
| T16 | ARCH-002, REQ-002 | capturé |
| T17 | ARCH-002 | capturé |
| T18 | ARCH-004 | capturé |
| T19 | ARCH-003 | capturé |
| T20 | REQ-020, CON-005, §8 | capturé |
| T21 | CON-002, §8 | contrainte |
| T22 | CON-002, ARCH-006, ARCH-009, ARCH-010 | capturé |
| T23 | §9 | idée / référence |
| T24 | UI-003 | capturé |
| T25 | UI-003, D-4 | capturé |
| T26 | UI-003 | capturé |
| T27 | UI-003 | capturé |
| T28 | UI-004 | capturé |
| T29 | UI-004 | capturé |
| T30 | UI-004 | capturé |
| T31 | UI-004 | capturé |
| T32 | UI-004, UI-010 | capturé |
| T33 | UI-005, D-4 | capturé |
| T34 | REQ-003 | capturé |
| T35 | REQ-001, REQ-002, D-5, CON-005 | capturé |
| T36 | D-3, ARCH-007 | décision |
| T37 | REQ-005, REQ-021 | capturé |
| T38 | REQ-006, REQ-021, D-10 | capturé |
| T39 | REQ-007, UI-009, D-15 | capturé |
| T40 | REQ-007, D-11 | capturé |
| T41 | UI-009 | capturé |
| T42 | §8 | hors périmètre |
| T43 | UI-006, UI-008, UI-010 | capturé |
| T44 | UI-006, D-6 | capturé |
| T45 | UI-006 | capturé |
| T46 | UI-006 | capturé |
| T47 | UI-007, §9 | capturé |
| T48 | REQ-010 | capturé |
| T49 | REQ-008 | capturé |
| T50 | REQ-008, D-12, D-19 | capturé |
| T51 | REQ-008 | capturé |
| T52 | REQ-009 | capturé |
| T53 | REQ-015 | capturé |
| T54 | UI-011 | capturé |
| T55 | UI-011 | capturé |
| T56 | UI-011, D-8 | capturé |
| T57 | UI-011 | capturé |
| T58 | UI-011, §8 | capturé |
| T59 | REQ-011, UI-012 | capturé |
| T60 | REQ-012, UI-012, D-7 | capturé |
| T61 | REQ-013 | capturé |
| T62 | REQ-013, D-9 | capturé |
| T63 | REQ-013 | capturé |
| T64 | REQ-013, ARCH-011 | capturé |
| T65 | REQ-013, REQ-016, Q-002 | capturé |
| T66 | REQ-014, D-14, ARCH-012 | capturé |
| T67 | REQ-016, ARCH-008 | capturé |
| T68 | REQ-017, CON-008 | capturé |
| T69 | REQ-018, D-13 | capturé |
| T70 | REQ-019 | capturé |
| T71 | REQ-019 | capturé |
| T72 | REQ-019 | capturé |
| T73 | UI-001, UI-002, UI-008, ARCH-001 | capturé |
| T74 | ARCH-002 | capturé |
| T75 | ARCH-003 | capturé |
| T76 | ARCH-004 | capturé |
| T77 | UI-003, UI-005, REQ-003 | capturé |
| T78 | ARCH-006 | capturé |
| T79 | REQ-001 | capturé |
| T80 | REQ-002 | capturé |
| T81 | UI-006, UI-007, REQ-010 | capturé |
| T82 | REQ-008, REQ-009 | capturé |
| T83 | REQ-005, REQ-006, UI-009, UI-010 | capturé |
| T84 | UI-011 | capturé |
| T85 | REQ-011, REQ-012, REQ-013 | capturé |
| T86 | REQ-014, ARCH-012 | capturé |
| T87 | REQ-016 | capturé |
| T88 | REQ-017, REQ-018, REQ-019 | capturé |
| T89 | ARCH-004, ARCH-010, CON-007 | capturé |
| T90 | ARCH-001, ARCH-011, Q-004, D-2, D-25 | résolu |
| T91 | REQ-004, ARCH-007, ARCH-013, ARCH-014, Q-003, D-24 | résolu |
| T92 | ARCH-006, Q-001, D-21 | résolu |
| T93 | ARCH-005, UI-007 | capturé |
| T94 | REQ-001 | capturé |
| T95 | ARCH-008, UI-009 | capturé |
| T96 | ARCH-012, Q-005 | capturé / question |
| T97 | REQ-013 | capturé |
| T98 | REQ-016, Q-002, D-23, CON-006 | résolu |
| T99 | REQ-008 | capturé |

### Points de la source non résolus

- Aucun. Q-001 à Q-004 répondues le 22.10.2026 ; Q-005 et Q-006 résolues par une proposition (D-17, D-18), approuvée ou non à l'étape 4.

## 13. Revue d'architecture

Trois revues indépendantes (`architecture-reviewer`, 22.10.2026), une par domaine : A la fenêtre, B le domaine et les normes, C le fichier du cas et l'Affichage. Verdicts : A et B **APPROUVER AVEC RÉSERVES**, C **REVOIR** (trois points bloquants, corrigés ci-dessous dans la spec). Après les corrections et les réponses de l'ingénieur (Q-007, Q-008) : **APPROUVER AVEC RÉSERVES**, les réserves étant les risques listés, chacun traité par le plan (§14).

### 13.1 Ce qui existe et sera réutilisé

- **Cadre** : `LoadTab` (`calc/tools/load_tab.py:316`), `SourceEditorTab` (liste, archives, Nouveau/Dupliquer), `DisplayTab`/`ViewPanes` (`display_view.py:726-801`), `views.CALC_VIEWS`, `identity`, `cards`, `chrome.FoldButton` (`chrome.py:189`) pour ▾/▸, le patron `QDrag` de `formula_tab_widgets.py:487-546`, le minuteur de `flowbar.DelayedTips` (`flowbar.py:130`), `linkable_spin.LinkableSpin`, `theme.colour` et les callouts `danger|warning|ok`, `usersettings.cache_dir`.
- **Lecteur PDF** : `pdf_pane.ZoomablePdfView` (`:171`, Ctrl+molette, ajuster) sous un `QPdfDocument` — pas `PdfPane`, lié à la compilation Typst.
- **Contrats** : `calc/domains/contracts.py` (des `Protocol` tenus par `tests/test_domain_contracts.py`) ; un domaine est un module, pas une classe.
- **Norme** : `calc/norms/_loader.py` (seul lecteur de JSON de `calc/norms/`), `norms.json`, `check_fields(src, fail)` (`snow_source.py:95`), seule source des règles « rouge ».
- **Export de figures** : `engine.Figures` + `instance["_files"]` (`dead_load_source.py:185-189`, `registry.py:196`), `project.FIGURE_KINDS` (`project.py:153`), `project.APP_ROOT` (sources comme gelé).
- **Fichier du cas** : `unfold._write` (atomique, `check_unchanged`), `formula_domain.patched` (ne touche que les arguments changés), `Command.written`/`read_call`, `status`/`refresh`/`regenerate`/`reinsert`, le précédent « retirer sans forcer » (`eta_s`, decisions.md), le suffixe de forme `-a` des moments polaires (`unfold.py:76`).
- **Affichage** : `FormulaTab.display_preset`/`write_display`/`merged_options` (à remonter dans `display_options.py`), `SpecPanel.for_view`, `ref.signature_defaults`/`call_command`, `lib/display-presets.json` (patron d'une table lue par Python et Typst), l'état `uniform-level` (`calc-engine-core.typ:42`, patron d'un interrupteur posé par l'en-tête du snippet).

### 13.2 Ce qui monte dans la base, ce qui reste au domaine (ARCH-001)

| Monte (`calc/tools/`, Qt) | Reste au domaine (`calc/domains/`, `calc/norms/`, sans Qt) |
|---|---|
| Cadre, liste, vues, enregistrer (existants, `LoadTab`) | Champs : clé, unité, genre, section, choix et leurs mots (glossaire), visibilité par cas, liens possibles (`LINKABLE`) |
| Widgets par genre de champ (`number`, `buttons` + valeur libre, `tiles`, `checkbox`, `select`), ⓘ, clignotement | Emplacement et texte des extraits (JSON de norme), chapitre à ouvrir |
| Bulle, épingle, Ctrl+clic, lecteur de norme, image découpée | Messages `Message(code, field, severity, params)`, résultats déclarés |
| Volet de modules, fenêtre ⧉, état retenu | Dessins SVG (figure, tuiles), données du graphique (séries + sonde) |
| Modules : état, résultats, extrait, dessin, graphique | Carte externe (gabarit d'URL), générateur du `.typ` |
| Vue Affichage d'un fichier de domaine | API sans Qt du fichier (`elements`, `set_display`, niveau, figure masquée) |

**Deux chemins sans troisième base (D-25, revue A)** : un mixin `DeclaredTabMixin` (`calc/tools/calc_tab.py`) surcharge les crochets que `LoadTab` expose déjà (`build_inputs`, `fill_inputs`, `draft_inputs`, `build_result`, `refresh`, `fill_results`, `fill_figure`, `display_entries`) ; `class SnowTab(DeclaredTabMixin, LoadTab)`. `DeadLoadTab` et `WindTab` restent sans changement. Pas de `if self.DECLARATION:` dans `LoadTab`.

**Les vérifications d'éléments, plus tard (ARCH-011, description seulement)** : les composants (champs par genre, bulle, volet, ⧉, état) ne dépendent pas de `LoadTab` ; `DeclaredTabMixin` n'exige que l'API de `SourceEditorTab` ; `MemberCheckTab` le mélangera à la place de ses `build_effort/fill_effort/draft_effort`, la carte « Position » restant un crochet `extra_cards` ; le genre de message s'étendra d'un `verdict` ; les copies `touch/spin/linked` de `member_check_tab.py:181-228` disparaîtront alors derrière `calc_fields.py`. La vue Affichage gère `#verify` dès cette issue.

**Le vent, plus tard** : le contrat prévoit déjà `select` (les ~50 tableaux de l'annexe C), une valeur spéciale (`z` « = h »), des résultats en tableaux (`instance["tables"]`), des extraits répartis sur plusieurs JSON de norme (le lecteur d'extraits prend une liste de fichiers). Le séisme : un module `chart` (spectre) et des champs `number`/`select`. Le poids propre : un genre `custom` (le tableau de couches), non construit ici (D-25).

### 13.3 Risques et ce que la spec en fait

Les tableaux des risques des trois revues (W01–W16, D01–D10, F01–F16) et la réponse à chacun sont dans `docs/history/2026-10-22-onglet-neige-type-risques-revue.md` (déplacés mot pour mot, la spec passant 100 Ko).

## 14. Plan d'implémentation

Neuf lots, dans cet ordre : chacun laisse la suite des tests verte et l'onglet utilisable (CON-010). Le §16 est mis à jour à la fin de chaque lot.

**Lot 1 — Les normes livrées** (ARCH-007, ARCH-014, D-22, D-24)
- `norm-library/` à la racine : les PDF de la racine du dépôt `norms` (sans `Litteratur/`), contenu LFS réel, `git lfs pull` sur un clone temporaire du scratchpad ; tailles listées avant la copie.
- `calc/norms/library.py` (sans Qt) : le dossier par `project.APP_ROOT`, le fichier d'une édition par `norms.json` (`files` par langue, additif), repli DE.
- `packaging/woodcore.spec` : `tree("norm-library")` ; `tests/test_packaging.py` l'exige. `tests/test_no_third_party_name.py` saute `*.pdf`. `tests/conftest.norms_library()` rend le dossier livré (`WOODCORE_NORMS_LIBRARY` le remplace s'il est posé).
- Tests : `test_packaging`, `test_no_third_party_name`, `test_sia260`, `test_norms`, `test_bibliography`.

**Lot 2 — Les extraits de la norme** (ARCH-006, ARCH-013, REQ-004, UI-004, UI-005, D-21)
- `calc/norms/sia261-2020-5.2-schnee.json` : `editions` (pages du chapitre par langue, FR 26–29, DE 25–28) à la place de `clause.pages` ; `excerpts` repris de la table `N` du prototype (page, rectangle, texte FR/DE, genre `text|figure`, carte externe de l'annexe D) ; `_source` corrigé ; `sia261_snow.clause()` inchangé pour ses lecteurs.
- `calc/norms/excerpts.py` (sans Qt, par `_loader`) : lecture d'une liste de fichiers, validation (langues, page dans le chapitre, rectangle dans la page, pas de texte pour une figure), `excerpt(id, lang)` avec repli DE, `chapter(norm, lang)`.
- Tests : nouveau `tests/test_norm_excerpts.py` (forme, champs → extraits, texte ↔ PDF par pypdf normalisé, repli DE, PDF absent sans exception).

**Lot 3 — Le domaine de la neige** (REQ-005 à REQ-008b, REQ-021, ARCH-002, ARCH-009, D-19)
- `contracts.py` : `Message` et le Protocol `CalcTabDomain` (déclaration, `messages`, `results`, dessins, données du graphique, extraits, carte externe — facultatifs ce qu'un domaine n'a pas) ; une ligne dans `test_domain_contracts.py`.
- `snow_source.py` : `problems(src)` extrait de `check_fields` ; `messages(src)` (erreurs + informations du prototype, seuils et clauses du JSON) ; `warnings` et `notes_of` en dérivent ; `fields()`/sections (Bâtiment en tête), `results()`, `external_map(lang)` ; schéma 1.3 (`exposure: "custom"` + `c_e`), planchers par tuples ; `wind_source.messages` aligné (`field=None`).
- `schemas/snow-source.schema.json` 1.3.
- Tests : `test_snow_source`, `test_load_sheets`, `test_load_tab` (mots des 2000 m), `test_domain_contracts`, `test_schemas`.

**Lot 4 — Les dessins** (REQ-016, UI-009, UI-010, ARCH-008, Q-007)
- `snow_svg.py` récrit en noir et blanc d'après `geometry()`/`fig3()` du prototype : la colonne de la figure 3 du toit (structure, modèles 1 et 2, « μ₁₁ = 0.80 », « α₁ = 30° », α₀) ; `words=None` pour le rapport ; les tuiles des cinq toits ; les séries de la figure 2 et `probe(alpha)` lues du JSON.
- Export : `build_instance` rend `figures`/`_files` ; `FIGURE_KINDS["snow-load"]`, `structure_folders`, `registry.write_files` par genre ; `unfold.figure_line(...)` factorisée (les trois écrivains) ; jetons `snow`/`snow-edge` de la palette retirés s'ils ne servent plus.
- Tests : `test_figure_golden` (hash, `CHANGES`), `test_snow_source`, `test_registry`, `test_project` (dossiers), un test noir et blanc et un test « même SVG onglet/export ».

**Lot 5 — Le fichier du cas** (REQ-014, REQ-017, REQ-018, REQ-019, ARCH-012, D-17, D-18, D-29, Q-008)
- `lib/display-vocabulary.json` (les `fine-keys`/`fine-values` de `lib/formula.typ`, lues par Typst et Python) ; `unfold.comparable_text` unique (`line_digests`, `_line_text`, `_forget`) ; fusion des arguments d'affichage dans `_replace_line` et `regenerate` ; normalisation des anciennes empreintes ; `_own_line` restreint ; ligne de figure retrouvée par son fichier ; état « masquée » d'une figure commentée, `hide_figure`/`show_figure`.
- Neige : s_k en `#eq` (formule `max` calculable) ; corniche hors export ; `norm-section` et symboles traduits par le glossaire, μ₁ (export et glossaire ensemble) ; suffixe de forme `snow-load`.
- `formula_domain` : `Domain.level`, en-tête par `patched` ; API `unfold.elements(here, kind, id)`, `unfold.set_display(...)`, `unfold.set_level(...)`.
- Tests : `test_unfold` (F01, F02, F03, F04, F12, ARCH-012 sur poids propre et moment polaire), `test_domain_generators`, `test_line_keys`, `test_formula_domain`, `test_i18n`.

**Lot 6 — Typst : montrer le masqué** (UI-011)
- Un état dans `lib/` posé par l'en-tête de l'aperçu ; `#var`, `#eq`, `#verify`, `#domain` impriment une ligne masquée pâle avec « masquée » (glossaire, trois langues) ; `///`, deux exemples, `calc/i18n/commands.json`.
- Tests : `test_commands`, `test_fine_display` (ou `test_formula`).

**Lot 7 — La base de la fenêtre** (UI-001 à UI-008, UI-010, REQ-001 à REQ-003, REQ-010, ARCH-003, ARCH-005, W01–W11)
- `calc/tools/calc_tab.py` (`DeclaredTabMixin`), `calc_fields.py` (genres, ⓘ, clignotement, `LinkableSpin`), `module_pane.py` + `module_window.py` (⧉, Ctrl+molette), `norm_bubble.py` (`place()` pure, 350 ms, fin de vie), `norm_reader.py` (`FramedPdfView`, `page_rect_in_view`), `excerpt_image.py` (QtPdf, cache), `calc_tab_words.py` (`ct_`) ; `layout_store.get_state/put_state` (par poste) ; `tab_guard.WRITERS`.
- Tests : nouveaux `tests/fake_domain.py`, `test_calc_tab_base.py` (le domaine inventé), `test_norm_bubble.py`, `test_norm_reader.py`, `test_module_pane.py` ; `test_layout_store`, `test_i18n` (clés disjointes), `test_module_size`, `test_module_imports`.

**Lot 8 — L'onglet Neige sur la base, et son Affichage** (REQ-005 à REQ-015, UI-011, UI-012, D-25, D-28, D-30)
- `calc/tools/snow_tab.py` + `snow_tab_words.py` (`sn_`) : `SnowTab(DeclaredTabMixin, LoadTab)` ; `tab_registry` ; les mots neige quittent `load_tab.py` ; `next_free_id` de `source_editor`.
- `calc/tools/domain_file_display.py` : aperçu (vraie page, `keep_place`), fichier, commande à copier, niveau du domaine (auto, 1, 2, 3), « Éléments du fichier » (0 1 2 3, pointillé), arguments d'une ligne (`display_options` : options fines `view="display"`, `views` en tuple, panneau de la figure), ligne écrite, « Voir le fichier entier » ; `display_preset`/`merged_options` remontés ; `FormulaTab.write_display` sur la même fonction.
- Tests : `test_load_tab`, `test_linkable_spin`, `test_tab_registry`, `test_display_view`, nouveau `test_domain_file_display.py`, `test_read_only`/garde.

**Lot 9 — Documentation et version** (ARCH-004, CON-007)
- `docs/ui/calc-tab.md` (« construire un onglet de calcul », la neige en exemple complet) et `docs/ui/tab-snow.md`, listés dans `window.md` et `docs/README.md` ; `docs/domain/loads.md` §3.3bis ; `reference-library.md` §11bis et `principles.md` (règles 13 et 15) ; `layout.md` ; `report-engine.md` ; `decisions.md` + `decisions-index.md` (D-1, D-2, D-3, D-14, D-17, D-18, D-21 à D-30, et les trois décisions « pas de dessin de la neige » *superseded*) ; `docs/conventions/testing-catalogue*.md` ; `CHANGELOG.md` ; « Nouveautés » fr/de/en ; version.
- Puis la vérification indépendante (étape 6) et `finish` (suite entière, commit, une question).

## 15. Vérification

Vérification indépendante (`requirements-verifier`, 22.10.2026) sur l'arbre de travail contre `d06f3403`, puis un second tour sur ses remarques. Tests du premier tour : `test_norm_excerpts` 7, `test_snow_source` 18, `test_case_file_display` 8, `test_calc_tab_base` 8, `test_domain_file_display` 7, `test_load_tab` 6, `test_unfold` 23, `test_domain_contracts` 10, `test_fine_display` 24, `test_docs_coherence` 7, `test_figure_golden` 1, `test_commands` 44 — verts ; `test_i18n` 2 échecs (corrigés au second tour : `sn_f_exposure` traduit en allemand ; le test reconnaît les clés composées par le préfixe que déclare un domaine ; cinq clés `ct_` inutilisées retirées → 23 verts).

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `calc_tab.open_excerpt` → `norm_reader.show_excerpt` ; `test_calc_tab_base.test_the_reader_frames_…` (chapitre de 4 pages, cadre, `page_rect_in_view`) ; l'édition allemande pour une fenêtre allemande : `test_an_excerpt_whose_edition_is_not_shipped_…` (2ᵉ tour) |
| REQ-002 | ✅ | `test_norm_excerpts.test_the_map_of_annex_d_…` (fr, de, en) ; aucun `261.sia` dans la base |
| REQ-003 | ✅ | `test_calc_tab_base.test_the_modules_move_fold_…` |
| REQ-004 | ✅ | `test_norm_excerpts.test_a_missing_pdf_leaves_the_words` ; bulle sans PDF : `test_an_excerpt_whose_edition_is_not_shipped_…` (2ᵉ tour) |
| REQ-005 | ✅ | `test_snow_source` (μ₁ 0.96, sections) |
| REQ-006 | ✅ | `test_snow_source.test_a_free_c_e_…`, `test_load_tab.test_a_free_c_e_…` |
| REQ-007 | ✅ | `test_snow_source` (cinq formes, modèles) |
| REQ-008 | ✅ | `test_load_tab.test_the_snow_tabs_state_…` ; `test_snow_source.test_the_messages_…` |
| REQ-008b | ✅ | `test_snow_source.test_the_messages_…` |
| REQ-009 | ✅ | `test_snow_source.test_the_results_…`, `test_calc_tab_base.test_the_results_…` |
| REQ-010 | ✅ | `test_calc_tab_base.test_a_drop_reorders_and_the_state_is_each_tabs_on_this_machine` (2ᵉ tour : `get_state/put_state`, deux onglets, rien dans le projet) |
| REQ-011 à REQ-015 | ✅ | `test_domain_file_display` (7), `test_case_file_display` (8) |
| REQ-016 à REQ-018 | ✅ | `test_snow_source.test_the_export_carries_…`, `test_the_written_out_snow_…`, `test_a_height_step_…` |
| REQ-019 | ✅ | `test_snow_source.test_a_french_file_prints_no_german_word_…` (2ᵉ tour) |
| REQ-020 | ✅ | §13 |
| REQ-021 | ✅ | `test_snow_source.test_a_free_c_e_…`, `test_a_source_1_0_read_and_written_again_is_the_same_bytes` (2ᵉ tour) |
| UI-001 | ✅ | `test_calc_tab_base.test_the_cases_list_the_two_views_…` (2ᵉ tour) |
| UI-002 | ✅ | `test_calc_tab_base.test_an_invented_domain_…` |
| UI-003 | ✅ | `test_the_bubble_never_covers_its_info`, `test_the_bubble_shows_the_words_then_the_image_…`, `DELAY_MS == 350` (2ᵉ tour) ; la tenue sous la souris est vue à l'écran, sans test |
| UI-004, UI-005 | ✅ | `test_snow_source.test_the_declaration_…`, `test_norm_excerpts.test_english_falls_back_…` |
| UI-006 | ✅ | `test_a_drop_reorders_…` (un vrai `dropEvent`, 2ᵉ tour), pas de flèches, × des seules épingles |
| UI-007 | ✅ | `open_window`, `zoom_by` ; l'événement Ctrl+molette lui-même n'est pas simulé |
| UI-008 | ✅ | `test_calc_tab_base` |
| UI-009 | ✅ | noir, blanc et gris de la palette (`ink` #1f1f1f, `ground`, `muted` #8a8a8a) : un dessin en niveaux de gris comme la figure 3 ; la revue (W16) parlait de #000/#fff, l'encre de la palette est son noir — écart assumé |
| UI-010 | ✅ | `test_calc_tab_base.test_the_results_…` (`probe`) |
| UI-011 | ✅ | `test_domain_file_display.test_the_figure_is_masked_…`, `test_the_page_compiles` ; l'aperçu est le `ZoomablePdfView` de toutes les pages (pas de clic, pas de cadre, Ctrl+molette, largeur), sans test propre |
| UI-012 | ✅ | `test_domain_file_display.test_the_case_is_written_…` |
| ARCH-001, ARCH-002, ARCH-005 | ✅ | `snow_tab.py` (25 lignes), `contracts.py`, `test_domain_contracts`, `test_the_base_holds_no_word_of_a_domain` |
| ARCH-003 | ✅ | `tests/fake_domain.py`, `test_calc_tab_base` (11) ; la vue Affichage n'est montée que sur la neige (le domaine inventé n'a pas de générateur de fichier) |
| ARCH-004, ARCH-007 | ✅ | `docs/ui/calc-tab.md`, `tab-snow.md`, `decisions.md` (6), §11bis, `principles.md` |
| ARCH-006, ARCH-013 | ✅ | `test_norm_excerpts` ; image de 5.3.4 FR non vide (2ᵉ tour) |
| ARCH-008 à ARCH-012 | ✅ | `test_snow_source`, `test_i18n` (23), `test_unfold` (23) |
| ARCH-014 | ✅ | `norm-library/` (78 PDF), `woodcore.spec`, `test_packaging` ; SZS C4 et C5 non livrées, décision de l'ingénieur (« Sans C4 et C5 », D-24) |
| CON-001 à CON-011 | ✅ | §6 tenu ; le prototype lu au commit `5f2b2dc`, non copié (CON-011) |
| §8 | ✅ | pas de vent, pas de reprise d'altitude, `member_check_tab.py` intact |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-22 | draft | spécification extraite de l'issue #94 (T0–T99, découpage par `requirements-analyst`), complétée par la lecture du code 0.123 et du prototype |
| 2026-10-22 | specified | Q-001 à Q-004 répondues (normes livrées et copiées dans le dépôt, sans la littérature ; §11bis changé ; figure dans la source ; Poids propre et Vent inchangés) |
| 2026-10-22 | reviewed | trois revues d'architecture (A fenêtre, B domaine et normes, C fichier et Affichage) ; Q-007, Q-008 répondues ; D-17, D-18 précisées, D-23 remplacée, D-26 à D-32 ; §13 et plan §14 en neuf lots |
| 2026-10-22 | approved | approuvée par l'ingénieur (« Approuver et implémenter ») |
| 2026-10-22 | implementation | Lots 1 à 8 faits : leurs lignes sont dans `docs/history/2026-10-22-onglet-neige-type-journal-lots-1-8.md` (déplacées mot pour mot, la spec passant 100 Ko). |
| 2026-10-22 | testing | Lot 9 fait (ARCH-004, CON-007) : `docs/ui/calc-tab.md`, `docs/ui/tab-snow.md` (index `docs/README.md`, `window.md`), `loads.md` §3.3bis, `reference-library.md` §11bis, `principles.md` (règles 13 et 15, la bibliothèque), `layout.md`, `typst/formulas.md`, `decisions.md` (6 décisions, celle de l'issue #56 partiellement remplacée) et `decisions-index.md`, `open-questions.md` (3 points), catalogue des tests (4 lignes), `CHANGELOG.md` v0.124, « Nouveautés » 0.124.0 fr/de/en, version 0.124.0 ; journal des lots 1 à 8 déplacé dans `docs/history/`. Ajout : « Régénérer » dans l'Affichage (`write_unfold_regenerate`), test. Reste : vérification indépendante, puis `finish`. |
| 2026-10-22 | verification | Vérification indépendante : tout ✅ ou ⚠️ (preuves manquantes), `test_i18n` ❌ (2). Second tour : `sn_f_exposure` en allemand, préfixes des domaines reconnus par `test_i18n`, 5 clés `ct_` mortes retirées ; preuves ajoutées (`test_snow_source` +2, `test_calc_tab_base` +3) ; D-24 amendé (SZS C4/C5). Tout ✅ (§15). |
| 2026-10-22 | completed | §11 coché ; spec déplacée dans `docs/requirements/completed/`. Reste : `finish`. |
