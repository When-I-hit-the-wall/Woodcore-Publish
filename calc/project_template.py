"""A new project, and an old folder made into one (docs/architecture/layout.md §11, v0.83): `woodcore-cli new` and the start page's «Nouveau projet» and «Convertir un ancien dossier».

**A new project** is a template copied into an empty folder -- Standard, `templates/projet/`, where none is chosen, else one of the engineer's or the office's, its languages, layout and people its own (calc/templates.py, v0.94) -- the report, its config and commands, sections that loop over what the export holds, Tinymist's settings -- plus the folders Woodcore's window saves into, an empty `positions.json` among them (calc/positions_store.py: the positions are Woodcore's own since v0.114, and no `Positionen.xlsx` is made any more), the `.woodcore` file naming it, the engine, and the export of a project holding nothing yet (`export_all.seed`, v0.86.1), so its report compiles before its first export. A load workbook is **not** created: the office's is a `Belastungsannahmen` template, with macros and controls openpyxl cannot write, so the engineer copies it in, and the first export says so by name until then.

**It is laid out in three documents** (the engineer's request of 30.09.2026): the convention d'utilisation, the base de projet and the rapport de statique -- the report, which keeps every name it had -- each in a folder of its own at the top of the project, numbered and named in the project's language (calc/documents.py, `1_Nutzungsvereinbarung`, `2_Projektbasis`, `3_Statischer Bericht`), and beside them what the three share: `config.typ`, `commands.typ`, `references.bib`, `Images/` and the export's `_woodcore/`. The project's folder is the Typst root, and its `.woodcore` states the layout in full (project.full_layout). Standard stays a report alone on disk -- the folder a template keeps is an implementation detail every project renames -- so a report-shaped skeleton is laid out as it is copied -- each part copied straight to where it goes, the shared files to the top and the report into its new folder, never copied and then renamed (`_copy_skeleton`) -- every path its `.typ` files write that would no longer reach what it names rewritten root-absolute (calc/typst_paths.py: `#import "/commands.typ": *`, `image("/Images/…")`), and the two other documents made from their own templates (calc/doc_templates.py). A documents-shaped template, saved from a project laid out so, is copied as it stands, each of its three folders into the one it is named now. `project.DEFAULT_LAYOUT` does not move: a project created before stays laid out as a report alone and reads it.

**Form and content** (the engineer's decision of 06.10.2026): a new project is made from a **form**, the look of its three documents (calc/forms.py: `Template/`, `title.typ`, and a config.typ that keeps only the language and the engineer's adjustments), and one **content template** per document (calc/doc_templates.py: its sections and what they say, the report's included -- `templates/documents/rs/`). The project templates of calc/templates.py no longer make a project by themselves: Standard is the neutral form with the three standard content templates, and `templates/projet/` stays on disk as the skeleton of what the three share -- commands.typ, references.bib, `.vscode/`, the folders -- where the report's own entry file, sections, config.typ and title.typ it also carries are put aside for the content and the form (`create`). A project template of the engineer's own, saved before forms, still makes a project as it did: its report, its config.typ and its title page are its own, and a form is applied over them only where one is asked for.

**An old folder** is one laid out before Woodcore -- the report in `000-TypstRapport/`, the code and the export in `000-TypstRapport/000-Python/` -- or an archive of one. Converting it moves nothing and deletes nothing: it writes a `.woodcore` whose `layout` names the folders where they are, so Woodcore opens it as it stands. The first export then finds the engine that folder carried with no VERSION naming it (`project.engine_state`, `unknown`) and asks before replacing it.
"""

import os
import shutil
import stat
from pathlib import Path, PurePosixPath

import project
import validation

TEMPLATE = project.APP_ROOT / "templates" / "projet"   # Standard, the builtin template (templates.STANDARD)

def _empty(folder):
    return not folder.exists() or not any(folder.iterdir())


def file_name(name):
    """The project file's name: the project's name with what Windows refuses in a file name taken out."""
    cleaned = "".join("_" if ch in '<>:"/\\|?*' or ord(ch) < 32 else ch for ch in name).strip().rstrip(".")
    return (cleaned or "Projekt") + project.EXTENSION


