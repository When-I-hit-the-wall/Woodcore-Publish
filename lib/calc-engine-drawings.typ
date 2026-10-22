// lib/calc-engine-drawings.typ -- the position plans, the fire-protection plans, the static models, the detail schemas and the annexes.
// Split out of lib/calc-engine.typ by subject, its text moved and not rewritten (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, G9). Each part imports the one before it, so a name reads everything defined above it as it did in one file; lib/calc-engine.typ imports the last and is what every caller names.

#import "calc-engine-core.typ": *

// --- Position plans (docs/domain/position-plans.md §3.3sexies) ---------------------------
// The plans drawn in Woodcore's «Plan de positions» tab, in their own file: data/plans.json. A plan is a background -- the page of the architect's PDF it was drawn on, or an image, copied under data/plans/ -- and an SVG of the STE symbols over the same frame, in the background's own units (its sheet); show-plan sets the one exactly over the other. A position appears on a plan by its number and nothing else: the plan says where it is, Positionen.xlsx what it is.

/// The plans a position is drawn on, in file-name order -- what `calc-block(..., plan: auto)` shows. Data access, not a display function.
///
/// ```typ
/// #plans-of("T001")
/// ```
///
/// ```typ
/// #for p in plans-of("S001") {
///   figure(image-positions-plan(p, highlight: "S001", frame: "highlight", width: 40%), kind: image, caption: [#p])
/// }
/// ```
///
/// - position (str): a position id, e.g. "T001".
/// -> array
#let plans-of(position) = load-plans().plans.pairs().filter(((_, p)) => position in p.labels).map(((id, _)) => id)

