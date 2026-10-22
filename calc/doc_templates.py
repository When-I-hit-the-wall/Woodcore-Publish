"""Document templates -- the «templates de fond», content templates: what a new Convention d'utilisation (CU), Base de projet (BP) or Rapport de statique (RS) is made from -- its sections and the text they start with.

A project template (calc/templates.py) is the skeleton of a whole project, and makes the report a new project starts with; since v0.114 the report has content templates of its own beside it, as the two other documents have -- chosen as a project's report is made (calc/project_template.py) and what a report is saved as. A **document template** is the skeleton of one document: a folder under `templates/documents/<mode>/<folder>/` holding a `template.json` (schemas/document-template.schema.json: the mode, the name and description in the three languages, the languages the template exists in) and, for each language, a folder that is **exactly the document's own folder** -- the entry `.typ` (the only `.typ` at its top, named after the document in that language), its `structure.json` (calc/structure.py) and `Sections/<id>.typ`, one file per lowest-level section.

**The report's** language folder is the report's own folder: its entry `Statischer Rapport.typ` -- named so in every language, as a project names it (documents.RS_ENTRY) -- and `Sections/NNN-<name>.typ`, numbered in the order they print, which is the order of the entry's `#include "Sections/…"` lines; a line commented out is a section that is not printed. It has no structure.json: the report keeps its order and its state in its include lines (calc/structure.py `tree`, calc/templates.py `sync_includes`), and `check` holds that every include names a file there and every file there is included.

`instantiate` copies the folder of a project's language into the document's folder, names the entry file what the project calls it, and writes the structure block of that entry from the copied structure.json -- so a document made from a template is laid out as its structure says, whatever the template's own entry file carried. It never overwrites: a file already there stops the copy before anything is written.

What a template sets down is a document's sections and the text they start with. The files are **copied**, not shared: after the copy a document's sections are the engineer's own, and what stays synchronised between documents is only what lies between shared tags (calc/structure.py reads them, calc/sharing.py keeps the copies in step).

**Three places**, as a project template has (calc/templates.py), each a folder `documents/` holding `<mode>/<folder>/`, and a template is named `<place>:<mode>/<folder>`:

* **builtin** -- `templates/documents/` beside the program, read only: `builtin:cu/standard`, `builtin:bp/standard`, `builtin:rs/standard`;
* **user** -- `documents/` inside the engineer's own folder of templates (`%APPDATA%\\Woodcore\\templates\\documents\\`, calc/usersettings.py `templates_dir`): `user:cu/<folder>`;
* **office** -- `documents/` inside the folder the settings name for the office's shared templates (`templates.shared_folder`, what calc/templates.py calls the place `shared` -- `shared:` is read as `office:`): `office:cu/<folder>`.

A folder `documents/` holds no `template.json` of its own, so calc/templates.py, which lists a place's folders that carry one, never takes it for a project template.

**Saving a document as a template** (`save_from_document`, the engineer's «Enregistrer comme modèle…» of the «Structure document» tab): the document's folder of a project laid out in three documents -- its entry `.typ`, its `structure.json` **with the enabled flags as they stand**, and each section file **as the engineer wrote it** -- copied into `<place>/documents/<mode>/<folder>/<language>/`, the language the project's document is written in, with a `template.json` naming it in that language. What is left out is what is not the document: `Sections/archives/`, a PDF or a preview, the journal (a document's history is not its skeleton), the pictures and every file a section does not list. Such a template usually exists in one language, and is then offered only for a project in that language (`list_templates(language=)`); saving the same folder again in another language adds that language to it (`overwrite=True`), which is how an engineer builds the three. **Nothing is written before everything is checked, and what is replaced is never deleted**: the template made is staged and read back by `check` first, and a language folder an overwrite replaces, like a template `delete` takes away, is moved into `<place>/documents/archives/`.

**Shared sections.** A section shared between documents carries `// woodcore:shared <id>` tags in its file and `shared_with` in its structure.json (calc/sharing.py). A saved template keeps both as they are, and `instantiate` copies both -- so a template made from a project that shares its live loads between the two documents shares them again in a new project whose other document carries the same id. **The tags are the truth** (calc/sharing.py `reconcile`): two files carrying one id are one shared block, and a `shared_with` whose other side does not hold a copy is a flag that says nothing. `instantiate(siblings=...)` keeps `shared_with` only for the documents a new project has (a section shared with the report, in a project whose report has no such file, is not shared), and `settle_sharing(here)` writes every flag again from the tags once the documents are there -- the one place a mix of templates, a user's convention with the builtin base de projet, is brought to agree.

There is no Qt in this file.
"""

import json
import os
import re
import shutil
import time
from pathlib import Path

import engine
import project
import structure
import typst_paths
import validation

FILE = "template.json"
FORMAT = "woodcore-document-template"
SCHEMA_VERSION = "1.0"
# The documents laid out by a structure.json: what the window offers a template for when a project is created (calc/tools/home_page.py) and saves one from in the structure tab. The report is not among them: it has content templates too (ALL_MODES), made and saved by the functions of this module that take a mode, and chosen as a document is made from the «Projet» tab (project_template.create_document).
MODES = structure.MODES
# Every document a content template exists for, the report included: what every function of this module that takes a mode accepts.
ALL_MODES = structure.SHARE_MODES
LANGUAGES = structure.LANGUAGES
BUILTIN_DIR = Path(__file__).resolve().parent.parent / "templates" / "documents"
# The three places, in the order a list shows them. `shared` -- what calc/templates.py calls the office's folder -- is read as `office`.
PLACES = ("builtin", "user", "office")
PLACE_ALIASES = {"shared": "office"}
# Where a place keeps what it removes and what a saved template replaces: `<place>/documents/archives/`. Beside the `<mode>/` folders and not inside one, so a list of a mode's templates never meets it.
ARCHIVES = "archives"
# The folder a template is written into before it is moved to its place -- beside the `<mode>/` folders, where no list looks.
STAGING = ".saving"
# The folder the template every mode ships is in (`builtin:cu/standard`).
STANDARD = "standard"
# What Windows refuses in a file's name: the entry file of a document is one.
_REFUSED_CHARS = '<>:"/\\|?*'
# A section file of the report: `001-einleitung.typ` -- its number, three digits or more, then its name, as calc/templates.py numbers them.
REPORT_SECTION = re.compile(r"^(\d{3,})-([0-9A-Za-z][0-9A-Za-z_-]*)\.typ$")
# Every refusal a function of this module states, by `code`: a window writes its own sentence for each. An error raised by an older function states none (""), its English sentence being all there is to it.
CODES = (
    "bad_mode", "bad_language", "bad_place", "bad_folder", "read_only", "no_folder", "place_taken",
    "no_such_document", "no_entry", "structure_unreadable", "section_missing", "entry_unreadable",
    "no_name", "name_is_builtin", "name_taken", "exists", "not_a_template", "mode_mismatch",
    "no_such_template", "template_unusable", "language_missing", "invalid", "write_failed",
    "not_a_folder", "no_template", "project_template", "already_mine",
)


