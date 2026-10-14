// The bibliography: every norm and document the report cites, listed in full at the end of it (v0.99).
//
// A citation in the right-hand column stays exactly what it was -- «SIA 265 §4.2.1», the designation and the clause, which is what a reader checks a line against (docs/typst/citations.md §10). What it did not say is *which* SIA 265: its title, its edition, its publisher. So a citation is now **registered as it is made**, and `#show-bibliography` prints, at the end, the four fields of each document actually cited: its designation, its full title, its edition and its publisher.
//
// ⚠️ It is not Typst's own `#cite`/`#bibliography`, and deliberately: those set a citation as a key in the text («[1]», «SIA265») and a CSL style decides how, which is neither the form this report cites in nor a form a checking engineer reads. The engineer's rule was that **no existing page moves** -- so nothing here touches how a citation is printed, and a report that never calls `#show-bibliography` is the report it was.
//
// Where the entries come from, in this order:
//
//   * **`calc/norms/norms.json`**, the documents the engine knows -- read through the relative path `../calc/norms/`, the way `lib/distance.typ` reads its tables, so it resolves in the program and in a project's `_woodcore/` alike. `calc/norms/norms.py` checks the same file before an export reads anything, and `tests/test_bibliography.py` holds the two lists equal;
//   * **the project's own `references.bib`**, named by `project:`, at the Typst root -- the project's top folder, shared by the project's documents (in a project laid out before there were three documents, the report's folder, which was the root) -- a manufacturer's ETA, an office handbook, a course document. It wins over the engine's catalogue for a key both carry, a project knowing its own editions best;
//   * **nothing**, for a citation neither names: it is printed as it was cited, in a third block of its own. A citation without an entry is never lost and never invented.
//
// What is registered, and where. A citation reaches the page from five places (section 10quinquies, 3.3): the `norm` field of a record of the export, `norm-text` in calc-engine.typ, `lib/distance.typ`, `lib/timber.typ`, and the `norm:` argument of `var`, `eq`, `val`, `var-unit` and `var-line`. They are covered two ways rather than one:
//
//   * **the data is walked** (`bib-of-data`): every `norm` field of `data/calculations.json`, `data/connections.json` and `data/connectors.json`. That is what covers `show-calc`, `show-input`, `show-polar-moment`, `show-connector-resistance` and `show-live-load` at once, with no edit to any of them -- and it is why the walk is the default;
//   * **what the report writes by hand is registered** at the call: `var`, `eq`, `val`, `var-unit` and `var-line` register their `norm:`, `distance` registers SIA 265, `cite-norm` registers what it cites. `timber.typ`'s checks need nothing of their own: every one of them cites through `var(..., norm: "SIA 265")` and `eq(..., norm: "SIA 265")`. Neither does `verify`, which prints no citation at all.
//
// ⚠️ **A registration is emitted before its command's `context`, never inside one.** A state written inside a context is read back by a later context and *not* by the folded chain an update function reads -- the panne section 3.3quinquies records for v0.85, where `show-polar-moment` published its forces from inside its own context and `find`, `val` and `verify` saw them while `eq` did not. `bib-note` therefore returns content, and every caller emits it at the top of its body, outside every context and outside anything that is `measure`d.
//
// ⚠️ `state.final()` is what lets the list be printed anywhere and still hold what the whole document cited -- one convergence pass more, which Typst carries.

// It imports from calc-engine.typ and from nothing else, which is what keeps the chain calc-engine -> bibliography -> distance -> formula acyclic: formula.typ imports this file's two commands by name, as it imports `distance` and the member checks (docs/typst/api-conventions.md §10bis point 3).
#import "calc-engine.typ": norm-text, report-lang, t-str

// --- What the report has cited ---------------------------------------------

// Every citation string the report has made, in the order it first made them. A plain array and not a set: Typst has none, and the order is what a test reads.
#let bib-cited = state("bibliography-cited", ())

