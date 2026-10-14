// A calculation written by hand in the report, printed in letters and in numbers, and *computed* -- with its units (docs/project/purpose.md §1, docs/typst/api-conventions.md §10bis).
//
// `show-calc` prints what a Python domain already computed: the formula in letters, then the same formula with the numbers put in their place, derived by substitution so that the two cannot disagree (section 10bis). That guarantee stops at the edge of `data/`. A calculation written directly in `Sections/` -- a capacity read off a manufacturer's table, a lever arm measured on a drawing -- had until v0.60 to be written *twice*: once as an expression that computes, once as math that displays. Nothing compared them, and they drifted: `Sections/005` printed `M = 1 kN · 0.5 m = 0.25 kNm` for a line whose code said `F * l/2`, and `F = 0.275 kNm · 10⁶ / 135 mm = 2.037 kN`, which is off by a thousand as written.
//
// `eq` closes that. The formula is written **once**, in ordinary Typst math source, and it is
//
//   * displayed as it stands -- so every math command works, integrals and matrices included;
//   * substituted, each symbol replaced by its value and its unit;
//   * **evaluated**, with a real unit algebra, so the answer comes out of the formula rather than beside it.
//
// The unit algebra is the half that earns its keep. `M_"Ed" / a` where M_Ed is in kNm and a in mm comes to 2037.04 N, which is 2.037 kN -- the conversion is the algebra's, and **the factor of 1000 the engineer used to type in is no longer needed**. Where the declared unit cannot be reached from the operands, the compile stops naming both.
//
// ⚠️ What it cannot catch is a *magnitude* error whose units happen to line up: 1000 is dimensionless, so `M / a dot 1000` is dimensionally valid and comes to 2037 kN. The algebra checks dimensions, never sizes. What it buys against that is visibility -- the substituted line now reads `0.275 kNm / 135 mm · 1000`, and 2037 kN under a bench is an answer you see.
//
// ⚠️ Still untraced, like everything computed in Typst (section 1): no `source`, nothing in `data/`, nothing catalogued. What it guarantees is that the printed formula, the printed numbers and the printed answer are one statement. A value a checker must re-derive from the data belongs in a Python domain.

// The display helpers this file prints through. The dependency runs one way only -- calc-engine.typ knows nothing of this file -- and commands.typ imports both, which is how section 10bis says a second library file joins the report.
#import "calc-engine.typ": annotated-rows, chain-leading, chain-line, colon-str, connection-domain, connector-domain, domain-ids, find-calculation, fmt-decimals, formula-chain, get-choices, instance-ids, norm-text, number-digits, override-colour, render-prose, render-symbol, render-table, resolve-level, semicolon-str, signed-text, source-label, t-str, test-aliases, test-nok, test-ok, test-relations, tl-str, value-type, var-current, var-lookup, var-names, var-of, var-registry, var-store
// The minimum distances of SIA 265 computed with a diameter (lib/distance.typ, v0.87): imported here by name, so commands.typ, which re-exports this file at the wildcard, gives every section `distance` and none of its helpers.
#import "distance.typ": distance
// The member checks of SIA 265 4.2 (lib/timber.typ, v0.88): imported here by name for the same reason, and the only other file this one imports -- timber.typ needs var, eq and verify back, and imports them inside its commands' bodies, which is what keeps the two out of a cycle.
#import "timber.typ": member, show-check-member, check-member-ids, verify-tension, verify-compression, verify-compression-perp, verify-bending, verify-bending-normal, verify-shear, verify-shear-off, verify-shear-perp
// the steel checks of Woodcore's «Acier» tabs, printed as the export computed them (issues #50-#52)
#import "steel.typ": show-check-steel, check-steel-ids
// The bibliography (lib/bibliography.typ, v0.99): its two commands by name, on distance.typ's arrangement, and `bib-note` -- which every command below that takes a `norm:` emits **before its context**, so that the document it cites is listed at the end (docs/typst/api-conventions.md §10bis).
#import "bibliography.typ": bib-note, cite-norm, show-bibliography
// The summary tables (lib/summary.typ, v0.99): the three commands by name, and `summary-mark` -- which `var` and `eq` call inside the `var-registry.update` they already have when they are given `summary: true`. summary.typ imports calc-engine.typ and nothing else, so the chain calc-engine -> summary -> formula stays acyclic (docs/typst/api-conventions.md §10bis).
#import "summary.typ": show-line-load-summary, show-load-summary, show-result-summary, summary-mark
// The parametric objects of a project's documents (lib/document.typ, the three document modes): the eleven commands by name, on distance.typ's arrangement -- document.typ imports calc-engine.typ and bibliography.typ at its top and nothing from this file, a value in a cell being `doc-value`'s, so the chain stays acyclic.
#import "document.typ": doc-annexes, doc-checklist, doc-choice, doc-extract, doc-field, doc-fire-plan, doc-image, doc-plan, doc-signatures, doc-table, doc-value, dead-load-table, live-load-table, show-norm-list
// The export sheets (lib/sheet.typ, v0.114): the six commands, and since v0.115 the fire-protection plan's two, by name, on the same arrangement -- sheet.typ imports calc-engine.typ and document.typ and nothing from this file, so the chain stays acyclic.
#import "sheet.typ": sheet, sheet-fire-legend, sheet-fire-viewport, sheet-legend, sheet-position-list, sheet-quantities, sheet-section, sheet-text, sheet-titleblock, sheet-viewport
// The list of the positions (lib/positions.typ, v0.116): its one command by name -- positions.typ imports calc-engine.typ and nothing else, and sheet.typ imports its table builder, so the chain calc-engine -> positions -> sheet -> formula stays acyclic.
#import "positions.typ": show-plan-quantities, show-position-list

// --- Units ------------------------------------------------------------------
// A unit is parsed into a scale factor and a map of base dimensions, so that two units can be multiplied, divided and compared. `kN` is (1000, N:1); `mm²` is (1e-6, m:2); `kN/m²` is (1000, N:1 m:-2) and `N/mm²` is (1e6, N:1 m:-2) -- the same dimensions, a factor of a thousand apart, which is what makes 1 N/mm² print as 1000 kN/m² rather than as an error.
//
// N is kept as a base rather than resolved to kg·m/s²: nothing in a structural report mixes the two, and keeping force whole makes every message read in the units an engineer writes.

// **The tables are lib/units.json's** (v0.117, spec 2026-10-08-onglet-formule-domaines ARCH-005): the prefixes, the bases with their factor and dimensions, the superscript digits, the unit a result of each dimension is printed in -- written once, for this file and for the «Formule» tab's instant calculation (calc/units.py, its Python twin, which tests/test_units.py holds equal to this one). A unit is read as the longest prefix-and-base match, the first listed where two are as long, so the file's order is part of the rule; every factor is a float there, which `json` reads as one. The file is copied into a project with the engine (project.ENGINE_FILES).
#let units-data = json("units.json")
#let unit-prefixes = units-data.prefixes

// symbol: (factor towards the base, dimensions). An angle is dimensionless in the algebra but not interchangeable in print, so `rad` and `°` are kept apart; `t` is the tonne and `l` the litre.
#let unit-bases = units-data.bases.pairs().map(((symbol, spec)) => (symbol, (spec.factor, spec.dims))).to-dict()

// Superscripts as the report writes them, and as a workbook writes them (kg/m3). All ten digits, and read as a *run*, so that a unit this file composes itself reads back: the base-unit fallback for a dimension the table does not name (`N²`), and the natural unit of a formula's operands (`Nmm²`). Both are stored in the registry and may come back as an operand, so the parser has to accept everything the writer emits.
#let unit-exponents = units-data.exponents

// An integer as superscript digits: 2 → "²", 12 → "¹²", -5 → "⁻⁵".
//
// ⚠️ A caret would not do, and this is the whole of the v0.63 display bug: every unit this file writes is printed as a **quoted word inside math**, where `^` is not an operator but a character -- so a dimension the preference table did not name came out on the page as `1000000 N^2`, caret and all.
// ⚠️ Both minus signs: `str(-5)` gives a **typographic** minus (U+2212), not the hyphen the keyboard writes, and a table holding only the hyphen fails on the first negative exponent it meets.
#let superscript-digits = units-data.superscripts

#let sup(n) = str(n).clusters().map(c => superscript-digits.at(c)).join("")

// A unit written by hand with a caret, spelt as the report prints one: `N/mm^2` → `N/mm²`, `m^3` → `m³`. Applied where a unit enters from a call -- `var`, `var-unit`, `eq`'s `unit:`, `unit`, `val`'s `unit:` -- so that the registry holds one spelling and every line printing it shows a real exponent (v0.86, the engineer's request: a caret is quicker to type than ², which a Swiss keyboard has no key for). parse-unit already read `^2` as an exponent; only the page showed the caret, for the reason `superscript-digits` gives.
// Only `^` followed by digits, which is all parse-unit reads after a caret: `^-1` is left as written, and refused where it is read.
#let written-unit(u) = {
  if type(u) != str or not u.contains("^") { return u }
  u.replace(regex("\^([0-9]+)"), m => m.captures.at(0).clusters().map(c => superscript-digits.at(c)).join(""))
}

// Every dimension with a zero exponent dropped, so that two maps can be compared with ==.
#let clean-dims(dims) = {
  let out = (:)
  for (k, v) in dims { if v != 0 { out.insert(k, v) } }
  out
}

#let dims-equal(a, b) = clean-dims(a) == clean-dims(b)

// A dimension map as a unit an engineer would recognise: (N: 1, m: -2) -> "N/m²". Three jobs at once, which is why it is worth being exact about: the wording of a refusal, the **key** of the unit table below, and the unit a result is printed in where that table names none.
//
// The dimensions are **sorted**, so that one physical dimension has exactly one text whichever order the formula built it in -- `F dot l` and `l dot F` both give `N·m`, and a table keyed by this cannot miss. Negative exponents go behind the `/`, so no `⁻` is ever emitted here and parse-unit reads back everything this writes.
#let dims-text(dims) = {
  let d = clean-dims(dims)
  if d.len() == 0 { return "1" }
  let up = d.pairs().filter(p => p.at(1) > 0).sorted(key: p => p.at(0))
  let down = d.pairs().filter(p => p.at(1) < 0).sorted(key: p => p.at(0))
  let part(pairs, sign) = pairs.map(p => p.at(0) + (if calc.abs(p.at(1)) == 1 { "" } else { sup(calc.abs(p.at(1))) })).join("·")
  let top = if up.len() == 0 { "1" } else { part(up, 1) }
  if down.len() == 0 { top } else { top + "/" + part(down, -1) }
}

// One factor of a unit product -- `kN`, `mm²`, `m3` -- read off the front of `cl` (a cluster array) at `i`. Returns (factor, dims, next) or none.
//
// The match is the **longest** that any prefix/base pair produces, which is what tells `mm` (milli-metre, two clusters) from `m`·`m` (metre squared, one and one), and `kNm` (kN then m) from anything else. A rule rather than a table of special cases.
#let read-factor(cl, i) = {
  let best = none
  for (symbol, spec) in unit-bases {
    let n = symbol.clusters().len()
    if i + n <= cl.len() and cl.slice(i, i + n).join("") == symbol {
      if best == none or n > best.at(2) { best = (spec.at(0), spec.at(1), n) }
    }
    for (p, scale) in unit-prefixes {
      let m = p.clusters().len() + n
      if i + m <= cl.len() and cl.slice(i, i + m).join("") == p + symbol {
        if best == none or m > best.at(2) { best = (spec.at(0) * scale, spec.at(1), m) }
      }
    }
  }
  if best == none { return none }
  let (factor, dims, used) = best
  let j = i + used
  // an exponent: ², ³, a bare digit (kg/m3), or ^n
  let power = 1
  if j < cl.len() and cl.at(j) in unit-exponents {
    // a run of them, so that a composed unit with a two-digit exponent reads back
    power = 0
    while j < cl.len() and cl.at(j) in unit-exponents {
      power = power * 10 + unit-exponents.at(cl.at(j))
      j += 1
    }
  } else {
    let k = j
    if k < cl.len() and cl.at(k) == "^" { k += 1 }
    let digits = ""
    while k < cl.len() and cl.at(k).match(regex("^[0-9]$")) != none { digits += cl.at(k); k += 1 }
    if digits != "" { power = int(digits); j = k }
  }
  let out = (:)
  for (d, e) in dims { out.insert(d, e * power) }
  (calc.pow(factor, power), out, j)
}

// A product of factors -- `kNm`, `N`, `mm²` -- with no division in it.
#let read-product(text) = {
  let cl = text.trim().clusters().filter(c => c != " " and c != "·" and c != "*" and c != "⋅")
  let factor = 1.0
  let dims = (:)
  let i = 0
  while i < cl.len() {
    let got = read-factor(cl, i)
    if got == none { return none }
    factor *= got.at(0)
    for (d, e) in got.at(1) { dims.insert(d, dims.at(d, default: 0) + e) }
    i = got.at(2)
  }
  (factor: factor, dims: dims)
}

/// A unit string as a scale factor and a map of base dimensions, or `none` where it cannot be read.
///
/// `"kN"` → `(factor: 1000.0, dims: (N: 1))`; `"kN/m²"` → `(factor: 1000.0, dims: (N: 1, m: -2))`; `""` → dimensionless. Everything after the first `/` is a denominator, so `kNm/rad` and `kg/m³` read as written.
/// - text (str): the unit, as the report writes it.
/// -> dictionary | none
#let parse-unit(text) = {
  let t = if text == none { "" } else { text.trim() }
  if t == "" { return (factor: 1.0, dims: (:)) }
  let parts = t.split("/")
  let factor = 1.0
  let dims = (:)
  for (i, part) in parts.enumerate() {
    if part.trim() == "" { return none }
    let got = read-product(part)
    if got == none { return none }
    let sign = if i == 0 { 1 } else { -1 }
    factor = if sign == 1 { factor * got.factor } else { factor / got.factor }
    for (d, e) in got.dims { dims.insert(d, dims.at(d, default: 0) + sign * e) }
  }
  (factor: factor, dims: clean-dims(dims))
}

// --- Quantities -------------------------------------------------------------
// Inside the evaluator every value is carried in base units, so that a sum can check its operands and a product can just multiply. The number the engineer wrote is kept separately, for the substituted line.
//
// Beside the dimensions, every quantity carries `nat`: the units **as the operands were written**, as a map {unit → exponent}. The dimensions say a result is a moment; `nat` says it was reached by multiplying an N by a mm. That is what lets a result whose declared unit cannot be reached still be printed in something an engineer recognises -- `Nmm` rather than base units -- instead of stopping the report (v0.63).

// The unit maps of two operands combined: exponents added (a product) or subtracted (a quotient), and a zero dropped so that `Nmm/mm` comes out as `N`.
#let nat-mul(a, b, sign) = {
  let out = a
  for (u, e) in b { out.insert(u, out.at(u, default: 0) + sign * e) }
  let clean = (:)
  for (u, e) in out { if e != 0 { clean.insert(u, e) } }
  clean
}

// A unit map raised to a power, `sqrt` included as the power ½: `mm²` squared is `mm⁴`, and the square root of an `mm²` is an `mm`. A power that would leave any exponent fractional -- the square root of a `kNm` -- has no unit map to give, so it gives none rather than invent one, and the caller falls back to the table.
#let nat-pow(a, n) = {
  let out = (:)
  for (u, e) in a {
    let x = e * n
    if x != calc.round(x) { return (:) }
    if x != 0 { out.insert(u, int(calc.round(x))) }
  }
  out
}

#let quantity(value, unit) = {
  let u = parse-unit(unit)
  if u == none { return none }
  let written = if unit == none { "" } else { unit.trim() }
  (base: value * u.factor, dims: u.dims, nat: if written == "" { (:) } else { ((written): 1) })
}

#let q-nat(q) = q.at("nat", default: (:))

#let q-mul(a, b) = {
  let dims = a.dims
  for (d, e) in b.dims { dims.insert(d, dims.at(d, default: 0) + e) }
  (base: a.base * b.base, dims: clean-dims(dims), nat: nat-mul(q-nat(a), q-nat(b), 1))
}

#let q-div(a, b) = {
  if b.base == 0 { panic("eq: division by zero in the formula") }
  let dims = a.dims
  for (d, e) in b.dims { dims.insert(d, dims.at(d, default: 0) - e) }
  (base: a.base / b.base, dims: clean-dims(dims), nat: nat-mul(q-nat(a), q-nat(b), -1))
}

#let q-add(a, b, sign) = {
  if not dims-equal(a.dims, b.dims) {
    panic("eq: cannot add " + dims-text(a.dims) + " and " + dims-text(b.dims)
      + " -- the two sides of a + or a - must have the same dimensions")
  }
  // the two sides have one dimension but may be written in two units (a kN plus a N): the left one is the one the result is offered in, as it is the one the formula leads with
  (base: a.base + sign * b.base, dims: clean-dims(a.dims),
   nat: if q-nat(a).len() > 0 { q-nat(a) } else { q-nat(b) })
}

#let q-pow(a, n) = {
  let dims = (:)
  for (d, e) in a.dims { dims.insert(d, e * n) }
  (base: calc.pow(a.base, n), dims: clean-dims(dims), nat: nat-pow(q-nat(a), n))
}

// --- The unit the operands were written in -----------------------------------

// The scale factor and the dimensions a unit map stands for, read from the units themselves: {kN: 1, m: 1} is (1000, N·m). `none` where one of them cannot be read, which cannot happen for a map built out of units that were parsed on the way in, but is checked rather than assumed.
#let nat-parsed(nat) = {
  let factor = 1.0
  let dims = (:)
  for (u, e) in nat {
    let p = parse-unit(u)
    if p == none { return none }
    factor *= calc.pow(p.factor, e)
    for (d, x) in p.dims { dims.insert(d, dims.at(d, default: 0) + x * e) }
  }
  (factor: factor, dims: clean-dims(dims))
}

// A unit map written out: positives first, then `/` and the negatives, exponents as real superscripts. Sorted, for the reason dims-text is -- one map, one spelling, whichever order the formula built it in. `joiner` is what separates two factors of the same side.
#let compose-unit(nat, joiner) = {
  let up = nat.pairs().filter(p => p.at(1) > 0).sorted(key: p => p.at(0))
  let down = nat.pairs().filter(p => p.at(1) < 0).sorted(key: p => p.at(0))
  let part(pairs) = pairs.map(p => p.at(0) + (if calc.abs(p.at(1)) == 1 { "" } else { sup(calc.abs(p.at(1))) })).join(joiner)
  let top = if up.len() == 0 { "1" } else { part(up) }
  if down.len() == 0 { top } else { top + "/" + part(down) }
}

/// The unit a formula's operands were written in -- an N times a mm gives `"Nmm"` -- or `none` where they compose into nothing writable.
///
/// Composed **without a separator**, the way `kNm` is written. That is a real risk and it is checked rather than reasoned about: the candidate is read back with `parse-unit`, and it is kept only if it comes to the very factor and dimensions it was built from. Where it does not, the same map is written with `·` (`kN·mm`, which `read-product` also reads), and where that fails too there is no natural unit and the caller falls back.
/// - nat (dictionary): the unit map, {unit → exponent}.
/// -> str | none
#let natural-unit(nat) = {
  if nat.len() == 0 { return none }
  let want = nat-parsed(nat)
  if want == none { return none }
  let fits(text) = {
    let p = parse-unit(text)
    (p != none and dims-equal(p.dims, want.dims)
      and calc.abs(p.factor - want.factor) <= 1e-9 * calc.max(1.0, calc.abs(want.factor)))
  }
  let tight = compose-unit(nat, "")
  if fits(tight) { return tight }
  let spaced = compose-unit(nat, "·")
  if fits(spaced) { return spaced }
  none
}

// --- The expression --------------------------------------------------------
// A recursive-descent parser over the substituted formula. Small on purpose: it reads exactly the arithmetic an engineering formula is made of, and anything outside it -- an integral, a derivative -- is not evaluated at all but printed, the caller then giving the answer with `value:`.

#let formula-functions = ("sqrt", "abs", "max", "min", "sin", "cos", "tan", "arcsin", "arccos", "arctan", "asin", "acos", "atan", "ln", "log", "exp")

