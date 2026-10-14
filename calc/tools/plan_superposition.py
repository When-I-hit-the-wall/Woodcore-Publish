"""The «Superposition» module of the plan tabs' right pane (v0.116, docs/domain/position-plans.md §3.3sexies, docs/domain/fire-plans.md §3.3vicies, docs/ui/window.md §10quater): another plan of the same tab shown over the plan open, to draw what stands on the storey above or below.

The engineer: «superposer au plan un autre plan déjà existant avec ou sans les éléments que l'on a dessinés par dessus … en transparence avec une quantité de transparence que l'on peut modifier … le dessin affiché avec ses couleurs normales ou le dessin en gris avec ses éléments en couleur ou le dessin et les éléments en gris ou alors … dans une couleur … vert, bleu, jaune, rouge … rose … faire correspondre le point d'un plan au point d'un autre plan … au travers de deux clics … les éléments du plan rajouté … ne doivent pas pouvoir être sélectionnés».

What it is: a card shown while nothing is selected on the plan (drawing_tab's modules, `when="plan"`), standing right after «Taille des symboles». Its controls write the open plan's optional `superposition` (plan.superposition_of) through the tab's `edit`, one step of «Annuler» each -- a drag of the opacity one step --; the canvas shows what it says (PlanCanvas.sync_superposition) and says back what it found (`superposition_changed`), which is what the card is filled from. The colour is two controls: a colour -- «Couleurs normales», «Gris» or one of five -- given to the superposed plan's background, and «Éléments dans cette couleur aussi», which gives it to its elements as well: «Gris» alone is «le dessin en gris avec ses éléments en couleur», with the switch «le dessin et les éléments en gris», and a colour alone «le plan rouge, les éléments gardent leur couleur». «Aligner…» is the canvas's two-click tool (plan_canvas.ALIGN_TOOL).

Nothing here is printed or exported: the field lies in the source and in no record of data/ (plan.record, fire's), and the superposed plan is drawn by the window alone. Both tabs of plans get the module from their shared base (drawing_tab.DrawingTab.build_properties -> install); the plans offered are the tab's own.
"""

import json

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QCheckBox, QComboBox, QPushButton, QVBoxLayout

import cards
from domains import fire
from domains import plan as model
import plan_canvas

