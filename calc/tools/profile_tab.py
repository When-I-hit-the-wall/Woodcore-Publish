# -*- coding: utf-8 -*-
"""The «Profilés» tab of the «Acier» group: the SZS C5 library to browse, and the free profiles of the project -- rectangles typed, drawn with the mouse or loaded from a model or a C5 profile, then changed (issue #50, spec 2026-10-12-section-acier REQ-003, UI-002, D-03, D-10, D-11, D-16; docs/ui/tab-steel.md).

The engineer: «profilé défini par l'utilisateur: dessiné par lui de manière paramétrique ou par dessin (s'inspirer légèrement du fichier python dans le cours de l'acier). L'utilisateur peut charger des profils modèles et ensuite les modifier pour arriver à son profil personnel». Three panes: **the free profiles** on the left; **the profile** in cards in the middle -- Nom · Description · ID, a model drawn from its numbers (I, U, T, L, tube, plate) or an SZS C5 profile loaded as its model, root radii left out (D-10), and the rectangles, each with its role in the section class (D-11); **the drawing and the values** on the right -- the rectangles drawn to scale, a drag adding one, and the section's values as domains/profile.py computes them --, and under them the library of SZS C5, read only.

A profile is a file of Woodcore-Datei/profiles/ (`Project.profiles_dir`), checked by `profile.check_source` before it is written. **A profile a position names (type USR) can be neither renamed nor deleted** (D-16): the refusal names the positions. Nothing is computed here: `profile.properties` is.
"""

import source_editor  # Ctrl+S bound the one way (source_editor.save_shortcut)
import copy
import json
import time

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem, QPushButton, QSplitter,
    QStyledItemDelegate, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

import autosave
import cards
import identity
import project
import richtext
import theme
import engine
from domains import connector, profile
from norms import szs_c5
from steel_tab_words import STRINGS  # noqa: F401  -- merged into the window's STRINGS by woodcore_gui_words

COLUMNS = ("name", "y", "z", "b", "h", "role")
ROLE_KEYS = {"internal": "pr_role_internal", "outstand": "pr_role_outstand", "none": "pr_role_none"}
MODEL_KEYS = {"I": "pr_model_I", "U": "pr_model_U", "T": "pr_model_T", "L": "pr_model_L", "RHS": "pr_model_RHS", "plate": "pr_model_plate"}
# what a model starts from, mm -- an I 200 × 100 as profile.new_source draws
MODEL_DEFAULTS = {"I": {"h": 200, "b": 100, "t_w": 6, "t_f": 10}, "U": {"h": 200, "b": 80, "t_w": 6, "t_f": 10}, "T": {"h": 100, "b": 100, "t_w": 6, "t_f": 10},
                  "L": {"a": 100, "b": 100, "t": 10}, "RHS": {"h": 200, "b": 100, "t": 8}, "plate": {"b": 200, "t": 10}}
# the values the right pane lists, in its order, with their unit
VALUES = (("A", "A", "mm²"), ("I_y", "I_y", "mm⁴"), ("I_z", "I_z", "mm⁴"), ("W_el_y", "W_(e l,y)", "mm³"), ("W_el_z", "W_(e l,z)", "mm³"),
          ("W_pl_y", "W_(p l,y)", "mm³"), ("W_pl_z", "W_(p l,z)", "mm³"), ("i_y", "i_y", "mm"), ("i_z", "i_z", "mm"), ("z_s", "z_s", "mm"), ("y_s", "y_s", "mm"))


def _fmt(value):
    if value is None:
        return "—"
    if abs(value) >= 1e5:
        return "%.4g" % value
    return ("%.3f" % value).rstrip("0").rstrip(".")


