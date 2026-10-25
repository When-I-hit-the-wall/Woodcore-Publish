// lib/calc-engine-connections.typ -- the forces in a connection's fasteners, what verify prints through, the shear resistance of a connector.
// Split out of lib/calc-engine.typ by subject, its text moved and not rewritten (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, G9). Each part imports the one before it, so a name reads everything defined above it as it did in one file; lib/calc-engine.typ imports the last and is what every caller names.

#import "calc-engine-records.typ": *

// --- Forces in the fasteners of a connection (docs/domain/connections.md §3.3quinquies)
// The one calculation this engine carries out rather than reads. N, V and M are written in the report -- until load combinations export them (section 3.5) there is nowhere else for them to come from -- so they are distributed here. Everything they are distributed *over* is data: the fasteners, the rotation centre, I_p, the directions and the members come from data/connections.json, calculated and validated in Python, and a force given by #image-polar-moment as the name of a variable written above (var-lookup) is taken with its unit checked. Woodcore previews the same distribution in Python (calc/domains/connection.py, fastener_forces), and the two are checked against each other.
//
// The frame is the detail schema's (section 3.3quinquies): millimetres, x to the right, z down; angles from x towards z; M positive the other way, turning z towards x. So F_x,i = (N_x + V_x)/n + M·Δz_i/I_p and F_z,i = (N_z + V_z)/n - M·Δx_i/I_p.

