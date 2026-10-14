// The parametric objects of a project's documents -- the convention d'utilisation, the base de projet and the statical report (the three document modes, phase 3): the tables, the live loads and the non-structural self-weight, a labelled field, a list to tick, a single choice, a picture, an extract of a position plan, the signatures and the norms a section names.
//
// Each command is one object. Woodcore writes it between two tags of the section's own .typ file -- `// woodcore:object <command> <id>` and `// woodcore:/object <id>`, a line each -- as one call in the canonical form its editor parses and writes back: one named argument per line, a trailing comma everywhere, the arguments in the order each signature below states them. **The .typ is the source of truth**: an object written by hand is the same call, and prints the same. Nothing here reads the tags; they are the editor's.
//
// ⚠️ **The engineer's own words are content and are never looked up in the glossary**, which is the rule the journal's free text follows (v0.99): a title, a cell, a caption, a label, a note is printed exactly as it is written -- a string included, which is wrapped as content before it reaches `render-table` -- so a use typed «Element 3» cannot match a template of the glossary and come out translated. What the engine says of its own accord -- a column's default heading, the line saying what orange means, a placeholder -- is `calc/i18n/strings.json`'s, in the report's language.
//
// ⚠️ **A table is set as every table of this engine is**, by `render-table` (docs/domain/calculation-domains.md §3.3): three rules and nothing else, a column aligned by what it holds. Only a table without its heading row -- a list of terms and what they are -- is laid out here, with the same rules, the same insets and the same alignments, render-table always setting a heading row.
//
// ⚠️ formula.typ imports the eleven commands from here by name, which is how commands.typ gives every section these and none of the helpers. Nothing is imported back from formula.typ: a value quoted in a cell is `doc-value`'s, which reads the registry and the export through calc-engine.typ's own lookups -- so the chain calc-engine -> bibliography -> document -> formula is acyclic, with no import inside a body (the live-load table imported `val` inside its own until `doc-value` stood in for it).
#import "calc-engine.typ": colon-str, column-align, column-width, find-calculation, fmt-number, live-load-domain, load-calculations, override-colour, render-table, report-lang, rule-thick, show-annexes, show-extract, show-fire-plan, show-plan, source-label, t-str, table-figure, table-spacing, var-lookup, var-names, var-registry
#import "bibliography.typ": bib-index, bib-line, bib-note, bib-read-file

// --- Refusals and shapes ------------------------------------------------------------------
//
// An argument that is not what the command takes is refused naming the command and what to write, never passed over: an object Woodcore cannot read back is one its editor would silently rewrite. Every refusal is a `panic` inside an `if` and never `assert(cond, message: ...)`, whose message Typst builds before it tests the condition (v0.63.1).

#let doc-refuse(fn, message) = panic(fn + ": " + message)

// What a column's id is made of: letters, digits, `_` and `-` -- a Typst dictionary key, so that a row can name it bare, `(q_k: auto)`.
#let doc-id-pattern = regex("^[A-Za-z][A-Za-z0-9_-]*$")

// The keys a dictionary argument may carry. A key it does not take is a typo -- `titel:` for `title:` -- and a field nobody reads.
#let doc-keys(fn, what, d, allowed) = {
  for k in d.keys() {
    if not (k in allowed) {
      doc-refuse(fn, what + " carries " + repr(k) + ", which it does not take -- it takes " + allowed.map(a => repr(a)).join(", "))
    }
  }
}

// A text argument: none, content or a string -- the engineer's words either way.
#let doc-text-arg(fn, what, x) = {
  if x != none and type(x) != content and type(x) != str {
    doc-refuse(fn, what + " is [content] or a string -- got " + repr(x))
  }
}

// The engineer's words as content, never looked up: a string wrapped as it is, content passed through.
#let doc-words(x) = if x == none { [] } else if type(x) == str { [#x] } else { x }

// One cell of a row. A number is printed as every number of this engine is -- at the document's decimals, with a real minus sign -- and its unit is the column's, in the heading; a string and content are the engineer's words. `auto` is refused where the column has nothing to fill it from.
#let doc-cell(fn, row, id, cell) = {
  if cell == none { [] } else if type(cell) == content { cell } else if type(cell) == str { [#cell] } else if type(cell) in (int, float) {
    fmt-number(cell, "")
  } else if cell == auto {
    doc-refuse(fn, "row " + str(row + 1) + ", column " + repr(id) + ": auto has nothing to be filled from in this column -- write the value")
  } else {
    doc-refuse(fn, "row " + str(row + 1) + ", column " + repr(id) + " is [content], a string, a number or none -- got " + repr(cell))
  }
}

// --- Columns, hidden columns, rows ----------------------------------------------------------

#let doc-column-keys = ("id", "title", "unit", "kind")
#let doc-kinds = ("text", "number", "math", "wide")

// The columns of a table, checked: (id, title, unit, kind, known) each. `defaults` is the command's own table of the columns it knows by id -- their heading, their unit, their kind -- which is what lets a known column leave its `title:` out.
#let doc-columns(fn, columns, defaults: (:)) = {
  if type(columns) != array {
    doc-refuse(fn, "columns: is an array of (id: \"...\", title: [...]) -- got " + repr(columns))
  }
  let seen = ()
  let out = ()
  for (i, c) in columns.enumerate() {
    let where = "column " + str(i + 1)
    if type(c) != dictionary {
      doc-refuse(fn, where + " is (id: \"...\", title: [...]) -- got " + repr(c))
    }
    doc-keys(fn, where, c, doc-column-keys)
    let id = c.at("id", default: none)
    if type(id) != str or id.match(doc-id-pattern) == none {
      doc-refuse(fn, where + ": id: is letters, digits, `_` and `-`, starting with a letter -- got " + repr(id))
    }
    if id in seen { doc-refuse(fn, "two columns are called " + repr(id) + " -- an id names one column") }
    seen.push(id)
    let known = defaults.at(id, default: none)
    let title = c.at("title", default: none)
    doc-text-arg(fn, "column " + repr(id) + ": title:", title)
    if title == none and known == none {
      doc-refuse(fn, "column " + repr(id) + " has no title: -- write one, (id: " + repr(id) + ", title: [...])"
        + (if defaults.len() > 0 { "; the columns known by their id alone are " + defaults.keys().map(k => repr(k)).join(", ") } else { "" }))
    }
    let unit = c.at("unit", default: none)
    if unit != none and type(unit) != str { doc-refuse(fn, "column " + repr(id) + ": unit: is a string, \"kN/m²\" -- got " + repr(unit)) }
    let kind = c.at("kind", default: none)
    if kind != none and not (kind in doc-kinds) {
      doc-refuse(fn, "column " + repr(id) + ": kind: is " + doc-kinds.map(k => repr(k)).join(", ") + " -- got " + repr(kind))
    }
    out.push((id: id, title: title, unit: unit, kind: kind, known: known))
  }
  out
}