class DocTemplateError(validation.ValidationError):
    """A document template that cannot be read or used, or an instantiation, a save or a delete that cannot be made, said by name. A ValidationError, so whatever catches a defect of a source catches this.

    The functions that save and delete (and `instantiate`'s refusals of a mode, a language and a template that cannot be used) state a `code` -- one of CODES -- and the `values` the refusal is about (`folder`, `place`, `languages` …), beside the English sentence, as calc/structure.py's StructureError does: the window writes its own sentence for the code.
    """

    def __init__(self, message="", code="", **values):
        super().__init__(message)
        self.code = code
        self.values = values


def _refuse(code, message, **values):
    raise DocTemplateError(message, code, **values)


def place_name(place):
    """`place` as one of PLACES -- `shared`, calc/templates.py's word for the office's folder, read as `office`. Raises DocTemplateError (`bad_place`) for any other."""
    place = PLACE_ALIASES.get(place, place)
    if place not in PLACES:
        _refuse("bad_place", f"unknown place of document templates {place!r} -- expected one of {', '.join(PLACES)}", place=place)
    return place


def _read_json(path):
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


# --- one template --------------------------------------------------------------------------

class DocTemplate:
    """One document template: its place, its mode, its folder, what its template.json says, and -- where it cannot be used -- why (`error`, "" for a sound one)."""

    def __init__(self, place, mode, folder, meta=None, error=""):
        self.place = place
        self.mode = mode
        self.folder = Path(folder)
        self.meta = meta if isinstance(meta, dict) else {}
        self.error = error
        # What `save_from_document` found worth saying about the template it made and did not refuse for: engine.Notes, [] for a template that was read.
        self.notes = []

    @property
    def ref(self):
        return f"{self.place}:{self.mode}/{self.folder.name}"

    @property
    def read_only(self):
        return self.place == "builtin"

    @property
    def languages(self):
        value = self.meta.get("languages")
        return [lang for lang in value if lang in LANGUAGES] if isinstance(value, list) else []

    def _text(self, key, lang):
        texts = self.meta.get(key)
        if not isinstance(texts, dict):
            return ""
        return str(texts.get(lang) or texts.get("en") or next(iter(texts.values()), ""))

    def name(self, lang="fr"):
        """The template's name in `lang` -- in English, then in any language it has, where it has none in `lang`; its folder's name where it states none."""
        return self._text("name", lang) or self.folder.name

    def description(self, lang="fr"):
        return self._text("description", lang)

    def language_dir(self, lang):
        """The folder of the template in `lang`: the document's folder as it will be copied."""
        return self.folder / lang

    def entry_file(self, lang):
        """The entry `.typ` of the template in `lang` -- the only `.typ` at the top of its language folder -- or None where there is not exactly one."""
        found = sorted(p for p in self.language_dir(lang).glob("*.typ") if p.is_file())
        return found[0] if len(found) == 1 else None

    def structure_file(self, lang):
        """The structure.json of the template in `lang` -- a CU's or a BP's; the report's template has none."""
        return self.language_dir(lang) / structure.FILE

    def __repr__(self):
        return f"DocTemplate({self.ref!r})"


def report_includes(text):
    """[(file name, printed)] of the `#include "Sections/…"` lines of a report's entry file `text`, in order -- a line commented out is a section not printed. calc/templates.py's own pattern, so the two agree on what a section's line is."""
    import templates
    out = []
    for line in text.splitlines():
        found = templates._INCLUDE.match(line)
        if found:
            out.append((found.group(2), not found.group(1).strip().startswith("//")))
    return out


def report_stem(name):
    """What a report's section is called without its number: `001-einleitung.typ` -> `einleitung` -- how a report and a template of it are compared. The stem of the file where it carries no number."""
    found = REPORT_SECTION.match(name)
    return found.group(2) if found else Path(name).stem


def _check_report(template, lang, folder, entry):
    """The report's half of `check` for the language folder `folder`: a `Sections/` holding the section files only, each named `NNN-<name>.typ`, each included once by the entry and every include naming one of them, no name twice once its number is taken off."""
    with open(entry, encoding="utf-8", newline="") as handle:
        includes = report_includes(handle.read())
    present = sorted(p.name for p in (folder / structure.SECTIONS_DIR).glob("*.typ")) if (folder / structure.SECTIONS_DIR).is_dir() else []
    others = sorted(p.relative_to(folder).as_posix() for p in (folder / structure.SECTIONS_DIR).rglob("*") if p.is_file() and p.parent != folder / structure.SECTIONS_DIR) if (folder / structure.SECTIONS_DIR).is_dir() else []
    if others:
        raise DocTemplateError(f"{folder}: {', '.join(others)} lies in a folder inside Sections/ -- a report's template holds its section files and nothing else")
    bad = [name for name in present if not REPORT_SECTION.match(name)]
    if bad:
        raise DocTemplateError(f"{folder}: {', '.join(bad)} is not named NNN-<name>.typ, as a report's section is")
    names = [name for name, _printed in includes]
    twice = sorted({name for name in names if names.count(name) > 1})
    if twice:
        raise DocTemplateError(f"{entry}: includes {', '.join(twice)} more than once")
    missing = [name for name in names if name not in present]
    if missing:
        raise DocTemplateError(f"{entry}: includes Sections/{missing[0]}, which is not there")
    orphans = [name for name in present if name not in names]
    if orphans:
        raise DocTemplateError(f"{folder}: Sections/{', Sections/'.join(orphans)} is in Sections/ and no #include of the entry names it")
    stems = [report_stem(name) for name in present]
    clash = sorted({stem for stem in stems if stems.count(stem) > 1})
    if clash:
        raise DocTemplateError(f"{folder}: two sections are called {clash[0]!r} once their number is taken off")


