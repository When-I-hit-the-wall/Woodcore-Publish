---
id: 2026-10-08-onglet-formules-editeur-dossiers-include
titre: Onglet « Formules » (issue #15) — deux bugs, options au clic simple, id = nom de fichier, #include, éditeur de texte, ordre et dossiers par un noyau commun
status: completed
cree: 2026-10-08
mis_a_jour: 2026-10-09
source: message écrit (issue GitHub When-I-hit-the-wall/Woodcore#15 « Formules », son corps et ses deux commentaires du 2026-10-08)
docs: [docs/ui/window.md, docs/typst/formulas.md, docs/architecture/principles.md, docs/architecture/layout.md, docs/architecture/data-contracts.md, docs/decisions.md, docs/open-questions.md]
---

# Onglet « Formules » : éditeur, dossiers, ordre et `#include` — Spécification

## 1. Objectif

L'onglet *Formule* (v0.117, spec `docs/requirements/completed/2026-10-08-onglet-formule-domaines.md`) écrit des domaines de calcul par blocs de commandes. L'ingénieur, à l'usage, veut : deux bugs corrigés (un fantôme de bloc après Entrée, le nom d'une équation perdu au double-clic) ; les options d'un bloc au clic simple ; l'onglet renommé « Formules » ; un domaine appelé par son **id = nom de fichier**, imprimé par un simple `#include "/Formules/<id>.typ"` pour qu'un renommage ne casse rien ; un volet central qui se comporte comme un **éditeur de texte** (du Typst libre entre les blocs, coloré) ; et une liste de domaines **ordonnable et rangée en dossiers**, par **un seul noyau** partagé avec les autres onglets qui ont cet arbre (Schémas…).

## 2. Source

> **T1** — « un bug lorsqu'on crée une nouvelle variable (accepter la variable avec enter): un fantome du bloc de commande reste visible » *(corps de l'issue, avec une capture 944×76)*
>
> **T2** — « Un **clic simple** sur un bloc `var` validé affiche dans le volet de droite les options de la commande `var` (aujourd'hui seulement au double-clic). »
>
> **T3** — « **Bug** : double-clic sur une équation (`eq`). observé : le nom de la variable résultat disparaît ; attendu : le nom reste affiché dans le bloc rouvert ; pour reproduire : double-cliquer sur un bloc `eq` validé »
>
> **T4** — « Renommer l'onglet dans les trois langues : FR **Formules**, DE **Formeln**, EN **Formulas**. »
>
> **T5** — « L'**id du domaine est le nom de son fichier** (`Formules/<id>.typ`) ; `#show-formula` appelle l'id et non plus le nom du domaine, pour qu'un renommage du domaine ne casse pas les appels : `#show-formula("<id>", level: 2)`. »
>
> **T6** — « Dans le volet de droite, un champ **ID**, rempli automatiquement depuis le nom mais écrasable ; changer l'ID renomme le fichier. »
>
> **T7** — « Le volet central fonctionne comme un **éditeur de texte** : hors d'un bloc de commande, un curseur clignotant indique où l'on écrit, et on y tape du Typst (titre, sous-titre, formule mathématique), affiché comme **source Typst colorée** (comme l'onglet Python, `TypstHighlighter`). »
>
> **T8** — « Un **clic en dehors d'un bloc de commande** en cours d'écriture valide le bloc, comme Entrée. »
>
> **T9** — « Réorganiser l'ordre des domaines par **glisser-déposer** ; l'ordre est gardé par Woodcore dans un fichier du projet (`_woodcore/`), le même mécanisme pour tous les onglets du même noyau ; noms de fichiers et id inchangés. »
>
> **T10** — « **Dossiers** : créer un dossier, supprimer un dossier ou un domaine (→ « Archives »), dupliquer un domaine, comme dans l'onglet *Schémas*. Un dossier est un **groupe** (`GroupedList`) ; les fichiers restent à plat dans `Formules/`. »
>
> **T11** — « **Un seul noyau** pour tous les onglets qui ont cet arbre (Schémas, Formules…) — pas de copie propre à l'onglet Formules. »
>
> **T12** — « Remplacer `#show-formula` par `#include "/Formules/<id>.typ"`, puisque l'id du domaine est le nom de son fichier. Le domaine s'imprime alors au niveau du rapport : le `level:` propre au domaine (règle 0/1/2/3 de `formula-block`, `lib/formula.typ`) et le refus qui liste les domaines existants disparaissent. Ce point remplace le précédent « `#show-formula` appelle l'id et non plus le nom du domaine : `#show-formula("<id>", level: 2)` ». » *(second commentaire)*

## 3. Exigences fonctionnelles

### REQ-001 — Plus de fantôme après Entrée
- **Exigence** : Woodcore doit, quand un bloc en cours d'écriture est validé (Entrée, ou le clic de REQ-007), ne plus laisser visible aucun élément de son éditeur (champs, libellés, ✕, rappel des touches).
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : test : un bloc `var` créé, rempli, validé par Entrée ; après le traitement des événements, le bloc n'a plus aucun `QLineEdit` ni `QPushButton` enfant visible, et sa hauteur est celle d'un bloc lu depuis le fichier. *(Cause relevée dans le code, à confirmer par le test : `Block.clear()` retire la grille de son layout sans détruire les widgets qu'elle range — `item.widget()` vaut `None` pour un layout imbriqué.)*

### REQ-002 — Le nom d'une équation reste au double-clic
- **Exigence** : Woodcore doit, à la réouverture d'un bloc `eq` validé, remplir le champ « Variable affichée » avec le symbole affiché de l'équation (son symbole, ou sa clé quand le symbole est la clé elle-même).
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : test : `#eq("M_d", …)` (symbole = clé, donc `symbol` vide dans le modèle) rouvert → le champ vaut `M_d` ; revalidé sans changement → le fichier est identique octet pour octet.

### REQ-003 — Options au clic simple
- **Exigence** : Woodcore doit, à un clic simple sur un bloc validé, afficher à droite — **au-dessus de la palette, les deux visibles, le volet défilant** (Q-008) — les options de sa commande (lues de sa signature, comme pour un bloc ouvert) ; une option changée là est écrite dans le fichier, comme une validation, une fois la saisie finie (pas à chaque touche). Tous les blocs validés : `var`, `eq`, `verify`, `val`, `var-unit` (Q-001).
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : test : clic simple sur un `var` validé → la pile de droite montre les options de `var` ; `label` changé → `Formules/<id>.typ` contient le nouveau `label:` ; le bloc reste fermé.

### REQ-004 — L'id d'un domaine est le nom de son fichier, éditable
- **Exigence** : Woodcore doit offrir, dans les options du domaine (volet de droite), un champ **ID** : rempli depuis le nom (`slug`) **tant que le fichier n'existe pas** et que l'ingénieur ne l'a pas écrit lui-même (après le premier enregistrement, changer le nom ne renomme jamais le fichier — ARCH-RISK-104), écrasable, refusé s'il n'est pas un id valable (`structure.ID_PATTERN`) ou déjà pris ; un ID changé **renomme le fichier** `Formules/<ancien>.typ` → `Formules/<nouveau>.typ`, l'argument de `#var-domain` est réécrit, l'ordre et le dossier du domaine (REQ-008, REQ-009) le suivent, et Woodcore **avertit en listant** les fichiers et lignes du projet qui citent l'ancien id (`#include "/Formules/<ancien>.typ"`, `domain: "<ancien>"`) sans rien réécrire (Q-007). Un fichier dont l'argument de `#var-domain` diffère du nom de fichier est `hand_edited` ; deux fichiers au même argument arrêtent l'export.
- **Source** : T5, T6
- **Priorité** : doit
- **Critère d'acceptation** : tests : nouveau domaine « Poutre P2 » → ID `poutre-p2` ; nom changé avant tout ID écrit → ID suit ; ID écrit `p2` → fichier `Formules/p2.typ`, l'ancien n'existe plus, le domaine garde sa place et son dossier ; ID `P 2` ou un ID déjà pris → refus nommant la raison, rien renommé.

### REQ-005 — `#include` remplace `#show-formula`, tout par l'id
- **Exigence** : Woodcore doit faire imprimer un domaine par `#include "/Formules/<id>.typ"` : la commande `#show-formula`, sa règle de niveau propre au domaine (`formula-block`, `block-level`, `line-level` en tant qu'elles ne servent qu'à elle) et son refus listant les domaines sont retirés ; chaque commande du domaine s'imprime à son propre `level:` ou à celui du rapport. Le mode *Affichage* de l'onglet montre et copie la ligne `#include`, et le « Typst développé » n'a plus de niveau à choisir. **Tout par l'id** (Q-002) : le fichier écrit `#var-domain("<id>")`, une valeur se lit `#val(key, domain: "<id>")`, et l'onglet *Variables* liste le domaine sous son id ; le **nom** est l'argument `title:` de `#var-domain` (Q-006), que `var-domain` **imprime comme titre** au niveau de la section qui l'inclut + 1 (Q-011) ; `title:` est facultatif, un `#var-domain` sans lui (documents existants) n'imprime rien de plus. Un ID changé (REQ-004) réécrit aussi l'argument de `#var-domain`.
- **Source** : T12 (remplace T5 pour l'appel)
- **Priorité** : doit
- **Critère d'acceptation** : un rapport d'essai `#include "/Formules/poutre-p1.typ"` compile et imprime les quatre blocs ; `grep show-formula` hors `archive/`, `CHANGELOG.md`, `website/content/*/changes/0.117.0.md` et `docs/requirements/completed/` ne trouve plus rien ; `test_units.py` reste vert ; le mode Affichage copie exactement `#include "/Formules/poutre-p1.typ"` ; le fichier d'exemple écrit `#var-domain("poutre-p1")` et `#val("M_d", domain: "poutre-p1")` compile ; un domaine renommé (nom seul) ne change pas son fichier hors de la ligne du nom et ne casse aucun appel.

### REQ-006 — Le volet central est un éditeur de texte
- **Exigence** : Woodcore doit permettre d'écrire, **entre les blocs de commandes** d'un domaine (avant le premier, entre deux, après le dernier), du Typst libre — titre, sous-titre, formule mathématique — dans une **fine zone de texte dans chaque intervalle**, toujours éditable, haute d'une ligne quand elle est vide et non écrite au fichier si vide (Q-009), à curseur clignotant, colorée par `richtext.TypstHighlighter` ; ce texte est écrit dans le corps du `#var-domain` du fichier, à sa place parmi les commandes, et relu tel quel (un fichier ainsi écrit reste `canonical`) ; les calculs Python l'ignorent. Une commande de la palette s'insère **à l'endroit du curseur** (le texte y est coupé en deux). Refusés avant toute écriture, rien n'étant écrit : un `#var`/`#eq`/`#var-unit`/`#verify` dans le texte (Typst l'exécuterait, Python non), une ligne `// woodcore:`, des crochets déséquilibrés ; le corps est relu en mémoire et doit redonner le modèle avant d'être écrit (ARCH-RISK-108).
- **Source** : T7
- **Priorité** : doit
- **Critère d'acceptation** : tests : `= Poutre P1` tapé avant le premier bloc et `$ M = q l^2 / 8 $` entre deux blocs → le fichier les contient à ces places, relu `canonical`, mêmes résultats de calcul ; `var` ajouté curseur au milieu d'un texte → texte coupé, bloc entre les deux moitiés ; le domaine d'exemple sans texte se relit octet pour octet.

### REQ-007 — Un clic hors du bloc valide
- **Exigence** : Woodcore doit valider le bloc en cours d'écriture, comme Entrée, quand l'ingénieur clique dans le volet central en dehors de ce bloc ; un bloc qui ne se valide pas (champ manquant, formule refusée) reste ouvert avec son message.
- **Source** : T8
- **Priorité** : doit
- **Critère d'acceptation** : tests : bloc `var` rempli, clic sur un autre bloc ou dans une zone de texte → validé, fichier écrit ; bloc à valeur « abc », même clic → reste ouvert, message `fm_not_number`. Un clic sur une variable de droite (insertion, REQ-010 de la spec v0.117) ne valide pas.

### REQ-008 — Ordre choisi par glisser-déposer, gardé dans `_woodcore/`
- **Exigence** : Woodcore doit permettre de réordonner les entrées de la liste de gauche par glisser-déposer (dans un dossier et à la racine), et garder cet ordre dans un fichier du projet sous `_woodcore/`, par onglet ; noms de fichiers et id inchangés ; une entrée que le fichier d'ordre ne connaît pas (nouvelle, ou créée hors de Woodcore) se range à la fin, par id ; une entrée disparue est oubliée sans erreur. Le mécanisme est celui du noyau (ARCH-001), donc valable pour **tous les onglets** qui l'utilisent ; le fichier est `Woodcore-Datei/lists.json` (dossier des sources, Q-005 — pas `_woodcore/`, qui est régénéré). L'ordre promis est celui **dans un dossier et à la racine** ; les dossiers restent alphabétiques. L'ordre ne vaut que pour la fenêtre : le rapport imprime toujours par id et le fichier n'entre pas dans l'export (Q-010).
- **Source** : T9, T11
- **Priorité** : doit
- **Critère d'acceptation** : tests : dans *Formules*, `b` glissé avant `a` → liste `b, a` après rechargement et redémarrage, fichier d'ordre écrit, aucun `.typ` touché ; même test dans *Schémas* ; un `.typ` ajouté à la main apparaît à la fin ; un fichier d'ordre mal formé → avertissement nommant le fichier et le champ, ordre par id, fichier laissé intact, glisser-déposer refusé avec le même message (il n'entre pas dans l'export, Q-010).

### REQ-009 — Dossiers, archives, duplication dans *Formules*
- **Exigence** : Woodcore doit offrir dans *Formules*, par le même `GroupedList` que *Schémas* : créer, renommer, supprimer un dossier (ses domaines reviennent à la racine, comme dans *Schémas*) ; ranger un domaine dans un dossier par glisser-déposer ; supprimer un domaine → « Archives » (restaurable, purgeable comme ailleurs) ; dupliquer un domaine (nouveau fichier, nouvel id libre, même dossier). Les fichiers restent à plat dans `Formules/`. Le dossier d'un domaine est gardé dans le fichier d'ordre de `_woodcore/` (Q-003) : ranger un domaine ne réécrit pas son `.typ`.
- **Source** : T10
- **Priorité** : doit
- **Critère d'acceptation** : tests : dossier « Toiture » créé, `poutre-p1` glissé dedans → affiché dans le dossier après rechargement, `Formules/poutre-p1.typ` toujours à plat ; dupliqué → `poutre-p1-2.typ` (ou id libre suivant), nom « … (copie) », même dossier ; supprimé → sous « Archives », fichier dans `Formules/archives/`, restauré → revient.

### REQ-010 — Les variables restent calculées en Python dès leur création
- **Exigence** : Woodcore doit continuer de calculer chaque bloc en Python à sa validation (`calc/units.py`) et d'écrire l'index `data/formulas.json` à chaque enregistrement (Q-004 : gardé), de sorte qu'une variable créée dans *Formules* soit aussitôt listée, avec sa valeur, dans l'onglet *Variables* — le texte libre (REQ-006), l'id (REQ-004) et l'ordre (REQ-008) n'y changent rien.
- **Source** : réponse à Q-003
- **Priorité** : doit
- **Critère d'acceptation** : test : un `var` validé dans *Formules* → `data/formulas.json` réécrit, `variable_sources` lit le domaine sous son id avec la valeur ; `test_variable_sources` vert.

## 4. Exigences d'interface

### UI-001 — L'onglet s'appelle « Formules »
- **Exigence** : le titre de l'onglet devient FR « Formules », DE « Formeln », EN « Formulas » (clé `tab_formula`, partout où l'onglet est nommé : barre, navigation, aide).
- **Source** : T4
- **Langues** : fr / de / en
- **Critère d'acceptation** : `test_formula_tab` assert les trois titres ; `test_i18n` vert.

### UI-002 — Le champ ID et les mots nouveaux
- **Exigence** : le champ ID (REQ-004), les zones de texte (REQ-006), les actions de dossier et de duplication (REQ-009) et tout message nouveau existent dans les trois langues ; les textes qui nomment `#show-formula` ou « le niveau du domaine » (`fm_name_tip`, `fm_domain_note`, `fm_options_note`, `fm_display_call`…) sont réécrits.
- **Source** : T5–T7, T10, T12
- **Langues** : fr / de / en
- **Critère d'acceptation** : aucune chaîne de `formula_tab.STRINGS` ne mentionne `show-formula` ; `test_i18n` vert.

## 5. Exigences d'architecture

### ARCH-001 — Un seul noyau pour l'arbre des onglets
- **Exigence** : l'ordre (REQ-008), les dossiers et les archives (REQ-009) sont réalisés **dans** `calc/tools/grouped_list.py` et un module de stockage d'ordre sans Qt partagé, utilisés par *Formules* comme par *Schémas* et les autres onglets à `GroupedList` ; aucune copie propre à *Formules*. L'arbre de *Formules* (`QTreeWidget` + `_Rows`) est remplacé par `GroupedList`.
- **Source** : T11, T10 ; principe « One source of truth »
- **Critère d'acceptation** : `formula_tab.py` ne construit plus de `QTreeWidget` pour la liste des domaines ; le code d'ordre n'existe qu'une fois (grep) ; les tests de `grouped_list` et des onglets qui l'utilisent restent verts.

### ARCH-002 — Le domaine reste hors de Qt
- **Exigence** : le texte libre (REQ-006), l'id éditable et le renommage de fichier (REQ-004), la duplication (REQ-009) sont dans `calc/domains/formula_domain.py`, sans Qt ; l'onglet ne fait que les appeler.
- **Source** : principe « Domain logic is independent of the UI »
- **Critère d'acceptation** : `test_formula_domain` couvre lecture/écriture du texte libre, `rename`, `duplicate` sans importer Qt.

### ARCH-003 — Contrats versionnés
- **Exigence** : le fichier d'ordre de `_woodcore/` a un schéma dans `schemas/` avec `schema_version` ; le sort de `data/formulas.json` (Q-004) est tranché et, s'il change, son `schema_version` monte.
- **Source** : principe « Explicit, versioned data models »
- **Critère d'acceptation** : `validation.validate_structure` appliqué au fichier d'ordre à l'écriture et à la lecture ; test de refus nommant le champ.

## 6. Contraintes

- **CON-001** *(inféré, CLAUDE.md)* — la spec v0.117 n'est pas commitée et ses fichiers ne sont qu'à elle jusqu'ici ; la session « Onglet formule avec domaines de calcul » a cédé #15 le 2026-10-08 et ne modifie plus rien. Éditions ciblées ; `grouped_list.py` et les onglets qui l'utilisent peuvent être modifiés par d'autres sessions : coordination avant d'y toucher.
- **CON-002** *(inféré, la session v0.117)* — `tests/test_units.py` tient Python = Typst (31 formules) : toute modification de `lib/formula.typ` le garde vert.
- **CON-003** *(inféré)* — un domaine écrit à la main en VS Code reste lisible (`hand_edited` / `unreadable` inchangés) ; un projet sans fichier d'ordre s'ouvre (ordre par id).
- **CON-004** *(inféré, décision à reporter)* — T12 renverse D-09/D-11/D-02/D-12 de la spec v0.117 : `docs/decisions.md` reçoit une entrée REVERSING avec son prix (plus de niveau propre au domaine).
- **CON-005** *(inféré, CLAUDE.md)* — documentation : `docs/ui/window.md` (paragraphe de l'onglet et §10quater de `GroupedList`), `docs/typst/formulas.md` (§ de `show-formula` remplacé par `#include`), `docs/architecture/layout.md`/`data-contracts.md` (fichier d'ordre), `CHANGELOG.md`, « Nouveautés » fr/de/en ; une commande Typst retirée : son `///`, ses exemples (`examples/show-formula-*.typ`) et sa traduction dans `calc/i18n/commands.json` retirés.

## 7. Décisions prises

- **D-01** — `#include "/Formules/<id>.typ"` remplace `#show-formula` ; le niveau propre au domaine disparaît (T12, l'ingénieur, 2026-10-08). Prix accepté : on ne choisit plus d'un coup le niveau d'un domaine entier ; chaque commande garde son `level:`.
- **D-02** — l'id du domaine est le nom de son fichier, éditable dans le volet de droite, et le changer renomme le fichier (T5, T6).
- **D-03** — un dossier est un groupe de `GroupedList`, pas un répertoire ; les fichiers restent à plat (T10).
- **D-05** — options au clic simple pour tout bloc validé (Q-001).
- **D-06** — tout par l'id : `#var-domain("<id>", title: …)`, `#val(key, domain: "<id>")` ; le nom n'est qu'affiché (Q-002). Prix : les appels `#val(domain: "<nom>")` déjà écrits (domaine d'exemple, exemples, tests) sont réécrits ; v0.117 n'étant pas publiée, aucun projet de l'ingénieur ne les porte (à vérifier dans la revue).
- **D-07** — le dossier d'un domaine est gardé dans le fichier d'ordre de `_woodcore/` (Q-003). Prix : un `.typ` copié dans un autre projet arrive à la racine.
- **D-08** — `data/formulas.json` est gardé comme index pour *Variables* et l'export (Q-004) ; il est indexé par id.
- **D-09** — fichier d'ordre et de dossiers : `Woodcore-Datei/lists.json` (dossier des sources), pas `_woodcore/` (Q-005). Prix : l'écart avec la lettre de l'issue, et une ligne de plus dans l'archive export.
- **D-10** — le nom du domaine est `#var-domain(id, title: "<nom>")`, et `var-domain` l'imprime comme titre au niveau de la section + 1 (Q-006, Q-011). Prix : une commande de tous les documents s'élargit (argument facultatif : `///`, deux exemples, `commands.json` fr/de/en) ; un titre tapé aussi en texte libre ferait double emploi.
- **D-11** — un ID changé : Woodcore avertit et liste les citations de l'ancien id, ne réécrit rien (Q-007).
- **D-12** — volet de droite : variables, options du bloc choisi, palette, tout visible, le volet défile (Q-008).
- **D-13** — texte libre : une fine zone dans chaque intervalle (Q-009).
- **D-14** — l'ordre de la fenêtre ne change pas l'ordre d'impression ; `lists.json` n'est pas une entrée de l'export (Q-010).
- **D-15** — les pages 0.117 (`CHANGELOG.md`, « Nouveautés » 0.117.0) ne sont pas publiées (`project.VERSION` = 0.116.0) : elles sont réécrites pour décrire `#include`, pas gardées comme histoire.
- **D-16** *(revue)* — Formules est la seule exception à « un dossier est un champ » (décision v0.69) : un domaine est un `.typ` ; les onglets JSON gardent leur `group` et `lists.json` n'y garde que l'ordre ; `groups` n'est accepté que pour l'onglet marqué.
- **D-04** — un seul noyau pour l'arbre des onglets ; l'ordre est gardé dans `_woodcore/`, valable pour tous les onglets du noyau (T9, T11).

## 8. Hors périmètre

- Les autres onglets à `GroupedList` ne gagnent ni duplication ni archives qu'ils n'ont pas déjà : seul l'**ordre** leur est ajouté (T9).
- L'issue #13 (onglet *Variables*) : déjà faite par sa propre spec (`completed/2026-10-08-onglet-variables-trois-colonnes.md`).
- La substitution d'une clé dans une unité entre guillemets (`open-questions.md`, piège v0.117) n'est pas traitée ici.

## 9. Idées non retenues comme exigences

- T5 dans sa forme `#show-formula("<id>", level: 2)` : remplacé par T12 sur décision de l'ingénieur ; gardé ici pour la trace.

## 10. Questions

### Q-001 — Options au clic simple : `var` seulement ou tout bloc ?
- **Pourquoi elle compte** : T2 nomme `var` ; `eq`, `verify`, `val`, `var-unit` ont aussi des options (label, norm, level…).
- **Options** : A tout bloc validé ; B `var` seulement.
- **Réponse** : A — tout bloc validé (l'ingénieur, 2026-10-08).

### Q-002 — `#val(key, domain: …)` et le nom du domaine
- **Pourquoi elle compte** : T5 veut qu'« un renommage du domaine ne casse pas les appels » ; `#include` règle l'appel du domaine, mais `#val(key, domain: "<nom>")` lit toujours le **nom** donné à `#var-domain("<nom>")` : renommer le domaine casse ces appels-là.
- **Options** : A `#var-domain` reçoit l'id et `#val(domain:)` aussi ; le nom n'est que ce que l'onglet affiche. B garder le nom pour `#val(domain:)` (un renommage casse ces appels, la compilation dit lequel).
- **Réponse** : A — tout par l'id : `#var-domain("<id>")` et `#val(key, domain: "<id>")` ; le nom n'est que ce que l'onglet affiche (l'ingénieur, 2026-10-08).

### Q-003 — Où est gardé le dossier d'un domaine ?
- **Pourquoi elle compte** : ailleurs, le dossier est un champ `group` dans le JSON de chaque source ; un domaine est un `.typ`.
- **Options** : A dans le fichier d'ordre de `_woodcore/`, à côté de l'ordre (les `.typ` ne changent pas) ; B dans le `.typ`, sur la ligne de balise (`// woodcore:object formula-domain domain` + un groupe).
- **Réponse** : A — dans le fichier d'ordre de `_woodcore/`, après explication des deux options (l'ingénieur, 2026-10-08). Il a ajouté : « Je souhaiterais que les calculs soient également calculés en python, donc que les variables soient disponibles dans woodcore lorsqu'elles sont créées » — déjà le cas (D-10 v0.117 : calcul Python à chaque validation ; l'index réécrit à chaque enregistrement ; l'onglet *Variables* recalcule les domaines) et tenu par REQ-010.

### Q-004 — `data/formulas.json` après `#include`
- **Pourquoi elle compte** : Typst ne le lit plus ; l'onglet *Variables* (`variable_sources.FILE_SOURCES`) et la vérification à l'export (deux fichiers nommant un même domaine, fichier illisible) s'en servent.
- **Options** : A le garder comme index pour *Variables* et l'export ; B le retirer, *Variables* lisant `Formules/` directement (une source de moins).
- **Réponse** : A — le garder comme index pour *Variables* et l'export (l'ingénieur, 2026-10-08).

