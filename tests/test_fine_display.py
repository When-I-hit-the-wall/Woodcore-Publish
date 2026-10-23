"""The fine display arguments of `#var`, `#eq` and `#verify`, the level as a preset of them, `#unit`'s scope, `#calc-defaults` and `#domain` (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-001 to REQ-008, ARCH-001, Q-001, Q-005, Q-011, D-9, D-12).

The engineer's words (20.10.2026): «Les niveaux sont remplacés par un réglage fin de tous les paramètres», and a level written gives the fine arguments it presets, an argument written winning over it (REQ-007). What is held here, each by compiling Typst and reading the page or the registry back:

* every fine argument takes the values the engineer listed and refuses any other, naming the argument and the values;
* the order of the layers -- the line's argument, its level, `#calc-defaults` of the domain, the domain's level, `#calc-defaults` of the document, the document's level -- and `--input uniform` over all;
* `#var` without a value prints a variable again with what it was declared with, and `unit:` converts it for that line alone;
* `#eq`'s two displays, `unit:` and `as-unit:`; `#verify`'s ratio under a name, and its citation;
* `#unit` reaching the next answer of its dimension, the domain or the document;
* `#domain`'s heading, its level and its footnote, printed once.

lib/display-presets.json is held complete here, and equal to the table docs/typst/formulas.md shows of it.

⚠️ Skipped where `typst` is not on the path.
"""

import json
import re
import subprocess
import unicodedata

import conftest
from conftest import ROOT, Skip

TYPST_ROOT = conftest.TYPST_ROOT
PRESETS = ROOT / "lib" / "display-presets.json"


