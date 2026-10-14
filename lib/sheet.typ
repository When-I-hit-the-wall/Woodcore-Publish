// The export sheets of a project (v0.114): a plan sheet A0 to A6, portrait or landscape, on which the position plans drawn in Woodcore are set at a chosen scale, beside a legend of their symbols, a schematic section with the storey the sheet shows highlighted, texts of the engineer's own and a title block -- the plan de positions of STE Compact 02 «Plans dans la construction en bois» (p. 12), the one sheet a timber engineer hands to the site.
//
// A sheet is a .typ file of its own, `Plans/<id>.typ` at the top of the project's Typst root, compiled to `Plans/<id>.pdf` beside it (calc/sheets.py). It starts with the show rule `sheet`, which sets the page, and every other thing on it is **placed**: `x` and `y` are millimetres from the sheet's top-left corner -- the page's, the sheet's own margin being the frame drawn round it, not a margin of the page -- so nothing on a sheet flows and nothing moves another.
//
// Each command is one object of the window's sheet editor: Woodcore writes it between two tags, `// woodcore:object sheet-viewport ground-floor` and `// woodcore:/object ground-floor`, as one call in the canonical form calc/typst_objects.py parses and writes back -- named arguments only, one a line, in the order the signatures below state them. **The .typ is the source of truth**: an object written by hand is the same call and prints the same.
//
// ⚠️ formula.typ imports the six commands from here by name, on distance.typ's arrangement (docs/typst/api-conventions.md §10bis): this file imports calc-engine.typ, document.typ and positions.typ and nothing from formula.typ, so the chain stays acyclic.
//
// ⚠️ **A sheet is of one kind** (v0.116): a sheet of position plans or a sheet of fire-protection plans, never both -- the engineer: «le plan de position ne doit absolument pas être mélangé avec le plan d'incendie». The page says which (`sheet(kind:)`); calc/sheets.py reads it, and infers it from the objects of a sheet written before v0.116.
#import "calc-engine.typ": colon-str, load-fire-plans, load-plans, plan-figure, plan-legend, plan-number, plan-scale-bar, project-info, t-str
#import "document.typ": doc-frame
#import "positions.typ": position-list-ids, position-list-table, quantity-summary, quantity-table

// --- What a sheet knows of itself ------------------------------------------------------------
//
// Three states, each read by the title block and the legend in their `context`: the format the show rule set, the scales the viewports and sections are drawn at, and the plans they show. `.final()` is what lets the title block stand anywhere in the file and still name every scale of the sheet.
#let sheet-state = state("woodcore-sheet", none)
#let sheet-scales = state("woodcore-sheet-scales", ())
#let sheet-plans = state("woodcore-sheet-plans", ())
// The fire-protection plans the viewports show (v0.115): a state of their own, a fire plan and a position plan being free to share an id.
#let sheet-fire-plans = state("woodcore-sheet-fire-plans", ())

// The ISO 216 formats, short side and long side in millimetres.
#let sheet-formats = (
  A0: (841, 1189), A1: (594, 841), A2: (420, 594), A3: (297, 420), A4: (210, 297), A5: (148, 210), A6: (105, 148),
)

// The typeface of a sheet: a sans-serif, as a drawing office letters a plan. Typst falls back on its own where none of them is installed.
#let sheet-font = ("Arial", "Liberation Sans")

// The red a section marks the sheet's storey in, as STE Compact 02 marks it: a translucent fill and a dashed outline.
#let sheet-red = "#e30613"

// An argument that is not what the command takes is refused naming the command and what to write -- a `panic` inside an `if`, never `assert(cond, message: ...)`, whose message Typst builds before it tests the condition (v0.63.1).
#let sheet-refuse(fn, message) = panic(fn + ": " + message)

// A coordinate or a size of a sheet: a length, or a number of millimetres.
#let sheet-mm(fn, what, v) = {
  if type(v) == length { v }
  else if (type(v) == int or type(v) == float) and type(v) != bool { v * 1mm }
  else { sheet-refuse(fn, what + " is a length, 20mm, or a number of millimetres -- got " + repr(v)) }
}

// The engineer's own words as content: a string as it is written, content passed through, never looked up in the glossary.
#let sheet-words(x) = if x == none { [] } else if type(x) == str { [#x] } else { x }

// A text argument: none, content or a string.
#let sheet-text-arg(fn, what, x) = {
  if x != none and x != auto and type(x) != content and type(x) != str {
    sheet-refuse(fn, what + " is [content] or a string -- got " + repr(x))
  }
}

// A plan of the export by its id, refused naming the ones there are.
#let sheet-plan(fn, plan) = {
  let plans = load-plans().plans
  if type(plan) != str or not (plan in plans) {
    sheet-refuse(fn, "no plan " + repr(plan) + " -- " + (if plans.len() == 0 { "none saved yet (draw one in Woodcore's position plan tab)" } else { "valid plans: " + plans.keys().join(", ") }))
  }
  plans.at(plan)
}

