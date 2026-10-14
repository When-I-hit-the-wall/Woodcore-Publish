# Audit 260916-2326 — Phase 7 (agent p7d) : CLAUDE.md §10ter à §12, puis §13 et §14 en entier

Commit audité `997570dbaf7eda09738d4fad6f65e815053c52f3`. Bac à sable `projet-phase7d` (scripts et sorties dans `projet-phase7d/p7d/`, sonde Typst `projet-phase7d/000-TypstRapport/p7dprobe.typ`). `git -C <projet réel> status --short` vide au départ et à la fin : rien n'a été écrit dans le projet réel. Toute exécution Qt/Python s'est faite avec `LOCALAPPDATA` et `TYPST_KATALOG_SETTINGS` pointés dans le bac à sable ; aucune fenêtre construite par `main()`.

Session interrompue à 23 h 52 par la limite de l'API puis reprise ; dédoublonnage fait contre `rapport-phase2/3/6/7a/7b/7c.md` et MISSIONS.md. Non re-signalés : AUD-1-1 à 1-5 ; AUD-6-4, 6-10, 6-21 (dont CLAUDE.md 2121, 2176, 2182-2183, 2187, 2230) ; AUD-7-101 à 7-110 (tables de tests, arbre du §11, comptes du §10ter/§10sexies/§11bis, « sixty lines ») ; AUD-7-112, 7-118, 7-119, 7-128 ; AUD-7-205, 7-226 ; AUD-7-303, 7-316, 7-317, 7-318 ; les arrêts d'export « schéma supprimé / point supprimé » établis en phase 8.

## Bilan

Contrôles menés : 152 (§10ter 10, §10quater 34, §10quinquies 13, §10sexies 14, §11 6, §11bis 4, §11ter 10, §12 14, §13 : 33 décisions non couvertes par p7c relues contre le code, §14 : 14 points ouverts non couverts par p7c). Conformes : 125. Constats : A 23, B 2, C 4. NON FAIT : 3.

## Méthode et preuves communes

- `p7d/check_static.py` : `identity.slug_id` contre `connection.id_from_name` (15 noms, 0 écart) ; avertissements d'un plan dupliqué ; `build_examples.ids_in`/`dangling()` contre les schémas ; feuilles et fonctions `call_*` de `build_reference.py`.
- `p7d/check_behaviour.py` : (a) articulation en cisaillement portant une raideur passée à `statics.check_source` ; (b) 30 ordres d'import de `connector`, `connector_svg`, `connection`, `connection_svg`, `schema`, `schema_svg` (sous-processus) ; (c) bandeau « périmé » du Katalog avant/après `connector.export()`.
- Sonde Typst `p7dprobe.typ` (compilée, texte relu par pypdf) : niveaux de `#var`, `#eq`, `#verify`, notation scientifique de `#val`, `#unit("Nmm")`, unité déclarée inatteignable.
- `make -n` dans le bac à sable (GNU Make 4.4.1) : refus `LEVEL`+`UNIFORM`, `LEVEL=4`, `REPORT_LANG=it`, `-f` depuis un autre dossier, `LANG=en_US.UTF-8` ignoré, `make -n all SKIP_DATA=1 REPORT_LANG=fr`. `typst compile` vers un dossier absent : refus « os error 3 ».
- `p7d/check_unique.py` : chaque « texte actuel » proposé ci-dessous apparaît **exactement une fois** dans CLAUDE.md (25/25).

## Conformes (résumé)

§10ter : 14 feuilles écrites après `data/` par `export_all.py` (erreur de permission = avertissement), `example_call` sur Calculations/Checks/Vars/Connectors/Connections/Plans/Statics/Schemas, pas d'`example_call` sur Steps, `action` sur Calculations, `show-live-load` pour une catégorie à valeurs et `show-calc` pour E, `source_type` `norm`/`sheet`/`position`/`connection` par `iter_sources()`, régénération seule par `python calc/tools/build_reference.py`, `import_line()` = `#import "../commands.typ": *`.

