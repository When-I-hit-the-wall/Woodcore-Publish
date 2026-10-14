"""What an object editor is given to work with -- the categories, the plans, the fire plans, the excerpts and the variables it may offer, the bibliography, the context the host hands every pane -- and the dialog that picks a variable: split out of calc/tools/object_panes.py (issue #30), moved verbatim. object_panes.py imports every name back.
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
import typst_objects as objects  # the models the panes edit (calc/typst_objects.py)
import validation
from i18n import strings as glossary  # the engine's words: a category of Tabelle 8 in the window's language
from norms import norms as catalogue  # the documents the engine can name in full (calc/norms/norms.json)
from norms import sia261  # Tabelle 8, where the project has no export yet
from object_panes_words import ERROR_WORDS, NNBSP, REASON_WORDS, STRINGS, _DE, _EN, _FR, _french, text  # split out of this module (issue #30): every name it had is still importable from it


LANGUAGES = ("de", "fr", "en")


@dataclass(frozen=True)
class Category:
    """One category of SIA 261 Tabelle 8 as a drop-down offers it: its id, its name and its example in the window's language, and its two characteristic values -- None where the norm gives none (category E, 8.2.2)."""
    id: str
    name: str
    q_k: object = None
    Q_k: object = None
    example: str = ""

    @property
    def label(self):
        return f"{self.id} — {self.name}"


@dataclass(frozen=True)
class PlanInfo:
    """A position plan of the project: its id, its label, and the positions drawn on it, which a halo may be set under."""
    id: str
    label: str = ""
    positions: tuple = ()


@dataclass(frozen=True)
class FirePlanInfo:
    """A fire-protection plan of the project (v0.115): its id and its description."""
    id: str
    label: str = ""


@dataclass(frozen=True)
class ExcerptInfo:
    """An excerpt of the project's annexes (v0.115): its id, its name, the name of its source and the page it is taken from, and whether the export found it in its source -- one it did not stops the report, so the pane says so."""
    id: str
    name: str = ""
    source: str = ""
    page: int = 0
    resolved: bool = True

    @property
    def label(self):
        return f"{self.id} — {self.name}" if self.name else self.id


@dataclass(frozen=True)
class VariableChoice:
    """One variable the picker offers: its name -- what a call writes --, the domain it is read in (None for the report's own, a string for a var-domain of the report, a pair for a calculation of the export and its instance), the symbol the page prints, its label, value and unit."""
    name: str
    domain: object = None
    symbol: str = ""
    label: str = ""
    value: object = None
    unit: str = ""
    kind: str = "report"   # "report" or "calculation"

    def cell(self):
        """The content a cell holds for this variable: `[#doc-value(...)]`."""
        return objects.variable_cell(self.name, self.domain)

    @property
    def domain_text(self):
        if self.domain is None or self.domain == "":
            return ""
        return self.domain if isinstance(self.domain, str) else " / ".join(self.domain)

    @property
    def value_text(self):
        return fmt_value(self.value)

    def matches(self, words):
        haystack = " ".join(str(part).lower() for part in (self.name, self.symbol, self.label, self.domain_text, self.unit, self.value_text))
        return all(word in haystack for word in words)


def fmt_value(value, digits=3):
    """A value the way the window lists it: a number to at most `digits` decimals with no trailing zero, a word as it is."""
    if isinstance(value, bool) or value is None:
        return "" if value is None else str(value)
    if isinstance(value, (int, float)):
        if isinstance(value, float):
            shown = f"{value:.{digits}f}".rstrip("0").rstrip(".")
            return shown if shown not in ("", "-0") else "0"
        return str(value)
    return str(value)


_BIB_ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")


_BIB_TITLE = re.compile(r"title\s*=\s*[{\"]([^}\"]*)[}\"]", re.IGNORECASE)


def bib_entries(path):
    """[(key, title)] of the entries of a BibTeX file, best effort and in order: what a list to pick from needs. [] for a file that is not there or cannot be read."""
    try:
        source = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError, TypeError):
        return []
    found, seen = [], set()
    matches = list(_BIB_ENTRY.finditer(source))
    for n, match in enumerate(matches):
        if match.group(1).lower() in ("comment", "string", "preamble") or match.group(2) in seen:
            continue
        chunk = source[match.end():matches[n + 1].start() if n + 1 < len(matches) else len(source)]
        title = _BIB_TITLE.search(chunk)
        seen.add(match.group(2))
        found.append((match.group(2), " ".join(title.group(1).split()) if title else ""))
    return found


