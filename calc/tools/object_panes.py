"""The right pane's editors of the objects of a document -- one pane for each kind of thing the «Structure du document» tab can have selected (the engineer's rework of 01.10.2026, work package R1-D2).

**No Typst code is ever shown in Woodcore.** A table is edited as a list of rows, the fields of the row chosen, a list of columns with a check box each, a caption and notes; a variable put in a cell is shown as the variable it is (`g_k = 1.9 kN/m²`), never as the call that writes it; a paragraph is a plain text box holding its markup as written -- the document's own words, in the document's own font, no syntax colours. The engineer who wants to read the code opens the file in VS Code.

**A pane is a column of cards over one model** (calc/typst_objects.py: `TableModel`, `LiveLoadTableModel`, `ChoiceModel`, `ChecklistModel`, `SignaturesModel`, `NormListModel`, `FieldModel`, `ImageModel`, `PlanModel`), or over a body string (a heading, a paragraph) or a small state (a section, a chapter):

* `pane.load(subject, context=None)` shows `subject` -- a model, a `Call`, an `Object` of calc/typst_objects.py, or for the two kinds that are markup (`heading`, `text`) the body as a string, a `HeadingModel`/`TextModel` or an `Object` of one of those types -- and says nothing: loading is not an edit. A pending edit of the pane's previous subject is emitted first, so none is lost. An `Object` that Woodcore did not write in its own form -- `hand_edited`, `unreadable` -- is flagged in a notice over the pane (`notice`) before it is edited: editing it rewrites it, or replaces it; a heading or a paragraph that is no single heading or paragraph is shown read only, and said.
* `pane.changed(payload)` is emitted after an edit, with a **snapshot** of what the pane now holds: a new model (`payload.to_call()` is what is written between the object's tags, `typst_objects.write_object(text, id, payload.to_call())`), a body string for a heading and a paragraph (`write_object(text, id, body)`), or a `NodeState` for a section and a chapter. A button (add a row, move it, hide a column) emits at once; typing is debounced (`DEBOUNCE_MS`, 400 ms) so a paragraph typed is one write and not forty. `pane.flush()` emits what is pending now -- what a host calls **before it changes what it considers current**, which is why the host (`ObjectPaneHost`) does it first thing in `show_object`.
* `pane.current()` is the same snapshot, whenever it is asked for. `pane.set_language(lang)` writes the pane's words again.
* A refusal of the model (`ModelError`) is said in a banner in the pane, in the window's words -- never in a modal: the engineer is typing -- and the model is left as it was. An object written in a form Woodcore cannot edit (an argument that is an expression) says so, and offers no editor.

**What a pane needs from its surroundings is a `PaneContext`**: the window's language, the project (`here`) from which the live-load categories and their values (data/calculations.json, else SIA 261 Tabelle 8), the plans, the norms catalogue and the project's own `references.bib`, the Images folder and the variables of the export and of the compiled report are read, each of them replaceable by an explicit value -- which is how a test, and a host that has already read them, hand them over. Two things are asked of the engineer through the context and can be replaced by a callable: `pick_variable(parent)` (a dialog listing the variables) and `choose_image(parent)` (a file dialog under the project's folder).

**The live loads** (`LiveLoadPane`): the row's category is chosen in a drop-down of SIA 261 Tabelle 8's categories, named in the window's language; q_k and Q_k stand in their fields as the export has them (`auto`) and are written over by typing -- the field and its readout then turn **orange** (the override colour of the window, theme.json) and «Reprendre» goes back to the norm's. ψ0, ψ1 and ψ2 are no part of a live-load table (the engineer's rule of 01.10.2026, calc/typst_objects.py): there is no ψ column to list, and no ψ variable to offer.

**A cell is one line** (`Text` with `grow`): the field of a row's cell starts as a single line and grows with its text -- a line break, or a text too long for the box -- up to eight lines, from where it scrolls; it is not a box of three lines left mostly empty. **A section's pane** (`SectionPane`) carries the title of its file's first heading (an object of the file or not), the file, whether it is printed, and its **sharing**: the documents it is shared with, «Partager avec…» and «Arrêter le partage» -- the pane asks (`shareRequested`, `stopShareRequested`) and the tab writes, through calc/sharing.py.

**Variables in a cell** are inserted from a picker fed by the context and written as `typst_objects.variable_cell(name, domain)` -- `[#doc-value("g_k", domain: ("dead-load", "D1"))]` -- so the cell follows the calculation. The pane reads such a cell back and shows the variable; `variable_of(value)` is the reader, held equal to `variable_cell`.

The words are `STRINGS`, keys `op_`, in the three languages: the window merges them into its own (the panes take their language from the context and do not read the window's).
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QEvent, QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

import cards  # the cards a pane is made of (cards.py)
import richtext  # a symbol set as mathematics (richtext.py)
import theme  # the orange of a value written over
import typst_objects as objects  # the models the panes edit (calc/typst_objects.py)
import validation
from i18n import strings as glossary  # the engine's words: a category of Tabelle 8 in the window's language
from norms import norms as catalogue  # the documents the engine can name in full (calc/norms/norms.json)
from norms import sia261  # Tabelle 8, where the project has no export yet
from typst_objects import AUTO, Content, Expr, ModelError
from object_panes_words import ERROR_WORDS, NNBSP, REASON_WORDS, STRINGS, _DE, _EN, _FR, _french, text  # split out of this module (issue #30): every name it had is still importable from it
from object_panes_context import Category, ExcerptInfo, FirePlanInfo, LANGUAGES, PaneContext, PlanInfo, VariableChoice, VariableDialog, _BIB_ENTRY, _BIB_TITLE, bib_entries, fmt_value  # split out of this module (issue #30): every name it had is still importable from it
from object_panes_fields import (  # split out of this module (issue #30): every name it had is still importable from it
    CellField,
    DEBOUNCE_MS,
    ListBox,
    Pane,
    Switch,
    Text,
    _STRING,
    _VARIABLE,
    _between,
    _drop,
    _unescape,
    as_context,
    call_of,
    parse_number,
    plain,
    show_number,
    variable_of,
)
from object_panes_table import (  # split out of this module (issue #30): every name it had is still importable from it
    KNOWN_KINDS,
    KNOWN_SYMBOLS,
    KNOWN_TITLES,
    LOAD_VALUES,
    RawTablePane,
    TablePane,
)
from object_panes_options import NormListPane, SIGNATURE_FIELDS  # split out of this module (issue #30): every name it had is still importable from it
from object_panes_media import set_width  # split out of this module (issue #30): every name it had is still importable from it

# The autonyms of the three languages, in the order a chapter's titles are written.
LANGUAGE_NAMES = {"de": "Deutsch", "fr": "Français", "en": "English"}


# --- what a pane needs from its surroundings -----------------------------------------------------


# --- the variable picker --------------------------------------------------------------------------


# --- reading a cell back ----------------------------------------------------------------------------


# --- small widgets ---------------------------------------------------------------------------------


# --- the base of every pane --------------------------------------------------------------------------


# --- the tables -----------------------------------------------------------------------------------------


# --- the lists to choose and to tick ---------------------------------------------------------------------


# --- the signatures ----------------------------------------------------------------------------------------


# --- the norms -------------------------------------------------------------------------------------------------


# --- a field, a picture, a plan ---------------------------------------------------------------------------------


# --- a heading and a paragraph, edited as the markup they are -------------------------------------------------------

class BodyPane(Pane):
    """What a pane over a body string shares: the body is the object, `current()` is it as a string -- what `typst_objects.write_object` takes for a heading and a paragraph --, and what was loaded is given back unchanged until the engineer edits it. A body that is no single heading or paragraph (`typst_objects.model_for_body` refuses it) is shown read only and says so: it is corrected in VS Code.

    The subject is the body (a string), a `HeadingModel` or a `TextModel`, or an `Object` of the file whose type is `heading` or `text` -- read by its `written` body."""
    KINDS = ()
    MARKUP = ""

    def init_state(self):
        self.body = ""
        self.readonly = False

    def subject_in(self, subject):
        if isinstance(subject, str):
            body = subject
        elif isinstance(subject, objects.Object):
            if not subject.markup:
                raise TypeError(f"a pane over a body shows a heading or a paragraph -- got the object {subject.type!r}")
            body = subject.written
        elif hasattr(subject, "to_body"):
            body = subject.to_body()
        else:
            body = getattr(subject, "body", None)
        if not isinstance(body, str):
            raise TypeError(f"a pane over a body shows a string, a model or an object with a body -- got {subject!r}")
        self.body = body.replace("\r\n", "\n").replace("\r", "\n")
        try:
            objects.model_for_body(self.MARKUP, self.body)
            self.readonly = False
        except ModelError:
            self.readonly = True
            self._notice_key = "op_unreadable_markup"
            self.show_notice()

    def ready(self):
        return True

    def current(self):
        return self.body

    def checked(self, make, *args):
        """`make(*args)` -- a model of the markup -- or None after a sentence in the banner where the model refuses it."""
        try:
            found = make(*args)
        except ModelError as exc:
            self.say(self.error_words(exc))
            return None
        self.say(None)
        return found


class HeadingPane(BodyPane):
    """A heading of a section: its text and its level. The body is `= Title` -- one `=` for each level -- and what the pane writes back is `HeadingModel.to_body()`'s."""
    MARKUP = "heading"

    def parse(self):
        try:
            model = objects.model_for_body("heading", self.body)
            self.level, self.title = model.level, model.title
        except ModelError:
            self.level, self.title = 1, self.body.partition("\n")[0]

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_title"))
        form = cards.form(card)
        self.title_edit = self.line_edit(self.title_edited)
        form.addRow(QLabel(t("op_heading_text")), self.title_edit)
        self.level_spin = QSpinBox()
        low, high = getattr(objects, "HEADING_LEVELS", (1, 6))
        self.level_spin.setRange(low, high)
        self.level_spin.valueChanged.connect(self.level_changed)
        form.addRow(QLabel(t("op_heading_level")), self.level_spin)
        layout.addWidget(card)

    def refresh(self):
        self.parse()
        was = self.title_edit.blockSignals(True)
        self.title_edit.setText(self.title)
        self.title_edit.blockSignals(was)
        was = self.level_spin.blockSignals(True)
        self.level_spin.setValue(min(max(self.level, self.level_spin.minimum()), self.level_spin.maximum()))
        self.level_spin.blockSignals(was)
        self.title_edit.setEnabled(not self.readonly)
        self.level_spin.setEnabled(not self.readonly)

    def written(self, level, title):
        model = self.checked(objects.HeadingModel, level, title)
        if model is None:
            return False
        self.level, self.title, self.body = model.level, model.title, model.to_body()
        return True

    def title_edited(self, typed):
        if self.written(self.level, typed):
            self.touch(immediate=False)

    def level_changed(self, level):
        if self._loading:
            return
        if self.written(level, self.title):
            self.touch(immediate=True)
        else:
            was = self.level_spin.blockSignals(True)
            self.level_spin.setValue(self.level)
            self.level_spin.blockSignals(was)


