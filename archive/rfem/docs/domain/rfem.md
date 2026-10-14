# RFEM 6 import and the rfem domain

> Reading RFEM's table export, structures, static models, and the solver's extremes.
>
> Moved verbatim from CLAUDE.md (§3.3duodecies, §3.3quindecies) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

### 3.3duodecies RFEM 6: a model read from its own table export (v0.98)

The engineer models in RFEM 6. What he has drawn there — the members, where they are held, what acts on them — is the static system Woodcore's «Modèles statiques» tab draws by hand (§3.3octies), so drawing it a second time is the duplication §2 rule 1 forbids everywhere else. This is the one place the pipeline reads a file it did not write.

**What is read is RFEM's own table export.** In RFEM: *Fichier → Exporter → Tableaux…*, tick the tables, choose *MS Excel (xlsx)* — or *CSV*, a folder of one file per table — and save. The dialog's selection can be saved as a template, so the second export is two clicks. What Woodcore needs is **Nœuds, Barres, Surfaces, Sections, Matériaux, Appuis nodaux, Articulations de barre, Cas de charge, Combinaisons**, and per load case its own **Charges sur barres** / **Charges sur surfaces** sheet; the result tables (**Barres | Efforts internes**) are read only when asked for.

⚠️ **The API is not the route.** `dlubal.api` over gRPC on 127.0.0.1:9000 reads the same model in a second and would need no export at all, and it **requires a Dlubal API key** that not every office has. So the file is what the pipeline reads, and the API can only ever be an accelerator that writes that same file (§14). Nothing in `calc/` imports `dlubal`.

### What the engineer writes in RFEM, and where

Every object in RFEM has a **comment** field, and that is where he says what the object *is* in Woodcore's terms. One `@key value` per line, `@key: value` and `@ key = value` read alike (`calc/rfem_import/metadata_parser.py`):

| key | on what | what it says |
|---|---|---|
| `@position` | **a member or a surface, and nothing else** | the row of `Positionen.xlsx` this element realises (`T001`) |
| `@model` | any object | the structure this object's component belongs to — what merges two components into one structure |
| `@label` | any object | that structure's name, as the report prints it |
| `@descr` | any object | that structure's description |
| `@load` | a load | the Woodcore load instance its value came from, `snow-load/SL-Dach1` |
| `@be` | a load | an influence width, in metres once read (`3.6`, `360 cm`, `3600 mm`) |
| `@note` | any object | free text about this object, carried through and printed nowhere |

⚠️ **The sigil is `@`, and it is `@` because RFEM destroys `#`.** A `#word` typed into an RFEM comment is read by RFEM as one of its own tags and is **gone** from the comment by the time the table is exported — so a convention built on `#` would lose the engineer's work silently, which is the failure this project treats as the worst kind. One sigil serves every key rather than one sigil per kind (`@position` a reference, `&model` a name), which was the first design and was dropped: a line written with the wrong sigil is then not a line at all, and the engineer would have four characters to remember. A line written with `&`, `$`, `>`, `!`, `+`, `:` or `~` is therefore matched too — and **reported**, naming the key and saying to write `@`, rather than being taken for prose. A `#` found in a comment is reported the same way, with what RFEM did to it.

⚠️ **A `@position` only on a member or a surface** is the engineer's own rule, and it is enforced where the object's kind is known (`validation.position_places`): a node, a support or a load carrying one is a warning naming the object. A position the workbook does not have is a warning saying what to add to `Positions Element` (`positions_resolve`), and the same position on two structures is a warning naming both (`positions_across_structures`) — identical elements may share a number (§3.3sexies, v0.44), so it is a thing to look at and not a defect.

### The tables, in three languages

