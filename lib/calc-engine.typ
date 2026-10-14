// Display layer for the calc/ -> data/ pipeline (docs/typst/report-engine.md §4-10). Typst never computes anything here -- it only reads and formats what calc/export_all.py already validated and wrote to data/.

// Every word this file prints comes out of one glossary, in the report's language (docs/typst/language.md §4bis). `t-str` is the engine's own word by a key, `tl-str` a string the data carries -- translated if the glossary knows it, left alone if not, which is what keeps a material's name and an Excel description in the engineer's own words. Imported here rather than in each section, so commands.typ re-exports it with the rest.
#import "i18n.typ": *

// --- Report level (docs/typst/report-engine.md §4) -----------------------------------
/// The report's default level of detail, 1, 2 or 3 (section 3.7). Set once in `Statischer Rapport.typ` — `#report-level.update(2)` — from `--input level=`; any `show-*` call overrides it locally with `level:`.
///
/// ```typ
/// #report-level.update(3)
/// #show-calc("snow-load", "SL")
/// ```
///
/// ```typ
/// #report-level.update(1)
/// #show-calc("snow-load", "SL")
/// ```
///
/// -> state
#let report-level = state("report-level", 1)

/// The level forced on **every** call, or `none` (section 4). Set only for the uniform variants in `out/`, from `--input uniform=1|2|3`: while it holds a level, every `show-*` renders at exactly that one and the per-call `level:` overrides written in `Sections/` are ignored — which is the only way to get a PDF that really is one level throughout, an override being a literal argument no outside state could otherwise disarm. `none`, the normal case, honours them.
///
/// ```typ
/// #uniform-level.update(1)
/// #show-calc("snow-load", "SL", level: 3)
/// ```
///
/// ```typ
/// #uniform-level.update(none)
/// #show-input("snow-load", "SL", "ce", level: 3)
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

// --- The level of detail -1: the variables a call names, each at its own level (issue #20, v0.117; docs/typst/report-engine.md §4) ----
// `level: -1, shown: (A: 2, W_y: 1)` prints the variables `shown:` names, each at the level it gives it, and none of the others; the title is printed as at level 1, a check's verdict at the level `shown:` gives its utilisation's key (`eta`, `eta_s`… -- issue #58), a heading printed from level 2 only where one of its keys is chosen, a figure where a key is chosen at 2 or 3 (spec 2026-10-10-issues-github-19-20-21, D-09, D-12, D-14). Like 0 it is a level of one call and never of a report: `resolve-level` hands it back as it stands, and a uniform level is still forced over it. Which keys a command may name is lib/shown-variables.json's, read here and by calc/shown_variables.py for the switches the window offers -- show-calc's are the export's own. One place decides the level a line prints at (`plan-at`), for every command that takes `shown:` -- the -1 below is the only one in lib/.
#let selection-level = -1
#let shown-variables = json("shown-variables.json").commands

// The keys lib/shown-variables.json lets `command` name, in the order it prints them.
#let shown-keys(command) = shown-variables.at(command).keys
// {heading: keys}: the headings `command` prints from level 2 only, and the keys under each.
#let shown-parts(command) = shown-variables.at(command).parts
// A call's `level:` and `shown:` checked together, on what the call wrote -- a uniform level forced over it does not let a mistake through: the level one of `levels` or -1, `shown:` given with -1 only, a dictionary whose every key is one of `keys` and every level 1, 2 or 3 -- a check's verdict included, which is left out like any key (issue #58).
#let check-shown(fn, level, shown, keys, levels: (auto, 0, 1, 2, 3)) = {
  if not (level in levels or level == selection-level) {
    panic(fn + ": invalid level " + repr(level) + " -- use " + levels.map(repr).join(", ") + ", or -1 with shown:")
  }
  if shown == none { return }
  if level != selection-level { panic(fn + ": shown: names what level: -1 prints -- give level: -1, or leave shown: out") }
  if type(shown) != dictionary { panic(fn + ": shown: is a dictionary of variables and their levels, (A: 2, W_y: 1) -- got " + repr(shown)) }
  for (key, n) in shown {
    if not (key in keys) { panic(fn + ": shown: names " + repr(key) + ", which " + fn + " does not print -- it prints: " + keys.join(", ")) }
    if not (n in (1, 2, 3)) { panic(fn + ": shown: gives " + key + " the level " + repr(n) + " -- 1, 2 or 3; a variable not printed is left out") }
  }
}

// What a call prints, line by line: (lv, picked, shown, parts). `lv` is the level the call resolves to -- 1 at -1, which is the level its title prints at --, `picked` whether the variables are chosen one by one. At -1 a check's verdict is a key like any other: printed where `shown:` names it, at its level (issue #58). Call inside `context`, as resolve-level.
#let level-plan(level, shown, parts: (:)) = {
  let lv = resolve-level(level)
  if lv == selection-level {
    (lv: 1, picked: true, shown: if shown == none { (:) } else { shown }, parts: parts)
  } else {
    (lv: lv, picked: false, shown: (:), parts: parts)
  }
}

// The level the line of `key` prints at: at -1 the level `shown:` gives it, 0 where it names it not; otherwise nothing below `from`, the call's own level from there on.
#let plan-at(plan, key, from) = if plan.picked { plan.shown.at(key, default: 0) } else if plan.lv >= from { plan.lv } else { 0 }
// The level of a `var-line` holding `keys`: at -1 `auto`, each item at its own, where one of them is chosen, and 0 where none is -- an empty row would still take its line.
#let plan-row(plan, keys, from) = if plan.picked { if keys.any(k => plan.shown.at(k, default: 0) >= 1) { auto } else { 0 } } else if plan.lv >= from { plan.lv } else { 0 }
// Whether the heading `name`, printed from level `from`, is printed: at -1 where one of its keys is chosen.
#let plan-part(plan, name, from) = if plan.picked { plan.parts.at(name, default: ()).any(k => plan.shown.at(k, default: 0) >= 1) } else { plan.lv >= from }
// Whether what is printed from level `from` and belongs to no key -- a figure -- is printed: at -1 where a key is chosen at `from` or above.
#let plan-any(plan, from) = if plan.picked { plan.shown.values().any(n => n >= from) } else { plan.lv >= from }

// --- Number formatting (document-wide) ------------------------------------
/// How many decimals every number printed by this engine carries, at most — trailing zeros are dropped. Set once in `Statischer Rapport.typ`: `#number-digits.update(3)`.
///
/// ```typ
/// #number-digits.update(1)
/// #val("s_k", domain: ("snow-load", "SL"))
/// ```
///
/// ```typ
/// #number-digits.update(5)
/// #val("s_k", domain: ("snow-load", "SL"))
/// ```
///
/// Every display path goes through `fmt-decimals`, so a change here reaches `show-calc`, `show-input`, `val`, the layer tables and the checks at once — and an equation written by hand in math mode too, as long as it prints its numbers with `val`.
/// -> state
#let number-digits = state("number-digits", 3)

// Stack of the position-id arrays declared by the enclosing calc-block(s) (docs/typst/report-engine.md §5). A stack rather than a single value so blocks can nest; empty means "not inside any block", which disables the scope guard below instead of failing. State is document-order, not lexical: calc-block pushes before rendering its body and pops after.
#let block-scope = state("calc-block-scope", ())

// The position ids the innermost enclosing calc-block declares, or none when the call site is outside every block. Requires `context`.
#let current-scope() = {
  let stack = block-scope.get()
  if stack.len() == 0 { none } else { stack.last() }
}

// Guards against a calculation drifting into the wrong position's block -- a silently wrong report otherwise, since nothing else ties a show-* call's position argument to the block it is printed under.
#let assert-in-scope(fn-name, position) = {
  let scope = current-scope()
  if scope != none and position not in scope {
    panic(
      fn-name + ": position '" + position + "' is not declared by the "
        + "enclosing calc-block (declares: " + scope.join(", ") + ") -- add "
        + "it to that block's positions, or move this call out of the block",
    )
  }
}

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

/// Every position id, in Positions-sheet order (section 7). Data access, not a display function: `for id in position-ids() { member(id, level: 1) }` is what lets `Sections/003-baustoffe.typ` list every element without naming one.
///
/// ```typ
/// #position-ids()
/// ```
///
/// ```typ
/// #for id in position-ids() {
///   member(id, level: 1)
/// }
/// ```
///
/// Typst cannot enumerate a directory, which is why `calc/export_all.py` writes the index file this reads.
/// -> array
#let position-ids() = json("../data/positions-index.json").positions

// The positions deleted with their values kept («Copier les valeurs», issue #9, calc/renumbering.py): «S110-old», which a call may still name and no list of the project's positions shows. A project exported before has none.
#let archived-position-ids() = json("../data/positions-index.json").at("archived", default: ())
// Every id a call may name: the project's positions, and the old ones whose values were kept.
#let known-position-ids() = position-ids() + archived-position-ids()

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

/// Every connection saved in Woodcore, in file-name order (docs/domain/connections.md §3.3quinquies). Data access, not a display function: `for c in connection-ids() { show-polar-moment(c, ...) }`.
///
/// ```typ
/// #connection-ids()
/// ```
///
/// ```typ
/// #for id in connection-ids() [ #id \ ]
/// ```
///
/// -> array
#let connection-ids() = load-connections().connections.keys()

// The connectors of connectors/<id>.json, written by Woodcore (docs/domain/connectors.md §3.3nonies), in file-name order: descriptive records with their own shear-resistance calculation.
#let connector-domain = "connector"
#let load-connectors() = json("../data/connectors.json")

/// Every connector saved in Woodcore, in file-name order (docs/domain/connectors.md §3.3nonies). Data access, not a display function: `for id in connector-ids() { show-connector(id) }`.
///
/// ```typ
/// #connector-ids()
/// ```
///
/// ```typ
/// #for id in connector-ids() {
///   show-connector(id)
///   parbreak()
/// }
/// ```
///
/// -> array
#let connector-ids() = load-connectors().connectors.keys()

// The steel checks of Woodcore's «Acier» tabs (issues #50-#52, docs/domain/steel.md): computed by the export, once (calc/domains/steel_check.py), each a {vars, steps, tables} record show-calc prints as it is -- `#show-check-steel` (lib/steel.typ) heads it and prints its verdict. A file of its own, as a connector's is; a steel check belongs to no position's calc-block either.
#let steel-domain = "steel"
#let load-steel() = json("../data/steel.json")

// The scripts of the project, one instance each of the `script` domain (docs/domain/scripts.md §3.3sexdecies): the values a
// script the engineer wrote declared with `result()`. A file of its own, as a connector's and a connection's are --
// it is exported on its own, and a script belongs to no position.
#let script-domain = "script"
#let load-scripts() = json("../data/scripts.json")

/// Every script of the project, in file-name order (docs/domain/scripts.md §3.3sexdecies). Data access, not a display function: what a script produced is printed with `val` or `show-calc`, addressed `("script", "<id>")`.
///
/// ```typ
/// #script-ids()
/// ```
///
/// ```typ
/// #for id in script-ids() [ #id \ ]
/// ```
/// -> array
#let script-ids() = load-scripts().scripts.keys()

/// Every calculation domain of data/calculations.json, in its order -- the sheet domains, then the norm tables: ("dead-load", "snow-load", "wind-load", "live-load"). Connections and connectors are addressed as domains too but are not listed here. Data access, not a display function.
///
/// ```typ
/// #domain-ids()
/// ```
///
/// ```typ
/// #for d in domain-ids() [ #d: #instance-ids(d).len() Fälle \ ]
/// ```
///
/// -> array
#let domain-ids() = load-calculations().domains.keys()

/// Every instance of one calculation domain -- the workbook sheets it was read from, the load workbooks in file-name order and each one's sheets in tab order (docs/domain/calculation-domains.md §3.3). Lets a section show every case of a load without naming them: `for s in instance-ids("snow-load") { show-calc("snow-load", s) }`, so copying a sheet in Excel is all it takes to add one. `instance-ids("connection")` is every connection, as connection-ids() gives them.
///
/// ```typ
/// #instance-ids("snow-load")
/// ```
///
/// ```typ
/// #for sheet in instance-ids("snow-load") {
///   show-calc("snow-load", sheet)
/// }
/// ```
///
/// - domain (str): a domain id from domain-ids(), e.g. "snow-load", or "connection".
/// -> array
#let instance-ids(domain) = {
  if domain == connection-domain { return connection-ids() }
  if domain == connector-domain { return connector-ids() }
  if domain == script-domain { return script-ids() }
  if domain == steel-domain { return load-steel().checks.keys() }
  let doms = load-calculations().domains
  assert(domain in doms,
    message: "instance-ids: unknown domain '" + domain + "' -- valid domains: " + (doms.keys() + (connection-domain, connector-domain, script-domain)).join(", "))
  doms.at(domain).instances.keys()
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
      message: fn-name + ": position '" + instance + "' has no domain '" + domain + "' -- its domains: " + listed + "; calculation domains: " + (doms.keys() + (connection-domain, connector-domain, script-domain)).join(", "))
    domains.at(domain)
  } else {
    // Neither a calculation domain nor a position: say so with both lists, rather than letting Typst fail on a missing positions/<id>.json.
    panic(
      fn-name + ": '" + domain + "' is not a calculation domain (valid: "
        + (doms.keys() + (connection-domain, connector-domain)).join(", ") + ") and '" + instance + "' is not a "
        + "position (valid: " + position-ids().join(", ") + ") -- the call "
        + "shape is show-*(domain, instance, ...)",
    )
  }
}

// What every *display* function uses: the same lookup, plus the calc-block scope guard. The guard is a presentation concern -- it catches a calculation printed under the wrong position's header -- so it applies here and not in find-calculation. Requires `context`.
#let resolve-source(fn-name, domain, instance) = {
  if domain not in load-calculations().domains and domain != connection-domain and domain != connector-domain and domain != script-domain and domain != steel-domain and instance in known-position-ids() {
    assert-in-scope(fn-name, instance)
  }
  find-calculation(fn-name, domain, instance)
}

// --- get-* abstraction (docs/typst/report-engine.md §6) ------------------------------
// The rest of this file, and report/*.typ, must go through these instead of reading .value/.unit/... directly, so a future schema change only touches this block.

/// Reads the numeric value of an already-resolved var object.
///
/// ```typ
/// #get-value(var-of("snow-load", "SL", "s_k"))
/// ```
///
/// ```typ
/// #let q = var-of("live-load", "A1", "q_k")
/// #fmt-number(get-value(q) * 0.7, get-unit(q))
/// ```
///
/// - v (dictionary): a `var` object from a position/load JSON file's `vars` (docs/architecture/data-contracts.md §3.1), e.g. `dom-data.vars.at("M_Ed")`.
/// -> int | float | str
#let get-value(v) = v.value

/// Reads the unit string of an already-resolved var object (never implicit -- an empty string "" for dimensionless quantities).
///
/// ```typ
/// #get-unit(var-of("snow-load", "SL", "s_k"))
/// ```
///
/// ```typ
/// Dimensionslos, also leer: #repr(get-unit(var-of("snow-load", "SL", "ce")))
/// ```
///
/// - v (dictionary): a `var` object (section 3.1).
/// -> str
#let get-unit(v) = v.unit

/// Reads the raw Typst-math-source symbol string of a var object. Use render-symbol to get real rendered math instead of the raw string.
///
/// ```typ
/// #get-symbol(var-of("snow-load", "SL", "q_k11"))
/// ```
///
/// ```typ
/// #eval(get-symbol(var-of("snow-load", "SL", "h_ref")), mode: "math")
/// ```
///
/// - v (dictionary): a `var` object (section 3.1).
/// -> str
#let get-symbol(v) = v.symbol

/// Reads the human-readable label of a var object.
///
/// ```typ
/// #get-label(var-of("snow-load", "SL", "s_k"))
/// ```
///
/// ```typ
/// #for n in ("h_ref", "s_k", "q_k11") [ #n -- #get-label(var-of("snow-load", "SL", n)) \ ]
/// ```
///
/// - v (dictionary): a `var` object (section 3.1).
/// -> str
#let get-label(v) = v.label

/// Reads the norm name a var/step/check cites (e.g. "SIA 265").
///
/// ```typ
/// #get-norm(var-of("snow-load", "SL", "s_k"))
/// ```
///
/// ```typ
/// #let v = var-of("snow-load", "SL", "ce")
/// Nach #get-norm(v) §#get-norm-ref(v).
/// ```
///
/// - v (dictionary): a var, step, or check object carrying `norm` (section 3.1/3.4/10).
/// -> str | none
#let get-norm(v) = v.norm

/// Reads the norm clause a var/step/check cites (e.g. "4.2.1").
///
/// ```typ
/// #get-norm-ref(var-of("snow-load", "SL", "s_k"))
/// ```
///
/// ```typ
/// #get-norm-ref(var-of("live-load", "A1", "q_k"))
/// ```
///
/// - v (dictionary): a var, step, or check object carrying `norm_ref` (section 3.1/3.4/10).
/// -> str
#let get-norm-ref(v) = v.norm_ref

/// Reads the optional prose description of a var object, if any.
///
/// ```typ
/// #get-description(var-of("snow-load", "SL", "ce"))
/// ```
///
/// ```typ
/// #let d = get-description(var-of("snow-load", "SL", "s_k"))
/// #if d == none [Diese Variable trägt keine Beschreibung.] else [#d]
/// ```
///
/// - v (dictionary): a `var` object (section 3.1). Gives none where the field is absent.
/// -> str | none
#let get-description(v) = v.at("description", default: none)

/// Reads the optional discrete-choices list of a var object, if any (e.g. Ce in {1.0: "exposed", 1.5: "sheltered"}, section 3.3).
///
/// ```typ
/// #get-choices(var-of("snow-load", "SL", "ce"))
/// ```
///
/// ```typ
/// #for c in get-choices(var-of("snow-load", "SL", "ce")) [ #c.value -- #c.desc \ ]
/// ```
///
/// - v (dictionary): a `var` object (section 3.1). Each entry of what it gives is (value: ..., desc: ...); none where the field is absent.
/// -> array | none
#let get-choices(v) = v.at("choices", default: none)

/// Formats a number with *at most* `digits` decimals, dropping trailing zeros: 1.7291232 -> "1.729", 0.800 -> "0.8", 438 -> "438".
///
/// ```typ
/// #fmt-decimals(1.7291232, 3)
/// ```
///
/// ```typ
/// #fmt-decimals(0.800, 3) -- #fmt-decimals(438, 3)
/// ```
///
/// Not `calc.round` + `str`, which is the obvious route and the wrong one: it leaves float artefacts (a value that rounds to 1.084 can print as 1.0840000000000001). The digits are built here from an integer instead, so what is printed is exactly what was rounded, then the tail is trimmed. A string (a load model name, a material) comes back unchanged; anything else that is not a number is refused.
/// - x (int, float, str): the value to format.
/// - digits (int): the maximum number of decimals to show.
/// -> str
#let fmt-decimals(x, digits) = {
  // a var's value may legitimately be text (a load model name), so strings pass through; anything else is a mistake at the call site -- most often math content, from calling this inside $...$ without the leading #
  if type(x) == str { return x }
  assert(type(x) == int or type(x) == float,
    message: "fmt-decimals: expected a number or a string, got " + str(type(x))
      + " -- inside math mode, escape back to code with #, as in "
      + "$ x = #val(get-value(v)) $")
  let scaled = int(calc.round(calc.abs(x) * calc.pow(10, digits)))
  let s = str(scaled)
  // left-pad so a value below 1 still has an integer digit ("0.005")
  while s.len() <= digits { s = "0" + s }
  let cut = s.len() - digits
  // a whole number keeps no decimal point at all
  let frac = s.slice(cut).trim("0", at: end)
  let out = if frac == "" { s.slice(0, cut) } else { s.slice(0, cut) + "." + frac }
  // a value that rounds to zero must not come out as "-0"
  if x < 0 and scaled != 0 { "-" + out } else { out }
}

// The sign a negative number is *printed* with: U+2212 «−», the minus sign, and never the hyphen «-» the keyboard types (the engineer, v0.87: «un signe moins doit être affiché»). `fmt-decimals` above keeps the hyphen on purpose -- what it returns is also Typst math source, which sets a minus of its own for an unquoted `-0.25`, and SVG coordinates, which a parser reads back -- so the sign is changed here, at the point a number becomes text on the page, and nowhere upstream of it.
#let minus-sign = "\u{2212}"
#let signed-text(s) = if type(s) == str and s.starts-with("-") { minus-sign + s.slice(1) } else { s }

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
  let s = fmt-decimals(value-word(value), number-digits.get())
  // a number's sign is printed as a minus (signed-text); a value that is a word stays exactly as it was entered
  if value-type(value) == int or value-type(value) == float { s = signed-text(s) }
  // a no-break space: «Q_k = 20» at the end of a line and «kN» alone on the next was what a plain one allowed (v0.86)
  if unit == "" { s } else { s + "\u{a0}" + unit }
}

/// Formats a var's value together with its unit for display, e.g. "26.916 kNm", or the bare number for a dimensionless value (empty unit). Decimals follow the document's number-digits setting.
///
/// ```typ
/// #fmt-value(var-of("snow-load", "SL", "s_k"))
/// ```
///
/// ```typ
/// #fmt-value(var-of("snow-load", "SL", "ce"))
/// ```
///
/// - v (dictionary): a `var` object (section 3.1).
/// -> content
#let fmt-value(v) = fmt-number(get-value(v), get-unit(v))

// --- Raw data access, for arithmetic done in Typst (docs/project/purpose.md §1) --
// The display functions above all end in content. To *compute* with a value -- a one-off arrangement the data does not carry -- the number itself is needed, in a plain `#let` that the rest of the document can reuse. These deliberately carry no calc-block scope guard (that guards what is printed under a header, not what is read into a variable), which is also what lets them work outside `context`.

/// Reads one whole `var` object out of the data, for use in Typst-side arithmetic and in hand-written equations. To *print* one, `val` reads the same variable by name: `val("s_k", domain: ("snow-load", "SL"))`.
///
/// ```typ
/// #let s-k = var-of("snow-load", "SL", "s_k")
/// #val(s-k)
/// ```
///
/// ```typ
/// #let q = var-of("snow-load", "SL", "q_k11")
/// Symbol #render-symbol(q), Wert #val(q), Norm #get-norm(q) §#get-norm-ref(q).
/// ```
///
/// - domain (str): a calculation domain, or a domain of a position.
/// - instance (str): the workbook sheet, or a position id.
/// - name (str): var name within that instance's `vars`. An unknown name raises an assertion error listing the valid var names. The `var` object returned (section 3.1) is read with get-value, get-unit, …, never directly.
/// -> dictionary
#let var-of(domain, instance, name) = {
  let vars = find-calculation("var-of", domain, instance).vars
  assert(name in vars,
    message: "var-of: unknown var '" + name + "' in " + source-label(domain, instance) + " -- valid vars: " + vars.keys().join(", "))
  vars.at(name)
}

/// The bare number of one variable, for arithmetic: shorthand for `get-value(var-of(...))`. Use var-of instead when the same variable is also going to be displayed, so it is looked up once.
///
/// ```typ
/// #let s = value-of("snow-load", "SL", "s_k")
/// #fmt-number(s * 0.65, "kN/m²")
/// ```
///
/// ```typ
/// #fmt-number(value-of("live-load", "A1", "q_k") * 1.5, "kN/m²")
/// ```
///
/// - domain (str): a calculation domain, or a domain of a position.
/// - instance (str): the workbook sheet, or a position id.
/// - name (str): var name within that instance's `vars`.
/// -> int | float | str
#let value-of(domain, instance, name) = get-value(var-of(domain, instance, name))

// Norm references (docs/typst/citations.md §10): "SIA 261 §5.2.6", no comma, no brackets -- rendered smaller in a dedicated right-hand column so it reads as a margin note level with the equation it cites.
// A document cited as a whole has no clause, and is printed without one -- a connection's design aid (section 3.3quinquies).
// A colon and a semicolon joining the engine's own parts, set the way each language sets them: French keeps a narrow no-break space before them, as `t-label` does for a word of the glossary (periodic audit 260916, AUD-3-12). Strings, so they join math and text alike; read inside a show-* function's context.
#let colon-str() = if report-lang() == "fr" { "\u{202f}:" } else { ":" }
#let semicolon-str() = if report-lang() == "fr" { "\u{202f};" } else { ";" }

// An annex is not a clause: «SIA 261 Anhang D» takes no §, and «Anhang» is a word, printed in the report's language -- a term of the glossary, so a glossary without it (the frozen examples') prints the German (periodic audit 260916).
#let norm-text(v) = {
  let ref = get-norm-ref(v)
  // a table, likewise (v0.88, the member checks cite Tabellen 4, 8, 9, 47 and 48): «SIA 265 Tabelle 8», as distance-cite prints one
  if ref == "" [#get-norm(v)] else if ref.starts-with("Anhang ") [#get-norm(v) #context tl-str("Anhang") #ref.slice("Anhang ".len())] else if ref.starts-with("Tabelle ") [#get-norm(v) #context tl-str("Tabelle") #ref.slice("Tabelle ".len())] else [#get-norm(v) §#ref]
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
  align(right + horizon, text(size: 8pt, norm-text(note-var)))
}

// The same citation set **on the line** it cites, at the end of it: a box as wide as the citation column, pushed to the right edge. A stacked formula's first line is measured to its ink (chain-cell), and a fraction whose numerator is built higher than its denominator puts the middle of that ink well above the `=`, so a citation centred in its row sat level with the numerator; on the line, it stands on the formula's own baseline.
#let note-on-line(note-var) = h(1fr) + box(width: note-column, align(right, text(size: 8pt, norm-text(note-var))))

// --- A formula too wide for its row, stacked at its relation signs -----------
// A calculation printed in letters, in numbers and as its answer stands on one line -- `B_v = <letters> = <numbers> = 116.122 kN` -- and a display fraction is one atom that cannot break (`show math.frac: it => $display(it)$` in the report's config.typ). So a line wider than its row ran into the citation column and off the page (the engineer's exercise: «une longue fraction qui ne peut pas passer à la ligne déborde dans la colonne des références»), and one that could break broke wherever the width ran out, an `=` left dangling at the end of a line. Such a line is now set the classic way, **stacked at its relation signs**: `B_v = <letters>`, then `= <numbers>`, then `= 116.122 kN`, each `=` under the first -- as rows of the same grid, so the citation stays level with the first line. A line that fits is set exactly as it always was: what is measured decides, and nothing else changes.
//
// A row that may be stacked is a `formula-chain`: the one line it has always been (`line`), and what it is stacked into -- its first line (`first`, the left-hand side and the formula in letters), the segments after it (`rest`, math source, the numbers and the answer), the function that sets some of them as one line under the first (`build`, given them joined by ` = `), and what the last line ends on (`last`, a label or a footnote). `annotated-rows` measures the one line against the width the row has -- the column left of the citation, or the full width where the row carries none -- and stacks only where it does not fit.
#let formula-chain(line, first, rest, build, last: x => x) = (chain: true, line: line, first: first, rest: rest, build: build, last: last)
#let is-chain(c) = type(c) == dictionary and c.at("chain", default: false) == true

