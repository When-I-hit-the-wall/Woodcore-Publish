"""The editors of an image, a plan, a fire plan, an extract and the annexes in the right pane -- what a picture's width, a plan's options and an extract's pages are -- split out of calc/tools/object_panes.py (issue #30), moved verbatim. object_panes.py imports every name back.
"""

from PySide6.QtCore import QEvent, QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)
import cards  # the cards a pane is made of (cards.py)
import typst_objects as objects  # the models the panes edit (calc/typst_objects.py)
from typst_objects import AUTO, Content, Expr, ModelError
from object_panes_fields import (  # split out of this module (issue #30): every name it had is still importable from it
    CellField,
    DEBOUNCE_MS,
    ListBox,
    OverrideField,
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
    make_combo,
    parse_number,
    plain,
    show_number,
    variable_of,
)


class ImagePane(Pane):
    """A picture of the document (`doc-image`): its file -- chosen under the project's folder -- its caption, its width and the text of the empty frame printed while there is no file."""
    KINDS = ("doc-image",)

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_image"))
        box = QVBoxLayout(card)
        form = cards.form()
        self.file_label = QLabel()
        self.file_label.setWordWrap(True)
        self.file_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow(QLabel(t("op_image_file")), self.file_label)
        row = QHBoxLayout()
        self.choose_button = self.button("op_image_choose", self.choose_file)
        self.clear_button = self.button("op_remove", self.clear_file)
        row.addWidget(self.choose_button)
        row.addWidget(self.clear_button)
        row.addStretch(1)
        form.addRow(row)
        self.caption_edit = self.line_edit(lambda typed: self.do(self.model.set_caption, typed if typed.strip() else None, immediate=False))
        form.addRow(QLabel(t("op_caption")), self.caption_edit)
        self.width_edit = self.line_edit(self.width_edited, "100%")
        form.addRow(QLabel(t("op_width")), self.width_edit)
        self.placeholder_edit = self.line_edit(lambda typed: self.do(self.model.set_placeholder, typed if typed.strip() else None, immediate=False))
        form.addRow(QLabel(t("op_placeholder")), self.placeholder_edit)
        box.addLayout(form)
        layout.addWidget(card)

    def refresh(self):
        file = self.model.get("file")
        self.file_label.setText(file if isinstance(file, str) and file else self.t("op_image_none"))
        self.clear_button.setVisible(isinstance(file, str) and bool(file))
        self.set_edit(self.caption_edit, self.model.get("caption"), self.t("op_expr"))
        self.set_edit(self.placeholder_edit, self.model.get("placeholder"), self.t("op_expr"))
        set_width(self.width_edit, self.model.get("width"), self.t("op_expr"))

    def choose_file(self):
        chosen = self.context.choose_image(self)
        if chosen is None:
            return
        if not isinstance(chosen, str) or not chosen:
            self.say(self.t("op_err_outside"))
            return
        ok, _ = self.do(self.model.set_file, chosen)
        if ok:
            self.reload_view()

    def clear_file(self):
        ok, _ = self.do(self.model.set_file, None)
        if ok:
            self.reload_view()

    def width_edited(self, typed):
        write_width(self, typed)


def set_width(edit, value, expression_words):
    """A width field shown as the model holds it: `60%`; an expression read only."""
    was = edit.blockSignals(True)
    if isinstance(value, Expr):
        edit.setText("")
        edit.setPlaceholderText(expression_words)
        edit.setEnabled(False)
    else:
        edit.setText(objects.inline(value))
        edit.setEnabled(True)
    edit.blockSignals(was)


def write_width(pane, typed):
    """The width typed -- `60%`, `8cm`, nothing for the default -- written to the pane's model, or refused in a sentence."""
    shown = typed.strip().replace(" ", "") or "100%"
    try:
        width = objects.length(shown)
    except ValueError:
        pane.say(pane.t("op_err_width"))
        return
    pane.do(pane.model.set_width, width, immediate=False)


