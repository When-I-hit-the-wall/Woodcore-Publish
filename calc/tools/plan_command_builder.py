"""The «Commande Typst» entry of the position-plan tab (v0.114): every option of `#show-plan` as a control, the page that exactly that command prints compiled live beside them, and the command itself to copy.

It replaces the «Commandes Typst» card that stood at the bottom of the plan tab's right pane, which offered a handful of calls written in advance; here the engineer builds the call he wants -- the plan, its width, the legend, the axes, the scale bar, the positions to highlight, a detail round them and its zoom, the caption -- and sees what it prints before he pastes it into a .typ.

Three pieces, and the tab places them in different panes:

* `CommandOptions` -- the controls, in cards, for the right pane. `values()` is exactly the keyword arguments of `build_reference.call_show_plan`, so the command is `call_show_plan(**values)` and the controls hold no knowledge of Typst's syntax: only what differs from `show-plan`'s own defaults is written out.
* `command_text(values)` and `snippet_source(here, mode, values, language)` -- pure functions: the call, and the small Typst document the preview compiles (calc/structure_preview.py's header, then the call).
* `FireCommandOptions` and `fire_command_text` (v0.115) -- the same for `#show-fire-plan`, handed to the builder as its `options_factory` and `command_fn`.
* `CommandBuilder` -- assembles them: `options` goes in the right pane, `preview` in the centre (the command in a code field with its «Copié ✓» button over the compiled page, `pdf_pane.PdfPane.request_snippet`, newest request wins), and `set_project` / `set_plans` / `set_plan` drive both.

A control that has no effect says so rather than being absent: the scale bar is greyed where the plan has no scale (there is none to draw), and the detail and its zoom where nothing is highlighted -- a detail frames the highlighted positions, and `zoom` enlarges a detail.
"""

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QVBoxLayout, QWidget)

import build_reference as ref
import cards
import pdf_pane
import richtext
import structure_preview
import usersettings

# The widths offered; anything else is typed (a percentage of the text's width, or a length).
WIDTHS = ("100%", "80%", "60%", "50%", "40%")
# What a typed width may be: a number and its unit, as Typst reads one. Anything else is left out of the call rather than written into it.
WIDTH_PATTERN = re.compile(r"^\d+(\.\d+)?(%|cm|mm|pt|em)$")
ZOOM_RANGE = (0.5, 4.0)
ZOOM_STEP = 0.25
# The caption's three states: show-plan's own, none (no figure round the plan), and the engineer's.
CAPTIONS = ("auto", "none", "custom")
# The key of the snippet the pane shows; a new one for every command, so the pane knows which it holds.
SNIPPET_PREVIEW_FOLDER = "plan-command"

