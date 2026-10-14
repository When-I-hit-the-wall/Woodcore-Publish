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
#import "calc-engine.typ": fmt-decimals, load-plans, load-position, position-ids, render-table, report-lang, t-str

// The STE colours of a position's letter -- calc/domains/plan_svg.py's COLOURS, the colour the plan draws the symbol and the number's box with, and LABEL_COLOURS, the number's own where it differs (a W carries an orange and a violet symbol, so its number is black). Restated here, Typst reading no Python, and held equal by tests/test_position_list.py.
#let position-colours = (
  V: "#E8841A", H: "#7C3AA0", W: "#E8841A", T: "#2E5FAA", S: "#2E5FAA", A: "#7C3AA0", D: "#8A5A2B",
  M: "#2E8B40", L: "#3FA9D6", "Ö": "#F4D03F", B: "#9AA4AC", PL: "#E8841A", LL: "#E8841A",
)
#let position-label-colours = (W: "#111111")
// The letters whose number sits in a stadium rather than a rectangle, as plan_svg sets them (STADIUM).
#let position-stadium = ("T", "A", "D")

// The columns of the list, in the order they are printed, and what each holds (render-table's kinds). The same nine as Woodcore's «Positions» tab and the display view's column list (calc/tools/display_options.py POSITION_LIST_COLUMNS, held equal by tests/test_position_list.py).
#let position-list-columns-all = ("id", "type", "material", "strength_class", "section_type", "dimension", "units", "moisture_class", "description")
#let position-list-kinds = (
  id: "text", type: "text", material: "text", strength_class: "text", section_type: "text", dimension: "text",
  units: "text", moisture_class: "math", description: "wide",
)

// The scopes a list is drawn from: every position, those drawn on given plans, those of one storey.
#let position-list-scopes = ("all", "plans", "storey")

#let position-list-refuse(fn, message) = panic(fn + ": " + message)

/// The ids a position list shows, in the project's order (data/positions-index.json): every position for `scope: "all"`, those drawn on the plans `plans` for `"plans"` -- a plan's `labels`, the positions its elements carry --, those whose numbering character (the id's second letter, STE's storey: T**1**01) is `storey` for `"storey"`. A number a plan carries that the project has no position for is left out, there being no row to print.
///
/// - scope (str): "all", "plans" or "storey".
/// - plans (str, array): the position plans, by their ids, for `scope: "plans"`.
/// - storey (none, str): the numbering character, for `scope: "storey"`.
/// - fn (str): the command that asks, named in a refusal.
/// -> array
#let position-list-ids(scope: "all", plans: (), storey: none, fn: "show-position-list") = {
  if not (scope in position-list-scopes) {
    position-list-refuse(fn, "scope: is \"all\", \"plans\" or \"storey\" -- got " + repr(scope))
  }
  let all = position-ids()
  if scope == "all" { return all }
  if scope == "storey" {
    if type(storey) != str or storey.clusters().len() != 1 {
      position-list-refuse(fn, "storey: is the numbering character of a storey, \"0\" for T001 -- got " + repr(storey))
    }
    return all.filter(id => id.clusters().at(1, default: none) == storey)
  }
  let wanted = if type(plans) == str { (plans,) } else if type(plans) == array { plans } else {
    position-list-refuse(fn, "plans: is a position plan's id or an array of them -- got " + repr(plans))
  }
  let known = load-plans().plans
  let labels = ()
  for id in wanted {
    if type(id) != str or not (id in known) {
      position-list-refuse(fn, "no position plan " + repr(id) + " -- " + (if known.len() == 0 { "none saved yet (draw one in Woodcore's position plan tab)" } else { "valid plans: " + known.keys().join(", ") }))
    }
    labels += known.at(id).at("labels", default: ())
  }
  all.filter(id => id in labels)
}

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

