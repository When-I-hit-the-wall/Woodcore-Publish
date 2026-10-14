// The steel checks of Woodcore's «Acier» tabs, printed (issues #50-#52, spec 2026-10-12-section-acier D-09, D-17; docs/domain/steel.md).
//
// A steel check is computed by the export, once, in Python (calc/domains/steel_check.py, steel_resistance.py), and data/steel.json holds its rows in the shape show-calc prints: its vars, its steps and its tables, each with its symbol, its label in German (a term of calc/i18n/strings.json, which tl-str translates), its level and its citation of SIA 263. Nothing here computes: `#show-check-steel` heads the check, has show-calc print its rows, and prints its verdict -- the utilisation `ratio <= 1` the export wrote with the vars' keys, which `verify` sets in letters, numbers and value with ✔ or ✘. The vars and the utilisation are published in the var-domain `"<id>-verify-steel-<kind>"`, which is what the Nachweisübersicht walks (lib/summary.typ) and what `#val("eta", domain: "ST-01-verify-steel-bending")` reads.

#import "calc-engine.typ": check-shown, level-plan, plan-any, selection-level, show-calc, steel-domain, load-steel, t-str, tl-str, var-registry, var-store, annotated-rows

// The var-domain a check's values are published in -- the timber checks' `"<member>-verify-<check>"` shape, so the summary finds it by the same mark.
#let steel-domain-of(id, kind) = id + "-verify-steel-" + kind

/// Every steel check saved in Woodcore, in file-name order -- the loop a section printing all of them is written as.
///
/// ```typ
/// #for id in check-steel-ids() {
///   show-check-steel(id, level: 1)
/// }
/// ```
///
/// ```typ
/// Gespeicherte Stahlnachweise: #check-steel-ids().join(", ").
/// ```
///
/// -> array
#let check-steel-ids() = load-steel().checks.keys()

/// A steel check saved in Woodcore's «Acier» tabs, printed: its heading -- the check's kind after SIA 263:2013 and its id --, the line of what it checks («IPE 360, S355, Position S010»), its calculation as the export computed it, at the level asked, and its verdict. The kinds are the section class (Tabelle 5), the tension and the compression of the section (5.1.2), its bending (5.1.3, 5.1.6, 5.2.3, 5.2.6) and its shear (5.1.4, 5.1.5).
///
/// ```typ
/// #show-check-steel("ST-01")
/// ```
///
/// ```typ
/// #show-check-steel("ST-02", level: 3, unit: "%")
/// ```
///
/// - id (str): the check's id, the name of its file in Woodcore-Datei/steel/.
/// - level (int, auto): 1 the heading, its line, the class and the verdict; 2 the resistances; 3 every value and step; -1 with `shown:` only what it names. auto follows the report.
/// - shown (dictionary, none): at level -1, the keys to print and at which level, `(N_Rd: 2, eta: 1)`.
/// - title (auto, none, str): auto the check's kind and id, none no heading, or a heading of your own.
/// - unit (auto, str): the utilisation as a ratio (auto) or in percent ("%").
/// -> content
#let show-check-steel(id, level: auto, shown: none, title: auto, unit: auto) = context {
  import "formula.typ": verify-core, var-domain
  let checks = load-steel().checks
  assert(type(id) == str and id in checks,
    message: "show-check-steel: no steel check " + repr(id) + " -- " + (if checks.len() == 0 { "none saved in Woodcore yet (its «Acier» tabs)" } else { "valid steel checks: " + checks.keys().join(", ") }))
  assert(unit in (auto, "%"), message: "show-check-steel: unit is auto or \"%\" -- got " + repr(unit))
  let c = checks.at(id)
  if not c.calculable {
    panic("show-check-steel: steel check '" + id + "' cannot be calculated -- " + c.reason + ". Open it in Woodcore's «Acier» tabs, put that right and export again.")
  }
  check-shown("show-check-steel", level, shown, c.vars.keys() + range(c.at("tables", default: ()).len()).map(i => "table-" + str(i + 1)), levels: (auto, 1, 2, 3))
  let plan = level-plan(level, shown)
  let heading = if title == auto { t-str("steel.kind." + c.kind) + " " + id } else { title }
  if heading != none {
    block(above: 1em, below: 0.7em, sticky: true, text(weight: "bold", heading))
  }
  // what is checked, at every level: the profile and the grade, where each came from, and the position
  let what = (c.designation, c.grade).filter(s => s != none and s != "").join(", ")
  if c.position != none { what += ", " + t-str("steel.position") + " " + c.position }
  block(above: 0.4em, below: 0.6em, text(what))
  let dom = steel-domain-of(id, c.kind)
  var-domain(dom, {
    // the vars, published: what `val` and the summary read, and what the verdict's ratio names
    var-registry.update(d => {
      for (key, v) in c.vars { d = var-store(d, key, v) }
      if c.eta != none {
        d = var-store(d, "eta", (value: if unit == "%" { c.eta * 100 } else { c.eta }, unit: if unit == "%" { "%" } else { "" },
          symbol: "eta", label: "Ausnutzung", description: none, norm: "SIA 263", norm_ref: c.at("clause", default: ""), source: "python:domains/steel_resistance.py"))
      }
      d
    })
    if plan.picked {
      show-calc(steel-domain, id, level: selection-level, shown: plan.shown, title: none)
    } else {
      show-calc(steel-domain, id, level: plan.lv, title: none)
    }
    // what the check leaves to the engineer, in the report's language (a term of calc/i18n/strings.json)
    for note in c.at("notes", default: ()) { block(above: 0.5em, below: 0.5em, text(size: 0.9em, tl-str(note))) }
    if c.eta != none {
      let relation = if unit == "%" { "(" + c.ratio + ") * (100 \"%\") <= (100 \"%\")" } else { c.ratio + " <= 1" }
      let lv = if plan.picked { if "eta" in plan.shown { 3 } else { 0 } } else { plan.lv }
      if lv == 1 { block(above: 0.7em, below: 0.7em, verify-core(relation, level: 1, brief: true)) }
      else if lv >= 2 { block(above: 1em, below: 0.9em, verify-core(relation, level: 3, brief: true)) }
      else { verify-core(relation, level: 0, brief: true) }
    }
  })
}
