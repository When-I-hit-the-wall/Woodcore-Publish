"""What every editor tab's writers go through: refused in a project opened read-only, and followed by the reconciliation of the domains' files where the tab makes domains (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, ARCH-001, ARCH-RISK-101).

Split out of woodcore_gui.py, which re-exports every name (the tests read `woodcore_gui.WRITERS`). Until v0.120 the window wrapped the writers of a list of classes and of their mixins, by name, in `vars()` of each -- so a `save` moved into a base class shared by several tabs was no longer guarded, and the domains' files were no longer written after it, without a word. Now `guard(cls)` walks the whole hierarchy of a tab, its base classes included, and wraps each writer **where it is defined, once**: a base shared by twenty tabs is wrapped one time, and a subclass that calls `super().save()` does not run the guard twice. Whether the domains' files follow is the tab's own declaration, `SYNC_DOMAIN = True` on its class, read when the writer runs -- not a list kept beside the classes.
"""

import functools
import inspect

import project

# Every way an editor tab writes a source: its «Enregistrer» and its Ctrl+S, «Supprimer» and a drop on «Archives» or out of it, a drop into a folder, the several plans «Nouveau» makes from the pages of one PDF (v0.83), and what each tab added since -- the one list, read by name.
WRITERS = ("save", "delete", "on_moved", "create_plans", "delete_document", "delete_sheet", "write_enabled", "write_title",
           "write_add_section", "write_add_group", "write_remove", "write_rename", "write_move",
           "write_object", "write_node_state", "write_heading_line", "write_add_object", "write_remove_object", "write_tag", "write_import",
           "write_sync_import", "write_sync_flag", "write_share", "write_stop_share", "add_annex_source", "replace_annex_source",
           # v0.116: the plan tabs' PDF bundles, their sheets moved between them, the list of the positions made as a sheet, and a frame of the document view resized or deleted (drawing_tab.DrawingTab)
           "new_bundle", "rename_bundle", "delete_bundle", "on_sheets_moved", "export_bundle", "create_position_list", "write_frame_crop", "on_frames_delete",
           # issue #64: the documents of Imported Plans/ read again against their files as a tab of plans is shown (drawing_tab_documents.DrawingDocumentsMixin)
           "write_refresh_documents",
           # issue #64: an annex's PDF written over in Appendix/ read again as the «Annexes» tab is shown (annex_tab.AnnexTab)
           "write_refresh_sources",
           # issue #15: the «Formules» tab's domain duplicated, its id changed, an option of a closed block and a text written (formula_tab.FormulaTab)
           "duplicate_domain", "rename_id", "write_options", "write_text",
           # issue #19: a line's printing set in the «Formules» tab's «Affichage» (formula_tab.FormulaTab)
           "write_display",
           # issue #16: the annexes' excerpts made by a frame drawn, a range of pages or a frame found (annex_tab.AnnexTab)
           "extract_annex_pages", "extract_annex_rects", "write_extracted",
           # issue #94: a line of a case's file, its figure and its domain's level set in «Affichage» (calc_tab.DeclaredTabMixin, spec 2026-10-22-onglet-neige-type, ARCH-RISK-W06)
           "write_line_display", "write_figure", "write_domain_level",
           # issues #35-#37: the project's own materials saved (load_tab.DeadLoadTab)
           "save_project_library",
           # issue #46: the project's building for VKF 15-15, saved from the «Résistance au feu» tab (fire_check_tab.FireCheckTab)
           "save_building",
           # spec 2026-10-15: an unfolded check's lines imported, taken back, reinserted, chosen in a conflict, and the check regenerated (formula_tab_unfold.FormulaUnfoldMixin)
           "write_unfold_import", "write_unfold_import_all", "write_unfold_take_back", "write_unfold_reinsert", "write_unfold_choice", "write_unfold_regenerate",
           # issues #88, #90: the «Projet» tab's form applied to the project and a document made from its content template (project_tab.ProjectTab)
           "write_apply_form", "write_create_document")

_MARK = "_woodcore_tab_guard"


def _app_of(holder):
    return getattr(holder, "app", None) or getattr(getattr(holder, "tab", None), "app", None)


def _sync_domains(app):
    """The domains' files reconciled (domains/domain_file.py `sync`, issue #64): a domain saved, renamed, archived or restored has its `.typ` written or archived at once. Nothing in a project open read-only, nor in one laid out before, which has no such files; a file that cannot be written is said by the next export, which reconciles again."""
    if getattr(app, "read_only", False):
        return
    try:
        from domains import domain_file
        domain_file.sync(project.current())
    except (OSError, project.ProjectError):
        pass


def refused_when_read_only(method, sync=None):
    """`method` refused, and said so, while the window it belongs to has its project read-only -- and, where it ran, followed by the domains' files reconciled when `sync(self)` says the tab makes domains. Called with no more arguments than it takes: a Qt signal hands a slot what it carries -- «clicked» a bool -- and the method may take none."""
    parameters = list(inspect.signature(method).parameters.values())[1:]
    variadic = any(p.kind == p.VAR_POSITIONAL for p in parameters)
    positional = len([p for p in parameters if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)])

    @functools.wraps(method)
    def guarded(self, *args, **kwargs):
        app = _app_of(self)
        if getattr(app, "read_only", False):
            app.refuse_read_only()
            return False
        result = method(self, *(args if variadic else args[:positional]), **kwargs)
        if sync is not None and sync(self):
            _sync_domains(app)
        return result
    setattr(guarded, _MARK, True)
    return guarded


def _makes_domains(tab):
    return bool(getattr(type(tab), "SYNC_DOMAIN", False))


def own_classes(cls):
    """`cls` and every class of its hierarchy that is Woodcore's own -- its mixins (issue #30) and the base classes it shares with other tabs -- in the order of its MRO: what «a method the tab defines» means once tabs share a base. Qt's and Python's classes are not Woodcore's."""
    return [klass for klass in cls.__mro__ if klass.__module__ not in ("builtins",) and not klass.__module__.startswith(("PySide6", "shiboken"))]


def guard(cls):
    """Every writer of `cls`'s hierarchy wrapped where it is defined, once (refused read-only, the domains' files following where the tab declares `SYNC_DOMAIN`). Returns `cls`."""
    for owner in own_classes(cls):
        for name in WRITERS:
            method = vars(owner).get(name)
            if method is not None and callable(method) and not getattr(method, _MARK, False):
                setattr(owner, name, refused_when_read_only(method, sync=_makes_domains))
    return cls


def guard_actions(actions_cls):
    """The archive every tab shares (source_archive.Actions): its archive, restore and purge refused read-only, and always followed by the domains' files -- an archived domain's `.typ` goes into the archives with it."""
    for name in ("archive", "restore", "purge"):
        method = vars(actions_cls)[name]
        if not getattr(method, _MARK, False):
            setattr(actions_cls, name, refused_when_read_only(method, sync=lambda _self: True))
