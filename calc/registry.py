"""Builds data/calculations.json (docs/domain/calculation-domains.md §3.3): every calculation domain, whether its instances are sheets of the project's Belastungsannahmen workbooks or the rows of a norm table.

A *domain* is one kind of calculation (`snow-load`, `dead-load`, `wind-load`); an *instance* is one sheet of it, found by the domain's sheet prefix. That is the whole registry: adding a case to the report means copying a sheet in Excel, not editing anything here. What each domain module differs in is only which side computed the numbers -- snow reads what its sheet calculated, dead-load calculates from what its sheet holds -- and that is recorded per var, in `source`.

One domain is not read from a workbook at all: `live-load` (Nutzlasten) is Tabelle 8 of SIA 261, whose instances are its categories (section 3.3septies). Such a module declares `SHEET_PREFIX = None` and exposes `build_instances()` instead of `read_instances(cells, sheets)`; it is not looked for in any workbook, and never warned about for having no sheet.

The workbooks are found the same way the sheets are, by name: every `.xlsm`/`.xlsx` in the project folder whose name contains `Belastungsannahmen` is a load workbook, so an office's `02_Belastungsannahmen.xlsm` is read without being named here, and a project whose loads are split over two files gets both. Each instance records the workbook it was read from, since a sheet name alone no longer says.

Replaces the old load registry, which keyed a flat `data/loads.json` by load id and could not express two cases of the same calculation.

**Loads entered in Woodcore (issues #35-#37, decision D-04).** Beside its sheets, a domain may have instances computed in Python from sources of the project -- `Woodcore-Datei/loads/<kind>/<id>.json`, one per case, written by the window's tabs. Each such module is named in `SOURCE_MODULES` and gives `source_paths(here)`, `read_source(path)` and `build_instance(src, here)`; its instances join the sheets' under the same domain, each saying where it came from (`engine: "python"`, `source_file`), and an id both a sheet and a source carry is refused naming the two. Their drawings (`figures`) are written beside the export, `data/calculations/` -- `Permanent-loads/Exports/Figures/` in a project laid out by folders, issue #64 (`write_files`).
"""

import importlib

import sys
from pathlib import Path

import engine
import io_excel
import validation
from domains import links  # a load source that follows a variable (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import dead_load, live_load, snow, wind

WORKBOOK_NAME = "Belastungsannahmen"
WORKBOOK_SUFFIXES = (".xlsm", ".xlsx")

# Order here is the order the domains appear in data/calculations.json, and so in docs/typst-reference.xlsx. The sheet domains first, then the norm tables (live_load), which is SIA 261's own chapter order.
DOMAIN_MODULES = (dead_load, snow, wind, live_load)

# The modules computing a domain's instances from the project's own sources, by domain (D-04): imported by name when the export asks, each beside the sheet reader of its domain.
SOURCE_MODULES = {dead_load.DOMAIN: "domains.dead_load_source", snow.DOMAIN: "domains.snow_source", wind.DOMAIN: "domains.wind_source"}
# The export's folder of the drawings an instance carries (an instance's `figures[].file` is relative to data/)
FIGURES_FOLDER = "calculations"
SCHEMA_VERSION = "1.5"
# 1.6 is 1.5 with an instance's `links`, where each field of a load source that follows a variable came from (spec 2026-10-11-variables-liees-champs-et-textes, REQ-012): written only where one does
LINKED_SCHEMA_VERSION = "1.6"
# 1.7 is 1.6 with an instance's drawings named from the Typst root (`/Permanent-loads/Exports/Figures/dead-load-A1.svg`): written where a project laid out by folders draws one, in its domain's Exports/Figures/ (issue #64, D-10)
ROOTED_SCHEMA_VERSION = "1.7"
# 1.8 is 1.7 with no level on a var, a step or a check: lib/line-levels.json says the level each line is printed from, read by Typst when it prints (spec 2026-10-20-indices-et-niveaux, UI-002, D-13). Written by every export from v0.120, links and drawings from the root admitted as in 1.6 and 1.7; 1.4 to 1.7 are still read, a line's own level then read where the table names it not
LEVELS_SCHEMA_VERSION = "1.8"


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


def reads_sheets(module):
    """Whether this domain's instances are workbook sheets. A domain read from a norm table declares no sheet prefix (docs/domain/loads.md §3.3septies)."""
    return module.SHEET_PREFIX is not None


