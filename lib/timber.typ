// The member checks of SIA 265:2021, chapter 4.2, written in the report and computed there (v0.88).
//
// `#member("S001")` writes a member down -- any position, whose line it prints, and for timber of SIA 265 Tabelle 8 or 9 with a rectangular or a round section also the section's values, its strength class, its moisture class and the design values they give -- into a `var-domain` named after it, and every `#verify-*` command checks one kind of action on it: tension (4.2.1), compression (4.2.2 and buckling, 4.2.8), compression perpendicular or at an angle to the grain (4.2.2.2, 4.2.2.3), bending (4.2.3 and lateral torsional buckling, 4.2.9), bending with a normal force (4.2.4, with 4.2.8 and 4.2.9), shear and torsion (4.2.5), Abscheren (4.2.6), and shear with a stress perpendicular to the grain (4.2.7).
//
// Nothing here computes a number itself. Every line is a `#var`, an `#eq` or a `#verify` of lib/formula.typ, so a check is printed the way a calculation written by hand is -- the formula in letters, the same formula with its numbers, the answer, the relation double-ruled with its ✔ or ✘ -- with formula.typ's unit algebra, its levels and its stacking at the `=` signs; and what a check works out stays in the registry, in a `var-domain` named `"<member>-verify-<check>"`, where `#val`, `#find` and a `#verify` further down can read it.
//
// Every norm value is read from calc/norms/ by the relative path `../calc/norms/`, as lib/distance.typ reads its tables (docs/architecture/principles.md §2 rule 13, 11): the design values of Tabellen 8 and 9, eta_w of Tabelle 4, eta_t of 2.2.6, the characteristic values of Anhang B, and the constants of clauses 3.4.2.3, 4.2.6, 4.2.7, 4.2.8 and 4.2.9. calc/norms/sia265.py checks the same files before an export reads anything.
//
// ⚠️ Untraced, like everything computed in Typst (docs/project/purpose.md §1): nothing reaches data/. What the checks guarantee is that the printed formula, the printed numbers and the printed verdict are one statement, and that the values of the norm are the transcribed ones.
//
// ⚠️ The import runs both ways, and that is the one trick of this file. formula.typ imports the public commands from here by name, which is how commands.typ -- which re-exports formula.typ at the wildcard -- gives every section `member` and the `verify-*` commands, and none of the helpers below. This file needs `var`, `eq` and `verify` from formula.typ in turn, and a module-level import back would be a cycle Typst refuses; so each command imports them **inside its body**, where the import runs when the command is called and formula.typ is already evaluated.
#import "calc-engine.typ": check-shown, level-plan, selection-level, plan-at, plan-part, plan-row, shown-keys, shown-parts, annotated-rows, colon-str, fmt-decimals, t-str, load-position, number-digits, position-ids, known-position-ids, position-archived-note, position-line, position-refusal, render-prose, resolve-level, semicolon-str, tl-str, value-type, var-lookup, var-names, var-registry, var-store

// --- The norm, as calc/norms/ states it --------------------------------------

// Where the norm files are, seen from this file.
#let timber-dir = "../calc/norms/"

// The files this command reads, by what they hold. calc/norms/sia265.py names the same files, and tests/test_timber.py holds the two lists equal.
#let timber-files = (
  eta-w: "sia265-2021-tab04-eta-w",
  eta-t: "sia265-2021-2.2.6-eta-t",
  solid: "sia265-2021-tab08-vollholz",
  glulam: "sia265-2021-tab09-brettschichtholz",
  characteristic-solid: "sia265-2021-tab47-druckfestigkeit-e005-vollholz",
  characteristic-glulam: "sia265-2021-tab48-druckfestigkeit-e005-brettschichtholz",
  k-h: "sia265-2021-3.4.2.3-k-h",
  shear-off: "sia265-2021-4.2.6-abscheren",
  shear-perp: "sia265-2021-4.2.7-schub-querdruck",
  buckling: "sia265-2021-4.2.8-knicken",
  lateral: "sia265-2021-4.2.9-kippen",
  fire: "sia265-2021-4.5-brandfall",
)

#let timber-json(what) = json(timber-dir + timber-files.at(what) + ".json")

// One clause file's `clause` block.
#let timber-clause(what) = timber-json(what).clause

// The two families a strength class belongs to: Tabelle 8 (Vollholz, keilgezinktes Vollholz, Balkenschichtholz) and Tabelle 9 (Brettschichtholz). What gamma_M/eta_M, beta_c and the Abscheren factor are chosen by.
#let timber-tables = (("solid", "table_8"), ("glulam", "table_9"))

// The family as the clause files key it: "Vollholz" standing for Vollholz, keilgezinktes Vollholz and Balkenschichtholz, as the norm groups them.
#let timber-family-word(family) = if family == "glulam" { "Brettschichtholz" } else { "Vollholz" }

// Every strength class the two tables carry, for a refusal.
#let timber-grade-ids() = timber-tables.map(((file, key)) => timber-json(file).at(key).grades.map(g => g.id)).flatten()

// A strength class, as its table states it: (row, table, family), `family` being "solid" or "glulam". none for a class no table carries.
#let timber-grade(grade) = {
  for (file, key) in timber-tables {
    let tbl = timber-json(file).at(key)
    let row = tbl.grades.find(g => g.id == grade)
    if row != none { return (row: row, table: tbl, family: file) }
  }
  none
}

// The characteristic values of Anhang B for a strength class: f_c,0,k and E_0,05, which the relative slenderness of buckling and lateral torsional buckling read (4.2.8.4, 4.2.9.3).
#let timber-characteristic(grade) = {
  for (file, key) in (("characteristic-solid", "table_47"), ("characteristic-glulam", "table_48")) {
    let row = timber-json(file).at(key).grades.find(g => g.id == grade)
    if row != none { return row }
  }
  none
}

// eta_w of Tabelle 4, for the resistance or the stiffness, and the moisture classes it knows.
#let timber-eta-w(moisture, kind) = {
  let classes = timber-json("eta-w").table_4.classes
  let row = classes.find(c => c.id == moisture)
  if row == none { none } else { row.at(kind) }
}
#let timber-moisture-ids() = timber-json("eta-w").table_4.classes.map(c => c.id)

// Saint-Venant's torsion of a rectangle whose longer side is `ratio` times its shorter: k_tor with tau_max = T / (k_tor · a · c²), from the series of the theory of elasticity (Timoshenko & Goodier) -- k_1 = (1 − 192/(π⁵ r) · Σ tanh(nπr/2)/n⁵)/3 for the torsional constant J = k_1 · a · c³, and tau_max = T · c / J · (1 − 8/π² · Σ 1/(n² cosh(nπr/2))), n odd. 0.208 for a square, 1/3 for a thin plate; the Bemessungsbeispiele zur SIA 265 read the same values off a table (p. 114, h/b = 2.75: W_T = 2.95·10⁶ mm³).
#let timber-torsion-k(ratio) = {
  let (s1, s2) = (0.0, 0.0)
  for n in range(1, 60, step: 2) {
    let x = n * calc.pi * ratio / 2
    s1 += (if x > 40 { 1.0 } else { calc.tanh(x) }) / calc.pow(n, 5)
    s2 += if x > 40 { 0.0 } else { 1 / (n * n * calc.cosh(x)) }
  }
  let k1 = (1 - 192 / (calc.pow(calc.pi, 5) * ratio) * s1) / 3
  k1 / (1 - 8 / (calc.pi * calc.pi) * s2)
}

// --- The members of the report -------------------------------------------------

// Every member written down so far, by its name: its strength class, its family, its moisture class, its shape (`rec` or `cir`), its radii of gyration and the position it was read from -- or, for a position `#member` computed not (v0.94), `calculable: false` and the reason every check on it is refused with. What a `verify-*` command needs beyond the numbers, which live in the registry under the member's own name.
#let timber-members = state("timber-members", (:))

// A section's side: a number in mm, or a Typst length (`20cm`).
#let timber-mm(fn, what, x) = {
  if value-type(x) in (int, float) { return x }
  if value-type(x) == length { return x.mm() }
  panic(fn + ": " + what + " is a number in mm or a length (20cm) -- got " + repr(x))
}

// The section a member is calculated with -- `(shape: "rec", b:, h:)` or `(shape: "cir", d:)` in mm -- or `(reason: …)` saying why there is none. The position's is read off the `section` domains/section.py wrote into its record at the export (v0.94, docs/domain/positions.md §7): nothing here reads its `dimension` text, which until v0.94 a regular expression of this file parsed a second time beside schema.parse_section. A record exported before carries no `section` and is not guessed at: it is exported again, or the call states the section.
#let timber-section-of(pos, record) = {
  if not ("section" in record) {
    return (reason: pos + " was exported before Woodcore read a position's section (data/positions/" + pos + ".json carries none) -- export the project again (Import données), or state b: and h:, or d:, in the call")
  }
  let s = record.section
  if s == none {
    let dim = str(record.at("dimension", default: ""))
    return (reason: pos + " has no section" + (if dim != "" { " -- its dimension " + repr(dim) + " is descriptive text" } else { "" }) + ": give it a section type in Woodcore's Positions tab (rec b/h, cir d), or state b: and h:, or d:, in the call")
  }
  if s.kind == "steel" {
    let grade = record.at("strength_class", default: "")
    return (reason: pos + " is steel (" + s.text + (if grade != "" { ", " + grade } else { "" }) + "): #member computes timber of SIA 265 Tabelle 8/9 only")
  }
  if s.type == "rec" { return (shape: "rec", b: s.b, h: s.h) }
  if s.type == "cir" { return (shape: "cir", d: s.d) }
  (reason: pos + " is " + (if s.type == "clt" { "a CLT panel" } else { "a plate" }) + " (" + s.text + "): #member computes a rectangular or a round section only")
}

// The woods Tabelle 13 reads a charring rate for, and the four faces of a rectangle the fire may reach -- calc/norms/sia265.py's FIRE_WOODS and FIRE_SIDES, which tests/test_fire_resistance.py holds equal to these.
#let timber-fire-woods = ("softwood", "beech", "oak", "cladding")
#let timber-fire-sides = ("bottom", "top", "left", "right")

// The ideal residual section of SIA 265 4.5.2.2 for `fire:` of #member (issue #46): `(duration:, sides:, wood:)` checked, the row of Tabelle 13 the grade and the wood give, d_char,n = beta_n · t (50), d_ef = d_char,n + d_red (49), the section reduced by d_ef on each exposed face (Figur 13), 4.5.2.4's minimum width where several faces burn, and (51)'s factor. `sec` the section before the fire, `row` the grade's row of Tabelle 8 or 9, `family` "solid" or "glulam". none for `fire: none`. Every refusal is a panic: a saved check that cannot be computed is refused before, with its reason (calc/domains/member_check.py, `resolve`).
#let timber-fire-of(fn, fire, sec, row, family) = {
  if fire == none { return none }
  if value-type(fire) != dictionary { panic(fn + ": fire is none or (duration: 60, sides: (\"bottom\", \"left\", \"right\"), wood: none) -- got " + repr(fire)) }
  for key in fire.keys() {
    if not (key in ("duration", "sides", "wood")) { panic(fn + ": fire has no key " + repr(key) + " -- it takes duration:, sides: and wood:") }
  }
  let clause = timber-clause("fire")
  let t = fire.at("duration", default: none)
  if not (value-type(t) in (int, float)) or t <= 0 { panic(fn + ": fire.duration is the fire resistance in minutes, above 0 -- got " + repr(t)) }
  if t > clause.d_red.max_duration { panic(fn + ": fire.duration is " + str(t) + " min -- SIA 265 " + clause.d_red.norm_ref + " states d_red for a fire resistance up to " + str(clause.d_red.max_duration) + " minutes only") }
  let sides = fire.at("sides", default: ())
  if value-type(sides) == str { sides = (sides,) }
  if value-type(sides) != array or sides.len() == 0 or sides.any(s => not (s in timber-fire-sides)) {
    panic(fn + ": fire.sides lists the faces the fire reaches, among " + timber-fire-sides.map(repr).join(", ") + " -- got " + repr(sides))
  }
  if sides.dedup().len() != sides.len() { panic(fn + ": fire.sides names a face twice -- got " + repr(sides)) }
  if sec.at("shape", default: none) != "rec" { panic(fn + ": fire: computes the residual section of a rectangle (SIA 265 4.5.2.2, Figur 13) -- a round section is not computed") }
  let wood = fire.at("wood", default: none)
  if wood != none and not (wood in timber-fire-woods) { panic(fn + ": fire.wood is none or one of " + timber-fire-woods.map(repr).join(", ") + " -- got " + repr(wood)) }
  if wood == none {
    if row.species != "Nadelholz" { panic(fn + ": " + row.id + " is " + row.species + " -- SIA 265 Tabelle 13 reads beech and oak at different rates: state fire.wood \"beech\" or \"oak\"") }
    wood = "softwood"
  }
  let word = timber-family-word(family)
  let rate = clause.charring.rows.find(r => wood in r.woods and word in r.families)
  if rate == none { panic(fn + ": SIA 265 Tabelle 13 gives no row for " + wood + " " + word) }
  let nb = sides.filter(s => s in ("left", "right")).len()
  let nh = sides.filter(s => s in ("bottom", "top")).len()
  let d-char = rate.beta_n * t
  let d-ef = d-char + clause.d_red.value
  if sides.len() >= 2 {
    let need = clause.min_width.rows.find(r => t <= r.duration)
    let least = calc.min(sec.b, sec.h)
    if need != none and least < need.b { panic(fn + ": " + fmt-decimals(least, 3) + " mm is under the minimum width of " + str(need.b) + " mm SIA 265 " + clause.min_width.norm_ref + " sets for R" + str(need.duration) + " with the fire on several faces") }
  }
  let b = sec.b - nb * d-ef
  let h = sec.h - nh * d-ef
  if b <= 0 or h <= 0 { panic(fn + ": the fire leaves no section -- d_ef = " + fmt-decimals(d-ef, 3) + " mm on " + str(sides.len()) + " faces of " + fmt-decimals(sec.b, 3) + "/" + fmt-decimals(sec.h, 3) + " mm") }
  (t: t, sides: sides, wood: wood, row: rate, beta: rate.beta_n, d-red: clause.d_red.value, d-char: d-char, d-ef: d-ef, nb: nb, nh: nh, b0: sec.b, h0: sec.h, b: b, h: h, factor: clause.resistance_factor.value, clause: clause)
}

// Every `eq` of the checks, on a line of its own (v0.117, issue #19, spec D-07): `#eq` prints inline by default since then, as `#var` does, and a check's working is a column of lines with their citations in the right-hand column -- so the checks pass `note: "line"` here, once, and every page of a check looks as it did. A call that names its own `note` keeps it.
#let timber-eq(..args) = {
  import "formula.typ": eq
  let named = args.named()
  if not ("note" in named) { named.insert("note", "line") }
  eq(..args.pos(), ..named)
}

// The level a line below a command is printed at: nothing below `from`, the command's own level from there on.
#let timber-sub(lv, from) = if lv >= from { lv } else { 0 }

// A value a check is handed -- a force, a moment, a length, a stress -- as a record the registry can hold: a number in `unit`, a Typst length for a length, a string «40 kN» with its unit, the name of a variable declared above the line, or a var object. `none` where a name is not declared, which the context of the command then refuses: read inside an update, which is the one place the registry is a plain dictionary.
#let timber-value(d, x, unit) = {
  if value-type(x) in (int, float) { return (value: x, unit: unit) }
  if value-type(x) == length { return (value: x.mm(), unit: "mm") }
  if value-type(x) == dictionary and "value" in x { return (value: x.value, unit: x.at("unit", default: "")) }
  if value-type(x) == str {
    let m = x.match(regex("^\s*([-−]?[0-9]+(?:\.[0-9]+)?)\s*([^0-9\s].*?)\s*$"))
    if m != none { return (value: float(m.captures.at(0).replace("−", "-")), unit: m.captures.at(1)) }
    let r = var-lookup(d, x)
    if r == none { return none }
    return (value: r.value, unit: r.at("unit", default: ""))
  }
  none
}

// Stores what a call hands a check under `key`, printed as `symbol` -- through `transform`, which a check uses to keep only the magnitude of a signed force. Inside an update: nothing is refused here, a refusal written in an update being silent where nothing reads the registry again (formula.typ, `var-unit`); `timber-need` refuses it in the context.
#let timber-store(key, symbol, x, unit, label: none, transform: v => v) = var-registry.update(d => {
  let r = timber-value(d, x, unit)
  if r == none { return d }
  var-store(d, key, (value: transform(r.value), unit: r.unit, symbol: symbol, label: label, description: none, norm: none, norm_ref: "", source: none))
})