class TextPane(BodyPane):
    """A paragraph of a section: a plain text box holding its markup as written -- the document's words in the window's font, no syntax colours, no toolbar. What is typed is checked by `TextModel` as it is typed: a blank line, a heading line or an unclosed bracket is said in a sentence and the body stays the last that was valid."""
    MARKUP = "text"

    def build(self, layout):
        card = cards.card(self.t("op_text"))
        box = QVBoxLayout(card)
        box.addWidget(cards.note(self.t("op_text_note")))
        self.edit = QPlainTextEdit()
        self.edit.setTabChangesFocus(True)
        self.edit.setMinimumHeight(self.fontMetrics().lineSpacing() * 10)
        self.edit.textChanged.connect(self.typed)
        box.addWidget(self.edit)
        layout.addWidget(card)

    def refresh(self):
        was = self.edit.blockSignals(True)
        self.edit.setPlainText(self.body)
        self.edit.blockSignals(was)
        self.edit.setReadOnly(self.readonly)

    def typed(self):
        if self._loading or self.readonly:
            return
        typed = self.edit.toPlainText()
        if self.checked(objects.TextModel, typed) is None:
            return
        self.body = typed
        self.touch(immediate=False)


# --- sections and chapters ------------------------------------------------------------------------------------------

@dataclass
class NodeState:
    """What the right pane shows of a node of the document's tree that is no object: a section (a file) or a chapter (a group). `title` a section's title where it has one to set here -- the first heading of its file, an object of it or not --, `titles` a chapter's in each language, `printed` whether it is printed, `untagged` whether the file holds text that is not tagged yet, `has_title` whether the section's title is edited here -- not where the file has no heading, or one whose title is not plain text --, `file` the section's file (relative to its document's folder), `shared_with` the names of the documents the file is shared with and `sharing` whether the section can be shared at all (it is a file, in a project that has another document): the two buttons of the sharing card ask the tab, which writes -- the pane changes none of it."""
    id: str = ""
    title: str = ""
    titles: dict = field(default_factory=dict)
    printed: bool = True
    untagged: bool = False
    has_title: bool = True
    file: str = ""
    shared_with: tuple = ()
    sharing: bool = False