class PlanPane(Pane):
    """An extract of a position plan (`doc-plan`): which plan, the positions set on a halo, the close-up around them and its zoom, the axes, the legend, the scale bar, the width and the caption -- automatic (the plan's own), a text of the engineer's, or none."""
    KINDS = ("doc-plan",)
    CAPTIONS = ("auto", "text", "none")

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_plan"))
        form = cards.form(card)
        self.plan_combo = make_combo()
        self.plan_combo.currentIndexChanged.connect(self.plan_chosen)
        form.addRow(QLabel(t("op_plan_which")), self.plan_combo)
        self.no_plans = cards.note(t("op_plan_none"))
        form.addRow(self.no_plans)
        self.width_edit = self.line_edit(self.width_edited, "100%")
        form.addRow(QLabel(t("op_width")), self.width_edit)
        layout.addWidget(card)

        card = cards.card(t("op_plan_highlight"))
        box = QVBoxLayout(card)
        self.position_list = self.make_list(5)
        self.position_list.itemChanged.connect(self.position_ticked)
        box.addWidget(self.position_list)
        self.detail_check = Switch(t("op_plan_detail"))
        self.detail_check.toggled.connect(self.detail_toggled)
        box.addWidget(self.detail_check)
        form = cards.form()
        self.zoom_spin = QDoubleSpinBox()
        self.zoom_spin.setRange(0.25, 20.0)
        self.zoom_spin.setSingleStep(0.25)
        self.zoom_spin.setDecimals(2)
        self.zoom_spin.valueChanged.connect(self.zoom_changed)
        form.addRow(QLabel(t("op_plan_zoom")), self.zoom_spin)
        box.addLayout(form)
        layout.addWidget(card)

        card = cards.card(t("op_plan_display"))
        box = QVBoxLayout(card)
        self.axes_check = Switch(t("op_plan_axes"))
        self.axes_check.toggled.connect(lambda on: self.do(self.model.set_axes, bool(on)))
        self.dimensions_check = Switch(t("op_plan_dimensions"))   # issue #9
        self.dimensions_check.toggled.connect(lambda on: self.do(self.model.set_dimensions, bool(on)))
        self.lengths_check = Switch(t("op_plan_lengths"))
        self.lengths_check.toggled.connect(lambda on: self.do(self.model.set_lengths, bool(on)))
        self.legend_check = Switch(t("op_plan_legend"))
        self.legend_check.toggled.connect(lambda on: self.do(self.model.set_legend, bool(on)))
        self.scale_check = Switch(t("op_plan_scale_bar"))
        self.scale_check.toggled.connect(lambda on: self.do(self.model.set_scale_bar, bool(on)))
        for one in (self.axes_check, self.dimensions_check, self.lengths_check, self.legend_check, self.scale_check):
            box.addWidget(one)
        form = cards.form()
        self.caption_combo = make_combo()
        for kind, words in (("auto", "op_caption_auto"), ("text", "op_caption_text"), ("none", "op_caption_none")):
            self.caption_combo.addItem(t(words), kind)
        self.caption_combo.currentIndexChanged.connect(self.caption_mode)
        form.addRow(QLabel(t("op_caption")), self.caption_combo)
        self.caption_edit = self.line_edit(self.caption_edited)
        form.addRow(QLabel(""), self.caption_edit)
        box.addLayout(form)
        layout.addWidget(card)

    def refresh(self):
        wanted = self.model.get("plan")
        was = self.plan_combo.blockSignals(True)
        self.plan_combo.clear()
        self.plan_combo.addItem(self.t("op_choose"), None)
        known = set()
        for plan in self.context.plans():
            self.plan_combo.addItem(f"{plan.id} — {plan.label}" if plan.label else plan.id, plan.id)
            known.add(plan.id)
        if isinstance(wanted, str) and wanted not in known:
            self.plan_combo.addItem(self.t("op_unknown", id=wanted), wanted)
        self.plan_combo.setCurrentIndex(max(self.plan_combo.findData(wanted), 0) if wanted else 0)
        self.plan_combo.blockSignals(was)
        self.no_plans.setVisible(not known)
        self.refresh_positions()
        detail = self.model.get("detail")
        self.detail_check.set(detail)
        was = self.zoom_spin.blockSignals(True)
        zoom = self.model.get("zoom")
        self.zoom_spin.setValue(float(zoom) if isinstance(zoom, (int, float)) and not isinstance(zoom, bool) else 1.0)
        self.zoom_spin.blockSignals(was)
        self.zoom_spin.setEnabled(bool(detail))
        self.axes_check.set(self.model.get("axes"))
        self.dimensions_check.set(self.model.get("dimensions"))
        self.lengths_check.set(self.model.get("lengths"))
        self.legend_check.set(self.model.get("legend"))
        self.scale_check.set(self.model.get("scale-bar"))
        set_width(self.width_edit, self.model.get("width"), self.t("op_expr"))
        caption = self.model.get("caption")
        mode = "auto" if caption is AUTO else ("none" if caption is None else "text")
        was = self.caption_combo.blockSignals(True)
        self.caption_combo.setCurrentIndex(self.CAPTIONS.index(mode))
        self.caption_combo.blockSignals(was)
        self.set_edit(self.caption_edit, caption if mode == "text" else None, self.t("op_expr"))
        self.caption_edit.setEnabled(mode == "text" and plain(caption) is not None)

    # -- the plan and its positions

    def highlighted(self):
        value = self.model.get("highlight")
        if value is None:
            return []
        return list(value) if isinstance(value, (list, tuple)) else [value]

    def refresh_positions(self):
        plan = self.context.plan(self.model.get("plan")) if isinstance(self.model.get("plan"), str) else None
        listed = list(plan.positions) if plan is not None else []
        chosen = [h for h in self.highlighted() if isinstance(h, str)]
        self._loading += 1
        try:
            self.position_list.clear()
            for position in listed + [h for h in chosen if h not in listed]:
                item = QListWidgetItem(position if position in listed else self.t("op_unknown", id=position))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if position in chosen else Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, position)
                self.position_list.addItem(item)
        finally:
            self._loading -= 1

    def plan_chosen(self, _index):
        if self._loading:
            return
        ok, _ = self.do(self.model.set_plan, self.plan_combo.currentData())
        if ok:
            self.refresh_positions()

    def position_ticked(self, _item):
        if self._loading or not self.ready():
            return
        ticked = [self.position_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.position_list.count())
                  if self.position_list.item(i).checkState() == Qt.CheckState.Checked]
        highlight = None if not ticked else (ticked[0] if len(ticked) == 1 else ticked)
        self.do(self.model.set_highlight, highlight)

    def detail_toggled(self, on):
        ok, _ = self.do(self.model.set_detail, bool(on))
        if ok:
            self.zoom_spin.setEnabled(bool(on))

    def zoom_changed(self, value):
        if self._loading:
            return
        self.do(self.model.set_zoom, int(value) if float(value).is_integer() else value, immediate=False)

    def width_edited(self, typed):
        write_width(self, typed)

    def caption_mode(self, _index):
        if self._loading:
            return
        mode = self.caption_combo.currentData()
        value = AUTO if mode == "auto" else (None if mode == "none" else (self.caption_edit.text() or self.t("op_caption")))
        ok, _ = self.do(self.model.set_caption, value)
        if ok:
            self.reload_view()

    def caption_edited(self, typed):
        self.do(self.model.set_caption, typed if typed.strip() else None, immediate=False)


