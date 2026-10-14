"""The structures an RFEM model holds: which members, surfaces, supports and loads form one static system, and what the engineer called it.

An RFEM model is one file and usually several structures — this project's is a bicycle shelter, an escape stair and a pavilion in one `.rf6` — and a Woodcore static model is one of them (docs/domain/static-models.md §3.3octies). This module is what tells them apart: it groups the objects that are physically connected and reads the engineer's `@model`, `@label` and `@descr` off their comments to name each group. It computes nothing structural, draws nothing and writes nothing.

**It works on plain objects and knows no file format.** Its input is a list of `Item` — a kind, a number, the nodes the object is defined by or acts on, and the `Metadata` its comment held — so the same detection serves a table exported from RFEM's interface, a table an API script wrote, and a fixture. That is deliberate: the format of the model tables is still being established against a real GUI export, and nothing here has to wait for it.

**A structure is a connected component of the node graph.** A member joins its two nodes, a surface joins its boundary nodes, and two objects are in one structure when a chain of elements runs from one to the other. Supports, loads and nodes carry no connectivity of their own: each belongs to the component of what it sits on. This is RFEM's own notion of connection — **by node, never by distance**.

⚠️ **Two members that touch on the drawing and share no node are two structures, and that is reported rather than repaired.** It is the commonest way a model surprises its author: a hinge modelled as two coincident nodes, a member drawn to a point that was never merged. Joining them by proximity would need a tolerance, and a tolerance that merges two structures the engineer meant to keep apart is worse than a list he can read — so geometry is not consulted at all. What repairs it is `@model`:

**`@model` names a structure, and where two components carry the same name they are one structure.** That is the one direction the engineer can override the geometry in, and it is the direction that is safe: saying «these two groups are the Velo-Unterstand» adds information the model does not hold. The other direction cannot work — two different `@model` inside one connected component is a contradiction, since nothing can part what RFEM has joined — so it is reported by name, with the value that most objects carry used meanwhile.

**Three keys, and they name two different things** (`metadata_parser.KEYS`, the engineer's own mapping): **`@model` is the structure's name**, while **`@label` and `@descr` are the name and the description of the *static model* it will become** — «VU-gunstig» naming the structure, «Velo Unterstand mit günstige Einwirkungen» the static model, «günstige Einwirkung mit reduzierte Einwirkungsbreite» its description. The same structure calculated with another set of load assumptions is another static model, which is why the two are apart. ⚠️ The engineer's word for it is «schéma»; Woodcore's own «Schémas» tab is the connection details (docs/domain/detail-schemas.md §3.3decies), so the fields here are named after **statics**, which is what they will be written into.

**No id is made here.** A structure's id is the file name of the `statics/<id>.json` it becomes, and it is made where files are written, by `connection.id_from_name` — the one slug this project has. A `Structure` carries its `name` and a `key` that is stable enough to list and group by, and nothing that looks like a file name.

**Nothing refuses.** A group nobody named, a load acting on a member the model no longer carries, a comment on a node that touches nothing: each is an `engine.Note` in `problems` and the import goes on — the rule the plans, the static models and the connectors already follow (docs/architecture/data-contracts.md §3.6), since a detection that stopped on one unnamed group would stop the import of every other.

👉 **What is measured and what is not.** The algorithm was run on the engineer's own model — 62 members over 93 nodes, read through the member → line → nodes chain — and the counts it gives are in `tests/test_structure_detection.py`. The *format* the items are built from is not settled: the model tables of that run were API-shaped, and the reader that builds `Item`s from an interface export is written against a real one (docs/open-questions.md §14).
"""

import engine
from rfem_import.metadata_parser import SIGIL, Metadata

# The kinds of object that *connect* nodes, and so the only ones the components are built from. Everything else — a node, a support, a load, a hinge — belongs to the component of what it sits on. ⚠️ It is the same pair `metadata_parser.MEMBER_OR_SURFACE_ONLY` names, and for a different reason: there, because only these may carry a position; here, because only these carry connectivity. Two facts about one pair, so neither is derived from the other.
ELEMENT_KINDS = ("member", "surface")

# The key that names the structure, and the two that name and describe the static model it becomes (above).
NAME_KEY = "model"
STATICS_NAME_KEY = "label"
STATICS_DESCR_KEY = "descr"

# How many objects a message names before it says «…». A group of sixty members must not print sixty numbers into a warning.
LISTED = 4


def _hosts(on):
    """What an item acts on, as a tuple of `(kind, number)` pairs — given as one pair or as a list of them."""
    if not on:
        return ()
    if isinstance(on[0], str):
        return ((str(on[0]), int(on[1])),)
    return tuple((str(kind), int(number)) for kind, number in on)


