"""The plan tabs' requests of 07.10.2026 (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-012 to REQ-020): snapping in the right pane, the position's words in the window's language, and what follows.

The engineer, 07.10.2026: «pouvoir activer et désactiver le magnétisme dans le volet de droite lorsque rien n'est sélectionné» · «la "Position" possède encore les noms en allemand (e.g. T001 - Träger, Fichte». The window is built once, off-screen, on a copy of the example project (conftest.project_copy); every dialog is stubbed -- a modal off-screen never comes back.
"""

TIER = "fast"  # tests/run_tests.py --fast

import contextlib
import os
import sys

import conftest
from conftest import ROOT, Skip

import project

_STATE = {}


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdf  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdf is not installed ({exc})")
    return QApplication.instance() or QApplication([])


@contextlib.contextmanager
def _dialogs():
    """Nothing modal can block the run: a question says yes."""
    from PySide6.QtWidgets import QFileDialog, QMessageBox
    stubs = {
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "critical"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "information"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),
    }
    originals = {key: key[0].__dict__[key[1]] for key in stubs}
    for (owner, attr), stub in stubs.items():
        setattr(owner, attr, stub)
    try:
        yield
    finally:
        for (owner, attr), original in originals.items():
            setattr(owner, attr, original)


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("plan_tabs_v0117")
        with project.using(here), _dialogs():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(kind):
    window, here = _window()
    tab = next(t for t in window.tabs if type(t).__name__ == kind)
    tab.dirty = False
    return tab, here


def _plan_source():
    """A position plan of one beam T001 and one column S001, shown unsaved."""
    from domains import plan as model
    source = model.new_source("P99", floor="0")
    source["elements"] = [{"type": "T", "label": "T001", "points": [[0.0, 0.0], [100.0, 0.0]]},
                          {"type": "S", "label": "S001", "points": [[50.0, 50.0]]}]
    return source


def _open_plan(tab, source):
    tab.open_source(source, None, False)
    tab.show_plan_view()
    tab.canvas.select(None)
    tab.dirty = False


# --- REQ-012: snapping in the right pane -----------------------------------------------------------

def test_snapping_is_a_module_of_the_right_pane_with_nothing_selected_in_both_plan_tabs():
    from PySide6.QtWidgets import QToolButton
    for kind in ("PlanTab", "FireTab"):
        tab, here = _tab(kind)
        with project.using(here), _dialogs():
            _open_plan(tab, _plan_source())
            titles = [card.title() for card in tab.visible_modules()]
            assert tab.t("plan_group_snap") in titles, (kind, titles)
            assert tab.snap_group.isAncestorOf(tab.snap_axes) and tab.snap_group.isAncestorOf(tab.snap_elements), kind
            on_bar = [b.text() for row in getattr(tab, "tool_rows", []) for b in row.findChildren(QToolButton)]
            assert tab.t("plan_snap_axes") not in on_bar, (kind, "still on the tool bar")
            if kind == "PlanTab":   # the fire plan's own elements are of other kinds: the same rule (update_modules) holds there
                tab.canvas.select(("element", 0))
                assert tab.snap_group.isHidden(), (kind, "shown while something is selected")
                tab.canvas.select(None)
            tab.snap_axes.setChecked(False)
            tab.snap_elements.setChecked(False)
            assert not tab.canvas.snap_axes and not tab.canvas.snap_elements, kind
            tab.snap_axes.setChecked(True)
            tab.snap_elements.setChecked(True)
            assert tab.canvas.snap_axes and tab.canvas.snap_elements, kind


# --- REQ-014: the position's type in the window's language -------------------------------------------

def test_the_position_list_of_a_selected_element_names_its_type_in_the_window_s_language():
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QComboBox
    tab, here = _tab("PlanTab")
    window = tab.app
    language = window.lang
    expected = {"fr": "Poutre", "de": "Träger", "en": "Beam"}
    try:
        with project.using(here), _dialogs():
            _open_plan(tab, _plan_source())
            for lang, word in expected.items():
                window.lang = lang
                tab.canvas.select(None)
                tab.canvas.select(("element", 0))
                QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)   # the card of the previous selection really gone
                combos = [c for c in tab.selection_group.findChildren(QComboBox) if c.findData("T001") >= 0]
                assert combos, lang
                text = combos[0].itemText(combos[0].findData("T001"))
                assert text.startswith(f"T001 — {word}"), (lang, text)
                assert "Fichte" in text, "the material is the engineer's word, kept as written"
    finally:
        window.lang = language
        tab.canvas.select(None)


# --- REQ-015: the symbols' layer is drawn once per zoom, not at every frame ---------------------------

