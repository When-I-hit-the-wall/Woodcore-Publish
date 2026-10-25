"""The life of a draft -- new, a copy, back to what is saved, a case loaded, the form once its case is gone -- written once and without Qt (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, ARCH-005, ARCH-006).

Until issue #95 (v0.125) these transitions were `source_editor.SourceEditorTab`'s methods. They are functions of a **host** now -- the editor tab, or the tab built on a type (tab_host.py) --, which both call. A host has `source`, `current_id`, `dirty`, `ids`, `DUPLICATE_FORGETS`, and `confirm_leave()`, `make_source()`, `after_new()`, `duplicate_id(source)`, `draft()`, `fill_form()`, `refresh()`, `reload_list(select)`, `read_saved(path)`, `sources_dir()`, and, where it keeps its own way of opening the first source, `load_first()`. Nothing here imports PySide6.
"""


def new(host):
    """«Nouveau»: a new source, carrying the dot -- the draft is left first."""
    new_from(host, None)


def new_from(host, source):
    """A new source, carrying the dot -- `source` where one is given (a build-up made from a template, issue #111), else the host's new one; the draft is left first."""
    if not host.confirm_leave():
        return
    host.source = source if source is not None else host.make_source()
    host.current_id = None
    host.dirty = True
    host.after_new()
    host.fill_form()
    host.refresh()
    host.reload_list()


def duplicate(host):
    """«Dupliquer»: the draft copied under a new id, without what a copy does not keep (`DUPLICATE_FORGETS`, its name)."""
    if not host.confirm_leave():
        return
    source = host.draft()
    source["id"] = host.duplicate_id(source)
    for key in host.DUPLICATE_FORGETS:
        source.pop(key, None)
    host.source = source
    host.current_id = None
    host.dirty = True
    host.fill_form()
    host.refresh()
    host.reload_list()


def revert(host):
    """«Annuler les modifications»: the case as it is saved, or a new one where none is."""
    if host.current_id:
        host.load(host.current_id)
    else:
        host.new()


def load(host, cid):
    """The saved case `cid` in the form, with no dot."""
    host.source = host.read_saved(host.sources_dir() / ("%s.json" % cid))
    host.current_id = cid
    host.dirty = False
    host.fill_form()
    host.refresh()


def blank(host):
    """The form once its source is gone and nothing is left to open: a new source, as an empty tab shows at the start, with no dot -- nobody asked for it. «Nouveau»'s draft carries the dot, and here it was saved by itself as soon as the engineer looked elsewhere, an empty `SN-01.json` that «Supprimer» replaced by the next one (issue #97). Typed into, it is a draft like any other."""
    host.source = host.make_source()
    host.current_id = None
    host.after_new()
    host.fill_form()
    host.dirty = False
    host.refresh()
    host.reload_list()


def open_first(host):
    """What the form shows once the source it showed is gone: the first source of the list, else a new one. A host that keeps its own way of opening the first (`load_first`) says so."""
    if hasattr(host, "load_first"):
        host.load_first()
        return
    host.reload_list()
    if host.ids:
        host.load(host.ids[0])
        host.reload_list(host.ids[0])
    else:
        blank(host)


def after_archive(host):
    """The source the form showed was archived: a new one opens, as deleting always did -- with no dot (`blank`)."""
    host.reload_list()
    blank(host)


def shown(host):
    """The tab brought forward: `live` from now on, the draft kept as it is typed -- the list filled again, the form filled from it, its dot kept -- and computed."""
    host.live = True
    dirty = host.dirty
    host.source = host.draft()
    host.reload_list(host.current_id)
    host.fill_form()
    host.dirty = dirty
    host.refresh()


def discard(host):
    """«Abandonner» where a draft never saved gives its place to the first source of the list (`DISCARD_OPENS_FIRST`): the draft forgotten."""
    host.dirty = False
    if host.current_id is None:
        host.load_first()
