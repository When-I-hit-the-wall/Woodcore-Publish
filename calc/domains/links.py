"""A value of a form taken from a variable of the export: the one place a link is checked, looked up, converted and reported (spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, ARCH-001).

A field a tab lets the engineer type -- a member check's N, a static model's point x, a load's magnitude -- may instead **follow a variable** of the export: a load of data/calculations.json, a connection's, a connector's, a script's, or a domain of the «Formule» tab. The number stays in the source where it always was, and is the **last value known** (D-06, D-17); beside it the entry's `links` names, by the field's key, the variable it follows:

    "N": {"value": 12.5, "unit": "kN"},
    "links": {"N": {"domain": "snow-load", "instance": "SL", "var": "q_k", "factor": 1.5}}

`domain` and `instance` are the pair a call names an export's calculation by (`var-of("snow-load", "SL", "q_k")`, the «Variables» tab's `address`); a domain of the «Formule» tab carries `"origin": "formulas"` and its id as `instance`. The value is `factor × variable + offset` (1 and 0 by default, D-04), converted into the field's unit when the variable's is another of the same dimension -- 12 500 N gives 12.5 in a field in kN (REQ-004). Which units a field accepts is `calc/units.py`'s algebra, the one `lib/formula.typ` computes with, never a list written here (CON-003).

A link whose variable is gone is **never a stop**: the field keeps its last value and a warning says so (D-06, `CLAUDE.md` «a missing input warns»). That last value is written by Woodcore's window when it saves, never by the export, which writes no source (D-14).

Nothing here reads a file: the caller hands over the values (`index`), built from the export in memory by export_all or from data/ by the window (`variable_sources.known_values`), so this module imports none of the domains it serves and none of them can import it in a circle (ARCH-RISK-010). No Qt.
"""

import math

import engine
import units

# The key of an entry under which its links are kept, by the key of the field each one fills
LINKS = "links"

# A link's keys: the variable it names, then what it may add
LINK_KEYS = ("domain", "instance", "var")
LINK_EXTRAS = ("factor", "offset", "origin")

# The origin of a domain of the «Formule» tab (formula_domain.ORIGIN): it has no (calculation, instance) a call names it by, so a link names it by its id in `instance`
FORMULAS = "formulas"
# Where an index keeps the «Formule» domains, beside the export's calculations -- a key no calculation id can be (they are words and hyphens)
FORMULAS_KEY = "@formulas"

# The sources each consumer may name (ARCH-005, D-11), by the word an index files them under: the loads are computed first at the export, so a load may only name another load or a «Formule» domain; every later consumer may name anything of the export. `None` is «any».
LOADS = "loads"
JOINTS = "joints"
ANY = "any"
NOT_LOADS = ("connection", "connector", "script")
# A connector and a polar moment are built before each other's variables exist and give variables of their own: they follow a load, a script or a «Formule» domain, never a joint (ARCH-005)
NOT_JOINTS = ("connection", "connector")


def links_of(entry):
    """The links an entry carries, {field: link} -- empty where it carries none."""
    found = entry.get(LINKS) if isinstance(entry, dict) else None
    return found if isinstance(found, dict) else {}


def link_text(link):
    """A link as one string, for a warning and the record's provenance: `snow-load/SL/q_k`, `formulas:geo/L`."""
    if link.get("origin") == FORMULAS:
        return f"{FORMULAS}:{link['instance']}/{link['var']}"
    return f"{link['domain']}/{link['instance']}/{link['var']}"


def make(domain, instance, var, factor=1.0, offset=0.0, origin=None):
    """A link as it is saved: factor and offset only where they are not 1 and 0, so a plain link stays three keys."""
    out = {"domain": domain, "instance": instance, "var": var}
    if origin == FORMULAS:
        out["origin"] = FORMULAS
    if float(factor) != 1.0:
        out["factor"] = _clean(factor)
    if float(offset) != 0.0:
        out["offset"] = _clean(offset)
    return out


def from_choice(origin, domain_name, var_key, address):
    """The link the «Variables» tab's choice names: an export's domain by its address, a «Formule» domain by its id. None for a document's registry, which no link may name (D-02)."""
    if address is not None:
        return make(address[0], address[1], var_key)
    if origin == FORMULAS:
        return make(FORMULAS, domain_name, var_key, origin=FORMULAS)
    return None