`calc/rfem_import/model_tables.py` reads them, and its `SHEETS` and `COLUMNS` alias tables carry the French, German and English headers RFEM writes — **every one of them measured on a real export of the same model in the three languages**, never guessed. Six aliases written from memory were wrong (`Stabgelenke` for `Stabendgelenke`, `Lasttyp` for `Lastart`, and four more), which is why the tables are held by `tests/fixtures/rfem_model.py` rather than by care. The three languages read to the same model — the same nodes, members, sections, supports, hinges, metadata and 22 structures — and only what RFEM itself translates differs (a material's name, a load's type and distribution, a design situation, and a load case's own abbreviation CC/LF/LC, which is carried opaquely).

Four things about RFEM's own headers had to be learnt rather than assumed, and each one had silently lost a whole table first:

- ⚠️ **A hyphen in a header is never a word boundary.** RFEM hyphenates inside a cell and across the two header rows (`Last-` on one line, `kombin.` on the next) *and* uses a hyphen as a joiner (`Cross-Section`), so a header is folded by removing every hyphen and the line break with it (`csv_tables.fold`). Reading `-` as a separator lost the German combinations.
- ⚠️ **RFEM abbreviates the identifier header per language** — «Quersch. Nr.», «Last-kombin.», «Load Combs.», «Comb. charges» — so the first column is the identifier where no alias matches (`_identifier`). Without that fallback the German sections and the German and English combinations came back empty.
- ⚠️ **A number cell may be a list or a range**: a support holds `2-4`, a load acts on `1,2,5,8-10`. `numbers()` expands both, up to `RANGE_LIMIT`.
- ⚠️ **A support and a hinge read `inf` oppositely.** On a nodal support an infinite spring constant means *held*; on a member hinge it means *not released*. Both came out «pinned» until `Restraint.role` told the reader which table it was in.

⚠️ **A table of no rows is a table.** The engineer's own model has no surfaces, and a headers-only sheet was refused as malformed until `_headers` stopped claiming two header rows in a one-row file.

⚠️ **The load cases are not numbered rows.** A load case's identifier is `CC1`, not a number, and `Table.data_rows()` — which drops a row whose first cell is not a number — is a *results* notion (§3.3duodecies's results, below). Reading the model through it gave back a model with **no loading at all, silently**; the model reader reads `table.rows` and skips an empty numbered row into `skipped` itself.

⚠️ **The workbook is read lazily** (`csv_tables.Workbook`): his export is 490 sheets and 13.3 MB, of which the 19 sheets that are read are **36 kB**. Reading it eagerly took 43 s to use 4 % of it; `sheet()` resolves a name without reading, and only `_load()` reads. A sheet name is matched by prefix as well, Excel truncating a sheet name at 31 characters.

