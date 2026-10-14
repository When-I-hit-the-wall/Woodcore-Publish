"""The `rfem` domain: one instance per **structure** of an RFEM model, carrying what the solver found for its bars.

The engineer's own words: «Chaque Structure est un domaine … Dans typst, le user peut appeler un domaine rfem (i.e. une structure rfem). Depuis là, il peut appeler les efforts et déformations maximums par barre.»

**It is a domain of the shape §3.3 defines, so nothing in the report had to be taught it.** `#val`, `#find`, `#show-calc`, `#var(domain: …)` and the summary tables all work on it because it carries the same `{vars, steps, checks, results}` record a load instance carries. It is read from a file of its own, `data/rfem.json`, and addressed `("rfem", "<structure>")` — exactly the arrangement `connector` and `connection` already have (§3.3quinquies), and for the same reason: it is exported on its own, and it belongs to no position.

⚠️ **`engine` is `rfem`, a fourth kind beside `excel`, `python` and `norm`.** Every var's `source` says so with the export it came from and the combination that produced it -- `rfem:260929-01_29509-Model.xlsx!SP1!CO3` -- so a number in the report can be traced to the sheet, the design situation and the load combination without opening anything.

**A bar is one RFEM member** (the engineer's own choice of three), identified by the position its comment names and an index: `T001_1`, `T001_2`, … in increasing member number within the structure.

⚠️ **The index is always written, even where the position occurs once.** `T001` alone would be shorter today and would become `T001_1` the day a second member of that position joins the structure — and every call naming it would break, silently, since `T001` would then name nothing. A call that is right today stays right.

⚠️ **A member whose comment names no position is still carried**, as `bar_<number>`: its forces are real, and dropping them would lose them without a word. What it cannot do is be addressed by a position, which is the engineer's own scheme and not a defect.

⚠️ **The design situation is part of the variable's name**, `SP1_T001_1_M_y_max`. The engineer asked that one always state which situation or combination is being looked at; with one instance per structure, a bar therefore holds four different `M_y` maxima — one per situation — and only the name can tell them apart. The printed symbol stays the engineer's, `M_(y,max)`.

⚠️ **The values are RFEM's envelopes, not an envelope computed here** (`envelopes.py`): RFEM's own result-combination tables carry the extreme and the combination that reached it, and this module arranges them. Nothing is compared, added or reduced.
"""

import engine

DOMAIN = "rfem"
LABEL = "RFEM"

# The contract `data/rfem.json` follows (§3.0), beside the others in `schemas/`.
SCHEMA_VERSION = "1.0"

# A fourth engine beside `excel`, `python` and `norm` (§3.3): the numbers are a solver's, read from its export.
ENGINE = "rfem"

# The member-forces quantities, in the order a report reads them, with the symbol each is printed as.
FORCE_SYMBOLS = {
    "N": "N",
    "Vy": "V_y", "Vz": "V_z",
    "MT": "M_T", "My": "M_y", "Mz": "M_z",
}

# The deformation quantities, likewise. `|u|` is the resultant displacement, which is what a deflection check
# reads; the rotations are carried because RFEM exports them and a connection check may want one.
DEFORMATION_SYMBOLS = {
    "|u|": "u", "ux": "u_x", "uy": "u_y", "uz": "u_z",
    "φx": "phi_x", "φy": "phi_y", "φz": "phi_z",
}

# The support-reaction quantities.
REACTION_SYMBOLS = {
    "Px": "P_x", "Py": "P_y", "Pz": "P_z",
    "Mx": "M_x", "My": "M_y", "Mz": "M_z",
}

# What a var's name says after the bar: the quantity with its dots and bars taken out, since a name is a key
# a formula may hold (`lib/formula.typ` -- letters, digits and underscores, never a hyphen).
NAME_OF = {
    "N": "N", "Vy": "V_y", "Vz": "V_z", "MT": "M_T", "My": "M_y", "Mz": "M_z",
    "|u|": "u", "ux": "u_x", "uy": "u_y", "uz": "u_z",
    "φx": "phi_x", "φy": "phi_y", "φz": "phi_z",
    "Px": "P_x", "Py": "P_y", "Pz": "P_z", "Mx": "M_x",
}

# Which kinds an extreme comes in, and the word each is labelled with.
KINDS = ("max", "min")

# The level every var of this domain carries: it is a number read from a solver, printed where the report asks
# for it by name rather than walked through. `show-calc` on a structure is a listing, and a listing is level 2.
LEVEL = 2


def bar_id(position, index):
    """`T001_1` — the position a member's comment names, and its index among that position's members here."""
    return f"{position}_{index}" if position else f"bar_{index}"


