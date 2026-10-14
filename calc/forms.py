"""Forms: the look of a project's three documents -- the *form* templates, against the *content* templates (calc/templates.py for a whole project, calc/doc_templates.py for a convention or a base).

The engineer's decision of 06.10.2026: Woodcore separates what a document **looks like** -- fonts, sizes, margins, how the headings and the sections are set, the layout of the title page, with no data in it -- from what it **says** -- the sections, the objects, their text. A **form** is the first, and it lives in a folder `Template/` at the project's Typst root (the project's own folder for a project in three documents):

* `Template/template.typ` defines `#let template(doc, lang: "de", region: "CH")`, the look, and any design token the title page needs (the BFH form exports its `sans`, `bfh-grey`, `bfh-yellow` and `muted`);
* `Template/form.json` says which form it is (`id`, `place`, `name`, `description`; schemas/form.schema.json);
* the assets the form uses -- a logo -- lie beside them, and `image("logo-bfh.png")` written in template.typ resolves from there;
* `config.typ`, at the root, **keeps only the document's language and the engineer's own adjustments** and calls the function (`config_text`): the engineer's `set text(...)` written in the place it marks wins over the form's, and survives the form being switched;
* `title.typ`, at the root, is **dedicated to the form**: plain Typst the engineer edits by hand -- the rows, the line breaks, the spacing --, imports the form's tokens from `/Template/template.typ`, and is replaced with it.

A form is a folder holding a `form.json`, a `template.typ` and a `title.typ`, in one of three places, as a template has: **builtin** (`templates/forms/` beside the program, read only: `neutral`, `compact`, `bfh`), **user** (`forms/` inside the engineer's folder of templates) and **shared** (`forms/` inside the folder the settings name for the office's). It is named `<place>:<folder>`.

`apply` switches a project's form: what is there -- `Template/`, `title.typ`, and `config.typ` where it is not already in the new format -- is moved into `<archives>/<yymmdd-hhmmss>-forme/` and never deleted, the form's `Template/` and `title.typ` are put in place, and `config.typ` is written in the new format keeping the project's `doc-lang` and `doc-region`, or left untouched where it is in it already, since it holds the engineer's adjustments. It is all or nothing: everything is checked and staged first, and a failure puts back what was moved.

There is no Qt in this file.
"""

import json
import os
import re
import shutil
import time
from pathlib import Path

import project
import templates
import validation

FILE = "form.json"
FORMAT = "woodcore-form"
SCHEMA_VERSION = "1.0"
TEMPLATE_FILE = "template.typ"
TITLE_FILE = project.TITLE_FILE
# The folder of a project the form lives in, at its Typst root.
TEMPLATE_DIR = project.TEMPLATE_FOLDER
PLACES = ("builtin", "user", "shared")
LANGUAGES = ("fr", "de", "en")
NEUTRAL = "neutral"
# Where a place keeps what it removes: `<place>/forms/archives/<yymmdd-hhmmss>-<id>`. It holds no form.json, so a list never takes it for a form.
ARCHIVES = "archives"
# The folder a form is staged in before it is moved into place -- beside the forms, where no list looks.
STAGING = ".forming"
# What a project's archives folder gets when a form is switched: `<yymmdd-hhmmss>-forme`.
ARCHIVE_LABEL = "forme"
# `#import "/Template/template.typ": template`: what makes a config.typ the new format.
_FORM_IMPORT = re.compile(r'^[ \t]*#import[ \t]+"/Template/template\.typ"', re.M)
_TEMPLATE_DEF = re.compile(r"^[ \t]*#let[ \t]+template[ \t]*\(", re.M)
_TITLE_DEF = re.compile(r"^[ \t]*#let[ \t]+title-page[ \t]*\(", re.M)
_LANG_VALUE = re.compile(r"^[A-Za-z-]*$")
# Every refusal, by `code`: a window writes its own sentence for each.
CODES = (
    "bad_place", "no_shared_folder", "read_only", "no_such_form", "form_unusable", "no_project_form", "no_name",
    "name_is_builtin", "not_a_folder", "no_form", "invalid", "already_mine", "exists", "write_failed",
)


