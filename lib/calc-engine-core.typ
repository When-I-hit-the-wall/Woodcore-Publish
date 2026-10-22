// lib/calc-engine-core.typ -- the report's level, the numbers, the data and its access (`ids`, `get`, `find`), the formula laid out on its rows, the position and connector summary lines.
// Split out of lib/calc-engine.typ by subject, its text moved and not rewritten (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, G9). Each part imports the one before it, so a name reads everything defined above it as it did in one file; lib/calc-engine.typ imports the last and is what every caller names.

// Display layer for the calc/ -> data/ pipeline (docs/typst/report-engine.md §4-10). Typst never computes anything here -- it only reads and formats what calc/export_all.py already validated and wrote to data/.

// Every word this file prints comes out of one glossary, in the report's language (docs/typst/language.md §4bis). `t-str` is the engine's own word by a key, `tl-str` a string the data carries -- translated if the glossary knows it, left alone if not, which is what keeps a material's name and an Excel description in the engineer's own words. Imported here rather than in each section, so commands.typ re-exports it with the rest.
#import "i18n.typ": *
// how a number is written: the one display rule, and the rounding it is built on (UI-002, UI-003, v0.120)
#import "number.typ": *
// how a subscript is written: every symbol and formula is evaluated through `math-eval` (UI-001, spec 2026-10-20-indices-et-niveaux)
#import "subscript.typ": *

// --- Report level (docs/typst/report-engine.md §4) -----------------------------------
/// The report's default level of detail, 1, 2 or 3 (section 3.7). Set once in `Statischer Rapport.typ` — `#report-level.update(2)` — from `--input level=`; any call overrides it locally with `level:`.
///
/// ```typ
/// #report-level.update(3)
/// #var("s_k", domain: ("snow-load", "SL"))
/// ```
///
/// ```typ
/// #report-level.update(1)
/// #var("s_k", domain: ("snow-load", "SL"))
/// ```
///
/// -> state
#let report-level = state("report-level", 1)

/// The level forced on **every** call, or `none` (section 4). Set only for the uniform variants in `out/`, from `--input uniform=1|2|3`: while it holds a level, every call renders at exactly that one and the per-call `level:` overrides written in `Sections/` are ignored -- what a `#sync` holds aside, printed as it is written — which is the only way to get a PDF that really is one level throughout, an override being a literal argument no outside state could otherwise disarm. `none`, the normal case, honours them.
///
/// ```typ
/// #uniform-level.update(1)
/// #var("s_k", domain: ("snow-load", "SL"), level: 3)
/// ```
///
/// ```typ
/// #uniform-level.update(none)
/// #var("ce", domain: ("snow-load", "SL"), level: 3)
/// ```
///
/// -> state
#let uniform-level = state("uniform-level", none)

/// The level a show-* call actually renders at (docs/typst/report-engine.md §4). Three sources, in order: the uniform level if one is forced, else the call's own `level:` when it states one, else the global report level. Call inside `context` -- it reads two states.
/// - level (int, auto): the `level:` the calling show-* function was given.
/// -> int
#let resolve-level(level) = {
  let forced = uniform-level.get()
  let from-state = if forced != none { forced } else if level == auto { report-level.get() } else { none }
  if from-state == none { return level }
  // ⚠️ The two states are checked where they are read (v0.86): `#report-level.update(0)` hid every #var and #val while show-calc went on printing, `update(4)` printed level 3 without a word, and `update("2")` failed on «cannot compare string and integer». 0 is a level of one call, never of a report (section 4).
  if not (from-state in (1, 2, 3)) {
    panic("the report level is " + repr(from-state) + " -- report-level and uniform-level take 1, 2 or 3; "
      + "0, which prints nothing, is given to one call as level: 0 (docs/typst/report-engine.md §4)")
  }
  from-state
}

// --- The level of a figure, a table or a list (spec 2026-10-20-indices-et-niveaux, UI-003, D-04, D-07) ----
// Every command that prints takes `level:` (Q-007 of the base saine): 1 the figure, the table or the list alone; 2 with its legend and its titles -- what a document printed until v0.120, its own level 2 being unchanged --; 3 with its sources and its citations, where it has any (build_reference_lib.LEVELS_CONFOUNDED names those that have none, and why).

/// The level a figure, a table or a list prints at: its call's `level:` -- auto, 1, 2 or 3 -- resolved as every command's is (`resolve-level`: the uniform level, else the call's, else the report's). Call inside `context`.
///
/// ```typ
/// #context print-level("image-positions-plan", auto)
/// ```
///
/// ```typ
/// #context print-level("image-positions-plan", 3)
/// ```
///
/// - fn (str): the command's name, for the message where `level` is not one of auto, 1, 2, 3.
/// - level (auto, int): the call's `level:`.
/// -> int
#let print-level(fn, level) = {
  if not (level in (auto, 1, 2, 3)) { panic(fn + ": invalid level " + repr(level) + " -- use auto, 1, 2 or 3") }
  resolve-level(level)
}

/// An argument whose default is `auto` decided by the level: what the call wrote where it wrote it -- `legend: false` stays false at every level --, else printed from level `from` on.
///
/// ```typ
/// #at-level(auto, 1, 2) -- #at-level(auto, 2, 2) -- #at-level(true, 1, 2)
/// ```
///
/// ```typ
/// #at-level(false, 3, 2)
/// ```
///
/// - arg (auto, bool): the argument as the call wrote it.
/// - lv (int): the level the command prints at (`print-level`).
/// - from (int): the level it is printed from when the call leaves it `auto`.
/// -> bool
#let at-level(arg, lv, from) = if arg == auto { lv >= from } else { arg }

// The figures' colours and font, lib/figure-palette.json -- the drawing engines of calc/domains/ read the same file (svg_draw.colour), so a figure the report draws itself (a scale bar, a halo, a connection's arrows) is in the very colours of one Python drew (spec 2026-10-19-base-saine-nettoyage, D5). A colour is named by its token, as `figure-colour("ink")`, a `#rrggbb` string an SVG takes as it is and `rgb()` reads.
#let figure-palette = json("figure-palette.json")
#let figure-colour(token) = figure-palette.colours.at(token)

// A citation as the page sets it: in the palette's `ink-soft` grey, so that it draws the eye less than the calculation it cites (spec 2026-10-21-commandes-typst-refonte, UI-001, D-10) -- `ink-soft` and not `muted`, which is too pale to read at 8 pt. `size` is the citation column's 8 pt, and `auto` for a citation in a sentence, which keeps the size of its text.
#let cite-text(body, size: 8pt) = if size == auto { text(fill: rgb(figure-colour("ink-soft")), body) } else { text(size: size, fill: rgb(figure-colour("ink-soft")), body) }

// A coordinate as SVG text: `digits` decimals, and a hyphen for the sign -- Typst's str() writes a typographic minus, which an SVG parser does not read, so an element whose coordinate is negative would be dropped without a word. The one writer of a number into a figure's SVG; each figure keeps the precision its Python engine draws at (calc/domains/svg_draw.number_at): 2 for a plan, a schema and a connection, 3 for a static model (spec 2026-10-19-base-saine-nettoyage, D7, which merged plan-number, static-number, schema-number and the connections' own svg-number).
#let svg-number(x, digits: 2) = str(calc.round(x, digits: digits)).replace("−", "-")

// --- Number formatting (document-wide) ------------------------------------
// `number-digits` set how many decimals the report printed, until v0.120. Since then every number is printed by one rule (lib/number.typ, `display-number`: three decimals at most, powers of ten past 99 999 -- the engineer's decision of 19.10.2026, spec 2026-10-19-base-saine-nettoyage UI-003), and the setting changes nothing. The state stays so that a document written before -- every template set `#number-digits.update(3)` -- still compiles; it is no longer a command of the reference.
#let number-digits = state("number-digits", 3)

