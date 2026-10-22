# Audit du 19.10.2026 — base saine

Issue mère #73, sous-issues #65 à #72. État de départ : `master` au commit `44a4ff9` (fusion de `origin/master` dans le travail en cours sur les commandes en ligne), version déclarée `0.118.0` (`calc/project.py:27`) alors que `CHANGELOG.md` décrit déjà quatre lots « v0.119 ». Taille : 127 000 lignes Python dans `calc/`, 11 300 lignes Typst dans `lib/`, 177 fichiers de tests (75 400 lignes), 4,1 Mo de `docs/`.

Méthode : la suite complète lancée deux fois en local (Windows 11, Python 3.14.7), quatre audits en lecture seule menés en parallèle (code mort et commandes, structure des onglets, moteurs de calcul et de dessin, normes et formules), chaque constat avec sa preuve `fichier:ligne`. Rien n'a été supprimé : selon la décision de l'ingénieur (#67), l'audit dresse la liste et l'ingénieur tranche.

## 1. Ce qui a été fait dans cette session

| Issue | Fait | Preuve |
|---|---|---|
| #66 | La branche `ccr-d93df6af-ie8kzm` est supprimée sur GitHub ; elle n'avait aucun commit absent de `master`. Seule `master` reste. | `git ls-remote --heads origin` → `refs/heads/master` seul |
| #65 | Suite complète : **3013 réussis, 11 sautés, 2 échecs**, puis les deux échecs corrigés à leur source (ci-dessous). | `python tests/run_tests.py` |
| #65 | **Régression de fusion** : la fenêtre ne s'ouvrait plus sur un projet ayant un domaine. `_top_level_lines` rend des triplets depuis le travail sur les commandes en ligne, `_body_span` (venu de `master`) attendait des couples. | `calc/domains/formula_domain.py:515` |
| #65 | Le nom d'un projet de l'ingénieur était écrit dans la spec active et dans un test, et le test lisait le chemin de ce projet en dur. Le test lit maintenant le dossier dans `WOODCORE_INLINE_DOMAINS`. | `tests/test_no_third_party_name.py`, `tests/test_formula_domain.py:505` |
| #65 | Un test écrivait son fichier en CRLF sous Windows et comparait à une relecture LF : il n'échouait que sous Windows, la CI tournant sous Ubuntu. | `tests/test_formula_domain.py:290` |
| #69 | `build_examples.py` écrivait les 441 exemples `examples/*.typ` en CRLF sous Windows, d'où 441 fichiers « modifiés » sans changement réel. Écrits en LF, et les 441 fichiers remis en LF. | `calc/tools/build_examples.py:130,157,297` |
| #69 | `engine.write_json` écrivait chaque `data/*.json` d'un export en CRLF sous Windows. Écrit en LF. | `calc/engine.py:155` |

**Incident** : un agent d'audit a arrêté des processus `python.exe` par leur nom, ce qui a interrompu le premier passage de la suite (21 fichiers sur 208). La suite a été relancée entière. À éviter : arrêter un processus par son PID, jamais par son nom d'image.

## 2. Code mort, commandes et onglets inutilisés (#67) — à trancher

Analyse statique (`ast` pour Python, `lib_bindings` pour Typst) ; « inutilisé » veut dire « inutilisé dans le dépôt » : les sections écrites dans les projets de l'ingénieur ne sont pas visibles d'ici.

### 2.1 Modules

| Module | Constat | Confiance | Ce qu'on perdrait |
|---|---|---|---|
| `calc/tools/migrate_to_schemas.py` (247 l.) | importé par personne ; travaille sur `ROOT/connectors`, `ROOT/details`, dossiers qui n'existent plus | probable | la migration unique des sources d'avant v0.74 |
| `calc/tools/catalog_gui.py` (12 l.) | gardé pour les lanceurs installés en 0.83–0.90 | sûr (non importé) | le démarrage par un lanceur de cette époque |
| `calc/tools/build_document_templates.py` (603 l.) | lancé à la main avec un `catalogue.json` qui n'est pas dans git | probable | la régénération des gabarits intégrés `cu/standard`, `bp/standard` |
| `calc/norms/sia260.py` | lu par les tests seuls ; attend l'onglet « Combinaisons » | sûr | la table ψ transcrite, prête pour les combinaisons |

`archive/` n'est importé par aucun code vivant (`tests/test_retired_features.py` le garde) : sain.

### 2.2 Définitions sans appelant (~45)

Toujours présentes depuis `260917-code-mort.md` : `MEMBER_FILLS`, `MEMBER_OPACITY`, `_over_white` (`connection_svg.py`), `ALL_ASSEMBLIES`, `VIEWS` (`connector.py`), `TIMBER_ASSEMBLIES`, `STEEL_ASSEMBLIES` (`dowel.py`), deux `TOOL_ORDER` (`schema_canvas.py`, `statics_canvas.py`), `_to_model` (`statics_svg.py`), `GroupedList.set_strings`, `clear_marks`, `parse_doc_comments`, `lib_records`, `parse_param_docs` (gardés par des ré-imports « compat »), `axis_orientation`.

Nouvelles : `_quarter`, `_mu`, `is_link`, `TOOL_DEFAULT_KEYS`, `_document_background`, `TRACK_KINDS`, `values_of`, `Calculation.add_check`, `requirement_edition`, `SOURCE_FILE` (`journal.py`), `OLD_SHEET`, `LIB_DIR`, `Project.as_project_path`, `Project.loads_dir`, `SELECTION_LEVEL`, `NODE_KINDS`, `fit_file`, `_stop_writes`, `write_languages`, `REPLACE`/`CLOSE` (`autosave.py`), `COMMANDS_IMPORT_PATH`, `staging_png`, `entry_title`, `SNAP_TOOLS`, `FireCanvas.snap_to_existing`, `set_frame`, `DocumentView.select_pages`, `page_rect`, `frame_page`, `choose_template`, `PlanTab.plans_on`, `_section_label`, `request_compile`, `set_stopped`, `TitleBlockModel.set_logo`, `Sizes.on_text`, `pdf_page_count`. Ces suppressions ne font perdre que du code sans appelant.

Environ 90 fonctions ne sont appelées que par des tests (lecteurs de normes `sia265.gamma_m`, `distance_table`…, gestion de projets `templates.save_project`, `move_section`…, neuf `call_*` de `build_reference_calls.py`) : à examiner une par une, chacune garde un test.

### 2.3 Commandes Typst

Sur 118 commandes publiques, une seule n'est utilisée par aucun code : **`schema-ids`** (`lib/calc-engine.typ:1607`, sûr). Probablement inutilisées : `show-plan-legend` (`show-plan` a déjà `legend: true`) et `moisture-class-of`. Interne et sans aucune référence : `distance-scopes` (`lib/distance.typ:31`).

Fusions possibles (ce qu'on gagne / ce qu'on perd) :

- **Les 13 commandes `*-ids`** → un `ids(kind)` : douze entrées de moins dans `commands.json` (×3 langues), la référence, les exemples. On perd les noms parlants et les sections existantes cassent, sauf à garder des alias.
- **`show-load-summary` / `show-line-load-summary`** (`lib/summary.typ:270,304`), corps identiques à une unité près → `show-load-summary(unit:)`. On perd un nom d'appel.
- **`doc-plan` / `doc-fire-plan` / `doc-extract`**, **`sheet-legend` / `sheet-fire-legend`**, **`sheet-viewport` / `sheet-fire-viewport`** : un helper interne commun, sans changer les noms. Ce sont des étiquettes `// woodcore:object` écrites dans les sections.
- **Les `get-*`** → `get(v, "champ")` : gain faible, usage massif (`get-value` 28 fois). Déconseillé.

### 2.4 Onglets

Aucun onglet caché ni remplacé. Six onglets **réservés et vides** : « Charge utile » et « Séisme » (`FutureTab`), « Combinaisons » (sans module), « Torsion », « Déformation », « Vibrations » (`SoonTab`). « Charge utile » est vide alors que le domaine `live_load` (SIA 261, tab. 8) existe. « Poids propre », « Neige » et « Vent » n'ont pas de fichier `docs/ui/tab-*.md`.

## 3. Structure des onglets (#68)

**Constat** : il n'existe ni classe de base, ni protocole, ni registre d'onglet. Un onglet est une fabrique dans `TABS` (`calc/tools/woodcore_gui.py:200`), et la fenêtre l'interroge par `getattr`/`hasattr`. **Ajouter un onglet demande huit retouches à la main** : `TABS`, `NAV_GROUPS` et `NAV_SECTIONS`, `MODE_TABS`/`DOCUMENT_TABS`/`MODE_BOUND`, `GUARDED_TABS` et `DOMAIN_TABS`, l'icône dans `chrome.ICONS`, le titre dans `woodcore_gui_words.py`, une boucle de fusion de `STRINGS` par module, la doc et le catalogue de tests.

Divergences principales :

- **Classe de base** : `DisplayTab` + `QWidget` pour 8 onglets, `QWidget` seul pour 7.
- **Affichage** : monté à la main dans « Charges » et « Vérifications ».
- **`set_view`** : quatre implémentations différentes.
- **`save`** : trois signatures (`save()`, `save(quiet)`, `save(close_open)`).
- **`export`** : quatre formes.
- **Clé d'onglet** : déclarée (`KEY`) dans certains onglets, écrite en dur dans d'autres.
- **Annuler** : trois piles identiques (`HISTORY = 200`), dans le dessin, les schémas et la statique.
- **Garde en lecture seule** : elle repose sur une liste de noms de méthodes (`WRITERS`, `woodcore_gui.py:302`). Une méthode d'écriture mal nommée lui échappe.

Code recopié d'onglet en onglet, avec preuves `fichier:ligne` dans le rapport d'agent :

| Code | Copies |
|---|---|
| `confirm_leave` | 14 |
| `update_list_marker` | 11 |
| raccourci Ctrl+S | 13 |
| `reload_list`, `on_list_change`, `on_moved` | 7 à 10 chacun |
| `save` (validation de l'id, renommage, écriture, export) | 3 copies littérales : Connecteurs, Charges, Vérifications |
| squelette « éditeur de sources » | au moins 7 onglets, environ 150 à 200 lignes par copie |

Trois voies, à trancher par l'ingénieur :

- **A — Déclarer sans refondre.** Un `TabSpec` unique (clé, fabrique, groupe, icône, modes, garde, mots, domaine) remplace les huit points ; un `Protocol` décrit le contrat ; un test paramétré le vérifie pour chaque onglet.
  - Coût et risque : faibles.
  - Le code recopié reste.
- **B — Une classe de base `SourceEditorTab`.** Elle porte la liste, le formulaire, le résultat, enregistrer, exporter et annuler.
  - Gain : le plus grand.
  - Coût : élevé, plusieurs milliers de lignes déplacées pendant que d'autres sessions éditent les mêmes fichiers.
- **C — Des services par composition, un à un.** Dans l'ordre : `SourceListController` → `SourceStore` → `DisplayHost` → `UndoHistory`.
  - Les onglets délèguent, et leurs noms de méthodes publiques restent intacts, si bien que la garde en lecture seule continue de marcher.
  - Coût moyen, étalé ; risque faible à chaque étape.

**Recommandation : A, puis C service par service, B restant la cible des nouveaux onglets.**

## 4. Moteurs de calcul et de dessin (#69)

### 4.1 Calcul

Point fort : les domaines à source JSON suivent le même squelette (`source_paths / check_source / read_source / new_source / prepare / write / export`), et aucun import Qt n'entre dans `calc/domains/`.

| # | Divergence | Gravité |
|---|---|---|
| C1 | **Quatre formes de résultat** : `engine.var/step/check` (charges, goujons, assemblages), `rows` de `member_check`, `steel_calc.Calc` (réécrit `engine.Calculation` à la main), `Result` des domaines. | élevée |
| C2 | La citation est facultative dans les lignes de `member_check` (`clause=None`), et `published_vars` fige `"norm": "SIA 265"` même pour une ligne VKF/feu (`member_check.py:757,1393`). | élevée |
| C3 | Les schémas `steel-source` et `profile-source` existent mais ne sont jamais appliqués à l'exécution, alors que 11 autres domaines appellent `validate_structure`. | moyenne |
| C4 | Trois formes d'avertissement : `engine.Note` traduisible, chaînes brutes en allemand ou en anglais (`dowel.py`, `connector.py`, 25 sites), `print` sur stderr (`wind.py:221`, `registry.py:136`). | moyenne |
| C6 | Le bois est calculé deux fois : en Python pour la fenêtre, en Typst pour le rapport, tenus égaux par un test de parité. Le docstring de `member_check.py:1` est faux. | moyenne |
| C7 | `UnfoldError`, `DomainError`, `Refused`, `FormulaError` ne dérivent pas de `ValidationError` et échappent aux `except (ValidationError, EngineError)` de `cli.py` et `export_all.py`. | moyenne |
| C8 | Pas de test direct de `snow.py`, `wind.py`, `live_load.py`, `materials.py`. | faible |

### 4.2 Dessin

| # | Divergence | Gravité |
|---|---|---|
| D1 | La règle 16 (une seule mécanique de toile) ne vaut que pour le plan et le plan feu. Schémas et modèles statiques ont leur propre toile, leur pile d'annulation et leur aimantation (déjà dans `docs/open-questions.md`). | élevée |
| D2 | `SvgLayer` en 3 exemplaires, avec deux stratégies de cache différentes ; `_cosmetic` ×3, `_round` ×4. | moyenne |
| D4 | La géométrie de cotation et d'aimantation est recopiée entre `schema_geometry.py` et `statics_geometry.py` (90 à 100 % identique) ; `normalize_angle` existe en 5 copies. | moyenne |
| D5 | Couleurs de figure écrites en dur dans les 9 modules `*_svg` : cinq quasi-noirs, trois oranges de surbrillance, `font-family="Arial"` en dur. `theme.json` ne couvre que la fenêtre. | moyenne |
| D6 | Le formateur de coordonnées SVG `_f` existe en 8 copies avec trois précisions ; `_text` ×7. | moyenne |
| D7 | Le Typst recalcule des tailles que Python a déjà calculées (`schema-extent`, `schema-halo`, `static-halo`) ; quatre fonctions de nombres SVG. | moyenne |
| D3, D8 | Rendu SVG → `QIcon` en 5 copies ; l'azimut calculé dans la toile statique. | faible |

### 4.3 Incohérences générales

| # | Sujet | Gravité |
|---|---|---|
| G1 | **Fins de ligne** : 61 des 73 `.write_text` de `calc/` n'imposent pas LF. Corrigé ici pour `write_json` et `build_examples` ; les autres restent. Il faut un seul `write_text_lf` et un test qui interdit l'appel nu. | élevée |
| G2 | **Les onglets écrivent leurs sources eux-mêmes** (`json.dumps(...)` à la main, au moins 15 fois), sans `check_source` préalable, alors que `member_check.write_source` existe. | élevée |
| G3 | Dix chargeurs de normes, chacun avec son cache et ses messages ; un seul retire du cache une table en échec. | moyenne |
| G4 | Utilitaires recopiés : `_fail` ×27, `_number` ×19, `_fmt` ×5 avec trois précisions, `KG_TO_KN` ×2, des conversions d'unités locales alors que `units.py` existe. | moyenne |
| G5 | 13 `except Exception` sans justification ; des `pass` silencieux sur un échec de dessin. | faible |
| G6 | Des couches inversées : `domains/` importe `tools/` (`build_reference`, `usersettings`), et 273 imports différés évitent des cycles. | moyenne |
| G7 | 13 fichiers `*_words.py` (environ 466 Ko) hors de `calc/i18n/`. La frontière fenêtre/rapport n'est pas écrite dans CLAUDE.md. | faible |
| G8 | Un même concept porte plusieurs noms : « schéma » = dossier `details/` ; `LABEL` désigne une couleur ici et un nom de domaine là ; `woodcore_gui_polar.py` sort de la convention `*_tab.py`. | faible |
| G9 | `lib/calc-engine.typ` fait 3708 lignes, à découper par sujet comme les modules Python (#30). | moyenne |

## 5. Normes et affichage des formules (#70)

**Bilan : bon pour le bois, les charges et les goujons.** Les 116 JSON de `calc/norms/` portent tous `edition` et `_source` (clause ou tableau, PDF). Aucun γ, η, ψ, μ, β_n, k_fi n'est écrit en dur.

Écarts :

| # | Constat | Gravité |
|---|---|---|
| N1 | **Acier SIA 263 : coefficients écrits dans le code et dans le texte des formules.** Facteur 0.9 de la section nette (`steel_resistance.py:156`, SIA 263 5.1.2), exposants d'interaction 2.0, 5·n, 1.1, 1.66/(1−1.33n²), 6.0 (`:264,278,285,287`, 5.1.6.4), 0.5 (`:251-273`), seuil n ≤ 0.9 (`:227`). Le chiffre affiché et le chiffre calculé peuvent diverger. | **élevée** |
| N2 | **Deux sources pour les valeurs SIA 261 de neige et de vent** : le classeur Excel (`snow.py`, `wind.py`) et les JSON (`sia261-2020-5.2-schnee.json`, tables du vent) pour les sources Python. | **élevée** |
| N3 | `SteelCalc.given()` admet `norm=""` et n'appelle pas `_check_citation`. Les efforts E_d et les valeurs de section hors catalogue partent sans norme alors que `schemas/steel.schema.json` l'exige. La provenance de `beta_N` dit « python ». | moyenne |
| N4 | La moelle (`f_v,d / 2`, SIA 265 tab. 8 note 6) est écrite deux fois, en Python et en Typst ; le JSON ne porte que le texte de la note. La limite h > 200 m du vent (SIA 261 6.1.2) est écrite en dur. | moyenne |
| N5 | Les `#eq`, `#var` et `#val` écrits à la main ont `norm: none` par défaut, alors que `docs/typst/citations.md` dit que toute étape porte `norm` et `norm_ref`. | moyenne |
| N6 | Les JSON citent `ExternalFiles/000-Normes/…`, chemin qui n'existe pas sur ce poste (les PDF sont dans `02_Normen und Bibliothek/`) ; `test_sia260` est sauté pour cette raison. | faible |

**Affichage des formules, divergences d'un onglet à l'autre :**

- **Indices.** « Rd » et « Ed » s'impriment en italique et séparés dans l'acier et les goujons (`N_(R d)`, `gamma_(M 2)`), en droit dans les domaines écrits à la main (`F_"Ed"`), avec des virgules dans le bois (`f_(m,y,d)`). γ_M s'écrit de trois façons.
- **Grands nombres.** `eq`/`var`/`val` passent en notation scientifique au-delà de 99 999 ; `show-calc` jamais (`60910.397` contre `6.091 · 10⁴`).
- **Décimales.** 3 par défaut, 6 fixes pour les constantes du bois en Typst, 3 et 1 pour les distances, 1 ou 2 dans les tableaux de l'acier. Le formateur Python `_fmt` existe en 4 copies : trois à 6 décimales, une à 3.
- **Constantes dans les formules.** Composées depuis le JSON pour les goujons (bien) ; tapées dans la chaîne pour l'acier (voir N1).
- **Niveau de détail.** Décidé par la commande dans le bois (`plan-at`), figé à l'export dans l'acier et les goujons (`level=1`) : on le règle à deux endroits.
- **Commandes sans niveau.** `distance` n'a pas de paramètre `level` ; `distance`, `show-fire-plan` et `show-plan` n'ont pas d'exemple L1/L3.
- **Mise en forme.** Signe moins, espace insécable avant l'unité et séparateur décimal (« . » dans les trois langues) ne sont pas uniformes.

## 6. Risques, dangers et avenir (#71)

### 6.1 Les grands dangers

1. **Les fusions entre sessions concurrentes cassent sans bruit.** La preuve est dans cet audit : la fusion `44a4ff9` a empêché la fenêtre de s'ouvrir, sans conflit textuel. Un commit « WIP » est arrivé sur `master`, et la spec qu'il implémente est encore dans `active/` avec `status: verification`, alors que `CHANGELOG.md` la cite déjà dans `completed/`. Six specs dorment dans `docs/requirements/active/`, dont deux depuis le 07.10.
   - **Parade :** jamais de WIP sur `master` ; une branche par session et une fusion seulement après la suite ; la CI (`tests.yml`) rendue obligatoire avant une fusion.
2. **La CI ne voit pas Windows.** Elle tourne sous Ubuntu, alors que le programme est livré sous Windows. Deux défauts de cet audit n'existaient que sous Windows (CRLF).
   - **Parade :** un job `windows-latest` dans `tests.yml`, au moins pour les tests du moteur et de l'export.
3. **La suite dure 31 minutes.** Une suite longue finit par ne plus être lancée avant un commit.
   - **Parade :** un niveau « rapide » (moteur, normes, export, moins de 3 min) avant chaque commit, la suite entière en CI. Le plus lent : `test_polar_tab` (212 s pour un seul test).
4. **Des valeurs qui vieillissent sans le dire.** C'est la peur n° 1 de CLAUDE.md, et elle existe à trois endroits :
   - les coefficients de l'acier (N1) ;
   - la double source neige et vent (N2) ;
   - le double calcul du bois Python/Typst (C6, tenu par un seul test de parité).
5. **Les copies du moteur dans les projets.** `_woodcore/lib/` est copié dans chaque projet, et les sections de l'ingénieur appellent les commandes par leur nom. Supprimer ou renommer une commande (§2.3) casse des projets que le dépôt ne voit pas.
   - **Parade :** une politique écrite d'alias et de dépréciation (une version d'avertissement, puis le retrait), avant toute fusion de commandes.
6. **Le coût d'un onglet.** Huit retouches à la main et un squelette recopié (§3) : chaque nouvel onglet ajoute une variante, et chaque correction doit être faite N fois.
7. **La documentation comme mémoire.** `docs/decisions.md` (400 Ko) et 4 Mo de `docs/` portent l'histoire en prose. Un renvoi faux ou une décision remplacée sans le dire égare la session suivante. `test_docs_coherence` aide, mais ne vérifie pas le sens.
8. **Le démarrage.** Les 37 onglets sont construits au démarrage, sur le fil de la fenêtre (`woodcore_gui.py:682`). `docs/open-questions.md` mesure déjà des arrêts de 0,5 à 1,3 s, et chaque onglet en ajoute.

### 6.2 Améliorations d'architecture, par ordre de rendement

1. **Fins de ligne et écriture des sources** : G1 et G2, un seul écrivain LF et `write_source` par domaine. Petit, mécanique, protège les données.
2. **Registre d'onglets** (voie A) avec un test de contrat, puis les services de la voie C.
3. **Une seule forme de résultat** avec citation obligatoire (C1, C2, N3), autour de `engine.Calculation`.
4. **Les coefficients SIA 263 en JSON**, et les formules de l'acier composées depuis ces valeurs comme le font les goujons (N1).
5. **Trancher la source des valeurs SIA 261** pour la neige et le vent : classeur ou JSON (N2).
6. **Un module de géométrie plane et une base de toile communs** (D1, D2, D4, D6), puis une palette de figures (D5).
7. **Un seul chargeur de normes** (`norms/_loader.py`) et un module d'utilitaires communs (`fail`, `is_number`, `fmt_number`, unités depuis `units.py`) (G3, G4).
8. **Une seule écriture des formules** : indices, notation scientifique, décimales, niveaux (§5).
9. **Découper `lib/calc-engine.typ`** par sujet, et remettre `build_reference` et `usersettings` hors de `tools/` (G6, G9).
10. **Construire les onglets à la demande**, à leur première ouverture, pour le temps de démarrage.

### 6.3 Où Woodcore peut aller

- **Combinaisons d'actions SIA 260.** C'est le chaînon manquant le plus évident : l'onglet est réservé, la table ψ est transcrite (`sia260.py`), et aujourd'hui aucun γ_G ni γ_Q n'existe. Les vérifications reçoivent leurs efforts saisis à la main ; avec les combinaisons, elles les recevraient des charges.
- **Aptitude au service** (déformations, vibrations des planchers, SIA 265) et **torsion** : les trois onglets sont réservés.
- **Un graphe de dépendances du projet** : positions → charges → efforts → vérifications → rapport. Une valeur changée en amont dirait ce qu'elle rend périmé en aval. C'est l'extension naturelle de « une seule source de vérité », et de la colonne « périmé » que les domaines dépliés (#62) ont commencée.
- **Un modèle statique qui calcule**, au moins pour les poutres simples et continues : aujourd'hui les modèles statiques sont dessinés, et les efforts viennent d'ailleurs (RFEM a été retiré).
- **EC5 à côté de SIA 265**, à partir du même registre de normes. L'architecture de `calc/norms/` le permet ; il faudrait un choix de norme par projet.
- **Comparer deux versions d'un rapport** : quelles valeurs ont changé entre deux exports. Utile pour le contrôle par un tiers.
- **Les normes comme paquet versionné à part** (les JSON et leurs éditions), mis à jour sans reconstruire le programme ; #34 va dans ce sens.

## 7. Plan de nettoyage proposé

| Lot | Contenu | Mode |
|---|---|---|
| 1 | G1 (écrivain LF unique et test) + G2 (`write_source` par domaine) | small-feature par domaine |
| 2 | Suppressions de §2 validées par l'ingénieur | small-feature |
| 3 | Registre d'onglets (voie A) | big-feature |
| 4 | Acier en JSON (N1, N3) | big-feature |
| 5 | Forme de résultat unique (C1, C2) | big-feature |
| 6 | Neige et vent, une seule source (N2) | big-feature, décision d'abord |
| 7 | Toile commune (D1–D6) | big-feature |
| 8 | Écriture des formules unifiée (§5) | big-feature |
| 9 | CI Windows, niveau de tests rapide, règle « pas de WIP sur master » | small-feature + décision |

## 8. Décisions demandées à l'ingénieur

1. Lesquelles des suppressions du §2 (modules, définitions, `schema-ids`, `show-plan-legend`, `moisture-class-of`, `distance-scopes`) valider ?
2. Fusionner les commandes du §2.3, et avec quelle politique d'alias ?
3. Garder ou retirer les six onglets réservés ? « Charge utile » pourrait afficher `live_load`.
4. Structure des onglets : la voie A, B ou C du §3 ?
5. Neige et vent : le classeur ou les JSON comme seule source ?
6. Ajouter un job Windows à la CI, et un niveau de tests rapide ?