§10quater : onglet Charges (groupes par `action`, filtre nom/symbole/libellé/feuille/classeur/valeur, *Résultats seulement* coché par défaut, ★ et gras, sources Excel/Python/norme, *Ouvrir le classeur*, appels de `var_commands`/`instance_commands`/`domain_commands` et `-var` pour un nom qui masquerait un global) ; *Importer Excel* (processus séparé, délai 600 s, message de l'exportateur) ; *Exporter PDF* (export puis `typst compile` seulement si code 0, `MAIN_TYP`/`REPORT_PDF`, `--input` identiques à `build.ps1`, groupe exclusif de sept niveaux, infobulle vide « tel qu'écrit », choix non écrits dans `settings.json`, PDF ouvert puis archivé) ; fermeture pendant un export différée ; onglet réservé *Combinaisons de charges* ; `nowheel` (filtre sur l'application, `QScrollBar` exclu, renvoi au viewport) ; `grouped_list`/`source_archive` (archives hors glob, ID libéré, restauration sous un ID du nom) ; `identity.IdentityRows` dans les onglets plan, modèles statiques, schémas, connecteurs, et Schéma · Nom · Description · ID dans *Moments polaires* ; `id_from_name` = `slug_id` sans variante (0 écart sur 15 noms) ; renommage d'un schéma propagé (`rename_references` → `schema_renamed` des deux onglets) ; `on_shown` ; `install_error_box` ; `stallwatch` (STALL_S 1,5 s, HITCH_S 0,75 s, un seul fil, journal remis à zéro au-delà de 512 Ko) ; dépendances (`check()` hors ligne, PyPI dans un fil, bandeau bleu, `pin()` après installation) ; grilles `auto/5/1/0,5/0,1 m` et `auto/1000/100/10/1 mm`.

§10quinquies (sonde) : `#var` au niveau 3 imprime la description sur la ligne après un tiret cadratin (« F = 2 kN — Kraft am Ende ») ; `#eq` au niveau 1 imprime symbole et réponse (« M = 6 kNm ») ; `#verify` au niveau 2 imprime les nombres seuls (« 2 kN ⩽ 7 kN ✔ ») ; `#val` au-delà de 99 999 : « 1.235 · 10⁶ N » ; `#unit("Nmm")` : « 6 · 10⁶ Nmm » ; `unit: "N"` inatteignable : réponse en kNm et ligne rouge « Die verlangte Einheit N passt nicht… » ; côté seul d'un `verify` garde son unité (`relation-side`) ; refus de `var-unit` dans le `context` ; `show-polar-moment(N: "N_Ed")` lu dans le registre (décision v0.61).

§10sexies : pages lues dans `examples/out/`, manifeste `index.json`, états fresh/stale/missing, repli contre les données **figées** (`fallback_imports`), `typ-dry` réservé à `show-check`, sélecteur désactivé pour un exemple qui fixe son `level:`, `--freeze` jamais passé par `export_all.py`, copie de `lib/` comparée octet par octet par `test_commands.py`, cache dans `%LOCALAPPDATA%\typst-katalog\examples`, messages d'erreur renumérotés (`in_example`).

§11/§11bis : aucun module de `calc/` n'ouvre un fichier de `000-ExternalFiles/` (seules mentions : docstrings, `_source` des JSON, exclusion d'`archive_export.py`) ; chemins dérivés de `__file__` (aucun `getcwd`/`Path.cwd`).

§11ter : dossier temporaire par pid, `cleanup()` idempotent, réglages redirigés et amorcés en anglais, `requirements.txt` épinglé exactement, `dependencies.py` conforme au texte.

§12 : options de `build.ps1` (`Level`, `Uniform` exclusifs, `Language`, `AllLevels` en `uniform`, `SkipData`, archivage en `try/catch`, `--detail` omis quand vide) ; `Makefile` (refus avant exécution, `REPORT_LANG` et non `LANG`, cibles `.PHONY`, archivage avec `-`, `report-N` en `uniform`) ; `.vscode/settings.json` `"$dir/../$name"` ; `archive_export.py` (horodatage `AAMMJJ-HHhMM`, suffixe `-2`, `main()` sort toujours 0, exclusions `000-ExternalFiles`, `000-Archives`, `examples`, `out`, `tests/.tmp`, `Sections/*.pdf`) ; `.gitignore` (`000-Archives/`, `.preview/`, `examples/lib/`, `tests/.tmp/`).

§13 relues (hors liste de p7c) et conformes : v0.77 Nom·Description·ID, renommage de schéma suivi, surveillance des blocages ; v0.75 barre sans défilement vertical, dossiers vides dans `settings.json` et tests isolés des réglages ; v0.74 graphe d'import acyclique (30 ordres, 0 échec), *Grille…* dans *Schémas* ; v0.73 sélection « focus et reste », *Trancher* prend sa ligne dans la sélection ; v0.69 molette ; v0.71 archivage ; v0.65 exemples figés, MWE générés, pages pré-rendues ; v0.64 catégories écrites à la main et tenues dans les deux sens, exemple = un document ; v0.63 une unité par dimension, `#unit`, ligne rouge, `var-unit`, conversion par `#var`, notation scientifique confinée ; v0.63.1 arguments nommés déclarés ; v0.62 compilation directe et menu à cases ; v0.61 un nom par variable, domaines nommés, `verify`, niveaux ; v0.60 fichier `formula.typ` ; v0.59 vérifications dans le dépôt, refus plutôt qu'avertissement, versions épinglées, modules sans appelant supprimés ; v0.58 police des marques ; v0.52/v0.54 langues ; v0.40 `commands.typ` ; v0.30 PySide6 (boîte Windows si absent) ; v0.31 source par fichier, export séparé, forces en Typst ; v0.32 flèches insérées par le rapport, tableaux centrés ; v0.28 `action` déclarée, Katalog lisant l'export ; v0.26 classeurs trouvés par nom.

