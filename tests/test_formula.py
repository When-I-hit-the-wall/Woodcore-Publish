"""`var`, `eq`, `verify` — the calculations a report writes by hand, computed with their units.

`lib/formula.typ` is the only part of this project that carries a real algebra: units are parsed into dimensions, an expression is parsed and evaluated over quantities, and the answer is converted into the unit the engineer declared — or, since v0.63, into the one unit the table names for that dimension, which `#unit` sets. That is a lot of arithmetic to get wrong quietly, and none of it is reachable from Python — so these run Typst itself and read the numbers back out of the compiled document.

What is checked is of three kinds, and all three matter:

* **the answers**, against values this project already knows from elsewhere: the snow load of `SL`, the Sherpa capacity of `Sections/005`, the influence-width product of `Bankli-Fall1`;
* **the refusals**, each fired on purpose. A unit algebra that accepts everything is decoration;
* **the registry** itself: that a name resolves, that a domain keeps two sets of variables apart, and that what one domain wrote is still readable further down the document. That last one is the whole reason `var-domain` exists rather than a stack that pops.

⚠️ Skipped where `typst` is not on the path.
"""

import json
import re
import subprocess
import unicodedata

import conftest
from conftest import ROOT, Skip

TYPST_ROOT = conftest.TYPST_ROOT    # the example project's report folder, where commands.typ is


