"""The order the engineer gives the lists of the window's tabs by drag and drop, and the folders of the «Formules» tab -- one file of the project, `Woodcore-Datei/lists.json` (issue #15, spec docs/requirements/completed/2026-10-08-onglet-formules-editeur-dossiers-include.md REQ-008, REQ-009, D-09, D-14, D-16).

The engineer, 08.10.2026: «Réorganiser l'ordre des domaines par glisser-déposer ; l'ordre est gardé par Woodcore dans un fichier du projet, le même mécanisme pour tous les onglets du même noyau ; noms de fichiers et id inchangés.»

**One file for every tab**, keyed by the tab (`tab_schema`, `tab_formula`…), beside the sources the engineer draws -- not in the generated `_woodcore/`, which an export may rebuild (ARCH-RISK-201, his answer Q-005):

    {"format": "woodcore-lists", "schema_version": "1.0",
     "tabs": {"tab_schema": {"order": ["S-02", "S-01"]},
              "tab_formula": {"order": ["poutre-p1"], "groups": {"poutre-p1": "Toiture"}}}}

**The order is the window's alone** (D-14): the report prints by id, so the file is no input of the export and an export never reads it. An id the file does not know -- new, or made outside Woodcore -- comes last, by id; an id no longer listed is ignored, and forgotten only when it is archived, renamed or purged here, never because a list hides it (a search filter, a draft row).

**`groups` is the «Formules» tab's alone** (D-16): a calculation domain is a `.typ`, which has no field to file it in, so its folder is kept here; every other tab keeps its folder in its source's own `group` field (decision v0.69, «a folder is a field»), and the file refuses a `groups` for it -- one folder, one place.

**A file that cannot be read is said and left as it is** (ARCH-RISK-207): the lists fall back to the order by id, and a drop is refused with the same words rather than writing over a file the engineer may have broken by hand. Nothing here imports Qt.
"""

import json
from pathlib import Path

import positions_store
import validation

FORMAT = "woodcore-lists"
SCHEMA_VERSION = "1.0"
FILE_NAME = "lists.json"
SCHEMA = "lists"
# The tabs whose folders are kept here, their sources having no `group` field of their own (D-16)
GROUPED_TABS = ("tab_formula",)


class ListOrderError(validation.ValidationError):
    """lists.json cannot be read or would not be valid: the file and the field, said."""


def empty():
    return {"format": FORMAT, "schema_version": SCHEMA_VERSION, "tabs": {}}


def path(here):
    return Path(here.lists_file)


def check(data, where=FILE_NAME):
    """The file's shape (schemas/lists.schema.json) and its one business rule: `groups` only for a tab of GROUPED_TABS."""
    try:
        validation.validate_structure(data, SCHEMA)
    except validation.ValidationError as exc:
        raise ListOrderError(f"{where}: {exc}") from None
    for key, tab in data["tabs"].items():
        if tab.get("groups") and key not in GROUPED_TABS:
            raise ListOrderError(f"{where}: tabs.{key}.groups -- the tab {key!r} keeps its folders in its own sources, not here")


def read(here):
    """The whole file, or an empty one where there is none. Raises ListOrderError naming the file and the field where it cannot be read."""
    target = path(here)
    if not target.is_file():
        return empty()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ListOrderError(f"{target}: cannot be read -- {exc}") from None
    check(data, str(target))
    return data


def write(here, data):
    """The whole file, checked, written beside itself and moved into place (positions_store._replace: tried again a moment where the sync client holds it). Written only where it changes, so a drop that moves nothing writes nothing."""
    check(data)
    target = path(here)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if target.is_file() and target.read_text(encoding="utf-8") == text:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_name(target.name + ".new")
    staged.write_text(text, encoding="utf-8")
    positions_store._replace(staged, target)


def tab_of(data, key):
    """(order, groups) of tab `key`: copies."""
    tab = data["tabs"].get(key) or {}
    return list(tab.get("order") or []), dict(tab.get("groups") or {})


def set_tab(data, key, order, groups=None):
    """`data` with tab `key` holding `order` (and `groups` for a tab of GROUPED_TABS); a tab left with nothing is taken out, so an unused tab writes nothing."""
    entry = {"order": list(order)}
    if groups:
        entry["groups"] = dict(sorted(groups.items()))
    if entry["order"] or entry.get("groups"):
        data["tabs"][key] = entry
    else:
        data["tabs"].pop(key, None)
    data["tabs"] = dict(sorted(data["tabs"].items()))
    return data