def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _compile(name, body, inputs=()):
    """(error or None, the PDF's text with its whitespace collapsed) of `body` under the report's own commands."""
    _guard()
    d = conftest.probe_dir("fine_" + name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    args = ["typst", "compile", "--root", str(TYPST_ROOT)]
    for key, value in inputs:
        args += ["--input", f"{key}={value}"]
    out = subprocess.run(args + [str(probe), str(d / "probe.pdf")], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        return (conftest.panic_message(out.stderr) or out.stderr), ""
    from pypdf import PdfReader
    raw = "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
    # math sets its letters in the mathematical alphabets (𝑅, 𝜂): read back as the letters they are
    return None, re.sub(r"\s+", " ", unicodedata.normalize("NFKC", raw))


def _text(name, body, inputs=()):
    error, text = _compile(name, body, inputs)
    assert error is None, error
    return text


def _refused(name, body):
    error, _text = _compile(name, body)
    assert error is not None, "expected a refusal"
    return error


def _query(body, tag="out"):
    _guard()
    d = conftest.probe_dir("fine_query")
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "query", "--root", str(TYPST_ROOT), str(probe), f"<{tag}>", "--field", "value", "--one"],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


# --- the presets ------------------------------------------------------------------

def test_every_level_presets_every_fine_argument_of_its_command():
    """lib/display-presets.json: four levels for each command, each giving every fine argument the command takes a value it accepts (ARCH-001)."""
    data = json.loads(PRESETS.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.2"   # 1.2: fine-values and fine-keys moved here from lib/formula.typ (spec 2026-10-22-onglet-neige-type, D-17)
    keys = {
        "var": {"display", "label-position", "descr-position", "norm-position"},
        "eq": {"display-formula", "display-equation", "label-position", "descr-position", "norm-position"},
        "verify": {"display", "label-position", "descr-position", "norm-position"},
        "domain": {"label-position", "descr-position", "norm-position"},
    }
    display = {"none", "variable", "value", "value-unit", "variable-value-unit"}
    values = {"display": display, "display-formula": display, "display-equation": display,
              "label-position": {"none", "before", "after", "footnote"}, "descr-position": {"none", "after", "footnote"},
              "norm-position": {"none", "in-line", "line-right", "footnote"}}
    for family in ("commands", "block"):   # the default family, `inline`, and `block` (Q-014)
        assert set(data[family]) == set(keys), family
        for command, levels in data[family].items():
            assert set(levels) == {"0", "1", "2", "3"}, (family, command)
            for level, preset in levels.items():
                assert set(preset) == keys[command], (family, command, level)
                assert all(preset[k] in values[k] for k in preset), (family, command, level, preset)
    # `block` shows what `inline` shows at each level, and puts it after the line and in the right-hand column
    for command in ("var", "eq", "verify"):
        for level, preset in data["commands"][command].items():
            block = data["block"][command][level]
            assert (block["label-position"] == "none") == (preset["label-position"] == "none") and (block["norm-position"] == "none") == (preset["norm-position"] == "none"), (command, level)
            assert block["label-position"] in ("none", "after") and block["norm-position"] in ("none", "line-right"), (command, level)
    # level 0 prints nothing of a line, as it always has
    for command in ("var", "verify"):
        assert data["commands"][command]["0"]["display"] == "none"
    assert data["commands"]["eq"]["0"]["display-formula"] == "none" == data["commands"]["eq"]["0"]["display-equation"]


def test_the_presets_are_the_table_the_documentation_shows():
    """docs/typst/formulas.md shows lib/display-presets.json as a table, row for row: the two cannot part without this failing."""
    data = json.loads(PRESETS.read_text(encoding="utf-8"))
    doc = (ROOT / "docs" / "typst" / "formulas.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| `(var|eq|verify|domain)` \| (inline|block) \| (\d) \| (.+?) \|$", doc, re.M)
    shown = {(command, family, level): [cell.strip().strip("`") for cell in rest.split(" | ")] for command, family, level, rest in rows}
    for family, levels_of in (("inline", data["commands"]), ("block", data["block"])):
      for command, levels in levels_of.items():
        for level, preset in levels.items():
            command_key = (command, family, level)
            cells = shown.get(command_key)
            assert cells is not None, f"docs/typst/formulas.md has no row for {command} ({family}) at level {level}"
            for key in ("display", "display-formula", "display-equation", "label-position", "descr-position", "norm-position"):
                expected = preset.get(key, "—")
                column = ("display", "display-formula", "display-equation", "label-position", "descr-position", "norm-position").index(key)
                assert cells[column] == expected, (command, level, key, cells[column], expected)


# --- the values a fine argument takes ----------------------------------------------

def test_a_value_out_of_its_list_is_refused_naming_the_argument_and_the_values():
    for call, name in (
        ('#var("a", 1, display: "all")', "display"),
        ('#var("a", 1, label-position: "left")', "label-position"),
        ('#var("a", 1, descr-position: "before")', "descr-position"),
        ('#var("a", 1, norm-position: "margin")', "norm-position"),
        ('#var("a", 1, style: "italic")', "style"),
        ('#var("a", 1, role: "input")', "role"),
        ('#var("a", 1)\n#eq("b", `a`, display-formula: "letters")', "display-formula"),
        ('#var("a", 1)\n#verify(`a <= 2`, display: "value")', "display"),
    ):
        message = _refused("refuse", call)
        assert name in message and "is not one of" in message, (call, message)


# --- the order of the layers -------------------------------------------------------

def test_an_argument_written_wins_over_the_level_written():
    """REQ-007: `level: 3` presets the citation in the footnote, and `norm-position: "none"` written beside it wins."""
    with_norm = _text("level3", '#var("g", 1.7, norm: "SIA 265", norm-section: "2.2.5", level: 3)')
    assert "SIA 265 2.2.5" in with_norm, with_norm
    without = _text("level3_none", '#var("g", 1.7, norm: "SIA 265", norm-section: "2.2.5", level: 3, norm-position: "none")')
    assert "SIA 265" not in without, without


def test_a_domain_level_reaches_its_lines_but_a_line_s_own_level_wins():
    text = _text("domain_level", '#domain("p", level: 3)[\n#var("a", 1, label: "Erste", norm: "SIA 265", norm-section: "1.1")\n#var("b", 2, label: "Zweite", norm: "SIA 265", norm-section: "2.2", level: 1)\n]')
    assert "Erste" in text and "SIA 265 1.1" in text, text
    assert "Zweite" not in text and "SIA 265 2.2" not in text, text


def test_calc_defaults_of_the_domain_reach_its_lines_and_end_with_it():
    body = ('#domain("p")[\n#calc-defaults(norm-position: "in-line", label-position: "before", scope: "domain")\n'
            '#var("a", 1, label: "Erste", norm: "SIA 265", norm-section: "1.1")\n]\n'
            '#var("b", 2, label: "Zweite", norm: "SIA 265", norm-section: "2.2")')
    text = _text("defaults_domain", body)
    assert "Erste: a = 1 SIA 265 1.1" in text, text
    assert "Zweite" not in text and "SIA 265 2.2" not in text, "the defaults end with their domain, and level 1 shows neither"


def test_calc_defaults_for_the_next_line_reach_that_line_alone():
    body = ('#calc-defaults(label-position: "after", scope: "next")\n#var("a", 1, label: "Erste")\n#var("b", 2, label: "Zweite")')
    text = _text("defaults_next", body)
    assert "a = 1 — Erste" in text and "Zweite" not in text, text


def test_a_level_given_to_the_line_wins_over_calc_defaults():
    body = '#calc-defaults(norm-position: "in-line", scope: "document")\n#var("g", 1.3, norm: "SIA 260", norm-section: "4.4", level: 1)'
    assert "SIA 260" not in _text("defaults_level", body)


def test_the_uniform_level_overrides_the_arguments_written():
    """Q-005: a uniform report is one level throughout, the fine arguments written included."""
    body = '#var("g", 1.7, label: "Teil", label-position: "after", norm: "SIA 265", norm-section: "2.2.5", norm-position: "in-line")'
    assert "Teil" in _text("written", body) and "SIA 265 2.2.5" in _text("written", body)
    uniform = _text("uniform", '#uniform-level.update(1)\n' + body)
    assert "Teil" not in uniform and "SIA 265" not in uniform, uniform


# --- #var -------------------------------------------------------------------------------

def test_a_variable_without_a_value_is_printed_again_with_what_it_was_declared_with():
    """REQ-002, Q-011: «#var("R_d", "N") reprendrait tous les arguments donnés initialement … en changeant uniquement les unités» -- written `unit: "N"`, for that line alone."""
    body = ('#var("R_d", 5, "kN", label: "Widerstand", label-position: "after", level: 0)\n'
            'A #var("R_d") B #var("R_d", unit: "N") C\n'
            '#context [#metadata(var-lookup(var-registry.get(), "R_d")) <out>]')
    text = _text("again", body)
    assert "Rd = 5 kN — Widerstand B Rd = 5000 N — Widerstand C" in text, text
    held = _query(body)
    assert held["value"] == 5 and held["unit"] == "kN", "the registry keeps the unit it was declared in"
    message = _refused("again_unknown", '#var("Q_x")')
    assert "no variable named" in message and "Q_x" in message, message


def test_the_name_symbol_value_and_unit_may_be_written_by_name():
    text = _text("named", '#var(name-calc: "l_1", name-visible: "l", value: 5, unit: "m")\n#eq("A", `l_1 * 2`)')
    assert "l = 5 m" in text, text
    assert "twice" in _refused("named_twice", '#var("a", "x", 1, name-visible: "y")')


def test_display_keeps_what_it_names_of_the_line():
    for display, shown, hidden in (("variable", "k ", "0.8"), ("value", "0.8", "k ="), ("value-unit", "0.8 m", "k ="), ("variable-value-unit", "k = 0.8 m", None)):
        text = _text("display_" + display.replace("-", "_"), f'X #var("k", 0.8, "m", display: "{display}") Y')
        assert shown in text, (display, text)
        if hidden is not None:
            assert hidden not in text, (display, text)


# --- #eq --------------------------------------------------------------------------------

def test_the_two_displays_of_eq_print_the_four_forms_of_the_engineer_s_page():
    """Q-001: «display-formula» the formula, «display-equation» the name and the answer -- the result alone, the formula alone, the formula and the result without the numbers, all of it."""
    head = '#var("N_d", 50, "kN", level: 0)\n#var("A", 56000, "mm²", level: 0)\n'
    alone = _text("eq_result", head + 'X #eq("s", `N_d / A`, display-formula: "none", display-equation: "variable-value-unit") Y')
    assert "X s = 0.893 N/mm2 Y" in alone, alone
    formula = _text("eq_formula", head + 'X #eq("s", `N_d / A`, display-formula: "variable", display-equation: "variable") Y')
    assert "0.893" not in formula and "Nd" in formula, formula
    full = _text("eq_full", head + 'X #eq("s", `N_d / A`, display-formula: "variable-value-unit", display-equation: "variable-value-unit") Y')
    assert "50 kN" in full and "56000 mm2" in full and "0.893 N/mm2" in full, full
    bare = _text("eq_bare", head + 'X #eq("s", `N_d / A`, display-formula: "value", display-equation: "value") Y')
    assert "50" in bare and "kN" not in bare and "0.893" in bare and "N/mm" not in bare, bare


def test_unit_converts_and_as_unit_keeps_the_number():
    """REQ-003, T37: «un qui est unit et un qui est as unit. Le as unit permet de modifier l'unité.»"""
    head = '#var("M_d", 4.2, "kNm", level: 0)\n'
    converted = _query(head + '#eq("M", `M_d`, unit: "Nmm", level: 0)\n#context [#metadata(var-lookup(var-registry.get(), "M")) <out>]')
    assert abs(converted["value"] - 4.2e6) < 1e-6 and converted["unit"] == "Nmm", converted
    given = _query(head + '#eq("q", `M_d / (100 "mm")`, as-unit: "kN/m", level: 0)\n#context [#metadata(var-lookup(var-registry.get(), "q")) <out>]')
    assert given["unit"] == "kN/m" and given["as_unit_from"] not in (None, "kN/m"), given
    assert "write one of the two" in _refused("as_unit_both", head + '#eq("q", `M_d`, unit: "kNm", as-unit: "kN")')


# --- #verify ----------------------------------------------------------------------------

def test_verify_keeps_its_ratio_under_a_name_and_prints_it_under_another():
    """REQ-004, D-12: name-calc keeps the left over the right for <=, the right over the left for >=; name-visible prints the relation as that ratio against 1."""
    head = '#var("s", 0.893, "N/mm²", level: 0)\n#var("f", 1.187, "N/mm²", level: 0)\n'
    kept = _query(head + '#verify(`s <= f`, name-calc: "eta", level: 0)\n#context [#metadata(var-lookup(var-registry.get(), "eta").value) <out>]')
    assert abs(kept - 0.893 / 1.187) < 1e-9, kept
    turned = _query(head + '#verify(`f >= s`, name-calc: "eta", level: 0)\n#context [#metadata(var-lookup(var-registry.get(), "eta").value) <out>]')
    assert abs(turned - 0.893 / 1.187) < 1e-9, turned
    text = _text("verify_named", head + '#verify(`s <= f`, name-visible: "eta", display: "variable-value-unit")')
    assert "η" in text and "0.752" in text and "1" in text, text
    assert "equality" in _refused("verify_equal", head + '#verify(`s = f`, name-calc: "eta")')


def test_verify_cites_its_norm_and_registers_it():
    head = '#var("s", 0.893, "N/mm²", level: 0)\n#var("f", 1.187, "N/mm²", level: 0)\n'
    text = _text("verify_norm", head + '#verify(`s <= f`, label: "Zug", label-position: "after", norm: "SIA 265", norm-section: "4.2.1", norm-position: "line-right")\n#show-bibliography(data: false)')
    assert "Zug" in text and "SIA 265 4.2.1" in text and "SIA 265" in text.split("4.2.1", 1)[1], text


def test_an_id_names_one_line_of_the_three_commands_together():
    message = _refused("id_twice", '#var("a", 1, id: "x")\n#eq("b", `a`, id: "x")')
    assert "two lines" in message and "x" in message, message


# --- #unit --------------------------------------------------------------------------------

def test_unit_reaches_the_next_answer_of_its_dimension_and_no_further_by_default():
    """REQ-005, T14: «uniquement pour le prochain affichage (var ou eq), pour tout le reste du domain, pour tout le reste du document» -- the next answer of its dimension, a line of another dimension between them taking nothing of it."""
    head = '#var("F", 5, "kN", level: 0)\n#var("l", 2, "m", level: 0)\n'
    text = _text("unit_next", head + '#unit("N")\n#eq("a", `2 * l`)\n#eq("b", `2 * F`)\n#eq("c", `3 * F`)')
    assert "b = 10000 N" in text and "c = 15 kN" in text, text
    document = _text("unit_document", head + '#unit("N", scope: "document")\n#eq("b", `2 * F`)\n#eq("c", `3 * F`)')
    assert "b = 10000 N" in document and "c = 15000 N" in document, document
    domain = _text("unit_domain", head + '#domain("p")[\n#unit("N", scope: "domain")\n#eq("b", `2 * F`)\n#eq("c", `3 * F`)\n]\n#eq("d", `4 * F`)')
    assert "b = 10000 N" in domain and "c = 15000 N" in domain and "d = 20 kN" in domain, domain
    assert "scope" in _refused("unit_scope", '#unit("N", scope: "page")')


# --- #domain --------------------------------------------------------------------------------

def test_a_domain_prints_its_label_keeps_its_names_and_its_footnote_once():
    body = ('#outline()\n= Statik\n#domain("p1", label: "Poutre P1", descr: "Travée unique", descr-position: "footnote", norm: "SIA 265", norm-section: "4.2.1", norm-position: "in-line")[\n'
            '#var("F", 1, "kN")\n]\n#domain("p2")[#var("F", 2, "kN")]\nNach #var("F", domain: "p1").')
    text = _text("domain", body)
    assert text.count("Travée unique") == 1, "a footnote on a heading is printed once, the outline aside"
    assert "Poutre P1" in text and "SIA 265 4.2.1" in text, text
    assert "F = 1 kN." in text, "what a domain declares stays readable by its id"
    assert "gen" in _refused("domain_gen", '#domain("p", gen: (kind: "tension", form: "(6)", version: 1))[]')


# --- #var-table and #get by name -----------------------------------------------------------------

def test_a_table_lists_the_variables_of_a_role_before_they_are_declared():
    """REQ-010, T3: «faire des tableaux uniquement avec les variables data, ou résultat», the columns chosen -- read from the registry, never copied, so a table at the head of a domain lists what is declared below it."""
    body = ('#domain("p1")[\n#var-table(role: "data", columns: ("label", "symbol", "value"))\n'
            '#var("b", 140, "mm", label: "Largeur", level: 0)\n#var("h", 400, "mm", label: "Hauteur", level: 0)\n#eq("A", `b * h`, level: 0)\n'
            '#var-table(role: "compute", columns: ("symbol", "value"))\n]')
    text = _text("var_table", body)
    head, _, rest = text.partition("A 56000")
    assert "Largeur" in head and "140 mm" in head and "Hauteur" in head and "400 mm" in head, text
    assert "56000 mm2" in text, "the computed value is the compute table's"
    assert text.count("Largeur") == 1, "the data table does not list the computed A, nor the compute table the data"


def test_a_table_over_every_domain_filtered_by_unit_is_the_summary_of_the_loads():
    """Q-009: `#var-table` over every domain, filtered by unit, is what `show-load-summary` printed."""
    body = ('#var("g_k", 1.2, "kN/m²", label: "Eigengewicht", level: 0)\n#var("l", 3, "m", label: "Spannweite", level: 0)\n'
            '#domain("dach")[#var("s_k", 1.4, "kN/m²", label: "Schnee", level: 0)]\n'
            '#var-table(role: "data", domain: "all", unit: "kN/m²", columns: ("label", "value", "unit"))')
    text = _text("var_table_all", body)
    assert "Eigengewicht" in text and "Schnee" in text and "Spannweite" not in text, text
    assert "column" in _refused("var_table_column", '#var-table(columns: ("label", "colour"))')


def test_get_reads_a_variable_by_its_name_for_a_sentence_that_depends_on_a_result():
    """REQ-009: «Texte qui dépend du résultat» -- `get` by name, in a context."""
    body = '#var("eta", 0.75, level: 0)\n#domain("p")[#var("eta", 1.2, level: 0)]\n#context [#metadata((get("eta", "value"), get("eta", "value", domain: "p"), get("eta", "role"))) <out>]'
    assert _query(body) == [0.75, 1.2, "data"]



def test_a_domain_chooses_the_block_family_and_its_lines_keep_their_levels():
    """Q-014: `#calc-defaults(presets: "block", scope: "domain")` -- what a generated file writes at its head -- puts the label after the line and the citation in the right-hand column, at the levels `inline` shows them and no other: a client report of level 1 still shows neither."""
    body = ('#domain("p", level: {lv})[\n#calc-defaults(presets: "block", scope: "domain")\n'
            '#var("N_t_d", 50, "kN", label: "Zugkraft", norm: "SIA 265", norm-section: "4.2.1")\n]')
    one = _text("block_1", body.replace("{lv}", "1"))
    assert "Zugkraft" not in one and "SIA 265" not in one, one
    three = _text("block_3", body.replace("{lv}", "3"))
    assert "50 kN — Zugkraft" in three and "SIA 265 4.2.1" in three, three
    assert "family of presets" in _refused("presets_unknown", '#calc-defaults(presets: "wide")')


# --- the preview of «Affichage»: what the report hides, shown pale (spec 2026-10-22-onglet-neige-type, UI-011) -----------

def test_show_masked_prints_every_hidden_line_pale_and_marked():
    """`show-masked` (lib/calc-engine-core.typ), set by the preview of a domain's file: a `#var` at level 0, an `#eq` whose two displays are none and a `#verify` at level 0 are printed at level 3's preset, each marked «ausgeblendet»; a line the report prints is not marked; without the state nothing hidden is printed."""
    body = '''#var("h_0", 850, "m", level: 0)
#eq("h_r", `h_0 + 1 "m"`, display-formula: "none", display-equation: "none")
#verify(`h_r >= h_0`, level: 0)
#var("b", 3, "m")'''
    shown = _text("masked_on", "#show-masked.update(true)\n" + body)
    assert shown.count("ausgeblendet") == 3, shown
    assert "h0 = 850 m (ausgeblendet)" in shown and shown.endswith("b = 3 m"), shown
    hidden = _text("masked_off", body)
    assert hidden.strip() == "b = 3 m", hidden