// The halo show-plan draws under the positions it highlights, as SVG elements for the plan's `<!-- highlight -->` marker: along a line, over an area, round a point -- sized by the plan's symbol unit and sliders, so it is as broad on every plan.
#let plan-halo(p, labels) = {
  let colour = figure-colour("yellow")
  let w-line = p.unit * p.style.at("line", default: 1)
  let w-point = p.unit * p.style.at("point", default: 1)
  let points(e) = e.points.map(q => svg-number(q.at(0)) + "," + svg-number(q.at(1))).join(" ")
  let out = ""
  for e in p.elements.filter(e => e.label in labels) {
    if e.kind == "point" {
      let q = e.points.first()
      out += "<circle cx=\"" + svg-number(q.at(0)) + "\" cy=\"" + svg-number(q.at(1)) + "\" r=\"" + svg-number(16 * w-point) + "\" fill=\"" + colour + "\" fill-opacity=\"0.6\"/>"
    } else if e.kind == "line" {
      out += "<polyline points=\"" + points(e) + "\" fill=\"none\" stroke=\"" + colour + "\" stroke-opacity=\"0.6\" stroke-width=\"" + svg-number(18 * w-line) + "\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>"
    } else {
      out += "<polygon points=\"" + points(e) + "\" fill=\"" + colour + "\" fill-opacity=\"0.3\" stroke=\"" + colour + "\" stroke-opacity=\"0.7\" stroke-width=\"" + svg-number(8 * w-line) + "\" stroke-linejoin=\"round\"/>"
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
    let ink = rgb(figure-colour("axis"))
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
#let plan-legend(p, width, centres: true) = {
  let lines = p.legend
  if type(lines) == str { return image(figure-path(lines), width: width) }
  // The stiffness centre, the mass centre and the outline (issue #54) have a line each where the plan prints them, which the export marks (`centres`): a call that leaves the three out of the drawing leaves their lines out of its legend -- by the mark, so that no list of keys is written here a second time.
  let lines = if centres { lines } else { lines.filter(l => not l.at("centres", default: false)) }
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
  set text(size: size, fill: rgb(figure-colour("axis")))
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

// The drawing of plan `p` -- the architect's page faded under it, the STE symbols over it -- cut to `window` (in the plan's sheet units; the plan's own crop by default) and printed at `s`, a length per sheet unit. What show-plan sets in a report, at a scale it works out from the column, and sheet-viewport and sheet-section on an export sheet, at the scale the sheet states (lib/sheet.typ, v0.114) -- one drawing, so the two cannot come to draw a plan two ways. `marked` puts a halo under those positions and `extra` is SVG of the caller's put in at the same `<!-- highlight -->` marker (a section's storey); the marker is left alone where there is neither, so a plan with nothing highlighted is the very SVG the export wrote. `axes: false` strips the axes, `legend: false` the legend a fire-protection plan carries on itself (a position plan has none on its overlay: its legend is `plan-legend`'s), `dimensions: false` the plan's dimensions and `lengths: false` the lengths written beside its elements (issue #9), `centres: false` the stiffness centre, the mass centre and the building's outline (issue #54) -- each between markers the drawing writes only where it has some.
//
// Both images are given their width and their height: given one only, an image covers the area its container leaves it (fit: "cover"), and a detail's box, shorter than the plan, would crop them about their middle.
#let plan-figure(p, s, window: auto, marked: (), axes: true, extra: "", legend: true, dimensions: true, lengths: true, centres: true) = {
  let crop = p.crop
  let window = if window == auto { crop } else { window }
  // A fire-protection plan (v0.115) is drawn once per language -- its legend carries words --, and so is a section carrying a load transfer level (v0.116, «Niveau de reprise des charges (x0xx)»): the figure of the report's language is the one set. Every other position plan has the one overlay. Reading the language needs a context, which a drawing with `figures` is set in here -- so that a sheet's viewport or section, which stands in none, sets one too.
  let draw(file) = {
    let overlay = read(figure-path(file))
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
    if not centres {
      // two pairs of markers, the outline under the symbols and the two centres over the numbers: every one is taken out
      overlay = overlay.replace(regex("(?s)<!-- centres -->.*?<!-- /centres -->"), "")
    }
    if marked.len() > 0 or extra != "" {
      overlay = overlay.replace("<!-- highlight -->", plan-halo(p, marked) + extra)
    }
    box(width: window.w * s, height: window.h * s, clip: true, {
      if "background" in p {
        place(top + left, dx: -window.x * s, dy: -window.y * s,
          image(figure-path(p.background.file), width: p.sheet.width * s, height: p.sheet.height * s, fit: "stretch"))
      }
      place(top + left, dx: -(window.x - crop.x) * s, dy: -(window.y - crop.y) * s,
        image(bytes(overlay), format: "svg", width: crop.w * s, height: crop.h * s, fit: "stretch"))
    })
  }
  if "figures" in p { context draw(p.figures.at(report-lang())) } else { draw(p.overlay) }
}

// A position plan as a figure, its legend, its scale bar and its caption by their arguments: what image-positions-plan draws (spec 2026-10-21-commandes-typst-refonte, REQ-013) -- #show-plan until then.
#let plan-drawing(plan, width: 100%, legend: auto, highlight: none, detail: false, zoom: 1, axes: true, dimensions: true, lengths: auto, centres: auto, scale-bar: auto, caption: auto, level: auto) = context {
  // the level: what is left `auto` is printed from level 2, what the call wrote as it wrote it (spec 2026-10-20-indices-et-niveaux, UI-003, D-07)
  let lv = print-level("image-positions-plan", level)
  let (legend, lengths, centres, scale-bar) = (legend, lengths, centres, scale-bar).map(arg => at-level(arg, lv, 2))
  let caption = if caption == auto and lv < 2 { none } else { caption }
  let plans = load-plans().plans
  assert(type(plan) == str and plan in plans,
    message: "image-positions-plan: no plan " + repr(plan) + " -- " + (if plans.len() == 0 { "none saved yet (draw one in Woodcore's position plan tab)" } else { "valid plans: " + plans.keys().join(", ") }))
  let p = plans.at(plan)
  let marked = if highlight == none { () } else if type(highlight) == str { (highlight,) } else { highlight }
  for label in marked {
    assert(type(label) == str and label in p.labels,
      message: "image-positions-plan: plan '" + plan + "' does not show " + repr(label) + " -- it shows " + (if p.labels.len() == 0 { "no position" } else { p.labels.join(", ") }))
  }
  assert(not detail or marked.len() > 0,
    message: "image-positions-plan: detail: true frames the highlighted positions -- give highlight: \"T001\" as well")
  assert((type(zoom) == int or type(zoom) == float) and zoom > 0,
    message: "image-positions-plan: zoom must be a number greater than 0, got " + repr(zoom))
  assert(type(dimensions) == bool and type(lengths) == bool and type(centres) == bool,
    message: "image-positions-plan: dimensions:, lengths: and centres: are true or false, got " + repr((dimensions, lengths, centres)))

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
    let body = plan-figure(p, s, window: window, marked: marked, axes: axes, dimensions: dimensions, lengths: lengths, centres: centres)
    // under the plan: its scale bar, where it has a scale, set against the plan's left edge; then its legend, as wide as the plan but not narrower than a legend reads well at
    let framed = if scale-bar and "scale" in p {
      stack(spacing: 0.7em, body, block(width: window.w * s, align(left, plan-scale-bar(p.scale.units_per_m * s, window.w * s))))
    } else { body }
    let key = if legend and not detail { plan-legend(p, calc.min(size.width, calc.max(window.w * s, 11cm)), centres: centres) } else { none }
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

// --- Fire-protection plans (calc/domains/fire.py, v0.115) ---------------------------------------------
// The plans drawn in Woodcore's «Plan de protection incendie» tab, in their own file: data/fire.json. A plan is a figure -- the surfaces of the escape routes, the walls with their fire resistance, the doors, the escape routes' lengths, exits and widths, and its legend, drawn by calc/domains/fire_svg.py once per language of the report, the legend carrying words -- set exactly over a background: the architect's plan it was drawn on, which is the position plan's own exported page where the plan follows a position plan. A drawing and not a calculation: what it measures -- an area, a length, a width -- is the drawing's own. It is set by `plan-figure`, as a position plan is, so a report, a sheet and a detail cannot come to draw one two ways.

// A fire-protection plan as a figure: what image-fire-plan draws (REQ-014) -- #show-fire-plan until then.
#let fire-plan-drawing(plan, width: 100%, legend: auto, scale-bar: auto, caption: auto, level: auto) = context {
  let lv = print-level("image-fire-plan", level)
  let (legend, scale-bar) = (legend, scale-bar).map(arg => at-level(arg, lv, 2))
  let caption = if caption == auto and lv < 2 { none } else { caption }
  let plans = load-fire-plans().plans
  assert(type(plan) == str and plan in plans,
    message: "image-fire-plan: no plan " + repr(plan) + " -- " + (if plans.len() == 0 { "none saved yet (draw one in Woodcore's fire-protection plan tab)" } else { "valid plans: " + plans.keys().join(", ") }))
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

// The halo show-static-model draws under the parts it highlights, as SVG elements for the figure's `<!-- highlight -->` marker: along a member, round a node, round a load's arrows -- sized by the model's own symbol unit and sliders, so it is as broad on every figure. Drawn in Typst and not in Python for the reason a plan's is: which part is highlighted is the call's to say, not the drawing's.
#let static-halo(m, ids) = {
  let colour = figure-colour("yellow")
  let u = m.unit * m.style.at("point", default: 1)
  let pt(p) = svg-number(p.at(0), digits: 3) + "," + svg-number(p.at(1), digits: 3)
  let stroke-line(a, b, w) = (
    "<line x1=\"" + svg-number(a.at(0), digits: 3) + "\" y1=\"" + svg-number(a.at(1), digits: 3) + "\" x2=\""
      + svg-number(b.at(0), digits: 3) + "\" y2=\"" + svg-number(b.at(1), digits: 3) + "\" stroke=\"" + colour
      + "\" stroke-width=\"" + svg-number(w, digits: 3) + "\" stroke-linecap=\"round\"/>"
  )
  let disc(p, r) = (
    "<circle cx=\"" + svg-number(p.at(0), digits: 3) + "\" cy=\"" + svg-number(p.at(1), digits: 3) + "\" r=\""
      + svg-number(r, digits: 3) + "\" fill=\"" + colour + "\"/>"
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

// A static model as a figure: what image-static-model draws (REQ-014) -- #show-static-model until then.
#let static-model-drawing(model, width: 100%, loads: true, dimensions: true, highlight: none, caption: auto, level: auto) = context {
  // the level (spec 2026-10-20-indices-et-niveaux, UI-003): the caption from 2
  let caption = if caption == auto and print-level("image-static-model", level) < 2 { none } else { caption }
  let models = load-statics().models
  assert(type(model) == str and model in models,
    message: "image-static-model: no static model " + repr(model) + " -- " + (if models.len() == 0 { "none saved yet (draw one in Woodcore's static models tab)" } else { "valid models: " + models.keys().join(", ") }))
  let m = models.at(model)
  let marked = if highlight == none { () } else if type(highlight) == str { (highlight,) } else { highlight }
  for id in marked {
    assert(type(id) == str and id in m.labels,
      message: "image-static-model: model '" + model + "' has no " + repr(id) + " -- it carries " + (if m.labels.len() == 0 { "nothing" } else { m.labels.join(", ") }))
  }
  // The figure of the report's language: the notes are drawn inside it and its frame is sized to hold them, so the frame travels with the file rather than standing beside all three (docs/typst/language.md §4bis).
  let fig = m.figures.at(report-lang())
  let figure-svg = read(figure-path(fig.file))
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


// The halo schema-drawing() draws under the parts it highlights, as SVG elements for the figure's `<!-- highlight -->` marker -- static-halo's own shape, one collection at a time: an element's whole polyline, a line-shaped aid's or a dimension's line, an angle dimension's own centre.
//
// ⚠️ A **point** is ringed, and its ring goes *over* the pieces (v0.87, the engineer: «la mise en évidence d'un point dans show-schema est invisible, cachée sous les pièces. Un point doit être affiché au-dessus de tout»). Its disc sat at `<!-- highlight -->`, before the pieces, and a piece is filled at three quarters opacity: a halo under a pin inside a beam and a post -- every pin of a joint -- did not show at all. schema_svg.body writes a second marker, `<!-- highlight-points -->`, after the pieces, the lines and the dimensions and before the markers and the named points, so the point's own symbol still stands on its halo. A ring rather than a disc: drawn above a piece, a disc covered the piece around the point, and a ring says «this one» and leaves the detail readable. It is sized from the point it rings and the record's `size`, where the disc was a fixed 6 or 10 mm whatever the detail's scale. `points:` picks what is drawn: auto everything, true the points alone, false the rest.
#let schema-halo(m, ids, points: auto) = {
  let colour = figure-colour("yellow")
  let stroke-line(a, b, w) = (
    "<line x1=\"" + svg-number(a.at(0)) + "\" y1=\"" + svg-number(a.at(1)) + "\" x2=\""
      + svg-number(b.at(0)) + "\" y2=\"" + svg-number(b.at(1)) + "\" stroke=\"" + colour
      + "\" stroke-width=\"" + svg-number(w) + "\" stroke-linecap=\"round\"/>"
  )
  let disc(p, r) = (
    "<circle cx=\"" + svg-number(p.at(0)) + "\" cy=\"" + svg-number(p.at(1)) + "\" r=\""
      + svg-number(r) + "\" fill=\"" + colour + "\"/>"
  )
  let ring(p, r, w) = (
    "<circle cx=\"" + svg-number(p.at(0)) + "\" cy=\"" + svg-number(p.at(1)) + "\" r=\""
      + svg-number(r) + "\" fill=\"none\" stroke=\"" + colour + "\" stroke-width=\"" + svg-number(w) + "\"/>"
  )
  // schema_svg.layout's own sizes: a point's cross reaches 0.45 font either way, a marker's radius is size/130 or its own diameter's half
  // the extent schema_svg.layout sized the symbols by, which the export carries since 1.4 (D7): an older export is written again by Woodcore, never worked out here
  assert("size" in m, message: "image-schema: data/schemas.json was written before v0.120 and carries no size for '" + m.source + "' -- export the project again in Woodcore")
  let size = m.size
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

// A detail schema: what image-schema draws (REQ-014) -- #schema until then.
#let schema-drawing(schema, width: 100%, highlight: none, aids: auto, level: auto) = context {
  // the level (spec 2026-10-20-indices-et-niveaux, UI-003): the construction aids from 2, where the call leaves them auto
  let aids = at-level(aids, print-level("schema", level), 2)
  let schemas = load-schemas().schemas
  assert(type(schema) == str and schema in schemas,
    message: "image-schema: no schema " + repr(schema) + " -- " + (if schemas.len() == 0 { "none saved yet (draw one in Woodcore's Schémas tab)" } else { "valid schemas: " + schemas.keys().join(", ") }))
  let m = schemas.at(schema)
  let marked = if highlight == none { () } else if type(highlight) == str { (highlight,) } else { highlight }
  for part in marked {
    assert(type(part) == str and part in m.labels,
      message: "image-schema: schema '" + schema + "' has no " + repr(part) + " -- it carries " + (if m.labels.len() == 0 { "nothing" } else { m.labels.join(", ") }))
  }
  // The figure of the report's language: a connector marker's kind, and any legend the drawing carries, may be a word (docs/typst/language.md §4bis), so the frame travels with the file rather than standing beside all three.
  let fig = m.figures.at(report-lang())
  let figure-svg = read(figure-path(fig.file))
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
    image(bytes(figure-svg), format: "svg", width: fig.view.w * s, height: fig.view.h * s, fit: "stretch")
  })
}

