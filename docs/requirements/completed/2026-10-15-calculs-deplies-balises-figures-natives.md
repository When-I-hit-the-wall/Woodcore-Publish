---
id: 2026-10-15-calculs-deplies-balises-figures-natives
titre: Calculs dépliés en Typst, balises robustes et figures natives
status: completed
cree: 2026-10-15
mis_a_jour: 2026-10-15
source: message écrit (conversation du 15.10.2026, dictée, quatre messages et les réponses aux questions)
docs: [docs/architecture/principles.md, docs/typst/formulas.md, docs/ui/tab-formulas.md, docs/domain/member-checks.md, docs/ui/tab-member-checks.md, docs/domain/documents.md, docs/domain/detail-schemas.md, docs/ui/tab-schemas.md, docs/domain/variable-links.md, docs/decisions.md]
---

# Calculs dépliés en Typst, balises robustes et figures natives — Spécification

## 1. Objectif

Aujourd'hui une vérification enregistrée dans Woodcore est imprimée par une commande toute faite (`#show-check-member("ZT-01")`) : toujours à jour, mais opaque — on ne voit ni ne modifie ses lignes ou ses tableaux —, et les balises en commentaires (`// woodcore:object …`) qui permettent à Woodcore de retrouver ce qu'il édite sont fragiles et provoquent des erreurs d'aller-retour. L'ingénieur veut que **le calcul soit écrit en entier dans le `.typ`**, en commandes de base (`#var`, `#eq`, `#verify`) qu'il peut lire et modifier dans VS Code comme dans Woodcore, **sans qu'un calcul puisse vieillir en silence** : chaque valeur venue de l'export est écrite en clair et contrôlée contre lui, chaque objet porte une balise que le compilateur vérifie, et ce qui est modifié à la main d'un côté est vu et repris de l'autre. Les figures suivent le même principe : Woodcore fournit le dessin, l'ingénieur écrit la figure en Typst natif. Premier périmètre : les domaines de l'onglet « Formules », la vérification à la traction, les schémas de détail.

## 2. Source

Les messages de l'ingénieur, mot pour mot (dictés), et ses réponses aux questions de l'assistant. Les propositions de l'assistant auxquelles les réponses renvoient sont résumées entre crochets, sans valeur de source.

> **T1** — « Le problème que j'ai actuellement, c'est que Woodcore permet la modification de fichiers TIPST, que ce soit dans l'aperçu des différents PDF, donc de la convention d'utilisation, de la base de projet et du rapport de statique. Également, ça permet d'interagir avec du fichier TIPST dans les formules. Et le problème de tout ça, c'est que ça produit beaucoup d'erreurs dans un va-et-vient lorsque des balises sont écrasées, lorsqu'il y a une forme qui est utilisée dans TIPST qui n'est pas acceptée ou prise en compte dans Woodcore. »
>
> **T2** — « avec les commandes toutes faites à copier-coller, comme par exemple une commande pour copier-coller une vérification à la traction, eh bien on perd beaucoup de flexibilité, car l'on peut que copier-coller en fait une commande. On peut pas voir l'entièreté des calculs qui sont faits, ou peut-être s'il y a un tableau, l'on peut pas directement aller modifier le tableau. »
>
> **T3** — « il faut prendre en compte également le fait que des calculs peuvent vieillir de manière silencieuse et ne plus être mis à jour parce qu'une balise a été supprimée et donc Woodcore n'actualise plus le fichier TIPST. »
>
> **T4** — « Soit TIPST génère des fichiers JSON, donc par exemple une vérification à la traction, ça génère un fichier JSON et ensuite du code Python permet de convertir ce fichier JSON en fichier TIPST lisible pour l'utilisateur et où tout est contenu dedans. Donc les tableaux, les références aux normes, les calculs. Et donc tout est écrit en format TIPST avec uniquement quelques commandes de base que l'on a implémentées nous-mêmes comme la commande VAR, la commande EQ, la commande VERIFY. »
>
> **T5** — « Comment est-ce que les balises sont enregistrées? Si c'est juste un commentaire dans TIPST, la balise, c'est quelque chose de très faible. Si tout est paramétrique, comme par exemple il y a des tableaux avec plein de choses paramétriques, eh bien le problème c'est que l'utilisateur ne peut plus voir les données qui sont rentrées car c'est juste un paramètre qu'il peut voir dans le fichier TIPST. »
>
> **T6** — « Peut-être par exemple une solution ce serait que dans chaque commande VAR, EQ ou VERIFY, qu'il y ait un argument de balise. Ou qu'il y ait un ID pour toutes les commandes et que l'ID et la balise. De cette manière, peu importe où la commande se trouve et si elle a été modifiée ou non par l'utilisateur, la balise peut être retrouvée par Woodcore. Et si elle a été supprimée, l'utilisateur peut la réintégrer si par exemple il a supprimé une ligne du calcul de neige. »
>
> **T7** — « L'autre manière que je vois de faire, c'est que Woodcore génère immédiatement des TIPST et non pas de JSON, mais je trouve ça dangereux. »
>
> **T8** — « lorsque l'on exporte une figure, donc un système statique ou un schéma, eh bien, il y a un SVG évidemment qui est généré par Woodcore et qu'il faut importer, mais dans Tipst, on peut réellement écrire une figure. Donc on peut faire hashtag figure, dans la figure avoir une image, avoir un caption, avoir un label, et on peut vraiment écrire du fichier Tipst et pas avoir l'impression de devoir utiliser une commande spécifique inventée sur le coup pour en fait faire quelque chose de très simple qui est juste afficher une figure. »
>
> **T9** — « Pour ton point 3, je valide effectivement l'idée B, C, D et E. » [B : la balise est un argument de la commande ; C : labels natifs Typst ; D : `typst query` pour lire l'état ; E : fichier annexe comme base de fusion seulement.]
>
> **T10** — « Et je valide l'idée d'un calcul déplié, comme tu l'as indiqué, avec l'argument from. Je me demande si on ne peut pas remplacer l'argument from par l'argument domaine, vu que c'est quelque chose qui existe déjà. Ou alors, est-ce qu'il faut tout passer sur l'argument from? »
>
> **T11** — « Pour le point 5, je valide l'idée A de garder le point TYP comme source. » [Documents CU/BP : le `.typ` reste la source, balises en arguments et écriture ciblée.]
>
> **T12** — « Il faudra donc pour le point 6 changer la règle 15 qui est vraie pour la fenêtre mais qui n'est plus du tout vraie pour les calculs car tout le code TYPST est montré dans les fichiers. TYPST. »
>
> **T13** — « Pour le point 3, il n'y a pas comme alternative, il y a uniquement le déplié. Comme ça on diminue le code mort. » [`#show-check-member` disparaît.]
>
> **T14** — « Pour le point 4, je valide le périmètre de faire cela pour les formules, ainsi que pour la vérification à l'attraction, et ainsi que pour afficher les schémas. De telle manière, on a trois comportements différents ou trois objets très différents à trancher. »
>
> **T15** — « Pour la question du SVG, je valide ton idée de pouvoir copier-coller la commande où il y a la figure directement dans la commande et au lieu de l'image, une commande spéciale comme le static model avec les différentes options disponibles pour le modèle. »
>
> **T16** — « je trouve... que la vérification dépliée est une bonne chose dans la forme littérale contrôlée. Comme ça, on peut effectivement voir la valeur que prend la variable. »
>
> **T17** — « s'il y a un changement manuel dans VS Code, eh bien, dans WoodCore, cela doit apparaître et il doit être possible par variable. Donc lorsqu'on l'aurait dans les domaines, dans l'onglet formule, il doit être possible par variable d'importer les changements de WoodCore ou de cliquer sur importer tout et d'importer tous les changements dans WoodCore. »
>
> **T18** — « Car il peut être pertinent pour l'utilisateur de modifier directement les valeurs dans VS Code et ça doit continuer à fonctionner avec WoodCore et WoodCore doit reprendre les valeurs manuellement entrées dans VS Code. »
>
> **T19** — « Pour ta question 1, je valide le point A. Et B lorsque ce n'est pas possible, mais ça devrait être très rarement le cas. » [A : une valeur modifiée dans VS Code et importée remonte dans la source JSON ; B : là où elle ne peut pas remonter (valeur d'une position ou de la norme), elle reste une valeur de l'ingénieur dans le `.typ`, en orange, avec « Reprendre ».]
>
> **T20** — « Pour le point 2, je valide par principe. Mais explique-moi ce que signifie concrètement "seul la donnée a changé". » [Export : donnée seule changée → actualisation automatique ; fichier seul changé → « Importer » / « Tout importer » ; les deux → conflit par variable.]
>
> **T21** — « 3 oui. » [Une formule (`#eq`) modifiée dans VS Code suit la même mécanique, par ligne.]
>
> **T22** — « 4 oui à tout. » [Les projets existants qui appellent `#show-check-member` sont dépliés automatiquement ; `show-static-model`, `show-schema` et `show-plan` sont retirés avec migration automatique.]
>
> **T23** — « 5 ce que tu recommandes » [Une spécification dans `docs/requirements/active/` et une issue GitHub qui la résume et la référence.]

## 3. Exigences fonctionnelles

### REQ-001 — `domain:` avec une valeur : le littéral contrôlé
- **Exigence** : `#var(key, value, unit, domain: …)` doit être accepté (aujourd'hui refusé, `lib/formula.typ` « nothing to write beside it ») : la valeur écrite est celle qui est imprimée et calculée, et Typst la compare à la valeur que `domain:` lit (export ou `var-domain`). Égale (à la précision de l'arrondi d'écriture) : rien de plus. Différente : la valeur est imprimée **en rouge** avec « périmé : <valeur de l'export> » (mots du glossaire, trois langues), et la ligne est signalée par la métadonnée de REQ-004. `domain:` sans valeur garde son comportement actuel. Pas de nouvel argument `from:`.
- **Source** : T10, T16
- **Priorité** : doit
- **Critère d'acceptation** : un test compile `#var("N_t_d", 25, "kN", domain: ("check", "ZT-01"))` avec un export à 25 kN (pas de rouge, métadonnée `stale: false`) puis à 28 kN (rouge, texte « périmé », métadonnée `stale: true`, valeur de l'export 28 kN) ; `#var("N_t_d", domain: ("check", "ZT-01"))` imprime 28 kN comme aujourd'hui.

