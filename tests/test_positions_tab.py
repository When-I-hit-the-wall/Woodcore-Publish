"""Woodcore's «Positions» tab (calc/tools/positions_tab.py, docs/domain/positions.md §7, docs/ui/window.md §10quater): the project's positions listed and edited, kept since v0.114 in Woodcore's own `Woodcore-Datei/positions.json` (calc/positions_store.py) -- Positionen.xlsx is no longer read, and «Importer depuis Excel…» reads one found later.

What is held here: the list in the file's order, in the «Projet» group after the plan; a position added, changed, renamed and deleted, each read back from the file and each followed by the import «Import données» runs; only the id and the type stopping a save -- a dimension that does not read as its section type said under its field and saved all the same; a file that cannot be read said in the banner and never written over; a workbook imported, the positions the project lacks added and the ones it has written over or kept as the engineer answers; a project opened read-only writing nothing; a draft surviving the window built again; the schema's element panel opening a new position here, prefilled; and the tab's words in three languages.

⚠️ The window is built off-screen on a copy of the example project (conftest.project_copy), whose positions.json is written here anew before each test. The message boxes are stubbed -- a modal off-screen never comes back -- and so is the import after a write, which would run the whole export.
"""

import contextlib
import os
import sys

import conftest
from conftest import ROOT, Skip

import project

_STATE = {}

