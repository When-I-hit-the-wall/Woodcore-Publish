"""«Annuler» of the «Domaines» tab: one step, the last deletion or the last gesture on several lines (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, D-17, UI-007, ARCH-015).

The engineer's answer to Q-002 (A): «Annuler» undoes the last row deleted and the last gesture of several lines -- a group moved, the links «Valider» wrote --, in the message that follows it, **one step**, no Ctrl+Z of the whole tab. The step is the file's text before and after the gesture: undoing writes the text before back, byte for byte, **only where the file is still, on the disk, the text after** -- a file changed since (VS Code, another field of the tab) is never written over, and the refusal says so. A new gesture replaces the step.

No Qt.
"""

from pathlib import Path


class UndoError(ValueError):
    """«Annuler» refused: the file changed since the gesture, or there is nothing to undo. `code` is what the window says it by."""

    def __init__(self, code, message, **values):
        super().__init__(message)
        self.code = code
        self.values = values


class Undo:
    """The one step «Annuler» undoes -- see the module's docstring."""

    def __init__(self):
        self.step = None

    def record(self, name, path, before, after, **values):
        """The gesture `name` (`delete`, `move`, `link`) just wrote `after` over `before` in `path`: the step, replacing any older one."""
        self.step = {"name": name, "path": Path(path), "before": before, "after": after, "values": values}

    def forget(self):
        self.step = None

    @property
    def name(self):
        return self.step["name"] if self.step else None

    def undo(self):
        """The file written back as it was before the gesture; returns its path. Raises UndoError `nothing` or `changed`, nothing written."""
        step = self.step
        if step is None:
            raise UndoError("nothing", "nothing to undo")
        path = step["path"]
        try:
            with open(path, encoding="utf-8", newline="") as file:
                now = file.read()
        except OSError:
            now = None
        if now != step["after"]:
            self.step = None
            raise UndoError("changed", f"{path.name} changed since -- nothing written over it", file=path.name)
        with open(path, "w", encoding="utf-8", newline="") as file:
            file.write(step["before"])
        self.step = None
        return path
