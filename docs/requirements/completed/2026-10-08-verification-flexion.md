---
id: 2026-10-08-verification-flexion
titre: Vérification à la flexion (SIA 265 4.2.3, avec effort normal 4.2.4), sans déversement
status: completed
cree: 2026-10-08
mis_a_jour: 2026-10-08
source: message écrit
docs: [docs/domain/member-checks.md, docs/ui/window.md, docs/typst/api-conventions.md, docs/open-questions.md]
---

# Vérification à la flexion — Spécification

## 1. Objectif

Construire le module « Flexion » des vérifications d'élément enregistrées dans Woodcore (aujourd'hui un `SoonTab`), comme l'ont été « Traction » et « Compression » en v0.117 : la section seule, sans déversement — (14) le long du fil, (17)/(18) avec k_mc,α et k_mt,α de (19)/(20) sous un angle, (21) avec une traction, (22) avec une compression — calculée à l'instant en Python dans la fenêtre et par `#show-check-member` dans le rapport.

## 2. Source

> **T1** — « Implémente la vérification à la flexion d'après la SIA265 §4.2.3 (sans déversement): »
>
> **T2** — « prendre en compte le facteur k_mc,alpha et k_mt, alpha (équation 19 et 20) »
>
> **T3** — « équation 21 si effort normal positif (traction) »
>
> **T4** — « équation 22 si effort normal négatif (compression) »

Lecture de la norme (SIA 265:2021 DE et FR, p. 32–33, `ExternalFiles/000-Normes/`) : (14) en 4.2.3.1, (15)/(16) en 4.2.3.2, (17) à (20) en 4.2.3.3 ; (21) et (22) sont en **4.2.4.1 et 4.2.4.2** (« Biegung mit Normalkraft »), pas en 4.2.3. (17) à (22) écrivent f_m,d, que Woodcore lit comme f_m,y,d (la seule flexion sous un angle est autour de y).

## 3. Exigences fonctionnelles

### REQ-001 — Le genre `bending` est implémenté
- **Exigence** : `member_check.IMPLEMENTED` doit contenir `bending` ; une source `kind: "bending"` est lue, vérifiée, résolue et exportée dans `data/checks.json` comme les deux autres genres.
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_member_check.py` lit une source de flexion, l'exporte `calculable: true`, et une source malformée (un moment présent mais non numérique, une unité inconnue) arrête l'export en nommant le fichier et le champ ; un moment absent vaut 0 (REQ-007).

### REQ-002 — Flexion le long du fil, (14)
- **Exigence** : avec α = 0 et N = 0, Woodcore doit vérifier σ_m,y,d/f_m,y,d + σ_m,z,d/f_m,z,d ⩽ 1 (4.2.3.1), un moment non donné étant 0.
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : `compute()` donne l'équation « (14) », la clause 4.2.3.1 et un η égal à celui de `verify-bending` (registre Typst) à 1e-6 près.

### REQ-003 — Flexion sous un angle, (17) à (20)
- **Exigence** : avec 0 < α < 90, Woodcore doit vérifier les deux côtés, σ_m,α,d ⩽ k_mc,α·f_m,d (17) et σ_m,α,d ⩽ k_mt,α·f_m,d (18), k_mc,α et k_mt,α de (19) et (20), η étant le plus grand ; à α = 90, (15) et (16) — que (17)/(18) donnent aussi à cette limite.
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : `compute()` montre k_mc,α et k_mt,α avec leur formule et donne le η de `verify-bending(alpha:)` à 1e-6 près, à 30° et à 90°.

### REQ-004 — Flexion avec traction, (21)
- **Exigence** : avec N > 0 (traction, α = 0), Woodcore doit vérifier σ_t,0,d/f_t,0,d + σ_m,y,d/f_m,y,d + σ_m,z,d/f_m,z,d ⩽ 1 (4.2.4.1).
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : η de `compute()` = η de `verify-bending-normal(N: +…)` à 1e-6 près.

### REQ-005 — Flexion avec compression, (22)
- **Exigence** : avec N < 0 (compression, α = 0), Woodcore doit vérifier (σ_c,0,d/f_c,0,d)² + σ_m,y,d/f_m,y,d + σ_m,z,d/f_m,z,d ⩽ 1 (4.2.4.2), sans flambage.
- **Source** : T4, T1 (« sans déversement »)
- **Priorité** : doit
- **Critère d'acceptation** : η de `compute()` = η de `verify-bending-normal(N: -…, stability: false)` à 1e-6 près ; aucune longueur de flambage demandée.

### REQ-006 — Sans déversement ni flambage
- **Exigence** : la vérification enregistrée doit être celle de la section seule : ni le déversement (4.2.9) ni le flambage (4.2.8) — ce sont les modules « Déversement » et « Flambage ».
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : la page de `#show-check-member` d'une flexion n'a ni partie « Stabilität » ni note « Kippen nicht nachgewiesen » ; son η est celui de la section.

