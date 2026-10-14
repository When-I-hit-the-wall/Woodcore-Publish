"""DrawingTab's panes -- the left pane and its boxes, the tool bar, the centre and the right pane's modules by what is selected, what the left pane has chosen, and the views -- a mixin of methods moved verbatim out of calc/tools/drawing_tab.py (issue #30). DrawingTab names it among its bases.
"""

import json
from PySide6.QtCore import QByteArray, QModelIndex, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QScrollArea, QSlider, QSplitter, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)
import cards  # the properties in cards, after the website (cards.py)
import tasks  # what runs in the background, said by the chip at the top right (tasks.activity, v0.117)
import chrome  # the fold button of the left pane, the navigation's own (chrome.py, v0.117)
import grouped_list
import project  # where the project this tab works on is (calc/project.py)
import sheets  # the export sheets, Plans/<id>.typ (calc/sheets.py, v0.114)
import source_archive  # «Supprimer» archives (source_archive.py)
import document_view  # every page of a document, ticked into the plans (v0.114)
import plan_superposition  # another plan of the tab shown over the plan open (v0.116)
import sheet_editor  # the export sheets' editor (v0.114)
import sheet_list  # the export sheets' list, the PDF bundles as folders (v0.116)
import bundle_view  # an export document's pages and its fields, its folder chosen (v0.117)


# The row that stands for the plan nobody has saved yet. Not an id anything can be filed under: a plan's own id is letters, digits and `_ . + -`, so no angle bracket can reach it.
NEW_ROW = "<new>"


# What the left pane may have chosen: a plan, a document, an export sheet, the command builder -- and so what the centre and the right pane show (their stacks' pages, in this order).
KINDS = ("plan", "document", "sheet", "command", "bundle")   # «bundle»: an export document's folder chosen, its pages and its fields (v0.117)


# The left pane's boxes (v0.116): no list shorter than about three rows, whatever a drag of a box's grip asks for.
LIST_MIN_HEIGHT = 64


# The four views of a tab of plans (v0.117, the engineer's request of 07.10.2026: «document import, dessin, typst et document export»), chosen in the top bar's switch (views.py): each is one of the kinds above -- the centre's and the right pane's page -- and shows only its own boxes on the left. One table, so the view and the kind can never say two things (review A08).
VIEW_KIND = {"import": "document", "draw": "plan", "typst": "command", "export": "sheet"}


KIND_VIEW = {kind: view for view, kind in VIEW_KIND.items()}


KIND_VIEW["bundle"] = "export"


VIEW_BOXES = {"import": ("documents",), "draw": ("plans", "entries"), "typst": ("plans",), "export": ("sheets",)}


# When a card of the right pane shows (v0.116, the engineer: «le volet de droite doit davantage être dépendant de ce que l'on sélectionne»): `plan` only while nothing is selected on the plan open -- its identity, its background, its crop, its scale, and what a later version adds of the plan's own --; `selection` only while something is; `always` either way -- «Taille des symboles». (add_module, update_modules)
MODULE_WHEN = ("plan", "selection", "always")


def plain_label(text, wrap=False):
    """A label showing `text` exactly as it is -- given a text that looks like HTML, QLabel would render it as HTML."""
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


CurrentStack = cards.CurrentStack   # a stack whose size is its current page's: in cards.py since v0.117


