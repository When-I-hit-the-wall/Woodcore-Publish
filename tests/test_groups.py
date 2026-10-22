"""Folders in the left pane of the editor tabs -- `calc/tools/grouped_list.py` (docs/ui/window.md §10quater).

A project grows a plan per building, a model per beam and a connector per node, and a flat list of forty is a list nobody reads. The engineer asked for folders, drag and drop, and the Ctrl/Shift selection of the Windows explorer.

What has to be held is the decision underneath, because everything downstream rests on it: **a folder is a field, not a directory**. The ids stay flat, so the rule that decides the whole pipeline -- *the id is the file name* (section 3.3quinquies) -- is untouched, no `show-*` call changes, and no report can break because somebody tidied a list. The tests below are written on that: a move writes a field, never a path, and the set of ids is the same before and after.

⚠️ Skipped where PySide6 is not installed: a machine that only builds the report is a legitimate machine. Everything is built off-screen; a test run must never open a window.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import sys

from conftest import ROOT, Skip

SOURCE_SCHEMAS = ("plan-source", "statics-source", "connection-source", "connector-source")
_qt = None


def _gl():
    global _qt
    if _qt is None:
        path = str(ROOT / "calc" / "tools")
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        import grouped_list
        QApplication.instance() or QApplication([])
        _qt = grouped_list
    return _qt


def _entries():
    return [
        {"id": "SD_01", "text": "SD_01", "group": "Halle"},
        {"id": "SD_02", "text": "SD_02", "group": "Halle"},
        {"id": "SD_09", "text": "SD_09", "group": ""},
    ]


def _rows(widget):
    return [widget.topLevelItem(i).text(0) for i in range(widget.topLevelItemCount())]


# --- the field ----------------------------------------------------------------

def test_a_source_with_no_group_reads_as_the_root():
    """Absent, empty, whitespace and a non-string all mean the root, so a file written before folders existed needs no migration."""
    gl = _gl()
    assert gl.group_of({}) == gl.ROOT_GROUP
    assert gl.group_of({"group": ""}) == gl.ROOT_GROUP
    assert gl.group_of({"group": "   "}) == gl.ROOT_GROUP
    assert gl.group_of({"group": None}) == gl.ROOT_GROUP
    assert gl.group_of({"group": 3}) == gl.ROOT_GROUP
    assert gl.group_of({"group": " Halle "}) == "Halle"


def test_the_folders_are_derived_from_the_sources():
    """A folder is never declared anywhere: it is the set of `group` values in use, sorted for a reader."""
    gl = _gl()
    assert gl.folders_in([{"group": "b"}, {"group": "A"}, {"group": ""}, {}]) == ["A", "b"]


def test_every_source_schema_documents_group_and_none_requires_it():
    """Optional and additive: a source that has never heard of folders is still valid, which is why no schema_version was bumped."""
    for name in SOURCE_SCHEMAS:
        schema = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert "group" in schema["properties"], f"{name} does not document `group`"
        assert "group" not in schema.get("required", []), f"{name} requires `group`, so an older file would be refused"


# --- the widget ---------------------------------------------------------------

def test_a_folder_holds_its_entries_and_the_root_holds_the_rest():
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.set_entries(_entries(), empty_folders=["Pavillon"])
    assert _rows(widget) == ["Halle", "Pavillon", "SD_09", "Archives"], "«Archives» is the last row, after the root's own entries (v0.77)"
    halle = widget.topLevelItem(0)
    assert [halle.child(i).text(0) for i in range(halle.childCount())] == ["SD_01", "SD_02"]


def test_an_empty_folder_survives_a_rebuild():
    """It cannot live in the project -- no source names it -- so the window keeps it, and a reload must not lose it."""
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.set_entries(_entries(), empty_folders=["Pavillon"])
    kept = widget.empty_folders()
    assert kept == ["Pavillon"]
    widget.set_entries(_entries(), empty_folders=kept)
    assert "Pavillon" in _rows(widget)


def test_a_folder_that_has_gained_an_entry_is_no_longer_empty():
    """Otherwise it would be listed twice over -- once as a real folder and once as one the window remembers."""
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["fr"])
    entries = _entries() + [{"id": "SD_11", "text": "SD_11", "group": "Pavillon"}]
    widget.set_entries(entries, empty_folders=["Pavillon"])
    assert widget.empty_folders() == []
    assert _rows(widget).count("Pavillon") == 1


def test_selecting_and_reading_back():
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.set_entries(_entries(), select="SD_02")
    assert widget.current_id() == "SD_02"
    assert widget.select("SD_09") and widget.current_id() == "SD_09"
    assert not widget.select("nothing-of-the-sort")
    assert sorted(widget.ids()) == ["SD_01", "SD_02", "SD_09"]


def test_select_makes_an_entry_the_selection_alone_whatever_ctrl_the_application_last_saw():
    """v0.116 (WP-K): `select` on an entry not selected set it current with Qt's default command, which reads the application's keyboard modifiers -- so a Ctrl the application last saw held (a click with Ctrl sent by an earlier test, test_document_view's, or one still down in the window) kept the previous entry selected beside the new one, and «Nouveau» in «Moyens d'assemblage» came out with two rows selected in the full suite only. Planted back -- `setCurrentItem(item)` alone -- this fails."""
    gl = _gl()
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QWidget
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.set_entries(_entries(), select="SD_02")
    other = QWidget()
    other.resize(40, 40)
    QTest.mouseClick(other, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, QPoint(5, 5))
    try:
        assert QGuiApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier, "the test no longer leaves Ctrl held: it tests nothing"
        assert widget.select("SD_09")
        assert widget.selected_ids() == ["SD_09"], widget.selected_ids()
    finally:
        QTest.mouseClick(other, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(5, 5))


def test_a_move_carries_the_whole_selection_and_names_the_folder():
    """Ctrl and Shift select several; the drop must report all of them, or a multiple drag would move one file."""
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.set_entries(_entries())
    seen = []
    widget.moved.connect(lambda ids, group: seen.append((sorted(ids), group)))
    widget.selectAll()
    widget._remove_folder(widget.topLevelItem(0))     # what «Supprimer le dossier» does: its entries go to the root
    assert seen and seen[-1][1] == gl.ROOT_GROUP
    assert seen[-1][0] == ["SD_01", "SD_02"], "removing a folder must move exactly what it held"


def test_removing_a_folder_never_removes_what_is_in_it():
    """The one thing a tidy-up must not do. The entries go back to the root and the widget says so; nothing is deleted here at all."""
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.set_entries(_entries())
    before = sorted(widget.ids())
    moved = []
    widget.moved.connect(lambda ids, group: moved.append((list(ids), group)))
    widget._remove_folder(widget.topLevelItem(0))
    widget.set_entries([dict(e, group="" if e["group"] == "Halle" else e["group"]) for e in _entries()])
    assert sorted(widget.ids()) == before, "an id changed, or one went missing, when a folder was removed"


# --- what the engineer asked for at the end of v0.77 ------------------------------

def test_a_ctrl_selection_survives_the_list_being_rebuilt():
    """«il doit être possible de sélectionner plusieurs fichiers en maintenant CTRL». A click loads the entry and loading rebuilds the list, whose `clear()` took the selection with it: Ctrl+click only ever held the last entry clicked. Planted back -- no selection restored in set_entries -- this fails on the first assertion."""
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.set_entries(_entries())
    for entry_id in ("SD_01", "SD_09"):
        widget._item_for(entry_id).setSelected(True)
    widget.set_entries(_entries(), select="SD_09")      # what a tab does when it loads the entry clicked
    assert sorted(widget.selected_ids()) == ["SD_01", "SD_09"], widget.selected_ids()
    assert widget.current_id() == "SD_09"
    assert widget.select("SD_01") and sorted(widget.selected_ids()) == ["SD_01", "SD_09"], "moving the current entry undid the selection"


def test_a_folder_stays_when_its_last_entry_leaves_and_goes_when_removed():
    """«Les dossiers doivent continuer à exister même s'ils sont vides». A folder is derived from the `group` values in use, so moving the last file out of one made it vanish; one removed from its menu must still go."""
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.set_entries(_entries())
    emptied = [dict(e, group="") for e in _entries()]
    widget.set_entries(emptied, empty_folders=widget.empty_folders())
    assert "Halle" in _rows(widget) and widget.empty_folders() == ["Halle"]
    widget.set_entries(_entries(), empty_folders=widget.empty_folders())
    widget._remove_folder(widget.topLevelItem(0))
    widget.set_entries(emptied, empty_folders=widget.empty_folders())
    assert "Halle" not in _rows(widget), "a folder removed from its menu came back"


def test_archives_is_the_last_row_and_is_never_opened():
    """«le fichier doit apparaître dans un dossier Archives qui se trouvera toujours tout en bas». An archived entry is listed under it, is not a tab's entry (`ids`, `rows`, `current_id`), and choosing it asks no tab to open it."""
    gl = _gl()
    widget = gl.GroupedList(gl.STRINGS["de"], lang="de")
    archived = [{"id": "archive:260916-224000-SD_03.json", "text": "SD_03"}]
    widget.set_entries(_entries(), archived=archived)
    last = widget.topLevelItem(widget.topLevelItemCount() - 1)
    assert last.text(0) == "Archiv" and last.childCount() == 1
    assert "archive:260916-224000-SD_03.json" not in widget.ids()
    assert widget.archived_ids() == ["archive:260916-224000-SD_03.json"]
    opened = []
    widget.currentIdChanged.connect(opened.append)
    widget.setCurrentItem(last.child(0))
    assert opened == [] and widget.current_id() is None
    assert widget.selected_archives() == ["archive:260916-224000-SD_03.json"]
    assert "Archiv" in widget._existing(), "a folder of the project named like the shelf would be mistaken for it"


def test_the_widget_speaks_the_window_s_language():
    """A tab hands over its own STRINGS, which carry no `grp_` word: until v0.77 the folder menu said French in a German window."""
    gl = _gl()
    assert gl.GroupedList({}, lang="de")._t("grp_new", "?") == "Neuer Ordner…"
    assert gl.GroupedList({}, lang="en")._t("grp_restore", "?") == "Restore"


def test_archiving_frees_the_id_and_restoring_takes_one_from_the_name():
    """«Lorsqu'on supprime un fichier, son ID doit être supprimé, puis le fichier doit apparaître dans un dossier Archives». The file moves into archives/, which no exporter's `*.json` glob reaches, with its `id` taken out; restoring writes it back under an ID made from its name, unique among those in use."""
    conftest_dir = __import__("conftest").tmpdir("archive_module")
    _gl()
    import source_archive
    source = {"schema_version": "1.1", "id": "S01", "group": "Halle", "name": "Träger Nord", "label": "Dach"}
    (conftest_dir / "S01.json").write_text(json.dumps(source), encoding="utf-8")
    key = source_archive.archive(conftest_dir, "S01")
    assert not (conftest_dir / "S01.json").exists() and "s01" not in source_archive.taken_ids(conftest_dir)
    assert [p.name for p in conftest_dir.glob("*.json")] == [], "an archived file is still where the export reads"
    stored = json.loads(source_archive._path(conftest_dir, key).read_text(encoding="utf-8"))
    assert "id" not in stored and "group" not in stored and stored["archived"]["id"] == "S01"
    rows = source_archive.entries(conftest_dir)
    assert [r["id"] for r in rows] == [key] and rows[0]["text"] == "Träger Nord — Dach"
    (conftest_dir / "Trager_Nord.json").write_text("{}", encoding="utf-8")   # the name's own ID is taken
    sid = source_archive.restore(conftest_dir, key, "Pavillon")
    assert sid == "Trager_Nord-2", sid
    back = json.loads((conftest_dir / f"{sid}.json").read_text(encoding="utf-8"))
    assert back["id"] == sid and back["group"] == "Pavillon" and "archived" not in back
    assert list(back)[:2] == ["schema_version", "id"]
    assert source_archive.entries(conftest_dir) == []
    key = source_archive.archive(conftest_dir, sid)
    source_archive.purge(conftest_dir, key)
    assert source_archive.entries(conftest_dir) == [] and not (conftest_dir / f"{sid}.json").exists()


def test_the_three_languages_carry_the_same_keys():
    """`_check_strings` in woodcore_gui checks its own STRINGS; this widget's are merged in from here."""
    gl = _gl()
    keys = {lang: set(texts) for lang, texts in gl.STRINGS.items()}
    assert set(keys) == {"fr", "de", "en"}
    assert keys["fr"] == keys["de"] == keys["en"]
    assert all(k.startswith("grp_") for k in keys["fr"]), "a key without the grp_ prefix could be taken by another module"


# --- v0.116: folders and files told apart, root files flush, a multiple selection dragged whole ----------------

def _shown(gl, entries=None, **kw):
    """A list shown off-screen, so that rows have a geometry (visualItemRect) -- the one thing these checks read."""
    from PySide6.QtWidgets import QApplication
    widget = gl.GroupedList(gl.STRINGS["fr"])
    widget.resize(320, 420)
    widget.set_entries(entries or _entries(), **kw)
    widget.show()
    QApplication.processEvents()
    return widget


def _centre(widget, item):
    return widget.visualItemRect(item).center()


def _mouse(kind, point, buttons, button=None):
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    point = QPointF(point)
    return QMouseEvent(kind, point, point, button if button is not None else Qt.MouseButton.LeftButton, buttons, Qt.KeyboardModifier.NoModifier)


def test_a_folder_and_a_file_are_told_apart():
    """«on ne comprend pas très bien ce qui est un fichier et ce qui est un dossier». A folder carries a folder icon, drawn at its own size, and a semibold face; a file keeps the plain face and the slot of its dot of unsaved changes. «Archives» keeps its italic."""
    gl = _gl()
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QStyleOptionViewItem
    widget = _shown(gl)
    try:
        folder = widget.topLevelItem(0)
        leaf = next(widget.topLevelItem(i) for i in range(widget.topLevelItemCount()) if widget.topLevelItem(i).data(0, gl.KIND_ROLE) == "leaf")
        assert folder.data(0, gl.KIND_ROLE) == "folder"
        assert not folder.icon(0).isNull(), "a folder has no icon"
        assert folder.font(0).weight() == QFont.Weight.DemiBold and leaf.font(0).weight() != QFont.Weight.DemiBold
        before = folder.icon(0).pixmap(16).toImage()
        folder.setExpanded(not folder.isExpanded())        # the icon follows the folder's state
        assert folder.icon(0).pixmap(16).toImage() != before, "an open folder and a shut one have the same icon"
        shelf = widget.topLevelItem(widget.topLevelItemCount() - 1)
        assert shelf.font(0).italic() and not shelf.icon(0).isNull()
        opt = QStyleOptionViewItem()
        widget.itemDelegate().initStyleOption(opt, widget.indexFromItem(folder))
        assert opt.decorationSize.width() == gl.FOLDER_PX, "a folder's icon is drawn at the dot's size"
    finally:
        widget.close()


def test_a_root_file_stands_where_a_folder_does_and_only_a_file_in_a_folder_is_indented():
    """«lorsque des fichiers ne sont pas dans un dossier, on a déjà l'impression qu'ils y sont car ils sont indentés». The root has no arrow column: a file in no folder starts at the same x as a folder, and one in a folder starts further right."""
    gl = _gl()
    widget = _shown(gl)
    try:
        folder = widget.topLevelItem(0)
        root_file = next(widget.topLevelItem(i) for i in range(widget.topLevelItemCount()) if widget.topLevelItem(i).data(0, gl.KIND_ROLE) == "leaf")
        inside = folder.child(0)
        assert widget.visualItemRect(root_file).left() == widget.visualItemRect(folder).left(), "a root file is indented against the folder above"
        assert widget.visualItemRect(inside).left() > widget.visualItemRect(folder).left(), "a file in a folder is not indented"
        assert not widget.rootIsDecorated()
        kinds = [widget.topLevelItem(i).data(0, gl.KIND_ROLE) for i in range(widget.topLevelItemCount())]
        assert kinds == ["folder", "leaf", "archives"], kinds      # folders first, then the root's own files, «Archives» last
    finally:
        widget.close()


def test_a_click_on_a_folder_opens_and_shuts_it():
    gl = _gl()
    from PySide6.QtCore import QEvent, Qt
    widget = _shown(gl)
    try:
        folder = widget.topLevelItem(0)
        was = folder.isExpanded()
        point = _centre(widget, folder)
        widget.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, point, Qt.MouseButton.LeftButton))
        widget.mouseReleaseEvent(_mouse(QEvent.Type.MouseButtonRelease, point, Qt.MouseButton.NoButton))
        assert folder.isExpanded() != was, "a click on the folder's row did not toggle it"
    finally:
        widget.close()