### REQ-007 — Ce que l'export ne peut pas calculer
- **Exigence** : une flexion sans moment (M_y = M_z = 0) ou sous un angle avec M_z ≠ 0 ((17)–(20) ne lisent que M_y) doit être exportée `calculable: false` avec sa raison, jamais arrêter l'export (règle v0.33).
- **Source** : inféré (docs/architecture/principles.md, « a missing input warns »), Q-002
- **Priorité** : doit
- **Critère d'acceptation** : test : chacun de ces cas donne `calculable: false` et une raison qui dit pourquoi ; `#show-check-member` la refuse avec cette raison.

### REQ-008 — Flexion sous un angle avec un effort normal
- **Exigence** : avec 0 < α ⩽ 90 et N ≠ 0, Woodcore doit appliquer (21) ou (22) avec les résistances sous l'angle — f_t,α,d de (9) ou f_c,α,d de (13) (f_c,90,d « generell »), et en flexion k_mt,α·f_m,d ou k_mc,α·f_m,d —, sur le côté où N s'ajoute à la flexion, et vérifier l'autre côté par la flexion seule, sans le soulagement de N :
  - traction : σ_t,α,d/f_t,α,d + σ_m,α,d/(k_mt,α·f_m,d) ⩽ 1 (côté tendu) et (17) σ_m,α,d ⩽ k_mc,α·f_m,d (côté comprimé) ;
  - compression : (σ_c,α,d/f_c,α,d)² + σ_m,α,d/(k_mc,α·f_m,d) ⩽ 1 (côté comprimé) et (18) σ_m,α,d ⩽ k_mt,α·f_m,d (côté tendu) ;
  - η est le plus grand des deux. La page dit que c'est l'application de (21)/(22) sous un angle, avec (9)/(13) et (19)/(20) — la norme ne l'écrit pas.
