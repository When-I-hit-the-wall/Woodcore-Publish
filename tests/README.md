# tests/ — the checks this pipeline is allowed to rely on

Until v0.59 every verification this project claimed was written once, run once, and thrown away: `CLAUDE.md`'s changelog reports more than six hundred checks, and not one of them was in the repository. They were therefore unrepeatable, which for a project whose whole argument is traceability at ten years (§1bis) is the wrong way round — the norm edition is versioned, the report is versioned, and the proof that the engine still reads them correctly was not.

This folder is where a check goes so that it can be run again.

## Running them

```
python tests/run_tests.py
```

from `Woodcore/`. No framework, no extra dependency: the runner is standard library alone. It runs every test file in a process of its own, as many at once as the machine has cores, prints one line per test (a file's lines together, when the file ends), then the failures and a summary, and exits non-zero if anything failed — which is what lets a script or a CI job call it. A test still running after 300 s is stopped with the stack of every thread written, fails under its own name, and the rest of its file runs on (issue #22, `docs/conventions/testing.md` §11ter).

`pytest` also finds and runs these files unchanged, because the convention below is pytest's own. It is not required, and nothing here imports it.

```
python tests/run_tests.py -k dead_load     # only the tests whose name matches
python tests/run_tests.py -v               # print the assertion detail of failures
python tests/run_tests.py --failed         # only the tests that failed in the previous run
python tests/run_tests.py --related calc/renumbering.py   # the test files naming that module, and the previous failures
python tests/run_tests.py -j 1             # one file at a time
python tests/run_tests.py --times          # the time per file and the slowest tests
```

## The convention

* One file per concern, named `test_<concern>.py`.
* One function per check, named `test_<what it checks>`, taking no argument.
* Plain `assert`, with a message that says what was expected and what was found.
* A test that cannot run — the workbooks are not there, Typst is not installed — raises `Skip("why")` rather than failing. A skip is printed, counted, and never fails the run.

`conftest.py` puts `calc/` on the import path, so a test imports the pipeline exactly as `export_all.py` does (`from domains import dead_load`).

## The project the tests work on (v0.81)

The code no longer sits inside a project, so the tests carry one: `projet-exemple/`, a real project anonymised — the sources drawn in its window, its export and its report, no workbook, blank pages in place of the architect's plans and blank pictures of the same sizes. `conftest.py` copies it beside `.tmp/` once per run (`.project-<pid>/`), copies the engine into it and makes it the current project (`conftest.PROJECT`). So:

* a test reads the export with `conftest.PROJECT.data_dir` and the sources with `conftest.PROJECT.connectors_dir` and the like, never with a path of its own;
* a `.typ` probe goes in `conftest.probe_dir(name)` and is compiled with `--root conftest.TYPST_ROOT`, importing `"/commands.typ"` — or an import computed with `conftest.import_path(...)`;
* a test that must work on a copy of the project to write into it takes `conftest.project_copy(name)` and `project.using(...)`;
* a test that needs a workbook takes the engineer's own project, `conftest.real_project()`, which is named by `WOODCORE_REAL_PROJECT` (else the one beside the checkout) and skips where there is none. The cells of `Verbindung.xlsm` are frozen in `fixtures/verbindung.json` for that reason.

A full run that skips more than `MAX_SKIPPED` fails: a clone of the code skips the few checks that need a workbook, and a run skipping much more than that is checking less than it seems.

## What is in here, and why each one exists

Every file of the folder is listed here, grouped by what it guards. A file added to `tests/` is not finished until it has its row. No count of tests is given: it changes with every version, and a number nobody updates is a number that lies.

### The pipeline, the data and the norms

| File | Guards against |
|---|---|
| `test_project.py` | A project named by its `.woodcore` file (v0.81): the defaults of a new project, a path leaving the project refused, a file that is not a project refused by name, the order `current()` looks in, the export reading the project it is given, and no module of `calc/` fixing a project path at import again. |
| `test_new_project.py` | A new project made from `templates/projet/` (v0.83): laid out as the default one, only in an empty folder, its workbook carrying the headers the export reads, its report compiling once exported, `woodcore-cli new`; an old folder converted where it stands, its engine replaced only once asked; and `project.update` keeping what it is not given. Since v0.96: a project file written with the window's old key, `katalog`, read and migrated to `gui` by its first change of folders. |
| `test_packaging.py` | The installed program's launcher and installer (v0.83): the version a project asks for, else the newest, a newer project refused, the sources chosen for a double-click, by the window's file of their time (`woodcore_gui.py`, `catalog_gui.py` before v0.96), `--dry-run`; the installer per user, one AppId per version, HKCU only; and `catalog_gui.py`, the window's old name, a shim nothing imports. The build itself is `packaging/build.py`'s to check. |
| `test_export.py` | An artifact whose schema version is not the one the code reading it expects, an older record passing as a current one, a record left behind for a position Excel no longer has (`D001`, v0.59), and an export that does not give the same bytes twice. Also the strength class read from its own column and the moisture class under its new header and its old one (v0.77). |
| `test_constants.py` | The lists of allowed values restated in `validation.py` drifting from the domain modules they were copied from. A circular import is what forced the copy; this is what keeps the two honest. |
| `test_norms.py` | The files of `calc/norms/`: each named `<norm>-<year>-<table or clause>-<designation>.json`, none in a subfolder, none read by no module, and no SIA 265 coefficient written into `domains/dowel.py`. Spot values read off the norm's own pages, SIA 263 Tabellen 1 and 2 (S460 included, which `Verbindung.xlsm` lacks), SIA 261 Anhang A, and SIA 265 against the engineer's independent transcription. Each guard is fired against a planted defect. |
| `test_i18n.py` | A translation that was never made, in either glossary: `calc/i18n/strings.json` (what the report prints) and the window's `STRINGS` (what the window says). Same keys in every language, and no sentence left word for word identical in two languages unless it is whitelisted after being looked at. Since v0.79: a norm's word inside a template's hole, the embedment table's note sentence by sentence, Auflast as SIA 261 Tabelle 80 names it, the editors' warnings, two dialogs and Qt's own buttons in the window's language, and every STRINGS key named by some code. Since v0.96: no «Katalog» said by the window, its message boxes or the launcher. |
| `test_archive.py` | What lands in a project's `_Archiv/` on every successful export -- one zip and a flat copy of the PDF -- and what stays out (docs/conventions/build-and-release.md §12), on a small project of its own rather than a real one's archive folder; the window's route named `gui`, and `katalog`, its name until v0.96, read as it. |

### The calculations

| File | Guards against |
|---|---|
| `test_dead_load.py` | The two rules added in v0.59: a chosen permanent load below the sum of its own layers, and a specific weight typed over the sheet's lookup. Both are built on a workbook this folder writes itself; the engineer's own sheets are also read end to end. Since v0.79: a load typed in column K with no material, counted and printed as typed. |
| `test_connection.py` | The polar moment and the distribution of N, V and M, against the HB2 method sheet's worked example (§3.3quinquies), plus the invariants no published answer is needed for: static equivalence, the moment's force at right angles to its lever arm, every tied fastener named. |
| `test_dowel.py` | The shear resistance of a Stabdübel connection, SIA 265 6.2.1: both sheets of `Verbindung.xlsm` reproduced cell by cell, the 28 published cells of Tabelle 21, Tabelle 45's short form falling out of the general one, k_β continuous and monotone and one Figur 45 curve per thickness, and the places the workbook departs from the norm. Since v0.79: the Holz-Holz sheet of `Verbindung.xlsm` against the project's own connector, cell by cell, K_ser,Verb with η_w included. |
| `test_connectors.py` | A connector from its source file to `data/connectors.json` and to the report: a member's timber resolved afresh at every export, a reference that no longer resolves warning without stopping, the ten descriptive keys unchanged, the id composed of the name, and the «Connecteurs» form itself — every assembly builds and calculates, every row carries a unit, the results carry real subscripts, hovering a box lights its results, and no top-level window flashes while switching connectors. |
| `test_formula.py` | `var`, `eq`, `verify` and the unit algebra of `lib/formula.typ`: the answers against values the project already knows, the refusals each fired on purpose, the unit a result is printed in and the red line where a declared unit cannot be reached. Runs Typst and reads the numbers back from the compiled document. Since v0.79: a key that cannot be printed as its own symbol, refused saying what to write. |
| `test_arrows.py` | The force arrows on a connection's figure being drawn two ways. They are written twice — Python for the window's preview, Typst for the report — and `CLAUDE.md` says they are kept "rule for rule alike". Both are handed the same figure and forces, and their SVG is compared element by element. |

### The detail schemas

| File | Guards against |
|---|---|
| `test_schema.py` | The source's own checks, the three ways to draw a rectangle agreeing to the digit, what is exported (a named point) and what is not (a construction line), a label's leader appearing exactly when it leaves its piece, the drawing unchanged when nothing moved, and `details/` never being confused with the contracts' `schemas/` folder. |
| `test_schema_edit.py` | Move, duplicate, turn, mirror, split and merge: a cut piece keeps its position number, a merge of two numbers refuses naming both, four quarter-turns and two mirrors give back the coordinates to the digit, split and merge are an exact pair, a multiple delete is one undo step and a refusal is none. |
| `test_schema_section.py` | An element's b and h following its position and staying written over once typed, the band being the side the view shows, the label «T001 C24 100/200» placed clear of the node, a 1.0 file whose drawing does not move, and the crop. |
| `test_schema_consumers.py` | A connector and a polar-moment calculation reading one drawing: moving a marker moves it in both, a member reaches its position through its element, what the schema no longer carries warns rather than stops, and a detail turned by 30° leaves a member's `local` angle where it was while its `axis` angle moves. Since v0.79: a schema or a marker lost never stops the export, the record says why, and the report refuses a polar moment its schema no longer carries. |
| `test_schema_tab.py` | The «Schémas» tab built off-screen: every tool reachable from the bar, what a click puts down being a source the export accepts, the element panel, *Ajouter* under every list, a hovered row lit, a construction line selectable and cut on, and the ticks centred in their cells. |

### Woodcore's window

| File | Guards against |
|---|---|
| `test_home.py` | The start page, the File menu and the user's settings (v0.83): the recent projects, a project gone greyed, a `.woodcore` dropped, the settings of before v0.83 (`typst-katalog`) taken over once, «• Exemple — Woodcore», another project never opened under a running export, a project opened read-only saving and exporting nothing, and `--self-test` -- by `woodcore_gui.py` and by `catalog_gui.py`, its old name (v0.96). |
| `test_lock.py` | The lock a window holds on its project (v0.83): another machine's asked about and taken only when forced, never removed by a window that does not hold it, a crashed window's stale, and a name NextCloud syncs. |
| `test_editor_buttons.py` | A button that raises and so silently does nothing: every list button of the five editor tabs (load, Nouveau, Enregistrer, Dupliquer, Annuler les modifications, Supprimer, new folder) clicked against a copy of the project's sources, with every dialog stubbed. Since v0.78 also *Supprimer* on a draft never saved, which archived a saved entry, and a refused *Ajouter* of the static models, which left a step of *Annuler*. |
| `test_identity.py` | Nom · Description · ID in every editor tab, a saved object never renamed by naming it, a folder made in any of the five tabs still there after the list is rebuilt, a schema renamed being followed by what names it, a tab brought to the front reading the schemas again, and one «Connecteurs» box lit at a time. |
| `test_polar_tab.py` | The «Moments polaires» tab: the id made from the name and writable over, a 3.x file read as 4.0, the *Identité* box holding exactly Schéma · Nom · Description · ID, *Nouveau* opening on a schema with every marker ticked, *Enregistrer* writing the file, and a drop filing a calculation without renaming it. |
| `test_groups.py` | The folders of the left panes: a folder is a `group` field and never a directory, a source without one reads as the root, a multiple selection moves whole, an empty folder survives a rebuild, and removing a folder never removes what is in it. |
| `test_window.py` | The mark of unsaved changes: a dot at the left of the row and of the tab, with its room kept whether it is drawn or not, and never written into the text; the stale banner hidden by a connector saved; an example compiled on the spot in another language than the committed pages. |
| `test_pdf_button.py` | The split buttons «Importer Excel» and «Exporter PDF»: the Typst input and output and the `--input` flags being the ones `woodcore-cli` passes (one function, `calc/cli.py`'s `input_args`), *tel qu'écrit* passing none, a base and a uniform level never combined. |
| `test_panes.py` | The position plan tab's three panes being draggable: the tool bar no longer setting the centre pane's minimum, and the slack between the panes' minima. |
| `test_toolbar.py` | The tool bars of the static models' and schemas' tabs: a tall bar wraps without scrolling, a short one uses fewer rows and scrolls sideways, one row is one row, and no tool is ever left outside the bar at any height. |
| `test_fit.py` | *Ajuster* in the static models tab fitting the figure whatever its size, the four-metre floor applying only to a model whose points span nothing. |
| `test_wheel.py` | The wheel changing a value in a spin box, a combo box or a slider: it must scroll the panel behind them instead, and a scroll bar is the one widget left alone. |
| `test_statics.py` | A static model's source as the export and the window read it: a shear or normal-force release carrying a stiffness keeps its freedom and loses the stiffness with a warning, where it stopped every model's export; a moment release keeps its rotational spring. |
| `test_stallwatch.py` | The window's watch on itself: a planted stall is logged with its frame, a window that answers logs nothing, no thread is started while idle, and a whole-computer stop is logged as «System hitch». The planted stall and the whole-computer stop run in a process of their own (`python tests/test_stallwatch.py <log> <seconds>`, or `hitch`): under the full suite the posted events earlier windows leave behind ran inside the test's own loop. |

### The report, the commands and the editor

| File | Guards against |
|---|---|
| `test_report.py` | The report not compiling as written, in one of the three languages, or at one of the three uniform levels, and an invalid level or language not being refused; and a command compiled on its own saying the wrong thing -- a refusal without the valid ids, `verify` refusing `==`, a connector's words in German in a French report, the forces note losing its semicolons. Slow; skipped when `typst` is not on the path. Since v0.79: an annex cited without §, and a French page's narrow space before the engine's colons and semicolons. |
| `test_commands.py` | The commands tab: every binding of `lib/` placed in a category and every category naming one that still exists, every public command carrying a `///` block, a bullet per argument and at least two examples, **every example compiling** as its own document, the copy of the engine beside the frozen examples matching `lib/`, no example naming an id the project has dropped, and no engine name shadowing a Typst global. |
| `test_doc_comments.py` | The `///` blocks of `lib/*.typ`, which no build ever breaks: a parameter with no bullet, a command hiding its arguments behind a variadic sink, a block without exactly one `->` line, a union not written with `\|`, and a `//` line detaching a block from its `#let`. |
| `test_editor.py` | A report that compiles but cannot be edited: tinymist's language server surviving the analysis of every file of the report and of a call into the engine (v0.60's stack overflow). |

### The harness

| File | Guards against |
|---|---|
| `test_harness.py` | Two runs of the suite at once reaching into each other's files: `tests/.tmp/` partitioned by process id, `cleanup()` removing only its own directory, no second copy of the removal in the runner, and no test writing a depth-dependent `#import`. Since v0.78: `-k` selecting a test by its function name, `Skip` being a skip for pytest too, and no Python file raising a `SyntaxWarning`. |

## Adding one

Write the check where it belongs by concern, not by the file it was found in. If it needs a workbook, build one with `fixtures.workbook.build()` rather than pointing at the engineer's — a test that depends on `Positionen.xlsx` breaks the day a row is edited, and then gets deleted instead of fixed.

A check that caught a real defect keeps the defect in its docstring, with the version it was found in. That is what tells the next reader whether the check is still earning its place.