§14 relus (hors p7c) et toujours ouverts dans le code : `domains` toujours `{}` ; c_f du vent non lus ; ψ et catégorie E ; `N37`/`N38` refusés ; autres organes d'assemblage (`connector.MODULES = {dowel.TYPE: dowel}`) ; force de calcul ; GL40h et plus refusés (`sia265.py:433`) ; modèle de connexion à rigidité égale ; plans (DXF, axes dérivés, calques cachés avertis par `plan._hidden_layers`) ; glossaire non utilisé par l'onglet Charges, pas de `--check-i18n` ; exemple non éditable ; `show-check` en `typ-dry` ; validation `data_type`.

## Constats

### AUD-7-401 | A | CLAUDE.md:1252 (§10ter)

« Since v0.18 every sheet leads with `source_type` / `domain` / `instance` » est faux pour 8 des 14 feuilles (`Functions`, `Parameters`, `Examples`, `Connectors`, `Connections`, `Plans`, `Statics`, `Schemas`). Preuve : `build_reference.SHEET_SPECS` (`check_static.py` §4). Remplacer `Since v0.18 every sheet leads with `source_type` / `domain` / `instance`, the two arguments` par `Since v0.18 every sheet that catalogues a calculation — `Calculations`, `Results`, `Steps`, `Checks`, `Vars`, `Choices` — leads with `source_type` / `domain` / `instance`, the two arguments`. Test : `SHEET_SPECS` dont l'en-tête commence par `source_type` = exactement ces six feuilles.

### AUD-7-402 | A | CLAUDE.md:1261 (§10ter)

« so it always reflects exactly the domains/instances/steps/checks/vars that will compile successfully » : seul `export_all.py:227` appelle `build_reference_workbook` ; *Enregistrer* dans les onglets connecteurs, moments polaires, plans, modèles et schémas n'exporte que sa partie de `data/` (`connector.export`, `connection.export`, …), si bien que les feuilles `Connectors`, `Connections`, `Plans`, `Statics`, `Schemas` restent en retard jusqu'au prochain export complet. Preuve : `grep build_reference_workbook calc/` → `export_all.py:16,227` et `build_reference.py:1026` seulement. Remplacer `so it always reflects exactly the domains/instances/steps/checks/vars that will compile successfully.` par `so after every full export it reflects exactly the domains/instances/steps/checks/vars that will compile successfully. A connector, a connection, a plan, a static model or a schema saved in the Katalog exports its own part of data/ and not this workbook, whose sheet for it then lags until the next *Importer Excel*.` Test : aucun (la phrase décrit un fait).

### AUD-7-403 | A | CLAUDE.md:1263, 1270 (§10ter)

La liste des fonctions `call_*` « the one place a Typst call is spelled out » omet `call_show_connector_resistance` et `call_connector_loop` (utilisées par `connectors_tab.py:1654-1660`), `call_show_schema` et `call_schema_loop` (`schema_tab.py:1612-1618`, `build_reference.py:509`) ; la feuille `Schemas` (`SHEET_SPECS`, v0.72) et les colonnes `schema`, `member_elements`, `markers` de `Connectors` (v0.74) ne sont décrites nulle part au §10ter. Remplacements : (1) `` `call_show_connector` (v0.33), `import_line` — `` → `` `call_show_connector` (v0.33), `call_show_connector_resistance` and `call_connector_loop` (v0.68), `call_show_schema` and `call_schema_loop` (v0.72), `import_line` — `` ; (2) `` `show-calc` for the one that does not (E), which the report refuses. `` → `` `show-calc` for the one that does not (E), which the report refuses. Since v0.72 a `Schemas` sheet lists each detail schema: its label, how many elements, connector markers, aids and dimensions it carries, the ids of its elements and markers, the elements whose position no longer resolves, and its `show-schema` call; and since v0.74 the `Connectors` sheet also names each connector's schema, its members' elements and its markers. `` Test : chaque `def call_` de `build_reference.py` est nommée au §10ter (comme AUD-7-101 pour les tests).

### AUD-7-404 | A | calc/tools/catalog_gui.py:737-741 ; CLAUDE.md:1290 (§10quater)

