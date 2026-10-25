"""The graph of dependencies of a project: which of its objects reads which, built at every export, written to data/dependencies.json, and what a change touches said as a warning (spec docs/requirements/completed/2026-10-21-graphe-dependances.md, issue #71; docs/domain/dependencies.md).

A Woodcore project is a network -- a member check follows a position, a load follows another load, a static model draws a load, a script reads a value of the export, a domain of «Formules» reads a calculation, a connector follows a schema and the positions of its members, and the report prints all of it --, and each object knows what it reads, none who reads it. This module writes the network down. **A node** is one object, `"<kind>:<id>"` (`KINDS`): a position, a case of a load (`load:snow-load/SL`), a script, a domain of «Formules», a timber check, a steel check and its profile, a connector, a polar moment, a schema, a static model, a plan and the document it is drawn on, a fire plan, an excerpt of an annex, and a section of one of the three documents. **An edge** `{from, to, field}` says that `from` reads `to` through `field` -- with the variable (`domain`, `instance`, `var`) where it is one, `previous: true` where it is read in the last export rather than in this one (a script reading a connector), `line` where a section names it. An argument a section computes (`for id in ids("position")`) gives the wildcard `position:*`, never one edge per position (D-07).

**Nothing is computed again** (ARCH-RISK-1102): the references are read off the records the export has just built (`references()` of each domain), the sources (`links.references`, every variable a source names wherever it stands), the domains of «Formules» (`formula_domain.reference`), what each script read as it ran (`script.prepare(reads=)`), and the calls of the documents' sections (`COMMAND_REFERENCES`, `typst_calls`). A domain a member check is unfolded into is the check's own file, never a node: its `domain: ("check", id)` would otherwise make every unfolded check a circle (ARCH-RISK-1101). A reference whose object is not there is no edge -- the domain that holds it already says it is gone.

**What changed** (D-04, ARCH-RISK-1106). Each node carries a `digest`, the fingerprint of its record (`engine.digest`) without the keys that only present it (`PRESENTATION`); a section, a profile and a document carry none. Between the last export's graph and this one, a node whose digest moved has changed; the warnings name only the **roots** -- a changed node none of whose own inputs changed -- and, for each, what depends on it downstream, by kind, at most `SHOWN` ids then «(+N)». The file holds no «changed»: it is a function of the sources alone, the same bytes from one export to the next when nothing moved. **A circle** between objects of different kinds is said too (`links.find_cycles`); a circle of loads stays the registry's refusal, one of «Formules» domains the tab's own.

Qt-free; imported by export_all and by the «Dépendances» tab, which only reads `data/dependencies.json` (`read`).
"""

import json
import re
from pathlib import Path

import engine
import validation
import typst_calls
from domains import links

EXPORT_FILE = "dependencies.json"
EXPORT_SCHEMA = "dependencies"
EXPORT_SCHEMA_VERSION = "1.0"

# The kinds of node, in the order the tab lists them: the word of a node's key (`check:ZT-01`)
KINDS = ("position", "load", "script", "formula", "check", "steel", "profile", "connector", "connection", "schema",
         "statics", "plan", "document", "fire", "extract", "section")

# The keys of a record that only present it -- its drawing, its style, its names and notes --, left out of its digest: a change of them touches nothing downstream (ARCH-RISK-1106). Everything else counts, so a field added to a record is seen without anyone listing it here.
PRESENTATION = frozenset(("figures", "figure", "overlay", "legend", "style", "label", "name", "group", "warnings", "description", "notes", "svg", "size", "files"))

# How many ids of one kind a warning names before «(+N)»
SHOWN = 8

# The words a link's or a call's (domain, instance) is said in for the objects that are no calculation domain
_WORD_KINDS = {"connector": "connector", "connection": "connection", "script": "script", "check": "check", "steel": "steel"}
# The words `ids(kind)` takes, and the node kind each lists
IDS_KINDS = {"position": "position", "connection": "connection", "connector": "connector", "script": "script", "plan": "plan",
             "fire-plan": "fire", "static-model": "statics", "schema": "schema", "extract": "extract", "annex": "extract",
             "check-member": "check", "check-steel": "steel", "domain": "load"}

