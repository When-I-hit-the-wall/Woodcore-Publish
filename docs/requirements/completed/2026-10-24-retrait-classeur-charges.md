---
id: 2026-10-24-retrait-classeur-charges
titre: Retirer la lecture du classeur de charges pour le vent, la neige et les charges permanentes (D-33)
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-25
source: issue GitHub #109
docs: [docs/domain/loads.md, docs/domain/calculation-domains.md, docs/architecture/layout.md, docs/architecture/principles.md, docs/decisions.md, docs/conventions/testing-catalogue.md]
---

# Retirer la lecture du classeur de charges — Spécification

## 1. Objectif

Woodcore ne lit plus les feuilles `WL-*`, `SL-*` et `EL+AL-*` des classeurs « Belastungsannahmen » : le vent, la neige et les charges permanentes ne viennent plus que des sources saisies dans Woodcore (`wind_source`, `snow_source`, `dead_load_source`). Le retrait touche les lecteurs, le registre et l'export, les projets existants dont les cas viennent d'un classeur, le projet d'exemple, les tests et la documentation. **L'ingénieur a répondu aux six questions de l'issue le 24.10.2026 (§10) : aucune conversion, un message générique, tout retiré y compris le vocabulaire et les schémas relevés, l'exemple converti une fois à la main. La revue (§13) et le plan (§14) suivent ; rien n'est implémenté avant son approbation.**

État constaté du code (au 24.10.2026, voir §13 pour les modules) :

- `calc/registry.py` cherche tout fichier `.xlsm`/`.xlsx` dont le nom contient « Belastungsannahmen » (`open_workbooks`), découvre les feuilles par préfixe (`SHEET_PREFIX` : `WL` pour `calc/domains/wind.py`, `SL` pour `snow.py`, `EL+AL` pour `dead_load.py`) puis ajoute les instances des sources (`SOURCE_MODULES`). `live_load.py` a `SHEET_PREFIX = None` : la charge utile vient du tableau 8 de la SIA 261, pas d'un classeur.
- Depuis v0.120, `wind.read_source(cells, sheet)` et `snow.read_source(cells, sheet)` ne lisent déjà que les entrées d'une feuille et rendent **un dict de source** que `wind_source.build_instance` / `snow_source.build_instance` calculent : la conversion d'une feuille de vent ou de neige en source existe donc presque entière. `dead_load.read_instance` lit les couches et les pèse contre la bibliothèque du classeur (`MaterialLibrary`) ; `dead_load.instance_from_layers` (l'arithmétique partagée) est aussi appelée par `dead_load_source.build_instance`.
- `export_all.run` (l. 184–192) appelle `open_workbooks`, écrit une ligne « no load workbook … -- loads: none » et `project.record` consigne les empreintes des classeurs lus dans `data/project.json` (`workbooks`) ; l'export s'arrête si un classeur lu à l'export précédent a disparu (v0.89.1).
- Le **projet d'exemple n'a pas de classeur** (`tests/conftest.py` : « no workbook »). Son `000-Woodcore/data/calculations.json` est un export ancien : `dead-load` 4 instances (`EL+AL-Dach mit Wasser`, `EL+AL-Dach ohne Wasser`, `EL+AL-DachRand`, `EL+AL-Wand`), `snow-load` 1 (`SL`), `wind-load` 3 (`WL-Velo`, `WL-Fluchttreppe+Geräte`, `WL-Pavillon`), toutes de « Belastungsannahmen.xlsm » ; ses sections `Variable-loads/Wind/WL-*.typ` (3), `Variable-loads/Snow/SL.typ` (1), `Permanent-loads/EL+AL-*.typ` (4) les citent. Il n'a **aucune** source `loads/` dans `000-Woodcore/sources/`.
- Ce que fait déjà #111 (spec `docs/requirements/completed/2026-10-24-poids-propre-repense.md`, commité en be5b85f : `dead_load_migrate.py`, `dead_load_layers.py`, …) : `dead_load_migrate.upgrade` migre **les sources `dead-load-source` 1.0–1.2 vers 2.0**, en mémoire, et convertit l'« Ebene » du classeur en rôle de couche (`EBENE_ROLES`) ; la bibliothèque de matériaux vient de `calc/libraries/` (CON-004 de #111 : « Le classeur n'est pas lu (#109) »). **Il ne convertit aucune feuille de classeur en source** : le « classeur » n'y est qu'une origine de matériaux (`belastungsannahmen`, déjà extraite dans `materials-library.json` par #110). #111 liste explicitement « La lecture du classeur de charges (#109) » hors périmètre.

## 2. Source

L'issue GitHub #109, par points. Rien n'est reformulé.

> **T1** — « L'ingénieur, 24.10.2026 : « il n'y aura plus jamais de feuille excel à lire pour le vent, ni pour la neige, ni pour les charges permanentes » (D-33 de la spec `docs/requirements/active/2026-10-23-onglet-vent-briques.md`). »
>
> **T2** — « Woodcore doit donc retirer la lecture des feuilles du classeur de charges (Belastungsannahmen) pour ces trois domaines. Ils ne viendront plus que des sources saisies dans Woodcore (`wind_source`, `snow_source`, `dead_load_source`). »
>
> **T3** — « Poser d'abord toutes les questions d'implémentation à l'ingénieur, et attendre ses réponses. Rien n'est implémenté avant. Passer par le skill `big-feature` : spec, questions, revue d'architecture, une approbation. »
>
> **T4** — « les lecteurs : `calc/domains/wind.py` (feuilles WL-*), `calc/domains/snow.py`, et celui des charges permanentes ; »
>
> **T5** — « l'export : `registry`, `export_all`, l'avertissement « pas de classeur » ; »
>
> **T6** — « les projets existants dont les cas viennent d'un classeur : migration vers des sources Woodcore, ou un message, ou rien ; »
>
> **T7** — « le projet d'exemple `tests/projet-exemple/`, avec ses fichiers `Variable-loads/Wind/WL-*.typ` et ceux de la neige et des charges permanentes ; »
>
> **T8** — « les tests (`tests/test_load_sheets.py` et ceux qui lisent un classeur) ; »
>
> **T9** — « la documentation (`docs/domain/loads.md` §3.3, §3.3quater, §3.3sexies-bis), le CHANGELOG et les « Nouveautés » ; »
>
> **T10** — « la suite du classeur : les charges utiles (`live-load`) et les autres feuilles restent-elles lues ? »
>
> **T11** — « Les cas d'un projet existant venant d'un classeur sont-ils convertis en sources Woodcore (une fois, à l'ouverture, ou par une commande), ou simplement plus lus ? »
>
> **T12** — « Que voit l'ingénieur dans un projet qui n'a que des feuilles : un message, un bouton de conversion ? »
>
> **T13** — « Les identifiants des cas (`WL-Pavillon`…) et les variables que les sections citent restent-ils les mêmes ? »
>
> **T14** — « Le classeur reste-t-il lu pour autre chose ? »
>
> **T15** — « Fait : D-33, la cellule G86 n'est pas lue. Depuis 6a18d7c, une feuille WL-* passe par `wind_source.build_instance` et n'imprime que « réparties ». »

## 3. Exigences fonctionnelles

### REQ-001 — Plus de lecture de feuille pour le vent, la neige, les charges permanentes
- **Exigence** : Woodcore doit ne plus lire les feuilles `WL-*`, `SL-*` et `EL+AL-*` d'aucun classeur, ni à l'export ni à l'enregistrement d'un cas dans un onglet (`registry.export`) ; les instances des trois domaines (`wind-load`, `snow-load`, `dead-load`) ne viennent que de leurs sources (`loads/wind`, `loads/snow`, `loads/dead`). Aucun lecteur réduit n'est gardé (Q-001 C).
- **Source** : T1, T2, T4
- **Priorité** : doit
- **Critère d'acceptation** : un projet avec un classeur contenant des feuilles `WL-x`, `SL-x`, `EL+AL-x` et sans source exporte sans que `data/calculations.json` contienne une instance venue d'une feuille, et sans ouvrir le fichier (test sur un classeur aux octets illisibles : l'export et `registry.export` n'y échouent pas).

### REQ-002 — Registre, export et schémas sans classeur
- **Exigence** : Woodcore doit retirer de `registry` la découverte des feuilles (`SHEET_PREFIX`, `_discover`, `reads_sheets`, `open_workbooks`, `is_load_workbook`, `WORKBOOK_SUFFIXES`), de `export_all` l'ouverture des classeurs, la ligne « no load workbook … -- loads: none », l'arrêt quand un classeur lu auparavant a disparu (`_workbooks_read_before`), l'avertissement `registry_no_sheet` et les `sheet_*` (trois langues dans `woodcore_gui_words.py`), `calc/io_excel.py`, le contrôle `SHEET_PREFIX` / `ENGINES = excel` de `validation.py`, les champs `workbook`, `sheet` et `sheet_prefix` de `calculations.json`, la provenance `excel:` (`variables.py`, `variable_sources.py`, onglet Variables) et le champ `workbooks` de `project.json` (Q-004 B : tout, vocabulaire compris). Ne reste du classeur que le motif du nom de fichier du message de REQ-003.
- **Source** : T4, T5 ; Q-004 B
- **Priorité** : doit
- **Critère d'acceptation** : `grep` de `open_workbooks`, `reads_sheets`, `registry_no_sheet`, `io_excel`, `SHEET_PREFIX`, `sheet_prefix`, `"excel"` (moteur), `excel:` (provenance), `model.EXCEL` dans `calc/`, `lib/`, `schemas/` et `tests/` : aucune occurrence hors historique ; un projet sans classeur ni source exporte et le rapport dit quels domaines de charges sont vides (comportement v0.117 conservé).

### REQ-003 — Un projet dont les cas ne sont que des feuilles : un message, aucune conversion
- **Exigence** : Woodcore ne convertit aucun cas de classeur (Q-001 C) et **un cas ne disparaît jamais sans que l'ingénieur le sache** (règle « un manque avertit »). Quand le dossier du projet contient un fichier `.xlsm` ou `.xlsx` dont le nom contient `Belastungsannahmen` (sans casse, sans sous-dossier, sans fichier de verrou `~$` d'Excel), chaque export complet donne **un avertissement générique** qui nomme le ou les fichiers, dit qu'ils ne sont plus lus et où se saisissent les cas (UI-001). Le fichier n'est pas ouvert (Q-002 B) : ni feuilles, ni cas listés. Il reste en place, intact (Q-006).
- **Source** : T6, T11, T12 ; Q-001 C, Q-002 B
- **Priorité** : doit
- **Critère d'acceptation** : test : un dossier avec `02_Belastungsannahmen.xlsm` (octets illisibles) et sans source ; l'export réussit, ses avertissements contiennent une seule `Note` de code `load_workbook_not_read` qui porte le nom du fichier ; `~$02_Belastungsannahmen.xlsm` seul ne donne rien ; deux fichiers donnent une note qui les nomme tous deux ; octets et date du fichier intacts ; trois phrases (fr/de/en) dans `woodcore_gui_words.py`.

### REQ-004 — Projet d'exemple : huit cas devenus des sources
- **Exigence** : Woodcore doit rendre le projet d'exemple cohérent avec le retrait : ses 8 cas (3 vents, 1 neige, 4 charges permanentes) existent comme sources dans `000-Woodcore/sources/loads/{wind,snow,dead}/` (Q-005 A), de mêmes valeurs ; 5 identifiants sont gardés (`SL`, `WL-Velo`, `WL-Pavillon`, `EL+AL-DachRand`, `EL+AL-Wand`), 3 corrigés (Q-003 A) ; leurs sections sont réécrites par le code des onglets, les citations de `004-einwirkungen.typ` suivent ; l'export est régénéré, figures comprises.
- **Source** : T7 ; Q-003 A, Q-005 A
- **Priorité** : doit
- **Critère d'acceptation** : `python tests/run_tests.py` vert avec un export complet du projet d'exemple ; chaque identifiant cité par une section de `Variable-loads/` et `Permanent-loads/` et par `004-einwirkungen.typ` existe dans `calculations.json` ; la comparaison de ARCH-002.

### REQ-005 — Tests
- **Exigence** : Woodcore doit retirer ou récrire `tests/test_load_sheets.py` (fixture `tests/fixtures/load-sheets-reference.json`, constructeur `tests/fixtures/workbook.py`), les parties de `tests/test_dead_load.py` (17), `test_dead_load_source.py` (25), `test_new_project.py` (14), `test_archive.py` (13), `test_wind_source.py` (11), `test_snow_source.py` (6), `test_export.py` (8), `test_window.py` (7), `test_project.py` (10), `test_norms.py` (10), `test_variables.py` (10), `test_variable_sources.py`, `test_sia260.py`, `test_line_levels.py`, `test_domain_contracts.py` qui construisent ou lisent un classeur de charges ou son vocabulaire (comptes de mentions « workbook/xlsx/xlsm » à trier : beaucoup concernent `Positions.xlsx` ou `Verbindung.xlsm`, qui ne sont pas touchés), et tenir la ligne du catalogue `docs/conventions/testing-catalogue*.md` de chaque fichier changé ou supprimé.
- **Source** : T8
- **Priorité** : doit
- **Critère d'acceptation** : aucun test ne construit de classeur de charges, sauf le fichier aux octets illisibles de REQ-003 ; la suite complète passe.

### REQ-006 — Les charges utiles et les autres feuilles
- **Exigence** : Woodcore doit garder `live-load` tel quel (tableau 8 de la SIA 261, sans classeur) moins sa ligne `SHEET_PREFIX = None` ; aucun code de `calc/` ne lit une autre feuille d'un classeur de charges (constat du code), donc le classeur n'est plus lu du tout. `calc/build_reference.py` (docs/typst-reference.xlsx, écrit, jamais lu) perd sa seule colonne `workbook` et son `source_type` « sheet » (l.490, 583, 658), qui lisaient les champs retirés ; `positions_workbook.py` ne change pas.
- **Source** : T10, T14
- **Priorité** : doit
- **Critère d'acceptation** : `data/calculations.json` d'un projet sans classeur contient les 12 catégories de `live-load` (A1 … H) ; `positions_workbook.py` intact ; `build_reference.py` ne change que ces deux endroits.

### REQ-007 — Schémas relevés, anciens exports refusés (revue)
- **Exigence** : `data/calculations.json` passe de 1.8 à **1.9** (plus de `sheet_prefix` requis, de `workbook` ni de `sheet` ; l'énumération de `schema_version` ne contient que « 1.9 » ; le moteur d'un domaine est `python` ou `norm`) et `data/project.json` de 1.0 à **1.1** (plus de `workbooks`). Un export plus ancien est **refusé là où il est lu**, jamais par l'export qui le remplace (C-1) : le schéma (l'onglet Variables dit `bad_file`, `variable_sources.read_export`), le compilateur Typst (`load-calculations`) et `woodcore-cli check` disent « écrit par une version antérieure (1.8) : lancer Import données ».
- **Source** : Q-004 B ; revue (ARCH-RISK-002) ; principe « un fichier malformé arrête en nommant le fichier et le champ »
- **Priorité** : doit
- **Critère d'acceptation** : tests : un `calculations.json` en 1.8 mis dans la copie de l'exemple — `read_export` rend une `bad_file` qui nomme `schema_version`, la compilation d'une section s'arrête avec la phrase et le remède, l'export complet n'est pas arrêté et réécrit le fichier en 1.9 ; un `project.json` en 1.0 est reconstruit par `refresh_project_info` sans erreur ; `schemas/calculations.schema.json` et `project.schema.json` validés par `tests/test_schema_consumers.py` ; le CHANGELOG et la page « Nouveautés » nomment les deux versions.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Ce que voit l'ingénieur dans un projet qui n'a que des feuilles
- **Exigence** : une `Note` de code `load_workbook_not_read` (`warn_load_workbook_not_read` dans `woodcore_gui_words.py`, trois langues), donnée à chaque export complet quand un fichier au nom `*Belastungsannahmen*` est dans le dossier ; une phrase d'une ligne sur la sortie de `woodcore-cli`. Fr : « Un classeur de charges est présent dans le dossier du projet ({files}) : Woodcore ne le lit plus. Les cas de vent, de neige et de charges permanentes se saisissent dans les onglets Vent, Neige et Poids propre. » Ni bouton, ni liste de feuilles (Q-002 B).
- **Source** : T12, Q-002 B
- **Langues** : fr / de / en
- **Critère d'acceptation** : voir REQ-003.