Le bandeau « données périmées » compare `Positionen.xlsx` à `data/connectors.json` « where the connectors come from » : les connecteurs ne viennent plus de `Positionen.xlsx` depuis v0.68, et `connectors.json` est réécrit à chaque connecteur enregistré dans le Katalog (`engine.write_json` réécrit toujours), ce qui **efface le bandeau** alors que les positions n'ont pas été réexportées. Preuve (`check_behaviour.py` c) : `Positionen.xlsx` touché après l'export → `stale_workbooks` = `['Positionen.xlsx']` ; après `connector.export()` → `[]`, alors que `positions-index.json` reste plus ancien que le classeur (`True`). Correction code (4 lignes) : remplacer
`    # The connectors' positions come from Positionen.xlsx (CLAUDE.md section 7bis): one added there is not offered until the export has read it.` / `    connectors_file = data_file.parent / connector_model.EXPORT_FILE` / `    connectors_exported = connectors_file.stat().st_mtime if connectors_file.exists() else 0` / `    if POSITIONS_BOOK.exists() and POSITIONS_BOOK.stat().st_mtime > connectors_exported:`
par
`    # The positions come from Positionen.xlsx (CLAUDE.md section 7): one added there is offered to no tab until the export has read it. Compared with positions-index.json, which export_all.py alone writes -- data/connectors.json is rewritten by every connector saved in the Katalog, which hid a workbook saved in between.` / `    index_file = data_file.parent / "positions-index.json"` / `    positions_exported = index_file.stat().st_mtime if index_file.exists() else 0` / `    if POSITIONS_BOOK.exists() and POSITIONS_BOOK.stat().st_mtime > positions_exported:`.
CLAUDE.md : `(since v0.33 also `Positionen.xlsx`, where the connectors come from)` → `(since v0.33 also `Positionen.xlsx`, where the positions come from, against `data/positions-index.json`)`. Test (`test_catalog.py`, sur une copie) : classeur plus récent que l'index, puis `connector.export()` → `stale_workbooks` contient toujours `Positionen.xlsx`.

### AUD-7-405 | A | CLAUDE.md:1303, 1295 (§10quater, *Moments polaires*)

« every connector marker **and every construction point** of the schema » : le code (`connection.fastener_places` → `schema.fastener_places`) ne propose que les points **cochés « connecteur »** (aide `point` avec `connector: true`), comme le disent §3.3decies et §10quater *Schémas* ; et *Nouveau calcul* coche les repères **ou**, faute de repère, les points cochés (`schema.default_fasteners`). Remplacements : (1) `every connector marker **and every construction point** of the schema` → `every connector marker **and every construction point ticked «connecteur»** of the schema` ; (2) `its members the schema's linear elements and every one of its markers ticked` → `its members the schema's linear elements and every one of its markers ticked — or, on a schema carrying none, every point ticked «connecteur» (`schema.default_fasteners`)`. Test : existe déjà côté code (`test_schema_consumers`, point non coché non proposé).

### AUD-7-406 | A | CLAUDE.md:1309 (§10quater, *Moments polaires*)

« *Supprimer* removes the source and exports again » : depuis la fin de v0.77, `PolarTab.delete` → `source_archive.Actions.delete` déplace la source dans `connections/archives/` sans son `id` (le même §10quater le dit plus bas pour tous les onglets). Remplacer `*Supprimer* removes the source and exports again, which removes its figure.` par `*Supprimer* moves the source into «Archives», its ID removed, and exports again, which removes its figure (v0.77, `source_archive.py`).` Test : couvert par `test_editor_buttons.py` (archivage sans id).

### AUD-7-407 | A | CLAUDE.md:1404 (§10quater)

« Before anything else the window compares what is installed » : `main()` construit la fenêtre, l'affiche, installe `stallwatch`, puis `QTimer.singleShot(0, window.check_dependencies)` (`catalog_gui.py:3122-3126`, commentaire « After show() … never before »). Remplacer `Before anything else the window compares what is installed against `requirements.txt`` par `As soon as the window is on screen — `main()` queues `check_dependencies` after `show()`, a modal needing a window to sit on — it compares what is installed against `requirements.txt``. Test : `test_wheel.test_the_guard_is_installed_by_main` a le modèle ; ajouter l'ordre `show()` < `check_dependencies` lu dans le source de `main()`.

### AUD-7-408 | A | CLAUDE.md:1386 (§10quater, *Schémas*)

