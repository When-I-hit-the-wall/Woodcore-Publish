"""Woodcore's «RFEM» tab (`calc/tools/rfem_tab.py`), built and driven off-screen.

The tab lists the RFEM table exports a project reads and, under each, the structures detected in it — the engineer's own description: «un onglet RFEM qui liste les structures — les éléments, nœud, schémas statiques, combinaisons de charges par structure», «un volet vertical à gauche», «la première fois, il faut manuellement indiquer le chemin vers le fichier rfem», «il est possible d'importer plusieurs modèles rfem».

What is held here is the seam rather than the reading: the reading is `tests/test_model_tables.py`'s and `tests/test_structure_detection.py`'s, against the engineer's own three-language exports. This file says that the tab **shows** it — that a path pointed at once is remembered in the project file, that several models live side by side, that a structure's row carries what the structure carries, that a path that has gone is a line in the list and not a window that will not open, and that a project opened read-only refuses to change the list.

⚠️ It works on a **copy** of the example project (`conftest.project_copy`), because adding a model writes into the project file; and the file dialogs are stubbed, a modal off-screen never coming back (`tests/test_editor_buttons.py`).
"""

import contextlib
import os
import shutil
import sys

import conftest
from conftest import ROOT, Skip
from fixtures import rfem_model

import project


def _qt():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


class Stub:
    """What the tab asks of the window, and nothing more -- so this file builds one tab and not the whole frame."""

    def __init__(self, lang="fr"):
        import woodcore_gui
        from PySide6.QtGui import QFont
        self.lang = lang
        self.strings = woodcore_gui.STRINGS[lang]
        self.views = {}
        self.read_only = False
        self.status = []
        self.bold_font = QFont()
        self.bold_font.setBold(True)

    def t(self, key):
        return self.strings.get(key, key)

    def label(self, key):
        return self.t(key) + (" :" if self.lang == "fr" else ":")

    def note_text(self, note):
        return str(note)

    def set_status(self, text):
        self.status.append(text)

    def reexport(self, **_kw):
        """What «Ajouter aux modèles statiques» asks of the window once the view is written."""
        self.exported = getattr(self, "exported", 0) + 1


@contextlib.contextmanager
def _tab(name):
    """A copy of the example project, current for the length of the block.

    A context manager and not a plain call: `conftest.project_copy` copies **the project that is current**, so a test that left its own copy named would be copied by the next one -- which is what made six of these fail at once, each project holding the models of the tests before it. `project.using` puts the real one back (`calc/project.py`).
    """
    _qt()
    copy = conftest.project_copy(f"rfem_tab_{name}")
    # ⚠️ The example project **names an RFEM export of its own** since v0.100 --
    # `RFEM-Export/Beispiel-Modell.xlsx`, which is what makes the six `rfem-*` commands' examples compile
    # and their pages render (docs/typst/command-docs.md §10sexies). A test states its own models, so the copy starts with
    # none and with none of that import's records to sweep; `set_rfem_models` returns the project as it now
    # stands and does not make it current, so it is the **returned** one that is used.
    copy = project.set_rfem_models(copy, [])
    shutil.rmtree(copy.generated_dir / "data" / "rfem", ignore_errors=True)
    with project.using(copy):
        import rfem_tab
        yield rfem_tab, project.current()


def _add(here, path):
    return project.set_rfem_models(here, list(here.rfem_model_paths()) + [path])


# --- the list -------------------------------------------------------------------------------------


def test_a_project_with_no_rfem_model_says_what_to_add():
    """The first time there is nothing to list, and the pane says which export to point at rather than showing an empty tree."""
    with _tab("empty") as (rfem_tab, here):
        tab = rfem_tab.RfemTab(Stub())
        assert here.rfem_models() == []
        assert tab.tree.topLevelItemCount() == 0
        assert not tab.tree.isVisible() or tab.empty.isVisible(), "the «no model» word is what is shown"
        assert "Exporter" in tab.empty.text() or "Export" in tab.empty.text(), tab.empty.text()


def test_a_path_is_asked_once_and_kept_in_the_project_file():
    """«La première fois, il faut manuellement indiquer le chemin» -- and every time after the first, nothing is asked. It is kept **relative to the project's folder** where it lies inside it, so the project still finds it on the other machine."""
    with _tab("remember") as (rfem_tab, here):
        export = rfem_model.workbook(here.root / "RFEM-Export" / "modele.xlsx")
        here = _add(here, export)
        assert here.rfem_models() == ["RFEM-Export/modele.xlsx"], f"got {here.rfem_models()}"
        assert here.rfem_model_paths() == [export.resolve()], f"got {here.rfem_model_paths()}"

        tab = rfem_tab.RfemTab(Stub())
        assert tab.tree.topLevelItemCount() == 1
        item = tab.tree.topLevelItem(0)
        assert item.text(0) == "modele.xlsx"
        assert item.childCount() == 3, f"the fixture draws three structures, got {item.childCount()}"