// The refusal of a value a check could not read, in its context.
#let timber-need(fn, d, what, x) = {
  if x == none { return }
  if value-type(x) in (int, float, length) { return }
  if value-type(x) == dictionary {
    if "value" in x { return }
    panic(fn + ": " + what + " is a var object with a value and a unit -- got a dictionary without them")
  }
  if value-type(x) == str {
    if x.match(regex("^\s*[-−]?[0-9]+(?:\.[0-9]+)?\s*[^0-9\s]")) != none { return }
    if var-lookup(d, x) != none { return }
    panic(fn + ": " + what + " names " + repr(x) + ", which is not declared above this line -- declare it with #var(" + repr(x) + ", …), or write the value with its unit (\"40 kN\"). Declared here: " + var-names(d).join(", "))
  }
  panic(fn + ": " + what + " is a number, a value with its unit (\"40 kN\"), the name of a variable or a var object -- got " + repr(x))
}

// The value a record holds, read in a context.
#let timber-read(d, key) = {
  let r = var-lookup(d, key)
  if r == none { none } else { r.value }
}

// Copies every value of a member into the check that reads it, so that the check's formulas name `A`, `f_m_d` and `E_0_05` without reaching into another domain -- and so that none of them can be taken silently from a variable of the report that happens to share the name.
#let timber-take(member) = var-registry.update(d => {
  let src = d.domains.at(member, default: (:))
  for (k, r) in src { d = var-store(d, k, r) }
  d
})

// The member a check names, or a refusal listing the members written down.
#let timber-member-of(fn, member) = {
  let known = timber-members.get()
  if value-type(member) != str or not (member in known) {
    panic(fn + ": no member " + repr(member) + " is written down above this line -- write it with #member(" + repr(member) + "), "
      + (if known.len() == 0 { "none is yet" } else { "or name one of " + known.keys().map(repr).join(", ") }))
  }
  let m = known.at(member)
  // a position #member printed and computed not -- steel, a plate, no moisture class -- is refused here, by the reason it was written down with
  if not m.at("calculable", default: true) { panic(fn + ": " + m.reason) }
  m
}

// The heading of a check, its citation in the right-hand column (docs/typst/citations.md §10).
#let timber-title(body, ref) = block(above: 1em, below: 0.5em, sticky: true,
  annotated-rows(((text(weight: "bold", body), if ref == none { none } else { (norm: "SIA 265", norm_ref: ref) }),)))

// The heading of one part of a check -- «Tragsicherheit», «Stabilität», «Knicken um die z-Achse» -- its clause in the right-hand column. The two concepts are set apart in every check that has both (the engineer: «clairement séparer la sécurité structurale et la stabilité»).
#let timber-part(body, ref) = block(above: 0.9em, below: 0.9em, sticky: true,
  annotated-rows(((emph(body), if ref == none { none } else { (norm: "SIA 265", norm_ref: ref) }),)))

// A line of prose under a check -- what was not checked and why -- in the orange of what the report says of itself (the connector's warnings).
#let timber-note(body) = block(above: 0.4em, below: 0.4em, text(size: 0.9em, fill: rgb("#b35c00"), body))

// The check's own title: auto names the check and its member, none prints none, a string replaces it.
#let timber-heading(title, words, member) = if title == auto { [#tl-str(words) --- #member] } else if title == none { none } else { render-prose(tl-str(title)) }

#let timber-levels = (auto, 0, 1, 2, 3)
#let timber-check-level(fn, level) = {
  if not (level in timber-levels) { panic(fn + ": invalid level " + repr(level) + " -- use auto, 0, 1, 2 or 3") }
}
#let timber-check-unit(fn, unit) = {
  if not (unit in (auto, "%")) { panic(fn + ": unit is auto (a ratio, 0.603) or \"%\" (60.3 %) -- got " + repr(unit)) }
}

// `stability:` of verify-bending and verify-bending-normal: a bool, and with false -- the section alone -- no input of lateral torsional buckling, which would say a check is made that is not.
#let timber-check-stability(fn, stability, a, sigma-crit) = {
  if value-type(stability) != bool { panic(fn + ": stability is true or false -- got " + repr(stability)) }
  if not stability and (a != none or sigma-crit != none) { panic(fn + ": " + (if a != none { "a:" } else { "sigma-m-crit:" }) + " is an input of lateral torsional buckling -- stability: false checks the section alone") }
}

// The degree of utilisation, and the relation it is held against: a ratio against 1, or a percentage against 100 %.
#let timber-eta-unit(unit) = if unit == "%" { "%" } else { "" }
#let timber-one(unit) = if unit == "%" { "100 \"%\"" } else { "1" }

// The verdict of one part of a check, at its level -- the check's, or at -1 the level `shown:` gives the key of its utilisation, `eta`, `eta_s`… (issue #58): the ratio of the action to the resistance against 1 -- never the utilisation η, never the stress against the resistance (issue #12, the engineer, 09.10.2026). Level 1 prints the ratio's symbols and its value, `σ_t,0,d / f_t,0,d = 0.41 ⩽ 1 ✔`; levels 2 and 3 its symbols, its numbers and its value, `σ_t,0,d / f_t,0,d = 2.04 N/mm² / 4.97 N/mm² = 0.41 ⩽ 1 ✔`; a sum of ratios is its own ratio, `… ⩽ 1` already. In percent the ratio is printed in percent and the relation's right-hand side is not, `σ_t,0,d / f_t,0,d = 41 % ✔` (the engineer: «il ne faut pas indiquer en plus <= 100%») -- the comparison is still made against 100 %.
//
// `eta` the key and `eta-formula` the formula of the utilisation, which is the ratio printed: η is still stored at every level, where #val and the summary of the checks read it (summary.typ), and printed nowhere. Until issue #12 a `relation`, the norm's inequality, was passed beside it and printed from level 2, η alone at level 1.
#let timber-verdict(plan, eta, eta-symbol, eta-formula, unit) = {
  import "formula.typ": verify-core
  // the verdict's own level: the check's, or at -1 the one `shown:` gives the utilisation's key, 0 where it names it not (issue #58)
  let lv = plan-at(plan, eta, 1)
  timber-eq(eta, eta-symbol, eta-formula, unit: timber-eta-unit(unit), level: 0)
  let percent = unit == "%"
  let relation = eta-formula + " <= " + timber-one(unit)
  let shown(level) = verify-core(relation, level: level, brief: true, left-unit: if percent { "%" } else { none }, left-only: percent)
  // each verdict a line of its own: a verify is inline content, and two of them in a row ran on in one line
  if lv == 1 { block(above: 0.7em, below: 0.7em, shown(1)) }
  else if lv >= 2 { block(above: 1em, below: 0.9em, shown(3)) }
  else { shown(0) }
}

// --- The member ----------------------------------------------------------------