def check(template):
    """Raises DocTemplateError where `template` cannot make a document: its template.json not of the schema, a mode that is not its folder's, a language it says it has and has no folder, name or entry file for, a structure.json that is not valid or is another document's, a leaf whose file is not there, a file in `Sections/` no leaf names, or an entry file whose structure tags Woodcore cannot read. A report's template (mode `rs`) has no structure.json and is checked by its include lines instead (`_check_report`)."""
    meta, where = template.meta, template.folder / FILE
    try:
        validation.validate_structure(meta, "document-template")
    except validation.ValidationError as exc:
        raise DocTemplateError(f"{where}: {exc}") from None
    if meta["mode"] != template.mode:
        raise DocTemplateError(f"{where}: mode is {meta['mode']!r} and the template lies in the folder of {template.mode!r}")
    languages = meta["languages"]
    if not languages or len(set(languages)) != len(languages):
        raise DocTemplateError(f"{where}: languages must list at least one language, each once")
    for lang in languages:
        if not str(meta["name"].get(lang, "")).strip():
            raise DocTemplateError(f"{where}: the template exists in {lang} and has no name in {lang}")
        if "description" in meta and not str(meta["description"].get(lang, "")).strip():
            raise DocTemplateError(f"{where}: the template has a description and none in {lang}, a language it exists in")
        folder = template.language_dir(lang)
        if not folder.is_dir():
            raise DocTemplateError(f"{where}: the template exists in {lang} and has no folder {lang}/")
        entry = template.entry_file(lang)
        if entry is None:
            raise DocTemplateError(f"{folder}: a document template has exactly one .typ at the top of a language folder, its entry file")
        if template.mode == "rs":
            _check_report(template, lang, folder, entry)
            continue
        try:
            source = structure.read(template.structure_file(lang))
        except validation.ValidationError as exc:
            raise DocTemplateError(f"{folder}: {exc}") from None
        if source["document"] != template.mode:
            raise DocTemplateError(f"{template.structure_file(lang)}: is the structure of the document {source['document']!r} and this template makes {template.mode!r}")
        named = set()
        for node, file in structure.named_files(source):     # the sections' files, and the chapters' in an absolute document
            named.add(file)
            if not (folder / file).is_file():
                raise DocTemplateError(f"{folder}: the section {node['id']!r} names {file}, which is not there")
        present = {p.relative_to(folder).as_posix() for p in (folder / structure.SECTIONS_DIR).rglob("*.typ")}
        orphans = sorted(present - named)
        if orphans:
            raise DocTemplateError(f"{folder}: {', '.join(orphans)} is in Sections/ and no section of structure.json names it")
        with open(entry, encoding="utf-8", newline="") as handle:
            text = handle.read()
        blocks, problems = structure.pair_tags(text)
        if problems or sum(1 for b in blocks if b.kind == "structure") != 1:
            raise DocTemplateError(f"{entry}: must carry exactly one woodcore:structure block with no tag problem" + (f" -- {'; '.join(map(str, problems))}" if problems else ""))


def read(folder, mode, place="builtin"):
    """The template in `folder`, read and checked -- one that cannot be used carries its reason in `error` rather than raising, so a list of templates still shows it."""
    folder = Path(folder)
    try:
        meta = _read_json(folder / FILE)
    except FileNotFoundError:
        return DocTemplate(place, mode, folder, {}, f"{folder}: no {FILE}")
    except (OSError, ValueError) as exc:
        return DocTemplate(place, mode, folder, {}, f"{folder / FILE}: cannot be read ({exc})")
    template = DocTemplate(place, mode, folder, meta)
    if not isinstance(meta, dict):
        template.error = f"{folder / FILE}: not an object"
        return template
    try:
        check(template)
    except DocTemplateError as exc:
        template.error = str(exc)
    return template


# --- the places and the list -----------------------------------------------------------------

def place_dir(place, settings=None):
    """The folder of document templates of `place`: `templates/documents/` for builtin, `documents/` inside the engineer's own folder of templates for user, and inside the office's shared folder for office -- None for office where the settings name no folder. `settings` are Woodcore's preferences (calc/usersettings.py), read where not given. The folder may not exist yet: a place holds nothing until a template is saved there."""
    place = place_name(place)
    if place == "builtin":
        return BUILTIN_DIR
    import templates
    root = templates.place_dir("user" if place == "user" else "shared", settings)
    return None if root is None else Path(root) / "documents"


def _places(settings=None):
    """(place, folder of documents' templates) of every place there is, builtin first, then the engineer's own, then the office's where the settings name a folder."""
    out = [("builtin", BUILTIN_DIR)]
    for place in ("user", "office"):
        root = place_dir(place, settings)
        if root is not None:
            out.append((place, root))
    return out


def _check_mode(mode):
    if mode not in ALL_MODES:
        _refuse("bad_mode", f"mode {mode!r} -- expected one of {', '.join(ALL_MODES)}", mode=mode)


def _check_language(language):
    if language not in LANGUAGES:
        _refuse("bad_language", f"language {language!r} -- expected one of {', '.join(LANGUAGES)}", language=language)


def list_templates(mode=None, language=None, settings=None):
    """Every document template of every place, builtin first, then the engineer's own, then the office's, each place in the order of its folders' names -- of `mode` only, where one is given, and of the ones a project written in `language` can be made from where one is given: a template is offered only for the languages it has, and one that cannot be used has none. A folder holding no template.json is not a template and is left out; one whose template.json is wrong is listed, its `error` saying why -- unless `language` is asked for, which asks for what can be used. (Not `list`: a module that defines `list` has no `list` of its own to call.)"""
    if mode is not None:
        _check_mode(mode)
    if language is not None:
        _check_language(language)
    out = []
    for place, root in _places(settings):
        for kind in ([mode] if mode else ALL_MODES):
            base = root / kind
            if not base.is_dir():
                continue
            for folder in sorted(base.iterdir(), key=lambda p: p.name.lower()):
                if folder.is_dir() and (folder / FILE).is_file():
                    found = read(folder, kind, place)
                    if language is None or (not found.error and language in found.languages):
                        out.append(found)
    return out