def _clean(value):
    value = round(float(value), 9) + 0.0
    return int(value) if value.is_integer() else value


# --- what a file may say -----------------------------------------------------------

def check_link(link, fail, what):
    """One link's shape, `fail(message)` called on the first breach naming `what` -- a defect of a file Woodcore wrote, which stops the export (`CLAUDE.md`)."""
    if not isinstance(link, dict):
        fail(f"{what} must be an object naming a variable of the export, got {link!r}")
    unknown = sorted(set(link) - set(LINK_KEYS) - set(LINK_EXTRAS))
    if unknown:
        fail(f"{what} has {', '.join(unknown)} -- a link has {', '.join(LINK_KEYS + LINK_EXTRAS)}")
    for key in LINK_KEYS:
        if not isinstance(link.get(key), str) or not link[key].strip():
            fail(f"{what}'s {key} must name the variable it follows, got {link.get(key)!r}")
    for key in ("factor", "offset"):
        if key in link and (isinstance(link[key], bool) or not isinstance(link[key], (int, float)) or not math.isfinite(link[key])):
            fail(f"{what}'s {key} must be a number, got {link[key]!r}")
    if "origin" in link and link["origin"] != FORMULAS:
        fail(f"{what}'s origin is {link['origin']!r} -- {FORMULAS!r} for a domain of the «Formule» tab, or absent for the export")


def check_links(entry, fields, fail, what):
    """An entry's `links`: an object whose every key is one of `fields` (the keys of that entry a link may fill) and whose every value is a link."""
    if LINKS not in entry:
        return
    found = entry[LINKS]
    if not isinstance(found, dict):
        fail(f"{what}'s {LINKS} must be an object, got {found!r}")
    for key, link in found.items():
        if key not in fields:
            fail(f"{what}'s {LINKS} names {key!r}, which is no field a variable may fill -- {', '.join(fields) or 'none'}")
        check_link(link, fail, f"{what}'s link of {key}")


# --- units -------------------------------------------------------------------------

def compatible(unit, field_unit):
    """Whether a variable in `unit` may fill a field in `field_unit` (REQ-003, D-15): the same dimension by calc/units.py. A field without a unit takes only a variable without one, never one in rad, which lib/units.json holds dimensionless; and the reverse."""
    a, b = (unit or "").strip(), (field_unit or "").strip()
    if (a == "") != (b == ""):
        return False
    pa, pb = units.parse_unit(a), units.parse_unit(b)
    if pa is None or pb is None:
        return a == b
    return units.dims_equal(pa[1], pb[1])


def convert(value, unit, field_unit):
    """`value` in `unit` written in `field_unit`: 12500 N → 12.5 kN. Assumes `compatible`."""
    a, b = (unit or "").strip(), (field_unit or "").strip()
    if a == b:
        return float(value)
    pa, pb = units.parse_unit(a), units.parse_unit(b)
    return float(value) * pa[0] / pb[0]


# --- the values a link may name ------------------------------------------------------

def index(calculations=None, records=(), formulas=None):
    """The values the export holds, {domain: {instance: {var: record}}} -- the shape `statics.values_of` has always given, so a load's reference and a field's link read the same thing:

    * `calculations`, data/calculations.json's record, under its calculation ids;
    * `records`, [(word, {id: record})] -- the connections, the connectors, the scripts, each under the word `find-calculation` reads it by (`connection`, `connector`, `script`);
    * `formulas`, {domain id: {var: record}} -- the «Formule» tab's domains computed now, under FORMULAS_KEY.
    """
    out = {}
    for domain, d in ((calculations or {}).get("domains") or {}).items():
        out[domain] = {instance: record.get("vars") or {} for instance, record in (d.get("instances") or {}).items()
                       if isinstance(record, dict)}   # a load not built yet holds its place with None (registry.build_calculations)
    for word, found in records:
        out.setdefault(word, {}).update({rid: (rec or {}).get("vars") or {} for rid, rec in (found or {}).items() if isinstance(rec, dict)})
    if formulas:
        out[FORMULAS_KEY] = {fid: dict(found) for fid, found in formulas.items()}
    return out


