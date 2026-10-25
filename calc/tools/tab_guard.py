"""What every editor tab's writers go through: refused in a project opened read-only, and followed by the reconciliation of the domains' files where the tab makes domains (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, ARCH-001, ARCH-RISK-101).

Split out of woodcore_gui.py, which re-exports every name (the tests read `woodcore_gui.WRITERS`). Until v0.120 the window wrapped the writers of a list of classes and of their mixins, by name, in `vars()` of each -- so a `save` moved into a base class shared by several tabs was no longer guarded, and the domains' files were no longer written after it, without a word. Now `guard(cls)` walks the whole hierarchy of a tab, its base classes included, and wraps each writer **where it is defined, once**: a base shared by twenty tabs is wrapped one time, and a subclass that calls `super().save()` does not run the guard twice. Whether the domains' files follow is the tab's own declaration, `SYNC_DOMAIN = True` on its class, read when the writer runs -- not a list kept beside the classes.
"""

import functools
import inspect

import project

# Every way an editor tab writes a source: its «Enregistrer» and its Ctrl+S, «Supprimer» and a drop on «Archives» or out of it, a drop into a folder, and what each tab added since -- the one list, read by name; a name no tab, service or widget defines any more leaves it (tests/test_tab_registry.py: «create_plans», gone with the plans of v0.83, left in issue #107).
WRITERS = ("save", "delete", "on_moved", "delete_document", "delete_sheet", "write_enabled", "write_title",
           "write_add_section", "write_add_group", "write_remove", "write_rename", "write_move",
           "write_object", "write_node_state", "write_heading_line", "write_add_object", "write_remove_object", "write_tag", "write_import",
           "write_sync_import", "write_sync_flag", "write_share", "write_stop_share", "add_annex_source", "replace_annex_source",
           # v0.116: the plan tabs' PDF bundles, their sheets moved between them, the list of the positions made as a sheet, and a frame of the document view resized or deleted (drawing_tab.DrawingTab)
           "new_bundle", "rename_bundle", "delete_bundle", "on_sheets_moved", "export_bundle", "create_position_list", "write_frame_crop", "on_frames_delete",
           # issue #64: the documents of Imported Plans/ read again against their files as a tab of plans is shown (drawing_tab_documents.DrawingDocumentsMixin)
           "write_refresh_documents",
           # issue #64: an annex's PDF written over in Appendix/ read again as the «Annexes» tab is shown (annex_tab.AnnexTab)
           "write_refresh_sources",
           # issue #15: the «Domaines» tab's domain duplicated and its id changed (formula_tab.FormulaTab)
           "duplicate_domain", "rename_id",
           # issue #113: the «Domaines» tab's form, code and display -- a field of a row, a line written at the foot or by the +, rows deleted, undone, moved, links written, an argument, the code's buffer, the domain's options and level, a line's display reset (formula_tab.FormulaTab)
           "write_field", "write_new_line", "write_delete_rows", "write_undo", "write_move_rows", "write_links", "write_argument", "write_code",
           "write_domain_option", "write_reset_line",
           # issue #16: the annexes' excerpts made by a frame drawn, a range of pages or a frame found (annex_tab.AnnexTab)
           "extract_annex_pages", "extract_annex_rects", "write_extracted",
           # issue #94: a line of a case's file, its figure and its domain's level set in «Affichage» (spec 2026-10-22-onglet-neige-type, ARCH-RISK-W06; since issue #95 the writers of calc_display.DomainDisplay, guarded by guard_service: these names stay for the tabs that still define them)
           "write_line_display", "write_figure", "write_domain_level",
           # spec 2026-10-23-onglet-vent-briques: a table of a case's file shown or masked, its title and its note (calc_display.DomainDisplay, guarded by guard_service)
           "write_table",
           # issue #110: a copy of the engineer's material taken again, or kept, in the project (material_copies.MaterialCopies, guarded by guard_service; the project's own library, «save_project_library», went with it)
           "take_material", "keep_material",
           # issue #46: the project's building for VKF 15-15, saved from the «Résistance au feu» tab (fire_check_tab.FireCheckTab)
           "save_building",
           # spec 2026-10-15: an unfolded check's lines imported, taken back, reinserted, chosen in a conflict, and the check regenerated (formula_tab_unfold.FormulaUnfoldMixin)
           "write_unfold_import", "write_unfold_import_all", "write_unfold_take_back", "write_unfold_reinsert", "write_unfold_choice", "write_unfold_regenerate")
# (issues #88, #90: the «Projet» tab's form applied and a document made, «write_apply_form» and «write_create_document», are its service's since issue #107 -- project_services.ProjectActions.WRITERS, guarded by guard_service)

_MARK = "_woodcore_tab_guard"


def _app_of(holder):
    """The window whose project a writer writes into: the tab's, the tab of an archive's actions, or -- a service of a tab built on a type (tab_host.py) -- its context's. A writer whose window cannot be found would let an edit through in a project open read-only, without a word (spec 2026-10-23-onglets-types-et-services, ARCH-RISK-001)."""
    return getattr(holder, "app", None) or getattr(getattr(holder, "tab", None), "app", None) or getattr(getattr(holder, "ctx", None), "app", None)


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


def _makes_domains(holder):
    """Whether the domains' files follow a writer of `holder`: a store's own `sync_domain` (source_store.SourceStore, ARCH-004), else the tab's class `SYNC_DOMAIN` -- False for a tab built on a type, whose writers are its services' and its store's --, else a service's context's store's: the files follow once, after the writer that wrote."""
    own = getattr(holder, "sync_domain", None)
    if own is not None:
        return bool(own)
    declared = getattr(type(holder), "SYNC_DOMAIN", None)
    if declared is not None:
        return bool(declared)
    return bool(getattr(getattr(getattr(holder, "ctx", None), "store", None), "sync_domain", False))


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


def guard_service(cls):
    """Every writer a service class names in its `WRITERS` -- a service of a tab built on a type, or the store of its cases (tab_host.py, source_store.py) -- wrapped where it is defined in its hierarchy, once: refused read-only, followed by the domains' files where its store says `sync_domain` (spec 2026-10-23-onglets-types-et-services, ARCH-004). A name in `WRITERS` that no class of the hierarchy defines is an error: a writer declared and never guarded is what this module exists to prevent. Returns `cls`."""
    for name in getattr(cls, "WRITERS", ()):
        owner = next((klass for klass in own_classes(cls) if name in vars(klass)), None)
        if owner is None:
            raise AttributeError(f"{cls.__name__} declares the writer {name!r} and defines none")
        method = vars(owner)[name]
        if callable(method) and not getattr(method, _MARK, False):
            setattr(owner, name, refused_when_read_only(method, sync=_makes_domains))
    return cls


def guard_actions(actions_cls):
    """The archive every tab shares (source_archive.Actions): its archive, restore and purge refused read-only, and always followed by the domains' files -- an archived domain's `.typ` goes into the archives with it."""
    for name in ("archive", "restore", "purge"):
        method = vars(actions_cls)[name]
        if not getattr(method, _MARK, False):
            setattr(actions_cls, name, refused_when_read_only(method, sync=lambda _self: True))
