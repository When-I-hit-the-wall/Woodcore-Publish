"""What the lines of a domain of the «Domaines» tab read from one another, and what a variable linked from elsewhere is (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-010, REQ-019, ARCH-012).

**The linked hovers** (REQ-019, UI-018): a line lit, what it is computed from in blue, what is computed from it in green -- read off what `formula_domain.compute` evaluated (`Result.uses`, the keys each line names), never parsed again here nor in the window. A key a line names is the one the closest line above it defines, as Typst reads it.

**A linked variable** (REQ-010): `#var("gk_ak_gew", domain: ("dead-load", "EL+AL-Dach_ohne_Wasser"))` shows the symbol and the label of its source -- (g_k + a_k)_"gew", read off `data/calculations.json`, or off the other domain of the tab it names -- and its origin, the kind and the case or the domain's id, which the window says in its own words. `formula_domain.resolve_import` (its value, and the guard against a circle of domains) is not touched (CON-004): this is a reader beside it, of the same data.

No Qt.
"""

import json

from domains import formula_domain as fd


def definer(domain, key, before):
    """The index of the line closest above `before` that defines `key`, or None."""
    for j in range(min(before, len(domain.commands)) - 1, -1, -1):
        if domain.commands[j].defines == key:
            return j
    return None


def dependencies(domain, results):
    """{index: {"uses": [indices], "used": [indices]}} for every command of `domain`: the lines it is computed from, the lines computed from it -- in the file's order, a text having none."""
    out = {i: {"uses": [], "used": []} for i, c in enumerate(domain.commands) if not c.is_text}
    for j, (c, r) in enumerate(zip(domain.commands, results)):
        if c.is_text:
            continue
        for key in r.uses:
            d = definer(domain, key, j)
            if d is not None and d != j and d not in out[j]["uses"]:
                out[j]["uses"].append(d)
                out[d]["used"].append(j)
    for entry in out.values():
        entry["uses"].sort()
        entry["used"].sort()
    return out


def _calculations(here, calculations=None):
    if calculations is not None:
        return calculations
    try:
        return json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, AttributeError):
        return {}


def linked_info(here, command, calculations=None, domains=()):
    """{symbol, label, origin} of a variable linked from elsewhere (`#var(key, domain: …)`), or None for any other command: the export's variable (`origin` ("export", calculation, instance)) or another domain's of the tab (`origin` ("domain", id)), its symbol and label as its source writes them -- "" where the source does not give them."""
    found = fd.reference(command)
    if found is None or not (command.source and command.source[0] == "domain"):
        return None
    calc, instance, name = found
    if instance is not None:
        try:
            var = _calculations(here, calculations)["domains"][calc]["instances"][instance]["vars"][name]
        except (KeyError, TypeError):
            var = {}
        return {"symbol": str(var.get("symbol") or ""), "label": str(var.get("label") or ""), "origin": ("export", calc, instance)}
    other = next((d for d in domains if d.id == calc), None)
    symbol = label = ""
    if other is not None:
        c = next((c for c in reversed(other.commands) if c.defines == name), None)
        if c is not None:
            symbol, label = c.symbol, str(c.options.get("label") or "")
    return {"symbol": symbol, "label": label, "origin": ("domain", calc)}


def describer(here, domains=(), calculations=None):
    """The `describe` `formula_domain.compute` takes: `linked_info` with the export read once."""
    data = _calculations(here, calculations)
    return lambda command: linked_info(here, command, data, domains)


def linkable(here, domain=None, export=None):
    """The variables a domain of the tab may link (REQ-013, UI-014), as the «Variables» tab reads them (variable_sources.read_export, #42, #114): [{key, calc, instance, symbol, label, value, unit, source}] -- each case of the export (`source` ("domain", (calc, instance))), then each other domain of the tab (`source` ("domain", id), `instance` None). `domain` is the one linking: its own variables are not offered."""
    import variable_sources
    export = export if export is not None else variable_sources.read_export(here)
    cases, others = [], []
    for d in export.domains:
        if d.address:
            for var in d.variables:
                cases.append({"key": var.key, "calc": d.address[0], "instance": d.address[1], "symbol": var.symbol or var.key, "label": var.label,
                              "value": var.value, "unit": var.unit, "source": ("domain", (d.address[0], d.address[1]))})
        elif d.origin == fd.ORIGIN and (domain is None or d.name != domain.id):
            for var in d.variables:
                others.append({"key": var.key, "calc": d.name, "instance": None, "symbol": var.symbol or var.key, "label": var.label,
                               "value": var.value, "unit": var.unit, "source": ("domain", d.name), "domain_label": d.label})
    return cases + others


def link_command(candidate):
    """The `#var(key, domain: …)` a candidate is linked by (REQ-013): the export's case as a pair, another domain by its id. Its key is the variable's own -- `domain:` reads the variable of that name --, which is why a variable whose key the domain holds already is not offered («déjà dans ce domaine»)."""
    return fd.Command("var", key=candidate["key"], source=candidate["source"])
