# -*- coding: utf-8 -*-
"""Nom · Description · ID -- how every object Woodcore's window edits is named (docs/ui/window.md §10quater).

The engineer's rule, stated once for the whole window: **what describes an object is its name and its description; what identifies it is its ID**, and the ID is generated from the name and may be written over. Until then each tab named its objects its own way -- «Groupe · Nom · Variante · ID · Désignation · Description» in one, «ID · Désignation · Groupe» in another -- and the folder a thing was filed in was typed into a field beside it, where the left pane's drag and drop already set it.

So every editor tab takes these three rows from here, in this order, and nothing else of the kind:

- **Nom** (`name`), free text;
- **Description** (`label` -- the word the report prints in a caption, «Detailschema D01: <description>» -- or a connector's own `description`), free text;
- **ID** (`id`), the file name and the string the report addresses the object by, composed of the name by `slug_id` and writable over. The folder (`group`) is no longer a field: it is set by dragging the object into a folder of the left pane (grouped_list.py).

⚠️ **An ID written over stays written over.** The rows remember what they last composed: while the ID field still holds that, the name owns it; the moment it holds anything else it is the engineer's, and typing a name never touches it again. A saved object whose ID is not its name's slug -- every object saved before names existed -- therefore opens as written over, so giving it a name does not rename its file behind the engineer's back.
"""

import unicodedata

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit

# What an ID may hold: a file name and a string the report quotes, so letters, digits and `_ . + -` (connector.ID_PATTERN, schema.ID_PATTERN, the plans' and the models' own).
ID_CHARACTERS = r"[A-Za-z0-9_.+-]*"


def slug_id(name, variant=""):
    """The ID a name composes: `Velo Unterstand` -> `Velo_Unterstand`, and with a variant `Velo_Unterstand-8mm`.

    An ID is a file's name and the string the report addresses the object by, so it is kept to letters, digits and `_ . + -`, opening on a letter or a digit.

    ⚠️ An accent is **decomposed**, not dropped: `Élément` gives `Element`. Dropping it gave `lment`, which is what an engineer writing French would have been handed for a name that is perfectly ordinary here. `unicodedata.normalize("NFKD", ...)` is the standard decomposition and gives the same answer for the same name whoever typed it, which is the property an ID has to have. A letter it cannot decompose -- a ß, a Cyrillic name -- is still dropped, and the field stays writable for exactly those cases.
    """
    def clean(text):
        out = []
        for char in unicodedata.normalize("NFKD", (text or "").strip()):
            if unicodedata.combining(char):
                continue                       # the accent NFKD split off
            if char.isalnum() and char.isascii():
                out.append(char)
            elif char in "_.+-":
                out.append(char)
            elif char.isspace():
                out.append("_")
        return "".join(out).strip("_")
    head, tail = clean(name), clean(variant)
    made = "-".join(part for part in (head, tail) if part)
    while made and not (made[0].isalnum() and made[0].isascii()):
        made = made[1:]
    return made


class IdentityRows:
    """The three rows, added to a QFormLayout: Nom, Description, ID. `on_change()` is called whenever the engineer edits one of them -- on every keystroke (`live`), or when a field is left (`live=False`, for a tab whose every change is a step of «Annuler»)."""

    def __init__(self, form, t, on_change, live=True):
        self.name = QLineEdit()
        self.description = QLineEdit()
        self.id = QLineEdit()
        self.id.setValidator(QRegularExpressionValidator(QRegularExpression(ID_CHARACTERS), self.id))
        self.id.setToolTip(t("idn_id_tip"))
        form.addRow(t("idn_name"), self.name)
        form.addRow(t("idn_description"), self.description)
        form.addRow(t("idn_id"), self.id)
        self.on_change = on_change
        self._composed = ""
        if live:
            # textChanged and not textEdited, so a caller (or a test) setting a field is heard as typing is; fill() blocks the signals
            self.name.textChanged.connect(lambda _text: self._name_changed())
            self.description.textChanged.connect(lambda _text: self.on_change())
            self.id.textChanged.connect(lambda _text: self.on_change())
        else:
            self.name.editingFinished.connect(self._name_changed)
            self.description.editingFinished.connect(self.on_change)
            self.id.editingFinished.connect(self.on_change)

    def fill(self, name, description, sid, saved):
        """The rows as a source has them. `saved` says whether the object is on disk: a new one's ID follows its name from the first letter typed, a saved one's only where it already is its name's slug."""
        for edit, text in ((self.name, name), (self.description, description), (self.id, sid)):
            edit.blockSignals(True)
            edit.setText(text or "")
            edit.blockSignals(False)
        made = slug_id(name)
        self._composed = made if saved else (sid or made)

    def follows(self):
        """True while the ID is the name's to change."""
        current = self.id.text().strip()
        return not current or current == self._composed

    def _name_changed(self):
        made = slug_id(self.name.text())
        if made and self.follows():
            if self.id.text().strip() != made:
                self.id.setText(made)
            self._composed = made
        self.on_change()

    def values(self):
        """(name, description, id), as typed -- the name and the ID stripped, the description as it stands."""
        return self.name.text().strip(), self.description.text(), self.id.text().strip()


STRINGS = {
    "fr": {
        "idn_name": "Nom",
        "idn_description": "Description",
        "idn_id": "ID",
        "idn_id_tip": "Composé à partir du nom tant qu'il n'a pas été écrasé ; c'est le nom du fichier et ce que le rapport cite.",
    },
    "de": {
        "idn_name": "Name",
        "idn_description": "Beschreibung",
        "idn_id": "ID",
        "idn_id_tip": "Wird aus dem Namen gebildet, solange sie nicht überschrieben ist; sie ist der Dateiname und das, womit der Bericht das Objekt aufruft.",
    },
    "en": {
        "idn_name": "Name",
        "idn_description": "Description",
        "idn_id": "ID",
        "idn_id_tip": "Composed from the name until it is written over; it is the file name and what the report calls the object by.",
    },
}