# What each command of lib/ that names an object of the project names, and where (ARCH-RISK-1104): ("pair", i) -- a calculation's (domain, instance), the i-th and the next positional; ("domain", name) -- `domain:` a pair, or the id of a «Formules» domain; ("id", kind, i or name) -- one object of `kind`; ("ids", kind, i) -- an array of them; ("kinds", i) -- `ids(kind)`, every object of a kind; ("all", kind) -- the command prints every object of `kind`; ("file", 0) -- `domain-file(kind, id)`, the object whose file it names. tests/test_dependency_graph.py holds this table against the public commands of lib/: each is here or in NO_REFERENCE.
COMMAND_REFERENCES = {
    "var": ("domain", "domain"), "find": ("domain", "domain"),
    "plans-of": ("id", "position", 0),
    "ids": ("kinds", 0),
    "show-annexes": ("all", "extract"),
    # the commands of the spec 2026-10-21-commandes-typst-refonte: one position on a line (REQ-015), the five drawings as images (REQ-013, REQ-014)
    "position": ("id", "position", 0),
    "image-positions-plan": ("id", "plan", 0), "image-fire-plan": ("id", "fire", 0), "image-static-model": ("id", "statics", 0),
    "image-schema": ("id", "schema", 0), "image-extract": ("id", "extract", 0), "image-polar-moment": ("id", "connection", 0),
    # an export sheet's section and legend (Q-015)
    "image-section": ("id", "plan", 0), "image-legend": ("all", "plan"),
    # a domain's file, included (spec 2026-10-21-commandes-typst-refonte, REQ-017): `#include domain-file(kind, id)`, the object of `kind` it prints
    "domain-file": ("file", 0),
}
# The node kind of each kind of domain file `domain-file(kind, id)` names (lib/formula.typ; calc/domains/list_files.py) -- a load's by its calculation domain, read from the graph's
FILE_KINDS = {"check": "check", "steel": "steel", "connector": "connector", "connection": "connection", "script": "script"}
# The public commands that name no object of the project: they format, compute what they are given, or lay out a page
NO_REFERENCE = frozenset((
    "calc-defaults", "caption-rules", "cite-norm", "from-level", "distance", "doc-tables", "domain", "eq", "fmt-decimals", "fmt-number", "fmt-value", "get",
    "image-titleblock", "journal-entries", "project-info", "render-formula", "render-prose", "render-symbol", "report-lang", "set-report-language",
    "show-bibliography", "show-norm-list", "sync", "t", "t-label", "t-of", "t-pattern", "t-str", "tl", "tl-of", "tl-str", "unit", "var-table",
    "verify", "woodcore-document",
))

_INCLUDE = re.compile(r'#include\s+"([^"\n]+)"')


def key(kind, ident):
    return f"{kind}:{ident}"


def kind_of(node):
    return node.split(":", 1)[0]


def _digest(record):
    return engine.digest({k: v for k, v in record.items() if k not in PRESENTATION}) if isinstance(record, dict) else engine.digest(record)


def target(domain, instance, calculation_domains, origin=None):
    """The node a variable's (domain, instance) names: a «Formules» domain (`origin: formulas`), a connector, a polar moment, a script, a check, or a case of a calculation domain (`load:<domain>/<instance>`); None where it names none of them. `instance` None is every object of that kind (the wildcard)."""
    ident = "*" if instance is None else instance
    if origin == links.FORMULAS:
        return key("formula", ident)
    if domain in _WORD_KINDS:
        return key(_WORD_KINDS[domain], ident)
    if domain in calculation_domains:
        return key("load", "*" if instance is None else f"{domain}/{instance}")
    return None