class FirePlanPane(Pane):
    """A fire-protection plan (`doc-fire-plan`, v0.115): which plan -- chosen among those of Woodcore's «Plan de protection incendie» tab --, its width, the legend drawn on it, the scale bar and the caption: automatic (the plan's own), a text of the engineer's, or none."""
    KINDS = ("doc-fire-plan",)
    CAPTIONS = ("auto", "text", "none")

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_fire_plan"))
        form = cards.form(card)
        self.plan_combo = make_combo()
        self.plan_combo.currentIndexChanged.connect(self.plan_chosen)
        form.addRow(QLabel(t("op_fire_plan_which")), self.plan_combo)
        self.no_plans = cards.note(t("op_fire_plan_none"))
        form.addRow(self.no_plans)
        self.width_edit = self.line_edit(self.width_edited, "100%")
        form.addRow(QLabel(t("op_width")), self.width_edit)
        layout.addWidget(card)

        card = cards.card(t("op_plan_display"))
        box = QVBoxLayout(card)
        self.legend_check = Switch(t("op_plan_legend"))
        self.legend_check.toggled.connect(lambda on: self.do(self.model.set_legend, bool(on)))
        self.scale_check = Switch(t("op_plan_scale_bar"))
        self.scale_check.toggled.connect(lambda on: self.do(self.model.set_scale_bar, bool(on)))
        for one in (self.legend_check, self.scale_check):
            box.addWidget(one)
        form = cards.form()
        self.caption_combo = make_combo()
        for kind, words in (("auto", "op_caption_auto"), ("text", "op_caption_text"), ("none", "op_caption_none")):
            self.caption_combo.addItem(t(words), kind)
        self.caption_combo.currentIndexChanged.connect(self.caption_mode)
        form.addRow(QLabel(t("op_caption")), self.caption_combo)
        self.caption_edit = self.line_edit(self.caption_edited)
        form.addRow(QLabel(""), self.caption_edit)
        box.addLayout(form)
        layout.addWidget(card)

    def refresh(self):
        wanted = self.model.get("plan")
        was = self.plan_combo.blockSignals(True)
        self.plan_combo.clear()
        self.plan_combo.addItem(self.t("op_choose"), None)
        known = set()
        for plan in self.context.fire_plans():
            self.plan_combo.addItem(f"{plan.id} — {plan.label}" if plan.label else plan.id, plan.id)
            known.add(plan.id)
        if isinstance(wanted, str) and wanted not in known:
            self.plan_combo.addItem(self.t("op_unknown", id=wanted), wanted)
        self.plan_combo.setCurrentIndex(max(self.plan_combo.findData(wanted), 0) if wanted else 0)
        self.plan_combo.blockSignals(was)
        self.no_plans.setVisible(not known)
        self.legend_check.set(self.model.get("legend"))
        self.scale_check.set(self.model.get("scale-bar"))
        set_width(self.width_edit, self.model.get("width"), self.t("op_expr"))
        caption = self.model.get("caption")
        mode = "auto" if caption is AUTO else ("none" if caption is None else "text")
        was = self.caption_combo.blockSignals(True)
        self.caption_combo.setCurrentIndex(self.CAPTIONS.index(mode))
        self.caption_combo.blockSignals(was)
        self.set_edit(self.caption_edit, caption if mode == "text" else None, self.t("op_expr"))
        self.caption_edit.setEnabled(mode == "text" and plain(caption) is not None)

    def plan_chosen(self, _index):
        if self._loading:
            return
        ok, _ = self.do(self.model.set_plan, self.plan_combo.currentData())
        if ok:
            self.reload_view()

    def width_edited(self, typed):
        write_width(self, typed)

    def caption_mode(self, _index):
        if self._loading:
            return
        mode = self.caption_combo.currentData()
        value = AUTO if mode == "auto" else (None if mode == "none" else (self.caption_edit.text() or self.t("op_caption")))
        ok, _ = self.do(self.model.set_caption, value)
        if ok:
            self.reload_view()

    def caption_edited(self, typed):
        self.do(self.model.set_caption, typed if typed.strip() else None, immediate=False)


