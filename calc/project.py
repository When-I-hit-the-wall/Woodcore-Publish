"""Where the program is, and where the project it works on is (Woodcore, docs/architecture/layout.md §11).

Two roots, kept apart since v0.81. The PROGRAM -- calc/, lib/, schemas/, examples/ -- is found from this file, or, once frozen by PyInstaller, from the folder the executable unpacks it into. The PROJECT -- the workbooks, the report, what Woodcore's window draws, what the export writes -- is found from its `.woodcore` file, which may sit in any folder. Until v0.80 every module derived both from its own `__file__`, which tied one copy of the code to one project.

One process works on one project. An entry point names it once, with `use()`, before anything asks for a path; every module then asks `current()` at the moment it needs one, never at import, so nothing is fixed before the project is known. A process that names none gets the project `WOODCORE_PROJECT` points at, else the one `.woodcore` beside the code's own checkout (`checkout_project`).

The engine a project's report compiles with is the program's, copied into the project beside its export (`sync_engine`, v0.81), and what produced an export is written beside it (`record`, data/project.json, v0.82): the program's version and revision, Typst's version and the workbooks' hashes -- what the one git repository proved until the code and the project came apart.

A project is laid out in one of two ways, and its .woodcore says which (the engineer's request of 30.09.2026). **As one report**, the way every project was laid out until then and the way DEFAULT_LAYOUT still lays one out: the report's folder is the Typst root, and the export, the pictures and the report's config.typ lie inside it. **In three documents** -- the convention d'utilisation, the base de projet and the rapport de statique, which is the report and keeps every name it had (MODES) -- where the project's own folder is the Typst root and holds what the three share: config.typ, commands.typ, references.bib, Images/ and the export. The second is recognised by `layout.typst_root` and by nothing else, so a project whose file states none is read, and compiled, exactly as before (`Project.has_modes`); the names the three documents are given in each language are calc/documents.py's.
"""

import contextlib
import difflib
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import proc
import validation

# The program's version: what a project's engine copy and its export record, and what lets a program refuse a project a newer one wrote.
VERSION = "0.118.0"

EXTENSION = ".woodcore"
FORMAT = "woodcore-project"
SCHEMA_VERSION = "1.0"
# An environment variable naming the project, for a process started without an argument -- the tests' subprocesses, a script.
ENV = "WOODCORE_PROJECT"

# What a project file may say about the project besides its name: what the report's title page and the PDF's metadata print (v0.82). Each optional, and empty where the file leaves it out.
DETAILS = ("number", "client", "address", "company", "author", "checker")

# The Woodcore version a project asks to be opened with, where it asks for one: the launcher starts the newest installed version whose number begins with it (packaging/launcher.py, v0.83). Optional; absent, the newest installed version opens it.
PIN_KEY = "woodcore_version"

# What the window keeps in the project file rather than in the user's settings (v0.83): the folders of the editor tabs that hold nothing -- a folder is a property of the project's sources, and until v0.83 one project's empty folders showed in every other. `gui` since v0.96, the window having been the Katalog until then.
GUI_KEY = "gui"
# GUI_KEY's name in a project file written before v0.96, still read: the first time the window writes its folders it writes GUI_KEY and takes this one out, so a project is migrated by being used and never by a pass over it.
KATALOG_KEY = "katalog"