class _Graph:
    def __init__(self, calculation_domains):
        self.nodes = {}        # key -> {digest?, file?, enabled?, unresolved?}
        self.edges = []
        self.domains = calculation_domains

    def node(self, node, digest=None, file=None, **more):
        entry = self.nodes.setdefault(node, {})
        if digest is not None:
            entry["digest"] = digest
        if file is not None:
            entry["file"] = file
        entry.update({k: v for k, v in more.items() if v is not None})
        return entry

    def edge(self, source, to, field, **more):
        if to is None:
            return
        self.edges.append({"from": source, "to": to, "field": field, **{k: v for k, v in more.items() if v not in (None, False)}})


def _records(graph, kind, records, module, here, folder):
    """Every record of a domain as a node, its references as edges, and the variables its source names (`links.references`)."""
    for ident, record in (records or {}).items():
        node = key(kind, ident)
        source = Path(folder) / f"{ident}.json" if folder is not None else None
        graph.node(node, _digest(record), here.rel(source) if source is not None and source.is_file() else None)
        for to_kind, to_id, field in module.references(record):
            graph.edge(node, key(to_kind, to_id), field)
        if source is not None:
            _variables(graph, node, source)


def _variables(graph, node, path):
    """The variables a source names -- its links, a static model's magnitudes, a text's `vars` -- as edges; a source that cannot be read gives none (its own domain says so)."""
    try:
        source = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for field, link in links.references(source):
        graph.edge(node, target(link["domain"], link["instance"], graph.domains, link.get("origin")), field, variable=f"{link['domain']}/{link['instance']}/{link['var']}")


def _sections(graph, here, formula_ids, unfolded):
    """The sections of the three documents as nodes, and the objects their calls name as edges (D-06): each file a document's structure names (`structure_nodes.section_files`, no heading read), read once; `enabled` whether the document prints it."""
    import structure_nodes
    seen = set()
    root = Path(here.root)
    for mode in here.modes:
        folder = here.document_dir(mode)
        for file, printed in structure_nodes.section_files(here, mode):
            path = folder / file
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            node = key("section", f"{mode}/{file}")
            graph.node(node, file=path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path), enabled=bool(printed))
            _section_calls(graph, node, path.read_text(encoding="utf-8", errors="replace"), formula_ids, unfolded, here)


def _section_calls(graph, node, text, formula_ids, unfolded, here):
    unresolved = 0
    masked = typst_calls.mask_comments(text)
    for name, _start, args, line in typst_calls.calls(text, COMMAND_REFERENCES, masked):
        rule = COMMAND_REFERENCES[name]
        positional, named = typst_calls.arguments(args)

        def at(where):
            if isinstance(where, int):
                return positional[where] if len(positional) > where else None
            return named.get(where)
        how = rule[0]
        if how == "pair":
            domain = typst_calls.literal(at(rule[1]) or "")
            instance = typst_calls.literal(at(rule[1] + 1) or "")
            found = target(domain, instance, graph.domains) if domain else None
            if found is None:
                unresolved += 1
            graph.edge(node, found, name, line=line)
        elif how == "domain":
            written = named.get("domain")
            if written is None:
                continue
            pair = typst_calls.pair(written)
            if pair is not None:
                found = target(pair[0], pair[1], graph.domains)
                if pair[0] == "check" and pair[1] in unfolded:
                    found = key("check", pair[1])
            else:
                ident = typst_calls.literal(written)
                found = key("formula", ident) if ident in formula_ids else None
            if found is None:
                unresolved += 1
            graph.edge(node, found, name, line=line)
        elif how == "id":
            written = at(rule[2])
            if written is None:
                continue
            ident = typst_calls.literal(written)
            if rule[1] == "load" and ident is not None:
                ident = f"live-load/{ident}"
            graph.edge(node, key(rule[1], "*" if ident is None else ident), name, line=line)
        elif how == "ids":
            written = at(rule[2]) or ""
            names = [typst_calls.literal(written[a:b]) for a, b in typst_calls.split(written.strip()[1:-1])] if written.strip().startswith("(") else [typst_calls.literal(written)]
            for ident in names:
                graph.edge(node, key(rule[1], "*" if ident is None else ident), name, line=line)
        elif how == "kinds":
            word = typst_calls.literal(at(rule[1]) or "")
            kind = IDS_KINDS.get(word)
            if kind is None and word in graph.domains:
                graph.edge(node, key("load", "*"), name, line=line)
            elif kind is not None:
                graph.edge(node, key(kind, "*"), name, line=line)
            else:
                unresolved += 1
        elif how == "all":
            graph.edge(node, key(rule[1], "*"), name, line=line)
        elif how == "file":
            kind, ident = typst_calls.literal(at(0) or ""), typst_calls.literal(at(1) or "")
            if kind in FILE_KINDS:
                found = key(FILE_KINDS[kind], ident if ident is not None else "*")
            elif kind in graph.domains:
                found = key("load", f"{kind}/{ident}" if ident is not None else "*")
            else:
                found = None     # a journal, a list of the positions: no object of the graph
            graph.edge(node, found, name, line=line)
    for found in _INCLUDE.finditer(masked):
        stem = Path(found.group(1)).stem
        line = text.count("\n", 0, found.start()) + 1
        if stem in unfolded:
            graph.edge(node, key("check", stem), "include", line=line)
        elif stem in formula_ids:
            graph.edge(node, key("formula", stem), "include", line=line)
    if unresolved:
        graph.nodes[node]["unresolved"] = unresolved