// A fire-protection plan of the export by its id, refused naming the ones there are (v0.115).
#let sheet-fire-plan(fn, plan) = {
  let plans = load-fire-plans().plans
  if type(plan) != str or not (plan in plans) {
    sheet-refuse(fn, "no fire-protection plan " + repr(plan) + " -- " + (if plans.len() == 0 { "none saved yet (draw one in Woodcore's fire-protection plan tab)" } else { "valid plans: " + plans.keys().join(", ") }))
  }
  plans.at(plan)
}

// The size a plan is drawn at on a sheet, as (s: the length of one of its sheet units, n: the scale 1:n or none): from `scale` where the plan is calibrated -- a metre of the building is `units_per_m` sheet units and is printed 1000 mm / n long, so the drawing is crop.w / units_per_m / n · 1000 mm wide -- else from `width`. One of the two and not both: a viewport has one size.
#let sheet-size(fn, plan, p, scale, width, tab: "position plan") = {
  let calibration = p.at("scale", default: none)
  let per-m = if calibration == none { none } else { calibration.at("units_per_m", default: none) }
  if scale != none and width != none {
    sheet-refuse(fn, "give scale: or width:, not both -- a drawing has one size")
  }
  if scale != none {
    if type(scale) == bool or not (type(scale) in (int, float)) or scale <= 0 {
      sheet-refuse(fn, "scale: is the n of 1:n, 100 for 1:100 -- got " + repr(scale))
    }
    if per-m == none {
      sheet-refuse(fn, "the plan " + repr(plan) + " has no scale, so it cannot be printed at 1:" + str(scale) + " -- calibrate it in Woodcore's " + tab + " tab, or give width: instead")
    }
    (s: 1000mm / (scale * per-m), n: scale)
  } else if width != none {
    let w = sheet-mm(fn, "width:", width)
    if w <= 0mm { sheet-refuse(fn, "width: is greater than 0 -- got " + repr(width)) }
    let s = w / p.crop.w
    let n = if per-m == none { none } else {
      let raw = 1000mm / (s * per-m)
      if raw >= 20 { calc.round(raw / 5) * 5 } else { calc.round(raw) }
    }
    (s: s, n: n)
  } else {
    sheet-refuse(fn, "the plan " + repr(plan) + " needs a size: scale: 100 where the plan is calibrated in Woodcore" + (if per-m == none { " (it is not)" } else { "" }) + ", or width: 180mm")
  }
}

// «1:100» of a scale n.
#let sheet-ratio(n) = "1:" + str(int(n))

// The line above a plan on a sheet, as STE Compact 02 heads each plan of a plan de positions (p. 12): «Nom — description, étage (éch. 1:n)» -- the plan's name and description as the engineer typed them in Woodcore, the storey it shows, the scale it is printed at. A part the plan does not have is left out with its separator; a plan with neither a name nor a description is named by its id. `title` is the argument: auto this line, none (or false) no line, content or a string the engineer's own words. In a context: the abbreviation of «scale» is the engine's word, in the report's language.
#let sheet-plan-title(fn, id, p, n, title) = {
  if title == none or title == false { return none }
  if title != auto { return text(size: 10pt, weight: "bold", sheet-words(title)) }
  let name = str(p.at("name", default: "")).trim()
  let label = str(p.at("label", default: "")).trim()
  let storey = str(p.at("storey", default: "")).trim()
  let line = if name != "" { name } else if label == "" { id } else { "" }
  if label != "" { line = if line == "" { label } else { line + " — " + label } }
  if storey != "" { line += ", " + storey }
  if n != none { line += " (" + t-str("sheet.scale_short") + sheet-ratio(n) + ")" }
  text(size: 10pt, weight: "bold", line)
}

// A viewport's `title:`: auto, none, false, a string or content.
#let sheet-title-arg(fn, title) = {
  if title != auto and title != none and title != false and type(title) != content and type(title) != str {
    sheet-refuse(fn, "title: is auto (the plan's name, description, storey and scale), none, [content] or a string -- got " + repr(title))
  }
}

// What the window's sheet editor reads of every object it draws a frame round: the object's kind and the box it takes on the paper, in millimetres from the sheet's top-left corner -- `metadata`, which prints nothing, labelled `<woodcore-sheet-box>` and read back with `typst eval 'query(<woodcore-sheet-box>).map(it => it.value)' --in <sheet>` (calc/tools/sheet_editor.py). Every command below emits exactly one, a body that prints nothing a box of nought, so the boxes come in the order the file writes its objects. A plan or a section adds `dw`, the width its drawing is printed at, and `n`, its scale where it has one: what a frame dragged larger is turned into.
#let sheet-box(kind, x, y, size, ..extra) = [#metadata((kind: kind, x: x / 1mm, y: y / 1mm, w: size.width / 1mm, h: size.height / 1mm, ..extra.named())) <woodcore-sheet-box>]

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
  doc
}