#let doc-hidden(fn, hidden, ids) = {
  if type(hidden) != array {
    doc-refuse(fn, "hidden: is an array of column ids -- " + (if type(hidden) == str { "write (" + repr(hidden) + ",) for one" } else { "got " + repr(hidden) }))
  }
  for h in hidden {
    if type(h) != str or not (h in ids) {
      doc-refuse(fn, "hidden: names " + repr(h) + ", which is not a column -- the columns are " + ids.map(i => repr(i)).join(", "))
    }
  }
}

#let doc-rows(fn, rows, ids) = {
  if type(rows) != array { doc-refuse(fn, "rows: is an array of (column: value, ...) -- got " + repr(rows)) }
  for (i, r) in rows.enumerate() {
    if type(r) != dictionary { doc-refuse(fn, "row " + str(i + 1) + " is (column: value, ...) -- got " + repr(r)) }
    for k in r.keys() {
      if not (k in ids) {
        doc-refuse(fn, "row " + str(i + 1) + " names the column " + repr(k) + ", which the table does not have -- its columns are " + ids.map(x => repr(x)).join(", "))
      }
    }
  }
}

// The heading of one column, as render-table reads a column: a title the call gives is printed as it is written, with the unit the call gives; a column known by its id takes its default heading -- a word of the glossary in the report's language, or a symbol set as math -- and its default unit. Call inside `context`: a word reads the report's language.
#let doc-column-spec(c) = {
  let known = if c.known == none { (:) } else { c.known }
  let kind = if c.kind != none { c.kind } else { known.at("kind", default: "text") }
  if c.title != none {
    (label: doc-words(c.title), kind: kind, unit: if c.unit != none { c.unit } else { "" })
  } else {
    let unit = if c.unit != none { c.unit } else { known.at("unit", default: "") }
    if "math" in known {
      (label: known.math, label_math: known.math, kind: kind, unit: unit)
    } else {
      (label: [#t-str(known.word)], kind: kind, unit: unit)
    }
  }
}

// The small print under a table: the call's notes, one line each, then the line saying what orange means where a cell was written over. Call inside `context`.
#let doc-note(fn, notes, overridden) = {
  let lines = if notes == none { () } else if type(notes) == array { notes } else { (notes,) }
  for n in lines { doc-text-arg(fn, "notes:", n) }
  let out = lines.map(doc-words)
  if overridden { out.push(text(fill: override-colour, t-str("document.override"))) }
  if out.len() == 0 { none } else { out.join(linebreak()) }
}

// A table without its heading row -- a list of terms and what they are -- set with render-table's own rules, insets and alignments: a thick rule above the first row and under the last, and nothing else. render-table always sets a heading row, which is the one thing a key-value table has no use for.
// Its title is a numbered caption above it, as every table's is (table-figure), centred over the table, which keeps its place at the left.
#let doc-plain-table(specs, body, title, note) = block(above: table-spacing, below: table-spacing, breakable: true, {
  let lines = {
    set par(justify: false)
    table(
      columns: specs.map(s => column-width(s.kind)),
      stroke: none,
      inset: (x: 5pt, y: 4pt),
      align: specs.map(s => column-align(s.kind)),
      table.hline(stroke: rule-thick),
      ..body.flatten(),
      table.hline(stroke: rule-thick),
    )
  }
  let rest = {
    lines
    if note != none {
      v(0.25em, weak: true)
      text(size: 7.5pt, style: "italic", note)
    }
  }
  if title == none { rest } else {
    layout(size => {
      let width = calc.min(measure(lines, width: size.width).width, size.width)
      table-figure(title, width, rest)
    })
  }
})

// Prints one table of the document, its hidden columns left out. Call inside `context`.
#let doc-print-table(fn, shown, body, caption, notes, overridden, header: true) = {
  if shown.len() == 0 { return [] }
  let specs = shown.map(doc-column-spec)
  let note = doc-note(fn, notes, overridden)
  let title = if caption == none { none } else { doc-words(caption) }
  // ⚠️ **A narrow column is hyphenated**, as `show-journal`'s is: a table's cells are set ragged (`render-table`), Typst's `hyphenate: auto` hyphenates only what it justifies, and the engineer's own words in a document table are long German compounds -- «Qualitätssicherungsprogramm» simply ran past its column's edge. It is set here, on the tables of the document, and nowhere else, so no other table of the report changes.
  set text(hyphenate: true)
  if header {
    render-table((title: if title == none { [] } else { title }, columns: specs, rows: body, note: note))
  } else {
    doc-plain-table(specs, body, title, note)
  }
}

/// **A table of the document, written by the engineer** -- columns with their headings, rows of cells, columns hidden but kept -- set as every table of this engine is set: three rules and nothing else (docs/domain/calculation-domains.md §3.3).
///
/// ```typ
/// #doc-table(
///   columns: (
///     (id: "part", title: [Bauteil]),
///     (id: "years", title: [Nutzungsdauer], unit: "Jahre", kind: "number"),
///     (id: "remark", title: [Bemerkung], kind: "wide"),
///   ),
///   hidden: (),
///   rows: (
///     (part: [Tragwerk], years: 50, remark: [SIA 260, Ziffer 2.3.2]),
///     (part: [Fassade], years: 25, remark: [Austauschbares Bauteil]),
///   ),
///   caption: [Geplante Nutzungsdauer],
/// )
/// ```
///
/// ```typ
/// #doc-table(
///   columns: (
///     (id: "item", title: [Element]),
///     (id: "text", title: [Beschreibung], kind: "wide"),
///   ),
///   rows: (
///     (item: [Bauherrschaft], text: [[…]]),
///     (item: [Standort], text: [[…]]),
///   ),
///   header: false,
/// )
/// ```
///
/// It is the object Woodcore writes between a `// woodcore:object doc-table <id>` tag and its `// woodcore:/object <id>`; written by hand it is the same call. **The engineer's words are printed exactly as they are written** -- a title, a cell, the caption and the notes are never looked up in the glossary, a string no more than content. A number is printed as every number of this engine is, at the document's decimals and with a real minus sign.
///
/// A hidden column is not printed and its cells stay in the rows, so showing it again gives back what it held. A table with no column, or whose every column is hidden, prints nothing.
///
/// - columns (array): the columns, in order: `(id: "part", title: [Bauteil])`, and optionally `unit: "kN/m²"`, set on a second line of the heading, and `kind:` -- `"text"` (the default, read from the left), `"number"` (read from the right), `"math"` (centred) or `"wide"` (takes the width left over). An id is letters, digits, `_` and `-`, and unique.
/// - hidden (array): the ids of the columns not printed, `("remark",)`.
/// - rows (array): one dictionary per row, keyed by column id, `(part: [Tragwerk], years: 50)`. A cell is content, a string, a number or `none`; a column a row leaves out is empty in it.
/// - caption (none, content, str): the line set in italics above the table.
/// - notes (none, content, str, array): the small print under the table, one line each.
/// - header (bool): `false` sets the table without its heading row -- a list of terms and what they are.
/// -> content
#let doc-table(columns: (), hidden: (), rows: (), caption: none, notes: none, header: true) = {
  let fn = "doc-table"
  let cols = doc-columns(fn, columns)
  let ids = cols.map(c => c.id)
  doc-hidden(fn, hidden, ids)
  doc-rows(fn, rows, ids)
  doc-text-arg(fn, "caption:", caption)
  if type(header) != bool { doc-refuse(fn, "header: is true or false -- got " + repr(header)) }
  let shown = cols.filter(c => not (c.id in hidden))
  let body = rows.enumerate().map(((i, row)) => shown.map(c => doc-cell(fn, i, c.id, row.at(c.id, default: none))))
  context doc-print-table(fn, shown, body, caption, notes, false, header: header)
}

