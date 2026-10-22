---
id: 2026-10-16-plans-copier-coller-entre-plans
titre: Plan de positions et plan incendie — sélection multiple, copier-coller entre plans (issue #61)
status: completed
cree: 2026-10-16
mis_a_jour: 2026-10-16
source: issue GitHub #61 (demande de Gian du 2026-10-14) ; demande «implémente tous les issues de github», périmètre réduit à #61 par l'ingénieur le 2026-10-16
docs: [docs/ui/tab-plans.md, docs/domain/position-plans.md, docs/domain/fire-plans.md, docs/ui/tab-fire.md, docs/architecture/principles.md]
---

# Sélection multiple et copier-coller entre plans — Spécification

## 1. Objectif

Dessiner un étage une fois et le reprendre sur les autres : sélectionner plusieurs objets d'un plan de positions (Ctrl+clic, Ctrl+A), les copier avec un point de base (Ctrl+C), ouvrir un autre plan et les coller ensemble à l'endroit cliqué (Ctrl+V), chaque élément collé recevant le numéro suivant de son préfixe sur l'étage du plan cible. Même fonctionnement entre plans de protection incendie. Suite de #18 («Copier» dans un même plan), qui reste inchangé.

## 2. Source

Issue #61, mot pour mot.

> **T1** — « Onglets «Plan de positions» et «Plan de protection incendie» (`docs/ui/tab-plans.md`). Aujourd'hui, on ne sélectionne qu'un objet à la fois, et «Copier» (#18) ne pose des copies que dans le même plan. Demande de Gian du 2026-10-14 : copier ce qui est dessiné sur un plan (par exemple le sous-sol), passer à un autre plan (par exemple le rez-de-chaussée) et y coller tous les objets sélectionnés. Suite de #18 (fermée). »
>
> **T2** — « Permettre de sélectionner plusieurs objets sur un plan : Ctrl+clic ajoute un objet à la sélection ou l'en retire ; Ctrl+A sélectionne tout ce qui est dessiné sur le plan, sauf le contour du bâtiment. »
>
> **T3** — « Copier la sélection avec Ctrl+C : Woodcore demande alors un point de base, à cliquer sur le plan. »
>
> **T4** — « Ouvrir un autre plan et coller avec Ctrl+V : tous les objets copiés arrivent ensemble, avec leur point de base à l'endroit cliqué sur le nouveau plan. »
>
> **T5** — « Aucun bouton n'est ajouté dans la barre, et le bouton «Copier» actuel (copie répétée dans le même plan) ne change pas. »
>
> **T6** — « Donner de nouveaux numéros de position aux éléments collés : chacun prend le numéro suivant de son préfixe sur l'étage du plan cible (S201, S202… au 2e étage), selon la numérotation par étage de #9. »
>
> **T7** — « Ne copier le contour du bâtiment que s'il a été sélectionné à la main (Ctrl+clic), jamais par Ctrl+A. »
>
> **T8** — « Même fonctionnement dans l'onglet «Plan de protection incendie», entre plans incendie, mais jamais d'un plan de positions vers un plan incendie. »
>
> **T9** — « Questions ouvertes — Un plan n'a qu'un contour du bâtiment (#54). Si on colle un contour sur un plan qui en a déjà un : remplacer l'ancien / laisser le contour collé de côté avec un message. »

## 3. Exigences fonctionnelles

### REQ-001 — Sélection multiple du plan de positions
- **Exigence** : Woodcore doit garder sur le canevas du plan de positions une sélection de plusieurs objets, de tout genre (élément, axe, ligne et boîte d'étage, niveau de reprise, cote, aide, texte, contour). Ctrl+clic sur un objet l'ajoute à la sélection ou l'en retire, et un clic simple remplace la sélection. Le dernier objet ajouté est l'objet « en focus », celui que le volet de droite montre et dont on tire les poignées (comportement du plan incendie, `FireCanvas.select_ids`).
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran. Deux Ctrl+clics sur deux éléments donnent une sélection de 2. Un troisième Ctrl+clic sur le premier le retire. Un clic simple ne laisse que l'objet cliqué. Les objets sélectionnés sont tous dessinés en orange `plan-select`.

### REQ-002 — Ctrl+A
- **Exigence** : Ctrl+A, le canevas ayant le focus, doit sélectionner tout ce que le plan porte (toutes les listes de `plan.ENTRY_LISTS`), sauf le contour du bâtiment. Sur le plan incendie, Ctrl+A sélectionne toutes les entrées (`fire.ENTRY_COLLECTIONS`).
- **Source** : T2, T7
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran. Sur un plan avec 3 éléments, 1 axe et un contour, Ctrl+A sélectionne 4 objets, et le contour n'en fait pas partie.

### REQ-003 — Les outils d'édition agissent sur toute la sélection
- **Exigence** (implicite, inférée de T2 et de la cohérence avec le plan incendie, §2 règle 16) : «Déplacer», «Supprimer» (et Delete) agissent sur toute la sélection, en un seul pas d'«Annuler». «Copier» et «Dupliquer» copient toute la sélection sauf le contour, qui reste unique dans son plan, comme aujourd'hui. Avec un objet sélectionné, le comportement de #18 est inchangé.
- **Source** : T2, T5 (inféré)
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran. Deux éléments sélectionnés et déplacés de (10, 0) : leurs deux points ont bougé, et un Ctrl+Z les remet en place. La même sélection supprimée disparaît en un pas.

### REQ-004 — Ctrl+C et le point de base
- **Exigence** : Ctrl+C, avec une sélection non vide, doit mettre le canevas dans l'état « point de base ». L'indication sous le plan le dit, le clic suivant (accroché comme tout point du plan) fixe le point de base, et la sélection est alors copiée dans un presse-papiers propre à Woodcore, avec le point de base. Escape annule. Sans sélection, Ctrl+C ne fait rien d'autre que l'indiquer.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran. Ctrl+C puis un clic en (100, 50) : le presse-papiers contient les objets sélectionnés, tels quels (copies profondes), le point (100, 50) et le genre de plan d'origine. Le plan n'a pas changé (pas de pas d'«Annuler»).

### REQ-005 — Ctrl+V sur un autre plan (ou le même)
- **Exigence** : Ctrl+V, le presse-papiers étant du même genre de plan, doit montrer les objets copiés qui suivent le pointeur (aperçu orange, comme «Copier»). Un clic les pose : chaque objet est décalé de (point cliqué − point de base) et ajouté au plan, le tout en un seul pas d'«Annuler». Les objets collés deviennent la sélection et l'outil revient à «Sélection». Escape annule le collage. Le collage peut être répété sur d'autres plans tant que le presse-papiers n'est pas remplacé.
- **Source** : T4
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran. Copier deux éléments du plan A avec la base (100, 50), ouvrir le plan B, Ctrl+V puis un clic en (300, 80) : B porte deux éléments décalés de (200, 30). Ctrl+Z les retire. A n'a pas changé.

### REQ-006 — Numéros des éléments collés
- **Exigence** : chaque élément collé qui porte un numéro de position reçoit le numéro suivant de son préfixe sur l'étage du plan cible (`positions_store.propose_id`, sur les positions du projet, les numéros déjà dessinés et ceux attribués dans le même collage). La position nouvelle reprend la section (type, section, dimension) de la position de l'élément copié, connue du projet ou en attente dans le plan d'origine, comme `on_new_element` le fait pour un élément dessiné. Une charge (PL, LL) reçoit le numéro suivant du plan (`next_load_label`). Un élément sans numéro le reste. Deux éléments copiés qui partagent un numéro (deux occurrences d'une même position) partagent aussi leur nouveau numéro : la correspondance ancien → nouveau est faite une fois par numéro (revue, ARCH-RISK-103). Un collage dans le plan d'origine renumérote lui aussi, à la différence de «Copier», qui garde le numéro (D-005). Les sections sont lues au moment de Ctrl+C et gardées dans le presse-papiers.
- **Source** : T6
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran. Copier S101 et S102 d'un plan d'étage `1` et les coller sur un plan d'étage `2` qui a déjà S201 : les éléments collés portent S202 et S203. Leurs positions en attente portent la section de S101 et de S102.

### REQ-007 — Le contour du bâtiment
- **Exigence** : le contour n'entre dans le presse-papiers que s'il était dans la sélection, c'est-à-dire choisi à la main (clic ou Ctrl+clic), jamais par Ctrl+A. Collé sur un plan qui a déjà un contour, il **remplace l'ancien**, dans le même pas d'«Annuler» que le reste du collage (réponse de l'ingénieur, 2026-10-16).
- **Source** : T7, T9
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran. Un contour copié et collé sur un plan qui a un autre contour : le plan cible a un seul contour, celui qui a été collé et décalé. Ctrl+Z rend l'ancien.

### REQ-008 — Plan incendie
- **Exigence** : sur le plan incendie, Ctrl+A, Ctrl+C (point de base) et Ctrl+V fonctionnent de la même manière entre plans incendie. Chaque entrée collée reçoit un identifiant à elle (`fire.next_id`). Un presse-papiers d'un plan de positions n'est jamais collé sur un plan incendie, ni l'inverse : Ctrl+V le refuse avec un message.
- **Source** : T8
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran. Deux zones copiées d'un plan incendie et collées sur un autre ont des identifiants nouveaux, uniques dans le plan cible. Un Ctrl+V sur le plan incendie après un Ctrl+C sur le plan de positions ne change rien et affiche le message de refus.

### REQ-009 — Entrées que le plan cible ne peut pas porter
- **Exigence** (inférée de `plan.check_source`, étendue par la revue, ARCH-RISK-104) : une entrée que le plan cible refuserait est laissée de côté, avec les prédicats mêmes de `check_source`. Cela vise les lignes d'étage, les boîtes d'étage et les niveaux de reprise hors d'une coupe, les charges PL et LL hors d'un plan de descente des charges (`loadpath`), et le contour sur une coupe (`plan_centres.applies`). Un axe qui coïncide avec un axe du plan cible (même ligne, même angle) est aussi laissé de côté, puisque la trame est la même d'un étage à l'autre. Un message dit combien d'entrées sont laissées de côté. Les autres axes sont nommés par leur place (`insert_axis`), et les renommages sont réunis en un seul signal.
- **Source** : T4 (inféré)
- **Priorité** : doit
- **Critère d'acceptation** : test du domaine. Une ligne d'étage et un élément collés sur un plan d'étage : seul l'élément est ajouté, et le résultat dit « 1 laissé de côté ». Le plan cible passe `check_source`, et ce contrôle figure dans chaque test de collage. Un axe identique à un axe du plan cible n'est pas dupliqué.

### REQ-010 — Plans d'échelles différentes
- **Exigence** : quand le plan d'origine et le plan cible ont tous deux une échelle (`units_per_m`), la géométrie collée est mise à l'échelle autour du point de base, avec le rapport cible/origine. Sont mis à l'échelle : les `points` (éléments, lignes d'étage, niveaux de reprise, cotes, textes, contour, et toutes les entrées incendie avec les `holes` des zones), le `point` des axes et des aides, `x`, `y`, `w`, `h` des boîtes d'étage, et l'`offset` des cotes (revue, ARCH-RISK-105). Ne changent pas : `label_offset`, `angle`, `diagonal`, `span`, `style`, et la taille des symboles et des textes. L'échelle d'un plan est celle de son cadre (`frame_source()`), ce qui donne aussi celle d'un plan incendie qui suit un plan de positions. Si l'un des deux plans n'a pas d'échelle, rien n'est mis à l'échelle et l'indication le dit.
- **Source** : Q-001 (réponse A)
- **Priorité** : doit
- **Critère d'acceptation** : test du domaine. Un mur de 100 unités copié d'un plan au 1:100 et collé sur un plan au 1:50 mesure 200 unités, et son premier point est sur le point cliqué quand c'était le point de base.

## 4. Exigences d'interface

### UI-001 — Raccourcis seulement, aucun bouton
- **Exigence** : Ctrl+A, Ctrl+C et Ctrl+V sont des raccourcis du canevas (`Qt.WidgetShortcut`, comme les lettres des outils), pour que Ctrl+C dans un champ de texte reste la copie du texte. Aucun bouton n'est ajouté à la barre. «Copier» ne change pas.
- **Source** : T5
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran. Ctrl+C dans le champ de numéro ne remplit pas le presse-papiers de Woodcore. La barre a le même nombre de boutons qu'avant.

### UI-002 — Indications et messages
- **Exigence** : l'indication sous le plan, dans les trois langues, pour : « cliquer le point de base », « cliquer où poser les objets copiés », « copié : n objets » ; et les messages « rien à coller », « un presse-papiers d'un plan de positions ne se colle pas sur un plan incendie » (et l'inverse), « n objets laissés de côté : ce plan n'est pas une coupe », « contour remplacé ». Les tooltips de «Sélection» mentionnent Ctrl+clic, Ctrl+A, Ctrl+C et Ctrl+V.
- **Source** : T2–T4, T8 (inféré)
- **Langues** : fr / de / en
- **Critère d'acceptation** : chaque clé existe dans `plan_tab_words.py` et `fire_tab_words.py` dans les trois langues (`tests/test_i18n*`).

### UI-003 — Volet de droite avec plusieurs objets sélectionnés
- **Exigence** (inférée) : le volet de droite et la carte « Objet sélectionné » montrent l'objet en focus. Le titre de la carte dit le nombre d'objets quand il y en a plus d'un.
- **Source** : T2 (inféré)
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran. Avec deux éléments sélectionnés, le champ du numéro montre celui du dernier ajouté.

## 5. Exigences d'architecture

### ARCH-001 — Le collage est une fonction du domaine
- **Exigence** : ce qui est copié et la façon dont il est posé (décalage, numérotation, contour remplacé, entrées refusées, axes renommés) sont des fonctions de `calc/domains/plan.py` (`clip_entries`, `paste_entries`) et de `calc/domains/fire.py`, sans Qt. Le canevas ne fait que les appeler (principe « le domaine est indépendant de l'UI »).
- **Source** : CLAUDE.md, principes 2 et 16
- **Critère d'acceptation** : les tests du domaine appellent `paste_entries` sans QApplication. `tests/test_module_imports.py` reste vert.

### ARCH-002 — Un seul presse-papiers, en mémoire
- **Exigence** : le presse-papiers est un objet unique du processus, partagé par les onglets, qui porte son genre (`position` ou `fire`), le projet d'où il vient et l'échelle de son plan d'origine ; il est propre au projet, puisque Woodcore n'ouvre qu'un projet par processus (`woodcore_gui.open_project`). Il garde en plus la racine du projet, et un collage dont la racine diffère du projet courant est refusé (D-004, corrigée par la revue, ARCH-RISK-102). Le contenu est dans `calc/domains/plan_clip.py` (sans Qt), le détenteur unique dans `calc/tools/plan_clipboard.py`. Il n'est pas écrit sur le disque et n'utilise pas le presse-papiers du système. Aucun fichier, schéma ou contrat ne change.
- **Source** : T4, T8 (inféré)
- **Critère d'acceptation** : aucune version de schéma ne change (`plan-source` 1.8, `fire-source`). Un test montre que le presse-papiers survit au changement de plan dans l'onglet.

### ARCH-003 — La sélection unique reste lisible
- **Exigence** : `PlanCanvas.selection` reste l'objet en focus, `(kind, index)` ou None, pour le code qui le lit aujourd'hui. La liste complète devient `selected_entries`. Le plan incendie garde sa liste d'identifiants.
- **Source** : principe 15 (préserver l'architecture) (inféré)
- **Critère d'acceptation** : la suite existante des plans (`test_plan_*`, `test_fire_*`) passe sans modification de ses assertions sur la sélection unique.

### ARCH-004 — Sélection multiple : focus et `extra` (revue)
- **Exigence** : `PlanCanvas.selection` devient une propriété (le focus). Son setter vide `extra`, qui n'est rempli que par `select(..., add=True)` et `select_all`. Ce schéma est celui de `SchemaCanvas.select(add=True)`. `entry_at(raw)` est extrait de `press_select` (ce qui est sous le pointeur, sans drag), et `entry_outline(kind, entry, dx, dy)` de `selection_outline` : un seul tracé sert à l'aperçu, au collage et au dessin de la sélection. Les indices sont élagués à chaque `changed`.
- **Source** : revue (ARCH-RISK-101)
- **Critère d'acceptation** : `add_element` et les autres assignations directes laissent une sélection d'un seul objet. Après un Ctrl+Z, aucun indice ne déborde.

## 6. Contraintes

- **CON-001** — Le bouton «Copier» et sa copie répétée (D-014 de #18) ne changent pas pour un objet seul. Source : T5.
- **CON-002** — Jamais d'un plan de positions vers un plan incendie (ni l'inverse). Source : T8.
- **CON-003** — Pas de nouvelle version de schéma : un plan collé est un plan dessiné à la main. Source : inférée (principe 4).
- **CON-004** — Trois langues pour tout texte visible. Source : CLAUDE.md.

## 7. Décisions prises

- **D-001** — Périmètre : #61 seule parmi les issues ouvertes (l'ingénieur, 2026-10-16). Les autres issues demandent la bibliothèque de normes absente de cette session ou un autre dépôt. #54 et #46, déjà implémentées, seront fermées au push avec un commentaire.
- **D-002** — Un contour collé sur un plan qui en a un remplace l'ancien (l'ingénieur, 2026-10-16, réponse à T9).
- **D-003** — Entre deux plans d'échelles différentes, la géométrie collée est mise à l'échelle autour du point de base (Q-001, réponse A). Ce qu'on accepte de payer : un objet collé depuis un plan sans échelle n'est pas corrigé.
- **D-004** — Le presse-papiers ne vit que dans un projet (Q-002, réponse A). La forme est précisée par la revue : il n'y a pas de changement de projet en cours de processus, et le presse-papiers garde la racine de son projet, si bien qu'un collage ailleurs est refusé.
- **D-005** — «Copier» (#18) garde le numéro de position, et Ctrl+V renumérote toujours, même dans le plan d'origine (T6 ; à consigner dans `docs/decisions.md`).

## 8. Hors périmètre

- Coller d'un plan de positions vers un plan incendie, et l'inverse (T8).
- Un bouton dans la barre (T5).
- Le presse-papiers du système d'exploitation, et le collage entre deux fenêtres de Woodcore.
- Les autres onglets de dessin (Schémas, Modèles statiques).

## 9. Idées non retenues comme exigences

- « par exemple le sous-sol … le rez-de-chaussée » (T1) : exemple d'usage, pas une contrainte sur les étages.

## 10. Questions

### Q-001 — Deux plans d'échelles différentes
- **Pourquoi elle compte** : les points sont en unités de la feuille. Un plan au 1:100 collé sur un plan au 1:50 sans correction donnerait des objets deux fois trop petits par rapport au bâtiment.
- **Options** : A (recommandée) mettre à l'échelle autour du point de base selon le rapport des `units_per_m`, quand les deux plans ont une échelle (rien sinon) ; B coller en unités de la feuille, sans correction.
- **Réponse** : A — mettre à l'échelle (l'ingénieur, 2026-10-16) → REQ-010, D-003.

### Q-002 — Coller dans un autre projet
- **Pourquoi elle compte** : la section d'une position collée vient du projet d'origine.
- **Options** : A (recommandée) le presse-papiers est vidé quand un autre projet est ouvert ; B le collage est permis, les sections reprises telles quelles.
- **Réponse** : A — vidé en changeant de projet (l'ingénieur, 2026-10-16) → ARCH-002, D-004.

## 11. Critères d'acceptation

- [x] REQ-001 — Ctrl+clic ajoute ou retire, un clic simple remplace, tout est dessiné en orange.
- [x] REQ-002 — Ctrl+A sélectionne tout sauf le contour.
- [x] REQ-003 — Déplacer et Supprimer agissent sur toute la sélection, Copier et Dupliquer sur toute la sélection sauf le contour, chaque fois en un pas.
- [x] REQ-004 — Ctrl+C demande le point de base, puis remplit le presse-papiers sans changer le plan.
- [x] REQ-005 — Ctrl+V pose les objets, base sur le clic, en un pas d'«Annuler».
- [x] REQ-006 — S202 et S203 sur le plan d'étage 2, avec la section reprise.
- [x] REQ-007 — Le contour collé remplace l'ancien, et Ctrl+Z rend l'ancien.
- [x] REQ-008 — Le plan incendie a de nouveaux identifiants, et le collage entre genres de plans est refusé.
- [x] REQ-009 — Les entrées de coupe sont laissées de côté sur un plan d'étage, avec un message.
- [x] REQ-010 — Un mur de 100 unités au 1:100 en mesure 200 au 1:50, mis à l'échelle autour du point de base.
- [x] UI-001 — Raccourcis du canevas seulement, aucun bouton, «Copier» inchangé.
- [x] UI-002 — Les messages existent dans les trois langues.
- [x] UI-003 — Le volet montre l'objet en focus.
- [x] ARCH-001 — Le collage est dans le domaine, sans Qt.
- [x] ARCH-002 — Presse-papiers en mémoire, aucun schéma changé.
- [x] ARCH-004 — `selection` en propriété avec `extra`, `entry_at` et `entry_outline` extraits.
- [x] ARCH-003 — `selection` reste l'objet en focus, et les tests existants passent.
- [x] Documentation : `docs/ui/tab-plans.md`, `docs/domain/position-plans.md`, `docs/domain/fire-plans.md` / `docs/ui/tab-fire.md`, `docs/decisions.md` (D-002, le presse-papiers), `CHANGELOG.md`, «Nouveautés» fr/de/en.
- [x] Tests : `tests/test_plan_clipboard.py` (domaine et fenêtre), lignes du catalogue des tests, suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1, §9 | contexte |
| T2 | REQ-001, REQ-002, REQ-003, UI-003 | capturé |
| T3 | REQ-004 | capturé |
| T4 | REQ-005, REQ-009, ARCH-002 | capturé |
| T5 | UI-001, CON-001, §8 | capturé |
| T6 | REQ-006 | capturé |
| T7 | REQ-002, REQ-007 | capturé |
| T8 | REQ-008, CON-002 | capturé |
| T9 | REQ-007, D-002 | décidé |

### Points de la source non résolus

- Aucun. Q-001 et Q-002 sont répondues (D-003, D-004).

## 13. Revue d'architecture

Revue par l'agent `architecture-reviewer` le 2026-10-16. **Verdict : APPROUVER AVEC RÉSERVES.** Chaque réserve est reportée dans la spec.

- **Modules** : `calc/domains/plan.py` (590–629), `plan_geometry.py` (`insert_axis`, `next_load_label`, `units_per_m`), `fire.py` (499–537), `calc/tools/plan_canvas_editing.py` (267–401), `plan_canvas_edit.py`, `plan_canvas_input.py` (`press_select` 253–342, `keyPressEvent` 588, `update_helpers` 652–723), `fire_canvas.py`, `plan_tab_selection.py` (100–140), `drawing_tab.py` (`init_shortcuts` 220).
- **À réutiliser** : `FireCanvas.select_ids` et son Ctrl ; `SchemaCanvas.select(add=True)` (focus + `extra`) ; `PlanCanvas.per_m()` ; `plan.shifted`, `insert_axis`, `positions_store.propose_id` / `section_of` / `last_section_of_type`, `next_load_label` ; `plan_centres.applies` ; `plan_canvas_edit.preview` et `EDIT_COLOUR`.
- **ARCH-RISK-101** (important) — environ 40 lecteurs et une douzaine d'assignations de `selection` → ARCH-004.
- **ARCH-RISK-102** (important) — aucun changement de projet en cours de processus ; racine du projet dans le presse-papiers ; module `plan_clip.py` sans Qt et détenteur `plan_clipboard.py` → ARCH-002, D-004.
- **ARCH-RISK-103** (important) — `positions_store` injecté (`propose`) et non importé dans le domaine ; numéro partagé conservé ; sections lues à Ctrl+C ; `PENDING` écrit par l'onglet dans le même pas d'Annuler ; collage dans le même plan → REQ-006, D-005.
- **ARCH-RISK-104** (important) — charges hors `loadpath`, contour sur une coupe, axes coïncidents, `setdefault` côté incendie (`fire.copy_entry` suppose la collection présente) → REQ-009.
- **ARCH-RISK-105** (important) — liste exacte des champs mis à l'échelle ; `span` est un angle → REQ-010 ; une seule fonction `placed` pour l'aperçu et le collage.
- **ARCH-RISK-106** (mineur) — le collage est une édition du brouillon, pas un writer (`WRITERS`) ; aucune méthode nommée `save*` / `write*`.
- **ARCH-RISK-107** (important) — `QShortcut` en `WidgetShortcut` dans `DrawingTab` ; `choose_tool` doit admettre les états « base » et « coller » et leur `plan_hint_*`.
- **ARCH-RISK-108** (mineur) — `plan.py` (1294 lignes) et `fire.py` ne grossissent pas ; ligne de `plan_clip.py` dans `layout.md`.
- **ARCH-RISK-109** (mineur) — le domaine rend des comptes et des codes, et les phrases sont dans `plan_tab_words.py` / `fire_tab_words.py`.

## 14. Plan d'implémentation

1. **Domaine** — `calc/domains/plan_clip.py` (nouveau, sans Qt) :
   - `Clip` : genre, entrées en copies profondes, base, `units_per_m`, sections par numéro, racine du projet ;
   - `clip_plan(source, selection, base, per_m, sections, root)` et `clip_fire(...)` ;
   - `placed(clip, point, per_m)`, qui décale et met à l'échelle (liste des champs de REQ-010) ;
   - `paste_plan(source, clip, point, per_m, window, propose)`, qui renvoie `{added, relabelled, left_out, axes_renamed, outline_replaced}` ;
   - `paste_fire(source, clip, point, per_m)`.
   → REQ-004–010, ARCH-001. Tests : `tests/test_plan_clipboard.py`, partie domaine, avec `check_source` sur chaque résultat.
2. **Détenteur** — `calc/tools/plan_clipboard.py` (`current`, `put`, `clear`). → ARCH-002.
3. **Sélection multiple du plan de positions** — dans `plan_canvas.py`, `plan_canvas_editing.py` et `plan_canvas_input.py` :
   - la propriété `selection` et `extra`, `selected_entries`, `select(add=)`, `select_all` (sans le contour) ;
   - `entry_at` et `entry_outline` extraits, Ctrl+clic sans drag ;
   - le dessin de toute la sélection ;
   - Déplacer, Supprimer, Copier et Dupliquer sur toute la liste, en un pas d'Annuler.
   
   Côté incendie, `fire_canvas.select_all`. → REQ-001–003, ARCH-003, ARCH-004. Tests : `test_plan_clipboard.py` (fenêtre) ; `test_plan_edit_tools.py`, `test_fire_tab.py` et les tests existants des plans restent verts.
4. **États « base » et « coller »** — dans `plan_canvas_edit.py` :
   - `CLIP_BASE`, `PASTE`, et l'aperçu par `placed` ;
   - `clip_selection` et `paste_clip` sur les deux canevas ;
   - `choose_tool` et `mark_tool` les admettent.
   
   → REQ-004, REQ-005, REQ-008.
5. **Onglets** :
   - les `QShortcut` Ctrl+A, Ctrl+C et Ctrl+V dans `DrawingTab` (`WidgetShortcut`) ;
   - `propose` et les sections fournis par `plan_tab_selection`, et `PENDING` écrit dans le même pas ;
   - refus de genre et de projet ;
   - indications et messages dans `plan_tab_words.py` et `fire_tab_words.py` (fr, de, en) ;
   - titre de carte « n objets ».
   
   → REQ-006, UI-001–003.
6. **Documentation** : `docs/ui/tab-plans.md`, `docs/domain/position-plans.md`, `docs/domain/fire-plans.md`, `docs/architecture/layout.md`, `docs/decisions.md` et son index (D-002, D-003, D-004, D-005), `CHANGELOG.md`, «Nouveautés» fr/de/en, catalogue des tests.
7. **Suite complète** (skill `finish`), puis vérification indépendante.

## 15. Vérification

Deux tours de vérification indépendante (`requirements-verifier`), le 2026-10-16.

- **Tour 1** : aucun ❌, mais dix ⚠️, presque tous des preuves manquantes :
  - REQ-001 (couleur), REQ-003 (Ctrl+Z, Dupliquer à plusieurs objets), REQ-007 (Ctrl+Z rend l'ancien contour) ;
  - REQ-008 (fenêtre incendie), UI-001 (aucun bouton), UI-002 (info-bulle de «Sélection» muette sur les raccourcis : seul vrai écart, corrigé dans `plan_tab_build.py`), UI-003 (champ du numéro) ;
  - ARCH-002, ARCH-004, Échap et collage répété.
  
  Huit tests ajoutés.
- **Tour 2** : tout est ✅.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `test_ctrl_click_adds_and_takes_out_and_a_plain_click_replaces`, `test_the_selection_is_drawn_in_the_selections_orange` |
| REQ-002 | ✅ | `test_ctrl_a_takes_everything_but_the_outline` ; incendie : `test_the_fire_tab_selects_copies_and_pastes_…` |
| REQ-003 | ✅ | `test_move_and_delete_act_on_the_whole_selection_in_one_step`, `test_move_duplicate_and_their_undo_act_on_the_whole_selection`, `test_copy_with_an_outline_selected_copies_the_rest` ; `test_plan_edit_tools` (14) vert |
| REQ-004 | ✅ | `test_ctrl_c_and_ctrl_v_carry_the_selection_…` ; Échap : `test_the_clip_survives_a_change_of_plan_escape_gives_up_…` |
| REQ-005 | ✅ | même test (aperçu, décalage, un pas d'Annuler) ; collage répété et Échap au collage |
| REQ-006 | ✅ | `test_a_paste_puts_the_base_on_the_point_and_renumbers_…`, `test_two_occurrences_…`, `test_pasting_on_the_plan_copied_from_…` ; positions en attente S202, S203 |
| REQ-007 | ✅ | `test_a_pasted_outline_replaces_the_plans_and_undo_gives_the_old_one_back` |
| REQ-008 | ✅ | `test_the_fire_tab_selects_copies_and_pastes_…`, `test_a_paste_of_the_other_kind_…`, `test_a_fire_plan_paste_gives_new_ids_…` |
| REQ-009 | ✅ | `test_what_the_target_cannot_hold_is_left_out_and_counted`, `test_a_new_axis_is_named_where_it_lands` (`check_source` sur chaque résultat) |
| REQ-010 | ✅ | `test_the_geometry_is_scaled_about_the_base_…`, `test_placed_scales_every_geometric_field_…` |
| UI-001 | ✅ | `drawing_tab_clip.py` (`WidgetShortcut`) ; `test_ctrl_c_in_a_field_is_the_field_s`, `test_no_button_for_the_clip_…` |
| UI-002 | ✅ | `test_the_words_exist_in_three_languages`, `test_i18n` (22) ; info-bulles de «Sélection» des deux onglets |
| UI-003 | ✅ | `test_the_number_field_shows_the_object_in_focus` ; titre « n objets » dans le test principal |
| ARCH-001 | ✅ | `calc/domains/plan_clip.py` sans Qt, tests du domaine sans QApplication, `test_module_imports` vert |
| ARCH-002 | ✅ | `plan_clipboard.py` ; survie au changement de plan et refus d'un autre projet testés ; aucun schéma touché |
| ARCH-003 | ✅ | `test_plan_edit_tools`, `test_plan_centres_window`, `test_fire_tab` verts |
| ARCH-004 | ✅ | `test_a_selection_of_one_object_after_a_new_one_and_no_index_left_behind_by_an_undo` |
| CON-001…004 | ✅ | «Copier» inchangé, refus testés, aucun schéma modifié, trois langues |
| Documentation | ✅ | docs/ (tab-plans, position-plans, fire-plans, layout, decisions + index, catalogue), CHANGELOG, Nouveautés 0.119 fr/de/en ; `test_docs_coherence` (7) |

Réserves mineures, gardées : Ctrl+A/C/V sur l'onglet incendie sont prouvés par les méthodes de l'onglet et non par des frappes, mais le câblage `QShortcut` est le même que celui du plan de positions, qui est testé au clavier. Les boutons ne sont pas comptés avant et après : le test prouve seulement qu'aucun outil du presse-papiers n'a de bouton.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-16 | draft | spécification extraite de l'issue #61 ; D-001, D-002 répondues ; Q-001, Q-002 ouvertes |
| 2026-10-16 | specified | Q-001 → A (mise à l'échelle, REQ-010, D-003) ; Q-002 → A (vidé en changeant de projet, D-004) |
| 2026-10-16 | reviewed | revue APPROUVER AVEC RÉSERVES (ARCH-RISK-101…109), réserves reportées (REQ-006, REQ-009, REQ-010, ARCH-002, ARCH-004, D-004, D-005) ; plan en 7 étapes |
| 2026-10-16 | approved | approuvée par l'ingénieur ; implémentation commence |
| 2026-10-16 | implementation | étapes 1-2 : calc/domains/plan_clip.py (Clip, clip_plan, clip_fire, placed, paste_plan, paste_fire, new_positions), calc/tools/plan_clipboard.py ; tests/test_plan_clipboard.py partie domaine (9 verts) → REQ-006, REQ-007, REQ-009, REQ-010, ARCH-001, ARCH-002 |
| 2026-10-16 | implementation | étapes 3-5 : sélection multiple (selection en propriété + extra, set_selected, select_all, entry_at, entry_outline, press_toggle), états clip-base et paste (plan_canvas_edit), drawing_tab_clip.py (Ctrl+A/C/V en WidgetShortcut), make_clip/paste_clip des deux onglets, mots fr/de/en, titre « n objets » ; tests/test_plan_clipboard.py 17 verts → REQ-001…REQ-008, UI-001…UI-003, ARCH-003, ARCH-004 |
| 2026-10-16 | testing | étape 6 : documentation (tab-plans, position-plans, fire-plans, layout, decisions + index, catalogue, CHANGELOG, Nouveautés 0.119 fr/de/en) ; tests liés verts (test_plan_clipboard 17, fichiers liés 158, gardes : imports, taille, i18n, home, theme, broad except, docs) |
| 2026-10-16 | verification | tour 1 : 0 ❌, 10 ⚠️ (preuves manquantes, info-bulle de «Sélection») → corrigé, 8 tests ajoutés ; tour 2 : tout ✅ ; suite complète en cours |
| 2026-10-16 | completed | suite complète verte (3003 passés, 15 ignorés, 1462 s) ; spec déplacée dans completed/ |