def state_of(subject):
    if isinstance(subject, NodeState):
        return NodeState(subject.id, subject.title, dict(subject.titles), subject.printed, subject.untagged, subject.has_title,
                         subject.file, tuple(subject.shared_with), subject.sharing)
    if isinstance(subject, dict):
        return NodeState(subject.get("id", ""), subject.get("title", ""), dict(subject.get("titles", {})), subject.get("printed", True),
                         subject.get("untagged", False), subject.get("has_title", True), subject.get("file", ""),
                         tuple(subject.get("shared_with", ())), bool(subject.get("sharing", False)))
    raise TypeError(f"a node's state is a NodeState or a dictionary -- got {subject!r}")


class NodePane(Pane):
    """What a section and a chapter share: a state, not a model."""
    KINDS = ()

    def init_state(self):
        self.state = NodeState()

    def subject_in(self, subject):
        self.state = state_of(subject)

    def ready(self):
        return True

    def current(self):
        return state_of(self.state)

    def printed_row(self, box):
        self.printed_check = Switch(self.t("op_printed"))
        self.printed_check.setToolTip(self.t("op_printed_tip"))
        self.printed_check.toggled.connect(self.printed_toggled)
        box.addWidget(self.printed_check)

    def printed_toggled(self, on):
        if self._loading:
            return
        self.state.printed = bool(on)
        self.touch(immediate=True)


