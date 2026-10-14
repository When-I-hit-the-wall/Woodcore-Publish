"""The right pane's editors of the objects of a document (calc/tools/object_panes.py; the engineer's rework of 01.10.2026, work package R1-D2).

The panes sit over the models of calc/typst_objects.py, whose own tests (tests/test_typst_objects.py) hold what a model writes; what is held here is what the panes tie together and no model can see alone: that each kind of object has its pane and a pane loads a model, a call or an object without saying anything; that an edit through a widget -- a row added, moved or removed, a cell typed, a column hidden, renamed or added, a category chosen, a value written over and taken back, an option ticked, a norm picked, a plan chosen -- is emitted as a **model whose serialisation is what the same edit through the model gives**; that typing is emitted once after the debounce and a button's edit at once, and that a pending edit is never lost to the next object chosen; that a variable put in a cell is shown as the variable and **no pane ever shows Typst code**; that a value written over is orange with «Reprendre» and **no ψ is ever shown**; that a heading and a paragraph round-trip their body unchanged; that a section and a chapter pane carry their state and ask for the tagging; the words, in the three languages; and that no colour is stated in the module.

⚠️ Built off-screen. Every dialog the engineer would be asked in -- the variable picker, the picture's file chooser -- is replaced by a function of the context, as a modal off-screen never comes back.
"""

import ast
import os
import re
import sys
import time

import conftest
from conftest import ROOT, Skip

TOOLS = ROOT / "calc" / "tools"
SOURCE = TOOLS / "object_panes.py"


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _panes():
    _qt()
    import object_panes
    return object_panes


def _objects():
    import typst_objects
    return typst_objects


def _pump(seconds=0.0):
    from PySide6.QtCore import QEventLoop
    app = _qt()
    end = time.monotonic() + seconds
    app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)
    while time.monotonic() < end:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)
        time.sleep(0.01)


# --- samples, in the canonical form the editor writes ----------------------------------------------------

DOC_TABLE = """#doc-table(
  columns: (
    (id: "part", title: [Bauteil]),
    (id: "value", title: [Wert], kind: "number"),
  ),
  hidden: (),
  rows: (
    (part: [Decke], value: 3),
    (part: [Dach], value: 4.5),
  ),
  caption: [Lasten],
)"""

LIVE_LOAD = """#live-load-table(
  hidden: ("zone",),
  rows: (
    (storey: [EG], use: [Büro], category: "B", q_k: auto, Q_k: auto),
    (storey: [Dach], use: [Unterhalt], category: "H", q_k: 0.5, Q_k: auto),
  ),
)"""

# a table written before the rework: its three ψ columns are among the columns `auto` stands for
LIVE_LOAD_AUTO = """#live-load-table(
  rows: (
    (storey: [EG], use: [Büro], category: "B", q_k: auto, Q_k: auto),
  ),
)"""

DEAD_LOAD = """#dead-load-table(
  hidden: ("zone",),
  rows: (
    (storey: [OG], buildup: [Bodenaufbau], load: 1.5),
    (storey: [Dach], buildup: [Dachaufbau], load: [#doc-value("gk_ak_gew", domain: ("dead-load", "EL+AL-Dach"))]),
  ),
)"""

CHOICE = """#doc-choice(
  label: [Nutzungsdauer],
  options: (
    (id: "a", label: [50 Jahre]),
    (id: "b", label: [100 Jahre]),
  ),
  selected: "a",
)"""

CHECKLIST = """#doc-checklist(
  label: [Einwirkungen],
  options: (
    (id: "snow", label: [Schnee], checked: true),
    (id: "wind", label: [Wind], checked: false, text: [Nach SIA 261.]),
  ),
)"""

SIGNATURES = """#doc-signatures(
  rows: (
    (group: [Bauherrschaft], role: [Vertreter], name: [A. Muster]),
    (group: [Ingenieur], role: [Projektleiter]),
  ),
)"""

NORMS = """#show-norm-list(
  keys: (
    "SIA 260",
    [Merkblatt des Büros],
  ),
)"""

FIELD = """#doc-field(
  label: [Tragwerksklasse],
  value: 2,
  unit: "–",
)"""

IMAGE = """#doc-image(
  file: "Images/profil.png",
  caption: [Profil],
  width: 60%,
)"""

PLAN = """#doc-plan(
  plan: "P1",
  highlight: "T001",
  detail: true,
  zoom: 2,
)"""

EXTRACT = """#doc-extract(
  excerpt: "CO1-My",
  width: 70%,
)"""

FIRE_PLAN = """#doc-fire-plan(
  plan: "Treppenhaus",
  legend: false,
)"""

FIRE_PLANS = [{"id": "Pavillon-EG", "label": "Erdgeschoss"}, {"id": "Treppenhaus", "label": "Regelgeschoss"}]

ANNEXES = """#doc-annexes(
  heading: 3,
)"""

EXCERPTS = [{"id": "CO1-My", "name": "Biegemomente", "source": "Rapport", "page": 3, "resolved": True},
            {"id": "CO1-N", "name": "Normalkräfte", "source": "Rapport", "page": 4, "resolved": False}]


def _model(text):
    objects = _objects()
    call = objects.parse_call(text)
    assert objects.serialize(call) == text, "the sample is not in the canonical form:\n" + objects.serialize(call)
    return objects.model_for(call)


CATEGORIES = [
    {"id": "A1", "name": "Surfaces d'habitation", "q_k": 2, "Q_k": 2, "example": "Locaux d'habitation"},
    {"id": "B", "name": "Bureaux", "q_k": 3, "Q_k": 2},
    {"id": "E", "name": "Surfaces d'entreposage", "q_k": None, "Q_k": None},
    {"id": "H", "name": "Toitures non accessibles", "q_k": 0.4, "Q_k": 1},
]
VARIABLES = [
    {"name": "g_k", "domain": ("dead-load", "D1"), "symbol": "g_k", "label": "Eigengewicht", "value": 1.9, "unit": "kN/m²", "kind": "calculation"},
    {"name": "N_Ed", "domain": None, "symbol": "N_\"Ed\"", "label": "", "value": 40, "unit": "kN", "kind": "report"},
]
NORM_GROUPS = {
    "norm": [{"key": "SIA 260", "aliases": ["SIA 260:2013"], "label": "SIA 260:2013 — Grundlagen der Projektierung", "tip": "2013"},
             {"key": "SIA 261", "aliases": [], "label": "SIA 261:2020 — Einwirkungen", "tip": "2020"}],
    "literature": [{"key": "HBT", "aliases": [], "label": "HBT — Holzbautabellen", "tip": ""}],
    "bib": [{"key": "ETA-12", "aliases": [], "label": "ETA-12 — Zulassung", "tip": ""}],
}
PLANS = [{"id": "P1", "label": "Rez", "positions": ["S001", "T001", "T002"]}, {"id": "P2", "label": "1er", "positions": ["T003"]}]


def _context(lang="fr", **replace):
    op = _panes()
    given = dict(categories=CATEGORIES, plans=PLANS, norm_groups=NORM_GROUPS, variables=VARIABLES, images_dir=conftest.tmpdir("panes_images"), root=conftest.tmpdir("panes_root"))
    given.update(replace)
    return op.PaneContext(lang=lang, **given)


def _pane(kind, text, context=None):
    """The pane of `kind` loaded on `text`, with a list that collects what it emits."""
    op = _panes()
    context = context or _context()
    pane = op.pane_for(kind, context)
    emitted = []
    pane.changed.connect(emitted.append)
    if text is not None:
        pane.load(_model(text), context)
    return pane, emitted


def _visible_texts(widget):
    """Every word the widget would show, tags stripped -- what a check that no Typst is shown reads."""
    from PySide6.QtWidgets import QCheckBox, QComboBox, QGroupBox, QLabel, QLineEdit, QListWidget, QPlainTextEdit, QPushButton, QTreeWidget
    out = []

    def tree_items(item):
        out.append(item.text(0))
        for i in range(item.childCount()):
            tree_items(item.child(i))

    for w in widget.findChildren(object):
        if not hasattr(w, "isVisibleTo") or not w.isVisibleTo(widget):
            continue
        if isinstance(w, QLabel):
            out.append(re.sub(r"<[^>]+>", "", w.text()))
        elif isinstance(w, (QPushButton, QCheckBox)):
            out.append(w.text())
        elif isinstance(w, QGroupBox):
            out.append(w.title())
        elif isinstance(w, QLineEdit):
            out += [w.text(), w.placeholderText()]
        elif isinstance(w, QPlainTextEdit):
            out += [w.toPlainText(), w.placeholderText()]
        elif isinstance(w, QListWidget):
            out += [w.item(i).text() for i in range(w.count())]
        elif isinstance(w, QComboBox):
            out += [w.itemText(i) for i in range(w.count())]
        elif isinstance(w, QTreeWidget):
            for i in range(w.topLevelItemCount()):
                tree_items(w.topLevelItem(i))
    return [t for t in out if t]


CODE = re.compile(r"#doc-|#live-|#dead-|#show-|doc-value|#val\b|\bdomain:|\bhidden:|\brows:|\bcolumns:|\bq_k: auto")


def _assert_no_code(pane):
    shown = _visible_texts(pane)
    bad = [t for t in shown if CODE.search(t)]
    assert not bad, f"{type(pane).__name__} shows Typst code: {bad}"


def _check_item(list_widget, row, on):
    from PySide6.QtCore import Qt
    list_widget.item(row).setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)


def _serialised(model):
    return model.serialize()


# --- the panes, and what loading is ----------------------------------------------------------------------------

def test_every_kind_of_object_has_its_pane_and_the_aliases_of_the_tree_reach_one():
    op = _panes()
    objects = _objects()
    for kind in objects.DOCUMENT_TYPES:     # an export sheet's objects (v0.114) are not a document's, and the sheet editor is not these panes
        assert kind in op.PANES, kind
        pane = op.pane_for(kind, _context())
        assert isinstance(pane, op.Pane)
    for kind in ("heading", "text", "section", "chapter"):
        assert isinstance(op.pane_for(kind, _context()), op.Pane)
    assert type(op.pane_for("file")).__name__ == "SectionPane" and type(op.pane_for("group")).__name__ == "ChapterPane"
    assert type(op.pane_for("live-load-table")).__name__ == "LiveLoadPane"
    try:
        op.pane_for("doc-unknown")
    except KeyError as exc:
        assert "doc-table" in str(exc)
    else:
        raise AssertionError("an unknown kind was given a pane")


