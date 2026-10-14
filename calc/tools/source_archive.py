# -*- coding: utf-8 -*-
"""What «Supprimer» does in every editor tab since v0.77: it **archives** (docs/ui/window.md §10quater).

The engineer's rule: a file deleted has its ID removed and appears in an «Archives» folder, always at the bottom of the list. So a deleted source is moved into `archives/` inside its own folder -- `statics/archives/`, `connectors/archives/`, ... -- with its `id` taken out of it and noted beside it as the one it had.

**Why a directory, when a folder of the list is a field** (grouped_list.py). An archived source has to leave the export and free its ID, and a field would have done neither without every reader learning to skip it. A subfolder does both by construction: every exporter globs `<folder>/*.json` and nothing deeper (`source_paths` in each domain module), and every «ID already taken» check reads the same glob. The file keeps its content, so nothing is lost.

**Restoring** is a drop out of «Archives» (or «Restaurer» on its menu): the source is written back as `<id>.json` under an ID made from its name -- identity.py's own rule -- or, with no name, the one it had, made unique against the IDs in use. **Deleting for good** is only offered on an archived entry, and asks.

**Sources that are not JSON** (issue #15): `Actions` works through a *backend* -- `JsonSources`, these functions, by default -- so the «Formules» tab, whose calculation domains are `.typ` files, archives, restores and purges through the same «Archives» row, the same questions and the same words with a backend of its own (formula_domain.ArchiveBackend), rather than a copy of this class (ARCH-RISK-206).
"""

import json
import re
from datetime import datetime
from pathlib import Path

import identity
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)

FOLDER = "archives"
KEY_PREFIX = "archive:"      # the list's id of an archived entry: never a valid source ID, so a tab cannot mistake one for the other
ARCHIVED = "archived"        # {"id": the ID it had, "at": when} -- written into the archived file, taken out on restore
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")   # every domain's own (connection.py, plan.py, schema.py, statics.py, connector.py)


def folder(source_dir):
    return Path(source_dir) / FOLDER


def is_key(entry_id):
    return isinstance(entry_id, str) and entry_id.startswith(KEY_PREFIX)


def _path(source_dir, key):
    name = key[len(KEY_PREFIX):] if is_key(key) else key
    if "/" in name or "\\" in name or not name.endswith(".json"):
        raise ValueError("not an archive key: %r" % key)
    return folder(source_dir) / name


def taken_ids(source_dir):
    """The IDs in use, lower-cased: the file system ignores case, the report does not."""
    return {p.stem.lower() for p in Path(source_dir).glob("*.json")}


