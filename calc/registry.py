"""Builds data/calculations.json (docs/domain/calculation-domains.md §3.3): every calculation domain, its instances the cases entered in Woodcore or the rows of a norm table.

A *domain* is one kind of calculation (`snow-load`, `dead-load`, `wind-load`); an *instance* is one case of it. The cases of the three loads are entered in Woodcore's tabs -- `Woodcore-Datei/loads/<kind>/<id>.json`, one per case (issues #35-#37, decision D-04) -- each computed in Python by its source module (`SOURCE_MODULES`: `source_paths(here)`, `read_source(path)`, `build_instance(src, here)`), each saying where it came from (`engine: "python"`, `source_file`). Their drawings (`figures`) are written beside the export -- `Permanent-loads/Exports/Figures/` in a project laid out by folders, issue #64 (`write_files`).

One domain is computed by nobody: `live-load` (Nutzlasten) is Tabelle 8 of SIA 261, whose instances are its categories (section 3.3septies); its module exposes `build_instances()`.

**No load workbook is read** (issue #109, decision D-33: «il n'y aura plus jamais de feuille excel à lire pour le vent, ni pour la neige, ni pour les charges permanentes»). Until then the `WL-*`, `SL-*` and `EL+AL-*` sheets of every `*Belastungsannahmen*.xlsm|xlsx` of the project folder were cases beside the sources. What stays of the workbook is its name: a file that carries it is said at every full export, never opened (`load_workbook_names`, `workbook_note`), so that its cases are not lost without the engineer knowing.
"""

import importlib

from pathlib import Path

import engine
import validation
from domains import links  # a load source that follows a variable (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import dead_load, live_load, snow_source, wind_source

# The name a load workbook of the office carries, and its suffixes: what `load_workbook_names` looks for -- the file is never opened (issue #109, REQ-003)
WORKBOOK_NAME = "Belastungsannahmen"
WORKBOOK_SUFFIXES = (".xlsm", ".xlsx")
# Excel's lock file of a workbook open, «~$02_Belastungsannahmen.xlsm»: no workbook of the engineer's
LOCK_PREFIX = "~$"

# Order here is the order the domains appear in data/calculations.json, and so in docs/typst-reference.xlsx: the loads entered in Woodcore first, then the norm tables (live_load), which is SIA 261's own chapter order. A domain's label, action and engine are read off its module (ARCH-001 of issue #109).
DOMAIN_MODULES = (dead_load, snow_source, wind_source, live_load)

# The modules computing a domain's instances from the project's own sources, by domain (D-04): imported by name when the export asks.
SOURCE_MODULES = {dead_load.DOMAIN: "domains.dead_load_source", snow_source.DOMAIN: "domains.snow_source", wind_source.DOMAIN: "domains.wind_source"}
# The export's folder of the drawings an instance carries (an instance's `figures[].file` is relative to data/)
FIGURES_FOLDER = "calculations"
# 1.9 (issue #109, D-33): 1.8 without the load workbooks -- no `sheet_prefix`, no instance naming a `workbook` or a `sheet`, an engine `python` or `norm`. Written by every export from v0.125; an export written before is refused where it is read (schemas/calculations.schema.json, lib/calc-engine-core.typ), never by the export that replaces it
SCHEMA_VERSION = "1.9"


def source_module(domain):
    """The module computing `domain`'s instances from the project's sources, or None where it has none (yet)."""
    name = SOURCE_MODULES.get(domain)
    if name is None:
        return None
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            return None
        raise


def _sources(here):
    """{domain: [(path, source), ...]} -- every source of the project's load folders, read and checked, in file-name order."""
    out = {}
    if here is None:
        return out
    for domain in SOURCE_MODULES:
        module = source_module(domain)
        if module is None:
            continue
        out[domain] = [(path, module.read_source(path)) for path in module.source_paths(here)]
    return out