// --- The variables a report writes by hand (docs/typst/formulas.md §10quinquies) -
// One dictionary for the whole document: `#var` and `#eq` write into it, and `#eq`, `#verify` and `#val` read it back by name. That is what lets a formula name its own operands -- `` `F_Ed / R_d` `` -- instead of repeating them in a `where:`, which is what made v0.60's eq unreadable: a variable had *three* names (the Typst binding `R-k`, the `where:` key `R_k`, the printed symbol `R_"k"`), the three had to agree, and nothing checked that they did.
//
// ⚠️ A name here is a **string**, and this dictionary is where it lives: Typst gives a function no way to bind a name in its caller's scope -- there are no macros, and `eval(scope:)` evaluates in a fresh scope -- so `#var("R_k", 7, "kN")` cannot create a `#let R_k`. That is the whole reason for the registry, and it is not a limitation anyone can lift later.
//
// The domain stack lives *inside* the same dictionary rather than in a state of its own, and that is not tidiness: a state's update function cannot read another state, so `var-registry.update(d => ...)` -- which is where a variable is computed and stored, outside any `context` -- has to find the current domain in `d` itself. `var-domain` pushes and pops it exactly as calc-block pushes block-scope.
#let var-registry = state("var-registry", (stack: ("",), domains: (:)))

// The name the report's own variables travel under **inside the PDF** (v0.110): `woodcore-document` attaches
// them there, and `calc/variables.py` reads them back out by this name. Written in both places and held equal
// by `tests/test_variables.py`, the way the registry's own default is -- a name that drifted would not fail,
// it would leave the window quietly compiling the report again on every opening for want of finding it.
//
// ⚠️ **Typst resolves this as a path, relative to the file that calls `pdf.attach`**, so what reaches the PDF
// is `_woodcore/lib/woodcore-variables.json` -- the engine's own place inside the project. Measured, not
// assumed. `calc/variables.py` therefore matches on the **basename**, which is right whatever a project calls
// its generated folder (`layout.generated` is a project's to state, §12) and whatever Typst does with the
// prefix later.
#let variables-attachment = "woodcore-variables.json"

// The domain a variable written at this point belongs to: the innermost var-domain, or "" outside them all.
#let var-current(d) = d.stack.last()

// One variable by name: the current domain first, then the default domain "". That fallback is what lets R_d, declared at the level of a section, be named inside the columns of a grid that each declare a domain of their own. `none` when there is no such name.
#let var-lookup(d, key) = {
  let here = var-current(d)
  if here in d.domains and key in d.domains.at(here) { return d.domains.at(here).at(key) }
  if "" in d.domains and key in d.domains.at("") { return d.domains.at("").at(key) }
  none
}

// Every name a formula written at this point could cite, for the message of one that is not among them.
#let var-names(d) = {
  let here = var-current(d)
  let names = if "" in d.domains { d.domains.at("").keys() } else { () }
  if here != "" and here in d.domains { names += d.domains.at(here).keys() }
  names.dedup().sorted()
}

// Writes one variable into the current domain. A pure function of the dictionary, so that it runs inside `var-registry.update(...)` and never has to read a state.
#let var-store(d, key, record) = {
  let here = var-current(d)
  let dom = d.domains.at(here, default: (:))
  dom.insert(key, record)
  d.domains.insert(here, dom)
  d
}

// --- Data access (docs/architecture/principles.md §2) ------------------------------------
#let load-position(id) = json("../data/positions/" + id + ".json")
#let load-calculations() = json("../data/calculations.json")

// The positions deleted with their values kept («Copier les valeurs», issue #9, calc/renumbering.py): «S110-old», which a call may still name and no list of the project's positions shows. A project exported before has none.
#let archived-position-ids() = json("../data/positions-index.json").at("archived", default: ())
// Every id a call may name: the project's positions, and the old ones whose values were kept.
#let known-position-ids() = json("../data/positions-index.json").positions + archived-position-ids()

/// The project as its `.woodcore` file describes it, and what produced this export: `name`, `number`, `client`, `address`, `company`, `author`, `checker` -- each "" where the file leaves it out -- and `woodcore` (its `version` and git `revision`), `typst` and the `workbooks` read with their SHA-256 (data/project.json, docs/architecture/layout.md §11, v0.82). Data access, not a display function: what a title page is written from, so the project's name is typed once, in its file.
///
/// ```typ
/// #project-info().name
/// ```
///
/// ```typ
/// #let info = project-info()
/// #text(size: 14pt)[#info.name] \
/// Woodcore #info.woodcore.version
/// ```
///
/// -> dictionary
#let project-info() = json("../data/project.json")

// --- Which document of the project is being compiled (three documents, docs/domain/journal.md §3.3terdecies) ---
// A project holds up to three documents -- the convention d'utilisation («cu»), the base de projet («bp») and the statical report («rs», the one a project has always had) -- compiled one by one against ONE engine and ONE export. What tells them apart at compile time is the `document:` of `woodcore-document`, which each entry file states once (`#show: woodcore-document.with(document: "cu")`) and which is kept here, so that a command printing something that belongs to one document and not to the others -- today the revision journal, each document having its own -- reads it without being told.
//
// ⚠️ A state is read only inside a `context`, and is read there from what the **previous** layout pass recorded: in the first pass of a convention d'utilisation `wc-document.get()` still says «rs», in the second «cu», and the third finds nothing moved. Nothing is lost by it -- every journal is in the export, so the first pass reads one that exists -- but it is why a function that must work outside a context (`journal-entries`) takes the document as an argument and defaults to «rs» instead of asking this state.
//
// The default «rs» is what a document that never says which it is gets -- the statical reports written before there were three documents, every probe of the test suite and every worked example of the commands tab -- so that a report that does not call `woodcore-document` with a `document:` is, to the byte, the report it was.
//
// The name is the state's key, and is not `document`, which is a Typst global (`set document(title: ...)`) that a binding here would replace in every file of every report (section 10bis, point 3).
#let wc-document = state("woodcore-document-id", "rs")

// Where a figure the export wrote lies, as its JSON names it -- the one place the engine resolves one (spec 2026-10-15 ARCH-003). A project laid out by folders (issue #64) has its figures in each tab's `Exports/Figures/`, their one copy, and names them from the Typst root, `/Plans/Position-plan/Exports/Figures/P01.svg`, which Typst reads as it stands from any file; every export before, and every project laid out before, names them under the export's `data/`, `plans/P01.svg`, read beside this file as `../data/plans/P01.svg` -- so an old export goes on being read as it was (calc/engine.py `Figures`).
#let figure-path(file) = if file.starts-with("/") { file } else { "../data/" + file }

// The file each document's journal is exported to, in `data/`, written by `calc/journal.py` and held equal to `calc/documents.py`'s `JOURNAL_FILES`. One journal per document: each prints its own «Historique des versions», and a revision of the convention does not make the statical report a revision.
#let journal-files = (rs: "journal.json", cu: "journal-cu.json", bp: "journal-bp.json")

// One document's journal, read from the export: `{schema_version, entries}`, the entries **newest first**. Declared here and not beside `journal-entries`, which it serves, because `woodcore-document` reads it for the PDF's keywords and Typst's top-level bindings are not hoisted -- a function cannot name one defined further down. Nothing is computed.
//
// `document: auto` is **the document being compiled** -- `wc-document`, so only inside a `context`; a name ("rs", "cu", "bp") is that document's journal anywhere. A name the project has no journal for, and a value that is not a name, stop the compile listing the ones it has.
#let load-journal(document: auto) = {
  let id = if document == auto { wc-document.get() } else { document }
  assert(type(id) == str and id in journal-files,
    message: "no journal for the document " + repr(id) + " -- documents: " + journal-files.keys().join(", "))
  json("../data/" + journal-files.at(id))
}