/// Writes a member down -- any position of the project (Woodcore's Positions tab), or a member stated in the call -- and prints its line: at level 1 the position's line, «T001: Träger, Fichte C24, 100/200 mm, Feuchteklasse 2», its type, material and strength class, section, moisture class, the axes and the description a call asks for. For timber of SIA 265 Tabelle 8 or 9 with a rectangular or a round section it also computes the section's values and the design values, in a `var-domain` named after it, where every `verify-*` command reads them.
///
/// ```typ
/// #member("S001")
/// ```
///
/// ```typ
/// #member("R1", b: 120, h: 240, grade: "GL24h", moisture-class: 1, level: 3)
/// ```
///
/// ```typ
/// #for id in position-ids() {
///   member(id, level: 1, description: true)
/// }
/// ```
///
/// ```typ
/// #member("S002", level: 3)
/// ```
///
/// ```typ
/// #member("R", d: 200, grade: "GL24h", moisture-class: 1, level: 3)
/// ```
///
/// ```typ
/// #member("T001", level: 0)
/// #val("f_m_y_d", domain: "T001", type: "expression")
/// ```
///
/// ```typ
/// #member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: -1, shown: (A: 2, W_y: 1, f_m_y_d: 3))
/// ```
///
/// ```typ
/// #member("FB", b: 140, h: 200, grade: "C24", moisture-class: 1, fire: (duration: 60, sides: ("bottom", "left", "right")), level: 3)
/// ```
///
/// ```typ
/// #member("FS", b: 140, h: 240, grade: "D30", moisture-class: 1, fire: (duration: 30, sides: ("bottom", "top", "left", "right"), wood: "oak"), level: 2)
/// #verify-compression("FS", N: "-185 kN", l: 2400mm, level: 1)
/// ```
///
/// Read from the position of the same name where there is one: its section -- what the export read off its `section type` and `dimension` (a `rec` gives b and h, a `cir` d) --, its strength class and its moisture class, each written over by the argument that states it. A member that is no position states its section, `b:` and `h:` or `d:`, its grade and its moisture class. A position that is not such a member -- steel, a plate, a CLT panel, a strength class Tabelle 8 and 9 do not give, no moisture class -- is printed and computed not: the member is written down as one that cannot be checked, and every `verify-*` on it says why.
///
/// What it stores, and a check copies: b, h, A, W_y, W_z, I_y, I_z, i_y, i_z, and W_t (for a rectangle Saint-Venant's, from its series with k_tor; for a round section π·d³/16, d standing for b and h where a check needs a width); eta_w for the resistance and eta_w_E for the stiffness (Tabelle 4), eta_t (2.2.6); the design values f_m_y_d, f_m_z_d, f_t_0_d, f_c_0_d, f_t_90_d, f_c_90_d and f_v_d of Tabelle 8 or 9, times eta_w and eta_t -- and, for glulam, f_m by k_h (3.4.2.3); the characteristic values f_m_k and f_c_0_k and the stiffness E_0_05 times eta_w_E, which buckling and lateral torsional buckling read (Anhang B). `#val("A", domain: "S001")` reads one, `#find(object: "variable", domain: "S001")` lists them.
/// - name (str): the member's name, and the `var-domain` its values are stored in. Where it is a position of the project, the position is read unless `position:` says otherwise.
/// - b (auto, int, float, length): the width in mm, or a length (10cm). auto reads the position's section.
/// - h (auto, int, float, length): the height in mm, likewise -- the side in whose plane M_y bends.
/// - d (auto, int, float, length): the diameter of a round section, in mm, in place of b and h. auto reads the position's section.
/// - grade (auto, str): the strength class, one of Tabelle 8 or 9 -- "C24", "GL24h". auto reads the position's strength class.
/// - moisture-class (auto, int): 1, 2 or 3 (Tabelle 3); auto reads the position's.
/// - position (auto, none, str): the position read for what the call does not state. auto is the position named `name` where there is one; none reads none.
/// - impact (bool): true for stossartige Einwirkungen -- impact, earthquake, collision -- which take eta_t = 1.4 (2.2.6).
/// - k-h (bool): for glulam, whether f_m,d takes the height factor k_h of 3.4.2.3 -- which the norm allows («darf») for a height under 600 mm, a round section's being its diameter. true by default; no effect on solid timber, nor in the fire situation (4.5.2.5).
/// - fire (none, dictionary): the design situation fire of SIA 265 4.5.2, `(duration: 60, sides: ("bottom", "left", "right"), wood: none)`: the member becomes its ideal residual section -- d_char,n = beta_n · t (50) with beta_n of Tabelle 13, d_ef = d_char,n + d_red (49), the rectangle reduced by d_ef on each face of `sides` ("bottom", "top", "left", "right"; left and right reduce b, bottom and top h) -- and its design values f_m, f_t,0, f_c,0 and f_v are multiplied by (51)'s 1.8, without k_h; f_c,0,k and E_0,05, which buckling reads, are not. `duration` is the fire resistance in minutes, up to 90 (d_red = 7 mm); `wood` is none for a softwood grade, "beech" or "oak" for a hardwood one (D30), "cladding" for solid timber cladding. With several faces the smaller side must reach 4.5.2.4's minimum width (80 mm for R30, 140 mm for R60). Every verify-* on the member then checks it in the fire situation; the action it is handed is E_d,fi. A rectangle only. none (the default) is the member at normal temperature.
/// - description (bool): false (the default) prints the position's line alone; true also its description text, after an em dash.
/// - axes (str, none): display-only plan axes, e.g. "Achse X3 / Achse YC" (section 5), printed in parentheses after the line.
/// - level (int, auto): 0 prints nothing (the member is still written down), 1 its line, 2 also its section and its design values, 3 also how each is found. auto follows the report. -1 prints only what `shown:` names, each at its own level, beside its line (v0.117).
/// - shown (dictionary, none): at `level: -1`, the variables printed and the level of each, `(A: 2, W_y: 1)` -- 1, 2 or 3: each printed as a line of that level, and none of the others. A key the command does not print is refused naming those it does (lib/shown-variables.json); one it prints only for other arguments is ignored. none at any other level.
/// - title (auto, none, str): the name the line is headed with: auto the member's own, none prints no line, a string replaces the name.
/// -> content
#let member(name, b: auto, h: auto, d: auto, grade: auto, moisture-class: auto, position: auto, impact: false, k-h: true, fire: none, description: false, axes: none, level: auto, shown: none, title: auto) = {
  import "formula.typ": var, var-domain, var-line, val
  let fn = "member"
  if value-type(name) != str or name == "" { panic(fn + ": the name is a non-empty string -- got " + repr(name)) }
  check-shown(fn, level, shown, shown-keys(fn))
  if value-type(description) != bool { panic(fn + ": description is true or false -- got " + repr(description)) }
  let known = known-position-ids()
  let pos = if position == auto { if name in known { name } else { none } } else { position }
  if pos != none and not (value-type(pos) == str and pos in known) { panic(position-refusal(fn, pos)) }
  let record = if pos == none { none } else { load-position(pos) }

  // --- the section: stated in the call, or the position's
  if d != auto and (b != auto or h != auto) { panic(fn + ": d: states a round section and b:, h: a rectangular one -- not both") }
  let held = if record == none { none } else { timber-section-of(pos, record) }
  let sec = if d != auto {
    (shape: "cir", d: timber-mm(fn, "d", d))
  } else if b != auto and h != auto {
    (shape: "rec", b: timber-mm(fn, "b", b), h: timber-mm(fn, "h", h))
  } else if b != auto or h != auto {
    // one side written over: the other is the position's, which it has only as a rectangle
    if pos == none { panic(fn + ": " + repr(name) + " is no position, so both b: and h: are stated in the call") }
    if held.at("shape", default: none) != "rec" { panic(fn + ": position " + pos + " has no b/h to take the other side from -- state both b: and h:") }
    (shape: "rec", b: if b == auto { held.b } else { timber-mm(fn, "b", b) }, h: if h == auto { held.h } else { timber-mm(fn, "h", h) })
  } else if pos == none {
    panic(fn + ": " + repr(name) + " is no position, so its section is stated in the call -- b: and h:, or d:")
  } else { held }
  let sizes = if sec.at("shape", default: none) == "cir" { (sec.d,) } else if sec.at("shape", default: none) == "rec" { (sec.b, sec.h) } else { () }
  if sizes.any(v => v <= 0) { panic(fn + ": a section's sides are positive -- got " + sizes.map(v => repr(v) + " mm").join(", ")) }

  // --- the strength class and the moisture class: stated in the call, or the position's; a position gives none a check can use without that being an error
  let reason = sec.at("reason", default: none)
  let gr = if grade != auto { grade } else if record == none { panic(fn + ": " + repr(name) + " is no position, so its grade: is stated in the call") } else { record.at("strength_class", default: record.at("material", default: "")) }
  let found = timber-grade(gr)
  if found == none {
    let refusal = "strength class " + repr(gr) + " is not one of SIA 265 Tabelle 8 or 9 (" + timber-grade-ids().join(", ") + ")"
    if grade != auto { panic(fn + ": no " + refusal) }
    if reason == none { reason = pos + "'s " + (if gr == "" { "strength class is not stated" } else { refusal }) + ": #member computes timber of SIA 265 Tabelle 8/9 only -- state grade: to write it over" }
  }
  let mc = if moisture-class != auto { moisture-class } else if record == none { panic(fn + ": " + repr(name) + " is no position, so its moisture-class: is stated in the call") } else { record.at("moisture_class", default: none) }
  if moisture-class != auto and not (mc in timber-moisture-ids()) { panic(fn + ": moisture class " + repr(mc) + " -- SIA 265 Tabelle 3 knows " + timber-moisture-ids().map(str).join(", ")) }
  if mc == none and reason == none { reason = pos + " states no moisture class -- state moisture-class: 1, 2 or 3 in the call, or in Woodcore's Positions tab" }

  // the line: the position's, with what the call writes over, or for a member that is no position what it has
  let sec-text = if sec.at("shape", default: none) == "cir" { "Ø\u{a0}" + fmt-decimals(sec.d, 3) + "\u{a0}mm" } else if sec.at("shape", default: none) == "rec" { fmt-decimals(sec.b, 3) + "/" + fmt-decimals(sec.h, 3) + "\u{a0}mm" } else { none }
  let line = if title == none { none } else if pos != none {
    position-line(pos, description: description, axes: axes, name: title,
      grade: if grade != auto { gr } else { auto },
      section: if b != auto or h != auto or d != auto { sec-text } else { auto },
      moisture: if moisture-class != auto { mc } else { auto })
  } else {
    context [*#(if title == auto { name } else { title })*#colon-str() #(gr, sec-text, t-str("moisture_class") + "\u{a0}" + str(mc)).join(", ")#if axes != none [ (#axes)]]
  }

  // --- a member no check can use: written down with why, and printed; nothing is computed
  if reason != none {
    return timber-members.update(m => { m.insert(name, (calculable: false, reason: reason)); m }) + context {
      if level-plan(level, shown).lv >= 1 and line != none { block(above: 1em, below: 0.4em, sticky: true, line) }
    }
  }

  let ch = timber-characteristic(gr)
  if ch == none { panic(fn + ": SIA 265 Anhang B gives no characteristic values for " + gr) }
  let row = found.row
  let glulam = found.family == "glulam"
  // the fire situation (4.5.2, issue #46): the member is its ideal residual section from here on, so A, W, I, i and every check read it
  let fi = timber-fire-of(fn, fire, sec, row, found.family)
  if fi != none { sec = (shape: "rec", b: fi.b, h: fi.h) }
  let round = sec.shape == "cir"
  // the sides a check reads where it needs a width or a height -- a contact width, a sheared width, the radius of gyration its branch is chosen by: a round section's diameter for both
  let (bb, hh) = if round { (sec.d, sec.d) } else { (sec.b, sec.h) }
  let tab-ref = "Tabelle " + found.table.number
  let eta-t = timber-json("eta-t").eta_t
  let kh = timber-clause("k-h")
  let digits = 3

  let meta = (calculable: true, grade: gr, family: found.family, species: row.species, moisture: mc, position: pos, shape: sec.shape, b: bb, h: hh,
    iy: if round { sec.d / 4 } else { hh / calc.sqrt(12) }, iz: if round { sec.d / 4 } else { bb / calc.sqrt(12) },
    impact: impact, table: found.table.number, notes: found.table.notes, row: row, fck: ch.f_c_0_k, fmk: row.f_m_k, E005: ch.E_0_05 * timber-eta-w(mc, "stiffness"), fire: fi != none)
  timber-members.update(m => { m.insert(name, meta); m })

  // a design value of the table, times eta_w and eta_t (2.2.2, 3.3.2.1): its literal, with its unit, in a formula
  let lit(v) = fmt-decimals(v, 6) + " \"N/mm²\""
  let f90 = row.f_c_90_d.generell

  context {
    let plan = level-plan(level, shown, parts: shown-parts("member"))
    let lv = plan.lv
    var-domain(name, {
      // a round section's first line at level 3 is a display fraction, pi d^2 / 4, which reaches above its line box -- Typst does not count that height -- and ran into the member's line 0.4em above it: the rows' own 1em keeps them apart
      if lv >= 1 and line != none { block(above: 1em, below: if round and lv >= 3 { 1em } else { 0.4em }, sticky: true, line) }
      // the fire situation: the duration, the charring, the residual b and h -- which every formula below reads by the names b and h
      if fi != none {
        let fref = fi.clause.norm_ref
        var("t_fi", "t", fi.t, "min", level: plan-at(plan, "t_fi", 3), label: "R" + str(fi.t), norm: "SIA 265", norm-ref: fref, note: "line")
        var("beta_n", "beta_n", fi.beta, "mm/min", level: plan-at(plan, "beta_n", 3), norm: "SIA 265", norm-ref: "Tabelle " + fi.clause.charring.table, note: "line")
        timber-eq("d_char_n", "d_(char,n)", `beta_n dot t_fi`, level: plan-at(plan, "d_char_n", 3), norm: "SIA 265", norm-ref: fi.clause.d_red.norm_ref)
        var("d_red", "d_(red)", fi.d-red, "mm", level: plan-at(plan, "d_red", 3), norm: "SIA 265", norm-ref: fi.clause.d_red.norm_ref, note: "line")
        timber-eq("d_ef", "d_(ef)", `d_char_n + d_red`, level: plan-at(plan, "d_ef", 3), norm: "SIA 265", norm-ref: fi.clause.d_red.norm_ref)
        var("b_0", "b_0", fi.b0, "mm", level: 0)
        var("h_0", "h_0", fi.h0, "mm", level: 0)
        let reduced(base, n) = if n == 0 { base } else if n == 1 { base + " - d_ef" } else { base + " - " + str(n) + " dot d_ef" }
        timber-eq("b", "b_(fi)", reduced("b_0", fi.nb), level: plan-at(plan, "b", 3), norm: "SIA 265", norm-ref: fi.clause.d_red.norm_ref)
        timber-eq("h", "h_(fi)", reduced("h_0", fi.nh), level: plan-at(plan, "h", 3), norm: "SIA 265", norm-ref: fi.clause.d_red.norm_ref)
        var("k_fi", "k_(fi)", fi.factor, level: plan-at(plan, "k_fi", 3), norm: "SIA 265", norm-ref: fi.clause.resistance_factor.norm_ref, note: "line")
        if lv == 1 or lv == 2 {
          set par(justify: false)
          var-line(label: t-str("timber.fire"), norm: "SIA 265", norm-ref: fref, level: 1, {
            val("t_fi", type: "expression", level: 1)
            val("d_ef", type: "expression", level: 1)
            val("b", type: "expression", level: 1)
            val("h", type: "expression", level: 1)
          })
        }
      }
      // the section
      if round {
        var("d", sec.d, "mm", level: 0)
        // d stands for b and h where a check reads a side: a contact width, a sheared width
        var("b", sec.d, "mm", level: 0)
        var("h", sec.d, "mm", level: 0)
        timber-eq("A", `pi dot d^2 / 4`, level: plan-at(plan, "A", 3))
        timber-eq("W_y", `pi dot d^3 / 32`, level: plan-at(plan, "W_y", 3))
        timber-eq("W_z", `W_y`, level: 0)
        timber-eq("I_y", `pi dot d^4 / 64`, level: plan-at(plan, "I_y", 3))
        timber-eq("I_z", `I_y`, level: 0)
        timber-eq("i_y", `d / 4`, level: plan-at(plan, "i_y", 3))
        timber-eq("i_z", `i_y`, level: 0)
        // the torsion of a circle, exact -- mechanics, not the norm, as a rectangle's Saint-Venant series is
        timber-eq("W_t", `pi dot d^3 / 16`, level: plan-at(plan, "W_t", 3), note: "line", descr: "Torsionswiderstand des Kreisquerschnitts, exakt nach der Mechanik.")
      } else {
        if fi == none {
          var("b", bb, "mm", level: 0)
          var("h", hh, "mm", level: 0)
        }
        timber-eq("A", `b dot h`, level: plan-at(plan, "A", 3))
        timber-eq("W_y", `b dot h^2 / 6`, level: plan-at(plan, "W_y", 3))
        timber-eq("W_z", `h dot b^2 / 6`, level: plan-at(plan, "W_z", 3))
        timber-eq("I_y", `b dot h^3 / 12`, level: plan-at(plan, "I_y", 3))
        timber-eq("I_z", `h dot b^3 / 12`, level: plan-at(plan, "I_z", 3))
        timber-eq("i_y", `sqrt(I_y / A)`, level: plan-at(plan, "i_y", 3))
        timber-eq("i_z", `sqrt(I_z / A)`, level: plan-at(plan, "i_z", 3))
        // Saint-Venant's torsion of a rectangle, tau_max = T / (k_tor · a · c²), a the longer side and c the shorter -- mechanics, not the norm, and computed from its series rather than read off a table (timber-torsion-k)
        let (long, short) = if hh >= bb { (hh, bb) } else { (bb, hh) }
        var("k_tor", "k_\"tor\"", timber-torsion-k(long / short), level: plan-at(plan, "k_tor", 3), note: "line", descr: t-str("timber.torsion_coefficient", ratio: fmt-decimals(long / short, 3)))
        if hh >= bb { timber-eq("W_t", `k_tor dot h dot b^2`, level: plan-at(plan, "W_t", 3)) } else { timber-eq("W_t", `k_tor dot b dot h^2`, level: plan-at(plan, "W_t", 3)) }
      }
      // the factors
      var("eta_w", "eta_w", timber-eta-w(mc, "resistance"), level: plan-at(plan, "eta_w", 3), label: t-str("moisture_class") + " " + str(mc), norm: "SIA 265", norm-ref: "Tabelle 4", note: "line")
      var("eta_w_E", "eta_(w,E)", timber-eta-w(mc, "stiffness"), level: plan-at(plan, "eta_w_E", 3), label: t-str("moisture_class") + " " + str(mc) + ", " + tl-str("Steifigkeit"), norm: "SIA 265", norm-ref: "Tabelle 4", note: "line")
      var("eta_t", "eta_t", if impact { eta-t.impact } else { eta-t.normal }, level: plan-at(plan, "eta_t", 3), norm: "SIA 265", norm-ref: "2.2.6", note: "line")
      // k_h, glulam only, a side under 600 mm (3.4.2.3) -- a round section's diameter being both its sides, its one k_h is printed once
      let sides = if round { (("k_h_y", "d", "k_h"),) } else { (("k_h_y", "h", "k_(h,y)"), ("k_h_z", "b", "k_(h,z)")) }
      for (key, side, sym) in sides {
        let v = if side == "b" { bb } else { hh }
        if glulam and k-h and fi == none and v < kh.reference_height {
          timber-eq(key, sym, "min((" + str(kh.reference_height) + " \"mm\" / " + side + ")^" + str(kh.exponent) + ", " + str(kh.maximum) + ")", level: plan-at(plan, key, 3), norm: "SIA 265", norm-ref: if side == "b" { kh.at("norm_ref_z", default: kh.norm_ref) } else { kh.norm_ref })
        } else {
          var(key, sym, 1, level: 0)
        }
      }
      if round { timber-eq("k_h_z", "k_h", `k_h_y`, level: 0) }
      // the design values -- in the fire situation f_m, f_t,0, f_c,0 and f_v times (51)'s k_fi; the values across the grain no fire check reads stay as they are
      let kfi = if fi != none { "k_fi dot " } else { "" }
      timber-eq("f_m_y_d", "f_(m,y,d)", kfi + "k_h_y dot eta_w dot eta_t dot " + lit(row.f_m_d), level: plan-at(plan, "f_m_y_d", 3), norm: "SIA 265", norm-ref: tab-ref)
      if round { timber-eq("f_m_z_d", "f_(m,z,d)", `f_m_y_d`, level: 0) } else { timber-eq("f_m_z_d", "f_(m,z,d)", kfi + "k_h_z dot eta_w dot eta_t dot " + lit(row.f_m_d), level: plan-at(plan, "f_m_z_d", 3), norm: "SIA 265", norm-ref: tab-ref) }
      timber-eq("f_t_0_d", "f_(t,0,d)", kfi + "eta_w dot eta_t dot " + lit(row.f_t_0_d), level: plan-at(plan, "f_t_0_d", 3), norm: "SIA 265", norm-ref: tab-ref)
      timber-eq("f_c_0_d", "f_(c,0,d)", kfi + "eta_w dot eta_t dot " + lit(row.f_c_0_d), level: plan-at(plan, "f_c_0_d", 3), norm: "SIA 265", norm-ref: tab-ref)
      timber-eq("f_t_90_d", "f_(t,90,d)", "eta_w dot eta_t dot " + lit(row.f_t_90_d), level: plan-at(plan, "f_t_90_d", 3), norm: "SIA 265", norm-ref: tab-ref)
      timber-eq("f_c_90_d", "f_(c,90,d)", "eta_w dot eta_t dot " + lit(f90), level: plan-at(plan, "f_c_90_d", 3), norm: "SIA 265", norm-ref: tab-ref)
      timber-eq("f_v_d", "f_(v,d)", kfi + "eta_w dot eta_t dot " + lit(row.f_v_d), level: plan-at(plan, "f_v_d", 3), norm: "SIA 265", norm-ref: tab-ref)
      // what buckling and lateral torsional buckling read: characteristic values, and the stiffness times eta_w (the engineer's rule, v0.88)
      var("f_m_k", "f_(m,k)", row.f_m_k, "N/mm²", level: plan-at(plan, "f_m_k", 3), norm: "SIA 265", norm-ref: tab-ref, note: "line")
      var("f_c_0_k", "f_(c,0,k)", ch.f_c_0_k, "N/mm²", level: plan-at(plan, "f_c_0_k", 3), norm: "SIA 265", norm-ref: "Tabelle " + (if glulam { "48" } else { "47" }), note: "line")
      timber-eq("E_0_05", "E_(0,05)", "eta_w_E dot " + fmt-decimals(ch.E_0_05, 6) + " \"N/mm²\"", level: plan-at(plan, "E_0_05", 3), norm: "SIA 265", norm-ref: "Tabelle " + (if glulam { "48" } else { "47" }))
      // level 2: the same values, two lines -- set ragged, a justified row of values being spread across the line; a round section's W and i are one value about either axis, and said once
      set par(justify: false)
      if lv == 2 {
        var-line(label: "Querschnitt", level: 1, {
          val("A", type: "expression", level: 1)
          val("W_y", type: "expression", level: 1)
          if not round { val("W_z", type: "expression", level: 1) }
          val("i_y", type: "expression", level: 1)
          if not round { val("i_z", type: "expression", level: 1) }
        })
        var-line(label: "Bemessungswerte", norm: "SIA 265", norm-ref: tab-ref, level: 1, {
          val("f_m_y_d", type: "expression", level: 1)
          val("f_t_0_d", type: "expression", level: 1)
          val("f_c_0_d", type: "expression", level: 1)
          val("f_t_90_d", type: "expression", level: 1)
          val("f_c_90_d", type: "expression", level: 1)
          val("f_v_d", type: "expression", level: 1)
        })
      }
    })
  }
}

// --- The checks ----------------------------------------------------------------

// What every check starts with: its domain, the member's values copied into it, and the level it prints at.
#let timber-domain(member, check, name) = if name == auto { member + "-verify-" + check } else { name }

/// Tension, SIA 265 4.2.1: parallel to the grain (6), perpendicular to it (7), or at an angle (8), (9).
///
/// ```typ
/// #member("S001")
/// #verify-tension("S001", N: 25)
/// ```
///
/// ```typ
/// #member("T", b: 100, h: 200, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-tension("T", N: "40 kN", alpha: 30, level: 3)
/// ```
///
/// ```typ
/// #member("T", b: 100, h: 200, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-tension("T", N: "40 kN", alpha: 30, level: -1, shown: (f_t_alpha_d: 3, eta: 1))
/// ```
///
/// The normal force is signed, tension positive: a compression is refused here and checked by `verify-compression`. Its stress is N/A over the member's whole section, which is what 4.2.1.2 asks of a stress perpendicular to the grain -- «in einem gleichmässig beanspruchten Querschnitt».
/// - member (str): a member written down with `#member`.
/// - N (int, float, str, dictionary): the design normal force, tension positive: a number in kN, a value with its unit ("40 kN"), the name of a variable, or a var object.
/// - alpha (int, float): the angle between the force and the grain, in degrees: 0 (6), 90 (7), anything between (8), (9).
/// - level (int, auto): 0 prints nothing (the check is still made, and its results stored), 1 the verdict, 2 also the stress and the relation, 3 also how each value is found. auto follows the report. -1 prints only what `shown:` names, each at its own level, beside the title (v0.117); a verdict is printed where `shown:` names the key of its utilisation (issue #58).
/// - shown (dictionary, none): at `level: -1`, the variables printed and the level of each, `(A: 2, W_y: 1)` -- 1, 2 or 3: each printed as a line of that level, and none of the others. A key the command does not print is refused naming those it does (lib/shown-variables.json); one it prints only for other arguments is ignored. none at any other level. A verdict is named by the key of its utilisation -- `eta`, `eta_s`, `eta_y`… --: at 1 its ratio and value, at 2 or 3 also its numbers, and nothing where `shown:` leaves it out (issue #58).
/// - title (auto, none, str): the check's heading: auto names the check and the member, none prints none, a string replaces it.
/// - name (auto, str): the `var-domain` the check's values are stored in: auto is `"<member>-verify-tension"`.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let verify-tension(member, N: none, alpha: 0, level: auto, shown: none, title: auto, name: auto, unit: auto) = {
  import "formula.typ": var, verify, var-domain
  let fn = "verify-tension"
  check-shown(fn, level, shown, shown-keys(fn))
  timber-check-unit(fn, unit)
  if N == none { panic(fn + ": N: is the design normal force, tension positive") }
  if not (value-type(alpha) in (int, float)) or alpha < 0 or alpha > 90 { panic(fn + ": alpha is the angle between force and grain in degrees, 0 to 90 -- got " + repr(alpha)) }
  let dom = timber-domain(member, "tension", name)
  var-domain(dom, {
    timber-take(member)
    timber-store("N_t_d", "N_(t,d)", N, "kN")
    context {
      let m = timber-member-of(fn, member)
      let d = var-registry.get()
      timber-need(fn, d, "N", N)
      let nv = timber-read(d, "N_t_d")
      if nv < 0 { panic(fn + ": N is " + fmt-decimals(nv, 3) + " -- a compression; tension is positive, and a compression is checked with verify-compression") }
      if alpha == 0 and m.row.at("notes", default: (:)).at("f_t_0_d", default: ()).len() > 0 {
        let notes = m.row.notes.f_t_0_d.map(n => m.notes.at(n, default: "")).filter(s => s.contains("Zugglieder"))
        if notes.len() > 0 { panic(fn + ": " + m.grade + " -- SIA 265 Tabelle " + m.table + ": " + notes.first()) }
      }
      let plan = level-plan(level, shown, parts: shown-parts("verify-tension"))
      let lv = plan.lv
      let (words, ref, eqn) = if alpha == 0 { ("Zug parallel zur Faserrichtung", "4.2.1.1", "(6)") } else if alpha == 90 { ("Zug rechtwinklig zur Faserrichtung", "4.2.1.2", "(7)") } else { ("Zug unter einem Winkel zur Faserrichtung", "4.2.1.3", "(8)") }
      let head = timber-heading(title, words, member)
      if lv >= 1 and head != none { timber-title(head, ref) }
      if lv >= 1 { timber-part(tl-str("Tragsicherheit"), if head != none { none } else { ref }) }
      // N and, at an angle, alpha on one line, as bending sets its actions: two inline #var side by side ran into each other («20 kNα = 10 °»).
      import "formula.typ": var-line
      var-line(level: plan-row(plan, ("N_t_d", "alpha"), 2), {
        var("N_t_d", domain: dom, level: plan-at(plan, "N_t_d", 2))
        if alpha != 0 and alpha != 90 { var("alpha", alpha, "°", level: plan-at(plan, "alpha", 2)) }
      })
      if alpha == 0 {
        timber-eq("sigma_t_0_d", "sigma_(t,0,d)", `N_t_d / A`, level: plan-at(plan, "sigma_t_0_d", 2))
        timber-verdict(plan, "eta", "eta", "sigma_t_0_d / f_t_0_d", unit)
      } else if alpha == 90 {
        timber-eq("sigma_t_90_d", "sigma_(t,90,d)", `N_t_d / A`, level: plan-at(plan, "sigma_t_90_d", 2))
        timber-verdict(plan, "eta", "eta", "sigma_t_90_d / f_t_90_d", unit)
      } else {
        timber-eq("f_t_alpha_d", "f_(t,alpha,d)", `f_t_90_d dot f_t_0_d / (f_t_0_d dot sin(alpha)^2 + f_t_90_d dot cos(alpha)^2)`, level: plan-at(plan, "f_t_alpha_d", 2), norm: "SIA 265", norm-ref: "4.2.1.3")
        timber-eq("sigma_t_alpha_d", "sigma_(t,alpha,d)", `N_t_d / A`, level: plan-at(plan, "sigma_t_alpha_d", 2))
        timber-verdict(plan, "eta", "eta", "sigma_t_alpha_d / f_t_alpha_d", unit)
      }
    }
  })
}

