// lib/subscript.typ -- how the report writes a subscript: one rule for every symbol and every formula it evaluates (spec docs/requirements/completed/2026-10-20-indices-et-niveaux.md, UI-001, ARCH-001, D-06, D-14).
//
// The engineer, 19.10.2026 and 20.10.2026: descriptive subscripts upright, in the norm's own form, and no subscript set as a variable -- «tout droit». Until v0.120 a subscript was written four ways and printed three: `N_(R d)` (an italic R and an italic d, apart), `N_"Rd"` (upright), `f_(m,y,d)` (italic, commas spaced), `gamma_(M 1)` (an italic M and an upright 1). Every source Typst evaluates as math now goes through `math-eval`, which rewrites each subscript made of letters, digits, Greek names, commas and spaces as one quoted block -- `N_(R d)` → `N_"Rd"`, `f_(c,alpha,d)` → `f_"c,α,d"`, `gamma_M1` → `gamma_"M1"` -- upright, its commas tight as the norm prints them (SIA 265 §1.2: `f_m,y,d`), its Greek letters upright too, bold where the line is bold. Measured by compiling the forms side by side on 20.10.2026.
//
// What it leaves alone: a subscript of digits only (`mu_11`, `E_(0,05)`, numbers being upright already), one that holds anything else -- an operator, a nested subscript, a call, a bracket (`x_(i+1)`, `x_(a_b)`) --, the bounds of an operator (`sum_(i=1)`, `lim_`, `max_`…), quoted text, `#` code, an escape, a superscript, and the symbol before the `_`. The data are never rewritten (D-14): an export, a `Formules/<id>.typ` keeps its author's writing, and the rule is applied where it is read.
//
// One pass of `str.replace` with a regex, no loop over characters: a formula is evaluated at every line it prints, and a long chain of branches inside a loop is what overflowed tinymist's stack in v0.60.1 (lib/formula.typ). The rule is written twice, here and in calc/typst_math.py (`normalise`, the window's and the figures'), and tests/test_subscripts.py holds the two equal on every symbol and formula of the domains, of lib/ and of the example's export.
//
// Imports nothing of the engine: lib/calc-engine-core.typ imports it, as it imports lib/number.typ, and hands its names on.

// The Greek names math knows, small then capital: a subscript's `alpha` is written as its letter, α, inside the quoted block. calc/greek.py is the same list (tests/test_units.py).
#let greek-names = (
  "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota",
  "kappa", "lambda", "mu", "nu", "xi", "pi", "rho", "sigma", "tau", "upsilon",
  "phi", "chi", "psi", "omega",
  "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega",
)
#let subscript-greek = greek-names.map(n => (n, str(dictionary(sym).at(n)))).to-dict()

// The operators whose subscript is a bound and not a name: left as written.
#let subscript-limits = ("sum", "product", "integral", "lim", "limsup", "liminf", "max", "min", "sup", "inf")

// A quoted span, an escaped quote inside it kept.
#let subscript-quoted = "\"(?:[^\"\\\\]|\\\\.)*\""
// A name's characters: letters, marks, digits -- not the superscript and subscript digits (², ₁), which Rust's \w leaves out and Python's takes: written out, so both engines read the same.
#let subscript-name = "[^\\W_²³¹¼½¾⁰-₟]"
// What the one pass reads, in this order: a quoted span, an escape, `#` code's name, an operator with its bound (all four copied as they stand), a subscript in brackets (capture 1), a subscript of one name (capture 2).
#let subscript-pattern = regex(
  subscript-quoted + "|\\\\.|#[^\\W\\d][\\w.-]*"
  + "|\\b(?:" + subscript-limits.join("|") + ")_(?:\\([^()]*\\)|" + subscript-name + "+)"
  + "|_\\(((?:[^()\"]|" + subscript-quoted + ")*)\\)"
  + "|_(" + subscript-name + "+)")
// A bracketed subscript the rule rewrites: letters, digits, commas, spaces and quoted spans only.
#let subscript-simple = regex("^(?:" + subscript-name + "|[ ,]|" + subscript-quoted + ")*$")
// The pieces of such a subscript: a quoted span, a name, a comma; spaces are dropped (`R d` is `Rd`).
#let subscript-piece = regex(subscript-quoted + "|" + subscript-name + "+|,")
#let subscript-letter = regex("[^\\W\\d_²³¹¼½¾⁰-₟]")

// The quoted block a simple subscript is written as: its parts joined by tight commas, a quoted span's text taken as it is, a Greek name as its letter.
#let subscript-block(content) = {
  let out = ""
  for m in content.matches(subscript-piece) {
    let t = m.text
    out += if t == "," { "," } else if t.starts-with("\"") { t.slice(1, -1) } else { subscript-greek.at(t, default: t) }
  }
  "\"" + out + "\""
}

#let subscript-rewrite(m) = {
  let (group, name) = m.captures
  if group != none {
    // a subscript with anything but letters, digits, commas, spaces and quotes -- or with no letter at all -- is left as written
    if group.match(subscript-simple) == none { return m.text }
    if group.replace("\"", "").match(subscript-letter) == none { return m.text }
    return "_" + subscript-block(group)
  }
  if name != none {
    if name.match(regex("^\\d+$")) != none { return m.text }
    return "_" + subscript-block(name)
  }
  m.text
}

/// A math source with every subscript written as the report prints it: upright, one quoted block, in the norm's form -- `N_(R d)` → `N_"Rd"`, `f_(m,y,d)` → `f_"m,y,d"`, `gamma_(M 1)` → `gamma_"M1"`, `k_beta` → `k_"β"`. A subscript of digits, the bound of an operator, quoted text and code are left as they stand; a source already written so comes back unchanged.
///
/// ```typ
/// #raw(normalize-subscripts("M_(y,R d) = f_y dot W_(p l,y) / gamma_(M 1)"))
/// ```
///
/// ```typ
/// #raw(normalize-subscripts("sum_(i=1)^n F_(x,i) + mu_11"))
/// ```
///
/// - src (str): Typst math source.
/// -> str
#let normalize-subscripts(src) = {
  if type(src) != str or not src.contains("_") { return src }
  src.replace(subscript-pattern, subscript-rewrite)
}

/// Evaluates Typst math source with its subscripts written as the report prints them (`normalize-subscripts`): the one door every symbol and every formula of the report goes through -- `render-symbol`, `render-formula`, the lines of `show-calc`, `#var`, `#eq`, `#val`, `#verify`. tests/test_subscripts.py refuses an `eval(..., mode: "math")` anywhere else in lib/.
///
/// ```typ
/// #math-eval("N_(R d) = f_y dot A / gamma_(M 1)")
/// ```
///
/// ```typ
/// #math-eval("sigma_(m,y,d) = M_(y,E d) / W_y")
/// ```
///
/// - src (str): Typst math source.
/// - scope (dictionary): names the source may use, as `eval`'s own `scope:`.
/// -> content
#let math-eval(src, scope: (:)) = eval(normalize-subscripts(src), mode: "math", scope: scope)
