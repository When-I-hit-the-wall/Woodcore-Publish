"""What an RFEM import's metadata means once the model is around it: whether a `@position` may be where it is written, whether what it names exists, and whether the two agree about the section.

`metadata_parser` reads a comment's **syntax** and refuses nothing; this reads its **meaning**, which needs the model, the structures and the project's own `Positionen.xlsx`. The line between the two is the one that module's docstring draws, and it is why they are apart: a typo in a key is caught with no model open, and «position T001 is on a support» cannot be.

**Nothing refuses.** Every finding is an `engine.Note` — the rule the plans, the static models and the connectors already follow (docs/architecture/data-contracts.md §3.6): an import that stopped on one mistyped position would stop the import of every other structure, and the window could not then show the engineer what to fix. What a caller cannot do without, it asks for; `problems(...)` is what it reads.

**What is checked, and why each is here:**

- ⚠️ **A position may be written on a member or on a surface, and nowhere else** — the engineer's own rule: «une position ne peut être attribué qu'à un élément barre ou panneau. Une charge ou un appui ne peux pas recevoir de position». A node, a support, a hinge or a load carrying `@position` is reported by name; the value is kept, so the window can show it while it is being moved.
- **A position that `Positionen.xlsx` does not hold** is reported with the row to add, which is what the plan tab already offers for a number drawn on a plan and missing from the sheet (§3.3sexies). It is a warning and not a stop for exactly that reason: stopping would stop the positions' own export, and then nothing could add the row.
- **A position on elements of two different structures.** Two elements of one position are legal and ordinary — the position plan has allowed identical elements to share a number since v0.44 — but *across two static systems* it is nearly always a number reused by accident, and it is the one thing a reader cannot see from either structure alone.
- ⚠️ **The section RFEM gives and the section the position gives, compared.** The one check here that catches an error of substance rather than of naming: RFEM's `Sections` table says 500/200 for member 24 and `Positionen.xlsx` says «500/200» for T001, and where those two disagree one of them is out of date. Compared to the millimetre after both are read into `b`/`h`, so a difference of rounding is not a finding.
- **A `@load` that names no instance of `data/calculations.json`**, listed with the domains and instances that do exist — the refusal `show-calc` already makes, made at import time instead of at compile time.
- **A `@be` outside what a structure can plausibly have.** The parser reads «1500» as 1500 m because catching that needs a notion of plausibility, which is here: a width beyond `MAX_WIDTH` is almost always metres typed where millimetres were meant.
- **A structure nobody named**, once, with the comment to write — the one thing the model cannot tell, and what `@model` exists for.
"""

import engine
from rfem_import.metadata_parser import KEYS, MEMBER_OR_SURFACE_ONLY, REFERENCES, SIGIL
from rfem_import.structure_detection import ELEMENT_KINDS

# A width beyond this is read as a mistake rather than as a structure: the widest influence width this kind of building has is a few metres, and «1500» typed for 1500 mm is the way it goes wrong (`metadata_parser` reads a bare number as metres).
MAX_WIDTH = 100.0

# How far apart two readings of one section may be and still be the same section: a tenth of a millimetre, which is below anything either side states.
SECTION_TOLERANCE = 0.1


def _note(code, text, **args):
    return engine.Note(code, text, **args)


def position_places(items):
    """Every `@position` written where it may not be: a node, a support, a hinge, a load.

    ⚠️ The engineer's rule, and the reason it is a rule: a position is a *thing built*, so it belongs to the object that realises it. A load carrying one would say that a load is a position, and the import would then have two answers to «what is T001».
    """
    found = []
    for item in items:
        for key in MEMBER_OR_SURFACE_ONLY:
            if key in item.meta and item.kind not in ELEMENT_KINDS:
                found.append(_note(
                    "rfem_position_place",
                    f"{item.where} carries {SIGIL}{key} «{item.meta[key]}», which only a member or a surface may -- "
                    f"write it on the member or the panel that realises the position",
                    where=item.where, key=key, value=item.meta[key], kind=item.kind,
                ))
    return found


def positions_resolve(model, known):
    """Every `@position` the project's own `Positionen.xlsx` does not hold, with the number to add.

    `known` is the position ids the sheet holds -- `data/positions-index.json`'s `positions`, or any iterable of them. Where it is empty nothing is checked: a project whose positions have never been exported must not be told that every one of them is unknown.
    """
    known = {str(name) for name in known or ()}
    if not known:
        return []
    found = []
    for item in _elements(model):
        name = item.meta.get("position")
        if name and name not in known:
            found.append(_note(
                "rfem_position_unknown",
                f"{item.where} names position «{name}», which the project's positions do not hold -- "
                f"add it in Woodcore's «Positions» tab, or correct the comment in RFEM",
                where=item.where, value=name,
            ))
    return found


def positions_across_structures(structures):
    """A position whose elements are in more than one structure -- ordinary within one, and nearly always an accident across two."""
    where = {}
    for structure in structures:
        for name, carriers in structure.positions.items():
            where.setdefault(name, []).append((structure, carriers))
    found = []
    for name, places in sorted(where.items()):
        if len(places) < 2:
            continue
        told = "; ".join(
            f"«{structure.name or structure.key}» ({', '.join(item.where for item in carriers)})"
            for structure, carriers in places)
        found.append(_note(
            "rfem_position_shared",
            f"Position «{name}» is on elements of {len(places)} structures -- {told}; "
            f"two elements of one position are ordinary inside one structure and rarely meant across two",
            value=name, count=len(places), places=told,
        ))
    return found


