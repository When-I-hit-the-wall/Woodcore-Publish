// lib/number.typ -- how the report writes a number: the one rule every display goes through, and the rounding it is built on (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, UI-002, UI-003, Q-005, D-08, D-12, D-22).
//
// The engineer, 19.10.2026: «Les grands nombres : toujours en notation scientifique au-delà de 99'999. Toujours 3 décimales après la virgule (sauf si zéro, 3.120 => 3.12)» and «3 chiffres significatifs, mais pas plus de 3 chiffres après la virgule. Donc 0.00234 => 2,34 · 10⁻³». Until v0.120 the report printed by five functions, two rules and a setting (`number-digits`): a value of show-calc and the same value of `eq` could be written two ways. One rule now, `display-number`, written once here and in calc/number_text.py, its Python twin, held equal by tests/test_number_text.py.
//
// What is **displayed** follows the rule; what is **transported** does not (D-22): a value Typst evaluates again -- a literal of an unfolded check, a coordinate of a figure -- keeps its precision, written by `fmt-decimals` at the digits its use needs. A figure's coordinates are not displayed numbers either (svg-number).
//
// Imports nothing of the engine: lib/calc-engine-core.typ imports it and hands its names on, so every part of the engine and every command module reads them.

// An integer as superscript digits -- 2 → "²", -5 → "⁻⁵" --, the table lib/units.json holds for the units (both minus signs: `str(-5)` writes U+2212).
#let superscript-digits = json("units.json").superscripts
#let sup(n) = str(n).clusters().map(c => superscript-digits.at(c)).join("")

// A pure rounding: what a value **transported** is written with (a literal Typst evaluates again, a math source), and what the display rule below is built on -- a number **printed** for a reader goes through `display-number` (D-22).
/// Formats a number with *at most* `digits` decimals, dropping trailing zeros: 1.7291232 -> "1.729", 0.800 -> "0.8", 438 -> "438".
///
/// ```typ
/// #fmt-decimals(1.7291232, 3)
/// ```
///
/// ```typ
/// #fmt-decimals(0.800, 3) -- #fmt-decimals(438, 3)
/// ```
///
/// Not `calc.round` + `str`, which is the obvious route and the wrong one: it leaves float artefacts (a value that rounds to 1.084 can print as 1.0840000000000001). The digits are built here from an integer instead, so what is printed is exactly what was rounded, then the tail is trimmed. A string (a load model name, a material) comes back unchanged; anything else that is not a number is refused.
/// - x (int, float, str): the value to format.
/// - digits (int): the maximum number of decimals to show.
/// -> str
#let fmt-decimals(x, digits) = {
  // a var's value may legitimately be text (a load model name), so strings pass through; anything else is a mistake at the call site -- most often math content, from calling this inside $...$ without the leading #
  if type(x) == str { return x }
  assert(type(x) == int or type(x) == float,
    message: "fmt-decimals: expected a number or a string, got " + str(type(x))
      + " -- inside math mode, escape back to code with #, as in "
      + "$ x = #val(get(v, \"value\")) $")
  let scaled = int(calc.round(calc.abs(x) * calc.pow(10, digits)))
  let s = str(scaled)
  // left-pad so a value below 1 still has an integer digit ("0.005")
  while s.len() <= digits { s = "0" + s }
  let cut = s.len() - digits
  // a whole number keeps no decimal point at all
  let frac = s.slice(cut).trim("0", at: end)
  let out = if frac == "" { s.slice(0, cut) } else { s.slice(0, cut) + "." + frac }
  // a value that rounds to zero must not come out as "-0"
  if x < 0 and scaled != 0 { "-" + out } else { out }
}

// The sign a negative number is *printed* with: U+2212 «−», the minus sign, and never the hyphen «-» the keyboard types (the engineer, v0.87: «un signe moins doit être affiché»). `fmt-decimals` keeps the hyphen on purpose -- what it returns is also Typst math source, which sets a minus for a hyphen by itself.
#let minus-sign = "\u{2212}"
#let signed-text(s) = if type(s) == str and s.starts-with("-") { minus-sign + s.slice(1) } else { s }

// The rule's two bounds: past this a number is written as a mantissa and a power of ten (D-08) ...
#let display-limit = 99999
// ... and never with more decimals than this, trailing zeros dropped (UI-003).
#let display-decimals = 3

// (mantissa, exponent) of `x` as the rule writes it: the mantissa a string of `fmt-decimals` (a hyphen for a sign), the exponent an integer or none. Scientific past 99 999, and below 0.1 where three decimals would not write the value whole -- they cannot keep its first three significant digits there: 0.00234 is "0.002" at three decimals, so it is 2.34 · 10⁻³, while 0.05, written whole at two, stays 0.05.
#let display-parts(x) = {
  let fixed = fmt-decimals(x, display-decimals)
  let a = calc.abs(x)
  if a == 0 { return ("0", none) }
  let lossy = calc.abs(float(fixed) - x) > 1e-12 * calc.max(1, a)
  // below 0.1, three decimals hold fewer than three significant digits: a value they do not write whole is written in powers of ten
  if a <= display-limit and not (lossy and a < 0.1) { return (fixed, none) }
  let e = int(calc.floor(calc.log(a, base: 10)))
  // a mantissa the rounding carries over: 999999.9 is 10.000 · 10⁵, which is 1 · 10⁶
  if calc.abs(float(fmt-decimals(x / calc.pow(10.0, e), display-decimals))) >= 10 { e += 1 }
  (fmt-decimals(x / calc.pow(10.0, e), display-decimals), e)
}

/// A number as the report prints it, the one rule of every display (UI-002, UI-003): at most three decimals and no trailing zero, a minus sign for a negative one, and a mantissa and a power of ten past 99 999 or where three decimals would lose its first three significant digits. A string passes through.
///
/// ```typ
/// #display-number(3.120) -- #display-number(1 / 3) -- #display-number(0.00234)
/// ```
///
/// ```typ
/// #display-number(123456) -- #display-number(99999) -- #display-number(-0.75)
/// ```
///
/// - x (int, float, str): the value.
/// -> str
#let display-number(x) = {
  if type(x) != int and type(x) != float { return x }
  let (m, e) = display-parts(x)
  signed-text(m) + if e == none { "" } else { " · 10" + sup(e) }
}

// The same number as **math source**, one atom: bare where it is a plain number (a negative one in parentheses, so "a - b" never reads "a - -b"), a quoted word where it carries a power of ten -- the superscript digits are text, and a quoted word is one atom, so `M / a` cannot read as M · (…/a).
#let display-source(x) = {
  if type(x) != int and type(x) != float { return x }
  let (m, e) = display-parts(x)
  if e != none { return "\"" + display-number(x) + "\"" }
  if m.starts-with("-") { "(" + m + ")" } else { m }
}

// A number and its unit as the report prints them, joined by a no-break space -- none before «°» (Q-013: «pas d'espace avant °»): 12.5°, 4.2 kN.
#let unit-gap(unit) = if unit == "°" { "" } else { "\u{a0}" }
#let display-quantity(x, unit) = {
  let s = display-number(x)
  if unit == "" { s } else { s + unit-gap(unit) + unit }
}