def create(folder, name, template=None, document_language=None, report_language=None, report_folder=None,
           folders=None, document_templates=None, style=None, form=None, make=None, **details):
    """Makes `folder` a new project named `name`, laid out in three documents, `details` any of project.DETAILS, from `template` -- a calc/templates.py Template or the reference of one (`user:Holzbau`), Standard where none is given (v0.94) -- its form `form` and its three contents `document_templates`. The folder must be empty or not exist yet. Returns the Project.

    **The three folders** are `folders` -- {mode: folder}, or three names in project.MODES' order, a name left out or empty taking what `templates.folders_offered` offers: calc/documents.py's for the project's language (MODE_FOLDERS), or a template's own where it names them. `report_folder` names the report's alone, as «Nouveau projet» and `woodcore-cli new --report-folder` have since v0.100, and must not contradict `folders`. Each is checked, and the three must differ, **before anything is created** (documents.modes_layout), so a refused name leaves nothing behind.

    **The languages**: `document_language` and `report_language`, where given, are written into the project's config.typ and into every document's entry file (templates.write_project_languages; templates.languages_for says what they come to). The project's language -- what its folders are named in and what the convention d'utilisation and the base de projet are written in -- is the document language, else the template's own. Where the report language is not given, the report's own is written into the two other documents, so that the three print the engine's words in one language.

    **The form** is the look of the three documents (calc/forms.py): `form` -- a forms.Form or its reference (`bfh`, `builtin:compact`), else the settings' default (forms.default_ref), else builtin neutral -- is applied once the project is made (forms.apply: `Template/` and `title.typ` put in place, and a config.typ in the new format holding the project's language and region, which the languages written below then set). `style` is the older name of the same thing, an alias: a calc/templates.py Style or an id (`compact`, which a form of that name answers), and asking for two different forms is refused. An unknown form is refused, naming the valid ones, before anything is created.

    **When a form is applied.** For Standard always, the default one where none is asked for: the skeleton's own config.typ and title.typ are put aside first, being nothing but a stand-in for the form's. For another template of the engineer's, **only where one is asked for**: its config.typ and its title page are its own look and are left as they are otherwise, a form given explicitly replacing them (put aside before, so that nothing is archived in a project that is not yet there ; a config.typ already in the new format, which holds the engineer's adjustments, is kept, as forms.apply keeps it) -- so a template saved before forms makes the project it always made, and one saved since, carrying its own `Template/`, makes one with that form.

    **The contents** are `document_templates`, {mode: DocTemplate or reference}, else each mode's builtin standard one (doc_templates.default_ref). The convention d'utilisation and the base de projet are made from theirs for a report-shaped template (a documents-shaped one carries its own); **the report** (`rs`) is made from `templates/documents/rs/` for Standard, and for another template only where `document_templates` names one -- the template's own entry file and `Sections/` are then left out. A DocTemplate is taken as it is, so one of the office's -- whose place lies in a folder the settings name -- needs no settings file to be found again. Once both documents are there their sharing is settled from the tags (doc_templates.settle_sharing), whichever templates they came from.

    **The documents made now** are `make`, some of project.MODES, all three where none is given (issue #90): a project made with `make=()` -- the skeleton «Nouveau projet» makes since 0.122, `create_skeleton` -- states its three folders and its language, its form and its title page, and holds no document yet; each is made later by `create_document`. The content template each document was made from is written into the project file (`content_templates`, issue #88).

    The people are the ones given, the callers filling them from the template (templates.people_for). A creation that fails takes away everything it wrote -- the folder was empty -- and raises a ProjectError.
    """
    import documents
    import forms
    import templates
    folder = Path(os.path.abspath(folder))
    if not name or not name.strip():
        raise project.ProjectError("a new project needs a name")
    if template is None:
        template = templates.standard()
    elif isinstance(template, str):
        template = templates.find(template)
    if template.error:
        raise project.ProjectError(template.error)
    asked = _form_asked(form, style)
    is_standard = template.ref == templates.STANDARD
    # What the report is made from: its content template (templates/documents/rs/) for Standard, and for another template where one is named -- else the template's own entry file and sections.
    use_rs = is_standard or "rs" in (document_templates or {})
    if is_standard or asked is not None:
        chosen = asked if asked is not None else _default_form()
    else:
        chosen = None
    if not _empty(folder):
        raise project.ProjectError(f"{folder} is not empty -- a new project is created in an empty folder")
    own_document, own_report = templates.read_languages(template.report)
    language = documents.language_of(document_language or own_document or report_language or "")
    engine_language = report_language or own_report or None
    # ⚠️ Everything is checked **before** anything is created (templates.check_report_folder, v0.100): refused after the copy, it left a half-copied project behind, and the next attempt then failed on «is not empty» instead of on the name.
    layout = _layout(template, _wanted_folders(template, language, report_folder, folders), language)
    file = folder / file_name(name.strip())
    project.Project(file, {"schema_version": project.schema_version_for(layout), "format": project.FORMAT, "name": name.strip(), "layout": layout})
    _check_names(template, layout, file)
    made_from = {} if template.has_modes else {
        mode: _document_template(mode, language, (document_templates or {}).get(mode)) for mode in DOCUMENTS_BESIDE}
    if use_rs:
        made_from["rs"] = _document_template("rs", language, (document_templates or {}).get("rs"))
    if make is not None:
        made_from = {mode: found for mode, found in made_from.items() if mode in make}
    made = not folder.exists()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        moves, root_old = _copy_skeleton(folder, template, layout)
        if use_rs:
            _drop_report(folder, layout)   # the skeleton's own entry file and sections: the report's content template takes their place below
        here = project.write(file, name.strip(), layout=layout,
                             **{k: v.strip() for k, v in details.items() if isinstance(v, str) and v.strip()})
        project.sync_engine(here)   # the engine beside the export-to-be, so every document's import resolves -- in Tinymist too
        # The paths the skeleton's files write, rewritten where what they name moved (calc/typst_paths.py) -- after the engine is copied, so `commands.typ`'s own import of it is seen to resolve and left exactly as it is.
        normalise(folder, moves, root_old, skip=(here.generated_dir,))
        # The title page every document's entry sets (`#import "/title.typ": title-page`): the template's own where it carries one, Standard's where it does not -- a template saved before the title page was a file of its own, or one that keeps its report's title page in its entry -- since a convention d'utilisation and a base de projet made from the builtin document templates import it and do not compile without it.
        ensure_title(here)
        import doc_templates
        for mode, doc_template in made_from.items():
            try:
                # `siblings`: the documents this project has besides this one, so that a section a template shares with a document the project does not have is not shared
                doc_templates.instantiate(mode, language, here.document_dir(mode), entry_name=here.document_typ(mode).name, template=doc_template,
                                          siblings=tuple(other for other in here.modes if other != mode and (make is None or other in make)))
            except doc_templates.DocTemplateError as exc:
                raise project.ProjectError(str(exc)) from None
        if chosen is not None:
            _drop_look(here)
            forms.apply(here, chosen)   # before the languages are written, so that the language the project has now is written into the config.typ the form leaves
        if all(mode in here.modes and (make is None or mode in make) for mode in DOCUMENTS_BESIDE):
            # Both documents are there: every `shared_with` is written again from the tags the files carry (the tags are the truth), so that a convention d'utilisation of the engineer's combined with a base de projet that lacks a section it shares keeps no flag saying it is shared with nothing (doc_templates.settle_sharing)
            doc_templates.settle_sharing(here)
        # laid out by folders, what the content templates and the template's own files name at the root -- `/commands.typ`, `/title.typ`, `/Template/…`, `project: "references.bib"` -- named where 000-Typst-Config/ keeps it (issue #64; nothing for a project laid out before)
        documents.relocate_config_paths(here, [path for path in sorted(folder.rglob("*.typ")) if not project._is_within(path, here.generated_dir)])
        templates.write_project_languages(here.config_typ, [here.document_typ(mode) for mode in here.modes], document_language, engine_language)
        for path in (here.images_dir, here.archives_dir, *(here.sources_dir / sub for sub in project.SOURCE_FOLDERS)):
            path.mkdir(parents=True, exist_ok=True)
        here.ensure_folders()   # every folder of a project laid out by folders, the domains' and the drawing tabs' among them, empty ones included (REQ-011)
        # the project's positions, none yet: Woodcore's own file, which the Positions tab fills (calc/positions_store.py, v0.114) -- no Positionen.xlsx is made any more
        import positions_store
        if not positions_store.path(here).exists():
            positions_store.write(here, [])
        import export_all
        export_all.seed(here)       # and the export of a project holding nothing yet -- the journals of the three documents among it -- so every document compiles from the moment the project exists and not from its first export (v0.86.1)
        if made_from:
            here = project.update(here.file, **{project.CONTENT_TEMPLATES_KEY: {mode: found.ref for mode, found in made_from.items()}})
    except BaseException as exc:
        _undo(folder, made)
        if isinstance(exc, validation.ValidationError) and not isinstance(exc, project.ProjectError):
            raise project.ProjectError(str(exc)) from exc
        raise
    return here


