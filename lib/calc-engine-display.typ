// lib/calc-engine-display.typ -- the calculation block, the input variables, the tables that keep to the page, the formulas in letters then numbers, the calculation and check display.
// Split out of lib/calc-engine.typ by subject, its text moved and not rewritten (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, G9). Each part imports the one before it, so a name reads everything defined above it as it did in one file; lib/calc-engine.typ imports the last and is what every caller names.

#import "calc-engine-drawings.typ": *

// --- Calculation block (docs/typst/report-engine.md §5) ------------------------------
// The report-side unit of work: a group of calculations that all concern the same position(s). Attribution runs block -> position and is a pure presentation concern, exactly like axes -- declaring a position here puts nothing onto that position's data, and a load's show-input may sit inside a block without any of this creating a position<->load link (sections 7-8).

// --- Input variable display, with description/choices (docs/typst/report-engine.md §9)
// The one call that reaches for a single named value. show-calc renders a whole calculation and never takes a var name; show-input is how a report pulls one intermediate value out of it and sets it in its own prose.

// `inline-value` stood here until v0.80: one var of the export, inline, as `symbol = value unit`. It is `val("s_k", domain: ("snow-load", "SL"), type: "expression")` now -- the same lookup, in the one command that prints a value (section 13). `show-input` keeps the other half of that pair: the *block* row, whose citation stands in the right-hand column, which inline content cannot reach.

// --- One-off calculations done in Typst (docs/project/purpose.md §1) ------------
// There is deliberately no show-* function for these. An arrangement of already-traced values that the data does not carry -- a quick product, a value read off two sheets -- is written as an ordinary Typst equation, with the numbers pulled from the data rather than retyped:
//
//   #let g-k = var-of("dead-load", "EL+AL-Dach1.mitPV", "gk_ak_gew")
//   #let s-k = var-of("snow-load", "SL-Dach1", "s_k")
//   #let x = get(g-k, "value") * get(s-k, "value")
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
  let name = if "label_math" in c { math-eval(c.label_math) } else if type(c.label) == str { [#tl-str(c.label)] } else { [#c.label] }
  // A column the group line above it already names ("in Faserrichtung" over a distance and its multiple of d) carries no label of its own, and its unit then stands alone rather than under an empty line.
  let unnamed = "label_math" not in c and c.label == ""
  if unit == "" { name } else if unnamed { [#("[" + unit + "]")] } else { name + linebreak() + [#("[" + unit + "]")] }
}

// A `math` cell is Typst math source, evaluated like a var's symbol (section 6bis): it is how the build-up prints the g_k a layer counts towards instead of the sheet's own "gk". A `value` cell names a var of the same instance instead of repeating its number, so the table cannot drift from the value it shows (section 2, rule 1) -- and it is set bold where that var is one of the calculation's results, bold marking the answer in a table exactly as it does in a formula. Every other cell goes through fmt, so a number in a table rounds exactly like the same number in a formula.
#let table-cell(kind, cell, vars: (:), results: ()) = {
  if kind == "math" and type(cell) == str and cell != "" {
    math-eval(cell)
  } else if kind == "value" and type(cell) == str and cell != "" {
    assert(cell in vars,
      message: "render-table: a table cell names var '" + cell + "', which this calculation does not declare -- valid vars: " + vars.keys().join(", "))
    let printed = fmt-number(get(vars.at(cell), "value"), "")
    if cell in results { text(weight: "bold", printed) } else { printed }
  } else {
    // A text cell is a word of the table -- "Wand A", "Total" -- or a material's name out of the workbook. The glossary decides which: it carries the first and not the second.
    // One carrying a dollar is prose with its symbols between dollars, set as math (render-prose, section 4bis): a connector's «$K_("ser","Verb")$» and «$7 d$» (v0.77). A material's name carries none, and an unpaired dollar is left as written.
    // A number is printed by fmt-number, its sign a minus; a word goes through render-prose, which sets a sign the same way where the word carries one («-5 °C») and leaves every other hyphen as typed.
    // ⚠️ **Content passes through untouched** (v0.99), as a column's own `label` already does: it is how a caller says «these are not the engine's words, do not look them up». The journal's label and its two descriptions are free text the engineer typed, and free text is the one case where the glossary's own rule -- translate it if the glossary carries it -- can go wrong: a template matches on the literal segments around its holes, so a revision labelled «Element 3 ergänzt» matches «Element {n}» and a French report would print «élément 3 ergänzt» (section 3.3terdecies; the risk section 14 records for `tl-of`). A string still goes through the glossary, which is what every table read from the data needs.
    if type(cell) == content { cell } else if type(cell) == str { context render-prose(tl-str(cell)) } else { fmt-number(cell, "") }
  }
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
        annotated-rows(lines.enumerate().map(((i, f)) => (math-eval(f), if i == 0 { cite } else { none })))
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
              image(figure-path(f.file), width: 100%)
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

// --- Calculation display (docs/typst/report-engine.md §4, §5, docs/typst/citations.md §10) --------------------
// (domain, instance) select one whole calculation -- an instance of a calculation domain (a workbook sheet), or one domain of a position. There is deliberately no step-name argument: show-calc renders the calculation entire, ending on its result, and show-input is what picks a single intermediate value out. level: auto reads the global report-level. Position/axes headers are the job of the enclosing calc-block, not of each individual call.

// --- Check display (docs/typst/citations.md §10) ---------------------------------