// A value a call gives, known when the call is made: a number in `unit`, a Typst length, a value with its unit or a var object -- converted to mm, or N/mm² for a stress. `none` for the name of a variable, which only the registry can answer.
//
// ⚠️ What a check's branch is decided with. λ_rel depends on the section, the strength class and a length, all known at the call where the length is written out, so the branch of k_c and of k_m is chosen **before** anything is printed -- where reading it back from the registry in a nested `context` cost Typst one more layout pass per check, and a check of bending with lateral torsional buckling did not converge in five (v0.88). Only a length named by a variable of the report is read back.
#let timber-static(x) = {
  let factors = ("mm": 1, "cm": 10, "m": 1000, "N/mm²": 1, "N/mm^2": 1, "MPa": 1, "kN/cm²": 10)
  if value-type(x) in (int, float) { return x }
  if value-type(x) == length { return x.mm() }
  let (v, u) = if value-type(x) == dictionary and "value" in x { (x.value, x.at("unit", default: "")) } else if value-type(x) == str {
    let m = x.match(regex("^\s*([0-9]+(?:\.[0-9]+)?)\s*([^0-9\s].*?)\s*$"))
    if m == none { return none }
    (float(m.captures.at(0)), m.captures.at(1))
  } else { return none }
  let f = factors.at(u, default: none)
  if f == none { none } else { v * f }
}

// A buckling length as `timber-store-lk` stores it, known at the call, in mm, or none.
#let timber-lk-static(spec) = {
  if value-type(spec) == dictionary and "beta" in spec and "base" in spec {
    let base = timber-static(spec.base)
    if base == none { none } else { spec.beta * base }
  } else { timber-static(spec) }
}

// The branch of k_c that holds for `lam`: 1 up to λ_rel = 0.3 (Figur 10), else (30) with (31). Stores k_c_<axis>.
#let timber-kc-branch(axis, lam, plan) = {
  import "formula.typ": var
  let c = timber-clause("buckling")
  let lr = "lambda_rel_" + axis
  if lam != none and lam <= c.lambda_rel_limit {
    var("k_c_" + axis, "k_(c," + axis + ")", 1, level: plan-at(plan, "k_c_" + axis, 2), note: "line", label: t-str("timber.for") + " $lambda_(\"rel\"," + axis + ") <= " + str(c.lambda_rel_limit) + "$", norm: "SIA 265", norm-ref: "4.2.8.2")
  } else {
    timber-eq("k_" + axis, "k_" + axis, str(c.k_factor) + " dot (1 + beta_c dot (" + lr + " - " + str(c.lambda_rel_offset) + ") + " + lr + "^2)", level: plan-at(plan, "k_" + axis, 3), norm: "SIA 265", norm-ref: "4.2.8.2")
    timber-eq("k_c_" + axis, "k_(c," + axis + ")", "1 / (k_" + axis + " + sqrt(k_" + axis + "^2 - " + lr + "^2))", level: plan-at(plan, "k_c_" + axis, 2), norm: "SIA 265", norm-ref: "4.2.8.2")
  }
}

// The guide values of 4.2.8.4 for the geometric slenderness, said where they are exceeded.
#let timber-slender-note(geo, lv) = {
  let c = timber-clause("buckling")
  if lv >= 2 and geo != none and geo > c.slenderness_limits.primary.value {
    timber-note(render-prose(tl-str("Die geometrische Schlankheit übersteigt den Richtwert von 4.2.8.4") + colon-str() + " $lambda <= " + str(c.slenderness_limits.primary.value) + "$ " + tl-str("für Haupttragelemente") + ", $lambda <= " + str(c.slenderness_limits.secondary.value) + "$ " + tl-str("für Verbände und Sekundärelemente") + "."))
  }
}

// Buckling about one axis, 4.2.8: the slenderness, the relative slenderness, k and k_c -- printed as its branch holds (λ_rel ⩽ 0.3 takes k_c = 1). Stores k_c_<axis>. Reads the member's i_<axis>, f_c_0_k, E_0_05 and beta_c; `m` is the member's record, which decides the branch where the length is known at the call.
#let timber-kc(axis, spec, plan, m) = {
  import "formula.typ": var
  let l = "lambda_" + axis
  let lr = "lambda_rel_" + axis
  timber-eq(l, "lambda_" + axis, "l_k_" + axis + " / i_" + axis, level: plan-at(plan, l, 2), norm: "SIA 265", norm-ref: "4.2.8.4")
  timber-eq(lr, "lambda_(rel," + axis + ")", l + " / pi dot sqrt(f_c_0_k / E_0_05)", level: plan-at(plan, lr, 2), norm: "SIA 265", norm-ref: "4.2.8.4")
  let lk = timber-lk-static(spec)
  if lk != none {
    let geo = lk / m.at("i" + axis)
    timber-kc-branch(axis, geo / calc.pi * calc.sqrt(m.fck / m.E005), plan)
    timber-slender-note(geo, plan-at(plan, l, 2))
  } else {
    context {
      let d = var-registry.get()
      timber-kc-branch(axis, timber-read(d, lr), plan)
      timber-slender-note(timber-read(d, l), plan-at(plan, l, 2))
    }
  }
}

// The branch of k_m that holds for `lam`, (39). Stores k_m.
#let timber-km-branch(lam, plan) = {
  import "formula.typ": var
  let c = timber-clause("lateral")
  let (lo, hi) = (c.k_m.lower_bound, c.k_m.upper_bound)
  if lam != none and lam <= lo { var("k_m", "k_m", 1, level: plan-at(plan, "k_m", 2), note: "line", label: t-str("timber.for") + " $lambda_(\"rel\",m) <= " + str(lo) + "$", norm: "SIA 265", norm-ref: "4.2.9.2") }
  else if lam == none or lam <= hi { timber-eq("k_m", "k_m", str(c.k_m.intercept) + " - " + str(c.k_m.slope) + " dot lambda_rel_m", level: plan-at(plan, "k_m", 2), label: t-str("timber.for") + " $" + str(lo) + " < lambda_(\"rel\",m) <= " + str(hi) + "$", norm: "SIA 265", norm-ref: "4.2.9.2") }
  else { timber-eq("k_m", "k_m", "1 / lambda_rel_m^2", level: plan-at(plan, "k_m", 2), label: t-str("timber.for") + " $" + str(hi) + " < lambda_(\"rel\",m)$", norm: "SIA 265", norm-ref: "4.2.9.2") }
}

// The axis a section tips about (D-09): "y" for a rectangle as high as wide or higher, "z" for one wider than high, none for a round one -- as stiff about either axis and stiffer in torsion than any rectangle. member_check.strong_axis's twin.
#let timber-strong(m) = if m.shape == "cir" { none } else if m.b > m.h { "z" } else { "y" }

// Lateral torsional buckling, 4.2.9: sigma_m,crit (41) from a, or as the call gives it, the relative slenderness (40) and k_m (39), printed as its branch holds. Stores k_m. (41) is written for a b × h rectangle bent about y; one wider than high tips about z, and reads h²/(a·b) instead (D-09 of spec 2026-10-12-audit-issues-47-48-49) -- member_check._compute_lateral's twin.
#let timber-km(a, sigma-crit, plan, m) = {
  import "formula.typ": var
  let c = timber-clause("lateral")
  let about-z = timber-strong(m) == "z"
  if sigma-crit != none {
    timber-eq("sigma_m_crit", "sigma_(m,crit)", "sigma_m_crit_given", level: plan-at(plan, "sigma_m_crit", 2), label: "vorgegeben")
  } else {
    timber-eq("sigma_m_crit", "sigma_(m,crit)", str(c.sigma_m_crit_factor) + if about-z { " dot E_0_05 dot h^2 / (a dot b)" } else { " dot E_0_05 dot b^2 / (a dot h)" }, level: plan-at(plan, "sigma_m_crit", 2), norm: "SIA 265", norm-ref: "4.2.9.3")
  }
  timber-eq("lambda_rel_m", "lambda_(rel,m)", `sqrt(f_m_k / sigma_m_crit)`, level: plan-at(plan, "lambda_rel_m", 2), norm: "SIA 265", norm-ref: "4.2.9.3")
  let crit = if sigma-crit != none { timber-static(sigma-crit) } else {
    let aa = timber-static(a)
    let (narrow, deep) = if about-z { (m.h, m.b) } else { (m.b, m.h) }
    if aa == none { none } else { c.sigma_m_crit_factor * m.E005 * narrow * narrow / (aa * deep) }
  }
  if crit != none { timber-km-branch(calc.sqrt(m.fmk / crit), plan) }
  else { context timber-km-branch(timber-read(var-registry.get(), "lambda_rel_m"), plan) }
}

// The buckling lengths a call gives: l_k directly, or beta · l (Euler's cases), per axis.
#let timber-lk(fn, axis, direct, l-axis, l, beta) = {
  if direct != auto { return direct }
  let base = if l-axis != auto { l-axis } else { l }
  if base == auto { return none }
  if not (value-type(beta) in (int, float)) or beta < 0 { panic(fn + ": beta-" + axis + " is the buckling length coefficient, a number -- got " + repr(beta)) }
  (base: base, beta: beta)
}

// Stores l_k_<axis>, either as given or as beta · l printed as a formula.
#let timber-store-lk(axis, spec, plan) = {
  import "formula.typ": var
  if value-type(spec) == dictionary and "beta" in spec and "base" in spec {
    timber-store("l_" + axis, "l_" + axis, spec.base, "mm")
    var("beta_" + axis, "beta_" + axis, spec.beta, level: 0)
    timber-eq("l_k_" + axis, "l_(k," + axis + ")", "beta_" + axis + " dot l_" + axis, level: plan-at(plan, "l_k_" + axis, 2))
  } else {
    timber-store("l_k_" + axis, "l_(k," + axis + ")", spec, "mm")
  }
}

/// Compression parallel to the grain, SIA 265 4.2.2.1 and 4.2.8: the section's own resistance, σ_c,0,d ⩽ f_c,0,d, and apart from it the member's stability -- buckling about both axes, (29) with k_c of (30), (31) and the relative slenderness of (34).
///
/// ```typ
/// #member("S001")
/// #verify-compression("S001", N: -40, l-k-y: 3000, l-k-z: 3000)
/// ```
///
/// ```typ
/// #var("N_d", -60, "kN")
/// #member("S", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-compression("S", N: "N_d", l: 3200, beta-y: 1, beta-z: 0.7, level: 3)
/// ```
///
/// ```typ
/// #member("P", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-compression("P", N: "-60 kN", stability: false, level: 2)
/// ```
///
/// ```typ
/// #member("S", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-compression("S", N: "-60 kN", l: 3200, beta-z: 0.7, level: -1, shown: (sigma_c_0_d: 2, eta_s: 1, lambda_rel_z: 2, k_c_z: 1, eta_z: 2))
/// ```
///
/// The normal force is signed, tension positive: a compression is negative. A buckling length is given directly, `l-k-y:`, or as a system length and a coefficient, `l:` with `beta-y:` (Euler's cases); a length of 0 says the member is held against buckling about that axis, and takes k_c = 1. The relative slenderness is the exact one of (34), with f_c,0,k and E_0,05 of Anhang B -- E_0,05 times eta_w for the stiffness.
/// - member (str): a member written down with `#member`.
/// - N (int, float, str, dictionary): the design normal force, tension positive -- a compression is negative: a number in kN, a value with its unit ("-40 kN"), the name of a variable, or a var object.
/// - l-k-y (auto, int, float, length, str): the buckling length for buckling about y (in the plane of h), in mm, or a length.
/// - l-k-z (auto, int, float, length, str): the buckling length for buckling about z.
/// - l (auto, int, float, length, str): the system length both axes read with their beta, where l-k-* is not given.
/// - l-y (auto, int, float, length, str): the system length about y, where it differs from l.
/// - l-z (auto, int, float, length, str): the system length about z.
/// - beta-y (int, float): the buckling length coefficient about y: 1 pinned-pinned, 2 cantilever, 0.7, 0.5.
/// - beta-z (int, float): likewise about z.
/// - stability (bool): true (the default) also checks buckling about both axes; false checks the section alone, σ_c,0,d ⩽ f_c,0,d -- no buckling length is needed, no «Stabilität» part is printed, and eta is the section's.
/// - level (int, auto): 0 prints nothing (the check is still made, and its results stored), 1 the verdicts, 2 also the stresses, the slenderness and the relations, 3 also how each value is found. auto follows the report. -1 prints only what `shown:` names, each at its own level, beside the title (v0.117); a verdict is printed where `shown:` names the key of its utilisation (issue #58).
/// - shown (dictionary, none): at `level: -1`, the variables printed and the level of each, `(A: 2, W_y: 1)` -- 1, 2 or 3: each printed as a line of that level, and none of the others. A key the command does not print is refused naming those it does (lib/shown-variables.json); one it prints only for other arguments is ignored. none at any other level. A verdict is named by the key of its utilisation -- `eta`, `eta_s`, `eta_y`… --: at 1 its ratio and value, at 2 or 3 also its numbers, and nothing where `shown:` leaves it out (issue #58).
/// - title (auto, none, str): the check's heading: auto names the check and the member, none prints none, a string replaces it.
/// - name (auto, str): the `var-domain` the check's values are stored in: auto is `"<member>-verify-compression"`.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let verify-compression(member, N: none, l-k-y: auto, l-k-z: auto, l: auto, l-y: auto, l-z: auto, beta-y: 1, beta-z: 1, stability: true, level: auto, shown: none, title: auto, name: auto, unit: auto) = {
  import "formula.typ": var, verify, var-domain
  let fn = "verify-compression"
  check-shown(fn, level, shown, shown-keys(fn))
  timber-check-unit(fn, unit)
  if value-type(stability) != bool { panic(fn + ": stability is true or false -- got " + repr(stability)) }
  if N == none { panic(fn + ": N: is the design normal force, tension positive -- a compression is negative") }
  // the section alone needs no buckling length: the lengths are read only where the stability is checked
  let ly = if stability { timber-lk(fn, "y", l-k-y, l-y, l, beta-y) } else { 0 }
  let lz = if stability { timber-lk(fn, "z", l-k-z, l-z, l, beta-z) } else { 0 }
  if stability and (ly == none or lz == none) {
    panic(fn + ": the buckling lengths are needed for both axes -- l-k-y: and l-k-z:, or l: (with beta-y: and beta-z:); 0 says the member is held against buckling about that axis")
  }
  let dom = timber-domain(member, "compression", name)
  var-domain(dom, {
    timber-take(member)
    timber-store("N_c_d", "N_(c,d)", N, "kN", transform: v => -v)
    context {
      let m = timber-member-of(fn, member)
      let d = var-registry.get()
      timber-need(fn, d, "N", N)
      let nv = timber-read(d, "N_c_d")
      if nv < 0 { panic(fn + ": N is " + fmt-decimals(-nv, 3) + " -- a tension; a compression is negative, and a tension is checked with verify-tension") }
      if stability { for (what, spec) in (("buckling length about y", ly), ("buckling length about z", lz)) { timber-need(fn, d, what, if value-type(spec) == dictionary and "beta" in spec { spec.base } else { spec }) } }
      let plan = level-plan(level, shown, parts: shown-parts("verify-compression"))
      let lv = plan.lv
      let head = timber-heading(title, "Druck parallel zur Faserrichtung", member)
      if lv >= 1 and head != none { timber-title(head, "4.2.2.1") }
      // the section
      if lv >= 1 { timber-part(tl-str("Tragsicherheit"), "4.2.2.1") }
      var("N_c_d", domain: dom, level: plan-at(plan, "N_c_d", 2))
      timber-eq("sigma_c_0_d", "sigma_(c,0,d)", `N_c_d / A`, level: plan-at(plan, "sigma_c_0_d", 2))
      timber-verdict(plan, "eta_s", "eta_s", "sigma_c_0_d / f_c_0_d", unit)
      if not stability {
        // the section alone: its utilisation is the check's
        timber-eq("eta", "eta", `eta_s`, unit: timber-eta-unit(unit), level: 0)
      } else {
        // the stability
        if lv >= 1 { timber-part(tl-str("Stabilität"), "4.2.8") }
        var("beta_c", "beta_c", timber-clause("buckling").beta_c.at(timber-family-word(m.family)), level: plan-at(plan, "beta_c", 3), note: "line", norm: "SIA 265", norm-ref: "4.2.8.3")
        for (axis, spec) in (("y", ly), ("z", lz)) {
          if plan-part(plan, "buckling_" + axis, 2) { timber-part(tl-str(if axis == "y" { "Knicken um die y-Achse" } else { "Knicken um die z-Achse" }), none) }
          timber-store-lk(axis, spec, plan)
          timber-kc(axis, spec, plan, m)
          timber-verdict(plan, "eta_" + axis, "eta_(c," + axis + ")", "sigma_c_0_d / (k_c_" + axis + " dot f_c_0_d)", unit)
        }
        timber-eq("eta", "eta", `max(eta_s, eta_y, eta_z)`, unit: timber-eta-unit(unit), level: 0)
      }
    }
  })
}