def create_skeleton(folder, name, language, form=None, **details):
    """A new project as «Nouveau projet» makes it since 0.122 (issue #90, the engineer, 21.10.2026: «La fenêtre qui s'ouvre pour créer le nouveau projet doit uniquement demander le nom du projet […] ainsi que l'endroit»): Standard laid out in three documents, in `language` -- chosen once, in the dialog, and never changed --, its form (`form`, else the settings' default), its title page `details` and no document. Each document is made later from the «Projet» tab, `create_document`. Returns the Project."""
    return create(folder, name, document_language=language, report_language=language, form=form, make=(), **details)


def create_document(here, mode, template=None):
    """Document `mode` of project `here` made from content template `template` (a DocTemplate or its reference; the builtin standard one where none is given), in the project's language, into its folder (issue #90: «lorsqu'un template de fond est choisi et validé, eh bien le document TYPST est créé dans le dossier correspondant et le template de fond ne peut plus être modifié»).

    Made as `create` makes it: the template's language folder copied in, its entry named as the project file says, sharing kept only with the documents already there and settled once both the convention d'utilisation and the base de projet are, the report language of the documents there (else the project's) written into its entry, its own journal and the export's files a document reads seeded, and the template's reference written into the project file (`content_templates`). Refused, with nothing written, for a project laid out as a report alone, a document that is there already, or a template that does not exist in the project's language. A failure after the copy takes away what was written. Returns the Project as it now stands."""
    import doc_templates
    import documents
    import export_all
    import templates
    if not here.has_modes:
        raise project.ProjectError(f"{here.file.name}: a project laid out as a report alone has its one document")
    here._document(mode)
    if here.is_created(mode):
        raise project.ProjectError(f"{here.rel(here.document_typ(mode))} is there already -- a document's content template is chosen once")
    language = templates.project_language(here, fallback="")
    if language not in templates.LANGUAGES:
        raise project.ProjectError(f"{here.file.name}: the project states no language -- its config.typ has no doc-lang")
    found = _document_template(mode, language, template)
    created = here.created_modes
    folder = here.document_dir(mode)
    was_there = folder.exists() and any(folder.iterdir())
    if was_there:
        raise project.ProjectError(f"{here.rel(folder)} holds files already -- a document is made in an empty folder")
    try:
        try:
            entry = doc_templates.instantiate(mode, language, folder, entry_name=here.document_typ(mode).name, template=found,
                                              siblings=tuple(other for other in created if other != mode))
        except doc_templates.DocTemplateError as exc:
            raise project.ProjectError(str(exc)) from None
        documents.relocate_config_paths(here, sorted(folder.rglob("*.typ")))
        reports = [templates.read_languages(here.document_typ(other))[1] for other in created]
        report = next((lang for lang in reports if lang in templates.LANGUAGES), language)
        templates.write_project_languages(here.config_typ, [entry], None, report)
        if all(here.is_created(other) for other in DOCUMENTS_BESIDE):
            doc_templates.settle_sharing(here)
        export_all.seed(here)   # the new document's own journal file, and data/domain-files.json listing it
        return project.set_content_template(here, mode, found.ref)
    except BaseException:
        remove_tree(folder)
        raise


