"""The «Structure du document» tab (calc/tools/structure_tab.py, structure_tree.py, import_dialog.py; the engineer's rework of 01.10.2026, work package R2-D1): **the one tab a document is written in**, in the convention d'utilisation, the base de projet and the report alike.

What the tree, the panes, the model and the snippet each do has its own module's tests (tests/test_structure.py, test_object_panes.py, test_structure_preview.py, test_pdf_pane.py, test_doc_import.py, test_sync.py, test_typst_objects.py). What is held here is what the tab ties together and none of them can see alone: that the tree shows **chapters › sections › objects** with an icon, a box and a mark each; that choosing a row shows its pane and the page of **that row only**; that a pane writes **between the object's tags and nowhere else** -- the bytes outside unchanged, an object written by hand asked about first, a file changed under a pane refused -- and does not reload the pane it came from; that a drop on the tree is a move of the model and a refusal is said in the banner, translated by its code, never in a modal; that the import dialog's answer arrives at the bottom of the tree; that a file edited elsewhere -- VS Code -- is read again, and the files the tab wrote itself are not; that a project held read-only writes nothing; that what is shared with another document shows where the other copy changed (orange), where both did (red) and where the engineer chose to ignore it (grey), and is imported between the tags only; and that the project's layout template («template de forme», which replaced the style on 06.10.2026) applied from the «Projet» tab makes the tab compile its page again -- the tab's own checks being tests/test_project_tab.py's --, and that a style is still chosen at `woodcore-cli new --style`.

**No Typst code is ever shown**: the tab has no code editor and no highlighter, which one check holds.

Built off-screen, and every modal a check would meet is replaced first (`ask_section`, `ask_group`, `ask_rename`, `ask_import`, `ask_confirm`, `ask_overwrite`, `ask_choice` are methods of the tab for that reason): a modal off-screen never comes back. Most checks work on a **light stand-in for the window** (`FakeApp`) and on a copy of one project made once by `project_template.create`, so that a check that writes puts nothing back; the few that need the window's own navigation build the real one. Nothing compiles unless a check asks it to -- the checks that do skip where Typst is not installed -- and a preview is compiled into a folder of the test's own, never into Woodcore's cache.
"""

import contextlib
import os
import re
import shutil
import sys
import time
from pathlib import Path

import conftest
from conftest import ROOT, Skip

import project

TOOLS = ROOT / "calc" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
_STATE = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdfWidgets  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdfWidgets is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _pristine():
    """A project in three documents, French, made once for the file: every check that writes works on a copy of it."""
    if "pristine" not in _STATE:
        import project_template
        base = conftest.tmpdir("structure_tab_pristine")
        here = project_template.create(base / "Halle", "Halle", document_language="fr", report_language="fr", author="L. Exempel")
        # the documents are in step from the day they are made: a baseline is what tells a change here from a change there (calc/sync.py settles it at the first look)
        import sync
        for mode in ("cu", "bp"):
            sync.status(here, mode)
        _STATE["pristine"] = here
    return _STATE["pristine"]


def _copy(name):
    """A copy of that project of this check's own, loaded."""
    source = _pristine()
    target = conftest.tmpdir(name) / "Halle"
    shutil.copytree(source.root, target)
    return project.Project.load(target / "Halle.woodcore")


ASKS = ("ask_section", "ask_group", "ask_rename", "ask_import", "ask_confirm", "ask_choice", "ask_template", "ask_share", "tell")


def _unexpected(name):
    def ask(*args, **kwargs):
        raise AssertionError(f"the tab asked a question ({name}) that this check did not expect")
    return ask


class FakeApp:
    """The window as far as the tab asks anything of it: its language, the document it shows, whether another window holds the project, a status line, and the one message a refused write says."""

    def __init__(self, lang="fr", mode="cu", read_only=False):
        from PySide6.QtGui import QFont
        self.lang, self.mode, self.read_only = lang, mode, read_only
        self.views = {}
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.statuses = []
        self.refused = 0

    def t(self, key, **values):
        import structure_words
        text = structure_words.STRINGS[self.lang][key]
        return text.format(**values) if values else text

    def current_document(self):
        return self.mode

    def set_status(self, text):
        self.statuses.append(text)

    def refuse_read_only(self):
        self.refused += 1


@contextlib.contextmanager
def _open(name, mode="cu", lang="fr", read_only=False, here=None):
    """A tab on a copy of the project, built the way the window builds it -- `yield tab, app, here` -- and let go of afterwards. `woodcore_gui` is imported first: it is what guards the tab's writers against a project held read-only."""
    _qt()
    import structure_tab
    import woodcore_gui  # noqa: F401
    here = here or _copy(name)
    app = FakeApp(lang, mode, read_only)
    with project.using(here):
        tab = structure_tab.StructureTab(app)
        for name in ASKS:       # a modal off-screen never comes back: a check that expects a question answers it first
            setattr(tab, name, _unexpected(name))
        try:
            yield tab, app, here
        finally:
            tab.stop_watching()
            tab.pane.stop()
            tab.deleteLater()


@contextlib.contextmanager
def _patched(obj, **values):
    missing = object()
    saved = {name: getattr(obj, name, missing) for name in values}
    for name, value in values.items():
        setattr(obj, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is missing:
                delattr(obj, name)
            else:
                setattr(obj, name, value)


def _pump(seconds=0.0):
    """The event loop run -- once where no time is given: what a timer of zero, which is how the tab defers a write out of the tree's own signal, needs."""
    from PySide6.QtCore import QEventLoop
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    end = time.monotonic() + seconds
    while True:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)
        if time.monotonic() >= end:
            return
        time.sleep(0.01)


def _wait(condition, timeout=120, what="the pane"):
    end = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > end:
            raise AssertionError(f"{what}: nothing after {timeout} s")
        _pump(0.05)


def _choose(tab, *ids):
    """The rows chosen, the way a click on them does: the tree's selection set and the tab told, which reads the right pane and asks for the page."""
    tab.tree.select_ids(list(ids), ids[0] if ids else None)
    for node_id in ids:
        tab.tree.reveal(node_id)
    tab.on_selection_changed()


def _clear(tab):
    tab.tree.select_ids([])
    tab.on_selection_changed()


def _section_path(here, mode, file_id):
    return here.document_dir(mode) / "Sections" / f"{file_id}.typ"


def _bytes(path):
    return path.read_bytes() if path.exists() else None


def _text(path):
    return path.read_bytes().decode("utf-8")


def _lines(text):
    import structure_tab
    return structure_tab._lines(text)


def _outside(text, object_id):
    """`text` with the object `object_id` -- both its tags and everything between -- cut out: what a write to that object must leave exactly as it was."""
    import typst_objects
    found = typst_objects.find(text, object_id)
    lines = _lines(text)
    return "".join(lines[:found.start] + lines[found.end + 1:])


def _body(text, object_id):
    import typst_objects
    return typst_objects.find(text, object_id).written


def _rows(body):
    """The rows of a raw table's body (calc/typst_raw_table.py): its lines of four spaces and a cell's bracket."""
    return len(re.findall(r"^    \[", body, re.M))


def _object_ids(text):
    import typst_objects
    return [o.id for o in typst_objects.parse(text)] if hasattr(typst_objects, "parse") else re.findall(r"^// woodcore:object \S+ (\S+)", text, re.M)


def _sections(here, mode):
    """The ids of the sections of `mode`, flat, in document order: a file node's id is the section's."""
    import structure
    return [n.id for n in structure.flatten(structure.tree(here, mode)) if n.kind == "file"]


def _children_of(here, mode, group_id):
    import structure
    found = structure.find(structure.read(here.structure_file(mode)), group_id)
    return [entry["id"] for entry in found[0].get("children", [])]


def _top_level(here, mode):
    import structure
    return [entry["id"] for entry in structure.read(here.structure_file(mode))["sections"]]


def _banner(tab):
    """What the banner over the tree says now, "" while it is hidden."""
    return tab.banner.text() if not tab.banner.isHidden() else ""


# --- the tab in the window ----------------------------------------------------------------------

def test_the_tab_is_the_only_document_tab_and_first_after_projet_in_the_navigation_and_the_sections_tab_is_gone():
    """Second in the navigation since issue #87, under the «Projet» tab, the one the window opens on and every change of document brings forward."""
    _qt()
    import chrome
    import project_tab
    import structure_tab
    import woodcore_gui
    assert woodcore_gui.TABS[0][0] == "tab_project" and woodcore_gui.TABS[0][1] is project_tab.ProjectTab
    assert woodcore_gui.TABS[1][0] == "tab_structure" and woodcore_gui.TABS[1][1] is structure_tab.StructureTab
    title, members = woodcore_gui.NAV_GROUPS[0]
    assert title == "nav_document_group" and members == ("tab_project", "tab_structure"), woodcore_gui.NAV_GROUPS[0]
    keys = [key for key, _factory in woodcore_gui.TABS]
    assert "tab_sections" not in keys
    named = set(keys) | {m for _t, group in woodcore_gui.NAV_GROUPS for m in group}
    for mode, tabs in woodcore_gui.MODE_TABS.items():
        named |= set(tabs)
        assert tabs[:2] == ("tab_project", "tab_structure"), mode
    named |= set(woodcore_gui.MODE_BOUND)
    assert "tab_sections" not in named, "a module nothing builds is named in the navigation or a document's modules"
    assert "tab_structure" in chrome.ICONS and "tab_sections" not in chrome.ICONS and "badge_link" in chrome.ICONS
    assert "tab_structure" in woodcore_gui.MODE_BOUND and "tab_sections" not in woodcore_gui.MODE_BOUND
    assert not (TOOLS / "sections_tab.py").exists() and not (ROOT / "tests" / "test_sections_tab.py").exists()
    for lang in ("fr", "de", "en"):
        strings = woodcore_gui.STRINGS[lang]
        assert strings["tab_structure"] and strings["nav_document_group"] and strings["nav_document_group"] != strings["nav_document"], lang
        assert "tab_sections" not in strings
    # every writer of the tab is among those the window guards while a project is held read-only
    defined = {k: v for c in reversed(woodcore_gui.own_classes(structure_tab.StructureTab)) for k, v in vars(c).items()}  # the class and its mixins (issue #30)
    own = [n for n in woodcore_gui.WRITERS if n in defined]
    for expected in ("write_enabled", "write_title", "write_add_section", "write_add_group", "write_remove", "write_rename", "write_move",
                     "write_object", "write_node_state", "write_heading_line", "write_add_object", "write_remove_object", "write_tag",
                     "write_import", "write_sync_import", "write_sync_flag"):
        assert expected in woodcore_gui.WRITERS and expected in own, expected
        assert getattr(defined[expected], "__wrapped__", None) is not None, f"{expected} is not guarded"


def test_the_window_shows_the_tab_second_for_each_document_and_writes_what_a_pane_held_before_another_document_is_shown():
    _qt()
    import structure
    import structure_tab
    import woodcore_gui
    here = _copy("structure_tab_window")
    with project.using(here):
        window = woodcore_gui.MainWindow()
        try:
            window.lang = "fr"
            window.mode = "rs"
            window.rebuild()
            tab = next(t for t in window.tabs if isinstance(t, structure_tab.StructureTab))
            select = window.nav.mode_select
            for mode in project.MODES:
                select.setCurrentIndex(select.findData(mode))
                keys = [woodcore_gui.TABS[index][0] for index in window.nav.order()]
                assert keys[:2] == ["tab_project", "tab_structure"] and "tab_sections" not in keys, (mode, keys)
                assert window.tab_widget.currentIndex() == window.project_index(), "another document did not bring «Projet» forward"
                tab = next(t for t in window.tabs if isinstance(t, structure_tab.StructureTab))
                assert tab.mode() == mode
                assert tab.tree.ids() == [n.id for n in structure.flatten(structure.tree(here, mode))] and tab.tree.ids(), mode
                assert window.t("st_heading", document=tab.document_name()) == tab.title.text()
            select.setCurrentIndex(select.findData("cu"))
            tab = next(t for t in window.tabs if isinstance(t, structure_tab.StructureTab))
            window.tab_widget.setCurrentWidget(tab)
            node = next(n for n in structure.flatten(tab.nodes) if n.kind == "object" and n.object_type == "text" and n.parent == "purpose")
            _choose(tab, node.id)
            pane = tab.host.pane()
            pane.edit.setPlainText("Un texte tapé, pas encore écrit.")
            assert "Un texte tapé" not in _text(_section_path(here, "cu", "purpose")), "a paragraph is written after a moment, not at each key"
            select.setCurrentIndex(select.findData("bp"))      # another document shown: what the pane held is written first (MODE_BOUND)
            assert "Un texte tapé, pas encore écrit." in _text(_section_path(here, "cu", "purpose"))
            tab = next(t for t in window.tabs if isinstance(t, structure_tab.StructureTab))
            assert tab.mode() == "bp" and tab.tree.ids() == [n.id for n in structure.flatten(structure.tree(here, "bp"))]
        finally:
            conftest.dispose(window)
def test_it_has_nothing_unsaved_to_mark_and_compiles_nothing_before_it_is_shown():
    """It writes at once, so it has no `dirty` -- the dot of unsaved changes is for the editors -- and the window, which builds every tab when it opens, does not pay a compile for one the engineer has not looked at."""
    with _open("structure_tab_idle") as (tab, app, here):
        assert not hasattr(tab, "dirty")
        assert tab.confirm_leave() is True
        _pump(0.3)
        assert not tab.pane_loaded and not tab.pane.showing and not tab.pane.is_pending() and tab.pane.process is None
        assert tab.tree.ids(), "the tree is read when the tab is built: it is cheap, and the compile is what waits"
        assert tab.watcher is None, "nothing is watched before the tab is shown: a watch holds a directory on Windows"
        assert tab.request_preview() is None and not tab.pane.is_pending(), "no page is asked for before the tab has been given its document"


# --- the tree ---------------------------------------------------------------------------------------

def test_the_tree_shows_chapters_sections_and_objects_each_with_an_icon_a_box_and_its_marks():
    _qt()
    import chrome
    import structure
    import structure_tree
    from PySide6.QtCore import Qt
    with _open("structure_tab_tree") as (tab, app, here):
        nodes = structure.tree(here, "cu")
        flat = structure.flatten(nodes)
        assert tab.tree.ids() == [n.id for n in flat]
        kinds = {n.kind for n in flat}
        assert {"group", "file", "object"} <= kinds, kinds
        types = {n.object_type for n in flat if n.kind == "object"}
        assert {"heading", "text", "table"} <= types, types   # the parametric objects of a document written in raw Typst since the spec 2026-10-21-commandes-typst-refonte (REQ-019)
        group = next(n for n in flat if n.kind == "group")
        assert tab.tree.row(group.id).parent() is None and tab.tree.row(group.id).font(0).bold()
        for node in flat:
            row = tab.tree.row(node.id)
            assert not row.icon(structure_tree.TITLE).isNull(), f"{node.id} has no icon"
            assert structure_tree.icon_key(node) in chrome.ICONS
            boxed = bool(row.flags() & Qt.ItemFlag.ItemIsUserCheckable)
            assert boxed == (node.kind in ("file", "group")), f"{node.id}: only a chapter and a section carry a box"
            if node.kind in ("file", "group"):
                assert (row.checkState(structure_tree.TITLE).value == 2) == bool(node.enabled), node.id
            if node.kind == "object":
                assert node.parent in tab.tree.items and tab.tree.row(node.id).parent() is tab.tree.row(node.parent)
            assert not row.text(structure_tree.TYP), f"{node.id}: the .typ mark is the report's alone"
            assert (not row.icon(structure_tree.LINK).isNull()) == bool(node.shared_with), node.id
        # an object is indented by its level under its file, and says where it is stored
        title = next(n for n in flat if n.kind == "object" and n.object_type == "heading" and n.parent == "purpose")
        text = next(n for n in flat if n.kind == "object" and n.object_type == "text" and n.parent == "purpose")
        assert tab.tree.row(text.id).data(0, structure_tree.INDENT_ROLE) > tab.tree.row(title.id).data(0, structure_tree.INDENT_ROLE) >= 0
        tip = tab.tree.row(text.id).toolTip(0)
        assert "purpose.typ" in tip and str(text.span[0] + 1) in tip, tip
        # a shared section says with which document, on its link mark
        shared = next(n for n in flat if n.kind == "file" and n.shared_with)
        assert "Base de projet" in tab.tree.row(shared.id).toolTip(structure_tree.LINK)
        # a row is a short label: the title as the words Typst prints, never the markup
        assert all("#" not in tab.tree.row(n.id).text(0) and "woodcore:" not in tab.tree.row(n.id).text(0) for n in flat)


def test_each_document_has_its_own_tree_and_the_report_keeps_its_headings_under_files_that_are_not_tagged():
    import structure
    with _open("structure_tab_modes") as (tab, app, here):
        for mode in ("cu", "bp", "rs"):
            app.mode = mode
            tab.on_mode()
            assert tab.mode() == mode and tab.title.text() == app.t("st_heading", document=tab.document_name())
            expected = structure.flatten(structure.tree(here, mode))
            assert tab.tree.ids() == [n.id for n in expected] and expected, mode
            if mode == "rs":
                files = [n for n in expected if n.kind == "file"]
                assert files and not [n for n in expected if n.kind == "group"], "the report has no chapters"
                # made from its own content template since 06.10.2026, the report's sections carry their tags; a file that carries none shows its headings (test_a_file_with_text_no_tag_wraps_…)
                assert [n for n in expected if n.kind in ("object", "heading")], "the report's sections show neither their objects nor their headings"
            else:
                assert [n for n in expected if n.kind == "group"] and [n for n in expected if n.kind == "object"], mode