STRINGS = {
    "fr": {
        "pcb_entry": "Commande Typst",
        "pcb_plan_card": "Plan",
        "pcb_plan": "Plan",
        "pcb_width": "Largeur",
        "pcb_width_tip": "Largeur d'impression du plan entier : un pourcentage de la largeur du texte (60%) ou une longueur (12cm).",
        "pcb_display_card": "Affichage",
        "pcb_legend": "Légende sous le plan",
        "pcb_fire_legend": "Légende sur le plan",
        "pcb_axes": "Axes et leurs bulles",
        "pcb_dimensions": "Cotes",
        "pcb_lengths": "Longueurs des éléments",
        "pcb_scale_bar": "Barre d'échelle",
        "pcb_scale_bar_none": "Ce plan n'a pas d'échelle : il n'y a pas de barre à dessiner.",
        "pcb_highlight_card": "Positions mises en évidence",
        "pcb_highlight_none": "Ce plan ne porte aucun numéro de position.",
        "pcb_highlight_note": "Un halo sous le symbole de chaque position cochée.",
        "pcb_detail": "Détail autour des positions",
        "pcb_detail_needs": "Un détail encadre les positions mises en évidence : en cocher au moins une.",
        "pcb_zoom": "Agrandissement du détail",
        "pcb_zoom_needs": "Le zoom agrandit un détail.",
        "pcb_caption_card": "Légende de la figure",
        "pcb_caption_auto": "Automatique (plan et échelle)",
        "pcb_caption_none": "Aucune (pas de figure)",
        "pcb_caption_custom": "Mon texte",
        "pcb_caption_text": "Texte de la légende",
        "pcb_command": "Commande Typst",
        "pcb_copy": "Copier",
        "pcb_copied": "Copié ✓",
        "pcb_no_plan": "Aucun plan exporté : dessiner un plan, l'enregistrer, puis « Import données ».",
        "pcb_no_project": "Aucun projet ouvert.",
    },
    "de": {
        "pcb_entry": "Typst-Befehl",
        "pcb_plan_card": "Plan",
        "pcb_plan": "Plan",
        "pcb_width": "Breite",
        "pcb_width_tip": "Druckbreite des ganzen Plans: ein Prozentsatz der Textbreite (60%) oder eine Länge (12cm).",
        "pcb_display_card": "Darstellung",
        "pcb_legend": "Legende unter dem Plan",
        "pcb_fire_legend": "Legende auf dem Plan",
        "pcb_axes": "Achsen und ihre Blasen",
        "pcb_dimensions": "Masse",
        "pcb_lengths": "Längen der Elemente",
        "pcb_scale_bar": "Massstabsbalken",
        "pcb_scale_bar_none": "Dieser Plan hat keinen Massstab: es gibt keinen Balken zu zeichnen.",
        "pcb_highlight_card": "Hervorgehobene Positionen",
        "pcb_highlight_none": "Dieser Plan trägt keine Positionsnummer.",
        "pcb_highlight_note": "Ein Hof unter dem Symbol jeder angekreuzten Position.",
        "pcb_detail": "Ausschnitt um die Positionen",
        "pcb_detail_needs": "Ein Ausschnitt rahmt die hervorgehobenen Positionen: mindestens eine ankreuzen.",
        "pcb_zoom": "Vergrösserung des Ausschnitts",
        "pcb_zoom_needs": "Der Zoom vergrössert einen Ausschnitt.",
        "pcb_caption_card": "Bildunterschrift",
        "pcb_caption_auto": "Automatisch (Plan und Massstab)",
        "pcb_caption_none": "Keine (keine Abbildung)",
        "pcb_caption_custom": "Eigener Text",
        "pcb_caption_text": "Text der Unterschrift",
        "pcb_command": "Typst-Befehl",
        "pcb_copy": "Kopieren",
        "pcb_copied": "Kopiert ✓",
        "pcb_no_plan": "Kein Plan exportiert: einen Plan zeichnen, speichern, dann «Daten importieren».",
        "pcb_no_project": "Kein Projekt geöffnet.",
    },
    "en": {
        "pcb_entry": "Typst command",
        "pcb_plan_card": "Plan",
        "pcb_plan": "Plan",
        "pcb_width": "Width",
        "pcb_width_tip": "The width the whole plan is printed at: a percentage of the text's width (60%) or a length (12cm).",
        "pcb_display_card": "Display",
        "pcb_legend": "Legend under the plan",
        "pcb_fire_legend": "Legend on the plan",
        "pcb_axes": "Axes and their bubbles",
        "pcb_dimensions": "Dimensions",
        "pcb_lengths": "Lengths of the elements",
        "pcb_scale_bar": "Scale bar",
        "pcb_scale_bar_none": "This plan has no scale: there is no bar to draw.",
        "pcb_highlight_card": "Highlighted positions",
        "pcb_highlight_none": "This plan carries no position number.",
        "pcb_highlight_note": "A halo under the symbol of every position ticked.",
        "pcb_detail": "Detail round the positions",
        "pcb_detail_needs": "A detail frames the highlighted positions: tick at least one.",
        "pcb_zoom": "Enlargement of the detail",
        "pcb_zoom_needs": "The zoom enlarges a detail.",
        "pcb_caption_card": "Figure caption",
        "pcb_caption_auto": "Automatic (plan and scale)",
        "pcb_caption_none": "None (no figure)",
        "pcb_caption_custom": "My text",
        "pcb_caption_text": "Caption text",
        "pcb_command": "Typst command",
        "pcb_copy": "Copy",
        "pcb_copied": "Copied ✓",
        "pcb_no_plan": "No plan exported: draw a plan, save it, then «Import data».",
        "pcb_no_project": "No project open.",
    },
}


