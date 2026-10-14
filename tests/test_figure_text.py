"""A text placed on a drawing, and the variables it prints (calc/domains/figure_text.py, spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, lot 3, REQ-011, D-09, D-13).

What is held:

* **the token text** (D-13): `{1}` names a variable of `vars`, `{{` and `}}` are literal braces; a token naming none and a brace standing alone are refused naming the text;
* **what it prints** (REQ-011, D-09): «value» prints the variable's value and unit, «symbol» its symbol as a figure sets it, `=`, then the value; the value after factor and offset, as a figure prints a number;
* **live, and never a stop** (D-06): a variable gone prints its `last` with a warning; `refresh` writes the last value, and keeps it where the variable cannot be read;
* **the symbol** (ARCH-006): `typst_math` reads a symbol once, and sets it as the window's HTML and as a figure's text; every symbol of the example project is read the same way by both;
* **the drawing**: the lines are set by svg_text, one <text> per run, subscripts smaller.
"""

import json

import conftest

import typst_math
import validation
from domains import figure_style, figure_text, links

VALUES = links.index({"domains": {
    "snow-load": {"instances": {"SL": {"vars": {"F": {"value": 12500, "unit": "N", "symbol": "F_(d,\"max\")"},
                                                "k": {"value": "A1", "unit": ""}}}}},
}}, formulas={"poutre": {"M_d": {"value": -14.06254, "unit": "kNm", "symbol": "M_d"}}})


def _fail(message):
    raise validation.ValidationError(message)


def _refused(entry, *words):
    try:
        figure_text.check(entry, _fail, "text T1")
    except validation.ValidationError as exc:
        for word in words:
            assert word in str(exc), f"the refusal {exc} does not name {word!r}"
        return
    raise AssertionError("accepted")


def test_a_token_text_is_cut_into_text_and_tokens():
    assert figure_text.pieces("N = {1} kN") == [("text", "N = "), ("var", "1"), ("text", " kN")]
    assert figure_text.pieces("{{a}} {1}") == [("text", "{a} "), ("var", "1")]
    assert figure_text.tokens("{2} {1} {2}") == ["2", "1"]
    assert figure_text.escape("a{b}") == "a{{b}}"


def test_a_token_naming_no_variable_and_a_lone_brace_are_refused():
    _refused({"text": "N = {1}"}, "text T1", "{1}")
    _refused({"text": "N = {1", "vars": {}}, "brace")
    _refused({"text": "{1}", "vars": {"1": {"domain": "snow-load", "instance": "SL", "var": "F", "show": "both"}}}, "show")
    _refused({"text": "{1}", "vars": {"1": {"domain": "snow-load", "var": "F"}}}, "instance")
    figure_text.check({"text": "{{ {1} }}", "vars": {"1": {"domain": "snow-load", "instance": "SL", "var": "F", "show": "symbol",
                                                            "last": {"value": 1, "unit": "kN", "symbol": "F"}}}}, _fail, "text T1")


def test_a_variable_prints_its_value_or_its_symbol_and_value():
    entry = {"text": "N = "}
    figure_text.insert(entry, links.make("snow-load", "SL", "F", factor=2))
    assert entry["text"] == "N = {1}"
    assert figure_text.lines(entry, VALUES) == ["N = 25000 N"]
    entry["vars"]["1"]["show"] = "symbol"
    assert figure_text.lines(entry, VALUES) == ["N = F_(d,max) = 25000 N"]
    # a «Formule» domain, a negative value with the real minus and three decimals, two lines
    key = figure_text.insert(entry, links.make("formulas", "poutre", "M_d", origin="formulas"), show="value")
    entry["text"] = entry["text"].replace("{" + key + "}", "\nM = {" + key + "}")
    assert figure_text.lines(entry, VALUES) == ["N = F_(d,max) = 25000 N", "M = −14.063 kNm"]


def test_a_variable_gone_prints_its_last_value_with_a_warning():
    entry = {"text": ""}
    figure_text.insert(entry, links.make("snow-load", "SL", "F"), show="symbol")
    figure_text.refresh(entry, VALUES)
    assert entry["vars"]["1"]["last"] == {"value": 12500, "unit": "N", "symbol": "F_(d,\"max\")"}
    gone = links.index({"domains": {}})
    printed, provenance, notes = figure_text.resolve(entry, gone, "schema S1, text T1")
    assert printed == ["F_(d,max) = 12500 N"]
    assert provenance[0]["stale"] and notes and notes[0].code == "text_stale" and "schema S1" in notes[0]
    figure_text.refresh(entry, gone)
    assert entry["vars"]["1"]["last"]["value"] == 12500
    # a variable with no last value and none to read prints `?`
    assert figure_text.lines({"text": "{1}", "vars": {"1": {"domain": "x", "instance": "y", "var": "z"}}}, gone) == ["?"]


def test_a_variable_removed_takes_its_token_with_it_and_unused_ones_are_dropped():
    entry = {"text": "a {1} b"}
    key = figure_text.insert(entry, links.make("snow-load", "SL", "F"), at=2)
    assert key == "2" and entry["text"] == "a {2}{1} b"
    entry["vars"]["1"] = dict(entry["vars"]["2"])
    figure_text.remove_var(entry, "1")
    assert entry["text"] == "a {2} b" and list(entry["vars"]) == ["2"]
    entry = {"text": "x", "vars": {"9": {"domain": "a", "instance": "b", "var": "c"}}}
    figure_text.drop_unused(entry)
    assert "vars" not in entry


def test_a_text_states_only_its_text_factor():
    for kind in ("schema", "statics", "plan", "fire"):
        assert figure_style.allowed(kind, "texts") == ("text",)


def test_the_drawing_sets_each_line_with_its_subscripts():
    out = []
    figure_text.draw(out, (10.0, 20.0), ["q_k = 2 kN", "", "b"], 4.0, "#000000")
    assert sum(line.startswith("<text") for line in out) == 4   # q, k (subscript), " = 2 kN", b
    assert 'font-size="2.88"' in "".join(out)                   # the subscript at 0.72 of the size


def test_a_symbol_reads_the_same_in_the_window_and_on_a_figure():
    assert typst_math.to_figure('q_(k,"max")') == "q_(k,max)"
    assert typst_math.to_figure("f_(h,alpha,k)") == "f_(h,α,k)"
    assert typst_math.to_html("f_(h,alpha,k)") == "f<sub>h,α,k</sub>"
    data = json.loads((conftest.SAMPLE.parent / "_woodcore" / "data" / "calculations.json").read_text(encoding="utf-8"))
    symbols = {var.get("symbol") for d in data["domains"].values() for i in d["instances"].values() if isinstance(i, dict)
               for var in (i.get("vars") or {}).values() if isinstance(var, dict) and var.get("symbol")}
    assert len(symbols) > 20
    for symbol in symbols:
        html, figure = typst_math.to_html(symbol), typst_math.to_figure(symbol)
        # the same letters, in the same order: the HTML's tags and the figure's subscript marks taken off
        plain = html.replace("<sub>", "").replace("</sub>", "").replace("<sup>", "^").replace("</sup>", "")
        plain = plain.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        assert plain == figure.replace("_(", "").replace(")", "").replace("(", "") or \
            plain.replace("(", "").replace(")", "") == figure.replace("_(", "").replace("(", "").replace(")", ""), symbol