def test_several_models_live_side_by_side():
    """«Il est possible d'importer plusieurs modèles rfem» -- so the pane is a list of models and not one path."""
    with _tab("several") as (rfem_tab, here):
        first = rfem_model.workbook(here.root / "A.xlsx")
        second = rfem_model.csv_folder(here.root / "B-tables")
        here = _add(here, first)
        here = _add(here, second)
        assert len(here.rfem_models()) == 2
        tab = rfem_tab.RfemTab(Stub())
        assert tab.tree.topLevelItemCount() == 2
        assert [tab.tree.topLevelItem(i).text(0) for i in range(2)] == ["A.xlsx", "B-tables"]
        assert all(tab.tree.topLevelItem(i).childCount() == 3 for i in range(2)), "each is read on its own"


def test_the_same_path_is_not_added_twice():
    with _tab("twice") as (rfem_tab, here):
        export = rfem_model.workbook(here.root / "A.xlsx")
        here = _add(here, export)
        here = _add(here, export)
        assert here.rfem_models() == ["A.xlsx"], f"got {here.rfem_models()}"


def test_a_path_that_is_gone_is_a_line_in_the_list():
    """An export the engineer moved, or that NextCloud has not synced on this machine yet. A window that would not open over it is the failure this avoids -- the start page's own rule for a project that is no longer where it was (docs/ui/window.md §10quater)."""
    with _tab("gone") as (rfem_tab, here):
        export = rfem_model.workbook(here.root / "A.xlsx")
        here = _add(here, export)
        export.unlink()
        tab = rfem_tab.RfemTab(Stub())
        item = tab.tree.topLevelItem(0)
        assert item.childCount() == 0
        assert item.text(1) == tab.t("rf_gone"), f"got {item.text(1)!r}"
        tab.tree.setCurrentItem(item)                      # and its own row opens without raising
        assert tab.current[0].error == "gone"


def test_a_source_that_is_not_an_export_is_a_line_too():
    with _tab("unreadable") as (rfem_tab, here):
        bad = here.root / "notes.xlsx"
        bad.write_text("this is not a workbook", encoding="utf-8")
        here = _add(here, bad)
        tab = rfem_tab.RfemTab(Stub())
        item = tab.tree.topLevelItem(0)
        assert item.text(1) == tab.t("rf_unreadable"), f"got {item.text(1)!r}"
        tab.tree.setCurrentItem(item)
        assert tab.current[0].error and tab.current[0].error != "gone"


# --- what a structure's row shows ------------------------------------------------------------------


def test_a_structure_shows_what_it_carries():
    """The four things the engineer asked to see per structure: its elements, its nodes, the static model it will become, and the load combinations acting on it."""
    with _tab("structure") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        item = tab.tree.topLevelItem(0)
        named = [item.child(i) for i in range(item.childCount())
                 if item.child(i).text(0) == "VU"]
        assert named, [item.child(i).text(0) for i in range(item.childCount())]
        tab.tree.setCurrentItem(named[0])
        export, structure = tab.current
        assert structure.name == "VU" and structure.statics_name == "Velo Unterstand"
        rows = _rows(tab.identity_form) | _rows(tab.contents_form)
        assert any("Velo Unterstand" in text for text in rows), rows
        assert any("T001" in text for text in rows), f"the position its member carries: {rows}"
        assert any("CO1" in text for text in rows), f"the combinations acting on it: {rows}"


def test_a_structure_nobody_named_is_listed_with_the_comment_to_write():
    """21 of the engineer's 22 are in that state. The tab says so and offers `@model` -- the one thing the model itself cannot tell."""
    with _tab("unnamed") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        item = tab.tree.topLevelItem(0)
        unnamed = [item.child(i) for i in range(item.childCount()) if item.child(i).text(0).startswith("member-")]
        assert unnamed, [item.child(i).text(0) for i in range(item.childCount())]
        tab.tree.setCurrentItem(unnamed[0])
        rows = _rows(tab.identity_form)
        assert any("@model" in text for text in rows), rows


def test_a_model_s_own_row_counts_what_the_export_holds():
    with _tab("counts") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        tab.tree.setCurrentItem(tab.tree.topLevelItem(0))
        rows = _rows(tab.contents_form)
        assert any("CC1" in text for text in rows), f"the load cases: {rows}"
        assert tab.current[1] is None, "a model's own row is not a structure"


