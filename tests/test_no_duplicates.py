"""No function written twice in calc/ (spec 2026-10-19-base-saine-nettoyage, lot 0; rule 1 «one source of truth», applied to code).

The audit of 19.10.2026 counted the same helper in five, seven, twenty-seven copies -- `_fail`, `_f`, `normalize_angle`, `confirm_leave`, an undo stack three times -- each copy free to age apart from the others. This test finds every function or method of `calc/` whose body, its name and docstring set aside, is the very same syntax tree as another's, five lines or more.

What exists today is listed in `tests/fixtures/duplicates-baseline.json`, a group per body: the cleanup of lots 1 to 9 removes them one by one. The list may only shrink. A **new** duplicate, or a group that gains a copy, fails here naming both places; a group that has gone fails too, until it is taken out of the list -- so the list always says what is left, never what was.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import hashlib
import json
import os
from collections import defaultdict

from conftest import ROOT

CALC = ROOT / "calc"
BASELINE = ROOT / "tests" / "fixtures" / "duplicates-baseline.json"
MIN_LINES = 5
UPDATE = os.environ.get("WOODCORE_UPDATE_DUPLICATES") == "1"


def _body_key(node):
    """The function's body as a syntax tree, without its name, its docstring or its positions: two copies that differ only there are one function."""
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if not body:
        return None
    dumped = ast.dump(ast.Module(body=body, type_ignores=[]), annotate_fields=False, include_attributes=False)
    args = ast.dump(node.args, annotate_fields=False, include_attributes=False)
    return hashlib.sha256((args + dumped).encode("utf-8")).hexdigest()[:16]


def _groups():
    """{key: sorted ["calc/x.py:name", ...]} for every body found in two places or more."""
    found = defaultdict(set)
    for path in sorted(CALC.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno - node.lineno + 1 >= MIN_LINES:
                key = _body_key(node)
                if key:
                    found[key].add(f"{rel}:{node.name}")
    return {k: sorted(v) for k, v in found.items() if len(v) > 1}


def test_no_function_is_written_twice_beyond_what_the_baseline_still_lists():
    groups = _groups()
    if UPDATE or not BASELINE.is_file():
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(groups, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return
    held = json.loads(BASELINE.read_text(encoding="utf-8"))
    new = {k: v for k, v in groups.items() if k not in held}
    grown = {k: sorted(set(v) - set(held[k])) for k, v in groups.items() if k in held and set(v) - set(held[k])}
    gone = sorted(k for k in held if k not in groups)
    assert not new, f"a function now written twice -- make one, and call it: {list(new.values())}"
    assert not grown, f"a copy added to a known duplicate: {grown}"
    assert not gone, f"duplicates removed -- take them out of {BASELINE.name} (WOODCORE_UPDATE_DUPLICATES=1): {[held[k] for k in gone]}"
