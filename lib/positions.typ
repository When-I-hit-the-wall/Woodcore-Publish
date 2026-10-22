// The list of the positions (v0.116): every position of the project, or those drawn on given position plans, or those of one storey, in one table -- the «liste des positions» of STE Compact 02 «Plans dans la construction en bois», with this project's own columns: ID, type, material, strength class, section type, dimension, units, moisture class and description, the columns of Woodcore's «Positions» tab (the engineer, 06.10.2026: «tu peux reprendre le nom de nos colonnes à nous»).
//
// Two commands print it: `show-position-list` in a report, a convention or a base de projet, and lib/sheet.typ's `sheet-position-list` on an export sheet, which builds the same table through `position-list-table` -- one table, two places.
//
// ⚠️ **The table is this engine's own** (`render-table`: three rules and nothing else, a column aligned by what it holds, docs/domain/calculation-domains.md §3.3), not STE's grid -- the engineer's choice: «pas besoin de reprendre leur type de tableau à eux».
//
// ⚠️ **The ID is coloured by the position's type**, its STE letter -- the very colour the plan draws that letter's symbol and number box with (calc/domains/plan_svg.py's COLOURS and LABEL_COLOURS, restated below and held equal by tests/test_position_list.py): a W's number in black in an orange box, a T's in blue in a rounded one.
//
// ⚠️ **The type is printed in the document's language** where the glossary carries it (`tl-str`, the STE types' German being the key) and as stored where it does not -- a type typed freely stays as typed; the ID's letter never changes («T» stays «T» in French). The material and the strength class go the same way, the glossary deciding what is the norm's word. **The description is the engineer's own words and is never looked up** (content passes `render-table` untouched, section 3.3terdecies).
//
// It imports calc-engine.typ and nothing else, so the chain calc-engine -> positions -> sheet -> formula stays acyclic: formula.typ imports `show-position-list` by name, sheet.typ imports the table builder by name (docs/typst/api-conventions.md §10bis point 3).
#import "calc-engine.typ": figure-colour, fmt-decimals, known-position-ids, load-position, ids, override-colour, render-table, report-lang, t-str, tl-str

// The STE colours of a position's letter -- calc/domains/plan_svg.py's COLOURS, the colour the plan draws the symbol and the number's box with, and LABEL_COLOURS, the number's own where it differs (a W carries an orange and a violet symbol, so its number is black). Restated here, Typst reading no Python, and held equal by tests/test_position_list.py.
#let position-colours = (
  V: figure-colour("orange"), H: figure-colour("violet"), W: figure-colour("orange"), T: figure-colour("blue"), S: figure-colour("blue"), A: figure-colour("violet"), D: figure-colour("brown"),
  M: figure-colour("green"), L: figure-colour("light-blue"), "Ö": figure-colour("yellow"), B: figure-colour("aid"), PL: figure-colour("orange"), LL: figure-colour("orange"),
)
#let position-label-colours = (W: figure-colour("ink"))
// The letters whose number sits in a stadium rather than a rectangle, as plan_svg sets them (STADIUM).
#let position-stadium = ("T", "A", "D")

// The columns of the list, in the order they are printed, and what each holds (render-table's kinds). The same nine as Woodcore's «Positions» tab and the display view's column list (calc/tools/display_options.py POSITION_LIST_COLUMNS, held equal by tests/test_position_list.py).
#let position-list-columns-all = ("id", "type", "material", "strength_class", "section_type", "dimension", "units", "moisture_class", "description")
#let position-list-kinds = (
  id: "text", type: "text", material: "text", strength_class: "text", section_type: "text", dimension: "text",
  units: "text", moisture_class: "math", description: "wide",
)

#let position-list-refuse(fn, message) = panic(fn + ": " + message)

// The ID's cell: the number in its STE box -- white, framed in the letter's colour, the number bold in the label's colour, a stadium for T, A and D -- as the plan draws it. A letter STE does not know is printed plain.
#let position-id-cell(id) = {
  let letter = id.clusters().at(0, default: "")
  let colour = position-colours.at(letter, default: none)
  if colour == none { return [#id] }
  let ink = rgb(position-label-colours.at(letter, default: colour))
  box(fill: white, stroke: 0.8pt + ink, inset: (x: 2.5pt, y: 1.5pt), radius: if letter in position-stadium { 4pt } else { 1.2pt },
    text(fill: ink, weight: "bold", id))
}

// A field of a position record: a string, the number of a moisture class, or nothing ("" where the record leaves it out or holds none).
#let position-field(record, key) = {
  let v = record.at(key, default: none)
  if v == none { "" } else if type(v) == str { v } else { str(v) }
}

