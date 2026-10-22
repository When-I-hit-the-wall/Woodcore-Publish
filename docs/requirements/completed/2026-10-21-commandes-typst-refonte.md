---
id: 2026-10-21-commandes-typst-refonte
titre: Commandes Typst — refonte et uniformisation (issues #74 à #82)
status: completed
cree: 2026-10-21
mis_a_jour: 2026-10-22
source: message écrit (retour de l'ingénieur sur le PDF de toutes les commandes Typst, 20.10.2026), ses réponses point par point (20.10.2026 et 21.10.2026), issues GitHub #74 à #82
docs: [docs/typst/formulas.md, docs/typst/api-conventions.md, docs/typst/report-engine.md, docs/typst/citations.md, docs/typst/command-docs.md, docs/domain/member-checks.md, docs/domain/documents.md, docs/domain/positions.md, docs/domain/position-plans.md, docs/architecture/principles.md, docs/architecture/data-contracts.md, docs/ui/window.md]
---

# Commandes Typst — refonte et uniformisation — Spécification

## 1. Objectif

Passer de ~80 commandes Typst spécialisées, dont plusieurs affichent la même chose par des chemins différents, à trois couches : un **noyau de calcul uniforme** (`#var`, `#eq`, `#verify`, `#unit`, `#domain`, `#calc-defaults`, `#get`) aux arguments d'affichage identiques et orthogonaux, où `level` n'est plus qu'un préréglage ; **un fichier `.typ` par domaine**, écrit par Woodcore avec ce noyau et modifiable comme du Typst normal ; des **documents en Typst brut** (`#table`, `#figure`, listes), Woodcore ne tenant que ce qui est balisé par `#sync` et les figures `#image-*`. Le but de l'ingénieur : un code Typst épuré, la liberté de tout formater en Typst normal, et une base saine pour les commandes futures.

## 2. Source

Le retour de l'ingénieur sur le PDF des commandes (20.10.2026), mot pour mot :

> **T1** — « dans typst, je souhaite uniformisier la manière d'afficher les résultats (par domaine, donc par fichier .typ), ainsi qu'uniformiser les commandes typst de calcul et ajouter des options. »
>
> **T2** — « Pour savoir si un valeur appartient à une donnée, un calcul ou un résultat, il y a un argument type: "data", "compute", "result". »
>
> **T3** — « Il devrait ensuite être possible de faire des tableaux uniquement avec les variables data, ou resultat. Le user devrait pouvoir choisir quelles colonnes afficher (colonne descr, norm, norm-section, label, etc...) »
>
> **T4** — « comment (peut-être y a-t-il quelque chose à implémenter) permettre l'automatisation, pour un domaine, d'afficher les données, les blocs de calculs (avec titre), un tableau avec les résultats (pas dans le screenshot). Propose-moi plusieurs variantes. Mon focus est sur un code typst épuré ainsi que sur la flexibilité (i.e. pouvoir tout formater normalement dans typst). »
>
> **T5** — « Je souhaite homogénéiser les commandes typst pour les calculs. »
>
> **T6** — « À quoi sert l'argument "own" ? Est-il vraiment nécessaire? »
>
> **T7** — « Les niveaux sont remplacés par un réglage fin de tous les paramètres. Si un level est indiqué, cela écrase les réglages fins par des réplages pré-programmés. »
>
> **T8** — « Les normes affichées en ligne doivent être écrites en gris, afin de moins attirer le regard. Il ne doit pas y avoir de "§" avant le norm-ref. »
>
> **T9** — « Voici les arguments que j'envisage pour les commandes suivantes. Dis-moi ce que tu en penses, garde toutes mes propositions et les tiennes dans un fichier .md afin que je puisse garder l'historique chez moi pour une décision ou implémentation future. »
>
> **T10** — « #var * name-calc (nom variable de calcul) * name-visible (nom variable affichée) * domain: deux formes possible de domaine: 1. "domain_name" 2. ("domain_type", "domain_name") note: à l'avenir, il n'y aura plus que domain_name. Il n'y aura plus 2 clés pour les domaines qui viennent de excel, car il n'y aura plus de excel qui fournira des calculs. * value * unit * var-show: "none", "variable", "value", "value-unit", "variable-value-unit" * style: "normal", "bold", "underline", "double" * type: "data", "compute", "result" * label * label-position: "none", "before", "after", "footnote" * descr * descr-position: "none", "after", "footnote" * norm * norm-section (paragraphe ou section dans la norme) * norm-position: "none", "in-line", "line-right", "footnote" * id: (utilisé par woodcore pour reconnaître où se trouvent les calculs si jamais j'écris du texte ou des figures entre) * level: 0, 1, 2, 3 »
>
> **T11** — « #var-line il me semble que cette commande n'est plus utile, puisque #var est écrit en ligne. On pourrait la supprimer »
>
> **T12** — « #var-unit est-ce qu'il ne serait pas possible de supprimer cette commande en permettant de réutiliser #var pour cela ? E.g. #var("R_d", 5, "kN", norm: "SIA265", norm-section: "6.5.5.2") #var ("R_d", "N") écrire la deuxième commande reprendrait tous les arguments données initiallement à la commande #var("R_d", 5, "kN"), en changeant uniquement les unités »
>
> **T13** — « #eq * name-calc (nom variable de calcul) * name-visible (nom variable affichée) * equation * unit (permet de transformer e.g. l'unité par défaut de "kNm" en "Nmm" ; mais permet également de transgresser l'unité en prenant le résultat du calcul et en lui attribuant définitivement une autre unité sans convertir aucune unité e.g. #eq("R_d", "F_d/a", "kN/m") * eq-show: "none", "variable" (affiche l'équation uniquement avec les variables), "value" (affiche l'équation uniquement avec les valeurs), "value-unit" (affiche l'équation uniquement avec les valeurs et unités), "variable-value-unit" (affiche l'équation uniquement avec variables, puis avec les valeurs et unités) * style: "normal", "bold", "underline", "double" * type: "data", "compute", "result" * label * label-position: "none", "before", "after", "footnote" * descr * descr-position: "none", "after", "footnote" * norm * norm-section (paragraphe ou section dans la norme) * norm-position: "none", "in-line", "line-right", "footnote" * id: (utilisé par woodcore pour reconnaître où se trouvent les calculs si jamais j'écris du texte ou des figures entre) * level: 0, 1, 2, 3 * #eq est affiché en ligne (donc il faut une ligne vide avant et après afin que ce soit affiché comme paragraphe seul) * #eq doit permettre également de calculer avec des valeurs à la volée, e.g. #eq("R_d", "M_d/[100, "mm"]) »
>
> **T14** — « #unit * unit (nouvelle unité à afficher). E.g. #unit("N") fera en sorte que les calculs affichent les résultats en "N" au lieu de "kN" (par défaut)) * scope: "one", "domain", "infinit" (par défaut: "one") => permet de définir la portée de cette fonction: uniquement pour le prochain affichage (var ou eq), pour tout le reste du domain, pour tout le reste du document »
>
> **T15** — « #var-domain. Est-il possible de renommer cette commande en #domain ? Si oui, fais-le. #domain * id * label (titre) * label-position: "none", "before", "after", "footnote" * descr * descr-position: "none", "after", "footnote" * norm * norm-section (paragraphe ou section dans la norme) * norm-position: "none", "in-line", "line-right", "footnote" (in-line = après le label) * id: (utilisé par woodcore pour reconnaître où se trouvent les calculs si jamais j'écris du texte ou des figures entre) * level: 0, 1, 2, 3 (défini un niveau pour toutes les commandes contenues dans le domaine, à moins qu'un argument de détail fin ou un level est défini pour une commande, ce qui écrase le niveau général du domaine) => il ne faut donc pas l'argument gen. L'id remplace l'argument gen »
>
> **T16** — « #val est-ce que val peut être remplacé par var? »
>
> **T17** — « #verify * name-calc (nom variable de calcul) (optionel, si le user veut sauvegarder le résultat dans une variable) * name-visible (nom variable affichée) (à afficher avant le calcul, e.g. "eta = ..." (optionnel)) * relation * verify-show: "none", "variable" (affiche l'équation uniquement avec les variables), "value-unit" (affiche l'équation uniquement avec les valeurs et unités), "variable-value-unit" (affiche l'équation uniquement avec variables, puis avec les valeurs et unités) * type: "data", "compute", "result" * label * label-position: "none", "before", "after", "footnote" * descr * descr-position: "none", "after", "footnote" * norm * norm-section (paragraphe ou section dans la norme) * norm-position: "none", "in-line", "line-right", "footnote" * id: (utilisé par woodcore pour reconnaître où se trouvent les calculs si jamais j'écris du texte ou des figures entre) * level: 0, 1, 2, 3 »
>
> **T18** — « #distance * connector: dowel, bolt, nail, screw, ring * table: auto, (chiffre), liste de chiffre (30, 31) * alpha * label (titre du tableau) * descr (légende du tableau) * norm (au-dessus du titre à droite) * norm-section (paragraphe ou section dans la norme) * id * level: 0, 1, 2, 3 »
>
> **T19** — « #calc-block je n'ai plus besoin de cette commande, supprime-la »
>
> **T20** — « #show-connector, #show-calc, #show-live-load, #show-polar-moment, #show-connector-resistance, #show-journal, #show-position-list, #show-plan-quantities (pour celui-là, il faut implémenter un nouvelle onglet sous les positions), #verify-tension, #verify-compression, #verify-compression-perp, #verify-bending, #verify-bending-normal, #verify-shear, #verify-shear-off, #verify-shear-perp, #show-check-member, #check-member-ids(), #show-check-steel, #check-steel-ids() n'est plus nécessaire. Tous les calculs typst de ce domaine sont créés dans un fichier .typ qu'il suffit d'importer. L'affichage des schémas, graphiques, calculs, tableaux, sont dans ce fichier. »
>
> **T21** — « #show-input n'est plus nécessaire. #var remplirait exactement les mêmes fonctions et davantage. »
>
> **T22** — « #show-check n'est plus nécessaire. Remplacé par #verify »
>
> **T23** — « #show-plan-legend pas nécessaire. Le user ne va jamais souhaité imprimer la légende sans le plan. La légende est donc directement imprimée dans le plan à l'aide des options. »
>
> **T24** — « #show-load-summary, #show-line-load-summary, #show-result-summary, #member n'est plus nécessaire. »
>
> **T25** — « #doc-table, #live-load-table, #dead-load-table, #doc-field, #doc-checklist, #doc-choice, #doc-image, #doc-plan, #doc-fire-plan, #doc-extract, #doc-annexes, #doc-signatures il faut trouver un autre moyen de paramétriser les tableaux, liste numérotés, bullet list, figures. Ma proposition est que les tableaux sont écrits dans du typst brut (sans paramètre). Il pourrait y avoir, dans chaque cellule des tableaux, par exemple, des balises de commandes qui n'affichent rien, mais permette de délimiter du contenu. E.g. Nutzlast, #id-begin(number) A1 #id-end(number), #id-begin(number) $5 "kN"/"m"^2$ #id-end(number), #id-begin(number) $2 "kN"$ #id-end(number) De cette manière, les valeurs entre les balises peuvent être synchronisées. Si le user supprime une balise, alors cette valeur cesse d'être synchronisée. »
>
> **T26** — « Pour les figures, il faut pouvoir copier/coller une commande de figure, e.g. #figure( #image-svg(), ) <label> »
>
> **T27** — « #show-plan #image-positions-plan() * id (appelle l'id de l'image, du plan à afficher afin de retrouver laquelle c'est) * label (caption de la figure) * detail-figure: "length" (métré des longueurs), "axes", "dimensions", "centres", le user doit également pouvoir écrir ("length", "axes", "dimensions") * detail-legend: "none" (pas de légende sur la figure), "length" (métrés totaux par positions, ainsi que par type d'objet), "objects" (légende des objets utilisés sur le dessin), "scale-bar", le user doit également pouvoir écrir ("length", "objects") * highlight * caption copier la commande dans woodcore, copie: #figure( #image-positions-plan(...) ) <label> »
>
> **T28** — « #show-fire-plan, #show-static-model, #schema, #show-extract Remplacées par #image-fire-plan, #image-static-model, #image-schema, #image-extract S'inspirer de #image-positions-plan pour implémenter ces commandes »
>
> **T29** — « #sheet, #sheet-text, #sheet-viewport, #sheet-fire-viewport, #sheet-section, #sheet-legend, #sheet-fire-legend, #sheet-titleblock, #sheet-position-list, #sheet-quantities, => Ne sont plus nécessaires. Un fichier .typ est directement produit avec les éléments entourés par des balises id (id-begin, id-end). »
>
> **T30** — « #member est remplacé par #position, qui liste une position par son id #position * id (e.g. "T001") * label * descr * category-show: "type", "material", "strength-class", "section-type", "dimension", "units", "moisture-class", "length", "label", "descr" le user doit pouvoir écrire ("type", "material", "strength-class") »
>
> **T31** — « #var-of, #value-of, #moisture-class-of, #fmt-number, #fmt-value, #fmt-decimals, #render-symbol, #render-formula, #render-prose ceux-là ne sont plus nécessaires il me semble »
>
> **T32** — « #get-value, #get-unit, #get-symbol, #get-label, #get-choices sont-ils encore nécessaires? »

Ses réponses point par point aux propositions (20.10.2026), mot pour mot :

> **T33** — « L'argument OWN peut effectivement disparaître. »
>
> **T34** — « Pour le point 2, cela me va d'écrire VAR en parenthèse. Le nom de la variable, virgule, unit. Fermez la parenthèse. »
>
> **T35** — « Pour les arguments d'affichage var show, eq show et verify show, cela me va de remplacer cela par display. Je suis d'accord de renommer type en role. »
>
> **T36** — « Pour le level, je suis d'accord avec ta proposition. » _(la proposition : un argument écrit explicitement gagne toujours, `level` ne remplit que ce qui n'est pas écrit ; ordre argument de la commande > level de la commande > réglages du domaine > level du domaine > document)_
>
> **T37** — « Pour le point 5, je suis d'accord dans la commande EQ. Il doit pouvoir y avoir deux arguments, un qui est unit et un qui est as unit. Le as unit permet de modifier l'unité. »
>
> **T38** — « Pour le point 6, cela me va tout à fait d'avoir une balise qui entoure ce qui est balisé et que cette balise s'appelle sync. »
>
> **T39** — « Pour le point 7, je suis d'accord d'avoir la fonction get qui remplace les autres commandes. Garde alors les commandes fmt et render. »
>
> **T40** — « Pour le point 8, je suis d'accord avec le renommage de tes valeurs. Je suis également d'accord avec ta proposition de généraliser ce principe avec le calc default. » _(les valeurs : `"next"`, `"domain"`, `"document"` ; `#calc-defaults(…, scope:)`)_
>
> **T41** — « pour ton point d'automatiser un domaine. Je valide l'option A. Plus C. » _(A : Woodcore écrit chaque `#var`, `#eq`, `#verify` en clair ; C : les tableaux de données et de résultats se placent par requête)_
>
> **T42** — « Effectivement, quand Woodcore régénère un fichier que j'ai modifié, eh bien Woodcore ne reprend que ce qui a été balisé et signale en rouge une structure qu'elle ne peut pas appliquer. Cela permet de remplacer le GEN que l'on a aujourd'hui. »
>
> **T43** — « La migration n'est pas nécessaire, il suffit d'avoir un message d'alerte. Les projets seront manuellement transportés par le user sur la nouvelle version. »
>
> **T44** — « nom de variable positionnel: oui, garder. sep: non, enlever. » (21.10.2026)
>
> **T45** — « implémente les issues #75 à #82 » (21.10.2026)

## 3. Exigences fonctionnelles

### REQ-001 — Arguments communs de `#var`, `#eq`, `#verify`
- **Exigence** : Woodcore doit offrir à `#var`, `#eq` et `#verify` le même jeu d'arguments d'affichage : `display` (`#eq` : `display-formula` et `display-equation`, Q-001), `style` (`"normal"`, `"bold"`, `"underline"`, `"double"`), `role` (`"data"`, `"compute"`, `"result"`), `label` + `label-position` (`"none"`, `"before"`, `"after"`, `"footnote"`), `descr` + `descr-position` (`"none"`, `"after"`, `"footnote"`), `norm` + `norm-section` + `norm-position` (`"none"`, `"in-line"`, `"line-right"`, `"footnote"`), `id`, `level` (0 à 3). `norm-ref` devient `norm-section` ; `note:` disparaît, remplacé par les trois `*-position`.
- **Source** : T5, T10, T13, T17, T35
- **Priorité** : doit
- **Critère d'acceptation** : chaque argument de chaque valeur listée produit le rendu attendu dans un test Typst par commande (`tests/test_formula.py` étendu) ; une valeur hors liste arrête la compilation en nommant l'argument et les valeurs admises.

### REQ-002 — `#var` : déclarer, réafficher, changer d'unité
- **Exigence** : `#var` doit garder ses formes positionnelles (`#var("l_1", "l", 5, "m")` : nom de calcul, nom affiché, valeur, unité) et accepter les formes nommées `name-calc`, `name-visible`, `value`, `unit`. Avec une valeur, il déclare ; sans valeur, il affiche une variable déjà déclarée, reprenant tous ses arguments sauf ceux qu'on écrit ; `#var("R_d", unit: "N")` la réaffiche convertie dans une autre unité, **pour l'affichage seul** : le registre garde l'unité déclarée, la suite et `#var-table` ne changent pas (Q-011) ; l'héritage des arguments exclut `level` et `id`. `domain:` accepte `"nom"` et, tant qu'Excel fournit des domaines, `("type", "nom")`.
- **Source** : T10, T12, T16, T21, T34, T44
- **Priorité** : doit
- **Critère d'acceptation** : `#var("R_d", 5, "kN", norm: "SIA 265", norm-section: "6.5.5.2")` puis `#var("R_d", unit: "N")` imprime `R_d = 5000 N` avec la même citation ; `#var("M_d")` imprime la variable déclarée ; un nom inconnu arrête la compilation en le nommant.

### REQ-003 — `#eq` : `unit`, `as-unit`, valeurs à la volée, en ligne
- **Exigence** : `#eq` doit prendre `name-calc`, `name-visible` (positionnels comme aujourd'hui), `equation`, `unit` (convertit toujours, refuse une dimension différente) et `as-unit` (attribue au résultat une autre unité sans conversion, p. ex. `#eq("R_d", "F_d/a", as-unit: "kN/m")`), et les arguments communs, `display` y étant remplacé par `display-formula` et `display-equation` (Q-001). Il s'imprime en ligne : une ligne vide avant et après en fait un paragraphe seul. Il calcule avec des valeurs littérales à la volée, dans la syntaxe déjà acceptée `` `M_d / (100 "mm")` ``.
- **Source** : T13, T37
- **Priorité** : doit
- **Critère d'acceptation** : `unit: "Nmm"` sur un résultat en kNm multiplie par 10⁶ ; `unit: "kN/m"` sur un résultat en kN est refusé ; `as-unit: "kN/m"` garde le nombre et change l'unité, la fenêtre le signale sur le domaine et le PDF n'en dit rien (Q-004) ; les quatre combinaisons du PDF de l'ingénieur (résultat seul, formule seule, formule + résultat, complet) sont reproduites par `display-formula` × `display-equation` ; `` `M_d / (100 "mm")` `` calcule ; un `#eq` au milieu d'une phrase reste dans la phrase.

### REQ-004 — `#verify` : garder le taux, nom affiché, citation
- **Exigence** : `#verify` doit prendre `name-calc` (optionnel : garde le taux dans une variable), `name-visible` (optionnel : imprimé avant la relation, p. ex. `η = …`), `relation` et les arguments communs ; `display` y admet `"none"`, `"variable"`, `"value-unit"`, `"variable-value-unit"`. Il cite sa norme comme `#var` et `#eq` (il n'en cite aucune aujourd'hui).
- **Source** : T17, T22
- **Priorité** : doit
- **Critère d'acceptation** : `#verify(`sigma <= f`, name-calc: "eta", name-visible: "eta")` imprime `η = … ≤ 1.00 ✓` et `#var("eta")` le relit ; `norm:` apparaît dans la bibliographie.

### REQ-005 — `#unit` à portée
- **Exigence** : `#unit(unit, scope: "next" | "domain" | "document")`, défaut `"next"` : l'unité vaut pour le prochain affichage d'une valeur de cette dimension, pour le reste du domaine, ou pour le reste du document.
- **Source** : T14, T40
- **Priorité** : doit
- **Critère d'acceptation** : trois tests, un par portée ; avec `"next"`, le second résultat de même dimension revient à l'unité par défaut ; avec `"domain"`, l'unité cesse à la fin du `#domain`.

### REQ-006 — `#calc-defaults`
- **Exigence** : `#calc-defaults(…, scope: "next" | "domain" | "document")` doit fixer n'importe quel argument commun de REQ-001 et l'unité, avec les mêmes portées que `#unit`.
- **Source** : T40
- **Priorité** : doit
- **Critère d'acceptation** : `#calc-defaults(norm-position: "line-right", scope: "domain")` met toutes les citations du domaine à droite, sauf celles qui écrivent leur propre `norm-position`.

### REQ-007 — `level` comme préréglage, ordre de priorité
- **Exigence** : `level` (0 à 3) doit être un jeu de réglages fins pré-programmés par commande ; un argument écrit explicitement gagne toujours. Ordre : argument de la commande > `level` de la commande > `#calc-defaults` du domaine > `level` du domaine > `#calc-defaults` du document > niveau du document (`--input level`). `level: 0` équivaut à `display: "none"` (la variable est déclarée, rien ne s'imprime). `--input uniform=N` garde son rôle (cf. Q-005).
- **Source** : T7, T15, T36
- **Priorité** : doit
- **Critère d'acceptation** : une table des préréglages par commande et par niveau dans `docs/typst/formulas.md` ; tests : `level: 2, norm-position: "none"` n'imprime aucune citation ; un `#domain(level: 3)` imprime ses lignes au niveau 3 sauf celle qui écrit `level: 1`.

### REQ-008 — `#domain` remplace `#var-domain`
- **Exigence** : `#var-domain` doit être renommé `#domain` avec `id` (remplace `name` et `gen`), `label`, `label-position`, `descr`, `descr-position`, `norm`, `norm-section`, `norm-position` (`"in-line"` = après le label), `level` (pour toutes les commandes contenues). `gen` disparaît.
- **Source** : T15
- **Priorité** : doit
- **Critère d'acceptation** : `#domain("P1", label: "Poutre P1")[…]` imprime son titre et isole ses noms comme `#var-domain` aujourd'hui ; `gen:` n'est plus accepté.

### REQ-009 — Suppressions du noyau
- **Exigence** : les commandes et arguments suivants doivent être retirés : `own:`, `sep:`, `note:`, `summary:`, `#val`, `#var-unit`, `#var-line`, `#show-input`, `#show-check`, `#calc-block`, `#var-of`, `#value-of`. `fmt-*` et `render-*` sont gardés. `#get(v, champ)` est gardé (fusion de la v0.120) et accepte aussi un nom de variable du registre.
- **Source** : T6, T11, T16, T19, T21, T22, T31, T32, T33, T39, T44
- **Priorité** : doit
- **Critère d'acceptation** : aucune définition de ces commandes dans `lib/` ; chacune produit l'alerte de REQ-020 ; `#context get("eta", "value")` rend le nombre. Les définitions disparaissent au dernier lot (ARCH-RISK-101) ; avant, les anciens noms ne sont plus publics.

### REQ-010 — `#var-table` : tableaux par rôle
- **Exigence** : `#var-table(role:, domain:, unit:, columns:)` doit lister les variables d'un rôle (`"data"`, `"compute"`, `"result"`) d'un domaine, d'une liste de domaines ou de tous (`domain: "all"`), filtrées par unité si `unit:` est donné — ce qui remplace `#show-load-summary` (`#var-table(role: "data", domain: "all", unit: "kN/m²")`) et `#show-result-summary` (`#var-table(role: "result", domain: "all")`) (Q-009) —, colonnes au choix parmi `descr`, `label`, `symbol`, `value`, `unit`, `norm`, `norm-section` ; plaçable avant les déclarations ; rendu par un `#table` Typst que `#show table` et `#set table` mettent en forme.
- **Source** : T2, T3, T4, T41 ; Q-009
- **Priorité** : doit
- **Critère d'acceptation** : dans le projet exemple, un domaine imprime en tête son tableau des données et en fin celui des résultats, sans valeur recopiée ; changer une valeur dans le `#var` change le tableau ; la Nachweisübersicht et le récapitulatif des charges du projet exemple s'impriment par `#var-table` avec les mêmes valeurs qu'avant.

### REQ-011 — `#sync` : valeur tenue par Woodcore
- **Exigence** : `#sync(id)[contenu]` doit n'imprimer que son contenu ; Python doit lire et réécrire le contenu entre ses crochets, dans une cellule, une liste ou une phrase ; retirer `#sync` (en gardant le contenu) arrête la synchronisation. **Le contenu est une lecture vivante quand Typst peut lire la donnée** — `#sync("live-load/A1/q_k")[#var("q_k", domain: ("live-load", "A1"), display: "value-unit")]` —, un littéral sinon — `#sync("live-load/A1/category")[A1]` ; Woodcore tient ce qui est entre les crochets (l'appel ou le littéral), la valeur vivante ne vieillit pas, et l'ingénieur remplace le contenu à la main en retirant le `#sync` (Q-007). Ids : `domaine/instance/variable`, unicité par fichier, règle d'échappement documentée.
- **Source** : T25, T29, T38 ; Q-007
- **Priorité** : doit
- **Critère d'acceptation** : un test Python réécrit `#sync("A1.q_k")[$5 "kN"/"m"^2$]` sans toucher un octet hors des crochets ; un contenu sans `#sync` n'est jamais réécrit.

### REQ-012 — Régénération : seul le balisé est repris, le reste signalé en rouge
- **Exigence** : quand Woodcore régénère un fichier qu'il a écrit, il ne doit réécrire que le contenu des `#sync` et les lignes portant un `id:` qu'il connaît — **chaque ligne qu'il écrit porte un `id:`** (Q-006) ; un changement de structure qu'il ne peut pas appliquer (ligne ajoutée ou retirée par le générateur, formule changée) doit être signalé en rouge à la tête du domaine dans le PDF et dans la fenêtre. Cela remplace `gen` (l'état est écrit par Python, ARCH-007) ; une ligne sans `id:` (ou hors `#sync`) appartient à l'ingénieur, ce qui remplace `own` : pour garder sa valeur contre l'export, l'ingénieur retire l'`id:` de la ligne. Une ligne qu'un générateur ajoute à une liste (journal, liste des positions, métré) est proposée en alerte avec une action « Ajouter » dans la fenêtre (Q-008).
- **Source** : T6, T15, T33, T42 ; Q-006, Q-008
- **Priorité** : doit
- **Critère d'acceptation** : test sur une vérification dépliée : l'ingénieur modifie une ligne sans id et ajoute du texte ; la régénération met à jour les valeurs balisées, garde le reste et, quand le générateur change de forme, imprime la ligne rouge.

### REQ-013 — `#image-positions-plan`
- **Exigence** : `#image-positions-plan` doit remplacer `#show-plan` avec le plan en positionnel (l'`id` de T27), `highlight`, `width`, `detail-figure` (`"length"`, `"axes"`, `"dimensions"`, `"centres"`, ou une liste) et `detail-legend` (`"none"`, `"length"`, `"objects"`, `"scale-bar"`, ou une liste) ; il rend une image à placer dans un `#figure` natif, qui porte la légende (`caption:`) et l'étiquette (`<label>`) de T27 ; la légende des objets est dans la figure selon `detail-legend` (D-13).
- **Source** : T23, T26, T27
- **Priorité** : doit
- **Critère d'acceptation** : `#figure(image-positions-plan("PL-1", detail-legend: ("length", "objects")), kind: image, caption: […]) <pl1>` compile, se numérote et se référence par `@pl1`.

### REQ-014 — `#image-fire-plan`, `#image-static-model`, `#image-schema`, `#image-extract`
- **Exigence** : ces quatre commandes doivent remplacer `#show-fire-plan`, `#show-static-model`, `#schema` et `#show-extract`, sur le modèle de `#image-positions-plan` (mêmes noms d'arguments là où le sens est le même).
- **Source** : T28
- **Priorité** : doit
- **Critère d'acceptation** : chacune compile dans un `#figure` natif sur le projet exemple.

### REQ-015 — `#position` remplace `#member`
- **Exigence** : `#position(id, label:, descr:, category-show:)` doit lister une position par son id, `category-show` parmi `"type"`, `"material"`, `"strength-class"`, `"section-type"`, `"dimension"`, `"units"`, `"moisture-class"`, `"length"`, `"label"`, `"descr"`, ou une liste.
- **Source** : T24, T30
- **Priorité** : doit
- **Critère d'acceptation** : `#position("T001", category-show: ("type", "material", "strength-class"))` imprime ces trois champs lus de `data/positions/T001.json` (`length` est lu de `data/quantities.json`) ; l'alerte de `#member` renvoie au fichier de domaine de la vérification, pas à `#position` (`#member` déclarait b, h, A… pour les `#verify-*`).

### REQ-016 — `#distance` aux arguments uniformes
- **Exigence** : `#distance` doit prendre `connector` (`dowel`, `bolt`, `nail`, `screw`, `ring`), `table` (`auto`, un numéro, une liste ; aujourd'hui `tab`), `alpha`, `label` (titre ; aujourd'hui `title`), `descr` (légende), `norm` (au-dessus du titre à droite), `norm-section` (aujourd'hui `norm-ref`), `id`, `level`.
- **Source** : T18
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_distance.py` passe avec les nouveaux noms ; les anciens produisent l'alerte de REQ-020.

### REQ-017 — Un fichier `.typ` par domaine
- **Exigence** : chaque domaine dont une commande `#show-*` ou `#verify-*` est retirée doit écrire son fichier `.typ` avec le noyau (REQ-001 à 008), `#var-table` (REQ-010), `#sync` et `id:` (REQ-011, 012) et les `#image-*` (REQ-013, 014), sur le modèle des vérifications dépliées de `calc/domains/unfold.py` (variante A + C) : charges (neige, vent, poids propre, charges utiles), connecteurs, moments polaires, vérifications de barres (traction, compression, compression ⊥, flexion, flexion composée, flambement, déversement, cisaillement, cisaillement de bord, cisaillement ⊥, et la situation de feu), vérifications acier, journal, liste des positions, métré. Le journal, la liste des positions et le métré sont écrits une fois en Typst brut, chaque cellule en `#sync`, une ligne nouvelle proposée par « Ajouter » (Q-008). Les fichiers sont inclus par `domain-file(kind, id)` (ARCH-008). Les titres des blocs passent par `label-position: "before"`. Les sections du rapport incluent ces fichiers.
- **Source** : T4, T20, T24, T41 ; Q-008, Q-010
- **Priorité** : doit
- **Critère d'acceptation** : les trois documents du projet exemple compilent avec les fichiers de domaine et sans aucune commande retirée ; chaque générateur a son test (fichier compilé, `#eq` recalculés égaux aux lignes Python à 1e-9) ; les valeurs imprimées sont celles d'avant (extraction de texte du PDF avant/après, écarts expliqués).

### REQ-018 — Suppressions des commandes de domaine
- **Exigence** : `#show-connector`, `#show-calc`, `#show-live-load`, `#show-polar-moment`, `#show-connector-resistance`, `#show-journal`, `#show-position-list`, `#show-plan-quantities`, les huit `#verify-*`, `#show-check-member`, `#show-check-steel`, `#show-load-summary`, `#show-result-summary`, `#member`, `#show-plan`, `#show-fire-plan`, `#show-static-model`, `#schema`, `#show-extract` doivent être retirées de `lib/`, après REQ-017. (`#check-member-ids`, `#check-steel-ids`, `#show-line-load-summary`, `#show-plan-legend` sont déjà retirés.)
- **Source** : T20, T23, T24, T27, T28
- **Priorité** : doit
- **Critère d'acceptation** : aucune définition dans `lib/` ; chacune produit l'alerte de REQ-020.

### REQ-019 — Documents en Typst brut
- **Exigence** : `#doc-table`, `#live-load-table`, `#dead-load-table`, `#doc-field`, `#doc-checklist` et `#doc-choice` (retirés sans remplaçant paramétrique, Q-002), `#doc-image`, `#doc-plan`, `#doc-fire-plan`, `#doc-extract`, `#doc-annexes`, `#doc-signatures` et les dix `#sheet-*` doivent être retirés ; les modèles de la convention, de la base de projet et du rapport (de, fr, en) sont réécrits en Typst brut (`#table`, listes, `#figure`), les valeurs tenues par Woodcore entourées de `#sync` (Q-007) ; une règle `#show: doc-tables` définie une fois donne aux tables des documents leur style d'aujourd'hui. `calc/sheets.py` écrit les feuilles de plan en Typst brut (`#place` d'images) : la coupe schématique, la légende de plusieurs plans et le cartouche deviennent `#image-section`, `#image-legend` et `#image-titleblock`, les listes sont les fichiers de domaine (liste des positions, métré) inclus dans la feuille ; un primitif de page interne reste pour l'éditeur de feuilles (Q-013).
- **Source** : T25, T26, T29 ; Q-002, Q-012, Q-013
- **Priorité** : doit
- **Critère d'acceptation** : aucune de ces commandes dans `lib/` ni dans `templates/` ; les modèles compilent dans les trois langues ; l'onglet « Structure du document » édite les tableaux bruts comme il édite les `#doc-table` aujourd'hui (cf. ARCH-004).

### REQ-020 — Commandes retirées : alerte, pas de migration
- **Exigence** : chaque commande et chaque argument retiré par cette spec doit produire, à l'ouverture du projet et à l'export, une alerte qui le nomme et nomme son remplaçant (ARCH-006 : par Python, un nom indéfini ne pouvant donner en Typst que « unknown variable ») ; tout `#unit(` sans `scope:` est signalé en avertissement (CON-007) ; les projets ne sont pas migrés automatiquement.
- **Source** : T43
- **Priorité** : doit
- **Critère d'acceptation** : `#val("M_d")` dans un projet donne « `#val` a été retiré : écrire `#var("M_d")` » dans la fenêtre et dans le refus de l'export, fichier et ligne nommés ; la table complète ancienne commande → remplaçant est dans `docs/typst/` et dans les « Nouveautés ».

### REQ-021 — Cisaillement de bord et cisaillement ⊥ calculés en Python
- **Exigence** : les calculs de `#verify-shear-off` et `#verify-shear-perp` (aujourd'hui en Typst seul, `lib/timber.typ:1391`, `:1449`) doivent être portés dans `calc/domains/member_check.py` comme deux types de vérification, chaque valeur de norme lue de `calc/norms/` et citée, avec leur générateur.
- **Source** : Q-010
- **Priorité** : doit
- **Critère d'acceptation** : les cas de `tests/test_timber.py` sur ces deux commandes donnent les mêmes valeurs par le calcul Python et par le fichier généré compilé.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Citations en gris, sans « § »
- **Exigence** : une norme citée en ligne ou dans la colonne de droite doit être imprimée en gris, sans « § » devant `norm-section` (aujourd'hui ajouté à `lib/calc-engine-core.typ:690` et `lib/distance.typ:159`). La couleur est lue d'un fichier de couleurs du rapport, pas écrite dans le code.
- **Source** : T8
- **Langues** : sans objet (aucun mot ajouté)
- **Critère d'acceptation** : le PDF du projet exemple montre `SIA 265 4.2.1` en gris (D-10) ; aucun « § » dans les citations ; test sur la couleur lue.

### UI-002 — Les boutons « Copier » copient les nouvelles commandes
- **Exigence** : les boutons « Copier » des 15 onglets qui copient aujourd'hui une commande retirée doivent copier la nouvelle forme : `#figure(image-…(…)) <label>` pour une figure, `#include` du fichier de domaine pour un calcul, `#var` pour une variable (onglet Variables).
- **Source** : T27 ; inféré de REQ-013 à 019 (règle 14 de `docs/architecture/principles.md`)
- **Langues** : fr / de / en pour tout libellé ajouté
- **Critère d'acceptation** : aucun bouton ne copie une commande retirée (test qui parcourt toutes les entrées de `tab_registry` et de `build_reference_calls` contre `calc/renamed-commands.json`) ; une figure se copie `#figure(image-…(…), kind: image) <label>` par un seul `call_image_figure`.

### UI-003 — Onglet « Métré » sous les positions
- **Exigence** : la carte « Métrés » de l'onglet Positions doit devenir un onglet « Métré » sous Positions, qui remplace `#show-plan-quantities`, lit `data/quantities.json` sans recalculer dans la fenêtre (aujourd'hui `positions_tab.py:587` recalcule), et produit son fichier `.typ` comme les autres domaines : tableau par matériau et section, totaux, portée tout / plans / positions (Q-003).
- **Source** : T20
- **Langues** : fr / de / en
- **Critère d'acceptation** : l'onglet s'ouvre sur le projet exemple, affiche le métré lu de `data/quantities.json` agrégé par `quantities.summary` (aucun recalcul géométrique dans la fenêtre), la date de l'export et un bandeau « périmé » quand un plan est plus récent ; son fichier compile.

### UI-004 — Alerte rouge de structure dans la fenêtre
- **Exigence** : l'alerte de REQ-012 doit aussi apparaître dans la fenêtre, sur le domaine concerné.
- **Source** : T42
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : après une régénération qui ne peut s'appliquer, l'onglet du domaine affiche l'alerte.

### UI-005 — Type de cisaillement dans l'onglet Cisaillement
- **Exigence** : l'onglet « Cisaillement » doit offrir un menu déroulant du type de cisaillement à calculer — cisaillement, cisaillement de bord (aujourd'hui `#verify-shear-off`), cisaillement ⊥ (aujourd'hui `#verify-shear-perp`) —, chaque type calculé en Python (REQ-021) et écrit par son générateur.
- **Source** : Q-010
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : choisir « cisaillement de bord » dans le menu, enregistrer, exporter : `data/checks.json` porte le type et le fichier de domaine imprime le calcul.

## 5. Exigences d'architecture

### ARCH-001 — Un seul résolveur d'affichage
- **Exigence** : les arguments communs, `level`, `#calc-defaults` et l'ordre de priorité doivent être résolus par **une** fonction de `lib/` appelée par `#var`, `#eq`, `#verify`, `#domain` et `#var-table`, les préréglages par niveau dans un fichier JSON de `lib/` (pas dans le code).
- **Source** : T5, T7, T36 ; principes, règles 2 et 4
- **Critère d'acceptation** : une seule définition de la résolution (grep) ; la table des préréglages est un JSON lu par Typst.

### ARCH-002 — Un seul générateur de fichier de domaine
- **Exigence** : les générateurs de REQ-017 doivent étendre le mécanisme de `calc/domains/unfold.py` (états par ligne, base, conflits) plutôt qu'en créer un par domaine ; `calc/domains/domain_file.py` (stubs `#show-*`) et `gen` disparaissent.
- **Source** : T20, T42 ; inféré (règle 1, « one source of truth »)
- **Critère d'acceptation** : un module de régénération, un générateur par type de domaine qui ne fait qu'écrire les lignes.

### ARCH-003 — Le calcul reste dans `calc/domains/` ou dans le noyau
- **Exigence** : ce que les `#verify-*` calculaient en Typst à partir des tables de la norme doit être écrit par le générateur en `#var` (valeurs lues des normes, citées) et `#eq` ; aucune valeur de norme n'est recopiée à la main.
- **Source** : inféré (CLAUDE.md : « One source of truth », « SIA calculations stay traceable »)
- **Critère d'acceptation** : chaque `#var` d'une valeur de norme écrite par un générateur porte `norm:` et `norm-section:` et sa valeur est lue de `calc/norms/` par le générateur.

### ARCH-004 — Le modèle d'objet lit et écrit le Typst brut
- **Exigence** : `calc/typst_objects*` doit savoir lire un `#table` brut (avec ses `#sync`) en modèle et le réécrire, pour que l'onglet « Structure du document » continue de n'afficher aucun code (règle 15). Sous-ensemble documenté : arguments nommés gardés verbatim, positionnels en blocs `[…]`, `table.header`, `table.hline` ; hors sous-ensemble (spread, `for`, `colspan`, `columns:` calculé), le tableau est affiché en lecture seule et jamais réécrit ni remplacé. Écriture par remplacement d'étendue. Le panneau garde les **colonnes cachées et l'alignement**, écrits dans `columns:` / `align:` du `#table` brut (Q-012) ; l'unité et l'id de colonne, la catégorie et l'override orange des charges utiles disparaissent.
- **Source** : T25 ; principes, règle 15 ; revue (301) ; Q-012
- **Critère d'acceptation** : aller-retour lecture → écriture d'un tableau brut sans aucun octet changé hors de l'étendue touchée ; édition d'une cellule qui réécrit la cellule seule ; cacher une colonne et changer son alignement depuis le panneau ; un tableau hors sous-ensemble n'est jamais réécrit.

### ARCH-005 — `calc/domains/formula_domain.py` suit le noyau
- **Exigence** : l'onglet « Formules » doit lire et écrire les nouvelles formes (`display`, `role`, `*-position`, `#domain`, plus de `#val`, `#var-unit`, `own`).
- **Source** : inféré de REQ-001 à 009
- **Critère d'acceptation** : `tests/test_formula_domain*.py` passent sur les nouvelles formes.

## 6. Contraintes

- **CON-001** — Trois langues pour tout mot nouveau (fenêtre : `STRINGS` ; rapport : `calc/i18n/strings.json`), `tests/test_i18n.py`. Source : inféré (CLAUDE.md).
- **CON-002** — Toute commande ajoutée ou changée porte son bloc `///`, deux exemples qui compilent, sa catégorie dans `build_reference.CATEGORIES` et sa traduction dans `calc/i18n/commands.json` (`tests/test_commands.py`). Source : inféré (règle 14).
- **CON-003** — Tout contrat JSON changé (`checks.json` sans `gen`, base des fichiers de domaine, préréglages) monte sa `schema_version`. Source : inféré (règle 8).
- **CON-004** — Pas de migration automatique ; une commande retirée alerte (REQ-020). Source : T43.
- **CON-005** — Les pages du projet exemple sont tenues à l'octet (spec « Indices et niveaux », lot 0) : les lots du noyau sont octet-neutres sauf UI-001 ; les lots transcrits prouvent « mêmes valeurs imprimées » par extraction de texte avant/après ; chaque lot qui change le rendu re-gèle la référence et dit pourquoi. Source : inféré ; revue (115, 210).
- **CON-006** — Plusieurs sessions éditent le dépôt : pas de `checkout --`, `stash`, `reset`, `clean`. Source : CLAUDE.md.
- **CON-007** — `#unit` change de sens par défaut (portée `"next"` au lieu du reste du document aujourd'hui) : les « Nouveautés » le disent en tête. Source : T14, T40, inféré.

## 7. Décisions prises

| Sujet | Décision | Source |
|---|---|---|
| `own` | supprimé : une ligne avec `id:` / dans un `#sync` est tenue par Woodcore, sans `id:` elle appartient à l'ingénieur | T33, Q-006 |
| `#val`, `#var-unit`, `#show-input`, `#value-of` | fusionnés dans `#var` ; `#var("R_d", unit: "N")` en argument nommé | T12, T16, T21, T34 |
| Affichage | un seul argument `display:` (`show` est réservé en Typst) | T35 |
| `type:` | renommé `role:` | T35 |
| `level` contre réglages fins | l'argument écrit gagne ; `level` remplit le reste ; ordre de REQ-007 | T36 |
| Unité de `#eq` | `unit:` convertit, `as-unit:` attribue sans conversion | T37 |
| Balises | `#sync(id)[contenu]` | T38 |
| `#get-*` | `#get` (déjà fait en v0.120) ; `fmt-*` et `render-*` gardés | T39 |
| `#unit` | `scope:` `"next"` (défaut), `"domain"`, `"document"` ; `#calc-defaults` généralise | T40 |
| Automatisation d'un domaine | variante A + C | T41 |
| Régénération | seul le balisé est repris, le reste signalé en rouge ; remplace `gen` | T42 |
| Migration | aucune, alerte seulement | T43 |
| Noms de variable | positionnels gardés | T44 |
| `sep:` | retiré | T44 |
| `#var-domain` | renommé `#domain` | T15 |
| Affichage de `#eq` | `display-formula` et `display-equation`, mêmes cinq valeurs (interprétation à confirmer) | Q-001 |
| Checklists | `#doc-checklist`, `#doc-choice` retirés sans remplaçant | Q-002 |
| Métré | la carte devient un onglet sous Positions, lu de `data/quantities.json` | Q-003 |
| `as-unit` | signalé dans la fenêtre seulement | Q-004 |
| `--input uniform` | écrase tout, arguments écrits compris (par défaut) | Q-005 |
| `--input uniform` et `#sync` | ce que tient un `#sync` s'imprime comme il est écrit : le niveau uniforme n'y entre pas (une cellule lue en direct par `#var(…, display: "value")` reste la valeur seule à tout niveau) — déduit au lot 18 de Q-005 et Q-007, qui sans cela se contredisaient dans une cellule | Q-005, Q-007 |
| Mise en page d'un fichier généré | famille de préréglages `block` (`#calc-defaults(presets: "block", scope: "domain")`), qui remplace `note: "line"` | Q-014 |
| Identité des lignes générées | `id:` sur chaque ligne ; retirer l'`id:` garde la valeur de l'ingénieur | Q-006 |
| Valeurs de données dans les documents | chaque cellule en `#sync`, le contenu une lecture vivante (`#var(…, domain:)`) quand Typst peut lire la donnée, un littéral sinon | Q-007 |
| Journal, liste des positions, métré | écrits une fois en Typst brut, cellules en `#sync`, ligne nouvelle par « Ajouter » | Q-008 |
| Résumés | `#var-table` sur plusieurs domaines (`domain: "all"`, filtre `unit:`) remplace `#show-load-summary` et `#show-result-summary` | Q-009 |
| Cisaillement de bord et ⊥ | calculés en Python, choisis par un menu déroulant de l'onglet Cisaillement | Q-010 |
| `#var(unit:)` | affichage seul ; le registre garde l'unité déclarée | Q-011 |
| Tableaux bruts | le panneau garde colonnes cachées et alignement ; unité, id de colonne et override orange disparaissent | Q-012 |
| Feuilles | coupe, légende multi-plans, cartouche → `#image-section`, `#image-legend`, `#image-titleblock` ; listes = fichiers de domaine ; primitif de page interne | Q-013 |

## 8. Hors périmètre

- La migration automatique des projets existants (T43).
- La disparition des domaines Excel à deux clés : `domain:` garde `("type", "nom")` tant qu'Excel fournit des domaines (T10, « à l'avenir »).
- Les objets de document qui ne sont ni tableau, ni liste, ni figure (titres, paragraphes) : leur balisage `// woodcore:object` reste tel quel.

## 9. Idées non retenues comme exigences

- T9 « garde toutes mes propositions et les tiennes dans un fichier .md » : fait par les issues #74 à #82 et par ce fichier.
- Variante B de l'automatisation (`#domain(layout: …)` qui cache les lignes) : écartée par T41.
- Une réécriture automatique des modèles (219 `#doc-table` dans `templates/`, 73 dans le projet exemple) est un outil de travail pour REQ-019, pas une migration des projets.

## 10. Questions

### Q-001 — Ce que `display` imprime de `#eq` (et le résultat)
- **Pourquoi elle compte** : les cinq valeurs de T13 décrivent l'équation, pas le résultat ; or le niveau 1 d'aujourd'hui imprime `σ = 0.89 N/mm²` (le résultat seul) et le PDF montre « Formule seule » (sans résultat) et « Formule + résultat, sans substitution ». Sans réponse, les préréglages de niveau ne peuvent pas reproduire les pages actuelles.
- **Options** : A `display` accepte une liste de parties ; B les cinq valeurs de T13, résultat toujours imprimé ; C les cinq valeurs plus `"result"`.
- **Réponse** : (21.10.2026, aucune des trois) « deux arguments différents: - display-formula: "none", "variable", "value", "value-unit", "variable-value-unit" - display-equation:. "none", "variable", "value", "value-unit", "variable-value-unit" ». **Interprétation retenue, à confirmer à l'approbation** : `display-equation` est la partie nom et résultat, au sens du `display` de `#var` (`"variable"` → σ, `"value"` → 0.89, `"value-unit"` → 0.89 N/mm², `"variable-value-unit"` → σ = 0.89 N/mm²) ; `display-formula` est la partie formule (`"variable"` → N/A, `"value"` → 50/56000, `"value-unit"` → 50 kN / 56000 mm², `"variable-value-unit"` → N/A = 50 kN / 56000 mm²). La ligne se compose `nom = formule = résultat`, chaque partie absente sautée. Résultat seul (niveau 1 d'aujourd'hui) : `display-formula: "none"`, `display-equation: "variable-value-unit"` ; formule seule : `display-formula: "variable"`, `display-equation: "variable"`.

### Q-002 — `#doc-checklist` et `#doc-choice` en Typst brut
- **Pourquoi elle compte** : ces deux commandes gardent les options non cochées (pour les recocher) et n'impriment que les cochées ; un Typst brut ne garde que ce qu'il imprime. 72 appels dans les modèles.
- **Options** : A liste brute ☒/☐ ; B garder ces deux commandes ; C liste brute, options non cochées en commentaire.
- **Réponse** : (21.10.2026) « supprimer l'option d'avoir des checklists, le user n'utilisera jamais de checklist paramétrique ». `#doc-checklist` et `#doc-choice` sont retirés sans remplaçant ; les modèles écrivent à leur place une liste brute (les options retenues par le modèle, comme du texte).

### Q-003 — L'onglet « Métré »
- **Pourquoi elle compte** : la carte « Métrés » existe déjà dans l'onglet Positions (`positions_tab.py:555`) et recalcule dans la fenêtre au lieu de lire `data/quantities.json`, contre la règle « un onglet ne recalcule pas ».
- **Options** : A (recommandée) la carte devient un onglet « Métré » sous Positions, lit `data/quantities.json` et écrit son fichier `.typ` (tableau par matériau et section, totaux, portée tout / plans / positions comme aujourd'hui) ; B un onglet plus riche (par étage, par type d'objet, export tableur) à spécifier à part.
- **Réponse** : (21.10.2026) A — la carte devient un onglet « Métré » sous Positions, lit `data/quantities.json` et écrit son fichier `.typ`.

### Q-004 — Ce que `as-unit` laisse voir
- **Pourquoi elle compte** : changer l'unité sans conversion rend un calcul faux s'il est mal employé ; la règle « SIA calculations stay traceable » demande que le lecteur le voie.
- **Options** : A (recommandée) la ligne imprime le résultat dans sa nouvelle unité et une note de bas de page en orange dit « unité attribuée (sans conversion) : kN → kN/m », comme la note orange d'aujourd'hui pour une valeur réaffichée ; B rien n'est signalé dans le PDF, seulement dans la fenêtre ; C rien n'est signalé.
- **Réponse** : (21.10.2026) B — signalé seulement dans la fenêtre, rien dans le PDF.

### Q-005 — `--input uniform=N`
- **Pourquoi elle compte** : aujourd'hui il force un niveau sur tout le document, par-dessus tout ; avec les réglages fins qui gagnent, il faut décider s'il écrase aussi les arguments écrits.
- **Options** : A (recommandée) il reste le seul à tout écraser, arguments écrits compris (c'est son rôle : un rapport uniforme) ; B il se range comme un `level` de document.
- **Réponse** : résolue par défaut sur A (non posée : elle ne change pas le plan) ; à confirmer à l'approbation.

Questions issues de la revue d'architecture (§13), posées le 21.10.2026 :

### Q-006 — Comment Woodcore reconnaît ses lignes, et comment l'ingénieur garde sa valeur
- **Pourquoi elle compte** : aujourd'hui une ligne générée se reconnaît à son nom de calcul, sans `id:` ; la règle « sans `id:` → à l'ingénieur » ne reprendrait aucune ligne générée (ARCH-RISK-201, 202, 107).
- **Options** : A (recommandée) nom de calcul + `domain:`, retirer `domain:` garde la valeur ; B `id:` sur chaque ligne ; C `#sync` autour de la valeur.
- **Réponse** : (21.10.2026) B — `id:` sur chaque ligne.

### Q-007 — Valeurs de données dans les tableaux de documents
- **Pourquoi elle compte** : `doc-value` lit la valeur vivante ; une copie `#sync` vieillirait (ARCH-RISK-302).
- **Options** : A (recommandée) lecture vivante + `#sync` réservé à ce que Typst ne peut pas lire ; B `#sync` partout.
- **Réponse** : (21.10.2026) « #sync(A1), #sync(#var(A1, domain: live-load)). Les deux cellules comportent chacune leur sync. De cette manière, rien ne vieilli et le user peut modifier facilement des choses manuellement » — chaque cellule en `#sync`, la cellule de valeur contenant la lecture vivante.

### Q-008 — Journal, liste des positions, métré
- **Pourquoi elle compte** : leurs lignes sont les données ; chaque ajout serait une alerte de structure (ARCH-RISK-205).
- **Options** : A (recommandée) écrits une fois + « Ajouter » ; B une commande `#data-table` ; C fichier entièrement à Woodcore.
- **Réponse** : (21.10.2026) A.

### Q-009 — Remplaçant des résumés
- **Pourquoi elle compte** : `#show-load-summary` et `#show-result-summary` retirés sans remplaçant (ARCH-RISK-206).
- **Options** : A (recommandée) `#var-table` multi-domaines ; B supprimer ; C garder les deux.
- **Réponse** : (21.10.2026) A.

### Q-010 — `#verify-shear-off` et `#verify-shear-perp`
- **Pourquoi elle compte** : calculés en Typst seul, sans onglet ni jumeau Python (ARCH-RISK-203).
- **Options** : A (recommandée) les calculer en Python ; B retirer sans remplaçant ; C reporter.
- **Réponse** : (21.10.2026) « ajouter ces cisaillements dans l'onglet cisaillement. Le user choisi dans un menu déroulant quel type de cisaillement il souhaite calculer » → REQ-021, UI-005.

### Q-011 — `#var(unit:)` affiche ou change la suite
- **Pourquoi elle compte** : `#val(unit:)` affichait, `#var-unit` changeait la suite (ARCH-RISK-106).
- **Options** : A (recommandée) affichage seul ; B change la suite.
- **Réponse** : (21.10.2026) A.

### Q-012 — Ce que perd le panneau d'un tableau brut
- **Pourquoi elle compte** : `hidden`, `kind`, unité et id de colonne, catégorie et override orange n'ont pas d'équivalent brut (ARCH-RISK-301).
- **Options** : A (recommandée) accepter ; B garder colonnes cachées + alignement.
- **Réponse** : (21.10.2026) B.

### Q-013 — Feuilles sans `#sheet-*`
- **Pourquoi elle compte** : coupe, légende multi-plans, cartouche et listes sans remplaçant (ARCH-RISK-306).
- **Options** : A (recommandée) images + fichiers de domaine ; B supprimer coupe et légende multi ; C reporter.
- **Réponse** : (21.10.2026) A.

### Q-015 — Le format des objets d'une feuille de plan
- **Pourquoi elle compte** : posée au lot 17 ; en Typst brut, l'éditeur de feuilles doit encore savoir où est chaque objet (ARCH-RISK-306) et certains réglages d'aujourd'hui n'ont pas d'équivalent brut.
- **Options** : A (recommandée) chaque objet un `#place(top + left, dx:, dy:, …) <type>` brut, la page `#show: sheet.with(…)` gardée comme primitif interne dont une règle `show place` dit à l'éditeur où est chaque objet étiqueté ; un plan `image-positions-plan(id, scale:, title:)`, un texte `text(size:, weight:)[…]`, une liste `box(width:)[#include …]`, légende, coupe et cartouche `#image-legend`, `#image-section`, `#image-titleblock` ; perdus : la légende courte sous un plan de feuille et le niveau propre à chaque objet ; B garder les `#sheet-*` comme primitifs internes ; C reporter les feuilles.
- **Réponse** : (21.10.2026) A — `#place` brut.

### Q-014 — Ce que devient `note: "line"` dans un fichier généré
- **Pourquoi elle compte** : posée au lot 8. `note: "line"` disait « libellé après la ligne, norme à droite, mais seulement quand le niveau les montre » ; avec les réglages fins, visibilité et position sont un argument, et un argument écrit l'emporte sur le niveau -- un fichier généré ne pouvait plus le dire.
- **Options** : A (recommandée) une famille de préréglages `block`, choisie par `#calc-defaults(presets: "block", scope: "domain")` ; B les positions écrites sur chaque ligne, visibles à tous les niveaux ; C garder `note:`.
- **Réponse** : (21.10.2026) A. `lib/display-presets.json` 1.1 porte la famille `block` (même visibilité que `inline` à chaque niveau, libellé `after`, norme `line-right`, la ligne à part) ; un appel écrit `note: "line"` est imprimé avec elle, ce qui fait d'elle son remplaçant.

## 11. Critères d'acceptation

- [x] REQ-001 — arguments communs sur les trois commandes, testés, valeurs hors liste refusées
- [x] REQ-002 — `#var` déclare, réaffiche, change d'unité ; formes positionnelles et nommées
- [x] REQ-003 — `#eq` `unit` / `as-unit`, littéraux, en ligne
- [x] REQ-004 — `#verify` garde le taux, nom affiché, cite sa norme
- [x] REQ-005 — `#unit` à trois portées
- [x] REQ-006 — `#calc-defaults`
- [x] REQ-007 — préréglages de niveau, ordre de priorité, table documentée
- [x] REQ-008 — `#domain`, `gen` retiré
- [x] REQ-009 — suppressions du noyau, `#get` par nom
- [x] REQ-010 — `#var-table`
- [x] REQ-011 — `#sync` lu et réécrit sans toucher le reste
- [x] REQ-012 — régénération du balisé, alerte rouge
- [x] REQ-013 — `#image-positions-plan` dans `#figure`
- [x] REQ-014 — quatre autres `#image-*`
- [x] REQ-015 — `#position`
- [x] REQ-016 — `#distance` renommé
- [x] REQ-017 — un fichier `.typ` par domaine, projet exemple sans commande retirée
- [x] REQ-018 — commandes de domaine retirées
- [x] REQ-019 — documents et feuilles en Typst brut
- [x] REQ-020 — alerte pour chaque commande retirée, table des remplaçants
- [x] UI-001 — citations grises sans « § »
- [x] UI-002 — boutons « Copier » à jour
- [x] UI-003 — onglet « Métré »
- [x] UI-004 — alerte de structure dans la fenêtre
- [x] UI-005 — menu du type de cisaillement
- [x] REQ-021 — cisaillement de bord et ⊥ en Python
- [x] ARCH-006 à ARCH-012 (revue)
- [x] ARCH-001 à ARCH-005 — ARCH-002 avec un écart de nom assumé (§15)
- [x] Documentation : `docs/typst/formulas.md`, `api-conventions.md`, `report-engine.md`, `citations.md`, `docs/domain/member-checks.md`, `documents.md`, `positions.md`, `position-plans.md`, `principles.md` (règles 3, 11, 15), `docs/decisions.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en avec la table des remplaçants ; `///`, exemples et traductions de chaque commande.
- [x] Tests : `tests/test_formula.py`, `test_unfold.py`, `test_commands.py`, `test_commands_migrate.py`, `test_distance.py`, `test_quantities.py`, `test_typst_objects*.py`, `test_i18n.py` étendus ; nouveaux fichiers inscrits au catalogue ; suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-017 | capturé |
| T2 | REQ-001 (`role`), REQ-010 | capturé |
| T3 | REQ-010 | capturé |
| T4 | REQ-010, REQ-017 ; variantes → T41 | capturé |
| T5 | REQ-001, ARCH-001 | capturé |
| T6 | REQ-009, REQ-012 | capturé |
| T7 | REQ-007, ARCH-001 | capturé |
| T8 | UI-001 | capturé |
| T9 | — | idée (§9), fait par les issues |
| T10 | REQ-001, REQ-002 | capturé |
| T11 | REQ-009 | capturé |
| T12 | REQ-002 | capturé |
| T13 | REQ-001, REQ-003 ; Q-001 | capturé, une question |
| T14 | REQ-005, CON-007 | capturé |
| T15 | REQ-007, REQ-008 | capturé |
| T16 | REQ-002, REQ-009 | capturé |
| T17 | REQ-004 | capturé |
| T18 | REQ-016 | capturé |
| T19 | REQ-009 | capturé |
| T20 | REQ-017, REQ-018, UI-003 ; Q-003 | capturé, une question |
| T21 | REQ-002, REQ-009 | capturé |
| T22 | REQ-004, REQ-009 | capturé |
| T23 | REQ-013, REQ-018 | capturé |
| T24 | REQ-015, REQ-017, REQ-018 | capturé |
| T25 | REQ-011, REQ-019, ARCH-004 ; Q-002 | capturé, une question |
| T26 | REQ-013, REQ-019 | capturé |
| T27 | REQ-013, UI-002 | capturé |
| T28 | REQ-014 | capturé |
| T29 | REQ-011, REQ-019 | capturé |
| T30 | REQ-015 | capturé |
| T31 | REQ-009 (var-of, value-of retirés ; fmt, render gardés par T39) | capturé |
| T32 | REQ-009 | capturé |
| T33 | REQ-009, REQ-012 | décision (§7) |
| T34 | REQ-002 | décision (§7) |
| T35 | REQ-001 | décision (§7) |
| T36 | REQ-007 ; Q-005 | décision (§7) |
| T37 | REQ-003 ; Q-004 | décision (§7) |
| T38 | REQ-011 | décision (§7) |
| T39 | REQ-009 | décision (§7) |
| T40 | REQ-005, REQ-006 | décision (§7) |
| T41 | REQ-010, REQ-017 | décision (§7) |
| T42 | REQ-012, UI-004 | décision (§7) |
| T43 | REQ-020, CON-004 | décision (§7) |
| T44 | REQ-002, REQ-009 | décision (§7) |
| T45 | toute la spec | portée |

| Q-006 à Q-013 | REQ-002, 010, 011, 012, 013, 017, 019, 021, UI-005, ARCH-004 | décisions (§7) |

### Points de la source non résolus

Aucun : Q-001 à Q-013 répondues le 21.10.2026 sauf Q-005, résolue par défaut. L'interprétation de Q-001, la Q-005 et D-9 à D-13 sont reprises à l'approbation.

## 13. Revue d'architecture

Trois relecteurs `architecture-reviewer` en parallèle, le 21.10.2026 : zone 1 noyau Typst (REQ-001 à 010, 020, UI-001, ARCH-001, 005), zone 2 fichiers de domaine (REQ-011, 012, 017, 018, UI-004, ARCH-002, 003), zone 3 documents, figures, fenêtre (REQ-013 à 016, 019, UI-002, 003, ARCH-004).

### Verdicts

- Zone 1 — **APPROUVER AVEC RÉSERVES**.
- Zone 2 — **APPROUVER AVEC RÉSERVES**.
- Zone 3 — **REVOIR** (risques 301, 302, 304), à lever par les décisions D-1 à D-8 (§10, Q-006 à Q-013) et les ARCH-006 à ARCH-012 ajoutées.

### Existant à réutiliser (relevé par la revue)

- Registre unique `var-registry` (`lib/calc-engine-core.typ:218`), mises à jour pures, `line-note` (fusion en une note, `lib/formula.typ:932`), `evaluate-formula` + `present` (à réutiliser pour `#verify(name-calc:)`), `converted`, `literal-stale` (`lib/formula.typ:1046`, garde-fou d'un littéral vérifié par `domain:`), `wc-meta` (lu par `unfold.query_state`).
- `summary.typ` lit déjà `var-registry.final()` : précédent de `#var-table`.
- Gabarit « JSON de `lib/` + test d'égalité » (`lib/line-levels.json` + `calc/line_levels.py`) : forme de `lib/display-presets.json`. `lib/figure-palette.json` (lu par Typst et Python, testé) : jeton de couleur des citations.
- **Jumeau Python complet des six types de vérification de barres** (`calc/domains/member_check.py:819` `_lines`, feu compris) et `published_vars` (`:1386`, valeurs de table citées) : REQ-017 pour les barres est une transcription, pas un nouveau calcul. Acier, neige, vent, poids propre, connecteurs : déjà calculés en Python. Seul calcul Typst restant : le moment polaire (`lib/calc-engine-connections.typ:140`), qui reste en `#eq`.
- `sync.digest` / `three_way` et la base `[own, seen]` de `unfold.py` : la mécanique de REQ-012 existe. `formula_domain.replace/patched`, `query_state`, `domain_file.domains()` (énumération), `calc/project.py` (chemins), `include` dynamique (`lib/timber.typ:1561`).
- `calc/renamed-commands.json` + `commands_migrate.refusal` (refus d'export qui nomme le remplaçant) : la seule table des retraits.
- `build_reference_calls.wrap_figure` / `figure_label` (`#figure(…, kind: image) <fig-id>`, décision v0.118) : à généraliser en un `call_image_figure` pour les cinq `image-*`. `plan-figure`, `plan-legend`, `plan-scale-bar` déjà partagés.
- Parseur `typst_objects_parse` (`Call.positional`, `Expr` verbatim, `spans` par argument) et précédent `MARKUP_TYPES` (illisible jamais remplacé).
- `position-line` (`lib/calc-engine-core.typ:918`), `position-field` (`lib/positions.typ:79`), `quantities.summary` (agrégateur pur).

### Risques et suite donnée

| Risque | Gravité | Objet | Suite |
|---|---|---|---|
| 101 | bloquant | `timber.typ`/`summary.typ` appellent `var-line`, `val`, `var-unit`, `summary-mark` jusqu'aux lots de REQ-017/018 | les anciens noms deviennent internes dès le lot noyau ; les définitions ne disparaissent qu'au dernier lot (§14) |
| 102, 304 | bloquant | une commande sans définition donne « unknown variable » en Typst ; les anciens tags rendent un fichier non réécrivable | ARCH-006 : l'alerte vient de Python (ouverture et export), entrées `removed` jamais réécrites ; `LEGACY_OBJECT_TYPES` dérivés de `renamed-commands.json` ; critère de REQ-020 reformulé en conséquence |
| 103 | important | `#unit` change de portée sans bruit | le contrôle Python signale tout `#unit(` sans `scope:` (avertissement) ; « Nouveautés » en tête (CON-007) |
| 104 | important | limites d'état Typst pour `"next"`/`"domain"` | consommation dans l'`update` de la commande suivante, sauvegarde/restauration à l'entrée/sortie de `#domain`, `none` jamais `auto` dans le registre ; hors `#domain`, `"domain"` = `"document"` (ARCH-001) |
| 105 | important | `#var-table` lit l'état final ; rôle absent du registre | `role` et ordre de déclaration stockés ; rôle par défaut D-9 |
| 106 | important | `#var(unit:)` : affichage ou mutation | Q-011 |
| 107, 201, 202, 204 | bloquant | `gen` et `own` sans remplaçant ; « sans `id:` = à l'ingénieur » contredit la clé implicite des lignes générées | Q-006 (identité de ligne et valeur gardée) ; ARCH-007 (état de domaine écrit par Python dans `data/`, lu par `#domain` pour la ligne rouge et par `summary`) |
| 108 | important | `id` sur `#var`/`#eq` | `verify_ids` étendu en `line_ids` |
| 109 | important | couleur et format de la citation, trois écrivains du format | D-10 ; `distance-cite` appelle `norm-text`, `variables.py:citation` suit avec ses tests |
| 110 | important | quatre résolveurs de niveau existent | le nouveau résolveur appelle `resolve-level` en dernière couche (ARCH-001) |
| 111 | important | `line-right` hors bloc, fusion des notes, nom de `display-equation` | D-11 ; fusion en une note gardée ; nom confirmé à l'approbation |
| 112 | important | taux de `#verify(name-calc:)` | D-12 |
| 113 | important | `#get` par nom demande un `context` | critère de REQ-009 : `#context get("eta", "value")` |
| 114 | mineur | `formula_domain.py` | `formulas.json` 2.0 → 3.0 (CON-003) |
| 115, 210 | mineur / important | pages à l'octet impossibles pour les domaines transcrits | CON-005 précisée : octet-neutre dans les lots du noyau, « mêmes valeurs imprimées » (extraction de texte avant/après) pour les lots transcrits, référence re-gelée avec la raison |
| 116 | mineur | `///` à refaire, décisions dépassées | CON-002 ; `docs/decisions.md` marque v0.80, v0.87, v0.117 `[partly superseded]` |
| 203 | important | `verify-shear-off`/`-perp` sans jumeau Python | Q-010 |
| 205 | important | journal, liste des positions, métré : la structure est la donnée | Q-008 |
| 206 | important | `#show-load-summary`/`#show-result-summary` sans remplaçant | Q-009 |
| 207 | important | inclusion des fichiers générés | ARCH-008 : index `data/domain-files.json` + `domain-file(kind, id)` |
| 208, 303 | important | `#sync` face à `// woodcore:object` et au partage `calc/sync.py` | ARCH-009 |
| 209 | important | l'égalité Python/Typst des barres | test : fichier généré compilé, `#eq` recalculés = lignes Python à 1e-9 ; oracles gardés |
| 211 à 214 | mineur | stubs, graphe de dépendances, mots allemands en dur dans `unfold.py`, `WRITERS` | ARCH-011 ; arêtes depuis `#include` et ids de `#sync` ; mots dans `calc/i18n/strings.json` ; écrivains dans `tab_guard.WRITERS` |
| 301 | bloquant | lire un `#table` brut quelconque | ARCH-004 précisée : sous-ensemble documenté, écriture par étendues, illisible affiché en lecture seule et jamais remplacé ; pertes Q-012 |
| 302 | bloquant | `#sync` copie ce que `doc-value` lit vivant | Q-007 ; ARCH-010 (contrôle d'obsolescence) ; grammaire d'id `domaine/instance/variable` |
| 305 | important | style des tables brutes, légende numérotée | règle `#show: doc-tables` définie une fois, appliquée aux seules sections de document |
| 306 | important | feuilles sans `sheet-*` | Q-013 ; un primitif de page interne gardé, boîtes émises par `image-*` |
| 307 | important | noms d'arguments des `image-*` (`id`, `label`, `detail`) | D-13, ARCH-012 ; `kind: image` dans le texte copié |
| 308 | important | `#member` enregistre b, h, A… pour les `verify-*` | l'alerte de `#member` renvoie au fichier de domaine ; `#position` n'est que l'affichage ; table argument → clé dérivée de `position-list-columns-all` ; `length` lu de `quantities.json` |
| 309 | mineur | paramètre `table` masque `table()` dans `distance` | variable interne renommée |
| 310 | important | `quantities.json` écrit à l'export seulement | onglet Métré : agrégation par `quantities.summary` (pas de recalcul géométrique), date de l'export et bandeau « périmé » (`calc/stamps.py`) |
| 311 | important | test des boutons « Copier » trop étroit ; ordre | test sur toutes les entrées de `tab_registry` et `build_reference_calls` contre `renamed-commands.json` ; UI-002 après les générateurs |
| 312, 313 | mineur | arêtes depuis les noms de commandes ; CON-001/002 | arêtes depuis les ids de `#sync` ; entrées des commandes retirées supprimées de `CATEGORIES` et `commands.json` |

### Exigences ajoutées par la revue

#### ARCH-006 — Les retraits sont signalés par Python
- **Exigence** : les commandes et arguments retirés sont signalés à l'ouverture et à l'export depuis `calc/renamed-commands.json` (section `arguments` ajoutée, `schema_version` 1.1, entrées `removed` jamais réécrites) ; les anciens types d'objet restent lisibles, affichés « commande retirée », jamais réécrits ni restaurés.
- **Source** : revue (102, 304)
- **Critère d'acceptation** : un projet contenant `#val` s'ouvre, ses sections restent lisibles, l'export refuse en nommant fichier, ligne et remplaçant.

#### ARCH-007 — L'état d'un fichier de domaine est écrit par Python
- **Exigence** : la forme écrite, les lignes en écart et la structure non appliquée sont calculées par Python et écrites dans `data/domain-state.json` (schéma versionné) ; `#domain` y lit sa ligne rouge, `summary` y reconnaît les vérifications. `gen` quitte `checks.json` (version montée) et le `.typ`, et reste dans la base de régénération.
- **Source** : revue (107, 204)
- **Critère d'acceptation** : un domaine dont le générateur a changé de forme imprime la ligne rouge sans que Woodcore ait réécrit son fichier.

#### ARCH-008 — Un index des fichiers de domaine
- **Exigence** : `data/domain-files.json` (schéma versionné) donne le fichier de chaque domaine ; Typst l'inclut par une seule fonction `domain-file(kind, id)`.
- **Source** : revue (207)
- **Critère d'acceptation** : les sections du rapport bouclent `for id in ids(kind) { include domain-file(kind, id) }` ; un domaine sans fichier arrête l'export en le nommant.

#### ARCH-009 — `#sync` en bas de chaîne, lu par le lexeur
- **Exigence** : `#sync` est défini au plus bas de la chaîne d'imports ; Python le lit et l'écrit par le lexeur (`calc/typst_sync.py`), jamais par regex ; le hash du partage entre documents (`calc/sync.py`) ignore le contenu des `#sync`.
- **Source** : revue (208, 303)
- **Critère d'acceptation** : rafraîchir une valeur `#sync` dans un bloc partagé ne change aucun état de partage.

#### ARCH-010 — Contrôle d'obsolescence des `#sync`
- **Exigence** : à l'export, chaque `#sync` est comparé à ce que Python écrirait ; un écart est un avertissement qui nomme fichier et id, jamais un écrasement ; le rafraîchissement est une action. Le texte écrit par Python passe par un seul formateur, tenu égal à `fmt-number` par test.
- **Source** : revue (302)
- **Critère d'acceptation** : une charge modifiée dans les données fait signaler la cellule `#sync` correspondante sans la réécrire.

#### ARCH-011 — Un registre de générateurs
- **Exigence** : un seul registre `GENERATORS = {kind: générateur}` ; `domain_file.STUBS`, `stub_text`, `is_untouched` et `unfold_migrate.py` disparaissent.
- **Source** : revue (211, 213)
- **Critère d'acceptation** : une seule table des types de domaine (grep).

#### ARCH-012 — Un vocabulaire pour les cinq `image-*`
- **Exigence** : une table unique du vocabulaire des arguments des cinq `image-*`, un seul constructeur `call_image_figure` côté Python.
- **Source** : revue (307)
- **Critère d'acceptation** : les cinq boutons « Copier » passent par `call_image_figure`.

### Recommandations reprises à l'approbation

- **D-9** rôle par défaut : `#var` → `"data"`, `#eq` → `"compute"`, `#verify` → `"result"`.
- **D-10** citation : « SIA 265 4.2.1 » (sans « § », sans virgule), jeton `citation` dans `lib/figure-palette.json` à la valeur `ink-soft` #5b646c (lisible à 8 pt), appliqué à la colonne de droite et aux citations en ligne, pas aux notes de bas de page.
- **D-11** `norm-position: "line-right"` dans une phrase : refusé avec un message (il faut une ligne propre).
- **D-12** `#verify(name-calc:)` garde le taux gauche/droite pour `<=` et `<`, droite/gauche pour `>=` et `>`, refus pour `=` ; `name-visible` imprime alors `nom = taux ≤ 1.00 ✓`.
- **D-13** `image-*` : l'objet en positionnel (`image-positions-plan("PL-1")`), la légende laissée au `#figure` natif (pas de `label`/`caption` dans `image-*`), `width` sur les cinq, `detail-figure` aux valeurs propres à chaque commande (`detail`/`zoom` actuels → `detail-figure: "zoom"`), `highlight` sur quatre.

## 14. Plan d'implémentation

Règles de tout le plan : aucune commande retirée tant qu'un modèle, un exemple, un générateur ou un bouton l'appelle (ARCH-RISK-101, 311) ; les anciens noms cessent d'être publics dès leur lot et leurs définitions disparaissent au lot 19 ; un commit par lot (« Commandes Typst, lot n »), comme les specs précédentes, aucun push sans le mot de l'ingénieur ; chaque lot finit avec ses tests verts, ses `///`, exemples et traductions (CON-002) et une ligne au §16. Les lots 1 à 6 sont le noyau (issue #75, #76), 7 à 8 la synchronisation (#77), 9 à 14 les domaines (#79, #80), 15 à 17 les figures et feuilles (#78), 18 les documents (#81), 19 et 20 les retraits et la documentation (#82).

| Lot | Contenu | Fichiers principaux | Éléments | Tests qui le prouvent |
|---|---|---|---|---|
| 0 | Caractérisation : référence des pages verte, tests du comportement actuel de `unit`, `own`, `note`, `val`, `var-unit` | `tests/test_formula.py`, `tests/test_report_golden.py` | CON-005 | suite actuelle verte, nouveaux tests de caractérisation |
| 1 | Citations grises sans « § » : jeton `citation` dans `lib/figure-palette.json`, `norm-text` seul écrivain (`distance-cite` l'appelle), `calc/variables.py:citation` aligné ; référence des pages re-gelée | `lib/calc-engine-core.typ:682`, `lib/distance.typ:155`, `lib/figure-palette.json`, `calc/variables.py:183` | UI-001, D-10 | `test_variables.py`, `test_distance.py`, `test_figure_palette.py`, `test_report_golden.py` |
| 2 | Infrastructure des retraits : `renamed-commands.json` 1.1 (section `arguments`, entrées `removed` jamais réécrites), alertes à l'ouverture et à l'export, `LEGACY_OBJECT_TYPES` dérivés de la table, `restore` refuse un type retiré, avertissement `#unit(` sans `scope:` | `calc/renamed-commands.json`, `calc/domains/commands_migrate.py`, `calc/structure_tags.py`, `calc/removed_objects.py`, `calc/export_all.py:161` | ARCH-006, REQ-020 (mécanisme), CON-004, CON-007 | `test_commands_migrate.py`, `test_structure.py` |
| 3 | Résolveur d'affichage : `lib/display-presets.json` + `resolve-display` (appelle `resolve-level`), `#calc-defaults`, `#unit(scope:)`, `#domain` (renommé, portées sauvegardées et restaurées, `label`/`descr`/`norm`/`level`), `line_ids` ; octet-neutre sauf `#unit` | `lib/calc-engine-core.typ`, `lib/formula.typ:1676`, `:1733`, nouveau `lib/display-presets.json` | REQ-005, 006, 007, 008, ARCH-001, Q-005 | `test_formula.py`, nouveau `test_display_presets.py` (JSON complet, égal au tableau de `formulas.md`) |
| 4 | Arguments communs : `display`, `display-formula`/`display-equation`, `role` (D-9), `*-position` (fusion en une note, D-11), `norm-section`, `style`, `id` sur `#var`/`#eq`/`#verify` ; `#var` réaffiche (affichage seul, héritage sans `level`/`id`) ; `#eq` `unit`/`as-unit` ; `#verify` `name-calc`/`name-visible` (D-12) et citation ; `#val`, `#var-unit`, `#var-line`, `own`, `note`, `sep`, `summary` deviennent internes | `lib/formula.typ`, `lib/bibliography.typ:13`, `lib/timber.typ`/`lib/summary.typ` (appels internes) | REQ-001 à 004, REQ-009 (en partie), Q-001, Q-011 | `test_formula.py` (une section par argument et valeur, refus des valeurs hors liste), `test_bibliography.py`, `test_report_golden.py` octet-neutre |
| 5 | `#var-table` (rôle, domaine, liste, `"all"`, filtre `unit:`, colonnes, avant les déclarations) et `#get` par nom | `lib/formula.typ`, `lib/calc-engine-core.typ:474` | REQ-009, REQ-010, Q-009 | `test_formula.py`, `test_summary.py` (mêmes valeurs que `show-load-summary`/`show-result-summary`) |
| 6 | Onglet « Formules » sur les nouvelles formes : `formula_domain.py` (`#domain`, `display`, `role`, `*-position`, plus de `#val`/`#var-unit`/`own`), `formulas.json` 3.0 | `calc/domains/formula_domain.py`, `calc/build_reference_calls.py`, `schemas/formulas.schema.json` | ARCH-005, CON-003 | `test_formula_domain*.py` |
| 7 | `#sync` : définition en bas de chaîne, `calc/typst_sync.py` (lexeur, ids `domaine/instance/variable`), hash du partage ignorant le contenu des `#sync`, contrôle d'obsolescence à l'export, formateur unique tenu égal à `fmt-number` | `lib/calc-engine-core.typ`, nouveau `calc/typst_sync.py`, `calc/sync.py:106`, `calc/export_all.py` | REQ-011, ARCH-009, ARCH-010, Q-007 | nouveau `test_typst_sync.py`, `test_sync.py` |
| 8 | Régénération : registre `GENERATORS` tiré de `unfold.py`, `id:` sur chaque ligne, plus d'`own`/`gen` dans le `.typ`, `data/domain-state.json` et `data/domain-files.json` (schémas), `domain-file(kind, id)`, ligne rouge de `#domain`, alerte et « Ajouter » dans la fenêtre, `as-unit` signalé dans la fenêtre ; la traction migrée ; `checks.json` sans `gen` (version montée) | `calc/domains/unfold.py` → `calc/domains/domain_gen.py`, `calc/domains/member_check.py:1346`, `calc/tools/formula_tab_unfold.py`, `calc/tools/tab_guard.py`, `schemas/` | REQ-012, UI-004, ARCH-002, 007, 008, 011, Q-004, Q-006 | `test_unfold.py` (réécrit), `test_domain_file.py`, `test_member_check.py`, `test_tab_guard*`, `test_export.py` |
| 9 | Vérifications de barres : générateurs compression, flexion, cisaillement, flambement, déversement, feu ; cisaillement de bord et ⊥ portés en Python avec le menu de l'onglet Cisaillement | `calc/domains/member_check.py`, `calc/domains/domain_gen.py`, `calc/tools/member_check_tab.py:780` | REQ-017 (barres), REQ-021, UI-005, ARCH-003 | nouveau `test_domain_generators.py` (fichier compilé = lignes Python à 1e-9, `norm:` sur chaque valeur de norme), `test_timber.py` (oracles), `test_member_check_tab.py` |
| 10 | Acier : générateur | `calc/domains/steel_check.py`, `domain_gen.py` | REQ-017 (acier) | `test_domain_generators.py`, `test_steel*.py` |
| 11 | Charges : poids propre, neige, charges utiles, vent (dans cet ordre) | `calc/domains/dead_load.py`, `snow*.py`, `live_load*.py`, `wind*.py`, `domain_gen.py` | REQ-017 (charges) | `test_domain_generators.py`, extraction de texte avant/après |
| 12 | Connecteurs | `calc/domains/connector.py`, `domain_gen.py` | REQ-017 (connecteurs) | idem |
| 13 | Moments polaires : géométrie en `#var`, N/V/M écrits pour l'ingénieur, forces par fixation en `#eq` | `calc/domains/connection.py`, `domain_gen.py` | REQ-017 (moments polaires) | idem, égalité avec `fastener_forces` |
| 14 | Journal, liste des positions, onglet « Métré » (carte → onglet, lecture de `quantities.json`, bandeau « périmé ») et leurs fichiers ; `#position` | `calc/tools/positions_tab.py:539`, nouvel onglet, `calc/tools/tab_registry.py:55`, `calc/domains/quantities.py`, `lib/positions.typ` | REQ-015, REQ-017 (listes), UI-003, Q-003, Q-008 | nouveau `test_metre_tab.py`, `test_quantities.py`, `test_position_list.py` |
| 15 | Figures : `#image-positions-plan`, `#image-fire-plan`, `#image-static-model`, `#image-schema`, `#image-extract` (corps des `show-*` sans `figure`), table de vocabulaire, `call_image_figure` ; `#distance` renommé | `lib/calc-engine-drawings.typ`, `lib/distance.typ:269`, `calc/build_reference_calls.py:281-361`, `calc/tools/plan_command_builder.py` | REQ-013, 014, 016, ARCH-012, D-13 | `test_plan_command_builder.py`, `test_distance.py`, `test_schema.py` |
| 16 | Tableau brut dans l'onglet Structure : parseur (sous-ensemble), modèle par étendues, colonnes cachées et alignement, lecture seule hors sous-ensemble | `calc/typst_objects_parse.py:499`, `calc/typst_objects.py`, `calc/typst_objects_models.py:238`, `calc/tools/object_panes_table.py` | ARCH-004, Q-012 | `test_typst_objects.py`, `test_object_panes.py` |
| 17 | Feuilles en Typst brut : primitif de page interne, `#image-section`, `#image-legend`, `#image-titleblock`, listes par fichiers de domaine, éditeur sur `#place(…)` | `lib/sheet.typ`, `calc/sheets.py`, `calc/tools/sheet_editor*.py` | REQ-019 (feuilles), Q-013 | `test_sheets.py`, `test_sheet_editor.py`, `test_sheet_bundles_tab.py` |
| 18 | Modèles réécrits : CU, BP, RS × de/fr/en et projet exemple en Typst brut + `#sync` + `domain-file`, règle `#show: doc-tables` ; outil de réécriture local, hors production ; référence des pages re-gelée par document | `templates/documents/*/standard/*`, `tests/projet-exemple/`, `lib/document.typ` | REQ-017, REQ-019, Q-002 | `test_doc_templates.py`, `test_document_commands.py`, `test_report_golden.py` |
| 19 | Retraits : boutons « Copier » (UI-002), définitions retirées de `lib/` (noyau, domaines, `doc-*`, `sheet-*`), `domain_file.py`, `unfold_migrate.py`, modèles et panneaux d'objets, `CATEGORIES`, `commands.json`, `dependency_graph.COMMAND_REFERENCES` (arêtes depuis `#include` et `#sync`) | `lib/*.typ`, `calc/tools/*`, `calc/build_reference*.py`, `calc/domains/dependency_graph.py` | REQ-009, 018, 019, 020, UI-002 | test « aucun bouton ne copie une commande retirée », `test_commands.py`, `test_dependency_graph.py`, `test_commands_migrate.py` |
| 20 | Documentation : `docs/typst/*`, `docs/domain/*`, `principles.md` (règles 3, 11, 15), `decisions.md` (nouvelles décisions, v0.80/v0.87/v0.117 `[partly superseded]`), table ancienne → nouvelle commande, `CHANGELOG.md`, « Nouveautés » fr/de/en (portée de `#unit` en tête), catalogue des tests | `docs/`, `CHANGELOG.md`, site | §11 Documentation | `test_docs_coherence.py`, `test_i18n.py`, suite complète |

## 15. Vérification

Vérification indépendante (`requirements-verifier`, base `878bda8`, HEAD `3d8ab91` puis l'arbre corrigé), deux tours, 2026-10-22. Tests ciblés lancés par le vérificateur (la suite complète est verte par ailleurs) ; aucune régression réelle.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `lib/formula.typ` `var`, `eq`, `verify` : arguments communs, sans `note:`/`own:`/`sep:` ; `test_fine_display` (23) dont les valeurs hors liste refusées |
| REQ-002 | ✅ | `lib/formula.typ` `var` ; `test_fine_display` (réaffichage, `unit:` à l'affichage, registre gardant son unité, Q-011) |
| REQ-003 | ✅ | `eq` (`unit`, `as-unit`, `display-formula`, `display-equation`) ; `test_fine_display` ; `as-unit` dit dans la fenêtre (`formula_tab_widgets.py`, `fm_as_unit`) |
| REQ-004 | ✅ | `verify` ; `test_fine_display.test_verify_keeps_its_ratio_under_a_name_and_prints_it_under_another`, `test_verify_cites_its_norm_and_registers_it` |
| REQ-005 | ✅ | `unit(written, scope: "next")` ; `test_fine_display` (portées next, domain, document) |
| REQ-006 | ✅ | `calc-defaults` ; `test_fine_display` |
| REQ-007 | ✅ | `lib/display-presets.json` ; `test_fine_display` (table égale à `formulas.md`, priorité, `uniform`) |
| REQ-008 | ✅ | `domain(id, label:, …)` sans `gen` ; `test_fine_display` |
| REQ-009 | ✅ | aucune définition `val`, `var-unit`, `var-line`, `show-input`, `show-check`, `calc-block`, `var-of`, `value-of` dans `lib/` ; `get(v, field, domain:)` |
| REQ-010 | ✅ | `var-table` ; `test_fine_display`, `test_formula`, `test_report_golden` |
| REQ-011 | ✅ | `sync`, `calc/typst_sync.py` ; `test_typst_sync` (9) |
| REQ-012 | ✅ | `unfold.domain_state` ; `test_unfold.test_a_domain_that_no_longer_matches_its_data_says_so_in_red_and_is_not_rewritten` |
| REQ-013 | ✅ | `image-positions-plan` ; `test_image_figures`, `test_plan_command_builder` |
| REQ-014 | ✅ | les quatre autres `image-*` ; `test_image_figures` |
| REQ-015 | ✅ | `lib/positions.typ` `position` ; `test_position_list` (11), `test_renumbering` (position archivée) |
| REQ-016 | ✅ | `distance(table:, label:, norm-section:, id:, level:)` ; `test_distance` (24) ; `tab`/`title`/`norm-ref` dits par `test_commands_migrate.test_the_old_arguments_of_distance_are_said_with_what_to_write` (2ᵉ tour) |
| REQ-017 | ✅ | `unfold.GENERATORS` ; `test_domain_generators` (7), `test_unfold`, `test_list_files`, `test_metre_tab`, `test_doc_templates` (41), `test_report_golden` |
| REQ-018 | ✅ | plus de `show-*` de domaine, `verify-*`, `member`, `schema`, `sheet-*` dans `lib/` ; `test_commands_migrate.test_no_button_copies_a_retired_command`, `test_no_file_of_the_engine_the_templates_or_the_example_calls_an_old_name` |
| REQ-019 | ✅ | `doc-tables` seul `doc-*` ; `image-section`/`-legend`/`-titleblock` ; `test_doc_templates`, `test_document_commands`, `test_sheets`, `test_sheet_editor` |
| REQ-020 | ✅ | `calc/renamed-commands.json` 1.1 (86 noms, `arguments`) — le 2ᵉ tour a ajouté les huit noms publics retirés qui manquaient (`verify-compression-perp`, `verify-bending-normal`, `verify-shear-off`, `verify-shear-perp`, `line-level`, `position-list-ids`, `summary-mark`, `summary-report-rows`) ; le vérificateur a comparé les 110 commandes documentées à `878bda8` : aucune manquante ; table dans `api-conventions.md` §10bis |
| REQ-021 | ✅ | `test_unfold.test_a_shear_off_and_a_shear_across_the_grain_unfolded_compute_what_python_computes`, `test_member_check` (75) |
| UI-001 | ✅ (écart de nom) | `cite-text`, couleur lue dans `lib/figure-palette.json` ; jeton `ink-soft` existant et non un jeton `citation` de même valeur, que `test_figure_palette` refuse (journal lot 1) ; `test_formula` |
| UI-002 | ✅ | `test_commands_migrate.test_no_button_copies_a_retired_command` ; `call_image_figure` |
| UI-003 | ✅ | `calc/tools/metre_tab.py` ; `test_metre_tab` (2) |
| UI-004 | ✅ | `formula_tab_unfold.refresh_unfold` : l'alerte en rouge du thème ; `test_member_check_tab.test_a_domain_whose_form_no_longer_matches_its_check_says_so_in_red_in_the_formulas_tab` (2ᵉ tour ; ❌ au 1ᵉʳ) |
| UI-005 | ✅ | `test_member_check_tab.test_the_shear_tab_offers_its_three_checks_in_a_list` |
| ARCH-001 | ✅ | `resolve-display` unique, préréglages dans `lib/display-presets.json` |
| ARCH-002 | ⚠️ (écart assumé) | registre `GENERATORS` unique ; `gen` hors de `checks.json` (1.6) ; `domain_file.py` reste pour la seule réconciliation (`sync`, `domains`, `path_of`), sans stubs, et `unfold.py` n'est pas renommé `domain_gen.py` (§14 lot 8) : aucun effet fonctionnel |
| ARCH-003 | ✅ | `test_domain_generators` (norm: sur chaque valeur de norme) |
| ARCH-004 | ✅ | `test_raw_table` (7), `test_object_panes` (31), `test_typst_objects` (45) |
| ARCH-005 | ✅ | `test_formula_domain` (33), `test_formula_tab` |
| ARCH-006 | ✅ | `test_removed_objects` (6), `test_commands_migrate` |
| ARCH-007 | ✅ | `unfold.domain_state` ; `test_unfold`, `test_domain_generators` |
| ARCH-008 | ✅ | `domain-file` ; `test_unfold`, `test_dependency_graph` (règle `file`) |
| ARCH-009 | ✅ | `test_typst_sync.test_a_refreshed_value_changes_no_state_of_a_block_shared_between_documents` |
| ARCH-010 | ✅ | `test_typst_sync` (littéraux périmés nommés, nombre écrit = nombre imprimé) |
| ARCH-011 | ✅ | `STUBS`, `stub_text`, `is_untouched`, `unfold_migrate.py` retirés ; `test_domain_file` |
| ARCH-012 | ✅ | `lib/image-vocabulary.json` ; `test_plan_command_builder`, `test_image_figures` |
| CON-001 à CON-003 | ✅ | `test_i18n` (27), `test_commands` (43) |
| CON-004, §8 | ✅ | aucune migration automatique des retraits ; §8 non touché |
| CON-005 | ✅ | `test_report_golden`, raison dans `CHANGES` |
| CON-007 | ✅ | « Nouveautés » 0.120 fr/de/en, la portée de `#unit` en tête |
| Documentation | ✅ | `formulas.md`, `api-conventions.md`, `report-engine.md`, `citations.md`, `docs/domain/*`, `principles.md`, `layout.md`, `decisions.md`, `CHANGELOG.md` ; les quatre lignes `verify-*` de `member-checks.md` complétées au 2ᵉ tour ; `test_docs_coherence` (7) |

Corrigé entre les deux tours : UI-004 (alerte rouge et test), REQ-016 (`title` et test), les huit noms de REQ-020, les commentaires `gen:` et le bloc mort `gens` de `lib/`, deux tests fragiles à l'ordre d'import (`test_member_check_tab`, `test_linkable_spin`).

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-21 | draft | spécification extraite du retour de l'ingénieur, de ses réponses et des issues #74 à #82 ; existant cartographié (noyau `lib/formula.typ`, `unfold.py`, `lib/document.typ`, `lib/sheet.typ`, boutons « Copier ») ; 5 questions |
| 2026-10-21 | specified | Q-001 à Q-004 répondues (deux arguments d'affichage pour `#eq`, checklists retirées, carte Métrés → onglet, `as-unit` signalé dans la fenêtre seulement) ; Q-005 par défaut |
| 2026-10-21 | reviewed | revue d'architecture en trois zones (noyau : réserves ; domaines : réserves ; documents : revoir, levé par Q-006 à Q-013 et ARCH-006 à 012) ; Q-006 à Q-013 répondues ; REQ-021 et UI-005 ajoutées ; plan en 21 lots |
| 2026-10-21 | approved | approuvée par l'ingénieur, avec les sept points par défaut (interprétation de Q-001, Q-005, D-9 à D-13) |
| 2026-10-21 | implementation | lots 0 à 12 — leurs lignes, telles qu'écrites, sont dans `docs/history/2026-10-21-commandes-typst-refonte-journal-lots-0-12.md` (la spécification sous 100 Ko) |
| 2026-10-21 | implementation | lots 13 à 18 — leurs lignes, telles qu'écrites, sont dans `docs/history/2026-10-21-commandes-typst-refonte-journal-lots-13-18.md` (la spécification sous 100 Ko) |
| 2026-10-22 | implementation | lot 19 — retraits (UI-002, REQ-009, REQ-017, REQ-019) : les définitions retirées quittent `lib/` (noyau, `val`/`var-unit`/`var-line`/`var-domain`, `show-*`, `verify-*`, `member`, `calc-block`, `doc-*` sauf `doc-tables`, `sheet-*` ; `timber.typ`, `steel.typ`, `summary.typ` supprimés ; ~6 000 lignes de moins), leurs entrées de `commands.json`, `CATEGORIES`, les générateurs d'appels, les modèles et volets d'objets `doc-*`, `domain_file.STUBS`/`stub_text`/`is_untouched` (un stub d'une version antérieure reste reconnu octet pour octet et réécrit : `unfold.LEGACY_STUBS`), `unfold_migrate.py` et `woodcore-cli unfold migrate` ; `dependency_graph` lit `#include domain-file(kind, id)` (règle `file`) ; `gen` quitte `data/checks.json` (1.6) ; `sheets.add_position_list`/`add_quantities`/`new_position_list_sheet` sans `plans`/`scope`/`storey` (Q-015) ; `calc/renamed-commands.json` porte les 78 noms retirés. Rendu à l'identique de ce que les commandes retirées imprimaient : les légendes des deux figures d'un connecteur, le dessin d'une charge permanente, la ligne d'appel d'un `result()` sans norme, la ligne orange d'une position archivée (`#position`) ; `#var(nom, domain: …)` lu par la migration des charges. Test UI-002 : aucune chaîne de la fenêtre ni générateur n'écrit une commande retirée. Pertes à signaler : la torsion n'est plus calculée ; le verdict en pour-cent ; les flèches de forces sur la figure d'une connexion (`test_arrows` retiré) ; la sélection manuelle `level: -1, shown:` ; la portée et les plans d'une liste de feuille (Q-015) ; la légende automatique d'un extrait. Page d'or : page 8 du rapport (`#position` joint dimension et unité), raison dans `CHANGES`. |
| 2026-10-22 | testing | lot 20 — documentation : `docs/typst/api-conventions.md` §10bis (les lignes de référence des commandes retirées déplacées telles quelles dans `docs/history/typst-retired-commands.md`, des lignes pour `domain`, `domain-file`, `sync`, `calc-defaults`, `var-table`, `position`, les `image-*`, `doc-tables`, et la table « ce que devient un appel » tirée de `calc/renamed-commands.json`) ; `formulas.md` et `report-engine.md` (leurs sections sur `#val`, `#var-line`, `#var-unit`, `#var-domain`, `note:`/`sep:`/`summary:`, `#calc-block`, `#show-input` déplacées dans `docs/history/`, remplacées par la forme actuelle) ; chaque paragraphe de `docs/domain/`, `docs/ui/` et de `open-questions.md` qui décrit une commande retirée le dit en tête, avec quoi écrire (la même source) ; `principles.md` règles 3, 11, 15 ; `layout.md` ; `decisions.md` : trois décisions et le statut de douze qu'elles remplacent (index à jour) ; `CHANGELOG.md` ; « Nouveautés » 0.120 en trois langues, la portée de `#unit` en tête (CON-007) ; les tutoriels du site ; le catalogue des tests ; ces lignes du journal pour les lots 13 à 18 déplacées dans `docs/history/`. |
| 2026-10-22 | verification | vérification indépendante en deux tours (`requirements-verifier`) : au 1ᵉʳ, UI-004 ❌, REQ-016, ARCH-002, la documentation de quatre `verify-*` et deux tests fragiles ⚠️ ; corrigés (alerte rouge de l'onglet et son test, `#distance(title:)` dit et testé, huit noms publics retirés ajoutés à `calc/renamed-commands.json`, commentaires `gen:` et bloc mort `gens` retirés, imports après la fenêtre) ; au 2ᵉ, tout ✅ sauf ARCH-002, écart de nom assumé (`domain_file.py` garde la réconciliation, `unfold.py` non renommé). Tableau au §15, §11 coché. |
| 2026-10-22 | completed | décisions de l'ingénieur après la vérification : ARCH-002 accepté tel quel (`domain_file.py` garde la réconciliation, `unfold.py` non renommé) ; la torsion, la sélection manuelle `level: -1`, la légende automatique d'un extrait laissées ; #82 fermée (un appel ancien arrête tout le document, les « Nouveautés » résument) ; correction : le taux en pour-cent n'était pas perdu (`unit: "%"`), le pour mille ajouté (`unit: "%%"`, imprimé ‰) ; `#distance` : `label:` est le titre de chaque tableau, `tab:`, `title:`, `norm-ref:` retirés ; deux suites en issues — la liste des positions et le métré créés depuis leurs onglets, les restes du `level: -1` dans la fenêtre ; les flèches d'un moment polaire, `#image-polar-moment`, une spec à part. Spécification déplacée dans `completed/`. |