def _program_root():
    """The program's folder while the code runs from its sources (000-Python/, Woodcore/ once moved); the folder PyInstaller unpacked it into once frozen."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


# The program: fixed for the life of the process, so these are constants.
APP_ROOT = _program_root()
CALC_DIR = APP_ROOT / "calc"
LIB_DIR = APP_ROOT / "lib"
EXPORT_SCRIPT = CALC_DIR / "export_all.py"

# Where each part of a project is, relative to its folder, when its .woodcore does not say: the layout a new project is created with. Each value is also a key of schemas/woodcore-project.schema.json's `layout`. The PDF is written beside its `.typ`, in the report's own folder, which is the Typst root and where Tinymist writes it by default (the engineer's request, v0.87); until then it was written one level above, at the top of the project folder, and a project whose .woodcore states `layout.pdf` keeps its own.
DEFAULT_LAYOUT = {
    "report": "Statischer Bericht (typst)/Statischer Rapport.typ",
    "pdf": "Statischer Bericht (typst)/Statischer Rapport.pdf",
    "sources": "Woodcore-Datei",
    "generated": "Statischer Bericht (typst)/_woodcore",
    "archives": "_Archiv",
}

# The three documents a project may be written as (the engineer's request of 30.09.2026), in the order the window offers them and their folders are numbered: the convention d'utilisation (Nutzungsvereinbarung, SIA 260's service criteria agreement), the base de projet (Projektbasis, basis of design) and the rapport de statique -- the report every project has had, which nothing renames and which is simply the third. What each is called is calc/documents.py's.
MODES = ("cu", "bp", "rs")
# The one document a project laid out as a report alone has: the report.
REPORT_ONLY = ("rs",)
# What a project laid out in three documents states beside DEFAULT_LAYOUT's keys -- **all of them or none**, which is what tells the two layouts apart (`Project.has_modes`): the Typst root, the pictures the three documents share, and the entry file and the PDF of the two documents the report is joined by. None of them has a default, so DEFAULT_LAYOUT is unchanged and a project that states none is read as it always was. The report keeps `report` and `pdf`, so every caller of `report_typ` and `report_pdf` goes on meaning the report. ⚠️ Until 0.117 a seventh, `rfem_export`, named the folder of the RFEM exports; the RFEM import was retired then (archive/rfem/), and a project that still states it is read with the key ignored and said (RETIRED_KEYS) -- a project made since states six, which a Woodcore older than 0.117 refuses by name: a one-way step, without a new schema_version (docs/decisions.md, «Retrait de RFEM»).
MODE_KEYS = ("typst_root", "images", "report_cu", "pdf_cu", "report_bp", "pdf_bp")
# Every key a project file's `layout` may state; each is also a key of schemas/woodcore-project.schema.json's `layout`, which tests/test_project.py holds.
LAYOUT_KEYS = tuple(DEFAULT_LAYOUT) + MODE_KEYS
# The order a layout in three documents is written in (full_layout): the root, then each document's entry and PDF in the order of MODES' folders, then what the three share -- the order a reader of the .woodcore looks for them in.
LAYOUT_ORDER = ("typst_root", "report", "pdf", "report_cu", "pdf_cu", "report_bp", "pdf_bp",
                "generated", "images", "sources", "archives")
# Each document's entry file and PDF, by the layout key that names them.
ENTRY_KEYS = {"cu": "report_cu", "bp": "report_bp", "rs": "report"}
PDF_KEYS = {"cu": "pdf_cu", "bp": "pdf_bp", "rs": "pdf"}
# Each document's revision journal, in `sources`: one per document, since each prints its own «Historique des versions» (the engineer's decision), the report's keeping the name it has had since v0.99 (docs/domain/journal.md §3.3terdecies).
JOURNAL_FILES = {"rs": "journal.json", "cu": "journal-cu.json", "bp": "journal-bp.json"}
# What the three documents share at the top of their Typst root, and what a report alone keeps in its own folder: the files a document's entry imports and the pictures and exports its sections read -- the same names in both layouts, only the folder they are in differs.
CONFIG_FILE = "config.typ"
COMMANDS_FILE = "commands.typ"
REFERENCES_FILE = "references.bib"
# The title page of the documents, plain Typst the engineer edits in VS Code: `title-page(document:)`, its rows taking the people of the .woodcore and the words it prints in the document's language. Shared by the three documents as config.typ is, and optional for a report alone, whose entry file may keep a title page of its own (a project created before the title page was a file of its own does).
TITLE_FILE = "title.typ"
# The folder of a project's Typst root that holds its **form**, the look of the three documents (calc/forms.py): `Template/template.typ`, the form's assets and its `form.json`. Shared by the three documents as config.typ and title.typ are, and kept wherever they are.
TEMPLATE_FOLDER = "Template"
IMAGES_FOLDER = "Images"
# The calculation domains written in the «Formule» tab, one `.typ` each, at the top of the Typst root -- the project's own folder in three documents, the report's in a report alone -- so that any document prints one with `#include "/Formules/<id>.typ"` (issue #15) and VS Code compiles what the tab wrote the moment it is written (v0.117, spec 2026-10-08-onglet-formule-domaines D-11; calc/domains/formula_domain.py).
FORMULAS_FOLDER = "Formules"
# The order, the nesting and the state of the sections of the convention d'utilisation and of the base de projet, one file in each document's folder; the report keeps its order in its own #include lines and has none.
STRUCTURE_FILE = "structure.json"
# Where a compile writes what it read, one record per document, so that a document whose Typst did not change since its PDF is not compiled again -- inside the export's folder, which the three share.
STAMPS_FOLDER = "stamps"

# The folders of `sources`, one per kind of thing Woodcore's window draws. `details/` and not `schemas/`, which is the contracts' own folder (docs/domain/detail-schemas.md §3.3decies). `annexes/` holds the documents the report draws on from outside and the excerpts it shows of them, in two sub-folders of its own, `sources/` and `excerpts/` (docs/domain/annexes.md §3.3undevicies, v0.115). `fire/` holds the fire-protection plans, one file per plan, as `plans/` holds the position plans they may follow (domains/fire.py). `checks/` holds the member checks, one file per check, the arrangement of `connectors/` (domains/member_check.py, v0.117). `loads/` holds the loads entered in Woodcore, one sub-folder per domain -- `dead/`, `snow/`, `wind/` -- and one file per case (registry.SOURCE_MODULES, issues #35-#37).
SOURCE_FOLDERS = ("connectors", "connections", "plans", "statics", "details", "scripts", "annexes", "fire", "checks", "loads", "profiles", "steel")

# What a project file may still carry of a feature Woodcore no longer has, by (section, key), with what the warning says of it (v0.117). Such a key is **read and ignored, and said at every export** (`Project.retired_keys`): a missing input warns and never stops, and the file is the engineer's, which Woodcore does not rewrite to take a key out -- he removes it when he chooses, and the warning stops then. The RFEM import was retired in 0.117 (archive/rfem/, docs/decisions.md «Retrait de RFEM»).
RETIRED_KEYS = {
    ("gui", "rfem_models"): "the RFEM import was retired in 0.117 (archive/rfem/): the exports it names are no longer read",
    ("layout", "rfem_export"): "the RFEM import was retired in 0.117 (archive/rfem/): the folder it names is no longer read and stays as it is",
}


class ProjectError(validation.ValidationError):
    """A project file that cannot be read, or that points outside its own folder -- an input defect, reported like any other (export_all prints it and exits 1)."""


class EngineDecision(ProjectError):
    """The project's copy of the engine is not one to replace without asking: another version wrote it, or it was edited by hand. `state` says which (`engine_state`)."""

    def __init__(self, state, message):
        super().__init__(message)
        self.state = state


