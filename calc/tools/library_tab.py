"""The type «Bibliothèque»: a tab of the engineer's own files rather than the project's (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, ARCH-006, Q-005 answer A; issue #110). The «Matériaux» tab is the first.

`calc_tab.CalcTab` and its host (`tab_host.TabHost`) are built round a domain of cases saved in the project -- a store, «Affichage», Ctrl+S, the read-only guard. A library is none of these: one list of entries, some read only, the others the engineer's, each edited in a sheet and saved by its own «Enregistrer». So this type is apart from `TabHost`, and as thin: it mounts `tab_host.Service`s in the three zones -- left, centre, right --, keeps the draft in a context of its own (`LibraryContext`), runs phases in the order of `SERVICES`, and answers what the window calls on a tab (`view_state`, `restore`, `on_shown`, `confirm_leave`, `dirty`, `splitter`, `service`). No service calls another (D-06): the context's operations and phases join them. What a library is -- its entries, which are editable, how one is saved -- is its domain's, `STORE`, a Qt-free module (`domains.materials_library` for the materials).

It writes nothing of the project: its writers are named so that the read-only guard (tab_guard.WRITERS) never wraps them, and its `TabSpec` says `project=False` (tab_registry.PROJECT_FREE). It has no `save`: the window's autosave never writes a half-typed entry into a file every project reads -- leaving with one unsaved asks (`confirm_leave`). Bringing it and `TabHost` onto one base is a later step (docs/ui/building-a-tab.md).
"""

import copy

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QSplitter, QVBoxLayout, QWidget

import validation
from tab_host import run_phase, service_named


class LibraryContext(QObject):
    """All a service of a library knows: the window, its words, the entries (`entries`, read from the domain), the one selected (`current_id`), the draft of it the sheet edits (`draft`), whether the draft differs from the saved one (`dirty`), whether it is being filled (`loading`), and the operations every service may ask -- select, new, duplicate, delete, save, cancel, reveal."""

    changed = Signal()          # the draft changed (a field typed): the panes that say what it is, again
    revealRequested = Signal(str)   # a label asks the right pane to show one of its modules (the source)

    def __init__(self, tab):
        super().__init__(tab)
        self.tab = tab
        self.app = tab.app
        self.store = tab.STORE
        self.entries = []
        self.error = ""
        self.current_id = None
        self.draft = None
        self.saved = None
        self.dirty = False
        self.loading = False

    def t(self, key, **args):
        return self.tab.word(key, **args)

    def prefix(self):
        """The prefix of the tab's words (`mat_`): the sentences that name its entries are `<prefix>saved`, `<prefix>unsaved`…, the tab's own."""
        return self.tab.PREFIX

    # --- the entries ---------------------------------------------------------------

    def load(self):
        """The entries read again from the domain -- the library on disk, which another window may have written."""
        self.entries, self.error = self.store.entries()
        self.tab.phase("listed")

    def find(self, entry_id):
        return next((e for e in self.entries if e["id"] == entry_id), None)

    def editable(self, entry=None):
        entry = self.draft if entry is None else entry
        return bool(entry) and self.store.editable(entry) and not self.error

    # --- the draft -----------------------------------------------------------------

    def select(self, entry_id, ask=True):
        """The entry `entry_id` shown in the sheet -- after asking what to do with the draft unsaved, where `ask`. False where the engineer stayed."""
        if entry_id == self.current_id and self.draft is not None:
            return True
        if ask and not self.tab.confirm_leave():
            return False
        found = self.find(entry_id)
        self.current_id = found["id"] if found else None
        self.saved = copy.deepcopy(found)
        self.draft = copy.deepcopy(found)
        self.dirty = False
        self.loading = True
        try:
            self.tab.phase("selected")
        finally:
            self.loading = False
        return True

    def touch(self, *_ignored):
        """A change of the engineer's to the draft -- never one the sheet makes as it is filled."""
        if self.loading or self.draft is None:
            return
        self.dirty = True
        self.changed.emit()
        self.tab.phase("drafted")

    def rebuild(self):
        """The sheet built again for the draft as it is -- a change of what it is (a member made a panel)."""
        self.loading = True
        try:
            self.tab.phase("selected")
        finally:
            self.loading = False
        self.tab.phase("drafted")

    def start(self, entry):
        """A new entry, not saved yet, made the draft and listed at once."""
        if not self.tab.confirm_leave():
            return False
        self.entries.append(entry)
        self.tab.phase("listed")
        self.current_id = entry["id"]
        self.saved = None
        self.draft = entry
        self.dirty = True
        self.loading = True
        try:
            self.tab.phase("selected")
        finally:
            self.loading = False
        self.tab.phase("drafted")
        return True

    def save_entry(self):
        """The draft written by the domain (checked first) -- the entries read again, the draft now the saved one. Refused, in the tab's words, where the domain refuses it."""
        if self.draft is None or not self.editable():
            return False
        try:
            self.store.save(self.draft)
        except validation.ValidationError as exc:
            self.app.set_status(self.t(self.prefix() + "invalid", error=str(exc)))
            return False
        name = self.store.name(self.draft, self.app.lang)
        kept = self.draft["id"]
        self.dirty = False
        self.load()
        self.current_id = None
        self.select(kept, ask=False)
        self.app.set_status(self.t(self.prefix() + "saved", name=name))
        return True

    def cancel(self):
        """The draft put back as it was saved -- a new entry not saved taken away."""
        if self.saved is None:
            self.entries = [e for e in self.entries if e["id"] != self.current_id]
            self.dirty = False
            self.current_id = None
            self.draft = None
            self.tab.phase("listed")
            self.tab.phase("selected")
            return
        self.dirty = False
        kept, self.current_id = self.current_id, None
        self.select(kept, ask=False)

    def delete_entry(self):
        """The entry selected taken out of the library, after the engineer said so."""
        if self.draft is None or not self.editable():
            return False
        name = self.store.name(self.draft, self.app.lang)
        answer = QMessageBox.question(self.tab, self.t(self.prefix() + "delete_title"), self.t(self.prefix() + "delete_ask", name=name))
        if answer != QMessageBox.StandardButton.Yes:
            return False
        gone, saved = self.draft["id"], self.saved is not None
        self.dirty = False
        self.current_id = None
        self.draft = None
        self.tab.phase("selected")     # the panes let go of the entry first -- its PDF shown on the right is closed before it is deleted
        if saved:
            self.store.delete(gone)
        self.load()
        self.tab.phase("selected")
        self.app.set_status(self.t(self.prefix() + "deleted", name=name))
        return True

    def reveal(self, module_id, entry_id=None):
        """A label asks to see one of the right pane's modules -- the entry it belongs to selected first."""
        if entry_id is not None and entry_id != self.current_id and not self.select(entry_id):
            return
        self.revealRequested.emit(module_id)


