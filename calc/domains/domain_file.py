"""One `.typ` per domain of a specialised tab (issue #64, spec 2026-10-15-structure-projet-dossiers REQ-004, REQ-010, REQ-015, ARCH-004; spec 2026-10-21-commandes-typst-refonte, ARCH-011).

In a project laid out by folders, every domain a specialised tab makes -- a snow load, a wind load, a permanent load, a connector, a polar moment, a member check, a steel check, a script -- has a Typst file of its own in its kind's folder (project.DOMAIN_FOLDERS: `Variable-loads/Snow/<id>.typ`, `Timber-checks/Tension/<id>.typ` …), which a section prints with `#include domain-file("snow-load", "neige")`. **The file is the domain written out whole**, `#var` by `#var`, by calc/domains/unfold.py (REQ-017) -- at the tab's save and at every export. Until the spec 2026-10-21-commandes-typst-refonte it was a stub calling a command that printed the domain folded (`#show-calc`, `#show-check-member` …); those commands are retired, and a stub an earlier Woodcore wrote is written over by the domain (`unfold.LEGACY_STUBS`).

**The file is the engineer's once written** (CON-002): he completes it in VS Code, and Woodcore never writes over what he changed -- its lines are compared three ways with what it wrote (calc/domains/unfold.py).

**One reconciliation** (`sync`), run at every export and after every save of a tab (spec §13 ARCH-RISK-B06): a file of a domain folder that no domain names any more -- archived, renamed, or a check whose kind changed -- is put into its folder's `archives/` where it is a stub an earlier Woodcore wrote, untouched; any other is the engineer's, left where it is and said (`domain_file_orphan`). Nothing is done in a project laid out before, which has no such folders.

Qt-free.
"""

import json
import os
import time
from pathlib import Path

import engine
import project
import structure

def path_of(here, kind, domain_id, sub=None):
    """The file of domain `domain_id` of `kind` -- in its `sub` kind's folder for a member check or a steel check -- or None in a project laid out before."""
    folder = here.domain_dir(kind, sub)
    return None if folder is None else folder / f"{domain_id}.typ"


def _kind_of(path):
    """A member check's or a steel check's kind, read from its source -- None where the file cannot say (the export says why)."""
    try:
        kind = json.loads(Path(path).read_text(encoding="utf-8")).get("kind")
    except (OSError, ValueError, AttributeError):
        return None
    return kind if isinstance(kind, str) else None


def domains(here):
    """Every domain of the specialised tabs project `here` holds, as {(kind, sub): [id, …]} -- `sub` the kind of a member check or a steel check, None for every other -- read from the sources the tabs write (archives left out, as every tab's own listing leaves them). A check whose kind is no kind of the table is left out: its source is malformed, and the export stops on it, naming it."""
    from domains import connection, connector, dead_load_source, member_check, script, snow_source, steel_check, wind_source
    found = {}

    def add(kind, sub, domain_id):
        found.setdefault((kind, sub), []).append(domain_id)

    for kind, paths in (("snow-load", snow_source.source_paths(here)), ("wind-load", wind_source.source_paths(here)),
                        ("dead-load", dead_load_source.source_paths(here)), ("connector", connector.source_paths(here.connectors_dir)),
                        ("connection", connection.source_paths(here.connections_dir))):
        for path in paths:
            add(kind, None, path.stem)
    for kind, paths in (("check", member_check.source_paths(here)), ("steel", steel_check.source_paths(here))):
        for path in paths:
            sub = _kind_of(path)
            if sub in project.KIND_FOLDERS[kind]:
                add(kind, sub, path.stem)
    for path in script.source_paths(here):
        add("script", None, path.stem)
    return found


def _archive(path):
    """`path` moved into `archives/` beside it, under its own name -- `<yymmdd-hhmmss>-<name>` where one of that name is there already. Returns where it went."""
    folder = path.parent / project.DOMAIN_ARCHIVES
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / path.name
    if target.exists():
        target = folder / f"{time.strftime('%y%m%d-%H%M%S')}-{path.name}"
    os.replace(path, target)
    return target


def _domain_files(here):
    """Every `.typ` at the top of a domain folder (archives aside), as [(kind, sub, path)]."""
    out = []
    for kind in project.DOMAIN_FOLDERS:
        subs = list(project.KIND_FOLDERS.get(kind, {})) or [None]
        for sub in subs:
            folder = here.domain_dir(kind, sub)
            if folder is not None and folder.is_dir():
                out += [(kind, sub, path) for path in sorted(folder.glob("*.typ"))]
    return out


def sync(here):
    """Every file of a domain folder whose domain is gone put into its folder's archives where it is an untouched stub of an earlier Woodcore, said where it is the engineer's (module docstring). Returns (archived, notes): the files archived, and an `engine.Note` per file left where it is that no domain names any more. Nothing for a project laid out before. A domain's own file is written by calc/domains/unfold.py, never here."""
    from domains import unfold
    archived, notes = [], []
    if not here.has_folders:
        return archived, notes
    present = domains(here)
    bases = {}

    def written_out(kind):
        """The ids of the domains of `kind` Woodcore wrote out from the export (calc/domains/unfold.py) -- a load's case of a workbook among them, which is no source of a tab and is no orphan for it."""
        if kind not in bases:
            try:
                bases[kind] = set(unfold.read_base(here, kind)["domains"]) if kind in unfold.DOMAIN_KINDS else set()
            except Exception:  # broad: a base that cannot be read names nothing here, and the export names it
                bases[kind] = set()
        return bases[kind]

    wanted = {(kind, sub, domain_id) for (kind, sub), ids in present.items() for domain_id in ids}
    for kind, sub, path in _domain_files(here):
        if (kind, sub, path.stem) in wanted or path.stem in written_out(kind):
            continue
        if unfold.is_legacy_stub(here, kind, path.stem, path):
            archived.append(_archive(path))
        else:
            notes.append(engine.Note("domain_file_orphan", f"{here.rel(path)}: no domain of its folder is named {path.stem!r} any more -- the file is yours and is left where it is",
                                     file=here.rel(path)))
    return archived, notes


def include_call(here, kind, domain_id, sub=None):
    """`#include "/Variable-loads/Snow/<id>.typ"`: what prints the domain from any document by its path. None in a project laid out before."""
    path = path_of(here, kind, domain_id, sub)
    return None if path is None else f'#include "{here.from_root(path)}"'