class Project:
    """One project, read from its .woodcore file: every path the pipeline and the window read or write in it."""

    def __init__(self, file, data):
        self.file = Path(file).resolve()
        self.root = self.file.parent
        self.data = data
        self.layout = {**DEFAULT_LAYOUT, **data.get("layout", {})}
        for key in LAYOUT_KEYS:
            if key in self.layout:
                self._inside(key)
        stated = [key for key in MODE_KEYS if key in self.layout]
        if stated and len(stated) != len(MODE_KEYS):
            missing = ", ".join(f"layout.{key}" for key in MODE_KEYS if key not in self.layout)
            raise ProjectError(
                f"{self.file.name}: a project laid out in three documents states every one of "
                f"{', '.join(MODE_KEYS)} -- this one states {', '.join(stated)} and not {missing}"
            )
        if self.has_modes:
            self._check_documents()
        elif not _is_within(self.generated_dir, self.typst_root):
            raise ProjectError(
                f"{self.file.name}: layout.generated ({self.layout['generated']}) must lie inside the "
                f"report's folder ({self._rel(self.typst_root)}) -- the report reads the export through "
                f"the engine, and Typst reads nothing outside its root"
            )

    def _check_documents(self):
        """The rules of a layout in three documents, beyond every path lying inside the project's folder.

        **The Typst root is the project's own folder**, `layout.typst_root` being ".": the three documents share the config.typ, the commands.typ, the pictures and the export at its top, and a section imports them as `/commands.typ` whatever document it is in, which is what lets one section be shared between two documents. Every path of the layout lying inside the project's folder (`_inside`), the export, the pictures and the three entry files lie inside the Typst root by that alone -- the rule a report alone needs stated of its `generated` (above) holds here by construction.

        **Each document has a folder of its own**, below the project's: a document keeps its structure.json, its Sections/ and its PDF beside its entry file, so two documents in one folder would share them, and a document at the top of the project would put its sections among the files the three share.
        """
        if self._path("typst_root") != self.root:
            raise ProjectError(
                f"{self.file.name}: layout.typst_root ({self.layout['typst_root']}) must be \".\" -- the three "
                f"documents compile from the project's own folder, where the config.typ, the commands.typ and "
                f"the export they share lie"
            )
        seen = {}
        for mode in MODES:
            key = ENTRY_KEYS[mode]
            folder = self._path(key).parent
            if folder == self.root:
                raise ProjectError(
                    f"{self.file.name}: layout.{key} ({self.layout[key]}) lies at the top of the project -- each "
                    f"document has a folder of its own, beside the files the three share"
                )
            other = seen.get(os.path.normcase(str(folder)))
            if other is not None:
                raise ProjectError(
                    f"{self.file.name}: layout.{other} and layout.{key} are in one folder ({self._rel(folder)}) -- "
                    f"each document keeps its structure, its sections and its PDF in a folder of its own"
                )
            seen[os.path.normcase(str(folder))] = key

    @classmethod
    def load(cls, file):
        file = Path(file)
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ProjectError(f"{file}: no such project file") from None
        except (OSError, ValueError) as exc:
            raise ProjectError(f"{file}: cannot be read as a project file ({exc})") from None
        validation.validate_structure(data, "woodcore-project")
        return cls(file, data)

    def _inside(self, key):
        value = self.layout[key]
        if not isinstance(value, str) or not value.strip():
            raise ProjectError(f"{self.file.name}: layout.{key} must be a path relative to the project's folder")
        if not _is_within(self.root / value, self.root):
            raise ProjectError(
                f"{self.file.name}: layout.{key} ({value}) leaves the project's folder -- every part of a "
                f"project lies inside the folder its .woodcore file is in"
            )

    def _path(self, key):
        return (self.root / self.layout[key]).resolve()

    def _rel(self, path):
        try:
            return Path(path).relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def rel(self, path):
        """A path of this project as its folder sees it, for a message: `Statischer Bericht (typst)/_woodcore/data`."""
        return self._rel(Path(path).resolve())

    @property
    def name(self):
        return self.data.get("name") or self.file.stem

    def detail(self, key):
        """One of DETAILS as the project file states it, "" where it does not."""
        value = self.data.get(key)
        return value if isinstance(value, str) else ""

    def gui(self):
        """What the project file keeps of the window, {} where it keeps nothing: `gui`, else `katalog` in a file written before v0.96 (KATALOG_KEY)."""
        for key in (GUI_KEY, KATALOG_KEY):
            kept = self.data.get(key)
            if isinstance(kept, dict):
                return kept
        return {}

    def empty_folders(self, tab):
        """The folders editor tab `tab` holds nothing in, as the project file keeps them (v0.83) -- `gui.empty_folders.<tab>`, `katalog.empty_folders.<tab>` before v0.96."""
        folders = self.gui().get("empty_folders")
        names = folders.get(tab) if isinstance(folders, dict) else None
        return [name for name in names if isinstance(name, str) and name.strip()] if isinstance(names, list) else []

    def retired_keys(self):
        """What this project file still states of a feature Woodcore no longer has (RETIRED_KEYS), one `engine.Note` each, naming the key and why it is ignored -- for the export to warn of at every run and the window as the project opens. Nothing here reads what the key names: a retired key's paths are neither resolved nor checked, so one naming a file that is gone is no new stop."""
        import engine  # late: engine is the export's module, and a Project is read by the window before any export
        found = []
        for (section, key), why in RETIRED_KEYS.items():
            held = self.gui() if section == GUI_KEY else self.data.get(section)
            if isinstance(held, dict) and key in held:
                found.append(engine.Note("retired_key", f"{self.file.name}: {section}.{key} is ignored -- {why}; take it out of the project file to silence this", file=self.file.name, key=f"{section}.{key}"))
        return found

    def as_project_path(self, path):
        """`path` written as the project file keeps it: relative to the project's folder where it lies inside it, absolute where it does not."""
        path = Path(path).resolve()
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    # --- the report, and the documents beside it ------------------------------
    @property
    def has_modes(self):
        """True for a project laid out in three documents -- its .woodcore states `layout.typst_root`, and with it every one of MODE_KEYS -- and False for one laid out as a report alone, as every project was until the three documents and as DEFAULT_LAYOUT still lays one out."""
        return "typst_root" in self.layout

    @property
    def modes(self):
        """The documents this project is written as, in their order: MODES in three documents, the report alone (REPORT_ONLY) otherwise."""
        return MODES if self.has_modes else REPORT_ONLY

    def _document(self, mode):
        """`mode` if it is one of this project's documents -- else a ProjectError saying which it is not."""
        if mode not in MODES:
            raise ProjectError(f"unknown document {mode!r} -- expected one of {', '.join(MODES)}")
        if mode not in self.modes:
            raise ProjectError(
                f"{self.file.name} is laid out as one report and has no {mode} document -- a project in three "
                f"documents states layout.typst_root, and this one states none; migrate it to write the three"
            )
        return mode

    @property
    def report_typ(self):
        return self._path("report")

    @property
    def typst_root(self):
        """The folder Typst compiles from and reads nothing outside of: the project's own folder for a project in three documents (`layout.typst_root`, "."), the report's folder for a report alone -- which is also the folder Typst takes for its root when it is given none, so compiling it with `--root` changes nothing."""
        if self.has_modes:
            return self._path("typst_root")
        return self.report_typ.parent

    @property
    def report_pdf(self):
        return self._path("pdf")

    def document_typ(self, mode):
        """The entry file of document `mode` -- the report's own for "rs", which is `report_typ`."""
        return self._path(ENTRY_KEYS[self._document(mode)])

    def document_pdf(self, mode):
        """Where document `mode` is compiled to -- `report_pdf` for "rs". Beside its entry file in every layout Woodcore writes, as the report's has been since v0.87."""
        return self._path(PDF_KEYS[self._document(mode)])

    def document_dir(self, mode):
        """The folder of document `mode`: the folder its entry file lies in, where its sections, and for the convention d'utilisation and the base de projet its structure.json, lie beside it."""
        return self.document_typ(mode).parent

    def structure_file(self, mode):
        """The structure.json of document `mode` -- the order, the nesting and the state of its sections -- or None for the report, which keeps them in its #include lines."""
        if self._document(mode) == "rs":
            return None
        return self.document_dir(mode) / STRUCTURE_FILE

    # --- what the documents share -----------------------------------------------
    @property
    def config_typ(self):
        """The config.typ the documents are styled by: one at the top of the project for the three, the report's own for a report alone."""
        return self.typst_root / CONFIG_FILE

    @property
    def commands_typ(self):
        """The commands.typ every entry file and every section imports the engine through (docs/typst/api-conventions.md §10bis)."""
        return self.typst_root / COMMANDS_FILE

    @property
    def title_typ(self):
        """The title.typ every document's entry file sets its title page with, `#title-page(document: "cu")`: one at the top of the project for the three -- the engineer's to edit, never Woodcore's to rewrite -- and none in a report alone, whose entry keeps its own."""
        return self.typst_root / TITLE_FILE

    @property
    def references_bib(self):
        """The project's own references.bib, which `#show-bibliography(project: "references.bib")` reads from the Typst root (docs/typst/citations.md §10)."""
        return self.typst_root / REFERENCES_FILE

    @property
    def images_dir(self):
        """The pictures the documents' sections set: `layout.images`, shared by the three, else the report's own Images/."""
        if self.has_modes:
            return self._path("images")
        return self.typst_root / IMAGES_FOLDER

    @property
    def formulas_dir(self):
        """The calculation domains of the «Formule» tab: `Formules/` at the top of the Typst root, where every document reaches it as `/Formules/<id>.typ` (FORMULAS_FOLDER)."""
        return self.typst_root / FORMULAS_FOLDER

    # --- what the engineer enters -----------------------------------------------
    @property
    def positions_book(self):
        return self.root / "Positionen.xlsx"

    @property
    def sources_dir(self):
        return self._path("sources")

    @property
    def lists_file(self):
        """The order the engineer gives the window's lists, and the folders of the «Formules» tab (calc/list_order.py, issue #15): beside the sources he draws, never in the generated folder an export may rebuild."""
        return self.sources_dir / "lists.json"

    @property
    def building_file(self):
        """The building's data VKF / AEAI 15-15 reads the fire resistance of its load-bearing structure off -- height category, use, concept, storeys --, one file for the project, written by Woodcore's «Résistance au feu» tab and read by domains/member_check.py at the export (issue #46, schemas/fire-building.schema.json)."""
        return self.sources_dir / "building.json"

    @property
    def connectors_dir(self):
        return self.sources_dir / "connectors"

    @property
    def connections_dir(self):
        return self.sources_dir / "connections"

    @property
    def plans_dir(self):
        return self.sources_dir / "plans"

    @property
    def statics_dir(self):
        return self.sources_dir / "statics"

    @property
    def details_dir(self):
        return self.sources_dir / "details"

    @property
    def annexes_dir(self):
        return self.sources_dir / "annexes"

    @property
    def fire_dir(self):
        return self.sources_dir / "fire"

    @property
    def checks_dir(self):
        """The member checks, one source file each, written by Woodcore and resolved against the positions at the export (domains/member_check.py)."""
        return self.sources_dir / "checks"

    @property
    def profiles_dir(self):
        """The free steel profiles, one source file each -- rectangles drawn or typed in the «Profilés» tab, named by a position whose section type is USR (domains/profile.py, spec 2026-10-12-section-acier D-12)."""
        return self.sources_dir / "profiles"

    @property
    def steel_dir(self):
        """The steel checks and connections, one source file each, written by the «Acier» tabs and resolved against the positions and the profiles at the export (domains/steel_check.py, D-12)."""
        return self.sources_dir / "steel"

    @property
    def loads_dir(self):
        """The loads entered in Woodcore, `loads/dead`, `loads/snow`, `loads/wind`: one source file per case, computed at the export beside the sheets of a load workbook (registry.SOURCE_MODULES, issues #35-#37)."""
        return self.sources_dir / "loads"

    @property
    def journal_file(self):
        """The report's revision journal, one file for the whole project rather than a folder of them (calc/journal.py, docs/domain/journal.md §3.3terdecies): a journal is read as a whole and nothing addresses one revision by an id."""
        return self.sources_dir / JOURNAL_FILES["rs"]

    def journal_file_for(self, mode):
        """The revision journal of document `mode`, in the sources: `journal_file` for the report, journal-cu.json and journal-bp.json for the two documents beside it, each printing its own «Historique des versions»."""
        return self.sources_dir / JOURNAL_FILES[self._document(mode)]

    # --- what the export writes --------------------------------------------------
    @property
    def generated_dir(self):
        return self._path("generated")

    @property
    def data_dir(self):
        return self.generated_dir / "data"

    @property
    def docs_dir(self):
        return self.generated_dir / "docs"

    @property
    def stamps_dir(self):
        """What each compile of a document read, one record per document (STAMPS_FOLDER), which says whether its Typst changed since its PDF was written."""
        return self.generated_dir / STAMPS_FOLDER

    @property
    def archives_dir(self):
        return self._path("archives")

    def __repr__(self):
        return f"Project({str(self.file)!r})"


