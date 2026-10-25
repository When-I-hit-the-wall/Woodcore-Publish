"""The level each line of a calculation is printed from: one table, lib/line-levels.json, read by Python -- the reference workbook and the steel checks; Typst read it too until the spec 2026-10-21-commandes-typst-refonte retired show-calc (spec 2026-10-20-indices-et-niveaux, UI-002, ARCH-002, D-13).

The engineer, 19.10.2026: «Niveau de détail : corrige (décidé par la commande)». Until v0.120 a line's level was a literal twice over -- written into the export by each domain in Python (snow, wind, the loads, steel), written into lib/timber.typ for the member checks --, two places to set one thing (audit 261019). The table is now the one place; these checks hold that it changed no line of any report: every line the domains exported until v0.120 resolves to the level it was exported at (tests/fixtures/line-levels-history.json, collected by running the domain tests with the engine instrumented), and Typst's reader answers as Python's.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import re
import subprocess

import conftest
from conftest import ROOT, Skip

import line_levels
import project

HISTORY = json.loads((ROOT / "tests" / "fixtures" / "line-levels-history.json").read_text(encoding="utf-8"))["lines"]


def test_every_line_keeps_the_level_it_was_exported_at():
    """CON-001: a report prints the same lines at the same level as before -- the table says, for every line the domains wrote until v0.120, the level they wrote."""
    wrong = [(h["domain"], h["kind"], h["role"], h["key"], h["level"], line_levels.level(h["domain"], h["key"], h["role"], h["kind"]))
             for h in HISTORY if line_levels.level(h["domain"], h["key"], h["role"], h["kind"]) != h["level"]]
    assert not wrong, wrong
    assert {h["domain"] for h in HISTORY} >= {"dead-load", "live-load", "snow-load", "wind-load", "steel"}
    assert {h["kind"] for h in HISTORY if h["domain"] == "steel"} >= {"tension", "compression", "bending", "shear"}


def test_a_value_and_its_working_and_a_kind_of_check_may_differ():
    """ARCH-RISK-601: snow's h_ref is printed as a value from 2 and its working from 3; steel's N_Rd is the answer of a tension (1) and one term of a bending's interaction (2)."""
    assert (line_levels.level("snow-load", "h_ref", "var"), line_levels.level("snow-load", "h_ref", "step")) == (2, 3)
    assert line_levels.level("steel", "N_Rd", kind="tension") == 1 and line_levels.level("steel", "N_Rd", kind="bending") == 2
    assert line_levels.level("wind-load", "qk_max_cfs2") == 1, "a family of keys is named by its pattern (ARCH-RISK-602)"


def test_a_line_the_table_does_not_name_keeps_its_own_or_its_domains_default():
    """The priority of docs/typst/report-engine.md §4: the table's, else the line's own (an export written before v0.120, a domain written by hand), else the domain's `*` (a script's results, named by the engineer), else none."""
    assert line_levels.level("snow-load", "not_a_key", own=2) == 2
    assert line_levels.level("script", "anything") == 1
    assert line_levels.level("no-such-domain", "x") is None and line_levels.level("no-such-domain", "x", own=3) == 3


# --- lot 4: Python no longer writes a line's level ------------------------------------------------

LINE_DOMAINS = ("connection", "dead_load", "dowel", "live_load", "snow_source", "wind_source", "steel_calc", "steel_resistance", "timber_calc", "script")
LINE_BUILDERS = {"add_var", "add_step", "var", "step", "check", "given", "add", "add263", "step263"}


