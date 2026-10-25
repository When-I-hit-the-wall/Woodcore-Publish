"""The «Formulaire» of the «Domaines» tab off-screen, and its modules on the right (calc/tools/formula_form.py, formula_row.py, formula_new_line.py, formula_modules.py; issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-004 to UI-018, ARCH-002, ARCH-010, ARCH-RISK-008).

Held: a row a line of the file, its number the file's, its values `compute`'s, a field changed written into its line with no other row rebuilt; a click on a variable writes into the calculation that last had the cursor, as it is now, through a redraw (the prototype's defect), and says when there is none; the line at the foot inferred -- «var auto» --, fixed by the pill, written by Enter, given up by Escape; the + between two rows writes there; × and «Annuler» byte for byte; Ctrl+click makes a group, its grip moves it whole, Escape lets it go, a move refused says why and writes nothing; the hovers light what a line uses and what uses it; a message of the state leads to its row; «Résultats», «Variables du domaine», a bubble of the norm pinned and taken off; 200 rows built in reasonable time.
"""

import shutil
import sys
import time

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
        window.resize(1500, 900)
        tab = next(t for t in window.tabs if isinstance(t, formula_tab.FormulaTab))
        window.tab_widget.setCurrentWidget(tab)
        window.show()
        _STATE.update(window=window, tab=tab)
    return _STATE["window"], _STATE["tab"]


def _pump():
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    for _ in range(3):
        QApplication.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _open(tab, text=None, name="panne-p2"):
    """Panne P2 (or `text`) copied into the project of the run and opened."""
    path = project.current().formulas_dir / f"{name}.typ"
    if text is None:
        shutil.copy(FIXTURE, path)
    else:
        path.write_text(text, encoding="utf-8", newline="")
    tab.reload(keep=name)
    tab.set_view("form")
    _pump()
    return path


def _close(tab, path):
    path.unlink(missing_ok=True)
    tab.reload(keep="")


def _item(tab, key):
    return next(i for i, c in enumerate(tab.domain.commands) if c.key == key)


def test_a_row_is_a_line_of_the_file_and_a_field_writes_its_line_alone():
    """UI-005, UI-006, ARCH-RISK-008: Poutre P1's five rows at lines 4 to 8, its values compute's; the value of q_d changed writes its line and rebuilds no other row; a row chosen shows its key, label, norm, clause and description under it."""
    _window, tab = _tab()
    here = project.current()
    original = (here.formulas_dir / "poutre-p1.typ").read_text(encoding="utf-8")
    path = _open(tab, original, "poutre-p1")
    try:
        rows = tab.form.rows
        assert [(r.row.kind, r.row.line) for r in rows] == [("var", 4), ("var", 5), ("eq", 6), ("var", 7), ("verify", 8)]
        assert "14.063 kNm" in rows[2].value.text()
        before = list(rows)
        field = rows[0].field(0, "value")
        field.setText("5")
        field.editingFinished.emit()
        _pump()
        assert '#var("q_d", 5, "kN/m"' in path.read_text(encoding="utf-8")
        assert tab.form.rows == before, "a value changed rebuilt the rows"
        assert "15.625 kNm" in tab.form.rows[2].value.text()
        tab.form.row_clicked(rows[3], _no_modifiers())
        assert rows[3].chosen and not rows[3].detail.isHidden()
        assert {(i, n) for (i, n) in rows[3].fields} >= {(3, "key"), (3, "label"), (3, "norm"), (3, "norm-section"), (3, "descr")}
        key = rows[3].field(3, "norm-section")
        key.setText("4.2.1")
        key.editingFinished.emit()
        _pump()
        assert 'norm-section: "4.2.1"' in path.read_text(encoding="utf-8")
    finally:
        path.write_text(original, encoding="utf-8", newline="")
        tab.reload(keep="")


def _no_modifiers():
    from PySide6.QtCore import Qt
    return Qt.KeyboardModifier.NoModifier


def _ctrl():
    from PySide6.QtCore import Qt
    return Qt.KeyboardModifier.ControlModifier


