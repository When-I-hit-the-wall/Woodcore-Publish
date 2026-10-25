"""The views of a tab, chosen in the top bar (v0.117, calc/tools/views.py; spec docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md, UI-001 to UI-005, REQ-006, REQ-010, ARCH-001).

The engineer, 07.10.2026: «il y a pour l'instant trop d'informations dans les onglets. On se perd un peu» -- a switch left of FR · DE · EN, «document import, dessin, typst et document export» for the plans, «calcul et affichage» for a check, and the same for «la plupart des onglets». Held here: where the switch stands and what it holds for the tab in front; that every tab of the engineer's list that exists declares its views; that the plans' four views show their own boxes and their own pages; that a tab arrives in its first view and compiles nothing, its view holding while it stays in front and through a rebuild, never in the user's settings nor in the project (issue #86); and that the views kept by older versions are no longer read (review A10).
"""

import contextlib
import os
import sys

import conftest
from conftest import ROOT, Skip

import project

_STATE = {}

# The engineer's list (T22) as the window names its tabs; the six checks not built yet get their views when they are built on MemberCheckTab, as «Flexion» did (08.10.2026).
LISTED = ("tab_plan", "tab_fire", "tab_positions", "tab_journal", "tab_statics", "tab_schema", "tab_connections",
          "tab_polar", "tab_mc_tension", "tab_mc_compression", "tab_mc_bending", "tab_mc_shear",
          "tab_mc_fire")
# Tabs of the list that have one view since then: «Variables» lost «Affichage» with issue #114 (D-4, the engineer: the card suffices).
ONE_VIEW = ("tab_variables",)


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
def _boxes():
    from PySide6.QtWidgets import QMessageBox
    shown = []
    names = ("warning", "critical", "information", "question")
    originals = {name: QMessageBox.__dict__[name] for name in names}
    for name in names:
        setattr(QMessageBox, name, staticmethod(lambda *a, name=name, **k: shown.append(name) or QMessageBox.StandardButton.Ok))
    try:
        yield shown
    finally:
        for name, original in originals.items():
            setattr(QMessageBox, name, original)


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("views_v0118")
        with project.using(here), _boxes():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window, key):
    import woodcore_gui
    index = [k for k, _f in woodcore_gui.TABS].index(key)
    return index, window.tabs[index]


def test_the_switch_stands_left_of_the_languages_and_holds_the_views_of_the_tab_in_front():
    window, here = _window()
    import views
    with project.using(here), _boxes() as shown:
        layout = window.centralWidget().layout().itemAt(0).layout()
        widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
        assert widgets.index(window.view_switch) < widgets.index(window.language), "the switch stands left of FR · DE · EN"
        # the notices' indicators stand between them since issue #11 (woodcore_gui.py), and nothing else
        assert [w for w in widgets[widgets.index(window.view_switch) + 1:widgets.index(window.language)] if w is not None] == [window.notice_bar], "only the notices between them"
        index, plan = _tab(window, "tab_plan")
        window.tab_widget.setCurrentIndex(index)
        assert not window.view_switch.isHidden() and window.view_switch.keys == ["import", "draw", "typst", "export"]
        assert [window.view_switch.button(k).text() for k in window.view_switch.keys] == [window.t(views.WORDS[k]) for k in window.view_switch.keys]
        index, _check = _tab(window, "tab_mc_tension")
        window.tab_widget.setCurrentIndex(index)
        assert window.view_switch.keys == ["calc", "display"]
        index, _commands = _tab(window, "tab_commands")
        window.tab_widget.setCurrentIndex(index)
        assert window.view_switch.isHidden(), "a tab without views shows no switch"
        assert not shown, shown