// The one line of a row that may be a chain: what a caller joining rows into a line of its own reads (show-polar-moment's `n = 4; I_p = …`).
#let one-line(c) = if is-chain(c) { c.line } else { c }

// A line after the first of a stacked formula: its relation and what follows it, set where the first line's relation stands. The first line's left-hand side is **measured** and an empty box of that width stands in its place inside the same equation, so the space math sets around the `=` is the first line's own and the two signs fall one under the other to the point. `wrap` is what the line is set in -- `math.bold` for an answer -- and `side` what the first line's left-hand side was set in, `wrap` unless said otherwise: a bold B_v is wider than a regular one, and a step set on one row prints its letters regular and its numbers bold. Read inside a context, like everything that measures.
#let chain-line(lhs, rel, seg, scope: (:), wrap: x => x, side: auto) = {
  let side = if side == auto { wrap } else { side }
  let pad = box(width: measure(side(eval(lhs, mode: "math", scope: scope))).width)
  wrap(eval("#chain-pad " + rel + " " + seg, mode: "math", scope: scope + (chain-pad: pad)))
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

// Symbol/formula strings in data/ are authored as Typst math source (e.g. "C_e", "gamma_M", "f_(m,k)") so they render with real subscripts and Greek glyphs instead of literal underscores -- never print get-symbol() or a formula string as plain text.

// A symbol that is nothing but a quoted word is a word, not a symbol: the load model, the terrain category, the category of Nutzfläche -- a var whose value is text has no letter to stand for it, so its own name is set in its place. Those follow the report's language like every other word; q_k, C_e and mu do not, being the norm's own letters in every language.
//
// ⚠️ The `///` block below must stay **flush against the `#let`**: a plain `//` line between the two detaches it, and the editor then shows no tooltip at all -- which is what this very comment was doing until v0.63.1.
/// Evaluates a var's `symbol` field as Typst math source and returns real rendered math (a real subscript / Greek glyph), not a string (section 6bis).
///
/// ```typ
/// #render-symbol(var-of("snow-load", "SL", "q_k11"))
/// ```
///
/// ```typ
/// #for n in ("h_ref", "ce", "s_k") [ #render-symbol(var-of("snow-load", "SL", n)) #h(1em) ]
/// ```
///
/// - v (dictionary): a `var` object (section 3.1) whose `symbol` field is valid Typst math source.
/// -> content
#let render-symbol(v) = {
  let src = get-symbol(v)
  let word = src.match(regex("^\"([^\"]+)\"$"))
  // A symbol that is a word («Lastmodell») follows the report's language, which is a state: read inside a context of its own, so the call works in plain markup as var-of's own example writes it -- it failed there with «can only be used when context is known» (v0.86).
  if word != none {
    return context eval("\"" + tl-str(word.captures.first()) + "\"", mode: "math")
  }
  eval(src, mode: "math")
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
#let render-formula(step) = eval(step.formula, mode: "math")

/// One sentence the data carries — a table's note, a var's or a step's description, a choice — with the symbols in it set as real math (section 6bis). A symbol inside a sentence is written between dollars, as it would be in a formula: `$c_"red"$ ist der Reduktionsfaktor` prints c with the subscript red where `cred` printed three letters.
///
/// ```typ
/// #render-prose("$c_\"red\"$ ist der Reduktionsfaktor der Bezugsfläche.")
/// ```
///
/// ```typ
/// #context render-prose(tl-str(get-description(var-of("snow-load", "SL", "ce"))))
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
    .map(((i, part)) => if calc.even(i) { [#prose-minus(part)] } else { eval(part, mode: "math") })
    .join()
}

// --- Position summary line (docs/domain/positions.md §7-8) -----------------------
// Positions carry no shared section catalog and no load assignment -- just their own type, material, section and description, read directly off data/positions/<id>.json (there is no "var" object to go through get-* for these plain descriptive fields, unlike vars/steps/checks above). `#member` prints this line at level 1 and calc-block heads a block with it; `show-position`, which printed it on its own until v0.94, is gone, `#member` taking any position (lib/timber.typ).

// The refusal of a position id a call names, listing the ones there are -- and saying there are none rather than joining an empty list, which gives none and not a string.
#let position-refusal(fn, position) = fn + ": no position " + repr(position) + " -- " + (if position-ids().len() == 0 { "none in Woodcore's Positions tab yet" } else { "valid positions: " + position-ids().join(", ") })

// What a position's section prints: the text domains/section.py wrote into its record at the export (v0.94) -- «100/200 mm», «Ø 200 mm», «20/30/20/30/20 mm (120 mm)», «ROR 101.6×10» -- never broken across a line; and where it has none, its dimension as typed with its unit («180 mm»), a unit never printed without its dimension. A record exported before v0.94 carries no `section`, and is printed as it was then: its dimension and its unit.
#let position-section-text(pos) = {
  let shape = pos.at("section", default: none)
  if shape != none { return shape.text.replace(" ", "\u{a0}") }
  let dimension = pos.at("dimension", default: none)
  dimension = if dimension == none { "" } else { str(dimension) }
  let units = pos.at("units", default: none)
  units = if units == none { "" } else { units }
  if dimension == "" { "" } else if units == "" { dimension } else { dimension + " " + units }
}

// What a position deleted with its values kept says wherever it is called (issue #9, the engineer: «partout où la position est appelée, un message orange apparaît et indique que les calculs portent sur les valeurs d'une ancienne position»): in the orange of what the report says of itself (override-colour, further down, which this part of the file cannot name yet), the id it had and the day it went. Called in a context; none for any other position.
#let position-archived-note(pos) = {
  let old = pos.at("archived", default: none)
  if old == none { return none }
  block(above: 0.3em, below: 0.3em, text(size: 0.9em, fill: rgb("#b35c00"), t-str("position.archived") + " " + old.was + " (" + t-str("position.archived_on") + " " + old.deleted + ")"))
}

// One position's line -- «*T001*: Träger, Fichte C24, 100/200 mm, Feuchteklasse 1 (Achse 3 / Achse C) --- UK» (docs/domain/positions.md §7): its type, its material and strength class as one part, its section, its moisture class, the axes the call gives in parentheses, and with `description` the row's free text after an em dash. What the sheet leaves blank is left out, without a dangling separator. `name`, `grade`, `section` and `moisture` replace the id, the strength class, the section's text and the moisture class where #member writes one over, so that the line says what is calculated. The id is not checked here: the caller has.
#let position-line(position, description: false, axes: none, name: auto, grade: auto, section: auto, moisture: auto) = context {
  let pos = load-position(position)
  let dim = if section == auto { position-section-text(pos) } else { section }
  // the moisture class is a number, or none for a position that is not timber (section 7) -- "Feuchteklasse 1", never broken across a line
  let mc = if moisture == auto { pos.at("moisture_class", default: none) } else { moisture }
  let moisture-text = if mc == none { "" } else { t-str("moisture_class") + "\u{a0}" + str(mc) }
  // the material and its strength class read as one part, "Fichte C24"; a record exported before the sheet had a `resistance class` column carries none, its `material` being the strength class then
  let strength = if grade == auto { pos.at("strength_class", default: "") } else { grade }
  let material = (pos.at("material", default: ""), strength).filter(s => s != "" and s != none).join(" ")
  // material and the moisture class are facultative, so join only the parts that are actually filled in rather than printing "Träger, , 140/400 mm"
  // the type is stored once, as the STE key (German); it is printed in the language the report is compiled in, a type typed freely -- one the glossary does not carry -- as typed (v0.116)
  let type-text = tl-str(pos.at("type", default: ""))
  let parts = (type-text, if material == none { "" } else { material }, dim, moisture-text).filter(s => s != "" and s != none)
  [
    *#(if name == auto { pos.at("position", default: position) } else { name })*#colon-str() #parts.join(", ")
    #if axes != none [ (#axes)]
    #let free = pos.at("description", default: "")
    #if description and free != "" and free != none [ --- #free]
    #position-archived-note(pos)
  ]
}

/// The moisture class of a position (Feuchteklasse, docs/domain/positions.md §7): 1, 2 or 3, or none where Woodcore's Positions tab leaves it blank -- what a calculation written in Typst picks its factors by. Data access, not a display function, so it works in a plain `#let`: `#let fk = moisture-class-of("T001")`.
///
/// ```typ
/// #moisture-class-of("T001")
/// ```
///
/// ```typ
/// #for id in position-ids() [ #id: Feuchteklasse #moisture-class-of(id) \ ]
/// ```
///
/// - position (str): position id, e.g. "T001". An unknown id fails listing the valid ones.
/// -> int | none
#let moisture-class-of(position) = {
  let known = known-position-ids()
  assert(type(position) == str and position in known,
    message: "moisture-class-of: no position " + repr(position) + " -- " + (if known.len() == 0 { "none in Woodcore's Positions tab yet" } else { "valid positions: " + known.join(", ") }))
  load-position(position).at("moisture_class", default: none)
}

// --- Connector summary display (docs/domain/connectors.md §7bis) -------------------
// A connector is a descriptive record like a position, read directly off data/connectors.json: what the connector's source says about it, and nothing it leaves empty.