class Item:
    """One RFEM object as the detection sees it: its kind, its number, the nodes it is defined by or acts on, and the metadata its comment held.

    `kind` is free text — «member», «surface», «node», «support», «load», «hinge» — and only membership of `ELEMENT_KINDS` changes what the algorithm does with it, so a reader may introduce a kind this module has never heard of and it will be grouped and listed like the rest.

    `nodes` is what places the object: a member's two ends, a surface's boundary, **the nodes** a support is applied to. A load that acts on elements rather than on nodes names them in `on` — `("member", 24)`, or `[("member", 2), ("member", 8)]` — and is placed where they are; `case` is the load case it belongs to, carried so that a structure can say which loadings act on it.

    ⚠️ **An RFEM support or load is one object applied to a set**, not one physical support or one arrow: this model's nodal support 2 holds 23 nodes and its member load 1 acts on members 2, 8 and 9. So `nodes` and `on` are plural, and such an object may reach more than one structure — which `detect` places in each of them rather than in the first it finds.
    """

    __slots__ = ("kind", "number", "nodes", "meta", "on", "case")

    def __init__(self, kind, number, nodes=(), meta=None, on=None, case=None):
        self.kind = str(kind)
        self.number = int(number)
        self.nodes = tuple(int(node) for node in nodes)
        self.meta = meta if meta is not None else Metadata()
        self.on = _hosts(on)
        self.case = case

    @property
    def is_element(self):
        return self.kind in ELEMENT_KINDS

    @property
    def where(self):
        """How a message names this object: «Member 24», «Node 36», «Member load 1» — the `where` `parse_metadata` was given for the same comment, so one object is named one way wherever it is reported."""
        kind = self.kind.replace("_", " ")
        return f"{kind[:1].upper()}{kind[1:]} {self.number}"

    def __repr__(self):
        return f"Item({self.kind!r}, {self.number}, nodes={self.nodes})"


class Structure:
    """One structure: what it is made of, what the engineer called it, and which loadings act on it.

    ⚠️ `nodes` is a list of **node numbers** where `members`, `surfaces`, `supports` and `loads` are lists of **items**. The asymmetry is the graph's: a node is a vertex of the component and exists whether or not a node table was read, while an element or a load is an object that was.
    """

    __slots__ = ("key", "name", "statics_name", "statics_descr", "nodes", "items", "cases", "combinations", "problems")

    def __init__(self, key, name, statics_name, statics_descr, nodes, items, cases, combinations, problems):
        self.key, self.name = key, name
        self.statics_name, self.statics_descr = statics_name, statics_descr
        self.nodes, self.items = nodes, items
        self.cases, self.combinations = cases, combinations
        self.problems = problems

    @property
    def named(self):
        """True where the engineer wrote `@model` on one of its objects. A structure that is not named is one the import can list and not one it can address."""
        return self.name is not None

    def of(self, kind):
        """Its items of one kind, by number — `of("member")`, `of("load")`, and any kind a reader introduced."""
        return [item for item in self.items if item.kind == kind]

    def numbers(self, kind):
        return [item.number for item in self.of(kind)]

    @property
    def members(self):
        return self.of("member")

    @property
    def surfaces(self):
        return self.of("surface")

    @property
    def supports(self):
        return self.of("support")

    @property
    def loads(self):
        return [item for item in self.items if item.kind.endswith("load")]

    @property
    def elements(self):
        """Its members and its surfaces, which are the objects a position may be written on."""
        return [item for item in self.items if item.is_element]

    @property
    def positions(self):
        """The Woodcore positions its elements name: `{position: [item, …]}` — what the window lists and what validation resolves against `Positionen.xlsx`."""
        found = {}
        for item in self.elements:
            position = item.meta.get("position")
            if position:
                found.setdefault(position, []).append(item)
        return found

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return (f"Structure({self.name or self.key!r}, {len(self.members)} members, "
                f"{len(self.surfaces)} surfaces, {len(self.nodes)} nodes)")