// `asin`, `acos` and `atan` are what a programmer types and Typst's math does not know: they evaluated and then stopped the display with «unknown variable: atan», while `arctan`, which the math prints, was refused as a name nobody declared (v0.86). Both spellings evaluate now, and the short ones are printed as the long ones.
#let formula-display-names = (asin: "arcsin", acos: "arccos", atan: "arctan")

// The formula with every known symbol replaced by a placeholder, so that the tokenizer never has to parse math: a symbol may contain quotes, parentheses and commas (`q_(k,11)`), all of which would otherwise be operators. Longest symbol first, so `mu_1` cannot eat `mu_11`.
#let placeholder(i) = "\u{0001}" + str(i) + "\u{0002}"

// The two parts of a numeric literal that are not its digits, each read off the clusters at `i` and each returning what it adds and where it ends. Functions rather than blocks inside `tokenize`, for the reason the note on `read-token` gives.

// An exponent written `1e3` or `1e-3`. Where there is none -- no `e`, or an `e` no digit follows -- it adds nothing and `i` does not move, so `1e` reads as the number 1 followed by a word.
#let read-exponent(cl, i) = {
  if i >= cl.len() or (cl.at(i) != "e" and cl.at(i) != "E") { return ("", i) }
  let tail = cl.at(i)
  let j = i + 1
  if j < cl.len() and (cl.at(j) == "-" or cl.at(j) == "+") { tail += cl.at(j); j += 1 }
  let expo = ""
  while j < cl.len() and cl.at(j).match(regex("^[0-9]$")) != none { expo += cl.at(j); j += 1 }
  if expo == "" { return ("", i) }
  (tail + expo, j)
}

// The unit a literal carries after it, written as math writes it: `350 "m"`, `0.4 "kN/m²"`. Norm formulas need it -- SIA 261's s_k = (1 + (h_0/350)²) · 0.4 has a length in that 350 and a pressure in that 0.4, and without them the sum is dimensionally false. Which the algebra says, rather than letting it pass. Where there is no unit, or its quote is never closed, the unit is empty and `i` does not move.
#let read-literal-unit(cl, i) = {
  let k = i
  while k < cl.len() and cl.at(k) == " " { k += 1 }
  if k >= cl.len() or cl.at(k) != "\"" { return ("", i) }
  let j = k + 1
  let text = ""
  while j < cl.len() and cl.at(j) != "\"" { text += cl.at(j); j += 1 }
  if j >= cl.len() { return ("", i) }
  (text, j + 1)
}

// The tokens written with a single character, in a table rather than in a chain of `else if`: the character, and the token it is.
#let single-tokens = (
  "+": (kind: "op", op: "+"),
  "-": (kind: "op", op: "-"),
  "*": (kind: "op", op: "*"),
  "/": (kind: "op", op: "/"),
  "^": (kind: "op", op: "^"),
  "⋅": (kind: "op", op: "*"),
  "·": (kind: "op", op: "*"),
  "(": (kind: "lpar"),
  ")": (kind: "rpar"),
  ",": (kind: "comma"),
)

#let space-chars = (" ", "\n", "\t")
#let is-digit(c) = c.match(regex("^[0-9.]$")) != none
#let is-letter(c) = c.match(regex("^[A-Za-z]$")) != none

// The symbol the substitution put a placeholder in the place of, at `i`: its token and where it ends, or `none` for a placeholder whose end marker never comes.
#let read-placeholder(cl, i) = {
  let j = i + 1
  let digits = ""
  while j < cl.len() and cl.at(j) != "\u{0002}" { digits += cl.at(j); j += 1 }
  if j >= cl.len() { return none }
  (((kind: "sym", index: int(digits)),), j + 1)
}

// The number at `i` -- its digits, the exponent and the unit those two read -- as a token, and where it ends. `none` for a unit that is not a unit.
#let read-number(cl, i) = {
  let j = i
  let digits = ""
  while j < cl.len() and is-digit(cl.at(j)) { digits += cl.at(j); j += 1 }
  let (expo, past-expo) = read-exponent(cl, j)
  let (unit, past-unit) = read-literal-unit(cl, past-expo)
  let q = quantity(float(digits + expo), unit)
  if q == none { return none }
  (((kind: "qty", value: q),), past-unit)
}

// The word at `i`: `dot`, which multiplies, or one of the functions the formula may call. Anything else is a symbol the caller did not declare, and the formula is then not evaluable.
#let read-word(cl, i) = {
  let j = i
  let word = ""
  while j < cl.len() and is-letter(cl.at(j)) { word += cl.at(j); j += 1 }
  if word == "dot" { return (((kind: "op", op: "*"),), j) }
  // π, which math prints as the letter and a formula of the norm needs as a number -- SIA 265 (34), lambda_rel = lambda/pi · sqrt(f_c,0,k / E_0,05) (v0.88)
  if word == "pi" { return (((kind: "qty", value: quantity(calc.pi, "")),), j) }
  if word in formula-functions { return (((kind: "func", name: word),), j) }
  none
}

// One step of the tokenizer: the tokens the character at `i` begins -- none of them, for a space -- and where it ends. `none` is a character the tokenizer does not know, and aborts the whole evaluation.
//
// 👉 Every case is one line here, and what each reads is a function of its own. That is not a matter of style: written out as one chain of `else if` inside the `while` loop, as it was in v0.60, this defeated tinymist's type checker -- which runs on every keystroke, for completion and for inlay hints -- and it recursed until it overflowed its stack and killed the language server (`has overflowed its stack`, exit 3221225725, v0.60.1). The document compiled perfectly throughout, so nothing but the editor ever showed it. Removing either of the two long branches was enough to stop it, so what costs is the weight of the chain as a whole: keep each case short, and read what it needs elsewhere.
#let read-token(cl, i) = {
  let c = cl.at(i)
  if c in space-chars { return ((), i + 1) }
  if c in single-tokens { return ((single-tokens.at(c),), i + 1) }
  if c == "\u{0001}" { return read-placeholder(cl, i) }
  if is-digit(c) { return read-number(cl, i) }
  if is-letter(c) { return read-word(cl, i) }
  // \/ is math's own slanted division, and it divides
  if c == "\\" and i + 1 < cl.len() and cl.at(i + 1) == "/" { return (((kind: "op", op: "/"),), i + 2) }
  none
}

#let tokenize(src) = {
  let cl = src.clusters()
  let tokens = ()
  let i = 0
  while i < cl.len() {
    let got = read-token(cl, i)
    if got == none { return none }
    tokens += got.at(0)
    i = got.at(1)
  }
  tokens
}

// expr := term (("+" | "-") term)*
// term := unary (("*" | "/") unary)*
// unary := "-" unary | power
// power := atom ("^" number)?
// atom := number | symbol | "(" expr ")" | func "(" expr ("," expr)* ")"
//
// Each returns (value, next) or none; `none` anywhere aborts the whole evaluation, and the caller falls back to printing without computing.

#let parse-expr(tokens, i, values) = {
  let parse-atom(i) = {
    if i >= tokens.len() { return none }
    let t = tokens.at(i)
    if t.kind == "qty" { return (t.value, i + 1) }
    if t.kind == "sym" {
      if t.index >= values.len() { return none }
      return (values.at(t.index), i + 1)
    }
    if t.kind == "lpar" {
      let got = parse-expr(tokens, i + 1, values)
      if got == none { return none }
      if got.at(1) >= tokens.len() or tokens.at(got.at(1)).kind != "rpar" { return none }
      return (got.at(0), got.at(1) + 1)
    }
    if t.kind == "func" {
      if i + 1 >= tokens.len() or tokens.at(i + 1).kind != "lpar" { return none }
      let args = ()
      let j = i + 2
      while true {
        let got = parse-expr(tokens, j, values)
        if got == none { return none }
        args.push(got.at(0))
        j = got.at(1)
        if j < tokens.len() and tokens.at(j).kind == "comma" { j += 1 } else { break }
      }
      if j >= tokens.len() or tokens.at(j).kind != "rpar" { return none }
      let a = args.first()
      let out = if t.name == "sqrt" {
        let dims = (:)
        for (d, e) in a.dims {
          if calc.rem(e, 2) != 0 { panic("eq: sqrt of " + dims-text(a.dims) + ", whose dimensions are not even") }
          dims.insert(d, int(e / 2))
        }
        (base: calc.sqrt(a.base), dims: clean-dims(dims), nat: nat-pow(q-nat(a), 0.5))
      } else if t.name == "abs" { (base: calc.abs(a.base), dims: a.dims, nat: q-nat(a))
      } else if t.name == "max" or t.name == "min" {
        for other in args.slice(1) {
          if not dims-equal(a.dims, other.dims) {
            panic("eq: " + t.name + " compares " + dims-text(a.dims) + " with " + dims-text(other.dims))
          }
        }
        let bases = args.map(q => q.base)
        (base: if t.name == "max" { calc.max(..bases) } else { calc.min(..bases) }, dims: a.dims, nat: q-nat(a))
      } else {
        // the rest take and return a plain number: an angle in radians, a ratio
        if clean-dims(a.dims).len() != 0 and clean-dims(a.dims) != (deg: 1) {
          panic("eq: " + t.name + " takes a number, got " + dims-text(a.dims))
        }
        let x = if clean-dims(a.dims) == (deg: 1) { a.base * calc.pi / 180 } else { a.base }
        let v = if t.name == "sin" { calc.sin(x) } else if t.name == "cos" { calc.cos(x) }
          else if t.name == "tan" { calc.tan(x) } else if t.name in ("asin", "arcsin") { calc.asin(x).rad() }
          else if t.name in ("acos", "arccos") { calc.acos(x).rad() } else if t.name in ("atan", "arctan") { calc.atan(x).rad() }
          else if t.name == "ln" { calc.ln(x) } else if t.name == "log" { calc.log(x) }
          else { calc.exp(x) }
        (base: v, dims: (:), nat: (:))
      }
      return (out, j + 1)
    }
    none
  }

  let parse-power(i) = {
    let got = parse-atom(i)
    if got == none { return none }
    let (value, j) = got
    // one line: a line break inside a Typst `if` condition ends the expression
    if (j + 1 < tokens.len() and tokens.at(j).kind == "op" and tokens.at(j).op == "^" and tokens.at(j + 1).kind == "qty" and clean-dims(tokens.at(j + 1).value.dims).len() == 0) {
      let n = tokens.at(j + 1).value.base
      // ⚠️ A power that leaves a dimension fractional has no unit to give -- `d^2.6` of a d in mm is mm^2.6 -- and until v0.86 it crashed deep in the display with «dictionary does not contain key "."», on the one formula a timber engineer writes most: SIA 265 (87), M_u,k = 0.3 · f_u,k · d^2.6, which holds for d in mm and gives Nmm **by convention**. Refused here, saying what to write instead.
      if clean-dims(value.dims).values().any(e => calc.fract(e * n) != 0) {
        panic("eq: " + dims-text(value.dims) + " raised to " + str(n) + " has no unit -- a formula that holds only "
          + "in given units (SIA 265 (87): d in mm) is written with its answer and its unit, value: and unit:, "
          + "or with its operands as plain numbers")
      }
      return (q-pow(value, n), j + 2)
    }
    (value, j)
  }

  let parse-unary(i) = {
    if i < tokens.len() and tokens.at(i).kind == "op" and tokens.at(i).op == "-" {
      let got = parse-unary(i + 1)
      if got == none { return none }
      return ((base: -got.at(0).base, dims: got.at(0).dims, nat: q-nat(got.at(0))), got.at(1))
    }
    parse-power(i)
  }

  let parse-term(i) = {
    let got = parse-unary(i)
    if got == none { return none }
    let (value, j) = got
    while j < tokens.len() and tokens.at(j).kind == "op" and (tokens.at(j).op == "*" or tokens.at(j).op == "/") {
      let op = tokens.at(j).op
      let next = parse-unary(j + 1)
      if next == none { return none }
      value = if op == "*" { q-mul(value, next.at(0)) } else { q-div(value, next.at(0)) }
      j = next.at(1)
    }
    (value, j)
  }

  let got = parse-term(i)
  if got == none { return none }
  let (value, j) = got
  while j < tokens.len() and tokens.at(j).kind == "op" and (tokens.at(j).op == "+" or tokens.at(j).op == "-") {
    let sign = if tokens.at(j).op == "+" { 1 } else { -1 }
    let next = parse-term(j + 1)
    if next == none { return none }
    value = q-add(value, next.at(0), sign)
    j = next.at(1)
  }
  (value, j)
}

// --- Symbols ----------------------------------------------------------------
// A registry key is an identifier -- `k_dens`, `mu_11` -- and the formula names the symbol as math source -- `k_"dens"`, `mu_11`. The two are tied by the project's own rule (section 3.1): a multi-letter subscript that is not a known Greek name is quoted. A key that cannot be written as an identifier at all (`q_(k,11)`) is given as a string instead and used exactly as written.

#let greek-names = (
  "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota",
  "kappa", "lambda", "mu", "nu", "xi", "pi", "rho", "sigma", "tau", "upsilon",
  "phi", "chi", "psi", "omega",
  "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega",
)

// `key-symbol` stands below `quoted-words`, which it reads: a key whose part before its first `_` is not one letter or a Greek name is printed as a symbol written by hand would be.

// --- Words in a symbol written by hand (v0.87) -------------------------------
// A symbol is Typst math source, and in math a run of two or more letters is a **name**: the `Ed` of `G_(1,Ed)` is looked up, found nowhere, and the compile stops on «unknown variable: Ed». That is why a report had to write `"G_(1,\"Ed\")"`, a quote escaped inside a string, for the subscript every design value carries (the engineer's question, v0.86: «est-ce qu'on peut corriger cela, cela rendrait l'écriture beaucoup plus facile»). Every symbol the report writes by hand -- `#var`'s and `#eq`'s printed symbol, `#val`'s `symbol:` -- now has such a word quoted before it is stored: `G_(1,Ed)` is `G_(1,"Ed")`, `W_(y,erf)` is `W_(y,"erf")`.
//
// ⚠️ **Only a word math does not know is touched**, so what compiled before compiles to the same page: a Greek name, a symbol (`dot`, `arrow.r`), an operator (`max`, `sin`, `lim`) or a function it calls (`sqrt(x)`, `upright(R)`) keeps its meaning -- a function it names and does not call, the `mid` of `M_mid`, is a word, math printing a bare function as its own name in a monospaced face. The corollary is Typst's own and is not corrected here: `c_(pi)` is c with the subscript π, and `x_(eq)` is x with the subscript =, since `pi` and `eq` are names math knows -- `c_("pi")` is written with its quotes. Quoted text, `#` code, numbers and escapes are left as they are, and a symbol already quoted comes out unchanged, so the rewriting may be applied twice.

// Every name math mode resolves: the math module, with the symbols it re-exports -- read from Typst itself rather than listed here, so a name a later Typst adds is known the day it is added. Math mode resolves nothing else: `red`, `box` and `calc`, globals of the language, are unknown inside `eval(..., mode: "math")`, which is what this has to agree with.
#let math-names = dictionary(math)

// What a math name is made of, as Typst's lexer reads one: a letter, then letters, marks and digits -- `M1` is one name, and an unknown one, where `M 1` is a letter and a number.
#let is-word-start(c) = c.match(regex("^\\p{L}$")) != none
#let is-word-char(c) = c.match(regex("^[\\p{L}\\p{M}\\p{Nd}]$")) != none

// A quoted span, `"Ed"`, is copied whole: where it ends, past its closing quote -- an escaped quote inside it does not close it.
#let skip-quoted(cl, i) = {
  let j = i + 1
  while j < cl.len() and cl.at(j) != "\"" { j += if cl.at(j) == "\\" { 2 } else { 1 } }
  calc.min(j + 1, cl.len())
}

// Embedded code -- `#x`, `#calc.pi`, `#h(1em)` -- is copied whole: its name and fields, then every bracketed group straight after it.
#let skip-code(cl, i) = {
  let j = i + 1
  while j < cl.len() and (is-word-char(cl.at(j)) or cl.at(j) in ("_", "-", ".")) { j += 1 }
  let pairs = ("(": ")", "[": "]", "{": "}")
  while j < cl.len() and cl.at(j) in pairs {
    let (open, close) = (cl.at(j), pairs.at(cl.at(j)))
    let depth = 0
    while j < cl.len() {
      if cl.at(j) == open { depth += 1 } else if cl.at(j) == close { depth -= 1 }
      j += 1
      if depth == 0 { break }
    }
  }
  j
}

// A run of name characters from `i`, and where it ends.
#let read-name(cl, i) = {
  let j = i
  while j < cl.len() and is-word-char(cl.at(j)) { j += 1 }
  (cl.slice(i, j).join(""), j)
}

// One run of letters as math is to read it. A name math knows stays; one letter followed by a number -- the `M1` of `gamma_(M1)` -- is that letter and that number, set as math sets them, an italic M and an upright 1, where math alone read `M1` as one unknown name; anything else is the word it was meant to be, upright, as a quoted word is.
#let symbol-word(word) = {
  let cl = word.clusters()
  if cl.len() == 1 or word in math-names { return word }
  if cl.slice(1).join("").match(regex("^[0-9]+$")) != none { return cl.first() + " " + cl.slice(1).join("") }
  "\"" + word + "\""
}

// A name's modifiers after it -- `arrow.r.long`, `dot.op` -- are fields of the name, never words of their own: copied as they stand.
#let read-fields(cl, j) = {
  let out = ""
  while j + 1 < cl.len() and cl.at(j) == "." and is-word-start(cl.at(j + 1)) {
    let (field, next) = read-name(cl, j + 1)
    out += "." + field
    j = next
  }
  (out, j)
}

// One piece of a symbol from `i` -- a quoted span, an escape, code, a number, a word, or one character -- as it is to be written, and where it ends. Each case one line, and what it reads a function of its own, for the reason `read-token` gives: a long chain of branches inside a loop is what overflowed tinymist's stack in v0.60.1.
#let symbol-piece(cl, i) = {
  let c = cl.at(i)
  if c == "\"" { let j = skip-quoted(cl, i); return (cl.slice(i, j).join(""), j) }
  if c == "\\" { let j = calc.min(i + 2, cl.len()); return (cl.slice(i, j).join(""), j) }
  if c == "#" { let j = skip-code(cl, i); return (cl.slice(i, j).join(""), j) }
  // a number is copied with any letters glued to it read as a word of their own: `2ab` is 2 and ab, as math reads it
  if c.match(regex("^[0-9]$")) != none { let (n, j) = read-name(cl, i); let d = n.position(regex("\\p{L}")); return if d == none { (n, j) } else { (n.slice(0, d), i + n.slice(0, d).clusters().len()) } }
  if not is-word-start(c) { return (c, i + 1) }
  let (word, j) = read-name(cl, i)
  if not (word in math-names) { return (symbol-word(word), j) }
  // A function math knows and the symbol does not call is a word: set bare, math prints the function itself, its name in a monospaced face -- the «mid» of `M_mid`, the «norm» of a key `norm` (key-symbol).
  if type(math-names.at(word)) == function and not (j < cl.len() and cl.at(j) == "(") { return ("\"" + word + "\"", j) }
  let (fields, k) = read-fields(cl, j)
  (word + fields, k)
}

/// A symbol written by hand, with every word math does not know quoted: `G_(1,Ed)` → `G_(1,"Ed")`, `W_(y,erf)` → `W_(y,"erf")`, `gamma_(M1)` → `gamma_(M 1)`, `M_mid` → `M_"mid"`. A name math knows -- `alpha`, `dot`, `max`, `sqrt(x)`, `arrow.r` -- keeps its meaning, a function only where it is called; quoted text, `#` code and numbers are left alone; a symbol already right comes back unchanged.
/// - src (str): the symbol, as Typst math source.
/// -> str
#let quoted-words(src) = {
  if type(src) != str { return src }
  let cl = src.clusters()
  let out = ""
  let i = 0
  while i < cl.len() {
    let (piece, next) = symbol-piece(cl, i)
    out += piece
    i = next
  }
  out
}

