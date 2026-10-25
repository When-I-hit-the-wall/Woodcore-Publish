"""The calculation tabs' common base, mounted on a domain invented for it (spec 2026-10-22-onglet-neige-type, ARCH-002, ARCH-003, ARCH-005, UI-001 to UI-008, UI-010, REQ-001 to REQ-003, REQ-010; calc/tools/calc_tab.py, calc_fields.py, module_pane.py, norm_bubble.py, norm_reader.py).

What is held:

* **the base knows no domain**: its modules hold no word of the snow, and it draws tests/fake_domain.py -- a beam, a field of each kind -- as it draws the snow: its sections, its fields each with its ⓘ, its free value, its tiles, its rows shown for its source;
* **the right pane is made of modules**: the state first in red, orange, green, a message's click giving its field the focus and a flash; the results, never an input; the drawing and the chart, which reads its value under the pointer; no arrow to move one, a move and a fold kept for the tab on this machine and an unknown id ignored; an excerpt pinned under «Résultats» once, closed by ×, the fixed modules never closable; ⧉ opening a window of the module that zooms by itself;
* **the bubble's place** never covers its ⓘ, above where there is no room under, scrolling where neither holds it; its words before its image, the German edition for the English window;
* **the reader's frame** is where QPdfView draws the page, and an edition not shipped says so without an error.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import re
import sys

import conftest
import project
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
_STATE = {}
# The type «Calcul» and its services (spec 2026-10-23-onglets-types-et-services): none of them holds a word of a domain
BASE = ("calc_tab.py", "tab_host.py", "case_list.py", "case_list_logic.py", "draft_logic.py", "source_store.py", "field_links.py", "calc_form.py", "calc_modules.py",
        "calc_bubbles.py", "calc_display.py", "calc_fields.py", "module_pane.py", "norm_bubble.py", "norm_reader.py", "excerpt_image.py", "calc_tab_words.py",
        "calc_blocks.py")


def _qt():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


class _Store:
    """layout_store's settings, kept in memory: a test never writes the engineer's own."""

    def __init__(self):
        self.settings = {}

    def read(self):
        return dict(self.settings)

    def write(self, settings):
        self.settings = dict(settings)


def _tab():
    if "tab" not in _STATE:
        _qt()
        import fake_domain
        import calc_tab
        import layout_store
        import load_words
        import woodcore_gui
        import woodcore_gui_words
        for lang, words in fake_domain.WORDS.items():
            woodcore_gui_words.STRINGS[lang].update(words)
        here = conftest.project_copy("calc_tab_base")
        store = _Store()
        with project.using(here):
            window = woodcore_gui.MainWindow()

            # REQ-004 of the spec 2026-10-23-onglets-types-et-services: a tab of calculation is a class of parameters on its type -- no widget, no method
            class FakeTab(calc_tab.CalcTab):
                KEY = "tab_fake"
                MODULE = fake_domain
                ID_PREFIX = "BM-"
                LIST_KEY = "fk_list"
                EMPTY_KEY = "fk_empty"
            FakeTab.__module__ = "fake_domain"            # the list reads its words off the tab's module
            fake_domain.STRINGS = load_words.STRINGS
            original = layout_store.Store
            layout_store.Store = lambda *a, **k: original(read=store.read, write=store.write)
            try:
                tab = FakeTab(window)
            finally:
                layout_store.Store = original
            kept = original(read=store.read, write=store.write)
            tab.ctx.layout = kept                         # the form's sections and the modules' order, kept in memory
            tab.service("modules").pane.store = kept
        _STATE.update(tab=tab, here=here, store=store)
    return _STATE["tab"]


def _form():
    return _tab().service("form")


def _modules():
    return _tab().service("modules")


def _code(path):
    """The code of a module, its comments and docstrings taken away: what it does, not what it says it is the base of."""
    import ast
    import io
    import tokenize
    source = path.read_text(encoding="utf-8")
    docstrings = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)) and node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant) and isinstance(node.body[0].value.value, str):
            docstrings.add(node.body[0].lineno)
    kept = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT or (token.type == tokenize.STRING and token.start[0] in docstrings):
            continue
        kept.append(token.string)
    return " ".join(kept)


def test_the_base_holds_no_word_of_a_domain():
    """ARCH-002: no word, no key and no rule of a domain in the base's code -- its docstrings may name the snow as its first tab."""
    for name in BASE:
        text = _code(TOOLS / name).lower()
        found = [w for w in ("snow", "schnee", "neige", "roof", "toit", "sia261", "261.sia", "sn_") if re.search(r"\b" + re.escape(w), text)]
        assert not found, (name, found)