def lookup(link, values):
    """The record of the variable a link names, or None."""
    if link.get("origin") == FORMULAS:
        return (values or {}).get(FORMULAS_KEY, {}).get(link["instance"], {}).get(link["var"])
    return (values or {}).get(link["domain"], {}).get(link["instance"], {}).get(link["var"])


def apply(link, value):
    """`factor × value + offset`, the one piece of arithmetic a link does (D-04)."""
    return float(link.get("factor", 1.0)) * float(value) + float(link.get("offset", 0.0))


def allowed(link, consumer=ANY):
    """Whether `consumer` may name the variable `link` names (ARCH-005, D-11): a load only another load or a «Formule» domain; a connector or a polar moment no joint."""
    refused = {LOADS: NOT_LOADS, JOINTS: NOT_JOINTS}.get(consumer, ())
    return link.get("origin") == FORMULAS or link.get("domain") not in refused


def resolve(link, values, field_unit=None, last=None, consumer=ANY):
    """What a link gives now: {value, unit, base_value, base_unit, from, missing, stale}.

    `value` is in `field_unit` (the variable's own unit where None), after factor and offset. Where the variable cannot be read -- gone, not a number, of another dimension, or of a source `consumer` may not name -- `value` is `last` (the number the source holds) and `stale` is True, `missing` an engine.Note saying why: a warning, never a stop (D-06).
    """
    out = {"value": last, "unit": field_unit or "", "base_value": None, "base_unit": "", "from": link_text(link), "missing": "", "stale": False}

    def miss(code, text, **args):
        out["missing"] = engine.Note(code, text, ref=out["from"], **args)
        out["stale"] = True
        return out

    if not allowed(link, consumer):
        return miss("link_not_allowed", f"{out['from']} may not be named here -- a load follows only another load or a domain of the «Formule» tab, a connector or a polar moment no connector and no polar moment")
    record = lookup(link, values)
    if record is None:
        return miss("link_missing", f"no such variable: {out['from']}")
    raw = record.get("value")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return miss("link_not_a_number", f"{out['from']} is {raw!r}, which is not a number", value=raw)
    unit = record.get("unit") or ""
    if field_unit is not None and not compatible(unit, field_unit):
        return miss("link_unit", f"{out['from']} is in {unit or 'no unit'}, which cannot fill a value in {field_unit or 'no unit'}",
                    unit=unit or "–", field_unit=field_unit or "–")
    out["base_value"], out["base_unit"] = float(raw), unit
    value = apply(link, raw)
    out["value"] = convert(value, unit, field_unit) if field_unit is not None else value
    if field_unit is None:
        out["unit"] = unit
    return out


# --- the fields of an entry ------------------------------------------------------------

def get_path(entry, key):
    """The value at a field's key -- `N`, `section.b` -- or None."""
    node = entry
    for part in key.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def set_path(entry, key, value):
    parts = key.split(".")
    node = entry
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def field_value(entry, key):
    """(number, unit) of a field -- a bare number, or a {value, unit} block -- or (None, None)."""
    found = get_path(entry, key)
    if isinstance(found, dict):
        return found.get("value"), found.get("unit")
    if isinstance(found, bool) or not isinstance(found, (int, float)):
        return None, None
    return found, None


def apply_links(entry, values, fields, where, consumer=ANY):
    """Every link of `entry` resolved, its field set to what the variable gives now: (entry copy, provenance, warnings).

    `fields` is {key: unit} -- the unit a field is written in, or None where the field's own {value, unit} block says it. The source is never changed: a copy is returned, where a field whose variable cannot be read keeps the number the source holds (its last value, D-06) and earns a warning naming `where`, the field and the variable. `provenance` is {key: {variable, factor, offset, base_value, base_unit, stale}}, what an export record carries beside the value it printed (REQ-012).
    """
    found = links_of(entry)
    if not found:
        return entry, {}, []
    out = _copy(entry)
    provenance, notes = {}, []
    for key, link in found.items():
        if key not in fields:
            continue
        parent = get_path(entry, key.rsplit(".", 1)[0]) if "." in key else entry
        if not isinstance(parent, dict) or get_path(entry, key) is None:
            continue   # a field the entry does not hold -- a section it follows from elsewhere, a spacing a single fastener has none of: nothing to fill (the window takes such a link off as it saves)
        number, own_unit = field_value(entry, key)
        unit = fields[key] if fields[key] is not None else own_unit
        resolved = resolve(link, values, unit if unit is not None else "", number, consumer)
        if resolved["stale"]:
            notes.append(engine.Note("link_stale", f"{where}: {key} keeps its last value {number} -- {resolved['missing']}",
                                     where=where, field=key, detail=resolved["missing"]))
        elif isinstance(get_path(entry, key), dict):
            set_path(out, key + ".value", _clean(resolved["value"]))
        else:
            set_path(out, key, _clean(resolved["value"]))
        provenance[key] = {
            "variable": dict(link),
            "factor": float(link.get("factor", 1.0)),
            "offset": float(link.get("offset", 0.0)),
            "base_value": resolved["base_value"],
            "base_unit": resolved["base_unit"],
            "stale": resolved["stale"],
        }
    return out, provenance, notes


