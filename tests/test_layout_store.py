"""The panes' sizes kept by tab, by view and by the screens plugged in, and the navigation's groups folded and its width dragged (calc/tools/layout_store.py, chrome.SideNav; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-022, REQ-023, ARCH-005).

The engineer, 07.10.2026: «il y a une sauvegarde d'affichage pour l'écran externe lorsqu'il est utilisé et une sauvegarde pour mon pc portable lorsqu'il est utilisé sans l'écran externe» · «"Projet" qui contient Plan de position, Plan de protection incendie, Positions, Journal, etc... doit pouvoir être réduit ou maximisé» · «La largeur du volet tout à gauche doit pouvoir être modifiée».
"""

import os
import sys

from conftest import ROOT, Skip

LAPTOP = "Lenovo|ThinkPad|SN123||1.5"
SCREEN = "Dell|U2720Q|SN999||1"


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _stores():
    """Two stores over one dictionary of settings, as two configurations of screens see the same file."""
    import layout_store
    settings = {}
    read = lambda: dict(settings)
    write = lambda new: (settings.clear(), settings.update(new))
    alone = layout_store.Store(sig=layout_store.signature([LAPTOP]), read=read, write=write)
    docked = layout_store.Store(sig=layout_store.signature([LAPTOP, SCREEN]), read=read, write=write)
    return layout_store, settings, alone, docked


def test_the_screens_signature_is_the_set_of_screens_whatever_their_order():
    _qt()
    import layout_store
    assert layout_store.signature([LAPTOP, SCREEN]) == layout_store.signature([SCREEN, LAPTOP])
    assert layout_store.signature([LAPTOP]) != layout_store.signature([LAPTOP, SCREEN])
    assert len(layout_store.signature()) == 12, "the application's own screens give a key too"


def test_each_configuration_of_screens_keeps_its_own_layout_and_an_unknown_one_takes_the_last_used():
    _qt()
    layout_store, settings, alone, docked = _stores()
    key = ("tab_plan", "draw", "panes")
    alone.put(key, [0.2, 0.5, 0.3])
    docked.put(key, [0.1, 0.7, 0.2])
    assert alone.get(key) == [0.2, 0.5, 0.3] and docked.get(key) == [0.1, 0.7, 0.2]
    assert alone.get(("tab_plan", "export", "panes")) is None, "another view, never kept: the pane's own default"
    third = layout_store.Store(sig=layout_store.signature(["Other|Screen|X||2"]), read=alone.read, write=alone.write)
    assert third.get(key) == [0.1, 0.7, 0.2], "a configuration never seen takes the one used last"


def test_a_splitter_bound_is_put_back_and_written_after_a_drag():
    app = _qt()
    import time
    from PySide6.QtWidgets import QLabel, QSplitter
    layout_store, settings, alone, _docked = _stores()
    splitter = QSplitter()
    for text in ("a", "b", "c"):
        splitter.addWidget(QLabel(text))
    splitter.resize(1000, 300)
    splitter.show()
    alone.put(("t", "v", "panes"), [0.25, 0.5, 0.25])
    binding = layout_store.bind(splitter, lambda: ("t", "v", "panes"), store=alone)
    sizes = splitter.sizes()
    assert abs(sizes[0] / sum(sizes) - 0.25) < 0.02, sizes
    splitter.setSizes([600, 200, 200])
    splitter.splitterMoved.emit(600, 1)
    end = time.monotonic() + 3
    while time.monotonic() < end and alone.get(("t", "v", "panes"))[0] < 0.5:
        app.processEvents()
        time.sleep(0.02)
    assert alone.get(("t", "v", "panes"))[0] > 0.55, "the drag is written, once it stands still"
    splitter.close()
    del binding


def test_a_group_of_the_navigation_folds_by_its_title_and_ctrl_digits_still_count_its_rows():
    _qt()
    import chrome
    nav = chrome.SideNav([("Projet", [(0, "Plan de positions", "tab_plan"), (1, "Journal", "tab_journal")]),
                          ("Actions", [(2, "Combinaisons", "tab_combinations")])])
    nav.resize(214, 400)
    nav.show()
    folded = []
    nav.foldedChanged.connect(folded.append)
    nav.toggle_group("Projet")
    assert nav.rows[0].isHidden() and nav.rows[1].isHidden() and not nav.rows[2].isHidden()
    assert folded == [["Projet"]] and nav.list.item(0).text() == "Projet", "the title keeps its text; its arrow is painted"
    assert nav.order() == [0, 1, 2], "Ctrl+1 … Ctrl+9 count a folded group's rows still"
    nav.set_visible([0, 2])
    assert nav.order() == [0, 2] and not nav.visible(1), "what the document hides stays hidden"
    nav.toggle_group("Projet")
    assert not nav.rows[0].isHidden() and nav.rows[1].isHidden(), "unfolded: the rows the document shows"
    widths = []
    nav.widthChanged.connect(widths.append)
    nav.set_expanded_width(300)
    assert nav.width() == 300 and widths == [300]
    nav.set_expanded_width(9999)
    assert nav.width() == chrome.MAX_EXPANDED_WIDTH
    nav.set_collapsed(True)
    assert nav.width() == chrome.COLLAPSED_WIDTH and not nav.grip.isVisible()
    nav.set_collapsed(False)
    assert nav.width() == chrome.MAX_EXPANDED_WIDTH, "unfolded, the width dragged comes back"
    nav.close()
