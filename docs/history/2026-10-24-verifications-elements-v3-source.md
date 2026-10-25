# Source de la spec 2026-10-24-verifications-elements-v3 (§2, déplacée telle quelle)

La §2 de [la spécification](../requirements/completed/2026-10-24-verifications-elements-v3.md) déplacée mot pour mot le 25.10.2026, pour tenir la spec sous 100 KB tant qu'elle est active. Les points T restent cités par leur numéro dans la spec.

L'issue GitHub #112, par points. Le prototype (artefact claude.ai « troisième version ») en est la référence visuelle ; **ce que l'issue dit l'emporte sur lui** (l'issue le dit : ses défauts de rendu sont des simplifications, et son « × η_w · η_t » d'un panneau est à vérifier dans la norme, voir Q-002). Les tableaux de réponses sont gardés ligne par ligne. Le contexte « Aujourd'hui (master `57172dd`…) » et la liste des artefacts ne sont pas des demandes ; le premier est repris dans l'état actuel du §3, la seconde dans le §8.

> **T1** — « L'ingénieur a revu trois versions d'un prototype HTML des **onglets de vérification d'éléments** (traction, compression, flexion, cisaillement) les 23 et 24.10.2026. Le 24.10.2026, il a validé la troisième version et choisi, pour le matériau, la **variante A : un menu, puis la sollicitation**. Cette issue décrit ce qui est à implémenter dans Woodcore, dans une autre session. »
>
> **T2** — « Ses mots, 24.10.2026 : « je valide ta proposition A, un menu puis la sollicitation. Il faut simplement que la sollicitation soit davantage claire. Par exemple, si je choisis comme matériau l'OSB3, la sollicitation est suffisamment claire, c'est bon, ne modifie pas ça. » »
>
> **T3** — « **Le calcul du prototype est celui de Woodcore.** Son moteur JavaScript est une traduction ligne à ligne de `member_check._compute_section` et de ses genres (Woodcore 0.122). Il a été comparé à Woodcore : 13 vérifications du projet d'exemple, 300 cas de cisaillement tirés au hasard et 400 cas des autres genres, sans aucun écart (au plus 2·10<sup>-16</sup>). L'implémentation n'a pas à reprendre ce moteur : Woodcore l'a déjà en Python. Elle reprend ce que la fenêtre montre et ce que la source enregistre. »
>
> **T4** — « Les quatre sortes — Traction, compression, flexion et cisaillement sont **des onglets séparés**, comme dans Woodcore. La barre de la fenêtre ne nomme que l'onglet (« Sécurité structurale › Cisaillement »). »
>
> **T5** — « Compression et flexion — **Pas d'avertissement** quand la stabilité n'est pas cochée : la case de l'accordéon Stabilité suffit. Le reste de la compression est inchangé. »
>
> **T6** — « Les résultats — **Dans l'ordre du calcul**, le taux d'utilisation η **en dernier**. Le verdict (vert ou rouge) reste en tête. La ligne qui gouverne un maximum (un côté, un axe) a un cadre pointillé. »
>
> **T7** — « L'affichage — Un bouton **Calcul | Affichage** au-dessus de la fenêtre. »
>
> **T8** — « Traction — Tout était bon : inchangée. »
>
> **T9** — « Flexion — **Un schéma dans le style de la SIA**, dans l'accordéon Efforts (voir plus bas). »
>
> **T10** — « Effort tranchant — Renommé **« Cisaillement »**, avec le cisaillement d'about et le cisaillement avec contrainte ⊥, en **trois figures** de gauche à droite au lieu de la liste déroulante. »
>
> **T11** — « 1. Le nom du 4.2.6 — **« Cisaillement d'about »** dans la fenêtre ; le rapport garde le titre de la norme, **« Cisaillement »**. »
>
> **T12** — « 2. σ<sub>90,d</sub> hors de −f<sub>c,90,d</sub> … f<sub>t,90,d</sub> — **Un avertissement orange** ; la vérification est calculée quand même. »
>
> **T13** — « 3. Les options de l'affichage — **Dans la source de la vérification** ; Woodcore réécrit le fichier tant que l'ingénieur ne l'a pas modifié. »
>
> **T14** — « 4. La page de la vue Affichage — **L'aperçu compilé par Typst**, comme partout ailleurs. L'ingénieur ne veut plus qu'on lui pose ce genre de question : l'Affichage est toujours le rendu Typst réel. »
>
> **T15** — « 5. Le schéma de la flexion — **Avec les contraintes aux bords, en nombres.** »
>
> **T16** — « La commande de l'Affichage — **`#include domain-file("check", "<id>")`** (`lib/calc-engine-core.typ`, ligne 359), pas `#show-check-member`. »
>
> **T17** — « Les défauts de rendu du prototype (fractions, parenthèses, racine, `#verify`) — Des simplifications du prototype : **ne pas s'en préoccuper**. Woodcore les rend par Typst. »
>
> **T18** — « Le matériau — Le C24 repris de la position T001 est juste, mais on doit pouvoir **choisir tout le bois de la bibliothèque** (onglet Matériaux, #110), **panneaux compris** ; un panneau a besoin de la **direction de sollicitation** pour la flexion. »
>
> **T19** — « Les trois variantes du matériau — **Variante A : un menu, puis la sollicitation.** La sollicitation doit être claire pour tout matériau ; celle de l'OSB/3 l'est déjà et ne change pas. »
>
> **T20** — « **Décisions antérieures qui restent** (revue de la version 1, 23.10.2026) : chaque valeur saisie peut venir d'une variable du projet, par un bouton à sa droite ; les onglets sont en accordéons ; »
>
> **T21** — « la stabilité est le dernier accordéon, à option, désactivée par défaut (« vérifier la stabilité au flambage » pour la compression) ; »
>
> **T22** — « vert à 100 % ou moins, rouge au-delà, pas d'orange pour le taux ; le taux en pourcent ; »
>
> **T23** — « l'en-tête compact, la liste qui dit l'état (triée par position ou par taux), l'état du calcul et la norme au survol comme pour la neige ; »
>
> **T24** — « pas de jauge, pas de section à l'échelle, pas de chaîne résistance / contrainte ; β saisissable à la main, avec des appuis glissants et des appuis fixes qui n'acceptent qu'une rotation. »
>
> **T25** — « **Quatre onglets séparés** dans la navigation de Woodcore : Traction, Compression, Flexion, Cisaillement. Chacun a sa liste à gauche, la vérification au centre en accordéons, le volet droit de modules. »
>
> **T26** — « **La barre de la fenêtre** ne nomme que l'onglet ouvert. La synthèse n'y est plus : elle est l'onglet « Synthèse ». »
>
> **T27** — « **Calcul | Affichage** au-dessus de la fenêtre, comme les autres onglets (`calc/tools/views.py`). »
>
> **T28** — « La liste (gauche) — Les vérifications de l'onglet, **groupées par position** (« T001 · Poutre », « Sans position »), chacune avec son taux en vert ou en rouge ; triées **par position** ou **par taux**. Les archives en bas. « Nouveau », « Dupliquer ». »
>
> **T29** — « L'en-tête « Élément » — Le nom, l'id, « + description » ; la position (une liste) ; puis une rangée de bulles : **le matériau**, la section, la classe d'humidité, et la case « chocs ou séisme · η<sub>t</sub> = 1,4 » avec son **i** (2.2.6). »
>
> **T30** — « Une bulle **suit la position** (grise, l'id de la position à droite) ou **l'écrase** (orange, « Reprendre » revient à la position). L'état du calcul le dit en orange : « Classe de résistance est écrasée (GL24h) alors que T001 dit C24. » »
>
> **T31** — « Le résumé de l'accordéon fermé : « T001 · C24 · 100 × 200 · classe d'humidité 2 ». »
>
> **T32** — « **La bulle du matériau** montre son nom court : « C24 », « GL24h », ou pour un panneau « OSB/3 en plaque ∥ ». Un clic ouvre, sous la rangée, **le menu de la bibliothèque** de l'onglet Matériaux (#110) : un champ de recherche (« C24, GL, OSB, panneau… »), qui cherche dans les noms en fr, de et en, le groupe et la source ; en tête, le matériau de la position, « suit T001 » ; »
>
> **T33** — « puis les groupes de l'onglet Matériaux : **Bois massif · SIA 265, tableau 8**, **Lamellé-collé · SIA 265, tableau 9**, **Panneaux · SIA 265/1**, **Personnel**, et **Bois sans résistance : un poids seulement**, grisé et non choisissable ; »
>
> **T34** — « chaque ligne montre la résistance que l'onglet ouvert lit : f<sub>m,d</sub> en flexion, f<sub>t,0,d</sub> en traction, f<sub>c,0,d</sub> en compression, f<sub>v,d</sub> en cisaillement ; pour un panneau ses valeurs par sollicitation (« p∥ 9,6 · p⊥ 4,8 · v∥ 5,5 · v⊥ 4,1 »), et la source (SIA 265, SIA 265/1, Perso). »
>
> **T35** — « **La rangée « Sollicitation »**, sous la bulle, est **toujours là**, pour que la sollicitation soit toujours dite : **pour un panneau**, ses bulles, **telles que l'ingénieur les a validées pour l'OSB/3 : ne pas les changer.** En flexion : « en plaque ∥ 9,6 », « en plaque ⊥ 4,8 », « en voile ∥ 5,5 », « en voile ⊥ 4,1 » (OSB/3, 10–18 mm). En traction et en compression : « en traction / compression ∥ » et « ⊥ ». En cisaillement : « en plaque ∥ », « en voile ∥ ». Une bulle sans valeur est grisée ; »
>
> **T36** — « **pour un bois en barre**, une seule bulle, cochée, non cliquable : « flexion f<sub>m,d</sub> = 14,1 » ; »
>
> **T37** — « dessous, une ligne dit **ce que la vérification lit** : « La vérification lit f<sub>m,d</sub> = 9,6 N/mm² · SIA 265/1:2018, tableaux 19a et 19b, plage 10–18 mm · épaisseur 18 mm, le plus petit côté de la section · × η<sub>w</sub> · η<sub>t</sub> ». Une valeur déduite dans l'onglet Matériaux est marquée « (déduite) ». »
>
> **T38** — « **L'épaisseur d'un panneau** est le plus petit côté de la section ; elle choisit la plage du tableau (OSB/3 : 6–10, 10–18, 18–25 mm). Hors des plages, la rangée et l'état du calcul le disent en rouge, avec les plages, et la vérification ne se calcule pas. »
>
> **T39** — « **Un matériau qui ne donne pas une résistance nécessaire** (un panneau n'a ni f<sub>c,90,d</sub> ni E<sub>0,05</sub> ni k<sub>a</sub> ; un bois personnel incomplet) : la vérification ne se calcule pas, l'état dit en rouge « OSB/3 en plaque ∥ ne donne pas toutes les résistances de cette vérification (compression) : choisissez un bois en barre ou une autre sollicitation, ou complétez-le dans l'onglet Matériaux. » »
>
> **T40** — « Les variantes B (une bulle par sollicitation) et C (une liste, puis les figures du tableau 19a) sont **écartées**. »
>
> **T41** — « Traction (inchangée) — L'effort N<sub>t,d</sub>, la case « à un angle α du fil » (4.2.1.3), le dessin de la barre. »
>
> **T42** — « Compression (inchangée, sans l'avertissement de stabilité) — Les trois cas dessinés : ∥ au fil (10), ⊥ au fil (11) (12), à un angle (13). Pour ⊥ et l'angle : l'appui dessiné, l et w, et les cinq valeurs de f<sub>c,90,d</sub> en cartes (generell, mit Vorholz, Endauflagerung, avec ou sans grössere Eindrückungen) ; une valeur absente est grisée. La stabilité en dernier accordéon, à option : « vérifier la stabilité au flambage », le flambage sur sa courbe, β saisissable ou choisi par ses appuis (dont glissant et fixe à rotation seule). »
>
> **T43** — « Flexion — Les efforts sur une ligne, signés : N<sub>d</sub> (traction | compression), M<sub>y,d</sub>, M<sub>z,d</sub> ; la case de l'angle α. »
>
> **T44** — « **Le schéma dans le style de la SIA**, dans l'accordéon Efforts, noir et blanc, traits fins, lettres en italique : la barre et ses moments M<sub>y,d</sub>, l'effort normal, le fil hachuré à l'angle α ; la section avec y, z, b, h, M<sub>z,d</sub> en double flèche ; la répartition de σ<sub>m,y,d</sub> (+ σ<sub>c,d</sub> ou σ<sub>t,d</sub>) sur la hauteur, **avec les valeurs aux deux bords** (réponse 5). Le dessin lit les contraintes de `compute` ; il n'en calcule aucune. »
>
> **T45** — « Le déversement en dernier accordéon, à option, sur sa figure 11. »
>
> **T46** — « Cisaillement (renommé, trois figures) — L'onglet « Effort tranchant » s'appelle **« Cisaillement »** (`tab_mc_shear`). En tête, **trois figures côte à côte, de gauche à droite**, au lieu de `variant_box` ; la figure choisie change ce qu'on saisit dessous. »
>
> **T47** — Les trois lignes du tableau : « **Effort tranchant**, 4.2.5.1 — On saisit V<sub>z,d</sub>, V<sub>y,d</sub>, avec ou sans moelle — Woodcore calcule τ = 1,5 · V / A (4/3 pour un rond), les deux plans en vecteur, (23) τ<sub>d</sub> ⩽ f<sub>v,d</sub> ; la moelle divise f<sub>v,d</sub> par 2 pour le bois massif — SC-01, 76,0 % » ; « **Cisaillement d'about**, 4.2.6 — F<sub>a,d</sub>, la longueur cisaillée l<sub>a</sub>, et w<sub>a</sub> s'il diffère de b — τ<sub>a,d</sub> = F<sub>a,d</sub> / (l<sub>a</sub> · w<sub>a</sub>) ⩽ k<sub>a</sub> · f<sub>v,d</sub>, k<sub>a</sub> = 0,6 bois massif (26), 0,8 lamellé-collé (27) ; sous 150 mm, pas calculable, comme aujourd'hui — SC-02, 138,9 % (l'exemple `verify-shear-off-1`) » ; « **Avec contrainte ⊥ au fil**, 4.2.7.1 — V<sub>z,d</sub>, σ<sub>90,d</sub> en compression ⊥ ou en traction ⊥ — (28), k<sub>t,90</sub> = 4,0 en compression, 1,0 en traction ; la figure interactive est le diagramme de la figure 8 de la norme, avec le point de la vérification — SC-03, 20,5 % (l'exemple `verify-shear-perp-1`) ».
>
> **T48** — « Le nom de la deuxième figure : **« Cisaillement d'about »** dans la fenêtre, **« Cisaillement »** dans le rapport (titre de la norme). La SIA 265 en français appelle 4.2.5 « Effort tranchant et torsion » et 4.2.6 « Cisaillement ». »
>
> **T49** — « **σ<sub>90,d</sub> hors de −f<sub>c,90,d</sub> … f<sub>t,90,d</sub>** : un avertissement orange dans l'état, la vérification calculée quand même. »
>
> **T50** — « La source ne change pas : `variant`, `F`, `l`, `w`, `sigma_90` restent ; seul l'onglet change. »
>
> **T51** — « Le volet droit — Les modules, déplaçables et repliables, comme pour la neige : 1. **État du calcul** : vert, orange, rouge ; un clic mène au champ. Plus d'avertissement de stabilité. 2. **Résultats** : le verdict en tête, puis **les lignes dans l'ordre du calcul**, η en dernier ; la ligne qui gouverne un maximum a un cadre pointillé ; un clic déplie la formule et ses nombres ; la clause à droite. 3. **Figure interactive** : la figure de la SIA 265 de la vérification (diagramme d'interaction, courbe de flambage, figure 8…), le point de la vérification dessus. 4. **La norme** : la clause, mot pour mot, et son extrait ; les extraits épinglés. »
>
> **T52** — « La vue Affichage — **Au centre, l'aperçu compilé par Typst** de la vérification, comme partout ailleurs (réponse 4). Le prototype dessine une esquisse ; Woodcore compile le vrai fichier. »
>
> **T53** — « **À droite** : le **niveau** du rapport : 0 rien, 1 les verdicts, 2 les contraintes et la relation, 3 chaque formule en nombres ; les **options** : la ligne de l'élément (aucune, 1, 2, 3), le verdict en rapport (« = 0,833 ⩽ 1 ✔ ») ou en % (« = 83,3 % ✔ »), imprimer la description, le titre ; **la commande à copier dans la section : `#include domain-file("check", "BI-04")`** ; **le fichier de la vérification**, `Timber-checks/<Sorte>/<id>.typ`, tel que Woodcore l'écrit (un domaine déplié : `#domain`, `#calc-defaults(presets: "block", scope: "domain")`, la ligne de l'élément, les `#var`, `#eq`, `#verify`). »
>
> **T54** — « **Les options s'enregistrent dans la source de la vérification** (réponse 3). Woodcore réécrit le fichier tant que l'ingénieur ne l'a pas modifié. »
>
> **T55** — Le tableau « Ce qui change dans Woodcore », ligne par ligne : « Quatre onglets séparés — `calc/tools/tab_registry.py`, `member_check_tab.py` — Un onglet par sorte (la compression porte le flambage, la flexion le déversement, comme aujourd'hui en stabilité). » ; « L'onglet « Cisaillement » — `member_check_tab_words.py` (`tab_mc_shear`), trois langues — Aucun contrat ne change. » ; « Les trois figures au lieu de `variant_box` — `member_check_tab.py` (`ShearTab`), trois boutons dessinés — **Une décision dans `docs/decisions.md` §13 qui remplace Q-010** (« le user choisit dans un menu déroulant », cité par `SHEAR_VARIANTS`). » ; « Plus d'avertissement de stabilité — l'état de l'onglet — Une ligne retirée. » ; « Les résultats dans l'ordre du calcul — le module Résultats — Les lignes de `compute` telles quelles : c'est aussi l'ordre du rapport. » ; « Le schéma de la flexion — un dessin de l'onglet, sans couleur — Il lit les contraintes de `compute`. » ; « σ<sub>90,d</sub> hors de l'intervalle — l'état, en orange — Une note, pas un refus. »
>
> **T56** — Même tableau : « **Le matériau de la bibliothèque** — `member_check_tab_form.py` (`grade_box` remplacé par la bulle et son menu), la source (`material`, `loading`), `member_check.compute` (les valeurs lues) — **Change le contrat de la source : `schema_version` monte**, avec la lecture des sources 1.0 à 1.2 (`grade` reste lu). La bibliothèque vient de l'onglet Matériaux (#110) et de la copie que le projet en garde. » ; « Les panneaux — `calc/norms/` (SIA 265/1, tableaux 19a et 19b), le moteur — Les valeurs par sollicitation, direction et plage d'épaisseur ; une vérification qui manque d'une valeur le dit et ne se calcule pas. » ; « L'Affichage — l'onglet, l'aperçu que l'onglet compile déjà (`request_preview`, `structure_preview`), les options dans la source — La commande `#include domain-file("check", id)` ; les options d'affichage dans la source. »
>
> **T57** — Demandes, domaine : « La source porte le matériau choisi dans la bibliothèque (son identifiant), la sollicitation d'un panneau (`plaque`, `voile`, `tc` × `par`, `perp`), et les options d'affichage ; nouveau `schema_version`, lecture des anciennes versions, schéma dans `schemas/`. »
>
> **T58** — « `compute` lit la résistance du matériau choisi : SIA 265 tableaux 8 et 9 comme aujourd'hui ; un bois personnel par ses valeurs de dimensionnement (saisies ou déduites, #110) ; un panneau par SIA 265/1 tableaux 19a et 19b, selon sa sollicitation et la plage de son épaisseur. »
>
> **T59** — « Une vérification dont le matériau ne donne pas une résistance nécessaire n'est pas calculable, avec sa raison (le nom du matériau, la sollicitation, la grandeur qui manque). L'épaisseur d'un panneau hors de ses plages : pas calculable, avec les plages. »
>
> **T60** — « σ<sub>90,d</sub> hors de −f<sub>c,90,d</sub> … f<sub>t,90,d</sub> : une note orange. Le fichier `Timber-checks/<Sorte>/<id>.typ` cite la norme du matériau (SIA 265/1 tableau 19b pour un panneau) et son nom dans la ligne de l'élément. »
>
> **T61** — « Les tests : C24, GL24h, OSB/3 dans chaque sollicitation et chaque plage (dont 18 mm à la limite de deux plages), un bois personnel complet et incomplet, un panneau en compression ⊥ (pas calculable) ; les 13 vérifications du projet d'exemple inchangées. »
>
> **T62** — Demandes, onglets : « Traction, Compression, Flexion, Cisaillement, séparés ; la barre ne nomme que l'onglet. » ; « L'en-tête : la bulle du matériau, son menu groupé avec recherche, la rangée « Sollicitation » toujours présente (les bulles d'un panneau telles que validées pour l'OSB/3 ; une bulle cochée pour un bois en barre), la ligne « La vérification lit … ». » ; « Suivre la position, l'écraser (orange), « Reprendre ». » ; « La compression sans l'avertissement de stabilité ; la flexion avec son schéma SIA et les valeurs aux bords. » ; « Le Cisaillement en trois figures, « Cisaillement d'about » dans la fenêtre. » ; « Les résultats dans l'ordre du calcul, η en dernier, le cadre pointillé de la ligne qui gouverne. » ; « L'Affichage : l'aperçu Typst, le niveau, les options enregistrées dans la source, la commande `#include domain-file("check", id)` à copier, le fichier. »
>
> **T63** — Demandes, partout : « Les mots en de, fr et en (`tests/test_i18n.py`) ; les tests du domaine et des onglets ; une ligne au catalogue des tests. » ; « La documentation : `docs/domain/member-checks.md`, `docs/ui/tab-member-checks.md`, `docs/ui/window.md` ; `docs/decisions.md` §13 (la fin de Q-010, le matériau de la bibliothèque) ; `CHANGELOG.md` ; la page « Nouveautés » en trois langues. »
>
> **T64** — « Une copie du prototype dans `docs/requirements/prototypes/2026-10-24-verifications-elements/`, lue par `action: "read"` sur l'artefact de la version 3. »
>
> **T65** — Points à étudier : « **η<sub>w</sub> et η<sub>t</sub> pour un panneau.** Le prototype applique aux valeurs du tableau 19b les mêmes facteurs qu'à une barre. **À lire dans SIA 265/1 avant d'écrire Woodcore** (ExternalFiles/000-Normes/), pas de mémoire : quel facteur d'humidité et de durée vaut pour un panneau, et si les valeurs du tableau 19b sont déjà des valeurs de dimensionnement. »
>
> **T66** — « **L'épaisseur d'un panneau** : le plus petit côté de la section, comme le prototype, ou une épaisseur saisie à part. En voile, l'épaisseur est b et la hauteur h ; en plaque, l'inverse. »
>
> **T67** — « **Les vérifications qu'un panneau peut faire** dans ce premier lot : flexion en plaque et en voile, traction et compression ∥ et ⊥, cisaillement en plaque et en voile ; ni compression ⊥ au fil, ni stabilité, ni cisaillement d'about. »
>
> **T68** — « **k<sub>h</sub> pour un panneau** : le prototype n'en applique pas (famille « Platte »). À confirmer dans la norme. »
>
> **T69** — « **L'identifiant d'un matériau** dans la source : celui de la bibliothèque (#110), stable entre versions, et la copie que le projet en garde. »
>
> **T70** — « **La position** : aujourd'hui elle donne une classe (`strength_class` ou `material`). Dit-elle demain un matériau de la bibliothèque, et une sollicitation ? »
>
> **T71** — « **La synthèse** (onglet « Synthèse ») lit les résultats : elle doit dire le matériau d'un panneau avec sa sollicitation. »
>
> **T72** — Liens : « **#110** : l'onglet Matériaux, dont cette vérification lit la bibliothèque (bois massif, lamellé-collé, panneaux, personnels). **#111** : l'onglet Poids propre et surcharge, l'autre lecteur de la bibliothèque. **#105, #106** : les types Éditeur et Données. **#38** : le flambement, le déversement et l'effort tranchant, la première version de ces vérifications. **#46** : la vérification au feu, qui porte `fire` dans la même source. »