// --- One value, in a cell -----------------------------------------------------------------------

/// **One value of the export or of the report, printed alone** -- the number a cell of a table quotes, with no unit, no label and never a footnote, at every level of the report.
///
/// ```typ
/// #doc-table(
///   columns: (
///     (id: "use", title: [Nutzung]),
///     (id: "q", title: [$q_k$], unit: "kN/m²", kind: "number"),
///   ),
///   rows: (
///     (use: [Büro], q: [#doc-value("q_k", domain: ("live-load", "B"))]),
///     (use: [Wohnen], q: [#doc-value("q_k", domain: ("live-load", "A1"))]),
///   ),
/// )
/// ```
///
/// ```typ
/// #var("g_k", 1.25, "kN/m²", level: 0)
/// #report-level.update(3)
///
/// Die Auflast beträgt #doc-value("g_k") kN/m², und #doc-value("Q_k", domain: ("live-load", "B")) kN als Einzellast.
/// ```
///
/// It is what the editor of a section writes into a cell for a value of the Variables tab -- `[#doc-value("…", domain: …)]` -- and what `live-load-table` fills its automatic cells with. `val` prints the same number and follows the report's level: from level 2 the value's label, from level 3 its description and its citation, all in one footnote, which a cell has no room for -- and a level forced with `--input uniform=3` reaches every `val` whatever it was given. **This prints the value and nothing else, whatever the level**: the unit is the column's heading, and what the value is, the row says.
///
/// The value is printed as every number of this engine is, at the document's decimals and with a real minus sign; a value that is a word is printed as the glossary gives it. The norm a value of the export cites is registered for the bibliography, before anything is set (docs/typst/citations.md §10); a variable of the report's own was registered by the `#var` or the `#eq` that declared it.
///
/// - name (str): the variable's name, `"q_k"`.
/// - domain (none, str, array): where it is read, as `val` reads it: left out, the innermost `var-domain` and then the report's own variables; a string, that `var-domain`; a pair, a calculation and its instance, `("live-load", "B")` -- and, for a name the export does not carry, the `var-domain` named after the instance, where `show-polar-moment` publishes its forces.
/// -> content
#let doc-value(name, domain: none) = {
  let fn = "doc-value"
  if type(name) != str or name.trim() == "" {
    doc-refuse(fn, "the variable is named by a non-empty string, #doc-value(\"q_k\", domain: (\"live-load\", \"B\")) -- got " + repr(name))
  }
  let pair = type(domain) == array and domain.len() == 2 and domain.all(x => type(x) == str)
  if domain != none and type(domain) != str and not pair {
    doc-refuse(fn, "domain: is a var-domain of the report, \"Ende\", or a calculation and its instance, (\"live-load\", \"B\") -- got " + repr(domain))
  }
  if pair {
    // a value of the export is read here, outside every context -- which is where its norm is registered (docs/typst/api-conventions.md §10bis)
    let vars = find-calculation(fn, domain.at(0), domain.at(1)).vars
    if name in vars {
      let v = vars.at(name)
      return bib-note(v.at("norm", default: none)) + fmt-number(v.at("value", default: none), "")
    }
  }
  context {
    let d = var-registry.get()
    let v = if domain == none {
      var-lookup(d, name)
    } else if type(domain) == str {
      d.domains.at(domain, default: (:)).at(name, default: none)
    } else {
      d.domains.at(domain.at(1), default: (:)).at(name, default: none)
    }
    if v == none {
      if domain == none {
        doc-refuse(fn, "no variable named " + repr(name) + " -- "
          + (if var-names(d).len() == 0 { "none is declared yet" } else { "declared here: " + var-names(d).join(", ") })
          + ". A value of the export is read with domain: (\"live-load\", \"B\")")
      } else if type(domain) == str {
        let known = d.domains.at(domain, default: (:)).keys()
        doc-refuse(fn, "no variable named " + repr(name) + " in the domain " + repr(domain) + " -- "
          + (if known.len() == 0 { "that domain declares nothing" } else { "it declares: " + known.join(", ") }))
      } else {
        let vars = find-calculation(fn, domain.at(0), domain.at(1)).vars
        let published = d.domains.at(domain.at(1), default: (:))
        doc-refuse(fn, "unknown var " + repr(name) + " in " + source-label(domain.at(0), domain.at(1))
          + " -- valid vars: " + (vars.keys() + published.keys()).join(", "))
      }
    }
    fmt-number(v.at("value", default: none), "")
  }
}

// --- The live loads, read off SIA 261 Tabelle 8 (docs/domain/loads.md §3.3septies) ----------------

// The columns the live-load table knows by their id: their heading and their unit. q_k and Q_k are headed by their symbol as Tabelle 8 heads them. No Reduktionsbeiwert ψ is ever a column of the live loads (the engineer, 01.10.2026): SIA 260 Tabelle 2 stays transcribed in calc/norms/ for the load combinations, and is shown by no live-load table.
#let live-load-known = (
  zone: (word: "document.zone", kind: "text"),
  storey: (word: "document.storey", kind: "text"),
  use: (word: "document.use", kind: "wide"),
  category: (word: "document.category", kind: "math"),
  q_k: (math: "q_k", unit: "kN/m²", kind: "number"),
  Q_k: (math: "Q_k", unit: "kN", kind: "number"),
)
#let live-load-columns = ("zone", "storey", "use", "category", "q_k", "Q_k").map(id => (id: id))
// The columns whose cell is filled from the row's category where the row leaves it to `auto`.
#let live-load-filled = ("q_k", "Q_k")