/// The captions of a document, the engineer's way (v0.117): «Tableau 1 — Les documents de référence», «Figure 1 — Système statique» -- the word of its kind in the report's language (`figure.supplement_table`, `figure.supplement_image`), its number, a long dash, its title. `woodcore-document` applies it to every document of a project, so the engine's tables and figures and the author's own read alike; a project's `config.typ` saying otherwise is overridden, the format being the office's.
///
/// ```typ
/// #show: caption-rules
/// #figure(table(columns: 2)[A][B], caption: [Les documents de référence])
/// ```
///
/// ```typ
/// #show: caption-rules
/// #figure(rect(width: 2cm, height: 1cm), caption: [Système statique])
/// ```
///
/// - doc (content): the document.
/// -> content
#let caption-rules(doc) = {
  show figure.where(kind: table): set figure(supplement: context t-str("figure.supplement_table"))
  show figure.where(kind: image): set figure(supplement: context t-str("figure.supplement_image"))
  set figure.caption(separator: [ — ])
  doc
}

/// The tables of a document written in raw Typst, the engine's way (spec 2026-10-21-commandes-typst-refonte, REQ-019): no rule but those the table writes -- the three of a report, thick above the header, thin under it, thick under the last row, `table.hline` in the table itself --, cells padded as the engine's own tables are, the caption above the table and the table set from the left. `woodcore-document` applies it to every document, so a `#table` written by hand and one Woodcore wrote read alike.
///
/// ```typ
/// #show: doc-tables
/// #figure(
///   table(
///     columns: (auto, 1fr),
///     table.hline(stroke: 1pt),
///     table.header([*Bauteil*], [*Beschreibung*]),
///     table.hline(stroke: 0.5pt),
///     [Dach], [Flachdach, extensiv begrünt],
///     table.hline(stroke: 1pt),
///   ),
///   caption: [Bauteile],
/// )
/// ```
///
/// ```typ
/// #show: doc-tables
/// #table(columns: 3, align: (left, right, right), [Last], [2.5], [kN/m²])
/// ```
///
/// - doc (content): the document.
/// -> content
#let doc-tables(doc) = {
  set table(stroke: none, inset: (x: 5pt, y: 4pt))
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: table): set figure(gap: 0.5em)
  show figure.where(kind: table): set block(breakable: true)
  show figure.where(kind: table): set align(left)
  doc
}

/// The PDF's own metadata from the project's file, as a show rule: its title the project's name, its authors the report's author and office, and its keywords the Woodcore version and revision and the Typst version that produced it -- so a PDF found years later says which program made it (docs/architecture/layout.md §11, v0.82) -- and, since v0.99, **which revision of the report it is**: «Rev. 3 (2026-09-27)», the newest entry of the journal (section 3.3terdecies), so that two PDFs of one project can be told apart by their properties and not only by their pages.
///
/// ```typ
/// #show: woodcore-document
/// A report whose PDF names its project and its program.
/// ```
///
/// ```typ
/// #show: woodcore-document
/// = Statischer Bericht
/// Die Metadaten des PDF nennen das Projekt und das Programm.
/// ```
///
/// A project holds up to three documents, each with its own entry file and its own PDF, and each entry file says which it is once: `#show: woodcore-document.with(document: "cu")`. That is what makes `show-journal` print the journal of *that* document, and the PDF's keywords name *its* latest revision. A statical report says nothing and is `"rs"`, which is what it was before there were three.
///
/// - doc (content): the whole document, as a show rule hands it over.
/// - document (str): which of the project's documents this is -- `"rs"` the statical report (the default), `"cu"` the convention d'utilisation, `"bp"` the base de projet. For `"cu"` and `"bp"` the revision the keywords name is the newest entry of `data/journal-cu.json` or `data/journal-bp.json`, which every export writes; Typst cannot ask whether a file is there, so a project whose export has never run stops the compile on the missing file. For `"rs"` it is read from `data/project.json` as before. Any other name is refused, listing these three.
/// -> content
#let woodcore-document(doc, document: "rs") = {
  assert(type(document) == str and document in journal-files,
    message: "woodcore-document: no document " + repr(document) + " -- documents: " + journal-files.keys().join(", "))
  let info = project-info()
  let authors = (info.author, info.company).filter(a => a != "")
  let program = "Woodcore " + info.woodcore.version + if info.woodcore.revision != "" { " (" + info.woodcore.revision + ")" } else { "" }
  // The report's own revision, where its journal has one. Read from data/project.json rather than from data/journal.json, and with a default: a `set document` rule stands at the top of a document and cannot ask whether a file is there, so a second `json()` here would stop every report of a project whose engine was updated without being exported again. «Rev.» is left as it is, in every language: a keyword is a search term in a file's properties, not a word on the page, and this rule runs before the report's language is set.
  //
  // ⚠️ **A convention d'utilisation or a base de projet reads its own journal instead** (`document: "cu"` / `"bp"`): the statical report's revision lives in `data/project.json` so that a revision of the report is one more thing the report's own compile already reads, and a revision of *another* document in that file would make the statical report look changed every time the convention is -- which the export-only-if-changed rule would then recompile for nothing. So a CU or a BP reads `data/journal-<document>.json`, which the export **always** writes (`export_all.seed`, like every other file of `data/` a report reads), and which is the one file a `set document` rule can read without being able to ask whether it is there. Its entries are newest first, so the first is the revision the document is at. A journal with nothing in it gives no keyword, as a project record with no `revision` does.
  let revision = if document == "rs" { info.at("revision", default: none) } else {
    let entries = load-journal(document: document).entries
    if entries.len() > 0 { entries.first() } else { none }
  }
  let typst-keyword = if info.typst != "" { ("Typst " + info.typst,) } else { () }
  let revision-keyword = if revision != none { ("Rev. " + str(revision.index) + " (" + revision.date + ")",) } else { () }
  let keywords = (program,) + typst-keyword + revision-keyword
  // ⚠️ `document` is this function's own argument now, so Typst's `document` element is reached as `std.document`.
  set std.document(title: info.name, author: authors, keywords: keywords)
  // Which of the project's documents this is, for whatever below reads it (`show-journal`); an invisible update, emitted before `doc` so that every context inside it sees it.
  wc-document.update(document)
  // the captions: «Tableau 1 — …», «Figure 1 — …» (caption-rules, v0.117)
  show: caption-rules
  // the tables written in raw Typst, the engine's way (doc-tables, spec 2026-10-21-commandes-typst-refonte, REQ-019)
  show: doc-tables
  doc
  // ⚠️ **The report's own variables, carried inside the PDF itself** (v0.110, the engineer's choice of three).
  // Everything `#var`, `#eq`, `#var-unit`, `show-polar-moment` and every `verify-*` computes lives in
  // `var-registry` and reaches no `data/` file, which is docs/project/purpose.md §1's standing condition on anything
  // computed in Typst -- so the only way Python can say what a report holds is to compile it, and a compile is
  // 8-10 s. This is the one moment that compile is already being paid for: the PDF's own. The attachment costs
  // a few hundred bytes, adds **no page**, and is **silently ignored for a PNG or SVG target**, so the frozen
  // example pages and the website's renders are untouched (both measured before this was written).
  //
  // 👉 It is read back by `calc/variables.py` with the pypdf already pinned, which is what lets Woodcore's
  // «Variables» tab open instantly on a report that has just been exported instead of compiling it again.
  // The name is `variables-attachment` here and `variables.ATTACHMENT` there, held equal by a test.
  //
  // ⚠️ Deterministic, so an unchanged report still writes an unchanged PDF: the registry is a dictionary in the
  // order the document declared it, and nothing here carries a date -- the same reason `data/project.json`
  // carries none (§12).
  context pdf.attach(
    variables-attachment,
    bytes(json.encode(var-registry.final())),
    description: "Woodcore: the variables this report computes, by domain",
  )
}