# --- the engine a project compiles with ---------------------------------------------

# The engine a project's report compiles with, copied into the project beside its export (docs/architecture/layout.md §11, v0.81): lib/'s three files, and the glossary lib/i18n.typ reads as `../calc/i18n/strings.json`. Typst reads nothing outside the report's folder, and the engine finds the export by the relative path `../data/`, so the copy sits in `generated`, beside data/ -- exactly the arrangement examples/ has used since v0.65.
ENGINE_FILES = ("lib/calc-engine.typ", "lib/formula.typ", "lib/i18n.typ", "calc/i18n/strings.json")
# lib/distance.typ and the norm tables it reads as `../calc/norms/<file>.json` (v0.87): the minimum distances of SIA 265, which `#distance` computes in the report from calc/norms/'s own files. tests/test_distance.py holds this list equal to the files lib/distance.typ names and calc/norms/sia265.py reads.
ENGINE_FILES += ("lib/distance.typ",) + tuple("calc/norms/%s.json" % name for name in (
    "sia265-2021-tab24-abstaende",
    "sia265-2021-tab27-holzdicken-naegel",
    "sia265-2021-tab28-abstaende-naegel",
    "sia265-2021-tab32-holzdicken-naegel-vorgebohrt",
    "sia265-2021-tab33-abstaende-naegel-vorgebohrt",
    "sia265-2021-tab36-holzdicken-schrauben",
    "sia265-2021-tab37-holzdicken-schrauben-vorgebohrt",
    "sia265-2021-tab38-abstaende-schrauben",
    "sia265-2021-tab39-abstaende-schrauben-vorgebohrt",
    "sia265-2021-tab40-abstaende-schrauben-axial",
    "sia265-2021-tab41-abstaende-ringduebel",
    "sia265-2021-6.2.1.1-k-alpha",
    "sia265-2021-6.4.1.1-nageldurchmesser",
    "sia265-2021-6.5.2.3.1-schraubendurchmesser",
))
# lib/timber.typ and the norm files it reads (v0.88): the member checks of SIA 265 4.2, which `#member` and the `verify-*` commands compute in the report -- the design values of Tabellen 8 and 9, eta_w and eta_t, Anhang B's Tabellen 47 and 48, and the constants of 3.4.2.3 and 4.2.6 to 4.2.9. tests/test_timber.py holds this list equal to the files lib/timber.typ names.
ENGINE_FILES += ("lib/timber.typ",) + tuple("calc/norms/%s.json" % name for name in (
    "sia265-2021-tab04-eta-w",
    "sia265-2021-2.2.6-eta-t",
    "sia265-2021-tab08-vollholz",
    "sia265-2021-tab09-brettschichtholz",
    "sia265-2021-tab47-druckfestigkeit-e005-vollholz",
    "sia265-2021-tab48-druckfestigkeit-e005-brettschichtholz",
    "sia265-2021-3.4.2.3-k-h",
    "sia265-2021-4.2.6-abscheren",
    "sia265-2021-4.2.7-schub-querdruck",
    "sia265-2021-4.2.8-knicken",
    "sia265-2021-4.2.9-kippen",
    "sia265-2021-4.5-brandfall",
))
# lib/bibliography.typ and the catalogue it reads (v0.99): the documents the engine can name in full, which `#show-bibliography` prints for every norm the report cites. calc/norms/norms.py checks the same file; tests/test_bibliography.py holds this pair equal to what lib/bibliography.typ names.
ENGINE_FILES += ("lib/bibliography.typ", "calc/norms/norms.json")
# lib/summary.typ (v0.99): the report's summary tables -- the area loads, the line loads and the main results, which `show-load-summary`, `show-line-load-summary` and `show-result-summary` gather from the export and from the registry. It reads no file of its own: the export it reads is already beside it, and the glossary it names is the one every other file of lib/ reads.
ENGINE_FILES += ("lib/summary.typ",)
# lib/steel.typ (issues #50-#52): the steel checks of the «Acier» tabs, printed as the export computed them -- it computes nothing and reads no norm file, data/steel.json carrying every value (spec 2026-10-12-section-acier D-09).
ENGINE_FILES += ("lib/steel.typ",)
# lib/document.typ (the three document modes, phase 3): the parametric objects of a project's documents -- the tables, the live loads and the non-structural self-weight, a field, a list to tick, a choice, a picture, a plan's extract, the signatures and the norms a section names. It reads no file of its own: the live loads come out of the export through `val`, and the norms out of norms.json through lib/bibliography.typ, both already beside it.
ENGINE_FILES += ("lib/document.typ",)
ENGINE_FILES += ("lib/sheet.typ", "lib/assets/logo-bfh.png")  # the export sheets (v0.114) and the logo of their title block -- copied as bytes by sync_engine
ENGINE_FILES += ("lib/units.json",)  # the units lib/formula.typ reads as `json("units.json")` and calc/units.py reads too (v0.117, ARCH-005): one table for the report and the «Formule» tab
ENGINE_FILES += ("lib/positions.typ",)  # the list of the positions (v0.116): `show-position-list`, and the table sheet.typ's `sheet-position-list` prints -- it reads the export beside it
ENGINE_FILES += ("lib/shown-variables.json",)  # what `level: -1, shown:` may name, command by command (v0.117, issue #20): lib/calc-engine.typ reads it as `json("shown-variables.json")`, calc/shown_variables.py for the window's boxes
ENGINE_STAMP = "VERSION"
# The states of engine_state an export replaces only once the engineer agrees: `--update-engine`, or the window's dialog (engine_consent).
ASKED = ("older", "edited", "unknown")


