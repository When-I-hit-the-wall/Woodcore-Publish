"""Project templates: what a new project is made from (docs/conventions/build-and-release.md §12, v0.94).

The engineer: «il doit être possible d'avoir différents templates (construction des fichiers, section, fichier config propre, langue, auteur par défaut, etc.)». A **template** is a folder: the skeleton of a project -- the report's folder with its `config.typ`, `commands.typ`, entry file and `Sections/*.typ`, `.vscode/`, anything else a new project starts with -- and a `template.json` at its top (schemas/template.schema.json) saying its name and description, the two languages a project made from it is written in (config.typ's `doc-lang`, and the default of `#set-report-language`), where its parts lie (the `layout` a `.woodcore` may state) and who the report is by by default (company, author, checker). A new project is the skeleton copied, `template.json` left out, and the languages written into the copy (calc/project_template.py).

Three places, each a folder of templates, one folder each:

* **builtin** -- `templates/` beside the program, read only: «Standard» (`templates/projet/`), what every project was made from until v0.94;
* **user** -- `%APPDATA%\\Woodcore\\templates\\` (usersettings.templates_dir), the engineer's own;
* **shared** -- a folder the settings name (`templates.shared_folder`), on NextCloud or a network drive: the office's.

A template is named `<place>:<folder>` -- `builtin:projet`, `user:Holzbau` -- which stays when its name is edited, so the default the settings name (`templates.default`) survives a rename. A template that states no language takes the settings' default report language (`defaults.report_language`), and its document is written in the report's language; one that states no company, author or checker is filled from the settings' defaults (`defaults.company` …) by whoever asks (`people_for`).

**A template has one of two shapes**, as a project has (calc/project.py). **Report-shaped**, which Standard is and stays on disk: the skeleton of a report alone, its config.typ, commands.typ, references.bib and pictures inside the report's folder, its layout stating no `typst_root`. **Documents-shaped**, which only «Enregistrer ce projet comme modèle» makes, from a project laid out in three documents: what the three share at its top and each document's folder, its layout stated in full, `typst_root` among it (`Template.has_modes`). A new project is laid out in three documents whichever shape its template has (calc/project_template.py): a report-shaped skeleton is laid out so as it is copied -- the shared files copied to the top, the report into its new folder, its paths rewritten (calc/typst_paths.py) and the two other documents made from their own templates (calc/doc_templates.py) -- and a documents-shaped one is copied as it stands, its three folders named as the engineer asks.

Qt-free: *Paramètres* in Woodcore's window (calc/tools/settings_dialog.py), the start page's *Nouveau projet* and `woodcore-cli new --template` all go through it.
"""

import json
import os
import re
import shutil
import unicodedata
from pathlib import Path, PurePosixPath

import documents
import project
import validation
import usersettings  # the engineer's settings and folders (calc/usersettings.py; calc/tools/ until v0.120, G6)

FILE = "template.json"
FORMAT = "woodcore-template"
SCHEMA_VERSION = "1.0"
PLACES = ("builtin", "user", "shared")
BUILTIN_DIR = project.APP_ROOT / "templates"
STANDARD = "builtin:projet"
LANGUAGES = ("de", "fr", "en")
DEFAULT_LANGUAGE = "de"
# The report folder's name a new project is created with, per language: what «Nouveau projet» offers and `woodcore-cli new --report-folder` takes (v0.100). The engineer: «Lors de la création d'un nouveau projet dans woodcore, le nom de ce dossier est demandé. Par défaut: "Rapport de statique" <- dépendant de la langue choisie», and «sans (typst)».
#
# ⚠️ The folder is named **once**, at creation, and the project's own `.woodcore` states where its report lies from then on (project_template.create). `project.DEFAULT_LAYOUT` therefore does **not** move: a project created before v0.100 states no `layout` at all -- the engineer's own Musterprojekt and tests/projet-exemple both state none -- and goes on reading «Statischer Bericht (typst)» from it. Renaming the constant would make the report folder of both unfindable at once, and nothing on disk is renamed in a project that already exists.
#
# Since the three documents a new project is laid out in (the engineer's request of 30.09.2026) the report's folder is the third of three, numbered and named in the project's language exactly as calc/documents.py writes them -- `3_Statischer Bericht`, `3_Rapport de statique`, `3_Statical report` -- and this is the report's word of those three (`folders_offered` gives all three), so that a caller still offering the one report folder offers the form the spec names.
# Since the project laid out by folders (issue #64) the three folders are the same in every language, `300-Statical report` for the report (calc/documents.py MODE_FOLDERS, D-07, D-14); the table keeps its languages so that every caller naming one goes on working.
REPORT_FOLDERS = {lang: documents.MODE_FOLDERS["rs"] for lang in LANGUAGES}
# The names Windows reserves for a device: a folder so named cannot be created whatever is asked for, so it is refused where the name is typed (check_report_folder).
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{n}" for n in range(1, 10)), *(f"LPT{n}" for n in range(1, 10))}
PEOPLE = ("company", "author", "checker")
# The layout keys a template's form edits; `generated` and `pdf` follow the report's folder unless template.json states them (layout_of).
EDITED_LAYOUT = ("report", "sources", "archives")
SECTIONS = "Sections"
# calc/project.py's names, named here once more for the callers of this module: the file a document is styled by, and the folder of pictures «Enregistrer ce projet comme modèle» keeps only where a .typ of the template names them (save_project) -- inside the report's folder for a report alone, at the top of the project for three documents.
CONFIG = project.CONFIG_FILE
IMAGES = project.IMAGES_FOLDER
# The record of what a document shares with the others (calc/sync.py `FILE`, held equal by tests/test_templates.py -- sync is not imported here): Woodcore's own file about **this project's copies**, never a template's -- a document made from the template has no copy of another document yet.
SYNC_FILE = "sync.json"

# `#let doc-lang = "de"` in config.typ, and `#set-report-language(sys.inputs.at("lang", default: "de"))` in the report's entry file: the two lines a template's languages are written into.
_DOC_LANG = re.compile(r'^([ \t]*#let[ \t]+doc-lang[ \t]*=[ \t]*")([A-Za-z-]*)(")', re.M)
_REPORT_LANG = re.compile(r'(set-report-language\(\s*sys\.inputs\.at\(\s*"lang"\s*,\s*default:\s*")([A-Za-z-]*)(")')
# `#include "Sections/002-grundlagen.typ"`, commented out or not: the lines the sections' order is written into (sync_includes).
_INCLUDE = re.compile(r'^([ \t]*(?://[ \t]*)?)#include[ \t]+"Sections/([^"/]+\.typ)"[ \t]*$')
_SECTION = re.compile(r"^(\d+)-(.*)\.typ$", re.I)


