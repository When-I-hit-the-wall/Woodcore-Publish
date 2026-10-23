# Repository and project layout

> The folders of the program, of a project, and of calc/.
>
> Moved verbatim from CLAUDE.md (§11) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 11. Detailed layout

Since v0.82 the program and the project are folders of their own, and only the program is a git repository (§13). The split is by *what a thing belongs to*: what the engineer edits and hands over belongs to the project, whose folder holds nothing else; what generates a report belongs to the program, which reads and writes a project wherever it lies, named by its `.woodcore` file (`calc/project.py`). Beside them, the reference library.

```
305-typst-static-report/
├── Woodcore/                      the program -- the one git repository, shared with developers
├── Musterprojekt/                      a project -- in NextCloud, in no repository
├── ExternalFiles/                 the reference library: norms, literature, course documents, third-party tools (§11bis) -- in no repository
├── ancien-depot-v0.82.bundle      the repository as it stood before the move, whole: history, norms and project included -- kept apart, shared with nobody
└── _ancien-git/                   that repository's .git, renamed rather than deleted -- the engineer's to remove
```

**How long a module may be (v0.117, issue #30).** A Python module of `calc/` aims at **1000 lines** and may not pass **1500**: past that it is hard to read through, to test on its own and to change from two sessions at once without a conflict -- 22 modules had passed it, `woodcore_gui.py` at 3742 lines. `tests/test_module_size.py` refuses a module over 1500 that the list below does not name with its reason; what justifies one is a single class or table that cannot be cut without cutting what it says. **A module is split by moving its text, never by rewriting it** -- the same lines, the same names, the same behaviour -- into modules beside it named after it (`statics.py` → `statics_geometry.py`, `object_panes.py` → `object_panes_table.py`): the module split imports every moved name back on one line marked `# split out of this module (issue #30)`, so `statics.snap` and `woodcore_gui.MainWindow` are still read where they always were. What moves takes with it every top-level name it reads (the set moved is closed), so a part never imports the module it came from and no import goes round in a circle. **A class too long for one module** is cut into **mixins** by subject (the engineer's choice, spec D-14): `class MainWindow(WindowExportMixin, …, QMainWindow)`, each mixin in a module of its own; a method keeps its text, `self` reaching what the others define. What a test assigns on a module (`structure.write`, `woodcore_gui.TABS`, `woodcore_gui.relaunch`) stays in that module, so the assignment still reaches every caller. `tests/test_module_imports.py` imports every part in a fresh interpreter, before the module it came from, and every module of `calc/domains/` with PySide6 out of reach. A test that reads a module's text reads its parts too (`conftest.module_source`). **The Typst of `lib/` follows the same ceiling since 19.10.2026** (spec 2026-10-19-base-saine-nettoyage, lot 0): a file of `lib/` over 1500 lines is named below with its reason, and is split into files beside it (`calc-engine.typ` → `calc-engine-<subject>.typ`, the first one a façade that imports the others back), flat in `lib/` because a `json("../data/…")` is read from the file that calls it; the engine a project carries in `_woodcore/lib/` follows from the one list of the engine's files.

<!-- module-size-exceptions: the modules of calc/ over 1500 lines, each with its reason (tests/test_module_size.py) -->
- `lib/formula.typ` -- the hub that imports every other file of the engine and the formula language (`var`, `eq`, `val`, `verify`) with its one evaluator: cut, the evaluator's helpers would be read across files that each import the other
<!-- /module-size-exceptions -->

The program:

```
Woodcore/
├── Woodcore.bat                   Woodcore from its sources: the start page, or the project given as its argument (§10quater)
├── Woodcore.pyw                   Woodcore from its sources double-clicked with no console at all, run by pythonw -- what Woodcore.bat cannot avoid for the instant cmd takes (v0.117)
├── woodcore-cli.bat               the report built from a terminal: export, check, sync-engine, new, migrate (§12)
├── templates/projet/              what a new project starts from: the report, its sections, .vscode -- copied by woodcore-cli new and «Nouveau projet» (§12)
├── templates/documents/           what a new convention d'utilisation and a new base de projet start from: <cu|bp>/<template>/template.json and, per language, the document's own folder -- its entry, structure.json and Sections/<id>.typ -- a convention of 59 sections and a base of 72 in three languages since v0.112 (§3.3octodecies, §12)
├── templates/styles/              the look of the three documents, their one config.typ: `neutral` (the default) and `compact`, each a config.typ and a style.json naming it in three languages (§3.3octodecies, §12, v0.112)
├── packaging/                     the installed program: build.py, the two PyInstaller specs, the launcher, the Inno Setup script (§12)
│   ├── auto_build.py              the installer of a new version built by itself: install / uninstall / status / start / hook (§12, v0.87)
│   ├── publish.py                 an installer built, uploaded to a Release of the public releases repository on GitHub and recorded in website/releases.json (§12, v0.89, v0.117)
│   ├── notices.py                 legal/THIRD-PARTY-NOTICES.txt written from the pinned versions and legal/licenses/; build.py refuses a stale one (§12, v0.91.1)
│   └── hooks/                     core.hooksPath once activated: post-commit, and a .gitattributes keeping it LF (§12, v0.87)
├── dist/                          gitignored: what a build hands over -- the installer, or the zip without Inno Setup -- and build-<version>.log of a build the hook started (§12)
├── CLAUDE.md                      the short entry point: principles, workflow, and the index of docs/
├── docs/                          the reference, one file per domain (docs/README.md maps every § to its file), docs/requirements/ the specifications
├── .claude/                       the project skills (big-feature, small-feature, requirements, architecture-review, implementation, verify-requirements) and agents; its settings.json calls tests/bootstrap.py at the start of a cloud session (v0.117, issue #26)
├── website/                       the website, https://woodcore.pages.dev/ (§12, v0.89, v0.117): build.py, its words (strings.json), its pages (content/<lang>/: the download page, the tutorial, changes.md and changes/<version>.md), the versions published (releases.json), site.json, assets/
├── .github/workflows/site.yml     the workflow that builds the website, checks the latest installer on its Release and publishes the site on Cloudflare Pages (§12, v0.117)
├── .github/workflows/tests.yml    the test suite at every push and pull request: Linux always, Windows on a push to master, each machine prepared by tests/bootstrap.py (§12, v0.117, issue #27)
├── CHANGELOG.md                   the journal of every version, newest first (§15)
├── legal/                         © 2026 Florian Lamprecht: the licence in French, German and English (LICENSE-<lang>.txt), THIRD-PARTY-NOTICES.txt and the licence texts it is written from (licenses/) -- shipped with the program and published on the site (§12, v0.91.1)
├── README.md                      the quickstart
├── prompt-audit.md                the periodic audit prompt: calculations against the reference workbooks, translations of the report and Woodcore, every button, dead commands and duplicates, CLAUDE.md against the code -- run it every few days
├── 000-Audits/                    one report per run of prompt-audit.md, AAMMJJ-HHhMM-audit.md -- versioned, since each audit is compared with the one before it
├── calc/                          the pipeline, detailed below
├── norm-library/                  the norms shipped with Woodcore: the PDFs of the engineer's `norms` repository but its Litteratur/ and the SZS C4/C5 tables, frozen into the installer beside calc/, never copied into a project (§11bis, v0.124, issue #94)
├── lib/i18n.typ                   the report's language, and the glossary every word the engine prints comes out of (§4bis)
├── lib/calc-engine.typ            the engine's display layer, split by subject into calc-engine-core.typ (the `get` and `ids` abstraction, the data loaders, `domain-file`, `doc-tables`), -records, -display, -drawings (the five `image-*` and the drawing primitives), -connections: each importing the one before, calc-engine.typ re-exporting them, imported whole by formula.typ (§10bis)
├── lib/formula.typ                var/eq/verify/domain/unit/calc-defaults/var-table/find/sync: the variables a report writes, the unit algebra that computes with them, the fine display arguments and their presets (lib/display-presets.json), the unit each dimension is printed in -- and the hub that imports every other file of the engine (spec 2026-10-21-commandes-typst-refonte: `val`, `var-unit`, `var-line`, `var-domain` merged or retired)
├── lib/units.json                 the units formula.typ reads -- prefixes, bases, superscripts, the unit of each dimension, the units offered for each -- and calc/units.py reads too: one table for the report and the «Formules» tab (v0.117)
├── lib/number.typ                 how a number is printed: `display-number`, the one rule of every display (3 decimals, powers of ten past 99 999 and below 0.1 where needed), and `fmt-decimals`, the pure rounding it is built on -- calc/number_text.py is its Python twin (v0.120, UI-002, UI-003)
├── lib/subscript.typ              how a subscript is printed: `normalize-subscripts` (every subscript of letters, digits, Greek names, commas and spaces one upright quoted block, `N_(R d)` → `N_"Rd"`) and `math-eval`, the one door every symbol and formula is evaluated through -- calc/typst_math.py's `normalise` is its twin (v0.120, UI-001)
├── lib/figure-palette.json       the figures' colours and font, by token -- calc/domains/svg_draw.py and lib/calc-engine-core.typ (`figure-colour`) read it: one palette for the drawing engines and the report (v0.120, D5)
├── lib/line-levels.json           the level each line of a calculation is printed from, domain by domain (lines, kinds, patterns, `*`): read by calc/line_levels.py and the export, which give each line of a calculation its level
├── lib/distance.typ               #distance: SIA 265's minimum distances and timber thicknesses in mm for a diameter, read from calc/norms/ (§10bis, v0.87) -- imported by name into formula.typ
├── lib/bibliography.typ         #show-bibliography and #cite-norm: every norm the report cites, named in full at the end -- read from calc/norms/norms.json and from the project's own references.bib (§10, v0.99) -- imported by name into formula.typ
├── lib/document.typ               `show-norm-list`, the list of the norms a document cites -- the one parametric command of a document left, its tables, fields and images raw Typst since the spec 2026-10-21-commandes-typst-refonte (REQ-019)
├── lib/positions.typ              `#position(id, category-show:)`, one position on a line in its type's colour (spec 2026-10-21-commandes-typst-refonte, REQ-015); the list of the positions is written once in raw Typst by Python (calc/domains/list_files.py)
├── lib/sheet.typ                  the export sheets: the page's show rule `sheet(kind:)`, whose `show place` rule tells the editor where each object labelled `<sheet-…>` stands, and `image-section`, `image-legend`, `image-titleblock` -- every object a raw `#place` the sheet editor writes (Q-013, Q-015)
├── schemas/                       JSON schemas (position/positions-index/connector-source/connectors/calculations/connection-source/connections/plan-source/plans/statics-source/statics/schema-source/schemas/journal-source/journal/formulas/annex-source/annex-excerpt/annexes/member-check-source/checks/woodcore-project/project/template/structure/document-template); sync.schema.json, the record of what the documents share (v0.117, issue #33)
├── examples/                      the frozen worked examples: a snapshot of an export, a config.typ, one .typ per example and its rendered page, all versioned;
│                                  plus a generated, gitignored copy of lib/ that puts the engine beside them (§10sexies)
├── requirements.txt               the three packages outside the standard library, pinned to the versions this report was verified with (§11ter)
├── typst-version.txt              the one place the pinned Typst is written (§11ter, v0.117, issue #26)
├── typst-sha256.json              the SHA-256 of each official archive of that Typst, which tests/bootstrap.py refuses an archive without
└── tests/                         every check the engine is allowed to rely on: python tests/run_tests.py (§11ter)
    ├── bootstrap.py               a machine prepared for the suite in one command, standard library only: the packages, Qt's libraries on Linux, the pinned Typst (§11ter, v0.117)
    └── projet-exemple/            the project they work on: a real project anonymised, without its workbooks -- laid out in three documents since v0.111; tests/fixtures/legacy_example.py rebuilds the one report it was; its convention and its base are the full templates since v0.112
```

A project laid out as one report (`project.DEFAULT_LAYOUT`: every project until v0.111, and any whose `.woodcore` states no `layout.typst_root`; a `.woodcore` may name other places in its `layout`, each inside the project's folder):

```
Musterprojekt/
├── Musterprojekt.woodcore              names the project: schema_version, format, name, and optionally number, client, address, company, author, checker, layout, woodcore_version, content_templates (the content template each document was made from, v0.122, additive) and gui (the editor tabs' empty folders; `katalog` until v0.96, still read)
├── Musterprojekt.woodcore.lock         while a window has the project open: who, on which machine, since when -- removed when it closes (§10quater)
├── Positionen.xlsx                hand-edited source of truth (Positions Element, data_type) -- NO loads (§8), NO connectors (§7bis)
├── *Belastungsannahmen*.xlsm      hand-edited too: every load, one sheet per case -- every .xlsm/.xlsx whose name contains "Belastungsannahmen" is read (§3.3)
├── Verbindung.xlsm                the engineer's connection workbook the Stabdübel resistance is checked against, cell by cell (§3.3nonies, §11ter)
├── Verbindungen.xlsx              the engineer's Verbindungen workbook, whose I_p,x / I_p,z naming the polar moment follows (§3.3quinquies)
├── 01_Pläne/ … 04_Skizzen/        the office's own folders: the architect's plans a position plan is drawn over (§3.3sexies), sketches and details -- read by no module
├── .vscode/settings.json          Tinymist's settings; no outputPath since v0.87, its default writing the same PDF (§12)
├── Statischer Bericht (typst)/    the report, and the Typst root
│   ├── Statischer Rapport.typ     the entry point: #show: woodcore-document, a title page from project-info(), the outline, the sections
│   ├── Statischer Rapport.pdf     the finished report, written beside its .typ since v0.87 -- at the top of the project until then (§12)
│   ├── references.bib          # what only this project cites: a manufacturer's ETA, an office handbook, a course document -- a BibTeX subset lib/bibliography.typ reads, named by Sections/007's `project:` (§10, v0.99)
│   ├── commands.typ               every command of the engine, re-exported from _woodcore/lib/: the one import each .typ starts with (§10bis)
│   ├── config.typ, Sections/*.typ, Images/    the report itself
│   └── _woodcore/                 generated, never edited by hand
│       ├── lib/, calc/i18n/strings.json, calc/norms/, VERSION   the engine and the fourteen norm files #distance reads, copied at every export, read-only, VERSION naming its version and each file's hash (§12)
│       ├── data/                  the export: generated JSON and figures, project.json among them (§12) -- never hand-edited
│       ├── docs/typst-reference.xlsx   generated command/variable catalog, never hand-edited (§10ter)
│       └── out/report-1|2|3.pdf   one PDF per detail level (§3.7), written by --all-levels
├── Woodcore-Datei/                what Woodcore draws, one file per object, the id being the file name
│   ├── connectors/<id>.json       one connector each, with its own shear-resistance calculation, drawn on a detail schema, which it names (§3.3nonies)
│   ├── connections/<id>.json      one polar-moment calculation each, drawn on a detail schema too, often the same one (§3.3quinquies)
│   ├── plans/<id>.json            one position plan each (§3.3sexies)
│   ├── statics/<id>.json          one static model each (§3.3octies)
│   ├── details/<id>.json          one connection detail each -- **the one drawing** a connector and a polar moment are both calculated on (§3.3decies)
│   └── journal.json               the report's revision journal, ONE file rather than a folder of them (§3.3terdecies, v0.99)
│   ├── lists.json                 the order the engineer gives the window's lists by drag and drop, and the «Formules» tab's folders -- the window's alone, never read by an export (calc/list_order.py, schema lists 1.0, issue #15)
│   ├── checks/<id>.json           one member check each (member-check-source 1.0, 1.1 where a field follows a variable, v0.117): its position, the values it follows or states, the force and, for a compression, its contact -- resolved by the export into data/checks.json and computed in the report by #show-check-member (§3.3unvicies)
│   ├── fire/<id>.json             one fire-protection plan each, schema 2.0 (a 1.0 file is read as it is and written as 2.0 when saved), that follows a position plan or has a frame of its own on a document's page (§3.3vicies, v0.115)
│   └── annexes/                   the documents the report draws on from outside (v0.115, §3.3undevicies): sources/<id>.pdf copied into the project beside its record <id>.json, and excerpts/<id>.json, a region of one page each, anchored on the bookmark of its title -- the convention, the base and the report each show the excerpts they choose
└── _Archiv/                       one zip per export and a flat copy of its PDF beside it, the PDF not in the zip (§12)
```

A project in three documents (since v0.111: a new project's layout and a migrated one's; its `.woodcore` states `layout.typst_root` and every key of the layout, `project.full_layout`). The Typst root is the project's own folder, and the tree above holds as it stands wherever this one does not say otherwise:

```
Halle Nord/
├── Halle Nord.woodcore            states the layout in full: typst_root ".", report/pdf, report_cu/pdf_cu, report_bp/pdf_bp, generated, images, sources, archives (a project made before 0.117 may state rfem_export too: ignored, and said at every export)
├── Positionen.xlsx, *Belastungsannahmen*.xlsm, …   as above
├── .vscode/settings.json          Tinymist's settings, stating "tinymist.rootPath": "${workspaceFolder}" (§12)
├── config.typ, commands.typ, references.bib   the three documents' shared files -- the Typst root is THIS folder
├── Images/                        the pictures the three share
├── Formules/                      the calculation domains of the «Formules» tab, one <id>.typ each -- the id the file's name --, printed by #include "/Formules/<id>.typ" from any document (+ archives/; folders and order in Woodcore-Datei/lists.json, issue #15); a report alone keeps it in its own folder, its Typst root (v0.117)
├── _woodcore/                     generated, never edited by hand, ONE for the three: lib/, calc/, VERSION, data/ (journal.json, journal-cu.json and journal-bp.json among it), docs/, out/, and stamps/ -- what each compile read, one record per document, gitignored (calc/stamps.py)
├── 1_Convention d'utilisation/    the convention d'utilisation (CU): Convention d'utilisation.typ (+ its PDF), structure.json, sync.json (what it shares with the other two, §3.3octodecies), Sections/<english-id>.typ (+ Sections/archives/)
├── 2_Base de projet/              the base de projet (BP): Base de projet.typ (+ its PDF), structure.json, sync.json, Sections/ (+ Sections/archives/)
├── 3_Rapport de statique/         the rapport de statique (RS), the report: Statischer Rapport.typ (+ its PDF) -- its entry keeps its name -- and Sections/001-….typ -- a sync.json beside its entry where it shares
├── Woodcore-Datei/                what Woodcore draws, as above, and the three journals: journal.json (RS), journal-cu.json, journal-bp.json
└── _Archiv/                       per document, <timestamp>-<mode>.zip and a flat copy of its PDF; a migration's own folder, migration-<timestamp>/ (§12)
```

**A project laid out by folders** (since v0.119, issue #64, spec `docs/requirements/completed/2026-10-15-structure-projet-dossiers.md`): a new project's layout and a migrated one's, schema_version 1.1 of its `.woodcore`, which states `layout.config` beside every key above (`Project.has_folders`). The engineer asked for what configures the documents to lie apart, for what is Woodcore's and need not be opened to lie apart, then the three documents, then one folder per kind of domain -- «dans le dossier Snow, il y aura dedans à chaque fois un fichier typst par domaine de neige». Every name is English and fixed whatever the project's language; only `config` is a key of the file, every other folder below is `calc/project.py`'s (`DOMAIN_FOLDERS`, `KIND_FOLDERS`, `DRAWING_FOLDERS`), and every one of them is made with the project and made again where it is missing (`Project.ensure_folders`):

```
Halle Nord/
├── Halle Nord.woodcore            schema_version 1.1, the layout in full: typst_root ".", config "000-Typst-Config", the documents' entries and PDFs, generated "000-Woodcore", images, sources "000-Woodcore/sources", archives "000-Woodcore/archives"
├── .vscode/settings.json          Tinymist's settings, "tinymist.rootPath": "${workspaceFolder}" (§12)
├── 000-Typst-Config/              config.typ, commands.typ, title.typ, references.bib and the form's Template/ -- every document imports "/000-Typst-Config/commands.typ" (§10bis)
├── 000-Woodcore/                  what is Woodcore's: the engine (lib/, calc/, VERSION), the export (data/, docs/, out/, stamps/), and inside it the sources (sources/, Woodcore-Datei/ before) and the archives (archives/, _Archiv/ before) -- which no walk of the export takes in (`Project.generated_excludes`)
├── 100-Service criteria agreement/   the convention d'utilisation: its entry named in the project's language, structure.json, sync.json, Sections/
├── 200-Basis of design/           the base de projet, as above
├── 300-Statical report/           the rapport de statique: Statischer Rapport.typ, Sections/
├── Domains/                       the domains the engineer writes in the «Domaines» tab, one <id>.typ each (Formules/ before) + archives/
├── Images/                        the pictures the three share
├── Positions/                     positions.json, the source, and Positions.xlsx written beside it at every change, never read (calc/positions_store.py)
├── Permanent-loads/               one <id>.typ per permanent load (calc/domains/domain_file.py), Exports/Figures/ (a build-up's drawing)
├── Variable-loads/                Snow/, Wind/ -- one <id>.typ per snow load, per wind load
├── Plans/                         Position-plan/ and Fire-plan/, each: Imported Plans/ (the documents a plan is drawn on, copied there at their import) and Exports/ (its export sheets; Figures/, the figures and reduced backgrounds the export draws) -- and bundles.json, the PDF bundles of both
├── Statics/, Details/             Exports/Figures/ (the figures of the static models, of the schemas)
├── Connectors/, Connections/      one <id>.typ per connector, per polar moment; Exports/Figures/
├── Timber-checks/                 Tension/, Compression/, Bending/, Shear/, Torsion/, Buckling/, Lateral-torsional/, Deformation/, Vibration/ -- one <id>.typ per member check, its stub until it is unfolded -- and unfold.json
├── Steel-checks/                  Class/, Tension/, … Splice/ -- one <id>.typ per steel check
├── Scripts/                       <id>.py, the script, and <id>.typ, which prints it
└── Appendix/                      the annexes' PDFs under the names they were added under, Exports/ (the excerpts and the annexes the export cuts from them)
```

**The export's figures lie in the tabs' folders, their one copy** (lot 2, D-10, D-17): every figure the export draws -- a plan's overlay and its background reduced to its page, a fire plan's, a static model's, a schema's, a connection's, a connector's, a dead load's build-up -- in its tab's `Exports/Figures/`, the annexes' excerpts in `Appendix/Exports/`; `000-Woodcore/data/` keeps the JSON alone, which names each figure from the Typst root, `/Plans/Position-plan/Exports/Figures/P01.svg` (`project.FIGURE_KINDS`, `figures_folder`, `Project.figures_dir`, `exports_dir`; each export's `schema_version` raised by one where it does). One writer puts them there, `engine.Figures.write` over `engine.write_managed`: written whole and LF, an unchanged file left alone, and **removed only what the last export's JSON listed** -- the folder is one the engineer sees, and a file of his in it is his. One function of the engine reads them, `figure-path` (lib/calc-engine.typ): a name from the root as it stands, a name without its slash under `../data/` -- every export before 0.119, and a project laid out before, whose figures stay in `data/<kind>/` as they always were. **The documents a plan is drawn on** are copied at their import into their tab's `Imported Plans/` under their own name, the original untouched (`plan_documents.import_file`); a file of that name with other bytes replaces the copy only once the engineer confirms, the plans drawn on it following (D-18); one written over there from outside Woodcore is read again as its tab is shown and at the export (`refresh_all`). **An annex's PDF** lies in `Appendix/` under the name it was added under (`file`, annex-source 1.1, `annex.copy_pdf`), read again where it was written over (`refresh_sources`). A document or an annex added before is copied there by the migration and by every export after it (`plan_documents.adopt`, `annex.adopt`), its record rewritten to name the copy. The stamps and the archive of a document take in these folders (`stamps.enumerated`, `archive_export.members_of_document`).

**A domain's file** is the calculation written out whole (spec 2026-10-21-commandes-typst-refonte, REQ-017, ARCH-011): `calc/domains/unfold.py` writes it from the export when the domain is saved in its tab and at every export -- a member check, a steel check, a load, a connector, a polar moment, a script --, its lines kept in step three ways with a base beside it, and a section prints it by `#include domain-file(kind, id)` (`data/domain-files.json`). It is the engineer's once written: a line he changed is his, said and never overwritten. `calc/domains/domain_file.py` keeps the one reconciliation (`sync`), run at every export and after every save of a tab that makes domains: a file whose domain is gone is archived where it is a stub an earlier Woodcore wrote, said where it is the engineer's. Until then a domain's file was a stub, `#show-calc("snow-load", "neige")`, which a version since recognises byte for byte and writes over (`unfold.LEGACY_STUBS`).

**A project laid out before** -- three documents in `1_…`, `2_…`, `3_…` with what they share at the top, or a report alone -- is read and compiled exactly as before, and is offered its migration as it opens (`calc/project_migrate_folders.py`, the second step of `calc/project_migrate.py` for a report alone): renames, nothing copied or deleted; every path rewritten where it would stop reaching its target; the three documents compiled before and after and compared; everything undone on a failure, and on request (`woodcore-cli migrate --rollback`).

The Python pipeline itself, inside `Woodcore/`:

```
calc/
├── i18n/
│   ├── strings.json         # every word the engine prints, in German, French and English (§4bis) --
│   │                        # the one place they are written down, read by Python here and by lib/i18n.typ
│   ├── commands.json        # the French and German of every public command's documentation, unit by unit, each matched on its English (§10sexies, v0.86)
│   ├── reference.json       # the reference's categories -- their names and the line introducing each -- and the words it says beside every command, in three languages: read by the commands tab and the website alike (§10sexies, v0.94)
│   └── strings.py           # reads and checks it; LANGUAGES, text(), template(), term(), translate()
├── norms/
│   │                           # EVERY value a Python calculation -- or, since v0.87, Typst's #distance -- takes from a norm, one JSON
│   │                           # per table or clause, flat, named <norm>-<year>-<table or clause>-<designation>.json (v0.77) -- and one reader per norm:
│   ├── sia261.py               # SIA 261:2020 -- Tab. 8 (the Nutzlasten, §3.3septies) and Anhang A Tab. 28-30 (mean unit
│   │                           # weights, stored and read by no calculation)
│   ├── sia261-2020-tab08-nutzlasten.json, sia261-2020-tab28-raumlasten-baustoffe.json,
│   │   sia261-2020-tab29-flaechenlasten-bedachungen.json, sia261-2020-tab30-raumlasten-lagergueter.json
│   ├── sia260.py                   # SIA 260:2013 -- Anhang A Tab. 2, the Reduktionsbeiwerte ψ0, ψ1, ψ2 of buildings, snow as the formula in h0 as the norm prints it: kept for the load combinations, shown by no table (§3.3octodecies, v0.112)
│   ├── sia260-2013-tab02-reduktionsbeiwerte.json
│   ├── sia263.py               # SIA 263:2013 -- Tab. 1 (S235..S460) and Tab. 2 (4.6..10.9), both read off a render of
│   │                           # pp. 18-19; Tab. 3 deliberately absent (its «Stifte» are not a timber Stabdübel)
│   ├── sia263-2013-tab01-baustaehle.json, sia263-2013-tab02-schrauben.json
│   ├── sia261_snow.py          # SIA 261:2020 chapter 5 -- s_k, C_e, Figur 2 to 4, Anhang D (issue #36)
│   ├── sia261_wind.py          # SIA 261:2020 chapter 6 and the 37 building tables of Annexe C, c_red of Figur 9 (issue #37)
│   ├── sia265.py               # SIA 265:2021 -- the tables AND the coefficients inside its formulas, checked on reading
│   ├── sia265-2021-tab01-gamma-m.json, -tab03-feuchteklassen, -tab04-eta-w, -tab08-vollholz, -tab09-brettschichtholz,
│   │   -tab22-lochleibungsfestigkeit, -tab24-abstaende, -tab25-kser, -tab45-kbeta-holz-holz, -tab46-kbeta-stahl-holz,
│   │   -2.2.6-eta-t, -5.3.6.2.2-fachwerk, -6.1.4.2-k-red, -6.1.4.4-fliessmoment, -6.2.1.1-k-alpha, -6.2.1.3-schlupf;
│   │   and #distance's (v0.87): -tab27-holzdicken-naegel, -tab28-abstaende-naegel, -tab32-holzdicken-naegel-vorgebohrt,
│   │   -tab33-abstaende-naegel-vorgebohrt, -tab36-holzdicken-schrauben, -tab37-holzdicken-schrauben-vorgebohrt,
│   │   -tab38-abstaende-schrauben, -tab39-abstaende-schrauben-vorgebohrt, -tab40-abstaende-schrauben-axial,
│   │   -tab41-abstaende-ringduebel, -6.4.1.1-nageldurchmesser, -6.5.2.3.1-schraubendurchmesser (tab24 extended)
│   ├── vkf.py, vkf-2016-symbole-brandschutzplan.json   # the AEAI/VKF sheet of symbols of the fire-protection plan: its fire resistances, escape-route marks, doors and their colours (§3.3vicies, v0.115)
│   ├── szs_c5.py, szs-c5-2018-edv-kurzbezeichnungen.json   # SZS C5:2018's 24 families of steel sections, codes and names only -- no profile table (§7, v0.94)
│   ├── norms.py, norms.json    # the documents the engine can name in full: designation, full title, edition, publisher and `kind` per entry, each read off the edition's own title page in  (§10, §11bis, v0.99) -- a catalogue and not a list to print
│   ├── library.py              # where a shipped norm's PDF is: norm-library/ beside the program (project.APP_ROOT), or WOODCORE_NORMS_LIBRARY (§11bis, v0.124)
│   ├── excerpts.py             # the excerpts a tab of calculation shows: per edition the file and the chapter, per excerpt its page, box and words, German the fallback (v0.124, issue #94)
│   ├── sn_en_14592.py          # SN EN 14592+A1:2012 -- f_u,k of a Stabdübel, S355, 510 N/mm² (the engineer's value;
│   └── sn-en-14592-2012-fu-k-stabduebel.json   # the edition is not in the library, so no page is cited yet)
├── domains/                     # one module per calculation topic; a load domain
│   │                            # declares DOMAIN/LABEL/ACTION/ENGINE/SHEET_PREFIX and a
│   │                            # read_instances(cells, sheets) -- or, read from a norm table,
│   │                            # SHEET_PREFIX = None and build_instances() (§3.3, §3.3septies)
│   ├── figure_style.py           # the three factors a figure is set with, and which of them each kind of entry
│   │                             # may state over the drawing's: one table, read by the plans, the static models
│   │                             # and the detail schemas (§3.3quaterdecies, v0.99)
│   ├── snow.py                  # reads the SL-* sheets' inputs, computed by snow_source; what the sheet computed compared (§3.3bis, v0.120)
│   ├── dead_load.py             # computes gk/ak from the EL+AL-* layer tables (§3.3ter)
│   ├── wind.py                  # reads the WL-* sheets' inputs, computed by wind_source; what the sheet computed compared (§3.3quater, v0.120)
│   ├── loads_names.py           # the snow and wind values renamed in v0.120, by roof and table, and the cells a sheet shows each in (§3.3bis)
│   ├── loads_migrate.py         # a project's sections, scripts and sources taken to those names when it is opened; the export's refusal (§3.3bis)
│   ├── dependency_graph.py      # which object reads which: built at every export, data/dependencies.json, what changed and what it touches, circles across kinds (§3.3quinvicies, issue #71)
│   ├── dead_load_source.py      # a build-up of loads/dead/<id>.json, weighed and summed by dead_load's own arithmetic (§3.3ter, issue #35)
│   ├── dead_load_svg.py         # the drawing of a build-up: bands to scale, heights, widths and spacings dimensioned (§3.3ter)
│   ├── materials.py             # the three libraries a layer is weighed with: SIA 261 Anhang A, Woodcore's materials library, the project's (§3.3ter)
│   ├── snow_source.py           # a roof of loads/snow/<id>.json, its snow computed from SIA 261 chapter 5 (§3.3bis, issue #36)
│   ├── snow_svg.py              # the sketch of a snow load's disposition, Figur 3 (§3.3bis)
│   ├── wind_source.py           # a building of loads/wind/<id>.json, its wind computed from SIA 261 chapter 6 and Annexe C (§3.3quater, issue #37)
│   ├── live_load.py             # the Nutzlasten, one instance per category of SIA 261's Tabelle 8,
│   │                            # built from norms/sia261-2020-tab08-nutzlasten.json -- no workbook (§3.3septies)
│   ├── section.py               # a position's section read once from its section type and its dimension -- rec, cir, pla, clt, an SZS C5 family -- into the record's `section` (§7, v0.94)
│   ├── connector.py             # a connector from connectors/<id>.json: its checks, the timber it resolves
│   │                            # against the positions, and data/connectors.json with its figures (§3.3nonies)
│   ├── dowel.py                 # the shear resistance of a Stabdübel connection, SIA 265 6.2.1 and Anhang A --
│   │                            # one module per kind of fastener, and the first of them
│   ├── connector_svg.py         # a connector's two figures and the tool bar's swatches, as SVG text
│   ├── connection.py            # a connection's geometry and polar moment, from connections/<id>.json and the
│   │                            # detail schema it names; builds data/connections.json -- not a load domain (§3.3quinquies)
│   ├── connection_svg.py        # a connection's figure: the schema's own drawing (schema_svg.body) plus the
│   │                            # numbered fasteners, the centre, the x/z pair, the moment's arc and the arrows
│   ├── lines.py                 # a line without ends, a point and an angle: through two points, parallel at a distance -- the position plan's construction aids (issue #18)
│   ├── plan.py                  # a position plan from plans/<id>.json: its checks, sheet, geometry, snapping,
│   │                            # numbering, and data/plans.json with its files -- not a load domain (§3.3sexies)
│   ├── plan_geometry.py         # split out of plan.py (issue #30): lengths, areas, centroids, the axes and their names, hits, the snapping index
│   ├── plan_background.py       # split out of plan.py (issue #30): a background's format, storey, page size, file state and hash, its path
│   ├── plan_svg.py              # a plan's STE symbols and its legend's swatches, as SVG text: Woodcore's canvas and the report's
│   ├── plan_centres.py          # a plan's stiffness centre S and mass centre M, computed from its bracing walls and its outline and stored nowhere: the modes and their powers, the walls, the reasons, the warnings, the export's block -- no Qt (§3.3sexies, issue #54)
│   ├── plan_clip.py             # what Ctrl+C takes from a plan and Ctrl+V puts down on another: the clip, its placing (base point, scale), the numbering of the elements pasted, what the target cannot hold -- for the position plan and the fire-protection plan, no Qt (§3.3sexies, issue #61)
│   ├── statics.py               # a static model from statics/<id>.json: its checks, its register, its geometry, its
│   │                            # dimensions, its
│   │                            # snapping and its AutoCAD-style tracking, the influence width its loads are
│   │                            # multiplied by, and data/statics.json with its figures -- not a load domain (§3.3octies)
│   ├── statics_geometry.py      # split out of statics.py (issue #30): where a member's points, a load and a dimension stand, what a click hits, what the pointer snaps and tracks to
│   ├── statics_svg.py           # a static model's drawing, as SVG text: Woodcore's canvas and the report's figure
│   ├── statics_svg_layout.py    # split out of statics_svg.py (issue #30): where everything of the figure stands -- its scale, its strokes and texts, its labels' frames, a release's cuts -- before anything is drawn
│   ├── schema.py                # a connection detail from details/<id>.json: its checks, its register, its geometry, its
│   │                            # dimensions, its snapping and its tracking, and data/schemas.json with its figures --
│   │                            # a drawing, not a calculation (§3.3decies)
│   ├── schema_geometry.py       # split out of schema.py (issue #30): an element's outline, sides, width and caption, its aids and fasteners, the dimensions, what a click hits, snapping and tracking
│   ├── schema_edit.py           # split out of schema.py (issue #30): moving, turning, mirroring, duplicating, splitting and merging elements
│   ├── schema_svg.py            # a detail's drawing, as SVG text, at its real size in mm: Woodcore's canvas and the report's figure
│   ├── script.py                 # a script of the project: read, run in a process of its own, and its named results exported (§3.3sexdecies, v0.100)
│   ├── script_runner.py          # what runs inside that process: the API a script is given, and the guard that refuses a write
│   ├── annex.py                  # the annexes: sources and excerpts read and checked, the bookmarks of a PDF read, an excerpt found again in a new version of its source, cropped as a one-page PDF, and data/annexes.json with the pages the annexes carry (§3.3undevicies, v0.115)
│   ├── formula_domain.py         # a calculation domain of the «Formules» tab: its file Formules/<id>.typ read and written between its tag -- commands and the engineer's own Typst between them --, its id renamed, duplicated, archived and restored (ArchiveBackend), its keys, the formula typed, what it computes (calc/units.py), data/formulas.json (v0.117, issue #15)
│   ├── links.py                  # a field that follows a variable of the export (issue #42, §3.3duovicies): its shape beside the field, units by calc/units.py, factor and offset, the last value kept with a warning, what a consumer may name -- no Qt, no file read
│   ├── figure_text.py            # a text placed with the Text tool of the four drawing engines (issue #43, §3.3duovicies-bis): its token text and variables, what it prints now, its last values, its drawing -- no Qt
│   ├── svg_text.py               # the one text engine of the figures (D-19): Arial's widths, a subscript cut and set, a text measured and drawn -- the static models', the schemas' and the texts'
│   ├── svg_draw.py               # how every drawing engine writes SVG: a coordinate (`number_at`), a text escaped, a colour of lib/figure-palette.json (`colour`, `colours`, `FONT`) (v0.120, D5, D6)
│   ├── contracts.py              # SourceDomain and ExportDomain: what a domain offers, as two Protocols, held by tests/test_domain_contracts.py (v0.120, C5)
│   ├── unfold_display.py         # «Affichage» of a domain's file: its elements, a line's display, the figure, the domain's level written into the file (v0.124, issue #94)
│   ├── timber_calc.py            # the lines of a member check, each an engine var (and step), and their projection as compute()'s rows (§3.3undecies, v0.120)
│   ├── member_check.py           # a member check from checks/<id>.json: read and checked, resolved against the positions (what it follows, whether it can be calculated and why not), the Typst of a draft, data/checks.json -- and `compute`, the instant calculation of the window's results, which the report does not read (§3.3unvicies, v0.117)
│   ├── fire.py                   # a fire-protection plan from fire/<id>.json: its checks, the upgrade of a 1.0 source, its frame (own or following a position plan), detach, rotate_source, measuring and hit tests, and data/fire.json with its figures per language and its legend lines (§3.3vicies, v0.115)
│   ├── fire_svg.py               # a fire-protection plan's drawing and its legend's swatches, as SVG text: Woodcore's canvas and the report's figure
│   ├── plan_pages.py             # the plans of both kinds drawn on a page of an imported document: which they are, the page turned and both kinds with it, both exported -- no Qt (§3.3vicies, v0.115)
│   ├── plan_tracking.py          # the tracking of the plan tabs, pure: the polar rays in the sheet's frame, the lock, the preference among plan points, ray crossings and edges, the distance typed, and the snap index with the storey lines and boxes (§10quater, v0.116)
│   └── (bending.py and combinations.py stood here until v0.59, uncalled since
│       v0.11: both carried norm values hardcoded and their labels in English,
│       so they were deleted rather than left to be woken up wrong. Deflection
│       and fire were never written. Section 14 says what each needs.)
├── registry.py                   # the domain list and the load-workbook name pattern; finds the
│                                 # workbooks by name, each domain's sheets in them by prefix,
│                                 # takes a norm domain's instances from its own table, and
│                                 # assembles data/calculations.json (§3.3, §3.3septies)
├── engine.py                     # Calculation class, norm/ref helpers, schema-conforming JSON export (§3)
├── list_order.py                 # the order of the window's lists and the «Formules» tab's folders, Woodcore-Datei/lists.json: read, checked, written; a Store the window holds, read only where the project is (issue #15)
├── project.py                    # where the program is and where the project is: the .woodcore file, project.current(), the engine copied into a project (sync_engine, engine_state) and what produced an export (record) -- v0.81, v0.82; and since v0.111 the paths of the three documents (has_modes, document_typ, document_pdf, document_dir, journal_file_for, structure_file, full_layout)
├── build_reference.py        # generates docs/typst-reference.xlsx; its call_* functions are the
│                             # one place a Typst call is spelled out (§10ter)
├── build_reference_lib.py    # split out of build_reference.py (issue #30): the public commands of lib/ read -- signatures, /// blocks, parameters, examples, categories
├── build_reference_calls.py  # split out of build_reference.py (issue #30): the Typst call each row of the reference workbook offers, one function per command
├── usersettings.py           # %APPDATA%\Woodcore\settings.json and %LOCALAPPDATA%\Woodcore\: the recent projects, the Typst-Katalog's taken over once (v0.83)
├── (build_reference*.py and usersettings.py: calc/tools/ until v0.120 -- the export and the window both import them, so they live where both look, G6)
├── number_text.py                # lib/number.typ's twin: `display` (the report's rule) and `trimmed`/`exact`, the one copy of the number trimming the domains wrote four times (v0.120, UI-003)
├── units.py                      # the unit algebra of lib/formula.typ in Python, read off lib/units.json, held equal to Typst by tests/test_units.py: what the «Formules» tab computes at once (v0.117)
├── line_levels.py                # lib/line-levels.json read for Python: `level(domain, key, role, kind, own)`, the rule Typst's `line-level` follows (v0.120, UI-002)
├── line_display.py               # the arguments a line of a domain's file is displayed by -- fine-keys, style, role, level --, read from lib/display-presets.json where lib/formula.typ reads them: what «Affichage» sets and the base of a file's lines keeps through an export (v0.124, D-17)
├── greek.py                      # the Greek names math knows and their letters: formula.typ's `greek-names`, read by richtext and the domain modules (v0.117)
├── typst_math.py                 # a symbol in Typst's math source read once and set two ways: HTML for the window (richtext.math_html) and the subscripts of a figure's text (issue #43); `normalise`, lib/subscript.typ's twin, which both read through (v0.120, UI-001)
├── journal.py                    # the report's revision journal: read, checked, sorted newest first and exported (§3.3terdecies, v0.99)
├── variables.py                  # what the report itself computes, read back out of a COMPILED report by
│                                 # `typst eval` -- the values that live in a Typst state and in no file at
│                                 # all (§1, §10quater, v0.100). Read, never written; cached outside the project
├── variable_sources.py           # every variable of the export -- calculations, connections, connectors, scripts, the Formule domains --
│                                 # as the Variables tab lists it, and where each comes from: Excel, Woodcore or Typst (§10quater, v0.117, issue 13)
├── cli.py                        # woodcore-cli: export, check, sync-engine, new, migrate -- the report built from a terminal (§12, v0.82, v0.111)
├── cli_sync.py                   # woodcore-cli sync status|share|import|move and what check says of sync.json: the Structure tab's sharing from a terminal (§12, v0.117, issue #33)
├── project_lock.py               # the lock a window holds on its project, <name>.woodcore.lock (§10quater, v0.83)
├── project_template.py           # a new project from templates/projet/ -- since v0.122 its skeleton (`create_skeleton`) and each document made later (`create_document`) --, and an old folder made into one (§12, v0.83)
├── template_preview.py           # the «Projet» tab's preview: a document with a content template and a form in a throw-away project of the cache, Qt-free (v0.122, issue #88)
├── palette_index.py              # what the command palette searches, read at its sources each time, and how a query matches, Qt-free (v0.122, issue #83)
├── templates.py                  # project templates in three places (Standard, the user's, an office's shared folder): template.json, a project made from one, a project saved as one (§10quater, §12, v0.94)
├── documents.py                  # the three documents a project is written as: what each is called in each language, its folder and its entry file, `compile_args` -- the one spelling of a compile's command line -- and `import_line` (§10quater, §12, v0.111)
├── stamps.py                     # whether a document's Typst changed since its PDF: a stamp per document in _woodcore/stamps/, built from `typst compile --deps` (§12, v0.111)
├── typst_paths.py                # the path literals of a .typ file, found and rewritten when what they name moves -- textually, every other byte kept (§12, v0.111)
├── typst_calls.py   # the calls a .typ makes, read without compiling: brackets, arguments, strings, comments left out -- the migrations' and the graph's one reader (issue #71)
├── project_migrate.py            # a project laid out as one report moved into three documents, proved against a reference and undone at the first difference: `woodcore-cli migrate` (§12, v0.111)
├── structure.py                  # a document's structure.json (order, nesting, enabled), the block of its entry file generated from it, the tags of parametric objects and shared blocks, the tree with the objects of each file and the operations that write it: add, remove, move, rename, tag (§3.3octodecies, §12, v0.111, v0.112)
├── structure_source.py           # split out of structure.py (issue #30): structure.json -- its constants, its check, its reading -- and StructureError
├── structure_tags.py             # split out of structure.py (issue #30): a section file's woodcore tags paired, its headings lexed, a PDF's bookmarks matched to them
├── structure_nodes.py            # split out of structure.py (issue #30): the tree of a document as the «Structure du document» tab shows it
├── doc_templates.py              # what a new convention d'utilisation or base de projet is made from -- templates/documents/ in three places, and a document saved as a template (§3.3octodecies, §12, v0.111, v0.112)
├── typst_objects.py              # the parametric objects of a document's .typ files, found by their tags, parsed, edited through models and written back between the tags and nowhere else -- every heading and paragraph among them: canonical form, tag_file (§3.3octodecies, v0.112)
├── typst_objects_parse.py        # split out of typst_objects.py (issue #30): Typst values read and written in an object's call, and the commands' signatures
├── typst_objects_models.py       # split out of typst_objects.py (issue #30): the Model of each object the right pane edits -- tables, options, signatures, norms, images, plans
├── typst_objects_sheets.py       # split out of typst_objects.py (issue #30): the models of an export sheet's objects, and of a heading and a paragraph
├── sharing.py                    # a section shared between the three documents as the whole file it lies in, the shared tags, `share`, `stop_sharing`, `reconcile` (§3.3octodecies, v0.112)
├── sync.py                       # what the documents share kept in step as the engineer decides: each copy's state (in step, local, incoming/orange, conflict/red, ignored), «Importer les modifications», «Ignorer», sync.json (§3.3octodecies, v0.112)
├── doc_import.py                 # content imported from another document of the project, linked or independent, and the move of an object (§3.3octodecies, v0.112)
├── structure_preview.py          # the Typst source of the page of what the «Structure du document» tab has chosen -- a chapter, a section, an object -- and nothing else (§3.3octodecies, v0.112)
├── notifications.py              # every error, warning and information in one store, Qt-free: the notice, its words, the log, the structured lines of a child process (§10quater, v0.117)
├── typst_diagnostics.py          # Typst's errors and warnings read once: severity, message, file, line, column, the trace of a panic (§10quater, v0.117)
├── proc.py                       # every child process of the program started without a console window flashing: run, popen, qprocess, start_detached (§10quater, v0.112)
├── positions_workbook.py         # Positionen.xlsx written: rows added, changed, renamed, deleted, the section type column added, the engineer's drop-down lists kept (§7, v0.94)
├── validation.py                 # structure/type/business validation against schemas/ (§3.6)
├── io_excel.py                   # the only module touching a workbook: read_workbook() for
│                                 # Positionen.xlsx's tables, find_workbooks() + open_cells() for the
│                                 # Belastungsannahmen workbooks -- sheet_names() by prefix,
│                                 # value()/at() by address, find_row() by label, address() for provenance
├── tools/
│   ├── archive_export.py         # one zip and a flat copy of the PDF in the project's _Archiv/ after every successful compile, for both build routes -- and the revision journal beside the folders of the drawings (§12, v0.99)
│   ├── dependencies.py           # the installed packages against requirements.txt on every start of Woodcore, and PyPI asked for newer ones (§10quater, §11ter)
│   ├── updates.py                # whether a newer Woodcore is published, and its installer downloaded and checked -- Qt-free (§10quater, §12, v0.89)
│   ├── update_gui.py             # the window's question at the start, the download's progress, the installer started (§10quater, v0.89)
│   ├── woodcore_gui.py            # Woodcore's window, opened by Woodcore.bat and by Woodcore.exe: its tabs, its File menu, its start (§10quater)
│   ├── woodcore_gui_words.py      # split out of woodcore_gui.py (issue #30): the window's words, every tab's merged in
│   ├── polar_tab.py               # split out of woodcore_gui.py (issue #30), named after its tab since v0.120 (woodcore_gui_polar.py until then, G8): the «Moments polaires» tab (PolarTab) and its helpers
│   ├── woodcore_gui_menus.py      # split out of woodcore_gui.py (issue #30): WindowMenusMixin -- packages, settings, title and marks, the File menu
│   ├── woodcore_gui_export.py     # split out of woodcore_gui.py (issue #30): WindowExportMixin -- the import, the export and the documents compiled
│   ├── home_page.py              # the start page, the new-project dialog (the name, the place and the language since v0.122), the lock's question, the File menu's words (§10quater, v0.83)
│   ├── project_tab.py            # the «Projet» tab: the title page, the language, the form, the documents and their content templates, the preview of the templates (v0.122, issues #87, #88, #90)
│   ├── command_palette.py        # the command palette, Ctrl+K, and what the window hands it (v0.122, issue #83)
│   ├── migrate_dialog.py         # a project laid out as one report, offered its migration into three documents as it opens: the question, its progress and the banner «Migrer…» (§10quater, v0.111)
│   ├── structure_tab.py          # its «Structure du document» tab, the one tab a document is written in: the tree, the page of what is chosen, the options by kind, what is shared (§10quater, v0.112)
│   ├── structure_tab_view.py     # split out of structure_tab.py (issue #30): StructureTabViewMixin -- the files watched, the tree, the selection, the right pane, the page
│   ├── structure_tab_write.py    # split out of structure_tab.py (issue #30): StructureTabWriteMixin -- a section's state, title, place and objects written
│   ├── structure_tab_share.py    # split out of structure_tab.py (issue #30): StructureTabShareMixin -- tagging, importing, sharing, templates, drops, what is shared
│   ├── structure_tree.py         # that tab's tree: chapters, sections and objects, boxes, marks, the sync colours, the selection and the drop (§10quater, v0.112)
│   ├── structure_words.py        # that tab's words in three languages, a sentence for every refusal code of the five modules that write a document (§10quater, v0.112)
│   ├── object_panes.py           # the right pane's editors of the objects of a document -- a pane per kind, no Typst code ever shown (§10quater, v0.112)
│   ├── object_panes_words.py     # split out of object_panes.py (issue #30): the editors' words in three languages
│   ├── object_panes_context.py   # split out of object_panes.py (issue #30): what an editor is given -- categories, plans, variables, the bibliography -- and the variable dialog
│   ├── object_panes_fields.py    # split out of object_panes.py (issue #30): the fields an editor is built of, and Pane, the base of every editor
│   ├── object_panes_table.py     # split out of object_panes.py (issue #30): the editors of a table and of a live-load table
│   ├── object_panes_options.py   # split out of object_panes.py (issue #30): the editors of options, a choice, a checklist, signatures, norms and a field
│   ├── object_panes_media.py     # split out of object_panes.py (issue #30): the editors of an image, a plan, a fire plan, an extract and the annexes
│   ├── import_dialog.py          # that tab's dialogs: a new section or chapter, «Importer depuis un autre document», sharing, a version kept in a conflict, «Enregistrer comme modèle…» (§10quater, v0.112)
│   ├── pdf_pane.py               # the compiled page beside what it is written from: a PDF read into memory, a preview compiled in the background, a snippet compiled from standard input (§10quater, v0.112)
│   ├── settings_dialog.py        # *Fichier → Paramètres…*: templates, defaults, languages, appearance and updates, paths (§10quater, v0.94)
│   ├── typst_check.py, typst_gui.py   # Typst's version checked at every start from the sources, winget on a yes, the pin rewritten (§10quater, v0.94)
│   ├── theme.json                # every colour of Woodcore, light and dark, the radius and the two font stacks -- the website's site.css is written from it too (v0.90)
│   ├── theme.py                  # the window's look: palette, one style sheet on Fusion, the fonts as a browser resolves them, *Fichier → Apparence* (§10quater, v0.90)
│   ├── legal.py                  # the copyright line of the start page and *Fichier → À propos de Woodcore…*: the licence and the notices a click away (§12, v0.91.1)
│   ├── chrome.py                 # the window's frame after the site's: the segmented language switch, the grouped side navigation, the module icons, the start page's cards (§10quater, v0.91) -- since v0.117 SegmentedSwitch, the switch of the views a LanguageSwitch is one of, and FoldButton, the navigation's fold for any pane -- since issue #10 also `FoldablePane`, the arrow and the floor of every tab's own left pane
│   ├── richtext.py               # what the window sets as rich text: a symbol as mathematics, a Typst call coloured as the site's code, the call field and its «Copié ✓» button (§10quater, v0.92)
│   ├── typst_syntax.py           # the one Typst tokeniser, Qt-free: the website's build and the window colour their code with it (§10quater, §12, v0.92)
│   ├── woodcore_start.py         # the start screen before the heavy imports, the steps and their weights, the taskbar's identity (§10quater, v0.117)
│   ├── notices_ui.py             # the activity chip, the octagon and the triangle at the top right and their panel; tell, inline_error, install_hooks (§10quater, v0.117)
│   ├── tasks.py                  # long work in the pool, its result on the window's thread; the activity said by the chip (§10quater, v0.117)
│   ├── layout_store.py           # the panes' sizes by tab, view and set of screens, in the user's settings (§10quater, v0.117)
│   ├── calc_tab.py               # the common base of the tabs of calculation: DeclaredTabMixin, its modules, «Affichage» of the case's file (docs/ui/calc-tab.md, v0.124, issue #94)
│   ├── calc_fields.py            # the fields a domain's declaration names: number, buttons with a free value, tiles, checkbox, select, custom, each with its ⓘ
│   ├── calc_tab_words.py         # the base's words, prefixed ct_
│   ├── module_pane.py            # the right pane of modules: drag and drop, fold, unpin, ⧉ a window zoomed by Ctrl+wheel, the order kept per tab on this machine
│   ├── norm_bubble.py            # the norm under a datum: the ⓘ, the bubble (place), the excerpt's words then its image
│   ├── norm_reader.py            # Woodcore's reader of a norm: the chapter at the clause, framed (FramedPdfView, page_rect_in_view)
│   ├── excerpt_image.py          # an excerpt cut out of the shipped PDF by QtPdf, kept in Woodcore's cache
│   ├── domain_file_display.py    # «Affichage» of a tab of calculation: the case's file compiled, what the report hides pale, «Éléments du fichier»
│   ├── snow_tab.py, snow_tab_words.py  # «Neige», the first tab built on calc_tab (docs/ui/tab-snow.md), words sn_
│   ├── bundle_view.py            # an export document's pages and its id, name, description and storey (§10quater, v0.117)
│   ├── views.py                  # the views of a tab -- Import · Dessin · Typst · Export, Calcul · Affichage, … -- their words, and the user's setting that keeps each tab's (§10quater, v0.117)
│   ├── autosave.py               # saving without a question when a tab, a view, a document or the window is left; what is never saved without the engineer (§10quater, v0.117)
│   ├── display_view.py           # the «Affichage» view of every tab: the command chosen, its panel, the call to copy, the page compiled (DisplayView, SpecPanel, ViewPanes, DisplayTab) (§10quater, v0.117)
│   ├── display_options.py        # the option panel of each command, written by hand, Qt-free: no default -- the signature's -- and every argument offered or dismissed (§10quater, v0.117)
│   ├── cards.py                  # forms in cards, after the site: card(), note(), form() whose labels go above their fields where they must, Reflow (cards side by side where they have the room), and a column that scrolls up and down only and is never narrower than its cards (§10quater, v0.93, v0.95) -- since v0.117 SizedBox, a box whose grip sets its own height, and CurrentStack, a stack the size of its page
│   ├── stylefactors.py           # how those factors are typed: a slider in per cent, and one entry's own rows --
│   │                             # orange with «Reprendre» where it states one (§10quater, v0.99)
│   ├── flowbar.py                # a row of controls that wraps onto the next line: the plan's tool bar, the static models' and the schemas' (§10quater);
│   │                             # since v0.87 also the compact measures of the last two bars and ResizableColumns, their lists' dragged column widths
│   ├── nowheel.py                # one event filter on the application: the wheel scrolls and zooms, it never changes a value (§10quater)
│   ├── tab_registry.py           # every tab declared once, a TabSpec; TABS, the navigation, the documents' tabs derived (v0.120, ARCH-001)
│   ├── tab_guard.py              # the read-only guard and the domains' files after a writer, applied where each writer is defined, once (v0.120)
│   ├── source_editor.py          # SourceEditorTab: the base of every editor tab of sources -- list (the four canvases' too, through its hooks), draft's actions, Ctrl+S, unsaved question, export (v0.120)
│   ├── canvas_editor.py          # CanvasEditorTab: an editor of a drawing, with «Annuler» and «Rétablir» once (v0.120)
│   ├── canvas_base.py            # CanvasBase: what the four canvases share -- zoom, grid, cursor, snap marker, handles, tracking, a dimension under way; each says its own by class attributes (v0.120, D1)
│   ├── canvas_items.py           # SvgLayer (Qt's device cache, or once per view), the cosmetic pen, a coordinate rounded as it is saved (v0.120, D2)
│   ├── svg_icons.py              # SVG text as a pixmap or an icon at the screen's pixel ratio, fitted or stretched, and a swatch recoloured -- every icon of the window (v0.120, D3)
│   ├── reserved_tab.py           # ReservedTab: the six tabs to come (v0.120, FutureTab and SoonTab until then)
│   ├── grouped_list.py           # the left pane of every editor tab: folders, drag and drop, Ctrl/Shift, the tree's lines and «Archives» -- a folder being a `group` FIELD and never a directory (§10quater)
│   ├── source_archive.py         # «Supprimer» archives: a source moved into <folder>/archives/ with its id removed, restored under a new one (§10quater)
│   ├── identity.py               # Nom · Description · ID, the rows every editor tab names its objects with, and slug_id (§10quater)
│   ├── check_cell.py             # a check box centred in its table cell, drawn and clicked there: the tick columns of «Schémas» (§10quater)
│   ├── stallwatch.py             # one watch thread: a window stalled past 1.5 s (Python stacks) or the whole computer stopped past 0.75 s, logged to %LOCALAPPDATA% (§10quater)
│   ├── plan_tab.py               # its position plan tab, and that tab's texts in three languages
│   ├── plan_tab_words.py         # split out of plan_tab.py (issue #30): the tab's words in three languages
│   ├── plan_tab_build.py         # split out of plan_tab.py (issue #30): PlanBuildMixin -- building and drawing a plan, its scale, storey, type, section
│   ├── plan_tab_selection.py     # split out of plan_tab.py (issue #30): PlanSelectionMixin -- the tools, new elements, the selection and its properties
│   ├── plan_canvas.py            # the tab's drawing surface: background, symbols, tools, snapping
│   ├── plan_canvas_edit.py       # «Déplacer», «Copier» and the construction aids, for the position plan's canvas and the fire plan's (issue #18)
│   ├── plan_clipboard.py         # the one clip of the process, in memory -- the project's (issue #61)
│   ├── plan_canvas_outline.py    # the building's outline on the position plan's canvas: its tool, and how it is taken by its edge, reshaped and moved (issue #54)
│   ├── plan_centres_card.py      # the right pane's card «Centres S et M» and a bracing wall's «Mode de construction» (issue #54)
│   ├── plan_canvas_render.py     # split out of plan_canvas.py (issue #30): the background rendered -- jobs, caches in memory and on disk, PDF pages, tiles, SVG layers, tinting
│   ├── plan_canvas_view.py       # split out of plan_canvas.py (issue #30): PlanCanvasViewMixin -- the crop or the page, the background, the superposition, «Aligner»
│   ├── plan_canvas_edit.py       # split out of plan_canvas.py (issue #30): PlanCanvasEditMixin -- tools, tracking, editing
│   ├── plan_canvas_input.py      # split out of plan_canvas.py (issue #30): PlanCanvasInputMixin -- the mouse and keys, the editor's helpers
│   ├── drawing_tab.py            # what every tab of plans drawn on imported documents shares -- documents, list, export sheets, builder, history, entry sizes, autosave, view state -- on hooks (§10quater, v0.115)
│   ├── drawing_tab_panes.py      # split out of drawing_tab.py (issue #30): DrawingPanesMixin -- the panes, the right pane's modules, the left pane's choice, the views
│   ├── drawing_tab_documents.py  # split out of drawing_tab.py (issue #30): DrawingDocumentsMixin -- the documents, their pages, frames and layers
│   ├── drawing_tab_sheets.py     # split out of drawing_tab.py (issue #30): DrawingSheetsMixin -- the export sheets, the bundles, the history, the entry's size
│   ├── drawing_tab_clip.py       # DrawingClipMixin: Ctrl+A, Ctrl+C (base point) and Ctrl+V between the plans of one tab, the canvas's shortcuts (issue #61)
│   ├── fire_tab.py               # its fire-protection plan tab on that base, and that tab's texts in three languages (§10quater, v0.115)
│   ├── fire_tab_words.py         # split out of fire_tab.py (issue #30): the tab's words in three languages
│   ├── fire_tab_build.py         # split out of fire_tab.py (issue #30): FireTabBuildMixin -- the tree, the combos, the centre and the right pane's cards
│   ├── fire_tab_form.py          # split out of fire_tab.py (issue #30): FireTabFormMixin -- the frame, the source and the form, the tools
│   ├── fire_tab_selection.py     # split out of fire_tab.py (issue #30): FireTabSelectionMixin -- the selection, its lists, its size and style
│   ├── fire_canvas.py            # the tab's drawing surface, on PlanCanvas.frame_source(): surfaces, walls, doors, routes, exits, widths and the legend
│   ├── plan_superposition.py     # the «Superposition» module of the plan tabs: another plan of the tab shown over the open one, its opacity, colour and alignment (§3.3sexies, §10quater, v0.116)
│   ├── sheet_list.py             # the export list of the plan tabs, a GroupedList whose folders are PDF bundles and whose sheets are dragged into, within and out of them (§10quater, v0.116)
│   ├── journal_tab.py            # its journal tab: the report's revisions, written by hand (§10quater, v0.99)
│   ├── action_tabs.py            # the words of the six empty tabs of «Actions» and their two sections -- Poids propre, Surcharge | Charge utile, Neige, Vent, Séisme (v0.117; `FutureTab` carries them, `woodcore_gui.NAV_SECTIONS` places the sub-titles)
│   ├── load_tab.py               # the loads entered in Woodcore: «Poids propre et surcharge», «Vent» on one base, LoadTab (list | form in cards | the instant result and the drawing), issues #35-#37 -- the frame «Neige» is built on since v0.124 (calc_tab.py)
│   ├── linkable_spin.py          # the button 𝑥 beside a field that may follow a variable, its linked state, factor, offset, «Délier» and «Introuvable» (issue #42, §3.3duovicies)
│   ├── text_pane.py              # the right pane of a text placed with the Text tool, the same in the four drawing engines: content, «Insérer une variable», a card per variable (issue #43)
│   ├── member_check_tab.py       # the member checks' two navigation groups: the «Traction» and «Compression» tabs on one base (list | form in cards | the instant results and the call, then the command's options and the Typst page of the draft, both collapsible) and the seven placeholders of the other modules (§10quater, v0.117)
│   ├── member_check_tab_words.py # split out of member_check_tab.py (issue #30): the member checks' words in three languages
│   ├── member_check_tab_form.py  # split out of member_check_tab.py (issue #30): MemberCheckFormMixin -- the form, the result, the «Affichage» view, the draft
│   ├── member_check_tab_actions.py # split out of member_check_tab.py (issue #30): MemberCheckActionsMixin -- the list, the calculation and its command, the buttons
│   ├── annex_tab.py              # its annexes tab: the sources and excerpts in two fixed folders, the page with its bookmarks, a title clicked and a frame dragged (§10quater, v0.115)
│   ├── annex_tab_words.py        # split out of annex_tab.py (issue #30, after issue #16 grew it past 1500 lines): the tab's words in three languages
│   ├── annex_tab_pages.py        # split out of annex_tab.py (issue #30): the PDF read, the source's pages shown with their frames, the frames found in a page
│   ├── formula_tab.py            # its «Formules» tab: the domains in the shared list (folders, order, «Archives»), a domain written as text zones and blocks, options a click away, the ID renamed, «Affichage» with #include (§10quater, v0.117, issue #15)
│   ├── formula_tab_widgets.py    # split out of formula_tab.py (issue #30): a block of a calculation with its fields, a zone of Typst between the blocks
│   ├── formula_tab_domains.py    # split out of formula_tab.py (issue #30): FormulaDomainsMixin -- the domains, the name line and the ID
│   ├── formula_tab_blocks.py     # split out of formula_tab.py (issue #30): FormulaBlocksMixin -- the blocks and texts, the variables taken from elsewhere
│   ├── variables_tab.py          # its variables tab: every value the report computes, by domain, filtered by
│   ├── dependencies_tab.py      # «Dépendances»: the graph of the last export, «dépend de» / «utilisé par», an object opened in its tab (issue #71)
│   │                             # name and by unit, with the calls that print one (§10quater, v0.100)
│   ├── python_tab.py             # its Python tab: the editor, the run, the variable inspector and the terminal (§10quater, v0.100)
│   ├── positions_tab.py          # its positions tab: Positionen.xlsx listed and edited, every write through positions_workbook (§10quater, v0.94)
│   ├── statics_tab.py            # its static models tab, its five lists and that tab's texts in three languages
│   ├── statics_tab_words.py      # split out of statics_tab.py (issue #30): the tab's words in three languages
│   ├── statics_tab_build.py      # split out of statics_tab.py (issue #30): StaticsBuildMixin -- the list, the four tables, the tool bar, the canvas, the right pane
│   ├── statics_tab_properties.py # split out of statics_tab.py (issue #30): StaticsPropertiesMixin -- the properties of what is selected
│   ├── statics_canvas.py         # the tab's drawing surface: the grid, the tools, the snapping and the tracking
│   ├── schema_tab.py             # its schemas tab, its six lists and that tab's texts in three languages (§10quater)
│   ├── schema_tab_words.py       # split out of schema_tab.py (issue #30): the tab's words in three languages
│   ├── schema_tab_build.py       # split out of schema_tab.py (issue #30): SchemaBuildMixin -- the list, the tool bar, the canvas, the tables, the properties
│   ├── schema_tab_draft.py       # split out of schema_tab.py (issue #30): SchemaDraftMixin -- the draft and the form, «Surfacique», the lists
│   ├── schema_canvas.py          # the tab's drawing surface, in millimetres: the grid, the tools, the snapping and the tracking
│   ├── schema_canvas_place.py    # split out of schema_canvas.py (issue #30): SchemaCanvasPlaceMixin -- what a click puts down, tracking, modifications
│   ├── schema_canvas_input.py    # split out of schema_canvas.py (issue #30): SchemaCanvasInputMixin -- the mouse and keys, what only the editor shows
│   ├── schema_canvas_place.py    # split out of schema_canvas.py (issue #30): SchemaCanvasPlaceMixin -- what a click puts down, tracking, modifications
│   ├── schema_canvas_input.py    # split out of schema_canvas.py (issue #30): SchemaCanvasInputMixin -- the mouse and keys, what only the editor shows
│   ├── connectors_tab.py         # its connectors tab, and that tab's texts in three languages (§10quater)
│   ├── connectors_tab_words.py   # split out of connectors_tab.py (issue #30): the tab's words in three languages
│   ├── connectors_tab_form.py    # split out of connectors_tab.py (issue #30): ConnectorsFormMixin -- the form, its rows and boxes, the figures and results
│   ├── connectors_tab_draft.py   # split out of connectors_tab.py (issue #30): ConnectorsDraftMixin -- the draft and the form, the live preview, the table's buttons
│   │                             # as a detail schema, the two sources left naming it (v0.74, §3.3decies)
│   ├── commands_tab.py           # its commands tab: every command of lib/, its arguments, its calls and its examples (§10sexies)
│   ├── command_preview.py        # the page one example is compiled as, and the fallback render
│   ├── command_docs.py           # the translation of the documentation the commands tab shows, and what tests hold of it (§10sexies, v0.86)
│   ├── build_examples.py         # writes the frozen MWEs from the /// fences and renders them once (§10sexies)
│   └── woodcore.svg              # its icon, in the title bar and on the taskbar -- and the installed program's woodcore.ico
└── export_all.py                 # orchestrates everything: the calculation domains, one descriptive
                                   # position record per Positions Element row (§7), the positions index,
                                   # the connectors (§7bis), the connections and the plans (§3.3sexies), all
                                   # checked before anything is written; then the reference workbook

```

👉 **No path in `calc/` is derived from the module's own location but the program's own** (v0.81). `project.APP_ROOT` is `Woodcore/`, and what lies in it — `schemas/`, `calc/norms/`, `calc/i18n/`, `lib/`, `examples/` — is read from there. Everything else is the project's, asked of `project.current()` at the moment it is needed: the workbooks by name or by the pattern `registry.py` searches the project's folder for (§3.3), the sources in `Woodcore-Datei/`, the export in `_woodcore/data/`, a plan's background by the path its source gives from the project's folder (§3.3sexies). A process works on one project: `--project <file>.woodcore`, else `WOODCORE_PROJECT`, else the one `.woodcore` in a folder beside `Woodcore/`. `tests/test_project.py` refuses a module that fixes a project path at import.

Principles:
- **`schemas/`** holds the documented JSON schemas (§3.0), the formal contract between Python and Typst — every structural change starts with updating the schema and its `schema_version`. It lives beside `calc/`, under `Woodcore/`, not nested inside it.
- **`calc/libraries/`** holds what is no norm but is read like one: Woodcore's materials library, read out once, every entry keeping its source (`domains/materials.py`, issue #35, D-07). A value of a norm never goes here.
- **`calc/norms/`** is the sole source of values taken from a norm for a calculation made in Python (one made in Excel keeps its own) — **and, since v0.87, for Typst's `#distance`**, which reads the very same files by the relative path `../calc/norms/` (§10bis): one source for both, `calc/norms/sia265.py` checking them before an export reads anything and `tests/test_distance.py` holding the two lists of files equal, the files copied into each project's `_woodcore/` with the engine and into `examples/calc/norms/` at a freeze (§12, §10sexies) — **no norm value twice**, the engineer's rule (v0.77). One JSON per table or clause, **flat in the folder**, named `<norm>-<year>-<table or clause>-<designation>.json` — `sia265-2021-tab08-vollholz.json`, `sia265-2021-6.2.1.1-k-alpha.json`, `sn-en-14592-2012-fu-k-stabduebel.json` — and one reader per norm beside them (`sia261.py`, `sia263.py`, `sia265.py`, `sn_en_14592.py`) that checks each file before a value is taken out. **A coefficient inside a formula is a norm value like any other** and lives here, not beside its formula (v0.77, reversing v0.68). `tests/test_norms.py` holds the naming, that no file is read by nobody, and that `domains/dowel.py` writes none of SIA 265's coefficients. If a normative value changes edition, only one file needs updating. Populated since v0.49, when SIA 261's Tabelle 8 was the first file (`sia261_tables.json` until v0.77) — the pattern for every table that followed: the numbers in the JSON, the edition named there, the checks in its reader. Nothing is outside it any more: the GL24h constants that used to sit in `domains/bending.py` went with that module in v0.59, so a norm value now has exactly one place it may be written down. 👉 Where those values come *from* is the reference library (§11bis): a number reaches this folder by being read off a named edition at a page that can be turned to, and `sia261-2020-tab08-nutzlasten.json`'s `SIA 261:2020` is the name of a file in the reference library. ⚠️ One file cannot say that yet: SN EN 14592's f_u,k was given by the engineer, the edition not being in the library, and its `norm_ref` stays empty until it is. #distance's tables (v0.87) were transcribed off page renders of `SIA265-2021-DE.pdf` — Tabelle 24 p. 66 (extended, `dowel.py` reading it unchanged), 27 and 28 p. 68, 32 and 33 p. 71, 36 p. 74, 37 to 39 p. 75, 40 p. 76, 41 p. 80 — their French words from the French edition, their row names SIA 265's own words (it uses no a₃,t or a₄,c symbols), and their footnotes restated in one sentence each, never copied. ⚠️ Tabelle 38's first column is headed «d = 4 mm» in both editions; it is read as d ≤ 4 mm, and the printed text is kept in the file.
- **`domains/`**: one file per calculation topic, each returning `Calculation` objects (via `engine.py`), never hand-written JSON. A *load* domain additionally declares `DOMAIN`, `LABEL`, `ACTION`, `ENGINE` and `SHEET_PREFIX` and exposes `read_instances(cells, sheets)`; that is the whole interface `registry.py` needs, which is why adding a `wind-load` domain means writing one module and adding it to `DOMAIN_MODULES`. Load combinations will follow the same `Calculation` logic when they are written (§3.5) — a domain like any other, not a special case.
- **`engine.py`** requires `norm`/`norm_ref` on every step — raises an explicit error at export time if a calculation doesn't cite its norm, to prevent oversights.
- **`validation.py`** applies the three validation levels (§3.6) to every file before it's written to `data/` — blocking on failure.
- **`export_all.py`** is the sole entry point of the Python build (called by `woodcore-cli` and by Woodcore) — it guarantees positions, calculations, and combinations are always consistent and validated before Typst runs.

---