/// The math source a registry key stands for: `k_dens` → `k_"dens"`, `mu_11` → `mu_11`, `q_(k,11)` → itself -- and, where the part before its first `_` is not one letter or a Greek name, the key read the way a symbol written by hand is read (`quoted-words`): `M2` → `M 2`, `FEd` → `"FEd"`, `Ed_max` → `"Ed"_"max"`.
/// - key (str): the key as written in #var or #eq.
/// -> str
#let key-symbol(key) = {
  // a key that is already math -- it carries a quote, a parenthesis or a space -- is used as it stands
  if key.contains("\"") or key.contains("(") or key.contains(" ") { return key }
  let i = key.position("_")
  let base = if i == none { key } else { key.slice(0, i) }
  let sub = if i == none { none } else { key.slice(i + 1) }
  // the project's own rule (section 3.1): a multi-letter subscript that is not a Greek name is quoted
  let derived = if sub == none or sub.len() <= 1 or sub in greek-names or sub.match(regex("^[0-9]+$")) != none { key }
    else { base + "_\"" + sub + "\"" }
  // A key whose first part is one letter or a Greek name -- `R_k`, `k_dens`, `gamma_M` -- is printed exactly as it always was. Any other went through math as one unknown name and stopped the compile, which is why `M2` was refused until the engineer asked for it (periodic audit 260916, AUD-7-425; «Fais la suite»): it is read now as a symbol written by hand is, a letter and a number being that letter and that number -- `M2` prints M and 2 as `gamma_(M1)` prints M and 1 -- and any other word upright, as a quoted one is.
  if base.clusters().len() == 1 or base in greek-names { derived } else { quoted-words(derived) }
}

// A key printed as its own symbol has to start with a letter: `_x` has no part before its `_` to be printed, and math reads it as a stray subscript. Every other key is printed since `key-symbol` reads it as a symbol written by hand -- `M2`, `Mx` and `FEd` were refused here until then (periodic audit 260916, AUD-7-425). Checked when the call is made, at every level: a level-0 line prints nothing and would have let the key through until a report that prints it.
#let check-printable-key(fn, key) = {
  if key.contains("\"") or key.contains("(") or key.contains(" ") { return }
  if key.starts-with("_") {
    panic(fn + ": " + repr(key) + " cannot be printed as its own symbol -- it starts with `_`, which math reads as a subscript of nothing. "
      + "Write it with a letter first, or give the printed symbol as the second argument: #" + fn + "(" + repr(key) + ", " + repr(key.trim("_", at: start)) + ", ...)")
  }
}

// `*` as a keyboard writes a multiplication, read as `dot` -- evaluated as one and printed as one, `·` in the letters line and in the numbers line (v0.87, the engineer: `show math.star: $dot$` in config.typ did not reach `#eq`, a show rule working on content and never on the string a formula is written as). Left as it is inside a quoted span, after a backslash, and where it is an attachment -- `F^*`, `F_*` -- which is a star and not a product.
#let star-as-dot(src) = {
  if type(src) != str or not src.contains("*") { return src }
  let cl = src.clusters()
  let out = ""
  let i = 0
  while i < cl.len() {
    let c = cl.at(i)
    let j = if c == "\"" { skip-quoted(cl, i) } else if c == "\\" { calc.min(i + 2, cl.len()) } else { i + 1 }
    let attached = i > 0 and cl.at(i - 1) in ("^", "_")
    out += if c == "*" and not attached { " dot " } else { cl.slice(i, j).join("") }
    i = j
  }
  out
}

// The levels a command of this file may be given: `auto` follows the report, **0 prints nothing**, and 1, 2 and 3 are the three reports of section 3.7.
//
// ⚠️ **0 is the one level that prints nothing, and every other level prints something** (v0.85, the engineer's rule in his own words: «tout autre chose que level:0 doit toujours afficher quelque chose»). Until then it was `level: 1` that hid a declaration, which put the two notions on one scale and made the *client* report -- level 1, section 3.7 -- the one report a variable written by hand never reached. They are apart now: 0 says "not on the page", 1, 2 and 3 say how much of the page it takes, and `#var` prints at level 1 exactly what it prints at level 2.
#let check-level(fn, level) = {
  if not (level == auto or level in (0, 1, 2, 3)) {
    panic(fn + ": invalid level " + repr(level) + " -- use auto, 0 (nothing printed), 1, 2 or 3")
  }
}

// --- Naming ------------------------------------------------------------------

// What a key may be made of, and what counts as "inside a word" when one is substituted.
#let name-char(c) = c.match(regex("^[A-Za-z0-9_]$")) != none

// A key is letters, digits and `_`, and never a `-`.
//
// ⚠️ The hyphen is refused rather than merely discouraged. A formula is read by substituting each known name for a token *before* it is tokenized, so a key `R-k` would win over the subtraction: in a formula that also names `R` and `k`, `R-k` would silently stop meaning "R minus k". Nothing downstream could detect that, so it is stopped here.
#let check-key(fn, key) = {
  assert(type(key) == str and key != "", message: fn + ": a name must be a non-empty string, got " + repr(key))
  assert(key.match(regex("^[A-Za-z_][A-Za-z0-9_]*$")) != none,
    message: fn + ": " + repr(key) + " is not a usable name -- letters, digits and `_` only, and never a `-`, "
      + "which a formula would read as a subtraction. Write " + repr(key.replace("-", "_")) + " instead")
  // ⚠️ The words a formula reads as an operation are refused for the hyphen's reason: a key `max` would be substituted into `max(a, b)`, and the formula would stop on «cannot be computed» with nothing to say why. Until a key such as `M2` was printed (key-symbol), `#var("max", 5)` was refused for another reason and this one never came up.
  if key == "dot" or key == "pi" or key in formula-functions {
    panic(fn + ": " + repr(key) + " is not a usable name -- a formula reads it as "
      + (if key == "dot" { "a multiplication" } else if key == "pi" { "the number π" } else { "the function " + key + "()" }) + ". Write " + repr(key + "_1") + " or another name instead")
  }
}

// `src` with every **whole-word** occurrence of `key` replaced -- **outside quotes**.
//
// Whole word, because these names are short and one is easily a piece of another: without it the key `n` would rewrite the `n` inside `ln(x)`, and `l` the `l` of `log`. (A key that is a *prefix* of another key -- `F` and `F_Ed` -- is a different problem, solved by substituting the longest first.)
//
// Outside quotes (v0.117, issue #32), because a quoted span is a unit or a text and never a name: a variable `m` rewrote the "m" of `(3 "m")`, and the line died on «cannot be computed» -- the family of the v0.86 defect below, where the key `N` rewrote the "N" of "21 N/mm²". A quoted span is copied whole, by `skip-quoted` -- the tokenizer's own rule, an escaped quote included --, so every substitution of this file (the operands found, the unknown names, the values computed, the symbols displayed) reads a quote the way the tokenizer does. A quote left open runs to the end of the formula, as it does for the tokenizer.
#let replace-word(src, key, with) = {
  let cl = src.clusters()
  let n = key.clusters().len()
  let out = ""
  let i = 0
  while i < cl.len() {
    if cl.at(i) == "\"" {
      let j = skip-quoted(cl, i)
      out += cl.slice(i, j).join("")
      i = j
      continue
    }
    let fits = i + n <= cl.len() and cl.slice(i, i + n).join("") == key
    let free-before = i == 0 or not name-char(cl.at(i - 1))
    let free-after = i + n >= cl.len() or not name-char(cl.at(i + n))
    if fits and free-before and free-after { out += with; i += n } else { out += cl.at(i); i += 1 }
  }
  out
}

// --- The unit a computed result is printed in --------------------------------
// The algebra gives a dimension; this says which unit an engineer writes it in. Without it `M_Ed / a`, kNm over mm, would print 2037.037 N -- correct, and not what anybody writes under a bench.
//
// **One unit per dimension** (v0.63), keyed by `dims-text`, and no magnitude window: what `#unit("Nmm")` asks for is what every moment comes out in, whether it is 0.5 or 5·10⁷. Until v0.62 this was a flat list tried in order, the first candidate landing between 0.1 and 1000 winning. That had one merit -- a stress printed in N/mm² and a snow load in kN/m² though they share a dimension -- and one defect that outweighed it: a unit chosen on purpose could be unreachable, 20 kNm being 2·10⁷ Nmm, outside the window, so `#unit("Nmm")` would have been quietly ignored exactly where it was asked for.
//
// ⚠️ The price is that `N/m²` is **one** dimension: a stress and a surface load share it, and the default below serves the stress, which is the commoner computed result. A line that wants the other says so -- `unit: "kN/m²"` on that call, or `#unit("kN/m²")` before the section that needs it. That is the same trade in the other direction, and this time it is the engineer's to make rather than the value's size.
// ⚠️ Written with real superscripts, `N/mm²` and not `N/mm^2`: the chosen unit is printed as a quoted word inside math, so a caret would come out on the page as a caret.
#let default-units = units-data.default_units

// The table in force where a variable is written.
//
// 👉 It lives **inside the registry's own dictionary**, under `units`, rather than in a state of its own -- and that is not tidiness, it is the same constraint that put var-domain's stack there (calc-engine.typ, above `var-registry`): `#eq` computes and stores its answer inside `var-registry.update(...)`, and the function of a state's update cannot read another state. Reading it out of the `d` it is handed is the only way `#eq` can know what `#unit` asked for. The default is given here rather than in the state's initial value so that calc-engine.typ, which knows nothing of units, does not have to.
#let unit-table(d) = d.at("units", default: default-units)

// The unit a computed result of these dimensions is printed in, or `none` for a dimension the table does not name -- a square of forces, a stiffness nobody declared -- which then falls back to base units.
#let pick-unit(dims, table) = table.at(dims-text(clean-dims(dims)), default: none)

// --- Reading a formula against the registry ----------------------------------

// The variables the registry holds that this formula actually names, longest key first so that a key which is the beginning of another cannot eat it.
#let formula-operands(d, src) = {
  var-names(d)
    .filter(key => replace-word(src, key, "\u{0003}") != src)
    .sorted(key: key => -key.len())
    .map(key => {
      let r = var-lookup(d, key)
      (key: key, symbol: r.at("symbol", default: key-symbol(key)),
       value: r.value, unit: r.at("unit", default: ""))
    })
}

// `src` with every quoted span blanked -- read by `skip-quoted`, the rule `replace-word` and the tokenizer read a quote by, so an escaped quote does not end it (v0.117, issue #32: a regex of its own here stopped at `\"`).
#let blank-quoted(src) = {
  let cl = src.clusters()
  let out = ""
  let i = 0
  while i < cl.len() {
    if cl.at(i) == "\"" { i = skip-quoted(cl, i); out += " " } else { out += cl.at(i); i += 1 }
  }
  out
}

// A word still standing once every known name has been taken out of the formula is a name the report never declared -- the one mistake this design can make, and the one it must not make in silence. A unit written inside a literal (`350 "m"`) is not a name, so quoted spans go first.
#let unknown-names(src, operands) = {
  let rest = blank-quoted(src)
  for o in operands { rest = replace-word(rest, o.key, " ") }
  let words = ()
  for m in rest.matches(regex("[A-Za-z_][A-Za-z0-9_]*")) {
    if m.text != "dot" and m.text != "pi" and m.text not in formula-functions and m.text not in words { words.push(m.text) }
  }
  words
}

// One formula, read against the registry `d`: its value as a quantity, and the operands it named. `none` where it cannot be evaluated at all.
//
// `strict` decides what an unknown word means. Normally it is a typo -- a name the report never declared -- and it stops the compile here rather than turning the whole formula into "not evaluable", which would hide that typo behind a `value:`. But a formula given its answer with `value:` is *expected* to carry words no registry holds: `integral`, `dif`, the name of a function that is only being displayed. There, an unknown word is the point and not a mistake.
#let evaluate-formula(fn, d, src, strict: true) = {
  let operands = formula-operands(d, src)
  let unknown = if strict { unknown-names(src, operands) } else { () }
  if unknown.len() > 0 {
    let known = var-names(d)
    // `value:` is eq's alone: verify has no such argument, and offering it sent the reader to a call that is refused (v0.86)
    panic(fn + ": no variable named " + unknown.map(w => repr(w)).join(", ")
      + " here -- declare it with #var(...) above this line"
      + (if fn == "eq" { ", or, for a formula meant to be displayed and not evaluated (an integral, a derivative), give its answer with value:. " } else { ". " })
      + (if known.len() == 0 { "No variable is declared yet." } else { "Declared here: " + known.join(", ") }))
  }
  let coded = src
  let values = ()
  for (i, o) in operands.enumerate() {
    coded = replace-word(coded, o.key, placeholder(i))
    let q = quantity(o.value, o.unit)
    if q == none { panic(fn + ": cannot read the unit " + repr(o.unit) + " of `" + o.key + "`") }
    values.push(q)
  }
  let tokens = tokenize(coded)
  if tokens == none { return (result: none, operands: operands) }
  let got = parse-expr(tokens, 0, values)
  if got == none or got.at(1) != tokens.len() { return (result: none, operands: operands) }
  (result: got.at(0), operands: operands)
}

// A quantity in base units, as the value and unit a report prints. `want` is the declared unit, `auto` letting the table choose; `table` is the one in force (`unit-table(d)`).
//
// Where the declared unit cannot be reached from the operands, this does **not** stop the compile (v0.63). It prints the result in the unit the operands themselves were written in -- `F` in N times `l` in mm gives Nmm, whatever unit was asked for -- and returns a `warning` the caller sets in red under the line. Three reasons for that, in order: the number printed is right whatever happens; a report that will not build teaches an engineer nothing about which of the two is wrong; and the value stored in the registry stays physically correct, so the lines below go on computing. What stays blocking is a unit that cannot be *read* at all, which is a typo and not a disagreement.
#let present(fn, symbol, parsed, want, table) = {
  // the unit the algebra itself arrives at, whichever way the declared one turns out
  let natural() = {
    let nat = natural-unit(q-nat(parsed))
    if nat != none { return (value: parsed.base / parse-unit(nat).factor, unit: nat) }
    let u = pick-unit(parsed.dims, table)
    if u != none { (value: parsed.base / parse-unit(u).factor, unit: u) }
    else { (value: parsed.base, unit: dims-text(parsed.dims)) }
  }
  if want == auto {
    if clean-dims(parsed.dims).len() == 0 { return (value: parsed.base, unit: "") }
    let u = pick-unit(parsed.dims, table)
    if u == none { return (value: parsed.base, unit: dims-text(parsed.dims)) }
    return (value: parsed.base / parse-unit(u).factor, unit: u)
  }
  let p = parse-unit(want)
  if p == none {
    panic(fn + ": cannot read the unit " + repr(want) + " of " + symbol
      + " -- write it as the report writes one, `kN`, `N/mm²`, `kNm`")
  }
  if dims-equal(parsed.dims, p.dims) { return (value: parsed.base / p.factor, unit: want) }
  let shown = natural()
  (value: shown.value, unit: shown.unit, warning: (wanted: want, natural: shown.unit))
}

// --- Printing a number ------------------------------------------------------
// A calculation written by hand reaches sizes the rest of the report does not: a second moment of area in mm⁴, a stress in N/m², a square of forces. Past 99 999 those are unreadable written out, so they are printed as a mantissa and a power of ten.
//
// 👉 Confined to this file **on purpose**. `fmt-decimals` is the primitive every other display path goes through -- show-calc, show-input, the tables, the figures -- and putting the rule there would have rewritten numbers on pages nobody asked about (a connection's I_p = 157000 mm² among them). So these three are this file's own, and `fmt-decimals` underneath them is untouched: the scientific notation reaches exactly `#var`, `#eq`, `#verify`, `#val` and `#var-unit`.
#let sci-threshold = 99999

/// A number at the document's decimals, as a mantissa and a power of ten past 99 999: `1234567` → `"1.235 · 10⁶"`.
///
/// ⚠️ The exponent is written with **superscript digits**, never `10^6`. These strings are printed inside quoted words in math -- which is what keeps a substituted operand one atom, so that `M / a` does not read as `M · (kNm/a) · mm` -- and inside quotes a caret is a caret.
/// - x (int, float, str): the value. A string passes through, a var's value being allowed to be text.
/// - digits (int): decimals, as `number-digits` sets them.
/// -> str
#let fmt-magnitude(x, digits) = {
  if type(x) != int and type(x) != float { return fmt-decimals(x, digits) }
  if calc.abs(x) <= sci-threshold { return fmt-decimals(x, digits) }
  let e = int(calc.floor(calc.log(calc.abs(x), base: 10)))
  // an exponent the rounding carries over: 999999.9 is 10.000 · 10⁵, which is 1 · 10⁶
  if calc.abs(float(fmt-decimals(x / calc.pow(10.0, e), digits))) >= 10 { e += 1 }
  fmt-decimals(x / calc.pow(10.0, e), digits) + " · 10" + sup(e)
}

// A number as it is **printed** takes the typographic minus, U+2212, for its sign and never the hyphen `fmt-decimals` and `fmt-magnitude` write (v0.87, the engineer: «un signe moins doit être affiché»): calc-engine.typ's `signed-text`, one rule for both files. Applied at the point of display and nowhere earlier, so that nothing is converted twice and every string that is read again -- math source, where math sets a hyphen as a minus by itself; the registry; an SVG -- keeps the hyphen it can parse.

// `fmt-number`'s counterpart for a value written by hand: the same line, with the scientific notation above. A value that is a word rather than a number goes through the glossary, as it does everywhere else (docs/typst/language.md §4bis). The number and its unit are joined by a no-break space, as fmt-number joins them (v0.86): a line ending on «R_d = 4.969» and the next beginning with «kN» is what a plain space allowed.
#let formula-number(value, unit, digits) = {
  let s = if type(value) == str { tl-str(value) } else { signed-text(fmt-magnitude(value, digits)) }
  if unit == "" { s } else { s + "\u{a0}" + unit }
}

// `quantity-in-formula`'s counterpart: "5.544 kN" as **quoted math source**, one atom, with a typographic minus for a sign -- quoted text keeps a hyphen where math would set a minus.
#let formula-quantity(x, unit, digits) = {
  let s = signed-text(fmt-magnitude(x, digits))
  "\"" + s + (if unit == "°" { "" } else { " " }) + unit + "\""
}

// The line a result whose declared unit the formula cannot reach carries under it (v0.63). Red and small, the colour `#verify` marks a relation that does not hold with -- the one visual language this file already has for "read this, it is not what you asked for".
#let unit-warning(warning) = {
  if warning == none { return none }
  text(fill: test-nok, size: 8pt,
    t-str("formula.unit_mismatch", wanted: warning.wanted, natural: warning.natural))
}

// --- eq ---------------------------------------------------------------------

// One operand as it is written *inside* the substituted line: its value and its unit, as **one** math atom.
//
// ⚠️ One atom is the whole point. `M / a` substituted as `0.275 "kNm" / 135 "mm"` is four atoms, and math's `/` takes the single atom on each side of it: the line then reads 0.275 · (kNm/135) · mm -- a printed formula that does not state what was computed, which is the one thing this file exists to prevent (v0.60.1). So a value that carries a unit is quoted whole, the way `#test` writes its two sides (`quantity-in-formula`), which also turns a leading `-` into a typographic minus. A value without a unit is a bare number, math already, parenthesised where it is negative so that `a - b` never reads `a - -b` -- `value-in-formula`'s rule, which `show-calc` applies for the same reason.
//
// 👉 `show-calc` has no such case: it substitutes the bare number and lets the result carry the unit at the end of the line. `eq` cannot, its whole subject being operands whose units differ.
#let substituted(value, unit, digits) = {
  if type(value) != int and type(value) != float { return "\"" + str(value) + "\"" }
  if unit != "" { return formula-quantity(value, unit, digits) }
  let s = fmt-magnitude(value, digits)
  if value < 0 { "(" + s + ")" } else { s }
}

