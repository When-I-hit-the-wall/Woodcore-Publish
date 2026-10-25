"""The rules of a list of cases, written once and without Qt (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, ARCH-005, ARCH-006).

Until issue #95 (v0.125) these rules lived in `source_editor.SourceEditorTab`, where a tab of calculation built on services (tab_host.py) could not reach them without being an editor tab itself. They are functions now, of a **host** -- the editor tab, or the tab built on a type --, which both call: one rule, one place, testable without a QApplication (tests/test_tab_services.py).

A host has what the rules read and write: `source`, `current_id`, `dirty`, `loading`, `ids`, `empty_folders`, `list` (a grouped_list.GroupedList, or anything that answers its few calls), `app`, `KEY`; and what a tab says of its own list -- `listed()`, `draft_text()`, `draft_group()`, `list_selection(select)`, `archived_entries()`, `show_empty_hint()`, `update_list_marker()`, `confirm_leave()`, `load(cid)`, `after_row_loaded(cid)`, `on_row_again(cid)`, `take_group(group)`, `sources_dir()`, `export_listed(text)`, `word(suffix, **args)`, `t(key, **args)`. Nothing here imports PySide6.
"""

import json

import engine
import grouped_list

NEW_ROW = "<new>"   # the list's row of the draft nobody has saved yet -- the one constant, which the tabs import (six copies until v0.120)


def next_free_id(taken, prefix):
    """The first id `prefix` + two digits that no source of `taken` holds -- compared without case, a file system that does not tell `s01` from `S01` being the engineer's own (five copies of this until v0.120, each with its own format)."""
    lowered = {t.lower() for t in taken}
    index = 1
    while f"{prefix}{index:02d}".lower() in lowered:
        index += 1
    return f"{prefix}{index:02d}"


def group_of_file(path):
    """The folder a source is filed in, read off its own `group` -- the field, never a directory (grouped_list.py)."""
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return grouped_list.ROOT_GROUP
    return grouped_list.group_of(source)


def set_group(source, group):
    """`source` takes the folder `group` (None: the root): what it is saved with, so that its next save does not put it back where it was."""
    if source is None:
        return
    if group:
        source["group"] = group
    else:
        source.pop("group", None)


def selection(select, current_id, ids):
    """The row the list chooses once filled: `select`, else the source open -- the draft's row where it is unsaved."""
    if select is None:
        select = current_id
    if select in ids:
        return select
    return NEW_ROW if current_id is None else None


def is_mine(cid, current_id):
    """Whether the row `cid` is the one the form shows: the source open, or the draft's row while the draft is open."""
    return cid == current_id or (current_id is None and cid == NEW_ROW)


def entries(rows, current_id, draft_text, draft_group):
    """The list's entries: the saved sources' rows `(id, text, group)`, then -- while the draft is not saved -- the draft's row, where it can be seen."""
    found = [{"id": cid, "text": text, "group": group} for cid, text, group in rows]
    if current_id is None:
        found.append({"id": NEW_ROW, "text": draft_text(), "group": draft_group()})
    return found


def reload(host, select=None):
    """The list rebuilt from what the host lists, the row `select` chosen, the folders kept, the dot of unsaved changes put again."""
    was_loading = host.loading
    host.loading = True
    rows = host.listed()
    host.ids = [cid for cid, _text, _group in rows]
    host.list.set_entries(entries(rows, host.current_id, host.draft_text, host.draft_group), host.empty_folders, host.list_selection(select), archived=host.archived_entries())
    host.empty_folders = host.list.empty_folders()
    host.app.save_folder_settings(host.KEY, host.empty_folders)
    host.show_empty_hint()
    host.loading = was_loading   # a list rebuilt while the form is being filled leaves it being filled
    host.update_list_marker()


def update_marks(host):
    """A dot beside the source being edited while it has unsaved changes. Every row carries a mark, dot or blank, so none of them moves sideways as the form is typed into."""
    for cid in host.list.ids():
        host.list.set_mark(cid, host.app.dirty_mark(is_mine(cid, host.current_id) and host.dirty))
    host.app.update_tab_marks()


def row_changed(host, cid):
    """A row chosen in the list: the source open chosen again does nothing to the form; another one is loaded once the draft is left (`confirm_leave`), the draft given up leaving the list."""
    if host.loading or not cid:
        return
    if is_mine(cid, host.current_id):
        host.on_row_again(cid)
        return
    if cid not in host.ids:
        return
    if not host.confirm_leave():
        host.reload_list(host.current_id)   # the row of the source kept chosen again
        return
    host.load(cid)
    host.after_row_loaded(cid)
    if NEW_ROW in host.list.ids():
        host.reload_list(cid)         # the draft given up leaves the list


def folders_changed(host):
    """A folder made, renamed or removed in the list: what the widget now holds is what the host keeps. ⚠️ Rebuilding the list from the host's own copy of the empty folders, taken BEFORE the new one was added, made a folder just made vanish the moment it was made."""
    host.empty_folders = host.list.empty_folders()
    host.reload_list(select=host.current_id)


def lists_object(host, ident):
    """Whether the object `ident` of the graph of dependencies is one of the host's cases (MainWindow.open_object, issue #71)."""
    return any(host.graph_id(cid) == ident for cid in host.saved_ids())


def open_object(host, ident):
    """The case the graph names `ident` opened, the draft open left as choosing another row leaves it (`confirm_leave`)."""
    cid = next((c for c in host.saved_ids() if host.graph_id(c) == ident), None)
    if cid is None or cid == host.current_id or not host.confirm_leave():
        return
    host.load(cid)
    host.reload_list(cid)


def move(host, ids, group):
    """A drop wrote a folder (UI-001 of the spec 2026-10-21-restes-issue-69): the draft is saved first where it can be (`confirm_leave`, the question asked only where it cannot), then the field goes into each source, the sources written are exported, and the list is rebuilt from the files. The draft takes the folder too -- the source open, or the draft never saved, whose row was dropped -- or its next save would put it back where it was. A file the disk refuses (OneDrive holding it) stops the move there: what was written before is exported, and the status bar says which file failed, last."""
    if not host.confirm_leave():
        host.reload_list(host.current_id)
        return
    targets = [cid for cid in ids if cid != NEW_ROW]
    if NEW_ROW in ids:
        if host.current_id is None:
            host.take_group(group)    # a draft has no file to write the field into: it carries the folder until it is saved
        elif host.current_id not in targets:
            targets.append(host.current_id)   # saved just now by confirm_leave: its file takes the folder
    written, failure = [], None
    for cid in targets:
        path = host.sources_dir() / ("%s.json" % cid)
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        set_group(source, group)
        try:
            engine.write_json(path, source)
        except OSError as exc:
            failure = host.t("list_write_failed", id=cid, error=str(exc))
            break
        written.append(cid)
        if cid == host.current_id:
            host.take_group(group)
    if written:
        host.export_listed(host.word("moved", count=len(written), group=group or "—"))
    host.reload_list(host.current_id)
    if failure:
        host.app.set_status(failure)