def _version_tuple(text):
    parts = []
    for piece in str(text).split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def engine_state(project):
    """How the project's copy of the engine stands against the program's, as (state, detail).

    own      -- the project's generated folder is the program's own folder, as when the code sat inside its project (until v0.82): nothing is copied there
    absent   -- no copy yet
    current  -- the program's engine, to the byte
    stale    -- another build of this same version (the code run from its sources, between two versions): replaced without asking
    older    -- written by an older version: replaced only once the engineer agrees, since the report may print otherwise
    newer    -- written by a newer version than this program: never replaced, the project must be opened with that one
    edited   -- a file of the copy is not the one its VERSION recorded: edited by hand, and never overwritten without asking
    unknown  -- engine files lie there and no VERSION names them: the code of a folder laid out before v0.81, converted (project_template.convert, v0.83) -- replaced only once the engineer agrees, as an older version's
    """
    target = project.generated_dir
    if target.resolve() == APP_ROOT.resolve():
        return "own", ""
    stamp_file = target / ENGINE_STAMP
    if not stamp_file.is_file():
        present = [name for name in ENGINE_FILES if (target / name).is_file()]
        return ("unknown", ", ".join(present)) if present else ("absent", "")
    try:
        stamp = json.loads(stamp_file.read_text(encoding="utf-8"))
        recorded, written_by = dict(stamp["files"]), str(stamp["version"])
    except (OSError, ValueError, KeyError, TypeError):
        return "edited", ENGINE_STAMP
    # The files the VERSION names are the ones checked: a file the engine gained since (lib/distance.typ and its norm tables, v0.87) is absent from an older copy by construction, which makes the copy older or stale, not edited.
    edited = []
    for name in recorded:
        path = target / name
        if not path.is_file() or _sha(path.read_bytes()) != recorded[name]:
            edited.append(name)
    if edited:
        return "edited", ", ".join(edited)
    if _version_tuple(written_by) > _version_tuple(VERSION):
        return "newer", written_by
    ours = {name: _sha((APP_ROOT / name).read_bytes()) for name in ENGINE_FILES}
    if ours == recorded:
        return "current", written_by
    if _version_tuple(written_by) < _version_tuple(VERSION):
        return "older", written_by
    return "stale", written_by