def is_load_workbook(name):
    """Whether a file name is one `open_workbooks` takes for a load workbook -- the same two tests `io_excel.find_workbooks` applies, on a name alone (one data/project.json recorded, which never holds Excel's `~$` lock files)."""
    name = str(name).casefold()
    return WORKBOOK_NAME.casefold() in name and any(name.endswith(s.casefold()) for s in WORKBOOK_SUFFIXES)


def open_workbooks(folder, read_before=(), record=None):
    """A CellReader on every load workbook in `folder`, ordered by file name -- none at all where the folder has none and no export has read one.

    `read_before` names the load workbooks the project's last export read (data/project.json, `record` being that file, named in the message). Finding none stopped the export until v0.89.1, whatever the project: every domain would come out empty, and a workbook renamed out of the pattern looks exactly like a project without loads. It stops now only where that confusion is possible -- a workbook the last export read and that is gone, which is said by name -- and a project that has never had one, a new project, is exported without loads (the engineer's rule, 23.09.2026) -- with a warning until v0.116, one line of information since v0.117 (export_all.run).
    """
    paths = io_excel.find_workbooks(folder, WORKBOOK_NAME, WORKBOOK_SUFFIXES)
    gone = sorted({str(name) for name in read_before if is_load_workbook(name)}, key=str.casefold)
    if not paths and gone:
        where = f"{record}" if record else "data/project.json"
        raise validation.ValidationError(
            f"no load workbook in {folder} -- the last export read "
            f"{', '.join(gone)}, which is no longer there: copy it back, or give "
            f"a renamed copy a name containing '{WORKBOOK_NAME}' "
            f"({' or '.join(WORKBOOK_SUFFIXES)}); a project that no longer has "
            f"loads is exported without them once {where} is deleted"
        )
    return [io_excel.open_cells(path) for path in paths]


def _discover(workbooks, sources=None, notes=None):
    """{module: [(cells, [sheet, ...]), ...]} -- each domain's sheets, workbook by workbook, each in tab order.

    A sheet's name is its instance id, the string the report addresses it by (`show-calc("snow-load", "SL-Dach1")`), so it has to name one sheet across every load workbook at once. Two cases of it are refused outright rather than one of them silently winning: a sheet claimed by two prefixes would land in two domains with two different readers, and a sheet name found in two workbooks would be one id for two calculations. A domain with no sheet in any workbook is only a warning, since a project may genuinely have no facade, or no snow.
    """
    sheet_modules = [module for module in DOMAIN_MODULES if reads_sheets(module)]
    found = {module: [] for module in sheet_modules}
    claimed = {}
    for cells in workbooks:
        for module in sheet_modules:
            sheets = cells.sheet_names(module.SHEET_PREFIX)
            for sheet in sheets:
                if sheet in claimed:
                    other, domain = claimed[sheet]
                    if other is cells:
                        raise validation.ValidationError(
                            f"sheet '{sheet}' in {cells.path.name} matches both "
                            f"the '{domain}' and '{module.DOMAIN}' sheet "
                            f"prefixes -- one sheet is one calculation, so give "
                            f"the domains prefixes that cannot both match"
                        )
                    raise validation.ValidationError(
                        f"sheet '{sheet}' is in both {other.path.name} and "
                        f"{cells.path.name} -- the sheet name is the id the "
                        f"report addresses a case by, so it must be unique "
                        f"across the load workbooks: rename one of the two"
                    )
                claimed[sheet] = (cells, module.DOMAIN)
            if sheets:
                found[module].append((cells, sheets))

    for module, per_workbook in found.items():
        # With no workbook at all there is nothing to have looked in -- the empty calculations a new project starts with (export_all.seed) -- and a warning per domain would name none. A domain whose cases are entered in Woodcore is not empty for having no sheet (D-04).
        if not per_workbook and workbooks and not (sources or {}).get(module.DOMAIN):
            names = ", ".join(cells.path.name for cells in workbooks)
            # a warning of the export's list, said in the window's language (C4, v0.120: printed to stderr until then, where no one read it)
            if notes is not None:
                notes.append(engine.Note(
                    "registry_no_sheet",
                    f"no sheet named '{module.SHEET_PREFIX}...' in {names} -- domain '{module.DOMAIN}' will be empty and "
                    f"show-calc(\"{module.DOMAIN}\", ...) will find nothing",
                    prefix=module.SHEET_PREFIX, workbooks=names, domain=module.DOMAIN))
    return found


