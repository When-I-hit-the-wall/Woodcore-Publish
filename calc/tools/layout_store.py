# -*- coding: utf-8 -*-
"""The panes' sizes, kept by tab, by view and by the screens plugged in (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-022, REQ-023, ARCH-005).

The engineer, 07.10.2026: «les dispositions des volets (largeurs, hauteur, etc...) sont enregistrés par fenêtre d'affichage (par onglet, par affichage, par mode) pour un display spécifique (i.e. si je branche mon ordinateur portable à un écran, il y a une sauvegarde d'affichage pour l'écran externe lorsqu'il est utilisé et une sauvegarde pour mon pc portable lorsqu'il est utilisé sans l'écran externe)».

* **Which screens** (`signature`): every screen plugged in, by its maker, its model and its serial number -- or, where Windows gives none, its physical size in millimetres -- and its scaling, sorted, hashed: the laptop alone is one signature, the laptop and its external screen another. Never `QScreen.name()`, `\\\\.\\DISPLAY1` on Windows, which changes as screens are plugged and unplugged; never a position, which changes as they are arranged.
* **What is kept**: a splitter's sizes as fractions of its length (a window of another size keeps the same proportions), under `settings["layouts"][signature][tab][view][name]`, in the user's settings (usersettings.py) -- how the engineer likes to work, never the project. A configuration never seen takes the layout last used (`last_used`, the signature written last), else the panes' own defaults.
* **How a splitter is kept** (`bind`): its sizes put back where some are kept, and written a moment after it is dragged (WRITE_DELAY_MS) -- one write for a drag, not one per pixel. `key` says under which tab and view: a tab that changes its view calls `restore` again.

Nothing here knows the tabs: the window binds the splitters it has (woodcore_gui.bind_layouts).
"""

import hashlib
import json

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtGui import QGuiApplication

import usersettings

WRITE_DELAY_MS = 400
LAYOUTS = "layouts"
LAST_USED = "last_used"


def screen_identity(screen):
    """One screen as it stays the same from one plugging to the next: its maker, its model and its serial number, else its physical size, and its scaling."""
    serial = (screen.serialNumber() or "").strip()
    size = screen.physicalSize()
    physical = "" if serial else f"{round(size.width())}x{round(size.height())}mm"
    return "|".join((screen.manufacturer() or "", screen.model() or "", serial, physical, f"{screen.devicePixelRatio():g}"))


def signature(screens=None):
    """The screens plugged in, as one short key: the same set of screens gives the same key whatever their order or arrangement. `screens` -- QScreen objects or their identities as text -- for a test; the application's own where None."""
    if screens is None:
        screens = QGuiApplication.screens() if QGuiApplication.instance() is not None else []
    identities = sorted(s if isinstance(s, str) else screen_identity(s) for s in screens)
    return hashlib.sha256("\n".join(identities).encode("utf-8")).hexdigest()[:12]