- **Source** : Q-002 (réponse de l'ingénieur), Q-004
- **Priorité** : doit
- **Critère d'acceptation** : η de `compute()` = η de `verify-bending-normal(alpha: 30, N: ±…, stability: false)` à 1e-6 près, en traction et en compression ; la page porte la note qui le dit.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — L'onglet « Flexion »
- **Exigence** : `tab_mc_bending` doit devenir un `BendingTab(MemberCheckTab)` : liste des flexions, formulaire en cartes (identité, position, matériau, section), une carte « Effort » avec α, M_y,d, M_z,d (kNm) et N_d (signé ou en deux champs, Q-003), le résultat Python instantané à droite, la vue « Affichage ».
- **Source** : T1
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_member_check_tab.py` crée, remplit, enregistre et recharge une flexion ; les résultats s'affichent sans compilation ; tous les libellés existent dans les trois langues (`tests/test_i18n.py`).

### UI-002 — Les champs qui ne s'appliquent pas
- **Exigence** : avec α > 0, M_z doit être désactivé, puisque (17)/(18) ne lisent que M_y ; N reste actif (REQ-008).
- **Source** : Q-002
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : α = 30 → M_z inactif, N actif ; α = 0 → les deux actifs.

### UI-003 — Le rapport
- **Exigence** : `#show-check-member` doit imprimer une flexion par `#member` puis `#verify-bending(..., alpha:, stability: false)` (N = 0) ou `#verify-bending-normal(..., alpha:, stability: false)` (N ≠ 0), toutes les valeurs écrites ; `draft_typst` donne exactement le même appel. `verify-bending` et `verify-bending-normal` reçoivent `stability: true|false` (Q-001), et `verify-bending-normal` reçoit `alpha:` (REQ-008).
- **Source** : T1–T4
- **Langues** : la page dans la langue du document (glossaire)
- **Critère d'acceptation** : deux exemples `examples/show-check-member-*.typ` compilent ; `draft_typst` = l'appel de `#show-check-member` (test).

## 5. Exigences d'architecture

### ARCH-001 — Une seule arithmétique par côté, tenues égales
- **Exigence** : le calcul Python (`member_check.compute`) lit toutes les valeurs de la norme par `norms.sia265`, aucune n'est écrite dans le code ; le test qui tient Python égal au registre Typst (1e-6) couvre chaque branche de la flexion.
- **Source** : principes (une source de vérité ; pas de valeur en dur), décision du 07.10.2026 (résultats Python instantanés)
- **Critère d'acceptation** : `test_member_check.py` compare ≥ 6 enregistrements de flexion (14, 14 avec M_z, 17/18 à 30°, 15/16 à 90°, 21, 22, une section ronde).

### ARCH-002 — Contrats additifs
- **Exigence** : `member-check-source.schema.json` et `checks.schema.json` reçoivent `M_y` et `M_z` ({value, unit}, kNm) comme champs optionnels ; la signification de `N` pour `bending` est écrite (signé, traction positive) ; `schema_version` reste 1.0 si l'ajout est additif (précédent : `case`/`l`/`w` en v0.117).
- **Source** : principes (modèles de données explicites et versionnés)
- **Critère d'acceptation** : les sources existantes (traction, compression) se lisent et s'exportent inchangées (`tests/projet-exemple/`).

### ARCH-003 — Logique hors de l'interface
- **Exigence** : l'onglet montre, édite et appelle `member_check` ; il ne recalcule rien.
- **Source** : principes
- **Critère d'acceptation** : `member_check_tab.py` n'a aucune formule de flexion.

## 6. Contraintes

- **CON-001** — SIA 265:2021, édition de `ExternalFiles/000-Normes/SIA265-2021-DE.pdf` ; numéros d'équation et de clause de cette édition. Source : CLAUDE.md.
- **CON-002** — Trois langues pour toute chaîne visible. Source : CLAUDE.md.
- **CON-003** — Une commande Typst modifiée (`verify-bending`, `verify-bending-normal` : argument `stability`) reçoit son `///`, deux exemples qui compilent et sa traduction dans `calc/i18n/commands.json`. Source : CLAUDE.md.
- **CON-004** — Documentation : `docs/domain/member-checks.md`, `docs/ui/window.md`, `docs/open-questions.md` (le module n'est plus un placeholder), `CHANGELOG.md`, « Nouveautés » 0.117.0 fr/de/en. Source : CLAUDE.md.

## 7. Décisions prises

- Le module « Flexion » regroupe 4.2.3 et 4.2.4 — le regroupement de l'ingénieur déjà écrit dans `mc_what_bending`.
- Sans déversement : le module ne vérifie que la section ; déversement et flambage restent leurs modules (T1).
- Le signe de N choisit l'équation : > 0 (21), < 0 (22), 0 (14) ou (17)–(20) (T3, T4).

- **Q-001** (08.10.2026) : « sans déversement » est un argument `stability: false` de `verify-bending` et `verify-bending-normal`, comme `verify-compression` en v0.117 — la section seule, aucune longueur, aucune partie « Stabilität ». Prix : deux commandes changent de surface (///, exemples, traductions).
- **Q-002 / Q-004** (08.10.2026) : sous un angle, M_z est désactivé, N est permis ; (21)/(22) s'appliquent avec f_t,α,d (9) ou f_c,α,d (13) et k_mt,α/k_mc,α, le côté où N s'ajoute en interaction, l'autre par (17) ou (18) seule. C'est l'interprétation de l'ingénieur, au-delà du texte de 4.2.4 : la page le dit, `docs/decisions.md` le note.
- **Q-003** (08.10.2026) : `N` est signé pour `bending` (traction +, compression −, 0 = flexion pure), un seul champ dans la fenêtre — la convention des commandes Typst.

## 8. Hors périmètre

- Déversement (4.2.9) et flambage (4.2.8, (37)) dans ce module.
- Les modules Effort tranchant, Torsion, Flambage, Déversement, Déformations, Vibrations.

## 9. Idées non retenues comme exigences

_(aucune)_

## 10. Questions

### Q-001 — Comment `#show-check-member` obtient « sans déversement » dans le rapport
- **Pourquoi elle compte** : `verify-bending` sans `a:` imprime « Kippen nicht nachgewiesen » ; `verify-bending-normal` avec compression exige les longueurs de flambage et calcule (37). Il faut changer la surface de deux commandes Typst.
- **Options** : A (recommandée) un argument `stability: true/false` sur `verify-bending` et `verify-bending-normal`, comme `verify-compression` depuis v0.117 — false : la section seule, aucune longueur, aucune partie « Stabilität » ; B pas de nouvel argument : `#show-check-member` appelle `verify-bending` sans `a:` (la note « Kippen nicht nachgewiesen » reste imprimée) et, pour (22), `l-k-y: 0, l-k-z: 0` (k_c = 1, mais (37) imprimé et un η qui mélange section et stabilité).
- **Réponse** : A — `stability: false` (l'ingénieur, 08.10.2026).

### Q-002 — Une flexion sous un angle avec N ou M_z
- **Pourquoi elle compte** : (17)–(20) ne lisent que M_y et aucune équation ne combine l'angle avec un effort normal.
- **Options** : A (recommandée) la fenêtre désactive N et M_z dès que α > 0 ; une source qui les porte quand même est exportée `calculable: false` avec la raison ; B la source est malformée et arrête l'export.
- **Réponse** : « désactiver M_z. Il est possible de donner un N. Les équations 9 et 13 permettent de calculer le f_c ou f_t nécessaire pour la formule 21 ou 22 » (l'ingénieur, 08.10.2026) → Q-004.

### Q-003 — L'effort normal dans la source et dans la fenêtre
- **Pourquoi elle compte** : pour traction et compression, `N` est une grandeur positive ; pour la flexion il doit dire traction ou compression.
- **Options** : A (recommandée) le même champ `N`, signé pour `bending` (traction +, compression −, 0 = flexion pure) — un seul champ « N_d (traction +, compression −) » dans la fenêtre, la convention des commandes Typst ; B une liste « Aucun / Traction / Compression » et une grandeur positive (`N` positif + un champ `normal`).
- **Réponse** : A — N signé (l'ingénieur, 08.10.2026).

### Q-004 — Flexion sous un angle avec N : quelles conditions
- **Pourquoi elle compte** : la norme n'écrit pas (21)/(22) sous un angle ; il faut fixer quels côtés sont vérifiés et avec quelles résistances.
- **Options** : A (recommandée) l'interaction du côté où N s'ajoute (k_mt,α en traction, k_mc,α en compression), l'autre côté par (17) ou (18) seule ; B l'interaction seule ; C l'interaction des deux côtés.
- **Réponse** : A (l'ingénieur, 08.10.2026).

## 11. Critères d'acceptation

- [x] REQ-001 — `bending` dans IMPLEMENTED, source lue/vérifiée/exportée, une source malformée arrête l'export en nommant le champ
- [x] REQ-002 — (14) : η Python = η Typst
- [x] REQ-003 — (17)–(20) à 30°, (15)/(16) à 90° : η Python = η Typst, k_mc,α et k_mt,α affichés
- [x] REQ-004 — (21) : η Python = η Typst
- [x] REQ-005 — (22) sans flambage : η Python = η Typst
- [x] REQ-006 — ni « Stabilität » ni note de déversement sur la page
- [x] REQ-007 — cas non calculables exportés avec leur raison
- [x] REQ-008 — (21)/(22) sous un angle : η Python = η Typst, en traction et en compression, la note sur la page
- [x] UI-001 — onglet Flexion construit, testé, trois langues
- [x] UI-002 — M_z inactif à α > 0, N actif
- [x] UI-003 — `#show-check-member` et `draft_typst` identiques, exemples compilés
- [x] ARCH-001 — test d'égalité Python/Typst sur ≥ 6 cas de flexion
- [x] ARCH-002 — schémas additifs, anciennes sources inchangées
- [x] ARCH-003 — aucune formule dans l'onglet
- [x] Documentation : sections de `docs/` mises à jour, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en, `///` + exemples + traductions pour toute commande Typst.
- [x] Tests : `test_member_check.py`, `test_member_check_tab.py`, `test_i18n.py`, tests des exemples Typst — passent.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-002, REQ-006, UI-001, UI-003, Q-001 | capturé |
| T2 | REQ-003, REQ-008, UI-002, Q-002, Q-004 | capturé |
| T3 | REQ-004, Q-003 | capturé |
| T4 | REQ-005, Q-003 | capturé |

### Points de la source non résolus

_(aucun : Q-001 à Q-004 répondues le 08.10.2026)_

## 13. Revue d'architecture

Revue par `architecture-reviewer` le 08.10.2026 — **APPROUVER AVEC RÉSERVES**.

- **Modules** : `calc/domains/member_check.py` (`IMPLEMENTED`, `check_source`, `new_source`, `resolve`, `draft_typst`, `compute`), `lib/timber.typ` (`verify-bending` :864, `verify-bending-normal` :962, `show-check-member` :1294), `calc/tools/member_check_tab.py` (base, `SOON`, `STRINGS`), `calc/tools/woodcore_gui.py:2813` (instanciation, fichier modifié par d'autres sessions), `schemas/member-check-source.schema.json`, `schemas/checks.schema.json`, `calc/validation.py:221-248`, `calc/i18n/strings.json` (`terms`), `calc/i18n/commands.json`.
- **À réutiliser** : l'ossature de `CompressionTab` ; `_table_of`, `design()`, `at_angle()`, `_row`, `_fmt`, `_TO_KN` ; `sia265.k_h()` ; les parties `Biegezugseite`/`Biegedruckseite` de `verify-bending` ; `test_compute_is_what_the_report_computes` et `_synthetic()`.
- **ARCH-RISK-001 (bloquant)** — N signé contre trois garde-fous qui supposent N > 0 : `resolve` (:299), `validate_checks_business` (:240, qui arrêterait l'export), les descriptions des deux schémas. → brancher sur `kind`, écrire la convention dans les schémas, test de non-régression (N ⩽ 0 toujours refusé pour traction et compression).
- **ARCH-RISK-002 (important)** — `compute` doit reproduire `#member` : k_h,y / k_h,z du lamellé-collé (< 600 mm), W_y, W_z (cercle π d³/32), f_c,90,d « generell ». → lire `sia265.k_h()` ; cas d'essai GL < 600, GL ⩾ 600, rond, massif.
- **ARCH-RISK-003 (important)** — le test d'égalité suppose une commande par genre et une relation « σ <= f ». → mapping par N, comparaison adaptée aux sommes.
- **ARCH-RISK-004 (important)** — `alpha:` sur `verify-bending-normal` : panics alignés sur `verify-bending` ; α = 90 avec N. → décidé : les formules sous un angle (clés `f_t_alpha_d`, `f_c_alpha_d`, `k_mt_alpha`, `k_mc_alpha`) pour tout α > 0, qui donnent f_t,90 / f_c,90 à 90°.
- **ARCH-RISK-005 (important)** — `stability:` ne doit rien casser : défaut `true` ; avec `false` aucune longueur lue ; `a:` / `sigma-m-crit:` → décidé : refusés avec `stability: false`.
- **ARCH-RISK-006 (important)** — i18n : la note d'interprétation imprimée par `tl-str` dans `strings.json` `terms` (fr/en) avec un test qui pose la clé ; les clés `mc_*` de l'onglet dans les trois langues.
- **ARCH-RISK-007 (important)** — `n_spin` de 0 à 1e6 : paramétrer `effort_card` (minimum négatif) ; M_z remis à 0 et désactivé à α > 0, `draft_effort` écrit alors `M_z: null`.
- **ARCH-RISK-008 (mineur)** — REQ-001/REQ-007 contradictoires → décidé : un moment absent vaut 0 (non calculable si les deux le sont), seul un champ présent et mal formé arrête.
- **Contrats** : `schema_version` reste 1.0 (champs optionnels, pas d'`additionalProperties: false`) ; `resolve` n'émet `M_y`/`M_z` que pour `bending`, de sorte que `checks.json` des traction/compression reste identique à l'octet.
- **Exemples gelés** : `///` à jour (puces `stability`, `alpha`), un exemple qui montre le nouvel argument, traductions dans `commands.json`, `build_examples.py` ; `show-check-member` : `///` et un exemple de flexion.
- **Décisions** : rien de contredit ; à ajouter dans `docs/decisions.md` : (21)/(22) sous un angle, N signé pour `bending`.

## 14. Plan d'implémentation

1. **Typst** (`lib/timber.typ`) — `stability: true|false` sur `verify-bending` et `verify-bending-normal` (false : ni `a:`, ni `sigma-m-crit:`, ni longueurs, aucune partie « Stabilität », η de la section) ; `alpha:` sur `verify-bending-normal` (M-z refusé à α > 0 ; f_t,α,d (9) / f_c,α,d (13), k_mt,α / k_mc,α ; le côté où N s'ajoute en interaction, l'autre par (17) ou (18) ; η = max ; une note `tl-str`). `///`, exemples, `commands.json`, la note dans `strings.json` `terms`. → REQ-003, REQ-005, REQ-006, REQ-008, UI-003. Tests : `test_timber.py` / `test_commands.py`, exemples compilés.
2. **Domaine** (`member_check.py`) — `bending` dans `IMPLEMENTED` ; `M_y`, `M_z` ({value, unit}, `MOMENT_UNITS`) dans `check_source`, `new_source`, `resolve` (émis pour `bending` seulement) ; N signé pour `bending` ; non calculable : aucun moment, M_z à α > 0 ; `draft_typst` dispatché par genre ; `_compute_bending` (14), (15)/(16), (17)–(20), (21), (22), (21)/(22) sous un angle, k_h compris. → REQ-001..008, ARCH-001, ARCH-003.
3. **Contrats** — descriptions et champs `M_y`/`M_z` des deux schémas ; `validate_checks_business` branché sur `kind`. → ARCH-002.
4. **Rapport** — `show-check-member` : le genre `bending`, le même appel que `draft_typst` ; `///` et un exemple. → UI-003.
5. **Fenêtre** — `effort_card` paramétrable (N signé) ; `BendingTab(MemberCheckTab)` (carte Effort : α, M_y,d, M_z,d, N_d), M_z remis à 0 et inactif à α > 0 ; `tab_mc_bending` retiré de `SOON` ; `woodcore_gui.py` : `BendingTab` à la place du `SoonTab` (Edit ciblé) ; `STRINGS` fr/de/en. → UI-001, UI-002. Tests : `test_member_check_tab.py`, `test_i18n.py`.
6. **Tests** — `test_member_check.py` : défauts, non calculables, non-régression N ⩽ 0, égalité Python = Typst sur 8+ cas (massif, GL < 600, GL ⩾ 600, rond), `draft_typst` = `show-check-member`.
7. **Documentation** — `docs/domain/member-checks.md`, `docs/ui/window.md`, `docs/open-questions.md`, `docs/decisions.md`, `CHANGELOG.md`, « Nouveautés » 0.117.0 fr/de/en ; docstrings des modules.

## 15. Vérification

Vérification indépendante (`requirements-verifier`, 08.10.2026), arbre de travail contre HEAD ; tests relancés par le vérificateur : `test_member_check` + `test_member_check_tab` 67, `test_timber` 38, `test_i18n` 21, `test_commands` 34, tous verts. Premier tour : 15 ✅, 3 ⚠️, 0 ❌ ; les trois ⚠️ corrigés ensuite (deuxième colonne).

| Élément | Verdict | Preuve (fichier:ligne, test, sortie) |
|---|---|---|
| REQ-001 | ✅ | `member_check.IMPLEMENTED` ; `check_source` refuse un moment mal formé en nommant le champ — `test_a_bending_source_is_checked_field_by_field`, `test_a_good_source_passes` |
| REQ-002 | ✅ | `_compute_bending` (14)/4.2.3.1 ; `test_compute_is_what_the_report_computes` (BI-01, BS-0..4) à 1e-6 |
| REQ-003 | ✅ | k_mc,α, k_mt,α avec formule ; (15)/(16) et (17)–(20) ; égalité BS-5 (90°), BS-6 (25°), BS-7 (rond, 15°) ; `test_bending_at_an_angle_is_19_and_20` |
| REQ-004 | ✅ | (21)/4.2.4.1 ; égalité BS-8, BI-03 |
| REQ-005 | ✅ | (22)/4.2.4.2 sans flambage ; égalité BS-9, BS-10, BI-02 ; `test_stability_false_checks_the_section_alone` |
| REQ-006 | ✅ | `stability: false` dans `show-check-member` ; `test_a_bending_saved_in_woodcore_prints_the_section_alone` (ni « Stabilität » ni « Kippen ») |
| REQ-007 | ⚠️ → ✅ | `resolve` « no moment » / « read M_y alone » ; refus par `#show-check-member` et par le brouillon ajouté : `test_a_bending_that_cannot_be_checked_is_refused_by_the_report_with_its_reason` |
| REQ-008 | ✅ | branche α > 0, N ≠ 0 en Python et Typst, note sur la page ; égalité BS-11..14, BI-03 ; `test_bending_with_a_normal_force_at_an_angle` |
| UI-001 | ⚠️ → ✅ | `BendingTab`, `woodcore_gui.py:2813`, trois langues ; rechargement ajouté : `test_a_saved_bending_is_loaded_back_into_its_fields` ; `tests/test_views.py` : `tab_mc_bending` dans `LISTED` (signalé rouge par la session pair, corrigé, 9 passed) |
| UI-002 | ✅ | `update_effort_view`, `draft_effort` ; `test_at_an_angle_m_z_is_closed_and_zero_and_n_stays_open` |
| UI-003 | ✅ | `draft_typst` = `show-check-member` : `test_show_check_member_prints_what_the_draft_prints` (BI-01..03) ; exemples compilés (`test_every_example_compiles`) |
| ARCH-001 | ✅ | valeurs par `norms.sia265` ; 18 flexions comparées, toutes les clés de lignes vues |
| ARCH-002 | ✅ | schémas 1.0, `M_y`/`M_z` optionnels ; `checks.json` : 126 lignes ajoutées, 0 retirée ; N ⩽ 0 toujours refusé pour traction et compression |
| ARCH-003 | ✅ | aucune formule dans `BendingTab` |
| CON-001 | ✅ | numéros et clauses relus dans SIA265-2021-DE.pdf p. 32–33 |
| CON-002 | ✅ | `mc_*` fr/de/en, termes du glossaire ; `test_i18n`, `test_every_phrase_typst_translates_is_a_term` |
| CON-003 | ✅ | `///` (puces `stability`, `alpha`), exemples, `commands.json` fr/de ; `test_commands` |
| CON-004 / Documentation | ⚠️ → ✅ | docs, CHANGELOG, Nouveautés fr/de/en présents ; le lien vers `completed/` est juste une fois la spec déplacée (clôture) |
| Tests | ✅ | voir l'en-tête ; suite complète à la clôture : 2672 passed, 17 skipped, 11 FAILED — 1 de ce travail (`test_commands.test_the_frozen_examples_run_against_the_current_engine`, copie `examples/lib/` périmée : exemples régénérés, repassé), 7 par PySide6 mélangé installé à 13 h 56 (Essentials/shiboken 6.12.0, Addons 6.11.2 : QtPdf ne se charge plus), 2 de temps sous deux suites simultanées (`test_startup` 1.522 s > 1.5 s, `test_tasks`), 1 réseau (`test_typst_check`), `test_structure_tab` non relançable tant que Qt est cassé |

Remarques sans impact reprises : le commentaire déplacé et l'espace perdu dans `lib/timber.typ` corrigés ; les deux paragraphes existants de `commands.json` reformulés sans raison rendus à leur texte d'origine.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-08 | draft | spécification extraite de la demande ; la norme lue (p. 32–33) : (21)/(22) sont en 4.2.4, les commandes Typst existent déjà |
| 2026-10-08 | specified | Q-001 à Q-004 répondues : `stability: false`, N signé, M_z désactivé sous un angle, (21)/(22) sous un angle avec (9)/(13) et l'autre côté seul |
| 2026-10-08 | reviewed | revue APPROUVER AVEC RÉSERVES, réserves reprises dans le plan (§13, §14) |
| 2026-10-08 | approved | approuvé par l'ingénieur |
| 2026-10-08 | implementation | étape 1 (Typst) faite : `stability` sur verify-bending et verify-bending-normal, `alpha` sur verify-bending-normal, note et titres dans strings.json, commands.json ; tests test_timber (2) et test_i18n (tl-str) — REQ-003, REQ-005, REQ-006, REQ-008 côté Typst ; exemples à générer après l'étape 4 |
| 2026-10-08 | implementation | étapes 2–4 faites : member_check (bending dans IMPLEMENTED, M_y/M_z, N signé, raisons, draft_typst, _compute_bending), validation et schémas, show-check-member (+ exemple BI-01..03 dans le projet d'exemple, examples/data/checks.json) ; clés eta_m_t/eta_m_c (le facteur eta_t n'est plus écrasé) — REQ-001..008, ARCH-002, UI-003 |
| 2026-10-08 | testing | étapes 5–7 faites : BendingTab (effort_card paramétrable ALPHA_KEY/N_MIN, M_z fermé à α > 0), woodcore_gui, STRINGS fr/de/en, tests (test_member_check 31, test_member_check_tab 36, test_timber 38, test_i18n 21, test_commands 34 — tous verts) ; docs member-checks.md, window.md, open-questions.md, decisions.md, CHANGELOG, Nouveautés 0.117.0 fr/de/en |
| 2026-10-08 | verification | vérification indépendante : 15 ✅, 3 ⚠️ (REQ-007, UI-001, lien de la doc) corrigés ; test_views rouge signalé par la session pair (commit b462466) corrigé |
| 2026-10-08 | completed | ⚠️ levés et repassés (2 tests ajoutés, test_views) ; suite complète lue par nom ; spec déplacée dans completed/ |