L'ordre des groupes décrit (… Aides · **Cotation** · **Modification**) n'est pas celui de la barre : `schema_tab.TOOL_GROUPS` place `sc_group_modify` avant `sc_group_dimensions` (`schema_tab.py:83-89`), donc Aides · Modification · Cotation. Remplacer la chaîne `· **Cotation** (horizontale · verticale · parallèle · angle) · **Modification** (v0.73: *Déplacer · Dupliquer · Tourner · Symétrie*, four tools of two clicks, and *Trancher · Fusionner*, two **buttons** — they act on what is already selected, so there is nothing on the grid for them to point at and nothing for the exclusive tool group to hold checked).` par `· **Modification** (v0.73: *Déplacer · Dupliquer · Tourner · Symétrie*, four tools of two clicks, and *Trancher · Fusionner*, two **buttons** — they act on what is already selected, so there is nothing on the grid for them to point at and nothing for the exclusive tool group to hold checked) · **Cotation** (horizontale · verticale · parallèle · angle).` Test : aucun.

### AUD-7-409 | A | CLAUDE.md:1684 (§10sexies)

Le sélecteur 1 · 2 · 3 « recompiles the same example at that level » et « passes `--input level=` » : depuis v0.65 il **charge** la page pré-rendue du niveau (`build_examples.examples_of` rend les trois niveaux, `stem()` → `<commande>-<n>-L1`/`-L3`, `CommandBox.on_level` → `start()` → `page_for`), et le niveau est écrit dans le document (`command_preview.preamble` : `#report-level.update(n)`), ce que la même section dit trois paragraphes plus haut. Remplacer `and recompiles the same example at that level — which shows §3.7's three reports rather than describing them. It passes `--input level=`, never `uniform=`:` par `and shows the same example's page at that level, rendered ahead of time like the others (`<command>-<n>-L1.png` and `-L3.png` beside the level-2 page) — which shows §3.7's three reports rather than describing them. The level is written into the example as `#report-level.update(n)`, never as `uniform`:`. Test : aucun.

### AUD-7-410 | A | calc/tools/build_examples.py:193-194 (contrôle décrit CLAUDE.md:1692, §10sexies)

`dangling()` doit signaler un exemple citant un id que le projet n'a plus, mais `ids_in()` ignore `schemas.json` : `show-schema-1.typ` et `show-schema-2.typ` citent `"Beispiel"`, schéma absent du projet (`schemas` figé `['Beispiel','SD_01','SD_02']`, projet `['SD_01','SD_02','VU-Skizze']`), et `dangling()` ne le rapporte pas (`check_static.py` §3 : 17 occurrences, aucune `Beispiel`). Distinct d'AUD-1-1 (qui porte sur les ids que le contrôle voit). Correction : remplacer `                      ("plans.json", "plans"), ("statics.json", "models")):` par `                      ("plans.json", "plans"), ("statics.json", "models"), ("schemas.json", "schemas")):`, et dans la docstring `the plans and the static models` → `the plans, the static models and the schemas`. Test : dans `test_the_dangling_check_catches_a_planted_one`, planter aussi un schéma retiré. ⚠️ Rendra `test_no_example_names_something_the_project_no_longer_has` rouge sur un id de plus tant qu'AUD-1-1 n'est pas traité.

### AUD-7-411 | A | calc/tools/commands_tab.py:643, 658, 661, 686 (CLAUDE.md:1680, §10sexies)

« Rendered in German, once … So switching the window to French no longer re-renders the examples » et « a fallback reading the live export would disagree with every page beside it » : le repli (page manquante ou périmée) compile avec `self.app.lang` (clé de cache, `write_document`, `in_example`), donc dans la langue de la fenêtre, alors que toutes les pages validées sont rendues en `build_examples.LANG = "de"`. Preuve : `check_static.py` §6 (4 occurrences de `self.app.lang`, `LANG = de`). Correction : remplacer `self.app.lang` par `examples.LANG` aux quatre lignes (module déjà importé sous le nom `examples`). Test : onglet construit en français, exemple rendu en repli → `preview.PREVIEW_TYP` contient `#set-report-language("de")`.

### AUD-7-412 | A | tests/conftest.py:36 (CLAUDE.md:1934, §11ter)

« `pytest`, where it happens to be installed, discovers the same files unchanged … raises `Skip` and is counted as skipped, never as a failure » : `class Skip(Exception)` n'est connu que de `run_tests.py` ; sous pytest un `Skip` levé est une **erreur**. Correction : `import unittest` et `class Skip(Exception):` → `class Skip(unittest.SkipTest):` (pytest traite `unittest.SkipTest` comme un saut dans toute fonction de test ; `run_tests.py` l'attrape toujours avant `AssertionError`). CLAUDE.md : `raises `Skip` and is counted as skipped, never as a failure.` → `raises `Skip` and is counted as skipped, never as a failure — by `run_tests.py`, and by pytest as well, `Skip` being a `unittest.SkipTest`.` Test (`test_harness.py`) : `issubclass(conftest.Skip, unittest.SkipTest)`. ⚠️ Comportement sous pytest NON exécuté (pytest absent du poste).

### AUD-7-413 | A | CLAUDE.md:1936 (§11ter)

