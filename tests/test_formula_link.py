"""«Lier une variable…» of the «Domaines» tab off-screen, and the three ways to a link (calc/tools/formula_link_dialog.py, formula_tab.py, calc/domains/formula_links.py; issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-014, REQ-013, ARCH-010, D-5, D-12).

Held: a click chooses one variable without linking it, Ctrl+click adds, Shift+click a range, a box toggles -- the model of the «Variables» tab, calc/variable_select.py --; «Valider (3)» writes three `#var(…, domain: …)` above the row chosen, in the order of the list, in one write «Annuler» takes back; a variable already in the domain greyed; typing «q_k» offers «Neige · SL», whose choice writes the link above; the fix of a message writes the same link; the three ways write the same file.
"""

import shutil
import sys

import conftest
from conftest import ROOT, Skip

import project
from domains import formula_domain as fd

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


def _open(tab, text=None):
    path = project.current().formulas_dir / "panne-p2.typ"
    if text is None:
        shutil.copy(FIXTURE, path)
    else:
        path.write_text(text, encoding="utf-8", newline="")
    tab.reload(keep="panne-p2")
    tab.set_view("form")
    _pump()
    return path


def _close(tab, path):
    path.unlink(missing_ok=True)
    tab.reload(keep="")


def test_three_variables_ticked_and_validated_are_linked_in_one_write():
    """UI-014, D-12, ARCH-010: a click chooses one without linking it; Ctrl+click, Shift+click; «Valider (3)» writes three links above the row chosen, in the order of the list; «Annuler» takes them all back; a variable already in the domain is greyed."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        before = path.read_bytes()
        e_row = tab.form.row_of(next(i for i, c in enumerate(tab.domain.commands) if c.key == "e"))
        tab.form.row_clicked(e_row, _no_modifiers())
        dialog = tab.open_link_dialog(None, run=False)
        shown = dialog.shown_keys()
        snow = [k for k in shown if k[0] == "snow-load" and k[1] == "SL"]
        assert len(snow) >= 3, snow
        taken = dialog.items[("snow-load", "SL", "q_k1")]
        from PySide6.QtCore import Qt
        assert not (taken.flags() & Qt.ItemFlag.ItemIsUserCheckable) and taken.text(3) == tab.t("fm_pick_has")
        dialog.click(snow[0])
        assert len(dialog.selection) == 1 and path.read_bytes() == before, "a click chose and linked"
        dialog.click(snow[2], shift=True)
        assert len(dialog.selection) == 3
        dialog.click(snow[1], ctrl=True)
        dialog.click(snow[1], box=True)
        assert len(dialog.selection) == 3 and dialog.ok.text() == tab.t("fm_pick_ok", n=3)
        dialog.validate()
        _pump()
        keys = [c.key for c in tab.domain.commands if c.source and c.source[0] == "domain" and c.source[1] == ("snow-load", "SL")]
        assert keys[1:] == [k[2] for k in snow[:3]] or keys == ["q_k1"] + [k[2] for k in snow[:3]], keys
        at = next(i for i, c in enumerate(tab.domain.commands) if c.key == "e")
        assert [c.key for c in tab.domain.commands[at - 3:at]] == [k[2] for k in snow[:3]]
        assert not tab.undo_bar.isHidden()
        tab.write_undo()
        assert path.read_bytes() == before
    finally:
        _close(tab, path)


def test_the_name_typed_the_window_and_the_fix_write_the_same_link():
    """REQ-013 (a, b, c): «s_k» typed in a calculation offers «Neige · SL» and its choice writes `#var("s_k", domain: ("snow-load", "SL"))` above the line; the fix of the message of the name unknown writes the same; and the window: the three files are the same."""
    _window, tab = _tab()
    text = FIXTURE.read_text(encoding="utf-8").replace("`q_d dot l^2 / 8`", "`q_d dot l^2 / 8 + 0 * s_k`")
    files = []
    try:
        # (c) the fix of the message
        path = _open(tab, text)
        message = next(m for m in tab.state.errors if m.fix)
        assert tab.say_fix(message.fix) == tab.t("fm_fix_link", var="s_k", source=tab.t("fm_origin_export", kind=tab.t("fm_group_snow-load"), instance="SL").lstrip("↗ "))
        tab.apply_fix(message)
        files.append(path.read_text(encoding="utf-8"))
        assert '#var("s_k", domain: ("snow-load", "SL"))' in files[-1]
        # (a) the name typed
        path = _open(tab, text)
        md = next(i for i, c in enumerate(tab.domain.commands) if c.key == "M_d")
        field = tab.form.field(md, "formula")
        field.setText("q_d dot l^2 / 8 + 0 * s_k")
        field.setCursorPosition(len(field.text()))
        field.complete_fill("s_k")
        offered = [e for e in field.completer_.model().stringList() if "SL" in e and e.startswith("s_k")]
        assert offered, field.completer_.model().stringList()[:5]
        field.complete_choose(offered[0])
        _pump()
        files.append(path.read_text(encoding="utf-8"))
        # (b) the window
        path = _open(tab, text)
        tab.form.row_clicked(tab.form.row_of(next(i for i, c in enumerate(tab.domain.commands) if c.key == "M_d")), _no_modifiers())
        dialog = tab.open_link_dialog(None, run=False)
        dialog.click(("snow-load", "SL", "s_k"))
        dialog.validate()
        _pump()
        files.append(path.read_text(encoding="utf-8"))
        assert files[0] == files[1] == files[2], "the three ways wrote different files"
        lines = files[0].split("\n")
        assert lines.index('  #var("s_k", domain: ("snow-load", "SL"))') == next(i for i, l in enumerate(lines) if l.startswith('  #eq("M_d"')) - 1
    finally:
        _close(tab, project.current().formulas_dir / "panne-p2.typ")


def _no_modifiers():
    from PySide6.QtCore import Qt
    return Qt.KeyboardModifier.NoModifier
