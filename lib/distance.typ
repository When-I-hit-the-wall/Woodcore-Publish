// The minimum distances and timber thicknesses of a fastener, out of SIA 265:2021, computed with its diameter (v0.87).
//
// SIA 265 gives them as multiples of d, one table per kind of fastener and per way of driving it: Tabelle 24 for dowels and bolts, 27, 28, 32 and 33 for nails without and with predrilling, 36 to 40 for screws, 41 for split rings. `#distance(d, connector)` prints the tables of one kind with every multiple turned into millimetres for the d it is given -- laid out as a connector's own Tabelle 24 is (docs/domain/connectors.md §3.3nonies): a row per distance, its value in mm and its multiple of d under each direction, the diameter named over the first column.
//
// Nothing here is a norm value. The multiples, the floors in mm, the diameter ranges and which fastener a table is stated for are read from calc/norms/ (docs/architecture/principles.md §2 rule 13, 11), one JSON per table, through the relative path `../calc/norms/` -- which resolves in the program and in a project's _woodcore/ alike, lib/ sitting beside calc/ in both. calc/norms/sia265.py checks the same files before an export reads anything, and tests/test_distance.py holds this file's list of them equal to its own.
//
// It imports from calc-engine.typ and never from formula.typ: formula.typ imports `distance` from here, which is how commands.typ, re-exporting formula.typ at the wildcard, gives every section the command -- and the helpers below stay out of the sections' scope.
#import "calc-engine.typ": colon-str, fmt-decimals, note-column, note-gutter, number-digits, render-prose, render-table, t-str, tl-str, value-type, var-lookup, var-registry
// The bibliography (lib/bibliography.typ, v0.99): `bib-note` registers SIA 265 so that the tables printed here are listed at the end of the report. bibliography.typ imports calc-engine.typ and nothing else, so the chain calc-engine -> bibliography -> distance -> formula stays acyclic.
#import "bibliography.typ": bib-note

// Where the norm files are, seen from this file.
#let distance-dir = "../calc/norms/"

// The tables this command prints, by their number in SIA 265, in the norm's order. calc/norms/sia265.py's DISTANCE_TABLES names the same files.
#let distance-files = (
  "24": "sia265-2021-tab24-abstaende",
  "27": "sia265-2021-tab27-holzdicken-naegel",
  "28": "sia265-2021-tab28-abstaende-naegel",
  "32": "sia265-2021-tab32-holzdicken-naegel-vorgebohrt",
  "33": "sia265-2021-tab33-abstaende-naegel-vorgebohrt",
  "36": "sia265-2021-tab36-holzdicken-schrauben",
  "37": "sia265-2021-tab37-holzdicken-schrauben-vorgebohrt",
  "38": "sia265-2021-tab38-abstaende-schrauben",
  "39": "sia265-2021-tab39-abstaende-schrauben-vorgebohrt",
  "40": "sia265-2021-tab40-abstaende-schrauben-axial",
  "41": "sia265-2021-tab41-abstaende-ringduebel",
)

// The clauses a table's fastener may name as the diameters it holds for -- a nail from 1.9 to 8.5 mm (6.4.1.1), a screw of Tabellen 36/37 from 6 to 12 mm (6.5.2.3.1), a dowel from 6 to 30 mm (6.2.1.1). sia265.py's DIAMETER_SCOPES, likewise.
#let distance-scopes = (
  "sia265-2021-6.2.1.1-k-alpha",
  "sia265-2021-6.4.1.1-nageldurchmesser",
  "sia265-2021-6.5.2.3.1-schraubendurchmesser",
)

// The kinds of fastener, by the English key a call writes. The last two have no table in SIA 265, and are refused with the reason rather than as an unknown word.
#let distance-kinds = ("dowel", "bolt", "nail", "screw", "ring", "staple", "threaded-rod")