// "SD001: Stabdübel, Holz-Holz zweischnittig, Ø 12 mm, L = 160 mm, S235, vorgebohrt (Bauteile: T001, S001)" -- show-connector's line.
#let connector-summary(c) = {
  // "Ø 12 mm" and "L = 160 mm" are never broken across a line
  let size(prefix, q) = context prefix + signed-text(fmt-decimals(q.value, number-digits.get())) + "\u{a0}" + q.unit
  // the type and the assembly are the engine's words, which the glossary carries: printed in the report's language, as show-connector-resistance's heading prints them (periodic audit 260916)
  let parts = (c.type, c.assembly).filter(s => s != "").map(s => [#tl-str(s)])
  if c.diameter != none { parts.push(size("Ø\u{a0}", c.diameter)) }
  if c.length != none { parts.push(size("L\u{a0}=\u{a0}", c.length)) }
  if c.dimension != "" { parts.push([#c.dimension]) }
  if c.steel != "" { parts.push([#c.steel]) }
  if c.predrilled != none { parts.push(if c.predrilled { [#t-str("predrilled")] } else { [#t-str("not_predrilled")] }) }
  [*#c.position*#colon-str() ] + parts.join([, ])
  if c.elements.len() > 0 { [ (#t-str("members_joined")#colon-str() #c.elements.join(", "))] }
}

/// Displays one connector's descriptive data (docs/domain/connectors.md §7bis): its type and assembly, diameter and length, other dimensions, steel and predrilling, and the elements it joins -- "SD001: Stabdübel, Holz-Holz zweischnittig, Ø 12 mm, S235, vorgebohrt (Bauteile: T001, S001)". What the source leaves empty is left out.
///
/// ```typ
/// #show-connector("SD-10")
/// ```
///
/// ```typ
/// #show-connector("SD-10", description: true)
/// ```
///
/// - connector (str): the connector's id, e.g. "SD-10". An unknown id fails listing the valid ones.
/// - description (bool): false (the default) prints the summary line alone; true also appends the row's `description` text.
/// - level (int, auto): accepted and validated for a consistent error if mistyped, but unused -- a connector's line reads the same at every level.
/// -> content
#let show-connector(connector, description: false, level: auto) = context {
  assert(level == auto or level in (1, 2, 3),
    message: "show-connector: invalid level " + repr(level) + " -- use auto, 1, 2, or 3")
  assert(type(description) == bool,
    message: "show-connector: description must be true or false, got " + repr(description))
  let known = load-connectors().connectors
  assert(type(connector) == str and connector in known,
    message: "show-connector: no connector " + repr(connector) + " -- " + (if known.len() == 0 { "none saved yet (Woodcore, tab Connecteurs)" } else { "valid connectors: " + known.keys().join(", ") }))
  let c = known.at(connector)
  connector-summary(c)
  if description and c.description != "" [ --- #c.description]
}

// --- Position plans (docs/domain/position-plans.md §3.3sexies) ---------------------------
// The plans drawn in Woodcore's «Plan de positions» tab, in their own file: data/plans.json. A plan is a background -- the page of the architect's PDF it was drawn on, or an image, copied under data/plans/ -- and an SVG of the STE symbols over the same frame, in the background's own units (its sheet); show-plan sets the one exactly over the other. A position appears on a plan by its number and nothing else: the plan says where it is, Positionen.xlsx what it is.
#let load-plans() = json("../data/plans.json")

// A coordinate as SVG text: two decimals, and a hyphen for the sign -- Typst's str() writes a typographic minus, which an SVG parser does not read (as svg-number does for a connection's arrows, further down).
#let plan-number(x) = str(calc.round(x, digits: 2)).replace("−", "-")

/// Every position plan saved in Woodcore, in file-name order (docs/domain/position-plans.md §3.3sexies). Data access, not a display function: `for p in plan-ids() { show-plan(p) }`, the loop Sections/003-baustoffe.typ is written as.
///
/// ```typ
/// #plan-ids()
/// ```
///
/// ```typ
/// #for p in plan-ids() [ #p \ ]
/// ```
///
/// -> array
#let plan-ids() = load-plans().plans.keys()

/// The plans a position is drawn on, in file-name order -- what `calc-block(..., plan: auto)` shows. Data access, not a display function.
///
/// ```typ
/// #plans-of("T001")
/// ```
///
/// ```typ
/// #for p in plans-of("S001") {
///   show-plan(p, highlight: "S001", detail: true, width: 40%)
/// }
/// ```
///
/// - position (str): a position id, e.g. "T001".
/// -> array
#let plans-of(position) = load-plans().plans.pairs().filter(((_, p)) => position in p.labels).map(((id, _)) => id)

// The halo show-plan draws under the positions it highlights, as SVG elements for the plan's `<!-- highlight -->` marker: along a line, over an area, round a point -- sized by the plan's symbol unit and sliders, so it is as broad on every plan.
#let plan-halo(p, labels) = {
  let colour = "#ffcc00"
  let w-line = p.unit * p.style.at("line", default: 1)
  let w-point = p.unit * p.style.at("point", default: 1)
  let points(e) = e.points.map(q => plan-number(q.at(0)) + "," + plan-number(q.at(1))).join(" ")
  let out = ""
  for e in p.elements.filter(e => e.label in labels) {
    if e.kind == "point" {
      let q = e.points.first()
      out += "<circle cx=\"" + plan-number(q.at(0)) + "\" cy=\"" + plan-number(q.at(1)) + "\" r=\"" + plan-number(16 * w-point) + "\" fill=\"" + colour + "\" fill-opacity=\"0.6\"/>"
    } else if e.kind == "line" {
      out += "<polyline points=\"" + points(e) + "\" fill=\"none\" stroke=\"" + colour + "\" stroke-opacity=\"0.6\" stroke-width=\"" + plan-number(18 * w-line) + "\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>"
    } else {
      out += "<polygon points=\"" + points(e) + "\" fill=\"" + colour + "\" fill-opacity=\"0.3\" stroke=\"" + colour + "\" stroke-opacity=\"0.7\" stroke-width=\"" + plan-number(8 * w-line) + "\" stroke-linejoin=\"round\"/>"
    }
  }
  out
}

// The scale bar under a plan: a round length, about a fifth of the plan's width but never much shorter than 2.5 cm, in alternate black and white parts -- a 2 m bar in four half metres, 1 m or 5 m in five --, the metres under its ends (and its middle, where that is a part's end). Under the plan, not on it, where it would hide part of the drawing. `per-m` is the printed length of one metre of the building, `width` the plan's printed width. It measures its numbers, so it carries its own `context`: a sheet calls it outside one (issue #9).
#let plan-scale-bar(per-m, width) = {
  context {
    let room = calc.min(0.8 * width, calc.max(0.2 * width, 25mm))
    let length = (100, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1).find(v => v * per-m <= room)
    if length == none { length = 0.1 }
    let parts = if calc.round(length / calc.pow(10, calc.floor(calc.log(length)))) == 2 { 4 } else { 5 }
    let part = length / parts * per-m
    let ink = luma(20%)
    set text(size: 7pt, fill: ink)
    let at(x, body) = place(top + left, dx: x - measure(body).width / 2, body)
    let bar = stack(dir: ltr, ..range(parts).map(i => rect(width: part, height: 1.1mm, stroke: 0.4pt + ink, fill: if calc.even(i) { ink } else { white })))
    let marks = box(width: parts * part, height: measure[0].height, {
      at(0pt, [0])
      if parts == 4 { at(2 * part, [#(length / 2)]) }
      // the unit follows the last number, which stays centred under the bar's end
      place(top + left, dx: parts * part - measure[#length].width / 2, [#length~m])
    })
    stack(spacing: 0.9mm, bar, marks)
  }
}

// The legend of a plan: each symbol it uses -- drawn by plan_svg.py, as on the plan -- beside what it stands for, in the report's own typeface, read down one column and then the next, in as many columns (three at most) as `width` takes without a line wrapping. A plan exported before schema 1.1 (by a Woodcore window not restarted since) has its legend as one SVG, shown as it is.
#let plan-legend(p, width) = {
  let lines = p.legend
  if type(lines) == str { return image("../data/" + lines, width: width) }
  if lines.len() == 0 { return none }
  let (size, swatch, gap, gutter) = (8pt, 10mm, 2.2mm, 5mm)
  // STE's wording is the engine's, not the plan's: a line is looked up by the `key` the export already carries (section 3.3sexies), and a symbol the glossary does not know yet keeps the text it was drawn with.
  // A fire-protection plan's lines (v0.115) say it themselves: `engine` is the glossary key of the engine's own word, `term` the glossary term the sheet's German stands for.
  let wording(l) = {
    let key = "plan.legend." + l.key
    if "engine" in l { t-str(l.engine) }
    else if "term" in l { tl-str(l.term) }
    else if key in glossary.engine { t-str(key) } else { l.text }
  }
  let widest = calc.max(..lines.map(l => measure(text(size: size, wording(l))).width))
  let columns = calc.max(1, calc.min(3, lines.len(), int((width + gutter) / (swatch + gap + widest + gutter))))
  let rows = calc.ceil(lines.len() / columns)
  let cells = ()
  for r in range(rows) {
    for c in range(columns) {
      let i = c * rows + r
      cells += if i < lines.len() { (image(bytes(lines.at(i).swatch), format: "svg"), wording(lines.at(i))) } else { ([], []) }
    }
  }
  set text(size: size, fill: luma(25%))
  set par(justify: false)
  let symbols = block(width: width, grid(
    columns: (swatch, 1fr) * columns,
    column-gutter: range(2 * columns - 1).map(i => if calc.even(i) { gap } else { gutter }),
    row-gutter: 1.8mm,
    align: left + horizon,
    ..cells,
  ))
  // Under the symbols, the plan's quantities by kind of symbol (v0.117, the engineer: «dans légende … sous le descriptif des symboles, les métrés totaux par type d'objet»): what the export measured (calc/domains/plan.py quantities) -- the lines in metres, the areas in square metres, the points counted --, the decimal a point in every language. Nothing on a plan with no scale, which carries none.
  let measured = lines.filter(l => "quantity" in l)
  if measured.len() == 0 { return symbols }
  let amount(q) = if q.unit == "pcs" { str(q.value) + " " + t-str("plan.legend.pieces") } else {
    fmt-decimals(q.value, 2).split(".").at(0) + "." + (fmt-decimals(q.value, 2).split(".").at(1, default: "") + "00").slice(0, 2) + if q.unit == "m2" { " m²" } else { " m" }
  }
  stack(spacing: 2.6mm, symbols, block(width: width, {
    text(weight: "bold", t-str("plan.legend.quantities"))
    v(1mm, weak: true)
    grid(columns: (1fr, auto), column-gutter: gutter, row-gutter: 1.2mm,
      ..measured.map(l => (wording(l), align(right, amount(l.quantity)))).flatten())
  }))
}

// The drawing of plan `p` -- the architect's page faded under it, the STE symbols over it -- cut to `window` (in the plan's sheet units; the plan's own crop by default) and printed at `s`, a length per sheet unit. What show-plan sets in a report, at a scale it works out from the column, and sheet-viewport and sheet-section on an export sheet, at the scale the sheet states (lib/sheet.typ, v0.114) -- one drawing, so the two cannot come to draw a plan two ways. `marked` puts a halo under those positions and `extra` is SVG of the caller's put in at the same `<!-- highlight -->` marker (a section's storey); the marker is left alone where there is neither, so a plan with nothing highlighted is the very SVG the export wrote. `axes: false` strips the axes, `legend: false` the legend a fire-protection plan carries on itself (a position plan has none on its overlay: its legend is `plan-legend`'s), `dimensions: false` the plan's dimensions and `lengths: false` the lengths written beside its elements (issue #9) -- each between markers the drawing writes only where it has some.
//
// Both images are given their width and their height: given one only, an image covers the area its container leaves it (fit: "cover"), and a detail's box, shorter than the plan, would crop them about their middle.
#let plan-figure(p, s, window: auto, marked: (), axes: true, extra: "", legend: true, dimensions: true, lengths: true) = {
  let crop = p.crop
  let window = if window == auto { crop } else { window }
  // A fire-protection plan (v0.115) is drawn once per language -- its legend carries words --, and so is a section carrying a load transfer level (v0.116, «Niveau de reprise des charges (x0xx)»): the figure of the report's language is the one set. Every other position plan has the one overlay. Reading the language needs a context, which a drawing with `figures` is set in here -- so that a sheet's viewport or section, which stands in none, sets one too.
  let draw(file) = {
    let overlay = read("../data/" + file)
    if not axes {
      overlay = overlay.replace(regex("(?s)<!-- axes -->.*?<!-- /axes -->"), "")
    }
    if not legend {
      overlay = overlay.replace(regex("(?s)<!-- legend -->.*?<!-- /legend -->"), "")
    }
    if not dimensions {
      overlay = overlay.replace(regex("(?s)<!-- dimensions -->.*?<!-- /dimensions -->"), "")
    }
    if not lengths {
      overlay = overlay.replace(regex("(?s)<!-- lengths -->.*?<!-- /lengths -->"), "")
    }
    if marked.len() > 0 or extra != "" {
      overlay = overlay.replace("<!-- highlight -->", plan-halo(p, marked) + extra)
    }
    box(width: window.w * s, height: window.h * s, clip: true, {
      if "background" in p {
        place(top + left, dx: -window.x * s, dy: -window.y * s,
          image("../data/" + p.background.file, width: p.sheet.width * s, height: p.sheet.height * s, fit: "stretch"))
      }
      place(top + left, dx: -(window.x - crop.x) * s, dy: -(window.y - crop.y) * s,
        image(bytes(overlay), format: "svg", width: crop.w * s, height: crop.h * s, fit: "stretch"))
    })
  }
  if "figures" in p { context draw(p.figures.at(report-lang())) } else { draw(p.overlay) }
}

/// Displays a position plan drawn in Woodcore (docs/domain/position-plans.md §3.3sexies): the architect's plan it was drawn on, faded, with the structure's STE symbols, their position numbers and the axes over it, the frame the plan was cropped to, and under it the scale bar and the legend of the symbols it uses. The caption gives the printed scale when the plan has one.
///
/// ```typ
/// #show-plan("Velo-Unterstand")
/// ```
///
/// ```typ
/// #show-plan("Pavillon", highlight: ("S001", "S002"), detail: true)
/// ```
///
/// ```typ
/// #show-plan("Fluchttreppe", width: 60%, legend: false, axes: false)
/// ```
///
/// A position is highlighted by a halo under its symbol; `detail: true` then shows only the part of the plan around the highlighted positions -- at the scale the whole plan would be printed at, so its symbols and numbers keep their size -- which is what a calculation block's header shows.
/// - plan (str): the plan's id, as saved in Woodcore ("EG", "Pavillon"). An unknown id fails listing the valid ones.
/// - width (relative, length): the width the whole plan is printed at, 100% of the text width by default; a plan taller than it is wide is kept within three quarters of the page's height. A detail is printed at the same scale, so it is narrower.
/// - legend (bool): the legend under the plan. Not printed under a detail.
/// - highlight (str, array, none): the position(s) to highlight, e.g. "T001" or ("T001", "S001"); each must be drawn on this plan.
/// - detail (bool): show only the surroundings of the highlighted positions, their symbols and their numbers -- 1.5 m around them where the plan has a scale, a tenth of the plan otherwise. Needs `highlight`.
/// - zoom (int, float): enlarges a detail beyond the plan's scale, symbols included -- up to the column's width and three quarters of the page's height; 1 by default.
/// - axes (bool): the axes and their bubbles; false leaves them out.
/// - dimensions (bool): the dimensions drawn on the plan in Woodcore; false leaves them out.
/// - lengths (bool): the lengths written beside the walls, the beams and the slabs, where the plan or an element asks for them; false leaves them out.
/// - scale-bar (bool): the scale bar under the plan, where the plan has a scale; false leaves it out.
/// - caption (content, str, none, auto): auto names the plan (and the positions a detail frames) with the scale; none prints the plan without a figure around it; anything else replaces the caption.
/// -> content
#let show-plan(plan, width: 100%, legend: true, highlight: none, detail: false, zoom: 1, axes: true, dimensions: true, lengths: true, scale-bar: true, caption: auto) = {
  let plans = load-plans().plans
  assert(type(plan) == str and plan in plans,
    message: "show-plan: no plan " + repr(plan) + " -- " + (if plans.len() == 0 { "none saved yet (draw one in Woodcore's position plan tab)" } else { "valid plans: " + plans.keys().join(", ") }))
  let p = plans.at(plan)
  let marked = if highlight == none { () } else if type(highlight) == str { (highlight,) } else { highlight }
  for label in marked {
    assert(type(label) == str and label in p.labels,
      message: "show-plan: plan '" + plan + "' does not show " + repr(label) + " -- it shows " + (if p.labels.len() == 0 { "no position" } else { p.labels.join(", ") }))
  }
  assert(not detail or marked.len() > 0,
    message: "show-plan: detail: true frames the highlighted positions -- give highlight: \"T001\" as well")
  assert((type(zoom) == int or type(zoom) == float) and zoom > 0,
    message: "show-plan: zoom must be a number greater than 0, got " + repr(zoom))
  assert(type(dimensions) == bool and type(lengths) == bool,
    message: "show-plan: dimensions: and lengths: are true or false, got " + repr((dimensions, lengths)))

  let crop = p.crop
  let window = if detail {
    // each highlighted element's points, and the centre of its number -- which the engineer may have moved clear of the symbol (a plan exported before schema 1.2 does not say where it is)
    let pts = p.elements.filter(e => e.label in marked).map(e => e.points + (if "label_at" in e { (e.label_at,) } else { () })).join()
    let margin = if "scale" in p { 1.5 * p.scale.units_per_m } else { 0.1 * calc.max(crop.w, crop.h) }
    let x0 = calc.max(crop.x, calc.min(..pts.map(q => q.at(0))) - margin)
    let y0 = calc.max(crop.y, calc.min(..pts.map(q => q.at(1))) - margin)
    let x1 = calc.min(crop.x + crop.w, calc.max(..pts.map(q => q.at(0))) + margin)
    let y1 = calc.min(crop.y + crop.h, calc.max(..pts.map(q => q.at(1))) + margin)
    (x: x0, y: y0, w: calc.max(x1 - x0, 1e-6), h: calc.max(y1 - y0, 1e-6))
  } else { crop }

  layout(size => {
    let full = if type(width) == length { width } else if type(width) == ratio { width * size.width } else { width.ratio * size.width + width.length }
    // length per sheet unit: the whole plan at `width`, kept within three quarters of the page's height
    let s = full / crop.w
    // a region without a height of its own (a box that grows with its content) says so with an infinite one
    if size.height > 0pt and size.height < 100000pt {
      s = calc.min(s, 0.75 * size.height / crop.h)
    }
    if detail {
      s = s * zoom
      // ⚠️ The zoom enlarges a detail up to the column's width and three quarters of the page's height, and no further: applied after those two limits, zoom: 2 ran the drawing past both edges of the page (v0.86).
      s = calc.min(s, size.width / window.w)
      if size.height > 0pt and size.height < 100000pt { s = calc.min(s, 0.75 * size.height / window.h) }
    }
    let body = plan-figure(p, s, window: window, marked: marked, axes: axes, dimensions: dimensions, lengths: lengths)
    // under the plan: its scale bar, where it has a scale, set against the plan's left edge; then its legend, as wide as the plan but not narrower than a legend reads well at
    let framed = if scale-bar and "scale" in p {
      stack(spacing: 0.7em, body, block(width: window.w * s, align(left, plan-scale-bar(p.scale.units_per_m * s, window.w * s))))
    } else { body }
    let key = if legend and not detail { plan-legend(p, calc.min(size.width, calc.max(window.w * s, 11cm))) } else { none }
    let content = if key == none { framed } else { stack(spacing: 1.2em, framed, key) }
    let scale = if "scale" in p {
      // 1:n of the paper: a metre of the building is 1/units_per_m sheet units, each printed s long
      let n = 1 / (p.scale.units_per_m * (s / 1000mm))
      let rounded = if n >= 20 { calc.round(n / 5) * 5 } else { calc.round(n) }
      " (" + t-str("plan.scale_approx") + str(int(rounded)) + ")"
    } else { "" }
    if caption == none {
      content
    } else {
      figure(
        content,
        caption: if caption != auto { caption } else {
          [#t-str("plan.caption", id: plan)#if p.label != "" [#colon-str() #p.label]#if detail [, #t-str("plan.crop") #marked.join(", ")]#scale]
        },
      )
    }
  })
}

/// Displays the legend of a position plan on its own: the STE symbols the plan uses, with what each stands for -- for a report that prints the legend once, under several plans or before them.
///
/// ```typ
/// #show-plan-legend("Velo-Unterstand")
/// ```
///
/// ```typ
/// #show-plan-legend("Pavillon", width: 60%)
/// ```
///
/// - plan (str): the plan's id, as saved in Woodcore.
/// - width (relative, length): the width the legend's columns share, the text width by default.
/// -> content
#let show-plan-legend(plan, width: 100%) = {
  let plans = load-plans().plans
  assert(type(plan) == str and plan in plans,
    message: "show-plan-legend: no plan " + repr(plan) + " -- " + (if plans.len() == 0 { "none saved yet" } else { "valid plans: " + plans.keys().join(", ") }))
  layout(size => plan-legend(plans.at(plan), if type(width) == length { width } else if type(width) == ratio { width * size.width } else { width.ratio * size.width + width.length }))
}

// --- Fire-protection plans (calc/domains/fire.py, v0.115) ---------------------------------------------
// The plans drawn in Woodcore's «Plan de protection incendie» tab, in their own file: data/fire.json. A plan is a figure -- the surfaces of the escape routes, the walls with their fire resistance, the doors, the escape routes' lengths, exits and widths, and its legend, drawn by calc/domains/fire_svg.py once per language of the report, the legend carrying words -- set exactly over a background: the architect's plan it was drawn on, which is the position plan's own exported page where the plan follows a position plan. A drawing and not a calculation: what it measures -- an area, a length, a width -- is the drawing's own. It is set by `plan-figure`, as a position plan is, so a report, a sheet and a detail cannot come to draw one two ways.
#let load-fire-plans() = json("../data/fire.json")

/// Every fire-protection plan saved in Woodcore's «Plan de protection incendie» tab, in file-name order. Data access, not a display function: `for p in fire-plan-ids() { show-fire-plan(p) }` prints them all, and a plan saved in Woodcore joins that loop with no edit.
///
/// ```typ
/// #fire-plan-ids()
/// ```
///
/// ```typ
/// #for p in fire-plan-ids() [ #p \ ]
/// ```
///
/// -> array
#let fire-plan-ids() = load-fire-plans().plans.keys()

/// Displays a fire-protection plan drawn in Woodcore's «Plan de protection incendie» tab: the architect's plan it was drawn on, faded, and over it the fire-protection concept in the colours of the VKF / AEAI sheet of symbols -- the surfaces of the escape routes, the walls as the band of their fire resistance, the doors, the escape routes' lengths, the emergency exits and the widths -- with the legend placed on it in Woodcore, written in the report's language. Under it the scale bar, where the plan has a scale; the caption gives the printed scale.
///
/// ```typ
/// #show-fire-plan("Treppenhaus")
/// ```
///
/// ```typ
/// #show-fire-plan("Pavillon-EG", width: 70%)
/// ```
///
/// ```typ
/// #show-fire-plan("Treppenhaus", width: 60%, legend: false, scale-bar: false, caption: none)
/// ```
///
/// A drawing and not a calculation: it has no levels, and nothing on it is checked. What it shows of the sheet is the plan's crop -- its own, or the one of the position plan it follows.
/// - plan (str): the plan's id, as saved in Woodcore ("Pavillon-EG", "Treppenhaus"). An unknown id fails listing the valid ones.
/// - width (relative, length): the width the plan is printed at, 100% of the text width by default; a plan taller than it is wide is kept within three quarters of the page's height.
/// - legend (bool): the legend drawn on the plan, where Woodcore placed one; false leaves it out.
/// - scale-bar (bool): the scale bar under the plan, where the plan has a scale; false leaves it out.
/// - caption (content, str, none, auto): auto names the plan with its description and the printed scale; none prints the plan without a figure around it; anything else replaces the caption.
/// -> content
#let show-fire-plan(plan, width: 100%, legend: true, scale-bar: true, caption: auto) = {
  let plans = load-fire-plans().plans
  assert(type(plan) == str and plan in plans,
    message: "show-fire-plan: no plan " + repr(plan) + " -- " + (if plans.len() == 0 { "none saved yet (draw one in Woodcore's fire-protection plan tab)" } else { "valid plans: " + plans.keys().join(", ") }))
  let p = plans.at(plan)
  let crop = p.crop

  layout(size => {
    let full = if type(width) == length { width } else if type(width) == ratio { width * size.width } else { width.ratio * size.width + width.length }
    // length per sheet unit: the plan at `width`, kept within three quarters of the page's height
    let s = full / crop.w
    // a region without a height of its own (a box that grows with its content) says so with an infinite one
    if size.height > 0pt and size.height < 100000pt {
      s = calc.min(s, 0.75 * size.height / crop.h)
    }
    let body = plan-figure(p, s, legend: legend)
    let content = if scale-bar and "scale" in p {
      stack(spacing: 0.7em, body, block(width: crop.w * s, align(left, plan-scale-bar(p.scale.units_per_m * s, crop.w * s))))
    } else { body }
    let scale = if "scale" in p {
      // 1:n of the paper: a metre of the building is 1/units_per_m sheet units, each printed s long
      let n = 1 / (p.scale.units_per_m * (s / 1000mm))
      let rounded = if n >= 20 { calc.round(n / 5) * 5 } else { calc.round(n) }
      " (" + t-str("plan.scale_approx") + str(int(rounded)) + ")"
    } else { "" }
    if caption == none {
      content
    } else {
      figure(
        content,
        caption: if caption != auto { caption } else {
          [#t-str("fire.caption", id: plan)#if p.label != "" [#colon-str() #p.label]#scale]
        },
      )
    }
  })
}

// --- Static models (docs/domain/static-models.md §3.3octies) ---------------------------
// The static systems drawn in Woodcore's «Modèles statiques» tab, in their own file: data/statics.json. A model is one SVG, drawn whole by calc/domains/statics_svg.py -- there is no background under it, which is the one way it is simpler than a plan. It is a drawing and not a calculation: no reactions, no N/V/M, and deliberately nothing show-calc can address.
#let load-statics() = json("../data/statics.json")

// A coordinate as SVG text: three decimals, and a hyphen for the sign -- Typst's str() writes a typographic minus, which an SVG parser does not read (the rule plan-number and svg-number follow, at the precision a figure normalised to a thousand units wants).
#let static-number(x) = str(calc.round(x, digits: 3)).replace("−", "-")

/// Every static model saved in Woodcore, in file-name order (docs/domain/static-models.md §3.3octies). Data access, not a display function: `for s in static-model-ids() { show-static-model(s) }`, the loop Sections/005-tragwerksanalyse.typ is written as.
///
/// ```typ
/// #static-model-ids()
/// ```
///
/// ```typ
/// #for s in static-model-ids() {
///   show-static-model(s, width: 50%)
/// }
/// ```
///
/// -> array
#let static-model-ids() = load-statics().models.keys()

// The halo show-static-model draws under the parts it highlights, as SVG elements for the figure's `<!-- highlight -->` marker: along a member, round a node, round a load's arrows -- sized by the model's own symbol unit and sliders, so it is as broad on every figure. Drawn in Typst and not in Python for the reason a plan's is: which part is highlighted is the call's to say, not the drawing's.
#let static-halo(m, ids) = {
  let colour = "#ffd34d"
  let u = m.unit * m.style.at("point", default: 1)
  let pt(p) = static-number(p.at(0)) + "," + static-number(p.at(1))
  let stroke-line(a, b, w) = (
    "<line x1=\"" + static-number(a.at(0)) + "\" y1=\"" + static-number(a.at(1)) + "\" x2=\""
      + static-number(b.at(0)) + "\" y2=\"" + static-number(b.at(1)) + "\" stroke=\"" + colour
      + "\" stroke-width=\"" + static-number(w) + "\" stroke-linecap=\"round\"/>"
  )
  let disc(p, r) = (
    "<circle cx=\"" + static-number(p.at(0)) + "\" cy=\"" + static-number(p.at(1)) + "\" r=\""
      + static-number(r) + "\" fill=\"" + colour + "\"/>"
  )
  let out = ()
  for member in m.members {
    if member.id in ids { out.push(stroke-line(member.at.at(0), member.at.at(1), 3.2 * u)) }
  }
  for point in m.points {
    if point.id in ids { out.push(disc(point.at, 2.6 * u)) }
  }
  for support in m.supports {
    if support.id in ids { out.push(disc(support.at, 5.5 * u)) }
  }
  for release in m.releases {
    if release.id in ids { out.push(disc(release.at, 3.4 * u)) }
  }
  for load in m.loads {
    if load.id in ids { out.push(disc(load.at, 4.0 * u)) }
  }
  // a length is marked along the line it is written on; an angle under the value itself, its arc being a polyline this side does not carry
  for dim in m.at("dimensions", default: ()) {
    if dim.id in ids {
      if "line" in dim { out.push(stroke-line(dim.line.at(0), dim.line.at(1), 2.2 * u)) }
      else { out.push(disc(dim.at, 4.0 * u)) }
    }
  }
  // an empty array joins to `none`, which `str.replace` will not take: an id the figure draws nothing for leaves the marker as it is
  if out.len() == 0 { "" } else { out.join("") }
}

/// Displays a static model (statisches System) drawn in Woodcore (docs/domain/static-models.md §3.3octies): the members, where they are held, where they are hinged, and the loads that act on them, with each load's name and value as the model says to show them. It is a drawing and nothing else -- no reaction, no internal force and no check is computed anywhere behind it.
///
/// ```typ
/// #show-static-model("Bankli-Fall1")
/// ```
///
/// ```typ
/// #show-static-model("Bankli-Fall1", loads: false)
/// ```
///
/// ```typ
/// #show-static-model("Bankli-Fall2", width: 70%, highlight: "B1")
/// ```
///
/// A load whose magnitude names a variable of the export carries that workbook's value, read afresh at every export, and the influence width b_e it is multiplied by where the model gives one.
/// - model (str): the model's id, as saved in Woodcore ("Bankli-Fall1"). An unknown id fails listing the valid ones.
/// - width (relative, length): the width the figure is printed at, 100% of the text width by default; one taller than it is wide is kept within three quarters of the page's height.
/// - loads (bool): the loads and their labels; false shows the bare system, which is how a report prints the system first and the actions after it.
/// - dimensions (bool): the dimensions and their values; false leaves them out. They stand in a region of their own, so the two flags are independent: a system may be printed dimensioned and bare, then undimensioned with its actions, both in the same frame at the same scale.
/// - highlight (str, array, none): the part(s) to put a halo under, by id -- a point, a member, a support, a release, a load or a dimension, as the model's own list names them.
/// - caption (content, str, none, auto): auto names the model; none prints the figure without a figure around it; anything else replaces the caption.
/// -> content
#let show-static-model(model, width: 100%, loads: true, dimensions: true, highlight: none, caption: auto) = context {
  let models = load-statics().models
  assert(type(model) == str and model in models,
    message: "show-static-model: no static model " + repr(model) + " -- " + (if models.len() == 0 { "none saved yet (draw one in Woodcore's static models tab)" } else { "valid models: " + models.keys().join(", ") }))
  let m = models.at(model)
  let marked = if highlight == none { () } else if type(highlight) == str { (highlight,) } else { highlight }
  for id in marked {
    assert(type(id) == str and id in m.labels,
      message: "show-static-model: model '" + model + "' has no " + repr(id) + " -- it carries " + (if m.labels.len() == 0 { "nothing" } else { m.labels.join(", ") }))
  }
  // The figure of the report's language: the notes are drawn inside it and its frame is sized to hold them, so the frame travels with the file rather than standing beside all three (docs/typst/language.md §4bis).
  let fig = m.figures.at(report-lang())
  let figure-svg = read("../data/" + fig.file)
  if not loads {
    figure-svg = figure-svg.replace(regex("(?s)<!-- loads -->.*?<!-- /loads -->"), "")
  }
  if not dimensions {
    figure-svg = figure-svg.replace(regex("(?s)<!-- dims -->.*?<!-- /dims -->"), "")
  }
  if marked.len() > 0 {
    figure-svg = figure-svg.replace("<!-- highlight -->", static-halo(m, marked))
  }
  layout(size => {
    let full = if type(width) == length { width } else if type(width) == ratio { width * size.width } else { width.ratio * size.width + width.length }
    let s = full / fig.view.w
    // a region without a height of its own (a box that grows with its content) says so with an infinite one
    if size.height > 0pt and size.height < 100000pt {
      s = calc.min(s, 0.75 * size.height / fig.view.h)
    }
    // width and height both, as show-plan gives them: with one only, an image covers the area its container leaves it and the drawing is cropped about its middle
    let body = image(bytes(figure-svg), format: "svg", width: fig.view.w * s, height: fig.view.h * s, fit: "stretch")
    if caption == none {
      body
    } else {
      figure(
        body,
        caption: if caption != auto { caption } else {
          [#t-str("statics.caption", id: model)#if m.label != "" [#colon-str() #m.label]]
        },
      )
    }
  })
}

// --- Detail schemas (docs/domain/detail-schemas.md §3.3decies) ------------------------------
// The one drawing of a connection detail: the pieces, the fastener markers, the construction aids that are shown, and the dimensions. *Connecteurs* and *Moments polaires* name a schema since v0.74 instead of carrying their own geometry; this block prints one on its own, exactly as show-static-model prints a static model.

#let load-schemas() = json("../data/schemas.json")

/// Every detail schema saved in Woodcore, in file-name order. Data access, not a display function: `for id in schema-ids() { show-schema(id) }`.
///
/// ```typ
/// #schema-ids()
/// ```
///
/// ```typ
/// #for id in schema-ids() {
///   show-schema(id, width: 50%)
/// }
/// ```
///
/// -> array
#let schema-ids() = load-schemas().schemas.keys()

// A coordinate as SVG text: two decimals, and a hyphen for the sign -- a schema is drawn at its real size in millimetres, schema_svg.py's own precision (DIGITS = 2), and Typst's str() writes a typographic minus an SVG parser does not read (plan-number's and static-number's own rule).
#let schema-number(x) = str(calc.round(x, digits: 2)).replace("−", "-")

// The extent schema_svg.layout sizes a schema's symbols by (its `size`: font = size/40, a marker's radius size/130), worked out again from the geometry the record carries -- every piece's band or outline, every marker, every shown aid. The record carries the geometry and not the size, and a point's halo has to be drawn at the size of the point it rings, whatever the detail's scale.
#let schema-extent(m) = {
  let xs = ()
  let zs = ()
  for e in m.elements {
    let points = e.at
    // `e.at` is the piece's points -- a key of the record that shadows the dictionary method, so the width is asked for by name
    let half = if "width" in e { e.width } else { none }
    if e.kind == "linear" and half != none and points.len() > 1 {
      // a band: its axis offset by half the drawn width either side, as layout draws it
      half = half / 2
      for i in range(1, points.len()) {
        let (a, b) = (points.at(i - 1), points.at(i))
        let (dx, dz) = (b.at(0) - a.at(0), b.at(1) - a.at(1))
        let l = calc.max(calc.sqrt(dx * dx + dz * dz), 1e-9)
        for p in (a, b) {
          for s in (-1, 1) {
            xs.push(p.at(0) - s * half * dz / l)
            zs.push(p.at(1) + s * half * dx / l)
          }
        }
      }
    } else {
      for p in points { xs.push(p.at(0)); zs.push(p.at(1)) }
    }
  }
  for c in m.connectors { xs.push(c.at.at(0)); zs.push(c.at.at(1)) }
  for a in m.aids { if "at" in a { xs.push(a.at.at(0)); zs.push(a.at.at(1)) } }
  if xs.len() == 0 { return 100 }
  calc.max(calc.max(..xs) - calc.min(..xs), calc.max(..zs) - calc.min(..zs), 1)
}

// The halo show-schema draws under the parts it highlights, as SVG elements for the figure's `<!-- highlight -->` marker -- static-halo's own shape, one collection at a time: an element's whole polyline, a line-shaped aid's or a dimension's line, an angle dimension's own centre.
//
// ⚠️ A **point** is ringed, and its ring goes *over* the pieces (v0.87, the engineer: «la mise en évidence d'un point dans show-schema est invisible, cachée sous les pièces. Un point doit être affiché au-dessus de tout»). Its disc sat at `<!-- highlight -->`, before the pieces, and a piece is filled at three quarters opacity: a halo under a pin inside a beam and a post -- every pin of a joint -- did not show at all. schema_svg.body writes a second marker, `<!-- highlight-points -->`, after the pieces, the lines and the dimensions and before the markers and the named points, so the point's own symbol still stands on its halo. A ring rather than a disc: drawn above a piece, a disc covered the piece around the point, and a ring says «this one» and leaves the detail readable. It is sized from the point it rings (schema-extent), where the disc was a fixed 6 or 10 mm whatever the detail's scale. `points:` picks what is drawn: auto everything, true the points alone, false the rest.
#let schema-halo(m, ids, points: auto) = {
  let colour = "#ffd34d"
  let stroke-line(a, b, w) = (
    "<line x1=\"" + schema-number(a.at(0)) + "\" y1=\"" + schema-number(a.at(1)) + "\" x2=\""
      + schema-number(b.at(0)) + "\" y2=\"" + schema-number(b.at(1)) + "\" stroke=\"" + colour
      + "\" stroke-width=\"" + schema-number(w) + "\" stroke-linecap=\"round\"/>"
  )
  let disc(p, r) = (
    "<circle cx=\"" + schema-number(p.at(0)) + "\" cy=\"" + schema-number(p.at(1)) + "\" r=\""
      + schema-number(r) + "\" fill=\"" + colour + "\"/>"
  )
  let ring(p, r, w) = (
    "<circle cx=\"" + schema-number(p.at(0)) + "\" cy=\"" + schema-number(p.at(1)) + "\" r=\""
      + schema-number(r) + "\" fill=\"none\" stroke=\"" + colour + "\" stroke-width=\"" + schema-number(w) + "\"/>"
  )
  // schema_svg.layout's own sizes: a point's cross reaches 0.45 font either way, a marker's radius is size/130 or its own diameter's half
  let size = schema-extent(m)
  let font = size / 40
  let wanted(point) = points == auto or points == point
  let out = ()
  if wanted(false) {
    for element in m.elements {
      if element.id in ids {
        for i in range(1, element.at.len()) { out.push(stroke-line(element.at.at(i - 1), element.at.at(i), 8)) }
      }
    }
  }
  if wanted(true) {
    for c in m.connectors {
      if c.id in ids {
        let r = calc.max(size / 130, if "diameter" in c { c.diameter / 2 } else { 0 })
        out.push(ring(c.at, r + 0.4 * font, 0.3 * font))
      }
    }
  }
  for aid in m.aids {
    if aid.id in ids {
      if "line" in aid { if wanted(false) { out.push(stroke-line(aid.line.at(0), aid.line.at(1), 4)) } }
      else if "at" in aid { if wanted(true) { out.push(ring(aid.at, 0.72 * font, 0.3 * font)) } }
    }
  }
  if wanted(false) {
    for dim in m.dimensions {
      if dim.id in ids {
        if "line" in dim { out.push(stroke-line(dim.line.at(0), dim.line.at(1), 4)) }
        else if "centre" in dim { out.push(disc(dim.centre, 6)) }
      }
    }
  }
  if out.len() == 0 { "" } else { out.join("") }
}

/// Displays a detail schema drawn in Woodcore's «Schémas» tab: the pieces, the fastener markers, the construction aids that were left shown, and the dimensions. It is a drawing and nothing else, like a static model -- no resistance, no polar moment is computed anywhere behind it; a *Connecteurs* or *Moments polaires* calculation names a schema and checks off which of its markers belong to it.
///
/// ```typ
/// #show-schema("VU-Skizze")
/// ```
///
/// ```typ
/// #show-schema("VU-Skizze", width: 60%, highlight: "E1")
/// ```
/// - schema (str): the schema's id, as saved in Woodcore. An unknown id fails listing the valid ones.
/// - width (relative, length): the width the figure is printed at, 100% of the text width by default; one taller than it is wide is kept within three quarters of the page's height.
/// - highlight (str, array, none): the part(s) to put a halo under, by id -- an element, a connector marker, a shown aid or a dimension, as the schema's own list names them.
/// - aids (bool): true prints the construction aids ticked «visible» in the Schémas tab -- a point or a centre is by default, a construction line only once ticked; false leaves them all out, for a figure that wants the detail alone.
/// - caption (content, str, none, auto): auto names the schema; none prints the figure without a figure around it; anything else replaces the caption.
/// -> content
#let show-schema(schema, width: 100%, highlight: none, aids: true, caption: auto) = context {
  let schemas = load-schemas().schemas
  assert(type(schema) == str and schema in schemas,
    message: "show-schema: no schema " + repr(schema) + " -- " + (if schemas.len() == 0 { "none saved yet (draw one in Woodcore's Schémas tab)" } else { "valid schemas: " + schemas.keys().join(", ") }))
  let m = schemas.at(schema)
  let marked = if highlight == none { () } else if type(highlight) == str { (highlight,) } else { highlight }
  for id in marked {
    assert(type(id) == str and id in m.labels,
      message: "show-schema: schema '" + schema + "' has no " + repr(id) + " -- it carries " + (if m.labels.len() == 0 { "nothing" } else { m.labels.join(", ") }))
  }
  // The figure of the report's language: a connector marker's kind, and any legend the drawing carries, may be a word (docs/typst/language.md §4bis), so the frame travels with the file rather than standing beside all three.
  let fig = m.figures.at(report-lang())
  let figure-svg = read("../data/" + fig.file)
  if not aids {
    figure-svg = figure-svg.replace(regex("(?s)<!-- aids -->.*?<!-- /aids -->"), "")
  }
  if marked.len() > 0 {
    // A point's ring over the pieces, at the marker the figure keeps for it; a figure exported before v0.87 has none, and takes every halo where it always did (schema-halo).
    if figure-svg.contains("<!-- highlight-points -->") {
      figure-svg = figure-svg
        .replace("<!-- highlight -->", schema-halo(m, marked, points: false))
        .replace("<!-- highlight-points -->", schema-halo(m, marked, points: true))
    } else {
      figure-svg = figure-svg.replace("<!-- highlight -->", schema-halo(m, marked))
    }
  }
  layout(size => {
    let full = if type(width) == length { width } else if type(width) == ratio { width * size.width } else { width.ratio * size.width + width.length }
    let s = full / fig.view.w
    if size.height > 0pt and size.height < 100000pt {
      s = calc.min(s, 0.75 * size.height / fig.view.h)
    }
    let body = image(bytes(figure-svg), format: "svg", width: fig.view.w * s, height: fig.view.h * s, fit: "stretch")
    if caption == none {
      body
    } else {
      figure(
        body,
        caption: if caption != auto { caption } else {
          [#t-str("schema.caption", id: schema)#if m.label != "" [#colon-str() #m.label]]
        },
      )
    }
  })
}

// --- Annexes (docs/domain/annexes.md §3.3undevicies, v0.115) -------------------------
// The documents a report draws on from outside -- a FEM program's print report first -- and the excerpts it shows of them: a diagram, a table, taken from one page of a source. Nothing here computes: an excerpt is a picture of another program's calculation. The export has already found each excerpt again in its source's current version, by the bookmark it is anchored on, and written it as a one-page PDF cropped to its frame (calc/domains/annex.py) -- Typst sets that page at the origin, since it draws a page made of clipped image tiles wrongly as soon as it is placed anywhere else.
//
// An excerpt and the annex page it comes from are linked both ways, by where each one lands rather than by a label: a label written twice is an error in Typst, and an excerpt may be shown twice. Each leaves a `metadata` behind it -- `<woodcore-extract>` carrying its id, `<woodcore-annex-page>` carrying its source and page -- and the other end asks `query` for it and links to its location, where there is one. An excerpt shown in a report that prints no annexes is therefore simply not a link.

#let load-annexes() = json("../data/annexes.json")

// The frame an annex page draws around the region an excerpt shows, and the tag beside it: a colour of its own, which is neither the orange of a value written over nor the yellow of a highlight.
#let annex-frame-colour = rgb("#c2410c")

/// Every excerpt of the project's annexes, in file-name order -- what Woodcore's «Annexes» tab calls «Extraits». Data access, not a display function: `for id in extract-ids() { show-extract(id) }`.
///
/// ```typ
/// #extract-ids()
/// ```
///
/// ```typ
/// #for id in extract-ids() {
///   show-extract(id, width: 60%)
/// }
/// ```
///
/// -> array
#let extract-ids() = load-annexes().excerpts.keys()

/// Every source of the project's annexes -- the documents copied into Woodcore's «Annexes» tab, a print report, an ETA -- in file-name order, which is the order `show-annexes` letters them A, B, C in. Data access, not a display function.
///
/// ```typ
/// #annex-ids()
/// ```
///
/// ```typ
/// #for id in annex-ids() [ #id \ ]
/// ```
///
/// -> array
#let annex-ids() = load-annexes().sources.keys()

/// Displays an excerpt of an annex: the region of one page of a source that Woodcore's «Annexes» tab framed -- a diagram of internal forces, a table of results -- as a numbered figure, at the source's own vector quality. It is found again in every new version of the source by the bookmark of its title, so a print report printed again with more pages and renumbered chapters is followed; one that cannot be found stops the report, naming the excerpt and why (the engineer's choice: a diagram that is not the right one is worse than no report). Clicking the excerpt leads to the page it is taken from in the annexes, where `show-annexes` frames it and links back. There are no levels: an excerpt is a picture, printed whole or not at all.
///
/// ```typ
/// #show-extract("CO1-My")
/// ```
///
/// ```typ
/// #show-extract("CO1-My", width: 70%, caption: [Biegemomente unter CO1])
/// ```
/// - excerpt (str): the excerpt's id, as Woodcore's «Annexes» tab saved it. An unknown id fails listing the valid ones; one the export could not find in its source fails with the reason.
/// - width (relative, length): the width it is printed at, 100% of the text width by default; its height follows the frame's own proportions.
/// - caption (content, str, none, auto): auto names the source and its page -- «Auszug aus Rapport RFEM, S. 24»; none prints the excerpt without a figure around it; anything else replaces the caption.
/// -> content
#let show-extract(excerpt, width: 100%, caption: auto) = {
  let annexes = load-annexes()
  let excerpts = annexes.excerpts
  assert(type(excerpt) == str and excerpt in excerpts,
    message: "show-extract: no excerpt " + repr(excerpt) + " -- " + (if excerpts.len() == 0 { "none saved yet (frame one in Woodcore's Annexes tab)" } else { "valid excerpts: " + excerpts.keys().join(", ") }))
  let e = excerpts.at(excerpt)
  if not e.resolved {
    panic("show-extract: the excerpt " + repr(excerpt) + " cannot be printed -- " + e.reason)
  }
  let source = annexes.sources.at(e.source, default: (name: e.source))
  let name = if source.name != "" { source.name } else { e.source }
  [#metadata((id: excerpt, source: e.source, page: e.page))<woodcore-extract>]
  context {
    let body = image("../data/" + e.file, width: width)
    // the annex page this excerpt comes from, where the report prints one: the whole picture is the link
    let target = query(<woodcore-annex-page>).filter(m => m.value.source == e.source and m.value.page == e.page)
    let shown = if target.len() > 0 { link(target.first().location(), body) } else { body }
    if caption == none {
      shown
    } else {
      figure(
        shown,
        kind: image,
        caption: if caption != auto { caption } else { t-str("annex.caption", source: name, page: str(e.page)) },
      )
    }
  }
}

// The letter of the n-th annex, from 0: A ... Z, then AA, AB ...
#let annex-letter(n) = {
  let letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  if n < 26 { letters.at(n) } else { letters.at(calc.div-euclid(n, 26) - 1) + letters.at(calc.rem(n, 26)) }
}

/// Prints the report's annexes: for every source Woodcore's «Annexes» tab holds, a cover page «Anhang A — its name», then the pages it carries, **whole and at their own size**, without the report's header or page number over them. Which pages is the source's own choice in the tab: the pages an excerpt the report shows is taken from (the default), every page, or none. On each page the region every excerpt shows is framed, and the frame links back to the excerpt; the excerpt links here. The sources are lettered A, B, C in file-name order.
///
/// Its examples are shown and not rendered: every page of a source is a page of its own, and a documentation page is one picture. The tests compile its annexes on a project of their own (tests/test_annex.py).
///
/// ```typ-dry
/// #show-extract("CO1-My", width: 50%)
/// #show-annexes()
/// ```
///
/// ```typ-dry
/// #show-annexes(heading: none)
/// ```
/// - heading (int, none): the level each annex's name is set as a heading at, so it stands in the outline -- 2 by default, under the engineer's own «= Anhänge»; none sets it in bold on its cover page instead and keeps the outline the engineer's.
/// -> content
#let show-annexes(heading: 2) = {
  assert(heading == none or (type(heading) == int and heading >= 1),
    message: "show-annexes: heading: is none (the name set in bold) or the level of a heading, got " + repr(heading))
  let annexes = load-annexes()
  context {
    let shown = query(<woodcore-extract>).map(m => m.value.id)
    let letter = 0
    for (sid, source) in annexes.sources {
      let annex = source.annex
      if annex == none or source.mode == "none" { continue }
      let mine = source.excerpts.filter(id => id in annexes.excerpts and annexes.excerpts.at(id).resolved)
      let pages = if source.mode == "all" { annex.pages } else {
        annex.pages.filter(p => mine.any(id => id in shown and annexes.excerpts.at(id).page == p))
      }
      if pages.len() == 0 { continue }
      let name = if source.name != "" { source.name } else { sid }
      let title = t-str("annex.letter", letter: annex-letter(letter)) + " — " + name
      letter += 1
      // The first cover stands under the engineer's own «= Anhänge», which Sections/009 opens on a page of its own; every later one opens a page. Each page of a source is a page of its own anyway (`page` below).
      if letter > 1 { pagebreak(weak: true) }
      if heading == none {
        block(below: 1em, text(weight: "bold", size: 1.2em, title))
      } else {
        std.heading(level: heading, title)
      }
      if source.label != "" { par(source.label) }
      par(t-str("annex.pages", pages: pages.map(str).join(", ")))
      for p in pages {
        let i = annex.pages.position(q => q == p)
        let (w, h) = annex.sizes.at(i)
        page(width: w * 1pt, height: h * 1pt, margin: 0pt, header: none, footer: none, {
          [#metadata((source: sid, page: p))<woodcore-annex-page>]
          place(top + left, image("../data/" + annex.file, page: i + 1, width: w * 1pt, height: h * 1pt))
          for id in mine {
            let e = annexes.excerpts.at(id)
            if e.page != p or not (id in shown) { continue }
            let (x, y, fw, fh) = e.rect
            let back = query(<woodcore-extract>).filter(m => m.value.id == id)
            let frame = rect(width: fw * 1pt, height: fh * 1pt, stroke: 1.5pt + annex-frame-colour)
            let tag = box(fill: annex-frame-colour, inset: (x: 3pt, y: 1.5pt), text(size: 7pt, fill: white, id))
            place(top + left, dx: x * 1pt, dy: y * 1pt, if back.len() > 0 { link(back.first().location(), frame) } else { frame })
            place(top + left, dx: x * 1pt, dy: calc.max(0, y - 11) * 1pt, if back.len() > 0 { link(back.first().location(), tag) } else { tag })
          }
        })
      }
    }
  }
}

// --- Calculation block (docs/typst/report-engine.md §5) ------------------------------
// The report-side unit of work: a group of calculations that all concern the same position(s). Attribution runs block -> position and is a pure presentation concern, exactly like axes -- declaring a position here puts nothing onto that position's data, and a load's show-input may sit inside a block without any of this creating a position<->load link (sections 7-8).

/// Groups calculations that all concern the same position(s), under a header showing each position's descriptive summary, inside a visual frame that ties everything in the body to those positions.
///
/// ```typ
/// #calc-block("T001", title: "Nachweis Dachträger", axes: "Achse 3 / Achse C")[
///   Der Träger wird auf Biegung nachgewiesen.
/// ]
/// ```
///
/// ```typ
/// #calc-block(
///   ("S001", "S002"),
///   title: "Stützen des Pavillons",
///   axes: ("Achse 1 / Achse A", "Achse 2 / Achse A"),
///   description: true,
/// )[
///   Beide Stützen tragen dieselbe Last.
/// ]
/// ```
///
/// Every show-calc/show-check/show-input call in the body that reads a *position* is checked against the declared positions, so a calculation cannot silently end up under the wrong position's header. A call that reads a calculation domain's sheet instead is not checked: a load belongs to no position (section 8), so it may sit in any block without that creating a link. Blocks may nest.
/// - positions (str, array): one position id ("T001") or several (("T001", "T002")) that this group of calculations concerns.
/// - title (str, content, none): optional heading for the block, e.g. "Berechnung von Schneelast".
/// - axes (str, array, none): display-only plan axes (section 5). One string applies to every declared position; an array supplies one per position, in the same order as `positions`.
/// - description (bool): false (the default) heads the block with each position's summary line alone -- the line `#member` prints at level 1 --; true also prints each position's description text after it.
/// - level (int, auto): checked, and otherwise unused: the header's summary lines print the same at every level, and the body's own calls resolve their level independently. auto = the global report level.
/// - plan (str, auto, none): the position plan shown in the header, under the summaries (section 3.3sexies): auto = every plan the block's positions are drawn on, each as a detail around them with them highlighted; a plan id = that plan, the block's positions highlighted on it; none (the default) = no plan.
/// - body (content): the calculations, prose, and figures of the block.
/// -> content
#let calc-block(positions, title: none, axes: none, description: false, level: auto, plan: none, body) = {
  let ids = if type(positions) == str { (positions,) } else { positions }
  assert(ids.len() > 0,
    message: "calc-block: needs at least one position id")
  assert(level == auto or level in (1, 2, 3),
    message: "calc-block: invalid level " + repr(level) + " -- use auto, 1, 2, or 3")
  assert(type(description) == bool,
    message: "calc-block: description must be true or false, got " + repr(description))
  for id in ids {
    if not (type(id) == str and id in known-position-ids()) { panic(position-refusal("calc-block", id)) }
  }
  // the plans shown in the header, each with the block's positions it carries -- a plan named by hand may carry none of them, and is then shown whole
  let shown = if plan == none { () } else if plan == auto {
    ids.map(id => plans-of(id)).join().dedup()
  } else if type(plan) == str { (plan,) } else { plan }
  let plan-views = shown.map(pid => {
    let plans = load-plans().plans
    assert(pid in plans,
      message: "calc-block: no plan " + repr(pid) + " -- " + (if plans.len() == 0 { "none saved yet" } else { "valid plans: " + plans.keys().join(", ") }))
    let marked = ids.filter(id => id in plans.at(pid).labels)
    if marked.len() > 0 {
      show-plan(pid, highlight: marked, detail: true, legend: false, dimensions: false, scale-bar: false, caption: none)
    } else {
      show-plan(pid, legend: false, dimensions: false, scale-bar: false, caption: none)
    }
  })
  let axes-list = if axes == none {
    ids.map(_ => none)
  } else if type(axes) == str {
    ids.map(_ => axes)
  } else {
    axes
  }
  assert(axes-list.len() == ids.len(),
    message: "calc-block: got " + str(axes-list.len()) + " axes for "
      + str(ids.len()) + " positions -- pass one string for all of them, or "
      + "one entry per position in the same order")

  block-scope.update(stack => stack + (ids,))
  block(
    width: 100%,
    breakable: true,
    inset: (left: 0.8em, top: 0.6em, bottom: 0.6em, right: 0em),
    stroke: (left: 1.5pt + luma(45%)),
    {
      if title != none {
        block(below: 0.45em, text(weight: "bold", title))
      }
      for (id, ax) in ids.zip(axes-list) {
        block(below: 0.3em, position-line(id, description: description, axes: ax))
      }
      for view in plan-views {
        block(above: 0.5em, below: 0.3em, breakable: false, view)
      }
      block(above: 0.55em, below: 0.75em, line(length: 100%, stroke: 0.4pt + luma(70%)))
      body
    },
  )
  block-scope.update(stack => stack.slice(0, -1))
}

// --- Input variable display, with description/choices (docs/typst/report-engine.md §9)
// The one call that reaches for a single named value. show-calc renders a whole calculation and never takes a var name; show-input is how a report pulls one intermediate value out of it and sets it in its own prose.

// One var as `symbol = value unit`, with its description and choices as a footnote when `notes` is true. Shared by show-input and show-calc so a var is formatted identically wherever it appears.
//
// One footnote, not two: a var carrying both a description and a choices list used to print two markers side by side, which read as a single two-digit number rather than as two references.
#let var-row(v, notes: false) = {
  let desc = get-description(v)
  let choices = get-choices(v)
  let note = if not notes or (desc == none and choices == none) { none } else {
    [
      #if desc != none [#render-prose(tl-str(desc))]
      #if choices != none [
        #if desc != none [ ]
        // A choice goes through the glossary like every other string the data carries: its value is a number on most vars, but a word on the ones whose value is text -- and where that word is the norm's own (a Geländekategorie of SIA 261's Tabelle 4), the glossary carries it and it follows the report's language. One the workbook alone names passes through untouched.
        #for c in choices [#render-symbol(v) = #render-prose(tl-str(c.value))#colon-str() #render-prose(tl-str(c.desc)) \ ]
      ]
    ]
  }
  // Set on one line, with no space before the footnote marker: a multi-line
  // markup block would leave a trailing space inside the content, which shows
  // up as a gap the moment two of these rows are joined by a semicolon.
  (
    [#render-symbol(v) = #fmt-value(v)#if note != none [#h(0.2em)#footnote(note)]],
    v,
  )
}

/// Displays one input variable as `symbol = value unit`, with its `description`/`choices` (section 3.3) as a footnote at level >= 2.
///
/// ```typ
/// #show-input("snow-load", "SL", "h_ref")
/// ```
///
/// ```typ
/// #show-input("snow-load", "SL", "ce", level: 2)
/// ```
///
/// - domain (str): a calculation domain ("snow-load"), or a domain of a position ("bending"). An unknown domain raises an assertion error listing the valid ones.
/// - instance (str): the workbook sheet the domain was read from ("SL-Dach1"), or a position id ("T001") for a domain carried by a position. An unknown instance raises an assertion error listing the valid ones. A position, unlike a sheet, is scope-checked against the enclosing calc-block (section 5).
/// - name (str): var name within that instance's `vars` (section 3.1/3.3), e.g. "h_ref". An unknown name raises an assertion error listing the valid var names.
/// - level (int, auto): 1 = value only, 2+ = also show `description`/`choices` as a footnote. auto = use the global report level (the "report-level" state, section 4).
/// -> content
#let show-input(domain, instance, name, level: auto) = context {
  assert(level == auto or level in (1, 2, 3),
    message: "show-input: invalid level " + repr(level) + " -- use auto, 1, 2, or 3")
  let eff-level = resolve-level(level)

  let vars = resolve-source("show-input", domain, instance).vars
  assert(name in vars,
    message: "show-input: unknown var '" + name + "' in " + source-label(domain, instance) + " -- valid vars: " + vars.keys().join(", "))

  annotated-rows((var-row(vars.at(name), notes: eff-level >= 2),))
}

// `inline-value` stood here until v0.80: one var of the export, inline, as `symbol = value unit`. It is `val("s_k", domain: ("snow-load", "SL"), type: "expression")` now -- the same lookup, in the one command that prints a value (section 13). `show-input` keeps the other half of that pair: the *block* row, whose citation stands in the right-hand column, which inline content cannot reach.

// --- One-off calculations done in Typst (docs/project/purpose.md §1) ------------
// There is deliberately no show-* function for these. An arrangement of already-traced values that the data does not carry -- a quick product, a value read off two sheets -- is written as an ordinary Typst equation, with the numbers pulled from the data rather than retyped:
//
//   #let g-k = var-of("dead-load", "EL+AL-Dach1.mitPV", "gk_ak_gew")
//   #let s-k = var-of("snow-load", "SL-Dach1", "s_k")
//   #let x = get-value(g-k) * get-value(s-k)
// $ x = #val(g-k) dot #val(s-k) = #val(x, unit: "kN/m²") $
//
// val takes a var object, a number, or the name of a variable of the report or of the export, so the same call serves a value read from the data and one computed here -- and where it is handed a var object the unit comes with it, never retyped (section 2, rule 1).
//
// val is what keeps such an equation consistent with the rest of the report: it prints at the document's own number-digits setting, so a hand-written formula and a generated one round alike.
//
// ⚠️ A value computed this way is NOT traced: no `source`, it never reaches data/, it is not validated, and it is not catalogued in docs/typst-reference.xlsx. For a one-off only -- anything a checker must be able to re-derive belongs in a Python domain, and load combinations belong in calc/domains/combinations.py without exception (section 3.5).

// --- Tabular detail (docs/domain/calculation-domains.md §3.3) -------------------------------
// An instance may carry `tables`, each in either of two shapes, and the data says which. The dead load's layer build-up is the *working*: shown to a checker (level 3) and set *above* the values it explains, its `totals` rows being the sums the lines under it carry forward. The wind load's global forces are the *answer*: shown from level 1 and set below the values that lead to it, with the formula it evaluates in letters above it. `level` and `place` carry that difference, and default to the first shape -- the one this block was written for. So one calculation may hold both: the wind load's local forces are working again, a level-3 table set after its level-1 answer. Values arrive as numbers, or as the names of vars, and are formatted here like every other value.

// A column declares what it holds, never how wide it should be (section 3.3) -- with **one exception since v0.117: the list of the positions**, whose columns may carry an optional `width` and whose table sets `fit` (fit-widths below; docs/decisions.md) --, so the widths are decided here -- and one declaration settles them all: the `wide` column takes the leftover width, every other column its natural one.
//
// Which is not what happens if they are all left to size themselves. A table of auto columns that does not fit the text width is shrunk proportionally, so the numeric columns keep room they have no use for while the material names wrap three deep; giving one column `1fr` makes the others exactly as wide as their own header and hands the rest to the text that needs it.
#let column-width(kind) = {
  if kind == "wide" { 1fr } else { auto }
}

// And a column is aligned by what it holds too, which is what a table without vertical rules needs: a number read from the right, so the digits line up down the column and a long value cannot be mistaken for a short one; a symbol centred in its own column; a word -- and a `wide` column is the material names -- read from the left like the text around it. A header follows its column, so a numeric heading stands over its own last digit.
#let column-align(kind) = {
  if kind == "number" or kind == "value" { right } else if kind == "math" { center } else { left }
}

// A column's header, its unit set on a second line: "Dicke" over "[m]". The unit is carried as its own field rather than typed into the label (section 3.3), so the break falls where the data says the name ends -- and a column of two-decimal numbers ends up as narrow as its own name instead of as wide as "Dicke [m]". The brackets are display, like every unit's.
//
// A column headed by a *symbol* rather than by a word carries it as Typst math source in `label_math` (q_k, Q_k over the two columns of SIA 261's Tabelle 8), and is set as real math here -- its `label` staying the same name in plain text, for the catalog window and anything else that reads the data as text.
#let column-header(c) = {
  let unit = c.at("unit", default: "")
  let name = if "label_math" in c { eval(c.label_math, mode: "math") } else if type(c.label) == str { [#tl-str(c.label)] } else { [#c.label] }
  // A column the group line above it already names ("in Faserrichtung" over a distance and its multiple of d) carries no label of its own, and its unit then stands alone rather than under an empty line.
  let unnamed = "label_math" not in c and c.label == ""
  if unit == "" { name } else if unnamed { [#("[" + unit + "]")] } else { name + linebreak() + [#("[" + unit + "]")] }
}

// A `math` cell is Typst math source, evaluated like a var's symbol (section 6bis): it is how the build-up prints the g_k a layer counts towards instead of the sheet's own "gk". A `value` cell names a var of the same instance instead of repeating its number, so the table cannot drift from the value it shows (section 2, rule 1) -- and it is set bold where that var is one of the calculation's results, bold marking the answer in a table exactly as it does in a formula. Every other cell goes through fmt, so a number in a table rounds exactly like the same number in a formula.
#let table-cell(kind, cell, vars: (:), results: ()) = {
  if kind == "math" and type(cell) == str and cell != "" {
    eval(cell, mode: "math")
  } else if kind == "value" and type(cell) == str and cell != "" {
    assert(cell in vars,
      message: "render-table: a table cell names var '" + cell + "', which this calculation does not declare -- valid vars: " + vars.keys().join(", "))
    let printed = fmt-number(get-value(vars.at(cell)), "")
    if cell in results { text(weight: "bold", printed) } else { printed }
  } else {
    // A text cell is a word of the table -- "Wand A", "Total" -- or a material's name out of the workbook. The glossary decides which: it carries the first and not the second.
    // One carrying a dollar is prose with its symbols between dollars, set as math (render-prose, section 4bis): a connector's «$K_("ser","Verb")$» and «$7 d$» (v0.77). A material's name carries none, and an unpaired dollar is left as written.
    // A number is printed by fmt-number, its sign a minus; a word goes through render-prose, which sets a sign the same way where the word carries one («-5 °C») and leaves every other hyphen as typed.
    // ⚠️ **Content passes through untouched** (v0.99), as a column's own `label` already does: it is how a caller says «these are not the engine's words, do not look them up». The journal's label and its two descriptions are free text the engineer typed, and free text is the one case where the glossary's own rule -- translate it if the glossary carries it -- can go wrong: a template matches on the literal segments around its holes, so a revision labelled «Element 3 ergänzt» matches «Element {n}» and a French report would print «élément 3 ergänzt» (section 3.3terdecies; the risk section 14 records for `tl-of`). A string still goes through the glossary, which is what every table read from the data needs.
    if type(cell) == content { cell } else if type(cell) == str { context render-prose(tl-str(cell)) } else { fmt-number(cell, "") }
  }
}

// Every var a table prints in its own `value` cells. show-calc reads it to leave those vars off rows of their own -- the same rule that keeps an intermediate step's operands from being set out twice, applied to a table.
#let table-vars(tbl) = {
  let kinds = tbl.columns.map(c => c.kind)
  let names = ()
  for row in tbl.rows + tbl.at("totals", default: ()) {
    for pair in row.zip(kinds) {
      if pair.at(1) == "value" and type(pair.at(0)) == str and pair.at(0) != "" {
        names.push(pair.at(0))
      }
    }
  }
  names
}

// A column may name a heading spanning it and the consecutive columns sharing it -- "Bezugsflaeche" over b*h, d*h and d*b -- set on a header line of its own above the column names. The same idea as a var's `group`: what the source states together is printed together. A column with no group leaves that line empty above it, so it says only what the data says.
//
// The runs themselves are worked out once, as (start, end, label) with `end` exclusive, because they are read twice over: once for the spanning cell that names a run, and once for the rule drawn under that name -- which is what says how far the name reaches, now that no vertical rule does.
#let group-spans(columns) = {
  let spans = ()
  let i = 0
  while i < columns.len() {
    let group = columns.at(i).at("group", default: none)
    let span = 1
    if group != none {
      while i + span < columns.len() and columns.at(i + span).at("group", default: none) == group {
        span += 1
      }
      spans.push((start: i, end: i + span, label: group))
    }
    i += span
  }
  spans
}

#let group-header-cells(columns) = {
  let spans = group-spans(columns)
  let cells = ()
  let i = 0
  while i < columns.len() {
    let here = spans.find(s => s.start == i)
    if here == none {
      cells.push([])
      i += 1
    } else {
      // A group over ONE column names that column rather than spanning a run of them -- a connector's
      // «$d$ = 10 mm» over the distances of Tabelle 24, every one of which is a multiple of it. It is
      // set where its column is set, and takes no rule under it (group-rules): there is nothing for a
      // rule to say about how far a name over a single column reaches. Its label may carry math between
      // dollars, like every other word the data hands the display layer (render-prose, section 4bis).
      let span = here.end - here.start
      cells.push(table.cell(colspan: span, align: if span == 1 { column-align(columns.at(i).kind) } else { center },
                            text(weight: "bold", render-prose(tl-str(here.label)))))
      i = here.end
    }
  }
  cells
}

// `bold-rows` sets whole body rows bold by their index, `bold-columns` whole columns -- the most stressed fastener and the resultants in show-polar-moment's table, bold for the same reason a result is. No table read from the data uses them.
//
// A table read from the data marks its own rows instead, with the `highlight` it may carry (section 3.3septies): the one row a calculation actually reads out of a norm table -- its category in SIA 261's Tabelle 8 -- set bold on a tinted ground, so the value quoted above the table can be found in it at a glance. Which row that is, is the data's to say; the colour is here, in one place.
//
// A table is centred in the space it has (v0.32): the calculation's own column, left of the citations, when it fits there -- so it sits under the formulas it goes with -- and the full width when it does not, or when it has a `wide` column that takes whatever width there is (the dead load's build-up, which is therefore laid out as before). Its title and its note keep to the table's width. Inside `layout` the table sits in breakable blocks, never in a box, so a long one still breaks across pages with its header repeated.
//
// Its cells, its headers and its title are set at the text's own size, whatever the document sets it to -- a table is read like the lines around it, not as small print. Only its note stays small, like the citations. It keeps `table-spacing` clear of the text before and after it, more than a line keeps from the next (annotated-rows' 1em), so that it reads as a block of its own; `above` narrows that where the table opens a calculation right under its heading, which it belongs to.
#let table-spacing = 1.6em
#let table-highlight = rgb("#fff2b2")

// A table is set the way a printed norm and a paper set one, and there are only ever three rules in it: a thick one above the headings and a thick one under the last row, closing the table, and a thin one under the headings, under a group's name and above the totals, separating one kind of row from another. Nothing else is drawn -- no vertical rule, no box around a cell, no grid. What tells one column from the next is the space between them and what each one holds (column-align), which is what makes a table of numbers readable down its columns rather than cell by cell; a grid makes every cell equally loud, and a calculation table is read for its columns.
#let rule-thick = 1pt
#let rule-thin = 0.5pt

// The rule under a group's name, spanning exactly the columns that name covers -- and it is what now says how far a group reaches, a vertical rule no longer being there to say it. Placed inside the header, so it is repeated with it on a table that breaks.
#let group-rules(columns) = group-spans(columns).filter(s => s.end - s.start > 1).map(s => table.hline(y: 1, start: s.start, end: s.end, stroke: rule-thin))

// A table's title is its caption, numbered as a figure is: «Tabelle 1: Allgemeine Beschreibung», set as the document sets «Abbildung 1: …» -- the same counter rules, the same supplement in the document's language, the same separator and whatever `show figure.caption` the project's `config.typ` states -- above the table rather than under it, upright and centred over the table (the engineer, v0.114: «le titre doit être numéroté … centré par rapport au tableau, pas en italique … comme le numéro des images, sauf au-dessus»). A real `figure(kind: table)`, so a list of the tables (`outline(target: figure.where(kind: table))`) finds every one of them. `area` is the width the table is centred in: the caption is centred in it too, and so over the table, and may take all of it rather than wrap to a narrow table's own width. The body is left as it is laid out, in one full-width block, so the figure's own centring moves nothing. A figure is not breakable by default, and a long table must still break, its header repeated -- whether it may is decided by the block around it, as before. A plate of figures with no grid (a connector's Figur 45) is a figure and not a table: it is numbered «Abbildung», its caption under it as every picture's is (`kind: image`).
#let table-figure(title, area, body, kind: table) = {
  show figure: set block(breakable: true)
  show figure.caption: c => block(width: 100%, align(left, block(width: area, align(center, c))))
  figure(kind: kind, gap: 0.5em, caption: figure.caption(position: if kind == table { top } else { bottom }, title), block(width: 100%, align(left, body)))
}

// --- A table that keeps to the page (v0.117, docs/domain/calculation-domains.md §3.3) -------------------------
// A table whose `tbl` carries `fit: true` is laid out within the width it has, whatever its cells hold -- the list of the positions, the first (the engineer, v0.117: «le tableau ne doit pas dépasser dans la marge de droite»). Left to Typst, its auto columns keep the least width their longest unbreakable word takes, and a description column that was to take the leftover got none: its last column began 5pt past the text area on a project of long values. Here every column is given its width, from what is in it, and the sum is never more than the area.
//
// A column may state `width`, a length or a percentage of the area (a data table never does: its columns say what they hold and never how wide, §3.3). The others take what their cells and their heading ask for -- their natural width, a heading counting at most `fit-heading-cap` --, and where the area is too small for all of them the widest are narrowed to one common width, never below what a column's least breakable piece takes (its longest word, a heading's up to the cap), so a word is not cut while any other column can still give. A width that is left over goes to the `wide` column. Where even the least of every column does not fit the area, the widest are narrowed to one common width -- the table keeps to the page and a long word is cut, the short ones staying whole --, and where the widths that were stated leave the others less than `fit-floor` they are reduced, and `reduced` says so: the table prints it (`table.width_over`).
#let fit-pad = 10pt          // the inset (x: 5pt) either side of a cell
#let fit-heading-cap = 8em   // the most a heading asks for on one line
#let fit-floor = 2em         // the least any column is narrowed to
#let table-warning = rgb("#b35c00")   // the orange of override-colour (further down), which a table cannot name from here

// In a context (it measures). `columns` are the table's column declarations, `headers` their headings as set, `cells` the rows of cells as set, `avail` the area's width.
#let fit-widths(columns, headers, cells, avail) = {
  let n = columns.len()
  let cap = fit-heading-cap.to-absolute()
  let least = fit-floor.to-absolute() + fit-pad
  let given = columns.map(c => {
    let w = c.at("width", default: none)
    if w == none { none } else if type(w) == ratio { avail * w } else { w.to-absolute() }
  })
  // what a column asks for at most -- one line of its widest cell, its heading up to the cap -- and at least -- the widest piece it cannot break, a word, its heading up to the cap
  let head = range(n).map(i => calc.min(measure(headers.at(i)).width, cap) + fit-pad)
  let pref = range(n).map(i => calc.max(head.at(i), ..cells.map(row => measure(row.at(i)).width + fit-pad)))
  // a column whose widest cell is no longer than a heading may be is not cut, a short word is not hyphenated: only the longer ones give
  let floors = range(n).map(i => calc.max(least, head.at(i), calc.min(pref.at(i), cap + fit-pad), ..cells.map(row => measure(row.at(i), width: 0pt).width + fit-pad)))
  let free = range(n).filter(i => given.at(i) == none)
  let fixed-sum = given.filter(w => w != none).fold(0pt, (a, b) => a + b)
  let floor-sum = free.map(i => floors.at(i)).fold(0pt, (a, b) => a + b)
  let reduced = false
  let scale = 1.0
  // the widths that were stated win: the others are narrowed for them, down to the very least a column takes (`fit-floor`); only where they leave the others less than that are they reduced
  if fixed-sum > 0pt and fixed-sum + least * free.len() > avail {
    reduced = true
    scale = calc.max(avail - least * free.len(), avail * 0.2) / fixed-sum
  }
  let room = avail - fixed-sum * scale
  let widths = given.map(w => if w == none { 0pt } else { w * scale })
  if free.len() > 0 {
    let pref-sum = free.map(i => pref.at(i)).fold(0pt, (a, b) => a + b)
    if room < floor-sum {
      // not even the least of every column fits: the widest are narrowed to one common width, a long word -- a heading, «Festigkeitsklasse» -- being cut where it must, the short ones left whole
      let lo = 0pt
      let hi = floors.fold(0pt, calc.max)
      for _ in range(40) {
        let mid = (lo + hi) / 2
        let sum = free.map(i => calc.max(least, calc.min(floors.at(i), mid))).fold(0pt, (a, b) => a + b)
        if sum > room { hi = mid } else { lo = mid }
      }
      for i in free { widths.at(i) = calc.max(least, calc.min(floors.at(i), lo)) }
    } else if pref-sum <= room {
      for i in free { widths.at(i) = pref.at(i) }
      // what is left over goes to the wide column
      let wide = free.find(i => columns.at(i).kind == "wide")
      if wide != none { widths.at(wide) += room - pref-sum }
    } else {
      // the widest columns are narrowed to one common width, found by halving: every column takes the lesser of what it asks for and that width, and no less than its least
      let lo = 0pt
      let hi = pref.fold(0pt, calc.max)
      for _ in range(40) {
        let mid = (lo + hi) / 2
        let sum = free.map(i => calc.max(floors.at(i), calc.min(pref.at(i), mid))).fold(0pt, (a, b) => a + b)
        if sum > room { hi = mid } else { lo = mid }
      }
      for i in free { widths.at(i) = calc.max(floors.at(i), calc.min(pref.at(i), lo)) }
    }
  }
  // whatever was asked, the sum keeps to the area
  let total = widths.fold(0pt, (a, b) => a + b)
  if total > avail { widths = widths.map(w => w * (avail / total)) }
  (widths: widths, reduced: reduced)
}

#let render-table(tbl, vars: (:), results: (), bold-rows: (), bold-columns: (), above: auto) = block(
  above: if above == auto { table-spacing } else { above }, below: table-spacing, breakable: true,
  {
    // A title read from the data may carry its symbol between dollars -- «Hilfswert $k_beta$» -- set as math, where a bare «k_β» printed its underscore (v0.77).
    // A table with no title -- a key-value list of the documents, a table set inside another command's own heading -- is no figure and takes no number (table-figure).
    let titled = tbl.title not in (none, [], "")
    let title = if type(tbl.title) == str { render-prose(tl-str(tbl.title)) } else { tbl.title }
    // A table may state the formula it evaluates, for a calculation whose answer is a table of cases rather than one number (the global wind forces, one per reference area). It is set in letters above the table, its citation in the same right-hand column every other formula's sits in -- the table below it is that formula's numbers line. Its title then heads the formula, as before. The formula may be several, one row each (a fastener's two components and their resultant); a table built inside a calculation whose reference is cited once elsewhere carries no `norm`, and its formula no citation.
    let has-formula = "formula" in tbl
    let head = if has-formula {
      let lines = if type(tbl.formula) == array { tbl.formula } else { (tbl.formula,) }
      let cite = if "norm" in tbl { tbl } else { none }
      // A built-up formula -- a fraction, a root -- reaches well above and below the line box its text edges give it, and that box is what its row and every gap around it are measured against: at 11pt the ink of the superposition's fractions stood 5pt outside its row on either side, so the 1em between two formulas left 1pt of white, and the 0.4em under the last left 3pt before the table's own rule, which the superscript on a tall bracket then all but touched (the engineer, v0.97: «il n'y a pas assez d'espace dans le moment polaire entre F_i^* et le tableau»). The formulas of a head are therefore set to their ink (`top-edge`/`bottom-edge: "bounds"`, row-cell's own instrument, v0.87), and every gap in it -- under the title, between two formulas, above the table -- is then the white it says it is. It replaces the push that stood here, which moved the *first* formula down by how much taller than an ordinary line it was: the one side a push can reach, and measured against the line box rather than the ink.
      block(width: 100%, {
        set text(top-edge: "bounds", bottom-edge: "bounds")
        // the title is the figure's caption above this head (table-figure), no longer its first line
        annotated-rows(lines.enumerate().map(((i, f)) => (eval(f, mode: "math"), if i == 0 { cite } else { none })))
      })
      v(0.5em, weak: true)
    }
    let kinds = tbl.columns.map(c => c.kind)
    // A `tables` entry may carry **no grid at all** and be only its title, its note and its figures --
    // a connector's Figur 45, one line per thickness, whose numbers are written out as formulas above
    // it since v0.84 (docs/domain/calculation-domains.md §3.3, docs/domain/connectors.md §3.3nonies). It goes through this one function so that a
    // plate of figures carries its own `level` and its own `place` like every other table, rather than
    // needing a mechanism of its own.
    let plate = kinds.len() == 0
    let totals = tbl.at("totals", default: ())
    let has-groups = tbl.columns.any(c => "group" in c)
    let highlight = tbl.at("highlight", default: ())
    // The body starts under the column names, and under the group line above them where there is one -- `fill` is given the whole grid's rows, header included.
    let header-rows = if has-groups { 2 } else { 1 }
    // One row of cells, each rendered as its column says. `weight` sets the totals apart: they are the answer the rows above add up to, so they are read the way a bold result line is.
    let row-cells(row, weight) = row
      .zip(kinds)
      .enumerate()
      .map(((i, pair)) => text(weight: if i in bold-columns { "bold" } else { weight }, table-cell(pair.at(1), pair.at(0), vars: vars, results: results)))
    // A cell's words are set ragged, whatever the document justifies: a column is a few centimetres wide, and justified there a long value -- the norm's example beside a category of Nutzfläche, a material's name -- was stretched into a line of words with holes between them («behindert     oder    er-schwert», v0.87, `find`'s Wert column). Lines are broken where they were; only the stretch goes.
    // a row of a table that keeps to the page (`fit`) is not split between two pages
    let keep-whole(on) = c => if on { table.cell(breakable: false, c) } else { c }
    // a table that keeps to the page (`fit`) hyphenates what it holds, in the report's language: a word longer than its column would otherwise run out of its cell, and past the margin
    let make-body(col-widths, whole-rows) = if plate { none } else { set par(justify: false); set text(hyphenate: true) if whole-rows; table(
      columns: col-widths,
      stroke: none,
      // With no vertical rule between two columns, the space between them is what parts them, and 4pt either side of a number is not enough of it; the rules span that space, as a printed table's do.
      inset: (x: 5pt, y: 4pt),
      align: kinds.map(column-align),
      fill: (_, y) => if (y - header-rows) in highlight { table-highlight },
      // Marked as the table's header, so it is repeated at the top of every page the table breaks onto: a continued page of ten numeric columns without their headings would not say which opening a value belongs to. Both of its rules are placed *inside* it for the same reason -- an hline written outside the header is not repeated with it, and a continued page would carry its headings with nothing above or below them.
      table.header(
        table.hline(stroke: rule-thick),
        ..if has-groups { group-header-cells(tbl.columns) } else { () },
        ..if has-groups { group-rules(tbl.columns) } else { () },
        ..tbl.columns.map(c => text(weight: "bold", column-header(c))),
        table.hline(stroke: rule-thin),
      ),
      ..tbl.rows.enumerate().map(((i, r)) => row-cells(r, if i in bold-rows or i in highlight { "bold" } else { "regular" }).map(keep-whole(whole-rows))).flatten(),
      // The sums are the answer the rows above add up to, so a rule sets them apart -- the thin one that closes the headings, since both part one kind of row from another. It was heavier than every other rule while the table was a grid, to be seen at all among them; with no grid left it has nothing to be seen against.
      ..if totals.len() > 0 { (table.hline(stroke: rule-thin),) } else { () },
      ..totals.map(r => row-cells(r, "bold")).flatten(),
      table.hline(stroke: rule-thick),
    ) }
    let body = make-body(kinds.map(column-width), false)
    // A note read from the data is translated here, and its symbols set as math (render-prose); one built by a show-* function comes in already set in the report's language, and passes through -- the glossary holds German keys only.
    let note = {
      let n = tbl.at("note", default: none)
      // a list of sentences, each translated on its own (a term or a template), joined as one paragraph
      if type(n) == array { n.map(s => render-prose(tl-str(s))).join(" ") } else if type(n) == str { render-prose(tl-str(n)) } else { n }
    }
    let has-wide = kinds.contains("wide")
    layout(size => {
      // `fit`: the widths are worked out here, from what the cells hold, and the body is built with them (fit-widths)
      let fit = tbl.at("fit", default: false) and not plate
      let fitted = if fit {
        fit-widths(tbl.columns, tbl.columns.map(c => text(weight: "bold", column-header(c))),
          tbl.rows.enumerate().map(((i, r)) => row-cells(r, if i in bold-rows or i in highlight { "bold" } else { "regular" })), size.width)
      } else { none }
      let body = if fit { make-body(fitted.widths, true) } else { body }
      let beside-notes = size.width - note-column - note-gutter
      let natural = if fit { fitted.widths.fold(0pt, (a, b) => a + b) } else if has-wide or plate { size.width } else { measure(body).width }
      let full = has-wide or plate or fit or natural > beside-notes
      let area = if full { size.width } else { beside-notes }
      // a note kept to a narrow table's width is set ragged: justified, it would stretch its few words across the line
      set par(justify: false) if not full
      let whole = {
        head
        block(width: area, breakable: true, align(center, block(width: calc.min(natural, area), breakable: true, align(left, {
          if not plate { body }
          if note != none {
            v(0.25em, weak: true)
            text(size: 7.5pt, style: "italic", note)
          }
          if fit and fitted.reduced {
            v(0.25em, weak: true)
            text(size: 7.5pt, fill: table-warning, t-str("table.width_over"))
          }
        }))))
        // A table may carry the figures it is read off, set under it side by side, each named under it in the report's language -- a connector's k_beta table and SIA 265 Figur 45, one line per thickness (v0.77). A figure carries no word of its own, so one file serves every language.
        let figures = tbl.at("figures", default: ())
        if figures.len() > 0 {
          v(0.6em, weak: true)
          block(width: area, breakable: false, grid(
            columns: calc.min(figures.len(), 2) * (1fr,),
            column-gutter: 1.2em,
            row-gutter: 0.8em,
            ..figures.map(f => align(center, {
              image("../data/" + f.file, width: 100%)
              v(0.2em, weak: true)
              text(size: 8pt, tl-str(f.label) + " — " + tl-str(f.role))
            })),
          ))
        }
      }
      if titled { whole = table-figure(title, area, whole, kind: if plate { image } else { table }) }
      // A table shorter than a page is kept whole, its title and formula with it: where the rest of a page cannot take it, it moves to the next rather than leave its heading behind. Only a longer one breaks, its header repeated. `size.height` is the page's whole text height, wherever on it the table falls.
      block(breakable: measure(whole, width: size.width).height > size.height, whole)
    })
  },
)

// --- Formulas in letters, then in numbers (docs/typst/citations.md §10) ----------
// Every calculated value is printed twice over: the formula in letters, then the same formula with the numbers put in their place. The second line is *derived* from the first rather than authored beside it -- its operands are the step's own `uses` -- so a number can never drift out of sync with the symbol it stands in for, the way a hand-typed substitution would.

// The right-hand side of a formula. Splits on the first spaced " = ", which the assignment always is and a relational operator never is: ">= 0.9" has no space between its > and its =.
#let formula-rhs(formula) = {
  let i = formula.position(" = ")
  if i == none { formula } else { formula.slice(i + 3) }
}

// One value as it is written *inside* a formula: the bare number, the unit being carried by the result at the end of the line. A signed value loses a leading + and parenthesises a leading - , so "h_0 + Delta h" reads "438 + 200" and not "438 + +200"; a textual value is quoted so the line stays valid Typst math. Both of these build Typst math *source* that is eval'd, so they must return strings. fmt/fmt-value return content and cannot be concatenated into a source string; fmt-decimals is the string primitive underneath them, and reading number-digits here keeps a substituted formula rounding exactly like every other number in the report. `context` propagates from show-calc, which is where these are ultimately called from.
#let value-in-formula(v) = {
  let val = get-value(v)
  if type(val) == str {
    if val.starts-with("+") { val.slice(1) }
    else if val.starts-with("-") { "(" + val + ")" }
    else { "\"" + val + "\"" }
  } else {
    let s = fmt-decimals(val, number-digits.get())
    if val < 0 { "(" + s + ")" } else { s }
  }
}