class SectionPane(NodePane):
    """A section, a file of the document: its title where it has one to set here, the file it is, whether it is printed; **its sharing** -- the documents it is shared with, «Partager avec…» and «Arrêter le partage» -- and «Baliser ce fichier» where it holds text that is not tagged yet. The three buttons ask the host (`shareRequested`, `stopShareRequested`, `tagRequested`) and change nothing here: the tab writes."""
    tagRequested = Signal()
    shareRequested = Signal()
    stopShareRequested = Signal()

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_section"))
        box = QVBoxLayout(card)
        self.title_form = cards.form()
        self.title_edit = self.line_edit(self.title_edited)
        self.title_label = QLabel(t("op_title"))
        self.title_form.addRow(self.title_label, self.title_edit)
        box.addLayout(self.title_form)
        self.file_note = cards.note("")
        self.file_note.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(self.file_note)
        self.printed_row(box)
        layout.addWidget(card)

        self.share_card = cards.card(t("op_share_title"))
        box = QVBoxLayout(self.share_card)
        self.share_note = cards.note("")
        box.addWidget(self.share_note)
        row = QHBoxLayout()
        row.setSpacing(6)
        self.share_button = self.button("op_share_button", self.shareRequested.emit, "op_share_tip")
        self.stop_button = self.button("op_stop_share_button", self.stopShareRequested.emit, "op_stop_share_tip")
        row.addWidget(self.share_button)
        row.addWidget(self.stop_button)
        row.addStretch(1)
        box.addLayout(row)
        layout.addWidget(self.share_card)

        self.tag_card = cards.card(t("op_tag_title"))
        box = QVBoxLayout(self.tag_card)
        box.addWidget(cards.note(t("op_tag_note")))
        self.tag_button = self.button("op_tag_button", self.tagRequested.emit)
        box.addWidget(self.tag_button)
        layout.addWidget(self.tag_card)

    def refresh(self):
        self.title_label.setVisible(self.state.has_title)
        self.title_edit.setVisible(self.state.has_title)
        was = self.title_edit.blockSignals(True)
        self.title_edit.setText(self.state.title)
        self.title_edit.blockSignals(was)
        self.file_note.setText(self.t("op_file", file=self.state.file) if self.state.file else "")
        self.file_note.setVisible(bool(self.state.file))
        self.printed_check.set(self.state.printed)
        shared = tuple(self.state.shared_with)
        self.share_card.setVisible(bool(self.state.sharing))
        self.share_note.setText(self.t("op_share_with", documents=", ".join(shared)) if shared else self.t("op_share_none"))
        self.stop_button.setEnabled(bool(shared))
        self.stop_button.setToolTip(self.t("op_stop_share_tip") if shared else self.t("op_stop_share_off"))
        self.tag_card.setVisible(self.state.untagged)

    def title_edited(self, typed):
        self.state.title = typed
        self.touch(immediate=False)