### REQ-002 — Une vérification à la traction est un domaine « Formules » déplié
- **Exigence** : enregistrer une vérification de type `tension` dans l'onglet « Traction » (et l'export) doit écrire `Formules/<id>.typ`, un `#var-domain("<id>", title: …)` contenant, dans l'ordre où `#verify-tension` les imprime aujourd'hui : chaque entrée en littéral contrôlé (REQ-001) — l'effort, la section, l'aire, les facteurs η_w, η_t, γ_M, les résistances caractéristiques —, chaque grandeur dérivée en `#eq` avec sa formule et sa clause SIA 265 (4.2.1.1 (6), 4.2.1.2 (7), 4.2.1.3 (8)/(9)), et la relation en `#verify(…, id: …)`. Le résultat imprimé (valeurs, η, ✔/✘) est celui de `#show-check-member` aujourd'hui pour les mêmes données. En tête, la ligne de l'élément que `#member` imprimait (position, section, classe de résistance, classe d'humidité) en texte et en `#var` contrôlées ; le titre est celui du domaine ; η est imprimé en % ; `shown:` et le niveau −1 sont remplacés par le `level:` de chaque ligne (Q-005, D-15). Le domaine porte le nom de la vérification, `Formules/ZT-01.typ`, `#var-domain("ZT-01")` (Q-004, D-14). Le fichier est un domaine comme un autre de l'onglet « Formules » : édité là, ou dans VS Code.
- **Source** : T2, T4, T14, T16
- **Priorité** : doit
- **Critère d'acceptation** : pour ZT-01 et pour une traction à α = 90° et à α = 30° de `tests/projet-exemple/`, le fichier généré compile, et un test lit le registre (niveau 0) : chaque clé et η égaux à `member_check.compute()` à 1e-6 ; chaque `#eq` porte `norm: "SIA 265"` et sa clause ; le domaine apparaît dans la liste de l'onglet « Formules ».

### REQ-003 — `gen:` : le calcul déplié sait de quelle forme il vient
- **Exigence** : le domaine déplié doit porter la forme dont il a été tiré (type, équation, version du générateur), et Typst doit comparer cette forme à celle que l'export donne aujourd'hui pour la vérification : si elles diffèrent (α passé de 0 à 30°, donc (6) → (8)/(9)), le domaine imprime en tête, en rouge, « le calcul ne correspond plus aux données — régénérer dans Woodcore » (trois langues), et la métadonnée le dit.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : un test change α de ZT-01 dans l'export sans régénérer : le PDF porte l'avertissement ; après régénération, il ne le porte plus.

### REQ-004 — Les commandes publient leur état (balise D)
- **Exigence** : `#var`, `#eq`, `#verify` et les commandes de dessin (REQ-012) doivent émettre une `metadata` étiquetée (domaine, clé ou `id`, valeur, unité, `domain:` lu, `stale`, forme `gen:` attendue et lue) ; Woodcore lit l'état d'un domaine par `typst query` et non en analysant le Typst. Le parseur (`formula_domain`, lexer de `typst_paths`) ne sert plus qu'à **localiser** l'appel à modifier.
- **Source** : T9 (D)
- **Priorité** : doit
- **Critère d'acceptation** : un test compile un domaine et lit par `typst query` la liste exacte de ses clés, valeurs et états ; une ligne ajoutée à la main dans VS Code apparaît dans cette liste sans modification du parseur.

### REQ-005 — Balises en arguments (balise B), et `id:` sur `#verify`
- **Exigence** : l'identité d'une `#var` ou d'une `#eq` est le couple (domaine, clé), déjà unique ; `#verify` prend un argument `id:` (facultatif pour un domaine écrit à la main, toujours écrit par le générateur) ; deux `#verify` d'un même domaine avec le même `id` sont refusés par un `panic` qui les nomme. Aucune balise en commentaire n'est écrite dans un domaine « Formules ».
- **Source** : T5, T6, T9 (B)
- **Priorité** : doit
- **Critère d'acceptation** : test de compilation : `id:` en double → `panic` nommant le domaine et l'id ; le fichier généré pour ZT-01 ne contient aucune ligne `// woodcore:` ; la ligne `// woodcore:object formula-domain domain` des domaines existants est retirée par la migration (REQ-015) et leur lecture n'en dépend plus.

### REQ-006 — Une ligne supprimée se voit et se réinsère
- **Exigence** : pour un domaine déplié, Woodcore doit comparer les clés que la forme `gen:` attend aux clés présentes (REQ-004) et signaler chaque clé manquante dans l'onglet « Formules » (« ligne supprimée : f_t_0_d ») avec « Réinsérer », qui la remet à sa place dans l'ordre du générateur. Masquer une ligne reste `level: 0` et n'est pas une suppression.
- **Source** : T6, T3
- **Priorité** : doit
- **Critère d'acceptation** : test : supprimer la ligne `f_t_0_d` du fichier → l'état du domaine la liste manquante ; « Réinsérer » la rétablit avant `sigma_t_0_d` ; une ligne mise à `level: 0` n'est pas listée.

### REQ-007 — Base de comparaison et états par variable (balise E)
- **Exigence** : Woodcore doit garder, pour chaque domaine déplié et pour chaque ligne (clé ou `id`), l'empreinte de ce qu'il a écrit en dernier (fichier annexe à contrat versionné, comme `sync.json`), et en déduire l'état de chaque ligne : `in_sync`, `data` (seule la donnée de l'export a changé), `local` (seul le fichier a changé — modifié dans VS Code ou dans l'onglet), `conflict` (les deux). Les états réutilisent la mécanique de `calc/sync.py` plutôt qu'une seconde implémentation.
- **Source** : T9 (E), T17, T20
- **Priorité** : doit
- **Critère d'acceptation** : tests des quatre états sur ZT-01 (N changé dans l'export seul ; N changé dans le fichier seul ; les deux ; rien) ; le fichier annexe a un schéma avec `schema_version` et un défaut de ce fichier arrête l'export en nommant le fichier et le champ.

### REQ-008 — À l'export : la donnée seule changée est actualisée sans question
- **Exigence** : à chaque export (et à chaque enregistrement de la vérification dans l'onglet « Traction »), une ligne à l'état `data` doit être actualisée automatiquement : Woodcore réécrit **seulement l'argument valeur** de cet appel, à sa place, sans toucher au reste du fichier ; les lignes `local` et `conflict` ne sont jamais réécrites sans l'ingénieur.
- **Source** : T20
- **Priorité** : doit
- **Critère d'acceptation** : test : N de ZT-01 passe de 25 à 28 kN dans `checks/ZT-01.json`, un commentaire et une mise en forme à la main existent ailleurs dans le fichier ; après export, seul `25` → `28` a changé (diff d'une ligne, fins de ligne conservées) et le PDF ne porte pas de rouge.

### REQ-009 — Reprendre dans Woodcore une valeur modifiée dans VS Code
- **Exigence** : une ligne à l'état `local` ou `conflict` doit apparaître dans l'onglet « Formules » (UI-002), avec « Importer » par variable et « Tout importer » pour le domaine. Importer une **valeur** : (a) si elle vient de la source de la vérification (`checks/<id>.json` : N, α, section, classe de résistance, classe d'humidité, impact indiqués), Woodcore l'écrit dans cette source — l'onglet « Traction » l'affiche ensuite —, et la ligne revient `in_sync` ; (b) sinon (valeur d'une position de `Positionen.xlsx`, d'une table de norme), elle devient une **valeur de l'ingénieur** : gardée dans le `.typ` avec `domain:` et `own: true` (Q-003, D-13) — la provenance reste écrite —, imprimée en orange, jamais « périmée » (la convention du tableau des charges utiles), non actualisée à l'export, avec « Reprendre » qui rétablit la valeur de l'export. Importer une **formule** (`#eq`) ou une ligne ajoutée : elle est acceptée comme la version de l'ingénieur et devient la base (REQ-007). Un conflit demande, par ligne, quelle version garder.
- **Source** : T17, T18, T19, T21
- **Priorité** : doit
- **Critère d'acceptation** : tests : N modifié à 30 dans le fichier → `local` → « Importer » → `checks/ZT-01.json` porte 30 kN, la ligne est `in_sync`, l'export suivant ne change rien ; f_t_0_k (norme) modifié → « Importer » → valeur de l'ingénieur, orange au PDF, inchangée par l'export, « Reprendre » rétablit la valeur de la norme ; `#eq` modifiée → « Importer » → nouvelle base, plus signalée.

### REQ-010 — Régénérer : fusion à trois voies par ligne
- **Exigence** : quand la forme change (REQ-003) ou que le générateur évolue, « Régénérer » doit calculer la nouvelle version et la fusionner ligne par ligne avec le fichier (base de REQ-007) : une ligne que l'ingénieur n'a pas touchée prend la nouvelle version ; une ligne qu'il a modifiée ou ajoutée est gardée ; une ligne modifiée des deux côtés est un conflit demandé par ligne. Le texte libre de l'ingénieur entre les commandes est conservé.
- **Source** : T3, T21
- **Priorité** : doit
- **Critère d'acceptation** : test : ZT-01 déplié à α = 0, une phrase et une ligne `#eq` ajoutées à la main, `η_t` modifié ; α passe à 30° ; « Régénérer » → les lignes (8)/(9) apparaissent, la phrase et l'`#eq` ajoutées restent, `η_t` modifié est proposé en conflit.

### REQ-011 — `#show-check-member` disparaît pour la traction ; migration des projets
- **Exigence** : un appel `#show-check-member("<id>")` d'une vérification de type `tension` dans un `.typ` d'un projet doit être remplacé, à l'ouverture du projet (migration, une fois, avec copie de sauvegarde), par `#include "/Formules/<id>.typ"` après génération du domaine ; `show-check-member` imprime alors, pour une traction dépliée, son domaine et refuse ses options (D-18, qui remplace le refus d'abord écrit ici), et reste pour les types non encore dépliés jusqu'à la spécification qui déplie le dernier (Q-001, D-11).
- **Source** : T13, T22
- **Priorité** : doit
- **Critère d'acceptation** : test sur une copie de `tests/projet-exemple/` contenant un appel pour ZT-01 : après migration, l'appel est un `#include`, le domaine existe, la page compilée donne les mêmes valeurs et le même verdict ; l'ancien fichier est sauvegardé ; une seconde ouverture ne change rien.