def test_every_tab_of_the_list_declares_its_views_and_the_words_are_in_three_languages():
    window, _here = _window()
    import views
    import woodcore_gui
    for key, tab in zip([k for k, _f in woodcore_gui.TABS], window.tabs):
        declared = views.declared(tab)
        if key in LISTED:
            assert declared and ("display" in declared or "typst" in declared), (key, declared)   # how the report prints it: «Affichage», a plan's being its compiled #show-plan (key `typst`)
            assert all(view in views.WORDS for view in declared), (key, declared)
        if key.startswith("tab_mc_") and key not in LISTED or key in ("tab_commands", "tab_structure", "tab_annexes", "tab_python") + ONE_VIEW:
            assert not declared, (key, declared)
    reference = set(views.STRINGS["fr"])
    assert set(views.STRINGS["de"]) == reference == set(views.STRINGS["en"])
    for view, word in views.WORDS.items():
        assert word in reference and views.TIPS[view] in reference, view
    # the plans' compiled command is named as every tab's display view (UI-007 of spec 2026-10-07-performance-erreurs-plans-legendes): «Affichage», «Darstellung», «Display»
    assert [views.STRINGS[lang][views.WORDS["typst"]] for lang in ("fr", "de", "en")] == ["Affichage", "Darstellung", "Display"]


def test_the_plan_tab_is_named_plan_de_positions_and_its_four_views_in_three_languages():
    """UI-006 and UI-007 of spec 2026-10-07-performance-erreurs-plans-legendes: the tab's title as the window shows it, and the four buttons of a plan's switch -- «Typst» became «Affichage», the word of every tab's display view."""
    window, _here = _window()
    import plan_tab
    import views
    import woodcore_gui
    index, _tab_ = _tab(window, "tab_plan")
    assert window.tab_widget.tabText(index) == window.t("tab_plan")
    titles = {lang: woodcore_gui.STRINGS[lang]["tab_plan"] for lang in ("fr", "de", "en")}
    assert titles == {"fr": "Plan de positions", "de": "Positionsplan", "en": "Position plan"}, titles
    for lang, expected in (("fr", ["Import", "Dessin", "Affichage", "Export"]), ("de", ["Import", "Zeichnung", "Darstellung", "Export"]),
                           ("en", ["Import", "Drawing", "Display", "Export"])):
        names = [name for _key, name, _tip in views.items(plan_tab.PlanTab, lambda key: woodcore_gui.STRINGS[lang][key])]
        assert names == expected, (lang, names)


def test_the_plans_four_views_show_their_own_boxes_and_pages():
    window, here = _window()
    import drawing_tab
    with project.using(here), _boxes() as shown:
        for key in ("tab_plan", "tab_fire"):
            index, tab = _tab(window, key)
            window.tab_widget.setCurrentIndex(index)
            for view in ("import", "draw", "typst", "export"):
                window.on_view_chosen(view)
                assert tab.view == view and window.view_switch.current_key() == view, (key, view)
                kind = drawing_tab.VIEW_KIND[view]
                assert tab.view_kind == kind and tab.center.currentIndex() == drawing_tab.KINDS.index(kind) == tab.right.currentIndex(), (key, view)
                shown_boxes = sorted(name for name, box in tab.left_boxes.items() if not box.isHidden())
                assert shown_boxes == sorted(n for n in drawing_tab.VIEW_BOXES[view] if n in tab.left_boxes), (key, view, shown_boxes)
                if view == "typst":
                    assert all(button.isHidden() for button in tab.plan_buttons), "a plan is chosen in «Typst», not made"
                    assert tab.builder.options.plan.isHidden(), "the list of the left pane is the one choice of the plan"
            tab.builder.stop()
            # a frame of a document opening its plan: the switch follows the tab
            window.on_view_chosen("import")
            tab.show_plan_view()
            assert tab.view == "draw" and window.view_switch.current_key() == "draw", key
        assert not shown, shown


@contextlib.contextmanager
def _compiles():
    """Every page asked of Typst -- a snippet or a document -- counted rather than compiled."""
    import pdf_pane
    asked = []
    originals = (pdf_pane.PdfPane.request_snippet, pdf_pane.PdfPane.request)
    pdf_pane.PdfPane.request_snippet = lambda self, *a, **k: asked.append(("snippet", a))
    pdf_pane.PdfPane.request = lambda self, *a, **k: asked.append(("document", a))
    try:
        yield asked
    finally:
        pdf_pane.PdfPane.request_snippet, pdf_pane.PdfPane.request = originals


