---
id: 2026-10-14-verdict-niveau-manuel
titre: Le verdict d'une vérification au niveau −1 (issue #58)
status: completed
cree: 2026-10-14
mis_a_jour: 2026-10-14
source: issue GitHub When-I-hit-the-wall/Woodcore#58 (message écrit de l'ingénieur, 14.10.2026) et ses réponses du 14.10.2026
docs: [docs/ui/window.md, docs/ui/tab-member-checks.md, docs/domain/member-checks.md, docs/typst/report-engine.md]
---

# Le verdict d'une vérification au niveau −1 — Spécification

## 1. Objectif

Au niveau de détail −1 «Sélection manuelle», le résultat d'une vérification de barre est son **verdict** — la ligne `verify` du taux d'utilisation η ≤ 1 —, et non la contrainte σ/τ que l'issue #39 avait désignée. L'ingénieur veut voir ce verdict dans le volet de droite de «Affichage», avec son niveau `0 | 1 | 2 | 3`, 0 compris.

## 2. Source

> **T1** — « en mode affichage, dans le volet de droire, lorsque le niveau est réglé manuellement, il doit le résultat doit également pouvoir recevoir le niveau 0. »
>
> **T2** — « De plus, tu t'es trompé. Le résultats pour les vérifications sont le verify et non pas le sigma. »
>
> **T3** — « Le verify n'apparait même pas dans le volet de droite, c'est une erreur »
>
> **T4** — Réponse à Q-001 (14.10.2026) : « Une clé par verdict » (eta, eta_s, eta_y, eta_m_t…).
>
> **T5** — Réponse à Q-002 (14.10.2026) : « Non, absent = 0 » — un verdict que `shown:` ne nomme pas ne s'imprime pas.

## 3. Exigences fonctionnelles

### REQ-001 — Le verdict a sa clé dans `shown:`
- **Exigence** : chaque verdict que imprime un `verify-*` de `lib/timber.typ` qui prend `shown:` (`verify-tension`, `verify-compression`, `verify-compression-perp`, `verify-bending`, `verify-bending-normal`, `verify-shear`, et donc `show-check-member`) doit pouvoir être nommé dans `shown:` par la clé de son η : `eta`, `eta_s`, `eta_y`, `eta_z`, `eta_m`, `eta_m_t`, `eta_m_c`. Ces clés entrent dans les `keys` de la commande dans `lib/shown-variables.json`, à leur place dans l'ordre d'impression.
- **Source** : T2, T4
- **Priorité** : doit
- **Critère d'acceptation** : `#verify-compression(…, level: -1, shown: (eta_y: 3))` compile et imprime le verdict η_c,y en entier (la forme du niveau 3 actuel) ; `shown: (eta_q: 1)` est refusé, en nommant la clé.

### REQ-002 — Le niveau du verdict à −1 suit `shown:`, 0 compris
- **Exigence** : au niveau −1, un verdict s'imprime au niveau que `shown:` lui donne : 1 la forme brève, 2 et 3 la forme complète (comme aux niveaux 1, 2 et 3 d'aujourd'hui). Un verdict que `shown:` ne nomme pas ne s'imprime pas, comme toute autre clé (absent = 0). Hors du niveau −1, rien ne change.
- **Source** : T1, T5
- **Priorité** : doit
- **Critère d'acceptation** : `verify-tension(…, level: -1, shown: (:))` n'imprime pas de verdict ; `shown: (eta: 1)` l'imprime sous la forme brève ; aux niveaux 1, 2 et 3, la page est identique à celle d'avant (test de compilation). Au niveau −1, le titre et les intertitres « Tragsicherheit » et « Stabilität » s'impriment comme aujourd'hui ; « Biegezugseite » et « Biegedruckseite » s'impriment au-dessus de leur verdict quand celui-ci a le niveau 2 ou 3, comme au niveau 2 (ARCH-RISK-003).