def standard_title():
    """The title.typ of the builtin Standard template: the plain title page, in German, French and English, its rows the people of the .woodcore."""
    import templates
    return templates.standard().typst_root / project.TITLE_FILE


def ensure_title(here):
    """`title.typ` written at the Typst root of project `here` where it has none -- Standard's (`standard_title`) -- and **never over one that is there**: it is the engineer's, edited in VS Code, and Woodcore does not rewrite it. Nothing is done for a project laid out as one report, whose entry keeps its own title page. Returns the path written, or None."""
    if not here.has_modes:
        return None
    target = here.title_typ
    if target.exists():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(standard_title(), target)
    return target


def _form_asked(form, style):
    """The form a caller asked for -- `form`, or `style`, its older name -- as a forms.Form, or None where neither is given: each a Form, a reference (`bfh`, `builtin:compact`) or, for `style`, a calc/templates.py Style. Raises ProjectError, naming the forms there are, for one that is not there or cannot be used, and for two that name different forms. Nothing is written."""
    import forms
    import templates

    def one(value):
        if value is None or value == "":
            return None
        try:
            found = value if isinstance(value, forms.Form) else forms.find(value)
        except forms.FormError as exc:
            raise project.ProjectError(str(exc)) from None
        if found.error:
            raise project.ProjectError(found.error)
        return found

    wanted, alias = one(form), one(style)
    if wanted is not None and alias is not None and wanted.ref != alias.ref:
        raise project.ProjectError(f"two forms were asked for, {wanted.ref} (form) and {alias.ref} (style, the older name of the same thing) -- ask for one")
    return wanted if wanted is not None else alias