/// **The live loads of the building, by part and storey, their values read off SIA 261 Tabelle 8** -- q_k and Q_k filled in from the category of each row and written over where a number is given.
///
/// ```typ
/// #live-load-table(
///   hidden: ("zone",),
///   rows: (
///     (storey: [EG], use: [Büro], category: "B", q_k: auto, Q_k: auto),
///     (storey: [Dach], use: [Nur für Unterhalt begehbar], category: "H", q_k: auto, Q_k: auto),
///   ),
/// )
/// ```
///
/// ```typ
/// #live-load-table(
///   columns: (
///     (id: "use", title: [Nutzung]),
///     (id: "category"),
///     (id: "q_k"),
///     (id: "Q_k"),
///   ),
///   hidden: (),
///   rows: (
///     (use: [Wohnen], category: "A1", q_k: auto, Q_k: auto),
///     (use: [Archiv], category: "E", q_k: 7.5, Q_k: 7),
///   ),
///   caption: [Nutzlasten],
/// )
/// ```
///
/// A cell of `q_k` or `Q_k` is `auto` -- the value of the row's category, read from the export as `#val("q_k", domain: ("live-load", "B"))` reads it, so it follows the norm table and is never typed twice -- or a **number**, which is then the engineer's own and is printed in orange, with a line under the table saying what the orange means. A row that leaves one of these cells out takes `auto`, and a row with no category leaves them empty.
///
/// ⚠️ Category E has no values in SIA 261 Tabelle 8 (8.2.2): its `q_k` and `Q_k` are the project's and are written in the row as numbers, `auto` being refused naming the clause.
///
/// The columns `zone`, `storey`, `use`, `category`, `q_k` and `Q_k` carry their own heading, in the report's language, and their unit; a column of another id takes a `title:`. The words of a row are the engineer's and are printed as they are written.
///
/// - columns (array, auto): the columns, as `doc-table` takes them. auto is the six above, in that order. A column of a known id may leave its `title:` out.
/// - hidden (array): the ids of the columns not printed.
/// - rows (array): one dictionary per row, keyed by column id; `category:` is a category of SIA 261 Tabelle 8 as a string, `"A1"` to `"H"`.
/// - caption (none, content, str): the line set in italics above the table.
/// - notes (none, content, str, array): the small print under the table, one line each.
/// -> content
#let live-load-table(columns: auto, hidden: (), rows: (), caption: none, notes: none) = {
  let fn = "live-load-table"
  let cols = doc-columns(fn, if columns == auto { live-load-columns } else { columns }, defaults: live-load-known)
  let ids = cols.map(c => c.id)
  doc-hidden(fn, hidden, ids)
  doc-rows(fn, rows, ids)
  doc-text-arg(fn, "caption:", caption)
  let shown = cols.filter(c => not (c.id in hidden))
  let domains = load-calculations().domains
  let instances = if live-load-domain in domains { domains.at(live-load-domain).instances } else { none }
  let cited = ()
  let overridden = false
  let body = ()
  for (i, row) in rows.enumerate() {
    let where = "row " + str(i + 1)
    let cat = row.at("category", default: none)
    if cat != none {
      if type(cat) != str {
        doc-refuse(fn, where + ": category: is a category of SIA 261 Tabelle 8 as a string, \"B\" -- got " + repr(cat))
      }
      if instances == none {
        doc-refuse(fn, "the export carries no '" + live-load-domain + "' domain -- rerun calc/export_all.py")
      }
      if not (cat in instances) {
        doc-refuse(fn, where + ": unknown Nutzungskategorie " + repr(cat) + " -- valid categories: " + instances.keys().join(", "))
      }
    }
    let cells = ()
    for c in shown {
      let filled = c.id in live-load-filled
      let cell = row.at(c.id, default: if filled { auto } else { none })
      if filled and cell == auto {
        if cat == none {
          cells.push([])
        } else {
          let vars = instances.at(cat).vars
          if not (c.id in vars) {
            let hint = if "hinweis" in vars { " " + vars.hinweis.value } else { "" }
            doc-refuse(fn, where + ": Nutzungskategorie " + cat + " carries no " + c.id
              + " in SIA 261 Tabelle 8 (8.2.2) --" + hint + " Write the value in the row as a number, " + c.id + ": 5")
          }
          let norm = vars.at(c.id).at("norm", default: none)
          if norm != none and not (norm in cited) { cited.push(norm) }
          // the value alone, the unit being the heading's and a cell having no room for a footnote -- at every level, `--input uniform=3` included, which is what `val` could not promise
          cells.push(doc-value(c.id, domain: (live-load-domain, cat)))
        }
      } else if filled and type(cell) in (int, float) {
        // a number in a column the norm fills is the engineer's own, and is said so in orange (v0.80's rule, the Katalog's colour)
        overridden = true
        cells.push(text(fill: override-colour, fmt-number(cell, "")))
      } else {
        cells.push(doc-cell(fn, i, c.id, cell))
      }
    }
    body.push(cells)
  }
  // The norms the values came from, registered for the bibliography before the context, never inside it (docs/typst/api-conventions.md §10bis).
  for n in cited { bib-note(n) }
  context doc-print-table(fn, shown, body, caption, notes, overridden)
}

// --- The non-structural self-weight (Auflast) --------------------------------------------------

#let dead-load-known = (
  zone: (word: "document.zone", kind: "text"),
  storey: (word: "document.storey", kind: "text"),
  buildup: (word: "document.buildup", kind: "wide"),
  load: (word: "document.superimposed", unit: "kN/m²", kind: "number"),
)
#let dead-load-columns = ("zone", "storey", "buildup", "load").map(id => (id: id))

/// **The non-structural self-weight of the building, by part and storey, in kN/m²** -- a table whose load column takes a number or a value of the export.
///
/// ```typ
/// #dead-load-table(
///   rows: (
///     (zone: [Wohnen], storey: [OG], buildup: [Bodenaufbau, Trennwände], load: 1.5),
///     (zone: [Dach], storey: [Dach], buildup: [Dachaufbau mit Begrünung], load: [#doc-value("gk_ak_gew", domain: ("dead-load", "EL+AL-Dach mit Wasser"))]),
///   ),
/// )
/// ```
///
/// ```typ
/// #dead-load-table(
///   hidden: ("zone",),
///   rows: ((storey: [EG], buildup: [Unterlagsboden 80 mm], load: 1.6),),
///   caption: [Auflasten],
///   notes: [Ohne das Eigengewicht der tragenden Decke.],
/// )
/// ```
///
/// The `load` column is the one a value of the Variables tab goes into: Woodcore writes it as `[#doc-value("…", domain: …)]`, content that is printed as the value it names, so the table follows the calculation -- `doc-value` prints the value alone, with no unit because the unit is the column's heading and no footnote because a cell has no room for one, whatever the report's level.
///
/// The columns `zone`, `storey`, `buildup` and `load` carry their own heading in the report's language, the load's in SIA 261's own words for an Auflast; a column of another id takes a `title:`.
///
/// - columns (array, auto): the columns, as `doc-table` takes them. auto is the four above, in that order.
/// - hidden (array): the ids of the columns not printed.
/// - rows (array): one dictionary per row, keyed by column id; a `load:` cell is a number, `[#doc-value(...)]` content or `none`.
/// - caption (none, content, str): the line set in italics above the table.
/// - notes (none, content, str, array): the small print under the table, one line each.
/// -> content
#let dead-load-table(columns: auto, hidden: (), rows: (), caption: none, notes: none) = {
  let fn = "dead-load-table"
  let cols = doc-columns(fn, if columns == auto { dead-load-columns } else { columns }, defaults: dead-load-known)
  let ids = cols.map(c => c.id)
  doc-hidden(fn, hidden, ids)
  doc-rows(fn, rows, ids)
  doc-text-arg(fn, "caption:", caption)
  let shown = cols.filter(c => not (c.id in hidden))
  let body = rows.enumerate().map(((i, row)) => shown.map(c => doc-cell(fn, i, c.id, row.at(c.id, default: none))))
  context doc-print-table(fn, shown, body, caption, notes, false)
}

