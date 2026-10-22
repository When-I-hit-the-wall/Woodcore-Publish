"""Every text file Woodcore writes says its line endings (spec 2026-10-19-base-saine-nettoyage, G1; CLAUDE.md: every text file is LF, on every machine).

Python writes a file opened in text mode with the platform's line ending: on Windows `Path.write_text(text)` turns every "\\n" into "\\r\\n". Until 19.10.2026 that is what 43 writes of calc/ did, `engine.write_json` and `build_examples.py` among them -- every `data/*.json` of an export and the 441 examples came out CRLF on the engineer's machine and LF on the CI's, and a file written on one machine changed every line on the other.

The rule, held here on calc/'s syntax tree: a `write_text(..., encoding=...)` and an `open(..., "w")` in text mode name `newline=`, either "\\n" -- the text written as it is, which makes a new file LF and keeps the line endings of one read with `typst_paths.read_text` -- or "" (the same, written out). The few writers of calc/ that keep a file's own endings (`typst_paths.write_text`, `structure`) take bytes or call these.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast

from conftest import ROOT

ALLOWED = ("\n", "")


def _newline(call):
    for keyword in call.keywords:
        if keyword.arg == "newline":
            return keyword.value.value if isinstance(keyword.value, ast.Constant) else ...
    return None


def _bare_writes():
    found = []
    for path in sorted((ROOT / "calc").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            where = f"{path.relative_to(ROOT).as_posix()}:{node.lineno}"
            if name == "write_text" and any(k.arg == "encoding" for k in node.keywords):
                if _newline(node) not in ALLOWED:
                    found.append(where)
            elif name == "open":
                mode = None
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for keyword in node.keywords:
                    if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                        mode = keyword.value.value
                if isinstance(mode, str) and any(c in mode for c in "wax") and "b" not in mode and _newline(node) not in ALLOWED:
                    found.append(where)
    return found


def test_no_text_file_is_written_without_its_line_endings():
    bare = _bare_writes()
    assert not bare, 'a text write that lets the platform choose its line endings -- add newline="\\n":\n' + "\n".join(bare)


def test_a_json_export_is_lf_on_every_platform():
    import engine
    import conftest
    out = conftest.tmpdir("text_writes") / "x.json"
    engine.write_json(out, {"a": [1, 2]})
    assert b"\r" not in out.read_bytes() and out.read_bytes().endswith(b"}\n")