class Structures:
    """Every structure one model holds, in the order of their lowest element, with what belonged to none of them.

    `orphans` are the items the graph could not place: a node no element touches, a load acting on an element the model no longer carries. `shared` are the ones that reached more than one structure — an RFEM support or load being one object applied to a set (`Item`) — and they are listed in each. Both are kept rather than dropped, so that an import can say how many objects it accounted for: `items_accounted` is every item it was given.
    """

    __slots__ = ("structures", "orphans", "shared", "problems", "_by_element")

    def __init__(self, structures, orphans, shared, problems):
        self.structures, self.orphans, self.shared, self.problems = structures, orphans, shared, problems
        self._by_element = {}
        for structure in structures:
            for item in structure.elements:
                self._by_element[(item.kind, item.number)] = structure

    def of(self, name):
        """The structure of that name or key, or None."""
        for structure in self.structures:
            if name in (structure.name, structure.key):
                return structure
        return None

    def holding(self, kind, number):
        """The structure one element belongs to, or None — what tells a member's forces which static system they act in."""
        return self._by_element.get((kind, int(number)))

    def by_member(self, number):
        return self.holding("member", number)

    @property
    def names(self):
        return [structure.name or structure.key for structure in self.structures]

    @property
    def items_accounted(self):
        """Every item this detection was given, as it placed them — what a test compares with the length of its input.

        Counted by identity rather than summed over the structures, an object applied to a set of nodes being listed in each structure it reaches.
        """
        placed = {id(item) for structure in self.structures for item in structure.items}
        return len(placed) + len(self.orphans)

    def __len__(self):
        return len(self.structures)

    def __iter__(self):
        return iter(self.structures)

    def __repr__(self):
        return f"Structures({len(self.structures)} structures, {len(self.orphans)} orphans)"


class _Sets:
    """Union-find over node numbers: the components, built in one pass over the elements.

    A surface's boundary is joined by chaining its nodes to the first rather than by pairing them all, which is what keeps a surface of thirty nodes thirty unions instead of four hundred. The **lowest** number is kept as a set's root, so a root is a readable node number and the grouping is the same whatever order the elements came in.
    """

    __slots__ = ("parent",)

    def __init__(self):
        self.parent = {}

    def add(self, node):
        self.parent.setdefault(node, node)

    def __contains__(self, node):
        return node in self.parent

    def find(self, node):
        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[node] != root:                       # path compression, so a long chain is walked once
            self.parent[node], node = root, self.parent[node]
        return root

    def union(self, a, b):
        first, second = self.find(a), self.find(b)
        if first != second:
            self.parent[max(first, second)] = min(first, second)


def _some(items):
    """The items a message names: at most `LISTED` of them, by number, and «…» for the rest."""
    shown = ", ".join(item.where for item in items[:LISTED])
    return shown + (" …" if len(items) > LISTED else "")


def _decide(items, key, where, problems):
    """The one value a group of objects gives for `key`, with every disagreement named.

    Where they disagree the value **most** of them carry is used, ties going to the lowest-numbered object, and the note says what to do about it: a connected group cannot be two structures, so the parting has to happen in RFEM.
    """
    written = {}
    for item in items:
        value = item.meta.get(key)
        if value:
            written.setdefault(value, []).append(item)
    if not written:
        return None
    if len(written) == 1:
        return next(iter(written))
    chosen = max(written, key=lambda value: (len(written[value]), -min(item.number for item in written[value])))
    told = "; ".join(f"«{value}» on {_some(carriers)}" for value, carriers
                     in sorted(written.items(), key=lambda pair: min(item.number for item in pair[1])))
    problems.append(engine.Note(
        "rfem_structure_conflict",
        f"{where}: {SIGIL}{key} is given as {told} -- these objects are one connected group, so «{chosen}» is used; "
        f"to make two structures of them, part them in RFEM",
        where=where, key=key, chosen=chosen, values=told,
    ))
    return chosen


def _placeholder(elements):
    """The key a group nobody named is listed under: its lowest element, «member-1». Stable while that element exists, which is what keeps a second import from renaming everything."""
    lowest = min(elements, key=lambda item: (item.kind, item.number))
    return f"{lowest.kind}-{lowest.number}"


def _roots_of(item, sets, by_element):
    """Every component an item reaches, and the hosts it names that the model does not carry: `(roots, missing)`.

    **Every** node is looked at rather than the first alone, because an RFEM support or load is one object applied to a set and that set may span two structures (`Item`). A load naming elements in `on` is placed where each of them is, and one naming a node at that node; an element's own nodes are in one component by construction, having been united by it.
    """
    roots, missing = set(), []
    for node in item.nodes:
        if node in sets:
            roots.add(sets.find(node))
    for kind, number in item.on:
        host = by_element.get((kind, number))
        if host is not None:
            for node in host.nodes:
                if node in sets:
                    roots.add(sets.find(node))
        elif kind == "node" and number in sets:
            roots.add(sets.find(number))
        elif kind in ELEMENT_KINDS:
            missing.append((kind, number))
    return sorted(roots), missing