// The string counterpart of fmt-value: "1.729 kN/m²" as source, not as content. It is set as a *quoted* word inside math, where a hyphen stays a hyphen, so a negative answer carries its minus sign already written (signed-text).
#let value-text(v) = {
  let value = get-value(v)
  let s = fmt-decimals(value, number-digits.get())
  if type(value) == int or type(value) == float { s = signed-text(s) }
  let unit = get-unit(v)
  if unit == "" { s } else { s + " " + unit }
}

// A step's formula with each operand replaced by its value. Longest symbol first, so a symbol that is the prefix of another (mu_1 of mu_11) cannot eat it. An operand the formula does not mention -- `abgleiten`, which selects the branch rather than appearing in it -- replaces nothing.
//
// ⚠️ A symbol made only of word characters is replaced on **word boundaries**, and that is not tidiness: a dowel's diameter carries the norm's own symbol `d`, and a plain replace rewrites the `d` of every `dot` in the formula, so `0.3 dot f_(u,k) dot d^2.6` came out as `0.3 12ot ...` and the line would not even evaluate. Longest-first does not help -- `dot` is not an operand, it is the multiplication sign. A symbol carrying anything else (`f_(h,1,k)`, `mu_11`, `q_(k,11)`) cannot be a substring of an operator name, so it keeps the plain replace and no pattern has to be escaped.
#let word-symbol = regex("^[A-Za-z0-9_]+$")
#let substituted-rhs(st, vars) = {
  let rhs = formula-rhs(st.formula)
  let ops = st.uses
    .filter(u => u in vars)
    .map(u => vars.at(u))
    .sorted(key: v => -get-symbol(v).len())
  for v in ops {
    let symbol = get-symbol(v)
    if symbol.match(word-symbol) != none {
      rhs = rhs.replace(regex("\b" + symbol + "\b"), value-in-formula(v))
    } else {
      rhs = rhs.replace(symbol, value-in-formula(v))
    }
  }
  rhs
}