// A formula as it is printed twice over: in letters, every key replaced by its symbol, and in numbers, every key replaced by its value and unit -- the two lines `#eq` prints, and the two `#verify` prints of a side that is a whole expression.
//
// ⚠️ Every key is replaced by a placeholder first and the placeholders expanded after, as evaluate-formula does: substituted one after the other, a key `N` rewrote the "N" inside the "21 N/mm²" `f_c` had just become, and the line died on «unknown variable: kN» -- at level 3 only, so in the checking report alone (v0.86).
// A symbol as **one atom** of the formula it is put into. A symbol that is several atoms side by side -- `M 2`, which the key `M2` is printed as (key-symbol), or a `Delta h` written by hand -- would otherwise lend only its last atom to the operator after it: `M 2 / a` is set as M times 2/a, a fraction the formula does not state. `class("normal", …)` groups it without printing anything, and a symbol that is one atom already is left exactly as it was.
#let atom-symbol(s) = {
  let cl = s.clusters()
  let depth = 0
  let i = 0
  while i < cl.len() {
    let c = cl.at(i)
    if c == "\"" { i = skip-quoted(cl, i); continue }
    if c == "#" { i = skip-code(cl, i); continue }
    if c in ("(", "[", "{") { depth += 1 } else if c in (")", "]", "}") { depth -= 1 }
    else if c == " " and depth == 0 { return "class(\"normal\", " + s + ")" }
    i += 1
  }
  s
}

#let formula-lines(src, operands, digits) = {
  let coded = src
  for (i, o) in operands.enumerate() { coded = replace-word(coded, o.key, placeholder(i)) }
  // the short names of the inverse functions are printed as math knows them (formula-display-names)
  for (short, long) in formula-display-names { coded = replace-word(coded, short, long) }
  let letters = coded
  let numbers = coded
  for (i, o) in operands.enumerate() {
    letters = letters.replace(placeholder(i), atom-symbol(o.symbol))
    numbers = numbers.replace(placeholder(i), substituted(o.value, o.unit, digits))
  }
  (letters, numbers)
}

// --- The commands -------------------------------------------------------
// `var` writes a variable down, `eq` computes one from the others, `verify` states a relation between them, `var-unit` carries one into another unit, `unit` says which unit a whole dimension is printed in, and `var-domain` keeps two sets of variables apart. Between them the report never names a variable twice: the string given to `var` is the key a formula cites and, unless a second one is given, the symbol that is printed.
//
// Each of those that store something is **two pieces of content**: a `var-registry.update(...)`, then a `context` that reads the registry back and prints. The order matters and is the whole mechanism -- an update is a pure function of the dictionary, so the arithmetic runs there without reading a state, and the `context` placed after it sees the result. Reading and writing one state from inside one `context` is what Typst cannot be asked to do.
//
// ⚠️ And the corollary, which cost a silent refusal in v0.63: the function of an update runs **only where something reads that state**. A `panic` written inside one is silent in a document that never looks the registry up again -- so a check that must always fire belongs in the `context`, which is where `var-unit` refuses a name it cannot find and where `eq` reads the registry at every level.

// --- A row of variables (docs/typst/formulas.md §10quinquies) ---------------------
// `var-line` sets several declarations on one line -- "R_k = 7 kN; k_dens = 0.806; gamma_M = 1.7" -- the way `show-calc` sets the vars of a `group` (section 3.3). Each `#var` keeps every argument it has; what the row adds is the **joining**, and that is the whole reason it is a container rather than an `inline: true` flag on each command:
//
//   * the separator is written by the engine, so a value hidden by its level takes its separator with it, where hand-typed commas would be left behind -- and a `;` is never typed after a `#var(...)`, where Typst swallows it as the end of the expression;
//   * the row carries one label, like a var's `group_label`, and one citation in the right-hand column, which is a grid and so cannot be reached from inside a line;
//   * a label and a citation of an item's own become **one footnote**, since neither can be set after an em dash in the middle of a line (section 9's rule for a description and its choices, applied to a row).
//
// The state is what tells a command inside a row from one printing on a line of its own: `none` outside, and inside a dictionary carrying how many items the row has printed, the row's label, its separator and its level. Every command reads it in the `context` it already prints from, so a row passes nothing as an argument.
#let var-line-state = state("var-line", none)

// A space and a paragraph break, as the children of a content block report themselves. ⚠️ Compared by the *name of the element function*: `space` and `parbreak` are elements a markup block produces and neither is a binding this file could name.
#let line-filler = ("space", "parbreak")