def default_ref(mode):
    """The reference of the template a new document of `mode` is made from unless another is chosen: the builtin standard one."""
    return f"builtin:{mode}/{STANDARD}"


def _named(name, mode, settings):
    """(candidates, everything there is) for `name` -- the reference form, folder or name `find` documents -- the candidates in the order a bare name is resolved in: the engineer's own templates first, then the office's, then the builtin ones, as calc/templates.py resolves a project template's. A sound template before one that cannot be used, where a bare name matches both."""
    name = (name or "").strip() or (default_ref(mode) if mode else "")
    place, colon, rest = name.partition(":")
    place = PLACE_ALIASES.get(place.lower(), place.lower()) if colon else None
    if place in PLACES:
        name = rest
    else:
        place = None
    kind, slash, folder = name.partition("/")
    if slash and kind.lower() in ALL_MODES:
        mode, name = kind.lower(), folder
    wanted = name.strip().lower()
    found = list_templates(mode, settings=settings)
    order = {"user": 0, "office": 1, "builtin": 2}
    candidates = sorted((t for t in found if (place is None or t.place == place)
                         and wanted in {t.folder.name.lower(), *(t.name(lang).lower() for lang in LANGUAGES)}),
                        key=lambda t: (bool(t.error), order[t.place]))
    return name, candidates, found


def find(name, mode=None, settings=None):
    """The template `name` names: `builtin:cu/standard`, `user:cu/<folder>`, `office:cu/<folder>` (`shared:` for `office:`), `cu/standard`, or -- with `mode` -- the folder `standard` alone, or its name in some language. A mode the name itself carries (`bp/standard`) is the mode looked in, whatever `mode` says: `instantiate` then refuses the mismatch by name, where a search in the wrong mode would only say it found nothing. A bare name is looked for in the engineer's own templates first, then the office's, then the builtin ones.

    Raises DocTemplateError (`no_such_template`) naming those there are where none is, or (`template_unusable`) the reason where the one found cannot be used."""
    name, candidates, found = _named(name, mode, settings)
    if not candidates:
        names = ", ".join(f"{t.name('en')} ({t.ref})" for t in found) or "none"
        _refuse("no_such_template", f"no document template {name!r} -- there are: {names}", name=name)
    if candidates[0].error:
        _refuse("template_unusable", candidates[0].error, ref=candidates[0].ref)
    return candidates[0]


# --- instantiating one ------------------------------------------------------------------------

def _check_entry_name(entry_name):
    """`entry_name` as the entry file's name: one file name and not a path, `.typ` added where left out."""
    name = (entry_name or "").strip()
    if name.lower().endswith(".typ"):
        stem = name[:-4]
    else:
        stem, name = name, name + ".typ"
    if not stem.strip() or stem != stem.strip() or any(ch in _REFUSED_CHARS or ord(ch) < 32 for ch in stem) or stem.endswith("."):
        raise DocTemplateError(f"{entry_name!r} is not the name of a document's entry file -- one file name, nothing Windows refuses in it")
    return name


def _restrict_sharing(path, keep):
    """The structure.json at `path` with each section's `shared_with` kept only for the documents in `keep`, written back only where something changed."""
    held = structure.read(path)
    changed = False
    for node, _depth in structure.leaves(held):
        listed = node.get("shared_with", [])
        kept = [mode for mode in listed if mode in keep]
        if kept != listed:
            changed = True
            if kept:
                node["shared_with"] = kept
            else:
                node.pop("shared_with", None)
    if changed:
        structure.write(path, held)


def instantiate(mode, language, target_dir, entry_name=None, template=None, siblings=None):
    """A new document of `mode` written in `language`, made from `template` (a DocTemplate or its reference; the builtin standard one by default) into the folder `target_dir`. Returns the entry file's path.

    The language folder of the template is copied into `target_dir` -- made where it is not there -- and the entry file is named `entry_name` (`.typ` added where left out; the template's own name where none is given); the structure block of that entry is then written from the copied structure.json (`structure.sync_entry`). `template.json` is not copied: it describes the template and not the document. A template of the engineer's or the office's is made into a document exactly as a builtin one is, in the languages it has -- a project in another language is refused (`language_missing`), naming them.

    **Nothing is overwritten.** A file the copy would write and that is there already stops it before any file is written, naming it; and a copy that fails midway removes what it wrote, so a folder is never left half a document.

    **Sharing.** The section files are copied with their `// woodcore:shared` tags and structure.json with its `shared_with`, as the template has them -- so a template that shares its live loads with the other document shares them again where that document carries the same id. `siblings`, where given -- the documents the new project has besides this one, `("bp", "rs")` -- keeps each section's `shared_with` only for those: a section shared with a document the project does not have is not shared. The tags stay, and `settle_sharing` writes every flag again from them once the documents are all there.

    **The report** (`rs`) is copied the same way -- its entry, named `entry_name` (the template's own, `Statischer Rapport.typ`, where none is given), and its `Sections/` -- and has no structure block to write: its include lines are the template's as they stand. `siblings` says nothing to it, a report keeping no `shared_with`.
    """
    _check_mode(mode)
    _check_language(language)
    if siblings is not None:
        siblings = tuple(siblings)
        bad = [m for m in siblings if m not in structure.SHARE_MODES]
        if bad:
            _refuse("bad_mode", f"siblings {', '.join(map(repr, bad))} -- expected some of {', '.join(structure.SHARE_MODES)}", mode=bad[0])
    if not isinstance(template, DocTemplate):
        template = find(template or default_ref(mode), mode)
    if template.error:
        _refuse("template_unusable", template.error, ref=template.ref)
    if template.mode != mode:
        _refuse("mode_mismatch", f"{template.ref} makes the document {template.mode!r}, and {mode!r} was asked for", ref=template.ref, mode=mode)
    if language not in template.languages:
        _refuse("language_missing", f"{template.ref} exists in {', '.join(template.languages)} and not in {language}",
                ref=template.ref, language=language, languages=list(template.languages))
    source = template.language_dir(language)
    template_entry = template.entry_file(language)
    entry_name = _check_entry_name(entry_name) if entry_name else template_entry.name
    target = Path(target_dir)

    copies = []
    for path in sorted(source.rglob("*")):
        if path.is_file():
            relative = path.relative_to(source)
            copies.append((path, target / (entry_name if path == template_entry else relative)))
    taken = [dest for _src, dest in copies if dest.exists()]
    if taken:
        raise DocTemplateError(f"{target}: {', '.join(d.relative_to(target).as_posix() for d in taken[:5])} is there already -- a document is never written over another")

    made_dirs, made_files = [], []
    # a template writes what configures the documents at the root, `/commands.typ`; in a project laid out by folders it lies in 000-Typst-Config/, and each .typ is written naming it there (issue #64) -- as it is copied, one write per file: a file just written and written again is one a sync client may still hold
    here = _project_of(target)
    try:
        missing = [p for p in [target, *target.parents] if not p.exists()]
        target.mkdir(parents=True, exist_ok=True)
        made_dirs.extend(missing)
        for src, dest in copies:
            if not dest.parent.exists():
                dest.parent.mkdir(parents=True)
                made_dirs.append(dest.parent)
            if here is not None and dest.suffix.lower() == ".typ":
                import documents
                dest.write_bytes(documents.relocate_config_text(here, typst_paths.read_text(src)).encode("utf-8"))
            else:
                shutil.copyfile(src, dest)
            made_files.append(dest)
        entry = target / entry_name
        if mode != "rs":
            if siblings is not None:
                _restrict_sharing(target / structure.FILE, set(siblings))
            structure.sync_entry(entry, target / structure.FILE, language)
    except BaseException:
        for file in reversed(made_files):
            file.unlink(missing_ok=True)
        for folder in sorted(set(made_dirs), key=lambda p: len(p.parts), reverse=True):
            try:
                folder.rmdir()
            except OSError:
                pass
        raise
    return entry