def _run(body, tag="out"):
    """Compiles `body` against the report's own commands and returns what it put in `metadata(...) <out>`, or the message it panicked with."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir("formula")
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(
        ["typst", "query", "--root", str(TYPST_ROOT), str(probe), f"<{tag}>", "--field", "value", "--one"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        message = conftest.panic_message(out.stderr)
        if message is None:  # not a panic but a compile error of its own -- a file not found, a syntax error
            found = re.search(r"error: (.*?)\n", out.stderr, re.S)
            message = found.group(1) if found else out.stderr.strip()
        return ("error", message)
    return ("ok", json.loads(out.stdout))


def _value(body):
    kind, got = _run(body)
    assert kind == "ok", f"expected a value, got an error:\n  {got}"
    return got


def _error(body):
    kind, got = _run(body)
    assert kind == "error", f"expected a refusal, got the value {got!r}"
    return got


def _stored(body, key, field="value"):
    """Runs `body`, then reads one field of the variable `key` back out of the registry.

    A variable's value lives in a state, so it can only be read inside a `context` -- which is exactly the trade the registry makes, and the reason `#eq` prints instead of returning.
    """
    return _value(body + f'\n#context [#metadata(var-lookup(var-registry.get(), "{key}").{field}) <out>]')


# --- the unit parser --------------------------------------------------------

def test_units_parse_to_the_right_factor_and_dimensions():
    """The units this project actually writes, each read into a factor and a dimension map.

    `N/mm²` is the one to look at: 1 N/mm² is 1 MPa is 1e6 Pa, so its factor is a million and its dimensions are those of `kN/m²` — which is what lets a stress in one be printed in the other.
    """
    cases = {
        "kN": (1000.0, "N"), "mm": (0.001, "m"), "kNm": (1000.0, "N·m"),
        "kN/m²": (1000.0, "N/m²"), "N/mm²": (1e6, "N/m²"), "kg/m³": (1000.0, "g/m³"),
        "mm3": (1e-9, "m³"), "mm²": (1e-6, "m²"), "kNm/rad": (1000.0, "N·m"),
        "m": (1.0, "m"), "": (1.0, "1"), "%": (0.01, "1"), "MPa": (1e6, "N/m²"),
        # composed by this file itself, and therefore to be readable again (v0.63)
        "Nmm": (0.001, "N·m"), "N²": (1.0, "N²"), "mm⁴": (1e-12, "m⁴"), "kNm/mm": (1e6, "N"),
    }
    body = "#metadata((" + ", ".join(
        f'"{u}": (parse-unit("{u}").factor, dims-text(parse-unit("{u}").dims))' for u in cases
    ) + ")) <out>"
    got = _value(body)
    for unit, (factor, dims) in cases.items():
        f, d = got[unit]
        assert abs(f - factor) <= 1e-9 * max(1.0, abs(factor)), f"{unit}: factor {f}, expected {factor}"
        assert d == dims, f"{unit}: dimensions {d!r}, expected {dims!r}"


def test_a_unit_that_cannot_be_read_is_none():
    assert _value('#metadata(parse-unit("Zork") == none) <out>') is True


def test_a_caret_in_a_hand_written_unit_is_stored_as_a_real_exponent():
    """`N/mm^2` typed into a call is held, and so printed, as `N/mm²` (v0.86, the engineer's request).

    parse-unit read the caret as an exponent all along, so nothing was ever computed wrong; the page showed `N/mm^2`, caret and all, because a unit is printed as a quoted word inside math. Every door a unit written by hand comes in by is checked: `var` with a number and with a var object, `var-unit`, `eq`'s `unit:` and `unit`. The var object is the case worth a line of its own: `kN/m^2` given beside an `s_k` the export holds in `kN/m²` is the same unit and must not be read as a conversion.
    """
    assert _value('#metadata(written-unit("N/mm^2")) <out>') == "N/mm²"
    assert _value('#metadata(written-unit("mm^4")) <out>') == "mm⁴"
    assert _value('#metadata(written-unit("kN/m²")) <out>') == "kN/m²"     # already right, untouched
    assert _stored('#var("f_y", 235, "N/mm^2", level: 0)', "f_y", "unit") == "N/mm²"
    body = '#var("F", 2, "kN", level: 0)\n#var("A", 400, "mm^2", level: 0)\n#eq("s", `F / A`, unit: "N/mm^2", level: 0)'
    assert _stored(body, "s", "unit") == "N/mm²"
    assert abs(_stored(body, "s") - 5) < 1e-9
    body = '#unit("m^2")\n#var("a", 2, "m", level: 0)\n#var("b", 3, "m", level: 0)\n#eq("A", `a dot b`, level: 0)'
    assert _stored(body, "A", "unit") == "m²"


def test_a_caret_in_a_hand_written_unit_is_printed_as_an_exponent():
    """What the engineer saw: `#var("f_y", 235, "N/mm^2")` printed `N/mm^2` on the page. A value printed alone, `display: "value-unit"`, is read back from the page too."""
    text = _printed('A #var("f_y", 235, "N/mm^2", level: 1)\nB #var("p", 7, "kN/m^2", display: "value-unit")', "caret_units")
    assert "^" not in text, text
    assert "235 N/mm²" in text, text
    assert "7 kN/m²" in text, text


def test_every_default_unit_is_readable_and_filed_under_its_own_dimension():
    """The unit table is keyed by `dims-text`, so an entry filed under the wrong key is an entry nothing can ever reach.

    Three things at once, and the third is the one a human eye misses: the unit parses; it carries no caret (it is printed as a quoted word inside math, where `^` comes out as `^`); and its key is exactly the dimension it has. `"N·m": "kNm"` works and `"Nm": "kNm"` would be dead weight — `pick-unit` would look up `N·m`, find nothing, and silently fall back to base units.
    """
    got = _value(
        "#metadata(default-units.pairs().map(p => "
        "(p.at(0), p.at(1), parse-unit(p.at(1)) != none, p.at(1).contains(\"^\"), "
        "dims-text(parse-unit(p.at(1)).dims)))) <out>"
    )
    assert len(got) >= 11, got
    for key, unit, readable, has_caret, dims in got:
        assert readable, f"default-units carries {unit!r}, which parse-unit cannot read"
        assert not has_caret, f"default-units carries {unit!r} with a caret -- write the superscript"
        assert key == dims, f"{unit!r} is filed under {key!r} but its dimension is {dims!r}"


# --- the names --------------------------------------------------------------

def test_a_key_becomes_the_symbol_the_report_prints():
    """The project's own rule (docs/architecture/data-contracts.md §3.1): a multi-letter subscript that is not a Greek name is quoted."""
    cases = {
        "k_dens": 'k_"dens"', "M_Ed": 'M_"Ed"', "mu_11": "mu_11",
        "F_x": "F_x", "gamma_M": "gamma_M", "eta_w": "eta_w", "b": "b",
        "q_(k,11)": "q_(k,11)",          # already math: used verbatim
        'f_(m,k)': "f_(m,k)",
        # a key whose first part is not one letter or a Greek name is read as a symbol written by hand (quoted-words)
        "M2": "M 2", "FEd": '"FEd"', "Mx": '"Mx"', "Ed_max": '"Ed"_"max"', "M2_d": "M 2_d", "mid": '"mid"',
    }
    body = "#metadata((" + ", ".join(f'"{k}": key-symbol("{k}")' for k in cases) + ")) <out>"
    got = _value(body)
    for key, want in cases.items():
        assert got[key] == want, f"{key!r} -> {got[key]!r}, expected {want!r}"


def test_a_key_with_a_hyphen_is_refused():
    """`R-k` would win over the subtraction: in a formula that also names R and k, it would stop meaning "R minus k".

    Nothing downstream could detect that, which is why it is refused at the door rather than discouraged in a comment.
    """
    message = _error('#var("R-k", 7, "kN")')
    assert "R-k" in message and "R_k" in message, message


def test_a_key_like_M2_is_printed_as_it_is_written():
    """`#eq("M2", ...)` stopped the compile on Typst's own «unknown variable: M2» (periodic audit 260916, AUD-7-425), and was then refused with a message saying to write `M_2`. The engineer asked for the key itself: it is read now as a symbol written by hand is (key-symbol through quoted-words) -- `M2` is M and 2, as `gamma_(M1)` gives M and 1, `FEd` one upright word -- and a formula naming it still substitutes it, whole word and longest first.

    Two refusals stay, each for the hyphen's reason: a key starting with `_` has nothing before its subscript to print, and a key a formula reads as an operation -- `dot`, `max` -- would be substituted into `max(a, b)`.
    """
    assert _stored('#var("M2", 5, "kNm")', "M2", "symbol") == "M 2"
    assert _stored('#var("F", 2, "kN")\n#eq("Mx", `F dot 2 "m"`)', "Mx", "symbol") == '"Mx"'
    # a formula naming such a key computes, and the longer key is not eaten by the shorter one
    body = '#var("M2", 5, "kNm")\n#var("M2_d", 3, "kNm")\n#var("a", 2, "m")\n#eq("F", `(M2 + M2_d) / a`)'
    assert abs(_stored(body, "F") - 4) < 1e-9
    assert _stored(body, "F", "unit") == "kN"
    # printed as written: the letters line groups M 2 into one atom, so the fraction is (M2)/a and not M·(2/a)
    assert _value('#metadata((atom-symbol("M 2"), atom-symbol("q_(k,11)"), atom-symbol("M_\\"E d\\""))) <out>') == \
        ['class("normal", M 2)', "q_(k,11)", 'M_"E d"']
    text = _printed('#report-level.update(3)\n' + body + "\n#eq(\"G\", `M2 / a`)", "key_m2")
    text = unicodedata.normalize("NFKC", text)
    assert "M2 = 5 kNm" in text, text
    assert "2.5 kN" in text, text
    # the two ways out of v0.79 still compile
    assert _stored('#var("M2", "M_2", 5, "kNm")', "M2") == 5
    assert _stored('#var("M_2", 5, "kNm")', "M_2") == 5
    assert _stored('#var("gamma", 1.5)', "gamma") == 1.5
    assert _stored('#var("Mx", (value: 3, unit: "kNm", symbol: "M_x"))', "Mx") == 3
    # what is still refused
    assert "starts with `_`" in _error('#var("_x", 1)')
    for word in ("dot", "max", "sqrt"):
        message = _error(f'#var("{word}", 1)')
        assert "is not a usable name" in message and "formula reads it" in message, message


def test_only_whole_words_are_substituted():
    """The names are short and one is easily a piece of another: without a word boundary the key `n` would rewrite the `n` of `ln`, and `l` the `l` of `log`."""
    got = _value('#metadata((replace-word("ln(x) + n", "n", "N"), replace-word("F_Ed + F", "F", "G"))) <out>')
    assert got[0] == "ln(x) + N", got[0]
    assert got[1] == "F_Ed + G", got[1]


def test_a_quoted_span_is_never_substituted():
    """Issue #32: a variable `m` rewrote the "m" of `(3 "m")`, the line then dying on «cannot be computed». A quoted span -- a unit, a text -- is copied whole by every substitution, an escaped quote not ending it; `unknown-names` blanks it by the same rule rather than a regex of its own, which stopped at the escaped quote."""
    got = _value('#metadata((replace-word("(3 \\"m\\") + m", "m", "X"), replace-word("\\"a\\\\\\"m\\" + m", "m", "X"), unknown-names("k + \\"x\\\\\\" y\\" + m", ((key: "m"),)))) <out>')
    assert got[0] == '(3 "m") + X', got[0]
    assert got[1] == '"a\\"m" + X', got[1]
    assert got[2] == ["k"], got[2]


# Issue #32: a variable named like a unit beside a literal carrying that unit -- each (declarations, formula, unit asked, value expected).
UNIT_NAMED = [
    ('#var("m", 2, "m")', '`m + (3 "m")`', "m", 5),
    ('#var("N", 2, "kN")', '`N + (21 "N/mm²") * (100 "mm²")`', "kN", 4.1),
    ('#var("kN", 3, "kN/m")', '`kN + (5 "kN/m")`', "kN/m", 8),
    ('#var("mm", 10, "mm")', '`mm + (3 "m")`', "mm", 3010),
    ('#var("s", 2, "s")', '`s + (1 "s")`', "s", 3),
]


def test_a_variable_named_like_a_unit_leaves_the_literal_s_unit_alone_at_every_level():
    """Issue #32: `(3 "m")` is three metres whatever a variable `m` holds -- computed and stored the same, and printed at the three levels, where the formula is substituted with symbols (2) and with values (3)."""
    for declared, formula, unit, expected in UNIT_NAMED:
        body = declared.replace(")", ", level: 0)", 1) + f'\n#eq("R", {formula}, unit: "{unit}", level: 0)'
        got = _stored(body, "R")
        assert abs(got - expected) < 1e-9, (declared, formula, got)
        for level in (1, 2, 3):
            printed = unicodedata.normalize("NFKC", _printed(f"#report-level.update({level})\n{declared}\n#eq(\"R\", {formula}, unit: \"{unit}\")", f"unit_named_{level}"))
            assert f"{expected:g}" in printed, (level, declared, formula, printed[-300:])


def test_the_v0_86_case_still_prints_at_level_three():
    """v0.86: the key `N` rewrote the "N" inside the "21 N/mm²" `f_c` had just become, and the line died on «unknown variable: kN» at level 3 only. Placeholders cured it then; the quotes being skipped now must not undo it."""
    body = '#report-level.update(3)\n#var("N", 2, "kN")\n#var("f_c", 21, "N/mm^2")\n#var("A", 100, "mm^2")\n#eq("F", `N + f_c * A`, unit: "kN")'
    text = unicodedata.normalize("NFKC", _printed(body, "v086_level3"))
    assert "4.1 kN" in text or "4,1 kN" in text, text[-300:]


# --- the answers ------------------------------------------------------------

def test_the_snow_load_of_the_project():
    """s_k and q_k of the `SL` sheet, computed by eq from the sheet's own values and checked against what the export carries.

    The constants of SIA 261 5.2.6 carry units of their own -- the 350 is a length, the 0.4 a pressure -- and the algebra needs them said, which is why a literal may take a unit. The coefficients are read from the export rather than invented here: a test that makes up its inputs and compares against real output measures nothing.
    """
    sheets = conftest.exported("calculations.json")["domains"]["snow-load"]["instances"]
    if "SL" not in sheets:
        raise Skip("the SL sheet is not in this export")
    v = sheets["SL"]["vars"]
    h_ref, s_k = v["h_ref"]["value"], v["s_k"]["value"]

    got = _stored(
        f'#var("h_ref", {h_ref}, "m")\n'
        rf'#eq("s_k", `(1 + (h_ref \/ 350 "m")^2) dot 0.4 "kN/m²"`, unit: "kN/m²")',
        "s_k")
    assert abs(got - s_k) < 1e-9, f"eq gives s_k = {got}, the sheet gives {s_k}"

    # q_k, with the sheet's own coefficients and its own branch (the sliding is hindered, so mu is floored at 0.8)
    got = _stored(
        f'#var("mu_1", {v["mu_1"]["value"]})\n'
        f'#var("C_e", {v["ce"]["value"]})\n'
        f'#var("C_T", {v["ct"]["value"]})\n'
        f'#var("s_k", {s_k}, "kN/m²")\n'
        f'#eq("q_k", `max(mu_1, 0.8) dot C_e dot C_T dot s_k`, unit: "kN/m²")',
        "q_k")
    assert abs(got - v["q_k1"]["value"]) < 1e-9, (
        f"eq gives q_k = {got}, the export's SL sheet gives {v['q_k1']['value']}"
    )


def test_the_unit_algebra_does_the_conversion_itself():
    """M_Ed / a, kNm over mm, comes to kN -- the factor of 1000 `Sections/005` used to type in by hand is what the algebra replaces."""
    got = _stored('#var("M_Ed", 0.275, "kNm")\n#var("a", 135, "mm")\n#eq("F_Ed", `M_Ed / a`, unit: "kN")', "F_Ed")
    assert abs(got - 2.037037037037037) < 1e-9, got


def test_the_default_unit_is_chosen_when_none_is_declared():
    """With no `unit:`, the same division comes out in kN rather than in the algebra's own 2037.037 N.

    One unit per dimension since v0.63, and the choice no longer reads the value: a moment is a kNm whether it is 0.5 or 5·10⁷. The price is below — a stress and a surface load share the dimension N/m² and must share its unit.
    """
    body = '#var("M_Ed", 0.275, "kNm")\n#var("a", 135, "mm")\n#eq("F_Ed", `M_Ed / a`)'
    assert _stored(body, "F_Ed", "unit") == "kN"
    assert abs(_stored(body, "F_Ed") - 2.037037037037037) < 1e-9

    stress = '#var("F", 10, "kN")\n#var("A", 2000, "mm²")\n#eq("sigma", `F / A`)'
    assert _stored(stress, "sigma", "unit") == "N/mm²", _stored(stress, "sigma", "unit")
    assert abs(_stored(stress, "sigma") - 5.0) < 1e-9

    lever = '#var("l", 6.5, "m")\n#var("n", 2)\n#eq("a", `l / n`)'
    assert _stored(lever, "a", "unit") == "mm", _stored(lever, "a", "unit")
    assert abs(_stored(lever, "a") - 3250.0) < 1e-9


def test_a_surface_load_shares_the_stress_dimension_and_says_so_in_its_unit():
    """The accepted price of one unit per dimension: N/m² is one dimension, and its default serves the stress.

    A computed surface load therefore comes out in N/mm² unless the line asks otherwise — which is what `unit:` and `#unit` are for. Held by a test because it is a decision, not an accident: if it ever changes, it changes here first.
    """
    load = '#var("g_k", 1.729, "kN/m²")\n#var("n", 1)\n#eq("q", `g_k / n`)'
    assert _stored(load, "q", "unit") == "N/mm²", _stored(load, "q", "unit")
    assert abs(_stored(load, "q") - 0.001729) < 1e-12

    asked = '#var("g_k", 1.729, "kN/m²")\n#var("n", 1)\n#eq("q", `g_k / n`, unit: "kN/m²")'
    assert _stored(asked, "q", "unit") == "kN/m²"
    assert abs(_stored(asked, "q") - 1.729) < 1e-9


def test_a_stress_converts_between_the_two_units_it_is_written_in():
    """1 N/mm² is 1000 kN/m²: same dimensions, a factor of a thousand."""
    head = '#var("F", 10, "kN")\n#var("A", 2000, "mm²")\n'
    assert abs(_stored(head + '#eq("sigma", `F / A`, unit: "N/mm²")', "sigma") - 5.0) < 1e-9
    assert abs(_stored(head + '#eq("sigma", `F / A`, unit: "kN/m²")', "sigma") - 5000.0) < 1e-6


def test_the_influence_width_of_a_static_model():
    """q_k · b_e, the one piece of arithmetic domains/statics.py does -- here written by hand and coming to the same number.

    The symbol the norm writes, `q_(k,11)`, cannot be spelled in a formula, so the key is `q_k11` and the printed symbol is given beside it. That is the second name earning its keep.
    """
    got = _stored('#var("q_k11", "q_(k,11)", 1.383, "kN/m²")\n#var("b_e", 2.5, "m")\n'
                  '#eq("q", `q_k11 dot b_e`, unit: "kN/m")', "q")
    assert abs(got - 3.4575) < 1e-9, got


def test_a_square_root_halves_the_dimensions():
    got = _stored('#var("F_x", 3, "kN")\n#var("F_z", 4, "kN")\n'
                  '#eq("F", `sqrt(F_x^2 + F_z^2)`, unit: "kN")', "F")
    assert abs(got - 5.0) < 1e-9, got


def test_a_result_feeds_the_next_line():
    """eq stores its result under its own key, so the next formula names it -- carrying its unit with it, and with nothing declared twice."""
    body = ('#var("F", 0.55, "kN")\n#var("l", 0.5, "m")\n#var("a", 135, "mm")\n'
            '#eq("M_Ed", `F dot l`)\n#eq("F_Ed", `M_Ed / a`)')
    assert abs(_stored(body, "M_Ed") - 0.275) < 1e-9
    assert _stored(body, "M_Ed", "unit") == "kNm"
    assert abs(_stored(body, "F_Ed") - 2.037037037037037) < 1e-9
    assert _stored(body, "F_Ed", "unit") == "kN"


def test_a_value_of_the_export_can_be_written_into_the_registry():
    """`#var("s_k", var-of(...))` is what ties a hand-written calculation back to the workbook (docs/typst/formulas.md §10quinquies).

    It keeps the value, the unit *and* the symbol the export spells, so the printed line is the one `data/` would have printed and the key stays whatever a formula can cite. It is also the call Woodcore copies.
    """
    sheets = conftest.exported("calculations.json")["domains"]["snow-load"]["instances"]
    if "SL" not in sheets:
        raise Skip("the SL sheet is not in this export")
    v = sheets["SL"]["vars"]["s_k"]
    body = '#var("s_k", domain: ("snow-load", "SL"))'
    assert abs(_stored(body, "s_k") - v["value"]) < 1e-9
    assert _stored(body, "s_k", "unit") == v["unit"]
    assert _stored(body, "s_k", "symbol") == v["symbol"]


def test_a_formula_that_cannot_be_evaluated_still_prints():
    """An integral: the display is ordinary math source, so it renders; the answer is given."""
    got = _stored('#eq("w", `integral_0^l (M(x) dot overline(M)(x))/(E I) dif x`, unit: "mm", value: 12.4)', "w")
    assert got == 12.4


def test_the_symbol_may_differ_from_the_key():
    """The second positional argument is the printed symbol; a *value* is never a string, so the two can never be confused."""
    assert _stored('#var("q_k11", "q_(k,11)", 1.729, "kN/m²")', "q_k11", "symbol") == "q_(k,11)"
    assert _stored('#var("k_dens", 0.806)', "k_dens", "symbol") == 'k_"dens"'


# --- the unit a result is printed in (v0.63) --------------------------------

def test_unit_sets_the_default_for_one_dimension_and_leaves_the_others():
    """`#unit` reads the dimension off the unit itself, so one call settles one kind of result.

    And it is *not* the magnitude that decides any more: 6 kNm is 6 000 000 Nmm, far outside the 0.1–1000 window the old table used, and it comes out in Nmm all the same. That window is exactly why `#unit` could not have been built on the old mechanism.
    """
    head = '#var("F", 2, "kN")\n#var("l", 3, "m")\n'
    assert _stored(head + '#eq("M", `F dot l`)', "M", "unit") == "kNm"

    moments = head + '#unit("Nmm")\n#eq("M", `F dot l`)\n#eq("a", `l / 2`)'
    assert _stored(moments, "M", "unit") == "Nmm"
    assert abs(_stored(moments, "M") - 6e6) < 1e-3
    # the length is untouched: one call, one dimension
    assert _stored(moments, "a", "unit") == "mm"

    # and it can be set back, mid-document
    both = head + '#unit("Nmm")\n#eq("M_a", `F dot l`)\n#unit("kNm")\n#eq("M_b", `F dot l`)'
    assert _stored(both, "M_a", "unit") == "Nmm"
    assert _stored(both, "M_b", "unit") == "kNm"


def test_unit_leaves_a_value_that_already_carries_one_alone():
    """`#unit` reaches what the engine *computes*, never what it was handed (docs/architecture/principles.md §2 rule 1).

    A number written out with its unit, and a value read from the export, keep the unit they came with — otherwise a global setting would silently rewrite the workbook's own figures on the page.
    """
    body = '#unit("Nmm")\n#var("M_k", 0.275, "kNm")\n#var("l", 3, "m")'
    assert _stored(body, "M_k", "unit") == "kNm"
    assert abs(_stored(body, "M_k") - 0.275) < 1e-12
    assert _stored(body, "l", "unit") == "m"


def test_unit_refuses_a_unit_with_no_dimension_and_one_it_cannot_read():
    """A dimensionless result is printed as a bare number, so `#unit("%")` would be the unit of nothing."""
    assert "no dimension" in _error('#unit("%")')
    assert "Zork" in _error('#unit("Zork")')


def test_the_natural_unit_is_composed_from_the_operands():
    """An N times a mm is an Nmm — composed without a separator, the way `kNm` is written.

    The composition is checked by reading it back rather than reasoned about: `natural-unit` keeps a spelling only if `parse-unit` returns the very factor and dimensions it was built from, and writes `·` where it does not. That is what makes a run of concatenated symbols safe.
    """
    got = _value(
        "#metadata(("
        'a: natural-unit((N: 1, mm: 1)), '
        'b: natural-unit((kN: 1, m: 1)), '
        'c: natural-unit((kN: 1, m: 1, mm: -1)), '
        'd: natural-unit((mm: 2)), '
        "e: natural-unit((:)) == none"
        ")) <out>"
    )
    assert got["a"] == "Nmm", got
    assert got["b"] == "kNm", got
    assert got["c"] == "kNm/mm", got
    assert got["d"] == "mm²", got
    assert got["e"] is True

    # every one of them reads back to what it was built from
    checks = _value(
        "#metadata((parse-unit(\"Nmm\").factor, parse-unit(\"kNm/mm\").factor, "
        "dims-text(parse-unit(\"Nmm\").dims))) <out>"
    )
    assert abs(checks[0] - 0.001) < 1e-12 and abs(checks[1] - 1e6) < 1.0
    assert checks[2] == "N·m"


def test_a_dimension_the_table_does_not_name_falls_back_to_base_units():
    """The v0.63 display bug, held: two forces multiplied give N², and it is printed as N², not `N^2`.

    The caret was not cosmetic. A chosen unit is printed as a *quoted word* inside math, where `^` is a character and not an operator, so the page read `1000000 N^2`.
    """
    body = '#var("F", 1, "kN")\n#eq("M", `F dot F`)'
    assert _stored(body, "M", "unit") == "N²", _stored(body, "M", "unit")
    assert abs(_stored(body, "M") - 1e6) < 1e-6

    printed = _value(body + '\n#context [#metadata(display-number(var-lookup(var-registry.get(), "M").value)) <out>]')
    assert printed == "1 · 10⁶", printed


def test_a_variable_inline_is_one_word_of_its_sentence():
    """A `#var` printed inline broke between its symbol and `= 2 m` at the end of a line -- «γ_M = 1.7 a» on one line and «= 2 m» on the next. The symbol, the sign and the value are joined by no-break spaces now, in `#var`, `#var-unit` and `#val`'s expression, as the number and its unit already were (v0.86): in a column narrower than the variable it overflows on one line rather than break inside it."""
    for call in ('var("a", 2, "m")', 'var("M2", 5, "kNm")'):
        one, narrow = _value(f'#context [#metadata((measure(block({call})).height / 1pt, measure(block(width: 3mm, {call})).height / 1pt)) <out>]')
        assert abs(narrow - one) < 0.01, f"{call} breaks inside itself: {narrow} pt in a narrow block against {one} pt on one line"


def test_a_unit_beside_a_value_that_has_one_converts_it():
    """`#var("F", <a var worth 7 kN>, "N")` prints 7000 N, not "7 N" (v0.63).

    Until v0.63 the unit given replaced the label and left the number alone — silently wrong, on a value read from the workbook, which is the one class of error this whole file exists to prevent.
    """
    body = '#var("F", (value: 7, unit: "kN", symbol: "F"), "N")'
    assert _stored(body, "F", "unit") == "N"
    assert abs(_stored(body, "F") - 7000.0) < 1e-9

    # and one whose dimension does not match keeps its own unit, with the warning to read
    refused = '#var("G", (value: 7, unit: "kN", symbol: "G"), "mm")'
    assert _stored(refused, "G", "unit") == "kN"
    assert _stored(refused, "G", "warning")["wanted"] == "mm"


def test_a_big_number_is_printed_as_a_power_of_ten():
    """Past 99 999 a number is unreadable written out; below it, nothing changes -- and a small one that three decimals would not write whole takes a power of ten too (lib/number.typ, the one rule since v0.120: Q-005)."""
    got = _value(
        "#metadata((display-number(99999), display-number(100000), display-number(1234567), "
        "display-number(999999.9), display-number(-2500000), display-number(1.729), "
        "display-number(0.0000123))) <out>"
    )
    assert got[0] == "99999"                    # the threshold itself stays plain
    assert got[1] == "1 · 10⁵"
    assert got[2] == "1.235 · 10⁶"
    assert got[3] == "1 · 10⁶"                  # the rounding carries the mantissa to 10
    assert got[4] == "−2.5 · 10⁶"               # a printed number carries a minus sign
    assert got[5] == "1.729"
    assert got[6] == "1.23 · 10⁻⁵"              # three decimals would print 0: the first three significant digits are kept (Q-005)


def test_the_scientific_notation_does_not_reach_the_rest_of_the_report():
    """Confined to lib/formula.typ on purpose: `fmt-decimals` is what show-calc, the tables and the figures print through.

    Putting the rule there would have rewritten numbers on pages nobody asked about — a connection's I_p = 157000 mm² among them. This is the check that the confinement holds.
    """
    got = _value('#metadata((fmt-decimals(157000, 3), fmt-decimals(1234567, 3))) <out>')
    assert got == ["157000", "1234567"], got


# --- the registry and its domains -------------------------------------------

def test_a_name_the_registry_does_not_hold_is_refused():
    """The one mistake this design can make, and the one it must not make in silence."""
    message = _error('#var("F", 1, "kN")\n#eq("M", `F dot l`)')
    # The panic reaches us with its quotes escaped, so the words are what to match on.
    assert "no variable named" in message and "l" in message and "#var" in message, message
    assert "Declared here: F" in message, f"the message should list what *is* declared: {message}"


def test_two_domains_keep_their_own_variables_and_both_survive():
    """The reason var-domain exists rather than a scope that pops: what a column wrote is still readable further down the document.

    A domain is a key in the registry, not a stack frame -- only the *current* domain is pushed and popped, never what it holds.
    """
    body = """
#domain("left")[#var("F", 0.55, "kN") #var("l", 0.5, "m") #eq("M", `F dot l`)]
#domain("right")[#var("F", 1, "kN") #var("l", 0.5, "m") #eq("M", `F dot l/2`)]
#context [#metadata((
  left: var-registry.get().domains.at("left").M.value,
  right: var-registry.get().domains.at("right").M.value,
)) <out>]
"""
    got = _value(body)
    assert abs(got["left"] - 0.275) < 1e-9, got
    assert abs(got["right"] - 0.25) < 1e-9, got


def test_a_domain_sees_what_was_declared_outside_it():
    """R_d, declared at the level of a section, must be nameable inside every column of a grid."""
    got = _value("""
#var("R_d", 2.655, "kN")
#domain("a-column")[#var("F_Ed", 2.037, "kN") #eq("eta", `F_Ed / R_d`)]
#context [#metadata(var-registry.get().domains.at("a-column").eta.value) <out>]
""")
    assert abs(got - 2.037 / 2.655) < 1e-9, got


# --- verify -----------------------------------------------------------------

def test_verify_holds_and_fails_on_the_full_values():
    """The comparison is made on the values, not on the decimals printed."""
    body = '#var("a", 2.0374, "kN")\n#var("b", 2.0371, "kN")\n'
    assert _value(body + '#context [#metadata(relation-negation.at("<=")) <out>]') == ">"
    # a <= b is false on the full values though both print as 2.037
    assert _value(body + '#metadata(fmt-decimals(2.0374, 3) == fmt-decimals(2.0371, 3)) <out>') is True


def test_verify_refuses_two_sides_of_different_dimensions():
    """Comparing a kN with a kNm is a mistake at the call site, not a comparison."""
    message = _error('#var("F", 1, "kN")\n#var("M", 1, "kNm")\n#verify(`F <= M`)')
    assert "N·m" in message and "comparing" in message.lower(), message


def test_verify_reads_a_whole_formula_on_either_side():
    """Either side is an expression, read by the same parser #eq uses."""
    body = ('#var("F_Ed", 2.037, "kN")\n#var("R_d", 2.655, "kN")\n'
            '#verify(`F_Ed / R_d <= 1`)\n#metadata("compiled") <out>')
    assert _value(body) == "compiled"


def test_verify_prints_the_relation_that_actually_holds():
    """Where `a <= b` does not hold, the line prints `a > b`: what is written is then true, and the ✘ is what says the relation the report wanted is not the one that holds."""
    got = _value('#metadata(relation-negation) <out>')
    assert got == {"<=": ">", ">=": "<", "<": ">=", ">": "<=", "=": "!=", "!=": "="}, got


# --- the refusals -----------------------------------------------------------

def test_a_declared_unit_the_formula_cannot_reach_prints_and_does_not_stop():
    """Since v0.63 this is a red line under the result, not a refusal (docs/typst/formulas.md §10quinquies).

    Three things have to hold at once, and the second is the one that matters: the compile finishes; the value stored is *physically right*, in the unit the operands themselves were written in, so the lines below go on computing from it; and the warning names both units, so the page says which two disagree.
    """
    body = '#var("M", 0.275, "kNm")\n#var("a", 135, "mm")\n#eq("F", `M / a`, unit: "kNm")'
    assert _stored(body, "F", "unit") == "kNm/mm", _stored(body, "F", "unit")
    assert abs(_stored(body, "F") - 0.275 / 135) < 1e-12

    warning = _stored(body, "F", "warning")
    assert warning["wanted"] == "kNm" and warning["natural"] == "kNm/mm", warning

    # and the line below still computes from it: a kNm/mm *is* a force, so twice it is 4.074 kN
    chained = body + '\n#eq("G", `F dot 2`)'
    assert _stored(chained, "G", "unit") == "kN"
    assert abs(_stored(chained, "G") - 2 * 2.037037037037037) < 1e-9


def test_adding_different_dimensions_is_refused():
    message = _error('#var("a", 1, "kN")\n#var("b", 2, "m")\n#eq("x", `a + b`, unit: "kN")')
    assert "cannot add" in message, message


def test_a_given_value_that_contradicts_the_formula_is_refused():
    message = _error('#var("M", 0.275, "kNm")\n#var("a", 135, "mm")\n'
                     '#eq("F", `M / a`, unit: "kN", value: 9.9)')
    assert "9.9" in message and "one of the two is wrong" in message, message


def test_an_unreadable_unit_is_refused():
    message = _error('#var("a", 1, "Zork")\n#eq("x", `a`, unit: "Zork")')
    assert "Zork" in message, message


def test_a_formula_that_cannot_be_computed_and_has_no_value_is_refused():
    message = _error('#eq("w", `integral_0^l dif x`, unit: "mm")')
    assert "value:" in message, message
    assert "integral" in message, message


def test_a_square_root_of_odd_dimensions_is_refused():
    message = _error('#var("a", 4, "m")\n#eq("x", `sqrt(a)`, unit: "m")')
    assert "sqrt" in message and "even" in message, message


def test_an_unknown_argument_is_refused():
    """A typo in a named argument would otherwise pass silently, the sink taking anything."""
    message = _error('#var("a", 1, "kN", descrip: "oops")')
    assert "descrip" in message and "descr" in message, message


def test_a_dimensionless_factor_is_accepted_and_is_the_one_thing_not_caught():
    """1000 is a valid dimensionless factor, so `M / a dot 1000` passes the algebra and comes to 2037 kN.

    Here on purpose, and as a warning in the docstring of `lib/formula.typ`: the algebra checks *dimensions*, never *sizes*. What it buys against a magnitude error is that the substituted line prints `0.275 kNm / 135 mm · 1000`, and 2037 kN under a bench is an answer a reader sees.
    """
    got = _stored('#var("M", 0.275, "kNm")\n#var("a", 135, "mm")\n'
                  '#eq("F", `M / a dot 1000`, unit: "kN")', "F")
    assert abs(got - 2037.037037037037) < 1e-6, got


# --- the substituted line ---------------------------------------------------

def test_a_substituted_operand_is_one_math_atom():
    """An operand carrying a unit is two words, and math's `/` takes the one atom on each side of it.

    Found in v0.60.1, writing `F_"Ed" = M / a` in `Sections/005`. Substituted as `0.275 "kNm" / 135 "mm"` the line printed as 0.275 · (kNm/135) · mm -- a formula that does not state what was computed, which is the one thing `eq` exists to prevent. A value with a unit is therefore quoted whole, so it is a single atom; one without is a bare number, parenthesised where it is negative so that `a - b` never reads `a - -b`.
    """
    got = _value('#metadata((\n'
                 '  unit: substituted(0.275, "kNm"),\n'
                 '  bare: substituted(135, ""),\n'
                 '  negative: substituted(-2.5, ""),\n'
                 '  negative-unit: substituted(-2.5, "kN"),\n'
                 ')) <out>')
    assert got["unit"] == '"0.275 kNm"', got["unit"]
    assert got["bare"] == "135", got["bare"]
    assert got["negative"] == "(-2.5)", got["negative"]
    # quantity-in-formula writes a typographic minus, not a hyphen
    assert got["negative-unit"] == '"−2.5 kN"', got["negative-unit"]


# --- val: one value, wherever it comes from (v0.80) -------------------------
# `val` replaced `fmt`, `inline-value` and `live-load`: one command prints one value, whether it is handed over, named in the report's registry or named in the export (docs/typst/formulas.md §10quinquies, docs/decisions.md §13). What is checked here is that the sources give the same four parts, that a unit written over is said on the page, and that each refusal fires.


def _printed(body, name="formula_print"):
    """What `body` puts on the page, whitespace collapsed -- for what is *printed* rather than what is stored.

    A footnote is laid out at the foot of the page and comes back in this text too, which is how the orange line under an overridden unit is read back.
    """
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    from pypdf import PdfReader
    raw = "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
    return re.sub(r"\s+", " ", raw)


def test_a_unit_written_over_changes_nothing():
    """`unit:` is display only (the engineer's request, Q-011 of the spec 2026-10-21-commandes-typst-refonte): the value printed is converted, the variable keeps the unit it was declared with."""
    text = _printed('#var("R", 7, "kN", level: 0)\nA #var("R", unit: "N", display: "value-unit") B #var("R", display: "value-unit")', "val_override")
    # the footnote's marker stands between the two, which is the point of it
    assert "A 7000 N" in text and "B 7 kN" in text, text
    assert _stored('#var("R", 7, "kN", level: 0)\n#var("R", unit: "N")', "R", "unit") == "kN"


# --- var-line: a row of declarations (v0.80) --------------------------------


# --- the levels: 0 prints nothing, every other level prints something (v0.85)


# One probe exercising all six commands at one level, so that the rule is read on a page rather than
# command by command. `#var-unit` names the `b` the row above it declared -- a row does not scope.
_LEVELS_PROBE = (
    '#report-level.update(3)\n'
    '#var("R_k", 7, "kN", level: {lv})\n'
    '#eq("R_d", `R_k / 2`, level: {lv})\n'
    '#verify(`R_d <= R_k`, level: {lv})\n'
    'A #var("R_d", level: {lv}) B\n'
    'ENDE'
)


def test_level_0_prints_nothing_at_all():
    """The engineer's rule, in his own words: «au level 0, il ne doit pas y avoir d'affichage».

    Asserted on the *whole* page rather than value by value, which is what catches a command that leaves a mark of itself behind -- a separator, an empty grid row, a footnote marker, the ✔ of a relation. What is left is the prose around the calls: the value printed alone left nothing between A and B, and the sentence closed over it.
    """
    text = _printed(_LEVELS_PROBE.format(lv=0), "level_0")
    assert text.strip() == "A B ENDE", text


def test_level_0_still_declares_computes_and_converts():
    """What "prints nothing" must not mean: does nothing. A variable hidden today is read by a formula tomorrow, so every command does its whole work at level 0 and holds back only the emission."""
    assert _stored('#var("R_k", 7, "kN", level: 0)', "R_k") == 7
    assert _stored('#var("R_k", 7, "kN", level: 0)\n#eq("R_d", `R_k / 2`, level: 0)', "R_d") == 3.5
    # and the refusals still fire, at the level that prints nothing: a line hidden today is a line
    # printed in the next report, and it must not be the report that finds the mistake
    assert "cannot add" in _error('#var("a", 1, "kN")\n#var("b", 2, "m")\n#eq("x", `a + b`, level: 0)')
    assert "same dimensions" in _error('#var("a", 1, "kN")\n#var("b", 2, "m")\n#verify(`a <= b`, level: 0)')


def test_every_level_but_0_prints_something():
    """The other half of the rule: «tout autre chose que level:0 doit toujours afficher quelque chose».

    It is what parts the two notions. Until v0.85 `#var` printed nothing at level 1, so the *client* report -- level 1, section 3.7 -- was the one report from which every variable written by hand was missing, and "hide this declaration" and "this is a client report" were the same argument. Level 1 now prints what level 2 prints, and the levels above it add to it; only 0 is silent.
    """
    for lv in (1, 2, 3):
        text = _printed(_LEVELS_PROBE.format(lv=lv), "level_%d" % lv)
        assert "= 7 kN" in text, (lv, text)             # var
        assert "= 3.5 kN" in text, (lv, text)           # eq, the answer at every level
        assert "⩽" in text and "✔" in text, (lv, text)  # verify, its relation and its mark
        assert "3.5 kN B" in text, (lv, text)           # a variable printed again, in the sentence


def test_a_level_outside_0_to_3_is_refused_by_every_command():
    """Fired on purpose, once per command. Until v0.85 none of these five checked at all: `level: 4` behaved as 3, and `level: 0` as 1 -- so the level the engineer has just been given would have been read as "nothing special" by the four commands that did not gate on it."""
    for call in ('#var("a", 1, "kN", level: 4)',
                 '#var("a", 1, "kN")\n#eq("x", `a`, level: 4)',
                 '#var("a", 1, "kN")\n#verify(`a <= a`, level: 4)'):
        message = _error(call)
        assert "invalid level" in message, (call, message)
        assert "0 (nothing printed)" in message, (call, message)


# --- label and description are two fields (v0.85.1) -------------------------


def test_a_var_of_the_export_keeps_its_label_and_its_description():
    """The defect the engineer read off `find`'s Bezeichnung column, and the reason that column had to look in two places.

    In the data the two are different fields (sections 3.1, 9): `label` is what the variable *is* -- «Expositionsbeiwert» -- and `description` is why this value was chosen, which carries the `choices` with it. `var-record` stored `#var`'s `label:` under `description`, a leftover from v0.80 renaming `descr:` to `label:` without renaming the field, so a var object read out of the export had its label **dropped** and printed its choices sentence in its place. Invisible for five versions because nothing put a var of the export and a var of the report in one column until `find` did.
    """
    carried = '#var("korrektur", domain: ("snow-load", "SL"))'
    assert _stored(carried, "korrektur", "label") == "Korrektur Wert"
    assert "Anhang D" in _stored(carried, "korrektur", "description")
    # written down here, `label:` is the label and there is no description at all
    assert _stored('#var("a", 135, "mm", label: "Abstand")', "a", "label") == "Abstand"
    assert _stored('#var("a", 135, "mm", label: "Abstand")', "a", "description") is None
    # the call's own label still wins over the one the value carries
    assert _stored('#var("korrektur", domain: ("snow-load", "SL"), label: "Eigene")', "korrektur", "label") == "Eigene"
    # and it is the label that reaches the page, where until v0.85.1 the description did
    text = _printed('#report-level.update(2)\n' + carried, "carried_label")
    assert "Korrektur Wert" in text, text


def test_var_val_and_eq_share_one_level_scheme():
    """The engineer's rule for the three commands that print a single value: 0 nothing, 1 the value, 2 the label with it, 3 the citation as well.

    What moved in v0.85.1 is the two ends. `#var` printed its citation in the right-hand column at **every** level, so a client report carried «SIA 265 §6.2.1.1» beside a bare number and nothing saying what the number was; and it printed its label only at level 3, which is one level later than the word it names is wanted. `#eq` had no label at all.
    """
    body = ('#var("R_k", 7, "kN", label: "Kapazitaet", norm: "Sherpa", norm-ref: "ETA-12/0197")\n'
            '#eq("R_d", `R_k / 2`, label: "Bemessungswert", norm: "SIA 265", norm-ref: "2.2.5")\n'
            'A #var("R_k") B')
    at = {lv: _printed('#report-level.update(%d)\n' % lv + body, "scheme_%d" % lv) for lv in (1, 2, 3)}

    # 1: the value and nothing else
    assert "= 7 kN" in at[1] and "= 3.5 kN" in at[1], at[1]
    for word in ("Kapazitaet", "Bemessungswert", "Sherpa", "SIA 265"):
        assert word not in at[1], (word, at[1])

    # 2: the labels, still no citation
    assert "Kapazitaet" in at[2] and "Bemessungswert" in at[2], at[2]
    assert "Sherpa" not in at[2] and "SIA 265" not in at[2], at[2]

    # 3: the citations join them
    assert "Kapazitaet" in at[3] and "Bemessungswert" in at[3], at[3]
    assert "Sherpa" in at[3] and "ETA-12/0197" in at[3], at[3]
    assert "SIA 265" in at[3] and "2.2.5" in at[3], at[3]


def test_eq_carries_a_label_of_its_own():
    """`#eq` gained `label:` in v0.85.1 -- what the answer *is*, printed after it from level 2, the way `#var` prints its own. Its formula lines did not move: letters at 2, numbers at 3."""
    text = _printed('#report-level.update(3)\n#var("M", 0.275, "kNm")\n#var("a", 135, "mm")\n'
                    '#eq("F", `M / a`, label: "Schraubenkraft")', "eq_label")
    assert "Schraubenkraft" in text, text
    assert "0.275 kNm" in text, text      # the numbers line is still there at level 3


def test_level_3_is_complete_label_description_norm_and_norm_ref():
    """The engineer's own word for it: at level 3 nothing a value carries is left unsaid.

    Where each part goes is settled and not interchangeable. On a line of its own -- `#eq`, and `#var` with `note: "line"` -- the **label** is what the variable *is*, so it is read with it, after an em dash on the line (v0.61.1); the **description** is why *this* value was chosen, which is section 9's footnote and stays one; the **citation** is the right-hand column's, which is what keeps it level with the line it cites (section 10). Inline -- `#var` by default since v0.86, a sentence, a `var-line` -- there is no em dash and no column, so all three fold into the one footnote `line-note` builds.
    """
    body = ('#var("R_k", 7, "kN", label: "Kapazitaet", descr: "Aus dem Katalog",'
            ' norm: "Sherpa", norm-ref: "ETA-12/0197")\n'
            '#eq("R_d", `R_k / 2`, label: "Bemessungswert", descr: "Haelfte", norm: "SIA 265", norm-ref: "2.2.5")\n'
            'A #var("R_k") B')
    three = _printed('#report-level.update(3)\n' + body, "complete_3")
    for word in ("Kapazitaet", "Aus dem Katalog", "Sherpa", "ETA-12/0197",
                 "Bemessungswert", "Haelfte", "SIA 265", "2.2.5"):
        assert word in three, (word, three)
    # the description is level 3's and not level 2's: a label names a number, a description explains a choice
    two = _printed('#report-level.update(2)\n' + body, "complete_2")
    assert "Kapazitaet" in two and "Bemessungswert" in two, two
    assert "Aus dem Katalog" not in two and "Haelfte" not in two, two
    # and inline the three are one footnote, in that order
    assert "Kapazitaet; Aus dem Katalog; Sherpa" in three, three


def test_var_val_and_eq_all_take_label_descr_norm_and_norm_ref():
    """One set of four arguments on the three commands that print a single value, each overriding what the value already carries (v0.85.2, the engineer's request).

    The override is the point rather than the declaration: a var of the export arrives with a label, a description and a citation of its own, and a report quoting it for something narrower has to be able to say so at the call.
    """
    # given where the value carries none
    assert _stored('#var("a", 1, "kN", label: "L", descr: "D")', "a", "label") == "L"
    assert _stored('#var("a", 1, "kN", label: "L", descr: "D")', "a", "description") == "D"
    assert _stored('#eq("x", `1 + 1`, label: "L", descr: "D")', "x", "label") == "L"
    assert _stored('#eq("x", `1 + 1`, label: "L", descr: "D")', "x", "description") == "D"

    # and overriding what a var of the export brought with it
    carried = '#var("ce", domain: ("snow-load", "SL"), label: "Eigene", descr: "Eigener Grund")'
    assert _stored(carried, "ce", "label") == "Eigene"
    assert _stored(carried, "ce", "description") == "Eigener Grund"
    assert _stored(carried, "ce", "norm") == "SIA 261"          # what is not overridden is kept
    over = '#var("ce", domain: ("snow-load", "SL"), norm: "SIA 265", norm-ref: "3.1")'
    assert _stored(over, "ce", "norm") == "SIA 265"
    assert _stored(over, "ce", "norm_ref") == "3.1"

    # a value written here states its own four, and overrides those a var does carry
    text = _printed('#report-level.update(3)\nA #var("R_k", 7, "kN", label: "L", descr: "D",'
                    ' norm: "Sherpa", norm-ref: "ETA-1") B', "val_four")
    assert "L; D; Sherpa" in text, text
    quoted = _printed('#report-level.update(3)\nA #var("s_k", domain: ("snow-load", "SL"),'
                      ' label: "Enger", descr: "Nur hier") B', "val_override_four")
    assert "Enger; Nur hier" in quoted, quoted

def test_the_commands_val_replaced_are_gone():
    """`fmt`, `inline-value` and `live-load` were folded into `val` in v0.80 (section 13). Named here so that bringing one back is a decision and not an accident -- and so that what an old report gets is Typst's own «unknown variable», which names the call."""
    for call in ('#fmt(1.5)', '#inline-value("snow-load", "SL", "s_k")', '#live-load("A1", "q_k")'):
        assert "unknown variable" in _error(call), call


# --- v0.86: what the engineer asked of the commands a report writes by hand --------


def _lines(body, name):
    """What `body` puts on the page, line by line as the PDF sets it -- for what lands on which line, which `_printed` collapses away."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    from pypdf import PdfReader
    raw = "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
    return [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]


def test_verify_prints_a_formula_side_in_letters_numbers_and_value_at_level_3():
    """The engineer's line, word for word: «`#verify(`F_Ed / R_d <= 1`)` au niveau 3 doit afficher `F_Ed/R_d = 12kN/24kN = 0.5 <= 1`».

    A side that is a whole formula is its letters, the same with the numbers put in, and its value; a single variable stays `F_Ed = 12 kN`; a bare number is itself. The right-hand side keeps its mirrored order -- value, numbers, letters -- so the two values meet at the sign. Level 2 is the values alone and level 1 the symbols, as before.
    """
    decl = '#var("F_Ed", 12, "kN", level: 0)\n#var("R_d", 24, "kN", level: 0)\n'
    three = _printed(decl + '#verify(`F_Ed / R_d <= 1`, level: 3)', "verify_formula_3")
    # the fraction is set as a fraction, so its two halves come back one above the other: what is read here is the chain
    assert "12 kN" in three and "24 kN" in three and "= 0.5 ⩽ 1" in three, three
    mirrored = _printed(decl + '#verify(`1 >= F_Ed / R_d`, level: 3)', "verify_formula_mirror")
    assert "1 ⩾ 0.5 = 12 kN" in mirrored, mirrored
    two = _printed(decl + '#verify(`F_Ed / R_d <= 1`, level: 2)', "verify_formula_2")
    assert "0.5 ⩽ 1" in two and "kN" not in two, two
    one = _printed(decl + '#verify(`F_Ed / R_d <= 1`, level: 1)', "verify_formula_1")
    assert "0.5" not in one and "kN" not in one and "⩽ 1" in one, one
    # a variable on each side is as it was
    assert "= 12 kN ⩽ 24 kN =" in _printed(decl + '#verify(`F_Ed <= R_d`, level: 3)', "verify_vars_3")
    # a product needs no fraction to read: letters, numbers and value in one run
    product = _printed(decl + '#verify(`2 * F_Ed <= R_d`, level: 3)', "verify_product_3")
    assert "2 ⋅ 12 kN = 24 kN ⩽ 24 kN" in product.replace("·", "⋅"), product


def test_a_negative_number_is_printed_with_a_minus_sign():
    """«un nombre négatif doit afficher un vrai signe moins» (v0.86): U+2212, never the hyphen `fmt-decimals` writes.

    Converted where a number is printed and nowhere earlier: the registry keeps the number, and `fmt-decimals`, which builds math source, keeps its hyphen -- math sets that as a minus by itself.
    """
    text = _printed('#report-level.update(3)\n#var("M", -2.5, "kNm")\nA #var("M") B #var("M", display: "value") C\n'
                    '#eq("M_2", `M * 2`)\n#verify(`M <= 0 "kNm"`)\n#find(object: "variable")', "minus_sign")
    assert "-2.5" not in text and "-5" not in text, text
    assert "−2.5 kNm" in text and "B −2.5 C" in text and "−5 kNm" in text, text
    assert _value('#metadata(fmt-decimals(-2.5, 3)) <out>') == "-2.5"       # the primitive is untouched
    assert _value('#metadata(signed-text("EL+AL-Dach")) <out>') == "EL+AL-Dach"   # a word is not a number


def test_find_sets_a_long_word_as_words_that_wrap():
    """«une valeur texte longue est placée dans une cellule de formule qui ne passe pas à la ligne et déborde» (v0.86).

    The norm's example beside category A1 is a hundred characters long, and set as math it ran past the page and squeezed the Bezeichnung column to a letter, its heading hyphenated three times over. As words it wraps, and the heading stands whole.
    """
    for kind in ("val+unit", "expression", "val"):
        lines = _lines(f'#find(object: "variable", domain: ("live-load", "A1"), type: "{kind}")', "find_words_" + kind.replace("+", "_"))
        assert any("Bezeichnung" in line for line in lines), (kind, lines)
        example = [line for line in lines if "Wohngebäuden" in line]
        assert example and not any("Toiletten" in line for line in example), (kind, lines)
    # a table of numbers alone is laid out as before
    assert "1.394 kN/m²" in _printed('#find(object: "variable", domain: ("snow-load", "SL"), type: "val+unit")', "find_numbers")


def test_a_word_math_does_not_know_is_quoted_in_a_symbol():
    """«pourquoi dois-je écrire `G_(1,\\"Ed\\")` … cela rendrait l'écriture beaucoup plus facile» (v0.86).

    A run of letters math does not know is quoted; a name it knows keeps its meaning -- Typst's own reading, so what compiled before compiles to the same page; one letter and a number is that letter and that number; quoted text, code and numbers are left alone; and the rewriting given its own output gives it back.
    """
    cases = {
        "G_(1,Ed)": 'G_(1,"Ed")', "W_(y,erf)": 'W_(y,"erf")', "gamma_(M1)": "gamma_(M 1)",
        'M_"Ed"': 'M_"Ed"', "q_(k,11)": "q_(k,11)", "mu_11": "mu_11", "k_(mod)": "k_(mod)",
        "arrow.r_(ab)": 'arrow.r_("ab")', "sqrt(Ed)": 'sqrt("Ed")', "c_(pi)": "c_(pi)",
        "F_(Rück)": 'F_("Rück")', "#h(1em) Ed": '#h(1em) "Ed"', '"Lastmodell"': '"Lastmodell"',
        "M_(Ed,max)": 'M_("Ed",max)', "2ab": '2"ab"',
        # a function math knows is a word where the symbol does not call it: set bare, math printed its name in a monospaced face
        "M_mid": 'M_"mid"', "N_(norm)": 'N_("norm")', "sqrt(x)": "sqrt(x)", "lr(x)": "lr(x)",
    }
    typ = lambda s: json.dumps(s, ensure_ascii=False)   # a Typst string: its escapes are JSON's but for \uXXXX
    body = "#metadata((" + ", ".join(f"(quoted-words({typ(k)}), quoted-words(quoted-words({typ(k)})))" for k in cases) + ")) <out>"
    for (src, want), (got, twice) in zip(cases.items(), _value(body)):
        assert got == want, f"{src!r} -> {got!r}, expected {want!r}"
        assert twice == got, f"{src!r} is not stable: {got!r} -> {twice!r}"
    # every door a symbol written by hand comes in by
    assert _stored('#var("G_1_Ed", "G_(1,Ed)", 1.5, "kN/m²")', "G_1_Ed", "symbol") == 'G_(1,"Ed")'
    assert _stored('#var("g_k", 1.2, "kN/m²")\n#eq("G_2_Ed", "G_(2,Ed)", `1.35 dot g_k`)', "G_2_Ed", "symbol") == 'G_(2,"Ed")'
    text = _printed('#report-level.update(3)\n#var("W_y", "W_(y,erf)", 12.5, "cm³")\n#var("g_k", 1.2, "kN/m²")\n'
                    '#eq("G_Ed", "G_(1,Ed)", `1.35 dot G_1 dot g_k`, value: 0)\n'
                    'A #var("M_Ed_max", "M_(Ed,max)", 5, "kNm") B', "unquoted_words")
    assert "erf" in text and "Ed" in text and "max" in text, text


def test_a_star_is_a_product_printed_as_a_dot():
    """`show math.star: $dot$` in config.typ did not reach `#eq` (v0.86): a show rule works on content, never on the string a formula is written as. So a `*` is read as `dot` where the formula is read -- evaluated as a product and printed as one, `·` -- and left alone inside quotes and where it is an attachment, `F^*`."""
    got = _value('#metadata((star-as-dot("1.35 * g_k"), star-as-dot("F^* + a*b"), star-as-dot("\\"a*b\\" * 2"))) <out>')
    assert got[0].split() == ["1.35", "dot", "g_k"], got
    assert got[1].replace(" ", "") == "F^*+adotb", got
    assert got[2].startswith('"a*b"') and "dot" in got[2], got
    body = '#var("g_k", 1.2, "kN/m²")\n#eq("G_d", `1.35 * g_k`, unit: "kN/m²")'
    assert abs(_stored(body, "G_d") - 1.62) < 1e-9
    text = _printed('#report-level.update(3)\n' + body, "star_dot")
    assert "∗" not in text and "*" not in text, text
    assert "1.35 ⋅ 1.2 kN/m²" in text.replace("·", "⋅"), text
    assert "✔" in _printed('#var("a", 2, "kN", level: 0)\n#var("b", 5, "kN", level: 0)\n#verify(`2 * a <= b`)', "star_verify")


def test_var_label_and_descr_everywhere_it_may_stand():
    """«#eq, #var and #val should be able to take "label" and "descr" as an argument» -- they do, `#var` and `#eq` (`#val` was merged into `#var`, spec 2026-10-21-commandes-typst-refonte, REQ-009), at every level, each line's own label, description and citation its one footnote."""
    row = ('#var("a", 1, "kN", label: "La", descr: "Da")\n'
           '#eq("b", `a dot 2`, label: "Lb", descr: "Db")\n#var("a", label: "Lc", descr: "Dc")')
    three = _printed('#report-level.update(3)\n' + row, "row_label_descr_3")
    for word in ("La; Da", "Lb; Db", "Lc; Dc"):
        assert word in three, (word, three)
    two = _printed('#report-level.update(2)\n' + row, "row_label_descr_2")
    assert "La" in two and "Lb" in two and "Lc" in two and "Da" not in two and "Db" not in two, two
    assert "La" not in _printed('#report-level.update(1)\n' + row, "row_label_descr_1")


def test_var_is_inline_and_runs_on_in_one_paragraph():
    """«de base, #var doit s'afficher inline (afin de pouvoir afficher plusieurs var les uns après les autres). S'il y a deux retours à la ligne, alors ça fait un nouveau paragraphe» (v0.86).

    Consecutive calls share a line; a blank line starts another; a variable at level 0 leaves no space of its own behind; and the extras are one footnote, the label from level 2 -- there is no em dash inline.
    """
    lines = _lines('#report-level.update(2)\nA #var("b", 100, "mm")\n#var("h", 200, "mm", label: "Hoehe") B\n\nC #var("t", 24, "mm") D', "var_inline")
    assert any("A" in line and "100 mm" in line and "200 mm" in line and "B" in line for line in lines), lines
    assert not any("100 mm" in line and "24 mm" in line for line in lines), lines
    text = " ".join(lines)
    assert "Hoehe" in text and "— Hoehe" not in text, text
    same = _value('#context [#metadata(measure([A #var("x", 1, level: 0) B]).width == measure([A B]).width) <out>]')
    assert same is True


def test_eq_is_inline_by_default_and_follows_a_var_on_its_line():
    """Issue #19: «#eq s'imprime en ligne par défaut, comme #var depuis v0.87, de sorte qu'il peut suivre un #var sur la même ligne ; note: "line" garde la ligne à part». A sentence with a `#var` and an `#eq` in it is one line of the page; the same `#eq` with `note: "line"` takes lines of its own -- and a long level-3 formula, inline, still compiles on a narrow page."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")

    def lines(body, name):
        d = conftest.probe_dir(name)
        probe = d / "probe.typ"
        probe.write_text('#import "/000-Typst-Config/commands.typ": *\n#set page(width: 16cm, height: auto)\n' + body + "\n", encoding="utf-8")
        out = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")], capture_output=True, text=True, encoding="utf-8")
        assert out.returncode == 0, out.stderr
        from pypdf import PdfReader
        return [l for l in PdfReader(str(d / "probe.pdf")).pages[0].extract_text().splitlines() if l.strip()]

    sentence = 'Kraft #var("F", 5, "kN", level: 1) und #eq("M", `F * 2`, unit: "kN", level: 1%s) danach.'
    inline = lines(sentence % "", "eq_inline_lines")
    assert any("Kraft" in l and "danach" in l for l in inline), inline
    apart = lines('#calc-defaults(presets: "block", scope: "next")\n' + sentence % "", "eq_apart_lines")   # the block presets set the line apart (Q-014: note: "line" until then)
    assert not any("Kraft" in l and "danach" in l for l in apart), apart
    text = _printed('#report-level.update(3)\nKraft #var("F", 5, "kN") und #eq("M", `F * 2`, unit: "kN") danach.', "eq_inline")
    assert re.search(r"und \S+ = .* = 10\s*kN danach", text), text
    long = _printed('#set page(width: 9cm, height: auto)\n#report-level.update(3)\n#var("a_1", 1250.5, "mm", level: 0)\n#var("b_1", 3.75, "kN", level: 0)\nEs folgt #eq("c_1", `a_1 * b_1 + a_1 * b_1 / 2 + a_1 * b_1 / 3`, unit: "kNm").', "eq_inline_long")
    assert "kNm" in long, long


# --- `style:` (v0.100) ------------------------------------------------------

def _measure(expr, what="width"):
    """What Typst itself measures `expr` to be, in points -- the only way to see a *display* argument do anything."""
    return _value(f'#context [#metadata(measure({expr}).{what}.pt()) <out>]')


def test_a_style_sets_apart_the_whole_line_and_not_the_value():
    """The engineer's own answer when he asked for `#eq`'s `style:` on `#var`: «**R_k = 7 kN**», the whole expression and not the value alone.

    ⚠️ Measured with `underline` and not with `bold`, and that is what makes this check decisive rather than merely suggestive: underlining changes no glyph's width, so a styled line can only come out wider than a plain one if the `=` itself is **inside** the wrapper -- `apply-style` re-evaluates in math mode, and math sets its own spacing around a relation. A style that reached the value alone would leave the `=` outside it and the two widths equal.
    """
    plain = _measure('[#var("R_k", 7, "kN", level: 1)]')
    ruled = _measure('[#var("R_k", 7, "kN", level: 1, style: "underline")]')
    assert ruled > plain + 1, f"the styled line is {ruled} pt and the plain one {plain} pt -- the = is not inside the style"


def test_a_style_leaves_the_value_alone():
    """A display argument that moved a number would be the worst kind of defect here, so it is checked rather than assumed: the registry holds the same value, unit and symbol whether or not the line is set apart."""
    for style in ('none', '"bold"', '"underline"', '"double"'):
        body = f'#var("R_k", 7, "kN", level: 0, style: {style})'
        assert _stored(body, "R_k") == 7, style
        assert _stored(body, "R_k", "unit") == "kN", style
        assert _stored(body, "R_k", "symbol") == "R_k", style


def test_every_style_compiles_on_every_command_that_takes_one():
    """`style:` is on `var` and `eq` -- and not on `verify`, which carry no line of their own to set apart. Each is compiled, because `apply-style` evals a name into math and a command that passed its body the wrong way would fail only here."""
    for style in ('"bold"', '"underline"', '"double"'):
        for body in (
            f'#var("R_k", 7, "kN", style: {style})',
            f'#var("a", 2, "m", level: 0)\n#var("b", 3, "m", level: 0)\n#eq("A", `a dot b`, style: {style})',
            f'#var("R_d", 5, "kN", level: 0)\n#var("R_d", style: {style})',
        ):
            kind, got = _run(body + '\n#metadata(1) <out>')
            assert kind == "ok", f"style {style} on {body.splitlines()[-1]}: {got}"


def test_a_double_rule_is_drawn_under_the_line():
    """`"double"` is `verify`'s own mark -- two nested boxes, each with a bottom rule -- for a value a section rests on. It draws ink below the line, so the line is taller; `"bold"` and `"underline"` are not, which is what tells the three apart."""
    plain = _measure('[#var("R_k", 7, "kN", level: 1)]', "height")
    ruled = _measure('[#var("R_k", 7, "kN", level: 1, style: "double")]', "height")
    assert ruled > plain, f"the double rule adds no height: {ruled} pt against {plain} pt"


def test_a_style_that_is_no_math_function_is_refused_naming_it():
    """`style:` is a math function's name -- `#eq`'s contract since v0.85, which is why it is not kept to a list -- so an unknown one is refused by Typst itself, and what matters is that the message names what was asked for rather than failing somewhere unrecognisable."""
    message = _error('#var("R_k", 7, "kN", style: "zork")')
    assert "zork" in message, message


# --- a literal checked by domain:, own:, verify's id:, var-domain's gen: (spec 2026-10-15-calculs-deplies-balises-figures-natives) ---

def test_a_value_beside_a_pair_is_the_one_stored_and_keeps_the_export_s_provenance():
    """REQ-001: `#var(key, value, unit, domain: pair)` was refused until 2026-10-15; it is now a literal checked by the export. The value written is the one stored -- the engineer reads it in the file -- and the export's symbol, label, citation and `source` stay with it."""
    rec = _stored('#var("s_k", 1.5, "kN/m²", domain: ("snow-load", "SL"))', "s_k", field="source")
    assert rec == "python:domains/snow_source.py", rec   # computed by Woodcore from the sheet's inputs since v0.120 (spec 2026-10-21-restes-issue-69)
    assert _stored('#var("s_k", 1.5, "kN/m²", domain: ("snow-load", "SL"))', "s_k") == 1.5
    assert _stored('#var("s_k", 1.5, "kN/m²", domain: ("snow-load", "SL"))', "s_k", field="norm") == "SIA 261"


def test_a_literal_agreeing_with_the_export_is_not_stale_and_one_that_differs_is():
    """REQ-001: the comparison is made after converting the export's value into the written unit, at a relative 1e-6 (`literal-tolerance`), or within half the last decimal written where that stays under a relative 1e-3 (`literal-rounding`) -- found on the first build, whose documentation example printed «1.394 kN/m² (stale: 1.394 kN/m²)» for an export of 1.39411547558108; a value of another dimension is stale in its own unit."""
    assert _value('#metadata(literal-stale((value: 7000, unit: "N"), (value: 7, unit: "kN"))) <out>') is None
    assert _value('#metadata(literal-stale((value: 25, unit: "kN"), (value: 28, unit: "kN"))) <out>') == {"value": 28, "unit": "kN"}
    assert _value('#metadata(literal-stale((value: 25, unit: "kN"), (value: 28, unit: "kNm"))) <out>') == {"value": 28, "unit": "kNm"}
    exact = _value('#metadata(find-calculation("t", "snow-load", "SL").vars.s_k.value) <out>')
    assert _value(f'#metadata(literal-stale((value: {exact!r}, unit: "kN/m²"), find-calculation("t", "snow-load", "SL").vars.s_k)) <out>') is None
    assert _value('#metadata(literal-stale((value: 1.5, unit: "kN/m²"), find-calculation("t", "snow-load", "SL").vars.s_k)) <out>') is not None
    # a value typed to the decimals it is printed at agrees (`literal-rounding`), half a unit on a whole number does not
    assert _value('#metadata(literal-stale((value: 1.394, unit: "kN/m²"), find-calculation("t", "snow-load", "SL").vars.s_k)) <out>') is None
    assert _value('#metadata(literal-stale((value: 25, unit: "kN"), (value: 25.4, unit: "kN"))) <out>') == {"value": 25.4, "unit": "kN"}


def test_a_literal_beside_a_var_domain_is_checked_against_what_the_domain_held():
    """REQ-001, the string form of `domain:`: the value the var-domain holds is read before the literal is stored, and a name it does not declare is refused as before."""
    assert _stored('#domain("A")[#var("F", 7, "kN")]\n#var("F", 7000, "N", domain: "A")', "F") == 7000
    assert _stored('#domain("A")[#var("F", 7, "kN")]\n#var("F", 8, "kN", domain: "A")', "F", field="checked_against.value") == 7
    assert "declares no" in _error('#domain("A")[#var("F", 7, "kN")]\n#var("G", 8, "kN", domain: "A")')


def test_a_stale_value_compiles_in_the_three_languages():
    """UI-004: the red «stale» note is the glossary's (`formula.stale`) in each language; the page compiles inline and set apart by the block presets."""
    for lang in ("de", "fr", "en"):
        assert _value(f'#set text(lang: "{lang}")\n#var("s_k", 1.5, "kN/m²", domain: ("snow-load", "SL"))\n'
                      '#calc-defaults(presets: "block", scope: "next")\n'
                      '#var("s_k", 1.5, "kN/m²", domain: ("snow-load", "SL"))\n#metadata(1) <out>') == 1


def test_a_verify_id_is_once_per_domain():
    """REQ-005: `#verify(..., id:)` names a relation; the same id twice in one domain stops the compile, the same id in two domains does not."""
    assert _value('#var("a", 1)\n#domain("X")[#verify(`a <= 2`, id: "v")]#domain("Y")[#verify(`a <= 2`, id: "v")]\n#metadata(1) <out>') == 1
    message = _error('#var("a", 1)\n#domain("X")[#verify(`a <= 2`, id: "v")#verify(`a <= 3`, id: "v")]')
    assert '"v"' in message and '"X"' in message, message
    assert "non-empty" in _error('#var("a", 1)\n#verify(`a <= 2`, id: "")')


def test_a_citation_is_grey_and_takes_no_section_sign():
    """The engineer, 20.10.2026: «Les normes affichées en ligne doivent être écrites en gris, afin de moins attirer le regard. Il ne doit pas y avoir de "§" avant le norm-ref» (spec 2026-10-21-commandes-typst-refonte, UI-001).

    The grey is the palette's `ink-soft`, read from lib/figure-palette.json and written nowhere else; the column, a citation on its line and one in a sentence (`cite-norm`) take it alike.
    """
    palette = json.loads((ROOT / "lib" / "figure-palette.json").read_text(encoding="utf-8"))
    grey = palette["colours"]["ink-soft"]
    # the fill the clause is set in: read by a show rule, since a style is not in a value's repr
    probe = '#show text.where(text: "4.2.1"): it => context [#metadata(repr(text.fill)) <out>]\n'
    for call in ('note-cell((norm: "SIA 265", norm_ref: "4.2.1"))', 'note-on-line((norm: "SIA 265", norm_ref: "4.2.1"))', 'cite-norm(norm: "SIA 265", norm-ref: "4.2.1")'):
        assert _value(probe + "#" + call) == f'rgb("{grey}")', call
        shown = _value(f'#metadata(repr({call})) <out>')
        assert "§" not in shown, (call, shown)