def test_a_click_writes_into_the_calculation_that_had_the_cursor_through_a_redraw():
    """UI-011 (T41, the prototype's defect): the cursor in M_d's calculation, another row chosen -- and the rows rebuilt --, a click on l in «Variables du domaine» writes `l` where the cursor was, in the field as it is now, the cursor left there; with no calculation being typed, the window says so."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        md = _item(tab, "M_d")
        field = tab.form.field(md, "formula")
        field.setFocus()
        field.setCursorPosition(4)
        tab.form.formula_focused(None, md, "formula", field)
        tab.form.row_clicked(tab.form.rows[3], _no_modifiers())
        tab.form.build()            # a redraw: the field above is gone
        _pump()
        live = tab.form.field(md, "formula")
        assert live is not field
        live.kept = 4
        variables = tab.pane_bodies["variables"]
        clicked = next(label for key, label in variables.entries if key == "l")
        clicked.on_click()
        assert live.text() == "q_d ldot l^2 / 8", live.text()
        assert live.cursorPosition() == 5
        tab.form.target = None
        said = []
        saved = tab.app.set_status
        tab.app.set_status = said.append
        try:
            assert tab.insert_variable("l") is False
        finally:
            tab.app.set_status = saved
        assert said == [tab.t("fm_insert_none")]
    finally:
        _close(tab, path)


def test_the_line_at_the_foot_is_inferred_fixed_written_and_given_up():
    """UI-010, D-11: «h2 = 240 mm» is «var auto» with its symbol, value and unit filled; fixed on eq it says «eq» alone; Enter writes it at the foot; Escape writes nothing."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        foot = tab.form.foot
        foot.text.setText("h_2 = 240 mm")
        foot.refresh()
        assert foot.pill.text().startswith("var " + tab.t("fm_nl_auto"))
        assert {n: f.text() for n, f in foot.fields.items()} == {"symbol": "h_2", "value": "240", "unit": "mm", "label": ""}
        foot.choose("eq")
        assert foot.pill.text().startswith("eq") and tab.t("fm_nl_auto") not in foot.pill.text()
        foot.choose(None)
        before = path.read_text(encoding="utf-8")
        foot.cancel()
        _pump()
        assert path.read_text(encoding="utf-8") == before and foot.text.text() == ""
        foot = tab.form.foot
        foot.text.setText("h_2 = 240 mm")
        foot.refresh()
        foot.commit()
        _pump()
        lines = path.read_text(encoding="utf-8").split("\n")
        assert lines[-3] == '  #var("h_2", 240, "mm")', lines[-4:]
    finally:
        _close(tab, path)


def test_the_plus_between_two_rows_writes_there():
    """UI-008: the + between rows 3 and 4 of Poutre P1, «var», writes the new line as the fourth row."""
    _window, tab = _tab()
    here = project.current()
    original = (here.formulas_dir / "poutre-p1.typ").read_text(encoding="utf-8")
    path = _open(tab, original, "poutre-p1")
    try:
        line = tab.form.open_insert(3, "var")
        assert line.pill.text().startswith("var") and tab.t("fm_nl_auto") not in line.pill.text()
        line.text.setText("k = 2")
        line.refresh()
        line.commit()
        _pump()
        assert [c.key for c in tab.domain.commands] == ["q_d", "l", "M_d", "k", "M_Rd", ""]
        assert tab.form.rows[3].row.line == 7
    finally:
        path.write_text(original, encoding="utf-8", newline="")
        tab.reload(keep="")


