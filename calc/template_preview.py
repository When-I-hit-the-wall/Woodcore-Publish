"""A document shown with a content template and a form chosen, and nothing of the project but its basic data: the «Templates» view of the «Projet» tab (issue #88, docs/ui/tab-project.md).

The engineer, 21.10.2026: «je décide d'afficher la convention d'utilisation avec le template de fond convention d'utilisation courte et le template de forme BFH. Et ce qui s'affiche au centre, c'est ce document avec ces deux templates […] il ne doit pas y avoir de calcul qui est fait, il ne doit pas y avoir de graphie qui a été générée par le projet».

**A throw-away project in Woodcore's cache.** A template's sections call the engine, which reads the files of `data/` -- the title page's `project-info` among them -- and Typst stops on a missing one: a template is not compiled alone. So a project is made for the preview by the very functions that make a new one (project_template.create_skeleton, create_document), named and titled as the real one, in its language, with the form and the one document asked for, and the export of a project holding nothing (export_all.seed): where a calculation is missing the document shows what a report shows for a missing value. It lies in `usersettings.cache_dir("template-preview")`, one folder per real project and one numbered folder per build, so that a build never writes where Typst may still be reading the previous one; `clean` takes away the ones before.

**Of the real project, only its name, its title page and its language are read** (project.details_of, templates.project_language): nothing is written into it, and no other file of it is opened -- what `tests/test_template_preview.py` holds.

Qt-free: the «Projet» tab runs `prepare` off the window's thread, the last request alone counting, and compiles what it gives with its PdfPane.
"""

import hashlib
import itertools
from pathlib import Path

import project
import project_template
import templates
import usersettings
import validation

CACHE = "template-preview"
# Why a preview could not be made, each said in the window's three languages by the «Projet» tab (tpv_why_<code>).
CODES = ("no_language", "bad_mode", "template_unusable", "build_failed")

_counter = itertools.count(1)


class TemplatePreviewError(validation.ValidationError):
    """A preview that could not be made: `code` (one of CODES) says why, the message names what."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def folder_for(here, root=None):
    """Where the previews of project `here` are built: a folder of Woodcore's cache named after its project file, never the project."""
    key = hashlib.sha256(str(Path(here.file).resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(root) if root is not None else usersettings.cache_dir(CACHE) / key


def prepare(here, mode, content=None, form=None, root=None):
    """A throw-away project showing document `mode` of `here` made from content template `content` (a reference or a DocTemplate; the document's own, else the builtin standard one, where none is given) with form `form` (a reference; the project's, else the settings' default, where none is given), and `here`'s name, title page and language alone. Returns the Project to compile -- its document `mode` -- or raises TemplatePreviewError."""
    if mode not in project.MODES:
        raise TemplatePreviewError("bad_mode", f"unknown document {mode!r} -- expected one of {', '.join(project.MODES)}")
    language = templates.project_language(here, fallback="")
    if language not in templates.LANGUAGES:
        raise TemplatePreviewError("no_language", f"{here.file.name}: the project states no language")
    try:   # the content template checked before anything is built: one that does not exist, or not in this language, is said as such
        content = project_template._document_template(mode, language, content or here.content_template(mode) or None)
    except project.ProjectError as exc:
        raise TemplatePreviewError("template_unusable", str(exc)) from None
    base = folder_for(here, root)
    target = base / f"{next(_counter):04d}"
    project_template.remove_tree(target, keep=False)
    try:
        skeleton = project_template.create_skeleton(target, here.name, language, form=form, **project.details_of(here))
        return project_template.create_document(skeleton, mode, content)
    except project.ProjectError as exc:
        project_template.remove_tree(target, keep=False)
        raise TemplatePreviewError("build_failed", str(exc)) from None
    except OSError as exc:
        project_template.remove_tree(target, keep=False)
        raise TemplatePreviewError("build_failed", str(exc)) from None


def clean(here, keep=None, root=None):
    """The previews of `here` built before taken away, `keep` -- the Project of the one shown -- left. Returns how many were taken. A folder Typst still holds open is left for the next time."""
    base = folder_for(here, root)
    if not base.is_dir():
        return 0
    kept = Path(keep.root).resolve() if keep is not None else None
    taken = 0
    for folder in sorted(base.iterdir()):
        if folder.is_dir() and folder.resolve() != kept:
            try:
                project_template.remove_tree(folder, keep=False)
            except OSError:
                continue
            taken += not folder.exists()
    return taken
