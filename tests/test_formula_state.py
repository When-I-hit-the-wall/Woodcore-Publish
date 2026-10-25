"""The state of a domain of the «Domaines» tab and what `compute` says of it, without Qt (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-004 to REQ-008, REQ-010, REQ-011, REQ-013, REQ-015, REQ-019, ARCH-012).

Held: every code of `units.FormulaError` and of `formula_domain.DomainError` has its words in three languages, its values filled; a fault is said once, the lines below that only inherit it counted with it; a parenthesis forgotten is placed where Typst places it; a fault of computation names the line of the domain's file; a check that fails, a domain read by its name and not printed above, a domain not printed in a block are orange; a name the export knows offers its link; a linked variable carries its source's symbol and label; the hovers' lines are `compute`'s; `#calc-defaults` is read and written option by option, a new domain opening on it; «Article» is `norm-section:`, `norm-ref:` read.
"""

TIER = "fast"

import shutil
import string
import sys

import conftest
from conftest import ROOT, Skip

import project
import units
from domains import formula_defaults, formula_domain as fd, formula_errors, formula_links, formula_rows, formula_state

TOOLS = ROOT / "calc" / "tools"
FIXTURE = ROOT / "tests" / "fixtures" / "domains" / "panne-p2.typ"


def _words():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    import formula_tab_words
    return formula_tab_words


def _panne(text=None):
    """Panne P2, the prototype's domain (tests/fixtures/domains/panne-p2.typ), copied into the project of the run -- `text` in its place where given -- and read."""
    here = project.current()
    path = here.formulas_dir / "panne-p2.typ"
    if text is None:
        shutil.copy(FIXTURE, path)
    else:
        path.write_text(text, encoding="utf-8", newline="")
    return here, path, fd.read(path)


def _computed(here, domain):
    domains = fd.list_domains(here)
    return fd.compute(domain, lambda c: fd.resolve_import(here, c, domains), describe=formula_links.describer(here, domains))


def _fields(text):
    return {name for _lit, name, _spec, _conv in string.Formatter().parse(text) if name}


def test_every_code_has_its_words_in_three_languages_with_its_values():
    """REQ-005: each code a FormulaError or a DomainError is raised with is said by the window in fr, de and en, with the values it carries -- the English message stays the report's."""
    words = _words()
    for lang in ("fr", "de", "en"):
        table = words.STRINGS[lang]
        for code, values in units.CODES.items():
            key = "fm_e_" + code
            assert key in table, (lang, key)
            if code != "formula":
                said = {"var" if v == "key" else v for v in values}   # a variable's key is said `{var}`: `key` is MainWindow.t's own argument
                assert _fields(table[key]) <= said, (lang, key, _fields(table[key]), values)
        for code in fd.CODES:
            assert code in words.REFUSALS and words.REFUSALS[code] in table, (lang, code)
    try:
        units.FormulaError("x", "no-such-code")
    except ValueError:
        pass
    else:
        raise AssertionError("a FormulaError of an unknown code was made")


def test_an_unknown_name_is_said_in_french_with_every_name_known():
    """REQ-005, defect 4: «eq: no variable named 'L' here» is said in French, the names known listed whole (no cut at 80 characters)."""
    here, path, domain = _panne()
    try:
        domain.commands[8].formula = "q_d dot L^2 / 8"
        results = _computed(here, domain)
        r = results[8]
        assert r.code == "unknown" and r.values["names"] == ("L",) and "no variable named 'L'" in r.error
        st = formula_state.state(domain, results, formula_rows.item_lines(domain))
        message = st.errors[0]
        text = _words().STRINGS["fr"]["fm_e_" + message.code].format(**message.values)
        assert text.startswith("« L » n'est déclaré nulle part") and "gamma_Q" in text and "q_d" in text, text
        assert len(text) > 80
    finally:
        path.unlink()


def test_a_fault_is_said_once_its_dependents_counted():
    """REQ-006, defect 5: `L` for `l` in M_d -- one red fault, «3 lignes plus bas en dépendent» (σ_m,d, the check, η); corrected, none; a second fault of its own in one of the three stays red."""
    here, path, domain = _panne()
    try:
        domain.commands[8].formula = "q_d dot L^2 / 8"
        results = _computed(here, domain)
        st = formula_state.state(domain, results, formula_rows.item_lines(domain))
        assert [m.item for m in st.errors] == [8] and st.errors[0].dependents == 3, st.errors
        assert sorted(i for i, s in st.rows.items() if s == "blocked") == [13, 17, 18]
        assert st.rows[8] == "error"
        domain.commands[8].formula = "q_d dot l^2 / 8"
        assert not formula_state.state(domain, _computed(here, domain), formula_rows.item_lines(domain)).errors
        domain.commands[8].formula = "q_d dot L^2 / 8"
        domain.commands[18].formula = "sigma_m_d / f_m_d + Z"
        st = formula_state.state(domain, _computed(here, domain), formula_rows.item_lines(domain))
        assert [m.item for m in st.errors] == [8, 18], st.errors
    finally:
        path.unlink()


