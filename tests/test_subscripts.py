"""How a subscript is printed: one rule, written in lib/subscript.typ and in calc/typst_math.py, held equal here (spec 2026-10-20-indices-et-niveaux, UI-001, ARCH-001, D-06, D-14).

The engineer, 20.10.2026: every subscript upright, in the norm's form -- «tout droit». Until v0.120 `N_(R d)` printed an italic R and d apart, `N_"Rd"` an upright word, `gamma_(M 1)` an italic M beside an upright 1, `f_(m,y,d)` italic letters with spaced commas: the same symbol looked different from one command to the next (audit 261019, «indices»). Every source the report evaluates as math now goes through `math-eval`, and the window and the figures read theirs through `typst_math.normalise`; this file holds the two equal on the cases the rule turns on and on every symbol and formula the example's export carries, says the rule is idempotent, and refuses an `eval(..., mode: "math")` anywhere in lib/ but `math-eval`.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import json
import re
import subprocess

import conftest
from conftest import ROOT, Skip

import typst_math

CASES = [
    ("N_(R d)", 'N_"Rd"'), ("N_(E d)", 'N_"Ed"'), ("N_Rd", 'N_"Rd"'), ('N_"Rd"', 'N_"Rd"'), ("N_(Rd)", 'N_"Rd"'),
    ("gamma_(M 1)", 'gamma_"M1"'), ("gamma_M1", 'gamma_"M1"'), ("gamma_(M1)", 'gamma_"M1"'),
    ("f_(m,y,d)", 'f_"m,y,d"'), ("f_(c,alpha,d)", 'f_"c,α,d"'), ("k_beta", 'k_"β"'),
    ('K_("ser","Verb")', 'K_"ser,Verb"'), ('c_("red", "b/h")', 'c_"red,b/h"'), ("W_(p l,y)", 'W_"pl,y"'),
    ("M_(y,R d) = f_y dot W_(p l,y) / gamma_(M 1)", 'M_"y,Rd" = f_"y" dot W_"pl,y" / gamma_"M1"'),
    ('(g_k + a_k)_"gew"', '(g_"k" + a_"k")_"gew"'),
    # left as written: digits, the bound of an operator, a subscript with an operator or a nested script, quoted text, code, a superscript
    ("mu_11", "mu_11"), ("E_(0,05)", "E_(0,05)"), ("a_(1,2)", "a_(1,2)"),
    ("sum_(i=1)^n x_i", 'sum_(i=1)^n x_"i"'), ("lim_(x -> 0) f", "lim_(x -> 0) f"), ("max_i", "max_i"),
    ("x_(i+1)", "x_(i+1)"), ("x_(a_b)", "x_(a_b)"), ('"a_b" + #h(1em)', '"a_b" + #h(1em)'), ("x^(a b)", "x^(a b)"),
    ("#chain-pad = M_(E d)", '#chain-pad = M_"Ed"'), ("sigma_max", 'sigma_"max"'), ("t_fi", 't_"fi"'),
]


def _corpus():
    """Every symbol and formula of the example's export and of the frozen examples' data, and every string of calc/domains/ that writes a subscript -- what the report and the window actually print."""
    found = set(source for source, _ in CASES)

    def walk(x):
        if isinstance(x, dict):
            for key, value in x.items():
                if key in ("symbol", "formula", "label_math") and isinstance(value, str):
                    found.add(value)
                walk(value)
        elif isinstance(x, list):
            for value in x:
                walk(value)
    for folder in (ROOT / "tests" / "projet-exemple" / "000-Woodcore" / "data", ROOT / "examples" / "data"):
        for path in sorted(folder.rglob("*.json")) if folder.is_dir() else ():
            walk(json.loads(path.read_text(encoding="utf-8")))
    # the symbols lib/ writes itself -- `"d_(char,n)"`, `"k_(h,y)"` in timber.typ -- as string literals without an escape inside
    for path in sorted((ROOT / "lib").glob("*.typ")):
        for literal in re.findall(r'"([A-Za-z]+_\([^"\\()]*\)[^"\\]*)"', path.read_text(encoding="utf-8")):
            found.add(literal)
    for path in sorted((ROOT / "calc" / "domains").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and re.search(r'[A-Za-z]_[("A-Za-z]', node.value) and len(node.value) < 300 and "\n" not in node.value:
                found.add(node.value)
    return sorted(found)


def test_python_writes_every_case_as_the_spec_says():
    for source, wanted in CASES:
        assert typst_math.normalise(source) == wanted, (source, typst_math.normalise(source), wanted)


def test_the_rule_is_idempotent():
    for source in _corpus():
        once = typst_math.normalise(source)
        assert typst_math.normalise(once) == once, (source, once)


def test_typst_writes_every_symbol_as_python_does():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    corpus = _corpus()
    d = conftest.tmpdir("subscripts")
    (d / "corpus.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    probe = d / "probe.typ"
    rel = (ROOT / "lib" / "subscript.typ").relative_to(ROOT).as_posix()
    data = "/" + (d / "corpus.json").relative_to(ROOT).as_posix()
    probe.write_text('#import "/' + rel + '": normalize-subscripts\n#metadata(json("' + data + '").map(normalize-subscripts)) <out>\n', encoding="utf-8")
    out = subprocess.run(["typst", "query", "--root", str(ROOT), str(probe), "<out>", "--field", "value", "--one"],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    differ = [(s, t, typst_math.normalise(s)) for s, t in zip(corpus, got) if t != typst_math.normalise(s)]
    assert not differ, differ[:10]
    assert len(corpus) > 150, len(corpus)


def test_every_normalised_symbol_compiles():
    """Each symbol and formula of the example's export, normalised, is still math Typst evaluates -- a quoted block in the wrong place would stop the report."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    corpus = [s for s in _corpus() if s in _export_strings()]
    d = conftest.tmpdir("subscripts_compile")
    (d / "corpus.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    rel = (ROOT / "lib" / "subscript.typ").relative_to(ROOT).as_posix()
    data = "/" + (d / "corpus.json").relative_to(ROOT).as_posix()
    probe = d / "probe.typ"
    probe.write_text('#import "/' + rel + '": math-eval\n#for s in json("' + data + '") [#math-eval(s) \\ ]\n', encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr


def _export_strings():
    found = set()

    def walk(x):
        if isinstance(x, dict):
            for key, value in x.items():
                if key in ("symbol", "formula") and isinstance(value, str):
                    found.add(value)
                walk(value)
        elif isinstance(x, list):
            for value in x:
                walk(value)
    for path in sorted((ROOT / "tests" / "projet-exemple" / "000-Woodcore" / "data").rglob("*.json")):
        walk(json.loads(path.read_text(encoding="utf-8")))
    return found


def test_lib_evaluates_math_only_through_math_eval():
    """ARCH-001: one door. An `eval(..., mode: "math")` outside `math-eval` would print its subscripts as written, the divergence this rule ended."""
    found = []
    for path in sorted((ROOT / "lib").glob("*.typ")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("//", 1)[0]
            if re.search(r'(?<![\w-])eval\(', code) and path.name != "subscript.typ":
                found.append(f"{path.name}:{i}")
    assert not found, found