def sections_agree(model, sections_of):
    """Every element whose section RFEM states and whose position states another.

    `sections_of` answers, for a position id, that position's `b` and `h` in millimetres -- `{"T001": (500.0, 200.0)}`, or a callable of the id giving the pair or None. The check is the one that catches an error of substance: a member RFEM carries at 500/200 and a position the workbook carries at 400/200 is one of the two out of date, and the report would print the workbook's while the forces are the other's.
    """
    look = sections_of.get if hasattr(sections_of, "get") else sections_of
    found = []
    for item in _elements(model):
        name = item.meta.get("position")
        if not name:
            continue
        stated = look(name)
        if not stated:
            continue
        section = _section_of(model, item)
        if section is None or section.b is None or section.h is None:
            continue
        theirs = tuple(float(value) for value in stated[:2])
        ours = (float(section.b), float(section.h))
        if _apart(ours, theirs) and _apart(ours, tuple(reversed(theirs))):
            found.append(_note(
                "rfem_section_disagrees",
                f"{item.where} realises position «{name}»: RFEM gives {_mm(ours)} "
                f"(section «{section.name}») where Woodcore's position gives {_mm(theirs)} -- one of the two is out of date",
                where=item.where, value=name, rfem=_mm(ours), woodcore=_mm(theirs),
            ))
    return found


def loads_resolve(model, instances):
    """Every `@load` that names no instance of `data/calculations.json`.

    `instances` is `{domain: [instance, …]}` as `calculations.json` holds them. A load is named «snow-load/SL-Dach1», the pair `show-calc` is addressed by.
    """
    instances = {str(domain): [str(name) for name in names] for domain, names in (instances or {}).items()}
    if not instances:
        return []
    known = {f"{domain}/{name}" for domain, names in instances.items() for name in names}
    found = []
    for item in _with_key(model, "load"):
        named = item.meta["load"]
        if named in known:
            continue
        found.append(_note(
            "rfem_load_unknown",
            f"{item.where} names load «{named}», which data/calculations.json does not hold -- "
            f"it holds {', '.join(sorted(known)[:8])}…",
            where=item.where, value=named,
        ))
    return found


def widths_plausible(model):
    """Every `@be` too wide to be an influence width -- «1500» typed for 1500 mm, which the parser reads as 1500 m because deciding that needs this notion and not its own."""
    found = []
    for item in _with_key(model, "be"):
        width = item.meta["be"]
        if width is None or 0 < width <= MAX_WIDTH:
            continue
        found.append(_note(
            "rfem_width_implausible",
            f"{item.where}: {SIGIL}be is {width:g} m, which is not an influence width -- "
            f"write the unit, as «1.5m» or «1500mm»",
            where=item.where, value=width,
        ))
    return found


def structures_named(structures):
    """Every structure nobody named, with the comment to write. One note per structure, not per member."""
    return [
        _note(
            "rfem_structure_unnamed",
            f"The structure of {_some(structure)} has no name -- write «{SIGIL}model \"<name>\"» in the comment "
            f"of one of its members in RFEM, so that the report can address it",
            where=structure.key, key="model", sigil=SIGIL,
        )
        for structure in structures if not structure.named
    ]


def problems(model, structures, known_positions=(), sections_of=None, instances=None):
    """Every finding of this module, in one list -- what an import reports and the window lists.

    Each argument a caller cannot supply is simply left out and the checks that need it do nothing: a project with no exported positions is not told that all of them are unknown, and one with no `calculations.json` is not told that every `@load` is.
    """
    items = list(model.items())
    found = []
    found += position_places(items)
    found += positions_resolve(model, known_positions)
    found += positions_across_structures(structures)
    found += sections_agree(model, sections_of or {})
    found += loads_resolve(model, instances)
    found += widths_plausible(model)
    found += structures_named(structures)
    return found


def keys_in_use(model):
    """Which of the convention's keys this model's comments actually carry, and how often -- what an import prints to say the convention reached the model at all.

    A model where every count is zero is one where the engineer has written no metadata, which is the state every model starts in and is not a fault.
    """
    counts = {key: 0 for key in KEYS}
    for item in model.items():
        for key in item.meta.values:
            if key in counts:
                counts[key] += 1
    return counts


def references(model):
    """Every reference the comments make, by key: `{"position": {"T001": ["Member 24"]}, "load": {...}}` -- what validation resolves and what the window lists."""
    found = {key: {} for key in sorted(REFERENCES)}
    for item in model.items():
        for key in found:
            value = item.meta.get(key)
            if value:
                found[key].setdefault(value, []).append(item.where)
    return found


# --- the small readings the checks share -----------------------------------------------------------


def _elements(model):
    """The members and the surfaces, as `Item`s -- the only objects a position may be on."""
    return [item for item in model.items() if item.kind in ELEMENT_KINDS]


def _with_key(model, key):
    return [item for item in model.items() if key in item.meta]


def _section_of(model, item):
    if item.kind != "member":
        return None
    for member in model.members:
        if member.no == item.number:
            return model.section_of(member)
    return None


def _apart(ours, theirs):
    return any(abs(a - b) > SECTION_TOLERANCE for a, b in zip(ours, theirs))


def _mm(pair):
    return f"{pair[0]:g}/{pair[1]:g} mm"


def _some(structure, limit=4):
    numbers = structure.numbers("member") or structure.numbers("surface")
    shown = ", ".join(str(number) for number in numbers[:limit])
    kind = "members" if structure.numbers("member") else "surfaces"
    return f"{kind} {shown}" + (" …" if len(numbers) > limit else "")