def _default_form():
    """The form a project gets where none is asked for: the settings' default, builtin neutral where it is gone or unusable (forms.default_form)."""
    import forms
    form = forms.default_form()
    if form.error:
        raise project.ProjectError(form.error)
    return form


def _drop_report(folder, layout):
    """The entry file and `Sections/` the skeleton copied into the new project's report folder taken away again -- they are the skeleton's own, written a moment ago in a folder that was empty -- so that the report's content template (doc_templates.instantiate, "rs") is written in their place."""
    entry = folder / PurePosixPath(str(layout["report"]).replace("\\", "/"))
    if entry.is_file():
        entry.unlink()
    sections = entry.parent / "Sections"
    if sections.is_dir():
        shutil.rmtree(sections)


def _drop_look(here):
    """What the template carried of a look, taken away before a form is applied: its `Template/` and `title.typ`, and its config.typ unless that is in the new format already -- which holds the engineer's own adjustments and is kept (forms.apply). The project was made a moment ago, so nothing is archived: forms.apply would otherwise keep each in `_Archiv/` as the old look of a project that never had one."""
    import forms
    for path in (forms.template_dir(here), Path(here.title_typ)):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
    config = Path(here.config_typ)
    if config.is_file() and not forms.is_form_config(config):
        config.unlink()


# The two documents a project in three documents is written as beside the report, which a report-shaped template does not carry and a new project is given from their own templates (calc/doc_templates.py).
DOCUMENTS_BESIDE = ("cu", "bp")


def _wanted_folders(template, language, report_folder, folders):
    """The three folders a new project asks for, {mode: folder}: what `templates.folders_offered` offers, each written over by `folders` or, for the report, by `report_folder` -- a name that is None or empty being no name at all. The names are checked by `_layout`."""
    import templates
    wanted = templates.folders_offered(template, language)
    given = {}
    if folders is not None:
        if isinstance(folders, dict):
            unknown = sorted(set(folders) - set(project.MODES))
            if unknown:
                raise project.ProjectError(f"no document {', '.join(map(repr, unknown))} -- a folder is named for one of {', '.join(project.MODES)}")
            items = list(folders.items())
        else:
            items = list(folders)
            if len(items) != len(project.MODES):
                raise project.ProjectError(f"three folders are named, one per document ({', '.join(project.MODES)}) -- {len(items)} were given")
            items = list(zip(project.MODES, items))
        given = {mode: str(value).strip() for mode, value in items if value is not None and str(value).strip()}
    if report_folder is not None and str(report_folder).strip():
        named = str(report_folder).strip()
        if given.get("rs", named) != named:
            raise project.ProjectError(f"the report's folder is named twice, {named!r} and {given['rs']!r}")
        given["rs"] = named
    wanted.update(given)
    return wanted