// --- Annexes (docs/domain/annexes.md §3.3undevicies, v0.115) -------------------------
// The documents a report draws on from outside -- a FEM program's print report first -- and the excerpts it shows of them: a diagram, a table, taken from one page of a source. Nothing here computes: an excerpt is a picture of another program's calculation. The export has already found each excerpt again in its source's current version, by the bookmark it is anchored on, and written it as a one-page PDF cropped to its frame (calc/domains/annex.py) -- Typst sets that page at the origin, since it draws a page made of clipped image tiles wrongly as soon as it is placed anywhere else.
//
// An excerpt and the annex page it comes from are linked both ways, by where each one lands rather than by a label: a label written twice is an error in Typst, and an excerpt may be shown twice. Each leaves a `metadata` behind it -- `<woodcore-extract>` carrying its id, `<woodcore-annex-page>` carrying its source and page -- and the other end asks `query` for it and links to its location, where there is one. An excerpt shown in a report that prints no annexes is therefore simply not a link.


// The frame an annex page draws around the region an excerpt shows, and the tag beside it: a colour of its own, which is neither the orange of a value written over nor the yellow of a highlight.
#let annex-frame-colour = rgb("#c2410c")

// An excerpt of an annex: what image-extract draws (REQ-014) -- #show-extract until then.
#let extract-drawing(excerpt, width: 100%, caption: auto, level: auto) = {
  if not (level in (auto, 1, 2, 3)) { panic("image-extract: invalid level " + repr(level) + " -- use auto, 1, 2 or 3") }
  let annexes = load-annexes()
  let excerpts = annexes.excerpts
  assert(type(excerpt) == str and excerpt in excerpts,
    message: "image-extract: no excerpt " + repr(excerpt) + " -- " + (if excerpts.len() == 0 { "none saved yet (frame one in Woodcore's Annexes tab)" } else { "valid excerpts: " + excerpts.keys().join(", ") }))
  let e = excerpts.at(excerpt)
  if not e.resolved {
    panic("image-extract: the excerpt " + repr(excerpt) + " cannot be printed -- " + e.reason)
  }
  let source = annexes.sources.at(e.source, default: (name: e.source))
  let name = if source.name != "" { source.name } else { e.source }
  [#metadata((id: excerpt, source: e.source, page: e.page))<woodcore-extract>]
  context {
    let body = image(figure-path(e.file), width: width)
    // the annex page this excerpt comes from, where the report prints one: the whole picture is the link
    let target = query(<woodcore-annex-page>).filter(m => m.value.source == e.source and m.value.page == e.page)
    let shown = if target.len() > 0 { link(target.first().location(), body) } else { body }
    let caption = if caption == auto and print-level("image-extract", level) < 2 { none } else { caption }
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
/// #figure(image-extract("CO1-My", width: 50%), kind: image, caption: [Auszug])
/// #show-annexes()
/// ```
///
/// ```typ-dry
/// #show-annexes(heading: none)
/// ```
/// - heading (int, none): the level each annex's name is set as a heading at, so it stands in the outline -- 2 by default, under the engineer's own «= Anhänge»; none sets it in bold on its cover page instead and keeps the outline the engineer's.
/// - level (auto, int): 1 the pages alone, without the cover naming each annex, its letter and its pages; 2 with it (what a document prints by default); 3 the same as 2, the cover citing each source already. auto follows the report.
/// -> content
#let show-annexes(heading: 2, level: auto) = {
  if not (level in (auto, 1, 2, 3)) { panic("show-annexes: invalid level " + repr(level) + " -- use auto, 1, 2 or 3") }
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
      // The first cover stands under the engineer's own «= Anhänge», which Sections/009 opens on a page of its own; every later one opens a page. Each page of a source is a page of its own anyway (`page` below). At level 1 the pages alone, without their cover (spec 2026-10-20-indices-et-niveaux, UI-003).
      if print-level("show-annexes", level) >= 2 {
        if letter > 1 { pagebreak(weak: true) }
        if heading == none {
          block(below: 1em, text(weight: "bold", size: 1.2em, title))
        } else {
          std.heading(level: heading, title)
        }
        if source.label != "" { par(source.label) }
        par(t-str("annex.pages", pages: pages.map(str).join(", ")))
      }
      for p in pages {
        let i = annex.pages.position(q => q == p)
        let (w, h) = annex.sizes.at(i)
        page(width: w * 1pt, height: h * 1pt, margin: 0pt, header: none, footer: none, {
          [#metadata((source: sid, page: p))<woodcore-annex-page>]
          place(top + left, image(figure-path(annex.file), page: i + 1, width: w * 1pt, height: h * 1pt))
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



// --- What a sheet knows of itself, and a plan drawn on one (moved from lib/sheet.typ, spec 2026-10-21-commandes-typst-refonte, Q-015) ---
// A plan placed on an export sheet is `image-positions-plan(id, scale: 100)` -- a raw `#place` of the sheet holds it --, so what a sheet knows of itself lives here, where the image commands are, and lib/sheet.typ imports it: the format the show rule set, the scales the plans are drawn at and the plans they show, read by the title block and the legend.

// --- What a sheet knows of itself ------------------------------------------------------------
//
// Three states, each read by the title block and the legend in their `context`: the format the show rule set, the scales the viewports and sections are drawn at, and the plans they show. `.final()` is what lets the title block stand anywhere in the file and still name every scale of the sheet.
#let sheet-state = state("woodcore-sheet", none)

#let sheet-scales = state("woodcore-sheet-scales", ())

#let sheet-plans = state("woodcore-sheet-plans", ())

// The fire-protection plans the viewports show (v0.115): a state of their own, a fire plan and a position plan being free to share an id.
#let sheet-fire-plans = state("woodcore-sheet-fire-plans", ())

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

// What the last drawing placed on a sheet was drawn at -- the width of its drawing `dw` and its scale `n` --, which the page's `show place` rule hands to the sheet editor with the box it reads (lib/sheet.typ, `sheet`), then forgets.
#let sheet-last = state("woodcore-sheet-last", (dw: none, n: none))

// The frame a plan not chosen yet stands in on a sheet: a grey rectangle, the word of what is to come in it.
#let sheet-placeholder(w, words) = rect(width: w, height: w * 0.6, stroke: 0.5pt + luma(60%), align(center + horizon, text(fill: luma(45%), words)))

// A position plan on a sheet (Q-015): its title, the drawing at its scale or width, the scale bar where asked -- `(shown, dw, n)`, in a context. What `sheet-viewport` placed, and what `image-positions-plan(…, scale:)` prints in the `#place` of a sheet.
#let sheet-viewport-content(fn, plan, scale, width, highlight, axes, dimensions, lengths, centres, scale-bar, title) = {
  sheet-title-arg(fn, title)
  if plan == none {
    let w = if width == none { 80mm } else { sheet-mm(fn, "width:", width) }
    return (shown: sheet-placeholder(w, t-str("document.plan")), dw: w / 1mm, n: none)
  }
  let p = sheet-plan(fn, plan)
  let marked = if highlight == none { () } else if type(highlight) == str { (highlight,) } else { highlight }
  for label in marked {
    if type(label) != str or not (label in p.labels) {
      sheet-refuse(fn, "the plan " + repr(plan) + " does not show " + repr(label) + " -- it shows " + (if p.labels.len() == 0 { "no position" } else { p.labels.join(", ") }))
    }
  }
  let size = sheet-size(fn, plan, p, scale, width)
  let drawing = plan-figure(p, size.s, marked: marked, axes: axes, dimensions: dimensions, lengths: lengths, centres: centres)
  let head = sheet-plan-title(fn, plan, p, size.n, title)
  let parts = if head == none { (drawing,) } else { (head, drawing) }
  if scale-bar and "scale" in p {
    parts.push(align(left, plan-scale-bar(p.scale.units_per_m * size.s, p.crop.w * size.s)))
  }
  // the plan and its scale made known to the legend and the title block, with what is shown (a state's update is content)
  let known = {
    sheet-plans.update(a => if plan in a { a } else { a + (plan,) })
    if size.n != none { sheet-scales.update(a => if size.n in a { a } else { a + (size.n,) }) }
  }
  (shown: known + stack(spacing: 2mm, ..parts), dw: p.crop.w * size.s / 1mm, n: size.n)
}

// A fire-protection plan on a sheet (Q-015): `sheet-viewport-content`'s, the plan's own legend drawn on it where asked.
#let sheet-fire-viewport-content(fn, plan, scale, width, legend, scale-bar, title) = {
  sheet-title-arg(fn, title)
  if plan == none {
    let w = if width == none { 80mm } else { sheet-mm(fn, "width:", width) }
    return (shown: sheet-placeholder(w, t-str("document.fire_plan")), dw: w / 1mm, n: none)
  }
  let p = sheet-fire-plan(fn, plan)
  let size = sheet-size(fn, plan, p, scale, width, tab: "fire-protection plan")
  let drawing = plan-figure(p, size.s, legend: legend)
  let head = sheet-plan-title(fn, plan, p, size.n, title)
  let parts = if head == none { (drawing,) } else { (head, drawing) }
  if scale-bar and "scale" in p {
    parts.push(align(left, plan-scale-bar(p.scale.units_per_m * size.s, p.crop.w * size.s)))
  }
  let known = {
    sheet-fire-plans.update(a => if plan in a { a } else { a + (plan,) })
    if size.n != none { sheet-scales.update(a => if size.n in a { a } else { a + (size.n,) }) }
  }
  (shown: known + stack(spacing: 2mm, ..parts), dw: p.crop.w * size.s / 1mm, n: size.n)
}

// --- The five figures as images, for a native #figure (spec 2026-10-21-commandes-typst-refonte, REQ-013, REQ-014, ARCH-012, D-13) ---
// Each draws what its `show-*` drew, without the figure around it: the caption and the label are the document's own, written on a native `#figure(…, kind: image, caption: […]) <label>`, which numbers it and lets `@label` cite it. What the drawing shows is `detail-figure`, what is set under it `detail-legend`: one vocabulary for the five, lib/image-vocabulary.json, which calc/build_reference_calls.py `call_image_figure` reads too.

#let image-vocabulary = json("image-vocabulary.json").commands

// The values of `detail-figure` or `detail-legend` a call gives, checked against the vocabulary: auto the command's defaults, a word or a list of words; "none" alone is none of them.
#let image-details(fn, arg, given) = {
  let entry = image-vocabulary.at(fn)
  let allowed = entry.at(arg)
  let given = if given == auto { entry.at(arg + "-default") } else if type(given) == str { (given,) } else if type(given) == array { given } else {
    panic(fn + ": " + arg + ": is a word or an array of words -- got " + repr(given))
  }
  for value in given {
    if not (value in allowed) {
      panic(fn + ": " + arg + ": has no " + repr(value) + " -- valid: " + (if allowed.len() == 0 { "none" } else { allowed.map(v => repr(v)).join(", ") }))
    }
  }
  given.filter(v => v != "none")
}

/// **A position plan as an image**: the architect's plan it was drawn on, faded, the structure's STE symbols and numbers over it -- `#show-plan`'s drawing without its figure.
///
/// ```typ
/// #figure(image-positions-plan("Velo-Unterstand"), kind: image, caption: [Positionsplan Velo-Unterstand]) <pl-velo>
///
/// Die Positionen zeigt @pl-velo.
/// ```
///
/// ```typ
/// #figure(image-positions-plan("Pavillon", highlight: ("S001", "S002"), frame: "highlight", detail-legend: "none"), kind: image, caption: [Stützen des Pavillons])
/// ```
///
/// It is an image to set in a native `#figure(…, kind: image, caption: […]) <label>`, which numbers it and lets `@label` cite it -- the caption and the label are the document's own.
///
/// - plan (str): the plan's id, as saved in Woodcore.
/// - highlight (str, array, none): the part(s) put under a halo, by id.
/// - width (relative, length): the width it is printed at, 100% of the room it is given by default.
/// - frame (str): `"all"` the whole plan, `"highlight"` only the surroundings of the highlighted positions, at the scale of the whole.
/// - zoom (int, float): enlarges a framed detail beyond the plan's scale.
/// - detail-figure (auto, str, array): what the drawing shows, a word or a list of words of the command's vocabulary (lib/image-vocabulary.json); auto its defaults.
/// - detail-legend (auto, str, array): what is set under the drawing, among the command's words -- `"none"` nothing; auto its defaults.
/// - scale (none, int, float): on an export sheet, the n of 1:n the plan is drawn at, where it is calibrated; none prints it at `width`.
/// - title (none, auto, str, content): on an export sheet, the line above the plan -- auto its name, description, storey and scale.
/// -> content
#let image-positions-plan(plan, highlight: none, width: 100%, frame: "all", zoom: 1, detail-figure: auto, detail-legend: auto, scale: none, title: none) = {
  let fn = "image-positions-plan"
  let shown = image-details(fn, "detail-figure", detail-figure)
  // on a sheet (a scale, or a title, given -- Q-015) nothing is set under the plan but its scale bar: its legend is an object of the sheet of its own
  let on-sheet = scale != none or title != none
  let under = if on-sheet and detail-legend == auto { () } else { image-details(fn, "detail-legend", detail-legend) }
  if not (frame in ("all", "highlight")) { panic(fn + ": frame: is \"all\" or \"highlight\" -- got " + repr(frame)) }
  if on-sheet {
    return context {
      // a width that is a ratio is the report's default, no size on a sheet: one given as a length with a scale is refused by `sheet-size` -- a drawing has one size
      let r = sheet-viewport-content(fn, plan, scale, if type(width) == ratio { none } else { width }, highlight,
        "axes" in shown, "dimensions" in shown, "length" in shown, "centres" in shown, "scale-bar" in under, title)
      sheet-last.update((dw: r.dw, n: r.n))
      r.shown
    }
  }
  plan-drawing(plan, width: width, highlight: highlight, detail: frame == "highlight", zoom: zoom,
    axes: "axes" in shown, dimensions: "dimensions" in shown, lengths: "length" in shown or "length" in under, centres: "centres" in shown,
    legend: "objects" in under, scale-bar: "scale-bar" in under, caption: none, level: 2)
}

/// **A fire-protection plan as an image**: the concept drawn over the architect's plan in the colours of the VKF sheet of symbols -- `#show-fire-plan`'s drawing without its figure.
///
/// ```typ
/// #figure(image-fire-plan("Treppenhaus"), kind: image, caption: [Brandschutzplan Treppenhaus]) <bs-treppe>
/// ```
///
/// ```typ
/// #figure(image-fire-plan("Pavillon-EG", width: 70%, detail-legend: "objects"), kind: image, caption: [Brandschutz Pavillon])
/// ```
///
/// It is an image to set in a native `#figure(…, kind: image, caption: […]) <label>`, which numbers it and lets `@label` cite it -- the caption and the label are the document's own.
///
/// - plan (str): the plan's id, as saved in Woodcore's fire-protection tab.
/// - width (relative, length): the width it is printed at, 100% of the room it is given by default.
/// - detail-legend (auto, str, array): what is set under the drawing, among the command's words -- `"none"` nothing; auto its defaults.
/// - scale (none, int, float): on an export sheet, the n of 1:n the plan is drawn at, where it is calibrated; none prints it at `width`.
/// - title (none, auto, str, content): on an export sheet, the line above the plan -- auto its name, description, storey and scale.
/// -> content
#let image-fire-plan(plan, width: 100%, detail-legend: auto, scale: none, title: none) = {
  let fn = "image-fire-plan"
  let under = image-details(fn, "detail-legend", detail-legend)
  if scale != none or title != none {
    // on a sheet (Q-015): the plan's own legend drawn on it where `"objects"` is asked, the scale bar under it
    return context {
      let r = sheet-fire-viewport-content(fn, plan, scale, if type(width) == ratio { none } else { width }, "objects" in under, "scale-bar" in under, title)
      sheet-last.update((dw: r.dw, n: r.n))
      r.shown
    }
  }
  fire-plan-drawing(plan, width: width, legend: "objects" in under, scale-bar: "scale-bar" in under, caption: none, level: 2)
}

/// **A static model as an image**: the system drawn in Woodcore, its supports, releases, loads and dimensions -- `#show-static-model`'s drawing without its figure.
///
/// ```typ
/// #figure(image-static-model("Bankli-Fall1"), kind: image, caption: [Statisches System]) <sys-1>
/// ```
///
/// ```typ
/// #figure(image-static-model("Bankli-Fall1", detail-figure: "dimensions", width: 60%), kind: image, caption: [System ohne Lasten])
/// ```
///
/// It is an image to set in a native `#figure(…, kind: image, caption: […]) <label>`, which numbers it and lets `@label` cite it -- the caption and the label are the document's own.
///
/// - model (str): the model's id, as saved in Woodcore.
/// - highlight (str, array, none): the part(s) put under a halo, by id.
/// - width (relative, length): the width it is printed at, 100% of the room it is given by default.
/// - detail-figure (auto, str, array): what the drawing shows, a word or a list of words of the command's vocabulary (lib/image-vocabulary.json); auto its defaults.
/// -> content
#let image-static-model(model, highlight: none, width: 100%, detail-figure: auto) = {
  let shown = image-details("image-static-model", "detail-figure", detail-figure)
  static-model-drawing(model, width: width, loads: "loads" in shown, dimensions: "dimensions" in shown, highlight: highlight, caption: none, level: 2)
}

