"""The «Formules» tab, built off-screen in a window on the example project (calc/tools/formula_tab.py; specs docs/requirements/completed/2026-10-08-onglet-formule-domaines.md, UI-001 to UI-007, REQ-010, and docs/requirements/completed/2026-10-08-onglet-formules-editeur-dossiers-include.md, issue #15).

Held: the tab is in *Référence*, first, named «Formules / Formeln / Formulas», with its icon; the left pane is every tab's list (grouped_list.GroupedList) -- the domains and what each holds, folders kept in Woodcore-Datei/lists.json and never as directories, «Archives», a duplicate, the order dropped -- and makes no domain; a domain is made from the right, its name typed on the first line, its ID made from it until it is written, and written on Enter; an ID changed renames the file and lists what still cites the old one; a block is written in fields, Tab going from one to the next, Enter -- or a click elsewhere in the middle -- validating, the file then holding the call, and leaves no ghost of its fields; an equation opened again keeps its name; a single click on a block validated shows its options, which are written as they change; Typst of the engineer's own between the blocks is written as typed, a command added where its cursor stands, what the file would not read back refused; the right pane is one column -- the variables, the options, the domain's card, the commands --; «Affichage» offers `#include "/Formules/<id>.typ"`; the writers are refused in a project opened read-only.
"""

import json
import os
import sys

import conftest
from conftest import ROOT, Skip

import list_order
import project
from domains import formula_domain as fd
from domains import unfold

TOOLS = ROOT / "calc" / "tools"
_STATE = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _tab():
    if "tab" not in _STATE:
        _qt()
        import woodcore_gui
        import formula_tab
        window = woodcore_gui.MainWindow()
        tab = next(t for t in window.tabs if isinstance(t, formula_tab.FormulaTab))
        _STATE.update(window=window, tab=tab)
    return _STATE["window"], _STATE["tab"]


def _pump():
    from PySide6.QtWidgets import QApplication
    for _ in range(3):
        QApplication.processEvents()


def _flush():
    """deleteLater is not run by processEvents: the posted deletions are sent explicitly, so a test sees what the window shows."""
    from PySide6.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _cleanup(tab, name):
    here = project.current()
    for domain in fd.list_domains(here):
        if domain.name == name:
            fd.remove(here, domain)
    tab.reload(keep="")


def _new(tab, name):
    _cleanup(tab, name)
    tab.new_domain()
    tab.name_edit.setText(name)
    tab.name_done()
    return project.current().formulas_dir / f"{tab.current_id}.typ"


def _var(tab, key, value, unit=""):
    tab.add_block("var")
    block = tab.open_block
    block.fields["key"].setText(key)
    block.fields["value"].setText(str(value))
    block.fields["unit"].setText(unit)
    block.validate()
    return block


def _said(tab):
    said = []
    tab.fail = lambda message: said.append(message) or False
    return said


def test_the_tab_is_first_in_reference_in_three_languages_with_its_icon():
    _qt()
    import chrome
    import formula_tab
    import grouped_list
    import woodcore_gui
    keys = [key for key, _factory in woodcore_gui.TABS]
    assert "tab_formula" in keys and "tab_dsl" not in keys
    assert dict(woodcore_gui.NAV_GROUPS)["nav_reference"][0] == "tab_formula"
    assert all("tab_formula" in woodcore_gui.MODE_TABS[mode] for mode in ("cu", "bp", "rs"))
    assert "tab_formula" in chrome.ICONS
    words = [set(formula_tab.STRINGS[lang]) for lang in ("fr", "de", "en")]
    assert words[0] == words[1] == words[2], sorted(words[0] ^ words[1] | words[0] ^ words[2])
    # issue #15, UI-001, renamed by issue #64 (UI-001): «Domaines / Domänen / Domains»
    assert [woodcore_gui.STRINGS[lang]["tab_formula"] for lang in ("fr", "de", "en")] == ["Domaines", "Domänen", "Domains"]
    assert not [k for lang in ("fr", "de", "en") for k, v in formula_tab.STRINGS[lang].items() if "show-formula" in v], "a word of the tab still names #show-formula"
    own = {k: v for c in reversed(woodcore_gui.own_classes(formula_tab.FormulaTab)) for k, v in vars(c).items()}  # the class and its mixins (issue #30)
    for name in woodcore_gui.WRITERS:
        if name in own:
            assert hasattr(getattr(formula_tab.FormulaTab, name), "__wrapped__"), f"FormulaTab.{name} is not refused in a project opened read-only"
    for name in ("save", "delete", "duplicate_domain", "rename_id", "write_text", "write_options"):
        assert name in woodcore_gui.WRITERS and name in own, name
    # ARCH-001: one kernel -- the list is every tab's GroupedList, no tree of the tab's own
    _window, tab = _tab()
    assert isinstance(tab.list, grouped_list.GroupedList)


def test_the_left_pane_lists_the_domains_and_what_each_holds_and_makes_none():
    _window, tab = _tab()
    tab.reload()
    item = tab.list._item_for("poutre-p1")
    assert item is not None and item.text(0) == "Poutre P1"
    assert item.childCount() == 5 and "M_d = 14.063 kNm" in [item.child(i).text(0) for i in range(5)]
    tab.on_tree_clicked(item)
    assert tab.domain.id == "poutre-p1" and len(tab.blocks) == 5 and tab.var_list.topLevelItemCount() == 4
    assert len(tab.zones) == 1 and [kind for p in tab.zones[0].paragraphs() for kind, _v in p].count("cmd") == 5, "one text, a pill for each command (issue #40)"
    # making a domain is the right pane's (D-01 of v0.117): nothing on the left makes one
    from PySide6.QtWidgets import QPushButton
    assert not [b for b in tab.list.parentWidget().findChildren(QPushButton)], "the left pane offers a button"


def test_a_domain_is_named_on_its_first_line_its_id_made_from_it_and_written_on_enter():
    _window, tab = _tab()
    _cleanup(tab, "Essai A")
    tab.new_domain()
    assert tab.current_id is None
    tab.name_edit.setText("Essai A")
    tab.name_typed("Essai A")
    assert tab.id_edit.text() == "essai-a", "the ID does not follow the name before the first write"
    tab.name_done()
    assert tab.current_id == "essai-a" and "commands" in tab.right_cards()
    path = project.current().formulas_dir / "essai-a.typ"
    read = fd.read(path)
    assert path.is_file() and read.name == "Essai A" and read.declared == "essai-a"
    assert '#domain("essai-a", label: "Essai A")[' in path.read_text(encoding="utf-8")
    # a name changed once the domain is written renames nothing: the ID is the file's (REQ-004)
    tab.name_edit.setText("Essai A bis")
    tab.name_done()
    assert tab.current_id == "essai-a" and fd.read(path).name == "Essai A bis"
    # two domains may bear one name: the id tells them apart (D-06)
    _cleanup(tab, "Essai A bis")