### REQ-003 — Les contraintes redeviennent des variables ordinaires
- **Exigence** : `sigma_*` et `tau_*` ne sont plus le « résultat » d'une vérification. La notion `results` de `lib/shown-variables.json` (#39, D-05) est retirée avec ce qui la lit : `shown-results`, `level-plan(results:)`, `check-shown(results:)`, `shown_variables.results`, `member_check.locked_keys`. Au niveau −1, une contrainte non nommée ne s'imprime pas, et `shown:` peut lui donner 1, 2 ou 3 comme à toute variable.
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : `verify-tension(…, level: -1, shown: (:))` n'imprime pas σ_t,0,d ; plus aucune occurrence de `results` dans `lib/shown-variables.json`, ni de `shown-results` / `locked_keys` dans le code.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Le verdict dans le volet de droite, `0 | 1 | 2 | 3`
- **Exigence** : au niveau −1 d'une vérification de barre, le volet de droite de «Affichage» (et le panneau de l'onglet de la vérification) propose chaque verdict que la vérification imprime, avec ses quatre boutons `0 | 1 | 2 | 3`. Aucune ligne n'est plus verrouillée : toutes vont de 0 à 3, et l'infobulle `ds_shown_locked` est retirée dans les trois langues.
- **Source** : T1, T3
- **Langues** : fr / de / en (une chaîne retirée, aucune ajoutée)
- **Critère d'acceptation** : pour une vérification de traction, `member_check.shown_keys` contient `eta` ; pour une compression avec stabilité, `eta_s`, `eta_y` et `eta_z` ; `LevelControl` les montre avec `0 | 1 | 2 | 3` ; régler `eta` sur 0 l'enlève de l'appel, régler σ sur 0 aussi (test).

### UI-002 — Le verdict nommé par son symbole (déduit)
- **Exigence** : dans le volet, un verdict porte le symbole de sa ligne dans le tableau des résultats de l'onglet (η_c,y, η_m,t…, le `symbol` des lignes de `_compute`), et non le nom de la clé. La page, elle, imprime le rapport σ/f ⩽ 1 et non η (ARCH-RISK-002).
- **Source** : déduit de T3 (le verdict doit se reconnaître)
- **Langues** : symboles mathématiques, pas de mot
- **Critère d'acceptation** : la ligne `eta_y` d'un flambage s'affiche η_c,y.

### UI-003 — L'infobulle de la sélection manuelle (revue)
- **Exigence** : `ds_shown_tip` ne dit plus que le verdict s'imprime toujours ; seul le titre s'imprime toujours. À corriger en fr/de/en.
- **Source** : revue (ARCH-RISK-006)
- **Langues** : fr / de / en
- **Critère d'acceptation** : les trois textes ne parlent plus du verdict.

## 5. Exigences d'architecture

### ARCH-002 — Les lignes Python reprennent les clés de Typst (revue)
- **Exigence** : là où Typst imprime le verdict d'une section seule sous `eta_s` (compression sans stabilité, flexion à 0° sans stabilité, avec ou sans N), `_compute` ajoute la ligne `eta_s` avant `eta`, et `eta` prend la formule `eta_s`, comme Typst le stocke et comme `_compute_lateral` le fait déjà. `shown_keys` reste `own ∩ rows`, sans règle de plus.
- **Source** : revue (ARCH-RISK-001)
- **Critère d'acceptation** : `test_member_check` confirme que les lignes et le registre Typst sont égaux, `eta_s` compris.

### ARCH-001 — Une seule source pour les clés
- **Exigence** : les clés de verdict sont écrites une seule fois, dans `lib/shown-variables.json`, que lisent `calc-engine.typ` et `calc/shown_variables.py`. Le choix des verdicts que la fenêtre propose pour un enregistrement est fait dans `calc/domains/member_check.py` (sans Qt), à partir des lignes de `_compute`, et un test confirme que ce sont exactement les verdicts que Typst imprime.
- **Source** : principes 1 et 2 (docs/architecture/principles.md), déduit
- **Critère d'acceptation** : `tests/test_member_check.py` compile, pour chaque type de vérification de l'exemple, `show-check-member` au niveau −1 avec chaque verdict proposé, et confirme que chacun s'imprime.

## 6. Contraintes

- **CON-001** — Hors du niveau −1, rien ne change sur la page d'un rapport (niveaux auto, 0 à 3). Déduit.
- **CON-002** — Un rapport existant avec `level: -1` et un `shown:` qui donne un niveau à une contrainte σ/τ compile toujours, la contrainte restant une clé valide. En revanche, un rapport qui comptait sur l'impression automatique du résultat (#39) ne l'a plus : c'est le prix accepté (D-02).
- **CON-003** — `verify-shear-off` et `verify-shear-perp`, qui ne prennent pas `shown:`, ne changent pas.

## 7. Décisions prises

- **D-01** — Une clé par verdict (`eta`, `eta_s`, `eta_y`, `eta_z`, `eta_m`, `eta_m_t`, `eta_m_c`), et non une seule clé `verify`. Raison : on peut cacher un verdict et garder l'autre. Prix : plus de boutons, et des noms en `eta_*`. (Q-001, 14.10.2026)
- **D-02** — Un verdict absent de `shown:` ne s'imprime pas, comme toute clé. Raison : une seule règle. Prix : un appel −1 existant perd son verdict sans avertissement. (Q-002, 14.10.2026) Cela renverse D-05 de l'issue #39.
- **D-03** — Les contraintes σ/τ ne sont plus un « résultat » et n'ont plus aucun statut particulier. (T2)