def engine_diff(project):
    """The differences between the project's copy of the engine and the program's, as a unified diff -- what «Voir la différence» shows before an edited copy is overwritten."""
    out = []
    for name in ENGINE_FILES:
        theirs = project.generated_dir / name
        ours = APP_ROOT / name
        a = theirs.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True) if theirs.is_file() else []
        b = ours.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        out += difflib.unified_diff(a, b, fromfile=f"project/{name}", tofile=f"Woodcore {VERSION}/{name}")
    return "".join(out)


def engine_message(state, detail):
    """The sentence a refusal to replace the copy says, in English like every message of the pipeline (the window writes its own)."""
    if state == "newer":
        return (f"this project's engine was written by Woodcore {detail}, newer than this program ({VERSION}) -- "
                f"open the project with that version, or a newer one")
    if state == "older":
        return (f"this project's engine was written by Woodcore {detail}; this program is {VERSION}, and its engine "
                f"may print the report otherwise -- export with --update-engine to replace it")
    if state == "unknown":
        return (f"this project carries an engine no VERSION names ({detail}), the code of a folder laid out before "
                f"Woodcore; this program's engine may print the report otherwise -- export with --update-engine to replace it")
    return (f"this project's copy of the engine was edited by hand ({detail}) -- export with --update-engine to "
            f"overwrite it, after carrying the change into the program if it is meant")