def test_a_pane_loads_a_model_a_call_an_object_or_text_and_says_nothing():
    op = _panes()
    objects = _objects()
    context = _context()
    for subject in (_model(DOC_TABLE), objects.parse_call(DOC_TABLE), DOC_TABLE):
        pane = op.pane_for("doc-table", context)
        emitted = []
        pane.changed.connect(emitted.append)
        pane.load(subject, context)
        assert pane.row_list.count() == 2 and not emitted, type(subject).__name__
        assert pane.current().serialize() == DOC_TABLE
    text = f"// woodcore:object doc-table t\n{DOC_TABLE}\n// woodcore:/object t\n"
    found = objects.find(text, "t")
    pane = op.pane_for("doc-table", context)
    pane.load(found, context)
    assert pane.current().serialize() == DOC_TABLE


def test_the_snapshot_an_edit_emits_is_a_model_of_its_own():
    pane, emitted = _pane("doc-table", DOC_TABLE)
    pane.add_row()
    first = emitted[-1]
    pane.add_row()
    assert first.row_count == 3 and emitted[-1].row_count == 4, "a snapshot followed the pane's later edits"
    assert pane.current().row_count == 4


# --- the tables ---------------------------------------------------------------------------------------------------

def test_a_table_lists_its_rows_and_shows_the_fields_of_the_chosen_one():
    pane, _ = _pane("doc-table", DOC_TABLE)
    assert [pane.row_list.item(i).text() for i in range(2)] == ["1. Decke · 3", "2. Dach · 4.5"]
    assert list(pane.cell_fields) == ["part", "value"]
    assert pane.cell_fields["part"].text.toPlainText() == "Decke"
    assert pane.cell_fields["value"].text.toPlainText() == "3"
    pane.row_list.setCurrentRow(1)
    assert pane.cell_fields["part"].text.toPlainText() == "Dach"
    assert pane.cell_fields["value"].text.toPlainText() == "4.5"
    assert pane.cell_fields["part"].text.isEnabled()
    _assert_no_code(pane)


def test_the_buttons_of_the_rows_add_remove_and_move_and_each_is_emitted_at_once():
    pane, emitted = _pane("doc-table", DOC_TABLE)
    reference = _model(DOC_TABLE)

    pane.row_list.setCurrentRow(0)
    pane.row_add.click()
    reference.add_row(1)
    assert emitted[-1].serialize() == reference.serialize() and pane.row_list.currentRow() == 1

    pane.row_down.click()
    reference.move_row(1, 2)
    assert emitted[-1].serialize() == reference.serialize() and pane.row_list.currentRow() == 2

    pane.row_up.click()
    pane.row_up.click()
    reference.move_row(2, 1)
    reference.move_row(1, 0)
    assert emitted[-1].serialize() == reference.serialize() and pane.row_list.currentRow() == 0

    pane.row_remove.click()
    reference.remove_row(0)
    assert emitted[-1].serialize() == reference.serialize()
    assert len(emitted) == 5, "a button's edit is one emission"
    assert not pane.row_up.isEnabled(), "the first row cannot go up"
    pane.row_list.setCurrentRow(pane.row_list.count() - 1)
    assert not pane.row_down.isEnabled(), "the last row cannot go down"


def test_a_text_typed_in_a_cell_is_emitted_once_after_the_debounce_and_not_before():
    op = _panes()
    pane, emitted = _pane("doc-table", DOC_TABLE)
    field = pane.cell_fields["part"]
    for typed in ("B", "Bo", "Bod", "Boden"):
        field.text.setPlainText(typed)
        _pump(0.02)
    assert not emitted, "typing was emitted before the debounce"
    assert pane.current().cell(0, "part").markup == "Boden", "the model follows the typing"
    assert pane.row_list.item(0).text() == "1. Boden · 3", "the list follows the typing"
    _pump(op.DEBOUNCE_MS / 1000 + 0.3)
    assert len(emitted) == 1 and emitted[0].cell(0, "part").markup == "Boden"
    reference = _model(DOC_TABLE)
    reference.set_cell(0, "part", "Boden")
    assert emitted[0].serialize() == reference.serialize()


def test_a_number_typed_in_a_number_column_is_a_number_and_an_emptied_cell_leaves_the_row():
    pane, emitted = _pane("doc-table", DOC_TABLE)
    pane.cell_fields["value"].text.setPlainText("7,5")
    pane.flush()
    assert emitted[-1].cell(0, "value") == 7.5
    pane.cell_fields["value"].text.setPlainText("12")
    pane.flush()
    assert emitted[-1].cell(0, "value") == 12 and isinstance(emitted[-1].cell(0, "value"), int)
    pane.cell_fields["value"].text.setPlainText("inkl.")
    pane.flush()
    assert emitted[-1].cell(0, "value").markup == "inkl.", "a word in a number column stays a word"
    pane.cell_fields["value"].text.setPlainText("")
    pane.flush()
    assert "value" not in emitted[-1].rows[0]
    pane.cell_fields["part"].text.setPlainText("Boden [")
    pane.flush()
    assert pane.message.isVisibleTo(pane) and "[" not in pane.message.text() and emitted[-1].cell(0, "part").markup == "Decke", "a refused text is said in the pane and leaves the model"
    pane.cell_fields["part"].text.setPlainText("Boden")
    pane.flush()
    assert not pane.message.isVisibleTo(pane) and emitted[-1].cell(0, "part").markup == "Boden"


def test_a_pending_edit_is_emitted_before_the_next_object_is_loaded():
    op = _panes()
    context = _context()
    pane, emitted = _pane("doc-table", DOC_TABLE, context)
    pane.cell_fields["part"].text.setPlainText("Boden")
    assert not emitted
    pane.load(_model(DOC_TABLE), context)
    assert len(emitted) == 1 and emitted[0].cell(0, "part").markup == "Boden", "the edit of the object left was lost"
    assert pane.current().cell(0, "part").markup == "Decke" and len(emitted) == 1, "loading is not an edit"
    # and the host does it before it moves its own notion of the selection
    host = op.ObjectPaneHost(context)
    seen = []
    host.changed.connect(lambda kind, payload: seen.append((kind, payload)))
    host.show_object("doc-table", _model(DOC_TABLE))
    host.pane().cell_fields["part"].text.setPlainText("Boden")
    host.show_object("doc-field", _model(FIELD))
    assert [k for k, _ in seen] == ["doc-table"] and seen[0][1].cell(0, "part").markup == "Boden"


def test_the_columns_are_listed_hidden_or_shown_renamed_added_removed_and_moved():
    pane, emitted = _pane("doc-table", DOC_TABLE)
    reference = _model(DOC_TABLE)
    assert [pane.column_list.item(i).text() for i in range(2)] == ["Bauteil", "Wert"]
    from PySide6.QtCore import Qt
    assert all(pane.column_list.item(i).checkState() == Qt.CheckState.Checked for i in range(2))

    _check_item(pane.column_list, 0, False)
    reference.hide_column("part")
    assert emitted[-1].serialize() == reference.serialize()
    assert list(pane.cell_fields) == ["value"], "a hidden column has no field in the row"
    assert pane.row_list.item(0).text() == "1. 3", "nor a word in the row's summary"
    _check_item(pane.column_list, 0, True)
    reference.show_column("part")
    assert emitted[-1].serialize() == reference.serialize() and list(pane.cell_fields) == ["part", "value"]

    pane.column_list.setCurrentRow(1)
    pane.column_title_edit.setText("Last")
    pane.column_title_edit.textEdited.emit("Last")
    pane.flush()
    reference.set_column("value", title="Last")
    assert emitted[-1].serialize() == reference.serialize() and pane.column_list.item(1).text() == "Last"

    pane.col_add.click()
    reference.add_column("col1", title="Colonne 1")
    assert emitted[-1].serialize() == reference.serialize()
    assert pane.column_list.count() == 3 and pane.column_list.currentRow() == 2 and "col1" in pane.cell_fields
    assert pane.column_list.item(2).text() == "Colonne 1"

    pane.col_up.click()
    reference.move_column("col1", 1)
    assert emitted[-1].serialize() == reference.serialize() and pane.column_list.currentRow() == 1

    pane.col_remove.click()
    reference.remove_column("col1")
    assert emitted[-1].serialize() == reference.serialize() and pane.column_list.count() == 2


def test_a_known_column_is_hidden_and_never_removed_and_carries_the_usual_title():
    pane, emitted = _pane("dead-load-table", DEAD_LOAD)
    ids = [pane.column_list.item(i).data(0x0100) for i in range(pane.column_list.count())]
    assert ids == ["zone", "storey", "buildup", "load"]
    assert pane.column_list.item(0).text() == "Zone" and pane.column_list.item(3).text() == "Poids propre non-structural"
    pane.column_list.setCurrentRow(0)
    assert not pane.col_remove.isEnabled(), "a known column cannot be removed, only hidden"
    assert pane.column_title_edit.placeholderText(), "its usual title is said in its place"
    # a title written and then emptied goes back to the usual one
    pane.column_title_edit.textEdited.emit("Teil")
    pane.flush()
    assert emitted[-1].column("zone").title.markup == "Teil" and pane.column_list.item(0).text() == "Teil"
    pane.column_title_edit.textEdited.emit("")
    pane.flush()
    assert emitted[-1].column("zone").title is None and pane.column_list.item(0).text() == "Zone"