class RoleDelegate(QStyledItemDelegate):
    """The role of a rectangle, chosen in a list while the cell is edited -- the item keeps the role in its user data and shows its words; a combo set into every cell did not follow the table's layout off screen."""

    def __init__(self, words, parent=None):
        super().__init__(parent)
        self.words = words      # role -> its words

    def createEditor(self, parent, _option, _index):
        combo = QComboBox(parent)
        for role in profile.ROLES:
            combo.addItem(self.words[role], role)
        return combo

    def setEditorData(self, editor, index):
        editor.setCurrentIndex(max(editor.findData(index.data(Qt.ItemDataRole.UserRole)), 0))

    def setModelData(self, editor, model, index):
        role = editor.currentData()
        model.setData(index, role, Qt.ItemDataRole.UserRole)
        model.setData(index, self.words[role], Qt.ItemDataRole.DisplayRole)


class ProfileCanvas(QWidget):
    """The rectangles drawn to scale, y to the right and z upwards; a drag draws a new one, snapped to the millimetre."""

    drawn = Signal(float, float, float, float)

    def __init__(self):
        super().__init__()
        self.parts = []
        self.setMinimumSize(260, 260)
        self._start = None
        self._now = None

    def set_parts(self, parts):
        self.parts = parts
        self.update()

    def _frame(self):
        if self.parts:
            y0 = min(p["y"] for p in self.parts)
            y1 = max(p["y"] + p["b"] for p in self.parts)
            z0 = min(p["z"] for p in self.parts)
            z1 = max(p["z"] + p["h"] for p in self.parts)
        else:
            y0, y1, z0, z1 = 0, 200, 0, 200
        span = max(y1 - y0, z1 - z0, 1.0) * 1.3
        cy, cz = (y0 + y1) / 2, (z0 + z1) / 2
        scale = min(self.width(), self.height()) / span
        return scale, cy, cz

    def to_screen(self, y, z):
        scale, cy, cz = self._frame()
        return QPointF(self.width() / 2 + (y - cy) * scale, self.height() / 2 - (z - cz) * scale)

    def to_world(self, point):
        scale, cy, cz = self._frame()
        return round(cy + (point.x() - self.width() / 2) / scale), round(cz - (point.y() - self.height() / 2) / scale)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(theme.colour("paper")))
        fills = {"internal": theme.colour("accent-soft"), "outstand": theme.colour("wood-soft"), "none": theme.colour("bg-sunk")}
        for p in self.parts:
            a = self.to_screen(p["y"], p["z"] + p["h"])
            b = self.to_screen(p["y"] + p["b"], p["z"])
            painter.setBrush(QBrush(QColor(fills.get(p["role"], fills["none"]))))
            painter.setPen(QPen(QColor(theme.colour("ink")), 1.2))
            painter.drawRect(QRectF(a, b))
        if self._start and self._now:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(theme.colour("drawing-select")), 1.2, Qt.PenStyle.DashLine))
            painter.drawRect(QRectF(self._start, self._now).normalized())
        painter.end()

    def mousePressEvent(self, event):
        self._start = event.position()
        self._now = None

    def mouseMoveEvent(self, event):
        if self._start is not None:
            self._now = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        if self._start is None:
            return
        y0, z0 = self.to_world(self._start)
        y1, z1 = self.to_world(event.position())
        self._start = self._now = None
        self.update()
        if abs(y1 - y0) >= 1 and abs(z1 - z0) >= 1:
            self.drawn.emit(min(y0, y1), min(z0, z1), abs(y1 - y0), abs(z1 - z0))


