---
id: 2026-10-22-retrait-niveau-manuel
titre: Retrait des restes du niveau de détail −1 « Sélection manuelle » (issue #93) et clôture de l'épopée #74
status: completed
cree: 2026-10-22
mis_a_jour: 2026-10-22
source: message écrit (« Implémente les issues 74 et 93. », 22.10.2026), issues GitHub #74 et #93
docs: [docs/ui/window.md, docs/ui/tab-member-checks.md, docs/domain/member-checks.md, docs/domain/calculation-domains.md, docs/typst/report-engine.md, docs/architecture/data-contracts.md, docs/architecture/layout.md, docs/open-questions.md, docs/conventions/testing-catalogue-window.md, docs/conventions/testing-catalogue-guards.md]
---

# Retrait des restes du niveau de détail −1 « Sélection manuelle » — Spécification

## 1. Objectif

La refonte des commandes Typst (#74, sous-issues #75 à #82, spec `completed/2026-10-21-commandes-typst-refonte.md`) a retiré du moteur le niveau de détail −1 « Sélection manuelle » (`level: -1, shown: (…)`) : aucune commande de `lib/` ne prend plus `shown:` et `check-level` refuse −1. La fenêtre et deux modules de domaine en gardent les restes, morts : un genre de contrôle `detail` qui n'est plus jamais construit, un module `calc/shown_variables.py` et son fichier `lib/shown-variables.json` qui n'ont plus de lecteur (sauf une fonction), des mots dans trois langues, des tests et des paragraphes de `docs/` qui décrivent la sélection manuelle comme actuelle. L'ingénieur (22.10.2026) : elle « peut simplement disparaître ». L'épopée #74, dont toutes les sous-issues sont fermées, n'a plus rien à implémenter : elle est fermée avec un résumé.

## 2. Source

> **T1** — « Implémente les issues 74 et 93. » (message de l'ingénieur, 22.10.2026)
>
> Issue #93, « Retirer les restes du niveau de détail −1 « Sélection manuelle » dans la fenêtre » :
>
> **T2** — « La refonte des commandes Typst (#74) a retiré le niveau de détail −1 « Sélection manuelle » (`level: -1, shown:`) du moteur : plus aucune commande ne le prend. L'ingénieur, 22.10.2026 : il peut simplement disparaître. »
>
> **T3** — « `calc/tools/display_options.py` : le genre de contrôle `detail` avec −1 et le mot `ds_level_manual` (« Sélection manuelle ») ; »
>
> **T4** — « `calc/tools/display_view.py` : le niveau des commandes qui prenaient `shown:` ; »
>
> **T5** — « `calc/tools/connectors_tab.py`, `member_check_tab*.py`, `load_tab.py` : ce qui alimentait la sélection manuelle ; »
>
> **T6** — « `calc/shown_variables.py` et `lib/shown-variables.json` s'ils n'ont plus de lecteur ; »
>
> **T7** — « les mots retirés dans les trois langues, les tests, la documentation (`docs/ui/`). »
>
> **T8** — « Petite modification (small-feature) une fois #83 à #91 commités. »
>
> Issue #74, « Commandes Typst : refonte et uniformisation » (épopée) :
>
> **T9** — « Sous-issues (dans l'ordre) : #75 … #82 » — toutes fermées au 22.10.2026 ; la spec `2026-10-21-commandes-typst-refonte` est `completed`, ses pertes restantes (torsion, légende automatique d'un extrait) laissées par décision de l'ingénieur, ses deux suites ouvertes en issues (#92, #93).

## 3. Exigences fonctionnelles

### REQ-001 — Le volet « Affichage » n'a plus de niveau −1
- **Exigence** : Woodcore doit retirer de `calc/tools/display_options.py` le genre de contrôle `detail` (de `KINDS`, sa branche de lecture), `LEVELS_SHOWN`, `SELECTION`, `LEVEL_SHOWN`, `DETAIL`, et de `calc/tools/display_view.py` la classe `LevelControl` et chaque branche `detail` / `-1` / `shown` (construction, `_set`, `set_context`, `values`, `state`, dépendances). Le contrôle de niveau `level` (auto, 0 à 3) reste tel quel.
- **Source** : T2, T3, T4
- **Priorité** : doit
- **Critère d'acceptation** : `grep -n "detail\|SELECTION\|LevelControl\|\"shown\"" calc/tools/display_options.py calc/tools/display_view.py` ne trouve plus que des homonymes sans rapport (`ds_card_shown`, `detail-figure`) ; chaque volet « Affichage » de `SPECS` se construit et compile (`tests/test_display_view.py`).

### REQ-002 — `calc/shown_variables.py` et `lib/shown-variables.json` supprimés
- **Exigence** : Woodcore doit supprimer `calc/shown_variables.py` et `lib/shown-variables.json`. Sa seule fonction encore vivante, `check_command`, n'est appelée qu'à un endroit (`member_check._compute_section`, pour décider de la ligne `eta_s` d'une compression) : elle disparaît avec cette ligne (REQ-007, Q-001).
- **Source** : T6
- **Priorité** : doit
- **Critère d'acceptation** : les deux fichiers n'existent plus ; `git grep -n "shown_variables\|shown-variables"` hors `docs/history/`, `docs/requirements/completed/`, `CHANGELOG.md` et les pages « Nouveautés » publiées ne trouve que le garde de `tests/test_display_view.py`, les décisions de `docs/decisions.md`, les paragraphes de `docs/` marqués « retiré » ou qui disent le retrait, et les specs anciennes de `docs/requirements/active/` ; rien dans `calc/`, `lib/` ni `tests/` hors du garde ; `tests/test_member_check.py` vert.

### REQ-003 — Ce qui alimentait la sélection manuelle disparaît
- **Exigence** : Woodcore doit retirer `member_check.shown_keys`, `member_check.shown_choices`, `_NOT_ROUND` et `FIRE_MEMBER_KEYS` (leurs seuls lecteurs) ; `LoadTab.shown_choices` ; les imports inutilisés de `shown_variables` (`connectors_tab.py`, `woodcore_gui.py`, `load_tab.py`) et de `display_options` laissés pour la sélection manuelle (`member_check_tab.py`, `member_check_tab_actions.py`, `member_check_tab_form.py`), avec leurs commentaires.
- **Source** : T5
- **Priorité** : doit
- **Critère d'acceptation** : aucun de ces noms dans `calc/` ; la fenêtre s'ouvre (`tests/test_member_check_tab.py`, `test_connectors*.py`, `test_load_tab*.py` verts) ; un `pyflakes`/lecture ne laisse aucun import mort dans ces six modules.

### REQ-004 — Les mots retirés dans les trois langues
- **Exigence** : Woodcore doit retirer de `STRINGS` de `display_options.py`, en fr, de et en : `ds_level_manual`, `ds_shown`, `ds_shown_tip`, `ds_shown_none` et les huit `ds_shown_<clé>` du moment polaire. `ds_card_shown`, `ds_choice_none`, `ds_level_auto` restent (lus ailleurs).
- **Source** : T3, T7
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_i18n.py` vert ; aucune des clés retirées dans `calc/`.

### REQ-005 — Les tests suivent
- **Exigence** : Woodcore doit retirer les tests de la sélection manuelle (`test_display_view.py` : `test_no_line_of_minus_one_is_locked_and_a_symbol_handed_over_is_shown`, `test_minus_one_sets_its_variables_side_by_side_as_the_width_allows`), adapter `test_every_level_a_panel_offers_compiles` (plus de −1 ni de `shown:`), retirer l'en-tête orphelin de `test_display.py` et la phrase fausse du docstring de `test_line_levels.py`, et ajouter un garde : aucun volet « Affichage » n'offre −1, aucun module de `calc/` n'importe `shown_variables`, aucun mot `ds_level_manual`/`ds_shown*` n'existe.
- **Source** : T7 ; inféré (`docs/conventions/testing.md` : un retrait est gardé par un test)
- **Priorité** : doit
- **Critère d'acceptation** : le garde existe dans `tests/test_display_view.py` et passe ; la suite complète est verte.

### REQ-007 — Plus de verdict `eta_s` doublé en compression et en flexion simples
- **Exigence** : Woodcore doit cesser d'écrire la ligne `eta_s` qu'il ajoutait pour le niveau −1 (issue #58) à une compression sans angle et à une flexion sans angle (avec ou sans effort normal) : leur verdict n'est plus que `eta`. `eta_s` reste là où il est un verdict intermédiaire (flambage, déversement, où `eta` est le maximum de plusieurs). Cela vaut aussi en situation d'incendie (`_lines` appelle `_compute_section`) et pour la carte « Résultats » de l'onglet, qui affiche `result["rows"]`. Les fichiers de domaine déjà écrits ne sont pas touchés : leur ligne `eta_s` reste, inerte (Typst la calcule, Woodcore ne la synchronise plus, aucune alerte) ; l'ingénieur la supprime à la main ; « Régénérer » — que la fenêtre ne propose que si la forme du domaine change — la retirerait tant qu'il ne l'a pas modifiée ; la forme d'un domaine (`member_check.form_of`) et `GENERATOR_VERSION` ne changent pas. Les quatre domaines concernés du projet exemple (BI-01, BI-02, FE-01, DR-02) sont réécrits sans elle dans `tests/projet-exemple/` (fichier et entrée de `unfold.json`) et dans la copie `examples/`.
- **Source** : T6, Q-001 (réponse de l'ingénieur, 22.10.2026)
- **Priorité** : doit
- **Critère d'acceptation** : `member_check.compute` d'une compression sans angle et d'une flexion sans angle (avec et sans N, et au feu) n'a pas de ligne `eta_s` ; celle d'un flambage et d'un déversement l'a toujours (test dans `tests/test_member_check.py`) ; un domaine existant qui garde sa ligne `eta_s` a `matches` vrai, aucune ligne `missing`/`conflict`, `refresh` ne fait rien, `regenerate` la retire (test dans `tests/test_unfold.py`) ; `tests/projet-exemple/Timber-checks/` et `examples/Timber-checks/` sans `eta_s` en compression et flexion simples, les quatre autres `eq:eta_s` de la base gardés ; `test_unfold.test_the_example_projects_unfolded_checks_are_written_byte_for_byte_as_held` vert.

### REQ-006 — L'épopée #74 fermée
- **Exigence** : Woodcore n'a rien à implémenter pour #74 ; elle est fermée par `finish` avec un commentaire qui renvoie à ses huit sous-issues fermées, à la spec `completed/2026-10-21-commandes-typst-refonte.md`, aux versions 0.120/0.121, à ses suites (#92 ouverte, #93 par ce travail) et aux pertes laissées par décision (torsion, légende automatique d'un extrait).
- **Source** : T1, T9
- **Priorité** : doit
- **Critère d'acceptation** : #74 et #93 fermées avec un commentaire, après la réponse de l'ingénieur à « Pousser et fermer les issues ? ».

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Rien de visible ne change
- **Exigence** : le volet « Affichage » de chaque commande offre les mêmes niveaux qu'aujourd'hui (le −1 n'y apparaissait déjà plus). Seul changement visible : une compression ou une flexion simples n'impriment plus leur verdict deux fois, ni dans le rapport ni dans la carte « Résultats » de l'onglet (REQ-007). Une page d'or qui imprimerait un de ces domaines serait renouvelée avec sa raison dans `CHANGES` ; le rapport de statique du projet exemple n'en imprime aucun (constaté à l'implémentation), ses pages ne changent donc pas.
- **Source** : inféré de T2 (le −1 est déjà inaccessible)
- **Langues** : fr / de / en — aucune chaîne ajoutée
- **Critère d'acceptation** : `tests/test_report_golden.py` vert sans page renouvelée (le rapport du projet exemple n'inclut aucun contrôle de barre) ; `tests/test_display_view.py` vert.

## 5. Exigences d'architecture

### ARCH-001 — Aucune source orpheline ni description fausse
- **Exigence** : chaque paragraphe de `docs/` qui décrit la sélection manuelle comme actuelle est corrigé (retiré ou marqué retiré, avec ce qui la remplace : les arguments d'affichage fins et `#var-table`) ; les phrases fausses (« lib/calc-engine.typ lit shown-variables.json », « les volets d'options lisent ce fichier ») disparaissent. Les paragraphes déjà marqués « retiré » restent de l'histoire.
- **Source** : T7 ; principe « une seule source de vérité » (CLAUDE.md, une copie qui vieillit sans le dire)
- **Critère d'acceptation** : `docs/ui/window.md`, `docs/ui/tab-member-checks.md`, `docs/domain/member-checks.md`, `docs/domain/calculation-domains.md`, `docs/typst/report-engine.md`, `docs/architecture/data-contracts.md`, `docs/architecture/layout.md`, `docs/open-questions.md`, `docs/conventions/testing-catalogue-window.md`, `testing-catalogue-guards.md` relus ; `tests/test_docs_coherence.py` vert.

### ARCH-002 — Le calcul reste sans Qt
- **Exigence** : le retrait de `eta_s` (REQ-007) se fait dans `calc/domains/member_check.py`, le générateur `unfold` n'en sait rien ; aucun module de domaine ne dépend de la fenêtre.
- **Source** : principe « la logique de domaine est indépendante de l'UI »
- **Critère d'acceptation** : `member_check.py` n'importe ni `display_*` ni module Qt.

## 6. Contraintes

- **CON-001** — Les fichiers de domaine déjà écrits dans les projets de l'ingénieur ne passent pas en alerte rouge (`unfold.domain_state`) et ne sont pas réécrits du seul fait de ce nettoyage : la forme et `GENERATOR_VERSION` ne changent pas. Source : Q-001 (option « sans forcer »).
- **CON-002** — Ne sont **pas** des restes du −1 et restent intacts : le champ `shown` des aides de construction (`schemas/schemas.schema.json`, « l'aide est-elle exportée »), `lib/line-levels.json` (le niveau de chaque ligne), `unfold.LEGACY_STUBS` (reconnaissance des stubs d'anciennes versions), `calc/renamed-commands.json`, les homonymes `shown` de `lib/sheet.typ`, `lib/formula.typ`, `lib/positions.typ`, `lib/distance.typ`, `calc-engine-drawings.typ`, et `ds_card_shown`. Source : inférée de la cartographie.
- **CON-003** — `calc/domains/loads_migrate.py` lit encore les clés `shown:` d'un ancien `show-calc` pour renommer les valeurs de neige et de vent d'un vieux projet : c'est une migration de fichiers anciens, pas la fenêtre ; elle reste (§8).
- **CON-004** — Aucune commande Typst ne change : pas de `///`, d'exemple ni de traduction de commande à écrire.
- **CON-005** — Documentation de fin de tâche : `CHANGELOG.md`, « Nouveautés » de la prochaine version en fr/de/en (une ligne : la sélection manuelle a quitté la fenêtre aussi), catalogue des tests si un fichier de test change de rôle. Source : CLAUDE.md.

## 7. Décisions prises

- **D-1** — La sélection manuelle −1 disparaît sans remplaçant dans la fenêtre (l'ingénieur, 22.10.2026, issue #93 ; la refonte a déjà retiré le −1 du moteur, les arguments d'affichage fins et `#var-table` le remplacent).
- **D-2** — #74 n'a plus de travail : ses pertes restantes (torsion, légende automatique d'un extrait) ont été laissées par l'ingénieur à la clôture de la refonte (spec `2026-10-21-commandes-typst-refonte`, §16, 22.10.2026) ; elles ne sont pas reprises ici.
- **D-4** — `eta_s` quitte la compression et la flexion simples sans forcer de régénération (Q-001, l'ingénieur, 22.10.2026) : les nouveaux domaines n'ont que `eta` ; dans les projets existants la ligne `eta_s` reste, inerte et juste, que l'ingénieur supprime à la main s'il le veut (« Régénérer » n'est proposé que si la forme change : il ne l'est pas ici). Prix accepté : un ancien domaine et un nouveau n'ont pas exactement les mêmes lignes. Écartés : forcer « Régénérer » par un changement de forme (du rouge dans chaque projet) et garder la ligne doublée. Reportée dans `docs/decisions.md`.
- **D-3** — Mode `big-feature` imposé par l'ingénieur (`/big-feature`), bien que #93 se décrive comme une petite modification (T8) : le nettoyage touche plusieurs modules, la documentation et un calcul (`eta_s`).

## 8. Hors périmètre

- `calc/domains/loads_migrate.py` et son test (`tests/test_loads_migrate.py`) : migration des anciens projets, gardée (CON-003).
- Les `level` par ligne encore présents dans `examples/data/calculations.json` et `connectors.json` (forme antérieure à 0.120) : autre sujet.
- L'issue #92 (liste des positions et métré créés depuis leurs onglets).
- Les paragraphes de `docs/` déjà marqués « retiré » et `docs/decisions.md` (déjà « [retired in v0.120] »), sauf une ligne de décision si Q-001 change la sortie.

## 9. Idées non retenues comme exigences

- T8 « Petite modification (small-feature) » : remplacé par le mode imposé (D-3).

## 10. Questions

### Q-001 — La ligne `eta_s` doublée d'une compression et d'une flexion simples
- **Pourquoi elle compte** : pour le niveau −1 (issue #58), une compression sans angle et une flexion (avec ou sans effort normal) écrivent deux lignes de même valeur : `eta_s` (le verdict de la section) puis `eta`. Les fichiers de domaine générés l'impriment donc deux fois (p. ex. `Timber-checks/Compression/DR-02.typ` : `#eq("eta_s", …)` puis `#eq("eta", …, unit: "%")`). Sans le −1, `eta_s` n'a plus de raison d'être dans ces deux cas (il garde la sienne dans le flambage et le déversement, où `eta` est le maximum de plusieurs verdicts). Le retirer allège les fichiers et le rapport, mais change la forme de chaque domaine de compression et de flexion : dans les projets existants, un fichier non modifié est réécrit à la régénération, un fichier modifié par l'ingénieur passe en alerte rouge (« forme qui ne correspond plus »), et la page d'or change.
- **Options** : **A (recommandée)** — garder les lignes `eta_s` telles quelles ; seule la condition de `check_command` est écrite dans `member_check.py` et le commentaire dit pourquoi la ligne existe. Aucun fichier de projet ne change. **B** — retirer `eta_s` de la compression sans angle et de la flexion ; fichiers régénérés, alerte rouge pour ceux que l'ingénieur a modifiés, page d'or et `tests/projet-exemple` mis à jour, décision dans `docs/decisions.md`.
- **Réponse** : 22.10.2026 — après une explication détaillée demandée par l'ingénieur (« Je souhaite vraiment supprimer le level moins 1 car il est remplacé par tous les arguments d'affichage fin »), et la vérification dans `unfold.status` qu'une ligne que Woodcore n'écrit plus reste inerte, sans alerte : **retirer, sans forcer** (option B ; une option C « retirer et proposer Régénérer » par changement de forme a été écartée). → REQ-007, D-4, CON-001.

## 11. Critères d'acceptation

- [x] REQ-001 — plus de genre `detail`, de −1, de `LevelControl` dans `display_options.py` / `display_view.py`
- [x] REQ-002 — `calc/shown_variables.py` et `lib/shown-variables.json` supprimés, condition `eta_s` dans `member_check.py`
- [x] REQ-003 — `shown_keys`, `shown_choices`, `_NOT_ROUND`, `FIRE_MEMBER_KEYS`, `LoadTab.shown_choices` et les imports morts retirés
- [x] REQ-004 — douze mots retirés en fr/de/en, `test_i18n` vert
- [x] REQ-005 — tests −1 retirés ou adaptés, garde ajouté
- [x] REQ-007 — plus de `eta_s` en compression et flexion simples ; flambage/déversement inchangés ; domaines existants sans alerte ; projet exemple réécrit
- [ ] REQ-006 — #74 et #93 fermées avec un commentaire (après accord de l'ingénieur)
- [x] UI-001 — volets « Affichage » et page d'or inchangés
- [x] ARCH-001 — `docs/` sans description actuelle de la sélection manuelle
- [x] ARCH-002 — `member_check.py` sans dépendance à la fenêtre
- [x] CON-001 à CON-003 — fichiers de domaine existants, homonymes `shown` et migration des charges intacts
- [x] Documentation : sections de `docs/` corrigées (ARCH-001), entrée `CHANGELOG.md`, « Nouveautés » de la prochaine version fr/de/en, catalogue des tests.
- [x] Tests : `tests/test_display_view.py`, `test_member_check.py`, `test_member_check_tab.py`, `test_i18n.py`, `test_report_golden.py`, `test_docs_coherence.py` ; suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-006, D-3 | capturé |
| T2 | REQ-001, D-1 | capturé |
| T3 | REQ-001, REQ-004 | capturé |
| T4 | REQ-001 | capturé |
| T5 | REQ-003 | capturé |
| T6 | REQ-002, REQ-007, Q-001 | capturé ; `check_command` encore lu → Q-001 répondue |
| T7 | REQ-004, REQ-005, ARCH-001 | capturé |
| T8 | — | idée / remplacé par D-3 (§9) |
| T9 | REQ-006, D-2 | capturé |

### Points de la source non résolus

- Aucun (T6 résolu par Q-001).

## 13. Revue d'architecture

Revue indépendante (`architecture-reviewer`, lecture du code, 2026-10-22). **Verdict : APPROUVER AVEC RÉSERVES** — réserves intégrées ci-dessous et au plan.

**Modules concernés.** `calc/tools/display_options.py` (`KINDS` :32, `LEVELS_SHOWN` :79, `SELECTION` :81, `LEVEL_SHOWN` :85, `DETAIL` :86, branche `detail` de `initial()` :582-584, douze mots par langue :300-311, :416-427, :532-543) ; `calc/tools/display_view.py` (`LevelControl` :122-226, branches `detail` de `SpecPanel` :326-331, :379, :402-404, :467-473, :507, :542) ; `calc/shown_variables.py` et `lib/shown-variables.json` (aucun lecteur Typst, absents de `project.ENGINE_FILES`) ; `calc/domains/member_check.py` (import :25, `FIRE_MEMBER_KEYS` :61, `_NOT_ROUND` :696, `shown_keys` :699, `shown_choices` :713, lignes `eta_s` :917-919 et :1014-1015 ; celles de :1235-1347 sont le flambage et le déversement, qui restent) ; `calc/domains/unfold.py` (n'en sait rien : `_generate_member` écrit chaque ligne de `result["rows"]`) ; imports morts `connectors_tab.py:34`, `woodcore_gui.py:82`, `load_tab.py:30` (+ `shown_choices` :617-627), `member_check_tab.py:43`, `_actions.py:21`, `_form.py:17`.

**Ce qui lit `eta_s` en compression/flexion simples : rien.** `governing_ratio` (:719-729) ne le lit que sous un `eta` en `max(` (flambage, déversement) ; aucun `eta_s` dans `lib/*.typ` ; `lib/line-levels.json:257` reste pour le flambage/déversement ; acier indépendant ; la ligne `eta` ne dépend pas d'`eta_s` (ses `keys` viennent de la relation ou de sa propre formule).

**Ancien fichier qui garde `#eq("eta_s", …)` : confirmé sans effet.** `status` (:871-888) n'itère que sur l'écriture neuve, `matches` ne compare que `form_of` au `gen` de la base ; `refresh`, `domain_state`, `import_lines`, `take_back`, `reinsert` ne voient pas la ligne ; l'entrée `eq:eta_s` restante de la base n'est jamais consultée ; Typst ne vérifie que le type d'un `id:` ; `regenerate` (:1178-1189) retire une ligne hors de l'écriture neuve que l'ingénieur n'a pas modifiée.

**Risques.**
- **ARCH-RISK-001 (important)** — `tests/test_member_check.py:652,653,661,662` : `ORACLE_RECORDS` nomme la ligne `eta_s` de flexions simples → `{"eta": "eta_s"}` (clé Woodcore d'abord, clé de l'oracle ensuite). `:552` (déversement) reste.
- **ARCH-RISK-002 (important)** — `examples/Timber-checks/` est une copie gelée des mêmes fichiers (`build_examples.py --freeze`) ; la page d'or hache des pages SVG : une ligne de moins décale toutes les pages `rs` à partir du premier domaine concerné, dans chaque variante → UI-001 reformulé, raison dans `CHANGES`.
- **ARCH-RISK-003 (important)** — `tests/projet-exemple/Timber-checks/unfold.json` a 8 `eq:eta_s` ; seuls ceux de BI-01, BI-02, FE-01, DR-02 partent → retirer par identifiant (fichier + entrée de base), puis `member_check.export(here)` qui réécrit seulement les domaines absents.
- **ARCH-RISK-004 (important)** — résidus plus larges : imports `chrome` (:20) et `flowbar` (:22) de `display_view.py` deviennent morts, `CHANGED["detail"]` (`tests/test_display_view.py:82`), commentaires `display_options.py:13,31,43,80`, `member_check.py:60` → pyflakes sur les fichiers touchés.
- **ARCH-RISK-005 (mineur)** — le feu est couvert aussi (`_lines` :822 → `_compute_section`) : dit dans REQ-007, testé.
- **ARCH-RISK-006 (mineur)** — même `gen` pour un ancien et un nouveau domaine aux lignes différentes : une phrase au commentaire de `GENERATOR_VERSION` et dans la décision.
- **ARCH-RISK-007 (mineur)** — « Régénérer » retire la ligne ancienne : dit dans REQ-007, D-4, `docs/domain/member-checks.md`.
- **ARCH-RISK-008 (mineur)** — la carte « Résultats » (`member_check_tab_form.py:270`) perd aussi la ligne : dit dans UI-001.
- **ARCH-RISK-009 (mineur)** — docs : `docs/domain/member-checks.md:32,36,38,78` (plus de parité Python/Typst sur `eta_s`), `docs/ui/window.md:85`, `docs/typst/report-engine.md:41,51`, `docs/architecture/data-contracts.md:137`, `docs/architecture/layout.md:61,289`, `docs/open-questions.md:19`, `docs/domain/calculation-domains.md:20`, `docs/ui/tab-member-checks.md:9`, catalogues des tests.

**Approche.** Trois lots qui gardent les tests verts : (1) calcul + exemples + page d'or ensemble ; (2) fenêtre ; (3) `member_check` débarrassé de l'import, puis suppression du module et du JSON ; puis la documentation.

## 14. Plan d'implémentation

1. **Calcul `eta_s` (REQ-007, ARCH-002, CON-001)** — `calc/domains/member_check.py` : retirer les deux `rows.append(_row("eta_s", …))` (compression sans angle, flexion sans angle) et leurs commentaires ; `calc/domains/unfold.py` : une phrase au commentaire de `GENERATOR_VERSION` (ARCH-RISK-006). Tests : `test_member_check.py` nouveau `test_a_simple_compression_and_a_simple_bending_have_no_eta_s_row` (compression, flexion avec et sans N, feu ; flambage et déversement gardent `eta_s`), `ORACLE_RECORDS` corrigé (ARCH-RISK-001) ; `test_unfold.py` nouveau `test_a_domain_that_keeps_a_line_the_writer_no_longer_writes_is_in_step` (matches, ni missing ni conflict, refresh vide, domain_state propre, regenerate la retire).
2. **Projet exemple (REQ-007, ARCH-RISK-002/003)** — sur `tests/projet-exemple/` seulement : retirer `Bending/BI-01.typ`, `BI-02.typ`, `FE-01.typ`, `Compression/DR-02.typ` et leurs entrées de `Timber-checks/unfold.json`, puis `member_check.export(here)` ; `git diff` : seules ces quatre entrées et ces quatre fichiers changent ; `python calc/tools/build_examples.py --freeze` pour `examples/` ; page d'or renouvelée (`WOODCORE_UPDATE_GOLDEN=1`) avec sa raison dans `CHANGES`. Tests : `test_unfold` (octet pour octet), `test_report_golden`.
3. **Fenêtre (REQ-001, REQ-003, REQ-004)** — `display_options.py` : `detail` hors de `KINDS`, `LEVELS_SHOWN`, `SELECTION`, `LEVEL_SHOWN`, `DETAIL`, branche `initial()`, douze mots × 3 langues, docstrings ; `display_view.py` : `LevelControl`, les branches `detail`, imports `chrome`/`flowbar` ; `load_tab.py` : `shown_choices` et l'import ; imports morts de `connectors_tab.py`, `woodcore_gui.py`, `member_check_tab*.py`. Tests : `test_display_view.py` (deux tests −1 retirés, `test_every_level_a_panel_offers_compiles` adapté, `CHANGED["detail"]` retiré, nouveau garde REQ-005 hors `tests/`), `test_i18n`, `test_member_check_tab`, `test_connectors*`, `test_load_tab*` ; pyflakes.
4. **Domaine et suppression (REQ-002, REQ-003)** — `member_check.py` : import, `FIRE_MEMBER_KEYS`, `_NOT_ROUND`, `shown_keys`, `shown_choices` ; puis `git rm calc/shown_variables.py lib/shown-variables.json`. Tests : `test_member_check`, le garde ; `test_display.py` en-tête orphelin, docstring de `test_line_levels.py`.
5. **Documentation (ARCH-001, CON-005)** — les sections d'ARCH-RISK-009 ; décision D-4 dans `docs/decisions.md` (+ index) avec « Régénérer » ; `CHANGELOG.md` ; « Nouveautés » de la prochaine version fr/de/en ; catalogues des tests. Test : `test_docs_coherence`.
6. **Fin (REQ-006)** — vérification indépendante, suite complète, `finish` : un commit, la question « Pousser et fermer les issues ? », #74 et #93 fermées avec un commentaire.

## 15. Vérification

Vérification indépendante (`requirements-verifier`, base `699038dc`, arbre de travail), un tour, 2026-10-22. Tests lancés par le vérificateur : `test_display_view` 13, `test_member_check` (+ `_tab`) 76, `test_member_check_tab` 40, `test_unfold` 23, `test_i18n` 22, `test_docs_coherence` 7, `test_report_golden` 1, `test_display` 24, `test_line_levels` 6, `test_loads_migrate` 5, `test_connectors` 69 (3 ignorés), `test_load_tab` 5 — aucun échec.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `display_options.KINDS` sans `detail` ; `LEVELS_SHOWN`, `SELECTION`, `LEVEL_SHOWN`, `DETAIL`, branche `initial()` retirés ; `LevelControl` et ses branches hors de `display_view.py`, imports `chrome`/`flowbar` retirés ; `test_display_view.test_every_level_a_panel_offers_compiles` |
| REQ-002 | ✅ | `calc/shown_variables.py`, `lib/shown-variables.json` supprimés (`git rm`) ; `check_command` parti avec la ligne `eta_s` ; ⚠️ du critère littéral levé : il listait mal les exceptions (garde, décisions, paragraphes « retiré », specs anciennes), critère précisé |
| REQ-003 | ✅ | `FIRE_MEMBER_KEYS`, `_NOT_ROUND`, `shown_keys`, `shown_choices`, `LoadTab.shown_choices` et les imports morts retirés ; `test_member_check_tab` 40, `test_connectors` 69, `test_load_tab` 5 |
| REQ-004 | ✅ | 12 clés × 3 langues retirées ; garde ; `test_i18n` 22 |
| REQ-005 | ✅ | deux tests −1 retirés, test des niveaux adapté, `CHANGED["detail"]` retiré, garde `test_the_manual_selection_is_gone_from_the_window` ; `test_display.py`, `test_line_levels.py` |
| REQ-006 | ⏳ | #74 et #93 ouvertes : fermées par `finish` après la réponse de l'ingénieur à « Pousser et fermer les issues ? » |
| REQ-007 | ✅ | les deux `eta_s` retirés ; flambage, déversement, `governing_ratio` inchangés ; `test_member_check.test_a_simple_compression_and_a_simple_bending_have_no_eta_s_row`, `test_unfold.test_a_domain_that_keeps_a_line_the_writer_no_longer_writes_is_in_step`, `test_unfold.test_the_example_projects_unfolded_checks_are_written_byte_for_byte_as_held` ; `unfold.json` 8 → 4 `eq:eta_s` (FE-02, KN-01, KI-01, KI-02 gardés) ; `form_of` et `GENERATOR_VERSION` inchangés |
| UI-001 | ✅ | aucune chaîne ajoutée à la fenêtre ; `test_report_golden` vert sans page renouvelée |
| ARCH-001 | ✅ | docs corrigées, histoire dans `docs/history/2026-10-22-niveau-manuel.md` (indexée) ; ⚠️ levé : la phrase résiduelle de `docs/domain/member-checks.md:68` (« `shown:` and the level -1 are, for it, the file's ») dit maintenant le retrait ; `test_docs_coherence` 7 |
| ARCH-002 | ✅ | `member_check.py` sans `display_*` ni Qt |
| CON-001 à CON-004 | ✅ | test du domaine ancien ; `lib/line-levels.json`, `schemas/`, `renamed-commands.json`, `loads_migrate.py`, `lib/*.typ` hors du diff |
| CON-005 | ✅ | `CHANGELOG.md` v0.123, « Nouveautés » 0.123.0 fr/de/en, `project.VERSION` 0.123.0, deux décisions et l'index, catalogues ; ⚠️ levé : les liens vers `completed/` résolus par le déplacement de la spec |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-22 | draft | spécification extraite des issues #74 et #93 ; restes cartographiés (code-scout) : le moteur est déjà propre, la chaîne −1 de la fenêtre est morte, seule `shown_variables.check_command` est encore lue (ligne `eta_s` d'une compression) ; #74 sans travail restant ; 1 question |
| 2026-10-22 | specified | Q-001 répondue (après explication détaillée) : `eta_s` retiré de la compression et de la flexion simples, sans forcer de régénération → REQ-007, D-4 ; CON-001 vérifié dans `unfold.status` |
| 2026-10-22 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (9 risques, intégrés : oracle de flexion, copie `examples/`, page d'or plus large, base par identifiant, imports morts, feu, carte « Résultats », « Régénérer », docs) ; plan en 6 étapes |
| 2026-10-22 | approved | approuvée par l'ingénieur (« Approuver et implémenter ») ; base `699038dc` |
| 2026-10-22 | implementation | étape 1 (REQ-007, ARCH-002, CON-001) : les deux lignes `eta_s` retirées de `member_check._compute_section` (compression sans angle) et de la flexion sans angle ; phrase au commentaire de `GENERATOR_VERSION` ; `ORACLE_RECORDS` lit `eta` (ARCH-RISK-001) ; nouveaux tests `test_member_check.test_a_simple_compression_and_a_simple_bending_have_no_eta_s_row` (normal, N±, feu ; flambage et déversement gardent `eta_s`) et `test_unfold.test_a_domain_that_keeps_a_line_the_writer_no_longer_writes_is_in_step` (matches, ni missing ni conflict, refresh vide, domain_state propre, export sans toucher le fichier, regenerate retire la ligne) |
| 2026-10-22 | implementation | étape 2 : BI-01, BI-02, FE-01, DR-02 retirés de `tests/projet-exemple/Timber-checks/` avec leurs entrées de base puis réécrits par `member_check.export` (diff : une ligne par fichier, quatre `eq:eta_s` de la base ; les effets de bord de l'export partiel sur `checks.json` et `formulas.json` — champs `file`, une entrée de script — remis à leur contenu de HEAD) ; copiés tels quels dans `examples/Timber-checks/` (ce que `--freeze` aurait fait pour eux, sans réécrire tout l'instantané). Page d'or : **inchangée** — le rapport de statique du projet exemple n'inclut aucun contrôle de barre (la revue l'avait supposé) ; UI-001 tenu sans nouvelle page |
| 2026-10-22 | implementation | étape 3 (REQ-001, REQ-003, REQ-004) : `display_options.py` sans `detail`, `LEVELS_SHOWN`, `SELECTION`, `LEVEL_SHOWN`, `DETAIL`, branche `initial()`, paragraphe du docstring, douze mots × 3 langues (36 lignes) ; `display_view.py` sans `LevelControl`, ses six branches, imports `chrome`/`flowbar` ; `LoadTab.shown_choices` et imports morts (`connectors_tab`, `woodcore_gui`, `load_tab`, `member_check_tab*`) ; `test_display_view.py` : deux tests −1 retirés, test des niveaux adapté (`-1` jamais offert), `CHANGED["detail"]` retiré, garde `test_the_manual_selection_is_gone_from_the_window` |
| 2026-10-22 | implementation | étape 4 (REQ-002, REQ-003) : `member_check.py` sans l'import, `FIRE_MEMBER_KEYS`, `_NOT_ROUND`, `shown_keys`, `shown_choices` ; `git rm calc/shown_variables.py lib/shown-variables.json` ; en-tête orphelin de `test_display.py`, docstring de `test_line_levels.py` |
| 2026-10-22 | implementation | étape 5 (ARCH-001, CON-005) : paragraphes décrivant le −1 comme actuel déplacés tels quels dans `docs/history/2026-10-22-niveau-manuel.md` (window.md, tab-member-checks.md, member-checks.md ×2, report-engine.md §4 et son pas 5, data-contracts.md) et remplacés par l'état actuel ; `calculation-domains.md`, `layout.md` (deux fichiers retirés), question ouverte sur le −1 fermée (`docs/history/open-questions-closed.md`), trois catalogues des tests ; deux décisions dans `docs/decisions.md` (+ index) ; `CHANGELOG.md` v0.123 ; `calc/project.py` 0.123.0 ; « Nouveautés » 0.123.0 fr/de/en. Précision trouvée en route : le bouton « Régénérer » n'est actif que si la forme a changé (`formula_tab_unfold.py:134`) — l'ancienne ligne `eta_s` se supprime donc à la main ; Nouveautés, docs et D-4 le disent |
| 2026-10-22 | testing | tests liés aux fichiers modifiés : 1446 passés, 4 ignorés, aucun échec (910 s) ; puis `test_docs_coherence` (le fichier d'histoire indexé dans `docs/README.md`), `test_display_view` (13), `test_i18n` (22), `test_unfold` (23), `test_report_golden` (1) verts |
| 2026-10-22 | verification | vérification indépendante, un tour : tout ✅ sauf REQ-006 (après le push) et trois ⚠️ mineurs, levés (phrase résiduelle de `member-checks.md:68`, critère de REQ-002 précisé, liens `completed/` par le déplacement) ; §15 écrit, §11 coché sauf REQ-006 |
| 2026-10-22 | completed | spécification déplacée dans `docs/requirements/completed/` ; reste REQ-006 : fermer #74 et #93 par `finish`, après l'accord de l'ingénieur |
