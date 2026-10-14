---
id: 2026-10-14-neige-vent-affichage-altitude
titre: Neige et vent — variables choisies en «Affichage», croquis de la neige retiré du rapport, altitude au-dessus de 2000 m
status: completed
cree: 2026-10-14
mis_a_jour: 2026-10-14
source: message écrit (commande /issue), issues GitHub #56 et #57
docs: [docs/domain/loads.md, docs/ui/window.md, docs/typst/report-engine.md]
---

# Neige et vent — affichage, croquis, altitude — Spécification

## 1. Objectif

Dans les onglets «Neige» et «Vent», le mode «Affichage» doit permettre de choisir chaque variable imprimée et son niveau, comme les autres onglets le permettent déjà. Le rapport n'imprime plus de graphique pour la neige. Une altitude au-dessus de 2000 m n'est plus refusée : Woodcore avertit que la norme ne la couvre pas, et le rapport n'en dit rien.

## 2. Source

Message de l'ingénieur du 14.10.2026, classé en issues #56 et #57 :

> **T1** — « pour le calcul de la charge de neige et de la charge du vent dans Woodcore. Dans le mode affichage, il faut également pouvoir choisir toutes les variables à afficher ou non avec leur niveau. »
>
> **T2** — « De plus, pour la neige, il ne faut afficher aucun graphique. »
>
> **T3** — « Et dans le calcul de la neige, il faut pouvoir indiquer une altitude plus grande que 2000 mètres et simplement avoir un message d'avertissement dans Woodcore, mais pas dans Tipst, que cela n'est pas autorisé par la norme. »
>
> Réponses données lors du classement (/issue, 14.10.2026) :
>
> **T4** — Le choix des variables et de leur niveau vit « Dans l'appel » : un argument de `show-calc`, réglé dans «Options de la commande», rien dans la source.
>
> **T5** — « aucun graphique » = « Retirer du rapport » : `show-calc` n'imprime plus le croquis (`snow_svg`) à aucun niveau.

## 3. Exigences fonctionnelles