def test_a_parenthesis_forgotten_is_placed_where_typst_places_it():
    """REQ-007, defect 8: the `)` of `#var("h", …)` forgotten -- line 19, at the `(` Typst names (its column as `typst compile` prints it), not where Woodcore's parser stumbled; held to Typst where the binary is here."""
    lines = FIXTURE.read_text(encoding="utf-8").split("\n")
    assert lines[18].startswith('  #var("h"')
    lines[18] = lines[18].rstrip(")")
    text = "\n".join(lines)
    fault = formula_errors.read_fault(text)
    assert fault == {"code": "unclosed", "line": 19, "col": 6}, fault
    assert formula_errors.read_fault(FIXTURE.read_text(encoding="utf-8")) is None
    here, path, domain = _panne(text)
    try:
        assert domain.state == "unreadable"
        st = formula_state.state(domain, [], [])
        assert [(m.code, m.line, m.col) for m in st.errors] == [("read_unclosed", 19, 6)]
        typst = project.typst_executable() if hasattr(project, "typst_executable") else None
        if typst:
            import re
            import subprocess
            probe = conftest.probe_dir("formula_state") / "unclosed.typ"
            probe.write_text(text.replace('#import "/000-Typst-Config/commands.typ": *', ""), encoding="utf-8")
            out = subprocess.run([str(typst), "compile", str(probe)], capture_output=True, text=True, encoding="utf-8", errors="replace")
            found = re.search(r"unclosed delimiter\s*\n\s*┌─ .*:(\d+):(\d+)", out.stderr)
            assert found and (int(found.group(1)), int(found.group(2))) == (19, 6), out.stderr[:400]
    finally:
        path.unlink()


def test_a_fault_of_computation_names_the_line_of_the_domain_s_file():
    """REQ-007, defect 10: a name unknown on line 13 (q_d) -- «ligne 13 de Domains/panne-p2.typ»."""
    here, path, domain = _panne()
    try:
        domain.commands[7].formula = "(gamma_G dot gk_ak_gew + gamma_Q dot q_k9) dot e"
        results = _computed(here, domain)
        st = formula_state.state(domain, results, formula_rows.item_lines(domain))
        message = st.errors[0]
        rel, line = formula_errors.where_text(here, domain, message.line)
        said = _words().STRINGS["fr"]["fm_e_at"].format(line=line, file=rel, text="…")
        assert said.startswith("Ligne 13 de Domains/panne-p2.typ"), said
    finally:
        path.unlink()


def test_the_orange_warnings():
    """REQ-011: h = 200 mm, the check fails (orange, its ratio); a domain without `presets: "block"` (orange, leading to the options); a name the export knows offers its link (REQ-013)."""
    here, path, domain = _panne()
    try:
        domain.commands[11].value = 200
        results = _computed(here, domain)
        st = formula_state.state(domain, results, formula_rows.item_lines(domain))
        fails = [m for m in st.warnings if m.code == "fails"]
        assert len(fails) == 1 and fails[0].item == 17 and st.rows[17] == "warning" and not st.errors
        assert fails[0].values["ratio"] == "127.2", fails[0].values
        assert not [m for m in st.warnings if m.code == "inline"]
        poutre = fd.read(here.formulas_dir / "poutre-p1.typ")
        st = formula_state.state(poutre, fd.compute(poutre), formula_rows.item_lines(poutre))
        inline = [m for m in st.warnings if m.code == "inline"]
        assert inline and inline[0].fix == {"kind": "options"}
        # a name unknown here that the export knows: its link offered
        domain.commands[8].formula = "q_d dot l^2 / 8 + 0 * s_k"
        results = _computed(here, domain)
        candidates = [{"key": "s_k", "calc": "snow-load", "instance": "SL", "label": "Schnee", "symbol": "s_k", "value": 0.9, "unit": "kN/m²"}]
        st = formula_state.state(domain, results, formula_rows.item_lines(domain), candidates=candidates)
        assert st.errors[0].fix["kind"] == "link" and st.errors[0].fix["calc"] == "snow-load"
    finally:
        path.unlink()


