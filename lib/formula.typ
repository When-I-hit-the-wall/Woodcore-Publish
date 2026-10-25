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
#import "calc-engine.typ": cite-text, uniform-level, show-masked, sync-depth, note-column, note-gutter, load-domain-state, annotated-rows, chain-leading, chain-line, colon-str, connection-domain, connector-domain, ids, find-calculation, formula-chain, get, norm-text, render-prose, render-symbol, render-table, resolve-level, semicolon-str, source-label, t-str, test-aliases, test-nok, test-ok, test-relations, tl-str, value-type, var-current, var-lookup, var-names, var-registry, var-store, display-number, display-quantity, display-source, sup, superscript-digits, math-eval, greek-names
// The minimum distances of SIA 265 computed with a diameter (lib/distance.typ, v0.87): imported here by name, so commands.typ, which re-exports this file at the wildcard, gives every section `distance` and none of its helpers.
#import "distance.typ": distance
// The bibliography (lib/bibliography.typ, v0.99): its two commands by name, on distance.typ's arrangement, and `bib-note` -- which every command below that takes a `norm:` emits **before its context**, so that the document it cites is listed at the end (docs/typst/api-conventions.md §10bis).
#import "bibliography.typ": bib-note, cite-norm, show-bibliography
// The list of the norms a document cites (lib/document.typ), by name -- the parametric objects of the documents left with their own commands when the documents were written in raw Typst (spec 2026-10-21-commandes-typst-refonte, REQ-019); document.typ imports calc-engine.typ and bibliography.typ and nothing from this file, so the chain stays acyclic.
#import "document.typ": show-norm-list
// The export sheets (lib/sheet.typ, v0.114): the page and the three images a sheet's `#place` holds besides the plans (spec 2026-10-21-commandes-typst-refonte, Q-013, Q-015) -- sheet.typ imports calc-engine.typ, document.typ and positions.typ and nothing from this file, so the chain stays acyclic.
#import "sheet.typ": sheet, image-legend, image-section, image-titleblock
// A position on its line (lib/positions.typ, spec 2026-10-21-commandes-typst-refonte, REQ-015): positions.typ imports calc-engine.typ and nothing else, and sheet.typ imports its table builders, so the chain calc-engine -> positions -> sheet -> formula stays acyclic.
#import "positions.typ": position

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

// A unit written by hand with a caret, spelt as the report prints one: `N/mm^2` → `N/mm²`, `m^3` → `m³`. Applied where a unit enters from a call -- `var`, `var-unit`, `eq`'s `unit:`, `unit`, `val`'s `unit:` -- so that the registry holds one spelling and every line printing it shows a real exponent (v0.86, the engineer's request: a caret is quicker to type than ², which a Swiss keyboard has no key for). parse-unit already read `^2` as an exponent; only the page showed the caret, for the reason `superscript-digits` gives.
// Only `^` followed by digits, which is all parse-unit reads after a caret: `^-1` is left as written, and refused where it is read.
#let written-unit(u) = {
  if type(u) != str { return u }
  // per mille is written "%%", two signs one after the other as the keyboard has them, and printed ‰ (the engineer, 22.10.2026)
  let u = u.replace("%%", "‰")
  if not u.contains("^") { return u }
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

// The Greek names math knows are lib/subscript.typ's `greek-names`, imported above: the subscript rule writes them as their letters (UI-001).

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
// ⚠️ Since the fine arguments (spec 2026-10-21-commandes-typst-refonte, REQ-005) the table is three layers: the document's (`units`), the domains' open around the line (their frames' `units`, innermost last), and the next answer's (`next-units`) -- the last one written for a dimension wins.
#let unit-table(d) = {
  let table = d.at("units", default: default-units)
  for f in d.at("frames", default: ()) { for (k, u) in f.units.pairs() { table.insert(k, u) } }
  for (k, u) in d.at("next-units", default: (:)).pairs() { table.insert(k, u) }
  table
}

// How far a `#unit` or a `#calc-defaults` reaches (REQ-005, REQ-006): the next line it concerns, the rest of the domain it stands in -- the document's rest where it stands in none --, the rest of the document.
#let scopes = ("next", "domain", "document")

#let check-scope(fn, scope) = {
  if not (scope in scopes) { panic(fn + ": scope: " + repr(scope) + " is not one of " + scopes.map(s => repr(s)).join(", ") + " -- the next line, the rest of the domain, the rest of the document") }
}

// A unit set for one dimension at one scope, in the registry: the next answer of that dimension (`next-units`, spent by it -- `spend-next-unit`), the innermost domain (its frame's `units`, gone with it), the document (`units`).
#let set-unit(d, dims-key, written, scope) = {
  let frames = d.at("frames", default: ())
  if scope == "next" {
    let next = d.at("next-units", default: (:))
    next.insert(dims-key, written)
    d.insert("next-units", next)
  } else if scope == "domain" and frames.len() > 0 {
    let f = frames.last()
    f.units.insert(dims-key, written)
    frames.at(frames.len() - 1) = f
    d.insert("frames", frames)
  } else {
    let table = d.at("units", default: default-units)
    table.insert(dims-key, written)
    d.insert("units", table)
  }
  d
}

// The unit `#unit(scope: "next")` set for this dimension, spent by the first answer of it.
#let spend-next-unit(d, dims) = {
  let next = d.at("next-units", default: (:))
  let k = dims-text(clean-dims(dims))
  if k in next {
    let _ = next.remove(k)
    d.insert("next-units", next)
  }
  d
}


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
// A number as it is **printed** takes the typographic minus, U+2212, for its sign and never the hyphen `fmt-decimals` and `fmt-magnitude` write (v0.87, the engineer: «un signe moins doit être affiché»): calc-engine.typ's `signed-text`, one rule for both files. Applied at the point of display and nowhere earlier, so that nothing is converted twice and every string that is read again -- math source, where math sets a hyphen as a minus by itself; the registry; an SVG -- keeps the hyphen it can parse.

// `fmt-number`'s counterpart for a value written by hand: the same line, with the scientific notation above. A value that is a word rather than a number goes through the glossary, as it does everywhere else (docs/typst/language.md §4bis). The number and its unit are joined by a no-break space, as fmt-number joins them (v0.86): a line ending on «R_d = 4.969» and the next beginning with «kN» is what a plain space allowed.
#let formula-number(value, unit) = {
  if type(value) != str { return display-quantity(value, unit) }
  let s = tl-str(value)
  if unit == "" { s } else { s + "\u{a0}" + unit }
}

// `quantity-in-formula`'s counterpart: "5.544 kN" as **quoted math source**, one atom, with a typographic minus for a sign -- quoted text keeps a hyphen where math would set a minus.
#let formula-quantity(x, unit) = {
  let s = display-number(x)
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
#let substituted(value, unit) = {
  if type(value) != int and type(value) != float { return "\"" + str(value) + "\"" }
  if unit != "" { return formula-quantity(value, unit) }
  // a negative one in parentheses, so "a - b" never reads "a - -b" (display-source)
  display-source(value)
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

#let formula-lines(src, operands) = {
  let coded = src
  for (i, o) in operands.enumerate() { coded = replace-word(coded, o.key, placeholder(i)) }
  // the short names of the inverse functions are printed as math knows them (formula-display-names)
  for (short, long) in formula-display-names { coded = replace-word(coded, short, long) }
  let letters = coded
  let numbers = coded
  for (i, o) in operands.enumerate() {
    letters = letters.replace(placeholder(i), atom-symbol(o.symbol))
    numbers = numbers.replace(placeholder(i), substituted(o.value, o.unit))
  }
  (letters, numbers)
}

// --- The fine display arguments, and the level as a preset of them (spec 2026-10-21-commandes-typst-refonte, REQ-001, REQ-005 to REQ-008, ARCH-001) ---
// What a line of `#var`, `#eq` and `#verify` shows is set by **fine arguments**, one per thing it may show and where: `display` (what of the line itself -- its symbol, its value, its unit; on `#eq`, `display-formula` and `display-equation`), `label-position`, `descr-position` and `norm-position`. A level is no longer a scale of its own but a **preset** of them, `lib/display-presets.json`, which reproduces what each level printed before the fine arguments existed. The engineer's order decides which layer wins (REQ-007): the call's argument, the call's level, `#calc-defaults` of the domain, the domain's level, `#calc-defaults` of the document, the document's level -- and `--input uniform=N` alone over the arguments written (Q-005), save in a `#sync`, whose content prints as it is written (Q-007).
//
// ⚠️ The layers live in the registry's own dictionary -- `defaults` for the document, `frames` for the domains open around a line, `next` for the next line --, for var-domain's reason: an update cannot read another state, and a command resolves what it can of them in its update. The last two layers, the document's level and the uniform one, are states, read in the command's context by `resolve-display`.
#let display-presets = json("display-presets.json").commands
// The families of presets (Q-014, 21.10.2026): `inline`, the default, and `block` -- the same visibility at each level, the label after the line and the citation in the right-hand column, the line set apart, what `note: "line"` printed. A domain chooses one with `#calc-defaults(presets: "block", scope: "domain")`; a line written `note: "line"` is printed with `block`.
#let display-families = (inline: display-presets, block: json("display-presets.json").block)

// The values each fine argument takes: what the engineer listed (20.10.2026), refused otherwise naming the argument and the values (REQ-001). Read from display-presets.json since the spec 2026-10-22-onglet-neige-type (D-17), where Python reads them too (calc/line_display.py): one list for the two.
#let fine-values = json("display-presets.json").at("fine-values")
#let display-values = fine-values.at("display")

// The fine arguments each command takes: `#verify` has no `display: "value"` -- the engineer's list for it --, and no `style:`, its double rule saying whether the relation holds. From display-presets.json too.
#let fine-keys = json("display-presets.json").at("fine-keys")

// The role a line has where nothing states one (D-9): a `#var` writes a datum down, an `#eq` computes, a `#verify` concludes.
#let default-roles = ("var": "data", "eq": "compute", "verify": "result")

// One fine argument checked against its values -- `auto` is always allowed, and means «not written».
#let check-fine(fn, name, value) = {
  if value == auto { return }
  let allowed = fine-values.at(name)
  if fn == "verify" and name == "display" { allowed = allowed.filter(v => v != "value") }
  if not (value in allowed) {
    panic(fn + ": " + name + ": " + repr(value) + " is not one of " + allowed.map(v => repr(v)).join(", "))
  }
}

// The fine arguments a call wrote, as a dictionary without its `auto`s: the strongest layer.
#let written-fine(fn, args) = {
  let out = (:)
  for (name, value) in args.pairs() {
    check-fine(fn, name, value)
    if value != auto { out.insert(name, value) }
  }
  out
}

// What a level presets of a command's fine arguments, in a family of presets.
#let preset(command, lv, family: "inline") = display-families.at(family).at(command).at(str(lv))

// The next line's `#calc-defaults` and `#unit`, taken by the update of the line that consumes them: `next` emptied, what it held kept under `last-next` for that line's context, which reads the registry after its own update (REQ-005, REQ-006).
#let take-next(d) = {
  d.insert("last-next", d.at("next", default: (:)))
  d.insert("next", (:))
  d
}

// The frame a domain opens around its lines: its id, its level, the `#calc-defaults` and the `#unit` given for it (scope: "domain"). One per open `#domain` or `var-domain`, innermost last; what they held is gone with them when the domain closes.
#let push-frame(d, id, level) = {
  let frames = d.at("frames", default: ())
  frames.push((id: id, level: level, defaults: (:), units: (:)))
  d.insert("frames", frames)
  d
}
#let pop-frame(d) = {
  let frames = d.at("frames", default: ())
  if frames.len() > 0 { d.insert("frames", frames.slice(0, -1)) }
  d
}

// The layers of `#calc-defaults` a line reads, from the strongest: the one given for it alone, then the domains' from the innermost out, then the document's.
#let default-layers(d, next-key) = (d.at(next-key, default: (:)),) + d.at("frames", default: ()).rev().map(f => f.defaults) + (d.at("defaults", default: (:)),)

// The role a line takes: the one written, else the defaults' (`default-layers`), else the command's own (D-9). Resolved in the update, being a pure function of the registry, and stored with the variable for `#var-table`. Read before `take-next`, so the next line's defaults are still `next`.
#let resolve-role(command, written, d) = {
  if written != auto { return written }
  for layer in default-layers(d, "next") { if "role" in layer { return layer.role } }
  default-roles.at(command)
}

