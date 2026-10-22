"""The «Moments polaires» tab -- a polar moment of a group of fasteners, its form, its schema and its members -- with the helpers it reads, split out of calc/tools/woodcore_gui.py (issue #30), moved verbatim. woodcore_gui.py imports every name back, so woodcore_gui.PolarTab is still read where it always was.
"""

import source_editor  # Ctrl+S bound the one way (source_editor.save_shortcut)
import json
import sys
try:
    from PySide6.QtCore import QByteArray, QLibraryInfo, QLocale, QPoint, QProcess, QProcessEnvironment, QRectF, QRegularExpression, QSize, Qt, QTimer, QTranslator, QUrl, Signal
    from PySide6.QtGui import (
        QActionGroup, QColor, QDesktopServices, QFont, QGuiApplication, QIcon,
        QKeySequence, QPainter, QPixmap, QRegularExpressionValidator, QShortcut,
    )
    from PySide6.QtSvgWidgets import QSvgWidget
    from PySide6.QtWidgets import (
        QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout,
        QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
        QMenu, QMessageBox, QPlainTextEdit, QPushButton, QRadioButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QTableWidget,
        QTableWidgetItem, QTabWidget, QToolButton, QVBoxLayout, QWidget,
    )
except ImportError as exc:
    if __name__ == "__main__" and sys.platform == "win32":
        # Started from Woodcore.bat there is no console to print this to, so it gets a window of its own -- Windows' own, Qt being what is missing.
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, f"PySide6 est introuvable · PySide6 fehlt · PySide6 is missing\n\n{sys.executable}\n{exc}\n\npython -m pip install PySide6", "Woodcore", 0x10)
    raise
from woodcore_gui_words import STRINGS, _check_strings  # split out of this module (issue #30): every name it had is still importable from it
import project  # noqa: E402  -- where the program is, and where the project it works on is
import build_reference as ref
import grouped_list  # the left pane of every editor tab: folders, drag and drop, Ctrl/Shift (grouped_list.py)
import source_archive  # «Supprimer» archives rather than deletes (source_archive.py)
import views  # the views of a tab and the switch in the top bar that chooses one (views.py, v0.117)
import autosave  # saving without a question when a tab, a view, a document or the window is left (autosave.py, v0.117)
import notifications  # noqa: E402  -- every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # noqa: E402  -- the red octagon and the orange triangle at the top right, and their panel (v0.117)
import display_view  # the «Affichage» view a tab shows its commands in (display_view.py, v0.117)
import richtext  # symbols as mathematics, Typst calls coloured, «Copié ✓» (richtext.py, v0.92)
import cards  # forms in cards, after the website (cards.py, v0.93)
import theme  # the website's look: one palette, one style sheet, light or dark (theme.py, v0.90)
import engine  # noqa: E402
import validation  # noqa: E402
from domains import connection, connection_svg  # noqa: E402
from domains import links  # noqa: E402  -- a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
import linkable_spin  # noqa: E402  -- the button beside it
from domains import connector as connector_model  # noqa: E402  -- the one reader of the exported positions (known_positions)
from domains import schema as schema_model  # noqa: E402  -- a connection is drawn on one


# Every path of the project -- the export (data/), the connections' and the schemas' sources, the workbooks, the report and its PDF -- is the current project's, asked of project.current() when it is needed and never fixed at import (v0.81, docs/architecture/layout.md §11). What the PDF is compiled from and written to is the project's `report` and `pdf`, the two paths woodcore-cli names for the same reason (section 12): every build route must name the one deliverable.
# How many members may meet at the node -- the connection module's own bounds, named here so the member boxes can be built against them.
MIN_MEMBERS, MAX_MEMBERS = connection.MIN_MEMBERS, connection.MAX_MEMBERS


# Decimals a value is shown with -- the report's own default `number-digits` (docs/typst/report-engine.md §4), so the window reads like the PDF.
DIGITS = 3


def fmt_value(value, digits=DIGITS):
    """As lib/calc-engine.typ's fmt-decimals: at most `digits` decimals, trailing zeros dropped (`1.7291232 -> 1.729`, `0.8 -> 0.8`, `438 -> 438`); a text value passes through unchanged."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    text = f"{value:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def list_connections(folder=None):
    """[(id, label, folder), ...] of every saved connection, in file-name order, `folder` its own `group` (v0.75). A file that cannot be read is still listed, under its file name, so it can be opened and repaired or deleted."""
    listed = []
    for path in connection.source_paths(folder or project.current().connections_dir):
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
            label = source.get("label", "")
        except (OSError, ValueError, AttributeError):
            source, label = {}, "⚠"
        listed.append((path.stem, label if isinstance(label, str) else "", grouped_list.group_of(source)))
    return listed


def next_free_name(base, taken):
    """`base` where no calculation's id is already made from it, else `base 2`, `base 3`, ... -- case ignored, as the file system ignores it. A suggestion, which the engineer is free to change (v0.76, where a variant was suggested until then)."""
    taken = {t.lower() for t in taken}
    base = base.strip() or "A01"
    name, n = base, 1
    while connection.id_from_name(name).lower() in taken:
        n += 1
        name = f"{base} {n}"
    return name


def clean_number(value):
    """A number as it is saved: an integer where it is one (70, not 70.0), otherwise rounded to what a form can mean."""
    value = round(float(value), 6)
    return int(value) if value.is_integer() else value


def members_from_schema(schema_id, schemas):
    """The members of a new calculation drawn on `schema_id`: one per linear element of that schema, up to six, in the order the schema draws them. None where the schema is not one of `schemas`, which leaves default_source to put down two empty members.

    ⚠️ This replaces members_from_elements, which read each of the connector's positions and PARSED its
    dimension text into a b and an h. Nothing parses a dimension any more (docs/domain/positions.md §7): the piece
    is the schema's element, drawn at the width the engineer gave it, and the position comes with it.
    """
    detail = (schemas or {}).get(schema_id)
    if detail is None:
        return None
    elements = [e for e in detail.get("elements", []) if e.get("kind") == "linear"]
    members = [{"name": "", "element": e["id"]} for e in elements[:connection.MAX_MEMBERS]]
    while len(members) < connection.MIN_MEMBERS:
        members.append({"name": "", "element": ""})
    return members


def default_source(cid, members=None, schema=""):
    """A new calculation, named after its id: connection.new_source, with the members given (members_from_schema) where there are some; N along x and V along z; no fastener ticked yet. It cites the default design aid, with no clause."""
    source = connection.new_source(cid, schema)
    if members:
        source["members"] = members
    return source


def plain_label(text, wrap=False):
    """A label showing `text` exactly as it is -- given a text that looks like HTML, QLabel would render it as HTML."""
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


def length_box(maximum=100_000.0, minimum=-100_000.0, suffix=" mm", decimals=1, step=10.0):
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSuffix(suffix)
    box.setSingleStep(step)
    box.setKeyboardTracking(True)
    box.setMinimumWidth(70)  # left to itself, a spin box is as wide as its largest value, and two of them overflow the form
    return box