def _copy(value):
    if isinstance(value, dict):
        return {k: _copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_copy(v) for v in value]
    return value


def refresh(entry, values, fields, consumer=ANY):
    """Writes into `entry` itself, for each field that follows a variable, the value the variable gives now -- what Woodcore's window does before it saves, so the number the source holds is the last value known (D-14). A field whose variable cannot be read is left as it is. Never called by the export, which writes no source."""
    resolved, _provenance, _notes = apply_links(entry, values, fields, "", consumer)
    for key in links_of(entry):
        if key in fields:
            set_path(entry, key, _copy(get_path(resolved, key)))
    return entry


# --- a source of several entries -------------------------------------------------------------
#
# `spec` is {collection: {key: unit}}: the fields a variable may fill, by collection -- SELF for the source's own fields, a key of the source holding a list of entries for each of them (`members`, `points`, `layers`). What every domain of a source with links does, written once (ARCH-001).

SELF = "self"


def entries(source, spec):
    """(label, entry, fields) for the source itself and each entry of each collection of `spec` -- an entry named by its id, else by its place (`members[0]`)."""
    if spec.get(SELF):
        yield "self", source, spec[SELF]
    for collection, fields in spec.items():
        if collection == SELF or not fields:
            continue
        for i, entry in enumerate(source.get(collection) or ()):
            if isinstance(entry, dict):
                yield (entry.get("id") or f"{collection}[{i}]"), entry, fields


def is_linked(source, spec):
    """Whether a source follows a variable anywhere `spec` names."""
    return any(links_of(entry) for _label, entry, _fields in entries(source, spec))


def check_all(source, spec, fail, what="the source", consumer=ANY):
    """`check_links` on the source and on every entry of `spec`'s collections -- and, for a `consumer` that may not name every source, each link's source: a load naming a script, a joint naming a joint is a defect of a file Woodcore wrote, which stops the export (ARCH-005, REQ-007)."""
    for label, entry, fields in entries(source, spec):
        name = what if label == "self" else label
        check_links(entry, fields, fail, name)
        for key, link in links_of(entry).items():
            if not allowed(link, consumer):
                fail(f"{name}'s link of {key} names {link_text(link)}, which it may not follow -- a load follows only another load or a domain of the «Formule» tab, a connector or a polar moment no connector and no polar moment")


def follow(source, spec, values, where, consumer=ANY):
    """The source with every linked field set to what its variable gives now: (copy, provenance, warnings) -- `apply_links` on the source and every entry, the source itself never changed. `provenance` is [{entry, field, variable, factor, offset, base_value, base_unit, stale}], what an export record carries (REQ-012)."""
    out = _copy(source)
    provenance, notes = [], []
    for label, entry, fields in list(entries(out, spec)):
        if not links_of(entry):
            continue
        resolved, found, said = apply_links(entry, values, fields, where if label == "self" else f"{where}, {label}", consumer)
        entry.clear()
        entry.update(resolved)
        notes.extend(said)
        provenance.extend({"entry": label, "field": key, **origin} for key, origin in found.items())
    return out, provenance, notes


def refresh_all(source, spec, values, consumer=ANY):
    """`refresh` on the source and on every entry: what the window does before it saves (D-14)."""
    for _label, entry, fields in list(entries(source, spec)):
        if links_of(entry):
            refresh(entry, values, fields, consumer)
    return source