def sync_engine(project, update=False):
    """Copies the program's engine into `project`'s generated folder, and writes its VERSION: the program's version and each file's SHA-256. Returns the files written, relative to the generated folder.

    Nothing is copied into the program's own folder (`own`). A copy that is absent or another build of this version (`stale`) is replaced; one another version wrote (`older`), one edited by hand (`edited`) or one no VERSION names (`unknown`) only with `update`, else EngineDecision says which; one a newer program wrote (`newer`) never. The files are left read-only, which is what says they are not the place to edit the engine.
    """
    state, detail = engine_state(project)
    if state in ("own", "current"):
        return []
    if state == "newer" or (state in ASKED and not update):
        raise EngineDecision(state, engine_message(state, detail))
    target = project.generated_dir
    written, hashes = [], {}
    for name in ENGINE_FILES:
        data = (APP_ROOT / name).read_bytes()
        hashes[name] = _sha(data)
        path = target / name
        if not path.is_file() or path.read_bytes() != data:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                path.chmod(stat.S_IREAD | stat.S_IWRITE)
            path.write_bytes(data)
            written.append(name)
        path.chmod(stat.S_IREAD)
    stamp = json.dumps({"version": VERSION, "files": hashes}, indent=2) + "\n"
    version = target / ENGINE_STAMP
    if not version.is_file() or version.read_text(encoding="utf-8") != stamp:
        version.write_text(stamp, encoding="utf-8")
        written.append(ENGINE_STAMP)
    return written


# --- what produced an export ----------------------------------------------------------

def cli_command(args):
    """`woodcore-cli` with `args`, as a program and its arguments: `woodcore-cli.exe` beside `Woodcore.exe` once installed, `calc/cli.py` under a console interpreter from the sources (v0.100).

    The Qt-free route from anywhere in the program to the command line, which is what lets a part of the pipeline start a child process of its own -- a script of the project runs that way (calc/domains/script.py), and an installed Woodcore carries no `python.exe` to spawn, so it relaunches itself exactly as «Import donnees» does.

    ⚠️ `pythonw.exe` is swapped for the `python.exe` beside it: the window runs under the first, which has no console, and a child started from it must still be able to write to the pipes its parent reads. Woodcore's window has carried its own copy of this since v0.83 (`woodcore_gui.cli_command`), which adds nothing this one does not and is left where it is.
    """
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).with_name("woodcore-cli.exe")), list(args)
    runner = Path(sys.executable)
    if runner.name.lower() == "pythonw.exe" and runner.with_name("python.exe").is_file():
        runner = runner.with_name("python.exe")
    return str(runner), [str(CALC_DIR / "cli.py"), *args]


def typst_executable():
    """The Typst the report is compiled with: the one shipped beside a frozen program, else the one on PATH."""
    shipped = APP_ROOT / "typst.exe"
    if getattr(sys, "frozen", False) and shipped.is_file():
        return str(shipped)
    return shutil.which("typst") or "typst"


