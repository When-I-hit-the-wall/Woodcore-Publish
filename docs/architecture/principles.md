# Architecture principle and design rules

> The pipeline Woodcore's sources -> Python -> JSON -> Typst (Excel until v0.125 for the loads), and the 16 design rules every change must respect.
>
> Moved verbatim from CLAUDE.md (§2) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 2. Architecture principle

```
Woodcore's window (input data -- user entry, project parameters), its sources under Woodcore-Datei/ (§11)
  ├─ positions.json                  the positions, entered in the Positions tab (§7; a Positionen.xlsx is imported once, v0.114). NO loads, NO connectors (§7bis).
  └─ loads/{wind,snow,dead}/<id>.json  every load, one source per case, entered in the tabs Vent, Neige, Poids propre et surcharge (§3.3):
                                     snow/   the roof of a snow load (§3.3bis)
                                     dead/   the layer build-up Python sums (§3.3ter)
                                     wind/   the building of a wind load (§3.3quater)
        │  no load workbook is read since v0.125 (issue #109, D-33): a *Belastungsannahmen* file left in the folder is named by a warning, never opened
        │
        │  + connectors/<id>.json           one connector each, with its own shear-resistance calculation, drawn on a detail schema, written by Woodcore (§3.3nonies)
        │  + connections/<id>.json          one polar-moment calculation each, drawn on a detail schema, written by Woodcore (§3.3quinquies)
        │  + plans/<id>.json                one position plan each, drawn in Woodcore over the architect's plan (§3.3sexies)
        │  + statics/<id>.json              one static model each, drawn in Woodcore (§3.3octies)
        │  + details/<id>.json              one connection detail each, drawn in Woodcore (§3.3decies)
        │  + checks/<id>.json              one member check each (SIA 265 4.2.1 tension and 4.2.2 compression so far), written by Woodcore's «Traction» and «Compression» tabs and computed in the report by #show-check-member (§3.3unvicies)
        │  + Formules/<id>.typ + unfold.json   a member check printed unfolded is one too, written by Woodcore from its checks/<id>.json and edited like any other, the base of its lines beside it (v0.118, issue #62, calc/domains/unfold.py)
        │  + Formules/<id>.typ             one calculation domain each, at the top of the Typst root, written by Woodcore's «Formules» tab and by VS Code alike -- the .typ the source of truth, its id the file's name, printed by #include "/Formules/<id>.typ" (§10quinquies, v0.117, issue #15)
        │  + journal[-cu|-bp].json         each document's revisions, ONE file each and not a folder of them, written by hand in
        │                                   Woodcore's «Journal» tab (§3.3terdecies)
        │  + <document>/structure.json, Sections/<id>.typ, sync.json   a convention's and a base de projet's chapters and sections, the objects in them -- every heading, paragraph and table between tags -- and what each shares with the others, written by Woodcore's «Structure du document» tab and by VS Code alike, the .typ being the source of truth (§3.3octodecies)
        │  + calc/norms/<norm>-<year>-<table>-<designation>.json  every norm value a Python calculation uses, one file per table or clause, transcribed once (§11) --
        │                                   the same files Typst's #distance reads for SIA 265's minimum distances (v0.87, §10bis)
        │  + calc/domains/figure_style.py  the three factors every figure is drawn with -- the strokes, the symbols placed on a point,
        │                                   the texts -- and the factor one entry of a drawing may state over them (§3.3quaterdecies)
        │  + calc/norms/norms.json          the documents the engine can name in full -- designation, title, edition, publisher --
        │                                   for the report's bibliography, beside the project's own references.bib (§10); 43 entries since v0.112, the SIA and VKF documents the two other documents name
        │  + calc/i18n/strings.json         every word the engine prints, in German, French and English -- read by
        │                                   Python for the figures it draws and by Typst for the rest (§4bis)
        ▼
Python (validation, calculations, calculation domains, load combinations)
        │
        ├─ schemas/*.schema.json          documented, versioned JSON schemas (data contract)
        ├─ data/positions/<id>.json       type/material/dimension per position (descriptive only, §7)
        ├─ data/connectors.json           every connector: its description and its shear resistance (§3.3nonies, §7bis)
        ├─ data/calculations.json         one entry per domain, one per case entered in Woodcore inside it -- or per category, for a domain read from a norm table (§3.3septies)
        ├─ data/connections.json (+ .svg) one entry per connection: its schema, its geometry and polar moment
        ├─ data/plans.json (+ plans/)     one entry per plan: its symbols' SVG, its legend's lines, its background's page
        ├─ data/statics.json (+ statics/) one entry per static model -- drawn in Woodcore (until 0.117 also imported from RFEM, an import retired then: archive/rfem/)
        ├─ data/checks.json              one entry per member check saved in Woodcore: its values resolved against the positions, whether it can be calculated and why not -- nothing computed (§3.3unvicies)
        ├─ data/formulas.json            the index of the «Formules» tab's domains, id -> title and Formules/<id>.typ (2.0), read by the «Variables» tab and the export's checks, no longer by Typst (v0.117, issue #15)
        └─ data/journal[-cu|-bp].json    each document's revisions, newest first (§3.3terdecies)
        │
        ▼  read by Typst (json())
_woodcore/lib/calc-engine.typ  (the program's lib/, copied into the project at every export with the norm tables lib/distance.typ reads: shared display functions + get-* data-access abstraction)
        │
        ▼
the three documents (v0.111), each its entry .typ + Sections/*.typ in a folder of its own: 1_… the convention d'utilisation, 2_… the base de projet,
3_…/Statischer Rapport.typ the report (layout, text, report structure, axes passed as an argument); a project laid out as one report has the report alone (§12)
        │
        ▼  woodcore-cli export [--document cu|bp|rs|all] --level 1|2|3   (typst compile --root <the Typst root> --input level=1|2|3)
one PDF per document, beside its .typ (§12, v0.87) -- compiled only if its Typst changed since its PDF (calc/stamps.py, v0.111)
```

