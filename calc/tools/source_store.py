"""Where a tab's cases lie and how one is saved, written once and without Qt (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, ARCH-004, ARCH-005).

A case is checked before it is written -- its id well formed and free, its source one its domain reads -- and then written, the file of its old id taken away where it was renamed. `SourceStore` is what a tab built on a type (tab_host.py) owns through its context; `LoadTab` calls the same functions (`id_refusal`, `check_refusal`, `write`) until the wind leaves it.

**A save is one guarded writer** (`SourceStore.save`, in `WRITERS`): refused in a project open read-only, and followed by the domains' files reconciled where the store says `sync_domain` (tab_guard.py) -- so the order is always «write → the domain's before_export, where it has one → export → unfold → sync», the last by the guard once the save returns (ARCH-RISK-014). Nothing here imports PySide6.
"""

import json

import engine
import project
import registry
import validation
from case_list_logic import next_free_id


def saved_ids(folder):
    """The ids of the cases in `folder`, sorted."""
    return sorted(p.stem for p in folder.glob("*.json")) if folder.is_dir() else []


def id_refusal(module, taken, source, current_id):
    """Why `source` cannot be saved under its id -- ("taken", {"id": …}) for an id malformed or held by another case, compared without case --, else None."""
    cid = source.get("id") or ""
    if not module.ID_PATTERN.match(cid):
        return "taken", {"id": cid}
    held = {t.lower() for t in taken} - ({current_id.lower()} if current_id else set())
    if cid.lower() in held:
        return "taken", {"id": cid}
    return None


def check_refusal(module, source):
    """Why the domain refuses `source` -- ("invalid", {"error": …}) --, else None."""
    try:
        module.check_source(source, "%s/%s.json" % (module.FOLDER, source.get("id")))
    except (validation.ValidationError, ValueError) as exc:
        return "invalid", {"error": str(exc)}
    return None


def is_rename(source, current_id):
    """Whether saving `source` renames the case open."""
    return bool(current_id) and current_id != source.get("id")


def write(folder, source, current_id):
    """`source` written into `folder` under its id; the file of the old id taken away where it was renamed."""
    folder.mkdir(parents=True, exist_ok=True)
    if is_rename(source, current_id):
        (folder / ("%s.json" % current_id)).unlink(missing_ok=True)
    engine.write_json(folder / ("%s.json" % source["id"]), source)


class SourceStore:
    """The cases of one domain of a tab built on a type: where they lie, read, checked, saved. `app` is the window, which the read-only guard asks; `sync_domain` says the domains' files follow a save (the former `SYNC_DOMAIN` of a tab's class); `unfold` that the cases' files of the domain's kind are written or refreshed with the export (a calculation tab's)."""

    WRITERS = ("save",)

    def __init__(self, app, module, sync_domain=True, unfold=True):
        self.app = app
        self.module = module
        self.sync_domain = sync_domain
        self.unfold = unfold

    def folder(self):
        return project.current().sources_dir / self.module.FOLDER

    def all_ids(self):
        """Every id of the folder -- what a new id must differ from, the cases of several tabs sharing one folder (the member checks, issue #112)."""
        return saved_ids(self.folder())

    def ids(self):
        """The ids of this tab's cases: every one of the folder, or those its domain says are its own (`owns(src)`: the member checks' tabs, each listing its kinds, issue #112)."""
        found = saved_ids(self.folder())
        owns = getattr(self.module, "owns", None)
        if owns is None:
            return found
        out = []
        for cid in found:
            try:
                src = json.loads(self.path(cid).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(src, dict) and owns(src):
                out.append(cid)
        return out

    def owns_archived(self, path):
        """Whether an archived case of the folder is this tab's (`owns`), every one where the domain says nothing."""
        owns = getattr(self.module, "owns", None)
        if owns is None:
            return True
        try:
            src = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        return isinstance(src, dict) and owns(src)

    def path(self, cid):
        return self.folder() / ("%s.json" % cid)

    def read(self, path):
        """A saved case read to be edited: its domain's reading, and a source the domain refuses opened as it is, so that it can be repaired."""
        try:
            return self.module.read_source(path)
        except validation.ValidationError:
            return json.loads(path.read_text(encoding="utf-8"))

    def new_source(self, prefix):
        return self.module.new_source(next_free_id(self.all_ids(), prefix))

    def id_refusal(self, source, current_id):
        return id_refusal(self.module, self.all_ids(), source, current_id)

    def check_refusal(self, source):
        return check_refusal(self.module, source)

    def save(self, source, current_id):
        """The case written (`write`) and the export rebuilt with it -- calculations.json, then the cases' files of the domain's kind --; returns "" or the export's failure, the case staying saved. The caller has checked it (`id_refusal`, `check_refusal`) and asked the rename."""
        # a domain that saves its cases itself (`save_case(here, source, current_id)`: the member checks, which move a check's file when its kind changes, issue #112) -- "" or the export's failure
        saver = getattr(self.module, "save_case", None)
        if saver is not None:
            return saver(project.current(), source, current_id)
        write(self.folder(), source, current_id)
        # what a domain does between the case written and the export (`before_export(here)`, optional): the permanent loads take the copies of the engineer's materials their layers name (issue #110, REQ-013) -- a failure said like the export's, the case staying saved
        hook = getattr(self.module, "before_export", None)
        if hook is not None:
            try:
                hook(project.current())
            except validation.ValidationError as exc:
                return str(exc)
        return self.export()

    def export(self):
        """calculations.json rebuilt, then, where `unfold`, the cases' files of the domain's kind written or refreshed -- what «Affichage» shows and a section includes, there as soon as the case is saved (REQ-015 of the spec 2026-10-22-onglet-neige-type). "" or the failure, said by the caller."""
        here = project.current()
        exporter = getattr(self.module, "export_cases", None)
        if exporter is not None:
            # a domain that exports its cases itself (`export_cases(here)`: the member checks, data/checks.json and their files)
            try:
                with project.using(here):
                    exporter(here)
            except Exception as exc:  # broad: the exporter's own message is what helps, said in the status bar
                return str(exc)
            return ""
        try:
            registry.export(here)
            if self.unfold:
                from domains import unfold
                data = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
                with project.using(here):
                    unfold.unfold_domains(here, self.module.DOMAIN, data)
        except Exception as exc:  # broad: the exporter's own message is what helps, said in the status bar; the case stays saved
            return str(exc)
        return ""
