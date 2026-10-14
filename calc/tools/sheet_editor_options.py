"""The right pane of the export sheets' editor -- the options of the sheet and of the object chosen -- split out of calc/tools/sheet_editor.py (issue #30), moved verbatim. sheet_editor.py imports every name back.
"""

from PySide6.QtCore import QBuffer, QByteArray, QFileSystemWatcher, QIODevice, QObject, QPointF, QRect, QRectF, QSize, QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMessageBox,
                               QPlainTextEdit, QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget)
import cards
import flowbar
import sheets
import typst_objects as to
from sheet_editor_words import BUNDLE_KEYS, STRINGS, bundle_words, words  # split out of this module (issue #30): every name it had is still importable from it
from sheet_editor_render import (  # split out of this module (issue #30): every name it had is still importable from it
    BOX_LABEL,
    BOX_QUERY,
    Box,
    COMPILE_TIMEOUT_S,
    Compiler,
    DEBOUNCE_MS,
    DRAWING_KINDS,
    LEGEND_KINDS,
    RESIZABLE_KINDS,
    SNAP_MM,
    TITLE_MM,
    _Job,
    _RUNNING,
    _count_positions,
    _objects,
    _position,
    cache_target,
    drawing_width,
    estimate_boxes,
    file_signature,
    markup_of,
    match_boxes,
    parse_boxes,
    parse_scale,
    query_args,
    read_fire_plans,
    read_plans,
    render,
    scale_for,
    snap,
    units_per_m,
)


# How long typed text (a text's body) waits before it is written.
TYPING_MS = 400


# The scales offered in the scale combo, the n of 1:n.
SCALES = (20, 50, 100, 200, 500)


# The SIA 112 phases a sheet is drawn in, offered in the title block's phase combo.
PHASES = ("31", "32", "33", "41", "51", "52", "53")


# The title block's cells the options pane edits, and those of them that take the project's value at `auto`.
CELLS = ("object", "element", "client", "architect", "phase", "plan-number", "index", "modification", "drawn-by", "date", "scale")


AUTO_CELLS = frozenset(name for name in CELLS if to.DEFAULTS["sheet-titleblock"][name] is to.AUTO)


def _spin(minimum, maximum, decimals=1, suffix=""):
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setKeyboardTracking(False)
    if suffix:
        box.setSuffix(suffix)
    return box


class _Blocked:
    """Signals of the widgets given held while a value is set from the file, so that showing a value never writes it back."""

    def __init__(self, *widgets):
        self.widgets = widgets

    def __enter__(self):
        for w in self.widgets:
            w.blockSignals(True)

    def __exit__(self, *_):
        for w in self.widgets:
            w.blockSignals(False)