## 8. Hors périmètre

- Les commandes de la vérification acier (`show-check-steel`), dont les clés sont celles de l'export.
- `show-calc`, `show-connector-resistance`, `show-polar-moment`.
- La forme du verdict elle-même (le texte de `verify-core`).

## 9. Idées non retenues comme exigences

_(aucune)_

## 10. Questions

### Q-001 — Sous quelle clé le verdict est-il nommé dans `shown:` ?
- **Pourquoi elle compte** : la syntaxe d'appel, le nombre de boutons.
- **Options** : A une clé `verify` pour tous les verdicts, B une clé par verdict.
- **Réponse** : B, une clé par verdict — l'ingénieur, 14.10.2026.

### Q-002 — Un appel −1 qui ne nomme pas le verdict l'imprime-t-il ?
- **Pourquoi elle compte** : la compatibilité des rapports existants, l'uniformité de la règle.
- **Options** : A oui, au niveau 1 ; B non, absent = 0.
- **Réponse** : B — l'ingénieur, 14.10.2026.

## 11. Critères d'acceptation

- [x] REQ-001 — les clés `eta*` sont acceptées par `shown:`, et une clé inconnue est refusée.
- [x] REQ-002 — le verdict à −1 suit son niveau (0 absent, 1 bref, 2/3 complet) ; la page aux niveaux 1 à 3 est inchangée.
- [x] REQ-003 — `results` et tout ce qui le lit sont retirés ; une contrainte non nommée ne s'imprime pas.
- [x] UI-001 — le volet propose les verdicts, `0 | 1 | 2 | 3` partout, rien de verrouillé, `ds_shown_locked` retirée.
- [x] UI-002 — un verdict porte son symbole.
- [x] UI-003 — `ds_shown_tip` corrigée dans les trois langues.
- [x] ARCH-002 — les lignes `eta_s` ajoutées en Python, égales au registre.
- [x] ARCH-001 — les verdicts proposés pour chaque type de vérification sont exactement ceux que Typst imprime (test).
- [x] Documentation : le `///` de `level` et `shown` des six `verify-*` et de `show-check-member`, et leurs traductions dans `calc/i18n/commands.json` ; les exemples gelés `examples/verify-*` et `examples/show-check-member-*` en −1 (avec `eta*` ajouté) régénérés ; `docs/ui/window.md`, `docs/ui/tab-member-checks.md`, `docs/domain/member-checks.md`, `docs/typst/report-engine.md`, `docs/decisions.md` (§13, qui remplace D-05 de #39) et `docs/decisions-index.md`, une entrée `CHANGELOG.md`, la page « Nouveautés » en fr/de/en, et le texte `about` de `lib/shown-variables.json`.
- [x] Tests : `test_timber`, `test_member_check`, `test_member_check_tab`, `test_display_view` adaptés et étendus, et ils passent.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-002, UI-001 | capturé |
| T2 | REQ-001, REQ-003, D-03 | capturé |
| T3 | UI-001, UI-002 | capturé |
| revue | UI-003, ARCH-002 | ajouté par la revue |
| T4 | D-01, REQ-001 | décision |
| T5 | D-02, REQ-002 | décision |

### Points de la source non résolus

_(aucun)_

## 13. Revue d'architecture

Revue par `architecture-reviewer`, 14.10.2026. **Verdict : APPROUVER AVEC RÉSERVES.**

**Modules concernés** : `lib/shown-variables.json` ; `lib/calc-engine.typ:53-100` (`shown-results`, `check-shown`, `level-plan`, plus des commentaires à reprendre) ; `lib/timber.typ` (import l.12, `timber-verdict` l.275 et ses 28 appels, les `check-shown`/`level-plan` des verify-*, `show-check-member` l.1544, les `///` l.573-574 et l.1537-1538) ; `calc/shown_variables.py:49` ; `calc/domains/member_check.py:762-781`, 922, 1016 ; `calc/tools/display_view.py:125-240` ; `calc/tools/display_options.py` (`ds_shown_locked`, `ds_shown_tip`) ; `calc/tools/member_check_tab_actions.py:205-220` ; `calc/tools/steel_tab.py:57` ; `calc/i18n/commands.json` ; `examples/verify-*`, `examples/show-check-member-*`.

**À réutiliser** : `plan-at` (seul endroit où se décide le niveau d'une ligne) ; `LevelControl.set_keys((key, words, math))` ; le modèle `eta_s` puis `eta = eta_s` de `_compute_lateral`.

**Risques** :
- ARCH-RISK-001 (important) — `eta` en Python et `eta_s` en Typst pour une section seule → **ARCH-002** (ajouter les lignes, solution b).
- ARCH-RISK-002 (important) — la page imprime σ/f, pas η → **UI-002** reformulée : c'est le symbole du tableau des résultats.
- ARCH-RISK-003 (important) — intertitres gardés par `lv` → les côtés (Biegezug-/Biegedruckseite) suivent le niveau de leur verdict (≥ 2) ; « Tragsicherheit » et « Stabilität » ne changent pas (REQ-002).
- ARCH-RISK-004 (important) — `timber-verdict(plan, key, …)` sans test de type ; `verify-shear-off` et `verify-shear-perp` prennent `level-plan(level, none)`.
- ARCH-RISK-005 (important) — `///`, `commands.json`, les 21 exemples gelés → ajoutés au §11.
- ARCH-RISK-006 (important) — `ds_shown_tip` → **UI-003**.
- ARCH-RISK-007 (mineur) — l'ordre `eta_m_t`/`eta_m_c` varie selon N → l'ordre du JSON est un sur-ensemble, c'est documenté.
- ARCH-RISK-008 (mineur) — code mort (`locked`, `results()`, `steel_tab.locked_keys_of`) → retiré.
- ARCH-RISK-009 (mineur) — un verdict absent disparaît sans prévenir (D-02) → noté dans le CHANGELOG.

Aucun schéma, aucune `schema_version`, pas de Qt dans `calc/domains/`.

## 14. Plan d'implémentation

1. **Typst** — `lib/shown-variables.json` : ajouter les `eta*` aux `keys`, retirer `results`, mettre à jour `about`. `calc-engine.typ` : retirer `shown-results` et l'argument `results`, reprendre les commentaires. `timber.typ` : `timber-verdict(plan, key, …)` au niveau `plan-at(plan, key, 1)` ; les intertitres des côtés à `plan-at(plan, key, 2) >= 2` ; `verify-shear-off`/`perp` sur `level-plan(level, none)` ; `show-check-member` ; les `///`. (REQ-001 à 003, CON-001, CON-003) — tests `test_timber`.
2. **Python, domaine** — `shown_variables.results` retiré ; `member_check` : les lignes `eta_s` (l.922 compression, l.1016 flexion), `locked_keys` retiré, une fonction `shown_choices(record)` qui donne `(key, None, symbol)`. (ARCH-002, UI-002) — tests `test_member_check`.
3. **Fenêtre** — `LevelControl` sans `locked` ; `member_check_tab_actions` et `steel_tab` ; `ds_shown_locked` retirée, `ds_shown_tip` corrigée en fr/de/en. (UI-001, UI-003) — tests `test_display_view`, `test_member_check_tab`.
4. **Commandes et exemples** — `calc/i18n/commands.json` ; les exemples −1 avec `eta*` ; `examples/out` régénéré. — `test_examples` / `test_command_docs`.
5. **Docs** — window.md, tab-member-checks.md, member-checks.md, report-engine.md, decisions.md, decisions-index.md, CHANGELOG, Nouveautés fr/de/en.
6. **Tests** — la suite complète.

## 15. Vérification

_(à venir)_

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-14 | draft | spécification extraite de l'issue #58 |
| 2026-10-14 | specified | Q-001 et Q-002 répondues avant la rédaction (D-01, D-02) |
| 2026-10-14 | reviewed | revue APPROUVER AVEC RÉSERVES (§13) ; ARCH-002 et UI-003 ajoutées ; plan écrit (§14) |
| 2026-10-14 | approved → implementation | approuvée par l'ingénieur |
| 2026-10-14 | implementation | étape 1 faite : shown-variables.json (clés eta*, results retirés), calc-engine.typ, timber.typ (timber-verdict(plan…), intertitres des côtés, shear-off/perp) ; test_timber vert (REQ-001 à 003) |
| 2026-10-14 | implementation | étapes 2 et 3 faites : lignes eta_s (compression, flexion à 0°), shown_choices, locked_keys et results() retirés, LevelControl sans verrou, ds_shown_locked retirée, ds_shown_tip corrigée ; test_member_check, test_member_check_tab, test_display_view verts (UI-001 à 003, ARCH-001, ARCH-002) |
| 2026-10-14 | implementation | étapes 4 et 5 : `///` et commands.json (fr/de/en), exemples −1 avec clés eta*, docs (window, tab-member-checks, member-checks, report-engine, decisions + index), CHANGELOG, Nouveautés 0.118 fr/de/en ; rendu des exemples en cours |
| 2026-10-14 | verification | exemples rendus (431) : seules les pages verify-* et show-check-member-* −1 changent, le bruit de rendu des autres PNG remis à leurs octets commités ; vérification indépendante lancée |
| 2026-10-14 | completed | vérification ✅ sur tous les éléments ; spec déplacée dans `completed/` |
