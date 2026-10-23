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
BASE = ("calc_tab.py", "calc_fields.py", "module_pane.py", "norm_bubble.py", "norm_reader.py", "excerpt_image.py", "calc_tab_words.py")


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
        import load_tab
        import woodcore_gui
        import woodcore_gui_words
        for lang, words in fake_domain.WORDS.items():
            woodcore_gui_words.STRINGS[lang].update(words)
        here = conftest.project_copy("calc_tab_base")
        store = _Store()
        with project.using(here):
            window = woodcore_gui.MainWindow()

            class FakeTab(calc_tab.DeclaredTabMixin, load_tab.LoadTab):
                KEY = "tab_fake"
                MODULE = fake_domain
                ID_PREFIX = "BM-"
                LIST_KEY = "fk_list"
                EMPTY_KEY = "fk_empty"
            FakeTab.__module__ = "fake_domain"            # source_editor.list_words reads the list's words off the tab's module
            fake_domain.STRINGS = load_tab.STRINGS
            original = layout_store.Store
            layout_store.Store = lambda *a, **k: original(read=store.read, write=store.write)
            try:
                tab = FakeTab(window)
            finally:
                layout_store.Store = original
            tab.pane.store = original(read=store.read, write=store.write)
        _STATE.update(tab=tab, here=here, store=store)
    return _STATE["tab"]


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
    assert set(tab.fields) == {"span", "kind", "shape", "braced", "grade"}
    assert all(isinstance(f, calc_fields.FieldWidget) for f in tab.fields.values())
    assert [f.field.kind for f in tab.fields.values()] == ["number", "buttons", "tiles", "checkbox", "select"]
    assert all(f.info.isVisibleTo(f.label) or not f.field.excerpts for f in tab.fields.values()) and tab.fields["span"].info.text() == "ⓘ"
    assert [b.text() for b in tab.fields["kind"].buttons.values()] == ["light 0.5", "heavy 2"]
    assert [b.text() for b in tab.fields["shape"].buttons.values()] == ["box", "slab"] and not tab.fields["shape"].buttons["box"].icon().isNull()
    # a row the source does not show
    form, widget = tab.rows["grade"]
    assert not form.isRowVisible(widget)
    tab.fields["braced"].check.setChecked(True)
    tab.field_changed("braced")
    assert form.isRowVisible(widget)
    # a free value is the source's, and the buttons' choice again
    tab.fields["kind"].free.setValue(3.0)
    assert tab.draft()["kind"] == "custom" and tab.draft()["factor"] == 3.0
    tab.fields["kind"].buttons["light"].click()
    assert tab.draft()["kind"] == "light" and "factor" not in tab.draft()


def test_the_state_says_red_orange_green_and_takes_to_the_field():
    tab = _tab()
    state = tab.pane.modules["state"].body
    tab.fields["span"].spin.setValue(5)
    assert tab.instance and [r.text() for r in state.rows] == ["✓ " + tab.t("ct_complete")]
    assert tab.pane.modules["state"].summary.text() == tab.t("ct_summary_complete")
    tab.fields["span"].spin.setValue(12)
    assert [r.property("callout") for r in state.rows] == ["info", "warning"] and state.rows[1].text() == "A long span: 12 m"
    tab.fields["span"].spin.setValue(0)
    assert tab.instance is None and [r.property("callout") for r in state.rows] == ["danger"]
    state.rows[0].mousePressEvent(None)
    assert tab.fields["span"].blinking
    tab.fields["span"].spin.setValue(4)


def test_the_results_are_what_is_computed_and_the_chart_reads_under_the_pointer():
    tab = _tab()
    tab.fields["span"].spin.setValue(4)
    html = tab.pane.modules["results"].body.label.text()
    assert "M<sub>d</sub>" in html and "<sub>" in html and ">l<" not in html, "the span is an input, never a result"
    chart = tab.pane.modules["chart"].body
    assert chart.data["marks"][0]["x"] == 4 and abs(chart.probe(5.0)[0][1] - 0.5 * 12.5 / 2) < 1e-9
    assert "<svg" in tab.drawing


def test_the_modules_move_fold_and_are_kept_per_tab_and_an_excerpt_is_pinned_once():
    tab = _tab()
    from PySide6.QtWidgets import QToolButton
    pane = tab.pane
    assert pane.ids()[:4] == ["state", "results", "drawing", "chart"]
    arrows = [b for b in pane.findChildren(QToolButton) if b.text() in ("↑", "↓", "▲", "▼")]
    assert not arrows, "no arrow moves a module (D-6)"
    assert all(pane.modules[i].close_button is None for i in ("state", "results", "drawing", "chart"))
    pane.move("chart", 0)
    pane.modules["results"].set_folded(True)
    kept = _STATE["store"].settings["modules"]["tab_fake"]
    assert kept["order"][0] == "chart" and kept["folded"] == ["results"]
    module = tab.pin_excerpts("sia261-2020-5.2-schnee", ("5.3.4",))
    again = tab.pin_excerpts("sia261-2020-5.2-schnee", ("5.3.4",))
    assert module is again and pane.ids().count(module.spec.id) == 1
    assert pane.ids().index(module.spec.id) == pane.ids().index("results") + 1, "under «Résultats»"
    second = tab.pin_excerpts("sia261-2020-5.2-schnee", ("fig3",))
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
    items = tab.bubbles.excerpts("sia261-2020-5.2-schnee", ("5.3.4",))
    view = norm_bubble.ExcerptView(items, tab.t)
    labels = [w for w in view.findChildren(QLabel)]
    assert labels[0].text().startswith("SIA 261:2020 · 5.3.4") and labels[1].text()[:30] == items[0].text[:30], "the words first (D-4)"
    assert isinstance(labels[2], norm_bubble.FitImage) or labels[2].text() == tab.t("ct_no_pdf", file=items[0].file), "then the image"
    from norms import excerpts
    assert excerpts.excerpt("sia261-2020-5.2-schnee", "5.3.4", "en").lang == "de"
    bare = norm_bubble.ExcerptView(items, tab.t, bare=True)
    assert not [w for w in bare.findChildren(QLabel) if w.text().startswith("SIA")], "a tile's bubble shows the excerpt alone (T28)"


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
    assert tab.list is not None and norm_bubble.DELAY_MS == 350


def test_a_drop_reorders_and_the_state_is_each_tabs_on_this_machine():
    """UI-006, REQ-010: a module dropped on the pane takes its place; layout_store keeps one state per tab, two tabs apart, in the user's settings and never in the project."""
    tab = _tab()
    import layout_store
    import module_pane
    from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt
    from PySide6.QtGui import QDropEvent
    pane = tab.pane
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