// --- Texts -----------------------------------------------------------------------------------

/// **A text on the sheet**: the plan's title and subtitle, a remark, anything the engineer writes there, placed at `x` and `y` -- its top-left corner -- in the size and weight given.
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-text(x: 14mm, y: 14mm, body: [Plan de positions], size: 16pt, weight: "bold")
/// #sheet-text(x: 14mm, y: 22mm, body: [Parois du rez, plancher sur rez (éch. 1:100)], size: 10pt)
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-text(x: 12mm, y: 60mm, width: 90mm, body: [*Remarque :* \ Les plans de l'architecte font foi quant aux dimensions.])
/// ```
///
/// The words are the engineer's and are never translated. `width` makes a paragraph that wraps; auto keeps the text on the lines it is written on.
///
/// - x (length, int, float): the left edge, from the sheet's left edge -- a length or millimetres.
/// - y (length, int, float): the top edge, from the sheet's top edge.
/// - body (none, content, str): the text; none prints nothing.
/// - size (length): the size of the letters.
/// - weight (str, int): "regular", "bold", or a weight from 100 to 900.
/// - width (auto, length, int, float): the width the text wraps at; auto does not wrap it.
/// -> content
#let sheet-text(x: 0mm, y: 0mm, body: none, size: 10pt, weight: "regular", width: auto) = {
  let fn = "sheet-text"
  let x = sheet-mm(fn, "x:", x)
  let y = sheet-mm(fn, "y:", y)
  sheet-text-arg(fn, "body:", body)
  if type(size) != length { sheet-refuse(fn, "size: is a length, 10pt -- got " + repr(size)) }
  let w = if width == auto { auto } else { sheet-mm(fn, "width:", width) }
  if body != none {
    let shown = block(width: w, text(size: size, weight: weight, sheet-words(body)))
    place(top + left, dx: x, dy: y, shown)
    context sheet-box(fn, x, y, measure(shown))
  } else {
    sheet-box(fn, x, y, (width: 0mm, height: 0mm))
  }
}

// --- Plans -----------------------------------------------------------------------------------

/// **A position plan on the sheet**, at a scale: the plan drawn in Woodcore -- the architect's page faded under it, the STE symbols, their numbers and the axes over it -- cut to the frame it was cropped to and placed with its top-left corner at `x` and `y`. At `scale: 100` it is printed at 1:100 exactly, from the plan's calibration; a plan that has none is given its `width` instead.
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-viewport(plan: "Pavillon", x: 14mm, y: 14mm, width: 75mm)
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-viewport(plan: "Velo-Unterstand", x: 12mm, y: 20mm, width: 100mm, highlight: "T001", axes: false)
/// ```
///
/// The scale it is drawn at is what the title block's «Éch.» names (`sheet-titleblock`), and the plan is one the legend lists (`sheet-legend`). Above it stands its title, as STE heads each plan of a plan de positions: «Nom — description, étage (éch. 1:100)», from the plan's name, description and storey in Woodcore; `title: none` leaves it out. Unlike `show-plan`, nothing caps it to the page: a sheet is laid out by the engineer, and a plan larger than the sheet runs past its edge.
///
/// - plan (none, str): the plan, by its id in Woodcore's «Plan de positions» tab; none draws a frame in its place.
/// - x (length, int, float): the plan's left edge, from the sheet's left edge.
/// - y (length, int, float): the plan's top edge, from the sheet's top edge.
/// - scale (none, int, float): the n of 1:n -- 100 prints the plan at 1:100, which needs the plan calibrated in Woodcore.
/// - width (none, length, int, float): the width the plan is printed at, where it is given no scale -- a length or millimetres.
/// - highlight (none, str, array): the position(s) set on a halo, each drawn on this plan.
/// - axes (bool): the plan's axes and their bubbles.
/// - dimensions (bool): the dimensions drawn on the plan.
/// - lengths (bool): the lengths written beside its elements.
/// - scale-bar (bool): a scale bar under the plan, where it is calibrated.
/// - caption (none, auto, content, str): a line under the plan: auto names it with its scale, «Grundriss (1:100)»; none prints none.
/// - title (auto, none, bool, content, str): the line above the plan: auto is «Nom — description, étage (éch. 1:n)» from the plan; none or false prints none; content or a string the engineer's own words.
/// -> content
#let sheet-viewport(plan: none, x: 0mm, y: 0mm, scale: none, width: none, highlight: none, axes: true, dimensions: true, lengths: true, scale-bar: false, caption: none, title: auto) = {
  let fn = "sheet-viewport"
  let x = sheet-mm(fn, "x:", x)
  let y = sheet-mm(fn, "y:", y)
  if type(axes) != bool { sheet-refuse(fn, "axes: is true or false -- got " + repr(axes)) }
  if type(scale-bar) != bool { sheet-refuse(fn, "scale-bar: is true or false -- got " + repr(scale-bar)) }
  if type(dimensions) != bool { sheet-refuse(fn, "dimensions: is true or false -- got " + repr(dimensions)) }
  if type(lengths) != bool { sheet-refuse(fn, "lengths: is true or false -- got " + repr(lengths)) }
  sheet-text-arg(fn, "caption:", caption)
  sheet-title-arg(fn, title)
  if plan == none {
    let w = if width == none { 80mm } else { sheet-mm(fn, "width:", width) }
    return {
      place(top + left, dx: x, dy: y, context doc-frame(w, t-str("document.plan")))
      context sheet-box(fn, x, y, measure(doc-frame(w, t-str("document.plan"))), dw: w / 1mm, n: none)
    }
  }
  let p = sheet-plan(fn, plan)
  let marked = if highlight == none { () } else if type(highlight) == str { (highlight,) } else { highlight }
  for label in marked {
    if type(label) != str or not (label in p.labels) {
      sheet-refuse(fn, "the plan " + repr(plan) + " does not show " + repr(label) + " -- it shows " + (if p.labels.len() == 0 { "no position" } else { p.labels.join(", ") }))
    }
  }
  let size = sheet-size(fn, plan, p, scale, width)
  let drawing = plan-figure(p, size.s, marked: marked, axes: axes, dimensions: dimensions, lengths: lengths)
  let head = context sheet-plan-title(fn, plan, p, size.n, title)
  let parts = if title == none or title == false { (drawing,) } else { (head, drawing) }
  if scale-bar and "scale" in p {
    parts.push(align(left, plan-scale-bar(p.scale.units_per_m * size.s, p.crop.w * size.s)))
  }
  if caption != none {
    let line = if caption == auto {
      [#p.label#if size.n != none [ (#sheet-ratio(size.n))]]
    } else { sheet-words(caption) }
    parts.push(text(size: 9pt, line))
  }
  sheet-plans.update(a => if plan in a { a } else { a + (plan,) })
  if size.n != none { sheet-scales.update(a => if size.n in a { a } else { a + (size.n,) }) }
  let shown = stack(spacing: 2mm, ..parts)
  place(top + left, dx: x, dy: y, shown)
  context sheet-box(fn, x, y, measure(shown), dw: p.crop.w * size.s / 1mm, n: size.n)
}

/// **A schematic section on the sheet**, with the storey the sheet shows highlighted: the section plan drawn in Woodcore -- its storey lines, each with its designation in a bubble at both ends -- and over the box of `storey` a translucent red with a dashed red outline, as STE Compact 02 marks the storey a plan de positions shows (p. 12). Its title stands above it, «Coupe schématique (éch. 1:200)».
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-section(plan: "Fluchttreppe", x: 12mm, y: 14mm, width: 50mm)
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-section(plan: none, x: 12mm, y: 14mm, title: [Schnitt A-A])
/// ```
///
/// A section plan is a plan whose role is «section» in Woodcore; its storey boxes are drawn there with the storey tool. A storey the section has no box for is refused, naming the boxes it has.
///
/// - plan (none, str): the section plan, by its id; none draws a frame in its place.
/// - storey (none, str): the storey to highlight, as its box names it ("EG", "1.OG"); none highlights nothing.
/// - x (length, int, float): the left edge of the section and its title, from the sheet's left edge.
/// - y (length, int, float): the top edge of the title, from the sheet's top edge.
/// - scale (none, int, float): the n of 1:n, where the section is calibrated.
/// - width (none, length, int, float): the width the section is printed at, where it is given no scale.
/// - title (auto, none, content, str): auto is «Coupe schématique» in the report's language with the scale; none prints no title.
/// -> content
#let sheet-section(plan: none, storey: none, x: 0mm, y: 0mm, scale: none, width: none, title: auto) = {
  let fn = "sheet-section"
  let x = sheet-mm(fn, "x:", x)
  let y = sheet-mm(fn, "y:", y)
  sheet-text-arg(fn, "title:", title)
  if storey != none and type(storey) != str { sheet-refuse(fn, "storey: is a storey's designation, \"EG\", or none -- got " + repr(storey)) }
  let heading(n) = if title == none { none } else if title == auto {
    context text(size: 12pt, weight: "bold", t-str("sheet.section") + if n != none { " (" + t-str("sheet.scale_short") + sheet-ratio(n) + ")" } else { "" })
  } else { text(size: 12pt, weight: "bold", sheet-words(title)) }
  if plan == none {
    let w = if width == none { 60mm } else { sheet-mm(fn, "width:", width) }
    let parts = (heading(none), context doc-frame(w, t-str("document.plan"))).filter(c => c != none)
    let shown = stack(spacing: 3mm, ..parts)
    return {
      place(top + left, dx: x, dy: y, shown)
      context sheet-box(fn, x, y, measure(shown), dw: w / 1mm, n: none)
    }
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
    extra = "<rect x=\"" + plan-number(found.x) + "\" y=\"" + plan-number(found.y) + "\" width=\"" + plan-number(found.w) + "\" height=\"" + plan-number(found.h) + "\" fill=\"" + sheet-red + "\" fill-opacity=\"0.18\" stroke=\"" + sheet-red + "\" stroke-width=\"" + plan-number(1.4 * w) + "\" stroke-dasharray=\"" + plan-number(7 * w) + " " + plan-number(4 * w) + "\"/>"
  }
  let size = sheet-size(fn, plan, p, scale, width)
  if size.n != none { sheet-scales.update(a => if size.n in a { a } else { a + (size.n,) }) }
  let parts = (heading(size.n), plan-figure(p, size.s, extra: extra)).filter(c => c != none)
  let shown = stack(spacing: 3mm, ..parts)
  place(top + left, dx: x, dy: y, shown)
  context sheet-box(fn, x, y, measure(shown), dw: p.crop.w * size.s / 1mm, n: size.n)
}

