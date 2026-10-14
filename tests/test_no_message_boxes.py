"""No message box for an error, a warning or an information (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-009).

The engineer, 07.10.2026: «Il ne doit plus y avoir de : MessageBox / Erreur ! / Exception... qui interrompent brutalement l'utilisateur. Toutes les erreurs doivent être centralisées dans le système global de notifications d'erreurs de Woodcore». A module says what went wrong with `notices_ui.tell` (or calc/notifications.py), a dialog says it in its own band (`notices_ui.inline_error`). What stays a box is a **decision** that waits for its answer -- `QMessageBox.question`, or a box built with its buttons -- and such a box says so on its line: `# dialog-ok: <why>`. Read in the source, as tests/test_no_console.py reads the processes: a box added tomorrow fails here, naming its file and line.
"""

import ast

from conftest import ROOT

KINDS = {"warning", "critical", "information"}
ICONS = {"Warning", "Critical", "Information"}


def _boxes(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    found = []
    for node in ast.walk(ast.parse(text)):
        # QMessageBox.warning, .critical, .information -- called, or only named: `(QMessageBox.warning if bad else QMessageBox.information)(...)` is a box too (the verification of 08.10.2026 found one in migrate_dialog)
        if isinstance(node, ast.Attribute) and node.attr in KINDS and isinstance(node.value, ast.Name) and node.value.id == "QMessageBox":
            found.append((node.lineno, f"QMessageBox.{node.attr}"))
            continue
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # QMessageBox(QMessageBox.Icon.Warning, ...) -- a box built by hand
        if isinstance(func, ast.Name) and func.id == "QMessageBox":
            icons = [a for a in ast.walk(node) if isinstance(a, ast.Attribute) and a.attr in ICONS
                     and isinstance(a.value, ast.Attribute) and a.value.attr == "Icon"]
            if icons and "dialog-ok:" not in lines[node.lineno - 1]:
                found.append((node.lineno, "QMessageBox(Icon...) without # dialog-ok"))
    return found


def test_no_module_of_the_window_opens_a_box_for_an_error_a_warning_or_an_information():
    found = []
    for path in sorted((ROOT / "calc" / "tools").glob("*.py")):
        found += [f"{path.name}:{line}: {what}" for line, what in _boxes(path)]
    assert not found, "say it with notices_ui.tell (or inline_error in a dialog), or mark a decision # dialog-ok:\n" + "\n".join(found)


def test_the_lint_sees_a_box_and_lets_a_decision_marked_as_such_through(tmp=None):
    import conftest
    folder = conftest.tmpdir("no-message-boxes")
    probe = folder / "probe.py"
    probe.write_text(
        "from PySide6.QtWidgets import QMessageBox\n"
        "QMessageBox.warning(None, 'W', 'x')\n"
        "QMessageBox(QMessageBox.Icon.Information, 'W', 'x')\n"
        "QMessageBox(QMessageBox.Icon.Question, 'W', 'x')\n"
        "QMessageBox(QMessageBox.Icon.Warning, 'W', 'x')  # dialog-ok: a decision\n"
        "QMessageBox.question(None, 'W', 'x')\n"
        "(QMessageBox.warning if True else QMessageBox.information)(None, 'W', 'x')\n", encoding="utf-8")
    assert sorted({line for line, _what in _boxes(probe)}) == [2, 3, 7], "a box named in an expression is found too"