def _project_of(folder):
    """The project laid out by folders whose document `folder` is -- the one `.woodcore` in the folder above it --, or None: a document made outside a project, or in one laid out before, whose files keep the template's paths."""
    found = sorted(Path(folder).resolve().parent.glob("*" + project.EXTENSION))
    if len(found) != 1:
        return None
    try:
        here = project.Project.load(found[0])
    except (project.ProjectError, OSError):
        return None
    return here if here.has_folders else None


# --- sharing, once the documents are there -------------------------------------------------------

def settle_sharing(here):
    """Every `shared_with` of project `here`'s documents written again from the tags the section files carry (calc/sharing.py `reconcile`: **the tags are the truth**). What a new project made from templates of different origins needs once its documents are all there: a flag whose other side holds no copy goes, one both sides carry stays. Returns sharing's ReconcileResult -- what differed, what was written, what could not be read."""
    import sharing
    return sharing.reconcile(here, write=True)


# --- saving a document as a template --------------------------------------------------------------

def _move(source, target):
    """`source` -- a file or a folder -- moved to `target`, tried again a few times on the PermissionError the sync client of NextCloud gives while it holds what it has just seen written."""
    for attempt in range(6):
        try:
            return os.replace(source, target)
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.1 * (attempt + 1))


def _write_json(path, meta):
    """`meta` written as a template.json, beside itself and moved into place: LF, two-space indent, the languages' keys in the order of LANGUAGES."""
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    _move(temporary, path)


def _texts(value, language, what):
    """{language: text} of `value` -- a string is the text in `language`, a dict gives the texts of some of the languages -- each stripped, blanks left out, in the order of LANGUAGES. A name is one line, a description may have several."""
    code = "no_name" if what == "name" else "invalid"
    if value is None:
        return {}
    if isinstance(value, str):
        value = {language: value}
    if not isinstance(value, dict):
        _refuse(code, f"a template's {what} is a text, or a text for each language -- not {value!r}")
    extra = sorted(set(value) - set(LANGUAGES))
    if extra:
        _refuse("bad_language", f"the {what} is given in {', '.join(map(repr, extra))} -- expected some of {', '.join(LANGUAGES)}", language=extra[0])
    out = {}
    for lang in LANGUAGES:
        text = value.get(lang)
        if text is not None and not isinstance(text, str):
            _refuse(code, f"a template's {what} in {lang} is a text -- not {text!r}")
        text = (text or "").strip()
        if not text:
            continue
        if what == "name" and any(ord(ch) < 32 for ch in text):
            _refuse("no_name", f"a template's name is one line -- the name in {lang} carries a line break or another control character", language=lang)
        out[lang] = text
    return out


def _fill(texts, languages):
    """`texts` with a text for each of `languages` -- the first one there is where one is missing, a description in another language being better than none (a template that has descriptions must have one in each language it exists in, which `check` holds) -- in the order of LANGUAGES."""
    texts = {lang: text for lang, text in texts.items() if isinstance(text, str) and text.strip()}
    if not texts:
        return {}
    first = next(iter(texts.values()))
    return {lang: texts.get(lang, first) for lang in LANGUAGES if lang in texts or lang in languages}


def _meta(mode, names, descriptions, languages):
    meta = {"schema_version": SCHEMA_VERSION, "format": FORMAT, "mode": mode, "name": {lang: names[lang] for lang in LANGUAGES if lang in names}}
    filled = _fill(descriptions, languages)
    if filled:
        meta["description"] = filled
    meta["languages"] = [lang for lang in LANGUAGES if lang in languages]
    return meta


