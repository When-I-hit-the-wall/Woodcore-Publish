"""The base of the tabs whose source is a drawing edited on a canvas -- the position plans and the fire plans, the static models, the detail schemas (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, ARCH-001, ARCH-RISK-108).

On `source_editor.SourceEditorTab`, it adds what such a tab has and a form has not: **«Annuler» and «Rétablir»**. Until v0.120 three tabs each kept their own two stacks of 200 steps, written three times (drawing_tab_sheets, statics_tab, schema_tab); they are kept here once. A tab says how a state of its source is copied (`snapshot`: a deep copy by default, the schema's own `model.snapshot`) and how one is put back (`replace_source`), and calls `push_history()` before a change -- one step a change, never one a pixel of a drag (test_fire_tab). The canvas widgets themselves -- zoom, tools, snapping -- are the drawing engines' (ARCH-004, D1), not this base's.
"""

import copy

from source_editor import SourceEditorTab

HISTORY = 200   # the steps «Annuler» goes back, in every tab with a canvas


class CanvasEditorTab(SourceEditorTab):
    LIST_MARGINS = (0, 0, 6, 0)   # the list's column keeps a gap before the splitter, as it always has on a canvas

    def export_listed(self, text):
        """A canvas's export, naming no drawing (`export(id, text)`): what a drop into a folder or an archive needs, which changes a field and no drawing."""
        return self.export("", text)

    def snapshot(self, state):
        return copy.deepcopy(state)

    def init_history(self):
        """Both stacks emptied: a source opened or made starts with nothing to undo."""
        self.undo_stack, self.redo_stack = [], []

    def push_history(self):
        """One step of «Annuler», taken before a change: the source as it is, the oldest step let go beyond HISTORY, and nothing left to redo."""
        self.undo_stack.append(self.snapshot(self.source))
        del self.undo_stack[:-HISTORY]
        self.redo_stack.clear()

    def replace_source(self, state):
        """The source replaced by `state` -- a step of «Annuler» or «Rétablir». An undo helper and never a writer: it is not in tab_guard.WRITERS."""
        raise NotImplementedError(f"{type(self).__name__} says how a state of its drawing is put back")

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.snapshot(self.source))
            self.replace_source(self.undo_stack.pop())

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.snapshot(self.source))
            self.replace_source(self.redo_stack.pop())