### UI-002 — Documentation et nouveautés
- **Exigence** : `docs/domain/loads.md` §3.3bis, §3.3ter, §3.3quater, §3.3sexies-bis (et `docs/domain/calculation-domains.md` §3.3, `docs/architecture/layout.md`, `principles.md`, `data-contracts.md`) réécrits sans la lecture de feuilles, une décision (D-… dans `docs/decisions.md` et `decisions-index.md`), une entrée `CHANGELOG.md`, la page « Nouveautés » de la prochaine version en fr/de/en, qui dit en tête de cliquer « Import données » une fois (C-1) ; le tutoriel `website/content/*/tutorial/04-loads.md` et `02-project.md`, qui parlent du classeur, suivent.
- **Source** : T9
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_docs_coherence.py` passe ; `grep -ri "Belastungsannahmen" docs/domain docs/architecture website/content` ne laisse que l'historique et la description de l'ancienne lecture.

### UI-003 — La fenêtre sans classeur (revue)
- **Exigence** : l'onglet Variables (tel que #114 l'aura laissé) ne montre plus la provenance « Excel » (filtre, colonne ou « Vient de »), ni « Ouvrir le classeur », ni les champs `workbook`/`sheet` du domaine ; le bandeau `stale` (« ... modifié après le dernier export », `woodcore_gui_menus.stale_workbooks`) disparaît ; un état de vue enregistré avec la provenance `excel` se restaure sans erreur.
- **Source** : Q-004 B ; revue
- **Langues** : fr / de / en
- **Critère d'acceptation** : tests de l'onglet Variables et de `tests/test_variable_sources.py` récrits sans `excel:` ; `tests/test_window.py:145–161` (bandeau) retiré ; un test restaure un état de vue portant `excel`.

## 5. Exigences d'architecture

### ARCH-001 — Une seule source de vérité des cas
- **Exigence** : une fois le retrait fait, `calc/domains/wind.py`, `snow.py`, `calc/io_excel.py` et le lecteur de feuilles de `dead_load.py` (`MaterialLibrary`, `read_materials`, `_read_layers`, `_check_chosen`, `read_instance`, `read_instances`) n'existent plus, sauf le noyau partagé `instance_from_layers` (utilisé par `dead_load_source.build_instance`) ; `registry` lit `LABEL`, `ACTION`, `ENGINE` sur les modules de source (`snow_source`, `wind_source`, `dead_load`) et non plus sur les modules de feuille ; `validation.py` (contrôle `SHEET_PREFIX`, l.367–378) et `loads_names.py` (ce que la feuille a calculé) suivent.
- **Source** : T2 ; principes 1 (une source de vérité) et 3 (pas de code mort qui vieillit sans le dire) de `docs/architecture/principles.md`
- **Critère d'acceptation** : aucun import de `domains.wind` / `domains.snow` / `io_excel` ; `tests/test_harness.py` et l'audit de modules passent.

### ARCH-002 — Pas de recalcul, pas de copie, pas de code gardé pour une seule fois
- **Exigence** : la conversion de l'exemple (Q-005 A) n'ajoute rien au dépôt : un script jeté dans le scratchpad, qui écrit les sources par `check_source` / `stamp_version` des modules de source, et les sections par le chemin des onglets (`unfold`) ; elle ne réécrit aucun calcul et ne garde aucune copie du classeur.
- **Source** : Q-001 C, Q-005 A ; principe « No value copied by hand »
- **Critère d'acceptation** : pour chacun des huit cas, `build_instance(source)` donne les mêmes noms de variables, les mêmes valeurs (tolérance 1e-9) et les mêmes `results` que l'ancien export 1.8 de l'exemple ; la sortie de la comparaison est collée au §16.

### ARCH-003 — Cohérence avec #111
- **Exigence** : le retrait ne touche pas `dead_load_migrate.py` (migration de schéma 1.x → 2.0, pas de feuilles) ni la bibliothèque `calc/libraries/` ; #111 est commité (be5b85f), l'ordre est donc tenu ; l'état de `dead_load*.py` est relu avant d'y toucher (une autre session peut l'avoir changé).
- **Source** : inféré (règles de travail de CLAUDE.md : plusieurs sessions)
- **Critère d'acceptation** : le plan (§14) place les étapes touchant `dead_load*.py` après le commit de #111 (tenu).

### ARCH-004 — Les règles de conception et les décisions qui changent (revue)
- **Exigence** : D-33 contredit les règles 5 (« provenance Excel / Python / Typst ») et 6 (« un cas est une feuille Excel »), le paragraphe « Excel as the primary source » et le schéma de `docs/architecture/principles.md` §2, et huit décisions encore « in force » de `docs/decisions-index.md` (§13, ARCH-RISK-001) : le plan les réécrit et les marque `superseded` dans la décision qui porte D-33.
- **Source** : revue ; CLAUDE.md « Preserve the architecture unless there is a stated, justified reason »
- **Critère d'acceptation** : `grep -n "Excel" docs/architecture/principles.md` ne laisse que l'import des positions et l'historique ; une entrée `docs/decisions.md` §13 et ses lignes de `decisions-index.md`.

### ARCH-005 — `loads_migrate` et `loads_names` restent, sans cellules de feuille (revue)
- **Exigence** : voir C-3. `loads_names.py` n'importe plus `domains.snow` (`roof_of`, `ROOF_OF` y migrent) ; `loads_migrate.py` lit encore l'ancien export par `engine.previous_json`, sans le valider, donc sans être touché par le refus de REQ-007.
- **Source** : revue
- **Critère d'acceptation** : `tests/test_loads_migrate.py` passe sans changement ; `grep "SNOW_COMPARED\|wind_compared\|WIND_AREAS" calc/` : aucune occurrence de la lecture d'une cellule.

### ARCH-006 — Les textes du produit (revue)
- **Exigence** : `calc/cli.py:205` (`woodcore-cli new` : « copy the office's Belastungsannahmen workbook into the folder »), la docstring de `woodcore-cli check` (« every workbook read »), `calc/project_template.py`, les gabarits `templates/projet/**/004-einwirkungen.typ` et `templates/documents/rs/standard/{de,en,fr}/Sections/004-einwirkungen.typ` (commentaire « Every case of the load workbooks, one sheet each »), le tutoriel (`01-install`, `02-project`, `04-loads`, `05-window`, trois langues), les pages `download` et `README.md` ne disent plus de copier le classeur ; la mention « Excel » du bouton « Import données » (`reexport_what`) suit.
- **Source** : revue
- **Critère d'acceptation** : `grep -ril "Belastungsannahmen" templates website/content calc README.md` ne laisse que `website/content/*/changes/` (historique) et le motif unique du message.

## 6. Contraintes

- **CON-001** — Un fichier que Woodcore a écrit mais malformé arrête l'export en nommant le fichier et le champ ; ce qui manque avertit (CLAUDE.md). Un cas de feuille qui n'est plus lu manque donc d'une manière que l'ingénieur doit voir (REQ-003). Source : principe.
- **CON-002** — Les identifiants de source doivent vérifier `ID_PATTERN = ^[A-Za-z0-9][A-Za-z0-9_.+-]*$` (`wind_source`, `snow_source`, `dead_load_source`) : `WL-Fluchttreppe+Geräte` (accent), `EL+AL-Dach mit Wasser` et `EL+AL-Dach ohne Wasser` (espaces) **ne sont pas des identifiants de source valides** : trois des huit cas de l'exemple (Q-003 A les corrige). Source : constat du code.
- **CON-003** — Les noms des variables ont déjà été renommés une fois en v0.120 (`qk_max_bh` → `qk_max_cf1`, `loads_names.py`, migration `loads_migrate.py` à l'ouverture) ; un nouveau renommage doit passer par ce même mécanisme. Source : constat.
- **CON-004** — Le projet d'exemple est un vrai projet anonymisé, sans classeur ; tous les tests travaillent sur sa copie (`tests/conftest.py`). Source : conftest.
- **CON-005** — Publication (installeur, site, push) attend le mot de l'ingénieur. Source : CLAUDE.md.
- **CON-006** — Rien n'est écrit dans un projet réel (D-02) ; les tests travaillent sur la copie de `tests/projet-exemple/`. Source : Q-001 C.

## 7. Décisions prises

- **D-33** (spec du vent, 24.10.2026) : « il n'y aura plus jamais de feuille excel à lire pour le vent, ni pour la neige, ni pour les charges permanentes ». La cellule G86 n'est pas lue ; depuis 6a18d7c une feuille `WL-*` passe par `wind_source.build_instance` (T15).
- **D-01** — Les charges utiles (`live-load`) viennent du tableau 8 et n'ont jamais lu de classeur : rien à retirer (REQ-006). Constat, à confirmer par la lecture de cette spec.
- **D-02** — Aucune conversion des projets existants (Q-001 C, 24.10.2026) : les feuilles ne sont plus lues, rien n'est écrit dans un projet réel, l'ingénieur ressaisit ses cas. Remplace les options A, B et D de Q-001.
- **D-03** — Un message générique, sans ouvrir le classeur (Q-002 B) : « un classeur de charges est présent et n'est plus lu », dès qu'un fichier dont le nom contient `Belastungsannahmen` est trouvé dans le dossier du projet.
- **D-04** — Identifiants gardés quand ils sont valides, sinon corrigés par un tableau de renommage listé (Q-003 A) ; appliqué au projet d'exemple seul (trois cas).
- **D-05** — Tout retirer, vocabulaire compris (Q-004 B) ; schémas relevés d'une version (`calculations` 1.9, `project` 1.1), anciens exports refusés (sens et lieu du refus : C-1).
- **D-06** — Les huit cas de l'exemple convertis une fois, à la main, en sources de mêmes valeurs et d'identifiants corrigés ; sections réécrites par le code des onglets (Q-005 A).
- **D-07** — Le fichier Excel reste en place, jamais ouvert ni déplacé (Q-006, par Q-001 C et Q-002 B).

## 8. Hors périmètre

- `Positions.xlsx` et `positions_workbook.py` (import des positions, déjà archivé à la migration v0.114) et `docs/typst-reference.xlsx` (écrit par `build_reference.py`).
- La bibliothèque de matériaux (#110) et la refonte des couches (#111, y compris `dead_load_migrate.py`).
- Toute nouvelle norme ou tout nouveau calcul de vent, neige, charges permanentes.

## 9. Idées non retenues comme exigences

- Une commande générale « importer un classeur » réutilisable pour d'autres cabinets : non demandée ; la question Q-001 la traite si l'ingénieur la veut.

## 10. Questions

### Q-001 — Les cas d'un projet existant qui ne sont que des feuilles sont-ils convertis en sources Woodcore, et quand ?
- **Contexte** : aujourd'hui un projet peut avoir ses cas dans un classeur (par exemple `02_Belastungsannahmen.xlsm`, feuilles `WL-Pavillon`, `SL`, `EL+AL-Wand`) et rien dans `Woodcore-Datei/loads/`. Dès que la lecture des feuilles est retirée, ces cas disparaissent du rapport au prochain export, et les sections qui les citent (`show-calc("wind-load", "WL-Pavillon")`) s'arrêtent. Le code sait déjà transformer une feuille de vent ou de neige en source (`wind.read_source`, `snow.read_source`) ; pour les charges permanentes il faut lire les couches du classeur, ce que #111 ne fait pas (il ne migre que les sources 1.x vers 2.0). Le projet d'exemple, lui, n'a pas de classeur du tout.
- **Pourquoi elle compte** : c'est la différence entre garder un petit lecteur de feuilles (réduit à l'import) ou le supprimer entièrement avec les tests qui le portent (`test_load_sheets.py`, le classeur de test), et entre un projet réel qui continue de s'exporter ou qui perd ses charges.
- **Options** :
  - A (recommandée) — **Une commande explicite**, par exemple `woodcore-cli import-loads` et un bouton dans la fenêtre : elle lit le classeur une dernière fois, écrit une source par feuille (vent, neige, charges permanentes), sans toucher au classeur, et dit ce qu'elle a fait ; le lecteur réduit (`read_source` des trois domaines) reste dans un module `loads_import` jusqu'à une version fixée, puis part. Prix : un petit code gardé un temps, mais rien n'est converti sans que l'ingénieur le décide.
  - B — **Conversion automatique, une fois, à l'ouverture** du projet (comme `loads_migrate` à l'ouverture et la migration de `Positionen.xlsx` v0.114) : l'ingénieur ne fait rien. Prix : des fichiers écrits sans demande dans le projet ; une feuille mal lue donne une source fausse dont il ne sait pas d'où elle vient.
  - C — **Aucune conversion** : les feuilles ne sont plus lues, un message dit lesquelles (Q-002) ; l'ingénieur ressaisit ses cas dans les onglets. Prix : le plus simple et le plus net avec D-33 ; mais un projet réel perd ses cas jusqu'à la ressaisie.
  - D — Conversion **seulement pour le vent et la neige** (lecteurs déjà proches de la source), les charges permanentes ressaisies. Prix : deux régimes.
- **Réponse** : C — aucune conversion (ingénieur, 24.10.2026) : les feuilles des projets existants ne sont plus lues, l'ingénieur ressaisit ses cas dans les onglets. Conséquence : ni commande `import-loads`, ni module `loads_import`, ni lecteur réduit gardé ; `wind.read_source` et `snow.read_source` partent avec leurs modules.

### Q-002 — Que voit l'ingénieur dans un projet qui n'a que des feuilles ?
- **Contexte** : un classeur « Belastungsannahmen » est trouvé par son nom dans le dossier du projet (`registry.is_load_workbook`). Si on ne le lit plus, trois comportements sont possibles pour un projet où ce classeur contient des feuilles `WL-*`, `SL-*`, `EL+AL-*` et où aucune source n'existe. L'export imprime aujourd'hui une seule ligne (« export_all: no load workbook … -- loads: none »), sans avertissement depuis v0.117.
- **Pourquoi elle compte** : sans message, un rapport perd ses charges sans bruit — le défaut que le projet craint le plus (« une copie qui vieillit sans le dire »).
- **Options** :
  - A (recommandée) — **Un avertissement à l'export, par feuille repérée par son nom seul** (le classeur est ouvert pour lister les noms de feuilles `WL*`/`SL*`/`EL+AL*`, rien d'autre n'est lu) : « La feuille WL-Pavillon du classeur X n'est plus lue — créez le cas dans l'onglet Vent (ou lancez l'import, Q-001) », fr/de/en, dans la fenêtre et dans le rapport CLI. Prix : le classeur reste ouvert pour les noms.
  - B — **Message générique sans ouvrir le classeur** : « un classeur de charges est présent et n'est plus lu » dès que `Belastungsannahmen` est trouvé par son nom de fichier. Prix : aucun code de lecture, mais ne dit pas quels cas manquent.
  - C — **Rien** (comme un projet neuf sans charges). Prix : silencieux ; non recommandé.
  - D — Selon Q-001 A : en plus du message A, un bouton « Importer le classeur » à côté.
- **Réponse** : B — message générique, sans ouvrir le classeur (ingénieur, 24.10.2026) : « un classeur de charges est présent et n'est plus lu » dès qu'un fichier `Belastungsannahmen` est trouvé par son nom. Aucune liste de feuilles, aucun bouton. Conséquence : le seul reste du classeur dans le code est le motif de son nom de fichier ; sa permanence est à confirmer en C-2.

### Q-003 — Les identifiants des cas et les variables citées restent-ils les mêmes ?
- **Contexte** : les sections du projet citent les cas par leur nom de feuille (`WL-Pavillon`, `SL`, `EL+AL-Dach mit Wasser`) et leurs variables par nom (`h_0`, `qp0`, `b`, `d`…, renommées une fois en v0.120 : `qk_max_bh` → `qk_max_cf1`). Or un identifiant de source doit suivre `^[A-Za-z0-9][A-Za-z0-9_.+-]*$` : `WL-Fluchttreppe+Geräte` (le « ä ») et `EL+AL-Dach mit Wasser`, `EL+AL-Dach ohne Wasser` (les espaces) sont refusés. Dans le projet d'exemple, ce sont 2 des 8 cas.
- **Pourquoi elle compte** : garder les identifiants garde les sections intactes, mais oblige à élargir `ID_PATTERN` (trois modules, noms de fichiers `loads/<kind>/<id>.json`, Windows) ; les changer oblige à réécrire les sections et les scripts (un `loads_migrate` de plus).
- **Options** :
  - A (recommandée) — **Identifiants gardés quand ils sont valides ; sinon proposés corrigés** (`WL-Fluchttreppe+Geraete`, `EL+AL-Dach_mit_Wasser`) et les sections réécrites par le mécanisme de `loads_migrate` (renommage listé, jamais deviné) ; les variables gardent leurs noms de v0.120. Prix : un tableau de renommage pour les cas à identifiant refusé.
  - B — **Élargir `ID_PATTERN`** pour accepter espaces et lettres accentuées, tous les identifiants gardés. Prix : fichiers aux noms difficiles, le motif reste à justifier côté Typst (`<WL-…-presets>` des étiquettes).
  - C — **Tout nouveau** : l'ingénieur nomme ses cas à la création, les sections sont réécrites à la main. Prix : la plus lourde pour un projet existant ; sans objet si Q-001 = C.
- **Réponse** : A — identifiants gardés quand ils sont valides, sinon corrigés par un tableau de renommage listé, sections réécrites (ingénieur, 24.10.2026). Comme Q-001 est C, cela ne vaut que pour le projet d'exemple : `WL-Fluchttreppe+Geräte` → `WL-Fluchttreppe+Geraete`, `EL+AL-Dach mit Wasser` → `EL+AL-Dach_mit_Wasser`, `EL+AL-Dach ohne Wasser` → `EL+AL-Dach_ohne_Wasser` (trois des huit cas, non deux). Les variables gardent leurs noms de v0.120 ; `ID_PATTERN` ne change pas ; `loads_migrate` n'a pas de renommage de plus.

### Q-004 — Jusqu'où va le retrait : le code de lecture seulement, ou aussi le vocabulaire du classeur ?
- **Contexte** : le classeur est aujourd'hui dans plus que les trois lecteurs : `registry.py` (découverte des feuilles, `WORKBOOK_NAME`, arrêt si un classeur lu a disparu), `io_excel.py`, `project.record` (empreintes `workbooks` dans `data/project.json`, `tests/test_new_project.py` l. 320 teste l'arrêt), la provenance `excel:<classeur>!<feuille>!<cellule>` des variables (`variables.py`, onglet Variables « Excel », `variable_sources.py`), `ENGINES = {"excel", …}` dans `validation.py`, et le schéma de `calculations.json`. Aucun code de `calc/` ne lit une autre feuille du classeur que ces trois domaines (les charges utiles viennent du tableau 8 ; `Positions.xlsx` est un autre fichier). Les exports anciens (le `calculations.json` du projet d'exemple) portent `engine: "excel"` et `excel:…`.
- **Pourquoi elle compte** : supprimer le vocabulaire casse la lecture d'anciens exports et demande une version de schéma ; le garder laisse une provenance « Excel » que plus rien n'écrit.
- **Options** :
  - A (recommandée) — **Retirer la lecture et le mécanisme** (`open_workbooks`, `_discover`, la règle du classeur disparu, `io_excel` si plus utilisé) **et garder le vocabulaire en lecture** : `engine: "excel"` et la provenance `excel:` restent valides pour les anciens exports et les variables historiques ; `project.json` n'écrit plus `workbooks` (champ optionnel conservé au schéma). Prix : un peu de vocabulaire mort, aucune rupture.
  - B — **Tout retirer**, vocabulaire compris, schéma de `calculations.json` et de `project.json` relevés d'une version, anciens exports refusés. Prix : le plus net, mais le projet d'exemple et les anciens projets doivent être réexportés.
  - C — **Garder le mécanisme du registre** (chercher un classeur, lire des feuilles par préfixe) mais sans aucun domaine qui l'utilise, pour un futur domaine. Prix : du code sans usage, contraire à la règle de ne pas laisser de copie qui vieillit.
- **Réponse** : B — tout retirer, vocabulaire compris (ingénieur, 24.10.2026) : `engine: "excel"`, la provenance `excel:`, les champs `workbook`, `sheet` et `sheet_prefix`, le champ `workbooks` de `project.json` ; les schémas de `calculations.json` (1.8 → 1.9) et de `project.json` (1.0 → 1.1) relevés d'une version, les anciens exports refusés. Conséquences relevées au §13 et à confirmer en C-1 (où le refus vit) et C-5.

### Q-005 — Que devient le projet d'exemple ?
- **Contexte** : `tests/projet-exemple/` n'a pas de classeur ni de source de charges, mais son `calculations.json` contient 8 cas venus d'un ancien classeur (4 charges permanentes, 1 neige `SL`, 3 vents) cités par 8 sections (`Permanent-loads/EL+AL-*.typ`, `Variable-loads/Snow/SL.typ`, `Variable-loads/Wind/WL-*.typ`, avec leurs `unfold.json`) et par le rapport. Tout le jeu de tests travaille sur sa copie et les figures de `Permanent-loads/Exports/Figures/` en sont tirées. Sans ces cas, un nouvel export du projet d'exemple les perdrait.
- **Pourquoi elle compte** : l'exemple est la preuve que « un clone du code se teste lui-même » ; ses captures (`examples/out/`) et ses figures en dépendent.
- **Options** :
  - A (recommandée) — **Convertir les 8 cas en sources Woodcore** (`000-Woodcore/sources/loads/{wind,snow,dead}/`), mêmes identifiants autant que Q-003 le permet, sections gardées, export régénéré ; les valeurs sont celles du `calculations.json` actuel (le test de conversion de ARCH-002 les compare). Prix : un travail d'une demi-journée, et des figures régénérées.
  - B — **Retirer les 8 cas, leurs sections et leurs `unfold.json`** de l'exemple ; le rapport d'exemple n'a plus de charges de vent, de neige ou permanentes. Prix : on perd la démonstration des trois domaines.
  - C — Garder `calculations.json` tel quel, figé, sans source. Prix : l'exemple ment (un export le viderait), à refuser.
- **Réponse** : A — convertir les 8 cas en sources Woodcore, une fois, à la main (ingénieur, 24.10.2026) : mêmes valeurs, identifiants corrigés selon Q-003, sections réécrites, export et figures régénérés. « À la main » : un script jeté (scratchpad, non commité), le code des onglets pour écrire les sections ; la comparaison à l'ancien export est la preuve (§14, étape 1).

### Q-006 — Que devient le fichier Excel lui-même ?
- **Contexte** : le classeur « Belastungsannahmen » du bureau est un fichier de l'ingénieur dans le dossier de son projet ; il contient aussi les bibliothèques (matériaux, `Dropdowns`) déjà extraites dans `calc/libraries/` par #110. À la migration de `Positionen.xlsx` (v0.114), Woodcore l'a déplacé dans les archives du projet. Les gabarits de nouveau projet (`project_template.py`) et le tutoriel (`04-loads.md`) parlent du classeur.
- **Pourquoi elle compte** : Woodcore n'écrit jamais dans les fichiers de l'ingénieur sans sa demande ; déplacer ou ignorer le classeur change ce qu'il retrouve dans son dossier et ce que dit le tutoriel.
- **Options** :
  - A (recommandée) — **Laissé en place, jamais touché, plus ouvert** (sauf, selon Q-001/Q-002, par l'import ou la liste des noms) ; le tutoriel et le gabarit n'en parlent plus. Prix : le fichier reste un doublon inerte dans le dossier.
  - B — **Déplacé dans les archives** à la conversion (Q-001 A ou B), comme `Positionen.xlsx`. Prix : une écriture sur son fichier, qu'il n'a pas demandée si la conversion est automatique.
  - C — **Reconnu et signalé** à chaque export comme « classeur de charges ignoré ». Prix : bruit permanent.
- **Réponse** : résolue par Q-001 C et Q-002 B (ingénieur, 24.10.2026) : le fichier reste en place, jamais touché ni ouvert ; seul le message générique de Q-002 le signale. Le tutoriel et le gabarit n'en parlent plus.

### À confirmer à l'approbation

Des conséquences des réponses que l'ingénieur n'a pas eu à trancher et que la revue (§13) a relevées. Chacune a une proposition ; sans mot contraire à l'approbation, le plan (§14) la suit.

- **C-1 — Ce que « anciens exports refusés » veut dire pour un projet réel.** Tout projet exporté par Woodcore v0.120 à v0.125 porte un `data/calculations.json` en **1.8** et un `data/project.json` en **1.0** : après la mise à jour, ils sont tous des « anciens exports ». Un export qui lirait sa propre ancienne version pour la refuser se bloquerait lui-même ; or l'export réécrit ces fichiers à neuf et ne les lit que par `engine.previous_json`, sans les valider (`registry.py:272,299`, `export_all.py:311`). Proposition : **le refus vit là où l'export est lu** — le schéma (l'énumération de `schema_version` ne contient que « 1.9 » : l'onglet Variables, `variable_sources.read_export`, dit `bad_file` en nommant le champ), le compilateur Typst (`load-calculations`, `lib/calc-engine-core.typ:175`, une garde comme `load-quantities` de `lib/positions.typ:129` : « data/calculations.json est en 1.8 -- lancer Import données ») et `woodcore-cli check` — et **jamais l'export lui-même**, qui est le remède. Prix : le premier rapport de chaque projet réel ne compile plus tant que l'ingénieur n'a pas cliqué « Import données » une fois ; la page « Nouveautés » le dit en tête. Une réexportation automatique à l'ouverture serait une écriture sans demande : non retenue.
- **C-2 — Le message de Q-002 B est permanent.** Tant que le fichier `*Belastungsannahmen*` est dans le dossier, chaque export complet l'avertit (les enregistrements de cas dans les onglets, non : `registry.export` ne l'émet pas). Aucun réglage ne le fait taire, sauf déplacer ou renommer le fichier hors du motif — ce que Q-006 C (« bruit permanent ») avait écarté. Proposition : tel que répondu, avec le nom du fichier dans la phrase.
- **C-3 — `loads_migrate.py` et `loads_names.py` restent.** La migration des noms de v0.120 (`q_k11` → `q_k1`, `qk_max_bh` → `qk_max_cf1`) lit l'ancien export, pas un classeur : elle n'est pas du « classeur ». Seul son vocabulaire de cellules de feuille (`SNOW_COMPARED`, les colonnes de `WIND_AREAS`, `wind_compared`) part ; `roof_of` y migre. Sa retraite est une autre décision, plus tard.
- **C-4 — Règles de conception 5 et 6 et `CLAUDE.md`.** Les règles 5 (« provenance Excel / Python / Typst ») et 6 (« un cas est une feuille Excel ») de `docs/architecture/principles.md` et son paragraphe « Excel as the primary source » sont contredits par D-33 : le plan les réécrit (revue ARCH-RISK-001). La première ligne de `CLAUDE.md` (« from Excel, Python and Typst ») n'est pas touchée sans son mot : les positions viennent encore, à l'import, d'un classeur.
- **C-5 — `project.json` perd aussi l'empreinte de `Positionen.xlsx`.** Le champ `workbooks` regroupe l'empreinte du classeur des positions (`project.record`, l.845) et celle des classeurs de charges ; le retirer retire les deux. Les positions sont à Woodcore depuis v0.114 (le classeur est archivé à la migration), donc la perte est nulle pour un projet migré.
- **C-6 — Les quatre charges permanentes de l'exemple.** « Mêmes valeurs » dépend du poids de chaque matériau dans la bibliothèque (`calc/libraries/`, origine `belastungsannahmen`, #110) : `Dachbegrünung (Bienenweide) (voll Nass / trocken)`, `PUR / PIR Dämmung`, `Kerto-Q`, `Fi/Ta`, `Blech Aluminium 2mm`, `3-Schichtplatte`. Un poids différent ne se « corrige » pas : la couche devient un matériau du projet ou une charge directe, à poids identique, et le §16 le dit.

## 11. Critères d'acceptation

- [x] REQ-001 — un classeur à feuilles `WL/SL/EL+AL` et sans source donne un export sans instance venue d'une feuille ; un classeur illisible n'arrête ni l'export ni l'enregistrement d'un cas dans un onglet
- [x] REQ-002 — plus d'occurrence de `open_workbooks`, `reads_sheets`, `registry_no_sheet`, `io_excel`, `SHEET_PREFIX`, `sheet_prefix`, `engine: "excel"`, `excel:`, `model.EXCEL` ; projet sans classeur ni source exporté, domaines vides dits
- [x] REQ-003 — un fichier `*Belastungsannahmen*.xlsm|xlsx` donne une `Note` `load_workbook_not_read` à l'export, jamais ouvert, fichier de verrou `~$` ignoré, fichier intact ; trois phrases (fr/de/en)
- [x] REQ-004 — l'exemple a ses 8 sources (5 identifiants gardés, 3 corrigés), mêmes noms et mêmes valeurs que l'ancien export (comparaison jetée, sortie au §16), sections écrites par le code des onglets, export complet, tout identifiant cité existe
- [x] REQ-005 — tests de classeur retirés ou récrits, catalogue de tests à jour, suite complète verte
- [x] REQ-006 — 12 catégories `live-load` présentes sans classeur ; `positions_workbook.py` intact, `build_reference.py` changé de sa seule colonne `workbook` et de son `source_type` « sheet »
- [x] REQ-007 — `calculations.json` 1.9 et `project.json` 1.1 ; un export 1.8 refusé par le schéma (onglet Variables, `bad_file`), par le compilateur Typst et par `woodcore-cli check`, avec le remède dit ; l'export qui le remplace n'est pas arrêté par lui
- [x] UI-001 — message de REQ-003 en fr/de/en, `tests/test_i18n.py` et `tests/test_domain_contracts.py` passent
- [x] UI-002 — `docs/domain/loads.md` §3.3bis, §3.3ter, §3.3quater, §3.3sexies-bis, `calculation-domains.md` §3.3, `layout.md`, `principles.md` (règles 5 et 6), décision, tutoriel, CHANGELOG, « Nouveautés » fr/de/en
- [x] UI-003 — l'onglet Variables sans « Excel », sans « Ouvrir le classeur » ; plus de bandeau `stale` ; un état de vue enregistré avec `excel` se restaure sans erreur
- [x] ARCH-001 — aucun import de `domains.wind` / `domains.snow` ; `validation.py` sans contrôle `SHEET_PREFIX` ; `LABEL`/`ACTION`/`ENGINE` lus sur les modules de source
- [x] ARCH-002 — la conversion de l'exemple n'ajoute aucun code au dépôt ; sa comparaison à l'ancien export est au §16
- [x] ARCH-003 — étapes touchant `dead_load*.py` après le commit de #111 (tenu : be5b85f)
- [x] ARCH-004 — règles 5 et 6, paragraphe « Excel as the primary source » et schéma de `principles.md` §2 réécrits ; décisions listées au §13 marquées `superseded`
- [x] ARCH-005 — `loads_migrate.py` et `test_loads_migrate.py` inchangés et verts ; `loads_names.py` sans cellule de feuille
- [x] ARCH-006 — plus aucun texte du produit qui dise de copier le classeur dans le dossier
- [x] Documentation : sections de `docs/` mises à jour, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en.
- [x] Tests : fichiers `tests/test_*.py` ajoutés ou étendus, et passent ; `python tests/run_tests.py` complet à la fin.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §7 D-33, REQ-001 | décision, capturé |
| T2 | REQ-001, ARCH-001 | capturé |
| T3 | Q-001 à Q-006 (§10) | contrainte de méthode, tenue |
| T4 | REQ-001, REQ-002, ARCH-001 | capturé |
| T5 | REQ-002, REQ-003 | capturé |
| T6 | REQ-003, §7 D-02 | résolu : Q-001 C, rien ne se convertit, un message |
| T7 | REQ-004, §7 D-06 | résolu : Q-005 A |
| T8 | REQ-005 | capturé |
| T9 | UI-002, ARCH-004 | capturé |
| T10 | REQ-006, D-01 | résolu par le code |
| T11 | REQ-003, §7 D-02 | résolu : Q-001 C |
| T12 | REQ-003, UI-001, §7 D-03 | résolu : Q-002 B |
| T13 | CON-002, CON-003, §7 D-04 | résolu : Q-003 A (l'exemple seul) |
| T14 | REQ-002, REQ-006, REQ-007, §7 D-05 | résolu : Q-004 B |
| T15 | §7 | fait |
| revue | REQ-007, UI-003, ARCH-004, ARCH-005, ARCH-006 | exigences nées de la revue (§13) |

### Points de la source non résolus

Aucun : les six questions ont leur réponse (§10). Restent six points **à confirmer à l'approbation** (C-1 à C-6, fin du §10), des conséquences des réponses que l'ingénieur n'a pas eu à trancher.

## 13. Revue d'architecture

Revue faite par moi-même, contre le code de `master` (be5b85f, #111 commité) et `docs/`, en lisant `.claude/skills/architecture-review/SKILL.md` et `.claude/agents/architecture-reviewer.md`. #114, #113, #112 et #115 passent avant #109 dans l'ordre de l'ingénieur : leurs fichiers (surtout `calc/tools/variables_tab.py`, que #114 remplace) sont **à relire avant l'étape 5**.

### Verdict

**APPROUVER AVEC RÉSERVES.** Le retrait est faisable sans toucher à l'architecture des sources (D-04) : les trois domaines ont déjà leur module de source, leur dossier et leur calcul ; ce qui part est un second chemin d'entrée. Une réserve bloquante (ARCH-RISK-001 : les règles de conception 5 et 6 changent, `principles.md` doit changer avec elles) et cinq importantes (002 à 006), que le plan §14 traite une à une ; trois mineures. Rien n'oblige à revoir la spec avant l'approbation, mais l'ingénieur doit lire C-1 (§10) : tout projet réel exporté par v0.120 à v0.125 devient, par « anciens exports refusés », un projet dont le rapport ne compile plus avant un clic sur « Import données ».

### Modules concernés (constat du code)

- `calc/registry.py` (302 l.) : `WORKBOOK_NAME`/`WORKBOOK_SUFFIXES` l.25–26, `reads_sheets` l.70, `is_load_workbook` l.75, `open_workbooks` l.81 (l'arrêt si un classeur lu a disparu), `_discover` l.100 (la `Note` `registry_no_sheet` l.138), `build_calculations(workbooks, here, …)` l.145 (branche des feuilles l.155–173, `"sheet_prefix"` l.182, id d'une feuille et d'une source refusé l.164), `export(here)` l.286 (`open_workbooks` l.294, appelé à chaque enregistrement d'un cas par `source_store`). Constantes de version l.35–41 : `SCHEMA_VERSION` 1.5 (lu par `_follow_loads` l.248), `LINKED_SCHEMA_VERSION` et `ROOTED_SCHEMA_VERSION` jamais lus, `rooted` l.186 calculé et jamais lu.
- `calc/export_all.py` : import l.36, `_workbooks_read_before` l.107, bloc l.182–192, `build_calculations(workbooks, …)` l.198, `project.record(here, [cells.path …])` l.297, `seed` : `build_calculations([])` l.420, `refresh_project_info` l.390.
- `calc/io_excel.py` (196 l.) : seul appelant `registry` (et `tests/test_dead_load.py`, `test_dead_load_source.py`, `test_load_sheets.py`), plus `calc/tools/woodcore_start.py:49` qui le charge à l'avance. Supprimé ; seul survit le test du nom de `find_workbooks` l.180, **règle des fichiers de verrou `~$` comprise**, déplacé dans `registry` (`load_workbook_names`).
- `calc/domains/wind.py` (123 l.), `snow.py` (121 l.) : supprimés. Ils sont aussi les modules que `registry.DOMAIN_MODULES` interroge pour `LABEL`, `ACTION`, `ENGINE` (wind.py:20–23) que `snow_source.py` et `wind_source.py` ne déclarent pas ; `tests/test_sia260.py:419` lit les mêmes constantes sur `live_load` ; `loads_names.py:76` appelle `snow.roof_of`.
- `calc/domains/dead_load.py` (389 l.) : part tout ce qui lit une feuille — `SHEET_PREFIX` l.27, `MATERIAL_*`, `LAYER_COLUMNS`, `CHOSEN_*`, `WEIGHT_COLUMN` l.35–59, `MaterialLibrary` l.68, `read_materials` l.109, `_number` l.127, `_check_weight_formula` l.136, `_read_layers` l.164, `_check_chosen` l.287, `read_instance` l.307, `read_instances` l.385 ; reste ce que #111 lit — `DOMAIN`/`LABEL`/`ENGINE`/`ACTION`, `DIRECT_LOAD` (`dead_load_messages.py:50,55`), `KINDS` (`dead_load_source.py:39`), `CHOSEN_TOLERANCE` (`dead_load_messages.py:97`), `KG_TO_KN`, `KIND_SYMBOLS`, `_weight_text`, `_layer_table`, `instance_from_layers` l.326 (`dead_load_source.py:347`). `live_load.py:25` : `SHEET_PREFIX = None`.
- `calc/domains/_common.py` : `require_one_of` l.47, `sheet_differences` l.59, `SHEET_TOLERANCE` l.55, sans appelant une fois snow.py et wind.py partis. `snow_source.build_instance(…, inputs=)` l.312 et `wind_source.build_instance` : le paramètre `inputs` (la provenance « excel:<cellule> ») perd son seul appelant.
- `calc/domains/loads_names.py` (98 l.) : `SNOW_COMPARED`, `WIND_AREAS` (colonnes), `wind_compared` sont du vocabulaire de cellules de feuille ; `snow_renamed`, `wind_renamed`, `renamed`, `wind_table_of` sont la migration de v0.120, qui lit l'ancien export. `calc/domains/loads_migrate.py` (294 l.) : ne lit aucun classeur.
- `calc/validation.py` : `ENGINES = {"excel", "python", "norm"}` l.25, contrôle `sheet_prefix`/`workbook`/`sheet` l.367–410. `schemas/calculations.schema.json` : `sheet_prefix` requis par domaine, `workbook`, `sheet`, énumération 1.4 à 1.8, descriptions. `calc/project.py:839–856` `record` et `schemas/project.schema.json` (`workbooks` requis, `schema_version` const « 1.0 »). `calc/build_reference.py:490,583,658` (`source_type` « sheet », colonne `workbook`).
- Provenance et fenêtre : `calc/variables.py:119–145` (`EXCEL`, `parse_source`, `provenance_of`), `calc/variable_sources.py:57–72,92–108,228` (`Domain.workbook`, `.sheet`, `instance_workbook`), `calc/tools/variables_tab.py` (46 mentions : `vr_prov_excel`, `vr_open_workbook`, `open_workbook()`, filtre l.769, fiche l.1025–1078 — **ou son remplaçant après #114**), `calc/tools/woodcore_gui_menus.py:50` `stale_workbooks` et l.209 `stale_text` (+ le mot `stale` ×3), `calc/tools/woodcore_gui_words.py` (`warn_registry_no_sheet`, `warn_sheet_value_differs`, `warn_sheet_slope_empty`, `warn_sheet_direction_unknown`, `reexport_what` « Excel et les dessins… », trois langues chacun).
- Typst : `lib/calc-engine-core.typ:175` `load-calculations()` (4 usages), qui ne lit pas `schema_version`.
- Textes : `calc/cli.py:205`, `calc/project_template.py`, `templates/**/004-einwirkungen.typ` ×4, tutoriel ×3 langues, `download.md` ×3, `README.md`.
- Le projet d'exemple : `000-Woodcore/data/calculations.json` (1.8, 8 instances de « Belastungsannahmen.xlsm »), `Permanent-loads/` (4 sections), `Variable-loads/Snow/SL.typ`, `Variable-loads/Wind/` (3), leurs `unfold.json`, `domain-files.json`, `domain-state.json`, `formulas.json`, `300-Statical report/Sections/004-einwirkungen.typ` (l.15, 17, 19, 29, 35, 39, 43) ; **aucune source `loads/`**.

### Code à réutiliser

- `engine.Note(code, text, **args)` et la clé `warn_<code>` de `woodcore_gui_words.py` : le message est une `Note`, donnée **dans `registry.py`** — `tests/test_domain_contracts.py:171–190` ne lit que `calc/domains/*.py` et `registry.py` pour exiger les trois phrases de chaque code.
- La garde de `load-quantities` (`lib/positions.typ:129`, `panic(… "-- export again")`) pour `load-calculations`.
- La validation à la lecture de `variable_sources.read_export` (l.144–164) : `validate_structure` y arrête déjà « un export à la mauvaise version, en nommant les deux » (`validation.py:85–93`) ; l'erreur `bad_file` existe avec son mot.
- `refresh_project_info` (`export_all.py:390`) traite déjà un `project.json` invalide en le reconstruisant : le passage à 1.1 n'y casse rien.
- `domain-file` (`lib/calc-engine-core.typ:373`) s'arrête déjà, en nommant l'id et les ids connus, sur une section qui cite un cas disparu : c'est le second signal que verra l'ingénieur à la compilation.
- Les modules de source et le code des onglets (`source_store`, `unfold`) pour écrire l'exemple : rien à inventer.

### Risques

**ARCH-RISK-001 — bloquant — D-33 contredit des règles de conception et des décisions « in force ».** `docs/architecture/principles.md` : le schéma de §2 (l.12–16, « Excel (input data -- primary source) … every load, one sheet per case »), le paragraphe « Excel as the primary source » (l.63), la règle 5 (« Systematic provenance (Excel / Python / Typst direct) ») et la règle 6 (« A load is a calculation domain, its cases are Excel sheets »). Dans `docs/decisions-index.md`, encore « in force » : « A load is a domain whose instances are Excel sheets (v0.18) » (l.474), « A load workbook's snow and wind sheets give their inputs… (v0.120) » (l.517), « The norm's values for snow and wind come from calc/norms/ on both paths… » (l.519), « A new project carries no load workbook (v0.83) » (l.542), « No load workbook is a warning while no export has read one (v0.89.1) » (l.543), « The load workbooks are found by name (v0.26) » (l.557), « Woodcore reads the export, not the workbooks (v0.28) » (l.560), « Neither Excel carries loads (v0.18) » (l.567), « Two non-overlapping Excel workbooks (v0.10) » (l.568). *Correction* : une décision `docs/decisions.md` §13 porte D-33 et ses prix, marque ces neuf `superseded`, et le plan réécrit les quatre endroits de `principles.md` (étape 8). CLAUDE.md dit « Preserve the architecture unless there is a stated, justified reason » : la raison est l'ingénieur, 24.10.2026 (T1) ; le coût est que la provenance d'une variable ne connaît plus que `python:`, `norm:`, `entered:`, `woodcore:`.

**ARCH-RISK-002 — important — « anciens exports refusés » n'a de dents que là où l'export est lu, et se retournerait contre l'export.** Toute v0.120 à v0.125 écrit 1.8 : tous les projets réels seraient « anciens ». L'export lui-même ne valide jamais l'ancien fichier (`engine.previous_json` est tolérant, `registry.py:272,299`, `export_all.py:311`) ; **le refus ne doit pas y être mis**. Le compilateur Typst, lui, ne lit `schema_version` nulle part (`validation.py:85` : « reached Typst, which reads the field nowhere at all ») : sans garde, un ancien export compile en silence, avec ses cas `excel`. *Correction* : REQ-007 et C-1 — énumération du schéma à « 1.9 » (l'onglet Variables, `bad_file`), garde Typst dans `load-calculations` à la manière de `load-quantities`, `woodcore-cli check` ; l'export, jamais. Le message dit le remède (« Import données »). Les lecteurs de `calculations.json` qui ne valident pas (`unfold`, `formula_domain.py:1270`, `script_runner.py:59`, `object_panes_context.py:213`, `source_store.py:110`, `typst_sync.py:168`, `links`) lisent l'ancien fichier jusqu'au prochain export : tolérés, parce que leurs appels viennent après un export ou ne montrent que ce qu'il contient (étape 4, test).

**ARCH-RISK-003 — important — supprimer `snow.py` et `wind.py` casse sans bruit ce qui les prenait pour modèle.** (a) `registry.DOMAIN_MODULES` lit `LABEL`/`ACTION`/`ENGINE` dessus ; `snow_source` et `wind_source` ne les déclarent pas : à y mettre avant de supprimer (ARCH-001). (b) `tests/test_line_levels.py:46` liste `"snow"` et `"wind"` comme fichiers de `calc/domains/` à lire (l.55) : `FileNotFoundError`. (c) `calc/tools/woodcore_start.py:49` charge `io_excel` à l'avance dans le fil de démarrage : à retirer sous peine d'un `ImportError` au démarrage de la fenêtre. (d) `loads_names.renamed` importe `snow.roof_of` : `ROOF_OF` et `roof_of` migrent dans `loads_names.py`. (e) `tests/test_sia260.py:417–421` construit un `calculations` en 1.4 avec `sheet_prefix`. (f) `tests/test_domain_contracts.py:188` exige les codes `registry_no_sheet`, `sheet_value_differs`. *Correction* : l'étape 2 est faite d'un seul tenant (une suite rouge entre ses fichiers est attendue) et suivie des tests qui nomment ces fichiers.

**ARCH-RISK-004 — important — la conversion de l'exemple peut changer ce que quarante tests lisent.** Plus de quarante appels de test et de fiches compilent contre `("snow-load", "SL")` (`test_fine_display`, `test_formula`, `test_commands`, `test_display*`, `test_command_review`, …) : leurs noms de variables (`ce`, `dachform`, `korrektur`, `h_0`, `q_k1`) et leurs libellés viennent de l'export committé, qui est un export **ancien** (1.8, `data/` non régénéré depuis un classeur). Une source reconstruite à la main qui diffère d'un pas (un `ce` libre, une pente, un `abgleiten`) change ces tests sans bruit. Les sections de l'exemple sont des fichiers *dépliés* gardés par des empreintes (`unfold.json` : `gen.form`, `lines`) : les réécrire à la main fait de chaque ligne une ligne « à soi ». Pour les charges permanentes, « mêmes valeurs » dépend du poids de chaque matériau dans la bibliothèque (C-6). *Correction* : l'étape 1 se fait **avant** tout retrait, le code ancien tenant encore, avec la comparaison nom par nom et valeur par valeur de ARCH-002 (un écart arrête, ne se corrige pas), les sections écrites par `unfold`, et la suite complète lancée avant de passer à l'étape 2.

**ARCH-RISK-005 — important — la fenêtre garde le classeur en trois endroits que #114 aura déplacés.** La provenance « Excel » (`variables.EXCEL`, `parse_source`, `variable_sources.provenance_of`, filtre, colonne, fiche « Vient de » de #114), le bouton « Ouvrir le classeur » (`variables_tab.py:586–1078`, `Domain.workbook` et `.sheet`), le bandeau `stale` (`woodcore_gui_menus.py:50,209`). L'état de vue d'un ingénieur peut avoir enregistré `provenance = excel` : `restore` ne doit pas lever (la spec de #114 prévoit déjà qu'un état d'avant se restaure sans largeurs). Après le retrait, une `source` « excel:… » d'un fichier non écrit par Woodcore se lit `UNKNOWN`. *Correction* : UI-003, étape 5 : relire l'onglet tel que #114 l'a laissé, retirer par `grep` (`EXCEL`, `excel`, `workbook`, `sheet`, `vr_prov_excel`, `vr_open_workbook`, « classeur »), un test de restauration.

**ARCH-RISK-006 — important — le message générique est permanent et peut mentir.** Tel que répondu (Q-002 B), il est donné à chaque export complet tant que le fichier est dans le dossier (C-2) ; un fichier de verrou `~$02_Belastungsannahmen.xlsm` que l'ouverture dans Excel laisse a le même nom : sans la règle de `find_workbooks` il donnerait un faux avertissement. Les enregistrements de cas dans les onglets passent par `registry.export`, qui ne doit pas l'émettre (bruit à chaque clic). Le fichier est trouvé par son nom seul — un `.xlsx` qui n'est pas un classeur de charges, mais dont le nom contient « Belastungsannahmen », est aussi signalé : c'est la règle de v0.26, gardée. *Correction* : REQ-003 (motif unique dans `registry.py`, règle de verrou, sous-dossiers exclus, test sur un fichier aux octets illisibles) ; message dans `export_all` seulement ; C-2 demande à l'ingénieur de le confirmer.

**ARCH-RISK-007 — mineur — du code et des mots que le retrait laisse mourir.** `inputs=` de `snow_source.build_instance` / `wind_source.build_instance`, `entered(field)` ; `ROOTED_SCHEMA_VERSION`, `LINKED_SCHEMA_VERSION`, `rooted` de `registry.py` ; `SHEET_TOLERANCE`, `require_one_of`, `sheet_differences` de `_common.py` ; les mots `warn_sheet_*` ; les docstrings de `dead_load.py`, `registry.py`, `export_all.py` qui disent « sheet ». *Correction* : étape 2, 3 et 4, relevés par `grep` en fin d'étape (principe 3).

**ARCH-RISK-008 — mineur — la spec disait deux choses fausses.** REQ-006 écrivait que `build_reference.py` n'est pas modifié alors qu'il lit `workbook` (l.583) et `source_type` « sheet » (l.490) ; Q-003 comptait 2 des 8 cas à identifiant refusé, ils sont 3. *Corrigé* dans REQ-006 et CON-002.

**ARCH-RISK-009 — mineur — `loads_migrate` est la seule chose qui lit un ancien export, et ne doit pas être refusé avec lui.** Il lit `data/calculations.json` par `engine.previous_json` sans validation, au moment d'ouvrir le projet, avant tout export ; l'énumération du schéma n'y change rien. C-3 : il reste. Son test ne construit pas de classeur.

**ARCH-RISK-010 — mineur — les contrats.** `calculations.json` 1.9 retire des champs, ce qui n'est pas additif : le relèvement est obligatoire (principe 8) et c'est ce que Q-004 B demande ; l'export reste reproductible octet pour octet (`tests/test_export.py::test_the_export_is_reproducible` lit le classeur de l'ingénieur et saute sans lui ; à reprendre sur l'exemple). `project.json` 1.1 retire `workbooks` (aussi l'empreinte de `Positionen.xlsx`, C-5). Aucune commande Typst n'est ajoutée ni retirée : pas de `///` ni de `commands.json`.

### Approche recommandée

1. **L'exemple d'abord**, avec le code ancien en place (il n'a pas de classeur : son export ne lit que des sources) : huit sources, sections par `unfold`, comparaison à l'ancien export, suite complète verte.
2. **Un seul tenant pour le registre** : les modules de source portent `LABEL`/`ACTION`/`ENGINE`, `registry` n'a plus de classeur, `snow.py`, `wind.py`, `io_excel.py`, le lecteur de `dead_load.py` et les aides de `_common.py` sont supprimés.
3. **Le message**, une `Note` de `registry.py` dont le seul savoir est le motif du nom du fichier (règle de verrou comprise), émise par `export_all` ; mots dans les trois langues.
4. **Les schémas et le refus**, au lieu où l'export est lu : énumération, garde Typst, `check` ; jamais dans l'export.
5. **La fenêtre et les textes**, après avoir relu l'état laissé par #114.
6. **La documentation, dont les règles de conception**, avant la suite complète.

### Tests à ajouter ou étendre

- `tests/test_export.py` (étendre) : classeur aux octets illisibles sans source ; verrou `~$` ; deux fichiers ; fichier intact ; `registry.export` ne dit rien ; chaque cas cité par une section de l'exemple existe ; un `calculations.json` en 1.8 posé dans la copie de l'exemple : l'export le réécrit en 1.9 ; `test_the_export_is_reproducible` repris sur l'exemple.
- `tests/test_domain_contracts.py` (étendre) : codes de `Note` (`load_workbook_not_read` ajouté, `registry_no_sheet` et `sheet_*` retirés), trois phrases chacun.
- `tests/test_new_project.py` (récrire l.302–327) : plus d'arrêt sur un classeur disparu, plus la ligne « no load workbook » ; `tests/test_project.py` (l.281, 556–563) : `record` sans `workbooks`, `project.json` 1.0 reconstruit.
- `tests/test_variable_sources.py` (l.46–63) et `tests/test_variables.py` (l.620–682, ou ce que #114 en aura fait) : plus de `excel:` ; un état de vue portant `excel` se restaure ; `read_export` d'un 1.8 rend `bad_file` nommant `schema_version`.
- `tests/test_report.py` ou `tests/test_export.py` : la compilation d'une section sur un ancien `calculations.json` s'arrête avec la phrase.
- `tests/test_sia260.py` (l.417), `tests/test_line_levels.py` (l.46) : mis à jour.
- Supprimés : `tests/test_load_sheets.py`, `tests/fixtures/load-sheets-reference.json`, `tests/fixtures/workbook.py` (si plus aucun appelant), les tests de feuille de `test_dead_load.py` et `test_dead_load_source.py`, `test_window.py` l.145–161.
- À relancer inchangés : `test_loads_migrate.py`, `test_snow_source.py`, `test_wind_source.py`, `test_links.py`, `test_i18n.py`, `test_docs_coherence.py`, `test_harness.py`.

### Exigences nées de la revue

REQ-007 (schémas et refus), UI-003 (la fenêtre), ARCH-004 (règles et décisions), ARCH-005 (`loads_migrate`), ARCH-006 (textes du produit), et la correction de REQ-006 et CON-002.

## 14. Plan d'implémentation

Dix étapes, dans cet ordre ; chaque étape finit par ses tests, la suite complète est lancée à l'étape 1 et à la fin (en tâche de fond, `python tests/run_tests.py`). Le journal §16 est tenu à jour à chaque étape (reprise possible). Les risques sont notés entre crochets.

| # | Étape | Fichiers | Exigences | Preuve |
|---|---|---|---|---|
| 0 | **Avant de toucher** : `git status` et `git log` (qui a changé depuis be5b85f : #114, #113, #112, #115), lire `calc/tools/variables_tab*.py` / `variables_words.py` tels qu'ils sont, coordonner par SendMessage si un fichier de l'étape est modifié par une autre session ; suite complète une fois pour la base. | aucun | ARCH-003 | liste des rouges d'avant, au §16 |
| 1 | **L'exemple d'abord, le code ancien en place** [R-004, C-6]. (a) Script jeté (scratchpad, non commité) : à partir de l'ancien `000-Woodcore/data/calculations.json`, écrire par `check_source` / `stamp_version` les 8 sources `000-Woodcore/sources/loads/wind/{WL-Velo,WL-Fluchttreppe+Geraete,WL-Pavillon}.json`, `snow/SL.json`, `dead/{EL+AL-Dach_mit_Wasser,EL+AL-Dach_ohne_Wasser,EL+AL-DachRand,EL+AL-Wand}.json` ; couches de la bibliothèque `materials` au même poids, sinon matériau du projet ou charge directe. (b) Comparer `build_instance(source)` à l'ancienne instance : noms, valeurs (1e-9), `results` ; l'écart arrête. (c) Sections par le code des onglets (`source_store.write`, puis `unfold.unfold_domains`) ; retirer les 8 anciens `.typ` et leurs lignes d'`unfold.json` ; suivre les citations de `300-Statical report/Sections/004-einwirkungen.typ` (l.15, 17, 19, 39). (d) Export complet de l'exemple ; relire le `git diff` de `data/`. | `tests/projet-exemple/000-Woodcore/sources/loads/**`, `Permanent-loads/`, `Variable-loads/{Snow,Wind}/`, `300-Statical report/Sections/004-einwirkungen.typ`, `000-Woodcore/data/*` | REQ-004, ARCH-002, CON-004, CON-006 | la sortie de la comparaison au §16 ; `python tests/run_tests.py` complet vert ; test « chaque cas cité existe » (`tests/test_export.py`) |
| 2 | **Le registre sans classeur, d'un seul tenant** [R-003, R-007]. `snow_source.py`, `wind_source.py` : `LABEL`, `ACTION`, `ENGINE` ; retirer `inputs=` ; `registry.py` : plus de classeur (`build_calculations(here=None, files=None, notes=None)`, `export(here)`), `DOMAIN_MODULES` lit les modules de source, retirer `rooted` et les versions mortes ; supprimer `domains/wind.py`, `domains/snow.py`, `io_excel.py` ; `dead_load.py` : lecteurs retirés, docstring réécrite (`instance_from_layers` reste) ; `live_load.py` : sans `SHEET_PREFIX` ; `_common.py` : sans `require_one_of`, `sheet_differences`, `SHEET_TOLERANCE` ; `loads_names.py` : sans cellules de feuille, `roof_of` / `ROOF_OF` rapatriés ; `woodcore_start.py:49` ; `tests/test_line_levels.py:46`, `tests/test_sia260.py`. | `calc/registry.py`, `calc/domains/{snow_source,wind_source,dead_load,live_load,_common,loads_names}.py`, `calc/tools/woodcore_start.py`, `tests/test_line_levels.py`, `tests/test_sia260.py` | REQ-001, REQ-002, ARCH-001, ARCH-005 | `python tests/run_tests.py -k snow_source`, `-k wind_source`, `-k dead_load_source`, `-k links`, `-k line_levels`, `-k sia260`, `-k loads_migrate`, `-k harness` ; `grep` de REQ-002 sur `calc/` |
| 3 | **L'export et le message** [R-006]. `registry.load_workbook_names(folder)` (nom contenant `Belastungsannahmen`, `.xlsm`/`.xlsx`, sans casse, sans sous-dossier, sans `~$`) et la `Note` `load_workbook_not_read` ; `export_all.py` : plus d'`open_workbooks`, de `_workbooks_read_before`, de ligne « no load workbook », la note émise ici seulement (pas par `registry.export`), `seed` ; mots `warn_load_workbook_not_read` ×3, `warn_registry_no_sheet` et `warn_sheet_*` retirés, `reexport_what` sans « Excel » ; `cli.py` (docstring de `check`, message de `new`). | `calc/registry.py`, `calc/export_all.py`, `calc/tools/woodcore_gui_words.py`, `calc/cli.py` | REQ-003, UI-001, ARCH-006 (cli) | `tests/test_export.py` (classeur aux octets illisibles, verrou, deux fichiers, fichier intact), `tests/test_domain_contracts.py`, `tests/test_i18n.py`, `tests/test_new_project.py` récrit |
| 4 | **Les schémas et le refus** [R-002, R-010]. `validation.py` (`ENGINES`, l.367–410) ; `schemas/calculations.schema.json` 1.9 (énumération « 1.9 », sans `sheet_prefix` requis, `workbook`, `sheet`, descriptions) ; `registry.LEVELS_SCHEMA_VERSION` = « 1.9 » ; `project.py` `record` sans `workbooks`, `schemas/project.schema.json` 1.1 ; `variable_sources.read_export` : l'erreur de version dit « écrit par une version antérieure : lancer Import données » ; `lib/calc-engine-core.typ:175` : garde comme `load-quantities` ; `build_reference.py` (`source_type`, colonne `workbook`) ; descriptions des trois schémas de source ; les cinq `tests/` qui nomment `workbooks`/`1.8`. Régénérer l'exemple (1.9). | `calc/validation.py`, `schemas/{calculations,project,dead-load-source,snow-source,wind-source}.schema.json`, `calc/registry.py`, `calc/project.py`, `calc/variable_sources.py`, `lib/calc-engine-core.typ`, `calc/build_reference.py`, `tests/projet-exemple/000-Woodcore/data/*` | REQ-002, REQ-006, REQ-007 | `tests/test_schema_consumers.py`, `tests/test_project.py`, `tests/test_export.py` (un 1.8 posé dans la copie : `bad_file`, compilation arrêtée avec la phrase, export qui le réécrit en 1.9), `tests/test_variable_sources.py` |
| 5 | **La fenêtre sans classeur** [R-005]. Relire l'onglet Variables tel que #114 l'a laissé ; retirer `EXCEL` / `excel:` de `variables.py` et `variable_sources.py`, `Domain.workbook` et `.sheet`, la provenance « Excel », « Ouvrir le classeur », « Vient de » du classeur, les mots `vr_prov_excel`, `vr_open_workbook*`, `vr_workbook` ; `stale_workbooks`, `stale_text` et le mot `stale` ×3 ; la restauration d'un état de vue portant `excel` ne lève pas. | `calc/variables.py`, `calc/variable_sources.py`, `calc/tools/variables_tab*.py` (ou `variables_*` de #114), `calc/tools/woodcore_gui_menus.py`, `calc/tools/woodcore_gui.py`, `calc/tools/woodcore_gui_words.py` | UI-003, REQ-002 | `tests/test_variables.py`, `tests/test_variable_sources.py`, `tests/test_window.py`, `tests/test_i18n.py` ; `grep` d'`excel` / `workbook` dans `calc/tools/` (hors positions) |
| 6 | **Les textes du produit.** `calc/project_template.py`, gabarits `004-einwirkungen.typ` ×4 (commentaires), tutoriel `01-install`, `02-project`, `04-loads`, `05-window` ×3 langues, `download.md` ×3, `README.md`. | `calc/project_template.py`, `templates/**/004-einwirkungen.typ`, `website/content/{fr,de,en}/**`, `README.md` | ARCH-006, UI-002 | `tests/test_templates.py`, `tests/test_docs_coherence.py`, `grep` d'ARCH-006 |
| 7 | **Les tests de classeur et le catalogue.** Supprimer `test_load_sheets.py` + `load-sheets-reference.json` + (si plus d'appelant) `fixtures/workbook.py` ; retirer des autres fichiers les tests de feuille (`test_dead_load.py`, `test_dead_load_source.py`, `test_window.py` l.145–161, `test_export.py::test_the_export_is_reproducible` repris sur l'exemple) ; trier les mentions de `test_new_project`, `test_archive`, `test_norms`, `test_wind_source`, `test_snow_source` (la plupart ne concernent pas le classeur de charges) ; une ligne du catalogue `docs/conventions/testing-catalogue*.md` par fichier changé ou supprimé. | `tests/**`, `docs/conventions/testing-catalogue*.md`, `docs/conventions/testing.md` (l.41) | REQ-005 | `python tests/run_tests.py --related` des fichiers touchés ; `tests/test_docs_coherence.py` |
| 8 | **La documentation.** `docs/domain/loads.md` §3.3bis, §3.3ter, §3.3quater, §3.3sexies-bis (et §8) ; `docs/domain/calculation-domains.md` §3.3 (trouvés par nom, `workbook`/`sheet`/`sheet_prefix`, `engine`) ; `docs/architecture/layout.md` (snow.py, wind.py, io_excel.py, le schéma de `project.json`) ; `docs/architecture/principles.md` §2 : schéma, « Excel as the primary source », règles 5 et 6 ; `docs/architecture/data-contracts.md` (préfixes de `source`, `value`) ; `docs/ui/window.md`, `docs/ui/tab-variables.md` (tel que #114 l'a écrit), mentions de `tab-connectors`, `tab-journal`, `domain/materials`, `connections`, `journal` triées ; `docs/conventions/build-and-release.md` (l.62) ; `docs/decisions.md` §13 (D-33 et ses prix, neuf décisions marquées `superseded`) et `docs/decisions-index.md` ; `CHANGELOG.md` ; « Nouveautés » fr/de/en de la version en préparation (en tête : cliquer « Import données » une fois) ; aucune commande Typst ajoutée ou retirée : ni `///`, ni `commands.json`. | `docs/**`, `CHANGELOG.md`, `website/content/{fr,de,en}/changes/<version>.md` | UI-002, ARCH-004 | `tests/test_docs_coherence.py`, `grep -ri Belastungsannahmen docs/domain docs/architecture website/content` |
| 9 | **Suite complète, vérification indépendante, fin.** `python tests/run_tests.py` complet (en tâche de fond) ; `verify-requirements` ; `finish` (commit ; « Pousser ? » reste à l'ingénieur ; l'issue #109 close par `finish`). | — | tous | suite verte, §15 écrit par le vérificateur |

Notes du plan :

- **L'ordre tient les réserves** : l'étape 1 avant tout retrait [ARCH-RISK-004] ; l'étape 2 d'un seul tenant [ARCH-RISK-003] ; le refus dans les lecteurs et jamais dans l'export [ARCH-RISK-002] ; le motif du nom du fichier à un seul endroit, la règle de verrou gardée [ARCH-RISK-006] ; la fenêtre après #114 [ARCH-RISK-005] ; les règles de conception avec la décision [ARCH-RISK-001].
- Les étapes qui touchent `dead_load*.py` (1, 2) viennent après le commit de #111 (ARCH-003) ; l'état de ces fichiers est relu à l'étape 0.
- Rien n'est écrit dans un projet réel (CON-006) ; les tests travaillent sur la copie de l'exemple (CON-004). Publication (installeur, site, push) : au mot de l'ingénieur (CON-005).
- Hors périmètre, relevé : la retraite de `loads_migrate.py` / `loads_names.py` (C-3) ; la ligne 3 de `CLAUDE.md` (C-4).

## 15. Vérification

Vérification indépendante (agent `requirements-verifier`, 25.10.2026, contre `a8fc583` → arbre de travail), 14 fichiers de test relancés par lui, tous verts. Verdicts :

| Élément | Verdict | Preuve et suite donnée |
|---|---|---|
| REQ-001 | ✅ | `registry.build_calculations` ne lit que les sources ; `test_new_project` : un classeur aux octets illisibles n'arrête ni l'export ni `registry.export` |
| REQ-002 | ✅ | grep de `open_workbooks`, `reads_sheets`, `registry_no_sheet`, `io_excel`, `SHEET_PREFIX`, `sheet_prefix`, `excel:`, `model.EXCEL` : seulement des assertions d'absence, des docstrings d'historique et la fixture de `loads_migrate` |
| REQ-003 | ✅ | `registry.load_workbook_names`, `workbook_note` ; `test_new_project` (une note, verrou, sous-dossier, deux fichiers, octets et date intacts) ; noms complets des onglets dans la phrase (écart noté) |
| REQ-004 | ✅ | 8 sources, `test_export::test_every_case_a_section_of_the_example_cites_is_exported` ; comparaison au §16 ; le domaine de plus de l'onglet Variables est le script `dreigelenk` que l'export complet a ajouté à `formulas.json` |
| REQ-005 | ⚠️ → ✅ | `docs/conventions/testing.md` citait encore `test_dead_load` : corrigé ; suite complète : 3383 passés, 8 ignorés, 2 échecs relancés seuls et verts (`test_unfold`, PermissionError OneDrive ; `test_member_check_tab`, violation d'accès déjà présente dans la suite de base) |
| REQ-006 | ⚠️ → ✅ | `positions_workbook.py` remis intact ; deux docstrings de `build_reference.py` ajustées en plus de la colonne et du `source_type` (noté) |
| REQ-007 | ⚠️ → ✅ | 1.9/1.1, garde Typst, `check` qui avertit, export 1.8 réécrit ; l'onglet Variables dit `old_export` (code plus précis que `bad_file`, noté) ; « Nouveautés » nomme maintenant 1.9 et 1.1 |
| UI-001, UI-003 | ✅ | trois langues ; « Ouvrir le classeur », provenance Excel et bandeau retirés, état `excel` restauré (test) |
| UI-002, ARCH-006 | ⚠️ (accepté) | les mentions restantes de « Belastungsannahmen » disent que le fichier n'est plus lu ; aucune ne dit de le copier (noté) |
| ARCH-001 à ARCH-005 | ✅ | modules supprimés, `DOMAIN_MODULES` sur les modules de source ; script de conversion hors dépôt ; #111 intact ; décision §13 et index ; `loads_migrate` et son test inchangés et verts |
| CON-001 à CON-006 | ✅ | — |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #109 ; 6 questions (§10) à poser à l'ingénieur avant toute implémentation |
| 2026-10-24 | specified | les six réponses de l'ingénieur (24.10.2026) écrites au §10 et dans §3 à §7, §11, §12 : Q-001 C (aucune conversion), Q-002 B (message générique, classeur jamais ouvert), Q-003 A, Q-004 B (tout retirer, schémas relevés, anciens exports refusés), Q-005 A, Q-006 résolue ; conséquences du refus des anciens exports relevées (C-1), reste à confirmer à l'approbation : C-1 à C-6 (§10) |
| 2026-10-24 | reviewed | revue d'architecture au §13 (APPROUVER AVEC RÉSERVES : ARCH-RISK-001 à 010, contre le code de `master` be5b85f, #111 commité) et plan au §14 (dix étapes, l'exemple d'abord) ; exigences nées de la revue : REQ-007, UI-003, ARCH-004 à ARCH-006 ; en attente de l'approbation de l'ingénieur |
| 2026-10-24 | approved | approbation unique des huit specs du 24.10.2026 par l'ingénieur (AskUserQuestion) : plan approuvé tel quel ; toutes les propositions « à confirmer » des revues acceptées comme recommandées ; ordre d'implémentation #108 → #115 → #114 → #113 → #112 → #109 → #107 → #106, un agent par issue ; commits et push autorisés au fil du travail ; écarts et questions notés en §16 et posés à la fin |
| 2026-10-25 | implementation | étape 0 : `git log` relu (#108, #115, #114, #113, #112 commités après be5b85f ; `variables_browser.py`, `variables_detail.py`, `variable_card.py` de #114 portent « Ouvrir le classeur » et `vr_from_workbook`) ; suite de base : 3399 passés, 10 ignorés, 2 échecs indépendants (`test_fire_tab.test_saving_exports_the_plans_…`, `test_member_check_tab` en violation d'accès) |
| 2026-10-25 | implementation | étape 1 (REQ-004, ARCH-002) : les 8 sources écrites par un script jeté (`check_source` / `stamp_version` des modules de source), comparées à l'ancien export 1.8 avant tout retrait ; trois identifiants corrigés (`WL-Fluchttreppe+Geraete`, `EL+AL-Dach_mit_Wasser`, `EL+AL-Dach_ohne_Wasser`), leurs anciens `.typ` et lignes d'`unfold.json` retirés, `004-einwirkungen.typ` suit ; export complet de l'exemple (sections écrites par `unfold`, figures). Comparaison : `snow-load SL -> SL 12 vars, results q_k1: SAME` ; `wind-load WL-Velo -> WL-Velo 27 vars, results qk_max_cf1,qk_min_cf1,qk_max_cf2,qk_min_cf2,qk_max_cf3,qk_min_cf3,Qk_max_cf1,Qk_min_cf1,Qk_max_cf2,Qk_min_cf2,Qk_max_cf3,Qk_min_cf3: SAME (added by the current code: Qk_max_cf1, Qk_min_cf1, Qk_max_cf2, Qk_min_cf2, Qk_max_cf3, Qk_min_cf3)` ; `wind-load WL-Fluchttreppe+Geräte -> WL-Fluchttreppe+Geraete 27 vars, results qk_max_cf1,qk_min_cf1,qk_max_cf2,qk_min_cf2,qk_max_cf3,qk_min_cf3,Qk_max_cf1,Qk_min_cf1,Qk_max_cf2,Qk_min_cf2,Qk_max_cf3,Qk_min_cf3: SAME (added by the current code: Qk_max_cf1, Qk_min_cf1, Qk_max_cf2, Qk_min_cf2, Qk_max_cf3, Qk_min_cf3)` ; `wind-load WL-Pavillon -> WL-Pavillon 27 vars, results qk_max_cf1,qk_min_cf1,qk_max_cf2,qk_min_cf2,qk_max_cf3,qk_min_cf3,Qk_max_cf1,Qk_min_cf1,Qk_max_cf2,Qk_min_cf2,Qk_max_cf3,Qk_min_cf3: SAME (added by the current code: Qk_max_cf1, Qk_min_cf1, Qk_max_cf2, Qk_min_cf2, Qk_max_cf3, Qk_min_cf3)` ; `dead-load EL+AL-Dach mit Wasser -> EL+AL-Dach_mit_Wasser 4 vars, results gk_ak_gew: SAME` ; `dead-load EL+AL-Dach ohne Wasser -> EL+AL-Dach_ohne_Wasser 4 vars, results gk_ak_gew: SAME` ; `dead-load EL+AL-DachRand -> EL+AL-DachRand 4 vars, results gk_ak_gew: SAME` ; `dead-load EL+AL-Wand -> EL+AL-Wand 4 vars, results gk_ak_gew: SAME`. L'ancien export datait de v0.120 : les six `Qk_*` et le tableau des forces locales « réparties » sont ceux du code actuel. C-6 : deux « Dachbegrünung » (absentes de la bibliothèque) et « Blech Aluminium 2mm » (8 kg/m² dans la feuille, 5,4 dans la bibliothèque) deviennent des charges saisies au poids de la feuille. En passant : `lib/line-levels.json` donne le niveau 1 aux `Qk_*` (ils n'en avaient pas), `variables.PROVENANCE` connaît `entered:`, les tests qui supposaient l'exemple sans source de charge filtrent leurs propres cas ; empreintes `figure-golden` et `report-golden` réécrites. Suite complète verte (3399 passés, 1 FLAKY) |
| 2026-10-25 | implementation | étape 1 commitée et poussée (a64c41a), le code ancien en place, suite verte |
| 2026-10-25 | implementation | étapes 2 à 4 (REQ-001, REQ-002, REQ-003, REQ-006, REQ-007, UI-001, ARCH-001, ARCH-005) : `snow_source`/`wind_source` portent `LABEL`/`ENGINE`/`ACTION`, sans `inputs=` ; `domains/snow.py`, `wind.py`, `io_excel.py` supprimés, le lecteur de `dead_load.py` aussi (`instance_from_layers` reste) ; `_common` sans aides de feuille ; `loads_names` sans cellules (`roof_of` rapatrié) ; `registry.build_calculations(here, files, notes)`, `load_workbook_names`, `workbook_note` (`load_workbook_not_read`), `old_export_note` (`calculations_old_export`, pour `woodcore-cli check`) ; `export_all` sans classeur ; `validation.ENGINES` = python, norm, règles sans `sheet_prefix`, remède « Import données » sur une version plus ancienne (`_older_remedy`) ; schémas `calculations` 1.9 et `project` 1.1 ; garde `load-calculations` dans `lib/calc-engine-core.typ` ; `build_reference` sans colonne `workbook` (« source » au lieu de « sheet ») ; exemple réexporté en 1.9, les trois vents écrits en 1.2 (`openings: rep`, mêmes valeurs) |
| 2026-10-25 | implementation | étape 5 (UI-003) : `variables.EXCEL` et `excel` retirés de `PROVENANCE`, `parse_source` → (kind, rest), `Domain.workbook/.sheet`, `instance_workbook`, `variable_card.workbook_of`, « Ouvrir le classeur » et ses mots, bandeau `stale` (`stale_workbooks`, `stale_text`) et son mot ; `variable_sources.read_export` rend `old_export` (`vr_err_old_export` fr/de/en) ; un état de vue portant `excel` se restaure (test) |
| 2026-10-25 | implementation | étape 6 (ARCH-006) : `cli.py` (`new`, `check`), gabarits `004-einwirkungen.typ` ×4 (commentaire, boucle `case`), `project_template.py`, README, tutoriel 01/02/04/05 et `download.md` ×3 (sous-agent), `reexport_what` « les cas et les dessins de Woodcore » |
| 2026-10-25 | testing | étape 7 (REQ-005) : `test_load_sheets.py`, `test_dead_load.py`, `fixtures/workbook.py`, `load-sheets-reference.json` supprimés ; `test_dead_load_source`, `test_snow_source`, `test_wind_source`, `test_new_project` (message, verrou, sous-dossier, deux fichiers, fichier intact, enregistrement muet), `test_export` (reproductible sur l'exemple, 1.8 → 1.9, compilation arrêtée, `check`, cas cités), `test_project`, `test_variable_sources`, `test_variables`, `test_window`, `test_light_refresh`, `test_domain_contracts`, `test_line_levels`, `test_links`, `test_sia260`, `test_runner`, `test_pdf_button`, `test_domain_generators`, `test_schema_consumers` suivent ; catalogue tenu ; `examples/` regelé (`build_examples.freeze`) sur l'export 1.9 de l'exemple, les trois anciens fichiers retirés ; `calc/i18n/commands.json` suit les trois `///` changés (`domain`, `project-info`, `tl-of`) |
| 2026-10-25 | verification | étape 8 (UI-002, ARCH-004) : `principles.md` §2 (schéma, « Woodcore as the point of entry », règles 5 et 6), `loads.md` §3.3bis, §3.3ter, §3.3quater, §3.3sexies-bis et `calculation-domains.md` §3.3 réécrits, l'ancienne lecture déplacée telle quelle dans `docs/history/load-workbook-sheets.md` ; `layout.md`, `data-contracts.md`, `performance.md`, `window.md`, `tab-variables.md`, `build-and-release.md`, `testing.md`, `open-questions.md` ; décision §13 (six décisions superseded, trois partly) et index ; CHANGELOG ; « Nouveautés » 0.125 fr/de/en avec « À faire une fois » en tête. Vérifié dans la fenêtre (hors écran) : « Ouvrir l'onglet Neige ↗ » de l'onglet Variables ouvre maintenant `SnowTab` sur le cas SL (#114 ne le pouvait pas tant que les cas venaient du classeur) |
| 2026-10-25 | completed | vérification indépendante (§15), écarts corrigés (`testing.md`, « Nouveautés » 1.9/1.1, `positions_workbook.py` intact) ou notés ; suite complète verte une fois relancés seuls les deux échecs indépendants ; spec déplacée dans `completed/` |
