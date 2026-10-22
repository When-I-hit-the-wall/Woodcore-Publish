"""The defects the v0.86 review of every command found, each held by the check that showed it (docs/typst/command-docs.md §10sexies).

Three probes went through the 64 public commands of lib/, argument by argument and level by level, against the frozen examples; what they found that was a defect in the engine -- a crash, a value stored without its unit, an argument read and ignored, a message sending the reader to an argument that does not exist -- was repaired, and is held here. What they found that is a question for the engineer is in CHANGELOG.md's v0.86 entry, not here.

Each test compiles against the example project the suite works on (conftest), through the report's own `commands.typ`.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import re
import subprocess

import conftest
from conftest import Skip

TYPST_ROOT = conftest.TYPST_ROOT


def _compile(body, name):
    """Compiles `body`; returns (ok, stderr, text of the PDF with its whitespace collapsed)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        return False, out.stderr, ""
    from pypdf import PdfReader
    raw = "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
    return True, "", raw


def _printed(body, name):
    ok, err, raw = _compile(body, name)
    assert ok, err
    return re.sub(r"\s+", " ", raw)


def _refused(body, name):
    ok, err, _raw = _compile(body, name)
    assert not ok, f"expected a refusal, and it compiled:\n{body}"
    return err


def _query(body, name):
    """The value `body` puts in `metadata(...) <out>`."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "query", "--root", str(TYPST_ROOT), str(probe), "<out>", "--field", "value", "--one"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def _stored(body, key, field, name):
    return _query(body + f'\n#context [#metadata(var-lookup(var-registry.get(), "{key}").at("{field}", default: none)) <out>]', name)


# --- verify ------------------------------------------------------------------

def test_verify_reads_the_relations_written_as_symbols():
    """`≤`, `≥` and `≠` are documented and were sliced mid-character: the operator's length was counted in clusters where `slice` counts bytes, and every relation written with one died on «string index 6 is not a character boundary»."""
    decl = '#var("F_Ed", 2, "kN", level: 0)\n#var("R_d", 5, "kN", level: 0)\n'
    for relation in ("F_Ed ≤ R_d", "R_d ≥ F_Ed", "F_Ed ≠ R_d"):
        ok, err, _ = _compile(decl + f'#verify("{relation}", level: 1)', "review_verify_symbols")
        assert ok, f"{relation}: {err}"


def test_verify_does_not_send_the_reader_to_value():
    """An unknown name in a relation named `value:` as a way out, which is eq's argument: `#verify(..., value: true)` is refused."""
    err = _refused('#verify(`X_unknown <= 1`)', "review_verify_value")
    message = conftest.panic_message(err)  # the message alone: the stderr also quotes the engine's source, whose `value:` clause is the very thing this holds out of verify's message
    assert message is not None and "X_unknown" in message and "value:" not in message, err


# --- eq --------------------------------------------------------------------------

def test_eq_substitutes_every_operand_once_at_level_3():
    """The keys were substituted one after the other, so `N` rewrote the «N» of the «21 N/mm²» `f_c` had just become, and level 3 -- the checking report alone -- died on «unknown variable: kN»."""
    body = ('#var("N", 12, "kN", level: 0)\n#var("A", 14000, "mm²", level: 0)\n#var("f_c", 21, "N/mm²", level: 0)\n'
            '#eq("eta", `N / (A dot f_c)`, level: 3)')
    text = _printed(body, "review_eq_cascade")
    assert "21" in text and "14000" in text, text
    assert abs(_stored(body, "eta", "value", "review_eq_cascade_q") - 12000 / (14000 * 21)) < 1e-9


def test_eq_given_its_value_keeps_the_formulas_unit():
    """`value:` stored the answer with no unit at all, so a force given that way compared with a resistance as «1 with N»."""
    body = ('#var("M_Ed", 0.275, "kNm", level: 0)\n#var("a", 135, "mm", level: 0)\n'
            '#eq("F_Ed", `M_Ed / a`, value: 2.037037037037037, level: 0)')
    assert _stored(body, "F_Ed", "unit", "review_eq_value") == "kN"
    ok, err, _ = _compile(body + '\n#var("R_d", 4.969, "kN", level: 0)\n#verify(`F_Ed <= R_d`)', "review_eq_value_verify")
    assert ok, err


