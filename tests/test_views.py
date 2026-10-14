"""The views of a tab, chosen in the top bar (v0.117, calc/tools/views.py; spec docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md, UI-001 to UI-005, REQ-006, REQ-010, ARCH-001).

The engineer, 07.10.2026: «il y a pour l'instant trop d'informations dans les onglets. On se perd un peu» -- a switch left of FR · DE · EN, «document import, dessin, typst et document export» for the plans, «calcul et affichage» for a check, and the same for «la plupart des onglets». Held here: where the switch stands and what it holds for the tab in front; that every tab of the engineer's list that exists declares its views; that the plans' four views show their own boxes and their own pages; that a view is remembered in the user's settings, never in the project; and that a view remembered as one that compiles compiles nothing while the window is built (review A10).
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
          "tab_mc_buckling", "tab_mc_ltb", "tab_mc_fire", "tab_variables")


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
        if key.startswith("tab_mc_") and key not in LISTED or key in ("tab_commands", "tab_structure", "tab_annexes", "tab_python"):
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


def test_a_view_is_remembered_in_the_users_settings_and_never_in_the_project():
    window, here = _window()   # a project begun on its convention d'utilisation, whose modules the journal is one of (MODE_TABS)
    import usersettings
    with project.using(here), _boxes():
        index, tab = _tab(window, "tab_journal")
        window.tab_widget.setCurrentIndex(index)
        before = here.file.read_bytes()
        window.on_view_chosen("display")
        assert usersettings.read()["views"]["tab_journal"] == "display"
        assert here.file.read_bytes() == before, "a view is the engineer's preference, not the project's"
        window.rebuild()
        index, tab = _tab(window, "tab_journal")
        assert tab.view == "display", "a rebuild of the window keeps the view"
        window.on_view_chosen("entry")
        assert usersettings.read()["views"]["tab_journal"] == "entry"


def test_a_view_that_compiles_compiles_nothing_while_the_window_is_built():
    """Views remembered as «Typst» and «Affichage»: the window built off-screen and never shown asks Typst for nothing (review A10) -- the page is asked for when a tab is shown in that view."""
    _qt()
    import pdf_pane
    import usersettings
    settings = usersettings.read()
    # «tab_loads» kept on purpose: the tab was retired in v0.117 (issue 13), and a user's settings that still name it must build the window all the same (review ARCH-RISK-008)
    usersettings.write({**settings, "views": {"tab_plan": "typst", "tab_fire": "typst", "tab_mc_tension": "display", "tab_statics": "display", "tab_loads": "display"},
                        "layouts": {"last_used": "old-screens", "old-screens": {"tab_loads": {"calc": {"panes": [0.7, 0.3]}}}}})
    asked = []
    original = pdf_pane.PdfPane.request_snippet
    pdf_pane.PdfPane.request_snippet = lambda self, *a: asked.append(a)
    try:
        here = conftest.project_copy("views_no_compile")
        with project.using(here), _boxes():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            assert "tab_loads" not in [key for key, _factory in woodcore_gui.TABS] and len(window.tabs) == len(woodcore_gui.TABS), "no ghost of the retired loads tab"
            index, plan = _tab(window, "tab_plan")
            assert plan.view == "typst" and plan.view_pending, "the view is a state until the tab is shown"
            assert not asked, f"{len(asked)} compile(s) asked for while the window was built"
            conftest.dispose(window)
    finally:
        pdf_pane.PdfPane.request_snippet = original
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
    """REQ-008 and REQ-009, tab by tab: in «Affichage» every command offered for what is chosen on the left gives its own call, and either a page is asked for or a note says why there is none. The variables offer val and var, each with its own options."""
    window, here = _window()
    import views
    import woodcore_gui
    with project.using(here), _boxes() as shown:
        for key, _factory in woodcore_gui.TABS:
            index, tab = _tab(window, key)
            if "display" not in views.declared(tab):
                continue
            window.tab_widget.setCurrentIndex(index)
            if key == "tab_variables":
                exported = next((d for d in tab.export.domains if d.variables), None)
                assert exported is not None, "the example's export lists values"
                tab.select_key(("export", exported.name, exported.variables[0].key))
                assert tab.variable(tab.selected_key()) is not None
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
            if key == "tab_variables" and display.chooser.count() >= 2:
                titles = [display.chooser.itemText(i) for i in range(display.chooser.count())]
                assert titles[:2] == ["val", "var"], titles
                display.chooser.setCurrentIndex(0)
                val_options = set(display.panel().controls)
                display.chooser.setCurrentIndex(1)
                assert set(display.panel().controls) != val_options, "val and var have their own options"
            display.activate(False)
            window.on_view_chosen(views.declared(tab)[0])
        assert not shown, shown


def test_the_loads_offer_each_rows_commands_a_value_a_case_and_a_category():
    """REQ-008 of v0.117 for the loads, carried to the Variables tab that took them over in v0.117 (issue 13, D-006, D-013): a value offers val, var, show-input and the bare objects; a case show-calc, each of its checks, the loop over its calculation's cases and the two summary tables; a category of SIA 261 Tabelle 8 show-live-load first -- and each gives its own call, its page asked for or a note saying why there is none."""
    window, here = _window()
    with project.using(here), _boxes() as shown:
        index, tab = _tab(window, "tab_variables")
        window.tab_widget.setCurrentIndex(index)
        window.on_view_chosen("display")
        display = tab.display
        asked = []
        display.pane.request_snippet = lambda *a: asked.append(a)
        display.activate(True)
        case = next(d for d in tab.export.domains if d.address and d.address[0] not in ("live-load", "connection", "connector", "script") and d.variables)
        live = next(d for d in tab.export.domains if d.address and d.address[0] == "live-load" and d.variable("q_k") is not None)
        rows = {
            "value": ("export", case.name, case.variables[0].key),
            "case": ("export", case.name, None),
            "category": ("export", live.name, None),
        }
        expected = {
            "value": ["val", "var", "show-input", "var-of"],
            "case": ["show-calc"],
            "category": ["show-live-load", "show-calc"],
        }
        for what, key in rows.items():
            tab.select_key(key)
            titles = [display.chooser.itemText(n) for n in range(display.chooser.count())]
            assert titles[:len(expected[what])] == expected[what], (what, titles)
            if what != "value":
                assert titles[-2:] == ["show-load-summary", "show-line-load-summary"], (what, titles)
                assert display.t("ds_loop", command="show-calc") in titles, (what, titles)
            calls = []
            for n in range(display.chooser.count()):
                before = len(asked)
                display.chooser.setCurrentIndex(n)
                calls.append(display.command())
                assert len(asked) > before or not display.note.isHidden() or n == 0, (what, titles[n])
            assert len(set(calls)) == len(calls), (what, calls)
        display.activate(False)
        window.on_view_chosen("data")
        assert not shown, shown