/// Compression perpendicular to the grain or at an angle to it, SIA 265 4.2.2.2 and 4.2.2.3: (11), or (12) with f_c,α,d of (13) -- a support, a bearing plate, a load on a beam.
///
/// ```typ
/// #member("T001")
/// #verify-compression-perp("T001", F: 18, l: 120)
/// ```
///
/// ```typ
/// #member("T", b: 160, h: 400, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-compression-perp("T", F: "45 kN", l: 150, case: "endauflagerung", alpha: 60, level: 3)
/// ```
///
/// ```typ
/// #member("T", b: 160, h: 400, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-compression-perp("T", F: "45 kN", l: 150, level: -1, shown: (A_c: 3, sigma_c_90_d: 2, eta: 1))
/// ```
///
/// The contact area is l · w, w being the member's width unless the call gives it. Tabellen 8 and 9 give f_c,90,d three ways -- «generell», with at least 100 mm of timber beyond the load on both sides («mit Vorholz»), and at an end support («Endauflagerung») -- and a higher value in brackets where larger indentations provably do not matter (`larger: true`). Anhang C, the alternative to (11), is not built.
/// - member (str): a member written down with `#member`.
/// - F (int, float, str, dictionary): the design force pressing on the area, positive: a number in kN, a value with its unit, the name of a variable, or a var object.
/// - l (int, float, length, str): the contact length along the grain, in mm.
/// - w (auto, int, float, length, str): the contact width; auto is the member's b.
/// - alpha (int, float): the angle between force and grain in degrees: 90 (11), less than 90 (12), (13).
/// - case (str): "generell", "mit_vorholz" or "endauflagerung" -- which f_c,90,d of Tabelle 8 or 9 is read.
/// - larger (bool): the bracketed value of Tabelle 8 note 4 (Tabelle 9 note 3), where the larger indentation provably does not matter.
/// - level (int, auto): 0 prints nothing (the check is still made), 1 the verdict, 2 also the stress and the relation, 3 also how each value is found. auto follows the report. -1 prints only what `shown:` names, each at its own level, beside the title (v0.117); a verdict is printed where `shown:` names the key of its utilisation (issue #58).
/// - shown (dictionary, none): at `level: -1`, the variables printed and the level of each, `(A: 2, W_y: 1)` -- 1, 2 or 3: each printed as a line of that level, and none of the others. A key the command does not print is refused naming those it does (lib/shown-variables.json); one it prints only for other arguments is ignored. none at any other level. A verdict is named by the key of its utilisation -- `eta`, `eta_s`, `eta_y`… --: at 1 its ratio and value, at 2 or 3 also its numbers, and nothing where `shown:` leaves it out (issue #58).
/// - title (auto, none, str): the check's heading.
/// - name (auto, str): the `var-domain` the check's values are stored in: auto is `"<member>-verify-compression-perp"`.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let verify-compression-perp(member, F: none, l: none, w: auto, alpha: 90, case: "generell", larger: false, level: auto, shown: none, title: auto, name: auto, unit: auto) = {
  import "formula.typ": var, verify, var-domain
  let fn = "verify-compression-perp"
  check-shown(fn, level, shown, shown-keys(fn))
  timber-check-unit(fn, unit)
  if F == none { panic(fn + ": F: is the design force pressing on the contact area") }
  if l == none { panic(fn + ": l: is the contact length, in mm") }
  let cases = ("generell", "mit_vorholz", "endauflagerung")
  if not (case in cases) { panic(fn + ": case is one of " + cases.map(repr).join(", ") + " -- got " + repr(case)) }
  if not (value-type(alpha) in (int, float)) or alpha <= 0 or alpha > 90 { panic(fn + ": alpha is the angle between force and grain in degrees, above 0 and up to 90 -- got " + repr(alpha)) }
  let dom = timber-domain(member, "compression-perp", name)
  var-domain(dom, {
    timber-take(member)
    timber-store("F_c_d", "F_(c,90,d)", F, "kN")
    timber-store("l_c", "l", l, "mm")
    if w != auto { timber-store("w_c", "w", w, "mm") }
    context {
      let m = timber-member-of(fn, member)
      let d = var-registry.get()
      timber-need(fn, d, "F", F)
      timber-need(fn, d, "l", l)
      if w != auto { timber-need(fn, d, "w", w) }
      let plan = level-plan(level, shown, parts: shown-parts("verify-compression-perp"))
      let lv = plan.lv
      let cell = m.row.f_c_90_d.at(case)
      let f = if value-type(cell) == dictionary { if larger { cell.at("groessere_eindrueckungen", default: none) } else { cell.value } } else { if larger { none } else { cell } }
      if f == none { panic(fn + ": SIA 265 Tabelle " + m.table + " gives " + m.grade + " no bracketed f_c,90,d for " + repr(case) + " -- leave larger: false") }
      let (words, ref) = if alpha == 90 { ("Druck rechtwinklig zur Faserrichtung", "4.2.2.2") } else { ("Druck unter einem Winkel zur Faserrichtung", "4.2.2.3") }
      let head = timber-heading(title, words, member)
      if lv >= 1 and head != none { timber-title(head, ref) }
      if lv >= 1 { timber-part(tl-str("Tragsicherheit"), if head != none { none } else { ref }) }
      if w == auto { timber-eq("w_c", "w", `b`, level: 0) }
      let case-words = (generell: "generell", mit_vorholz: "mit Vorholz", endauflagerung: "Endauflagerung").at(case)
      timber-eq("f_c_90_d", "f_(c,90,d)", "eta_w dot eta_t dot " + fmt-decimals(f, 6) + " \"N/mm²\"", level: plan-at(plan, "f_c_90_d", 3), label: tl-str(case-words), norm: "SIA 265", norm-ref: "Tabelle " + m.table)
      timber-eq("A_c", "A_c", `l_c dot w_c`, level: plan-at(plan, "A_c", 2))
      if alpha == 90 {
        timber-eq("sigma_c_90_d", "sigma_(c,90,d)", `F_c_d / A_c`, level: plan-at(plan, "sigma_c_90_d", 2))
        timber-verdict(plan, "eta", "eta", "sigma_c_90_d / f_c_90_d", unit)
      } else {
        var("alpha", alpha, "°", level: plan-at(plan, "alpha", 2))
        timber-eq("f_c_alpha_d", "f_(c,alpha,d)", `f_c_90_d dot f_c_0_d / (f_c_0_d dot sin(alpha)^2 + f_c_90_d dot cos(alpha)^2)`, level: plan-at(plan, "f_c_alpha_d", 2), norm: "SIA 265", norm-ref: "4.2.2.3")
        timber-eq("sigma_c_alpha_d", "sigma_(c,alpha,d)", `F_c_d / A_c`, level: plan-at(plan, "sigma_c_alpha_d", 2))
        timber-verdict(plan, "eta", "eta", "sigma_c_alpha_d / f_c_alpha_d", unit)
      }
    }
  })
}

// The largest shear stress of a section under a shear force, at its centroid: 1.5 V/A for a rectangle, 4/3 V/A for a circle -- both mechanics, not the norm: SIA 265 (23) states tau_d <= f_v,d and no factor (read on SIA265-2021-DE p. 33, issue #38). calc/domains/member_check.py writes the same two factors (SHEAR_FACTORS), and tests/test_member_check.py holds the two equal.
#let timber-shear-stress(key, symbol, force, lv, m) = {
  if m.shape == "cir" {
    timber-eq(key, symbol, "4/3 dot " + force + " / A", level: lv, descr: "Grösste Schubspannung eines Kreisquerschnitts nach der Mechanik, 4/3 · V/A, wie 1.5 · V/A für den Rechteckquerschnitt; Gleichung (23) vergleicht sie mit f_v,d.")
  } else {
    timber-eq(key, symbol, "1.5 dot " + force + " / A", level: lv)
  }
}

// The ratios of a sum of stresses over their strengths, (14), (21), (22): only the terms whose action the call gives -- «+ 0 N/mm² / 11.28 N/mm²» said nothing.
#let timber-sum(terms) = terms.filter(t => t != none).join(" + ")

// The bending stresses of a check: sigma_m_y_d and sigma_m_z_d, each only where its moment is given -- a moment not given is 0.
#let timber-bending-stresses(plan, has-y, has-z) = {
  import "formula.typ": var
  if has-y { timber-eq("sigma_m_y_d", "sigma_(m,y,d)", `M_y_d / W_y`, level: plan-at(plan, "sigma_m_y_d", 2)) } else { var("sigma_m_y_d", "sigma_(m,y,d)", 0, "N/mm²", level: 0) }
  if has-z { timber-eq("sigma_m_z_d", "sigma_(m,z,d)", `M_z_d / W_z`, level: plan-at(plan, "sigma_m_z_d", 2)) } else { var("sigma_m_z_d", "sigma_(m,z,d)", 0, "N/mm²", level: 0) }
}

// Whether a check computes lateral torsional buckling: bending about the strong axis, a distance a or a given sigma_m,crit, and a section that can tip.
#let timber-tips(m, a, sigma-crit, has-y, has-z: false) = {
  let axis = timber-strong(m)
  axis != none and (if axis == "y" { has-y } else { has-z }) and (a != none or sigma-crit != none)
}

// The bending term the strong axis's k_m divides, "sigma_m_y_d / (k_m dot f_m_y_d)" or its z twin.
#let timber-km-term(m) = {
  let axis = if timber-strong(m) == "z" { "z" } else { "y" }
  "sigma_m_" + axis + "_d / (k_m dot f_m_" + axis + "_d)"
}

// The line a round member's check prints where lateral torsional buckling would stand.
#let timber-round-note() = timber-note(render-prose(tl-str("Ein Kreisquerschnitt kippt nicht: ein Nachweis nach 4.2.9 entfällt.")))

// The line a rectangle wider than high, bent about y alone, prints there: nothing tips about the weak axis (D-17).
#let timber-weak-note() = timber-note(render-prose(tl-str("Biegung nur um die schwache Achse: ein Nachweis nach 4.2.9 entfällt.")))

// Lateral torsional buckling as a part of a check, or the line saying why it is not checked -- or, for a round section, that it does not apply.
#let timber-lateral-part(plan, a, sigma-crit, has-y, m, has-z: false) = {
  let axis = timber-strong(m)
  if m.shape == "cir" {
    if (has-y or has-z) and plan.lv >= 1 {
      timber-part(tl-str("Stabilität") + " — " + tl-str("Kippen"), "4.2.9")
      timber-round-note()
    }
    return
  }
  if axis == "z" and not has-z {
    if has-y and plan.lv >= 1 {
      timber-part(tl-str("Stabilität") + " — " + tl-str("Kippen"), "4.2.9")
      timber-weak-note()
    }
    return
  }
  if not has-y and axis == "y" { return }
  if a == none and sigma-crit == none {
    if plan.lv >= 1 {
      timber-part(tl-str("Stabilität") + " — " + tl-str("Kippen"), "4.2.9")
      timber-note(render-prose(tl-str("Kippen nicht nachgewiesen: kein Abstand $a$ der Kipphalterungen angegeben.")))
    }
    return
  }
  if plan.lv >= 1 { timber-part(tl-str("Stabilität") + " — " + tl-str("Kippen"), "4.2.9") }
  timber-km(a, sigma-crit, plan, m)
}