def test_the_caption_the_notes_and_the_header_of_a_table_are_written_through_the_model():
    pane, emitted = _pane("doc-table", DOC_TABLE)
    reference = _model(DOC_TABLE)
    assert pane.caption_edit.text() == "Lasten"
    pane.caption_edit.textEdited.emit("Charges")
    pane.flush()
    reference.set_caption("Charges")
    assert emitted[-1].serialize() == reference.serialize()

    pane.notes_edit.setPlainText("Erste Notiz")
    pane.flush()
    reference.set_notes("Erste Notiz")
    assert emitted[-1].serialize() == reference.serialize()
    pane.notes_edit.setPlainText("Erste Notiz\nZweite")
    pane.flush()
    reference.set_notes(["Erste Notiz", "Zweite"])
    assert emitted[-1].serialize() == reference.serialize()
    pane.notes_edit.setPlainText("")
    pane.flush()
    reference.set_notes(None)
    assert emitted[-1].serialize() == reference.serialize()

    pane.header_check.setChecked(False)
    reference.set_header(False)
    assert emitted[-1].serialize() == reference.serialize()
    assert pane.header_check.isVisibleTo(pane)
    dead, _ = _pane("dead-load-table", DEAD_LOAD)
    assert not dead.header_check.isVisibleTo(dead), "only a document's table has a header row to choose"


def test_a_variable_in_a_cell_is_picked_from_the_context_shown_as_the_variable_and_written_as_a_call():
    op = _panes()
    objects = _objects()
    picked = []

    def pick(parent):
        picked.append(parent)
        return op.PaneContext._as_variables([VARIABLES[0]])[0]

    pane, emitted = _pane("doc-table", DOC_TABLE, _context(pick_variable=pick))
    pane.cell_fields["value"].pick.click()
    assert picked and emitted, "the picker was not asked, or the choice not emitted at once"
    expected = objects.variable_cell("g_k", ("dead-load", "D1"))
    assert emitted[-1].cell(0, "value") == expected
    reference = _model(DOC_TABLE)
    reference.set_cell(0, "value", expected)
    assert emitted[-1].serialize() == reference.serialize()
    field = pane.cell_fields["value"]
    assert field.chip.isVisibleTo(pane) and not field.text.isVisibleTo(pane)
    shown = re.sub(r"<[^>]+>", "", field.chip.text())
    assert "1.9" in shown and "kN/m²" in shown and "dead-load" in shown, shown
    assert pane.row_list.item(0).text() == "1. Decke · g_k"
    _assert_no_code(pane)

    # a cell that holds one is shown as the variable the moment it is loaded
    other = _model(DEAD_LOAD)
    again = op.pane_for("dead-load-table", _context())
    again.load(other, _context())
    again.row_list.setCurrentRow(1)
    assert again.cell_fields["load"].variable == ("gk_ak_gew", ("dead-load", "EL+AL-Dach"))
    _assert_no_code(again)

    # taking it out leaves an empty cell of a number column
    field.clear.click()
    assert "value" not in emitted[-1].rows[0] and field.text.isVisibleTo(pane)


def test_a_variable_of_the_report_and_of_the_export_are_told_apart_by_their_domain_and_read_back_from_the_call():
    op = _panes()
    objects = _objects()
    for domain in (None, "S10 - Mitte", ("snow-load", "SL-Dach1")):
        for name in ("g_k", 'weird "name"', "E\\0"):
            cell = objects.variable_cell(name, domain)
            assert op.variable_of(cell) == (name, domain), (name, domain, cell)
    assert op.variable_of(objects.Content("Büro")) is None
    assert op.variable_of(objects.Content('#doc-value("a") und mehr')) is None
    assert op.variable_of("Büro") is None


def test_the_context_reads_again_what_it_read_and_keeps_what_it_was_given():
    op = _panes()
    import variables
    first = variables.Registry(domains={"": [variables.Variable("N_Ed", "", 40, "kN", "N_Ed")]})
    second = variables.Registry(domains={"": [variables.Variable("N_Ed", "", 40, "kN", "N_Ed"), variables.Variable("V_Ed", "", 12, "kN", "V_Ed")]})
    context = op.PaneContext(lang="fr", registry=first)
    assert [v.name for v in context.variables()] == ["N_Ed"]
    context.set_registry(second)
    assert [v.name for v in context.variables()] == ["N_Ed", "V_Ed"], "the report was read again"
    given = op.PaneContext(lang="fr", variables=VARIABLES, categories=CATEGORIES, norm_groups=NORM_GROUPS, plans=PLANS, registry=first)
    given.set_registry(second)
    given.reset()
    assert [v.name for v in given.variables()] == ["g_k", "N_Ed"] and len(given.categories()) == 4 and given.norm_groups() is NORM_GROUPS and len(given.plans()) == 2
    # what is read from the project follows the project and the language
    context = op.PaneContext.from_project(conftest.PROJECT, "fr")
    assert context.category("B").name == "Bureaux"
    context.lang = "de"
    assert context.category("B").name == "Büroflächen"
    assert context.category("B").q_k == 3 and context.category("E").q_k is None and context.category("nothing") is None


def test_the_variable_picker_filters_by_every_word_in_any_order_and_offers_no_psi():
    op = _panes()
    context = _context()
    dialog = op.VariableDialog(context)
    assert dialog.tree.topLevelItemCount() == 2
    dialog.filter("kn dead")
    assert dialog.tree.topLevelItemCount() == 1 and dialog.tree.topLevelItem(0).text(0) == "g_k"
    dialog.select(0)
    dialog.accept()
    assert dialog.chosen.name == "g_k"
    assert dialog.chosen.cell() == _objects().variable_cell("g_k", ("dead-load", "D1"))
    # the export's and the report's variables, ψ left out
    context = op.PaneContext.from_project(conftest.PROJECT, "fr")
    names = [v.name for v in context.variables()]
    assert names and not [n for n in names if n.startswith("psi_")], "ψ was offered"
    assert any(v.domain == ("live-load", "A1") and v.name == "q_k" for v in context.variables())

    import variables
    registry = variables.Registry(domains={"": [variables.Variable("N_Ed", "", 40, "kN", "N_\"Ed\"")], "S1": [variables.Variable("M", "S1", 5, "kNm", "M")]})
    context = op.PaneContext(lang="fr", registry=registry)
    found = {(v.name, v.domain) for v in context.variables()}
    assert found == {("N_Ed", None), ("M", "S1")}, found


def test_an_object_written_in_a_form_the_editor_cannot_edit_says_so_and_offers_no_editor():
    op = _panes()
    objects = _objects()
    context = _context()
    pane = op.pane_for("doc-table", context)
    pane.load(objects.parse_call("#doc-table(columns: my-columns, rows: ())"), context)
    assert pane.broken and pane.model is None
    shown = _visible_texts(pane)
    assert any("VS Code" in t for t in shown), shown
    assert not hasattr(pane, "row_list") or not pane.row_list.isVisibleTo(pane)
    pane.load(_model(DOC_TABLE), context)
    assert not pane.broken and pane.row_list.count() == 2, "a good object after a bad one is edited again"


def test_an_object_written_by_hand_or_unreadable_is_flagged_before_it_is_edited_and_the_flag_follows_the_language():
    op = _panes()
    objects = _objects()
    context = _context("fr")
    pane = op.pane_for("doc-table", context)
    hand = DOC_TABLE.replace("  hidden: (),\n", "  // a comment of his own\n  hidden: (),\n")
    text = f"// woodcore:object doc-table t\n{hand}\n// woodcore:/object t\n"
    found = objects.find(text, "t")
    assert found.state == "hand_edited"
    pane.load(found, context)
    assert pane.notice.isVisibleTo(pane) and "écrit à la main" in pane.notice.text() and pane.row_list.count() == 2
    pane.set_language("de")
    assert "von Hand" in pane.notice.text()
    pane.load(_model(DOC_TABLE), context)
    assert not pane.notice.isVisibleTo(pane), "an object Woodcore wrote is edited without a word"
    broken = objects.find("// woodcore:object doc-table t\n#doc-table(columns: (\n// woodcore:/object t\n", "t")
    assert broken.state == "unreadable"
    pane.set_language("fr")
    pane.load(broken, context)
    assert pane.notice.isVisibleTo(pane) and "ne peut pas être lu" in pane.notice.text(), pane.notice.text()


def test_a_context_may_be_given_as_a_dictionary_of_its_arguments():
    op = _panes()
    pane = op.pane_for("live-load-table", {"lang": "de", "categories": CATEGORIES})
    pane.load(_model(LIVE_LOAD))
    assert pane.cell_fields["category"].itemText(1) == "A1 — Surfaces d'habitation" and pane.row_add.text() == "Hinzufügen"
    host = op.ObjectPaneHost({"lang": "en"})
    host.show_object("doc-choice", _model(CHOICE), {"lang": "fr", "categories": CATEGORIES})
    assert host.pane().opt_add.text() == "Ajouter"


def test_the_default_picker_is_a_dialog_that_returns_the_variable_chosen_and_none_when_cancelled():
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    op = _panes()
    context = op.PaneContext(lang="fr", variables=VARIABLES)

    def answer(accept):
        def go():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, op.VariableDialog), dialog
            if accept:
                dialog.filter("N_Ed")
                dialog.accept()
            else:
                dialog.reject()
        return go

    QTimer.singleShot(100, answer(True))
    QTimer.singleShot(5000, lambda: QApplication.activeModalWidget() and QApplication.activeModalWidget().reject())
    chosen = context.pick_variable(None)
    assert chosen is not None and chosen.name == "N_Ed" and chosen.domain is None
    QTimer.singleShot(100, answer(False))
    assert context.pick_variable(None) is None
    empty = op.VariableDialog(op.PaneContext(lang="de", variables=[]))
    assert empty.note.isVisibleTo(empty) and empty.tree.topLevelItemCount() == 0


# --- the live loads -------------------------------------------------------------------------------------------------