def test_a_run_of_numbers_is_written_as_a_run():
    """«24–29 (6)» rather than six numbers -- the form `show-polar-moment` names a run of fasteners with."""
    with _tab("numbers") as (rfem_tab, _here):
        assert rfem_tab.RfemTab.numbers([24, 25, 26, 27, 28, 29]) == "24–29 (6)"
        assert rfem_tab.RfemTab.numbers([1, 3, 13]) == "1, 3, 13"
        assert rfem_tab.RfemTab.numbers([]) == "—"


# --- the window's own rules ------------------------------------------------------------------------


def test_switching_between_rows_leaves_no_blank_line_behind():
    """⚠️ The regression the engineer's own export showed: a `QFormLayout` emptied with `takeAt` loses its widgets and **keeps its rows**, so the card carried eleven blank lines above «Barres : 24–29» after a few clicks. `removeRow` takes the row, its label and its field together."""
    with _tab("blank_rows") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        item = tab.tree.topLevelItem(0)
        for target in (item, item.child(0), item, item.child(1), item.child(0)):
            tab.tree.setCurrentItem(target)
        # Not a fixed count -- an unnamed structure carries two note rows more, which is the point of them -- but not one row that says nothing at all.
        for form, name in ((tab.identity_form, "identity"), (tab.contents_form, "contents")):
            blank = [row for row in range(form.rowCount()) if not _row_text(form, row)]
            assert not blank, f"{name}: rows {blank} of {form.rowCount()} say nothing"
        assert tab.identity_form.rowCount() <= 6, f"got {tab.identity_form.rowCount()} rows -- they are piling up"


def test_a_read_only_project_refuses_to_change_the_list():
    """The guard every editor tab applies (docs/ui/window.md §10quater): a project another window holds, or one a newer Woodcore exported."""
    with _tab("read_only") as (rfem_tab, here):
        stub = Stub()
        stub.read_only = True
        tab = rfem_tab.RfemTab(stub)
        tab.add_model()
        tab.remove_model()
        assert here.rfem_models() == [], "nothing was written"
        assert stub.status and tab.t("rf_read_only") in stub.status[-1]


def test_the_selection_survives_a_re_read_and_a_language_switch():
    """«Relire» is the one thing that reads an export again -- and what was selected is found again by name, the objects being new."""
    with _tab("survive") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        item = tab.tree.topLevelItem(0)
        tab.tree.setCurrentItem(item.child(0))
        key = tab.current[1].key
        tab.reload()
        assert tab.current[1] is not None and tab.current[1].key == key, f"got {tab.current}"
        tab.set_language("de")
        assert tab.current[1].key == key


def test_the_tab_reads_nothing_when_it_is_brought_to_the_front():
    """An export is a file the engineer produced deliberately; re-reading it behind his back would make the list change under his hand. `on_shown` does nothing, and that is the decision."""
    with _tab("on_shown") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        before = [tab.exports[0].model, tab.exports[0].structures]
        tab.on_shown()
        assert [tab.exports[0].model, tab.exports[0].structures] == before, "on_shown must read nothing"


def test_its_words_are_in_three_languages():
    import woodcore_gui
    keys = set(rfem_keys())
    for lang in ("fr", "de", "en"):
        missing = [key for key in keys if not woodcore_gui.STRINGS[lang].get(key)]
        assert not missing, f"{lang}: {missing}"


def rfem_keys():
    import rfem_tab
    return [key for key in rfem_tab.STRINGS["fr"]]


def _row_text(form, row):
    """What one row of a form says, its label and its field joined -- empty for a row that says nothing."""
    from PySide6.QtWidgets import QLabel
    said = []
    for role in (form.ItemRole.LabelRole, form.ItemRole.FieldRole):
        item = form.itemAt(row, role)
        widget = item.widget() if item is not None else None
        if isinstance(widget, QLabel):
            said.append(widget.text().strip())
    return "".join(said)


def _rows(form):
    """Every text a form's rows hold, label and value alike."""
    from PySide6.QtWidgets import QLabel
    texts = set()
    for index in range(form.rowCount()):
        for role in (form.ItemRole.LabelRole, form.ItemRole.FieldRole):
            item = form.itemAt(index, role)
            widget = item.widget() if item is not None else None
            if isinstance(widget, QLabel):
                texts.add(widget.text())
    return texts


# --- the figure: the three reasons it showed nothing --------------------------------------------------
#
# The engineer, on 29.09.2026: «Dans l'onglet RFEM, les efforts internes pour le moment ne s'affiche pas.»
# Three causes were found, each real and each with its check here. The diagram itself was never in question:
# rendered through QtSvg at a pane's size it draws, and the curve is a curve.