def detect(items, combinations=None):
    """The structures a model holds, from its objects.

    `items` are `Item`s in any order. `combinations` is optional and maps a combination to the load cases it is built from — `{"CO1": ["CC1", "CC2"], …}`, its keys and values compared with `Item.case` and never interpreted — so that a structure can say which combinations act on it, which is what the window lists beside its elements.
    """
    items = list(items)
    problems = []

    sets = _Sets()
    by_element = {}
    for item in items:
        if not item.is_element:
            continue
        by_element[(item.kind, item.number)] = item
        if len(item.nodes) < 2:
            problems.append(engine.Note(
                "rfem_structure_no_nodes",
                f"{item.where} is defined by {len(item.nodes)} node(s), so it connects nothing -- "
                f"check the line it is drawn on in RFEM",
                where=item.where, kind=item.kind, number=item.number, nodes=len(item.nodes),
            ))
        for node in item.nodes:
            sets.add(node)
        for node in item.nodes[1:]:
            sets.union(item.nodes[0], node)

    # The nodes of each component, gathered once. Asking `find` per node per component instead would be the length of the model times the number of structures, for an answer one pass already holds.
    component_nodes = {}
    for node in sets.parent:
        component_nodes.setdefault(sets.find(node), []).append(node)

    # Every item to every component it reaches, and what could not be placed. A host the model does not carry is reported whether or not the item was placed: a load acting on members 2, 8 and 9 of which 9 was deleted is a load that no longer says what it acts on.
    groups, orphans, shared = {}, [], []
    for item in items:
        roots, missing = _roots_of(item, sets, by_element)
        for kind, number in missing:
            problems.append(engine.Note(
                "rfem_structure_unknown_host",
                f"{item.where} acts on {kind} {number}, which the model does not carry -- "
                f"that part of it is left out",
                where=item.where, kind=kind, number=number,
            ))
        if not roots:
            orphans.append(item)
            if item.meta and not missing:
                problems.append(engine.Note(
                    "rfem_structure_orphan",
                    f"{item.where} carries metadata and belongs to no structure, no element touching it -- "
                    f"write it on a member or a surface of the structure it is about",
                    where=item.where, kind=item.kind, number=item.number,
                ))
            continue
        if len(roots) > 1:
            shared.append(item)
        for root in roots:
            groups.setdefault(root, []).append(item)

    # A component's name is decided before the merge, since it is what merges.
    names = {}
    for root in sorted(groups):
        group = groups[root]
        elements = [item for item in group if item.is_element]
        where = f"the group of {min(elements, key=lambda i: (i.kind, i.number)).where}" if elements else f"the group at node {root}"
        names[root] = _decide(group, NAME_KEY, where, problems)

    # Components carrying the same `@model` are one structure; two unnamed ones never merge, their placeholders differing by construction. The key is tagged so that a name equal to a placeholder cannot join two groups by accident.
    merged = {}
    for root in sorted(groups):
        name = names[root]
        elements = [item for item in groups[root] if item.is_element]
        key = ("named", name) if name else ("auto", _placeholder(elements) if elements else f"node-{root}")
        merged.setdefault(key, []).append(root)

    structures = []
    for (tag, key), roots in merged.items():
        # Deduplicated by identity: an object applied to nodes of two components that this name then merges would otherwise be listed twice in the structure they became.
        group = list(dict.fromkeys(item for root in roots for item in groups[root]))
        nodes = sorted(node for root in roots for node in component_nodes.get(root, ()))
        elements = [item for item in group if item.is_element]
        where = f"the structure «{key}»" if tag == "named" else (
            f"the group of {min(elements, key=lambda i: (i.kind, i.number)).where}" if elements else f"the group at node {roots[0]}")
        own = []
        statics_name = _decide(group, STATICS_NAME_KEY, where, own)
        statics_descr = _decide(group, STATICS_DESCR_KEY, where, own)
        if tag == "auto":
            own.append(engine.Note(
                "rfem_structure_unnamed",
                f"{where} is a structure nobody named -- write «{SIGIL}{NAME_KEY} <name>» in the comment of one of "
                f"its members ({_some(elements)}) so that the report can address it",
                where=where, key=NAME_KEY, sigil=SIGIL, elements=_some(elements),
            ))
        cases = sorted({item.case for item in group if item.case is not None}, key=str)
        acting = sorted((label for label, built in (combinations or {}).items()
                         if any(case in cases for case in built)), key=str)
        problems.extend(own)
        structures.append(Structure(
            key=key, name=key if tag == "named" else None,
            statics_name=statics_name, statics_descr=statics_descr,
            nodes=nodes, items=sorted(group, key=lambda i: (i.kind, i.number)),
            cases=cases, combinations=acting, problems=own,
        ))

    structures.sort(key=lambda structure: (
        min((item.number for item in structure.elements), default=0),
        structure.key,
    ))
    return Structures(structures, orphans, shared, problems)
