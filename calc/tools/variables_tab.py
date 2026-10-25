"""Woodcore's «Variables» tab (docs/ui/tab-variables.md, docs/project/purpose.md §1; spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, issue #114): every value of the project, from the export, the files Woodcore writes and the compiled documents -- to find one, print it elsewhere in the report, or have a field of another tab follow it.

**A class of parameters on the type «Données»** (data_tab.DataTab; spec docs/requirements/completed/2026-10-24-type-
donnees.md, issue #106). Its content is `variables_browser.VariablesBrowser`, one whole service (`tab.service(
"browser")`), below the type's banner, which it tells what failed or what is out of date. What the window and the
other tabs call on it by name is **exposed** (`EXPOSES`, D-06): `begin_pick`, `end_pick`, `pick_chosen`,
`selected_key`, `selected_keys`, `variable`, `address`, `select_key`, and the attributes `search` (the command
palette writes a variable's name in it, `_palette_show_in`), `domains`, `pick_bar` and `pick_label` (read by the
tests of the tabs that link a field). The frame answers `view_state`, `restore`, `on_shown`, `on_mode`,
`confirm_leave` (the browser's `leave` waits for a reading in its thread) and `splitter` (the browser's). Until
issue #106 a `QWidget` shell forwarded each of them, one line each.

⚠️ **No `dirty`, deliberately**: it is what tells an **editor** from a browser here. `update_tab_marks` reads it
with `getattr(..., "dirty", False)`, and `tests/test_window.py` takes every tab that has one for an editor,
calling `update_list_marker()` on it. No data tab has one (data_tab.py).

⚠️ **What a document's registry holds exists nowhere but in a compile**, so a reading is a full compile (8-10 s on
the example project) where a document's own PDF does not carry it already: the documents are read once, in a
thread (`Read`), and then from the cache (variables_browser's own warning).
"""

from PySide6.QtCore import QThread, Signal

import variable_sources as sources   # the export's variables and where each comes from (calc/variable_sources.py, v0.117)
import variables as model     # the one module that reads a document's registry (calc/variables.py)
from data_tab import DataTab
from variables_browser import VariablesBrowser

EXPORT = sources.EXPORT
# The origin of a domain of the files Woodcore writes (formulas.json): listed beside the export's.
FORMULAS = sources.formula_domain.ORIGIN


class Read(QThread):
    """The documents read, one after the other, off the main thread, so a compile of eight seconds does not hold the window.

    A thread rather than the `QProcess` the export and the compile use, because the command that reads a
    registry is spelled in `calc/variables.py` and nowhere else: a QProcess here would be a second place that
    knows the expression, the `--root` and the `--in`. The project is resolved on the main thread and handed
    over, so a project switched meanwhile cannot be read by a thread that started before it.
    """

    done = Signal(str, object)     # a document, and its variables.Registry
    failed = Signal(str, object)   # a document, and a variables.VariablesError

    def __init__(self, parent, here, modes):
        super().__init__(parent)
        self.here = here
        self.modes = list(modes)

    def run(self):
        for mode in self.modes:
            try:
                # `best` and not `read`: a document's own PDF carries its variables since v0.110, so where it is newer than every source the answer comes back in under a second instead of eight
                self.done.emit(mode, model.best(self.here, mode=mode))
            except model.VariablesError as exc:
                self.failed.emit(mode, exc)
            except Exception as exc:                     # broad: handed to the tab, which says it -- never leave it saying «reading» for ever
                self.failed.emit(mode, model.VariablesError(str(exc), "not_json"))


class VariablesTab(DataTab):
    """The tab: the type's banner, and the browser of the variables. Parameters only (tests/test_tab_overrides.py)."""

    KEY = "tab_variables"
    SERVICES = DataTab.SERVICES + (VariablesBrowser,)
    # what the window (begin_variable_pick), «Domaines», the linked fields, the command palette and the tests of the tabs that link a field call on the tab by name: the browser's (REQ-008, D-06)
    EXPOSES = {name: "browser" for name in ("begin_pick", "end_pick", "pick_chosen", "selected_key", "selected_keys", "variable", "address", "select_key",
                                            "search", "domains", "pick_bar", "pick_label")}