def build(here, calculations, positions, scripts, reads, formulas, checks, steel, connectors, connections, schemas, plans, fire_plans, models, annexes):
    """The graph of the project as the export has just built it: {schema_version, nodes, edges} -- `nodes` {key: {digest?, file?, enabled?, unresolved?}} sorted, `edges` [{from, to, field, variable?, previous?, line?}] sorted, every target an object the project has (a wildcard `kind:*` aside). Nothing is computed again (module doc)."""
    from domains import (connection as connection_domain, connector as connector_domain, fire as fire_domain, formula_domain,
                         member_check, plan as plan_domain, schema as schema_domain, statics as statics_domain, steel_check)
    domains = calculations.get("domains", {})
    graph = _Graph(set(domains))
    for ident, record in positions.items():
        graph.node(key("position", ident), _digest(record))
    for domain, block in domains.items():
        for instance, record in (block.get("instances") or {}).items():
            node = key("load", f"{domain}/{instance}")
            graph.node(node, _digest(record), record.get("source_file"))
            # a load entered in Woodcore names the variables it follows in its own source
            for field, link in links.references({"links": record.get("links")} if record.get("links") else {}):
                graph.edge(node, target(link["domain"], link["instance"], graph.domains, link.get("origin")), field, variable=f"{link['domain']}/{link['instance']}/{link['var']}")
    for ident, record in scripts.items():
        node = key("script", ident)
        graph.node(node, _digest(record.get("vars", {})), f"{record.get('id', ident)}.py")
        for domain, instance, name in (reads or {}).get(ident, ()):
            graph.edge(node, target(domain, instance, graph.domains), "value", variable=f"{domain}/{instance}/{name}",
                       previous=domain in ("connector", "connection"))
    unfolded = {cid for cid, record in checks.get("checks", {}).items() if member_check.is_unfolded(record)}
    formula_ids = set()
    for domain in formulas:
        if domain.gen or domain.id in unfolded:
            continue   # a check's own file, not a domain of the engineer's (ARCH-RISK-1101)
        formula_ids.add(domain.id)
    for domain in formulas:
        if domain.id not in formula_ids:
            continue
        node = key("formula", domain.id)
        graph.node(node, engine.digest(domain.text or ""), here.rel(domain.path) if domain.path else None)
        for command in domain.commands:
            found = formula_domain.reference(command)
            if found is None:
                continue
            domain_word, instance, name = found
            if instance is None and domain_word in formula_ids:
                graph.edge(node, key("formula", domain_word), "var", variable=f"{domain_word}/{name}")
            else:
                graph.edge(node, target(domain_word, instance, graph.domains), "var", variable=f"{domain_word}/{instance}/{name}")
    _records(graph, "check", checks.get("checks"), member_check, here, here.checks_dir)
    _records(graph, "steel", steel.get("checks"), steel_check, here, here.steel_dir)
    _records(graph, "connector", connectors.get("connectors"), connector_domain, here, here.connectors_dir)
    _records(graph, "connection", connections.get("connections"), connection_domain, here, here.connections_dir)
    _records(graph, "schema", schemas.get("schemas"), schema_domain, here, here.details_dir)
    _records(graph, "plan", plans.get("plans"), plan_domain, here, here.plans_dir)
    _records(graph, "fire", fire_plans.get("plans"), fire_domain, here, here.fire_dir)
    for ident, record in (models.get("models") or {}).items():
        node = key("statics", ident)
        source = here.statics_dir / f"{ident}.json"
        graph.node(node, _digest(record), here.rel(source) if source.is_file() else None)
        _variables(graph, node, source)   # a load's magnitude is in the source alone: the record keeps the text it prints (ARCH-RISK-1102)
    for ident, record in (annexes.get("excerpts") or {}).items():
        graph.node(key("extract", ident), _digest(record))
    for domain, module in (("dead-load", "dead_load_source"), ("snow-load", "snow_source"), ("wind-load", "wind_source")):
        import importlib
        source_module = importlib.import_module("domains." + module)
        for path in source_module.source_paths(here):
            node = key("load", f"{domain}/{path.stem}")
            if node in graph.nodes:
                graph.nodes[node]["file"] = here.rel(path)
                _variables(graph, node, path)
    _sections(graph, here, formula_ids, unfolded)
    return _finish(graph)