// A formula stating a bound rather than an equality -- s_k's "... >= 0.9 kN/m²" -- cannot be closed with "= result": the line would read as a chain of two different relations, one of which is not what happened. Such a step keeps the compact "mit x = ..." note instead and prints its result on a row of its own.
#let is-bounded(formula) = formula.contains(regex("[<>]"))

// The line that carries the answer: `symbol = <the formula, in numbers> = result`, set bold. Falls back to `symbol = result` where there is no formula, or where none of the operands appear in it -- restating the letters line verbatim would read as a printing error.
//
// Where it carries the numbers it is a `formula-chain`, so that a line too wide for its row is stacked -- `symbol = <numbers>`, then `= result` under its `=` -- rather than run over the citation column (annotated-rows).
#let substituted-line(st, vars, bold: true) = {
  let res = vars.at(st.result)
  let value = "\"" + value-text(res) + "\""
  let wrap(x) = if bold { math.bold(x) } else { x }
  let subs = if "formula" in st { substituted-rhs(st, vars) } else { none }
  if subs == none or subs == formula-rhs(st.formula) {
    return wrap(eval(get-symbol(res) + " = " + value, mode: "math"))
  }
  let line = wrap(eval(get-symbol(res) + " = " + subs + " = " + value, mode: "math"))
  formula-chain(line, wrap(eval(get-symbol(res) + " = " + subs, mode: "math")), (value,),
    s => chain-line(get-symbol(res), "=", s, wrap: wrap))
}

// A step set on ONE row: its formula in letters, then the same formula in numbers, then the answer --
// `M_(u,k) = 0.3 dot f_(u,k) dot d^2.6 = 0.3 dot 510 dot 10^2.6 = 60910.397 Nmm`. The data asks for it
// (`inline`), because whether a formula is short enough to be read across one line is a property of the
// formula (docs/typst/api-conventions.md §10bis); the engineer asked for it on the chain of short formulas a dowel
// connection is made of, which took two lines each and ran a checking report over pages.
//
// Only the numbers and the answer are set bold where the step is an answer: bolding the letters too
// would make the whole line one weight and say nothing. Where no operand appears in the formula the
// substitution is left out rather than printed twice, exactly as substituted-line does.
#let inline-step-row(st, vars, note, bold: true) = {
  let res = vars.at(st.result)
  let subs = substituted-rhs(st, vars)
  let value = "\"" + value-text(res) + "\""
  // The numbers line is left out where it would say nothing new: where no operand appears in the
  // formula (substituted-line's own rule), and where the substitution *is* the answer -- a step that
  // only renames a value, `k_(beta,1,2) = k_(beta,"max")`, which would otherwise read "= 1.414 = 1.414".
  let bare = fmt-decimals(get-value(res), number-digits.get())
  let says-nothing = subs == formula-rhs(st.formula) or subs.trim() == bare
  let wrap(x) = if bold { math.bold(x) } else { x }
  let tail = eval((if says-nothing { " = " } else { " = " + subs + " = " }) + value, mode: "math")
  let line = render-formula(st) + h(0.2em) + wrap(tail)
  // the note sits at the END of the row, where it does not come between the letters and their numbers
  let noted(x) = x + (if note != none { h(0.35em) + footnote(note) })
  // Too wide for its row, it is stacked (annotated-rows): the formula in letters, then `= <numbers>` and `= <answer>` under its `=`. A formula with no `=` of its own has nothing to align them on, and stays one line.
  let at = st.formula.position(" = ")
  if at == none { return ((noted(line), st),) }
  let lhs = st.formula.slice(0, at)
  let segments = (if says-nothing { () } else { (subs,) }) + (value,)
  ((formula-chain(noted(line), render-formula(st), segments, s => chain-line(lhs, "=", s, wrap: wrap, side: x => x), last: noted), st),)
}