def bars_of(structure, model):
    """Every member of `structure` as a bar: its id, the position it realises, and what RFEM says it is.

    In increasing member number, which is the order the index follows: a bar's name must not move because a
    drawing was read in another order.
    """
    by_number = {member.no: member for member in model.members}
    seen, bars = {}, []
    for number in sorted(structure.numbers("member")):
        member = by_number.get(number)
        if member is None:
            continue
        position = member.position or ""
        seen[position] = seen.get(position, 0) + 1
        index = seen[position]
        section = model.section_of(member)
        bars.append({
            "id": bar_id(position, index) if position else f"bar_{number}",
            "position": position,
            "index": index,
            "member": number,
            "length": member.length,
            "section": None if section is None else section.name,
            "material": None if section is None else section.material,
        })
    return bars


def _round(value, digits=6):
    """A number at RFEM's own precision. The export rounds to its «Unités et décimales» already; this keeps a
    float's tail out of a file that is read on every compile."""
    if value is None:
        return None
    return float(f"%.{digits}g" % value)


def _var(name, symbol, extreme, label, source, bar, situation):
    """One extreme as a var of the §3.1 shape.

    ⚠️ **The combination, the abscissa and what the value is about are fields and not prose.** A label
    saying «massgebend CO3, bei x = 2.115 m» reads well and cannot be printed on its own, cannot be searched
    and cannot be compared -- and repeated over 7696 vars it was two thirds of a 2.4 MB file that Typst reads
    on every compile. The display commands and `#find` read the fields; the label says what the value is.
    """
    return name, {
        "value": _round(extreme.value),
        "unit": extreme.unit or "",
        "symbol": symbol,
        "label": label,
        "level": LEVEL,
        "source": source,
        "norm": "",
        "norm_ref": "",
        "loading": extreme.loading,
        "at": _round(extreme.x, 4),
        "situation": situation,
        "bar": bar,
        "quantity": extreme.quantity,
        "kind": extreme.kind,
    }


def _label(quantity, kind, bar):
    """What the value **is**, in the glossary's own language -- and nothing that a field already says.

    ⚠️ Composed here rather than templated in `calc/i18n/strings.json`: §4bis matches a template on the
    literal text around its holes, and this one's holes are a quantity and a project's own bar name, which
    would make it match far too much.
    """
    word = "Grösster" if kind == "max" else "Kleinster"
    return f"{word} Wert von {quantity}, Stab {bar}"


def _extremes(envelopes, on, object, prefix, bar, symbols, source_of, out, situations):
    """Every extreme of one object into `out`, named `<situation>_<bar>_<quantity>_<kind>`."""
    for situation in sorted(envelopes):
        kinds = envelopes[situation]
        envelope = kinds.get(on)
        if envelope is None:
            continue
        situations.setdefault(situation, kinds.get("situation-label", situation))
        for quantity, symbol in symbols.items():
            slot = envelope.of(object, quantity)
            for kind in KINDS:
                extreme = slot.get(kind)
                if extreme is None:
                    continue
                name = f"{situation}_{prefix}_{NAME_OF.get(quantity, quantity)}_{kind}"
                printed = f"{symbol}_(\"{kind}\")"
                out.append(_var(
                    name, printed, extreme,
                    _label(quantity, kind, bar),
                    source_of(situation, extreme.loading),
                    prefix, situation,
                ))