def test_a_row_deleted_fails_what_used_it_and_undo_gives_the_file_back():
    """UI-007, D-17: b deleted -- W_y then fails, «b» unknown, said once --; «Annuler» writes the file back byte for byte."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        before = path.read_bytes()
        b = tab.form.row_of(_item(tab, "b"))
        b.delete_button.click()
        _pump()
        assert not tab.undo_bar.isHidden() and tab.undo_text.text() == tab.t("fm_deleted", line=18)
        wy = _item(tab, "W_y")
        assert [m.code for m in tab.state.of_item(wy)] == ["unknown"] and tab.form.row_of(wy).state == "error"
        tab.undo_button.click()
        _pump()
        assert path.read_bytes() == before and tab.undo_bar.isHidden()
    finally:
        _close(tab, path)


def test_a_group_is_moved_whole_by_one_grip_and_a_refused_move_writes_nothing():
    """UI-013, ARCH-010, D-10: Ctrl+click on e, l and γ_G makes a group, its banner and dashed frame; the grip of the second drags the three, moved under γ_Q in their order -- «Annuler» offered --; Escape lets the group go; a drop above what a line uses is refused, the file intact, the sentence said."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        rows = tab.form.rows
        e, l, g = (tab.form.row_of(_item(tab, k)) for k in ("e", "l", "gamma_G"))
        tab.form.row_clicked(e, _no_modifiers())
        tab.form.row_clicked(l, _ctrl())
        tab.form.row_clicked(g, _ctrl())
        assert len(tab.form.selection) == 3 and not tab.form.banner.isHidden() and e.grouped and g.grouped
        assert tab.form.dragged_rows(l) == [e.index, l.index, g.index]
        gq = tab.form.row_of(_item(tab, "gamma_Q"))
        assert tab.write_move_rows(tab.form.dragged_rows(l), gq.index + 1) is True
        _pump()
        keys = [c.key for c in tab.domain.commands if c.key in ("e", "l", "gamma_G", "gamma_Q")]
        assert keys == ["gamma_Q", "e", "l", "gamma_G"], keys
        assert not tab.undo_bar.isHidden()
        from PySide6.QtCore import QEvent, Qt
        from PySide6.QtGui import QKeyEvent
        tab.form.selection.click((tab.form.rows[1].row.first,), [(r.row.first,) for r in tab.form.rows])
        tab.form.selection.click((tab.form.rows[2].row.first,), [(r.row.first,) for r in tab.form.rows], ctrl=True)
        tab.form.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
        assert len(tab.form.selection) == 0 and tab.form.banner.isHidden()
        before = path.read_bytes()
        wy = tab.form.row_of(_item(tab, "W_y"))
        b = tab.form.row_of(_item(tab, "b"))
        assert tab.write_move_rows([wy.index], b.index) is False
        assert path.read_bytes() == before and tab.last_refusal == tab.t("fm_move_refused", user="W_y", used="b")
    finally:
        _close(tab, path)


def test_the_hovers_light_what_a_line_uses_and_what_uses_it():
    """UI-018, REQ-019: η lit, σ_m,d and f_m,d in blue, nothing in green; b lit, W_y in green."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        tab.light(_item(tab, "eta"))
        lit = {tab.domain.commands[r.row.first].key: r.lit for r in tab.form.rows if r.lit}
        assert lit == {"eta": "self", "sigma_m_d": "uses", "f_m_d": "uses"}, lit
        tab.light(_item(tab, "b"))
        lit = {tab.domain.commands[r.row.first].key: r.lit for r in tab.form.rows if r.lit}
        assert lit == {"b": "self", "W_y": "used"}, lit
        tab.light(None)
        assert not [r for r in tab.form.rows if r.lit]
        # a result of «Résultats» hovered lights the same lines, and is lit with them; a line of «Code» hovered too
        results = tab.pane_bodies["results"]
        eta = _item(tab, "eta")
        from PySide6.QtCore import QEvent, QPointF
        from PySide6.QtGui import QEnterEvent
        from PySide6.QtWidgets import QApplication
        # a QEnterEvent, as the window sends: Qt 6 casts every Enter to one, and a bare QEvent read as such crashed the worker now and then (access violation)
        QApplication.sendEvent(results.names[eta], QEnterEvent(QPointF(2, 2), QPointF(2, 2), QPointF(2, 2)))
        lit = {tab.domain.commands[r.row.first].key: r.lit for r in tab.form.rows if r.lit}
        assert lit == {"eta": "self", "sigma_m_d": "uses", "f_m_d": "uses"}, lit
        assert results.names[eta].lit == "self" and results.names[_item(tab, "sigma_m_d")].lit == "uses"
        QApplication.sendEvent(results.names[eta], QEvent(QEvent.Type.Leave))
        assert not [r for r in tab.form.rows if r.lit]
        tab.code_hover(tab.lines[_item(tab, "b")])
        assert tab.code.editor.lit_lines == {18: tab_colour("lit"), 20: tab_colour("link-used")}, tab.code.editor.lit_lines
        tab.code_hover(0)
        assert tab.code.editor.lit_lines == {}
    finally:
        _close(tab, path)


def tab_colour(token):
    import theme
    return theme.colour(token)


def test_the_plus_opens_lier_une_variable_for_its_row():
    """UI-008: «lier une variable…» of the + between two rows opens the window with that row for its target."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        asked = []
        saved = tab.open_link_dialog
        tab.open_link_dialog = lambda row, run=True: asked.append(row)
        try:
            tab.form.open_insert(4, "link")
        finally:
            tab.open_link_dialog = saved
        assert asked == [4]
        dialog = tab.open_link_dialog(4, run=False)
        dialog.click(("snow-load", "SL", "s_k"))
        dialog.validate()
        _pump()
        assert tab.form.rows[4].row.kind == "var" and tab.domain.commands[tab.form.rows[4].row.first].key == "s_k"
    finally:
        _close(tab, path)