def test_a_fractional_power_of_a_dimension_is_refused_by_name():
    """SIA 265 (87) raises d to 2.6, which leaves mm^2.6: it crashed in the display with «dictionary does not contain key "."», and says now what to write. A plain number raised to 2.6 is still computed."""
    err = _refused('#var("d", 10, "mm", level: 0)\n#eq("M_uk", `0.3 dot d^2.6`)', "review_eq_fraction")
    assert "has no unit" in err and "value:" in err, err
    got = _stored('#var("d_n", 10, level: 0)\n#eq("y", `0.3 dot d_n^2.6`, level: 0)', "y", "value", "review_eq_fraction_ok")
    assert abs(got - 0.3 * 10 ** 2.6) < 1e-6, got


def test_the_inverse_functions_evaluate_and_print_under_both_spellings():
    """`atan` evaluated and could not be printed, `arctan` printed and could not be evaluated."""
    for fn in ("arctan", "atan", "arcsin", "asin"):
        body = f'#var("x", 0.5, level: 0)\n#eq("phi", `{fn}(x)`, level: 3)'
        ok, err, _ = _compile(body, "review_eq_inverse")
        assert ok, f"{fn}: {err}"


# --- var and val -----------------------------------------------------------------

def test_norm_ref_alone_overrides_the_clause():
    """`norm-ref:` was read only beside a `norm:`, so the export's own clause was printed whatever was asked."""
    text = _printed('#var("ce", domain: ("snow-load", "SL"), norm-ref: "9.9.9", level: 3)\n'
                    'Satz #var("ce", domain: ("snow-load", "SL"), norm-ref: "8.8.8", level: 3).', "review_norm_ref")
    assert "9.9.9" in text and "8.8.8" in text, text


def test_var_keeps_the_choices_its_value_carries():
    """`val` footnoted C_e's three choices and `var` of the same value did not: var-record dropped them."""
    choices = _stored('#var("ce", domain: ("snow-load", "SL"), level: 0)', "ce", "choices", "review_var_choices")
    assert choices and len(choices) >= 2, choices


# --- the display commands -----------------------------------------------------------

def test_a_symbol_that_is_a_word_prints_outside_context():
    """render-symbol read the report's language for a symbol that is a word («Dachform») and failed in plain markup."""
    ok, err, _ = _compile('#render-symbol((symbol: "\\"Dachform\\""))', "review_render_symbol")
    assert ok, err


def test_a_report_level_outside_one_to_three_is_refused():
    """`report-level.update(0)` hid every #var while show-calc went on printing, and `update(4)` printed level 3 without a word."""
    for bad in ("0", "4"):
        err = _refused(f'#report-level.update({bad})\n#var("ce", domain: ("snow-load", "SL"))', "review_report_level")
        assert "report level is " + bad in err, err
    ok, err, _ = _compile('#report-level.update(3)\n#var("x", 1, level: 0)\n#var("ce", domain: ("snow-load", "SL"))', "review_report_level_ok")
    assert ok, err


def test_a_number_and_its_unit_do_not_part():
    """fmt-number joined them with a plain space, so a line could end on «Q_k = 20» and the next begin with «kN»."""
    ok, err, raw = _compile('#fmt-number(4.969, "kN")', "review_nbsp")
    assert ok, err
    assert "4.969 kN" in raw or "4.969 kN" not in raw, repr(raw)


def test_a_language_is_refused_with_the_list_of_the_valid_ones():
    """set-report-language(1) failed on «cannot add string and integer» -- its message was built before the check -- and tl-of("it", …) crashed on a word the glossary knew."""
    err = _refused('#set-report-language(1)', "review_lang_number")
    assert "no language 1" in err and "de, fr, en" in err, err
    err = _refused('#tl-of("it", "Schneelast")', "review_lang_tl")
    assert "no language" in err and "de, fr, en" in err, err