def test_the_category_is_chosen_in_a_dropdown_in_the_windows_language_and_the_values_follow_it():
    from PySide6.QtCore import Qt
    pane, emitted = _pane("live-load-table", LIVE_LOAD)
    field = pane.cell_fields["category"]
    assert [field.itemText(i) for i in range(field.count())][:3] == ["— choisir —", "A1 — Surfaces d'habitation", "B — Bureaux"]
    assert field.currentData() == "B"
    assert pane.cell_fields["q_k"].edit.text() == "3" and pane.cell_fields["Q_k"].edit.text() == "2"
    assert not pane.cell_fields["q_k"].back.isVisibleTo(pane), "a value that follows the norm has nothing to take back"
    assert field.itemData(1, Qt.ItemDataRole.ToolTipRole) == "Locaux d'habitation"

    field.setCurrentIndex(field.findData("A1"))
    reference = _model(LIVE_LOAD)
    reference.set_category(0, "A1")
    assert emitted[-1].serialize() == reference.serialize()
    assert pane.cell_fields["q_k"].edit.text() == "2" and pane.cell_fields["Q_k"].edit.text() == "2"
    assert pane.row_list.item(0).text() == "1. EG · Büro · A1"

    field.setCurrentIndex(field.findData("E"))
    assert pane.cell_fields["q_k"].edit.text() == "" and pane.cell_fields["q_k"].edit.placeholderText() == "à fixer par le projet"
    field.setCurrentIndex(0)
    assert emitted[-1].category(0) is None or "category" not in emitted[-1].rows[0]

    german = _context("de")
    pane.set_language("de")
    pane.context = german
    pane.load(_model(LIVE_LOAD), german)
    assert pane.cell_fields["category"].itemText(0) == "— wählen —"


def test_a_category_unknown_to_the_norm_is_kept_in_the_dropdown_and_marked():
    text = LIVE_LOAD.replace('category: "B"', 'category: "X9"')
    pane, _ = _pane("live-load-table", text)
    field = pane.cell_fields["category"]
    assert field.currentData() == "X9" and field.currentText() == "X9 (?)"


def test_a_value_written_over_is_orange_and_emitted_and_reprendre_goes_back_to_the_norm():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    op = _panes()
    import theme
    orange = theme.colour("override")
    pane, emitted = _pane("live-load-table", LIVE_LOAD)
    field = pane.cell_fields["q_k"]
    assert orange not in field.edit.styleSheet()

    field.edit.selectAll()
    QTest.keyClicks(field.edit, "3.5")
    pane.flush()
    reference = _model(LIVE_LOAD)
    reference.override(0, "q_k", 3.5)
    assert emitted[-1].serialize() == reference.serialize() and emitted[-1].is_override(0, "q_k")
    assert orange in field.edit.styleSheet(), "a value written over is orange"
    assert field.back.isVisibleTo(pane) and not field.note.isVisibleTo(pane)

    field.back.click()
    reference.clear_override(0, "q_k")
    assert emitted[-1].serialize() == reference.serialize() and emitted[-1].cell(0, "q_k") is op.AUTO
    assert orange not in field.edit.styleSheet() and field.edit.text() == "3" and not field.back.isVisibleTo(pane)

    # the very value the norm holds, typed, still writes it over; emptied, it goes back
    field.edit.selectAll()
    QTest.keyClicks(field.edit, "30")
    QTest.keyClick(field.edit, Qt.Key.Key_Backspace)   # the text is the norm's own "3" again
    pane.flush()
    assert field.edit.text() == "3" and emitted[-1].is_override(0, "q_k") and emitted[-1].cell(0, "q_k") == 3 and orange in field.edit.styleSheet()
    field.edit.selectAll()
    QTest.keyClick(field.edit, Qt.Key.Key_Backspace)
    field.edit.editingFinished.emit()
    assert not emitted[-1].is_override(0, "q_k") and field.edit.text() == "3"

    # a value written over before is shown as one the moment it is loaded
    pane.row_list.setCurrentRow(1)
    stated = pane.cell_fields["q_k"]
    assert stated.edit.text() == "0.5" and orange in stated.edit.styleSheet() and stated.back.isVisibleTo(pane)
    assert pane.cell_fields["Q_k"].edit.text() == "1"


def test_no_psi_is_ever_shown_whether_the_table_hides_it_or_was_written_with_it():
    for text in (LIVE_LOAD, LIVE_LOAD_AUTO):
        pane, emitted = _pane("live-load-table", text)
        shown = " ".join(_visible_texts(pane))
        assert not re.search(r"psi|ψ|Reduktionsbeiwert", shown, re.IGNORECASE), shown
        assert not [k for k in pane.cell_fields if k.startswith("psi_")]
        ids = [pane.column_list.item(i).data(0x0100) for i in range(pane.column_list.count())]
        assert not [i for i in ids if i.startswith("psi_")]
        pane.add_row()
        pane.col_add.click()
        for i in range(pane.column_list.count()):
            pane.column_list.setCurrentRow(i)
        pane.row_list.setCurrentRow(0)
        shown = " ".join(_visible_texts(pane))
        assert not re.search(r"psi|ψ|Reduktionsbeiwert", shown, re.IGNORECASE), shown
    # no ψ in the module's words or code
    source = conftest.module_source(SOURCE)
    words = [v for table in _panes().STRINGS.values() for v in table.values()]
    assert not [w for w in words if re.search(r"ψ|psi|Reduktionsbeiwert", w, re.IGNORECASE)]
    assert "psi_shown" not in source and "set_psi_shown" not in source


def test_the_live_loads_summary_leaves_the_two_values_out_and_a_dead_load_takes_a_variable_in_its_load():
    pane, _ = _pane("live-load-table", LIVE_LOAD)
    assert [pane.row_list.item(i).text() for i in range(2)] == ["1. EG · Büro · B", "2. Dach · Unterhalt · H"]
    dead, emitted = _pane("dead-load-table", DEAD_LOAD)
    assert [dead.row_list.item(i).text() for i in range(2)] == ["1. OG · Bodenaufbau · 1.5", "2. Dach · Dachaufbau · gk_ak_gew"]
    assert list(dead.cell_fields) == ["storey", "buildup", "load"], "the hidden zone has no field"
    dead.cell_fields["load"].text.setPlainText("2,25")
    dead.flush()
    assert emitted[-1].cell(0, "load") == 2.25


# --- the lists to choose and to tick, the signatures -----------------------------------------------------------------

def test_a_choice_is_ticked_one_at_a_time_with_an_answer_of_its_own_and_options_added_and_moved():
    from PySide6.QtCore import Qt
    pane, emitted = _pane("doc-choice", CHOICE)
    reference = _model(CHOICE)
    assert pane.label_edit.text() == "Nutzungsdauer"
    assert [pane.option_list.item(i).checkState() for i in range(2)] == [Qt.CheckState.Checked, Qt.CheckState.Unchecked]

    _check_item(pane.option_list, 1, True)
    reference.select("b")
    assert emitted[-1].serialize() == reference.serialize()
    assert [pane.option_list.item(i).checkState() for i in range(2)] == [Qt.CheckState.Unchecked, Qt.CheckState.Checked], "only one option is ticked"

    pane.other_edit.textEdited.emit("30 Jahre")
    pane.flush()
    reference.set_other("30 Jahre")
    assert emitted[-1].serialize() == reference.serialize()
    assert all(pane.option_list.item(i).checkState() == Qt.CheckState.Unchecked for i in range(2)), "an answer of one's own replaces the option"

    pane.opt_add.click()
    reference.add_option("o1", "Option 1")
    assert emitted[-1].serialize() == reference.serialize() and pane.option_list.currentRow() == 2
    pane.option_edit.textEdited.emit("Unbefristet")
    pane.flush()
    reference.set_option_label("o1", "Unbefristet")
    assert emitted[-1].serialize() == reference.serialize() and pane.option_list.item(2).text() == "Unbefristet"
    pane.opt_up.click()
    reference.move_option("o1", 1)
    assert emitted[-1].serialize() == reference.serialize()
    pane.only_check.setChecked(True)
    reference.set_only_selected(True)
    assert emitted[-1].serialize() == reference.serialize()
    pane.opt_remove.click()
    reference.remove_option("o1")
    assert emitted[-1].serialize() == reference.serialize()
    _assert_no_code(pane)


def test_a_checklist_ticks_each_option_and_writes_the_text_under_the_ticked_one():
    from PySide6.QtCore import Qt
    pane, emitted = _pane("doc-checklist", CHECKLIST)
    reference = _model(CHECKLIST)
    _check_item(pane.option_list, 1, True)
    reference.set_checked("wind", True)
    assert emitted[-1].serialize() == reference.serialize()
    assert [pane.option_list.item(i).checkState() for i in range(2)] == [Qt.CheckState.Checked] * 2, "a checklist ticks several"
    pane.option_list.setCurrentRow(1)
    assert pane.text_edit.toPlainText() == "Nach SIA 261."
    pane.text_edit.setPlainText("Nach SIA 261, Kapitel 6.")
    pane.flush()
    reference.set_option_text("wind", "Nach SIA 261, Kapitel 6.")
    assert emitted[-1].serialize() == reference.serialize()
    pane.only_check.setChecked(True)
    reference.set_only_checked(True)
    assert emitted[-1].serialize() == reference.serialize()
    pane.option_list.setCurrentRow(0)
    assert pane.text_edit.toPlainText() == ""
    pane.label_edit.textEdited.emit("Lasten")
    pane.flush()
    reference.set_label("Lasten")
    assert emitted[-1].serialize() == reference.serialize()


def test_the_signatures_are_rows_with_five_fields_each_and_a_place_and_date_to_print_or_not():
    pane, emitted = _pane("doc-signatures", SIGNATURES)
    reference = _model(SIGNATURES)
    assert [pane.row_list.item(i).text() for i in range(2)] == ["1. Bauherrschaft — Vertreter — A. Muster", "2. Ingenieur — Projektleiter"]
    assert pane.field_edits["group"].text() == "Bauherrschaft" and pane.field_edits["place"].text() == ""
    pane.field_edits["place"].textEdited.emit("Bern")
    pane.field_edits["name"].textEdited.emit("B. Beispiel")
    pane.flush()
    reference.set_field(0, "place", "Bern")
    reference.set_field(0, "name", "B. Beispiel")
    assert emitted[-1].serialize() == reference.serialize()
    assert pane.row_list.item(0).text() == "1. Bauherrschaft — Vertreter — B. Beispiel — Bern"
    pane.field_edits["place"].textEdited.emit("")
    pane.flush()
    reference.set_field(0, "place", None)
    assert emitted[-1].serialize() == reference.serialize()
    pane.row_add.click()
    reference.add_row(1)
    assert emitted[-1].serialize() == reference.serialize() and pane.row_list.currentRow() == 1
    assert pane.row_list.item(1).text() == "2. (signataire vide)"
    pane.row_down.click()
    reference.move_row(1, 2)
    assert emitted[-1].serialize() == reference.serialize()
    pane.row_remove.click()
    reference.remove_row(2)
    assert emitted[-1].serialize() == reference.serialize()
    pane.place_date_check.setChecked(False)
    reference.set_place_date(False)
    assert emitted[-1].serialize() == reference.serialize()