def text(key, lang, **values):
    """One of STRINGS in `lang` -- English where the window's language is none of the three -- its holes filled."""
    table = STRINGS[lang if lang in STRINGS else "en"]
    return table[key].format(**values) if values else table[key]


def entry_title(lang):
    """The words of the left-pane entry the tab lists this builder under: «Commande Typst»."""
    return text("pcb_entry", lang)


# --- the command, as pure functions --------------------------------------------------------------------------

def valid_width(width):
    """`width` as typed, if Typst would read it as a width; None -- show-plan's own 100% -- where it is empty, the default, or not a width at all."""
    width = (width or "").strip()
    if not width or width == "100%" or not WIDTH_PATTERN.match(width):
        return None
    return width


def command_text(values):
    """The `#show-plan(…)` call the options say: `build_reference.call_show_plan`, which writes only what differs from `show-plan`'s defaults. `values` is `CommandOptions.values()` -- or any dictionary of the same keys, missing ones meaning the default."""
    highlight = [label for label in (values.get("highlight") or []) if label]
    detail = bool(values.get("detail")) and bool(highlight)    # a detail frames highlighted positions: without one it is no detail
    zoom = values.get("zoom")
    zoom = zoom if detail and zoom not in (None, 1, 1.0) else None
    return ref.call_show_plan(
        values.get("plan") or "?",
        highlight=highlight or None,
        detail=detail,
        legend=values.get("legend", True),
        width=valid_width(values.get("width")),
        axes=values.get("axes", True),
        dimensions=values.get("dimensions", True),
        lengths=values.get("lengths", True),
        zoom=zoom,
        scale_bar=values.get("scale_bar", True),
        caption=values.get("caption"),
    )


def fire_command_text(values):
    """The `#show-fire-plan(…)` call the options say (v0.115): `build_reference.call_show_fire_plan`, which writes only what differs from `show-fire-plan`'s defaults. `values` is `FireCommandOptions.values()` -- or any dictionary of the same keys, missing ones meaning the default."""
    return ref.call_show_fire_plan(
        values.get("plan") or "?",
        legend=values.get("legend", True),
        width=valid_width(values.get("width")),
        scale_bar=values.get("scale_bar", True),
        caption=values.get("caption"),
    )


def snippet_source(here, mode, values, language=None, command_fn=None):
    """The small Typst document the preview compiles: the project's `conf`, its page and its engine (calc/structure_preview.py's header, the lines every snippet starts with) and the call -- compiled from standard input against the project's folder as the Typst root, so `show-plan` reads the project's own export."""
    lines = structure_preview.header(here, mode, language)
    return "\n".join(lines) + "\n\n" + (command_fn or command_text)(values) + "\n"


# --- the controls --------------------------------------------------------------------------------------------