def archive(source_dir, sid, now=None):
    """Moves `<sid>.json` into archives/, its `id` and folder taken out and the ID it had noted under `archived`. Returns the archive's key. A file that is not JSON is moved as it is."""
    source_dir = Path(source_dir)
    path = source_dir / ("%s.json" % sid)
    now = now or datetime.now()
    target_dir = folder(source_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = "%s-%s" % (now.strftime("%y%m%d-%H%M%S"), sid)
    target, n = target_dir / ("%s.json" % stem), 2
    while target.exists():
        target, n = target_dir / ("%s-%d.json" % (stem, n)), n + 1
    raw = path.read_bytes()
    try:
        source = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        source = None
    if isinstance(source, dict):
        source.pop("id", None)
        source.pop("group", None)
        source[ARCHIVED] = {"id": sid, "at": now.strftime("%Y-%m-%dT%H:%M:%S")}
        target.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        target.write_bytes(raw)
    path.unlink()
    return KEY_PREFIX + target.name


def _read(path):
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
        return source if isinstance(source, dict) else {}
    except (OSError, ValueError):
        return {}


def entries(source_dir, text=None):
    """The archived sources as the list shows them, newest first: {id, text, tooltip}. `text(key, formatting)` gives the tooltip's words in the window's language (grouped_list's `_t`)."""
    rows = []
    base = folder(source_dir)
    if not base.is_dir():
        return rows
    for path in sorted(base.glob("*.json"), key=lambda p: p.name, reverse=True):
        source = _read(path)
        info = source.get(ARCHIVED) if isinstance(source.get(ARCHIVED), dict) else {}
        old = info.get("id") or path.stem
        shown = (source.get("name") or "").strip() or old
        label = (source.get("label") or "").strip()
        at = (info.get("at") or "").replace("T", " ")[:16]
        tooltip = (text("grp_archived_tip", "Ancien identifiant : {id} · archivé le {at}.\nGlisser dans un dossier pour le restaurer.")
                   if text else "{id} {at}").format(id=old, at=at)
        rows.append({"id": KEY_PREFIX + path.name, "text": "%s — %s" % (shown, label) if label else shown, "tooltip": tooltip})
    return rows


def restored_id(source, source_dir):
    """The ID a restored source takes: made from its name (identity.py), else the one it had, made unique against the IDs in use."""
    info = source.get(ARCHIVED) if isinstance(source.get(ARCHIVED), dict) else {}
    base = identity.slug_id(source.get("name") or "") or (info.get("id") or "")
    if not ID_PATTERN.match(base):
        base = "Restored"
    taken = taken_ids(source_dir)
    candidate, n = base, 2
    while candidate.lower() in taken:
        candidate, n = "%s-%d" % (base, n), n + 1
    return candidate


def restore(source_dir, key, group=""):
    """Writes the archived source back as `<id>.json` in `group`, and removes it from archives/. Returns the ID it took."""
    source_dir = Path(source_dir)
    path = _path(source_dir, key)
    source = _read(path)
    if not source:
        raise ValueError("%s cannot be read as a source" % path.name)
    sid = restored_id(source, source_dir)
    source.pop(ARCHIVED, None)
    # the ID sits where a source states it, after its version
    ordered = {}
    for k, v in source.items():
        ordered[k] = v
        if k == "schema_version":
            ordered["id"] = sid
    if "id" not in ordered:
        ordered = {"id": sid, **ordered}
    if group:
        ordered["group"] = group
    (source_dir / ("%s.json" % sid)).write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    path.unlink()
    return sid


def purge(source_dir, key):
    """Deletes an archived source for good."""
    _path(source_dir, key).unlink(missing_ok=True)


class JsonSources:
    """The sources of most tabs, one `<id>.json` each: what `Actions` archives, restores and purges by default. Another kind of source gives `Actions` an object with the same five methods."""

    def present(self, source_dir):
        return {p.stem for p in Path(source_dir).glob("*.json")}

    def archive(self, source_dir, sid):
        return archive(source_dir, sid)

    def restore(self, source_dir, key, group=""):
        return restore(source_dir, key, group)

    def purge(self, source_dir, key):
        purge(source_dir, key)

    def entries(self, source_dir, text=None):
        return entries(source_dir, text)


class Actions:
    """«Supprimer», a drop into «Archives», a drop out of it and «Supprimer définitivement», for one editor tab -- written once, here, and wired by each tab to its own folder, list, export and reload.

    `source_dir` is a callable returning the folder, read at every call so a test pointing the tab's module constant elsewhere is followed. `export(text)` runs the tab's export and writes the status line; `reload(select)` rebuilds the list; `forget_current()` is what the tab does when the object its form shows was archived -- open its first entry, or a new one.
    """

    def __init__(self, tab, source_dir, export, reload, forget_current, archive_note=None, before_archive=None, backend=None):
        self.tab = tab
        self.backend = backend or JsonSources()   # how a source is archived, restored, purged (issue #15)
        self.source_dir = source_dir
        self.export = export
        self.reload = reload
        self.forget_current = forget_current
        # v0.115, for a kind of source others depend on (a position plan fire plans follow): `archive_note(ids)` is a sentence added to the question, "" where there is nothing to add; `before_archive(ids)` runs once the engineer said yes, before a file is moved -- what depends on them is detached then, while what it depends on can still be read.
        self.archive_note = archive_note
        self.before_archive = before_archive

    def _t(self, key, fallback, **values):
        text = self.tab.list._t(key, fallback)
        return text.format(**values) if values else text

    def _ask(self, text):
        from PySide6.QtWidgets import QMessageBox
        return QMessageBox.question(self.tab, self._t("grp_archives", "Archives"), text) == QMessageBox.StandardButton.Yes

    def _fail(self, error):
        from PySide6.QtWidgets import QMessageBox
        notices_ui.tell(str(error), notifications.WARNING, source="source_archive")

    def delete(self):
        """The «Supprimer» button. An archived entry selected is deleted for good, asking; otherwise every saved entry selected -- or the one the form shows -- goes to «Archives». False where there is nothing saved to act on, so the tab discards its unsaved draft as it always did."""
        keys = self.tab.list.selected_archives()
        if keys:
            self.purge(keys)
            return True
        if getattr(self.tab, "current_id", None) is None and getattr(self.tab, "dirty", False):
            return False    # the form holds a draft never saved: «Supprimer» discards it, never a saved entry still highlighted in the list (periodic audit 260916)
        present = self.backend.present(self.source_dir())
        ids = [i for i in self.tab.list.selected_ids() if i in present]
        current = getattr(self.tab, "current_id", None)
        if not ids and current in present:
            ids = [current]
        if not ids:
            return False
        self.archive(ids)
        return True

    def archive(self, ids):
        present = self.backend.present(self.source_dir())
        ids = [i for i in ids if i in present]
        if not ids:
            return
        question = self._t("grp_archive_confirm", "« {ids} » ira dans « Archives » : son identifiant est retiré, et les appels Typst qui l'utilisent ne fonctionneront plus. Continuer ?", ids=", ".join(ids))
        note = self.archive_note(ids) if self.archive_note is not None else ""
        if not self._ask(question + ("\n\n" + note if note else "")):
            return
        if self.before_archive is not None:
            self.before_archive(ids)
        try:
            for sid in ids:
                self.backend.archive(self.source_dir(), sid)
        except OSError as exc:
            self._fail(exc)
        current = getattr(self.tab, "current_id", None)
        self.tab.dirty = False if current in ids else self.tab.dirty
        self.export(self._t("grp_archived_status", "{count} fichier(s) déplacé(s) dans « Archives ».", count=len(ids)))
        if current in ids:
            self.tab.current_id = None
            self.forget_current()
        else:
            self.reload(current)

    def restore(self, keys, group):
        restored = []
        try:
            for key in keys:
                restored.append(self.backend.restore(self.source_dir(), key, group))
        except (OSError, ValueError) as exc:
            self._fail(exc)
        if restored:
            self.export(self._t("grp_restored_status", "Restauré sous « {ids} ».", ids=", ".join(restored)))
        self.reload(getattr(self.tab, "current_id", None))

    def purge(self, keys):
        if not self._ask(self._t("grp_purge_confirm", "Supprimer définitivement {count} fichier(s) archivé(s) ? Cette action est irréversible.", count=len(keys))):
            return
        for key in keys:
            try:
                self.backend.purge(self.source_dir(), key)
            except (OSError, ValueError) as exc:
                self._fail(exc)
        self.reload(getattr(self.tab, "current_id", None))

    def connect(self):
        lst = self.tab.list
        lst.archiveRequested.connect(self.archive)
        lst.restoreRequested.connect(self.restore)
        lst.purgeRequested.connect(self.purge)