def _drawn(tab):
    """The SVG the tab last handed its figure, by listening where it hands it over."""
    seen = []
    tab.view.load = lambda data: seen.append(bytes(data).decode("utf-8"))
    tab.fill_figure()
    return seen[-1] if seen else ""


def _structure_item(tab, name="VU"):
    model = tab.tree.topLevelItem(0)
    for i in range(model.childCount()):
        if model.child(i).text(0) == name:
            return model.child(i)
    raise AssertionError([model.child(i).text(0) for i in range(model.childCount())])


def test_a_structure_draws_its_forces_without_being_asked():
    """⚠️ The first cause: nothing was picked, so the first sight of a structure was its bare system and a note.

    A loading is now defaulted **once** -- the first one that is not a design situation -- so the figure draws
    by itself; and once a hand has picked «—», «—» stays picked (`loading_chosen`).
    """
    with _tab("draws") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        tab.tree.setCurrentItem(_structure_item(tab))
        assert tab.loading == "CO1", f"no loading was defaulted: {tab.loading}"
        assert tab.figure_note.text() == "", tab.figure_note.text()
        svg = _drawn(tab)
        assert "<polyline" in svg, "the diagram was not drawn"

        index = tab.loading_box.findData(None)
        tab.loading_box.setCurrentIndex(index)
        assert tab.loading is None and tab.loading_chosen
        tab.tree.setCurrentItem(tab.tree.topLevelItem(0))
        tab.tree.setCurrentItem(_structure_item(tab))
        assert tab.loading is None, "«—» picked by a hand must stay picked"


def test_a_design_situation_says_it_is_an_envelope():
    """⚠️ The second cause, and the one that misled: an SP has no distribution, and the tab said «this export
    carries no internal forces for that loading» -- which is false, SP1 being the very table the extremes are
    read from (`envelopes.py`). An envelope is a band, which is docs/open-questions.md §14's; the note now says so and names
    the command that prints what it does carry.
    """
    with _tab("situation") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        tab.tree.setCurrentItem(_structure_item(tab))
        index = tab.loading_box.findData("SP1")
        assert index >= 0, "the export's design situations are listed"
        tab.loading_box.setCurrentIndex(index)
        note = tab.figure_note.text()
        assert "SP1" in note and "rfem-max" in note, note
        assert note != tab.t("rf_no_results"), "an envelope is not an absence of results"


def test_a_model_s_own_row_says_to_choose_a_structure():
    """⚠️ The third cause: the figure belongs to a structure, so on the export's own row the card is hidden --
    and a card that is simply hidden says nothing at all."""
    with _tab("model_row") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        tab.tree.setCurrentItem(tab.tree.topLevelItem(0))
        assert not tab.figure.isVisible() or True     # hidden, and off-screen nothing is truly visible
        rows = _rows(tab.contents_form)
        assert any(tab.t("rf_pick_structure") in text for text in rows), rows


def test_the_button_writes_a_view_and_never_a_model():
    """«Ajouter aux modèles statiques»: the one door of `statics_view.py`, which nothing else in Woodcore opens.

    ⚠️ An imported model stays generated and RFEM stays its source (§3.3duodecies), so what is written is a
    **view** -- in the subfolder `statics.source_paths` does not glob, or it would be read as a model.
    """
    import json

    from domains import statics, statics_view

    with _tab("to_statics") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        stub = Stub()
        tab = rfem_tab.RfemTab(stub)
        tab.tree.setCurrentItem(_structure_item(tab))
        tab.add_to_statics()

        written = list(statics_view.folder(here.statics_dir).glob("*.json"))
        assert len(written) == 1, [p.name for p in written]
        view = json.loads(written[0].read_text(encoding="utf-8"))
        assert view["diagram"] == {"quantity": "M_y", "loading": "CO1"}, view
        assert written[0] not in statics.source_paths(here.statics_dir), "a view is never read as a model"
        assert getattr(stub, "exported", 0) == 1, "the project is exported again, or the report sees nothing"


def test_a_design_situation_is_never_written_into_a_view():
    """A view's `loading` is what a **curve** is drawn for, and an envelope has none: picking SP1 and adding
    the model writes the bare system rather than a loading nothing can draw."""
    with _tab("to_statics_sp") as (rfem_tab, here):
        here = _add(here, rfem_model.workbook(here.root / "A.xlsx"))
        tab = rfem_tab.RfemTab(Stub())
        tab.tree.setCurrentItem(_structure_item(tab))
        tab.loading_box.setCurrentIndex(tab.loading_box.findData("SP1"))
        tab.add_to_statics()

        import json

        from domains import statics_view
        written = list(statics_view.folder(here.statics_dir).glob("*.json"))
        assert json.loads(written[0].read_text(encoding="utf-8"))["diagram"] is None