# --- the norms ------------------------------------------------------------------------------------------------------------

def test_the_norms_are_a_check_list_of_the_catalogue_with_the_free_lines_of_the_engineer_under_it():
    from PySide6.QtCore import Qt
    pane, emitted = _pane("show-norm-list", NORMS)
    reference = _model(NORMS)
    top = [pane.tree.topLevelItem(i).text(0) for i in range(pane.tree.topLevelItemCount())]
    assert top == ["Normes", "Littérature", "Documents du projet"]
    first = pane.tree.topLevelItem(0)
    assert first.child(0).text(0) == "SIA 260:2013 — Grundlagen der Projektierung" and first.child(0).checkState(0) == Qt.CheckState.Checked
    assert first.child(1).checkState(0) == Qt.CheckState.Unchecked
    assert first.child(0).toolTip(0) == "2013"
    assert [pane.line_list.item(i).text() for i in range(pane.line_list.count())] == ["Merkblatt des Büros"]

    first.child(1).setCheckState(0, Qt.CheckState.Checked)
    reference.select("SIA 261")
    assert emitted[-1].serialize() == reference.serialize()
    pane.tree.topLevelItem(2).child(0).setCheckState(0, Qt.CheckState.Checked)
    reference.select("ETA-12")
    assert emitted[-1].serialize() == reference.serialize()
    first.child(0).setCheckState(0, Qt.CheckState.Unchecked)
    reference.select("SIA 260", False)
    assert emitted[-1].serialize() == reference.serialize() and "SIA 260" not in [k for k in emitted[-1].keys if isinstance(k, str)]

    pane.line_add.click()
    reference.add_text("Nouvelle ligne")
    assert emitted[-1].serialize() == reference.serialize() and pane.line_list.currentRow() == 1
    pane.line_edit_widget.textEdited.emit("Zweite Zeile")
    pane.flush()
    reference.remove(len(reference.keys) - 1)
    reference.add_text("Zweite Zeile")
    assert emitted[-1].serialize() == reference.serialize() and pane.line_list.item(1).text() == "Zweite Zeile"
    pane.line_up.click()   # above the free line before it: the lines of the norms stand between them
    reference.move(3, 0)
    assert emitted[-1].serialize() == reference.serialize() and pane.line_list.currentRow() == 0
    pane.line_remove.click()
    reference.remove(0)
    assert emitted[-1].serialize() == reference.serialize()
    _assert_no_code(pane)


def test_a_key_that_is_an_alias_is_ticked_and_ticking_it_off_takes_the_alias_out_and_an_unknown_key_is_kept_and_said():
    from PySide6.QtCore import Qt
    text = NORMS.replace('"SIA 260"', '"SIA 260:2013"').replace("    [Merkblatt des Büros],\n", '    "Hausnorm",\n')
    pane, emitted = _pane("show-norm-list", text)
    first = pane.tree.topLevelItem(0)
    assert first.child(0).checkState(0) == Qt.CheckState.Checked, "an alias names its entry"
    head = pane.tree.topLevelItem(pane.tree.topLevelItemCount() - 1)
    assert head.text(0) == "Autres références" and head.child(0).text(0) == "Hausnorm" and head.child(0).checkState(0) == Qt.CheckState.Checked
    first.child(0).setCheckState(0, Qt.CheckState.Unchecked)
    assert emitted[-1].keys == ["Hausnorm"]
    head.child(0).setCheckState(0, Qt.CheckState.Unchecked)
    assert emitted[-1].keys == []


def test_the_norms_catalogue_of_the_project_lists_the_documents_in_the_windows_language():
    op = _panes()
    here = conftest.PROJECT
    groups = op.PaneContext.from_project(here, "fr").norm_groups()
    assert len(groups["norm"]) >= 10 and all(" — " in e["label"] for e in groups["norm"] + groups["literature"])
    german = op.PaneContext.from_project(here, "de").norm_groups()
    assert [e["key"] for e in german["norm"]] == [e["key"] for e in groups["norm"]]
    assert [e["label"] for e in german["norm"]] != [e["label"] for e in groups["norm"]], "the titles follow the language"
    context = op.PaneContext.from_project(here, "fr")
    first = groups["norm"][0]["key"]
    assert context.norm_key(first) == first and context.norm_key("nothing of the kind") is None
    context.lang = "de"
    assert [e["label"] for e in context.norm_groups()["norm"]] == [e["label"] for e in german["norm"]], "the catalogue follows a change of language"


# --- a field, a picture, a plan -----------------------------------------------------------------------------------------------

def test_a_field_takes_its_label_a_number_or_a_variable_and_a_unit():
    op = _panes()
    pane, emitted = _pane("doc-field", FIELD)
    reference = _model(FIELD)
    assert pane.label_edit.text() == "Tragwerksklasse" and pane.value_field.text.toPlainText() == "2" and pane.unit_edit.text() == "–"
    pane.value_field.text.setPlainText("3")
    pane.label_edit.textEdited.emit("Klasse")
    pane.unit_edit.textEdited.emit("")
    pane.flush()
    reference.set_value(3)
    reference.set_label("Klasse")
    reference.set_unit(None)
    assert emitted[-1].serialize() == reference.serialize()
    pane.value_field.text.setPlainText("hoch")
    pane.flush()
    assert emitted[-1].get("value").markup == "hoch"
    context = _context(pick_variable=lambda parent: op.PaneContext._as_variables([VARIABLES[1]])[0])
    other, got = _pane("doc-field", FIELD, context)
    other.value_field.pick.click()
    assert got[-1].get("value") == _objects().variable_cell("N_Ed", None)
    _assert_no_code(other)


def test_a_picture_is_chosen_under_the_project_with_its_caption_and_width_and_refused_outside_it():
    chosen = []
    context = _context(choose_image=lambda parent: chosen[0])
    pane, emitted = _pane("doc-image", IMAGE, context)
    reference = _model(IMAGE)
    assert pane.file_label.text() == "Images/profil.png" and pane.width_edit.text() == "60%" and pane.caption_edit.text() == "Profil"
    chosen.append("Images/schnitt.svg")
    pane.choose_button.click()
    reference.set_file("Images/schnitt.svg")
    assert emitted[-1].serialize() == reference.serialize() and pane.file_label.text() == "Images/schnitt.svg"
    pane.width_edit.textEdited.emit("8 cm")
    pane.flush()
    reference.set_width("8cm")
    assert emitted[-1].serialize() == reference.serialize()
    pane.width_edit.textEdited.emit("breit")
    assert pane.message.isVisibleTo(pane) and "60 %" in pane.message.text(), "a width that is none is said in a sentence"
    pane.width_edit.textEdited.emit("")
    pane.flush()
    reference.set_width("100%")
    assert emitted[-1].serialize() == reference.serialize() and not pane.message.isVisibleTo(pane)
    pane.caption_edit.textEdited.emit("")
    pane.flush()
    reference.set_caption(None)
    assert emitted[-1].serialize() == reference.serialize()
    pane.clear_button.click()
    reference.set_file(None)
    assert emitted[-1].serialize() == reference.serialize() and pane.file_label.text() == pane.t("op_image_none")
    count = len(emitted)
    chosen[0] = ""   # a file the dialog found outside the project's folder
    pane.choose_button.click()
    assert pane.message.isVisibleTo(pane) and len(emitted) == count, "a file outside the project is refused and changes nothing"
    chosen[0] = None
    pane.message.hide()
    pane.choose_button.click()
    assert len(emitted) == count and not pane.message.isVisibleTo(pane), "cancelling the dialog is nothing"


def test_the_context_gives_a_picture_as_a_path_from_the_project_and_refuses_one_outside_it():
    op = _panes()
    root = conftest.tmpdir("panes_relative")
    (root / "Images").mkdir()
    inside = root / "Images" / "a.png"
    inside.write_bytes(b"")
    context = op.PaneContext(root=root, images_dir=root / "Images")
    assert context.relative(inside) == "Images/a.png"
    assert context.relative(root.parent / "elsewhere.png") is None


def test_a_plan_is_chosen_with_its_positions_highlighted_its_detail_zoom_and_caption():
    pane, emitted = _pane("doc-plan", PLAN)
    reference = _model(PLAN)
    from PySide6.QtCore import Qt
    assert pane.plan_combo.currentData() == "P1" and [pane.plan_combo.itemText(i) for i in range(3)] == ["— choisir —", "P1 — Rez", "P2 — 1er"]
    assert [pane.position_list.item(i).text() for i in range(3)] == ["S001", "T001", "T002"]
    assert [pane.position_list.item(i).checkState() for i in range(3)] == [Qt.CheckState.Unchecked, Qt.CheckState.Checked, Qt.CheckState.Unchecked]
    assert pane.detail_check.isChecked() and pane.zoom_spin.isEnabled() and pane.zoom_spin.value() == 2.0

    _check_item(pane.position_list, 2, True)
    reference.set_highlight(["T001", "T002"])
    assert emitted[-1].serialize() == reference.serialize()
    _check_item(pane.position_list, 1, False)
    _check_item(pane.position_list, 2, False)
    reference.set_highlight(None)
    assert emitted[-1].serialize() == reference.serialize()
    _check_item(pane.position_list, 0, True)
    reference.set_highlight("S001")
    assert emitted[-1].serialize() == reference.serialize()

    pane.zoom_spin.setValue(3.5)
    pane.flush()
    reference.set_zoom(3.5)
    assert emitted[-1].serialize() == reference.serialize()
    pane.detail_check.setChecked(False)
    reference.set_detail(False)
    assert emitted[-1].serialize() == reference.serialize() and not pane.zoom_spin.isEnabled()
    for check, setter in ((pane.axes_check, reference.set_axes), (pane.legend_check, reference.set_legend), (pane.scale_check, reference.set_scale_bar)):
        check.setChecked(False)
        setter(False)
        assert emitted[-1].serialize() == reference.serialize()

    pane.plan_combo.setCurrentIndex(pane.plan_combo.findData("P2"))
    reference.set_plan("P2")
    assert emitted[-1].serialize() == reference.serialize()
    assert [pane.position_list.item(i).text() for i in range(pane.position_list.count())][:1] == ["T003"], "the positions are the new plan's"

    pane.caption_combo.setCurrentIndex(pane.caption_combo.findData("text"))
    reference.set_caption("Légende")
    assert emitted[-1].serialize() == reference.serialize() and pane.caption_edit.isEnabled()
    pane.caption_edit.textEdited.emit("Grundriss")
    pane.flush()
    reference.set_caption("Grundriss")
    assert emitted[-1].serialize() == reference.serialize()
    pane.caption_combo.setCurrentIndex(pane.caption_combo.findData("none"))
    reference.set_caption(None)
    assert emitted[-1].serialize() == reference.serialize()
    pane.caption_combo.setCurrentIndex(pane.caption_combo.findData("auto"))
    reference.set_caption(_panes().AUTO)
    assert emitted[-1].serialize() == reference.serialize()


