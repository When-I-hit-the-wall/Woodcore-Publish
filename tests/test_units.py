"""The unit algebra in two places, held equal (spec docs/requirements/completed/2026-10-08-onglet-formule-domaines.md, D-10, ARCH-002, ARCH-005, REQ-012).

The «Formule» tab computes at once in Python (calc/units.py) what `#eq` and `#verify` compute in the report (lib/formula.typ) -- the price of an instant result, accepted by the engineer. What keeps the two one:

* the units are written once, in lib/units.json, which both read -- no table of them is left in formula.typ, and the engine copies the file into a project;
* a corpus of formulas -- products, quotients, powers, roots, functions, sums of two units of one dimension, literals with their unit, a declared unit the formula cannot reach -- compiled in **one** probe and read back out of the registry with `typst eval`, gives in Python the same value **and the same unit**;
* what Typst refuses -- a sum of two dimensions, the root of an odd power, a fractional power of a dimension, a unit nobody can read, a name nobody declared -- Python refuses too: the tab never validates a block the report would stop on;
* the Greek names a key is printed with are one list (calc/greek.py, formula.typ's `greek-names`).
"""

import json
import re
import subprocess

import conftest
from conftest import ROOT, Skip

import greek
import project
import units

TYPST_ROOT = conftest.TYPST_ROOT

VARIABLES = (
    ("F", 12, "kN"), ("l", 3, "m"), ("a", 135, "mm"), ("b", 120, "mm"), ("h", 240, "mm"), ("q", 4.5, "kN/m"),
    ("f", 24, "N/mm²"), ("t", 30, "°"), ("n", 3, ""), ("s_k", 1.2, "kN/m²"), ("M", 4.5, "kNm"), ("A", 28800, "mm²"),
    ("eta", 0.8, ""), ("rho", 450, "kg/m³"), ("gamma_M", 1.3, ""), ("sigma_m_d", 9.6, "N/mm²"),
)
# (formula, the unit asked for or None)
CORPUS = (
    ("F * l", None), ("F / l", None), ("M / a", None), ("b * h^2 / 6", None), ("b * h^3 / 12", None),
    ("M / (b * h^2 / 6)", None), ("sqrt(A)", None), ("q * l^2 / 8", None), ('(12 "N") / (3 "m")', None),
    ('(12 "N") / (3000 "mm")', "N/mm"), ('F + 500 "N"', None), ('max(F, 10 "kN")', None), ("min(a, b)", None),
    ("abs(-F)", None), ("sin(t)", None), ("n * F", None), ("eta * f", None), ("F * l", "Nmm"), ("s_k * l", None),
    ("1.35 * q + 1.5 * q", None), ("F / A", None), ("M / a", "N"), ("pi * a^2 / 4", None), ("a / b", None),
    ("F * l", "kN"), ("rho * A", None), ('2.5 "kN/m²" * 4 "m"', "kN/m"), ("exp(eta) * ln(n)", None),
    # keys named after Greek letters, as the «Formule» tab makes them from σ_(m,d) or γ_M
    ("f / gamma_M", None), ("sigma_m_d / (f / gamma_M)", None), ("sigma_m_d * b * h^2 / 6", "kNm"),
)
REFUSED = ("F + l", "sqrt(F)", "a^2.5", '12 "Zork"', "F * nobody")


def _python():
    values = {key: (value, unit) for key, value, unit in VARIABLES}
    out = []
    for formula, want in CORPUS:
        q, _ops = units.evaluate("eq", formula, values)
        value, unit, _warning = units.present("eq", "r", q, want)
        out.append((value, unit))
    return out


def _registry(source, name):
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import variables
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/commands.typ": *\n' + source, encoding="utf-8")
    out = subprocess.run(["typst", "eval", "--in", str(probe), "--root", str(TYPST_ROOT), "--format", "json", variables.expression()],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return out


def test_the_units_are_written_once_and_copied_with_the_engine():
    source = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    assert 'json("units.json")' in source
    for leftover in ('"N":   (1.0', '"G": 1e9', '"m": "mm", "m²": "mm²"', '"⁰": 0, "¹": 1'):
        assert leftover not in source, f"formula.typ still writes a unit table of its own: {leftover!r}"
    assert "lib/units.json" in project.ENGINE_FILES
    data = json.loads((ROOT / "lib" / "units.json").read_text(encoding="utf-8"))
    assert all(isinstance(v, float) for v in data["prefixes"].values()), "a prefix written as an integer is read by Typst as one"
    assert all(isinstance(spec["factor"], float) for spec in data["bases"].values())
    # every unit offered for a dimension is of that dimension, and the default is offered
    for dims, offered in data["offered"].items():
        for unit in offered:
            assert units.dimension_of(unit) == dims, (dims, unit)
        if dims in data["default_units"]:
            assert data["default_units"][dims] in offered, dims


def test_python_and_typst_give_one_value_and_one_unit():
    source = '#var-domain("U")[\n'
    source += "".join(f'#var("{k}", {v}, "{u}", level: 0)\n' if u else f'#var("{k}", {v}, level: 0)\n' for k, v, u in VARIABLES)
    for i, (formula, want) in enumerate(CORPUS):
        source += f'#eq("r{i}", `{formula}`' + (f', unit: "{want}"' if want else "") + ", level: 0)\n"
    source += "]\n"
    out = _registry(source, "units_corpus")
    assert out.returncode == 0, out.stderr
    domain = json.loads(out.stdout)["domains"]["U"]
    assert len(CORPUS) >= 20
    for i, ((formula, want), (value, unit)) in enumerate(zip(CORPUS, _python())):
        record = domain[f"r{i}"]
        assert record["unit"] == unit, (formula, want, record["unit"], unit)
        assert abs(record["value"] - value) <= 1e-9 * max(1.0, abs(value)), (formula, record["value"], value)


def test_python_refuses_what_typst_refuses():
    values = {key: (value, unit) for key, value, unit in VARIABLES}
    head = "".join(f'#var("{k}", {v}, "{u}", level: 0)\n' if u else f'#var("{k}", {v}, level: 0)\n' for k, v, u in VARIABLES)
    for i, formula in enumerate(REFUSED):
        try:
            units.evaluate("eq", formula, values)
        except units.FormulaError:
            pass
        else:
            raise AssertionError(f"Python computed {formula!r}")
        out = _registry(head + f'#eq("x", `{formula}`, level: 0)\n', f"units_refused_{i}")
        assert out.returncode != 0, f"Typst computed {formula!r}, which Python refuses"


def test_numbers_are_printed_as_the_report_prints_them():
    assert units.fmt_decimals(2.0) == "2" and units.fmt_decimals(14.0625) == "14.063" and units.fmt_decimals(-0.0004) == "0"
    assert units.fmt_magnitude(1234567) == "1.235 · 10⁶" and units.fmt_magnitude(99999) == "99999"
    assert units.shown(-2.5, "kN") == units.MINUS + "2.5 kN" and units.shown(30, "°") == "30°"


def test_the_greek_names_are_the_engine_s():
    source = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    block = source[source.index("#let greek-names = ("):]
    block = block[:block.index(")\n")]
    names = tuple(re.findall(r'"([A-Za-z]+)"', block))
    assert names == greek.NAMES, sorted(set(names) ^ set(greek.NAMES))