/// Registers one citation, so that `#show-bibliography` lists the document it names -- and prints nothing.
///
/// It is what the commands that carry a `norm:` emit, and it is the one piece of this file that a caller outside it needs. ⚠️ Emit it **before** the command's `context`, never inside one: a state written inside a context is read back by a later context and not by the folded chain a `state.update` reads (docs/domain/connections.md §3.3quinquies).
///
/// - norm (str, none): the citation as it is written -- «SIA 265», «bauforumstahl, Arbeitshilfe: …». Anything else, and `none`, registers nothing.
/// -> content
#let bib-note(norm) = {
  if type(norm) != str or norm.trim() == "" { return [] }
  let norm = norm.trim()
  bib-cited.update(seen => if norm in seen { seen } else { seen + (norm,) })
}

// --- The engine's own catalogue ---------------------------------------------

// Where the catalogue is, seen from this file -- calc/norms/, beside lib/ in the program and in a project's _woodcore/ alike.
#let bib-dir = "../calc/norms/"
#let bib-file = "norms.json"

// The two blocks an entry may claim, and the third the report gives a citation no entry names. calc/norms/norms.py's KINDS is the first two.
#let bib-kinds = ("norm", "literature")
#let bib-blocks = ("norm", "literature", "other")

// The entries the engine knows: calc/norms/norms.json, as calc/norms/norms.py checks it. Nothing is validated again here -- a defective file stops an export long before a report is compiled.
#let bib-catalogue() = json(bib-dir + bib-file).references

// --- The project's own references.bib ---------------------------------------
//
// A subset of BibTeX, and one that says what it does not read rather than swallowing it: `@type{key, field = {value}, field = "value", field = 1234}`, one entry per document, braces balanced. `@comment` is skipped; `@string` and `@preamble` are **refused**, since a string macro changes how every value after it is read and skipping one would misread the file. Any other `@type` the table below does not name is refused with the list. A field the table does not name is ignored -- `author`, `address`, `isbn`, `url` are welcome and unread -- so a .bib written for something else can be used as it is.
//
// ⚠️ A value is a **string** and is printed exactly as the file writes it: no TeX is interpreted, so an en dash is typed as one and not as `--`, `{\"a}` prints as it stands, and `$...$` is not read as math either. That is the same promise `render-prose` makes of a description typed into Excel, one step further: nothing the engineer types into a title can change the page around it.
//
// The entry type says the block, and `kind = {norm}` or `kind = {literature}` overrides it: a bibliography's two blocks are not a BibTeX notion, and the entry is what has to know which it belongs to.

// ⚠️ An empty array joined is `none` in Typst and not the empty string, so every run of clusters this reader gathers goes through here. Without it a stray `@` at the end of a file, an empty key `@book{,`, an empty field name or an empty value failed on «type none has no method `trim`» instead of being refused with its line.
#let bib-join(parts) = if parts.len() == 0 { "" } else { parts.fold("", (a, b) => a + b) }

#let bib-ws = (" ", "\t", "\n", "\r")

// What a field's name is made of. A set of clusters and not a regex: this is asked once per character of the file, and compiling a pattern that often is work for nothing.
#let bib-name-chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-".clusters()

// The entry types this reader knows, and the block each falls into.
#let bib-bibtex-kinds = (
  "standard": "norm", "norm": "norm", "techreport": "norm", "report": "norm", "legislation": "norm",
  "book": "literature", "inbook": "literature", "incollection": "literature", "article": "literature",
  "inproceedings": "literature", "conference": "literature", "manual": "literature", "booklet": "literature",
  "thesis": "literature", "phdthesis": "literature", "mastersthesis": "literature",
  "misc": "literature", "online": "literature", "electronic": "literature", "unpublished": "literature",
)

// The types that change how the file is read, and so may not be passed over.
#let bib-bibtex-refused = ("string", "preamble")

// Which field of an entry fills which of the four printed ones. The first one present wins, in this order.
#let bib-bibtex-fields = (
  "title": ("title", "booktitle"),
  "edition": ("edition", "year", "date"),
  "publisher": ("publisher", "organization", "institution", "school", "howpublished"),
  "designation": ("designation", "number", "series"),
)

// The line a cluster index falls on, for a refusal that names where it is.
#let bib-line-at(cs, i) = cs.slice(0, calc.min(i, cs.len())).filter(c => c == "\n").len() + 1

#let bib-refuse(cs, i, path, what) = {
  panic("references.bib (" + path + "), line " + str(bib-line-at(cs, i)) + ": " + what)
}

#let bib-skip-ws(cs, i) = {
  let i = i
  while i < cs.len() and cs.at(i) in bib-ws { i += 1 }
  i
}

