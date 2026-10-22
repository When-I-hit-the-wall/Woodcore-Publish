---
id: 2026-10-19-base-saine-nettoyage
titre: Base saine — nettoyage décidé sur l'audit du 19.10.2026
status: verification
cree: 2026-10-19
mis_a_jour: 2026-10-20
source: message écrit (réponses de l'ingénieur au rapport 000-Audits/261019-audit-base-saine.md)
docs: [docs/architecture/principles.md, docs/architecture/layout.md, docs/ui/window.md, docs/typst/formulas.md, docs/typst/api-conventions.md, docs/conventions/testing.md, docs/domain/loads.md, docs/architecture/reference-library.md]
---

# Base saine — nettoyage décidé sur l'audit du 19.10.2026 — Spécification

## 1. Objectif

Appliquer les décisions de l'ingénieur sur le rapport d'audit `000-Audits/261019-audit-base-saine.md` (issues #67 à #71, mère #73). Le but est de repartir d'une base où un onglet, un moteur de calcul et un moteur de dessin ont chacun une seule forme, où chaque valeur de norme vient d'un JSON, et où les formules s'impriment de la même façon partout. C'est un programme en plusieurs lots : chaque lot est implémenté, testé et commité à part (§14), pour qu'une interruption ne laisse jamais un lot à moitié fait.

## 2. Source

> **T1** — « 3. Structure des onglets (#68) => Solution B »
>
> **T2** — « 4. Moteurs de calcul et de dessin (#69) => corrige C1 à C7 (pour le C6, c'est tout à fait normal de calculer en python, puis en typst). »
>
> **T3** — « 4.2 Dessin => Corrige D1 à D8 »
>
> **T4** — « 4.3 Incohérences générales => corrige G1 à G9 »
>
> **T5** — « 5. Normes et affichage des formules (#70) => laisse N1 de côté pour le moment. »
>
> **T6** — « N2: vérifie que les deux sources disent la même chose. En cas de doute, vérifie dans la SIA261. À la fin, les sources des valeurs doivent se trouver dans des fichiers .json. »
>
> **T7** — « N5: ne modifie rien, le comportement actuelle est juste. »
>
> **T8** — « N6: retire ce chemin du poste. »
>
> **T9** — « Affichage des formules, divergences d'un onglet à l'autre : unifie l'affichage des indices. »
>
> **T10** — « Les grands nombres: toujours en notation scientifique au-delà de 99'999. »
>
> **T11** — « Toujours 3 décimales après la virgule (sauf si zéro e.g. 3.120 => 3.12). »
>
> **T12** — « constantes dans les formules: corrige. »
>
> **T13** — « Niveau de détail: corrige (décié par la commande). »
>
> **T14** — « Commandes sans niveau: corrige, il faut des niveaux pour toutes les commandes. »
>
> **T15** — « Mise en forme: uniformise. »
>
> **T16** — « La suite dure 31 minutes => créé un niveau "Rapide" »
>
> **T17** — « Les copies du moteur dans les projets. => est-il possible de ne plus copier les moteurs dans les projets ? Tout le moteur tourne dans woodcore, sans copie des fichiers dans les projets? »
>
> **T18** — « Le coût d'un onglet: n'existera plus maintenant... »
>
> **T19** — « 6.2 Améliorations d'architecture, par ordre de rendement. Je valide 1, 2, »
>
> **T20** — « Explique ce qu'est 3. Je souhaite toujours avoir un calcul python rapide, et un double en typst, pour pouvoir le modifier facilement (à moins que l'on décide maintenant dans typst de charger un fichier python. On modifierait alors directement le fichier python pour modifier les calculs. Cela est-il possible? On devrait pouvoir garder toutes les options pour les commandes (normes, in-line, variable affichée, etc...). »
>
> **T21** — « Je valide 9. »
>
> **T22** — « Je valide Un graphe de dépendances du projet »
>
> **T23** — « 7. Plan de nettoyage proposé => je valide 1, 2, 3, 6, 7, 8, 9. »
>
> **T24** — « 8.1. toutes » (les suppressions du §2 du rapport)
>
> **T25** — « 8.2. ids(), show-load-summary(), get(), helper interne commun »
>
> **T26** — « 8.3. Garder » (les six onglets réservés)
>
> **T27** — « 8.4. C » (structure des onglets)
>
> **T28** — « 8.5. déjà répondu »
>
> **T29** — « 8.6. oui » (job Windows dans la CI, niveau de tests rapide)

## 3. Exigences fonctionnelles

### REQ-001 — Suppressions du code mort
- **Exigence** : Woodcore doit retirer tout ce que le §2 du rapport liste. Cela comprend :
  - les modules `migrate_to_schemas.py`, `catalog_gui.py` et `build_document_templates.py` ;
  - avec `migrate_to_schemas.py`, la lecture des formats de connecteurs et d'assemblages d'avant v0.74 (Q-016) ;
  - les environ 45 définitions sans appelant ;
  - la commande interne `distance-scopes` ;
  - `show-plan-legend` et `moisture-class-of`.
  - **Exceptions (revue, ARCH-RISK-405)** : `calc/norms/sia260.py` est gardé, car sa table ψ attend l'onglet « Combinaisons », qui est conservé (CON-004). `schema-ids` n'est pas supprimé : il devient `ids("schema")` (REQ-002).
- **Source** : T24, T23 (lot 2)
- **Priorité** : doit
- **Critère d'acceptation** : aucun des noms listés n'existe plus dans `calc/`, `lib/`, `templates/` ni dans le catalogue `calc/i18n/commands.json`, hors de la table des noms retirés (`lib/renamed-commands.json`). Une commande retirée qu'une section appelle encore fait échouer l'export avec un message qui dit par quoi la remplacer. La suite est verte.

### REQ-002 — Fusion des commandes
- **Exigence** : les 13 commandes `*-ids` deviennent `ids(kind)`. `show-load-summary` et `show-line-load-summary` deviennent `show-load-summary(unit:)`. Les 8 accesseurs `get-*` deviennent `get(v, champ)`. `doc-plan`, `doc-fire-plan` et `doc-extract`, `sheet-legend` et `sheet-fire-legend`, `sheet-viewport` et `sheet-fire-viewport` partagent un helper interne, et leurs noms restent.
- **Source** : T25
- **Priorité** : doit
- **Critère d'acceptation** :
  - chaque nouvelle commande a son bloc `///`, deux exemples qui compilent et ses traductions dans `commands.json` ;
  - les gabarits de `templates/` et le projet exemple appellent les nouvelles formes ;
  - les sections d'un projet qui appellent un ancien nom sont réécrites vers le nouveau à l'ouverture du projet, chaque fichier sauvegardé dans les archives d'abord (Q-006) ; un test le prouve sur une copie du projet exemple ;
  - `tests/test_commands.py` est vert.

### REQ-003 — Les valeurs de neige et de vent : une seule source, en JSON
- **Exigence** : comparer chaque valeur SIA 261 que le chemin « classeur » (`snow.py`, `wind.py` : C_e, Δh, μ, c_pe…) et le chemin JSON (`sia261-2020-5.2-schnee.json`, tables du vent) utilisent. Toute différence est tranchée sur la SIA 261:2020 elle-même. À la fin, les valeurs de norme sont lues dans les JSON de `calc/norms/` sur les deux chemins.
- **Source** : T6, T23 (lot 6)
- **Priorité** : doit
- **Critère d'acceptation** :
  - un tableau de comparaison (valeur, classeur, JSON, SIA 261 page/tableau, verdict) est écrit dans §13 ou dans `docs/domain/loads.md` ;
  - chaque différence est corrigée dans le JSON, d'après la norme ;
  - `snow.py` et `wind.py` ne lisent plus aucune valeur de norme dans le classeur ;
  - un test compare les deux chemins sur le projet exemple.

### REQ-004 — N6 : le chemin des normes
- **Exigence** : le chemin `ExternalFiles/000-Normes/` est retiré des champs `_source` des JSON de `calc/norms/`, qui gardent norme, édition, clause et nom du PDF ; les tests qui lisent la bibliothèque de normes la trouvent par une variable d'environnement (Q-008).
- **Source** : T8
- **Priorité** : doit
- **Critère d'acceptation** : `grep -r "ExternalFiles/000-Normes" calc/ lib/ docs/ tests/` ne trouve plus rien hors de `docs/history/` et `docs/decisions.md` ; la variable est documentée dans `docs/conventions/testing.md`.

### REQ-005 — Niveau de tests « Rapide »
- **Exigence** : `python tests/run_tests.py --fast` exécute un sous-ensemble (moteur, normes, export, contrats) en moins de 3 minutes sur le poste de l'ingénieur. La suite entière reste le défaut et tourne en CI.
- **Source** : T16, T29
- **Priorité** : doit
- **Critère d'acceptation** :
  - la durée de `--fast` est mesurée et écrite dans `docs/conventions/testing.md` ;
  - chaque fichier de test déclare son niveau, et un test vérifie que chacun en déclare un.

### REQ-006 — CI sous Windows
- **Exigence** : le job `windows-2025` existant de `.github/workflows/tests.yml` lance le niveau « Rapide » à chaque push et chaque PR ; la suite complète reste sur `master` (revue, ARCH-RISK-410).
- **Source** : T21, T29
- **Priorité** : doit
- **Critère d'acceptation** : le job existe, et `tests/test_ci_workflow.py` le vérifie (actions épinglées, lecture seule).

## 4. Exigences d'interface (rapport)

### UI-001 — Indices unifiés
- **Exigence** : un même indice s'imprime de la même façon dans tous les onglets et toutes les commandes (acier, goujons, bois, domaines écrits à la main), selon Q-004 : indices descriptifs droits, sous la forme de la norme (`N_Rd`, `γ_M1`, `f_m,y,d`), un indice-variable en italique (`σ_x`).
- **Source** : T9
- **Langues** : sans objet (notation)
- **Critère d'acceptation** : `N_Rd`, `N_Ed`, `γ_M1`, `f_m,y,d` s'impriment à l'identique dans `show-calc`, `show-check-steel`, `show-connector-resistance`, `verify-*` et `eq`. Un test compare le balisage produit.

### UI-002 — Grands nombres
- **Exigence** : au-delà de 99 999 en valeur absolue, un nombre s'imprime toujours en notation scientifique (`a · 10ⁿ`), quelle que soit la commande qui l'imprime.
- **Source** : T10
- **Critère d'acceptation** : `show-calc` et `eq` impriment la même valeur 60910.397 de la même façon. Un test le vérifie sur toutes les fonctions de formatage (`fmt-*`, `value-text`, `value-in-formula`, `formula-number`).

### UI-003 — Décimales
- **Exigence** : 3 décimales au plus, les zéros finaux retirés (3.120 → 3.12), partout, constantes comprises ; au moins 3 chiffres significatifs, et quand cela demanderait plus de 3 décimales, notation scientifique (0.00234 → 2.34 · 10⁻³) (Q-005).
- **Source** : T11
- **Critère d'acceptation** :
  - aucun nombre **affiché** ne suit une autre règle ; les valeurs **transportées** entre Python et Typst gardent leur pleine précision (`fmt_exact`, D-22) ;
  - le `_fmt` Python existe en une seule copie ;
  - un test fixe des cas (3.120 → 3.12, 0.75, 1/3 → 0.333, 0.00234 → 2.34 · 10⁻³, 0.0234 → 2.34 · 10⁻², 123456 → 1.235 · 10⁵, 99999 → 99999).

### UI-004 — Constantes dans les formules
- **Exigence** : une constante affichée dans une formule est composée à partir de la valeur qui sert au calcul, comme dans `dowel.py`. Elle n'est jamais tapée dans la chaîne. L'acier (N1) est hors périmètre.
- **Source** : T12, T5
- **Critère d'acceptation** : aucune constante numérique écrite dans une chaîne de formule hors `steel_resistance.py` (vérifié par un test qui parcourt les modules de domaine).

### UI-005 — Niveau de détail décidé par la commande
- **Exigence** : le niveau de chaque ligne est décidé par la commande Typst au moment de l'impression, comme pour le bois (`plan-at`). Python n'écrit plus de `level=` figé à l'export (acier, goujons, charges).
- **Source** : T13
- **Critère d'acceptation** : plus aucun `level=` littéral dans les exports Python. La même vérification imprimée aux niveaux 1, 2 et 3 change selon le niveau, et un test le vérifie pour chaque domaine.

### UI-006 — Toutes les commandes ont un niveau
- **Exigence** : chaque commande qui imprime quelque chose prend `level:`, c'est-à-dire chaque commande qui imprime un calcul, un tableau ou une figure (Q-007 : `show-*`, `verify-*`, `distance`, `doc-*`, `sheet-*`). C'est le cas notamment de `distance`, `show-fire-plan` et `show-plan`.
- **Source** : T14
- **Critère d'acceptation** : `build_reference` liste les commandes concernées, et chacune a un exemple `-L1` et un exemple `-L3` qui compilent.

### UI-007 — Mise en forme uniformisée
- **Exigence** :
  - le signe moins est toujours U+2212 ;
  - l'espace avant l'unité est toujours insécable, y compris avant « ° » ;
  - le séparateur décimal est le point dans les trois langues ;
  - le verdict d'utilisation a la même forme (σ/f ⩽ 1 ou %) partout.
- **Source** : T15
- **Critère d'acceptation** : un test de formatage couvre chaque règle sur toutes les fonctions de formatage de `lib/`.

## 5. Exigences d'architecture

### ARCH-001 — Structure des onglets
- **Exigence** : une classe de base `SourceEditorTab` porte liste, formulaire, résultat, nouveau / dupliquer / supprimer / enregistrer / exporter, l'Affichage et un seul `set_view` ; une `CanvasEditorTab` y ajoute toile et annulation (plan, plan feu, schémas, modèles statiques) ; une `BrowserTab` mince sert Structure, Variables, Commandes. Tous les onglets migrés en un passage (Q-001 : B d'un coup). Un registre `TabSpec` remplace les huit points de mise en place (6.2.2, lot 3).
- **Source** : T1, T27, T18, T19, T23
- **Critère d'acceptation** :
  - un onglet s'ajoute par une seule déclaration `TabSpec` plus son module ;
  - un test de contrat paramétré vérifie chaque onglet ;
  - les copies listées au §3 du rapport (`confirm_leave`, `update_list_marker`, Ctrl+S, `reload_list`, `on_list_change`, `on_moved`, `save` et les piles d'annulation) n'existent plus qu'une fois.

### ARCH-002 — Forme de résultat et citation (C1, C2)
- **Exigence** : C1 — `member_check` (rows), l'acier (`steel_calc.Calc`) et les domaines rendent leurs calculs par `engine.Calculation` (Q-002 : A), avec une nouvelle `schema_version` pour `checks` et `steel`, l'ancienne lue. C2 — toute ligne exportée par `member_check` et par l'acier porte `norm` et `norm_ref`, avec la norme réelle de la ligne : plus de `"SIA 265"` figé pour une ligne VKF ou feu. Le double calcul Python + Typst du bois est gardé (T2, T20).
- **Source** : T2, T20
- **Critère d'acceptation** : `steel_calc.Calc` n'existe plus ; `member_check._row` construit des lignes `engine` ; `_check_citation` est appliqué à toutes les lignes, et un test le vérifie.

### ARCH-003 — Domaines : C3, C4, C5, C6, C7
- **Exigence** :
  - **C3** : `steel-source` et `profile-source` sont validés par `validate_structure` ;
  - **C4** : les avertissements de `connector`, `dowel`, `wind` et `registry` sont des `engine.Note` ;
  - **C5** : un `Protocol` documenté décrit les domaines à source, et les noms des constantes de version sont harmonisés ;
  - **C6** : le docstring de `member_check.py` est corrigé, et le test de parité Python/Typst couvre chaque vérification ;
  - **C7** : `UnfoldError`, `DomainError`, `Refused` et `FormulaError` dérivent de `ValidationError`, ou sont attrapés là où l'export les attend.
- **Source** : T2
- **Critère d'acceptation** : un test par point. Aucun `print` sur stderr dans `calc/domains/`.

### ARCH-004 — Dessin : D1 à D8
- **Exigence** :
  - **D1** : une base de toile commune (zoom, outils, annulation, aimantation) pour plan, plan feu, schémas et modèles statiques ;
  - **D2** : un seul `SvgLayer`, et `_cosmetic` et `_round` en un exemplaire ;
  - **D3** : un seul `icon_from_svg` ;
  - **D4** : un module de géométrie plane partagé (cotes, aimantation, `normalize_angle`, `_inside`, `centroid`) ;
  - **D5** : une palette de figures dans un JSON, sans couleur ni police en dur dans les `*_svg` ;
  - **D6** : `svg_text.py`, seul endroit où s'écrit du SVG (`_f`, `_text`, `_escape`, `_unit`) ;
  - **D7** : les tailles calculées par Python sont exportées, et Typst ne les recalcule plus ; une seule fonction de nombre SVG ;
  - **D8** : l'azimut est calculé dans `statics_geometry.py`.
- **Source** : T3, T23 (lot 7)
- **Critère d'acceptation** : les doublons listés au §4.2 du rapport n'existent plus qu'une fois (vérifié par un test de doublons AST). Les figures du projet exemple restent identiques à l'octet près, ou leur différence est expliquée.

### ARCH-005 — Incohérences générales : G1 à G9
- **Exigence** :
  - **G1** : un seul écrivain de texte en LF, et un test qui interdit l'écriture nue ;
  - **G2** : `write_source` par domaine, qui vérifie la source puis l'écrit, appelé par les onglets ;
  - **G3** : `norms/_loader.py` partagé ;
  - **G4** : `domains/_common.py` (`fail`, `is_number`, `fmt_number`), et les unités lues dans `units.py` ;
  - **G5** : plus aucun `except Exception` sans justification, plus aucun `pass` silencieux ;
  - **G6** : `build_reference` et `usersettings` sortent de `tools/` (la scission de `variable_sources` est retirée par la revue, ARCH-RISK-311) ;
  - **G7** : la frontière entre mots de la fenêtre et mots du rapport est écrite dans CLAUDE.md et `docs/` ;
  - **G8** : glossaire des noms, `LABEL_COLOUR`, `woodcore_gui_polar.py` renommé en `polar_tab.py` ;
  - **G9** : `lib/calc-engine.typ` découpé par sujet.
- **Source** : T4, T19 (6.2.1), T23 (lot 1)
- **Critère d'acceptation** : un test par point (G1 : aucun `write_text` sans `newline` dans `calc/` ; G3 : un seul chargeur ; G4 : une seule définition de `_fail` ; G9 : `test_module_size` vert pour `lib/`).

## 6. Contraintes

- **CON-001** — Les rapports existants ne changent pas de valeurs. Seule la présentation change (UI-001 à UI-007), et chaque changement visible est dit dans la page « Nouveautés ». Source : T15 (déduite), CLAUDE.md.
- **CON-002** — Plusieurs sessions éditent le dépôt : un lot = un commit avec la suite verte, sans `checkout`, `stash`, `reset` ni `clean`. Source : CLAUDE.md.
- **CON-003** — Les sections des projets de l'ingénieur appellent les commandes par leur nom : une commande renommée ou retirée ne casse pas un projet sans le dire (Q-006). Source : déduite (rapport §6.1.5).
- **CON-004** — Les six onglets réservés sont gardés. Source : T26.
- **CON-005** — Une valeur de norme est lue sur une édition nommée. En cas de doute pour REQ-003, la SIA 261:2020 elle-même fait foi. Source : T6, CLAUDE.md.
- **CON-006** — Un contrat JSON qui change prend une nouvelle `schema_version`, et le lecteur accepte l'ancienne. Source : principes 8 et 10 (déduite).

## 7. Décisions prises

- **D-01** — Le double calcul du bois, en Python (rapide, pour la fenêtre) et en Typst (lisible et modifiable dans le rapport), est voulu et gardé (T2, T20).
- **D-02** — N1 (coefficients de l'acier en dur) est laissé de côté pour le moment (T5).
- **D-03** — N5 (`#eq`, `#var` et `#val` à la main sans citation par défaut) : le comportement actuel est juste, rien ne change (T7).
- **D-04** — Les six onglets réservés sont gardés (T26).
- **D-05** — Toutes les suppressions du §2 du rapport sont validées (T24).
- **D-06** — Fusions validées : `ids()`, `show-load-summary(unit:)`, `get()`, plus un helper interne commun pour les `doc-*` et `sheet-*` (T25).
- **D-07** — Un niveau de tests « Rapide » et un job Windows dans la CI (T16, T29).
- **D-08** — Les grands nombres au-delà de 99 999 s'impriment en notation scientifique. Les nombres ont 3 décimales au plus, sans zéros finaux (T10, T11).
- **D-09** — Le niveau de détail est décidé par la commande Typst (T13).
- **D-10** — Lots du plan du rapport validés : 1, 2, 3, 6, 7, 8 et 9, et le lot 5 (C1, C2) par Q-002. Le lot 4 (acier, N1) est hors périmètre (T23, Q-002).
- **D-11** — Onglets : solution B, d'un coup (Q-001).
- **D-12** — Indices droits, forme de la norme (Q-004) ; 3 chiffres significatifs, 3 décimales au plus, sinon notation scientifique (Q-005).
- **D-13** — Anciens noms de commandes : migration des sections à l'ouverture (Q-006).
- **D-14** — Typst n'exécute pas de Python : le calcul Python rapide et son double Typst restent (Q-002, T20).
- **D-15** — Moteur hors des projets et graphe de dépendances : specs dédiées après ce programme (Q-003, Q-009).
- **D-16** — Neige et vent : valeurs de norme en JSON seul, le classeur ne fournit que des entrées ; renverse `decisions.md:364,366` (Q-010).
- **D-17** — Une valeur saisie cite la norme et la clause où elle sert (Q-011).
- **D-18** — Niveaux des figures, tableaux et résumés : 1 seul, 2 + légende, 3 + détails ; renverse `decisions.md:131,479` (Q-012).
- **D-19** — Pas d'espace avant « ° » ; verdict en rapport η ⩽ 1 (Q-013, Q-014).
- **D-20** — Couleurs des figures fusionnées dans `lib/figure-palette.json` (Q-015).
- **D-21** — Formats de connecteurs et d'assemblages d'avant v0.74 non lus (Q-016).
- **D-22** — Transport et affichage séparés : les valeurs passent en pleine précision entre Python et Typst, seul l'affichage suit la règle des 3 décimales (revue, ARCH-RISK-401).

## 8. Hors périmètre

- N1 : les coefficients SIA 263 dans le code de l'acier (D-02).
- N5 : la citation par défaut des commandes écrites à la main (D-03).
- La construction des onglets à la demande (6.2.10 du rapport), non validée.
- Le graphe de dépendances du projet (Q-009) et l'arrêt des copies du moteur dans les projets par un paquet Typst local (Q-003) : chacun aura sa spec dédiée après ce programme.

## 9. Idées non retenues comme exigences

- T20 : « dans typst … charger un fichier python ». La question est posée (Q-002), la réponse est dans §10 : Typst n'exécute pas de Python.
- T18 : « Le coût d'un onglet n'existera plus » est la conséquence attendue d'ARCH-001, pas une exigence à part.

## 10. Questions

### Q-001 — Onglets : solution B ou C ?
- **Pourquoi elle compte** : T1 dit « Solution B » et T27 dit « C ». La première refond tous les éditeurs d'un coup ; la seconde migre service par service.
- **Options** :
  - **B** : une classe de base `SourceEditorTab` et un `CanvasEditorTab` pour les toiles, tous les éditeurs migrés. On gagne le plus ; c'est le lot le plus long, avec plusieurs milliers de lignes déplacées.
  - **C** : des services par composition (`SourceListController`, `SourceStore`, `DisplayHost`, `UndoHistory`), un par un. Le risque est faible à chaque étape, mais le gabarit unique n'est atteint qu'à la fin.
  - **B par étapes** : la classe de base B, construite à partir des services de C et migrée onglet par onglet. On atteint la cible B en gardant la sûreté de C.
- **Réponse** : **B d'un coup** — une classe de base `SourceEditorTab` (et `CanvasEditorTab` pour les toiles), tous les éditeurs migrés (l'ingénieur, 19.10.2026).

### Q-002 — Que fait le point 3 (une seule forme de résultat) ?
- **Explication** :
  - Aujourd'hui, les domaines Python rendent leurs calculs sous quatre formes : `engine.var/step/check` pour les charges et les goujons, `rows` pour les vérifications bois, `Calc` pour l'acier, `Result` pour les domaines.
  - Le point 3 les ramène à une seule, `engine.Calculation`, où chaque ligne porte son symbole, sa valeur, son unité, sa norme et sa clause (`_check_citation`).
  - Il ne retire **pas** le double calcul Python + Typst du bois : Python reste le calcul rapide de la fenêtre, Typst le double lisible et modifiable. Les options des commandes (normes, en ligne, variable affichée, niveaux) restent.
- **Typst peut-il charger un fichier Python ?** Non :
  - Typst n'exécute que des extensions compilées en WebAssembly (`plugin()`), et aucun interpréteur Python ne s'y branche de façon praticable.
  - La voie actuelle est la bonne : Python calcule et exporte, Typst imprime, et le Typst recalcule là où vous voulez pouvoir modifier la formule dans le rapport.
- **Options** :
  - **A** : unifier la forme de résultat (C1, C2) dans ce programme.
  - **B** : seulement C2, la citation obligatoire et juste dans chaque ligne ; C1 plus tard.
- **Réponse** : **A** — C1 et C2 : une seule forme de résultat, `engine.Calculation`, citation obligatoire ; le double calcul Python + Typst gardé (l'ingénieur, 19.10.2026).

### Q-003 — Ne plus copier le moteur dans les projets ?
- **Explication** :
  - **Pourquoi la copie existe.** Typst ne lit rien hors de la racine du projet. Le moteur (`lib/*.typ`) est donc copié dans `000-Woodcore/_woodcore/lib/` de chaque projet (`project.sync_engine`), et il lit les données par `json("../data/…")`.
  - **Ce qui est possible.** Woodcore installe son moteur comme **paquet Typst local versionné** (`@local/woodcore:0.120.0`) dans le dossier de paquets de Typst, hors des projets. Chaque projet ne garde qu'un fichier d'import de deux lignes, et ses données. Plusieurs versions vivent côte à côte, et un ancien projet compile avec la version qu'il nomme.
  - **Le prix.** Un paquet ne peut pas lire les fichiers du projet. Les environ 40 lectures `json("../data/…")` de `lib/` doivent recevoir les données du fichier du projet au lieu de les lire elles-mêmes, et tous les projets doivent être migrés. C'est un chantier à part entière.
- **Options** :
  - **A** : une spec dédiée après ce programme.
  - **B** : l'inclure ici, comme dernier lot.
  - **C** : garder la copie.
- **Réponse** : **A** — spec dédiée après ce programme (l'ingénieur, 19.10.2026).

### Q-004 — Quelle règle pour les indices ?
- **Pourquoi elle compte** : aujourd'hui, `N_(R d)` (italique, séparé), `F_"Ed"` (droit) et `f_(m,y,d)` (italique, virgules) coexistent.
- **Options** :
  - **A** : indices descriptifs **droits**, écrits comme la norme (`N_Rd`, `γ_M1`, `f_m,y,d`), conformément à l'ISO 80000-2. Seul un indice qui est une variable reste italique (`σ_x`).
  - **B** : tout en italique, sous la forme de la norme.
- **Réponse** : **A** — indices descriptifs droits, sous la forme de la norme (ISO 80000-2) ; un indice qui est une variable reste italique (l'ingénieur, 19.10.2026).

### Q-005 — Les petites valeurs, avec « 3 décimales »
- **Pourquoi elle compte** : avec 3 décimales fixes, 0.0023 s'imprimerait 0.002, et 0.00012 s'imprimerait 0.
- **Options** :
  - **A** : 3 décimales, et au moins 3 chiffres significatifs sous 0.01 ; sous 0.001, la notation scientifique.
  - **B** : 3 décimales strictes.
- **Réponse** : **Réponse libre** : « 3 chiffres significatifs, mais pas plus de 3 chiffres après la virgule. Donc 0.00234 => 2,34 * 10^-3. » Règle qui en découle : arrondir à 3 chiffres significatifs au moins ; si l'écriture demande plus de 3 décimales, notation scientifique (0.00234 → 2.34 · 10⁻³, 0.0234 → 2.34 · 10⁻², 0.234 → 0.234, 0.05 → 0.05) ; au-delà de 99 999, notation scientifique ; sinon 3 décimales au plus, zéros finaux retirés (l'ingénieur, 19.10.2026).

### Q-006 — Les anciens noms des commandes fusionnées ou retirées
- **Pourquoi elle compte** : les sections de vos projets les appellent (CON-003).
- **Options** :
  - **A** : un alias pendant une version, qui imprime le résultat et un avertissement nommant le remplaçant, retiré à la version suivante.
  - **B** : retrait immédiat, l'export s'arrêtant avec le nom du remplaçant.
  - **C** : une migration automatique des sections à l'ouverture du projet, comme pour la structure par dossiers.
- **Réponse** : **C** — migration des sections à l'ouverture du projet, chaque fichier sauvegardé dans les archives d'abord (l'ingénieur, 19.10.2026).

### Q-007 — « Des niveaux pour toutes les commandes » : lesquelles ?
- **Options** :
  - **A** : toutes les commandes qui **impriment** un calcul, un tableau ou une figure (`show-*`, `verify-*`, `distance`, `doc-*`, `sheet-*`). Les accesseurs (`get`, `ids`, `fmt-*`, `t`) n'impriment rien et n'en ont pas.
  - **B** : littéralement toutes, accesseurs compris (le niveau y serait ignoré).
- **Réponse** : **A** — les commandes qui impriment (`show-*`, `verify-*`, `distance`, `doc-*`, `sheet-*`) ; pas les accesseurs (l'ingénieur, 19.10.2026).

### Q-008 — N6, « retire ce chemin du poste »
- **Options** :
  - **A** : retirer `ExternalFiles/000-Normes/` des champs `_source` des 116 JSON, qui gardent la norme, l'édition, la clause et le nom du PDF. Les tests qui cherchent la bibliothèque la trouvent par une variable d'environnement.
  - **B** : remplacer ce chemin par celui où sont les PDF (`02_Normen und Bibliothek/`).
- **Réponse** : **A** — retirer le chemin des JSON ; la bibliothèque de normes trouvée par une variable d'environnement dans les tests (l'ingénieur, 19.10.2026).

### Q-009 — Le graphe de dépendances du projet
- **Pourquoi elle compte** : c'est une fonction nouvelle, avec une surface à concevoir (onglet, avertissements, commande).
- **Options** :
  - **A** : une spec dédiée après ce programme.
  - **B** : l'inclure ici.
- **Réponse** : **A** — spec dédiée après ce programme (l'ingénieur, 19.10.2026).

### Q-010 — Neige et vent : JSON seul ?
- **Pourquoi elle compte** : `decisions.md:364,366` dit « le classeur possède le calcul » ; lire les valeurs de norme en JSON lui retire ce rôle et change des valeurs (N37/N38, 5 cellules de vent, c_red).
- **Options** : A (recommandée) JSON seul, classeur = entrées ; B classeur moteur, JSON en contrôle.
- **Réponse** : **A** — JSON seul ; valeurs changées dites dans « Nouveautés », décision dans `decisions.md` (l'ingénieur, 19.10.2026).

### Q-011 — Que cite une valeur saisie ?
- **Options** : A (recommandée) la norme et la clause où elle sert ; B exemption explicite.
- **Réponse** : **A** — la norme où elle sert (N_Ed → SIA 263 5.1.2 ; ligne feu → sa norme d'exigence) (l'ingénieur, 19.10.2026).

### Q-012 — Que veut dire un niveau pour une figure, un tableau, un résumé ?
- **Options** : A (recommandée) 1 dessin seul, 2 + légende et titres, 3 + cotes, sources, citations ; B accepté sans effet.
- **Réponse** : **A** — `decisions.md:131` et `:479` sont renversées par une nouvelle décision (l'ingénieur, 19.10.2026).

### Q-013 — Espace avant « ° » ?
- **Réponse** : **A** — pas d'espace avant « ° » (ISO 80000) ; espace insécable avant toute autre unité (l'ingénieur, 19.10.2026).

### Q-014 — Forme du verdict ?
- **Réponse** : **A** — rapport η = 0.41 ⩽ 1 partout ; `unit: "%"` reste une option de commande (l'ingénieur, 19.10.2026).

### Q-015 — Palette des figures ?
- **Options** : A jetons aux valeurs actuelles (octets identiques) ; B fusion des couleurs.
- **Réponse** : **B** — fusionner maintenant ; les figures changent de teinte, dit dans « Nouveautés » et dans la carte de la garde d'octets (l'ingénieur, 19.10.2026).

### Q-016 — `migrate_to_schemas.py` et les formats d'avant v0.74 ?
- **Réponse** : **A** — supprimé ; un fichier d'avant v0.74 est refusé en disant de l'ouvrir d'abord dans une version 0.119 ou antérieure (l'ingénieur, 19.10.2026).

### Q-017 — La durée feu exigée par VKF 15-15, dans le rapport ? (ouverte, lot 7)
- **Contexte** : Q-011 veut qu'une ligne feu cite sa norme d'exigence. Le rapport cite la durée `t_fi` par SIA 265 4.5.2, même quand c'est VKF 15-15 qui l'exige : `#member(fire: (duration:, sides:, wood:))` ne connaît que la durée. Citer VKF 15-15 Tabelle 2 demande une clé de plus à `fire:`, ce qui change la surface d'une commande.
- **Options** : A ajouter une clé facultative `required: (norm:, norm-ref:)` à `fire:`, écrite par `#show-check-member` depuis l'export (la fenêtre et le rapport citent alors VKF 15-15) ; B garder SIA 265 4.5.2 pour la durée, VKF 15-15 restant dit dans la note de l'export.
- **État** : en attente de l'ingénieur ; la fenêtre et le rapport citent aujourd'hui tous deux SIA 265 4.5.2, et la parité le tient.

### Q-018 — Ce que cite un résultat de script ? (ouverte, lot 7)
- **Contexte** : ARCH-RISK-202 veut qu'un résultat de script cite « l'appel qui le produit ». Un résultat sans norme ne cite rien aujourd'hui (colonne de droite vide) ; sa provenance `python:scripts/<id>.py` est déjà exportée.
- **Options** : A citer le script et la ligne de `result(...)` dans la colonne de droite ; B laisser la colonne vide, la provenance restant dans l'export ; C exiger `norm=` dans `result(...)`.
- **État** : en attente de l'ingénieur ; rien n'est changé à l'impression.

## 11. Critères d'acceptation

- [ ] REQ-001 — les noms supprimés n'existent plus ; un appel restant fait échouer l'export en nommant le remplaçant
- [ ] REQ-002 — `ids`, `show-load-summary(unit:)`, `get` documentés, exemples, traductions ; helper commun `doc-*` et `sheet-*`
- [ ] REQ-003 — tableau de comparaison classeur/JSON/SIA 261 ; valeurs de norme lues en JSON ; test des deux chemins
- [ ] REQ-004 — chemin N6 retiré selon Q-008
- [x] REQ-005 — `--fast` en moins de 3 min, niveaux déclarés et testés
- [x] REQ-006 — job Windows dans la CI, testé
- [ ] UI-001 à UI-007 — formatage unifié, testé sur toutes les fonctions de formatage
- [ ] ARCH-001 — `TabSpec` et structure d'onglet selon Q-001, test de contrat
- [ ] ARCH-002 — citation juste et obligatoire ; forme unique selon Q-002
- [x] ARCH-003 — C3 à C7, un test chacun
- [ ] ARCH-004 — D1 à D8, test de doublons, figures identiques ou différences expliquées
- [ ] ARCH-005 — G1 à G9, un test chacun
- [ ] Documentation : sections de `docs/` mises à jour, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en, `///` + exemples + traductions pour toute commande Typst.
- [x] Tests : suite complète verte, niveau « Rapide » vert.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | ARCH-001 | ambigu → Q-001 |
| T2 | ARCH-002, ARCH-003, D-01 | capturé ; C1 → Q-002 |
| T3 | ARCH-004 | capturé |
| T4 | ARCH-005 | capturé |
| T5 | D-02, §8 | décision |
| T6 | REQ-003 | capturé |
| T7 | D-03, §8 | décision |
| T8 | REQ-004 | ambigu → Q-008 |
| T9 | UI-001 | capturé ; règle → Q-004 |
| T10 | UI-002, D-08 | capturé |
| T11 | UI-003, D-08 | capturé ; petites valeurs → Q-005 |
| T12 | UI-004 | capturé |
| T13 | UI-005, D-09 | capturé |
| T14 | UI-006 | capturé ; périmètre → Q-007 |
| T15 | UI-007 | capturé |
| T16 | REQ-005 | capturé |
| T17 | Q-003 | question |
| T18 | §9 | conséquence d'ARCH-001 |
| T19 | ARCH-005 (G1, G2), ARCH-001 | capturé |
| T20 | Q-002, D-01 | question + décision |
| T21 | REQ-006 | capturé |
| T22 | Q-009 | question |
| T23 | D-10 | décision |
| T24 | REQ-001, D-05 | capturé |
| T25 | REQ-002, D-06 | capturé ; anciens noms → Q-006 |
| T26 | CON-004, D-04 | décision |
| T27 | ARCH-001 | contradiction avec T1 → Q-001 |
| T28 | — | renvoi aux réponses ci-dessus |
| T29 | REQ-005, REQ-006, D-07 | capturé |

### Points de la source non résolus

- Aucun : les neuf questions ont reçu leur réponse le 19.10.2026.

## 13. Revue d'architecture

Quatre revues indépendantes en lecture seule (agent `architecture-reviewer`), le 19.10.2026 :

| Domaine | Verdict |
|---|---|
| A. Onglets (ARCH-001) | APPROUVER AVEC RÉSERVES |
| B. Calcul, neige et vent, normes (ARCH-002, ARCH-003, REQ-003, REQ-004) | APPROUVER AVEC RÉSERVES |
| C. Dessin et incohérences générales (ARCH-004, ARCH-005) | APPROUVER AVEC RÉSERVES |
| D. Commandes, formatage, tests (REQ-001, REQ-002, REQ-005, REQ-006, UI-001 à UI-007) | REVOIR |

Les points qui demandaient l'ingénieur ont reçu leur réponse (Q-010 à Q-016). Les autres sont réglés ci-dessous, et chaque correctif est repris dans le plan (§14).

### A. Onglets

- **ARCH-RISK-101 (bloquant) — la garde lecture seule et la synchronisation des domaines.**
  - Le problème : `WRITERS` et `DOMAIN_TABS` enveloppent les méthodes par nom, dans `vars()` de la classe et de ses mixins (`woodcore_gui.py:302-381`). Un `save` remonté dans la base n'est plus gardé, et `domain_file.sync` se tait.
  - Le correctif :
    - une feuille `calc/tools/tab_guard.py`, ré-exportée par `woodcore_gui`, appliquée dans `__init_subclass__` de la base sur chaque classe qui définit un writer ;
    - des attributs de classe `GUARDED` et `SYNC_DOMAIN` à la place de `GUARDED_TABS` et `DOMAIN_TABS` ;
    - pas de double enveloppe quand une sous-classe appelle `super().save()` ;
    - `replace_source` et les noms d'annulation restent hors de `WRITERS`.
- **ARCH-RISK-102 (bloquant) — `save` et `export` n'ont pas une forme unique.**
  - `save` devient une méthode-modèle, avec les hooks `check`, `write`, `after_write` et `id_field`.
  - `export` prend une seule signature : `export(done_text, quiet=False)`.
  - Positions, Python, Journal et Annexes surchargent `save` et ne reprennent que les parties communes.
  - La base appelle `self.fail` et `self.export` dynamiquement, car des tests les remplacent.
- **ARCH-RISK-103 — pas de classe abstraite sur un `QWidget`.** `abc.ABC` et `typing.Protocol` y entrent en conflit de métaclasse avec Shiboken. La base utilise des hooks qui lèvent `NotImplementedError`. Le `Protocol` ne sert qu'au test de contrat.
- **ARCH-RISK-104 — `set_view` et les vues.**
  - Une seule sémantique : `live`.
  - `VIEWS` reste optionnel : `test_views.py:98` exige son absence pour Structure, Annexes, Python et Commandes.
  - La vue initiale reste la clé des tailles déjà enregistrées.
- **ARCH-RISK-105 — Structure écrit des fichiers.** Elle reçoit une troisième sorte de base, `DocumentTab`, plutôt que `BrowserTab`. `FutureTab` et `SoonTab` fusionnent en `ReservedTab`.
- **ARCH-RISK-106 et ARCH-RISK-107 — le registre.**
  - `tab_registry.py` tient une liste ordonnée de `TabSpec`.
  - `TABS`, `NAV_GROUPS`, `NAV_SECTIONS`, `MODE_TABS` et `MODE_BOUND` en sont dérivés. Ils restent des globaux, que la fenêtre et une vingtaine de tests lisent.
  - La clé de l'onglet est `cls.KEY`, et la fabrique reste la classe.
  - Les icônes restent dans `chrome.ICONS`.
  - Les `STRINGS` restent des littéraux par module. Une clé définie dans deux modules lève une erreur.
- **ARCH-RISK-108 — l'annulation.** Elle revient à `CanvasEditorTab`, en une seule `UndoHistory`. D1 ne garde que les widgets de toile. `DrawingTab` dérive de `CanvasEditorTab`.
- **ARCH-RISK-109 — `save(quiet)`.** Un seul sens : ni export ni message de statut.
- **ARCH-RISK-110 — `restore`.** Il passe par une méthode-modèle, avec un hook `extra_state()`. Aucune clé de réglage enregistrée n'est renommée.
- **ARCH-RISK-111 — l'ordre.** G2 (`write_source`) et G8 (`polar_tab.py`) passent avant la base des onglets.
- **ARCH-RISK-113 — la taille.** Le registre vit hors de `woodcore_gui.py`, qui fait déjà 1254 lignes. La base reste sous 1000 lignes ; au-delà, elle est découpée en mixins par sujet (règle de l'issue #30).

### B. Calcul, neige et vent, normes

- **ARCH-RISK-201 (bloquant, tranché par Q-010) — la neige et le vent.**
  - Ce qui change : lire les valeurs de norme dans les JSON retire au classeur son rôle de moteur (`decisions.md:364,366`). Les `source` passent de `excel:…` à `python`/`entered`. L'écart N37/N38, les 5 cellules de vent fausses du classeur et `c_red`, désormais calculé, changent des résultats.
  - La comparaison : le projet exemple n'a pas de classeur de charges. Les tables du classeur (Dropdowns C_e, Δh, μ, c_h) sont donc extraites une fois, dans une fixture JSON comme `tests/fixtures/wind-tables-reference.json`, à partir du classeur de l'ingénieur.
  - `DOMAIN`, `LABEL`, `ACTION` et `NORM` passent dans les modules `*_source`, pour casser le cycle d'import.
  - La décision va dans `decisions.md`. Les valeurs qui changent sont dites dans « Nouveautés ».
- **ARCH-RISK-202 (bloquant, tranché par Q-011) — la citation des valeurs saisies.**
  - Une valeur saisie cite la norme et la clause où elle sert, sur le modèle de `snow_source.py:191`.
  - Une ligne feu cite la norme de son exigence (`member_check.py:446`).
  - Un résultat de script cite l'appel qui le produit ; `test_script.py:187` est adapté.
- **ARCH-RISK-203 — C1 côté bois.** `_row` reçoit un champ `norm`, par défaut `NORM = "SIA 265"`, et passe par `engine._check_citation`. Le contrat de `compute()` est gardé : environ 25 tests et `unfold` en dépendent.
- **ARCH-RISK-204 — les octets des fichiers dépliés.** `unfold.py:146` lit `row["norm"]`. Un test d'octets couvre les domaines `Timber-checks` du projet exemple.
- **ARCH-RISK-205 — les versions de schéma.** `steel.json` passe en 1.1, le schéma admettant `["1.0","1.1"]`. `checks.json` ne change pas de version tant que sa forme exportée ne change pas.
- **ARCH-RISK-206 — C4, les avertissements.**
  - Les avertissements des goujons et des connecteurs deviennent des `Note`, au texte allemand identique : le rapport les traduit par `tl-str`, avec ce texte pour clé.
  - Environ 25 phrases `warn_*` en fr, de et en.
  - Le test « aucun print » couvre aussi `calc/registry.py`.
  - Le `print` de `wind.py` attend REQ-003.
- **ARCH-RISK-207 — C3, un validateur partiel.** `validate_structure` ignore `$ref`, `pattern` et `minItems`. Il est appelé en tête de `check_source`, et les contrôles écrits à la main restent. Le validateur n'est pas étendu dans ce programme.
- **ARCH-RISK-208 — C7.** Les exceptions deviennent `class X(ValidationError, ValueError)`, pour que les `except ValueError` existants continuent de les attraper. Un test prouve d'abord qu'elles échappent à l'export aujourd'hui.
- **ARCH-RISK-209 — C5.** Deux Protocol, « source » et « export », vérifiés par un test-contrat en table. Seul `script.SCHEMA_VERSION` est renommé, en `EXPORT_SCHEMA_VERSION`.
- **ARCH-RISK-210 — C6.**
  - Le docstring de `member_check.py:1-16` est corrigé.
  - `_held_equal` compare aussi `clause` et `norm_ref`, et vérifie que chaque genre de `IMPLEMENTED` est couvert.
  - La parité reste hors du niveau « Rapide ».
- **ARCH-RISK-211 — REQ-004.**
  - Le chemin sert aussi de marqueur : `test_bibliography.py:598` et `norms.py:83` cherchent « Not in ExternalFiles/000-Normes/ ». Il est remplacé par « Not in the reference library », dans le même commit.
  - Les tests trouvent la bibliothèque par la variable `WOODCORE_NORMS_LIBRARY`.
  - `principles.md:65` est reformulé.

### C. Dessin et incohérences générales

- **ARCH-RISK-301 (bloquant) — aucune garde d'octets sur les figures.**
  - Les SHA-256 de toutes les figures du projet exemple sont figés avant tout changement (`tests/test_figure_golden.py`).
  - Des fixtures couvrent les genres absents de l'exemple : plan feu, connecteur, poids propre, neige.
  - Toute différence est expliquée dans une carte, à commencer par la fusion des couleurs (Q-015).
  - Un seul `svg_draw.number(value, digits)`. Chaque module en tire son `_f` par `number_at(DIGITS)`, avec sa précision actuelle : une coordonnée n'est pas un nombre affiché.
- **ARCH-RISK-302 (bloquant) — le découpage de `calc-engine.typ`.**
  - Des fichiers à plat, `lib/calc-engine-<sujet>.typ`, parce que les `json("../data/…")` sont relatifs au fichier qui les appelle.
  - La découpe suit les frontières de section, dans l'ordre actuel. `calc-engine.typ` devient une façade qui ré-exporte tout.
  - Une seule liste des fichiers du moteur, dérivée de `lib/*.typ`, sert à `project.ENGINE_FILES` et à `build_reference_lib.LIB_FILES`. Un test vérifie leur égalité.
  - `conftest.engine_source()` sert aux tests qui lisent le texte du moteur.
  - `test_module_size` s'étend à `lib/`. `formula.typ` et `timber.typ` y sont des exceptions nommées dans `layout.md`.
  - Le découpage passe avant UI-001 à UI-007.
- **ARCH-RISK-303 — les délais de la toile.** La base de toile reçoit en paramètre les délais de v0.116 : 350 ms pour les plans, 220 ms pour la statique.
- **ARCH-RISK-304 — D2.** Le `SvgLayer` du schéma, avec son cache par vue, est retenu, puis mesuré sur un plan A3. `plan_canvas.SvgLayer` reste ré-exporté.
- **ARCH-RISK-305 — D4, prémisse corrigée.** Seules 7 fonctions sont identiques entre `schema_geometry` et `statics_geometry`. Le reste diffère : unités (mm ou m), noms d'aimantation, cache. D4 étend `dimension.py` et `plan_tracking.py`, avec l'unité et les noms en paramètres. Il n'y a pas de troisième module de géométrie.
- **ARCH-RISK-306 — D5, tranché par Q-015 : les couleurs sont fusionnées.**
  - La palette vit dans `lib/figure-palette.json`, sur le modèle de `lib/units.json`. Python et Typst la lisent, et elle entre dans la liste des fichiers du moteur.
  - Elle couvre aussi `font-family`.
  - Le changement de teinte est dit dans « Nouveautés » et figure dans la carte de la garde d'octets.
- **ARCH-RISK-307 — D6 et D7.**
  - `svg_draw.py` porte le nombre, les points, l'échappement et les primitives ; `svg_text.py` reste le module du texte.
  - D7 : l'export des schémas gagne `size`, en version 1.2, avec son schéma.
  - Les 4 fonctions de nombre SVG de Typst deviennent `svg-number(x, digits:)`.
- **ARCH-RISK-308 — G1, trois modes d'écriture.**
  - Créer un fichier : en LF, par l'écrivain atomique unique d'`engine.py`.
  - Garder les fins de ligne d'un fichier : `typst_paths.write_text`.
  - Le test AST n'accepte que `newline="\n"` ou `newline=""`.
  - `plan_tab.py:328`, qui écrit avec `os.linesep`, est corrigé.
- **ARCH-RISK-309 — G2.**
  - Une seule signature : `write_source(here, source) -> path`, sur `sharing._commit`.
  - `source_bytes(source)` sert à l'écriture transactionnelle du plan et du magasin des positions.
  - G2 passe avant les onglets.
- **ARCH-RISK-310 — G3 et G4.**
  - Le test « une seule définition » vise les `_fail(where, message)` des domaines.
  - G4 compte trois fonctions : `is_number`, `check_number`, `fmt_number`.
  - Le chargeur de normes garde les noms `_cache`, `_read` et `_load` par module, que les tests manipulent.
- **ARCH-RISK-311 — G6.** `build_reference` et `usersettings`, qui n'importent pas Qt, passent dans `calc/`. La scission de `variable_sources` est retirée : rien dans le code ne la justifie.
- **ARCH-RISK-312 — G8.** `LABEL` devient `LABEL_COLOUR` seulement dans `schema_svg` et `statics_svg`. `woodcore_gui_polar.py` devient `polar_tab.py` en même temps que la migration de `PolarTab`.
- **ARCH-RISK-313 — G5 et G7.**
  - G5 : un `except Exception` porte son commentaire `# broad:` sur la même ligne, et le `pass` de `connector_svg.py:362` est remplacé.
  - G7 : la frontière est documentée, et un test vérifie que chaque `*_words.py` est fusionné.

### D. Commandes, formatage, tests

- **ARCH-RISK-401 (bloquant) — transport et affichage.**
  - Les 6 décimales de `timber.typ:433, 525, 905, 1487` et les `_fmt` Python à 6 décimales transportent des valeurs : Typst les évalue, et `unfold` garantit une tolérance de 1e-6. Les arrondir changerait le calcul.
  - Un seul `calc/numbers.py`, avec `fmt_exact` (transport, pleine précision) et `fmt_display` (règle de Q-005), et une feuille Typst `lib/number.typ` pour l'affichage.
  - Les constantes du bois sont transportées en pleine précision et affichées par la règle commune.
  - Un test de parité couvre Python et Typst.
  - Le critère d'UI-003 est reformulé en conséquence.
- **ARCH-RISK-402 — l'arrondi et l'affichage.**
  - `fmt-decimals` reste un arrondi pur : il sert aussi aux sources math, aux coordonnées et aux messages. La règle d'affichage vit dans `lib/number.typ`.
  - Le test de `fmt-decimals(157000,3) = "157000"` reste vrai, et un nouveau test couvre l'affichage.
  - Le réglage `number-digits` est retiré de l'affichage, qui suit une seule règle (D-08).
  - Les figures sont exclues de la règle.
- **ARCH-RISK-403 (bloquant, tranché par Q-012) — les niveaux des figures, tableaux et résumés.**
  - Niveau 1 : la figure ou le tableau seul. Niveau 2 : avec la légende et les titres. Niveau 3 : avec les cotes, les sources et les citations.
  - Cela renverse `decisions.md:131` et `:479` par une nouvelle décision.
  - Chaque `level:` ajouté est reporté dans `typst_objects_parse.SIGNATURES` et dans les options de `display_options` (`test_display_view`).
  - Les accesseurs (`get`, `ids`, `fmt-*`, `t`) vont dans un registre `NO_LEVEL`, testé dans les deux sens.
- **ARCH-RISK-404 (bloquant) — un contrat de données.**
  - `level` est exigé par `calculations.schema.json:185/250/303`.
  - Une table JSON `domaine → clé → niveau`, sur le modèle de `lib/shown-variables.json`, est lue par Typst et par Python.
  - `level` devient optionnel dans l'export : nouvelle `schema_version`, l'ancienne toujours lue, règle de priorité écrite.
  - Ce lot passe après ARCH-002.
- **ARCH-RISK-405 — contradictions entre REQ-001 et REQ-002.**
  - `schema-ids` n'est pas supprimé : il devient `ids("schema")`.
  - La table ancien → nouveau est un JSON (`calc/i18n/` ou `lib/`). C'est la seule exception au critère « le nom n'existe plus ».
  - `instance-ids(domain)` devient `ids("instance", domain)`.
  - `show-plan-legend` et `moisture-class-of` n'ont pas d'équivalent exact. Une section qui les appelle fait échouer l'export, en proposant `show-plan(legend: true)` ou la lecture de la position.
  - `sia260.py` est gardé, puisque l'onglet « Combinaisons » l'est (CON-004).
  - `migrate_to_schemas.py` est supprimé, et les formats d'avant v0.74 ne sont plus lus (Q-016).
  - La perte de `catalog_gui.py`, utilisé par les lanceurs 0.83 à 0.90, est dite dans « Nouveautés ».
- **ARCH-RISK-406 — la migration des sections.**
  - `unfold_migrate.py` est généralisé en `commands_migrate` : lexeur de `typst_paths` (raw et commentaires sautés), archives d'abord, idempotent.
  - Elle tourne aussi dans `woodcore-cli export`, où `plan()` arrête l'export en nommant le remplaçant.
  - La règle 11 est mise à jour dans `principles.md`, `README.md`, `layout.md` et `api-conventions.md`.
- **ARCH-RISK-407 — une règle exécutable pour les indices.** Une table de classification JSON (descriptif ou variable), un constructeur de symboles Python unique, un normaliseur Typst unique et le jumeau `typst_math.py`, tenus par un test de parité du balisage.
- **ARCH-RISK-408 — tranché par Q-013 et Q-014.**
  - Pas d'espace avant « ° », une espace insécable avant toute autre unité, y compris dans `value-text`.
  - Le verdict prend la forme de rapport η = 0.41 ⩽ 1.
  - La virgule de `dowel._de` disparaît, ce qui est dit dans « Nouveautés ».
- **ARCH-RISK-409 — UI-004 après REQ-003.** Le test AST garde une liste blanche : `/ 2`, `^2`, `10^3`.
- **ARCH-RISK-410 — REQ-006 existe déjà.**
  - `tests.yml:58` a un job `windows-2025`, épinglé, sur les pushs de `master`.
  - REQ-006 est reformulé : Windows lance `--fast` sur chaque push et chaque PR, et la suite complète reste sur `master`. Pas de `windows-latest`.
- **ARCH-RISK-411 — REQ-005.**
  - Le niveau se déclare `TIER = "fast"` dans le texte du fichier, comme `PERF`. Sans déclaration, le fichier est dans la suite complète, ce qui évite un diff dans 177 fichiers.
  - `test_commands` est scindé.
  - La durée de `--fast` est écrite avec sa date et sa machine.
- **ARCH-RISK-412 — un seul gel, à la fin** : `build_examples --freeze`, les pages -L1/-L3, le site.

### Approche retenue

1. Les filets : le niveau de tests rapide, la garde d'octets des figures, le test de doublons, la taille de `lib/`.
2. Les fondations : l'écriture, les sources, les suppressions, le découpage du moteur Typst.
3. Les onglets, puis le dessin, puis le calcul, puis l'affichage.

Chaque lot est un commit, avec ses tests verts. Le gel des exemples et du site se fait une seule fois, au dernier lot.

## 14. Plan d'implémentation

Chaque lot se termine dans le même état :
- ses tests ciblés sont verts, ainsi que `--fast` (dès le lot 0) ;
- un commit le livre, et une ligne du §16 le consigne ;
- la suite complète est lancée en arrière-plan à la fin du lot.

Un lot interrompu reprend à sa première case non cochée.

**Lot 0 — Les filets** (REQ-005, REQ-006, ARCH-RISK-301, ARCH-RISK-302, ARCH-RISK-411)
1. `tests/run_tests.py` lit `TIER = "fast"` dans le texte d'un fichier, comme `PERF`, et prend l'option `--fast`. Les fichiers moteur, normes, contrats et export sont marqués, et `test_commands` est scindé en catalogue et compilation. La durée mesurée va dans `docs/conventions/testing.md`. Tests : `test_harness`, `test_runner`.
2. `.github/workflows/tests.yml` : le job `windows-2025` lance `--fast` sur chaque push et chaque PR, et la suite complète sur `master`. Test : `test_ci_workflow`.
3. `tests/test_figure_golden.py` fige les SHA-256 de chaque figure exportée du projet exemple, plus des fixtures pour le plan feu, le connecteur, le poids propre et la neige.
4. `tests/test_no_duplicates.py` : un test de doublons AST, avec une liste de référence qui ne peut que diminuer.
5. `test_module_size` s'étend à `lib/*.typ`. Les exceptions sont nommées dans `layout.md`.

**Lot 1 — Écriture et sources** (G1, G2, REQ-004)
1. `engine.write_text_lf` et `engine.write_json` deviennent un seul écrivain atomique en LF. Les 61 `write_text` nus de `calc/` passent par lui, ou par `typst_paths.write_text` pour un fichier dont on garde les fins de ligne. `plan_tab.py:328` est corrigé. Test : `tests/test_text_writes.py`.
2. Chaque domaine à source reçoit `write_source(here, source) -> path` et `source_bytes(source)`. L'environ 30 `json.dumps` des onglets passent par eux. Test : `tests/test_write_source.py`.
3. REQ-004 : le chemin `ExternalFiles/000-Normes/` est retiré des 116 JSON. Le marqueur devient « Not in the reference library ». La variable `WOODCORE_NORMS_LIBRARY` est lue par `conftest`. `principles.md` et `reference-library.md` sont mis à jour. Tests : `test_norms`, `test_bibliography`, `test_sia260`.

**Lot 2 — Suppressions, fusions, migration des sections** (REQ-001, REQ-002, ARCH-RISK-405, ARCH-RISK-406)
1. La table `lib/renamed-commands.json` donne l'ancien nom, le nouveau nom et la transformation.
2. `calc/domains/commands_migrate.py`, généralisé à partir de `unfold_migrate.py`, migre les sections à l'ouverture de la fenêtre et dans `woodcore-cli export` (`plan()`). Le lexeur de `typst_paths` saute raw et commentaires, les fichiers sont archivés d'abord, et le passage est idempotent. Test : `tests/test_commands_migrate.py`.
3. Les nouvelles commandes `ids(kind, …)` (dans `lib/formula.typ`, le hub), `get(v, field)` et `show-load-summary(unit:)`, avec un helper interne pour `doc-*` et `sheet-*`. Chacune a son bloc `///`, deux exemples et ses traductions dans `commands.json`. Les gabarits et le projet exemple appellent les nouveaux noms. `display_options`, `variables_tab` et `build_reference_calls` écrivent les nouveaux noms.
4. Les suppressions :
   - les modules `migrate_to_schemas.py`, `catalog_gui.py` et `build_document_templates.py`, avec la lecture des formats d'avant v0.74 (Q-016) ;
   - les commandes `distance-scopes`, `show-plan-legend` et `moisture-class-of` ;
   - les environ 45 définitions sans appelant ;
   - `sia260.py` est gardé.
5. La règle 11 est mise à jour dans la doc. Tests : `test_commands`, `test_call_command`, `test_summary`, `test_display_view`, `test_packaging`.

**Lot 3 — Fondations Python et Typst** (G3, G4, G5, G7, G8, G9)
1. G9 : `lib/calc-engine.typ` est découpé en `lib/calc-engine-<sujet>.typ`, à plat, et devient une façade. Une seule liste des fichiers du moteur alimente `ENGINE_FILES` et `LIB_FILES`. `conftest.engine_source()` sert aux tests. Tests : `tests/test_lib_files.py`, `test_project`, et les tests qui lisent le moteur.
2. G3 : `calc/norms/_loader.py` partagé. Les noms `_cache`, `_read` et `_load` restent par module. Test : `tests/test_norm_loader.py`.
3. G4 : `calc/domains/_common.py` porte `fail`, `is_number`, `check_number` et `fmt_number`. Les conversions locales sont remplacées par `units.py`.
4. G5 : chaque `except Exception` porte `# broad:` sur sa ligne, et les `pass` silencieux sont remplacés.
5. G7 : la frontière entre mots de la fenêtre et mots du rapport est écrite dans CLAUDE.md et `docs/`.
6. G8 : `LABEL` devient `LABEL_COLOUR` dans `schema_svg` et `statics_svg`, et un glossaire des noms va dans `docs/conventions/`.

**Lot 4 — Onglets, solution B** (ARCH-001, ARCH-RISK-101 à 113, G8 `polar_tab.py`)
1. `tests/test_tab_contract.py` est écrit d'abord, vert sur le code actuel.
2. `tab_guard.py` et `tab_registry.py` dérivent les globaux. Test : `tests/test_tab_registry.py`, qui vérifie l'égalité avec les anciens tuples.
3. `SourceEditorTab`, extraite de `ConnectorsTab`, migre ensuite `LoadTab` (3 onglets), `MemberCheckTab` (9 onglets, avec Acier, Résistance au feu et Profilés), puis `PolarTab` (renommé `polar_tab.py`).
4. Le `set_view` unique remplace le montage manuel de l'Affichage.
5. `CanvasEditorTab` porte l'annulation unique et migre `StaticsTab`, `SchemaTab`, puis `DrawingTab` (plan et plan feu).
6. `Journal`, `Annex`, `Profile`, `Formula`, `Python` et `Positions` passent sur les parties communes.
7. `DocumentTab` (Structure), `BrowserTab` (Variables, Commandes) et `ReservedTab` sont en place ; les copies sont supprimées. Tests : ceux de la revue A §5, plus `test_editor_buttons` étendu à tous les éditeurs.

**Lot 5 — Dessin** (ARCH-004, D1 à D8, Q-015)
1. D6 : `svg_draw.py` porte `number_at`, les points, l'échappement et les primitives.
2. D4 : `dimension.py` et `plan_tracking.py` sont étendus et paramétrés.
3. D8 : l'azimut passe dans `statics_geometry.py`.
4. D5 : `lib/figure-palette.json`, avec les couleurs fusionnées et la carte des différences.
5. D7 : l'export des schémas porte `size` (version 1.2), et Typst a un seul `svg-number`.
6. D3 : un seul `icon_from_svg`, bâti sur `chrome._pixmap`.
7. D2 : un seul `SvgLayer`, mesuré sur un plan A3.
8. D1 : la base de toile commune.

Après chaque étape, la garde d'octets (lot 0) est verte, ou sa différence expliquée.

**Lot 6 — Domaines** (ARCH-003 : C3, C5, C6, C7)
1. C7 : les exceptions passent sous `ValidationError`.
2. C3 : `validate_structure` en tête de `check_source`.
3. C6 : le docstring de `member_check` et `_held_equal` étendu.
4. C5 : les Protocol « source » et « export », avec un test-contrat.

**Lot 7 — Une forme de résultat et sa citation** (ARCH-002, C1, C2, Q-011)
1. L'acier passe sur `engine.Calculation` : `steel.json` en version 1.1, `Calc` supprimé.
2. Une valeur saisie cite la norme et la clause où elle sert.
3. Les lignes du bois portent leur norme, la norme réelle pour une ligne feu ou VKF.
4. `published_vars` et `unfold` lisent cette norme. Test d'octets sur les domaines `Timber-checks` du projet exemple.

**Lot 8 — Neige et vent, une seule source** (REQ-003, Q-010, C4, UI-004)
1. Les tables du classeur sont extraites une seule fois dans une fixture, à partir du classeur de l'ingénieur.
2. Un tableau de comparaison classeur / JSON / SIA 261 est écrit dans `docs/domain/loads.md`, et chaque différence est corrigée dans le JSON d'après la norme.
3. `snow.py` et `wind.py` ne lisent plus que les entrées du classeur, et les valeurs de norme viennent des JSON.
4. C4 : les avertissements deviennent des `engine.Note` (environ 25 phrases fr, de, en).
5. UI-004 : les constantes des formules sont composées à partir des valeurs.
6. La décision va dans `decisions.md`, et la liste des valeurs qui changent dans « Nouveautés ».

**Lot 9 — Affichage** (UI-001 à UI-003, UI-005 à UI-007, ARCH-RISK-401 à 404, ARCH-RISK-407, ARCH-RISK-408)
1. `calc/numbers.py` (`fmt_exact`, `fmt_display`) et `lib/number.typ` : les 4 `_fmt` Python deviennent un seul module. Test de parité.
2. UI-002, UI-003, UI-007 : une seule règle d'affichage pour toutes les fonctions de formatage de `lib/`. Pas d'espace avant « ° », verdict sous forme de rapport.
3. UI-001 : la table des indices, le constructeur de symboles Python, le normaliseur Typst et `typst_math.py`.
4. UI-005 : la table `domaine → clé → niveau`. `level` devient optionnel à l'export (nouvelle `schema_version`).
5. UI-006 : `level:` est ajouté à chaque commande qui imprime, avec le sens niveau 1 / 2 / 3 de Q-012, et `NO_LEVEL` pour les accesseurs. `decisions.md:131` et `:479` sont renversées.
6. Gel unique des exemples (`build_examples --freeze`), pages -L1 et -L3, site.

**Lot 10 — Clôture** (G6, documentation)
1. G6 : `build_reference` et `usersettings` passent dans `calc/`.
2. Documentation :
   - `docs/` à jour : architecture, interface, Typst, conventions ;
   - `decisions.md` et son index ;
   - `CHANGELOG.md` ;
   - la page « Nouveautés » fr/de/en de la version suivante ;
   - le catalogue des tests.
3. Vérification indépendante (`verify-requirements`), puis `finish`.

### Ce qui n'est pas fait

- N1 (coefficients de l'acier) et N5.
- La construction des onglets à la demande.
- Le moteur hors des projets et le graphe de dépendances : specs dédiées.

### Dépendance externe

Le lot 8 a besoin du classeur de charges de l'ingénieur (Belastungsannahmen, avec Dropdowns et vent). Il n'est pas dans le dépôt. Il sera demandé au début du lot, et seules ses tables sont extraites dans une fixture.

## 15. Vérification

Vérification indépendante du 20.10.2026 (agent `requirements-verifier`, base e10eb91, commits 6b207a6..5728de6 et la documentation du lot 10), puis un premier tour de corrections. Suite complète après les lots 8 à 10 : 3049 passés, 11 ignorés, 0 échec ; niveau « Rapide » : 1139 passés.

| Exigence | Verdict | Ce qui reste |
|---|---|---|
| REQ-001 suppressions | ⚠️ | `distance-scopes` reste (gardé par `test_distance` au lot 2, le journal le disait à tort retiré) ; le commentaire doublé et les mentions de `catalog_gui` corrigés au 1er tour. |
| REQ-002 fusions | ⚠️ | `ids`, `get`, `show-load-summary(unit:)` faits et migrés ; le helper commun `doc-*`/`sheet-*` n'apporte rien de neuf (helpers déjà partagés). |
| REQ-003 neige/vent | ⚠️ | Valeurs de choix (C_e, Δh, z_g, α_r) lues en JSON et croisées ; les c_pe/c_pi de `wind._read_coefficients` et les μ, s_k, q_k calculés par le classeur restent lus dans ses cellules (le classeur calcule encore) : « classeur = entrées seulement » non atteint. |
| REQ-004 chemin N6 | ⚠️ | 0 occurrence dans `calc/`, `lib/`, `tests/` ; le chemin reste cité dans `docs/architecture/reference-library.md` et des specs terminées (historique). |
| REQ-005 niveau Rapide | ✅ | Selon ARCH-RISK-411 (déclaration dans le texte, défaut = suite complète) ; `test_commands` non scindé. |
| REQ-006 CI Windows | ✅ | |
| UI-001 indices | ❌ | Reporté à une spec dédiée. |
| UI-002, UI-003 nombres | ⚠️ | Règle unique `display-number`/`number_text.display`, parité testée sur 20 cas ; pas de test qui passe une même valeur par `show-calc`, `eq`, `value-text` ; d'autres rognages Python restent hors `calc/domains/` (`profile_tab`, `szs_c5`, `section.py`, …). |
| UI-004 constantes | ✅ | Test AST ajouté au 1er tour (`test_a_formula_composes_its_constants_from_the_values_it_computes_with`). |
| UI-005 niveau par Typst | ❌ | Reporté à une spec dédiée. |
| UI-006 `level:` partout | ❌ | Reporté à une spec dédiée ; `decisions.md:131,479` non renversées (D-18 pas encore appliquée). |
| UI-007 mise en forme | ⚠️ | Signe moins, espace insécable, « ° » sans espace, point décimal faits ; la forme unique du verdict n'est pas testée. |
| ARCH-001 onglets | ⚠️ | `TabSpec`, garde, bases `SourceEditorTab`/`CanvasEditorTab` faits ; `confirm_leave`, `update_list_marker`, `reload_list`, `on_list_change`, `on_moved` encore redéfinis dans plusieurs onglets ; pas de `BrowserTab`/`DocumentTab` (écart du lot 4). |
| ARCH-002 C1/C2 | ⚠️ | Acier sur `engine.Calculation`, citations faites ; `member_check._row` rend encore un dict (citation vérifiée, pas l'objet) ; Q-017, Q-018 ouvertes. |
| ARCH-003 C3–C7 | ✅ | Écarts documentés : C4 (connecteurs et goujons restent au glossaire), C7 (les deux `Refused`). |
| ARCH-004 D1–D8 | ⚠️ | `normalize_angle` réduit à une copie au 1er tour ; restent en double `schema_geometry`/`statics_geometry` (`fmt_number`, `typed_point`, `dimension_*`, `nearest_ray`, `label_corners`) et les `_text`/`_unit` minces des modules `*_svg`. |
| ARCH-005 G1–G9 | ⚠️ | G2 sans `write_source` par domaine (écart du lot 1) ; G4 sans `fmt_number` commun. |
| Documentation | ✅ | `docs/`, `decisions.md` et index, `CHANGELOG.md`, « Nouveautés » 0.120.0 fr/de/en (complétées au 1er tour : commandes fusionnées, formats d'avant v0.74, point décimal des goujons). |
| Tests | ✅ | Suite complète et niveau « Rapide » verts. |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-19 | draft | spécification extraite des réponses de l'ingénieur au rapport d'audit ; 9 questions ouvertes |
| 2026-10-19 | specified | les 9 questions répondues (D-11 à D-15) ; prochaine étape : revue d'architecture |
| 2026-10-19 | reviewed | quatre revues (§13) ; Q-010 à Q-016 répondues (D-16 à D-22) ; plan en 11 lots (§14) ; attend l'approbation |
| 2026-10-19 | approved | approuvée par l'ingénieur, «Approuver et implémenter» ; début du lot 0 |
| 2026-10-19 | implementation | **Lot 0 fait** : `--fast` (TIER, 86 fichiers, 1106 tests en 73 s) ; CI Windows `--fast` à chaque push/PR, suite complète sur master (REQ-005, REQ-006) ; `test_figure_golden.py` (33 figures) ; `test_no_duplicates.py` (86 groupes, 198 copies, liste qui ne fait que baisser) ; `test_module_size` sur `lib/*.typ` (3 exceptions nommées). Prochain : lot 1. |
| 2026-10-19 | implementation | **Lot 1 fait** : G1 — 43 `write_text` et 3 `open` de `calc/` disent `newline="
"`, `plan_tab` n'écrit plus en `os.linesep` (`test_text_writes.py`). G2 — `engine.source_bytes` (la seule sérialisation) et `engine.write_json` atomique (fichier `.part` puis `os.replace`) ; les 22 `json.dumps` écrits à la main des onglets, et ceux de `member_check`, `script`, `plan_pages`, `plan_documents`, `positions_store`, `renumbering`, passent par eux. *Écart à la spec* : pas de `write_source` par domaine en plus — chaque onglet appelle déjà `check_source` de son domaine juste avant d'écrire ; un writer par domaine aurait été onze enveloppes identiques ; `member_check`, `annex`, `journal` gardent le leur. REQ-004 — le chemin `ExternalFiles/000-Normes/` est retiré de 78 fichiers (JSON, code, tests) et de la doc courante ; le marqueur est «Not in the reference library» ; `WOODCORE_NORMS_LIBRARY` (`conftest.norms_library`) ; copies d'exemple de `calc/norms/` et `strings.json` resynchronisées. Catalogue des tests scindé (`testing-catalogue-guards.md`) : 100 Ko atteints. Prochain : lot 2. |
| 2026-10-20 | implementation | **Lot 2 fait (suite complète en cours)** : `ids(kind)` (13 `*-ids`) et `get(v, field)` (8 `get-*`) dans `lib/calc-engine.typ`, les chargeurs regroupés avant eux ; `show-load-summary(unit:)` (fusion de `show-line-load-summary`) ; retirés : `show-plan-legend`, `moisture-class-of`, `distance-scopes`, `check-member-ids`, `check-steel-ids`. Table `calc/renamed-commands.json` (*écart* : dans `calc/`, pas `lib/` — seul Python la lit). `calc/domains/commands_migrate.py` : réécriture (arguments gardés, imports, chaînes échappées, moins unaire), migration à l'ouverture de la fenêtre, refus de l'export (`refusal`), `commit` partagé avec `unfold_migrate`. Pas de commande `woodcore-cli` nouvelle (surface à décider par l'ingénieur). Supprimés : `migrate_to_schemas.py` (formats < v0.74 refusés, D-21), `catalog_gui.py`, `build_document_templates.py`, 48 définitions sans appelant ; gardés car cités comme notions : `TRACK_KINDS`, `SELECTION_LEVEL`, `REPLACE`, `CLOSE`, `Sizes.on_text`. `commands.json`, gabarits, projet exemple, tests, docs courantes (pas les notes des versions passées), exemples régénérés (100 anciens retirés, `ids-1/2`, `get-1/2`). `test_commands_migrate.py`. |
| 2026-10-20 | implementation | Lot 2 commité (19a1fe2), suite complète 3024/0. **Lot 3 fait** : G9 — `lib/calc-engine.typ` découpé en `calc-engine-core/drawings/display/records/connections.typ` (texte déplacé, chaîne d'imports), façade de 4 lignes ; `ENGINE_FILES` et `LIB_FILES` les nomment ; `conftest.engine_source()` ; exemples identiques à l'octet. G3 — `calc/norms/_loader.py` (`load`, `fail`, `edition`), 11 blocs de lecture et 7 contrôles d'édition remplacés, `test_norm_loader.py`. G4 — `calc/domains/_common.py` (`fail`, `is_number`, `check_number`) : 16 `_fail` et 10 `_number` retirés, importés sous leurs noms ; *reste* : tables d'unités locales (`member_check`, `section`) → lot 9, celle de l'acier part au lot 7. G5 — raison écrite sur les 5 retours arrière ; les 3 `pass` sur un dessin raté écrivent la trace. G7 — frontière des deux glossaires dans CLAUDE.md et `docs/typst/language.md`. G8 — `LABEL_COLOUR` ; `docs/conventions/naming.md` ; `polar_tab.py` au lot 4. |
| 2026-10-20 | implementation | Lot 3 commité (e51896b). **Lot 4 fait** (b6f1ade puis le commit suivant) : `tab_registry.py` (SPECS, globaux dérivés), `tab_guard.py` (garde structurelle, `SYNC_DOMAIN`), `reserved_tab.py` (fusion FutureTab/SoonTab), `source_editor.py` (`SourceEditorTab` : liste, actions du brouillon, Ctrl+S `save_shortcut`, `confirm_leave`, `export`, `next_free_id` unique, `NEW_ROW` unique), `canvas_editor.py` (`CanvasEditorTab` : annulation unique, `HISTORY`), `DisplayTab.set_view` unique (`live`, `prepare_display`). Tous les onglets d'édition dérivent de `SourceEditorTab` (Connecteurs, Charges ×3, Vérifications ×9 avec acier et feu, Polaires, Positions, Profilés, Annexes, Journal, Python, Formule), les toiles de `CanvasEditorTab` (Plan, Feu, Statique, Schémas). `woodcore_gui_polar.py` → `polar_tab.py` (G8). `test_tab_registry.py` (6 tests, contrat de structure). Doublons : 86/198 → 78/174. *Écarts* : pas de `BrowserTab`/`DocumentTab` — Structure, Variables et Commandes n'ont rien de commun à porter, une base vide serait une abstraction inutile ; les `reload_list`/`on_moved`/`load` propres aux toiles, aux Polaires, aux Positions, aux Profilés, aux Annexes et au Journal restent des redéfinitions explicites (listes à libellés, brouillon refilé, `QListWidget`), à resserrer avec D1 au lot 5. |
| 2026-10-20 | implementation | Lot 4 commité (4dfa405). **Lot 5 fait** (ARCH-004, Q-015) : D6 — `calc/domains/svg_draw.py` (`number`, `number_at`, `escape`) ; les 9 `_f` en tirent leur précision, figures identiques à l'octet. D4 — huit fonctions de géométrie plane identiques déplacées dans `dimension.py` (`_cross`, `_inside`, `_local`, `_point_segment`, `constrain`, `grid_snap`, `index_of`, `normalize_angle`), `_common.source_paths` pour les cinq domaines. D8 — `statics_geometry.angle_reach`. D3 — `calc/tools/svg_icons.py` (`pixel_ratio`, `svg_pixmap`, `svg_icon`, `recolour`) : les sept aides d'icônes (chrome, flowbar, connecteurs, statique, schémas, plans, cotes, dossiers) en font un appel ; les sentinelles de recoloriage en un seul endroit. D5 — `lib/figure-palette.json` (22 couleurs, 2 rotations, la police) lu par `svg_draw.colour` et par `lib/calc-engine-core.typ` (`figure-colour`) ; plus aucune couleur ni police écrite dans un moteur de dessin (`tests/test_figure_palette.py`) ; la copie Typst des couleurs (flèches d'une connexion, lettres STE de `positions.typ`, halos, échelle) lit la même palette. Couleurs fusionnées : cinq noirs en un, bleus, verts, rouges, orangés, gris chacun en un ; le gris discret reste neutre (#8a8a8a), le gris de superposition devant rester gris. Vérifié figure par figure contre le commit 4dfa405 : avec les anciennes couleurs remplacées par les nouvelles, les 33 figures de la garde et les 11 empreintes figées des tests sont le même texte à l'octet ; empreintes reprises avec leur raison (`CHANGES`). L'export du projet exemple refait pour ses figures, `fire.json`, `plans.json` et `schemas.json` (le reste remis tel quel). D7 — un seul `svg-number(x, digits: 2)` dans `calc-engine-core.typ` (fin de `plan-number`, `static-number`, `schema-number` et de l'`svg-number` des connexions) ; `data/schemas.json` porte `size` et Typst ne recalcule plus l'étendue (`schema-extent` supprimée, un export antérieur arrête le rapport en le disant). D2 — `calc/tools/canvas_items.py` : un seul `SvgLayer`, un seul `cosmetic`, un seul arrondi (`saved_at`). D1 — `calc/tools/canvas_base.py` : `CanvasBase`, base des quatre toiles (zoom, grille, curseur, marque d'aimantation, poignées, poursuite, cote en cours) ; chaque toile dit ses valeurs par attributs de classe (`MODEL`, `TOOLS`, `ROUND`, `MIN_ZOOM`, `MAX_ZOOM`, `GRID_STEPS`, `GRID_MIN_PX`, `SELECT_COLOUR`). Doublons : 78/174 → 55/121. *Écarts* : D7 — l'export porte `size` en **1.4** et non 1.2, 1.2 et 1.3 étant déjà pris (textes, figures nommées depuis la racine) ; 1.4 est écrit par tout export depuis v0.120, le contenu disant le reste. D2 — le `SvgLayer` unique garde deux façons de conserver le rendu (`per_view=True` pour les schémas, le cache de Qt sinon) : le cache par vue rend à nouveau à chaque déplacement, ce qu'une page A3 de plan ne supporterait pas, et le cache de Qt avait gelé les schémas (v0.77) ; la mesure sur un plan A3 n'a donc pas lieu, le plan gardant son cache. ARCH-RISK-303 — la base de toile ne porte aucun délai de rendu : ceux de v0.116 restent aux toiles qui rendent un fond (plans), la base n'en a pas l'usage. Le zoom, l'aimantation et la lecture du plan restent les siens (ils rendent son fond), la base n'en donne au plan que le curseur et la touche Espace. |
| 2026-10-20 | implementation | **Lot 6 fait** (ARCH-003) : C7 — `UnfoldError` (`ValidationError`), `DomainError` et `FormulaError` (`ValidationError, ValueError`) : un export qu'elles arrêtent dit «export failed: …» et non une trace ; aucun `except` ne se trouve masqué (vérifié sur l'arbre de `calc/`). C3 — `validate_structure` en tête de `steel_check.check_source` et de `profile.check_source` ; toutes les sources acier et profilés des tests y passent. C6 — le docstring de `member_check.py` dit le double calcul voulu (Python pour la fenêtre, Typst pour le rapport) ; `_held_equal` compare aussi la clause de chaque ligne à celle du registre, et le test exige chaque genre d'`IMPLEMENTED`. C5 — `calc/domains/contracts.py` : `SourceDomain` et `ExportDomain` (Protocol), `tests/test_domain_contracts.py` (table, et toute nouvelle source ou export sans ligne échoue) ; `script.SCHEMA_VERSION` → `EXPORT_SCHEMA_VERSION`. *Écart* : C7 — les deux `Refused` restent tels quels : celui de `schema_edit` est le refus d'une modification dans la fenêtre, celui de `script_runner` vit dans le processus d'un script ; aucun export ne les rencontre, il n'y a rien à attraper. |
| 2026-10-20 | implementation | **Lot 7 fait** (ARCH-002, C1, C2, Q-011) : `steel_calc.Calc` → `SteelCalculation(engine.Calculation)` (citation et niveau vérifiés par le moteur) ; une valeur saisie (effort, côté d'un profilé dessiné) cite SIA 263 et la clause du verdict qu'elle sert ; `data/steel.json` 1.1 (le schéma admet 1.0 et 1.1). `member_check` : `NORM`, `_row(norm=)` passe `engine._check_citation`, une ligne à clause porte `norm` ; les lignes feu citent les clauses que `#member(fire:)` cite (4.5.2, Tabelle 13, 4.5.2.2, 4.5.2.5) ; `published_vars` cite la clause du contrôle pour une valeur saisie ; `unfold` lit la norme de la ligne. Tests : `_held_equal` compare aussi la clause de chaque ligne au registre et exige chaque genre d'`IMPLEMENTED` (C6) ; `test_domain_contracts.test_every_row_and_var_of_a_check_cites_its_norm` ; `test_unfold.test_the_example_projects_unfolded_checks_are_written_byte_for_byte_as_held` (ARCH-RISK-204 : les fichiers dépliés du projet exemple restent identiques à l'octet). L'export du projet exemple refait pour `checks.json` et `steel.json`. *Laissé à l'ingénieur* : Q-017 (citer VKF 15-15 pour une durée exigée change `fire:` de `#member`) et Q-018 (ce que cite un résultat de script). |
| 2026-10-20 | implementation | Lots 5 à 7 commités (6b1391a), suite complète 3042 passés, 11 ignorés, l'unique échec (un test neuf qui lisait la copie du processus) corrigé. **Lot 8 fait** (REQ-003, C4, UI-004) : comparaison classeur / JSON / SIA 261:2020 (tableau dans `docs/domain/loads.md` §3.3sexies-bis) — C_e (5.2.4), corrections d'Anhang D, μ_1, μ_2 et toit plat étendu (Figur 2, 5.3.5), z_g et α_r (Tabelle 4) : les deux sources disent la même chose que la norme, rien à corriger dans les JSON ; les tables du classeur lues dans deux classeurs de l'ingénieur (identiques, ce sont celles du modèle), en lecture seule. `snow.py` et `wind.py` prennent désormais tous les nombres de la norme dans `calc/norms/` (`sia261_snow`, `sia261_wind`) et ne lisent du classeur que ses propres mots ; une table du classeur qui dit un autre nombre arrête l'import en nommant la cellule (tests dans `test_snow_source`, `test_wind_source`). UI-004 : la formule de s_k et le μ_1 du glissement empêché (5.3.4) composés depuis les valeurs ; `_common.plain` remplace les deux `_fmt` des sources de charges. C4 : les deux `print` (registry, wind) deviennent des `engine.Note` de la liste de l'export, avec leurs phrases fr/de/en (`warn_registry_no_sheet`, `warn_wind_surfaces_unchecked`) ; `test_domain_contracts.test_no_domain_prints_what_it_has_to_say`. *Écart* : C4 — les avertissements des connecteurs et des goujons restent des phrases allemandes traduites par le glossaire, pour la fenêtre comme pour le rapport ; en faire des `Note` à phrases `warn_*` écrirait chaque traduction deux fois (glossaire et chaînes de la fenêtre). |
| 2026-10-20 | implementation | Lot 8 commité (bcd28df). **Lot 9, première moitié** (a3607b1) : UI-002, UI-003, UI-007 — `lib/number.typ` (`display-number`, `display-source`, `display-quantity` ; `fmt-decimals`, `minus-sign`, `signed-text`, `sup` y passent) et `calc/number_text.py` (`display`, `trimmed`, `exact`), tenus égaux par `tests/test_number_text.py` ; toutes les fonctions d'affichage de `lib/` passent par la règle (`fmt-number` et les tableaux, `value-text`, `value-in-formula`, `#var`, `#eq`, `#verify`, `#val`, les nombres et les angles d'une connexion, les notes de `distance`) ; `fmt-magnitude` et le `digits` de `formula.typ` supprimés ; `number-digits` ne change plus rien (état gardé, retiré de la référence et de ses deux exemples) ; les quatre `_fmt` des domaines et `svg_draw.number` sont `number_text.trimmed` ; pas d'espace avant « ° » ; le point décimal dans `dowel` (`_de` supprimé). *Écarts* : le module Python s'appelle `number_text`, `numbers` étant un module de la bibliothèque standard que `calc/` masquerait ; la règle passe en notation scientifique sous 0.1 seulement là où trois décimales n'écrivent pas la valeur entière (0.05 reste 0.05, 0.00234 devient 2.34 · 10⁻³), lecture de « au moins trois chiffres significatifs » qui ne perd aucun chiffre ; les quantités de `positions.typ` et de la légende d'un plan gardent leurs zéros de colonne (une figure, ARCH-RISK-402). |
| 2026-10-20 | implementation | **Lot 10** : G6 (5728de6) — `build_reference`, `build_reference_lib`, `build_reference_calls` et `usersettings` passent dans `calc/`, les `try/except ImportError` et les deux `_usersettings()` disparaissent. Documentation : `decisions.md` §13 (six décisions, et les deux décisions « Snow/Wind is calculated in Excel » complétées) et son index, `CHANGELOG.md`, la page « Nouveautés » 0.120.0 en fr/de/en (0.120 n'étant pas publiée), les `docs/` de chaque lot. **Reporté à une spec dédiée** (décision de mise en œuvre, dite à l'ingénieur) : UI-001 (la table des indices et leur normaliseur), UI-005 (les niveaux décidés par Typst depuis une table, `level` optionnel à l'export), UI-006 (`level:` sur chaque commande qui imprime, renversement de `decisions.md:131,479`) et le gel unique des exemples — un changement typographique et de contrat qui touche chaque commande et chaque rapport, à décider et à vérifier pour lui-même. |