// The legend placed at `x` and `y`: its title over a framed block of `lines` (each {key, text, swatch}, a fire plan's also `term` or `engine`), and the box the editor reads. In a context, as the title is the engine's word.
#let sheet-legend-block(fn, x, y, w, title, lines) = {
  let head = if title == none { none } else if title == auto { text(size: 14pt, weight: "bold", t-str("sheet.legend") + colon-str()) } else { text(size: 14pt, weight: "bold", sheet-words(title)) }
  let body = if lines.len() == 0 { none } else { block(width: w, stroke: 0.5pt + black, inset: 2mm, plan-legend((legend: lines), w - 4mm)) }
  let parts = (head, body).filter(c => c != none)
  let shown = stack(spacing: 2.5mm, ..parts)
  if parts.len() > 0 { place(top + left, dx: x, dy: y, shown) }
  sheet-box(fn, x, y, if parts.len() > 0 { measure(shown) } else { (width: 0mm, height: 0mm) })
}

/// **The legend of the sheet**: every STE symbol its plans use, beside what it stands for, under a title -- the legend of STE Compact 02's plan de positions, set once for every plan on the sheet.
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-legend(plans: "Pavillon", x: 12mm, y: 14mm, width: 100mm)
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-viewport(plan: "Geratehaus", x: 12mm, y: 14mm, width: 60mm)
/// #sheet-legend(x: 80mm, y: 14mm, width: 50mm, title: [Légende])
/// ```
///
/// A symbol two plans use is listed once, in the order the plans list them. Its words follow the report's language, the STE legend being the engine's.
///
/// - plans (auto, str, array): the plans whose symbols are listed; auto is every plan the sheet's viewports show.
/// - x (length, int, float): the legend's left edge, from the sheet's left edge.
/// - y (length, int, float): its top edge, from the sheet's top edge.
/// - width (length, int, float): the width its columns share -- a length or millimetres.
/// - title (auto, none, content, str): auto is «Légende» in the report's language; none prints no title.
/// -> content
#let sheet-legend(plans: auto, x: 0mm, y: 0mm, width: 120mm, title: auto) = {
  let fn = "sheet-legend"
  let x = sheet-mm(fn, "x:", x)
  let y = sheet-mm(fn, "y:", y)
  let w = sheet-mm(fn, "width:", width)
  sheet-text-arg(fn, "title:", title)
  if plans != auto and type(plans) != str and type(plans) != array {
    sheet-refuse(fn, "plans: is auto, a plan's id or an array of them -- got " + repr(plans))
  }
  context {
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
    sheet-legend-block(fn, x, y, w, title, lines)
  }
}