/// Bending, SIA 265 4.2.3 and 4.2.9: stresses parallel to the grain about both axes (14), and apart from them the member's stability -- lateral torsional buckling, (38) with k_m of (39) and the relative slenderness of (40), (41) -- or bending perpendicular (15), (16) or at an angle to the grain (17) to (20).
///
/// ```typ
/// #member("T001")
/// #verify-bending("T001", M-y: 4.5, a: 3000)
/// ```
///
/// ```typ
/// #member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-bending("P", M-y: "30 kNm", M-z: 1.2, a: 6000, level: 3)
/// ```
///
/// ```typ
/// #member("R", b: 140, h: 280, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-bending("R", M-y: "18 kNm", M-z: "2 kNm", stability: false, level: 2)
/// ```
///
/// ```typ
/// #member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-bending("P", M-y: "30 kNm", a: 6000, level: -1, shown: (sigma_m_y_d: 2, eta_s: 1, k_m: 2, eta_m: 2))
/// ```
///
/// Lateral torsional buckling reads the moment about the strong axis -- M_y, or M_z where the section is wider than high, (41) then reading h²/(a·b) -- and the distance a between the lateral supports: (41) is the norm's approximation for a constant moment between them; `sigma-m-crit:` gives the critical stress of a finer calculation instead. Without either, the stability is not checked and the report says so; a round section does not tip, nor does a section wider than high bent about y alone, and the report says that instead. `stability: false` checks the section alone -- lateral torsional buckling being a check of its own, as a member check saved in Woodcore makes it. At an angle to the grain (`alpha:`), the stress is M_y/W_y and both sides of the section are checked.
/// - member (str): a member written down with `#member`.
/// - M-y (none, int, float, str, dictionary): the design moment about y (bending in the plane of h): a number in kNm, a value with its unit ("30 kNm"), the name of a variable, or a var object.
/// - M-z (none, int, float, str, dictionary): the design moment about z, likewise.
/// - a (none, int, float, length, str): the distance between the lateral supports (Kipphalterungen), in mm.
/// - sigma-m-crit (none, int, float, str, dictionary): the critical bending stress of a finer calculation, in N/mm², in place of (41).
/// - alpha (int, float): the angle between the bending stress and the grain in degrees: 0 (14), 90 (15), (16), anything between (17) to (20).
/// - stability (bool): true (the default) also checks lateral torsional buckling along the grain (4.2.9), or says why it is not checked; false checks the section alone -- no «Stabilität» part is printed, eta is the section's, and `a:` and `sigma-m-crit:` are refused.
/// - level (int, auto): 0 prints nothing (the check is still made, and its results stored), 1 the verdicts, 2 also the stresses and the relations, 3 also how each value is found. auto follows the report. -1 prints only what `shown:` names, each at its own level, beside the title (v0.117); a verdict is printed where `shown:` names the key of its utilisation (issue #58).
/// - shown (dictionary, none): at `level: -1`, the variables printed and the level of each, `(A: 2, W_y: 1)` -- 1, 2 or 3: each printed as a line of that level, and none of the others. A key the command does not print is refused naming those it does (lib/shown-variables.json); one it prints only for other arguments is ignored. none at any other level. A verdict is named by the key of its utilisation -- `eta`, `eta_s`, `eta_y`… --: at 1 its ratio and value, at 2 or 3 also its numbers, and nothing where `shown:` leaves it out (issue #58).
/// - title (auto, none, str): the check's heading.
/// - name (auto, str): the `var-domain` the check's values are stored in: auto is `"<member>-verify-bending"`.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let verify-bending(member, M-y: none, M-z: none, a: none, sigma-m-crit: none, alpha: 0, stability: true, level: auto, shown: none, title: auto, name: auto, unit: auto) = {
  import "formula.typ": var, verify, var-domain
  let fn = "verify-bending"
  check-shown(fn, level, shown, shown-keys(fn))
  timber-check-unit(fn, unit)
  timber-check-stability(fn, stability, a, sigma-m-crit)
  if M-y == none and M-z == none { panic(fn + ": M-y:, M-z: or both are the design moments") }
  if not (value-type(alpha) in (int, float)) or alpha < 0 or alpha > 90 { panic(fn + ": alpha is the angle between the bending stress and the grain in degrees, 0 to 90 -- got " + repr(alpha)) }
  if alpha != 0 and M-z != none { panic(fn + ": at an angle to the grain (alpha: " + repr(alpha) + ") the check reads M-y alone -- check M-z with alpha: 0") }
  let dom = timber-domain(member, "bending", name)
  let abs-v = v => calc.abs(v)
  var-domain(dom, {
    timber-take(member)
    if M-y != none { timber-store("M_y_d", "M_(y,d)", M-y, "kNm", transform: abs-v) }
    if M-z != none { timber-store("M_z_d", "M_(z,d)", M-z, "kNm", transform: abs-v) }
    if a != none { timber-store("a", "a", a, "mm") }
    if sigma-m-crit != none { timber-store("sigma_m_crit_given", "sigma_(m,crit)", sigma-m-crit, "N/mm²") }
    context {
      let m = timber-member-of(fn, member)
      let d = var-registry.get()
      timber-need(fn, d, "M-y", M-y)
      timber-need(fn, d, "M-z", M-z)
      timber-need(fn, d, "a", a)
      timber-need(fn, d, "sigma-m-crit", sigma-m-crit)
      let plan = level-plan(level, shown, parts: shown-parts("verify-bending"))
      let lv = plan.lv
      let (words, ref) = if alpha == 0 { ("Biegung", "4.2.3.1") } else if alpha == 90 { ("Biegung rechtwinklig zur Faserrichtung", "4.2.3.2") } else { ("Biegung unter einem Winkel zur Faserrichtung", "4.2.3.3") }
      let head = timber-heading(title, words, member)
      if lv >= 1 and head != none { timber-title(head, ref) }
      if lv >= 1 { timber-part(tl-str("Tragsicherheit"), if head != none { none } else { ref }) }
      import "formula.typ": var-line
      var-line(level: plan-row(plan, ("M_y_d", "M_z_d"), 2), {
        if M-y != none { var("M_y_d", domain: dom, level: plan-at(plan, "M_y_d", 2)) }
        if M-z != none { var("M_z_d", domain: dom, level: plan-at(plan, "M_z_d", 2)) }
      })
      if alpha == 0 {
        timber-bending-stresses(plan, M-y != none, M-z != none)
        let sum = timber-sum((if M-y != none { "sigma_m_y_d / f_m_y_d" }, if M-z != none { "sigma_m_z_d / f_m_z_d" }))
        timber-verdict(plan, "eta_s", "eta_s", sum, unit)
        if stability { timber-lateral-part(plan, a, sigma-m-crit, M-y != none, m, has-z: M-z != none) }
        if stability and timber-tips(m, a, sigma-m-crit, M-y != none, has-z: M-z != none) {
          timber-verdict(plan, "eta_m", "eta_m", timber-km-term(m), unit)
          timber-eq("eta", "eta", `max(eta_s, eta_m)`, unit: timber-eta-unit(unit), level: 0)
        } else {
          timber-eq("eta", "eta", `eta_s`, unit: timber-eta-unit(unit), level: 0)
        }
      } else if alpha == 90 {
        timber-eq("sigma_m_90_d", "sigma_(m,90,d)", `M_y_d / W_y`, level: plan-at(plan, "sigma_m_90_d", 2))
        if plan-at(plan, "eta_m_t", 2) >= 2 { timber-part(tl-str("Biegezugseite"), "4.2.3.2") }
        timber-verdict(plan, "eta_m_t", "eta_(m,t)", "sigma_m_90_d / f_t_90_d", unit)
        if plan-at(plan, "eta_m_c", 2) >= 2 { timber-part(tl-str("Biegedruckseite"), "4.2.3.2") }
        timber-verdict(plan, "eta_m_c", "eta_(m,c)", "sigma_m_90_d / f_c_90_d", unit)
        timber-eq("eta", "eta", `max(eta_m_t, eta_m_c)`, unit: timber-eta-unit(unit), level: 0)
      } else {
        var("alpha", alpha, "°", level: plan-at(plan, "alpha", 2))
        timber-eq("sigma_m_alpha_d", "sigma_(m,alpha,d)", `M_y_d / W_y`, level: plan-at(plan, "sigma_m_alpha_d", 2))
        timber-eq("k_mc_alpha", "k_(mc,alpha)", `f_c_90_d / (f_m_y_d dot sin(alpha)^2 + f_c_90_d dot cos(alpha)^2)`, level: plan-at(plan, "k_mc_alpha", 2), norm: "SIA 265", norm-ref: "4.2.3.3")
        timber-eq("k_mt_alpha", "k_(mt,alpha)", `f_t_90_d / (f_m_y_d dot sin(alpha)^2 + f_t_90_d dot cos(alpha)^2)`, level: plan-at(plan, "k_mt_alpha", 2), norm: "SIA 265", norm-ref: "4.2.3.3")
        if plan-at(plan, "eta_m_c", 2) >= 2 { timber-part(tl-str("Biegedruckseite"), "4.2.3.3") }
        timber-verdict(plan, "eta_m_c", "eta_(m,c)", "sigma_m_alpha_d / (k_mc_alpha dot f_m_y_d)", unit)
        if plan-at(plan, "eta_m_t", 2) >= 2 { timber-part(tl-str("Biegezugseite"), "4.2.3.3") }
        timber-verdict(plan, "eta_m_t", "eta_(m,t)", "sigma_m_alpha_d / (k_mt_alpha dot f_m_y_d)", unit)
        timber-eq("eta", "eta", `max(eta_m_t, eta_m_c)`, unit: timber-eta-unit(unit), level: 0)
      }
    }
  })
}

/// Bending with a normal force, SIA 265 4.2.4: with tension, (21), and apart from it lateral torsional buckling (38); with compression, (22), and apart from it the member's stability -- buckling about both axes with the bending of that axis, (37), k_c of 4.2.8 and k_m of 4.2.9.
///
/// ```typ
/// #member("S001")
/// #verify-bending-normal("S001", N: -40, M-y: 5, l-k-y: 3000, l-k-z: 3000, a: 3000)
/// ```
///
/// ```typ
/// #member("Z", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)
/// #verify-bending-normal("Z", N: "35 kN", M-y: "6 kNm", a: 4000, level: 3)
/// ```
///
/// ```typ
/// #member("K", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)
/// #verify-bending-normal("K", N: "-30 kN", M-y: "1.5 kNm", alpha: 10, stability: false, level: 2)
/// ```
///
/// ```typ
/// #member("K", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)
/// #verify-bending-normal("K", N: "-30 kN", M-y: "1.5 kNm", l: 2500, a: 2500, level: -1, shown: (sigma_c_0_d: 2, eta_s: 1, lambda_rel_z: 2, k_c_z: 2, eta_z: 2))
/// ```
///
/// The normal force is signed and chooses the equation: tension positive (21), compression negative (22) with (37). (37) is made for each axis on its own, with the bending about that axis, as 4.2.8.5 allows; k_m, which only the bending about the strong axis needs (y, or z where the section is wider than high), is taken as 1 where no distance a between lateral supports is given, and the report says so. `stability: false` checks the section alone, (21) or (22) -- buckling and lateral torsional buckling being checks of their own, as a member check saved in Woodcore makes them.
///
/// At an angle to the grain (`alpha:` above 0, M_y alone, the section alone), SIA 265 writes neither (21) nor (22): they are applied with the strengths at that angle -- f_t,α,d of (9) or f_c,α,d of (13), f_c,90,d «generell», and k_mt,α or k_mc,α of (19), (20) -- on the side where the normal stress adds to the bending stress, and the other side is checked by (17) or (18) alone, the normal force's relief not counted; eta is the larger. That is the engineer's reading (08.10.2026), and the page says so.
/// - member (str): a member written down with `#member`.
/// - N (int, float, str, dictionary): the design normal force, tension positive: a number in kN, a value with its unit, the name of a variable, or a var object.
/// - M-y (none, int, float, str, dictionary): the design moment about y, in kNm.
/// - M-z (none, int, float, str, dictionary): the design moment about z, in kNm -- along the grain only.
/// - alpha (int, float): the angle between the member's axis and the grain in degrees, 0 to 90; above 0 the check needs `stability: false` and reads M-y alone.
/// - stability (bool): true (the default) also checks the member's stability -- lateral torsional buckling with a tension, buckling with a compression; false checks the section alone: no buckling length is read, no «Stabilität» part is printed, eta is the section's, and `a:` and `sigma-m-crit:` are refused.
/// - l-k-y (auto, int, float, length, str): the buckling length about y, in mm (compression only).
/// - l-k-z (auto, int, float, length, str): the buckling length about z (compression only).
/// - l (auto, int, float, length, str): the system length, read with beta-y and beta-z where l-k-* is not given.
/// - l-y (auto, int, float, length, str): the system length about y, where it differs from l.
/// - l-z (auto, int, float, length, str): the system length about z.
/// - beta-y (int, float): the buckling length coefficient about y.
/// - beta-z (int, float): likewise about z.
/// - a (none, int, float, length, str): the distance between the lateral supports, in mm, for k_m.
/// - sigma-m-crit (none, int, float, str, dictionary): the critical bending stress of a finer calculation, in N/mm², in place of (41).
/// - level (int, auto): 0 prints nothing (the check is still made, and its results stored), 1 the verdicts, 2 also the stresses and the relations, 3 also how each value is found. auto follows the report. -1 prints only what `shown:` names, each at its own level, beside the title (v0.117); a verdict is printed where `shown:` names the key of its utilisation (issue #58).
/// - shown (dictionary, none): at `level: -1`, the variables printed and the level of each, `(A: 2, W_y: 1)` -- 1, 2 or 3: each printed as a line of that level, and none of the others. A key the command does not print is refused naming those it does (lib/shown-variables.json); one it prints only for other arguments is ignored. none at any other level. A verdict is named by the key of its utilisation -- `eta`, `eta_s`, `eta_y`… --: at 1 its ratio and value, at 2 or 3 also its numbers, and nothing where `shown:` leaves it out (issue #58).
/// - title (auto, none, str): the check's heading.
/// - name (auto, str): the `var-domain` the check's values are stored in: auto is `"<member>-verify-bending-normal"`.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let verify-bending-normal(member, N: none, M-y: none, M-z: none, alpha: 0, l-k-y: auto, l-k-z: auto, l: auto, l-y: auto, l-z: auto, beta-y: 1, beta-z: 1, a: none, sigma-m-crit: none, stability: true, level: auto, shown: none, title: auto, name: auto, unit: auto) = {
  import "formula.typ": var, verify, var-domain
  let fn = "verify-bending-normal"
  check-shown(fn, level, shown, shown-keys(fn))
  timber-check-unit(fn, unit)
  timber-check-stability(fn, stability, a, sigma-m-crit)
  if N == none { panic(fn + ": N: is the design normal force, tension positive -- without one, check verify-bending") }
  if M-y == none and M-z == none { panic(fn + ": M-y:, M-z: or both are the design moments -- without one, check verify-tension or verify-compression") }
  if not (value-type(alpha) in (int, float)) or alpha < 0 or alpha > 90 { panic(fn + ": alpha is the angle between the member's axis and the grain in degrees, 0 to 90 -- got " + repr(alpha)) }
  if alpha != 0 and M-z != none { panic(fn + ": at an angle to the grain (alpha: " + repr(alpha) + ") the check reads M-y alone -- check M-z with alpha: 0") }
  if alpha != 0 and M-y == none { panic(fn + ": at an angle to the grain (alpha: " + repr(alpha) + ") M-y: is the design moment") }
  if alpha != 0 and stability { panic(fn + ": at an angle to the grain (alpha: " + repr(alpha) + ") the check is the section's alone -- give stability: false") }
  // the section alone needs no buckling length: the lengths are read only where the stability is checked
  let ly = if stability { timber-lk(fn, "y", l-k-y, l-y, l, beta-y) } else { 0 }
  let lz = if stability { timber-lk(fn, "z", l-k-z, l-z, l, beta-z) } else { 0 }
  let dom = timber-domain(member, "bending-normal", name)
  let abs-v = v => calc.abs(v)
  var-domain(dom, {
    timber-take(member)
    timber-store("N_d", "N_d", N, "kN")
    if M-y != none { timber-store("M_y_d", "M_(y,d)", M-y, "kNm", transform: abs-v) }
    if M-z != none { timber-store("M_z_d", "M_(z,d)", M-z, "kNm", transform: abs-v) }
    if a != none { timber-store("a", "a", a, "mm") }
    if sigma-m-crit != none { timber-store("sigma_m_crit_given", "sigma_(m,crit)", sigma-m-crit, "N/mm²") }
    context {
      let m = timber-member-of(fn, member)
      let d = var-registry.get()
      timber-need(fn, d, "N", N)
      timber-need(fn, d, "M-y", M-y)
      timber-need(fn, d, "M-z", M-z)
      timber-need(fn, d, "a", a)
      timber-need(fn, d, "sigma-m-crit", sigma-m-crit)
      let nv = timber-read(d, "N_d")
      if nv == 0 { panic(fn + ": N is 0 -- check verify-bending") }
      let tension = nv > 0
      if stability and not tension and (ly == none or lz == none) {
        panic(fn + ": with a compression, the buckling lengths are needed for both axes -- l-k-y: and l-k-z:, or l: (with beta-y: and beta-z:); 0 says the member is held against buckling about that axis")
      }
      if stability and not tension { for (what, spec) in (("buckling length about y", ly), ("buckling length about z", lz)) { timber-need(fn, d, what, if value-type(spec) == dictionary and "beta" in spec { spec.base } else { spec }) } }
      let plan = level-plan(level, shown, parts: shown-parts("verify-bending-normal"))
      let lv = plan.lv
      let has-y = M-y != none
      let has-z = M-z != none
      let (words, ref) = if alpha != 0 {
        if tension { ("Biegung mit Zug unter einem Winkel zur Faserrichtung", "4.2.4.1") } else { ("Biegung mit Druck unter einem Winkel zur Faserrichtung", "4.2.4.2") }
      } else if tension { ("Biegung mit Zug", "4.2.4.1") } else { ("Biegung mit Druck", "4.2.4.2") }
      let head = timber-heading(title, words, member)
      if lv >= 1 and head != none { timber-title(head, ref) }
      if lv >= 1 { timber-part(tl-str("Tragsicherheit"), if head != none { none } else { ref }) }
      if alpha != 0 {
        // (21) or (22) at an angle: the strengths at that angle, (9) or (13) and (19), (20); the side where N adds in interaction, the other by (17) or (18) alone -- the engineer's reading, said on the page
        if lv >= 1 { timber-note(render-prose(tl-str("SIA 265 gibt (21) und (22) nur in Faserrichtung an: unter dem Winkel $alpha$ werden $f_(t,alpha,d)$ nach (9) bzw. $f_(c,alpha,d)$ nach (13) und $k_(\"mt\",alpha)$, $k_(\"mc\",alpha)$ nach (19), (20) eingesetzt, auf der Seite, auf der sich die Normalspannung zur Biegespannung addiert; die andere Seite wird nach (17) bzw. (18) allein nachgewiesen."))) }
        var("alpha", alpha, "°", level: plan-at(plan, "alpha", 2))
        var("M_y_d", domain: dom, level: 0)
        if tension {
          timber-eq("N_t_d", "N_(t,d)", `N_d`, level: plan-at(plan, "N_t_d", 2))
          timber-eq("sigma_t_alpha_d", "sigma_(t,alpha,d)", `N_t_d / A`, level: plan-at(plan, "sigma_t_alpha_d", 2))
          timber-eq("f_t_alpha_d", "f_(t,alpha,d)", `f_t_90_d dot f_t_0_d / (f_t_0_d dot sin(alpha)^2 + f_t_90_d dot cos(alpha)^2)`, level: plan-at(plan, "f_t_alpha_d", 2), norm: "SIA 265", norm-ref: "4.2.1.3")
        } else {
          timber-eq("N_c_d", "N_(c,d)", `abs(N_d)`, level: plan-at(plan, "N_c_d", 2))
          timber-eq("sigma_c_alpha_d", "sigma_(c,alpha,d)", `N_c_d / A`, level: plan-at(plan, "sigma_c_alpha_d", 2))
          timber-eq("f_c_alpha_d", "f_(c,alpha,d)", `f_c_90_d dot f_c_0_d / (f_c_0_d dot sin(alpha)^2 + f_c_90_d dot cos(alpha)^2)`, level: plan-at(plan, "f_c_alpha_d", 2), norm: "SIA 265", norm-ref: "4.2.2.3")
        }
        timber-eq("sigma_m_alpha_d", "sigma_(m,alpha,d)", `M_y_d / W_y`, level: plan-at(plan, "sigma_m_alpha_d", 2))
        timber-eq("k_mc_alpha", "k_(mc,alpha)", `f_c_90_d / (f_m_y_d dot sin(alpha)^2 + f_c_90_d dot cos(alpha)^2)`, level: plan-at(plan, "k_mc_alpha", 2), norm: "SIA 265", norm-ref: "4.2.3.3")
        timber-eq("k_mt_alpha", "k_(mt,alpha)", `f_t_90_d / (f_m_y_d dot sin(alpha)^2 + f_t_90_d dot cos(alpha)^2)`, level: plan-at(plan, "k_mt_alpha", 2), norm: "SIA 265", norm-ref: "4.2.3.3")
        if tension {
          if plan-at(plan, "eta_m_t", 2) >= 2 { timber-part(tl-str("Biegezugseite"), "4.2.4.1") }
          let sum = "sigma_t_alpha_d / f_t_alpha_d + sigma_m_alpha_d / (k_mt_alpha dot f_m_y_d)"
          timber-verdict(plan, "eta_m_t", "eta_(m,t)", sum, unit)
          if plan-at(plan, "eta_m_c", 2) >= 2 { timber-part(tl-str("Biegedruckseite"), "4.2.3.3") }
          timber-verdict(plan, "eta_m_c", "eta_(m,c)", "sigma_m_alpha_d / (k_mc_alpha dot f_m_y_d)", unit)
        } else {
          if plan-at(plan, "eta_m_c", 2) >= 2 { timber-part(tl-str("Biegedruckseite"), "4.2.4.2") }
          let sum = "(sigma_c_alpha_d / f_c_alpha_d)^2 + sigma_m_alpha_d / (k_mc_alpha dot f_m_y_d)"
          timber-verdict(plan, "eta_m_c", "eta_(m,c)", sum, unit)
          if plan-at(plan, "eta_m_t", 2) >= 2 { timber-part(tl-str("Biegezugseite"), "4.2.3.3") }
          timber-verdict(plan, "eta_m_t", "eta_(m,t)", "sigma_m_alpha_d / (k_mt_alpha dot f_m_y_d)", unit)
        }
        timber-eq("eta", "eta", `max(eta_m_t, eta_m_c)`, unit: timber-eta-unit(unit), level: 0)
      } else {
      if tension {
        timber-eq("N_t_d", "N_(t,d)", `N_d`, level: plan-at(plan, "N_t_d", 2))
        timber-eq("sigma_t_0_d", "sigma_(t,0,d)", `N_t_d / A`, level: plan-at(plan, "sigma_t_0_d", 2))
      } else {
        timber-eq("N_c_d", "N_(c,d)", `abs(N_d)`, level: plan-at(plan, "N_c_d", 2))
        timber-eq("sigma_c_0_d", "sigma_(c,0,d)", `N_c_d / A`, level: plan-at(plan, "sigma_c_0_d", 2))
      }
      if has-y { var("M_y_d", domain: dom, level: 0) }
      if has-z { var("M_z_d", domain: dom, level: 0) }
      timber-bending-stresses(plan, has-y, has-z)
      if tension {
        let sum = timber-sum(("sigma_t_0_d / f_t_0_d", if has-y { "sigma_m_y_d / f_m_y_d" }, if has-z { "sigma_m_z_d / f_m_z_d" }))
        timber-verdict(plan, "eta_s", "eta_s", sum, unit)
        if stability { timber-lateral-part(plan, a, sigma-m-crit, has-y, m, has-z: has-z) }
        if stability and timber-tips(m, a, sigma-m-crit, has-y, has-z: has-z) {
          timber-verdict(plan, "eta_m", "eta_m", timber-km-term(m), unit)
          timber-eq("eta", "eta", `max(eta_s, eta_m)`, unit: timber-eta-unit(unit), level: 0)
        } else {
          timber-eq("eta", "eta", `eta_s`, unit: timber-eta-unit(unit), level: 0)
        }
      } else if not stability {
        // the section alone: (22), buckling and lateral torsional buckling being checks of their own
        let sum = timber-sum(("(sigma_c_0_d / f_c_0_d)^2", if has-y { "sigma_m_y_d / f_m_y_d" }, if has-z { "sigma_m_z_d / f_m_z_d" }))
        timber-verdict(plan, "eta_s", "eta_s", sum, unit)
        timber-eq("eta", "eta", `eta_s`, unit: timber-eta-unit(unit), level: 0)
      } else {
        let sum = timber-sum(("(sigma_c_0_d / f_c_0_d)^2", if has-y { "sigma_m_y_d / f_m_y_d" }, if has-z { "sigma_m_z_d / f_m_z_d" }))
        timber-verdict(plan, "eta_s", "eta_s", sum, unit)
        if lv >= 1 { timber-part(tl-str("Stabilität"), "4.2.8.5") }
        var("beta_c", "beta_c", timber-clause("buckling").beta_c.at(timber-family-word(m.family)), level: plan-at(plan, "beta_c", 3), note: "line", norm: "SIA 265", norm-ref: "4.2.8.3")
        // k_m, for the bending about the strong axis -- y, or z where b > h (D-09)
        let strong = timber-strong(m)
        if timber-tips(m, a, sigma-m-crit, has-y, has-z: has-z) {
          if plan-part(plan, "lateral", 2) { timber-part(tl-str("Kippen"), "4.2.9") }
          timber-km(a, sigma-m-crit, plan, m)
        } else {
          var("k_m", "k_m", 1, level: 0)
          if lv >= 1 {
            if strong == none { if has-y or has-z { timber-round-note() } }
            else if strong == "z" and not has-z { if has-y { timber-weak-note() } }
            else if (strong == "y" and has-y) or (strong == "z" and has-z) { timber-note(render-prose(tl-str("Kippen nicht nachgewiesen: kein Abstand $a$ der Kipphalterungen angegeben."))) }
          }
        }
        let km-axis = if strong == "z" { "z" } else { "y" }
        for (axis, spec) in (("y", ly), ("z", lz)) {
          if plan-part(plan, "buckling_" + axis, 2) { timber-part(tl-str(if axis == "y" { "Knicken um die y-Achse" } else { "Knicken um die z-Achse" }), "4.2.8.5") }
          timber-store-lk(axis, spec, plan)
          timber-kc(axis, spec, plan, m)
          let has-axis = if axis == "y" { has-y } else { has-z }
          let bend = if not has-axis { none } else if axis == km-axis { "sigma_m_" + axis + "_d / (k_m dot f_m_" + axis + "_d)" } else { "sigma_m_" + axis + "_d / f_m_" + axis + "_d" }
          let sum = timber-sum(("sigma_c_0_d / (k_c_" + axis + " dot f_c_0_d)", bend))
          timber-verdict(plan, "eta_" + axis, "eta_(c," + axis + ")", sum, unit)
        }
        timber-eq("eta", "eta", `max(eta_s, eta_y, eta_z)`, unit: timber-eta-unit(unit), level: 0)
      }
      }
    }
  })
}