/// **A schema as an image**: a detail drawn in Woodcore's «Schémas» tab -- what `#schema` drew.
///
/// ```typ
/// #figure(image-schema("VU-Skizze"), kind: image, caption: [Detail der Verbindung]) <fig-vu>
/// ```
///
/// ```typ
/// #figure(image-schema("VU-Skizze", highlight: "E1", detail-figure: (), width: 60%), kind: image, caption: [Das Element E1])
/// ```
///
/// It is an image to set in a native `#figure(…, kind: image, caption: […]) <label>`, which numbers it and lets `@label` cite it -- the caption and the label are the document's own.
///
/// - schema (str): the schema's id, as saved in Woodcore.
/// - highlight (str, array, none): the part(s) put under a halo, by id.
/// - width (relative, length): the width it is printed at, 100% of the room it is given by default.
/// - detail-figure (auto, str, array): what the drawing shows, a word or a list of words of the command's vocabulary (lib/image-vocabulary.json); auto its defaults.
/// -> content
#let image-schema(schema, highlight: none, width: 100%, detail-figure: auto) = {
  let shown = image-details("image-schema", "detail-figure", detail-figure)
  schema-drawing(schema, width: width, highlight: highlight, aids: "aids" in shown, level: 2)
}

/// **An excerpt of an annex as an image**: the region of a source's page Woodcore's «Annexes» tab framed -- `#show-extract`'s picture without its figure.
///
/// ```typ
/// #figure(image-extract("CO1-My"), kind: image, caption: [Biegemomente unter CO1]) <ex-my>
/// ```
///
/// ```typ
/// #figure(image-extract("CO1-My", width: 70%), kind: image, caption: [Auszug])
/// ```
///
/// It is an image to set in a native `#figure(…, kind: image, caption: […]) <label>`, which numbers it and lets `@label` cite it -- the caption and the label are the document's own.
///
/// - excerpt (str): the excerpt's id, as Woodcore's «Annexes» tab saved it.
/// - width (relative, length): the width it is printed at, 100% of the room it is given by default.
/// -> content
#let image-extract(excerpt, width: 100%) = extract-drawing(excerpt, width: width, caption: none, level: 2)