def test_the_symbols_layer_has_room_in_the_pixmap_cache_for_a_full_screen_view():
    """Qt's QPixmapCache is 10 MB by default, less than one cached picture of a full-screen view (19 MB at 1920 x 1080 and 150 %): the SVG of the symbols was drawn again at every frame of a pan or a zoom. A layer made raises it (plan_canvas.ensure_pixmap_cache, v0.117)."""
    _qt()
    import plan_canvas
    from PySide6.QtGui import QPixmapCache
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtCore import QByteArray, QRectF
    plan_canvas.SvgLayer(QSvgRenderer(QByteArray(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>')), QRectF(0, 0, 10, 10))
    assert QPixmapCache.cacheLimit() >= 1920 * 1080 * 2.25 * 4 / 1024 * 2, QPixmapCache.cacheLimit()


# --- REQ-013, REQ-020: a column turned, an element's own length, in the right pane --------------------

def test_a_column_selected_is_turned_by_its_field_by_a_quarter_and_by_r():
    from PySide6.QtWidgets import QDoubleSpinBox, QPushButton
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        _open_plan(tab, _plan_source())
        tab.canvas.select(("element", 1))   # S001
        tab.set_angle(30)
        assert tab.source["elements"][1]["angle"] == 30
        tab.turn_quarter()
        assert tab.source["elements"][1]["angle"] == 120
        tab.set_angle(-240)
        assert tab.source["elements"][1]["angle"] == 120, "an angle is kept between -180 and 180"
        tab.set_angle(0)
        assert "angle" not in tab.source["elements"][1], "a column not turned carries no angle"
        tab.refresh_selection()
        fields = [w for w in tab.selection_group.findChildren(QDoubleSpinBox) if w.suffix() == "°"]
        buttons = [b for b in tab.selection_group.findChildren(QPushButton) if b.text() == tab.t("plan_turn_90")]
        assert fields and buttons, "the column's rotation and its quarter turn are in the right pane"
        tab.canvas.select(("element", 0))   # T001: a beam is not turned
        tab.turn_quarter()
        assert "angle" not in tab.source["elements"][0]


def test_an_element_s_own_length_follows_the_plan_or_says_otherwise():
    from PySide6.QtWidgets import QComboBox
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        source = _plan_source()
        source["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1.0}
        _open_plan(tab, source)
        tab.canvas.select(("element", 0))   # T001
        combos = [c for c in tab.selection_group.findChildren(QComboBox) if c.findData(True) >= 0 and c.findData(False) >= 0]
        assert combos and combos[-1].isEnabled(), "a beam's length shown, hidden, or as the plan"
        tab.set_show_length(True)
        assert tab.source["elements"][0]["show_length"] is True
        tab.set_show_length(None)
        assert "show_length" not in tab.source["elements"][0]


# --- REQ-019: «Coupe…» opens the section to draw the storey on ------------------------------------------

def test_coupe_opens_the_section_with_the_plan_s_storey_and_the_storey_line_armed():
    """The engineer, 07.10.2026: «lorsque je clique sur "Coupe..." … ce qu'il doit se passer à mon avis: ouvre le plan sélectionné dans le menu déroulant et permet de dessiner la ligne d'étage ou le rectangle d'étage directement avec le bon étage écrit». Until v0.117 the link was written and nothing else happened."""
    import json
    from domains import plan as model
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        floor = model.new_source("F99", floor="1")
        floor["storey"] = "1er étage"
        section = model.new_source("C99", floor="0")
        section["role"], section["plan_type"] = "section", "section"
        for source in (floor, section):
            (here.plans_dir / f"{source['id']}.json").write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tab.reload_list()
        tab.load("F99")
        assert tab.current_id == "F99"
        tab.ask_choice = lambda _title, _text, choices, _index: next(i for i, c in enumerate(choices) if "C99" in c)
        tab.choose_section()
        assert json.loads((here.plans_dir / "F99.json").read_text(encoding="utf-8")).get("section_plan") == "C99", "the link is written, the plan left saved"
        assert tab.current_id == "C99", "the section is open"
        assert tab.canvas.tool == "storey-line" and tab.storey_choice.currentText() == "1er étage"
        assert tab.section_back.isVisibleTo(tab) and "F99" in tab.section_back.text()
        # the line drawn already: the box is the next tool
        tab.source.setdefault("storey_lines", []).append({"storey": "1er étage", "points": [[0, 100], [400, 100]]})
        tab.save()
        tab.back_to_section_origin()
        assert tab.current_id == "F99"
        tab.choose_section()
        assert tab.current_id == "C99" and tab.canvas.tool == "storey-box"


def test_the_window_s_export_waits_for_a_layer_export_running_in_its_thread():
    """ARCH-003 (v0.117): one writer of data/ at a time -- the export a layer switched started in its thread is finished before the window starts its own."""
    window, here = _window()
    finished = []
    for tab in window.tabs:
        if hasattr(tab, "finish_layer_export"):
            original = tab.finish_layer_export
            tab.finish_layer_export = lambda original=original, tab=tab: finished.append(type(tab).__name__) or original()
    started = []
    import woodcore_gui
    saved = woodcore_gui.proc.qprocess
    woodcore_gui.proc.qprocess = lambda parent: (_ for _ in ()).throw(RuntimeError("stop here"))   # the export itself is not run
    try:
        with project.using(here), _dialogs():
            try:
                window.reexport()
            except RuntimeError:
                started.append(True)
    finally:
        woodcore_gui.proc.qprocess = saved
        import busy
        busy.stop_all()
        for tab in window.tabs:
            if "finish_layer_export" in tab.__dict__:
                del tab.finish_layer_export
    assert started, "the export was not reached"
    assert {"PlanTab", "FireTab"} <= set(finished), finished