def drop_unheld(source, spec):
    """Takes off every link whose field the entry does not hold -- a spacing a single fastener has none of, a centre not placed by hand --, so a source never names a variable for nothing. What the window does as it drafts."""
    for _label, entry, fields in list(entries(source, spec)):
        found = {key: link for key, link in links_of(entry).items() if key in fields and get_path(entry, key) is not None}
        if found:
            entry[LINKS] = found
        else:
            entry.pop(LINKS, None)
    return source


def find_cycle(graph, start):
    """A chain of nodes from `start` back to itself through `graph` ({node: iterable of nodes}), or None: what refuses a load following, through others, a variable of its own (REQ-007)."""
    path, on_path, done = [], set(), set()

    def visit(node):
        if node in on_path:
            return path[path.index(node):] + [node]
        if node in done:
            return None
        on_path.add(node)
        path.append(node)
        for target in graph.get(node, ()):
            found = visit(target)
            if found:
                return found
        path.pop()
        on_path.discard(node)
        done.add(node)
        return None

    return visit(start)


def find_cycles(graph):
    """Every circle of `graph` ({node: iterable of nodes}), once each: [[a, b, …, a]] -- one per strongly connected component that holds more than one node or a node naming itself, walked from its smallest node, so the same graph always says the same chains (spec 2026-10-21-graphe-dependances, ARCH-002, ARCH-RISK-1107). `find_cycle` asks for one, from a node."""
    index, low, stack, on_stack, components = {}, {}, [], set(), []
    counter = [0]
    nodes = sorted(set(graph) | {t for targets in graph.values() for t in targets}, key=repr)

    def connect(start):
        # Tarjan's algorithm, iterative: a deep chain of loads must not reach Python's recursion limit
        work = [(start, iter(sorted(graph.get(start, ()), key=repr)))]
        index[start] = low[start] = counter[0]
        counter[0] += 1
        stack.append(start)
        on_stack.add(start)
        while work:
            node, targets = work[-1]
            advanced = False
            for target in targets:
                if target not in index:
                    index[target] = low[target] = counter[0]
                    counter[0] += 1
                    stack.append(target)
                    on_stack.add(target)
                    work.append((target, iter(sorted(graph.get(target, ()), key=repr))))
                    advanced = True
                    break
                if target in on_stack:
                    low[node] = min(low[node], index[target])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    top = stack.pop()
                    on_stack.discard(top)
                    component.append(top)
                    if top == node:
                        break
                components.append(component)

    for node in nodes:
        if node not in index:
            connect(node)
    out = []
    for component in components:
        members = set(component)
        if len(component) == 1 and component[0] not in set(graph.get(component[0], ())):
            continue
        out.append(_shortest_cycle(graph, members, min(component, key=repr)))
    return sorted(out, key=repr)


def _shortest_cycle(graph, members, start):
    """The shortest chain from `start` back to itself inside `members`, its nodes' successors taken in order -- breadth first, so a component of thousands of nodes needs no recursion."""
    from collections import deque
    parent, queue = {}, deque()
    for target in sorted(graph.get(start, ()), key=repr):
        if target in members and target not in parent:
            parent[target] = start
            queue.append(target)
    while queue:
        node = queue.popleft()
        if node == start:
            break
        for target in sorted(graph.get(node, ()), key=repr):
            if target in members and target not in parent:
                parent[target] = node
                queue.append(target)
    chain, node = [start], parent[start]
    while node != start:
        chain.append(node)
        node = parent[node]
    chain.append(start)
    return chain[::-1]


def references(source, path=""):
    """Every variable a source names, wherever it stands -- a field's link, a static model's magnitude, a figure's text's `vars` --, as [(field, {domain, instance, var, origin?})]: the one walk the graph of dependencies reads a source's variables by (spec 2026-10-21-graphe-dependances, ARCH-RISK-1103; loads_migrate walks the same shape to rename)."""
    out = []
    if isinstance(source, dict):
        if all(isinstance(source.get(key), str) for key in LINK_KEYS):
            out.append((path or "/", {key: source[key] for key in LINK_KEYS + ("origin",) if key in source}))
        for key, value in source.items():
            out += references(value, "%s/%s" % (path, key))
    elif isinstance(source, list):
        for i, value in enumerate(source):
            out += references(value, "%s/%d" % (path, i))
    return out