/// Shear and torsion, SIA 265 4.2.5: the shear stress against f_v,d (23) -- 1.5 V/A for a rectangle and 4/3 V/A for a round section, which is mechanics --, the torsional stress T/W_t (24), and the two together (25).
///
/// ```typ
/// #member("T001")
/// #verify-shear("T001", V: 12)
/// ```
///
/// ```typ
/// #member("R", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)
/// #verify-shear("R", V: "15 kN", T: "0.6 kNm", level: 3)
/// ```
///
/// ```typ
/// #member("R", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)
/// #verify-shear("R", V: "15 kN", V-y: "4 kN", level: -1, shown: (V_z_d: 2, tau_d: 3, eta: 3))
/// ```
///
/// V is the shear force in the plane of h (z), V-y the one in the plane of b; both give their largest stress at the centroid, where they add as vectors. W_t is the one `#member` stores: Saint-Venant's for a rectangle, computed from its series, and π·d³/16 for a round section. A solid-timber member cut from the pith (Markstück) takes half of f_v,d (Tabelle 8 note 6, `pith: true`); a glulam's keeps it, Tabelle 9 having no such note, and the report says so.
/// - member (str): a member written down with `#member`.
/// - V (none, int, float, str, dictionary): the design shear force in the plane of h, in kN.
/// - V-y (none, int, float, str, dictionary): the design shear force in the plane of b, in kN.
/// - T (none, int, float, str, dictionary): the design torsional moment, in kNm.
/// - pith (bool): a member cut from the pith: f_v,d is halved for solid timber (Tabelle 8 note 6), not for glulam.
/// - level (int, auto): 0 prints nothing (the check is still made), 1 the verdict, 2 also the stresses and the relations, 3 also how each value is found. auto follows the report. -1 prints only what `shown:` names, each at its own level, beside the title (v0.117); a verdict is printed where `shown:` names the key of its utilisation (issue #58).
/// - shown (dictionary, none): at `level: -1`, the variables printed and the level of each, `(V_z_d: 2, tau_d: 3, eta: 1)` -- 1, 2 or 3: each printed as a line of that level, and none of the others; the verdict is `eta`, printed only where it is named (issue #58). A key the command does not print is refused naming those it does (lib/shown-variables.json); one it prints only for other arguments is ignored. none at any other level.
/// - title (auto, none, str): the check's heading.
/// - name (auto, str): the `var-domain` the check's values are stored in: auto is `"<member>-verify-shear"`.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let verify-shear(member, V: none, V-y: none, T: none, pith: false, level: auto, shown: none, title: auto, name: auto, unit: auto) = {
  import "formula.typ": var, verify, var-domain
  let fn = "verify-shear"
  check-shown(fn, level, shown, shown-keys(fn))
  timber-check-unit(fn, unit)
  if V == none and V-y == none and T == none { panic(fn + ": V:, V-y:, T: or several are the design actions") }
  let dom = timber-domain(member, "shear", name)
  let abs-v = v => calc.abs(v)
  var-domain(dom, {
    timber-take(member)
    if V != none { timber-store("V_z_d", "V_(z,d)", V, "kN", transform: abs-v) }
    if V-y != none { timber-store("V_y_d", "V_(y,d)", V-y, "kN", transform: abs-v) }
    if T != none { timber-store("T_d", "T_d", T, "kNm", transform: abs-v) }
    context {
      let m = timber-member-of(fn, member)
      let d = var-registry.get()
      timber-need(fn, d, "V", V)
      timber-need(fn, d, "V-y", V-y)
      timber-need(fn, d, "T", T)
      let plan = level-plan(level, shown, parts: shown-parts(fn))
      let lv = plan.lv
      let has-v = V != none or V-y != none
      let (words, ref) = if has-v and T != none { ("Schub und Torsion", "4.2.5.3") } else if T != none { ("Torsion", "4.2.5.2") } else { ("Schub", "4.2.5.1") }
      let head = timber-heading(title, words, member)
      if lv >= 1 and head != none { timber-title(head, ref) }
      if lv >= 1 { timber-part(tl-str("Tragsicherheit"), if head != none { none } else { ref }) }
      // Tabelle 8 note 6 halves f_v,d of solid timber cut from the pith; Tabelle 9 has no such note, and a glulam's pith is said and not applied (D-02 of spec 2026-10-12-audit-issues-47-48-49)
      let halved = pith and m.family != "glulam"
      if halved { timber-eq("f_v_d_p", "f_(v,d)", `f_v_d / 2`, level: plan-at(plan, "f_v_d_p", 2), label: "Markstück", norm: "SIA 265", norm-ref: "Tabelle 8, Anm. 6") }
      if pith and not halved and lv >= 1 { timber-note(render-prose(tl-str("Markstück: SIA 265 halbiert $f_(v,d)$ nach Tabelle 8, Anmerkung 6, nur für Vollholz; für Brettschichtholz (Tabelle 9) wird $f_(v,d)$ nicht abgemindert."))) }
      let fv = if halved { "f_v_d_p" } else { "f_v_d" }
      let keys = ()
      if V != none { var("V_z_d", domain: dom, level: plan-at(plan, "V_z_d", 2)); timber-shear-stress("tau_z_d", "tau_(z,d)", "V_z_d", plan-at(plan, "tau_z_d", 2), m); keys.push("tau_z_d") }
      if V-y != none { var("V_y_d", domain: dom, level: plan-at(plan, "V_y_d", 2)); timber-shear-stress("tau_y_d", "tau_(y,d)", "V_y_d", plan-at(plan, "tau_y_d", 2), m); keys.push("tau_y_d") }
      if keys.len() == 2 { timber-eq("tau_d", "tau_d", `sqrt(tau_z_d^2 + tau_y_d^2)`, level: plan-at(plan, "tau_d", 2)) }
      else if keys.len() == 1 { timber-eq("tau_d", "tau_d", keys.first(), level: 0) }
      if has-v and T == none {
        timber-verdict(plan, "eta", "eta", "tau_d / " + fv, unit)
      } else {
        var("T_d", domain: dom, level: plan-at(plan, "T_d", 2))
        timber-eq("tau_tor_d", "tau_(tor,d)", `T_d / W_t`, level: plan-at(plan, "tau_tor_d", 2))
        if not has-v {
          timber-verdict(plan, "eta", "eta", "tau_tor_d / " + fv, unit)
        } else {
          timber-verdict(plan, "eta", "eta", "tau_tor_d / " + fv + " + (tau_d / " + fv + ")^2", unit)
        }
      }
    }
  })
}

/// Abscheren, SIA 265 4.2.6: the shear stress over a sheared area, against a reduced f_v,d -- 0.6 f_v,d for solid timber (26), 0.8 f_v,d for glulam (27) -- and only where the sheared length is at least 150 mm.
///
/// ```typ
/// #member("T001")
/// #verify-shear-off("T001", F: 20, l: 200)
/// ```
///
/// ```typ
/// #member("G", b: 160, h: 320, grade: "GL24h", moisture-class: 1, level: 0)
/// #verify-shear-off("G", F: "45 kN", l: 250, w: 120, level: 3)
/// ```
///
/// The sheared area is l · w along the grain -- the Vorholz of a step joint, the timber in front of a notch -- w being the member's width unless the call gives it. A length under the norm's 150 mm does not count at all, which the check says with a ✘ of its own.
/// - member (str): a member written down with `#member`.
/// - F (int, float, str, dictionary): the design force sheared off, in kN.
/// - l (int, float, length, str): the sheared length along the grain, in mm.
/// - w (auto, int, float, length, str): the sheared width; auto is the member's b.
/// - level (int, auto): 0 prints nothing (the check is still made), 1 the verdict, 2 also the stress and the relation, 3 also how each value is found. auto follows the report.
/// - title (auto, none, str): the check's heading.
/// - name (auto, str): the `var-domain` the check's values are stored in: auto is `"<member>-verify-shear-off"`.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let verify-shear-off(member, F: none, l: none, w: auto, level: auto, title: auto, name: auto, unit: auto) = {
  import "formula.typ": var, verify, var-domain
  let fn = "verify-shear-off"
  timber-check-level(fn, level)
  timber-check-unit(fn, unit)
  if F == none { panic(fn + ": F: is the design force sheared off") }
  if l == none { panic(fn + ": l: is the sheared length along the grain, in mm") }
  let dom = timber-domain(member, "shear-off", name)
  var-domain(dom, {
    timber-take(member)
    timber-store("F_a_d", "F_(a,d)", F, "kN", transform: v => calc.abs(v))
    timber-store("l_a", "l_a", l, "mm")
    if w != auto { timber-store("w_a", "w_a", w, "mm") }
    context {
      let m = timber-member-of(fn, member)
      let d = var-registry.get()
      timber-need(fn, d, "F", F)
      timber-need(fn, d, "l", l)
      if w != auto { timber-need(fn, d, "w", w) }
      let c = timber-clause("shear-off")
      let plan = level-plan(level, none)
      let lv = plan.lv
      let at2 = timber-sub(lv, 2)
      let head = timber-heading(title, "Abscheren", member)
      if lv >= 1 and head != none { timber-title(head, "4.2.6") }
      if lv >= 1 { timber-part(tl-str("Tragsicherheit"), if head != none { none } else { "4.2.6" }) }
      if w == auto { timber-eq("w_a", "w_a", `b`, level: 0) }
      var("l_a", domain: dom, level: at2)
      if lv >= 1 { block(above: 0.6em, below: 0.6em, verify("l_a >= " + str(c.min_shear_length) + " \"mm\"", level: 3)) } else { verify("l_a >= " + str(c.min_shear_length) + " \"mm\"", level: 0) }
      timber-eq("tau_a_d", "tau_(a,d)", `F_a_d / (l_a dot w_a)`, level: at2)
      var("k_a", "k_a", c.factor.at(timber-family-word(m.family)), level: 0)
      timber-verdict(plan, "eta", "eta", "tau_a_d / (" + str(c.factor.at(timber-family-word(m.family))) + " dot f_v_d)", unit)
    }
  })
}

