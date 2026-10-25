"""«Code» of the «Domaines» tab off-screen, and the module «Arguments de la ligne» (calc/tools/formula_code.py, code_editor.py, formula_modules.py; issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-012, UI-015, UI-019, REQ-007, REQ-012, ARCH-016).

Held: the cursor on a `#verify` says verify, on line 13 an eq and its 17 arguments, «eq · Domains/panne-p2.typ:13»; `display-formula: "value"` written into the line by one edit, the cursor kept, *auto* taking it out; the right margin the result `compute` gives, a fault's number red; a parenthesis forgotten leaves the file as it was, said at Typst's line; each mode writes the file and the others read it; in «Formulaire» the module offers the other arguments.
"""

import shutil
import sys

import conftest
from conftest import ROOT, Skip

import project

TOOLS = ROOT / "calc" / "tools"
FIXTURE = ROOT / "tests" / "fixtures" / "domains" / "panne-p2.typ"
_STATE = {}


def _tab():
    if "tab" not in _STATE:
        if str(TOOLS) not in sys.path:
            sys.path.insert(0, str(TOOLS))
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        QApplication.instance() or QApplication([])
        import woodcore_gui
        import formula_tab
        window = woodcore_gui.MainWindow()
        tab = next(t for t in window.tabs if isinstance(t, formula_tab.FormulaTab))
        window.tab_widget.setCurrentWidget(tab)
        _STATE.update(window=window, tab=tab)
    return _STATE["window"], _STATE["tab"]


def _pump():
    from PySide6.QtWidgets import QApplication
    for _ in range(3):
        QApplication.processEvents()


def _open(tab, view="code"):
    path = project.current().formulas_dir / "panne-p2.typ"
    shutil.copy(FIXTURE, path)
    tab.reload(keep="panne-p2")
    tab.set_view(view)
    _pump()
    return path


def _close(tab, path):
    tab.set_view("form")
    path.unlink(missing_ok=True)
    tab.reload(keep="")


def _cursor(tab, line):
    tab.code.editor.select_line(line)
    tab.code_cursor(line)
    _pump()


def test_the_command_of_the_cursor_and_all_its_arguments():
    """UI-012, UI-019, D-13: line 25 a verify, line 13 an eq whose 17 arguments are listed, «eq · Domains/panne-p2.typ:13»; a text says it has none."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        _cursor(tab, 25)
        args = tab.pane_bodies["args"]
        assert tab.args_context()[2].kind == "verify"
        _cursor(tab, 13)
        assert len(args.fields) == 17 and "eq" in args.head.text() and "Domains/panne-p2.typ:13" in args.head.text()
        _cursor(tab, 5)
        assert tab.args_context() == tab.t("fm_a_text", line=5)
    finally:
        _close(tab, path)


def test_an_argument_is_written_into_the_line_by_one_edit_the_cursor_kept():
    """UI-012, ARCH-016: `display-formula: "value"` on line 13 written into that line alone, the cursor where it was; *auto* takes it out."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        _cursor(tab, 13)
        cursor = tab.code.editor.textCursor()
        cursor.setPosition(tab.code.editor.document().findBlockByNumber(12).position() + 5)
        tab.code.editor.setTextCursor(cursor)
        position = tab.code.editor.textCursor().position()
        index = tab.args_context()[0]
        assert tab.write_argument(index, "display-formula", "value") is True
        lines = path.read_text(encoding="utf-8").split("\n")
        assert lines[12].endswith('norm-section: "4.4.3.4", display-formula: "value")'), lines[12]
        assert tab.code.editor.textCursor().position() == position
        before = FIXTURE.read_text(encoding="utf-8").split("\n")
        assert [l for i, l in enumerate(lines) if i != 12] == [l for i, l in enumerate(before) if i != 12]
        _cursor(tab, 13)
        tab.write_argument(tab.args_context()[0], "display-formula", "")
        assert path.read_text(encoding="utf-8") == FIXTURE.read_text(encoding="utf-8")
    finally:
        _close(tab, path)


def test_the_margins_say_each_line_s_result_and_a_fault_s_number_is_red():
    """UI-019: the right margin of line 13 «= 4.238 kN/m», of line 25 «✔ 9.967 …»; a fault's number red."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        assert tab.code_margin(13) == (None, "= 4.238 kN/m")
        token, note = tab.code_margin(25)
        assert note.startswith("✔ 9.967 N/mm²") and "11.28 N/mm²" in note
        text = tab.code.text().replace("gamma_Q dot q_k1) dot e", "gamma_Q dot q_k9) dot e")
        tab.code.editor.setPlainText(text)
        tab.code.flush()
        _pump()
        assert tab.code_margin(13)[0] == "danger"
        assert tab.code_margin(14)[0] == "muted", "a line that only inherits the fault is no fault of its own"
    finally:
        _close(tab, path)


def test_a_parenthesis_forgotten_writes_nothing_and_is_said_at_typst_s_line():
    """REQ-012, REQ-007, ARCH-016: the `)` of line 19 forgotten in the buffer -- the file of before intact, the state at line 19, column 6, the number red."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        before = path.read_bytes()
        text = tab.code.text().replace('label: "Hauteur")', 'label: "Hauteur"')
        tab.code.editor.setPlainText(text)
        assert tab.write_code(text) is False
        assert path.read_bytes() == before
        assert [(m.code, m.line, m.col) for m in tab.state.errors] == [("read_unclosed", 19, 6)]
        assert tab.code_margin(19)[0] == "danger"
        _cursor(tab, 19)
        assert tab.args_context() == tab.t("fm_a_broken", line=19)
    finally:
        _close(tab, path)


def test_each_mode_writes_the_file_and_the_others_read_it():
    """REQ-012, UI-001: a value changed in «Code» is the form's; a value changed in the form is the buffer's; the file is what both say."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        text = tab.code.text().replace('#var("h", 240, "mm"', '#var("h", 260, "mm"')
        tab.code.editor.setPlainText(text)
        tab.code.flush()
        _pump()
        assert '#var("h", 260, "mm"' in path.read_text(encoding="utf-8")
        tab.set_view("form")
        h = next(i for i, c in enumerate(tab.domain.commands) if c.key == "h")
        field = tab.form.field(h, "value")
        assert field.text() == "260"
        field.setText("250")
        field.editingFinished.emit()
        _pump()
        tab.set_view("code")
        assert '#var("h", 250, "mm"' in tab.code.text() and '#var("h", 250, "mm"' in path.read_text(encoding="utf-8")
        tab.set_view("form")
        tab.form.row_clicked(tab.form.row_of(h), _no_modifiers())
        assert [name for name in tab.pane_bodies["args"].fields] == ["display", "label-position", "descr-position", "norm-position", "style", "role", "level"]
    finally:
        _close(tab, path)


def _no_modifiers():
    from PySide6.QtCore import Qt
    return Qt.KeyboardModifier.NoModifier