// One value: `{...}` with its braces balanced, `"..."`, or a bare run of characters up to the next comma or closing brace. Returns (text, index after it).
#let bib-read-value(cs, i, path) = {
  let i = bib-skip-ws(cs, i)
  if i >= cs.len() { bib-refuse(cs, i, path, "a field has no value -- the file ends here") }
  let open = cs.at(i)
  // `{...}`, with its braces balanced so that a title may carry one
  if open == "{" {
    // ⚠️ The braces **inside** a value are dropped, as BibTeX drops them: there they protect a capital from a style that would lower it, and this reader lowers nothing, so `{Titel}` is the word and not the word in braces. Only the balance is counted, so a title may carry as many as it likes.
    let depth = 1
    let out = ()
    let j = i + 1
    while j < cs.len() {
      let ch = cs.at(j)
      if ch == "{" { depth += 1 } else if ch == "}" {
        depth -= 1
        if depth == 0 { return (bib-join(out).trim(), j + 1) }
      } else { out.push(ch) }
      j += 1
    }
    bib-refuse(cs, i, path, "a value opened with `{` is never closed")
  }
  // `"..."`
  if open == "\"" {
    let out = ()
    let j = i + 1
    while j < cs.len() {
      if cs.at(j) == "\"" { return (bib-join(out).trim(), j + 1) }
      out.push(cs.at(j))
      j += 1
    }
    bib-refuse(cs, i, path, "a value opened with `\"` is never closed")
  }
  // a bare value: a year, a number, a single word
  let out = ()
  let j = i
  while j < cs.len() and not (cs.at(j) in (",", "}")) {
    out.push(cs.at(j))
    j += 1
  }
  let text = bib-join(out).trim()
  if text == "" { bib-refuse(cs, i, path, "a field has no value") }
  (text, j)
}

// One entry, from the `@`. Returns (entry or none, index after it) -- none for an `@comment`, which is passed over.
#let bib-read-entry(cs, i, path) = {
  let start = i
  let j = i + 1
  let word = ()
  while j < cs.len() and cs.at(j) not in bib-ws and not (cs.at(j) in ("{", "(")) {
    word.push(cs.at(j))
    j += 1
  }
  let kind = lower(bib-join(word))
  if kind == "comment" {
    // read it to its closing brace and pass over it
    let j = bib-skip-ws(cs, j)
    if j < cs.len() and cs.at(j) == "{" {
      let (_, after) = bib-read-value(cs, j, path)
      return (none, after)
    }
    return (none, j)
  }
  if kind in bib-bibtex-refused {
    bib-refuse(cs, start, path, "@" + kind + " is not read here -- this reader has no string macros, and passing one over would misread every value after it. Write each value out in its own entry.")
  }
  if not (kind in bib-bibtex-kinds) {
    bib-refuse(cs, start, path, "@" + kind + " is not an entry type this reader knows -- they are " + bib-bibtex-kinds.keys().map(k => "@" + k).join(", "))
  }
  let j = bib-skip-ws(cs, j)
  if j >= cs.len() or cs.at(j) != "{" {
    bib-refuse(cs, j, path, "@" + kind + " is not followed by `{` -- an entry is written `@" + kind + "{key, field = {value}}`, with braces and not parentheses")
  }
  j += 1
  // the key, up to the first comma
  let key = ()
  while j < cs.len() and not (cs.at(j) in (",", "}")) {
    key.push(cs.at(j))
    j += 1
  }
  let cite = bib-join(key).trim()
  if cite == "" { bib-refuse(cs, start, path, "@" + kind + " has no key -- the key is the string a citation writes, `@" + kind + "{Sherpa, …}`") }
  let fields = (:)
  while j < cs.len() and cs.at(j) == "," {
    j = bib-skip-ws(cs, j + 1)
    if j < cs.len() and cs.at(j) == "}" { break }  // a trailing comma
    let name = ()
    while j < cs.len() and cs.at(j) in bib-name-chars {
      name.push(cs.at(j))
      j += 1
    }
    let field = lower(bib-join(name))
    if field == "" { bib-refuse(cs, j, path, "expected a field name in @" + kind + "{" + cite + "}") }
    let j2 = bib-skip-ws(cs, j)
    if j2 >= cs.len() or cs.at(j2) != "=" {
      bib-refuse(cs, j2, path, "the field " + repr(field) + " of " + repr(cite) + " is not followed by `=`")
    }
    let (value, after) = bib-read-value(cs, j2 + 1, path)
    fields.insert(field, value)
    j = bib-skip-ws(cs, after)
  }
  if j >= cs.len() or cs.at(j) != "}" {
    bib-refuse(cs, start, path, "the entry " + repr(cite) + " is never closed")
  }
  let pick(names) = {
    let found = names.filter(n => n in fields)
    if found.len() == 0 { none } else { fields.at(found.first()) }
  }
  let title = pick(bib-bibtex-fields.title)
  if title == none or title.trim() == "" {
    bib-refuse(cs, start, path, "the entry " + repr(cite) + " has no `title` -- a bibliography's line is its designation and its title")
  }
  let block = fields.at("kind", default: bib-bibtex-kinds.at(kind))
  if not (block in bib-kinds) {
    bib-refuse(cs, start, path, "the entry " + repr(cite) + " says kind = " + repr(block) + " -- a bibliography's block is " + bib-kinds.map(k => repr(k)).join(" or "))
  }
  let aliases = if "aliases" in fields { fields.aliases.split(",").map(a => a.trim()).filter(a => a != "") } else { () }
  ((
    key: cite,
    aliases: aliases,
    kind: block,
    designation: pick(bib-bibtex-fields.designation),
    title: title,
    edition: pick(bib-bibtex-fields.edition),
    publisher: pick(bib-bibtex-fields.publisher),
  ), j + 1)
}

