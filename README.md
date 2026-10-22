# Structural calculation report engine (timber / SIA-EC5)

Generates structural calculation reports from Excel, Python, and Typst: Excel holds the project input, Python validates it and runs the calculations into JSON, and Typst renders the report from that JSON at one of three detail levels (client / engineer / review), in German, French or English.

Some calculations belong to Excel rather than to Python — the snow load is calculated in the `SL-*` sheets of the Belastungsannahmen workbooks and the wind load in their `WL-*` sheets, both only read from there. Either way the report displays the same traced record, and every value states the source that produced it, down to the cell.

For the full architecture, data model, and design decisions, see **`docs/README.md`**, the index of the reference documentation (`CLAUDE.md` is the short entry point the assistant reads first). This file is just a quickstart.

Language split: documentation, Typst comments, and all file/folder names except the section files are in English. The section file names and the report content itself (headings, title page, body text) are in German, since that is the language of the actual reports.

## Structure

**Woodcore is the program, and a project is a folder of its own** (v0.82). This repository holds the code and nothing of any project: the norms under licence and the client's data never enter it. A project folder holds the project and nothing else, named by its `<name>.woodcore` file; the program reads and writes it wherever it lies.

The program — this repository:

```
Woodcore/
├── Woodcore.bat                 # Woodcore from its sources: the start page, or Woodcore.bat "<path>\Musterprojekt.woodcore" for that project
├── woodcore-cli.bat             # the report built from a terminal: woodcore-cli export --project "<path>\Musterprojekt.woodcore"
├── templates/forms/             # the layout templates («templates de forme»): neutral, compact, bfh -- the look of the three documents, put in a project's Template/ folder
├── templates/documents/         # the content templates («templates de fond») of the convention, the base de projet and the report: their sections, objects and texts
├── templates/projet/            # the folder skeleton of a new project (woodcore-cli new --form … --content-cu … --content-bp … --content-rs …, «Nouveau projet»)
├── packaging/                   # the installed program: python packaging/build.py -> dist\ (installer, or zip); auto_build.py and hooks/ rebuild it at each new version; publish.py publishes it
├── website/                     # the website on Cloudflare Pages: python website/build.py (.github/workflows/site.yml publishes it)
├── calc/                        # Python pipeline: validation, calculations, JSON export (export_all.py), cli.py, project.py
│   ├── norms/                   # every norm value a Python calculation uses, one JSON per table or clause
│   ├── domains/section.py       # a position's section, read once from its section type and dimension
│   ├── i18n/strings.json        # every word the engine prints, in German, French and English
│   └── tools/woodcore_gui.py    # Woodcore's window, and home_page.py its start page
├── lib/calc-engine.typ          # Typst display layer (show-calc, show-input, show-check, show-connector, show-connector-resistance, show-polar-moment, show-plan, show-plan-legend, show-live-load, show-static-model, show-schema, get-*, project-info, woodcore-document)
├── lib/formula.typ              # var, var-line, eq, verify, unit, var-domain, val, var-unit: calculations written by hand, with their units
├── lib/i18n.typ                 # the engine's language, and the glossary every word it prints comes out of
├── lib/timber.typ               # member, the verify-* checks of SIA 265 4.2: a position's line, and for timber its design values
├── schemas/                     # JSON schemas -- the contract between Python and Typst, the .woodcore file's included
├── examples/                    # the commands tab's frozen worked examples and their rendered pages (docs/typst/command-docs.md §10sexies)
├── requirements.txt             # openpyxl, pypdf, PySide6 -- pinned to the versions this was built with
└── tests/                       # every check the engine relies on: python tests/run_tests.py
    └── projet-exemple/          # the project the tests work on: a real project anonymised, without its workbooks
```

A project — here `Musterprojekt/`, beside `Woodcore/` — laid out as a new one is:

```
Musterprojekt/
├── Musterprojekt.woodcore            # names the project: its name, its people (company, author, checker, client ...), where its parts lie
├── Musterprojekt.woodcore.lock       # while a window has it open: who, where, since when -- another window then opens it read-only
├── Woodcore-Datei/positions.json  # the positions, entered in Woodcore's Positions tab (a Positionen.xlsx is imported once, then moved to _Archiv/)
├── *Belastungsannahmen*.xlsm    # every load, one sheet per case: SL-* (snow), WL-* (wind), EL+AL-* (permanent)
│                                #   -- every .xlsm/.xlsx whose name contains "Belastungsannahmen" is read
├── Statischer Bericht (typst)/  # the report, and the Typst root
│   ├── Statischer Rapport.typ   # entry point: title page (from the .woodcore, through project-info()), outline, includes all sections
│   ├── Statischer Rapport.pdf   # the finished report, written beside its .typ (v0.87; one level above until then)
│   ├── config.typ               # page/text/heading setup (one function, plain set/show rules)
│   ├── commands.typ             # every command of the engine: each .typ starts with #import "../commands.typ": *
│   ├── Sections/                # file names are English, report content is German
│   ├── Images/                  # figures, plans, photos (#image("../Images/xxx.png") from a section)
│   └── _woodcore/               # generated, never edited: data/ (the export), docs/typst-reference.xlsx, out/,
│                                #   and lib/ with the norm tables #distance reads -- the engine, copied here at every export, read-only, with a VERSION naming it
├── Woodcore-Datei/              # what Woodcore's window draws: connectors/, connections/, plans/, statics/, details/
├── _Archiv/                     # one zip per export, with a flat copy of its PDF
└── .vscode/settings.json        # Tinymist's on-save export sent to the same PDF
```