**Woodcore as the point of entry.** Woodcore's window is where the engineer enters the project and its parameters; Python turns what it saved into JSON and performs the calculations. The loads are cases entered in its tabs -- the snow's roof, the wind's building, the permanent loads' layers --, each a source of `Woodcore-Datei/loads/` computed by its module (§3.3bis to §3.3ter). Until v0.125 they came from the `SL-*`, `WL-*` and `EL+AL-*` sheets of the Belastungsannahmen workbooks too; the engineer's decision of 24.10.2026 (issue #109, D-33: «il n'y aura plus jamais de feuille excel à lire pour le vent, ni pour la neige, ni pour les charges permanentes») took that way in away, and an export of before is refused where it is read (docs/decisions.md §13). Which code computed a value is never guessed: every var carries the `source` that produced it (`entered:loads/snow/SL.json`, `python:domains/dead_load.py`, `norm:SIA 261:2020, Tabelle 8`). The one workbook still read is `Positionen.xlsx`, imported once into a project made before v0.114. 👉 **The JSON files in `data/` must never be edited by hand**: they are always regenerated by `export_all.py` from the project's sources and the Python code.

**The norm is the source of truth above what is entered.** Woodcore's window is where the engineer enters *this project* — its geometry, its layers, the coefficients chosen for it. What the norm fixes for every project is entered nowhere: it is transcribed once into `calc/norms/*.json`, from the edition it was read in, and that edition is a PDF in the reference library (§11bis). ⚠️ Since v0.99 the folder also holds **`norms.json`**, which is not a value of a norm but the **name** of one: the designation, the full title, the edition and the publisher of every document the engine cites, for the report's bibliography (§10). It belongs here for the same reason every other file of the folder does — a norm's own words are transcribed once, off the edition named in its `_source`, and `calc/norms/norms.py` checks the file before an export or a report takes anything out of it — and it travels into every project with the engine (§12). What no file of this folder ever holds is the *path* to the library: the report prints the four fields and never names `ExternalFiles/`.