def test_a_domain_read_by_its_name_and_not_printed_above_is_orange():
    """REQ-011, D-8, P-2: «poutre-p1» read by Panne P2 by its name -- orange in a document that prints Panne P2 without Poutre P1 above it; nothing where neither is printed."""
    here, path, domain = _panne()
    sections = here.document_dir("rs") / "Sections"
    probe = sections / "999-probe-formula-state.typ"
    try:
        domain.commands.append(fd.Command("var", key="M_Rd", source=("domain", "poutre-p1")))
        tab = fd.list_domains(here)
        results = _computed(here, domain)
        st = formula_state.state(domain, results, formula_rows.item_lines(domain), here=here, tab_domains=tab)
        assert not [m for m in st.warnings if m.code == "tabdom"], "a domain printed nowhere gives no warning"
        report = here.document_typ("rs")
        was = report.read_text(encoding="utf-8")
        probe.write_text('#include "/Domains/panne-p2.typ"\n', encoding="utf-8")
        report.write_text(was + '\n#include "Sections/999-probe-formula-state.typ"\n', encoding="utf-8")
        try:
            st = formula_state.state(domain, results, formula_rows.item_lines(domain), here=here, tab_domains=tab)
            assert [m.values["key"] for m in st.warnings if m.code == "tabdom"] == ["M_Rd"]
            probe.write_text('#include "/Domains/poutre-p1.typ"\n#include "/Domains/panne-p2.typ"\n', encoding="utf-8")
            st = formula_state.state(domain, results, formula_rows.item_lines(domain), here=here, tab_domains=tab)
            assert not [m for m in st.warnings if m.code == "tabdom"]
        finally:
            report.write_text(was, encoding="utf-8")
    finally:
        probe.unlink(missing_ok=True)
        path.unlink()


def test_a_linked_variable_shows_its_source_s_symbol_and_label():
    """REQ-010, defect 6: the dead load linked from the export is (g_k + a_k)_"gew", labelled as the export labels it, from «dead-load · EL+AL-Dach_ohne_Wasser» -- `resolve_import` untouched."""
    here, path, domain = _panne()
    try:
        results = _computed(here, domain)
        r = results[1]
        assert r.symbol == '(g_k + a_k)_"gew"' and r.label == "Ständige Lasten, gewählt" and r.origin == ("export", "dead-load", "EL+AL-Dach_ohne_Wasser")
        assert results[2].symbol == "q_k" and results[2].origin == ("export", "snow-load", "SL")
        rows = {key: symbol for key, symbol, _v, _u in fd.variables_of(domain, results)}
        assert rows["gk_ak_gew"] == '(g_k + a_k)_"gew"'
    finally:
        path.unlink()


def test_the_hovers_are_the_lines_compute_read():
    """REQ-019, UI-018: η is computed from σ_m,d and f_m,d and nothing uses it; b is used by W_y alone."""
    here, path, domain = _panne()
    try:
        deps = formula_links.dependencies(domain, _computed(here, domain))
        assert deps[18] == {"uses": [13, 16], "used": []}
        assert deps[10] == {"uses": [], "used": [12]}
        assert deps[13]["uses"] == [8, 12] and deps[13]["used"] == [17, 18]
    finally:
        path.unlink()


def test_calc_defaults_is_read_and_written_option_by_option():
    """REQ-004, D-3: a new domain opens on the line; a domain without it is read and written back as it was; ticking, unticking, unticking everything; the line unfold.py writes, its label behind, read without loss."""
    here = project.current()
    new = fd.new_domain(here, "Essai défauts")
    assert [c.raw for c in new.commands] == ['#calc-defaults(presets: "block", scope: "domain")']
    assert '#calc-defaults(presets: "block", scope: "domain")' in fd.write_text(new)
    poutre = fd.read(here.formulas_dir / "poutre-p1.typ")
    assert fd.write_text(poutre) == poutre.text and formula_defaults.find(poutre) is None
    items = formula_defaults.set_option(poutre, "label-position", "after")
    assert items[0].raw == '#calc-defaults(label-position: "after", scope: "domain")'
    poutre.commands = items
    poutre.commands = formula_defaults.set_option(poutre, "presets", "block")
    assert poutre.commands[0].raw == '#calc-defaults(presets: "block", label-position: "after", scope: "domain")'
    poutre.commands = formula_defaults.set_option(poutre, "presets", None)
    poutre.commands = formula_defaults.set_option(poutre, "label-position", None)
    assert not [c for c in poutre.commands if c.is_text]
    unfolded = fd.Domain(id="ZT-01", name="ZT-01", commands=[fd.Command(fd.TEXT, raw='#calc-defaults(presets: "block", level: 2, scope: "domain") <ZT-01-presets>'), fd.Command("var", key="x", value=1)])
    found = formula_defaults.find(unfolded)
    assert found.options == {"presets": "block"} and found.tail == " <ZT-01-presets>" and ("level", "2") in found.others
    unfolded.commands = formula_defaults.set_option(unfolded, "style", "normal")
    assert unfolded.commands[0].raw == '#calc-defaults(presets: "block", style: "normal", level: 2, scope: "domain") <ZT-01-presets>'
    assert set(formula_defaults.OPTIONS) <= set(_calc_default_names())