def test_the_level_buttons_open_the_tree_and_a_row_not_printed_is_greyed_and_one_with_a_problem_says_what():
    _qt()
    import structure
    import structure_tree
    from PySide6.QtGui import QColor
    import theme
    with _open("structure_tab_levels") as (tab, app, here):
        flat = structure.flatten(tab.nodes)
        group = next(n for n in flat if n.kind == "group")
        file = next(n for n in group.children if n.kind == "file")
        tab.level_buttons[1].click()
        assert not tab.tree.row(group.id).isExpanded()
        tab.level_buttons[2].click()
        assert tab.tree.row(group.id).isExpanded() and not tab.tree.row(file.id).isExpanded()
        tab.level_buttons[3].click()
        assert tab.tree.row(file.id).isExpanded()
        tab.level_buttons[None].click()
        assert all(row.isExpanded() for row in tab.tree.items.values() if row.childCount())
        # a section switched off is greyed with its objects, and says why on its tooltip
        assert tab.write_enabled(file.id, False) is True
        muted = QColor(theme.colour("muted")).name()
        row = tab.tree.row(file.id)
        assert row.foreground(structure_tree.TITLE).color().name() == muted
        child = next(c for c in tab.tree.node(file.id).children if c.kind == "object")
        assert tab.tree.row(child.id).foreground(structure_tree.TITLE).color().name() == muted
        assert app.t("st_tip_off") in row.toolTip(structure_tree.TITLE)
        assert app.t("st_tip_off") in tab.tree.row(child.id).toolTip(structure_tree.TITLE), "an object has no state of its own: its section's is what it says"
        # a file whose tags cannot be read is set in the warning colour, and its tooltip says what is wrong
        path = _section_path(here, "cu", "purpose")
        path.write_bytes(_bytes(path) + b"\n// woodcore:object text unclosed\nUn texte jamais ferme.\n")
        tab.reload()
        node = tab.tree.node("purpose")
        assert node.problems, "a tag that is never closed is a problem of the file"
        warning = QColor(theme.colour("warning")).name()
        assert tab.tree.row("purpose").foreground(structure_tree.TITLE).color().name() == warning
        assert node.problems[0] in tab.tree.row("purpose").toolTip(structure_tree.TITLE)


def test_no_typst_code_is_ever_shown_and_the_tab_has_no_code_editor():
    """The engineer edits code in VS Code. Every kind of pane is loaded and nothing the tab or its panes show is a code box with syntax colours."""
    _qt()
    import structure
    from PySide6.QtGui import QSyntaxHighlighter
    from PySide6.QtWidgets import QLabel, QPlainTextEdit, QTextEdit
    with _open("structure_tab_nocode") as (tab, app, here):
        seen = set()
        for node in structure.flatten(tab.nodes):
            if node.kind == "heading" or (node.kind == "object" and node.object_type in seen):
                continue
            if node.kind == "object":
                seen.add(node.object_type)
            _choose(tab, node.id)
            for edit in tab.findChildren(QPlainTextEdit) + tab.findChildren(QTextEdit):
                assert not edit.document().findChildren(QSyntaxHighlighter), f"{node.id}: a highlighted editor ({type(edit).__name__})"
        assert len(seen) >= 3, seen
        source = conftest.module_source(TOOLS / "structure_tab.py") + (TOOLS / "structure_tree.py").read_text(encoding="utf-8") + (TOOLS / "import_dialog.py").read_text(encoding="utf-8")
        assert "TypstHighlighter" not in source and "CodeField" not in source and "typst_html" not in source
        texts = " ".join(label.text() for label in tab.findChildren(QLabel))
        assert "woodcore:object" not in texts and "#import" not in texts




def test_the_tree_widget_says_what_the_user_did_and_nothing_a_fill_does():
    """`StructureTree` reads no file and knows no document, and says three things -- a box ticked, the rows chosen, a drop -- and only when a user did them: filling it, selecting a row in code and opening its rows say nothing, so that a tab which writes on `toggled` never writes for its own refilling."""
    _qt()
    import structure
    import structure_tree
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QAbstractItemView
    here = _copy("structure_tab_widget")
    nodes = structure.tree(here, "cu")
    tree = structure_tree.StructureTree()
    said = {"toggled": [], "chosen": [], "dropped": []}
    tree.toggled.connect(lambda node_id, on: said["toggled"].append((node_id, on)))
    tree.selectionIdsChanged.connect(said["chosen"].append)
    tree.dropped.connect(lambda ids, target, where: said["dropped"].append((ids, target, where)))
    tree.resize(520, 1400)
    tree.show()
    try:
        tree.set_nodes(nodes, state={"selected": "purpose", "expanded": ["introduction"]})
        _pump()
        assert said == {"toggled": [], "chosen": [], "dropped": []}, "filling the tree said something"
        assert tree.selected_id() == "purpose" and tree.row("introduction").isExpanded()
        assert tree.select("scope-and-limits") and tree.select("nowhere") is False and said["chosen"] == [], "a row selected in code was said to be chosen"
        # a box ticked is said once, with the state it now has
        tree.row("purpose").setCheckState(0, Qt.CheckState.Unchecked)
        assert said["toggled"] == [("purpose", False)], said
        tree.set_nodes(nodes, state=tree.state())
        assert said["toggled"] == [("purpose", False)], "a tree filled again with a node's own state said it was toggled"
        assert tree.row("purpose").checkState(0) == Qt.CheckState.Checked, "a fill did not put the box back where the node says it is"
        # rows chosen by the user's hand -- a click, then Ctrl and Shift as in an explorer -- are said in document order
        tree.expandAll()
        tree.scrollToTop()
        center = lambda node_id: tree.visualItemRect(tree.row(node_id)).center()   # noqa: E731
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, center("purpose"))
        assert said["chosen"][-1] == ["purpose"], said["chosen"]
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, center("future-extension"))
        assert said["chosen"][-1] == ["purpose", "future-extension"], said["chosen"]
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, center("purpose"))
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier, center("scope-and-limits"))
        range_ = said["chosen"][-1]
        assert range_[0] == "purpose" and range_[-1] == "scope-and-limits" and len(range_) > 2, range_
        assert tree.selected_ids() == range_ and range_ == [i for i in tree.ids() if i in set(range_)], "the ids chosen are in document order"
        # every row is found by its node id, in document order; a level opens the rows below it
        assert tree.ids() == [n.id for n in structure.flatten(nodes)] and tree.node("purpose").parent == "introduction"
        tree.expand_to(1)
        assert not tree.row("introduction").isExpanded()
        tree.expand_to(2)
        assert tree.row("introduction").isExpanded() and not tree.row("purpose").isExpanded()
        assert structure_tree.display_title(tree.node("purpose")) == structure.plain_title(tree.node("purpose").title)

        # a drop says where it fell and changes nothing: the rows are never moved by Qt, the tab asks the model
        class FakeDrop:
            def __init__(self, point, source):
                self.point, self.src, self.action, self.accepted = point, source, None, True

            def source(self):
                return self.src

            def position(self):
                return QPointF(self.point)

            def setDropAction(self, action):
                self.action = action

            def ignore(self):
                self.accepted = False

        tree.select_ids(["scope-and-limits"])
        order = list(tree.ids())
        for indicator, where in ((QAbstractItemView.DropIndicatorPosition.AboveItem, "above"), (QAbstractItemView.DropIndicatorPosition.BelowItem, "below"),
                                 (QAbstractItemView.DropIndicatorPosition.OnItem, "on"), (QAbstractItemView.DropIndicatorPosition.OnViewport, "end")):
            tree.dropIndicatorPosition = lambda indicator=indicator: indicator
            event = FakeDrop(center("purpose"), tree)
            tree.dropEvent(event)
            assert said["dropped"][-1] == (["scope-and-limits"], "purpose", where), said["dropped"][-1]
            assert event.action == Qt.DropAction.IgnoreAction and not event.accepted
        assert tree.ids() == order, "Qt moved a row"
        count = len(said["dropped"])
        tree.dropEvent(FakeDrop(center("purpose"), None))       # a drop from elsewhere is none of the tree's
        assert len(said["dropped"]) == count
        del tree.dropIndicatorPosition
    finally:
        tree.close()


# --- the right pane writes between the tags and nowhere else --------------------------------------------

def test_a_table_chosen_loads_its_pane_and_a_row_added_is_written_between_its_tags_only_and_the_pane_is_not_reloaded():
    with _open("structure_tab_table") as (tab, app, here):
        path = _section_path(here, "cu", "intended-use")
        before = _text(path)
        rows_before = _rows(_body(before, "intended-use-table"))
        assert rows_before >= 3
        _choose(tab, "intended-use/intended-use-table")
        assert tab.host.kind == "table" and tab.subject["kind"] == "table" and tab.subject["object"] == "intended-use-table"
        pane = tab.host.pane()
        assert pane.row_list.count() == rows_before
        row, loads = tab.tree.row("intended-use/intended-use-table"), []
        original = pane.load
        pane.load = lambda *a, **k: loads.append(a) or original(*a, **k)
        pane.add_row()
        after = _text(path)
        assert after != before and _outside(after, "intended-use-table") == _outside(before, "intended-use-table"), "the bytes outside the object's tags changed"
        assert _rows(_body(after, "intended-use-table")) == rows_before + 1
        assert loads == [], "the pane was loaded again with what it had just written"
        assert pane.row_list.count() == rows_before + 1 and tab.host.pane() is pane
        assert tab.tree.row("intended-use/intended-use-table") is row and tab.tree.selected_ids() == ["intended-use/intended-use-table"], "the tree was refilled under a pane"
        assert tab.subject["body"] == _body(after, "intended-use-table") and tab.failure is None and not _banner(tab)
        assert tab.signature == tab.disk_signature(), "what the tab wrote itself is what it read last"
        # a second edit in a row is written against the first
        pane.add_row()
        assert _rows(_body(_text(path), "intended-use-table")) == rows_before + 2 and _outside(_text(path), "intended-use-table") == _outside(before, "intended-use-table")


def test_a_paragraph_and_a_heading_are_edited_in_place_and_the_tree_label_follows():
    with _open("structure_tab_text") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        before = _text(path)
        _choose(tab, "purpose/p2")
        assert tab.host.kind == "text"
        pane = tab.host.pane()
        pane.edit.setPlainText("Un paragraphe réécrit dans le volet de droite.")
        assert _text(path) == before, "a paragraph is written after a moment and not at each key"
        pane.flush()
        after = _text(path)
        assert "Un paragraphe réécrit dans le volet de droite." in _body(after, "p2") and _outside(after, "p2") == _outside(before, "p2")
        assert tab.tree.selected_ids() == ["purpose/p2"] and tab.host.pane() is pane
        # a heading: its text rewritten, the label of its row following in place
        row = tab.tree.row("purpose/title")
        _choose(tab, "purpose/title")
        assert tab.host.kind == "heading"
        pane = tab.host.pane()
        pane.title_edit.textEdited.emit("Objet réécrit")
        pane.flush()
        again = _text(path)
        assert _body(again, "title") == "== Objet réécrit" and _outside(again, "title") == _outside(after, "title")
        assert tab.tree.row("purpose/title") is row and row.text(0) == "Objet réécrit", row.text(0)


def test_an_object_written_by_hand_asks_first_naming_what_is_lost_and_nothing_is_written_without_a_yes():
    """A parametric object written otherwise than Woodcore writes it -- the list of the norms, the one left since the spec 2026-10-21-commandes-typst-refonte (REQ-019); a raw table is never rewritten but where it is edited -- is asked about before it is written."""
    import typst_objects
    with _open("structure_tab_hand") as (tab, app, here):
        path = _section_path(here, "cu", "norms")
        text = _text(path)
        hand = text.replace('    "SIA 260",\n', '    "SIA 260", // a note written in VS Code\n', 1)
        path.write_bytes(hand.encode("utf-8"))
        tab.reload()
        assert typst_objects.find(hand, "norms-selection").state == "hand_edited"
        assert "hand" in tab.tree.row("norms/norms-selection").toolTip(0).lower() or app.t("st_tip_hand") in tab.tree.row("norms/norms-selection").toolTip(0)
        keys = len(typst_objects.find(hand, "norms-selection").call.args["keys"])
        asked = []
        _choose(tab, "norms/norms-selection")
        pane = tab.host.pane()
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or False):
            pane.line_add.click()
        assert len(asked) == 1 and "norms-selection" in asked[0] and "a note written in VS Code" in asked[0], asked
        assert _bytes(path) == hand.encode("utf-8"), "a no wrote something"
        assert len(tab.host.pane().current().keys) == keys, "what was typed is given up: the pane shows the file again"
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or True):
            tab.host.pane().line_add.click()
            assert len(asked) == 2
            written = _text(path)
            assert "a note written in VS Code" not in written and len(typst_objects.find(written, "norms-selection").call.args["keys"]) == keys + 1
            assert _outside(written, "norms-selection") == _outside(hand, "norms-selection")
            tab.host.pane().line_add.click()
            assert len(asked) == 2, "an object the engineer said yes to is asked about once"
        # an object that cannot be read at all says so in its own words
        found = type("Found", (), {"state": "unreadable", "id": "x"})()
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or False):
            tab.ask_overwrite(found)
        assert app.t("st_overwrite_unreadable") in asked[-1]


def test_a_file_changed_under_a_pane_refuses_the_write_and_the_pane_reads_it_again():
    with _open("structure_tab_changed") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        _choose(tab, "purpose/p2")
        pane = tab.host.pane()
        text = _text(path)
        external = text.replace(_body(text, "p2"), "Un texte écrit entre-temps dans VS Code.")
        path.write_bytes(external.encode("utf-8"))
        pane.edit.setPlainText("Ce que le volet voulait écrire.")
        pane.flush()
        assert _bytes(path) == external.encode("utf-8"), "a pane overwrote a file that had changed under it"
        assert _banner(tab) == app.t("st_changed_outside") and not tab.banner.isHidden()
        assert tab.host.pane().edit.toPlainText() == "Un texte écrit entre-temps dans VS Code.", "the pane did not read the file again"
        # the next edit, of what the pane now shows, is written
        tab.host.pane().edit.setPlainText("Écrit depuis le volet après relecture.")
        tab.host.pane().flush()
        assert "Écrit depuis le volet après relecture." in _text(path) and not _banner(tab)


def test_a_chapter_and_a_section_are_edited_in_their_panes_through_the_model():
    import structure
    with _open("structure_tab_nodes") as (tab, app, here):
        structure_file = here.structure_file("cu")
        _choose(tab, "introduction")
        assert tab.host.kind == "chapter"
        pane = tab.host.pane()
        pane.title_edits["fr"].textEdited.emit("Introduction réécrite")
        pane.flush()
        found = structure.find(structure.read(structure_file), "introduction")[0]
        assert found["title"]["fr"] == "Introduction réécrite" and found["title"]["de"] and found["title"]["en"]
        assert tab.tree.node("introduction").title == "Introduction réécrite" and tab.tree.row("introduction").text(0) == "Introduction réécrite"
        assert tab.host.pane() is pane and tab.tree.selected_ids() == ["introduction"]
        pane.printed_check.setChecked(False)
        assert structure.find(structure.read(structure_file), "introduction")[0].get("enabled") is False
        assert tab.tree.row("introduction").checkState(0).value == 0 and not tab.tree.node("scope-and-limits").active
        # a section: its box in the pane is its box in the tree
        _choose(tab, "purpose")
        assert tab.host.kind == "section"
        pane = tab.host.pane()
        assert pane.printed_check.isChecked() is True
        pane.printed_check.setChecked(False)
        entry = structure.find(structure.read(structure_file), "purpose")[0]
        assert entry.get("enabled") is False and tab.tree.row("purpose").checkState(0).value == 0
        pane.printed_check.setChecked(True)
        assert structure.find(structure.read(structure_file), "purpose")[0].get("enabled", True) is True


def test_a_box_ticked_in_the_tree_is_written_after_the_signal_and_a_write_that_fails_is_said_and_leaves_no_box_ticked_for_nothing():
    _qt()
    import structure
    from PySide6.QtCore import Qt
    with _open("structure_tab_boxes") as (tab, app, here):
        structure_file = here.structure_file("cu")
        before = _bytes(structure_file)
        tab.tree.row("scope-and-limits").setCheckState(0, Qt.CheckState.Unchecked)
        assert _bytes(structure_file) == before, "written from inside the tree's own signal"
        _pump()
        assert structure.find(structure.read(structure_file), "scope-and-limits")[0].get("enabled") is False
        assert tab.tree.row("scope-and-limits").checkState(0).value == 0 and not tab.tree.node("scope-and-limits").enabled
        assert any("Délimitation" in words for words in app.statuses), app.statuses
        # a disk that refuses: the banner says it, and the box is put back where the file says it is
        def refuse(*args, **kwargs):
            raise OSError("disk full")
        with _patched(structure, set_enabled=refuse):
            tab.tree.row("purpose").setCheckState(0, Qt.CheckState.Unchecked)
            _pump()
        assert "disk full" in _banner(tab) and not tab.banner.isHidden()
        assert tab.tree.row("purpose").checkState(0).value == 2, "a box ticked for nothing was left ticked"
        # the next write that works clears the banner
        assert tab.write_enabled("purpose", False) is True and not _banner(tab)


def test_a_structure_that_cannot_be_read_is_said_in_the_banner_and_lists_nothing():
    with _open("structure_tab_broken") as (tab, app, here):
        assert tab.tree.ids()
        here.structure_file("cu").write_text("{ not json", encoding="utf-8")
        tab.reload()
        assert tab.tree.ids() == [] and tab.error and not tab.banner.isHidden()
        assert _banner(tab) == app.t("st_banner_unreadable", error=tab.error)
        tab.request_preview()
        assert not tab.pane.is_pending(), "a compile was asked for a document that cannot be read"




# --- the page of what is chosen ---------------------------------------------------------------------

def _spy_pane(tab):
    """The pane's three ways of being asked for a page replaced by recorders, so that a check sees what the tab asked for without Typst running."""
    calls = {"snippet": [], "document": 0, "request": []}
    tab.pane.request_snippet = lambda here, mode, source, key: calls["snippet"].append((mode, source, key))
    tab.pane.show_document = lambda: calls.__setitem__("document", calls["document"] + 1)
    tab.pane.request = lambda here=None, mode=None: calls["request"].append((here, mode))
    return calls