⚠️ **CSV or XLSX is measured, not argued** (the engineer's question): opening the 490-sheet workbook is 1.48 s and reading the 19 tables out of it 0.07 s, so end to end it is 0.92 s against 0.24 s for the same tables as CSV. **XLSX is kept** — it is one file to move, one to name in the project and one to hash — and the lever is which tables are read, not which format they are in. A folder of `.csv` is read all the same, by the same reader (`_Source`), for an office that prefers it.

### The structures

A model is not one static system. `calc/rfem_import/structure_detection.py` groups the members and surfaces into **connected components** by the nodes they share (union-find, the lowest number kept as the root), attaches to each component every support, hinge and load that sits on one of its elements, and then **merges components that carry the same `@model` name** — a system in two halves joined by nothing RFEM models, a cable stayed against a wall, is one structure the moment the engineer says so.

⚠️ **One object may belong to more than one structure.** A nodal support in RFEM holds a *list* of nodes, and his support 2 holds 23 of them across several components. So an item is placed in every component it reaches (`_roots_of`), `Structures.shared` says which items are in more than one, and what is accounted for is counted **by identity** rather than by adding the components up.

A structure carries its key (the lowest element number in it), its `@model` name, its `@label` and `@descr`, its nodes, its items, the load cases and combinations that act on it, and the problems found in it. Its name is decided per component and then across the merged group, so two components merged by a name agree on one label and one description. **On the engineer's own model this gives 22 structures**, most of one to six members, one of them named `VU-gunstig`.

### What it means, and what is wrong with it

`calc/rfem_import/validation.py` is the half that knows Woodcore: it resolves what the metadata names and reports what it cannot. `position_places` (the rule above), `positions_resolve` and `positions_across_structures`; `sections_agree`, which compares RFEM's own cross-section dimensions with what `Positionen.xlsx` states for that position, to `SECTION_TOLERANCE` (0.1 mm); `loads_resolve`, which looks a `@load` up among the export's own load instances; `widths_plausible` (`MAX_WIDTH`, 100 m — an influence width of 3600 typed in metres); and `structures_named`, which lists the structures that have no name and so will not be imported.

⚠️ **It found a real disagreement on the engineer's own model, which is the argument for its existing**: member 24 carries `@position T001` and RFEM draws it 500/200 mm, where `Positionen.xlsx` states 100/200. Both numbers are printed, and neither file is touched.

⚠️ **Nothing here refuses.** Every finding is an `engine.Note` — a code, an English sentence and its values — which the window writes in its own language (§4bis, the v0.79 rule): the export is the engineer's file, read and not validated, so a comment he has not finished typing must not stop the report.

### The intermediate JSON

`calc/rfem_import/json_export.py` writes **`data/rfem/<export>.json`**, schema `rfem-import` **1.0** (`schemas/rfem-import.schema.json`): the `source` (its path as the project names it, its size and its SHA-256), the `model` (nodes, members, surfaces, sections, materials, supports, hinges, cases, combinations, loads), the `metadata` each object carries, the `structures`, the `problems`, and `results` — **absent** when none were read, rather than an empty object that would read as «none found». ⚠️ JSON has no infinity, so an infinite spring constant is written as the string `"inf"` (`_finite`).

It is the file a checker opens: one place that says what was read out of RFEM, what Woodcore took it to mean, and what it could not resolve. `sweep()` removes the record of an export the project no longer names, as every other generated folder is swept.

### The static models

`calc/rfem_import/import_controller.py` turns a **named** structure into a `statics-source` record (§3.3octies) — `models_of(..., named_only=True)`: a structure with no `@model` or `@label` has no id to be addressed by, so it is listed and not imported.

**The frame needs no conversion.** Woodcore draws x right and **z down** (§3.3octies), which is RFEM's own global frame here, so a coordinate is carried over as it stands and no sign is flipped. What is translated is the vocabulary: a support's kind (`SUPPORT_FROM`), a hinge's degree of freedom (`RELEASE_FROM`, a rotational spring becoming a moment release carrying its stiffness in `kNm/rad`), a load's direction and its distribution (`UNIFORM`), and a member's own kind read off its RFEM type (`BEAM_TYPES`).

⚠️ **A load's number is per load case**, so an id made from the number alone collided the moment two cases were read: a load's id carries its case, `qCC1_4_26` (`_case_part`). ⚠️ **A release's `stiffness` is `{value, unit}`** and not a bare number — which the *fixture* caught and the real export could not, his member 24 carrying a plain moment release and the one spring in the model sitting on a member of an unnamed structure.

⚠️ **The record goes to `data/statics.json` and never to `Woodcore-Datei/statics/`.** That is the engineer's own decision and this section's most important line: `Woodcore-Datei/` is what he draws, and a file written there by an importer would be a drawing he did not draw, editable in a tab that would then write it back and lose whatever RFEM said next. So `statics.prepare(source_dir, values, generated=…)` takes the imported records beside the drawn ones, checks each with the same `check_source` (§3.3octies), and **refuses a duplicate id naming both** — a model drawn in Woodcore and an imported one of that name cannot both be `VU-gunstig`. They are regenerated at every export, so RFEM stays the source.

⚠️ **The forces are read behind a flag.** `prepare(..., read_results=False)`: reading a workbook's member-forces sheets takes **105 s** against 1.1 s for the model, so an export reads the model every time and the forces when asked (`woodcore-cli import --results`). What is read is every combination's own sheet, keyed by its abbreviation (`results.py`, `_LOADING`) — ⚠️ **the CSV writes `V_y` where the XLSX writes `Vy`**, so both are aliases of one force (`FORCE_ALIASES`).

👉 **Four independent routes agree to the digit**, which is what a reader of this section should know before trusting a number that came out of RFEM: the GUI's CSV export, the API's own `get_results` DataFrame, the workbook's result sheets and the stations counted by hand all give CO1's largest moment as **15.97 kNm on member 64 at x = 2.115 m**, member 1's normal force as **−17.0937 kN**, and CO1 as 385 stations.

### 3.3quindecies The `rfem` domain: what the solver found, read and never enveloped here (v0.100)

An RFEM structure is a **domain instance** (§3.3): `("rfem", "VU-Regelfall-Stuetze")`, one per named structure, in a file of its own — `data/rfem.json`, the arrangement a connector and a connection already have (§3.3quinquies), since it is exported on its own and belongs to no position. The engineer's own words: «Chaque Structure est un domaine … Dans typst, le user peut appeler un domaine rfem (i.e. une structure rfem). Depuis là, il peut appeler les efforts et déformations maximums par barre.»

**Because it carries the §3.3 shape, nothing in the report had to be taught about RFEM**: `#val`, `#find`, `#show-calc`, `#var(domain:)` and the summary tables all read it unchanged. `engine` is **`rfem`**, a fourth kind beside `excel`, `python` and `norm`, and every var's `source` says so with the export, the design situation and the combination — `rfem:260929-01_29509-Model.xlsx!SP1!CO3` — so a number on the page is traceable to the sheet without opening anything.

**The extremes are read, not computed.** RFEM's table export carries, beside the 48 combinations, the four *result combinations* the design situations are — SP1 ELU fondamental (29 CO), SP2 ELS rare (14), SP3 ELS fréquent (4), SP4 ELS quasi-permanent (1) — and each of their tables has one column a combination's has not: **«Chargement correspondant»**, naming the combination that reached the value on that row. So «l'effort maximal, et la combinaison de charge qui a calculé cet effort maximal» is a reading (`calc/rfem_import/envelopes.py`). It is also 4 tables instead of 48: the forces of every combination cost 11.9 s on the engineer's own export, the four envelopes about 6 s for forces, deformations and support reactions together.

⚠️ **One reader for three tables, because the criterion names the column.** Member internal forces, member deformations and nodal reactions are written one way — a row per object, per abscissa, per criterion, and the criterion *is the name of the column that row is extreme in*. Nothing holds a list of what each table contains.

⚠️ **A sheet holds more than one block and they are not the same width.** Measured: `SP1 | Barres | Efforts internes` writes 1812 rows with a leading *section* column, then a «Total» and a «max/min» trailer, then **770 more rows without it**, every cell one to the left; every `CO` sheet does the same, 84 rows one way and 578 the other. A reader that trusts the header's indices reads the second block with every value in the wrong field, in silence. The criterion is therefore found **in the row** (`results.criterion_at`) and the whole row read at the offset that puts it where the header says. ⚠️ **It was a live defect**: `forces_of` found no single criterion column at all, so 84 extremes rows per combination were read as **stations** and drawn on the diagrams. CO1 went from 222 stations to 144, and the row accounting balances.

⚠️ **A deformation table carries two kinds of row and only one is an envelope.** RFEM writes `max` and `min` rows, which are the **column-wise** extremes — each column's own, from different combinations — and therefore name no loading; then a row per quantity, which is one combination's and names it. Only the second is read: a row that cannot say which combination produced it is a row a report cannot cite.

⚠️ **The concomitant values are kept.** The row carrying the largest M_y also carries the N and the V *acting at that moment under that combination*, which is what a bending-and-normal-force check reads. What is not kept is any attempt to combine them.

**A bar is one RFEM member** (the engineer's own choice of three), identified by the position its comment names and an index: `T001_1`, `T001_2`, in increasing member number within the structure. ⚠️ **The index is always written, even where the position occurs once**: `T001` alone would be shorter today and would become `T001_1` the day a second member of that position joins the structure, and every call naming it would break in silence. A member whose comment names no position is carried as `bar_<number>` — its forces are real, and dropping them would lose them without a word.

⚠️ **The design situation is part of the variable's name**: `SP1_T001_1_M_y_max`. The engineer asked that one always state which situation or combination is being looked at; with one instance per structure a bar holds four maxima, and only the name can tell them apart. The printed symbol stays `M_(y,"max")`.

⚠️ **A quantity that is identically zero on a bar is left out, and said out loud** (`zero`). This model is a plane frame, so V_y, M_T, M_z, u_y, φ_x and φ_z are exactly zero on every one of its 62 members — **4955 of 7696 vars, two thirds of the file**, every one a number no report would print. They are dropped per bar and **across every situation**, never in one and not another, and `zero` names them so that «this structure carries no M_z» and «this export was read without M_z» stay two statements. `data/rfem.json` went from 2.4 MB to 1.05, and Typst reads it on every compile.

**The loadings travel with the domain**: `cases` and `combinations`, each combination with its **terms** — `CO3 = [(1.35, "CC1"), (1.5, "CC2")]` — so a report can print `1.35 · CC1 + 1.50 · CC2` or, with the cases' own names, `1.35 · (EG + AL) + 1.50 · Schnee`. ⚠️ **A case's name may itself be a sum**: CC1 is «EG + AL», so `1.35 · EG + AL + 1.50 · Schnee` reads as three terms. The engineer's own rule: parenthesise as soon as the name is not a simple word. Two exports that give one id two different definitions are reported and the first kept, rather than one standing for both.

**In Typst**: `rfem-ids()`, `rfem-bars(structure)`, `rfem-situations(structure)` are the data access, and three display commands (§10bis) — `rfem-max` for one extreme with its combination, `show-rfem-forces` for a bar's whole table of them, `show-rfem-combination` for a combination's formula. ⚠️ **`rfem-max` is a third command beside the two the engineer named**, and for a reason he did not have to foresee: `#val` prints the value and cannot print the combination, which is the half his «(1)» asks for.

**The curve of an internal force is reconstructed, exactly** (`calc/rfem_import/diagram_curve.py`). RFEM's tables list a member's forces at its **characteristic points only** — the engineer's 4.23 m beam comes out of CO1 with four rows, x = 0, 2.115, 2.115, 4.23 — so a polyline through them draws a **triangle** where the diagram is a parabola, which is what he reported: «Les efforts peuvent également être courbes.» The shape is read back out of the numbers already exported, by the relation every diagram obeys: **the shear is the slope of the moment**. Value and slope at two points are four conditions and a cubic has four coefficients, so the Hermite interpolant *is* the diagram wherever it is a polynomial of degree three or less — which a uniform or a linearly varying load makes it. ⚠️ **The sign of the relation is measured, never assumed**: both are tried over every segment of every member of one table and the one whose integral reproduces the exported moments wins; where neither does, the reconstruction is **refused** and the polyline is drawn through the stations exactly as before. ⚠️ **Only the moments are reconstructed** — a shear under a uniform load is already a straight line between its stations. ⚠️ **The values written on the figure stay RFEM's**: the refinement adds points to the drawn line and to nothing else, so no number beside a diagram was computed here. Verified on CO1, member 2: integrating V_z from 0 to 2.115 m gives **−8.527614** where RFEM exports **−8.527615**.

**An imported model's presentation is the engineer's** (`calc/domains/statics_view.py`, his own answer B of three): the model stays generated and regenerated at every import — the v0.98 rule, which stands — and a small file beside it keeps what he chose. `Woodcore-Datei/statics/views/<id>.json` holds the three size factors the drawing is set with and which internal force is drawn over the system, for which loading, with what written beside it. ⚠️ **It is in a subfolder**, because `statics.source_paths` globs `*.json` at the top of the folder and would read a view as a model and refuse it for having no points — the `details/` trap of §3.3decies, met again. ⚠️ **A view *replaces* the drawing's three factors**, where one *entry* of a drawing states a factor **multiplying** them (§3.3quaterdecies): there is one drawing and one engineer, so a view is the drawing's own setting. ⚠️ **The diagram is rendered by the import and nowhere else**, that being the only place that can read RFEM's distribution; `statics.prepare` takes the SVG out into `data/statics/<id>-diagram-<lang>.svg` and the record keeps only what it is, so no figure's source text sits in a file Typst reads on every compile. `#show-static-model(model, diagram: true)` prints it. ⚠️ **A view of a model that is gone is kept and reported**, never deleted: an export renamed, a structure renamed in RFEM, a workbook not synced yet — none is a reason to throw away a page of settings. And a **drawn** model has no view and is refused one: it carries its own `style` and its own everything.

⚠️ **The diagram is drawn for a combination and not for a design situation.** An envelope has no single curve but a **band** — a max and a min at every station — which is a different object; SP is what the *numbers* come from and CO what the *curve* comes from, and the engineer's own rule covers both («toujours préciser quelle situation ou combinaison on regarde»). The band is §14's.