// The style a line takes where it writes none, by the same layers; `none` where none says one. Read in the context, after `take-next`.
#let resolve-style(written, d) = {
  if written != auto { return if written == "normal" { none } else { written } }
  for layer in default-layers(d, "last-next") { if "style" in layer { return if layer.style == "normal" { none } else { layer.style } } }
  none
}

// The fine arguments a line is printed with, and the level it stands at: every layer of REQ-007 from the strongest down, the first to say a thing deciding it. Call inside the command's context, with the registry as its own update left it (`last-next` holding what `#calc-defaults(scope: "next")` gave it). `written` is what the call wrote, `level` its `level:`.
//
// The level returned is the one a level-bound thing still reads -- an item of a `var-line`, the metadata --: the first layer that states one, the uniform level over all.
#let resolve-display(command, written, level, d, family: auto) = {
  let keys = fine-keys.at(command)
  // a line a `#sync` holds keeps what its call states: the uniform level stops at a value kept in step (lib/calc-engine-core.typ, `sync`)
  let forced = if sync-depth.get() > 0 { none } else { uniform-level.get() }
  // the family of presets: the line's own (a call written `note: "line"`), else the first layer of `#calc-defaults` to choose one, else inline (Q-014)
  let family = if family != auto { family } else {
    let chosen = default-layers(d, "last-next").find(layer => "presets" in layer)
    if chosen == none { "inline" } else { chosen.presets }
  }
  let preset(command, lv) = display-families.at(family).at(command).at(str(lv))
  let layers = (written,)
  let lv = none
  let with-level(layer) = {
    let out = (layer,)
    if layer.at("level", default: auto) != auto { out.push(preset(command, layer.level)) }
    out
  }
  if level != auto { layers.push(preset(command, level)); lv = level }
  let next = d.at("last-next", default: (:))
  layers += with-level(next)
  if lv == none and next.at("level", default: auto) != auto { lv = next.level }
  for f in d.at("frames", default: ()).rev() {
    layers += with-level(f.defaults)
    if f.level != auto { layers.push(preset(command, f.level)) }
    if lv == none and f.defaults.at("level", default: auto) != auto { lv = f.defaults.level }
    if lv == none and f.level != auto { lv = f.level }
  }
  let doc = d.at("defaults", default: (:))
  layers += with-level(doc)
  if lv == none and doc.at("level", default: auto) != auto { lv = doc.level }
  if lv == none { lv = resolve-level(auto) }
  layers.push(preset(command, lv))
  let settings = (:)
  for k in keys {
    let found = layers.find(layer => k in layer)
    settings.insert(k, found.at(k))
  }
  // `--input uniform=N`: one level throughout, the arguments written included -- what a uniform report is for (Q-005)
  if forced != none {
    lv = forced
    settings = preset(command, forced)
  }
  // the preview of «Affichage» (`show-masked`, spec 2026-10-22-onglet-neige-type, UI-011): a line that would show nothing is printed at level 3's preset, `masked` saying so to the command, which prints it pale
  let masked = false
  if show-masked.get() and (if command == "eq" { settings.at("display-formula") == "none" and settings.at("display-equation") == "none" } else { settings.at("display", default: none) == "none" }) {
    masked = true
    settings = preset(command, 3)
  }
  (settings: settings, lv: lv, family: family, masked: masked)
}

// A line the report hides, printed by the preview of «Affichage» (`show-masked`): pale, and marked so after it.
#let masked-line(body) = if body == none { none } else {
  set text(fill: luma(150))
  body
  h(0.3em)
  text(size: 0.75em, style: "italic")[(#t-str("formula.masked"))]
}

// `level: 0` and `display: "none"` are one thing since the fine arguments (REQ-007): nothing of the line is printed.
#let shows-nothing(command, s) = if command == "eq" { s.at("display-formula") == "none" and s.at("display-equation") == "none" } else { s.at("display") == "none" }

// An `id:` given to a line of `#var`, `#eq` or `#verify`: what Woodcore finds the line by, wherever it stands in its file (REQ-001, REQ-012). Once per domain, for the three commands together -- counted by an update and refused in a context, which always runs, where a refusal in the update would be silent.
#let check-line-id(fn, id) = {
  if id != none and (type(id) != str or id.trim() == "") { panic(fn + ": id: is a non-empty string, got " + repr(id)) }
}
#let count-line-id(d, id) = {
  if id == none { return d }
  let seen = d.at("verify_ids", default: (:))
  let k = var-current(d) + "/" + id
  seen.insert(k, seen.at(k, default: 0) + 1)
  d.insert("verify_ids", seen)
  d
}
#let refuse-twice(fn, id, d) = {
  if id == none { return }
  let here-domain = var-current(d)
  if d.at("verify_ids", default: (:)).at(here-domain + "/" + id, default: 0) > 1 {
    panic(fn + ": the id " + repr(id) + " is given to two lines of " + (if here-domain == "" { "the report outside every domain" } else { "the domain " + repr(here-domain) }) + " -- an id names one line")
  }
}

