"""A position's type in the language of the project and of the report (v0.116, docs/typst/language.md §4bis, docs/domain/positions.md §7).

The type is stored once, as the STE key -- German, as the data has always carried it, so nothing is migrated --, and shown in a language:

* the Positions tab in the **project's** language (the `doc-lang` of its config.typ), a French project showing «Poutre» for a stored «Träger» and saving «Träger» again; a type typed freely, one the glossary does not carry, staying as typed; the list's column and the search following what is shown; a name typed in a language not the project's still read as the key it names;
* the report in the language it is **compiled** in: `#member` at level 1 prints «Poutre» in a French report;
* the glossary carrying every STE type in the three languages, and the ID's letter staying the STE one whatever the language (T stays T).
"""

import os
import re
import subprocess
import sys

import conftest
from conftest import ROOT, Skip

import project

_STATE = {}
TYPES = ("vertikal tragende Wand", "aussteifende Wand", "vertikal tragende und aussteifende Wand", "Träger", "Stütze",
         "Aussteifung, Stabilisierung Einzelstab", "Scheibenbildung Decke/Dach", "Decke/Dach", "Ausschnitt/Öffnung", "Betonwand",
         "Betondecke", "vertikal wirkendes Auflager", "horizontal wirkendes Auflager", "vertikal und horizontal wirkendes Auflager",
         "Abfangung Linienlast von oben", "Abfangung Punktlast von oben")

ROWS = (
    {"position": "T001", "type": "Träger", "material": "Fichte", "strength_class": "C24", "section_type": "rec", "dimension": "100/200", "units": "mm", "moisture_class": 2},
    {"position": "X001", "type": "Sonderbauteil", "material": "Fichte", "strength_class": "C24"},
)


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    if "window" not in _STATE:
        _qt()
        conftest.exported("calculations.json")
        here = conftest.project_copy("position_type_i18n")
        import positions_store as store
        store.write(here, ROWS)
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        window.reexport = lambda **kwargs: None
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window):
    import positions_tab
    return next(t for t in window.tabs if isinstance(t, positions_tab.PositionsTab))


def _language(here, lang):
    """The document language the project states: the copy of the example project carries no config.typ, so one holding the two lines `templates` reads is written."""
    config = here.config_typ
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('#let doc-lang = "%s"' % lang + chr(10) + '#let doc-region = "CH"' + chr(10), encoding="utf-8", newline=chr(10))


def _shown(tab, here, lang):
    _language(here, lang)
    tab.dirty = False
    tab.on_shown()
    tab.load_first()


def test_the_glossary_carries_every_ste_type_in_the_three_languages():
    from i18n import strings
    import positions_store as store
    assert tuple(store.types()) == TYPES, store.types()
    for name in TYPES:
        fr, en = strings.term(name, "fr"), strings.term(name, "en")
        assert fr != name and en != name and fr != en, (name, fr, en)
        assert "ß" not in fr + en
    assert strings.term("Träger", "fr") == "Poutre" and strings.term("Stütze", "en") == "Column"
    assert strings.term("Sonderbauteil", "fr") == "Sonderbauteil", "a free type is left as typed"


def test_the_key_of_what_is_shown_or_typed():
    import positions_store as store
    assert store.type_label("Träger", "fr") == "Poutre" and store.type_label("Träger", "de") == "Träger"
    assert store.type_label("", "fr") == "" and store.type_label("Sonderbauteil", "en") == "Sonderbauteil"
    for typed in ("Poutre", "poutre", "Träger", "Beam"):
        assert store.type_key(typed, "fr") == "Träger", typed
    assert store.type_key("Mon élément", "fr") == "Mon élément"
    assert store.type_key("", "fr") == ""
    # the symbol and the type of a letter work on the stored key, in any language
    assert store.symbol_for(store.type_key("Poutre", "fr")) == "T" and store.type_for("T") == "Träger"


def test_a_french_project_shows_poutre_for_a_stored_trager_and_saves_the_key():
    window, here = _window()
    import positions_store as store
    with project.using(here):
        tab = _tab(window)
        _shown(tab, here, "fr")
        assert tab.type_language == "fr"
        item = tab.list.item_of("T001")
        assert item.text(1) == "Poutre", item.text(1)
        assert tab.type_combo.currentText() == "Poutre"
        offered = [tab.type_combo.itemText(i) for i in range(tab.type_combo.count())]
        assert "Poteau" in offered and "Paroi en béton" in offered and "Träger" not in offered
        assert tab.type_combo.findData("Stütze") >= 0, "the stored key is the item's data"
        # the search finds a position by the type it is shown with
        tab.search.setText("poutre")
        assert [pid for it, pid in tab.list.rows() if not it.isHidden()] == ["T001"]
        tab.search.setText("")
        # a change elsewhere writes the key, not the shown word
        tab.description_edit.setPlainText("changé")
        assert tab.form_values()["type"] == "Träger"
        assert tab.save()
        assert {r["position"]: r for r in store.read(here)}["T001"]["type"] == "Träger"
        # a type chosen from the list is stored as its key
        tab.type_combo.setCurrentIndex(tab.type_combo.findData("Stütze"))
        assert tab.form_values()["type"] == "Stütze"
        # a name typed in French (or in another language) is read as the key it names; the letter stays the STE one
        tab.type_combo.setCurrentText("poutre")
        assert tab.form_values()["type"] == "Träger" and tab.symbol_for(tab.form_values()["type"]) == "T"


def test_a_free_type_stays_as_typed_and_a_german_project_shows_the_german():
    window, here = _window()
    import positions_store as store
    with project.using(here):
        tab = _tab(window)
        _shown(tab, here, "fr")
        free = tab.list.item_of("X001")
        assert free.text(1) == "Sonderbauteil"
        tab.load("X001")
        assert tab.type_combo.currentText() == "Sonderbauteil" and tab.form_values()["type"] == "Sonderbauteil"
        _shown(tab, here, "de")
        assert tab.type_language == "de"
        assert tab.list.item_of("T001").text(1) == "Träger"
        assert tab.type_combo.currentText() == "Träger"
        _shown(tab, here, "en")
        assert tab.list.item_of("T001").text(1) == "Beam" and tab.type_combo.currentText() == "Beam"
        _language(here, "de")


def test_position_prints_the_type_in_the_language_of_the_report():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import test_report
    for lang, word in (("de", "Träger"), ("fr", "Poutre"), ("en", "Beam")):
        code, err, text = test_report._probe("probe_type_" + lang, f'#set-report-language("{lang}")\n#position("T001")')
        assert code == 0, err
        assert re.search(r"T001\s*:\s*" + word, text), (lang, text)
        if lang != "de":
            assert "Träger" not in text, (lang, text)