class Store:
    """The layouts kept in the user's settings: `get(key)` and `put(key, sizes)` for the signature in force -- `read`/`write` injectable for a test."""

    def __init__(self, sig=None, read=None, write=None):
        self.sig = sig
        self.read = read or usersettings.read
        self.write = write or usersettings.write

    def signature(self):
        return self.sig or signature()

    def _table(self, settings):
        layouts = settings.get(LAYOUTS)
        return layouts if isinstance(layouts, dict) else {}

    def get(self, key):
        """The fractions kept for `key` (tab, view, name) on these screens -- or, never kept here, on the screens last used; None where none."""
        settings = self.read()
        layouts = self._table(settings)
        for sig in (self.signature(), layouts.get(LAST_USED)):
            node = layouts.get(sig) if isinstance(sig, str) else None
            for part in key:
                node = node.get(part) if isinstance(node, dict) else None
            if isinstance(node, list) and node and all(isinstance(v, (int, float)) and v >= 0 for v in node):
                return list(node)
        return None

    def put(self, key, fractions):
        settings = self.read()
        layouts = dict(self._table(settings))
        sig = self.signature()
        node = layouts.setdefault(sig, {})
        for part in key[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                child = node[part] = {}
            node = child
        node[key[-1]] = [round(float(v), 4) for v in fractions]
        layouts[LAST_USED] = sig
        settings[LAYOUTS] = layouts
        self.write(settings)


def fractions_of(sizes):
    total = sum(sizes)
    return [s / total for s in sizes] if total > 0 else None


def sizes_of(fractions, total):
    return [max(0, round(f * total)) for f in fractions]


class Binding(QObject):
    """One splitter kept: restored now, written a moment after each drag, under the key `key()` gives (its tab, its view, its name)."""

    def __init__(self, splitter, key, store):
        super().__init__(splitter)
        self.splitter, self.key, self.store = splitter, key, store
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(WRITE_DELAY_MS)
        self.timer.timeout.connect(self.save)
        splitter.splitterMoved.connect(lambda *_a: self.timer.start())
        self.restore()

    def restore(self):
        fractions = self.store.get(self.key())
        if fractions is None or len(fractions) != self.splitter.count():
            return False
        total = sum(self.splitter.sizes()) or (self.splitter.width() if self.splitter.orientation() == Qt.Orientation.Horizontal else self.splitter.height())
        if total <= 0:
            return False
        self.splitter.setSizes(sizes_of(fractions, total))
        return True

    def save(self):
        if getattr(self.splitter.widget(0), "folded", False):
            return   # a left pane folded to its arrow (chrome.FoldablePane, issue #10): its arrow's width is not a layout to give back at the next start
        fractions = fractions_of(self.splitter.sizes())
        if fractions is not None:
            self.store.put(self.key(), fractions)


def bind(splitter, key, store=None):
    """`splitter` kept under `key()` (a callable giving (tab, view, name)): its sizes put back now, and written after each drag. Returns the Binding, which `restore()` puts back again -- a view changed."""
    return Binding(splitter, key, store or Store())


# What a calculation tab keeps of its pane of modules on this machine (spec 2026-10-22-onglet-neige-type, REQ-010, D-26): the order of its modules and which are folded, by tab -- not by the screens' signature, an order having no reason to change with a screen plugged in. And the sections of its form folded (`sections`, the accordion of the spec 2026-10-23-neige-correctifs-issues-96-99, UI-005), beside them: each writer puts its own keys and keeps the others' (ARCH-RISK-010).
MODULES = "modules"
STATE_KEYS = ("order", "folded", "sections")


def get_state(tab, store=None):
    """The state a calculation tab was left in on this machine -- {"order": [...], "folded": [...], "sections": [...]}, the keys kept -- or {} where none was kept."""
    store = store or Store()
    node = store.read().get(MODULES)
    node = node.get(tab) if isinstance(node, dict) else None
    if not isinstance(node, dict):
        return {}
    return {key: [str(v) for v in node[key] if isinstance(v, str)] for key in STATE_KEYS if isinstance(node.get(key), list)}


def put_state(tab, state, store=None):
    """The keys of `state` ({"order", "folded"}, lists of module ids; {"sections"}, the sections folded) kept for `tab` on this machine, the keys it does not name as they were -- the pane of modules and the form write apart."""
    store = store or Store()
    settings = store.read()
    table = dict(settings.get(MODULES) or {}) if isinstance(settings.get(MODULES), dict) else {}
    node = dict(table.get(tab) or {}) if isinstance(table.get(tab), dict) else {}
    node.update({key: [str(v) for v in state[key]] for key in STATE_KEYS if key in state})
    table[tab] = node
    settings[MODULES] = table
    store.write(settings)


def put_value(name, value, store=None):
    """A single value kept for these screens (the navigation's width): under (name,)."""
    (store or Store()).put(("window", name), [value])


def get_value(name, store=None):
    found = (store or Store()).get(("window", name))
    return found[0] if found else None