def test_an_id_changed_renames_the_file_and_one_that_is_no_id_is_refused():
    window, tab = _tab()
    path = _new(tab, "Essai I")
    _var(tab, "F", 5, "kN")
    old_id = tab.current_id
    tab.list.drop_ids([old_id], None, "Essais")
    tab.list.drop_ids([old_id], tab.list._item_for(old_id), "Essais")
    place = list_order.tab_of(list_order.read(project.current()), tab.KEY)[0].index(old_id)
    section = project.current().typst_root / "probe-cite.typ"
    section.write_text(f'#include "/Domains/{tab.current_id}.typ"\n', encoding="utf-8")
    import notices_ui
    told = []
    saved_tell = notices_ui.tell
    notices_ui.tell = lambda message, *a, **k: told.append(message)
    said = _said(tab)
    try:
        tab.id_edit.setText("Essai I")
        tab.id_done()
        assert said and "Essai I" in said[0] and path.is_file(), said
        tab.id_edit.setText("poutre-p1")
        tab.id_done()
        assert "poutre-p1" in said[-1] and path.is_file(), said
        tab.id_edit.setText("essai-i2")
        tab.id_done()
    finally:
        notices_ui.tell = saved_tell
        del tab.fail
        section.unlink(missing_ok=True)
    new = project.current().formulas_dir / "essai-i2.typ"
    assert tab.current_id == "essai-i2" and new.is_file() and not path.exists()
    order, groups = list_order.tab_of(list_order.read(project.current()), tab.KEY)
    assert "essai-i" not in order and "essai-i" not in groups
    assert groups.get("essai-i2") == "Essais" and order.index("essai-i2") == place, (order, groups)
    assert tab.list._item_for("essai-i2").parent().text(0) == "Essais"
    tab.app.list_store.forget(tab.KEY, ["essai-i2"])
    assert '#domain("essai-i2", label: "Essai I")[' in new.read_text(encoding="utf-8")
    assert told and "probe-cite.typ:1" in told[0], told
    _cleanup(tab, "Essai I")