class FormError(validation.ValidationError):
    """A form that cannot be read or used, or a switch, an import, an archive or a save that cannot be made, said by name. A ValidationError, so whatever catches a defect of a source catches this.

    `code` is one of CODES and `values` what the refusal is about (`folder`, `ref`, `name`, `error` …), beside the English sentence, as calc/doc_templates.py's DocTemplateError carries them: the window writes its own sentence for the code."""

    def __init__(self, message="", code="", **values):
        super().__init__(message)
        self.code = code
        self.values = values


def _refuse(code, message, **values):
    raise FormError(message, code, **values)


# --- the places -----------------------------------------------------------------------------

def place_dir(place, settings=None):
    """The folder of forms of `place` -- `templates/forms/` for builtin, `forms/` inside the engineer's folder of templates for user and inside the office's for shared -- or None for shared where the settings name no folder."""
    if place == "builtin":
        return templates.BUILTIN_DIR / "forms"
    if place not in PLACES:
        _refuse("bad_place", f"unknown place of forms {place!r} -- expected one of {', '.join(PLACES)}", place=str(place))
    settings = settings if settings is not None else templates._usersettings().read()
    root = templates.place_dir(place, settings)
    return None if root is None else Path(root) / "forms"


def _writable_root(place, settings):
    if place == "builtin":
        _refuse("read_only", "the builtin forms are read only -- save a project as a form to make your own")
    root = place_dir(place, settings)
    if root is None:
        _refuse("no_shared_folder", "no shared folder of templates is set (Paramètres → Chemins)")
    return root


# --- one form -------------------------------------------------------------------------------

class Form:
    """One form: a folder holding form.json, template.typ and title.typ. `error` says why it cannot be used, "" for a sound one. A form read out of a project's `Template/` (`current`) has the form.json the switch wrote there, whose `id` and `place` say which form it was made from."""

    def __init__(self, folder, place, meta=None, error=""):
        self.folder = Path(folder)
        self.place = place
        self.meta = meta if isinstance(meta, dict) else {}
        self.error = error

    @property
    def id(self):
        """What a caller names it by: the `id` its form.json states where it is a project's copy, else its folder's name -- `neutral`, `bfh`."""
        return str(self.meta.get("id") or self.folder.name)

    @property
    def ref(self):
        return f"{self.place}:{self.id}"

    def name(self, lang="fr"):
        """Its name in `lang`, else in English, else in the first language it has, else its id."""
        return templates._in_language(self.meta.get("name"), lang) or self.id

    def description(self, lang="fr"):
        """Its description in `lang`, else in English -- "" where it has none."""
        return templates._in_language(self.meta.get("description"), lang)

    @property
    def read_only(self):
        return self.place == "builtin"

    @property
    def template_typ(self):
        return self.folder / TEMPLATE_FILE

    @property
    def title_typ(self):
        return self.folder / TITLE_FILE

    def __repr__(self):
        return f"Form({self.ref!r})"


def check(form):
    """Raises FormError where `form` cannot be applied: its form.json not of the schema or not a form's, no name, no template.typ defining `#let template(`, no title.typ defining `#let title-page(`."""
    meta = form.meta
    where = form.folder / FILE
    try:
        validation.validate_structure(meta, "form")
    except validation.ValidationError as exc:
        _refuse("invalid", f"{where}: {exc}", folder=str(form.folder), error=str(exc))
    names = meta.get("name") or {}
    if not any(isinstance(text, str) and text.strip() for text in names.values()):
        _refuse("no_name", f"{where}: the form has no name", folder=str(form.folder))
    for key in ("name", "description"):
        extra = sorted(set(meta.get(key) or {}) - set(LANGUAGES))
        if extra:
            _refuse("invalid", f"{where}: {key} names {', '.join(extra)}, which are no language of Woodcore ({', '.join(LANGUAGES)})", folder=str(form.folder), error=f"{key}: {', '.join(extra)}")
    for path, pattern, what in ((form.template_typ, _TEMPLATE_DEF, "#let template(doc, lang:, region:)"), (form.title_typ, _TITLE_DEF, "#let title-page(document:)")):
        if not path.is_file():
            _refuse("invalid", f"{form.folder}: {path.name} is not there", folder=str(form.folder), error=f"no {path.name}")
        if not pattern.search(templates._read_text(path)):
            _refuse("invalid", f"{path}: it has no `{what}` -- the entry files of the documents call it", folder=str(form.folder), error=f"{path.name} has no {what}")