class TemplateError(project.ProjectError):
    """A template that cannot be read, used or written, said by name."""


def _read_text(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


# --- the settings a template is read against ---------------------------------------------

def _prefs(settings, key):
    value = (settings or {}).get(key)
    return value if isinstance(value, dict) else {}


def shared_folder(settings):
    """The office's templates, as the settings name them (`templates.shared_folder`), or None."""
    text = _prefs(settings, "templates").get("shared_folder")
    return Path(text) if isinstance(text, str) and text.strip() else None


def default_ref(settings):
    """The template «Nouveau projet» offers first: the settings' `templates.default`, else Standard."""
    ref = _prefs(settings, "templates").get("default")
    return ref if isinstance(ref, str) and ref.strip() else STANDARD


def defaults(settings):
    """The settings' own defaults for a new project (`defaults`): company, author, checker and report language, "" where none is set."""
    prefs = _prefs(settings, "defaults")
    out = {key: prefs.get(key) if isinstance(prefs.get(key), str) else "" for key in PEOPLE}
    language = prefs.get("report_language")
    out["report_language"] = language if language in LANGUAGES else ""
    return out


def place_dir(place, settings=None):
    """The folder of templates of `place`: builtin, user, or shared -- None for shared where the settings name no folder."""
    if place == "builtin":
        return BUILTIN_DIR
    if place == "user":
        return usersettings.templates_dir()
    if place == "shared":
        return shared_folder(settings if settings is not None else usersettings.read())
    raise TemplateError(f"unknown place of templates {place!r} -- expected one of {', '.join(PLACES)}")


# --- one template ---------------------------------------------------------------------------

def layout_of(meta):
    """Where the parts of a project made from a template lie: its `layout`, each key left out taking the default -- and `generated` and `pdf`, where the template moves the report but states neither, following the report into its folder (`_woodcore/` beside the entry file, the PDF named after it), as they do in the default layout.

    A documents-shaped template, whose layout states `typst_root`, states it in full as the project's .woodcore did, and is given it back as project.full_layout writes one: nothing follows anything there, every part being named. A key calc/project.py does not know (project.LAYOUT_KEYS) is left out in both shapes; one of the three documents' keys stated without `typst_root` is kept, for project.Project to refuse by name (`check`).
    """
    stated = meta.get("layout") if isinstance(meta.get("layout"), dict) else {}
    stated = {key: value for key, value in stated.items() if key in project.LAYOUT_KEYS}
    if "typst_root" in stated:
        return project.full_layout(stated)
    layout = dict(project.DEFAULT_LAYOUT)
    if isinstance(stated.get("report"), str) and stated["report"].strip():
        report = PurePosixPath(stated["report"].replace("\\", "/"))
        folder = report.parent.as_posix()
        prefix = "" if folder in ("", ".") else folder + "/"
        layout["generated"] = prefix + documents.LEGACY_GENERATED_FOLDER
        layout["pdf"] = prefix + report.stem + ".pdf"
    layout.update(stated)
    return layout


def stated_layout(layout):
    """What a `.woodcore` states of `layout` (project.write): for a report alone the keys that differ from the default layout, and nothing where it keeps the default one; for three documents the whole of it, as project.full_layout writes it -- a project so laid out reads nothing from DEFAULT_LAYOUT. Only the keys calc/project.py knows (project.LAYOUT_KEYS) in either."""
    known = {key: value for key, value in layout.items() if key in project.LAYOUT_KEYS}
    if "typst_root" in known:
        return project.full_layout(known)
    return {key: value for key, value in known.items() if project.DEFAULT_LAYOUT.get(key) != value}


def template_layout(layout):
    """What a template.json states of `layout`: stated_layout's keys, less `generated` and `pdf` where they are what layout_of makes them follow the report to -- and, for three documents, every key, as the project's own file stated them."""
    stated = stated_layout(layout)
    if "typst_root" in stated:
        return stated
    rest = {key: value for key, value in stated.items() if key not in ("generated", "pdf")}
    followed = layout_of({"layout": rest})
    return {key: value for key, value in stated.items() if key in rest or followed[key] != value}


def report_folder_for(language):
    """The report folder's name a new project written in `language` is offered (REPORT_FOLDERS): German's word where the language is not one of the three."""
    return REPORT_FOLDERS.get(language or DEFAULT_LANGUAGE, REPORT_FOLDERS[DEFAULT_LANGUAGE])


def report_folder_offered(template, language):
    """The report folder's name a new project from `template` written in `language` is offered (v0.100).

    A template that names its report folder in its own `template.json` **means it**, so its name is kept whatever the language; one that states no layout at all -- Standard, `templates/projet/` -- takes REPORT_FOLDERS' word for the language. A documents-shaped template offers the folder its report lies in, which it states with the rest.

    ⚠️ This is why `templates/projet/`'s own folder on disk is still called «Statischer Bericht (typst)» and is deliberately not renamed: `stated_layout` compares a template's layout against `project.DEFAULT_LAYOUT`, so renaming that folder would make Standard *state* a report folder and the language's word would never be offered again. The folder is an implementation detail of the template -- every project made from it renames it.
    """
    if template.has_modes:
        return template.document_folder("rs")
    stated = template_layout(template.layout).get("report")
    if stated:
        parent = PurePosixPath(str(stated).replace("\\", "/")).parent.as_posix()
        if parent not in (".", ""):
            return parent
    return report_folder_for(language)


def folders_offered(template, language):
    """The three folders a new project from `template` written in `language` is offered, as {mode: folder} -- what «Nouveau projet» prefills its three fields with, and what `project_template.create` takes where it is given none (the question v0.100 asked of the one report folder, asked of the three).

    calc/documents.py's names for the language (MODE_FOLDERS), and for the report `report_folder_offered`'s -- the template's own where it names one. A documents-shaped template offers the three folders it states, which it means as a report-shaped one means its report folder.
    """
    if template.has_modes:
        return {mode: template.document_folder(mode) for mode in project.MODES}
    return {**documents.folders_for(language or DEFAULT_LANGUAGE), "rs": report_folder_offered(template, language)}


def check_report_folder(name):
    """`name` stripped, as the report's folder inside a project -- or a TemplateError naming what is wrong with it (v0.100).

    **One folder, and not a path.** What is typed here becomes the project's own `layout.report` (layout_in_folder), so a name carrying a separator would put the report somewhere the engineer did not ask for, and `..` would put it outside the project -- which `Project.__init__` refuses when the file is next read, by which time the folder has been created and the project written. It is refused here instead, at the one moment the name is typed, with the reason rather than a traceback.
    """
    cleaned = (name or "").strip()
    if not cleaned:
        raise TemplateError("the report's folder needs a name")
    if "/" in cleaned or "\\" in cleaned:
        raise TemplateError(f"the report's folder is one folder and not a path: {name!r} carries a separator")
    if cleaned in (".", ".."):
        raise TemplateError(f"{name!r} is not the name of a folder")
    refused = sorted({ch for ch in cleaned if ch in '<>:"|?*' or ord(ch) < 32})
    if refused:
        raise TemplateError("the report's folder cannot carry " + ", ".join(repr(ch) for ch in refused) + " -- Windows refuses it in a name")
    if cleaned.endswith("."):
        # a trailing space needs no check of its own: it is stripped above, which is what an engineer typing one means
        raise TemplateError(f"{name!r} ends in a dot, which Windows takes off a folder's name")
    if cleaned.split(".")[0].upper() in RESERVED_NAMES:
        raise TemplateError(f"{name!r} is a name Windows reserves for a device")
    return cleaned


def layout_in_folder(layout, folder):
    """`layout` -- a report alone's -- with its report folder renamed to `folder`, the entry file keeping its name (v0.100). What a new project was created with until the three documents; a project laid out in three names its three folders instead (documents.modes_layout, `folders_offered`), and this stays for a report alone's layout.

    The engineer renames **the folder and not the `.typ`** (his answer C6), so the PDF keeps its name too -- which matters because since v0.87 Tinymist states no `outputPath` and names the PDF after the entry file, and `woodcore-cli`, «Exporter PDF» and Tinymist must all name one PDF (docs/conventions/build-and-release.md §12).

    ⚠️ `generated` and `pdf` follow the report into the new folder exactly as they follow a template that moves it (`layout_of`), so only `report` is stated and the three cannot come apart: `Project.__init__` refuses a `generated` that does not lie inside the report's own folder, and says so with a message of its own. Every other part the template states -- `sources`, `archives` -- moves only where it lay inside the report's old folder, and stays where it is otherwise.
    """
    folder = check_report_folder(folder)
    old = PurePosixPath(layout["report"].replace("\\", "/")).parent
    if old.as_posix() in (".", ""):
        raise TemplateError("this template keeps its report at the top of the project, so it has no report folder to name")

    def moved(value):
        path = PurePosixPath(str(value).replace("\\", "/"))
        if path == old or old in path.parents:
            return (PurePosixPath(folder) / path.relative_to(old)).as_posix()
        return str(value)

    stated = {key: moved(value) for key, value in template_layout(layout).items()}
    stated["report"] = moved(layout["report"])
    return layout_of({"layout": stated})


class Template:
    """One template: its place, its folder, what its template.json says, and -- where it cannot be used -- why (`error`, "" for a sound one)."""

    def __init__(self, place, folder, meta=None, error=""):
        self.place = place
        self.folder = Path(folder)
        self.meta = meta if isinstance(meta, dict) else {}
        self.error = error

    @property
    def ref(self):
        return f"{self.place}:{self.folder.name}"

    @property
    def name(self):
        name = self.meta.get("name")
        return name.strip() if isinstance(name, str) and name.strip() else self.folder.name

    def description(self, lang="fr"):
        """The description in `lang` -- a builtin template carries one per language, a template of the engineer's the one he wrote."""
        text = self.meta.get("description")
        if isinstance(text, dict):
            return str(text.get(lang) or text.get("en") or next(iter(text.values()), ""))
        return text if isinstance(text, str) else ""

    @property
    def read_only(self):
        return self.place == "builtin"

    @property
    def layout(self):
        return layout_of(self.meta)

    @property
    def report(self):
        return self.folder / self.layout["report"]

    @property
    def report_dir(self):
        return self.report.parent

    @property
    def has_modes(self):
        """True for a documents-shaped template -- saved from a project laid out in three documents, its layout stating `typst_root` -- and False for a report-shaped one, which Standard is."""
        return "typst_root" in self.layout

    @property
    def typst_root(self):
        """The folder the template's documents compile from: its own top for a documents-shaped template, the report's folder for a report-shaped one -- where its config.typ and its commands.typ lie."""
        return (self.folder / self.layout["typst_root"]) if self.has_modes else self.report_dir

    @property
    def config(self):
        """The template's config.typ: in its configuration's folder for one saved from a project laid out by folders (`layout.config`, issue #64), at its Typst root otherwise."""
        if self.has_modes and "config" in self.layout:
            return self.folder / self.layout["config"] / CONFIG
        return self.typst_root / CONFIG

    @property
    def modes(self):
        """The documents the template holds: the three for a documents-shaped template, the report alone (project.REPORT_ONLY) for a report-shaped one."""
        return project.MODES if self.has_modes else project.REPORT_ONLY

    def entry(self, mode):
        """The entry file of document `mode` in the template -- `report` for "rs"."""
        return self.folder / self.layout[project.ENTRY_KEYS[mode]]

    @property
    def entries(self):
        """The entry file of every document the template holds, in the order of `modes`."""
        return [self.entry(mode) for mode in self.modes]

    def document_folder(self, mode):
        """The folder document `mode` lies in, as the template's layout writes it -- `3_Statischer Bericht`; "." for a report at the top of the template."""
        return PurePosixPath(str(self.layout[project.ENTRY_KEYS[mode]]).replace("\\", "/")).parent.as_posix()

    @property
    def sections_dir(self):
        return self.report_dir / SECTIONS

    @property
    def document_language(self):
        value = self.meta.get("document_language")
        return value if value in LANGUAGES else ""

    @property
    def report_language(self):
        value = self.meta.get("report_language")
        return value if value in LANGUAGES else ""

    def person(self, key):
        value = self.meta.get(key)
        return value.strip() if isinstance(value, str) else ""

    def __repr__(self):
        return f"Template({self.ref!r})"


def check(template):
    """Raises TemplateError where `template` cannot make a project: its template.json not of the schema, no name, a language not one of the three, a layout that leaves the folder or puts the export outside the report's (project.Project's own rules, those of three documents for a documents-shaped template), no entry file where the layout says -- one for each of the three documents of a documents-shaped template --, or a language stated that its files have no line for."""
    meta = template.meta
    try:
        validation.validate_structure(meta, "template")
    except validation.ValidationError as exc:
        raise TemplateError(f"{template.folder / FILE}: {exc}") from None
    if not isinstance(meta.get("name"), str) or not meta["name"].strip():
        raise TemplateError(f"{template.folder / FILE}: the template has no name")
    for key in ("document_language", "report_language"):
        value = meta.get(key)
        if value not in (None, "") and value not in LANGUAGES:
            raise TemplateError(f"{template.folder / FILE}: {key} is {value!r} -- expected one of {', '.join(LANGUAGES)}")
    try:
        project.Project(template.folder / ("template" + project.EXTENSION),
                        {"schema_version": project.schema_version_for(template.layout), "format": project.FORMAT, "name": template.name, "layout": template.layout})
    except project.ProjectError as exc:
        raise TemplateError(f"{template.folder}: {exc}") from None
    if not template.report.is_file():
        raise TemplateError(f"{template.folder}: the report's entry file {template.layout['report']} is not there")
    for mode in template.modes:
        if mode != "rs" and not template.entry(mode).is_file():
            raise TemplateError(f"{template.folder}: the entry file of the {documents.MODE_NAMES['en'][mode].lower()}, "
                                f"{template.layout[project.ENTRY_KEYS[mode]]}, is not there")
    if template.document_language and not (template.config.is_file() and _DOC_LANG.search(_read_text(template.config))):
        config = template.config.relative_to(template.folder).as_posix() if template.config.is_relative_to(template.folder) else template.config
        raise TemplateError(f"{template.folder}: document_language is stated, and {config} has no `#let doc-lang = \"…\"` line to write it into")
    if template.report_language and not _REPORT_LANG.search(_read_text(template.report)):
        raise TemplateError(f"{template.folder}: report_language is stated, and {template.layout['report']} has no `#set-report-language(sys.inputs.at(\"lang\", default: \"…\"))` to write it into")


def read(folder, place):
    """The template in `folder` of `place`, read and checked -- one that cannot be used carries its reason in `error` rather than raising, so a list of templates still shows it."""
    folder = Path(folder)
    try:
        meta = json.loads((folder / FILE).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Template(place, folder, {}, f"{folder}: no {FILE}")
    except (OSError, ValueError) as exc:
        return Template(place, folder, {}, f"{folder / FILE}: cannot be read ({exc})")
    template = Template(place, folder, meta)
    if not isinstance(meta, dict):
        template.error = f"{folder / FILE}: not an object"
        return template
    try:
        check(template)
    except TemplateError as exc:
        template.error = str(exc)
    return template


def standard():
    """Standard, the builtin template -- read without the settings, which cannot hide it."""
    return read(BUILTIN_DIR / STANDARD.split(":", 1)[1], "builtin")


def list_templates(settings=None):
    """Every template of the three places, builtin first, then the engineer's, then the office's, each place in the order of its folders' names. A folder holding no template.json is not a template and is left out; one whose template.json is wrong is listed, its `error` saying why."""
    settings = settings if settings is not None else usersettings.read()
    out = []
    for place in PLACES:
        root = place_dir(place, settings)
        if root is None or not root.is_dir():
            continue
        for folder in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if folder.is_dir() and (folder / FILE).is_file():
                out.append(read(folder, place))
    return out


def find(ref, settings=None):
    """The template `ref` names: `<place>:<folder or name>`, or a folder or a name alone -- the engineer's own first, then the office's, then the builtin ones. Raises TemplateError naming those there are where none is, or the reason where the one found cannot be used."""
    ref = (ref or "").strip() or STANDARD
    found = list_templates(settings)
    place, colon, name = ref.partition(":")
    if colon and place in PLACES:
        candidates = [t for t in found if t.place == place and name.lower() in (t.folder.name.lower(), t.name.lower())]
    else:
        order = {"user": 0, "shared": 1, "builtin": 2}
        candidates = sorted((t for t in found if ref.lower() in (t.folder.name.lower(), t.name.lower())), key=lambda t: order[t.place])
    if not candidates:
        names = ", ".join(f"{t.name} ({t.ref})" for t in found) or "none"
        raise TemplateError(f"no template {ref!r} -- there are: {names}")
    if candidates[0].error:
        raise TemplateError(candidates[0].error)
    return candidates[0]


def default_template(settings=None):
    """The template the settings name as the default, else Standard -- and Standard where the one named is gone or cannot be used."""
    settings = settings if settings is not None else usersettings.read()
    try:
        return find(default_ref(settings), settings)
    except TemplateError:
        return standard()


def languages_for(template, settings=None):
    """(document language, report language) of a project made from `template`: the template's own, else the settings' default report language, else German -- and the document in the report's language where the template states none for it."""
    settings = settings if settings is not None else usersettings.read()
    report = template.report_language or defaults(settings)["report_language"] or DEFAULT_LANGUAGE
    return template.document_language or report, report


def people_for(template, settings=None):
    """{company, author, checker} a new project from `template` starts with: the template's own, else the settings' defaults."""
    settings = settings if settings is not None else usersettings.read()
    own = defaults(settings)
    return {key: template.person(key) or own[key] for key in PEOPLE}


# --- the languages in a report's files -----------------------------------------------------

def config_for(entry):
    """The config.typ the document whose entry file is `entry` is styled by: beside it for a report alone, which keeps its config.typ in its own folder, at the top of the project -- the folder above the document's own -- for three documents, which share one, and in the configuration's folder there for three documents laid out by folders (000-Typst-Config/, issue #64). The one beside the entry where none is there, for the caller to find missing."""
    entry = Path(entry)
    for folder in (entry.parent, entry.parent.parent, entry.parent.parent / project.CONFIG_FOLDER):
        if (folder / CONFIG).is_file():
            return folder / CONFIG
    return entry.parent / CONFIG


def read_languages(report_typ, config=None):
    """(document language, report language) as the files of the report whose entry file is `report_typ` state them: the `doc-lang` of its config.typ -- `config`, else the one `config_for` finds, beside it or at the top of a project in three documents -- and the entry file's `set-report-language` default; "" for one there is no line for."""
    report_typ = Path(report_typ)
    config = Path(config) if config is not None else config_for(report_typ)
    document = _DOC_LANG.search(_read_text(config)) if config.is_file() else None
    report = _REPORT_LANG.search(_read_text(report_typ)) if report_typ.is_file() else None
    return (document.group(2) if document else ""), (report.group(2) if report else "")


def project_language(here, fallback="de"):
    """The language project `here`'s documents are written in -- the `doc-lang` of its config.typ, else the report's own language -- or `fallback` where the project states none (v0.116; moved here from positions_store in 0.122, the one reader of it). The language is chosen as the project is created and written into config.typ there and then (issue #90), whether or not a document is there yet."""
    try:
        document, report = read_languages(here.report_typ, config=config_for(here.report_typ))
    except (OSError, ValueError, AttributeError):
        return fallback
    for lang in (document, report):
        if lang in LANGUAGES:
            return lang
    return fallback


def write_project_languages(config, entries, document=None, report=None):
    """Writes the document language into `config` and the report language into each of `entries` -- the one config.typ three documents share and their three entry files, or a report alone's own two -- each only where given, differing from what the file says, and the line there; the rest of the file as it was, line endings included. Returns the files rewritten."""
    written = []
    targets = [(Path(config), _DOC_LANG, document)] + [(Path(entry), _REPORT_LANG, report) for entry in entries]
    for path, pattern, value in targets:
        if not value or not path.is_file():
            continue
        text = _read_text(path)
        found = pattern.search(text)
        if found is None or found.group(2) == value:
            continue
        _write_text(path, text[:found.start(2)] + value + text[found.end(2):])
        written.append(path)
    return written


# --- the look of a project -------------------------------------------------------------------
# A project's look is a **form** (calc/forms.py: `Template/`, `title.typ`, a config.typ holding the language and the engineer's adjustments). The older *styles* (templates/styles/) are gone; `replace_config` is what remains of the name, and is `forms.apply`.

# `#let doc-region = "CH"` beside `doc-lang`, and `#let conf(doc) = …`: what a project's config.typ must carry for its language to be read and for the entry files' `#import "/config.typ": conf` to resolve (read by calc/forms.py).
_DOC_REGION = re.compile(r'^([ 	]*#let[ 	]+doc-region[ 	]*=[ 	]*")([A-Za-z-]*)(")', re.M)
_CONF = re.compile(r"^[ 	]*#let[ 	]+conf[ 	]*\(", re.M)


def _in_language(value, lang):
    """`value` -- a string, or a {language: text} dictionary -- in `lang`, else in English, else the first there is (read by calc/forms.py for the names and descriptions of a form)."""
    if isinstance(value, dict):
        return str(value.get(lang) or value.get("en") or next(iter(value.values()), "")).strip()
    return value.strip() if isinstance(value, str) else ""


def replace_config(here, form):
    """Switches the look of project `here` to `form` -- the older name of `forms.apply`. `form` is a forms.Form or a reference (`neutral`, `compact`, `bfh`, `<place>:<id>`: `forms.find`; an unknown one is refused naming the forms there are, before anything is written). The project's `Template/` and `title.typ` -- and its config.typ where it is not in the new format already -- are moved into `_Archiv/<stamp>-forme/`, the form's put in their place, and the project's language kept. Returns the project's config.typ."""
    import forms
    try:
        forms.apply(here, form)
    except forms.FormError as exc:
        raise TemplateError(str(exc)) from None
    return Path(here.config_typ)


# --- the sections of a template's report ---------------------------------------------------

def sections(report_dir):
    """The `Sections/*.typ` of the report in `report_dir`, in the order of their numbers -- `002-grundlagen.typ` before `010-anhang.typ` -- then of their names."""
    folder = Path(report_dir) / SECTIONS
    if not folder.is_dir():
        return []
    def key(path):
        m = _SECTION.match(path.name)
        return (int(m.group(1)) if m else 10 ** 9, path.name.lower())
    return sorted((p for p in folder.glob("*.typ") if p.is_file()), key=key)


def section_title(path):
    """What a section is called in a list: its file name without its number and its `.typ` -- `grundlagen`."""
    m = _SECTION.match(Path(path).name)
    return m.group(2) if m else Path(path).stem


def slug(title):
    """A section's file name part: the title with its accents decomposed, lower case, anything but a letter or a digit a hyphen -- `Brandschutz Nachweis` -> `brandschutz-nachweis`."""
    out = []
    for char in unicodedata.normalize("NFKD", (title or "").strip().lower()):
        if unicodedata.combining(char):
            continue
        out.append(char if char.isascii() and char.isalnum() else "-")
    return re.sub("-+", "-", "".join(out)).strip("-") or "abschnitt"


def _numbered(number, width, part):
    return f"{number:0{width}d}-{part}.typ"


def renumber(report_dir, order=None):
    """The sections of `report_dir` numbered 1, 2, 3 … in `order` (their paths; their present order by default), three digits wide as the Standard template writes them. Returns {old name: new name} of the files renamed -- in two steps through a temporary name, so that two sections trading numbers never meet on one file."""
    order = list(order if order is not None else sections(report_dir))
    width = max(3, len(str(len(order))))
    renamed, moves = {}, []
    for index, path in enumerate(order, 1):
        new = _numbered(index, width, section_title(path))
        if new != path.name:
            renamed[path.name] = new
            moves.append((path, path.with_name(new)))
    temporary = [(path, path.with_name(path.name + ".renumber")) for path, _new in moves]
    for path, tmp in temporary:
        path.rename(tmp)
    for (_path, new), (_old, tmp) in zip(moves, temporary):
        tmp.rename(new)
    return renamed


def sync_includes(report_typ, renamed=None):
    """The report's `#include "Sections/…"` lines brought to its sections as they are: the lines stay where they stand in the entry file, and each is given the next section in order -- a section added takes a line after the last, one deleted takes its line away, and one the engineer had commented out stays commented out under its new number (`renamed`, {old name: new name}). Nothing else of the file moves. Returns whether it was rewritten."""
    report_typ = Path(report_typ)
    text = _read_text(report_typ)
    lines = text.splitlines(keepends=True)
    renamed = renamed or {}
    slots, commented = [], set()
    for index, line in enumerate(lines):
        m = _INCLUDE.match(line.rstrip("\r\n"))
        if m:
            slots.append(index)
            if m.group(1).strip().startswith("//"):
                commented.add(renamed.get(m.group(2), m.group(2)))
    ending = "\r\n" if "\r\n" in text else "\n"
    names = [path.name for path in sections(report_typ.parent)]

    def line_for(name, template_line=None):
        indent = re.match(r"[ \t]*", template_line or "").group(0)
        own = template_line[len(template_line.rstrip("\r\n")):] if template_line else ending
        return f'{indent}{"// " if name in commented else ""}#include "{SECTIONS}/{name}"{own or ending}'

    out, placed = list(lines), 0
    for index in slots:
        out[index] = line_for(names[placed], lines[index]) if placed < len(names) else None
        placed += 1
    rest = [line_for(name) for name in names[len(slots):]]
    if rest:
        if slots:
            at = slots[-1] + 1
            if out[slots[-1]] is not None and not out[slots[-1]].endswith(("\n", "\r")):
                out[slots[-1]] += ending
        else:
            at = len(out)
            if out and not out[-1].endswith(("\n", "\r")):
                out[-1] += ending
        out[at:at] = rest
    new_text = "".join(line for line in out if line is not None)
    if new_text == text:
        return False
    _write_text(report_typ, new_text)
    return True


def add_section(report_typ, title):
    """A new section after the last, `Sections/<n>-<slug>.typ` holding the import every section starts with and `title` as its heading, included in the report. Returns its path."""
    report_typ = Path(report_typ)
    folder = report_typ.parent / SECTIONS
    folder.mkdir(parents=True, exist_ok=True)
    existing = sections(report_typ.parent)
    numbers = [int(m.group(1)) for m in (_SECTION.match(p.name) for p in existing) if m]
    number = max(numbers, default=0) + 1
    path = folder / _numbered(number, max(3, len(str(number))), slug(title))
    if path.exists():
        raise TemplateError(f"{path.name} is there already")
    _write_text(path, f'#import "../commands.typ": *\n\n= {title.strip() or path.stem}\n')
    sync_includes(report_typ)
    return path


def rename_section(report_typ, name, title):
    """Section `name` given the file name `title` makes, its number kept, and its include line with it. The heading inside is the engineer's prose and is left alone. Returns its new path."""
    report_typ = Path(report_typ)
    path = report_typ.parent / SECTIONS / name
    m = _SECTION.match(name)
    new = path.with_name(f"{m.group(1)}-{slug(title)}.typ" if m else f"{slug(title)}.typ")
    if new == path:
        return path
    if new.exists():
        raise TemplateError(f"{new.name} is there already")
    path.rename(new)
    sync_includes(report_typ, {name: new.name})
    return new


def delete_section(report_typ, name):
    """Section `name` deleted, the others numbered again without the gap, and the report's include lines with them."""
    report_typ = Path(report_typ)
    (report_typ.parent / SECTIONS / name).unlink()
    sync_includes(report_typ, renumber(report_typ.parent))


def move_section(report_typ, name, step):
    """Section `name` moved `step` places (-1 up, +1 down) among the sections, all of them numbered again in the new order, and the report's include lines with them. Returns the section's new path."""
    report_typ = Path(report_typ)
    order = sections(report_typ.parent)
    index = next(i for i, p in enumerate(order) if p.name == name)
    target = max(0, min(len(order) - 1, index + step))
    order.insert(target, order.pop(index))
    renamed = renumber(report_typ.parent, order)
    sync_includes(report_typ, renamed)
    return report_typ.parent / SECTIONS / renamed.get(name, name)


# --- templates written -------------------------------------------------------------------------

def folder_name(name):
    """A template's folder: its name with what Windows refuses in a file name taken out."""
    cleaned = "".join("_" if ch in '<>:"/\\|?*' or ord(ch) < 32 else ch for ch in (name or "")).strip().rstrip(".")
    return cleaned or "Modell"


def _new_folder(root, name):
    root = Path(root)
    base = folder_name(name)
    candidate, n = root / base, 2
    while candidate.exists():
        candidate, n = root / f"{base} {n}", n + 1
    return candidate


def _writable_root(place, settings):
    if place == "builtin":
        raise TemplateError("the builtin templates are read only -- duplicate one to change it")
    root = place_dir(place, settings)
    if root is None:
        raise TemplateError("no shared folder of templates is set (Paramètres → Chemins)")
    return root


def _check_name(name, settings):
    if not name or not name.strip():
        raise TemplateError("a template needs a name")
    builtin = {t.name.lower() for t in list_templates(settings) if t.place == "builtin"}
    if name.strip().lower() in builtin:
        raise TemplateError(f"{name.strip()} is the name of a builtin template -- choose another")


def write_meta(folder, meta):
    """Writes `meta` as the template.json of `folder` -- checked first against the schema and the template's own files -- and the languages it states into those files, so that the skeleton and its template.json say the same thing. Returns the template as it now stands."""
    folder = Path(folder)
    meta = {key: value for key, value in meta.items() if value not in (None, "", {})}
    meta.update(schema_version=SCHEMA_VERSION, format=FORMAT)
    template = Template("user", folder, meta)
    check(template)
    write_project_languages(template.config, template.entries, template.document_language or None, template.report_language or None)
    ordered = {key: meta[key] for key in ("schema_version", "format", "name", "description") if key in meta}
    ordered.update((key, value) for key, value in meta.items() if key not in ordered)
    temporary = folder / (FILE + ".tmp")
    temporary.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(folder / FILE)
    return template


def duplicate(template, name, place="user", settings=None):
    """A copy of `template` under `name`, in `place` (the engineer's own by default) -- a copy of a builtin one without its description, which describes the builtin one. Returns the new template."""
    settings = settings if settings is not None else usersettings.read()
    root = _writable_root(place, settings)
    _check_name(name, settings)
    folder = _new_folder(root, name)
    folder.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template.folder, folder, ignore=shutil.ignore_patterns("__pycache__", FILE + ".tmp"))
    meta = dict(template.meta, name=name.strip())
    if template.read_only:
        meta.pop("description", None)
    try:
        write_meta(folder, meta)
    except TemplateError:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return read(folder, place)


def update(template, **changes):
    """Rewrites `template`'s template.json with `changes` -- a key given "" or None taken out, `layout` given as the keys the form edits (EDITED_LAYOUT) -- and, where the report's entry file moves, moves it and its folder in the skeleton first. Returns the template as it now stands.

    A documents-shaped template's layout is not edited here: its three documents' folders are named when a project is made from it (project_template.create, `folders_offered`), and moving the report alone would part it from the files the three share. A `layout` that says what the form showed -- `template_layout`'s own values for EDITED_LAYOUT, which is what *Paramètres* sends back with every change of name -- is taken for no change; any other is refused by name.
    """
    if template.read_only:
        raise TemplateError(f"{template.name} is a builtin template -- duplicate it to change it")
    if "name" in changes:
        _check_name(changes["name"], None)
        changes["name"] = changes["name"].strip()
    meta = dict(template.meta)
    layout = changes.pop("layout", None)
    if layout is not None and template.has_modes:
        shown = template_layout(template.layout)
        edited = [key for key in EDITED_LAYOUT if (layout.get(key) or "").strip().replace("\\", "/") != shown.get(key, "")]
        if edited:
            raise TemplateError(f"{template.name} is laid out in three documents, and its layout ({', '.join(edited)}) is not edited "
                                f"here -- its documents' folders are named when a project is made from it")
        layout = None
    for key, value in changes.items():
        if value is None or value == "":
            meta.pop(key, None)
        else:
            meta[key] = value
    if layout is not None:
        stated = dict(meta.get("layout") or {})
        old_report = template.layout["report"]
        for key in EDITED_LAYOUT:
            value = (layout.get(key) or "").strip().replace("\\", "/")
            if value and value != project.DEFAULT_LAYOUT[key]:
                stated[key] = value
            else:
                stated.pop(key, None)
        new_report = stated.get("report", project.DEFAULT_LAYOUT["report"])
        if new_report != old_report:
            stated.pop("generated", None)   # they follow the report into its new folder (layout_of)
            stated.pop("pdf", None)
            move_report(template, new_report)
        if stated:
            meta["layout"] = stated
        else:
            meta.pop("layout", None)
    write_meta(template.folder, meta)
    return read(template.folder, template.place)


def move_report(template, new_report):
    """The skeleton's report moved to where `new_report` (a path in the template) says: its folder renamed where the folder changes, its entry file where the name does. Refused where the new place holds something already, or where the report lies at the top of the template, which cannot be moved without everything else."""
    old = template.report
    new = template.folder / new_report
    if old.resolve() == new.resolve():
        return
    if not old.is_file():
        raise TemplateError(f"{template.folder}: the report's entry file {template.layout['report']} is not there")
    if new.exists():
        raise TemplateError(f"{new_report} is there already")
    old_dir, new_dir = old.parent, new.parent
    if old_dir.resolve() != new_dir.resolve():
        if old_dir.resolve() == template.folder.resolve():
            raise TemplateError("the report lies at the top of the template -- its folder cannot be moved")
        try:
            new_dir.resolve().relative_to(old_dir.resolve())
            raise TemplateError(f"{new_report} lies inside the report's own folder")
        except ValueError:
            pass
        if new_dir.exists() and any(new_dir.iterdir()):
            raise TemplateError(f"{new_dir.relative_to(template.folder).as_posix()} holds something already")
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        if new_dir.exists():
            new_dir.rmdir()
        old_dir.rename(new_dir)
        old = new_dir / old.name
    if old.name != new.name:
        old.rename(new)


def delete(template):
    """The template's folder removed, and everything in it -- refused for a builtin one."""
    if template.read_only:
        raise TemplateError(f"{template.name} is a builtin template and cannot be deleted")
    shutil.rmtree(template.folder)


# --- archived and imported (the settings' one «Modèles» page, v0.113) ------------------------------
#
# The engineer: no template is created or edited by hand in the settings any more -- a template is a folder, made elsewhere (in VS Code, or from a project), and brought in. «Supprimer» moves it into its place's `archives/`, never deletes it, as a document template's has since v0.112 (calc/doc_templates.py `delete`), and «Importer un dossier…» copies one template folder into the engineer's own place, an existing one of that folder's name moved into the archives first on his word.

# The folder of a place where what is taken away goes: `<place>/archives/<yymmdd-hhmmss>-<folder>`. It holds no template.json, so `list_templates` never takes it for a template.
ARCHIVES = "archives"
# Every refusal of `import_folder`, by `code`: the window writes its own sentence for each (calc/tools/settings_dialog.py).
IMPORT_CODES = ("not_a_folder", "no_template", "document_template", "invalid", "name_is_builtin", "already_mine", "exists", "write_failed")


class TemplateImportError(TemplateError):
    """A folder `import_folder` refuses, said by name: `code` one of IMPORT_CODES, `values` what the refusal is about (`folder`, `name`, `document`, `error`), beside the English sentence -- as doc_templates.DocTemplateError carries them."""

    def __init__(self, message="", code="", **values):
        super().__init__(message)
        self.code = code
        self.values = values


def _refuse_import(code, message, **values):
    raise TemplateImportError(message, code, **values)


def _move_retried(source, target):
    """`source` renamed to `target`, tried again a few times on the PermissionError NextCloud's client gives while it holds what it has just seen written (doc_templates._move's own rule)."""
    import time
    for attempt in range(6):
        try:
            return os.replace(source, target)
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.1 * (attempt + 1))