class CommandOptions(QWidget):
    """Every option of `#show-plan` as a control, in cards: for the right pane of the tab. `changed(dict)` is emitted, with `values()`, at every change the engineer makes -- and not by `set_plans` or `set_plan`, which show what the tab says."""

    changed = Signal(dict)

    def __init__(self, lang="en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self.records = {}           # plan id -> its record in data/plans.json (its `labels`, its `scale`)
        self.quiet = False          # set while the controls are being filled: nothing is emitted
        self.labels = {}            # the words of each control, kept to be set again in another language

        scroll, layout = cards.column()
        self.scroll = scroll
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # the plan and its width
        self.plan_card = cards.card()
        form = cards.form(self.plan_card)
        self.plan = QComboBox()
        self.width = QComboBox()
        self.width.setEditable(True)
        self.width.addItems(WIDTHS)
        self.plan_label, self.width_label = QLabel(), QLabel()
        form.addRow(self.plan_label, self.plan)
        form.addRow(self.width_label, self.width)
        layout.addWidget(self.plan_card)

        # what is shown
        self.display_card = cards.card()
        box = QVBoxLayout(self.display_card)
        self.legend = QCheckBox()
        self.axes = QCheckBox()
        self.dimensions = QCheckBox()   # the plan's dimensions (issue #9)
        self.lengths = QCheckBox()      # the lengths beside its elements (issue #9)
        self.scale_bar = QCheckBox()
        for check in (self.legend, self.axes, self.dimensions, self.lengths, self.scale_bar):
            check.setChecked(True)
            box.addWidget(check)
        layout.addWidget(self.display_card)

        # the positions to highlight, and the detail round them
        self.highlight_card = cards.card()
        box = QVBoxLayout(self.highlight_card)
        self.highlight_note = cards.note()
        box.addWidget(self.highlight_note)
        self.positions = QListWidget()
        self.positions.setMaximumHeight(150)
        box.addWidget(self.positions)
        self.detail = QCheckBox()
        box.addWidget(self.detail)
        zoom_row = QHBoxLayout()
        self.zoom_label = QLabel()
        self.zoom = QDoubleSpinBox()
        self.zoom.setRange(*ZOOM_RANGE)
        self.zoom.setSingleStep(ZOOM_STEP)
        self.zoom.setDecimals(2)
        self.zoom.setValue(1.0)
        zoom_row.addWidget(self.zoom_label, 1)
        zoom_row.addWidget(self.zoom)
        box.addLayout(zoom_row)
        layout.addWidget(self.highlight_card)

        # the caption
        self.caption_card = cards.card()
        box = QVBoxLayout(self.caption_card)
        self.caption = QComboBox()
        self.caption_text = QLineEdit()
        box.addWidget(self.caption)
        box.addWidget(self.caption_text)
        layout.addWidget(self.caption_card)
        layout.addStretch(1)

        self.set_language(lang)
        self._enable()

        self.plan.currentIndexChanged.connect(self._plan_changed)
        self.width.currentTextChanged.connect(self._edited)
        for check in (self.legend, self.axes, self.dimensions, self.lengths, self.scale_bar, self.detail):
            check.toggled.connect(self._edited)
        self.positions.itemChanged.connect(self._edited)
        self.zoom.valueChanged.connect(self._edited)
        self.caption.currentIndexChanged.connect(self._edited)
        self.caption_text.textChanged.connect(self._edited)

    # -- the words --

    def t(self, key, **values):
        return text(key, self.lang, **values)

    def set_language(self, lang):
        """The controls' words in `lang` -- the window's language switched."""
        self.lang = lang
        self.plan_card.setTitle(self.t("pcb_plan_card"))
        self.plan_label.setText(self.t("pcb_plan"))
        self.width_label.setText(self.t("pcb_width"))
        self.width.setToolTip(self.t("pcb_width_tip"))
        self.display_card.setTitle(self.t("pcb_display_card"))
        self.legend.setText(self.t("pcb_legend"))
        self.axes.setText(self.t("pcb_axes"))
        self.dimensions.setText(self.t("pcb_dimensions"))
        self.lengths.setText(self.t("pcb_lengths"))
        self.highlight_card.setTitle(self.t("pcb_highlight_card"))
        self.highlight_note.setText(self.t("pcb_highlight_note"))
        self.detail.setText(self.t("pcb_detail"))
        self.zoom_label.setText(self.t("pcb_zoom"))
        self.caption_card.setTitle(self.t("pcb_caption_card"))
        self.caption_text.setPlaceholderText(self.t("pcb_caption_text"))
        index = self.caption.currentIndex()
        self.quiet = True
        try:
            self.caption.clear()
            for state in CAPTIONS:
                self.caption.addItem(self.t(f"pcb_caption_{state}"), state)
            self.caption.setCurrentIndex(max(index, 0))
        finally:
            self.quiet = False
        self._enable()

    # -- what the tab says --

    def set_plans(self, records):
        """The plans there are to choose from: `data/plans.json`'s `plans` (a dictionary by id) or a list of records carrying an `id`, each with the `labels` it shows and its `scale`. The plan chosen stays chosen where it still exists, else the first."""
        if isinstance(records, dict):
            records = {pid: dict(rec or {}) for pid, rec in records.items()}
        else:
            records = {rec["id"]: dict(rec) for rec in (records or [])}
        keep = self.plan.currentData()
        self.records = records
        self.quiet = True
        try:
            self.plan.clear()
            for pid in records:
                self.plan.addItem(pid, pid)
            index = self.plan.findData(keep) if keep is not None else -1
            self.plan.setCurrentIndex(index if index >= 0 else (0 if records else -1))
            self._fill_positions(preserve=[])
        finally:
            self.quiet = False
        self._enable()

    def set_plan(self, plan_id):
        """Chooses plan `plan_id` -- the plan the tab shows -- where the list has it; the highlighted positions are those of the plan before and are cleared with it."""
        index = self.plan.findData(plan_id)
        if index < 0 or index == self.plan.currentIndex():
            return
        self.quiet = True
        try:
            self.plan.setCurrentIndex(index)
            self._fill_positions(preserve=[])
        finally:
            self.quiet = False
        self._enable()

    def current_plan(self):
        return self.plan.currentData()

    def scale_of(self, plan_id=None):
        """The scale the plan has in the export, or None -- where there is none, no scale bar can be drawn."""
        record = self.records.get(plan_id or self.current_plan()) or {}
        return record.get("scale")

    def labels_of(self, plan_id=None):
        record = self.records.get(plan_id or self.current_plan()) or {}
        return [label for label in record.get("labels", []) if label]

    def values(self):
        """The options, as the keyword arguments of `build_reference.call_show_plan`."""
        ticked = [self.positions.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.positions.count())
                  if self.positions.item(i).checkState() == Qt.CheckState.Checked]
        state = self.caption.currentData()
        if state == "none":
            caption = False
        elif state == "custom":
            caption = self.caption_text.text() or None
        else:
            caption = None
        detail = self.detail.isChecked() and bool(ticked)
        return {
            "plan": self.current_plan(),
            "width": valid_width(self.width.currentText()),
            "legend": self.legend.isChecked(),
            "axes": self.axes.isChecked(),
            "dimensions": self.dimensions.isChecked(),
            "lengths": self.lengths.isChecked(),
            "scale_bar": self.scale_bar.isChecked() or self.scale_of() is None,    # no scale, no bar: the option is greyed and says nothing
            "highlight": ticked,
            "detail": detail,
            "zoom": round(self.zoom.value(), 2) if detail else 1.0,
            "caption": caption,
        }

    # -- what the engineer does --

    def _fill_positions(self, preserve):
        self.positions.blockSignals(True)
        self.positions.clear()
        for label in self.labels_of():
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if label in preserve else Qt.CheckState.Unchecked)
            self.positions.addItem(item)
        self.positions.blockSignals(False)

    def _plan_changed(self, _index=None):
        if self.quiet:
            return
        self._fill_positions(preserve=[])    # a position is a number of one plan: the other plan's are not this one's
        self._enable()
        self.changed.emit(self.values())

    def _edited(self, *_args):
        if self.quiet:
            return
        self._enable()
        self.changed.emit(self.values())

    def _enable(self):
        """What has an effect says so: the scale bar needs a scale, the detail a highlighted position, the zoom a detail, the caption's text the caption chosen to be one's own."""
        has_scale = self.scale_of() is not None
        self.scale_bar.setEnabled(has_scale)
        self.scale_bar.setToolTip("" if has_scale else self.t("pcb_scale_bar_none"))
        self.scale_bar.setText(self.t("pcb_scale_bar"))
        ticked = any(self.positions.item(i).checkState() == Qt.CheckState.Checked for i in range(self.positions.count()))
        self.detail.setEnabled(ticked)
        self.detail.setToolTip("" if ticked else self.t("pcb_detail_needs"))
        detailed = ticked and self.detail.isChecked()
        self.zoom.setEnabled(detailed)
        self.zoom_label.setEnabled(detailed)
        self.zoom.setToolTip("" if detailed else self.t("pcb_zoom_needs"))
        self.positions.setToolTip("" if self.positions.count() else self.t("pcb_highlight_none"))
        self.caption_text.setEnabled(self.caption.currentData() == "custom")


