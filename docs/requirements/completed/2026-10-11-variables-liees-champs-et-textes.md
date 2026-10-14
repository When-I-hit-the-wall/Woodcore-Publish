---
id: 2026-10-11-variables-liees-champs-et-textes
titre: Variables liées aux champs de saisie, et outil Texte des moteurs de dessin
status: completed
cree: 2026-10-11
mis_a_jour: 2026-10-11
source: transcription dictée (issues GitHub #42 et #43)
docs: [docs/ui/tab-variables.md, docs/ui/tab-member-checks.md, docs/ui/tab-connectors.md, docs/ui/tab-polar-moments.md, docs/ui/tab-static-models.md, docs/ui/tab-schemas.md, docs/ui/tab-plans.md, docs/ui/tab-fire-plan.md, docs/architecture/principles.md]
---

# Variables liées aux champs de saisie, et outil Texte des moteurs de dessin — Spécification

## 1. Objectif

L'ingénieur veut qu'une valeur saisie dans un onglet (un effort, une dimension, une charge, une coordonnée) puisse être **liée à une variable** au lieu d'être tapée : un petit bouton à droite du champ ouvre l'onglet *Variables*, qui ne propose que les variables d'unité compatible, et le champ suit ensuite la variable. Il veut aussi, dans les quatre moteurs de dessin, un **outil Texte** dont le texte peut contenir des variables. But : plus aucune valeur recopiée à la main entre un calcul et un autre (`CLAUDE.md`, « One source of truth »).

## 2. Source

Dictée de l'ingénieur du 11.10.2026, mot pour mot (rangée dans les issues #42 et #43) :

> **T1** — « Je souhaite ajouter une fonctionnalité à Woodcore. Qui est de pouvoir entrer des variables dans les champs qui nécessitent en fait de mettre des valeurs dans les onglets. »
>
> **T2** — « Donc par exemple, dans l'onglet traction, lorsque je dois indiquer les newtons ou kilonewtons, eh bien à droite de la textbox, il doit y avoir les petits boutons. »
>
> **T3** — « Et lorsque l'on clique sur ce bouton, on saute dans l'onglet variable. Tous les autres onglets sont grisés, inaccessibles. L'on saute dans l'onglet variable et l'on peut sélectionner une variable. »
>
> **T4** — « Il ne doit être affiché que les variables dont l'unité fait sens pour la valeur que l'on doit remplir. Donc si l'on doit rentrer une valeur en kilonewton, ne doivent rester affichées que les variables qui sont en kilonewton, en newton, enfin en tout cas dans une unité équivalente. »
>
> **T5** — « Il faut faire cela partout où cela fait sens. »
>
> **T6** — « Pour la classe humidité, on ne doit pas pouvoir lier une variable, »
>
> **T7** — « mais on doit pouvoir lier des variables pour les dimensions également. »
>
> **T8** — « On doit pouvoir lier une variable également dans les schémas, donc dans les charges. »
>
> **T9** — « Et d'ailleurs dans tous les moteurs de dessin, partout où l'on dessine, donc par exemple les schémas, les systèmes statiques, les plans de position et les branch routes [Brandschutz : plan de protection incendie, confirmé], il doit y avoir un outil de texte qui permet d'écrire du texte »
>
> **T10** — « et un outil variable qui permet d'afficher une variable. Ou alors uniquement un outil texte, mais dans l'outil texte, quand on est dans la modification de l'outil texte, dans le volet de droite, on doit pouvoir y mettre une variable, avoir un bouton pour y mettre une variable. »

## 3. Exigences fonctionnelles

### REQ-001 — Lier un champ à une variable
- **Exigence** : Woodcore doit permettre de remplacer la valeur tapée d'un champ numérique par un **lien** vers une variable de l'export, enregistré dans le fichier source de l'objet (vérification, assemblage, moment polaire, charge, système statique) à la place du nombre.
- **Source** : T1, T2 ; D-03
- **Priorité** : doit
- **Critère d'acceptation** : sur `tests/projet-exemple/`, l'effort N d'une vérification *Traction* lié à une variable de charge est enregistré comme lien dans `checks/<id>.json` (le fichier se valide contre `member-check-source` à sa nouvelle version), et `data/checks.json` exporté porte la valeur de la variable.

### REQ-002 — Lien vivant
- **Exigence** : Woodcore doit résoudre un lien **à chaque export** contre les domaines calculés dans ce même export, et l'afficher dans la fenêtre avec la valeur courante, sans jamais figer de copie.
- **Source** : T1 ; D-03
- **Priorité** : doit
- **Critère d'acceptation** : un test change la valeur de la variable source, réexporte, et lit la nouvelle valeur dans l'export de l'objet lié.

### REQ-003 — Filtre par unité compatible
- **Exigence** : pendant le choix, l'onglet *Variables* ne doit montrer que les variables **numériques** dont l'unité a la **même dimension** que celle du champ (kN ↔ N ↔ MN ; kNm ↔ Nmm ; mm ↔ m ; kN/m² ↔ N/mm²…). La dimension est calculée par l'algèbre d'unités existante (`calc/units.py`, `lib/units.json`), jamais par une liste écrite à la main.
- **Source** : T4
- **Priorité** : doit
  Règle des angles et des grandeurs sans dimension (Q-008, D-15) : un champ en ° n'accepte qu'une variable en ° ; un champ sans unité (β) n'accepte qu'une variable dont l'unité est vide, jamais une variable en rad (que `lib/units.json` tient pour adimensionnelle).
- **Critère d'acceptation** : un test unitaire donne la compatibilité de paires d'unités (kN/N oui, kN/kNm non, mm/m oui, ° / ° oui, ° / rad non, sans unité / rad non, sans unité / sans unité oui) ; dans la fenêtre, pour un champ en kN, aucune variable en kNm ou en mm n'est listée.

### REQ-004 — Conversion d'unité
- **Exigence** : la valeur d'une variable d'unité équivalente doit être **convertie** dans l'unité du champ (une variable de 12 500 N donne 12.5 dans un champ en kN).
- **Source** : T4 (inférée : « une unité équivalente » n'a de sens qu'avec la conversion)
- **Priorité** : doit
- **Critère d'acceptation** : test unitaire N → kN, Nmm → kNm, m → mm, kN/m² → N/mm².

### REQ-005 — Facteur et décalage
- **Exigence** : un lien doit porter un **facteur** et un **décalage** facultatifs : valeur = facteur × variable + décalage (par défaut 1 et 0), comme l'intensité d'une charge des *Systèmes statiques* aujourd'hui.
- **Source** : D-04
- **Priorité** : doit
- **Critère d'acceptation** : N = 1.5 × q + 2 donne la bonne valeur à l'export et dans la fenêtre.

### REQ-006 — Variable disparue
- **Exigence** : un lien dont la variable n'existe plus (domaine supprimé, variable renommée, unité devenue incompatible) doit garder la **dernière valeur connue**, enregistrée avec le lien (`last`). Cette valeur est écrite **par la fenêtre** à chaque enregistrement et jamais par l'export, qui ne modifie aucun fichier source (D-14). Il doit le signaler par un **avertissement** à l'export (nommant l'objet, le champ et la variable), dans la fenêtre (champ en couleur d'avertissement) et dans le rapport (sa liste d'avertissements). Ce n'est jamais un arrêt.
- **Source** : D-06 ; `CLAUDE.md` « A missing input warns »
- **Priorité** : doit
- **Critère d'acceptation** : un test supprime la variable, réexporte et obtient la dernière valeur plus un avertissement ; l'export ne s'arrête pas.