// --- Fire-protection plans (v0.115) ----------------------------------------------------------

/// **A fire-protection plan on the sheet**, at a scale: the plan drawn in Woodcore's «Plan de protection incendie» tab -- the architect's page faded under the surfaces of the escape routes, the walls with their fire resistance, the doors, the escape routes' lengths, exits and widths -- cut to the frame it was cropped to and placed with its top-left corner at `x` and `y`. At `scale: 100` it is printed at 1:100 exactly, from the plan's calibration -- or the one of the position plan it follows --; a plan that has none is given its `width` instead.
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-fire-viewport(plan: "Pavillon-EG", x: 14mm, y: 14mm, width: 75mm)
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-fire-viewport(plan: "Treppenhaus", x: 12mm, y: 20mm, scale: 100, legend: false, caption: auto)
/// ```
///
/// The legend is both possible on a sheet: drawn on the plan, where Woodcore placed it (`legend: true`), and as an object of its own that moves freely (`sheet-fire-legend`), which lists the symbols of every fire plan the sheet shows. The scale it is drawn at is what the title block's «Éch.» names. Above it stands its title, «Nom — description (éch. 1:100)»; `title: none` leaves it out.
///
/// - plan (none, str): the plan, by its id in Woodcore's «Plan de protection incendie» tab; none draws a frame in its place.
/// - x (length, int, float): the plan's left edge, from the sheet's left edge.
/// - y (length, int, float): the plan's top edge, from the sheet's top edge.
/// - scale (none, int, float): the n of 1:n -- 100 prints the plan at 1:100, which needs the plan calibrated in Woodcore.
/// - width (none, length, int, float): the width the plan is printed at, where it is given no scale -- a length or millimetres.
/// - legend (bool): the legend Woodcore placed on the plan; false leaves it out, for a sheet whose legend is `sheet-fire-legend`.
/// - scale-bar (bool): a scale bar under the plan, where it is calibrated.
/// - caption (none, auto, content, str): a line under the plan: auto names it with its scale; none prints none.
/// - title (auto, none, bool, content, str): the line above the plan: auto is «Nom — description, étage (éch. 1:n)» from the plan; none or false prints none; content or a string the engineer's own words.
/// -> content
#let sheet-fire-viewport(plan: none, x: 0mm, y: 0mm, scale: none, width: none, legend: true, scale-bar: false, caption: none, title: auto) = {
  let fn = "sheet-fire-viewport"
  let x = sheet-mm(fn, "x:", x)
  let y = sheet-mm(fn, "y:", y)
  if type(legend) != bool { sheet-refuse(fn, "legend: is true or false -- got " + repr(legend)) }
  if type(scale-bar) != bool { sheet-refuse(fn, "scale-bar: is true or false -- got " + repr(scale-bar)) }
  sheet-text-arg(fn, "caption:", caption)
  sheet-title-arg(fn, title)
  if plan == none {
    let w = if width == none { 80mm } else { sheet-mm(fn, "width:", width) }
    return {
      place(top + left, dx: x, dy: y, context doc-frame(w, t-str("document.fire_plan")))
      context sheet-box(fn, x, y, measure(doc-frame(w, t-str("document.fire_plan"))), dw: w / 1mm, n: none)
    }
  }
  let p = sheet-fire-plan(fn, plan)
  let size = sheet-size(fn, plan, p, scale, width, tab: "fire-protection plan")
  // the figure of the report's language: its legend carries words, so it is read in a context
  let drawing = context plan-figure(p, size.s, legend: legend)
  let head = context sheet-plan-title(fn, plan, p, size.n, title)
  let parts = if title == none or title == false { (drawing,) } else { (head, drawing) }
  if scale-bar and "scale" in p {
    parts.push(align(left, plan-scale-bar(p.scale.units_per_m * size.s, p.crop.w * size.s)))
  }
  if caption != none {
    let line = if caption == auto {
      [#p.label#if size.n != none [ (#sheet-ratio(size.n))]]
    } else { sheet-words(caption) }
    parts.push(text(size: 9pt, line))
  }
  sheet-fire-plans.update(a => if plan in a { a } else { a + (plan,) })
  if size.n != none { sheet-scales.update(a => if size.n in a { a } else { a + (size.n,) }) }
  let shown = stack(spacing: 2mm, ..parts)
  place(top + left, dx: x, dy: y, shown)
  context sheet-box(fn, x, y, measure(shown), dw: p.crop.w * size.s / 1mm, n: size.n)
}

