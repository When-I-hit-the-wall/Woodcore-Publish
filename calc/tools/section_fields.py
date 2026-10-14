"""A position's section typed in fields of its own -- the one widget the Positions tab and the position plan's right pane both show (issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, REQ-008, UI-002).

The engineer, 08.10.2026: «choisir un type de section, puis saisir ses dimensions dans des champs séparés. Tous les types de section existants sont repris.» What a type's fields are is domains/section.py's FORMS and nothing written here: `rec` its width and height, a steel family its forms read off SZS C5 (L a·t or a·b·t, HD h or h·m …), a form chosen where a type has several, and a CLT panel one field a layer, as many as it has. What the fields write is the position's one `dimension` text (`section.join_dimension`), and **only when a field is typed in**: a dimension nobody touched is never rewritten (a «100 x 200» stays «100 x 200»). A text the type's forms do not read -- a descriptive one, «100/200» under a plate -- is left on its line, where it can be seen and mended (`set_code` says so).

The words are this module's own, in the window's three languages.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from domains import section

STRINGS = {
    "fr": {
        "sf_form": "Forme",
        "sf_b": "Largeur b", "sf_h": "Hauteur h", "sf_d": "Diamètre d", "sf_D": "Diamètre D", "sf_t": "Épaisseur t",
        "sf_a": "Côté a", "sf_m": "Masse m [kg/m]", "sf_l": "Longueur l", "sf_size": "Taille",
        "sf_layer": "Couche {n}", "sf_add_layer": "+ couche", "sf_remove_layer": "− couche",
        "sf_none": "—",
    },
    "de": {
        "sf_form": "Form",
        "sf_b": "Breite b", "sf_h": "Höhe h", "sf_d": "Durchmesser d", "sf_D": "Durchmesser D", "sf_t": "Dicke t",
        "sf_a": "Schenkel a", "sf_m": "Masse m [kg/m]", "sf_l": "Länge l", "sf_size": "Grösse",
        "sf_layer": "Lage {n}", "sf_add_layer": "+ Lage", "sf_remove_layer": "− Lage",
        "sf_none": "—",
    },
    "en": {
        "sf_form": "Form",
        "sf_b": "Width b", "sf_h": "Height h", "sf_d": "Diameter d", "sf_D": "Diameter D", "sf_t": "Thickness t",
        "sf_a": "Leg a", "sf_m": "Mass m [kg/m]", "sf_l": "Length l", "sf_size": "Size",
        "sf_layer": "Layer {n}", "sf_add_layer": "+ layer", "sf_remove_layer": "− layer",
        "sf_none": "—",
    },
}

# A CLT panel shown with no layers typed yet: three fields, the commonest panel's.
FIRST_LAYERS = 3


def _t(lang):
    return STRINGS[lang if lang in STRINGS else "en"]


def fill_types(combo, lang):
    """The section types in a combo -- none first, then the four of timber, then SZS C5's families, a separator between the kinds -- each «IPE — Profilés IPE», its data the code: what both tabs offer, from domains/section.py's TYPES."""
    combo.clear()
    # its longest name («ROR — Tubes ronds …», some 750 px) does not set the width of the pane it stands in: a drawing tool's options are in the right pane, which it would widen past the drawing (test_panes)
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(12)
    combo.addItem(_t(lang)["sf_none"], "")
    for i, entry in enumerate(section.TYPES):
        if i == 0 or entry["kind"] != section.TYPES[i - 1]["kind"]:
            combo.insertSeparator(combo.count())
        combo.addItem(f"{entry['code']} — {entry.get(lang) or entry['de']}", entry["code"])


class DimensionFields(QWidget):
    """The fields a type's dimension is typed in. `set_code(code, text)` shows the type's fields filled from the text (True), or none where the text does not read as one of its forms (False, the caller showing its line); `text()` what they write; `edited` when the engineer typed in a field, chose a form, added or took away a layer."""

    edited = Signal()

    def __init__(self, lang="fr", parent=None):
        super().__init__(parent)
        self.lang = lang
        self.code = ""
        self.form = ()
        self.form_layout = QFormLayout(self)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_combo = QComboBox()
        self.form_combo.currentIndexChanged.connect(self.on_form)
        self.form_caption = QLabel()
        self.form_layout.addRow(self.form_caption, self.form_combo)
        self.edits = []          # (caption, line edit) of the fields shown
        self.layer_row = QWidget()
        row = QHBoxLayout(self.layer_row)
        row.setContentsMargins(0, 0, 0, 0)
        self.add_layer = QPushButton()
        self.remove_layer = QPushButton()
        self.add_layer.clicked.connect(lambda: self.set_layers(len(self.edits) + 1, edited=True))
        self.remove_layer.clicked.connect(lambda: self.set_layers(max(2, len(self.edits) - 1), edited=True))
        row.addWidget(self.add_layer)
        row.addWidget(self.remove_layer)
        row.addStretch(1)
        self.form_layout.addRow(self.layer_row)
        self.loading = False
        self.retranslate(lang)
        self.set_code("", "")

    def retranslate(self, lang):
        self.lang = lang
        t = _t(lang)
        self.form_caption.setText(t["sf_form"])
        self.add_layer.setText(t["sf_add_layer"])
        self.remove_layer.setText(t["sf_remove_layer"])
        self._captions()

    def _caption(self, field, n):
        t = _t(self.lang)
        return t["sf_layer"].format(n=n) if section.is_layered(self.code) else t.get(f"sf_{field}", field)

    def _captions(self):
        for n, (caption, _edit) in enumerate(self.edits, start=1):
            caption.setText(self._caption(caption.property("field"), n))

    def _rows(self, fields, values=()):
        """The field rows rebuilt for `fields`, filled from `values`."""
        for caption, edit in self.edits:
            self.form_layout.removeRow(edit)
        self.edits = []
        for i, field in enumerate(fields):
            caption = QLabel()
            caption.setProperty("field", field)
            edit = QLineEdit(values[i] if i < len(values) else "")
            edit.setMaximumWidth(120)
            edit.textEdited.connect(lambda _text: self.loading or self.edited.emit())
            self.form_layout.insertRow(self.form_layout.rowCount() - 1, caption, edit)
            self.edits.append((caption, edit))
        self._captions()

    def set_code(self, code, text):
        """The fields of type `code`, filled from `text`; True where they are shown -- the text empty, or read as one of the type's forms --, False where the type has none or the text reads as none of them (nothing then shown)."""
        self.loading = True
        try:
            self.code = code or ""
            forms = section.dimension_forms(self.code)
            layered = section.is_layered(self.code)
            values = section.split_dimension(self.code, text) if (forms or layered) else None
            shown = bool(forms or layered) and (values is not None or not str(text or "").strip())
            self.form_combo.blockSignals(True)
            self.form_combo.clear()
            for form in forms:
                self.form_combo.addItem(" × ".join("n" if f == "size" else f for f in form), form)
            self.form_combo.blockSignals(False)
            many = len(forms) > 1 and shown
            self.form_layout.setRowVisible(self.form_combo, many)
            self.form_layout.setRowVisible(self.layer_row, layered and shown)
            if not shown:
                self._rows(())
                self.form = ()
            elif layered:
                self.form = ()
                count = len(values) if values else FIRST_LAYERS
                self._rows(("layer",) * count, values or ())
            else:
                self.form = section.form_of(self.code, len(values)) if values else forms[0]
                self.form_combo.blockSignals(True)
                self.form_combo.setCurrentIndex(forms.index(self.form))
                self.form_combo.blockSignals(False)
                self._rows(self.form, values or ())
            self.setVisible(shown)
            return shown
        finally:
            self.loading = False

    def on_form(self, index):
        """Another form chosen: its fields, the numbers typed kept where they fit."""
        if self.loading or index < 0:
            return
        values = [edit.text() for _caption, edit in self.edits]
        self.form = self.form_combo.itemData(index)
        self._rows(self.form, values)
        self.edited.emit()

    def set_layers(self, count, edited=False):
        values = [edit.text() for _caption, edit in self.edits]
        self._rows(("layer",) * count, values)
        if edited:
            self.edited.emit()

    def values(self):
        return [edit.text() for _caption, edit in self.edits]

    def text(self):
        """What the fields write into the dimension: «100/200», «101.6x10», «40/20/40» -- `section.join_dimension`."""
        if not self.edits:
            return ""
        return section.join_dimension(self.code, self.values())
