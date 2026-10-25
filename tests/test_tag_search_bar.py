"""The search bar that carries a filter as tags (calc/tools/tag_search_bar.py; spec 2026-10-24-onglet-variables-groupes, UI-004, ARCH-002).

⚠️ **A brick with no knowledge of variables**: it is used here with tags of no tab at all, and imports nothing of the «Variables» tab.
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys

from conftest import ROOT, Skip

sys.path.insert(0, str(ROOT / "calc" / "tools")) if str(ROOT / "calc" / "tools") not in sys.path else None


def _app():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _bar():
    _app()
    from tag_search_bar import TagSearchBar
    bar = TagSearchBar()
    tags = [["menu", "Fruits › Pommes"], ["source", "source : marché"], ["domain", "Gala [bio]"]]
    bar.removed.connect(lambda kind: (tags.remove(next(t for t in tags if t[0] == kind)), bar.set_tags([tuple(t) for t in tags], "Retirer")))
    bar.set_tags([tuple(t) for t in tags], "Retirer")
    bar.set_placeholders("Chercher…", "Chercher dans ce filtre…")
    return bar


def _backspace(bar):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication
    QApplication.sendEvent(bar.edit, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier))


def test_backspace_in_an_empty_bar_takes_the_tags_off_from_the_last():
    bar = _bar()
    assert bar.kinds() == ["menu", "source", "domain"]
    assert bar.edit.placeholderText() == "Chercher dans ce filtre…"
    _backspace(bar)
    assert bar.kinds() == ["menu", "source"]
    _backspace(bar)
    _backspace(bar)
    assert bar.kinds() == [] and bar.edit.placeholderText() == "Chercher…"
    _backspace(bar)   # nothing left: nothing happens
    assert bar.kinds() == []


def test_the_cross_takes_one_tag_off_and_the_text_typed_stays():
    bar = _bar()
    bar.edit.setText("gala")
    _backspace(bar)    # the text is not empty: an ordinary backspace, no tag taken off
    assert bar.kinds() == ["menu", "source", "domain"]
    bar.close_button("source").click()
    assert bar.kinds() == ["menu", "domain"] and bar.texts() == ["Fruits › Pommes", "Gala [bio]"]
    assert bar.edit.text().startswith("gal"), "the text typed is not touched by a tag taken off"
    assert bar.close_button("menu").toolTip() == "Retirer"


def test_the_brick_knows_nothing_of_the_variables_tab():
    source = (ROOT / "calc" / "tools" / "tag_search_bar.py").read_text(encoding="utf-8")
    assert "variables_tab" not in source and "variable_" not in source and "vr_" not in source
    assert "STRINGS" not in source, "the bar owns no word: the caller gives them"
