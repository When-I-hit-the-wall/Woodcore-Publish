"""What the engineer types in the «Domaines» tab, and the arguments of a line, without Qt (calc/domains/formula_infer.py, formula_args.py; issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-001, REQ-002, REQ-008, REQ-009, UI-012, ARCH-RISK-003, ARCH-RISK-004).

Held: a line typed is inferred a var, an eq, a verify or a text -- a relation with ≥, a number without a unit, a unit unknown, a symbol taken, a command chosen that wins; a calculation typed with the symbols shown is written with the keys and computes the same value, `f_(m,d,"Tab")`, `sigma_(m, d)`, a composed symbol and a symbol two keys bear included; the arguments a line is offered are calc/line_display.py's, their values lib/display-presets.json's -- a value added to the file appears with no code changed --, and each written compiles; the command of a line of the buffer is recognised, and an argument written changes that line alone.
"""

TIER = "fast"

import shutil
import subprocess

import conftest
from conftest import ROOT, Skip

import line_display
import project
from domains import formula_args as fa, formula_domain as fd, formula_infer as fi

FIXTURE = ROOT / "tests" / "fixtures" / "domains" / "panne-p2.typ"


def test_a_line_typed_is_inferred():
    """REQ-001: «h = 240 mm» a var, «M_d = q_d * l^2 / 8» an eq, «sigma_(m,d) <= f_(m,d)» and «a ≥ b» a verify, a number without a unit a var, a unit unknown an eq, a symbol taken a key suffixed, free words a text; a command chosen wins."""
    line = fi.infer_line("h = 240 mm")
    assert (line.kind, line.chosen, line.fields) == ("var", False, {"symbol": "h", "value": "240", "unit": "mm", "key": "h"})
    assert fi.infer_line("M_d = q_d * l^2 / 8").fields == {"symbol": "M_d", "formula": "q_d * l^2 / 8", "key": "M_d"}
    assert fi.infer_line("sigma_(m,d) <= f_(m,d)").kind == "verify"
    assert fi.infer_line("a ≥ b").fields == {"relation": "a ≥ b"}
    assert fi.infer_line("n = 3").fields == {"symbol": "n", "value": "3", "unit": "", "key": "n"}
    assert fi.infer_line("x = 3 zorglub").kind == "eq"
    assert fi.infer_line("M_(y,d) = 2 kNm", taken={"M_y_d"}).fields["key"] == "M_y_d_2"
    assert fi.infer_line("_Résistance_").kind == "text" and fi.infer_line("   ") is None
    chosen = fi.infer_line("h = 240 mm", kind="eq")
    assert (chosen.kind, chosen.chosen, chosen.fields["formula"]) == ("eq", True, "240 mm")
    command = fi.command_of(fi.infer_line("h = 240,5 mm"))
    assert (command.kind, command.key, command.value, command.unit) == ("var", "h", 240.5, "mm")
    try:
        fi.command_of(fi.infer_line("h = 240 mm"), taken={"h"} - {"h"} | {"x"})
        fi.command_of(fi.Inferred("var", fields={"symbol": "h", "key": "h", "value": "abc", "unit": ""}))
    except fd.DomainError as exc:
        assert exc.code == "value"
    else:
        raise AssertionError("«abc» was taken for a number")


def _panne():
    here = project.current()
    path = here.formulas_dir / "panne-p2.typ"
    shutil.copy(FIXTURE, path)
    return here, path, fd.read(path)


def test_a_calculation_typed_with_the_symbols_is_written_with_the_keys_and_computes_the_same():
    """REQ-002, ARCH-RISK-004: every eq of Poutre P1 and Panne P2, shown with the symbols of the lines above and typed back, computes the same value -- and, carrying no written unit, is the same text; `f_(m,d,"Tab")` typed as shown, `sigma_(m, d)` with its space, the composed (g_k + a_k)_"gew" by its key."""
    here = project.current()
    poutre = fd.read(here.formulas_dir / "poutre-p1.typ")
    _here, path, panne = _panne()
    try:
        for domain in (poutre, panne):
            domains = fd.list_domains(here)
            resolve = lambda c: fd.resolve_import(here, c, domains)   # noqa: E731
            results = fd.compute(domain, resolve)
            for i, c in enumerate(domain.commands):
                if c.kind not in ("eq", "verify"):
                    continue
                table = fi.symbol_table(domain, i, results)
                shown = fi.to_symbols(c.formula, table)
                back = fi.to_keys(shown, table)
                if '"' not in c.formula:
                    assert back == c.formula, (domain.id, c.formula, shown, back)
                trial = fd.Domain(id=domain.id, name=domain.name, commands=[fd.replace(x, formula=back) if x is c else x for x in domain.commands])
                again = fd.compute(trial, resolve)
                assert again[i].value == results[i].value, (domain.id, c.key)
        table = fi.symbol_table(panne, None, fd.compute(panne, lambda c: fd.resolve_import(here, c, fd.list_domains(here))))
        assert table.typed("f_m_d_tab") == 'f_(m,d,"Tab")' and table.typed("sigma_m_d") == "sigma_(m,d)"
        assert table.typed("gk_ak_gew") == "gk_ak_gew", "a composed symbol is typed by its key"
        assert fi.to_keys("sigma_(m, d) / f_(m,d)", table) == "sigma_m_d / f_m_d"
        assert fi.to_keys('eta_w * f_(m,d,"Tab")', table) == "eta_w * f_m_d_tab"
        # a symbol two keys bear: the lowest keeps it, the other is typed by its key and the table says so
        twice = fd.Domain(id="t", name="t", commands=[fd.Command("var", key="a1", symbol="a_1", value=1), fd.Command("var", key="a2", symbol="a_1", value=2)])
        table = fi.symbol_table(twice)
        assert table.typed("a2") == "a_1" and table.typed("a1") == "a1" and table.shadowed == ["a1"]
        assert fi.to_keys("a_1 + a1", table) == "a2 + a1"
    finally:
        path.unlink()