def test_a_message_of_the_state_leads_to_its_row():
    """UI-015: a fault on line 13 -- a name unknown in q_d --, its message clicked: row 13 flashes and its field takes the cursor."""
    _window, tab = _tab()
    text = FIXTURE.read_text(encoding="utf-8").replace("gamma_Q dot q_k1) dot e", "gamma_Q dot q_k9) dot e")
    path = _open(tab, text)
    try:
        state = tab.pane_bodies["state"]
        message, label = state.messages[0]
        assert message.line == 13 and tab.say(message).startswith("Ligne 13 de Domains/panne-p2.typ") or tab.app.lang != "fr"
        label.on_click()
        _pump()
        row = tab.form.row_of(message.item)
        assert row.row.line == 13 and row.blinker.active()
    finally:
        _close(tab, path)


def test_results_variables_and_the_norm_s_bubble():
    """UI-016, UI-017, REQ-014: «Résultats» lists every eq and verify, copies their values; «Variables du domaine» says where the linked ones come from -- «↗ Neige · SL» --; a bubble clicked pins its excerpt under the modules, clicked again takes it off."""
    _window, tab = _tab()
    path = _open(tab)
    try:
        results = tab.pane_bodies["results"]
        assert len(results.entries) == sum(1 for c in tab.domain.commands if c.kind in ("eq", "verify"))
        copied = tab.copy_values()
        assert "q_d = 4.238 kN/m" in copied and "M_d = 9.568 kNm" in copied
        assert tab.origin_text(None, tab.domain.commands[_item(tab, "q_k1")]) == tab.t("fm_origin_export", kind=tab.t("fm_group_snow-load"), instance="SL")
        gamma = tab.domain.commands[_item(tab, "gamma_G")]
        excerpt = tab.excerpt_for(gamma.options["norm"], gamma.options["norm-section"])
        assert excerpt is not None and excerpt.id == "tab01"
        tab.pin_excerpt(excerpt.norm, (excerpt.id,))
        assert tab.is_pinned(excerpt.norm, (excerpt.id,)) and tab.pane.order[-1].startswith("x:")
        tab.unpin_excerpt(excerpt.norm, (excerpt.id,))
        assert not tab.is_pinned(excerpt.norm, (excerpt.id,))
    finally:
        _close(tab, path)


def test_two_hundred_rows_are_built_in_reasonable_time():
    """ARCH-RISK-008: a domain of 200 lines -- an unfolded check holds about 40 -- built as rows; the time said, and held under a ceiling that a slow machine keeps."""
    _window, tab = _tab()
    lines = ['#import "/000-Typst-Config/commands.typ": *', "", '#domain("many", label: "Many")['] + [f'  #var("x{i}", {i}, "m")' for i in range(200)] + ["]", ""]
    path = _open(tab, "\n".join(lines), "many")
    try:
        start = time.perf_counter()
        tab.form.build()
        _pump()
        took = time.perf_counter() - start
        assert len(tab.form.rows) == 200
        print(f"200 rows built in {took:.2f} s")
        assert took < 30, took
    finally:
        _close(tab, path)