def test_an_invented_domain_is_drawn_with_a_field_of_each_kind_and_its_info():
    tab = _tab()
    import calc_fields
    assert set(_form().fields) == {"span", "kind", "shape", "braced", "grade", "width", "depth", "height", "side"}, "the third section's fields too (spec 2026-10-23-onglet-vent-briques)"
    assert all(isinstance(f, calc_fields.FieldWidget) for f in _form().fields.values())
    assert [f.field.kind for f in _form().fields.values()][:5] == ["number", "buttons", "tiles", "checkbox", "select"]
    assert all(f.info.isVisibleTo(f.label) or not f.field.excerpts for f in _form().fields.values()) and _form().fields["span"].info.text() == "ⓘ"
    assert [b.text() for b in _form().fields["kind"].buttons.values()] == ["light 0.5", "heavy 2"]
    assert [b.text() for b in _form().fields["shape"].buttons.values()] == ["box", "slab"] and not _form().fields["shape"].buttons["box"].icon().isNull()
    # a row the source does not show
    form, widget = _form().rows["grade"]
    assert not form.isRowVisible(widget)
    _form().fields["braced"].check.setChecked(True)
    _form().field_changed("braced")
    assert form.isRowVisible(widget)
    # a free value is the source's, and the buttons' choice again
    _form().fields["kind"].free.setValue(3.0)
    assert tab.draft()["kind"] == "custom" and tab.draft()["factor"] == 3.0
    _form().fields["kind"].buttons["light"].click()
    assert tab.draft()["kind"] == "light" and "factor" not in tab.draft()


def test_the_state_says_red_orange_green_and_takes_to_the_field():
    tab = _tab()
    state = _modules().pane.modules["state"].body
    _form().fields["span"].spin.setValue(5)
    assert tab.instance and [r.text() for r in state.rows] == ["✓ " + tab.t("ct_complete")]
    assert _modules().pane.modules["state"].summary.text() == tab.t("ct_summary_complete")
    _form().fields["span"].spin.setValue(12)
    assert [r.property("callout") for r in state.rows] == ["info", "warning"] and state.rows[1].text() == "A long span: 12 m"
    _form().fields["span"].spin.setValue(0)
    assert tab.instance is None and [r.property("callout") for r in state.rows] == ["danger"]
    state.rows[0].mousePressEvent(None)
    assert _form().fields["span"].blinking
    _form().fields["span"].spin.setValue(4)


def test_the_results_are_what_is_computed_and_the_chart_reads_under_the_pointer():
    tab = _tab()
    _form().fields["span"].spin.setValue(4)
    html = _modules().pane.modules["results"].body.text()
    assert "M<sub>d</sub>" in html and "<sub>" in html and ">l<" not in html, "the span is an input, never a result"
    chart = _modules().pane.modules["chart"].body
    assert chart.data["marks"][0]["x"] == 4 and abs(chart.probe(5.0)[0][1] - 0.5 * 12.5 / 2) < 1e-9
    assert "<svg" in tab.ctx.drawing