/// **The list of the positions**, in a table: the positions of the project -- all of them, those drawn on given position plans, or those of one storey -- with their ID, type, material, strength class, section type, dimension, units, moisture class and description, the columns of Woodcore's «Positions» tab. The ID is set in its STE box, coloured as the plan draws the letter's symbol; the type follows the document's language where the glossary carries it.
///
/// ```typ
/// #show-position-list()
/// ```
///
/// ```typ
/// #show-position-list(scope: "plans", plans: "Pavillon", title: [Positionen des Pavillons])
/// ```
///
/// ```typ
/// #show-position-list(scope: "storey", storey: "0", title: none)
/// ```
///
/// ```typ
/// #show-position-list(columns: ("id", "type", "dimension", "description"), widths: (id: 20mm, dimension: 25%))
/// ```
///
/// ```typ
/// #show-position-list(scope: "storey", storey: "0", legend: [Les dimensions sont données en mm.])
/// ```
///
/// The positions come from the export (`data/positions/`), in the order Woodcore's «Positions» tab lists them. On an export sheet the same table is the object `sheet-position-list`, which lists by default the positions of the plans the sheet shows.
///
/// - scope (str): "all" every position, "plans" those drawn on `plans`, "storey" those of the storey `storey`.
/// - plans (str, array): the position plans, by their ids in Woodcore's «Plan de positions» tab, for `scope: "plans"`; none named prints nothing.
/// - storey (none, str): the storey's numbering character -- the id's second letter, "0" for T001 -- for `scope: "storey"`.
/// - title (auto, none, content, str): the table's numbered caption: auto is «Liste des positions» in the document's language, none sets none.
/// - columns (auto, array): the columns printed, by name -- `"id"`, `"type"`, `"material"`, `"strength_class"`, `"section_type"`, `"dimension"`, `"units"`, `"moisture_class"`, `"description"` -- in the order given; auto prints all nine.
/// - widths (none, dictionary): the width of some columns, by name -- `(id: 30mm, type: 20%)` --, a length or a percentage of the text width; the others take what their cells need, and the table never goes past the right margin. A name that is not a column, or a width that is not one, stops the report naming it.
/// - legend (none, content, str): a text set small under the table -- notes, abbreviations --, as written.
/// -> content
#let show-position-list(scope: "all", plans: (), storey: none, title: auto, columns: auto, widths: none, legend: none) = {
  let fn = "show-position-list"
  if title != auto and title != none and type(title) != str and type(title) != content {
    position-list-refuse(fn, "title: is auto, none, [content] or a string -- got " + repr(title))
  }
  // no plan named, none ticked in Woodcore's display view: nothing is printed -- no table, no caption, no message (v0.117; until then this call was refused, and the window, which leaves `plans:` out when no plan is ticked, showed the refusal)
  if legend != none and type(legend) != str and type(legend) != content {
    position-list-refuse(fn, "legend: is none, [content] or a string -- got " + repr(legend))
  }
  // the columns and their widths are checked before anything is printed, a refusal naming the column
  let _ = position-list-layout(columns, widths, fn)
  if scope == "plans" and (plans == () or plans == "") { return }
  let ids = position-list-ids(scope: scope, plans: plans, storey: storey, fn: fn)
  context {
    let caption = if title == auto { t-str("position_list.title") } else if type(title) == str { [#title] } else { title }
    if ids.len() == 0 {
      if caption != none { block(text(weight: "bold", caption)) }
      text(style: "italic", t-str("position_list.empty"))
    } else {
      position-list-table(ids, title: caption, columns: columns, widths: widths, legend: legend, fn: fn)
    }
  }
}


// --- The quantities of the position plans (issue #9) ------------------------------------------
// What the plans draw, by material and section -- pieces, length, volume, a total per material --, as calc/domains/quantities.py computed it into data/quantities.json at the export (the engineer, 08.10.2026: «le résumé (les métrés) … par matériau et par section, longueurs et volumes»). Printed here and never computed again, but for the rows of the positions a call names, added up by `quantity-sum` the way `quantities.summary` does -- tests/test_quantities.py holds the two equal.

#let quantity-scopes = ("all", "plans", "positions")

// The export's quantities -- an export written before issue #9 has none, and prints an empty summary.
#let load-quantities() = {
  let found = json("../data/quantities.json")
  if found.at("schema_version", default: none) != "1.0" { panic("quantities: data/quantities.json is schema " + repr(found.at("schema_version", default: none)) + " -- export again") }
  found
}

#let quantity-add(a, b) = if a == none { b } else if b == none { a } else { a + b }

// The rows given, added up by material then section, with a total per material: quantities.summary's own rule, for a scope the export could not foresee.
#let quantity-sum(rows) = {
  let groups = (:)
  for r in rows {
    let key = lower(r.material) + "\u{1f}" + lower(r.section)
    let g = groups.at(key, default: (material: r.material, section: r.section, pieces: 0, length_m: none, area_m2: none, volume_m3: none))
    g.pieces += 1
    g.length_m = quantity-add(g.length_m, r.length_m)
    g.area_m2 = quantity-add(g.area_m2, r.area_m2)
    g.volume_m3 = quantity-add(g.volume_m3, r.volume_m3)
    groups.insert(key, g)
  }
  let ordered = groups.keys().sorted().map(k => groups.at(k))
  let totals = (:)
  let order = ()
  for g in ordered {
    if not (g.material in order) { order.push(g.material) }
    let t = totals.at(g.material, default: (material: g.material, pieces: 0, length_m: none, area_m2: none, volume_m3: none))
    t.pieces += g.pieces
    t.length_m = quantity-add(t.length_m, g.length_m)
    t.area_m2 = quantity-add(t.area_m2, g.area_m2)
    t.volume_m3 = quantity-add(t.volume_m3, g.volume_m3)
    totals.insert(g.material, t)
  }
  (groups: ordered, totals: order.map(m => totals.at(m)))
}