// --- A labelled value, a list to tick, a single choice --------------------------------------

// The placeholder the catalogue marks a text still to be written with, «[…]», printed where a value is not known yet.
#let doc-placeholder = "[…]"

/// **One labelled value of the document**: «Bauherrschaft: …», on a line of its own, the label bold and its colon set as the report's language sets one.
///
/// ```typ
/// #doc-field(label: [Nutzungsdauer], value: 50, unit: "Jahre")
/// ```
///
/// ```typ
/// #doc-field(label: [Bauherrschaft])
/// #doc-field(label: [Charakteristische Schneelast], value: [#val("q_k11", domain: ("snow-load", "SL"), level: 1)])
/// ```
///
/// A value not known yet is left out, and the line prints «[…]» in its place, the mark a text still to be written carries. A number is printed at the document's decimals with its unit; content is printed as it is written, so a `#val(...)` in it follows the calculation.
///
/// - label (none, content, str): what the value is. none prints the value alone.
/// - value (none, content, str, int, float): the value. none prints «[…]».
/// - unit (none, str): the unit printed after the value.
/// -> content
#let doc-field(label: none, value: none, unit: none) = {
  let fn = "doc-field"
  doc-text-arg(fn, "label:", label)
  if value != none and not (type(value) in (content, str, int, float)) {
    doc-refuse(fn, "value: is [content], a string or a number -- got " + repr(value))
  }
  if unit != none and type(unit) != str { doc-refuse(fn, "unit: is a string, \"kN/m²\" -- got " + repr(unit)) }
  context block(above: 1em, below: 1em, {
    if label != none { [#strong(doc-words(label))#colon-str() ] }
    if value == none {
      doc-placeholder
    } else if type(value) in (int, float) {
      fmt-number(value, if unit == none { "" } else { unit })
    } else {
      doc-words(value)
      if unit != none { [~#unit] }
    }
  })
}

// A box to tick and a round mark to fill, drawn rather than taken from a font, so that they print in whatever style a project's config.typ sets. The tick is the heavy U+2714 `verify` sets its verdict with, which the report's font carries (lib/summary.typ).
#let doc-box(checked) = box(width: 0.78em, height: 0.78em, stroke: 0.6pt, baseline: 0.1em,
  if checked { place(center + horizon, text(size: 0.72em, "✔")) })
#let doc-mark(on) = box(width: 0.78em, height: 0.78em, radius: 50%, stroke: 0.6pt, baseline: 0.1em,
  if on { place(center + horizon, circle(radius: 0.2em, fill: black, stroke: none)) })

// One option on a line of its own, its mark before it and a wrapped line aligned under its text.
#let doc-option(mark, body) = block(above: 0.45em, below: 0.45em,
  par(hanging-indent: 1.2em, first-line-indent: 0em, justify: false)[#box(width: 1.2em, mark)#body])

// A list or a choice, as one block spaced like a paragraph of its own, under its heading where it has one -- kept with its first option.
#let doc-list(label, body) = block(above: 1em, below: 1em, {
  if label != none { block(below: 0.5em, sticky: true, strong(doc-words(label))) }
  body
})

#let doc-option-keys = ("id", "label", "checked", "text")

/// **A list to tick**: the options ticked, and nothing else, as a list -- each with, where it carries one, the paragraph that explains it under it; or, with `only-checked: false`, every option with its box, ticked or not.
///
/// ```typ
/// #doc-checklist(
///   label: [Angestrebte Zertifizierung],
///   options: (
///     (id: "minergie", label: [Minergie], checked: true),
///     (id: "snbs", label: [SNBS Hochbau], checked: false),
///   ),
///   only-checked: false,
/// )
/// ```
///
/// ```typ
/// #doc-checklist(
///   label: [Akzeptierte Risiken],
///   options: (
///     (id: "ground", label: [Baugrundrisiko], checked: true, text: [Die Kostenfolgen unbekannter Inhomogenitäten im Baugrund gelten als akzeptiertes Risiko der Bauherrschaft.]),
///     (id: "vandalism", label: [Vandalismus], checked: false, text: [Mutwillige Beschädigungen sind nicht bemessen.]),
///   ),
/// )
/// ```
///
/// A report says what was chosen and not what was left aside (the engineer's rule of 06.10.2026), so the options not ticked are printed only where `only-checked: false` asks for them; nothing ticked yet prints «[…]». The boxes are drawn and not taken from a font, so they print in any style a project's `config.typ` sets. An option's words are the engineer's and are printed as they are written.
///
/// - label (none, content, str): the list's heading, bold on a line of its own.
/// - options (array): `(id: "minergie", label: [Minergie], checked: true)`, in order, and optionally `text: [...]`, printed under the option where it is ticked. An id is unique in the list.
/// - only-checked (bool): true, the default, prints the ticked options alone, as a list; false prints every option with its box.
/// -> content
#let doc-checklist(label: none, options: (), only-checked: true) = {
  let fn = "doc-checklist"
  doc-text-arg(fn, "label:", label)
  if type(options) != array { doc-refuse(fn, "options: is an array of (id: \"...\", label: [...], checked: true) -- got " + repr(options)) }
  if type(only-checked) != bool { doc-refuse(fn, "only-checked: is true or false -- got " + repr(only-checked)) }
  let seen = ()
  for (i, o) in options.enumerate() {
    let where = "option " + str(i + 1)
    if type(o) != dictionary { doc-refuse(fn, where + " is (id: \"...\", label: [...], checked: true) -- got " + repr(o)) }
    doc-keys(fn, where, o, doc-option-keys)
    let id = o.at("id", default: none)
    if type(id) != str or id == "" { doc-refuse(fn, where + ": id: is a string -- got " + repr(id)) }
    if id in seen { doc-refuse(fn, "two options are called " + repr(id) + " -- an id names one option") }
    seen.push(id)
    if o.at("label", default: none) == none { doc-refuse(fn, "option " + repr(id) + " has no label: -- write one, label: [...]") }
    doc-text-arg(fn, "option " + repr(id) + ": label:", o.label)
    if type(o.at("checked", default: false)) != bool { doc-refuse(fn, "option " + repr(id) + ": checked: is true or false -- got " + repr(o.checked)) }
    doc-text-arg(fn, "option " + repr(id) + ": text:", o.at("text", default: none))
  }
  let shown = if only-checked { options.filter(o => o.at("checked", default: false)) } else { options }
  if shown.len() == 0 and label == none { return [] }
  // What was chosen, as a plain list: a box ticked before every line says nothing a report needs to say (06.10.2026)
  if only-checked {
    return doc-list(label, {
      if shown.len() == 0 { doc-placeholder }
      for o in shown {
        list(tight: true, {
          doc-words(o.label)
          let explained = o.at("text", default: none)
          if explained != none { block(above: 0.3em, below: 0.4em, doc-words(explained)) }
        })
      }
    })
  }
  doc-list(label, {
    for o in shown {
      let checked = o.at("checked", default: false)
      doc-option(doc-box(checked), doc-words(o.label))
      let explained = o.at("text", default: none)
      if checked and explained != none { pad(left: 1.2em, block(above: 0.3em, below: 0.6em, doc-words(explained))) }
    }
  })
}