def _check_folder(folder):
    """`folder` stripped, as a template's folder: one folder and not a path, and nothing Windows refuses in a name -- or a DocTemplateError (`bad_folder`)."""
    import templates
    cleaned = (folder or "").strip()
    refused = sorted({ch for ch in cleaned if ch in '<>:"|?*' or ord(ch) < 32})
    if not cleaned:
        reason = "a template's folder needs a name"
    elif "/" in cleaned or "\\" in cleaned:
        reason = f"a template's folder is one folder and not a path: {folder!r} carries a separator"
    elif cleaned in (".", ".."):
        reason = f"{folder!r} is not the name of a folder"
    elif refused:
        reason = "a template's folder cannot carry " + ", ".join(repr(ch) for ch in refused) + " -- Windows refuses it in a name"
    elif cleaned.endswith("."):
        reason = f"{folder!r} ends in a dot, which Windows takes off a folder's name"
    elif cleaned.split(".")[0].upper() in templates.RESERVED_NAMES:
        reason = f"{folder!r} is a name Windows reserves for a device"
    else:
        return cleaned
    _refuse("bad_folder", reason, folder=folder)


def _stamp():
    """The `yymmdd-hhmmss` an archived template is named after."""
    return time.strftime("%y%m%d-%H%M%S")


def _archive_target(root, label):
    """Where what is taken out of `root` goes: `<root>/archives/<yymmdd-hhmmss>-<label>`, and `-2`, `-3` ... after the label where that is taken -- two templates removed in one second."""
    archives = Path(root) / ARCHIVES
    stamp = _stamp()
    target = archives / f"{stamp}-{label}"
    number = 2
    while target.exists():
        target = archives / f"{stamp}-{label}-{number}"
        number += 1
    return target


def _existing_meta(target, mode):
    """The template.json of the template folder `target`, which an overwrite writes into -- or a DocTemplateError: a folder that is no template of this module (`not_a_template`) is not one to write into, and another mode's (`mode_mismatch`) is another document's."""
    target = Path(target)
    try:
        with open(target / FILE, encoding="utf-8-sig") as handle:
            meta = json.load(handle)
    except (OSError, ValueError) as exc:
        _refuse("not_a_template", f"{target} is there and is no document template ({exc}) -- it is not written over", folder=str(target))
    if not isinstance(meta, dict) or not isinstance(meta.get("languages"), list):
        _refuse("not_a_template", f"{target / FILE} is not the template.json of a document template -- the folder is not written over", folder=str(target))
    if meta.get("mode") != mode:
        _refuse("mode_mismatch", f"{target} is a template of the document {meta.get('mode')!r}, and {mode!r} is being saved", folder=str(target), mode=mode)
    return meta


def _merged_meta(old, mode, names, descriptions, language):
    """The template.json of a template that exists already, once `language` is saved into it: its languages with this one, its names and descriptions with the ones given."""
    languages = [lang for lang in LANGUAGES if lang in old["languages"] or lang == language]
    name = {lang: text for lang, text in (old.get("name") or {}).items() if isinstance(text, str) and text.strip()}
    name.update(names)
    description = {lang: text for lang, text in (old.get("description") or {}).items() if isinstance(text, str) and text.strip()}
    description.update(descriptions)
    return _meta(mode, name, description, languages)


def _notes_of(texts):
    """The engine.Notes a saved template carries: {file: text} of everything copied in, read for what a document made from it would miss -- the files a section names that the template does not carry (a picture of `Images/`, a file read by the section), and a section file whose tags Woodcore cannot read, which its editors leave to text-only editing."""
    notes, files = [], {}
    for where, text in texts.items():
        for literal in typst_paths.literals(text):
            if literal.partial or literal.kind in ("import", "include", "project"):
                continue
            files.setdefault(literal.value, []).append(where)
    if files:
        named = {value: list(dict.fromkeys(where)) for value, where in files.items()}
        shown = "; ".join(f"{value} ({', '.join(where)})" for value, where in named.items())
        notes.append(engine.Note("template_files", f"the template names files it does not carry: {shown} -- a document made from it needs them in its project", files=named))
    for where, text in texts.items():
        if where.startswith(structure.SECTIONS_DIR + "/"):
            problems = structure.check_tags(text)
            if problems:
                notes.append(engine.Note("template_tags", f"{where}: Woodcore cannot read its tags ({'; '.join(problems)}) -- a document made from it edits that file as text only", file=where))
    return notes