// Every entry of one .bib file. `path` is read from the Typst root -- the project's top folder, or the report's folder in a project laid out before there were three documents -- so it resolves from whatever file the call is written in, and whichever of the project's documents the call is in.
#let bib-read-file(path) = {
  // ⚠️ The line endings are normalised **before** the text is cut into clusters, and that is not tidiness: `\r\n` is **one** grapheme cluster, so on a file saved on Windows -- which is every file the engineer saves -- no cluster ever equals `"\n"`. A reader without this line counted every refusal's line as 1, stopped skipping a `%` comment at the first line, and refused every entry written over more than one line as «never closed». Found by the test that plants a defect on line 3.
  let cs = read(if path.starts-with("/") { path } else { "/" + path }).replace("\r\n", "\n").replace("\r", "\n").clusters()
  let out = ()
  let i = 0
  while i < cs.len() {
    // ⚠️ `%` comments to the end of the line, as BibTeX's own does, and is skipped **before** the search for `@`: a commented-out entry -- «% @book{…}» -- would otherwise be read as an entry, which is the one way this scanner could silently find something nobody wrote.
    if cs.at(i) == "%" {
      while i < cs.len() and cs.at(i) != "\n" { i += 1 }
    } else if cs.at(i) == "@" {
      let (entry, after) = bib-read-entry(cs, i, path)
      if entry != none { out.push(entry) }
      i = after
    } else { i += 1 }
  }
  out
}

// --- Finding the entry one citation names -----------------------------------

// One index from every string a citation may write to its entry. ⚠️ The project's entries are read **first** and the first one found wins, so a project that states its own edition of a document overrides the engine's catalogue -- a project knows which edition it was calculated against.
#let bib-index(project) = {
  let index = (:)
  for entry in project + bib-catalogue() {
    for name in (entry.key,) + entry.at("aliases", default: ()) {
      if not (name in index) { index.insert(name, entry) }
    }
  }
  index
}

// --- The citations the export carries ---------------------------------------

// The exported records a `norm` field can stand in. The drawings are left out: a plan, a static model and a detail schema compute nothing and cite nothing (docs/domain/position-plans.md §3.3sexies, docs/domain/static-models.md §3.3octies, docs/domain/detail-schemas.md §3.3decies). ⚠️ A position's own `domains` is `{}` today; when one carries a calculation, the positions join this list, read through positions-index.json -- Typst cannot list a directory (section 7).
#let bib-data-files = ("calculations", "connections", "connectors")