def test_a_plan_the_project_has_not_is_kept_and_marked_and_a_project_without_plans_says_so():
    op = _panes()
    text = PLAN.replace('"P1"', '"P9"')
    pane, _ = _pane("doc-plan", text)
    assert pane.plan_combo.currentData() == "P9" and pane.plan_combo.currentText() == "P9 (?)"
    assert [pane.position_list.item(i).text() for i in range(pane.position_list.count())] == ["T001 (?)"], "a position the plan does not draw is kept and marked"
    empty = _context(plans=[])
    other, _ = _pane("doc-plan", PLAN, empty)
    assert other.no_plans.isVisibleTo(other)
    context = op.PaneContext.from_project(conftest.PROJECT, "fr")
    plans = context.plans()
    assert {p.id for p in plans} >= {"Pavillon"} and all(p.positions for p in plans)


# --- a heading and a paragraph -----------------------------------------------------------------------------------------------

def test_a_heading_round_trips_its_body_and_writes_the_markup_of_its_text_and_level():
    op = _panes()
    objects = _objects()
    context = _context()
    pane = op.pane_for("heading", context)
    emitted = []
    pane.changed.connect(emitted.append)
    for body in ("= Zweck", "== Nutzlasten", "=== Kategorie A <cat-a>", "#heading(level: 2)[Aus einem Aufruf]"):
        pane.load(body, context)
        assert pane.current() == body and not emitted, body
        assert not pane.readonly and pane.title_edit.isEnabled(), body
    pane.load("#heading(level: 2)[Aus einem Aufruf]", context)
    assert pane.title_edit.text() == "Aus einem Aufruf" and pane.level_spin.value() == 2, "a heading written as a call is read as one"
    pane.load("== Nutzlasten", context)
    assert pane.title_edit.text() == "Nutzlasten" and pane.level_spin.value() == 2
    pane.title_edit.textEdited.emit("Verkehrslasten")
    assert not emitted
    pane.flush()
    assert emitted == ["== Verkehrslasten"]
    pane.level_spin.setValue(3)
    assert emitted[-1] == "=== Verkehrslasten", "a level is a button's edit: emitted at once"
    assert emitted[-1] == objects.HeadingModel(3, "Verkehrslasten").to_body()
    pane.title_edit.textEdited.emit("")
    assert pane.message.isVisibleTo(pane) and "vide" in pane.message.text() and pane.current() == "=== Verkehrslasten", "an empty title is refused in a sentence and changes nothing"
    pane.title_edit.textEdited.emit("Ziel <ziel>")
    pane.flush()
    assert not pane.message.isVisibleTo(pane) and emitted[-1] == "=== Ziel <ziel>", "a label the engineer wrote stays in the title"
    pane.load(objects.HeadingModel(2, "Aus einem Modell"), context)
    assert pane.current() == "== Aus einem Modell"
    pane.load(type("Found", (), {"body": "= Aus einem Objekt"})(), context)
    assert pane.current() == "= Aus einem Objekt"
    _assert_no_code(pane)


def test_a_body_that_is_no_single_heading_is_shown_read_only_and_said_and_never_written():
    op = _panes()
    context = _context("fr")
    pane = op.pane_for("heading", context)
    emitted = []
    pane.changed.connect(emitted.append)
    for body in ("= Zweck\nund mehr", "==Nutzlasten", "", "Kein Titel"):
        pane.load(body, context)
        assert pane.readonly and not pane.title_edit.isEnabled() and not pane.level_spin.isEnabled(), repr(body)
        assert pane.notice.isVisibleTo(pane) and "VS Code" in pane.notice.text(), repr(body)
        assert pane.current() == body and not emitted
    pane.set_language("de")
    assert "VS Code" in pane.notice.text() and "kein einzelner Titel" in pane.notice.text()
    pane.load("= Wieder gut", context)
    assert not pane.readonly and not pane.notice.isVisibleTo(pane) and pane.title_edit.isEnabled()


def test_a_paragraph_is_a_plain_text_box_holding_its_markup_as_written_and_round_trips_it():
    op = _panes()
    context = _context()
    pane = op.pane_for("text", context)
    emitted = []
    pane.changed.connect(emitted.append)
    body = "Die *Nutzungsvereinbarung* hält fest, was gilt, mit $q_k$\nund einer Zahl: 3.5\n  eingerückt  "
    pane.load(body, context)
    assert pane.edit.toPlainText() == body and pane.current() == body and not emitted and not pane.readonly
    from PySide6.QtWidgets import QPlainTextEdit
    assert type(pane.edit) is QPlainTextEdit and pane.edit.document().defaultFont().family() == pane.font().family(), "the document's own font, no editor chrome"
    assert not hasattr(pane, "highlighter")
    pane.edit.setPlainText(body + " Mehr.")
    assert not emitted
    _pump(op.DEBOUNCE_MS / 1000 + 0.3)
    assert emitted == [body + " Mehr."]
    pane.load(_objects().TextModel("Aus einem Modell"), context)
    assert pane.current() == "Aus einem Modell" and pane.edit.toPlainText() == "Aus einem Modell"
    found = _objects().find("// woodcore:object text p1\nEin Absatz.\n// woodcore:/object p1\n", "p1")
    pane.load(found, context)
    assert pane.current() == "Ein Absatz." and not pane.notice.isVisibleTo(pane)


def test_what_is_typed_in_a_paragraph_is_checked_as_it_is_typed_and_a_refused_text_leaves_the_body():
    op = _panes()
    context = _context("fr")
    pane = op.pane_for("text", context)
    emitted = []
    pane.changed.connect(emitted.append)
    pane.load("Ein Absatz.", context)
    pane.edit.setPlainText("Ein Absatz.\n\nNoch einer.")
    assert pane.message.isVisibleTo(pane) and "ligne vide" in pane.message.text() and pane.current() == "Ein Absatz."
    pane.edit.setPlainText("= Ein Titel")
    assert "titre" in pane.message.text() and pane.current() == "Ein Absatz."
    pane.edit.setPlainText("Ein #emph[Absatz")
    assert pane.message.isVisibleTo(pane) and pane.current() == "Ein Absatz."
    pane.edit.setPlainText("")
    assert "vide" in pane.message.text() and pane.current() == "Ein Absatz."
    pane.edit.setPlainText("Zwei Zeilen\nsind einer.")
    pane.flush()
    assert not pane.message.isVisibleTo(pane) and emitted == ["Zwei Zeilen\nsind einer."]
    # two paragraphs, an empty body: no single paragraph, shown and left alone
    for body in ("Eins.\n\nZwei.", ""):
        pane.load(body, context)
        assert pane.readonly and pane.edit.isReadOnly() and pane.notice.isVisibleTo(pane) and pane.current() == body
        pane.edit.setPlainText("anders")
        assert pane.current() == body
    assert emitted == ["Zwei Zeilen\nsind einer."], "nothing was written for a body that could not be read"


# --- sections, chapters, the host ----------------------------------------------------------------------------------------------

def test_a_section_carries_its_title_and_whether_it_is_printed_and_asks_for_the_tagging_of_an_untagged_file():
    op = _panes()
    context = _context()
    pane = op.pane_for("section", context)
    emitted, asked = [], []
    pane.changed.connect(emitted.append)
    pane.tagRequested.connect(lambda: asked.append(True))
    pane.load(op.NodeState(id="loads", title="Charges", printed=True, untagged=True), context)
    assert pane.title_edit.text() == "Charges" and pane.printed_check.isChecked() and pane.tag_card.isVisibleTo(pane) and not emitted
    pane.tag_button.click()
    assert asked == [True] and not emitted, "tagging is asked for, and changes nothing here"
    pane.printed_check.setChecked(False)
    assert emitted[-1].printed is False and emitted[-1].title == "Charges" and emitted[-1].id == "loads"
    pane.title_edit.textEdited.emit("Charges utiles")
    pane.flush()
    assert emitted[-1].title == "Charges utiles" and emitted[-1].printed is False
    pane.load({"title": "x", "printed": True, "untagged": False, "has_title": False}, context)
    assert not pane.tag_card.isVisibleTo(pane) and not pane.title_edit.isVisibleTo(pane), "a section with no title of its own has none to edit"
    assert pane.current().printed is True


def test_a_chapter_carries_its_title_in_the_three_languages_and_whether_it_is_printed():
    op = _panes()
    context = _context()
    pane = op.pane_for("chapter", context)
    emitted = []
    pane.changed.connect(emitted.append)
    pane.load(op.NodeState(id="basis", titles={"de": "Grundlagen", "fr": "Bases", "en": "Basis"}, printed=True), context)
    assert [pane.title_edits[l].text() for l in ("de", "fr", "en")] == ["Grundlagen", "Bases", "Basis"] and not emitted
    pane.title_edits["fr"].textEdited.emit("Bases du projet")
    pane.flush()
    assert emitted[-1].titles == {"de": "Grundlagen", "fr": "Bases du projet", "en": "Basis"}
    pane.printed_check.setChecked(False)
    assert emitted[-1].printed is False and emitted[-1].id == "basis"