ROWS = (
    {"position": "T001", "type": "Träger", "material": "Fichte", "strength_class": "C24", "section_type": "rec", "dimension": "100/200", "units": "mm", "moisture_class": 2, "description": "UK"},
    {"position": "S001", "type": "Stütze", "material": "Fichte", "strength_class": "C24", "section_type": "rec", "dimension": "100/200", "units": "mm", "moisture_class": 2},
    {"position": "S002", "type": "Stütze", "material": "Stahl", "strength_class": "S355", "section_type": "ROR", "dimension": "101.6x10", "units": "mm"},
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


def _write(here, rows=ROWS):
    import positions_store as store
    store.write(here, rows)


def _window():
    """One window on one copy of the example project, for the whole file: the tabs read project.current() when they act, so every test runs inside `project.using` of that copy."""
    if "window" not in _STATE:
        _qt()
        conftest.exported("calculations.json")
        here = conftest.project_copy("positions_tab")
        _write(here)
        # the copy carries no config.typ: a German project states its document language, the one the types are shown in (v0.116; the window itself is English here)
        here.config_typ.parent.mkdir(parents=True, exist_ok=True)
        here.config_typ.write_text('#let doc-lang = "de"' + chr(10) + '#let doc-region = "CH"' + chr(10), encoding="utf-8", newline=chr(10))
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        imports = []
        window.reexport = lambda **kwargs: imports.append(kwargs)   # the export «Import données» runs: its own tests are the window's
        _STATE.update(window=window, here=here, imports=imports)
    return _STATE["window"], _STATE["here"]


def _tab(window):
    import positions_tab
    return next(t for t in window.tabs if isinstance(t, positions_tab.PositionsTab))


@contextlib.contextmanager
def _boxes(question=None, warning=None):
    """The message boxes stubbed: every sentence shown is kept, a question answered by `question` (Yes where none is given), a warning by `warning` (OK where none is given)."""
    from PySide6.QtWidgets import QMessageBox
    shown = []

    def ask(_parent, _title, text, *args, **kwargs):
        shown.append(text)
        return question(text) if question else QMessageBox.StandardButton.Yes

    def warn(_parent, _title, text, *args, **kwargs):
        shown.append(text)
        return warning(text) if warning else QMessageBox.StandardButton.Ok

    saved = {name: QMessageBox.__dict__[name] for name in ("question", "warning", "information")}
    QMessageBox.question = staticmethod(ask)
    QMessageBox.warning = staticmethod(warn)
    QMessageBox.information = staticmethod(warn)
    try:
        with conftest.notices_said(lambda notice: shown.append(notice.text)):   # what was a box is a notice since v0.117
            yield shown
    finally:
        for name, value in saved.items():
            setattr(QMessageBox, name, value)


def _fresh(tab, here, rows=ROWS):
    """The positions written anew and read again, the tab on its first position with nothing unsaved."""
    _write(here, rows)
    tab.dirty = False
    tab.on_shown()
    tab.load_first()


def _rows(here):
    import positions_store as store
    return {row["position"]: row for row in store.read(here)}


def test_the_tab_lists_the_projects_positions_in_the_projects_group():
    window, here = _window()
    import woodcore_gui
    import chrome
    keys = [key for key, _factory in woodcore_gui.TABS]
    # the fire protection plan stands between them since v0.115, right under the position plan it is drawn beside
    assert keys[keys.index("tab_plan") + 1] == "tab_fire" and keys[keys.index("tab_fire") + 1] == "tab_positions", keys
    group = dict(woodcore_gui.NAV_GROUPS)["nav_project"]
    assert group[:3] == ("tab_plan", "tab_fire", "tab_positions"), group
    assert "tab_positions" in chrome.ICONS
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        assert tab.list.ids() == ["T001", "S001", "S002"], tab.list.ids()
        item = tab.list.item_of("S002")
        import positions_tab
        # the fields; the column «Longueur [m]» after them is test_the_list_shows_the_length_each_position_is_drawn_with's (issue #14)
        assert [item.text(i) for i in range(len(positions_tab.COLUMNS))] == ["S002", "Stütze", "Stahl", "S355", "ROR", "101.6x10", "mm", ""]
        assert tab.id_edit.text() == "T001" and tab.dimension_edit.text() == "100/200" and tab.moisture_combo.currentData() == 2
        assert tab.section_note.isVisibleTo(tab) and "100/200 mm" in tab.section_note.text(), tab.section_note.text()
        assert not tab.banner.isVisibleTo(tab), "no banner where the positions read"
        tab.search.setText("stahl")
        assert [pid for item, pid in tab.list.rows() if not item.isHidden()] == ["S002"]
        tab.search.setText("")
        # what the form offers is built in: the STE types, SIA 265's and SIA 263's classes, a few materials
        types = [tab.type_combo.itemText(i) for i in range(tab.type_combo.count())]
        assert "vertikal tragende Wand" in types and "Träger" in types and "Betondecke" in types
        classes = [tab.strength_combo.itemText(i) for i in range(tab.strength_combo.count())]
        assert "GL24h" in classes and "S355" in classes
        materials = [tab.material_combo.itemText(i) for i in range(tab.material_combo.count())]
        assert "Lärche" in materials and "Stahl" in materials


def test_a_position_is_added_changed_renamed_and_deleted_and_each_write_is_imported():
    window, here = _window()
    import positions_store as store
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        imports = _STATE["imports"]
        imports.clear()
        assert tab.new_position(symbol="T", floor="0")
        assert tab.current_id is None and tab.type_combo.currentText() == "Träger"
        assert tab.id_edit.text() == store.propose_id(store.read(here), "T", "0") == "T002", tab.id_edit.text()
        tab.section_combo.setCurrentIndex(tab.section_combo.findData("rec"))
        tab.dimension_edit.setText("120/240")
        tab.dimension_edit.textEdited.emit("120/240")
        tab.moisture_combo.setCurrentIndex(tab.moisture_combo.findData(1))
        with _boxes() as shown:
            assert tab.save() is True, shown
        row = _rows(here)["T002"]
        assert (row["type"], row["section_type"], row["dimension"], row["moisture_class"]) == ("Träger", "rec", "120/240", 1), row
        assert tab.current_id == "T002" and not tab.dirty and len(imports) == 1, "a position written is imported, as «Import données» imports"
        tab.description_edit.setPlainText("Pfette")
        with _boxes() as shown:
            assert tab.save() is True, shown
        assert _rows(here)["T002"]["description"] == "Pfette" and len(imports) == 2
        # renamed, after a yes naming what the rename breaks
        tab.id_edit.setText("T003")
        tab.id_edit.textEdited.emit("T003")
        with _boxes() as shown:
            assert tab.save() is True
        assert any("T002" in text and "T003" in text for text in shown), shown
        rows = _rows(here)
        assert "T002" not in rows and rows["T003"]["description"] == "Pfette" and tab.current_id == "T003"
        assert list(rows) == ["T001", "S001", "S002", "T003"], "renamed in its place"
        with _boxes() as shown:
            assert tab.delete() is True
        assert "T003" not in _rows(here) and any("T003" in text for text in shown), shown
        assert len(imports) == 4 and tab.current_id in ("T001", "S001", "S002")
        # a no leaves the positions as they were
        from PySide6.QtWidgets import QMessageBox
        before = store.path(here).read_bytes()
        tab.load("S001")
        with _boxes(question=lambda _text: QMessageBox.StandardButton.No):
            assert tab.delete() is False
        assert store.path(here).read_bytes() == before


def test_only_the_id_and_the_type_stop_a_save_and_a_section_that_does_not_read_is_said_and_saved():
    """v0.114, the engineer: a value left blank is never a blocking error. A blank position (id and type) saves; a dimension that does not read as its type is said under its field in the danger colour, with what the export will do, and saved all the same; no id, an id taken (ignoring case) and no type are refused before anything is written."""
    window, here = _window()
    import positions_store as store
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        assert tab.new_position(symbol="D", floor="0")
        assert tab.id_edit.text() == "D001"
        with _boxes() as shown:
            assert tab.save() is True, shown
        assert _rows(here)["D001"] == store.normalise({"position": "D001", "type": "Scheibenbildung Decke/Dach"})
        tab.load("S001")
        tab.dimension_edit.setText("100")
        tab.dimension_edit.textEdited.emit("100")
        reason = tab.section_note.text()
        assert tab.section_note.isVisibleTo(tab) and "100" in reason and "rec" in reason and tab.t("po_section_export") in reason, reason
        with _boxes() as shown:
            assert tab.save() is True, shown
        assert _rows(here)["S001"]["dimension"] == "100", "a section that does not read is saved: the export warns"
        # a steel designation reads as its family's size, and says why where it does not
        tab.section_combo.setCurrentIndex(tab.section_combo.findData("ROR"))
        tab.dimension_edit.setText("101.6")
        tab.dimension_edit.textEdited.emit("101.6")
        assert "D×t" in tab.section_note.text(), tab.section_note.text()   # SZS C5 writes a tube D·t (issue #9)
        tab.dimension_edit.setText("101.6x10")
        tab.dimension_edit.textEdited.emit("101.6x10")
        assert "ROR 101.6×10" in tab.section_note.text(), tab.section_note.text()
        before = store.path(here).read_bytes()
        tab.id_edit.setText("t001")
        tab.id_edit.textEdited.emit("t001")
        assert "T001" in tab.id_note.text()
        with _boxes() as shown:
            assert tab.save() is False
        assert shown and "T001" in shown[0]
        tab.id_edit.setText("S001")
        tab.type_combo.setCurrentText("")
        with _boxes() as shown:
            assert tab.save() is False
        assert shown == [tab.t("po_type_missing")], shown
        assert store.path(here).read_bytes() == before, "a refused save wrote something"
        tab.dirty = False


def test_a_file_that_cannot_be_read_is_said_and_never_written_over():
    window, here = _window()
    import positions_store as store
    with project.using(here):
        tab = _tab(window)
        store.path(here).write_text("{ broken", encoding="utf-8")
        tab.dirty = False
        tab.on_shown()
        tab.load_first()
        assert tab.banner.isVisibleTo(tab) and store.FILE in tab.banner.text(), tab.banner.text()
        assert tab.list.ids() == ["<new>"]
        tab.type_combo.setCurrentText("Träger")
        tab.id_edit.setText("T001")
        tab.id_edit.textEdited.emit("T001")
        with _boxes() as shown:
            assert tab.save() is False
        assert shown and store.FILE in shown[0], shown
        assert store.path(here).read_text(encoding="utf-8") == "{ broken"
        tab.dirty = False
        _fresh(tab, here)
        assert not tab.banner.isVisibleTo(tab)


def test_a_workbook_is_imported_adding_what_is_missing_or_replacing_after_a_question():
    window, here = _window()
    from openpyxl import Workbook
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        imports = _STATE["imports"]
        imports.clear()
        book = conftest.tmpdir("positions_tab_import") / "Positionen.xlsx"
        wb = Workbook()
        sheet = wb.active
        sheet.title = "Positions Element"
        sheet.append(["position", "type", "material", "resistance class", "moisture class"])
        sheet.append(["T001", "Träger", "Lärche", "GL24h", 1])
        sheet.append(["S005", None, "Fichte", "C24", 2])
        sheet.append(["X1", None, None, None, None])
        wb.save(book)
        asked = []
        tab.ask_import = lambda file, count, existing: asked.append((file, count, existing)) or "add"
        with _boxes() as shown:
            assert tab.import_excel(str(book)) is True
        assert asked == [("Positionen.xlsx", 2, ["T001"])], asked
        said = " ".join(shown)   # each note a notice of its own since v0.117, where they were one box
        assert "S005" in said and "X1" in said, "what the import completed and left out is said"
        rows = _rows(here)
        assert rows["T001"]["material"] == "Fichte" and rows["S005"]["type"] == "Stütze" and "X1" not in rows
        assert len(imports) == 1
        tab.ask_import = lambda *args: "replace"
        with _boxes():
            assert tab.import_excel(str(book)) is True
        assert _rows(here)["T001"]["material"] == "Lärche" and len(imports) == 2
        tab.ask_import = lambda *args: None
        with _boxes():
            assert tab.import_excel(str(book)) is False, "cancelled, nothing written"
        assert tab.default_workbook().exists()
        tab.choose_workbook = lambda: None
        assert tab.import_excel() is False
        with _boxes() as shown:
            assert tab.import_excel(str(book.with_name("absent.xlsx"))) is False
        assert shown and "absent.xlsx" in shown[0]


def test_a_project_opened_read_only_refuses_the_tabs_writes():
    window, here = _window()
    import positions_store as store
    with project.using(here):
        _write(here)
        import woodcore_gui
        reader = woodcore_gui.MainWindow(read_only=True, holder={"user": "kollege", "host": "ANDERER-PC"})
        refused = []
        reader.refuse_read_only = lambda: refused.append(True)
        try:
            tab = _tab(reader)
            before = store.path(here).read_bytes()
            tab.load("S001")
            tab.description_edit.setPlainText("x")
            assert tab.save() is False and tab.delete() is False and tab.import_excel("whatever.xlsx") is False
            assert len(refused) == 3 and store.path(here).read_bytes() == before
        finally:
            for t in reader.tabs:
                if hasattr(t, "dirty"):
                    t.dirty = False
            reader.close()


def test_a_draft_survives_the_window_built_again():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        assert tab.new_position(symbol="S", floor="1")
        tab.material_combo.setCurrentText("Buche")
        assert tab.dirty and tab.id_edit.text() == "S101"
        window.rebuild()
        tab = _tab(window)
        assert tab.current_id is None and tab.dirty and tab.id_edit.text() == "S101" and tab.floor_edit.text() == "1"
        assert tab.material_combo.currentText() == "Buche" and tab.type_combo.currentText() == "Stütze"
        tab.dirty = False
        window.update_tab_marks()


def test_the_schema_and_the_window_open_a_new_position_here_prefilled():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        plan = next(t for t in window.tabs if type(t).__name__ == "PlanTab")
        window.tab_widget.setCurrentWidget(plan)
        assert window.new_position(symbol="T", floor="1")
        assert window.tab_widget.currentWidget() is tab, "the window's new_position does not bring the Positions tab forward"
        assert tab.current_id is None and tab.type_combo.currentText() == "Träger" and tab.floor_edit.text() == "1" and tab.id_edit.text() == "T101"
        tab.dirty = False
        # the schema's element panel: the button beside its Position
        schema = next(t for t in window.tabs if type(t).__name__ == "SchemaTab")
        window.tab_widget.setCurrentWidget(schema)
        tab.load("S001")
        schema.new_position_button.click()
        assert window.tab_widget.currentWidget() is tab and tab.current_id is None
        assert tab.type_combo.currentText() == "Stütze" and tab.id_edit.text() == "S003", tab.id_edit.text()
        tab.dirty = False
        window.update_tab_marks()


def test_the_tabs_words_are_in_three_languages():
    _qt()
    import woodcore_gui
    import positions_tab
    keys = set(positions_tab.STRINGS["fr"])
    for lang in ("fr", "de", "en"):
        assert set(positions_tab.STRINGS[lang]) == keys, lang
        assert all(positions_tab.STRINGS[lang][key].strip() for key in keys), lang
        assert keys <= set(woodcore_gui.STRINGS[lang]), "the tab's words are not merged into the window's"
        assert "ß" not in "".join(positions_tab.STRINGS["de"].values())
    assert all(key == "tab_positions" or key.startswith(("po_", "warn_positions_")) for key in keys), sorted(keys)
    assert all(value in keys for value in positions_tab.REFUSALS.values())
    assert not any("Positionen.xlsx" in text and key not in ("po_import_tip",) for lang in ("fr", "de", "en")
                   for key, text in positions_tab.STRINGS[lang].items()), "the tab no longer speaks of the workbook as the positions' place"
    # every note positions_store gives the window has its sentence
    import positions_store
    source = (ROOT / "calc" / "positions_store.py").read_text(encoding="utf-8")
    import re
    for code in set(re.findall(r'engine\.Note\("(positions_[a-z_]+)"', source)):
        assert "warn_" + code in keys, code
    note = positions_store.engine.Note("positions_migrated", "x", count=3, workbook="Positionen.xlsx", file="Woodcore-Datei/positions.json", archive="_Archiv/a.xlsx")
    assert "3" in woodcore_gui.note_text(note, "de") and "_Archiv/a.xlsx" in woodcore_gui.note_text(note, "fr")


def test_the_dimension_is_typed_in_the_boxes_of_the_section_type_and_a_text_nobody_touched_is_never_rewritten():
    """v0.117, the engineer: «lorsque le type de section est donné, une section "Dimension" qui apparait avec des textbox différentes: "rec" => largeur, hauteur; "plaque" => épaisseur». The boxes write the line the form reads, and only when one is typed in (`on_dimension_field`); a position opened and saved untouched keeps its text byte for byte."""
    window, here = _window()
    import positions_store as store
    odd = ({"position": "T001", "type": "Träger", "material": "Fichte", "strength_class": "C24", "section_type": "rec", "dimension": "100 x 200", "units": "mm", "moisture_class": 2},
           {"position": "P001", "type": "Platte", "section_type": "pla", "dimension": "22", "units": "mm"},
           {"position": "C001", "type": "Platte", "section_type": "clt", "dimension": "20/30/20", "units": "mm"},
           {"position": "D001", "type": "Platte", "section_type": "", "dimension": "OSB, nach Wahl"},
           {"position": "R001", "type": "Platte", "section_type": "rec", "dimension": "nach Plan", "units": "mm"})
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here, odd)
        fields = tab.dim_fields
        shown = lambda: sorted(letter for letter, (caption, edit) in fields.items() if not edit.isHidden())   # noqa: E731
        # a rectangle: its width and its height, filled from the text as it is written, and no line of text
        tab.load("T001")
        assert shown() == ["b", "h"] and fields["b"][1].text() == "100" and fields["h"][1].text() == "200", [fields[k][1].text() for k in fields]
        assert tab.dimension_edit.isHidden() and tab.captions["dimension"].isHidden() and tab.dim_by_fields
        assert fields["b"][0].text() == "Width b" and fields["h"][0].text() == "Height h", "the shared widget's words (section_fields)"
        # opened and saved untouched, the text is what it was: «100 x 200» is not rewritten as «100/200»
        assert tab.form_values()["dimension"] == "100 x 200"
        tab.dirty = True
        with _boxes() as said:
            assert tab.save() is True, said
        assert _rows(here)["T001"]["dimension"] == "100 x 200", "a dimension nobody touched is never rewritten"
        # a box typed in writes the line, a half-typed one keeps its place, and the section note reads what is there
        tab.load("T001")
        fields["h"][1].setText("240")
        fields["h"][1].textEdited.emit("240")
        assert tab.dimension_edit.text() == "100/240" and tab.dirty and tab.dim_by_fields
        fields["h"][1].setText("")
        fields["h"][1].textEdited.emit("")
        assert tab.dimension_edit.text() == "100/" and tab.dim_by_fields, "typing does not turn the boxes into a line"
        assert tab.t("po_section_export") in tab.section_note.text() and tab.section_note.isVisibleTo(tab), "and the problem is said"
        fields["h"][1].setText("240")
        fields["h"][1].textEdited.emit("240")
        with _boxes() as said:
            assert tab.save() is True, said
        assert _rows(here)["T001"]["dimension"] == "100/240"
        # a plate has one box, its thickness; the others are hidden
        tab.load("P001")
        assert shown() == ["t"] and fields["t"][1].text() == "22" and fields["t"][0].text() == "Thickness t"
        # a CLT panel: a box a layer (issue #9); no type keeps the line it always had
        tab.load("C001")
        assert shown() == ["layer1", "layer2", "layer3"] and tab.dim_by_fields and [fields[f"layer{n}"][1].text() for n in (1, 2, 3)] == ["20", "30", "20"]
        tab.load("D001")
        assert shown() == [] and not tab.dim_by_fields and not tab.dimension_edit.isHidden() and tab.dimension_edit.text() == "OSB, nach Wahl"
        # a text that does not read as its type stays on its line, where it can be seen and mended -- the boxes do not swallow it
        tab.load("R001")
        assert shown() == [] and tab.dimension_edit.text() == "nach Plan" and not tab.dim_by_fields
        # the type chosen changes the boxes: a round section has a diameter, and an empty type gives the line back
        tab.load("T001")
        tab.dimension_edit.setText("")
        tab.section_combo.setCurrentIndex(tab.section_combo.findData("cir"))
        assert shown() == ["d"] and fields["d"][0].text() == "Diameter d"
        fields["d"][1].setText("160")
        fields["d"][1].textEdited.emit("160")
        assert tab.form_values()["dimension"] == "160"
        tab.section_combo.setCurrentIndex(tab.section_combo.findData(""))
        assert shown() == [] and not tab.dimension_edit.isHidden()
        tab.dirty = False
    # the three languages
    import positions_tab
    import section_fields
    for lang in ("fr", "de", "en"):
        assert positions_tab.STRINGS[lang].get("po_dim_card", "").strip(), lang
        assert set(section_fields.STRINGS[lang]) == set(section_fields.STRINGS["fr"]) and all(v.strip() for v in section_fields.STRINGS[lang].values()), lang