// The connections saved in Woodcore (docs/domain/connections.md §3.3quinquies), in their own file: data/connections.json. Each is a {vars, steps, checks, tables, results} record like any calculation, addressed as the domain "connection" with the connection's id as its instance -- `show-calc("connection", "VU-MP-1")`, `var-of("connection", "VU-MP-1", "I_p")` -- plus the geometry show-polar-moment distributes forces over.
#let connection-domain = "connection"
#let load-connections() = json("../data/connections.json")

// The connectors of connectors/<id>.json, written by Woodcore (docs/domain/connectors.md §3.3nonies), in file-name order: descriptive records with their own shear-resistance calculation.
#let connector-domain = "connector"
#let load-connectors() = json("../data/connectors.json")

// The steel checks of Woodcore's «Acier» tabs (issues #50-#52, docs/domain/steel.md): computed by the export, once (calc/domains/steel_check.py), each a {vars, steps, tables} record show-calc prints as it is -- `#show-check-steel` (lib/steel.typ) heads it and prints its verdict. A file of its own, as a connector's is; a steel check belongs to no position's calc-block either.
#let steel-domain = "steel"
// The member checks Woodcore saves (calc/domains/member_check.py, data/checks.json), read here since the unfolded checks (spec 2026-10-15, ARCH-007): `#var(key, value, domain: ("check", id))` checks a literal against the `vars` the export publishes for a check printed unfolded; the form it was written from is the regeneration base's alone since the spec 2026-10-21-commandes-typst-refonte (ARCH-011).
#let check-domain = "check"
#let load-checks() = json("../data/checks.json").checks
// Where each domain Woodcore wrote stands against its data, and its file (spec 2026-10-21-commandes-typst-refonte, ARCH-007, ARCH-008): data/domain-state.json and data/domain-files.json, written by the export (calc/domains/unfold.py) and seeded empty in a project that has none.
#let load-domain-state() = json("../data/domain-state.json").domains
#let load-domain-files() = json("../data/domain-files.json").files

/// The file of a calculation domain Woodcore wrote from its data, from the Typst root -- what a section includes it by, `#include domain-file("check", id)`, so that no path to it is ever written by hand (spec 2026-10-21-commandes-typst-refonte, ARCH-008). A domain the export does not list stops the compile, naming the ones it lists.
///
/// ```typ
/// #for id in load-domain-files().at("check", default: (:)).keys() [#id: #raw(domain-file("check", id)) \ ]
/// ```
///
/// ```typ
/// #let ids-of(kind) = load-domain-files().at(kind, default: (:)).keys()
/// #ids-of("check").len()
/// ```
///
/// - kind (str): what wrote it -- `"check"` for a member check unfolded; `"journal"` for a document's journal, written once beside its entry file, its id the document (`"cu"`, `"bp"`, `"rs"`).
/// - id (str): its id.
/// -> str
#let domain-file(kind, id) = {
  let files = load-domain-files().at(kind, default: (:))
  if not (id in files) { panic("domain-file: no domain " + repr(id) + " of kind " + repr(kind) + " in data/domain-files.json -- " + (if files.len() == 0 { "it lists none; export the project" } else { "it lists " + files.keys().join(", ") })) }
  files.at(id)
}
#let load-steel() = json("../data/steel.json")

// The scripts of the project, one instance each of the `script` domain (docs/domain/scripts.md §3.3sexdecies): the values a
// script the engineer wrote declared with `result()`. A file of its own, as a connector's and a connection's are --
// it is exported on its own, and a script belongs to no position.
#let script-domain = "script"
#let load-scripts() = json("../data/scripts.json")

// The loaders of the files every `ids` kind reads, gathered here so that `ids` (below) stands before every call of it (spec 2026-10-19-base-saine-nettoyage, REQ-002).
#let load-plans() = json("../data/plans.json")
#let load-fire-plans() = json("../data/fire.json")
#let load-statics() = json("../data/statics.json")
#let load-schemas() = json("../data/schemas.json")
#let load-annexes() = json("../data/annexes.json")

// The kinds `ids` takes besides a calculation domain's id, in the order its refusal lists them.
#let ids-kinds = ("position", "domain", "connection", "connector", "script", "plan", "fire-plan", "static-model", "schema", "extract", "annex", "check-member", "check-steel")

/// **The ids of every object of one kind the export carries** -- one command for the thirteen `*-ids` of before v0.120 (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, REQ-002). Typst cannot list a folder, which is why `calc/export_all.py` writes the files this reads. A section that called an old name is rewritten when its project is opened (calc/renamed-commands.json).
///
/// ```typ
/// #ids("position")
/// ```
///
/// ```typ
/// #for sheet in ids("snow-load") {
///   include domain-file("snow-load", sheet)
/// }
/// ```
///
/// - kind (str): `"position"`, `"domain"` (the calculation domains), `"connection"`, `"connector"`, `"script"`, `"plan"`, `"fire-plan"`, `"static-model"`, `"schema"`, `"extract"`, `"annex"`, `"check-member"` or `"check-steel"` -- or the id of a calculation domain, one of `ids("domain")` such as `"snow-load"`, whose instances it gives. An unknown kind fails listing the valid ones.
/// -> array
#let ids(kind) = {
  if kind == "position" { return json("../data/positions-index.json").positions }
  if kind == "domain" { return load-calculations().domains.keys() }
  if kind == connection-domain { return load-connections().connections.keys() }
  if kind == connector-domain { return load-connectors().connectors.keys() }
  if kind == script-domain { return load-scripts().scripts.keys() }
  if kind == "plan" { return load-plans().plans.keys() }
  if kind == "fire-plan" { return load-fire-plans().plans.keys() }
  if kind == "static-model" { return load-statics().models.keys() }
  if kind == "schema" { return load-schemas().schemas.keys() }
  if kind == "extract" { return load-annexes().excerpts.keys() }
  if kind == "annex" { return load-annexes().sources.keys() }
  if kind == "check-member" or kind == check-domain { return load-checks().keys() }
  if kind == "check-steel" or kind == steel-domain { return load-steel().checks.keys() }
  let doms = load-calculations().domains
  assert(kind in doms,
    message: "ids: unknown kind " + repr(kind) + " -- " + ids-kinds.join(", ") + ", or a calculation domain: " + doms.keys().join(", "))
  doms.at(kind).instances.keys()
}


// How many `#sync` hold the line being printed: inside one, `resolve-display` leaves the uniform level out (lib/formula.typ).
#let sync-depth = state("woodcore-sync-depth", 0)

/// A value Woodcore keeps in step with its project, in a document written in raw Typst -- a cell of a table, an item of a list, a word of a sentence: it prints its content and nothing else, and Woodcore finds it by its id, reads the content and rewrites it, and nothing around it (spec 2026-10-21-commandes-typst-refonte, REQ-011, calc/typst_sync.py). Taking the tag away, the content kept, ends the keeping: the value is the engineer's from then on.
///
/// ```typ
/// #table(columns: 3,
///   [Nutzlast], [#sync("live-load/A1/category")[A1]], [#sync("live-load/A1/q_k")[#var("q_k", domain: ("live-load", "A1"), display: "value-unit")]],
/// )
/// ```
///
/// What the export holds is best **read** inside it, as the last cell reads it: the value printed is then the export's at every compile and never ages (Q-007). A literal is compared with the export when the project is exported, and a gap is said, never overwritten:
///
/// ```typ
/// Die Nutzlast der Kategorie #sync("live-load/A1/category")[A1] beträgt #sync("live-load/A1/q_k")[3 kN/m²].
/// ```
///
/// - id (str): what Woodcore finds the value by -- `"domain/instance/variable"` for a value of the export, a `/` inside a part written `\/`. Once per file.
/// - body (content): the value as it is printed.
/// -> content
#let sync(id, body) = {
  if type(id) != str or id.trim() == "" { panic("sync: the id is a non-empty string, \"domain/instance/variable\" -- got " + repr(id)) }
  // what it holds is printed as it is written: a `#var` in it keeps the display its call states, `--input uniform=N` included (Q-005, Q-007 -- a cell of a table reads its value live and prints the value alone at every level)
  sync-depth.update(n => n + 1)
  body
  sync-depth.update(n => n - 1)
}