### REQ-007 — Boucles refusées
- **Exigence** : Woodcore doit refuser un lien qui crée une boucle (une charge de neige liée à une variable qui dépend d'elle-même, directement ou par une chaîne). Le refus se produit au moment du choix, avec un message, et à l'export, qui s'arrête en nommant la chaîne (un fichier écrit par Woodcore ne peut pas en contenir une).
- **Source** : inférée de D-01 (les onglets de charges produisent eux-mêmes des variables)
- **Priorité** : doit
- **Critère d'acceptation** : test unitaire sur une boucle directe et une boucle à deux maillons.

### REQ-008 — Délier
- **Exigence** : un champ lié doit pouvoir être **délié** ; il redevient un champ tapé qui garde la valeur courante.
- **Source** : inférée (sans cela, un lien serait définitif)
- **Priorité** : doit
- **Critère d'acceptation** : délier puis enregistrer écrit un nombre dans le fichier source.

### REQ-009 — Périmètre des champs liables
- **Exigence** : le bouton « variable » doit être présent sur **tous les champs numériques munis d'une unité** des onglets suivants, et seulement de ceux-là :
  - *Vérifications de barres* (*Traction, Compression, Flexion, Flambage, Déversement, Effort tranchant*) : efforts (N, M_y, M_z, V_y, V_z), angle α, section (b, h, d), longueurs (l, w, l_y, l_z, a), coefficients β, σ_m,crit ;
  - *Moyens d'assemblage* : α, t, d, b, fente, a₁, f_u,k ;
  - *Moments polaires* : centre, direction, efforts d'essai N, V, M. Les efforts d'essai deviennent une donnée enregistrée du moment polaire, dans `connection-source` (D-12) ;
  - onglets de charges (*Charges permanentes, Neige, Vent*) : leurs champs numériques, liables **seulement** à d'autres variables de charges et aux domaines *Formule* qui ne dépendent que des charges (D-11) ;
  - *Systèmes statiques* : intensité d'une charge (début et fin d'une charge linéaire), coordonnées des points (x, z), largeur d'influence b_e, rigidité des ressorts et des relâchements élastiques.
  Les listes (classe d'humidité, classe de résistance, appui, élément…) et les champs de texte n'ont pas de bouton.
- **Source** : T2, T5, T6, T7, T8 ; D-01, D-02, D-05
- **Priorité** : doit
- **Critère d'acceptation** : un test parcourt les formulaires de ces onglets et vérifie qu'un bouton accompagne chaque champ numérique listé et qu'aucune liste n'en a.

### REQ-010 — Outil Texte dans les quatre moteurs de dessin
- **Exigence** : les *Schémas*, les *Systèmes statiques*, le *Plan de positions* et le *Plan de protection incendie* doivent avoir un outil **Texte**. On pose un texte sur le dessin, on l'édite dans le volet de droite, on le déplace et on le supprime. Il est enregistré dans le fichier source du dessin et imprimé dans la figure du rapport.
- **Source** : T9 ; D-07
- **Priorité** : doit
- **Critère d'acceptation** : pour chacun des quatre moteurs, un test pose un texte, enregistre, exporte et retrouve le texte dans l'export et dans le SVG de la figure.

### REQ-011 — Variable dans un texte
- **Exigence** : dans le volet de droite d'un texte, un bouton « Insérer une variable » doit ouvrir le même choix (REQ-003 sans filtre d'unité, D-08). La variable insérée s'imprime selon un choix **propre à chaque insertion** : « valeur unité » ou « symbole = valeur unité ». Elle suit la variable (lien vivant, REQ-002) et, si celle-ci disparaît, garde sa dernière valeur avec un avertissement (REQ-006).
- **Source** : T10 ; D-07, D-09
- **Priorité** : doit
- **Critère d'acceptation** : un texte « N = {lien} » exporté imprime la valeur courante ; le changement de mode d'affichage change l'impression ; une variable supprimée donne la dernière valeur et un avertissement.

### REQ-012 — Provenance d'une valeur liée
- **Exigence** : l'export d'une valeur liée doit porter sa provenance (la variable, son domaine, le facteur et le décalage), afin que la règle 5 (« provenance systématique ») soit tenue et que le rapport puisse dire d'où vient la valeur.
- **Source** : inférée de `docs/architecture/principles.md` §2 règles 1 et 5
- **Priorité** : doit
- **Critère d'acceptation** : l'export d'une vérification liée contient la référence de la variable à côté de la valeur ; son schéma d'export la décrit.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Le bouton « variable »
- **Exigence** : un petit bouton à droite de chaque champ du périmètre (REQ-009), avec une info-bulle « Lier à une variable ». Un clic ouvre l'onglet *Variables* dans son mode de choix ; la navigation latérale et Ctrl+1…9 sont désactivés jusqu'au choix ou à l'annulation (Échap ou « Annuler »). On revient ensuite à l'onglet qui a demandé.
- **Source** : T2, T3
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : clic → onglet *Variables* au premier plan, navigation désactivée ; choix → retour à l'onglet d'origine, navigation réactivée.

### UI-002 — L'aspect d'un champ lié
- **Exigence** : un champ lié montre la valeur courante, convertie, en lecture seule, ainsi que le nom de la variable (symbole et domaine) et, s'ils diffèrent de 1 et 0, le facteur et le décalage. Une action permet de modifier le facteur et le décalage, une autre de délier. Une variable disparue affiche le champ dans la couleur d'avertissement du thème (`calc/tools/theme.json`), avec « Introuvable : … ».
- **Source** : T1 ; D-04, D-06
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran sur les trois états (lié, lié avec facteur, introuvable).

### UI-003 — Filtre visible pendant le choix
- **Exigence** : pendant le choix, la barre du mode choix de l'onglet *Variables* dit pour quel champ et quelle unité on choisit (« Choisir une variable pour N [kN] »). Les variables incompatibles et les domaines des documents (registres cu/bp/rs) ne sont pas proposés.
- **Source** : T4 ; D-02
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : la liste ne contient que des variables compatibles.

### UI-004 — L'outil Texte et son volet
- **Exigence** : un bouton *Texte* dans la barre d'outils de chaque moteur. Le volet de droite d'un texte sélectionné offre le contenu, la taille (le facteur `text` existant de `figure_style`) et le bouton « Insérer une variable » ; chaque variable insérée y a son choix « valeur » / « symbole = valeur » et une action pour la retirer.
- **Source** : T9, T10 ; D-07, D-09
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran dans chacun des quatre onglets.

### UI-005 — Systèmes statiques : le bouton remplace les trois listes
- **Exigence** : l'intensité d'une charge n'a plus les trois listes domaine → instance → variable ; elle a le bouton « variable » commun (UI-001), avec facteur et décalage.
- **Source** : D-05
- **Langues** : fr / de / en
- **Critère d'acceptation** : un système statique existant dont une charge nomme une variable s'ouvre, s'affiche lié et s'exporte à l'identique.

## 5. Exigences d'architecture

### ARCH-001 — Un seul module de liens, sans Qt
- **Exigence** : la forme d'un lien, sa résolution (recherche, conversion, facteur et décalage, dernière valeur, avertissement), la compatibilité d'unités et la détection de boucle vivent **une fois**, dans un module de `calc/domains/` sans Qt. Chaque domaine et chaque onglet l'appelle et ne recalcule rien. La résolution qui existe aujourd'hui pour les charges des statiques (`calc/domains/statics.py` `resolve`, `_lookup`) passe par ce module.
- **Source** : `docs/architecture/principles.md` §2 ; `CLAUDE.md` « Domain logic is independent of the UI »
- **Critère d'acceptation** : `grep` ne trouve qu'une résolution de lien ; le module n'importe pas Qt (`tests/test_module_imports.py`).

### ARCH-002 — Un seul widget « champ liable »
- **Exigence** : le bouton, l'affichage lié et l'action « délier » forment un widget commun de `calc/tools/`, que chaque formulaire demande. Le mode de choix de la fenêtre (`MainWindow.begin_variable_pick`) est généralisé : il revient à l'onglet qui a demandé, et non plus toujours à l'onglet *Formule*, et il accepte un filtre (unité, numérique seulement, export seulement).
- **Source** : `docs/architecture/principles.md` règle 16 (« built once and asked for by hook »)
- **Critère d'acceptation** : les cinq familles d'onglets utilisent la même classe ; l'onglet *Formule* garde son import.

### ARCH-003 — Un objet Texte commun aux moteurs
- **Exigence** : l'objet Texte (données, validation, rendu SVG, résolution de ses variables) est écrit une fois et partagé par les quatre moteurs. Les deux plans le reçoivent par `DrawingTab` / `PlanCanvas` ; les *Schémas* et les *Systèmes statiques* l'emploient par le même module de domaine et le même volet. Toute différence entre moteurs est écrite à côté de sa raison (règle 16).
- **Source** : T9 ; `docs/architecture/principles.md` règle 16
- **Critère d'acceptation** : un seul module de domaine pour le texte ; les quatre `*_svg.py` l'appellent.

### ARCH-004 — Contrats versionnés
- **Exigence** : chaque schéma source qui accepte un lien ou un texte voit sa `schema_version` augmentée, et l'ancienne version reste lue (un nombre reste un nombre) : `member-check-source`, `connector-source`, `connection-source`, `dead-load-source`, `snow-source`, `wind-source`, `statics-source`, `schema-source`, `plan-source`, `fire-source`, ainsi que les schémas d'export qui portent la provenance (REQ-012) ou les textes. L'ancienne forme de la référence des statiques `{domain, instance, var}` reste lue.
- **Source** : `docs/architecture/principles.md` règles 8, 9 et 10
- **Critère d'acceptation** : les fichiers de `tests/projet-exemple/` de l'ancienne version se lisent et s'exportent sans changement de résultat.