// Every `norm` a record carries, wherever it sits in it: on the instance, on a var, on a step, on a check, on a table. Walked rather than read at the six places section 3.3 names, so a field added to the export is covered without an edit here.
#let bib-walk(node) = {
  if type(node) == dictionary {
    let out = if type(node.at("norm", default: none)) == str { (node.norm.trim(),) } else { () }
    for (_, value) in node {
      if type(value) in (dictionary, array) { out = (out + bib-walk(value)).dedup() }
    }
    out
  } else if type(node) == array {
    let out = ()
    for value in node {
      if type(value) in (dictionary, array) { out = (out + bib-walk(value)).dedup() }
    }
    out
  } else { () }
}

#let bib-of-data() = {
  let out = ()
  for name in bib-data-files {
    out = (out + bib-walk(json("../data/" + name + ".json"))).dedup()
  }
  out.filter(n => n != "")
}

// --- Printing ---------------------------------------------------------------

// One of an entry's texts in the report's language: the language it asks for, else German, else the one the document prints. A document printed in one language only carries one text, and that one is printed in every report (docs/typst/language.md §4bis).
#let bib-text(value, lang) = {
  if value == none { return none }
  if type(value) == str { return value }
  for candidate in (lang, "de") { if candidate in value { return value.at(candidate) } }
  if value.len() == 0 { return none }
  value.at(value.keys().sorted().first())
}

// What a line opens with -- always a string, so that a block never mixes two types under `sorted`.
#let bib-designation(item) = {
  let entry = item.entry
  let d = if entry == none { none } else { entry.at("designation", default: none) }
  if d == none or d.trim() == "" { item.cited } else { d }
}

// What sorts a block, which is not the designation as it stands. Two things a reader expects and codepoint order does not give:
//
//   * **a norm before its supplement** -- «SIA 261:2020» before «SIA 261/1:2020», where `/` (0x2F) sorts before `:` (0x3A) and put the supplement first. The colon that opens the edition is mapped below every printable character, so what the two designations share ends at the colon and the shorter one wins;
//   * **the case ignored** -- «bauforumstahl» belongs among the b's and not after «STE Compact 02», which a lowercase `b` (0x62) against an uppercase `S` (0x53) gave.
#let bib-sort-key(item) = lower(bib-designation(item)).replace(":", "\u{1}")

// One line of the bibliography: **designation** — title. publisher, edition.
//
// The dash is a long one, as every separating dash the report prints is (docs/decisions.md §13, v0.88); the dashes inside a title are the document's own and are left as it writes them. The edition is left off the line where the designation already ends on it -- «SIA 261:2020 … , 2020.» says it twice.
#let bib-line(item, lang) = {
  let entry = item.entry
  // a citation no entry names: printed as it was cited, and nothing invented around it
  if entry == none { return strong(item.cited) }
  let designation = bib-designation(item)
  let title = bib-text(entry.at("title", default: none), lang)
  let publisher = bib-text(entry.at("publisher", default: none), lang)
  let edition = bib-text(entry.at("edition", default: none), lang)
  let tail = ()
  if publisher != none and publisher.trim() != "" { tail.push(publisher) }
  if edition != none and edition.trim() != "" and not designation.ends-with(edition) { tail.push(edition) }
  // built by concatenation and never in markup: a title is a string, and `#title.` in markup reads the dot as a field access
  let out = strong(designation)
  if title != none and title.trim() != "" { out = out + [ — ] + title + [.] }
  if tail.len() > 0 { out = out + [ ] + tail.join(", ") + [.] }
  out
}