/// **One field of a variable already read** (`find`, a record's `vars`, or one the report declared, by its name) -- one command for the eight `get-*` of before v0.120 (spec 2026-10-19-base-saine-nettoyage, REQ-002). The rest of the engine reads a variable's fields through it, never `.value` or `.unit` directly, so a change of the variable's shape touches this one place (docs/typst/report-engine.md §6).
///
/// ```typ
/// #get((value: 1.394, unit: "kN/m²", symbol: "s_k"), "value")
/// ```
///
/// ```typ
/// #var("q_k", domain: ("live-load", "A1"), level: 0)
/// #context fmt-number(get("q_k", "value") * 0.7, get("q_k", "unit"))
/// ```
///
/// A variable the report declared is named by its name, read in the registry where the call stands -- a state, so in a `context` (spec 2026-10-21-commandes-typst-refonte, REQ-009): a sentence that depends on a result.
///
/// ```typ
/// #var("eta", 0.75, level: 0)
/// #context if get("eta", "value") <= 1 [Die Bemessung ist ausreichend.] else [Die Bemessung genügt nicht.]
/// ```
///
/// - v (dictionary, str): a `var` object (docs/architecture/data-contracts.md §3.1), or the name of a variable the report declared -- in a `context`.
/// - field (str): `"value"`, `"unit"` (never implicit: "" for a dimensionless quantity), `"symbol"`, `"label"`, `"norm"`, `"norm_ref"`, `"description"`, `"choices"` or `"role"`. The description and the choices are optional in a variable and give none where it has none, the role is "data" where none was given; every other field is required, and an unknown one fails naming the valid ones.
/// - domain (str, none): for a name, the domain it is read in; none reads the current domain, then the default one.
/// -> any
#let get(v, field, domain: none) = {
  // a variable named rather than handed over: read in the registry where the call stands -- the domain named, else the current one and the default (spec 2026-10-21-commandes-typst-refonte, REQ-009). A state, so the call stands in a `context`.
  if type(v) == str {
    let d = var-registry.get()
    let found = if domain != none { d.domains.at(domain, default: (:)).at(v, default: none) } else { var-lookup(d, v) }
    if found == none { panic("get: no variable named " + repr(v) + (if domain != none { " in the domain " + repr(domain) } else { " here" }) + " -- declared here: " + var-names(d).join(", ")) }
    v = found
  }
  if field in ("description", "choices") { return v.at(field, default: none) }
  if field == "role" { return v.at("role", default: "data") }
  assert(field in ("value", "unit", "symbol", "label", "norm", "norm_ref"),
    message: "get: unknown field " + repr(field) + " -- value, unit, symbol, label, norm, norm_ref, description, choices, role")
  v.at(field)
}

// Every show-* function reads the same {vars, steps, checks} record, addressed the same way: (domain, instance). An instance is a workbook sheet for a calculation domain, or a position id for a domain carried by a position. Resolved here once so all three functions fail the same actionable way (docs/typst/api-conventions.md §10bis).

// Human-readable name of what a show-* call is reading, for error messages.
#let source-label(domain, instance) = {
  "domain '" + domain + "', instance '" + instance + "'"
}

// The lookup itself, with no scope guard -- so it needs no `context` and can therefore be called from a plain `#let`, which is what makes var-of/value-of usable for arithmetic in the document body.
#let find-calculation(fn-name, domain, instance) = {
  let doms = load-calculations().domains
  if domain in doms {
    // A calculation domain's instance is a workbook sheet, which belongs to no position (docs/domain/loads.md §8), so the calc-block scope guard deliberately does not apply to this branch.
    let insts = doms.at(domain).instances
    assert(instance in insts,
      message: fn-name + ": domain '" + domain + "' has no instance '" + instance + "' -- valid instances: " + insts.keys().join(", "))
    insts.at(instance)
  } else if domain == connection-domain {
    // Before the position branch: a connection's id may look like a position's. A connection belongs to no position either, so no scope guard applies to it.
    let conns = load-connections().connections
    assert(instance in conns,
      message: fn-name + ": no connection '" + instance + "' -- " + (if conns.len() == 0 { "none saved yet (save one in Woodcore's polar moments tab)" } else { "valid connections: " + conns.keys().join(", ") }))
    let record = conns.at(instance)
    // A connection its schema no longer draws whole carries its reason rather than a polar moment of what remained (periodic audit 260916).
    if not record.at("calculated", default: true) {
      panic(fn-name + ": connection '" + instance + "' cannot be printed -- " + record.reason + ", then export again.")
    }
    record
  } else if domain == connector-domain {
    // Before the position branch, as the connection's is: a connector's id may look like a position's, and a connector belongs to no position either, so no calc-block scope guard applies to it.
    let known = load-connectors().connectors
    assert(instance in known,
      message: fn-name + ": no connector '" + instance + "' -- " + (if known.len() == 0 { "none saved yet (create one in Woodcore's connectors tab)" } else { "valid connectors: " + known.keys().join(", ") }))
    let record = known.at(instance)
    // A connector the export could not calculate carries its reason rather than a resistance nobody produced.
    if not record.calculated {
      panic(fn-name + ": connector '" + instance + "' carries no calculation -- " + record.reason + " Open it in Woodcore's connectors tab, put that right and export again.")
    }
    record
  } else if domain == steel-domain {
    // Before the position branch: a steel check's id may look like a position's, and it belongs to no position's calc-block (issues #50-#52).
    let known = load-steel().checks
    assert(instance in known,
      message: fn-name + ": no steel check '" + instance + "' -- " + (if known.len() == 0 { "none saved yet (create one in Woodcore's «Acier» tabs)" } else { "valid steel checks: " + known.keys().join(", ") }))
    let record = known.at(instance)
    if not record.calculable {
      panic(fn-name + ": steel check '" + instance + "' cannot be calculated -- " + record.reason + ". Open it in Woodcore's «Acier» tabs, put that right and export again.")
    }
    record
  } else if domain == check-domain {
    // Before the position branch: a check's id may look like a position's, and a check belongs to no position's calc-block. Only a check printed unfolded publishes `vars` (calc/domains/member_check.py, `published_vars`).
    let known = load-checks()
    assert(instance in known,
      message: fn-name + ": no member check '" + instance + "' -- " + (if known.len() == 0 { "none saved yet (create one in Woodcore's member check tabs)" } else { "valid checks: " + known.keys().join(", ") }))
    let record = known.at(instance)
    if not record.calculable {
      panic(fn-name + ": member check '" + instance + "' cannot be calculated -- " + record.reason + ". Open it in Woodcore, put that right and export again.")
    }
    if not ("vars" in record) {
      panic(fn-name + ": member check '" + instance + "' is not printed unfolded, so it publishes no values -- only a " + record.kind + " check unfolded in Formules/ does")
    }
    record
  } else if domain == script-domain {
    // Before the position branch, as the connection's and the connector's are: a script's id is
    // its file name, which the engineer chose and which may look like a position's -- and a script belongs to no
    // position either, so no calc-block scope guard applies to it.
    let known = load-scripts().scripts
    assert(instance in known,
      message: fn-name + ": no script '" + instance + "' -- " + (if known.len() == 0 { "this project has none yet (write one in Woodcore's Python tab and run it)" } else { "valid scripts: " + known.keys().join(", ") }))
    let record = known.at(instance)
    // A script that failed, was given up on or declared nothing carries its reason rather than a value nobody produced.
    if not record.calculated {
      panic(fn-name + ": the script '" + instance + "' produced no value -- " + record.reason + " Put that right in Woodcore's Python tab, run it again and export.")
    }
    record
  } else if instance in known-position-ids() {
    let pos = load-position(instance)
    // a position with no domain at all is the normal state today, so say that rather than trailing off after "its domains:"
    let domains = pos.at("domains", default: (:))
    let listed = if domains.len() == 0 { "none (it carries no calculation)" } else { domains.keys().join(", ") }
    assert(domain in domains,
      message: fn-name + ": position '" + instance + "' has no domain '" + domain + "' -- its domains: " + listed + "; calculation domains: " + (doms.keys() + (connection-domain, connector-domain, script-domain, steel-domain, check-domain)).join(", "))
    domains.at(domain)
  } else {
    // Neither a calculation domain nor a position: say so with both lists, rather than letting Typst fail on a missing positions/<id>.json.
    panic(
      fn-name + ": '" + domain + "' is not a calculation domain (valid: "
        + (doms.keys() + (connection-domain, connector-domain, script-domain, steel-domain, check-domain)).join(", ") + ") and '" + instance + "' is not a "
        + "position (valid: " + ids("position").join(", ") + ") -- the call "
        + "shape is show-*(domain, instance, ...)",
    )
  }
}