def test_the_arguments_of_a_line_are_line_display_s_with_the_presets_values():
    """REQ-009, ARCH-RISK-003, UI-012: the arguments are what the line is, then calc/line_display.py's -- 17 for an eq, 11 for a verify, `role` on a var (P-4) --; their values are lib/display-presets.json's: a value added to the file appears without a line of code; in «Formulaire» the module offers only what the row does not show."""
    eq = fd.Command("eq", key="M_d", formula="q_d * l^2 / 8", unit="kNm")
    assert len(fa.names("eq")) == 17 and len(fa.names("verify")) == 11 and "role" in fa.names("var")
    assert fa.names("eq")[9:] == line_display.display_args("eq")
    offered = {a.name: a for a in fa.arguments(eq)}
    assert offered["display-formula"].choices == line_display.fine_values()["display-formula"]
    assert "value" not in {a.name: a for a in fa.arguments(fd.Command("verify", formula="a <= b"))}["display"].choices
    assert offered["level"].choices == ("0", "1", "2", "3")
    assert [a.name for a in fa.arguments(eq, everything=False)] == ["as-unit"] + list(line_display.display_args("eq"))
    data = line_display._read()
    try:
        line_display._cache["data"] = dict(data, **{"fine-values": dict(data["fine-values"], **{"display-formula": list(data["fine-values"]["display-formula"]) + ["probe"]})})
        assert "probe" in {a.name: a for a in fa.arguments(eq)}["display-formula"].choices
    finally:
        line_display._cache["data"] = data
    # auto writes nothing; a value is written into the line
    set_ = fa.set_argument(eq, "display-formula", "value")
    assert set_.options == {"display-formula": "value"} and fa.set_argument(set_, "display-formula", "").options == {}
    assert fa.written(set_) == '#eq("M_d", `q_d * l^2 / 8`, unit: "kNm", display-formula: "value")'


def test_every_value_the_module_writes_compiles():
    """REQ-009: a line of each command with each value of each of its arguments compiles (lib/formula.typ's `check-fine` stops on a wrong one)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    lines = ['#domain("probe", label: "Probe")[', '  #var("a", 2, "m")', '  #eq("b", `a * 2`)']
    base = {"var": fd.Command("var", key="c", value=1, unit="m"), "eq": fd.Command("eq", key="d", formula="a * 3"), "verify": fd.Command("verify", formula="a <= b")}
    n = 0
    for kind, command in base.items():
        for argument in fa.arguments(command):
            if argument.kind != "choice":
                continue
            for value in argument.choices:
                n += 1
                one = fa.set_argument(fd.replace(command, key=f"{command.key}{n}" if command.key else ""), argument.name, value)
                lines.append("  " + fd.to_call(one))
    lines.append("]")
    folder = conftest.probe_dir("formula_input_values")
    doc = folder / "probe.typ"
    doc.write_text('#import "/000-Typst-Config/commands.typ": *\n' + "\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(doc), str(folder / "probe.pdf")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stderr[:800]
    assert n > 60


def test_the_command_of_a_line_is_recognised_and_written_alone():
    """UI-012, ARCH-RISK-010: line 13 of Panne P2 is its eq q_d, line 5 its text; an argument set gives the lines of the buffer to replace, the rest untouched; a buffer that does not read still names the command its line opens."""
    here, path, panne = _panne()
    try:
        at = fa.command_at(panne, 13)
        assert (at.kind, at.first, panne.commands[at.index].key) == ("eq", 13, "q_d")
        assert fa.command_at(panne, 5).kind == "text" and fa.command_at(panne, 25).kind == "verify"
        first, last, new = fa.line_edit(panne, at.index, fa.set_argument(panne.commands[at.index], "display-formula", "value"))
        assert (first, last) == (13, 13) and new.endswith('norm-section: "4.4.3.4", display-formula: "value")'), new
        broken = path.read_text(encoding="utf-8").replace('label: "Hauteur")', 'label: "Hauteur"')
        unread = fd.parse_text(broken, path)
        assert unread.state == "unreadable"
        at = fa.command_at(unread, 19, broken)
        assert (at.kind, at.reads) == ("var", False)
    finally:
        path.unlink()