// The same kinds by the German name calc/domains/connector.py's TYPES gives them -- what Woodcore's connectors carry -- so `#distance(12, "Stabdübel")` is `#distance(12, "dowel")`. A Passbolzen is a Stabdübel by its former name (SIA 265 1.1.36); a Dübel besonderer Bauart is read as a split ring, the one of them SIA 265 gives distances for (6.8.3). tests/test_distance.py holds these names equal to connector.TYPES.
#let distance-types = (
  "Stabdübel": "dowel",
  "Passbolzen": "dowel",
  "Bolzen": "bolt",
  "Vollgewindeschraube": "screw",
  "Teilgewindeschraube": "screw",
  "Nagel": "nail",
  "Klammer": "staple",
  "eingeklebte Gewindestange": "threaded-rod",
  "Dübel besonderer Bauart": "ring",
)

// Why a kind with no table has none, said in the refusal.
#let distance-none = (
  "staple": "SIA 265 gives no distances for staples: 6.6 sends staple connections to SIA 265/1 (its Tabelle 28, as SIA 265 Tabelle 15 cites it)",
  "threaded-rod": "SIA 265 gives no table of distances for glued-in threaded rods among Tabellen 24 to 41",
)

// A diameter's unit, towards millimetres: what a var object or a variable of the report may carry.
#let distance-units = ("mm": 1, "cm": 10, "m": 1000)

// One table, as calc/norms/ states it.
#let distance-table(number) = json(distance-dir + distance-files.at(number) + ".json").at("table_" + number)

// The norm these tables are out of, read from one of them rather than written down here (docs/architecture/principles.md §2 rule 13, 11): what `bib-note` registers for the bibliography. Every table of the list carries the same `norm`; Tabelle 24 is the one always there.
#let distance-norm() = distance-table("24").norm

// The kind a call names, or a refusal listing both spellings.
#let distance-kind(connector) = {
  if value-type(connector) != str {
    panic("distance: connector is the kind of fastener as a string -- " + distance-kinds.map(repr).join(", ") + " -- got " + repr(connector))
  }
  let low = lower(connector)
  if low in distance-kinds { return low }
  for (german, kind) in distance-types {
    if lower(german) == low { return kind }
  }
  panic("distance: no kind of fastener " + repr(connector) + " -- write one of " + distance-kinds.map(repr).join(", ")
    + ", or its German name: " + distance-types.keys().map(repr).join(", "))
}

// The diameter in mm: a number is one already; a var object and a variable of the report carry their unit, mm, cm or m. Read inside the command's context, the report's registry being a state.
#let distance-diameter(d) = {
  let held = if value-type(d) == str {
    let found = var-lookup(var-registry.get(), d)
    if found == none {
      panic("distance: no variable " + repr(d) + " is declared above this line -- write the diameter in mm, or declare it first with #var(" + repr(d) + ", 12, \"mm\")")
    }
    found
  } else { d }
  let (value, unit) = if value-type(held) == dictionary {
    if not ("value" in held and "unit" in held) {
      panic("distance: d is a number in mm, a var object or the name of a variable -- got a dictionary without a value and a unit")
    }
    (held.value, held.unit)
  } else { (held, "mm") }
  if not (unit in distance-units) {
    panic("distance: d is in " + repr(unit) + " -- a diameter is in " + distance-units.keys().join(", "))
  }
  if not (value-type(value) in (int, float)) or value <= 0 {
    panic("distance: d is " + repr(value) + " -- a diameter is a positive number")
  }
  value * distance-units.at(unit)
}

// A multiple as the norm writes it: a number, or its fraction [4, 3].
#let distance-factor(v) = if value-type(v) == array { v.at(0) / v.at(1) } else { v }
#let distance-factor-math(v) = if value-type(v) == array { str(v.at(0)) + "\\/" + str(v.at(1)) } else { fmt-decimals(v, 3) }