class SheetOptions(QWidget):
    """The right pane of the sheet editor, in cards, **driven by what is chosen on the sheet** (v0.116, the engineer: «lorsque je clique sur le titre … uniquement le module texte»):

    * nothing chosen: the module «Feuille» -- format, orientation, margin, the PDF -- and the module «Options»: a switch for the title block and one for the legend, and one under another the buttons that add a plan view, a schematic section, a text and a list of the positions (a fire sheet: a fire-protection plan and a text). An object added shows no options until it is chosen;
    * one object chosen: its own module and nothing else -- «Titre» for the sheet's title, «Texte» for any other text, «Vue en plan» for a plan with the position to highlight chosen in a list of those the plan shows, the title block's cells, the legend's width and title, the section's storey, the position list's scope.

    It reads the sheet through its editor and writes nothing itself: every change is one of the editor's methods."""

    def __init__(self, editor, lang="en"):
        super().__init__()
        self.editor = editor
        self.lang = lang
        self.object_widgets = {}
        self.cell_widgets = {}
        self.typing = QTimer(self)
        self.typing.setSingleShot(True)
        self.typing.setInterval(TYPING_MS)
        self.typing.timeout.connect(self._body_typed)
        self.typed_id = None
        self.build()

    def t(self, key, **values):
        return words(self.lang, key, **values)

    def set_language(self, lang):
        self.lang = lang
        self.build()
        self.load()

    def build(self):
        old = self.layout()
        if old is not None:
            QWidget().setLayout(old)       # the old layout and its widgets go with a throwaway parent
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll, column = cards.column()
        outer.addWidget(scroll)

        # the page and the PDF: the module «Feuille»
        self.page_card = cards.card(self.t("se_title_page"))
        form = cards.form(self.page_card)
        self.format_combo = QComboBox()
        self.format_combo.addItems(list(sheets.FORMATS))
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem(self.t("se_portrait"), False)
        self.orientation_combo.addItem(self.t("se_landscape"), True)
        self.margin_spin = _spin(0, 50, 1, " mm")
        form.addRow(self.t("se_format"), self.format_combo)
        form.addRow(self.t("se_orientation"), self.orientation_combo)
        form.addRow(self.t("se_margin"), self.margin_spin)
        self.export_button = QPushButton(self.t("se_export"))
        self.export_button.setProperty("primary", True)
        flowbar.set_tip(self.export_button, self.t("se_export"), self.t("se_export_usage", id=self.editor.sheet_id or "…"))
        form.addRow(self.export_button)
        self.format_combo.currentTextChanged.connect(lambda text: self.editor.set_page(format=text))
        self.orientation_combo.currentIndexChanged.connect(lambda _i: self.editor.set_page(landscape=self.orientation_combo.currentData()))
        self.margin_spin.valueChanged.connect(lambda value: self.editor.set_page(margin=value))
        self.export_button.clicked.connect(self.editor.exportRequested.emit)
        column.addWidget(self.page_card)

        # the module «Options»: two switches -- the title block, the legend --, then what may be added, one under another
        self.options_card = cards.card(self.t("se_options"))
        box = QVBoxLayout(self.options_card)
        self.titleblock_check = QCheckBox(self.t("se_titleblock_show"))
        self.titleblock_check.toggled.connect(self.editor.set_titleblock)
        box.addWidget(self.titleblock_check)
        self.legend_check = QCheckBox(self.t("se_legend_show"))
        self.legend_check.toggled.connect(self.editor.set_sheet_legend)
        box.addWidget(self.legend_check)
        # one switch for the legend of the sheet's kind: a fire sheet's is the fire plans' legend
        self.fire_legend_check = self.legend_check
        self.add_buttons = {}
        for key, usage, action in (("se_add_plan_view", "se_add_plan_view_usage", self.editor.add_viewport_chosen),
                                   ("se_add_fire_view", "se_add_fire_view_usage", self.editor.add_fire_viewport_chosen),
                                   ("se_add_section_view", "se_add_section_view_usage", self.editor.add_section_chosen),
                                   ("se_add_text_object", "se_add_text_object_usage", self.editor.add_text),
                                   ("se_add_position_list", "se_add_position_list_usage", self.editor.add_position_list),
                                   ("se_add_quantities", "se_add_quantities_usage", self.editor.add_quantities)):
            button = QPushButton(self.t(key))
            flowbar.set_tip(button, button.text(), self.t(usage))
            button.clicked.connect(lambda _checked=False, action=action: action())
            box.addWidget(button)
            self.add_buttons[key] = button
        column.addWidget(self.options_card)

        # the module of the object chosen, made again for its kind
        self.object_card = cards.card("")
        self.object_layout = QVBoxLayout(self.object_card)
        column.addWidget(self.object_card)
        column.addStretch(1)

    # -- showing what the sheet holds ------------------------------------------------------

    def load(self):
        """The cards for what is chosen, filled from the sheet as it is on disk -- nothing written back."""
        e = self.editor
        enabled = e.sheet_id is not None
        for card in (self.page_card, self.options_card, self.object_card):
            card.setEnabled(enabled)
        chosen = enabled and bool(e.selected)
        self.page_card.setVisible(not chosen)
        self.options_card.setVisible(not chosen)
        self.object_card.setVisible(chosen)
        if not enabled:
            self._fill_object()
            return
        page = e.page_model()
        with _Blocked(self.format_combo, self.orientation_combo, self.margin_spin):
            if page is not None:
                self.format_combo.setCurrentText(page.get("format") if isinstance(page.get("format"), str) else "A3")
                self.orientation_combo.setCurrentIndex(1 if page.get("landscape") is not False else 0)
                self.margin_spin.setValue(to.mm_of(page.get("margin")) or 0.0)
        flowbar.set_tip(self.export_button, self.t("se_export"), self.t("se_export_usage", id=e.sheet_id))
        objs = e.objects()
        kind = e.sheet_kind()
        legend_type = "sheet-fire-legend" if kind == "fire" else "sheet-legend"
        with _Blocked(self.titleblock_check, self.legend_check):
            self.titleblock_check.setChecked(any(o.type == "sheet-titleblock" for o, _m in objs))
            self.legend_check.setChecked(any(o.type == legend_type for o, _m in objs))
        # what a sheet of this kind may hold, and nothing of the other kind
        shown = {"se_add_plan_view": kind == "position", "se_add_fire_view": kind == "fire", "se_add_section_view": kind == "position",
                 "se_add_text_object": True, "se_add_position_list": kind == "position", "se_add_quantities": kind == "position"}
        for key, button in self.add_buttons.items():
            button.setVisible(shown[key])
        self._fill_object()

    def _clear_object(self):
        while self.object_layout.count():
            item = self.object_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout() is not None:
                QWidget().setLayout(item.layout())
        self.object_widgets = {}
        self.cell_widgets = {}

    def module_title(self, obj):
        """The module's name for object `obj`: «Titre» for the sheet's title, «Texte» for another text, the kind's own name otherwise -- no id: the engineer reads what it is, not how the file names it."""
        if obj.type == "sheet-text" and obj.id == "title":
            return self.t("se_kind_title")
        return self.t("se_kind_" + obj.type.removeprefix("sheet-"))

    def _fill_object(self):
        """The module of the object chosen, made again for its kind."""
        self._clear_object()
        e = self.editor
        obj, model = e.selected_object()
        if obj is None:
            self.object_card.setTitle("")
            return
        self.object_card.setTitle(self.module_title(obj))
        if model is None:
            self.object_layout.addWidget(cards.note(self.t("se_why_unreadable")))
            return
        holder = QWidget()
        form = cards.form(holder)
        self.object_layout.addWidget(holder)
        w = self.object_widgets
        kind = obj.type
        if isinstance(model, to._Placed):
            x, y = model.position()
            for key, value in (("x", x), ("y", y)):
                spin = _spin(-2000, 2000, 1)
                spin.setValue(value or 0.0)
                spin.setEnabled(value is not None)
                spin.valueChanged.connect(lambda _v: e.move(obj.id, w["x"].value(), w["y"].value()))
                w[key] = spin
                form.addRow(self.t(f"se_{key}"), spin)
        if kind in DRAWING_KINDS:
            self._fill_drawing(form, obj, model)
        elif kind == "sheet-text":
            body = QPlainTextEdit()
            body.setPlainText(markup_of(model.get("body")))
            body.setFixedHeight(90)
            body.textChanged.connect(lambda: self._body_changed(obj.id))
            w["body"] = body
            form.addRow(self.t("se_body"), body)
            size = _spin(4, 200, 1)
            found = model.get("size")
            size.setValue(float(found.value) if isinstance(found, to.Length) and found.unit == "pt" else 10.0)
            size.valueChanged.connect(lambda value: e.set_text_size(obj.id, value))
            w["size"] = size
            form.addRow(self.t("se_size"), size)
            bold = QCheckBox(self.t("se_bold"))
            bold.setChecked(model.get("weight") == "bold")
            bold.toggled.connect(lambda on: e.set_bold(obj.id, on))
            w["bold"] = bold
            form.addRow(bold)
        elif kind in LEGEND_KINDS or kind in ("sheet-position-list", "sheet-quantities"):
            if kind == "sheet-position-list":
                self._fill_position_list(form, obj, model)
            width = _spin(10, 1000, 1)
            width.setValue(to.mm_of(model.get("width")) or {"sheet-position-list": 180.0, "sheet-quantities": 150.0}.get(kind, 120.0))
            width.editingFinished.connect(lambda: e.set_legend_width(obj.id, width.value()))
            w["width"] = width
            form.addRow(self.t("se_width"), width)
            title = QLineEdit()
            title.setPlaceholderText(self.t("se_auto_title"))
            title.setText(markup_of(model.get("title")))
            title.editingFinished.connect(lambda: e.set_legend_title(obj.id, title.text()))
            w["title"] = title
            form.addRow(self.t("se_title"), title)
        elif kind == "sheet-titleblock":
            self._fill_titleblock(form, obj, model)
        if kind != "sheet-titleblock":
            remove = QPushButton(self.t("se_remove"))
            flowbar.set_tip(remove, self.t("se_remove"), self.t("se_remove_usage"))
            remove.clicked.connect(e.remove_selected)
            w["remove"] = remove
            form.addRow(remove)

    def _fill_drawing(self, form, obj, model):
        """A plan, a fire-protection plan or a section: which plan, its storey (a section), its scale or width, its title (a plan), the position highlighted -- a list of those it shows --, its axes and its scale bar."""
        e = self.editor
        w = self.object_widgets
        kind = obj.type
        plans = e.plans_for(kind)
        wanted = "section" if kind == "sheet-section" else None
        combo = QComboBox()
        combo.addItem(self.t("se_no_plan"), None)
        for pid, plan in plans.items():
            role = plan.get("role", "plan") if isinstance(plan, dict) else "plan"
            if kind == "sheet-fire-viewport" or (role == "section") == (wanted == "section"):
                label = plan.get("label", "") if isinstance(plan, dict) else ""
                combo.addItem(f"{pid} — {label}" if label else pid, pid)
        current = model.get("plan")
        if current is not None and combo.findData(current) < 0:
            combo.addItem(f"{current} (?)", current)
        combo.setCurrentIndex(max(0, combo.findData(current)))
        combo.currentIndexChanged.connect(lambda _i: e.set_plan(obj.id, combo.currentData()))
        w["plan"] = combo
        form.addRow(self.t("se_plan"), combo)
        plan = plans.get(current or "", {})
        if kind == "sheet-section":
            storey = QComboBox()
            storey.addItem(self.t("se_no_storey"), None)
            for item in (plan.get("storey_boxes") or []) if isinstance(plan, dict) else []:
                name = item.get("storey") if isinstance(item, dict) else None
                if isinstance(name, str) and storey.findData(name) < 0:
                    storey.addItem(name, name)
            chosen = model.get("storey")
            if chosen is not None and storey.findData(chosen) < 0:
                storey.addItem(f"{chosen} (?)", chosen)
            storey.setCurrentIndex(max(0, storey.findData(chosen)))
            storey.currentIndexChanged.connect(lambda _i: e.set_storey(obj.id, storey.currentData()))
            w["storey"] = storey
            form.addRow(self.t("se_storey"), storey)
        calibrated = units_per_m(plan) is not None
        scale = QComboBox()
        scale.setEditable(True)
        scale.addItems([f"1:{n}" for n in SCALES])
        n = model.get("scale")
        box = e.canvas.box(obj.id)
        if not isinstance(n, (int, float)) or isinstance(n, bool):
            n = box.n if box is not None and box.n else None
        scale.setCurrentText(f"1:{int(n) if float(n) == int(n) else n}" if n else "")
        scale.setEnabled(calibrated)
        flowbar.set_tip(scale, self.t("se_scale"), self.t("se_scale_usage") if calibrated else self.t("se_not_calibrated"))
        scale.activated.connect(lambda _i: e.set_scale(obj.id, parse_scale(scale.currentText())))
        scale.lineEdit().editingFinished.connect(lambda: e.set_scale(obj.id, parse_scale(scale.currentText())))
        w["scale"] = scale
        form.addRow(self.t("se_scale"), scale)
        width = _spin(1, 5000, 1)
        dw = drawing_width(plan, model) or (box.dw if box is not None and box.dw else 0.0)
        width.setValue(dw or 0.0)
        width.editingFinished.connect(lambda: e.set_width(obj.id, width.value()))
        w["width"] = width
        form.addRow(self.t("se_width"), width)
        if kind in ("sheet-viewport", "sheet-fire-viewport"):
            title = QCheckBox(self.t("se_viewport_title"))
            title.setChecked(model.get("title") not in (None, False))
            title.toggled.connect(lambda on: e.set_viewport_title(obj.id, on))
            w["title"] = title
            form.addRow(title)
        if kind == "sheet-viewport":
            # the position highlighted: one of those the plan shows, or none
            highlight = QComboBox()
            highlight.addItem(self.t("se_highlight_none"), None)
            for label in e.positions_of_plan(current):
                highlight.addItem(label, label)
            value = model.get("highlight")
            if isinstance(value, (list, tuple)):
                value = ", ".join(value) if value else None
            if value is not None and highlight.findData(value) < 0:
                highlight.addItem(f"{value} (?)", value)
            highlight.setCurrentIndex(max(0, highlight.findData(value)))
            flowbar.set_tip(highlight, self.t("se_highlight"), self.t("se_highlight_tip"))
            highlight.activated.connect(lambda _i: e.set_highlight(obj.id, highlight.currentData() or ""))
            w["highlight"] = highlight
            form.addRow(self.t("se_highlight"), highlight)
            for key, arg, label in (("axes", "axes", "se_axes"), ("dimensions", "dimensions", "se_dimensions"), ("lengths", "lengths", "se_lengths"), ("scale_bar", "scale-bar", "se_scale_bar")):
                check = QCheckBox(self.t(label))
                check.setChecked(model.get(arg) is True)
                check.toggled.connect(lambda on, arg=arg: e.set_flag(obj.id, arg, on))
                w[key] = check
                form.addRow(check)
        elif kind == "sheet-fire-viewport":
            for key, arg, label in (("legend", "legend", "se_legend_on_plan"), ("scale_bar", "scale-bar", "se_scale_bar")):
                check = QCheckBox(self.t(label))
                check.setChecked(model.get(arg) is True)
                check.toggled.connect(lambda on, arg=arg: e.set_flag(obj.id, arg, on))
                w[key] = check
                form.addRow(check)

    def _fill_position_list(self, form, obj, model):
        """The list of the positions: which positions -- those of the sheet's plans, every one, one storey's -- and the storey."""
        e = self.editor
        w = self.object_widgets
        scope = QComboBox()
        for value, key in (("plans", "se_scope_plans"), ("all", "se_scope_all"), ("storey", "se_scope_storey")):
            scope.addItem(self.t(key), value)
        scope.setCurrentIndex(max(0, scope.findData(model.get("scope"))))
        w["scope"] = scope
        form.addRow(self.t("se_list_scope"), scope)
        storey = QComboBox()
        for char in e.storeys():
            storey.addItem(char, char)
        chosen = model.get("storey")
        if chosen is not None and storey.findData(chosen) < 0:
            storey.addItem(f"{chosen} (?)", chosen)
        storey.setCurrentIndex(max(0, storey.findData(chosen)))
        storey.setEnabled(model.get("scope") == "storey")
        w["storey"] = storey
        form.addRow(self.t("se_list_storey"), storey)
        scope.activated.connect(lambda _i: e.set_list_scope(obj.id, scope.currentData(), storey.currentData()))
        storey.activated.connect(lambda _i: e.set_list_scope(obj.id, "storey", storey.currentData()))

    def _fill_titleblock(self, form, obj, model):
        """The title block's cells -- `auto` the project's where the cell has a value of the project -- and its way back into the corner."""
        e = self.editor
        block_ok = isinstance(model, to.TitleBlockModel)
        for name in CELLS:
            if name == "phase":
                field = QComboBox()
                field.setEditable(True)
                field.addItem("")
                for phase in PHASES:
                    field.addItem(words(e.sheet_lang(), f"se_phase_{phase}"))
                field.lineEdit().editingFinished.connect(lambda name=name, field=field: e.set_cell(name, field.currentText()))
                field.activated.connect(lambda _i, name=name, field=field: e.set_cell(name, field.currentText()))
            else:
                field = QLineEdit()
                if name in AUTO_CELLS:
                    field.setPlaceholderText(self.t("se_auto_placeholder"))
                field.editingFinished.connect(lambda name=name, field=field: e.set_cell(name, field.text()))
            value = markup_of(model.get(name)) if block_ok else ""
            with _Blocked(field):
                if isinstance(field, QComboBox):
                    field.setCurrentText(value)
                else:
                    field.setText(value)
            field.setEnabled(block_ok)
            self.cell_widgets[name] = field
            form.addRow(self.t(f"se_cell_{name}"), field)
        corner = QPushButton(self.t("se_corner"))
        flowbar.set_tip(corner, self.t("se_corner"), self.t("se_corner_usage"))
        corner.clicked.connect(lambda: e.titleblock_to_corner(obj.id))
        self.object_widgets["corner"] = corner
        form.addRow(corner)

    def _body_changed(self, object_id):
        self.typed_id = object_id
        self.typing.start()

    def _body_typed(self):
        field = self.object_widgets.get("body")
        if field is not None and self.typed_id:
            self.editor.set_body(self.typed_id, field.toPlainText())

    def flush(self):
        """What is being typed written now, not 400 ms from now."""
        if self.typing.isActive():
            self.typing.stop()
            self._body_typed()
