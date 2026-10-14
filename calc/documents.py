"""The three documents a project is written as, by name: what each is called in each language, the folder it lies in and its entry file, and the one spelling of the command line that compiles one (the engineer's request of 30.09.2026).

A project is laid out as a report alone -- every project until the three documents, and every project whose .woodcore states no `layout.typst_root` -- or in three documents: the **convention d'utilisation** (Nutzungsvereinbarung, SIA 260's service criteria agreement), the **base de projet** (Projektbasis, basis of design) and the **rapport de statique**, which is the report every project has had and keeps every name it had, being simply the third. Where each lies is calc/project.py's (`Project.document_typ`, `document_pdf`, `document_dir`); what each is called, and what a new project's folders are named, is this module's.

Three folders at the top of the project, numbered in that order and named in the project's language, exactly as MODE_FOLDERS writes them: `1_Nutzungsvereinbarung`, `2_Projektbasis`, `3_Statischer Bericht` in German, `1_Convention d'utilisation`, `2_Base de projet`, `3_Rapport de statique` in French, `1_Service criteria agreement`, `2_Basis of design`, `3_Statical report` in English. Offered when a project is created, and editable there: what a project's .woodcore states is what it reads from then on, so a name chosen once is never recomputed from this table.

Qt-free, and it reads no project of its own: a function that needs one is handed it, which is what lets the command line, the window, a preview and the migration all build their command lines here.
"""

from pathlib import PurePosixPath

import project

# The documents, in the order the window's drop-down offers them and their folders are numbered: calc/project.py's, named here once more so that a caller of this module need not import both.
MODES = project.MODES
LANGUAGES = ("de", "fr", "en")
DEFAULT_LANGUAGE = "de"

# What each document is called, in the words of SIA 260's own editions (French, German and English) for the first two: what the window's drop-down shows and what the folders and the entry files are named after.
MODE_NAMES = {
    "de": {"cu": "Nutzungsvereinbarung", "bp": "Projektbasis", "rs": "Statischer Bericht"},
    "fr": {"cu": "Convention d'utilisation", "bp": "Base de projet", "rs": "Rapport de statique"},
    "en": {"cu": "Service criteria agreement", "bp": "Basis of design", "rs": "Statical report"},
}
# Each document's number, which its folder begins with and which the navigation shows where it is folded to its icons.
MODE_NUMBERS = {"cu": 1, "bp": 2, "rs": 3}
# The folder each document of a new project lies in, at the top of the project, in the project's language -- written out rather than composed from MODE_NUMBERS and MODE_NAMES, these being the engineer's exact forms (tests/test_documents.py holds the two agreeing all the same).
MODE_FOLDERS = {
    "de": {"cu": "1_Nutzungsvereinbarung", "bp": "2_Projektbasis", "rs": "3_Statischer Bericht"},
    "fr": {"cu": "1_Convention d'utilisation", "bp": "2_Base de projet", "rs": "3_Rapport de statique"},
    "en": {"cu": "1_Service criteria agreement", "bp": "2_Basis of design", "rs": "3_Statical report"},
}
# The report's entry file, which keeps the name it has always had in every language: nothing of the report is renamed by its becoming the third document (the engineer's decision), and every route that names its PDF names it after this file (docs/conventions/build-and-release.md §12).
RS_ENTRY = "Statischer Rapport.typ"
# Each document's entry file in a new project: the convention d'utilisation and the base de projet named after the document in the project's language, the report after its own.
ENTRY_NAMES = {
    lang: {"cu": names["cu"] + ".typ", "bp": names["bp"] + ".typ", "rs": RS_ENTRY}
    for lang, names in MODE_NAMES.items()
}
# Each document's revision journal in the sources, one per document: calc/project.py's (`Project.journal_file_for`).
JOURNAL_FILES = project.JOURNAL_FILES
# The export's folder in a project of three documents, at its top and shared by the three: the engine copied into the project, the data it reads, and the stamps that say whether a document changed since its PDF.
GENERATED_FOLDER = "_woodcore"
# How a document's section imports the engine: from the Typst root in three documents, the one spelling valid in every document's folder and at every depth -- which is what lets one section be copied into another document -- and from the folder above in a report alone, whose sections lie in `Sections/` beside the entry file (docs/typst/api-conventions.md §10bis).
COMMANDS_FROM_ROOT = "/" + project.COMMANDS_FILE
COMMANDS_FROM_SECTIONS = "../" + project.COMMANDS_FILE


