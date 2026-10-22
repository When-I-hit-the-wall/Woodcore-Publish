// The export sheets of a project (v0.114): a plan sheet A0 to A6, portrait or landscape, on which the position plans drawn in Woodcore are set at a chosen scale, beside a legend of their symbols, a schematic section with the storey the sheet shows highlighted, texts of the engineer's own and a title block -- the plan de positions of STE Compact 02 «Plans dans la construction en bois» (p. 12), the one sheet a timber engineer hands to the site.
//
// A sheet is a .typ file of its own, `Plans/<id>.typ` at the top of the project's Typst root, compiled to `Plans/<id>.pdf` beside it (calc/sheets.py). It starts with the show rule `sheet`, which sets the page, and every other thing on it is **placed**: `x` and `y` are millimetres from the sheet's top-left corner -- the page's, the sheet's own margin being the frame drawn round it, not a margin of the page -- so nothing on a sheet flows and nothing moves another.
//
// Each command is one object of the window's sheet editor: Woodcore writes it between two tags, `// woodcore:object sheet-viewport ground-floor` and `// woodcore:/object ground-floor`, as one call in the canonical form calc/typst_objects.py parses and writes back -- named arguments only, one a line, in the order the signatures below state them. **The .typ is the source of truth**: an object written by hand is the same call and prints the same.
//
// ⚠️ formula.typ imports the page and the three images from here by name, on distance.typ's arrangement (docs/typst/api-conventions.md §10bis): this file imports calc-engine.typ and document.typ and nothing from formula.typ, so the chain stays acyclic.
//
// ⚠️ **A sheet is of one kind** (v0.116): a sheet of position plans or a sheet of fire-protection plans, never both -- the engineer: «le plan de position ne doit absolument pas être mélangé avec le plan d'incendie». The page says which (`sheet(kind:)`); calc/sheets.py reads it, and infers it from the objects of a sheet written before v0.116.
#import "calc-engine.typ": report-level, colon-str, plan-figure, plan-legend, svg-number, project-info, t-str
// what a sheet knows of itself and a plan drawn on one, in lib/calc-engine-drawings.typ beside the image commands a sheet's `#place` holds (spec 2026-10-21-commandes-typst-refonte, Q-015)
#import "calc-engine.typ": sheet-state, sheet-scales, sheet-plans, sheet-fire-plans, sheet-last, sheet-refuse, sheet-mm, sheet-words, sheet-text-arg, sheet-plan, sheet-fire-plan, sheet-size, sheet-ratio
#import "document.typ": doc-frame

// The ISO 216 formats, short side and long side in millimetres.
#let sheet-formats = (
  A0: (841, 1189), A1: (594, 841), A2: (420, 594), A3: (297, 420), A4: (210, 297), A5: (148, 210), A6: (105, 148),
)

// The typeface of a sheet: a sans-serif, as a drawing office letters a plan. Typst falls back on its own where none of them is installed.
#let sheet-font = ("Arial", "Liberation Sans")

// The red a section marks the sheet's storey in, as STE Compact 02 marks it: a translucent fill and a dashed outline.
#let sheet-red = "#e30613"

// --- The page --------------------------------------------------------------------------------