def _layout(template, wanted, language):
    """The layout, in full, of a new project made from `template` with its documents in the folders `wanted`: documents.modes_layout's -- which checks each folder's name and that the three differ -- with the entry files the template's own for the report and calc/documents.py's for the two documents a report-shaped template does not carry. The template's `sources` and `archives` are kept, and a documents-shaped one's export and pictures; a part that lay inside a document's folder moves with it."""
    import documents
    if template.has_modes:
        entries = {mode: PurePosixPath(str(template.layout[project.ENTRY_KEYS[mode]]).replace("\\", "/")).name for mode in project.MODES}
        kept = ("sources", "archives", "generated", "images")
    else:
        if template.document_folder("rs") in (".", ""):
            raise project.ProjectError(
                f"{template.name} keeps its report at the top of the template -- a project in three documents keeps each "
                f"document in a folder of its own: move the report into a folder of the template (Paramètres)")
        entries = {**documents.ENTRY_NAMES[language], "rs": PurePosixPath(str(template.layout["report"]).replace("\\", "/")).name}
        kept = ("sources", "archives")
    layout = documents.modes_layout(wanted, entries)
    moved = [(PurePosixPath(template.document_folder(mode)), PurePosixPath(layout[project.ENTRY_KEYS[mode]]).parent) for mode in template.modes]
    for key in kept:
        if not template.has_modes and template.layout.get(key) == project.DEFAULT_LAYOUT.get(key):
            continue   # a report-shaped template left to the default keeps nothing of its own: the sources and the archives go where a new project keeps them, inside 000-Woodcore/ (issue #64)
        value = PurePosixPath(str(template.layout[key]).replace("\\", "/"))
        for was, now in moved:
            if value == was or was in value.parents:
                value = now / value.relative_to(was)
                break
        layout[key] = value.as_posix()
    return layout


def _check_names(template, layout, file):
    """Refuses, before the first file is written, a new project two of whose parts would meet on one name at the top of its folder -- a document's folder named like one of the files or folders the three share, or like something else the template carries at its top -- and, for a report-shaped template, a shared file moved up onto something the template already carries there. Compared as Windows compares names."""
    import documents
    import templates
    away = {PurePosixPath(template.document_folder(mode)) for mode in template.modes}
    away = {path.parts[0].casefold() for path in away if len(path.parts) == 1}
    staying = {p.name.casefold(): p.name for p in template.folder.iterdir() if p.name != templates.FILE and p.name.casefold() not in away}
    shared = {PurePosixPath(layout[key]).parts[0] for key in ("generated", "images", "sources", "archives", *project.FOLDER_KEYS) if key in layout}
    shared |= {project.CONFIG_FILE, project.COMMANDS_FILE, project.REFERENCES_FILE, project.TITLE_FILE, project.TEMPLATE_FOLDER, file.name}
    shared = {name.casefold(): name for name in shared}
    for mode in project.MODES:
        name = PurePosixPath(layout[project.ENTRY_KEYS[mode]]).parts[0]
        what = documents.MODE_NAMES["en"][mode].lower()
        if name.casefold() in staying:
            raise project.ProjectError(f"the {what}'s folder cannot be named {name!r}: the template carries {staying[name.casefold()]!r} at its top")
        if name.casefold() in shared:
            raise project.ProjectError(f"the {what}'s folder cannot be named {name!r}: the project keeps {shared[name.casefold()]!r} at its top, which the three documents share")
    if not template.has_modes:
        old = template.folder / template.document_folder("rs")
        for part, key in _shared_parts(template, layout):
            target = PurePosixPath(layout[key] if key else _config_part(layout, part)).parts[0]
            if (old / part).exists() and target.casefold() in staying:
                raise project.ProjectError(f"the template carries {staying[target.casefold()]!r} at its top, where the report's {part} goes in a project of three documents")


# What configures the documents, which a project laid out by folders keeps in 000-Typst-Config/ (`layout.config`, issue #64) and every one laid out before at the top of its Typst root.
CONFIG_PARTS = (project.CONFIG_FILE, project.COMMANDS_FILE, project.REFERENCES_FILE, project.TITLE_FILE, project.TEMPLATE_FOLDER)