The engine sits inside the project because Typst reads nothing outside its root and finds the export by a relative path: with its copy beside `data/`, a report compiles in Tinymist without the program, and the project carries the engine that produced its PDF. The export refuses to overwrite a copy another version wrote or one edited by hand unless asked to (`--update-engine`, or the dialog of Woodcore's window), and never overwrites one written by a newer program.

## Build

From the project's folder, or anywhere with `--project`:

```bash
woodcore-cli export --project Musterprojekt.woodcore                 # the report as written -> "Statischer Rapport.pdf"
woodcore-cli export --project Musterprojekt.woodcore --level 1       # force the base level for this run (overrides still apply)
woodcore-cli export --project Musterprojekt.woodcore --uniform 2     # every call at level 2, overrides ignored
woodcore-cli export --project Musterprojekt.woodcore --all-levels    # also the three uniform variants in _woodcore/out/
woodcore-cli export --project Musterprojekt.woodcore --skip-data     # compile only, against the data already exported
woodcore-cli export --project Musterprojekt.woodcore --lang fr       # the same report in French (de, fr, en)
woodcore-cli check  --project Musterprojekt.woodcore                 # the whole export, writing nothing
woodcore-cli new "D:\Projekte\Halle Nord"                        # an empty folder made a new project
woodcore-cli new "D:\Projekte\Halle Nord" --form bfh             # ... with the BFH layout template (neutral, compact, bfh); --content-cu / --content-bp / --content-rs choose each document's content template
```

`woodcore-cli` is `Woodcore\woodcore-cli.bat`, or `python calc/cli.py`, or `woodcore-cli.exe` once Woodcore is installed. Without `--project` it takes `WOODCORE_PROJECT`'s, else the one `.woodcore` in a folder beside `Woodcore/`. It replaces the `build.ps1` and the `Makefile` the project folder carried until v0.82.

Without `--level`, no `--input level=` is passed at all: the base detail level is the one the document itself declares (`Statischer Rapport.typ`, `sys.inputs.at("level", default: ...)`), and every per-call `level:` override written in `Sections/` applies on top — so the deliverable comes out *as written*. `--level N` forces the base for one run. `--uniform N` is different in kind: it renders **every** call at N and ignores the overrides, which is what makes `out/report-N.pdf` one level throughout — `--all-levels` writes those three. See `docs/typst/report-engine.md §4.

The export runs first (Excel -> validated JSON in `_woodcore/data/`, with `project.json` naming what produced it) and the compile only if it passed, so Typst is never compiled against unvalidated data; then the archive, a zip in `_Archiv/`. *Exporter PDF* in Woodcore's window does the same, in the same order.

In VS Code, Tinymist's own default (`$dir/$name`) exports the PDF beside `Statischer Rapport.typ`, which is that same place: `.vscode/settings.json` sets no `tinymist.outputPath` since v0.87 (it was `$dir/../$name`, one level above, while the PDF lay at the top of the project folder). Pin `Statischer Bericht (typst)/Statischer Rapport.typ` as the main file once (command palette -> *Typst: Pin the main file*), or each section compiles on its own and exports a stray PDF.

## The installed program

Woodcore is run from its sources day to day (`Woodcore.bat`). A version to hand round, or to keep, is built on demand:

```bash
python packaging/build.py
python packaging/build.py --installer-only   # the installer alone, from the program the last build left
```

It builds, in an environment of its own under `%LOCALAPPDATA%\Woodcore\build\`, `Woodcore.exe` (the window) and `woodcore-cli.exe` (the command line) with Typst inside, and `Woodcore-Launcher.exe`; runs them on a copy of the example project; and writes `dist\Woodcore-<version>-setup.exe` with Inno Setup 6 (`winget install --id JRSoftware.InnoSetup -e --scope user`), or `dist\Woodcore-<version>-win64.zip` without it. The installer needs no administrator, installs each version beside the others in `%LOCALAPPDATA%\Programs\Woodcore\<version>\`, and lets a double-click on a `.woodcore` start the launcher, which opens it with the version it asks for (*Propriétés du projet*), else the newest — or with these sources, where the window's *Fichier* menu says so. `docs/conventions/build-and-release.md §12 has the rest.

A new version's installer is also built by itself (v0.87): a git `post-commit` hook, `packaging/hooks/post-commit`, starts the build in the background when a commit changes `VERSION` in `calc/project.py` and `dist\` holds no installer for it — of that commit, in a clean checkout of its own under `%LOCALAPPDATA%\Woodcore\build\checkout\`, never of the working tree, so a version's commit must carry its new files. The commit does not wait for it, and its log is `dist\build-<version>.log`. The hook is activated once per clone:

```bash
python packaging/auto_build.py install     # git config core.hooksPath packaging/hooks
python packaging/auto_build.py status      # is it active, does a build run, is HEAD's installer in dist\
python packaging/auto_build.py start       # build HEAD's installer by hand, in the background (--force replaces one already there)
python packaging/auto_build.py uninstall   # deactivate it
```

`WOODCORE_NO_AUTOBUILD=1 git commit …` skips it for one commit.

## Publishing, and the website

The website, https://woodcore.pages.dev/, is built by the workflow `.github/workflows/site.yml` on every push to the default branch and published on Cloudflare Pages: what Woodcore is, the download, a tutorial and every command with its examples, in French, German and English (`website/`). An installed Woodcore reads its `version.json` at every start and offers a newer version (v0.89). To publish a version once its installer is built:

```bash
python packaging/publish.py --dry-run      # what would be sent: the installer of VERSION, from dist\
python packaging/publish.py                # uploads it to a Release of the public releases repository (token: WOODCORE_GITHUB_TOKEN, fine-grained, Contents: read and write) and records it in website/releases.json
```

Write the version's notes into `website/releases.json` first, in the three languages, then commit and push that file: the workflow checks the installer on its Release and puts `version.json` on the site. The installer is not in the site (Cloudflare Pages takes no file over 25 MiB): the download page links to its Release. The workflow needs the secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` (Settings › Secrets and variables › Actions).

```bash
python website/build.py --serve            # the site into public\, served on http://localhost:8000/
```

## Checking

```
cd Woodcore
python tests/run_tests.py
```

Every check the engine relies on, in one command: the two duplications that cannot be caught by a compiler (the force arrows drawn in both Python and Typst, the allowed-value lists restated in `validation.py`), the rules the Excel readers enforce, the polar moment against the HB2 method sheet, and the report compiling in three languages at three levels. They run on a copy of `tests/projet-exemple/`; the few that need a workbook read the project beside the code (`WOODCORE_REAL_PROJECT` names another) and are skipped where there is none. No framework to install — it is standard library, and `pytest` runs the same files where it is there. `docs/conventions/testing.md §11ter says what each file guards and why.

Before the first run on a new machine:

```
python -m pip install -r requirements.txt
```

The three packages, at the versions this report was verified with. Woodcore's window checks them on every start and offers an update when one is available.

## Personalizing

- **Title page** — the project's name, number, client, address, company, author and checker are the `.woodcore` file's, read through `project-info()`; edit them there, and the title page and the PDF's own metadata follow at the next export. The date and the layout of the page stay in `Statischer Rapport.typ`.
- **Section content** — fill in each file under `Sections/` with the actual text, tables, and figures. The section list is a generic starting point; rename, reorder, split, or drop files as needed for the project at hand.
- **Writing the report in another language** — **two settings, in two files**, because there are two questions:
  - `#set-report-language("fr")` in `Statischer Rapport.typ` sets the language **the engine prints in**: the labels of the calculations, the tables' headings and notes, the captions, the figures' legends, the STE legend of a position plan. `woodcore-cli export --lang fr` (or `--input lang=fr`, or the export menu of Woodcore's window) does it for one run without touching the document.
  - `#let doc-lang = "fr"` (with `doc-region`) at the top of `config.typ` sets the language **Typst itself works in**: «Abbildung»/«Fig.», «Tabelle»/«Tableau», the table of contents' title, the hyphenation, the quotation marks. It is a property of the report, not a build flag — edit it beside the paper size.

  **What you write is touched by neither**: the headings of `Sections/`, the document's title, your prose, and any `title:` or `caption:` you give a call. Nor is what you entered: the workbooks' descriptions and text values («Flachdach», «Ja»), material and sheet names, the positions, the citation of a norm. The one thing that *is* translated although it comes from a workbook is a value **the norm itself names** — the Geländekategorie, the category of Nutzfläche — in the norm's own wording. To correct a word, or to check one against your own edition, there is exactly one file to open: `calc/i18n/strings.json`, where each block names the edition its French and English came from (`docs/typst/language.md §4bis).
- **Adding a section** — create a new file in `Sections/`, give it a top-level heading (`= Title`), and add a matching `#include` line in `Statischer Rapport.typ`.
- **Adding a figure** — `#figure(image("../Images/xxx.png"), caption: [...])` inside the relevant section file.
- **Adding a load case** — copy the relevant sheet in a Belastungsannahmen workbook, keeping its prefix (`SL...` for snow, `WL...` for wind, `EL+AL...` for permanent loads), fill it in and save. The next export picks it up; the report prints it where `Sections/004-einwirkungen.typ` names it, or through an `ids(domain)` loop (`docs/domain/calculation-domains.md §3.3).
- **Load workbooks** — every `.xlsm`/`.xlsx` directly in the project folder whose name contains `Belastungsannahmen` is read (`Belastungsannahmen.xlsm`, `02_Belastungsannahmen.xlsm`, ...), in file-name order; each export prints which ones it took. A sheet name must be unique across all of them, since it is the id the report addresses the case by. Move a copy you do not want in the report out of the folder: every matching file counts.
- **Using a live load (Nutzlast)** — nothing to enter: the values are SIA 261's Tabelle 8, read by the category of Nutzfläche. Write `#show-live-load("A1")` in a section — level 1 the category with q_k and Q_k, level 2 the same line saying what the category is, level 3 the whole table with that row set apart. Inside a sentence, `#val("q_k", domain: ("live-load", "A1"))` prints `2 kN/m²`, `type: "val"` the value alone and `type: "unit"` the unit alone; `value-of("live-load", "A1", "q_k")` gives the bare number to compute with. The categories are `A1`, `A2`, `A3`, `B`, `C1`, `C2`, `C3`, `D`, `E`, `F`, `G`, `H`; `E` (Lager- und Fabrikationsflächen) has no values in the norm — SIA 261 8.2.2 leaves them to the project — so the call is refused and those values are written in the report itself (`docs/domain/loads.md §3.3septies).
- **Adding a new kind of load** — write one module under `calc/domains/` declaring `DOMAIN`/`LABEL`/`ACTION` (`"permanent"` or `"variable"`)/`ENGINE`/`SHEET_PREFIX` and a `read_instances(cells, sheets)`, then add it to `DOMAIN_MODULES` in `calc/registry.py`. A load read from a norm table rather than from a workbook declares `ENGINE = "norm"` and `SHEET_PREFIX = None` and exposes `build_instances()` instead, its values living in `calc/norms/` (`live_load.py` is the worked example). Whether it *reads* a sheet Excel already computed (like `snow.py` and `wind.py`) or *calculates* from what the sheet holds (like `dead_load.py`) is a per-domain decision — never reimplement in Python a calculation the sheet already performs (`docs/domain/loads.md §3.3bis-§3.3ter).
- **Adding a position calculation** — add project data in Woodcore's Positions tab (`Woodcore-Datei/positions.json`), extend the relevant module under `calc/` (see `docs/architecture/layout.md §11) and call `show-calc("<domain>", "<position>")` in the section file. Note this half is currently dormant — see `docs/open-questions.md §14.
- **Adding a connector** — in Woodcore's window. Draw the joint first in the *Schémas* tab: its pieces, each naming a position of the Positions tab, and its fastener markers (or points ticked «moyen d’assemblage»). Then in the *Moyens d’assemblage* tab (*Connecteurs* until v0.79) click *Nouveau*, choose the kind of fastener (only *Broche*, the Stabdübel, calculates today), the schema, the assembly, each member's element and the fasteners it carries. A member's strength class and moisture class follow its position at every export and may be written over, which the form marks in orange. *Enregistrer* writes `Woodcore-Datei/connectors/<id>.json` and exports it at once; `Sections/003-baustoffe.typ` lists it, and `#show-connector-resistance("<id>")` prints its shear resistance after SIA 265 6.2.1 (`docs/domain/connectors.md §3.3nonies, §7bis). Connectors left `Positionen.xlsx` in v0.68, and its `Positions Connectors` and `data_*` sheets were deleted in v0.79.
- **Adding a connection** — a polar-moment calculation, in Woodcore's *Moments polaires* tab, drawn on a detail schema of the *Schémas* tab: click *Nouveau calcul* — it opens on a schema, its linear elements as the members and every marker ticked. Give it a *Nom* (its ID is made from it and may be written over) and a *Description*; choose each member's element of the schema, the reference member the others' angles are counted from (x and z are the schema's, x to the right and z down), the fasteners among the schema's markers and points ticked «connecteur», the rotation centre (the fasteners' centroid, a fixed point, or a centre drawn in the schema) and the directions of N and V (angles from x towards z). The figure and I_p,x, I_p,z, I_p update as you edit, and a preview draws the forces for trial N, V, M and names the most stressed fastener(s). *Enregistrer* writes `Woodcore-Datei/connections/<id>.json` and exports it at once. In a section, `#show-polar-moment("<id>", N: 7.5, V: 25, M: 6.6)` — N, V in kN, M in kNm, positive anticlockwise — prints the force in the most stressed fastener (level 1), the figure with every fastener's forces drawn to one scale and the formulas (level 2), and before them the rotation centre, the positions and the angles between the members, after them the force in every fastener, as distributed and again in the most unfavourable superposition (level 3) (`docs/domain/connections.md §3.3quinquies). It was called `show-fastener-forces` until v0.32, and `show-fastener-polar-moment` until v0.38.
- **Adding a position plan** — in Woodcore's *Plan de position* tab, import the architect's document into the *Documents* list (PDF, PNG/JPG, SVG, DXF or DWG; a DWG is converted by the free ODA File Converter if it is installed, ezdxf reads the DXF). It opens in the centre as a continuous, scrollable view of all its pages (zoom buttons or Ctrl+wheel, 1…n pages per row); tick the pages that become plans, draw the crop and the calibration there, turn a page by ±90° and switch the PDF or CAD layers on and off. A plan is named «P01 – name – storey» and shows only its crop (*Afficher toute la page* shows the rest); it is saved automatically when you leave it.
  - **Drawing.** Draw the axes: a vertical one takes a letter and a horizontal one a number, and an oblique one is drawn with two clicks. A new axis is named by where it lies: drawn between A and B, it becomes B, and B becomes C. Then draw the STE symbols with the tools, or with their letters: V, H, W, T, S, A, D, Ö (or O), B, M, L. Two toggles make the points snap to the axes and to the elements already drawn, and Shift keeps a segment at 0°, 45° or 90°. A beam (T) and a bracing member (A) are one straight line: the second click ends it.
  - **Scale and size.** Drag the crop the report will show. Give the scale: 1:n for a PDF, or *Calibrer* on two points of known distance. The three sliders set the size of the strokes, the points and the texts.
  - **Numbers.** Each element's number is a position of the Positions tab (`Woodcore-Datei/positions.json`), chosen from a list. A tool whose letter has no position creates a blank position (id and type only). Identical elements share their number, so a tool draws the same one every time: renumber a column S003 and every column drawn after it is an S003. The storey is chosen from a list in the project's language or typed freely; the numbering character of the ids (U, 0, 1…) is a separate field, proposed from the storey.
  - **Moving a number.** Where a number falls on another symbol or number, drag it clear with *Sélection*. It keeps following its element, a thin line ties it back once it has left it, and «Remettre à sa place» puts it back.
  - **Saving.** *Enregistrer* writes `Woodcore-Datei/plans/<id>.json` and exports the plan at once. `Sections/003-baustoffe.typ` shows every plan before the positions.
  - **In a section.** `#show-plan("Pavillon")` prints a plan, with its scale bar and its legend under it. `highlight: "T001"` puts a halo under that position, `detail: true` shows its surroundings, and `axes: false` leaves the axes out. `#calc-block("T001", plan: auto)[...]` shows the plan's detail in a block's header (`docs/domain/position-plans.md §3.3sexies).
  - **Requirements.** Exporting a plan drawn on a PDF needs pypdf (`python -m pip install pypdf`), reading DXF files needs ezdxf 1.4.4 (both pinned in `requirements.txt`).
- **Adding a static model** — a statisches System, in Woodcore's *Modèles statiques* tab: click *Nouveau*, then draw. The tool bar is seven named boxes — **Éléments** (point, barre, câble, ressort), **Appuis** (encastrement, appui fixe, appui roulant), **Articulations** (rotule, N-libre, V-libre, ressort de rotation), **Charges** (ponctuelle, linéaire, trapèze), **Cotations** (horizontale, verticale, parallèle, angle), **Navigation** and **Historique**. Everything can be typed instead, in the five lists **under the drawing**: points, barres/câbles/ressorts, charges ponctuelles, charges linéaires, cotations. The frame is metres, **x to the right and z down**, as it is for a connection.
  - **Drawing.** The grid's step follows the zoom (5, 1, 0.5, 0.1 m, with heavier lines every 10, 5, 5 and 1) and the pointer snaps to it, to the nodes, to the middles and to the members; *Grille* forces one step, *Accrocher* turns it off. As in AutoCAD, resting the pointer on a point acquires it: the cursor then locks to 0°, 45° or 90° from it, to the axis or the normal of a member meeting there, or to where that ray crosses the line of a member extended — **Tab** then takes the distance and **Enter** puts the point down, the new end becoming the next anchor. The wheel always zooms about the pointer and the middle button always pans, whatever tool is chosen; *Ajuster* (F) zooms on everything. The pointer's coordinates, the x/z axes and the tool's hint are written inside the drawing.
  - **Supports** go in the points list, with their angle, or in the selected point's panel; one just drawn is turned by the pointer in steps of 45° until the next click sets it. An **appui fixe** and an **appui roulant** are hinges, so each carries the white circle a rotule carries, and a further column and panel row say **where that circle sits** — *Articulation de la barre*, the pin the bar itself turns about, drawn on the node; or *Barre continue*, a bar running over the support, the pin set back until the circle just touches the bar and the support hanging under it. An encastrement has no pin and is not offered the choice. **Articulations** belong to an end of a member: draw one with its own tool, set it in that member's panel, or pick it from the point's own row in the points list where just one member ends there — rotule, effort tranchant, effort normal, or a ressort de rotation in kNm/rad, whose centre is that same white circle. A node carrying one is not drawn as a dot: the symbol is the mark there, and so are an encastrement's hatched wall and a shared pin. A **translational spring is a member**, not an articulation, with its own stiffness in kN/m.
  - **What is drawn at a node** is what stands there. A **rotule** is the white circle; an **effort normal** is a sleeve of two lines along the member with the two ends seen sliding **inside** it, parted by a break about as wide as a bar is thick; an **effort tranchant** is two bars across the member with the ends coming up to them and stopping; a **ressort de rotation** is the rotule with a coil around it. A break is always centred on the node. The black dots on the plain points are the window's own, to say where one may click: they are not articulations and the report draws none.
  - **A point load takes two clicks**: the first names the point it acts on, the second the **barre** its angle is counted from. Its **décalage** says how far along that member it is drawn — `2.5` is metres, `0.5l` is midspan — which is how a load is put in the middle of a beam without inventing a point there. Several **line loads** on one member stand one above the other rather than on top of one another, each with its name and value inside its own band.
  - **A load's value is optional**, and it is either typed (a number and its unit) or **read from the export**: choose *Variables* and pick the domain, the case and the variable (`snow-load` → `SL-Dach1` → `q_k11`), and the figure then follows the workbook by itself. A **facteur** and a **constante** beside them write a design value as `0.8 · q_k11 + 0.2`, and a **description** says what it is; the note under the figure then gives the expression and the number it came to, so the arrow's value can be checked. A load with no value at all is drawn at full length and shows its name alone. Where the action is in kN/m² and the system carries kN/m, tick *Multiplier par une largeur d'action b_e*: the value is multiplied by b_e and one metre comes off the unit (kN/m² → kN/m, kN/m → kN). **The whole model can carry one b_e**, in the right-hand panel — it applies to every load, is written once at the foot of the figure with its description, and a load's own b_e overrides it. Each load shows nothing, its name, its value, or both.
  - **A dimension takes three clicks**: where it begins, where it ends, and then how far from those two its line is to be drawn. Four tools — **horizontale** (the distance along x), **verticale** (along z), **parallèle** (the true distance between the two ends) and **angle**. A click that lands on a point of the model anchors the dimension to it, so the dimension follows that point when it is moved; a click on nothing keeps its own place. The **angle** tool's first two clicks name the two barres instead — the one under the pointer is drawn with the one already picked, so you choose them by eye — and its third gives the arc its radius and **which of the four sectors** is measured: the one the click falls in, so the 90° below and to the left and the 90° below and to the right are each written by pointing at them. **The dimension is drawn while you make it**, from the first click: the far end follows the pointer with its length already read out, then the line follows the pointer to where it will be drawn, and an angle's arc moves between sectors as the pointer does — what the pointer shows is what the click writes. Its witness lines cover **a quarter of the way** from the dimension line towards what they measure and stop there, the rest being left blank. The value printed is what the model measures, to the millimetre and to a tenth of a degree; write something in the **texte** cell of the cotations list, or in the panel, and that replaces it (`l = 6.00`). A negative radius on an angle writes that sector's reflex, the 270° rather than the 90°. Échap gives a half-drawn dimension up, and Tab + a distance + Enter types the third click.
  - **Saving.** *Enregistrer* writes `Woodcore-Datei/statics/<id>.json` and exports the model at once, as `data/statics.json` and `data/statics/<id>.svg`. `Sections/005-tragwerksanalyse.typ` shows every model under *Statische Systeme*.
  - **In a section.** `#show-static-model("R01")` prints the figure; `width: 80%` sizes it, `loads: false` prints the bare system in the same frame at the same scale (so it can stand above the same system with its actions), `dimensions: false` leaves the dimensions out the same way — the two are independent, so one system can be printed dimensioned and bare and then undimensioned with its actions — and `highlight: "B1"` puts a halo under a point, a member, a support, an articulation, a load or a dimension (`docs/domain/static-models.md §3.3octies). It draws a system and solves nothing: no reactions, no N/V/M, no checks.
- **Finding what to type** — double-click `Woodcore.bat` and choose the project on the start page (or drop a `.woodcore` file on the `.bat`): a window (PySide6 — `python -m pip install PySide6` if it is missing) lists every load, permanent and variable, with its value and the workbook, sheet and cell it comes from, and copies the Typst call that prints it (double-click a row, or right-click for every variant); French, German or English (`docs/ui/window.md §10quater). `Statischer Bericht (typst)/_woodcore/docs/typst-reference.xlsx` (generated on every export) lists the same calls — every valid `show-*()` call for the current project, with a paste-ready `example_call` column — start from the `Calculations` sheet, which lists every `(domain, instance)` pair.
- **Page setup** — margins, font size, heading numbering, and the footer live in `config.typ` if they need to change.

## Notes

- The table of contents (`#outline()`) and page numbering are Typst's built-in defaults — no manual page-range bookkeeping.
- Every `show-*()` call is addressed the same way: `(domain, instance)` — `show-calc("snow-load", "SL-Dach1")`. `show-calc` renders a whole calculation (inputs, then each step, result last); `show-input` pulls a single intermediate value out of one.
- See `docs/README.md` for the full data model (positions, calculation domains), the report-level mechanism, and the reasoning behind every architectural decision.

## Licence

© 2026 Florian Lamprecht — woodcore@pineo.ch. Woodcore is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version (SPDX `GPL-3.0-or-later`). The licence's text is `LICENSE` (the same as `legal/licenses/GPL-3.0.txt`, which the installed program carries), presented in `legal/LICENSE-fr.txt`, `legal/LICENSE-de.txt` and `legal/LICENSE-en.txt`; the source of every version is published at https://github.com/When-I-hit-the-wall/Woodcore-Publish. The licences of the third-party software the installed program carries are in `legal/THIRD-PARTY-NOTICES.txt` (`python packaging/notices.py` writes it).