def test_the_modules_move_fold_and_are_kept_per_tab_and_an_excerpt_is_pinned_once():
    tab = _tab()
    from PySide6.QtWidgets import QToolButton
    pane = _modules().pane
    assert pane.ids()[:4] == ["state", "results", "drawing", "chart"]
    arrows = [b for b in pane.findChildren(QToolButton) if b.text() in ("↑", "↓", "▲", "▼")]
    assert not arrows, "no arrow moves a module (D-6)"
    assert all(pane.modules[i].close_button is None for i in ("state", "results", "drawing", "chart"))
    pane.move("chart", 0)
    pane.modules["results"].set_folded(True)
    kept = _STATE["store"].settings["modules"]["tab_fake"]
    assert kept["order"][0] == "chart" and kept["folded"] == ["results"]
    module = _modules().pin("sia261-2020-5.2-schnee", ("5.3.4",))
    again = _modules().pin("sia261-2020-5.2-schnee", ("5.3.4",))
    assert module is again and pane.ids().count(module.spec.id) == 1
    assert pane.ids().index(module.spec.id) == pane.ids().index("results") + 1, "under «Résultats»"
    second = _modules().pin("sia261-2020-5.2-schnee", ("fig3",))
    assert pane.ids().index(second.spec.id) == pane.ids().index(module.spec.id) + 1, "after the pins before it"
    assert module.spec.id not in _STATE["store"].settings["modules"]["tab_fake"]["order"], "a pin is the session's (D-27)"
    window = pane.open_window(module.spec.id)
    assert window.ZOOMS_ITSELF and module.spec.id in pane.modules
    window.zoom_by(2.0)
    assert abs(window.transform().m11() - 2.0) < 1e-9
    window.close()
    module.close_button.click()
    assert module.spec.id not in pane.modules
    # a state kept with an id no module has is read without it
    import layout_store
    import module_pane
    store = layout_store.Store(read=lambda: {"modules": {"tab_x": {"order": ["gone", "b", "a"], "folded": ["gone"]}}}, write=lambda s: None)
    other = module_pane.ModulePane(tab.t, "tab_x", store)
    for mid in ("a", "b"):
        other.add(module_pane.ModuleSpec(mid, mid, lambda: __import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel("x")))
    assert other.ids() == ["b", "a"]
    pane.move("state", 0)
    pane.modules["results"].set_folded(False)


def test_the_bubble_shows_the_words_then_the_image_and_german_for_english():
    tab = _tab()
    import norm_bubble
    from PySide6.QtWidgets import QLabel
    items = tab.ctx.bubbles.excerpts("sia261-2020-5.2-schnee", ("5.3.4",))
    view = norm_bubble.ExcerptView(items, tab.t)
    labels = [w for w in view.findChildren(QLabel)]
    assert labels[0].text().startswith("SIA 261:2020 · 5.3.4") and labels[1].text()[:30] == items[0].text[:30], "the words first (D-4)"
    assert isinstance(labels[2], norm_bubble.FitImage) or labels[2].text() == tab.t("ct_no_pdf", file=items[0].file), "then the image"
    from norms import excerpts
    assert excerpts.excerpt("sia261-2020-5.2-schnee", "5.3.4", "en").lang == "de"
    bare = norm_bubble.ExcerptView(items, tab.t, bare=True)
    assert not [w for w in bare.findChildren(QLabel) if w.text().startswith("SIA")], "a tile's bubble shows the excerpt alone (T28)"


def test_a_click_on_an_info_pins_and_a_second_takes_out_as_its_cross_does():
    """Issue #96 (REQ-003, UI-002 of the spec 2026-10-23-neige-correctifs-issues-96-99): the click on a ⓘ is a toggle -- pinned under «Résultats», taken out, pinned again --; × and the second click leave the same state; the ⓘ of an excerpt pinned is filled and hollow again when it goes; the bubble's foot says what the click will do."""
    tab = _tab()
    from PySide6.QtCore import Qt
    import calc_tab
    field = next(f for f in _form().fields.values() if f.field.excerpts)
    norm, ids = tab.ctx.declaration().norm, tuple(field.field.excerpts)
    mid = calc_tab.excerpt_module_id(norm, ids)
    assert calc_tab.excerpt_of_module(mid) == (norm, ids)
    target = tab.ctx.bubbles.targets[id(field.info)]
    none = Qt.KeyboardModifier.NoModifier
    assert not field.info.pinned and tab.ctx.bubbles.foot(norm, ids).startswith(tab.t("ct_click_pin"))
    tab.ctx.bubbles._act(target, none)
    assert mid in _modules().pane.modules and field.info.pinned, "pinned, its ⓘ filled"
    assert _modules().pane.ids().index(mid) == _modules().pane.ids().index("results") + 1
    assert tab.ctx.bubbles.foot(norm, ids).startswith(tab.t("ct_click_unpin"))
    tab.ctx.bubbles._act(target, none)
    assert mid not in _modules().pane.modules and not field.info.pinned, "a second click takes it out"
    tab.ctx.bubbles._act(target, none)
    assert mid in _modules().pane.modules and field.info.pinned, "and pins it again"
    _modules().pane.modules[mid].close_button.click()
    assert mid not in _modules().pane.modules and not field.info.pinned, "× leaves the same state as the second click"
    # a tile's click is still its choice: the bubble's filter lets a checkable widget's press through
    from PySide6.QtCore import QEvent, QPointF
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QPushButton
    tile = QPushButton()
    tile.setCheckable(True)
    tab.ctx.bubbles.attach(tile, norm, ("fig3",))
    press = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(2, 2), QPointF(2, 2), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, none)
    assert tab.ctx.bubbles.eventFilter(tile, press) is False, "the press reaches the tile"
    _modules().pane.remove(calc_tab.excerpt_module_id(norm, ("fig3",)))
    for lang in ("fr", "de", "en"):
        for key in ("ct_click_pin", "ct_click_unpin", "ct_ctrl_click"):
            assert __import__("woodcore_gui_words").STRINGS[lang].get(key), (lang, key)