def read(folder, place):
    """The form in `folder` of `place`, read and checked -- one that cannot be used carries its reason in `error` rather than raising, so a list of forms still shows it."""
    folder = Path(folder)
    try:
        meta = json.loads((folder / FILE).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return Form(folder, place, {}, f"{folder}: no {FILE}")
    except (OSError, ValueError) as exc:
        return Form(folder, place, {}, f"{folder / FILE}: cannot be read ({exc})")
    form = Form(folder, place, meta)
    if not isinstance(meta, dict):
        form.error = f"{folder / FILE}: not an object"
        return form
    try:
        check(form)
    except FormError as exc:
        form.error = str(exc)
    return form


def list_forms(settings=None):
    """Every form of the three places, builtin first (`neutral`, then the others in the order of their names), then the engineer's, then the office's. A folder holding no form.json is not a form and is left out; one whose form.json is wrong is listed, its `error` saying why."""
    settings = settings if settings is not None else templates._usersettings().read()
    out = []
    for place in PLACES:
        root = place_dir(place, settings)
        if root is None or not root.is_dir():
            continue
        found = [read(folder, place) for folder in sorted(root.iterdir(), key=lambda p: p.name.lower())
                 if folder.is_dir() and (folder / FILE).is_file()]
        if place == "builtin":
            found.sort(key=lambda form: form.id != NEUTRAL)   # stable: the order of the names is kept
        out.extend(found)
    return out


def find(ref, settings=None):
    """The form `ref` names: `<place>:<id>`, or an id alone -- `neutral`, `compact`, which the styles of the same names resolve to --, or a name in any language, in any case; the engineer's own first, then the office's, then the builtin ones. Neutral where none is given. Raises FormError naming those there are where none matches, or the reason where the one found cannot be used."""
    ref = (ref or "").strip() or f"builtin:{NEUTRAL}"
    found = list_forms(settings)
    place, colon, name = ref.partition(":")
    if colon and place in PLACES:
        wanted, scope = name.strip().casefold(), [form for form in found if form.place == place]
    else:
        wanted, scope = ref.casefold(), sorted(found, key=lambda form: {"user": 0, "shared": 1, "builtin": 2}[form.place])

    def names(form):
        out = {form.folder.name.casefold(), form.id.casefold()}
        if isinstance(form.meta.get("name"), dict):
            out |= {str(text).casefold() for text in form.meta["name"].values()}
        return out

    candidates = [form for form in scope if wanted in names(form)]
    if not candidates:
        listing = ", ".join(f"{form.name('en')} ({form.ref})" for form in found) or "none"
        _refuse("no_such_form", f"no form {ref!r} -- there are: {listing}", ref=ref)
    if candidates[0].error:
        _refuse("form_unusable", candidates[0].error, ref=candidates[0].ref, error=candidates[0].error)
    return candidates[0]


def default():
    """The form a new project starts with: builtin neutral -- read without the settings, which cannot hide it."""
    return read(place_dir("builtin") / NEUTRAL, "builtin")


def default_ref(settings=None):
    """The reference of the form «Nouveau projet» offers first: the settings' `forms.default`, else builtin neutral -- `templates.default_ref`'s arrangement for the forms. `settings` is read where none is given."""
    settings = settings if settings is not None else templates._usersettings().read()
    ref = (settings.get("forms") if isinstance(settings.get("forms"), dict) else {}).get("default")
    return ref.strip() if isinstance(ref, str) and ref.strip() else f"builtin:{NEUTRAL}"


def set_default(settings, ref):
    """`ref` written as the settings' default form (`forms.default`) in the dict `settings`, which is returned -- the caller writes the file (usersettings.write), as for `templates.default`. An empty `ref` takes the key out, so that the default is builtin neutral again."""
    prefs = settings.setdefault("forms", {})
    if isinstance(ref, str) and ref.strip():
        prefs["default"] = ref.strip()
    else:
        prefs.pop("default", None)
    return settings


def default_form(settings=None):
    """The form the settings name as the default, else builtin neutral -- and neutral where the one named is gone or cannot be used, as `templates.default_template` falls back to Standard."""
    settings = settings if settings is not None else templates._usersettings().read()
    try:
        return find(default_ref(settings), settings)
    except FormError:
        return default()


# --- the form a project is written in ---------------------------------------------------------

def template_dir(here):
    """`here`'s `Template/`, at its Typst root."""
    return Path(here.typst_root) / TEMPLATE_DIR


def current(here):
    """The form project `here` is written in, read from its `Template/form.json` -- a Form whose folder is the project's own `Template/`, its `id` and `place` those of the form it was made from -- or None where the project has no `Template/` (a project from before forms, whose config.typ is one monolithic file) or none that says which form it is."""
    folder = template_dir(here)
    path = folder / FILE
    if not path.is_file():
        return None
    try:
        meta = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    if not isinstance(meta, dict) or meta.get("format") != FORMAT:
        return None
    place = meta.get("place") if meta.get("place") in PLACES else "user"
    return Form(folder, place, meta)


def is_form_config(path):
    """True where the config.typ at `path` is in the new format -- it imports the function from `/Template/template.typ` -- and so holds only the language and the engineer's adjustments; False for a monolithic one, and for a file that is not there."""
    path = Path(path)
    try:
        return bool(_FORM_IMPORT.search(templates._read_text(path)))
    except OSError:
        return False


def config_text(doc_lang="de", doc_region="CH"):
    """The text of a config.typ in the new format: the document's language and region, and `conf`, which sets the form's look and then the engineer's own adjustments, which win over it. LF line endings."""
    for what, value in (("doc-lang", doc_lang), ("doc-region", doc_region)):
        if not isinstance(value, str) or not _LANG_VALUE.match(value):
            raise FormError(f"{what} is {value!r} -- a language or region code such as \"de\" or \"CH\"", "invalid", error=f"{what}: {value!r}")
    return f'''// The look of the project's three documents is the **form** in `Template/` (Template/template.typ, which Woodcore switches: Fichier → Propriétés du projet), and no longer lives here. This file keeps what is the project's own: the document's language, and your adjustments of the look -- the entry files of the three documents call `conf` below.

// **The document's own language lives here** (docs/typst/language.md §4bis). `lang` and `region` are what Typst itself works in: the hyphenation patterns, the quotation marks, and the words Typst writes of its own accord -- «Abbildung»/«Fig.», «Tabelle»/«Tableau», the outline's title. Set them by hand, to the language this report is written in.
//
// They are deliberately *not* the report language of `#set-report-language` (the entry files): that command translates what the *engine* prints -- the labels of the calculations, the tables' headings and notes, the figures' legends -- while what the report says in its own words, its headings and its title and its prose, is the engineer's and is never translated. Two settings, because they answer two questions; a report in French wants both.
#import "/Template/template.typ": template
#let doc-lang = "{doc_lang}"
#let doc-region = "{doc_region}"

#let conf(doc) = {{
  show: template.with(lang: doc-lang, region: doc-region)

  // ==================================================================================================
  // YOUR ADJUSTMENTS -- written here, they win over the form's, and they are kept when the form is switched
  // ==================================================================================================
  // Any `set` or `show` rule: a different text size, other margins, your own heading style. For example:
  //   set text(size: 10pt)
  //   set page(margin: (left: 3cm, right: 2cm, top: 3cm, bottom: 2.5cm))
  //   set figure(supplement: [Figure])

  doc
}}
'''


# --- applying a form --------------------------------------------------------------------------

_IGNORE = shutil.ignore_patterns("__pycache__", ".git", "*.tmp", ARCHIVES)


def _retried(call, *args):
    """`call(*args)`, tried again a few times on the PermissionError NextCloud's client gives while it holds what it has just seen written."""
    for attempt in range(6):
        try:
            return call(*args)
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.1 * (attempt + 1))