def language_of(lang):
    """`lang` where it is one of LANGUAGES, else German's -- the rule `templates.report_folder_for` follows for the report's folder."""
    return lang if lang in LANGUAGES else DEFAULT_LANGUAGE


def mode_name(mode, lang):
    """What document `mode` is called in `lang`: «Base de projet»."""
    return MODE_NAMES[language_of(lang)][mode]


def mode_choices(lang):
    """The documents as the window's drop-down offers them, in their order, as [(mode, name)] -- `[("cu", "Nutzungsvereinbarung"), ("bp", "Projektbasis"), ("rs", "Statischer Bericht")]` in German."""
    names = MODE_NAMES[language_of(lang)]
    return [(mode, names[mode]) for mode in MODES]


def folders_for(lang):
    """The folders a new project written in `lang` is offered, as {mode: folder} -- a copy, for a dialog to edit."""
    return dict(MODE_FOLDERS[language_of(lang)])


def _folder(mode, name):
    """`name` stripped, as the folder of document `mode` -- or a ProjectError naming the document and what is wrong with the name. The rule is the report's folder's own (templates.check_report_folder, v0.100): one folder and not a path, nothing Windows refuses in a name."""
    import templates   # here and not at the top: templates imports project, which this module is imported beside
    try:
        return templates.check_report_folder(name)
    except templates.TemplateError as exc:
        raise project.ProjectError(f"the folder of the {MODE_NAMES['en'][mode].lower()} ({name!r}): {exc}") from None


def _entry(mode, name):
    """`name` stripped, as the entry file of document `mode`: a file's name, ending in .typ, that lies in the document's folder."""
    cleaned = (name or "").strip()
    if not cleaned or "/" in cleaned or "\\" in cleaned or not cleaned.lower().endswith(".typ") or cleaned[:-4].strip() in ("", ".", ".."):
        raise project.ProjectError(
            f"the entry file of the {MODE_NAMES['en'][mode].lower()} ({name!r}) must be the name of a .typ file, "
            f"which lies in the document's own folder"
        )
    return cleaned


