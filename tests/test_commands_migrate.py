"""The report commands renamed or taken away in v0.120, and a project's sections taken to the new ones (spec 2026-10-19-base-saine-nettoyage, REQ-001, REQ-002, D-13; calc/domains/commands_migrate.py, calc/renamed-commands.json).

Thirteen `*-ids` became `ids(kind)`, eight `get-*` became `get(v, field)`, the two load summaries became `show-load-summary(unit:)`, two commands were taken away. The engineer's sections call the old names: they are rewritten once when the project is opened, every file saved into the archives first, and an export of a project that still calls one stops naming the file and the replacement. No file of the engine, the templates or the example project calls an old name, and no button of the window copies one (spec 2026-10-21-commandes-typst-refonte, UI-002).
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import shutil

import conftest
from conftest import ROOT

from domains import commands_migrate as cm


def test_a_call_keeps_its_arguments_and_takes_the_new_name():
    cases = {
        "#for id in position-ids() { x }": '#for id in ids("position") { x }',
        "#instance-ids(\"snow-load\")": '#ids("snow-load")',
        "#let q = get-value(v)": '#let q = get(v, "value")',
        # a command taken away is left as it is written, and said (spec 2026-10-21-commandes-typst-refonte, REQ-020)
        "#show-line-load-summary(title: \"L\")": '#show-line-load-summary(title: "L")',
        ".map(get-norm-ref)": '.map((v => get(v, "norm_ref")))',
        "#let n = -get-symbol(v).len()": '#let n = -get(v, "symbol").len()',
        "#my-get-value(x)": "#my-get-value(x)",
    }
    for before, after in cases.items():
        assert cm.rewrite(before)[0] == after, (before, cm.rewrite(before)[0])


def test_an_import_takes_the_new_name_once_and_a_quoted_call_is_escaped():
    text, notes, unresolved = cm.rewrite('#import "/x.typ": a, get-value, get-unit, position-ids, show-plan-legend\n')
    assert text == '#import "/x.typ": a, get, ids\n', text
    assert [name for name, _hint in unresolved] == ["show-plan-legend"]
    text, _notes, _unresolved = cm.rewrite('panic("write #val(get-value(v))")')
    assert text == 'panic("write #val(get(v, \\"value\\"))")', text


def test_a_command_taken_away_is_left_and_said_with_what_to_write():
    text, notes, unresolved = cm.rewrite('#show-plan-legend("EG")\n#moisture-class-of("S1")\n')
    assert text == '#show-plan-legend("EG")\n#moisture-class-of("S1")\n'
    assert [name for name, _ in unresolved] == ["show-plan-legend", "moisture-class-of"]
    assert all(hint for _name, hint in unresolved)


def test_every_new_name_is_a_command_of_the_engine_and_no_old_one_is():
    table = cm.table()
    commands = json.loads((ROOT / "calc" / "i18n" / "commands.json").read_text(encoding="utf-8"))["commands"]
    for old, rule in table.items():
        assert old not in commands, f"{old} is still documented as a command"
        if "to" in rule:
            assert rule["to"] in commands, f"{old} becomes {rule['to']}, which is no command"


def test_no_file_of_the_engine_the_templates_or_the_example_calls_an_old_name():
    files = [*(ROOT / "lib").glob("*.typ"), *(ROOT / "templates").rglob("*.typ"),
             *(p for p in (ROOT / "tests" / "projet-exemple").rglob("*.typ") if "_woodcore" not in p.parts)]
    calling = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        after, notes, unresolved = cm.rewrite(text)
        if after != text or unresolved:
            calling.append(f"{path.relative_to(ROOT).as_posix()}: {notes or unresolved}")
    assert not calling, "\n".join(calling)


def test_no_button_copies_a_retired_command():
    """UI-002 (spec 2026-10-21-commandes-typst-refonte): no «Copier» button, option panel or word of the window writes a command this table retires -- every string of the window's modules and of the call builders read outside their docstrings, and every command an «Affichage» panel builds (display_options.SPECS). `rewrite_documents.py`, the one-off tool that took the templates *from* the old forms (lot 18), is left out."""
    import ast
    import re
    import sys
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import display_options
    retired = set(cm.table())
    # a call, and not an English plural -- «{count} schema(s) moved»
    called = re.compile(r"(?<![A-Za-z0-9_.-])(" + "|".join(re.escape(n) for n in sorted(retired, key=len, reverse=True)) + r")\((?!s\))")
    files = [p for p in sorted((ROOT / "calc" / "tools").glob("*.py")) if p.name != "rewrite_documents.py"]
    files += [ROOT / "calc" / name for name in ("build_reference.py", "build_reference_calls.py", "build_reference_lib.py")]
    found = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                      if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body
                      and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                found += [f"{path.relative_to(ROOT).as_posix()}:{node.lineno}: {m.group(1)}(" for m in called.finditer(node.value)]
    assert not found, "a string of the window writes a retired command:\n" + "\n".join(found)
    assert not set(display_options.SPECS) & retired, sorted(set(display_options.SPECS) & retired)