def test_the_page_asked_for_is_the_snippet_of_what_is_chosen_and_the_whole_document_where_nothing_is():
    import structure_preview
    with _open("structure_tab_preview") as (tab, app, here):
        calls = _spy_pane(tab)
        tab.pane_loaded = True
        _choose(tab, "purpose/p2")
        wanted = structure_preview.build(here, "cu", tab.nodes, ["purpose/p2"])
        assert calls["snippet"] == [("cu", wanted.source, wanted.key)], "the page asked for is not the object's"
        assert tab.preview_label.text() == app.t("st_preview", what=app.t("st_preview_node", title=tab.tree.row("purpose/p2").text(0)))
        # a section, a chapter: each its own snippet, and none is the document
        _choose(tab, "purpose")
        assert calls["snippet"][-1][1] == structure_preview.build(here, "cu", tab.nodes, ["purpose"]).source
        _choose(tab, "introduction")
        chapter = calls["snippet"][-1][1]
        assert chapter == structure_preview.build(here, "cu", tab.nodes, ["introduction"]).source and 'Sections/introduction.typ' in chapter, "a chapter's heading is its own file (06.10.2026)"
        assert calls["document"] == 0 and not calls["request"]
        # several: one after the other, and the label says how many
        _choose(tab, "purpose", "scope-and-limits")
        several = calls["snippet"][-1][1]
        assert several == structure_preview.build(here, "cu", tab.nodes, ["purpose", "scope-and-limits"]).source
        assert tab.preview_label.text() == app.t("st_preview", what=app.t("st_preview_many", count=2))
        assert tab.host.kind is None and tab.subject is None, "several rows chosen have no pane of their own"
        # nothing chosen: the document, and a compile of it where it has no page yet
        count = len(calls["snippet"])
        _clear(tab)
        assert len(calls["snippet"]) == count and calls["document"] == 1 and calls["request"] == [(here, "cu")]
        assert tab.preview_label.text() == app.t("st_preview", what=app.t("st_preview_document"))
        # a section not printed says so, and is shown all the same
        assert tab.write_enabled("purpose", False) is True
        _choose(tab, "purpose")
        assert tab.preview_label.text() == app.t("st_preview", what=app.t("st_preview_not_printed", what=app.t("st_preview_node", title=tab.tree.row("purpose").text(0))))
        assert calls["snippet"][-1][1] == structure_preview.build(here, "cu", tab.nodes, ["purpose"]).source


def test_a_write_asks_for_the_page_again_and_a_project_held_read_only_compiles_nothing():
    with _open("structure_tab_preview_write") as (tab, app, here):
        calls = _spy_pane(tab)
        tab.pane_loaded = True
        _choose(tab, "purpose/p2")
        asked = len(calls["snippet"])
        tab.host.pane().edit.setPlainText("Un autre paragraphe.")
        tab.host.pane().flush()
        assert len(calls["snippet"]) == asked + 1 and "Un autre paragraphe." in calls["snippet"][-1][1], "the page was not asked for again after a write"
        assert tab.compile_button.isEnabled() and app.t("st_compile_tip", document=tab.document_name()) == tab.compile_button.toolTip()
    with _open("structure_tab_preview_ro", read_only=True) as (tab, app, here):
        calls = _spy_pane(tab)
        tab.pane_loaded = True
        _clear(tab)
        tab.request_preview(force=True)
        assert calls["request"] == [], "a project held read-only compiled its document: that writes its record into the project"
        assert not tab.compile_button.isEnabled() and tab.compile_button.toolTip() == app.t("st_read_only")
        tab.compile_now()
        assert calls["request"] == []


def test_what_is_chosen_compiles_to_its_own_page_and_nothing_else():
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    import io
    import structure_preview
    from pypdf import PdfReader

    def words(tab):
        text = " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(open(tab.pane.shown, "rb").read())).pages)
        return re.sub(r"\s+", " ", text.replace("’", "'").replace(" ", " ").replace(" ", " ")).strip()

    with _open("structure_tab_compile") as (tab, app, here):
        tab.pane_loaded = True
        tab.pane.set_document(here, "cu")
        tab.pane.preview_folder = conftest.tmpdir("structure_tab_compile_cache")

        def shown(*ids):
            _choose(tab, *ids)
            snippet = structure_preview.build(here, "cu", tab.nodes, list(ids))
            _wait(lambda: tab.pane.shown_snippet == snippet.key and not tab.pane.is_pending(), what="the snippet of " + ", ".join(ids))
            assert tab.pane.error_banner.isHidden(), tab.pane.error_banner.text()
            return words(tab)

        paragraph = _body(_text(_section_path(here, "cu", "purpose")), "p2")
        first = " ".join(re.sub(r"[-*_#\[\]]", " ", paragraph).split()[:3])
        got = shown("purpose/p2")
        assert first in got and "Objet de la convention" not in got and "Délimitation" not in got, got[:300]
        got = shown("purpose")
        assert "Objet de la convention" in got and "Délimitation" not in got and "Explications" not in got, got[:300]
        got = shown("introduction")
        assert "Explications" in got and "Objet de la convention" in got and "Délimitation" in got and "Description générale" not in got, got[:300]
        got = shown("purpose", "scope-and-limits")
        assert "Objet de la convention" in got and "Délimitation" in got and "Explications" not in got
        # a section switched off is not in its chapter's page
        assert tab.write_enabled("scope-and-limits", False) is True
        got = shown("introduction")
        assert "Objet de la convention" in got and "Délimitation" not in got
        # an edit in the right pane is on the next page
        _choose(tab, "purpose/p2")
        tab.host.pane().edit.setPlainText("Un paragraphe entièrement nouveau pour la page.")
        tab.host.pane().flush()
        snippet = structure_preview.build(here, "cu", tab.nodes, ["purpose/p2"])
        _wait(lambda: tab.pane.shown_snippet == snippet.key and not tab.pane.is_pending(), what="the page after the edit")
        assert "entièrement nouveau pour la page" in words(tab)


def test_a_snippet_that_does_not_compile_says_typst_s_own_words_in_the_pane_and_points_at_it_in_the_status_line():
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    with _open("structure_tab_compile_fail") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        path.write_bytes(_bytes(path) + b"\n#nicht-definiert-xyz()\n")
        tab.reload()
        tab.pane_loaded = True
        tab.pane.set_document(here, "cu")
        tab.pane.preview_folder = conftest.tmpdir("structure_tab_compile_fail_cache")
        _choose(tab, "purpose")
        _wait(lambda: not tab.pane.error_banner.isHidden() and not tab.pane.is_pending(), what="the failing snippet")
        assert "nicht-definiert-xyz" in tab.pane.error_banner.text()
        assert app.statuses[-1] == app.t("st_compile_failed")
        assert tab.banner.isHidden(), "the tab's banner is for refusals; Typst's own message is the pane's"


# --- moving: drag and drop ------------------------------------------------------------------------------

def test_sections_and_chapters_dropped_move_in_the_model_and_no_file_moves():
    import structure
    with _open("structure_tab_drop_sections") as (tab, app, here):
        files = lambda: sorted(p.name for p in (here.document_dir("cu") / "Sections").glob("*.typ"))   # noqa: E731
        before_files = files()
        before = {name: _bytes(here.document_dir("cu") / "Sections" / name) for name in before_files}
        assert _children_of(here, "cu", "introduction") == ["purpose", "scope-and-limits"]
        # above a section: its sibling, before it
        assert tab.drop_nodes(["scope-and-limits"], "purpose", "above") is True
        assert _children_of(here, "cu", "introduction") == ["scope-and-limits", "purpose"]
        assert tab.tree.selected_ids() == ["scope-and-limits"] and not _banner(tab), "what moved is chosen, and nothing is refused"
        assert [tab.tree.node(i).id for i in tab.tree.ids() if tab.tree.node(i).kind == "file"][:2] == ["scope-and-limits", "purpose"]
        # below a section
        assert tab.drop_nodes(["scope-and-limits"], "purpose", "below") is True
        assert _children_of(here, "cu", "introduction") == ["purpose", "scope-and-limits"]
        # on a chapter: at its end
        assert tab.drop_nodes(["purpose"], "use-objectives", "on") is True
        assert _children_of(here, "cu", "use-objectives")[-1] == "purpose" and _children_of(here, "cu", "introduction") == ["scope-and-limits"]
        # on an object or a heading: after its section, as its sibling
        assert tab.drop_nodes(["purpose"], "scope-and-limits/title", "above") is True
        assert _children_of(here, "cu", "introduction") == ["scope-and-limits", "purpose"]
        # a chapter above a chapter; a chapter dragged with a section of its own moves once, and the section stays in it
        top = _top_level(here, "cu")
        assert tab.drop_nodes(["annexes"], "introduction", "above") is True
        assert _top_level(here, "cu")[0] == "annexes" and len(_top_level(here, "cu")) == len(top)
        assert tab.drop_nodes(["introduction", "purpose"], "bases-and-documents", "below") is True
        assert _top_level(here, "cu").index("introduction") == _top_level(here, "cu").index("bases-and-documents") + 1
        assert _children_of(here, "cu", "introduction") == ["scope-and-limits", "purpose"], "a section dragged with its chapter left it"
        # several sections at once land one after the other, in the order given
        assert tab.drop_nodes(["scope-and-limits", "purpose"], "annexes", "on") is True
        assert _children_of(here, "cu", "annexes")[-2:] == ["scope-and-limits", "purpose"]
        # on nothing: at the end of the document
        assert tab.drop_nodes(["annexes"], "", "end") is True
        assert _top_level(here, "cu")[-1] == "annexes"
        assert files() == before_files and all(_bytes(here.document_dir("cu") / "Sections" / n) == before[n] for n in before_files), "a drop rewrote a section's file"
        assert tab.tree.ids() == [n.id for n in structure.flatten(structure.tree(here, "cu"))], "the tree does not show what the model says"


def test_the_reports_sections_are_reordered_among_its_include_lines():
    _qt()
    import structure
    with _open("structure_tab_drop_rs", mode="rs") as (tab, app, here):
        before = _sections(here, "rs")
        assert before[:2] == ["001-einleitung", "002-grundlagen"], before
        assert tab.drop_nodes(["002-grundlagen"], "001-einleitung", "above") is True
        assert _sections(here, "rs")[:2] == ["002-grundlagen", "001-einleitung"]
        assert tab.tree.selected_ids() == ["002-grundlagen"]
        entry = _text(here.document_typ("rs"))
        assert entry.index("002-grundlagen") < entry.index("001-einleitung"), "the include lines were not reordered"
        assert tab.drop_nodes(["001-einleitung"], "", "end") is True and _sections(here, "rs")[-1] == "001-einleitung"
        # a heading of a section that is not tagged is no object: it goes with its file, and refuses to be dragged alone
        heading = next(n.id for n in structure.flatten(tab.nodes) if n.kind == "heading")
        assert tab.drop_nodes([heading], "003-baustoffe", "below") is False
        assert _banner(tab) == app.t("st_drop_untagged")


def test_objects_dropped_move_within_their_file_or_into_another_and_their_bytes_are_kept():
    import typst_objects
    with _open("structure_tab_drop_objects") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        text = _text(path)
        ids = lambda t: [o for o in re.findall(r"^// woodcore:object \S+ (\S+)", t, re.M)]   # noqa: E731
        blocks = lambda t: {i: typst_objects.find(t, i).written for i in ids(t)}   # noqa: E731
        assert ids(text) == ["title", "p1", "p2", "p3", "document-family", "p4"]
        was = blocks(text)
        assert tab.drop_nodes(["purpose/document-family"], "purpose/p1", "above") is True
        text = _text(path)
        assert ids(text) == ["title", "document-family", "p1", "p2", "p3", "p4"] and blocks(text) == was
        assert tab.tree.selected_ids() == ["purpose/document-family"] and not _banner(tab)
        assert tab.drop_nodes(["purpose/document-family"], "purpose/p4", "below") is True
        assert ids(_text(path)) == ["title", "p1", "p2", "p3", "p4", "document-family"] and blocks(_text(path)) == was
        # several: one after the other, in the order given
        assert tab.drop_nodes(["purpose/p1", "purpose/p2"], "purpose/p4", "below") is True
        assert ids(_text(path)) == ["title", "p3", "p4", "p1", "p2", "document-family"] and blocks(_text(path)) == was
        # into another section: dropped on its row, at its end -- and the section it left no longer has it
        other = _section_path(here, "cu", "future-extension")
        other_before = _text(other)
        assert tab.drop_nodes(["purpose/document-family"], "future-extension", "on") is True
        assert ids(_text(other)) == ids(other_before) + ["document-family"] and "document-family" not in ids(_text(path))
        assert blocks(_text(other))["document-family"] == was["document-family"]
        assert _outside(_text(other), "document-family").strip() == other_before.strip(), "the section it went into changed beside the object"
        assert tab.tree.selected_ids() == ["future-extension/document-family"]
        # above an object of another section
        assert tab.drop_nodes(["purpose/p3"], "future-extension/extension-loads", "above") is True
        assert ids(_text(other))[-3:] == ["p3", "extension-loads", "document-family"] or ids(_text(other)).index("p3") < ids(_text(other)).index("extension-loads")


def test_a_drop_refused_is_said_in_the_banner_by_its_code_in_the_window_s_words_and_nothing_moves():
    _qt()
    import structure
    import structure_words
    with _open("structure_tab_drop_refused") as (tab, app, here):
        structure_before = _bytes(here.structure_file("cu"))
        sections_before = {p.name: p.read_bytes() for p in (here.document_dir("cu") / "Sections").glob("*.typ")}

        def unchanged():
            assert _bytes(here.structure_file("cu")) == structure_before
            assert {p.name: p.read_bytes() for p in (here.document_dir("cu") / "Sections").glob("*.typ")} == sections_before
            assert tab.tree.ids() == [n.id for n in structure.flatten(structure.tree(here, "cu"))]

        # a chapter cannot be moved into itself
        assert tab.drop_nodes(["introduction"], "purpose", "above") is False
        banner = _banner(tab)
        assert "introduction" in banner and not re.search(r"[{}]", banner) and banner.split("introduction")[0] in structure_words.STRINGS["fr"]["st_why_cycle"], banner
        french = banner
        unchanged()
        # an object of a larger shared block cannot leave it
        assert tab.drop_nodes(["live-loads/live-loads-table"], "purpose", "on") is False
        assert _banner(tab) == tab.why(type("E", (), {"code": "leaves_shared_block", "values": {"id": "live-loads-table", "shared_id": "live-loads"}})()) and _banner(tab)
        assert "live-loads" in _banner(tab)
        unchanged()
        # objects on a chapter, objects with sections, objects on nothing
        assert tab.drop_nodes(["purpose/p1"], "introduction", "on") is False and _banner(tab) == app.t("st_drop_object_on_group")
        assert tab.drop_nodes(["purpose", "purpose/p1"], "future-extension", "below") is False and _banner(tab) == app.t("st_drop_mixed")
        assert tab.drop_nodes(["purpose/p1"], "", "end") is False and _banner(tab) == app.t("st_drop_nowhere")
        unchanged()
        # the same refusal in another language is another sentence
        assert _banner(tab) != ""
    for lang in ("de", "en"):
        with _open("structure_tab_drop_refused_" + lang, lang=lang) as (tab, app, here):
            assert tab.drop_nodes(["introduction"], "purpose", "above") is False
            assert "introduction" in _banner(tab) and not re.search(r"[{}]", _banner(tab)) and _banner(tab) != french
            assert _banner(tab).startswith(structure_words.STRINGS[lang]["st_why_cycle"].split("{")[0]), _banner(tab)
    # a banner is never a modal: nothing here could answer one
    with _open("structure_tab_drop_banner") as (tab, app, here):
        from PySide6.QtWidgets import QMessageBox
        def modal(*a, **k):
            raise AssertionError("a refusal opened a message box")
        with _patched(QMessageBox, question=staticmethod(modal), warning=staticmethod(modal), critical=staticmethod(modal), information=staticmethod(modal)):
            assert tab.drop_nodes(["introduction"], "purpose", "above") is False
            assert tab.write_rename("scope-and-limits", "x") is False and not tab.banner.isHidden()


def test_a_drop_is_deferred_out_of_the_trees_signal_and_the_model_moves_after_it():
    with _open("structure_tab_drop_deferred") as (tab, app, here):
        before = _children_of(here, "cu", "introduction")
        tab.tree.dropped.emit(["scope-and-limits"], "purpose", "above")
        assert tab.drops == [(["scope-and-limits"], "purpose", "above")]
        assert _children_of(here, "cu", "introduction") == before, "the model moved from inside the tree's own signal"
        _pump()
        assert _children_of(here, "cu", "introduction") == ["scope-and-limits", "purpose"]
        assert tab.tree.selected_ids() == ["scope-and-limits"]
        # rows chosen by the user are read by the tab from the signal: the right pane shows the object
        tab.tree.select_ids(["purpose/p2"])
        tab.tree.selectionIdsChanged.emit(["purpose/p2"])
        assert tab.host.kind == "text" and tab.subject["id"] == "purpose/p2" and not tab._in_tree_signal




# --- the buttons: add, remove, rename, tag ---------------------------------------------------------------------