def test_a_result_hovered_lights_its_data_and_a_datum_its_results():
    """UI-004, ARCH-001 of the spec 2026-10-23-neige-correctifs-issues-96-99, on the invented domain: «Résultats» is a row a result; M_d hovered lights the span and the kind it is computed from (its steps, the fields' `var`), and the row of q between them; the span hovered lights itself and M_d; the pointer gone, nothing is lit -- the theme's `hover` ground, its labels' subscripts as rich text."""
    tab = _tab()
    import theme
    from PySide6.QtCore import QEvent, QPointF
    from PySide6.QtGui import QEnterEvent
    from PySide6.QtWidgets import QApplication

    def enter():
        return QEnterEvent(QPointF(2, 2), QPointF(2, 2), QPointF(2, 2))
    _form().fields["span"].spin.setValue(4)
    body = _modules().pane.modules["results"].body
    assert set(body.rows) == {"q", "M_d"}
    fields, names = tab.ctx.hover_result("M_d")
    assert fields == {"span", "kind"} and names >= {"M_d", "q"}
    assert _form().fields["span"].lit and _form().fields["kind"].lit and not _form().fields["shape"].lit
    assert theme.colour("hover") in body.rows["M_d"][0].styleSheet() and theme.colour("hover") in body.rows["q"][0].styleSheet()
    tab.ctx.hover_result(None)
    assert not any(f.lit for f in _form().fields.values()) and not body.rows["M_d"][0].styleSheet()
    fields, names = tab.ctx.hover_field("span")
    assert fields == {"span"} and names == {"span", "M_d"} and theme.colour("hover") not in body.rows["q"][0].styleSheet()
    tab.ctx.hover_field(None)
    # the pointer itself: entering a row's label and a field's label
    QApplication.sendEvent(body.rows["M_d"][2], enter())
    assert _form().fields["span"].lit
    QApplication.sendEvent(body.rows["M_d"][2], QEvent(QEvent.Type.Leave))
    QApplication.sendEvent(_form().fields["kind"].label, enter())
    assert body.lit == {"q", "M_d"}
    QApplication.sendEvent(_form().fields["kind"].label, QEvent(QEvent.Type.Leave))
    assert not body.lit


def test_the_sections_are_an_accordion_kept_beside_the_modules():
    """UI-005 of the spec 2026-10-23-neige-correctifs-issues-96-99: each section of the form is numbered, says what its fields hold and a dot -- red where one of its fields stops the calculation, orange where one is only said, green else --, folds and unfolds on its own by its header, kept per tab on this machine beside the modules' order without either writing over the other; a message clicked opens the section of its field."""
    tab = _tab()
    import theme
    main, more = _form().sections["main"], _form().sections["more"]
    assert main.number.text() == "1" and more.number.text() == "2" and main.title.text() == tab.t("fk_s_main")
    _form().fields["span"].spin.setValue(4)
    assert "4 m" in main.summary.text() and main.severity == "ok" and theme.colour("ok") in main.dot.styleSheet()
    _form().fields["span"].spin.setValue(12)
    assert main.severity == "info" and theme.colour("warning") in main.dot.styleSheet()
    _form().fields["span"].spin.setValue(0)
    assert main.severity == "error" and theme.colour("danger") in main.dot.styleSheet() and more.severity == "ok"
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    left = Qt.MouseButton.LeftButton
    main.header.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(2, 2), QPointF(2, 2), left, left, Qt.KeyboardModifier.NoModifier))
    assert main.folded and main.body.isHidden() and not more.folded
    kept = _STATE["store"].settings["modules"]["tab_fake"]
    assert kept["sections"] == ["main"] and "order" in kept and "folded" in kept, "the sections beside the modules"
    _modules().pane.move("chart", 0)
    assert _STATE["store"].settings["modules"]["tab_fake"]["sections"] == ["main"], "a module moved keeps the sections"
    _modules().pane.move("state", 0)
    tab.ctx.focus_field("span")
    assert not main.folded, "a message on a field of a folded section opens it"
    assert _STATE["store"].settings["modules"]["tab_fake"]["sections"] == [] and _STATE["store"].settings["modules"]["tab_fake"]["order"][0] == "state"
    _form().fields["span"].spin.setValue(4)