« The one test that does read the real workbooks only reads them » : trois tests les lisent — `test_dead_load.test_the_engineers_own_workbooks_still_pass` (Belastungsannahmen), `test_norms.test_grades_match_the_workbook` (`Verbindung.xlsm`), `test_export.test_the_export_is_reproducible` (lance `export_all.py` sur le projet réel, qui lit les deux classeurs et réécrit `data/`). Remplacer `The one test that does read the real workbooks only reads them, and says so in its name.` par `The tests that read the real workbooks — `test_dead_load.test_the_engineers_own_workbooks_still_pass`, `test_norms.test_grades_match_the_workbook` (`Verbindung.xlsm`) and `test_export.test_the_export_is_reproducible`, which runs the whole export — only read them, and are skipped where they are not there.` Test : aucun.

### AUD-7-414 | A | CLAUDE.md:2000 (§12)

« The three build routes also converge … each calls `archive_export.py` » : au §12 les trois routes sont `build.ps1`, `make` et **Tinymist**, qui n'archive pas ; les trois qui archivent sont `build.ps1`, `make report` et *Exporter PDF* (les cibles `report-N` n'archivent pas non plus, `Makefile:75-76`). Remplacer `The three build routes also converge on one more thing:` par `Three routes also converge on one more thing — `build.ps1`, `make report` and the Katalog's *Exporter PDF*; Tinymist's on-save export and the `report-N` variants do not archive:`. Test : `test_pdf_button.py` pourrait lire `archive_export.py` dans `build.ps1` et le `Makefile`.

### AUD-7-415 | A | CLAUDE.md:2045 (§13 v0.74)

« A new *polar-moment* calculation does the same with the schema its connector is drawn on » : depuis v0.76 un moment polaire ne nomme aucun connecteur ; `PolarTab.new` prend le schéma du calcul sélectionné, sinon du formulaire, sinon le premier (`catalog_gui.py:2433-2441`, `selected_schema`). Remplacer par `A new *polar-moment* calculation does the same with the schema of the calculation selected, else the form's, else the first there is — it names no connector since v0.76.` Test : couvert (`test_polar_tab`).

### AUD-7-416 | A | CLAUDE.md:2062 (§13 v0.69)

« ⚠️ *Moments polaires* shows the folders and takes no drop yet » : réalisé en v0.75 (`PolarTab.build_list` : `GroupedList`, `moved` → `on_moved`) et décrit ainsi au §10quater. Remplacer la phrase entière `⚠️ *Moments polaires* shows the folders and takes no drop yet: its left pane is a tree of connectors with their calculations beneath, which the schemas module replaces, and building the drag into it twice would be work thrown away.` par `⚠️ *Moments polaires* showed the folders and took no drop until v0.75, its left pane being a tree of connectors with their calculations beneath; since v0.75 it lists its calculations in folders of their own `group` and takes a drop like every other editor tab.` Test : couvert (`test_polar_tab`, dépôt qui classe).

### AUD-7-417 | A | CLAUDE.md:2091 (§13 v0.58)

La décision décrit au présent `#test(left, op, right, unit:)`, retiré en v0.61 (`grep "#let test("` → rien ; `formula.typ:1169 #let verify`). Les règles tiennent (comparaison par le moteur, deux côtés de dimensions différentes refusés). Remplacer `` `#test(left, op, right, unit:)` takes the two numbers, compares them itself, `` par `` `#test(left, op, right, unit:)` — `#verify` since v0.61, which keeps every rule below and reads its two sides out of the registry of variables (§10quinquies) — takes the two numbers, compares them itself, ``. Test : aucun.

### AUD-7-418 | A | CLAUDE.md:2127 (§13 v0.60)

« the answer is converted into the declared unit or the compile stops » : inversé en v0.63 (décision « A declared unit the formula cannot reach prints in red », ligne 2135) ; sonde MARK-F : `unit: "N"` sur un moment compile et imprime « 6 kNm » avec la ligne rouge. Remplacer `the answer is converted into the declared unit or the compile stops.` par `the answer is converted into the declared unit or the compile stops — until v0.63, when an unreachable declared unit became a red line under an answer printed in the operands' own unit (below).` Test : couvert (`test_formula.test_a_declared_unit_the_formula_cannot_reach_prints_and_does_not_stop`).

### AUD-7-419 | A | CLAUDE.md:2096 (§13 v0.33)

« Connectors are entered in Excel, as a second sheet of positions » reste au présent alors que v0.68 l'a inversée (ligne 2065 « reversing v0.33 ») ; les autres décisions inversées sont barrées (`~~…~~ **Reversed in v0.76**`). Remplacer `- **Connectors are entered in Excel, as a second sheet of positions, settled (v0.33).**` par `- ~~**Connectors are entered in Excel, as a second sheet of positions, settled (v0.33).**~~ **Reversed in v0.68** (above): a connector is a file of its own, `connectors/<id>.json`, written by the Katalog; what follows is kept as the record of v0.33.` Test : aucun.