def load_workbook_names(folder):
    """The names of the load workbooks in `folder`, by name alone and never opened (issue #109, REQ-003): every `.xlsm`/`.xlsx` whose name contains `Belastungsannahmen`, without case, in the folder itself and not below it, Excel's `~$` lock files left out; in file-name order without case."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    found = [p.name for p in folder.iterdir()
             if p.is_file() and not p.name.startswith(LOCK_PREFIX)
             and WORKBOOK_NAME.casefold() in p.name.casefold() and p.suffix.casefold() in WORKBOOK_SUFFIXES]
    return sorted(found, key=str.casefold)


def workbook_note(folder):
    """The warning of a full export whose project folder holds a load workbook (UI-001): one `Note` naming every such file, saying it is read no more and where the cases are entered -- None where there is none. Given by `export_all` only, never by `export`, which a tab runs at each save (C-2)."""
    names = load_workbook_names(folder)
    if not names:
        return None
    files = ", ".join(names)
    return engine.Note("load_workbook_not_read",
                       f"a load workbook is in the project folder ({files}): Woodcore no longer reads it -- the cases of wind, snow and permanent loads are entered in the tabs Wind, Snow and Self-weight and superimposed load",
                       files=files)


def old_export_note(data_dir):
    """What `woodcore-cli check` says of a data/calculations.json written by an earlier Woodcore (REQ-007, C-1): a `Note` naming its version and the remedy -- «Import données» once --, None where the file is the current version, is missing or cannot be read (the export writes it anew). Never a refusal: the export is the remedy, and reads the old file only through `engine.previous_json`."""
    found = engine.previous_json(Path(data_dir) / "calculations.json")
    version = (found or {}).get("schema_version") if isinstance(found, dict) else None
    if version is None or version == SCHEMA_VERSION:
        return None
    return engine.Note("calculations_old_export",
                       f"data/calculations.json was written by an earlier version of Woodcore (schema {version}, this one writes {SCHEMA_VERSION}) -- the report does not compile until «Import données» has written it again once",
                       version=str(version), current=SCHEMA_VERSION)


def build_calculations(here=None, files=None, notes=None):
    """Every domain and its instances: the cases entered in Woodcore of the project `here` (None: none -- the empty calculations a new project starts with, export_all.seed) and the norm tables' rows. `files`, a dict, is given the drawings the instances carry, {path under data/: SVG text} (`write_files`); `notes`, a list, what is worth saying -- the warnings of the load sources that follow a variable (issue #42).

    A load source whose fields follow a variable (`links`) is built once every load it names is: after the sources that follow nothing, in as many rounds as the chain is long, the «Formule» domains computed against the loads built so far and those naming one built last (`_follow_loads`). A chain that comes back to where it began stops the export, naming it (REQ-007)."""
    sources = _sources(here)
    deferred = []
    notes = notes if notes is not None else []
    domains = {}
    for module in DOMAIN_MODULES:
        if module.DOMAIN in SOURCE_MODULES:
            instances = {}
            # the cases entered in Woodcore, in file-name order: computed here, each saying where it came from (D-04)
            for path, src in sources.get(module.DOMAIN, ()):
                where = "%s/%s" % (source_module(module.DOMAIN).FOLDER, path.name)
                if links.is_linked(src, source_module(module.DOMAIN).LINKABLE):
                    deferred.append((module, where, src))
                    instances[src["id"]] = None      # its place in file-name order, filled once what it follows is built
                    continue
                instances[src["id"]] = _build_source(module, where, src, here, files, notes=notes)
        else:
            # A norm table: its instances are the table's own rows (docs/domain/loads.md §3.3septies).
            instances = module.build_instances()
        domains[module.DOMAIN] = {
            "label": module.LABEL,
            # permanent or variable: declared by the module, like its engine, so the classification a load combination will read lives where the load is calculated
            "action": module.ACTION,
            "engine": module.ENGINE,
            "instances": instances,
        }
    _follow_loads(deferred, domains, here, files, notes)
    return {"schema_version": SCHEMA_VERSION, "domains": domains}


def _build_source(module, where, src, here, files, provenance=None, notes=None):
    source = source_module(module.DOMAIN)
    built = source.build_instance(src, here)
    # what is said of a valid source and never printed -- a site above 5.1.4's limit, a c_red Figur 9 does not draw -- is a warning of the export (spec 2026-10-21-restes-issue-69, ARCH-RISK-811)
    if notes is not None and hasattr(source, "notes_of"):
        notes.extend(source.notes_of(src, where))
    figures = built.pop("_files", {})
    if files is not None:
        files.update(figures)
    instance = {"engine": "python", "source_file": where, **built}
    if provenance:
        instance["links"] = provenance
    return instance


def _load_targets(src, module):
    """The loads a source's links name, as (domain, instance) -- a «Formule» domain is no load."""
    out = set()
    for _label, entry, _fields in links.entries(src, source_module(module.DOMAIN).LINKABLE):
        for link in links.links_of(entry).values():
            if link.get("origin") != links.FORMULAS:
                out.add((link["domain"], link["instance"]))
    return out


def load_targets(src, domain):
    """The loads a source of `domain` follows, as (domain, instance): what a tab adds a link to before it asks whether a circle closes."""
    return _load_targets(src, next(m for m in DOMAIN_MODULES if m.DOMAIN == domain))