def _finish(graph):
    """The graph as it is written: the targets an object of the project names and the targets of the kinds only a reference creates (a profile, a document) kept, the rest dropped; every edge once; sorted."""
    for edge in graph.edges:
        if kind_of(edge["to"]) in ("profile", "document") and edge["to"] not in graph.nodes:
            graph.node(edge["to"])
    known = set(graph.nodes)
    seen, edges = set(), []
    for edge in graph.edges:
        to = edge["to"]
        if to not in known and not to.endswith(":*"):
            continue   # its object is gone: the domain that names it says so (D-04)
        if to.endswith(":*") and kind_of(to) not in KINDS:
            continue
        mark = json.dumps(edge, sort_keys=True)
        if mark in seen:
            continue
        seen.add(mark)
        edges.append(edge)
    edges.sort(key=lambda e: (e["from"], e["to"], e["field"], e.get("line") or 0, e.get("variable") or ""))
    return {"schema_version": EXPORT_SCHEMA_VERSION, "nodes": {k: graph.nodes[k] for k in sorted(graph.nodes)}, "edges": edges}


# --- reading the graph, and what changed ----------------------------------------------------------

def read(path):
    """The graph a file holds, checked -- or None where there is none, it cannot be read, or it is of another version: nothing to compare (CON-002). What the tab and the next export read."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        validation.validate_structure(data, EXPORT_SCHEMA)
    except (OSError, ValueError, validation.ValidationError):
        return None
    return data if data.get("schema_version") == EXPORT_SCHEMA_VERSION else None


def upstream(graph):
    """{node: [what it reads]} -- a wildcard `kind:*` read as every node of that kind."""
    by_kind = {}
    for node in graph["nodes"]:
        by_kind.setdefault(kind_of(node), []).append(node)
    out = {node: [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        targets = by_kind.get(kind_of(edge["to"]), []) if edge["to"].endswith(":*") else [edge["to"]]
        out.setdefault(edge["from"], []).extend(t for t in targets if t != edge["from"])
    return out


def reachable(down, node):
    """Every node that depends on `node`, transitively, through `down` (`downstream`'s map), `node` itself left out -- in the order of KINDS, then by key: what the «Dépendances» tab lists under «Utilisé par» and the command palette summarises (issue #83)."""
    reached, stack = [], list(down.get(node, ()))
    while stack:
        found = stack.pop(0)
        if found in reached or found == node:
            continue
        reached.append(found)
        stack.extend(down.get(found, ()))
    return sorted(reached, key=lambda n: (KINDS.index(kind_of(n)) if kind_of(n) in KINDS else len(KINDS), n))


def downstream(graph):
    """{node: [what reads it]}, the reverse of `upstream`."""
    out = {node: [] for node in graph["nodes"]}
    for node, targets in upstream(graph).items():
        for target_node in targets:
            out.setdefault(target_node, []).append(node)
    return out


def changes(previous, current):
    """[(root, {kind: [ids downstream]})]: every node whose digest moved since `previous` and none of whose own inputs did, with what depends on it, transitively, by kind -- an empty list where there is no previous graph (CON-002)."""
    if not previous:
        return []
    before = {node: entry.get("digest") for node, entry in previous.get("nodes", {}).items()}
    changed = {node for node, entry in current["nodes"].items()
               if entry.get("digest") is not None and node in before and before[node] is not None and before[node] != entry["digest"]}
    up, down = upstream(current), downstream(current)
    out = []
    for root in sorted(changed):
        if any(source in changed for source in up.get(root, ())):
            continue
        reached, stack = set(), list(down.get(root, ()))
        while stack:
            node = stack.pop()
            if node in reached or node == root:
                continue
            reached.add(node)
            stack.extend(down.get(node, ()))
        by_kind = {}
        for node in sorted(reached):
            by_kind.setdefault(kind_of(node), []).append(node.split(":", 1)[1])
        out.append((root, by_kind))
    return out


def cycles(graph):
    """Every circle of the graph through objects of at least two kinds -- [[node, …, node]] -- a wildcard, a section and a circle of one kind left to their own (ARCH-002)."""
    plain = {}
    for edge in graph["edges"]:
        if edge["to"].endswith(":*") or kind_of(edge["from"]) == "section":
            continue
        plain.setdefault(edge["from"], []).append(edge["to"])
    return [chain for chain in links.find_cycles(plain) if len({kind_of(node) for node in chain}) > 1]


def _kind_word(kind):
    return engine.Note("dep_kind_" + kind, kind)


def notes(previous, current):
    """The export's warnings (D-04): one per changed root and kind downstream -- «position:P12 changed: check ZT-01, BI-03 depend on it» --, at most SHOWN ids then «(+N)», and one per circle through objects of different kinds."""
    out = []
    for root, by_kind in changes(previous, current):
        if not by_kind:
            continue
        for kind in KINDS:
            ids = by_kind.get(kind)
            if not ids:
                continue
            shown = ", ".join(ids[:SHOWN]) + (" (+%d)" % (len(ids) - SHOWN) if len(ids) > SHOWN else "")
            out.append(engine.Note("dep_changed", f"{root} changed since the last export -- {kind}: {shown} depend on it",
                                   node=root, kind=_kind_word(kind), ids=shown))
    for chain in cycles(current):
        text = " → ".join(chain)
        out.append(engine.Note("dep_cycle", f"{text} -- these objects read each other in a circle; an export settles it only by chance", chain=text))
    return out


def write(data, data_dir):
    """data/dependencies.json, checked against its contract first."""
    validation.validate_structure(data, EXPORT_SCHEMA)
    engine.write_json(Path(data_dir) / EXPORT_FILE, data)


def empty():
    """The graph of a project that holds nothing yet: what a new project is seeded with (export_all.seed)."""
    return {"schema_version": EXPORT_SCHEMA_VERSION, "nodes": {}, "edges": []}


def newer_sources(here, graph):
    """The objects' sources changed since the graph was written -- what the tab says the graph is older than --, as their paths from the project's folder; [] where there is no graph file."""
    written = Path(here.data_dir) / EXPORT_FILE
    try:
        stamp = written.stat().st_mtime
    except OSError:
        return []
    out = []
    for entry in graph.get("nodes", {}).values():
        file = entry.get("file")
        if not file:
            continue
        try:
            if (Path(here.root) / file).stat().st_mtime > stamp + 1:
                out.append(file)
        except OSError:
            continue
    return sorted(out)