// The section type as a word in the document's language -- «rec» is «Section rectangulaire», «Rechteckquerschnitt», «Rectangular section» --; a steel family stays its code (IPE, ROR…), which is the designation SZS C5 gives it. In a context.
// The names are `calc/i18n/strings.json`'s `position_list.section.<code>`, held equal to calc/domains/section.py's by tests/test_position_list.py.
#let position-section-type(code) = {
  if code in ("rec", "cir", "pla", "clt") { t-str("position_list.section." + code) } else { code }
}

#let position-list-layout(columns, widths, fn) = {
  let all = position-list-columns-all
  let keys = if columns == auto { all } else if type(columns) == array { columns } else {
    position-list-refuse(fn, "columns: is auto or an array of column names -- columns: (\"id\", \"type\") -- got " + repr(columns))
  }
  if keys.len() == 0 { position-list-refuse(fn, "columns: names no column -- valid: " + all.join(", ")) }
  for key in keys {
    if type(key) != str or not (key in all) { position-list-refuse(fn, "columns: has no column " + repr(key) + " -- valid: " + all.join(", ")) }
  }
  if keys.dedup().len() != keys.len() { position-list-refuse(fn, "columns: names a column twice -- got " + repr(keys)) }
  let stated = if widths == none { (:) } else if type(widths) == dictionary { widths } else {
    position-list-refuse(fn, "widths: is a dictionary of column widths -- (id: 30mm, type: 20%) -- got " + repr(widths))
  }
  for (key, width) in stated {
    if not (key in all) { position-list-refuse(fn, "widths: has no column " + repr(key) + " -- valid: " + all.join(", ")) }
    let length-ok = type(width) == length and width.abs >= 0pt and width.em >= 0 and (width.abs > 0pt or width.em > 0)
    let ratio-ok = type(width) == ratio and width > 0% and width <= 100%
    if not (length-ok or ratio-ok) {
      position-list-refuse(fn, "widths: " + key + ": is a length -- 30mm -- or a percentage of the text width -- 20% -- above 0, and at most 100% for a percentage -- got " + repr(width))
    }
  }
  (keys: keys, widths: stated)
}