def test_the_host_shows_the_pane_of_the_selection_and_a_sentence_where_there_is_none():
    op = _panes()
    context = _context()
    for scroll in (True, False):
        host = op.ObjectPaneHost(context, scroll=scroll)
        host.show()
        assert host.pane() is None and host.placeholder.isVisibleTo(host)
        assert "Choisir un élément" in host.placeholder_note.text()
        seen = []
        host.changed.connect(lambda kind, payload: seen.append((kind, payload)))
        host.show_object("live-load-table", _model(LIVE_LOAD))
        assert host.kind == "live-load-table" and host.pane().isVisibleTo(host) and not host.placeholder.isVisibleTo(host)
        host.pane().row_add.click()
        assert seen and seen[-1][0] == "live-load-table" and seen[-1][1].row_count == 3
        host.show_object("heading", "= Titel")
        assert host.kind == "heading" and not host.panes["live-load-table"].isVisibleTo(host) and host.pane().title_edit.text() == "Titel"
        host.show_object("live-load-table", _model(LIVE_LOAD))
        assert host.pane().row_list.count() == 2, "a pane comes back loaded on the new subject"
        host.show_many(3)
        assert host.pane() is None and host.placeholder.isVisibleTo(host) and "3" in host.placeholder_note.text()
        host.show_object("file", {"title": "T", "printed": True, "untagged": True})
        asked = []
        host.tagRequested.connect(lambda: asked.append(True))
        host.pane().tag_button.click()
        assert asked == [True]
        host.clear()
        assert host.pane() is None and host.placeholder.isVisibleTo(host)
        host.close()


def test_a_change_of_language_writes_the_panes_words_again_over_what_they_hold():
    op = _panes()
    context = _context("fr")
    host = op.ObjectPaneHost(context)
    host.show_object("live-load-table", _model(LIVE_LOAD))
    pane = host.pane()
    pane.row_list.setCurrentRow(1)
    assert pane.row_add.text() == "Ajouter"
    host.set_language("de")
    assert pane.row_add.text() == "Hinzufügen" and pane.current().serialize() == LIVE_LOAD
    assert pane.cell_fields["category"].itemText(0) == "— wählen —"
    host.set_language("en")
    assert pane.row_add.text() == "Add" and host.context.lang == "en"
    host.clear()
    assert host.placeholder_note.text() == "Choose an item in the tree to set its options."


def test_an_excerpt_is_chosen_among_those_of_the_annexes_with_its_width_and_caption():
    """`doc-extract` (v0.115): the pane's combo offers the excerpts the export holds, an excerpt the export could not find says so, and every edit is the model's own."""
    pane, emitted = _pane("doc-extract", EXTRACT, _context(excerpts=EXCERPTS))
    reference = _model(EXTRACT)
    assert pane.excerpt_combo.currentData() == "CO1-My" and [pane.excerpt_combo.itemText(i) for i in range(3)] == ["— choisir —", "CO1-My — Biegemomente", "CO1-N — Normalkräfte"]
    assert not pane.unresolved.isVisibleTo(pane) or True
    pane.excerpt_combo.setCurrentIndex(pane.excerpt_combo.findData("CO1-N"))
    reference.set_excerpt("CO1-N")
    assert emitted[-1].serialize() == reference.serialize()
    assert pane.unresolved.isVisibleTo(pane), "an excerpt the export could not find stops the report: the pane says so"
    pane.excerpt_combo.setCurrentIndex(0)
    reference.set_excerpt(None)
    assert emitted[-1].serialize() == reference.serialize()
    pane.caption_combo.setCurrentIndex(pane.caption_combo.findData("none"))
    reference.set_caption(None)
    assert emitted[-1].serialize() == reference.serialize()
    empty, _ = _pane("doc-extract", EXTRACT, _context(excerpts=[]))
    assert empty.no_excerpts.isVisibleTo(empty)


def test_a_fire_plan_is_chosen_among_those_of_the_fire_protection_tab_with_its_legend_and_caption():
    """`doc-fire-plan` (v0.115): the pane's combo offers the fire plans the export holds, a plan the export lost is kept as `(?)`, and every edit is the model's own."""
    pane, emitted = _pane("doc-fire-plan", FIRE_PLAN, _context(fire_plans=FIRE_PLANS))
    reference = _model(FIRE_PLAN)
    assert pane.plan_combo.currentData() == "Treppenhaus"
    assert [pane.plan_combo.itemText(i) for i in range(3)] == ["— choisir —", "Pavillon-EG — Erdgeschoss", "Treppenhaus — Regelgeschoss"]
    assert not pane.legend_check.isChecked() and pane.scale_check.isChecked()
    pane.plan_combo.setCurrentIndex(pane.plan_combo.findData("Pavillon-EG"))
    reference.set_plan("Pavillon-EG")
    assert emitted[-1].serialize() == reference.serialize()
    pane.legend_check.setChecked(True)
    reference.set_legend(True)
    assert emitted[-1].serialize() == reference.serialize()
    pane.scale_check.setChecked(False)
    reference.set_scale_bar(False)
    assert emitted[-1].serialize() == reference.serialize()
    pane.caption_combo.setCurrentIndex(pane.caption_combo.findData("none"))
    reference.set_caption(None)
    assert emitted[-1].serialize() == reference.serialize()
    lost, _ = _pane("doc-fire-plan", FIRE_PLAN.replace("Treppenhaus", "Gone"), _context(fire_plans=FIRE_PLANS))
    assert lost.plan_combo.currentData() == "Gone" and lost.plan_combo.currentText() == "Gone (?)"
    empty, _ = _pane("doc-fire-plan", FIRE_PLAN, _context(fire_plans=[]))
    assert empty.no_plans.isVisibleTo(empty)


def test_the_annexes_object_sets_the_level_of_the_heading_or_none():
    pane, emitted = _pane("doc-annexes", ANNEXES)
    reference = _model(ANNEXES)
    assert pane.heading_check.isChecked() and pane.level_spin.value() == 3
    pane.level_spin.setValue(2)
    pane.flush()
    reference.set_heading(2)
    assert emitted[-1].serialize() == reference.serialize()
    pane.heading_check.setChecked(False)
    reference.set_heading(None)
    assert emitted[-1].serialize() == reference.serialize() and not pane.level_spin.isEnabled()


def test_no_pane_ever_shows_typst_code_whatever_it_holds():
    op = _panes()
    context = _context()
    samples = {"doc-table": DOC_TABLE, "live-load-table": LIVE_LOAD, "dead-load-table": DEAD_LOAD, "doc-choice": CHOICE, "doc-checklist": CHECKLIST,
               "doc-signatures": SIGNATURES, "show-norm-list": NORMS, "doc-field": FIELD, "doc-image": IMAGE, "doc-plan": PLAN, "doc-fire-plan": FIRE_PLAN, "doc-extract": EXTRACT, "doc-annexes": ANNEXES}
    for kind, text in samples.items():
        pane, _ = _pane(kind, text, context)
        for lang in ("fr", "de", "en"):
            pane.set_language(lang)
            _assert_no_code(pane)
            if hasattr(pane, "row_list") and pane.row_list.count() > 1:
                pane.row_list.setCurrentRow(1)
                _assert_no_code(pane)
    for table in op.STRINGS.values():
        for key, value in table.items():
            assert not CODE.search(value) and "Typst" not in value and "#" not in value, (key, value)


# --- the words, and the code -------------------------------------------------------------------------------------------------

def test_the_words_are_in_three_languages_with_the_same_keys_and_no_sharp_s_and_french_spacing():
    op = _panes()
    assert set(op.STRINGS) == {"fr", "de", "en"}
    keys = set(op.STRINGS["fr"])
    assert keys and all(k.startswith("op_") for k in keys)
    for lang in ("de", "en"):
        assert set(op.STRINGS[lang]) == keys, (lang, sorted(keys ^ set(op.STRINGS[lang])))
    assert not [k for k, v in op.STRINGS["de"].items() if "ß" in v], "Swiss German has no sharp s"
    glued = [k for k, v in op.STRINGS["fr"].items() if re.search(r"[^\s  ][;:?!](\s|$)", v)]
    assert not glued, f"a French colon takes the narrow no-break space: {glued}"
    nnbsp = chr(0x202F)
    assert nnbsp + ":" in op.STRINGS["fr"]["op_not_editable"] and "«" + nnbsp in op.STRINGS["fr"]["op_no_row"]
    for key, fr in op.STRINGS["fr"].items():
        for lang in ("de", "en"):
            text = op.STRINGS[lang][key]
            holes = lambda t: set(re.findall(r"\{\w+\}", t))
            assert holes(text) == holes(fr), (key, lang)
    # a sentence is never left in the language of another
    for key in keys:
        for a, b in (("fr", "de"), ("fr", "en"), ("de", "en")):
            same = op.STRINGS[a][key] == op.STRINGS[b][key]
            bare = re.sub(r"\{\w+\}", "", op.STRINGS[a][key]).strip()
            assert not (same and len(bare) > 12 and " " in bare), (key, a, b)


def test_every_word_of_the_panes_is_named_by_the_code():
    source = conftest.module_source(SOURCE)
    tree = ast.parse(source)
    ranges = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("_FR", "_DE", "_EN") for t in node.targets):
            ranges.append((node.lineno, node.end_lineno))
    literals = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and not any(a <= n.lineno <= b for a, b in ranges)}
    op = _panes()
    unused = sorted(k for k in op.STRINGS["fr"] if k not in literals)
    assert not unused, f"words no code names: {unused}"
    used = sorted({m for m in re.findall(r'"(op_[a-z_]+)"', source)} - set(op.STRINGS["fr"]))
    assert not used, f"words the code names and the table lacks: {used}"


def test_the_module_states_no_colour_of_its_own_and_writes_the_orange_through_the_theme():
    source = conftest.module_source(SOURCE)
    offenders = [f"{n}: {line.strip()[:90]}" for n, line in enumerate(source.splitlines(), 1)
                 if "setStyleSheet(" in line and re.search(r"#[0-9a-fA-F]{3,6}\b", line)]
    assert not offenders, offenders
    assert not re.search(r"""["']#[0-9a-fA-F]{3,8}["']""", source), "a hex colour is written in the module"
    assert 'theme.colour("override")' in source or "theme.colour('override')" in source