class FireCommandOptions(CommandOptions):
    """Every option of `#show-fire-plan` as a control (v0.115), for the fire-protection tab's right pane: the same cards as the position plan's, less what a fire plan has none of -- the axes, the positions to highlight, the detail round them. `values()` is exactly the keyword arguments of `build_reference.call_show_fire_plan`. The builder takes it as its `options_factory`, with `fire_command_text` as its `command_fn`."""

    def __init__(self, lang="en", parent=None):
        super().__init__(lang, parent)
        self.axes.hide()
        self.highlight_card.hide()

    def set_language(self, lang):
        super().set_language(lang)
        self.legend.setText(self.t("pcb_fire_legend"))

    def values(self):
        """The options, as the keyword arguments of `build_reference.call_show_fire_plan`."""
        state = self.caption.currentData()
        if state == "none":
            caption = False
        elif state == "custom":
            caption = self.caption_text.text() or None
        else:
            caption = None
        return {
            "plan": self.current_plan(),
            "width": valid_width(self.width.currentText()),
            "legend": self.legend.isChecked(),
            "scale_bar": self.scale_bar.isChecked() or self.scale_of() is None,    # no scale, no bar: the option is greyed and says nothing
            "caption": caption,
        }


# --- the whole -------------------------------------------------------------------------------------------------