/// **An export sheet**, as a show rule at the top of the sheet's file: the page in an ISO format, portrait or landscape, with a frame drawn at `margin` from its edges, the plan's sans-serif and no page number -- the paper of the plan de positions of STE Compact 02. Everything else on the sheet is placed on it in millimetres from its top-left corner (`sheet-text`, `sheet-viewport`, `sheet-legend`, `sheet-section`, `sheet-titleblock`).
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-text(x: 14mm, y: 14mm, body: [Plan de positions], size: 14pt, weight: "bold")
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: false, margin: 5mm)
/// #sheet-text(x: 10mm, y: 10mm, body: [Positionsplan Erdgeschoss], size: 11pt)
/// ```
///
/// Woodcore writes it between two tags as the object `sheet-page`, and the format and the frame are edited there; written by hand, it is the same line. The page's own margin is nought: `margin` is where the frame stands, and `x` and `y` count from the paper's corner.
///
/// - doc (content): the sheet, handed over by `#show:`.
/// - format (str): the ISO format, "A0" to "A6".
/// - landscape (bool): true lays the sheet on its long side.
/// - margin (length, int, float): how far the frame stands from the paper's edge -- a length, or millimetres.
/// - kind (str): what the sheet shows, "position" its position plans or "fire" its fire-protection plans -- never both, the window offering the objects of the one kind alone.
/// -> content
#let sheet(doc, format: "A3", landscape: true, margin: 10mm, kind: "position") = {
  let fn = "sheet"
  if type(format) != str or not (format in sheet-formats) {
    sheet-refuse(fn, "format: is one of " + sheet-formats.keys().join(", ") + " -- got " + repr(format))
  }
  if type(landscape) != bool { sheet-refuse(fn, "landscape: is true or false -- got " + repr(landscape)) }
  if not (kind in ("position", "fire")) { sheet-refuse(fn, "kind: is \"position\" or \"fire\" -- got " + repr(kind)) }
  let m = sheet-mm(fn, "margin:", margin)
  let (short, long) = sheet-formats.at(format)
  let (w, h) = if landscape { (long, short) } else { (short, long) }
  set page(width: w * 1mm, height: h * 1mm, margin: 0pt, header: none, footer: none, numbering: none,
    background: if m > 0mm { place(top + left, dx: m, dy: m, rect(width: w * 1mm - 2 * m, height: h * 1mm - 2 * m, stroke: 0.7pt + black)) })
  set text(font: sheet-font, size: 9pt)
  set par(justify: false)
  sheet-state.update((format: format, landscape: landscape, width: w, height: h, margin: m / 1mm, kind: kind))
  // a sheet prints at level 2 -- its titles, legends, lengths and centres, as it always did -- unless `--input level=` says otherwise (spec 2026-10-20-indices-et-niveaux, UI-003, ARCH-RISK-608): the report's state starts at 1, which would have left them out
  report-level.update(int(sys.inputs.at("level", default: "2")))
  // Each object of a sheet is a raw `#place(…) <kind>` (spec 2026-10-21-commandes-typst-refonte, Q-015): placed again with, at the start of what it holds, the box the window's sheet editor reads -- where Typst put it on the paper, its size, its kind (the label), the drawing's width and scale a plan left in `sheet-last`. A `#place` without such a label is no object of the sheet and is left as it is.
  show place: it => {
    let kind = it.at("label", default: none)
    if kind == none or not str(kind).starts-with("sheet-") { return it }
    place(it.alignment, dx: it.dx, dy: it.dy, {
      // a mark where the object starts -- its top-left corner on the paper, wherever it is placed from --, then the object, then its one box: the drawing's width and scale are known only once it is drawn
      [#metadata(none) <woodcore-sheet-start>]
      it.body
      context {
        let at = query(selector(<woodcore-sheet-start>).before(here())).last().location().position()
        let size = measure(it.body)
        let last = sheet-last.get()
        [#metadata((kind: str(kind), x: at.x / 1mm, y: at.y / 1mm, w: size.width / 1mm, h: size.height / 1mm, dw: last.dw, n: last.n)) <woodcore-sheet-box>]
      }
      sheet-last.update((dw: none, n: none))
    })
  }
  doc
}

// --- Texts -----------------------------------------------------------------------------------

// --- Plans -----------------------------------------------------------------------------------

// A section on a sheet (Q-015): its title and the section drawn at its scale or width, the storey highlighted -- `(shown, dw, n)`. What `sheet-section` placed, and what `image-section` prints in a sheet's `#place`.
#let sheet-section-content(fn, plan, storey, scale, width, title) = {
  sheet-text-arg(fn, "title:", title)
  if storey != none and type(storey) != str { sheet-refuse(fn, "storey: is a storey's designation, \"EG\", or none -- got " + repr(storey)) }
  let heading(n) = if title == none { none } else if title == auto {
    context text(size: 12pt, weight: "bold", t-str("sheet.section") + if n != none { " (" + t-str("sheet.scale_short") + sheet-ratio(n) + ")" } else { "" })
  } else { text(size: 12pt, weight: "bold", sheet-words(title)) }
  if plan == none {
    let w = if width == none { 60mm } else { sheet-mm(fn, "width:", width) }
    let parts = (heading(none), context doc-frame(w, t-str("document.plan"))).filter(c => c != none)
    return (shown: stack(spacing: 3mm, ..parts), dw: w / 1mm, n: none)
  }
  let p = sheet-plan(fn, plan)
  let extra = ""
  if storey != none {
    let boxes = p.at("storey_boxes", default: ())
    let found = boxes.find(b => b.at("storey", default: none) == storey)
    if found == none {
      sheet-refuse(fn, "the section " + repr(plan) + " has no box for the storey " + repr(storey) + " -- " + (if boxes.len() == 0 { "it has none drawn yet (Woodcore's storey box tool)" } else { "its boxes are " + boxes.map(b => b.at("storey", default: "?")).join(", ") }))
    }
    let w = p.at("unit", default: 1)
    extra = "<rect x=\"" + svg-number(found.x) + "\" y=\"" + svg-number(found.y) + "\" width=\"" + svg-number(found.w) + "\" height=\"" + svg-number(found.h) + "\" fill=\"" + sheet-red + "\" fill-opacity=\"0.18\" stroke=\"" + sheet-red + "\" stroke-width=\"" + svg-number(1.4 * w) + "\" stroke-dasharray=\"" + svg-number(7 * w) + " " + svg-number(4 * w) + "\"/>"
  }
  let size = sheet-size(fn, plan, p, scale, width)
  let known = if size.n != none { sheet-scales.update(a => if size.n in a { a } else { a + (size.n,) }) }
  let parts = (heading(size.n), plan-figure(p, size.s, extra: extra)).filter(c => c != none)
  (shown: known + stack(spacing: 3mm, ..parts), dw: p.crop.w * size.s / 1mm, n: size.n)
}