// A cell's footnote references, raised in math as the norm sets them: 10 d¹⁾.
#let distance-marks(cell) = {
  let notes = cell.at("notes", default: ())
  if notes.len() == 0 { "" } else { "^\"" + notes.map(n => n + ")").join(" ") + "\"" }
}

// Tabelle 41's multiple as the norm writes it, 4/3 · (3/2 − α/180°) · d -- set under the table rather than in its cell, where it took the width the distances' names need.
#let distance-alpha-math(a) = "$" + distance-factor-math(a.coefficient) + " dot (" + distance-factor-math(a.base) + " - alpha \\/ " + str(a.divisor) + "°) dot d$"

// One cell, for a diameter d in mm and the angle alpha in degrees, as (value, written): its value in mm, and its multiple of d as the norm writes it -- the case d falls in named after it, the floor after the multiple. Tabelle 41's multiple depends on the angle: the cell carries it evaluated at that angle, the angle after it, and its formula goes under the table (distance-render).
#let distance-cell(cell, d, alpha) = {
  let marks = distance-marks(cell)
  let (factor, written) = if "cases" in cell {
    let (low, high) = cell.cases
    let case = if d <= low.d_max { low } else { high }
    let bound = if d <= low.d_max { "$d <= " + fmt-decimals(low.d_max, 3) + "$ mm" } else { "$d > " + fmt-decimals(high.d_above, 3) + "$ mm" }
    (distance-factor(case.factor), "$" + distance-factor-math(case.factor) + " d" + marks + "$ (" + bound + ")")
  } else if "alpha" in cell {
    let a = cell.alpha
    let shown = if alpha == none { 0 } else { alpha }
    let factor = distance-factor(a.coefficient) * (distance-factor(a.base) - shown / a.divisor)
    (factor, "$" + fmt-decimals(factor, 3) + " d" + marks + "$ ($alpha = " + fmt-decimals(shown, 1) + "°$)")
  } else {
    (distance-factor(cell.factor), "$" + distance-factor-math(cell.factor) + " d" + marks + "$")
  }
  let floor = cell.at("min", default: none)
  let value = if floor == none { factor * d } else { calc.max(factor * d, floor) }
  if floor != none { written += " (min. " + fmt-decimals(floor, 3) + " mm)" }
  (value, written)
}

// A label's footnote references as math on an empty base, so they can follow the label in a cell that must stay a string: «Mindestholzdicke $t$» and its ²⁾. Empty where it has none.
#let distance-label-marks(entry) = {
  let notes = entry.at("notes", default: ())
  if notes.len() == 0 { "" } else { "$\"\"^\"" + notes.map(n => n + ")").join(" ") + "\"$" }
}