# --- the order applied, and changed ---------------------------------------------------------------

def ordered(entries, order):
    """`entries` (dicts with an `id`) in the order kept: those it names in its order, then the others by id."""
    rank = {eid: i for i, eid in enumerate(order)}
    known = sorted((e for e in entries if e["id"] in rank), key=lambda e: rank[e["id"]])
    unknown = sorted((e for e in entries if e["id"] not in rank), key=lambda e: str(e["id"]))
    return known + unknown


def place(order, shown, ids, group_of, group, before=None):
    """The order once `ids` are dropped into `group`, just above `before` -- or after the last id shown in `group` where `before` is None (at the end of the list where the group shows none). `order` is the order kept, `shown` every id the list shows in its order now, `group_of(id)` the folder an id shown is in. An id kept but not shown (hidden by a filter) keeps its slot."""
    full = list(order) + [i for i in shown if i not in order]
    moving = [i for i in full if i in set(ids)] + [i for i in ids if i not in full]
    rest = [i for i in full if i not in set(ids)]
    if before is not None and before in rest:
        at = rest.index(before)
    else:
        members = [k for k, i in enumerate(rest) if i in set(shown) and group_of(i) == group]
        at = members[-1] + 1 if members else len(rest)
    return rest[:at] + moving + rest[at:]


class Store:
    """The window's access to the file, for one project at a time: `here()` the project, `read_only()` whether it was opened read only -- a drop then changes nothing, as no other writer does (woodcore_gui.WRITERS) -- and `warn(message)` how a file that cannot be read is said, once per project and reason."""

    def __init__(self, here, read_only=lambda: False, warn=None):
        self.here = here
        self.read_only = read_only
        self.warn = warn
        self._said = set()

    def _data(self):
        """The file, or None where it cannot be read -- said once."""
        try:
            return read(self.here())
        except ListOrderError as exc:
            reason = str(exc)
            if self.warn is not None and reason not in self._said:
                self._said.add(reason)
                self.warn(reason)
            return None

    def problem(self):
        """Why the file cannot be read, or ''."""
        try:
            read(self.here())
            return ""
        except ListOrderError as exc:
            return str(exc)

    def tab(self, key):
        """(order, groups) of tab `key` -- both empty where the file is missing or cannot be read (the lists then follow the ids)."""
        data = self._data()
        return tab_of(data, key) if data is not None else ([], {})

    def save(self, key, order, groups=None):
        """Writes tab `key`'s order (and folders). False, writing nothing, in a project opened read only or where the file cannot be read -- which a drop refused says every time, the reason in the same words (REQ-008)."""
        if self.read_only():
            return False
        try:
            data = read(self.here())
        except ListOrderError as exc:
            if self.warn is not None:
                self.warn(str(exc))
            return False
        set_tab(data, key, order, groups if key in GROUPED_TABS else None)
        try:
            write(self.here(), data)
        except (ListOrderError, OSError) as exc:
            if self.warn is not None:
                self.warn(str(exc))
            return False
        return True

    # what a tab says when an id changes, so the engineer's order follows it (ARCH-RISK-208)

    def rename(self, key, old, new):
        order, groups = self.tab(key)
        if old not in order and old not in groups:
            return True
        order = [new if i == old else i for i in order]
        if old in groups:
            groups[new] = groups.pop(old)
        return self.save(key, order, groups)

    def forget(self, key, ids):
        order, groups = self.tab(key)
        gone = set(ids)
        if not gone & (set(order) | set(groups)):
            return True
        return self.save(key, [i for i in order if i not in gone], {i: g for i, g in groups.items() if i not in gone})

    def insert_after(self, key, new, ref, group=None):
        """`new` placed right after `ref` -- a duplicate beside what it copies -- in `group` where the tab keeps its folders here."""
        order, groups = self.tab(key)
        order = [i for i in order if i != new]
        order.insert(order.index(ref) + 1 if ref in order else len(order), new)
        if group:
            groups[new] = group
        return self.save(key, order, groups)

    def set_group(self, key, ids, group):
        """The folder of `ids` in a tab of GROUPED_TABS ('' the root)."""
        order, groups = self.tab(key)
        for i in ids:
            if group:
                groups[i] = group
            else:
                groups.pop(i, None)
        return self.save(key, order, groups)