// The force arrows drawn on a connection's figure, as SVG elements, and the legend's note on them -- calc/domains/connection_svg.py's _arrow, _shares, force_arrows and share_note, rule for rule, so the report's figure and Woodcore's preview draw alike: a line and a polygon head, the yellow resultant outlined and labelled F1, F2, …, and all of them at one scale, the longest `figure.arrow` long, every one of them at its true length, so that a fastener's three actions add up to its resultant; a share too small to make out beside the resultants of a moment is drawn all the same, the legend then naming it with its value.

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
  for (name, vector, colour) in (("N/n", n-share, figure-colour("blue")), ("V/n", v-share, figure-colour("red"))) {
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
    out += svg-arrow(p, q, figure-colour("yellow"), resultant-width * figure.stroke, figure.head, edge: figure-colour("ochre-dark"))
    let dx = q.at(0) - p.at(0)
    let dy = q.at(1) - p.at(1)
    let length = calc.sqrt(dx * dx + dy * dy)
    if length > 1e-9 {
      let x = q.at(0) + 0.6 * figure.font * dx / length
      let y = q.at(1) + 0.6 * figure.font * dy / length + 0.22 * figure.font
      labels += "<text x=\"" + svg-number(x) + "\" y=\"" + svg-number(y) + "\" font-family=\"" + figure-palette.at("font-family") + "\" font-size=\""
      labels += svg-number(0.62 * figure.font) + "\" font-weight=\"bold\" fill=\"" + figure-colour("ochre-dark") + "\" text-anchor=\"middle\">F" + str(r.nr) + "</text>"
    }
  }
  for (p, moment) in figure.points.zip(moment-parts(forces, n-share, v-share)) {
    let d = step(moment, k)
    out += svg-arrow(p, (p.at(0) + d.at(0), p.at(1) + d.at(1)), figure-colour("green"), action-width * figure.stroke, share-head * figure.head)
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
  let n = get(vars.n, "value")
  let ip = get(vars.I_p, "value")
  let with-moment = ip > 0
  let xc = get(vars.x_c, "value")
  let zc = get(vars.z_c, "value")
  let a-n = get(vars.alpha_N, "value")
  let a-v = get(vars.alpha_V, "value")
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

// References of the block below (moved out of it, issue #115): `#show-polar-moment`'s drawing until the spec 2026-10-21-commandes-typst-refonte retired it; brought back by the spec 2026-10-22-image-polar-moment.
/// **A polar moment as an image, the forces in its fasteners drawn on it**: the figure of the connection Woodcore exported, and over it, for the N, V and M given, the arrows of each fastener -- its resultant F_i in yellow, labelled F1, F2, …, the part of M in green, N/n in blue and V/n in red, all at one scale, at their true length -- and, at the legend's foot, the parts too small to make out, with their value (the drawing `#show-polar-moment` printed, brought back as an image).
///
/// ```typ
/// #figure(image-polar-moment("VU-MP-1", N: 7.5, V: 25, M: 6.6), kind: image, caption: [Kräfte in den Verbindungsmitteln]) <vu-mp-1>
/// ```
///
/// ```typ
/// #domain("VU-MP-1-forces")[
///   #var("N", 4, "kN")
///   #var("V", 12, "kN")
///   #var("M", 2.5, "kNm")
///   #figure(image-polar-moment("VU-MP-1", N: "N", V: "V", M: "M", width: 60%), kind: image, caption: [Anschluss VU-MP-1])
/// ]
/// ```
///
/// It is an image to set in a native `#figure(…, kind: image, caption: […]) <label>`, which numbers it and lets `@label` cite it -- the caption and the label are the document's own. The file Woodcore writes for a polar moment (`#include domain-file("connection", id)`) sets it after the lines of its forces, naming them, so that the arrows follow the values written there. It draws and publishes nothing: F_max and the F_i are the file's own `#eq`.
///
/// - connection (str): the polar moment's id, as saved in Woodcore's «Moment polaire» tab.
/// - N (int, float, str): the total normal force in kN, positive in the direction of its arrow in the figure -- a number, or the name of a variable declared above (`N: "N"`), in kN.
/// - V (int, float, str): the total shear force in kN, likewise.
/// - M (int, float, str): the moment about the rotation centre in kNm, likewise; refused on a group whose fasteners have no lever arm.
/// - width (relative, length): the width it is printed at, 100% of the room it is given by default.
/// - detail-figure (auto, str, array): what the drawing shows, a word or a list of words of the command's vocabulary (lib/image-vocabulary.json) -- `"forces"` the arrows; `()` the figure as exported; auto its defaults.
/// -> content
#let image-polar-moment(connection, N: 0, V: 0, M: 0, width: 100%, detail-figure: auto) = {
  let fn = "image-polar-moment"
  let shown = image-details(fn, "detail-figure", detail-figure)
  context {
    let conns = load-connections().connections
    if type(connection) != str or connection not in conns {
      panic(fn + ": no connection " + repr(connection) + " -- " + (if conns.len() == 0 { "none saved yet (save one in Woodcore's polar moments tab)" } else { "valid connections: " + conns.keys().join(", ") }))
    }
    let c = conns.at(connection)
    if not c.at("calculated", default: true) {
      panic(fn + ": connection '" + connection + "' cannot be drawn -- " + c.reason + ", then export again.")
    }
    // A force given as a number, or as the **name** of a variable written above with #var or #eq -- read here, in the context, from the domain the call stands in and then the document's own (var-lookup), its unit the one the drawing computes in (#show-polar-moment's rule)
    let magnitude(x, name, unit) = {
      let x = if type(x) == str {
        let found = var-lookup(var-registry.get(), x)
        if found == none {
          let names = var-names(var-registry.get())
          panic(fn + ": " + name + ": no variable named " + repr(x) + " -- " + (if names.len() == 0 { "none declared above" } else { "declared above: " + names.join(", ") }))
        }
        found
      } else { x }
      if type(x) == dictionary and "value" in x {
        if get(x, "unit") != unit { panic(fn + ": " + name + " is a variable in " + repr(get(x, "unit")) + " -- expected " + unit) }
        get(x, "value")
      } else {
        if type(x) != int and type(x) != float { panic(fn + ": " + name + " must be a number in " + unit + " or the name of a variable, got " + repr(x)) }
        x
      }
    }
    let n-total = magnitude(N, "N", "kN")
    let v-total = magnitude(V, "V", "kN")
    let m-total = magnitude(M, "M", "kNm")
    if m-total != 0 and get(c.vars.I_p, "value") <= 0 {
      panic(fn + ": connection '" + connection + "' has I_p = 0 -- its fasteners have no lever arm about the rotation centre, so it cannot take M = " + str(m-total) + " kNm")
    }
    let svg = read(figure-path(c.figure.files.at(report-lang())))
    if "forces" in shown {
      let dist = polar-distribution(c, n-total, v-total, m-total)
      let share(total, a) = (total / dist.n * calc.cos(a * 1deg), total / dist.n * calc.sin(a * 1deg))
      let n-share = share(n-total, dist.an)
      let v-share = share(v-total, dist.av)
      let arrows = fastener-arrows(c.figure, dist.forces, n-share, v-share)
      let note = share-note(c.figure, dist.forces, n-share, v-share)
      // the drawing's own metadata, what tests/test_arrows.py holds against Python's: the forces it drew, and the arrows and the note it set in the figure
      [#metadata((forces: dist.forces, n-share: n-share, v-share: v-share, arrows: arrows, note: note)) <woodcore-polar-arrows>]
      image(bytes(svg.replace("<!-- forces -->", arrows).replace("<!-- note -->", note)), format: "svg", width: width)
    } else {
      image(bytes(svg), format: "svg", width: width)
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

// Two numbers closer than this, relatively, are the same number: float noise must not fail a check that holds exactly (0.1 + 0.2 against 0.3). The absolute floor of 1 keeps that meaningful near zero. It is the rule `show-polar-moment` used to find the fasteners tied at the largest force (the spec 2026-10-21-commandes-typst-refonte retired it), and the same constant.
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
