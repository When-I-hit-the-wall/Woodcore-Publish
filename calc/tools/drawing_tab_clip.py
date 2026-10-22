"""Ctrl+A, Ctrl+C and Ctrl+V in the plan tabs (issue #61, docs/ui/tab-plans.md §10quater): what the position plan's tab and the fire-protection plan's share, DrawingTab's mixin.

Ctrl+A selects everything the plan holds (the canvas's `select_all`). Ctrl+C with something selected asks for a base point -- the canvas's state `clip-base`, no button of its own --, and the click takes the clip (`make_clip`, the subclass's) into the one clip of the process (plan_clipboard.py). Ctrl+V puts the canvas in its state `paste`, the clip following the pointer, and the click puts it down (`paste_clip`, the subclass's) in one step of «Annuler»; a clip of the other kind of plan (T8) or of another project (D-004) is refused, and said. The shortcuts are the canvas's own (`WidgetShortcut`), so Ctrl+C in a field copies its text.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

import plan_canvas_edit
import plan_clipboard
import project
from domains import plan_clip


class DrawingClipMixin:
    """Methods of drawing_tab.DrawingTab: the class names this mixin among its bases. Its `KIND` -- "position" or "fire", plan_clip.POSITION and FIRE -- is what it pastes; it answers `make_clip(point)` and `paste_clip(clip, point)`."""

    def init_clip_shortcuts(self):
        for keys, slot in (("Ctrl+A", self.clip_select_all), ("Ctrl+C", self.clip_copy), ("Ctrl+V", self.clip_paste)):
            shortcut = QShortcut(QKeySequence(keys), self.canvas)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(lambda slot=slot: slot())
        self.canvas.clip_point.connect(self.on_clip_point)

    def clip_root(self):
        """The project a clip belongs to: its root, as text."""
        try:
            return str(project.current().root)
        except project.ProjectError:
            return None

    def clip_select_all(self):
        """Ctrl+A: everything the plan holds, but the building's outline (T7)."""
        if self.KIND not in plan_clip.KINDS:
            return
        self.choose_tool("select")
        self.canvas.select_all()

    def clip_copy(self):
        """Ctrl+C: the base point asked for, when something is selected."""
        if self.KIND not in plan_clip.KINDS:
            return
        if not self.canvas.has_selection():
            self.hint.setText(self.t("plan_clip_nothing"))
            return
        self.choose_tool(plan_canvas_edit.CLIP_BASE)

    def clip_refusal(self, clip):
        """The key of what refuses `clip` a paste here, or None."""
        if clip is None or not len(clip):
            return "plan_paste_empty"
        if clip.kind != self.KIND:
            return f"plan_paste_from_{clip.kind}"
        if clip.root != self.clip_root():
            return "plan_paste_other_project"
        return None

    def clip_paste(self):
        """Ctrl+V: the clip following the pointer, put down by the next click."""
        if self.KIND not in plan_clip.KINDS:
            return
        refusal = self.clip_refusal(plan_clipboard.current())
        if refusal:
            self.hint.setText(self.t(refusal))
            return
        self.choose_tool(plan_canvas_edit.PASTE)

    def on_clip_point(self, tool, x, y):
        """The base point clicked after Ctrl+C, or the point the clip is put down at after Ctrl+V."""
        if tool == plan_canvas_edit.CLIP_BASE:
            clip = self.make_clip((x, y))
            plan_clipboard.put(clip)
            self.choose_tool("select")
            self.hint.setText(self.t("plan_clip_done", n=len(clip)))
            return
        clip = plan_clipboard.current()
        refusal = self.clip_refusal(clip)
        if refusal:
            self.choose_tool("select")
            self.hint.setText(self.t(refusal))
            return
        self.canvas.begin_change()
        selection, said = self.paste_clip(clip, (x, y))
        self.canvas.end_change()
        self.choose_tool("select")
        self.select_pasted(selection)
        self.hint.setText(" ".join(said))