/// **A schematic section as an image**, for a `#place` of an export sheet (spec 2026-10-21-commandes-typst-refonte, Q-013, Q-015): the section plan drawn in Woodcore, its storey lines and their bubbles, the storey the sheet shows highlighted in a translucent red with a dashed outline, its title above it -- what `#sheet-section` placed.
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #place(top + left, dx: 12mm, dy: 14mm, image-section("Fluchttreppe", width: 50mm)) <sheet-section>
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #place(top + left, dx: 12mm, dy: 14mm, image-section(none, title: [Schnitt A-A])) <sheet-section>
/// ```
///
/// - plan (none, str): the section plan, by its id; none draws a frame in its place.
/// - storey (none, str): the storey to highlight, as its box names it ("EG", "1.OG"); none highlights nothing.
/// - scale (none, int, float): the n of 1:n, where the section is calibrated.
/// - width (none, length, int, float): the width the section is printed at, where it is given no scale.
/// - title (auto, none, content, str): auto is «Coupe schématique» in the report's language with the scale; none prints no title.
/// -> content
#let image-section(plan, storey: none, scale: none, width: none, title: auto) = context {
  let r = sheet-section-content("image-section", plan, storey, scale, width, title)
  sheet-last.update((dw: r.dw, n: r.n))
  r.shown
}

// The legend's title over a framed block of `lines` (each {key, text, swatch}, a fire plan's also `term` or `engine`), or none where it shows nothing. In a context, as the title is the engine's word.
#let sheet-legend-content(w, title, lines) = {
  let head = if title == none { none } else if title == auto { text(size: 14pt, weight: "bold", t-str("sheet.legend") + colon-str()) } else { text(size: 14pt, weight: "bold", sheet-words(title)) }
  let body = if lines.len() == 0 { none } else { block(width: w, stroke: 0.5pt + black, inset: 2mm, plan-legend((legend: lines), w - 4mm)) }
  let parts = (head, body).filter(c => c != none)
  if parts.len() > 0 { stack(spacing: 2.5mm, ..parts) } else { none }
}