class ExtractPane(Pane):
    """An excerpt of an annex (`doc-extract`, v0.115): which excerpt -- chosen among those of Woodcore's «Annexes» tab --, its width and its caption: automatic (the source and its page), a text of the engineer's, or none."""
    KINDS = ("doc-extract",)
    CAPTIONS = ("auto", "text", "none")

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_extract"))
        form = cards.form(card)
        self.excerpt_combo = make_combo()
        self.excerpt_combo.currentIndexChanged.connect(self.excerpt_chosen)
        form.addRow(QLabel(t("op_extract_which")), self.excerpt_combo)
        self.no_excerpts = cards.note(t("op_extract_none"))
        form.addRow(self.no_excerpts)
        self.unresolved = cards.note(t("op_extract_unresolved"))
        form.addRow(self.unresolved)
        self.width_edit = self.line_edit(self.width_edited, "100%")
        form.addRow(QLabel(t("op_width")), self.width_edit)
        self.caption_combo = make_combo()
        for kind, words in (("auto", "op_caption_auto"), ("text", "op_caption_text"), ("none", "op_caption_none")):
            self.caption_combo.addItem(t(words), kind)
        self.caption_combo.currentIndexChanged.connect(self.caption_mode)
        form.addRow(QLabel(t("op_caption")), self.caption_combo)
        self.caption_edit = self.line_edit(self.caption_edited)
        form.addRow(QLabel(""), self.caption_edit)
        layout.addWidget(card)

    def refresh(self):
        wanted = self.model.get("excerpt")
        was = self.excerpt_combo.blockSignals(True)
        self.excerpt_combo.clear()
        self.excerpt_combo.addItem(self.t("op_choose"), None)
        known = {}
        for excerpt in self.context.excerpts():
            self.excerpt_combo.addItem(excerpt.label, excerpt.id)
            known[excerpt.id] = excerpt
        if isinstance(wanted, str) and wanted not in known:
            self.excerpt_combo.addItem(self.t("op_unknown", id=wanted), wanted)
        self.excerpt_combo.setCurrentIndex(max(self.excerpt_combo.findData(wanted), 0) if wanted else 0)
        self.excerpt_combo.blockSignals(was)
        self.no_excerpts.setVisible(not known)
        self.unresolved.setVisible(wanted in known and not known[wanted].resolved)
        set_width(self.width_edit, self.model.get("width"), self.t("op_expr"))
        caption = self.model.get("caption")
        mode = "auto" if caption is AUTO else ("none" if caption is None else "text")
        was = self.caption_combo.blockSignals(True)
        self.caption_combo.setCurrentIndex(self.CAPTIONS.index(mode))
        self.caption_combo.blockSignals(was)
        self.set_edit(self.caption_edit, caption if mode == "text" else None, self.t("op_expr"))
        self.caption_edit.setEnabled(mode == "text" and plain(caption) is not None)

    def excerpt_chosen(self, _index):
        if self._loading:
            return
        ok, _ = self.do(self.model.set_excerpt, self.excerpt_combo.currentData())
        if ok:
            self.reload_view()

    def width_edited(self, typed):
        write_width(self, typed)

    def caption_mode(self, _index):
        if self._loading:
            return
        mode = self.caption_combo.currentData()
        value = AUTO if mode == "auto" else (None if mode == "none" else (self.caption_edit.text() or self.t("op_caption")))
        ok, _ = self.do(self.model.set_caption, value)
        if ok:
            self.reload_view()

    def caption_edited(self, typed):
        self.do(self.model.set_caption, typed if typed.strip() else None, immediate=False)


