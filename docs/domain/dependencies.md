# The graph of dependencies

> §3.3quinvicies, written on 2026-10-21 (issue #71, spec [`requirements/completed/2026-10-21-graphe-dependances.md`](../requirements/completed/2026-10-21-graphe-dependances.md)). The tab that shows it is [`ui/tab-dependencies.md`](../ui/tab-dependencies.md).

### 3.3quinvicies The graph of dependencies (v0.120, issue #71)

**Why.** A project is a network: a member check follows a position, a load follows another load, a static model draws a load, a script reads a value of the export, a domain of «Formules» reads a calculation, a connector follows a schema and the positions of its members, and the three documents print all of it. Each object knows what it reads and none knows who reads it. The audit of 19.10.2026 (§6) proposed writing the network down, so that a value changed upstream says what it touches downstream -- «une seule source de vérité» extended to the links between objects. The engineer chose three forms on 21.10.2026 (D-01): a tab of the window, a file of `data/`, and warnings at the export.

**What is built** (`calc/domains/dependency_graph.py`, Qt-free). At every export, after every domain is prepared and before anything is written, `build` takes what the export holds in memory and writes nothing back:

- **a node** per object, keyed `"<kind>:<id>"`. The kinds (`KINDS`) are `position`, `load` (`load:snow-load/SL`, one case of a calculation domain), `script`, `formula` (a domain of «Formules»), `check`, `steel`, `profile`, `connector`, `connection` (a polar moment), `schema`, `statics`, `plan`, `document` (the document a plan is drawn on), `fire`, `extract` (an excerpt of an annex) and `section` (a section file of one of the three documents, `section:rs/Sections/004-einwirkungen.typ`).
- **an edge** `{from, to, field}` when `from` reads `to` through `field`. It also carries `variable` (`<domain>/<instance>/<var>`) where a variable is read, `previous: true` where it is read in the last export rather than this one, and `line` for a section's call.

**One reader per kind of reference** (ARCH-RISK-1103):

- **Records** — each domain module says what its exported record names, `references(record)` → `[(kind, id, field)]`:
  - `member_check` and `steel_check`: the position, and a steel check's profile.
  - `connector`: its schema and its members' positions. Its own `position` is its id, not a reference.
  - `connection`: its schema and its members' positions.
  - `schema`: its elements' positions.
  - `plan`: its labels, its section plan and its document.
  - `fire`: its position plan.
- **Sources** — every variable a source names, wherever it stands, is read by one walk, `links.references(source)`. That covers a field's link, a static model's magnitude (the record keeps only the text it prints) and a figure text's `vars`. `loads_migrate` walks the same shape to rename.
- **«Formules»** — a domain's commands through `formula_domain.reference(command)`, the classification `resolve_import` reads too. A domain a member check is unfolded into (its `gen`, `Timber-checks/`) is not a node: it is the check's own file, and its `domain: ("check", id)` would otherwise make every unfolded check a circle (ARCH-RISK-1101).
- **Scripts** — what a script's `value()` calls read is recorded as it runs: `script_runner` notes them, `script.prepare(reads=)` hands them over, and `data/scripts.json` is unchanged. A connector or a polar moment it reads is read in the last export: `previous: true`.
- **Sections** — the files `structure_nodes.section_files` lists (a CU's or BP's structure.json, the report's `#include` lines), with `enabled` when the document prints them. Their calls are read outside their comments (`calc/typst_calls.py`) by `COMMAND_REFERENCES`, the table of the commands of `lib/` that name an object and where:
  - `#include domain-file("snow-load", "SL")` names a case, `domain-file("check", "ZT-01")` a member check (the rule `file`, spec 2026-10-21-commandes-typst-refonte, REQ-017);
  - `#var(…, domain: "id")` names a domain, `#var(…, domain: ("snow-load", "SL"))` a case;
  - `#image-positions-plan("P01")` names a plan;
  - `ids("position")` names every position (`position:*`);
  - an argument the section computes (`for id in ids(…) [#position(id)]`) gives the wildcard rather than one edge per object (D-07);
  - a name Python cannot place (a document's own registry) is counted on the section, as `unresolved`.

  `tests/test_dependency_graph.py` holds the table against the public commands of `lib/`: each is in it or in `NO_REFERENCE`.

A reference whose object is not there is no edge: the domain that holds it already says it is gone (D-04, D-07).

**The file** `data/dependencies.json` (`schemas/dependencies.schema.json` 1.0) is `{schema_version, nodes, edges}`.
- `nodes` maps each key to `{digest?, file?, enabled?, unresolved?}`; `edges` is the sorted list.
- It contains no date and no «changed». It is a function of the sources alone, so the same bytes come out of two exports with nothing between them.
- A new project is seeded with an empty graph (`export_all.seed`). Typst never reads it.

**What changed** (D-04, ARCH-RISK-1106). `digest` is `engine.digest` of a node's record without the keys that only present it (`PRESENTATION`: figures, overlay, legend, style, label, name, group, warnings, description, notes…). Everything else counts, so a field added to a record is seen without anyone listing it. A section, a profile and a document carry none.

Between the previous file (`read`) and this export's graph, `changes` decides what to say:
- **Changed**: a node whose digest moved.
- **Not a change**: a new node, a removed node, and anything at all when there is no previous file, the file is unreadable, or it is of another version (CON-002).
- **Roots**: only the changed nodes none of whose own inputs changed are named. A position whose strength class changed is said once; the checks it moves too are not said again as roots of their own.

Each root comes with what depends on it, transitively (`reachable`, the walk «Dépendances» and the command palette read too, v0.122), by kind: at most `SHOWN` (8) ids, then «(+N)». The text is one `engine.Note` `dep_changed` per root and kind, with the kind as a nested Note `dep_kind_<kind>` that the window translates.

**Circles** (ARCH-002, ARCH-RISK-1107). `links.find_cycles` gives every strongly connected component, each walked from its smallest node. One through objects of at least two kinds is said, `dep_cycle`, for example:
- a load following a «Formules» domain that reads that load;
- a script reading a connector that follows the script, through the last export.

A circle of loads alone stays the registry's refusal (`registry._follow_loads`), and a circle of «Formules» domains stays the tab's own (`CIRCLE`).

**Cost.** Reading the documents' sections takes most of it: about 0.6 s on the example project's 166 section files on a OneDrive folder, mostly opening the files. Each file is read once and masked once.

**Not done** (spec §8):
- The graph says what is stale; it rewrites nothing.
- The renumbering does not rewrite a steel check's position. The graph knows the edge.
- A connector's warnings are still untyped sentences.
- A fire plan whose plan is gone is still dropped from `fire.json`.

`docs/open-questions.md` lists them.