### REQ-012 — `schema(...)` rend le dessin, la figure est native
- **Exigence** : une commande `schema(id, width:, highlight:, aids:)` doit rendre **seulement le dessin** d'un schéma de détail (langue du rapport, mise en évidence, aides, taille et plafond de hauteur comme aujourd'hui — le corps de `show-schema(caption: none)` extrait), sans `figure` ; l'ingénieur écrit `#figure(schema("D-01"), kind: image, caption: […]) <fig-d-01>` (Q-006, D-16) et la cite par `@fig-d-01`, la figure comptée avec les autres images (« Abbildung N »). `show-schema` est retiré, et les appels existants migrés en `#figure(schema(…), caption: <légende qu'il imprimait>) <fig-…>` (REQ-015).
- **Source** : T8, T14, T15, T22
- **Priorité** : doit
- **Critère d'acceptation** : test : `#figure(schema("…"), caption: [x]) <fig-x>` compile, une référence `@fig-x` imprime le numéro de figure ; deux `schema(...)` dans un `#grid` d'une même figure compilent ; `show-schema` n'existe plus dans `lib/` ; la migration d'un appel `show-schema("…", width: 50%)` donne la même image à la même largeur.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — « Copier » d'un schéma donne la figure native
- **Exigence** : l'action de copie de l'onglet « Schémas » (et de « Connecteurs » où elle copie un schéma) doit copier `#figure(schema("<id>", …options choisies…), kind: image, caption: [<titre du schéma>]) <fig-<id>>`, le label dérivé de l'id et assaini (caractères hors `[A-Za-z0-9_-]` remplacés par `-`).
- **Source** : T15
- **Langues** : la légende proposée dans la langue du rapport ; aucune nouvelle chaîne de fenêtre hors celles du bouton s'il change
- **Critère d'acceptation** : test hors écran : le presse-papiers contient exactement ce texte pour un schéma de `tests/projet-exemple/`.

### UI-002 — L'onglet « Formules » montre l'état de chaque ligne
- **Exigence** : chaque pastille d'un domaine porte son état (REQ-007) : rien pour `in_sync`, une marque « modifié hors Woodcore » pour `local`, rouge pour `conflict`, orange pour une valeur de l'ingénieur, « périmé » pour une ligne dont le fichier ne suit plus l'export ; une ligne manquante (REQ-006) est une pastille fantôme avec « Réinsérer ». La carte du domaine (volet de droite) porte « Tout importer », « Régénérer » et, pour un domaine déplié, le nom de la vérification dont il vient. Chaque pastille signalée offre « Importer », « Reprendre » ou le choix du conflit, selon son état.
- **Source** : T17, T19, T20
- **Langues** : fr / de / en, sous les clés `fm_` de l'onglet
- **Critère d'acceptation** : test hors écran sur les quatre états de REQ-007 : la marque et les actions attendues sont présentes ; « Tout importer » passe toutes les lignes `local` à `in_sync`.

### UI-003 — L'onglet « Traction » mène au domaine déplié
- **Exigence** : l'onglet « Traction » reste le formulaire des entrées (`checks/<id>.json`) ; son aperçu compile le domaine déplié, et il offre « Ouvrir dans Formules ». Une entrée importée depuis le fichier (REQ-009 a) y apparaît.
- **Source** : T14, T18
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : après REQ-009 (N à 30 importé), l'onglet « Traction » affiche 30 kN ; « Ouvrir dans Formules » sélectionne le domaine ZT-01.

### UI-004 — Les marques du rapport
- **Exigence** : « périmé », la valeur de l'ingénieur et « le calcul ne correspond plus aux données » sont imprimés dans la langue du rapport, avec les couleurs de `calc/tools/theme.json` / du moteur déjà en usage (rouge des refus, orange des valeurs écrites par-dessus).
- **Source** : T3, T19
- **Langues** : de / fr / en dans `calc/i18n/strings.json`
- **Critère d'acceptation** : test : les trois marques compilent dans les trois langues, sans clé manquante.

## 5. Exigences d'architecture

### ARCH-001 — Le JSON reste la source des entrées, le `.typ` celle de la présentation
- **Exigence** : `checks/<id>.json` (schéma inchangé ou étendu de façon additive) reste la seule source des entrées d'une vérification ; le `.typ` déplié est écrit **depuis** l'export par Python, jamais relu pour reconstruire le formulaire autrement que par REQ-009. Woodcore ne génère aucun Typst sans passer par un enregistrement validé.
- **Source** : T4, T7
- **Critère d'acceptation** : revue du code : le générateur prend un enregistrement `member_check.resolve` et rend un texte ; aucun chemin n'écrit `Formules/<id>.typ` pour une vérification sans `check_source` passé.

### ARCH-002 — Un seul calcul en Python, le Typst calcule par `#eq`
- **Exigence** : le générateur est écrit à partir des lignes de `member_check.compute()` (clé, symbole, unité, formule, clause), étendues au besoin pour que **chaque** grandeur dérivée porte sa formule et sa clause ; il n'existe pas de troisième copie de l'arithmétique de 4.2.1. Le test qui tient Python et Typst égaux compare `compute()` au registre du domaine déplié. Le code de `verify-tension` dans `lib/timber.typ` que plus rien n'appelle est retiré (T13).
- **Source** : T13 ; principe 1 (`docs/architecture/principles.md`)
- **Critère d'acceptation** : `tests/test_member_check.py` compile les tractions par le domaine déplié ; `grep verify-tension lib/` ne trouve plus que ce qui sert encore (autres types) ou rien.

### ARCH-003 — Écriture ciblée, pas de réécriture canonique, pour les domaines
- **Exigence** : une modification faite par Woodcore dans un domaine (valeur actualisée, import, réinsertion) remplace l'étendue exacte de l'argument ou de l'appel concerné, localisé par sa clé ou son `id` ; tout octet hors de cette étendue est conservé (fins de ligne comprises). Une mise en forme à la main n'est plus un état `hand_edited` à réécrire.
- **Source** : T1, T9
- **Critère d'acceptation** : test : un domaine aux arguments sur plusieurs lignes, commentés, dans un ordre libre ; une actualisation change une seule étendue ; le reste est identique octet pour octet.

### ARCH-004 — La règle 15 réécrite, et les décisions consignées
- **Exigence** : la règle 15 de `docs/architecture/principles.md` dit désormais : la fenêtre ne montre pas de code Typst (pastilles, formulaires) ; **un calcul est écrit en entier dans son `.typ`**, lisible et modifiable dans VS Code, et Woodcore suit ce qui y est écrit. `docs/decisions.md` (§13) reçoit les décisions D-01 à D-09 (§7) avec leur raison et leur prix, en particulier ce qu'elles renversent (§3.3unvicies « calculé dans le rapport par `#show-check-member` », l'objet `formula-domain` balisé en commentaire, `show-schema`).
- **Source** : T12
- **Critère d'acceptation** : `tests/test_docs_coherence.py` passe ; la règle 15 et les entrées de `decisions.md` existent et se citent.

### ARCH-005 — Le domaine reste sans Qt ; l'onglet affiche et appelle
- **Exigence** : générateur, états, fusion, import et migration vivent dans `calc/` (p. ex. `calc/domains/unfold.py` ou extension de `formula_domain.py`/`member_check.py`, à fixer par la revue), sans Qt ; les onglets « Formules », « Traction » et « Schémas » affichent et appellent. Chaque action a aussi sa commande `woodcore-cli` si l'onglet équivalent en a (comme `woodcore-cli sync`).
- **Source** : principe (CLAUDE.md, « Domain logic is independent of the UI »)
- **Critère d'acceptation** : `python -c "import calc.domains.<module>"` sans PySide6 ; les tests du domaine ne construisent pas de fenêtre.

### ARCH-006 — Écriture ciblée partout dans « Formules », lecture sans balise (revue)
- **Exigence** : toute écriture de Woodcore dans un domaine « Formules » (onglet, export, import, migration) passe par `replace_span` sur l'étendue de l'appel ou de l'argument, localisée par le lexer ; `write_text` ne réécrit plus le corps entier ; l'état `hand_edited` disparaît ; le lecteur localise `#var-domain(` sans balise et accepte encore la balise pendant la transition ; `Command` porte `own`, `id`, `gen` et une valeur avec `domain:`.
- **Source** : revue (ARCH-RISK-202, 203), T1
- **Critère d'acceptation** : `tests/test_formula_domain.py` : un domaine sans balise se lit ; un domaine aux arguments multi-lignes et commentés, modifié dans l'onglet (texte, option, affichage), ne change que l'étendue touchée ; plus aucun état `hand_edited`.

### ARCH-007 — `("check", id)` lisible, résumé et citations suivent (revue)
- **Exigence** : le chargeur de `data/checks.json` passe dans `lib/calc-engine.typ` ; `find-calculation` et `resolve-source` ont une branche `check` (une vérification non calculable panique avec sa raison) ; `checks.json` publie, de façon additive (version mineure), les `vars` (les entrées et valeurs caractéristiques de `compute()`) et la forme `gen` ; `lib/summary.typ` trouve un domaine déplié par sa forme `gen:` ; la migration réécrit `#val(…, domain: "<id>-verify-tension")` en `"<id>"` et la boucle `check-member-ids()` de façon à ne plus appeler `show-check-member` pour une traction.
- **Source** : revue (ARCH-RISK-101, 204)
- **Critère d'acceptation** : test : `#var("N_t_d", domain: ("check", "ZT-01"))` compile ; la Nachweisübersicht de `tests/projet-exemple/` liste ZT-01 déplié avec le même η ; la boucle migrée compile sans `panic`.

### ARCH-008 — `compute()` donne au générateur tout ce qu'il écrit (revue)
- **Exigence** : `_row` porte `clause` et `formula_keys` (la formule en clés, écrite une fois dans `_compute`) ; chaque valeur caractéristique de la norme (f_t,0,k …) est une ligne d'entrée lue par `calc/norms/sia265` ; aucune valeur de norme n'est écrite dans une formule ; le générateur est pur (aucune date, LF) et l'export n'écrit un domaine que si son texte change ; un défaut du fichier annexe `Formules/unfold.json` (`schemas/unfold.schema.json`) arrête l'export, et l'absence de base fait d'une différence un conflit ; import, régénération et migration écrivent leurs fichiers en une fois (`sharing._commit`) ; l'onglet « Traction » écrit sa source par `member_check.write_source` ; les actions nouvelles sont dans `WRITERS` ; la migration n'est jamais exécutée pendant l'export.
- **Source** : revue (ARCH-RISK-205 à 211, 107)
- **Critère d'acceptation** : tests : `compute()` d'une traction → chaque ligne dérivée a `clause` et `formula_keys` sans littéral de norme ; deux exports de suite identiques à l'octet ; échec simulé au milieu d'un import → aucun fichier changé ; `tests/test_home.py` couvre les nouveaux writers.