def form_layout(parent):
    """A form whose labels go above their fields when its column is too narrow for both side by side."""
    form = QFormLayout(parent)
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
    return form


def narrow_combo():
    """A combo box that does not insist on the width of its longest entry."""
    combo = QComboBox()
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(10)
    return combo


def angle_box():
    return length_box(360.0, -360.0, " °", 1, 15.0)


# The row that stands for the calculation nobody has saved yet -- the other editor tabs' own sentinel: ID_PATTERN allows no angle bracket, so it can collide with no id.
from source_editor import NEW_ROW as POLAR_NEW_ROW, SourceEditorTab  # the base of every editor tab of sources, and its draft's row (spec 2026-10-19-base-saine-nettoyage, ARCH-001)


class PolarTab(SourceEditorTab, display_view.DisplayTab, QWidget):
    KEY = "tab_polar"
    GRAPH_KIND = "connection"   # issue #71
    WORDS = "polar"
    UNSAVED_WORDS = ("polar_unsaved_title", "polar_unsaved")   # the question before the draft is left (SourceEditorTab.confirm_leave)
    DISCARD_OPENS_FIRST = True

    def current_label(self):
        """The draft named by its id as it will be saved -- typed, or made from its name (`draft_id`)."""
        return self.draft_id() or "?"

    SYNC_DOMAIN = True   # its sources are domains with a file of their own: every writer is followed by domain_file.sync (tab_guard.py, spec 2026-10-19-base-saine-nettoyage)
    VIEWS = views.CALC_VIEWS   # «Calcul» and «Affichage» (views.py, v0.117)

    """The polar moments of inertia of fastener groups (docs/domain/connections.md §3.3quinquies, docs/ui/window.md §10quater): on the left the calculations saved, in their folders, the form a calculation is defined in, and beside it the connection drawn as it is entered, its polar moment, a preview of the forces for trial values of N, V and M, and the Typst calls that print it.

    A calculation names a detail schema and nothing else to draw it with -- no connector since v0.76, a polar moment having no use for what fastens its points. Its identity is Schéma · Nom · Description · ID, the id made from the name unless written over; its folder (`group`) is set by a drop in the list, and its reference by the file, neither shown in the form. Everything calculated or drawn here is calc/domains/connection.py's -- the module export_all.py builds data/connections.json with -- so what this tab shows is what the report will. Saving writes the source, connections/<id>.json, and exports the connections at once. The draft being edited survives a language switch or a reload (it travels in view_state()); leaving it for another calculation, or closing the window, asks first.
    """

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False  # set while the form is being filled, so filling it is not taken for an edit
        self.dirty = False
        self.current_id = None  # the saved calculation the form holds; None for one not saved yet
        # Kept in the source and not shown (v0.76): the folder a drop files the calculation in, and the reference it cites.
        self.form_group = ""
        self.form_norm = connection.DEFAULT_NORM
        self.form_norm_ref = ""
        self.id_overridden = False  # the id written over rather than made from the name (v0.75 rule, v0.76 name)
        self.ids = []
        self.empty_folders = list(app.folder_settings("tab_polar"))  # folders holding nothing, kept by the window
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(120)  # one redraw per pause in the typing, not one per keystroke
        self.refresh_timer.timeout.connect(self.refresh)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_form())
        self.splitter.addWidget(self.build_preview())
        self.install_display("tab_polar")   # «Affichage»: show-polar-moment's options -- the trial forces of «Calcul» to start from --, the call and the page (v0.117)
        for index, stretch in enumerate((1, 3, 4)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)
        source_editor.save_shortcut(self)   # Ctrl+S

        self.restore(app.views.get("tab_polar"))

    # -- building --

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def note(self, text):
        """A card's explanation, muted and wrapping -- in its title it would set the form's minimum width (cards.note, v0.93)."""
        return cards.note(text)

    def build_list(self):
        """The calculations, in folders of their own `group` -- a drop files them, as in every other editor tab (v0.75, grouped_list.py).

        ⚠️ Until v0.75 this was a tree of the connectors with their calculations beneath, the folders read off the connectors' own and taking no drop. The engineer asked for the drop; a calculation's own `group` is what makes one possible without a drop in this tab moving a connector filed in another.
        """
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 6, 0)
        self.list = grouped_list.GroupedList(STRINGS.get(self.app.lang, STRINGS["fr"]), lang=self.app.lang)
        self.archive = source_archive.Actions(self, self.sources_dir, self.export_listed, lambda select: self.reload_list(select), self.load_first)
        self.archive.connect()
        v.addWidget(grouped_list.title_row(self.heading(self.t("polar_list")), self.list))
        self.list.setIconSize(self.app.mark_size)
        self.list.currentIdChanged.connect(self.on_list_change)
        self.list.moved.connect(self.on_moved)
        self.list.foldersChanged.connect(self.on_folders_changed)
        self.list.attach_order(self.KEY, self.app.list_store)   # the order the engineer gives the list by drag and drop, kept in Woodcore-Datei/lists.json (calc/list_order.py, issue #15)
        self.list.reordered.connect(lambda: self.reload_list(select=self.current_id))
        v.addWidget(self.list, 1)
        self.empty_hint = plain_label("", wrap=True)
        self.empty_hint.setStyleSheet(f"color: {self.app.muted};")
        v.addWidget(self.empty_hint)
        for suffix, slot in (("new", self.new), ("duplicate", self.duplicate), ("delete", self.delete)):
            button = QPushButton(self.word(suffix))
            button.clicked.connect(slot)
            v.addWidget(button)    # one under the other: the polar moments' pane is narrow
        return box

    def build_form(self):
        """The calculation's form, in cards after the website (v0.93, cards.py): Identité · Éléments · Moyens d'assemblage · Centre de rotation · Directions des efforts, on the soft ground of a column that scrolls up and down and never sideways -- where the form was wider than its pane until then, a horizontal scroll bar under it and its buttons cut at its right edge."""
        scroll, v = cards.column()

        # --- Identité, and nothing but these four rows (v0.76): Schéma · Nom · Description · ID.
        # ⚠️ The schema is the drawing, named and not drawn: it replaces the member form of v0.31 to v0.73, a
        # polar moment having no business holding a second drawing of a joint the schema already draws
        # (docs/architecture/principles.md §2 rule 1, section 3.3decies). It had a box of its own until v0.75. Gone from the
        # form with v0.76: the connector and the variant (no longer in the source at all), the folder (set by a
        # drop in the list, and kept) and the reference with its clause (kept in the source as the file has them).
        general = cards.card(self.t("polar_identity"))
        form = form_layout(general)
        self.schema_combo = narrow_combo()
        self.schema_info = self.note("")
        self.name_edit = QLineEdit()  # free text: the id is what must be safe, and it is made from this
        self.label_edit = QLineEdit()
        self.id_edit = QLineEdit()
        self.id_edit.setFont(self.app.mono_font)
        self.id_edit.setToolTip(self.t("polar_id_auto"))
        self.id_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[A-Za-z0-9][A-Za-z0-9_.+\-]*")))
        form.addRow(self.t("polar_schema"), self.schema_combo)
        form.addRow("", self.schema_info)
        form.addRow(self.t("polar_name"), self.name_edit)
        form.addRow(self.t("polar_label"), self.label_edit)
        form.addRow(self.t("polar_id"), self.id_edit)
        self.schema_combo.currentIndexChanged.connect(self.on_schema_change)
        for edit in (self.name_edit, self.label_edit):
            edit.textChanged.connect(self.changed)
        self.name_edit.textChanged.connect(self.compose_id)
        self.id_edit.textEdited.connect(self.on_id_edited)
        v.addWidget(general)

        # --- The members, 2 to 6, one row each in one card (v0.93): their number, what the report calls them, the
        # element of the schema each one is, and a ✕ -- where each had a box of its own and the reference a
        # «Géométrie» box holding nothing else. Rows rebuilt when their number changes (set_member_count).
        # ⚠️ The reference no longer fixes the frame (v0.74): x and z are the schema's, so a detail drawn at an
        # angle is calculated in the schema's own axes, and the reference only decides which member theta_(r,j)
        # is counted from -- which its label says since v0.93, where it said «axes x, z».
        members = cards.card(self.t("polar_members"))
        mv = QVBoxLayout(members)
        self.members, self.member_groups = [], []
        self.members_grid = QGridLayout()
        self.members_grid.setHorizontalSpacing(6)
        self.members_grid.setVerticalSpacing(4)
        self.members_grid.setColumnStretch(1, 2)
        self.members_grid.setColumnStretch(2, 3)
        for column, key in ((1, "polar_member_name"), (2, "polar_element")):
            header = self.note(self.t(key))
            header.setWordWrap(False)
            self.members_grid.addWidget(header, 0, column)
        mv.addLayout(self.members_grid)
        self.add_member_button = QPushButton("+ " + self.t("polar_add_member"))
        self.add_member_button.clicked.connect(self.add_member)
        add_row = QHBoxLayout()
        add_row.addWidget(self.add_member_button)
        add_row.addStretch(1)
        mv.addLayout(add_row)
        form = form_layout(None)
        self.reference_combo = narrow_combo()
        self.reference_combo.setToolTip(self.t("polar_reference_tip"))
        form.addRow(self.t("polar_reference"), self.reference_combo)
        self.reference_combo.currentIndexChanged.connect(self.changed)
        mv.addLayout(form)
        v.addWidget(members)

        # --- The fasteners: the schema's connector markers, with a tick against the ones this calculation
        # carries. ⚠️ It does not say what KIND of fastener they are -- a polar moment turns points about a
        # centre, and a dowel and a screw are the same point to it (the engineer's own words).
        fasteners = cards.card(self.t("polar_fasteners"))
        fv = QVBoxLayout(fasteners)
        fv.addWidget(self.note(self.t("polar_markers_note")))
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", self.t("polar_marker"), "x [mm]", "z [mm]"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 28)
        self.table.verticalHeader().setVisible(False)  # the row's number is the marker's own id beside it
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(180)
        self.table.setMinimumWidth(160)   # its columns stretch: left to itself it asks for every header's full width
        self.table.itemChanged.connect(self.on_marker_toggled)
        self.table.itemSelectionChanged.connect(lambda: self.refresh_timer.start())
        fv.addWidget(self.table)
        buttons = QHBoxLayout()
        for key, slot in (("polar_tick_all", self.tick_all), ("polar_tick_none", self.tick_none)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            buttons.addWidget(button)
        buttons.addStretch(1)
        fv.addLayout(buttons)
        v.addWidget(fasteners)

        # --- The rotation centre: the centroid, a point fixed here, or a centre DRAWN IN THE SCHEMA (v0.74),
        # which is what the schema's own «Centre» tool is for.
        center = cards.card(self.t("polar_center"))
        grid = QGridLayout(center)
        self.centroid_radio = QRadioButton(self.t("polar_centroid"))
        self.manual_radio = QRadioButton(self.t("polar_manual"))
        self.aid_radio = QRadioButton(self.t("polar_aid"))
        self.centroid_value = self.note("")
        self.center_x = length_box()
        self.center_z = length_box()
        self.center_aid = narrow_combo()
        # each choice on its own line and what it takes under it, indented: side by side they set the column's minimum width past its pane (v0.93)
        grid.setColumnMinimumWidth(0, 18)
        grid.addWidget(self.centroid_radio, 0, 0, 1, 5)
        grid.addWidget(self.centroid_value, 1, 1, 1, 4)
        grid.addWidget(self.manual_radio, 2, 0, 1, 5)
        grid.addWidget(QLabel("x"), 3, 1)
        grid.addWidget(self.linked(self.center_x, "center.x", "mm", "x"), 3, 2)
        grid.addWidget(QLabel("z"), 3, 3)
        grid.addWidget(self.linked(self.center_z, "center.z", "mm", "z"), 3, 4)
        grid.addWidget(self.aid_radio, 4, 0, 1, 5)
        grid.addWidget(self.center_aid, 5, 1, 1, 4)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(4, 1)
        for radio in (self.centroid_radio, self.manual_radio, self.aid_radio):
            radio.toggled.connect(self.on_center_mode)
        self.center_x.valueChanged.connect(self.changed)
        self.center_z.valueChanged.connect(self.changed)
        self.center_aid.currentIndexChanged.connect(self.changed)
        v.addWidget(center)

        directions = cards.card(self.t("polar_directions"))
        form = form_layout(directions)
        form.addRow(self.note(self.t("polar_directions_note")))
        self.direction_n = angle_box()
        self.direction_v = angle_box()
        form.addRow(self.t("polar_dir_N"), self.linked(self.direction_n, "directions.N", "°", "N"))
        form.addRow(self.t("polar_dir_V"), self.linked(self.direction_v, "directions.V", "°", "V"))
        self.direction_n.valueChanged.connect(self.changed)
        self.direction_v.valueChanged.connect(self.changed)
        v.addWidget(directions)
        v.addStretch(1)
        return scroll   # its minimum width is its cards' (cards.Column): no fixed 320 px, which would win over it

    # -- the schema this calculation is drawn on --------------------------------------

    def schemas(self):
        """{id: source} of every detail schema, read afresh off details/ -- so one saved in the «Schémas» tab is offered here the moment this tab is looked at again. One that does not check is left out and said in a warning notice naming the file and why (issue #28): this tab must stay usable while another is being edited."""
        out, problems = schema_model.readable_sources(project.current().details_dir)
        notices_ui.tell_unreadable_schemas(problems)   # one that does not read is left out and said, never skipped without a word (issue #28)
        return out

    def detail(self):
        """The schema in force, or None."""
        return self.schemas().get(self.schema_combo.currentData() or "")

    def set_schema_items(self, sid):
        """The schema combo, with -- selected -- the one a calculation names even where the folder no longer holds it, so the form shows what the file says until another is chosen. The plan tab's «T009 (?)» rule."""
        was_loading, self.loading = self.loading, True
        try:
            self.schema_combo.clear()
            self.schema_combo.addItem(self.t("polar_no_schema"), "")
            for key, detail in sorted(self.schemas().items()):
                label = detail.get("label", "")
                self.schema_combo.addItem(f"{key} — {label}" if label else key, key)
            found = self.schema_combo.findData(sid)
            if found < 0 and sid:
                self.schema_combo.addItem(f"{sid} (?)", sid)
                found = self.schema_combo.count() - 1
            self.schema_combo.setCurrentIndex(max(0, found))
        finally:
            self.loading = was_loading
        self.update_schema_info()

    def update_schema_info(self):
        sid = self.schema_combo.currentData() or ""
        detail = self.schemas().get(sid)
        if not sid:
            self.schema_info.setText(self.t("polar_schema_none_notice"))
        elif detail is None:
            self.schema_info.setText(self.t("polar_schema_gone", sid=sid))
        else:
            self.schema_info.setText(self.t("polar_schema_holds",
                                            n=len(detail.get("elements", [])),
                                            m=len(detail.get("connectors", [])),
                                            p=len([a for a in detail.get("aids", []) if a.get("kind") == "point" and a.get("connector")])))

    def on_schema_change(self, _index=0):
        """A schema chosen: the elements, the markers and the centres are all its, so the three lists are rebuilt."""
        if self.loading:
            return
        self.update_schema_info()
        self.fill_elements()
        self.fill_markers([])
        self.fill_centres()
        self.changed()

    def fill_elements(self):
        """Each member's element combo, from the schema in force."""
        detail = self.detail()
        for w in self.members:
            box = w["element"]
            was = box.currentData()
            box.blockSignals(True)
            box.clear()
            box.addItem("—", "")
            for element in (detail or {}).get("elements", []):
                pid = element.get("position", "")
                label = element.get("label", "")
                text = " — ".join(p for p in (element["id"], pid or label) if p)
                box.addItem(text, element["id"])
            found = box.findData(was)
            if found < 0 and was:
                box.addItem(f"{was} (?)", was)
                found = box.count() - 1
            box.setCurrentIndex(max(0, found))
            box.blockSignals(False)

    def fill_centres(self):
        """The combo of the schema's point-shaped aids -- a `centre` or a `point` -- which the connection may turn about."""
        detail = self.detail()
        was = self.center_aid.currentData()
        self.center_aid.blockSignals(True)
        self.center_aid.clear()
        for aid in (detail or {}).get("aids", []):
            if aid.get("kind") in schema_model.AID_POINT_KINDS:
                self.center_aid.addItem(f"{aid['id']} ({aid['x']:g} / {aid['z']:g})", aid["id"])
        found = self.center_aid.findData(was)
        if found < 0 and was:
            self.center_aid.addItem(f"{was} (?)", was)
            found = self.center_aid.count() - 1
        self.center_aid.setCurrentIndex(max(0, found))
        self.center_aid.blockSignals(False)
        self.aid_radio.setEnabled(self.center_aid.count() > 0 or bool(was))

    def fill_markers(self, ticked):
        """The fastener list: every connector marker **and every point ticked «connecteur»** in the schema (connection.fastener_places, v0.77), with a tick against the ones this calculation carries, and its place beside it, read only -- a point says what it is in its tooltip. One the schema has lost is still listed, ticked and marked, so that it can be seen and untangled rather than vanishing with the number it carried."""
        was_loading, self.loading = self.loading, True
        try:
            detail = self.detail()
            places = connection.fastener_places(detail)
            markers = {m.get("id") for m in (detail or {}).get("connectors", [])}
            rows = [(fid, x, z, True) for fid, (x, z) in places.items()]
            rows += [(mid, None, None, False) for mid in ticked if mid not in places]
            self.table.setRowCount(0)
            for mid, x, z, present in rows:
                r = self.table.rowCount()
                self.table.insertRow(r)
                tick = QTableWidgetItem("")
                tick.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                              | Qt.ItemFlag.ItemIsSelectable)
                tick.setCheckState(Qt.CheckState.Checked if mid in ticked else Qt.CheckState.Unchecked)
                tick.setData(Qt.ItemDataRole.UserRole, mid)
                self.table.setItem(r, 0, tick)
                for c, text in ((1, mid if present else f"{mid} (?)"),
                                (2, "" if x is None else fmt_value(x)),
                                (3, "" if z is None else fmt_value(z))):
                    item = QTableWidgetItem(str(text))
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    if present:
                        item.setToolTip(self.t("polar_kind_marker" if mid in markers else "polar_kind_point"))
                    self.table.setItem(r, c, item)
        finally:
            self.loading = was_loading

    def ticked_markers(self):
        """The marker ids ticked, in the table's own order -- which is the schema's, and so the order the report numbers them in."""
        out = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                out.append(item.data(Qt.ItemDataRole.UserRole))
        return out

    def on_marker_toggled(self, item):
        if self.loading or item.column() != 0:
            return
        self.changed()

    def tick_all(self):
        self._tick_every(True)

    def tick_none(self):
        self._tick_every(False)

    def _tick_every(self, on):
        was_loading, self.loading = self.loading, True
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item is not None:
                item.setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)
        self.loading = was_loading
        self.changed()

    def selected_marker_index(self):
        """Which fastener the figure rings: the position, among the ticked ones, of the row selected."""
        ticked = self.ticked_markers()
        for r in sorted({i.row() for i in self.table.selectedIndexes()}):
            item = self.table.item(r, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) in ticked:
                return ticked.index(item.data(Qt.ItemDataRole.UserRole))
        return None

    def build_member(self, index, count):
        """One member, one row of the Éléments card (v0.93): its number, what the report calls it, which element of the schema it is, and a ✕ to take it out where more than the fewest remain.

        ⚠️ Everything else this box held until v0.73 -- the section taken from a position, b, h, which of
        the two is the band drawn, the angle from member 1, whether it runs through and what it stops
        against -- is the schema's now (docs/domain/detail-schemas.md §3.3decies). The member names an element and
        reaches its position through it; there is nothing about the drawing left to type here.
        """
        badge = QLabel(str(index + 1))
        badge.setObjectName("cardBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(22, 22)
        badge.setToolTip(self.t("polar_member", n=index + 1))
        name = QLineEdit()
        name.setPlaceholderText(self.t("polar_member", n=index + 1))
        element = narrow_combo()
        remove = None
        if count > MIN_MEMBERS:
            remove = QToolButton()
            remove.setText("✕")
            remove.setToolTip(self.t("polar_remove_member"))
            remove.setAutoRaise(True)
            remove.clicked.connect(lambda _c=False, i=index: self.remove_member(i))
        name.textChanged.connect(self.changed)
        element.currentIndexChanged.connect(self.changed)
        return {"badge": badge, "name": name, "element": element, "remove": remove}

    def set_member_count(self, count):
        """Rebuilds the member rows so that there are `count` of them, keeping what the ones that survive hold."""
        count = max(MIN_MEMBERS, min(MAX_MEMBERS, int(count)))
        was_loading, self.loading = self.loading, True
        try:
            kept = [{"name": w["name"].text(), "element": w["element"].currentData()} for w in self.members]
            while self.member_groups:
                for widget in self.member_groups.pop():
                    self.members_grid.removeWidget(widget)
                    # hidden before it is detached: a shown widget with no parent is a top-level window, and Qt shows it as one (v0.77, connectors_tab._clear)
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()
            self.members = []
            for i in range(count):
                widgets = self.build_member(i, count)
                row = i + 1   # row 0 holds the headers
                self.members_grid.addWidget(widgets["badge"], row, 0)
                self.members_grid.addWidget(widgets["name"], row, 1)
                self.members_grid.addWidget(widgets["element"], row, 2)
                if widgets["remove"] is not None:
                    self.members_grid.addWidget(widgets["remove"], row, 3)
                self.member_groups.append([w for w in (widgets["badge"], widgets["name"], widgets["element"], widgets["remove"]) if w is not None])
                self.members.append(widgets)
            self.fill_elements()
            for i, widgets in enumerate(self.members):
                if i < len(kept):
                    widgets["name"].setText(kept[i]["name"])
                    found = widgets["element"].findData(kept[i]["element"])
                    widgets["element"].setCurrentIndex(max(0, found))
            self.reference_combo.clear()
            for i in range(count):
                self.reference_combo.addItem(self.t("polar_member", n=i + 1), i + 1)
            self.add_member_button.setEnabled(count < MAX_MEMBERS)
        finally:
            self.loading = was_loading

    def add_member(self):
        self.set_member_count(len(self.members) + 1)
        self.changed()

    def remove_member(self, index):
        """Takes one member out, keeping what the others hold."""
        if len(self.members) <= MIN_MEMBERS:
            return
        kept = [{"name": w["name"].text(), "element": w["element"].currentData()}
                for i, w in enumerate(self.members) if i != index]
        reference = self.reference_combo.currentData() or 1
        self.set_member_count(len(kept))
        was_loading, self.loading = self.loading, True
        try:
            for i, widgets in enumerate(self.members):
                widgets["name"].setText(kept[i]["name"])
                found = widgets["element"].findData(kept[i]["element"])
                widgets["element"].setCurrentIndex(max(0, found))
            # the reference follows the member it named, and falls back to the first where that was the one removed
            new_reference = reference - 1 if reference - 1 > index else reference
            if reference - 1 == index:
                new_reference = 1
            self.reference_combo.setCurrentIndex(max(0, self.reference_combo.findData(min(new_reference, len(kept)))))
        finally:
            self.loading = was_loading
        self.changed()

    def build_preview(self):
        """The figure above, everything read off it below in a pane of its own that scrolls -- so the calls keep their height however small the window -- and the save buttons under both, always in reach."""
        box = QWidget()
        outer = QVBoxLayout(box)
        outer.setContentsMargins(6, 0, 0, 0)
        self.preview_splitter = QSplitter(Qt.Orientation.Vertical)
        self.preview_splitter.setChildrenCollapsible(False)
        figure = cards.card(self.t("polar_figure"))   # the drawing on its paper, in a card like the rest (v0.93)
        fv = QVBoxLayout(figure)
        self.svg = QSvgWidget()
        self.svg.setMinimumSize(240, 200)
        self.svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        fv.addWidget(self.svg, 1)
        self.preview_splitter.addWidget(figure)

        scroll, v = cards.column(margins=(0, 10, 4, 0), hold=False)   # what is read off the figure, in cards on the soft ground (v0.93); read, not typed, so the pane may be narrower than it
        self.preview_splitter.addWidget(scroll)
        self.preview_splitter.setStretchFactor(0, 5)
        self.preview_splitter.setStretchFactor(1, 4)
        outer.addWidget(self.preview_splitter, 1)

        results = cards.card(self.t("polar_results"))
        rv = QVBoxLayout(results)
        self.results = plain_label("")
        self.results.setTextFormat(Qt.TextFormat.RichText)   # the symbols with their subscripts (richtext.results_html, v0.92)
        self.results.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        rv.addWidget(self.results)
        v.addWidget(results)

        trial = cards.card(self.t("polar_trial"))
        tv = QVBoxLayout(trial)
        inputs = QHBoxLayout()
        self.trial = {}
        for key, unit in (("N", " kN"), ("V", " kN"), ("M", " kNm")):
            box_ = length_box(100_000.0, -100_000.0, unit, 3, 1.0)
            # data of the calculation since issue #42 (D-12): an edit is one, and the preview follows it (`changed`)
            box_.valueChanged.connect(self.changed)
            inputs.addWidget(QLabel(key))
            inputs.addWidget(self.linked(box_, "trial." + key, unit.strip(), key), 1)
            self.trial[key] = box_
        tv.addLayout(inputs)
        self.trial_result = plain_label("", wrap=True)
        self.trial_result.setTextFormat(Qt.TextFormat.RichText)   # F_max with its subscript (richtext.subscripts, v0.92)
        self.trial_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        tv.addWidget(self.trial_result)
        v.addWidget(trial)

        v.addStretch(1)
        self.preview_layout = v

        self.message = plain_label("", wrap=True)
        self.message.setStyleSheet(f"color: {theme.colour('warning')};")
        outer.addWidget(self.message)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.revert_button = QPushButton(self.t("polar_revert"))
        self.revert_button.setToolTip(self.t("polar_revert_tip"))
        self.revert_button.clicked.connect(self.revert)
        self.save_button = QPushButton(self.t("polar_save"))
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save)
        actions.addWidget(self.revert_button)
        actions.addWidget(self.save_button)
        outer.addLayout(actions)
        return box

    def code_field(self, text):
        return richtext.CodeField(text, self.app.mono_font)   # the call as the site sets a code block, coloured (v0.92)

    def copy_button(self, text):
        return richtext.copy_button(self.t("copy"), self.t("copied_short"), lambda: self.app.copy(text))

    # -- the form and the source it stands for --

    def changed(self, *_args):
        """Any edit: the draft now differs from what is saved, and the preview is redrawn once the typing pauses."""
        if self.loading:
            return
        self.dirty = True
        self.refresh_timer.start()

    def composed_id(self):
        """The id the name makes (connection.id_from_name)."""
        return connection.id_from_name(self.name_edit.text())

    def draft_id(self):
        """The calculation's id: the ID field, which is made from the name unless it has been written over."""
        return self.id_edit.text().strip() or self.composed_id()

    def compose_id(self, *_args):
        """The name typed: the id follows it, unless it has been written over -- the connectors' own rule."""
        if self.loading or self.id_overridden:
            return
        was_loading, self.loading = self.loading, True
        self.id_edit.setText(self.composed_id())
        self.loading = was_loading

    def on_id_edited(self, text):
        """The id typed into: written over while it differs from what the name makes, and made from the name again the moment it agrees."""
        self.id_overridden = bool(text.strip()) and text.strip() != self.composed_id()
        self.changed()

    def draft(self):
        """The form as a connection source, schema 4.0 -- what Enregistrer would save. The folder and the reference are not in the form and travel as the file had them."""
        members = [{"name": w["name"].text().strip(), "element": w["element"].currentData() or ""}
                   for w in self.members]
        if self.manual_radio.isChecked():
            center = {"mode": "manual", "x": clean_number(self.center_x.value()), "z": clean_number(self.center_z.value())}
        elif self.aid_radio.isChecked() and (self.center_aid.currentData() or ""):
            center = {"mode": "aid", "aid": self.center_aid.currentData()}
        else:
            center = {"mode": "centroid"}
        return {
            "schema_version": connection.SOURCE_SCHEMA_VERSION,
            "id": self.draft_id(),
            "group": self.form_group,
            "name": self.name_edit.text().strip(),
            "label": self.label_edit.text().strip(),
            "norm": self.form_norm,
            "norm_ref": self.form_norm_ref,
            "schema": self.schema_combo.currentData() or "",
            "reference": self.reference_combo.currentData() or 1,
            "members": members,
            "fasteners": self.ticked_markers(),
            "center": center,
            "directions": {"N": clean_number(self.direction_n.value()), "V": clean_number(self.direction_v.value())},
            # the trial forces the «Calcul» view starts from, data of the calculation since issue #42 (D-12)
            "trial": {key: clean_number(box_.value()) for key, box_ in self.trial.items()},
        } | self.draft_links()

    def linked(self, spin, key, unit, label):
        """`spin` with the button that links it to a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes, UI-001): the widget the form holds in its place. `key` is the field's in the source (connection.LINKABLE)."""
        wrapper = linkable_spin.LinkableSpin(spin, unit, label, lambda: self.app, self.app.lang, links.JOINTS)
        wrapper.changed.connect(self.changed)
        if not hasattr(self, "link_fields"):
            self.link_fields = {}
        self.link_fields[key] = wrapper
        return wrapper

    def draft_links(self):
        """The links of the form, and the schema_version that says whether there is one -- only for the fields the draft holds: a centre not placed by hand takes none (links.drop_unheld)."""
        found = {key: w.link() for key, w in getattr(self, "link_fields", {}).items() if w.link() is not None}
        if not self.manual_radio.isChecked():
            found = {key: link for key, link in found.items() if not key.startswith("center.")}
        if not found:
            return {}
        return {links.LINKS: found, "schema_version": connection.LINKED_SCHEMA_VERSION}

    def on_shown(self):
        """The tab brought to the front: the schemas are read again, so one renamed, redrawn or added in «Schémas» is offered here at once -- the form keeps what it holds, draft and all."""
        dirty = self.dirty
        source = self.draft()
        if not dirty and self.current_id is not None:
            # a saved calculation takes the schema its file names now -- a rename in «Schémas» rewrote it
            try:
                on_disk = json.loads((project.current().connections_dir / f"{self.current_id}.json").read_text(encoding="utf-8"))
                source["schema"] = on_disk.get("schema", source.get("schema", ""))
            except (OSError, ValueError, AttributeError):
                pass
        self.fill(source)
        self.dirty = dirty
        self.refresh()

    def schema_renamed(self, old, new):
        """A schema saved under a new id (schema_tab): the draft follows it, as the saved files already have."""
        if self.schema_combo.currentData() == old or self.draft().get("schema") == old:
            dirty = self.dirty
            self.fill(self.draft() | {"schema": new})
            self.dirty = dirty
            self.refresh()

    def fill(self, source, rows=None):
        """Puts a source into the form. `rows` is accepted and ignored: since v0.74 the fastener list is the schema's own markers with ticks against them, so there is no half-typed cell to carry back -- the draft's ticks travel in the source itself."""
        # A 3.0 or 3.1 file (or a draft kept from before v0.76) is read as 4.0: its connector and variant dropped, its name the one it states or else its id.
        source = connection.upgrade_source(source)
        members = source.get("members") or default_source("")["members"]
        self.loading = True
        try:
            self.set_schema_items(str(source.get("schema", "")))
            self.set_member_count(len(members))
            self.fill_elements()
            self.form_group = grouped_list.group_of(source)
            norm = source.get("norm")
            self.form_norm = norm.strip() if isinstance(norm, str) and norm.strip() else connection.DEFAULT_NORM
            self.form_norm_ref = str(source.get("norm_ref", "") or "").strip()
            self.name_edit.setText(str(source.get("name", "") or ""))
            self.id_edit.setText(str(source.get("id", "")))
            # an id that is not what the name makes reads as written over -- which is what a 3.x id carrying its variant is
            self.id_overridden = bool(source.get("id")) and source.get("id") != self.composed_id()
            self.label_edit.setText(str(source.get("label", "")))
            for i, w in enumerate(self.members):
                m = members[i] if i < len(members) else {"name": "", "element": ""}
                w["name"].setText(str(m.get("name", "")))
                eid = m.get("element", "")
                found = w["element"].findData(eid)
                if found < 0 and eid:  # an element the schema no longer has: kept, and said so
                    w["element"].addItem(f"{eid} (?)", eid)
                    found = w["element"].count() - 1
                w["element"].setCurrentIndex(max(0, found))
            self.reference_combo.setCurrentIndex(max(0, self.reference_combo.findData(source.get("reference", 1))))
            self.fill_markers(list(source.get("fasteners") or []))
            self.fill_centres()
            center = source.get("center", {"mode": "centroid"})
            mode = center.get("mode", "centroid")
            self.manual_radio.setChecked(mode == "manual")
            self.aid_radio.setChecked(mode == "aid")
            self.centroid_radio.setChecked(mode not in ("manual", "aid"))
            self.center_x.setValue(float(center.get("x", 0)))
            self.center_z.setValue(float(center.get("z", 0)))
            self.center_x.setEnabled(mode == "manual")
            self.center_z.setEnabled(mode == "manual")
            if mode == "aid":
                found = self.center_aid.findData(center.get("aid", ""))
                if found < 0 and center.get("aid"):
                    self.center_aid.addItem(f"{center['aid']} (?)", center["aid"])
                    found = self.center_aid.count() - 1
                self.center_aid.setCurrentIndex(max(0, found))
            self.center_aid.setEnabled(mode == "aid")
            directions = source.get("directions", {})
            self.direction_n.setValue(float(directions.get("N", 0)))
            self.direction_v.setValue(float(directions.get("V", 90)))
            # the trial forces a source states (issue #42, D-12); one saved before keeps the form's
            for key, value in (source.get("trial") or {}).items():
                if key in self.trial:
                    self.trial[key].setValue(float(value))
            found = links.links_of(source)
            values = linkable_spin.current_values() if found else {}
            for key, wrapper in getattr(self, "link_fields", {}).items():
                wrapper.set_link(found.get(key), values)
            for key in ("center.x", "center.z"):
                self.link_fields[key].set_editable(mode == "manual")
        finally:
            self.loading = False
        self.refresh()

    def on_center_mode(self, _checked):
        manual = self.manual_radio.isChecked()
        self.center_x.setEnabled(manual)
        self.center_z.setEnabled(manual)
        for key in ("center.x", "center.z"):
            self.link_fields[key].set_editable(manual)   # only a centre placed by hand may follow a variable
        self.center_aid.setEnabled(self.aid_radio.isChecked())
        if manual and not self.loading:
            # a fixed point starts where the calculated one was, so switching changes nothing until it is moved
            g = connection.analyse(self.draft() | {"center": {"mode": "centroid"}}, self.detail())
            if g["centroid"] is not None:
                was_loading, self.loading = self.loading, True
                self.center_x.setValue(round(g["centroid"][0], 1))
                self.center_z.setValue(round(g["centroid"][1], 1))
                self.loading = was_loading
        self.changed()

    # -- preview, results, commands --

    def refresh(self):
        """Redraws the figure and recomputes the polar moment, the trial forces and the calls, from the form as it is now."""
        source = self.draft()
        detail = self.detail()
        geometry = connection.analyse(source, detail)
        # the trial forces drawn on the figure, at the report's scale, as soon as there are any
        N, V, M = self.trial_values()
        forces = {"N": N, "V": V, "M": M} if any((N, V, M)) else None
        # In the window's own language, so the preview reads like the report that language would set.
        svg = connection_svg.render(connection_svg.layout(source, geometry, detail, connector_model.known_positions(project.current().data_dir)), forces=forces,
                                    highlight=self.selected_marker_index(), lang=self.app.lang)
        self.svg.load(QByteArray(svg.encode("utf-8")))
        self.svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)

        gravity = geometry["centroid"]
        self.centroid_value.setText(f"x_c = {fmt_value(gravity[0])} mm · z_c = {fmt_value(gravity[1])} mm" if gravity else "")
        center = geometry["center"]
        rows = [("n", str(geometry["n"]), False)]
        if center is not None:
            rows.append(("(x_c, z_c)", f"{fmt_value(center[0])} / {fmt_value(center[1])} mm", False))
        rows += [
            ("I_(p,x)", f"{fmt_value(geometry['I_px'])} mm²", False),
            ("I_(p,z)", f"{fmt_value(geometry['I_pz'])} mm²", False),
            ("I_p", f"{fmt_value(geometry['I_p'])} mm²", True),
            ("r_max", f"{fmt_value(geometry['r_max'])} mm", False),
        ]
        self.results.setText(richtext.results_html(rows))
        self.refresh_trial(source, geometry)

        # What the schema does not carry is said here as the export says it: a warning, never a stop.
        messages = [self.app.note_text(n) for n in connection.schema_warnings(source, detail, self.schemas(), source["id"] or "?")]
        try:
            connection.check_source(source, f"{source['id'] or '?'}.json")
        except validation.ValidationError as exc:
            messages.append(str(exc))
        self.message.setText("\n".join(messages))
        self.message.setVisible(bool(messages))

        self.fill_commands(source["id"])
        self.revert_button.setEnabled(self.dirty)
        self.update_list_marker()

    def trial_values(self):
        return tuple(self.trial[k].value() for k in ("N", "V", "M"))

    def refresh_trial(self, source, geometry):
        """The forces for the trial N, V and M, by connection.fastener_forces -- the same distribution the file of the polar moment computes by `#eq` and `#image-polar-moment` draws, for a look before the report is built: the largest resultant and every fastener carrying it, its components, and its force-grain angle to each member."""
        N, V, M = self.trial_values()
        if geometry["n"] == 0:
            self.trial_result.setText("")
            return
        try:
            rows, governing = connection.fastener_forces(geometry, source["directions"], N, V, M)
        except ValueError:
            self.trial_result.setText(richtext.subscripts(self.t("polar_no_moment")))
            return
        top = rows[governing[0]]
        line = connection.force_line(top["fx"], top["fz"])

        def angle(member_deg):
            beta = connection.grain_angle(line, member_deg)
            return "–" if beta is None else f"{fmt_value(round(beta, 1))}°"

        betas = " · ".join(
            f"β{str(j + 1).translate(SUBSCRIPTS)} = {angle(axis)} ({connection.member_label(m, j, self.detail())})"
            for j, (m, axis) in enumerate(zip(source["members"], geometry["axis"]))
        )
        self.trial_result.setText(richtext.subscripts(self.t(
            "polar_trial_result", f=fmt_value(top["f"]), k=connection.number_ranges([g + 1 for g in governing]),
            fx=fmt_value(top["fx"]), fz=fmt_value(top["fz"]), betas=betas,
        )))

    def fill_commands(self, cid):
        """The «Affichage» view told the calculation as it stands (display_view.DisplayTab): the calls to copy left the right pane in v0.117."""
        self.update_display()

    def display_entries(self):
        """What can show the calculation open (spec 2026-10-21-commandes-typst-refonte, UI-002): its file written out by the export -- N, V and M left to the engineer in it, the forces in its fasteners worked out from them --, included where a section prints it, and its I_p read by `#var`."""
        cid = self.draft_id() or "?"
        here = project.current()
        banner = display_view.saved_state(self.t, cid, self.t("polar_unsaved_hint"), self.current_id is None or self.dirty,
                                          here.data_dir / "connections.json", "connections", here.connections_dir / f"{cid}.json")
        return [
            display_view.Entry("file", "domain-file", call=ref.call_include_domain(connection.DOMAIN, cid), banner=banner),
            display_view.Entry("var", "var", call=ref.call_var_domain(connection.DOMAIN, cid, "I_p"), banner=banner),
        ]

    # -- the list --

    def sources_dir(self):
        return project.current().connections_dir

    def listed(self):
        """The calculations, «id — label», in the folder each names (list_connections)."""
        return [(cid, f"{cid} — {label}" if label else cid, group) for cid, label, group in list_connections()]

    def draft_text(self):
        """The draft's row names the id its name makes, until the ID field is written over (draft_id)."""
        return f"{self.draft_id() or '?'} {self.word('new_item')}"

    def draft_group(self):
        return self.form_group

    def take_group(self, group):
        """The draft's folder is the form's own (`form_group`), which `draft()` writes into the source."""
        self.form_group = group or ""

    def show_empty_hint(self):
        """Under the list, how a calculation is made -- or that there is none yet."""
        self.empty_hint.setText(self.t("polar_list_hint") if self.ids else self.t("polar_empty"))

    def export_listed(self, text):
        """The connections exported without naming one: a drop into a folder, an archive."""
        return self.export("", text)

    def selected_schema(self):
        """The schema a new calculation is drawn on: that of the calculation selected in the list, else the form's own, else the first there is -- "" where there is none, a calculation then opening on no drawing and saying so. A polar moment is of a schema since v0.76, where it was of a connector."""
        schemas = self.schemas()
        chosen = self.list.current_id()
        if chosen and chosen != POLAR_NEW_ROW:
            try:
                sid = json.loads((project.current().connections_dir / f"{chosen}.json").read_text(encoding="utf-8")).get("schema", "")
            except (OSError, ValueError, AttributeError):
                sid = ""
            if sid in schemas:
                return sid
        sid = self.schema_combo.currentData() or ""
        if sid in schemas:
            return sid
        return sorted(schemas)[0] if schemas else ""

    def load(self, cid):
        path = project.current().connections_dir / f"{cid}.json"
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(source, dict):
                raise ValueError("not a JSON object")
        except (OSError, ValueError) as exc:
            notices_ui.tell(self.t("polar_unreadable", name=path.name, error=exc), notifications.CRITICAL, exc=exc, key="polar_unreadable", args=dict(name=path.name, error=exc), source="woodcore_gui")
            source = default_source(cid)
        self.current_id = cid
        self.dirty = False
        self.fill(source)
        self.reload_list(select=cid)

    def new_source(self, schema_id=""):
        """A new calculation **drawn on `schema_id`**, its members the schema's linear elements and every one of its markers ticked, so it calculates the moment it opens (the v0.70 rule, docs/decisions.md §13). It is named after that schema, or `A01` where there is none, the first such name no calculation's id is made from yet."""
        schemas = self.schemas()
        detail = schemas.get(schema_id)
        name = next_free_name(schema_id or "A01", self.taken_ids())
        source = default_source(connection.id_from_name(name), members_from_schema(schema_id, schemas),
                                schema_id if detail is not None else "")
        source["name"] = name
        # Every connector marker ticked -- or, on a schema that carries none, every point ticked «connecteur»: both at once would count a marker drawn on a point twice.
        source["fasteners"] = schema_model.default_fasteners(detail)
        return source

    def load_first(self):
        """The first calculation saved, in file-name order, else a new one on the first schema there is, unsaved."""
        ordered = self.taken_ids()
        if ordered:
            self.load(ordered[0])
        else:
            self.current_id = None
            self.dirty = False
            self.fill(self.new_source(self.selected_schema()))
            self.reload_list(select=None)

    def taken_ids(self):
        return [cid for cid, _label, _group in list_connections()]

    def new(self):
        """A new calculation on the schema of the calculation selected in the list (else the form's, else the first there is) -- the only way a calculation is created."""
        if not self.confirm_leave():
            return
        self.current_id = None
        self.fill(self.new_source(self.selected_schema()))
        self.dirty = True
        self.reload_list(select=None)
        self.refresh()

    def duplicate(self):
        """A copy of the form as a new calculation, under the next free name made from the form's own: the same schema, members, ticks and centre, in the same folder."""
        if not self.confirm_leave():
            return
        source = self.draft()
        name = next_free_name(source.get("name") or source.get("id") or "A01", self.taken_ids())
        source |= {"name": name, "id": connection.id_from_name(name)}
        self.current_id = None
        self.fill(source)
        self.dirty = True
        self.reload_list(select=None)
        self.refresh()

    def revert(self):
        self.dirty = False
        if self.current_id is not None:
            self.load(self.current_id)
        else:
            self.load_first()

    # -- saving --

    def fail(self, text):
        return autosave.refuse(self, self.t("polar_save_failed_title"), text)

    def save(self):
        """Writes connections/<id>.json and exports the connections -- the draft checked first by the same rules export_all.py applies, so a calculation that saves is one the export takes. True when saved."""
        source = self.draft()
        cid = source["id"]
        # ⚠️ No table of typed x/z any more (v0.74): the fasteners are ticks against the schema's markers, which check_source below checks. Until v0.77 this method still read that table as two numbers a row, found every row «bad» -- a tick and a marker id -- and raised a KeyError on a message that no longer exists, so Enregistrer wrote nothing and said nothing.
        # the id is made from the name and may be written over: what it must be is a file name
        if not connection.ID_PATTERN.match(cid or ""):
            return self.fail(self.t("polar_id_invalid", id=cid))
        old = self.current_id
        renaming = old is not None and cid != old
        # the file system ignores case, the report does not: A01 and a01 are one file, and two ids
        clash = any(t.lower() == cid.lower() for t in self.taken_ids()) and (old is None or cid.lower() != old.lower())
        if clash:
            return self.fail(self.t("polar_id_exists", id=cid))
        if renaming and not autosave.ask_rename(self, "Woodcore", self.t("polar_rename", old=old, new=cid)):
            return False
        target = project.current().connections_dir / f"{cid}.json"
        try:
            connection.check_source(source, target.name)
        except validation.ValidationError as exc:
            return self.fail(str(exc))
        try:
            project.current().connections_dir.mkdir(parents=True, exist_ok=True)
            if renaming:
                (project.current().connections_dir / f"{old}.json").unlink(missing_ok=True)
            engine.write_json(target, source)
        except OSError as exc:
            return self.fail(str(exc))
        self.current_id = cid
        self.dirty = False
        self.export(cid, self.t("polar_saved", id=cid))
        self.reload_list(select=cid)
        self.refresh()
        return True

    def export(self, cid, done_text):
        """The connections' part of the export, run here and now: data/connections.json and the figures, from every saved source and the schemas they are drawn on. A failure -- another connection's file that no longer validates -- leaves data/ as it was and says why; what a schema no longer carries is exported and counted in the status line, the form saying what it is."""
        try:
            _data, warnings = connection.export(project.current().connections_dir, project.current().data_dir)
        except (validation.ValidationError, engine.EngineError, OSError) as exc:
            autosave.warn(self, "Woodcore", self.t("polar_export_failed", id=cid, error=exc))
            return False
        self.app.set_status(done_text + (" " + self.t("polar_warnings_status", count=len(warnings)) if warnings else ""))
        return True

    # -- surviving a rebuild --

    def view_state(self):
        return {
            "draft": self.draft(),
            "current_id": self.current_id,
            "dirty": self.dirty,
            "trial": list(self.trial_values()),
            "splitter": self.splitter.sizes(),
            "preview_splitter": self.preview_splitter.sizes(),
            "id_overridden": self.id_overridden,
        }

    def restore(self, state):
        if state:
            self.current_id = state.get("current_id")
            for key, value in zip(("N", "V", "M"), state.get("trial", [])):
                self.trial[key].setValue(value)
            self.fill(state["draft"])
            self.id_overridden = state.get("id_overridden", self.id_overridden)
            self.dirty = state.get("dirty", False)
            self.reload_list(select=self.current_id)
            if state.get("splitter"):
                self.splitter.setSizes(state["splitter"])
            if state.get("preview_splitter"):
                self.preview_splitter.setSizes(state["preview_splitter"])
            self.refresh()
        else:
            self.splitter.setSizes([1800, 4200, 5000])
            self.preview_splitter.setSizes([5000, 4000])
            self.load_first()