def test_no_domain_writes_the_level_of_a_line():
    """UI-002 (the engineer: «décidé par la commande»): no call building a line passes a level, no helper of a domain takes one, and no line written as a dictionary carries one -- a table or a figure, which are objects and keep their own (`title` beside it), excepted."""
    import ast
    found = []
    for name in LINE_DOMAINS:
        path = ROOT / "calc" / "domains" / (name + ".py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                fn = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                if any(k.arg == "level" for k in node.keywords) and (fn in LINE_BUILDERS or fn in ("update", "dict")):
                    found.append(f"{path.name}:{node.lineno} {fn}(level=…)")
            if isinstance(node, ast.FunctionDef) and "level" in [a.arg for a in node.args.args + node.args.kwonlyargs]:
                found.append(f"{path.name}:{node.lineno} def {node.name}(…, level, …)")
            if isinstance(node, ast.Dict):
                keys = {k.value for k in node.keys if isinstance(k, ast.Constant)}
                if "level" in keys and "title" not in keys:
                    found.append(f"{path.name}:{node.lineno} {{'level': …}}")
    assert not found, found


def test_the_example_s_exports_carry_no_line_level_at_their_new_versions():
    """ARCH-002: calculations 1.8, steel 1.2, connectors 3.3, connections 4.4, scripts 1.1 -- the versions every export writes since v0.120 -- and no var, step or check of them carries a level; a table or a figure keeps its own."""
    import registry
    from domains import connection, connector, script, steel_check
    data = conftest.PROJECT.data_dir
    wanted = {"calculations.json": registry.SCHEMA_VERSION, "steel.json": steel_check.EXPORT_SCHEMA_VERSION,
              "connectors.json": connector.LEVELS_EXPORT_VERSION, "connections.json": connection.LEVELS_EXPORT_VERSION, "scripts.json": script.EXPORT_SCHEMA_VERSION}
    assert wanted == {"calculations.json": "1.9", "steel.json": "1.2", "connectors.json": "3.3", "connections.json": "4.4", "scripts.json": "1.1"}
    carried = []

    def walk(x, where):
        if isinstance(x, dict):
            if isinstance(x.get("vars"), dict) and isinstance(x.get("steps"), list):
                carried.extend(f"{where} var {k}" for k, v in x["vars"].items() if isinstance(v, dict) and "level" in v)
                carried.extend(f"{where} step {s.get('result')}" for s in x["steps"] if "level" in s)
                carried.extend(f"{where} check {c.get('name')}" for c in x.get("checks") or () if "level" in c)
            for k, v in x.items():
                walk(v, where + "/" + str(k))
        elif isinstance(x, list):
            for v in x:
                walk(v, where)
    for name, version in wanted.items():
        exported = json.loads((data / name).read_text(encoding="utf-8"))
        assert exported["schema_version"] == version, (name, exported["schema_version"])
        walk(exported, name)
    assert not carried, carried[:10]


def test_each_level_of_a_domain_prints_the_lines_of_the_level_below():
    """UI-002, its criterion: each level contains the one before -- every line (a var, a step) printed at 1 is printed at 2, every line at 2 at 3 -- and the three differ, for every instance of every domain the example exports, the levels being the table's. Measured on the lines and not on the page's words: a line printed at 3 may set its formula where 2 sets its value alone, which rewords it (the pages are held to the byte by tests/test_report_golden.py)."""
    data = conftest.PROJECT.data_dir
    instances = []
    for domain, entry in json.loads((data / "calculations.json").read_text(encoding="utf-8"))["domains"].items():
        instances += [(domain, None, inst) for inst in entry["instances"].values()]
    instances += [("steel", r["kind"], r) for r in json.loads((data / "steel.json").read_text(encoding="utf-8"))["checks"].values() if r.get("vars")]
    instances += [("connector", None, r) for r in json.loads((data / "connectors.json").read_text(encoding="utf-8"))["connectors"].values() if r.get("vars")]
    assert {d for d, _k, _i in instances} >= {"snow-load", "wind-load", "dead-load", "live-load", "steel", "connector"}
    flat = []
    for domain, kind, inst in instances:
        lines = [("var", k) for k in inst["vars"]] + [("step", s["result"]) for s in inst.get("steps") or ()]
        printed = [{(role, key) for role, key in lines if line_levels.level(domain, key, role, kind) <= n} for n in (1, 2, 3)]
        assert printed[0] <= printed[1] <= printed[2], (domain, kind)
        if printed[0] == printed[2]:
            flat.append(domain)
    assert set(flat) < {d for d, _k, _i in instances}, "no domain prints more at 3 than at 1: %s" % sorted(set(flat))