def test_a_section_added_goes_after_the_one_chosen_inside_the_chapter_chosen_or_at_the_end_and_a_refusal_is_said():
    import structure
    import typst_objects
    with _open("structure_tab_add_section") as (tab, app, here):
        asked = []
        answer = {"value": ("my-new-section", "Ma nouvelle section")}
        with _patched(tab, ask_section=lambda where: asked.append(where) or answer["value"]):
            _choose(tab, "purpose")
            tab.on_add_section()
            assert _children_of(here, "cu", "introduction") == ["purpose", "my-new-section", "scope-and-limits"]
            assert asked[-1] == app.t("st_where_after", title=tab.tree.row("purpose").text(0)) or "Objet" in asked[-1]
            created = _section_path(here, "cu", "my-new-section")
            assert created.is_file() and typst_objects.find(_text(created), "title") is not None or created.stat().st_size > 0
            assert tab.tree.selected_ids() == ["my-new-section"] and tab.subject["kind"] == "section"
            assert not _banner(tab) and any("my-new-section" in words for words in app.statuses)
            # inside the chapter chosen, at its end
            answer["value"] = ("second-section", "Seconde section")
            _choose(tab, "use-objectives")
            tab.on_add_section()
            assert _children_of(here, "cu", "use-objectives")[-1] == "second-section"
            assert "Description" in asked[-1] or app.t("st_where_inside", title=tab.tree.row("use-objectives").text(0)) == asked[-1]
            # nothing chosen: at the end of the document
            answer["value"] = ("third-section", "Troisième section")
            _clear(tab)
            tab.on_add_section()
            assert _top_level(here, "cu")[-1] == "third-section" and asked[-1] == app.t("st_where_top")
            # cancelled: nothing
            answer["value"] = None
            before = _bytes(here.structure_file("cu"))
            tab.on_add_section()
            assert _bytes(here.structure_file("cu")) == before
            # an id taken, an id that is none: said in the banner by their codes, and nothing is written
            answer["value"] = ("purpose", "Encore")
            tab.on_add_section()
            assert "purpose" in _banner(tab) and _bytes(here.structure_file("cu")) == before
            answer["value"] = ("Pas Un Id", "Encore")
            tab.on_add_section()
            assert _banner(tab) and "Pas Un Id" in _banner(tab) and _bytes(here.structure_file("cu")) == before
            assert not re.search(r"[{}]", _banner(tab))
        assert tab.tree.ids() == [n.id for n in structure.flatten(structure.tree(here, "cu"))]


def test_a_chapter_added_has_its_three_titles_and_the_report_has_no_chapters():
    import structure
    with _open("structure_tab_add_group") as (tab, app, here):
        titles = {"fr": "Nouveau chapitre", "de": "Neues Kapitel", "en": "New chapter"}
        with _patched(tab, ask_group=lambda where: ("new-chapter", titles)):
            _choose(tab, "introduction")
            tab.on_add_group()
        found = structure.find(structure.read(here.structure_file("cu")), "new-chapter")[0]
        assert found["title"] == titles and tab.tree.selected_ids() == ["new-chapter"] and tab.host.kind == "chapter"
        assert tab.tree.node("new-chapter").kind == "group"
        assert not tab.buttons["add_group"].toolTip() == "" and tab.buttons["add_group"].isEnabled()
    with _open("structure_tab_add_group_rs", mode="rs") as (tab, app, here):
        assert not tab.buttons["add_group"].isEnabled() and tab.buttons["add_group"].toolTip() == app.t("st_why_rs_no_groups")
        asked = []
        with _patched(tab, ask_group=lambda where: asked.append(where)):
            tab.on_add_group()
        assert not asked and _banner(tab) == app.t("st_why_rs_no_groups")


def test_an_object_of_every_kind_is_added_after_the_one_chosen_between_blank_lines_and_nothing_else_of_the_file_changes():
    import structure_tab
    import typst_objects
    with _open("structure_tab_add_object") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        assert len(structure_tab.OBJECT_KINDS) >= 4, structure_tab.OBJECT_KINDS
        _choose(tab, "introduction")
        assert not tab.buttons["add_object"].isEnabled() and tab.buttons["add_object"].toolTip() == app.t("st_off_none"), "a chapter holds no object"
        assert tab.write_add_object("text") is False and _banner(tab) == app.t("st_off_none")
        for kind in structure_tab.OBJECT_KINDS:
            _choose(tab, "purpose/p2")
            assert tab.buttons["add_object"].isEnabled()
            before = _text(path)
            ids = re.findall(r"^// woodcore:object \S+ (\S+)", before, re.M)
            blocks = {i: typst_objects.find(before, i).written for i in ids}
            assert tab.write_add_object(kind) is True, (kind, _banner(tab))
            after = _text(path)
            new = [i for i in re.findall(r"^// woodcore:object \S+ (\S+)", after, re.M) if i not in ids]
            assert len(new) == 1, (kind, new)
            now = re.findall(r"^// woodcore:object \S+ (\S+)", after, re.M)
            assert now.index(new[0]) == now.index("p2") + 1, (kind, now)
            assert typst_objects.find(after, new[0]).type == kind
            assert {i: typst_objects.find(after, i).written for i in ids} == blocks, (kind, "an object of the file changed")
            lines = _lines(after)
            found = typst_objects.find(after, new[0])
            assert not lines[found.start - 1].strip() and not lines[found.end + 1].strip(), (kind, "no blank line parts the new object from its neighbours")
            assert tab.tree.selected_ids() == [f"purpose/{new[0]}"] and tab.host.kind == kind, (kind, tab.host.kind)
            assert any(new[0] in words for words in app.statuses)
        # at the end of a section chosen
        _choose(tab, "future-extension")
        assert tab.write_add_object("text") is True
        ids = re.findall(r"^// woodcore:object \S+ (\S+)", _text(_section_path(here, "cu", "future-extension")), re.M)
        assert tab.tree.selected_ids() == [f"future-extension/{ids[-1]}"] and ids[-1] not in ("title", "p1", "extension-loads"), ids


def test_a_section_removed_is_archived_and_never_deleted_and_a_no_removes_nothing():
    import structure
    with _open("structure_tab_remove") as (tab, app, here):
        path = _section_path(here, "cu", "future-extension")
        content = _bytes(path)
        asked = []
        _choose(tab, "future-extension")
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or False):
            tab.on_remove()
        assert len(asked) == 1 and "archives" in asked[0] and path.is_file()
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or True):
            tab.on_remove()
        assert not path.exists() and "future-extension" not in tab.tree.ids()
        archived = list((here.document_dir("cu") / "Sections" / "archives").glob("*future-extension*.typ"))
        assert len(archived) == 1 and archived[0].read_bytes() == content, "the file was not archived whole"
        assert "future-extension" not in [e["id"] for e in structure.read(here.structure_file("cu"))["sections"][1]["children"]]
        assert tab.tree.selected_ids() and tab.tree.selected_ids()[0] in tab.tree.ids(), "a neighbour is chosen after a removal"
        # a chapter that still holds sections is not removed: its refusal is said
        _choose(tab, "introduction")
        with _patched(tab, ask_confirm=lambda words: True):
            tab.on_remove()
        assert "introduction" in tab.tree.ids() and _banner(tab) and not re.search(r"[{}]", _banner(tab))
        # several at once are asked about once
        _choose(tab, "service-life", "settlements")
        asked.clear()
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or False):
            tab.on_remove()
        assert asked == [app.t("st_remove_ask_many", count=2)]
        # nothing chosen: said, nothing asked
        _clear(tab)
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or True):
            tab.on_remove()
        assert app.statuses[-1] == app.t("st_off_none")


def test_an_object_removed_is_copied_into_the_archives_first_and_the_file_keeps_one_blank_line_where_it_stood():
    import typst_objects
    with _open("structure_tab_remove_object") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        before = _text(path)
        block = "".join(_lines(before)[typst_objects.find(before, "p3").start:typst_objects.find(before, "p3").end + 1])
        _choose(tab, "purpose/p3")
        asked = []
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or True):
            tab.on_remove()
        assert asked == [], "an object is taken out without a question: it stays in the tree, to be put back (06.10.2026)"
        after = _text(path)
        assert typst_objects.find(after, "p3") is None and "\n\n\n" not in after.replace("\r\n", "\n")
        assert _outside(before, "p3").replace("\n\n\n", "\n\n") == after.replace("\n\n\n", "\n\n") or all(i in after for i in ("p1", "p2", "p4"))
        archived = list((here.document_dir("cu") / "Sections" / "archives").glob("*purpose-p3.typ"))
        assert len(archived) == 1 and archived[0].read_text(encoding="utf-8") == block
        assert tab.tree.selected_ids() == ["purpose/document-family"], "the object after the one removed is chosen next"
        assert "purpose/p3" not in tab.tree.ids()
        removed = [i for i in tab.tree.ids() if i.startswith("purpose/~removed-") and i.endswith("-p3")]
        assert len(removed) == 1, "the object taken out is not shown in the tree where it stood"
        ids = tab.tree.ids()
        assert ids.index("purpose/p2") < ids.index(removed[0]) < ids.index("purpose/document-family"), "not shown where it stood"
        # put back from its row: right after the object that stood before it
        tab.write_restore(removed[0])
        back = _text(path)
        assert typst_objects.find(back, "p3") is not None and back.index("// woodcore:/object p2") < back.index("// woodcore:object text p3") < back.index("document-family")
        assert not [i for i in tab.tree.ids() if "~removed-" in i]


def test_a_section_renamed_keeps_its_file_name_in_step_and_a_shared_one_keeps_its_id():
    with _open("structure_tab_rename") as (tab, app, here):
        _choose(tab, "intended-use")
        with _patched(tab, ask_rename=lambda node_id, title: "purpose-of-use"):
            tab.on_rename()
        assert _section_path(here, "cu", "purpose-of-use").is_file() and not _section_path(here, "cu", "intended-use").exists()
        assert tab.tree.selected_ids() == ["purpose-of-use"] and "purpose-of-use/intended-use-table" in tab.tree.ids()
        # a shared section keeps its id: the other document names it too
        _choose(tab, "scope-and-limits")
        with _patched(tab, ask_rename=lambda node_id, title: "scope"):
            tab.on_rename()
        assert _section_path(here, "cu", "scope-and-limits").is_file() and "Base de projet" in _banner(tab) and "(bp)" not in _banner(tab), _banner(tab)
        # nothing chosen, or the same id: nothing is asked or written
        asked = []
        _clear(tab)
        with _patched(tab, ask_rename=lambda node_id, title: asked.append(node_id)):
            tab.on_rename()
        assert not asked and app.statuses[-1] == app.t("st_off_none")


def test_a_file_with_text_no_tag_wraps_is_tagged_from_the_button_and_the_pane_and_prints_as_before():
    import structure
    # a report section with no tag: since 06.10.2026 the report is made from a content template whose sections are tagged, so one is written here as a report written before carries it -- its tags taken out
    here = _copy("structure_tab_tag")
    first = sorted((here.document_dir("rs") / "Sections").glob("[0-9]*.typ"))[0]
    first.write_bytes(b"".join(line for line in first.read_bytes().splitlines(keepends=True) if not line.lstrip().startswith((b"// woodcore:object", b"// woodcore:/object"))))
    with _open("structure_tab_tag", mode="rs", here=here) as (tab, app, here):
        files = [n for n in structure.flatten(tab.nodes) if n.kind == "file"]
        file = next(n for n in files if Path(n.file).name == first.name)
        path = here.document_dir("rs") / "Sections" / Path(file.file).name
        before = _text(path)
        assert not [n for n in structure.flatten(tab.nodes) if n.kind == "object" and n.parent == file.id], "the section is not tagged"
        _choose(tab, file.id)
        assert tab.buttons["tag"].isEnabled() and tab.host.kind == "section" and tab.host.pane().tag_card.isVisibleTo(tab.host.pane())
        tab.host.pane().tag_button.click()          # the pane asks, the tab writes
        after = _text(path)
        assert "// woodcore:object" in after and after != before
        assert tab.tree.selected_ids() == [file.id]
        children = [n for n in structure.flatten(tab.nodes) if n.parent == file.id]
        assert children and all(n.kind == "object" for n in children), [n.kind for n in children]
        assert [c.id for c in children] == [i for i in tab.tree.ids() if i.startswith(file.id + "/")]
        count = len(re.findall(r"^// woodcore:object ", after, re.M))
        assert app.statuses[-1] == app.t("st_tagged", count=count, file=file.file)
        keep = lambda text: [line for line in text.replace("\r\n", "\n").split("\n") if line.strip() and not line.lstrip().startswith("// woodcore:")]   # noqa: E731
        assert keep(after) == keep(before), "tagging changed what the file prints"
        # nothing left to tag: the button says why it cannot
        assert not tab.buttons["tag"].isEnabled() and tab.buttons["tag"].toolTip() == app.t("st_off_tag")
        assert tab.write_tag(file.id) is True and _text(path) == after and app.statuses[-1] == app.t("st_tag_nothing", file=file.file)
    # a tagged section of the convention with a paragraph typed below its tags in VS Code
    with _open("structure_tab_tag_cu") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        _choose(tab, "purpose")
        assert not tab.buttons["tag"].isEnabled()
        path.write_bytes(_bytes(path) + b"\nUn paragraphe oublie par l'editeur.\n")
        tab.reload_external()
        assert tab.buttons["tag"].isEnabled() and tab.host.pane().tag_card.isVisibleTo(tab.host.pane())
        tab.on_tag()
        assert any(i.startswith("purpose/") and i not in {f"purpose/{o}" for o in ("title", "p1", "p2", "p3", "document-family", "p4")} for i in tab.tree.ids())


# --- importing from another document ---------------------------------------------------------------------------

def test_the_import_dialog_offers_the_other_documents_and_what_is_ticked_is_what_it_answers():
    _qt()
    import doc_import
    import import_dialog
    import structure_words
    from PySide6.QtWidgets import QDialog, QDialogButtonBox
    here = _copy("structure_tab_import_dialog")
    with project.using(here):
        for lang in ("fr", "de", "en"):
            table = structure_words.STRINGS[lang]
            dialog = import_dialog.ImportDialog(None, lambda key, _t=table, **v: _t[key].format(**v) if v else _t[key], here, "bp", lang)
            assert dialog.sources == list(doc_import.other_documents(here, "bp")) == ["cu", "rs"]
            assert dialog.source() == "cu" and dialog.combo.count() == 2
            assert dialog.windowTitle() == table["st_import_title"]
        dialog.close()
        t = lambda key, **v: structure_words.STRINGS["fr"][key].format(**v) if v else structure_words.STRINGS["fr"][key]   # noqa: E731
        dialog = import_dialog.ImportDialog(None, t, here, "bp", "fr")
        ok = dialog.buttons.button(QDialogButtonBox.StandardButton.Ok)
        assert dialog.items() == [] and not ok.isEnabled() and dialog.tree.topLevelItemCount() == len([i for i in doc_import.importable(here, "cu")])
        assert dialog.values()[0] == "cu" and dialog.values()[2] is True, "linked unless a copy of its own is asked for"
        # a section ticked whole is itself; objects ticked alone are those objects
        dialog.tick(lambda item: item.kind == "section" and item.id == "purpose")
        got = dialog.items()
        assert [(i.kind, i.id) for i in got] == [("section", "purpose")] and ok.isEnabled()
        dialog.tick(lambda item: True, on=False)
        dialog.tick(lambda item: item.kind == "object" and item.id == "intended-use-table")
        assert [(i.kind, i.id, i.section) for i in dialog.items()] == [("object", "intended-use-table", "intended-use")]
        # every object of a section ticked is the section ticked whole: it is imported whole
        dialog.tick(lambda item: item.kind == "object" and item.section == "intended-use")
        assert [(i.kind, i.id) for i in dialog.items()] == [("section", "intended-use")]
        dialog.independent.setChecked(True)
        assert dialog.values()[2] is False
        # another document chosen: its own tree is made again, nothing ticked
        dialog.combo.setCurrentIndex(dialog.combo.findData("rs"))
        assert dialog.source() == "rs" and dialog.items() == []
        assert {dialog.tree.topLevelItem(i).data(0, import_dialog.ITEM_ROLE).id for i in range(dialog.tree.topLevelItemCount())} >= {"001-einleitung"}
        dialog.close()
        # the tab asks it through one method and gets (source, items, linked)
        import structure_tab
        tab_dialog = import_dialog.ImportDialog

        def accept(self):
            self.tick(lambda item: item.kind == "section" and item.id == "purpose")
            return QDialog.DialogCode.Accepted

        with _open("structure_tab_import_ask", mode="bp") as (tab, app, here2):
            with _patched(tab_dialog, exec=accept):
                source, items, linked = structure_tab.StructureTab.ask_import(tab)
            assert source == "cu" and [(i.kind, i.id) for i in items] == [("section", "purpose")] and linked is True
            with _patched(tab_dialog, exec=lambda self: QDialog.DialogCode.Rejected):
                assert structure_tab.StructureTab.ask_import(tab) is None
        assert structure_tab.import_dialog is import_dialog


def test_what_is_imported_arrives_at_the_bottom_of_the_tree_chosen_linked_or_as_an_independent_copy():
    import doc_import
    import structure
    with _open("structure_tab_import_flow", mode="bp") as (tab, app, here):
        items = doc_import.flatten(doc_import.importable(here, "cu"))
        purpose = next(i for i in items if i.kind == "section" and i.id == "purpose")
        assert "purpose" not in tab.tree.ids()
        # the button: asked through one method, so the answer is the test's
        with _patched(tab, ask_import=lambda: ("cu", [purpose], False)):
            tab.on_import()
        assert "purpose" in tab.tree.ids() and tab.tree.selected_ids() == ["purpose"], tab.tree.selected_ids()
        assert _top_level(here, "bp")[-1] == "purpose", "an imported section goes to the bottom"
        copy = _text(_section_path(here, "bp", "purpose"))
        source = structure.fit_text(_text(_section_path(here, "cu", "purpose")), 1)       # its headings at the level it prints at here, the top of the tree (06.10.2026)
        assert "woodcore:shared" not in copy and copy.replace("\r\n", "\n") == source.replace("\r\n", "\n"), "an independent copy is a copy and shares nothing"
        assert not _banner(tab) and any("Convention" in words or "purpose" in words or "1" in words for words in app.statuses)
        assert tab.tree.row("purpose").isSelected() and not tab.tree.node("purpose").shared_with
        # linked: the copy and the source carry the same shared block
        future = next(i for i in items if i.kind == "section" and i.id == "future-extension")
        with _patched(tab, ask_import=lambda: ("cu", [future], True)):
            tab.on_import()
        assert "future-extension" in tab.tree.ids() and tab.tree.node("future-extension").shared_with == ("cu",)
        assert "woodcore:shared" in _text(_section_path(here, "cu", "future-extension")) and "woodcore:shared" in _text(_section_path(here, "bp", "future-extension"))
        # objects ticked alone go to the section «Importé», created at the bottom, and are chosen
        table = next(i for i in items if i.kind == "object" and i.id == "intended-use-table")
        with _patched(tab, ask_import=lambda: ("cu", [table], False)):
            tab.on_import()
        chosen = tab.tree.selected_ids()
        assert len(chosen) == 1 and chosen[0].endswith("/intended-use-table") and tab.tree.node(chosen[0]).object_type == "table", chosen
        assert _top_level(here, "bp")[-1] == chosen[0].split("/")[0]
        # a refusal -- a block this document already holds -- is said in the banner and writes nothing
        sections = {p.name: p.read_bytes() for p in (here.document_dir("bp") / "Sections").glob("*.typ")}
        service = next(i for i in items if i.kind == "section" and i.id == "service-life")
        with _patched(tab, ask_import=lambda: ("cu", [service], True)):
            tab.on_import()
        assert _banner(tab) and not re.search(r"[{}]", _banner(tab))
        assert {p.name: p.read_bytes() for p in (here.document_dir("bp") / "Sections").glob("*.typ")} == sections
        # cancelled: nothing
        before = _bytes(here.structure_file("bp"))
        with _patched(tab, ask_import=lambda: None):
            tab.on_import()
        assert _bytes(here.structure_file("bp")) == before
        assert tab.tree.ids() == [n.id for n in structure.flatten(structure.tree(here, "bp"))]


