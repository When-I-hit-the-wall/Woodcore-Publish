"""How a number is printed: one rule, written in lib/number.typ and in calc/number_text.py, held equal here case by case (spec 2026-10-19-base-saine-nettoyage, UI-002, UI-003, Q-005, D-22).

The engineer, 19.10.2026: «3 chiffres significatifs, mais pas plus de 3 chiffres après la virgule. Donc 0.00234 => 2,34 · 10⁻³» and «au-delà de 99'999, toujours en notation scientifique». The cases of the spec's acceptance criterion, and the edges the rule turns on: the bound of 99 999, a mantissa the rounding carries to 10, a negative number, an exact small value that keeps its digits.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import json
import subprocess

import conftest
from conftest import ROOT, Skip

import number_text as numbers

M = "−"
CASES = [
    (3.120, "3.12"), (0.75, "0.75"), (1 / 3, "0.333"), (0.00234, "2.34 · 10⁻³"), (0.0234, "2.34 · 10⁻²"),
    (123456, "1.235 · 10⁵"), (99999, "99999"), (100000, "1 · 10⁵"), (60910.397, "60910.397"),
    (999999.9, "1 · 10⁶"), (-0.75, M + "0.75"), (-123456, M + "1.235 · 10⁵"), (0.05, "0.05"), (0.001, "0.001"),
    (0.0005, "5 · 10⁻⁴"), (0, "0"), (438, "438"), (1.0006, "1.001"), (0.1234, "0.123"), (2457.95, "2457.95"),
]


def test_python_writes_every_case_as_the_spec_says():
    for value, wanted in CASES:
        assert numbers.display(value) == wanted, (value, numbers.display(value), wanted)


def test_typst_writes_every_case_as_python_does():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.tmpdir("numbers")
    probe = d / "probe.typ"
    rel = (ROOT / "lib" / "number.typ").relative_to(ROOT).as_posix()
    cases = ", ".join(repr(float(v)) if isinstance(v, float) else str(v) for v, _ in CASES)
    probe.write_text('#import "/' + rel + '": display-number\n#metadata((' + cases + ',).map(display-number)) <numbers>\n', encoding="utf-8")
    out = subprocess.run(["typst", "query", "--root", str(ROOT), str(probe), "<numbers>", "--field", "value", "--one"],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    for (value, wanted), printed in zip(CASES, got):
        assert printed == wanted == numbers.display(value), (value, printed, wanted)


def test_the_domains_trim_a_number_with_one_function():
    """UI-003: the `_fmt` the domains wrote for themselves -- member_check's, dowel's, the two load sources' -- are calc/number_text.py's `trimmed`; no module of calc/domains/ defines its own."""
    found = []
    for path in sorted((ROOT / "calc" / "domains").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in ("_fmt", "plain", "number"):
                body = ast.unparse(node)
                if ".rstrip('0').rstrip('.')" in body or '.rstrip("0").rstrip(".")' in body:
                    found.append(f"{path.name}:{node.name}")
    assert not found, found