def modes_layout(folders, entries, rs_entry=None):
    """The layout of a project in three documents, in full, as its .woodcore is written with it (`project.write`, `project.full_layout`).

    `folders` names each document's folder: {mode: folder}, or a sequence of three in MODES' order -- the command line's `--names CU BP RS`. `entries` names the entry files of the convention d'utilisation and of the base de projet, {mode: file}, and the report's where it carries "rs"; `rs_entry` names the report's all the same, which is what a project created from a template or migrated passes, its report's entry file being the one its skeleton has. Each PDF is named after its entry file and lies beside it, as the report's has since v0.87. What the three share lies at the top of the project: the export (GENERATED_FOLDER), the pictures, and the sources and the archives where DEFAULT_LAYOUT keeps them.

    Each folder is checked as the report's folder is when it is typed (templates.check_report_folder) and the three must differ, compared as Windows compares names; a ProjectError says which is wrong before anything is created.
    """
    if not isinstance(folders, dict):
        folders = list(folders)
        if len(folders) != len(MODES):
            raise project.ProjectError(f"three folders are named, one per document ({', '.join(MODES)}) -- {len(folders)} were given")
        folders = dict(zip(MODES, folders))
    missing = [mode for mode in MODES if mode not in folders]
    if missing:
        raise project.ProjectError(f"no folder is named for {', '.join(missing)} -- a project in three documents has one per document")
    named = {mode: _folder(mode, folders[mode]) for mode in MODES}
    seen = {}
    for mode in MODES:
        other = seen.get(named[mode].casefold())
        if other is not None:
            raise project.ProjectError(
                f"the {MODE_NAMES['en'][other].lower()} and the {MODE_NAMES['en'][mode].lower()} are both given the "
                f"folder {named[mode]!r} -- each document lies in a folder of its own"
            )
        seen[named[mode].casefold()] = mode
    files = dict(entries or {})
    if rs_entry is not None:
        files["rs"] = rs_entry
    files.setdefault("rs", RS_ENTRY)
    for mode in ("cu", "bp"):
        if mode not in files:
            raise project.ProjectError(f"no entry file is named for {mode} -- the convention d'utilisation and the base de projet are each named after the document")
    layout = {"typst_root": "."}
    for mode in MODES:
        entry = PurePosixPath(named[mode]) / _entry(mode, files[mode])
        layout[project.ENTRY_KEYS[mode]] = entry.as_posix()
        layout[project.PDF_KEYS[mode]] = entry.with_suffix(".pdf").as_posix()
    layout.update({
        "generated": GENERATED_FOLDER,
        "images": project.IMAGES_FOLDER,
        "sources": project.DEFAULT_LAYOUT["sources"],
        "archives": project.DEFAULT_LAYOUT["archives"],
    })
    return project.full_layout(layout)


def layout_for(lang, folders=None):
    """The layout of a new project in three documents written in `lang`: its folders MODE_FOLDERS' for the language unless `folders` names others ({mode: folder}, a dialog's), its entry files ENTRY_NAMES'."""
    lang = language_of(lang)
    return modes_layout({**MODE_FOLDERS[lang], **(folders or {})}, ENTRY_NAMES[lang])


def compile_args(here, mode, flags=(), target=None, deps=None):
    """`typst compile`'s arguments for document `mode` of project `here`, the executable left out (project.typst_executable) -- **the one spelling of a document's command line**, for the command line, the window, a preview and the migration alike.

    `["compile", "--root", <Typst root>, *flags, "--deps", <deps>, "--deps-format", "json", <entry>, <target>]`: the root always stated, the project's own folder in three documents and the report's folder for a report alone -- the folder Typst takes for its root when it is given none, so a report alone compiles exactly as it did without it; `flags` the `--input` flags (cli.input_args); `--deps` only where `deps` names the file Typst writes what it read into (a JSON of `inputs` and `outputs`, each path absolute or from the folder Typst was started in -- every compile starts it in the Typst root), which is what says whether a document changed since its PDF; and **the entry file and the target last**, where every reader of a command line looks for them (tests/test_pdf_button.py reads the last two). `target` is the document's own PDF unless another is named -- a preview's, a level's in out/.
    """
    args = ["compile", "--root", str(here.typst_root), *flags]
    if deps is not None:
        args += ["--deps", str(deps), "--deps-format", "json"]
    return args + [str(here.document_typ(mode)), str(here.document_pdf(mode) if target is None else target)]


def commands_import(here=None):
    """The path a section imports the engine from: `/commands.typ` in a project of three documents, `../commands.typ` in a report alone -- and where no project is named, which is what every section has written until the three documents."""
    return COMMANDS_FROM_ROOT if here is not None and here.has_modes else COMMANDS_FROM_SECTIONS


def import_line(here=None):
    """The line a section starts with: `#import "/commands.typ": *` in a project of three documents, `#import "../commands.typ": *` in a report alone or where no project is named -- what build_reference's calls and Woodcore's copy buttons put above a call. In three documents an entry file starts with the same line; a report alone's entry file lies beside its commands.typ and imports it by its bare name."""
    return f'#import "{commands_import(here)}": *'