class LibraryTab(QWidget):
    """The host of a tab of the type «Bibliothèque» -- see the module's docstring. A tab is a subclass naming its parameters: `KEY`, `STORE`, `PREFIX`, `SERVICES`."""

    KEY = ""
    STORE = None
    PREFIX = ""
    SERVICES = ()
    VIEWS = ()
    STRETCH = (3, 6, 4)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.ctx = LibraryContext(self)
        self.services = [cls() for cls in self.SERVICES]
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        widgets = {s: s.mount(self.ctx) for s in self.services}
        for zone in ("left", "centre", "right"):
            self.splitter.addWidget(self._zone(zone, widgets))
        for index, stretch in enumerate(self.STRETCH):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)
        self.ctx.load()
        self.restore(app.views.get(self.KEY))

    def _zone(self, zone, widgets):
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 0, 0)
        for s, widget in widgets.items():
            if s.ZONE == zone and widget is not None:
                column.addWidget(widget, 1)
        return holder

    def word(self, key, **args):
        text = self.app.t(key)
        return text.format(**args) if args else text

    def service(self, name):
        return service_named(self, name)

    def phase(self, name, *args):
        """The phase `name` run by every service that has it, in the order of `SERVICES`."""
        run_phase(self.services, name, *args)

    # --- what the window calls ---------------------------------------------------------

    @property
    def dirty(self):
        return self.ctx.dirty

    @dirty.setter
    def dirty(self, value):
        self.ctx.dirty = bool(value)

    @property
    def current_id(self):
        return self.ctx.current_id

    def view_state(self):
        """What a rebuild of the window keeps: the entry selected, the draft where it is unsaved, and each service's own."""
        return {"current": self.ctx.current_id, "draft": copy.deepcopy(self.ctx.draft) if self.ctx.dirty else None,
                "saved": copy.deepcopy(self.ctx.saved) if self.ctx.dirty else None,
                "services": {s.NAME: s.state() for s in self.services}}

    def restore(self, state):
        state = state or {}
        for s in self.services:
            s.restore((state.get("services") or {}).get(s.NAME) or {})
        if state.get("draft") is not None:
            draft = state["draft"]
            if self.ctx.find(draft["id"]) is None:
                self.ctx.entries.append(draft)
                self.phase("listed")
            self.ctx.current_id, self.ctx.draft, self.ctx.saved, self.ctx.dirty = draft["id"], draft, state.get("saved"), True
            self.ctx.loading = True
            try:
                self.phase("selected")
            finally:
                self.ctx.loading = False
            self.phase("drafted")
        elif state.get("current") and self.ctx.find(state["current"]):
            self.ctx.select(state["current"], ask=False)
        elif self.ctx.entries:
            self.ctx.select(self.ctx.entries[0]["id"], ask=False)

    def on_shown(self):
        """The tab in front: the library read again from the disk -- another window, or a project opened, may have written it --, the draft kept where it is unsaved."""
        if self.ctx.dirty:
            return
        kept = self.ctx.current_id
        self.ctx.load()
        self.ctx.current_id = None
        if kept and self.ctx.find(kept):
            self.ctx.select(kept, ask=False)
        elif self.ctx.entries:
            self.ctx.select(self.ctx.entries[0]["id"], ask=False)

    def confirm_leave(self):
        """What to do with an entry unsaved before another is shown or the window closes: saved, discarded, or stayed on. True where the tab may be left."""
        if not self.ctx.dirty or self.ctx.draft is None:
            return True
        name = self.STORE.name(self.ctx.draft, self.app.lang) or self.ctx.t(self.ctx.prefix() + "unnamed")
        answer = QMessageBox.question(self, self.ctx.t(self.ctx.prefix() + "unsaved_title"), self.ctx.t(self.ctx.prefix() + "unsaved", name=name),
                                      QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            return self.ctx.save_entry()
        if answer == QMessageBox.StandardButton.Discard:
            self.ctx.cancel()
            return True
        return False