/// **Every norm and document the report cites, listed in full** -- its designation, its full title, its edition and its publisher, in three blocks: the norms, the literature, and the documents no entry names (v0.99).
///
/// A citation stays exactly what it was where it is made -- «SIA 265 §4.2.1» in the right-hand column, «SIA 265 Tabelle 24» beside a table of distances -- and is *registered* as it is made. This prints what was registered, and nothing else: a norm the report never cites is never listed, and a norm cited without an entry is listed as it was cited.
///
/// ```typ
/// #show-bibliography()
/// ```
///
/// ```typ
/// In #cite-norm(norm: "SIA 265", norm-ref: "4.2.2.1") steht der Nachweis auf Druck.
///
/// #show-bibliography(data: false)
/// ```
///
/// Where the entries come from: `calc/norms/norms.json`, the documents the engine knows, and the project's own `references.bib` where `project:` names one, which wins for a key both carry. A document neither names is printed as it was cited.
/// - data (bool): also list what the export cites -- every `norm` field of `data/calculations.json`, `data/connections.json` and `data/connectors.json`, which is what `show-calc`, `show-polar-moment`, `show-connector-resistance` and `show-live-load` print. `false` lists only what the report registered at a call, which is narrower and does not see a calculation the report has not printed either.
/// - project (str, none): the project's own `references.bib`, as a path from the Typst root -- the project's top folder, where the project's documents share one -- `"references.bib"`. `none` reads none, which is why a project without one compiles.
/// - blocks (array, auto): which blocks to print, in order: `"norm"`, `"literature"`, `"other"`. `auto` prints the three.
/// - heading (int, none): `none` names each block in bold on a line of its own, which keeps the outline the engineer's (section 4bis); an integer sets the names as headings of that level.
/// -> content
#let show-bibliography(data: true, project: none, blocks: auto, heading: none) = {
  assert(type(data) == bool, message: "show-bibliography: data: is true or false, got " + repr(data))
  assert(project == none or type(project) == str,
    message: "show-bibliography: project: names the project's references.bib as a path from the Typst root -- the project's top folder (\"references.bib\"), got " + repr(project))
  assert(heading == none or type(heading) == int,
    message: "show-bibliography: heading: is none (each block named in bold) or the level of a heading, got " + repr(heading))
  let blocks = if blocks == auto { bib-blocks } else { blocks }
  assert(type(blocks) == array, message: "show-bibliography: blocks: is an array of " + bib-blocks.map(b => repr(b)).join(", ") + ", got " + repr(blocks))
  for b in blocks {
    assert(b in bib-blocks, message: "show-bibliography: " + repr(b) + " is not a block -- they are " + bib-blocks.map(x => repr(x)).join(", "))
  }
  context {
    let lang = report-lang()
    let entries = if project == none { () } else { bib-read-file(project) }
    let index = bib-index(entries)
    let cited = (bib-cited.final() + (if data { bib-of-data() } else { () })).dedup()
    let items = cited.map(c => (cited: c, entry: index.at(c, default: none)))
    // ⚠️ `kind` and not `block`: a loop variable named `block` would shadow Typst's own `block()` for the whole body, which is what sets the lines below.
    for kind in blocks {
      let here = items.filter(i => (if i.entry == none { "other" } else { i.entry.kind }) == kind)
      if here.len() == 0 { continue }
      let name = t-str("bibliography." + kind)
      if heading == none {
        block(above: 1.2em, below: 0.6em, strong(name))
      } else {
        std.heading(level: heading, name)
      }
      for item in here.sorted(key: bib-sort-key) {
        block(above: 0.5em, below: 0.5em, bib-line(item, lang))
      }
    }
  }
}

/// Cites a norm **in the prose**, as the right-hand column cites one, and registers it for the bibliography (v0.99).
///
/// A clause takes its §, a table and an annex take the report's own word and none -- `norm-text`'s rule, so a citation in a sentence and a citation in the right-hand column are set alike. The document is registered whether or not a clause is printed with it.
///
/// ```typ
/// Die Baustoffe sind nach #cite-norm(norm: "VKF 14-15", norm-ref: "2.5.3") zu verwenden.
/// ```
///
/// ```typ
/// #cite-norm(norm: "SIA 265", norm-ref: "Tabelle 8")
/// #cite-norm(norm: "SIA 261", norm-ref: "Anhang D")
///
/// #show-bibliography(data: false)
/// ```
///
/// - norm (str): the document, as the bibliography's entries name it -- «SIA 265», «VKF 14-15».
/// - norm-ref (str): the clause, the table or the annex, without its § -- `""` cites the document as a whole.
/// -> content
#let cite-norm(norm: none, norm-ref: "") = {
  assert(type(norm) == str and norm.trim() != "",
    message: "cite-norm: write the document it cites, #cite-norm(norm: \"SIA 265\", norm-ref: \"4.2.2.1\") -- got " + repr(norm))
  assert(type(norm-ref) == str,
    message: "cite-norm: norm-ref: is the clause as a string, without its §, or \"\" for the document as a whole -- got " + repr(norm-ref))
  bib-note(norm) + context norm-text((norm: norm.trim(), norm_ref: norm-ref.trim()))
}