### AUD-7-420 | A | CLAUDE.md:2093 (§13 v0.32)

« A v0.31 file is converted as it is read rather than refused » : `connection.check_source` refuse une source 1.0/2.0/2.1 et renvoie à `migrate_to_schemas.py` (`connection.py:40, 164-165`), et le repère est celui du schéma depuis v0.74 (décision ligne 2039, dont AUD-7-303 traite la formulation). Remplacer `A v0.31 file is converted as it is read rather than refused: the conversion is exact, and the forces printed for it do not change.` par `A v0.31 file was converted as it was read rather than refused: the conversion is exact, and the forces printed for it do not change. ⚠️ Both halves were superseded in v0.74 (above): the frame is the detail schema's, `reference` only names the Bezugselement, and a 1.0, 2.0 or 2.1 source is refused by name and converted once by `calc/tools/migrate_to_schemas.py`.` Test : couvert (`test_schema_consumers`, source à dessin propre refusée).

### AUD-7-421 | A | CLAUDE.md:2147 (§13 v0.14)

« because nothing reads the string back as a number » : `schema.parse_section` le lit depuis v0.75 (décision ligne 2033 « relaxed in exactly one place »). AUD-7-202 ne couvre que §7/§10bis. Remplacer `A panel, a round column, or anything else now needs no special case, because nothing reads the string back as a number.` par `A panel, a round column, or anything else now needs no special case, because nothing reads the string back as a number — with one exception since v0.75 (above): `schema.parse_section` reads a b/h `dimension` as the default section of a detail schema's element, leniently.` Test : aucun.

### AUD-7-422 | A | CLAUDE.md:2227 (§14, onglet des commandes)

Point ouvert « The preview follows the *engine's* language … a French preview says «Abbildung» » : depuis v0.65 les aperçus sont des pages rendues une fois en allemand (`build_examples.LANG = "de"`), sans aperçu français (sauf le repli d'AUD-7-411). Remplacer la puce entière (chaîne unique commençant par `  - **The preview follows the *engine's* language, not the document's.**` et finissant par `until someone actually writes a French report.`) par `  - **The previews are rendered in German, whatever the window's language** (v0.65, §10sexies), `config.typ`'s `doc-lang` included, so every preview says «Abbildung»; an example that wants French asks for it itself with `set-report-language`. Whether the pages should also exist in a second language is the question the day a French report is written.` Test : aucun.

### AUD-7-423 | A | CLAUDE.md:2233 (§14)

« the embedment strength and minimum spacings the *Connecteurs* tab will need are SIA 265 6.2–6.5 » : réalisé pour la broche en v0.68 (`calc/norms/sia265-2021-tab22-lochleibungsfestigkeit.json`, `-tab24-abstaende.json`, `dowel.py`). Remplacer `the embedment strength and minimum spacings the *Connecteurs* tab will need are SIA 265 6.2–6.5, in `SIA265-2021-DE.pdf`;` par `the embedment strength and minimum spacings of a Stabdübel were transcribed from SIA 265 6.2.1 in v0.68 (`calc/norms/sia265-2021-tab22-lochleibungsfestigkeit.json`, `-tab24-abstaende.json`), and those of the other kinds of fastener are in the rest of chapter 6 of the same `SIA265-2021-DE.pdf`;`. Test : aucun.

### AUD-7-424 | B | CLAUDE.md:2107 (§13 v0.51) ; calc/domains/statics.py:419-422

Décision : « a release that carried a translational stiffness … keeps its degree of freedom and loses the stiffness ». Code : `statics.check_source` **refuse** une articulation en cisaillement ou en effort normal portant une raideur (« a spring along a member is a member of kind 'spring', not a release »), et `read_source` ne convertit rien : un tel fichier arrête l'export. Preuve (`check_behaviour.py` a) : articulation `G9` `dof: shear`, `stiffness 500 kN/m` → `REFUSED (export would stop)`. Aucun fichier du projet n'a cette forme aujourd'hui. Options : (a) garder le refus et réécrire la décision (« is refused by name; the engineer turns it into a member of kind `spring` ») ; (b) appliquer la décision : à la lecture, retirer la raideur d'une articulation non-moment et avertir.

### AUD-7-425 | B | lib/formula.typ:514-523 (`key-symbol`) ; CLAUDE.md §10quinquies « The names »