/// **The legend of the fire-protection plans of the sheet**: every symbol of the VKF sheet of symbols the plans use -- the fire resistance of the walls, the doors, the surfaces of the escape routes, the exits, the lengths and the widths -- beside what it stands for, under a title, as a block of its own that is placed and moved freely.
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-fire-legend(plans: "Treppenhaus", x: 12mm, y: 14mm, width: 100mm)
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A6", landscape: true)
/// #sheet-fire-viewport(plan: "Pavillon-EG", x: 12mm, y: 14mm, width: 60mm, legend: false)
/// #sheet-fire-legend(x: 80mm, y: 14mm, width: 50mm, title: [Légende])
/// ```
///
/// A symbol two plans use is listed once, in the order the plans list them. Its words follow the report's language. A sheet may also show the legend on the plan itself (`sheet-fire-viewport`'s `legend:`), or both.
///
/// - plans (auto, str, array): the fire plans whose symbols are listed; auto is every fire plan the sheet's viewports show.
/// - x (length, int, float): the legend's left edge, from the sheet's left edge.
/// - y (length, int, float): its top edge, from the sheet's top edge.
/// - width (length, int, float): the width its columns share -- a length or millimetres.
/// - title (auto, none, content, str): auto is «Légende» in the report's language; none prints no title.
/// -> content
#let sheet-fire-legend(plans: auto, x: 0mm, y: 0mm, width: 120mm, title: auto) = {
  let fn = "sheet-fire-legend"
  let x = sheet-mm(fn, "x:", x)
  let y = sheet-mm(fn, "y:", y)
  let w = sheet-mm(fn, "width:", width)
  sheet-text-arg(fn, "title:", title)
  if plans != auto and type(plans) != str and type(plans) != array {
    sheet-refuse(fn, "plans: is auto, a fire-protection plan's id or an array of them -- got " + repr(plans))
  }
  context {
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
    sheet-legend-block(fn, x, y, w, title, lines)
  }
}

