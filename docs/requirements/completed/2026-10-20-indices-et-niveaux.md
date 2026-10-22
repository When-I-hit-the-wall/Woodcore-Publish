---
id: 2026-10-20-indices-et-niveaux
titre: Indices et niveaux — une seule écriture des indices, le niveau de chaque ligne décidé par Typst, un niveau pour chaque commande qui imprime
status: completed
cree: 2026-10-20
mis_a_jour: 2026-10-21
source: spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md (§2 T9, T13, T14 ; §10 Q-004, Q-007, Q-012, Q-017, Q-018 ; §13 ARCH-RISK-403, 404, 407, 408, 412 ; §15), et le message de la session qui a lancé ce travail (20.10.2026)
docs: [docs/typst/formulas.md, docs/typst/report-engine.md, docs/typst/api-conventions.md, docs/typst/command-docs.md, docs/architecture/data-contracts.md, docs/architecture/principles.md, docs/conventions/testing.md, docs/decisions.md]
---

# Indices et niveaux — Spécification

## 1. Objectif

Terminer ce que la spec « base saine » (2026-10-19) a reporté exprès, parce que cela change chaque formule et chaque commande imprimées : 
- un indice s'imprime d'une seule façon partout (Q-004) ;
- le niveau de chaque ligne de calcul est décidé par Typst, à partir d'une table, et non plus figé par Python à l'export (D-09) ;
- chaque commande qui imprime prend `level:`, avec le sens de Q-012.

Les exemples et le site sont figés une seule fois, à la fin. Les restes ⚠️ que le vérificateur a laissés aux lots 1 à 8, ainsi que deux questions ouvertes (citer VKF 15-15 pour une durée feu, ce que cite un résultat de script), sont soumis à l'ingénieur.

## 2. Source

Les mots de l'ingénieur, cités de la spec « base saine » (§2, mot pour mot) :

> **T1** — « Affichage des formules, divergences d'un onglet à l'autre : unifie l'affichage des indices. » (base saine T9)
>
> **T2** — « Niveau de détail: corrige (décié par la commande). » (base saine T13)
>
> **T3** — « Commandes sans niveau: corrige, il faut des niveaux pour toutes les commandes. » (base saine T14)