`check-key` accepte toute clé de lettres, chiffres et `_` (`^[A-Za-z_][A-Za-z0-9_]*$`), mais `key-symbol` renvoie telle quelle une clé sans `_` : `M2`, `Mx`, `Fd` deviennent une source mathématique invalide et la compilation échoue sur l'erreur brute de Typst, dans `formula.typ:1008`, sans le message qui nomme quoi corriger (§10bis point 2). Preuve (sonde) : `#eq("M2", …)` → `error: unknown variable: M2 … formula.typ:1008:26` ; `#eq("Mx", …)` → idem ; `M_2`/`M_x` compilent. Options : (a) imprimer une clé de plusieurs lettres sans `_` comme mot droit (`"Mx"`) ; (b) mettre les chiffres finaux en indice (`M_2`) ; (c) refuser dans `check-key` en disant d'écrire le symbole en second argument positionnel (`#eq("M2", "M_2", …)`). Un choix d'impression, donc à l'ingénieur.

### AUD-7-426 | C | calc/tools/catalog_gui.py:2985-2988 (§10quater, *Exporter PDF*)

Un export qui écrit sur stderr ouvre `QMessageBox.warning` **avant** `compile_pdf()` ; sur ce projet l'export avertit toujours (AUD-1-5), donc chaque *Exporter PDF* s'arrête sur une boîte à valider avant de compiler. Non contradictoire au texte (l'ordre export → compilation tient), à connaître.

### AUD-7-427 | C | calc/tools/archive_export.py:25-35 (§12, §13 v0.71)

L'instantané copie `000-TypstRapport/000-Audits/` (rapports d'audit, sans rapport avec la réouverture du Katalog) et `tests/.settings-<pid>.json` si un run est en cours ; ni exclu, ni revendiqué exclu. À décider si l'on veut l'exclure.

### AUD-7-428 | C | Makefile:75-76 (§12)

`make report-N` écrit dans `out/` sans le créer, et `typst compile` refuse un dossier de sortie absent (preuve : `failed to write PDF file (… os error 3)`) ; `build.ps1` le crée (`New-Item`). Sans effet aujourd'hui (`out/report-*.pdf` suivis par Git, donc le dossier existe).

### AUD-7-429 | C | tests/conftest.py ; calc/tools/command_preview.py:31 ; calc/tools/plan_canvas.py:37 (§13 v0.75)

La suite isole les réglages (`TYPST_KATALOG_SETTINGS`) mais pas `LOCALAPPDATA` : les rendus d'exemples (`command_preview.CACHE_DIR`) et de plans (`DiskCache`) des tests vont dans les caches réels de l'ingénieur (lecture de code, non exécuté). La décision v0.75 ne promet que les réglages ; information pour la phase 8.

## NON FAIT

- NF-1 : comportement de `conftest.Skip` sous pytest (AUD-7-412) non exécuté : pytest n'est pas installé (`ModuleNotFoundError`) et l'installer modifierait l'environnement du poste.
- NF-2 : interaction réelle des onglets (glisser, survol, clic sur la barre) non rejouée : la consigne interdit `main()` et la phase 5 couvre les boutons ; les points §10quater ont été vérifiés par lecture du code, par `check_behaviour.py` et par le journal des tests de la phase 1 (499 réussis).
- NF-3 : `build.ps1` non exécuté de bout en bout (compilerait et archiverait ; lu ligne à ligne et recoupé avec le `Makefile` en `make -n`).

## Vérifications manuelles proposées

1. Katalog : modifier `Positionen.xlsx`, enregistrer un connecteur, rouvrir → le bandeau jaune doit nommer `Positionen.xlsx` (échoue aujourd'hui, AUD-7-404).
2. Onglet *Commandes* en français, supprimer une page de `examples/out/` et ouvrir l'exemple → la page de repli doit être en allemand comme ses voisines (AUD-7-411).
3. Décider AUD-7-424 et AUD-7-425.

## Contrôles qui pourraient devenir des tests

- Chaque `def call_` de `build_reference.py` nommée au §10ter ; en-têtes `source_type` exactement sur les six feuilles de calcul (AUD-7-401, 403).
- Bandeau périmé robuste à un connecteur enregistré (AUD-7-404).
- `dangling()` voit un schéma retiré (AUD-7-410).
- Repli de l'onglet *Commandes* rendu en `examples.LANG` (AUD-7-411).
- `issubclass(conftest.Skip, unittest.SkipTest)` (AUD-7-412).
- `main()` : `check_dependencies` programmé après `show()` (AUD-7-407).
- Une clé `#eq("M2", …)` échoue avec un message du moteur, pas de Typst (AUD-7-425, selon l'option choisie).
- Décisions §13 au présent contredites par une décision ultérieure « reversing vN » non barrée (recherche de `reversing v0.NN` et de l'entrée vN correspondante sans `~~`) (AUD-7-419).