/// The table of positions `ids` -- a `render-table` table, `title` its numbered caption (none for no caption). In a context: its headings are the engine's words in the document's language. The type, the material and the strength class are strings, which the table translates where the glossary carries them; the section type, the dimension and the description are the engineer's and pass as content.
///
/// - ids (array): the positions, in the order they are listed.
/// - title (none, content, str): the table's caption; none sets none.
/// - columns (auto, array): the columns printed, by name -- the same nine as Woodcore's «Positions» tab -- in the order given; auto prints them all.
/// - widths (none, dictionary): a width for some columns, by name: a length (`30mm`) or a percentage of the text width (`20%`); the others take what their cells need.
/// - legend (none, content, str): a text set small under the table.
/// - fn (str): the command that asks, named in a refusal.
/// -> content
#let position-list-table(ids, title: none, columns: auto, widths: none, legend: none, fn: "position-list-table") = {
  let layout = position-list-layout(columns, widths, fn)
  // A heading is set as its column lets it: wider than `fit-heading-cap` it takes more lines, broken at its spaces where it has some -- «Classe de / résistance» --, a single long word hyphenated in the report's language -- «Festigkeits-/klasse». Nine columns of «Classe de résistance» and «Festigkeitsklasse» left the description no room at all on an A4 page (v0.116); the table now gives every column its width (render-table, `fit`).
  // in a context of its own, so that the language is read where the heading is set
  let heading(key) = context {
    let words = t-str("position_list." + key)
    text(lang: report-lang(), hyphenate: not words.contains(" "), words)
  }
  // the description takes what width is left, and its heading is never cut
  let col(key) = {
    let kind = position-list-kinds.at(key)
    let column = (label: if kind == "wide" { t-str("position_list." + key) } else { heading(key) }, kind: kind)
    if key in layout.widths { column.insert("width", layout.widths.at(key)) }
    column
  }
  let cell(key, id, r) = {
    if key == "id" { position-id-cell(id) }
    else if key == "section_type" { [#position-section-type(position-field(r, "section_type"))] }
    else if key in ("dimension", "moisture_class", "description") { [#position-field(r, key)] }
    else { position-field(r, key) }
  }
  let rows = ids.map(id => {
    let r = load-position(id)
    layout.keys.map(key => cell(key, id, r))
  })
  // the legend is the table's note, set small under it, as content: what the engineer wrote is never looked up in the glossary
  let note = if legend == none { none } else if type(legend) == str { [#legend] } else { legend }
  render-table((
    title: title,
    columns: layout.keys.map(col),
    rows: rows,
    note: note,
    fit: true,
  ))
}

// --- The quantities of the position plans (issue #9) ------------------------------------------
// What the plans draw, by material and section -- pieces, length, volume, a total per material --, as calc/domains/quantities.py computed it into data/quantities.json at the export (the engineer, 08.10.2026: «le résumé (les métrés) … par matériau et par section, longueurs et volumes»). Printed here and never computed again, but for the rows of the positions a call names, added up by `quantity-sum` the way `quantities.summary` does -- tests/test_quantities.py holds the two equal.

// The export's quantities -- an export written before issue #9 has none, and prints an empty summary.
#let load-quantities() = {
  let found = json("../data/quantities.json")
  if found.at("schema_version", default: none) != "1.0" { panic("quantities: data/quantities.json is schema " + repr(found.at("schema_version", default: none)) + " -- export again") }
  found
}

// --- One position on a line (spec 2026-10-21-commandes-typst-refonte, REQ-015) ----------------------------------------

// The fields `#position` may show, by the name a call writes, and the field of the position record each reads -- `length` the quantities' (data/quantities.json), `label` and `descr` the call's own.
#let position-categories = ("type", "material", "strength-class", "section-type", "dimension", "units", "moisture-class", "length", "label", "descr")

/// **One position on a line**: its id in its box, as the plan draws it, then the fields `category-show` names, read from the export (`data/positions/<id>.json`) -- what `#member` printed of a position before its values went into the check's own file.
///
/// ```typ
/// #position("T001")
/// ```
///
/// ```typ
/// #position("T001", label: "Pfette", category-show: ("type", "material", "strength-class", "dimension", "units", "length"))
/// ```
///
/// - id (str): the position's id, `"T001"`; one the export does not carry stops the report, naming those it carries. A position renumbered and kept with its values (`"S110-old"`) is printed with an orange line naming the position it was and when.
/// - label (none, str, content): a name of the call's own, printed after the id.
/// - descr (none, str, content): a sentence of the call's own, printed after the fields -- `"descr"` in `category-show` prints the position's own description where none is given.
/// - category-show (str, array): the fields printed, in their order, among `"type"`, `"material"`, `"strength-class"`, `"section-type"`, `"dimension"`, `"units"`, `"moisture-class"`, `"length"` (the length the position plans draw it with, data/quantities.json), `"label"`, `"descr"`.
/// -> content
#let position(id, label: none, descr: none, category-show: ("type", "material", "strength-class")) = context {
  let fn = "position"
  // a position renumbered and kept with its values (S110 -> S110-old) is one of the report's still, said in orange below its line
  let known = known-position-ids()
  if type(id) != str or not (id in known) {
    position-list-refuse(fn, "no position " + repr(id) + " -- " + (if known.len() == 0 { "the project has none yet" } else { "valid positions: " + known.join(", ") }))
  }
  let shown = if type(category-show) == str { (category-show,) } else if type(category-show) == array { category-show } else {
    position-list-refuse(fn, "category-show: is a field or an array of them -- got " + repr(category-show))
  }
  for c in shown {
    if not (c in position-categories) { position-list-refuse(fn, "category-show: has no field " + repr(c) + " -- valid: " + position-categories.join(", ")) }
  }
  let r = load-position(id)
  let field(key) = position-field(r, key)
  let parts = ()
  for c in shown {
    let part = if c == "type" { if field("type") != "" { tl-str(field("type")) } }
      else if c == "material" { if field("material") != "" { tl-str(field("material")) } }
      else if c == "strength-class" { field("strength_class") }
      else if c == "section-type" { if field("section_type") != "" { position-section-type(field("section_type")) } }
      // the dimension with its unit, one part «12/24 cm»; a unit is never printed without its dimension -- a support, an opening carry none (v0.87)
      else if c == "dimension" { if field("dimension") != "" { if "units" in shown and field("units") != "" [#field("dimension") #field("units")] else [#field("dimension")] } }
      else if c == "units" { if field("dimension") != "" and not ("dimension" in shown) { field("units") } }
      else if c == "moisture-class" { if field("moisture_class") != "" { t-str("moisture_class") + " " + field("moisture_class") } }
      else if c == "length" {
        let rows = load-quantities().rows.filter(q => q.position == id and q.length_m != none)
        if rows.len() > 0 { "L = " + fmt-decimals(rows.map(q => q.length_m).sum(), 2) + " m" }
      }
      else if c == "label" { label }
      else if c == "descr" { if descr != none { descr } else if field("description") != "" { [#field("description")] } }
    if part != none and part != "" { parts.push(if type(part) == str { [#part] } else { part }) }
  }
  position-id-cell(id)
  if label != none and not ("label" in shown) [ #label]
  if parts.len() > 0 [: #parts.join([, ])]
  if descr != none and not ("descr" in shown) [ --- #descr]
  let old = r.at("archived", default: none)
  if old != none {
    block(above: 0.3em, below: 0.3em, text(size: 0.9em, fill: override-colour, t-str("position.archived") + " " + old.was + " (" + t-str("position.archived_on") + " " + old.deleted + ")"))
  }
}