### ARCH-005 — Ordre de l'export
- **Exigence** : l'export garde ses étapes. Ce qu'un consommateur peut nommer est fixé par un tableau **consommateur → sources permises**, écrit une fois dans le module de liens, que le choix (filtre) et l'export (validation) lisent tous les deux (D-11, revue ARCH-RISK-001) :

  | Consommateur | Sources permises | Résolu |
  |---|---|---|
  | Onglets de charges | autres charges ; domaines *Formule* qui ne nomment que des charges | à la fin de `build_calculations`, par tri des charges entre elles ; une boucle arrête l'export |
  | Vérifications de barres, moyens d'assemblage, moments polaires, systèmes statiques, textes des dessins | toute variable de l'export : charges, assemblages, moyens d'assemblage, scripts, *Formule* | après le calcul de toutes les variables de l'export : les scripts et les domaines *Formule* sont calculés **avant** les consommateurs, en mémoire, contre l'export en cours (jamais relus sur le disque, ARCH-RISK-003) |

  Un moyen d'assemblage et un moment polaire ne se nomment pas l'un l'autre (ce sont des consommateurs, pas des sources, pour les champs liés ; leurs variables restent des sources pour les autres consommateurs). Rien n'est écrit avant que tout soit résolu (le principe actuel de `export_all.run`).
- **Source** : inférée de D-02 et de `calc/export_all.py` ; D-11 ; revue
- **Critère d'acceptation** : un test lie une vérification à une variable de script, un système statique à une variable d'assemblage et un champ de vent (q_p0) à une variable de charges permanentes ; les trois sont résolus. Un champ de neige lié à une variable de script est refusé au choix et à l'export. *(Corrigé le 11.10.2026 à la vérification du lot 2 : le critère écrivait « un champ de neige » ; aucun champ de neige n'a la dimension des variables d'une charge permanente, toutes en kN/m², et le filtre d'unités le refuserait. Le cas est donc un champ de vent en kN/m².)*

### ARCH-006 — Un seul moteur de texte des figures, un seul lecteur de symboles
- **Exigence** : le texte à indices des figures (`text_runs`, `text_width`, `_text`, tables de largeurs) vit dans un seul module sans Qt, `calc/domains/svg_text.py`. `statics_svg_layout`, `schema_svg` (aujourd'hui une copie) et `plan_svg` l'appellent et réexportent ses noms. L'analyseur du Typst math des symboles (`richtext.math_html`, aujourd'hui en Qt) est extrait dans un module sans Qt (`calc/typst_math.py`) avec deux sorties : HTML pour la fenêtre, dialecte de figure pour le SVG. La valeur d'une variable s'imprime dans une figure par la seule fonction de nombre des figures (`figure_number`).
- **Source** : revue, ARCH-RISK-101, 102 et 103 ; règle 1
- **Critère d'acceptation** : `grep` ne trouve qu'un `text_runs` ; les SVG existants restent identiques octet pour octet (test) ; tous les symboles de `tests/projet-exemple/` donnent le même résultat par `typst_math` que par l'ancien `math_html`.

### ARCH-007 — Les valeurs vont jusqu'au rendu, fenêtre comprise
- **Exigence** : les valeurs de l'export sont passées à `prepare` et au rendu de chaque dessin (`plan.prepare/export`, `fire.prepare`, `schema.prepare`, `statics.prepare` ; `plan_svg.render`, `fire_svg.render`, `schema_svg.layout`), et la fenêtre les lit par une seule fonction du module de liens, qui remplace `statics.known_values`. Les textes se résolvent une fois, et la fenêtre comme l'export affichent ce même résultat. Le facteur `text` de `figure_style` est admis sur la nouvelle collection `texts` des quatre moteurs (`ENTRY_KEYS`). Aucune commande ni aucun argument Typst n'est ajouté : un texte est imprimé dans le SVG que Typst pose déjà.
- **Source** : revue, ARCH-RISK-104, 106 et 111
- **Critère d'acceptation** : une variable modifiée change la figure dans la fenêtre et à l'export ; un plan sans texte donne un SVG identique à celui d'avant.

## 6. Contraintes

