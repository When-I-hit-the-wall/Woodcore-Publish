"""Every reader of calc/norms/ opens its files through one loader (spec 2026-10-19-base-saine-nettoyage, G3; calc/norms/_loader.py).

Ten modules read the norms' JSON and each wrote its own few lines to open a file, parse it and refuse it -- ten wordings of one refusal. They read through `_loader.load` now: a file missing, unreadable or not JSON is refused naming it, `calc/norms/<name>.json: …`, and a module that opened a file itself would be the copy that ages apart.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast

import conftest
from conftest import ROOT

import validation
from norms import _loader


def test_no_module_of_calc_norms_opens_a_file_itself():
    offenders = []
    for path in sorted((ROOT / "calc" / "norms").glob("*.py")):
        if path.name == "_loader.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("load", "loads", "open", "read_text") \
                    and not (isinstance(node.func.value, ast.Name) and node.func.value.id == "_loader"):
                offenders.append(f"{path.name}:{node.lineno} {ast.unparse(node.func)}")
    assert not offenders, "a norm module reading a file itself -- read it through _loader.load:\n" + "\n".join(offenders)


def test_a_file_missing_or_broken_is_refused_by_its_name():
    folder = conftest.tmpdir("norm_loader")
    for name, text, words in (("absent.json", None, "not found at"), ("broken.json", "{", "is not valid JSON")):
        path = folder / name
        if text is not None:
            path.write_text(text, encoding="utf-8", newline="\n")
        try:
            _loader.load(path)
        except validation.ValidationError as exc:
            assert str(exc).startswith(f"calc/norms/{name}: ") and words in str(exc), str(exc)
        else:
            raise AssertionError(f"{name} was read")
    try:
        _loader.edition("sia261-2020-x", {"edition": "SIA 261:2014"}, "SIA 261:2020")
    except validation.ValidationError as exc:
        assert "calc/norms/sia261-2020-x.json: edition is 'SIA 261:2014' -- expected 'SIA 261:2020'" == str(exc), str(exc)
    else:
        raise AssertionError("the wrong edition was taken")