class CommandField(richtext.CodeField):
    """The call as the site sets a code block (richtext.CodeField), its text replaceable: the call changes at every option."""

    def set_code(self, code):
        self.code = code
        self.setToolTip(code)
        QLabel.setText(self, f'<span style="white-space:pre">{richtext.typst_html(code)}</span>')


class CommandBuilder(QWidget):
    """The builder: `options` for the right pane, `preview` for the centre -- the command to copy over the page it prints, compiled again at every change (`pdf_pane.PdfPane.request_snippet`: 250 ms after the last change, the newest request winning, Typst's own message in the pane's banner where it does not compile). The widget itself is `preview`'s parent only for ownership: the tab places `options` and `preview` in their panes."""

    commandChanged = Signal(str)

    def __init__(self, lang="en", mono_font=None, copy=None, parent=None, options_factory=None, command_fn=None, cache_key=None):
        """`options_factory(lang)` makes the controls and `command_fn(values)` writes the call they say: `CommandOptions` and `command_text` -- `#show-plan` -- unless another kind of plan (a fire plan) hands over its own, with the same methods."""
        super().__init__(parent)
        self.lang = lang
        self.here = None
        self.mode = None
        self.copy_text = copy or self._clipboard
        self.command_fn = command_fn or command_text

        self.options = (options_factory or CommandOptions)(lang)
        self.preview = QWidget()
        box = QVBoxLayout(self.preview)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)
        self.heading = QLabel()
        self.heading.setObjectName("meta")
        box.addWidget(self.heading)
        row = QHBoxLayout()
        font = mono_font
        if font is None:
            import theme
            font = theme.mono_font(self.font().pointSizeF())
        self.field = CommandField("", font)
        self.copy_button = richtext.copy_button(self.t("pcb_copy"), self.t("pcb_copied"), lambda: self.copy_text(self.command()))
        row.addWidget(self.field, 1)
        row.addWidget(self.copy_button)
        box.addLayout(row)
        self.pane_box = box
        self._pane = None          # made the first time it is needed: building the window compiles nothing (v0.117)
        # a folder of its own -- the «Structure du document» tab's snippet is compiled to the same file name otherwise --, and since v0.117 one for each tab of plans (`cache_key`): the position plans' and the fire plans' compiled into one file until then
        self.preview_folder = usersettings.cache_dir(SNIPPET_PREVIEW_FOLDER, cache_key) if cache_key else usersettings.cache_dir(SNIPPET_PREVIEW_FOLDER)

        self.options.changed.connect(self._changed)
        self.set_language(lang)

    @property
    def pane(self):
        """The compiled page, made the first time it is needed (v0.117: the plan tabs' «Typst» view, not the window's building)."""
        if self._pane is None:
            self._pane = pdf_pane.PdfPane(self.preview, lang=self.lang, snippets_only=True)   # never the document's own PDF, whose title page showed while the first snippet compiled (issue #21)
            self._pane.preview_folder = self.preview_folder
            self.pane_box.addWidget(self._pane, 1)
        return self._pane

    @staticmethod
    def _clipboard(command):
        QApplication.clipboard().setText(command)

    # -- the words --

    def t(self, key, **values):
        return text(key, self.lang, **values)

    def set_language(self, lang):
        self.lang = lang
        self.options.set_language(lang)
        if self._pane is not None:
            self._pane.set_language(lang)
        self.heading.setText(self.t("pcb_command"))
        self.copy_button.setText(self.t("pcb_copy"))
        self._show_command()

    # -- what the tab says --

    def set_project(self, here, mode=None):
        """The project the preview is compiled against, and the document of it the snippet is compiled as -- `mode`, else the first document the project has. `here` None: no project, nothing to compile."""
        self.here = here
        self.mode = None
        if here is not None:
            self.mode = mode if mode in here.modes else here.modes[0]
            self.pane.set_document(here, self.mode)
        self.refresh()

    def set_plans(self, records):
        self.options.set_plans(records)
        self._show_command()
        self.refresh()

    def set_plan(self, plan_id):
        self.options.set_plan(plan_id)
        self._show_command()
        self.refresh()

    def command(self):
        """The `#show-plan(…)` call for the options as they stand."""
        return self.command_fn(self.options.values())

    def source(self):
        """The Typst source the preview compiles -- None where there is no project, or no plan."""
        if self.here is None or not self.options.current_plan():
            return None
        return snippet_source(self.here, self.mode, self.options.values(), None, self.command_fn)

    def refresh(self):
        """Asks the pane for the page of the command as it stands: compiled a moment from now, the newest request winning. Nothing is asked where there is no project or no plan, and the pane then says there is nothing to show."""
        if self.here is None:
            self.pane.placeholder.setText(self.t("pcb_no_project"))
            return
        source = self.source()
        if source is None:
            self.pane.placeholder.setText(self.t("pcb_no_plan"))
            return
        self.pane.request_snippet(self.here, self.mode, source, self.command())

    def stop(self):
        if self._pane is not None:
            self._pane.stop()

    # -- what the engineer does --

    def _show_command(self):
        command = self.command() if self.options.current_plan() else ""
        self.field.set_code(command)
        self.copy_button.setEnabled(bool(command))
        return command

    def _changed(self, _values):
        command = self._show_command()
        self.commandChanged.emit(command)
        self.refresh()