def test_pressing_on_a_selected_entry_keeps_the_multiple_selection():
    """Why only one file could be dragged: the press made the entry the current one, the tab loaded it and rebuilt the list, and the drag was lost. The press must change nothing until it is known whether it is a drag or a click."""
    gl = _gl()
    from PySide6.QtCore import QEvent, Qt
    widget = _shown(gl)
    try:
        seen = []
        widget.currentIdChanged.connect(seen.append)
        for entry_id in ("SD_01", "SD_09"):
            widget._item_for(entry_id).setSelected(True)
        widget.select("SD_09")
        seen.clear()
        point = _centre(widget, widget._item_for("SD_01"))
        widget.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, point, Qt.MouseButton.LeftButton))
        assert sorted(widget.selected_ids()) == ["SD_01", "SD_09"], widget.selected_ids()
        assert widget.current_id() == "SD_09" and seen == [], "the press already changed the current entry"
        # released without moving: a click, which selects that entry alone, as the explorer does
        widget.mouseReleaseEvent(_mouse(QEvent.Type.MouseButtonRelease, point, Qt.MouseButton.NoButton))
        assert widget.selected_ids() == ["SD_01"] and widget.current_id() == "SD_01" and seen == ["SD_01"]
    finally:
        widget.close()


def test_a_press_and_a_move_starts_the_drag_with_the_whole_selection():
    gl = _gl()
    from PySide6.QtCore import QEvent, QPoint, Qt
    widget = _shown(gl)
    try:
        for entry_id in ("SD_01", "SD_09"):
            widget._item_for(entry_id).setSelected(True)
        started = []
        widget.startDrag = lambda actions: started.append(sorted(widget.selected_ids()))
        point = _centre(widget, widget._item_for("SD_01"))
        widget.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, point, Qt.MouseButton.LeftButton))
        widget.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, point + QPoint(1, 0), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
        assert started == [], "a one-pixel jitter started a drag"
        widget.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, point + QPoint(40, 0), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
        assert started == [["SD_01", "SD_09"]], started
        widget.mouseReleaseEvent(_mouse(QEvent.Type.MouseButtonRelease, point, Qt.MouseButton.NoButton))   # the press is spent
        assert sorted(widget.selected_ids()) == ["SD_01", "SD_09"]
    finally:
        widget.close()