def _unique(path):
    """`path`, or `path-2`, `path-3` … where it is taken."""
    path = Path(path)
    candidate, number = path, 2
    while candidate.exists():
        candidate, number = path.with_name(f"{path.name}-{number}"), number + 1
    return candidate


def _write_json(path, meta):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
    _retried(os.replace, temporary, path)


def _stamped(form, meta=None):
    """The form.json a project's `Template/` carries: the form's own, with the `id` and `place` of the form it was made from."""
    meta = dict(meta if meta is not None else form.meta)
    ordered = {"schema_version": SCHEMA_VERSION, "format": FORMAT, "id": form.id, "place": form.place}
    ordered.update((key, meta[key]) for key in ("name", "description") if meta.get(key))
    return ordered


def _project_languages(here):
    """(doc-lang, doc-region) the project states today -- its config.typ's, else the report's language, else German and Switzerland."""
    config = Path(here.config_typ)
    text = templates._read_text(config) if config.is_file() else ""
    lang = templates._DOC_LANG.search(text)
    region = templates._DOC_REGION.search(text)
    language = lang.group(2) if lang and lang.group(2) else ""
    if not language:
        language = templates.read_languages(here.report_typ, config=config)[1] or templates.DEFAULT_LANGUAGE
    return language, (region.group(2) if region and region.group(2) else "CH")