// --- The list of the positions (v0.116) ------------------------------------------------------

/// **The list of the positions on the sheet**: the positions the sheet's plans show -- or every position of the project, or those of one storey -- in a table under a title, ID, type, material, strength class, section type, dimension, units, moisture class and description, the ID set in its STE box in the colour the plan draws its letter with: the «liste des positions» of STE Compact 02, with this project's own columns. Placed and moved like the legend.
///
/// ```typ
/// #show: sheet.with(format: "A5", landscape: true)
/// #sheet-position-list(plans: "Pavillon", x: 10mm, y: 12mm, width: 190mm)
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A5", landscape: true)
/// #sheet-position-list(scope: "all", x: 10mm, y: 12mm, width: 190mm, title: [Positionsliste])
/// ```
///
/// The table is the report's own (`show-position-list` prints the same in a document), set at the sheet's size. The type follows the report's language where the glossary carries it; the description is the engineer's and is printed as written. ⚠️ A sheet does not break onto a second page: a list longer than the sheet runs past its edge.
///
/// - plans (auto, str, array): the position plans whose positions are listed, for `scope: "plans"`; auto is every plan the sheet's viewports show.
/// - scope (str): "plans" the positions of `plans`, "all" every position of the project, "storey" those of `storey`.
/// - storey (none, str): the storey's numbering character -- "0" for T001 -- for `scope: "storey"`.
/// - x (length, int, float): the list's left edge, from the sheet's left edge.
/// - y (length, int, float): its top edge, from the sheet's top edge.
/// - width (length, int, float): the width of the table -- a length or millimetres.
/// - title (auto, none, content, str): auto is «Liste des positions» in the report's language; none prints no title.
/// -> content
#let sheet-position-list(plans: auto, scope: "plans", storey: none, x: 0mm, y: 0mm, width: 180mm, title: auto) = {
  let fn = "sheet-position-list"
  let x = sheet-mm(fn, "x:", x)
  let y = sheet-mm(fn, "y:", y)
  let w = sheet-mm(fn, "width:", width)
  sheet-text-arg(fn, "title:", title)
  if plans != auto and type(plans) != str and type(plans) != array {
    sheet-refuse(fn, "plans: is auto, a position plan's id or an array of them -- got " + repr(plans))
  }
  context {
    let named = if plans == auto { sheet-plans.final() } else if type(plans) == str { (plans,) } else { plans }
    let ids = position-list-ids(scope: scope, plans: named, storey: storey, fn: fn)
    let head = if title == none { none } else if title == auto { text(size: 14pt, weight: "bold", t-str("position_list.title")) } else { text(size: 14pt, weight: "bold", sheet-words(title)) }
    // set a size smaller than the sheet's own, nine columns sharing the width a plan leaves
    let body = if ids.len() == 0 { text(style: "italic", t-str("position_list.empty")) } else { block(width: w, { set text(size: 8pt); position-list-table(ids) }) }
    let shown = stack(spacing: 2.5mm, ..(head, body).filter(c => c != none))
    place(top + left, dx: x, dy: y, shown)
    sheet-box(fn, x, y, measure(shown))
  }
}

// --- The quantities (issue #9) -----------------------------------------------------------------

/// **The quantities on the sheet**: what the sheet's plans draw -- or what every plan draws, or chosen positions -- by material then section, pieces, length in metres and volume in cubic metres, with a total per material, under a title: the «métrés» Woodcore measures from the plans' scale. Placed and moved like the list of the positions.
///
/// ```typ
/// #show: sheet.with(format: "A5", landscape: true)
/// #sheet-quantities(plans: "Pavillon", x: 10mm, y: 12mm, width: 150mm)
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A5", landscape: true)
/// #sheet-quantities(scope: "all", x: 10mm, y: 12mm, width: 150mm, title: [Métrés])
/// ```
///
/// The table is the report's own (`show-plan-quantities` prints the same in a document), set at the sheet's size. ⚠️ A sheet does not break onto a second page: a table longer than the sheet runs past its edge.
///
/// - plans (auto, str, array): the position plans whose quantities are added up, for `scope: "plans"`; auto is every plan the sheet's viewports show.
/// - scope (str): "plans" what `plans` draw, "all" what every plan draws, "positions" the positions `positions`.
/// - positions (str, array): the positions, by their ids, for `scope: "positions"`.
/// - x (length, int, float): the table's left edge, from the sheet's left edge.
/// - y (length, int, float): its top edge, from the sheet's top edge.
/// - width (length, int, float): the width of the table -- a length or millimetres.
/// - title (auto, none, content, str): auto is «Métrés» in the report's language; none prints no title.
/// -> content
#let sheet-quantities(plans: auto, scope: "plans", positions: (), x: 0mm, y: 0mm, width: 150mm, title: auto) = {
  let fn = "sheet-quantities"
  let x = sheet-mm(fn, "x:", x)
  let y = sheet-mm(fn, "y:", y)
  let w = sheet-mm(fn, "width:", width)
  sheet-text-arg(fn, "title:", title)
  if plans != auto and type(plans) != str and type(plans) != array {
    sheet-refuse(fn, "plans: is auto, a position plan's id or an array of them -- got " + repr(plans))
  }
  context {
    let named = if plans == auto { sheet-plans.final() } else if type(plans) == str { (plans,) } else { plans }
    let summary = if scope == "plans" and named.len() == 0 { (groups: (), totals: ()) } else { quantity-summary(scope, named, positions, fn) }
    let head = if title == none { none } else if title == auto { text(size: 14pt, weight: "bold", t-str("quantities.title")) } else { text(size: 14pt, weight: "bold", sheet-words(title)) }
    let body = if summary.groups.len() == 0 { text(style: "italic", t-str("quantities.empty")) } else { block(width: w, { set text(size: 8pt); quantity-table(summary) }) }
    let shown = stack(spacing: 2.5mm, ..(head, body).filter(c => c != none))
    place(top + left, dx: x, dy: y, shown)
    sheet-box(fn, x, y, measure(shown))
  }
}

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