def test_the_bubble_never_covers_its_info():
    _qt()
    import norm_bubble
    from PySide6.QtCore import QRect, QSize
    screen = QRect(0, 0, 1000, 800)
    trigger = QRect(100, 100, 12, 12)
    rect, scroll = norm_bubble.place(trigger, QSize(400, 300), screen)
    assert rect.top() > trigger.bottom() and not scroll and not rect.intersects(trigger)
    low = QRect(100, 700, 12, 12)
    rect, scroll = norm_bubble.place(low, QSize(400, 300), screen)
    assert rect.bottom() < low.top() and not scroll
    rect, scroll = norm_bubble.place(QRect(100, 380, 12, 12), QSize(400, 900), screen)
    assert scroll and not rect.intersects(QRect(100, 380, 12, 12)) and screen.contains(rect)
    rect, _scroll = norm_bubble.place(QRect(950, 100, 12, 12), QSize(400, 100), screen)
    assert rect.right() <= screen.right()


def test_the_reader_frames_the_rectangle_where_the_page_is_drawn():
    _qt()
    import norm_reader
    sizes = [(595.0, 842.0), (595.0, 842.0)]
    rect = norm_reader.page_rect_in_view(1, (40, 100, 548, 140), sizes, 1.0, 6, (6, 6, 6, 6), 607, (0, 0))
    assert (rect.x(), rect.y(), rect.width(), rect.height()) == (46.0, 6 + 842 + 6 + 100, 508.0, 40.0)
    centred = norm_reader.page_rect_in_view(0, (0, 0, 10, 10), sizes, 0.5, 6, (6, 6, 6, 6), 1000, (0, 50))
    assert centred.x() == (1000 - (297.5 + 12)) / 2 + 6 and centred.y() == 6 - 50
    from norms import excerpts
    e = excerpts.excerpt("sia261-2020-5.2-schnee", "5.3.4", "fr")
    if e.pdf() is None:
        raise conftest.Skip("SIA261-2020-FR.pdf is not in norm-library/")
    tab = _tab()
    reader = norm_reader.NormReader(tab.t, "fr")
    assert reader.show_excerpt(e)
    assert reader.document.pageCount() == 4 and reader.view.framed == (1, tuple(e.box)), "the chapter's four pages, the clause on its second"
    assert reader.view.frame_rect() is not None
    reader.close()


def test_the_cases_list_the_two_views_and_the_bubbles_delay_are_the_bases():
    """UI-001, UI-003: the invented domain's tab has the list of the cases with «Nouveau» and «Dupliquer», «Archives», and the views «Calcul» and «Affichage»; the bubble waits 350 ms."""
    tab = _tab()
    import norm_bubble
    import views
    from PySide6.QtWidgets import QPushButton
    assert tab.VIEWS == views.CALC_VIEWS == ("calc", "display")
    texts = {b.text() for b in tab.findChildren(QPushButton)}
    assert tab.word("new") in texts and tab.word("duplicate") in texts
    assert tab.service("cases").list is not None and norm_bubble.DELAY_MS == 350