// A label, a description and a citation placed by their fine arguments, around a line already built: `before` and `after` on the line, `footnote` gathered into the **one** footnote of the line (line-note's rule: three markers side by side read as one three-digit number), `in-line` after the line in the citation grey, `line-right` in the right-hand column -- which makes the line a block of its own (`annotated-rows`). `record` carries `label`, `description`, `choices`, `norm` and `norm_ref`. Returns what to set before the line, after it, its footnote, and the citation of the right-hand column, each `none` where there is nothing.
#let placed-extras(record, s) = {
  let label = record.at("label", default: none)
  let descr = record.at("description", default: none)
  let choices = record.at("choices", default: none)
  let norm = record.at("norm", default: none)
  let before = if s.at("label-position") == "before" and label != none { [#render-prose(tl-str(label))#colon-str()#h(0.35em)] } else { none }
  let after = ()
  if s.at("label-position") == "after" and label != none { after.push([ --- #render-prose(tl-str(label))]) }
  if s.at("descr-position") == "after" and descr != none { after.push([ (#render-prose(tl-str(descr)))]) }
  if s.at("norm-position") == "in-line" and norm != none { after.push([ #cite-text(norm-text(record), size: auto)]) }
  let parts = ()
  if s.at("label-position") == "footnote" and label != none { parts.push(render-prose(tl-str(label))) }
  if s.at("descr-position") == "footnote" and descr != none { parts.push(render-prose(tl-str(descr))) }
  if s.at("descr-position") == "footnote" and choices != none {
    parts.push(choices.map(c => [#render-symbol(record) = #render-prose(tl-str(c.value))#colon-str() #render-prose(tl-str(c.desc))]).join(linebreak()))
  }
  if s.at("norm-position") == "footnote" and norm != none { parts.push(norm-text(record)) }
  let note = if parts.len() == 0 { none } else { [#h(0.2em)#footnote(parts.join([#semicolon-str() ]))] }
  let right = if s.at("norm-position") == "line-right" and norm != none { record } else { none }
  (before: before, after: if after.len() == 0 { none } else { after.join() }, footnote: note, right: right)
}


// --- The commands -------------------------------------------------------
// `var` writes a variable down, `eq` computes one from the others, `verify` states a relation between them, `var-unit` carries one into another unit, `unit` says which unit a whole dimension is printed in, and `var-domain` keeps two sets of variables apart. Between them the report never names a variable twice: the string given to `var` is the key a formula cites and, unless a second one is given, the symbol that is printed.
//
// Each of those that store something is **two pieces of content**: a `var-registry.update(...)`, then a `context` that reads the registry back and prints. The order matters and is the whole mechanism -- an update is a pure function of the dictionary, so the arithmetic runs there without reading a state, and the `context` placed after it sees the result. Reading and writing one state from inside one `context` is what Typst cannot be asked to do.
//
// ⚠️ And the corollary, which cost a silent refusal in v0.63: the function of an update runs **only where something reads that state**. A `panic` written inside one is silent in a document that never looks the registry up again -- so a check that must always fire belongs in the `context`, which is where `var-unit` refuses a name it cannot find and where `eq` reads the registry at every level.

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
  math-eval((if style == "double" { "dbl" } else { style }) + "(printed)",
    scope: (printed: body, dbl: double-rule))
}

// What one command says of itself to `typst query` (spec 2026-10-15, REQ-004): one label for all of them, `<woodcore-var>`, read by calc/domains/unfold.py (`query_state`) -- so that Woodcore learns what a domain holds from the compiler and never from parsing the file. Emitted from the command's context, where its value is known, outside every row item; invisible, at every level, level 0 included. A value that is not JSON (`auto`) is written as its repr.
#let wc-meta(fields) = {
  let plain(v) = if v == auto { "auto" } else if type(v) == dictionary { v.pairs().map(((k, x)) => (k, plain(x))).to-dict() } else if type(v) == array { v.map(plain) } else if type(v) in (str, int, float, bool) or v == none { v } else { repr(v) }
  // no space before the label: in markup it would be printed, a space before every separator of a row (found by tests/test_formula.py on the first build)
  [#metadata(plain(fields))<woodcore-var>]
}

#let var-argument-names = ("name-calc", "name-visible", "value", "unit", "domain", "display", "style", "role", "label", "label-position", "descr", "descr-position", "norm", "norm-section", "norm-position", "id", "level")

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

// The relative gap under which a value written beside `domain:` is taken as the one it names (docs/typst/formulas.md, «a literal checked by domain:», spec 2026-10-15). One constant for Typst; Python writes a value it unfolds with at least this precision (calc/domains/unfold.py LITERAL_TOLERANCE, held equal by tests/test_unfold.py).
#let literal-tolerance = 1e-6

// The largest relative gap a value written rounded may keep from the export and still agree with it: what a value typed by hand to the decimals it is printed at stays within.
#let literal-rounding = 1e-3

// A value written beside `domain:` against the value `domain:` reads: none where they agree, else the value read, in the written unit -- what the line prints in red as stale. A reference of another dimension than the written value is stale too, shown in its own unit. A reference that is a word, or a written value that is, agrees only when equal.
#let literal-stale(written, reference) = {
  let ref-value = reference.at("value", default: none)
  let ref-unit = reference.at("unit", default: "")
  if ref-unit == none { ref-unit = "" }
  let numeric = v => type(v) == int or type(v) == float
  if not numeric(written.value) or not numeric(ref-value) {
    return if written.value == ref-value { none } else { (value: ref-value, unit: ref-unit) }
  }
  let carried = if ref-unit == written.unit or written.unit == "" and ref-unit == "" { (value: ref-value, unit: written.unit, warning: none) } else {
    let a = parse-unit(ref-unit)
    let b = parse-unit(written.unit)
    if a == none or b == none or not dims-equal(a.dims, b.dims) { (value: ref-value, unit: ref-unit, warning: true) } else { converted("var", "", ref-value, ref-unit, written.unit) }
  }
  if carried.warning != none { return (value: ref-value, unit: ref-unit) }
  let scale = calc.max(calc.abs(written.value), calc.abs(carried.value))
  // A value written to fewer decimals than the export holds agrees where the export rounds to it -- 1.394 against 1.39411547558108 -- as long as that rounding stays within a relative `literal-rounding`: 25 written for an export's 25.4 is half a unit off and still stale. Otherwise the two agree within `literal-tolerance`, what Python's own writing keeps.
  let written-text = str(written.value)
  let decimals = if written-text.contains("e") or not written-text.contains(".") { 0 } else { written-text.split(".").at(1).len() }
  let rounding = calc.min(0.5 * calc.pow(10.0, -decimals), literal-rounding * scale)
  let gap = calc.abs(written.value - carried.value)
  if gap <= calc.max(literal-tolerance * scale + 1e-12, rounding) { none } else { (value: carried.value, unit: carried.unit) }
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

#let var-line-print(command, held, written, level, d, style, stale) = {
  // the number in red with the value the export now holds where it is stale -- the mark a literal checked by domain: carries
  let marked(number) = if stale != none {
    text(fill: test-nok, number) + text(fill: test-nok, size: 8pt, [~(#t-str("formula.stale", value: formula-number(stale.value, stale.unit)))])
  } else { number }
  let symbol = held.at("symbol", default: none)
  let warning = unit-warning(held.at("warning", default: none))
  let rd = resolve-display("var", written, level, d)
  let s = rd.settings
  let shown-line = if not shows-nothing("var", s) {
    let number = marked(formula-number(held.value, held.unit))
    let shown = if s.display == "variable" { math-eval(symbol) }
      else if s.display == "value" { marked(formula-number(held.value, "")) }
      else if s.display == "value-unit" { number }
      else { [#math-eval(symbol)~=~#number] }
    let value = apply-style(style, shown)
    let x = placed-extras(held, s)
    if rd.family == "block" or x.right != none {
      // The line set apart: its label after an em dash (v0.61.1, the engineer's own correction: what the variable *is* is read with it), its description in a footnote, its citation in the right-hand column -- the `block` presets (Q-014) or a citation placed on the right
      let line = [
        #x.before#value#x.after#x.footnote
      ]
      annotated-rows(((line, x.right),))
      if warning != none { warning }
    } else {
      // Inline, which is the default since v0.87 (the engineer: «de base, #var doit s'afficher inline, afin de pouvoir afficher plusieurs var les uns après les autres»): its footnote gathers what goes to the foot of the page
      inline-item([#x.before#value#x.after], x.footnote, warning)
    }
  }
  if rd.masked { masked-line(shown-line) } else { shown-line }
}

// References of the block below (moved out of it, issue #115): spec 2026-10-21-commandes-typst-refonte, REQ-002, Q-011; REQ-001.
/// Writes one variable down: it is stored under its name, where every formula below can name it, and printed -- **inline**, `symbol = value unit`, like a word of the sentence it stands in, so that several written one after the other run on in one paragraph and a blank line starts a new one.
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
/// #var("s_k", domain: ("snow-load", "SL"))
/// ```
///
/// **Without a value it prints a variable already declared** -- with everything it was declared with, its label, its citation and how it was shown, the level and the id aside -- and `unit:` shows it in another unit of the same dimension, for that line alone: the variable keeps its own, and the formulas below compute with it. `#val` and `#var-unit` were this until then.
///
/// ```typ
/// #var("R_d", 5, "kN", norm: "SIA 265", norm-section: "6.5.5.2", level: 0)
/// Der Widerstand beträgt #var("R_d") oder #var("R_d", unit: "N").
/// ```
///
/// A value written down somewhere else is named with `domain:` -- a **pair** being a calculation of the export and its instance, a **string** a `#domain` of the report. The first is the short form of `#var("R_d", var-of("connector", "SD-10", "R_d"))`, and the two store exactly the same thing:
///
/// ```typ
/// #var("s_k", domain: ("snow-load", "SL"))
/// ```
///
/// The second is what carries a result out of the column that computed it, so that a `#verify` below can name it -- a formula reads the current domain and the default one, and nothing else:
///
/// ```typ
/// #domain("Ende")[ #var("F", 0.55, "kN") ]
/// #var("F", domain: "Ende")
/// ```
///
/// A value **written beside** `domain:` is a literal checked by it: the number written is the one printed and computed with, and the export's is compared with it -- the same, nothing more; another, the written value is printed in red with the one the export now holds. It is how Woodcore writes a calculation it generates, so that the value can be read in the file and still cannot age unseen:
///
/// ```typ
/// #var("s_k", 1.394, "kN/m²", domain: ("snow-load", "SL"))
/// ```
///
/// **What is printed, and where**: `display` says what of the line itself -- `"variable"`, `"value"`, `"value-unit"`, `"variable-value-unit"` or `"none"` --, and `label-position`, `descr-position` and `norm-position` where its label, its description and its citation go: `"before"` and `"after"` on the line, `"footnote"` in its one footnote, `"in-line"` after it in grey, `"line-right"` in the right-hand column, which sets the line apart. A level is a preset of them, and an argument written wins over it (`lib/display-presets.json`):
///
/// ```typ
/// #var("R_k", 7, "kN", label: "Kapazität Sherpa XS", descr: "Aus dem Katalog des Herstellers", norm: "Sherpa", norm-section: "ETA-12/0197", label-position: "after", norm-position: "line-right", level: 3)
/// ```
///
/// ```typ
/// #var("gamma_M", 1.7, label: "Teilsicherheitsbeiwert", label-position: "before", norm: "SIA 265", norm-section: "2.2.5", norm-position: "in-line")
/// ```
///
/// At `level: 0` -- or `display: "none"` -- the variable is written down and nothing is printed, so that a formula below can name a coefficient the page does not show:
///
/// ```typ
/// #var("k_dens", 0.806, level: 0)
/// #var("R_k", 7, "kN", level: 0)
/// #eq("R_d", `k_dens dot R_k`)
/// ```
///
/// The line may be set apart the way `#eq` sets an answer: `style:` -- `"bold"`, `"underline"`, or `"double"`, which rules it twice underneath, for a value a section rests on.
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
/// ⚠️ There is no `#let`: Typst gives a function no way to bind a name in its caller's scope, so the name is the string, and the registry is where it lives (see `var-registry`). Read one back with `#var` without a value, or `get` in a context.
/// - ..rest (any): the positional arguments, whose four slots are the bullets below -- the name, the optional printed symbol, the value, then its optional unit, in that order. Variadic only because Typst has no optional positionals; every *named* argument is declared, so an editor shows them all.
/// - key (str): the name a formula cites -- the first positional, or `name-calc:`. Letters, digits and `_`; never a `-`, which a formula would read as a subtraction, nor a word a formula reads as an operation -- `dot`, `max`, `sqrt`. Where no symbol is given it is printed as a symbol written by hand would be: `k_dens` as k with the subscript "dens", `M2` as M and 2, `FEd` as one word.
/// - symbol (str): optional second positional argument, or `name-visible:`, the math source that is *printed* -- `"q_(k,11)"`. A word math does not know may be written without its quotes, `"W_(y,erf)"`. Left out, the key itself is printed, requoted by `key-symbol`.
/// - name-calc (str, none): the name, written by name rather than first -- `#var(name-calc: "l_1", name-visible: "l", value: 5, unit: "m")`.
/// - name-visible (str, none): the printed symbol, written by name. Beside `domain:` it is the symbol printed over the one read, never a value.
/// - value (int, float, dictionary, none): the value, written by name -- the number, or a var object which brings its own unit and description. Left out with every positional value, the line prints a variable already declared.
/// - unit (str, none): the value's unit, written by name; on a line that prints a variable already declared, the unit to show it in, for that line alone (same dimension, else the line says so in red).
/// - domain (none, str, array): where the value is read. A **pair** is a calculation of the export and its instance -- `("snow-load", "SL")`, `("connector", "SD-10")` -- and falls back to the domain named after that instance for a name the export does not carry; a **string** is a `#domain` of the report, and the variable is copied out of it into wherever this line stands. Either way the var of this same name is what is taken, with its unit, its symbol, its description and its citation -- `label:`, `norm:` and `norm-section:` still override what it carries.
/// - display (str, auto): what of the line is printed -- `"none"`, `"variable"` (the symbol), `"value"` (the number), `"value-unit"`, `"variable-value-unit"` (`symbol = value unit`). auto leaves it to the level.
/// - style (str, auto): `"normal"`, `"bold"`, `"underline"` or `"double"` (ruled twice underneath, the mark `verify` sets a relation with), applied to the **whole line**. auto leaves it to `#calc-defaults`, else normal.
/// - role (str, auto): what the value is to the calculation -- `"data"` (the default of `#var`), `"compute"`, `"result"` --, which `#var-table` lists by.
/// - label (str, none): what the value is -- «Expositionsbeiwert». It **overrides** the label a var object carries.
/// - label-position (str, auto): `"none"`, `"before"` (before the line, followed by a colon), `"after"` (after it, set apart by an em dash), `"footnote"`. auto leaves it to the level -- the footnote from level 2.
/// - descr (str, none): why *this* value was chosen. It overrides the description a var object carries.
/// - descr-position (str, auto): `"none"`, `"after"` (after the line, in parentheses), `"footnote"`. auto leaves it to the level -- the footnote from level 3, with the choices it explains.
/// - norm (str, none), norm-section (str, none): the citation -- the norm, and its clause or table, «SIA 265 6.5.5.2».
/// - norm-position (str, auto): `"none"`, `"in-line"` (after the line, in grey), `"line-right"` (in the right-hand column, the line then a block of its own), `"footnote"`. auto leaves it to the level -- the footnote from level 3.
/// - id (str, none): the name the line is found by -- by Woodcore in its file, and by `typst query` -- wherever it is moved. Once per domain, for `#var`, `#eq` and `#verify` together.
/// - level (int, auto): a preset of the fine arguments above -- 0 nothing, 1 the line, 2 also the label, 3 also the description and the citation (`lib/display-presets.json`) --, which an argument written overrides. auto follows the domain, else the report.
/// - norm-ref (str): written before `norm-section:`, which it is.
/// -> content
#let var(..rest, name-calc: none, name-visible: none, value: none, unit: none, domain: none, display: auto, style: auto, role: auto, label: none, label-position: auto, descr: none, descr-position: auto, norm: none, norm-section: none, norm-ref: "", norm-position: auto, id: none, level: auto) = {
  // ⚠️ The named arguments are declared one by one rather than swept into `..rest`, and that is what an editor reads: a function whose whole signature is `..args` shows as `var(args: arguments)` in a tooltip, and `label:`, `level:`, `norm:` are then invisible to the engineer writing the call (v0.63.1). Only the *positional* tail stays variadic, because the printed symbol is an optional second positional and Typst has no optional positionals.
  // ⚠️ `panic` inside an `if`, not `assert(cond, message: ...)`: Typst builds an assert's message *before* it tests the condition, so `unknown.first()` on an empty array fails every correct call.
  let unknown = rest.named().keys()
  if unknown.len() > 0 {
    panic("var: unknown argument " + repr(unknown.first())
      + " -- " + var-argument-names.map(n => repr(n)).join(", "))
  }
  // The name, the symbol, the value and the unit, written by position or by name (REQ-002): one tail of positionals after the name, whichever way they came.
  let pos = rest.pos()
  if name-calc == none and pos.len() == 0 { panic("var: write #var(\"key\", value) at least -- the name first, or name-calc:") }
  let key = if name-calc != none { name-calc } else { pos.first() }
  let tail = if name-calc != none { pos } else { pos.slice(1) }
  if name-visible != none {
    if tail.len() > 0 and type(tail.first()) == str { panic("var: " + repr(key) + " is given its symbol twice, by position and as name-visible:") }
    tail = (name-visible,) + tail
  }
  let declared-by-name = value != none
  if declared-by-name {
    if tail.filter(x => type(x) != str).len() > 0 { panic("var: " + repr(key) + " is given its value twice, by position and as value:") }
    tail.push(value)
    if unit != none { tail.push(unit) }
  }
  check-key("var", key)
  check-level("var", level)
  check-line-id("var", id)
  if norm-section != none and norm-ref != "" { panic("var: norm-section: and norm-ref: are one argument -- write norm-section: alone") }
  let norm-ref = if norm-section != none { norm-section } else { norm-ref }
  let written = written-fine("var", (display: display, label-position: label-position, descr-position: descr-position, norm-position: norm-position))
  // `style: none` was the default until the fine arguments, and is still the plain line
  let style = if style == none { "normal" } else { style }
  check-fine("var", "style", style)
  check-fine("var", "role", role)
  // what a line printing this variable again takes from this one (REQ-002: «reprendrait tous les arguments donnés initialement»), its level and its id aside
  let shown = written + (if style != auto { (style: style) } else { (:) })

  // **No value, no domain: the variable is printed again** (REQ-002), with what it was declared with; `unit:` converts it for this line alone, the registry keeping the unit it was declared in (Q-011).
  let has-value = tail.filter(x => type(x) != str).len() > 0
  if domain == none and not has-value {
    if tail.len() > 0 { panic("var: " + repr(key) + " has a symbol but no value -- to print it in another unit, write unit: \"" + str(tail.first()) + "\"") }
    var-registry.update(d => count-line-id(take-next(d), id))
    context {
      let d = var-registry.get()
      refuse-twice("var", id, d)
      let r = var-lookup(d, key)
      if r == none {
        let known = var-names(d)
        panic("var: no variable named " + repr(key) + " -- " + (if known.len() == 0 { "none is declared yet" } else { "declared here: " + known.join(", ") }) + ". A value is written #var(\"" + key + "\", value)")
      }
      let held = r
      if unit != none {
        let c = converted("var", r.at("symbol", default: key-symbol(key)), r.value, r.at("unit", default: ""), written-unit(unit))
        held = held + (value: c.value, unit: c.unit, warning: c.warning)
      }
      if label != none { held.insert("label", label) }
      if descr != none { held.insert("description", descr) }
      if norm != none { held.insert("norm", norm) }
      if norm != none or norm-ref != "" { held.insert("norm_ref", norm-ref) }
      let inherited = r.at("shown", default: (:))
      let fine = inherited + written
      let st = if "style" in fine { fine.style } else { auto }
      wc-meta((kind: "var", domain: var-current(d), key: key, value: held.value, unit: held.unit, symbol: held.symbol, from: none, stale: none, level: level, id: id, role: r.at("role", default: "data"), again: true))
      var-line-print("var", held, fine.pairs().filter(((k, _)) => k != "style").to-dict(), level, d, resolve-style(st, d), none)
    }
  } else {

    // `domain:` says where the value is read and hands it over as if it had been written positionally (v0.85): `#var("R_d", domain: ("connector", "SD-10"))` and `#var("R_d", var-of("connector", "SD-10", "R_d"))` store the same record, which is what makes the two spellings one command rather than two.
    //
    // ⚠️ The two shapes are read in different places, and that is why a string runs a path of its own below. A **pair** is the export: a plain json read, so it can be made here and turned into a positional like any other value. A **string** is a domain of the report, which lives in the registry -- a state, which nothing outside a context may read -- so its record is built **inside the update**, which is handed the dictionary itself, exactly as `#eq` computes its answer there; the line then prints what it reads back.
    // ⚠️ A value written **beside** `domain:` is a literal checked by it (spec 2026-10-15-calculs-deplies-balises-figures-natives, REQ-001): the value written is the one printed and computed with, and the one `domain:` reads is compared with it -- the same, nothing more; another, the value printed in red with the one the export now holds. `own: true` says the value is the engineer's own over the one `domain:` names: printed in orange, never stale.
    // ⚠️ Only a written **value** makes the line a controlled literal: a symbol alone -- `name-visible:`, or a string in second place -- names what `domain:` reads (spec 2026-10-23-neige-correctifs-issues-96-99, REQ-001). Counting the symbol made `#var("dachform", domain: ("snow-load", "SL"), name-visible: "\"Forme de la toiture\"")` a literal without its value, and every new snow case of a French project stopped the compile.
    let controlled = domain != none and has-value
    let written-symbol = if tail.len() > 0 and type(tail.first()) == str { tail.first() } else { none }
    let pair = domain != none and value-type(domain) == array
    if domain != none and not pair and value-type(domain) != str {
      panic("var: domain: is a domain of the report (\"Gelenkige Verbindung\") or a calculation and its instance ((\"snow-load\", \"SL\")) -- got " + repr(domain))
    }
    if pair and domain.len() != 2 {
      panic("var: domain: names a calculation and its instance, two of them ((\"snow-load\", \"SL\")) -- got " + repr(domain))
    }
    let exported = if pair { find-calculation("var", domain.at(0), domain.at(1)).vars } else { (:) }
    // ⚠️ A pair the export does not carry falls back to the **domain named after its instance** (v0.85), which is where `show-polar-moment` publishes the forces it computed (section 3.3quinquies) -- and which `find` already lists under that very pair. The export wins a name both carry, being the traced one.
    let named-domain = (domain != none and not pair) or (pair and not (key in exported))
    // `from-domain`: the value is read from a domain of the report; `checked-domain`: the value is written, and a domain holds what it is checked against
    let from-domain = named-domain and not controlled
    let checked-domain = named-domain and controlled
    let source-domain = if pair { domain.at(1) } else { domain }
    // the value the export carries, after the symbol written where one is: var-record prints that symbol over the export's
    let pos = if domain == none or from-domain or controlled { tail } else { (if written-symbol == none { () } else { (written-symbol,) }) + (exported.at(key),) }
    let record = if from-domain { none } else {
      // The first of them is the printed symbol when it is a string: a *value* is a number or a var object, never a string, so the two can never be confused. `none` here means "not stated", and var-record then takes the symbol the value brought with it, or the key.
      let has-symbol = type(pos.at(0)) == str
      let symbol = if has-symbol { pos.at(0) } else { none }
      let after = if has-symbol { pos.slice(1) } else { pos }
      assert(after.len() >= 1, message: "var: `" + key + "` has a symbol but no value")
      // a var object carries its own symbol, and then the key is never printed
      if not has-symbol and not (type(after.at(0)) == dictionary and "symbol" in after.at(0)) { check-printable-key("var", key) }
      // A literal checked against the export keeps everything the export's var carries -- its symbol, label, citation and `source` -- but the value and the unit, which are the ones written.
      let ref = if controlled and pair and key in exported { exported.at(key) } else { none }
      if type(ref) == dictionary and (type(after.at(0)) == int or type(after.at(0)) == float) {
        let given-unit = after.at(1, default: none)
        var-record(key, symbol, ref + (value: after.at(0), unit: if given-unit == none { "" } else { written-unit(given-unit) }), none, label, descr, norm, norm-ref)
      } else {
        var-record(key, symbol, after.at(0), after.at(1, default: none), label, descr, norm, norm-ref)
      }
    }

    // The document this line rests on, for the bibliography (lib/bibliography.typ, v0.99): the citation the record ends up carrying -- the `norm:` written here, else the one a var object of the export brought with it. ⚠️ Emitted **here**, before the context below, exactly as the registry's own update is: a state written inside a context is not read back by the folded chain an update function reads (section 3.3quinquies). ⚠️ And it follows the *record* and not the level: whether the clause is printed is a matter of level, whether the document is a source is not, so a value declared at level 0 and used by the formula under it still names its norm.
    bib-note(if record == none { norm } else { record.at("norm", default: norm) })

    // A literal checked against the export: the comparison needs no state, so it is made here; the record keeps the export's provenance (`source`), the value being the one written.
    let exported-ref = if controlled and not named-domain { exported.at(key) } else { none }
    let stale-now = if exported-ref == none { none } else { literal-stale(record, if type(exported-ref) == dictionary { exported-ref } else { (value: exported-ref, unit: "") }) }

    // What a line stores beside its value (REQ-002, REQ-010): its role, resolved against the `#calc-defaults` in force, and the fine arguments it was written with, which a line printing it again takes.
    let with-role(d, r) = r + (role: resolve-role("var", role, d), shown: shown)
    // ⚠️ A name the domain does not hold stores nothing here rather than panicking: the function of a state update runs only where something reads that state, so a refusal written here would be silent in a document that never looks the registry up again (the finding `var-unit` records). The context below always runs, and is where it is refused.
    if from-domain {
      var-registry.update(d => {
        let src = d.domains.at(source-domain, default: (:))
        let d = if key in src { var-store(d, key, with-role(d, var-record(key, written-symbol, src.at(key), none, label, descr, norm, norm-ref))) } else { d }
        count-line-id(take-next(d), id)
      })
    } else if checked-domain {
      // the value a domain holds is read **before** the literal is stored, which may land in that very domain, and kept beside it for the context below
      var-registry.update(d => {
        let src = d.domains.at(source-domain, default: (:))
        let against = src.at(key, default: none)
        count-line-id(take-next(var-store(d, key, with-role(d, record) + (checked_against: against))), id)
      })
    } else {
      var-registry.update(d => count-line-id(take-next(var-store(d, key, with-role(d, record))), id))
    }
    context {
      let d = var-registry.get()
      refuse-twice("var", id, d)
      let held = if not from-domain and not checked-domain { record } else {
        let declared = d.domains.keys().filter(k => k != "")
        // A pair got here because the export has no such name, so its own list belongs in the refusal: the reader asked one question and both places have to answer it.
        let carried = if not pair { "" } else {
          source-label(domain.at(0), domain.at(1)) + " carries " + exported.keys().join(", ") + ", and "
        }
        let published = if not pair { "" } else {
          " A polar moment publishes its forces where show-polar-moment has already run above this line (F_max, F_1 …, beta_1 …)."
        }
        if not (source-domain in d.domains) {
          panic("var: " + carried + "no domain " + repr(source-domain) + " is declared above this line -- "
            + (if declared.len() == 0 { "none is" } else { "declared: " + declared.map(k => repr(k)).join(", ") })
            + "." + (if pair { published } else { " A calculation of the export is named as a pair, (\"snow-load\", \"SL\")" }))
        }
        if not (key in d.domains.at(source-domain)) {
          panic("var: " + carried + "the domain " + repr(source-domain) + " declares no " + repr(key)
            + " -- it declares: " + d.domains.at(source-domain).keys().join(", ") + "." + published)
        }
        var-lookup(d, key)
      }
      let stale = if checked-domain {
        let against = held.at("checked_against", default: none)
        if against == none { none } else { literal-stale(held, against) }
      } else { stale-now }
      wc-meta((kind: "var", domain: var-current(d), key: key, value: held.value, unit: held.unit, symbol: held.symbol, from: domain, stale: stale, level: level, id: id, role: (var-lookup(d, key) + (:)).at("role", default: "data")))
      var-line-print("var", held, written, level, d, resolve-style(style, d), stale)
    }

  }
}

#let eq-argument-names = ("name-calc", "name-visible", "equation", "unit", "as-unit", "value", "display-formula", "display-equation", "style", "role", "label", "label-position", "descr", "descr-position", "norm", "norm-section", "norm-position", "id", "level")

// A formula with its numbers put in and their units left out -- what `display-formula: "value"` prints (REQ-001): `formula-lines`'s numbers, each a bare number.
#let formula-bare(src, operands) = {
  let coded = src
  for (i, o) in operands.enumerate() { coded = replace-word(coded, o.key, placeholder(i)) }
  for (short, long) in formula-display-names { coded = replace-word(coded, short, long) }
  for (i, o) in operands.enumerate() { coded = coded.replace(placeholder(i), substituted(o.value, "")) }
  coded
}

// References of the block below (moved out of it, issue #115): spec 2026-10-21-commandes-typst-refonte, Q-001; REQ-003; Q-004.
/// A calculation written by hand: the formula in letters, the same formula with the numbers and their units put in, and the answer -- **computed from the formula**, with its units checked. The result is stored under its name, so the next line names it without redeclaring anything.
///
/// ```typ
/// #var("R_k", 7, "kN")
/// #var("k_dens", 0.806, level: 0)
/// #var("eta_w", 0.8, level: 0)
/// #var("gamma_M", 1.7, level: 0)
/// #eq("R_d", `k_dens dot eta_w / gamma_M dot R_k`, style: "bold", norm: "Sherpa", norm-section: "ETA-12/0197")
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
/// **What is printed** is two fine arguments: `display-equation` the name and the answer -- `"variable"` the symbol, `"value"` the bare number, `"value-unit"` the number and its unit, `"variable-value-unit"` both --, `display-formula` the formula between them -- `"variable"` in letters, `"value"` with the numbers put in, `"value-unit"` with the numbers and their units, `"variable-value-unit"` the letters then the numbers. The line is `name = formula = answer`, every part left out skipped:
///
/// ```typ
/// #var("N_d", 50, "kN", level: 0)
/// #var("A", 56000, "mm²", level: 0)
/// #eq("sigma", `N_d / A`, display-formula: "variable-value-unit", display-equation: "variable-value-unit")
/// #eq("sigma2", "sigma", `N_d / A`, display-formula: "variable", display-equation: "variable")
/// ```
///
/// At `level: 0` -- both `"none"` -- the answer is computed, checked and stored, and nothing is printed: an intermediate value the next line names.
///
/// ```typ
/// #var("b", 100, "mm", level: 0)
/// #var("h", 200, "mm", level: 0)
/// #eq("A", `b dot h`, level: 0)
/// #var("N", 12, "kN", level: 0)
/// #eq("sigma", `N / A`)
/// ```
///
/// `unit:` converts the answer into another unit of its dimension; `as-unit:` gives the answer **another unit without converting it** -- the number kept, the unit replaced, as the engineer asked for a factor whose unit the formula cannot carry: Woodcore says so beside the domain in its window.
///
/// ```typ
/// #var("M_d", 4.2, "kNm", level: 0)
/// #eq("M_N", `M_d`, unit: "Nmm")
/// #eq("q_d", `M_d / (100 "mm")`, as-unit: "kN/m")
/// ```
///
/// A `*` is a product, printed as `·`, and a word math does not know may stand in the symbol without its quotes -- `G_(1,Ed)` for `G_(1,"Ed")`:
///
/// ```typ
/// #var("g_k", 1.2, "kN/m²", level: 0)
/// #eq("G_1_Ed", "G_(1,Ed)", `1.35 * g_k`, unit: "kN/m²")
/// ```
///
/// It is printed **inline**, as `#var` is: one word of its sentence, so it may follow a `#var` on the same line -- a blank line before and after sets it as a paragraph of its own. Its label, description and citation go where their positions say, as `#var`'s:
///
/// ```typ
/// #var("R_k", 7, "kN", level: 0)
/// Mit #var("gamma_M", 1.7, "") wird #eq("R_d", `R_k / gamma_M`, label: "Bemessungswert", norm: "SIA 265", norm-section: "2.2.5", level: 3).
///
/// #eq("R_d2", "R_(d,2)", `R_k / 1.7`, label: "Bemessungswert", label-position: "before", norm: "SIA 265", norm-section: "2.2.5", norm-position: "line-right", level: 3)
/// ```
///
/// The formula names the **keys of the registry** and literals, a literal taking its unit in quotes -- `(100 "mm")` --, and nothing else: a name the registry does not hold stops the compile saying which names it does hold. A key that is the beginning of another (`F` and `F_Ed`) is safe: the longest is substituted first, and only whole words are.
///
/// **The units are algebra, not decoration.** Each operand's unit is parsed into dimensions, the formula's operations propagate them, and the answer comes out in the unit `unit:` declares -- or, left to itself, in the one unit the table names for that dimension, which `#unit` sets. A sum whose sides have different dimensions, a `sqrt` of an odd power, an unreadable unit, an answer given with `value:` that the formula contradicts: each stops the compile naming both sides. A declared unit the formula cannot *reach* does not: the answer is printed in the unit the operands were written in, with a red line naming both.
///
/// **What cannot be computed is still printed.** An integral, a derivative: the formula displays exactly as written, and `value:` gives the answer. Nothing is verified then.
/// - ..rest (any): the positional arguments -- the name, the optional printed symbol, then the formula, in that order. Variadic only because Typst has no optional positionals; every *named* argument is declared, so an editor shows them all.
/// - key (str): the name the result is stored under -- the first positional, or `name-calc:` -- and printed as where no symbol is given, as `#var` prints a key.
/// - symbol (str): optional second positional argument, or `name-visible:`, the math source printed in the key's place.
/// - formula (content, str): the formula -- the last positional, or `equation:` --, in Typst math source naming the registry's keys. A raw block -- `` `M / a` `` -- saves escaping every quote. `*` multiplies, as `dot` does. A literal takes its unit in quotes, `(3 "m")`, and what is quoted is never read as a name.
/// - name-calc (str, none), name-visible (str, none), equation (content, str, none): the name, the symbol and the formula, written by name.
/// - unit (str, auto): the unit of the answer, **converted** into. auto takes the one the table names for that dimension (`#unit` sets it); `""` asserts it is dimensionless. A unit of another dimension prints the answer in the operands' own units, with a red line.
/// - as-unit (str, none): the unit the answer is **given without conversion** -- its number kept. Not with `unit:`.
/// - value (int, float, auto): the answer, for a formula that cannot be evaluated.
/// - display-formula (str, auto): the formula between the name and the answer -- `"none"`, `"variable"`, `"value"`, `"value-unit"`, `"variable-value-unit"`. auto leaves it to the level.
/// - display-equation (str, auto): the name and the answer -- `"none"`, `"variable"`, `"value"`, `"value-unit"`, `"variable-value-unit"`. auto leaves it to the level.
/// - style (str, auto): `"normal"`, `"bold"`, `"underline"` or `"double"`, applied to the answer.
/// - role (str, auto): `"data"`, `"compute"` (the default of `#eq`) or `"result"`, which `#var-table` lists by.
/// - label (str, none), label-position (str, auto): what the answer is, and where: `"none"`, `"before"`, `"after"`, `"footnote"` -- the footnote from level 2 where auto.
/// - descr (str, none), descr-position (str, auto): why the answer is what it is, and where: `"none"`, `"after"`, `"footnote"` -- the footnote from level 3 where auto.
/// - norm (str, none), norm-section (str, none), norm-position (str, auto): the citation, and where: `"none"`, `"in-line"`, `"line-right"`, `"footnote"` -- the footnote from level 3 where auto.
/// - id (str, none): the name the line is found by, once per domain for `#var`, `#eq` and `#verify` together.
/// - level (int, auto): a preset of the fine arguments -- 0 nothing, 1 the symbol and the answer, 2 also the formula in letters and the label, 3 also the formula in numbers, the description and the citation (`lib/display-presets.json`) --, which an argument written overrides.
/// - norm-ref (str): written before `norm-section:`, which it is.
/// -> content
#let eq(..rest, name-calc: none, name-visible: none, equation: none, unit: auto, as-unit: none, value: auto, display-formula: auto, display-equation: auto, style: auto, role: auto, label: none, label-position: auto, descr: none, descr-position: auto, norm: none, norm-section: none, norm-ref: "", norm-position: auto, id: none, level: auto) = {
  // ⚠️ Declared one by one rather than swept into `..args`: a tooltip on a sink signature reads `eq(args: arguments) -> any` and says nothing about `unit:`, which is how this was found (v0.63.1). Only the positional tail stays variadic.
  let unknown = rest.named().keys()
  if unknown.len() > 0 {
    panic("eq: unknown argument " + repr(unknown.first())
      + " -- " + eq-argument-names.map(n => repr(n)).join(", "))
  }
  let pos = rest.pos()
  if name-calc == none and pos.len() == 0 { panic("eq: write #eq(\"key\", `formula`) -- the name first, or name-calc:") }
  let key = if name-calc != none { name-calc } else { pos.first() }
  let tail = if name-calc != none { pos } else { pos.slice(1) }
  if name-visible != none { tail = (name-visible,) + tail }
  if equation != none { tail.push(equation) }
  check-key("eq", key)
  check-level("eq", level)
  check-line-id("eq", id)
  if norm-section != none and norm-ref != "" { panic("eq: norm-section: and norm-ref: are one argument -- write norm-section: alone") }
  let norm-ref = if norm-section != none { norm-section } else { norm-ref }
  let written = written-fine("eq", (display-formula: display-formula, display-equation: display-equation, label-position: label-position, descr-position: descr-position, norm-position: norm-position))
  // `style: none` was the default until the fine arguments, and is still the plain answer
  let style = if style == none { "normal" } else { style }
  check-fine("eq", "style", style)
  check-fine("eq", "role", role)
  if as-unit != none and unit != auto { panic("eq: unit: converts the answer and as-unit: gives it another unit without converting it -- write one of the two") }
  if as-unit != none and (type(as-unit) != str or parse-unit(written-unit(as-unit)) == none) { panic("eq: as-unit: is a unit the report can read, `kN/m`, `Nmm` -- got " + repr(as-unit)) }

  // ⚠️ The unit is named and cannot be a third positional, where `var`'s is the last one: a formula may be written as a string (`#eq("N_Ed", "N - N_gunstig")`), so with two positionals a unit and a formula are the same shape and nothing could tell `#eq("eta", "F/R", "%")` from a symbol and a formula. So the message names `unit:` rather than leaving it to be found.
  assert(tail.len() >= 1 and tail.len() <= 2,
    message: "eq: write #eq(\"key\", `formula`), or #eq(\"key\", \"symbol\", `formula`) -- the unit is a named argument, #eq(..., unit: \"%\"), a formula being written as a string too")
  let has-symbol = tail.len() == 2
  if not has-symbol { check-printable-key("eq", key) }
  let symbol = if has-symbol { quoted-words(tail.at(0)) } else { key-symbol(key) }
  let formula = tail.at(if has-symbol { 1 } else { 0 })
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
    // `as-unit:` keeps the number and gives it the unit written, with no conversion (REQ-003): what the line computed in is kept beside it, for the window to say (Q-004)
    let answer = if as-unit == none { answer } else { (value: answer.value, unit: written-unit(as-unit), as_unit_from: answer.unit) }
    // a unit `#unit(scope: "next")` set for this dimension is spent by the first answer of it (REQ-005)
    let d = if got.result == none { d } else { spend-next-unit(d, got.result.dims) }
    count-line-id(take-next(var-store(d, key, (
      value: answer.value, unit: answer.unit, symbol: symbol,
      warning: answer.at("warning", default: none), as_unit_from: answer.at("as_unit_from", default: none),
      label: label, description: descr, norm: norm, norm_ref: norm-ref, source: none,
      role: resolve-role("eq", role, d), shown: written + (if style != auto { (style: style) } else { (:) }),
    ))), id)
  })

  context {
    let d = var-registry.get()
    refuse-twice("eq", id, d)
    let r = var-lookup(d, key)
    wc-meta((kind: "eq", domain: var-current(d), key: key, value: r.value, unit: r.unit, symbol: r.symbol, formula: src, level: level, id: id, role: r.at("role", default: "compute"), as_unit_from: r.at("as_unit_from", default: none)))
    // The result itself is in the registry by now; it is not one of its own operands.
    let operands = formula-operands(d, src).filter(o => o.key != key)
    let (letters, numbers) = formula-lines(src, operands)
    let style = resolve-style(style, d)

    let tail = display-source(r.value) + (if r.unit == "" { "" } else { " \"" + r.unit + "\"" })
    // `style` is spliced into the math **source** and evaluated with the rest of the chain, which is what lets it name any math function -- `bold`, `underline` -- without this file knowing one of them. A double rule is not a math function at all but two nested boxes (verify, below), so it is handed to the same eval through its `scope`: one equation still, so the spacing around every `=` stays math's own.
    let styled(x) = if style != none { (if style == "double" { "dbl" } else { style }) + "(" + x + ")" } else { x }

    // The parts the line is made of, by its fine arguments (Q-001): the name, the formula, the answer.
    let parts = ()
    let rd = resolve-display("eq", written, level, d)
    let s = rd.settings
    let blocked = rd.family == "block"
    let df = s.at("display-formula")
    let de = s.at("display-equation")
    if de in ("variable", "variable-value-unit") { parts.push(symbol) }
    if df == "variable" { parts.push(letters) }
    else if df == "value" { parts.push(formula-bare(src, operands)) }
    else if df == "value-unit" { parts.push(numbers) }
    else if df == "variable-value-unit" {
      parts.push(letters)
      // left out where nothing was substituted -- an integral would otherwise be printed twice over
      if numbers != letters { parts.push(numbers) }
    }
    if de == "value" { parts.push(styled(display-source(r.value))) }
    else if de in ("value-unit", "variable-value-unit") { parts.push(styled(tail)) }

    // The double rule is `double-rule` above, one place for the three commands that draw one (v0.100); it is handed to the eval through its `scope` because it is not a math function at all but two nested boxes.
    let dbl = double-rule
    // a line with nothing to show -- level 0, both displays "none" -- is computed and checked all the same, and builds nothing
    let body = if parts.len() == 0 { none } else { math-eval(parts.join(" = "), scope: (dbl: dbl)) }
    // The same statement stacked at its `=` signs, for a line too wide for its row (annotated-rows, formula-chain): `symbol = <letters>`, then `= <numbers>` and `= <answer>` under it -- together where the width holds them, each on its own where it does not -- each `=` under the first. `after` is what the line ends on, its label or its footnote, set after the answer on the last line. A line of one `=` has nothing to stack and stays one line.
    let chained(line, before, after) = {
      if parts.len() < 3 { return line }
      formula-chain(line, [#before#math-eval(parts.at(0) + " = " + parts.at(1), scope: (dbl: dbl))], parts.slice(2),
        x => chain-line(symbol, "=", x, scope: (dbl: dbl)), last: after)
    }
    let warning = unit-warning(r.at("warning", default: none))
    // ⚠️ Everything above is computed at **every** level, level 0 included, and only the emission is held back: the registry is read, the operands are resolved and the units are checked, so a formula naming a variable that does not exist is refused whatever the level -- a line hidden today is a line printed in the next report, and it must not be the report that finds the mistake.
    let said = (label: label, description: descr, norm: norm, norm_ref: norm-ref, symbol: symbol)
    let emitted = if parts.len() > 0 {
      let x = placed-extras(said, s)
      if blocked or x.right != none {
        // The label follows the answer as `#var`'s follows its value, and for the same reason: what the result *is* is read with it, not at the foot of the page.
        let after(y) = [#y#x.after#x.footnote]
        annotated-rows(((chained([#x.before#after(body)], x.before, after), x.right),))
        if warning != none { warning }
      } else {
        // Inline, the default since v0.117 (issue #19: «#eq s'imprime en ligne par défaut, comme #var»): one word of its sentence.
        inline-item([#x.before#body#x.after], x.footnote, warning)
      }
    }
    if rd.masked { masked-line(emitted) } else { emitted }
  }
}

// References of the block below (moved out of it, issue #115): spec 2026-10-21-commandes-typst-refonte, REQ-005.
/// Sets the unit **computed** results of one dimension are printed in: for the next one (the default), for the rest of the domain, or for the rest of the document.
///
/// ```typ
/// #var("F", 12, "kN")
/// #var("A", 2400, "mm²")
/// #unit("N/mm²")
/// #eq("sigma", `F / A`)
/// ```
///
/// ```typ
/// #var("M", 4.2, "kNm")
/// #var("l", 3, "m")
/// #unit("N", scope: "document")
/// #eq("V", `M / l`)
/// #eq("V_2", `2 * M / l`)
/// ```
///
/// The dimension is read from the unit itself, so one call settles one kind of result and leaves the others alone: `scope: "next"` is spent by the first answer **of that dimension**, the lines of another dimension between them taking nothing of it. The defaults are `default-units`: mm, mm², mm³, mm⁴, s, kN, kNm, N/mm², kN/m, kg, °.
///
/// It reaches **only what the engine computes** -- the answer of an `#eq`, a side of a `#verify` that is a whole expression. A value that already carries a unit keeps it: one read from the export, and one written out by hand (`#var("R_k", 7, "kN")`). The unit of a value is the data's, and is never retyped (docs/architecture/principles.md §2, rule 1); `#var("R_k", unit: "N")` shows one in another unit for its line.
///
/// ⚠️ Until the fine arguments `#unit` reached the rest of the document; it now reaches the next answer unless `scope:` says otherwise -- `scope: "document"` is the former reach.
///
/// ⚠️ A stress and a surface load are **one** dimension, N/m². The default serves the stress; a line that wants kN/m² says `unit: "kN/m²"`, or this command says it for a domain or the document.
/// - written (str): the unit, as the report writes one. Must have a dimension -- `#unit("%")` is refused, a dimensionless result being printed as a bare number.
/// - scope (str): `"next"` (the default) -- the next answer of that dimension --, `"domain"` -- the rest of the `#domain` it stands in, the rest of the document outside every domain --, or `"document"` -- the rest of the document.
/// -> content
#let unit(written, scope: "next") = {
  assert(type(written) == str and written.trim() != "",
    message: "unit: write the unit as a string, as in #unit(\"Nmm\") -- got " + repr(written))
  check-scope("unit", scope)
  let written = written-unit(written)
  let p = parse-unit(written)
  assert(p != none, message: "unit: cannot read " + repr(written)
    + " -- write it as the report writes one, `mm`, `kN`, `kNm`, `N/mm²`")
  assert(clean-dims(p.dims).len() > 0, message: "unit: " + repr(written)
    + " has no dimension, so there is no kind of result it could be the unit of "
    + "-- a result without dimensions is printed as a bare number")
  var-registry.update(d => set-unit(d, dims-text(clean-dims(p.dims)), written.trim(), scope))
}

// What `#calc-defaults` may set: every fine argument the lines take, their level, and a unit.
#let calc-default-names = ("display", "display-formula", "display-equation", "label-position", "descr-position", "norm-position", "style", "role", "level", "unit", "presets")

// References of the block below (moved out of it, issue #115): spec 2026-10-21-commandes-typst-refonte, REQ-006; REQ-007.
/// Sets the fine arguments of the lines that follow -- the next one (the default), the rest of the domain, or the rest of the document -- where they write none of their own: what to show of them, where their labels, descriptions and citations go, their style, their role, their level, and the unit of a dimension. A line's own argument still wins, then its own `level:`, then these.
///
/// ```typ
/// #calc-defaults(norm-position: "line-right", scope: "document")
/// #var("gamma_M", 1.7, norm: "SIA 265", norm-section: "2.2.5", level: 3)
/// #var("k_mod", 0.8, norm: "SIA 265", norm-section: "Tabelle 7", level: 3)
/// ```
///
/// ```typ
/// #domain("P1", label: "Poutre P1")[
///   #calc-defaults(level: 3, label-position: "before", scope: "domain")
///   #var("b", 140, "mm", label: "Largeur")
///   #var("h", 400, "mm", label: "Hauteur", level: 1)
/// ]
/// ```
///
/// - scope (str): `"next"` (the default) -- the next line of `#var`, `#eq` or `#verify` --, `"domain"` -- the rest of the `#domain` it stands in, the rest of the document outside every domain --, or `"document"`.
/// - ..defaults (any): named arguments only, among `display`, `display-formula`, `display-equation`, `label-position`, `descr-position`, `norm-position`, `style`, `role`, `level`, `unit` -- each with the values the lines take -- and `presets`: `"inline"`, the default family of presets, or `"block"`, the same visibility at each level with the label after the line and the citation in the right-hand column, the line set apart (what a generated file writes once at its head).
/// -> content
#let calc-defaults(scope: "next", ..defaults) = {
  check-scope("calc-defaults", scope)
  if defaults.pos().len() > 0 { panic("calc-defaults: every default is named -- calc-defaults(norm-position: \"line-right\", scope: \"domain\")") }
  let given = defaults.named()
  let fine = (:)
  let unit-set = none
  for (name, value) in given.pairs() {
    if not (name in calc-default-names) { panic("calc-defaults: " + repr(name) + " is not a default -- " + calc-default-names.map(n => repr(n)).join(", ")) }
    if name == "level" {
      check-level("calc-defaults", value)
      if value != auto { fine.insert("level", value) }
    } else if name == "presets" {
      if not (value in display-families.keys()) { panic("calc-defaults: presets: " + repr(value) + " is not a family of presets -- " + display-families.keys().map(k => repr(k)).join(", ")) }
      fine.insert("presets", value)
    } else if name == "unit" {
      let written = written-unit(value)
      let p = if type(written) == str { parse-unit(written) } else { none }
      if p == none or clean-dims(p.dims).len() == 0 { panic("calc-defaults: unit: " + repr(value) + " is not a unit with a dimension the report can read") }
      unit-set = (dims: dims-text(clean-dims(p.dims)), written: written.trim())
    } else {
      check-fine("calc-defaults", name, value)
      if value != auto { fine.insert(name, value) }
    }
  }
  var-registry.update(d => {
    let d = if unit-set == none { d } else { set-unit(d, unit-set.dims, unit-set.written, scope) }
    let frames = d.at("frames", default: ())
    if scope == "next" {
      d.insert("next", d.at("next", default: (:)) + fine)
    } else if scope == "domain" and frames.len() > 0 {
      let f = frames.last()
      f.defaults = f.defaults + fine
      frames.at(frames.len() - 1) = f
      d.insert("frames", frames)
    } else {
      d.insert("defaults", d.at("defaults", default: (:)) + fine)
    }
    d
  })
}

// The heading a domain's label is printed as: one level below the heading it stands under (1 where there is none), as var-domain's title always was. A footnote is attached **by reference** -- the footnote itself placed invisibly beside the heading, its marker in it --, the outline repeating everything a heading holds: a footnote in it is printed twice, once for the outline (found by compiling it, Typst 0.15).
#let domain-heading(title, notes, cite-right) = context {
  // the headings of the document, a domain's own left out: a domain set after another is not one level below it, and the level of one heading never hangs on another's (Typst converges -- the example's 38 domains in a row did not)
  let above = query(selector(heading).before(here())).filter(h => h.at("label", default: none) != <wc-domain-heading>)
  let at = if above.len() > 0 { above.last().level + 1 } else { 1 }
  let mark = std.label("wc-domain-note-" + str(here().page()) + "-" + repr(here().position().y))
  let body = if notes == none { title } else { [#title#footnote(mark)] }
  let head = [#heading(level: at, body) <wc-domain-heading>]
  if cite-right != none {
    grid(columns: (1fr, note-column), column-gutter: note-gutter, head, align(right + horizon, cite-text(cite-right)))
  } else { head }
  if notes != none { place(hide[#footnote(notes)#mark]) }
}

// References of the block below (moved out of it, issue #115): spec 2026-10-21-commandes-typst-refonte, REQ-008; REQ-007.
/// A calculation domain: keeps one set of variables apart from another, **without losing it** -- what is declared inside belongs to `id`, and stays readable further down the document through `#var(key, domain: id)` --, prints its label as a heading, and sets a level for every line it holds. `var-domain` was it until then.
///
/// ```typ
/// #var("l", 2.4, "m")
/// #domain("ende", label: "Ende")[
///   #var("F", 0.55, "kN")
///   #eq("M", `F dot l`)
/// ]
/// Das massgebende Moment beträgt #var("M", domain: "ende").
/// ```
///
/// ```typ
/// #domain("traction", label: "Vérification à la traction", descr: "Barre tendue, section nette", norm: "SIA 265", norm-section: "4.2.1", norm-position: "line-right", level: 3)[
///   #var("N_t_d", 50, "kN", label: "Effort de traction")
///   #var("A", 56000, "mm²", level: 1)
///   #eq("sigma_t_d", `N_t_d / A`)
/// ]
/// ```
///
/// Without it the second `F` would quietly replace the first, the registry being one dictionary for the whole document. A name is looked up in the innermost domain first and then in the default one, so what a section declares outside every domain -- R_d, a partial factor -- is readable inside all of them.
///
/// **Its level** is the level of every line inside that states none of its own: a line's own `level:`, or a fine argument it writes, wins. `#calc-defaults(scope: "domain")` sets the defaults of its lines, and a `#unit(scope: "domain")` the unit of a dimension -- both gone when the domain closes.
///
/// 👉 A *domain* here is a set of names in the report. It has nothing to do with a calculation domain of the export (docs/domain/calculation-domains.md §3.3), which is a kind of calculation -- `snow-load`, `dead-load` -- whose instances are the cases entered in Woodcore's tabs.
/// - id (str): the domain's name -- what `#var(key, domain: id)` reads, and what Woodcore finds the domain by.
/// - label (str, none): its title.
/// - label-position (str, auto): `"none"`, `"before"` (a heading before the domain, one level below the heading above it), `"after"` (the same heading after it), `"footnote"`. auto leaves it to the level -- before, from level 1.
/// - descr (str, none): what the domain is about.
/// - descr-position (str, auto): `"none"`, `"after"` (a paragraph after its label), `"footnote"` (on its label). auto leaves it to the level -- after, from level 2.
/// - norm (str, none), norm-section (str, none): the norm the domain follows.
/// - norm-position (str, auto): `"none"`, `"in-line"` (after its label, in grey), `"line-right"` (level with its label, in the right-hand column), `"footnote"` (on its label). auto leaves it to the level -- the right-hand column at level 3.
/// - level (int, auto): the level of every line it holds that states none of its own; auto follows the domain around it, else the report.
/// - body (content): its lines.
/// -> content
#let domain(id, label: none, label-position: auto, descr: none, descr-position: auto, norm: none, norm-section: none, norm-position: auto, level: auto, body) = {
  if type(id) != str or id.trim() == "" { panic("domain: the id is a non-empty string, got " + repr(id)) }
  if label != none and (type(label) != str or label == "") { panic("domain: label: is a non-empty string or none, got " + repr(label)) }
  check-level("domain", level)
  let written = written-fine("domain", (label-position: label-position, descr-position: descr-position, norm-position: norm-position))
  let record = (label: label, description: descr, norm: norm, norm_ref: if norm-section == none { "" } else { norm-section })
  bib-note(norm)
  // What of its own the domain prints, by its fine arguments over its level's preset -- the uniform level over both.
  let settings() = {
    let forced = uniform-level.get()
    if forced != none { return preset("domain", forced) }
    preset("domain", if level == auto { resolve-level(auto) } else { level }) + written
  }
  let notes(s) = {
    let parts = ()
    if s.at("label-position") == "footnote" and label != none { parts.push(render-prose(tl-str(label))) }
    if s.at("descr-position") == "footnote" and descr != none { parts.push(render-prose(tl-str(descr))) }
    if s.at("norm-position") == "footnote" and norm != none { parts.push(norm-text(record)) }
    if parts.len() == 0 { none } else { parts.join([#semicolon-str() ]) }
  }
  let title(s) = {
    let t = render-prose(tl-str(label))
    if s.at("norm-position") == "in-line" and norm != none { [#t #cite-text(norm-text(record), size: auto)] } else { t }
  }
  let right(s) = if s.at("norm-position") == "line-right" and norm != none { norm-text(record) } else { none }
  // where the domain stands against its data, where Woodcore wrote it (REQ-012, ARCH-007): its form, and the lines not applied -- said in red at its head, the file being the engineer's and never rewritten for it
  let state = load-domain-state().at(id, default: none)
  let matches = state == none or state.matches
  wc-meta((kind: "domain", domain: id, title: label, gen: none, matches: matches, level: level))
  if state != none and (not state.matches or state.missing.len() > 0 or state.conflict.len() > 0) {
    let form(g) = if g == none { "?" } else { g.form + " (" + g.kind + ", v" + str(g.version) + ")" }
    context block(above: 0.6em, below: 0.6em, text(fill: test-nok, {
      if state.at("gone", default: false) { t-str("formula.unfold_missing", id: id) }
      else if not state.matches { t-str("formula.unfold_mismatch", have: form(state.written), want: form(state.form)) }
      let lines = state.missing + state.conflict
      if lines.len() > 0 { [ ] + t-str("formula.unfold_lines", lines: lines.join(", ")) }
    }))
  }
  context {
    let s = settings()
    if s.at("label-position") == "before" and label != none {
      domain-heading(title(s), notes(s), right(s))
    } else {
      // no heading to carry them: the footnote at the head of the domain, the citation on a line of its own
      if notes(s) != none { footnote(notes(s)) }
      if s.at("norm-position") == "in-line" and norm != none { block(cite-text(norm-text(record), size: auto)) }
      if right(s) != none { block(width: 100%, align(right, cite-text(right(s)))) }
    }
    if s.at("descr-position") == "after" and descr != none { block(render-prose(tl-str(descr))) }
  }
  var-registry.update(d => {
    d.stack.push(id)
    push-frame(d, id, level)
  })
  body
  var-registry.update(d => {
    d.stack = d.stack.slice(0, -1)
    pop-frame(d)
  })
  context {
    let s = settings()
    if s.at("label-position") == "after" and label != none { domain-heading(title(s), none, none) }
  }
}

// References of the block below (moved out of it, issue #115): spec 2026-10-23-onglet-vent-briques, D-29.
/// Prints what it holds **from a level on**: at the level the place stands at -- the innermost `#domain` that states one, else the report's, the uniform level over both -- or above, and nothing below it. What a domain's file writes a figure in that only its most detailed print shows: the figure of the norm of a wind load, printed at level 3 alone. The figure keeps its own line, its width, its caption and its label, which «Affichage» sets; the preview of «Affichage» prints it pale where the report would hide it.
///
/// ```typ
/// #domain("WL-01", label: "Charge de vent", level: 3)[
///   #from-level(3)[#figure(rect(width: 3cm, height: 1cm), caption: [Printed at level 3]) <wl-figure>]
/// ]
/// ```
///
/// At level 2 it prints nothing:
///
/// ```typ
/// #domain("WL-02", label: "Charge de vent", level: 2)[
///   #from-level(3)[#figure(rect(width: 3cm, height: 1cm), caption: [Not printed at level 2])]
///   #var("q_p", 0.98, "kN/m²")
/// ]
/// ```
///
/// - lowest (int): 1, 2 or 3 -- the lowest level what it holds is printed at.
/// - body (content): what it holds, a figure on its line.
/// -> content
#let from-level(lowest, body) = {
  if not (lowest in (1, 2, 3)) { panic("from-level: the lowest level is 1, 2 or 3, got " + repr(lowest)) }
  context {
    let forced = uniform-level.get()
    let at = if forced != none { forced } else {
      let own = var-registry.get().at("frames", default: ()).rev().find(f => f.level != auto)
      if own != none { own.level } else { resolve-level(auto) }
    }
    if at >= lowest { body } else if show-masked.get() { masked-line(body) }
  }
}

// The columns `#var-table` may show, in the order they stand in when named: what the engineer listed (T3: «colonne descr, norm, norm-section, label, etc.»).
#let var-table-columns = ("label", "descr", "symbol", "value", "unit", "norm", "norm-section")

// References of the block below (moved out of it, issue #115): spec 2026-10-21-commandes-typst-refonte, REQ-010; Q-009.
/// A table of the variables of one role -- the data, the computed values or the results -- of a domain, of several, or of the whole document, **read from the registry and never copied**: the values are those the lines declare, wherever they stand, so a table at the head of a domain lists what is declared below it.
///
/// ```typ
/// #domain("p1", label: "Poutre P1")[
///   #var-table(role: "data", columns: ("label", "symbol", "value"))
///   #var("b", 140, "mm", label: "Largeur", level: 0)
///   #var("h", 400, "mm", label: "Hauteur", level: 0)
///   #eq("A", `b * h`, level: 0)
/// ]
/// ```
///
/// Over every domain and filtered by unit, it is the summary of the loads or of the results -- what `show-load-summary` and `show-result-summary` printed:
///
/// ```typ
/// #var("g_k", 1.2, "kN/m²", label: "Eigengewicht", level: 0)
/// #var("q_k", 3, "kN/m²", label: "Nutzlast", level: 0)
/// #var("s_k", 1.4, "kN/m²", label: "Schnee", level: 0)
/// #var-table(role: "data", domain: "all", unit: "kN/m²")
/// ```
///
/// It is a Typst `#table`, set as the document sets its tables: `#show table` and `#set table` style it like any other.
/// - role (str, auto): `"data"`, `"compute"` or `"result"` -- the role a line was given, or its command's own (`#var` data, `#eq` compute, `#verify` result). auto lists every role.
/// - domain (auto, str, array): the domain whose variables are listed -- auto the one the table stands in, a string one domain by its id, an array several, `"all"` every domain of the document and the variables outside them.
/// - unit (none, str, array): only the variables in that unit, or in one of those units -- `"kN/m²"` the area loads, `"kN/m"` the line loads.
/// - columns (array): the columns, among `"label"`, `"descr"`, `"symbol"`, `"value"`, `"unit"`, `"norm"`, `"norm-section"`. `"value"` writes the unit beside the number unless `"unit"` is a column of its own; `"norm"` cites the norm and its clause unless `"norm-section"` is one.
/// -> content
#let var-table(role: auto, domain: auto, unit: none, columns: ("label", "symbol", "value", "norm")) = {
  if role != auto { check-fine("var-table", "role", role) }
  if type(columns) != array or columns.len() == 0 { panic("var-table: columns: is a list of columns among " + var-table-columns.map(c => repr(c)).join(", ")) }
  for c in columns { if not (c in var-table-columns) { panic("var-table: " + repr(c) + " is not a column -- " + var-table-columns.map(c => repr(c)).join(", ")) } }
  let units = if unit == none { none } else if type(unit) == str { (written-unit(unit),) } else { unit.map(written-unit) }
  context {
    // the domain the table stands in is read where it stands; the variables, from the registry as the whole document leaves it -- so a table placed before its lines lists them
    let here-domain = var-current(var-registry.get())
    let final = var-registry.final()
    let wanted = if domain == auto { (here-domain,) } else if domain == "all" { final.domains.keys() } else if type(domain) == str { (domain,) } else { domain }
    let rows = ()
    for name in wanted {
      for (key, r) in final.domains.at(name, default: (:)).pairs() {
        if role != auto and r.at("role", default: "data") != role { continue }
        if units != none and not (r.at("unit", default: "") in units) { continue }
        rows.push(r + (key: key))
      }
    }
    if rows.len() == 0 { return emph(t-str("var_table.empty")) }
    let split-unit = "unit" in columns
    let split-section = "norm-section" in columns
    let cell(r, c) = {
      if c == "label" { let x = r.at("label", default: none); if x == none { [] } else { render-prose(tl-str(x)) } }
      else if c == "descr" { let x = r.at("description", default: none); if x == none { [] } else { render-prose(tl-str(x)) } }
      else if c == "symbol" { math-eval(r.at("symbol", default: key-symbol(r.key))) }
      else if c == "value" { formula-number(r.value, if split-unit { "" } else { r.at("unit", default: "") }) }
      else if c == "unit" { r.at("unit", default: "") }
      else if c == "norm" {
        if r.at("norm", default: none) == none { [] } else if split-section { [#r.norm] } else { norm-text(r) }
      }
      else if c == "norm-section" { r.at("norm_ref", default: "") }
    }
    table(
      columns: columns.len(),
      table.header(..columns.map(c => strong(t-str("var_table." + c)))),
      ..rows.map(r => columns.map(c => cell(r, c))).flatten(),
    )
  }
}

// --- find: what there is to name in a call (v0.85) ------------------------
// A command for **writing** a report rather than for the finished page: it prints which domains exist, which keys each one carries and which variables one of them holds, so that a call can be written without reading data/ by hand. It is the one command here whose output is not meant to be delivered -- one calls it, reads it, and deletes the call. What makes it necessary rather than convenient is that nothing else answers the question: the catalog window's loads tab reads data/calculations.json and nothing else (section 10quater), so a connector's three dozen vars and a polar moment's geometry, which are files of their own, are listed nowhere at all.

// The four parts a value can be printed as, in the engineer's own words (v0.80): the value alone, its unit alone, the two together -- the default -- and the whole expression, `s_k = 1.729 kN/m²` -- what `find` prints a variable as.
#let val-types = ("val", "unit", "val+unit", "expression")

// Every domain a call may address: the calculation domains of data/calculations.json, then the two that are files of their own. `ids("domain")` lists the first alone and says so in its own header, that being what calculations.json holds; a command written to answer "what is there?" has to be complete, so it names all of them here rather than widening a promise made elsewhere.
#let find-domains() = ids("domain") + (connector-domain, connection-domain)

#let find-objects = ("domain", "variable")

// The four parts `val` prints, and the name to type into a call -- which is what one comes here for. Built from `val-types` rather than restated, so that the two cannot come to offer different words.
#let find-types = ("name",) + val-types

// References of the block below (moved out of it, issue #115): v0.85.
/// **What there is to name in a call**: every domain with its keys, or the variables one of them holds. A command for *writing* a report rather than for the finished page -- one calls it, reads it, and deletes the call -- and the only thing that answers "which variables does this connector carry?": the catalog window's loads tab reads `data/calculations.json` alone, so a connector's own vars and a polar moment's are listed nowhere else.
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
      let keys = ids(d)
      [#raw(d)#colon-str() #(if keys.len() == 0 { emph(t-str("find.none")) } else { keys.map(k => raw(k)).join(", ") })]
    }).join(linebreak())
  } else {
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
    let prose-value(v, unit) = if value-type(v) == str { tl-str(v) } else if type == "val" { display-number(v) } else { "$" + formula-quantity(v, unit) + "$" }
    let value-cell(k, v) = {
      let unit = v.at("unit", default: "")
      let symbol = v.at("symbol", default: key-symbol(k))
      if type == "name" { () } else if type == "unit" { (unit,) }
      else if has-words and type == "expression" { ("$" + symbol + " =$ " + prose-value(v.value, unit),) }
      else if has-words { (prose-value(v.value, unit),) }
      else if type == "val" { (display-number(v.value),) }
      else if type == "val+unit" { (formula-quantity(v.value, unit),) }
      else { (symbol + " = " + formula-quantity(v.value, unit),) }
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

// The relation a failed comparison is printed with instead: the line then states something true, and the ✘ says the relation the report *wanted* is not the one that holds.
#let relation-negation = ("<=": ">", ">=": "<", "<": ">=", ">": "<=", "=": "!=", "!=": "=")

// The operators a relation may be written with, two characters first so that `<=` is never read as `<`.
#let relation-ops = ("==", "<=", ">=", "!=", "≤", "≥", "≠", "<", ">", "=")

// A relation cut at its operator: the operator found first in `relation-ops`' order, and the two sides as written.
#let relation-split(src) = {
  let found = none
  for o in relation-ops {
    if found == none {
      let i = src.position(o)
      if i != none { found = (op: o, at: i, len: o.len()) }
    }
  }
  if found == none { panic("verify: no relation in " + repr(src) + " -- write one of " + relation-ops.join(", ")) }
  (op: found.op, left: src.slice(0, found.at), right: src.slice(found.at + found.len))
}

// One side of a relation, read against the registry: its value and unit, and what it is -- `"number"` for a bare number, `"var"` for exactly one variable, `"formula"` for anything else -- with the math source of its symbols (`letters`) and, for a formula, of the same formula with the numbers put in (`numbers`). A bare number has neither.
#let relation-side(d, src) = {
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
  let (letters, numbers) = formula-lines(trimmed, got.operands)
  let kind = if got.operands.len() == 0 { "number" } else if one != none { "var" } else { "formula" }
  (base: got.result.base, dims: got.result.dims, value: shown.value, unit: shown.unit, kind: kind,
   letters: if kind == "number" { none } else { letters }, numbers: if kind == "formula" { numbers } else { none })
}

// One side as the relation prints it at `lv`. Level 1 the symbols, level 2 the value, level 3 everything: a variable `F_Ed = 12 kN`, a formula `F_Ed / R_d = 12 kN / 24 kN = 0.5` -- its letters, its numbers and its value (v0.86, the engineer: «au niveau 3 doit afficher F_Ed/R_d = 12 kN/24 kN = 0.5 <= 1»). A bare number is its value at every level. `mirrored` writes the right-hand side the other way round, the value first, so that the two values meet at the sign, which is what the eye compares.
// Returned as the segments the side's `=` signs part, so that a relation too wide for its line can be stacked at them (verify); joined with " = " they are the side as one line.
// `brief` (verify-core, the member checks' verdict, issue #12): at level 1 the symbols *and* the value, `σ_t,0,d / f_t,0,d = 0.41`, where `verify` prints the symbols alone.
#let relation-segments(side, lv, mirrored, brief: false) = {
  // the side's value ends its chain: no parentheses for a sign, a power of ten as one quoted atom
  let value = if side.unit == "" { "\"" + display-number(side.value) + "\"" } else { formula-quantity(side.value, side.unit) }
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
// `written`, `prefix` and `extras` are the public `#verify`'s (spec 2026-10-21-commandes-typst-refonte, REQ-004): the fine arguments it was written with, resolved here against the layers of REQ-007 -- `display` taking the place of the level's scale --, the printed name it sets before the relation (`name-visible`), and its label, description and citation, placed as `#var` places them. The engine's own callers give none of them and print by the level, as they always did.
#let verify-core(relation, level: auto, brief: false, left-unit: none, left-only: false, id: none, written: none, prefix: none, extras: none) = context {
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
  let l = relation-side(d, src.slice(0, found.at))
  let r = relation-side(d, src.slice(found.at + found.len))
  if left-unit == "%" { l = (..l, value: l.base * 100, unit: "%") }

  assert(dims-equal(l.dims, r.dims),
    message: "verify: comparing " + dims-text(l.dims) + " with " + dims-text(r.dims)
      + " -- the two sides of " + repr(src) + " must have the same dimensions")

  let holds = (test-relations.at(key).holds)(l.base, r.base)
  let shown-op = if holds { key } else { relation-negation.at(key) }
  // what the relation says of itself to `typst query` (REQ-004), joined to whatever the lines below print -- which is why they are a closure: a `return` of theirs would otherwise drop it
  let meta = wc-meta((kind: "verify", domain: var-current(d), id: id, relation: src, holds: holds, left: (value: l.value, unit: l.unit), right: (value: r.value, unit: r.unit), level: level))
  let render() = {
  // the level's scale -- 1 the symbols, 2 the values, 3 all of it -- is what `display` names since the fine arguments: `"variable"`, `"value-unit"`, `"variable-value-unit"`
  let rd = if written == none { none } else { resolve-display("verify", written, level, d) }
  let s = if rd == none { none } else { rd.settings }
  let lv = if s == none { resolve-level(level) } else { ("none": 0, "variable": 1, "value": 2, "value-unit": 2, "variable-value-unit": 3).at(s.display) }
  let x = if s == none or extras == none { (before: none, after: none, footnote: none, right: none) } else { placed-extras(extras, s) }

  // At level 3 the right-hand side is written the other way round -- value, numbers, symbols -- so the two values meet in the middle of the line, which is what the eye compares.
  let left = relation-segments(l, lv, false, brief: brief)
  // the name the relation is given (`name-visible`), before its left-hand side: `η = σ/f = … ⩽ 1`
  if prefix != none and lv >= 1 { left = (prefix,) + left }
  let right = if left-only { () } else { relation-segments(r, lv, true) }
  let op = test-relations.at(shown-op).math

  let body = math-eval(left.join(" = ") + (if left-only { "" } else { " " + op + " " + right.join(" = ") }))
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
  // its label, description and citation where their positions put them, as `#var` places them; the right-hand column sets the relation apart
  let placed(m) = if x.right != none { annotated-rows((([#x.before#m#x.after#x.footnote], x.right),)) } else if x.before == none and x.after == none and x.footnote == none { m } else { [#x.before#m#x.after#x.footnote] }
  if left.len() + right.len() <= 2 { return placed(marked) }
  // A relation wider than its line is stacked at its signs, as `#eq` stacks a formula (annotated-rows): the left side's letters, then `= <numbers>`, then `= <value> ⩽ <the right side>` -- as much of it on each line as the width holds, so the two values the eye compares stay together where they can -- each sign under the one before, the whole double-ruled and marked as the one line is. A display fraction is one atom no line break can enter, so without this the relation ran off the page. What fits is set exactly as before, in a box the width of the line it stands in, so it still sits in a sentence.
  placed(box(layout(size => {
    if measure(marked).width <= size.width + 0.01pt { return marked }
    // The signs stand where the first line's would: after its variable, or -- where the first line is a whole formula, as wide as the widest line -- at a fixed indent.
    let pad = box(width: if l.kind == "var" { measure(math-eval(left.first())).width } else { relation-indent })
    let line(src) = math-eval("#chain-pad " + src, scope: (chain-pad: pad))
    let pieces = left.slice(1).map(s => "= " + s) + (if left-only { () } else { (op + " " + right.first(),) + right.slice(1).map(s => "= " + s) })
    let rows = ()
    let current = none
    for p in pieces {
      let candidate = if current == none { p } else { current + " " + p }
      if current != none and measure(line(candidate)).width > size.width + 0.01pt { rows.push(current); current = p } else { current = candidate }
    }
    rows.push(current)
    let lines = (math-eval(left.first()),) + rows.map(line)
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
  })))
  }
  // the preview of «Affichage» prints a relation the report hides pale, marked so (`show-masked`): known from the same layers render() reads
  let masked = written != none and resolve-display("verify", written, level, d).masked
  meta + (if masked { masked-line(render()) } else { render() })
}

// References of the block below (moved out of it, issue #115): spec 2026-10-21-commandes-typst-refonte, REQ-004, D-12.
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
/// A side that is a whole formula is printed with `display: "variable-value-unit"` -- level 3's -- as its letters, then the same with the numbers put in, then its value -- `F_Ed / R_d = 12 kN / 24 kN = 0.5 ⩽ 1`:
///
/// ```typ
/// #var("F_Ed", 12, "kN", level: 0)
/// #var("R_d", 24, "kN", level: 0)
/// #verify(`F_Ed / R_d <= 1`, display: "variable-value-unit")
/// ```
///
/// **Its utilisation, named**: `name-calc:` keeps the ratio of the two sides -- the left over the right for `<=` and `<`, the right over the left for `>=` and `>` -- under that name, for a line below; `name-visible:` prints the relation as that ratio against 1, under that name -- `η = σ/f = … ⩽ 1`:
///
/// ```typ
/// #var("sigma_t_d", 0.893, "N/mm²", level: 0)
/// #var("f_t_d", 1.187, "N/mm²", level: 0)
/// #verify(`sigma_t_d <= f_t_d`, name-calc: "eta", name-visible: "eta", display: "variable-value-unit")
/// Le taux de travail vaut #var("eta").
/// ```
///
/// At `level: 0` -- `display: "none"` -- the relation is still performed, two sides of different dimensions still stopping the compile, and nothing is printed:
///
/// ```typ
/// #var("F_Ed", 2.037, "kN", level: 0)
/// #var("R_d", 4.969, "kN", level: 0)
/// #verify(`F_Ed <= R_d`, level: 0)
/// #eq("eta", `F_Ed / R_d`)
/// ```
///
/// Its label, description and citation are placed as `#var` places them -- the norm in the right-hand column with `norm-position: "line-right"`:
///
/// ```typ
/// #var("sigma_t_0_d", 4.2, "N/mm²")
/// #var("f_t_0_d", 9.9, "N/mm²")
/// #verify(`sigma_t_0_d <= f_t_0_d`, label: "Zugspannung", norm: "SIA 265", norm-section: "4.2.1", norm-position: "line-right", id: "v-6")
/// ```
///
/// **The printed sign follows the truth.** Where `F_Ed <= R_d` does not hold, the line prints `F_Ed > R_d`: what is written is then a true statement, and the ✘ is what says the relation the report wanted is not the one that holds.
///
/// The comparison is made on the **full** values, not on the decimals printed, so two numbers that print alike can still be marked ✘; a tie is absorbed at a relative 1e-9. Two sides whose dimensions differ stop the compile -- comparing a kN with a kNm is a mistake at the call site, not a comparison.
/// - relation (content, str): the relation, in math source naming the registry's keys. `<=`, `>=`, `<`, `>`, `=`, `==`, `!=` (and ≤, ≥, ≠). `*` multiplies, as `dot` does. What is quoted -- a literal's unit, `(21 "N/mm²")` -- is never read as a name.
/// - name-calc (str, none): the name the ratio of the two sides is kept under -- not for `=` and `!=`, which have none.
/// - name-visible (str, none): the symbol the relation is printed under, as its ratio against 1 -- not for `=` and `!=`.
/// - display (str, auto): `"none"`, `"variable"` (the symbols), `"value-unit"` (the values), `"variable-value-unit"` (all of it, the right-hand side reversed so that the two values meet at the sign). auto leaves it to the level.
/// - role (str, auto): `"data"`, `"compute"` or `"result"` (the default of `#verify`) -- the role of the ratio `name-calc:` keeps.
/// - label (str, none), label-position (str, auto): what the relation states, and where -- `"none"`, `"before"`, `"after"`, `"footnote"`.
/// - descr (str, none), descr-position (str, auto): why, and where -- `"none"`, `"after"`, `"footnote"`.
/// - norm (str, none), norm-section (str, none), norm-position (str, auto): the citation, and where -- `"none"`, `"in-line"`, `"line-right"`, `"footnote"`.
/// - id (str, none): the name the relation is found by -- by Woodcore in the file, and by `typst query` -- once per domain for `#var`, `#eq` and `#verify` together.
/// - level (int, auto): a preset of `display` and the positions -- 0 nothing, 1 the symbols, 2 the values, 3 all of it --, which an argument written overrides.
/// -> content
#let verify(relation, name-calc: none, name-visible: none, display: auto, role: auto, label: none, label-position: auto, descr: none, descr-position: auto, norm: none, norm-section: none, norm-position: auto, id: none, level: auto) = {
  check-level("verify", level)
  check-line-id("verify", id)
  check-fine("verify", "role", role)
  let written = written-fine("verify", (display: display, label-position: label-position, descr-position: descr-position, norm-position: norm-position))
  // a `*` is a product, printed as `dot` (star-as-dot)
  let src = star-as-dot(if type(relation) == str { relation } else { relation.text })
  let split = relation-split(src)
  let named = name-calc != none or name-visible != none
  if named and split.op in ("=", "==", "!=", "≠") {
    panic("verify: " + repr(src) + " is an equality, which has no ratio -- name-calc: and name-visible: name the ratio of a relation <=, <, >= or >")
  }
  if name-calc != none { check-key("verify", name-calc) }
  // the ratio against 1 the relation is printed as where it is given a name (D-12): the left over the right for <= and <, the right over the left for >= and >, so that a relation that holds stays one that holds
  let greater = split.op in (">=", ">", "≥")
  let ratio = "(" + (if greater { split.right } else { split.left }).trim() + ") / (" + (if greater { split.left } else { split.right }).trim() + ")"
  let shown-src = if name-visible == none { src } else { ratio + " " + (if greater { ("≥": "<=", ">=": "<=", ">": "<").at(split.op) } else { split.op }) + " 1" }
  bib-note(norm)
  var-registry.update(d => {
    let d = count-line-id(d, id)
    let d = if name-calc == none { d } else {
      let got = evaluate-formula("verify", d, ratio)
      if got.result == none { d } else {
        var-store(d, name-calc, (value: got.result.base, unit: "", symbol: key-symbol(name-calc), warning: none,
          label: label, description: descr, norm: norm, norm_ref: if norm-section == none { "" } else { norm-section }, source: none,
          role: resolve-role("verify", role, d), shown: (:)))
      }
    }
    take-next(d)
  })
  context refuse-twice("verify", id, var-registry.get())
  let extras = (label: label, description: descr, norm: norm, norm_ref: if norm-section == none { "" } else { norm-section })
  verify-core(shown-src, level: level, id: id, written: written, prefix: if name-visible == none { none } else { quoted-words(name-visible) }, extras: extras)
}