def _drop(widget, point):
    from PySide6.QtCore import QMimeData, QPointF, Qt
    from PySide6.QtGui import QDropEvent
    widget.dropEvent(QDropEvent(QPointF(point), Qt.DropAction.MoveAction, QMimeData(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))


def test_dropping_two_selected_entries_on_a_folder_moves_both_in_one_emission():
    """«quand je sélectionne deux fichiers, je ne peux pas tous les deux les drag dans un dossier»."""
    gl = _gl()
    entries = _entries() + [{"id": "SD_10", "text": "SD_10", "group": ""}]
    widget = _shown(gl, entries, empty_folders=["Pavillon"])
    try:
        moves = []
        widget.moved.connect(lambda ids, group: moves.append((sorted(ids), group)))
        for entry_id in ("SD_09", "SD_10"):
            widget._item_for(entry_id).setSelected(True)
        pavillon = next(widget.topLevelItem(i) for i in range(widget.topLevelItemCount()) if widget.topLevelItem(i).text(0) == "Pavillon")
        _drop(widget, _centre(widget, pavillon))
        assert moves == [(["SD_09", "SD_10"], "Pavillon")], moves
        # and out of a folder, onto an empty spot of the pane: back to the root, still all of them
        moves.clear()
        widget.clearSelection()
        for entry_id in ("SD_01", "SD_02"):
            widget._item_for(entry_id).setSelected(True)
        from PySide6.QtCore import QPoint
        _drop(widget, QPoint(5, widget.viewport().height() - 3))
        assert moves == [(["SD_01", "SD_02"], gl.ROOT_GROUP)], moves
    finally:
        widget.close()


# --- the order the engineer gives the list (issue #15, calc/list_order.py) ------------------------------

class _MemoryStore:
    """A list_order.Store held in memory, which may refuse as a project opened read only does."""

    def __init__(self, order=(), groups=None, refuse=False):
        self.order, self.groups, self.refuse, self.saves = list(order), dict(groups or {}), refuse, 0

    def tab(self, _key):
        return list(self.order), dict(self.groups)

    def save(self, _key, order, groups=None):
        if self.refuse:
            return False
        self.saves += 1
        self.order = list(order)
        if groups is not None:
            self.groups = dict(groups)
        return True

    def set_group(self, key, ids, group):
        for i in ids:
            if group:
                self.groups[i] = group
            else:
                self.groups.pop(i, None)
        return self.save(key, self.order, self.groups)


def _ordered(gl, store, entries=None, **attach):
    widget = _shown(gl, [])
    widget.attach_order("tab_test", store, **attach)
    widget.set_entries(entries or _entries() + [{"id": "SD_10", "text": "SD_10", "group": ""}])
    return widget


def test_an_order_attached_is_shown_and_a_drop_above_an_entry_reorders_without_moving_a_file():
    gl = _gl()
    store = _MemoryStore(order=["SD_10", "SD_09", "SD_02", "SD_01"])
    widget = _ordered(gl, store)
    try:
        halle = widget.topLevelItem(0)
        assert [halle.child(i).text(0) for i in range(halle.childCount())] == ["SD_02", "SD_01"]
        assert [widget.topLevelItem(i).text(0) for i in (1, 2)] == ["SD_10", "SD_09"]
        signals = []
        widget.moved.connect(lambda ids, group: signals.append(("moved", list(ids), group)))
        widget.reordered.connect(lambda: signals.append(("reordered",)))
        # SD_09 dropped above SD_10, in the same folder (the root): the order alone, no file written
        widget.drop_ids(["SD_09"], widget._item_for("SD_10"), gl.ROOT_GROUP, below=False)
        assert signals == [("reordered",)] and store.order.index("SD_09") < store.order.index("SD_10"), (signals, store.order)
        # below an entry of a folder, from the root: the order written, then `moved` for the one that changes folder
        signals.clear()
        widget.drop_ids(["SD_10"], widget._item_for("SD_02"), "Halle", below=True)
        assert signals == [("moved", ["SD_10"], "Halle")], signals
        assert store.order.index("SD_02") < store.order.index("SD_10") < store.order.index("SD_01"), store.order
        # dropped on a folder: at its end
        widget.set_entries(_entries() + [{"id": "SD_10", "text": "SD_10", "group": "Halle"}])
        signals.clear()
        widget.drop_ids(["SD_02"], widget.topLevelItem(0), "Halle")
        assert signals == [("reordered",)] and [i for i in store.order if i in ("SD_01", "SD_02", "SD_10")][-1] == "SD_02", store.order
    finally:
        widget.close()


def test_a_drop_the_store_refuses_changes_nothing_and_says_nothing():
    gl = _gl()
    store = _MemoryStore(refuse=True)
    widget = _ordered(gl, store)
    try:
        signals = []
        widget.moved.connect(lambda *a: signals.append(a))
        widget.reordered.connect(lambda: signals.append("reordered"))
        widget.drop_ids(["SD_09"], widget._item_for("SD_01"), "Halle")
        assert signals == [] and store.saves == 0
    finally:
        widget.close()


def test_folders_kept_by_the_store_are_written_there_and_regroup_off_never_changes_a_folder():
    gl = _gl()
    store = _MemoryStore(groups={"SD_01": "Toiture"})
    entries = [{"id": i, "text": i} for i in ("SD_01", "SD_02")]
    widget = _ordered(gl, store, entries, groups=True)
    try:
        assert widget._item_for("SD_01").parent().text(0) == "Toiture" and widget._item_for("SD_02").parent() is None
        signals = []
        widget.moved.connect(lambda *a: signals.append(("moved",) + a))
        widget.reordered.connect(lambda: signals.append(("reordered",)))
        widget.drop_ids(["SD_02"], widget._item_for("SD_01"), "Toiture")
        assert store.groups == {"SD_01": "Toiture", "SD_02": "Toiture"} and signals == [("reordered",)], (store.groups, signals)
        widget.set_entries(entries)
        folder = widget.topLevelItem(0)
        widget._remove_folder(folder)
        assert store.groups == {}, store.groups
    finally:
        widget.close()
    store = _MemoryStore()
    widget = _ordered(gl, store, regroup=False)
    try:
        signals = []
        widget.moved.connect(lambda *a: signals.append(a))
        widget.drop_ids(["SD_09"], widget._item_for("SD_01"), "Halle")
        assert signals == [] and store.saves == 0, "a list that may not change a folder changed one"
    finally:
        widget.close()


def test_a_list_with_no_order_attached_behaves_as_before():
    """SheetList's order is its bundle's: a list that attaches nothing shows its entries as given and a drop is `moved` alone."""
    gl = _gl()
    widget = _shown(gl, [{"id": "b", "text": "b"}, {"id": "a", "text": "a"}])
    try:
        assert [widget.topLevelItem(i).text(0) for i in (0, 1)] == ["b", "a"]
        moves = []
        widget.moved.connect(lambda ids, group: moves.append((list(ids), group)))
        widget._item_for("a").setSelected(True)
        from PySide6.QtCore import QPoint
        _drop(widget, QPoint(5, widget.viewport().height() - 3))
        assert moves == [(["a"], gl.ROOT_GROUP)]
    finally:
        widget.close()