def save_from_document(here, mode, name, description=None, place="user", folder=None, overwrite=False, settings=None, language=None):
    """Document `mode` (`cu`, `bp` or `rs`) of project `here` saved as a template in `place` (`user`, the engineer's own, or `office`) -- the engineer's «Enregistrer comme modèle…». Returns the DocTemplate, its `notes` saying what is worth knowing about it.

    `name` is the template's name in the document's language -- a text, or a {language: text} for some or all of them --, `description` likewise (optional). `folder` names the template's folder in its place, the name with what Windows refuses taken out where not given; the template is then `<place>:<mode>/<folder>`. `language` is the language the document is written in -- config.typ's `doc-lang`, else the engine's (structure.document_language), where not given -- and the one folder the template is made with.

    **What is copied** is the document: its entry `.typ`, its structure.json -- the enabled flags as they stand -- and the section file of each of its sections as the engineer wrote it, the shared tags and `shared_with` included. For the report (`rs`), which has no structure.json, its entry and the section file each of its `#include "Sections/…"` lines names, commented out or not. `Sections/archives/`, a PDF, a preview, the journal, the pictures, and any file no section lists are not the document and are left. Everything is checked **before anything is written** -- the document is there and readable, the name is a name, nothing is taken -- the template is staged beside its place and read back by `check`, and only then moved into it: a refusal or a failure leaves nothing behind.

    **An existing folder is refused** (`exists`) unless `overwrite`, which writes into it: its `<language>/` folder is replaced -- **the old one moved into `<place>/documents/archives/`, never deleted** -- or added where the template has not that language yet, which is how one template comes to exist in the three. The template.json then names the languages it has, with this name and description in this language and the others' as they were.

    Refusals carry a `code` (CODES): `bad_mode`, `bad_language`, `bad_place`, `read_only` (builtin), `no_folder` (no office folder in the settings), `place_taken`, `no_such_document`, `no_entry`, `structure_unreadable`, `section_missing`, `entry_unreadable`, `no_name`, `bad_folder`, `name_is_builtin`, `name_taken`, `exists`, `not_a_template`, `mode_mismatch`, `invalid`, `write_failed`.
    """
    import templates
    _check_mode(mode)
    place = place_name(place)
    if place == "builtin":
        _refuse("read_only", "the builtin document templates are read only -- save it among your own or the office's", place=place)
    root = place_dir(place, settings)
    if root is None:
        _refuse("no_folder", "no shared folder of templates is set (Paramètres → Modèles)", place=place)
    if not (here.has_modes and mode in here.modes):
        _refuse("no_such_document", f"{here.name} has no {mode!r} document to save -- only a project laid out in three documents has one", mode=mode)
    entry = here.document_typ(mode)
    if not entry.is_file():
        _refuse("no_entry", f"{entry}: the entry file of the {mode!r} document is not there", mode=mode)
    language = language or structure.document_language(here, mode)
    _check_language(language)
    names = _texts(name, language, "name")
    if not names.get(language):
        _refuse("no_name", f"a template needs a name in {language}, the language of the document", language=language)
    descriptions = _texts(description, language, "description")
    folder = _check_folder(folder if folder is not None and str(folder).strip() else templates.folder_name(names[language]))
    if (root / FILE).exists():
        _refuse("place_taken", f"{root} is a project template's folder -- a folder `documents` of templates there would lie inside it", place=place)
    ref = f"{place}:{mode}/{folder}"
    target = root / mode / folder

    mine = {text.lower() for text in names.values()}
    for other in list_templates(mode, settings=settings):
        if other.place == place and other.folder.name.lower() == folder.lower():
            continue
        if not mine & {other.name(lang).lower() for lang in LANGUAGES}:
            continue
        if other.place == "builtin":
            _refuse("name_is_builtin", f"{other.name('en')} is the name of a builtin template -- choose another", name=names[language])
        if other.place == place:
            _refuse("name_taken", f"{other.ref} is called that already -- a bare name must mean one template", name=names[language], ref=other.ref)
    previous = None
    if target.exists():
        if not overwrite:
            _refuse("exists", f"{ref} is there already -- saving over it asks for `overwrite`, which replaces its {language} folder and keeps the old one in archives/", ref=ref)
        previous = _existing_meta(target, mode)

    if mode == "rs":
        copies = _report_copies(here, entry)
    else:
        copies = _structured_copies(here, mode, entry)
    texts = {}
    for source, rel in copies:
        if rel.endswith(".typ"):
            try:
                texts[rel] = source.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                pass
    notes = _notes_of(texts)

    stage = root / f"{STAGING}-{os.getpid()}"
    staged = stage / folder
    shutil.rmtree(stage, ignore_errors=True)
    try:
        try:
            for source, rel in copies:
                destination = staged / language / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            _write_json(staged / FILE, _meta(mode, names, descriptions, [language]))
            made = read(staged, mode, place)
            if made.error:
                _refuse("invalid", f"the template made from {here.name}'s {mode} document cannot be used: {made.error}", error=made.error)
            (root / mode).mkdir(parents=True, exist_ok=True)
            if previous is None:
                _move(staged, target)
            else:
                _write_into(root, target, staged, mode, folder, language, _merged_meta(previous, mode, names, descriptions, language))
        except OSError as exc:
            _refuse("write_failed", f"the template could not be written: {exc}", error=str(exc))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    saved = read(target, mode, place)
    saved.notes = notes
    return saved


def _structured_copies(here, mode, entry):
    """[(source, relative path in the template)] of what a template of the CU or the BP of `here` copies: its entry, its structure.json and every file the structure names -- refused (`structure_unreadable`, `section_missing`, `entry_unreadable`) where it cannot be read whole."""
    structure_file = here.structure_file(mode)
    try:
        held = structure.read(structure_file)
    except validation.ValidationError as exc:
        _refuse("structure_unreadable", str(exc), mode=mode)
    if held["document"] != mode:
        _refuse("structure_unreadable", f"{structure_file}: is the structure of the document {held['document']!r} and {mode!r} is being saved", mode=mode)
    copies = [(entry, entry.name), (structure_file, structure.FILE)]
    missing = []
    for node, file in structure.named_files(held):
        source = here.document_dir(mode) / file
        if source.is_file():
            copies.append((source, file))
        else:
            missing.append(file)
    if missing:
        _refuse("section_missing", f"{structure_file}: names {', '.join(missing)}, which is not there -- a template of it could not be used", files=missing)
    with open(entry, encoding="utf-8", newline="") as handle:
        blocks, problems = structure.pair_tags(handle.read())
    if problems or sum(1 for b in blocks if b.kind == "structure") != 1:
        _refuse("entry_unreadable", f"{entry}: must carry exactly one woodcore:structure block with no tag problem" + (f" -- {'; '.join(map(str, problems))}" if problems else ""), file=str(entry))
    return copies


def _report_copies(here, entry):
    """[(source, relative path in the template)] of what a template of the report of `here` copies: its entry and the section file each include line names -- refused (`entry_unreadable`, `section_missing`) where it cannot be read whole, or where a section's name is not one a report's template can hold (`NNN-<name>.typ`)."""
    try:
        with open(entry, encoding="utf-8", newline="") as handle:
            includes = report_includes(handle.read())
    except (OSError, UnicodeDecodeError) as exc:
        _refuse("entry_unreadable", f"{entry}: could not be read -- {exc}", file=str(entry))
    copies = [(entry, entry.name)]
    missing, seen = [], set()
    for name, _printed in includes:
        if name in seen:
            continue
        seen.add(name)
        source = here.document_dir("rs") / structure.SECTIONS_DIR / name
        if source.is_file() and REPORT_SECTION.match(name):
            copies.append((source, f"{structure.SECTIONS_DIR}/{name}"))
        else:
            missing.append(f"{structure.SECTIONS_DIR}/{name}")
    if missing:
        _refuse("section_missing", f"{entry}: includes {', '.join(missing)}, which is not there or not named NNN-<name>.typ -- a template of it could not be used", files=missing)
    return copies


def _write_into(root, target, staged, mode, folder, language, meta):
    """The staged `language` folder put into the template folder `target` that exists, and its template.json written from `meta` -- the `language` folder it replaces moved into archives/ first, and **put back if anything after fails**."""
    archived = None
    placed = False
    try:
        old = target / language
        if old.exists():
            archived = _archive_target(root, f"{mode}-{folder}-{language}")
            archived.parent.mkdir(parents=True, exist_ok=True)
            _move(old, archived)
        _move(staged / language, old)
        placed = True
        _write_json(target / FILE, meta)
    except BaseException:
        if placed:
            shutil.rmtree(target / language, ignore_errors=True)
        if archived is not None:
            try:
                _move(archived, target / language)
            except OSError:
                pass
        raise