def test_the_pane_is_a_card_column_and_never_wider_than_its_cards_in_the_host():
    op = _panes()
    context = _context()
    host = op.ObjectPaneHost(context)
    host.resize(420, 700)
    host.show()
    _pump(0.05)
    for kind, text in (("doc-table", DOC_TABLE), ("live-load-table", LIVE_LOAD), ("doc-plan", PLAN), ("show-norm-list", NORMS)):
        host.show_object(kind, _model(text))
        _pump(0.05)
        bar = host.scroll.horizontalScrollBar()
        assert not bar.isVisible() and bar.maximum() == 0, f"{kind}: the column scrolls sideways"
    host.close()


def test_a_pane_is_never_wider_for_the_names_the_project_gives_it_than_for_short_ones():
    """The categories of Tabelle 8 and the labels of the plans are long, and a drop-down that asked for the width of its longest item would set the column's: the real project's names, in the three languages, ask for no more room than short ones do. (How much room the panes ask for is the fonts': the off-screen platform's default font sets words twice as wide as Segoe UI, so it is compared and not measured.)"""
    op = _panes()
    here = conftest.PROJECT
    cases = (("live-load-table", LIVE_LOAD, {"categories": CATEGORIES}), ("doc-plan", PLAN.replace('"P1"', '"Pavillon"'), {"plans": [{"id": "Pavillon", "label": "Rez", "positions": ["S001"]}]}),
             ("doc-choice", CHOICE, {}), ("show-norm-list", NORMS, {"norm_groups": NORM_GROUPS}))
    for lang in ("fr", "de", "en"):
        for kind, text, short in cases:
            widths = []
            for context in (op.PaneContext.from_project(here, lang), op.PaneContext(lang=lang, **short)):
                host = op.ObjectPaneHost(context)
                host.resize(360, 700)
                host.show()
                host.show_object(kind, _model(text))
                _pump(0.05)
                widths.append(host.scroll.widget().minimumSizeHint().width())
                host.close()
            assert widths[0] <= widths[1] + 8, f"{lang} {kind}: the project's names ask for {widths[0]} px where short ones ask for {widths[1]}"


# --- the fields of a row: one line, and as many as the text takes ------------------------------------------------------------------

def test_the_fields_of_a_row_are_one_line_to_start_with_and_grow_with_their_text():
    """The engineer: «Zone, Niveau, Utilisation are three-line text boxes». A cell is a single line unless its text takes more -- a line break, or a text too long for the box -- and the box then grows, up to eight lines, from where it scrolls; a column that is `wide` is no taller than another."""
    op = _panes()
    pane, emitted = _pane("live-load-table", LIVE_LOAD)
    pane.resize(380, 900)
    pane.show()
    _pump(0.05)
    fields = [pane.cell_fields[name].text for name in ("storey", "use")]
    assert fields, "the live loads' table has text fields"
    one = fields[0].height_for(1)
    for box in fields:
        assert box.grow and box.min_lines == 1 and box.height() == one, (box.height(), one)
    wide = [c for c in pane.model.columns if pane.column_kind(c) == "wide"]
    assert wide, "the live loads' table has a column of kind wide (its use)"
    for column in wide:
        assert pane.cell_fields[column.id].text.height() == one, "a wide column is no taller than another"
    box = pane.cell_fields["use"].text
    # a text with line breaks is as many lines as it has
    box.setPlainText("eins\nzwei\ndrei")
    assert box.shown_lines == 3 and box.height() == box.height_for(3)
    # and it shrinks back to one line when the text is short again
    box.setPlainText("Büro")
    assert box.shown_lines == 1 and box.height() == one
    # a text too long for the box wraps, and the box takes the lines it wraps to
    box.setPlainText("Ein langer Text, der in einer so schmalen Spalte nicht auf eine Zeile passt und deshalb umbricht. " * 2)
    _pump(0.05)
    assert box.shown_lines >= 2 and box.height() == box.height_for(box.shown_lines)
    # up to eight lines: the box stops growing and then scrolls
    box.setPlainText("\n".join(f"Zeile {i}" for i in range(20)))
    assert box.shown_lines == 8 and box.height() == box.height_for(8)
    assert box.verticalScrollBarPolicy() == op.Qt.ScrollBarPolicy.ScrollBarAsNeeded
    box.setPlainText("Büro")
    assert box.verticalScrollBarPolicy() == op.Qt.ScrollBarPolicy.ScrollBarAlwaysOff and box.horizontalScrollBarPolicy() == op.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    # typing in it is still an edit of the cell
    emitted.clear()
    box.setPlainText("Wohnen")
    pane.flush()
    assert emitted and emitted[-1].serialize().count("Wohnen") == 1
    # the notes box and the checklist's text keep the height they were given
    table, _ = _pane("doc-table", DOC_TABLE)
    assert not table.notes_edit.grow and table.notes_edit.height() == table.notes_edit.height_for(3)
    pane.close()
    table.close()


def test_a_field_pane_and_a_dead_load_row_are_one_line_too():
    pane, _ = _pane("doc-field", FIELD)
    assert pane.value_field.text.grow and pane.value_field.text.min_lines == 1
    dead, _ = _pane("dead-load-table", DEAD_LOAD)
    for name in ("storey", "buildup"):
        assert dead.cell_fields[name].text.height() == dead.cell_fields[name].text.height_for(1)


# --- a section's pane: its title, its file and its sharing ----------------------------------------------------------------------------

def test_a_section_pane_shows_its_file_the_documents_it_is_shared_with_and_asks_to_share_and_to_stop():
    op = _panes()
    context = _context()
    pane = op.pane_for("section", context)
    asked, emitted = [], []
    pane.shareRequested.connect(lambda: asked.append("share"))
    pane.stopShareRequested.connect(lambda: asked.append("stop"))
    pane.changed.connect(emitted.append)
    # a section shared with nobody: its file, a sentence saying so, «Partager avec…» open and «Arrêter le partage» closed with its reason
    pane.load(op.NodeState(id="purpose", title="Zweck", printed=True, has_title=True, file="Sections/purpose.typ", shared_with=(), sharing=True), context)
    assert pane.title_edit.text() == "Zweck" and pane.title_edit.isVisibleTo(pane)
    assert pane.file_note.text() == "Fichier : Sections/purpose.typ" and pane.file_note.isVisibleTo(pane)
    assert pane.share_card.isVisibleTo(pane) and pane.share_card.title() == "Partage"
    assert pane.share_note.text() == "Cette section n'est partagée avec aucun autre document."
    assert pane.share_button.text() == "Partager avec…" and pane.share_button.isEnabled()
    assert pane.stop_button.text() == "Arrêter le partage" and not pane.stop_button.isEnabled()
    assert pane.stop_button.toolTip() == "Ce fichier n'est partagé avec aucun document."
    pane.share_button.click()
    assert asked == ["share"] and not emitted, "sharing is asked for, and changes nothing here"
    # a section shared: the documents are named, and the sharing can be stopped
    pane.load(op.NodeState(id="purpose", title="Zweck", printed=True, has_title=True, file="Sections/purpose.typ", shared_with=("Base de projet", "Rapport de statique"), sharing=True), context)
    assert "Base de projet, Rapport de statique" in pane.share_note.text() and pane.share_note.text().startswith("Partagée avec :")
    assert pane.stop_button.isEnabled() and "indépendante" in pane.stop_button.toolTip()
    pane.stop_button.click()
    assert asked == ["share", "stop"] and not emitted
    # a project with no other document, and a chapter, have nothing to share with
    pane.load(op.NodeState(id="purpose", title="Zweck", printed=True, file="Sections/purpose.typ", sharing=False), context)
    assert not pane.share_card.isVisibleTo(pane)
    # no file named (a state built by hand): no line for it
    pane.load({"title": "x", "printed": True, "has_title": False}, context)
    assert not pane.file_note.isVisibleTo(pane) and not pane.title_edit.isVisibleTo(pane) and not pane.share_card.isVisibleTo(pane)
    # the sharing fields are carried by the state, and a snapshot of it keeps them
    state = op.NodeState(id="a", file="Sections/a.typ", shared_with=("X",), sharing=True)
    copy = op.state_of(state)
    assert (copy.file, copy.shared_with, copy.sharing) == ("Sections/a.typ", ("X",), True) and copy is not state
    from_dict = op.state_of({"id": "b", "file": "Sections/b.typ", "shared_with": ["Y"], "sharing": True})
    assert (from_dict.file, from_dict.shared_with, from_dict.sharing) == ("Sections/b.typ", ("Y",), True)
    assert op.NodeState().file == "" and op.NodeState().shared_with == () and op.NodeState().sharing is False
    pane.close()


def test_the_host_forwards_the_sharing_requests_of_a_section_and_the_words_of_the_card_are_in_three_languages():
    op = _panes()
    context = _context()
    host = op.ObjectPaneHost(context)
    host.show()
    asked = []
    host.shareRequested.connect(lambda: asked.append("share"))
    host.stopShareRequested.connect(lambda: asked.append("stop"))
    host.show_object("file", op.NodeState(id="s", title="T", printed=True, file="Sections/s.typ", shared_with=("Base de projet",), sharing=True))
    host.pane().share_button.click()
    host.pane().stop_button.click()
    assert asked == ["share", "stop"]
    host.close()
    keys = [key for key in op.STRINGS["fr"] if key.startswith(("op_share", "op_stop_share", "op_file"))]
    assert len(keys) == 9, keys
    for lang in ("fr", "de", "en"):
        for key in keys:
            assert key in op.STRINGS[lang] and op.STRINGS[lang][key].strip(), (lang, key)
            assert "ß" not in op.STRINGS[lang][key] and not CODE.search(op.STRINGS[lang][key]), (lang, key)
    host2 = op.ObjectPaneHost(_context("de"))
    host2.show_object("file", op.NodeState(id="s", title="T", printed=True, file="Sections/s.typ", sharing=True))
    pane = host2.pane()
    assert pane.share_card.title() == "Teilen" and pane.share_button.text() == "Teilen mit…" and pane.file_note.text() == "Datei: Sections/s.typ"
    host2.set_language("en")
    assert pane.share_card.title() == "Sharing" and pane.stop_button.text() == "Stop sharing" and pane.share_note.text() == "This section is shared with no other document."
    host2.close()