def test_panne_p2_compiled_with_its_calc_defaults_prints_a_line_a_value():
    """REQ-004, defect 1: Panne P2 with `#calc-defaults(presets: "block")` prints one line a value; without it its values run in one paragraph -- far fewer lines, its labels in footnotes."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import subprocess
    from pypdf import PdfReader
    lines = {}
    for name, text in (("block", FIXTURE.read_text(encoding="utf-8")),
                       ("inline", FIXTURE.read_text(encoding="utf-8").replace('#calc-defaults(presets: "block", scope: "domain")\n', ""))):
        folder = conftest.probe_dir("formula_state_" + name)
        doc = folder / "probe.typ"
        doc.write_text(text, encoding="utf-8")
        out = folder / "probe.pdf"
        r = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(doc), str(out)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0, r.stderr[:600]
        page = "\n".join(p.extract_text() for p in PdfReader(str(out)).pages)
        lines[name] = [l for l in page.split("\n") if "=" in l]
    assert len(lines["block"]) >= 15, lines["block"]
    assert len(lines["block"]) > 2 * len(lines["inline"]), (len(lines["block"]), len(lines["inline"]))


def _calc_default_names():
    import re
    text = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    found = re.search(r"#let calc-default-names = \(([^)]*)\)", text)
    return re.findall(r'"([^"]+)"', found.group(1))


def test_article_is_norm_section_and_norm_ref_is_read():
    """REQ-008, defect 3: γ_G cited `norm-section: "Tableau 1"` shows it; a file of before with `norm-ref:` is read into it and written `norm-section:` once the line changes -- never the two."""
    here, path, domain = _panne()
    try:
        assert domain.commands[5].options["norm-section"] == "Tableau 1"
        old = FIXTURE.read_text(encoding="utf-8").replace('norm-section: "Tableau 1")\n  #var("gamma_Q"', 'norm-ref: "Tableau 1")\n  #var("gamma_Q"')
        here, path, domain = _panne(old)
        c = domain.commands[5]
        assert c.options.get("norm-section") == "Tableau 1" and "norm-ref" not in c.options
        assert fd.write_text(domain) == old, "a line not changed keeps its bytes"
        from domains import formula_args
        domain.commands[5] = formula_args.set_argument(c, "norm-section", "Tableau 2")
        line = fd.write_text(domain).split("\n")[10]
        assert 'norm-section: "Tableau 2"' in line and "norm-ref" not in line, line
    finally:
        path.unlink()


def test_the_states_of_an_unfolded_check_colour_their_rows():
    """REQ-015, ARCH-RISK-018: each state of a line of an unfolded check gives its row its colour (a conflict and a line taken out red, changed outside and data changed orange, the engineer's own the accent), in step none."""
    states = {0: "conflict", 1: "missing", 2: "local", 3: "data", 4: "own", 5: "in_sync"}
    domain = fd.Domain(id="x", name="x", commands=[fd.Command("var", key=f"k{i}", value=1) for i in range(6)] + [fd.Command(fd.TEXT, raw=formula_defaults.NEW_LINE)])
    st = formula_state.state(domain, fd.compute(domain), formula_rows.item_lines(domain), unfold_states=states)
    assert {i: formula_state.COLOURS.get(s) for i, s in st.rows.items()} == {0: "danger", 1: "danger", 2: "warning", 3: "warning", 4: "accent"}
    import json
    theme = json.loads((TOOLS / "theme.json").read_text(encoding="utf-8"))
    tokens = set(theme.get("light", theme))
    assert set(formula_state.COLOURS.values()) <= tokens, set(formula_state.COLOURS.values()) - tokens