def _shown(window):
    """The window shown, as the engineer meets it: a tab's showEvent -- where «Affichage» compiles -- happens only on a window shown (issue #86's review: a hidden window passes a test of arrival wrongly)."""
    from PySide6.QtWidgets import QApplication
    window.show()
    for _ in range(3):
        QApplication.processEvents()


def test_a_tab_arrives_in_its_first_view_and_compiles_nothing():
    """Issue #86 (the engineer, 21.10.2026: «lorsque l'on ouvre un onglet, on est toujours en mode calcul et pas en mode affichage») -- a check left in «Affichage» and a plan left in «Typst» come back in «Calcul» and «Dessin», and arriving asks Typst for nothing."""
    from PySide6.QtWidgets import QApplication
    window, here = _window()
    _shown(window)
    with project.using(here), _boxes():
        rest, _other = _tab(window, "tab_positions")
        for key, away, first in (("tab_mc_bending", "display", "calc"), ("tab_plan", "typst", "draw"), ("tab_statics", "display", "draw")):
            index, tab = _tab(window, key)
            with _compiles():
                window.tab_widget.setCurrentIndex(index)
                QApplication.processEvents()
                window.on_view_chosen(away)
                QApplication.processEvents()
                assert tab.view == away, key
                window.tab_widget.setCurrentIndex(rest)
                QApplication.processEvents()
            assert tab.view == first, f"{key}: left in «{away}», put back in «{tab.view}» rather than its first view"
            with _compiles() as asked:
                window.tab_widget.setCurrentIndex(index)
                QApplication.processEvents()
            assert tab.view == first and window.view_switch.current_key() == first, (key, tab.view)
            assert not asked, f"{key}: arriving asked Typst for {asked}"


def test_the_view_holds_while_the_tab_stays_in_front_and_through_a_rebuild():
    """The view chosen holds while the tab is in front, through a rebuild of the window (an export, a change of language) -- carried in memory, never in the user's settings nor in the project."""
    import usersettings
    window, here = _window()
    with project.using(here), _boxes(), _compiles():
        index, tab = _tab(window, "tab_journal")
        window.tab_widget.setCurrentIndex(index)
        settings = usersettings.read().get("views")
        before = here.file.read_bytes()
        window.on_view_chosen("display")
        assert usersettings.read().get("views") == settings, "the view is written in the user's settings again"
        assert here.file.read_bytes() == before, "a view is not the project's"
        window.rebuild()
        index, tab = _tab(window, "tab_journal")
        assert window.tab_widget.currentIndex() == index and tab.view == "display", "a rebuild of the window loses the view of the tab in front"
        window.refresh_tab("tab_journal")
        index, tab = _tab(window, "tab_journal")
        assert tab.view == "display", "a tab built again in its place loses its view"
        window.on_view_chosen("entry")


def test_the_views_setting_is_neither_read_nor_written():
    """Views kept by a version up to 0.121 -- «Typst» and «Affichage» -- are no longer read: the window is built with every tab in its first view and asks Typst for nothing (review A10); the key is left in the settings as it is."""
    _qt()
    import usersettings
    settings = usersettings.read()
    # «tab_loads» kept on purpose: the tab was retired in v0.117 (issue 13), and a user's settings that still name it must build the window all the same (review ARCH-RISK-008)
    kept = {"tab_plan": "typst", "tab_fire": "typst", "tab_mc_tension": "display", "tab_statics": "display", "tab_loads": "display"}
    usersettings.write({**settings, "views": kept, "layouts": {"last_used": "old-screens", "old-screens": {"tab_loads": {"calc": {"panes": [0.7, 0.3]}}}}})
    try:
        here = conftest.project_copy("views_no_compile")
        with project.using(here), _boxes(), _compiles() as asked:
            import views
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            assert "tab_loads" not in [key for key, _factory in woodcore_gui.TABS] and len(window.tabs) == len(woodcore_gui.TABS), "no ghost of the retired loads tab"
            for key in ("tab_plan", "tab_fire", "tab_mc_tension", "tab_statics"):
                _index, tab = _tab(window, key)
                assert tab.view == views.default(tab), f"{key}: built in «{tab.view}» from the old setting"
            assert not asked, f"{len(asked)} compile(s) asked for while the window was built"
            index, plan = _tab(window, "tab_plan")
            window.tab_widget.setCurrentIndex(index)
            window.on_view_chosen("export")
            assert usersettings.read()["views"] == kept, "the old key is rewritten"
            conftest.dispose(window)
    finally:
        usersettings.write(settings)