### REQ-001 — Variables choisies une à une pour la neige et le vent
- **Exigence** : Woodcore doit offrir, dans la vue «Affichage» des onglets «Neige» et «Vent» (et «Poids propre et surcharge», D-05), le niveau de détail de `show-calc` avec **-1 «Sélection manuelle»** : chaque variable (et chaque tableau) de l'instance avec ses boutons `0 | 1 | 2 | 3`, l'appel écrit `#show-calc("snow-load", "<id>", level: -1, shown: (…))`. Rien n'est écrit dans `loads/<kind>/<id>.json`.
- **Source** : T1, T4
- **Priorité** : doit
- **Critère d'acceptation** : un test de `tests/test_load_tab.py` vérifie que l'entrée «show-calc» des deux onglets porte la commande `show-calc` (son panneau, l'option `detail`) et que `context["shown"]` offre les clés de l'instance exportée ; l'appel avec `level: -1, shown: (s_k: 1)` compile.

### REQ-002 — Aucun croquis de la neige dans le rapport
- **Exigence** : l'instance `snow-load` exportée ne porte plus de `figures` : `show-calc` n'imprime le croquis de la disposition à aucun niveau, et `figure-1` n'est plus offert dans la sélection manuelle.
- **Source** : T2, T5
- **Priorité** : doit
- **Critère d'acceptation** : `snow_source.build_instance(...)` ne contient pas de clé `figures` ; l'export n'écrit aucun `calculations/snow-load-*.svg` ; le volet «Calcul» de l'onglet montre toujours le croquis (D-03).

### REQ-003 — Altitude au-dessus de 2000 m acceptée
- **Exigence** : une source dont `h_0` dépasse 2000 m (`max_altitude` du fichier de norme, 5.1.4) n'est plus refusée : elle est calculée par l'équation (10) comme les autres.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : `check_source` accepte `h_0 = 2100` et `build_instance` rend `s_k` de l'équation (10) ; l'export n'est pas arrêté.

### REQ-004 — Avertissement dans Woodcore, rien dans Typst
- **Exigence** : au-dessus de 2000 m, Woodcore avertit que SIA 261 5.1.4 n'autorise pas ce calcul ; le rapport compilé ne contient aucune mention de cet avertissement.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : l'onglet «Neige» montre le message dans un callout d'avertissement pour `h_0 = 2100` et pas pour `h_0 = 1900` ; l'instance exportée ne porte aucune var ni texte de cet avertissement ; l'export n'émet aucune notice (D-04).

## 4. Exigences d'interface

### UI-001 — Message d'avertissement en trois langues
- **Exigence** : le message de REQ-004 existe en fr, de et en (`ld_` de `load_tab.py`), et cite 5.1.4 et la limite lue dans le fichier de norme (non écrite dans le texte).
- **Source** : T3, principe (trois langues, pas de valeur codée en dur)
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_i18n.py` passe ; la valeur 2000 vient de `max_altitude`.

## 5. Exigences d'architecture

### ARCH-001 — Le calcul reste dans le domaine
- **Exigence** : la décision « au-dessus de la limite » est prise par `calc/domains/snow_source.py` (sans Qt), qui la rend à l'onglet ; l'onglet l'affiche sans recalculer.
- **Source** : principe (docs/architecture/principles.md, logique métier hors UI) — inféré
- **Critère d'acceptation** : `load_tab.py` ne compare pas `h_0` à une limite.

### ARCH-002 — Réutiliser le niveau -1 existant
- **Exigence** : REQ-001 réutilise `display_options.SPECS["show-calc"]`, `shown_variables.export_choices` et `LevelControl`, sans nouvel argument Typst ni nouvelle clé dans `lib/shown-variables.json`.
- **Source** : T4 et l'existant (docs/typst/report-engine.md, issue #20) — inféré
- **Critère d'acceptation** : aucun changement de `lib/calc-engine.typ` pour REQ-001.

## 6. Contraintes

- **CON-001** — Les valeurs de norme restent lues de `calc/norms/sia261-2020-5.2-schnee.json` (`max_altitude`, 5.1.4). Source : CLAUDE.md (inféré).
- **CON-002** — Les sources existantes restent valides sans migration ; aucun schéma de source ne change. Source : T4 (inféré).
- **CON-003** — Le renversement de la décision « au-dessus de 2000 m refusé » (REQ-002 de la spec 2026-10-12-audit-issues-47-48-49) est écrit dans `docs/decisions.md`. Source : CLAUDE.md (inféré).

## 7. Décisions prises

- **D-01** (T4, 14.10.2026) — Le choix des variables vit dans l'appel, pas dans la source. Il est réalisé par l'argument existant `level: -1, shown:` de `show-calc` (constat du code, ARCH-002), pas par un nouvel argument.
- **D-02** (T5, 14.10.2026) — Le croquis de la neige est retiré du rapport à tous les niveaux.
- **D-03** (Q-001, 14.10.2026, précisée par la revue ARCH-RISK-001) — Le croquis reste dans le volet de droite de la vue «Calcul» de l'onglet «Neige». L'instance ne porte plus ni `figures` ni `_files` (sinon `registry._build_source` écrirait le `.svg`) ; l'onglet demande le croquis au domaine, `snow_source.sketch(src)`.
- **D-04** (Q-002, 14.10.2026) — L'avertissement au-dessus de 2000 m est dans l'onglet «Neige» seulement (callout) : ni notice à l'export, ni Typst.
- **D-05** (Q-003, 14.10.2026) — La sélection manuelle vaut pour les trois onglets de charges, branchée dans `LoadTab`.

## 8. Hors périmètre

- La charge de vent n'a pas de croquis ; rien n'est retiré pour le vent.
- Une méthode de calcul de la neige propre au site au-dessus de 2000 m : le calcul suit l'équation (10) tel quel.

## 9. Idées non retenues comme exigences

Aucune.

## 10. Questions

### Q-001 — Le croquis reste-t-il dans la vue «Calcul» de l'onglet ?
- **Pourquoi elle compte** : T2 parle du mode Affichage ; le volet de droite de «Calcul» montre aussi le croquis.
- **Options** : A (recommandée) garder le croquis dans «Calcul», le retirer seulement du rapport — B le retirer partout, la fonction `snow_svg` n'étant plus appelée.
- **Réponse** : A — garder dans «Calcul» (14.10.2026) → D-03.

### Q-002 — Où l'avertissement au-dessus de 2000 m apparaît-il ?
- **Pourquoi elle compte** : « dans Woodcore » peut être l'onglet seul ou aussi le panneau des notices à l'export.
- **Options** : A (recommandée) dans l'onglet «Neige» (callout) et dans les notices (triangle orange) à chaque export — B dans l'onglet seulement.
- **Réponse** : B — dans l'onglet seulement (14.10.2026) → D-04.

### Q-003 — La sélection manuelle vaut-elle aussi pour «Poids propre et surcharge» ?
- **Pourquoi elle compte** : les trois onglets partagent `LoadTab` ; brancher le panneau dans la base le donne aux trois sans code de plus.
- **Options** : A (recommandée) oui, les trois onglets de charges — B neige et vent seulement.
- **Réponse** : A — les trois onglets (14.10.2026) → D-05.

## 11. Critères d'acceptation

- [x] REQ-001 — «Affichage» de «Neige» et «Vent» offre -1 et les clés de l'instance ; l'appel avec `shown:` compile.
- [x] REQ-002 — l'instance `snow-load` ne porte plus de `figures`.
- [x] REQ-003 — `h_0 = 2100` est accepté et calculé.
- [x] REQ-004 — avertissement dans Woodcore au-dessus de la limite, rien dans l'instance ni le rapport.
- [x] UI-001 — message en fr/de/en, limite lue de la norme.
- [x] ARCH-001 — la limite est jugée par `snow_source`, pas par l'onglet.
- [x] ARCH-002 — aucun changement de `lib/` pour REQ-001.
- [x] Documentation : `docs/domain/loads.md`, `docs/ui/window.md`, `docs/decisions.md`, `CHANGELOG.md`, «Nouveautés» fr/de/en.
- [x] Tests : `tests/test_snow_source.py`, `tests/test_load_tab.py` étendus et verts.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, ARCH-002 | capturé |
| T2 | REQ-002, Q-001 | capturé, une question |
| T3 | REQ-003, REQ-004, UI-001, ARCH-001, Q-002 | capturé, une question |
| T4 | D-01 | décision |
| T5 | D-02 | décision |

### Points de la source non résolus

Aucun (Q-001 à Q-003 répondues le 14.10.2026).

## 13. Revue d'architecture

Agent `architecture-reviewer`, 14.10.2026. **Verdict : APPROUVER AVEC RÉSERVES.**

- **Modules** : `calc/tools/load_tab.py` (`display_entries` 694, `refresh` 625, `fill_figure`, `save` 790), `calc/domains/snow_source.py` (`check_source` 102-104, `build_instance` 254-256), `calc/registry.py:183-185` (`_build_source` écrit tout `_files`), `calc/shown_variables.py` (`export_choices`), `calc/tools/display_options.py:130` (`show-calc` porte déjà `DETAIL`).
- **À réutiliser** : le patron `Entry("calc", "show-calc", "show-calc", positional=…, context={"shown": export_choices(…)})` de `woodcore_gui_polar.py:979` et `variables_tab.py:1117` ; `sia261_snow.clause()["max_altitude"]` ; `snow_svg.render`.
- **ARCH-RISK-001 (bloquant)** — retirer `figures` en gardant `_files` laisse l'export écrire `snow-load-*.svg`. → `snow_source.sketch(src)` appelé par l'onglet, plus de `_files` pour la neige (D-03 précisée).
- **ARCH-RISK-002 (important)** — `export_choices` relirait `calculations.json` à chaque frappe (`refresh` → `fill_command`). → mémoriser les choix par (instance, mtime de l'export).
- **ARCH-RISK-003 (important)** — trois onglets : `DeadLoadTab` garde `figure-1`, offert par `export_choices`. → test sur les trois domaines.
- **ARCH-RISK-004 (important)** — `tests/test_i18n.py` ne lit pas `load_tab.STRINGS`. → test de parité fr/de/en des clés `ld_*`.
- **ARCH-RISK-005 (mineur)** — l'avertissement et `reason` partageraient le callout ; `fill_results` lit `reason`. → attribut `warning` distinct.
- **ARCH-RISK-006 (mineur)** — `max_altitude` reste dans le fichier de norme (contrôlé par `sia261_snow.py:57`) ; sa note dit qu'il n'est plus un refus.
- **ARCH-RISK-007 (mineur)** — un export ancien garde `figures` jusqu'au prochain export ; sans conséquence, noté au CHANGELOG.
- **Décisions renversées** : `docs/decisions.md` (le refus au-dessus de 2000 m, spec 2026-10-12-audit-issues-47-48-49 REQ-002).

## 14. Plan d'implémentation

1. **Domaine neige** — `calc/domains/snow_source.py` : retirer le refus de `check_source` ; ajouter `warnings(src) -> [(code, params)]` (limite et clause lues de la norme) ; extraire le calcul des μ ; `sketch(src)` ; `build_instance` sans `figures` ni `_files`. Note du fichier de norme. → REQ-002, REQ-003, REQ-004, ARCH-001, D-03. Tests : `tests/test_snow_source.py`.
2. **Onglet** — `calc/tools/load_tab.py` : `display_entries` avec la commande `show-calc` (panneau, `DETAIL`, `context["shown"]` mémorisé par mtime, `banner`, `note_text`) ; `fill_figure` par `MODULE.sketch` quand le module en a un ; callout de l'avertissement (`ld_warn_above_limit` fr/de/en). → REQ-001, REQ-004, UI-001, ARCH-002, D-05. Tests : `tests/test_load_tab.py` (trois onglets, callout, croquis, aucun `.svg`, parité des clés).
3. **Compilation** — un test `level: -1, shown:` sur la neige et le vent. → REQ-001.
4. **Documentation** — `docs/domain/loads.md`, `docs/ui/window.md`, `docs/decisions.md` (renversement), `CHANGELOG.md`, «Nouveautés» fr/de/en.
5. **Suite complète** par `finish`.

## 15. Vérification

Agent `requirements-verifier`, 14.10.2026, sur le diff depuis d19b091 et les tests qu'il a lancés lui-même.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `load_tab.display_entries` → `show-calc` avec son panneau et `context["shown"]` ; `test_the_three_load_tabs_offer_the_manual_selection_of_show_calc` ; compilation `level: -1, shown:` neige et vent |
| REQ-002 | ✅ | `snow_source.build_instance` sans `figures` ni `_files` ; `test_the_export_carries_a_snow_source_and_no_drawing` ; compilation 1-3 sans image, `figure-1` refusé |
| REQ-003 | ✅ | refus retiré de `check_source` ; `test_the_2000_m_limit_reads_the_site_altitude` |
| REQ-004 | ✅ | `snow_source.warnings`, `LoadTab.warning` dans le callout ; rien dans l'instance (test) |
| UI-001 | ✅ | `ld_warn_above_limit` fr/de/en ; `test_the_load_tab_words_exist_in_the_three_languages` ; `test_the_limit_is_read_from_the_norm_file` |
| ARCH-001 | ✅ | la comparaison n'est que dans `snow_source.warnings` |
| ARCH-002 | ✅ | `lib/` inchangé |
| CON-001 à CON-003 | ✅ | `max_altitude` lu de la norme ; aucun schéma changé ; `decisions.md` + index |
| Documentation | ✅ | loads.md, window.md, report-engine.md, decisions.md, CHANGELOG, Nouveautés 0.118 fr/de/en (le lien du CHANGELOG vers `completed/` tient une fois la spec déplacée) |
| Tests | ✅ | test_snow_source 12, test_load_tab 6, test_docs_coherence 7, test_i18n 22, test_dead_load_source 12, test_wind_source 10 |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-14 | draft | spécification extraite des issues #56 et #57 |
| 2026-10-14 | specified | Q-001 à Q-003 répondues (D-03 à D-05) |
| 2026-10-14 | reviewed | revue : approuver avec réserves ; D-03 précisée ; plan écrit |
| 2026-10-14 | approved | approuvée par l'ingénieur |
| 2026-10-14 | implementation | étape 1 faite : `snow_source` (refus retiré, `warnings`, `sketch`, plus de `figures`/`_files`), note de `max_altitude` — REQ-002, REQ-003, ARCH-001 |
| 2026-10-14 | implementation | étape 2 faite : `load_tab` (panneau `show-calc`, choix mémorisés par mtime, callout de l'avertissement, croquis par `sketch`, `ld_warn_above_limit` fr/de/en, `command_text` retiré) — REQ-001, REQ-004, UI-001, ARCH-002, D-05 |
| 2026-10-14 | testing | étape 3 faite : test de compilation (neige 1-3 sans image, `figure-1` refusé, -1 neige et vent) ; `--related` : 63 tests verts |
| 2026-10-14 | verification | étape 4 faite : loads.md, window.md, report-engine.md, decisions.md (+ index), CHANGELOG, Nouveautés 0.118 fr/de/en |
| 2026-10-14 | completed | vérification ✅ sur tous les éléments ; spec déplacée dans completed/ |