⚠️ Since v0.87 those files are read by **Typst** as well as by Python: `#distance` prints SIA 265's minimum distances from the very JSON `calc/norms/sia265.py` reads (§10bis), one source for both, and the tables it names are copied into each project's `_woodcore/` with the engine (§12). The reference library sits beside the pipeline and outside it: it is read by the engineer and by the assistant and by nothing else — no module of `calc/` opens a file in it, no schema mentions it, and `export_all.py` does not know it is there. ⚠️ **Not the norms since v0.124** (issue #94, D-22, D-24): their PDFs are shipped in `norm-library/`, the window shows an excerpt of them under each datum of a tab of calculation and opens their chapters (`calc/norms/library.py`, `excerpts.py`; docs/architecture/reference-library.md §11bis); the export still does not read them.

Design rules (kept up to date):

1. **One single source of truth per variable** — no value copied by hand.
2. **Every calculation (Python or Typst) has the same data shape** and is rendered with the same display function.
3. **What a calculation concerns is stated in the report, never in the data**: a section names a position by `#position(id)` and sets the calculation that concerns it after it -- a `#domain` of its own or a domain Woodcore wrote out, `#include domain-file(kind, id)` (spec 2026-10-21-commandes-typst-refonte, REQ-015; a `calc-block` attributed calculations to positions until then, §5) --, and a load, a connection, a connector or a schema belongs to no position (§8, §14).
4. **The default level of detail is a compile-time parameter**, but any calculation can override it individually.
5. **Systematic provenance** (entered in Woodcore / Python / a norm / Typst direct) on every variable -- a workbook's cell (`excel:`) was one until v0.125 (issue #109).
6. **A load is a calculation domain, its cases are sources entered in Woodcore** (§3.3; Excel sheets until v0.125, issue #109): addressed `(domain, instance)`, never duplicated, and never assigned to a position at the data level either (§7-§8) — positions only carry their own type/material/dimension.
7. **Every calculation step cites its norm and norm clause** — or, where it follows a document rather than a norm (a connection's handbook, §3.3quinquies), that document, whose clause may then be left empty (v0.32). The reference itself is never optional.
8. **Every JSON file follows a versioned schema** (`schema_version`).
9. **Every value has an explicit unit.**
10. **Data is validated** (structure, type, business rules) **before export.**
11. **Typst accesses data through abstraction functions**: `get(v, field)` for one field of a variable, `ids(kind)` for the ids of one kind of object, `#var(key, domain: (calculation, instance))` for a value of the export, read live, and `domain-file(kind, id)` for a file Woodcore wrote -- the eight `get-*` and the thirteen `*-ids` until v0.120, each merged into one (spec 2026-10-19-base-saine-nettoyage, REQ-002), `#val`, `#show-input`, `#var-of` and `#value-of` merged into `#var` (spec 2026-10-21-commandes-typst-refonte, REQ-009); a project's sections migrated when it is opened (`calc/domains/commands_migrate.py`, from `calc/renamed-commands.json`, the one list of what a retired call becomes).
12. **Axes are a display concern**, not stored in the data.
13. **A value taken from a norm is read from the norm itself**, at a named edition and a page that can be turned to (§11bis) — never from memory, never from a handbook's restatement of it, and never from one of the unverified tools beside it in `ExternalFiles/`. Since v0.124 the norms' editions are shipped in `norm-library/` (§11bis), and an excerpt's words copied into its norm file are held to them by a test.
14. **Every command the report can call is documented in Woodcore's commands tab** (§10sexies). A command added to `lib/` is not finished when it compiles: it is finished when it carries a `///` block with a summary, a `- name (type):` line for each of its arguments, a `->` line, and **at least two worked examples that compile**, and when it is placed in one of the categories of `build_reference.CATEGORIES`. A binding nobody outside the engine should call is placed in *Internes* instead, which is the same decision made explicitly. `tests/test_commands.py` enforces all of it, so the obligation is a check and not an intention. Since v0.86 a command is finished when its paragraphs and arguments are translated into French and German as well, in `calc/i18n/commands.json` (§10sexies), and the same test names every one that is not.
15. **A document's `.typ` files are the source of truth, the window shows no Typst code, and a calculation is written out whole in its file** (v0.112, §3.3octodecies; rewritten in v0.118, issue #62, docs/decisions.md §13): an object — a heading, a paragraph, a table — is found by its tags, edited through a model and written back between them and nowhere else; what the documents share is kept in step by the engineer's import and never by an overwrite. **The window** shows no Typst code — pills, forms, cards —, and the engineer who wants to read code opens the file in VS Code, where Woodcore follows what he writes; ⚠️ save, since v0.124 (issue #94, D-28), what «Affichage» of a tab of calculation writes into a case's file -- the line as written and the whole file, read only, as it shows the command to copy. **A calculation** is the other way round: every calculation Woodcore makes -- a member check, a steel check, a load, a connector, a polar moment, a script (spec 2026-10-21-commandes-typst-refonte, REQ-017) -- is written out whole in a file of its own, its every `#var`, `#eq` and `#verify` found by its keys and `id:`, never by a comment, and included where a section prints it, `#include domain-file(kind, id)`; each value written there is a literal checked against the export by `domain:`, and what the engineer changes in VS Code is taken back into Woodcore line by line, so that nothing of it ages unseen. **A document and an export sheet are raw Typst** (spec 2026-10-21-commandes-typst-refonte, REQ-019, Q-015): a table is a `#table` the window edits cell by cell, a sheet's object a `#place`, a list Woodcore writes once a table of `#sync` cells the export keeps in step.
16. **The drawing engines work alike wherever they can** (v0.116, §3.3sexies, §3.3vicies, §10quater, §13). The position plan and the fire-protection plan are **one engine** — `DrawingTab`, `PlanCanvas`, the document view, the export sheets — and a feature of one is a feature of the other unless it belongs to the domain: plan types, sections and their levels, the load symbols and the list of the positions are the position plan's alone. Snapping and tracking live **once**, in `PlanCanvas` and `calc/domains/plan_tracking.py`, a second kind of plan supplying only its own points; a right pane, a left pane, a frame, a layer and a sheet are built once and asked for by hook. A future drawing tab — a plan of another trade, a fire section — is built on the same base and follows the same rule where it can; where a feature cannot be shared the reason is written down next to it, the way §3.3vicies says which of this version's changes the fire plan did not take.

---