def test_a_project_laid_out_as_one_report_offers_no_import():
    _qt()
    from fixtures import legacy_example
    here = legacy_example.build(conftest.tmpdir("structure_tab_legacy_import") / "Exemple", conftest.SAMPLE)
    for pdf in here.root.rglob("*.pdf"):
        pdf.unlink()
    project.sync_engine(here)
    with _open("structure_tab_legacy_import", mode="rs", here=here) as (tab, app, here):
        assert not here.has_modes
        assert not tab.buttons["import"].isEnabled() and tab.buttons["import"].toolTip() == app.t("st_import_empty")
        assert not tab.sync_box.isVisibleTo(tab), "a project of one document shares nothing"


def test_the_dialogs_for_a_new_section_a_new_chapter_and_a_choice_answer_what_was_typed():
    _qt()
    import import_dialog
    import structure_words
    from PySide6.QtWidgets import QDialogButtonBox
    t = lambda key, **v: structure_words.STRINGS["fr"][key].format(**v) if v else structure_words.STRINGS["fr"][key]   # noqa: E731
    dialog = import_dialog.SectionDialog(None, t, "après X", lambda title: title.lower().replace(" ", "-"))
    ok = dialog.buttons.button(QDialogButtonBox.StandardButton.Ok)
    assert not ok.isEnabled() and dialog.values() == ("", "")
    dialog.title.setText("Ma Section")
    assert ok.isEnabled() and dialog.values() == ("ma-section", "Ma Section"), "the id follows the title"
    dialog.id.textEdited.emit("mon-id")
    dialog.id.setText("mon-id")
    dialog.title.setText("Autre titre")
    assert dialog.values() == ("mon-id", "Autre titre"), "an id typed over is not replaced by the title's"
    group = import_dialog.GroupDialog(None, t, "à la fin", lambda title: title.lower().replace(" ", "-"))
    ok = group.buttons.button(QDialogButtonBox.StandardButton.Ok)
    group.titles["fr"].setText("Chapitre")
    group.titles["de"].setText("Kapitel")
    assert not ok.isEnabled(), "a chapter has its title in all three languages"
    group.titles["en"].setText("New chapter")
    assert ok.isEnabled() and group.values() == ("new-chapter", {"fr": "Chapitre", "de": "Kapitel", "en": "New chapter"})
    choice = import_dialog.ChoiceDialog(None, t, "service-life/p1", "Base de projet", [("mine", "garder la mienne"), ("theirs", "prendre celle de la Base de projet"), ("rs", "celle du rapport")])
    assert choice.chosen() == "mine"
    choice.radios[1].setChecked(True)
    assert choice.chosen() == "theirs"
    for lang in ("de", "en"):
        table = structure_words.STRINGS[lang]
        words = lambda key, _t=table, **v: _t[key].format(**v) if v else _t[key]   # noqa: E731
        assert import_dialog.SectionDialog(None, words, "x", lambda title: title).windowTitle() == table["st_new_section"]
        assert import_dialog.GroupDialog(None, words, "x", lambda title: title).windowTitle() == table["st_new_group"]


# --- «Enregistrer comme template de fond…» ---------------------------------------------------------------------------------

@contextlib.contextmanager
def _own_templates(name, office=False):
    """The engineer's document templates redirected into a clean folder of this process for the length of a check -- and, with `office`, the office's shared folder named in the test run's own settings -- everything put back after. Yields the folder."""
    import usersettings
    base = conftest.tmpdir(name)
    saved_env = os.environ.get("WOODCORE_TEMPLATES")
    saved_settings = usersettings.read()
    os.environ["WOODCORE_TEMPLATES"] = str(base / "user")
    if office:
        usersettings.write({**saved_settings, "templates": {"shared_folder": str(base / "office")}})
    try:
        yield base
    finally:
        usersettings.write(saved_settings)
        if saved_env is None:
            os.environ.pop("WOODCORE_TEMPLATES", None)
        else:
            os.environ["WOODCORE_TEMPLATES"] = saved_env


def _templates(mode, place=None):
    import doc_templates
    return [t for t in doc_templates.list_templates(mode) if t.place != "builtin" and (place is None or t.place == place)]


def _folder_digest(folder):
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_the_document_is_saved_as_a_template_with_the_name_description_and_place_asked_and_what_is_enabled_stays_so():
    import structure
    with _own_templates("structure_tab_template") as base:
        with _open("structure_tab_template_project") as (tab, app, here):
            button = tab.buttons["save_template"]
            assert button.isEnabled() and button.text() == app.t("st_save_template") and button.toolTip() == app.t("st_save_template_tip")
            assert tab.write_enabled("purpose", False), "a section switched off ..."
            flushed = []
            real = tab.host.flush
            tab.host.flush = lambda: flushed.append(1) or real()
            with _patched(tab, ask_template=lambda: ("Convention courte", "Pour les petits bâtiments", "user")):
                tab.on_save_template()
            assert flushed, "what a pane holds pending is written before the document is copied"
            found = _templates("cu")
            assert [t.ref for t in found] == ["user:cu/Convention courte"], [t.ref for t in found]
            saved = found[0]
            assert not saved.error and saved.name("fr") == "Convention courte" and saved.description("fr") == "Pour les petits bâtiments" and saved.languages == ["fr"]
            assert saved.folder == base / "user" / "documents" / "cu" / "Convention courte"
            held = structure.read(saved.structure_file("fr"))
            leaves = {node["id"]: node for node, _depth in structure.leaves(held)}
            assert leaves["purpose"]["enabled"] is False and leaves["intended-use"]["enabled"] is not False, "... is switched off in the template too"
            assert (saved.language_dir("fr") / "Sections" / "purpose.typ").read_bytes() == _section_path(here, "cu", "purpose").read_bytes(), "the sections are copied as written"
            assert app.statuses[-1] == app.t("st_template_saved", name="Convention courte", folder=saved.folder) and tab.failure is None and not _banner(tab)
            # the base de projet is a document of its own, and its template is its own
            assert _templates("bp") == []
        with _open("structure_tab_template_bp", mode="bp") as (tab, app, here):
            with _patched(tab, ask_template=lambda: ("Base courte", "", "user")):
                tab.on_save_template()
            assert [t.ref for t in _templates("bp")] == ["user:bp/Base courte"] and [t.ref for t in _templates("cu")] == ["user:cu/Convention courte"]


def test_the_report_saves_its_content_template_too_and_a_project_held_read_only_may_still_save_one():
    """The report has content templates of its own since 06.10.2026: «Enregistrer comme template de fond…» is open in the three documents, and it writes nothing into the project, so a project held read-only may save one too."""
    with _own_templates("structure_tab_template_rs") as base:
        with _open("structure_tab_template_rs_project", mode="rs") as (tab, app, here):
            button = tab.buttons["save_template"]
            assert button.isEnabled() and button.toolTip() == app.t("st_save_template_tip")
            with _patched(tab, ask_template=lambda: ("Rapport court", "", "user")):
                tab.on_save_template()
            assert [t.ref for t in _templates("rs")] == ["user:rs/Rapport court"], [t.ref for t in _templates("rs")]
            assert tab.failure is None and (base / "user").exists()
        with _open("structure_tab_template_ro_project", read_only=True) as (tab, app, here):
            before = _digest(here)
            assert tab.buttons["save_template"].isEnabled(), "a template is written beside the engineer's settings, never into the project"
            with _patched(tab, ask_template=lambda: ("Lecture seule", "", "user")):
                tab.on_save_template()
            assert app.refused == 0 and _digest(here) == before, "a project held read-only was written"
            assert [t.ref for t in _templates("cu")] == ["user:cu/Lecture seule"]

def test_a_template_of_that_name_asks_before_it_is_written_over_and_a_refusal_is_said_in_the_window_s_words():
    import doc_templates
    import settings_dialog
    import structure
    with _own_templates("structure_tab_template_over") as base:
        with _open("structure_tab_template_over_project") as (tab, app, here):
            answer = ("Convention courte", "", "user")
            with _patched(tab, ask_template=lambda: answer):
                tab.on_save_template()
                saved = _templates("cu")[0]
                before = _folder_digest(saved.folder)
                asked = []
                with _patched(tab, ask_confirm=lambda words: asked.append(words) or False):
                    tab.on_save_template()
                assert len(asked) == 1 and "user:cu/Convention courte" in asked[0] and app.t("st_lang_fr") in asked[0], asked
                assert _folder_digest(saved.folder) == before and tab.failure is None and not _banner(tab), "a no leaves the template as it was, and says nothing more"
                # a yes writes it over, and the old one is kept in archives/
                assert tab.write_enabled("purpose", False)
                with _patched(tab, ask_confirm=lambda words: asked.append(words) or True):
                    tab.on_save_template()
                leaves = {node["id"]: node for node, _depth in structure.leaves(structure.read(saved.structure_file("fr")))}
                assert leaves["purpose"]["enabled"] is False, "the template is the document as it stands now"
                kept = list((base / "user" / "documents" / doc_templates.ARCHIVES).iterdir())
                assert len(kept) == 1 and kept[0].name.endswith("-cu-Convention courte-fr"), kept
                assert len(_templates("cu")) == 1 and app.statuses[-1].startswith("Template de fond")
                # a builtin template's name is refused, said in French by its code, and nothing is written
                builtin = [t for t in doc_templates.list_templates("cu") if t.place == "builtin"][0].name("fr")
                answer = (builtin, "", "user")
                tab.on_save_template()
                assert tab.failure == settings_dialog.t("fr", "prefs_doc_err_name_is_builtin", name=builtin) and _banner(tab) == tab.failure
                assert len(_templates("cu")) == 1
                # no shared folder is set, and the office's place is asked for all the same: the sentence of its code
                answer = ("Pour le bureau", "", "office")
                tab.on_save_template()
                assert tab.failure == settings_dialog.t("fr", "prefs_doc_err_no_folder") and not (base / "office").exists()
                # a template that is saved clears the last refusal
                answer = ("Autre", "", "user")
                tab.on_save_template()
                assert tab.failure is None and not _banner(tab) and len(_templates("cu")) == 2


def test_the_office_s_place_is_offered_where_the_settings_name_a_folder_and_the_template_goes_there():
    import doc_templates
    with _own_templates("structure_tab_template_office") as base:
        with _open("structure_tab_template_closed") as (tab, app, here):
            user, office = tab.template_places()
            assert user == ("user", "Mes templates", True, "") and office[:3] == ("office", "Partagés", False) and office[3] == app.t("st_template_place_office_off")
    with _own_templates("structure_tab_template_office2", office=True) as base:
        with _open("structure_tab_template_open") as (tab, app, here):
            assert [p[2] for p in tab.template_places()] == [True, True]
            with _patched(tab, ask_template=lambda: ("Pour le bureau", "Partagé", "office")):
                tab.on_save_template()
            shared = _templates("cu", "office")
            assert [t.ref for t in shared] == ["office:cu/Pour le bureau"] and shared[0].folder == base / "office" / "documents" / "cu" / "Pour le bureau"
            assert shared[0].description("fr") == "Partagé" and _templates("cu", "user") == []
            assert doc_templates.find("office:cu/Pour le bureau", "cu").ref == shared[0].ref


def test_the_template_dialog_asks_the_name_the_description_and_the_place_and_the_tab_asks_it_through_one_method():
    _qt()
    import import_dialog
    import structure_tab
    import structure_words
    from PySide6.QtWidgets import QDialog, QDialogButtonBox
    t = lambda key, **v: structure_words.STRINGS["fr"][key].format(**v) if v else structure_words.STRINGS["fr"][key]   # noqa: E731
    reason = t("st_template_place_office_off")
    dialog = import_dialog.TemplateDialog(None, t, "Convention d'utilisation", "français", [("user", "Mes templates", True, ""), ("office", "Templates partagés", False, reason)])
    ok = dialog.buttons.button(QDialogButtonBox.StandardButton.Ok)
    assert dialog.windowTitle() == t("st_template_title") and not ok.isEnabled() and dialog.values() == ("", "", "user"), "a template needs a name"
    assert dialog.radios[0].isChecked() and not dialog.radios[1].isEnabled() and dialog.radios[1].toolTip() == reason and reason in dialog.radios[1].text()
    dialog.name.setText("  Convention courte ")
    dialog.description.setPlainText("Une phrase.")
    assert ok.isEnabled() and dialog.values() == ("Convention courte", "Une phrase.", "user")
    both = import_dialog.TemplateDialog(None, t, "Base de projet", "allemand", [("user", "Mes templates", True, ""), ("office", "Templates partagés", True, "")])
    both.name.setText("X")
    both.radios[1].setChecked(True)
    assert both.values() == ("X", "", "office") and both.radios[0].isEnabled() and both.radios[1].isEnabled()
    for lang in ("de", "en"):
        table = structure_words.STRINGS[lang]
        words = lambda key, _t=table, **v: _t[key].format(**v) if v else _t[key]   # noqa: E731
        assert import_dialog.TemplateDialog(None, words, "x", "y", [("user", "u", True, "")]).windowTitle() == table["st_template_title"]
    # the tab asks it through one method, and gets (name, description, place) -- or None where it is cancelled
    def accept(self):
        self.name.setText("Convention courte")
        self.description.setPlainText("Description")
        return QDialog.DialogCode.Accepted

    with _own_templates("structure_tab_template_ask") as base:
        with _open("structure_tab_template_ask_project") as (tab, app, here):
            with _patched(import_dialog.TemplateDialog, exec=accept):
                assert structure_tab.StructureTab.ask_template(tab) == ("Convention courte", "Description", "user")
            with _patched(import_dialog.TemplateDialog, exec=lambda self: QDialog.DialogCode.Rejected):
                assert structure_tab.StructureTab.ask_template(tab) is None
            tab.ask_template = lambda: None
            tab.on_save_template()      # cancelled: nothing is written
            assert not (base / "user").exists()


def test_what_a_saved_template_would_miss_is_said_in_a_box_in_the_window_s_words_and_a_clean_one_says_nothing():
    import engine
    told = []
    with _own_templates("structure_tab_template_notes") as base:
        with _open("structure_tab_template_notes_project") as (tab, app, here):
            path = _section_path(here, "cu", "purpose")
            path.write_bytes(path.read_bytes() + b'\n#image("/Images/site.png")\n')
            with _patched(tab, ask_template=lambda: ("Avec image", "", "user"), tell=lambda title, text: told.append((title, text))):
                tab.on_save_template()
            assert told == [(app.t("st_template_notes_title"), app.t("st_template_note_files", files="/Images/site.png"))], told
            assert "site.png" in told[0][1] and not re.search(r"[{}]", told[0][1])
            # a note this window has no sentence for says what it carries
            assert tab.template_note(engine.Note("other", "an English sentence")) == "an English sentence"
            assert tab.template_note(engine.Note("template_tags", "english", file="Sections/x.typ")) == app.t("st_template_note_tags", file="Sections/x.typ")
        told.clear()
        with _open("structure_tab_template_clean_project", mode="bp") as (tab, app, here):
            with _patched(tab, ask_template=lambda: ("Base propre", "", "user"), tell=lambda title, text: told.append((title, text))):
                tab.on_save_template()
            assert told == [] and app.statuses[-1] == app.t("st_template_saved", name="Base propre", folder=_templates("bp")[0].folder)


# --- a file edited elsewhere ------------------------------------------------------------------------------------

def _edit_object(path, object_id, body):
    """Object `object_id` of the file at `path` rewritten the way VS Code and a text editor leave a file: on disk, behind the tab's back."""
    import typst_objects
    path.write_bytes(typst_objects.write_object(_text(path), object_id, body, force=True).encode("utf-8"))


def test_a_file_edited_elsewhere_is_read_again_with_the_pane_of_the_object_chosen_and_the_files_the_tab_wrote_itself_are_not():
    import structure
    import typst_objects
    with _open("structure_tab_external") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        assert tab.reload_external() is False, "nothing changed on disk"
        _choose(tab, "purpose/p2")
        pane = tab.host.pane()
        pane.edit.setPlainText("Écrit par le volet.")
        pane.flush()
        assert tab.signature == tab.disk_signature() and tab.reload_external() is False, "what the tab wrote itself was read again"
        # VS Code adds an object and rewrites the one chosen
        text = _text(path)
        text = typst_objects.insert_object(text, len(_lines(text)) - 1, "text", "added-by-vscode")
        path.write_bytes(text.encode("utf-8"))
        _edit_object(path, "p2", "Corps de p2 modifié dans VS Code.")
        tab.on_files_changed()
        assert tab.external_timer.isActive() and tab.external_timer.interval() == 500, "a burst of saves is one reading, a moment later"
        assert tab.reload_external() is True
        assert "purpose/added-by-vscode" in tab.tree.ids() and app.statuses[-1] == app.t("st_reloaded")
        assert tab.tree.selected_ids() == ["purpose/p2"] and tab.host.pane().edit.toPlainText() == "Corps de p2 modifié dans VS Code.", "the pane did not follow the file"
        assert tab.reload_external() is False
        # structure.json edited (by hand or by another window): the chapter's title is read again
        structure.set_title(here, "cu", "introduction", "fr", "Introduction de VS Code")
        assert tab.reload_external() is True and tab.tree.row("introduction").text(0) == "Introduction de VS Code"
        # the object chosen deleted from the file: its row goes, and the pane shows nothing
        text = _text(path)
        lines = _lines(text)
        found = typst_objects.find(text, "p2")
        path.write_bytes("".join(lines[:found.start] + lines[found.end + 1:]).encode("utf-8"))
        assert tab.reload_external() is True
        assert "purpose/p2" not in tab.tree.ids() and tab.tree.selected_ids() == [] and tab.host.kind is None and tab.subject is None