def _archived_path(root, label):
    """`<root>/archives/<yymmdd-hhmmss>-<label>`, `-2`, `-3` … where that is taken."""
    import time
    stamp = time.strftime("%y%m%d-%H%M%S")
    target = Path(root) / ARCHIVES / f"{stamp}-{label}"
    number = 2
    while target.exists():
        target = Path(root) / ARCHIVES / f"{stamp}-{label}-{number}"
        number += 1
    return target


def archive(template):
    """«Supprimer»: the template's folder moved into its place's `archives/` -- `<place>/archives/<yymmdd-hhmmss>-<folder>` -- and never deleted. Refused for a builtin one. A template that cannot be used can be taken away all the same. Returns where it went."""
    if template.read_only:
        raise TemplateError(f"{template.name} is a builtin template and cannot be deleted")
    target = _archived_path(template.folder.parent, template.folder.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    _move_retried(template.folder, target)
    return target


def import_folder(source, replace=False, settings=None):
    """«Importer un dossier…»: the project template in the folder `source` -- a folder holding a template.json, like each of an office's shared folder -- copied into the engineer's own place (`place_dir("user")`) under its folder's name. Returns the template as it now stands there.

    **Checked before anything is written**: `source` must be a folder (`not_a_folder`) holding a template.json (`no_template`) of a project template -- a document template's is refused naming its document (`document_template`), the settings' page importing it under that document -- that `check` finds sound (`invalid`, its reason in `error`), not named as a builtin one (`name_is_builtin`), and not one of the engineer's own already (`already_mine`). A template of that folder's name in his place is refused (`exists`) unless `replace`, which moves the old one into the place's `archives/` -- never deleted -- and puts it back if the copy then fails. The copy is staged beside the place and read back first, so a failure (`write_failed`) leaves nothing half copied."""
    settings = settings if settings is not None else usersettings.read()
    source = Path(source)
    if not source.is_dir():
        _refuse_import("not_a_folder", f"{source} is not a folder", folder=str(source))
    if not (source / FILE).is_file():
        _refuse_import("no_template", f"{source} holds no {FILE} -- it is not a template", folder=str(source))
    try:
        meta = json.loads((source / FILE).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        _refuse_import("invalid", f"{source / FILE} cannot be read ({exc})", folder=str(source), error=str(exc))
    if isinstance(meta, dict) and meta.get("format") == "woodcore-document-template":
        _refuse_import("document_template", f"{source} is a document template ({meta.get('mode')!r}), not a project template", folder=str(source), document=meta.get("mode") or "")
    found = read(source, "user")
    if found.error:
        _refuse_import("invalid", found.error, folder=str(source), error=found.error)
    root = Path(place_dir("user", settings))
    mine, there = root.resolve(), source.resolve()
    if there == mine or mine in there.parents or there in mine.parents:
        _refuse_import("already_mine", f"{source} is among the engineer's own templates already", folder=str(source))
    if found.name.lower() in {t.name.lower() for t in list_templates(settings) if t.place == "builtin"}:
        _refuse_import("name_is_builtin", f"{found.name} is the name of a builtin template -- rename it in its {FILE} first", name=found.name)
    target = root / source.name
    if target.exists() and not replace:
        _refuse_import("exists", f"user:{source.name} is there already -- importing over it asks for `replace`, which keeps the old one in {ARCHIVES}/", folder=source.name, name=found.name)
    stage = root / f".importing-{os.getpid()}"
    staged = stage / source.name
    shutil.rmtree(stage, ignore_errors=True)
    try:
        try:
            stage.mkdir(parents=True)
            shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", ".git", FILE + ".tmp"))
            made = read(staged, "user")
            if made.error:
                _refuse_import("invalid", made.error, folder=str(source), error=made.error)
            archived = None
            if target.exists():
                archived = _archived_path(root, target.name)
                archived.parent.mkdir(parents=True, exist_ok=True)
                _move_retried(target, archived)
            try:
                _move_retried(staged, target)
            except OSError:
                if archived is not None:
                    _move_retried(archived, target)
                raise
        except OSError as exc:
            _refuse_import("write_failed", f"{source} could not be copied into the engineer's templates: {exc}", folder=str(source), error=str(exc))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return read(target, "user")


def save_project(here, name, place="user", settings=None, description=""):
    """«Enregistrer ce projet comme modèle»: project `here`'s skeleton made a template named `name` in `place`. Returns the new template.

    **A report alone** gives a report-shaped template: the report's folder -- its entry file, config.typ, commands.typ, Sections/ and whatever else the engineer keeps there -- and the project's `.vscode/`. Refused where the report lies at the top of its project's folder, which would take the whole project.

    **Three documents** give a documents-shaped template: what the three share at the top of the project -- config.typ, commands.typ, references.bib, title.typ, the form's `Template/`, the pictures -- each document's own folder and `.vscode/`, and **nothing else of the top of the project**: the architect's plans and the office's other folders lie there beside the documents and are not a template's. Its template.json states the project's layout in full, as the project's .woodcore does.

    In both, the languages the files state, the layout where it differs from the default, and the company, author and checker are taken; and what never is: the export and the engine's copy (`generated`), the drawings of Woodcore's window (`sources`), the archives, a PDF, the workbooks, the `.woodcore` and its lock, each document's `sync.json` (what it shares with the others is the project's, not a template's), and a picture of `Images/` no .typ of the template names -- a project's site photographs are not a template's.
    """
    settings = settings if settings is not None else usersettings.read()
    root = _writable_root(place, settings)
    _check_name(name, settings)
    top = here.root.resolve()
    if here.has_modes:
        parts = [here.config_typ, here.commands_typ, here.references_bib, here.title_typ, here.template_dir, here.images_dir, *(here.document_dir(mode) for mode in here.modes)]
    else:
        report_dir = here.typst_root.resolve()
        if report_dir == top:
            raise TemplateError(f"{here.name}: its report lies at the top of the project's folder -- a template takes the report's own folder, and here that would be the whole project")
        parts = [report_dir]
    skip = {p.resolve() for p in (here.generated_dir, here.sources_dir, here.archives_dir, here.formulas_dir, *(here.document_pdf(mode) for mode in here.modes))}

    def ignore(directory, names):
        out = set()
        for entry in names:
            path = (Path(directory) / entry).resolve()
            if path in skip or entry.lower().endswith((".pdf", ".xlsx", ".xlsm", ".xls", project.EXTENSION, ".lock", ".tmp")) or entry in ("__pycache__", ".probe", SYNC_FILE):
                out.add(entry)
        return out

    folder = _new_folder(root, name)
    folder.parent.mkdir(parents=True, exist_ok=True)
    try:
        folder.mkdir()
        for part in parts:
            part = Path(part).resolve()
            if part in skip or not part.exists():
                continue
            target = folder / part.relative_to(top)
            if part.is_dir():
                shutil.copytree(part, target, ignore=ignore)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(part, target)
        vscode = here.root / ".vscode"
        if vscode.is_dir():
            shutil.copytree(vscode, folder / ".vscode")
        images = folder / here.images_dir.resolve().relative_to(top)
        if images.is_dir():
            named = "\n".join(_read_text(p) for p in folder.rglob("*.typ"))
            for picture in sorted(images.rglob("*"), reverse=True):
                if picture.is_file() and picture.name not in named:
                    picture.unlink()
                elif picture.is_dir() and not any(picture.iterdir()) and picture != images:
                    picture.rmdir()
        document, report = read_languages(here.report_typ)
        meta = {"name": name.strip(), "description": description.strip(), "document_language": document, "report_language": report,
                "layout": template_layout({key: value for key, value in here.layout.items() if key in project.LAYOUT_KEYS})}
        meta.update({key: here.detail(key) for key in PEOPLE})
        write_meta(folder, meta)
    except (OSError, TemplateError):
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return read(folder, place)