def test_the_typst_view_takes_its_plan_from_the_list_and_recompiles_at_every_option():
    """UI-004: in «Typst» the plan is the one chosen on the left -- another one chosen, the call names it and the page is asked for again --, and an option changed asks for it again."""
    window, here = _window()
    with project.using(here), _boxes() as shown:
        for key in ("tab_plan", "tab_fire"):
            index, tab = _tab(window, key)
            window.tab_widget.setCurrentIndex(index)
            window.on_view_chosen("typst")
            tab.enter_view()            # what the tab's showEvent does on screen
            asked = []
            tab.builder.pane.request_snippet = lambda *a: asked.append(a)
            plans = [pid for pid in tab.list.ids() if pid in tab.builder.options.records]
            assert len(plans) >= 2, (key, plans)
            other = next(pid for pid in plans if pid != tab.current_id)
            tab.on_list_change(other)
            assert tab.current_id == other and f'("{other}"' in tab.builder.command() and asked, (key, tab.builder.command())
            count = len(asked)
            tab.builder.options.width.setCurrentText("60%")
            assert "width: 60%" in tab.builder.command() and len(asked) > count, key
            tab.builder.options.width.setCurrentText("100%")
            tab.builder.stop()
            window.on_view_chosen("draw")
        _i, plan = _tab(window, "tab_plan")
        _i, fire = _tab(window, "tab_fire")
        assert plan.builder.preview_folder != fire.builder.preview_folder, "the two tabs of plans compiled into one file until v0.117"
        assert not shown, shown


def test_affichage_offers_each_tabs_commands_and_each_changes_the_call():
    """REQ-008 and REQ-009, tab by tab: in «Affichage» every command offered for what is chosen on the left gives its own call, and either a page is asked for or a note says why there is none. (The loads' commands, «Variables»' «Affichage» since v0.117, are its card's since issue #114: tests/test_variable_card.py.)"""
    window, here = _window()
    import views
    import woodcore_gui
    with project.using(here), _boxes() as shown:
        for key, _factory in woodcore_gui.TABS:
            index, tab = _tab(window, key)
            if "display" not in views.declared(tab):
                continue
            window.tab_widget.setCurrentIndex(index)
            window.on_view_chosen("display")
            display = tab.display
            asked = []
            display.pane.request_snippet = lambda *a: asked.append(a)
            display.activate(True)
            calls = []
            for n in range(display.chooser.count()):
                before = len(asked) if n else 0     # the first is shown already: activating the view asked for its page
                display.chooser.setCurrentIndex(n)
                calls.append(display.command())
                assert display.command(), (key, display.current().title)
                assert len(asked) > before or not display.note.isHidden(), (key, display.current().title, "neither a page asked for nor a note")
            assert len(set(calls)) == len(calls), (key, calls)
            display.activate(False)
            window.on_view_chosen(views.declared(tab)[0])
        assert not shown, shown


def test_a_page_zoomed_goes_back_to_its_width_when_its_tab_is_left():
    """Issue #89: the zoom of a Typst page holds while its tab is in front, and the page is fitted to its pane again once the tab is left."""
    window, here = _window()
    import pdf_pane
    from PySide6.QtPdfWidgets import QPdfView
    with project.using(here), _boxes(), _compiles():
        index, tab = _tab(window, "tab_structure")
        window.tab_widget.setCurrentIndex(index)
        pages = tab.findChildren(pdf_pane.ZoomablePdfView)
        assert pages, "the Structure tab shows no page"
        pages[0].setZoomMode(QPdfView.ZoomMode.Custom)
        window.tab_widget.setCurrentIndex(_tab(window, "tab_positions")[0])
        assert pages[0].zoomMode() == QPdfView.ZoomMode.FitToWidth, "a page left zoomed"