#let doc-choice-keys = ("id", "label")

/// **One choice among several**: the answer alone, after its label -- or, with `only-selected: false`, every option with its round mark, the one chosen filled.
///
/// ```typ
/// #doc-choice(
///   label: [Nutzungsdauer des Tragwerks (SIA 260, Ziffer 2.3.2)],
///   options: (
///     (id: "replaceable", label: [Austauschbares Bauteil: bis 25 Jahre]),
///     (id: "normal", label: [Gebäude von normaler Bedeutung: 50 Jahre]),
///     (id: "major", label: [Bauwerk von übergeordneter Bedeutung: 100 Jahre]),
///   ),
///   selected: "normal",
///   only-selected: false,
/// )
/// ```
///
/// ```typ
/// #doc-choice(
///   label: [Bauwerksklasse],
///   options: ((id: "i", label: [BWK I]), (id: "ii", label: [BWK II]), (id: "iii", label: [BWK III])),
///   selected: "ii",
/// )
/// ```
///
/// Where no option fits, `other:` states the answer in the engineer's own words and is the choice, printed after the options under the report's word for «other». A choice holds one answer, so `selected:` and `other:` together are refused, and so is an id that names no option.
///
/// - label (none, content, str): what is chosen, bold before the answer -- or on a line of its own above the options, with `only-selected: false`.
/// - options (array): `(id: "normal", label: [...])`, in order. An id is unique.
/// - selected (none, str): the id of the option chosen. none chooses nothing yet.
/// - other (none, content, str): another answer, in the engineer's words, where no option fits.
/// - only-selected (bool): true, the default, prints the label and the answer alone, on one line -- «[…]» while nothing is chosen; false prints every option, the one chosen marked.
/// -> content
#let doc-choice(label: none, options: (), selected: none, other: none, only-selected: true) = {
  let fn = "doc-choice"
  doc-text-arg(fn, "label:", label)
  doc-text-arg(fn, "other:", other)
  if type(options) != array { doc-refuse(fn, "options: is an array of (id: \"...\", label: [...]) -- got " + repr(options)) }
  if type(only-selected) != bool { doc-refuse(fn, "only-selected: is true or false -- got " + repr(only-selected)) }
  let seen = ()
  for (i, o) in options.enumerate() {
    let where = "option " + str(i + 1)
    if type(o) != dictionary { doc-refuse(fn, where + " is (id: \"...\", label: [...]) -- got " + repr(o)) }
    doc-keys(fn, where, o, doc-choice-keys)
    let id = o.at("id", default: none)
    if type(id) != str or id == "" { doc-refuse(fn, where + ": id: is a string -- got " + repr(id)) }
    if id in seen { doc-refuse(fn, "two options are called " + repr(id) + " -- an id names one option") }
    seen.push(id)
    if o.at("label", default: none) == none { doc-refuse(fn, "option " + repr(id) + " has no label: -- write one, label: [...]") }
    doc-text-arg(fn, "option " + repr(id) + ": label:", o.label)
  }
  if selected != none and not (type(selected) == str and selected in seen) {
    doc-refuse(fn, "selected: " + repr(selected) + " names no option -- " + (if seen.len() == 0 { "there is none" } else { "the options are " + seen.map(s => repr(s)).join(", ") }))
  }
  if selected != none and other != none {
    doc-refuse(fn, "selected: and other: both answer -- a choice holds one answer, keep one of the two")
  }
  if options.len() == 0 and other == none and label == none { return [] }
  context {
    let other-word = t-str("document.other")
    if only-selected {
      let answer = if selected != none { doc-words(options.find(o => o.id == selected).label) } else if other != none { doc-words(other) } else { doc-placeholder }
      block(above: 1em, below: 1em, if label != none { [#strong(doc-words(label))#colon-str() #answer] } else { answer })
    } else {
      doc-list(label, {
        for o in options { doc-option(doc-mark(o.id == selected), doc-words(o.label)) }
        if other != none { doc-option(doc-mark(true), [#other-word#colon-str() #doc-words(other)]) }
      })
    }
  }
}

// --- A picture, an extract of a position plan --------------------------------------------------

// A frame standing where a picture will be, saying what will stand in it.
#let doc-frame(width, words) = block(width: width, height: 4cm, stroke: (paint: luma(150), thickness: 0.6pt, dash: "dashed"), inset: 8pt,
  align(center + horizon, text(fill: luma(110), words)))

#let doc-width(fn, width) = {
  if not (type(width) in (length, ratio, relative)) {
    doc-refuse(fn, "width: is a length or a ratio, 60% or 12cm -- got " + repr(width))
  }
}

// A picture, with its caption as a figure numbered in the document's language, or set on its own where there is none.
#let doc-figure(body, caption) = {
  if caption == none { block(width: 100%, align(center, body)) } else { figure(body, kind: image, caption: doc-words(caption)) }
}

/// **A picture of the document**: a file of the project -- a geological profile, a plan of the architect -- with its caption, or a frame standing in its place until the file is there.
///
/// ```typ
/// #doc-image(caption: [Geologisches Profil], placeholder: [Auszug aus dem geotechnischen Bericht])
/// ```
///
/// ```typ
/// #doc-image(file: "data/connectors/SD-10-section.svg", caption: [Schnitt durch den Anschluss], width: 40%)
/// ```
///
/// The path is read from the **Typst root** -- the project's folder, whichever document the call is written in -- so `"Images/profil.png"` and `"/Images/profil.png"` name the same file. ⚠️ Typst cannot ask whether a file exists, and a file named that is not there stops the compile: `file: none` is what a section carries until the picture is there, and it prints a frame saying what will stand in it.
///
/// - file (none, str): the picture, as a path from the project's folder. none prints the frame.
/// - caption (none, content, str): the figure's caption, numbered as Typst numbers a figure in the document's language. none sets the picture with no figure around it.
/// - width (relative): how wide the picture, or its frame, is set.
/// - placeholder (none, content, str): what the frame says while there is no file. none says «[Abbildung]» in the report's language.
/// -> content
#let doc-image(file: none, caption: none, width: 100%, placeholder: none) = {
  let fn = "doc-image"
  if file != none and (type(file) != str or file.trim() == "") {
    doc-refuse(fn, "file: is the picture's path from the project's folder, \"Images/profil.png\", or none -- got " + repr(file))
  }
  doc-text-arg(fn, "caption:", caption)
  doc-text-arg(fn, "placeholder:", placeholder)
  doc-width(fn, width)
  if file == none {
    context doc-figure(doc-frame(width, if placeholder == none { t-str("document.image") } else { doc-words(placeholder) }), caption)
  } else {
    let path = file.trim()
    doc-figure(image(if path.starts-with("/") { path } else { "/" + path }, width: width), caption)
  }
}

/// **An extract of a position plan drawn in Woodcore**, in a document -- `show-plan` with every argument it takes, and a frame standing in its place while no plan is chosen.
///
/// ```typ
/// #doc-plan(plan: "Pavillon", highlight: "T001", detail: true, width: 60%)
/// ```
///
/// ```typ
/// #doc-plan(plan: none, caption: [Belastungsplan Erdgeschoss])
/// ```
///
/// Everything but the frame is `show-plan`'s (docs/domain/position-plans.md §3.3sexies): the architect's plan faded under the STE symbols, the halo under the positions highlighted, the detail around them, the scale bar and the legend.
///
/// - plan (none, str): the plan, by its id in Woodcore's «Plan de positions» tab. none prints the frame.
/// - highlight (none, str, array): the positions set on a halo.
/// - detail (bool): only the surroundings of the positions highlighted.
/// - zoom (int, float): how much a detail is enlarged.
/// - axes (bool): the plan's axes.
/// - dimensions (bool): the dimensions drawn on the plan.
/// - lengths (bool): the lengths written beside its elements.
/// - legend (bool): the legend of the symbols, under the plan.
/// - scale-bar (bool): the scale bar, under the plan.
/// - width (relative): how wide the plan is set.
/// - caption (auto, none, content, str): auto is the plan's own caption, «Positionsplan …»; none prints the plan with no figure around it. A plan not chosen yet takes a caption the call gives, and none at auto.
/// -> content
#let doc-plan(plan: none, highlight: none, detail: false, zoom: 1, axes: true, dimensions: true, lengths: true, legend: true, scale-bar: true, width: 100%, caption: auto) = {
  let fn = "doc-plan"
  if plan != none and type(plan) != str { doc-refuse(fn, "plan: is a plan's id, \"Pavillon\", or none -- got " + repr(plan)) }
  doc-width(fn, width)
  if caption != auto { doc-text-arg(fn, "caption:", caption) }
  if plan == none {
    context doc-figure(doc-frame(width, t-str("document.plan")), if caption == auto { none } else { caption })
  } else {
    show-plan(plan, width: width, legend: legend, highlight: highlight, detail: detail, zoom: zoom, axes: axes, dimensions: dimensions, lengths: lengths, scale-bar: scale-bar,
      caption: if caption == auto or caption == none { caption } else { doc-words(caption) })
  }
}