/// **The title block of the sheet** (Plankopf, cartouche), in the Berner Fachhochschule's dress and laid out as STE Compact 02's: the logo, the object and the building element; the client and the architect; the SIA phase, the project's number and the plan's; the revision -- its index, date, author and what it changed --; who drew the sheet, its scale, its date and its size. Placed at the sheet's bottom-right corner, inside its frame, unless `x` and `y` say otherwise.
///
/// ```typ
/// #show: sheet.with(format: "A4", landscape: true)
/// #sheet-titleblock(element: [Plan de positions \ Parois du rez], plan-number: "B01", phase: [51 Projet d'exécution])
/// ```
///
/// ```typ
/// #show: sheet.with(format: "A4", landscape: true)
/// #sheet-titleblock(architect: [Muster Architekten AG], scale: "1:50", date: "2026-10-06", logo: none)
/// ```
///
/// Every value left at auto comes from the project: the object is its name, the client its client, the project number its number, who drew the sheet its author (Woodcore: Fichier → Propriétés du projet), the revision the newest entry of the journal, the date today, the scale every scale the sheet's plans and sections are drawn at -- «1:100 / 1:200» -- and the size the sheet's format in millimetres. A value given replaces it, and none leaves the cell empty. The labels are the engine's, in the report's language.
///
/// - x (auto, length, int, float): the block's left edge, from the sheet's left edge; auto sets it against the frame's right side.
/// - y (auto, length, int, float): its top edge; auto sets it against the frame's bottom side.
/// - width (auto, length, int, float): its width; auto is 200 mm, or the frame's width where that is narrower.
/// - logo (auto, none, content): auto is the BFH's logo; none leaves the cell empty; content stands in its place.
/// - object (auto, none, content, str): the building, the project's name at auto.
/// - element (none, content, str): what the sheet shows, «Plan de positions».
/// - client (auto, none, content, str): the client, the project's at auto.
/// - architect (none, content, str): the architect.
/// - phase (none, content, str): the SIA phase, «51 Projet d'exécution».
/// - project-number (auto, none, content, str): the project's number, the project's at auto.
/// - plan-number (none, content, str): the sheet's number.
/// - index (auto, none, content, str, int): the revision's index, the journal's newest at auto.
/// - revision-date (auto, none, content, str, datetime): that revision's date.
/// - revision-author (auto, none, content, str): who made it -- the short form the journal gives it.
/// - modification (auto, none, content, str): what it changed -- its label in the journal.
/// - drawn-by (auto, none, content, str): who drew the sheet, the project's author at auto.
/// - date (auto, none, content, str, datetime): the sheet's date, today at auto.
/// - scale (auto, none, content, str): the scales, every scale the sheet's plans are drawn at at auto.
/// - size (auto, none, content, str): the sheet's size, its format in millimetres at auto.
/// -> content
#let sheet-titleblock(x: auto, y: auto, width: auto, logo: auto, object: auto, element: none, client: auto, architect: none, phase: none, project-number: auto, plan-number: none, index: auto, revision-date: auto, revision-author: auto, modification: auto, drawn-by: auto, date: auto, scale: auto, size: auto) = {
  let fn = "sheet-titleblock"
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
    let px = if x != auto { sheet-mm(fn, "x:", x) } else if on == none { 0mm } else { on.width * 1mm - m - w }
    let py = if y != auto { sheet-mm(fn, "y:", y) } else if on == none { 0mm } else { on.height * 1mm - m - height }
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
    sheet-box(fn, px, py, (width: w, height: height))
    place(top + left, dx: px, dy: py, block(width: w, fill: white, grid(
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
    )))
  }
}