// A label of the table's head or of a column, with its footnote references after it.
#let distance-label(entry) = {
  let notes = entry.at("notes", default: ())
  let words = render-prose(tl-str(entry.label))
  if notes.len() == 0 { words } else { [#words#super(notes.map(n => n + ")").join(" "))] }
}

// The citation: «SIA 265 Tabelle 28» -- a table takes no §, and «Tabelle» is a word, printed in the report's language; a clause is cited with its §, as norm-text cites one.
#let distance-cite(norm, ref) = {
  if ref == "" { [#norm] }
  else if ref.starts-with("Tabelle ") { [#norm #tl-str("Tabelle") #ref.slice("Tabelle ".len())] }
  else if ref.starts-with("Anhang ") { [#norm #tl-str("Anhang") #ref.slice("Anhang ".len())] }
  else { [#norm §#ref] }
}

// One line with the citation beside it in the right-hand column, as annotated-rows sets one -- written here because a table is cited by its number, which norm-text would print after a §.
#let distance-line(body, cite) = {
  if cite == none { return block(width: 100%, body) }
  grid(columns: (1fr, note-column), column-gutter: note-gutter, body, align(right + horizon, text(size: 8pt, cite)))
}

// Whether a fastener's entry of a table holds for a diameter d: the range its clause states, or every d where it states none.
#let distance-in-scope(entry, d) = {
  if not ("scope" in entry) { return true }
  let span = json(distance-dir + entry.scope + ".json").clause.diameter_range
  d >= span.min and d <= span.max
}

// The table as render-table sets it (docs/domain/calculation-domains.md §3.3): the head over the first column with the diameter as its group, then a pair of columns -- the value in mm and the multiple of d -- under each of the table's own column heads.
//
// A table of timber thicknesses is one row -- the materials it holds for -- under two heads, t_erf and t_min (Tabellen 27, 32, 36, 37). Laid out as the page lays it, the materials' names took a column a few words wide beside two long heads; it is set **a row per thickness** instead, like every other table here, and its one row -- «Baustoff: Vollholz, …» -- goes under it. The same numbers, turned a quarter.
#let distance-render(tbl, entry, d, alpha, title: []) = {
  let turned = tbl.rows.len() == 1 and tbl.columns.len() > 1
  let named = not turned and (tbl.columns.len() > 1 or tbl.columns.first().label != "")
  let head = if turned { distance-label((label: "Holzdicke")) } else { distance-label(tbl.head) }
  let columns = ((label: head, kind: "wide", group: "$d$ = " + fmt-decimals(d, number-digits.get()) + " mm"),)
  let groups = if turned { (none,) } else { tbl.columns }
  for column in groups {
    let over = if named { (group: distance-label(column)) } else { (:) }
    columns.push((label: "", kind: "number", unit: tbl.unit, ..over))
    columns.push((label: "", kind: "text", ..over))
  }
  let rows = ()
  if turned {
    let only = tbl.rows.first()
    for column in tbl.columns {
      let (value, written) = distance-cell(only.at(column.id), d, alpha)
      rows.push((tl-str(column.label) + distance-label-marks(column), value, written))
    }
  } else {
    for row in tbl.rows {
      let cells = (row.label,)
      for column in tbl.columns {
        let (value, written) = distance-cell(row.at(column.id), d, alpha)
        cells += (value, written)
      }
      rows.push(cells)
    }
  }
  // Under the table: the materials a turned table holds for, what the norm says of this fastener in it, the formula of a multiple that depends on the angle -- with the angle it was read at where the call gave none -- and the table's own footnotes.
  let notes = ()
  if turned {
    notes.push([#distance-label(tbl.head)#colon-str() #render-prose(tl-str(tbl.rows.first().label)).])
  }
  if "note" in entry { notes.push(render-prose(tl-str(entry.note))) }
  for row in tbl.rows {
    for column in tbl.columns {
      let cell = row.at(column.id)
      if "alpha" in cell {
        notes.push([#render-prose(tl-str(row.label)), #render-prose(tl-str(column.label))#colon-str() #render-prose(distance-alpha-math(cell.alpha)).])
        if alpha == none {
          let at90 = distance-cell(cell, d, 90).at(0)
          notes.push(render-prose(t-str("distance.alpha_default", value: fmt-decimals(at90, number-digits.get()))))
        }
      }
    }
  }
  for (mark, sentence) in tbl.footnotes { notes.push(render-prose(mark + ") " + tl-str(sentence))) }
  render-table((title: title, columns: columns, rows: rows, note: if notes.len() == 0 { none } else { notes.join(" ") }), above: 0.4em)
}

/// Prints the minimum distances and timber thicknesses SIA 265:2021 gives for a kind of fastener, each multiple of d computed in mm for the diameter `d` -- Tabellen 24, 27, 28, 32, 33 and 36 to 41, read from `calc/norms/`.
///
/// ```typ
/// #distance(3.1, "nail", tab: 28)
/// ```
///
/// ```typ
/// #distance(8, "screw", tab: 38, label: "Anschluss Sparren – Pfette", descr: "Vollgewindeschrauben, nicht vorgebohrt.")
/// ```
///
/// Every table SIA 265 gives for the kind and that holds for that d, one under the other, when no `tab:` is given:
///
/// ```typ
/// #distance(12, "Stabdübel")
/// ```
///
/// Tabelle 41's spacing between two rings along the grain depends on the angle between force and grain; without `alpha:` it is given at 0°, the largest, and its value at 90° is said under the table:
///
/// ```typ
/// #distance(80, "ring", alpha: 30)
/// ```
///
/// A diameter declared with `#var` is named, and carries its unit:
///
/// ```typ
/// #var("d", 1.6, "cm")
/// #distance("d", "dowel", title: none)
/// ```
///
/// Which tables a kind is shown: dowel -- Tabelle 24 (d from 6 to 30 mm, 6.2.1.1); bolt -- Tabelle 24 (6.3.1.3); nail -- 27, 28, 32 and 33 (d from 1.9 to 8.5 mm, 6.4.1.1); screw -- 36 and 37 (d from 6 to 12 mm, 6.5.2.3.1), 38, 39 and 40, and 28 or 33 when asked for by `tab:` (a screw with d₁/d > 0.75, or one after DIN 7998); ring -- 41. The ranges and the assignments are the norm files', not this list's.
/// - d (int, float, str, dictionary): the fastener's diameter in mm; or a var object, or the name of a variable declared with `#var`, in mm, cm or m. For a ring, its outer diameter (6.8.3.1).
/// - connector (str): the kind of fastener -- "dowel", "bolt", "nail", "screw", "ring" -- or its German name as Woodcore's connectors carry it: "Stabdübel", "Passbolzen", "Bolzen", "Vollgewindeschraube", "Teilgewindeschraube", "Nagel", "Dübel besonderer Bauart". "staple" ("Klammer") and "threaded-rod" ("eingeklebte Gewindestange") are refused, SIA 265 giving them no table.
/// - tab (auto, int, str): auto prints every table the kind is shown by itself and that holds for d; a number prints that table alone -- refused, naming the ones that do, where it does not concern the kind or that d.
/// - title (auto, none, str): auto sets each table's own title from the norm, in the report's language; none sets none; a string replaces it, for one table.
/// - label (str, none): what the tables are for, on a line above them -- «Anschluss Sparren – Pfette».
/// - descr (str, none): a footnote on that line, or on the first title where there is no label.
/// - norm (auto, none, str): the citation in the right-hand column: auto is the norm's own, "SIA 265"; none prints none.
/// - norm-ref (auto, str): auto cites the table by its number, «Tabelle 28»; a string replaces it, for one table -- a clause is printed after a §.
/// - alpha (none, int, float): the angle between force and grain in degrees, 0 to 90, for the one value that depends on it, Tabelle 41's spacing between rings along the grain; refused where no table shown depends on it.
/// -> content
#let distance(d, connector, tab: auto, title: auto, label: none, descr: none, norm: auto, norm-ref: auto, alpha: none) = bib-note(distance-norm()) + context {
  // ⚠️ `bib-note(distance-norm()) + context { … }` above: the document these tables come out of is registered for the bibliography **outside** this context, which is where a state written is read back by the folded chain an update function reads (docs/domain/connections.md §3.3quinquies, v0.99). It is registered whatever `norm:` asks to be printed beside them -- `norm: none` prints no citation and the tables are still SIA 265's.
  let kind = distance-kind(connector)
  if kind in distance-none {
    panic("distance: " + distance-none.at(kind) + " -- the kinds with a table are " + distance-kinds.filter(k => not (k in distance-none)).map(repr).join(", "))
  }
  let dd = distance-diameter(d)
  if alpha != none and (not (value-type(alpha) in (int, float)) or alpha < 0 or alpha > 90) {
    panic("distance: alpha is " + repr(alpha) + " -- the angle between force and grain, in degrees from 0 to 90")
  }

  // Every table stated for this kind, with the entry that says so, and whether it holds for this d.
  let stated = ()
  for number in distance-files.keys() {
    let tbl = distance-table(number)
    let entry = tbl.fasteners.find(f => f.fastener == kind)
    if entry != none { stated.push((number: number, tbl: tbl, entry: entry, fits: distance-in-scope(entry, dd))) }
  }
  let shown = if tab == auto {
    stated.filter(s => s.entry.auto and s.fits)
  } else {
    let number = str(tab)
    if not (number in distance-files) {
      panic("distance: SIA 265 has no table of distances " + repr(tab) + " -- the tables are " + distance-files.keys().join(", "))
    }
    let pick = stated.find(s => s.number == number)
    let fitting = stated.filter(s => s.fits).map(s => s.number)
    if pick == none {
      panic("distance: Tabelle " + number + " is not stated for a " + kind + " -- for a " + kind + " of d = " + fmt-decimals(dd, 3) + " mm, tab: takes " + fitting.join(", "))
    }
    if not pick.fits {
      let span = json(distance-dir + pick.entry.scope + ".json").clause
      panic("distance: Tabelle " + number + " holds for a " + kind + " of d from " + fmt-decimals(span.diameter_range.min, 3) + " to " + fmt-decimals(span.diameter_range.max, 3)
        + " mm (SIA 265 " + span.norm_ref + ") -- d = " + fmt-decimals(dd, 3) + " mm" + (if fitting.len() == 0 { "" } else { "; tab: takes " + fitting.join(", ") }))
    }
    (pick,)
  }
  if shown.len() == 0 {
    let spans = stated.filter(s => "scope" in s.entry).map(s => json(distance-dir + s.entry.scope + ".json").clause).dedup()
    panic("distance: no table of SIA 265 holds for a " + kind + " of d = " + fmt-decimals(dd, 3) + " mm -- "
      + spans.map(c => "SIA 265 " + c.norm_ref + " states d from " + fmt-decimals(c.diameter_range.min, 3) + " to " + fmt-decimals(c.diameter_range.max, 3) + " mm").join("; "))
  }
  if shown.len() > 1 {
    if value-type(title) == str { panic("distance: title: a string names one table, and " + str(shown.len()) + " are shown -- pick one with tab: (" + shown.map(s => s.number).join(", ") + "), or leave title: auto") }
    if value-type(norm-ref) == str { panic("distance: norm-ref: a string cites one table, and " + str(shown.len()) + " are shown -- pick one with tab: (" + shown.map(s => s.number).join(", ") + "), or leave norm-ref: auto") }
  }
  if alpha != none and not shown.any(s => s.tbl.rows.any(r => s.tbl.columns.any(c => "alpha" in r.at(c.id)))) {
    panic("distance: alpha: no table shown depends on the angle between force and grain -- only Tabelle 41's spacing between rings does")
  }

  let note = if descr == none { none } else { footnote(render-prose(tl-str(descr))) }
  if label != none {
    block(above: 1em, below: 0.5em, sticky: true, [#render-prose(tl-str(label))#note])
  }
  for (i, s) in shown.enumerate() {
    // The table's title is its numbered caption, «Tabelle 3: …», set by render-table as every table's is (table-figure); the citation stays in the right-hand column of a line of its own above it.
    let head = if title == auto { render-prose(tl-str(s.tbl.title)) } else if title == none { [] } else { render-prose(tl-str(title)) }
    if i == 0 and label == none and note != none { head = [#head#note] }
    let cite = if norm == none { none } else {
      let ref = if norm-ref == auto { "Tabelle " + s.number } else { norm-ref }
      distance-cite(if norm == auto { s.tbl.norm } else { norm }, ref)
    }
    if cite != none { block(above: 1em, below: 0em, sticky: true, distance-line([], cite)) }
    distance-render(s.tbl, s.entry, dd, alpha, title: head)
  }
}