class DrawingPanesMixin:
    """Methods of drawing_tab.DrawingTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def note(self, text):
        """An explanation, muted and wrapping, as a card's note is (cards.note)."""
        return cards.note(text)

    def button_row(self, layout, buttons):
        row = QHBoxLayout()
        made = []
        for key, slot in buttons:
            button = QPushButton(self.w(key))
            button.clicked.connect(lambda _checked=False, slot=slot: slot())
            row.addWidget(button)
            made.append(button)
        layout.addLayout(row)
        return made

    def list_section(self):
        """A box of the left pane: a widget and its column, no margin (build_list)."""
        section = QWidget()
        v = QVBoxLayout(section)
        v.setContentsMargins(0, 0, 0, 0)
        return section, v

    def add_left_box(self, name, section):
        """`section` one box of the left pane, under the others, with a grip that sets its height and its alone (cards.SizedBox, v0.117)."""
        box = cards.SizedBox(section)
        box.setObjectName(f"leftBox_{name}")
        box.set_height(None)
        self.left_boxes[name] = box
        self.left_column.addWidget(box, 1)
        return box

    def build_list(self):
        """The left pane: the documents, the plans, what the subclass lists of the plan open, and the export sheets, one under the other (v0.114) -- each a box whose height its grip drags without touching the others' (v0.117, cards.SizedBox), the whole in a column that scrolls up and down where they are taller than the window, and never sideways (cards.Column); under it, the arrow that folds the pane away (`set_left_folded`). Which boxes are shown is the view's (VIEW_BOXES): the documents in «Import», the plans and what the plan open holds in «Dessin», the plans alone in «Typst», the export sheets in «Export». The «Commande Typst» row of v0.114 is the «Typst» view since v0.117."""
        self.left_boxes = {}
        body = QWidget()
        self.left_column = QVBoxLayout(body)
        self.left_column.setContentsMargins(0, 0, 6, 0)
        self.left_column.setSpacing(4)

        section, v = self.list_section()
        self.add_left_box("documents", section)
        v.addWidget(self.heading(self.w("plan_documents")))
        self.doc_list = QListWidget()
        self.doc_list.currentItemChanged.connect(self.on_doc_row)
        v.addWidget(self.doc_list, 1)
        self.doc_hint = self.note(self.w("plan_doc_empty"))
        v.addWidget(self.doc_hint)
        self.import_button, self.delete_doc_button = self.button_row(v, (("plan_doc_import", self.import_document), ("plan_doc_delete", self.delete_document)))
        self.delete_doc_button.setToolTip(self.w("plan_doc_empty"))   # a disabled button says why (v0.47's rule)

        section, v = self.list_section()
        self.add_left_box("plans", section)
        self.list = grouped_list.GroupedList(self.list_strings(), lang=self.app.lang)
        self.archive = source_archive.Actions(self, lambda: self.sources_dir(), lambda text: self.export("", text), lambda select: self.reload_list(select), self.load_first,
                                              archive_note=lambda ids: self.followers_note(ids), before_archive=lambda ids: self.detach_followers(ids))
        self.archive.connect()
        v.addWidget(grouped_list.title_row(self.heading(self.w("plan_list")), self.list))
        self.list.setIconSize(self.app.mark_size)
        self.list.currentIdChanged.connect(self.on_list_change)
        self.list.moved.connect(self.on_moved)
        self.list.foldersChanged.connect(self.on_folders_changed)
        self.list.attach_order(self.VIEW_KEY, self.app.list_store)   # the order the engineer gives the list by drag and drop, kept in Woodcore-Datei/lists.json (calc/list_order.py, issue #15)
        self.list.reordered.connect(lambda: self.reload_list(select=self.current_id))
        v.addWidget(self.list, 2)
        self.empty_hint = self.note(self.w("plan_empty"))
        v.addWidget(self.empty_hint)
        self.plan_buttons = self.button_row(v, (("plan_new", self.new), ("plan_duplicate", self.duplicate), ("plan_delete", self.delete)))

        section, v = self.list_section()
        self.build_entries(v)
        if v.count():
            self.add_left_box("entries", section)

        section, v = self.list_section()
        self.add_left_box("sheets", section)
        bundle_words = sheet_editor.bundle_words(self.app.lang)
        self.sheet_list = sheet_list.SheetList(sheet_list.bundle_strings(bundle_words), lang=self.app.lang)   # the PDF bundles are its folders
        self.sheet_list.setIconSize(self.app.mark_size)
        self.sheet_list.currentIdChanged.connect(self.on_sheet_id)
        self.sheet_list.sheetsMoved.connect(self.on_sheets_moved)
        self.sheet_list.bundleCreateRequested.connect(self.new_bundle)
        self.sheet_list.bundleRenameRequested.connect(self.rename_bundle)
        self.sheet_list.bundleDeleteRequested.connect(self.delete_bundle)
        v.addWidget(grouped_list.title_row(self.heading(self.w("plan_sheets")), self.sheet_list))
        v.addWidget(self.sheet_list, 1)
        self.button_row(v, (("plan_sheet_new", self.new_sheet), ("plan_sheet_delete", self.delete_sheet)))
        self.bundle_buttons = self.bundle_row(v, bundle_words)
        v.addSpacing(6)
        self.sheets_layout = v   # the export sheets' box: where the sheets' own rows go (WP-I's bundles)

        for widget in (self.doc_list, self.list, self.sheet_list):
            widget.setMinimumHeight(LIST_MIN_HEIGHT)
        self.left_column.addStretch(0)   # what the boxes of fixed height leave, under them
        scroll = cards.Column()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(body)
        body.installEventFilter(scroll)   # a box grown asks the column again (cards.Column.eventFilter)
        self.left_scroll = scroll
        # at the foot of the column, «Objet sélectionné»: the object selected on the plan duplicated or deleted (issue #18, D-016) -- the plan's own «Dupliquer» and «Supprimer» stay above, with the plans
        inner = QWidget()
        iv = QVBoxLayout(inner)
        iv.setContentsMargins(0, 0, 0, 0)
        iv.setSpacing(2)
        iv.addWidget(scroll, 1)
        self.object_box = QWidget()
        ov = QVBoxLayout(self.object_box)
        ov.setContentsMargins(0, 4, 6, 0)
        ov.setSpacing(2)
        ov.addWidget(self.heading(self.w("plan_object")))
        self.object_duplicate_button, self.object_delete_button = self.button_row(ov, (("plan_object_duplicate", self.duplicate_object), ("plan_object_delete", self.delete_object)))
        iv.addWidget(self.object_box)
        # the pane: the column, and under it the arrow that folds it away, at the bottom left as the navigation's (the engineer's request of 07.10.2026) -- the one every tab's left pane has since issue #10 (chrome.FoldablePane)
        self.left_pane = chrome.FoldablePane(inner, (self.t("pane_collapse"), self.t("pane_expand")))
        self.left_fold = self.left_pane.fold
        self.show_view_boxes()
        return self.left_pane

    def duplicate_object(self):
        """«Dupliquer» under «Objet sélectionné»: the canvas's copy of its selection, beside it (plan_canvas_edit.duplicate_offset)."""
        canvas = getattr(self, "canvas", None)
        if canvas is not None:
            canvas.duplicate_selection()
        self.update_object_buttons()

    def delete_object(self):
        """«Supprimer» under «Objet sélectionné»: the same action as the selection card's «Effacer» and the Delete key."""
        canvas = getattr(self, "canvas", None)
        if canvas is not None:
            canvas.delete_selection()
        self.update_object_buttons()

    def update_object_buttons(self):
        """The two buttons of «Objet sélectionné» open with something selected, closed with nothing."""
        canvas = getattr(self, "canvas", None)
        on = bool(canvas is not None and canvas.has_selection())
        for button in (getattr(self, "object_duplicate_button", None), getattr(self, "object_delete_button", None)):
            if button is not None:
                button.setEnabled(on)
                button.setToolTip("" if on else self.w("plan_object_none"))   # a disabled button says why (tests/test_window.py)

    @property
    def left_folded(self):
        """Whether the left pane is folded to its arrow (chrome.FoldablePane)."""
        pane = getattr(self, "left_pane", None)
        return bool(pane is not None and pane.folded)

    @property
    def left_sizes(self):
        """The splitter's sizes from before the left pane was folded."""
        pane = getattr(self, "left_pane", None)
        return pane.sizes if pane is not None else None

    def set_left_folded(self, folded):
        """The left pane folded to its arrow, or unfolded to the width it had (v0.117, UI-006; chrome.FoldablePane since issue #10)."""
        self.left_pane.set_folded(folded)

    def show_view_boxes(self):
        """The boxes of the left pane the view shows (VIEW_BOXES), the others hidden; in «Typst» the plans without the buttons that make and delete them, a plan being chosen there and not drawn."""
        shown = VIEW_BOXES.get(self.view, ())
        for name, box in self.left_boxes.items():
            box.setVisible(name in shown)
        for button in getattr(self, "plan_buttons", ()):
            button.setVisible(self.view != "typst")
        if hasattr(self, "object_box"):
            self.object_box.setVisible(self.view == "draw")   # an object is selected to be drawn: «Objet sélectionné» in «Dessin» alone
        self.update_object_buttons()

    def tool_button(self, text, tip=None, icon=None, checkable=True):
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tip or text)
        button.setCheckable(checkable)
        button.setAutoRaise(True)
        if icon is not None:
            button.setIcon(icon)
            button.setIconSize(QSize(26, 18))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        return button

    def doc_view_t(self, key, **values):
        """The document view's words, through WORDS: a subclass may say «Dans les plans de protection incendie» where the position plans say «Dans les plans»."""
        return self.w(key, **values)

    def build_center(self):
        """The centre: a stack of the plan's drawing with its tools, the document view, the export sheet's editor and the command builder's page (KINDS)."""
        self.center = CurrentStack()
        self.center.addWidget(self.build_drawing_center())
        self.doc_view = document_view.DocumentView(t=self.doc_view_t, lang=self.app.lang)
        self.doc_view.describe_error = self.document_error_text
        self.doc_view.pageToggled.connect(self.on_page_toggled)
        self.doc_view.rotateRequested.connect(self.on_rotate_requested)
        self.doc_view.cropDrawn.connect(self.on_doc_crop)
        self.doc_view.calibrated.connect(self.on_doc_calibrated)
        self.doc_view.planActivated.connect(self.open_plan)
        self.doc_view.pageSelected.connect(self.on_page_selected)
        self.doc_view.layersChanged.connect(self.on_layers_changed)
        self.doc_view.frameSelected.connect(self.on_frames_selected)
        self.doc_view.framesDeleteRequested.connect(self.on_frames_delete)
        self.doc_view.frameEdited.connect(self.on_doc_frame_edited)
        self.center.addWidget(self.doc_view)
        self.sheet_editor = sheet_editor.SheetEditor(self, lang=self.app.lang, ask=lambda question: self.ask_rewrite(question), kind=self.SHEET_KIND)
        self.center.addWidget(self.sheet_editor.canvas)
        self.builder = self.make_builder()
        # the plan of the command is the one chosen in the left pane's list, in the «Typst» view (v0.117): the builder's own choice of it is not shown (review A09)
        self.builder.options.plan.hide()
        self.builder.options.plan_label.hide()
        self.center.addWidget(self.builder.preview)
        self.bundle_pages = bundle_view.BundlePages(self.t)
        self.center.addWidget(self.bundle_pages)
        return self.center

    def build_properties(self):
        """The right pane: a stack of the plan's properties, the document's card, the export sheet's options and the command builder's (KINDS). The plan's come first, which is what a reader looking for the plan's column of cards finds first."""
        self.right = CurrentStack()
        self.right.addWidget(self.build_drawing_properties())
        self.superposition = plan_superposition.install(self)   # «Superposition»: another plan of the tab shown over this one, after «Taille des symboles» (v0.116)
        self.right.addWidget(self.build_document_properties())
        self.right.addWidget(self.holder(self.sheet_editor.options))
        self.right.addWidget(self.holder(self.builder.options))
        self.bundle_card = bundle_view.BundleCard(self.t)
        self.bundle_card.edited.connect(self.on_bundle_field)
        self.right.addWidget(self.holder(self.bundle_card))
        self.tasks = tasks.TaskRunner(self)
        return self.right

    @staticmethod
    def holder(widget):
        """`widget` in a page of its own: the right pane's pages each one level deep, so that the plan's column of cards is the one a search of the pane finds first."""
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(widget)
        return page

    def build_document_properties(self):
        """The document's own card (v0.114): its name, its file and its pages, its layers and the turning of the page last clicked."""
        outer = QWidget()
        ov = QVBoxLayout(outer)
        ov.setContentsMargins(6, 0, 0, 0)
        group = cards.card(self.w("plan_doc_group"))
        form = cards.form(group)
        self.doc_name_edit = QLineEdit()
        self.doc_name_edit.editingFinished.connect(lambda: self.rename_document())
        form.addRow(self.w("plan_doc_name"), self.doc_name_edit)
        self.doc_file_text = plain_label("", wrap=True)
        form.addRow(self.w("plan_doc_file"), self.doc_file_text)
        self.doc_pages_text = plain_label("")
        form.addRow(self.w("plan_doc_pages"), self.doc_pages_text)
        self.doc_layers_button = QPushButton(self.w("plan_doc_layers"))
        self.doc_layers_button.setCheckable(True)
        self.doc_layers_button.toggled.connect(self.doc_view.show_layers)
        self.doc_view.layers_button.toggled.connect(self.doc_layers_button.setChecked)
        row = QHBoxLayout()
        self.doc_rotate_left = QPushButton("⟲")
        self.doc_rotate_left.setToolTip(self.w("plan_doc_rotate_left"))
        self.doc_rotate_left.clicked.connect(lambda: self.rotate_selected_pages(-90))
        self.doc_rotate_right = QPushButton("⟳")
        self.doc_rotate_right.setToolTip(self.w("plan_doc_rotate_right"))
        self.doc_rotate_right.clicked.connect(lambda: self.rotate_selected_pages(90))
        for button in (self.doc_rotate_left, self.doc_rotate_right):
            button.setProperty("compact", True)
            row.addWidget(button)
        row.addWidget(self.doc_layers_button)
        row.addStretch(1)
        form.addRow("", row)
        ov.addWidget(group)
        self.doc_card = group
        self.doc_hint_note = self.note(self.w("plan_doc_hint"))
        ov.addWidget(self.doc_hint_note)
        # the plan of the frame chosen in the document view: its own «Plan» module, moved here while it is chosen and put back after (show_frame_module, v0.116)
        self.frame_box = QWidget()
        self.frame_layout = QVBoxLayout(self.frame_box)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_box.hide()
        ov.addWidget(self.frame_box)
        ov.addStretch(1)
        return outer

    def add_module(self, layout, card, when="plan"):
        """`card` added to the plan's column of cards `layout` and registered: shown while nothing is selected on the plan (`plan`), while something is (`selection`) or always (`always`) -- MODULE_WHEN. The cards stand in the order they are added; `insert_module` puts one after another. Returns the card."""
        assert when in MODULE_WHEN, when
        layout.addWidget(card)
        self.modules.append((card, when))
        self.properties_layout = layout
        return card

    def add_snap_module(self, layout):
        """«Magnétisme»: snapping to the axes and to the elements, on or off -- a plan module, shown while nothing is selected (the engineer, 07.10.2026: «pouvoir activer et désactiver le magnétisme dans le volet de droite lorsque rien n'est sélectionné»). Until v0.117 two buttons of the position plan's tool bar; the fire plan, whose canvas snaps the same way, gains them. The choice is the session's, never the plan's file."""
        group = cards.card(self.t("plan_group_snap"))
        box = QVBoxLayout(group)
        self.snap_axes = QCheckBox(self.t("plan_snap_axes"))
        self.snap_elements = QCheckBox(self.t("plan_snap_elements"))
        for check in (self.snap_axes, self.snap_elements):
            check.setChecked(True)
            check.toggled.connect(self.on_snap)
            box.addWidget(check)
        self.snap_group = self.add_module(layout, group)
        return group

    def on_snap(self, _checked=False):
        self.canvas.snap_axes = self.snap_axes.isChecked()
        self.canvas.snap_elements = self.snap_elements.isChecked()
        self.canvas._snap_index = None

    def insert_module(self, card, after, when="plan"):
        """`card` put in the plan's column right after the registered card `after` -- how a later module takes its place: «Superposition» after «Taille des symboles» (`insert_module(card, after=self.style_group)`). Shown by the selection as `add_module`'s are."""
        assert when in MODULE_WHEN, when
        layout = self.properties_layout
        layout.insertWidget(layout.indexOf(after) + 1, card)
        index = next((i + 1 for i, (c, _w) in enumerate(self.modules) if c is after), len(self.modules))
        self.modules.insert(index, (card, when))
        self.update_modules()
        return card

    def has_selection(self):
        """Whether something is selected on the plan open -- what turns the right pane from the plan's modules to the selection's. By default, the entry whose own sizes the panel shows (selected_entry)."""
        return self.selected_entry()[0] is not None

    def update_modules(self):
        """The plan's modules shown while nothing is selected, the selection's while something is, «Taille des symboles» always (the engineer: «lorsque l'on sélectionne un objet, toutes ces informations doivent disparaître … on gardera la taille des symboles et la taille propre»)."""
        selected = self.has_selection()
        for card, when in self.modules:
            card.setVisible(when == "always" or (when == "selection") == selected)

    def visible_modules(self):
        """The registered cards of the plan's page as they now stand, top to bottom, those shown -- what a test reads the pane by."""
        layout = self.properties_layout
        cards_in_order = sorted((layout.indexOf(card), card) for card, _when in self.modules)
        return [card for _index, card in cards_in_order if not card.isHidden()]

    def mark_tool(self, tool):
        """The tool bar's button of `tool` checked -- or none at all, for a tool that has no button there: the crop and the calibration, reached from the right pane since v0.116 («Dessiner le cadre», «Calibrer…»)."""
        button = self.tool_buttons.get(tool)
        if button is not None:
            if not button.isChecked():
                button.setChecked(True)
            return
        checked = self.tool_group.checkedButton()
        if checked is not None:
            self.tool_group.setExclusive(False)
            checked.setChecked(False)
            self.tool_group.setExclusive(True)

    def slider(self, minimum, maximum, slot):
        """A slider -- «a line with a point that moves on it» -- with its value beside it; one drag is one step of the undo history."""
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        value = QLabel("")
        value.setMinimumWidth(38)
        slider.valueChanged.connect(lambda v: value.setText(f"{v} %"))
        slider.valueChanged.connect(slot)
        slider.sliderPressed.connect(self.on_slider_pressed)
        slider.sliderReleased.connect(self.on_slider_released)
        row.addWidget(slider, 1)
        row.addWidget(value)
        box.slider = slider
        return box

    def show_kind(self, kind):
        """The centre and the right pane show `kind` (KINDS); the other lists of the left pane let their choice go."""
        if kind != "command" and self.view_kind == "command":
            self.builder.stop()
        if kind != "sheet" and self.view_kind == "sheet":
            self.sheet_editor.stop()
        if kind != "document":
            self.show_frame_module(None)
        self.view_kind = kind
        index = KINDS.index(kind)
        self.center.show_page(index)
        self.right.show_page(index)
        self.mark_left(kind)
        # the view is the kind's (VIEW_KIND): a kind reached from inside the tab -- a frame of a document opening its plan -- moves the top bar's switch with it
        view = KIND_VIEW[kind]
        if view != self.view:
            self.view = view
            self.show_view_boxes()
            changed = getattr(self.app, "view_changed", None)
            if changed is not None:
                changed(self)

    def mark_left(self, kind):
        self.filling = True
        try:
            for widget, own in ((self.doc_list, ("document",)), (self.sheet_list, ("sheet", "bundle"))):
                if kind not in own:
                    widget.blockSignals(True)
                    if isinstance(widget, QListWidget):
                        widget.setCurrentRow(-1)
                    else:       # the export sheets' tree
                        widget.setCurrentIndex(QModelIndex())
                    widget.clearSelection()
                    widget.blockSignals(False)
            if kind not in ("plan", "command"):   # the plans are the «Typst» view's list too
                self.list.blockSignals(True)
                self.list.setCurrentIndex(QModelIndex())
                self.list.clearSelection()
                self.list.blockSignals(False)
        finally:
            self.filling = False

    def leave_plan(self):
        """True where the engineer may leave the plan's view: nothing unsaved, or saved now (autosave)."""
        return self.view_kind != "plan" or self.confirm_leave()

    def on_doc_row(self, current, _previous):
        if current is None or self.filling:
            return
        docid = current.data(Qt.ItemDataRole.UserRole)
        if not self.leave_plan():
            self.mark_left("plan")
            return
        self.open_document(docid)

    def on_sheet_id(self, sid):
        """A sheet of the export list chosen: opened. A bundle (its folder) chosen: its pages and its fields (v0.117)."""
        if self.filling:
            return
        if not sid:
            item = self.sheet_list.currentItem()
            name = self.sheet_list.chosen_bundle()
            if item is not None and name and item.data(0, sheet_list.KIND_ROLE) == "folder":
                self.open_bundle(name)
            return
        if not self.leave_plan():
            self.mark_left("plan")
            return
        self.open_sheet(sid)

    def set_view(self, key, enter=True):
        """The view `key` of VIEW_KIND, chosen in the top bar's switch: its boxes on the left, and the centre and the right pane on what it last showed -- the document, the plan, the sheet. The window has saved the plan first (autosave.leave). With `enter` False -- the window being built (apply_views) -- it is a state: what it opens and compiles waits for the tab to be shown (review A10)."""
        if key not in VIEW_KIND:
            return
        if self.view == "import" and key != "import":
            self.finish_layer_export()   # a layer switched is exported before a view that reads the export (review A06)
        self.view = key
        self.show_view_boxes()
        if not enter:
            self.show_kind(VIEW_KIND[key])
            self.view_pending = True
            return
        self.view_pending = False
        self.enter_view()

    def enter_view(self):
        """The view shown opened: the document, the plan, the command or the sheet it last showed, or the first there is."""
        key = self.view
        if key == "import":
            docid = self.doc_id if self.doc_id and self.doc_row(self.doc_id) is not None else self.first_document()
            if docid:
                self.open_document(docid)
            else:
                self.show_kind("document")
        elif key == "typst":
            self.open_builder()
        elif key == "export":
            listed = sheets.list_sheets(project.current(), kind=self.SHEET_KIND)
            sid = self.sheet_id if self.sheet_id in listed else (listed[0] if listed else None)
            if sid:
                self.open_sheet(sid)
            else:
                self.show_kind("sheet")
        else:
            self.show_plan_view()

    def doc_row(self, docid):
        for row in range(self.doc_list.count()):
            if self.doc_list.item(row).data(Qt.ItemDataRole.UserRole) == docid:
                return row
        return None

    def first_document(self):
        return self.doc_list.item(0).data(Qt.ItemDataRole.UserRole) if self.doc_list.count() else None

    def showEvent(self, event):
        """The tab shown: a view set while it was hidden is opened now -- the builder compiled, the sheet compiled (review A10)."""
        super().showEvent(event)
        if self.view_pending:
            self.view_pending = False
            QTimer.singleShot(0, self, self.enter_view)   # once the window has painted: the builder or a sheet compiles behind it

    def show_plan_view(self):
        """Back to the plan open: its drawing in the middle, its properties on the right, its row chosen in the list."""
        self.show_kind("plan")
        self.list.blockSignals(True)
        self.list.select(self.current_id if self.current_id is not None else NEW_ROW)
        self.list.blockSignals(False)

    def on_shown(self):
        """The tab brought to the front: the documents and the sheets read again -- VS Code may have written a sheet --, and the plan open read again where its file changed while the tab was hidden and it holds nothing unsaved: the other tab of plans may have turned its page (plan_pages.rotate_page turns both kinds) or detached it."""
        self.reload_documents(select=self.doc_id if self.view_kind == "document" else None)
        self.reload_sheets(select=self.sheet_id if self.view_kind == "sheet" else None)
        if self.current_id is not None and not self.dirty and self.file_changed():
            self.reload_current()
        self.on_changed_quietly()

    def file_changed(self):
        """Whether the plan open's file holds something else than the plan shown -- written by the other tab of plans."""
        try:
            on_disk = json.loads((self.sources_dir() / f"{self.current_id}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        return isinstance(on_disk, dict) and self.complete_source(on_disk, self.current_id) != self.source

    def on_changed_quietly(self):
        loading, self.loading = self.loading, True
        try:
            self.on_changed()
        finally:
            self.loading = loading

    def hideEvent(self, event):
        """Another tab brought to the front: the plan open is saved (autosave). Not on a window minimised, which the system hides; and never with a question -- a tab switch cannot be cancelled, so a plan that cannot be saved keeps its dot."""
        if not event.spontaneous():
            self.autosave(ask=False)
            if self.view_kind == "sheet":
                self.sheet_editor.stop()
        super().hideEvent(event)