def build_calculations(workbooks, here=None, files=None, notes=None):
    """`workbooks` is a list of io_excel CellReaders, one per load workbook (`open_workbooks()`); `here` the project whose own load sources join them (None: the sheets alone, as `export_all.seed` builds an empty export); `files`, a dict, is given the drawings the instances carry, {path under data/: SVG text} (`write_files`); `notes`, a list, the warnings of the load sources that follow a variable (issue #42).

    A load source whose fields follow a variable (`links`) is built once every load it names is: after the sheets and the sources that follow nothing, in as many rounds as the chain is long, the «Formule» domains computed against the loads built so far and those naming one built last (`_follow_loads`). A chain that comes back to where it began stops the export, naming it (REQ-007)."""
    sources = _sources(here)
    deferred = []
    notes = notes if notes is not None else []
    sheets_by_module = _discover(workbooks, sources, notes)
    domains = {}
    for module in DOMAIN_MODULES:
        if reads_sheets(module):
            instances = {}
            # One call per workbook, never across them: a workbook's sheets are read against that workbook's own lookup tables (the dead load's material library, the snow sheets' Dropdowns), and a workbook without a single sheet of this domain is not asked for tables it may not have.
            for cells, sheets in sheets_by_module[module]:
                for sheet, instance in module.read_instances(cells, sheets, notes).items():
                    instances[sheet] = {"workbook": cells.path.name, **instance}
            # The cases entered in Woodcore, after the sheets and in file-name order: computed here, each saying where it came from -- an id a sheet already carries is refused rather than one of the two silently winning (D-04)
            for path, src in sources.get(module.DOMAIN, ()):
                where = "%s/%s" % (source_module(module.DOMAIN).FOLDER, path.name)
                if src["id"] in instances:
                    raise validation.ValidationError(
                        f"{where}: the id '{src['id']}' is also the sheet '{src['id']}' of "
                        f"{instances[src['id']]['workbook']} -- one id is one case of '{module.DOMAIN}': "
                        f"rename the source in Woodcore or the sheet in Excel")
                if links.is_linked(src, source_module(module.DOMAIN).LINKABLE):
                    deferred.append((module, where, src))
                    instances[src["id"]] = None      # its place in file-name order, filled once what it follows is built
                    continue
                instances[src["id"]] = _build_source(module, where, src, here, files, notes=notes)
        else:
            # A norm table: its instances are the table's own rows, and they name no workbook and no sheet, since there is none to name (docs/domain/loads.md §3.3septies).
            instances = module.build_instances()
        domains[module.DOMAIN] = {
            "label": module.LABEL,
            # permanent or variable: declared by the module, like its engine, so the classification a load combination will read lives where the load is calculated
            "action": module.ACTION,
            "engine": module.ENGINE,
            "sheet_prefix": module.SHEET_PREFIX or "",
            "instances": instances,
        }
    linked = _follow_loads(deferred, domains, here, files, notes)
    rooted = any(figure["file"].startswith("/") for domain in domains.values() for instance in domain["instances"].values() for figure in instance.get("figures") or ())
    return {"schema_version": LEVELS_SCHEMA_VERSION, "domains": domains}   # 1.8 holds what 1.6 (links) and 1.7 (rooted drawings) hold


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
    """calculations.json rebuilt alone, with the drawings beside it -- what a tab of loads runs when a case is saved, as a member check writes checks.json alone (member_check.export): the load workbooks read, the sources computed, the whole checked before anything is written."""
    import engine
    from domains import loads_migrate
    # a project whose files still name a value of a snow or wind sheet by its name before v0.120 is not exported a half (CON-002, ARCH-RISK-805)
    refused = loads_migrate.refusal(here)
    if refused:
        raise validation.ValidationError(refused)
    workbooks = open_workbooks(here.root)
    files = {}
    data = build_calculations(workbooks, here, files)
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)
    previous = engine.previous_json(here.data_dir / "calculations.json")
    engine.write_json(here.data_dir / "calculations.json", data)
    write_files(files, here.data_dir, previous)
    return data