// One step, as the reader works it: the formula in letters -- carrying the norm citation (section 10) and, as a footnote, the step's own description of its working -- and then the same formula in numbers.
#let step-rows(st, vars, bold: true) = {
  if "formula" not in st { return ((substituted-line(st, vars, bold: bold), st),) }
  // The gap keeps the footnote marker off the formula: set flush, it reads as another factor in the equation.
  // A step's own description of its working, translated where it is the engine's sentence and left as it is where it is the engineer's, its symbols set as math.
  let note = {
    let n = get-description(st)
    if n == none { none } else { render-prose(tl-str(n)) }
  }
  let formula = [#render-formula(st)#if note != none [#h(0.35em)#footnote(note)]]
  if not is-bounded(st.formula) {
    // ⚠️ never inline for a bounded formula: it has no numbers line to join (the branch below)
    if st.at("inline", default: false) { return inline-step-row(st, vars, note, bold: bold) }
    return ((formula, st), (substituted-line(st, vars, bold: bold), none))
  }
  // A bounded formula gets no numbers line of its own (section 10bis), so what its symbols stood for is set after it on the same row rather than under it -- a half-height row carrying two words reads as a stray line.
  let subs = st.uses.filter(u => u in vars).map(u => {
    let v = vars.at(u)
    [#render-symbol(v) = #fmt-value(v)]
  })
  // Content is joined in code mode, not written as `[#formula;...]`: in
  // markup a semicolon straight after a `#expression` terminates it and is
  // never printed. `[;]` is markup, where it is just a character.
  let head = if subs.len() == 0 { formula } else {
    formula + [#semicolon-str()] + h(0.5em) + text(size: 9pt)[#t-str("with") #subs.join([, ])]
  }
  ((head, st), var-row(vars.at(st.result)))
}

// A line announcing the run of calculations under it -- «Charakteristische Lochleibungsfestigkeiten für C24:» (v0.84). Plain text, in the report's own language and with its symbols set as math like every other sentence the data carries, and its colon written by the engine so a French report keeps its narrow no-break space.
//
// The space above it is what makes a run read as a block, and it is **not** weak: weak spacing is dropped at the start of a container, and a heading is very often the first thing in its grid cell. The gap it adds to the row gutter is the only thing that tells a heading from the line under it -- the Bemessungsbeispiele set theirs in the text's own face and weight, and so does this.
#let calc-heading(head) = [#v(0.6em)#render-prose(tl-str(head))#colon-str()]

// --- Calculation display (docs/typst/report-engine.md §4, §5, docs/typst/citations.md §10) --------------------
// (domain, instance) select one whole calculation -- an instance of a calculation domain (a workbook sheet), or one domain of a position. There is deliberately no step-name argument: show-calc renders the calculation entire, ending on its result, and show-input is what picks a single intermediate value out. level: auto reads the global report-level. Position/axes headers are the job of the enclosing calc-block, not of each individual call.

/// Displays a whole calculation, in the order the source carries it out: every value in the order the data states it, a calculated one printed as its formula in letters and then as the same formula in numbers, ending on the result (sections 4, 5, 10).
///
/// ```typ
/// #show-calc("snow-load", "SL")
/// ```
///
/// ```typ
/// #show-calc("dead-load", "EL+AL-Wand", level: 3)
/// ```
///
/// ```typ
/// #show-calc("wind-load", "WL-Velo", title: none)
/// ```
///
/// ```typ
/// #show-calc("snow-load", "SL", level: -1, shown: (ce: 2, mu_11: 2, s_k: 3))
/// ```
///
/// - domain (str): a calculation domain ("snow-load", "dead-load"), or a domain of a position ("bending"). An unknown domain raises an assertion error listing the valid ones.
/// - instance (str): the workbook sheet the domain was read from ("SL-Dach1"), or a position id ("T001") for a domain carried by a position. An unknown instance raises an assertion error listing the valid ones. A position outside the enclosing calc-block's declared positions panics; a sheet is not scope-checked, a load belonging to no position (section 8).
/// - level (int, auto): which vars, which steps and which of the instance's tables are printed -- 1 is the client report, 3 the checking report (section 3.7). *Which* value appears at which level is the data's decision, not this function's: a var, a step and a table each carry their own `level` (sections 3.1, 3.3), so a value can be shown from level 2 while the formula behind it waits for level 3, as h_ref and s_k do (section 3.3bis). auto = use the global report level (the "report-level" state, section 4). -1 prints only what `shown:` names (v0.117).
/// - shown (dictionary, none): at `level: -1`, the instance's own vars and tables printed, `(s_k: 2, table-1: 1)` -- a var or a step chosen is printed whatever its own level, its notes from 2; a table is named by its place, `table-1`, `table-2`; a result not chosen is not printed. A key the instance does not have is refused naming those it has. none at any other level. A drawing of the instance -- a build-up, a snow load's disposition -- is named `figure-1`, `figure-2`.
/// - title (str, none, auto): heading above the block. auto (the default) prints the instance name, which is what tells two cases of the same load apart; none prints no heading; a string replaces it.
/// -> content
#let show-calc(domain, instance, level: auto, shown: none, title: auto) = context {
  let data = resolve-source("show-calc", domain, instance)
  let vars = data.vars
  let steps = data.steps
  // at -1 what `shown:` names is printed and nothing else of it (issue #20, v0.117): its keys are the instance's own, its variables and its tables in their order -- `table-1`, `table-2` (calc/shown_variables.py, `export_keys`)
  let table-keys = range(data.at("tables", default: ()).len()).map(i => "table-" + str(i + 1))
  // its drawings, `figure-1`, … (schema 1.5, issues #35-#37): a build-up, a roof's snow -- a list; a connector's own `figures` is a dictionary of its drawings, which show-connector prints, and none of these
  let instance-figures = { let f = data.at("figures", default: ()); if type(f) == array { f } else { () } }
  let figure-keys = range(instance-figures.len()).map(i => "figure-" + str(i + 1))
  check-shown("show-calc", level, shown, vars.keys() + table-keys + figure-keys, levels: (auto, 1, 2, 3))
  let plan = level-plan(level, shown)
  let eff-level = plan.lv
  let chosen(name) = plan.shown.at(name, default: 0)
  // A position's domain carries no `results` (section 3.1); fall back to the last step's result, which is what such a calculation ends on.
  let results = data.at("results", default: ())
  if results.len() == 0 and steps.len() > 0 {
    results = (steps.last().result,)
  }

  // Bold is the answer, not the working -- and what counts as an answer is the data's to say: a step producing one of the calculation's `results`, or one the data marks `bold` (the wind load's Staudruck, which its own sheet sets apart from the forces built on it). Both are read the same way here, for the bold line itself and for the rows its operands keep.
  let is-answer(st) = st.result in results or st.at("bold", default: false)

  // Each table carries its own level and its own place (section 3.3): the dead load's build-up is the working, shown to a checker above the values it explains; the wind load's global forces are the answer, shown from level 1 below the values leading to it, and its local forces the checker's detail after them. The defaults are the first shape. Those shown on one side keep the order the data lists them in.
  let tables = data.at("tables", default: ()).enumerate().filter(((i, t)) => if plan.picked { chosen(table-keys.at(i)) >= 1 } else { eff-level >= t.at("level", default: 3) }).map(((i, t)) => t)
  let tables-above = tables.filter(t => t.at("place", default: "above") == "above")
  // An instance's drawings -- the build-up of a dead load, the disposition of a snow load (schema 1.5) -- are printed first, from their own level (2 when they say none): the picture a reader takes in before the numbers.
  let figures = instance-figures.enumerate().filter(((i, f)) => if plan.picked { chosen(figure-keys.at(i)) >= 1 } else { eff-level >= f.at("level", default: 2) }).map(((i, f)) => f)
  let tables-below = tables.filter(t => t.at("place", default: "above") == "below")
  // A var a shown table prints in a `value` cell of its own is not set out on a row as well -- the same rule as an intermediate step's operands, applied to a table.
  let in-table = tables.map(table-vars).flatten()

  let heading = if title == auto { instance } else { title }
  let heading-below = 0.7em
  if heading != none {
    // sticky: never left at the foot of a page, its calculation on the next
    block(above: 1em, below: heading-below, sticky: true, text(weight: "bold", heading))
  }

  // The steps printed at this level, keyed by the var each produces: the calculation is walked var by var, in the order the data states them, so a var some step produces is rendered as that step rather than as a bare value -- and the order stays a property of the data rather than of this function.
  let shown-steps = (:)
  for st in steps.filter(s => if plan.picked { chosen(s.result) >= 1 } else { s.level <= eff-level }) {
    shown-steps.insert(st.result, st)
  }
  let produced = steps.map(s => s.result)

  // An intermediate step already shows its operands inside its own substituted formula ("h_ref = 438 + 200"), so they are not set out a second time on rows of their own. An *answer's* operands are the calculation's real inputs -- C_e, C_T, mu; c_h and q_p0 -- and keep their row, with the norm reference and the choices footnote a checker reads them for.
  //
  // ⚠️ A var may say it is an *input of the calculation* and keep its row whatever absorbs it (`keep`,
  // v0.84): a dowel's diameter, a member's density and its thickness are the first things a reader
  // looks up, and each of them became the operand of a formula of its own the moment SIA 265's own
  // tables were written out as formulas. The default rule is right for a value that exists only to be
  // fed into the next line; it is wrong for the ones the calculation is *about*.
  // at -1 a var chosen is printed whatever absorbs it: the engineer named it
  let absorbed = if plan.picked { () } else { shown-steps
    .values()
    .filter(s => not is-answer(s))
    .map(s => s.uses)
    .flatten() }

  let rows = ()
  let printed = ()
  // The group of the var on the row just pushed, so the next one can join it.
  let last-group = none
  for (name, v) in vars.pairs() {
    // A var may announce the run it opens, on a line of its own above it -- «Charakteristische Lochleibungsfestigkeiten für C24:», the way the Bemessungsbeispiele zur SIA 265 set a block (v0.84, section 3.3). It is inserted where this var's own first row lands, so it follows every rule that decides whether that row exists: a var above this level announces nothing, and neither does one absorbed into an intermediate formula or one that merely joins a group's row already open.
    let before = rows.len()
    if name in in-table {
      // Printed by the table below, not on a row of its own.
      printed.push(name)
    } else if name in shown-steps {
      rows += step-rows(shown-steps.at(name), vars, bold: is-answer(shown-steps.at(name)))
      last-group = none
      printed.push(name)
    } else if name in produced {
      // Its step sits above this level: the value it produced, alone.
      if (plan.picked and chosen(name) >= 1) or (not plan.picked and v.level <= eff-level) {
        rows.push(var-row(v))
        last-group = none
        printed.push(name)
      }
    } else if (plan.picked and chosen(name) >= 1) or (not plan.picked and (name not in absorbed or v.at("keep", default: false)) and v.level <= eff-level) {
      // Values the calculation states together are printed together: two vars carrying the same `group` (C_e and C_T, L and B) join one row, semicolon-separated, instead of taking a row each. Only *consecutive* ones, so a step between them still breaks the run, and the row keeps the first var's norm reference -- a group whose members cited different clauses would be a grouping error in the data.
      let group = v.at("group", default: none)
      let row = var-row(v, notes: if plan.picked { chosen(name) >= 2 } else { eff-level >= 2 })
      let group-label = v.at("group_label", default: none)
      if group != none and group == last-group {
        let prev = rows.last()
        // A var that joins a run already open and carries a `group_label` names itself *inside* the row:
        // "Bauteil 1: rho_(k,1) = ...; t_1 = ...; Bauteil 2: rho_(k,2) = ...; t_2 = ...". One row of
        // material for a connection of two members, which is what the engineer asked for in v0.84 --
        // where two groups one under the other took a line each to say the same thing.
        let joined = if group-label == none { row.at(0) } else {
          [#tl-str(group-label)] + [#colon-str()] + h(0.35em) + row.at(0)
        }
        rows.at(rows.len() - 1) = (prev.at(0) + [#semicolon-str()] + h(0.5em) + joined, prev.at(1))
      } else {
        // A group may name itself ("Gebäude Geometrie: L = ...; B = ..."), read off the var that opens the run. Joined in code mode for the same reason the semicolon is: a `:` written after a `#expression` in markup is fine, but keeping both joins in one idiom keeps them fixable in one place.
        if group-label != none {
          row = ([#tl-str(group-label)] + [#colon-str()] + h(0.35em) + row.at(0), row.at(1))
        }
        rows.push(row)
      }
      last-group = group
      printed.push(name)
    }
    let head = v.at("heading", default: none)
    if head != none and rows.len() > before {
      rows.insert(before, (calc-heading(head), none))
    }
  }

  // A result is never allowed to go missing: one that no step produces, or that this level filtered out, would otherwise vanish from a report that is meant to end on it. At -1 it goes like any other (spec D-12): the engineer chose what is printed.
  for name in results.filter(n => n not in printed and not plan.picked) {
    rows.push(var-row(vars.at(name)))
  }
  for fig in figures {
    block(above: 0.8em, below: 0.8em, breakable: false, align(left, image("../data/" + fig.file, width: fig.at("width", default: 120) * 1mm)))
  }
  // Above the values, the table is the working they come from -- its totals rows the sums the lines below carry forward (section 3.3ter). Below them, it is the answer they lead to (section 3.3quater).
  for (i, tbl) in tables-above.enumerate() {
    // the first, right under the heading, keeps to it as a row would; any other keeps its distance
    render-table(tbl, vars: vars, results: results, above: if i == 0 and heading != none { heading-below } else { auto })
  }
  annotated-rows(rows)
  for tbl in tables-below {
    render-table(tbl, vars: vars, results: results)
  }
}

// --- Check display (docs/typst/citations.md §10) ---------------------------------

/// Displays one entry of a calculation's `checks[]` (utilization ratio and status, sections 3.1, 10).
///
/// ```typ-dry
/// #show-check("bending", "T001", "Biegenachweis")
/// ```
///
/// ```typ-dry
/// #show-check("bending", "T001", "Biegenachweis", level: 3)
/// ```
///
/// - domain (str): a calculation domain, or a domain of a position ("bending") -- the same lookup shape as show-calc/show-input.
/// - instance (str): the workbook sheet, or a position id. Inside a calc-block, a position must be one of the positions that block declares.
/// - check-name (str): a check's `name` within that instance's `checks[]`, e.g. "Bending utilization". An unknown check name raises an assertion error listing the valid check names.
/// - level (int, auto): currently unused by show-check's body (every check renders the same way regardless of level) -- still validated against auto/1/2/3 for a consistent error if mistyped, and reserved for a future per-check detail split.
/// -> content
#let show-check(domain, instance, check-name, level: auto) = context {
  assert(level == auto or level in (1, 2, 3),
    message: "show-check: invalid level " + repr(level) + " -- use auto, 1, 2, or 3")
  let dom-data = resolve-source("show-check", domain, instance)

  let valid-checks = dom-data.checks.map(x => x.name)
  assert(check-name in valid-checks,
    message: "show-check: unknown check '" + check-name + "' in " + source-label(domain, instance) + " -- valid checks: " + valid-checks.join(", "))
  let c = dom-data.checks.find(x => x.name == check-name)
  let status-text = if c.status == "ok" { t-str("check_ok") } else { t-str("check_failed") }
  annotated-rows((
    (
      [#tl-str(c.name)#colon-str() #eval("eta", mode: "math") = #fmt-number(c.eta, "") --- #status-text],
      c,
    ),
  ))
}

// --- Nutzlasten, read off SIA 261's Tabelle 8 (docs/domain/loads.md §3.3septies)
// A live load is neither calculated nor entered: it is looked up, by the category of Nutzfläche a surface belongs to (A1 Wohnflächen, A3 Treppen, B Büroflächen, ... H nicht begehbare Dächer), and the norm's table gives the Flächenlast q_k and the Einzellast Q_k. So the instances of the `live-load` domain are the rows of that table, and the two functions below address one by its category. What they read is the ordinary {vars, tables, results} record every calculation has, exported by calc/domains/live_load.py -- show-calc, var-of and value-of work on this domain unchanged; these two are how the report says it in one line, and how a sentence quotes one of the two values.

#let live-load-domain = "live-load"

// The record of one category. Two things can be wrong here and neither may surface as a dictionary error: a category the norm does not have, and one the norm leaves to the project -- category E, whose instance deliberately carries no q_k at all, only the sentence saying what has to be fixed and where (section 3.3septies). A number invented for it would be exactly what this pipeline exists to prevent.
#let live-load-record(fn-name, category) = {
  let doms = load-calculations().domains
  assert(live-load-domain in doms,
    message: fn-name + ": the export carries no '" + live-load-domain + "' domain -- rerun calc/export_all.py")
  let insts = doms.at(live-load-domain).instances
  assert(category in insts,
    message: fn-name + ": unknown Nutzungskategorie '" + category + "' -- valid categories: " + insts.keys().join(", "))
  let rec = insts.at(category)
  if "q_k" not in rec.vars {
    panic(
      fn-name + ": Nutzungskategorie " + category + " ("
        + get-value(rec.vars.nutzflaeche) + ") carries no values in Tabelle 8 -- "
        + get-value(rec.vars.hinweis)
        + " State them in the report itself, as its own values.",
    )
  }
  rec
}

/// Displays the live load of one category of Nutzfläche, as SIA 261's Tabelle 8 gives it (section 3.3septies): the category, and the Flächenlast q_k and Einzellast Q_k on one line, with the table itself for a checker.
///
/// ```typ
/// #show-live-load("A1")
/// ```
///
/// ```typ
/// #show-live-load("B", level: 3)
/// ```
///
/// ```typ
/// #show-live-load("H", title: "Nicht begehbare Dächer")
/// ```
///
/// The wording comes from the data, not from here: the category's label and value, the Art der Nutzfläche and the norm's example, and each value's own footnotes from the table's notes.
/// - category (str): a category of Tabelle 8, e.g. "A1", "B", "H". An unknown one raises an assertion error listing the valid categories; category E, whose values SIA 261 8.2.2 leaves to the project, fails saying so.
/// - level (int, auto): 1 = the category with q_k and Q_k; 2 = the same line, naming what the category is and footnoting the table's notes on the values; 3 = Tabelle 8 entire with this category's row highlighted, and that line under it. auto = the global report level (section 4).
/// - title (str, none, auto): heading above the block. auto (the default) prints none -- the line names its own category; a string prints one.
/// -> content
#let show-live-load(category, level: auto, title: auto) = context {
  assert(level == auto or level in (1, 2, 3),
    message: "show-live-load: invalid level " + repr(level) + " -- use auto, 1, 2, or 3")
  let eff-level = resolve-level(level)

  let rec = live-load-record("show-live-load", category)
  let vars = rec.vars
  let results = rec.at("results", default: ())

  let heading = if title == auto { none } else { title }
  let heading-below = 0.7em
  if heading != none {
    block(above: 1em, below: heading-below, sticky: true, text(weight: "bold", heading))
  }

  // "Nutzungskategorie A1" at level 1; from level 2 also what that category is, as the norm names it and exemplifies it.
  let kat = vars.kategorie
  let head = [#tl-str(get-label(kat)) #get-value(kat)]
  if eff-level >= 2 {
    head += [, #tl-str(get-value(vars.nutzflaeche))]
    if "beispiel" in vars { head += [ (#tl-str(get-value(vars.beispiel)))] }
  }

  // The two values as every var is set, joined on one row the way show-calc joins a group.
  let q = vars.at("q_k")
  let big-q = vars.at("Q_k")
  let line = head + [#colon-str()] + h(0.35em) + var-row(q).at(0) + [#semicolon-str()] + h(0.5em) + var-row(big-q).at(0)

  // One footnote for the line, not one per value: the notes Tabelle 8 puts on this row -- on the category (the Dächer of H), on the Flächenlast and on the Einzellast -- carry the half of the table that is not a number, and the same note often stands against both values (a Parkfläche's, which act at once). Set at the end of the line, where the marker cannot be read as another exponent of kN/m².
  if eff-level >= 2 {
    let notes = ()
    for v in (kat, q, big-q) {
      let note = get-description(v)
      if note != none {
        // A note standing against both values (a Parkfläche's "gleichzeitig") reaches this line twice, once inside each value's notes: the shorter text is dropped for the one that already carries it, so the footnote says it once.
        notes = notes.filter(n => not note.contains(n))
        if not notes.any(n => n.contains(note)) { notes.push(note) }
      }
    }
    // Dropped duplicates first, then translated: the de-duplication reads the German the export carries. Joined with a content space, the notes being content once their symbols are set as math.
    // a thin space before the marker, which set flush after «kN» read as its exponent (v0.86)
    if notes.len() > 0 { line += [#h(0.2em)#footnote(notes.map(n => render-prose(tl-str(n))).join([ ]))] }
  }

  // The table is the working the two values are read off, so it keeps its place above them -- level and place are the data's, as for every other table (section 3.3).
  let tables = rec.at("tables", default: ()).filter(t => eff-level >= t.at("level", default: 3))
  for (i, tbl) in tables.filter(t => t.at("place", default: "above") == "above").enumerate() {
    render-table(tbl, vars: vars, results: results,
      above: if i == 0 and heading != none { heading-below } else { auto })
  }
  annotated-rows(((line, vars.at("q_k")),))
  for tbl in tables.filter(t => t.at("place", default: "above") == "below") {
    render-table(tbl, vars: vars, results: results)
  }
}

// `live-load` stood here until v0.80: one of the two values of a category of Nutzfläche, inside a sentence. It is `val("q_k", domain: ("live-load", "A1"))` now -- exactly as long, since the domain is a named argument, and one command less to remember (section 13). `show-live-load` keeps the category's own line, its notes and Tabelle 8 above it.

// --- The report's revision journal (docs/domain/journal.md §3.3terdecies) -----------
// One entry per revision of the report, written by hand in Woodcore's «Journal» tab and read here: its number, the day, who made it and the office's short form, then the three texts the levels govern -- the label at 1, the short description as well at 2, and everything at 3 (the engineer's decision 6.5).
//
// Nothing is computed. The export is the source's entries sorted, and this prints them: there is no {vars, steps, checks} record behind a journal, so nothing addresses one with show-calc, which is the rule a static model and a detail schema already follow.
// `load-journal` -- which reads one document's journal, `journal-files` and `wc-document` -- is declared with `woodcore-document` near the top of this file, which needs it for the PDF's keywords.

/// Every revision of the report, **newest first** -- the largest index first, which is the order `calc/journal.py` exports them in. Data access, not a display function: `journal-entries().first()` is the revision the report is at, and what the PDF's keywords name (project-info's `revision`).
///
/// ```typ
/// #journal-entries().len()
/// ```
///
/// ```typ
/// #for e in journal-entries() [ Rev. #e.index — #e.label \ ]
/// ```
///
/// Each entry carries `index`, `date` (ISO), `name`, `initials`, `label`, `summary` and `description`, the last two "" where the revision has none. Ordered by the index and never by the date: the date is typed, so it may be wrong, and a journal that reordered itself around a typo would print a revision under the wrong one.
///
/// Each of a project's documents has its own journal. `document:` says which one this reads: the statical report's (`"rs"`, the default, so that the call works outside a `context`, as it always has), the convention d'utilisation's (`"cu"`) or the base de projet's (`"bp"`); `auto` is the document being compiled -- the `document:` its entry file gave `woodcore-document` -- which Typst can only tell inside a `context`.
///
/// - document (str, auto): `"rs"`, `"cu"`, `"bp"` or `auto`. The default is `"rs"`, and **not** `auto`: a function that returns an array cannot ask a state, so `#journal-entries()` in a convention d'utilisation gives the statical report's entries unless it is written `#context journal-entries(document: auto)`. `show-journal` does follow the document by itself.
/// -> array
#let journal-entries(document: "rs") = load-journal(document: document).entries

// The three forms a journal may be set in (the engineer's own list): a table, a list of paragraphs, a grid of cards.
#let journal-forms = ("table", "list", "grid")

// An ISO date as the report prints one: «2026-09-27» -> «27.09.2026». The report's own convention, not the language's -- the title page already prints `[day].[month].[year]` whatever the report is written in -- so a date is one less thing to translate and reads the way the page the reader already has reads. Anything that is not an ISO day is printed as it stands, which `journal.check_source` makes unreachable from a saved journal.
#let journal-date(iso) = {
  let parts = if type(iso) == str { iso.split("-") } else { () }
  if parts.len() == 3 { parts.at(2) + "." + parts.at(1) + "." + parts.at(0) } else { iso }
}

// The texts an entry shows at a level: the label alone, the label and the short description, or everything it carries. Empty ones are dropped, so a revision with no short description prints its label alone rather than an empty cell (section 3.3terdecies).
#let journal-texts(entry, level) = {
  let wanted = if level <= 1 { ("label",) } else if level == 2 { ("label", "summary") } else { ("label", "summary", "description") }
  wanted.map(key => entry.at(key, default: "")).filter(t => t != "")
}

// «Rev. 3 — 27.09.2026 — FLL»: what identifies a revision, printed at every level. A long dash parts them, as every separating dash in this engine does (v0.88).
#let journal-head(entry) = [#t-str("journal.index") #str(entry.index) — #journal-date(entry.date) — #entry.initials]

/// Sets the report's revision journal -- every entry Woodcore's «Journal» tab holds, newest first -- as a table, a list or a grid of cards (docs/domain/journal.md §3.3terdecies).
///
/// ```typ
/// #show-journal()
/// ```
///
/// ```typ
/// #show-journal(form: "list", level: 3)
/// ```
///
/// ```typ
/// #show-journal(form: "grid", level: 1, title: "Änderungsverzeichnis")
/// ```
///
/// What the level governs is the **three texts** and nothing else: 1 the label, 2 the label and the short description, 3 everything the entry carries. The revision's number, its day and the office's short form identify it and are printed at every level -- a table is a table, and its levels change what its columns carry rather than which entries it has.
///
/// A journal with nothing in it prints one line saying so, rather than nothing at all.
///
/// Which journal it prints follows the document being compiled: `#show: woodcore-document.with(document: "cu")` makes it the convention d'utilisation's own (`data/journal-cu.json`), `"bp"` the base de projet's, and a document that says nothing -- the statical report -- its own, `data/journal.json`, exactly as before.
///
/// - form (str): "table" (Rev. · date · name · short form · the texts, through `render-table`, so it is set the way every other table of this engine is), "list" (one paragraph per revision) or "grid" (cards, several to a line).
/// - level (int, auto): 1, 2 or 3; auto takes the report's own (section 4).
/// - title (auto, none, str, content): auto and none print no heading -- the section's own heading is the engineer's (section 4bis) -- a string or content prints one above the journal.
/// -> content
#let show-journal(form: "table", level: auto, title: auto) = context {
  if not (form in journal-forms) {
    panic("show-journal: no form " + repr(form) + " -- valid forms: " + journal-forms.join(", "))
  }
  assert(level == auto or level in (1, 2, 3),
    message: "show-journal: invalid level " + repr(level) + " -- use auto, 1, 2, or 3")
  let eff-level = resolve-level(level)
  // The journal of the document being compiled (`wc-document`, read here: this is a context), so a convention d'utilisation prints its own «Historique des versions» and never the statical report's.
  let entries = journal-entries(document: auto)

  let heading = if title == auto { none } else { title }
  let heading-below = 0.7em
  if heading != none {
    block(above: 1em, below: heading-below, sticky: true, text(weight: "bold", heading))
  }

  if entries.len() == 0 {
    // Silence would read as a command that did nothing; what the page says is that the report has not been revised.
    block(above: if heading == none { table-spacing } else { heading-below }, below: table-spacing, emph(t-str("journal.empty")))
  } else if form == "table" {
    // Through render-table like every other table of this engine (section 3.3): three rules and nothing else, a column aligned by what it holds, the whole centred in the space it has. The texts are added as columns from the level they belong to.
    //
    // **Every text column shares the leftover width** (`wide`, which is `1fr`) as soon as there is more than one of them, and at level 1, where the label is the only one, none does -- the table is then measured and centred in the calculation's own column, which is where five columns of short values read best. Sized by their own text (`text`, which is `auto`) they do not fit: at level 3 the label column took the width its longest label wanted and the two descriptions were left with less than their own headings, and the table ran off the page.
    //
    // ⚠️ **And a narrow prose column is hyphenated**, which is the one place this engine asks for it: a table's cells are set ragged (`render-table`), and Typst's `hyphenate: auto` hyphenates only what it justifies -- so in a column three centimetres wide a German compound («Verbindungsmittel», «Kurzbeschreibung») simply ran past its column's edge. It is set here and nowhere else, so no other table of the report changes; a revision block on paper is hyphenated for exactly this reason.
    let texts = if eff-level <= 1 { ("label",) } else if eff-level == 2 { ("label", "summary") } else { ("label", "summary", "description") }
    let text-columns = texts.map(key => (
      label: [#t-str("journal." + key)],
      kind: if texts.len() == 1 { "text" } else { "wide" },
    ))
    set text(hyphenate: true)
    render-table(
      (
        // No title: a journal's heading is the section's own, written by hand, and a table titling itself here would say it twice (section 4bis).
        title: [],
        columns: (
          (label: [#t-str("journal.index")], kind: "number"),
          (label: [#t-str("journal.date")], kind: "text"),
          (label: [#t-str("journal.name")], kind: "text"),
          (label: [#t-str("journal.initials")], kind: "text"),
          ..text-columns,
        ),
        // The engineer's own words go in as CONTENT, which render-table passes through untouched: they are free text and must not be looked up in the glossary (table-cell, v0.99).
        rows: entries.map(e => (
          e.index, journal-date(e.date), [#e.name], [#e.initials],
          ..texts.map(key => [#e.at(key, default: "")]),
        )),
      ),
      above: if heading == none { auto } else { heading-below },
    )
  } else if form == "list" {
    // One paragraph per revision: what identifies it, then its texts -- the label bold, since it is the one text every level prints, the short description on the same line after a colon, and the long one as a paragraph of its own, a sentence of several lines being unreadable inside a line that started with a date.
    block(above: if heading == none { table-spacing } else { heading-below }, below: table-spacing, {
      for (i, e) in entries.enumerate() {
        let texts = journal-texts(e, eff-level)
        block(above: if i == 0 { 0em } else { row-spacing }, {
          journal-head(e) + [ — ] + [#e.name] + [#colon-str() ] + text(weight: "bold", [#texts.first()])
          if texts.len() > 1 { [#colon-str() ] + [#texts.at(1)] }
          if texts.len() > 2 { block(above: 0.35em, [#texts.at(2)]) }
        })
      }
    })
  } else {
    // Cards, several to a line, as the start page sets its recent projects: two to a line where there is prose to read, three where a level prints the label alone.
    // ⚠️ A card is as tall as what it holds and never `height: 100%`: in a grid whose row height is itself decided by its cells, that asks the cell how tall the row is while the row is being measured, and the cards of one row were drawn over each other. Two cards of one row therefore end at different heights, which is what a grid of cards does anywhere else.
    let columns = if eff-level <= 1 { 3 } else { 2 }
    block(above: if heading == none { table-spacing } else { heading-below }, below: table-spacing, grid(
      columns: columns * (1fr,),
      column-gutter: 0.9em,
      row-gutter: 0.9em,
      align: top,
      ..entries.map(e => block(
        width: 100%, breakable: false,
        inset: 0.7em, radius: 3pt, stroke: 0.5pt + luma(70%),
        {
          text(size: 8.5pt, journal-head(e) + [ — ] + [#e.name])
          let texts = journal-texts(e, eff-level)
          block(above: 0.4em, text(weight: "bold", [#texts.first()]))
          for extra in texts.slice(1) { block(above: 0.35em, [#extra]) }
        },
      )),
    ))
  }
}

// --- Forces in the fasteners of a connection (docs/domain/connections.md §3.3quinquies)
// The one calculation this engine carries out rather than reads. N, V and M are written in the report -- until load combinations export them (section 3.5) there is nowhere else for them to come from -- so they are distributed here. Everything they are distributed *over* is data: the fasteners, the rotation centre, I_p, the directions and the members come from data/connections.json, calculated and validated in Python, and a force given as a var object (var-of) is taken with its unit checked. Woodcore previews the same distribution in Python (calc/domains/connection.py, fastener_forces), and the two are checked against each other.
//
// The frame is the detail schema's (section 3.3quinquies): millimetres, x to the right, z down; angles from x towards z; M positive the other way, turning z towards x. So F_x,i = (N_x + V_x)/n + M·Δz_i/I_p and F_z,i = (N_z + V_z)/n - M·Δx_i/I_p.

// A raw number as it is written inside a formula's numbers line: a negative one in parentheses, so "a - b" never reads "a - -b". The raw-number counterpart of value-in-formula, and like it a Typst math *source* string. Requires `context` (number-digits).
#let number-in-formula(x) = {
  let s = fmt-decimals(x, number-digits.get())
  if s.starts-with("-") { "(" + s + ")" } else { s }
}

// A number with its unit, as a quoted math source string: "5.544 kN" -- how a numbers line ends. Quoted text keeps a hyphen where math would set a minus, so the sign is given as one.
#let quantity-in-formula(x, unit, digits: auto) = {
  let s = fmt-decimals(x, if digits == auto { number-digits.get() } else { digits })
  if s.starts-with("-") { s = "−" + s.slice(1) }
  "\"" + s + (if unit == "°" { "" } else { " " }) + unit + "\""
}

// Angles are printed to a tenth of a degree at most: a force-grain angle is read into f_h,α, where more would be false precision.
#let angle-digits() = calc.min(1, number-digits.get())

// The direction a force acts in, in degrees from x towards z within (-180°, 180°]; none for no force at all. Typst's atan2 takes x first.
#let force-line(fx, fz) = if fx == 0 and fz == 0 { none } else { calc.atan2(fx, fz).deg() }

// The angle between a force's line and a member's grain (Kraft-Faser-Winkel), folded into 0°-90° -- a line and a grain have no sense. For the reference member, at 0°, it is arctan(|F_z| / |F_x|).
#let grain-angle(line, member) = {
  if line == none { return none }
  let b = calc.rem(calc.abs(line - member), 180)
  if b > 90 { 180 - b } else { b }
}

// Fastener numbers as the report writes them: runs of consecutive numbers as "1–4", the rest one by one -- "1, 3, 13, 15". The same rule as calc/domains/connection.py's number_ranges.
#let number-ranges(numbers) = {
  let parts = ()
  let i = 0
  while i < numbers.len() {
    let j = i
    while j + 1 < numbers.len() and numbers.at(j + 1) == numbers.at(j) + 1 { j += 1 }
    parts.push(if j == i { str(numbers.at(i)) } else { str(numbers.at(i)) + "–" + str(numbers.at(j)) })
    i = j + 1
  }
  parts.join(", ")
}

// The force arrows drawn on a connection's figure, as SVG elements, and the legend's note on them -- calc/domains/connection_svg.py's _arrow, _shares, force_arrows and share_note, rule for rule, so the report's figure and Woodcore's preview draw alike: a line and a polygon head, the yellow resultant outlined and labelled F1, F2, …, and all of them at one scale, the longest `figure.arrow` long, every one of them at its true length, so that a fastener's three actions add up to its resultant; a share too small to make out beside the resultants of a moment is drawn all the same, the legend then naming it with its value.
// Typst writes a negative number with a typographic minus, which an SVG parser does not read as one: the elements of the upper fasteners, whose y is negative, would be dropped without a word.
#let svg-number(x) = str(calc.round(x, digits: 2)).replace("−", "-")

#let svg-arrow(p, q, color, width, head, edge: none) = {
  let dx = q.at(0) - p.at(0)
  let dy = q.at(1) - p.at(1)
  let length = calc.sqrt(dx * dx + dy * dy)
  if length < 1e-9 { return "" }
  let ux = dx / length
  let uy = dy / length
  let h = calc.min(head, 0.6 * length)
  let base = (q.at(0) - h * ux, q.at(1) - h * uy)
  let side = (-uy * 0.37 * h, ux * 0.37 * h)
  let pt(x, y) = svg-number(x) + "," + svg-number(y)
  let stem(colour, w) = (
    "<line x1=\"" + svg-number(p.at(0)) + "\" y1=\"" + svg-number(p.at(1)) + "\" x2=\"" + svg-number(base.at(0)) + "\" y2=\""
      + svg-number(base.at(1)) + "\" stroke=\"" + colour + "\" stroke-width=\"" + svg-number(w) + "\"/>"
  )
  let out = if edge != none { stem(edge, width * 1.7) } else { "" }
  out += stem(color, width)
  out += "<polygon points=\"" + pt(q.at(0), q.at(1)) + " " + pt(base.at(0) + side.at(0), base.at(1) + side.at(1)) + " "
  out += pt(base.at(0) - side.at(0), base.at(1) - side.at(1)) + "\" fill=\"" + color + "\""
  out += if edge != none { " stroke=\"" + edge + "\" stroke-width=\"" + svg-number(width * 0.35) + "\"/>" } else { "/>" }
  out
}

#let share-shown = 0.9
#let share-head = 0.7
// How thick an arrow is drawn, in strokes -- connection_svg.py's ACTION_WIDTH and RESULTANT_WIDTH: an action (N/n, V/n, the force from M) is the thinner, the resultant they add up to the heavier, and the two are tied so that the resultant cannot end up the thinner.
#let action-width = 1.6
#let resultant-width = 1.5 * action-width

// What the moment alone puts on each fastener: its force less the shares of N and V, which every fastener carries alike -- M·r_i/I_p at right angles to the lever arm, the V_b,i of bauforumstahl's Arbeitshilfe 2.9.
#let moment-parts(forces, n-share, v-share) = forces.map(r => (
  r.fx - n-share.at(0) - v-share.at(0),
  r.fz - n-share.at(1) - v-share.at(1),
))

// The common scale k and N/n, V/n as drawn: each that is not zero with its vector, size, colour and length -- always k times its size, and `hidden` where that is shorter than share-shown heads -- the legend's note then gives its value (v0.50).
#let fastener-shares(figure, forces, n-share, v-share) = {
  let size(v) = calc.sqrt(v.at(0) * v.at(0) + v.at(1) * v.at(1))
  // every arrow the figure carries, so that one scale fits them all: a resultant can be shorter than the forces it adds up, where they oppose each other
  let largest = calc.max(0, size(n-share), size(v-share), ..forces.map(r => r.f),
    ..moment-parts(forces, n-share, v-share).map(size))
  if largest <= 0 { return (0, ()) }
  let k = figure.arrow / largest
  let shortest = share-shown * figure.head
  let shares = ()
  for (name, vector, colour) in (("N/n", n-share, "#1f5fbf"), ("V/n", v-share, "#c0392b")) {
    let s = size(vector)
    if s > 0 {
      shares.push((name: name, vector: vector, size: s, colour: colour, length: k * s, hidden: k * s < shortest))
    }
  }
  (k, shares)
}

#let fastener-arrows(figure, forces, n-share, v-share) = {
  let (k, shares) = fastener-shares(figure, forces, n-share, v-share)
  if k <= 0 { return "" }
  let ex = figure.ex
  let ez = figure.ez
  let step(v, scale) = (
    scale * (v.at(0) * ex.at(0) + v.at(1) * ez.at(0)),
    scale * (v.at(0) * ex.at(1) + v.at(1) * ez.at(1)),
  )
  let out = ""
  let labels = ""
  // the resultants first: the thinner shares are drawn over them, which would otherwise hide them
  for (p, r) in figure.points.zip(forces) {
    let d = step((r.fx, r.fz), k)
    let q = (p.at(0) + d.at(0), p.at(1) + d.at(1))
    out += svg-arrow(p, q, "#f2c200", resultant-width * figure.stroke, figure.head, edge: "#6b5200")
    let dx = q.at(0) - p.at(0)
    let dy = q.at(1) - p.at(1)
    let length = calc.sqrt(dx * dx + dy * dy)
    if length > 1e-9 {
      let x = q.at(0) + 0.6 * figure.font * dx / length
      let y = q.at(1) + 0.6 * figure.font * dy / length + 0.22 * figure.font
      labels += "<text x=\"" + svg-number(x) + "\" y=\"" + svg-number(y) + "\" font-family=\"Arial\" font-size=\""
      labels += svg-number(0.62 * figure.font) + "\" font-weight=\"bold\" fill=\"#6b5200\" text-anchor=\"middle\">F" + str(r.nr) + "</text>"
    }
  }
  for (p, moment) in figure.points.zip(moment-parts(forces, n-share, v-share)) {
    let d = step(moment, k)
    out += svg-arrow(p, (p.at(0) + d.at(0), p.at(1) + d.at(1)), "#2e8b57", action-width * figure.stroke, share-head * figure.head)
  }
  for share in shares {
    let d = step(share.vector, k)
    for p in figure.points {
      out += svg-arrow(p, (p.at(0) + d.at(0), p.at(1) + d.at(1)), share.colour, action-width * figure.stroke, share-head * figure.head)
    }
  }
  out + labels
}

// The legend's last line, at the figure's `<!-- note -->` marker: which shares come out too small to make out at the figure's scale, with their values -- nothing when both can be read off the drawing.
#let share-note(figure, forces, n-share, v-share) = {
  let (_, shares) = fastener-shares(figure, forces, n-share, v-share)
  // a value written in the legend is text on the page and not a coordinate: its sign, were it ever negative, would be a minus (signed-text); svg-number's two decimals keep it Woodcore's own note
  let hidden = shares.filter(s => s.hidden).map(s => s.name + " = " + signed-text(svg-number(s.size)) + " kN")
  if hidden.len() == 0 { "" } else { t-str("figure.too_small") + hidden.join(", ") }
}

// The forces in the fasteners, from the three actions and the geometry the export carries: N and V shared equally among the n of them, M in proportion to each one's distance to the rotation centre and at right angles to it, the three added as vectors. A **pure function** of the record and the three magnitudes, and that is what it is for: the registry update that publishes them and the context that prints them are then the one arithmetic (section 2, rule 1) -- and an update, which may read no state, needs nothing here but the numbers it is handed.
#let polar-distribution(c, n-total, v-total, m-total) = {
  let vars = c.vars
  let n = get-value(vars.n)
  let ip = get-value(vars.I_p)
  let with-moment = ip > 0
  let xc = get-value(vars.x_c)
  let zc = get-value(vars.z_c)
  let a-n = get-value(vars.alpha_N)
  let a-v = get-value(vars.alpha_V)
  let nx = n-total * calc.cos(a-n * 1deg)
  let nz = n-total * calc.sin(a-n * 1deg)
  let vx = v-total * calc.cos(a-v * 1deg)
  let vz = v-total * calc.sin(a-v * 1deg)
  // kNm -> kN·mm, so that M·Δ/I_p comes out in kN
  let m = m-total * 1000
  let forces = c.fasteners.enumerate().map(((i, q)) => {
    let dx = q.x - xc
    let dz = q.z - zc
    let fx = (nx + vx) / n + (if with-moment { m * dz / ip } else { 0 })
    let fz = (nz + vz) / n - (if with-moment { m * dx / ip } else { 0 })
    (nr: i + 1, dx: dx, dz: dz, fx: fx, fz: fz, f: calc.sqrt(fx * fx + fz * fz))
  })
  // Every fastener carrying the largest resultant, within rounding: all are named, the working shown for the first -- the same tolerance as Woodcore's preview.
  let fmax = calc.max(..forces.map(r => r.f))
  let governing = forces.filter(r => r.f >= fmax - 1e-9 * calc.max(1, fmax)).map(r => r.nr)
  (n: n, ip: ip, moment: with-moment, xc: xc, zc: zc, an: a-n, av: a-v,
   nx: nx, nz: nz, vx: vx, vz: vz, m: m,
   forces: forces, fmax: fmax, governing: governing, top: forces.at(governing.first() - 1))
}

/// Displays a connection saved in Woodcore with the forces in its fasteners: N and V shared equally among the n fasteners, M in proportion to each fastener's distance to the rotation centre and at right angles to it, the three added as vectors -- F_x,i = (N_x + V_x)/n + M·Δz_i/I_p, F_z,i = (N_z + V_z)/n − M·Δx_i/I_p, F_i = √(F_x,i² + F_z,i²), in the frame of the detail schema the connection is drawn on -- millimetres, x to the right, z down (docs/domain/connections.md §3.3quinquies, docs/domain/detail-schemas.md §3.3decies).
///
/// ```typ
/// #show-polar-moment("VU-MP-1", N: 7.5, V: 25, M: 6.6)
/// ```
///
/// ```typ
/// #show-polar-moment("VU-MP-1", V: 12, level: 1)
/// ```
///
/// ```typ
/// #show-polar-moment("VU-MP-1", N: 7.5, V: 25, M: 6.6, level: -1, shown: (I_p: 3, F_max: 2))
/// ```
///
/// The one calculation the engine carries out itself: N, V and M are given here, in the report, and distributed over the geometry the connection carries in data/connections.json. The most stressed fastener is the one with the largest resultant, taken over all of them; where several carry it, all are named ("Verbindungsmittel 1–4") and the working is shown for the first. The figure is **the schema's own drawing**, with this connection's fasteners numbered on it and every fastener's share of N and V and its resultant drawn at one scale -- a share a moment would make too short to see is drawn at its true length all the same and named in the legend with its value. The reference the connection cites is printed once, beside the heading. A connection names a schema and no connector (v0.76): what fastens the joint is the connector's own calculation, show-connector-resistance.
/// - connection (str): the connection's id, as saved in Woodcore -- by default the slug of its name. An unknown id fails listing the valid ones.
/// - N (int, float, dictionary, str): the total normal force in kN, positive in the direction of its arrow in the figure. A var object (var-of(...)) is accepted too, its unit then required to be kN, and so is the name of a variable the report declared above (`N: "N_Ed"`).
/// - V (int, float, dictionary, str): the total shear force in kN, positive in the direction of its arrow; a number, a var object or a variable's name, as N.
/// - M (int, float, dictionary, str): the total moment about the rotation centre in kNm, positive anticlockwise on the figure (z towards x); a number, a var object or a variable's name, as N.
/// - level (int, auto): 1 = the force in the most stressed fastener; 2 = the figure, n and I_p on one line, the forces, the formulas in letters and in numbers for that fastener and its force-grain angles; 3 = first the fasteners' positions, then the rotation centre and how it is found, the Bezugselement and the angles between the members, then level 2's content with I_p in numbers and the components of N and V, and the force in every fastener in two tables: as the three forces distribute, and in the most unfavourable superposition, N, V and the force from M added component by component with their magnitudes (F*_x,i = (|N_x| + |V_x|)/n + |M|·|Δz_i|/I_p, F*_z,i likewise with |Δx_i|). auto = the global report level (section 4). Each formula in letters and the same formula in numbers stand on **one** row, joined by a semicolon (v0.84). -1 prints only the groups of lines `shown:` names, each at its own level, beside the heading (v0.117).
/// - shown (dictionary, none): at `level: -1`, the groups of lines printed and the level of each: `positions`, `centre`, `theta` (the angles between the members), `n`, `I_p`, `forces` (N, V, M), `components`, `F_x_i`, `F_z_i`, `F_max` (1 its one line, 2 its working), `beta`, `forces_table`, `worst_table` -- the figure where one is chosen at 2 or 3. none at any other level.
/// - title (str, none, auto): heading above the block. auto prints "Anschluss", the id and the connection's label; none prints no heading, the citation then standing beside the first line that can carry one -- F_max at level 1, n at level 2, and at level 3 the rotation centre, which is under the fasteners' table since v0.84; a string replaces it.
/// - width (relative, length): the figure's width, 60% of the text width by default.
/// -> content
#let show-polar-moment(connection, N: 0, V: 0, M: 0, level: auto, shown: none, title: auto, width: 60%) = {
  // What this call works out is written into the registry under the connection's own name (v0.85): F_max, every fastener's resultant, and the force-grain angle towards each member. Those numbers are computed here, in Typst, from an N, a V and an M the report states, so no file carries them (section 1) and nothing could name one afterwards; a var-domain named after the connection keeps two connections from writing over each other, and `#val("F_max", domain: "VU-MP-1")`, `#var("F_max", domain: ("connection", "VU-MP-1"))` and `#find` all reach them.
  //
  // ⚠️ The update is emitted **here, before the context below**, exactly as `var` and `eq` emit theirs (section 10quinquies) -- and it was emitted from *inside* the context until v0.85.1, which is a state written where it cannot be read back the same way. `find`, `val` and `verify` read the registry inside a context of their own and saw it; `eq` reads it inside its own `var-registry.update`, the folded chain, and did not. A value half the commands can name is worse than one none of them can. The price is that the magnitudes are resolved twice, here off `d` and below off the same registry -- and the arithmetic is not, `polar-distribution` being the one place it lives.
  //
  // ⚠️ Anything the context is about to refuse -- an unknown connection, a name not declared, a var in the wrong unit, a moment on a group with no lever arm -- publishes nothing and is reported *there*: the function of a state update runs only where something reads that state, so a panic written here would be silent in a document that never looks the registry up again.
  var-registry.update(d => {
    let conns = load-connections().connections
    if type(connection) != str or not (connection in conns) { return d }
    let c = conns.at(connection)
    if not c.at("calculated", default: true) { return d }
    let magnitude(x, unit) = {
      let x = if type(x) == str { var-lookup(d, x) } else { x }
      if type(x) == dictionary and "value" in x {
        if get-unit(x) == unit { get-value(x) } else { none }
      } else if type(x) == int or type(x) == float { x } else { none }
    }
    let n-total = magnitude(N, "kN")
    let v-total = magnitude(V, "kN")
    let m-total = magnitude(M, "kNm")
    if n-total == none or v-total == none or m-total == none { return d }
    if m-total != 0 and get-value(c.vars.I_p) <= 0 { return d }
    let dist = polar-distribution(c, n-total, v-total, m-total)
    let line-k = force-line(dist.top.fx, dist.top.fz)
    // What each of these *is* — «Grösste Kraft in einem Verbindungsmittel» — so it is a `label` and not a `description`, which is why a value was chosen and carries the choices with it (sections 3.1, 9; the two were parted in the registry in v0.85.1). It is what `find` prints in its Bezeichnung column, and what `#var("F_max", domain: ("connection", id))` reads.
    let record(value, unit, symbol, label) = (
      value: value, unit: unit, warning: none, symbol: symbol,
      label: label, description: none, norm: none, norm_ref: "", source: none,
    )
    let dom = d.domains.at(connection, default: (:))
    dom.insert("F_max", record(dist.fmax, "kN", "F_\"max\"", t-of("de", "polar.f_max")))
    for row in dist.forces {
      dom.insert("F_" + str(row.nr), record(row.f, "kN", "F_" + str(row.nr), t-of("de", "polar.f_i", i: str(row.nr))))
    }
    if line-k != none {
      for j in range(c.members.len()) {
        dom.insert("beta_" + str(j + 1), record(grain-angle(line-k, c.members.at(j).axis), "°",
          "beta_" + str(j + 1), t-of("de", "polar.beta_j", j: str(j + 1))))
      }
    }
    d.domains.insert(connection, dom)
    d
  })
  context {
  // A line of formulas that wraps -- the force-grain angles of three members, the long citation -- reads better ragged than stretched.
  set par(justify: false)
  // at -1 (issue #20, v0.117) each key of lib/shown-variables.json is a group of lines -- the fasteners' positions, the rotation centre, the angles between the members, n, I_p, the internal forces, their components, F_x,i, F_z,i, F_max, the force-grain angles, the two tables -- printed at the level chosen for it, the figure where one is chosen at 2 or 3 (spec D-14)
  check-shown("show-polar-moment", level, shown, shown-keys("show-polar-moment"), levels: (auto, 1, 2, 3))
  let plan = level-plan(level, shown)
  let eff-level = plan.lv
  let conns = load-connections().connections
  assert(type(connection) == str and connection in conns,
    message: "show-polar-moment: no connection " + repr(connection) + " -- " + (if conns.len() == 0 { "none saved yet (save one in Woodcore's polar moments tab)" } else { "valid connections: " + conns.keys().join(", ") }))
  let c = conns.at(connection)
  if not c.at("calculated", default: true) {
    panic("show-polar-moment: connection '" + connection + "' cannot be printed -- " + c.reason + ", then export again.")
  }
  let vars = c.vars

  // A force given as a number, or as a var read out of the data -- whose unit must then be the one this function computes in.
  // A force may be given as a number, as a var object, or -- since v0.61 -- as the **name** of a variable the report wrote down with #var or #eq. The name is what a registry can offer: its values live in a state, so they cannot be read outside a `context`, and an argument is evaluated before this function's own context is entered. Looking the name up in here is what lets `N: "N_Ed"` work at all.
  let magnitude(x, name, unit) = {
    let x = if type(x) == str {
      let found = var-lookup(var-registry.get(), x)
      assert(found != none,
        message: "show-polar-moment: " + name + ": no variable named " + repr(x)
          + " -- declared here: " + var-names(var-registry.get()).join(", "))
      found
    } else { x }
    if type(x) == dictionary and "value" in x {
      assert(get-unit(x) == unit,
        message: "show-polar-moment: " + name + " is a var in " + repr(get-unit(x)) + " -- expected " + unit)
      get-value(x)
    } else {
      assert(type(x) == int or type(x) == float,
        message: "show-polar-moment: " + name + " must be a number in " + unit + ", a var, or the name of one, got " + repr(x))
      x
    }
  }
  let n-total = magnitude(N, "N", "kN")
  let v-total = magnitude(V, "V", "kN")
  let m-total = magnitude(M, "M", "kNm")

  assert(m-total == 0 or get-value(vars.I_p) > 0,
    message: "show-polar-moment: connection '" + connection + "' has I_p = 0 -- its fasteners have no lever arm about the rotation centre, so it cannot take M = " + str(m-total) + " kNm")
  let dist = polar-distribution(c, n-total, v-total, m-total)
  let n = dist.n
  let ip = dist.ip
  let with-moment = dist.moment
  let xc = dist.xc
  let zc = dist.zc
  let a-n = dist.an
  let a-v = dist.av
  let nx = dist.nx
  let nz = dist.nz
  let vx = dist.vx
  let vz = dist.vz
  let m = dist.m
  let forces = dist.forces
  let f-max = dist.fmax
  let governing = dist.governing
  let top = dist.top
  let nr = str(top.nr)
  let members = c.members
  let r = c.reference - 1
  let member-name(j) = {
    let member = members.at(j)
    if member.name != "" { member.name } else if member.position != "" { member.position } else { t-str("connection.member_fallback", n: str(j + 1)) }
  }
  let line-k = force-line(top.fx, top.fz)

  let math-line(src, bold: false) = {
    let line = eval(src, mode: "math")
    if bold { math.bold(line) } else { line }
  }
  let q = quantity-in-formula
  let deg(x) = quantity-in-formula(x, "°", digits: angle-digits())
  let join-rows(parts) = parts.enumerate().map(((i, part)) => if i == 0 { part } else { [#semicolon-str()] + h(0.5em) + part }).sum()

  // The reference, once, beside the heading -- every line below follows it (section 3.3quinquies). Without a heading it stands beside the first line the level prints: `cite` is that citation, none where the heading carries it.
  let heading = if title == auto {
    t-str("connection.caption", id: connection) + (if c.label != "" { colon-str() + " " + c.label } else { "" })
  } else { title }
  let cite = if heading == none { c } else { none }
  if heading != none {
    // sticky: a heading is never left at the foot of a page, its content on the next
    block(sticky: true, annotated-rows(((text(weight: "bold", heading), c),)))
    v(0.4em, weak: true)
  }

  // Singular or plural as the count asks: one fastener carries it, or several do.
  let fastener-word = if governing.len() > 1 { t-str("fasteners") } else { t-str("fastener") }
  let governing-row = ([#t-label("governing") #fastener-word #number-ranges(governing)], none)

  // F_max's own level: 1 its one line, as level 1 prints it alone; 2 and 3 its working, with the fasteners carrying it
  let fmax-lv = plan-at(plan, "F_max", 1)
  if fmax-lv == 1 {
    // Level 1: the answer, and which fasteners carry it.
    annotated-rows(((
      math-line("F_\"max\" = F_" + nr + " = " + q(top.f, "kN"), bold: true) + h(0.6em) + text(size: 9pt)[(#fastener-word #number-ranges(governing))],
      cite,
    ),))
  }
  if eff-level >= 2 or plan.picked {
    let figure-content = {
      let svg = read("../data/" + c.figure.files.at(report-lang()))
      let share(total, a) = (total / n * calc.cos(a * 1deg), total / n * calc.sin(a * 1deg))
      let n-share = share(n-total, a-n)
      let v-share = share(v-total, a-v)
      let arrows = fastener-arrows(c.figure, forces, n-share, v-share)
      let note = share-note(c.figure, forces, n-share, v-share)
      figure(
        image(bytes(svg.replace("<!-- forces -->", arrows).replace("<!-- note -->", note)), format: "svg", width: width),
        caption: [#t-str("connection.caption", id: connection)#if c.label != "" [#colon-str() #c.label] -- #t-str("connection.figure_caption")],
      )
    }

    // Level 3 opens on the geometry: the fasteners' positions, then the rotation centre and how it is found, and the frame the numbers are in.
    if plan-at(plan, "positions", 3) >= 1 {
      // The table first, the centre under it (v0.84, the engineer's request): x_c and z_c are the means of the x and z columns, so they are set where the reader has just read those columns rather than above them. With `title: none` the citation therefore stands beside the centre rather than beside the first thing printed -- a table read from the data carries no norm of its own, so there is nowhere on it to put one.
      // The first, right under the heading, keeps to it as a row would; standing on its own it keeps its distance, like any other table.
      render-table(c.tables.first(), vars: vars, results: c.results, above: if heading != none { 0.7em } else { auto })
    }
    if plan-at(plan, "centre", 3) >= 1 {
      let centre-rows = ()
      // A centre drawn in the schema is a fixed point too: Σx_i/n is not how it was found.
      if c.center.mode in ("manual", "aid") {
        centre-rows.push((
          [#t-label("rotation_centre_fixed")] + h(0.35em) + join-rows((math-line("x_c = " + q(xc, "mm")), math-line("z_c = " + q(zc, "mm")))),
          cite,
        ))
      } else {
        // x_c = Σx_i/n, the sum set out by distinct value -- "(5 · (−70) + 5 · 0 + 5 · 70)/15" -- as long as that stays short.
        let mean-line(symbol, axis, value) = {
          let coordinates = c.fasteners.map(f => f.at(axis))
          let distinct = coordinates.dedup().sorted()
          let numerator = if distinct.len() > 6 {
            number-in-formula(coordinates.sum())
          } else {
            let terms = distinct.map(x => {
              let count = coordinates.filter(y => y == x).len()
              (if count > 1 { str(count) + " dot " } else { "" }) + number-in-formula(x)
            })
            if terms.len() > 1 { "(" + terms.join(" + ") + ")" } else { terms.first() }
          }
          math-line(symbol + "_c = (sum " + symbol + "_i)/n = " + numerator + "/" + number-in-formula(n) + " = " + q(value, "mm"))
        }
        centre-rows.push(([#t-label("rotation_centre_centroid")], cite))
        centre-rows.push((mean-line("x", "x", xc), none))
        centre-rows.push((mean-line("z", "z", zc), none))
      }
      // the label and its two formulas, kept on one page
      block(breakable: false, annotated-rows(centre-rows))
    }
    if plan-at(plan, "theta", 3) >= 1 {
      let angle-parts = range(members.len())
        .filter(j => j != r)
        .map(j => math-line("theta_(" + str(r + 1) + "," + str(j + 1) + ") = " + deg(members.at(j).local)))
      annotated-rows((
        ([#t-label("reference_member_axes") #member-name(r) (#t-str("member") #(r + 1))], none),
        ([#t-label("angles_between_members")] + h(0.35em) + join-rows(angle-parts), none),
      ))
    }

    if plan-any(plan, 2) { figure-content }

    // Under the figure: n and I_p -- I_p's working at level 3 -- then the forces, the most stressed fastener's numbers, and its force-grain angles.
    let rows = ()
    // n and I_p on one line, joined the way show-calc joins the vars of a `group` (section 3.3) -- and at level 3 I_p's own two lines with them, the formula in letters and the same formula in numbers: «n = 4; I_p = I_p,x + I_p,z; I_p = 14400 + 14400 = 28800 mm²». Two declarations and the working behind one of them read as a single statement, and each cost a line of its own until v0.84.
    let geometry-parts = if plan-at(plan, "n", 2) >= 1 { (var-row(vars.n).at(0),) } else { () }
    let ip-lv = plan-at(plan, "I_p", 2)
    if ip-lv >= 3 {
      let st = c.steps.find(s => s.result == "I_p")
      // each as its one line: joined into one row here, a line is never stacked (formula-chain)
      geometry-parts += step-rows(st, vars, bold: true).map(row => one-line(row.at(0)))
    } else if ip-lv >= 1 {
      geometry-parts.push(var-row(vars.I_p).at(0))
    }
    // At level 2 with no heading this is the first line printed, so it carries the citation; at level 3 the centre above it already did.
    if geometry-parts.len() > 0 { rows.push((join-rows(geometry-parts), if eff-level == 2 and not plan.picked { cite } else { none })) }
    if plan-at(plan, "forces", 2) >= 1 {
      rows.push((
        [#t-label("internal_forces")] + h(0.35em) + join-rows((math-line("N = " + q(n-total, "kN")), math-line("V = " + q(v-total, "kN")), math-line("M = " + q(m-total, "kNm")))),
        none,
      ))
    }
    // Level 3: how N and V split into x and z, one component a row -- but only where the split has something to say. A force along x or along z is its own component, and a force of zero has none: "N_x = N dot cos(0°) = 0 kN" and its z line then restate the N above them and nothing more. That is the common case, the two forces usually acting along the members: with the members at right angles, x along one and z along the other, both splits are trivial and neither is printed.
    if plan-at(plan, "components", 3) >= 1 {
      let angle(a) = fmt-decimals(a, number-digits.get()) + "°"
      let splits(total, a) = total != 0 and calc.rem(a, 90) != 0
      for (sym, total, a, fx, fz) in (("N", n-total, a-n, nx, nz), ("V", v-total, a-v, vx, vz)) {
        if splits(total, a) {
          rows.push((math-line(sym + "_x = " + sym + " cos alpha_" + sym + " = " + number-in-formula(total) + " dot cos(" + angle(a) + ") = " + q(fx, "kN")), none))
          rows.push((math-line(sym + "_z = " + sym + " sin alpha_" + sym + " = " + number-in-formula(total) + " dot sin(" + angle(a) + ") = " + q(fz, "kN")), none))
        }
      }
    }
    if fmax-lv >= 2 { rows.push(governing-row) }

    // Each formula in letters, then in numbers for the most stressed fastener -- the answer, its resultant, set bold (section 10bis). Without a lever arm at all (one fastener, or all of them at the rotation centre) there is no moment term to write.
    let m-num = number-in-formula(m-total) + " dot 10^3"
    let direct(a, b) = "(" + number-in-formula(a) + " + " + number-in-formula(b) + ")/" + number-in-formula(n)
    let moment-x = if with-moment { " + (" + m-num + " dot " + number-in-formula(top.dz) + ")/" + number-in-formula(ip) } else { "" }
    let moment-z = if with-moment { " - (" + m-num + " dot " + number-in-formula(top.dx) + ")/" + number-in-formula(ip) } else { "" }
    let formula-x = math-line("F_(x,i) = (N_x + V_x)/n" + (if with-moment { " + (M dot Delta z_i)/I_p" } else { "" }))
    if with-moment {
      // The gap keeps the footnote marker off the formula, as on every formula's.
      // The hole of this one sentence is a subscript, which no plain string can carry: the pattern is split on it and the math set between the halves.
      let moment-note = t-pattern("connection.moment_note").split("{p}")
      formula-x = formula-x + h(0.35em) + footnote[#moment-note.first()#sub[p]#moment-note.last()]
    }
    // Since v0.84 the two stand on **one** row, joined by a semicolon like the vars of a `group`: the second line is the first with its numbers put in, so the pair is one statement and reads as one. The answer stays bold and the letters line does not, which is what still marks the answer (section 10bis), and a footnote marker -- the moment note on F_x,i -- keeps its place before the semicolon. Three lines of six saved on every level-2 and level-3 connection.
    if plan-at(plan, "F_x_i", 2) >= 1 {
      rows.push((
        join-rows((formula-x, math-line("F_(x," + nr + ") = " + direct(nx, vx) + moment-x + " = " + q(top.fx, "kN")))),
        none,
      ))
    }
    if plan-at(plan, "F_z_i", 2) >= 1 {
      rows.push((
        join-rows((
          math-line("F_(z,i) = (N_z + V_z)/n" + (if with-moment { " - (M dot Delta x_i)/I_p" } else { "" })),
          math-line("F_(z," + nr + ") = " + direct(nz, vz) + moment-z + " = " + q(top.fz, "kN")),
        )),
        none,
      ))
    }
    if fmax-lv >= 2 { rows.push((
      join-rows((
        math-line("F_i = sqrt(F_(x,i)^2 + F_(z,i)^2)"),
        // The answer says which fastener it is *and* that it is the largest (v0.85, the engineer's request): the fastener the working was shown for is the governing one, so "F_max = F_1 = ..." is true by construction, and level 2 then closes on the same statement level 1 prints alone.
        math-line("F_\"max\" = F_" + nr + " = sqrt(" + number-in-formula(top.fx) + "^2 + " + number-in-formula(top.fz) + "^2) = " + q(top.f, "kN"), bold: true),
      )),
      none,
    )) }

    // The force-grain angle of that fastener, towards each member's grain: what the embedment strength f_h,α of the next check is read with. With x along the reference member's grain, its own angle is the arctangent of the components -- no separate direction to compute first.
    let beta-lv = plan-at(plan, "beta", 2)
    if line-k != none and beta-lv >= 1 {
      if beta-lv >= 3 {
        // arctan(|F_z| / |F_x|) is the reference member's grain angle only where its grain IS the frame's x, which is the usual case and was the invariant until v0.74. A detail drawn at an angle gets the value alone: printing the decomposition there would be a formula that does not produce the number beside it.
        let axis-r = members.at(r).axis
        let beta-r = deg(grain-angle(line-k, axis-r))
        rows.push((
          if axis-r == 0 {
            // a residue of cos(90°) is not a component: tested against the resultant, not against zero, which printed «arctan(2.5/0)» for a pure shear force (v0.86)
            let ratio = if calc.abs(top.fx) < 1e-9 * calc.max(1, top.f) { "" } else { " = arctan(" + number-in-formula(calc.abs(top.fz)) + "/" + number-in-formula(calc.abs(top.fx)) + ")" }
            math-line("beta_" + str(r + 1) + " = arctan(abs(F_(z," + nr + ")) / abs(F_(x," + nr + ")))" + ratio + " = " + beta-r)
          } else {
            math-line("beta_" + str(r + 1) + " = " + beta-r)
          },
          none,
        ))
      }
      // The grain angles are measured against `axis`, each member's grain from the SCHEMA's x -- which is the frame F_x and F_z are themselves in. `local`, the angle from the reference member, is what theta_(r,j) prints above. The two were one number until v0.74, the reference member's grain BEING x; a detail drawn at an angle parts them (docs/domain/connections.md §3.3quinquies).
      let beta-parts = range(members.len()).map(j => math-line("beta_" + str(j + 1) + " = " + deg(grain-angle(line-k, members.at(j).axis))) + [ (] + [#member-name(j)] + [)])
      // As the moment's note: the hole is F's subscript, so the sentence is split on it.
      let grain-note = t-pattern("connection.grain_angle_note").split("{nr}")
      rows.push((
        [#t-label("force_grain_angle")] + h(0.35em) + join-rows(beta-parts) + h(0.35em) + footnote[β#sub[j]#colon-str() #grain-note.first()#sub[#nr]#grain-note.last()],
        none,
      ))
    }
    if rows.len() > 0 { annotated-rows(rows) }

    // Level 3: every fastener, the resultants bold -- numbered as in the figure and in the positions table above.
    if plan-at(plan, "forces_table", 3) >= 1 {
      let dash(x) = if x == none { "—" } else { calc.round(x, digits: angle-digits()) }
      let beta-columns = range(members.len()).map(j => (label: [$beta_#(j + 1)$], kind: "number", unit: "°"))
      render-table(
        (
          title: t-str("fastener_forces_title"),
          note: [$F_x$, $F_z$#colon-str() #t-str("connection.forces_note_head")#semicolon-str() #range(members.len()).map(j => [$beta_#(j + 1)$ #t-str("connection.to_member", member: member-name(j))]).join([, ])#colon-str() #t-str("force_grain_angle")#semicolon-str() $F$#colon-str() #t-str("connection.forces_note_tail").],
          columns: (
            (label: "Nr.", kind: "number"),
            (label: $F_x$, kind: "number", unit: "kN"),
            (label: $F_z$, kind: "number", unit: "kN"),
            ..beta-columns,
            (label: $F$, kind: "number", unit: "kN"),
          ),
          rows: forces.map(row => {
            let line = force-line(row.fx, row.fz)
            (row.nr, row.fx, row.fz, ..members.map(member => dash(grain-angle(line, member.axis))), row.f)
          }),
        ),
        bold-rows: governing.map(k => k - 1),
        bold-columns: (3 + members.len(),),
      )
    }
    if plan-at(plan, "worst_table", 3) >= 1 {
      // Level 3 also gives every fastener's force in the most unfavourable superposition (v0.35): N, V and the force from M added component by component with their magnitudes, as if all three acted the same way on it -- none of them relieving another. A symmetric group then carries the same force in every fastener, the largest the vector sum gives any of them. Its direction is not defined -- the signs were chosen, not calculated -- so no force-grain angle is given.
      let unfavourable = c.fasteners.enumerate().map(((i, p)) => {
        let fx = (calc.abs(nx) + calc.abs(vx)) / n + (if with-moment { calc.abs(m * (p.z - zc)) / ip } else { 0 })
        let fz = (calc.abs(nz) + calc.abs(vz)) / n + (if with-moment { calc.abs(m * (p.x - xc)) / ip } else { 0 })
        (nr: i + 1, fx: fx, fz: fz, f: calc.sqrt(fx * fx + fz * fz))
      })
      let u-max = calc.max(..unfavourable.map(row => row.f))
      let u-governing = unfavourable.filter(row => row.f >= u-max - 1e-9 * calc.max(1, u-max)).map(row => row.nr)
      render-table(
        (
          title: t-str("fastener_forces_worst_title"),
          formula: (
            "F_(x,i)^* = (abs(N_x) + abs(V_x))/n" + (if with-moment { " + (abs(M) dot abs(Delta z_i))/I_p" } else { "" }),
            "F_(z,i)^* = (abs(N_z) + abs(V_z))/n" + (if with-moment { " + (abs(M) dot abs(Delta x_i))/I_p" } else { "" }),
            "F_i^* = sqrt((F_(x,i)^*)^2 + (F_(z,i)^*)^2)",
          ),
          note: t-str("worst_case_note"),
          columns: (
            (label: "Nr.", kind: "number"),
            (label: $F_x^*$, kind: "number", unit: "kN"),
            (label: $F_z^*$, kind: "number", unit: "kN"),
            (label: $F^*$, kind: "number", unit: "kN"),
          ),
          rows: unfavourable.map(row => (row.nr, row.fx, row.fz, row.f)),
        ),
        bold-rows: u-governing.map(k => k - 1),
        bold-columns: (3,),
      )
    }
  }
}
}

// --- What verify prints through (docs/typst/formulas.md §10quinquies) -----
// show-check above prints a check the *data* carries: Python computed its status and a reviewer re-derives it from the export. The other half is `verify` in lib/formula.typ -- a comparison the engineer writes in the report itself, over the registry's variables. The constants below are what it prints through.
//
// It *performs* the comparison rather than trusting the eye, and it prints the two numbers it compared, so a verdict cannot contradict the values beside it and neither value is retyped (section 2, rule 1).
//
// ⚠️ The price, plainly: the verdict is **untraced**. It is not in data/, carries no `source`, is catalogued by no reference workbook, and no norm citation stands beside it -- the standing condition for any calculation done in Typst (section 1). A check a reviewer must re-derive from the data belongs in a Python domain, where its status is data and show-check prints it. Typst cannot call Python at compile time -- no shell, no FFI, only WASM plugins -- so a comparison written in the report is a comparison performed in the report.

// Green where it holds, red where it does not, named once so the whole report marks a verdict in one green. They join table-highlight as the engine's colour constants, and the colour goes on the rule and on the mark -- never on the digits.
#let test-ok = rgb("#1a7f37")
#let test-nok = rgb("#c0392b")

// A value shown otherwise than it is held is written in orange -- the one Woodcore's window writes an overridden value in (`OVERRIDE_COLOR` in connectors_tab.py and schema_tab.py, held equal by tests/test_constants.py), so that the window and the report say "written over" in the same colour. Today: the footnote `val` adds under a value printed in another unit than the one it carries (v0.80).
#let override-colour = rgb("#b35c00")

// Two numbers closer than this, relatively, are the same number: float noise must not fail a check that holds exactly (0.1 + 0.2 against 0.3). The absolute floor of 1 keeps that meaningful near zero. It is the rule show-polar-moment already uses to find the fasteners tied at the largest force, and the same constant.
#let test-tolerance = 1e-9
#let test-slack(a, b) = test-tolerance * calc.max(1, calc.abs(a), calc.abs(b))

// The relations verify accepts: the predicate it applies, and how the relation is set in math. `lt.eq.slant` is the slanted form engineering writes, and the one the report's own equations already use.
// A strict < or > takes the slack off the other side, so that two numbers the same within noise fail it. Testing it exactly instead would let `=` and `<` both hold of the same pair, which is the one thing a relation may not do.
#let test-relations = (
  "<=": (holds: (a, b) => a <= b + test-slack(a, b), math: "lt.eq.slant"),
  ">=": (holds: (a, b) => a >= b - test-slack(a, b), math: "gt.eq.slant"),
  "<": (holds: (a, b) => a < b - test-slack(a, b), math: "<"),
  ">": (holds: (a, b) => a > b + test-slack(a, b), math: ">"),
  "=": (holds: (a, b) => calc.abs(a - b) <= test-slack(a, b), math: "="),
  "!=": (holds: (a, b) => calc.abs(a - b) > test-slack(a, b), math: "eq.not"),
)

// The same relations as they may also be written.
#let test-aliases = ("≤": "<=", "≥": ">=", "≠": "!=", "==": "=")

// 👉 `test-operand` and `test` itself stood here until v0.61. They compared two values handed over as arguments,
// which meant every number was retyped at the call site and the two sides carried their units by hand. `verify`
// in lib/formula.typ replaced them: it reads its two sides out of the variable registry above, so nothing is
// retyped and the units come from the algebra. What survives here is what `verify` still prints through --
// the relation table, the tolerance and the two colours.

// --- The shear resistance of a connector (docs/domain/connectors.md §3.3nonies) --------
// A connector carries its own calculation since v0.68: data/connectors.json holds the descriptive half
// the Positions Connectors sheet used to, and beside it the ordinary {vars, steps, checks, tables,
// results} record, computed in Python from SIA 265 6.2.1 and Anhang A. So show-calc("connector", id)
// renders it generically, and this command is the one that lays it out the way an engineer reads a
// connection: what it is, then the drawing, then the answer.

// "4 × Ø 10 mm Stabdübel, C24 und C24" -- what the connection is, in one line, at every level.
#let connector-headline(c) = {
  let n = c.n_tot
  let d = c.diameter
  let grades = c.members
    .filter(m => m.role == "timber")
    .map(m => m.at("grade", default: ""))
    .filter(g => g != "")
  // the grades named once each, in the order the members are drawn
  let seen = ()
  for g in grades { if g not in seen { seen.push(g) } }
  // "Ø 10 mm" is never broken across a line, as connector-summary sets it
  let parts = ([#n × Ø\u{a0}#signed-text(fmt-decimals(d.value, 3))\u{a0}#d.unit #tl-str(c.type)],)
  if seen.len() > 0 { parts.push([#seen.join(" / ")]) }
  parts.push([#tl-str(c.assembly)])
  parts.join([, ])
}

// A connector's figure file for one language, or none while the export carries no drawing for it.
#let connector-figure-file(c, key) = {
  let figures = c.at("figures", default: (:))
  let entry = figures.at(key, default: none)
  if entry == none { return none }
  entry.at(report-lang(), default: entry.at("de", default: none))
}

// A connector's two drawings -- the pattern on its schema and the section through the joint -- side by side, each a figure of its own with its caption (v0.77, the engineer's request: until then one under the other, uncaptioned). `width` is the width the pair is set at. Each figure is aligned to the foot of its cell, so the two captions stand on one line whatever the drawings' heights.
#let connector-figures(c, connector, width) = {
  let cells = ()
  for (key, caption) in (("pattern", "connector.pattern_caption"), ("section", "connector.section_caption")) {
    let file = connector-figure-file(c, key)
    if file != none {
      let scaled = if key == "section" { c.at("section_scaled", default: "") } else { "" }
      // the section carries no word: a diameter drawn at a bound is said here, in the report's language
      let drawing = image("../data/" + file, width: 100%)
      if scaled in ("enlarged", "reduced") {
        drawing = stack(spacing: 0.3em, drawing, align(left, text(size: 8pt, fill: luma(40%), t-str("connector.section_" + scaled))))
      }
      cells.push(figure(drawing, caption: [#connector --- #t-str(caption)]))
    }
  }
  if cells.len() == 0 { return none }
  align(center, block(width: width, grid(columns: cells.len() * (1fr,), column-gutter: 1.5em, align: bottom, ..cells)))
}

/// Displays the design value of the shear resistance of one connector, SIA 265 6.2.1 (docs/domain/connectors.md §3.3nonies).
///
/// A connector is defined in Woodcore's connectors tab and calculated in Python; this lays the
/// record out the way a connection is read. Level 1 names the connection and gives R_d, R_d,Verb and the
/// connection's slip modulus K_ser,Verb, with
/// the minimum distances of Tabelle 24, laid out as `Verbindung.xlsm` lays them out; level 2 adds, side by side and each with its caption, the
/// detail schema the connector is drawn on, with its fasteners numbered on it, and the section through the joint; level 3 adds the whole chain --
/// f_h,alpha,k per member out of Tabelle 22, beta_f, M_u,k, the thicknesses and k_beta corners of
/// Tabellen 45/46, k_red per member, p · k_beta, the resistance and the Verschiebungsmodul, each as the
/// norm's own formula -- which is `show-calc("connector", id)`'s own walk.
///
/// ```typ
/// #show-connector-resistance("SD-10")
/// ```
///
/// ```typ
/// #show-connector-resistance("SD-10", level: 3, title: "Stabdübel Velo-Unterstand")
/// ```
///
/// ```typ
/// #show-connector-resistance("SD-10", level: -1, shown: (d: 1, R_d: 3, table-2: 1))
/// ```
///
/// - connector (str): the connector's id, e.g. "SD-10". An unknown id fails listing the valid ones; one the export could not calculate fails with the reason it carries.
/// - level (int, auto): 1, 2 or 3, or auto for the report's own level (section 4). -1 prints only what `shown:` names, each at its own level, beside the headline (v0.117).
/// - shown (dictionary, none): at `level: -1`, the vars and tables of the connector's calculation printed, `(R_d: 1, table-2: 1)` -- the keys show-calc reads -- and the figures where one is chosen at 2 or 3. none at any other level.
/// - title (str, auto, none): auto heads the block with the connector's id, none prints no heading, a string replaces it.
/// - width (relative): the width the two figures are set at, side by side.
/// -> content
#let show-connector-resistance(connector, level: auto, shown: none, title: auto, width: 100%) = context {
  if not (level in (auto, 1, 2, 3) or level == selection-level) {
    panic("show-connector-resistance: invalid level " + repr(level) + " -- use auto, 1, 2, 3, or -1 with shown:")
  }
  let known = load-connectors().connectors
  assert(type(connector) == str and connector in known,
    message: "show-connector-resistance: no connector " + repr(connector) + " -- " + (if known.len() == 0 { "none saved yet (create one in Woodcore's connectors tab)" } else { "valid connectors: " + known.keys().join(", ") }))
  let c = known.at(connector)
  if not c.calculated {
    panic("show-connector-resistance: connector '" + connector + "' carries no calculation -- " + c.reason + " Open it in Woodcore's connectors tab, put that right and export again.")
  }
  // at -1 (issue #20, v0.117) the keys are the connector's own calculation's, as show-calc reads them: its headline is printed as a title is, its figures where a key is chosen at 2 or 3, and its calculation is show-calc's at -1
  check-shown("show-connector-resistance", level, shown, c.vars.keys() + range(c.at("tables", default: ()).len()).map(i => "table-" + str(i + 1)), levels: (auto, 1, 2, 3))
  let plan = level-plan(level, shown)
  let eff-level = plan.lv

  let heading = if title == auto { connector } else if title == none { none } else { title }
  if heading != none {
    block(above: 1em, below: 0.7em, sticky: true, text(weight: "bold", heading))
  }

  // What the connection is, and what it is made of -- the same line at every level.
  let vars = c.vars
  annotated-rows(((connector-headline(c), vars.R_d_Verb),))
  show-connector(connector)
  parbreak()

  if plan-any(plan, 2) {
    let figures = connector-figures(c, connector, width)
    if figures != none { figures }
  }

  if plan.picked {
    show-calc(connector-domain, connector, level: selection-level, shown: plan.shown, title: none)
  } else if eff-level >= 3 {
    // The whole chain, in the order the data states it -- vars, steps and every table at its own level.
    show-calc(connector-domain, connector, level: eff-level, title: none)
  } else {
    // The answer, then the tables this level asks for.
    let rows = ()
    for name in c.results {
      rows.push((var-row(vars.at(name)).at(0), vars.at(name)))
    }
    // The connection's slip modulus under its resistance, at levels 1 and 2 too (the engineer, v0.84):
    // it is not one of the `results` -- those are the resistances a verification reads -- and it is what
    // a deformation calculation needs next, so it is printed beside them rather than left to level 3.
    // Guarded: an export written before v0.84 carries it at level 3 and a frozen one may not carry it
    // at all, and a documentation page must not panic over a var this level never asked for.
    if "K_ser_Verb" in vars and "K_ser_Verb" not in c.results {
      rows.push((var-row(vars.K_ser_Verb).at(0), vars.K_ser_Verb))
    }
    annotated-rows(rows)
    for tbl in c.at("tables", default: ()).filter(t => eff-level >= t.at("level", default: 3)) {
      render-table(tbl, vars: vars, results: c.results)
    }
  }

  // What the export could not keep quiet about: a count set by hand, a distance below Tabelle 24.
  let notes = c.at("warnings", default: ())
  if notes.len() > 0 and plan-any(plan, 2) {
    block(above: 0.8em, text(size: 0.85em, fill: rgb("#b35c00"),
      notes.map(n => render-prose(tl-str(n))).join(linebreak())))
  }
}