// One item of a row: the separator the row is joined with -- or the row's label, before the first item -- and then the item. The count lives in the state, which is what makes a hidden item take its separator with it.
#let line-item(st, item) = {
  if st.count > 0 {
    [#(if st.sep == auto { semicolon-str() } else { st.sep })]
    h(0.5em)
  } else if st.label != none {
    [#tl-str(st.label)#colon-str()]
    h(0.35em)
  }
  item
  var-line-state.update(s => if s == none { s } else { (count: s.count + 1, label: s.label, sep: s.sep, level: s.level) })
}

// The level one command prints at: the row's, where the row states one, and the command's own otherwise -- a row's level is what hides a whole line of declarations at once. `--input uniform=N` still wins, resolve-level reading it last. (v0.117's level of a whole calculation domain, set by `#show-formula`, went with that command: a domain of the «Formules» tab is printed by `#include`, each command at its own level -- issue #15.)
#let line-level(st, level) = resolve-level(if st != none and st.level != auto { st.level } else { level })

// What a value carries beside itself when it is printed inline -- inside a row, or in a sentence: its label from level 2, its choices with it, and its citation from level 3, as **one** footnote. One footnote and not three: three markers side by side read as one three-digit number rather than as three references (section 9).
//
// `extra` is a sentence printed at **every** level and set before the rest -- today the orange line `val` writes under a value shown in another unit than the one it carries. `colour` is the colour of the footnote's own marker, so that such a value is marked in the text and not only at the foot of the page (v0.80, the engineer's request).
// `with-label`, `with-descr` and `with-norm` are what let a line that already has somewhere to put them ask for the rest: a block line sets its label after an em dash and its citation in the right-hand column, so its footnote carries the description alone (v0.85.2); `#val(note: "line")` sets its description in parentheses as well, so its footnote carries at most the choices and the orange line (v0.86).
#let line-note(record, lv, extra: none, colour: none, with-label: true, with-descr: true, with-norm: true) = {
  let parts = ()
  if extra != none { parts.push(extra) }
  // What the variable *is* comes first, then why this value was chosen: a label and a description are two fields in the data (section 3.1) and two different sentences, and the registry has carried both since v0.85.1.
  //
  // ⚠️ And they are printed at **different levels** (v0.85.2, the engineer's rule): the label at 2, because a number wants the word that names it as soon as it is shown; the description and the `choices` it explains at 3, with the citation, because why *this* value was chosen is what a checker reads and a level-2 report does not. Level 3 is therefore complete -- label, description, norm and norm-ref, in that order.
  let said = if with-label { record.at("label", default: none) } else { none }
  if lv >= 2 and said != none { parts.push(render-prose(tl-str(said))) }
  let descr = if with-descr { record.at("description", default: none) } else { none }
  if lv >= 3 and descr != none { parts.push(render-prose(tl-str(descr))) }
  let choices = record.at("choices", default: none)
  if lv >= 3 and choices != none {
    // A choice goes through the glossary like every other string the data carries: the norm's own wording follows the report's language, a value the workbook alone names is left as it was.
    parts.push(choices.map(c => [#render-symbol(record) = #render-prose(tl-str(c.value))#colon-str() #render-prose(tl-str(c.desc))]).join(linebreak()))
  }
  if with-norm and lv >= 3 and record.at("norm", default: none) != none { parts.push(norm-text(record)) }
  // Joined with the engine's own semicolon, which carries French's narrow space before it: a label and a citation set one after the other with nothing between them read as one sentence («Kapazität Sherpa XS Sherpa §ETA-12/0197»).
  let joined = parts.join([#semicolon-str() ])
  // ⚠️ A thin space before the marker: set flush after a unit it read as one more exponent -- «kN/m²³» -- which is what step-rows' own h(0.35em) already prevents (v0.86).
  if parts.len() == 0 { none }
  else if colour == none { [#h(0.2em)#footnote(joined)] }
  // The marker takes the colour, the sentence inside carries its own: a footnote's body is laid out at the foot of the page and does not inherit this, which is what lets the label and the citation beside the orange line stay in the text's own ink.
  else { [#h(0.2em)#text(fill: colour, footnote(joined))] }
}

// Where a value's extras go -- its label, its description and its citation -- when it stands on its own rather than in a `var-line` (v0.87, the engineer: «un argument permet de régler si la note vient en ligne ou en note de bas de page», on `#var`, `#val` and `#eq`). `"footnote"` gathers the three into the **one** footnote `line-note` builds, which is what a value in a sentence needs; `"line"` sets them on the line, as a block line has always set them -- the label after an em dash, the description a footnote, the citation in the right-hand column (`#val`, which has no column, sets the description and the citation in parentheses after its label). Inside a `var-line` it has no effect: a row has one citation column for all of it, and its items take one footnote each.
#let note-modes = ("footnote", "line")

#let check-note(fn, note) = {
  if not (note in note-modes) {
    panic(fn + ": invalid note " + repr(note) + " -- use " + note-modes.map(m => repr(m)).join(" or ")
      + ": \"footnote\" puts the label, the description and the citation in one footnote, \"line\" sets them on the line")
  }
}

// `sep:` (v0.117, the engineer: «l'option ... serait un argument de var», spec 2026-10-11-argument-sep-var): the separator a value printed **inline** is followed by -- `#var("b", 208, "mm", sep: ";")` where `#var(...) ;` was typed until a `;` after a call made its line a text. It is printed with the value, after its footnote, so a value its level hides takes its separator with it -- what `var-line` was made for. Refused where there is nothing to separate: a value on a line of its own (`note: "line"`), and a value in a `var-line`, which writes its own separators (`check-sep-row`, read in the context where the row is known).
#let check-sep(fn, sep, note) = {
  if sep != none and value-type(sep) != str {
    panic(fn + ": sep: is the separator printed after the value, a string -- \";\", \",\" -- got " + repr(sep))
  }
  if sep != none and note == "line" {
    panic(fn + ": sep: " + repr(sep) + " separates values printed inline, and note: \"line\" sets this one on a line of its own, with no neighbour to separate it from -- drop one of the two")
  }
}

#let check-sep-row(fn, st, sep) = {
  if sep != none and st != none {
    panic(fn + ": sep: " + repr(sep) + " inside a var-line, which writes its own separator between its items -- drop it here, or give the row var-line(sep: ...)")
  }
}

// What follows a value printed inline: its separator, glued to it as a `;` is to the word before it -- the space after it is the line break of the source, as between any two values written one under the other.
#let sep-after(sep) = if sep == none { none } else { [#sep] }

// One value set inline: the value, its footnote marker, and the red line of a unit it could not be carried into -- set a space apart, where glued to the value it read as part of it.
#let inline-item(value, note, warning) = {
  value
  if note != none { note }
  if warning != none { h(0.3em); warning }
}

// The double rule a result a section ends on is set with: two nested boxes, each drawing a bottom rule, and not two nested `underline`s -- an underline decorates the text runs it finds, so inside an equation it comes out under the units and not under the numbers between them (the same finding `verify` records). The weight and the two insets are verify's own, so a doubly ruled answer and a relation that holds are marked alike; the ink is the document's, where verify's says whether it holds. Read by `#eq`'s `style: "double"` through its eval's scope, and by `apply-style` for the three commands that print one value.
#let double-rule(x) = {
  let rule = (bottom: 0.9pt)
  box(stroke: rule, inset: (bottom: 1.7pt), outset: (x: 1pt),
    box(stroke: rule, inset: (bottom: 3.4pt), x))
}

// `style:` applied to a line already built -- `#var`, `#var-unit` and `#val`, which print `symbol = value unit` as content and not as math source (v0.100, the engineer: «ajoute à #var l'argument style comme pour #eq»). ⚠️ The whole expression is wrapped and not the value alone, which is what he asked for: `R_k = 7 kN` comes out bold, ruled or underlined entire.
//
// ⚠️ It is the content that is handed to the eval, through its **scope**, where `#eq` splices a math *source* string into its chain. The two cannot be one: eq's tail is a string it builds itself, while this line is content carrying the no-break spaces that keep a symbol with its value across a line break (v0.87) -- rebuilding it as one source string would put a relation where a line may break, and `R_k =` would be left at the end of a line with `7 kN` on the next. Passing it through the scope keeps both: any math function may still be named, as in eq, and the nbsp survive.
//
// ⚠️ The scope name is a **bare word of two letters or more, with neither hyphen nor underscore**: in math a single letter is that letter and never a lookup (`v` printed as an italic v), a hyphen is a minus and an underscore a subscript. Found by compiling all three.
#let apply-style(style, body) = {
  if style == none { return body }
  eval((if style == "double" { "dbl" } else { style }) + "(printed)",
    mode: "math", scope: (printed: body, dbl: double-rule))
}

#let var-argument-names = ("domain", "label", "descr", "level", "norm", "norm-ref", "note", "sep", "style", "summary")

// A value carried from one unit into another: the number as `to` writes it, or -- where the two are not the same dimension -- the value left exactly as it was, with the warning the caller prints in red. The one piece of arithmetic `#var`, `#var-unit` and a data value handed a unit all share.
//
// A unit that cannot be *read* stops the compile here: that is a typo, not a disagreement between two units.
#let converted(fn, symbol, value, from, to) = {
  let b = parse-unit(to)
  if b == none {
    panic(fn + ": cannot read the unit " + repr(to) + " of " + symbol
      + " -- write it as the report writes one, `kN`, `N/mm²`, `kNm`")
  }
  let a = parse-unit(from)
  if a == none { panic(fn + ": cannot read the unit " + repr(from) + " of " + symbol) }
  // a value that is a word -- a load model's name -- has nothing to convert
  if type(value) != int and type(value) != float { return (value: value, unit: to, warning: none) }
  if not dims-equal(a.dims, b.dims) {
    return (value: value, unit: from, warning: (wanted: to, natural: from))
  }
  (value: value * a.factor / b.factor, unit: to, warning: none)
}

// The value and unit a `#var` was given: a number with the unit beside it, or a var object -- from `var-of(...)`, from an earlier `#var`, or from an `#eq` -- which carries both already.
//
// A var object also carries its own **symbol**, and it is kept unless the call states one: a value taken out of the export is printed as `data/` spells it, `q_(k,11)` and all, while the key stays whatever a formula can cite. That is the two-name case arriving on its own, and it is the usual one for `#var("ak", var-of("dead-load", "EL+AL-Vordach", "ak"))`.
#let var-record(key, symbol, raw, unit, label, descr, norm, norm-ref) = {
  let unit = written-unit(unit)
  // a symbol the call states is written by hand, and its words are quoted (quoted-words); one a var object brings is the data's and is already math
  let symbol = quoted-words(symbol)
  if type(raw) == dictionary and "value" in raw {
    // ⚠️ A unit given beside a value that carries one of its own **converts** it (v0.63): `#var("F", var-of(...), "N")` on a value the export holds in kN prints 7000 N, not "7 N". Until v0.63 it replaced the label and left the number alone, which is the one thing this whole file exists to prevent -- and it did it silently, on a value read from the workbook.
    let have = raw.at("unit", default: "")
    let carried = if unit == none or unit == have {
      (value: raw.value, unit: if unit != none { unit } else { have }, warning: none)
    } else {
      converted("var", key, raw.value, have, unit)
    }
    return (
      value: carried.value,
      unit: carried.unit,
      warning: carried.warning,
      symbol: if symbol != none { symbol } else { raw.at("symbol", default: key-symbol(key)) },
      // ⚠️ Two fields, not one (v0.85.1). `label` is what the variable *is* -- «Expositionsbeiwert» -- and `description` is why this value was chosen, which carries the `choices` with it (sections 3.1, 9). Until v0.85.1 `#var`'s `label:` was stored as `description`, a leftover from v0.80 renaming `descr:` to `label:` without renaming the field, and a var object read out of the export therefore had its **label dropped**: `#var("ce", var-of("snow-load", "SL", "ce"))` printed the sentence about the wind exposure and never the word «Expositionsbeiwert».
      label: if label != none { label } else { raw.at("label", default: none) },
      description: if descr != none { descr } else { raw.at("description", default: none) },
      norm: if norm != none { norm } else { raw.at("norm", default: none) },
      // `norm-ref:` given alone replaces the clause and keeps the norm: it was read only beside a `norm:`, so `#var("ce", domain: …, norm-ref: "5.2.3")` printed the export's own clause (v0.86)
      norm_ref: if norm != none or norm-ref != "" { norm-ref } else { raw.at("norm_ref", default: "") },
      // the choices a description explains travel with it: `val` printed them and `var` of the same var object did not (v0.86)
      choices: raw.at("choices", default: none),
      source: raw.at("source", default: none),
    )
  }
  assert(type(raw) == int or type(raw) == float,
    message: "var: the value of `" + key + "` is " + str(type(raw))
      + " -- write the number, or a var object (var-of(...)); a variable the report declared is read with domain:, or computed with #eq")
  (
    value: raw, unit: if unit == none { "" } else { unit }, warning: none,
    symbol: if symbol != none { symbol } else { key-symbol(key) },
    label: label, description: descr, choices: none, norm: norm, norm_ref: norm-ref, source: none,
  )
}

/// Writes one variable down: it is stored under `key`, where every formula below can name it, and printed -- **inline**, `symbol = value unit`, like a word of the sentence it stands in, so that several written one after the other run on in one paragraph and a blank line starts a new one.
///
/// ```typ
/// #var("R_k", 7, "kN")
/// ```
///
/// ```typ
/// Der Querschnitt misst #var("b", 100, "mm") auf #var("h", 200, "mm"), bei #var("k_dens", 0.806).
/// ```
///
/// ```typ
/// #var("q_k11", "q_(k,11)", 1.729, "kN/m²")
/// ```
///
/// ```typ
/// #var("s_k", var-of("snow-load", "SL", "s_k"))
/// ```
///
/// A value written down somewhere else is named the way `val` names it, with `domain:` -- a **pair** being a calculation of the export and its instance, a **string** a `var-domain` of the report. The first is the short form of `#var("R_d", var-of("connector", "SD-10", "R_d"))`, and the two store exactly the same thing:
///
/// ```typ
/// #var("s_k", domain: ("snow-load", "SL"))
/// ```
///
/// The second is what carries a result out of the column that computed it, so that a `#verify` below can name it -- a formula reads the current domain and the default one, and nothing else:
///
/// ```typ
/// #var-domain("Ende")[ #var("F", 0.55, "kN") ]
/// #var("F", domain: "Ende")
/// ```
///
/// At `level: 0` the variable is written down and nothing is printed, so that a formula below can name a coefficient the page does not show:
///
/// ```typ
/// #var("k_dens", 0.806, level: 0)
/// #var("R_k", 7, "kN", level: 0)
/// #eq("R_d", `k_dens dot R_k`)
/// ```
///
/// Its label, its description and its citation go into **one footnote** by default. `note: "line"` sets them on the line instead, the line then a block of its own: the label after an em dash, the description a footnote, the citation in the right-hand column.
///
/// ```typ
/// #var("R_k", 7, "kN", label: "Kapazität Sherpa XS", descr: "Aus dem Katalog des Herstellers", norm: "Sherpa", norm-ref: "ETA-12/0197", note: "line", level: 3)
/// ```
///
/// Values printed one after the other on a line are told apart by `sep:`, the separator written after the value it follows -- and printed with it, so a value its level hides takes its separator with it:
///
/// ```typ
/// #var("b", 208, "mm", sep: ";")
/// #var("t", 8.5, "mm", sep: ";")
/// #var("epsilon", 124)
/// ```
///
/// ```typ
/// #var("a", 145, "mm", sep: ";")
/// #var("r", 27, "mm", sep: ";")
/// #eq("b_2", `a - r`)
/// ```
///
/// The line may be set apart the way `#eq` sets an answer: `style:` names a math function applied to the whole of it -- `symbol = value unit`, and not the value alone -- or `"double"`, which rules it twice underneath, for a value a section rests on.
///
/// ```typ
/// #var("R_d", 4.969, "kN", style: "bold")
/// ```
///
/// A symbol written by hand may carry its words unquoted: `W_(y,erf)` is printed as `W_(y,"erf")` would be, a word math does not know being quoted before it is evaluated (`quoted-words`).
///
/// ```typ
/// #var("W_y_erf", "W_(y,erf)", 12.5, "cm³")
/// ```
///
/// ⚠️ There is no `#let`: Typst gives a function no way to bind a name in its caller's scope, so the name is the string, and the registry is where it lives (see `var-registry`). Read one back with `val`, not with a binding.
/// - key (str): the name a formula cites. Letters, digits and `_`; never a `-`, which a formula would read as a subtraction, nor a word a formula reads as an operation -- `dot`, `max`, `sqrt`. Where no symbol is given it is printed as a symbol written by hand would be: `k_dens` as k with the subscript "dens", `M2` as M and 2, `FEd` as one word.
/// - ..rest (any): the positional tail, whose three slots are the bullets below -- the optional printed symbol, the value, then its optional unit, in that order. Variadic only because Typst has no optional positionals; every *named* argument is declared, so an editor shows them all.
/// - symbol (str): optional second positional argument, the math source that is *printed* -- `"q_(k,11)"`. A word math does not know may be written without its quotes, `"W_(y,erf)"`. Left out, the key itself is printed, requoted by `key-symbol` so `"k_dens"` comes out as k with the subscript "dens".
/// - value (int, float, dictionary): the number, or a var object which brings its own unit and description.
/// - unit (str): optional, after the value. No unit given means the variable has none.
/// - domain (none, str, array): where the value is read. A **pair** is a calculation of the export and its instance -- `("snow-load", "SL")`, `("connector", "SD-10")` -- and falls back to the `var-domain` named after that instance for a name the export does not carry, which is where `show-polar-moment` puts the forces it computed and what `find` lists under the same pair; a **string** is a `var-domain` of the report, and the variable is copied out of it into wherever this line stands. Either way the var of this same `key` is what is taken, with its unit, its symbol, its description and its citation, so nothing is written beside it -- `label:`, `norm:` and `norm-ref:` still override what it carries. To store it under another name, or to convert it, name it the long way: `#var("R", var-of("connector", "SD-10", "R_d"), "N")`.
/// - label (str, none): what the value is -- «Expositionsbeiwert» -- printed from level 2: in the footnote, or with `note: "line"` on the line after the unit, set apart by an em dash. It **overrides** the label a var object carries.
/// - descr (str, none): why *this* value was chosen, printed in the footnote from level 3, which is section 9's own form for it. The other half of what was one field until v0.85.1; it overrides the description a var object carries, and is the argument `descr:` named before v0.80, given back its own meaning rather than the label's.
/// - level (int, auto): 0 prints nothing (the variable is still stored, and `#find(object: "variable")` is what shows it), 1 the symbol, value and unit, 2 also the label, 3 also the description and the citation. auto follows the report (section 4).
/// - norm (str, none), norm-ref (str): the citation, printed from level 3: in the footnote, or with `note: "line"` in the right-hand column.
/// - style (str, none): a math function applied to the **whole line**, `symbol = value unit` -- `"bold"`, `"underline"` -- or `"double"`, which rules it twice underneath in the document's own ink, the mark `verify` sets a relation with, for a value a section rests on. `#eq`'s own argument (v0.100); ⚠️ a line it is given is set with math's own spacing around its `=`, a little wider than a line without it.
/// - note (str): where the label, the description and the citation go. `"footnote"` (the default) prints the variable inline and gathers the three into one footnote; `"line"` prints it on a line of its own, the label after an em dash, the description a footnote and the citation in the right-hand column. No effect inside a `var-line`, whose items are always inline with one footnote each.
/// - sep (str, none): the separator printed after the variable when it is printed inline -- `";"`, `","` --, glued to it, and hidden with it by its level. Refused with `note: "line"` and inside a `var-line`, which writes its own.
/// - summary (bool): lists this variable in a summary table (`show-load-summary`, `show-line-load-summary`), which is how a load the export does not carry -- a line load, a load read off a manufacturer's table -- reaches one. **Its unit decides which table**: kN/m² an area load, kN/m a line load, any other unit refused naming the two, where the table is printed. It changes nothing about how the line itself prints, so a declaration at `level: 0` is listed like any other.
/// -> content
#let var(key, ..rest, domain: none, label: none, descr: none, level: auto, norm: none, norm-ref: "", note: "footnote", sep: none, style: none, summary: false) = {
  // ⚠️ The named arguments are declared one by one rather than swept into `..rest`, and that is what an editor reads: a function whose whole signature is `..args` shows as `var(args: arguments)` in a tooltip, and `label:`, `level:`, `norm:` and `norm-ref:` are then invisible to the engineer writing the call (v0.63.1, from a screenshot of `#eq`'s own tooltip). Only the *positional* tail stays variadic, because the printed symbol is an optional second positional and Typst has no optional positionals.
  // ⚠️ `panic` inside an `if`, not `assert(cond, message: ...)`: Typst builds an assert's message *before* it tests the condition, so `unknown.first()` on an empty array fails every correct call.
  let unknown = rest.named().keys()
  if unknown.len() > 0 {
    panic("var: unknown argument " + repr(unknown.first())
      + " -- " + var-argument-names.map(n => repr(n)).join(", "))
  }
  check-key("var", key)
  check-level("var", level)
  check-note("var", note)
  check-sep("var", sep, note)

  // `domain:` says where the value is read and hands it over as if it had been written positionally (v0.85): `#var("R_d", domain: ("connector", "SD-10"))` and `#var("R_d", var-of("connector", "SD-10", "R_d"))` store the same record, which is what makes the two spellings one command rather than two.
  //
  // ⚠️ The two shapes are read in different places, and that is why a string runs a path of its own below. A **pair** is the export: a plain json read, so it can be made here and turned into a positional like any other value. A **string** is a `var-domain`, which lives in the registry -- a state, which nothing outside a context may read -- so its record is built **inside the update**, which is handed the dictionary itself, exactly as `#eq` computes its answer there; the line then prints what it reads back. Until v0.85 the string was refused for want of that second path.
  if domain != none and rest.pos().len() > 0 {
    panic("var: " + repr(key) + " takes its value from domain: " + repr(domain)
      + ", so there is nothing to write beside it -- drop one of the two")
  }
  let pair = domain != none and value-type(domain) == array
  if domain != none and not pair and value-type(domain) != str {
    panic("var: domain: is a var-domain of the report (\"Gelenkige Verbindung\") or a calculation and its instance ((\"snow-load\", \"SL\")) -- got " + repr(domain))
  }
  if pair and domain.len() != 2 {
    panic("var: domain: names a calculation and its instance, two of them ((\"snow-load\", \"SL\")) -- got " + repr(domain))
  }
  let exported = if pair { find-calculation("var", domain.at(0), domain.at(1)).vars } else { (:) }
  // ⚠️ A pair the export does not carry falls back to the **var-domain named after its instance** (v0.85), which is where `show-polar-moment` publishes the forces it worked out (section 3.3quinquies) -- and which `find` already lists under that very pair. Without the fallback the two commands disagreed about what `("connection", "VU-MP-1")` holds: the table named F_max and this refused it. The export wins a name both carry, being the traced one.
  let from-domain = (domain != none and not pair) or (pair and not (key in exported))
  let source-domain = if pair { domain.at(1) } else { domain }
  let pos = if domain == none or from-domain { rest.pos() } else { (exported.at(key),) }
  let record = if from-domain { none } else {
    assert(pos.len() >= 1, message: "var: write #var(\"key\", value) at least, optionally #var(\"key\", \"symbol\", value, \"unit\")")
    // The first of them is the printed symbol when it is a string: a *value* is a number or a var object, never a string, so the two can never be confused. `none` here means "not stated", and var-record then takes the symbol the value brought with it, or the key.
    let has-symbol = type(pos.at(0)) == str
    let symbol = if has-symbol { pos.at(0) } else { none }
    let after = if has-symbol { pos.slice(1) } else { pos }
    assert(after.len() >= 1, message: "var: `" + key + "` has a symbol but no value")
    // a var object carries its own symbol, and then the key is never printed
    if not has-symbol and not (type(after.at(0)) == dictionary and "symbol" in after.at(0)) { check-printable-key("var", key) }
    var-record(key, symbol, after.at(0), after.at(1, default: none), label, descr, norm, norm-ref)
  }

  // The document this line rests on, for the bibliography (lib/bibliography.typ, v0.99): the citation the record ends up carrying -- the `norm:` written here, else the one a var object of the export brought with it. ⚠️ Emitted **here**, before the context below, exactly as the registry's own update is: a state written inside a context is not read back by the folded chain an update function reads (section 3.3quinquies). ⚠️ And it follows the *record* and not the level: whether the clause is printed is a matter of level, whether the document is a source is not, so a value declared at level 0 and used by the formula under it still names its norm.
  bib-note(if record == none { norm } else { record.at("norm", default: norm) })

  // ⚠️ A name the var-domain does not hold stores nothing here rather than panicking: the function of a state update runs only where something reads that state, so a refusal written here would be silent in a document that never looks the registry up again (the finding `var-unit` records). The context below always runs, and is where it is refused.
  if from-domain {
    var-registry.update(d => {
      let src = d.domains.at(source-domain, default: (:))
      if key in src { summary-mark(var-store(d, key, var-record(key, none, src.at(key), none, label, descr, norm, norm-ref)), summary, key) } else { d }
    })
  } else {
    var-registry.update(d => summary-mark(var-store(d, key, record), summary, key))
  }
  context {
    let held = if not from-domain { record } else {
      let d = var-registry.get()
      let declared = d.domains.keys().filter(k => k != "")
      // A pair got here because the export has no such name, so its own list belongs in the refusal: the reader asked one question and both places have to answer it.
      let carried = if not pair { "" } else {
        source-label(domain.at(0), domain.at(1)) + " carries " + exported.keys().join(", ") + ", and "
      }
      let published = if not pair { "" } else {
        " A polar moment publishes its forces where show-polar-moment has already run above this line (F_max, F_1 …, beta_1 …)."
      }
      if not (source-domain in d.domains) {
        panic("var: " + carried + "no var-domain " + repr(source-domain) + " is declared above this line -- "
          + (if declared.len() == 0 { "none is" } else { "declared: " + declared.map(k => repr(k)).join(", ") })
          + "." + (if pair { published } else { " A calculation of the export is named as a pair, (\"snow-load\", \"SL\")" }))
      }
      if not (key in d.domains.at(source-domain)) {
        panic("var: " + carried + "the var-domain " + repr(source-domain) + " declares no " + repr(key)
          + " -- it declares: " + d.domains.at(source-domain).keys().join(", ") + "." + published)
      }
      var-lookup(d, key)
    }
    let st = var-line-state.get()
    check-sep-row("var", st, sep)
    let lv = line-level(st, level)
    // Level 0 and nothing else prints nothing: a declaration that belongs on no page says so with a level of its own, where until v0.85 it said it with `level: 1` and so vanished from the client report alone.
    if lv >= 1 {
      // joined by no-break spaces: inline, a variable is one word of its sentence, and a line ending on «a» with «= 2 m» on the next is what plain spaces allowed -- formula-number already keeps the number with its unit
      let value = apply-style(style, [#eval(held.symbol, mode: "math")~=~#formula-number(held.value, held.unit, number-digits.get())])
      let warning = unit-warning(held.at("warning", default: none))
      if st == none and note == "line" {
        // The label is set **on the line**, after the unit, and not as a footnote: a variable's label is what that variable *is*, so it is read with it (v0.61.1, the engineer's own correction). An em dash sets it apart, which is how a position's line (#member's at level 1) and show-connector print theirs. It still goes through render-prose, so a symbol written between dollars comes out as math (section 4bis).
        // The label after an em dash, the description in a footnote: the first is what the variable *is* and is read with it (v0.61.1, the engineer's own correction), the second is why this value was chosen and is section 9's footnote. Neither is the other's level -- 2 and 3 (v0.85.2).
        let extra = line-note(held, lv, with-label: false, with-norm: false)
        let line = [
          #value#if lv >= 2 and held.at("label", default: none) != none [ --- #render-prose(tl-str(held.label))]#if extra != none [#extra]
        ]
        // The citation stands in the right-hand column from level 3 and not before: one scale for the three commands that print a single value -- 1 the value, 2 what it is, 3 where it comes from (v0.85.1, the engineer's rule). Until then it was printed at every level, so a client report carried «SIA 265 §6.2.1» beside a bare number and nothing saying what the number was.
        let cite = if lv >= 3 and held.norm != none { held } else { none }
        annotated-rows(((line, cite),))
        if warning != none { warning }
      } else {
        // Inline, which is the default since v0.87 (the engineer: «de base, #var doit s'afficher inline, afin de pouvoir afficher plusieurs var les uns après les autres») and what a row has always been: there is no em dash to hang the label on and no column for the citation, so both go into the one footnote `line-note` builds, with the description between them.
        let item = inline-item(value, line-note(held, lv), warning)
        if st == none { item + sep-after(sep) } else { line-item(st, item) }
      }
    }
  }
}

/// Converts a variable already declared into another unit, and prints it as `#var` does: `#var-unit("R", "N")` turns the 7 kN it holds into 7000 N, inline.
///
/// ```typ
/// #var("F", 7, "kN")
///
/// #var-unit("F", "N")
/// ```
///
/// ```typ
/// #var("A", 0.12, "m²")
///
/// #var-unit("A", "mm²")
/// ```
///
/// A value taken out of the export, carried into the unit the report wants to print it in -- the polar moment is exported in mm² and read in cm²:
///
/// ```typ
/// #var("I_p", var-of("connection", "VU-MP-1", "I_p"))
///
/// #var-unit("I_p", "cm²")
/// ```
///
/// At `level: 0` the conversion is made and nothing is printed, so that the lines below read the variable in its new unit:
///
/// ```typ
/// #var("F", 7, "kN", level: 0)
/// #var-unit("F", "N", level: 0)
/// Die Kraft beträgt #val("F", type: "expression").
/// ```
///
/// Its line being `#var`'s, it takes `#var`'s `style:` too -- the whole of it set bold, underlined or ruled twice:
///
/// ```typ
/// #var("F", 7, "kN", level: 0)
///
/// #var-unit("F", "N", style: "bold")
/// ```
///
/// It prints, which is why it is called `var-unit` and not `change-unit`: its line is `#var`'s line, inline and with one footnote unless `note: "line"` says otherwise, and the two read as one pair. From here on every formula that names it substitutes the new unit, and `#val` gives it.
///
/// Its `label:`, `descr:`, `norm:` and `norm-ref:` are `#var`'s: given, they **override** what the variable carries -- stored with it, so every line below reads them too -- and they are printed by the same levels, in the one footnote or, with `note: "line"`, on the line:
///
/// ```typ
/// #var("I_p", var-of("connection", "VU-MP-1", "I_p"), level: 0)
/// #var-unit("I_p", "cm²", label: "Polares Trägheitsmoment", descr: "In cm² für den Vergleich mit dem Handbuch", norm: "bauforumstahl", level: 3)
/// ```
///
/// A unit of another dimension leaves the variable exactly as it was and says so in red beside it, as `#eq` does with an unreachable `unit:` -- a conversion nobody can perform is a disagreement to read, not a build to stop. A unit that cannot be *read*, and a name the registry does not hold, do stop it.
/// - key (str): the variable's name, as `#var` stored it.
/// - unit (str): the unit to carry it into. The same dimension, or the line comes out red.
/// - label (str, none): what the value is, printed from level 2 as `#var` prints it. It **overrides** the label the variable carries, and is stored with it.
/// - descr (str, none): why *this* value was chosen, printed from level 3 as `#var` prints it. It overrides the description the variable carries, and is stored with it.
/// - level (int, auto): as `#var`: 0 prints nothing (the conversion still happens), 1 the line, 2 also the label, 3 also the description and the citation.
/// - norm (str, none), norm-ref (str): the citation, printed from level 3: in the footnote, or with `note: "line"` in the right-hand column. They override the citation the variable carries; `norm-ref:` given alone replaces the clause and keeps the norm.
/// - style (str, none): a math function applied to the **whole line**, `symbol = value unit` -- `"bold"`, `"underline"` -- or `"double"`, which rules it twice underneath in the document's own ink, the mark `verify` sets a relation with, for a value a section rests on. `#eq`'s own argument (v0.100); ⚠️ a line it is given is set with math's own spacing around its `=`, a little wider than a line without it.
/// - note (str): as `#var`: `"footnote"` (the default) inline, the label, the description and the citation in one footnote; `"line"` on a line of its own, the label after an em dash, the description a footnote and the citation in the right-hand column. No effect inside a `var-line`.
/// - sep (str, none): as `#var`: the separator printed after the line when it is printed inline, hidden with it by its level; refused with `note: "line"` and inside a `var-line`.
/// -> content
#let var-unit(key, unit, label: none, descr: none, level: auto, norm: none, norm-ref: "", note: "footnote", sep: none, style: none) = {
  check-key("var-unit", key)
  check-level("var-unit", level)
  check-note("var-unit", note)
  check-sep("var-unit", sep, note)
  let unit = written-unit(unit)
  assert(type(unit) == str, message: "var-unit: the unit of `" + key + "` must be a string, got " + repr(unit))
  // read here rather than inside the update: an argument that is not a unit at all is a typo, and a typo must be refused where it is written
  assert(parse-unit(unit) != none, message: "var-unit: cannot read the unit " + repr(unit) + " of `" + key
    + "` -- write it as the report writes one, `kN`, `N/mm²`, `kNm`")

  // the citation this conversion states, for the bibliography -- before the update, as `var`'s is (lib/bibliography.typ, v0.99). The one the variable already carries was registered where it was declared.
  bib-note(norm)

  var-registry.update(d => {
    // written back **where the name lives** -- the current domain, or the default one it falls back to -- rather than into whichever domain happens to be open, which would shadow the variable instead of converting it
    let here = var-current(d)
    let dom = if here in d.domains and key in d.domains.at(here) { here } else if "" in d.domains and key in d.domains.at("") { "" } else { none }
    // a name the registry does not hold is refused in the `context` below, which is reached at every level. ⚠️ Here it would not be: the function of a `state.update` runs only where something reads that state, so a panic written here is silent in a document that never looks the registry up again -- which is exactly the document a mistyped name produces.
    if dom == none { return d }
    let r = d.domains.at(dom).at(key)
    let c = converted("var-unit", r.at("symbol", default: key-symbol(key)), r.value, r.at("unit", default: ""), unit)
    let out = r
    out.insert("value", c.value)
    out.insert("unit", c.unit)
    out.insert("warning", c.warning)
    // What the call states overrides what the variable carries, field by field and stored with it, as `#var` stores its own (var-record): a conversion is a new declaration of the same variable, and the lines below -- a `#val`, a `#find` -- read the label it was given here.
    if label != none { out.insert("label", label) }
    if descr != none { out.insert("description", descr) }
    if norm != none { out.insert("norm", norm) }
    // `norm-ref:` alone replaces the clause and keeps the norm, as on `#var` (v0.86)
    if norm != none or norm-ref != "" { out.insert("norm_ref", norm-ref) }
    let bucket = d.domains.at(dom)
    bucket.insert(key, out)
    d.domains.insert(dom, bucket)
    d
  })

  context {
    // the registry is read at **every** level, so that an unknown name is refused whatever the report is compiled at -- and so that the update above is resolved at all
    let d = var-registry.get()
    let r = var-lookup(d, key)
    if r == none {
      let known = var-names(d)
      panic("var-unit: no variable named " + repr(key) + " -- "
        + (if known.len() == 0 { "none is declared yet" } else { "declared here: " + known.join(", ") }))
    }
    let st = var-line-state.get()
    check-sep-row("var-unit", st, sep)
    let lv = line-level(st, level)
    if lv >= 1 {
      let value = apply-style(style, [#eval(r.at("symbol", default: key-symbol(key)), mode: "math")~=~#formula-number(r.value, r.unit, number-digits.get())])
      let warning = unit-warning(r.at("warning", default: none))
      if st == none and note == "line" {
        let extra = line-note(r, lv, with-label: false, with-norm: false)
        let line = [
          #value#if lv >= 2 and r.at("label", default: none) != none [ --- #render-prose(tl-str(r.label))]#if extra != none [#extra]
        ]
        annotated-rows(((line, if lv >= 3 and r.at("norm", default: none) != none { r } else { none }),))
        if warning != none { warning }
      } else {
        let item = inline-item(value, line-note(r, lv), warning)
        if st == none { item + sep-after(sep) } else { line-item(st, item) }
      }
    }
  }
}

#let eq-argument-names = ("style", "label", "descr", "norm", "norm-ref", "unit", "level", "value", "note", "sep", "summary")

/// A calculation written by hand: the formula in letters, the same formula with the numbers and their units put in, and the answer -- **computed from the formula**, with its units checked. The result is stored under `key`, so the next line names it without redeclaring anything.
///
/// ```typ
/// #var("R_k", 7, "kN")
/// #var("k_dens", 0.806, level: 0)
/// #var("eta_w", 0.8, level: 0)
/// #var("gamma_M", 1.7, level: 0)
/// #eq("R_d", `k_dens dot eta_w / gamma_M dot R_k`, style: "bold", norm: "Sherpa", norm-ref: "ETA-12/0197")
/// ```
///
/// The answer a section ends on, ruled twice as `verify` rules a relation:
///
/// ```typ
/// #var("M_Ed", 1.254, "kNm")
/// #var("a", 120, "mm")
/// #eq("F", `M_Ed / a`, style: "double")
/// ```
///
/// ```typ
/// #var("M_Ed", 0.275, "kNm")
/// #var("a", 135, "mm")
/// #eq("F_Ed", `M_Ed / a`)
/// ```
///
/// At `level: 0` the answer is computed, checked and stored, and nothing is printed -- an intermediate value the next line names:
///
/// ```typ
/// #var("b", 100, "mm", level: 0)
/// #var("h", 200, "mm", level: 0)
/// #eq("A", `b dot h`, level: 0)
/// #var("N", 12, "kN", level: 0)
/// #eq("sigma", `N / A`)
/// ```
///
/// A `*` is a product, printed as `·`, and a word math does not know may stand in the symbol without its quotes -- `G_(1,Ed)` for `G_(1,"Ed")`:
///
/// ```typ
/// #var("g_k", 1.2, "kN/m²", level: 0)
/// #eq("G_1_Ed", "G_(1,Ed)", `1.35 * g_k`, unit: "kN/m²")
/// ```
///
/// It is printed **inline** by default, as `#var` is (v0.117, issue #19): one word of its sentence, so it may follow a `#var` on the same line, with its label, its description and its citation gathered into one footnote on the answer. `note: "line"` sets it on a line of its own -- the label after the answer, the description as a footnote, the citation in the right-hand column:
///
/// ```typ
/// #var("R_k", 7, "kN", level: 0)
/// Mit #var("gamma_M", 1.7, "") wird #eq("R_d", `R_k / gamma_M`, label: "Bemessungswert", norm: "SIA 265", norm-ref: "2.2.5", level: 3).
/// #eq("R_d2", "R_(d,2)", `R_k / 1.7`, label: "Bemessungswert", descr: "Mit $gamma_M = 1.7$", norm: "SIA 265", norm-ref: "2.2.5", note: "line", level: 3)
/// ```
///
/// The formula names the **keys of the registry** and nothing else -- there is no `where:`, and a name the registry does not hold stops the compile saying which names it does hold. A key that is the beginning of another (`F` and `F_Ed`) is safe: the longest is substituted first, and only whole words are.
///
/// **The units are algebra, not decoration.** Each operand's unit is parsed into dimensions, the formula's operations propagate them, and the answer comes out in the unit `unit:` declares -- or, left to itself, in the one unit the table names for that dimension, which `#unit` sets. `M_Ed / a`, kNm over mm, comes to kN with no conversion factor typed in by hand. A sum whose sides have different dimensions, a `sqrt` of an odd power, an unreadable unit, an answer given with `value:` that the formula contradicts: each stops the compile naming both sides. A declared unit the formula cannot *reach* does not: the answer is printed in the unit the operands were written in, with a red line naming both (v0.63). A *dimensionless* mistake it cannot catch -- 1000 is a valid factor -- which is why the substituted line is printed.
///
/// **What cannot be computed is still printed.** An integral, a derivative: the formula displays exactly as written, and `value:` gives the answer. Nothing is verified then.
/// - key (str): the name the result is stored under, and printed as where no symbol is given -- as `#var` prints a key, `M2` as M and 2.
/// - ..rest (any): the positional tail, whose two slots are the bullets below -- the optional printed symbol, then the formula. Variadic only because Typst has no optional positionals; every *named* argument is declared, so an editor shows them all.
/// - symbol (str): optional second positional argument, the math source printed in the key's place. A word math does not know may be written without its quotes, `"G_(1,Ed)"`.
/// - formula (content, str): the formula, in Typst math source naming the registry's keys. A raw block -- `` `M / a` `` -- saves escaping every quote, and is the expected form. `*` multiplies, as `dot` does, and is printed as it. A literal takes its unit in quotes, `(3 "m")`, and what is quoted is never read as a name: `(3 "m")` is three metres even where a variable `m` is declared.
/// - unit (str, auto): the unit of the answer. auto takes the one the table names for that dimension (`#unit` sets it); `""` asserts it is dimensionless. A unit of another dimension prints the answer in the operands' own units, with a red line.
/// - style (str, none): a math function applied to the answer -- `"bold"`, `"underline"` -- or `"double"`, which rules the answer twice underneath, in the document's own ink: the mark `verify` sets a relation with, drawn the same way and at the same weight, for a result a section ends on.
/// - label (str, none): what the answer is, printed from level 2 -- in the answer's footnote, inline (the default) or in a `var-line`, and after it, set apart by an em dash, with `note: "line"`. `#var`'s own `label:`, on the command that computes rather than declares.
/// - descr (str, none): why the answer is what it is -- an assumption, a branch taken -- printed as a footnote from level 3, as `#var`'s is.
/// - level (int, auto): 0 prints nothing (the answer is still computed, checked and stored), 1 the symbol and the answer, 2 also the formula in letters and the label, 3 also the formula in numbers, the description and the citation. auto follows the report.
/// - norm (str, none), norm-ref (str): the citation, from level 3: in the answer's footnote, or in the right-hand column with `note: "line"`.
/// - value (int, float, auto): the answer, for a formula that cannot be evaluated.
/// - note (str): how the formula is set. `"footnote"` (the default since v0.117, as `#var`'s) prints it inline, one word of its sentence, and gathers the label, the description and the citation into one footnote on the answer. `"line"` sets it on a line of its own: the label after the answer, the description as a footnote and the citation in the right-hand column -- the engine's own checks are set so. No effect inside a `var-line`, whose items take one footnote each.
/// - sep (str, none): as `#var`: the separator printed after the answer when it is printed inline, hidden with it by its level; refused with `note: "line"` and inside a `var-line`.
/// - summary (bool): lists the answer in a summary table, as `#var`'s own does -- **its unit decides which**: kN/m² an area load, kN/m a line load, any other unit refused naming the two, where the table is printed. It is what puts a line load the export does not carry into `show-line-load-summary`.
/// -> content
#let eq(key, ..rest, unit: auto, style: none, label: none, descr: none, level: auto, norm: none, norm-ref: "", value: auto, note: "footnote", sep: none, summary: false) = {
  // ⚠️ Declared one by one rather than swept into `..args`: a tooltip on a sink signature reads `eq(args: arguments) -> any` and says nothing about `unit:`, which is how this was found (v0.63.1). Only the positional tail stays variadic — the printed symbol is an optional second positional, and Typst has no optional positionals.
  let unknown = rest.named().keys()
  if unknown.len() > 0 {
    panic("eq: unknown argument " + repr(unknown.first())
      + " -- " + eq-argument-names.map(n => repr(n)).join(", "))
  }
  check-key("eq", key)
  check-level("eq", level)
  check-note("eq", note)
  check-sep("eq", sep, note)

  let pos = rest.pos()
  // ⚠️ The unit is named and cannot be a third positional, where `var`'s is the last one: a formula may be written as a string (`#eq("N_Ed", "N - N_gunstig")`), so with two positionals a unit and a formula are the same shape and nothing could tell `#eq("eta", "F/R", "%")` from a symbol and a formula. `var` has no such trouble -- a value is a number or a var object, never a string. So the message names `unit:` rather than leaving it to be found.
  assert(pos.len() >= 1 and pos.len() <= 2,
    message: "eq: write #eq(\"key\", `formula`), or #eq(\"key\", \"symbol\", `formula`) -- the unit is a named argument, #eq(..., unit: \"%\"), a formula being written as a string too")
  let has-symbol = pos.len() == 2
  if not has-symbol { check-printable-key("eq", key) }
  let symbol = if has-symbol { quoted-words(pos.at(0)) } else { key-symbol(key) }
  let formula = pos.at(if has-symbol { 1 } else { 0 })
  // a `*` is a product, printed as `dot` (star-as-dot)
  let src = star-as-dot(if type(formula) == str { formula } else { formula.text })

  // the two the body reads under their older names: `unit` and `value` are the *arguments*, and reading them as `want` and `given` keeps every line below saying which of the two it means
  let want = written-unit(unit)
  let given = value

  // the document this formula rests on, for the bibliography -- before the update, as `var`'s is (lib/bibliography.typ, v0.99)
  bib-note(norm)

  var-registry.update(d => {
    // An answer given with `value:` says the formula is there to be displayed, not evaluated: the words it carries -- `integral`, `dif`, a function's name -- are then expected rather than mistaken.
    let got = evaluate-formula("eq", d, src, strict: given == auto)
    let shown = if got.result == none { none } else { present("eq", symbol, got.result, want, unit-table(d)) }
    let answer = if given != auto {
      // a formula whose declared unit is not its own is not compared against `value:`: the two are then in different units, and the disagreement the red line reports is the one to fix first
      let comparable = shown != none and shown.at("warning", default: none) == none
      if comparable and calc.abs(shown.value - given) > 1e-9 * calc.max(1.0, calc.abs(given)) {
        panic("eq: " + symbol + " is given as " + str(given)
          + ", but its own formula comes to " + str(shown.value) + " -- one of the two is wrong")
      }
      // the unit is the declared one, else the one the formula itself comes out in -- until v0.86 it was "", so an F_Ed given with value: was stored as a bare number and a verify against a force said «comparing 1 with N»
      (value: given, unit: if want != auto { want } else if shown != none { shown.unit } else { "" })
    } else if shown != none { shown } else {
      panic("eq: " + symbol + " cannot be computed from its formula -- an operation this evaluator does not "
        + "read (an integral, a derivative). Give the answer with value:, which prints it without checking it")
    }
    summary-mark(var-store(d, key, (
      value: answer.value, unit: answer.unit, symbol: symbol,
      warning: answer.at("warning", default: none),
      label: label, description: descr, norm: norm, norm_ref: norm-ref, source: none,
    )), summary, key)
  })

  context {
    let d = var-registry.get()
    let r = var-lookup(d, key)
    let st = var-line-state.get()
    check-sep-row("eq", st, sep)
    let lv = line-level(st, level)
    let digits = number-digits.get()
    // The result itself is in the registry by now; it is not one of its own operands.
    let operands = formula-operands(d, src).filter(o => o.key != key)
    let (letters, numbers) = formula-lines(src, operands, digits)

    let tail = fmt-magnitude(r.value, digits) + (if r.unit == "" { "" } else { " \"" + r.unit + "\"" })
    // `style` is spliced into the math **source** and evaluated with the rest of the chain, which is what lets it name any math function -- `bold`, `underline` -- without this file knowing one of them. A double rule is not a math function at all but two nested boxes (verify, below), so it is handed to the same eval through its `scope`: one equation still, so the spacing around every `=` stays math's own, where a box concatenated after the equation would have carried text spacing into it.
    if style != none { tail = (if style == "double" { "dbl" } else { style }) + "(" + tail + ")" }

    let parts = (symbol,)
    if lv >= 2 { parts.push(letters) }
    // left out where nothing was substituted -- an integral would otherwise be printed twice over
    if lv >= 3 and numbers != letters { parts.push(numbers) }
    parts.push(tail)

    let cite = if lv >= 3 and norm != none { (norm: norm, norm_ref: norm-ref) } else { none }
    // The double rule is `double-rule` above, one place for the three commands that draw one (v0.100); it is handed to the eval through its `scope` because it is not a math function at all but two nested boxes.
    let dbl = double-rule
    let body = eval(parts.join(" = "), mode: "math", scope: (dbl: dbl))
    // The same statement stacked at its `=` signs, for a line too wide for its row (annotated-rows, formula-chain): `symbol = <letters>`, then `= <numbers>` and `= <answer>` under it -- together where the width holds them, each on its own where it does not -- each `=` under the first, a display fraction being one atom that no line break can enter. `after` is what the line ends on, its label or its footnote, set after the answer on the last line. A line of one `=` has nothing to stack and stays one line.
    let chained(line, after) = {
      if parts.len() < 3 { return line }
      formula-chain(line, eval(parts.at(0) + " = " + parts.at(1), mode: "math", scope: (dbl: dbl)), parts.slice(2),
        s => chain-line(symbol, "=", s, scope: (dbl: dbl)), last: after)
    }
    let warning = unit-warning(r.at("warning", default: none))
    // ⚠️ Everything above is computed at **every** level, level 0 included, and only the emission is held back: the registry is read, the operands are resolved and the units are checked, so a formula naming a variable that does not exist is refused whatever the level -- a line hidden today is a line printed in the next report, and it must not be the report that finds the mistake.
    let said = (label: label, description: descr, norm: norm, norm_ref: norm-ref)
    if lv >= 1 {
      if st == none and note == "line" {
        // The label follows the answer as `#var`'s follows its value, and for the same reason: what the result *is* is read with it, not at the foot of the page. The description is the footnote beside it, at level 3.
        let extra = line-note(said, lv, with-label: false, with-norm: false)
        let after(x) = [#x#if lv >= 2 and label != none [ --- #render-prose(tl-str(label))]#if extra != none [#extra]]
        annotated-rows(((chained(after(body), after), cite),))
        if warning != none { warning }
      } else if st == none {
        // Inline, the default since v0.117 (issue #19: «#eq s'imprime en ligne par défaut, comme #var»): one word of its sentence, so it may follow a `#var` on the same line, and the label, the description and the citation are the answer's one footnote -- `#var`'s own inline branch. Until v0.117 `note: "footnote"` kept a block of its own.
        inline-item(body, line-note(said, lv), warning) + sep-after(sep)
      } else {
        // In a row there is no em dash and no column, so the label and the citation become the item's one footnote (`line-note`).
        line-item(st, inline-item(body, line-note(said, lv), warning))
      }
    }
  }
}

/// Sets the unit every **computed** result of one dimension is printed in, from here to the end of the document.
///
/// ```typ
/// #unit("N/mm²")
/// #var("F", 12, "kN")
/// #var("A", 2400, "mm²")
/// #eq("sigma", `F / A`)
/// ```
///
/// ```typ
/// #var("M", 4.2, "kNm")
/// #var("l", 3, "m")
/// #eq("V", `M / l`)
/// #unit("N")
/// #eq("V_N", `M / l`)
/// ```
///
/// The dimension is read from the unit itself, so one call settles one kind of result and leaves the others alone. The defaults are `default-units`: mm, mm², mm³, mm⁴, s, kN, kNm, N/mm², kN/m, kg, °.
///
/// It reaches **only what the engine computes** -- the answer of an `#eq`, a side of a `#verify` that is a whole expression. A value that already carries a unit keeps it: one read from the export (`var-of`, `show-calc`, `show-input`), and one written out by hand (`#var("R_k", 7, "kN")`). The unit of a value is the data's, and is never retyped (docs/architecture/principles.md §2, rule 1); `#var-unit` is what carries one into another unit deliberately.
///
/// ⚠️ A stress and a surface load are **one** dimension, N/m². The default serves the stress; a line that wants kN/m² says `unit: "kN/m²"`, or this command says it for a whole section.
/// - written (str): the unit, as the report writes one. Must have a dimension -- `#unit("%")` is refused, a dimensionless result being printed as a bare number.
/// -> content
#let unit(written) = {
  assert(type(written) == str and written.trim() != "",
    message: "unit: write the unit as a string, as in #unit(\"Nmm\") -- got " + repr(written))
  let written = written-unit(written)
  let p = parse-unit(written)
  assert(p != none, message: "unit: cannot read " + repr(written)
    + " -- write it as the report writes one, `mm`, `kN`, `kNm`, `N/mm²`")
  assert(clean-dims(p.dims).len() > 0, message: "unit: " + repr(written)
    + " has no dimension, so there is no kind of result it could be the unit of "
    + "-- a result without dimensions is printed as a bare number")
  var-registry.update(d => {
    let table = unit-table(d)
    table.insert(dims-text(p.dims), written.trim())
    d.insert("units", table)
    d
  })
}

/// Keeps one set of variables apart from another, **without losing it**: what is declared inside belongs to `name`, and stays readable further down the document through `val(key, domain: name)`.
///
/// ```typ
/// #var("l", 2.4, "m")
/// #var-domain("S10 - 0.55 kN Ende")[
///   #var("F", 0.55, "kN")
///   #eq("M", `F dot l`)
/// ]
/// ```
///
/// ```typ
/// #var("l", 2.4, "m")
/// #grid(columns: (1fr, 1fr),
///   var-domain("Ende")[ #var("F", 0.55, "kN") #eq("M", `F dot l`) ],
///   var-domain("Mitte")[ #var("F", 1, "kN") #eq("M", `F dot l / 2`) ],
/// )
/// Das massgebende Moment beträgt #val("M", domain: "Ende").
/// ```
///
/// Without it the second `F` would quietly replace the first, the registry being one dictionary for the whole document. A name is looked up in the innermost domain first and then in the default one, so what a section declares outside every domain -- R_d, a partial factor -- is readable inside all of them.
///
/// **A title** is printed as a heading one level below the heading it stands under -- a calculation domain of Woodcore's «Formules» tab is written `#var-domain("<its id>", title: "<its name>")[…]` in its own file `Formules/<id>.typ`, and a section prints it with `#include "/Formules/<id>.typ"`: the id is what `val(domain:)` reads, so renaming the domain breaks no call, and the name is the title the report shows (issue #15).
///
/// ```typ
/// = Poutre P1
/// #var-domain("poutre-p1", title: "Moment de flexion")[
///   #var("q_d", 4.5, "kN/m")
///   #var("l_1", "l", 5, "m")
///   #eq("M_d", `q_d * l_1^2 / 8`, unit: "kNm")
/// ]
/// Le moment vaut #val("M_d", domain: "poutre-p1").
/// ```
///
/// 👉 A *domain* here is a set of names in the report. It has nothing to do with a calculation domain of the Excel workbooks (docs/domain/calculation-domains.md §3.3), which is a kind of calculation -- `snow-load`, `dead-load` -- whose instances are Excel sheets.
/// - name (str): the domain's name -- for a domain of the «Formules» tab, its id, the name of its file.
/// - title (str, none): printed as a heading one level below the heading before it (level 1 where there is none); none prints nothing.
/// - body (content): where its variables are declared.
/// -> content
#let var-domain(name, title: none, body) = {
  assert(type(name) == str and name != "", message: "var-domain: the name must be a non-empty string, got " + repr(name))
  assert(title == none or (type(title) == str and title != ""), message: "var-domain: the title is a non-empty string or none, got " + repr(title))
  if title != none {
    context {
      let above = query(selector(heading).before(here()))
      heading(level: if above.len() > 0 { above.last().level + 1 } else { 1 }, title)
    }
  }
  var-registry.update(d => { d.stack.push(name); d })
  body
  var-registry.update(d => { d.stack = d.stack.slice(0, -1); d })
}

#let val-argument-names = ("domain", "type", "unit", "symbol", "level", "label", "descr", "norm", "norm-ref", "note", "style")

// The four parts a value can be printed as, in the engineer's own words (v0.80): the value alone, its unit alone, the two together -- the default -- and the whole expression, `s_k = 1.729 kN/m²`. They replace `"number"`, `"unit"`, `"number+unit"`, which `fmt` and `live-load` also read before those two commands were folded into this one.
#let val-types = ("val", "unit", "val+unit", "expression")

/// **One value, printed** -- wherever it comes from: a variable of the report, a value of the export, or a number written here. It is the one command that prints a single value without writing it down -- `#var` prints inline too since v0.86, and stores what it prints -- and it replaced `fmt`, `inline-value` and `live-load` in v0.80.
///
/// ```typ
/// #var("R_d", 4.969, "kN")
///
/// Der Bemessungswiderstand beträgt #val("R_d"), also #val("R_d", type: "expression").
/// ```
///
/// ```typ
/// Auf horizontalem Gelände liegt #val("s_k", domain: ("snow-load", "SL"), type: "expression").
/// ```
///
/// ```typ
/// #var-domain("Ende")[ #var("M", 1.32, "kNm") ]
///
/// In der Einheit #val("M", domain: "Ende", type: "unit") ist das #val("M", domain: "Ende", type: "val").
/// ```
///
/// A number quoted with where it comes from, which no variable of the report carries:
///
/// ```typ
/// #val(7, unit: "kN", symbol: "R_k", type: "expression", label: "Kapazität Sherpa XS", norm: "Sherpa", norm-ref: "ETA-12/0197", level: 3)
/// ```
///
/// Whatever part it prints may be set apart, as `#var`'s line is: `style:` names a math function -- `"bold"`, `"underline"` -- or `"double"`, which rules it twice underneath.
///
/// ```typ
/// #var("R_d", 4.969, "kN", level: 0)
///
/// Der Bemessungswiderstand beträgt #val("R_d", style: "bold").
/// ```
///
/// The same with its extras on the line rather than in a footnote -- the label after an em dash, the description and the citation in parentheses after it:
///
/// ```typ
/// #val(7, unit: "kN", symbol: "R_k", type: "expression", label: "Kapazität Sherpa XS", descr: "Katalogwert", norm: "Sherpa", norm-ref: "ETA-12/0197", note: "line", level: 3)
/// ```
///
/// At `level: 0` nothing is printed and the name is still read -- a value left out of a row takes its separator with it, and the relation after it still names it:
///
/// ```typ
/// #var("F_Ed", 2.037, "kN", level: 0)
/// #var("R_d", 4.969, "kN", level: 0)
/// #var-line[
///   #val("F_Ed", type: "expression")
///   #val("R_d", type: "expression", level: 0)
///   #verify(`F_Ed <= R_d`)
/// ]
/// ```
///
/// **What is printed follows the level**, and only the extras do -- level 0 apart, which prints nothing at all, as it does everywhere here: level 1 the value as `type` asks for it, level 2 the label with it, level 3 also the description, the `choices` it explains and the citation -- all of them as **one** footnote by default, because inline there is no column for a citation (section 9). So `level: 1` is what keeps a bare number in a sentence of a checking report.
///
/// **`unit:` is display only**: the variable in the registry keeps the unit it was declared with, which is what tells this command from `var-unit`. A unit of another dimension is refused, a conversion nobody can perform being a mistake at the call site rather than a disagreement to read (`eq`'s red line).
/// - what (str, dictionary, int, float): a variable's name, a var object (`var-of(...)`), or a number written here.
/// - ..rest (any): nothing. The domain used to be a second positional argument; it is `domain:` since v0.80, and a second positional is refused saying so.
/// - domain (none, str, array): where the name is read. Left out, the innermost `var-domain` and then the report's own variables; a string, that `var-domain`; a pair, a calculation and its instance -- `("snow-load", "SL")`, `("live-load", "A1")`, `("connection", "VU-MP-1")`.
/// - type (str): `"val+unit"` (the default) e.g. `1.729 kN/m²`, `"val"` e.g. `1.729`, `"unit"` e.g. `kN/m²`, `"expression"` e.g. `s_k = 1.729 kN/m²`.
/// - unit (none, str): the unit it is printed in, converted from the one it carries. A bare number takes it as its own.
/// - symbol (none, str): the math source printed by `"expression"`, for a number that carries none. A variable brings its own. A word math does not know may be written without its quotes, `"W_(y,erf)"`.
/// - level (int, auto): 0 nothing, 1 the value, 2 also the label, 3 also the description, its choices and the citation -- in one footnote. auto follows the report (section 4).
/// - label (none, str): what the value is, in place of the one it carries -- printed from level 2.
/// - descr (none, str): why *this* value was chosen, in place of the one it carries -- printed from level 3, with the `choices` it explains.
/// - norm (none, str), norm-ref (str): the citation, in place of the one it carries.
/// - style (str, none): a math function applied to the **whole line**, `symbol = value unit` -- `"bold"`, `"underline"` -- or `"double"`, which rules it twice underneath in the document's own ink, the mark `verify` sets a relation with, for a value a section rests on. `#eq`'s own argument (v0.100); ⚠️ a line it is given is set with math's own spacing around its `=`, a little wider than a line without it.
/// - note (str): where the label, the description and the citation go. `"footnote"` (the default) gathers them into one footnote; `"line"` sets the label after an em dash on the line and the description and the citation in parentheses after it -- a value in a sentence having no column -- the `choices` and the orange line of a unit written over staying a footnote. No effect inside a `var-line`, whose items take one footnote each.
/// -> content
#let val(what, ..rest, domain: none, type: "val+unit", unit: none, symbol: none, level: auto, label: none, descr: none, norm: none, norm-ref: "", note: "footnote", style: none) = bib-note(norm) + context {
  // ⚠️ `bib-note(norm) + context { … }` above: the registration for the bibliography is emitted **outside** this context, which is where a state written is read back by the folded chain an update function reads (docs/domain/connections.md §3.3quinquies, v0.99). Only the `norm:` written here is registered: every other citation `val` can print comes either from the export -- which the bibliography walks itself -- or from a variable of the registry, which the `var` or `eq` that declared it has already registered.
  check-level("val", level)
  check-note("val", note)
  // ⚠️ `panic` inside an `if`, never `assert(cond, message: ...)`: Typst builds an assert's message before it tests the condition, so `unknown.first()` on an empty array would fail every correct call (v0.63.1).
  let unknown = rest.named().keys()
  if unknown.len() > 0 {
    panic("val: unknown argument " + repr(unknown.first())
      + " -- " + val-argument-names.map(n => repr(n)).join(", "))
  }
  // The v0.61 form was #val("domain", "key"). Refused rather than read both ways, so that one spelling says one thing -- and the message is the rewrite.
  if rest.pos().len() > 0 {
    panic("val: the domain is a named argument since v0.80 -- write #val("
      + repr(rest.pos().first()) + ", domain: " + repr(what) + ")")
  }
  if not (type in val-types) {
    panic("val: invalid type " + repr(type) + " -- use " + val-types.map(t => repr(t)).join(", "))
  }

  let d = var-registry.get()
  let given-number = value-type(what) == int or value-type(what) == float
  let base = if value-type(what) == dictionary and "value" in what {
    if domain != none { panic("val: a var object carries where it comes from, so domain: says it a second time -- drop one of the two") }
    what
  } else if given-number {
    if domain != none { panic("val: a number written here is read from nowhere, so domain: has nothing to name -- drop it") }
    (value: what, unit: "", symbol: none, label: none, description: none, norm: none, norm_ref: "")
  } else if value-type(what) == str {
    if domain == none {
      let r = var-lookup(d, what)
      if r == none {
        panic("val: no variable named " + repr(what) + " -- "
          + (if var-names(d).len() == 0 { "none is declared yet" } else { "declared here: " + var-names(d).join(", ") })
          + ". A value of the export is read with domain: (\"snow-load\", \"SL\")")
      }
      r
    } else if value-type(domain) == str {
      let known = if domain in d.domains { d.domains.at(domain).keys() } else { () }
      if not (what in known) {
        panic("val: no variable named " + repr(what) + " in the domain " + repr(domain) + " -- "
          + (if known.len() == 0 { "that domain declares nothing" } else { "it declares: " + known.join(", ") })
          + ". A variable declared outside every var-domain is read without domain:")
      }
      d.domains.at(domain).at(what)
    } else if value-type(domain) == array and domain.len() == 2 {
      let vars = find-calculation("val", domain.at(0), domain.at(1)).vars
      // ⚠️ A name the export does not carry is looked up in the var-domain named after the instance, which is where show-polar-moment publishes the forces it worked out -- as `var` and `find` already did for the very same pair, so that `#val("F_max", domain: ("connection", "VU-MP-1"))` no longer refused what the other two named (v0.86). The export wins a name both carry, being the traced one.
      let published = d.domains.at(domain.at(1), default: (:))
      if what in vars { vars.at(what) } else if what in published { published.at(what) } else {
        panic("val: unknown var " + repr(what) + " in " + source-label(domain.at(0), domain.at(1))
          + " -- valid vars: " + (vars.keys() + published.keys()).join(", "))
      }
    } else {
      panic("val: domain: is a domain of the report (\"S10 - 0.55 kN Ende\") or a calculation and its instance"
        + " ((\"snow-load\", \"SL\")) -- got " + repr(domain))
    }
  } else {
    panic("val: write a variable's name, a var object (var-of(...)) or a number -- got " + repr(what))
  }

  let unit = written-unit(unit)
  let have = base.at("unit", default: "")
  let value = base.value
  let shown-unit = have
  // A unit written over the one the value carries is said on the page, in orange, at every level: the number printed is then not the number the registry or the export holds, and a reader who cannot see that has no way of finding it out (v0.80, the engineer's request). A bare number given its unit here has overwritten nothing, and neither has a unit equal to the one carried.
  let overridden = none
  if unit != none {
    if have == "" and given-number {
      shown-unit = unit
    } else {
      // a dimensionless value goes through the same conversion as any other, which is what lets it be printed in % -- refused outright until v0.86, where var-unit carried it there
      let c = converted("val", base.at("symbol", default: repr(what)), value, have, unit)
      if c.warning != none and have == "" {
        panic("val: " + repr(what) + " carries no unit, so it cannot be printed in " + repr(unit))
      }
      if c.warning != none {
        panic("val: " + repr(unit) + " and " + repr(have) + " are not the same dimension, so "
          + repr(what) + " cannot be printed in it")
      }
      value = c.value
      shown-unit = c.unit
      if shown-unit != have {
        // a ratio printed in % has no unit of its own to name, and «statt in .» said so badly (v0.86)
        overridden = text(fill: override-colour, if have == "" { t-str("formula.unit_override_bare", shown: shown-unit) } else { t-str("formula.unit_override", shown: shown-unit, have: have) })
      }
    }
  }

  let sym = if symbol != none { quoted-words(symbol) } else { base.at("symbol", default: none) }
  let digits = number-digits.get()
  // `style:` wraps what is printed, whichever of the four parts it is -- `#var`'s own argument (v0.100), so that a value quoted in a sentence can be set bold or ruled like the declaration it comes from.
  let printed = apply-style(style, if type == "unit" {
    if shown-unit == "" { panic("val: type: \"unit\" needs a value that carries one, and " + repr(what) + " has none") }
    [#shown-unit]
  } else if type == "val" {
    [#formula-number(value, "", digits)]
  } else if type == "val+unit" {
    [#formula-number(value, shown-unit, digits)]
  } else {
    if sym == none {
      panic("val: type: \"expression\" prints `symbol = value unit`, and a number written here has no symbol"
        + " -- give one with symbol:, or read a variable by its name")
    }
    // one word of its sentence, as #var's is: no line break between the symbol, the sign and the value
    [#render-symbol((symbol: sym))~=~#formula-number(value, shown-unit, digits)]
  })

  // The label and the citation the call states win over the ones the value carries: a number of a manufacturer's table has neither of its own, and a var of the export may be quoted for something narrower than its own label says.
  let noted = (
    symbol: if sym == none { "" } else { sym },
    label: if label != none { label } else { base.at("label", default: none) },
    description: if descr != none { descr } else { base.at("description", default: none) },
    choices: base.at("choices", default: none),
    norm: if norm != none { norm } else { base.at("norm", default: none) },
    norm_ref: if norm != none or norm-ref != "" { norm-ref } else { base.at("norm_ref", default: "") },
  )
  let st = var-line-state.get()
  let lv = line-level(st, level)
  // `note: "line"` (v0.87): the label after an em dash, as `#var`'s line sets it, and the description and the citation in parentheses after it -- a value in a sentence has no right-hand column to give a citation. What stays a footnote is what is not one sentence: the `choices`, a list, and the orange line of a unit written over, whose marker is the point.
  let on-line = st == none and note == "line"
  let extra = line-note(noted, lv, extra: overridden, colour: if overridden == none { none } else { override-colour },
    with-label: not on-line, with-descr: not on-line, with-norm: not on-line)
  let item = if on-line {
    let paren = ()
    if lv >= 3 and noted.description != none { paren.push(render-prose(tl-str(noted.description))) }
    if lv >= 3 and noted.norm != none { paren.push(norm-text(noted)) }
    [#printed#if extra != none [#extra]#if lv >= 2 and noted.label != none [ --- #render-prose(tl-str(noted.label))]#if paren.len() > 0 [ (#paren.join([#semicolon-str() ]))]]
  } else { printed + (if extra == none { [] } else { extra }) }
  // ⚠️ Level 0 prints nothing here too, and this is where the rule reads oddest: a value quoted in a sentence and then not printed leaves a hole in it. It is kept all the same, because 0 means "not printed" for every command of this file and an exception would be one more thing to remember -- and because in a row it is exactly right, an item that is not printed taking its separator with it (`line-item` is what counts an item, so one that never reaches it is never counted).
  if lv >= 1 { if st == none { item } else { line-item(st, item) } }
}

// --- find: what there is to name in a call (v0.85) ------------------------
// A command for **writing** a report rather than for the finished page: it prints which domains exist, which keys each one carries and which variables one of them holds, so that a call can be written without reading data/ by hand. It is the one command here whose output is not meant to be delivered -- one calls it, reads it, and deletes the call. What makes it necessary rather than convenient is that nothing else answers the question: the catalog window's loads tab reads data/calculations.json and nothing else (section 10quater), so a connector's three dozen vars and a polar moment's geometry, which are files of their own, are listed nowhere at all.

// Every domain a call may address: the calculation domains of data/calculations.json, then the two that are files of their own. `domain-ids()` lists the first alone and says so in its own header, that being what calculations.json holds; a command written to answer "what is there?" has to be complete, so it names all of them here rather than widening a promise made elsewhere.
#let find-domains() = domain-ids() + (connector-domain, connection-domain)

#let find-objects = ("domain", "variable")

// The four parts `val` prints, and the name to type into a call -- which is what one comes here for. Built from `val-types` rather than restated, so that the two cannot come to offer different words.
#let find-types = ("name",) + val-types

/// **What there is to name in a call**: every domain with its keys, or the variables one of them holds (v0.85). A command for *writing* a report rather than for the finished page -- one calls it, reads it, and deletes the call -- and the only thing that answers "which variables does this connector carry?": the catalog window's loads tab reads `data/calculations.json` alone, so a connector's own vars and a polar moment's are listed nowhere else.
///
/// ```typ
/// #find(object: "domain")
/// ```
///
/// ```typ
/// #find(object: "variable", domain: ("snow-load", "SL"), type: "name")
/// ```
///
/// What the report itself has written down at this point, which is what a `#verify` refusing a name is asking about:
///
/// ```typ
/// #var("R_k", 7, "kN")
/// #var("k_dens", 0.806, label: "Beiwert")
/// #find(object: "variable")
/// ```
///
/// - object (str): `"domain"` prints every domain and its keys, one line each; `"variable"` prints a table of the variables of one of them.
/// - domain (none, str, array): which one. With `object: "domain"`, a name narrows the listing to that domain and nothing at all lists them all. With `object: "variable"`, a **pair** is a calculation and its instance (`("snow-load", "SL")`, `("connector", "SD-10")`), a **string** is a `var-domain` of the report, and nothing at all is what a formula on this line can name: the report's own variables and those of the `var-domain` it stands in.
/// - type (str): what the value column holds -- `"name"` (no value column at all: the names, their symbols and labels), `"val"`, `"unit"`, `"val+unit"` (the default) or `"expression"`, the four parts `val` prints.
/// -> content
#let find(object: "domain", domain: none, type: "val+unit") = context {
  // panic inside an `if`, never assert(cond, message: ...): Typst builds an assert's message before it tests the condition, so repr() of an empty array would fail every correct call (v0.63.1).
  if not (object in find-objects) {
    panic("find: invalid object " + repr(object) + " -- use " + find-objects.map(o => repr(o)).join(", "))
  }
  if not (type in find-types) {
    panic("find: invalid type " + repr(type) + " -- use " + find-types.map(t => repr(t)).join(", "))
  }

  let known = find-domains()
  if object == "domain" {
    let named = if domain == none {
      known
    } else if value-type(domain) == str {
      if not (domain in known) {
        panic("find: no domain " + repr(domain) + " -- " + known.map(d => repr(d)).join(", "))
      }
      (domain,)
    } else {
      panic("find: object: \"domain\" takes one domain's name (\"snow-load\") or nothing at all -- got " + repr(domain))
    }
    // One line per domain, its name and its keys set in the face they are typed in: what one comes here to take away is a string to paste into a call.
    named.map(d => {
      let keys = instance-ids(d)
      [#raw(d)#colon-str() #(if keys.len() == 0 { emph(t-str("find.none")) } else { keys.map(k => raw(k)).join(", ") })]
    }).join(linebreak())
  } else {
    let digits = number-digits.get()
    let reg = var-registry.get()
    let found = if domain == none {
      (title: t-str("find.vars_report"), vars: var-names(reg).map(k => (k, var-lookup(reg, k))), note: none)
    } else if value-type(domain) == str {
      let declared = reg.domains.keys().filter(k => k != "")
      if not (domain in reg.domains) {
        panic("find: no var-domain " + repr(domain) + " declared here -- "
          + (if declared.len() == 0 { "none is" } else { "declared: " + declared.map(k => repr(k)).join(", ") })
          + ". A calculation of the export is named as a pair, (\"snow-load\", \"SL\")")
      }
      (title: t-str("find.vars_domain", domain: domain), vars: reg.domains.at(domain).pairs(), note: none)
    } else if value-type(domain) == array and domain.len() == 2 {
      let exported = find-calculation("find", domain.at(0), domain.at(1)).vars.pairs()
      // What the report itself has computed for this very instance and published under its name -- show-polar-moment's forces and force-grain angles, which are worked out in Typst and are in no file at all (section 1). They are listed with the export's own, because what one comes here for is everything there is to name; the note under the table is what says which half is which.
      let exported-names = exported.map(((k, v)) => k)
      let computed = reg.domains.at(domain.at(1), default: (:)).pairs().filter(((k, v)) => not (k in exported-names))
      (title: t-str("find.vars_source", domain: domain.at(0), instance: domain.at(1)),
       vars: exported + computed,
       note: if computed.len() == 0 { none } else { t-str("find.computed_here", names: computed.map(((k, v)) => k).join(", ")) })
    } else {
      panic("find: domain: is a var-domain of the report (\"S10 - 0.55 kN Ende\") or a calculation and its instance ((\"snow-load\", \"SL\")) -- got " + repr(domain))
    }

    // A value that is a **word** -- the Art der Nutzfläche, the norm's example beside it, a load model -- is set as words that wrap, where a math cell sets it on one line: «Räume in Wohngebäuden und Wohnhäusern, …» ran a hundred characters past the page and squeezed the Bezeichnung column to a letter (v0.86, the engineer: «une valeur texte longue est placée dans une cellule de formule qui ne passe pas à la ligne et déborde»). A table holding one takes the value column as a `wide` one, sharing the leftover width with the Bezeichnung; each cell is then prose, its math between dollars (render-prose), and a word goes through the glossary as `val` sends it. A table of numbers alone is laid out as before.
    let has-words = type != "name" and type != "unit" and found.vars.any(((k, v)) => value-type(v.value) == str)
    // The value column is the part `type:` asks for, and its heading says which part that is: a column of units headed "Wert" would be read as one of values. `"name"` drops the column altogether -- the keys are then the whole answer.
    let value-column = if type == "name" {
      ()
    } else if type == "unit" {
      ((label: "Einheit", kind: "text"),)
    } else if has-words {
      ((label: "Wert", kind: "wide"),)
    } else if type == "val" {
      ((label: "Wert", kind: "number"),)
    } else {
      ((label: "Wert", kind: "math"),)
    }
    // The key is what one types into a call and the symbol is what the page prints, and the two are not the same word: `q_k11` is set as q_(k,11), `f_u_k` as f_(u,k). A table read in order to write a call has to carry both. `"expression"` prints the symbol in its own value cell, so the column is left out there rather than saying it twice.
    let symbol-column = if type == "expression" { () } else { ((label: "Symbol", kind: "math"),) }
    let symbol-cell(k, v) = if type == "expression" { () } else { (v.at("symbol", default: key-symbol(k)),) }
    // A value as prose for a `wide` cell: a word as the glossary gives it, a number as the math it is set as elsewhere, between dollars.
    let prose-value(v, unit) = if value-type(v) == str { tl-str(v) } else if type == "val" { signed-text(fmt-magnitude(v, digits)) } else { "$" + formula-quantity(v, unit, digits) + "$" }
    let value-cell(k, v) = {
      let unit = v.at("unit", default: "")
      let symbol = v.at("symbol", default: key-symbol(k))
      if type == "name" { () } else if type == "unit" { (unit,) }
      else if has-words and type == "expression" { ("$" + symbol + " =$ " + prose-value(v.value, unit),) }
      else if has-words { (prose-value(v.value, unit),) }
      else if type == "val" { (signed-text(fmt-magnitude(v.value, digits)),) }
      else if type == "val+unit" { (formula-quantity(v.value, unit, digits),) }
      else { (symbol + " = " + formula-quantity(v.value, unit, digits),) }
    }
    // What a variable *is*, in `label`, whether it came from the export or was written down here -- the two agree since v0.85.1, where a var the report declared kept it under `description` and this column had to look in both. It is a word of the engine, so the table translates it as it translates every other text cell.
    let designation(v) = {
      let said = v.at("label", default: none)
      if said == none { "" } else { said }
    }

    if found.vars.len() == 0 {
      [#emph(found.title)#colon-str() #emph(t-str("find.none"))]
    } else {
      let tbl = (
        title: found.title,
        columns: ((label: "Name", kind: "text"),) + symbol-column + value-column + ((label: "Bezeichnung", kind: "wide"),),
        rows: found.vars.map(((k, v)) => (k,) + symbol-cell(k, v) + value-cell(k, v) + (designation(v),)),
      )
      let said = found.at("note", default: none)
      render-table(if said == none { tbl } else { tbl + (note: said) })
    }
  }
}

/// Sets several declarations on **one line**, joined the way `show-calc` joins the vars of a group: `R_k = 7 kN; k_dens = 0.806; γ_M = 1.7`.
///
/// ```typ
/// #var-line[
///   #var("R_k", 7, "kN")
///   #var("k_dens", 0.806)
///   #var("eta_w", 0.8)
/// ]
/// ```
///
/// ```typ
/// #var-line(label: "Teilsicherheitsbeiwerte", norm: "SIA 265", norm-ref: "2.2.5")[
///   #var("gamma_M", 1.7)
///   #var("eta_M", 1)
/// ]
/// ```
///
/// A row of what is declared here beside what is read from the export, and a value hidden by its own level -- which takes its separator with it, where a hand-typed one would be left behind:
///
/// ```typ
/// #var-line(sep: ",")[
///   #var("b", 100, "mm")
///   #var("h", 200, "mm", level: 0)
///   #val("s_k", domain: ("snow-load", "SL"), type: "expression")
/// ]
/// ```
///
/// A whole row at `level: 0` declares its variables and prints nothing, not even the space of a line -- the inputs of a formula the page shows:
///
/// ```typ
/// #var-line(level: 0)[
///   #var("gamma_M", 1.7)
///   #var("eta_M", 1)
/// ]
/// #var("R_k", 7, "kN", level: 0)
/// #eq("R_d", `R_k dot eta_M / gamma_M`)
/// ```
///
/// `#var`, `#var-unit`, `#eq`, `#val` and `#verify` all know they are in a row: each prints inline instead of taking a line of its own, and its own label and citation become one footnote whatever its `note:` says, since a row has one citation column for all of it. Anything else in the body is printed as it comes, without a separator.
/// - label (none, str): a name for the row, printed before the first value with a colon -- a var's `group_label` (section 3.3), for a line written by hand. Left out where the whole row is hidden.
/// - norm (none, str), norm-ref (str): one citation for the row, in the right-hand column from level 3. An item's own citation stays in its own footnote.
/// - level (int, auto): one level for the whole row, overriding each item's own -- `level: 0` declares the variables and prints nothing, not even the space of a line. auto leaves every item to its own level.
/// - sep (auto, str): what the values are joined with. auto is the engine's own semicolon, which carries French's narrow space before it.
/// - body (content): the declarations, in any order, one per line or several on one.
/// -> content
#let var-line(label: none, norm: none, norm-ref: "", level: auto, sep: auto, body) = bib-note(norm) + context {
  // The row's own citation is registered for the bibliography outside this context, as `val`'s is (v0.99); each item of the row registers its own.
  check-level("var-line", level)
  if not (sep == auto or value-type(sep) == str) {
    panic("var-line: sep must be auto or a string, got " + repr(sep))
  }

  // ⚠️ The spaces between the items are dropped. A body written one `#var` to a line carries the newline between them as a `space` child, which would stand *before* the separator the row writes itself -- "R_k = 7 kN ; k_dens = 0.806".
  let items = if body.has("children") {
    body.children.filter(c => not (repr(c.func()) in line-filler)).join()
  } else { body }

  let st = (count: 0, label: label, sep: sep, level: level)
  var-line-state.update(st)
  // A row the level hides still declares its variables: the body is emitted, every item prints nothing, and no grid is laid out around it -- an empty row would otherwise leave the space of a line behind.
  if level != auto and resolve-level(level) < 1 {
    items
  } else {
    // The row's citation follows its items': in the right-hand column from level 3, never below it.
    let lv = resolve-level(level)
    annotated-rows(((items, if lv >= 3 and norm != none { (norm: norm, norm_ref: norm-ref) } else { none }),))
  }
  var-line-state.update(none)
}

// The relation a failed comparison is printed with instead: the line then states something true, and the ✘ says the relation the report *wanted* is not the one that holds.
#let relation-negation = ("<=": ">", ">=": "<", "<": ">=", ">": "<=", "=": "!=", "!=": "=")

// The operators a relation may be written with, two characters first so that `<=` is never read as `<`.
#let relation-ops = ("==", "<=", ">=", "!=", "≤", "≥", "≠", "<", ">", "=")

// One side of a relation, read against the registry: its value and unit, and what it is -- `"number"` for a bare number, `"var"` for exactly one variable, `"formula"` for anything else -- with the math source of its symbols (`letters`) and, for a formula, of the same formula with the numbers put in (`numbers`). A bare number has neither.
#let relation-side(d, src, digits) = {
  let trimmed = src.trim()
  let got = evaluate-formula("verify", d, trimmed)
  if got.result == none {
    panic("verify: cannot evaluate " + repr(trimmed) + " -- verify compares numbers, and reads the same formulas #eq does")
  }
  // A side that is exactly one variable keeps that variable's own unit, rather than being handed the one the preference table would pick: `F_Ed <= R_d` must print the kN the report wrote, whatever their size.
  let one = if got.operands.len() == 1 and got.operands.first().key == trimmed { got.operands.first() } else { none }
  // A bare number written with its unit keeps that unit, for the same reason: `eta <= 100 "%"` prints 100 %, where the table would have made it 1 (v0.88, the member checks' utilisation in percent).
  let literal = trimmed.match(regex("^([0-9]+(?:\.[0-9]+)?)\s*\"([^\"]+)\"$"))
  let shown = if one != none { (value: one.value, unit: one.unit) } else if literal != none { (value: float(literal.captures.at(0)), unit: literal.captures.at(1)) } else { present("verify", trimmed, got.result, auto, unit-table(d)) }
  // Through placeholders, as `#eq` substitutes: one key replaced after another rewrote the symbol an earlier one had just become.
  let (letters, numbers) = formula-lines(trimmed, got.operands, digits)
  let kind = if got.operands.len() == 0 { "number" } else if one != none { "var" } else { "formula" }
  (base: got.result.base, dims: got.result.dims, value: shown.value, unit: shown.unit, kind: kind,
   letters: if kind == "number" { none } else { letters }, numbers: if kind == "formula" { numbers } else { none })
}

// One side as the relation prints it at `lv`. Level 1 the symbols, level 2 the value, level 3 everything: a variable `F_Ed = 12 kN`, a formula `F_Ed / R_d = 12 kN / 24 kN = 0.5` -- its letters, its numbers and its value (v0.86, the engineer: «au niveau 3 doit afficher F_Ed/R_d = 12 kN/24 kN = 0.5 <= 1»). A bare number is its value at every level. `mirrored` writes the right-hand side the other way round, the value first, so that the two values meet at the sign, which is what the eye compares.
// Returned as the segments the side's `=` signs part, so that a relation too wide for its line can be stacked at them (verify); joined with " = " they are the side as one line.
// `brief` (verify-core, the member checks' verdict, issue #12): at level 1 the symbols *and* the value, `σ_t,0,d / f_t,0,d = 0.41`, where `verify` prints the symbols alone.
#let relation-segments(side, lv, mirrored, digits, brief: false) = {
  let value = if side.unit == "" { fmt-magnitude(side.value, digits) } else { formula-quantity(side.value, side.unit, digits) }
  if side.kind == "number" or lv == 2 { return (value,) }
  if lv <= 1 { return if brief { (side.letters, value) } else { (side.letters,) } }
  let chain = (side.letters,) + (if side.kind == "formula" and side.numbers != side.letters { (side.numbers,) } else { () }) + (value,)
  if mirrored { chain.rev() } else { chain }
}

// The indent a stacked relation sets its `=` at where its first line is a whole formula rather than one variable: the formula's own width would put the `=` of the next line past the end of the widest one.
#let relation-indent = 2em

// How tall a relation may be before its rules are measured to its ink: a line of roots and indices, what only a built-up fraction exceeds (calc-engine.typ's tall-row-height, the same test).
#let tall-relation = 1.2em

// What `verify` does, with what only the engine asks of it (issue #12, the member checks' verdict, lib/timber.typ `timber-verdict`): `brief` prints a side that is a formula at level 1 as its symbols *and* its value; `left-unit` shows the left-hand side's value in that unit -- `"%"`, a ratio of 0.41 shown as 41 % --; `left-only` prints the left-hand side and the mark and not the relation's sign nor its right-hand side, the comparison still made against it (the engineer, 09.10.2026: «afficher sigma/f = 41 %», and not «⩽ 100 %» besides).
#let verify-core(relation, level: auto, brief: false, left-unit: none, left-only: false) = context {
  check-level("verify", level)
  // a `*` is a product, printed as `dot` (star-as-dot)
  let src = star-as-dot(if type(relation) == str { relation } else { relation.text })
  // In list order, so a `<=` is never read as a `<`; the first operator found wins.
  let found = none
  for o in relation-ops {
    if found == none {
      let i = src.position(o)
      // the length in bytes, which is what slice counts: ≤ is one cluster and three bytes, and counting clusters crashed every relation written with ≤, ≥ or ≠ (v0.86)
      if i != none { found = (op: o, at: i, len: o.len()) }
    }
  }
  assert(found != none,
    message: "verify: no relation in " + repr(src) + " -- write one of " + relation-ops.join(", "))

  let key = test-aliases.at(found.op, default: found.op)
  let d = var-registry.get()
  let digits = number-digits.get()
  let l = relation-side(d, src.slice(0, found.at), digits)
  let r = relation-side(d, src.slice(found.at + found.len), digits)
  if left-unit == "%" { l = (..l, value: l.base * 100, unit: "%") }

  assert(dims-equal(l.dims, r.dims),
    message: "verify: comparing " + dims-text(l.dims) + " with " + dims-text(r.dims)
      + " -- the two sides of " + repr(src) + " must have the same dimensions")

  let holds = (test-relations.at(key).holds)(l.base, r.base)
  let shown-op = if holds { key } else { relation-negation.at(key) }
  let st = var-line-state.get()
  let lv = line-level(st, level)

  // At level 3 the right-hand side is written the other way round -- value, numbers, symbols -- so the two values meet in the middle of the line, which is what the eye compares.
  let left = relation-segments(l, lv, false, digits, brief: brief)
  let right = if left-only { () } else { relation-segments(r, lv, true, digits) }
  let op = test-relations.at(shown-op).math

  let body = eval(left.join(" = ") + (if left-only { "" } else { " " + op + " " + right.join(" = ") }), mode: "math")
  let colour = if holds { test-ok } else { test-nok }
  // Two nested boxes, each drawing a bottom rule, rather than two nested `underline`s: underline decorates the text runs it finds, so inside an equation it comes out under the units and not under the numbers between them.
  let rule = (bottom: 0.9pt + colour)
  let (outer, inner) = (1.7pt, 3.4pt)
  // The inner box is measured to the ink at its foot: a display fraction (`show math.frac: it => $display(it)$`, the engineer's config.typ) reaches below the text's own bottom edge, and the rule, drawn at that edge, crossed the denominator of the last line (v0.88). A relation without one keeps the height it had.
  let ruled(x) = box(stroke: rule, inset: (bottom: outer), outset: (x: 1pt), box(stroke: rule, inset: (bottom: inner), {
    set text(bottom-edge: "bounds") if measure(x).height > tall-relation.to-absolute()
    x
  }))
  // ⚠️ The heavy glyphs, U+2714 and U+2718, never the light ✓ and ✗: Libertinus Serif, the font this report is set in, covers the heavy pair and not the light one, and Typst warns about neither. Never bold either -- Libertinus Serif Bold covers neither pair. The colour and the size carry it. `lift` raises it onto the last line of a stacked relation, whose ruled box stands on its bottom edge rather than on a line's baseline.
  let mark(lift: 0pt) = box(baseline: -0.12em - lift, text(fill: colour, size: 1.15em, if holds { "✔" } else { "✘" }))
  let marked = {
    ruled(body)
    h(0.35em)
    mark()
  }
  // Already inline content, so a row only has to join it: what `var-line` adds is the separator before it (v0.80). The comparison itself is made at every level, level 0 included -- two sides of different dimensions stop the compile whether or not the line is printed.
  if lv < 1 { return }
  if st != none { return line-item(st, marked) }
  if left.len() + right.len() <= 2 { return marked }
  // A relation wider than its line is stacked at its signs, as `#eq` stacks a formula (annotated-rows): the left side's letters, then `= <numbers>`, then `= <value> ⩽ <the right side>` -- as much of it on each line as the width holds, so the two values the eye compares stay together where they can -- each sign under the one before, the whole double-ruled and marked as the one line is. A display fraction is one atom no line break can enter, so without this the relation ran off the page. What fits is set exactly as before, in a box the width of the line it stands in, so it still sits in a sentence.
  box(layout(size => {
    if measure(marked).width <= size.width + 0.01pt { return marked }
    // The signs stand where the first line's would: after its variable, or -- where the first line is a whole formula, as wide as the widest line -- at a fixed indent.
    let pad = box(width: if l.kind == "var" { measure(eval(left.first(), mode: "math")).width } else { relation-indent })
    let line(src) = eval("#chain-pad " + src, mode: "math", scope: (chain-pad: pad))
    let pieces = left.slice(1).map(s => "= " + s) + (if left-only { () } else { (op + " " + right.first(),) + right.slice(1).map(s => "= " + s) })
    let rows = ()
    let current = none
    for p in pieces {
      let candidate = if current == none { p } else { current + " " + p }
      if current != none and measure(line(candidate)).width > size.width + 0.01pt { rows.push(current); current = p } else { current = candidate }
    }
    rows.push(current)
    let lines = (eval(left.first(), mode: "math"),) + rows.map(line)
    // the lines of one relation, as close as #eq's stacked lines: measured to their ink between them, and to the text's own edges above the first and below the last, so the rules stand under the last as they stand under the one line
    let edges(i) = (top: if i == 0 { auto } else { "bounds" }, bottom: if i == lines.len() - 1 { auto } else { "bounds" })
    let inked(x, top, bottom) = block({
      set text(top-edge: top) if top != auto
      set text(bottom-edge: bottom) if bottom != auto
      x
    })
    let stacked = grid(columns: (auto,), row-gutter: chain-leading, ..lines.enumerate().map(((i, x)) => inked(x, edges(i).top, edges(i).bottom)))
    // how far the last line's foot lies below its baseline, and the two insets under it: what the mark is raised by to stand on that line, the ruled box standing on its bottom edge rather than on a line's baseline
    let last = edges(lines.len() - 1)
    let below = measure(inked(lines.last(), last.top, last.bottom)).height - measure(inked(lines.last(), last.top, "baseline")).height
    ruled(stacked)
    h(0.35em)
    mark(lift: below + outer + inner)
  }))
}

/// States a relation between the report's variables, **performs it**, and marks the answer: double-ruled in green with a ✔ where it holds, in red with a ✘ where it does not.
///
/// ```typ
/// #var("F_Ed", 2.037, "kN")
/// #var("R_d", 4.969, "kN")
///
/// #verify(`F_Ed <= R_d`)
/// ```
///
/// ```typ
/// #var("F_Ed", 6.2, "kN")
/// #var("R_d", 4.969, "kN")
///
/// #verify(`F_Ed / R_d <= 1`)
/// ```
///
/// A side that is a whole formula is printed at level 3 as its letters, then the same with the numbers put in, then its value -- `F_Ed / R_d = 12 kN / 24 kN = 0.5 ⩽ 1`:
///
/// ```typ
/// #var("F_Ed", 12, "kN", level: 0)
/// #var("R_d", 24, "kN", level: 0)
/// #verify(`F_Ed / R_d <= 1`, level: 3)
/// ```
///
/// At `level: 0` the relation is still performed -- two sides of different dimensions still stop the compile -- and nothing is printed; the line below names the same variables:
///
/// ```typ
/// #var("F_Ed", 2.037, "kN", level: 0)
/// #var("R_d", 4.969, "kN", level: 0)
/// #verify(`F_Ed <= R_d`, level: 0)
/// #eq("eta", `F_Ed / R_d`)
/// ```
///
/// **The printed sign follows the truth.** Where `F_Ed <= R_d` does not hold, the line prints `F_Ed > R_d`: what is written is then a true statement, and the ✘ is what says the relation the report wanted is not the one that holds.
///
/// The comparison is made on the **full** values, not on the decimals printed, so two numbers that print alike can still be marked ✘; a tie is absorbed at a relative 1e-9. Two sides whose dimensions differ stop the compile -- comparing a kN with a kNm is a mistake at the call site, not a comparison.
///
/// ⚠️ Untraced, like everything computed in Typst (section 1): it carries no citation and no `source`. It guarantees that the mark agrees with the numbers beside it, not that those numbers are right.
/// - relation (content, str): the relation, in math source naming the registry's keys. `<=`, `>=`, `<`, `>`, `=`, `==`, `!=` (and ≤, ≥, ≠). `*` multiplies, as `dot` does, and is printed as it. What is quoted -- a literal's unit, `(21 "N/mm²")` -- is never read as a name.
/// - level (int, auto): 0 prints nothing (the relation is still performed), 1 the symbols alone, 2 the values alone, 3 all of it -- a variable as `F_Ed = 2.037 kN`, a formula as its letters, its numbers and its value, a bare number as itself, and the right-hand side reversed, `F_Ed = 2.037 kN ⩽ 4.969 kN = R_d`. auto follows the report.
/// -> content
#let verify(relation, level: auto) = verify-core(relation, level: level)