### Q-005 — Fichier de l'ordre et des dossiers
- **Réponse** : `Woodcore-Datei/` (recommandé par la revue, ARCH-RISK-201 : `_woodcore/` est régénéré) — l'ingénieur, 2026-10-08.

### Q-006 — Où garder le nom affiché
- **Options** : A ligne de commentaire dans le `.typ` ; B argument de `var-domain`.
- **Réponse** : B, argument de `var-domain` (`title:`) — l'ingénieur, 2026-10-08.

### Q-007 — Les citations d'un ancien id
- **Réponse** : avertir et lister, rien réécrire — l'ingénieur, 2026-10-08.

### Q-008 — Palette et options
- **Réponse** : « les deux. le volet pour se défiler » — options et palette visibles ensemble, le volet défile — l'ingénieur, 2026-10-08.

### Q-009 — Zones de texte
- **Réponse** : une zone dans chaque intervalle — l'ingénieur, 2026-10-08.

### Q-010 — L'ordre et le rapport
- **Réponse** : fenêtre seulement — l'ingénieur, 2026-10-08.

### Q-011 — `title:` imprimé ?
- **Réponse** : oui, comme titre (niveau de la section + 1) — l'ingénieur, 2026-10-08.

## 11. Critères d'acceptation

- [x] REQ-001 — aucun widget d'éditeur visible après Entrée.
- [x] REQ-002 — `eq` rouvert garde son nom ; revalidé, fichier identique.
- [x] REQ-003 — options au clic simple, écrites dans le fichier.
- [x] REQ-004 — champ ID, renommage du fichier, refus d'un id invalide ou pris.
- [x] REQ-005 — `#include` imprime le domaine ; `show-formula` retiré.
- [x] REQ-006 — texte Typst libre entre les blocs, coloré, écrit et relu `canonical`.
- [x] REQ-007 — clic hors du bloc = Entrée.
- [x] REQ-008 — ordre par glisser-déposer gardé dans `Woodcore-Datei/lists.json` (D-09), *Formules* et *Schémas*.
- [x] REQ-009 — dossiers, archives, duplication dans *Formules*.
- [x] ARCH-004 — `var-domain(title:)` documenté (`///`, deux exemples compilés, `commands.json` fr/de/en) ; `formulas.json` en `schema_version` 2.0 indexé par id.
- [x] REQ-010 — variable créée → calculée en Python, listée dans *Variables* sous l'id du domaine.
- [x] UI-001 — « Formules / Formeln / Formulas ».
- [x] UI-002 — mots nouveaux en trois langues, plus de `show-formula` dans l'onglet.
- [x] ARCH-001 — un seul noyau (`GroupedList` + stockage d'ordre).
- [x] ARCH-002 — domaine sans Qt.
- [x] ARCH-003 — fichier d'ordre schématisé et versionné.
- [x] Documentation : `window.md`, `formulas.md`, `layout.md`, `data-contracts.md`, `decisions.md` (REVERSING), `CHANGELOG.md`, « Nouveautés » fr/de/en ; `show-formula` retiré de `commands.json` et des exemples.
- [x] Tests : `test_formula_domain`, `test_formula_tab`, `test_units`, `test_grouped_list` (ou l'équivalent), `test_schema*`, `test_variables`, `test_variable_sources`, `test_i18n` verts.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001 | capturé |
| T2 | REQ-003 | capturé ; portée → Q-001 |
| T3 | REQ-002 | capturé |
| T4 | UI-001 | capturé |
| T5 | REQ-004, D-02 ; forme `#show-formula("<id>")` → §9 | capturé ; `#val` → Q-002 |
| T6 | REQ-004 | capturé |
| T7 | REQ-006 | capturé |
| T8 | REQ-007 | capturé |
| T9 | REQ-008, D-04 | capturé |
| T10 | REQ-009, D-03 | capturé ; stockage du dossier → Q-003 |
| T11 | ARCH-001, D-04 | capturé |
| T12 | REQ-005, D-01 | capturé ; index → Q-004 (D-08) |
| réponse Q-003 | REQ-010 | capturé |

### Points de la source non résolus

- Aucun : Q-001 à Q-004 répondues le 2026-10-08.

## 13. Revue d'architecture

Deux revues `architecture-reviewer` (Sonnet) en parallèle, 2026-10-08 : **domaine et Typst** (ARCH-RISK-101…113) et **noyau de liste** (ARCH-RISK-201…214). Verdict des deux : **APPROUVER AVEC RÉSERVES** ; les réserves qui demandaient l'ingénieur sont tranchées par Q-005 à Q-011, les autres sont reprises au plan (§14).

**Faits établis dans le code.**
- REQ-001 : `Block.clear()` (`formula_tab.py:281`) ne détruit que les `item.widget()` ; la grille ajoutée par `addLayout` garde ses champs, enfants du bloc et visibles — le fantôme, qui s'accumule à chaque double-clic. Piège de test : `deleteLater` n'est pas exécuté par `processEvents` (il faut `sendPostedEvents(None, DeferredDelete)`).
- REQ-002 : `show_editor` remplit `symbol` avec `c.symbol`, que `symbol_for` vide quand le symbole est la clé ; il faut `c.shown_symbol` pour `eq`.
- REQ-005 : `show-formula` faisait déjà `include ("/" + file)` (`lib/formula.typ:1645`) : `#include "/Formules/<id>.typ"` marche depuis une section ; les balises sont des commentaires, rien ne s'imprime en trop.

**Risques retenus (sévérité → traitement).**
- 101 important — fantôme : un conteneur par mode, remplacé en bloc. 102 mineur — symbole `eq`.
- 103 important — options d'un bloc fermé : extraire `panel_options`, `replace` du `Command`, écrire en différé (≈ 400 ms ou fin de saisie), sans remettre le volet à zéro ; palette et options visibles ensemble (Q-008).
- 104 important — id = nom de fichier : `read()` fixe `id = stem`, argument ≠ nom → `hand_edited`, deux arguments égaux arrêtent l'export ; l'id ne suit le nom qu'avant le premier enregistrement ; `name_taken` devient une règle douce de l'onglet.
- 105 important — renommer : valider, `os.replace` d'abord, réécrire l'argument, index, `lists.json` ; `PermissionError` (VS Code tient le fichier) dit, rien changé ; citations listées (Q-007).
- 106 important — retirer `show-formula` avec `formula-block`, `block-level`, `line-level(kind:)`, l'entrée CATEGORIES/SAMPLE_FOR, SPECS/DISMISSED, `commands.json`, les exemples, et le miroir Python (`block_level`, `expanded`, `show_call`).
- 107 mineur — un titre en texte libre prend l'`offset` de la section ; documenté.
- 108 important — texte libre : `Command("text", raw=…)` (branche `raw` de `to_call` déjà là, morte aujourd'hui) ; segmenteur fondé sur `typst_paths._Lexer`, pas sur une regex ; refus listés en REQ-006 ; relecture en mémoire avant écriture ; `compute` rend un `Result()` vide pour un texte (alignement des `zip`).
- 109 — zones de texte : une par intervalle (Q-009) ; `TypstHighlighter` est ligne par ligne, accepté tel quel (le site partage son tokenizer).
- 110 important — clic hors du bloc : filtre `MouseButtonPress` au niveau de l'application, parenté à l'onglet, limité au viewport central, hors du bloc ouvert ; validation différée (`singleShot(0)`) ; ni le volet droit ni la liste de gauche ne valident.
- 111 / 205 important — garde lecture seule : toute écriture nouvelle passe par `save()`/`delete()` ou entre dans `WRITERS` ; `app.save_list_order` se garde comme `save_folder_settings`.
- 112 important — `formulas.json` indexé par id : `schema_version` 2.0 ; `variable_domains` liste le dossier et `Domain(name=id, label=nom)`.
- 113 mineur — code mort (`MAIN`, `TAKEN`, `LEVELS`, `show_call`) retiré ; refus nouveaux traduits par leur code.
- 201 → Q-005. 202 important — l'ordre est opt-in (`attach_order`), `SheetList` n'en hérite pas, jamais d'élagage dans `set_entries` (filtre de l'onglet Python, brouillons `<new>`).
- 203 important — forme des signaux : `dropEvent` calcule `(ids, group, before)` en remontant `SheetList.drop_on` dans la base ; `moved(ids, group)` seulement pour les ids qui changent de dossier (signature inchangée), `reordered()` sinon ; un ordre seul ne réécrit aucune source et n'exporte pas.
- 204 → D-16. 206 important — `source_archive.Actions` reçoit un *backend* (JSON par défaut, `.typ` pour Formules), pas de clone ; `fd.remove` gagne la boucle anti-collision.
- 207 → Q-010. 208 important — `rename/forget/insert_after` du magasin ; câblés pour Formules et Schémas ; prix accepté pour les autres onglets : un id renommé va en fin de liste.
- 209 important — `FormulaTab.list` devient le `GroupedList` (contrat `rows()` de `test_window`) ; commandes en `children` aux ids composés `<id>#<n>`, jamais marquées ; `update_list_marker` après chaque `set_entries`.
- 210 mineur — sept copies du câblage des onglets : pas de huitième (deux lignes par onglet).
- 211 mineur → D-14, dit dans `window.md`. 212 mineur — couleurs par `theme.colour`. 213 mineur — onglet Python : un ordre seul ne change jamais de dossier.
- 214 — concurrence : `project.py`, `woodcore_gui.py`, `schema_tab.py`, `statics_tab.py`, `python_tab.py`, `archive_export.py`, `tests/conftest.py` sont modifiés non commités par d'autres sessions : éditions ciblées, prévenir avant.

**Exigence ajoutée par la revue.**

### ARCH-004 — Contrats changés et commande élargie
- **Exigence** : `formulas.json` passe en `schema_version` 2.0 (clé = id, champ `title`) ; `var-domain` gagne `title:` facultatif, documenté (`///`, deux exemples qui compilent, `commands.json` fr/de/en) ; `schemas/lists.schema.json` (format `woodcore-lists`, 1.0).
- **Source** : revue (ARCH-RISK-112, 201–204), Q-006
- **Critère d'acceptation** : `test_commands`, `test_display_view`, `test_formula_domain` (refus nommant le champ) verts ; `build_examples` compile les exemples de `var-domain`.

## 14. Plan d'implémentation

1. **Bugs du bloc** — `formula_tab.py` : `Block` à un conteneur par mode (REQ-001) ; `eq` rouvert avec `shown_symbol` (REQ-002). Tests `test_formula_tab` (fantôme avec `DeferredDelete`, aller-retour octet pour octet).
2. **Typst : `#include`, `title:`** — `lib/formula.typ` : retrait de `show-formula`, `formula-block`, `block-level`, `line-level(kind:)` ; `var-domain(name, title: none, body)` imprime le titre au niveau courant + 1 ; `build_reference` (CATEGORIES, SAMPLE_FOR, samples), `display_options` (SPECS, DISMISSED), `commands.json` (retrait + `title`), exemples `show-formula-*` retirés, deux exemples de `var-domain` ; `test_units` reste vert (REQ-005, ARCH-004).
3. **Domaine sans Qt** — `formula_domain.py` : `id = stem`, `title` lu/écrit, argument ≠ nom → `hand_edited` ; item `text` + segmenteur `_Lexer` + refus + relecture en mémoire (REQ-006) ; `rename` (avec liste des citations, D-11), `duplicate`, archive/restaure en backend `.typ` (anti-collision) ; `compute` aligné ; `resolve_import`/`variable_domains` par id ; index 2.0 ; code mort retiré (ARCH-002, REQ-004, REQ-010). Tests `test_formula_domain`, `test_variable_sources`.
4. **Noyau de liste** — `calc/list_order.py` (Qt-free, `lists.schema.json`, `Project.lists_file` = `Woodcore-Datei/lists.json`, écriture atomique réutilisée) ; `grouped_list.py` : `attach_order`, `drop_on` remonté de `SheetList`, `reordered`, `moved` restreint ; `source_archive.Actions(backend=…)` ; `app.save_list_order` gardé en lecture seule ; `conftest.project_copy` copie `lists.json` (ARCH-001, ARCH-003, REQ-008). Tests `test_list_order` (nouveau), `test_groups`.
5. **Onglets JSON** — `attach_order` + `reordered` dans Schémas (avec `rename` à l'enregistrement), Statique, Connecteurs, Vérifications, Plans, moments polaires, Python (ordre seul, jamais de changement de dossier) (REQ-008). Test de réordonnancement dans `test_schema*`.
6. **Onglet Formules** — `GroupedList` à la place du `QTreeWidget` (dossiers, archives, duplication, ordre, groupes dans `lists.json`) ; options au clic simple, palette et options visibles, volet défilant, écriture différée (REQ-003) ; zones de texte (REQ-006) ; filtre de clic (REQ-007) ; champ ID et ses refus traduits (REQ-004) ; Affichage = `#include` ; titres « Formules/Formeln/Formulas » et chaînes réécrites (UI-001, UI-002) ; `WRITERS` complété. Tests `test_formula_tab` (QTest.mouseClick), `test_window`, `test_i18n`.
7. **Documentation** — `window.md` (onglet + §10quater), `formulas.md`, `layout.md`, `data-contracts.md`, `principles.md` (mentions), `testing.md`, `decisions.md` (REVERSING de l'entrée v0.117 et des D-02/D-09/D-11/D-12/D-15 de la spec v0.117 ; D-09, D-10, D-16 ici), `CHANGELOG.md` et « Nouveautés » 0.117.0 fr/de/en réécrits (D-15).
8. **Tests** — `python tests/run_tests.py` sur `formula`, `units`, `groups`, `list_order`, `schema`, `variable`, `commands`, `display_view`, `window`, `i18n`, `project`, puis la suite entière.

## 15. Vérification

Deux tours du vérificateur indépendant (`requirements-verifier`, Sonnet), 2026-10-08/09, sur l'arbre de travail contre HEAD b462466.

**Tour 1** — 0 ❌, 7 ⚠️ de preuve : hauteur du bloc validé non comparée (REQ-001) ; clic simple prouvé sur `var` et `eq` seulement (REQ-003) ; dossier et place suivant un ID renommé non prouvés dans l'onglet (REQ-004) ; `#include` compilé sans preuve qu'il imprime les blocs (REQ-005) ; ordre non relu après reconstruction, drop refusé silencieux (REQ-008) ; renommage d'un dossier de *Formules* et dossier `archives/` non testés (REQ-009) ; deux docstrings nommant encore `#show-formula`. Tous corrigés : assertions et tests ajoutés, `Store.save` redit la raison à chaque refus, docstrings réécrites.

**Tour 2** — 0 ❌, aucun régression ; un défaut réel relevé (REQ-003 : une option changée puis un autre bloc choisi ou le domaine quitté en moins de 400 ms était perdue) — corrigé (`write_options` avant d'arrêter la minuterie et dans `confirm_leave`) et prouvé par test ; la relecture octet pour octet du domaine d'exemple devenue un test. Réserves acceptées : le clic simple est prouvé par `mousePressEvent` et non `QTest.mouseClick` (REQ-007 l'est) ; l'avertissement d'un `lists.json` mal formé est en anglais, comme toute `ValidationError` d'un fichier (règle du projet : un défaut de fichier reste anglais).

| Élément | Verdict | Preuve (fichier:ligne, test, sortie) |
|---|---|---|
| REQ-001 | ✅ | `formula_tab.py` `Block.clear` (conteneur remplacé entier) ; `test_a_block_validated_leaves_no_ghost_of_its_fields_and_an_equation_reopened_keeps_its_name` (aucun champ après DeferredDelete, hauteur = bloc relu, rien ne s'accumule) |
| REQ-002 | ✅ | `show_editor` `c.shown_symbol` pour `eq` ; même test (champ `M_d`, fichier identique) |
| REQ-003 | ✅ | `on_block_chosen`, `write_options`, `option_timer` ; `test_a_single_click_on_a_block_validated_shows_its_options_and_writes_them` (les cinq commandes, `label` écrit, écrit aussi au changement de bloc et à `confirm_leave`) |
| REQ-004 | ✅ | `formula_domain.check_id/rename/cited_by`, `formula_tab.id_done/rename_id` ; `test_an_id_changed_renames_the_file_and_one_that_is_no_id_is_refused` (dossier et place suivent), `test_a_domain_is_named_on_its_first_line_its_id_made_from_it_and_written_on_enter`, `test_an_id_changed_renames_the_file_and_lists_what_cites_the_old_one` |
| REQ-005 | ✅ | `lib/formula.typ` sans `show-formula`/`formula-block`/`block-level` ; `test_include_prints_the_domain_with_its_title_and_val_reads_it_by_its_id` (page identique au corps écrit à la main) ; Affichage copie `#include` ; mentions restantes historiques seulement (CHANGELOG, decisions REVERSING, commentaires d'histoire) |
| REQ-006 | ✅ | `TextZone`, `split_items`/`check_text`/`check_body` ; `test_typst_of_one_s_own_is_written_between_the_blocks_and_a_command_goes_where_the_cursor_stands`, `test_text_between_the_commands_reads_back_as_typed_and_is_never_computed`, `test_what_a_text_may_not_hold_is_refused_and_nothing_is_written`, `test_the_example_project_s_domain_reads_back_to_its_own_bytes` |
| REQ-007 | ✅ | `_ClickOutside`, `pressed_on` ; `test_a_click_elsewhere_in_the_middle_validates_the_block_being_written` (`QTest.mouseClick`) |
| REQ-008 | ✅ | `calc/list_order.py`, `GroupedList.attach_order/drop_ids/reordered`, sept onglets branchés ; `test_list_order` (8), `test_groups` (+4), `test_schema_tab.test_the_list_takes_the_order_dropped_…`, `test_folders_order_duplicate_and_archives_without_a_directory` (relu par une liste neuve) |
| REQ-009 | ✅ | `ArchiveBackend`, `duplicate`, dossiers par `set_group` ; `test_folders_order_duplicate_and_archives_without_a_directory` (dossier créé, renommé, `.typ` à plat, duplicata, `Formules/archives/`, restauration), `test_a_domain_is_duplicated_archived_without_overwriting_and_restored` |
| REQ-010 | ✅ | `formula_domain.save` → `export` ; `test_the_index_is_rewritten_at_every_save_and_lists_the_domain_under_its_id`, `test_variable_sources` (16) |
| UI-001 | ✅ | `test_the_tab_is_first_in_reference_in_three_languages_with_its_icon` ; `test_i18n` (21) |
| UI-002 | ✅ | mêmes clés fr/de/en, aucune chaîne `show-formula` (même test) |
| ARCH-001 | ✅ | `FormulaTab.list` est le `GroupedList` ; `insertion` remontée de `SheetList` ; `test_groups` (26) |
| ARCH-002 | ✅ | `test_the_domain_modules_import_without_qt`, `test_list_order.test_the_module_imports_without_qt` |
| ARCH-003 | ✅ | `schemas/lists.schema.json` 1.0 ; `test_the_file_is_checked_and_its_refusals_name_the_field` |
| ARCH-004 | ✅ | `var-domain(title:)` (`///`, trois exemples, `commands.json`) ; `formulas` 2.0 ; `test_commands` (34), `test_display_view` (13) |
| CON-001…005 | ✅ | éditions ciblées, coordination avec les sessions v0.117 et #9 ; `test_units` vert ; `hand_edited`/`unreadable` gardés ; REVERSING dans `decisions.md` ; documentation (voir §11) |
| §8 | ✅ | les autres onglets n'ont gagné que l'ordre ; *Variables* non refait |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-08 | draft | spécification extraite de l'issue #15 (corps + deux commentaires) ; la session v0.117 a cédé l'issue ; 4 questions |
| 2026-10-08 | specified | Q-001 à Q-004 répondues (tout bloc ; tout par l'id ; dossier dans le fichier d'ordre ; index gardé) ; REQ-010 ajoutée |
| 2026-10-08 | reviewed | deux revues d'architecture (APPROUVER AVEC RÉSERVES) ; Q-005 à Q-011 répondues ; ARCH-004 ajoutée ; plan §14 |
| 2026-10-08 | approved | plan approuvé par l'ingénieur (« Approuver et implémenter ») |
| 2026-10-08 | implementation | étape 1 faite : Block à un conteneur par mode (fantôme), eq rouvert avec shown_symbol, minuterie du focus liée au champ ; test_formula_tab vert (REQ-001, REQ-002) |
| 2026-10-08 | implementation | étape 2 faite : lib/formula.typ sans show-formula/formula-block/block-level/line-level(kind:), var-domain(title:) imprimé au niveau +1, commands.json, build_reference, display_options, build_examples (384 exemples rendus) ; étape 3 faite : formula_domain (id = nom de fichier, title, items text + segmenteur _Lexer + refus + relecture, rename/cited_by, duplicate, archived/restore/purge, index 2.0, resolve_import et variable_domains par id), schéma formulas 2.0, domaine d exemple ; test_formula_domain (17), test_units, test_variable_sources verts (REQ-005, REQ-006 domaine, REQ-004 domaine, REQ-010, ARCH-002, ARCH-004) |
| 2026-10-08 | implementation | étape 4 faite : calc/list_order.py + schemas/lists.schema.json + Project.lists_file (Woodcore-Datei/lists.json) + archive_export + conftest ; grouped_list attach_order/insertion/drop_ids/reordered, moved restreint, dossiers gardés pour groups=True ; SheetList lit insertion ; source_archive.Actions(backend=JsonSources) ; formula_domain.ArchiveBackend ; app.list_store gardé en lecture seule, WRITERS complétés ; test_list_order (8), test_groups (26), tests de feuilles (86) verts (ARCH-001, ARCH-003, REQ-008 noyau) |
| 2026-10-08 | implementation | étape 5 faite : attach_order + reordered dans Schémas (rename du magasin à l enregistrement), Statique, Connecteurs, Vérifications, Plans/Plans feu, moments polaires, Python (regroup=False) ; test_schema_tab (43) vert (REQ-008) |
| 2026-10-08 | testing | étape 6 faite : formula_tab réécrit -- GroupedList (dossiers, ordre, Archives par ArchiveBackend, duplication), volet droit en une colonne (variables, options, carte du domaine avec ID, commandes), options au clic simple écrites en différé, zones de texte TypstHighlighter dans chaque intervalle et commande insérée au curseur, filtre de clic qui valide, champ ID (rename_id + citations listées), Affichage = #include, mots fr/de/en ; test_formula_tab (15) vert (REQ-001 à REQ-010, UI-001, UI-002) |
| 2026-10-08 | testing | étape 7 faite : window.md (onglet Formules, ordre du §10quater), formulas.md (#include, id, title, texte), layout.md, principles.md, data-contracts.md, testing.md, open-questions.md, member-checks.md, decisions.md (deux entrées dont un REVERSING), CHANGELOG (entrée issue #15), Nouveautés 0.117.0 fr/de/en réécrites, commentaires de code périmés |
| 2026-10-08 | verification | test_commands rendu vert (code cité identique dans les traductions de var-domain) ; suite complète lancée ; vérification indépendante, tour 1 |
| 2026-10-08 | verification | tour 1 : 0 ❌, 7 ⚠️ de preuve (hauteur du bloc, clic simple sur verify/val/var-unit, dossier et place suivant un ID renommé, #include comparé au corps écrit à la main, rechargement de l ordre, refus de drop dit à chaque fois, renommage de dossier, dossier archives) et deux docstrings périmées : tous corrigés, tests relancés verts ; tour 2 lancé |
| 2026-10-09 | verification | tour 2 : 0 ❌ ; option perdue en moins de 400 ms corrigée et testée, relecture du domaine d exemple testée ; test_formula_tab (15), test_formula_domain (18) verts |
| 2026-10-09 | completed | suite complète : 7 échecs, dont 5 à moi dus à des éditions pendant le passage (test_formula_tab, test_list_order -- une fuite de lists.json entre tests corrigée), verts relancés seuls ; test_object_panes et test_plan_tab_rework verts seuls ; test_panes.test_the_bar_wraps_and_loses_no_tool rouge seul, barre d outils du plan de positions (issue #9), signalé à sa session ; spec déplacée dans completed/ |