## 6. Contraintes

- **CON-001** — Chaque `#eq` du domaine déplié cite SIA 265 et sa clause, lue sur l'édition de `ExternalFiles/000-Normes/` déjà référencée par `calc/norms/` ; aucune valeur de norme n'est écrite de mémoire (le littéral contrôlé lit `calc/norms` via l'export). Source : principes 7 et 13 (inférée).
- **CON-002** — Trois langues : toute chaîne nouvelle de la fenêtre (`fm_`, onglet « Traction », « Schémas ») et du rapport (`strings.json`) existe en de/fr/en ; le domaine généré est écrit dans la langue du rapport pour son titre, les clés restant les mêmes dans les trois. Source : CLAUDE.md (inférée).
- **CON-003** — Contrats versionnés : le fichier annexe de REQ-007 a un schéma avec `schema_version` ; `data/formulas.json` change de version mineure s'il gagne des champs (domaine déplié, vérification d'origine) ; `checks.json` aussi si l'export doit publier les valeurs pour `domain: ("check", id)`. Source : principe 8 (inférée).
- **CON-004** — Un projet existant s'ouvre sans perte : migration une fois, avec sauvegarde de chaque fichier modifié (comme `Sections/archives/`), idempotente. Source : T22 (inférée).
- **CON-005** — Plusieurs sessions et VS Code écrivent les mêmes fichiers : aucune écriture sans `check_unchanged` (le fichier relu n'a pas changé depuis), tout ou rien, sauvegarde et remise en place en cas d'échec. Source : `docs/typst/formulas.md` (inférée).
- **CON-006** — Documentation finie avec le changement : `docs/typst/formulas.md`, `docs/ui/tab-formulas.md`, `docs/domain/member-checks.md`, `docs/ui/tab-member-checks.md`, `docs/domain/detail-schemas.md`, `docs/ui/tab-schemas.md`, `docs/typst/api-conventions.md` (table des commandes), `///` + deux exemples + `calc/i18n/commands.json` pour `schema` et les arguments nouveaux de `var`/`verify`, `CHANGELOG.md`, page « Nouveautés » en trois langues, catalogue des tests. Source : CLAUDE.md (inférée).

## 7. Décisions prises

- **D-01** (T7, T4) — Woodcore n'écrit pas de Typst sans JSON : les entrées d'une vérification restent dans `checks/<id>.json`, validées ; Python en écrit le Typst lisible. Raison : le Typst seul n'a ni schéma ni validation, et relire le Typst pour rouvrir un formulaire recrée le problème de T1.
- **D-02** (T2, T13, T16) — Une vérification est imprimée **dépliée** en `#var`/`#eq`/`#verify` dans un domaine « Formules » ; il n'y a pas de forme compacte en parallèle. Prix : un calcul déplié ne suit plus de lui-même une correction du gabarit dans `lib/` ; il reçoit « Régénérer » (REQ-010).
- **D-03** (T10, T16) — Une entrée est un **littéral contrôlé** par `domain:` (argument existant, étendu), pas par un nouvel argument `from:`. Raison : un seul argument, une seule règle (« sans valeur : lu ; avec valeur : contrôlé ») ; la valeur se voit dans VS Code.
- **D-04** (T9) — Balises : B (la clé ou `id:` dans l'appel), C (labels natifs pour titres et figures), D (`typst query` pour lire l'état), E (fichier annexe comme base de fusion seulement). Les balises en commentaires ne sont plus écrites dans les domaines « Formules ».
- **D-05** (T11) — Documents CU/BP : le `.typ` reste la source (pas de tableaux sortis en JSON). Leur passage des balises en commentaires aux balises B/C : hors de ce premier pas (§8).
- **D-06** (T12) — La règle 15 est réécrite : vraie pour la fenêtre, pas pour les calculs, dont tout le Typst est dans les fichiers.
- **D-07** (T19, T20, T21) — Sens retour : une valeur modifiée dans VS Code et importée remonte dans la source JSON quand elle en vient (a), sinon devient une valeur de l'ingénieur orange avec « Reprendre » (b, rare) ; une donnée seule changée est actualisée sans question à l'export ; un fichier seul changé est importé par variable ou en bloc ; un conflit est tranché par ligne ; une formule suit la même mécanique.
- **D-08** (T8, T15, T22) — Une commande de dessin rend le dessin et pas la figure ; l'ingénieur écrit `#figure(…, caption:) <label>`. `show-schema`, `show-static-model` et `show-plan` sont retirés avec migration automatique (calendrier : Q-002).
- **D-09** (T22) — Les projets existants sont migrés automatiquement à l'ouverture (`#show-check-member` → domaine déplié et `#include`, `show-schema` → figure native), avec sauvegarde.
- **D-10** (T23) — Livrables de l'étape : cette spécification et une issue GitHub qui la résume et y renvoie.
- **D-11** (Q-001, 15.10.2026) — `#show-check-member` reste pour les types non encore dépliés et refuse la traction ; il disparaît avec la spécification qui déplie le dernier type.
- **D-12** (Q-002, 15.10.2026) — Ce pas fait `schema()` seul ; `static-model` puis `plan` passent en figure native dans une spécification chacun, sur le modèle établi ici.
- **D-13** (Q-003, 15.10.2026) — Une valeur de l'ingénieur s'écrit `#var(key, valeur, unité, domain: (…), own: true)` : provenance écrite, orange au PDF, jamais actualisée ni « périmée » ; « Reprendre » retire `own: true` et rétablit la valeur lue par `domain:`.
- **D-14** (Q-004, 15.10.2026) — Le domaine déplié porte le nom de sa vérification, tel quel (`Formules/ZT-01.typ`, `#var-domain("ZT-01")`) : la règle des noms de « Formules » accepte celle des vérifications ; les citations `"<id>-verify-tension"` sont migrées ; le résumé trouve les vérifications par `gen:`.
- **D-15** (Q-005, 15.10.2026) — Le domaine déplié garde tout ce que `#show-check-member` imprimait, en lignes : la ligne de l'élément, le titre, η en % ; `shown:` et le niveau −1 sont remplacés par le `level:` de chaque ligne (renversement de l'issue #39 pour les domaines dépliés). La traction au feu reste à `#show-check-member`.
- **D-16** (Q-006, 15.10.2026) — La commande s'appelle `schema()` et garde le plafond de hauteur ; la figure s'écrit avec `kind: image`, que la copie écrit.
- **D-17** (revue, 15.10.2026) — L'onglet « Formules » n'écrit plus sa forme canonique : toute écriture est ciblée et `hand_edited` disparaît (renversement à consigner dans `docs/decisions.md`).
- **D-18** (étape 8, 15.10.2026, l'ingénieur) — `#show-check-member` d'une traction dépliée **imprime son domaine** (`include "/Formules/<id>.typ"` fait par la commande) au lieu de la refuser, ce que REQ-011 disait : une boucle `#for id in check-member-ids() { show-check-member(id) }` et les rapports existants continuent de marcher, un seul calcul existant (le déplié) ; une option de `#show-check-member` donnée pour une traction dépliée est refusée, les niveaux se réglant ligne par ligne dans le fichier. Raison : refuser aurait arrêté chaque boucle et demandé une nouvelle forme de boucle.

## 8. Hors périmètre

- Les autres types de vérification (compression, flexion, cisaillement, flambage, déversement, feu, acier) : dépliés dans des spécifications suivantes, sur le même mécanisme.
- Les documents CU/BP : passage de leurs balises en commentaires (`// woodcore:object`, `// woodcore:shared`) aux balises B/C et à l'écriture ciblée — une spécification suivante (D-05).
- `show-static-model` et `show-plan` (et `doc-plan`, `doc-image`) : leur retrait est décidé (D-08) et fait dans les spécifications suivantes (D-12).
- Les calculs des charges (`show-calc`, neige, vent, poids propre) : non dépliés dans ce pas.
- La traction en situation d'incendie (`fire`) : reste à `#show-check-member` (D-15).

## 9. Idées non retenues comme exigences

- T6 « s'il a supprimé une ligne du calcul de neige » : exemple donné pour illustrer la réinsertion ; la neige n'est pas dépliée dans ce pas (§8), la réinsertion l'est (REQ-006).
- La variante « tableaux des documents CU/BP en JSON » (voie b de l'assistant) : écartée par T11.
- Un utilitaire de légende par défaut `schema-caption(id)` : non demandé ; la copie (UI-001) propose déjà le titre du schéma.

## 10. Questions

### Q-001 — `#show-check-member` pendant la transition
- **Pourquoi elle compte** : T13 retire la commande, mais seul le type traction est déplié dans ce pas (T14) ; les autres types n'ont encore que cette commande.
- **Options** : A (recommandée) — la commande reste pour les types non encore dépliés et refuse la traction ; elle disparaît avec la spécification qui déplie le dernier type. B — tous les types sont dépliés dans ce pas (périmètre plusieurs fois plus grand). C — la commande est retirée maintenant et les vérifications non dépliées ne s'impriment plus.
- **Réponse** : A, l'ingénieur, 15.10.2026 (D-11).

### Q-002 — Calendrier du retrait de `show-static-model` et `show-plan`
- **Pourquoi elle compte** : T22 les retire, T14 limite le pas aux schémas ; `show-plan` est appelé par les plans, les feuilles d'export, `doc-plan` des documents et une vingtaine de fichiers de tests.
- **Options** : A (recommandée) — ce pas fait `schema` seul ; `static-model` et `plan` suivent, une spécification chacun, sur le modèle établi ici. B — les trois dans ce pas.
- **Réponse** : A, l'ingénieur, 15.10.2026 (D-12).

### Q-003 — Forme d'une valeur de l'ingénieur dans le fichier (REQ-009 b)
- **Pourquoi elle compte** : la valeur doit garder sa provenance (principe 5) pour que « Reprendre » sache où relire, et ne doit pas être imprimée « périmée ».
- **Options** : A (recommandée) — `domain:` reste, avec un argument `own: true` : imprimée en orange, jamais actualisée, jamais « périmée ». B — `domain:` est retiré : la valeur devient un littéral libre ; « Reprendre » s'appuie sur le fichier annexe pour retrouver la source.
- **Réponse** : A, l'ingénieur, 15.10.2026 (D-13).

### Q-004 — Nom du domaine déplié (revue, ARCH-RISK-201)
- **Pourquoi elle compte** : les noms de vérification (`ZT-01`) ne sont pas des noms de « Formules » valides (minuscules) ; le résumé et les citations dépendent du nom.
- **Options** : A (recommandée) — le même nom, `ZT-01` ; B — transformé, `zt-01` ; C — préfixé, `check-zt-01`.
- **Réponse** : A, l'ingénieur, 15.10.2026 (D-14), après explication que JSON et domaine sont un seul objet et que seule l'orthographe du nom est en jeu.

### Q-005 — Ce que le domaine garde de `#show-check-member` (revue, ARCH-RISK-107)
- **Pourquoi elle compte** : la commande imprime aussi la ligne de l'élément, un titre, η en % et le niveau −1 avec `shown:`.
- **Options** : A (recommandée) — tout, en lignes ; B — le calcul seul.
- **Réponse** : A, l'ingénieur, 15.10.2026 (D-15).

### Q-006 — Nom et genre de la commande de dessin (revue, ARCH-RISK-106)
- **Pourquoi elle compte** : un corps `context`/`layout` n'est pas reconnu comme image par `figure` ; `schema` est un nom générique.
- **Options** : A (recommandée) — `detail-schema()` rendant une vraie image, sans plafond de hauteur ; B — `schema()`, plafond gardé, `kind: image` écrit dans la copie.
- **Réponse** : B, l'ingénieur, 15.10.2026 (D-16).

## 11. Critères d'acceptation

- [x] REQ-001 — `domain:` avec valeur : égal → rien, différent → rouge « périmé » et `stale: true`.
- [x] REQ-002 — ZT-01 et deux tractions à angle dépliées : registre égal à `compute()` à 1e-6, clauses citées.
- [x] REQ-003 — forme `gen:` différente de l'export → avertissement en tête de domaine.
- [x] REQ-004 — `typst query` donne clés, valeurs, états ; ligne ajoutée à la main listée.
- [x] REQ-005 — `id:` en double refusé ; aucune balise en commentaire dans un domaine.
- [x] REQ-006 — ligne supprimée listée et réinsérée ; `level: 0` non listé.
- [x] REQ-007 — quatre états testés ; fichier annexe à schéma versionné.
- [x] REQ-008 — donnée seule changée → une seule étendue réécrite à l'export.
- [x] REQ-009 — import vers la source (a), valeur de l'ingénieur orange et « Reprendre » (b), formule importée.
- [x] REQ-010 — régénération par fusion à trois voies, texte libre conservé, conflit proposé.
- [x] REQ-011 — migration de `#show-check-member` (traction) en `#include`, mêmes valeurs, idempotente.
- [x] REQ-012 — `#figure(schema(…)) <label>` compile et se cite ; `show-schema` retiré et migré.
- [x] UI-001 — copie de la figure native.
- [x] UI-002 — états et actions par pastille, « Tout importer ».
- [x] UI-003 — « Traction » montre l'entrée importée, « Ouvrir dans Formules ».
- [x] UI-004 — trois marques du rapport en trois langues.
- [x] ARCH-001 à ARCH-008 — vérifiés comme dit en §5.
- [x] Documentation : sections de `docs/` (CON-006), règle 15, `docs/decisions.md`, `CHANGELOG.md`, page « Nouveautés » fr/de/en, `///` + exemples + traductions pour `schema` et les arguments nouveaux.
- [x] Tests : `tests/test_formula_domain.py`, `tests/test_member_check.py`, `tests/test_member_check_tab.py`, `tests/test_schema.py`, `tests/test_commands.py` étendus, un fichier de test du dépliage et de ses états ajouté (et sa ligne au catalogue), suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | ARCH-003, D-04 | capturé |
| T2 | REQ-002, D-02 | capturé |
| T3 | REQ-003, REQ-006, REQ-010, UI-004 | capturé |
| T4 | REQ-002, ARCH-001, D-01 | capturé |
| T5 | REQ-005, D-03 | capturé |
| T6 | REQ-005, REQ-006 ; exemple de la neige → §9 | capturé |
| T7 | ARCH-001, D-01 | décision |
| T8 | REQ-012, D-08 | capturé |
| T9 | REQ-004, REQ-005, REQ-007, ARCH-003, D-04 | décision |
| T10 | REQ-001, D-03 | capturé |
| T11 | D-05, §8 | décision |
| T12 | ARCH-004, D-06 | capturé |
| T13 | REQ-011, ARCH-002, D-02, D-11 (Q-001) | capturé |
| T14 | REQ-002, REQ-012, UI-003, §8 | capturé |
| T15 | REQ-012, UI-001, D-08 | capturé |
| T16 | REQ-001, REQ-002, D-03 | capturé |
| T17 | REQ-007, REQ-009, UI-002 | capturé |
| T18 | REQ-009, UI-003 | capturé |
| T19 | REQ-009, D-07, D-13 (Q-003) | capturé |
| T20 | REQ-007, REQ-008, D-07 | capturé |
| T21 | REQ-009, REQ-010, D-07 | capturé |
| T22 | REQ-011, REQ-012, D-08, D-09, D-12 (Q-002) | capturé |
| T23 | D-10 | décision |

### Points de la source non résolus

Aucun (Q-001 à Q-006 répondues le 15.10.2026).

## 13. Revue d'architecture

Deux revues parallèles (`architecture-reviewer`, 15.10.2026) : côté Typst et figures — **APPROUVER AVEC RÉSERVES** ; côté Python, synchronisation, migration et fenêtre — **REVOIR** (trois points bloquants, 201 à 203). Verdict global : **REVOIR**, renvoyé à l'ingénieur pour Q-004 à Q-006 ; les autres risques se règlent dans la spécification et le plan.

### Modules touchés

- Typst : `lib/formula.typ` (`var` 1184, `var-argument-names` 1035, `eq` 1487, `var-domain` 1673, `verify-core` 2136, `verify` 2267) ; `lib/calc-engine.typ` (`find-calculation` 432, `resolve-source` 506, `show-schema` 1695, `override-colour` 3528) ; `lib/timber.typ` (`timber-checks` 1481, `check-member-ids` 1505, `show-check-member` 1548, `verify-tension`) ; `lib/summary.typ` 135-155 (Nachweisübersicht par la forme `-verify-`) ; `lib/shown-variables.json`.
- Python : `calc/domains/formula_domain.py` (`Command`/`Domain` 73-114, `from_call` 267, `to_call` 322, `_body_span` 371, `read` 552, `write_text` 596, `check_unchanged` 723, `save` 737, `prepare` 811) ; `calc/domains/member_check.py` (`resolve` 479, `draft_typst` 663, `_row` 741, `compute` 750, traction 870-926) ; `calc/shown_variables.py` 49 ; `calc/sync.py` (`digest` 126, règle `own`/`seen`) ; `calc/export_all.py` 162/219/232 ; `calc/tools/woodcore_gui.py` 302 (`WRITERS`) ; `calc/tools/formula_tab.py` 530/659 ; `calc/tools/member_check_tab_actions.py` 133/333 (écrit `checks/<id>.json` lui-même) ; appelants de `show-schema` (`build_reference_calls.py` 365-374, `build_reference.py`, `build_reference_lib.py` 88, `display_options.py` 110, `schema_tab.py` 678, `examples/show-schema-*.typ`, `calc/i18n/commands.json`, `website/`).

### Existant à réutiliser

`show-schema(..., caption: none)` est déjà le dessin seul : `schema` en est le corps extrait, pas un second dessinateur. Le patron `metadata(...) <woodcore-sheet-box>` de `lib/sheet.typ` 126 et sa requête dans `calc/tools/sheet_editor_render.py` 33 pour REQ-004. `variables.read` pour lancer Typst (`--root`, `--input`). `converted()`/`var-record()` et la tolérance relative 1e-9 d'`eq` pour comparer un littéral à l'export. `override-colour` et `test-nok` pour l'orange et le rouge. La règle à trois voies de `sync.py`, **extraite** en une fonction pure `three_way(base, mine, theirs)` utilisée par `sync` et par le dépliage (le reste de `sync` est lié aux blocs `shared`). `sync.digest`, le format de `sync.json`/`check_source` comme modèle du fichier annexe, `sharing._commit` pour l'écriture multi-fichiers atomique, `ArchiveBackend`, `free_id`, `cited_by`, le lexer de `typst_paths`.

### Risques

- **ARCH-RISK-201 (bloquant)** — Un id de vérification (`ZT-01`, majuscules, `.`, `+`) n'est pas un id de domaine « Formules » (minuscules, `check_id` 651). → Q-004.
- **ARCH-RISK-202 (bloquant)** — ARCH-003 contredit `formula_domain` : `save` réécrit tout le corps (`write_text`), `read` classe `hand_edited` tout corps non canonique, un commentaire dans un appel multi-ligne est perdu. Correction retenue : `replace_span(text, span, new)` fondé sur le lexer ; **toute** écriture de l'onglet dans un domaine passe par lui ; l'état `hand_edited` disparaît (renversement à consigner, ARCH-006).
- **ARCH-RISK-203 (bloquant)** — La lecture exige la balise `// woodcore:object formula-domain` (`_body_span`), sans quoi le fichier est `unreadable` et l'export s'arrête ; `from_call` refuse `domain:` avec une valeur. Correction retenue : lecteur qui localise `#var-domain(` par le lexer et tolère la balise pendant la transition ; `Command` gagne `own`, `id`, `gen` ; la migration retire la balise (ARCH-006).
- **ARCH-RISK-101 / 204 (important)** — `("check", id)` n'est pas lisible par `find-calculation` ; le résumé et les `#val(…, domain: "ZT-01-verify-tension")` cassent ; la boucle `#for id in check-member-ids() { show-check-member(id) }` paniquerait sur chaque traction. Correction : chargeur des vérifications déplacé dans `calc-engine.typ`, branche `check` dans `find-calculation` et `resolve-source`, `checks.json` publie `vars` et `gen` (additif, version mineure) ; le résumé trouve les domaines dépliés par `gen:` ; la migration réécrit les citations et la boucle (ARCH-007). Nom du domaine : Q-004.
- **ARCH-RISK-102 (important)** — `stale` : pour une paire de l'export, comparé hors contexte ; pour `domain: "<var-domain>"`, dans le `context` seulement (une `update` ne signale rien). Une seule fonction de comparaison pour les deux chemins et pour la métadonnée ; comparaison après `converted()` ; une constante de précision unique côté Typst, que Python respecte en écrivant (test).
- **ARCH-RISK-103 / 104 (important)** — Métadonnées émises depuis le `context` (seul lieu où `eq` et `verify` connaissent leur valeur), un seul label `<woodcore-var>`, hors des items de ligne (`sep`, `var-line`), aussi au niveau 0, sans texte traduit. `typst query` d'un `Formules/<id>.typ` seul : `--root` du projet et les mêmes `--input` que le rapport ; un domaine écrit à la main qui lit un `var-domain` du rapport ne compile pas seul → repli sur le rapport. Coût de compilation mesuré avant/après et consigné dans `docs/architecture/performance.md`.
- **ARCH-RISK-105 / 108 / 109 (important/mineur)** — `own`, `id`, `gen` ajoutés aux listes d'arguments (`var-argument-names`, `build_reference_calls.py` 196-207, `display_options.py` 159), `///`, exemples, `commands.json` ; `own` sans `domain:` ou sans valeur → `panic` ; `id:` en double vérifié dans le `context` de `verify-core` ; la forme `gen:` publiée une fois dans `checks.json`, un seul format ; clés nouvelles de `strings.json` en trois langues.
- **ARCH-RISK-106 (important)** — `#figure(schema(…))` : le corps est un `context`/`layout`, Typst ne peut pas y voir une `image` et prendrait un genre générique (autre compteur, autre supplément) ; label dérivé de l'id à assainir, deux copies du même schéma donnent deux fois le même label ; `schema` est un nom très générique, masqué par un `#let schema` de l'ingénieur. → Q-006.
- **ARCH-RISK-107 / 207 (important)** — `compute()` n'a pas de clause par ligne ; les valeurs de calcul portent la valeur de la table écrite **dans** la formule (`eta_w dot eta_t dot 18.5`) ; `f_t_0_k` n'est pas publiée ; les formules sont en symboles (`sigma_(t,0,d)`) et non en clés. Correction : `_row` gagne `clause` et `formula_keys` (écrites une fois dans `_compute`), une ligne d'entrée par valeur caractéristique lue par `calc/norms/sia265`, aucune valeur de norme dans une formule (ARCH-008). Ce que le domaine garde de `show-check-member` (ligne `#member`, titre, `unit: "%"`, `level: -1`/`shown:`, traction au feu) → Q-005.
- **ARCH-RISK-205 (important)** — Fichier annexe : `Formules/unfold.json` (format `woodcore-unfold`, `schemas/unfold.schema.json`, `schema_version`), écrit entier, LF, clés triées, sans date ; un défaut arrête l'export ; **sans base, une différence est un conflit** (règle de `sync`), jamais devinée.
- **ARCH-RISK-206 (important)** — Un import (a) écrit `checks/<id>.json`, le `.typ` et le fichier annexe : une seule écriture atomique (`sharing._commit`), relecture juste avant d'écrire ; l'onglet « Traction » cesse d'écrire le JSON lui-même → `member_check.write_source` (validée par `check_source`).
- **ARCH-RISK-208 (important)** — Migration dans `calc/`, appelée à l'ouverture et par `woodcore-cli`, **jamais pendant l'export** (reproductibilité) ; `woodcore-cli check` n'écrit rien ; une vérification non calculable garde son appel et avertit ; les arguments `level:`, `title:`, `unit:`, `shown:` de l'appel sont traduits ou listés comme perdus ; sauvegarde par `ArchiveBackend`.
- **ARCH-RISK-209 (important)** — « Importer », « Tout importer », « Réinsérer », « Régénérer », « Reprendre » sont des écritures : leurs noms dans `WRITERS` et dans `tests/test_home.py`.
- **ARCH-RISK-210 / 211 (mineur)** — Code mort à retirer avec la traction : branche `tension` de `draft_typst`, de `check_command`, de `shown_keys`/`shown_choices`, ses clés de `lib/shown-variables.json`, les clés `shown:` de l'onglet « Traction », `verify-tension` si plus rien ne l'appelle (`lib/formula.typ` 22 l'importe). Générateur pur (aucune date, LF) ; l'export n'écrit un domaine que si son texte change ; deux exports de suite identiques à l'octet.

### Approche recommandée

`calc/domains/unfold.py` (sans Qt) : `generate(record)`, `states(text, base, fresh)` sur `three_way`, `merge(base, mine, fresh)`, `import_line`, `reinsert`, `migrate` (plan puis écriture). `formula_domain.py` : lecteur sans balise, `Command.own/id/gen`, `replace_span`, plus de `hand_edited`. `member_check.py` : `_row` avec `clause`/`formula_keys`, lignes caractéristiques, `write_source`, `vars`/`gen` publiés. Typst : `own`/`domain:`+valeur, `id:`, `gen:`, métadonnée `<woodcore-var>`, branche `check`, `schema` extrait. `woodcore-cli unfold status|import|regenerate|migrate`. Onglets : affichent et appellent.

### Tests

Nouveau `tests/test_unfold.py` (+ catalogue) ; `tests/test_formula.py`, `test_formula_domain.py`, `test_member_check.py`, `test_member_check_tab.py`, `test_home.py`, `test_schema.py`, `test_display.py`, `test_commands.py`, `test_call_command.py`, `test_validation.py`, `test_docs_coherence.py` étendus.

## 14. Plan d'implémentation

Chaque étape finit par ses tests verts (`python tests/run_tests.py -k …` ou `--related`) et une ligne au §16.

1. **Moteur Typst : `var`, `verify`, `var-domain`** — `lib/formula.typ` : `domain:` avec valeur (littéral contrôlé, une fonction unique de comparaison après `converted()`, précision commune), `own: true` (orange `override-colour`, `panic` sans `domain:` ou sans valeur), `id:` sur `verify` (doublon refusé dans le `context` de `verify-core`), `gen:` sur `var-domain` ; clés de `calc/i18n/strings.json` (périmé, valeur de l'ingénieur, calcul ne correspondant plus) en trois langues ; `var-argument-names` et listes d'arguments Python. *Réalise* REQ-001, REQ-003 (partie Typst), REQ-005, UI-004. *Tests* : `tests/test_formula.py`, `tests/test_commands.py`.
2. **Métadonnées `<woodcore-var>` et lecture par `typst query`** — émission depuis le `context` de `var`, `eq`, `verify`, hors des items de ligne ; `calc/domains/unfold.py` : `query_state(here, path)` sur le modèle de `variables.read` (`--root`, mêmes `--input`), repli sur le rapport ; mesure du temps de compilation avant/après dans `docs/architecture/performance.md`. *Réalise* REQ-004. *Tests* : `tests/test_unfold.py` (nouveau, + catalogue).
3. **`checks.json` lisible par `domain:`** — chargeur dans `lib/calc-engine.typ`, branche `check` de `find-calculation` et `resolve-source` ; `member_check` publie `vars` et `gen` (additif, version mineure de `schemas/checks.schema.json`, `validation.validate_checks_business`) ; `_row` gagne `clause` et `formula_keys`, lignes caractéristiques lues par `calc/norms/sia265`. *Réalise* ARCH-007 (partie données), ARCH-008 (partie `compute`). *Tests* : `tests/test_member_check.py`, `tests/test_validation.py`.
4. **`formula_domain` : lecteur sans balise et écriture ciblée** — `_body_span` par le lexer (balise tolérée), `Command.own/id/gen` et valeur avec `domain:` dans `from_call`/`to_call`, `replace_span`, `save`/`write_text` ciblés, retrait de `hand_edited` et de son message ; `check_id` accepte un nom de vérification pour un domaine qui porte `gen:` (D-14). *Réalise* ARCH-003, ARCH-006. *Tests* : `tests/test_formula_domain.py`, `tests/test_formula_tab*.py`.
5. **Générateur de la traction** — `unfold.generate(record)` depuis `resolve` + `compute()` : ligne de l'élément, entrées en littéral contrôlé, `#eq` avec clause, `#verify(id:)`, η en %, `gen:` ; pur, LF ; `Formules/unfold.json` + `schemas/unfold.schema.json` (empreintes, `gen`) ; écrit à l'enregistrement de la vérification et à l'export seulement si le texte change ; `lib/summary.typ` trouve le domaine par `gen:`. *Réalise* REQ-002, REQ-003, ARCH-001, ARCH-002, ARCH-007 (résumé). *Tests* : `tests/test_unfold.py`, `tests/test_member_check.py` (registre égal à `compute()` à 1e-6, α = 0, 30, 90), Nachweisübersicht.
6. **États, actualisation, import, réinsertion, régénération** — `three_way` extrait de `calc/sync.py` et utilisé par `sync` et `unfold` ; `unfold.states`, actualisation ciblée à l'export (`data`), `import_line`/`import_all` ((a) par `member_check.write_source` validé, (b) `own: true`, formule), `reinsert`, `merge` ; écritures multi-fichiers par `sharing._commit` ; `woodcore-cli unfold status|import|regenerate`. *Réalise* REQ-006 à REQ-010, ARCH-008 (atomicité). *Tests* : `tests/test_unfold.py`, `tests/test_cli_sync.py` (non-régression de `sync`).
7. **Fenêtre** — onglet « Formules » : état par pastille, pastille fantôme, « Importer », « Tout importer », « Reprendre », « Régénérer », « Réinsérer », mots `fm_` en trois langues, noms dans `WRITERS` ; onglet « Traction » : écrit par `write_source`, aperçu = domaine déplié, « Ouvrir dans Formules », retrait des réglages `shown:` de la traction. *Réalise* UI-002, UI-003. *Tests* : `tests/test_formula_tab*.py`, `tests/test_member_check_tab.py`, `tests/test_home.py`.
8. **`show-check-member` refuse la traction ; code mort** — `panic` qui renvoie au domaine déplié ; retrait des branches `tension` de `draft_typst`, `check_command`, `shown_keys`/`shown_choices`, de `lib/shown-variables.json`, et de `verify-tension` si plus rien ne l'appelle (feu : D-15 le garde appelé). *Réalise* REQ-011 (partie commande), ARCH-002. *Tests* : `tests/test_timber.py`, `tests/test_member_check.py`, `tests/test_call_command.py`.
9. **`schema()` et figure native** — corps de `show-schema(caption: none)` extrait en `schema()`, `show-schema` retiré ; « Copier » de « Schémas » et « Connecteurs » écrit `#figure(schema(…), kind: image, caption: […]) <fig-…>` ; `///`, deux exemples, `commands.json`, `build_reference*`, `display_options`, `examples/`, `website/strings.json`. *Réalise* REQ-012, UI-001. *Tests* : `tests/test_schema.py`, `tests/test_display.py`, `tests/test_commands.py`, `tests/test_call_command.py`, `tests/test_site.py`.
10. **Migration** — `unfold.migrate(here)` (plan puis écriture, `ArchiveBackend`, idempotente), appelée à l'ouverture du projet et par `woodcore-cli unfold migrate`, jamais pendant l'export : balise retirée des domaines existants, `#show-check-member` d'une traction calculable → domaine + `#include`, citations `"<id>-verify-tension"` et boucle `check-member-ids()` réécrites, `show-schema(…)` → `#figure(schema(…), kind: image, caption: …) <fig-…>` ; `tests/projet-exemple/` migré. *Réalise* REQ-011, REQ-012 (migration), CON-004. *Tests* : `tests/test_unfold.py` (migration sur une copie, idempotence), compilation de `tests/projet-exemple/`.
11. **Documentation et décisions** — règle 15 réécrite ; `docs/decisions.md` (D-01 à D-17, renversements de §3.3unvicies, de `hand_edited`, de la balise `formula-domain`, de `show-schema`, de `shown:` pour les domaines dépliés) et `docs/decisions-index.md` ; `docs/typst/formulas.md`, `docs/ui/tab-formulas.md`, `docs/domain/member-checks.md`, `docs/ui/tab-member-checks.md`, `docs/domain/detail-schemas.md`, `docs/ui/tab-schemas.md`, `docs/typst/api-conventions.md`, `docs/conventions/build-and-release.md` (`woodcore-cli unfold`), catalogue des tests ; `CHANGELOG.md` ; page « Nouveautés » fr/de/en. *Réalise* ARCH-004, CON-006. *Tests* : `tests/test_docs_coherence.py`, `tests/test_commands.py`.
12. **Vérification et fin** — suite complète en arrière-plan, `verify-requirements`, puis `finish` (commit, une question pour pousser, issue GitHub).

## 15. Vérification

Vérification indépendante (`requirements-verifier`, 15.10.2026, 3375083..a44f029), puis une ronde de corrections ; les tests nommés passent un fichier à la fois.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `lib/formula.typ` `literal-stale` ; `test_formula.test_a_literal_agreeing_with_the_export_is_not_stale_and_one_that_differs_is`, `test_a_stale_and_an_own_value_compile_in_the_three_languages` |
| REQ-002 | ✅ | `unfold.generate` ; `test_unfold.test_an_unfolded_tension_computes_what_compute_computes` (α 0/30/90, 1e-6, clauses, aucune balise) ; `tests/projet-exemple/Formules/ZT-01.typ`, `ZT-02.typ` |
| REQ-003 | ✅ | `test_unfold.test_an_unfolded_domain_says_when_its_form_no_longer_matches` |
| REQ-004 | ✅ | `unfold.query_state` (`typst eval`) ; `test_a_domain_says_what_it_holds_through_typst`, `test_a_line_written_by_hand_is_read_without_a_parser` |
| REQ-005 | ✅ | `#verify(id:)` ; `test_formula.test_a_verify_id_is_once_per_domain` ; aucune balise écrite (`test_formula_domain`) |
| REQ-006 | ✅ | `test_unfold.test_a_line_taken_out_is_said_and_put_back_where_it_was` ; onglet : `test_formula_tab` (Réinsérer) |
| REQ-007 | ✅ | `test_unfold.test_each_state_of_a_line_and_a_base_that_does_not_read` (ronde 2 : les quatre états sur N, une base défectueuse nommée par fichier et champ) |
| REQ-008 | ✅ | `test_a_line_whose_data_changed_follows_it_and_nothing_else_of_the_file_moves` |
| REQ-009 | ✅ | `test_a_value_changed_in_vs_code_goes_back_into_the_check_s_source`, `…_becomes_the_engineer_s_own_and_is_taken_back`, `…_taken_as_written_and_a_conflict_waits_for_a_choice` |
| REQ-010 | ✅ | `test_regenerate_follows_a_new_form_and_keeps_what_the_engineer_wrote` |
| REQ-011 | ✅ | D-18 : `test_member_check.test_show_check_member_compiles_at_three_levels_and_prints_the_verdict` ; migration : `test_the_migration_rewrites_what_changed_saves_it_first_and_runs_once` |
| REQ-012 | ✅ | `test_schema.test_a_schema_is_a_drawing_a_native_figure_holds_and_cites` ; `show-schema` absent de `lib/` |
| UI-001 | ✅ | `test_schema_tab.test_the_highlighted_call_comes_first` (ronde 2 : texte exact copié) ; `test_call_command` (échappement de la légende). L'onglet « Connecteurs » ne copie aucun schéma : sans objet. |
| UI-002 | ✅ | `test_formula_tab.test_an_unfolded_check_shows_its_lines_states_and_imports_them` (ronde 2 : `local`, `own` + « Reprendre », `missing` + « Réinsérer », `conflict` + « Prendre celle de l'export », couleurs des pastilles) |
| UI-003 | ✅ | `test_member_check_tab.test_a_tension_saved_is_unfolded_shows_a_value_imported_from_its_file_and_opens_in_formulas` |
| UI-004 | ✅ | `test_formula.test_a_stale_and_an_own_value_compile_in_the_three_languages` |
| ARCH-001 | ✅ | `generate(record)` pur, écrit par `unfold_checks` après `checks.json` validé |
| ARCH-002 | ✅ | générateur sur `compute()` ; `verify-tension` reste dans `lib/timber.typ` pour la traction au feu (D-15), son dernier appelant |
| ARCH-003 | ✅ | (après correction, à la demande de l'ingénieur) une commande changée n'a que ses arguments changés remplacés, sur les étendues que le parseur relève (`typst_objects_parse._Parser.spans`, `formula_domain.patched`) : valeur, option ajoutée après le dernier argument, option retirée avec sa virgule, commentaires et retours à la ligne gardés ; l'export, « Importer » (`own: true`) et « Reprendre » passent par là (`unfold._replace_line`). `test_formula_domain.test_a_file_written_by_hand_is_kept_as_written…`, `test_unfold.test_a_line_the_engineer_laid_out_keeps_its_layout…` |
| ARCH-004 | ✅ | règle 15 réécrite ; décisions et index ; `test_docs_coherence` |
| ARCH-005 | ✅ | `domains.unfold`, `domains.unfold_migrate` sans PySide6 ; `calc/cli_unfold.py` |
| ARCH-006 | ✅ | (après correction) lecture sans balise, `Command.own/id/gen`, écriture ciblée (ARCH-003) ; plus aucun état `hand_edited` : `formula_domain.STATES` = `canonical`, `misnamed` (id déclaré autre que le nom du fichier, réécrit sous le sien), `unreadable` ; `test_formula_domain` |
| ARCH-007 | ✅ | `check-domain`, `checks.json` 1.3 ; `test_the_summary_lists_an_unfolded_check` |
| ARCH-008 | ✅ | `keys`/`clause`/`table` ; deux exports identiques ; `test_an_import_that_cannot_finish_writes_nothing` ; `write_source` ; `test_home.test_every_writer_an_editor_tab_reaches_is_guarded_wherever_it_is_defined` couvre les six nouveaux writers (`FormulaTab` est de `GUARDED_TABS`) |
| CON-001 à CON-006 | ✅ | clauses SIA 265 ; trois langues (`strings.json`, `fm_unfold_*`, `mc_open_formulas*`, `cli.json`) ; schémas versionnés ; sauvegarde et idempotence ; `check_unchanged` + `sharing._commit` ; docs, CHANGELOG v0.119, « Nouveautés » 0.119.0 fr/de/en, `///` et `commands.json` (`test_commands`) |
| §8 | ✅ | `show-static-model`, `show-plan`, les autres types, CU/BP non touchés |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-15 | draft | spécification extraite de la conversation du 15.10.2026 ; trois questions ouvertes (Q-001 à Q-003) |
| 2026-10-15 | specified | Q-001 à Q-003 répondues (A, A, A) → D-11 à D-13 ; reste : revue d'architecture, plan, approbation |
| 2026-10-15 | specified | revue d'architecture : REVOIR (201-203 bloquants) ; corrections 202/203 retenues ; Q-004 à Q-006 posées à l'ingénieur ; reste : réponses, plan, approbation |
| 2026-10-15 | reviewed | Q-004 à Q-006 répondues (A, A, B) → D-14 à D-16 ; ARCH-006 à ARCH-008 et D-17 ajoutés par la revue ; plan en 12 étapes ; reste : approbation |
| 2026-10-15 | approved | plan approuvé par l'ingénieur («je valide le plan d'implémentation») ; git pull fait (à jour avec origin/master fc22104) ; reste : étapes 1 à 12 |
| 2026-10-15 | implementation | étape 1 faite : `#var` littéral contrôlé par `domain:` (`literal-stale`, `literal-tolerance` 1e-6, `literal-rounding` 1e-3 — un 1.394 tapé contre un export de 1.39411… n'est pas périmé, trouvé sur l'exemple), `own:`, `#verify(id:)`, `#var-domain(gen:)` (forme seule ; la comparaison à l'export vient à l'étape 3) ; trois clés `formula.*` en trois langues ; `///`, exemples régénérés, `commands.json`, `display_options.DISMISSED` ; tests `test_formula` (+7), `test_commands`, `test_display_view`, `--related` vert (1383). Partiellement : REQ-001, REQ-003, REQ-005, UI-004. Reste : étapes 2 à 12 |
| 2026-10-15 | implementation | étape 2 faite : `wc-meta` émet `<woodcore-var>` depuis le contexte de `var`, `eq`, `verify` (le rendu de `verify-core` en fermeture, pour que la métadonnée ne soit pas perdue par un `return`) et `var-domain` ; `calc/domains/unfold.py` (`query_state` par `typst eval`, `typst query` étant obsolète en 0.15 ; repli sur le rapport) ; coût mesuré dans le bruit (2,27 s contre 2,21 s), consigné dans `docs/architecture/performance.md` ; `tests/test_unfold.py` (4) et sa ligne au catalogue. Réalisé : REQ-004. Reste : étapes 3 à 12 |
| 2026-10-15 | implementation | étape 3 faite : `_row` porte `keys`, `clause`, `table` (la valeur de Tabelle 8/9 d'une valeur de dimensionnement, jamais écrite dans une formule) ; `sia265.grade_table` ; `member_check.is_unfolded`, `form_of`, `published_vars` ; `checks.json` 1.3 (`vars`, `gen`, schéma additif) ; `check-domain` et `load-checks` dans `lib/calc-engine.typ`, branche de `find-calculation` et de `resolve-source` ; `#var-domain(gen:)` comparé au `gen` de l'export, rouge en tête et `matches: false` ; export du projet d'exemple régénéré. Tests `test_member_check` (85, +2), `test_unfold` (6, +2). Réalisé : REQ-003, ARCH-007 (partie données), ARCH-008 (partie `compute`). Reste : étapes 4 à 12 |
| 2026-10-15 | implementation | correctif : espace avant le label de `wc-meta` (imprimée devant chaque séparateur d'une ligne, `test_formula`) ; export 1.3 attendu par `test_links` et `test_fire_check_tab` là où une traction est dépliée. Étape 4 faite : `formula_domain` trouve le domaine par son appel `#var-domain(` (lexer, balise tolérée, plus écrite par `file_text`), garde pour chaque commande ses lignes écrites (`written`, `read_call`), l'en-tête écrit et le corps lu ; `body_of` rend le corps lu à l'octet quand rien n'a changé et n'écrit que la commande changée sinon ; `hand_edited` ne dit plus qu'un id autre que le nom du fichier (D-17) ; `domain:` avec valeur lu, écrit et calculé avec le littéral ; `gen:` lu et écrit dans l'en-tête ; `check_id(unfolded=True)` accepte l'id d'une vérification (D-14). Tests `test_formula_domain` (26, trois réécrits pour D-17, deux nouveaux), `--related` vert (102). Réalisé : ARCH-003, ARCH-006 (partie lecture et écriture). Reste : étapes 5 à 12 |
| 2026-10-15 | implementation | étape 5 faite : `unfold.generate` écrit une traction depuis les lignes de `compute()` (ligne de l'élément étiquetée `<id-member>`, côtés de la section au niveau 0, entrées en littéraux contrôlés, valeurs de table, `#eq` avec clause, titre de partie étiqueté, `#verify(id:)`, η en %), chaque ligne à part (`note: "line"`, vu à l'image) ; registre égal à `compute()` à 1e-6 pour α = 0, 30, 90 ; `Formules/unfold.json` (`schemas/unfold.schema.json`) ; `unfold_checks` appelé par `export_all` après `checks.json` et par `member_check.export` ; `#var-domain` garde son `gen` dans le registre et la Nachweisübersicht le trouve. Tests `test_unfold` (9). Réalisé : REQ-002, ARCH-001, ARCH-002 (générateur), ARCH-007 (résumé). Reste : étapes 6 à 12 |
| 2026-10-15 | implementation | étape 6 faite : `sync.three_way` extrait (la règle de `sync.py`, qui l'appelle désormais) ; `unfold.status` (états par ligne `in_sync`, `own`, `data`, `local`, `conflict`, `missing` ; une commande comparée par son appel, une forme ou un commentaire de l'ingénieur n'étant pas un changement), `refresh` (à l'export, la donnée seule changée, une seule ligne réécrite), `import_lines` ((a) vers `checks/<id>.json` par `member_check.write_source`, (b) `own: true`, formule prise telle qu'écrite, conflit sur choix), `take_back`, `reinsert`, `regenerate` (fusion par ligne, lignes de l'ingénieur gardées, nouveau `gen:`) ; base en paires `[own, seen]` ; écriture du domaine et de la base d'un seul coup (`sharing._commit`) ; `woodcore-cli unfold status|import|reinsert|take-back|regenerate` (`calc/cli_unfold.py`, mots fr/de/en dans `calc/i18n/cli.json`). Tests `test_unfold` (17, +8), `test_sync` (27). Réalisé : REQ-006 à REQ-010, ARCH-008 (atomicité, `write_source`). Reste : étapes 7 à 12 |
| 2026-10-15 | implementation | étape 7 faite : onglet « Formules » — carte « Vérification dépliée » (`formula_tab_unfold.FormulaUnfoldMixin` : vérification d'origine, forme, lignes non à jour et leur état, « Importer », « Tout importer », « Reprendre », « Réinsérer », « Garder la mienne », « Prendre celle de l'export », « Régénérer »), contour des pastilles à la couleur de l'état (`PILL_STATE_COLOURS` : `override`, `warning`, `danger`), mots `fm_unfold_*` fr/de/en, six écritures dans `WRITERS` ; onglet « Traction » — `UNFOLDED`, aperçu = domaine déplié du brouillon (`unfold.preview_body`), commande `#include "/Formules/<id>.typ"` sans les options de `#show-check-member`, « Ouvrir dans Formules », enregistrement par `member_check.write_source`. Tests : `test_formula_tab` (+1), `test_member_check_tab` (+1 ; sept tests génériques de `#show-check-member` portés sur la compression). Réalisé : UI-002, UI-003. Reste : étapes 8 à 12 |
| 2026-10-15 | implementation | étape 8 faite, modifiée par D-18 (question posée à l'ingénieur : refuser aurait arrêté chaque boucle `check-member-ids()`) : `#show-check-member` d'une traction dépliée imprime `Formules/<id>.typ` et refuse ses options ; une traction au feu reste à la commande (D-15), donc `verify-tension`, les branches `tension` de `draft_typst`, `check_command`, `shown_keys` et `lib/shown-variables.json` restent — aucun code mort pour l'instant, ils servent au feu ; l'onglet « Traction » ne montre plus les options de la commande (étape 7). Le projet d'exemple porte ses tractions dépliées (`Formules/ZT-01.typ`, `ZT-02.typ`, `unfold.json`, index régénéré). `///` de `#show-check-member` : D-18 dit et traduit, ses exemples sur DR-01/DR-02 (une traction ne se montre plus dans les données figées une fois regelées), pages régénérées. Tests `test_member_check` (cinq tests portés sur D-18), `test_commands` vert. Réalisé : REQ-011 (partie commande, D-18). Reste : étapes 9 à 12 |
| 2026-10-15 | implementation | étape 9 faite : `schema(schema, width:, highlight:, aids:)` (le corps de `show-schema` sans sa figure, le plafond de hauteur gardé) et `show-schema` retiré ; `build_reference` : `call_schema`, `call_schema_figure`, `wrap_figure`, `figure_label`, `typst_content`, la boucle en figure ; `display_options` « schema » sans légende ; l'onglet « Schémas » copie `#figure(schema(…), kind: image, caption: […]) <fig-…>` ; `///`, deux exemples (`@fig-…` imprime « Abbildung 1 », vu à l'image), traductions, galerie du site. Étape 10 faite : `calc/domains/unfold_migrate.py` (`plan`, `migrate` : balise des domaines retirée, `#show-check-member` d'une traction dépliée → `#include`, citations `-verify-tension`, `show-schema` → figure native, légende automatique écrite, label unique, boucle ; chaque fichier sauvé dans `<archives>/unfold-migration-<stamp>/`, tout ou rien, idempotent) appelée à l'ouverture d'un projet (`woodcore_gui`) et par `woodcore-cli unfold migrate [--dry-run]`, jamais par l'export ; le projet d'exemple migré (`poutre-p1.typ`). Étape 11 faite : règle 15 réécrite, cinq décisions et quatre « partly superseded in v0.118 » dans `docs/decisions.md` et son index, `docs/typst/formulas.md`, `docs/domain/member-checks.md`, `docs/ui/tab-member-checks.md`, `docs/ui/tab-formulas.md`, `docs/domain/detail-schemas.md`, `docs/ui/tab-schemas.md`, `docs/typst/api-conventions.md`, `docs/conventions/build-and-release.md`, `docs/open-questions.md`, `CHANGELOG.md` (v0.119), pages « Nouveautés » 0.119.0 fr/de/en. Tests : `test_schema` (+1), `test_call_command`, `test_display`, `test_schema_tab`, `test_unfold` (18, migration), `test_commands`, `test_site`, `test_docs_coherence` verts. Réalisé : REQ-012, UI-001, REQ-011 (migration), CON-004, ARCH-004, CON-006. Reste : étape 12 (suite complète, vérification indépendante) |
| 2026-10-15 | verification | vérification indépendante : 21 ✅, 8 ⚠️, 0 ❌ ; ronde 2 : tests ajoutés pour REQ-007 (les quatre états, base défectueuse), UI-001 (texte exact copié ; « Connecteurs » sans objet), UI-002 (own, missing, conflict dans l'onglet) ; ARCH-002 et ARCH-008 prouvés (D-15, `test_home`). Restent deux réserves, ARCH-003 et ARCH-006 (commande changée réécrite entière ; `hand_edited` pour un id autre que le nom du fichier), soumises à l'ingénieur. Suite complète en cours |
| 2026-10-15 | verification | suite complète : 2940 passés, 15 ignorés, 0 échec (1648 s) ; les tests de la ronde 2 passent seuls (`test_unfold` 19, `test_schema_tab` 43, `test_formula_tab` 21). Reste : la décision de l'ingénieur sur ARCH-003/ARCH-006, puis `completed` |
| 2026-10-15 | completed | les deux réserves corrigées à la demande de l'ingénieur (« traite les deux écarts maintenant ») : ARCH-003 — le parseur relève l'étendue de chaque argument, `formula_domain.patched` ne remplace que les arguments changés (ajout après le dernier, retrait avec sa virgule, commentaires gardés ; repli : l'appel seul réécrit, ce qui l'entoure gardé), `unfold` garde les lignes écrites en actualisant, important ou reprenant ; ARCH-006 — `hand_edited` remplacé par `misnamed`, `STATES` sans lui. Tests : `test_formula_domain` (26), `test_unfold` (20, un nouveau), `test_formula_tab` (21) ; décisions, `formulas.md`, catalogue, `CHANGELOG.md`, « Nouveautés » fr/de/en. Spécification terminée |