def test_a_project_is_migrated_once_its_files_saved_first_and_an_export_refuses_what_is_left():
    here = conftest.project_copy("commands_migrate", data=True)
    section = here.typst_root / "Old.typ"
    section.write_text('#for id in position-ids() { [#id] }\n#get-value(v)\r\n', encoding="utf-8", newline="")
    message = cm.refusal(here)
    assert message and "Old.typ" in message and "position-ids" in message, message
    changes = cm.migrate(here)
    assert [c.path.name for c in changes] == ["Old.typ"], [c.path for c in changes]
    assert section.read_bytes() == b'#for id in ids("position") { [#id] }\n#get(v, "value")\r\n', "the line endings are the file's own"
    saved = list((here.archives_dir).rglob("commands-migration-*/Old.typ"))
    assert len(saved) == 1 and b"position-ids" in saved[0].read_bytes(), saved
    assert cm.migrate(here) == [] and cm.refusal(here) is None, "a second run changes nothing"
    section.write_text('#show-plan-legend("EG")\n', encoding="utf-8", newline="")
    message = cm.refusal(here)
    assert message and "show-plan-legend" in message and "detail-legend" in message, message
    shutil.rmtree(saved[0].parent, ignore_errors=True)


def test_an_argument_taken_away_is_said_with_its_file_and_line_and_never_rewritten():
    """Spec 2026-10-21-commandes-typst-refonte, REQ-020, ARCH-006, CON-004: «la migration n'est pas nécessaire, il suffit d'avoir un message d'alerte». A command that stays and loses an argument is the table's `arguments` section; a call that still writes it is said at its file and line -- by the window when the project is opened (`removals`), by the export, which refuses it -- and the file is left exactly as the engineer wrote it."""
    taken = {"var": {"own": "write the value without domain: to keep it"}}
    found = cm.argument_calls('#var("a", 1)\n// #var("b", 2, own: true)\n#var("c", 3, "kN", domain: "d", own: true)\n', taken)
    assert [(name, argument) for name, argument, _hint, _at in found] == [("var", "own")], "the call in a comment calls nothing"
    assert json.loads((ROOT / "calc" / "renamed-commands.json").read_text(encoding="utf-8"))["schema_version"] == "1.1"
    here = conftest.project_copy("commands_migrate_arguments", data=True)
    section = here.typst_root / "Kept.typ"
    text = '#show-plan-legend("EG")\n\n#show-plan-legend("OG")\n'
    section.write_text(text, encoding="utf-8", newline="")
    removals = cm.removals(here)
    assert [(path.name, line, name) for path, line, name, _hint in removals] == [("Kept.typ", 1, "#show-plan-legend"), ("Kept.typ", 3, "#show-plan-legend")], removals
    message = cm.refusal(here)
    assert message and "Kept.typ:1:" in message and "#show-plan-legend is no longer a command" in message, message
    assert cm.migrate(here) == [] and section.read_text(encoding="utf-8") == text, "what was taken away is never rewritten"
    original = cm.removed_arguments
    try:
        cm.removed_arguments = lambda: taken
        section.write_text('#var("a", 1)\n#var("c", 3, "kN", own: true)\n', encoding="utf-8", newline="")
        message = cm.refusal(here)
        assert message and "Kept.typ:2:" in message and "#var(own:) is no longer an argument of its command" in message, message
    finally:
        cm.removed_arguments = original


def test_the_old_arguments_of_distance_are_said_with_what_to_write():
    """REQ-016 (spec 2026-10-21-commandes-typst-refonte): `#distance` takes `table:`, `label:` and `norm-section:`; a call still writing `tab:`, `title:` or `norm-ref:` -- read by Typst until they go -- is said with its replacement, from the one table."""
    found = cm.argument_calls('#distance(12, "dowel", tab: 24, title: none, norm-ref: "Tabelle 24")\n#distance(12, "dowel", table: 24, label: none, norm-section: "Tabelle 24")\n')
    said = {argument: hint for name, argument, hint, _at in found if name == "distance"}
    assert set(said) == {"tab", "title", "norm-ref"}, said
    assert "table:" in said["tab"] and "label:" in said["title"] and "norm-section:" in said["norm-ref"], said


def test_a_unit_without_its_scope_is_said_at_its_line_and_never_rewritten():
    """Spec 2026-10-21-commandes-typst-refonte, CON-007: `#unit` reached the rest of the document until its `scope:` existed, and now reaches the next answer of its dimension -- a call written before is said where it stands, never rewritten, and never refused."""
    assert cm.unscoped_units('#unit("N")\n#unit("kNm", scope: "domain")\n// #unit("x")\n') == [1]
    here = conftest.project_copy("commands_migrate_unit", data=True)
    section = here.typst_root / "Units.typ"
    text = '= A\n#unit("N")\n#unit("N", scope: "document")\n'
    section.write_text(text, encoding="utf-8", newline="")
    assert [(path.name, line) for path, line in cm.unit_scope_notes(here)] == [("Units.typ", 2)]
    assert cm.refusal(here) is None and section.read_text(encoding="utf-8") == text