def test_what_a_pane_holds_is_written_before_a_file_edited_elsewhere_is_read_again():
    with _open("structure_tab_external_pending") as (tab, app, here):
        path = _section_path(here, "cu", "purpose")
        _choose(tab, "purpose/p3")
        tab.host.pane().edit.setPlainText("En attente dans le volet.")
        _edit_object(path, "p1", "Écrit dans VS Code, ailleurs dans le fichier.")
        assert tab.reload_external() is True
        text = _text(path)
        assert _body(text, "p3") == "En attente dans le volet." and _body(text, "p1") == "Écrit dans VS Code, ailleurs dans le fichier."
        assert not _banner(tab)


def test_the_files_are_watched_only_while_the_tab_is_shown_and_a_save_in_an_editor_reads_the_tree_again():
    with _open("structure_tab_watch") as (tab, app, here):
        tab.pane_loaded = True          # shown: the page is not what this check is about
        tab.pane.set_document(here, "cu")
        assert tab.watcher is None
        tab.resize(900, 600)
        tab.show()
        _pump(0.2)
        try:
            assert tab.watcher is not None
            held = set(tab.watcher.files()) | set(tab.watcher.directories())
            assert str(here.document_dir("cu") / "Sections") in held and str(here.structure_file("cu")) in held and str(here.document_typ("cu")) in held
            assert not [p for p in held if "archives" in p], "the archives are not watched"
            path = _section_path(here, "cu", "intended-use")
            import typst_objects
            text = typst_objects.insert_object(_text(path), len(_lines(_text(path))) - 1, "text", "from-the-editor")
            path.write_bytes(text.encode("utf-8"))
            _wait(lambda: "intended-use/from-the-editor" in tab.tree.ids(), timeout=15, what="the tree to read the file the editor saved")
        finally:
            tab.hide()
        _pump(0.1)
        assert not (tab.watcher.files() + tab.watcher.directories()), "a hidden tab holds a directory on Windows"
        assert not tab.external_timer.isActive()


def test_the_tree_and_the_selection_survive_a_rebuilt_window_and_what_a_pane_held_is_written_first():
    with _open("structure_tab_state") as (tab, app, here):
        tab.tree.expand_to(3)
        _choose(tab, "purpose/p2")
        tab.host.pane().edit.setPlainText("Tapé juste avant la reconstruction.")
        state = tab.view_state()
        assert "Tapé juste avant la reconstruction." in _text(_section_path(here, "cu", "purpose")), "a pane held what the rebuilt window would lose"
        assert state["tree"]["selection"] == ["purpose/p2"] and "purpose" in state["tree"]["expanded"] and state["pending"] is False
        assert tab.watcher is None or not (tab.watcher.files() + tab.watcher.directories())
    with project.using(here):
        import structure_tab
        app3 = FakeApp()
        app3.views["tab_structure"] = state
        restored = structure_tab.StructureTab(app3)
        try:
            assert restored.tree.selected_ids() == ["purpose/p2"] and restored.tree.row("purpose").isExpanded()
            assert restored.host.kind == "text" and restored.host.pane().edit.toPlainText() == "Tapé juste avant la reconstruction."
            assert restored.resume is False
            restored.pane.stop()
            restored.view_state()
            restored.resume = False
        finally:
            restored.stop_watching()
            restored.deleteLater()


# --- a project held read-only -----------------------------------------------------------------------------------

def _digest(here):
    """Every file of the project's documents and shared folders: name, size and bytes -- what a project that is not written must keep."""
    out = {}
    for path in sorted(here.root.rglob("*")):
        if path.is_file() and ".probe" not in path.parts and "_woodcore" not in path.parts and "archives" not in path.parts:
            out[str(path.relative_to(here.root))] = path.read_bytes()
    return out


def test_a_project_held_read_only_writes_nothing_and_says_why_on_each_button():
    with _open("structure_tab_read_only", read_only=True) as (tab, app, here):
        before = _digest(here)
        assert not tab.host.isEnabled() and not tab.compile_button.isEnabled()
        for key in ("add_section", "add_group", "add_object", "remove", "rename", "import", "tag"):
            assert not tab.buttons[key].isEnabled() and tab.buttons[key].toolTip() == app.t("st_read_only"), key
        _choose(tab, "purpose/p2")
        assert tab.host.kind == "text", "the forms stay readable"
        # every writer the window guards is refused, and the window says so
        refused = app.refused
        results = [
            tab.write_enabled("purpose", False), tab.write_title("purpose", "x"), tab.write_add_section(None, None, "x", "X"),
            tab.write_add_group(None, None, "y", {"fr": "a", "de": "b", "en": "c"}), tab.write_remove("purpose"), tab.write_rename("future-extension", "z"),
            tab.write_move("purpose", None, 0), tab.write_object("purpose/p2", "texte"), tab.write_add_object("text"), tab.write_remove_object("purpose/p2"),
            tab.write_tag("purpose"), tab.write_import("rs", [], True), tab.write_sync_import(), tab.write_sync_flag(["service-life"], True),
        ]
        assert results == [False] * len(results), results
        assert app.refused == refused + len(results)
        for slot in (tab.on_add_section, tab.on_add_group, tab.on_remove, tab.on_rename, tab.on_import, tab.on_tag, tab.on_sync_import, tab.on_sync_ignore, tab.on_sync_reactivate):
            before_refused = app.refused
            slot()
            assert app.refused == before_refused + 1, slot.__name__
        assert tab.drop_nodes(["scope-and-limits"], "purpose", "above") is False
        # a box ticked in the tree is put back, and a pane edited writes nothing
        from PySide6.QtCore import Qt
        tab.tree.row("purpose").setCheckState(0, Qt.CheckState.Unchecked)
        _pump()
        assert tab.tree.row("purpose").checkState(0) == Qt.CheckState.Checked
        # working out what is shared records nothing in a project that is not written
        tab.refresh_sync()
        assert _digest(here) == before, "a project held read-only was written"


def test_a_project_not_held_read_only_keeps_its_buttons_enabled_with_their_own_words():
    with _open("structure_tab_writable") as (tab, app, here):
        _choose(tab, "purpose")
        for key in ("add_section", "add_group", "add_object", "remove", "rename", "import"):
            assert tab.buttons[key].isEnabled() and tab.buttons[key].toolTip() == app.t("st_" + key + "_tip"), key
        assert tab.compile_button.isEnabled() and tab.host.isEnabled()


# --- what is shared with the other documents -------------------------------------------------------------------------

def _ink(tab, node_id):
    """The colour a row is drawn in, as a name -- "" where it is the tree's own."""
    from PySide6.QtCore import Qt
    brush = tab.tree.row(node_id).foreground(0)
    return "" if brush.style() == Qt.BrushStyle.NoBrush else brush.color().name()


def _token(name):
    import theme
    from PySide6.QtGui import QColor
    return QColor(theme.colour(name)).name()


def _mark(tab, node_id):
    import structure_tree
    return tab.tree.row(node_id).text(structure_tree.SYNC)


def test_a_copy_edited_on_disk_in_the_other_document_is_orange_and_the_import_takes_it_between_the_tags_only():
    import structure_tab
    import sync
    with _open("structure_tab_sync_incoming", mode="bp") as (tab, app, here):
        cu, bp = _section_path(here, "cu", "service-life"), _section_path(here, "bp", "service-life")
        status = tab.refresh_sync()
        assert status is not None and not status.incoming and not status.conflicts and tab.sync_box.isVisibleTo(tab)
        assert tab.sync_label.text() == app.t("st_sync_nothing")
        assert not tab.buttons["sync_import"].isEnabled() and tab.buttons["sync_import"].toolTip() == app.t("st_sync_off_incoming")
        assert _ink(tab, "service-life") == "" and _mark(tab, "service-life") == ""
        before = _bytes(bp)
        # VS Code edits the convention's copy of a section the two documents share
        _edit_object(cu, "p1", "Un nouveau texte de la durée d'utilisation.")
        tab.refresh_sync()            # what `on_shown` and the debounce after a write call
        orange = _token("override")
        assert sync.item_key("service-life", "p1") in tab.sync_status.incoming
        assert _ink(tab, "service-life") == orange and _ink(tab, "service-life/p1") == orange, (_ink(tab, "service-life"), orange)
        assert _mark(tab, "service-life") == "↓" and _mark(tab, "service-life/p1") == "↓"
        assert _ink(tab, "service-life/title") == "" and _ink(tab, "scope-and-limits") == "", "what did not change is not coloured"
        assert _ink(tab, "use-and-logistics") == orange, "a chapter shows the worst of its sections"
        assert "Convention d'utilisation" in tab.tree.row("service-life/p1").toolTip(3)
        assert tab.sync_state(tab.tree.node("service-life")) == "incoming" and tab.sync_state(tab.tree.node("purpose-of-basis-of-design")) is None
        assert tab.buttons["sync_import"].isEnabled() and tab.sync_label.text() == app.t("st_sync_counts", incoming=len(tab.sync_status.incoming), conflicts=0, ignored=0)
        # «Importer les modifications» with nothing chosen takes everything incoming, between the tags only
        tab.on_sync_import()
        after = _text(bp)
        assert structure_tab.shared_block_text(after, "service-life") == structure_tab.shared_block_text(_text(cu), "service-life")
        outside = lambda text: text.replace(structure_tab.shared_block_text(text, "service-life"), "")   # noqa: E731
        assert outside(after) == outside(before.decode("utf-8")), "the import changed the file beside the shared block"
        assert not _banner(tab) and any("service-life" in words for words in app.statuses)
        status = sync.status(here, "bp")
        assert not status.incoming and not status.conflicts and not sync.status(here, "cu").incoming
        assert _ink(tab, "service-life") == "" and _mark(tab, "service-life") == "" and not tab.buttons["sync_import"].isEnabled()


def test_import_on_a_selection_takes_only_what_is_chosen():
    import sync
    with _open("structure_tab_sync_selection", mode="bp") as (tab, app, here):
        _edit_object(_section_path(here, "cu", "service-life"), "p1", "Texte modifié de la durée.")
        _edit_object(_section_path(here, "cu", "settlements"), "p1", "Texte modifié des tassements.")
        tab.refresh_sync()
        orange = _token("override")
        assert _ink(tab, "service-life") == orange and _ink(tab, "settlements") == orange
        _choose(tab, "service-life/p1")
        assert tab.buttons["sync_import"].isEnabled() and tab.buttons["sync_ignore"].isEnabled()
        tab.on_sync_import()
        assert _body(_text(_section_path(here, "bp", "service-life")), "p1") == "Texte modifié de la durée."
        assert "Texte modifié des tassements." not in _text(_section_path(here, "bp", "settlements")), "an import on a selection took what was not chosen"
        assert _ink(tab, "service-life") == "" and _ink(tab, "settlements") == orange
        # a section row chosen stands for every block in its file
        _choose(tab, "settlements")
        tab.on_sync_import()
        assert "Texte modifié des tassements." in _text(_section_path(here, "bp", "settlements")) and not sync.status(here, "bp").incoming


def test_ignore_keeps_a_change_out_of_the_import_greys_it_for_good_and_reactivate_takes_it_back():
    import sync
    with _open("structure_tab_sync_ignore", mode="bp") as (tab, app, here):
        bp = _section_path(here, "bp", "service-life")
        _edit_object(_section_path(here, "cu", "service-life"), "p1", "Un texte que le document ne veut pas.")
        tab.refresh_sync()
        before = _bytes(bp)
        _choose(tab, "service-life")
        assert not tab.buttons["sync_reactivate"].isEnabled() and tab.buttons["sync_reactivate"].toolTip() == app.t("st_sync_off_ignored")
        tab.on_sync_ignore()
        muted = _token("muted")
        assert tab.sync_state(tab.tree.node("service-life")) == "ignored" and _ink(tab, "service-life") == muted and _mark(tab, "service-life") == "–"
        assert tab.buttons["sync_reactivate"].isEnabled()
        # an import of everything leaves it alone, and so does a reload
        tab.on_sync_import()
        assert _bytes(bp) == before, "an ignored change was imported"
        tab.reload()
        tab.refresh_sync()
        assert tab.sync_state(tab.tree.node("service-life")) == "ignored" and _ink(tab, "service-life") == muted
        assert (here.document_dir("bp") / "sync.json").is_file(), "what is ignored is remembered in the document's sync.json"
    with _open("structure_tab_sync_ignore_again", mode="bp", here=here) as (tab, app, here):
        tab.refresh_sync()
        assert tab.sync_state(tab.tree.node("service-life")) == "ignored", "a window built again forgot what was ignored"
        _choose(tab, "service-life")
        tab.on_sync_reactivate()
        assert tab.sync_state(tab.tree.node("service-life")) == "incoming" and _ink(tab, "service-life") == _token("override")
        tab.on_sync_import()
        assert "Un texte que le document ne veut pas." in _text(bp) and not sync.status(here, "bp").incoming
        # nothing chosen: said, and nothing written
        _clear(tab)
        before = _bytes(here.document_dir("bp") / "sync.json")
        tab.on_sync_ignore()
        assert _banner(tab) == app.t("st_sync_off_selection") and _bytes(here.document_dir("bp") / "sync.json") == before


def test_a_conflict_asks_which_version_to_keep_and_honours_the_choice_and_a_cancel_writes_nothing():
    import structure_tab
    import sync
    key = sync.item_key("service-life", "p1")

    def conflicting(name):
        here = _copy(name)
        _edit_object(_section_path(here, "cu", "service-life"), "p1", "La version de la convention d'utilisation.")
        _edit_object(_section_path(here, "bp", "service-life"), "p1", "La version de la base de projet.")
        return here

    for choice, expected in (("mine", "La version de la base de projet."), ("theirs", "La version de la convention d'utilisation.")):
        with _open("structure_tab_sync_conflict_" + choice, mode="bp", here=conflicting("structure_tab_sync_conflict_copy_" + choice)) as (tab, app, here):
            tab.refresh_sync()
            assert tab.sync_state(tab.tree.node("service-life")) == "conflict" and _ink(tab, "service-life/p1") == _token("danger"), "a conflict is red"
            assert _mark(tab, "service-life/p1") == "!"
            asked = []
            with _patched(tab, ask_choice=lambda k, found: asked.append((k, found)) or choice):
                tab.on_sync_import()
            assert len(asked) == 1 and asked[0][0] == key and set(asked[0][1].sources) == {"cu"}, [k for k, _f in asked]
            assert asked[0][0] != "service-life", "the block was asked about as well as the object that conflicts in it"
            assert _body(_text(_section_path(here, "bp", "service-life")), "p1") == expected, choice
            assert not _banner(tab)
    # a cancel writes nothing and says nothing is imported
    with _open("structure_tab_sync_conflict_cancel", mode="bp", here=conflicting("structure_tab_sync_conflict_copy_cancel")) as (tab, app, here):
        tab.refresh_sync()
        before = _digest(here)
        with _patched(tab, ask_choice=lambda k, found: None):
            assert tab.write_sync_import() is False
        assert _digest(here) == before
    # the question itself: this document's version, the newest of the others, and each other document's
    with _open("structure_tab_sync_question", mode="bp") as (tab, app, here):
        from PySide6.QtWidgets import QDialog
        import import_dialog
        found = type("Found", (), {"sources": ("cu", "rs")})()
        seen = {}

        def accept(self):
            seen["options"] = [radio.property("choice") for radio in self.radios]
            seen["texts"] = [radio.text() for radio in self.radios]
            self.radios[1].setChecked(True)
            return QDialog.DialogCode.Accepted

        with _patched(import_dialog.ChoiceDialog, exec=accept):
            assert structure_tab.StructureTab.ask_choice(tab, key, found) == "theirs"
        assert seen["options"] == ["mine", "theirs", "rs"] and "Convention d'utilisation" in seen["texts"][1] and "Rapport" in seen["texts"][2]
        with _patched(import_dialog.ChoiceDialog, exec=lambda self: QDialog.DialogCode.Rejected):
            assert structure_tab.StructureTab.ask_choice(tab, key, found) is None
        assert structure_tab.import_dialog is import_dialog


def test_an_edit_in_the_right_pane_of_a_shared_object_writes_this_copy_only_and_the_other_document_sees_it_as_incoming():
    import sync
    with _open("structure_tab_sync_local") as (tab, app, here):
        bp = _section_path(here, "bp", "service-life")
        bp_before = _bytes(bp)
        cu = _section_path(here, "cu", "service-life")
        _choose(tab, "service-life/service-life-table")
        assert tab.host.kind == "table"
        tab.host.pane().add_row()
        assert _bytes(bp) == bp_before, "the edit was written into the other document's copy"
        assert _rows(_body(_text(cu), "service-life-table")) == _rows(_body(bp_before.decode("utf-8"), "service-life-table")) + 1
        status = sync.status(here, "bp")
        assert sync.item_key("service-life", "service-life-table") in status.incoming, status.counts
        assert not _banner(tab), "the edit was written but the record of it was not"
        # in this document it is the local edit: no alarm, a small mark
        tab.refresh_sync()
        assert tab.sync_state(tab.tree.node("service-life/service-life-table")) == "local" and _ink(tab, "service-life/service-life-table") == "" and _mark(tab, "service-life/service-life-table") == "↑"
        # and the base de projet's own tab shows it orange
        with _open("structure_tab_sync_local_bp", mode="bp", here=here) as (other, app2, _h):
            other.refresh_sync()
            assert _ink(other, "service-life/service-life-table") == _token("override") and _ink(other, "service-life") == _token("override")
            other.on_sync_import()
            assert _rows(_body(_text(bp), "service-life-table")) == _rows(_body(_text(cu), "service-life-table"))
        # adding and removing an object of a shared section is an edit of it too
        _choose(tab, "service-life/p1")
        assert tab.write_add_object("text") is True
        assert sync.status(here, "bp").incoming, "an object added to a shared section was not told to calc/sync.py"