# The module's words, in the window's three languages: its own, as the export sheets' bundles have theirs (sheet_editor.bundle_words) -- the module serves two tabs, each with STRINGS of its own.
WORDS = {
    "fr": {
        "title": "Superposition",
        "plan": "Plan superposé",
        "none": "(aucun)",
        "elements": "Avec les éléments dessinés",
        "opacity": "Opacité",
        "colour": "Couleur",
        "colour_normal": "Couleurs normales",
        "colour_grey": "Gris",
        "colour_green": "Vert",
        "colour_blue": "Bleu",
        "colour_yellow": "Jaune",
        "colour_red": "Rouge",
        "colour_pink": "Rose",
        "tint": "Éléments dans cette couleur aussi",
        "align": "Aligner…",
        "align_tip": "Deux clics : un point du plan superposé, puis le point de ce plan sur lequel il doit tomber.",
        "reset": "Réinitialiser l'alignement",
        "reset_tip": "Les coins supérieurs gauches des deux cadrages l'un sur l'autre.",
        "align_1": "Aligner : cliquez un point du plan superposé.",
        "align_2": "Aligner : cliquez le point de ce plan sur lequel il doit tomber.",
        "missing": "Le plan {plan} n'existe plus : rien n'est superposé.",
        "unscaled": "L'un des deux plans n'a pas d'échelle : le plan superposé l'est à l'échelle de sa feuille.",
        "note": "Une aide au dessin : ni imprimée ni exportée, et rien n'y est sélectionné.",
        "need_plan": "Choisissez d'abord un plan à superposer.",
        "need_colour": "Choisissez d'abord une couleur autre que les couleurs normales.",
    },
    "de": {
        "title": "Überlagerung",
        "plan": "Überlagerter Plan",
        "none": "(keiner)",
        "elements": "Mit den gezeichneten Elementen",
        "opacity": "Deckkraft",
        "colour": "Farbe",
        "colour_normal": "Normale Farben",
        "colour_grey": "Grau",
        "colour_green": "Grün",
        "colour_blue": "Blau",
        "colour_yellow": "Gelb",
        "colour_red": "Rot",
        "colour_pink": "Rosa",
        "tint": "Elemente ebenfalls in dieser Farbe",
        "align": "Ausrichten…",
        "align_tip": "Zwei Klicks: ein Punkt des überlagerten Plans, dann der Punkt dieses Plans, auf den er fallen soll.",
        "reset": "Ausrichtung zurücksetzen",
        "reset_tip": "Die oberen linken Ecken der beiden Ausschnitte aufeinander.",
        "align_1": "Ausrichten: Klicken Sie auf einen Punkt des überlagerten Plans.",
        "align_2": "Ausrichten: Klicken Sie auf den Punkt dieses Plans, auf den er fallen soll.",
        "missing": "Den Plan {plan} gibt es nicht mehr: nichts wird überlagert.",
        "unscaled": "Einer der beiden Pläne hat keinen Massstab: der überlagerte Plan erscheint im Massstab seines Blattes.",
        "note": "Eine Zeichenhilfe: weder gedruckt noch exportiert, und nichts darin wird ausgewählt.",
        "need_plan": "Wählen Sie zuerst einen Plan zum Überlagern.",
        "need_colour": "Wählen Sie zuerst eine andere Farbe als die normalen Farben.",
    },
    "en": {
        "title": "Overlay",
        "plan": "Plan shown over",
        "none": "(none)",
        "elements": "With its drawn elements",
        "opacity": "Opacity",
        "colour": "Colour",
        "colour_normal": "Normal colours",
        "colour_grey": "Grey",
        "colour_green": "Green",
        "colour_blue": "Blue",
        "colour_yellow": "Yellow",
        "colour_red": "Red",
        "colour_pink": "Pink",
        "tint": "Elements in this colour too",
        "align": "Align…",
        "align_tip": "Two clicks: a point of the plan shown over this one, then the point of this plan it is to lie on.",
        "reset": "Reset the alignment",
        "reset_tip": "The top left corners of the two crops on each other.",
        "align_1": "Align: click a point of the plan shown over this one.",
        "align_2": "Align: click the point of this plan it is to lie on.",
        "missing": "Plan {plan} no longer exists: nothing is shown over this one.",
        "unscaled": "One of the two plans has no scale: the plan shown over this one is at the scale of its sheet.",
        "note": "A drawing aid: neither printed nor exported, and nothing in it is selected.",
        "need_plan": "Choose a plan to show over this one first.",
        "need_colour": "Choose a colour other than the normal colours first.",
    },
}


def word(lang, key, **values):
    """A word of the module in `lang` (English where the language is none of the three)."""
    text = WORDS.get(lang, WORDS["en"])[key]
    return text.format(**values) if values else text


