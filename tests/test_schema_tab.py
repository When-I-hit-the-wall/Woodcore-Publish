"""The «Schémas» tab and its canvas, built off-screen (docs/ui/window.md §10quater).

What a click puts down is the half of this tab a test can reach without a window: `SchemaCanvas.place()` and the `add_*` behind it are plain Python on a plain dict, exactly as statics_canvas's are, so a piece, a fastener marker, an aid and a dimension can be drawn here and the source they make checked by the very rules `export_all.py` applies. That is the guard that matters: **a schema the tab can draw must be a schema the export accepts**, or the engineer meets the refusal only at *Enregistrer*.

What it cannot reach is the pointer itself -- hover, drag, the rubber band, what the bar looks like. That is the engineer's own walk through the window, which the plan's verification section asks for in so many words.

⚠️ Skipped where PySide6 is not installed: a machine that only builds the report is a legitimate machine.
"""

import os
import sys

from conftest import ROOT, Skip
from domains import schema as model
import validation

_app = None


def _canvas():
    """A canvas on an empty schema, off-screen. The tab itself is built by _tab() below; a canvas alone is enough for what a click puts down."""
    global _app
    path = str(ROOT / "calc" / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    _app = QApplication.instance() or QApplication([])
    from schema_canvas import SchemaCanvas
    canvas = SchemaCanvas()
    canvas.set_source(model.new_source("D99"))
    return canvas


def _drawn(canvas):
    """The source as it stands, checked the way the export checks it."""
    model.check_source(canvas.source, "D99.json")
    return canvas.source


# --- what a click puts down ------------------------------------------------------

def test_a_linear_element_is_drawn_by_two_clicks():
    canvas = _canvas()
    canvas.set_tool("linear")
    canvas.place((0.0, 0.0))
    canvas.place((300.0, 0.0))
    source = _drawn(canvas)
    assert len(source["elements"]) == 1
    element = source["elements"][0]
    assert element["kind"] == "linear"
    assert element["points"] == [[0, 0], [300, 0]]


def test_the_end_just_placed_becomes_the_next_anchor():
    """AutoCAD's chain, statics_canvas's own: the second click is where the next piece starts tracking from."""
    canvas = _canvas()
    canvas.set_tool("linear")
    canvas.place((0.0, 0.0))
    canvas.place((300.0, 0.0))
    assert canvas.acquired == (300.0, 0.0)
    assert canvas.rays, "the anchor carries the rays the cursor may lock to"


def test_an_area_element_is_drawn_by_two_diagonal_clicks():
    canvas = _canvas()
    canvas.set_tool("area")
    canvas.set_area_mode("diagonal")
    canvas.place((0.0, 0.0))
    canvas.place((100.0, 50.0))
    source = _drawn(canvas)
    assert source["elements"][0]["kind"] == "area"
    assert source["elements"][0]["points"] == [[0, 0], [100, 0], [100, 50], [0, 50]]


def test_an_area_element_drawn_edgewise_lands_on_the_same_box():
    """The three modes must agree, or the engineer sees the rectangle jump when he switches tool (schema.py's own rule, held again here through the canvas)."""
    canvas = _canvas()
    canvas.set_tool("area")
    canvas.set_area_mode("edge")
    canvas.place((0.0, 0.0))
    canvas.place((100.0, 0.0))
    canvas.place((0.0, 50.0))
    source = _drawn(canvas)
    assert source["elements"][0]["points"] == [[0, 0], [100, 0], [100, 50], [0, 50]]


def test_a_connector_marker_carries_the_tool_s_own_kind():
    canvas = _canvas()
    canvas.set_tool("connector:Stabdübel")
    canvas.place((70.0, 0.0))
    source = _drawn(canvas)
    assert source["connectors"][0]["kind"] == "Stabdübel"
    assert (source["connectors"][0]["x"], source["connectors"][0]["z"]) == (70, 0)


def test_a_point_aid_is_shown_and_a_construction_line_is_not():
    """The module's own rule, met here at the moment each is drawn: a point or a centre is exported, a line only if it is asked for."""
    canvas = _canvas()
    canvas.set_tool("aid-centre")
    canvas.place((0.0, 0.0))
    canvas.set_tool("aid-vertical")
    canvas.place((50.0, 0.0))
    source = _drawn(canvas)
    centre = next(a for a in source["aids"] if a["kind"] == "centre")
    line = next(a for a in source["aids"] if a["kind"] == "vertical")
    assert centre["shown"] is True
    assert line["shown"] is False
    assert line["angle"] == 90


def test_a_perpendicular_aid_takes_its_angle_from_the_line_it_names():
    canvas = _canvas()
    canvas.set_tool("linear")
    canvas.place((0.0, 0.0))
    canvas.place((100.0, 0.0))     # an element along x
    canvas.set_tool("aid-perpendicular")
    canvas.place((50.0, 20.0))     # the point it passes through
    canvas.place((50.0, 1.0))      # near the element: the line it is perpendicular to
    source = _drawn(canvas)
    aid = next(a for a in source["aids"] if a["kind"] == "perpendicular")
    assert abs(abs(aid["angle"]) - 90.0) < 1e-6


def test_a_perpendicular_aid_with_nothing_to_measure_from_is_refused():
    canvas = _canvas()
    seen = []
    canvas.refused.connect(seen.append)
    canvas.set_tool("aid-perpendicular")
    canvas.place((0.0, 0.0))
    canvas.place((10.0, 10.0))
    assert seen == ["reference"]
    assert canvas.source["aids"] == []


def test_a_length_dimension_takes_three_clicks_and_the_third_is_its_offset():
    canvas = _canvas()
    canvas.set_tool("dimension-horizontal")
    canvas.place((0.0, 0.0))
    canvas.place((300.0, 0.0))
    canvas.place((150.0, -80.0))
    source = _drawn(canvas)
    dim = source["dimensions"][0]
    assert dim["kind"] == "horizontal"
    assert dim["offset"] == -80
    value, unit = model.dimension_value(source, dim)
    assert (value, unit) == (300.0, "mm")


def test_an_angle_dimension_names_two_elements_and_the_sector_clicked():
    canvas = _canvas()
    canvas.set_tool("linear")
    canvas.place((-100.0, 0.0))
    canvas.place((100.0, 0.0))
    canvas.set_tool("linear")
    canvas.place((0.0, -100.0))
    canvas.place((0.0, 100.0))
    ids = [e["id"] for e in canvas.source["elements"]]
    canvas.set_tool("dimension-angle")
    canvas.dim_elements = list(ids)          # the two clicks that name the elements
    canvas.place((40.0, 40.0))               # the third: the radius, and which sector
    source = _drawn(canvas)
    dim = source["dimensions"][0]
    assert dim["kind"] == "angle"
    assert "bearing" in dim
    value, unit = model.dimension_value(source, dim)
    assert abs(value - 90.0) < 1e-6 and unit == "°"


def test_everything_drawn_together_still_passes_the_export_s_own_checks():
    """The guard that matters: a schema the tab can draw is a schema the export accepts."""
    canvas = _canvas()
    canvas.set_tool("linear")
    canvas.place((0.0, 0.0))
    canvas.place((300.0, 0.0))
    canvas.set_tool("area")
    canvas.set_area_mode("diagonal")
    canvas.place((0.0, 40.0))
    canvas.place((120.0, 90.0))
    canvas.set_tool("connector:Nagel")
    canvas.place((60.0, 0.0))
    canvas.set_tool("aid-point")
    canvas.place((0.0, 0.0))
    canvas.set_tool("dimension-vertical")
    canvas.place((0.0, 0.0))
    canvas.place((0.0, 90.0))
    canvas.place((-60.0, 45.0))
    source = _drawn(canvas)      # check_source: the very rules export_all.py applies
    # every id unique across the four collections, which is what `highlight` rests on
    ids = model.all_ids(source)
    assert len(ids) == len(set(ids))
    assert len(source["elements"]) == 2 and source["connectors"] and source["aids"] and source["dimensions"]


# --- the tab ---------------------------------------------------------------------

def _tab():
    canvas = _canvas()   # builds the QApplication, off-screen
    del canvas
    import woodcore_gui
    window = woodcore_gui.MainWindow()
    window.show()
    tab = next(t for t in window.tabs if type(t).__name__ == "SchemaTab")
    tab.window_ref = window   # the window outlives this call, or the tab goes with it
    return tab


def test_the_tab_is_listed_and_builds():
    tab = _tab()
    assert tab.canvas is not None
    assert tab.center_split.count() == 3, "the bar, the drawing and the lists, as three panes to drag"


def test_the_tab_carries_the_six_lists():
    """Linear, area, connectors, points (v0.77), aids, dimensions."""
    tab = _tab()
    assert tab.tables.count() == 6
    assert [tab.tables.tabText(i) for i in range(6)][2:4] == [tab.t("sc_tab_connectors"), tab.t("sc_tab_points")]


def test_the_tab_offers_every_tool_of_the_canvas():
    """A tool the canvas knows and the bar does not is a tool nobody can choose."""
    from schema_canvas import TOOLS
    tab = _tab()
    drawing_tools = {name for name, spec in TOOLS.items() if spec.get("geo")}
    assert drawing_tools <= set(tab.tool_buttons)


def test_every_tool_shows_its_own_symbol():
    """The bar shows what a tool draws, and no two tools may show the same thing.

    ⚠️ The case this is here for: an aid line and a dimension share three kind names -- `horizontal`, `vertical`, `parallel` -- so asking `swatch()` for a dimension tool's own `kind` draws the construction line's dashes on the cotation buttons, and four tools become indistinguishable. `schema_tab.tool_icon` maps them through `DIMENSION_SWATCHES` for exactly that reason.
    """
    from xml.dom import minidom
    from domains import schema_svg
    import schema_tab
    from schema_canvas import TOOLS

    drawn = {}
    for tool, spec in TOOLS.items():
        if not spec.get("geo"):
            continue
        # ⚠️ Asked of schema_tab rather than worked out again here. This test used to restate the
        # mapping, and the restatement broke in v0.73 the moment a tool arrived whose spec carries a
        # `verb` and no `kind` -- a guard failing because the thing it guards grew correctly.
        kind = schema_tab.swatch_kind(tool)
        assert kind is not None, f"{tool} has a geo and no swatch"
        svg = schema_svg.swatch(kind)
        minidom.parseString(svg)          # QtSvg reads XML, not nearly-XML
        assert svg not in drawn.values(), f"{tool} shows the same symbol as {[t for t, s in drawn.items() if s == svg][0]}"
        drawn[tool] = svg
    assert schema_tab.tool_icon("dimension-angle") is not None
    # The two buttons that are actions rather than tools are not in TOOLS, and carry symbols too.
    for verb in ("split", "merge"):
        svg = schema_svg.swatch(verb)
        minidom.parseString(svg)
        assert svg not in drawn.values(), f"{verb} shows the same symbol as another tool"
        drawn[verb] = svg


def test_the_tabs_texts_are_the_same_in_all_three_languages():
    import schema_tab
    keys = {lang: set(texts) for lang, texts in schema_tab.STRINGS.items()}
    assert keys["fr"] == keys["de"] == keys["en"]


# --- v0.75: the element's panel, the lists, the crop, the typed angle --------------------------

POSITIONS_75 = {
    "T001": {"material": "C24", "dimension": "100/200", "units": "mm", "type": "Träger", "moisture_class": 2},
    "S001": {"material": "C24", "dimension": "100/200", "units": "mm", "type": "Stütze", "moisture_class": 2},
}


def _tab_75():
    """The tab on a draft of its own -- a beam through a column with four markers -- against positions of its own, so nothing the project holds is read or written."""
    tab = _tab()
    source = model.new_source("D99")
    source["elements"] = [
        {"id": "E1", "kind": "linear", "points": [[-230, 0], [230, 0]], "view": "h", "position": "T001"},
        {"id": "E2", "kind": "linear", "points": [[0, -100], [0, 230]], "view": "h", "position": "S001"},
    ]
    source["aids"] = [{"id": "A1", "kind": "vertical", "x": 100, "z": 0, "angle": 90, "shown": False}]
    tab.open_source(source, None, False)
    tab.positions = dict(POSITIONS_75)
    tab.canvas.set_positions(tab.positions)
    tab.fill_positions()
    tab.fill_tables()
    return tab


def test_the_panel_shows_what_an_element_is_and_where_its_section_comes_from():
    tab = _tab_75()
    tab.canvas.select(("elements", "E1"))
    assert tab.position_combo.currentData() == "T001"
    assert tab.side_fields["b"]["spin"].value() == 100 and tab.side_fields["h"]["spin"].value() == 200
    assert tab.side_fields["h"]["spin"].suffix() == " mm — T001", "a side that follows says where from in its own field (v0.117: «— T001», no more «repris de»)"
    assert all(widget.isHidden() for widget in tab.side_fields["h"]["row"]), "and no line under it: nothing written over"
    assert tab.side_fields["h"]["back"].isHidden(), "nothing written over, nothing to take back"
    assert tab.element_label_edit.placeholderText() == "T001 C24 100/200"


def test_a_side_written_over_is_one_undo_step_orange_and_taken_back():
    tab = _tab_75()
    canvas = tab.canvas
    canvas.select(("elements", "E1"))
    steps = len(tab.undo_stack)
    tab.side_fields["h"]["spin"].setValue(240)
    element = canvas.source["elements"][0]
    assert element.get("h") == 240 and len(tab.undo_stack) == steps + 1
    assert not tab.side_fields["h"]["back"].isHidden()
    assert "200" in tab.side_fields["h"]["note"].text(), "the orange line names what the position holds"
    assert not any(widget.isHidden() for widget in tab.side_fields["h"]["row"]) and "b35c00" in tab.side_fields["h"]["note"].styleSheet()
    assert tab.side_fields["h"]["spin"].suffix() == " mm", "a side written over no longer says where from"
    assert [f["lines"] for key, f in canvas.label_frames() if key == ("elements", "E1")] == [["T001 C24 100/240"]]
    assert canvas.drawing_of()["elements"][0]["width"] == 240
    tab.take_back("h")
    assert "h" not in canvas.source["elements"][0]
    tab.undo()
    assert canvas.source["elements"][0].get("h") == 240
    tab.undo()
    assert "h" not in canvas.source["elements"][0]


def test_a_list_cell_writes_a_side_over_and_an_empty_one_follows_again():
    tab = _tab_75()
    table = tab.table_widgets["linear"]
    table.item(0, 4).setText("260")
    assert tab.canvas.source["elements"][0].get("h") == 260
    table = tab.table_widgets["linear"]
    table.item(0, 4).setText("")
    assert "h" not in tab.canvas.source["elements"][0]
    steps = len(tab.undo_stack)
    tab.table_widgets["linear"].item(0, 3).setText("abc")
    assert len(tab.undo_stack) == steps, "a cell that cannot be read leaves no step of «Annuler» behind"


def test_choosing_a_position_retitles_the_piece_and_is_given_to_the_next_one():
    tab = _tab_75()
    tab.canvas.select(("elements", "E2"))
    tab.position_combo.setCurrentIndex(tab.position_combo.findData("T001"))
    assert tab.canvas.source["elements"][1]["position"] == "T001"
    assert tab.canvas.element_position == "T001"
    tab.canvas.add_linear((0, 500), (300, 500))
    assert tab.canvas.source["elements"][-1].get("position") == "T001"
    tab.position_combo.setCurrentIndex(tab.position_combo.findData(""))
    assert "position" not in tab.canvas.source["elements"][-1]


def test_every_list_adds_an_entry_in_one_undo_step():
    tab = _tab_75()
    for which, collection in (("linear", "elements"), ("area", "elements"), ("connectors", "connectors"),
                              ("points", "aids"), ("aids", "aids"), ("dims", "dimensions")):
        before = len(tab.canvas.source[collection])
        steps = len(tab.undo_stack)
        tab.add_row(which)
        assert len(tab.canvas.source[collection]) == before + 1, which
        assert len(tab.undo_stack) == steps + 1, f"«Ajouter» under {which} took {len(tab.undo_stack) - steps} steps"
        assert tab.canvas.selection[0] == collection
    model.check_source(tab.canvas.source, "D99.json")
    for _ in range(6):
        tab.undo()
    assert len(tab.canvas.source["elements"]) == 2 and not tab.canvas.source["connectors"]


def test_the_points_have_a_list_of_their_own_with_a_connector_tick():
    """v0.77, the engineer: the points are not listed under «Aides» but in a «Points» list right of «Connecteurs», each with a «connecteur» tick -- and a point ticked is what «Moments polaires» may take as a fastener."""
    from PySide6.QtCore import Qt
    from domains import connection
    tab = _tab_75()
    names = [spec[0] for spec in tab.TABLE_SPECS]
    assert names.index("points") == names.index("connectors") + 1
    tab.add_row("points")
    pid = tab.canvas.source["aids"][-1]["id"]
    assert tab.canvas.source["aids"][-1]["kind"] == "point"
    assert [row["id"] for row in tab.rows_of("points")] == [pid]
    assert pid not in [row["id"] for row in tab.rows_of("aids")], "a point is still listed under «Aides»"
    table = tab.table_widgets["points"]
    tick = table.item(0, 4)
    assert tick.flags() & Qt.ItemFlag.ItemIsUserCheckable and tick.checkState() == Qt.CheckState.Unchecked
    assert pid not in connection.fastener_places(tab.canvas.source), "an unticked point is offered as a fastener"
    tick.setCheckState(Qt.CheckState.Checked)
    assert tab.canvas.source["aids"][-1]["connector"] is True
    assert pid in connection.fastener_places(tab.canvas.source)
    model.check_source(tab.canvas.source, "D99.json")


def test_a_point_is_named_in_its_list_and_the_name_is_drawn():
    """An aid's `label` was accepted by the check, drawn nowhere and typed nowhere (periodic audit 260916, AUD-7-310): the «Points» list has a «nom» column, and what is typed there is drawn beside the point, in the figure the report prints."""
    from domains import schema_svg
    tab = _tab_75()
    tab.add_row("points")
    table = tab.table_widgets["points"]
    headers = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
    assert len(headers) == 6, headers
    table.item(0, 5).setText("Punkt A")
    point = tab.canvas.source["aids"][-1]
    assert point.get("label") == "Punkt A", point
    model.check_source(tab.canvas.source, "D99.json")
    assert "Punkt A" in schema_svg.render(schema_svg.layout(tab.canvas.source))
    table.item(0, 5).setText("")
    assert "label" not in tab.canvas.source["aids"][-1]


def test_a_tick_sits_in_the_middle_of_its_cell_and_is_clicked_there():
    """v0.77, the engineer: «les cases à cocher doivent être centrées dans les grilles de schémas». Every tick column of the lists draws its box in the middle of the cell (check_cell.CentredCheck) and takes the click there -- a box drawn in the middle that toggled only at the cell's left edge would ignore the pointer; a click at the left edge now does nothing."""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QStyleOptionViewItem
    from check_cell import CentredCheck
    tab = _tab_75()
    tab.window_ref.resize(1600, 1000)
    for (which, column) in tab.CHECK_COLUMNS:
        assert isinstance(tab.table_widgets[which].itemDelegateForColumn(column), CentredCheck), (which, column)
    tab.add_row("points")
    tab.tables.setCurrentIndex([spec[0] for spec in tab.TABLE_SPECS].index("points"))
    table = tab.table_widgets["points"]
    table.show()
    QApplication.processEvents()
    for column, key in ((3, "shown"), (4, "connector")):
        index = table.model().index(0, column)
        cell = table.visualRect(index)
        option = QStyleOptionViewItem()
        option.initFrom(table)
        option.rect = cell
        box = table.itemDelegateForColumn(column).indicator_rect(option, index)
        assert abs(box.center().x() - cell.center().x()) <= 1 and abs(box.center().y() - cell.center().y()) <= 1, (key, box, cell)
        before = bool(tab.canvas.source["aids"][-1].get(key, key == "shown"))
        QTest.mouseClick(table.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(cell.left() + 3, cell.center().y()))
        assert bool(tab.canvas.source["aids"][-1].get(key, key == "shown")) == before, "%s toggled by a click at the cell's left edge" % key
        QTest.mouseClick(table.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, cell.center())
        assert bool(tab.canvas.source["aids"][-1].get(key, key == "shown")) != before, "%s not toggled by a click in the middle of its cell" % key


def test_shown_is_a_check_box_that_decides_the_export():
    from PySide6.QtCore import Qt
    tab = _tab_75()
    item = tab.table_widgets["aids"].item(0, 5)
    assert item.flags() & Qt.ItemFlag.ItemIsUserCheckable and item.checkState() == Qt.CheckState.Unchecked
    item.setCheckState(Qt.CheckState.Checked)
    assert tab.canvas.source["aids"][0]["shown"] is True
    from domains import schema_svg
    assert [a["id"] for a in schema_svg.layout(tab.canvas.source)["aids"]] == ["A1"]


def test_a_hovered_row_lights_its_entry_and_leaving_the_list_puts_it_out():
    from PySide6.QtCore import QEvent
    tab = _tab_75()
    tab.on_row_hover("linear", 1)
    assert tab.canvas.hover == ("elements", "E2") and not tab.canvas.hover_item.path().isEmpty()
    tab.eventFilter(tab.table_widgets["linear"].viewport(), QEvent(QEvent.Type.Leave))
    assert tab.canvas.hover is None and tab.canvas.hover_item.path().isEmpty()
    tab.on_row_hover("linear", 99)
    assert tab.canvas.hover is None


def test_the_crop_is_one_undo_step_refuses_no_area_and_is_taken_off():
    tab = _tab_75()
    canvas = tab.canvas
    said = []
    canvas.refused.connect(said.append)
    assert canvas.set_crop((0, 0, 0.5, 100)) is False and said == ["crop-empty"]
    steps = len(tab.undo_stack)
    assert canvas.set_crop((300, 250, -600, -400))
    assert canvas.source["crop"] == {"x": -300, "z": -150, "w": 600, "h": 400}, "a rectangle dragged backwards is the same crop"
    assert len(tab.undo_stack) == steps + 1
    assert "600" in tab.crop_text.text()
    model.check_source(canvas.source, "D99.json")
    canvas.set_crop(None)
    assert "crop" not in canvas.source


def test_a_rotation_takes_a_typed_angle_after_its_centre():
    tab = _tab_75()
    canvas = tab.canvas
    start = [list(map(list, e["points"])) for e in canvas.source["elements"]]
    canvas.select_many([("elements", "E1"), ("elements", "E2")])
    for _turn in range(4):
        canvas.set_tool("rotate")
        canvas.place((0.0, 0.0))
        assert canvas.rotation_waiting()
        canvas.show_distance()
        assert canvas.typing_angle
        canvas.distance.setText("abc")
        canvas.commit_typed()
        assert canvas.typing, "an angle that cannot be read is not applied"
        canvas.distance.setText("90")
        canvas.commit_typed()
        assert not canvas.typing
    assert [e["points"] for e in canvas.source["elements"]] == start, "four typed quarter-turns are the identity"
    canvas.set_tool("rotate")
    canvas.place((0.0, 0.0))
    canvas.show_distance()
    canvas.hide_distance()
    assert not canvas.typing and not canvas.typing_angle


def test_a_construction_line_is_selected_on_the_drawing():
    tab = _tab_75()
    canvas = tab.canvas
    canvas.set_tool("select")
    canvas.press_select((100.0, 400.0))
    assert canvas.selection == ("aids", "A1"), canvas.selection
    canvas.press_select((-150.0, 0.0))
    canvas.press_select((100.0, 400.0), add=True)
    assert set(canvas.selection_ids()) == {("elements", "E1"), ("aids", "A1")}
    canvas.split_selection()
    assert len(canvas.source["elements"]) == 3, "«Trancher» cuts on a line selected on the drawing"


def test_the_highlighted_call_comes_first():
    """What is selected on the drawing is ticked in «Affichage»'s highlight (v0.117), where the block of calls led with its call."""
    tab = _tab_75()
    tab.set_view("display")
    tab.canvas.select(("elements", "E1"))
    tab.update_calls()
    assert tab.display.command().endswith('highlight: "E1")'), tab.display.command()
    tab.canvas.select(None)
    tab.update_calls()
    assert "highlight" not in tab.display.command(), tab.display.command()
    tab.set_view("draw")


# --- the canvas's paint ---------------------------------------------------------------

def test_the_figure_is_rendered_once_and_not_on_every_paint():
    """The freeze the engineer met: every movement of the mouse repainted the view, and every paint rendered the whole SVG again -- about 300 ms a paint at a device pixel ratio of 2."""
    canvas = _canvas()
    canvas.resize(600, 400)
    canvas.show()
    canvas.set_tool("linear")
    canvas.place((0.0, 0.0))
    canvas.place((300.0, 0.0))
    canvas.fit()
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    layer = canvas.overlay
    real = layer.renderer
    count = []

    class Counting:
        def isValid(self):
            return real.isValid()

        def render(self, painter, rect):
            count.append(1)
            real.render(painter, rect)

    layer.renderer = Counting()
    layer._key = None
    try:
        for _ in range(4):
            canvas.viewport().repaint()
        assert len(count) == 1, count
        canvas.zoom_at(canvas.viewport().rect().center().toPointF(), 1.5)
        canvas.viewport().repaint()
        assert len(count) == 2, "a zoom renders it again"
    finally:
        layer.renderer = real


def test_every_construction_line_is_drawn_across_the_view_shown_or_not():
    canvas = _canvas()
    canvas.resize(600, 400)
    canvas.show()
    canvas.source["aids"] = [{"id": "A1", "kind": "vertical", "x": 0, "z": 0, "angle": 90, "shown": False},
                             {"id": "A2", "kind": "horizontal", "x": 0, "z": 0, "angle": 0, "shown": True}]
    canvas.invalidate()
    from PySide6.QtCore import QRectF
    rect = QRectF(-5000.0, -3000.0, 10000.0, 6000.0)
    drawn = canvas.aid_line_segments(rect)
    assert len(drawn) == 2, "the one the report leaves out is drawn here too"
    lengths = sorted(round(abs(a[0] - b[0]) + abs(a[1] - b[1]), 6) for (a, b), _shown in drawn)
    assert lengths == [6000.0, 10000.0], "each line spans the whole view it is given"
    assert sorted(shown for _ends, shown in drawn) == [False, True]
    # and none of them is in the SVG the canvas renders, which would stop them short
    from domains import schema_svg
    assert "stroke-dasharray" not in schema_svg.render(canvas.drawing_of(), None, background=False, aid_lines=False)


def test_the_canvas_draws_the_points_over_its_lines():
    """The points are green crosses the canvas draws itself, after the construction lines, so no line is ever drawn over one (v0.77); a centre and a line are not among them, and a point outside the view is not drawn."""
    canvas = _canvas()
    canvas.resize(600, 400)
    canvas.show()
    canvas.source["aids"] = [{"id": "A1", "kind": "vertical", "x": 0, "z": 0, "angle": 90, "shown": True},
                             {"id": "A2", "kind": "centre", "x": 10, "z": 10},
                             {"id": "A3", "kind": "point", "x": 20, "z": -30, "shown": True},
                             {"id": "A4", "kind": "point", "x": 90000, "z": 0, "shown": False}]
    canvas.invalidate()
    from PySide6.QtCore import QRectF
    marks = canvas.aid_point_marks(QRectF(-5000.0, -3000.0, 10000.0, 6000.0))
    assert marks == [((20.0, -30.0), True)], marks
    from domains import schema_svg
    rendered = schema_svg.render(canvas.drawing_of(), None, background=False, aid_lines=False, aid_points=False)
    assert schema_svg.POINT_COLOUR not in rendered, "the canvas's SVG would put the point under the lines"


def test_grille_places_valid_markers_whatever_tool_is_in_force():
    """«Grille…» raised `KeyError: 'kind'` with «Sélection» in force -- the tool the tab opens with -- and wrote markers of kind 'point' or 'horizontal' with an aid or a dimension tool, which `check_source` then refuses (periodic audit 260916, AUD-5-2, AUD-4-10). The grid's kind is the fastener tool in force, else a Stabdübel."""
    from domains import schema as model
    tab = _tab_75()
    import schema_tab
    original = schema_tab.GridDialog.exec
    schema_tab.GridDialog.exec = lambda self: 1          # accepted, off-screen: a modal never comes back
    try:
        for tool, kind in (("select", "Stabdübel"), ("linear", "Stabdübel"), ("aid-point", "Stabdübel"),
                           ("dimension-horizontal", "Stabdübel"), ("connector:Nagel", "Nagel")):
            tab.choose_tool(tool)
            tab.place_grid()
            markers = tab.canvas.source.get("connectors", [])
            assert len(markers) == 6, f"{tool}: {len(markers)} markers, the default grid is 3 x 2"
            assert {m["kind"] for m in markers} == {kind}, f"{tool}: {sorted({m['kind'] for m in markers})}"
            model.check_source(tab.canvas.source, "D99.json")
    finally:
        schema_tab.GridDialog.exec = original


def test_the_pointer_readout_names_what_it_snapped_to_in_the_window_s_language():
    """The readout under the drawing showed the snap kinds raw -- `[midpoint]`, `[ray|45|25]` -- in the three languages, where «Modèles statiques» names them (periodic audit 260916, AUD-4-1)."""
    tab = _tab()
    kinds = tuple(model.SNAP_KINDS) + ("ray|45|25", "ray-crossing|45|25", "shift||20")
    try:
        for lang in ("fr", "de", "en"):
            tab.window_ref.lang = lang
            for kind in kinds:
                tab.on_pointer(1, 2, kind)
                text = tab.canvas._readout
                assert "|" not in text, f"{lang}, {kind}: {text!r}"
                import schema_tab
                key = "sc_snap_" + kind.split("|")[0].replace("-", "_")
                assert key in schema_tab.STRINGS[lang], f"no word for the snap kind {kind!r}"
                assert f"[{schema_tab.STRINGS[lang][key]}]" in text, f"{lang}, {kind}: {text!r}"
    finally:
        tab.window_ref.lang = "en"


# --- what a dimension writes, chosen in its list and in its panel -----------------------------------------------


def test_a_dimension_s_show_is_chosen_in_its_list_and_in_its_panel():
    """«Pour les cotations, de manière similaire aux charges, il faut pouvoir choisir entre afficher la valeur, le nom, les deux, ou rien»: a combo of the four in the dimensions' list, the same in the panel, each choice one step of «Annuler», and the name the choice may print typed in either."""
    tab = _tab()
    source = model.new_source("D99")
    source["dimensions"] = [{"id": "D1", "kind": "horizontal", "from": {"x": 0, "z": 0}, "to": {"x": 300, "z": 0}, "offset": -80}]
    tab.open_source(source, None, False)
    tab.fill_tables()
    try:
        columns = {title: index for index, title in enumerate(dict((s[0], s[2]) for s in tab.TABLE_SPECS)["dims"])}
        table = tab.table_widgets["dims"]
        combo = table.cellWidget(0, columns["sc_col_show"])
        assert [combo.itemData(i) for i in range(combo.count())] == list(model.LABEL_MODES)
        assert combo.currentData() == "value", "a dimension saved with no label reads as the value it measured"
        steps = len(tab.undo_stack)
        combo.setCurrentIndex(combo.findData("none"))
        assert tab.source["dimensions"][0]["show"] == "none" and len(tab.undo_stack) == steps + 1
        assert table.item(0, columns["sc_col_value"]).text() == "300 mm", "the list still says what was measured"
        # the panel: the same four, and the name
        tab.canvas.select(("dimensions", "D1"))
        assert all(not caption.isHidden() and not widget.isHidden() for caption, widget in tab.dim_rows)
        assert all(caption.isHidden() for caption, _widget in tab.element_rows), "an element's rows are not a dimension's"
        assert tab.dim_show_combo.currentData() == "none"
        tab.dim_show_combo.setCurrentIndex(tab.dim_show_combo.findData("name+value"))
        tab.dim_name_edit.setText("a")
        tab.dim_name_edit.editingFinished.emit()
        dim = tab.source["dimensions"][0]
        assert dim["show"] == "name+value" and dim["label"] == "a", dim
        assert model.dimension_text(tab.source, dim) == "a = 300 mm"
        assert table.item(0, columns["sc_col_label"]).text() == "a"
    finally:
        tab.dirty = False


# --- the three factors, and one entry's own over them (v0.99) --------------------------------


def test_the_drawing_s_three_sliders_are_in_a_card_of_their_own():
    """A schema had no factors at all before v0.99 and now has the plans' and the static models' three, with the same names and the same range -- a slider means one thing in every tab (figure_style)."""
    from PySide6.QtWidgets import QGroupBox
    tab = _tab_75()
    assert set(tab.style_sliders) == set(model.STYLE_KEYS)
    for key, slider in tab.style_sliders.items():
        assert (slider.minimum(), slider.maximum()) == (25, 300), key
        assert slider.value() == 100, "a new schema opens with its three at rest"
    box = next(b for b in tab.findChildren(QGroupBox) if b.title() == tab.t("sc_group_style"))
    assert box.isVisibleTo(tab)


def test_moving_a_slider_is_one_step_of_annuler_and_redraws():
    """A factor is a change to the schema like any other: one step of «Annuler», the dot of unsaved changes, and the canvas redrawn with it -- the canvas showing the very figure the report will print."""
    tab = _tab_75()
    before = tab.canvas.drawing_of()["font"]
    steps = len(tab.undo_stack)
    tab.style_sliders["text"].setValue(150)
    assert tab.source["style"]["text"] == 1.5
    assert len(tab.undo_stack) == steps + 1, "a factor changed with no drag pushes its own step"
    assert tab.dirty, "the dot of unsaved changes"
    assert tab.canvas.drawing_of()["font"] == 1.5 * before, "the canvas was not redrawn with the factor"
    tab.undo()
    assert float(tab.source.get("style", {}).get("text", 1.0)) == 1.0
    assert tab.canvas.drawing_of()["font"] == before


def test_an_entry_s_own_factor_is_one_undo_step_orange_and_taken_back():
    """Point 3.5: an override is shown the way an overridden b/h is shown -- the row's name and its readout in `theme.colour("override")`, with «Reprendre» beside it -- and setting the slider back to 100 % does not take it off, which is the b/h rule of v0.75."""
    tab = _tab_75()
    import theme   # calc/tools is on sys.path once the tab has been built (_canvas)
    tab.canvas.select(("elements", "E1"))
    row = tab.entry_style.rows["text"]
    assert row["back"].isHidden(), "nothing is written over yet"
    steps = len(tab.undo_stack)
    row["slider"].setValue(200)
    element = tab.canvas.source["elements"][0]
    assert element["style"] == {"text": 2.0}
    assert len(tab.undo_stack) == steps + 1
    assert not row["back"].isHidden(), "no «Reprendre» beside a factor written over"
    assert theme.colour("override").lstrip("#") in row["name"].styleSheet().replace("#", "")
    assert theme.colour("override").lstrip("#") in row["readout"].styleSheet().replace("#", "")
    # back to 100 % states 1 and is still an override -- «Reprendre» is what follows the drawing again
    row["slider"].setValue(100)
    assert tab.canvas.source["elements"][0]["style"] == {"text": 1.0}
    assert not row["back"].isHidden()
    row["back"].click()
    assert "style" not in tab.canvas.source["elements"][0], "the entry carries no empty style either"
    assert row["back"].isHidden() and not row["name"].styleSheet()


def test_only_the_factors_an_entry_is_drawn_with_have_a_row():
    """`figure_style.ENTRY_KEYS`, in the window: a piece has no `point` row at all, a marker no `line` row, and nothing selected has no card."""
    tab = _tab_75()
    tab.canvas.source["connectors"] = [{"id": "C1", "kind": "Stabdübel", "x": 60, "z": 0}]
    tab.canvas.set_source(tab.canvas.source)
    for collection, eid, wanted in (("elements", "E1", ("line", "text")), ("connectors", "C1", ("point", "text")),
                                    ("aids", "A1", ("line", "point", "text"))):
        tab.canvas.select((collection, eid))
        shown = {key for key, row in tab.entry_style.rows.items() if not row["name"].isHidden()}
        assert shown == set(wanted), f"{collection}: {sorted(shown)}"
        assert not tab.entry_style_box.isHidden()
    tab.canvas.select(None)
    assert tab.entry_style_box.isHidden(), "a card of factors for nothing selected"


def test_the_canvas_cuts_its_construction_lines_at_the_labels_as_the_figure_does():
    """Point 4.3, in the window: the canvas draws the lines itself, across the whole view, so a cut made only in the exported figure would show the engineer one detail and the checker another -- which is the very thing this canvas exists to prevent (schema_canvas's own docstring)."""
    from PySide6.QtCore import QRectF
    from domains import schema_svg
    tab = _tab_75()
    frame = next(f for key, f in tab.canvas.label_frames() if key == ("elements", "E1"))
    label_z = frame["at"][1]
    tab.canvas.source["aids"] = [{"id": "A9", "kind": "horizontal", "x": 0, "z": label_z, "angle": 0, "shown": True}]
    tab.canvas.set_source(tab.canvas.source)
    rect = QRectF(-2000.0, -2000.0, 4000.0, 4000.0)
    pieces = tab.canvas.aid_line_segments(rect)
    assert len(pieces) >= 2, "one line across a label came back whole"
    assert all(shown for _ends, shown in pieces)
    # every piece stops clear of the box, and none of them is inside it
    for (a, b), _shown in pieces:
        middle = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        assert not schema_svg.on_label(frame, middle), "a piece was left inside the label's box"
    # a line that crosses no label is still one piece running the whole width of the view
    tab.canvas.source["aids"] = [{"id": "A9", "kind": "horizontal", "x": 0, "z": label_z + 40 * frame["hh"],
                                  "angle": 0, "shown": True}]
    tab.canvas.set_source(tab.canvas.source)
    whole = tab.canvas.aid_line_segments(rect)
    assert len(whole) == 1 and abs(whole[0][0][0][0] - (-2000.0)) < 1e-6


def test_surfacique_shows_its_options_when_it_is_chosen_and_a_position_fixes_one_side_of_what_is_drawn():
    """v0.117, the engineer: «lorsque je sélectionne l'outil "Surfacique", dans le volet de droite, je dois déjà voir les options pour cet outil. Je dois pouvoir indiquer la position, et, lorsque cela est fait, je dois pouvoir choisir si je dessine la largeur ou la hauteur de la position. Ensuite, je dessine l'élément qui possède donc une largeur fixe»."""
    tab = _tab_75()
    tab.positions["P001"] = {"type": "Platte", "section": {"type": "pla", "kind": "timber", "text": "22 mm", "t": 22}}
    tab.positions["S2"] = {"type": "Stütze", "section": {"type": "IPE", "kind": "steel", "text": "IPE 200", "dims": [200]}}
    tab.canvas.set_positions(tab.positions)
    tab.fill_positions()
    assert tab.tool_box.isHidden(), "no options for the tool «Sélection»"
    tab.choose_tool("area")
    assert not tab.tool_box.isHidden(), "the options are in the right pane as soon as the tool is chosen, before anything is drawn"
    assert tab.canvas.area_fixed is None and tab.tool_fixed_note.text() == tab.t("sc_fixed_free")
    assert tab.tool_draw_combo.isHidden() and tab.tool_draw_caption.isHidden(), "which dimension is drawn is asked once there is a position"
    # the drawing mode: the tool bar's, one value behind the two controls
    tab.tool_mode_combo.setCurrentIndex(tab.tool_mode_combo.findData("edge"))
    assert tab.area_combo.currentData() == "edge" and tab.canvas.area_mode == "edge"
    tab.area_combo.setCurrentIndex(tab.area_combo.findData("diagonal"))
    assert tab.tool_mode_combo.currentData() == "diagonal" and tab.canvas.area_mode == "diagonal"
    # the position offers the list the selection's combo does, and chooses the one the next element is of
    assert [tab.tool_position_combo.itemData(i) for i in range(tab.tool_position_combo.count())] == [tab.position_combo.itemData(i) for i in range(tab.position_combo.count())]
    tab.tool_position_combo.setCurrentIndex(tab.tool_position_combo.findData("T001"))
    assert tab.canvas.element_position == "T001" and tab.canvas.area_fixed == ("b", 200.0)
    assert not tab.tool_draw_combo.isHidden() and "200" in tab.tool_fixed_note.text() and "100" not in tab.tool_fixed_note.text()
    # drawn by two clicks: the width is the drag's, the height the position's, and the element is the position's
    before = len(tab.canvas.source["elements"])
    tab.canvas.place((0.0, 0.0))
    tab.canvas.place((300.0, 10.0))
    element = tab.canvas.source["elements"][-1]
    assert len(tab.canvas.source["elements"]) == before + 1
    assert element["kind"] == "area" and element["position"] == "T001" and element["points"] == [[0, 0], [300, 0], [300, 200], [0, 200]], element
    # the height drawn instead: the width is the position's
    tab.tool_draw_combo.setCurrentIndex(tab.tool_draw_combo.findData("h"))
    assert tab.canvas.area_fixed == ("h", 100.0) and "100" in tab.tool_fixed_note.text()
    tab.canvas.place((0.0, 500.0))
    tab.canvas.place((40.0, 800.0))
    assert tab.canvas.source["elements"][-1]["points"] == [[0, 500], [100, 500], [100, 800], [0, 800]]
    # by an edge, the third click says on which side: the width is the position's whatever its distance
    tab.tool_mode_combo.setCurrentIndex(tab.tool_mode_combo.findData("edge"))
    tab.tool_draw_combo.setCurrentIndex(tab.tool_draw_combo.findData("b"))
    for point in ((0.0, 1000.0), (300.0, 1000.0), (100.0, 940.0)):
        tab.canvas.place(point)
    assert tab.canvas.source["elements"][-1]["points"] == [[0, 1000], [300, 1000], [300, 800], [0, 800]], "the height 200 on the side of the third click"
    model.check_source(tab.canvas.source, "D99.json")
    # and what the export writes (data/schemas.json's record of the schema): the element, its position, its polygon in mm
    drawn = [e for e in tab.canvas.source["elements"] if e.get("kind") == "area" and e.get("position") == "T001"]
    record = model.build_record(tab.canvas.source, tab.positions)
    exported = [e for e in record["elements"] if e["id"] in {d["id"] for d in drawn}]
    assert len(exported) == len(drawn) == 3 and all(e["position"] == "T001" for e in exported), exported
    assert sorted(max(p[1] for p in e["at"]) - min(p[1] for p in e["at"]) for e in exported) == [200, 200, 300], "the fixed side, 200 or 100 mm, is the exported polygon's own"
    # a plate fixes its thickness and asks no question; a steel profile fixes nothing; no position gives the free drawing back
    tab.tool_mode_combo.setCurrentIndex(tab.tool_mode_combo.findData("diagonal"))
    tab.tool_position_combo.setCurrentIndex(tab.tool_position_combo.findData("P001"))
    assert tab.canvas.area_fixed == ("", 22.0) and tab.tool_draw_combo.isHidden() and "22" in tab.tool_fixed_note.text()
    tab.canvas.place((0.0, 1500.0))
    tab.canvas.place((400.0, 1530.0))
    assert tab.canvas.source["elements"][-1]["points"] == [[0, 1500], [400, 1500], [400, 1522], [0, 1522]]
    tab.tool_position_combo.setCurrentIndex(tab.tool_position_combo.findData("S2"))
    assert tab.canvas.area_fixed is None and tab.tool_fixed_note.text() == tab.t("sc_fixed_none")
    tab.tool_position_combo.setCurrentIndex(tab.tool_position_combo.findData(""))
    assert tab.canvas.area_fixed is None and tab.canvas.element_position == "" and tab.tool_fixed_note.text() == tab.t("sc_fixed_free")
    tab.canvas.place((0.0, 2000.0))
    tab.canvas.place((100.0, 2050.0))
    assert tab.canvas.source["elements"][-1]["points"] == [[0, 2000], [100, 2000], [100, 2050], [0, 2050]] and "position" not in tab.canvas.source["elements"][-1]
    # the selection's own combo and the options agree on the position, and leaving the tool hides the card
    tab.canvas.select(("elements", "E2"))
    tab.position_combo.setCurrentIndex(tab.position_combo.findData("T001"))   # E2 is S001's: this one changes it
    assert tab.tool_position_combo.currentData() == "T001" and tab.canvas.area_fixed == ("b", 200.0)
    tab.choose_tool("select")
    assert tab.tool_box.isHidden()
    for lang in ("fr", "de", "en"):
        for key in ("sc_tool_options", "sc_tool_draw", "sc_tool_draw_b", "sc_tool_draw_h", "sc_fixed_h", "sc_fixed_b", "sc_fixed_t", "sc_fixed_d", "sc_fixed_none", "sc_fixed_free"):
            assert tab.__class__.__module__ and key in __import__("schema_tab").STRINGS[lang], (lang, key)


def test_the_list_takes_the_order_dropped_and_keeps_it_through_a_rename_without_touching_a_file():
    """Issue #15, REQ-008: the order the engineer gives the list by drag and drop is kept in Woodcore-Datei/lists.json -- the same kernel as every list (calc/list_order.py) --, no schema's file is written for it, and a schema saved under a new id keeps its place."""
    import json
    import shutil
    import project
    import list_order
    tab = _tab()
    here = project.current()
    folder = here.details_dir
    first = sorted(p.stem for p in folder.glob("*.json"))[0]
    shutil.copy2(folder / f"{first}.json", folder / "ZZ-Ordre.json")
    data = json.loads((folder / "ZZ-Ordre.json").read_text(encoding="utf-8"))
    data["id"] = "ZZ-Ordre"
    (folder / "ZZ-Ordre.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        tab.reload_list()
        assert tab.list.ids().index(first) < tab.list.ids().index("ZZ-Ordre")
        stamps = {p.name: p.stat().st_mtime_ns for p in folder.glob("*.json")}
        group = next(e.get("group") or "" for e in tab.list._entries if e["id"] == first)
        tab.list.drop_ids(["ZZ-Ordre"], tab.list._item_for(first), group, below=False)
        assert tab.list.ids().index("ZZ-Ordre") < tab.list.ids().index(first), tab.list.ids()
        assert {p.name: p.stat().st_mtime_ns for p in folder.glob("*.json")} == stamps, "an order alone wrote a schema's file"
        order, _groups = list_order.tab_of(list_order.read(here), "tab_schema")
        assert order.index("ZZ-Ordre") < order.index(first)
        tab.app.list_store.rename("tab_schema", "ZZ-Ordre", "ZZ-Neu")
        assert list_order.tab_of(list_order.read(here), "tab_schema")[0][0] == "ZZ-Neu"
    finally:
        (folder / "ZZ-Ordre.json").unlink(missing_ok=True)
        tab.app.list_store.forget("tab_schema", ["ZZ-Ordre", "ZZ-Neu"])
        tab.reload_list()