Ses réponses aux questions de la spec « base saine » (§10, telles qu'elles y sont consignées) :

> **T4** — Q-004 : « **A** — indices descriptifs droits, sous la forme de la norme (ISO 80000-2) ; un indice qui est une variable reste italique (l'ingénieur, 19.10.2026). »
>
> **T5** — Q-007 : « **A** — les commandes qui impriment (`show-*`, `verify-*`, `distance`, `doc-*`, `sheet-*`) ; pas les accesseurs (l'ingénieur, 19.10.2026). »
>
> **T6** — Q-012 : « **A** — `decisions.md:131` et `:479` sont renversées par une nouvelle décision (l'ingénieur, 19.10.2026). » Option A : « 1 dessin seul, 2 + légende et titres, 3 + cotes, sources, citations ».

Le message de la session qui a lancé ce travail (mot pour mot, en anglais) :

> **T7** — « UI-001 — subscripts printed one way everywhere (Q-004: descriptive subscripts upright, «forme de la norme»; a variable subscript italic): a JSON classification table, one Python symbol builder, one Typst normaliser applied where symbols and formulas are evaluated (render-symbol, render-formula, eq, var…), the twin calc/typst_math.py, a markup parity test. The classification (which subscripts are variables: x? i? y in f_m,y,d?) is the engineer's to decide — ask him with options grounded in SIA 263/265 usage. »
>
> **T8** — « UI-005 — the level of each line decided by Typst from a table `domain → key → level` (model: lib/shown-variables.json), read by Python and Typst; `level` optional in the exports (new schema_version for calculations/steel/connectors, old read, priority rule written); a test per domain that levels 1/2/3 print differently. »
>
> **T9** — « UI-006 — `level:` on every command that prints (show-*, verify-*, distance, doc-*, sheet-*), meaning per Q-012 (1 the figure/table alone, 2 + legend and titles, 3 + dimensions, sources, citations), a NO_LEVEL registry for accessors tested both ways, typst_objects_parse.SIGNATURES and display_options updated, -L1/-L3 examples, translations in calc/i18n/commands.json; reverse docs/decisions.md lines ~131 and ~479 with a new decision. »
>
> **T10** — « The one-time examples freeze (`build_examples --freeze`, -L1/-L3 pages, site). »
>
> **T11** — « Optionally, the verifier's ⚠️ left by lots 1–8 (spec §15): ARCH-001 remaining per-tab copies (confirm_leave, update_list_marker, reload_list, on_list_change, on_moved), ARCH-004 D4/D6 duplicates (schema_geometry/statics_geometry fmt_number, typed_point, dimension_*, nearest_ray; the *_svg `_text`/`_unit` wrappers), ARCH-002 member_check rows as engine lines, REQ-003 c_pe/c_pi and μ still read from the workbook's cells — propose to the engineer which to include. »
>
> **T12** — « Also put the open questions Q-017 (citing VKF 15-15 for a fire duration it requires: a key on #member's fire:) and Q-018 (what a script's result cites) to the engineer. »

## 3. Exigences fonctionnelles

### REQ-001 — Une durée feu exigée par VKF 15-15 cite VKF 15-15
- **Exigence** : Woodcore doit citer VKF 15-15 pour la durée `t_fi` d'une vérification au feu quand c'est VKF 15-15 qui l'exige (durée non écrite dans la vérification, lue du bâtiment du projet, `duration_from == "vkf"`). L'export du contrôle porte un champ additif `fire.required: {norm, norm_ref} | null`, composé une seule fois en Python (`"Tabelle " + table`, la table venant de `fire.requirement`) ; `#member` prend dans `fire:` une clé facultative `required: (norm:, norm-ref:)` que `#show-check-member` recopie de l'export sans la recalculer ; la ligne `t_fi` cite cette référence dans le rapport (`timber.typ:445`) et dans la fenêtre (`member_check.py:841`). Une durée écrite par l'ingénieur garde SIA 265 4.5.2 (Q-004).
- **Source** : T12
- **Priorité** : doit
- **Critère d'acceptation** : une vérification feu sans durée, sur un bâtiment dont VKF 15-15 exige une durée, imprime `t_fi` cité « VKF 15-15, Tabelle n » dans le rapport et dans la fenêtre ; avec une durée écrite, SIA 265 4.5.2 ; `_held_equal` compare aussi la norme de chaque ligne ; `checks` monte de version (champ additif, anciennes versions lues) ; `fire:` de `#member` documenté (`///`, deux exemples, traductions fr/de).

### REQ-002 — Ce que cite un résultat de script
- **Exigence** : Woodcore doit citer, pour un résultat de script sans `norm=`, le script et la ligne de son `result(...)` dans la colonne de droite (« script `<id>.py`, l. N ») ; un résultat qui donne `norm=` cite sa norme comme aujourd'hui (Q-005). La ligne est connue dans `result()` (`script_runner.py`) par le cadre d'appel dont le fichier est le script, même quand `result()` est appelé depuis une fonction. L'export porte un champ additif `line` (jamais dans `norm`, que `_check_citation` et `bib-note` lisent comme un document) ; `scripts` passe de 1.0 à 1.1, 1.0 toujours lu ; `norm-text` gagne la branche qui imprime la ligne.
- **Source** : T12
- **Priorité** : doit
- **Critère d'acceptation** : `test_script` : un résultat sans norme exporte la ligne de son appel (aussi depuis une fonction du script) et le rapport imprime « script `<id>.py`, l. N » ; avec `norm=`, la norme ; les mots du glossaire existent en fr, de, en (`test_i18n`) ; `docs/domain/scripts.md` le dit.

## 4. Exigences d'interface (rapport, fenêtre, site)

### UI-001 — Un indice s'imprime d'une seule façon
- **Exigence** : Woodcore doit imprimer chaque indice selon une seule règle, dans le rapport (toutes les commandes), dans la fenêtre et sur les figures : **tout indice est droit** — lettres, chiffres et lettres grecques —, sous la forme de la norme : ses parties séparées par des virgules sans espace, des lettres qui se suivent formant un mot (`N_Rd`, `γ_M1`, `f_m,y,d`, `E_0,05`, `f_c,α,d`). Aucun indice n'est traité comme une variable (Q-001 C). Le symbole principal (avant `_`) garde la typographie de Typst ; les opérateurs à bornes (`sum`, `product`, `integral`, `lim`, `max`, `min`) gardent les leurs.
- **Source** : T1, T4, T7
- **Langues** : sans objet (notation)
- **Critère d'acceptation** :
  - `N_Rd`, `N_Ed`, `γ_M1`, `f_m,y,d` produisent le même balisage dans `show-calc`, `show-check-steel`, `show-connector-resistance`, `verify-*`, `#var`, `#eq` et `#val`, qu'ils soient écrits `N_(R d)`, `N_"Rd"`, `N_Rd` (clé), `N_(Rd)`, `gamma_(M 1)` ou `gamma_M1` ;
  - la fenêtre (`typst_math.to_html`) et les figures (`to_figure`) impriment le même indice (`M1`, et non `M 1`) ;
  - un test compare la forme normalisée produite par Typst et par Python sur tous les symboles et formules de `calc/domains/`, de `lib/` et des exports du projet exemple ; la normalisation est idempotente ;
  - les gardes d'octets touchées (`test_figure_golden`, `test_unfold`, exemples) sont refigées une fois, la raison écrite dans leur carte.

### UI-002 — Le niveau de chaque ligne décidé par Typst, à partir d'une table
- **Exigence** : Woodcore doit décider au moment de l'impression le niveau de chaque ligne (var, step, check) d'un calcul exporté par les domaines neige, vent, poids propre, charges utiles, acier et script, en lisant une seule table `lib/line-levels.json` ; le bois (`lib/timber.typ`) lit la même table au lieu de ses niveaux littéraux. Python n'écrit plus de niveau de ligne dans ces exports (Q-008).
  - Les connecteurs et les assemblages n'entrent pas dans la table : `show-connector-resistance` et `show-polar-moment` décident déjà par des seuils écrits en Typst et ne lisent jamais le niveau de leurs lignes (ARCH-RISK-603). Leurs exports cessent d'écrire `level`, leurs ~70 littéraux disparaissent.
  - Les tableaux et figures exportés gardent leur propre `level` : ce sont des objets, pas des lignes, et leur ordre dépend du calcul (ARCH-RISK-604). Exception nommée par le test.
- **Source** : T2, T8
- **Langues** : sans objet
- **Critère d'acceptation** :
  - aucun niveau de ligne littéral (`level=` ni `"level":`) dans `calc/domains/` (test AST ; liste blanche nommée : `unfold.py`, qui écrit dans un fichier Typst, et les tableaux et figures) ;
  - avant que Python cesse d'écrire, un test vérifie table = niveau exporté pour chaque clé (lot de transition) ;
  - **à niveau égal (1, 2, 3 et uniformes), les pages du rapport du projet exemple sont identiques à l'octet** à la référence prise après le lot des indices ;
  - pour chaque domaine tenu par la table, un test imprime un calcul aux niveaux 1, 2, 3 : chaque niveau contient le précédent et au moins deux diffèrent (un script utilisateur, qui n'a que le défaut du domaine, est testé avec une ligne au niveau 3).

### UI-003 — Chaque commande qui imprime prend `level:`
- **Exigence** : Woodcore doit donner `level:` (auto, 1, 2, 3 ; 0 où il existe déjà) à chaque commande qui imprime une figure, un tableau ou une liste (`show-*`, `distance`, les `doc-*` et `sheet-*` de figure et de tableau, hors `NO_LEVEL` ci-dessous), avec ce sens (Q-012, Q-002 révisée) :
  - **niveau 2 = aujourd'hui** : rien de ce qu'un document imprime au niveau 2 ne change ;
  - **niveau 1** : la figure ou le tableau seul — sans légende, titre (`caption`, `title`), notes, échelle, ni ce que le moteur ajoute au dessin (longueurs des barres, centres) ; les cotes que l'ingénieur a dessinées restent (elles sont le dessin) ;
  - **niveau 3** : le niveau 2 plus les sources et les citations là où la commande en a (document d'un extrait et sa page, norme et clause d'une ligne de résumé, table de norme de `distance`…) ; une commande qui n'en a pas imprime au niveau 3 ce qu'elle imprime au niveau 2, et est inscrite dans un registre « niveaux confondus » avec sa raison.
  Un argument écrit (`legend: false`, `caption: none`, `scale-bar: true`…) l'emporte sur le niveau, comme le `level:` d'un appel l'emporte sur celui du rapport : les défauts concernés passent de `true` à `auto`. Une feuille (`sheet()`) imprime au niveau 2 sauf `--input level=` (ARCH-RISK-608).
  - **`NO_LEVEL`** : les accesseurs (`get`, `ids`, `find`, `fmt-*`, `t`, `tl`, `t-str`…) et les commandes qui impriment ce que l'ingénieur a écrit, complet ou faux : `doc-field`, `doc-value`, `doc-choice`, `doc-checklist`, `doc-signatures`, `sheet-text`, `sheet-titleblock`, `sheet-section` (Q-003 révisée), et `doc-table`, `live-load-table`, `dead-load-table`, `doc-image` (Q-009, D-16), chacun avec sa raison.
  - Les calculs (`show-calc`, `verify-*`, `show-check-*`…) ont déjà leurs niveaux et ne changent pas de sens ; `show-connector` et `show-check`, qui acceptent `level:` sans s'en servir, passent sous la même règle (sens défini, ou « niveaux confondus » avec raison).
- **Source** : T3, T5, T6, T9
- **Langues** : fr / de / en — l'argument `level` de chaque commande et chaque argument dont le défaut devient `auto` sont traduits dans `calc/i18n/commands.json`
- **Critère d'acceptation** :
  - un test parcourt les commandes publiques de `lib/` (`build_reference_lib.CATEGORIES`) : chacune prend `level:` ou figure dans `NO_LEVEL` avec sa raison, jamais les deux ; `NO_LEVEL` et « niveaux confondus » ne nomment que des commandes existantes ;
  - **au niveau 2, chaque document du projet exemple et une feuille témoin s'impriment à l'octet comme avant ce lot** ;
  - chaque commande qui prend `level:` a un exemple `-L1` et un exemple `-L3` qui compilent ; ses niveaux 1 et 2 diffèrent, et ses niveaux 2 et 3 diffèrent sauf si elle est inscrite dans « niveaux confondus » ;
  - `distance`, `show-plan`, `show-fire-plan` (cités par l'audit) en font partie ; un `legend: true` écrit dans une section compile comme avant.

### UI-004 — Le gel unique des exemples
- **Exigence** : Woodcore doit régénérer une seule fois, à la fin, les exemples de la référence des commandes (`build_examples --freeze`) avec leurs pages `-L1` et `-L3` (~128 nouvelles), et le site qui les montre (construit localement, non publié).
- **Source** : T10 (ARCH-RISK-412 de la base saine)
- **Langues** : fr / de / en (pages du site)
- **Critère d'acceptation** : `examples/` contient un `-L1` et un `-L3` pour chaque commande qui prend `level:` ; `test_commands` et le test du site sont verts ; le gel est fait au dernier lot, une seule fois.

## 5. Exigences d'architecture

### ARCH-001 — Une règle exécutable pour les indices
- **Exigence** :
  - une feuille `lib/subscript.typ`, sans import de `lib/`, importée par `calc-engine-core.typ` comme `number.typ` (ARCH-RISK-501) : le lexeur de `formula.typ:530-617` (`math-names`, `skip-quoted`, `skip-code`, `read-name`…) y est **déplacé**, et le normaliseur y est écrit, en un seul passage `str.replace(regex, fonction)`, avec un chemin court pour une source sans `_` (ARCH-RISK-506) ; ses noms sont préfixés, la façade ré-exportant tout ;
  - **forme canonique** (mesurée par compilation le 20.10.2026) : un indice fait de lettres, de chiffres, de noms grecs, de virgules et d'espaces devient un seul bloc cité, les espaces entre lettres retirés et les lettres grecques écrites en Unicode (`N_(R d)` → `N_"Rd"`, `f_(c,alpha,d)` → `f_"c,α,d"`, `E_(0,05)` → `E_"0,05"`) : droit, virgules serrées, gras conservé, idempotent ; un indice qui contient autre chose (opérateur, indice ou exposant imbriqué, appel) garde sa structure, chacun de ses mots étant cité ; un indice purement numérique (`mu_11`) ne change pas ;
  - un seul `math-eval(src)` remplace les ~25 `eval(…, mode: "math")` de symboles et de formules (`render-symbol`, `render-formula`, les lignes de `show-calc`, `#var`, `#eq`, `#val`, `verify-core`, connexions) ; `quoted-words`, `symbol-word` et `key-symbol` s'appuient sur lui (`M2` reste `M 2` comme symbole principal, `atom-symbol` en dépend) ;
  - **les données ne sont pas réécrites** (ARCH-RISK-502) : exports et fichiers `Formules/<id>.typ` gardent l'écriture de leur auteur ; Typst normalise à l'évaluation, et c'est la source de vérité ;
  - son jumeau Python `typst_math.normalise` sert la fenêtre et les figures (`_render`) ; `shown_variables.key_math` et la chirurgie de `member_check.py:876` passent par lui (ARCH-RISK-508) ;
  - **pas de table de classification** : Q-001 C ne laisse aucun indice-variable ; la table naîtra le jour où un indice-variable sera voulu.
- **Source** : T7 (ARCH-RISK-407), Q-001, revue (ARCH-RISK-501 à 508)
- **Critère d'acceptation** : `tests/test_subscripts.py` — parité Typst/Python sur tous les symboles et formules du projet exemple, des domaines et de `lib/`, idempotence, cas limites (opérateurs à bornes, imbriqués, `E_0,05`, gras) ; un test greppe `lib/` : aucun `eval(…, mode: "math")` hors de `math-eval` ; le surcoût de compilation du rapport du projet exemple au niveau 3 uniforme reste sous 5 % (`docs/architecture/performance.md`).

### ARCH-002 — Le niveau des lignes : un contrat de données
- **Exigence** :
  - **la table** `lib/line-levels.json`, sur le modèle de `lib/shown-variables.json` (dans `project.ENGINE_FILES`, lue par Typst et par `calc/line_levels.py`), dit pour chaque domaine le niveau de chaque clé, avec :
    - un niveau distinct pour la variable et pour l'étape d'une même clé (`h_ref`, `s_k` de la neige : variable 2, étape 3 — ARCH-RISK-601) ;
    - un niveau par genre de vérification pour l'acier (`N_Rd` 1 en traction et compression, 2 en flexion avec interaction) ;
    - des motifs pour les familles indexées (`mu_{n}`, `q_k{n}`… — ARCH-RISK-602) ;
    - un défaut `"*"` réservé au script, dont les clés sont celles de l'ingénieur ; un domaine à défaut seul n'est pas contrôlé à l'export ;
  - **engine** : `level` devient un argument nommé facultatif de `var`, `step` et `check` (~175 appels adaptés) ; les lecteurs Python du niveau lisent la table (`build_reference.py:645-668`, `variable_sources.py:80`, `variables_tab.py:1041`) ; `steel_resistance.py:88` choisit ses résultats par un marqueur et non par leur niveau (ARCH-RISK-606) ;
  - **versions** : `level` facultatif dans les lignes : `calculations` 1.8, `steel` 1.2, `connectors` 3.3, `connections` 4.4, `scripts` 1.1 (avec le `line` de REQ-002) ; chaque nouvelle version contient la précédente (1.8 ⊇ 1.7 : liens et chemins depuis la racine admis), elle est écrite par tout export, et les anciennes sont toujours lues (ARCH-RISK-605) ;
  - **règle de priorité**, écrite dans `docs/typst/report-engine.md` §4 :
    1. le niveau forcé (`uniform`), sinon le `level:` de l'appel, sinon celui du rapport, fixe le niveau de la commande ;
    2. le niveau d'une ligne est celui de la table (domaine, genre, clé, rôle var/step/check) ;
    3. à défaut, celui que la ligne porte dans l'export (exports antérieurs, domaines écrits à la main) ;
    4. à défaut, le défaut `"*"` du domaine ;
    5. au niveau −1, celui que donne `shown:` ;
    6. une ligne qu'aucune source ne règle arrête le rapport en nommant le domaine et la clé (un défaut de Woodcore).
  - un export ancien est donc imprimé par la table actuelle ; CON-001 tient parce que la table reprend exactement les niveaux d'aujourd'hui (test).
- **Source** : T8 (ARCH-RISK-404), principes 1, 4, 8, revue (ARCH-RISK-601 à 606, 612)
- **Critère d'acceptation** : `tests/test_line_levels.py` — table = niveaux historiques pour chaque clé des exports figés (`examples/data/*.json`, projet exemple, fixtures des sources), avec et sans `level` retiré ; refus d'une clé inconnue d'un domaine tenu ; clés du bois égales à celles de `shown-variables.json` ; table dans `ENGINE_FILES` ; un export de chaque ancienne version imprime comme avant ; schémas et constantes de version à jour ; la parité du bois (`_held_equal`) reste verte.

### ARCH-003 — `NO_LEVEL`, signatures et options d'affichage
- **Exigence** :
  - chaque `level:` ajouté, et chaque défaut passé de `true` à `auto`, est reporté dans `calc/typst_objects_parse.py` (`SIGNATURES`, `SHEET_SIGNATURES`), dans les modèles d'objets (`typst_objects_models.py` : `_bool_value`, `set_legend`) et dans `calc/tools/display_options.py` : un réglage à trois états (auto / oui / non) pour ces arguments, `SPECS`, les deux `OWN_PANELS` écrits à la main (`show-plan`, `show-fire-plan`) ou `DISMISSED` avec sa raison (ARCH-RISK-609) ;
  - `build_reference_calls.call_command` n'écrit que ce qui diffère du défaut : `UNCHANGED` de `test_call_command` est réécrit pour `show-plan` et `show-fire-plan` ;
  - les registres `NO_LEVEL` et « niveaux confondus » vivent à côté de `build_reference_lib.CATEGORIES`, testés dans les deux sens.
- **Source** : T9 (ARCH-RISK-403), revue (ARCH-RISK-607, 609)
- **Critère d'acceptation** : `test_display_view` couvre chaque commande qui prend `level:` ; `test_typst_objects` relit les nouveaux arguments et un `level:` écrit à la main survit à l'aller-retour ; le test des registres d'UI-003.

### ARCH-004 — Géométrie et textes SVG sans double (Q-006)
- **Exigence** (revue C, ARCH-RISK-701 à 705) :
  - **géométrie** : les fonctions identiques de `schema_geometry` et `statics_geometry` (`typed_point`, `dimension_ends`, `dimension_direction`, `dimension_line`, `dimension_angle`, `nearest_ray`, `_midpoint` → `dimension.midpoint`) deviennent des noyaux paramétrés de `dimension.py` (le point d'ancrage, `same_point`, les décimales en paramètres) ; chaque module garde une enveloppe d'une à trois lignes, que les toiles et `schema.py`/`statics.py` appellent toujours ; pas de troisième module de géométrie (ARCH-RISK-305 de la base saine) ;
  - `fmt_number` (et `figure_number`) passent par une seule `number_text.plain(value, digits)` (garde non numérique + `trimmed`, `digits ≥ 1`), et non par `dimension.py`, qui ne connaît ni unité ni texte ; les enveloppes gardent `def fmt_number(value, digits=DIGITS)` (appelé avec un autre nombre de décimales) ;
  - `label_corners` (`schema_svg`, `statics_svg_layout`) et `plan_svg.number_corners` : une seule copie dans `dimension.py`, ré-exportée ;
  - **textes** : les `_text` minces de `schema_svg` et `statics_svg` deviennent des appels directs à `svg_text.draw` (octets identiques), et `connector_svg` cesse d'importer `statics_svg._text` ; les quatre `_text` qui recopient le dessin d'un texte (`plan_svg`, `connector_svg`, `dead_load_svg`, `snow_svg`) passent par une seule variante ancrée de `svg_text` qui garde leur ancre, leur ligne de base, leur rotation et leurs octets (D-15) ; leur échappement passe par `svg_draw.escape` (le texte de `snow_svg` n'était pas échappé) ;
  - **un seul `_unit`** dans `dimension.py`, le cas de deux points confondus tranché `(1, 0)` (D-15) ; `connection_svg._unit(degrees)`, qui est autre chose, ne change pas.
- **Source** : T11, revue (ARCH-RISK-701 à 705)
- **Critère d'acceptation** : `test_figure_golden` vert sans empreinte reprise (ou chaque reprise expliquée dans `CHANGES`) ; un test de parité `schema_geometry` / `statics_geometry` sur les mêmes sources, à l'unité près ; la liste de `test_no_duplicates` réduite d'autant ; `test_variables` (parité de `fmt_number`) vert.

### ARCH-005 — Copies par onglet : la partie sûre (Q-006, Q-007)
- **Exigence** :
  - les 4 `update_list_marker` identiques à la base (`schema_tab_draft.py:273`, `statics_tab.py:601`, `drawing_tab.py:517`, `polar_tab.py:1009`) et les 5 `NEW_ROW` redéfinis (`drawing_tab_panes.py:25`, `positions_tab.py:62`, `schema_tab_draft.py:24`, `statics_tab.py:79`, `POLAR_NEW_ROW`) sont supprimés ;
  - le `confirm_leave` de Schémas, Statique et Polaires remonte dans `SourceEditorTab` par un hook `discard` facultatif (les éditeurs qui n'en ont pas ne changent pas) ;
  - aucun changement de comportement ; aucun hook ne porte un nom de `WRITERS` ; pas de `super()` dans une méthode gardée (la garde l'envelopperait deux fois — ARCH-RISK-707, 708) ;
  - les redéfinitions qui restent (`reload_list`, `on_list_change`, `on_moved` des toiles ; `confirm_leave` du Journal, de Python, de Formule, du Plan, de Structure, de Variables ; `update_list_marker` des listes en arbre) gardent chacune sa raison en commentaire.
- **Source** : T11, Q-007, revue (ARCH-RISK-706 à 709)
- **Critère d'acceptation** : `tests/test_tab_overrides.py` — une table `PERMITTED = {(classe, méthode): raison}` ; toute redéfinition absente, ou dont le corps égale celui de la base aux noms près, échoue ; une entrée périmée échoue ; `test_window`, `test_tab_registry`, `test_schema_tab`, `test_polar_tab`, `test_plan_tab_rework`, `test_fire_tab`, `test_autosave`, `test_editor_buttons`, `test_i18n` verts.

## 6. Contraintes

- **CON-001** — (inféré, principe 8) Un export d'une version antérieure (calculations 1.4–1.7, steel 1.0–1.1, connectors 3.0–3.2, connections jusqu'à 4.3, scripts 1.0, checks antérieur) est toujours lu et imprimé comme aujourd'hui. Source : T8.
- **CON-002** — (inféré, choix de prudence, confirmé par Q-002 révisée) Au niveau 2, celui que les documents prennent par défaut (`--input level=2`), aucun rapport, document ni feuille existant ne change, **sauf l'écriture des indices** (UI-001, lot d'abord, référence refigée ensuite — ARCH-RISK-507). Ce que le niveau 1 retire et ce que le niveau 3 ajoute est nouveau. Source : T6, T9.
- **CON-003** — (inféré) Les gardes existantes restent vertes ou leur différence est expliquée : `test_figure_golden`, `test_unfold` (octets du projet exemple), la parité Python/Typst du bois (`_held_equal`), `test_number_text`, `test_export`. Une référence d'octets des pages du rapport (niveaux 1, 2, 3, uniformes) et d'une feuille témoin est figée au lot 0 (ARCH-RISK-611). Source : base saine §14, revue.
- **CON-004** — (inféré, CLAUDE.md) Chaque commande dont la signature change garde son bloc `///` à jour, deux exemples qui compilent et ses traductions fr/de dans `calc/i18n/commands.json`. Source : principe 14.
- **CON-005** — (inféré) Les décisions en vigueur `docs/decisions.md:137` (« les résumés sont trois commandes, sans niveau ») et `:485` (« un extrait n'a pas de niveaux ») sont renversées par une nouvelle décision au §13, qui dit pourquoi et ce que cela coûte, et cite celles qu'elle précise : `:84` (une cellule de tableau ne porte jamais de note), `:152` (la norme suit l'enregistrement), `:167` (les niveaux du journal). Les décisions `:245` et `:251` (`gamma_(M1)` = M italique et 1 ; `c_(pi)`) sont renversées par D-06. Les numéros 131 et 479 cités par la base saine sont périmés. Source : T6, revue (ARCH-RISK-504, 610).
- **CON-006** — (inféré) Les sections des projets qui écrivent aujourd'hui `legend: true`, `caption: …`, `dimensions: …` continuent de compiler à l'identique (un argument écrit l'emporte). Source : T9.

## 7. Décisions prises

- **D-01** — Indices descriptifs droits, sous la forme de la norme (Q-004 de la base saine, ISO 80000-2). *Constat* : SIA 265:2021 (§1.2 Notations) imprime elle-même tous ses indices en lettres en italique (Ed, Rd, mean, m,y,d), seuls les chiffres et les lettres grecques droits ; « la forme de la norme » désigne donc la forme (virgules, mots), non la typographie.
- **D-02** — Le niveau est décidé par la commande Typst (D-09 de la base saine), confirmé par Q-008.
- **D-03** — Les commandes qui impriment prennent `level:`, pas les accesseurs (Q-007 de la base saine).
- **D-04** — Sens des niveaux : 1 seul, 2 + légende et titres, 3 + sources et citations ; renverse `decisions.md:137` et `:485` (Q-012 de la base saine, D-18), précisé par D-07.
- **D-05** — Un seul gel des exemples et du site, au dernier lot (ARCH-RISK-412).
- **D-06** — Tout indice est droit, lettres grecques comprises ; aucun indice-variable (Q-001 C, l'ingénieur, 20.10.2026). Pas de table de classification.
- **D-07** — Figures et tableaux : niveau 2 = aujourd'hui ; niveau 1 le dessin ou le tableau seul (sans légende, titres, échelle, longueurs, centres ; les cotes dessinées restent) ; niveau 3 + sources et citations là où elles existent, sinon « niveaux confondus » avec sa raison (Q-002 révisée, l'ingénieur, 20.10.2026 ; remplace la première réponse, dont la question contenait une erreur).
- **D-08** — Formulaires (`doc-field`, `doc-value`, `doc-choice`, `doc-checklist`), signatures, texte posé, cartouche et coupe d'une feuille dans `NO_LEVEL` : ils impriment ce que l'ingénieur a écrit (Q-003 révisée, l'ingénieur, 20.10.2026).
- **D-09** — Une durée exigée par VKF 15-15 cite VKF 15-15 par une clé `required:` de `fire:` (Q-004 A, l'ingénieur, 20.10.2026).
- **D-10** — Un résultat de script sans norme cite son script et sa ligne (Q-005 A, l'ingénieur, 20.10.2026).
- **D-11** — Restes du vérificateur inclus : géométrie et SVG (ARCH-004), copies d'onglets (ARCH-005) ; laissés : les lignes du bois en lignes du moteur, le vent et la neige sans cellules calculées (Q-006, l'ingénieur, 20.10.2026).
- **D-12** — Copies d'onglets : la partie sûre seulement (Q-007, l'ingénieur, 20.10.2026).
- **D-13** — La table des niveaux est lue par Typst à l'impression ; `level` devient facultatif dans cinq exports, nouvelles versions de schéma (Q-008, l'ingénieur, 20.10.2026). Prix accepté : ~175 appels d'`engine`, cinq schémas, quatre lecteurs Python.
- **D-14** — (de mise en œuvre, revue A) Forme canonique d'un indice : un bloc cité, grec en Unicode ; les données ne sont pas réécrites, Typst normalise à l'évaluation ; normaliseur dans une feuille `lib/subscript.typ`.
- **D-15** — (de mise en œuvre, revue C) Les quatre `_text` recopiés passent par une variante ancrée de `svg_text` qui garde leurs octets ; un seul `_unit`, deux points confondus donnant `(1, 0)`.
- **D-16** — `doc-table`, `live-load-table`, `dead-load-table` et `doc-image` sans niveau, dans `NO_LEVEL` comme les formulaires : ils impriment ce que l'ingénieur a écrit (Q-009, l'ingénieur, 21.10.2026).
- **D-17** — Le lexeur de `formula.typ` reste dans `formula.typ` ; `key_math` et `_indices` restent, en amont de `typst_math.normalise` (Q-010, l'ingénieur, 21.10.2026).
- **D-18** — Le gel unique est fait au lot 5, après le dernier changement d'impression ; il tient lieu du gel « au dernier lot » de D-05 (Q-011, l'ingénieur, 21.10.2026).
- **D-19** — `show-annexes` et `doc-annexes` gardent leurs exemples ```` ```typ-dry ```` sans page -L1/-L3 ; leur preuve de niveau est un test qui les compile (Q-012, l'ingénieur, 21.10.2026).
- **D-20** — Un script n'écrit pas de niveau : ses résultats s'impriment à tout niveau, sa note dès 2 ; le critère « une ligne au niveau 3 » d'UI-002 tombe (Q-013, l'ingénieur, 21.10.2026).

## 8. Hors périmètre

- La typographie des exposants, des lettres grecques en position principale et des noms de fonctions (`max`, `min`) : seule celle des indices change.
- N1 (coefficients de l'acier en dur), N5, le moteur hors des projets, le graphe de dépendances (base saine §8, D-15).
- La publication (installeur, site en ligne, push) : elle attend la parole de l'ingénieur.
- Les lignes du bois en lignes du moteur (base saine ARCH-002, C1 : `member_check._row`, 99 appels) et le vent et la neige sans cellules calculées du classeur (base saine REQ-003) : non retenus (Q-006) ; ils restent ⚠️ dans la base saine.
- Pour les copies d'onglets, la partie « tout » de Q-007 : le contrat de liste des quatre toiles, `reload_list`, `on_list_change` et `on_moved` dans la base, les deux comportements alignés de Statique et Plan.
- Les niveaux des lignes des connecteurs et des assemblages : leurs commandes les décident déjà en Typst (ARCH-RISK-603).

## 9. Idées non retenues comme exigences

- Rendre configurable la règle droit/italique par projet : une seule règle est le but (T1).

## 10. Questions

### Q-001 — Quels indices sont des variables (en italique) ?
- **Pourquoi elle compte** : c'est la table d'UI-001 ; elle change l'aspect de presque chaque formule. SIA 263 et 265 n'aident pas à trancher : elles impriment tous leurs indices en lettres en italique. Une même lettre change de sens selon le symbole : `y` est un axe dans `f_m,y,d`, `M_y,Ed`, `W_pl,y`, mais « yield » dans `f_y` de l'acier ; `n` est « nominal » dans `d_char,n`.
- **Options** :
  - **A (recommandée)** : en italique, les axes et coordonnées `x`, `y`, `z` et les indices de comptage `i`, `j` (`σ_x`, `f_m,y,d` avec `y` italique, `F_x,i`, `θ_r,j`) ; tout le reste droit (`d`, `k`, `m`, `t`, `c`, `v`, `Ed`, `Rd`, `M1`, `mean`, `ser`, `fi`, `ef`, `n`…). Une liste d'exceptions, par symbole entier, dans la même table : `f_y`, `f_y,k`, `f_y,pl` (y = yield, droit).
  - **B** : seuls les indices de comptage `i`, `j` en italique ; les axes `x`, `y`, `z` droits, comme une étiquette (pas d'exception à tenir) ; `σ_x` serait droit.
  - **C** : tous les indices droits, aucune variable ; la règle la plus simple ; `σ_x` et `A_i` droits.
- **Réponse** : **C** — tous les indices droits, aucun indice-variable (l'ingénieur, 20.10.2026).

### Q-002 — Les « cotes » du niveau 3 : lesquelles ?
- **Pourquoi elle compte** : aujourd'hui un plan imprime ses cotes au niveau 2 des documents. Les réserver au niveau 3 changerait chaque rapport existant (CON-002).
- **Options** :
  - **A (recommandée)** : les cotes dessinées par l'ingénieur font partie du dessin et s'impriment à tout niveau ; seules celles que le moteur ajoute de lui-même (longueurs des barres `lengths:`, centres `centres:`, cotes d'un connecteur, échelle) passent au niveau 3. Au niveau 2, rien ne change.
  - **B** : toutes les cotes au niveau 3 seulement, à la lettre de Q-012 : les plans de vos rapports au niveau 2 perdent leurs cotes.
- **Réponse** : **A** — les cotes du moteur au niveau 3, les cotes dessinées à tout niveau (l'ingénieur, 20.10.2026).
- **Réponse révisée** (après la revue, ARCH-RISK-607) : la question contenait une erreur — `show-plan` imprime déjà au niveau 2 longueurs, centres, cotes, légende et échelle ; « longueurs et centres au niveau 3 » et « rien ne change au niveau 2 » ne tenaient pas ensemble. Reposée : **niveau 2 = aujourd'hui** ; niveau 1 le dessin seul ; niveau 3 + sources et citations là où elles existent, sinon « niveaux confondus » avec sa raison (l'ingénieur, 20.10.2026).

### Q-003 — Formulaires et cartouche : quel niveau ?
- **Pourquoi elle compte** : pour `doc-field`, `doc-value`, `doc-choice`, `doc-checklist`, `doc-signatures`, `sheet-text`, `sheet-titleblock`, `sheet-section`, le sens « 1 seul, 2 + légende, 3 + sources » n'est pas évident. Or `decisions.md:137` refusait un argument qui ne change rien (« un mensonge dans la signature »).
- **Options** :
  - **A (recommandée)** : un niveau là où il a un sens. `doc-field`, `doc-value`, `doc-choice`, `doc-checklist` : 1 la valeur seule, 2 + son libellé (aujourd'hui), 3 + sa provenance (fichier et champ). `doc-signatures`, `sheet-text`, `sheet-titleblock`, `sheet-section` vont dans `NO_LEVEL`, raison écrite : un cartouche, une signature ou un texte posé est complet ou faux.
  - **B** : toutes prennent `level:` à la lettre de Q-007, avec un sens inventé pour chacune (cartouche 1 = cases principales, 3 = + historique des révisions…).
- **Réponse** : **A** — un niveau là où il a un sens ; signatures, texte posé, cartouche, coupe dans `NO_LEVEL` (l'ingénieur, 20.10.2026).
- **Réponse révisée** (après la revue, ARCH-RISK-610) : `doc-value` n'imprime aucun libellé et le libellé de `doc-field` est toujours écrit (un argument écrit l'emporte) : le niveau 1 n'y changerait rien. Reposée : **dans `NO_LEVEL`**, avec signatures, texte posé, cartouche et coupe (l'ingénieur, 20.10.2026).

### Q-004 — La durée feu exigée par VKF 15-15, dans le rapport ? (ex-Q-017 de la base saine)
- **Pourquoi elle compte** : Q-011 veut qu'une ligne feu cite sa norme d'exigence. Le rapport cite la durée `t_fi` par SIA 265 4.5.2, même quand c'est VKF 15-15 qui l'exige : `#member(fire: (duration:, sides:, wood:))` ne connaît que la durée.
- **Options** :
  - **A (recommandée)** : une clé facultative `required: (norm:, norm-ref:)` dans `fire:`, écrite par `#show-check-member` depuis l'export ; la fenêtre et le rapport citent alors VKF 15-15 Tabelle 2.
  - **B** : garder SIA 265 4.5.2 pour la durée, VKF 15-15 n'étant dit que dans la note de l'export.
- **Réponse** : **A** — clé facultative `required: (norm:, norm-ref:)` dans `fire:` (l'ingénieur, 20.10.2026).

### Q-005 — Ce que cite un résultat de script ? (ex-Q-018 de la base saine)
- **Pourquoi elle compte** : un résultat sans `norm=` ne cite rien aujourd'hui (colonne de droite vide), alors que le principe 7 veut une référence ; sa provenance `python:scripts/<id>.py` est déjà exportée.
- **Options** :
  - **A (recommandée)** : la norme quand `result(...)` la donne ; sinon le script et la ligne de `result(...)` dans la colonne de droite.
  - **B** : la colonne reste vide, la provenance restant dans l'export.
  - **C** : `norm=` exigé dans `result(...)`, un script qui l'omet est refusé.
- **Réponse** : **A** — la norme si `result(...)` la donne, sinon le script et la ligne (l'ingénieur, 20.10.2026).

### Q-006 — Quels restes du vérificateur inclure ?
- **Pourquoi elle compte** : chacun est un lot de plus.
- **Options** (plusieurs possibles) :
  - **ARCH-004, géométrie et SVG en double** (recommandé) : environ 10 fonctions et 7 aides ; faible risque, tenu par la garde d'octets des figures.
  - **ARCH-005, copies par onglet** (recommandé) : seulement les quasi-copies, soit 10 à 15 méthodes ; risque moyen (Qt), tenu par les tests d'onglets.
  - **ARCH-006, lignes du bois → lignes du moteur** : 99 appels, `unfold` et tests ; gros, et sans effet visible.
  - **REQ-003, vent et neige sans cellules calculées** : environ 56 cellules de vent et 10 de neige ; des valeurs peuvent changer ; il faut les classeurs de test.
- **Réponse** : **ARCH-004** (géométrie et SVG) et **ARCH-005** (copies d'onglets) ; pas les lignes du bois ni le vent et la neige (l'ingénieur, 20.10.2026).

### Q-007 — Copies d'onglets : jusqu'où ? (après la revue, ARCH-RISK-706)
- **Pourquoi elle compte** : la revue montre que Schémas, Statique, Plan (avec Plan feu) et Polaires n'utilisent pas le contrat de liste de la base ; leurs `reload_list`, `on_list_change`, `on_moved` ne diffèrent pas que par des noms.
- **Options** :
  - **Partie sûre (recommandée)** : supprimer les 4 `update_list_marker` identiques à la base (`schema_tab_draft.py:273`, `statics_tab.py:601`, `drawing_tab.py:517`, `polar_tab.py:1009`) et les 5 `NEW_ROW` redéfinis ; remonter le `confirm_leave` de Schémas, Statique et Polaires dans la base par un hook `discard` ; un test nomme chaque redéfinition permise avec sa raison. Aucun changement de comportement.
  - **Tout** : en plus de la partie sûre :
    - les quatre toiles reçoivent le contrat de liste des autres éditeurs : `KEY`, `WORDS`, le dossier des sources, `saved_ids()` (aujourd'hui masqué par une variable du même nom dans Schémas et Statique) ;
    - remplir la liste (`reload_list`) devient la méthode de la base, chaque toile ne disant plus que le texte de ses lignes (« id — libellé » pour Schémas et Statique, « id » pour le Plan) ;
    - changer de ligne (`on_list_change`) passe dans la base pour Schémas, Statique et Polaires ;
    - glisser une ligne dans un autre groupe (`on_moved`) devient la méthode de la base, avec deux comportements alignés : Statique et Plan demandent d'abord d'enregistrer un brouillon en cours (aujourd'hui ils déplacent sans demander), et affichent l'erreur quand le fichier ne peut être écrit, par exemple verrouillé par OneDrive (aujourd'hui l'erreur n'est pas attrapée) ;
    - gain : environ 150 lignes en moins, un seul endroit où corriger un défaut de liste, rien ne change à l'écran hors les deux alignements ;
    - risque : ce sont les quatre onglets les plus complexes (sélection, annulation, glisser-déposer) ; `test_schema_tab`, `test_polar_tab`, `test_plan_tab_rework` et `test_fire_tab` tiennent la non-régression, mais c'est le lot le plus délicat de la spec.
- **Réponse** : **partie sûre** (l'ingénieur, 20.10.2026, après avoir demandé le détail, écrit ici).

### Q-008 — Qui lit la table des niveaux ? (après la revue, ARCH-RISK-601 à 605)
- **Pourquoi elle compte** : une même clé a deux niveaux (variable 2, étape 3 pour `s_k`, `h_ref`, `I_p` ; `N_Rd` 1 en traction, 2 en flexion) et des familles de clés existent (`rho_k_1`…) ; dans les deux cas une seule table les porte et plus aucun littéral ne reste dans le code. Reste à savoir qui la lit.
- **Options** :
  - **Python à l'export (recommandée)** : `engine` lit la table et écrit `level` dans l'export ; aucun schéma ne change ; prix : changer un niveau demande un nouvel export.
  - **Typst à l'impression** : à la lettre de D-09 ; `level` facultatif à l'export (cinq schémas montés de version, ~175 appels d'`engine`, quatre lecteurs Python réécrits) ; changer un niveau ne demande qu'une recompilation.
- **Réponse** : **Typst à l'impression** (l'ingénieur, 20.10.2026).

### Q-009 — `doc-table`, les deux tableaux de charges et `doc-image` : un niveau ? (vérification, 1er tour)
- **Pourquoi elle compte** : la spec (UI-003) les voulait avec `level:` ; à l'implémentation, ils ont été mis dans `NO_LEVEL`, comme les formulaires (D-08), sans votre décision. Leur légende (`caption`) et leurs notes (`notes`) sont écrites par vous dans la section, et un argument écrit l'emporte sur le niveau : un niveau 1 n'y retirerait rien, sauf à retirer ce que vous avez écrit.
- **Options** :
  - **Garder dans `NO_LEVEL` (recommandée)** : ils impriment ce que vous avez écrit, comme les formulaires ; la raison est écrite dans le registre.
  - **Leur donner `level:`** : niveau 1 sans la légende ni les notes, même écrites ; niveau 2 comme aujourd'hui ; niveau 3 comme 2.
- **Réponse** : **garder dans `NO_LEVEL`** (l'ingénieur, 21.10.2026).

### Q-010 — Le lexeur de `formula.typ` reste-t-il où il est ? (vérification, 2e tour)
- **Pourquoi elle compte** : ARCH-001 le voulait déplacé dans `lib/subscript.typ` ; le normaliseur, un seul passage de motif, n'en a pas besoin, et il ne sert qu'au dessin des formules ; `key_math` et `_indices` restent, ce qu'ils produisent passant par `typst_math.normalise`.
- **Options** : **accepter (recommandée)** ; le déplacer (~90 lignes, aucun changement imprimé, risque de cycle).
- **Réponse** : **accepter** (l'ingénieur, 21.10.2026).

### Q-011 — Le gel fait au lot 5 et non au dernier ? (vérification, 2e tour)
- **Pourquoi elle compte** : D-05 et UI-004 le voulaient au dernier lot ; il a été fait une fois, au lot 5, après le dernier changement d'impression ; les lots 6 et 7 ne changent aucun octet (gardes d'octets).
- **Options** : **accepter (recommandée)** ; refaire le gel (aucune différence attendue).
- **Réponse** : **accepter** (l'ingénieur, 21.10.2026).

### Q-012 — `show-annexes` et `doc-annexes` sans page -L1/-L3 ? (vérification, 2e tour)
- **Pourquoi elle compte** : UI-004 veut une page -L1 et -L3 pour chaque commande qui prend `level:` ; leurs exemples sont ```` ```typ-dry ```` (chaque page d'une source est une page à part), que la documentation ne rend pas ; un test les compile à 1, 2, 3.
- **Options** : **accepter (recommandée)** ; changer le rendu des exemples pour les annexes.
- **Réponse** : **accepter** (l'ingénieur, 21.10.2026).

### Q-013 — Un script « avec une ligne au niveau 3 » ? (vérification, 2e tour)
- **Pourquoi elle compte** : le critère d'UI-002 le demandait ; `result()` ne prend pas de niveau, les résultats d'un script prennent le `*` de la table et s'impriment à tout niveau, leur note dès 2. Lui en donner un serait un argument nouveau de l'API des scripts.
- **Options** : **accepter (recommandée)** ; ajouter `level=` à `result()` (une spec à part).
- **Réponse** : **accepter** (l'ingénieur, 21.10.2026).

## 11. Critères d'acceptation

- [x] UI-001 — même balisage d'indice dans toutes les commandes, la fenêtre et les figures ; parité Typst/Python ; idempotence ; gardes refigées avec leur raison
- [x] UI-002 — plus de niveau de ligne littéral dans les domaines ; pages du rapport identiques à niveau égal ; un test par domaine tenu, niveaux 1/2/3 croissants
- [x] UI-003 — chaque commande qui imprime prend `level:` ou est dans `NO_LEVEL` ; niveau 2 = aujourd'hui (documents et feuille témoin) ; -L1/-L3 qui compilent ; 1 ≠ 2, 2 ≠ 3 sauf « niveaux confondus »
- [x] UI-004 — gel unique des exemples et du site
- [x] ARCH-001 — `lib/subscript.typ`, `math-eval` unique, jumeau `typst_math.normalise` ; données non réécrites ; surcoût < 5 %
- [x] ARCH-002 — `lib/line-levels.json` (var/step, genres, motifs, défaut du script) ; `level` facultatif (calculations 1.8, steel 1.2, connectors 3.3, connections 4.4, scripts 1.1) ; règle de priorité écrite ; anciens exports lus
- [x] ARCH-003 — `SIGNATURES`, modèles, `display_options` à trois états, `UNCHANGED` ; `NO_LEVEL` et « niveaux confondus » testés dans les deux sens
- [x] ARCH-004 — géométrie et textes SVG sans double, garde d'octets verte, parité schéma/statique
- [x] ARCH-005 — partie sûre : 4 `update_list_marker`, 5 `NEW_ROW`, `confirm_leave` par hook ; `test_tab_overrides`
- [x] REQ-001 — durée exigée par VKF 15-15 citée VKF 15-15, rapport et fenêtre ; `checks` monte de version
- [x] REQ-002 — résultat de script cité par son script et sa ligne ; `scripts` 1.1
- [x] Documentation : `docs/typst/formulas.md`, `report-engine.md` §4, `api-conventions.md`, `data-contracts.md`, `docs/domain/scripts.md`, `docs/ui/window.md`, `decisions.md` (renversement de :137, :485, :245, :251 ; précisions :84, :152, :167) et son index, `CHANGELOG.md`, « Nouveautés » 0.120.0 fr/de/en, `///` + exemples + traductions de chaque commande touchée, catalogue des tests.
- [x] Tests : suite complète verte (`python tests/run_tests.py`), niveau « Rapide » vert.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | UI-001, ARCH-001 | capturé |
| T2 | UI-002, ARCH-002 | capturé |
| T3 | UI-003, ARCH-003 | capturé |
| T4 | D-01, D-06, UI-001 | capturé (Q-001) |
| T5 | D-03, D-08, UI-003 | capturé (Q-003) |
| T6 | D-04, D-07, CON-002, CON-005 | capturé (Q-002) |
| T7 | UI-001, ARCH-001 | capturé ; la table de classification devient sans objet (Q-001 C, D-06) |
| T8 | UI-002, ARCH-002, CON-001 | capturé (Q-008) |
| T9 | UI-003, ARCH-003, CON-005, CON-006 | capturé |
| T10 | UI-004, D-05 | capturé |
| T11 | ARCH-004, ARCH-005 ; §8 | capturé (Q-006, Q-007) ; deux restes et la partie « tout » hors périmètre |
| T12 | REQ-001, REQ-002 | capturé (Q-004, Q-005) |

### Points de la source non résolus

- Aucun : les huit questions ont reçu leur réponse le 20.10.2026.

## 13. Revue d'architecture

Trois revues indépendantes en lecture seule (agent `architecture-reviewer`), le 20.10.2026, puis un essai de compilation des formes d'indice.

| Zone | Verdict |
|---|---|
| A. Indices et citations (UI-001, ARCH-001, REQ-001, REQ-002) | APPROUVER AVEC RÉSERVES |
| B. Niveaux et commandes (UI-002, UI-003, UI-004, ARCH-002, ARCH-003) | REVOIR → réglé par Q-002 et Q-003 révisées, Q-008 et les corrections ci-dessous |
| C. Géométrie et onglets (ARCH-004, ARCH-005) | APPROUVER AVEC RÉSERVES |

Chaque risque est repris dans les exigences (§3 à §6) et dans le plan (§14).

### A. Indices et citations

- **ARCH-RISK-501 (bloquant)** — `render-symbol` et `render-formula` vivent dans `calc-engine-core.typ`, sous `formula.typ` dans la chaîne d'imports : le normaliseur ne peut pas rester dans `formula.typ` sans cycle. → une feuille `lib/subscript.typ` importée par `core`, comme `number.typ` ; lexeur déplacé, pas réécrit ; un seul `math-eval` pour les ~25 `eval` ; feuille dans `ENGINE_FILES` et `build_reference_lib`.
- **ARCH-RISK-502 (important)** — écrire la forme canonique dans les données mettrait des guillemets échappés dans les `Formules/<id>.typ` de l'ingénieur (règle 15), changerait le statut de chaque ligne dépliée, et ne couvrirait pas `_row`, `script.record`, `variables.py`. → les données ne sont pas réécrites ; Typst normalise à l'évaluation ; le jumeau Python sert la fenêtre, les figures et la parité (D-14).
- **ARCH-RISK-503 (important)** — `upright(alpha)` n'est pas idempotent et la fenêtre l'afficherait en toutes lettres. → mesuré : un bloc cité avec le grec en Unicode (`f_"c,α,d"`) est droit, garde le gras, des virgules serrées, et `to_html` le lit déjà.
- **ARCH-RISK-504 (important)** — `decisions.md:245`, `:251` (`gamma_(M1)` = M italique et 1, la clé `M2`) sont renversées pour les indices ; le symbole principal `M2` reste `M 2`. → nouvelle décision au §13 de `decisions.md`, `formulas.md:48-50` réécrit.
- **ARCH-RISK-505 (important)** — périmètre de « tout droit » : opérateurs à bornes exclus, imbriqués et `x_a^b` traités, `E_(0,05)` reste un nombre, mots que math connaît (`eq`, `in`) cités en indice. → cas du test `test_subscripts`.
- **ARCH-RISK-506 (important)** — performance et pile (débordement de tinymist, `formula.typ:362,586`). → un passage `str.replace(regex, fonction)`, itératif, chemin court sans `_`, surcoût mesuré < 5 %.
- **ARCH-RISK-507 (important)** — UI-001 change les octets de chaque formule : CON-002 et la référence d'UI-002 n'ont de sens qu'après. → lot des indices d'abord, gardes refigées, CON-002 « sauf indices ».
- **ARCH-RISK-508 (mineur)** — trois copies de la règle de symbole (`key-symbol`, `shown_variables.key_math`, `member_check.py:876`). → le jumeau.
- **ARCH-RISK-509 (important)** — REQ-001 : `norm_ref` de VKF vaut « 3.7.1 », la table est dans `fire.requirement`. → champ additif `fire.required` composé une fois en Python, recopié par Typst, `_held_equal` compare la norme, `checks` monte de version.
- **ARCH-RISK-510 (important)** — REQ-002 : la ligne vient du cadre d'appel du script ; ne pas la mettre dans `norm`. → champ additif `line`, `scripts` 1.1, branche de `norm-text`, mots du glossaire.

### B. Niveaux et commandes

- **ARCH-RISK-601 (bloquant)** — une clé a deux niveaux (variable et étape ; `N_Rd` selon le genre d'acier). → la table porte var/step et un niveau par genre.
- **ARCH-RISK-602 (bloquant)** — clés indexées (`rho_k_%d`, `mu_*`…), défaut `"*"`. → motifs ; `"*"` réservé au script, non contrôlé.
- **ARCH-RISK-603 (important)** — connecteurs et assemblages ne lisent jamais le niveau de leurs lignes. → hors table, plus de `level` exporté pour eux.
- **ARCH-RISK-604 (important)** — tableaux et figures portent leur propre `level`. → gardés, exception nommée du test AST.
- **ARCH-RISK-605 (important)** — `connections` et `scripts` exigent aussi `level` ; versions conditionnelles. → cinq versions montées, chacune ⊇ la précédente, écrite par tout export ; Q-008 a choisi Typst.
- **ARCH-RISK-606 (important)** — lecteurs Python du niveau et `level` positionnel d'`engine`. → argument nommé facultatif, lecteurs sur la table, marqueur pour l'acier.
- **ARCH-RISK-607 (bloquant)** — `show-plan` imprime déjà tout au niveau 2 ; certaines commandes n'ont rien pour le niveau 3. → Q-002 révisée (D-07) : 2 = aujourd'hui, registre « niveaux confondus ».
- **ARCH-RISK-608 (bloquant pour CON-002)** — une feuille compile au niveau d'état 1. → `sheet()` met le niveau 2 ; feuille témoin.
- **ARCH-RISK-609 (important)** — `legend: true` → `auto` et `call_command`. → réglage à trois états, `UNCHANGED` réécrit, aller-retour des modèles.
- **ARCH-RISK-610 (important)** — `decisions.md:84`, `:152`, `:167` ; `doc-value` sans libellé. → Q-003 révisée (D-08), décisions citées.
- **ARCH-RISK-611 (important)** — pas de référence d'octets des PDF. → lot 0 : empreintes des pages SVG des documents (niveaux 1, 2, 3, uniformes) et d'une feuille témoin.
- **ARCH-RISK-612 (mineur)** — clés du bois écrites dans deux JSON. → test d'égalité avec `shown-variables.json`.

### C. Géométrie et onglets

- **ARCH-RISK-701 (bloquant)** — les copies lisent les globaux de leur module. → noyaux paramétrés dans `dimension.py`, enveloppes de 1 à 3 lignes.
- **ARCH-RISK-702 (important)** — `fmt_number` n'a pas sa place dans `dimension.py`. → `number_text.plain`.
- **ARCH-RISK-703 (bloquant)** — les quatre `_text` recopiés ne donnent pas les mêmes octets avec `svg_text.draw` (ancre, ligne de base, rotation, échappement). → variante ancrée qui garde leurs octets (D-15) ; les deux enveloppes minces passent à `draw` sans changement.
- **ARCH-RISK-704 (important)** — un seul `_unit` change le cas dégénéré. → `(1, 0)`, vérifié par la garde.
- **ARCH-RISK-705 (mineur)** — `label_corners` a trois copies. → une dans `dimension.py`.
- **ARCH-RISK-706 (bloquant)** — les quatre toiles n'utilisent pas le contrat de liste de la base. → Q-007 : partie sûre seulement.
- **ARCH-RISK-707, 708 (importants)** — `on_moved` divergent ; garde lecture seule et `super()`. → hors périmètre (partie « tout ») ; pas de `super()` dans une méthode gardée.
- **ARCH-RISK-709 (important)** — liste des redéfinitions à garder. → `PERMITTED` de `test_tab_overrides`.

### Approche retenue

1. Le filet : références d'octets avant tout changement.
2. Les indices d'abord (ils changent chaque formule), puis les deux citations.
3. Les niveaux des lignes en deux temps : la table lue par Typst pendant que Python écrit encore (test d'égalité), puis Python cesse d'écrire.
4. `level:` sur les commandes, par famille.
5. La géométrie et les onglets, indépendants.
6. La documentation, le gel unique, la vérification.

## 14. Plan d'implémentation

Chaque lot se termine dans le même état : ses tests ciblés verts et `--fast` vert ; une ligne du §16 ; la suite complète en arrière-plan à la fin du lot ; un commit local par lot (aucun push sans la parole de l'ingénieur). Un lot interrompu reprend à sa première case non cochée.

**Lot 0 — Le filet** (CON-003, ARCH-RISK-611)
1. `tests/test_report_golden.py` : empreintes SHA-256 des pages SVG des trois documents du projet exemple aux niveaux 1, 2, 3 et uniformes 1, 2, 3 (`SOURCE_DATE_EPOCH` fixé), et d'une feuille témoin (`tests/fixtures/`) ; `WOODCORE_UPDATE_GOLDEN=1` et une carte `CHANGES` comme `test_figure_golden`. Ligne au catalogue des tests.

**Lot 1 — Les indices** (UI-001, ARCH-001, ARCH-RISK-501 à 508)
1. `lib/subscript.typ` : lexeur déplacé de `formula.typ`, normaliseur en un passage, `math-eval` ; import dans `calc-engine-core.typ` ; `ENGINE_FILES`, `build_reference_lib` (Internes).
2. Les ~25 `eval(…, mode: "math")` passent par `math-eval` ; `quoted-words`, `symbol-word`, `key-symbol` s'appuient dessus.
3. `calc/typst_math.py` : `normalise`, appelé par `_render` ; `shown_variables.key_math` et `member_check.py:876` passent par lui.
4. `tests/test_subscripts.py` (parité, idempotence, cas limites, grep des `eval`) ; `test_formula`, `test_richtext`, `test_figure_text` étendus ; mesure de performance.
5. Gardes refigées une fois, raison dans leur carte : `test_figure_golden`, `test_report_golden`, `test_unfold` (si ses octets bougent), exemples non régénérés (gel au dernier lot).
6. `docs/typst/formulas.md` réécrit (§ indices) ; décision au §13 de `decisions.md` (renverse :245, :251).

**Lot 2 — Les deux citations** (REQ-001, REQ-002, ARCH-RISK-509, 510)
1. REQ-001 : `member_check._fire_block` compose `fire.required` ; `checks.schema.json` et sa version ; `timber.typ:128` (clé `required`), `:445` (citation), `:1566-1567` (`burning`) ; `member_check.py:841` ; `draft_typst` ; `///` de `member`, deux exemples, `commands.json` ; `test_member_check` (`_held_equal` compare la norme), `test_fire_resistance`.
2. REQ-002 : `script_runner.result()` lit la ligne du cadre du script ; `script.py` exporte `line` ; `scripts.schema.json` 1.1 (1.0 lu) ; branche de `norm-text` ; mots du glossaire fr/de/en ; `docs/domain/scripts.md` ; `test_script`, `test_i18n`.

**Lot 3 — La table des niveaux, lue par Typst** (UI-002, ARCH-002 première moitié)
1. `lib/line-levels.json` (var/step, genres de l'acier, motifs, `"*"` du script) écrite depuis les niveaux littéraux actuels ; `calc/line_levels.py` (lecteur) ; `ENGINE_FILES`.
2. Typst : `line-level(domain, kind, key, role, fallback)` dans `calc-engine-core.typ`, lu par `show-calc` (`display.typ:686,721,726`) et `show-check-steel` selon la règle de priorité ; le bois lit la table au lieu de ses `plan-at(plan, "clé", n)` littéraux.
3. `tests/test_line_levels.py` : table = niveau exporté pour chaque clé (Python écrit encore) ; clés du bois = `shown-variables.json` ; `test_report_golden` identique.

**Lot 4 — Python cesse d'écrire le niveau des lignes** (UI-002, ARCH-002 seconde moitié, ARCH-RISK-603 à 606)
1. `engine.var/step/check` : `level` argument nommé facultatif ; les ~175 appels des domaines tenus le perdent ; connecteurs et assemblages ne l'écrivent plus.
2. Schémas et versions : calculations 1.8, steel 1.2, connectors 3.3, connections 4.4, scripts 1.1 (si pas déjà au lot 2) ; anciennes lues.
3. Lecteurs Python : `build_reference`, `variable_sources`, `variables_tab`, `steel_resistance` (marqueur).
4. Test AST (aucun niveau de ligne littéral, liste blanche) ; test par domaine niveaux 1/2/3 ; anciens exports imprimés comme avant ; `test_report_golden` identique ; export du projet exemple refait.
5. `docs/typst/report-engine.md` §4 (règle de priorité), `docs/architecture/data-contracts.md`.

**Lot 5 — `level:` sur chaque commande qui imprime** (UI-003, ARCH-003, ARCH-RISK-607 à 610)
1. Registres `NO_LEVEL` et « niveaux confondus » à côté de `CATEGORIES`, et leur test dans les deux sens (rouge d'abord, il liste ce qui manque).
2. Par famille, chacune avec `///`, exemples, `commands.json`, `SIGNATURES`/modèles, `display_options` (trois états), `test_display_view`, `test_call_command` :
   - figures : `show-plan`, `show-fire-plan`, `show-static-model`, `show-extract`, `show-connector`, `doc-plan`, `doc-fire-plan`, `doc-extract`, `doc-image`, `sheet-viewport`, `sheet-fire-viewport` ;
   - tableaux et listes : `show-position-list`, `show-plan-quantities`, `show-load-summary`, `show-result-summary`, `show-norm-list`, `show-bibliography`, `show-annexes`, `doc-annexes`, `doc-table`, `live-load-table`, `dead-load-table`, `sheet-legend`, `sheet-fire-legend`, `sheet-position-list`, `sheet-quantities` ;
   - `distance` ; `show-check`.
3. `sheet()` met le niveau 2 ; feuille témoin.
4. `test_report_golden` au niveau 2 identique ; les niveaux 1 et 3 refigés avec leur raison.
5. Décision au §13 de `decisions.md` : renverse :137, :485, précise :84, :152, :167 ; index.

**Lot 6 — Géométrie et textes SVG** (ARCH-004)
1. Noyaux de `dimension.py`, enveloppes, `_midpoint`, `label_corners` ; `number_text.plain`.
2. Enveloppes minces de `_text` → `svg_text.draw` ; variante ancrée pour les quatre copies ; un `_unit`.
3. `test_figure_golden` vert ; parité schéma/statique ; liste des doublons réduite (`WOODCORE_UPDATE_DUPLICATES=1`).

**Lot 7 — Copies d'onglets, partie sûre** (ARCH-005)
1. `tests/test_tab_overrides.py` d'abord.
2. Suppression des 4 `update_list_marker` et des 5 `NEW_ROW` ; hook `discard` dans `SourceEditorTab.confirm_leave`.
3. Commentaire de raison sur chaque redéfinition gardée ; tests d'onglets.

**Lot 8 — Clôture**
1. Gel unique : `build_examples --freeze`, pages `-L1`/`-L3`, site construit localement (UI-004).
2. Documentation : `docs/` touchés, `decisions.md` et son index, `CHANGELOG.md`, « Nouveautés » 0.120.0 fr/de/en, catalogue des tests.
3. Vérification indépendante (`verify-requirements`), corrections, puis `finish` (suite complète, un commit, la question du push).

### Ce qui n'est pas fait

- La partie « tout » des copies d'onglets, les lignes du bois en lignes du moteur, le vent et la neige sans cellules calculées (§8).
- Les niveaux des lignes des connecteurs et des assemblages (décidés par leurs commandes).

## 15. Vérification

Vérification indépendante du 21.10.2026 (agent `requirements-verifier`, base 1e57487, commits 3bc0ddf..4021f6c), tests rejoués par lui (aucun échec, « Rapide » 1158 passés), puis un premier tour de corrections ; 2e tour le même jour (tests rejoués par lui : `test_line_levels` 13, `test_command_levels` 5, `test_subscripts` 5, `test_docs_coherence` 7, `test_doc_comments` 6, aucun échec), ses restes corrigés (exports anciens de chaque autre version, libellés du spec) ou tranchés par l'ingénieur (Q-010 à Q-013, D-17 à D-20).

| Élément | Verdict (1er tour) | Preuve, et ce qui a été fait |
|---|---|---|
| REQ-001 | ✅ | `member_check.py:449-451`, `timber.typ:128,162-164,457,1579`, `checks` 1.5 ; `test_a_duration_vkf_15_15_requires_is_cited_by_it_in_the_window_and_in_the_report`. |
| REQ-002 | ✅ | `script_runner.py:125-131`, `norm-text` ; `test_a_result_naming_no_norm_is_cited_by_the_line_of_its_call`. |
| UI-001 | ✅ | `lib/subscript.typ`, 30 `math-eval` ; `test_subscripts` (parité, idempotence, aucun `eval` hors `math-eval`). Corrigé au 1er tour : le corpus de parité reçoit aussi les symboles écrits dans `lib/`. |
| UI-002 | ✅ (2e tour) | Le script : D-20. Inclusion 1 ⊂ 2 ⊂ 3 prouvée sur les lignes imprimées (`test_each_level_of_a_domain_prints_the_lines_of_the_level_below`), rendu différent par domaine, charges utiles comprises ; script : ses résultats à tout niveau, sa note dès 2 (`test_a_script_prints_its_results_at_every_level` — une ligne de script « au niveau 3 » n'existe pas, `result()` ne prenant pas de niveau) ; règle 6 (`test_a_line_no_source_gives_a_level_stops_the_report_naming_it`) ; un export 1.7 avec ses niveaux imprime comme celui d'aujourd'hui (`test_an_export_written_before_prints_as_it_did`). |
| UI-003 | ✅ (2e tour) | Pages -L1/-L3 des annexes : D-19. `doc-table` et trois autres dans `NO_LEVEL` : décidé par l'ingénieur (Q-009, D-16). Commandes des feuilles et annexes compilées à 1, 2, 3 (`test_the_sheets_and_the_annexes_print_differently_at_each_level_unless_they_say_why_not`) ; `show-annexes`/`doc-annexes` sans page -L1/-L3, leurs exemples étant `typ-dry` (décision en vigueur), raison écrite dans le test ; `show-check` : aucune vérification dans l'exemple, confondu (1, 2, 3). |
| UI-004 | ✅ (2e tour, D-18, D-19) | Gel unique au lot 5 (après tout ce qui change l'impression ; les lots 6 et 7 n'en changent rien) ; site construit localement au lot 8 (`python website/build.py` : 1416 pages d'exemple, 0 échec, 390 fichiers dans `public/`, non publié). |
| ARCH-001 | ✅ (2e tour, D-17) | Mesure du surcoût écrite dans `docs/architecture/performance.md` (+2 %) ; lexeur non déplacé et `key_math`/`_indices` gardés : écarts jugés acceptables. |
| ARCH-002 | ✅ (2e tour) | Règle 6 et export ancien prouvés (ci-dessus), puis, au 2e tour, un export de chaque autre version d'avant : acier 1.1, connecteurs 3.2, assemblages 4.3, scripts 1.0, leurs lignes portant les niveaux que Python écrivait, imprimés à 1, 2, 3 comme ceux d'aujourd'hui (`test_every_other_export_written_before_prints_as_it_did`). Connecteurs et assemblages hors de la table, comme UI-002 le dit (ARCH-RISK-603). |
| ARCH-003 | ✅ (2e tour) | Aller-retour d'un `level:` écrit (`test_a_level_written_survives_the_objects_round_trip`) ; `UNCHANGED` de `test_call_command` : les appels de `show-plan` et `show-fire-plan` qui y sont écrits sortent inchangés (cochée = `auto` non écrit), rien à réécrire. |
| ARCH-004 | ✅ (écarts visibles, D-15) | `plan_svg._text` garde son écriture (octets) ; `_text` minces de `schema_svg`/`statics_svg` gardés comme adaptateurs. |
| ARCH-005 | ✅ | `test_tab_overrides` ; tests des onglets verts. |
| CON-001 à CON-006 | ✅ | Gardes d'octets, historique, décisions. |
| Documentation | ✅ (2e tour) | `docs/typst/api-conventions.md` : la règle `level:` / `NO_LEVEL` / `LEVELS_CONFOUNDED`. |
| §8 | ✅ | Rien de hors périmètre fait. |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-20 | draft | spécification écrite à partir des reports de la base saine (UI-001, UI-005, UI-006, gel, restes ⚠️, Q-017, Q-018) et de quatre relevés du code ; 6 questions ouvertes |
| 2026-10-20 | specified | les 6 questions répondues (D-06 à D-11) ; prochaine étape : revue d'architecture |
| 2026-10-20 | reviewed | trois revues (§13 : A et C avec réserves, B à revoir) ; Q-002 et Q-003 révisées (la première question sur les cotes contenait une erreur), Q-007 et Q-008 répondues (D-07, D-08, D-12, D-13) ; essai de compilation des formes d'indice (D-14) ; plan en 9 lots (§14) ; attend l'approbation |
| 2026-10-20 | approved | approuvée par l'ingénieur, « Approuver et implémenter » ; début du lot 0 |
| 2026-10-20 | implementation | **Lot 0 fait** : `tests/test_report_golden.py` — les pages SVG des trois documents du projet exemple (rapport aux niveaux 1, 2, 3 et uniformes 1, 2, 3 ; convention et base de projet aux niveaux 1, 2, 3) et d'une feuille témoin (plan au 1:100, légende, liste des positions, quantités), `SOURCE_DATE_EPOCH` fixé, 13 variantes, 226 pages, figées dans `tests/fixtures/report-golden.json` ; déterministe (deux passages identiques) ; ligne au catalogue des gardes. Prochain : lot 1 (indices). |
| 2026-10-20 | implementation | **Lot 1 fait** (UI-001, ARCH-001) : `lib/subscript.typ` (`normalize-subscripts`, `math-eval`, `greek-names` déplacé de `formula.typ`), importé par `calc-engine-core.typ`, dans `ENGINE_FILES` et `LIB_FILES` (interne, pas de commande publique nouvelle) ; les 25 `eval(…, mode: "math")` de `lib/` passent par `math-eval` ; jumeau `typst_math.normalise`, lu par `_render` (fenêtre, figures) ; `tests/test_subscripts.py` (cas de la spec, parité Typst/Python sur 180+ symboles et formules, idempotence, compilation, aucun `eval` hors `math-eval`) ; `test_timber` : six attentes d'indices italiques devenues droites ; garde des pages refigée (`CHANGES`), garde des figures et `test_unfold` inchangés ; surcoût mesuré +2 % au niveau 3 uniforme (4,66 s → 4,77 s, quatre passages) ; décision au §13 de `decisions.md` (renverse en partie :245, :251), `formulas.md`, `layout.md`, catalogue. *Écarts* : le lexeur de `formula.typ` (`quoted-words`) n'est pas déplacé — le normaliseur est un passage regex et n'en a pas besoin, le lexeur ne sert qu'aux symboles écrits à la main ; `shown_variables.key_math` et `member_check._indices` restent : ils groupent une clé en indice (`sigma_t_0_d` → `sigma_(t,0,d)`) et la forme passe ensuite par `normalise`. Prochain : lot 2. |
| 2026-10-20 | implementation | **Lot 2 fait** (REQ-001, REQ-002) : REQ-001 — `member_check._fire_block` compose `fire.required` (`{norm: "VKF 15-15", norm_ref: "Tabelle <n>"}`) quand la durée suit le bâtiment ; `checks` 1.5 (⊇ 1.4, `REQUIRED_EXPORT_VERSION`, schéma) ; la ligne `t_fi` des lignes de la fenêtre et `#member(fire: (required:))` la citent, `fire_typst` l'écrit, `#show-check-member` la recopie ; `///` de `member` (troisième exemple feu), `commands.json` fr/de ; `_held_equal` compare aussi la norme ; `test_a_duration_vkf_15_15_requires_is_cited_by_it_in_the_window_and_in_the_report` ; `test_fire_check_tab` suit la version 1.5. REQ-002 — `result()` lit la ligne de son appel (premier cadre du fichier du script) ; `scripts` 1.1 (`line`, 1.0 lu) ; `norm-text` cite « script <fichier>, l. N » (modèle `script.line` du glossaire, fr/de/en) ; `#val` porte la ligne ; `test_a_result_naming_no_norm_is_cited_by_the_line_of_its_call` (depuis une fonction aussi, et dans un `show-calc` compilé). Exports `checks.json` et `scripts.json` du projet exemple refaits ; garde des pages inchangée (le rapport exemple n'imprime ni la ligne t_fi au niveau 3 ni de résultat de script sans norme). `docs/domain/fire-resistance.md`, `docs/domain/scripts.md`. *Précision* : la carte « Résultats » de la fenêtre n'imprime que la clause du contrôle, pas celle de chaque ligne ; « dans la fenêtre » se lit donc sur les lignes que la fenêtre calcule (`member_check.compute`). Suite liée : 2099 passés, l'échec (`test_fire_check_tab`, version) corrigé ; « Rapide » 1146. Prochain : lot 3. |
| 2026-10-20 | implementation | **Lot 3 fait** (UI-002, ARCH-002 première moitié) : niveaux de toutes les lignes relevés en faisant tourner les tests des domaines, le moteur instrumenté (182 lignes : poids propre, charges utiles, neige, vent, acier de chaque genre ; aucun conflit hors `h_ref`/`s_k` var 2 / étape 3 et `N_Rd` de l'acier, 1 en traction et compression, 2 en flexion) → `tests/fixtures/line-levels-history.json` ; `lib/line-levels.json` (`lines`, `kinds`, `patterns` pour `qk_(max|min)_cfs?N` du vent, `*` du script ; bois : 81 clés lues de `timber.typ`) dans `ENGINE_FILES` ; `calc/line_levels.py` ; `line-level` (`calc-engine-core.typ`) lu par `show-calc` pour chaque var et step ; `timber.typ` : les 104 `plan-at(plan, clé, n)` deviennent `timber-at(plan, clé)` — plus aucun niveau littéral dans le bois ; `tests/test_line_levels.py` (historique, priorité, parité Typst/Python, bois = `shown-variables.json`) ; pages du rapport identiques à l'octet ; `report-engine.md` §4 (règle de priorité), `layout.md`, catalogue. Suite liée 583 passés, « Rapide » 1152. Python écrit encore ses niveaux (retirés au lot 4). Prochain : lot 4. |
| 2026-10-21 | implementation | **Lot 4 fait** (UI-002, ARCH-002 seconde moitié) : `engine.var/step/check` — `level` argument nommé facultatif, écrit seulement s'il est donné ; un réécriveur AST retire ~256 niveaux de onze modules de domaine (paramètres `level` des aides et arguments de chaque appel) ; `script` n'écrit plus son `level: 1` ; l'acier choisit sa réponse par la table (`c.kind`) ; versions `calculations` 1.8, `steel` 1.2, `connectors` 3.3, `connections` 4.4 (`scripts` 1.1 du lot 2), chacune ⊇ les précédentes, écrites par tout export, `level` facultatif dans les schémas ; lecteurs Python sur la table (`variable_sources`, `build_reference`) ; exports du projet exemple : niveaux retirés des lignes (vérifié identique à un vrai réexport pour connecteurs, assemblages, acier, scripts ; les charges viennent de classeurs absents de l'exemple) ; table complétée (`hoehenspruenge`, `lastmodell`, `qk_*_bh/db/dh`, `e_1_eff`, motifs de l'acier `W_(pl|el)_[yz]`, `A_v_*`, `*_Ed`, `*_Rd`…), historique 302 lignes ; tests : aucun niveau de ligne dans les domaines (AST), versions et absence de niveau dans les exports de l'exemple, chaque domaine imprime différemment aux niveaux 1, 2, 3 ; pages identiques à l'octet ; `decisions.md` (décision D-13), `data-contracts.md`, `report-engine.md`. *Écart* : connecteurs et assemblages **dans** la table (82 lignes), non hors d'elle comme le disait la revue : un `#show-calc("connector", …)` écrit à la main lit les niveaux de ses lignes, et se serait arrêté. Suite complète : 3058 passés, 10 échecs corrigés (tests qui lisaient `["level"]` ou les anciennes versions), `test_toolbar` (fin de processus Qt) vert seul ; « Rapide » 1155. Prochain : lot 5. |
| 2026-10-21 | implementation | **Lot 5 fait** (UI-003, UI-004, ARCH-003) : `print-level` et `at-level` (`calc-engine-core.typ`) ; `level:` sur 23 commandes — `show-plan`, `show-fire-plan`, `show-static-model`, `schema`, `show-extract`, `show-annexes`, `show-position-list`, `show-plan-quantities`, `show-load-summary`, `show-result-summary`, `show-norm-list`, `show-bibliography`, `distance`, `doc-plan`, `doc-fire-plan`, `doc-extract`, `doc-annexes`, `sheet-viewport`, `sheet-fire-viewport`, `sheet-legend`, `sheet-fire-legend`, `sheet-position-list`, `sheet-quantities` — niveau 1 sans légende, légende de figure, titre, échelle, longueurs, centres, aides, « Bezeichnung » ; niveau 3 des résumés avec une colonne « Norm » (mot du glossaire fr/de/en), les autres « niveaux confondus » ; `sheet()` au niveau 2 ; registres `NO_LEVEL` (45, raisons) et `LEVELS_CONFOUNDED` (23) dans `build_reference_lib` ; `tests/test_command_levels.py` (registres dans les deux sens, chaque commande compilée à 1, 2, 3, un argument écrit l'emporte) ; garde des pages : niveaux 2, 3, uniformes 2, 3 et feuille témoin inchangés, niveau 1 refigé avec sa raison ; générateur d'appels (`_by_level` : cochée = auto non écrit, décochée = false), panneau du plan avec « Niveau », `display_options` (réglage `switch`, niveau du modèle statique, du schéma, du résumé, de la liste des positions), modèles d'objets (`_switch_value`), `typst_objects_parse` (signatures) ; `///` et 47 unités traduites fr/de dans `commands.json` ; décision (renverse `decisions.md:137` et `:485`, cite :152 et la règle des cellules), `report-engine.md`, `ui/window.md`, catalogue ; tests ajustés : sondes au niveau 2 des documents (13 fichiers), résumés, appels, panneaux, gabarits. **Gel unique fait ici** (UI-004, plutôt qu'au lot 8 : les lots 6 et 7 ne changent aucune impression) : `build_examples --freeze` — *défaut d'avant ce travail corrigé* : depuis l'issue #64 les figures sont nommées depuis la racine et le gel ne les recopiait pas (aucun plan d'exemple ne compilait) ; il recopie désormais chaque fichier nommé depuis la racine (37) ; l'exemple de `doc-image` nommait un chemin d'avant #64 ; 497 exemples rendus dont 123 `-L1` et 123 `-L3`. Suite complète 3063 passés, 7 échecs corrigés ; « Rapide » 1155. *Écarts* : `doc-table`, `live-load-table`, `dead-load-table`, `doc-image` dans `NO_LEVEL` comme les formulaires (D-08 : ils impriment ce que l'ingénieur a écrit) ; site non reconstruit à ce lot (lot 8). Prochain : lot 6. |
| 2026-10-21 | implementation | **Lot 6 fait** (ARCH-004) : noyaux de `dimension.py` (`ends`, `linear_direction`, `linear_line`, `angle_arc`, `along`, `typed_point`, `nearest_ray`, `box_corners`, `unit`) ; `schema_geometry` et `statics_geometry` n'en gardent qu'une enveloppe d'une ligne chacune (`fmt_number` sur `number_text.plain`, `_midpoint = dimension.midpoint`) ; `label_corners` (×2) et `number_corners` = `dimension.box_corners` ; un seul `_unit` (deux points confondus → (1, 0), D-15) ; `svg_text.plain`, seul écrivain des textes simples des connecteurs, du poids propre et de la neige (le texte de la neige désormais échappé) ; `connector_svg` appelle `svg_text.draw` au lieu du `_text` privé de `statics_svg` ; `number_text.trimmed` ne rogne plus les zéros d'un entier à 0 décimale (ARCH-RISK-702) ; garde des figures et des pages identiques à l'octet ; doublons 53 → 45 groupes ; `tests/test_geometry_kernels.py`, catalogue. *Écarts* : le `_text` du plan garde son écriture (centrage d'un tiers de corps, halo, ordre des attributs : le réunir aurait changé ses octets) ; les `_text` minces de `schema_svg` et `statics_svg` restent des adaptateurs d'une ligne (le halo du schéma est un couple). Tests liés 929 passés, « Rapide » 1158. Prochain : lot 7. |
| 2026-10-21 | implementation | **Lot 7 fait** (ARCH-005, partie sûre) : les 4 `update_list_marker` identiques (Schémas, Statique, Plan, Polaires) et les 4 `NEW_ROW = "<new>"` recopiés supprimés (importés de `source_editor` ; l'alias `POLAR_NEW_ROW` en vient déjà, le `NEW_ROW = -1` du Journal est autre chose) ; `confirm_leave` des Schémas, de la Statique et des Polaires par la base — `UNSAVED_WORDS`, `DISCARD_OPENS_FIRST`, `discard_draft`, le `current_label` des Polaires (l'id tiré du nom) ; aucun changement de comportement ; `tests/test_tab_overrides.py` (`PERMITTED` : 30 redéfinitions, chacune avec sa raison ; aucune ne recopie la base aux noms près) ; tests des onglets 378 passés, `test_window`, `test_tab_registry`, `test_autosave`, `test_editor_buttons` verts ; « Rapide » vert. Lot 8 : `CHANGELOG.md`, « Nouveautés » 0.120.0 fr/de/en écrits. Prochain : site local, vérification. |
| 2026-10-21 | verification | 1er tour du vérificateur (table au §15) ; corrections : tests d'inclusion, du script, de la règle 6, d'un export 1.7, des feuilles et des annexes, de l'aller-retour d'un `level:` ; corpus de parité étendu à `lib/` ; `api-conventions.md`, `performance.md` ; Q-009 posée et répondue (D-16) ; site construit localement. Prochain : 2e tour. |
| 2026-10-21 | verification | 2e tour du vérificateur : Q-009/D-16 et les corrections tenus ; restes : un export ancien par autre version (`test_every_other_export_written_before_prints_as_it_did`, acier 1.1, connecteurs 3.2, assemblages 4.3, scripts 1.0), UI-003 sans `live-load-table`/`dead-load-table`, D-16 après D-15, ligne ARCH-002 du §15 ; quatre écarts tranchés par l'ingénieur (Q-010 à Q-013 → D-17 à D-20). Prochain : suite complète, clôture. |
| 2026-10-21 | completed | suite complète verte (3083 passés, 11 ignorés, 1151 s) ; critères du §11 cochés ; spécification déplacée dans `docs/requirements/completed/`. |