def _config_part(layout, part):
    """Where `part` of CONFIG_PARTS lies in a project of `layout`, from its folder: in the configuration's folder laid out by folders, at the top before."""
    return (PurePosixPath(layout["config"]) / part).as_posix() if "config" in layout else part


def _shared_parts(template, layout):
    """What a report-shaped template keeps in its report's folder and a project in three documents at its top, as (the part's path in the report's folder, the layout key that places it at the top, or None for a file kept under its own name)."""
    report = PurePosixPath(template.document_folder("rs"))
    try:
        generated = PurePosixPath(str(template.layout["generated"]).replace("\\", "/")).relative_to(report).as_posix()
    except ValueError:
        import documents
        generated = documents.LEGACY_GENERATED_FOLDER
    return [(project.CONFIG_FILE, None), (project.COMMANDS_FILE, None), (project.REFERENCES_FILE, None), (project.TITLE_FILE, None),
            (project.TEMPLATE_FOLDER, None), (project.IMAGES_FOLDER, "images"), (generated, "generated")]


def _copy_skeleton(folder, template, layout):
    """The template's skeleton copied into `folder` laid out as `layout`, `template.json` left out: for a report-shaped template what the three documents share -- config.typ, commands.typ, references.bib, the pictures -- copied up out of the report's folder to the top and the rest of that folder into the report's new one; for a documents-shaped template each document's folder into the one it is named now. Everything else the template carries at its top is copied as it stands.

    ⚠️ **Each part is copied straight to where it goes, and nothing is copied and then renamed**: a folder just written is one NextCloud's client or an antivirus may still hold a file of -- the project folder being in NextCloud is the ordinary case -- and Windows then refuses to rename it, which a run of the suite met on its own copy of a project.

    Returns (moves, the Typst root the skeleton's paths were written against): `moves` maps each part's path as it would lie had the skeleton been copied as it stands -- none of them exists -- to where it lies now, the export's folder among them though the template carries none, which is what `normalise` reads its files' old paths from.
    """
    import templates
    source = template.folder
    placed = {}
    if template.has_modes:
        for mode in project.MODES:
            placed[source / template.document_folder(mode)] = folder / PurePosixPath(layout[project.ENTRY_KEYS[mode]]).parent
        if "config" in layout and "config" not in template.layout:
            # a documents-shaped template saved before the project laid out by folders keeps what configures its documents at its top: into 000-Typst-Config/ (issue #64)
            for part in CONFIG_PARTS:
                if (source / part).exists():
                    placed[source / part] = folder / layout["config"] / part
        root_old = folder
    else:
        old = source / template.document_folder("rs")
        for part, key in _shared_parts(template, layout):
            placed[old / part] = folder / (layout[key] if key else _config_part(layout, part))
        placed[old] = folder / PurePosixPath(layout["report"]).parent
        root_old = folder / template.document_folder("rs")
    targets = {os.path.normcase(str(path)): target for path, target in placed.items()}

    def copy(path, target):
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            for child in sorted(path.iterdir()):
                copy(child, targets.get(os.path.normcase(str(child)), target / child.name))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    for child in sorted(source.iterdir()):
        if child.name != templates.FILE:
            copy(child, targets.get(os.path.normcase(str(child)), folder / child.name))
    moves = {folder / path.relative_to(source): target for path, target in placed.items()}
    return moves, root_old


def normalise(root, moves, root_old, skip=()):
    """Every `.typ` under `root` -- the new project's folder, which is its Typst root -- with the paths it writes that would no longer reach what they name rewritten (typst_paths.rewrite_file): `moves` maps each old absolute path, a file or a folder, to its new one, and `root_old` is the Typst root the files were written against. A path that still reaches its target is left exactly as it is (`#include "Sections/…"`, `project: "references.bib"`), one that does not is written root-absolute (`#import "/commands.typ": *`, `image("/Images/…")`), and nothing else of a file moves, its line endings included. Nothing under `skip` is read -- the engine's copy is the program's and is read-only. Returns (changes, unresolved) as typst_paths gives them: a literal naming nothing in the template is left as it was, as broken as the template wrote it, which a new project reports no more than a report-shaped one did."""
    import typst_paths
    root = Path(root)
    back = sorted(((Path(new), Path(old)) for old, new in moves.items()), key=lambda pair: len(pair[0].parts), reverse=True)
    skipped = [os.path.normcase(os.path.abspath(path)) for path in skip]
    changes, unresolved = [], []
    for path in sorted(root.rglob("*.typ")):
        key = os.path.normcase(os.path.abspath(path))
        if any(key == other or key.startswith(other + os.sep) for other in skipped):
            continue
        was = path
        for new, old in back:
            if path == new or new in path.parents:
                was = old / path.relative_to(new)
                break
        found, left = typst_paths.rewrite_file(path, was, root_old, root, moves)
        changes += found
        unresolved += left
    return changes, unresolved