def test_a_drop_reorders_and_the_state_is_each_tabs_on_this_machine():
    """UI-006, REQ-010: a module dropped on the pane takes its place; layout_store keeps one state per tab, two tabs apart, in the user's settings and never in the project."""
    tab = _tab()
    import layout_store
    import module_pane
    from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt
    from PySide6.QtGui import QDropEvent
    pane = _modules().pane
    data = QMimeData()
    data.setData(module_pane.MIME, b"chart")
    event = QDropEvent(QPointF(5, 1), Qt.DropAction.MoveAction, data, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    pane.dropEvent(event)
    assert pane.ids()[0] == "chart"
    pane.move("chart", 3)
    store = _Store()
    s = layout_store.Store(read=store.read, write=store.write)
    layout_store.put_state("tab_a", {"order": ["x", "y"], "folded": ["y"]}, s)
    layout_store.put_state("tab_b", {"order": ["y", "x"], "folded": []}, s)
    assert layout_store.get_state("tab_a", s) == {"order": ["x", "y"], "folded": ["y"]}
    assert layout_store.get_state("tab_b", s) == {"order": ["y", "x"], "folded": []}
    assert layout_store.get_state("tab_c", s) == {}
    assert not list(_STATE["here"].root.rglob("*modules*")), "nothing written into the project"


def test_an_excerpt_whose_edition_is_not_shipped_shows_its_words_and_says_so():
    """REQ-004, ARCH-013: an edition not there gives no image and no error, the bubble its words and a sentence; the shipped one cuts 5.3.4 into an image; the German window reads the German edition."""
    tab = _tab()
    import dataclasses
    import excerpt_image
    import norm_bubble
    from PySide6.QtWidgets import QLabel
    from norms import excerpts
    e = excerpts.excerpt("sia261-2020-5.2-schnee", "5.3.4", "fr")
    gone = dataclasses.replace(e, file="SIA261-2020-XX.pdf")
    assert excerpt_image.image(gone) is None
    view = norm_bubble.ExcerptView([gone], tab.t)
    assert tab.t("ct_no_pdf", file="SIA261-2020-XX.pdf") in [l.text() for l in view.findChildren(QLabel)]
    assert excerpts.excerpt("sia261-2020-5.2-schnee", "5.3.4", "de").file == "SIA261-2020-DE.pdf"
    if e.pdf() is None:
        raise conftest.Skip("SIA261-2020-FR.pdf is not in norm-library/")
    image = excerpt_image.image(e)
    assert image is not None and image.width() > 500 and image.height() > 40


# --- the bricks completed for every tab (spec 2026-10-23-onglet-vent-briques, V2: ARCH-003 to ARCH-006, ARCH-RISK-014), on the invented domain's third section

def test_the_bricks_hold_no_word_of_the_wind():
    """ARCH-004: the hovers by keys, the blocks and the pins know no pressure coefficient, no direction and no wind -- the keys are the domain's, opaque."""
    for name in ("calc_blocks.py", "tab_host.py", "calc_modules.py", "module_pane.py", "calc_form.py", "calc_fields.py"):
        text = _code(TOOLS / name).lower()
        found = [w for w in ("cpe", "cpi", "φ", "wind", "vent", "c_pe", "c_pi") if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", text)]
        assert not found, (name, found)


def test_a_section_holds_a_line_of_fields_a_special_value_a_text_a_formula_and_a_select_on_the_line_of_its_words():
    """ARCH-003, ARCH-RISK-014: b · d on one row; h's special value «= l» writes null and gives the number back unticked; the text and the formula said from the blocks' data; the side chosen on the line of its words, filled and collected as a field, the table's marked column following it."""
    tab = _tab()
    form = _form()
    assert form.rows["width"][1] is form.rows["depth"][1], "b and d on one row"
    height = form.fields["height"]
    assert height.special is not None and tab.draft()["height"] is None and height.special.isChecked() and not height.spin.isEnabled()
    height.special.setChecked(False)
    height.spin.setValue(2.5)
    assert tab.draft()["height"] == 2.5
    height.special.setChecked(True)
    assert tab.draft()["height"] is None and height.summary(tab.draft()) == "h = l"
    form.fields["span"].spin.setValue(6)
    note, rule = form.blocks["note"].body, form.blocks["rule"].body
    assert note.label.text() == "A beam of 6 m" and "M<sub>d</sub>" in rule.label.text() and "5.2.2" in rule.label.text()
    side = form.fields["side"]
    assert form.rows["side"][1] is form.blocks["side_row"], "the select stands in its row_select"
    assert "c<sub>pi</sub> of the side" in form.blocks["side_row"].body.label.text()
    side.combo.setCurrentIndex(side.combo.findData("B"))
    assert tab.draft()["side"] == "B"
    table = form.blocks["coeffs"].body
    assert [c["marked"] for c in tab.ctx.blocks["coeffs"]["columns"]] == [False, True], "the marked column follows the side"
    assert form.section_of("side") == "blocks" and form.section_of("width") == "blocks"


def test_a_heat_table_colours_its_cells_by_their_value_from_the_theme():
    """ARCH-006: a cell's ground is theme.json's heat token of its value against the table's largest -- a pair by its strongest, none transparent --, ±0,2 written as the norm writes it, a legend under it; the table scrolls sideways below its width."""
    _tab()
    import calc_blocks
    import theme
    table = _form().blocks["coeffs"].body
    assert calc_blocks.heat_token(0.8, 0.8) == "heat-p3" and calc_blocks.heat_token(-0.5, 0.8) == "heat-s2" and calc_blocks.heat_token(0.01, 0.8) == "heat-z0" and calc_blocks.heat_token(0.2, 0.8) == "heat-p1"
    label, _keys, base = table.cells["cell:A:0"]
    assert theme.colour("heat-p3") in base and table.cells["cell:B:0"][0].text() == "±0.2" and table.cells["cell:B:1"][0].text() == "–"
    assert "transparent" in table.cells["cell:B:1"][2] and table.legend.isVisibleTo(table)
    assert calc_blocks.cell_text([0.15, -0.21]) == "0.15/−0.21" and calc_blocks.cell_text("direct") == "*"
    assert _form().blocks["coeffs"].body.minimumWidth() == 200


def test_an_element_hovered_lights_and_frames_what_its_keys_name_both_ways():
    """ARCH-004, UI-021: a cell hovered lights itself and the result it gives (M_d), and frames the cell beside it; the result hovered lights the cell back; nothing hovered, all plain -- the links the domain's, read once per calculation."""
    tab = _tab()
    _form().fields["span"].spin.setValue(5)
    table = _form().blocks["coeffs"].body
    results = _modules().pane.modules["results"].body
    tab.ctx.hover_element("cell:A:0")
    assert table.lit_ids() == {"cell:A:0"} and table.framed_ids() == {"cell:B:0"} and "M_d" in results.keyed
    tab.ctx.hover_element(None)
    assert not table.lit_ids() and not table.framed_ids() and not results.keyed
    results._enter("M_d")
    assert table.lit_ids() == {"cell:A:0"}
    results._enter(None)
    assert not table.lit_ids()


def test_a_block_is_pinned_under_the_results_kept_through_a_rebuild_and_a_window_may_follow_its_size():
    """ARCH-005: the table's 📌 pins it under «Résultats», once, a module of its own refreshed with the others; its id `b:coeffs` brings it back after a rebuild beside the excerpts; a module whose window fills it lays its body out at the window's size."""
    tab = _tab()
    import calc_blocks
    import module_pane
    pane = _modules().pane
    wrapper = _form().blocks["coeffs"]
    assert wrapper.pin is not None and _form().blocks["note"].pin is None
    wrapper.pin.click()
    wrapper.pin.click()
    assert pane.pins.count("b:coeffs") == 1 and pane.order.index("b:coeffs") == pane.order.index("results") + 1
    module = pane.modules["b:coeffs"]
    assert module.spec.kind == "block" and module.spec.title == "Coefficients" and isinstance(module.body.body, calc_blocks.HeatTable)
    assert module.body.pin is None, "pinned, no pin of its own"
    _form().fields["span"].spin.setValue(7)
    assert module.body.body.cells, "refreshed with the others"
    kept = _modules().state()
    pane.remove("b:coeffs")
    assert "b:coeffs" not in pane.modules
    _modules().restore(kept)
    assert "b:coeffs" in pane.modules
    pane.remove("b:coeffs")
    from PySide6.QtWidgets import QLabel
    spec = module_pane.ModuleSpec("fill", "Fill", lambda: QLabel("drawn"), fills_window=True)
    pane.add(spec)
    window = pane.open_window("fill")
    assert isinstance(window, module_pane.FillingWindow)
    window.resize(800, 600)
    window.layout().activate()
    assert window.body.width() > 700, "the body follows the window"
    window.close()


def test_a_drawing_s_view_is_the_context_s_one_per_drawing():
    """ARCH-005 (T87): the view of a drawing -- its rotation, its zoom, its direction -- is held by the context by its key, the same for its bodies in the form, the pane and a window, each drawing its own."""
    tab = _tab()
    view = tab.ctx.view_state("model")
    view["azimuth"] = 30
    assert tab.ctx.view_state("model") is view and tab.ctx.view_state("model")["azimuth"] == 30 and tab.ctx.view_state("other") == {}


def fake_domain_box():
    """The invented domain's 3D test model, for tests/test_model3d_widget.py."""
    _qt()
    import fake_domain
    return fake_domain.box({})
