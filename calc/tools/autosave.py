"""Saving without a question (docs/ui/window.md §10quater, v0.117).

The engineer's rule of 07.10.2026: «Lorsqu'on change de fenêtre, d'onglet, de mode, il doit y avoir un enregistrement automatique sans demander la confirmation». The plan tabs have saved themselves when a plan was left since v0.114 (`DrawingTab.autosave`); since v0.117 every editor does, from here, in one place (ARCH-004 of the spec `docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md`).

**Three contexts** (review A01):

- **(a) the draft stays in memory** -- another tab, another view of the tab, the window left for another application (`LEAVE`): saved where it can be, without a word; where it cannot, nothing is written, the dot stays and the status line says why. Nothing is asked: the engineer is not leaving the draft, only looking elsewhere.
- **(b) the draft is replaced** -- another object of the tab, «Nouveau», another document (`REPLACE`): saved where it can be; where it cannot, the tab's own question is asked as before (`confirm_leave`), since the draft would otherwise be lost.
- **(c) the window closes** (`CLOSE`): likewise.

**What is never saved without the engineer** (review A02): a **rename** -- an object saved under one ID whose ID field now says another; an annex's PDF follows its source's ID, so a half-typed ID saved in silence would rename files of the project -- a draft never saved, while the engineer only looks elsewhere (a tab, a view, the focus); and, on the window merely losing the focus, an object whose ID field holds the cursor. A new draft never touched (`untouched_draft`) is not saved at all, and a new draft, touched or not, is saved only when it is replaced or the window closes -- never while the engineer only looks elsewhere.

**How a tab takes part.** Its `save(quiet=…)` or `save()` is called inside `quiet(app)`; while it is, the tab's refusals go through `refuse`, its rename question through `ask_rename` and its export warnings through `warn`, which say them in the status line instead of a box and refuse the rename. A tab may declare `SAVE_ON_FOCUS = False` (Python: a script half typed would run at the next export, review A16), `untouched_draft()`, and `flush_pending()` for what it writes as it goes (the structure tab, which has no dot).
"""

from contextlib import contextmanager

from PySide6.QtWidgets import QApplication, QMessageBox

import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)

LEAVE = ("tab", "view", "focus", "export")
REPLACE = ("replace",)
CLOSE = ("close",)

STRINGS = {
    "fr": {
        "autosave_refused": "« {name} » n'est pas enregistré : {reason}",
        "autosave_rename": "un changement d'ID se confirme avec « Enregistrer »",
        "autosave_read_only": "projet en lecture seule",
        "autosave_later": "Un export est en cours : les modifications seront enregistrées à sa fin.",
        "autosave_engine": "Enregistré, mais l'import n'est pas lancé : le moteur du projet demande une décision. Cliquer « Import données ».",
        "autosave_warnings": "Import terminé avec des avertissements : {first}",
    },
    "de": {
        "autosave_refused": "«{name}» ist nicht gespeichert: {reason}",
        "autosave_rename": "eine Änderung der ID wird mit «Speichern» bestätigt",
        "autosave_read_only": "Projekt schreibgeschützt",
        "autosave_later": "Ein Export läuft: die Änderungen werden an seinem Ende gespeichert.",
        "autosave_engine": "Gespeichert, aber der Import ist nicht gestartet: die Engine des Projekts verlangt eine Entscheidung. «Daten importieren» klicken.",
        "autosave_warnings": "Import mit Warnungen beendet: {first}",
    },
    "en": {
        "autosave_refused": "«{name}» is not saved: {reason}",
        "autosave_rename": "a change of ID is confirmed with «Save»",
        "autosave_read_only": "project read-only",
        "autosave_later": "An export is running: the changes will be saved when it ends.",
        "autosave_engine": "Saved, but the import is not started: the project's engine asks for a decision. Click «Import data».",
        "autosave_warnings": "Import finished with warnings: {first}",
    },
}

_running = False   # one autosave at a time: a save that opens a box, or exports, must not start another (review A03)


def _app(widget):
    return getattr(widget, "app", None)


def is_quiet(widget):
    """Whether `widget`'s window is saving without a question right now."""
    return bool(getattr(_app(widget), "saving_quietly", False))


@contextmanager
def quiet(app):
    """The tabs' boxes turned into reasons while a save runs without a question: `refuse`, `ask_rename` and `warn` gather them in `app.quiet_reasons`."""
    app.saving_quietly = True
    app.quiet_reasons = []
    try:
        yield app.quiet_reasons
    finally:
        app.saving_quietly = False


def refuse(widget, title, message):
    """A save refused: a critical notice -- the save asked for was not made --, or -- saving without a question -- kept as the reason the status line gives, the dot staying (v0.117: no ⚠ beside the dot for the same reason). Returns False, as the tabs' `fail` always did."""
    if is_quiet(widget):
        _app(widget).quiet_reasons.append(str(message))
        return False
    notices_ui.tell(message, notifications.CRITICAL, source="autosave")
    return False