// The lines of the legend of `plans` -- auto the position plans the sheet shows --, each symbol once, the quantities of a symbol two plans draw added.
#let sheet-legend-lines(fn, plans) = {
  let ids = if plans == auto { sheet-plans.final() } else if type(plans) == str { (plans,) } else { plans }
  let lines = ()
  let keys = ()
  for id in ids {
    let p = sheet-plan(fn, id)
    let legend = p.at("legend", default: ())
    if type(legend) != array { continue }
    for line in legend {
      if not (line.key in keys) {
        keys.push(line.key)
        lines.push(line)
      } else if "quantity" in line {
        // the same symbol on two plans of the sheet: its quantities added (v0.117), each plan measured by the export
        let i = keys.position(k => k == line.key)
        let kept = lines.at(i)
        if "quantity" in kept and kept.quantity.unit == line.quantity.unit {
          lines.at(i) = kept + (quantity: (value: kept.quantity.value + line.quantity.value, unit: line.quantity.unit))
        } else if not ("quantity" in kept) {
          lines.at(i) = kept + (quantity: line.quantity)
        }
      }
    }
  }
  lines
}

// --- Fire-protection plans (v0.115) ----------------------------------------------------------

// The lines of the legend of the fire-protection plans `plans` -- auto those the sheet shows --, each line once.
#let sheet-fire-legend-lines(fn, plans) = {
  let ids = if plans == auto { sheet-fire-plans.final() } else if type(plans) == str { (plans,) } else { plans }
  let lines = ()
  let keys = ()
  for id in ids {
    let p = sheet-fire-plan(fn, id)
    for line in p.at("legend_lines", default: ()) {
      if not (line.key in keys) {
        keys.push(line.key)
        lines.push(line)
      }
    }
  }
  lines
}

/// **The legend of a sheet as an image**, for a `#place` of an export sheet (spec 2026-10-21-commandes-typst-refonte, Q-013, Q-015): the symbols of the plans the sheet shows, each once, their quantities added where two plans draw one -- or the fire-protection plans' lines -- under its title, in a frame: what `#sheet-legend` and `#sheet-fire-legend` placed.
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #place(top + left, dx: 10mm, dy: 10mm, image-positions-plan("Velo-Unterstand", width: 60mm, title: auto)) <sheet-viewport>
/// #place(top + left, dx: 75mm, dy: 10mm, image-legend(width: 25mm)) <sheet-legend>
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true, kind: "fire")
/// #place(top + left, dx: 10mm, dy: 10mm, image-legend(plans: "Treppenhaus", kind: "fire", width: 80mm)) <sheet-fire-legend>
/// ```
///
/// - plans (auto, str, array): the plans whose symbols are listed; auto is every plan the sheet's viewports show.
/// - kind (str): `"position"` the position plans' symbols, `"fire"` the fire-protection plans' lines.
/// - width (length, int, float): the width its columns share -- a length or millimetres.
/// - title (auto, none, content, str): auto is «Légende» in the report's language; none prints no title.
/// -> content
#let image-legend(plans: auto, kind: "position", width: 120mm, title: auto) = context {
  let fn = "image-legend"
  if not (kind in ("position", "fire")) { sheet-refuse(fn, "kind: is \"position\" or \"fire\" -- got " + repr(kind)) }
  if plans != auto and type(plans) != str and type(plans) != array {
    sheet-refuse(fn, "plans: is auto, a plan's id or an array of them -- got " + repr(plans))
  }
  sheet-text-arg(fn, "title:", title)
  let lines = if kind == "fire" { sheet-fire-legend-lines(fn, plans) } else { sheet-legend-lines(fn, plans) }
  let shown = sheet-legend-content(sheet-mm(fn, "width:", width), title, lines)
  if shown == none { [] } else { shown }
}