def typst_version():
    """`0.14.2`, or "" where no Typst answers."""
    try:
        out = proc.run([typst_executable(), "--version"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    words = out.split()
    return words[1] if len(words) > 1 else out.strip()


# What the build of a frozen program wrote beside it (packaging/build.py, v0.83): the version, the revision of the sources it was built from, when. Absent from a checkout, which asks git instead.
BUILD_INFO = "build-info.json"


def build_info():
    """The frozen program's build-info.json, or {} -- a checkout has none."""
    try:
        data = json.loads((APP_ROOT / BUILD_INFO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def source_revision():
    """The program's git revision -- `24106034`, `-dirty` appended while the tree has changes nobody committed: asked of git from a checkout, read from the build-info.json the build wrote once frozen (v0.83), and "" for a copy that has neither."""
    if getattr(sys, "frozen", False):
        return str(build_info().get("revision", ""))
    try:
        out = proc.run(["git", "-C", str(APP_ROOT), "describe", "--always", "--dirty", "--abbrev=8"],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def record(project, workbooks=(), revision=None):
    """data/project.json: the project as its file describes it, and what produced this export -- Woodcore's version and revision, Typst's version, and the SHA-256 of every workbook read. The report's title page and the PDF's metadata print from it (lib/calc-engine.typ, project-info), and the archive keeps it; no date, so an export repeated on the same inputs writes the same bytes.

    `revision` is the report's own latest revision, the newest entry of its journal (calc/journal.py, `latest`), which the PDF's keywords name -- `{index, date, label, initials}` or None where the journal is empty. It is passed IN rather than read here, so that this module knows nothing of the journal and `seed()` writes a record without one; and the date in it is the engineer's typed day, not a clock reading, so an unchanged journal still writes the same bytes.
    """
    books = {}
    for path in sorted({Path(p) for p in (project.positions_book, *workbooks)}, key=lambda p: p.name.lower()):
        if path.is_file():
            books[path.name] = _sha(path.read_bytes())
    info = {
        "schema_version": "1.0",
        "name": project.name,
        **{key: project.detail(key) for key in DETAILS},
        "woodcore": {"version": VERSION, "revision": source_revision()},
        "typst": typst_version(),
        "workbooks": books,
    }
    if revision is not None:
        info["revision"] = {key: revision[key] for key in ("index", "date", "label", "initials")}
    return info


# --- naming a project -----------------------------------------------------------------

def _is_within(path, folder):
    try:
        Path(path).resolve().relative_to(Path(folder).resolve())
    except ValueError:
        return False
    return True


def full_layout(layout):
    """`layout` as a project in three documents writes it: every key of LAYOUT_ORDER, each of DEFAULT_LAYOUT's it leaves out taking its default, in that order -- so the project's .woodcore says where every part of it lies and reads nothing from DEFAULT_LAYOUT (the engineer's rule: a new or migrated project states its layout, DEFAULT_LAYOUT being load-bearing for the projects that state none). A MODE_KEYS key it leaves out has no default and stays out, for `Project` to refuse by name; a key this module does not know is kept, after the others. A layout of a report alone, which states no `typst_root`, is given back as it is."""
    if "typst_root" not in layout:
        return dict(layout)
    full = {key: layout[key] if key in layout else DEFAULT_LAYOUT[key]
            for key in LAYOUT_ORDER if key in layout or key in DEFAULT_LAYOUT}
    full.update({key: value for key, value in layout.items() if key not in full})
    return full


def write(file, name, layout=None, **details):
    """Writes a project file: `name`, the DETAILS given, and `layout` -- a layout of a report alone as it is given, which its callers make what differs from DEFAULT_LAYOUT (templates.stated_layout), and a layout in three documents in full, every key stated (`full_layout`), whatever of it the caller left to the defaults. Returns the Project it describes."""
    data = {"schema_version": SCHEMA_VERSION, "format": FORMAT, "name": name}
    for key in DETAILS:
        if details.get(key):
            data[key] = details[key]
    if layout:
        data["layout"] = full_layout(layout)
    validation.validate_structure(data, "woodcore-project")
    project = Project(file, data)
    Path(file).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return project


def update(file, **changes):
    """Rewrites project file `file` with `changes` -- a key given None is taken out, every key not named is kept as it stands, `layout` and `gui` included -- and returns the Project it now describes. A `layout` given is the layout the file then states, whole, and one in three documents is written in full (`full_layout`), as `write` writes it. Written whole beside itself and then moved into place, so a file NextCloud syncs is never seen half-written; the current project is named again when it is the one rewritten, so the window reads what it just wrote."""
    global _current
    file = Path(file)
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ProjectError(f"{file}: no such project file") from None
    except (OSError, ValueError) as exc:
        raise ProjectError(f"{file}: cannot be read as a project file ({exc})") from None
    for key, value in changes.items():
        if value is None or value == "":
            data.pop(key, None)
        elif key == "layout" and isinstance(value, dict):
            data[key] = full_layout(value)
        else:
            data[key] = value
    validation.validate_structure(data, "woodcore-project")
    updated = Project(file, data)
    temporary = file.with_name(file.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, file)
    if _current is not None and _current.file == updated.file:
        _current = updated
    return updated


def set_empty_folders(here, tab, names):
    """Writes the folders editor tab `tab` holds nothing in into the project file (`gui.empty_folders.<tab>`), and only when they changed. Returns the Project as it now stands. A file written before v0.96 keeps them under `katalog`: what it holds is carried into `gui` and `katalog` taken out, so the project is migrated the first time its folders change."""
    names = [name for name in names if isinstance(name, str) and name.strip()]
    if here.empty_folders(tab) == names:
        return here
    gui = dict(here.gui())
    folders = {k: v for k, v in dict(gui.get("empty_folders") or {}).items() if v}
    if names:
        folders[tab] = names
    else:
        folders.pop(tab, None)
    if folders:
        gui["empty_folders"] = folders
    else:
        gui.pop("empty_folders", None)
    return update(here.file, **{GUI_KEY: gui or None, KATALOG_KEY: None})


_current = None


def use(project):
    """Names the project this process works on, a Project or the path of its .woodcore file, and returns it."""
    global _current
    _current = project if isinstance(project, Project) else Project.load(project)
    return _current


@contextlib.contextmanager
def using(project):
    """`use(project)` for the length of a `with` block, the project named before it put back after -- what a test works on a copy of a project with."""
    global _current
    before = _current
    try:
        yield use(project)
    finally:
        _current = before


def current():
    """The project this process works on: the one `use()` named, else `WOODCORE_PROJECT`'s, else the one beside the code's own checkout."""
    if _current is not None:
        return _current
    named = os.environ.get(ENV)
    if named:
        return use(named)
    beside = checkout_project()
    if beside is None:
        raise ProjectError(
            f"no project: open one with --project <file{EXTENSION}>, or name it in the {ENV} environment variable"
        )
    return use(beside)


def checkout_project():
    """The one project beside the code's own checkout, or None.

    It is looked for in the folders beside the program's -- `Musterprojekt/Musterprojekt.woodcore` next to `Woodcore/`, the layout the code and its projects share since v0.82. Until the move the program sat two levels inside its project and the file was looked for at the top of it; no checkout is laid out so any more. A frozen program has no checkout, and two files would be a choice nobody made, so both give None.
    """
    if getattr(sys, "frozen", False):
        return None
    found = set(APP_ROOT.parent.glob(f"*/*{EXTENSION}"))
    return sorted(found)[0] if len(found) == 1 else None


def take_argument(argv):
    """`--project <file>` out of an argument list: returns (the file or None, the arguments left)."""
    rest, file = [], None
    items = iter(argv)
    for arg in items:
        if arg == "--project":
            file = next(items, None)
            if file is None:
                raise ProjectError("--project needs the path of a .woodcore file")
        elif arg.startswith("--project="):
            file = arg.split("=", 1)[1]
        else:
            rest.append(arg)
    return file, rest