// --- get-* abstraction (docs/typst/report-engine.md §6) ------------------------------
// The rest of this file, and report/*.typ, must go through these instead of reading .value/.unit/... directly, so a future schema change only touches this block.

// The same rule for a sentence the data carries (render-prose, a text cell of a table): a hyphen standing where a number's sign stands -- at the start, or after a space, a bracket, `=`, `:`, `;`, `,` or `/`, and right before a digit -- is a minus. «Δh = -200 m» out of the workbook's Dropdowns sheet prints «−200 m». A hyphen inside a word or between two digits is left alone, so «Holz-Holz», «EL+AL-Dach1» and «EN 1995-1-1» keep theirs.
#let sign-hyphen = regex("(^|[\s(\[=:;,/])-(\d)")
#let prose-minus(s) = if type(s) == str { s.replace(sign-hyphen, m => m.captures.at(0) + minus-sign + m.captures.at(1)) } else { s }

// `type` is a named parameter of `val` (lib/formula.typ), which shadows Typst's builtin `type()` inside its body -- captured here so the body can still ask what it was handed.
#let value-type = type

// A value that is text rather than a number is a word: the load model's name, the terrain category, the Art der Nutzfläche. So it follows the report's language where the glossary carries it -- the norm's own wording does -- and stays exactly as entered where it does not, which is every value read from a workbook (docs/typst/language.md §4bis).
#let value-word(v) = if value-type(v) == str { tl-str(v) } else { v }

// `fmt` stood here until v0.80: one value, from a var object or a bare number, in one of three parts. It is `val` now (lib/formula.typ), which prints the same value whether it is handed over, named in the report's registry or named in the export -- one command for one value, the engineer's own decision (docs/decisions.md §13). `fmt-number` and `fmt-decimals` below are the primitives it and every other display path print through, and they stay.

/// Formats a raw number and unit for display, e.g. "1.902 kN/m²" (bare "0.9" for an empty unit). The counterpart to fmt-value for a value computed in Typst, which has no `var` object to read from.
///
/// ```typ
/// #fmt-number(1.7291232, "kN/m²")
/// ```
///
/// ```typ
/// #fmt-number(0.9, "")
/// ```
///
/// - value (int, float, str): the value to print.
/// - unit (str): its unit, "" for dimensionless.
/// -> content
#let fmt-number(value, unit) = context {
  // the one display rule (lib/number.typ, UI-003); a value that is a word stays exactly as it was entered, through the glossary
  if value-type(value) == int or value-type(value) == float { return display-quantity(value, unit) }
  let s = value-word(value)
  // a no-break space: «Q_k = 20» at the end of a line and «kN» alone on the next was what a plain one allowed (v0.86)
  if unit == "" { s } else { s + unit-gap(unit) + unit }
}

/// Formats a var's value together with its unit for display, e.g. "26.916 kNm", or the bare number for a dimensionless value (empty unit). Decimals follow the document's number-digits setting.
///
/// ```typ
/// #fmt-value((value: 26.916, unit: "kNm"))
/// ```
///
/// ```typ
/// #fmt-value((value: 0.8, unit: ""))
/// ```
///
/// - v (dictionary): a `var` object (section 3.1).
/// -> content
#let fmt-value(v) = fmt-number(get(v, "value"), get(v, "unit"))

// --- Raw data access, for arithmetic done in Typst (docs/project/purpose.md §1) --
// The display functions above all end in content. To *compute* with a value -- a one-off arrangement the data does not carry -- the number itself is needed, in a plain `#let` that the rest of the document can reuse. These deliberately carry no calc-block scope guard (that guards what is printed under a header, not what is read into a variable), which is also what lets them work outside `context`.

// Norm references (docs/typst/citations.md §10): "SIA 261 5.2.6", no §, no comma, no brackets (the engineer, 20.10.2026: «Il ne doit pas y avoir de "§" avant le norm-ref»), in the citation grey (`cite-text`) -- rendered smaller in a dedicated right-hand column so it reads as a margin note level with the equation it cites.
// A document cited as a whole has no clause, and is printed without one -- a connection's design aid (section 3.3quinquies).
// A colon and a semicolon joining the engine's own parts, set the way each language sets them: French keeps a narrow no-break space before them, as `t-label` does for a word of the glossary (periodic audit 260916, AUD-3-12). Strings, so they join math and text alike; read inside a show-* function's context.
#let colon-str() = if report-lang() == "fr" { "\u{202f}:" } else { ":" }
#let semicolon-str() = if report-lang() == "fr" { "\u{202f};" } else { ";" }

