# Performance — what Woodcore's start and use cost, measured

What makes Woodcore slow or frozen, measured before anything is changed, and the same measurements after each change (spec `docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md`, REQ-001; the engineer's rule: no optimisation without the measurement that justifies it).

## How it is measured

- `python tests/perf_startup.py [--runs 3] [--json out.json]` — not a test (its name keeps `run_tests.py` from collecting it). Each run is a fresh process on a copy of `tests/projet-exemple` with settings of its own, offscreen: the interpreter, PySide6, `QApplication`, `import woodcore_gui`, `open_project` (lock, seed, the window built tab by tab), the first events, then `rebuild()` — what a language switch and the end of every export run again. Then the export a window starts, `calc/cli.py export --data-only`, whole and by its imports.
- `python -X importtime …` for the imports, `cProfile` for a phase (its attribution inside Qt calls is unreliable: a Python callback run during a Qt call is charged to whatever Python frame was last on the stack — trust it for Python functions, not for `stat`), and experiments that switch one cause off at a time.
- The machine: the engineer's laptop, Windows 11, the checkout in a NextCloud folder, other sessions running — the runs vary by ±40 %; a cause is retained only where switching it off moves the time far beyond that.

## Before (08.10.2026, v0.117 unreleased, commit ae996b6 + the working tree)

### The start, phase by phase (seconds; run 1 first of the session, runs 2–3 warm)

| Phase | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| interpreter | 0.44 | 0.32 | 0.42 |
| PySide6 | 0.51 | 0.27 | 0.57 |
| QApplication | 0.04 | 0.02 | 0.04 |
| `import woodcore_gui` | 4.03 | 3.27 | 4.69 |
| `open_project` (window built) | 17.67 | 12.02 | 21.41 |
| first events | 0.12 | 0.10 | 0.17 |
| `rebuild()` | 12.52 | 14.66 | 19.70 |

Nothing is on screen until `open_project` shows its card (`busy.Splash`): **4–5 s at least after the double-click, 30 s at the first start of a day** (`python -X importtime`, cold: `import woodcore_gui` 29.7 s, of which `openpyxl` 15 s and `numpy` 6.7 s).

The tabs' own constructors add up to 6.5–12 s of the 12–21 s: `tab_fire` 1.2–2.2, `tab_plan` 0.7–1.4, `tab_schema` 0.7–1.3, `tab_statics` 0.7–1.2, `tab_connections` 0.6–1.2, `tab_structure` 0.4–0.8, each member check 0.3–0.6.

### What one cause costs, switched off alone (`open_project`, warm)

| Experiment | `open_project` | of which `build()` | tabs |
|---|---:|---:|---:|
| as it is | 19.2 / 19.8 | 17.9 / 17.5 | 11.7 / 11.2 |
| without the busy card's event filter (`busy._Guard`) | 11.1 | 10.1 | 6.4 |
| without the application style sheet (12 KB) | 8.4 | 6.7 | 5.8 |
| without either | 8.7 | 4.8 | 4.8 |

**Cause 1 — the busy card's event filter (≈ 8 s of 19).** `busy._Guard` is installed on the `QApplication` the first time a card is shown and **never removed**: every event of every widget of the process crosses into Python for the rest of the session — 127 505 calls while the window is built. With the style sheet, building a widget posts polish and style-change events for every child, each one through the filter: the card meant to show the wait doubles it. The same filter taxes every paint, scroll and zoom afterwards (PDF views included).

**Cause 2 — the application style sheet (≈ 3 s more).** 12 KB of QSS (`theme.style_sheet`): Qt re-polishes a widget each time it is added to a layout, a tab or a splitter (`addWidget` 1.4 s, `addLayout` 1.9 s, `addTab` 1.3 s, `setCentralWidget` 1.5 s of own time under the profiler).

**Cause 3 — `import woodcore_gui` (3.3–4.7 s warm, ~30 s cold)**, before any window: `openpyxl` imported at the head of `build_reference` (4–5 s warm, 15 s cold, of which `numpy`), `typst_check`/`urllib`/`http.client` (2.4 s cold), `project` (1.7 s cold), `home_page` (1.5 s cold).

**Cause 4 — `rebuild()` (12.5–19.7 s)**: the whole window built again after every export and every language switch, with causes 1 and 2 in full.

**Cause 5 — work done while building that could wait or move**: the *Affichage* panels built at once (`display_view.install_display`, 10 `DisplayView`, ≈ 5.8 s under the profiler), `connectors_tab` 0.6–1.2 s (its `load`), `statics_tab.restore` → `load` (2.7 s under the profiler), `structure_tab.reload` → `structure.tree` (1.5 s under the profiler), `plan.preload` in a thread importing `pypdf` (2.5 s, holding the GIL against the main thread).

### The export a window starts

`calc/cli.py export --data-only` on the example: **6.6 s**, of which imports ≈ 2.2 s at its head: `export_all` → `registry` → `io_excel` → `openpyxl` (2.0 s, `numpy` 0.6 s) and `pypdf` (0.6 s). Every re-export pays them again, and the window then runs `rebuild()` (cause 4).

## Causes measured afterwards

- **The console window seen at times** (REQ-008, 08.10.2026). The window run under `pythonw`, as the launcher, `Woodcore.pyw` and `Woodcore.exe` run it, an export and the compilation of the three documents asked for, and every window on screen enumerated every 10 ms (`tests/test_no_console.py::test_an_export_and_a_compilation_of_a_windowless_woodcore_open_no_console_window`): **no console window appears**. Each console program started -- python for the export, typst, git -- does get its console host (`conhost.exe`), hidden: `CREATE_NO_WINDOW` gives a host, never a window. What does open a console is **`Woodcore.bat` itself**: a `.bat` double-clicked is run by `cmd.exe` in a window, for the time `where pythonw` and `start` take. `Woodcore.pyw`, beside it, is run by `pythonw` and opens none.
- **The PDF views** (REQ-015, 08.10.2026), on the engineer's own architect's PDF (`01_Total.pdf`, 18 pages, A1):
  - one render of a page holds QtPdf's lock **0.2–0.5 s whatever its size** -- a page's whole 480-pixel coarse render 80–400 ms, a 512 x 512 clip of it 216 ms, a 2400 x 1500 clip 227 ms. A grid of small tiles would pay that for every tile: **D4's fixed-grid tiles would be slower**, and were not built.
  - *Document* view: after a scroll or a zoom, the coarse renders of up to ten pages round the view were asked for **before** the sharp render of the page looked at -- seconds of blur on a document of many heavy pages.
  - *Export* view: each zoom rendered the **whole page at once, in the paint, on the window's thread** -- an A3 at the deepest zoom, 10 500 x 7 400 pixels.
  - *Dessin* view: Qt's `QPixmapCache` is 10 MB by default, less than one cached picture of a full-screen view (19 MB at 1920 x 1080 and 150 %): the SVG layer of the symbols, cached by device, **was drawn again vector by vector at every frame**.
  - A clipped render of a page turned by its `/Rotate` matches the whole render's corner (checked): not the cause of the zones that never sharpen. That cause is still not reproduced off the engineer's screen.

## After

### 1. The guard only while the loop runs free (08.10.2026)

`busy._Guard` is installed while a window is held over an export, a compilation or `run_in_thread`, and taken off when no such hold is left. A window built, a reload, a language switch or a document switch are held with `guard=False`: their loop only turns in `pump()`, which leaves input queued, so the guard had nothing to hold there (`tests/test_busy.py::test_the_guard_is_on_only_while_free_running_work_is_held`).

| Phase | Before (runs 1–3) | After (runs 1–3) |
|---|---|---|
| `open_project` | 17.7 / 12.0 / 21.4 | 11.7 / 11.0 / 11.1 |
| `rebuild()` | 12.5 / 14.7 / 19.7 | 7.1 / 11.1 / 10.8 |

And no event of the session crosses into Python any more once nothing is held: paints, scrolls and zooms included.

### 2. The start screen before the imports (08.10.2026)

`calc/tools/woodcore_start.py` shows its screen after PySide6, the theme and the settings alone, then imports the libraries and the calculation modules that touch no Qt in a thread, the window's own modules on the main thread one by one, and hands over to `woodcore_gui.main`; `Woodcore.exe` (`packaging/entry_gui.py`), `Woodcore.bat` and `woodcore_gui.py` run directly all go through it.

| | Before | After |
|---|---:|---:|
| Screen on after the start (warm) | 4–5 s (the old card, after `import woodcore_gui`) | **0.5 s** (`tests/test_startup.py`, two runs: 0.56 / 0.50 s) |
| `--self-test` of the example, start to quit (1.5 s of it the self-test's own wait) | 17–25 s | 8.9–9.9 s |

### 3. openpyxl only where a workbook is read (08.10.2026)

`io_excel` imports openpyxl when it reads a workbook, `build_reference` when it writes `docs/typst-reference.xlsx` -- and it writes it only where its rows changed since the last time (their digest kept in `%LOCALAPPDATA%\Woodcore\reference-digests.json`, with the file's size and time).

| `cli.py export --data-only`, the example | Before | After |
|---|---:|---:|
| whole run | 6.6 s | 2.6 s (warm, `-X importtime` running) |

The example still imported openpyxl then: its RFEM export was a workbook it read (`rfem_import.csv_tables.read_workbook`). Since 0.117, when the RFEM import was retired (archive/rfem/), no project does.

### 4. The PDF views (08.10.2026)

- *Export* (`sheet_editor.SheetCanvas`): the page rendered by QtPdf's own thread (`QPdfPageRenderer`), once the zoom stands still (120 ms), the image before drawn stretched meanwhile; past 12 megapixels only the part in view and a quarter of the view round it, snapped to 256 pixels so a small scroll asks for nothing. A paint renders nothing (`tests/test_sheet_editor.py::test_a_zoom_never_renders_the_page_on_the_window_s_thread_and_a_deep_one_renders_the_part_in_view`).
- *Document* (`document_view.PageArea.schedule`): the pages in view first -- their coarse render where they have none, then their sharp one --, the pages round them last.
- *Dessin* and the static models: `QPixmapCache` raised to 256 MB by the first SVG layer made (`plan_canvas.ensure_pixmap_cache`).

### 5. The whole start again, every change in (08.10.2026, the working tree before the verification's second round)

`python tests/perf_startup.py --runs 3`, the same script and machine as *Before*, with other sessions running (±40 %):

| Phase | Before (runs 1–3) | After (runs 1–3) |
|---|---|---|
| interpreter | 0.44 / 0.32 / 0.42 | 0.26 / 0.23 / 0.25 |
| PySide6 | 0.51 / 0.27 / 0.57 | 0.37 / 0.24 / 0.27 |
| `import woodcore_gui` | 4.03 / 3.27 / 4.69 | **2.69 / 1.91 / 2.37** (warm: −40 to −50 %, REQ-005's third reached) |
| `open_project` (window built) | 17.67 / 12.02 / 21.41 | 14.06 / 9.66 / 9.95 |
| `rebuild()` | 12.52 / 14.66 / 19.70 | 6.87 / 8.10 / 8.34 |
| `cli.py export --data-only` | 6.6 | 5.5 (imports 4.4, of which openpyxl 1.4: the example's RFEM export is a workbook) |

The tabs' constructors, slowest first (after, runs 1–3): `tab_rfem` 3.35 / 2.19 / 1.26 s -- it reads the example's RFEM workbook (`model_tables` → `csv_tables.read_workbook`), whose import of openpyxl is 1.7 s of it where nothing imported it before; started through the start screen, openpyxl is already imported by its thread; the tab and that cost went with the RFEM import in 0.117 --, `tab_fire` 0.6–0.9, `tab_plan` 0.6–0.7, `tab_connections` 0.3–0.9, `tab_statics` 0.45–0.55, `tab_schema` 0.36–0.61.

The start screen, three starts of the example (`WOODCORE_START_TRACE=1`, `woodcore_gui.py --self-test`, offscreen):

| Run | Screen up | Longest without a frame (between) | Steps (s): config / libraries / calc / typst / window / project / tabs |
|---|---:|---|---|
| 1 | 1.59 s | 1.28 s (Schémas → Moyens d'assemblage) | 0.03 / 2.18 / 0.47 / 0.05 / 1.98 / 0.09 / 12.33 |
| 2 | 1.08 s | 0.97 s (Modèles statiques → Schémas) | 0.04 / 2.57 / 0.50 / 0.05 / 1.54 / 0.06 / 11.35 |
| 3 | 0.83 s | 0.92 s (Moyens d'assemblage → Moments polaires) | 0.03 / 2.49 / 0.59 / 0.06 / 1.64 / 0.08 / 10.61 |

Earlier the same day, with a lighter machine, the longest gap was 0.46–0.53 s and the screen up in 0.50–0.56 s (`tests/test_startup.py`). **REQ-003's 0.25 s is not reached**: the longest gap is always **one tab's constructor**, run whole on the window's thread (Qt builds widgets there only). Between two tabs, and between the plan tab's three panes (`DrawingTab`), the screen gets a frame (`woodcore_start.pump`). Bringing the gap under 0.25 s means cutting the constructors of `connectors_tab`, `schema_tab`, `statics_tab` and the polar moments into steps of their own -- a work package of its own (`docs/open-questions.md`).

## Threads kept beside `tasks.TaskRunner` (ARCH-002)

`calc/tools/tasks.py` is where new long work goes: a function in a pool, its answer or its exception back on the window's thread, a stale result dropped by its key, the project's writers one at a time, blocking (the card) or in the background (the chip). These were not moved into it, each for its reason:

| Where | What | Why it stays |
|---|---|---|
| `busy.run_in_thread` | the work a held window waits for | blocking by nature: it turns its own event loop under the card; `TaskRunner(blocking=True)` puts its card through the same `busy` |
| `pdf_pane._Job`, `sheet_editor._Job` | a Typst preview, a sheet's compilation (`QThread`) | a Typst process watched to its end, which `pdf_pane` kills itself when a snippet must run first; both announce themselves to `tasks.activity()` |
| `variables_tab.Read` | the variables read from a compiled document (`QThread`) | a result of its own shape, the tab's alone; quick |
| `document_view._Loader`, `plan_canvas.DiskCache.save`, `drawing_tab` `plan_model.preload` | a document's pages and layers, a render written to the disk cache, pypdf imported beside the window | each already off the window's thread with a generation number or nothing to answer; moving them changes nothing measured |
| `drawing_tab._run_layer_export` | the plan's layers written into `data/` | a **writer**: the window's export waits for it (`finish_layer_export`, ARCH-003, `tests/test_plan_tabs_v0117.py`) |
| `QPdfPageRenderer` in `document_view`, `plan_canvas`, `sheet_editor` | page renders | QtPdf's own thread; PDFium's single lock makes one renderer per view the right count (§4) |
| `commands_tab` `example-render` | a command's examples compiled one at a time | its own queue, in order, one Typst at a time |
| `woodcore_start._import_in_thread` | the libraries imported while the screen turns | before any window: `TaskRunner` is in the window's modules it waits for |
| `stallwatch`, `typst_gui`/`update_gui`/`woodcore_gui` checks | the watchdog; the network checks of Typst, of an update, of PyPI | a watchdog must not be in the pool it watches; the checks answer through Qt signals already |

ARCH-002's cancellation is not in `TaskRunner`: no caller needed it (`pdf_pane` kills its own process); a stale result is dropped instead.

## One rule for every subscript (2026-10-20)

`math-eval` (lib/subscript.typ; spec 2026-10-20-indices-et-niveaux, UI-001, ARCH-001) rewrites the subscripts of every symbol and formula before Typst evaluates it -- one `str.replace` with a regex, a source without `_` returned at once. Measured on the engineer's machine (8 cores, Windows 11, Typst 0.15.1), the example project's report compiled at `--input uniform=3`, four runs each, the engine before and after in two copies of the project: **4.66 s before, 4.77 s after, +2 %**, under the 5 % the spec allowed. The level of each line read from lib/line-levels.json (`line-level`) costs nothing measurable beside it.

## The metadata every command emits (2026-10-15)

Every `#var`, `#eq`, `#verify` and `#var-domain` emits a `metadata` labelled `<woodcore-var>` from its context (`wc-meta`, lib/formula.typ; spec 2026-10-15-calculs-deplies-balises-figures-natives, REQ-004), which `calc/domains/unfold.py` reads by `typst eval`. Measured on the example project's report, three compiles each on a cloud session, `wc-meta` emitting and then stubbed to `none`: 2.27 s (minimum) and 2.32 s (mean) with it, 2.21 s and 2.40 s without -- the difference is within the spread of one run, and no change was needed.