def load_graph(here):
    """{(domain, id): {(domain, instance) it follows}} of the project's load sources on the disk -- what the window refuses a link that would close a chain with (REQ-007)."""
    graph = {}
    for domain, found in _sources(here).items():
        module = next(m for m in DOMAIN_MODULES if m.DOMAIN == domain)
        for _path, src in found:
            graph[(domain, src["id"])] = _load_targets(src, module)
    return graph


def _follow_loads(deferred, domains, here, files, notes):
    """Builds the load sources that follow a variable, each once every load it names is built (see build_calculations); a chain closing on itself stops the export, naming it. True where one was built."""
    if not deferred:
        return False
    pending = {(module.DOMAIN, src["id"]): (module, where, src) for module, where, src in deferred}
    formulas = {}
    while pending:
        ready = [key for key, (module, _where, src) in pending.items() if not (_load_targets(src, module) & set(pending))]
        if not ready:
            graph = {key: _load_targets(src, module) for key, (module, _where, src) in pending.items()}
            chain = next(found for found in (links.find_cycle(graph, key) for key in graph) if found)
            raise validation.ValidationError(
                "loads: " + " → ".join(f"{domain}/{instance}" for domain, instance in chain)
                + " -- these loads follow each other's variables in a circle; take one of the links off in Woodcore")
        # what names a «Formule» domain last, so the domain is computed against every load it may itself read
        plain = [key for key in ready if not any(link.get("origin") == links.FORMULAS for _l, entry, _f in links.entries(pending[key][2], source_module(key[0]).LINKABLE) for link in links.links_of(entry).values())]
        for key in (plain or ready):
            module, where, src = pending.pop(key)
            calculations = {"schema_version": SCHEMA_VERSION, "domains": domains}
            if not plain and here is not None:
                formulas = _formula_values(here, calculations)   # again for each: a load built since may be one a «Formule» domain reads
            values = links.index(calculations, formulas=formulas)
            followed, provenance, said = links.follow(src, source_module(module.DOMAIN).LINKABLE, values, where, links.LOADS)
            notes.extend(said)
            domains[module.DOMAIN]["instances"][src["id"]] = _build_source(module, where, followed, here, files, provenance, notes=notes)
    return True


def _formula_values(here, calculations):
    """The «Formule» domains' variables, computed against the loads built so far ({id: {var: record}})."""
    from domains import formula_domain
    index, _notes = formula_domain.prepare(here)
    return {domain.name: {var.key: {"value": var.value, "unit": var.unit, "symbol": var.symbol} for var in domain.variables}
            for domain in formula_domain.variable_domains(index, here, calculations)}


def write_files(files, data_dir, previous=None):
    """The drawings of the instances, under the names their records give them -- each load's Exports/Figures/ in a project laid out by folders (Permanent-loads/, Variable-loads/Snow/: project.LOAD_FIGURE_KINDS), `data/calculations/` otherwise (engine.Figures) --, LF whatever the platform, and those of a case renamed or deleted removed: only what the last export wrote (`previous`, the calculations.json it wrote, read here when not given -- give it when the new one is written first), never a file of the engineer's. One write per folder: in a project laid out before, the kinds share data/calculations/, which one write empties of what it did not write."""
    import engine
    import project
    data_dir = Path(data_dir)
    if previous is None:
        previous = engine.previous_json(data_dir / "calculations.json")
    places = {}
    for kind in project.LOAD_FIGURE_KINDS:
        place = engine.figures(data_dir, kind)
        places.setdefault(str(place.folder.resolve()), (place, {}))
    for name, content in files.items():
        held = next((own for place, own in places.values() if place.rel(name) is not None), None)
        if held is None:
            raise ValueError(f"{name!r} lies in no folder of the loads' figures")
        held[name] = content
    for place, own in places.values():
        place.write(own, previous)


def export(here):
    """calculations.json rebuilt alone, with the drawings beside it -- what a tab of loads runs when a case is saved, as a member check writes checks.json alone (member_check.export): the sources computed, the whole checked before anything is written. No word of a load workbook here (`workbook_note`): the full export says it."""
    import engine
    from domains import loads_migrate
    # a project whose files still name a value of a snow or wind sheet by its name before v0.120 is not exported a half (CON-002, ARCH-RISK-805)
    refused = loads_migrate.refusal(here)
    if refused:
        raise validation.ValidationError(refused)
    files = {}
    data = build_calculations(here, files)
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)
    previous = engine.previous_json(here.data_dir / "calculations.json")
    engine.write_json(here.data_dir / "calculations.json", data)
    write_files(files, here.data_dir, previous)
    return data