/// Shear with a stress perpendicular to the grain, SIA 265 4.2.7.1: (28), with k_t,90 = 1 under transverse tension and 4 under transverse compression.
///
/// ```typ
/// #member("T001")
/// #verify-shear-perp("T001", V: 12, sigma-90: -1.2)
/// ```
///
/// ```typ
/// #member("R", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)
/// #verify-shear-perp("R", tau: "0.9 N/mm²", sigma-90: "0.05 N/mm²", level: 3)
/// ```
///
/// The shear stress is 1.5 V/A -- 4/3 V/A for a round section --, or given with `tau:`; the stress perpendicular to the grain is signed, transverse tension positive, and lies between −f_c,90,d and f_t,90,d. 4.2.7.2, which drops the loads near a support from the shear check, is not to be applied with it -- the call chooses one or the other.
/// - member (str): a member written down with `#member`.
/// - V (none, int, float, str, dictionary): the design shear force in the plane of h, in kN.
/// - tau (none, int, float, str, dictionary): the design shear stress, in N/mm², in place of V.
/// - sigma-90 (int, float, str, dictionary): the design stress perpendicular to the grain, in N/mm², transverse tension positive.
/// - level (int, auto): 0 prints nothing (the check is still made), 1 the verdict, 2 also the stresses and the relation, 3 also how each value is found. auto follows the report.
/// - title (auto, none, str): the check's heading.
/// - name (auto, str): the `var-domain` the check's values are stored in: auto is `"<member>-verify-shear-perp"`.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let verify-shear-perp(member, V: none, tau: none, sigma-90: none, level: auto, title: auto, name: auto, unit: auto) = {
  import "formula.typ": var, verify, var-domain
  let fn = "verify-shear-perp"
  timber-check-level(fn, level)
  timber-check-unit(fn, unit)
  if (V == none) == (tau == none) { panic(fn + ": V: or tau: -- one of the two gives the shear stress") }
  if sigma-90 == none { panic(fn + ": sigma-90: is the stress perpendicular to the grain, transverse tension positive") }
  let dom = timber-domain(member, "shear-perp", name)
  var-domain(dom, {
    timber-take(member)
    if V != none { timber-store("V_z_d", "V_(z,d)", V, "kN", transform: v => calc.abs(v)) }
    if tau != none { timber-store("tau_d", "tau_d", tau, "N/mm²", transform: v => calc.abs(v)) }
    timber-store("sigma_90_d", "sigma_(90,d)", sigma-90, "N/mm²")
    context {
      let m = timber-member-of(fn, member)
      let d = var-registry.get()
      timber-need(fn, d, "V", V)
      timber-need(fn, d, "tau", tau)
      timber-need(fn, d, "sigma-90", sigma-90)
      let c = timber-clause("shear-perp")
      let s = timber-read(d, "sigma_90_d")
      let plan = level-plan(level, none)
      let lv = plan.lv
      let at2 = timber-sub(lv, 2)
      let head = timber-heading(title, "Schub und Normalkraft rechtwinklig zur Faserrichtung", member)
      if lv >= 1 and head != none { timber-title(head, "4.2.7.1") }
      if lv >= 1 { timber-part(tl-str("Tragsicherheit"), if head != none { none } else { "4.2.7.1" }) }
      if V != none { var("V_z_d", domain: dom, level: at2); timber-shear-stress("tau_d", "tau_d", "V_z_d", at2, m) }
      else { var("tau_d", domain: dom, level: at2) }
      var("sigma_90_d", domain: dom, level: at2)
      let k = if s >= 0 { c.k_t_90.querzug } else { c.k_t_90.querdruck }
      var("k_t_90", "k_(t,90)", k, level: at2, label: if s >= 0 { "Querzug" } else { "Querdruck" }, norm: "SIA 265", norm-ref: "4.2.7.1")
      verify("sigma_90_d >= -f_c_90_d", level: timber-sub(lv, 3))
      verify("sigma_90_d <= f_t_90_d", level: timber-sub(lv, 3))
      let r = "(f_c_90_d / (f_c_90_d + k_t_90 dot f_t_90_d))"
      let formula = "((f_c_90_d + sigma_90_d) / (f_c_90_d + k_t_90 dot f_t_90_d))^2 + (tau_d / f_v_d)^2 dot (1 - " + r + "^2)"
      timber-verdict(plan, "eta", "eta", formula, unit)
    }
  })
}

// --- The member checks Woodcore saves ------------------------------------------

// data/checks.json, the member checks the export resolved (calc/domains/member_check.py): one record per Woodcore-Datei/checks/<id>.json, its strength class, section and moisture class written out, whether it can be calculated and why not. Read by the relative path calc-engine.typ reads every other export by.
#let timber-checks() = json("../data/checks.json").checks

// A refusal naming the checks there are.
#let timber-check-refusal(fn, id, checks) = fn + ": no member check " + repr(id) + " -- " + (if checks.len() == 0 { "none saved in Woodcore yet" } else { "valid checks: " + checks.keys().join(", ") })

// The design force of a record as the value with its unit verify-tension reads: «25 kN».
#let timber-check-force(force) = fmt-decimals(force.value, 6) + " " + force.unit

// A design moment of a record as verify-bending reads it: its magnitude with its unit, «12.5 kNm» -- member_check.moment_text's.
#let timber-check-moment(moment) = fmt-decimals(calc.abs(moment.value), 6) + " " + moment.unit

/// Every member check saved in Woodcore, in file-name order -- the loop a section printing all of them is written as, so a check saved in Woodcore reaches the report with no edit.
///
/// ```typ
/// #for id in check-member-ids() {
///   show-check-member(id, level: 1)
/// }
/// ```
///
/// ```typ
/// Gespeicherte Nachweise: #check-member-ids().join(", ").
/// ```
///
/// -> array
#let check-member-ids() = timber-checks().keys()

/// A member check saved in Woodcore, computed here: its member written down with `#member` -- the position it names, with the strength class, the section and the moisture class the export resolved, each the position's or the one stated in Woodcore -- and the check of its kind on it: `#verify-tension` for a tension (SIA 265 4.2.1); for a compression (4.2.2) `#verify-compression` with `stability: false` along the grain -- the section alone, buckling being a check of its own -- and `#verify-compression-perp` at an angle or across it; for a bending (4.2.3, 4.2.4) `#verify-bending` without a normal force and `#verify-bending-normal` with one, both with `stability: false` -- the section alone, lateral torsional buckling and buckling being checks of their own; for a buckling (4.2.8) `#verify-compression` with its stability, the buckling lengths beta · l about each axis; for a lateral torsional buckling (4.2.9) `#verify-bending` or `#verify-bending-normal` with their stability, a or sigma_m,crit, and with a compression the buckling lengths (37); for a shear (4.2.5) `#verify-shear`.
///
/// ```typ
/// #show-check-member("ZT-01")
/// ```
///
/// ```typ
/// #show-check-member("ZT-02", level: 3, member-level: 2, unit: "%")
/// ```
///
/// ```typ
/// #show-check-member("ZT-01", member-level: none, title: none, level: 1)
/// #val("eta", domain: "ZT-01-verify-tension", type: "expression")
/// ```
///
/// ```typ
/// #show-check-member("DR-01", level: 2)
/// #show-check-member("DR-02", level: 2)
/// ```
///
/// ```typ
/// #show-check-member("BI-01", level: 2)
/// #show-check-member("BI-02", level: 2)
/// #show-check-member("BI-03", level: 2)
/// ```
///
/// ```typ
/// #show-check-member("BI-01", level: -1, shown: (A: 2, W_y: 2, sigma_m_y_d: 3, eta_s: 1))
/// ```
///
/// A check of the «Résistance au feu» tab carries `fire` (issue #46): its member is written down with `fire: (duration:, sides:, wood:)` -- the duration the export resolved, the check's own or what VKF 15-15 requires of the project's building -- and the same check of its kind then checks the ideal residual section with R_d,fi = 1.8 · R_d (SIA 265 4.5.2), the forces being E_d,fi.
///
/// Nothing is computed in Python: the export only resolves what the check follows, and the call is exactly `#member(id, b:, h: or d:, grade:, moisture-class:, position:, impact:, …)` then the check of its kind -- `#verify-tension(id, N: "25 kN", alpha:, …)`, `#verify-compression(id, N: "-60 kN", stability: false, …)`, `#verify-compression-perp(id, F: "18 kN", l:, w:, alpha:, case:, larger:, …)`, `#verify-bending(id, M-y: "4.5 kNm", M-z:, alpha:, stability: false, …)` or `#verify-bending-normal(id, N: "-40 kN", M-y:, M-z:, alpha:, stability: false, …)` --, every value written out. The member's `var-domain` is the check's id, not the position's, so two checks on one position never collide, and what the check works out is published in `"<id>-verify-tension"`, `"<id>-verify-compression"`, `"<id>-verify-compression-perp"`, `"<id>-verify-bending"` or `"<id>-verify-bending-normal"`. Where the check names a position the export carries, the member's line is that position's line -- its type and material --, the resolved values in it. A check the export marked as one that cannot be calculated -- a position gone, no section, no strength class, no moisture class, a force that is not positive, a contact width a round section cannot give, a bending with no moment or with M_z at an angle -- is refused with its reason.
/// - id (str): the check's id, its file name in Woodcore. An unknown id fails listing the valid ones.
/// - level (int, auto): the check's level, the level of the verify-* command it calls: 0 prints nothing (the check is still made), 1 the verdict, 2 also the stress and the relation, 3 also how each value is found. auto follows the report. -1 prints only what `shown:` names, each at its own level, beside the title (v0.117); a verdict is printed where `shown:` names the key of its utilisation (issue #58).
/// - shown (dictionary, none): at `level: -1`, the variables printed and the level of each, `(A: 2, sigma_m_y_d: 3, eta_s: 1)` -- one list for the member and its check, a key both print being the check's; member-level then gives way to it. A key neither prints is refused naming those they do. none at any other level. A verdict is named by the key of its utilisation -- `eta`, `eta_s`, `eta_y`… --: at 1 its ratio and value, at 2 or 3 also its numbers, and nothing where `shown:` leaves it out (issue #58).
/// - member-level (int, auto, none): the member line's level, `#member`'s: 1 (the default) its line, 2 also its section and design values, 3 also how each is found; none prints no member line (level 0, the member still written down); auto follows the report.
/// - description (bool): true also prints the position's description after its line.
/// - title (auto, none, str): the check's heading: auto names the check and the check's id, none prints none, a string replaces it.
/// - unit (auto, str): how the verdict prints the ratio of the action to the resistance: against 1 (auto), `σ/f = 0.41 ⩽ 1`, or in percent ("%"), `σ/f = 41 %` and nothing after it. The utilisation eta stored is that ratio, never printed.
/// -> content
#let show-check-member(id, level: auto, shown: none, member-level: 1, description: false, title: auto, unit: auto) = {
  let fn = "show-check-member"
  let checks = timber-checks()
  if not (value-type(id) == str and id in checks) { panic(timber-check-refusal(fn, id, checks)) }
  if member-level != none { timber-check-level(fn, member-level) }
  if value-type(description) != bool { panic(fn + ": description is true or false -- got " + repr(description)) }
  let rec = checks.at(id)
  if not rec.calculable { panic(fn + ": " + id + " cannot be checked -- " + rec.reason) }
  if not (rec.kind in ("tension", "compression", "bending", "shear", "buckling", "lateral-torsional")) { panic(fn + ": the " + rec.kind + " check is not implemented yet") }
  let s = rec.section
  let sides = if s.type == "cir" { (d: s.d) } else { (b: s.b, h: s.h) }
  // the check of its kind, and at -1 one list for the member and the check (spec D-11): a key both print is the check's, the member taking the rest -- and its member-level giving way to it
  let command = if rec.kind == "tension" { "verify-tension" } else if rec.kind == "shear" { "verify-shear" } else if rec.kind in ("bending", "lateral-torsional") { if rec.N.value == 0 { "verify-bending" } else { "verify-bending-normal" } } else if rec.kind == "buckling" or rec.alpha == 0 { "verify-compression" } else { "verify-compression-perp" }
  let own = shown-keys(command)
  check-shown(fn, level, shown, shown-keys("member").filter(k => not (k in own)) + own)
  let picked = level == selection-level
  let check-shown-of = if shown == none { none } else { shown.pairs().filter(((k, n)) => k in own).to-dict() }
  let member-shown = if shown == none { none } else { shown.pairs().filter(((k, n)) => not (k in own)).to-dict() }
  // the position's line where the export carries the position; a member that is none, or whose position is gone, is headed by the check's id
  let pos = if rec.position != none and rec.position in known-position-ids() { rec.position } else { none }
  // no member line printed (member-level: none): a position deleted with its values kept still says so (issue #9)
  if member-level == none and pos != none and not picked { context position-archived-note(load-position(pos)) }
  // a check in the fire situation (issue #46): #member's fire:, the duration the export resolved -- stated, or what VKF 15-15 requires -- and the faces; a softwood's wood is read off the grade again
  let fire = rec.at("fire", default: none)
  let burning = if fire == none { (:) } else { (fire: (duration: fire.duration, sides: fire.sides, wood: if fire.wood in (none, "softwood") { none } else { fire.wood })) }
  member(id, ..sides, grade: rec.grade, moisture-class: rec.moisture_class, position: pos, impact: rec.impact, ..burning,
    description: description, level: if picked { level } else if member-level == none { 0 } else { member-level }, shown: if picked { member-shown } else { none })
  // the buckling lengths a buckling, and a lateral torsional buckling with a compression, read: beta · l about each axis (issue #38)
  let lengths = if rec.at("l_y", default: none) != none { (l-y: rec.l_y, l-z: rec.l_z, beta-y: rec.beta_y, beta-z: rec.beta_z) } else { (:) }
  if rec.kind == "tension" {
    verify-tension(id, N: timber-check-force(rec.N), alpha: rec.alpha, level: level, shown: check-shown-of, title: title, unit: unit)
  } else if rec.kind == "shear" {
    // 4.2.5: the shear forces in their planes, no torsion -- a check of its own
    let forces = (:)
    if rec.V_z != none { forces.insert("V", timber-check-force(rec.V_z)) }
    if rec.V_y != none { forces.insert("V-y", timber-check-force(rec.V_y)) }
    verify-shear(id, ..forces, pith: rec.pith, level: level, shown: check-shown-of, title: title, unit: unit)
  } else if rec.kind == "buckling" {
    // 4.2.8: along the grain with its stability
    verify-compression(id, N: "-" + timber-check-force(rec.N), ..lengths, level: level, shown: check-shown-of, title: title, unit: unit)
  } else if rec.kind == "lateral-torsional" {
    // 4.2.9: a bending with its stability -- (38) without a normal force or with a tension, (37) with a compression
    let moments = (:)
    if rec.M_y != none { moments.insert("M-y", timber-check-moment(rec.M_y)) }
    if rec.M_z != none { moments.insert("M-z", timber-check-moment(rec.M_z)) }
    let lateral = if rec.a != none { (a: rec.a) } else { (sigma-m-crit: rec.sigma_m_crit) }
    if rec.N.value == 0 {
      verify-bending(id, ..moments, ..lateral, level: level, shown: check-shown-of, title: title, unit: unit)
    } else {
      verify-bending-normal(id, N: timber-check-force(rec.N), ..moments, ..lateral, ..(if rec.N.value < 0 { lengths } else { (:) }), level: level, shown: check-shown-of, title: title, unit: unit)
    }
  } else if rec.kind == "bending" {
    // the section alone, lateral torsional buckling and buckling being checks of their own: without a normal force (14) or (17) to (20), with one (21) or (22) -- N signed, tension positive
    let moments = (:)
    if rec.M_y != none { moments.insert("M-y", timber-check-moment(rec.M_y)) }
    if rec.M_z != none { moments.insert("M-z", timber-check-moment(rec.M_z)) }
    if rec.N.value == 0 {
      verify-bending(id, ..moments, alpha: rec.alpha, stability: false, level: level, shown: check-shown-of, title: title, unit: unit)
    } else {
      verify-bending-normal(id, N: timber-check-force(rec.N), ..moments, alpha: rec.alpha, stability: false, level: level, shown: check-shown-of, title: title, unit: unit)
    }
  } else if rec.alpha == 0 {
    // along the grain: the section alone, buckling being a check of its own
    verify-compression(id, N: "-" + timber-check-force(rec.N), stability: false, level: level, shown: check-shown-of, title: title, unit: unit)
  } else {
    verify-compression-perp(id, F: timber-check-force(rec.N), l: rec.l, w: rec.w, alpha: rec.alpha, case: rec.case, larger: rec.larger, level: level, shown: check-shown-of, title: title, unit: unit)
  }
}