class PaneContext:
    """What the panes read from the window and the project, each piece replaceable by an explicit value.

    `lang` the window's language; `here` the project (a `calc/project.py` Project) -- from which the live-load categories (data/calculations.json of its export, else SIA 261 Tabelle 8), the plans (data/plans.json), the norms catalogue and `references.bib`, the pictures' folder and the variables of the export are read; `registry` the compiled report's variables (a `calc/variables.py` Registry) -- or None while it has not been read. `categories`, `plans`, `norm_groups`, `variables`, `images_dir` and `root` replace what would be read from `here`. `pick_variable(parent)` and `choose_image(parent)` replace the two dialogs: each returns the engineer's choice -- a `VariableChoice`, a path from the project's folder -- or None.
    """

    def __init__(self, lang="en", here=None, registry=None, categories=None, plans=None, norm_groups=None, variables=None,
                 images_dir=None, root=None, pick_variable=None, choose_image=None, excerpts=None, fire_plans=None):
        self._lang = lang if lang in LANGUAGES else "en"
        self.here = here
        self.registry = registry
        # what was handed over is kept as it is; what is read from the project is read again where the language it is named in changes
        self._given = {"categories": categories is not None, "norm_groups": norm_groups is not None, "variables": variables is not None, "plans": plans is not None, "excerpts": excerpts is not None, "fire_plans": fire_plans is not None}
        self._categories = self._as_categories(categories) if categories is not None else None
        self._plans = self._as_plans(plans) if plans is not None else None
        self._excerpts = self._as_excerpts(excerpts) if excerpts is not None else None
        self._fire_plans = self._as_fire_plans(fire_plans) if fire_plans is not None else None
        self._norm_groups = norm_groups
        self._variables = self._as_variables(variables) if variables is not None else None
        self._images_dir = images_dir
        self._root = root
        self._pick_variable = pick_variable
        self._choose_image = choose_image

    @classmethod
    def from_project(cls, here, lang="en", registry=None, **replace):
        return cls(lang=lang, here=here, registry=registry, **replace)

    def set_registry(self, registry):
        """The compiled report's variables, read again: what the picker offers is made again at the next ask."""
        self.registry = registry
        if not self._given["variables"]:
            self._variables = None

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, lang):
        lang = lang if lang in LANGUAGES else "en"
        if lang != self._lang:
            self._lang = lang
            # the names of the categories and the titles of the norms are in the window's language
            if not self._given["categories"]:
                self._categories = None
            if not self._given["norm_groups"]:
                self._norm_groups = None

    def reset(self):
        """What was read from the project is read again at the next ask -- the export was written, a plan saved."""
        if self.here is not None:
            if not self._given["plans"]:
                self._plans = None
            if not self._given["excerpts"]:
                self._excerpts = None
            if not self._given["fire_plans"]:
                self._fire_plans = None
            if not self._given["variables"]:
                self._variables = None
            if not self._given["categories"]:
                self._categories = None
            if not self._given["norm_groups"]:
                self._norm_groups = None

    # -- the live-load categories

    @staticmethod
    def _as_categories(found):
        out = []
        for item in found:
            out.append(item if isinstance(item, Category) else Category(item["id"], item.get("name", ""), item.get("q_k"), item.get("Q_k"), item.get("example", "")))
        return out

    def _calculation(self, domain):
        """A domain of data/calculations.json, or {} where the project has no export."""
        if self.here is None:
            return {}
        path = Path(self.here.data_dir) / "calculations.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return (data.get("domains") or {}).get(domain) or {}

    def categories(self):
        """The categories of SIA 261 Tabelle 8, in the norm's order, named in the window's language, with their values as the export carries them -- else as the norm's own file does."""
        if self._categories is not None:
            return list(self._categories)
        found = []
        instances = self._calculation("live-load").get("instances") or {}
        for key, instance in instances.items():
            variables = instance.get("vars") or {}
            found.append(Category(
                key,
                self._word((variables.get("nutzflaeche") or {}).get("value", "")),
                (variables.get("q_k") or {}).get("value"),
                (variables.get("Q_k") or {}).get("value"),
                self._word((variables.get("beispiel") or {}).get("value", "")),
            ))
        if not found:
            try:
                rows = sia261.table_8()["categories"]
            except validation.ValidationError:
                rows = []
            found = [Category(r["id"], self._word(r["nutzflaeche"]), r["q_k"], r["Q_k"], self._word(r.get("beispiel") or "")) for r in rows]
        self._categories = found
        return list(found)

    def category(self, category_id):
        return next((c for c in self.categories() if c.id == category_id), None)

    def _word(self, german):
        return glossary.translate(str(german), self.lang) if german else ""

    # -- the plans

    @staticmethod
    def _as_plans(found):
        out = []
        for item in found:
            if isinstance(item, PlanInfo):
                out.append(item)
            else:
                out.append(PlanInfo(item["id"], item.get("label", ""), tuple(item.get("positions", ()))))
        return out

    def plans(self):
        """The position plans of the project, with the positions each draws."""
        if self._plans is not None:
            return list(self._plans)
        found = []
        if self.here is not None:
            try:
                data = json.loads((Path(self.here.data_dir) / "plans.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            for key, plan in (data.get("plans") or {}).items():
                positions = []
                for element in plan.get("elements") or []:
                    label = element.get("label")
                    if label and label not in positions:
                        positions.append(label)
                found.append(PlanInfo(key, plan.get("label", ""), tuple(sorted(positions))))
        self._plans = found
        return list(found)

    def plan(self, plan_id):
        return next((p for p in self.plans() if p.id == plan_id), None)

    # -- the fire-protection plans (v0.115)

    @staticmethod
    def _as_fire_plans(found):
        return [item if isinstance(item, FirePlanInfo) else FirePlanInfo(item["id"], item.get("label", "")) for item in found]

    def fire_plans(self):
        """The fire-protection plans of the project, as the export holds them (data/fire.json): the ones a `doc-fire-plan` may name."""
        if self._fire_plans is not None:
            return list(self._fire_plans)
        found = []
        if self.here is not None:
            try:
                data = json.loads((Path(self.here.data_dir) / "fire.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            for key, plan in (data.get("plans") or {}).items():
                found.append(FirePlanInfo(key, plan.get("label", "")))
        self._fire_plans = found
        return list(found)

    def fire_plan(self, plan_id):
        return next((p for p in self.fire_plans() if p.id == plan_id), None)

    # -- the excerpts of the annexes (v0.115)

    @staticmethod
    def _as_excerpts(found):
        out = []
        for item in found:
            if isinstance(item, ExcerptInfo):
                out.append(item)
            else:
                out.append(ExcerptInfo(item["id"], item.get("name", ""), item.get("source", ""), item.get("page") or 0, item.get("resolved", True)))
        return out

    def excerpts(self):
        """The excerpts of the project's annexes, as the export holds them (data/annexes.json): the ones a `doc-extract` may name."""
        if self._excerpts is not None:
            return list(self._excerpts)
        found = []
        if self.here is not None:
            try:
                data = json.loads((Path(self.here.data_dir) / "annexes.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            sources = data.get("sources") or {}
            for key, excerpt in (data.get("excerpts") or {}).items():
                source = sources.get(excerpt.get("source", ""), {})
                found.append(ExcerptInfo(key, excerpt.get("name", "") or excerpt.get("label", ""), source.get("name", "") or excerpt.get("source", ""),
                                         excerpt.get("page") or 0, bool(excerpt.get("resolved"))))
        self._excerpts = found
        return list(found)

    def excerpt(self, excerpt_id):
        return next((e for e in self.excerpts() if e.id == excerpt_id), None)

    # -- the norms

    def norm_groups(self):
        """The documents a list can name: {group: [{key, label, tip}]} -- `norm` and `literature` from the catalogue (designation — title in the window's language), `bib` from the project's own references.bib, a catalogue entry the project's file shadows left out."""
        if self._norm_groups is not None:
            return self._norm_groups
        bib = bib_entries(self.here.references_bib) if self.here is not None else []
        shadowed = {key for key, _title in bib}
        groups = {"norm": [], "literature": [], "bib": []}
        try:
            records = catalogue.references()
        except validation.ValidationError:
            records = []
        for record in records:
            if record["key"] in shadowed or shadowed & set(record["aliases"]):
                continue
            title = catalogue.text(record, "title", self.lang)
            publisher = catalogue.text(record, "publisher", self.lang)
            tip = " — ".join(part for part in (record["edition"], publisher) if part)
            groups[record["kind"]].append({"key": record["key"], "aliases": list(record["aliases"]), "label": f"{record['designation']} — {title}", "tip": tip})
        for key, title in bib:
            groups["bib"].append({"key": key, "aliases": [], "label": f"{key} — {title}" if title else key, "tip": ""})
        self._norm_groups = groups
        return groups

    def norm_key(self, cited):
        """The key of the catalogue entry a string a call cites names -- by its key or one of its aliases -- or None."""
        for entries in self.norm_groups().values():
            for entry in entries:
                if cited == entry["key"] or cited in entry.get("aliases", ()):
                    return entry["key"]
        return None

    # -- the variables

    @staticmethod
    def _as_variables(found):
        out = []
        for item in found:
            if isinstance(item, VariableChoice):
                out.append(item)
            else:
                out.append(VariableChoice(item["name"], item.get("domain"), item.get("symbol", ""), item.get("label", ""), item.get("value"), item.get("unit", ""), item.get("kind", "report")))
        return out

    def variables(self):
        """Every variable the picker offers: those of the compiled report (a domain of the report, or none for its own) and those of the export's calculations, each with the domain a `doc-value` call reads it in."""
        if self._variables is not None:
            return list(self._variables)
        found = []
        if self.registry is not None:
            for var in self.registry.variables():
                found.append(VariableChoice(var.key, var.domain or None, var.symbol, var.label, var.value, var.unit, "report"))
        if self.here is not None:
            try:
                data = json.loads((Path(self.here.data_dir) / "calculations.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            for domain, body in (data.get("domains") or {}).items():
                for instance, record in (body.get("instances") or {}).items():
                    for key, var in (record.get("vars") or {}).items():
                        found.append(VariableChoice(key, (domain, instance), var.get("symbol", ""), var.get("label", ""), var.get("value"), var.get("unit", ""), "calculation"))
        self._variables = found
        return list(found)

    def variable_info(self, name, domain):
        """The variable a cell names, or None where the context does not list it."""
        wanted = tuple(domain) if isinstance(domain, (list, tuple)) else domain
        for var in self.variables():
            same = tuple(var.domain) if isinstance(var.domain, (list, tuple)) else var.domain
            if var.name == name and (same or None) == (wanted or None):
                return var
        return None

    # -- the two dialogs

    def pick_variable(self, parent=None):
        """The variable the engineer chooses, a `VariableChoice`, or None."""
        if self._pick_variable is not None:
            return self._pick_variable(parent)
        return VariableDialog.choose(self, parent)

    @property
    def root(self):
        """The folder a picture's path is written from: the project's Typst root."""
        if self._root is not None:
            return Path(self._root)
        return Path(self.here.typst_root) if self.here is not None else None

    @property
    def images_dir(self):
        if self._images_dir is not None:
            return Path(self._images_dir)
        return Path(self.here.images_dir) if self.here is not None else None

    def choose_image(self, parent=None):
        """The picture the engineer chooses, as a path from the project's folder with `/`; None where he cancels, '' where the file lies outside the folder (which the pane says)."""
        if self._choose_image is not None:
            return self._choose_image(parent)
        start = self.images_dir if self.images_dir is not None and self.images_dir.is_dir() else self.root
        chosen, _filter = QFileDialog.getOpenFileName(parent, text("op_image", self.lang), str(start or ""), "Images (*.png *.jpg *.jpeg *.gif *.svg *.webp *.pdf)")
        if not chosen:
            return None
        found = self.relative(chosen)
        return found if found is not None else ""

    def relative(self, path):
        """`path` as a path from the project's folder, or None where it lies outside it (said by the caller)."""
        if self.root is None:
            return Path(path).as_posix()
        try:
            return Path(path).resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return None


class VariableDialog(QDialog):
    """The variables a cell may name, filtered by what is typed -- every word, in any order, against the name, the symbol, the label, the domain, the unit and the value -- and chosen by a double click or «Insérer»."""

    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle(text("op_var_title", context.lang))
        self.choices = context.variables()
        self.chosen = None
        box = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText(text("op_var_search", context.lang))
        self.search.textChanged.connect(self.filter)
        box.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setRootIsDecorated(False)
        self.tree.setHeaderLabels([text("op_var_name", context.lang), text("op_var_value", context.lang), text("op_var_domain", context.lang)])
        self.tree.itemDoubleClicked.connect(lambda *_: self.accept())
        box.addWidget(self.tree)
        self.note = cards.note(text("op_var_none", context.lang))
        self.note.setVisible(not self.choices)
        box.addWidget(self.note)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(text("op_var_insert", context.lang))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        box.addWidget(self.buttons)
        self.resize(520, 420)
        self.filter("")

    def filter(self, words):
        shown = [c for c in self.choices if c.matches(str(words).lower().split())]
        self.tree.clear()
        for choice in shown:
            domain = choice.domain_text or text("op_var_report", self.context.lang)
            item = QTreeWidgetItem([choice.name, (choice.value_text + " " + choice.unit).strip(), domain])
            item.setData(0, Qt.ItemDataRole.UserRole, choice)
            if choice.label:
                item.setToolTip(0, choice.label)
            self.tree.addTopLevelItem(item)
        if shown:
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def select(self, row):
        """The row `row` of what is listed, chosen -- what a double click on it does before it closes the dialog."""
        self.tree.setCurrentItem(self.tree.topLevelItem(row))

    def accept(self):
        item = self.tree.currentItem()
        self.chosen = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        super().accept()

    @classmethod
    def choose(cls, context, parent=None):
        dialog = cls(context, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.chosen
        return None