def record(structure, model, envelopes, export, situation_labels=None):
    """One structure as an instance of the `rfem` domain: its bars, and every extreme RFEM found on them.

    `envelopes` is `{situation: {"forces": Envelope, "deformations": Envelope, "reactions": Envelope}}` as
    `envelopes.read_workbook_envelopes` gives it.
    """
    bars = bars_of(structure, model)
    labels = dict(situation_labels or {})
    situations, collected = {}, []

    def source_of(situation, loading):
        return f"rfem:{export}!{situation}!{loading}"

    for bar in bars:
        _extremes(envelopes, "forces", bar["member"], bar["id"], bar["id"],
                  FORCE_SYMBOLS, source_of, collected, situations)
        _extremes(envelopes, "deformations", bar["member"], bar["id"], bar["id"],
                  DEFORMATION_SYMBOLS, source_of, collected, situations)

    # The support reactions of the nodes this structure holds, addressed by the node: a support is one object
    # applied to a set of nodes (`structure_detection`), so the node is what a reaction belongs to.
    nodes = []
    for node in sorted(structure.nodes):
        before = len(collected)
        _extremes(envelopes, "reactions", node, f"N{node}", f"Knoten {node}",
                  REACTION_SYMBOLS, source_of, collected, situations)
        if len(collected) > before:
            nodes.append(node)

    # ⚠️ **A quantity that is identically zero on a bar is left out, and said out loud.** This model is a
    # plane frame, so V_y, M_T, M_z, u_y, phi_x and phi_z are exactly zero on every one of its 62 members:
    # 4955 of 7696 vars, two thirds of the file, every one of them a number no report would print. They are
    # dropped **per bar and across every situation** -- never in one situation and not another, which would
    # make a name exist in SP1 and not in SP2 -- and `zero` names them, so «this structure carries no M_z» and
    # «this export was read without M_z» stay two different statements.
    zero, by_object = {}, {}
    for name, value in collected:
        by_object.setdefault((value["bar"], value["quantity"]), []).append((name, value))
    vars = {}
    for (bar, quantity), items in by_object.items():
        if all(item[1]["value"] == 0 for item in items):
            zero.setdefault(bar, []).append(quantity)
            continue
        for name, value in items:
            vars[name] = value
    for bar in zero:
        zero[bar].sort()

    return {
        "label": structure.statics_name or structure.name or str(structure.key),
        "description": structure.statics_descr or "",
        "export": export,
        "engine": ENGINE,
        "bars": bars,
        "support_nodes": nodes,
        "zero": {bar: quantities for bar, quantities in sorted(zero.items())},
        "situations": {key: labels.get(key, key) for key in sorted(situations)},
        "vars": vars,
        "steps": [],
        "checks": [],
        "results": [],
        "calculated": bool(vars),
        "reason": "" if vars else (
            "this export carries no result combination -- calculate the model in RFEM and export the tables "
            "again, with the design situations ticked"
        ),
    }


def loadings_of(model):
    """The load cases and combinations one model holds, as the report prints a combination's formula.

    A combination carries its **terms** -- `[(1.35, "CC1"), (1.5, "CC2")]` -- and a case its own name, so the
    report can set either `1.35 · CC1 + 1.50 · CC2` or `1.35 · (EG + AL) + 1.50 · Schnee`. Both are RFEM's own;
    nothing is recomposed here.
    """
    cases = {
        case.id: {"name": case.name or "", "category": case.category or "", "action": case.action or ""}
        for case in model.cases
    }
    combinations = {}
    for combination in model.combinations:
        combinations[combination.id] = {
            "name": combination.name or "",
            "situation": combination.situation or "",
            "terms": [[float(factor), str(case)] for factor, case in combination.terms],
        }
    return cases, combinations


def build(models, situation_labels=None):
    """`{structure id: record}` for every named structure of every RFEM export the project holds.

    `models` is `[(export name, model, structures, envelopes), …]`. A structure nobody named is left out, for
    the reason `import_controller` leaves it out of the static models too: its id is what a report addresses it
    by, and `member-24` is a placeholder rather than a name.
    """
    out, problems = {}, []
    cases, combinations, from_export = {}, {}, {}
    for export, model, structures, envelopes in models:
        its_cases, its_combinations = loadings_of(model)
        for source, into in ((its_cases, cases), (its_combinations, combinations)):
            for key, value in source.items():
                held = into.get(key)
                if held is not None and held != value:
                    # ⚠️ Two exports of two buildings may both call a combination «CO1» and mean two different
                    # sums. The first is kept and the second named, rather than one silently standing for both.
                    problems.append(engine.Note(
                        "rfem_loading_disagrees",
                        f"«{export}» gives «{key}» a different definition from «{from_export.get(key, '?')}» -- "
                        f"the first is kept; a report naming «{key}» would otherwise print one of two sums at random",
                        value=key, where=export,
                    ))
                    continue
                into[key] = value
                from_export[key] = export
        for structure in structures.structures:
            name = structure.name
            if not name:
                continue
            if name in out:
                problems.append(engine.Note(
                    "rfem_domain_id_taken",
                    f"Two structures are called «{name}» -- «{export}» and «{out[name]['export']}»; "
                    f"the second is left out of the «rfem» domain, so give one of them another @model name",
                    value=name, where=export,
                ))
                continue
            out[name] = record(structure, model, envelopes, export, situation_labels)
    return {"structures": out, "cases": cases, "combinations": combinations}, problems


def document(built):
    """`data/rfem.json` as it is written: the contract, the structures, and the loadings a combination is printed from."""
    return {
        "schema_version": SCHEMA_VERSION,
        "structures": dict(sorted(built.get("structures", {}).items())),
        "cases": dict(sorted(built.get("cases", {}).items())),
        "combinations": dict(sorted(built.get("combinations", {}).items())),
    }