# --- taking one away ------------------------------------------------------------------------------

def delete(ref, settings=None):
    """The engineer's or the office's template `ref` (`user:cu/courte`, `office:bp/...`, or a DocTemplate) taken away -- **moved into `<place>/documents/archives/<yymmdd-hhmmss>-<mode>-<folder>`, never deleted**, which is the rule «Supprimer» follows everywhere in Woodcore. Returns where it went. A builtin template is refused (`read_only`); a reference that is not `<place>:<mode>/<folder>` -- a bare name could mean two -- or names none is `no_such_template`. A template that cannot be used can be taken away all the same."""
    if isinstance(ref, DocTemplate):
        template = ref
    else:
        place, colon, rest = (ref or "").strip().partition(":")
        place = PLACE_ALIASES.get(place.lower(), place.lower())
        kind, slash, folder = rest.partition("/")
        kind = kind.lower()
        if not colon or place not in PLACES or not slash or kind not in ALL_MODES or not folder.strip():
            _refuse("no_such_template", f"{ref!r} is not a document template's reference -- name it `<place>:<mode>/<folder>`, `user:cu/<folder>`", name=ref)
        found = [t for t in list_templates(kind, settings=settings) if t.place == place and t.folder.name.lower() == folder.strip().lower()]
        if not found:
            _refuse("no_such_template", f"no document template {ref!r}", name=ref)
        template = found[0]
    if template.read_only:
        _refuse("read_only", f"{template.ref} is a builtin template and cannot be deleted", ref=template.ref)
    root = template.folder.parent.parent
    target = _archive_target(root, f"{template.mode}-{template.folder.name}")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        _move(template.folder, target)
    except OSError as exc:
        _refuse("write_failed", f"{template.ref} could not be moved into archives/: {exc}", ref=template.ref, error=str(exc))
    return target


# --- bringing one in ----------------------------------------------------------------------------------

def import_folder(source, mode, replace=False, settings=None):
    """«Importer un dossier…» of the settings' «Modèles» page (v0.113): the document template of `mode` in the folder `source` -- a folder holding a template.json, like each `<mode>/<folder>` of an office's shared folder -- copied into the engineer's own place (`place_dir("user")`, `<user>/documents/<mode>/<folder>`) under its folder's name. Returns the DocTemplate as it now stands there.

    **Checked before anything is written**: `source` must be a folder (`not_a_folder`) holding a template.json (`no_template`) of a document template -- a project template's is refused (`project_template`), the page importing it under the report, and another document's (`mode_mismatch`, its own `document` among the values) -- that `check` finds sound (`invalid`), its folder's name a name (`bad_folder`), none of its names a builtin template's (`name_is_builtin`), and not one of the engineer's own already (`already_mine`). A template of that folder's name in his place is refused (`exists`) unless `replace`, which moves the old one into `<user>/documents/archives/` -- never deleted -- and puts it back if the copy then fails. The copy is staged beside the place and read back by `check` first, so a failure (`write_failed`) leaves nothing half copied."""
    _check_mode(mode)
    source = Path(source)
    if not source.is_dir():
        _refuse("not_a_folder", f"{source} is not a folder", folder=str(source))
    if not (source / FILE).is_file():
        _refuse("no_template", f"{source} holds no {FILE} -- it is not a template", folder=str(source))
    try:
        meta = _read_json(source / FILE)
    except (OSError, ValueError) as exc:
        _refuse("invalid", f"{source / FILE} cannot be read ({exc})", folder=str(source), error=str(exc))
    if isinstance(meta, dict) and meta.get("format") == "woodcore-template":
        _refuse("project_template", f"{source} is a project template, which makes the report -- not a document template", folder=str(source))
    if isinstance(meta, dict) and meta.get("mode") in ALL_MODES and meta["mode"] != mode:
        _refuse("mode_mismatch", f"{source} is a template of the document {meta['mode']!r}, and {mode!r} is being imported", folder=str(source), mode=mode, document=meta["mode"])
    found = read(source, mode, "user")
    if found.error:
        _refuse("invalid", found.error, folder=str(source), error=found.error)
    folder = _check_folder(source.name)
    root = Path(place_dir("user", settings))
    mine, there = root.resolve(), source.resolve()
    if there == mine or mine in there.parents or there in mine.parents:
        _refuse("already_mine", f"{source} is among the engineer's own templates already", folder=str(source))
    names = {found.name(lang).lower() for lang in found.languages}
    for builtin in list_templates(mode, settings=settings):
        if builtin.place == "builtin" and names & {builtin.name(lang).lower() for lang in LANGUAGES}:
            _refuse("name_is_builtin", f"{builtin.name('en')} is the name of a builtin template -- rename it in its {FILE} first", name=found.name(found.languages[0]))
    ref = f"user:{mode}/{folder}"
    target = root / mode / folder
    if target.exists() and not replace:
        _refuse("exists", f"{ref} is there already -- importing over it asks for `replace`, which keeps the old one in {ARCHIVES}/", ref=ref, folder=folder)
    stage = root / f"{STAGING}-{os.getpid()}"
    staged = stage / folder
    shutil.rmtree(stage, ignore_errors=True)
    try:
        try:
            stage.mkdir(parents=True)
            shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", ".git", FILE + ".tmp"))
            made = read(staged, mode, "user")
            if made.error:
                _refuse("invalid", made.error, folder=str(source), error=made.error)
            (root / mode).mkdir(parents=True, exist_ok=True)
            archived = None
            if target.exists():
                archived = _archive_target(root, f"{mode}-{folder}")
                archived.parent.mkdir(parents=True, exist_ok=True)
                _move(target, archived)
            try:
                _move(staged, target)
            except OSError:
                if archived is not None:
                    _move(archived, target)
                raise
        except OSError as exc:
            _refuse("write_failed", f"{source} could not be copied into the engineer's templates: {exc}", folder=str(source), error=str(exc))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return read(target, mode, "user")