class Applied:
    """What `apply` did: the folder of the archives it kept the old form in (None where there was nothing to keep), and whether it wrote config.typ."""

    def __init__(self, form, archive, config_written):
        self.form = form
        self.archive = archive
        self.config_written = config_written

    def __repr__(self):
        return f"Applied({self.form.ref!r}, archive={self.archive!r}, config_written={self.config_written!r})"


def apply(here, form):
    """Switches project `here` to `form` (a Form, or a reference `find` takes), **all or nothing**.

    The existing `Template/` and `title.typ` -- and config.typ where it is not in the new format -- are moved into `<archives>/<yymmdd-hhmmss>-forme/`, never deleted; the form's folder, everything but its title.typ, is copied into `<typst root>/Template/` with a form.json stating the form's `id` and `place`; its title.typ goes to the top of the project, `here.title_typ`. config.typ is left as it is when it is in the new format already -- it holds the engineer's adjustments, which survive the switch -- and otherwise written in it (`config_text`) with the project's own `doc-lang` and `doc-region`, the old one kept in the archives.

Everything is checked and staged first, beside the project, and what is moved or written is put back where a later step fails. Returns an Applied."""
    if not isinstance(form, Form):
        form = find(form)
    if form.error:
        _refuse("form_unusable", form.error, ref=form.ref, error=form.error)
    root = Path(here.typst_root)
    target, title, config = template_dir(here), Path(here.title_typ), Path(here.config_typ)
    keep_config = is_form_config(config)
    language, region = _project_languages(here)
    stage = root / f"{STAGING}-{os.getpid()}"
    shutil.rmtree(stage, ignore_errors=True)
    undo = []   # what to do, last first, to put the project back
    archive = None
    try:
        try:
            # 1. stage the new files beside the project, checked and complete before anything moves
            staged_template = stage / TEMPLATE_DIR
            shutil.copytree(form.folder, staged_template, ignore=_IGNORE)
            staged_title = stage / TITLE_FILE
            os.replace(staged_template / TITLE_FILE, staged_title)
            _write_json(staged_template / FILE, _stamped(form))
            staged_config = None
            if not keep_config:
                staged_config = stage / "config.typ"
                staged_config.write_text(config_text(language, region), encoding="utf-8", newline="")
            # 2. keep what was there
            old = [(target, TEMPLATE_DIR), (title, TITLE_FILE)] + ([] if keep_config else [(config, "config.typ")])
            old = [(path, name) for path, name in old if path.exists()]
            if old:
                archive = _unique(Path(here.archives_dir) / f"{time.strftime('%y%m%d-%H%M%S')}-{ARCHIVE_LABEL}")
                archive.mkdir(parents=True)
                for path, name in old:
                    _retried(os.replace, path, archive / name)
                    undo.append((os.replace, archive / name, path))
            # 3. put the new ones in place
            _retried(os.replace, staged_template, target)
            undo.append((os.replace, target, staged_template))
            _retried(os.replace, staged_title, title)
            undo.append((os.replace, title, staged_title))
            if staged_config is not None:
                _retried(os.replace, staged_config, config)
                undo.append((os.replace, config, staged_config))
        except Exception as exc:
            for call, source, destination in reversed(undo):
                try:
                    _retried(call, source, destination)
                except OSError:
                    pass   # what cannot be put back stays in the archives, which the message below names
            if archive is not None and not any(archive.iterdir()):
                try:
                    archive.rmdir()
                except OSError:
                    pass
            if isinstance(exc, FormError):
                raise
            _refuse("write_failed", f"the form {form.ref} could not be applied to {here.name!r}: {exc}" + (f" -- what was moved is in {archive}" if archive is not None and archive.exists() else ""),
                    ref=form.ref, error=str(exc))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return Applied(form, archive, not keep_config)