- **CON-001** — Trois langues : chaque mot visible existe en de, fr et en, dans les glossaires des onglets (`*_words.py`) ou dans `calc/i18n/`. Source : `CLAUDE.md`.
- **CON-002** — Aucun code Typst n'est montré dans Woodcore (règle 15) : un lien se montre par le symbole et le domaine de la variable, jamais par `var-of(...)`.
- **CON-003** — Les unités viennent de `lib/units.json` à travers `calc/units.py` (une seule algèbre d'unités, celle de `lib/formula.typ`). Source : `CLAUDE.md` « No hardcoding ».
- **CON-004** — Les couleurs (avertissement) viennent de `calc/tools/theme.json`.
- **CON-005** — Seules les variables de l'export sont liables (D-02).
- **CON-006** — Documentation : `docs/ui/tab-variables.md`, `tab-member-checks.md`, `tab-connectors.md`, `tab-polar-moments.md`, `tab-static-models.md`, `tab-schemas.md`, `tab-plans.md`, `tab-fire-plan.md`, la page de domaine des liens (nouvelle, sous `docs/domain/`), une entrée `CHANGELOG.md`, la page « Nouveautés » en fr/de/en, une ligne par nouveau fichier de test dans `docs/conventions/testing-catalogue*.md`, et la décision de forme du lien dans `docs/decisions.md` (§13).

## 7. Décisions prises

- **D-01** (11.10.2026, Q1) — Périmètre : *Vérifications de barres*, *Moyens d'assemblage*, *Moments polaires*, onglets de charges et *Systèmes statiques*. **Pas** les cotes de l'onglet *Schémas* ni l'onglet *Positions*.
- **D-02** (Q3) — Seules les variables **de l'export** (data/calculations.json, assemblages, moyens d'assemblage, scripts, domaines *Formule*) sont liables, résolues par Python sans compilation. Prix accepté : les variables définies seulement dans les `.typ` d'un document ne sont pas proposées.
- **D-03** (issue #42, question 3) — **Lien vivant**, jamais une copie.
- **D-04** (Q4) — Un lien porte **facteur et décalage**, comme les charges des statiques.
- **D-05** (Q2, Q5) — Les « charges des schémas » de la dictée sont celles des *Systèmes statiques*. Le bouton commun y **remplace** les trois listes. Sont liables dans les statiques : l'intensité des charges, la géométrie (coordonnées, b_e) et les ressorts.
- **D-06** (Q6) — Une variable disparue : **dernière valeur connue + avertissement**, jamais un arrêt.
- **D-07** (issue #43, question 1) — **Un seul outil Texte**, avec un bouton « Insérer une variable » dans son volet ; pas d'outil Variable séparé.
- **D-08** (inférée de D-07) — Une variable insérée dans un texte n'a pas de filtre d'unité, mais seulement les variables de l'export, comme D-02.
- **D-09** (Q7) — L'impression d'une variable dans un texte se choisit **par insertion** : « valeur unité » ou « symbole = valeur unité ».
- **D-10** (issue #43, question 2) — « branch routes » dans la dictée = *Brandschutz*, le *Plan de protection incendie*.
- **D-11** (Q-009) — Un champ d'un onglet de charges ne se lie qu'à **d'autres charges** et aux domaines *Formule* qui ne dépendent que des charges. L'ordre de l'export ne change pas pour les charges. Prix accepté : on ne peut pas lier une charge à un assemblage ou à un script.
- **D-12** (Q-010) — Les efforts d'essai N, V, M des *Moments polaires* deviennent une **donnée enregistrée** du moment polaire (`connection-source`, champ additif), pour pouvoir les lier.
- **D-13** (Q-011) — Un texte de dessin s'enregistre comme une **chaîne à jetons** : `"text": "N = {1}"` et `"vars": {"1": {lien…, "show": "value"|"symbol"}}`. Une accolade littérale s'écrit `{{` ; un jeton sans variable est un défaut de fichier, qui arrête l'export en nommant le fichier et le champ.
- **D-14** (revue, ARCH-RISK-008/105) — La dernière valeur connue d'un lien (`last`) est écrite par la fenêtre à l'enregistrement, **jamais par l'export**, qui ne touche aucun fichier source.
- **D-15** (revue, ARCH-RISK-002) — Compatibilité des unités : même dimension selon `calc/units.py`. Un champ en ° n'accepte que des °, et un champ sans unité n'accepte qu'une unité vide (pas de rad). `lib/units.json` n'est pas modifié.
- **D-17** (11.10.2026, question posée au début du lot 1) — Un lien s'enregistre **à côté** du champ, et non à sa place. Le nombre (ou le bloc `{value, unit}`) reste où il est et vaut **dernière valeur connue** (D-06, D-14). Un objet `links` de l'entrée nomme, par clé de champ (`"N"`, `"alpha"`, `"section.b"`, `"x"`, `"width"`, `"stiffness"`), la variable : `{"domain", "instance", "var", "factor"?, "offset"?, "origin"?}`. `origin` vaut `"formulas"` pour un domaine de l'onglet *Formule* (son id dans `instance`) et est absent pour l'export. L'intensité d'une charge des statiques garde sa forme de référence existante `{domain, instance, var, factor, offset}`, à laquelle s'ajoute `last` (additif). Pourquoi : chaque lecteur de nombre (validation, `compute`, canevas, dessins) reste juste sans substitution, et le diff est bien plus petit. Ce que cela coûte : la fenêtre et l'export doivent réconcilier le nombre avec la variable, ce que fait le module de liens.
- **D-18** (11.10.2026, à l'implémentation du lot 2, précision d'ARCH-005) — Un moyen d'assemblage et un moment polaire **ne suivent aucun assemblage** (`links.JOINTS`) : ils produisent eux-mêmes des variables et sont construits avant les autres consommateurs. Ils suivent une charge, un script ou un domaine *Formules*, et l'export calcule les scripts et l'index *Formules* avant eux. Le tableau d'ARCH-005 disait « toute variable de l'export » pour eux ; c'est précisé ici, avec son prix : passer par un domaine *Formules* ne suffit pas pour relier deux assemblages.
- **D-19** (11.10.2026, au début du lot 3) — **Un seul moteur de texte des figures**, celui des statiques : sa table de largeurs Arial, sa découpe des indices, sa mesure et sa pose (`calc/domains/svg_text.py`). Les schémas l'emploient aussi, comme l'objet Texte des quatre moteurs. La revue d'architecture tenait le moteur des schémas pour une copie inchangée de celui des statiques ; ce n'en était pas une : la table de largeurs diffère (« m » 0,7222 contre 0,833 em) et la pose des indices aussi. Prix accepté par l'ingénieur : les étiquettes des schémas déjà dessinés bougent légèrement (largeurs, position des indices). Le critère d'ARCH-006 (« SVG existants identiques ») ne vaut donc plus que pour les statiques, et les plans gardent leur propre texte pour leurs étiquettes.
- **D-16** (Q-012) — Livraison en **trois lots**, chacun commité et vérifié, l'ingénieur pouvant arrêter ou corriger entre deux : lot 1 = module de liens, mode choix, *Vérifications de barres*, *Systèmes statiques* ; lot 2 = *Moyens d'assemblage*, *Moments polaires*, onglets de charges ; lot 3 = outil Texte dans les quatre moteurs.

## 8. Hors périmètre

- La classe d'humidité (T6), et plus généralement toute liste de choix (classe de résistance, appui, élément, type…).
- Les cotes et les angles de l'onglet *Schémas* (D-01) ; l'onglet *Positions*.
- Les variables définies seulement dans les documents (registres cu/bp/rs, D-02).
- Un outil Variable séparé dans les moteurs de dessin (D-07).
- Les champs de texte libre (noms, libellés, descriptions).

## 9. Idées non retenues comme exigences

- T10, première moitié (« un outil variable qui permet d'afficher une variable ») : l'ingénieur a choisi l'autre branche de son alternative (D-07).

## 10. Questions

### Q-001 — Quels onglets reçoivent le bouton ?
- **Réponse** : Vérifications de barres, Assemblages et moments polaires, onglets de charges, « onglet structure statique » (11.10.2026) → D-01.

### Q-002 — « Dans les schémas, donc dans les charges » ?
- **Réponse** : les *Systèmes statiques*, où le bouton remplace les trois listes (11.10.2026) → D-05.

### Q-003 — Quelles variables sont liables ?
- **Réponse** : celles de l'export (11.10.2026) → D-02.

### Q-004 — Facteur et décalage ?
- **Réponse** : oui (11.10.2026) → D-04.

### Q-005 — Quoi lier dans les statiques en plus des charges ?
- **Réponse** : la géométrie et les ressorts (11.10.2026) → D-05.

### Q-006 — Variable disparue ?
- **Réponse** : dernière valeur et avertissement (11.10.2026) → D-06.

### Q-007 — Impression d'une variable dans un texte ?
- **Réponse** : au choix, par variable insérée (11.10.2026) → D-09.

### Q-008 — Angles (°) et grandeurs sans unité (β)
- **Pourquoi elle compte** : la compatibilité d'unités (REQ-003) doit savoir si un angle accepte une variable en rad, et si un champ sans dimension accepte toute variable sans dimension.
- **Réponse** : la revue a montré que `lib/units.json` tient rad pour adimensionnel et ° pour une dimension propre. Tranché sans changer ce fichier → D-15.

### Q-009 — À quoi un champ de charges peut-il se lier ?
- **Pourquoi elle compte** : les charges sont calculées en tout premier à l'export (`build_calculations`).
- **Options** : A (recommandée) charges et *Formule* seulement, ordre inchangé ; B tout, export réordonné en passes.
- **Réponse** : A (11.10.2026) → D-11.

### Q-010 — Efforts d'essai des moments polaires
- **Pourquoi elle compte** : ce sont des options d'affichage, non enregistrées dans `connections/<id>.json`.
- **Options** : A (recommandée) non liables ; B enregistrés pour être liables.
- **Réponse** : B (11.10.2026) → D-12.

### Q-011 — Forme enregistrée d'un texte à variables
- **Options** : A (recommandée) chaîne à jetons `{1}` + `vars` ; B liste de morceaux (`runs`).
- **Réponse** : A (11.10.2026) → D-13.

### Q-012 — Livraison
- **Options** : A (recommandée) trois lots ; B tout d'un coup.
- **Réponse** : A (11.10.2026) → D-16.

## 11. Critères d'acceptation

- [x] REQ-001 — un champ lié s'enregistre comme lien et se valide contre le schéma source à sa nouvelle version
- [x] REQ-002 — la valeur suit la variable d'un export à l'autre
- [x] REQ-003 — seules les variables numériques d'unité compatible sont proposées (test de compatibilité d'unités)
- [x] REQ-004 — conversion N→kN, Nmm→kNm, m→mm, kN/m²→N/mm²
- [x] REQ-005 — facteur × variable + décalage
- [x] REQ-006 — variable disparue : dernière valeur et avertissement, pas d'arrêt
- [x] REQ-007 — boucles refusées au choix et à l'export
- [x] REQ-008 — délier rend un nombre
- [x] REQ-009 — bouton sur chaque champ numérique du périmètre, jamais sur une liste
- [x] REQ-010 — texte posé, enregistré, exporté et imprimé dans les quatre moteurs
- [x] REQ-011 — variable dans un texte : vivante, mode d'affichage par insertion, dernière valeur et avertissement
- [x] REQ-012 — provenance d'une valeur liée dans l'export
- [x] UI-001 — mode choix : navigation désactivée, retour à l'onglet d'origine
- [x] UI-002 — trois états d'un champ lié
- [x] UI-003 — barre de choix nommant le champ et l'unité ; liste filtrée
- [x] UI-004 — outil et volet Texte dans les quatre moteurs
- [x] UI-005 — statiques : bouton à la place des trois listes, anciens fichiers identiques
- [x] ARCH-001 — une seule résolution, sans Qt
- [x] ARCH-002 — un seul widget, `begin_variable_pick` généralisé
- [x] ARCH-003 — un seul objet Texte
- [x] ARCH-004 — schémas versionnés, anciennes versions lues
- [x] ARCH-005 — tableau consommateur → sources permises, tenu au choix et à l'export
- [x] ARCH-006 — un seul `text_runs`, un seul lecteur de symboles, SVG existants identiques
- [x] ARCH-007 — valeurs passées jusqu'au rendu ; `texts` admis par `figure_style` ; aucune commande Typst ajoutée
- [x] Documentation : sections de `docs/` mises à jour, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en, catalogue des tests, décision dans `docs/decisions.md`.
- [x] Tests : fichiers `tests/test_*.py` ajoutés ou étendus, et passent ; suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-002, UI-002 | capturé |
| T2 | REQ-009, UI-001 | capturé |
| T3 | UI-001 | capturé |
| T4 | REQ-003, REQ-004, UI-003 | capturé |
| T5 | REQ-009 ; D-01 | capturé |
| T6 | §8 Hors périmètre | exclu |
| T7 | REQ-009 (section, longueurs, géométrie des statiques) | capturé |
| T8 | REQ-009, UI-005 ; D-05 | capturé (ambigu → Q-002 résolue) |
| T9 | REQ-010, UI-004, ARCH-003 ; D-10 | capturé |
| T10 | REQ-011, UI-004 ; D-07, D-09 ; §9 | capturé |

### Points de la source non résolus

Aucun.

Correction de l'issue #43 : elle disait que le *Plan de positions* avait déjà un objet *Texte*. C'est faux : son « Texte » n'est que le curseur de taille des textes (`plan_style_text`, facteur `text` de `figure_style`). Aucun des quatre moteurs n'a d'objet Texte aujourd'hui.

## 13. Revue d'architecture

Deux relecteurs indépendants (`architecture-reviewer`), le 11.10.2026 : l'un pour les liens, l'autre pour l'objet Texte. **Verdict des deux : APPROUVER AVEC RÉSERVES.** Toutes les réserves sont reportées ci-dessous et traitées dans la spec ou dans le plan.

### Existant à réutiliser

- **Mode choix** : `MainWindow.begin_variable_pick` (`calc/tools/woodcore_gui.py:865`, retour codé vers `FormulaTab`, aucun filtre) et `VariablesTab.begin_pick/end_pick/pick_chosen` (`calc/tools/variables_tab.py:918-935`), à généraliser (onglet demandeur, filtre `accept`).
- **Unités** : `calc/units.py` `parse_unit` (l.132, facteur et dimensions), `dims_equal` (l.59), `dimension_of` (l.158). La conversion vaut `valeur × f_src / f_dst`.
- **Résolution existante** : `calc/domains/statics.py:740-823` `values_of`, `known_values`, `_lookup`, `resolve` (facteur, décalage, `engine.Note` quand la variable manque). À déplacer dans le module de liens, que `statics` appelle ensuite.
- **Boucles** : `formula_domain.resolve_import` et `CIRCLE` (l.905-947), une pile qui nomme la chaîne. Le motif est à généraliser.
- **Versions** : le motif `SOURCE_SCHEMA_VERSIONS = (…anciennes, courante)` (`plan.py:115`, `statics.py:85`, `fire.py:41`, `schema.py:139`).
- **Avertissements** : `engine.Note` ; `member_check.warnings_of` (l.1059) imprime déjà les avertissements d'une vérification.
- **Figures** : `statics_svg._text`, `text_runs`, `text_width` ; `statics_svg_layout.place` (étiquettes multi-lignes, `label_offset`, `hit_label`) ; `figure_style` ; le motif additif `dimensions` du plan (marqueurs écrits seulement s'il y a une cote) ; `DrawingTab.add_module(…, when=…)` ; la puce de `object_panes_fields.CellField` pour l'affichage d'une variable choisie.

### Risques et leur traitement

| Risque | Gravité | Objet | Traitement |
|---|---|---|---|
| ARCH-RISK-001 | bloquant | Les charges sont calculées en premier : un graphe général des dépendances n'est pas réalisable sans réordonner l'export. | D-11 et ARCH-005 (tableau consommateur → sources). |
| ARCH-RISK-002 | bloquant | ° et rad dans `lib/units.json`. | D-15, REQ-003. |
| ARCH-RISK-003 | important | Les domaines *Formule* sont calculés à la lecture, contre le `calculations.json` du disque. | ARCH-005 : calcul en mémoire contre l'export en cours (plan, lot 1, étape 3). |
| ARCH-RISK-004 | important | Égalité stricte de `schema_version` dans chaque `check_source` ; chaque validateur de nombre refuserait un lien. | Motif `SOURCE_SCHEMA_VERSIONS` ; un seul validateur « nombre ou lien » dans `links.py` ; version haute écrite seulement si le fichier porte un lien. |
| ARCH-RISK-005 | important | Les efforts d'essai polaires ne sont pas enregistrés. | D-12 (lot 2). |
| ARCH-RISK-006 | important | Cinq fonctions `spin` en double ; tous les formulaires lisent `value()`, `setValue()` et `valueChanged`. | Le widget `LinkableSpin` garde ces trois membres et devient la seule fabrique des champs du périmètre. |
| ARCH-RISK-007 | important | Provenance dans `checks.json` sans changer Typst. | `N = {value, unit}` reste plat (valeur résolue) ; un objet `links` additif à côté (export 1.0 → 1.1). Même règle pour `connectors`, `connections` et `statics`. |
| ARCH-RISK-008 / 105 | mineur / important | La dernière valeur ne doit pas être écrite par l'export. | D-14. |
| ARCH-RISK-009 | mineur | Garde de lecture seule. | Le bouton est désactivé hors écriture (`write_enabled`) ; un test le vérifie. |
| ARCH-RISK-010 | mineur | Imports circulaires. | `links.py` n'importe pas `variable_sources` ; il reçoit un dictionnaire de valeurs construit par l'appelant. |
| ARCH-RISK-101 | important | Le moteur de texte à indices existe déjà en double (`schema_svg` copie `statics_svg`). | ARCH-006 : `svg_text.py` unique. |
| ARCH-RISK-102 | bloquant | Les symboles d'export sont du Typst math (`q_(p 0)`, `"Kategorie"`, `sigma`), que seul `richtext.math_html` (Qt) sait lire. | ARCH-006 : `calc/typst_math.py` sans Qt, deux sorties. |
| ARCH-RISK-103 | important | Le format des nombres diffère entre la figure et le rapport. | ARCH-006 : `figure_number` seul ; la règle est écrite dans la page de domaine. |
| ARCH-RISK-104 | bloquant | Les valeurs n'arrivent ni à `plan.prepare`, ni à `fire.prepare`, ni aux rendus de la fenêtre. | ARCH-007. |
| ARCH-RISK-106 | bloquant | `figure_style.ENTRY_KEYS` n'a pas de ligne `texts`. | ARCH-007. |
| ARCH-RISK-107 | important | Chaque parcours de « tout ce qui est dessiné » doit connaître `texts` : `ENTRY_LISTS`, `translate_entry`, `copy_entry`, `rotate_source`, `ENTITIES`, `ENTITY_PREFIX`, `remove`, `rename`… | Lot 3, un test par moteur : poser, déplacer, copier, supprimer, tourner. |
| ARCH-RISK-108 | important | Schémas JSON en `const` (`schema-source`, les quatre exports). | `enum` des versions ; versions mineures additives (`plan-source` 1.7, `fire-source` 2.1, `statics-source` 1.2, `schema-source` 1.2 ; exports `plans` 1.4, `fire` 2.1, `statics` 1.2, `schemas` 1.2), écrites seulement s'il y a un texte. |
| ARCH-RISK-109 | mineur | `fire.TEXT_COLLECTIONS` porte un nom trompeur à côté de `texts`. | Un test tient `texts` hors de cette liste. |
| ARCH-RISK-110 | important | Règle 16 : seuls les deux plans partagent une base. | Domaine et carte du volet partagés ; seuls l'outil et la sélection sont câblés par moteur. La raison est écrite à côté du code. |
| ARCH-RISK-111 | mineur | Pas d'argument Typst nouveau. | ARCH-007 : les textes sont toujours imprimés. |
| ARCH-RISK-112 | mineur | Mots du volet Texte. | Glossaires des onglets, en de/fr/en. |

### Approche retenue

- **Forme d'un lien** : *remplacée par D-17* (lien à côté du champ, dans `links`). Forme de la revue, abandonnée : `{"link": {"origin": "export", "domain": "snow-load", "instance": "SL", "var": "q_k"}, "factor": 1, "offset": 0, "unit": "kN", "last": {"value": 12.5, "unit": "kN"}}`. Un nombre reste un nombre, ou `{value, unit}` là où c'était déjà la forme. (L'intensité des statiques garde sa forme de référence, D-17.)
- **Domaines sans Qt** :
  - `calc/domains/links.py` : `is_link`, `check_value`, `compatible`, `convert`, `resolve`, `resolve_all` (tri et boucle nommée), `legacy_reference`, `ALLOWED_SOURCES`, `known(data_dir)` ;
  - `calc/domains/figure_text.py` : texte à jetons, résolution, enregistrement, dessin ;
  - `calc/domains/svg_text.py` ;
  - `calc/typst_math.py`.
- **Fenêtre** :
  - `calc/tools/linkable_spin.py` (`LinkableSpin`) ;
  - `calc/tools/text_pane.py`, la carte du volet Texte ;
  - `begin_variable_pick(on_done, title, accept=None)`, qui revient à l'onglet demandeur ;
  - `VariablesTab.begin_pick(…, accept=None)`, qui filtre la liste et cache les registres de documents.

## 14. Plan d'implémentation

Livré en trois lots (D-16). Chaque lot se termine par ses tests, sa documentation, une vérification indépendante sur ses éléments et un commit (skill `finish`, push sur ta parole). L'ingénieur peut arrêter ou corriger entre deux lots.

### Lot 1 — module de liens, mode choix, Vérifications de barres, Systèmes statiques

1. **`calc/domains/links.py`** : forme, validation « nombre ou lien », `compatible` et `convert` sur `calc/units.py`, facteur et décalage, `last`, `Note` de variable disparue, `resolve_all` avec boucle nommée (motif de `CIRCLE`), `ALLOWED_SOURCES` (tableau d'ARCH-005), `legacy_reference`, `known(data_dir)`. → REQ-003…007, ARCH-001, ARCH-005. Test : `tests/test_links.py` (nouveau).
2. **`statics.resolve` et `_lookup` passent par `links`** ; `statics.known_values` est remplacé par `links.known`. → ARCH-001. Test : `tests/test_statics.py`, ancienne référence au résultat identique.
3. **`export_all.run`** : construit le dictionnaire des valeurs en mémoire. Les charges se résolvent à la fin de `build_calculations` (charges et *Formule* sur charges). Les scripts et les domaines *Formule* sont calculés avant les consommateurs, contre l'export en cours. Les valeurs sont passées à `member_check.prepare` et à `statics.prepare`. → ARCH-005, REQ-002. Test : `tests/test_export_all.py` (ou le fichier existant de l'export).
4. **Contrats** :
   - `member-check-source` 1.1 (accepte le lien sur chaque champ du périmètre), lu avec 1.0 (`SOURCE_SCHEMA_VERSIONS`) ;
   - export `checks` 1.1 avec `links` (provenance, `stale`) ;
   - `statics-source` 1.2 (lien sur les coordonnées, b_e, les rigidités et les intensités), avec ancienne forme lue ;
   - export `statics` 1.2.
   → ARCH-004, REQ-001, REQ-012. Tests : `tests/test_member_check.py`, `tests/test_statics.py`, octet pour octet sans lien.
5. **`member_check.prepare` et `statics.prepare` résolvent les liens** ; les avertissements de variable disparue passent par `warnings_of` et `statics.warnings`. → REQ-002, REQ-006.
6. **Mode choix** :
   - `begin_variable_pick(on_done, title, accept=None)` revient à l'onglet demandeur ;
   - `VariablesTab.begin_pick(…, accept)` filtre, cache les registres de documents, et sa barre nomme le champ et l'unité ;
   - l'onglet *Formule* garde son comportement.
   → UI-001, UI-003, ARCH-002. Tests : `tests/test_variables.py`, et le test de l'onglet *Formule*.
7. **`calc/tools/linkable_spin.py`** : `value`, `setValue`, `valueChanged`, `link`, `setLink`, bouton, état lié (symbole et domaine), facteur et décalage, délier, état introuvable (couleur `warning`), désactivé en lecture seule, `last` mis à jour par la fenêtre à l'enregistrement. → UI-002, REQ-008, D-14. Test : `tests/test_linkable_spin.py` (nouveau, hors écran).
8. **Vérifications de barres** : `MemberCheckTab.spin` et le formulaire passent par `LinkableSpin` pour les champs du périmètre ; `draft_*` écrit le lien ; `compute()` reçoit la valeur résolue. → REQ-009 (vérifications). Test : `tests/test_member_check_tab.py`, un bouton par champ et aucun sur une liste.
9. **Systèmes statiques** :
   - les trois listes de l'intensité sont remplacées par `LinkableSpin` ;
   - coordonnées, b_e et rigidités liables ;
   - les valeurs sont relues au retour du mode choix (fin de l'instantané de `statics_tab.py:138`).
   → UI-005, REQ-009 (statiques). Test : `tests/test_statics_tab.py` (ou l'existant).
10. **Documentation du lot** :
    - `docs/domain/variable-links.md` (nouveau) ;
    - `tab-variables.md`, `tab-member-checks.md`, `tab-static-models.md` ;
    - une décision dans `docs/decisions.md` (forme du lien, D-11, D-14, D-15) ;
    - `CHANGELOG.md`, la page « Nouveautés » en fr/de/en, le catalogue des tests ;
    - les mots des glossaires (de/fr/en).

### Lot 2 — Moyens d'assemblage, Moments polaires, onglets de charges

11. **Contrats** : `connector-source`, `connection-source` (efforts d'essai enregistrés, D-12), `dead-load-source`, `snow-source`, `wind-source`, chacun avec ses versions lues ; exports `connectors` et `connections` avec `links`. → ARCH-004, REQ-012.
12. **Résolution** :
    - `connector.prepare` et `connection.prepare` reçoivent les valeurs ;
    - les sources de charges se résolvent dans `build_calculations` selon `ALLOWED_SOURCES` ;
    - une boucle de charges arrête l'export en nommant la chaîne.
    → REQ-007, ARCH-005.
13. **Formulaires** : `connectors_tab_form._spin/_field`, `woodcore_gui_polar.length_box/angle_box` et les efforts d'essai, `LoadTab.spin` passent par `LinkableSpin`. → REQ-009. Tests : `tests/test_connectors*.py`, `tests/test_polar*.py`, `tests/test_load_tab.py`.
14. **Documentation du lot** : `tab-connectors.md`, `tab-polar-moments.md`, les pages des charges, `CHANGELOG.md`, la page « Nouveautés ».

### Lot 3 — outil Texte dans les quatre moteurs

15. **`calc/domains/svg_text.py`** (texte à indices unique, réexporté par `statics_svg_layout`, `schema_svg` et `plan_svg`) et **`calc/typst_math.py`** (`richtext.math_html` l'appelle). → ARCH-006. Tests : SVG existants identiques ; égalité sur les symboles du projet exemple.
16. **`calc/domains/figure_text.py`** (texte à jetons D-13, `vars`, `show`, résolution, `last`, `figure_number`, dessin) ; ligne `texts` dans `figure_style.ENTRY_KEYS`. → REQ-010, REQ-011, ARCH-003, ARCH-007. Test : `tests/test_figure_text.py` (nouveau), `tests/test_figure_style.py`.
17. **Contrats et parcours** :
    - `plan-source` 1.7, `fire-source` 2.1, `statics-source` 1.2 (déjà monté au lot 1, `texts` ajouté), `schema-source` 1.2, en `enum` ;
    - exports `plans` 1.4, `fire` 2.1, `statics` 1.2, `schemas` 1.2, écrits seulement s'il y a un texte ;
    - `texts` dans `ENTRY_LISTS`, `translate_entry`, `copy_entry`, `rotate_source`, `fire.COLLECTIONS`, `statics.ENTITIES` et `ENTITY_PREFIX` (`T`), `remove`, `rename` ;
    - les valeurs sont passées à `prepare` et aux rendus.
    → ARCH-004, ARCH-007. Tests : `tests/test_plan_texts.py` (nouveau), `test_fire*.py`, `test_statics.py`, `test_schema*.py`.
18. **Fenêtre** : `calc/tools/text_pane.py`, puis l'outil *Texte* :
    - dans `plan_tab_build.TOOLS` et `fire_tab_build.TOOLS`, le volet par `DrawingTab.add_module` ;
    - dans `statics_canvas.TOOLS` et `TOOL_GROUPS` ;
    - dans `schema_canvas_place.TOOLS` et `TOOL_GROUPS`.
    Le bouton « Insérer une variable » passe par `begin_variable_pick` sans filtre d'unité. → UI-004. Tests : un test hors écran par onglet.
19. **Documentation du lot** : `tab-plans.md`, `tab-fire-plan.md`, `tab-schemas.md`, `tab-static-models.md`, la page de domaine des textes, `CHANGELOG.md`, la page « Nouveautés ».

Ce qui **ne** sera **pas** fait : voir §8. S'y ajoutent : pas d'angle de rotation du texte (absent de la demande ; s'ajoutera sans changer le contrat), et pas de nouvel argument Typst.

## 15. Vérification

### Lot 1 (11.10.2026, `requirements-verifier`, deux tours, copie de travail contre `3cdf44c`)

Premier tour : aucun ❌, des ⚠️ sur REQ-002, REQ-006, REQ-009, REQ-012, UI-005, ARCH-001, ARCH-002, ARCH-004, ARCH-005, CON-006 et ARCH-RISK-009. Corrigés : test de l'export complet (`export_all.run`) sur une copie du projet d'exemple ; checks.json identique octet pour octet sans lien ; boutons de tous les champs des statiques ; modèle 1.1 à référence ouvert sans écriture ; bouton fermé en lecture seule. Second tour : restaient REQ-006 (bout en bout) et ARCH-001 (`statics.resolve` gardait sa propre détection), corrigés ensuite (variable disparue via `export_all.run` ; `statics.resolve` passe par `links.resolve`, en gardant ses codes d'avertissement).

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `links.py` (forme D-17), `member_check.LINKABLE`, `check_source` 1.1 ; `test_links` (check lié, export 1.1), `test_linkable_spin` (brouillon `links`) |
| REQ-002 | ✅ | `test_links.test_the_whole_export_resolves_…` via `export_all.run` ; `test_the_check_export_with_a_link_is_1_1_and_follows_the_variable` (20 000 N → 30 kN) |
| REQ-003 | ✅ | `links.compatible` sur `calc/units.py` ; `test_a_variable_fills_a_field_of_its_dimension_and_no_other` ; filtre de la fenêtre dans `test_linkable_spin` |
| REQ-004 | ✅ | `links.convert` ; `test_a_value_is_converted_into_the_field_s_unit` |
| REQ-005 | ✅ | `links.apply` ; `test_factor_and_offset_then_the_conversion` ; facteur 1,5 → 3 dans la fenêtre |
| REQ-006 | ✅ | dernière valeur + `link_stale` ; ZT-02 lié à une variable disparue via `export_all.run` : valeur gardée, `stale`, avertissement dans la liste du rapport ; « Introuvable » en couleur d'avertissement |
| REQ-007 | lot 2 | boucles impossibles au lot 1 (vérifications et statiques ne produisent aucune variable) ; `links.allowed` en place |
| REQ-008 | ✅ | `LinkableSpin.unlink` ; `test_linkable_spin` |
| REQ-009 | ✅ lot 1 | vérifications : `test_every_field_of_the_perimeter_has_its_button_and_no_list_has_one` ; statiques : `test_every_number_of_a_static_model_that_may_follow_a_variable_has_its_button` ; assemblages, polaires, charges : lot 2 |
| REQ-010, REQ-011 | lot 3 | — |
| REQ-012 | ✅ | `links` dans `checks.json` 1.1 et `statics.json` 1.2, lus après `export_all.run` |
| UI-001 | ✅ | `begin_variable_pick(…, accept)` ; `test_linkable_spin` |
| UI-002 | ✅ | `LinkableSpin.show_state` ; trois états dans `test_linkable_spin` |
| UI-003 | ✅ | `VariablesTab.begin_pick(…, accept)`, `variable_sources.linkable` ; `test_linkable_spin` |
| UI-004 | lot 3 | — |
| UI-005 | ✅ | `pick_magnitude`, listes retirées ; `test_a_model_saved_before_whose_load_names_a_variable_opens_linked_and_exports_as_it_did` |
| ARCH-001 | ✅ | `links.resolve` seule résolution (`statics.resolve` l'appelle) ; `links.py` sans Qt (`test_module_imports`) |
| ARCH-002 | ✅ lot 1 | un seul `LinkableSpin` (vérifications, statiques) ; `begin_variable_pick` généralisé ; *Formules* inchangé (`test_formula_tab`) ; trois autres familles : lot 2 |
| ARCH-003 | lot 3 | — |
| ARCH-004 | ✅ lot 1 | `SOURCE_SCHEMA_VERSIONS` ; version haute seulement avec un lien ; `test_a_project_without_a_link_exports_its_checks_and_models_as_before` |
| ARCH-005 | ✅ lot 1 | scripts et *Formules* avant les consommateurs ; vérification ← script, statique ← *Formules* et assemblage via `export_all.run` ; charges : lot 2 |
| ARCH-006, ARCH-007 | lot 3 | — |
| CON-001…005 | ✅ | mots fr/de/en (`test_i18n`) ; aucun Typst montré ; `calc/units.py` ; `theme.colour("warning")` ; registres exclus |
| CON-006 | ✅ lot 1 | `variable-links.md` §3.3duovicies, trois `tab-*.md`, `layout.md`, décision et index, catalogue, CHANGELOG, « Nouveautés » fr/de/en ; `test_docs_coherence` |
| ARCH-RISK-009 | ✅ | `LinkableSpin.read_only` ; `test_a_project_opened_read_only_closes_the_button` |

Trouvé en route, non modifié : le `data/statics.json` committé du projet d'exemple porte encore un modèle « VU » dont la source a disparu.

### Lot 2 (11.10.2026, `requirements-verifier`, deux tours, copie de travail contre `1b93581`)

Premier tour : aucun ❌, quatre ⚠️, corrigés ensuite :
- REQ-009 : test de parcours des formulaires ;
- ARCH-005 / REQ-007 : un lien interdit est un défaut de fichier, refusé par `check_source` et donc à l'export ; boucle à trois maillons ;
- ARCH-005 : charge permanente suivie ;
- CON-006 : `docs/domain/loads.md`.

Second tour : tout ✅, sauf la lettre du critère « neige ← charge permanente », impossible par les unités ; le critère est corrigé.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 (lot 2) | ✅ | `connector-source` 2.1, `connection-source` 4.1, sources de charges 1.1 (`LINKABLE`, `stamp_version`, `check_source`) ; brouillons validés dans `test_linkable_spin` |
| REQ-002 | ✅ | `test_links` : diamètre 0,002 × 5 m = 10 mm et effort d'essai N = 19,2 via `export_all.run` ; h_0 = 100 × 5 dans `build_calculations` |
| REQ-003…005 | ✅ | facteur 0,0005 → 8,75 mm dans la fenêtre ; facteurs à l'export |
| REQ-006 | ✅ | variable disparue → dernière valeur, `stale`, avertissement (SN-02) ; avertissements des charges dans la liste de l'export (`load_link_warnings`) |
| REQ-007 | ✅ | boucle de deux (SN-09 ↔ WI-09) et de trois (SN-08 → AU-09 → WI-08 → SN-08) : arrêt nommant la chaîne ; refus au choix (`LoadTab.refuse_link`) |
| REQ-008 | ✅ | délier repasse en 2.0 / 4.0 |
| REQ-009 (lot 2) | ✅ | `test_every_number_of_the_joints_and_loads_tabs_has_its_button_and_no_list_has_one` |
| REQ-012 | ✅ | `links` sur `calculations` 1.6, `connectors` 3.1, `connections` 4.2 ; schémas validés |
| UI-001…003 (lot 2) | ✅ | `_pick` dans `test_linkable_spin` ; aucun script ni assemblage proposé à une charge, aucun assemblage à un assemblage ; défaut trouvé et corrigé : le choix est remis avant le retour à l'onglet |
| ARCH-001 | ✅ | `links.entries/follow/refresh_all/check_all/drop_unheld/find_cycle`, utilisés aussi par les statiques |
| ARCH-002 (lot 2) | ✅ | un seul `LinkableSpin` (assemblages, polaires, charges), interchangeable avec son champ |
| ARCH-004 (lot 2) | ✅ | anciennes et nouvelles versions lues ; version haute seulement avec un lien ; `test_export`, `test_connectors` |
| ARCH-005 | ✅ | `links.allowed` (`LOADS`, `JOINTS`) lu par le filtre, `check_source` et la résolution ; ordre de l'export ; vent ← charge permanente (critère corrigé) |
| D-11, D-12, D-18 | ✅ | `test_links`, `test_linkable_spin` |
| CON-001 | ✅ | `ld_link_circle` fr/de/en ; `test_i18n` |
| CON-006 (lot 2) | ✅ | `variable-links.md`, `loads.md`, `tab-connectors.md`, `tab-polar-moments.md`, `window.md`, décision et index, CHANGELOG, « Nouveautés », catalogue ; `test_docs_coherence` |
| REQ-010, REQ-011, UI-004, ARCH-003, ARCH-006, ARCH-007 | lot 3 | — |

### Lot 3 (11.10.2026, `requirements-verifier`, copie de travail contre `a002da5`)

Mesure indépendante : `prepare` des quatre moteurs sur `tests/projet-exemple` avec l'arbre de base et l'arbre du lot — statiques, plans et plans incendie identiques octet pour octet (SVG et données), seuls les trois SVG du schéma VU-Skizze changent (D-19).

| Élément | Premier tour | Après correction |
|---|---|---|
| REQ-010 | ✅ `test_text_tool` (4 moteurs : posé, enregistré, exporté, SVG) | ✅ |
| REQ-011 | ⚠️ pas de test « variable modifiée → nouvelle valeur », ni d'avertissement dans l'export d'un moteur | ✅ `test_plan_texts` : rendu des quatre moteurs avec d'autres valeurs ; `text_stale` dans l'export d'un modèle, export poursuivi |
| UI-004 | ⚠️ « Retirer » et la taille non testés | ✅ `test_text_tool` : « Retirer », facteur `text`, jeton sans variable refusé |
| ARCH-003 | ✅ un module, quatre rendus l'appellent | ✅ |
| ARCH-004 (lot 3) | ✅ versions écrites seulement avec un texte | ✅ |
| ARCH-006 (amendé par D-19) | ✅ un seul `text_runs`, `typst_math` à deux sorties | ✅ |
| ARCH-007 | ⚠️ « plan sans texte = SVG d'avant » non figé par un test | ✅ `test_plan_texts.test_a_drawing_without_a_text_draws_as_before` (plan, plan incendie, modèle) |
| CON-001 | ❌ `test_i18n` : clé orpheline `plan_text_selected` | ✅ clé retirée, `test_i18n` 22 passés |
| CON-006 | ✅ | ✅ |
| Étape 17 | ⚠️ pas de test déplacer / copier / tourner / renommer (ARCH-RISK-107) | ✅ `test_plan_texts` (plan : déplacer, copier, tourner ; schéma : déplacer, tourner, dupliquer ; modèle : renommer, supprimer) |

Réserve connue, conforme à D-02 et à ARCH-007 : la fenêtre résout un texte contre l'export écrit sur le disque, l'export contre celui qu'il construit en mémoire ; les deux concordent dès qu'un export a été fait.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-11 | draft | spécification extraite des issues #42 et #43 ; existant cartographié (mode choix de *Variables*, `calc/units.py`, lien des charges des statiques, absence d'objet Texte) |
| 2026-10-11 | specified | 7 questions posées et résolues (D-01 à D-10) ; reste : revue d'architecture |
| 2026-10-11 | reviewed | revue d'architecture (deux relecteurs, APPROUVER AVEC RÉSERVES) reportée en §13 ; Q-009 à Q-012 résolues (D-11 à D-16) ; ARCH-006 et ARCH-007 ajoutées ; plan en trois lots (§14) ; reste : approbation |
| 2026-10-11 | approved | approuvée par l'ingénieur ; début du lot 1 |
| 2026-10-11 | implementation | D-17 : lien enregistré à côté du champ (`links`), choisi par l'ingénieur avant le premier code |
| 2026-10-11 | implementation | lot 1, étapes 1–5 : `calc/domains/links.py` (forme D-17, unités, facteur et décalage, dernière valeur, sources permises), `statics.resolve` par `links`, géométrie et ressorts liables (`statics-source` 1.2, export 1.2), vérifications de barres liables (`member-check-source` 1.1, export `checks` 1.1 avec `links`), export : scripts et *Formule* avant les consommateurs, valeurs en mémoire (`variable_sources.export_values`) ; `tests/test_links.py` (17). Reste : étapes 6–10 (mode choix, widget, onglets, docs). Boucles (REQ-007) : impossibles au lot 1 (vérifications et statiques ne produisent aucune variable), traitées au lot 2 |
| 2026-10-11 | implementation | lot 1, étapes 6–8 : `begin_variable_pick(…, accept)` revient à l'onglet demandeur, `VariablesTab.begin_pick(…, accept)` filtre domaines et variables (`variable_sources.linkable`) ; `calc/tools/linkable_spin.py` (bouton, état lié, facteur et décalage, délier, introuvable) ; *Vérifications de barres* : tous les champs du périmètre liables (`linked`, `fill_links`, `draft_links`) ; mots fr/de/en (`lk_`, `warn_link_`) ; `tests/test_linkable_spin.py` (3). Reste : étape 9 (statiques), 10 (docs) |
| 2026-10-11 | testing | lot 1, étapes 9–10 : *Modèles statiques* (carte « Coordonnées », rigidités, b_e liables ; intensité choisie par « Variables », les trois listes retirées ; `refresh_links` à l'ouverture, `stamp_version` sur le modèle lui-même à l'enregistrement) ; documentation : `docs/domain/variable-links.md` §3.3duovicies, trois `docs/ui/tab-*.md`, `layout.md`, décision (`decisions.md` + index), catalogue des tests, CHANGELOG, « Nouveautés » 0.117 fr/de/en. Tests : `test_links` 17, `test_linkable_spin` 4, docs/i18n/site/modules verts ; tests liés en cours |
| 2026-10-11 | verification | lot 1 vérifié en deux tours (§15), réserves corrigées ; les éléments des lots 2 et 3 restent ouverts dans §11 ; reste : suite complète, commit (`finish`) |
| 2026-10-11 | verification | lot 1 : suite complète 2751 passés, 15 ignorés, 1 échec indépendant (`test_plan_style` : processus arrêté en fin d'exécution, 20/20 relancé seul) ; `test_editor_buttons` adapté au choix par « Variables » (UI-005). Commit du lot 1 ; reste : lots 2 et 3 |
| 2026-10-11 | implementation | reprise : lot 1 commité (1b93581) et poussé ; début du lot 2 (étapes 11–14) |
| 2026-10-11 | implementation | lot 2, étapes 11–12 et une partie de 13 : `links.py` générique (`entries`, `follow`, `refresh_all`, `check_all`, `drop_unheld`, `find_cycle`, `JOINTS`) ; statiques sur ces fonctions ; `connector-source` 2.1 / `connectors` 3.1, `connection-source` 4.1 (+ `trial`, D-12) / `connections` 4.2, `dead-load-source`, `snow-source`, `wind-source` 1.1, `calculations` 1.6 ; `registry.build_calculations` construit les charges liées après ce qu'elles suivent, boucle → arrêt nommant la chaîne, `load_graph` ; export : scripts et *Formules* avant les assemblages, qui ne suivent aucun assemblage (`links.JOINTS`, précision d'ARCH-005) ; onglet *Moyens d'assemblage* branché ; `test_links` 22. Reste : moments polaires, onglets de charges, tests fenêtre, docs |
| 2026-10-11 | testing | lot 2, étapes 13–14 : *Moyens d'assemblage* (`_field(…, link=)`, `row_cell`), *Moments polaires* (efforts d'essai enregistrés, D-12), onglets de charges (champs, couches, refus d'une boucle au choix) ; `LinkableSpin` interchangeable avec son champ ; `begin_variable_pick` transmet le choix avant de revenir à l'onglet (défaut trouvé : l'onglet des assemblages reconstruit son formulaire en se montrant) ; D-18 ; docs (domaine, onglets, décision, CHANGELOG, « Nouveautés », catalogue). Tests : `test_links` 22, `test_linkable_spin` 10 ; tests liés en cours |
| 2026-10-11 | verification | lot 2, premier tour : aucun ❌, 4 ⚠️ corrigés (test de parcours des formulaires ; lien interdit = défaut de fichier refusé par `check_source` ; charge permanente suivie et boucle à trois maillons ; `docs/domain/loads.md`) ; *Formules* recalculées à chaque tour ; libellé `self` documenté |
| 2026-10-11 | verification | lot 2 vérifié en deux tours (§15) ; critère d'ARCH-005 corrigé (vent ← charge permanente, la neige n'ayant aucun champ en kN/m²) ; reste : suite complète, commit ; puis lot 3 |
| 2026-10-11 | verification | lot 2 : suite complète 2758 passés, 15 ignorés, 1 échec indépendant (`test_plan_style`, processus arrêté, 20/20 relancé seul) ; commit du lot 2 ; reste : lot 3 |
| 2026-10-11 | implementation | début du lot 3 ; D-19 : un seul moteur de texte des figures (celui des statiques), les schémas changeant légèrement, au choix de l'ingénieur |
| 2026-10-11 | implementation | lot 3, étape 15 : `svg_text.py` (moteur de texte unique, D-19 ; statiques identiques, empreintes figées des schémas comparées hors `<text>`) et `typst_math.py` (`richtext.math_html` y délègue ; `to_figure` pour les figures) |
| 2026-10-11 | testing | lot 3, étapes 16–18 : `figure_text.py` (jetons D-13, `show` D-09, `last` et avertissement D-06, dessin par `svg_text`), ligne `texts` de `figure_style` ; collection `texts` dans les quatre moteurs (`statics-source`/`statics` 1.2, `schema-source`/`schemas` 1.2, `plan-source` 1.7 / `plans` 1.4, `fire-source`/`fire` 2.1, écrits seulement avec un texte) ; valeurs passées aux `prepare` et aux rendus, schémas exportés après les variables ; `text_pane.py` et l'outil *Texte* dans les quatre onglets. Tests : `test_figure_text` 8, `test_text_tool` 4 ; suites liées vertes. Reste : docs, vérification, suite complète |
| 2026-10-11 | verification | lot 3 vérifié (§15) : 1 ❌ (mot orphelin) et 4 ⚠️ corrigés — `test_plan_texts` (5) ajouté, `test_text_tool` étendu ; docs du lot (domaine §3.3duovicies-bis, quatre onglets, décision D-19, CHANGELOG, « Nouveautés », catalogue). Reste : suite complète, commit |
| 2026-10-11 | completed | lot 3 : suite complète 2769 passés, 15 ignorés, 1 échec (`test_i18n`, le mot orphelin, corrigé ensuite : 22 passés) ; fichiers relancés après correction verts (`test_i18n`, `test_text_tool`, `test_plan_texts`, `test_docs_coherence`, `test_harness`). Issues #42 et #43 réalisées dans les trois lots |
