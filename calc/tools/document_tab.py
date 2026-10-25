"""The type «Document»: a tab of the project's or a document's own files, built from services on the frame (spec docs/requirements/completed/2026-10-24-type-document.md, issue #107; docs/ui/building-a-tab.md).

The fourth type of the decision D-05 of the spec 2026-10-23-onglets-types-et-services, and the first that does not stand on `tab_host.TabHost`: a document has no case, no store of cases, no «Affichage» and no bar «Annuler / Enregistrer» of a case, so `DocumentTab` stands on the frame extracted from it (tab_frame.TabFrame, Q-001 A, D-04). It holds «Projet» (project_tab.ProjectTab, three services) and «Structure du document» (structure_tab.StructureTab, one whole service wrapping its widget, Q-002 A, D-05).

**Its context** (`DocumentContext`) is all its services share -- no service holds another (D-06 of the spec 2026-10-23-onglets-types-et-services, ARCH-002):
* **one draft flag a tab** (`dirty`, set by `touch()`, ARCH-RISK-006): a service that keeps a draft -- the title page of «Projet» -- says it was changed; a service that writes at every gesture -- the structure -- never does;
* **the project read-only** (`read_only()`, `writable()`, said once to the window where it refuses);
* **the files read again** (`reload()`: the phases `loaded` then `lock`, the draft gone);
* **what one service offers the others** (`provide(name)`, the frame's context's since issue #106, which a data tab's banner is reached by too): a service names in `PROVIDES` the methods it offers -- «Projet»'s acts, applying a form and creating a document, which both of its pages trigger --, and the context gives the one service that offers it.

**The type** answers once what the window calls on a tab of a document (REQ-005): `dirty` and `save` (each service that saves, in the order of `SERVICES`, false at the first refusal), `discard` (phase `discard`), `flush_pending` (phase `flush`: what a service holds pending, written), `confirm_leave` (phase `leave`, then -- something unsaved -- the one question of autosave.confirm with the tab's `UNSAVED_WORDS`), `set_view` (the page of `VIEWS` shown, phase `view_set`), and the frame's `on_shown`, `on_mode`, `view_state` and `restore`. A tab of the type defines none of them: it names its parameters -- `KEY`, `VIEWS`, `SERVICES`, `UNSAVED_WORDS` -- and `HOOKS` is empty (tests/test_tab_overrides.py, REQ-008). It defines neither `current_id`, `current`, `id_edit` nor `list` (ARCH-007): a draft of «Projet» is one the autosave treats as never saved -- saved when it is replaced or the window closes, not when the engineer only looks elsewhere --, as before the type.

**No default service** (D-07): nothing is common to «Projet» and «Structure» but the context and the type. A service becomes the type's default when a third tab of a document asks for it.

**The body**: the services' widgets, one page each -- where the tab names `VIEWS`, a stack of pages, each service shown in the view its `IN_VIEWS` names --, without margins; the tab's `splitter`, which the window binds and folds, is the first a service gives (`splitter`).
"""

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

import autosave
from source_editor import save_shortcut
from tab_frame import FrameContext, TabFrame


def writable(app):
    """Whether the project of the window `app` may be written; the window says it may not, once, where it may not -- the one answer of a document's context and of the structure's widget (structure_tab.StructureView)."""
    if getattr(app, "read_only", False):
        app.refuse_read_only()
        return False
    return True


class DocumentContext(FrameContext):
    """All a service of a tab of a document knows of its tab -- see the module's docstring."""

    def __init__(self, host, app):
        super().__init__(host, app)
        self.dirty = False

    def touch(self, *_ignored):
        """A change of the engineer's to the draft: the tab's one flag set, and the window's marks once."""
        if not self.dirty:
            self.dirty = True
            self.app.update_tab_marks()

    def read_only(self):
        """Whether the window holds the project read-only -- another window has it (project_lock.py)."""
        return bool(getattr(self.app, "read_only", False))

    def writable(self):
        """Whether the project may be written; the window says it may not, once, where it may not."""
        return writable(self.app)

    def reload(self):
        """Every service filled again from the files as they are now (`loaded`), what may be written then enabled (`lock`), nothing unsaved any more."""
        self.host.phase("loaded")
        self.dirty = False
        self.host.phase("lock")


class DocumentTab(TabFrame):
    """The type «Document» -- see the module's docstring."""

    CONTEXT = DocumentContext
    HOOKS = ()
    VIEWS = ()
    SERVICES = ()
    UNSAVED_WORDS = None    # (title, text) of the question asked before an unsaved draft is left: the tab's own words

    def frame_body(self, widgets):
        """The services' pages: one shown alone, or a stack in the order of `VIEWS`; the tab's splitter the first a service gives."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        pages = [(s, w) for s, w in widgets.items() if w is not None]
        if self.VIEWS:
            self.pages = QStackedWidget()
            for key in self.VIEWS:
                page = [w for s, w in pages if key in s.IN_VIEWS]
                self.pages.addWidget(page[0] if len(page) == 1 else self._column(page))
            layout.addWidget(self.pages, 1)
        else:
            self.pages = None
            layout.addWidget(pages[0][1] if len(pages) == 1 else self._column([w for _s, w in pages]), 1)
        self.splitter = next((s.splitter for s in self.services if getattr(s, "splitter", None) is not None), None)

    def _column(self, found):
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 0, 0)
        for widget in found:
            column.addWidget(widget, 1)
        return holder

    def frame_finish(self):
        """Ctrl+S where a service keeps a draft to save; then every service filled from the files (`reload`), before the frame gives back what a rebuild kept."""
        if any(hasattr(s, "save") for s in self.services):
            save_shortcut(self)
        self.ctx.reload()

    def on_properties_changed(self, look_changed):
        """The project's look changed -- a form applied, the properties edited (the window's `properties_written`) --: told to the services that compile a page (`properties_changed`)."""
        self.phase("properties_changed", look_changed)

    # --- the draft -------------------------------------------------------------------------

    dirty = property(lambda self: self.ctx.dirty, lambda self, v: setattr(self.ctx, "dirty", v))

    def save(self):
        """What each service keeps unsaved, saved in the order of `SERVICES`: False at the first that refuses, True where none has anything to save."""
        for service in self.services:
            if hasattr(service, "save") and not service.save():
                return False
        return True

    def discard(self):
        """What is unsaved let go of: each service reads its files again (`discard`)."""
        self.phase("discard")

    def flush_pending(self):
        """What a service holds pending written now -- the tab left, the window left for another application (autosave.leave)."""
        self.phase("flush")

    def confirm_leave(self):
        """Before the tab, the document or the window is left: what is pending written (`leave`), then, where a draft is unsaved, the tab's one question (autosave.confirm: saved without it where it can be)."""
        self.phase("leave")
        if not self.dirty or not self.UNSAVED_WORDS:
            return True
        title, text = self.UNSAVED_WORDS
        return autosave.confirm(self.app, self, self.t(title), self.t(text), discard=self.discard)

    # --- the views -------------------------------------------------------------------------

    def set_view(self, key, enter=True):
        """The page of view `key` shown, and the services told (`view_set`): a service builds what the page shows only where `enter` says the engineer came to it."""
        if key not in self.VIEWS:
            return
        self.view = key
        if self.pages is not None:
            self.pages.setCurrentIndex(self.VIEWS.index(key))
        self.phase("view_set", key, enter)