# --- the engineer's own forms -----------------------------------------------------------------

def _move_into_archives(folder, label):
    """`folder` moved to `<its parent>/archives/<yymmdd-hhmmss>-<label>`, never deleted. Returns where it went."""
    folder = Path(folder)
    target = _unique(folder.parent / ARCHIVES / f"{time.strftime('%y%m%d-%H%M%S')}-{label}")
    target.parent.mkdir(parents=True, exist_ok=True)
    _retried(os.replace, folder, target)
    return target


def archive(form):
    """«Supprimer»: the form's folder moved into its place's `archives/` -- `<place>/forms/archives/<yymmdd-hhmmss>-<id>` -- and never deleted. Refused for a builtin one. A form that cannot be used can be taken away all the same. Returns where it went."""
    if form.read_only:
        _refuse("read_only", f"{form.ref} is a builtin form and cannot be deleted", ref=form.ref)
    return _move_into_archives(form.folder, form.folder.name)


def _check_folder_name(name):
    name = (name or "").strip()
    if not name:
        _refuse("no_name", "a form needs a name")
    return name


def import_folder(source, replace=False, settings=None):
    """«Importer un dossier…»: the form in the folder `source` -- a folder holding a form.json, a template.typ and a title.typ -- copied into the engineer's own place (`place_dir("user")`) under its folder's name. Returns the form as it now stands there.

    **Checked before anything is written**: `source` must be a folder (`not_a_folder`) holding a form.json (`no_form`) that `check` finds sound (`invalid`, its reason in `error`), not named as a builtin form (`name_is_builtin`), and not one of the engineer's own already (`already_mine`). A form of that folder's name in his place is refused (`exists`) unless `replace`, which moves the old one into the place's `archives/` -- never deleted -- and puts it back if the copy then fails. The copy is staged beside the place and read back first, so a failure (`write_failed`) leaves nothing half copied."""
    settings = settings if settings is not None else templates._usersettings().read()
    source = Path(source)
    if not source.is_dir():
        _refuse("not_a_folder", f"{source} is not a folder", folder=str(source))
    if not (source / FILE).is_file():
        _refuse("no_form", f"{source} holds no {FILE} -- it is not a form", folder=str(source))
    found = read(source, "user")
    if found.error:
        _refuse("invalid", found.error, folder=str(source), error=found.error)
    root = Path(_writable_root("user", settings))
    mine, there = root.resolve(), source.resolve()
    if there == mine or mine in there.parents or there in mine.parents:
        _refuse("already_mine", f"{source} is among the engineer's own forms already", folder=str(source))
    if source.name.casefold() in {form.folder.name.casefold() for form in list_forms(settings) if form.place == "builtin"}:
        _refuse("name_is_builtin", f"{source.name} is the folder name of a builtin form -- rename the folder first", name=source.name)
    target = root / source.name
    if target.exists() and not replace:
        _refuse("exists", f"user:{source.name} is there already -- importing over it asks for `replace`, which keeps the old one in {ARCHIVES}/", folder=source.name, name=found.name("en"))
    stage = root / f"{STAGING}-{os.getpid()}"
    staged = stage / source.name
    shutil.rmtree(stage, ignore_errors=True)
    try:
        try:
            stage.mkdir(parents=True)
            shutil.copytree(source, staged, ignore=_IGNORE)
            made = read(staged, "user")
            if made.error:
                _refuse("invalid", made.error, folder=str(source), error=made.error)
            archived = None
            if target.exists():
                archived = _move_into_archives(target, target.name)
            try:
                _retried(os.replace, staged, target)
            except OSError:
                if archived is not None:
                    _retried(os.replace, archived, target)
                raise
        except OSError as exc:
            _refuse("write_failed", f"{source} could not be copied into the engineer's forms: {exc}", folder=str(source), error=str(exc))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return read(target, "user")