def _document_template(mode, language, chosen):
    """The document template the `mode` document of a new project is made from: `chosen` (a DocTemplate or its reference), else the builtin standard one -- checked to make that document in `language`, so a creation is refused before it begins rather than halfway."""
    import doc_templates
    try:
        found = chosen if isinstance(chosen, doc_templates.DocTemplate) else doc_templates.find(chosen or doc_templates.default_ref(mode), mode)
    except doc_templates.DocTemplateError as exc:
        raise project.ProjectError(str(exc)) from None
    if found.error:
        raise project.ProjectError(found.error)
    if found.mode != mode:
        raise project.ProjectError(f"{found.ref} makes the document {found.mode!r}, and {mode!r} was asked for")
    if language not in found.languages:
        raise project.ProjectError(f"{found.ref} exists in {', '.join(found.languages)} and not in {language}, the project's language")
    return found


def remove_tree(folder, keep=True):
    """Everything inside `folder` taken away -- the folder itself too where `keep` is False --, read-only files included: the engine's copy is left read-only (project.sync_engine), which Windows will not delete until it is made writable. What a creation that failed wrote, and a preview's throw-away project (calc/template_preview.py)."""
    def writable(function, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        function(path)

    folder = Path(folder)
    if not folder.exists():
        return
    for child in folder.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child, onexc=writable)
        else:
            os.chmod(child, stat.S_IWRITE)
            child.unlink()
    if not keep:
        try:
            folder.rmdir()
        except OSError:
            pass


def _undo(folder, made):
    """What a creation that failed wrote, taken away. The folder was empty, or not there, when it began, so everything in it is its own."""
    remove_tree(folder, keep=not made)


# --- a folder laid out before Woodcore -------------------------------------------------

OLD_REPORT = "Statischer Rapport.typ"
OLD_CODE = "000-Python"


def old_layout(folder):
    """The layout of a folder laid out before Woodcore, or None where `folder` is not one: `000-TypstRapport/` with `000-Python/` inside it at the top of a project folder, or a report folder or an archive of one holding `000-Python/` beside its `.typ`."""
    folder = Path(folder)
    for base in ("000-TypstRapport/", ""):
        code = folder / base / OLD_CODE
        report = folder / base / OLD_REPORT
        if code.is_dir() and report.is_file():
            return {
                "report": base + OLD_REPORT,
                "pdf": "Statischer Rapport.pdf",   # where build.ps1 wrote it, stated rather than left to the default, which moved beside the .typ in v0.87: a folder converted where it stands keeps its PDF where it stands
                "sources": base + OLD_CODE,
                "generated": base + OLD_CODE,
                "archives": base + "000-Archives",
            }
    return None


def convert(folder, name=None):
    """Writes a `.woodcore` into old folder `folder`, naming its parts where they are. Nothing is moved, copied or deleted. Returns the Project; refuses a folder that is not laid out the old way, or that is already a project."""
    folder = Path(folder)
    existing = sorted(folder.glob("*" + project.EXTENSION))
    if existing:
        raise project.ProjectError(f"{folder} is already a project: {existing[0].name}")
    layout = old_layout(folder)
    if layout is None:
        raise project.ProjectError(
            f"{folder} is not a folder laid out before Woodcore -- neither 000-TypstRapport/000-Python/ nor "
            f"000-Python/ beside {OLD_REPORT} is there")
    name = (name or folder.name).strip() or folder.name
    here = project.write(folder / file_name(name), name, layout=layout)
    validation.validate_structure(here.data, "woodcore-project")
    return here