// An annex is not a clause: «SIA 261 Anhang D», and «Anhang» is a word, printed in the report's language -- a term of the glossary, so a glossary without it (the frozen examples') prints the German (periodic audit 260916).
#let norm-text(v) = {
  // a script's result that names no norm is cited by its call -- «script beam.py, l. 12» (spec 2026-10-20-indices-et-niveaux, REQ-002): its file is the last part of its source, `python:Scripts/beam.py`
  if v.at("norm", default: "") in ("", none) and v.at("line", default: none) != none {
    let file = str(v.at("source", default: "")).split("/").last()
    return [#context t-str("script.line", file: file, line: str(v.line))]
  }
  let ref = get(v, "norm_ref")
  // a table, likewise (v0.88, the member checks cite Tabellen 4, 8, 9, 47 and 48): «SIA 265 Tabelle 8», as distance-cite prints one
  if ref == "" [#get(v, "norm")] else if ref.starts-with("Anhang ") [#get(v, "norm") #context tl-str("Anhang") #ref.slice("Anhang ".len())] else if ref.starts-with("Tabelle ") [#get(v, "norm") #context tl-str("Tabelle") #ref.slice("Tabelle ".len())] else [#get(v, "norm") #ref]
}

// The citation column's width and its gutter, shared by annotated-rows and by render-table, which centres a table in the space left of it.
#let note-column = 3.8cm
#let note-gutter = 0.6cm

// A formula that wraps onto a second line is two lines of one paragraph, kept apart by its leading -- and a line of inline math is not measured to its ink. A fraction set in display style (`show math.frac: it => $display(it)$` in the report's config.typ) reaches well above and below the line box its text edges give it, so the numerator of a second line ran into the first, and the denominator of the first into the second, whatever the leading: measured at 144 ppi, a 0.65 em leading left 0 to 4 px of white between the two lines, where two rows are 11 to 16 px apart, and doubling the leading bought 3 px on one side (the engineer, v0.87: «lorsqu'un calcul est sur 2 lignes, il n'y a plus assez d'espace entre les deux lignes»). So a row that is **taller than a line of roots and indices** -- measured on one line, what only a built-up fraction reaches -- **and wraps** is set with its lines measured to their ink (`top-edge`/`bottom-edge: "bounds"`), and its leading is then the white actually left between them: `wrapped-row-leading`, a little less than the gap between two rows, so the two lines still read as one formula. Every other row is left exactly as it was: a row that does not wrap, one of text or of small math, and every gap between rows.
#let row-spacing = 1em
#let tall-row-height = 1.2em
#let wrapped-row-leading = 0.5em
#let row-cell(content) = context {
  let line = measure(content).height
  if line <= tall-row-height.to-absolute() { return content }
  layout(size => {
    // one line wide enough for it: nothing to space
    if measure(content, width: size.width).height <= line + 0.5pt { return content }
    // in a block of its own: a paragraph takes its leading and its text edges from where it starts, which is outside this context, so a `set` in here would reach nothing without one
    block(width: 100%, {
      set text(top-edge: "bounds", bottom-edge: "bounds")
      set par(leading: wrapped-row-leading)
      content
    })
  })
}

// The citation of one row, small and right-aligned, level with the middle of its row.
#let note-cell(note-var) = if note-var == none { [] } else {
  align(right + horizon, cite-text(norm-text(note-var)))
}

// The same citation set **on the line** it cites, at the end of it: a box as wide as the citation column, pushed to the right edge. A stacked formula's first line is measured to its ink (chain-cell), and a fraction whose numerator is built higher than its denominator puts the middle of that ink well above the `=`, so a citation centred in its row sat level with the numerator; on the line, it stands on the formula's own baseline.
#let note-on-line(note-var) = h(1fr) + box(width: note-column, align(right, cite-text(norm-text(note-var))))

// --- A formula too wide for its row, stacked at its relation signs -----------
// A calculation printed in letters, in numbers and as its answer stands on one line -- `B_v = <letters> = <numbers> = 116.122 kN` -- and a display fraction is one atom that cannot break (`show math.frac: it => $display(it)$` in the report's config.typ). So a line wider than its row ran into the citation column and off the page (the engineer's exercise: «une longue fraction qui ne peut pas passer à la ligne déborde dans la colonne des références»), and one that could break broke wherever the width ran out, an `=` left dangling at the end of a line. Such a line is now set the classic way, **stacked at its relation signs**: `B_v = <letters>`, then `= <numbers>`, then `= 116.122 kN`, each `=` under the first -- as rows of the same grid, so the citation stays level with the first line. A line that fits is set exactly as it always was: what is measured decides, and nothing else changes.
//
// A row that may be stacked is a `formula-chain`: the one line it has always been (`line`), and what it is stacked into -- its first line (`first`, the left-hand side and the formula in letters), the segments after it (`rest`, math source, the numbers and the answer), the function that sets some of them as one line under the first (`build`, given them joined by ` = `), and what the last line ends on (`last`, a label or a footnote). `annotated-rows` measures the one line against the width the row has -- the column left of the citation, or the full width where the row carries none -- and stacks only where it does not fit.
#let formula-chain(line, first, rest, build, last: x => x) = (chain: true, line: line, first: first, rest: rest, build: build, last: last)
#let is-chain(c) = type(c) == dictionary and c.at("chain", default: false) == true

// A line after the first of a stacked formula: its relation and what follows it, set where the first line's relation stands. The first line's left-hand side is **measured** and an empty box of that width stands in its place inside the same equation, so the space math sets around the `=` is the first line's own and the two signs fall one under the other to the point. `wrap` is what the line is set in -- `math.bold` for an answer -- and `side` what the first line's left-hand side was set in, `wrap` unless said otherwise: a bold B_v is wider than a regular one, and a step set on one row prints its letters regular and its numbers bold. Read inside a context, like everything that measures.
#let chain-line(lhs, rel, seg, scope: (:), wrap: x => x, side: auto) = {
  let side = if side == auto { wrap } else { side }
  let pad = box(width: measure(side(math-eval(lhs, scope: scope))).width)
  wrap(math-eval("#chain-pad " + rel + " " + seg, scope: scope + (chain-pad: pad)))
}

// The white between two lines of one stacked formula, measured to their ink: less than the gap between two rows, so the lines read as one formula, and measured to the ink because a display fraction reaches well past the line box its text edges give it (row-cell's own finding, v0.87). Only the edges **between** the lines are the ink's: the top of the first line and the foot of the last keep the text's own, so the formula stands as far from the rows around it as a line that fits does.
#let chain-leading = wrapped-row-leading
#let chain-cell(content, top: "bounds", bottom: "bounds") = block(width: 100%, {
  set text(top-edge: top) if top != auto
  set text(bottom-edge: bottom) if bottom != auto
  content
})

// The lines a `formula-chain` is stacked into: `column` wide -- the column left of the citation -- on the line the citation stands beside, where the row carries one (`noted`), and `wide` on every other. The first line is the left-hand side and the formula in letters, on its own; the segments after it are packed onto the lines under it **as many as fit** -- `= <numbers> = <answer>` on one line where the width holds both, which is where a checker reads the one against the other, and a line of its own each where it does not. The classic stacked form costs no more lines than the breaks it replaces. The citation stays beside the first line, unless that line alone is wider than the column left of it: it then moves down to the next, which is packed to the column, rather than be run over. Returns the lines and the index of the one carrying the citation (`none` for a row carrying none).
#let chain-lines(chain, fits, column, wide, noted) = {
  let lines = (chain.first,)
  let cited = if not noted { none } else if fits(chain.first, column) { 0 } else { 1 }
  let current = none
  for (k, s) in chain.rest.enumerate() {
    let candidate = if current == none { s } else { current + " = " + s }
    let room = if cited == lines.len() { column } else { wide }
    // measured as it would be set: the last segment carries what the line ends on
    let shaped(src) = if k == chain.rest.len() - 1 { (chain.last)((chain.build)(src)) } else { (chain.build)(src) }
    if current != none and not fits(shaped(candidate), room) {
      lines.push((chain.build)(current))
      current = s
    } else {
      current = candidate
    }
  }
  if current != none { lines.push((chain.last)((chain.build)(current))) }
  (lines, if cited != none { calc.min(cited, lines.len() - 1) } else { none })
}