class ProfileTab(source_editor.SourceEditorTab, QWidget):
    """The «Profilés» tab -- see the module's docstring."""
    WORDS = "pr"   # the prefix of its words for the question about unsaved changes (source_editor.SourceEditorTab)


    KEY = "tab_st_profiles"

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False
        self.dirty = False
        self.current_id = None
        self.source = profile.new_source(self._free_id())
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_form())
        self.splitter.addWidget(self.build_right())
        for index, stretch in enumerate((2, 5, 5)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)
        source_editor.save_shortcut(self)   # Ctrl+S
        self.reload_list()
        ids = self.ids()
        if ids:
            self.load(ids[0])
        else:
            self.fill_form()

    # --- the list ------------------------------------------------------------------------

    def ids(self):
        return [p.stem for p in profile.source_paths()]

    def _free_id(self):
        taken = {i.lower() for i in self.ids()} if project.current() else set()
        n = 1
        while "pr-%02d" % n in taken:
            n += 1
        return "PR-%02d" % n

    def build_list(self):
        box = QWidget()
        column = QVBoxLayout(box)
        title = QLabel(self.t("pr_list"))
        title.setFont(self.app.bold_font)
        column.addWidget(title)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.on_list_change)
        column.addWidget(self.list, 1)
        self.empty_hint = cards.note(self.t("pr_empty"))
        column.addWidget(self.empty_hint)
        row = QHBoxLayout()
        for key, slot in (("pr_new", self.new), ("pr_duplicate", self.duplicate), ("pr_delete", self.delete)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        column.addLayout(row)
        return box

    def reload_list(self, select=None):
        self.loading = True
        self.list.clear()
        select = select or self.current_id
        for pid in self.ids():
            item = QListWidgetItem(pid)
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.list.addItem(item)
        if select:
            for row in range(self.list.count()):
                if self.list.item(row).text() == select:
                    self.list.setCurrentRow(row)
        self.empty_hint.setVisible(self.list.count() == 0)
        self.loading = False
        self.update_list_marker()

    def update_list_marker(self):
        """The dot of unsaved changes on the profile being edited and on the tab, every other row keeping the blank mark's room (the window's rule, test_window)."""
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setIcon(self.app.dirty_mark(self.dirty and item.data(Qt.ItemDataRole.UserRole) == self.current_id))
        self.app.update_tab_marks()

    def on_list_change(self, current, _previous=None):
        if self.loading or current is None or current.text() == self.current_id:
            return
        if not self.confirm_leave():
            self.reload_list(self.current_id)
            return
        self.load(current.text())

    # --- the form --------------------------------------------------------------------------

    def build_form(self):
        panel = QWidget()
        column = QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 0, 0)
        scroll, self.form = cards.column()
        column.addWidget(scroll, 1)

        box = cards.card()
        self.identity = identity.IdentityRows(cards.form(box), self.t, self.touch)
        self.form.addWidget(box)

        # a model drawn from its numbers
        box = cards.card(self.t("pr_box_model"))
        form = cards.form(box)
        self.model_box = QComboBox()
        for kind in profile.TEMPLATES:
            self.model_box.addItem(self.t(MODEL_KEYS[kind]), kind)
        self.model_box.currentIndexChanged.connect(self.on_model)
        form.addRow(self.t("pr_model"), self.model_box)
        self.param_spins = {}
        for name in sorted({p for params in profile.TEMPLATES.values() for p in params}):
            spin = QDoubleSpinBox()
            spin.setRange(0.1, 10000.0)
            spin.setDecimals(1)
            spin.setSuffix(" mm")
            self.param_spins[name] = spin
            form.addRow(name, spin)
        self.model_form = form
        draw = QPushButton(self.t("pr_load_model"))
        draw.clicked.connect(self.draw_model)
        form.addRow("", draw)
        self.form.addWidget(box)

        # an SZS C5 profile loaded as its model
        box = cards.card(self.t("pr_c5"))
        form = cards.form(box)
        self.c5_family = QComboBox()
        for code in profile.C5_TEMPLATES:
            self.c5_family.addItem(code, code)
        self.c5_family.currentIndexChanged.connect(lambda _i: self.fill_c5_sizes(self.c5_family, self.c5_size))
        self.c5_size = QComboBox()
        form.addRow(self.t("st_family"), self.c5_family)
        form.addRow(self.t("st_size"), self.c5_size)
        load = QPushButton(self.t("pr_load_c5"))
        load.clicked.connect(self.load_c5)
        form.addRow("", load)
        form.addRow("", cards.note(self.t("pr_c5_note")))
        self.fill_c5_sizes(self.c5_family, self.c5_size)
        self.form.addWidget(box)

        # the rectangles
        box = cards.card(self.t("pr_box_parts"))
        rows = QVBoxLayout(box)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([self.t("pr_col_" + c) for c in COLUMNS])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.role_words = {role: self.t(ROLE_KEYS[role]) for role in profile.ROLES}
        self.table.setItemDelegateForColumn(len(COLUMNS) - 1, RoleDelegate(self.role_words, self.table))
        self.table.itemChanged.connect(self.on_table)
        rows.addWidget(self.table)
        buttons = QHBoxLayout()
        add = QPushButton(self.t("pr_add"))
        add.clicked.connect(lambda: self.add_part(0, 0, 100, 10))
        remove = QPushButton(self.t("pr_remove"))
        remove.clicked.connect(self.remove_part)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        rows.addLayout(buttons)
        rows.addWidget(cards.note(self.t("pr_draw_hint")))
        self.form.addWidget(box)
        self.form.addStretch(1)

        actions = QHBoxLayout()
        revert = QPushButton(self.t("pr_revert"))
        revert.clicked.connect(self.revert)
        save = QPushButton(self.t("pr_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addStretch(1)
        actions.addWidget(revert)
        actions.addWidget(save)
        column.addLayout(actions)
        self.on_model()
        return panel

    def build_right(self):
        scroll, column = cards.column(margins=(0, 10, 4, 0), hold=False)
        self.message = QLabel("")
        self.message.setWordWrap(True)
        self.message.setProperty("callout", "warning")
        self.message.setVisible(False)
        column.addWidget(self.message)
        self.canvas = ProfileCanvas()
        self.canvas.drawn.connect(self.add_part)
        column.addWidget(self.canvas, 1)
        box = cards.card(self.t("pr_box_values"))
        self.values_label = QLabel("")
        self.values_label.setTextFormat(Qt.TextFormat.RichText)
        self.values_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        QVBoxLayout(box).addWidget(self.values_label)
        column.addWidget(box)
        box = cards.card(self.t("pr_box_library"))
        form = cards.form(box)
        self.lib_family = QComboBox()
        for code in szs_c5.tabulated():
            self.lib_family.addItem(code, code)
        self.lib_size = QComboBox()
        self.lib_family.currentIndexChanged.connect(lambda _i: self.fill_c5_sizes(self.lib_family, self.lib_size))
        self.lib_size.currentIndexChanged.connect(self.fill_library)
        form.addRow(self.t("st_family"), self.lib_family)
        form.addRow(self.t("st_size"), self.lib_size)
        self.library_label = QLabel("")
        self.library_label.setTextFormat(Qt.TextFormat.RichText)
        self.library_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("", self.library_label)
        self.fill_c5_sizes(self.lib_family, self.lib_size)
        column.addWidget(box)
        return scroll

    def fill_c5_sizes(self, family, sizes):
        sizes.blockSignals(True)
        sizes.clear()
        for size in szs_c5.sizes(family.currentData()):
            sizes.addItem(size.replace("x", "×"), size)
        sizes.blockSignals(False)
        if sizes is getattr(self, "lib_size", None):
            self.fill_library()

    def fill_library(self, *_args):
        code, size = self.lib_family.currentData(), self.lib_size.currentData()
        row = szs_c5.profile(code, size.split("x")) if code and size else None
        if not row:
            self.library_label.setText("")
            return
        keys = [k for k in ("m", "A", "A_v", "I_y", "W_el_y", "W_pl_y", "i_y", "I_z", "W_el_z", "W_pl_z", "i_z", "K", "h", "b", "t_w", "t_f", "t", "r", "h_1") if row.get(k) is not None]
        units = {"m": "kg/m", "A": "mm²", "A_v": "mm²", "K": "mm⁴", "I_y": "mm⁴", "I_z": "mm⁴"}
        lines = ["<tr><td>%s</td><td align='right'>%s</td><td>%s</td></tr>" % (richtext.math_html(k), richtext.escape(_fmt(row[k])),
                 units.get(k, "mm³" if k.startswith("W") else "mm")) for k in keys]
        note = richtext.escape(self.t("pr_library_note", page=row["norm_ref"]))
        self.library_label.setText("<table>%s</table><p style='color:%s'>%s</p>" % ("".join(lines), theme.colour("muted"), note))

    # --- the draft -------------------------------------------------------------------------

    def on_model(self, *_args):
        kind = self.model_box.currentData()
        for name, spin in self.param_spins.items():
            self.model_form.setRowVisible(spin, name in profile.TEMPLATES[kind])
            if name in MODEL_DEFAULTS[kind]:
                spin.setValue(MODEL_DEFAULTS[kind][name])

    def draw_model(self):
        kind = self.model_box.currentData()
        params = {name: self.param_spins[name].value() for name in profile.TEMPLATES[kind]}
        try:
            parts = profile.template(kind, **params)
        except ValueError as exc:
            return self.say(self.t("pr_invalid", error=str(exc)))
        self.source["template"] = {"kind": kind, "params": params}
        self.set_parts(parts)

    def load_c5(self):
        code, size = self.c5_family.currentData(), self.c5_size.currentData()
        model = profile.from_c5(code, size.split("x")) if code and size else None
        if model is None:
            return self.say(self.t("pr_invalid", error="%s %s" % (code, size)))
        kind, params = model
        self.source["template"] = {"c5": "%s %s" % (code, size.replace("x", "×")), "kind": kind, "params": params}
        self.set_parts(profile.template(kind, **params))

    def set_parts(self, parts):
        self.source["parts"] = copy.deepcopy(parts)
        self.fill_table()
        self.touch()

    def add_part(self, y, z, b, h):
        parts = self.draft()["parts"]
        names = {p["name"] for p in parts}
        n = len(parts) + 1
        while "R%d" % n in names:
            n += 1
        parts.append({"name": "R%d" % n, "y": float(y), "z": float(z), "b": float(b), "h": float(h), "role": "none"})
        self.set_parts(parts)

    def remove_part(self):
        row = self.table.currentRow()
        if row < 0:
            return
        parts = self.draft()["parts"]
        del parts[row]
        self.set_parts(parts)

    def fill_table(self):
        self.loading = True
        parts = self.source.get("parts") or []
        self.table.setRowCount(len(parts))
        for row, part in enumerate(parts):
            for col, key in enumerate(COLUMNS[:-1]):
                value = part.get(key)
                self.table.setItem(row, col, QTableWidgetItem(value if key == "name" else _fmt(float(value))))
            role = part.get("role") if part.get("role") in profile.ROLES else "none"
            item = QTableWidgetItem(self.role_words[role])
            item.setData(Qt.ItemDataRole.UserRole, role)
            self.table.setItem(row, len(COLUMNS) - 1, item)
        self.loading = False

    def on_table(self, _item):
        if not self.loading:
            self.touch()

    def draft(self):
        s = copy.deepcopy(self.source)
        name, description, pid = self.identity.values()
        s["id"], s["name"], s["label"] = pid, name, description
        parts = []
        for row in range(self.table.rowCount()):
            part = {}
            for col, key in enumerate(COLUMNS[:-1]):
                item = self.table.item(row, col)
                text = item.text().strip() if item else ""
                if key == "name":
                    part[key] = text
                else:
                    try:
                        part[key] = float(text.replace(",", "."))
                    except ValueError:
                        part[key] = text   # check_source names the cell
            item = self.table.item(row, len(COLUMNS) - 1)
            part["role"] = (item.data(Qt.ItemDataRole.UserRole) if item else None) or "none"
            parts.append(part)
        s["parts"] = parts
        return s

    def touch(self, *_args):
        if self.loading:
            return
        self.dirty = True
        self.refresh()
        self.update_list_marker()

    def refresh(self):
        s = self.draft()
        self.canvas.set_parts([p for p in s["parts"] if all(isinstance(p.get(k), float) for k in ("y", "z", "b", "h"))])
        try:
            profile.check_source(s)
            values = profile.properties(s["parts"])
        except Exception as exc:  # broad: what is wrong is said in the pane, never raised through a slot
            self.say(self.t("pr_invalid", error=str(exc)))
            self.values_label.setText("")
            return
        self.say("")
        rows = "".join("<tr><td>%s</td><td align='right'>%s</td><td>%s</td></tr>" % (richtext.math_html(sym), richtext.escape(_fmt(values[key])), unit)
                       for key, sym, unit in VALUES)
        self.values_label.setText("<table>%s</table>" % rows)

    def say(self, text):
        self.message.setText(text)
        self.message.setVisible(bool(text))
        return False

    def fill_form(self):
        self.loading = True
        s = self.source
        self.identity.fill(s.get("name", ""), s.get("label", ""), s.get("id", ""), saved=self.current_id is not None)
        self.loading = False
        self.fill_table()
        self.refresh()

    def load(self, pid):
        path = self.app_dir() / ("%s.json" % pid)
        try:
            self.source = profile.read_source(path)
        except Exception:  # broad: a profile the checks refuse is still opened, to be repaired here
            self.source = json.loads(path.read_text(encoding="utf-8"))
        self.current_id = pid
        self.dirty = False
        self.fill_form()
        self.update_list_marker()

    def app_dir(self):
        return project.current().profiles_dir

    # --- the buttons ----------------------------------------------------------------------

    def cited(self, pid):
        """The positions whose section is the free profile `pid` (D-16)."""
        positions = connector.known_positions(project.current().data_dir)
        return profile.cited_by(pid, [dict(record, id=key) for key, record in positions.items()])

    def new(self):
        if not self.confirm_leave():
            return
        self.source = profile.new_source(self._free_id())
        self.current_id = None
        self.dirty = True
        self.fill_form()
        self.reload_list()

    def duplicate(self):
        if not self.confirm_leave():
            return
        source = self.draft()
        source["id"] = self._free_id()
        self.source = source
        self.current_id = None
        self.dirty = True
        self.fill_form()
        self.update_list_marker()

    def revert(self):
        if self.current_id:
            self.load(self.current_id)
        else:
            self.new()

    def save(self):
        s = self.draft()
        pid = s.get("id") or ""
        taken = {i.lower() for i in self.ids()} - ({self.current_id.lower()} if self.current_id else set())
        if not profile.ID_PATTERN.match(pid) or pid.lower() in taken:
            autosave.refuse(self, self.t(self.KEY), self.t("pr_taken", id=pid))
            return False
        if self.current_id and self.current_id != pid:
            cited = self.cited(self.current_id)
            if cited:
                autosave.refuse(self, self.t(self.KEY), self.t("pr_cited", id=self.current_id, positions=", ".join(cited)))
                return False
        try:
            profile.check_source(s)
        except Exception as exc:  # broad: the checker's own message is what helps
            autosave.refuse(self, self.t(self.KEY), self.t("pr_invalid", error=str(exc)))
            return False
        folder = self.app_dir()
        folder.mkdir(parents=True, exist_ok=True)
        if self.current_id and self.current_id != pid:
            (folder / ("%s.json" % self.current_id)).unlink(missing_ok=True)
        engine.write_json(folder / ("%s.json" % pid), s)
        self.source, self.current_id, self.dirty = s, pid, False
        self.app.set_status(self.t("pr_saved", id=pid))
        self.reload_list(pid)
        return True

    def delete(self):
        """«Supprimer»: the profile goes into profiles/archives/, as every source of the window -- refused while a position names it (D-16)."""
        if not self.current_id:
            self.new()
            return False
        cited = self.cited(self.current_id)
        if cited:
            autosave.refuse(self, self.t(self.KEY), self.t("pr_cited", id=self.current_id, positions=", ".join(cited)))
            return False
        path = self.app_dir() / ("%s.json" % self.current_id)
        archives = self.app_dir() / "archives"
        archives.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            path.replace(archives / ("%s-%s.json" % (time.strftime("%y%m%d-%H%M%S"), self.current_id)))
        self.current_id, self.dirty = None, False
        self.reload_list()
        ids = self.ids()
        if ids:
            self.load(ids[0])
        else:
            self.new()
        return True

    # --- the window's bookkeeping ----------------------------------------------------------

    def view_state(self):
        return {"splitter": self.splitter.sizes()}

    def on_shown(self):
        self.reload_list(self.current_id)