def _drawn(here):
    """A position plan at 100 sheet units a metre drawing T001 twice -- 4 m and 2.5 m -- and S001 as a column, written in the copy's plans folder."""
    import json
    from domains import plan
    source = plan.new_source("EG", floor="1")
    source["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1.0}
    source["elements"] = [{"type": "T", "label": "T001", "points": [[0, 0], [400, 0]]},
                          {"type": "T", "label": "T001", "points": [[0, 100], [250, 100]]},
                          {"type": "S", "label": "S001", "points": [[500, 500]]}]
    here.plans_dir.mkdir(parents=True, exist_ok=True)
    (here.plans_dir / "EG.json").write_text(json.dumps(source), encoding="utf-8")


def test_the_list_shows_the_length_each_position_is_drawn_with():
    """Issue #14 (REQ-003, UI-007): a column «Longueur [m]» after the fields -- T001's two beams added up, nothing for a column -- and never a field of positions.json."""
    import positions_tab
    window, here = _window()
    with project.using(here), _boxes():
        tab = _tab(window)
        _drawn(here)
        _fresh(tab, here)
        # the lengths are the export's (spec 2026-10-21-commandes-typst-refonte, UI-003): read again once data/quantities.json says what EG draws
        from domains import quantities as q
        q.write_document(here)
        tab.on_shown()
        assert tab.list.columnCount() == len(positions_tab.COLUMNS) + 1
        assert tab.list.headerItem().text(positions_tab.LENGTH_COLUMN) == tab.t("po_col_length")
        from domains import plan, quantities
        import positions_store as store
        found, _notes = quantities.rows(plan.position_plan_sources(here.plans_dir), store.read(here))
        expected = quantities.length_by_position(found)   # the copy's other plans may draw T001 too
        cells = {pid: item.text(positions_tab.LENGTH_COLUMN) for item, pid in tab.list.rows()}
        assert expected["T001"] >= 6.5 and cells["T001"] == quantities.metres(expected["T001"]), (cells, expected)
        assert cells["S002"] == "" and (cells["S001"] == "" if expected.get("S001") is None else True), cells
        tab.load("T001")
        tab.save()
        after = _rows(here)
        assert all("length" not in row and "length_m" not in row for row in after.values()), "the length is never written"
        tab.dirty = False