/// **A fire-protection plan drawn in Woodcore**, in a document -- `show-fire-plan` with its width, its legend, its scale bar and its caption, and a frame standing in its place while no plan is chosen.
///
/// ```typ
/// #doc-fire-plan(plan: "Treppenhaus", width: 70%)
/// ```
///
/// ```typ
/// #doc-fire-plan(plan: none, caption: [Brandschutzplan Erdgeschoss])
/// ```
///
/// Everything but the frame is `show-fire-plan`'s: the architect's plan faded under the surfaces of the escape routes, the walls with their fire resistance, the doors, the escape routes' lengths, exits and widths, in the colours of the VKF sheet of symbols, with the legend Woodcore placed on it and the scale bar under it.
///
/// - plan (none, str): the plan, by its id in Woodcore's «Plan de protection incendie» tab. none prints the frame.
/// - legend (bool): the legend drawn on the plan.
/// - scale-bar (bool): the scale bar, under the plan.
/// - width (relative): how wide the plan is set.
/// - caption (auto, none, content, str): auto is the plan's own caption, «Brandschutzplan …»; none prints the plan with no figure around it. A plan not chosen yet takes a caption the call gives, and none at auto.
/// -> content
#let doc-fire-plan(plan: none, legend: true, scale-bar: true, width: 100%, caption: auto) = {
  let fn = "doc-fire-plan"
  if plan != none and type(plan) != str { doc-refuse(fn, "plan: is a fire-protection plan's id, \"Treppenhaus\", or none -- got " + repr(plan)) }
  doc-width(fn, width)
  if caption != auto { doc-text-arg(fn, "caption:", caption) }
  if plan == none {
    context doc-figure(doc-frame(width, t-str("document.fire_plan")), if caption == auto { none } else { caption })
  } else {
    show-fire-plan(plan, width: width, legend: legend, scale-bar: scale-bar,
      caption: if caption == auto or caption == none { caption } else { doc-words(caption) })
  }
}

/// **An excerpt of an annex**, in a document -- `show-extract` with its width and its caption, and a frame standing in its place while no excerpt is chosen. The excerpt is a region of one page of a source copied into Woodcore's «Annexes» tab: a diagram of a FEM program's print report, a table of an approval.
///
/// ```typ
/// #doc-extract(excerpt: "CO1-My", width: 70%, caption: [Biegemomente unter CO1])
/// ```
///
/// ```typ
/// #doc-extract(excerpt: none, caption: [Schnittkräfte der Stütze])
/// ```
///
/// Everything but the frame is `show-extract`'s (docs/domain/annexes.md §3.3undevicies): the excerpt follows every new version of its source by the bookmark of its title, one that cannot be found stops the compile naming why, and the annex page it comes from is linked both ways where the document prints `doc-annexes`. The excerpt may be shown in the convention, the base or the report: each document prints the annex pages of the excerpts **it** shows.
///
/// - excerpt (none, str): the excerpt, by its id in Woodcore's «Annexes» tab. none prints the frame.
/// - width (relative): how wide the excerpt is set; its height follows the frame's own proportions.
/// - caption (auto, none, content, str): auto names the source and its page, «Auszug aus Rapport RFEM, S. 24»; none prints the excerpt with no figure around it. An excerpt not chosen yet takes a caption the call gives, and none at auto.
/// -> content
#let doc-extract(excerpt: none, width: 100%, caption: auto) = {
  let fn = "doc-extract"
  if excerpt != none and type(excerpt) != str { doc-refuse(fn, "excerpt: is an excerpt's id, \"CO1-My\", or none -- got " + repr(excerpt)) }
  doc-width(fn, width)
  if caption != auto { doc-text-arg(fn, "caption:", caption) }
  if excerpt == none {
    context doc-figure(doc-frame(width, t-str("document.extract")), if caption == auto { none } else { caption })
  } else {
    show-extract(excerpt, width: width, caption: if caption == auto or caption == none { caption } else { doc-words(caption) })
  }
}