def test_blocks_are_written_in_fields_validated_on_enter_and_shown_as_what_matters():
    _window, tab = _tab()
    path = _new(tab, "Essai B")
    # a variable: its key made from the shown variable where none is typed (REQ-008)
    tab.add_block("var")
    block = tab.open_block
    assert block.editing and list(block.fields) == ["symbol", "key", "value", "unit"], "the shown variable first (issue #40, REQ-005)"
    block.fields["symbol"].setText("F_(E,d)")
    block.fields["value"].setText("12")
    block.fields["unit"].setText("kN")
    block.validate()
    assert not block.editing
    assert '#var("F_E_d", "F_(E,d)", 12, "kN")' in path.read_text(encoding="utf-8")
    # an equation typed with units, its output unit chosen on the right (REQ-009, T21)
    tab.add_block("eq")
    block = tab.open_block
    assert "options" in tab.right_cards() and tab.unit_box is not None
    block.fields["symbol"].setText("m")
    block.fields["formula"].setText("12 N / 3000 mm")
    block.validate()
    assert '#eq("m", `(12 "N") / (3000 "mm")`)' in path.read_text(encoding="utf-8"), "a key that reads as a unit is kept as typed (issue #32)"
    assert abs(block.result.value - 0.004) < 1e-12 and block.result.unit == "kN/m"
    # a click on a variable writes it into the formula being typed (REQ-010)
    tab.add_block("eq")
    block = tab.open_block
    block.fields["symbol"].setText("V")
    tab.on_field_focused(block.fields["formula"])
    item = next(tab.var_list.topLevelItem(i) for i in range(tab.var_list.topLevelItemCount())
                if tab.var_list.topLevelItem(i).data(0, 256) == "F_E_d")
    tab.on_variable_clicked(item)
    assert block.fields["formula"].text() == "F_(E,d)"
    block.fields["formula"].setText(block.fields["formula"].text() + " + 1 m")
    before = path.read_text(encoding="utf-8")
    block.validate()
    assert block.editing and not block.error.isHidden() and "cannot add" in block.error.text(), block.error.text()
    assert path.read_text(encoding="utf-8") == before
    block.fields["formula"].setText("F_(E,d) * 2")
    block.validate()
    assert "#eq(\"V\", `F_E_d * 2`)" in path.read_text(encoding="utf-8")
    # a double-click on its pill opens it again, on a line of its own (D-04); Escape gives up
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    window = tab.app
    window.show()
    window.tab_widget.setCurrentWidget(tab)
    _pump()
    # brought to the front, the tab reads its domains again (on_shown) and its blocks are new: the one of `V` is found again
    block = next(b for b in tab.blocks if not b.command.is_text and b.command.key == "V")
    zone = tab.zones[0]
    centre = QPointF(zone.pill_rect(block.uid).center())
    event = QMouseEvent(QEvent.Type.MouseButtonDblClick, centre, centre, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    zone.mouseDoubleClickEvent(event)
    window.hide()
    assert block.editing and tab.open_block is block and block.fields["formula"].text() == "F_(E,d) * 2"
    assert len(tab.zones) == 2
    block.give_up()
    assert not block.editing and tab.open_block is None and len(tab.zones) == 1
    # «Affichage» offers the line a section prints it with (issue #15, D-01)
    entries = tab.display_entries()
    assert [(e.key, e.call) for e in entries] == [("include", f'#include "/Domains/{tab.current_id}.typ"')]
    _cleanup(tab, "Essai B")


def test_a_block_validated_leaves_no_ghost_of_its_fields_and_an_equation_reopened_keeps_its_name():
    """Issue #15, REQ-001: Enter on a new variable left the editor's fields visible over the line validated -- the grid's widgets outlived `clear()`; REQ-002: an equation whose symbol is its key opened again with its name field empty."""
    from PySide6.QtWidgets import QLineEdit, QPushButton
    _window, tab = _tab()
    path = _new(tab, "Essai H")
    block = _var(tab, "F", 5, "kN")
    _flush()
    assert not block.editing
    assert not [w for w in block.findChildren(QLineEdit) + block.findChildren(QPushButton)], "the editor's fields outlived the validation"
    import formula_tab
    read = formula_tab.Block(tab, fd.read(path).commands[0], block.result)
    assert block.sizeHint().height() == read.sizeHint().height(), (block.sizeHint().height(), read.sizeHint().height())
    read.deleteLater()
    for _ in range(2):                         # a double-click then Enter, twice: nothing accumulates
        block.show_editor()
        block.validate()
        _flush()
    assert not block.findChildren(QLineEdit)
    tab.add_block("eq")
    eq = tab.open_block
    eq.fields["symbol"].setText("M_d")
    eq.fields["formula"].setText("F * 2")
    eq.validate()
    before = path.read_text(encoding="utf-8")
    assert '#eq("M_d", `F * 2`)' in before
    eq.show_editor()
    assert eq.fields["symbol"].text() == "M_d", "an equation opened again lost its name"
    eq.validate()
    assert path.read_text(encoding="utf-8") == before
    _cleanup(tab, "Essai H")


def test_a_single_click_on_a_block_validated_shows_its_options_and_writes_them():
    """REQ-003, D-05, D-12: a single click on any block validated shows its command's options above the commands, which stay reachable; an option changed is written into the file once, the block left closed."""
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    _window, tab = _tab()
    path = _new(tab, "Essai J")
    block = _var(tab, "F", 5, "kN")
    tab.add_block("eq")
    eq = tab.open_block
    eq.fields["symbol"].setText("M")
    eq.fields["formula"].setText("F * 2")
    eq.validate()
    tab.add_block("verify")
    tab.open_block.fields["formula"].setText("M <= 20 kN")
    tab.open_block.validate()
    assert [b.command.kind for b in tab.blocks] == ["var", "eq", "verify"] and not any(b.editing for b in tab.blocks), [b.error.text() for b in tab.blocks if b.editing]
    tab.chosen_block = None
    tab.show_right()
    assert tab.right_cards() == ["variables", "commands"]
    press = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(5, 5), QPointF(5, 5), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    for one in tab.blocks:                    # D-05: every block validated, whatever its command
        one.mousePressEvent(press)
        assert not one.editing and tab.chosen_block is one and tab.right_cards() == ["variables", "options", "commands"], tab.right_cards()
        assert tab.panel is not None and (tab.panel.controls or one.command.kind == "verify") and tab.panel.spec.command == one.command.kind, one.command.kind   # a verify's one option, its level, is set in «Affichage» (issue #19)
    block.mousePressEvent(press)
    tab.panel.set_values({"label": "Effort"})
    tab.panel.changed.emit(tab.panel.values())
    assert tab.option_timer.isActive(), "an option is written at every keystroke rather than once the typing pauses"
    tab.write_options()
    assert '#var("F", 5, "kN", label: "Effort")' in path.read_text(encoding="utf-8") and not block.editing
    # an option changed and another block chosen before the pause: written all the same, never lost
    tab.panel.set_values({"label": "Moment"})
    tab.panel.changed.emit(tab.panel.values())
    eq.mousePressEvent(press)
    assert not tab.option_timer.isActive() and '#var("F", 5, "kN", label: "Moment")' in path.read_text(encoding="utf-8")
    # and before leaving the domain
    eq_options = dict(tab.panel.values(), label="Flexion")
    tab.panel.set_values(eq_options)
    tab.panel.changed.emit(tab.panel.values())
    assert tab.confirm_leave() and 'label: "Flexion"' in path.read_text(encoding="utf-8")
    _cleanup(tab, "Essai J")


def test_a_click_elsewhere_in_the_middle_validates_the_block_being_written():
    """REQ-007: a click in the middle pane outside the block being written validates it, as Enter; one that does not validate stays open with its reason; a click on the right pane validates nothing."""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    window, tab = _tab()
    window.show()
    window.tab_widget.setCurrentWidget(tab)
    path = _new(tab, "Essai K")
    _var(tab, "F", 5, "kN")
    tab.add_block("var")
    block = tab.open_block
    block.fields["key"].setText("G")
    block.fields["value"].setText("3")
    _pump()
    QTest.mouseClick(tab.var_list.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(3, 3))
    _pump()
    assert block.editing, "a click on the right pane validated the block"
    QTest.mouseClick(tab.zones[0], Qt.MouseButton.LeftButton)
    _pump()
    assert not block.editing and '#var("G", 3)' in path.read_text(encoding="utf-8")
    tab.add_block("var")
    bad = tab.open_block
    bad.fields["key"].setText("H")
    bad.fields["value"].setText("abc")
    _pump()
    first = next(b for b in tab.blocks if b.command.key == "F")
    QTest.mouseClick(tab.zones[0], Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, tab.zones[0].pill_rect(first.uid).center())
    _pump()
    assert bad.editing and "abc" in bad.error.text(), bad.error.text()
    tab.remove_block(bad)
    window.hide()
    _cleanup(tab, "Essai K")


def test_typst_of_one_s_own_is_written_around_the_pills_and_a_command_goes_where_the_cursor_stands():
    """REQ-006 of issue #15, D-13; issue #40: the domain is one text, coloured as Typst, its commands pills in it; what is typed is written into the domain's file at its place; a command of the palette goes where the cursor stands, the text cut there, and opens on a line of its own (D-04); what the file would not read back is refused, nothing written."""
    import richtext
    from PySide6.QtGui import QTextCursor
    _window, tab = _tab()
    path = _new(tab, "Essai L")
    f = _var(tab, "F", 5, "kN")
    assert len(tab.zones) == 1 and isinstance(tab.zones[0].highlighter, richtext.TypstHighlighter)
    zone = tab.zones[0]
    cursor = QTextCursor(zone.document())
    cursor.insertText("= Charges\nLa charge : ")
    assert tab.text_timer.isActive()
    tab.write_text()
    text = path.read_text(encoding="utf-8")
    assert '[\n= Charges\nLa charge :\n  #var("F", 5, "kN")\n]' in text, text
    assert fd.read(path).state == "canonical"
    assert zone.paragraphs() == [[("text", "= Charges")], [("text", "La charge : "), ("cmd", f.uid)]], "the pill in its sentence"
    # a command added where the cursor stands: the text cut there, the block on a line of its own
    cursor = zone.textCursor()
    cursor.setPosition(len("= Charges"))
    zone.setTextCursor(cursor)
    tab.add_block("var", zone=zone)
    new = tab.open_block
    assert [z.paragraphs() for z in tab.zones] == [[[("text", "= Charges")]], [[("text", "La charge : "), ("cmd", f.uid)]]], [z.paragraphs() for z in tab.zones]
    new.fields["symbol"].setText("G")
    new.fields["value"].setText("2")
    new.validate()
    text = path.read_text(encoding="utf-8")
    # added at the end of the heading's line, G stands apart from the sentence after it, as the pane showed it: a blank line, Typst's new paragraph (D-05)
    assert '[\n= Charges\n  #var("G", 2)\n\nLa charge :\n  #var("F", 5, "kN")\n]' in text, text
    assert tab.zones[0].paragraphs() == [[("text", "= Charges")], [("cmd", new.uid)], [("text", "La charge : "), ("cmd", f.uid)]], tab.zones[0].paragraphs()
    # refused: a computing command inside a text
    said = _said(tab)
    before = path.read_text(encoding="utf-8")
    cursor = QTextCursor(tab.zones[0].document())
    cursor.movePosition(QTextCursor.MoveOperation.End)
    cursor.insertText('\nLe moment #eq("M", `F * 2`) vaut')
    tab.write_text()
    del tab.fail
    assert said and "#eq" in said[0] and path.read_text(encoding="utf-8") == before, said
    tab.render()
    _cleanup(tab, "Essai L")


def test_a_variable_is_imported_through_the_variables_tab_every_other_module_unavailable():
    """REQ-015, UI-007 of v0.117: «Importer…» brings «Variables» forward in its choosing mode, the navigation and Ctrl+n off; «Annuler» changes nothing; a value of the export chosen comes back as `#var(key, domain: (calculation, instance))` with the export's value (spec 2026-10-21-commandes-typst-refonte, REQ-009: `var-of` merged into `#var`)."""
    window, tab = _tab()
    path = _new(tab, "Essai C")
    import variables_tab
    listing = next(t for t in window.tabs if isinstance(t, variables_tab.VariablesTab))
    window.tab_widget.setCurrentWidget(tab)   # «Annuler» goes back to the tab that asked, which is in front when the engineer asks
    tab.import_variable()
    assert window.tab_widget.currentWidget() is listing and not window.nav.isEnabled() and not listing.pick_bar.isHidden()
    assert all(not s.isEnabled() for s in window.shortcuts)
    listing.end_pick(None)                                    # «Annuler»
    assert window.nav.isEnabled() and window.tab_widget.currentWidget() is tab and listing.pick_bar.isHidden()
    assert [c for c in tab.domain.commands if not c.is_text] == []
    tab.import_variable()
    key = next(k for k, d in listing.domains.items() if k[0] == variables_tab.EXPORT and d.address == ("snow-load", "SL"))
    listing.select_key((*key, "ce"))
    listing.pick_chosen()                                     # «Importer»
    assert window.nav.isEnabled() and window.tab_widget.currentWidget() is tab
    assert '#var("ce", domain: ("snow-load", "SL"))' in path.read_text(encoding="utf-8")
    assert tab.results[0].value == listing.variable((*key, "ce")).value and not tab.results[0].error
    # the tab's own domains are a source of the «Variables» tab, under their id (D-06)
    assert any(origin == variables_tab.FORMULAS and name == "poutre-p1" for origin, name in listing.domains), sorted(listing.domains)
    from PySide6.QtGui import QKeySequence, QShortcut
    tab.import_variable()
    escape = next(s for s in listing.findChildren(QShortcut) if s.key() == QKeySequence("Esc"))
    escape.activated.emit()
    assert window.nav.isEnabled() and window.tab_widget.currentWidget() is tab and len(tab.domain.commands) == 1
    _cleanup(tab, "Essai C")


def test_the_right_pane_is_one_column_the_name_line_the_fields_order_and_the_refusals():
    """D-12: the variables and the commands always, the domain's card while its line is chosen, a block's options while it is; UI-005: Tab and Shift+Tab go along the fields, a key taken twice and a name nobody declared refused; T19: a click on a variable in the list writes it in."""
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QFocusEvent
    from PySide6.QtWidgets import QApplication
    _window, tab = _tab()
    _cleanup(tab, "Essai D")
    tab.new_domain()
    assert tab.name_edit.selectedText() == tab.name_edit.text(), "a new domain's name is not selected to be typed over"
    tab.name_edit.setText("Essai D")
    tab.name_done()
    states = {"nothing": tab.right_cards()}
    QApplication.sendEvent(tab.name_edit, QFocusEvent(QEvent.Type.FocusIn, Qt.FocusReason.MouseFocusReason))
    states["domain line"] = tab.right_cards()
    tab.name_done()
    states["after the line"] = tab.right_cards()
    tab.add_block("var")
    states["a block"] = tab.right_cards()
    assert states == {"nothing": ["variables", "commands"], "domain line": ["variables", "domain", "commands"],
                      "after the line": ["variables", "commands"], "a block": ["variables", "options", "commands"]}, states
    block = tab.open_block
    fields = list(block.fields.values())

    def tab_stop(widget, forward=True):
        step = widget.nextInFocusChain if forward else widget.previousInFocusChain
        found = step()
        while not (found.focusPolicy() & Qt.FocusPolicy.TabFocus) or not found.isEnabled():
            found = found.nextInFocusChain() if forward else found.previousInFocusChain()
        return found
    assert [tab_stop(f) for f in fields[:-1]] == fields[1:], "Tab does not go from one field to the next"
    assert tab_stop(fields[1], forward=False) is fields[0], "Shift+Tab does not go back"
    block.fields["key"].setText("F")
    block.fields["value"].setText("5")
    block.fields["unit"].setText("kN")
    block.validate()
    tab.add_block("var")
    twice = tab.open_block
    twice.fields["key"].setText("F")
    twice.fields["value"].setText("6")
    twice.validate()
    assert twice.editing and "F" in twice.error.text(), twice.error.text()
    tab.remove_block(twice)
    tab.add_block("eq")
    unknown = tab.open_block
    unknown.fields["symbol"].setText("R")
    unknown.fields["formula"].setText("Z_x * 2")
    unknown.validate()
    assert unknown.editing and "Z_x" in unknown.error.text(), unknown.error.text()
    unknown.fields["formula"].setText("2 * ")
    unknown.fields["formula"].setCursorPosition(4)
    tab.on_field_focused(unknown.fields["formula"])
    item = tab.list._item_for(tab.current_id)
    tab.on_tree_clicked(item.child(0))
    assert unknown.fields["formula"].text() == "2 * F", unknown.fields["formula"].text()
    unknown.validate()
    assert not unknown.editing and (unknown.result.value, unknown.result.unit) == (10, "kN")
    _cleanup(tab, "Essai D")


def test_a_value_changed_by_hand_is_read_again_and_affichage_compiles_and_copies_the_include():
    """REQ-006 of v0.117: a value changed in the file -- by VS Code -- is what the tab shows once it is shown again; issue #15: «Affichage» compiles the page `#include` prints, and «Copier» copies exactly that line."""
    _window, tab = _tab()
    path = _new(tab, "Essai E")
    _var(tab, "F", 5, "kN")
    path.write_text(path.read_text(encoding="utf-8").replace('#var("F", 5, "kN")', '#var("F", 7.5, "kN")'), encoding="utf-8")
    tab.on_shown()
    assert (tab.blocks[0].result.value, tab.blocks[0].result.unit) == (7.5, "kN") and tab.var_list.topLevelItem(0).text(1) == "7.5 kN"
    tab.set_view("display", enter=False)
    try:
        tab.update_display(force=True)
        view = tab.display
        line = f'#include "/Domains/{tab.current_id}.typ"'
        assert view.command() == line
        source = view.source()
        assert source.rstrip().endswith(line) and "/000-Typst-Config/commands.typ" in source, source
        copied = []
        view.copy_text = copied.append
        view.copy_button.click()
        assert copied == [line]
    finally:
        tab.set_view("calc", enter=False)
    _cleanup(tab, "Essai E")


def test_a_file_changed_on_the_disk_while_the_tab_holds_it_is_never_written_over():
    """The lines written in VS Code (or by an engine synced) while the tab held the domain open were dropped by its next save: the save is refused, said, and the domain read again as the file now is."""
    _window, tab = _tab()   # calc/tools is on the path once the window is built: a module of it is imported after
    import notices_ui
    path = _new(tab, "Essai D")
    _var(tab, "F", 5, "kN")
    elsewhere = path.read_text(encoding="utf-8").replace('#var("F", 5, "kN")', '#var("F", 5, "kN")\n  #var("G", 2, "m")')
    path.write_text(elsewhere, encoding="utf-8", newline="")   # no on_shown: the tab still holds the domain as it read it
    told = []
    saved_tell = notices_ui.tell
    notices_ui.tell = lambda message, *a, **k: told.append(message)
    try:
        _var(tab, "H", 3, "m")
    finally:
        notices_ui.tell = saved_tell
    assert path.read_text(encoding="utf-8") == elsewhere, "the file changed on the disk was written over"
    assert any(path.name in m for m in told), told
    assert [b.command.key for b in tab.blocks] == ["F", "G"] and not tab.dirty, "the domain was not read again as the file now is"
    _cleanup(tab, "Essai D")


def _child(tab, index):
    """The row of the list of the `index`-th line of the domain open."""
    from grouped_list import ID_ROLE
    return next(item for item in tab.list._items(("child",)) if item.data(0, ID_ROLE) == f"{tab.current_id}#{index}")


def test_calcul_says_what_a_line_is_and_affichage_how_it_is_printed():
    """Issue #19 (UI-001, UI-003, UI-004, ARCH-005, ARCH-006, D-06, D-17): «Calcul» offers a variable and an equation their label, description, norm and clause and no level nor display type; «Affichage», a line chosen on the left, offers every argument of its printing first and the domain's `#include` after it -- a change written into the call in the file before the page is compiled again, kept when «Calcul» writes the line again, refused in a project open read-only --; a `val` is in italics in the list, in both views."""
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    window, tab = _tab()
    path = _new(tab, "Essai V")
    _var(tab, "F", 5, "kN")
    tab.add_block("eq")
    eq = tab.open_block
    eq.fields["symbol"].setText("M")
    eq.fields["formula"].setText("F * 2")
    eq.validate()
    press = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(5, 5), QPointF(5, 5), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    for block in tab.blocks[:2]:
        block.mousePressEvent(press)
        controls = set(tab.panel.controls)
        assert controls == {"label", "descr", "norm", "norm-ref"}, (block.command.kind, controls)
    tab.set_view("display", enter=False)
    try:
        tab.on_tree_clicked(_child(tab, 1))
        view = tab.display
        assert [e.key.split(":")[0] for e in view.entries] == ["line", "include"] and view.current().command == "eq", [e.key for e in view.entries]
        assert view.command() == f'#include "/Domains/{tab.current_id}.typ"', "the call to copy stays the include (D-06)"
        panel = view.panel()
        assert {"level", "style"} <= set(panel.controls) and "label" not in panel.controls, set(panel.controls)
        order = []
        original = view.refresh
        view.refresh = lambda: (order.append(("refresh", "style: \"bold\"" in path.read_text(encoding="utf-8"))), original())[1]
        option, combo = panel.controls["style"]
        combo.setCurrentIndex(combo.findData("bold"))
        assert '#eq("M", `F * 2`, style: "bold")' in path.read_text(encoding="utf-8"), path.read_text(encoding="utf-8")
        assert order and order[0] == ("refresh", True), f"the page was asked for before the file was written: {order}"
        view.refresh = original
        assert _child(tab, 1).isSelected(), "the line chosen stays chosen through the save"
        # read-only: refused, nothing written
        window.read_only = True
        try:
            before = path.read_text(encoding="utf-8")
            combo.setCurrentIndex(combo.findData("underline"))
            assert path.read_text(encoding="utf-8") == before
        finally:
            window.read_only = False
        # the domain itself: the include alone
        from grouped_list import ID_ROLE
        leaf = next(item for item in tab.list._items(("leaf",)) if item.data(0, ID_ROLE) == tab.current_id)
        tab.on_tree_clicked(leaf)
        assert [e.key for e in view.entries] == ["include"]
    finally:
        tab.set_view("calc", enter=False)
    # «Calcul» writes the line again: what «Affichage» wrote stays (ARCH-005)
    eq.mousePressEvent(press)
    tab.panel.set_values({"label": "Moment"})
    tab.panel.changed.emit(tab.panel.values())
    tab.write_options()
    text = path.read_text(encoding="utf-8")
    assert 'label: "Moment"' in text and 'style: "bold"' in text, text
    _cleanup(tab, "Essai V")


def test_folders_order_duplicate_and_archives_without_a_directory():
    """REQ-008, REQ-009, D-07: a domain filed in a folder and dropped in the order -- both kept in Woodcore-Datei/lists.json, the `.typ` untouched and flat --; duplicated beside itself in its folder; deleted into «Archives» and restored from there."""
    _window, tab = _tab()
    here = project.current()
    first = _new(tab, "Essai M")
    first_id = tab.current_id
    second = _new(tab, "Essai N")
    second_id = tab.current_id
    stamps = {p: p.stat().st_mtime_ns for p in (first, second)}
    tab.list.drop_ids([first_id], None, "Toiture")
    order, groups = list_order.tab_of(list_order.read(here), tab.KEY)
    assert groups.get(first_id) == "Toiture"
    assert tab.list._item_for(first_id).parent().text(0) == "Toiture" and first.parent == here.formulas_dir
    tab.list.drop_ids([second_id], tab.list._item_for(first_id), "Toiture", below=False)
    order, groups = list_order.tab_of(list_order.read(here), tab.KEY)
    assert order.index(second_id) < order.index(first_id) and groups.get(second_id) == "Toiture"
    assert {p: p.stat().st_mtime_ns for p in (first, second)} == stamps, "filing or ordering a domain rewrote its file"
    # read again by a store and a list made anew -- as after a restart
    fresh = list_order.Store(lambda: here)
    import grouped_list
    again = grouped_list.GroupedList(lang="fr")
    again.attach_order(tab.KEY, fresh, groups=True)
    again.set_entries([{"id": i, "text": i} for i in (first_id, second_id)])
    folder = again.topLevelItem(0)
    assert folder.text(0) == "Toiture" and [folder.child(i).text(0) for i in range(folder.childCount())] == [second_id, first_id]
    again.deleteLater()
    # a folder renamed: its domains follow it in lists.json, their files untouched
    import formula_tab
    item = next(tab.list.topLevelItem(i) for i in range(tab.list.topLevelItemCount()) if tab.list.topLevelItem(i).text(0) == "Toiture")
    saved_ask = tab.list._ask
    tab.list._ask = lambda *a, **k: "Couverture"
    try:
        tab.list._rename_folder(item)
    finally:
        tab.list._ask = saved_ask
    groups = list_order.tab_of(list_order.read(here), tab.KEY)[1]
    assert groups.get(first_id) == groups.get(second_id) == "Couverture", groups
    assert tab.list._item_for(first_id).parent().text(0) == "Couverture"
    assert {p: p.stat().st_mtime_ns for p in (first, second)} == stamps
    item = next(tab.list.topLevelItem(i) for i in range(tab.list.topLevelItemCount()) if tab.list.topLevelItem(i).text(0) == "Couverture")
    tab.list._ask = lambda *a, **k: "Toiture"
    try:
        tab.list._rename_folder(item)
    finally:
        tab.list._ask = saved_ask
    # duplicated: next to what it copies, in its folder
    tab.open_domain(fd.read(first))
    assert tab.duplicate_domain()
    copy_id = tab.current_id
    assert copy_id != first_id and fd.read(here.formulas_dir / f"{copy_id}.typ").name == tab.t("fm_copy", name="Essai M")
    order, groups = list_order.tab_of(list_order.read(here), tab.KEY)
    assert order.index(copy_id) == order.index(first_id) + 1 and groups.get(copy_id) == "Toiture"
    # deleted into «Archives», restored
    import source_archive
    from PySide6.QtWidgets import QMessageBox
    saved = QMessageBox.question
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    try:
        tab.archive.archive([copy_id])
    finally:
        QMessageBox.question = saved
    assert not (here.formulas_dir / f"{copy_id}.typ").exists() and list((here.formulas_dir / "archives").glob(f"*-{copy_id}.typ"))
    keys = tab.list.archived_ids()
    key = next(k for k in keys if copy_id in k)
    assert source_archive.is_key(key)
    tab.archive.restore([key], "")
    assert (here.formulas_dir / f"{copy_id}.typ").is_file()
    for name in ("Essai M", "Essai N", tab.t("fm_copy", name="Essai M")):
        _cleanup(tab, name)
    tab.app.list_store.forget(tab.KEY, [first_id, second_id, copy_id])


def test_a_circle_is_refused_at_the_import_and_a_document_s_variable_is_read_where_the_variables_tab_read_it():
    """REQ-015 of v0.117: a variable that would make two domains take their values from each other is refused when it is imported, nothing written; one of a document's named domain comes in as `#var(key, domain: …)` with the value the «Variables» tab read off that document. A domain of the tab is named by its id (D-06)."""
    import variables as model
    import variable_sources
    window, tab = _tab()
    for name in ("Essai F", "Essai G"):
        _cleanup(tab, name)
    here = project.current()
    fd.save(here, fd.Domain(id="essai-g", name="Essai G", path=here.formulas_dir / "essai-g.typ",
                            commands=[fd.Command("var", key="y", source=("domain", "essai-f"))]))
    tab.reload(keep="")
    path = _new(tab, "Essai F")
    assert tab.current_id == "essai-f"
    before = path.read_text(encoding="utf-8")
    said = _said(tab)
    try:
        tab.on_picked(("formulas", "essai-g", model.Variable(key="y", domain="essai-g", value=1, unit="", symbol="y"), None))
    finally:
        del tab.fail
    assert said and fd.CIRCLE in said[0], said
    assert path.read_text(encoding="utf-8") == before and tab.domain.commands == []
    import variables_tab
    listing = next(t for t in window.tabs if isinstance(t, variables_tab.VariablesTab))
    q = model.Variable(key="Q_k", domain="Lasten", value=3, unit="kN", symbol="Q_k")
    listing.domains[("rs", "Lasten")] = variable_sources.Domain(name="Lasten", origin="rs", variables=[q], kind="named")
    try:
        tab.on_picked(("rs", "Lasten", q, None))
        assert '#var("Q_k", domain: "Lasten")' in path.read_text(encoding="utf-8")
        assert (tab.results[0].value, tab.results[0].unit) == (3, "kN") and not tab.results[0].error
    finally:
        listing.domains.pop(("rs", "Lasten"), None)
    for name in ("Essai F", "Essai G"):
        _cleanup(tab, name)


def test_the_index_is_rewritten_at_every_save_and_lists_the_domain_under_its_id():
    """REQ-010: a variable validated is computed in Python and the index the «Variables» tab reads is written at once, the domain under its id with its name as title."""
    _window, tab = _tab()
    _new(tab, "Essai O")
    _var(tab, "F", 5, "kN")
    data = json.loads((project.current().data_dir / fd.EXPORT_FILE).read_text(encoding="utf-8"))
    assert data["domains"][tab.current_id] == {"title": "Essai O", "file": f"Domains/{tab.current_id}.typ"}
    found = fd.variable_domains(data)
    domain = next(d for d in found if d.name == tab.current_id)
    assert domain.label == "Essai O" and [(v.key, v.value, v.unit) for v in domain.variables] == [("F", 5, "kN")]
    _cleanup(tab, "Essai O")


def _shown(tab):
    """The window shown and the tab in front: a text lays its pills out only once it has a width."""
    window = tab.app
    window.show()
    window.tab_widget.setCurrentWidget(tab)
    _pump()
    return window


def _pill_text(block):
    from PySide6.QtGui import QTextDocument
    doc = QTextDocument()
    doc.setHtml(block.view_html())
    return doc.toPlainText()


def test_a_command_validated_is_a_pill_inline_in_its_sentence_or_on_a_line_of_its_own():
    """Issue #40, REQ-001, REQ-002, D-01, D-03: every command validated is a pill -- its shown variable, its value and its unit, an equation's answer alone, a relation and its ✔ --, inline in the sentence it stands in; `note: "line"` written in «Affichage» puts it on a line of its own, the file changed by that argument alone."""
    from PySide6.QtGui import QTextCursor
    _window, tab = _tab()
    path = _new(tab, "Essai P")
    f = _var(tab, "F", 5, "kN")
    tab.add_block("eq")
    m = tab.open_block
    m.fields["symbol"].setText("M")
    m.fields["formula"].setText("F * 2 m")
    m.validate()
    tab.add_block("verify")
    v = tab.open_block
    v.fields["formula"].setText("M <= 20 kNm")
    v.validate()
    assert [_pill_text(b) for b in (f, m)] == ["F = 5 kN", "M = 10 kNm"], [_pill_text(b) for b in (f, m)]
    assert "✔" in _pill_text(v) and "<br>" not in m.view_html() and "<br>" not in v.view_html()
    # a sentence round F: one paragraph of the pane, as Typst prints it
    zone = tab.zones[0]
    cursor = QTextCursor(zone.document())
    cursor.insertText("Kraft ")
    tab.write_text()
    tab.render()
    assert tab.zones[0].paragraphs()[0][:2] == [("text", "Kraft "), ("cmd", f.uid)], tab.zones[0].paragraphs()
    before = path.read_text(encoding="utf-8")
    # an option written in «Affichage»: that argument alone written, the pill still in its sentence -- every command of a domain prints inline since `note:` was retired (Q-014)
    assert tab.write_display(tab.ref_of(f.command), {"style": "bold"})
    after = path.read_text(encoding="utf-8")
    assert after == before.replace('#var("F", 5, "kN")', '#var("F", 5, "kN", style: "bold")'), after
    assert tab.zones[0].paragraphs()[0][:2] == [("text", "Kraft "), ("cmd", f.uid)], tab.zones[0].paragraphs()
    _cleanup(tab, "Essai P")


def test_a_pill_is_chosen_by_a_click_moved_by_a_drop_and_deleted_with_its_text():
    """Issue #40, REQ-004, D-06, CON-002: a click on a pill shows its options; a pill dropped elsewhere in the text moves its command there in the file; a drop inside an equation is refused and changes nothing, one above what the command is computed from is refused with the domain's reason; a pill deleted with the text is the command taken away; a copy carries the text alone."""
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent, QTextCursor
    window, tab = _tab()
    path = _new(tab, "Essai Q")
    f = _var(tab, "F", 5, "kN")
    zone = tab.zones[0]
    cursor = QTextCursor(zone.document())
    cursor.movePosition(QTextCursor.MoveOperation.End)
    cursor.insertText(" und danach $a + b$ Ende")
    tab.write_text()
    tab.render()
    _shown(tab)
    try:
        zone = tab.zones[0]
        tab.chosen_block = None
        centre = QPointF(zone.pill_rect(f.uid).center())
        zone.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress, centre, centre, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
        zone.mouseReleaseEvent(QMouseEvent(QEvent.Type.MouseButtonRelease, centre, centre, Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier))
        assert tab.chosen_block is f and "options" in tab.right_cards()
        # dropped after «und»: the file says text, F, text
        text = zone.toPlainText()
        at = text.index("und") + len("und ")
        assert tab.drop_refusal(zone, at) is None
        tab.pill_dropped(zone, f.uid, at)
        written = path.read_text(encoding="utf-8")
        assert 'und\n  #var("F", 5, "kN")\ndanach $a + b$ Ende' in written, written
        # inside the equation: refused, nothing written
        zone = tab.zones[0]
        inside = zone.toPlainText().index("a +") + 1
        assert tab.drop_refusal(zone, inside) is not None
        tab.pill_dropped(zone, f.uid, inside)
        assert path.read_text(encoding="utf-8") == written
        # in a heading: refused, its reason said in the window's words
        heading = QTextCursor(zone.document())
        heading.insertText("= Titre\n")
        tab.write_text()
        tab.render()
        zone = tab.zones[0]
        written = path.read_text(encoding="utf-8")
        status = []
        saved_status = tab.app.set_status
        tab.app.set_status = status.append
        try:
            tab.pill_dropped(zone, f.uid, 3)
        finally:
            tab.app.set_status = saved_status
        assert status == [tab.t("fm_drop_apart")] and path.read_text(encoding="utf-8") == written, status
        # above what it is computed from: refused with the domain's reason
        tab.add_block("eq")
        m = tab.open_block
        m.fields["symbol"].setText("M")
        m.fields["formula"].setText("F * 2")
        m.validate()
        written = path.read_text(encoding="utf-8")
        said = _said(tab)
        try:
            tab.pill_dropped(tab.zones[0], m.uid, len("= Titre\n"))   # before F, which it is computed from
        finally:
            del tab.fail
        assert said and path.read_text(encoding="utf-8") == written, said
        # a copy is text alone
        zone = tab.zones[0]
        zone.selectAll()
        assert "￼" not in zone.createMimeDataFromSelection().text()
        # deleted with the text: the command taken away
        position = zone.pill_position(m.uid)
        cursor = QTextCursor(zone.document())
        cursor.setPosition(position)
        cursor.setPosition(position + 1, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        tab.write_text()
        assert '#eq("M"' not in path.read_text(encoding="utf-8") and [b.command.key for b in tab.blocks] == ["F"]
    finally:
        window.hide()
    _cleanup(tab, "Essai Q")


def test_a_variable_is_typed_shown_variable_first_its_key_following_until_written_by_hand():
    """Issue #40, REQ-005: the fields of a `var` are the shown variable, the computation variable, the value, the unit, in that order; typing the shown variable writes the key it makes, Tab goes into the key and what is typed there stays; emptied, the key follows again; a block opened again whose key is not the one its symbol makes keeps it as written."""
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    window, tab = _tab()
    path = _new(tab, "Essai R")
    _shown(tab)
    try:
        tab.add_block("var")
        block = tab.open_block
        assert list(block.fields) == ["symbol", "key", "value", "unit"]
        QTest.keyClicks(block.fields["symbol"], "M_(y,d)")
        assert block.fields["key"].text() == "M_y_d"
        def tab_stop(widget):
            found = widget.nextInFocusChain()
            while not (found.focusPolicy() & Qt.FocusPolicy.TabFocus) or not found.isEnabled():
                found = found.nextInFocusChain()
            return found
        fields = list(block.fields.values())
        assert [tab_stop(f) for f in fields[:-1]] == fields[1:], "Tab goes from the shown variable into the computation variable, then the value and the unit"
        block.fields["key"].clear()
        QTest.keyClicks(block.fields["key"], "My")
        block.fields["symbol"].clear()
        QTest.keyClicks(block.fields["symbol"], "M_(z,d)")
        assert block.fields["key"].text() == "My", "a key written by hand must stay, whatever the shown variable becomes"
        block.fields["symbol"].clear()
        QTest.keyClicks(block.fields["symbol"], "M_(y,d)x")
        block.fields["key"].selectAll()
        QTest.keyClick(block.fields["key"], Qt.Key.Key_Backspace)    # Backspace: emptied, the key follows the shown variable again
        assert block.fields["key"].text() == fd.key_from_symbol("M_(y,d)x") == "M_y_d_x", block.fields["key"].text()
        block.fields["key"].setText("My")
        block.fields["symbol"].setText("M_(y,d)")
        block.fields["value"].setText("3")
        block.fields["unit"].setText("kNm")
        block.validate()
        assert '#var("My", "M_(y,d)", 3, "kNm")' in path.read_text(encoding="utf-8")
        block = next(b for b in tab.blocks if b.command.key == "My")
        tab.open_pill(block)
        assert block.key_by_hand and block.fields["key"].text() == "My" and block.fields["symbol"].text() == "M_(y,d)", "opened again, a key the symbol does not make is the engineer's"
        QTest.keyClicks(block.fields["symbol"], "z")
        assert block.fields["key"].text() == "My"
        block.give_up()
    finally:
        window.hide()
    _cleanup(tab, "Essai R")


def test_an_unfolded_check_shows_its_lines_states_and_imports_them():
    """UI-002 (spec 2026-10-15): a domain unfolded from a check shows its card -- the check it is written from, the lines not in step with their state -- and marks its pills: a formula changed outside Woodcore is `local`, its pill drawn in the warning's colour; «Tout importer» takes it, the card then says every line is up to date. Every action is a writer, refused in a project opened read only."""
    from domains import member_check, unfold
    _window, tab = _tab()
    import woodcore_gui   # after _tab(), which puts calc/tools on the path
    import formula_tab
    here = project.current()
    path = unfold.domain_path(here, "ZT-01")   # Timber-checks/Tension/ laid out by folders (issue #64)
    with project.using(here):
        member_check.export(here)
    try:
        assert path.is_file()
        path.write_text(path.read_text(encoding="utf-8").replace("`N_t_d / A`", "`N_t_d / (A)`"), encoding="utf-8")
        tab.reload(keep="ZT-01")
        _pump()
        assert "unfold" in tab.right_cards()
        listed = [tab.unfold_list.topLevelItem(i).text(0) for i in range(tab.unfold_list.topLevelItemCount())]
        assert listed == ["eq:sigma_t_0_d"], listed
        sigma = next(b for b in tab.blocks if b.command.key == "sigma_t_0_d")
        assert tab.pill_state(sigma) == "local"
        assert tab.unfold_buttons["import_all"].isEnabled() and not tab.unfold_buttons["regenerate"].isEnabled()
        assert tab.write_unfold_import_all() is True
        assert tab.unfold_list.topLevelItemCount() == 0 and not tab.unfold_none.isHidden()
        assert "`N_t_d / (A)`" in path.read_text(encoding="utf-8")
        # a value of the norm changed in the file and imported: the engineer's own, its pill in the override's colour, «Reprendre» offered
        path.write_text(path.read_text(encoding="utf-8").replace('"f_(t,0,d,\\"Tab\\")", 8.5', '"f_(t,0,d,\\"Tab\\")", 9'), encoding="utf-8")
        tab.reload(keep="ZT-01")
        tab.unfold_list.setCurrentItem(tab.unfold_list.topLevelItem(0))
        assert tab.write_unfold_import() is True
        tab.unfold_list.setCurrentItem(tab.unfold_list.topLevelItem(0))
        table = next(b for b in tab.blocks if b.command.key == "f_t_0_d_tab")
        assert tab.pill_state(table) == "own" and tab.unfold_buttons["take_back"].isEnabled()
        assert tab.write_unfold_take_back() is True and tab.unfold_list.topLevelItemCount() == 0
        # a line taken out: listed «ligne supprimée», put back by «Réinsérer»
        text = path.read_text(encoding="utf-8")
        line = next(l for l in text.split("\n") if l.strip().startswith('#eq("f_t_0_d"'))
        path.write_text(text.replace(line + "\n", ""), encoding="utf-8")
        tab.reload(keep="ZT-01")
        tab.unfold_list.setCurrentItem(tab.unfold_list.topLevelItem(0))
        assert tab.unfold_list.topLevelItem(0).text(0) == "eq:f_t_0_d" and tab.unfold_buttons["reinsert"].isEnabled()
        assert tab.write_unfold_reinsert() is True and line in path.read_text(encoding="utf-8")
        # a conflict: both changed; «Prendre celle de l'export» writes the export's line, its pill drawn in the danger's colour until then
        path.write_text(path.read_text(encoding="utf-8").replace('"N_(t,d)", 25, "kN"', '"N_(t,d)", 31, "kN"'), encoding="utf-8")
        source = json.loads((here.checks_dir / "ZT-01.json").read_text(encoding="utf-8"))
        with project.using(here):
            member_check.write_source(here, dict(source, N={"value": 27, "unit": "kN"}))
            member_check.export(here)
        tab.reload(keep="ZT-01")
        n = next(b for b in tab.blocks if b.command.key == "N_t_d")
        assert tab.pill_state(n) == "conflict"
        tab.unfold_list.setCurrentItem(tab.unfold_list.topLevelItem(0))
        assert tab.unfold_buttons["theirs"].isEnabled() and tab.write_unfold_choice("theirs") is True
        assert '"N_(t,d)", 27, "kN"' in path.read_text(encoding="utf-8")
        with project.using(here):
            member_check.write_source(here, source)
            member_check.export(here)
        own = {k: v for c in reversed(woodcore_gui.own_classes(formula_tab.FormulaTab)) for k, v in vars(c).items()}
        for name in ("write_unfold_import", "write_unfold_import_all", "write_unfold_take_back", "write_unfold_reinsert", "write_unfold_choice", "write_unfold_regenerate"):
            assert name in woodcore_gui.WRITERS and hasattr(own[name], "__wrapped__"), name
    finally:
        path.unlink(missing_ok=True)
        base = unfold.read_base(here)
        base["domains"].pop("ZT-01", None)
        unfold.write_base(here, base)
        tab.reload(keep="")