class SuperpositionModule(QObject):
    """The «Superposition» card of `tab` (a drawing_tab.DrawingTab), and what it does: the canvas's resolver of the plan named, the card filled from what the canvas found, the field written through the tab's edit."""

    def __init__(self, tab):
        super().__init__(tab)
        self.tab = tab
        self.canvas = tab.canvas
        self.lang = getattr(tab.app, "lang", "en")
        self.filling = False
        self.listed_for = None       # the plan the list of plans was filled for (opened): filled again when another is open
        self._cache = {}             # plan id -> ((mtime, size), source)

        self.card = cards.card(self.w("title"))
        form = cards.form(self.card)
        self.plan_combo = QComboBox()
        # as wide as the pane gives it, not as its longest plan's name: a combo sized to its content set the right pane's width (tests/test_panes.py)
        self.plan_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.plan_combo.setMinimumContentsLength(8)
        self.plan_combo.currentIndexChanged.connect(self.on_plan)
        form.addRow(self.w("plan"), self.plan_combo)
        self.elements_box = QCheckBox(self.w("elements"))
        self.elements_box.toggled.connect(self.on_elements)
        form.addRow("", self.elements_box)
        self.opacity = tab.slider(int(model.SUPERPOSITION_OPACITY[0] * 100), int(model.SUPERPOSITION_OPACITY[1] * 100), self.on_opacity)
        form.addRow(self.w("opacity"), self.opacity)
        self.colour_combo = QComboBox()
        for colour in model.SUPERPOSITION_COLOURS:
            self.colour_combo.addItem(self.w(f"colour_{colour}"), colour)
        self.colour_combo.currentIndexChanged.connect(self.on_colour)
        form.addRow(self.w("colour"), self.colour_combo)
        self.tint_box = QCheckBox(self.w("tint"))
        self.tint_box.toggled.connect(self.on_tint)
        form.addRow("", self.tint_box)
        row = QVBoxLayout()   # one under the other: side by side they set the right pane's width (tests/test_panes.py)
        self.align_button = QPushButton(self.w("align"))
        self.align_button.setToolTip(self.w("align_tip"))
        self.align_button.clicked.connect(self.start_align)
        self.reset_button = QPushButton(self.w("reset"))
        self.reset_button.setToolTip(self.w("reset_tip"))
        self.reset_button.clicked.connect(self.reset_alignment)
        row.addWidget(self.align_button)
        row.addWidget(self.reset_button)
        form.addRow("", row)
        self.state_note = cards.note("")
        form.addRow(self.state_note)
        form.addRow(cards.note(self.w("note")))
        self.card.installEventFilter(self)

        self.canvas.superposition_resolver = self.resolve
        self.canvas.superposition_changed.connect(self.fill)
        self.canvas.align_step.connect(self.on_align_step)
        self.fill()

    def w(self, key, **values):
        return word(self.lang, key, **values)

    def eventFilter(self, watched, event):
        if watched is self.card and event.type() == QEvent.Type.Show:
            self.fill_plans()   # a plan saved, renamed or archived meanwhile
        return False

    # -- the plan named --

    def resolve(self, pid):
        """(source, frame) of the tab's plan `pid` -- read from its file, kept while the file is unchanged -- or None where it is not there, cannot be read or is the plan open itself. A fire-protection plan that follows a position plan is drawn over that plan's frame, its own crop laid over it (fire_tab.followed_frame)."""
        if not pid or pid in (self.tab.current_id, self.tab.source.get("id")):
            return None
        path = self.tab.sources_dir() / f"{pid}.json"
        try:
            stat = path.stat()
            stamp = (stat.st_mtime_ns, stat.st_size)
            cached = self._cache.get(pid)
            if cached is not None and cached[0] == stamp:
                source = cached[1]
            else:
                source = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(source, dict):
                    return None
                self._cache[pid] = (stamp, source)
        except (OSError, ValueError):
            return None
        frame = source
        followed = getattr(self.tab, "followed_frame", None)
        if followed is not None and fire.follows(source) is not None:
            base = followed(source)
            if base is not None:
                frame = dict(base)
                if "crop" in source:
                    frame["crop"] = source["crop"]
        return source, frame

    def default_offset(self, pid):
        found = self.resolve(pid)
        if found is None:
            return None
        return model.superposition_default_offset(self.canvas.frame_source(), found[1])

    # -- the card --

    def opened(self):
        """What tells one plan opened from the next: its id and the draft itself -- a plan never saved has no id, and «Nouveau» opens another draft (open_source replaces it, an undo does not)."""
        return (self.tab.current_id, id(self.tab.source))

    def fill_plans(self):
        """The plans offered: the tab's own but the plan open, as the list names them."""
        self.listed_for = self.opened()
        spec = model.superposition_of(self.tab.source) or {}
        filling, self.filling = self.filling, True
        try:
            self.plan_combo.clear()
            self.plan_combo.addItem(self.w("none"), "")
            mine = {self.tab.current_id, self.tab.source.get("id")}
            for pid, source, _group in self.tab.list_sources():
                if source is None or pid in mine:
                    continue
                self.plan_combo.addItem(self.tab.entry_text(pid, source), pid)
            named = spec.get("plan", "")
            index = self.plan_combo.findData(named)
            if index < 0 and named:   # a plan that is gone stays named, said in the note
                self.plan_combo.addItem(f"{named} (?)", named)
                index = self.plan_combo.count() - 1
            self.plan_combo.setCurrentIndex(max(0, index))
        finally:
            self.filling = filling

    def fill(self):
        """The card from the source and from what the canvas found."""
        if self.listed_for != self.opened() or self.plan_combo.count() == 0:
            self.fill_plans()
        spec = model.superposition_of(self.tab.source)
        state = self.canvas.superposition_state
        filling, self.filling = self.filling, True
        try:
            named = spec["plan"] if spec else ""
            index = self.plan_combo.findData(named)
            if index < 0 and named:
                self.plan_combo.addItem(f"{named} (?)", named)
                index = self.plan_combo.count() - 1
            self.plan_combo.setCurrentIndex(max(0, index))
            values = spec or model.SUPERPOSITION_DEFAULT
            self.elements_box.setChecked(bool(values.get("elements", True)))
            self.opacity.slider.setValue(round(float(values.get("opacity", 0.5)) * 100))
            self.colour_combo.setCurrentIndex(max(0, self.colour_combo.findData(values.get("colour", "normal"))))
            self.tint_box.setChecked(bool(values.get("tint_elements", False)))
        finally:
            self.filling = filling
        on = spec is not None
        shown = on and state is not None and not state.get("missing")
        for widget in (self.elements_box, self.opacity, self.colour_combo):
            widget.setEnabled(on)
        self.tint_box.setEnabled(on and (spec or {}).get("colour", "normal") != "normal")
        # a disabled control says why (v0.47's rule, tests/test_window.py)
        self.elements_box.setToolTip("" if on else self.w("need_plan"))
        self.colour_combo.setToolTip("" if on else self.w("need_plan"))
        self.tint_box.setToolTip("" if self.tint_box.isEnabled() else self.w("need_colour" if on else "need_plan"))
        self.align_button.setEnabled(shown)
        self.reset_button.setEnabled(shown and "offset" in (self.tab.source.get("superposition") or {}))
        if on and (state is None or state.get("missing")):
            note = self.w("missing", plan=spec["plan"])
        elif shown and not state.get("scaled"):
            note = self.w("unscaled")
        else:
            note = ""
        self.state_note.setText(note)
        self.state_note.setVisible(bool(note))

    # -- what the controls write --

    def write(self, change):
        """`change(spec)` applied to the open plan's superposition, through the tab's edit: one step of «Annuler»."""
        if self.filling:
            return

        def apply():
            spec = self.tab.source.get("superposition")
            if isinstance(spec, dict):
                change(spec)
        self.tab.edit(apply)

    def on_plan(self, _index=None):
        if self.filling:
            return
        pid = self.plan_combo.currentData() or ""
        if not pid:
            self.tab.edit(lambda: self.tab.source.pop("superposition", None))
            return
        old = self.tab.source.get("superposition")
        spec = {key: value for key, value in (old if isinstance(old, dict) else model.SUPERPOSITION_DEFAULT).items() if key not in ("plan", "offset")}
        spec = {"plan": pid, **spec}
        offset = self.default_offset(pid)
        if offset is not None:
            spec["offset"] = offset
        self.tab.edit(lambda: self.tab.source.__setitem__("superposition", spec))

    def on_elements(self, checked):
        self.write(lambda spec: spec.__setitem__("elements", bool(checked)))

    def on_opacity(self, value):
        self.write(lambda spec: spec.__setitem__("opacity", round(value / 100, 2)))

    def on_colour(self, _index=None):
        colour = self.colour_combo.currentData() or "normal"
        self.write(lambda spec: spec.__setitem__("colour", colour))

    def on_tint(self, checked):
        self.write(lambda spec: spec.__setitem__("tint_elements", bool(checked)))

    def reset_alignment(self):
        spec = model.superposition_of(self.tab.source)
        offset = self.default_offset(spec["plan"]) if spec else None
        if offset is not None:
            self.write(lambda s: s.__setitem__("offset", offset))

    def start_align(self):
        """«Aligner…»: the canvas's two clicks (plan_canvas.ALIGN_TOOL), its button in no tool bar; the hint says which click is next."""
        self.canvas.set_tool(plan_canvas.ALIGN_TOOL)
        self.tab.mark_tool(plan_canvas.ALIGN_TOOL)
        self.on_align_step(1)
        self.canvas.setFocus()

    def on_align_step(self, step):
        hint = getattr(self.tab, "hint", None)
        if hint is not None and step in (1, 2):
            hint.setText(self.w(f"align_{step}"))


def install(tab):
    """The module made for `tab` and put in its right pane right after «Taille des symboles», shown while nothing is selected on the plan."""
    module = SuperpositionModule(tab)
    tab.insert_module(module.card, after=tab.style_group, when="plan")
    return module