// The summary a scope names: the export's own for every plan or for one, added up here for several plans or for chosen positions.
#let quantity-summary(scope, plans, positions, fn) = {
  if not (scope in quantity-scopes) { position-list-refuse(fn, "scope: is \"all\", \"plans\" or \"positions\" -- got " + repr(scope)) }
  let q = load-quantities()
  if scope == "all" { return q.all }
  if scope == "plans" {
    let wanted = if type(plans) == str { (plans,) } else if type(plans) == array { plans } else { position-list-refuse(fn, "plans: is a position plan's id or an array of them -- got " + repr(plans)) }
    for id in wanted {
      if type(id) != str or not (id in q.plans) { position-list-refuse(fn, "no position plan " + repr(id) + " -- " + (if q.plans.len() == 0 { "none saved yet (draw one in Woodcore's position plan tab)" } else { "valid plans: " + q.plans.keys().join(", ") })) }
    }
    if wanted.len() == 1 { return q.plans.at(wanted.first()) }
    return quantity-sum(q.rows.filter(r => r.plan in wanted))
  }
  let wanted = if type(positions) == str { (positions,) } else if type(positions) == array { positions } else { position-list-refuse(fn, "positions: is a position's id or an array of them -- got " + repr(positions)) }
  quantity-sum(q.rows.filter(r => r.position in wanted))
}

// A number as the summary prints it: a length to the centimetre, a volume to the litre, «—» where none was measured -- the decimal a point in every language.
#let quantity-number(value, digits) = if value == none { [—] } else {
  // fmt-decimals drops the zeros a whole number ends on; a column of lengths keeps them, as the plan's legend does
  let parts = fmt-decimals(value, digits).split(".")
  [#(parts.at(0) + "." + (parts.at(1, default: "") + "000").slice(0, digits))]
}

// The table: Material · Section · Pieces · Length [m] · Volume [m³], a bold line of total after each material -- render-table's three rules, a column aligned by what it holds (the engine's own table, as the list of the positions).
#let quantity-table(summary, title: none) = {
  let heading(key) = context t-str("quantities." + key)
  let columns = (
    (label: heading("material"), kind: "text"),
    (label: heading("section"), kind: "text"),
    (label: heading("pieces"), kind: "math"),
    (label: heading("length"), kind: "math"),
    (label: heading("volume"), kind: "math"),
  )
  let rows = ()
  for total in summary.totals {
    for g in summary.groups.filter(g => g.material == total.material) {
      rows.push(([#(if g.material == "" { [—] } else { g.material })], [#(if g.section == "" { [—] } else { g.section })], [#g.pieces], quantity-number(g.length_m, 2), quantity-number(g.volume_m3, 3)))
    }
    rows.push((strong(context t-str("quantities.total")), [], strong[#total.pieces], strong(quantity-number(total.length_m, 2)), strong(quantity-number(total.volume_m3, 3))))
  }
  render-table((title: title, columns: columns, rows: rows, note: none, fit: true))
}

/// **The quantities of the position plans**: what they draw, by material then section -- pieces, length in metres, volume in cubic metres -- with a total per material, in one table: the «métrés» Woodcore measures from the plans' scale at the export.
///
/// ```typ
/// #show-plan-quantities()
/// ```
///
/// ```typ
/// #show-plan-quantities(scope: "plans", plans: "Pavillon", title: [Métrés du pavillon])
/// ```
///
/// ```typ
/// #show-plan-quantities(scope: "positions", positions: ("T001", "S001"), title: none)
/// ```
///
/// A length is a line's along it -- a wall, a beam --, the very length the plan writes beside it; a volume is a timber section's: a rectangle or a circle times its length, a plate or a CLT slab its area times its thickness. A column's height and a wall's are not on a plan, and a steel profile's area is in SZS C5's tables and in no file of Woodcore: those print «—». On an export sheet the same table is `sheet-quantities`.
///
/// - scope (str): "all" what every plan draws, "plans" what `plans` draw, "positions" the positions `positions` wherever they are drawn.
/// - plans (str, array): the position plans, by their ids, for `scope: "plans"`.
/// - positions (str, array): the positions, by their ids, for `scope: "positions"`.
/// - title (auto, none, content, str): the table's numbered caption: auto is «Métrés» in the document's language, none sets none.
/// -> content
#let show-plan-quantities(scope: "all", plans: (), positions: (), title: auto) = {
  let fn = "show-plan-quantities"
  if title != auto and title != none and type(title) != str and type(title) != content {
    position-list-refuse(fn, "title: is auto, none, [content] or a string -- got " + repr(title))
  }
  let summary = quantity-summary(scope, plans, positions, fn)
  context {
    let caption = if title == auto { t-str("quantities.title") } else if type(title) == str { [#title] } else { title }
    if summary.groups.len() == 0 {
      if caption != none { block(text(weight: "bold", caption)) }
      text(style: "italic", t-str("quantities.empty"))
    } else {
      quantity-table(summary, title: caption)
    }
  }
}