/// **The annexes of the project, at this point of the document** -- `show-annexes`, as an object a section holds: for every source of Woodcore's «Annexes» tab, a cover page and the pages **this document's** excerpts come from (or every page, or none, as the source chooses), whole and at their own size.
///
/// ```typ-dry
/// #doc-annexes(heading: 2)
/// ```
///
/// ```typ-dry
/// #doc-annexes(heading: none)
/// ```
///
/// The level the name of each annex is set at is the one argument: a section written at depth 2 (`== …`) wants `heading: 3`, so the annexes stand under its own title in the outline -- the document's headings being written at the level they print at (docs/domain/documents.md §3.3octodecies).
///
/// - heading (int, none): the level each annex's name is set as a heading at; none sets it in bold on its cover page and keeps the outline the engineer's.
/// -> content
#let doc-annexes(heading: 2) = {
  let fn = "doc-annexes"
  if heading != none and not (type(heading) == int and heading >= 1) { doc-refuse(fn, "heading: is the level of a heading, 2, or none -- got " + repr(heading)) }
  show-annexes(heading: heading)
}

// --- The signatures --------------------------------------------------------------------------

#let doc-signature-keys = ("group", "role", "name", "place", "date")
// How tall a row one signs on is, and how wide the name and the place and date are kept -- room to write them in by hand where the row leaves them blank.
#let doc-signature-height = 1.3cm
#let doc-signature-name = 3.6cm
#let doc-signature-when = 3.2cm

/// **The signatures of the document**: one row per signatory -- the role, the name, the place and the date -- and a line to sign on.
///
/// ```typ
/// #doc-signatures(rows: (
///   (group: [Bauherrschaft], role: [Bauherrschaft]),
///   (group: [Projektverfassende], role: [Architekt:in]),
///   (group: [Projektverfassende], role: [Ingenieur:in]),
/// ))
/// ```
///
/// ```typ
/// #doc-signatures(rows: ((role: [Bauherrschaft], name: [M. Muster], place: [Bern]),), place-date: false)
/// ```
///
/// Rows sharing a `group:` are set under one bold line naming it -- the owner's side, the authors of the project -- as the signatures of a Nutzungsvereinbarung are grouped. What a row leaves out is left blank, to be written by hand on the paper.
///
/// - rows (array): `(role: [...], name: [...], place: [...], date: [...])`, each but `role` optional, and optionally `group: [...]`.
/// - place-date (bool): the column of the place and the date. false leaves it out.
/// -> content
#let doc-signatures(rows: (), place-date: true) = {
  let fn = "doc-signatures"
  if type(rows) != array { doc-refuse(fn, "rows: is an array of (role: [...], name: [...], place: [...], date: [...]) -- got " + repr(rows)) }
  if type(place-date) != bool { doc-refuse(fn, "place-date: is true or false -- got " + repr(place-date)) }
  for (i, r) in rows.enumerate() {
    let where = "row " + str(i + 1)
    if type(r) != dictionary { doc-refuse(fn, where + " is (role: [...], name: [...], place: [...], date: [...]) -- got " + repr(r)) }
    doc-keys(fn, where, r, doc-signature-keys)
    for k in r.keys() { doc-text-arg(fn, where + ": " + k + ":", r.at(k)) }
  }
  if rows.len() == 0 { return [] }
  context {
    // a cell of the height one signs in, its words at its foot where the line is
    let low(body, width: auto) = box(width: width, height: doc-signature-height, align(left + bottom, body))
    let columns = (
      (label: [#t-str("document.role")], kind: "text"),
      (label: [#t-str("document.name")], kind: "text"),
    ) + (if place-date { ((label: [#t-str("document.place_date")], kind: "text"),) } else { () }) + (
      (label: [#t-str("document.signature")], kind: "wide"),
    )
    let body = ()
    let bold = ()
    let group = none
    for r in rows {
      let here = r.at("group", default: none)
      if here != none and here != group {
        bold.push(body.len())
        body.push((doc-words(here),) + (columns.len() - 1) * ([],))
      }
      group = here
      let when = (r.at("place", default: none), r.at("date", default: none)).filter(x => x != none and x != "" and x != [])
      body.push(
        (low(doc-words(r.at("role", default: none))), low(doc-words(r.at("name", default: none)), width: doc-signature-name))
        + (if place-date { (low(when.map(doc-words).join([, ]), width: doc-signature-when),) } else { () })
        + (block(width: 100%, height: doc-signature-height, align(bottom, line(length: 100%, stroke: 0.5pt))),),
      )
    }
    render-table((title: [], columns: columns, rows: body), bold-rows: bold)
  }
}

// --- The norms a section names ------------------------------------------------------------------

/// **The norms and documents a section names, listed in full** -- designation, title, publisher and edition, as the bibliography sets them (docs/typst/citations.md §10): the selection the engineer makes in the section of the norms and the documents a convention d'utilisation and a base de projet rest on.
///
/// ```typ
/// #show-norm-list(keys: ("SIA 260", "SIA 261", "SIA 265"))
/// ```
///
/// ```typ
/// #show-norm-list(keys: ("VKF 14-15", "SIA 181:2020", [Lärmschutz-Verordnung (LSV)]))
/// ```
///
/// A key is a document of `calc/norms/norms.json`, or of the project's own `references.bib` where `project:` names it, by its key or one of its aliases (`"SIA 260:2013"`), and it is registered for the bibliography as a citation is; one neither names is printed as it is written and never invented. Content is a line in the engineer's own words, printed as it is and registered nowhere. They are printed in the order given, once each.
///
/// - keys (array): the documents, in order: strings naming an entry, or content.
/// - project (none, str): the project's own `references.bib`, as a path from the project's folder -- `"references.bib"` -- or none.
/// -> content
#let show-norm-list(keys: (), project: none) = {
  let fn = "show-norm-list"
  if type(keys) != array {
    doc-refuse(fn, "keys: is an array of the documents to list, (\"SIA 260\", \"SIA 261\") -- " + (if type(keys) == str { "write (" + repr(keys) + ",) for one" } else { "got " + repr(keys) }))
  }
  for k in keys {
    if not (type(k) in (str, content)) or (type(k) == str and k.trim() == "") {
      doc-refuse(fn, "keys: holds " + repr(k) + " -- a document is named by a non-empty string, \"SIA 260\", and a line of your own is [content]")
    }
  }
  if project != none and type(project) != str {
    doc-refuse(fn, "project: names the project's references.bib as a path from the project's folder, \"references.bib\" -- got " + repr(project))
  }
  // The entries the keys name, found once and outside the context: the catalogue and the project's file are read, not asked of a state. A key and an alias of one document -- «SIA 260» and «SIA 260:2013» -- are one document, listed once and registered under its own key, so that the bibliography, which dedups what it was handed, lists it once too.
  let index = bib-index(if project == none { () } else { bib-read-file(project) })
  let items = ()
  let seen = ()
  for k in keys {
    if type(k) == content {
      items.push(k)
    } else {
      let cited = k.trim()
      let entry = index.at(cited, default: none)
      let name = if entry == none { cited } else { entry.key }
      if not (name in seen) {
        seen.push(name)
        items.push((cited: name, entry: entry))
      }
    }
  }
  // registered before the context, never inside it (docs/typst/api-conventions.md §10bis)
  for name in seen { bib-note(name) }
  context {
    let lang = report-lang()
    for item in items {
      block(above: 0.5em, below: 0.5em, if type(item) == content { item } else { bib-line(item, lang) })
    }
  }
}