class ChapterPane(NodePane):
    """A chapter, a group of the document: its title in each of the three languages -- the document's own is the one printed -- and whether it is printed."""

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_chapter"))
        box = QVBoxLayout(card)
        box.addWidget(cards.note(t("op_chapter_titles")))
        form = cards.form()
        self.title_edits = {}
        for lang in LANGUAGES:
            edit = self.line_edit(lambda typed, lang=lang: self.title_edited(lang, typed))
            self.title_edits[lang] = edit
            form.addRow(QLabel(LANGUAGE_NAMES[lang]), edit)
        box.addLayout(form)
        self.printed_row(box)
        layout.addWidget(card)

    def refresh(self):
        for lang, edit in self.title_edits.items():
            was = edit.blockSignals(True)
            edit.setText(self.state.titles.get(lang, ""))
            edit.blockSignals(was)
        self.printed_check.set(self.state.printed)

    def title_edited(self, lang, typed):
        self.state.titles[lang] = typed
        self.touch(immediate=False)


# --- choosing the pane, and the host that swaps them ---------------------------------------------------------------------

PANES = {
    "table": RawTablePane,   # a table written in raw Typst (spec 2026-10-21-commandes-typst-refonte, ARCH-004)
    "show-norm-list": NormListPane,
    "heading": HeadingPane,
    "text": TextPane,
    "section": SectionPane,
    "chapter": ChapterPane,
}
# What the tree calls a file and a group.
ALIASES = {"file": "section", "group": "chapter"}


def kinds():
    return tuple(PANES)


def pane_for(kind, context=None, parent=None):
    """The pane that edits an object of `kind` -- the type of its tag (`doc-table`, `live-load-table`, `heading`, `text`, …), or `section` and `chapter` for a file and a group of the tree."""
    kind = ALIASES.get(kind, kind)
    if kind not in PANES:
        raise KeyError(f"no pane edits {kind!r} -- the kinds are {', '.join(PANES)}")
    return PANES[kind](context, parent)