class AnnexesPane(Pane):
    """The annexes of the project at this point of the document (`doc-annexes`, v0.115): the level each annex's name is set as a heading at, or none -- the name in bold on its cover page, the outline left to the engineer."""
    KINDS = ("doc-annexes",)

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_annexes"))
        box = QVBoxLayout(card)
        box.addWidget(cards.note(t("op_annexes_note")))
        form = cards.form()
        self.heading_check = Switch(t("op_annexes_heading_on"))
        self.heading_check.toggled.connect(self.heading_toggled)
        box.addWidget(self.heading_check)
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 6)
        self.level_spin.valueChanged.connect(self.level_changed)
        form.addRow(QLabel(t("op_annexes_level")), self.level_spin)
        box.addLayout(form)
        layout.addWidget(card)

    def refresh(self):
        level = self.model.get("heading")
        on = isinstance(level, int) and not isinstance(level, bool)
        self.heading_check.set(on)
        was = self.level_spin.blockSignals(True)
        self.level_spin.setValue(level if on else 2)
        self.level_spin.blockSignals(was)
        self.level_spin.setEnabled(on)

    def heading_toggled(self, on):
        if self._loading:
            return
        ok, _ = self.do(self.model.set_heading, self.level_spin.value() if on else None)
        if ok:
            self.level_spin.setEnabled(bool(on))

    def level_changed(self, value):
        if self._loading:
            return
        self.do(self.model.set_heading, int(value), immediate=False)