// --- The list of the positions (v0.116) ------------------------------------------------------

// --- The quantities (issue #9) -----------------------------------------------------------------

// --- The title block -------------------------------------------------------------------------

// One cell of the title block: its label, small and grey, above its value.
#let sheet-cell(label, value, size: 7.5pt) = {
  set par(leading: 0.35em)
  text(size: 4.5pt, fill: luma(35%), label)
  linebreak()
  text(size: size, value)
}

// A day written as the report writes one, «25.09.2026», from a datetime or an ISO date; anything else as it is.
#let sheet-day(d) = {
  if type(d) == datetime { d.display("[day].[month].[year]") }
  else if type(d) == str and d.match(regex("^\d{4}-\d{2}-\d{2}$")) != none {
    let (y, m, day) = d.split("-")
    day + "." + m + "." + y
  } else { sheet-words(d) }
}

// A field of the .woodcore as content, its lines kept apart: a client's name and its address on two lines.
#let sheet-field(info, key) = {
  let value = str(info.at(key, default: ""))
  if value.trim() == "" { [] } else { value.split(regex("\r?\n")).map(l => [#l.trim()]).join(linebreak()) }
}

/// **The title block of a sheet as an image**, for a `#place` of an export sheet (spec 2026-10-21-commandes-typst-refonte, Q-013, Q-015): STE Compact 02's cartouche -- the logo, the object and the element, the client and the architect, the phase, the project's and the plan's numbers, the latest revision, who drew it, the date, the scales of the sheet's plans and its size --, each field the project's own where it is auto: what `#sheet-titleblock` placed. Woodcore places it in the sheet's bottom right corner, `#place(bottom + right, dx: -10mm, dy: -10mm, …)`.
///
/// ```typ
/// #show: sheet.with(format: "A4", landscape: true)
/// #place(bottom + right, dx: -10mm, dy: -10mm, image-titleblock(plan-number: "P-01")) <sheet-titleblock>
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A4", landscape: true)
/// #place(bottom + right, dx: -10mm, dy: -10mm, image-titleblock(width: 180mm, phase: "Ausführung", logo: none)) <sheet-titleblock>
/// ```
///
/// - width (auto, length, int, float): its width; auto is 200 mm, or the frame's width where that is narrower.
/// - logo (auto, none, content): auto is the BFH's logo; none leaves the cell empty; content stands in its place.
/// - object (auto, none, str, content): the building, the project's name at auto.
/// - element (none, str, content): what the sheet shows, «Plan de positions».
/// - client (auto, none, str, content): the client, the project's at auto.
/// - architect (none, str, content): the architect.
/// - phase (none, str, content): the SIA phase, «51 Projet d'exécution».
/// - project-number (auto, none, str, content): the project's number, the project's at auto.
/// - plan-number (none, str, content): the sheet's number.
/// - index (auto, none, str, int): the revision's index, the journal's newest at auto.
/// - revision-date (auto, none, str, datetime): that revision's date.
/// - revision-author (auto, none, str, content): who made it -- the short form the journal gives it.
/// - modification (auto, none, str, content): what it changed -- its label in the journal.
/// - drawn-by (auto, none, str, content): who drew the sheet, the project's author at auto.
/// - date (auto, none, str, datetime): the sheet's date, today at auto.
/// - scale (auto, none, str, content): the scales, every scale the sheet's plans are drawn at at auto.
/// - size (auto, none, str, content): the sheet's size, its format in millimetres at auto.
/// -> content
#let image-titleblock(width: auto, logo: auto, object: auto, element: none, client: auto, architect: none, phase: none, project-number: auto, plan-number: none, index: auto, revision-date: auto, revision-author: auto, modification: auto, drawn-by: auto, date: auto, scale: auto, size: auto) = {
  let fn = "image-titleblock"
  for (what, v) in (("object:", object), ("element:", element), ("client:", client), ("architect:", architect), ("phase:", phase), ("project-number:", project-number), ("plan-number:", plan-number), ("revision-author:", revision-author), ("modification:", modification), ("drawn-by:", drawn-by), ("scale:", scale), ("size:", size)) {
    sheet-text-arg(fn, what, v)
  }
  if logo != auto and logo != none and type(logo) != content { sheet-refuse(fn, "logo: is auto, none or [content] -- got " + repr(logo)) }
  // The rows: the object and the element, then four of a line each -- room for a small label above a value.
  let height = 43mm
  context {
    let info = project-info()
    let revision = info.at("revision", default: none)
    let rev(key) = if revision == none { none } else { revision.at(key, default: none) }
    let on = sheet-state.get()
    let m = if on == none { 0mm } else { on.margin * 1mm }
    let frame = if on == none { none } else { on.width * 1mm - 2 * m }
    let w = if width == auto { if frame == none { 200mm } else { calc.min(200mm, frame) } } else { sheet-mm(fn, "width:", width) }
    let pick(v, fallback) = if v == auto { fallback } else if v == none { [] } else if type(v) == int { [#v] } else { sheet-words(v) }
    let scales = sheet-scales.final()
    let cells = (
      object: pick(object, [#info.at("name", default: "")]),
      element: pick(element, []),
      client: pick(client, sheet-field(info, "client")),
      architect: pick(architect, []),
      phase: pick(phase, []),
      project_number: pick(project-number, [#info.at("number", default: "")]),
      plan_number: pick(plan-number, []),
      index: if index == auto { let i = rev("index"); if i == none { [] } else { [#i] } } else { pick(index, []) },
      revision_date: if revision-date == auto { let d = rev("date"); if d == none { [] } else { sheet-day(d) } } else if revision-date == none { [] } else { sheet-day(revision-date) },
      revision_author: pick(revision-author, [#(if rev("initials") == none { "" } else { rev("initials") })]),
      modification: pick(modification, [#(if rev("label") == none { "" } else { rev("label") })]),
      drawn_by: pick(drawn-by, sheet-field(info, "author")),
      date: if date == auto { sheet-day(datetime.today()) } else if date == none { [] } else { sheet-day(date) },
      scale: pick(scale, [#scales.map(sheet-ratio).join(" / ")]),
      size: pick(size, if on == none { [] } else { [#calc.max(on.width, on.height) #sym.times #calc.min(on.width, on.height) mm] }),
    )
    let label(key) = t-str("sheet." + key)
    let mark = if logo == auto { image("assets/logo-bfh.png", width: calc.min(0.31 * w - 6mm, 50mm)) } else if logo == none { [] } else { logo }
    let c(colspan: 1, rowspan: 1, key, size: 7.5pt) = grid.cell(colspan: colspan, rowspan: rowspan, sheet-cell(label(key), cells.at(key), size: size))
    block(width: w, fill: white, grid(
      columns: (58fr, 13fr, 17fr, 13fr, 51fr, 24fr, 24fr),
      rows: (height - 26mm, 6.5mm, 6.5mm, 6.5mm, 6.5mm),
      stroke: 0.5pt + black,
      inset: (x: 1.2mm, y: 0.7mm),
      grid.cell(rowspan: 5, align: center + horizon, mark),
      c(colspan: 4, "object", size: 13pt), c(colspan: 2, "element", size: 9pt),
      c(colspan: 3, rowspan: 2, "client"), c(rowspan: 2, "architect"), c(colspan: 2, "phase"),
      c("project_number"), c("plan_number"),
      c(rowspan: 2, "index"), c(rowspan: 2, "revision_date"), c(rowspan: 2, "revision_author"), c(rowspan: 2, "modification"), c("drawn_by"), c("scale"),
      c("date"), c("size"),
    ))
  }
}