class ObjectPaneHost(QWidget):
    """The right pane of the «Structure du document» tab: the pane of whatever is selected, swapped as the selection moves.

    `show_object(kind, subject)` flushes what the pane shown before had pending -- first thing, before the host's own notion of the selection moves -- then shows the pane of `kind` over `subject`; `clear()` and `show_many(n)` show a sentence in place of a pane. `changed(kind, payload)` carries the edits of the pane shown, `tagRequested` the request of a section's «Baliser ce fichier», `shareRequested` and `stopShareRequested` those of its «Partager avec…» and «Arrêter le partage». By default the host holds its own column of cards, which scrolls up and down and never sideways and is never narrower than its cards (`scroll`); a host that sits in a column of its own passes `scroll=False`."""
    changed = Signal(str, object)
    tagRequested = Signal()
    shareRequested = Signal()
    stopShareRequested = Signal()

    def __init__(self, context=None, parent=None, scroll=True):
        super().__init__(parent)
        theme.ensure()
        self.context = as_context(context)
        self.panes = {}
        self.kind = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        if scroll:
            self.scroll, self.layout_ = cards.column()
            outer.addWidget(self.scroll)
        else:
            self.scroll = None
            self.layout_ = QVBoxLayout()
            self.layout_.setContentsMargins(0, 0, 0, 0)
            self.layout_.setSpacing(10)
            outer.addLayout(self.layout_)
        self.placeholder = cards.card("")
        box = QVBoxLayout(self.placeholder)
        self.placeholder_note = cards.note("")
        box.addWidget(self.placeholder_note)
        self.layout_.addWidget(self.placeholder)
        self.layout_.addStretch(1)
        self.say(self.t("op_empty"))

    def t(self, key, **values):
        return text(key, self.context.lang, **values)

    def say(self, words):
        self.placeholder.setTitle(self.t("op_empty_title"))
        self.placeholder_note.setText(words)
        self.placeholder.setVisible(True)

    def pane(self):
        """The pane shown, or None."""
        return self.panes.get(self.kind)

    def get_pane(self, kind):
        """The pane of `kind`, made the first time it is asked for."""
        if kind not in self.panes:
            pane = pane_for(kind, self.context)
            pane.changed.connect(lambda payload, k=kind: self.changed.emit(k, payload))
            if isinstance(pane, SectionPane):
                pane.tagRequested.connect(self.tagRequested)
                pane.shareRequested.connect(self.shareRequested)
                pane.stopShareRequested.connect(self.stopShareRequested)
            pane.setVisible(False)
            self.panes[kind] = pane
            self.layout_.insertWidget(self.layout_.count() - 1, pane)
        return self.panes[kind]

    def flush(self):
        pane = self.pane()
        if pane is not None:
            pane.flush()

    def show_object(self, kind, subject, context=None):
        """The pane of `kind` over `subject`. What the previous pane had pending is emitted first."""
        kind = ALIASES.get(kind, kind)
        self.flush()
        if context is not None:
            self.context = as_context(context)
            for pane in self.panes.values():
                pane.context = self.context
        pane = self.get_pane(kind)
        for other in self.panes.values():
            other.setVisible(other is pane)
        self.placeholder.setVisible(False)
        pane.load(subject, self.context)
        self.kind = kind
        return pane

    def clear(self):
        self.flush()
        for pane in self.panes.values():
            pane.setVisible(False)
        self.kind = None
        self.say(self.t("op_empty"))

    def show_many(self, count):
        self.flush()
        for pane in self.panes.values():
            pane.setVisible(False)
        self.kind = None
        self.say(self.t("op_many", n=count))

    def show_text(self, text):
        """No pane, and a sentence of the tab's own in its place -- what an object taken out of the document says of itself."""
        self.flush()
        for pane in self.panes.values():
            pane.setVisible(False)
        self.kind = None
        self.say(text)

    def set_language(self, lang):
        self.context.lang = lang if lang in LANGUAGES else "en"
        for pane in self.panes.values():
            pane.set_language(self.context.lang)
        if self.kind is None:
            self.say(self.t("op_empty"))