def save_from_project(here, name, place="user", settings=None, description=""):
    """«Enregistrer comme forme»: the form of project `here` -- its `Template/` and its title.typ -- made a form named `name` in `place`, in a folder of its own: everything of `Template/` but its form.json, which is written afresh with `name` and `description`, the same in the three languages (the engineer wrote them in one). Returns the new form.

    Refused where the project has no `Template/` with a template.typ (`no_project_form`: a project from before forms has its look in config.typ, which is the project's own and not a form), where the name is empty or a builtin form's, and where the place is builtin or shared without a folder. Staged and read back before it is moved into place, so a form that would not be sound is never left."""
    settings = settings if settings is not None else templates._usersettings().read()
    root = Path(_writable_root(place, settings))
    name = _check_folder_name(name)
    folder_id = templates.folder_name(name)
    if folder_id.casefold() in {form.folder.name.casefold() for form in list_forms(settings) if form.place == "builtin"}:
        _refuse("name_is_builtin", f"{name} is the name of a builtin form -- choose another", name=name)
    source = template_dir(here)
    title = Path(here.title_typ)
    if not (source / TEMPLATE_FILE).is_file() or not title.is_file():
        _refuse("no_project_form", f"{here.name!r} has no {TEMPLATE_DIR}/{TEMPLATE_FILE} and {TITLE_FILE} to make a form of -- its look is the config.typ's, which is the project's own", ref=here.name)
    target = root / folder_id
    candidate, number = target, 2
    while candidate.exists():
        candidate, number = root / f"{folder_id} {number}", number + 1
    target = candidate
    meta = {"schema_version": SCHEMA_VERSION, "format": FORMAT, "name": {lang: name for lang in LANGUAGES}}
    if description and description.strip():
        meta["description"] = {lang: description.strip() for lang in LANGUAGES}
    stage = root / f"{STAGING}-{os.getpid()}"
    staged = stage / target.name
    shutil.rmtree(stage, ignore_errors=True)
    try:
        try:
            stage.mkdir(parents=True)
            shutil.copytree(source, staged, ignore=_IGNORE)
            shutil.copy2(title, staged / TITLE_FILE)
            _write_json(staged / FILE, meta)
            made = read(staged, place)
            if made.error:
                _refuse("invalid", made.error, folder=str(staged), error=made.error)
            _retried(os.replace, staged, target)
        except OSError as exc:
            _refuse("write_failed", f"the form {name!r} could not be saved: {exc}", name=name, error=str(exc))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return read(target, place)