// The rows of `annotated-rows` where one of them is a `formula-chain`: laid out once the width is known. A chain whose one line fits the width its row has is set as it always was -- beside its citation, or, carrying none, spanning the citation column where only the full width holds it. One that does not fit is stacked (chain-lines): its lines take a row each, the citation beside the first, and every other line spans both columns, having no citation to leave room for.
//
// ⚠️ A single segment wider than even the full width is left as Typst sets it -- an inline equation breaks at its own relations and operators, never inside a fraction -- and may still run past the text. Setting such a fraction in inline style instead would overrule the engineer's own `show math.frac` rule of config.typ, which is his to make.
#let chain-rows(rows) = layout(size => {
  let has-notes = rows.any(pair => pair.at(1) != none)
  let column = if has-notes { size.width - note-column - note-gutter } else { size.width }
  let fits(c, room) = measure(c).width <= room + 0.01pt
  // each laid out as (content, note, spanning both columns, set close to the next line of the same formula)
  let cells = ()
  for (content, note) in rows {
    if not is-chain(content) { cells.push((content, note, false, false)); continue }
    let room = if note != none { column } else { size.width }
    if fits(content.line, room) {
      cells.push((content.line, note, note == none and not fits(content.line, column), false))
      continue
    }
    let (lines, cited) = chain-lines(content, fits, column, size.width, note != none)
    for (i, l) in lines.enumerate() {
      // ink between the lines, the text's own edges above the first and below the last (chain-cell)
      let top = if i == 0 { auto } else { "bounds" }
      let bottom = if i == lines.len() - 1 { auto } else { "bounds" }
      // every line spans both columns, and the one the citation belongs to carries it at its end, on its own baseline (note-on-line)
      let line = if i == cited { l + note-on-line(note) } else { l }
      cells.push((chain-cell(line, top: top, bottom: bottom), none, has-notes, i < lines.len() - 1))
    }
  }
  let gutters = cells.slice(0, calc.max(cells.len() - 1, 0)).map(c => if c.at(3) { chain-leading } else { row-spacing })
  let gutter = if gutters.len() == 0 { row-spacing } else { gutters }
  if not has-notes {
    return grid(columns: (1fr,), row-gutter: gutter, ..cells.map(c => row-cell(c.at(0))))
  }
  grid(
    columns: (1fr, note-column),
    column-gutter: note-gutter,
    row-gutter: gutter,
    ..cells.map(c => if c.at(2) { (grid.cell(colspan: 2, row-cell(c.at(0))),) } else { (row-cell(c.at(0)), note-cell(c.at(1))) }).flatten()
  )
})

// One or more (content, norm-var-or-none) rows, laid out as a two-column grid: content on the left, the norm note (small, right-aligned) on the right. A single grid -- rather than one place() per row -- keeps every row's note reliably level with its own equation instead of drifting onto the next line.
// ⚠️ Where **no** row carries a note, the citation column is not laid out at all. The column is a fixed 3.8 cm, and with its gutter it takes 4.4 cm whatever it is put inside: in a `grid` cell at half the text width -- the two load cases of `Sections/005` sit side by side like that -- it swallowed more than half of the 7.4 cm available and the text wrapped after three centimetres, with an empty column beside it (v0.61.2). Reserving room for a note that does not exist is the whole of that bug. Rows that *do* carry one keep the fixed column, so cited lines go on lining up down the page.
// A row whose content is a `formula-chain` is laid out by chain-rows, which needs the width; every other set of rows is laid out here exactly as before.
#let annotated-rows(rows) = {
  if rows.any(pair => is-chain(pair.at(0))) { return chain-rows(rows) }
  let notes = rows.map(pair => pair.at(1))
  if notes.all(n => n == none) {
    return grid(columns: (1fr,), row-gutter: row-spacing, ..rows.map(pair => row-cell(pair.at(0))))
  }
  grid(
    columns: (1fr, note-column),
    column-gutter: note-gutter,
    row-gutter: row-spacing,
    ..rows
      .map(pair => (row-cell(pair.at(0)), note-cell(pair.at(1))))
      .flatten()
  )
}

// Symbol/formula strings in data/ are authored as Typst math source (e.g. "C_e", "gamma_M", "f_(m,k)") so they render with real subscripts and Greek glyphs instead of literal underscores -- never print get("symbol") or a formula string as plain text.

// A symbol that is nothing but a quoted word is a word, not a symbol: the load model, the terrain category, the category of Nutzfläche -- a var whose value is text has no letter to stand for it, so its own name is set in its place. Those follow the report's language like every other word; q_k, C_e and mu do not, being the norm's own letters in every language.
//
// ⚠️ The `///` block below must stay **flush against the `#let`**: a plain `//` line between the two detaches it, and the editor then shows no tooltip at all -- which is what this very comment was doing until v0.63.1.
/// Evaluates a var's `symbol` field as Typst math source and returns real rendered math (a real subscript / Greek glyph), not a string (section 6bis).
///
/// ```typ
/// #render-symbol((symbol: "q_(k,1)"))
/// ```
///
/// ```typ
/// #for s in ("h_\"ref\"", "C_e", "s_k") [ #render-symbol((symbol: s)) #h(1em) ]
/// ```
///
/// - v (dictionary): a `var` object (section 3.1) whose `symbol` field is valid Typst math source.
/// -> content
#let render-symbol(v) = {
  let src = get(v, "symbol")
  let word = src.match(regex("^\"([^\"]+)\"$"))
  // A symbol that is a word («Lastmodell») follows the report's language, which is a state: read inside a context of its own, so the call works in plain markup as var-of's own example writes it -- it failed there with «can only be used when context is known» (v0.86).
  if word != none {
    return context math-eval("\"" + tl-str(word.captures.first()) + "\"")
  }
  math-eval(src)
}

/// Evaluates a step's `formula` field as Typst math source and returns real rendered math (section 6bis).
///
/// ```typ
/// #render-formula((formula: "q_(k,11) = max(mu_11, 0.8) dot C_e dot C_T dot s_k"))
/// ```
///
/// ```typ
/// #render-formula((formula: "sigma_m = M_\"Ed\" / W"))
/// ```
///
/// - step (dictionary): a `step` object from a domain's `steps[]` (section 3.1) that carries a `formula` field.
/// -> content
#let render-formula(step) = math-eval(step.formula)

/// One sentence the data carries — a table's note, a var's or a step's description, a choice — with the symbols in it set as real math (section 6bis). A symbol inside a sentence is written between dollars, as it would be in a formula: `$c_"red"$ ist der Reduktionsfaktor` prints c with the subscript red where `cred` printed three letters.
///
/// ```typ
/// #render-prose("$c_\"red\"$ ist der Reduktionsfaktor der Bezugsfläche.")
/// ```
///
/// ```typ
/// #var("ce", domain: ("snow-load", "SL"), level: 0)
/// #context render-prose(tl-str(get("ce", "description")))
/// ```
///
/// The sentence is split on the dollars — the even parts are words, the odd parts math source — so nothing *else* it may carry is interpreted: an underscore stays an underscore, a `#` a hash, a `*` a star, which is what makes this safe on a description typed into Excel. An unpaired dollar leaves the sentence exactly as it came, and so does anything that is not a string (a note a show-* function built as content). One thing only is changed in the words: a hyphen standing for a number's sign, as in «Δh = -200 m», is printed as a minus sign.
/// - sentence (str, content, none): the sentence to set.
/// -> content
#let render-prose(sentence) = {
  if type(sentence) != str { return sentence }
  let parts = sentence.split("$")
  // an even number of parts means an odd number of dollars: one of them opens math that nothing closes, so the sentence is left as written rather than half-evaluated -- all but a number's sign, which is a minus in words as it is in math (prose-minus)
  if calc.even(parts.len()) { return [#prose-minus(sentence)] }
  parts
    .enumerate()
    .map(((i, part)) => if calc.even(i) { [#prose-minus(part)] } else { math-eval(part) })
    .join()
}

// --- Position summary line (docs/domain/positions.md §7-8) -----------------------
// Positions carry no shared section catalog and no load assignment -- just their own type, material, section and description, read directly off data/positions/<id>.json (there is no "var" object to go through get-* for these plain descriptive fields, unlike vars/steps/checks above). `#member` prints this line at level 1 and calc-block heads a block with it; `show-position`, which printed it on its own until v0.94, is gone, `#member` taking any position (lib/timber.typ).

// --- Connector summary display (docs/domain/connectors.md §7bis) -------------------
// A connector is a descriptive record like a position, read directly off data/connectors.json: what the connector's source says about it, and nothing it leaves empty.
