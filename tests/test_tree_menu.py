"""The button that opens a tree of entries in a popup (calc/tools/tree_menu.py; spec 2026-10-24-onglet-variables-groupes, UI-002, ARCH-002).

⚠️ **An entry at zero is greyed and never chosen**, and Escape closes the popup -- used here with entries of no tab at all.
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys

from conftest import ROOT, Skip

sys.path.insert(0, str(ROOT / "calc" / "tools")) if str(ROOT / "calc" / "tools") not in sys.path else None


def _menu():
    try:
        from PySide6.QtWidgets import QApplication, QWidget
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    from tree_menu import Entry, TreeMenu
    host = QWidget()
    menu = TreeMenu(host)
    menu.set_label("Tout")
    menu.set_entries([Entry("", "Tout", "7", 0, bold=True), Entry("g:fruits", "Fruits", "7", 0), Entry("s:pommes", "Pommes", "5", 1),
                      Entry("gala", "Gala", "5", 2), Entry("poires", "Poires", "2", 1), Entry("coings", "Coings", "—", 1, enabled=False, tip="aucune")])
    chosen = []
    menu.chosen.connect(chosen.append)
    return host, menu, chosen


def test_an_entry_is_chosen_and_one_at_zero_is_not():
    host, menu, chosen = _menu()
    from PySide6.QtCore import Qt
    assert menu.text().startswith("Tout") and menu.text().endswith("▾")
    gala = menu.item("gala")
    assert gala.parent() is menu.item("s:pommes") and gala.parent().parent() is menu.item("g:fruits"), "a tree, by depth"
    assert menu.popup.tree.isExpanded(menu.popup.tree.indexFromItem(menu.item("g:fruits"))), "all of it open"
    assert not (menu.item("coings").flags() & Qt.ItemFlag.ItemIsEnabled) and menu.item("coings").toolTip(0) == "aucune"
    menu.choose("coings")
    assert chosen == []
    menu.choose("s:pommes")
    assert chosen == ["s:pommes"]
    host.deleteLater()


def test_escape_closes_the_popup():
    host, menu, _chosen = _menu()
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication
    host.show()
    menu.open()
    assert menu.is_open()
    closed = []
    menu.closed.connect(lambda: closed.append(True))
    QApplication.sendEvent(menu.popup, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
    assert not menu.is_open() and closed
    host.hide()
    host.deleteLater()


def test_the_brick_knows_nothing_of_the_variables_tab():
    source = (ROOT / "calc" / "tools" / "tree_menu.py").read_text(encoding="utf-8")
    assert "variables_tab" not in source and "variable_" not in source and "vr_" not in source and "STRINGS" not in source