def warn(widget, title, message):
    """A warning after a save that went through (an export that refused): a warning notice, or the status line while saving without a question."""
    if is_quiet(widget):
        _app(widget).set_status(str(message))
        return
    notices_ui.tell(message, notifications.WARNING, source="autosave")


def ask_rename(widget, title, text, ask=True):
    """Whether a rename may be made: the engineer's yes -- never given without him (review A02), so while saving without a question it is refused and the reason kept. `ask` False where the tab renamed without asking until now, which it still does when the engineer saves himself."""
    if is_quiet(widget):
        _app(widget).quiet_reasons.append(_app(widget).t("autosave_rename"))
        return False
    if not ask:
        return True
    return QMessageBox.question(widget, title, text) == QMessageBox.StandardButton.Yes


def is_new(tab):
    """Whether `tab` holds a draft never saved: no object of its own (`current_id`, or `current` in the tabs that name it so)."""
    if hasattr(tab, "current_id"):
        return tab.current_id is None
    return getattr(tab, "current", None) is None


def id_field(tab):
    """The ID field of `tab`'s form, where it has one."""
    return getattr(tab, "id_edit", None) or getattr(getattr(tab, "identity", None), "id", None)


def name_of(tab):
    """What the status line calls the object: its ID as typed, a revision's number, or what the tab holds."""
    field = id_field(tab)
    text = field.text().strip() if field is not None and hasattr(field, "text") else ""
    index = getattr(tab, "index_edit", None)
    if not text and index is not None and hasattr(index, "value"):
        text = str(index.value())
    return text or str(getattr(tab, "current_id", None) or getattr(tab, "current", None) or "?")


def _save(tab):
    """The tab's own save, quiet where it takes the word (the plans, Python)."""
    import inspect
    try:
        takes_quiet = "quiet" in inspect.signature(tab.save).parameters
    except (TypeError, ValueError):
        takes_quiet = False
    return tab.save(quiet=True) if takes_quiet else tab.save()


def leave(app, tab, reason):
    """Saves what `tab` holds unsaved without a question, where it can be; True where nothing is left unsaved. `reason` is one of LEAVE, REPLACE or CLOSE. Where it cannot, nothing is written and the status line says why; the caller of a REPLACE or a CLOSE then asks the tab's own question."""
    global _running
    flush = getattr(tab, "flush_pending", None)
    if flush is not None:
        flush()
    if not getattr(tab, "dirty", False) or not hasattr(tab, "save"):
        return True
    if _running:
        return False
    if reason == "focus":
        if not getattr(tab, "SAVE_ON_FOCUS", True) or QApplication.activeModalWidget() is not None:
            return False
        field = id_field(tab)
        if field is not None and field.hasFocus():
            return False
    untouched = getattr(tab, "untouched_draft", None)
    if is_new(tab) and untouched is not None and untouched():
        return False if reason in LEAVE else _discard(tab)   # kept while the engineer only looks elsewhere
    if is_new(tab) and reason in LEAVE:
        return False      # a draft never saved is saved when it is replaced or the window closes, not while the engineer only looks elsewhere (review A02): its ID may be half typed
    if getattr(app, "read_only", False):
        app.set_status(app.t("autosave_refused", name=name_of(tab), reason=app.t("autosave_read_only")))
        return False
    if getattr(app, "process", None) is not None:
        app.autosave_pending = True
        app.set_status(app.t("autosave_later"))
        return False
    name = name_of(tab)
    _running = True
    try:
        with quiet(app) as reasons:
            saved = bool(_save(tab))
    finally:
        _running = False
    if not saved and getattr(tab, "dirty", False):
        app.set_status(app.t("autosave_refused", name=name, reason="; ".join(reasons) or "?"))
        return False
    return True


def _discard(tab):
    """A new draft never touched, let go of without a file: what the engineer opened and did not use."""
    tab.dirty = False
    marker = getattr(tab, "update_list_marker", None)
    if marker is not None:
        marker()
    return True


def confirm(app, tab, title, text, discard=None, save=None):
    """Every editor's `confirm_leave` (v0.117): True where the draft may be replaced -- nothing unsaved, saved now without a question (`leave`, «replace»), or, where it could not be, the engineer's answer to the one question every tab asks, Save · Discard · Cancel. `discard` lets the draft go (the dot cleared by default), `save` saves it with the engineer's own boxes (the tab's `save` by default)."""
    if not getattr(tab, "dirty", False):
        return True
    if leave(app, tab, "replace"):
        return True
    answer = QMessageBox.question(tab, title, text, QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
    if answer == QMessageBox.StandardButton.Save:
        return bool((save or tab.save)())
    if answer == QMessageBox.StandardButton.Discard:
        if discard is not None:
            discard()
        else:
            _discard(tab)
        return True
    return False