def test_an_edit_whose_record_cannot_be_written_stays_written_and_says_so_and_a_sync_refusal_is_said_in_the_banner():
    import sync
    with _open("structure_tab_sync_failures") as (tab, app, here):
        cu = _section_path(here, "cu", "service-life")
        _choose(tab, "service-life/service-life-table")

        def fail(*args, **kwargs):
            raise sync.SyncError("the state file is unreadable", "state_unreadable", file="sync.json", error="boom")

        with _patched(sync, record_local_edit=fail):
            tab.host.pane().add_row()
        assert _rows(_body(_text(cu), "service-life-table")) >= 1 and "service-life" in _text(cu)
        assert _banner(tab) == app.t("st_record_failed", error=tab.why(sync.SyncError("x", "state_unreadable", file="sync.json", error="boom"))), _banner(tab)
    with _open("structure_tab_sync_failures_bp", mode="bp") as (tab, app, here):
        _edit_object(_section_path(here, "cu", "service-life"), "p1", "Autre texte.")
        tab.refresh_sync()

        def refuse(*args, **kwargs):
            raise sync.SyncError("a file changed", "changed_meanwhile", file="service-life.typ")

        with _patched(sync, import_changes=refuse):
            assert tab.write_sync_import() is False
        assert "service-life.typ" in _banner(tab) and not re.search(r"[{}]", _banner(tab)) and not tab.banner.isHidden()


# --- the words -----------------------------------------------------------------------------------------------------

def test_the_words_are_in_three_languages_with_the_same_keys_and_no_hex_colour_is_written():
    import structure_words
    langs = structure_words.STRINGS
    assert set(langs) == {"fr", "de", "en"}
    keys = set(langs["fr"])
    assert keys == set(langs["de"]) == set(langs["en"]), (keys ^ set(langs["de"]), keys ^ set(langs["en"]))
    for key in keys:
        holes = {lang: set(re.findall(r"{(\w+)}", langs[lang][key])) for lang in langs}
        assert holes["fr"] == holes["de"] == holes["en"], (key, holes)
        for lang in langs:
            assert langs[lang][key].strip(), (lang, key)
    for key, text in langs["de"].items():
        assert "ß" not in text, key
    for key, text in langs["fr"].items():
        assert not re.search(r"[^\s  ][ ][:;?!»]", text) and not re.search(r"«[ ]", text), f"{key}: a French colon, semicolon or quotation needs the narrow no-break space: {text!r}"
    for lang in ("de", "en"):
        assert len([k for k in keys if langs[lang][k] == langs["fr"][k] and len(langs["fr"][k]) > 14]) < 6, "sentences left in French"
    for name in ("structure_tab.py", "structure_tree.py", "import_dialog.py", "structure_words.py"):
        source = conftest.module_source(TOOLS / name)   # with the parts split out of it (issue #30)
        assert not re.search(r"[\"']#[0-9a-fA-F]{3,8}[\"']", source), f"{name} writes a colour: they are the theme's"


def test_the_window_says_each_word_of_the_tab_as_the_tab_wrote_it():
    """The window merges every tab's words into one table and the later tab wins a key: the static models' tab wrote `st_remove`, `st_rename` and `st_moved` of its own, and «Id…» read «Renommer « {old} » en « {new} » ? Un appel #show-static-model(…)» in the real window -- which no test of the tab, built on its own words, could see. What the window holds for each key of this tab is the tab's own sentence, in the three languages, and the buttons carry the words of the keys they name."""
    _qt()
    import structure_tab
    import structure_words
    import woodcore_gui
    for lang in ("fr", "de", "en"):
        wrong = [key for key, text in structure_words.STRINGS[lang].items() if woodcore_gui.STRINGS[lang].get(key) != text]
        assert not wrong, (lang, wrong)
    assert structure_tab.BUTTON_WORDS == {"remove": "st_remove_button", "rename": "st_rename_button"}
    with _open("structure_tab_words") as (tab, app, here):
        window_words = {"t": lambda key, **v: woodcore_gui.STRINGS["fr"][key].format(**v) if v else woodcore_gui.STRINGS["fr"][key]}
        for key, button in tab.buttons.items():
            wanted = structure_words.STRINGS["fr"][structure_tab.BUTTON_WORDS.get(key, "st_" + key)]
            assert button.text() == wanted and window_words["t"](structure_tab.BUTTON_WORDS.get(key, "st_" + key)) == wanted, key


def test_every_refusal_of_the_five_modules_has_a_sentence_in_each_language_naming_only_what_the_refusal_carries():
    import doc_import
    import sharing
    import structure
    import structure_tab
    import structure_words
    import sync
    import typst_objects
    wanted = set(structure.CODES) | set(doc_import.CODES) | set(sharing.CODES) | set(typst_objects.CODES) | set(sync.CODES)
    assert wanted <= set(structure_words.CODES), sorted(wanted - set(structure_words.CODES))
    for lang in ("fr", "de", "en"):
        for code in structure_words.CODES:
            assert "st_why_" + code in structure_words.STRINGS[lang], (lang, code)
    # what a sentence may name is what its module says the refusal is about
    carried = {}
    for module in (structure, doc_import, sharing, sync):
        source = (ROOT / "calc" / f"{module.__name__}.py").read_text(encoding="utf-8")
        block = source[source.index("CODES = ("):]
        block = block[:block.index("\n)\n")]
        for code, note in re.findall(r'^\s*"(\w+)",\s*#\s*(.*)$', block, re.M):
            carried.setdefault(code, set()).update(re.findall(r"`(\w+)`", note))
        for code, call in re.findall(r'_refuse\(\s*"(\w+)",(.*?)\)\s*$', source, re.M | re.S):      # and what each call of the refusal passes
            carried.setdefault(code, set()).update(re.findall(r"(\w+)=", call))
    for code, names in carried.items():
        if "st_why_" + code not in structure_words.STRINGS["fr"]:
            continue
        for lang in ("fr", "de", "en"):
            holes = set(re.findall(r"{(\w+)}", structure_words.STRINGS[lang]["st_why_" + code]))
            assert holes <= names | {"id", "title"}, (lang, code, holes - names)
    # a refusal is said through the tab with what it carries, in the window's language, and never as a raw code
    with _open("structure_tab_why") as (tab, app, here):
        for code in sorted(wanted):
            exc = type("E", (), {"code": code, "values": {name: "X" for name in carried.get(code, ())}})()
            said = tab.why(exc)
            assert said and not re.search(r"[{}]", said) and said != code, (code, said)
        # an exception with no code of its own says what it carries
        assert tab.why(ValueError("une phrase")) == "une phrase"
        assert "disque" in tab.why(OSError("disque plein")) or "disque plein" in tab.why(OSError("disque plein"))
    assert structure_tab.WHY["cycle"] == "st_why_cycle"


# --- a project laid out as one report ----------------------------------------------------------------------------------

def test_a_project_laid_out_as_one_report_has_the_tab_on_its_report_and_writes_its_include_lines():
    _qt()
    import structure
    from fixtures import legacy_example
    here = legacy_example.build(conftest.tmpdir("structure_tab_legacy") / "Exemple", conftest.SAMPLE)
    for pdf in here.root.rglob("*.pdf"):
        pdf.unlink()
    project.sync_engine(here)
    with _open("structure_tab_legacy", mode="rs", here=here) as (tab, app, here):
        assert not here.has_modes
        assert tab.tree.ids() == [n.id for n in structure.flatten(structure.tree(here, "rs"))] and tab.tree.ids()
        assert tab.mode() == "rs"
        entry = here.document_typ("rs")
        original = entry.read_bytes()
        assert tab.write_enabled("007-literatur", False) is True
        assert '// #include "Sections/007-literatur.typ"' in entry.read_bytes().decode("utf-8")
        assert not tab.tree.node("007-literatur").enabled and tab.tree.row("007-literatur").checkState(0).value == 0
        # a section of the report tagged from the tab: the objects of the file appear under it, and the report prints as before
        node = next(n for n in structure.flatten(tab.nodes) if n.kind == "file" and n.id != "007-literatur")
        assert tab.write_tag(node.id) is True
        children = tab.tree.node(node.id).children
        assert children and all(c.kind == "object" for c in children), [c.kind for c in children]
        entry.write_bytes(original)


# --- the layout template of the project, from the «Projet» tab, and a style at `woodcore-cli new` ---------------------------------

def test_the_window_tells_its_tabs_when_the_layout_template_was_switched_and_the_tab_compiles_its_page_again():
    """«Propriétés du projet» opens the «Projet» tab (issue #87); a form applied there (issue #88) tells every tab that shows a compiled page, a title page saved does not."""
    _qt()
    import forms
    import project_tab
    import structure_tab
    import woodcore_gui
    from PySide6.QtWidgets import QMessageBox
    here = _copy("structure_tab_form_window")
    with project.using(here):
        window = woodcore_gui.MainWindow()
        try:
            window.lang = "fr"
            window.mode = "rs"
            window.rebuild()
            window.tab_widget.setCurrentWidget(next(t for t in window.tabs if isinstance(t, structure_tab.StructureTab)))
            window.edit_properties()
            assert window.tab_widget.currentIndex() == window.project_index(), "«Propriétés du projet» did not open the «Projet» tab"
            tab = next(t for t in window.tabs if isinstance(t, structure_tab.StructureTab))
            projet = next(t for t in window.tabs if isinstance(t, project_tab.ProjectTab))
            told = []
            with _patched(tab, on_properties_changed=lambda changed: told.append(changed)), \
                    _patched(QMessageBox, question=staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)):
                projet.fields["author"].setText("L. Exempel")
                projet.mark_dirty()
                assert projet.save() and project.current().detail("author") == "L. Exempel"
                assert told == [], told
                assert projet.write_apply_form("builtin:compact")
                assert told == [True] and forms.current(here).ref == "builtin:compact", told
        finally:
            conftest.dispose(window)
    # the tab itself: a layout template switched under it -- Template/ and title.typ, a config.typ of the new format left as it is -- compiles its page again, a change of nothing else does not
    with _open("structure_tab_form_tab") as (tab, app, here):
        asked = []
        tab.pane_loaded = True
        with _patched(tab, request_preview=lambda force=False: asked.append(force)):
            tab.form_seen = tab.form_signature()
            tab.on_properties_changed(False)
            assert asked == [], "nothing switched and the page was compiled again"
            forms.apply(here, forms.find("builtin:bfh"))
            tab.on_properties_changed(False)
            assert asked == [True], "a layout template switched and the page was not compiled again"
            forms.apply(here, forms.find("builtin:compact"))
            assert forms.is_form_config(here.config_typ)
            tab.on_properties_changed(False)
            assert asked == [True, True], "a config.typ of the new format left as it is hid the switch"


def test_woodcore_cli_new_takes_a_style():
    import cli
    import templates
    base = conftest.tmpdir("structure_tab_cli")
    assert cli.parser().parse_args(["new", "x", "--style", "compact"]).style == "compact"
    assert cli.parser().parse_args(["new", "x"]).style is None
    code = cli.main(["new", str(base / "Kompakt"), "--name", "Kompakt", "--language", "fr", "--style", "compact"])
    assert code == 0
    here = project.Project.load(base / "Kompakt" / "Kompakt.woodcore")
    text = here.config_typ.read_bytes().decode("utf-8")
    assert "size: 10pt" in text and '#let doc-lang = "fr"' in text, text[:400]
    assert templates.read_languages(here.document_typ("rs")) == ("fr", "fr")
    # none: the neutral look -- the builtin neutral layout template since 06.10.2026, the template's own config.typ byte for byte before it
    assert cli.main(["new", str(base / "Neutral"), "--name", "Neutral"]) == 0
    neutral = project.Project.load(base / "Neutral" / "Neutral.woodcore")
    import forms
    if forms.is_form_config(neutral.config_typ):
        assert forms.current(neutral).ref == "builtin:neutral"
    else:
        assert neutral.config_typ.read_bytes() == templates.standard().config.read_bytes()
    # an unknown one is refused, naming the valid ones, and leaves nothing behind
    import io
    from contextlib import redirect_stderr
    err = io.StringIO()
    with redirect_stderr(err):
        code = cli.main(["new", str(base / "Barock"), "--name", "Barock", "--style", "barock"])
    said = err.getvalue()
    assert code == 1 and "'barock'" in said and "neutral" in said.lower() and "compact" in said.lower(), said     # a style is a layout template since 06.10.2026, and the refusal names those there are
    assert not (base / "Barock").exists()


# --- the polish of 01.10.2026: the .typ mark, a row chosen, the section's pane, the preview ------------------------------------------------------

def test_the_typ_mark_and_its_legend_are_the_reports_alone():
    """In a convention d'utilisation and a base de projet every section is a file, so the `.typ` mark stood on every row and said nothing. In the report it tells which headings open a file of their own."""
    import structure
    import structure_tree
    for mode in ("cu", "bp"):
        with _open(f"structure_tab_typ_{mode}", mode=mode) as (tab, app, here):
            flat = structure.flatten(tab.nodes)
            assert any(n.separate_file for n in flat), "every section is a file of its own"
            assert tab.tree.isColumnHidden(structure_tree.TYP) and not tab.tree.typ_mark
            assert not any(tab.tree.row(n.id).text(structure_tree.TYP) for n in flat), "no row carries the mark"
            assert tab.legend.text() == app.t("st_legend_documents") and ".typ" not in tab.legend.text()
            assert "lien" in tab.legend.text() and "orange" in tab.legend.text() and "rouge" in tab.legend.text()
    with _open("structure_tab_typ_rs", mode="rs") as (tab, app, here):
        files = [n for n in structure.flatten(tab.nodes) if n.kind == "file"]
        assert files and not tab.tree.isColumnHidden(structure_tree.TYP) and tab.tree.typ_mark
        assert all(tab.tree.row(n.id).text(structure_tree.TYP) == ".typ" for n in files)
        assert not any(tab.tree.row(n.id).text(structure_tree.TYP) for n in structure.flatten(tab.nodes) if n.kind != "file")
        assert tab.legend.text() == app.t("st_legend") and tab.legend.text().startswith(".typ")
    # the window's drop-down moves from one document to the other: the mark and the legend follow
    with _open("structure_tab_typ_switch", mode="cu") as (tab, app, here):
        app.mode = "rs"
        tab.on_mode()
        assert not tab.tree.isColumnHidden(structure_tree.TYP) and tab.legend.text() == app.t("st_legend")
        assert any(tab.tree.row(i).text(structure_tree.TYP) == ".typ" for i in tab.tree.ids())
        app.mode = "bp"
        tab.on_mode()
        assert tab.tree.isColumnHidden(structure_tree.TYP) and tab.legend.text() == app.t("st_legend_documents")
    for lang in ("fr", "de", "en"):
        import structure_words
        assert ".typ" in structure_words.STRINGS[lang]["st_legend"] and ".typ" not in structure_words.STRINGS[lang]["st_legend_documents"], lang


def _pixels_near(image, colour, within=70):
    """How many pixels of `image` are within `within` of `colour` (RGB distance)."""
    wanted = (colour.red(), colour.green(), colour.blue())
    count = 0
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            if sum((a - b) ** 2 for a, b in zip((pixel.red(), pixel.green(), pixel.blue()), wanted)) <= within * within:
                count += 1
    return count


def _row_image(tab, node_id):
    """The title cell of a row, as the tree draws it -- the viewport grabbed, so that the delegate's painting is what is read."""
    from PySide6.QtCore import QRect
    tab.tree.setUniformRowHeights(True)
    row = tab.tree.row(node_id)
    tab.tree.scrollToItem(row)
    rect = tab.tree.visualRect(tab.tree.indexFromItem(row, 0))
    full = tab.tree.viewport().grab()
    return full.toImage().copy(QRect(rect.left() + 20, rect.top(), max(rect.width() - 20, 1), rect.height()))


def test_a_row_chosen_keeps_its_own_colour_orange_red_or_grey_and_the_selection_grounds_the_whole_cell():
    """The style sheet gives a selected item the ink of the scheme, which turned an orange or red row dark at the very moment the engineer looked at it. The delegate paints a selected row itself: the selection's ground, then the row in its own ink."""
    _qt()
    import structure
    import theme
    from PySide6.QtGui import QColor
    with _open("structure_tab_selected_ink", mode="bp") as (tab, app, here):
        _edit_object(_section_path(here, "cu", "service-life"), "p1", "Un nouveau texte de la durée d'utilisation.")
        tab.refresh_sync()
        tab.resize(1400, 900)
        tab.show()          # the tree is laid out only inside a tab that is shown
        tab.tree.expandAll()
        _pump(0.1)
        orange, ink, ground = QColor(theme.colour("override")), QColor(theme.colour("ink")), QColor(theme.colour("accent-soft"))
        assert _ink(tab, "service-life/p1") == orange.name()
        tab.tree.select_ids([])
        plain = _row_image(tab, "service-life/p1")
        assert _pixels_near(plain, orange) > 15, "the row is orange where nobody chose it"
        tab.tree.select("service-life/p1")
        _pump(0.05)
        chosen = _row_image(tab, "service-life/p1")
        assert _pixels_near(chosen, orange) > 15, "a row chosen keeps its orange"
        assert _pixels_near(chosen, ink, 40) == 0, "...and no dark ink of the scheme"
        assert _pixels_near(chosen, ground, 6) > chosen.width() * chosen.height() // 3, "the selection's ground fills the cell"
        # a row with no state of its own is drawn in the scheme's ink, chosen or not
        quiet = "scope-and-limits"
        tab.tree.select(quiet)
        _pump(0.05)
        assert _pixels_near(_row_image(tab, quiet), ink, 40) > 15
        # a row that is not printed keeps its grey, chosen
        node = next(n for n in structure.flatten(tab.nodes) if n.kind == "file" and not n.enabled)
        muted = QColor(theme.colour("muted"))
        tab.tree.select(node.id)
        _pump(0.05)
        assert _pixels_near(_row_image(tab, node.id), muted, 40) > 10, "a section not printed stays grey while it is chosen"
        assert _pixels_near(_row_image(tab, node.id), ink, 25) == 0


def test_a_conflict_row_chosen_stays_red():
    _qt()
    import theme
    from PySide6.QtGui import QColor
    with _open("structure_tab_selected_red", mode="bp") as (tab, app, here):
        _edit_object(_section_path(here, "cu", "service-life"), "p1", "Texte de la convention.")
        _edit_object(_section_path(here, "bp", "service-life"), "p1", "Texte de la base de projet.")
        tab.refresh_sync()
        tab.resize(1400, 900)
        tab.show()          # the tree is laid out only inside a tab that is shown
        tab.tree.expandAll()
        _pump(0.1)
        red = QColor(theme.colour("danger"))
        assert _ink(tab, "service-life/p1") == red.name()
        tab.tree.select("service-life/p1")
        _pump(0.05)
        assert _pixels_near(_row_image(tab, "service-life/p1"), red) > 15


def test_the_preview_pane_has_the_biggest_share_of_the_tab_and_the_three_add_up():
    import structure_tab
    assert abs(sum(structure_tab.SHARES) - 1.0) < 1e-9
    tree, page, options = structure_tab.SHARES
    assert page > tree and page > options and page >= 0.42, "the preview is what is read, and its text is as large as the pane is wide"
    assert options >= 0.29, "the fields of a table row need the room"


def test_a_section_pane_carries_the_title_of_its_first_heading_tagged_file_or_not_and_writes_it_through_the_model():
    import object_panes
    import structure
    with _open("structure_tab_section_title") as (tab, app, here):
        _choose(tab, "purpose")
        assert tab.host.kind == "section"
        pane = tab.host.pane()
        node = tab.tree.node("purpose")
        assert any(c.kind == "object" for c in node.children), "the file is tagged: its heading is an object"
        assert pane.title_edit.isVisibleTo(pane) and pane.title_edit.text() == structure.plain_title(node.title)
        assert pane.file_note.text() == object_panes.text("op_file", "fr", file="Sections/purpose.typ")
        path = _section_path(here, "cu", "purpose")
        before = _text(path)
        heading = next(c for c in node.children if c.kind == "object" and c.object_type == "heading")
        pane.title_edit.textEdited.emit("Zweck, neu gefasst")
        pane.flush()
        after = _text(path)
        assert _body(after, heading.object_id) == "== Zweck, neu gefasst", _body(after, heading.object_id)
        assert _outside(after, heading.object_id) == _outside(before, heading.object_id), "nothing of the file but the heading's own body changed"
        assert tab.tree.node("purpose").title == "Zweck, neu gefasst" and tab.tree.row("purpose").text(0) == "Zweck, neu gefasst"
        assert tab.tree.row(heading.id).text(0) == "Zweck, neu gefasst" and tab.host.pane() is pane and tab.tree.selected_ids() == ["purpose"]
        assert not _banner(tab)
        # a title emptied to be typed again is not written
        pane.title_edit.textEdited.emit("")
        pane.flush()
        assert _body(_text(path), heading.object_id) == "== Zweck, neu gefasst"


def test_the_title_of_a_shared_section_is_the_documents_own_and_its_text_is_what_the_other_document_sees_as_incoming():
    """The title stands before the shared block -- the two documents place a shared section at different depths, so each writes its heading at its own level (06.10.2026) -- so renaming it is no edit of the block; a paragraph inside the block is, and the other document sees it as incoming."""
    import sync
    with _open("structure_tab_shared_title") as (tab, app, here):
        _choose(tab, "service-life")
        pane = tab.host.pane()
        assert "bp" in tab.tree.node("service-life").shared_with
        assert not sync.status(here, "bp").incoming
        pane.title_edit.textEdited.emit("Nutzungsdauer, neu")
        pane.flush()
        assert not sync.status(here, "bp").incoming, "the title is the document's own and not part of the shared block"
        paragraph = next(c for c in tab.tree.node("service-life").children if c.kind == "object" and c.object_type == "text")
        _choose(tab, paragraph.id)
        text_pane = tab.host.pane()
        text_pane.edit.setPlainText("Ein neuer Absatz im gemeinsamen Block.")
        text_pane.flush()
        incoming = sync.status(here, "bp").incoming
        assert "service-life" in incoming, incoming
        assert not _banner(tab)


def _icon_colour(icon):
    """The colour a small icon is drawn in: its most opaque pixel's, as a name."""
    from PySide6.QtGui import QColor
    image = icon.pixmap(14, 14).toImage()
    best = None
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            if best is None or pixel.alpha() > best.alpha():
                best = pixel
    return QColor(best.red(), best.green(), best.blue()).name()


def test_the_sections_pane_shares_the_file_with_another_document_and_stops_sharing_and_the_link_mark_is_greyed():
    import structure_tree
    import theme
    from PySide6.QtGui import QColor
    with _open("structure_tab_share") as (tab, app, here):
        _choose(tab, "purpose")
        pane = tab.host.pane()
        assert tab.tree.node("purpose").shared_with == () and tab.tree.row("purpose").icon(structure_tree.LINK).isNull()
        assert pane.share_card.isVisibleTo(pane) and not pane.stop_button.isEnabled()
        offered = []
        tab.ask_share = lambda node: (offered.append((node.id, list(node.shared_with))) or ["bp"])
        pane.share_button.click()
        assert offered == [("purpose", [])] and not _banner(tab)
        assert _section_path(here, "bp", "purpose").exists() and "woodcore:shared" in _text(_section_path(here, "cu", "purpose"))
        assert tab.tree.node("purpose").shared_with == ("bp",) and not tab.tree.row("purpose").icon(structure_tree.LINK).isNull()
        assert tab.tree.selected_ids() == ["purpose"], "the file stays chosen"
        pane = tab.host.pane()
        assert "Base de projet" in pane.share_note.text() and pane.stop_button.isEnabled()
        assert any("purpose.typ" in said and "Base de projet" in said for said in app.statuses)
        assert "purpose" in _sections(here, "bp"), "the other document's structure lists the section"
        assert _icon_colour(tab.tree.row("purpose").icon(structure_tree.LINK)) == QColor(theme.colour("accent-strong")).name()
        # stopping asks first, and a no changes nothing
        tab.ask_confirm = lambda text: False
        pane.stop_button.click()
        assert "woodcore:shared" in _text(_section_path(here, "cu", "purpose")) and not tab.stopped_ids()
        asked = []
        tab.ask_confirm = lambda text: asked.append(text) or True
        pane.stop_button.click()
        assert len(asked) == 1 and "Objet de la convention" in asked[0] and "indépendante" in asked[0]
        assert "woodcore:shared" not in _text(_section_path(here, "cu", "purpose")), "this copy's tags are taken off"
        assert _section_path(here, "bp", "purpose").exists(), "the other document keeps its copy"
        assert tab.stopped_ids() == {"purpose"} and tab.tree.node("purpose").shared_with == ()
        link = tab.tree.row("purpose").icon(structure_tree.LINK)
        assert not link.isNull() and _icon_colour(link) == QColor(theme.colour("muted")).name(), "the link mark is greyed: the sharing was stopped"
        assert tab.tree.row("purpose").toolTip(structure_tree.LINK) == app.t("st_tip_stopped")
        pane = tab.host.pane()
        assert pane.share_note.text() == "Cette section n'est partagée avec aucun autre document." and not pane.stop_button.isEnabled()
        assert any("n'est plus partagée" in said for said in app.statuses)
        # the greyed mark outlives a reload of the tree; a row never shared has none
        tab.reload()
        assert not tab.tree.row("purpose").icon(structure_tree.LINK).isNull()
        assert tab.tree.row("introduction").icon(structure_tree.LINK).isNull()
        # ... and a rebuilt window (a language switch) carries it
        import structure_tab
        state = tab.view_state()
        assert state["stopped"] == {"cu": ["purpose"]}
        app2 = FakeApp()
        app2.views["tab_structure"] = state
        again = structure_tab.StructureTab(app2)
        try:
            assert again.stopped_ids() == {"purpose"} and not again.tree.row("purpose").icon(structure_tree.LINK).isNull()
        finally:
            again.pane.stop()
            again.stop_watching()
            again.deleteLater()


def test_a_refusal_to_share_is_said_in_the_banner_by_its_code_and_the_greyed_marks_belong_to_the_document_they_were_made_in():
    import structure_tree
    with _open("structure_tab_share_refusal") as (tab, app, here):
        _choose(tab, "service-life")
        assert "bp" in tab.tree.node("service-life").shared_with
        # the other document holds a copy already: said in the window's words with what the refusal carries, never as a code
        assert tab.write_share("service-life", ["bp"]) is False
        said = _banner(tab)
        assert "Base de projet" in said and "service-life" in said and "?" not in said and not re.search(r"[{}]", said), said
        assert tab.write_share("service-life", ["cu"]) is False and _banner(tab) and _banner(tab) != said, "the section's own document is refused too"
        # sharing stopped marks the file; sharing a file marks none, and clears the mark of one that is shared again
        tab.ask_confirm = lambda text: True
        assert tab.write_stop_share("service-life") is True
        assert tab.stopped_ids() == {"service-life"} and tab.tree.row("service-life").toolTip(structure_tree.LINK) == app.t("st_tip_stopped")
        tab.stopped_ids().add("purpose")
        assert tab.write_share("purpose", ["bp"]) is True and tab.stopped_ids() == {"service-life"}
        # a refusal of the stop: a file shared with nobody
        assert tab.write_stop_share("introduction") is False and _banner(tab)
        # the marks of one document are not the marks of another
        app.mode = "bp"
        tab.on_mode()
        assert tab.stopped_ids() == set() and tab.tree.stopped == set()
        app.mode = "cu"
        tab.on_mode()
        assert tab.stopped_ids() == {"service-life"} and tab.tree.stopped == {"service-life"}


def test_the_share_dialog_lists_the_other_documents_and_answers_the_ones_ticked():
    _qt()
    import import_dialog
    import structure_words
    from PySide6.QtWidgets import QLabel

    def t(key, **values):
        text = structure_words.STRINGS["fr"][key]
        return text.format(**values) if values else text

    dialog = import_dialog.ShareDialog(None, t, "Zweck", [("bp", "Base de projet", False), ("rs", "Rapport de statique", False)])
    ok = lambda d: d.buttons.button(d.buttons.StandardButton.Ok)   # noqa: E731
    assert dialog.windowTitle() == t("st_share_title") and len(dialog.boxes) == 2
    assert dialog.values() == [] and not ok(dialog).isEnabled()
    dialog.boxes[1].setChecked(True)
    assert dialog.values() == ["rs"] and ok(dialog).isEnabled()
    dialog.boxes[0].setChecked(True)
    assert dialog.values() == ["bp", "rs"]
    # a document the section is shared with already is ticked and closed, and is not part of the answer
    dialog = import_dialog.ShareDialog(None, t, "Zweck", [("bp", "Base de projet", True), ("rs", "Rapport de statique", False)])
    assert dialog.boxes[0].isChecked() and not dialog.boxes[0].isEnabled() and "déjà partagée" in dialog.boxes[0].text()
    assert dialog.boxes[1].isChecked() and dialog.values() == ["rs"], "a single open document is ticked"
    # nobody to share with: the dialog says so and cannot be accepted
    for listed in ([("bp", "Base de projet", True)], []):
        nobody = import_dialog.ShareDialog(None, t, "Zweck", listed)
        assert nobody.values() == [] and not ok(nobody).isEnabled()
        assert any(label.text() == t("st_share_nobody") for label in nobody.findChildren(QLabel))


def test_the_tab_asks_the_share_dialog_with_the_other_documents_and_the_ones_the_file_is_shared_with_already_and_a_project_held_read_only_shares_nothing():
    _qt()
    import import_dialog
    import structure_tree
    seen = []

    class Spy:
        def __init__(self, parent, t, title, listed):
            seen.append((title, listed))

        def exec(self):
            from PySide6.QtWidgets import QDialog
            return QDialog.DialogCode.Rejected

        def values(self):
            return ["never"]

    with _open("structure_tab_ask_share") as (tab, app, here):
        del tab.ask_share           # the real question, whose dialog is the spy
        with _patched(import_dialog, ShareDialog=Spy):
            shared = tab.tree.node("service-life")
            assert tab.ask_share(shared) is None
            title, listed = seen[-1]
            assert title == structure_tree.display_title(shared)
            assert listed == [("bp", "Base de projet", True), ("rs", "Rapport de statique", "rs" in shared.shared_with)]
            tab.ask_share(tab.tree.node("purpose"))
            assert seen[-1][1] == [("bp", "Base de projet", False), ("rs", "Rapport de statique", False)]
    with _open("structure_tab_ask_share_ro", read_only=True) as (tab, app, here):
        _choose(tab, "purpose")
        tab.ask_share = _unexpected("ask_share")
        tab.ask_confirm = _unexpected("ask_confirm")
        tab.on_share()
        tab.on_stop_share()
        assert app.refused == 2, "the window says once for each refused write"
        assert not _section_path(here, "bp", "purpose").exists() and "woodcore:shared" not in _text(_section_path(here, "cu", "purpose"))


# --- the whole document, and the headings at the level they print at (06.10.2026) ------------------------------

def test_the_whole_document_is_a_row_of_its_own_at_the_top_with_no_box_and_nothing_under_it():
    """«Tout en haut de cette arborescence, pouvoir cliquer sur tout afficher»: a row at the top, a sibling of the first chapter -- nothing indented one step further for it --, no box, chosen whenever nothing else is, and what it shows is the whole document."""
    import structure_tree
    from PySide6.QtCore import Qt
    with _open("structure_tab_whole") as (tab, app, here):
        whole = tab.tree.whole
        assert whole is not None and tab.tree.topLevelItem(0) is whole and whole.text(0) == app.t("st_whole_document")
        assert whole.childCount() == 0 and whole.parent() is None, "the whole document's row is not the parent of the chapters"
        assert tab.tree.topLevelItem(1) is tab.tree.row("introduction"), "the first chapter is a sibling of the whole document's row"
        assert not whole.flags() & Qt.ItemFlag.ItemIsUserCheckable and not whole.flags() & Qt.ItemFlag.ItemIsDragEnabled
        assert whole.data(0, Qt.ItemDataRole.CheckStateRole) is None, "the whole document's row carries a box"
        _clear(tab)
        assert whole.isSelected() and tab.tree.selected_id() == "" and tab.tree.selected_ids() == [], "nothing chosen is the whole document, and its row says so"
        _choose(tab, "purpose")
        assert not whole.isSelected() and tab.tree.selected_ids() == ["purpose"]
        # choosing it chooses nothing else: the page is the document's
        tab.tree.select_ids([structure_tree.WHOLE_ID], structure_tree.WHOLE_ID)
        tab.on_selection_changed()
        assert tab.tree.selected_ids() == [] and tab.host.kind is None


def _laid_out_with_offsets(here):
    """The convention and the base of `here` written back the way a project made before 06.10.2026 has them: every section's headings starting at level 1, the chapters' titles in the entry's block and no file of their own, no `"headings"` key. Returns {path: bytes} of what they held before."""
    import structure
    import typst_paths
    before = {}
    for mode in ("cu", "bp"):
        folder = here.document_dir(mode)
        path = here.structure_file(mode)
        source = structure.read(path)
        for node, _depth, _parent in structure.walk(source):
            if "children" in node:
                group = folder / structure.group_file(node["id"])
                before[group] = group.read_bytes()
                group.unlink()
            else:
                file = folder / node["file"]
                before[file] = file.read_bytes()
                typst_paths.write_text(file, structure.fit_text(typst_paths.read_text(file), 1))
        before[path] = path.read_bytes()
        del source["headings"]
        structure.write(path, source)
        before[here.document_typ(mode)] = here.document_typ(mode).read_bytes()
        structure.sync_entry(here.document_typ(mode), path, structure.document_language(here, mode))
    return before


def test_a_document_laid_out_with_offsets_is_offered_its_headings_at_their_level_and_comes_back_as_the_templates_write_it():
    """A convention and a base made before 06.10.2026 -- `=` in every file, the chapters' titles in the entry -- are said in a banner with one button; on a yes the two are converted together, and they come back byte for byte as the templates write them: each heading at the level it prints at, every chapter a file of its own, a shared section's title before its block."""
    import structure
    with _open("structure_tab_levels") as (tab, app, here):
        assert not tab.relative_levels() and not tab.levels_box.isVisibleTo(tab), "a document laid out as the templates are is offered nothing"
        before = _laid_out_with_offsets(here)
        tab.reload()
        tab.update_banner()
        assert tab.relative_levels() and tab.levels_box.isVisibleTo(tab), "the banner does not offer to convert a document laid out with offsets"
        # a no writes nothing
        with _patched(tab, ask_confirm=lambda words: False):
            assert tab.on_make_absolute() is False
        assert not structure.is_absolute(structure.read(here.structure_file("cu")))
        asked = []
        with _patched(tab, ask_confirm=lambda words: asked.append(words) or True):
            assert tab.on_make_absolute() is True
        assert asked == [app.t("st_levels_ask")]
        for mode in ("cu", "bp"):
            assert structure.is_absolute(structure.read(here.structure_file(mode))), mode
        changed = [str(path) for path, data in before.items() if path.read_bytes().replace(b"\r\n", b"\n") != data.replace(b"\r\n", b"\n")]
        assert not changed, changed[:5]
        assert not tab.levels_box.isVisibleTo(tab) and not _banner(tab)
        assert tab.tree.row("introduction") is not None and tab.tree.node("introduction").file == "Sections/introduction.typ"

