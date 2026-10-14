"""The model an RFEM table export holds: its nodes, its members, its sections, its supports, its loads, its load cases and its combinations.

This is the half of the import that answers «what is in the model», where `results.py` answers «what did it come to». It reads what RFEM's **own table export** writes — *Fichier → Exporter → Tableaux*, which needs no API key — through the one table abstraction of `csv_tables.py`, so it is indifferent to which of that dialog's formats it was handed: **one XLSX of every table, or one CSV per table**. `read_model` takes either.

👉 **Written against an authentic export**, `Musterprojekt/01_29509-Model.xlsx`: 120 sheets of which 25 hold data, 62 members over 91 nodes, 5 load cases, 48 combinations, 162 loads. Every format fact below was measured on it, and the counts it gives are in `tests/test_model_tables.py`.

**The shape of a table**, and the three traps in it:

⚠️ **A number RFEM lists is not always an object.** A deleted object leaves an **empty row carrying its number**: this model's node table has 97 rows for 91 nodes (3, 4, 6, 10, 16, 56 are gone) and its member table 64 rows for 62 members (11 and 12 are gone). A row whose defining column is empty is skipped and counted. Ticking «Lignes remplies uniquement» in the export dialog removes them, and the reader does not depend on that having been ticked.

⚠️ **A list of object numbers carries ranges.** «Assignée aux barres n°» reads `2,8,9` on one load and `2-4` on another, and a section's member list reads `1,2,5,8-10,13,14,17-19`. Read without expanding the ranges, half the assignments are silently lost — a load on three members becoming a load on none.

⚠️ **The load tables are one sheet per load case**, and the prefix is the load case's own localised id: `CC1 - Charges de barre` here, `LF1 - Stablasten` in a German installation. So the sheets are not looked for by a name this module spells: the load cases are read first, and each one's loads are the sheets whose name begins with its own id. That is what makes the load → case link exist at all — the gRPC API's object listing carries none.

**Every number is read with the unit its header declares** — «X [m]», «Largeur b [mm]», «p [kN/m]» — because a unit is whatever the model's «Unités et décimales» says. Coordinates and lengths come back in **metres**, a section's b and h in **millimetres**, which is what a Woodcore static model and a detail schema respectively are drawn in (docs/domain/static-models.md §3.3octies, docs/domain/detail-schemas.md §3.3decies). ⚠️ The export **rounds to that setting**, per quantity: a line this model computes as 0.5099999999999998 is written `0.51`. Three decimals on a length in metres is a millimetre, which is what a static model needs; nothing here can recover more, and the gRPC route is where full precision lives.

**The headers are localised, and all three languages are read off a real export** -- `FR.xlsx`, `DE.xlsx` and `EN.xlsx` of 26.09.2026, 490 to 609 sheets each, the same model exported three times. Read against those, the three give **the same model to the digit**: the same nodes, members, sections, supports, hinges and metadata, and the same 22 structures. What differs is only what RFEM itself translates -- a material's name as its own library spells it, the load duration, a load's type and distribution, the design situation, and the load case's own abbreviation (`CC`, `LF`, `LC`), which is carried as an opaque label and never interpreted. ⚠️ **Two aliases written from the manual were wrong and silently so**, and the export is what said so: the German hinge sheet is «Stabendgelenke» and not «Stabgelenke», and a load's type is «Lastart» and not «Lasttyp». `require` names what a table actually holds, so an unrecognised header says which alias to add rather than producing a wrong number.

**Nothing refuses.** A sheet missing, a row whose number cannot be read, a member whose line the model lost, a load whose magnitude column is not named: each is an `engine.Note` in `problems` and the rest of the model is read — the rule the plans, the static models and the connectors already follow (docs/architecture/data-contracts.md §3.6). What a caller cannot do without, it asks for with `require`.

**What this module does not do.** It does not detect structures (`structure_detection.py`, which `Model.items()` feeds), does not resolve a `@position` against `Positionen.xlsx` (validation's), and computes nothing. It reads a model and hands it on.
"""

import math
import os

import engine
from rfem_import.csv_tables import LENGTH_UNITS, RfemCsvError, fold, number, read_table, read_workbook
from rfem_import.metadata_parser import parse_metadata
from rfem_import.structure_detection import Item

# What RFEM writes in a cell that holds nothing: a double dash. Read as empty, or a member's «--» hinge comes back as the string it is written with.
NONE_CELLS = frozenset({"--", "-", "–", "—", ""})

# The sheets, in the three languages, every one read off a real export (module docstring). The extra aliases after the first three are what the manual's vocabulary had, kept so that an older or a differently configured export is still recognised.
SHEETS = {
    "nodes": ("Nœuds", "Knoten", "Nodes"),
    "lines": ("Lignes", "Linien", "Lines"),
    "members": ("Barres", "Stäbe", "Members"),
    "surfaces": ("Surfaces", "Flächen", "Surfaces"),
    "sections": ("Sections", "Querschnitte", "Cross-Sections", "Sections"),
    "materials": ("Matériaux", "Materialien", "Materials"),
    "supports": ("Appuis nodaux", "Knotenlager", "Nodal Supports"),
    "hinges": ("Articulations de barre", "Stabendgelenke", "Member Hinges", "Stabgelenke"),
    "cases": ("Cas de charge", "Lastfälle", "Load Cases"),
    "combinations": ("Combinaisons de charges", "Lastkombinationen", "Load Combinations"),
}

# The kinds of load sheet a load case has, by the part of the name that follows its id.
LOAD_SHEETS = {
    "member_load": ("Charges de barre", "Stablasten", "Member Loads"),
    "nodal_load": ("Charges nodales", "Knotenlasten", "Nodal Loads"),
    "surface_load": ("Charges surfaciques", "Flächenlasten", "Surface Loads"),
    "line_load": ("Charges linéiques", "Linienlasten", "Line Loads"),
}

# The columns, per table. The first alias of each is the French one the export writes.
COLUMNS = {
    "node_no": ("Nœud n°", "Knoten Nr.", "Node No."),
    "node_x": ("Coordonnées globales X", "Globale Koordinaten X", "Global Coordinates X", "X"),
    "node_z": ("Coordonnées globales Z", "Globale Koordinaten Z", "Global Coordinates Z", "Z"),
    "line_no": ("Ligne n°", "Linie Nr.", "Line No."),
    "line_nodes": ("Nœuds n°", "Knoten Nr.", "Nodes No."),
    "member_no": ("Barre n°", "Stab Nr.", "Member No."),
    "member_line": ("Ligne n°", "Linie Nr.", "Line No."),
    "member_type": ("Type de barre", "Stabtyp", "Member Type"),
    "section_start": ("Section Début i", "Querschnitt Anfang i", "Cross-Section Start i", "Quersch. Anfang i", "Section Start i"),
    "hinge_start": ("Articulation Début i", "Gelenk Anfang i", "Hinge Start i"),
    "hinge_end": ("Articulation Fin j", "Gelenk Ende j", "Hinge End j"),
    "length": ("Longueur L", "Länge L", "Length L", "L"),
    "surface_no": ("Surface n°", "Fläche Nr.", "Surface No."),
    "surface_lines": ("Lignes de contour", "Randlinien", "Boundary Lines"),
    "surface_thickness": ("Épaisseur", "Dicke", "Thickness"),
    "cs_no": ("Section n°", "Quersch. Nr.", "Cross-Section No.", "Querschnitt Nr."),
    "cs_name": ("Nom de la section", "Name des Querschnitts", "Cross-Section Name", "Cross-Section Description"),
    "cs_members": ("Assigné aux barres n°", "Zugewiesen an Stäbe Nr.", "Assigned to Members No.", "Zugeordnet zu Stäben Nr."),
    "cs_material": ("Matériau", "Material"),
    "cs_b": ("Largeur b", "Breite b", "Width b"),
    "cs_h": ("Hauteur h", "Höhe h", "Depth h", "Height h"),
    "material_no": ("Matériau n°", "Material Nr.", "Material No."),
    "material_name": ("Nom", "Name des Materials", "Material Name", "Bezeichnung", "Description", "Name"),
    "name": ("Nom", "Bezeichnung", "Description", "Name"),
    "support_no": ("Appui n°", "Lager Nr.", "Support No."),
    "support_nodes": ("Assigné aux nœuds n°", "Zugewiesen an Knoten Nr.", "Assigned to Nodes No.", "Zugeordnet zu Knoten Nr."),
    "hinge_no": ("Articul. n°", "Gelenk Nr.", "Hinge No."),
    "spring_x": ("Cu,X", "Cu,x"),
    "spring_z": ("Cu,Z", "Cu,z"),
    "spring_phi": ("Cφ,Y", "Cφ,y"),
    "case_no": ("Cas de charge", "Lastfall", "Load Case"),
    "case_name": ("Nom", "Bezeichnung", "Description", "Name"),
    "case_category": ("Catégorie d'action", "Einwirkungskategorie", "Action Category"),
    "case_duration": ("Durée de charge", "Lasteinwirkungsdauer", "Load Duration"),
    "combination_no": ("Comb. charges", "Last-kombin.", "Load Combs.", "Lastkombination", "Load Combination"),
    "combination_situation": ("Situation de projet", "Bemessungssituation", "Design Situation"),
    "factor": ("Facteur", "Faktor", "Factor"),
    "load_no": ("n°", "Nr.", "No."),
    "load_members": ("Assignée aux barres n°", "Zugewiesen an Stäbe Nr.", "Assigned to Members No.", "Zugeordnet zu Stäben Nr."),
    "load_nodes": ("Assigné aux nœuds n°", "Zugewiesen an Knoten Nr.", "Assigned to Nodes No.", "Zugeordnet zu Knoten Nr."),
    "load_type": ("Type de charge", "Lastart", "Load Type", "Lasttyp"),
    "load_distribution": ("Répartition de charge", "Lastverteilung", "Load Distribution"),
    "load_direction": ("Direction de charge", "Lastrichtung", "Load Direction", "de charge"),
    "comment": ("Commentaire", "Kommentar", "Comment"),
}

# What SIA 260 calls the action a load case is: the word RFEM writes in «Catégorie d'action», folded, mapped to the `action` a Woodcore load domain declares (docs/domain/calculation-domains.md §3.3). A category this table does not name is carried as it was written and left unclassified rather than guessed at.
PERMANENT = ("permanent", "permanente", "standig", "ständig", "poids_propre", "eigengewicht", "self_weight")


# The widest run a «8-10» may stand for. A range beyond it is read as its two ends: an object number is not a quantity, and a mistyped range must not become a list nothing can use.
RANGE_LIMIT = 5000


def _text(cell):
    """A cell as text, RFEM's «--» read as nothing."""
    text = ("" if cell is None else str(cell)).strip()
    return "" if text in NONE_CELLS else text


def _int(cell):
    value = number(_text(cell))
    return None if value is None else int(value)


def numbers(cell):
    """The object numbers a cell lists, **ranges expanded**: «1,2» → [1, 2], «2-4» → [2, 3, 4], «1,2,5,8-10» → [1, 2, 5, 8, 9, 10].

    ⚠️ The ranges are the trap: read without expanding them a load «assignée aux barres 2-4» acts on nothing, and a section «assignée aux barres 8-10» is assigned to nothing. A range whose ends are the wrong way round, and one wider than `RANGE_LIMIT`, are read as the two numbers they name rather than as a run — a typo must not build a list of ten thousand.
    """
    found = []
    for part in _text(cell).replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        head, sep, tail = part.partition("-")
        if sep and head.strip().isdigit() and tail.strip().isdigit():
            first, last = int(head), int(tail)
            if 0 <= last - first <= RANGE_LIMIT:
                found.extend(range(first, last + 1))
            else:
                found.extend((first, last))
            continue
        if part.isdigit():
            found.append(int(part))
    return list(dict.fromkeys(found))




def _length(table, row, key, to="m", where="", problems=None):
    """A length out of the column `key`, in metres by default or in millimetres with `to="mm"`, converted from the unit the header declares.

    A header with no unit at all is read as already in the wanted unit and said so, since a value taken for metres that was millimetres is off by a thousand.
    """
    column = table.column(*COLUMNS[key])
    if column is None:
        return None
    # ⚠️ The cell of **this** column, never a second lookup by its bare name: the node table carries two
    # columns named «X» and two named «Z» -- «Coordonnées», relative to the node's reference node, and
    # «Coordonnées globales» -- and asking for «X» gives back the first, which is the relative one
    # (`csv_tables.Row.value`). That read every node defined relative to another at the wrong place.
    value = row.at(column)
    if value is None:
        return None
    factor = LENGTH_UNITS.get(fold(column.unit or ""))
    if factor is None:
        if problems is not None and column.unit:
            problems.append(engine.Note(
                "rfem_model_unit",
                f"{where}: «{column.name}» is given in «{column.unit}», which is not a length unit this reader knows -- "
                f"it knows {', '.join(sorted(LENGTH_UNITS))}",
                where=where, key=key, unit=column.unit,
            ))
        factor = LENGTH_UNITS[to]
    return value * factor / LENGTH_UNITS[to]


# How near a node must be to a member's axis to count as lying on it, in metres. Exact incidence and
# nothing else: a model states a node on a line, it does not state one a millimetre away (`Model.on_member`).
ON_MEMBER = 1e-6


class Node:
    """One node: its number, its global coordinates in **metres**, and the metadata its comment held."""

    __slots__ = ("no", "x", "z", "meta", "text")

    def __init__(self, no, x, z, meta):
        self.no, self.x, self.z, self.meta = no, x, z, meta
        self.text = meta.text

    def __repr__(self):
        return f"Node({self.no}, x={self.x}, z={self.z})"


class Member:
    """One member: the line it is drawn on, the nodes that line joins, its type, its section, its hinges and its metadata."""

    __slots__ = ("no", "line", "nodes", "type", "section", "hinge_start", "hinge_end", "length", "meta")

    def __init__(self, no, line, nodes, type, section, hinge_start, hinge_end, length, meta):
        self.no, self.line, self.nodes = no, line, nodes
        self.type, self.section = type, section
        self.hinge_start, self.hinge_end = hinge_start, hinge_end
        self.length, self.meta = length, meta

    @property
    def position(self):
        """The Woodcore position this member realises, where its comment names one."""
        return self.meta.get("position")

    def __repr__(self):
        return f"Member({self.no}, line={self.line}, nodes={self.nodes}, section={self.section})"


class Surface:
    __slots__ = ("no", "lines", "nodes", "thickness", "meta")

    def __init__(self, no, lines, nodes, thickness, meta):
        self.no, self.lines, self.nodes, self.thickness, self.meta = no, lines, nodes, thickness, meta

    @property
    def position(self):
        return self.meta.get("position")

    def __repr__(self):
        return f"Surface({self.no}, {len(self.nodes)} nodes)"


class Section:
    """One cross-section: its name, its material, its **b and h in millimetres**, and the members it is assigned to."""

    __slots__ = ("no", "name", "material", "b", "h", "members", "meta")

    def __init__(self, no, name, material, b, h, members, meta):
        self.no, self.name, self.material = no, name, material
        self.b, self.h, self.members, self.meta = b, h, members, meta

    def __repr__(self):
        return f"Section({self.no}, {self.name!r}, b={self.b}, h={self.h})"


class Material:
    __slots__ = ("no", "name", "meta")

    def __init__(self, no, name, meta):
        self.no, self.name, self.meta = no, name, meta

    def __repr__(self):
        return f"Material({self.no}, {self.name!r})"


class Restraint:
    """A support or a hinge: what it holds and how stiff it is.

    `x`, `z` and `phi` are `math.inf` where RFEM writes «inf» — rigid — a number where it is a spring, and None where the table leaves the cell empty. A support is `fixed` where all three are rigid, `pinned` where the translations are and the rotation is free, and a spring otherwise: the words a Woodcore static model uses (docs/domain/static-models.md §3.3octies).
    """

    __slots__ = ("no", "role", "nodes", "x", "z", "phi", "meta")

    def __init__(self, no, role, nodes, x, z, phi, meta):
        self.no, self.role, self.nodes = no, role, nodes
        self.x, self.z, self.phi, self.meta = x, z, phi, meta

    @staticmethod
    def _rigid(value):
        return value is not None and value == float("inf")

    @property
    def kind(self):
        """What it is, in the words a Woodcore static model uses (docs/domain/static-models.md §3.3octies).

        A **support**: `fixed` where both translations and the rotation are rigid, `pinned` where the translations are and the rotation is free, `roller` where one translation is, `spring` where a finite stiffness is given, `free` where nothing is held.

        A **hinge**: `moment` where the rotation is released and the translations are not, `shear` or `normal` where one of those is released, `rotational-spring` where the rotation carries a finite stiffness, `rigid` where nothing is released.

        ⚠️ **The two read the same number the opposite way round.** RFEM's hinge columns are «Libération/ressort de …», so an `inf` there means *not* released where on a support it means held — which is why a `Restraint` carries the role it was read under. Measured on this model: hinge 1 is Cφ,y = 0, a moment release, and hinge 2 is Cφ,y = 21.672 kNm/rad, a rotational spring; read as supports both came out «pinned».
        """
        free_x, free_z = not self._rigid(self.x), not self._rigid(self.z)
        spring_phi = self.phi is not None and self.phi != 0.0 and not self._rigid(self.phi)
        if self.role == "hinge":
            if spring_phi:
                return "rotational-spring"
            if free_z:
                return "shear"
            if free_x:
                return "normal"
            return "moment" if self.phi in (None, 0.0) else "rigid"
        rigid = [not free_x, not free_z]
        if all(rigid) and self._rigid(self.phi):
            return "fixed"
        if all(rigid):
            return "pinned"
        if any(rigid):
            return "roller"
        if spring_phi or any(value not in (None, 0.0) for value in (self.x, self.z)):
            return "spring"
        return "free"

    def __repr__(self):
        return f"Restraint({self.role} {self.no}, {self.kind}, nodes={self.nodes})"


class Case:
    """One load case: the id RFEM addresses it by («CC1» in French, «LF1» in German), its name, and what kind of action it is."""

    __slots__ = ("id", "name", "category", "duration", "meta")

    def __init__(self, id, name, category, duration, meta):
        self.id, self.name = id, name
        self.category, self.duration, self.meta = category, duration, meta

    @property
    def action(self):
        """`permanent` or `variable` in SIA 260's terms, or None where the category is one this reader does not classify."""
        folded = fold(self.category)
        if not folded:
            return None
        return "permanent" if any(word in folded for word in PERMANENT) else "variable"

    def __repr__(self):
        return f"Case({self.id!r}, {self.name!r}, {self.action})"


class Combination:
    """One load combination: its id, its name as RFEM writes it («1.35 * CC1»), its design situation, its load duration, and the factored cases it is built from.

    👉 **The duration is the one field of this table a timber check needs**: SIA 265's η_t and the modification of
    the strengths follow the duration of the governing action, and RFEM states it per combination — «Permanente»,
    «Court terme» — beside the design situation it belongs to. It is carried as RFEM writes it, since it is a word
    of the norm in the model's own language and not a number to compute with.
    """

    __slots__ = ("id", "name", "situation", "duration", "terms", "meta")

    def __init__(self, id, name, situation, duration, terms, meta):
        self.id, self.name, self.situation = id, name, situation
        self.duration, self.terms, self.meta = duration, terms, meta

    @property
    def cases(self):
        return [case for _, case in self.terms]

    def __repr__(self):
        return f"Combination({self.id!r}, {' + '.join(f'{f} · {c}' for f, c in self.terms)})"


class Load:
    """One load: the case it belongs to, what it acts on, how it acts, and the metadata its comment held — its `@be` among it."""

    __slots__ = ("no", "kind", "case", "members", "nodes", "type", "distribution", "direction", "magnitude", "unit", "meta")

    def __init__(self, no, kind, case, members, nodes, type, distribution, direction, magnitude, unit, meta):
        self.no, self.kind, self.case = no, kind, case
        self.members, self.nodes = members, nodes
        self.type, self.distribution, self.direction = type, distribution, direction
        self.magnitude, self.unit, self.meta = magnitude, unit, meta

    @property
    def width(self):
        """The influence width the comment states, in metres, or None."""
        return self.meta.get("be")

    def __repr__(self):
        return f"Load({self.case}/{self.kind} {self.no}, {self.magnitude} {self.unit})"


class Model:
    """The model one export holds, and what could not be read of it.

    `skipped` counts, per table, the rows RFEM listed for an object that is gone — the empty numbered rows — so an import can say «97 node rows, 91 nodes» rather than quietly reading six fewer nodes than the file seems to hold.
    """

    __slots__ = ("source", "nodes", "lines", "members", "surfaces", "sections", "materials",
                 "supports", "hinges", "cases", "combinations", "loads", "skipped", "problems")

    def __init__(self, source, **parts):
        self.source = source
        for name in self.__slots__[1:]:
            setattr(self, name, parts.get(name) if name in parts else ({} if name in ("skipped",) else []))

    def node(self, no):
        for node in self.nodes:
            if node.no == no:
                return node
        return None

    def section_of(self, member):
        """The section a member carries, resolved through the section table's own member list where the member table does not name one."""
        if member.section is not None:
            for section in self.sections:
                if section.no == member.section:
                    return section
        for section in self.sections:
            if member.no in section.members:
                return section
        return None

    def on_member(self):
        """The nodes that lie **on** a member without being one of its two ends: `{member: [node, …]}`.

        ⚠️ **A column whose top sits mid-span of an undivided beam shares no definition node with it**, and the
        two are then two structures although RFEM calculates them as one. It is not a hypothetical: the Velo
        Unterstand's Regelfall is a beam (member 2, nodes 14 and 15) carried at its middle by a column (member 1,
        whose top is node 2), and node 2 is on the beam's line without dividing it — so the beam came out as a
        structure with no support at all, and its figure as a beam floating in the air. RFEM says the two are
        joined: its own member-forces table gives member 2 a station **at node 2**, with the 15.1 kN shear jump
        the column puts there.

        👉 **This is not the proximity `structure_detection` refuses.** That module declines to join two members
        that merely *touch*, because that needs a tolerance and a tolerance merges what an engineer meant to keep
        apart. Here the node is on the member's own axis, to the micrometre, which is a statement the model makes
        and not a distance to judge: `ON_MEMBER` is 1e-6 m, small enough that nothing but an exact incidence
        passes it. A node at an end is left out, being a definition node already.
        """
        found = {}
        places = {node.no: (node.x, node.z) for node in self.nodes}
        # ⚠️ **Only a node that another member ENDS at, and only where that member crosses rather than lies along.**
        # A node loose in space joins nothing, and two collinear members that overlap are an overlap — not a column
        # landing on a beam — so joining them would merge two systems an engineer drew apart. The fixture of
        # `tests/fixtures/rfem_model.py` is exactly that case: its members 2 and 24 share a stretch of one line.
        ended_here = {}
        for member in self.members:
            axis = [places[n] for n in member.nodes if n in places]
            if len(axis) < 2:
                continue
            direction = (axis[-1][0] - axis[0][0], axis[-1][1] - axis[0][1])
            for node in member.nodes:
                ended_here.setdefault(node, []).append(direction)
        for member in self.members:
            ends = [places[n] for n in member.nodes if n in places]
            if len(ends) < 2:
                continue
            (ax, az), (bx, bz) = ends[0], ends[-1]
            ux, uz = bx - ax, bz - az
            span = ux * ux + uz * uz
            if span <= 0:
                continue
            for number, (px, pz) in places.items():
                if number in member.nodes:
                    continue
                t = ((px - ax) * ux + (pz - az) * uz) / span
                if not (0.0 < t < 1.0):
                    continue
                gap = math.hypot(px - (ax + t * ux), pz - (az + t * uz))
                if gap > ON_MEMBER:
                    continue
                # A node loose on the member -- a division point carrying a load -- belongs to it. One that is
                # another member's end belongs to it too, unless **every** member ending there runs along it:
                # two collinear members sharing a stretch are an overlap, not a column landing on a beam.
                here = ended_here.get(number, ())
                crossing = [d for d in here if abs(d[0] * uz - d[1] * ux) > ON_MEMBER * math.hypot(ux, uz)]
                if crossing or not here:
                    found.setdefault(member.no, []).append(number)
        return found

    def items(self):
        """The model as `structure_detection.Item`s: every member, surface, node, support and load, each with the nodes that place it and the metadata its comment held.

        A member carries the nodes that lie on it as well as its two ends (`on_member`), so that a column landing
        mid-span of an undivided beam is in the beam's own structure.
        """
        items = []
        through = self.on_member()
        for member, nodes in sorted(through.items()):
            # ⚠️ Reported, because the export cannot say whether RFEM divides the line there: «Lignes» lists a
            # line's two ends and no intermediate node, so incidence is all there is to go on. It is right for a
            # column landing mid-span, and wrong for two studies that merely cross -- this model's bench (member
            # 64) passes through the base of a column. Where the member forces are read, RFEM settles it itself:
            # it writes a station **at** the node only where the member is divided there.
            self.problems.append(engine.Note(
                "rfem.node-on-member",
                f"Member {member} is joined to node(s) {', '.join(str(n) for n in nodes)}, which lie on it -- "
                f"check that RFEM divides the member there, or the two are one structure by accident",
                member=member, nodes=list(nodes)))
        for member in self.members:
            nodes = list(member.nodes) + through.get(member.no, [])
            items.append(Item("member", member.no, nodes=nodes, meta=member.meta))
        for surface in self.surfaces:
            items.append(Item("surface", surface.no, nodes=surface.nodes, meta=surface.meta))
        for node in self.nodes:
            items.append(Item("node", node.no, nodes=[node.no], meta=node.meta))
        for support in self.supports:
            items.append(Item("support", support.no, nodes=support.nodes, meta=support.meta))
        for load in self.loads:
            items.append(Item(
                load.kind, load.no, nodes=load.nodes, case=load.case, meta=load.meta,
                on=[("member", no) for no in load.members],
            ))
        return items

    def combination_cases(self):
        """`{combination id: [case id, …]}` — what `structure_detection.detect` takes to say which combinations act on a structure."""
        return {combination.id: combination.cases for combination in self.combinations}

    def __repr__(self):
        return (f"Model({len(self.members)} members, {len(self.nodes)} nodes, {len(self.sections)} sections, "
                f"{len(self.cases)} cases, {len(self.combinations)} combinations, {len(self.loads)} loads)")


class _Source:
    """Where the tables come from: one XLSX workbook, or a folder of CSVs. One `table(kind)` either way, so nothing above here knows which it was given."""

    def __init__(self, path):
        self.path = str(path)
        self.workbook = None
        self.files = {}
        if os.path.isdir(self.path):
            for entry in sorted(os.listdir(self.path)):
                if entry.lower().endswith(".csv"):
                    self.files[os.path.splitext(entry)[0]] = os.path.join(self.path, entry)
        else:
            try:
                self.workbook = read_workbook(self.path)
            except RfemCsvError:
                raise
            except Exception as error:
                # openpyxl refuses a file that is no workbook in its own words and its own exception type. An import points at one path and must fail one way, naming it.
                raise RfemCsvError(
                    f"{self.path}: not a table export RFEM wrote -- neither a folder of CSVs nor a workbook ({error})"
                ) from error

    def table(self, *aliases):
        if self.workbook is not None:
            return self.workbook.table(*aliases)
        for alias in aliases:
            key = fold(alias)
            for stem, file in self.files.items():
                if fold(stem) == key or fold(stem).endswith("_" + key) or key.startswith(fold(stem)):
                    try:
                        return read_table(file)
                    except RfemCsvError:
                        return None
        return None

    def names(self):
        return sorted(self.workbook.names) if self.workbook is not None else sorted(self.files)

    def close(self):
        if self.workbook is not None:
            self.workbook.close()

    def prefixed(self, prefix, *aliases):
        """The table whose name begins with `prefix` and goes on with one of `aliases` — how a load case's own load sheets are found, its id being the prefix RFEM localised."""
        key = fold(prefix)
        for name in self.names():
            folded = fold(name)
            if not folded.startswith(key):
                continue
            rest = folded[len(key):].strip("_")
            for alias in aliases:
                if rest.startswith(fold(alias)) or fold(alias).startswith(rest):
                    return self.table(name)
        return None


def _meta(table, row, where):
    comment = table.cell(row, *COLUMNS["comment"], default="")
    return parse_metadata(comment, where=where)


def _identifier(table, key):
    """The column that carries a table's own object identifier: the one an alias names, else **the first column**.

    ⚠️ The fallback is what makes this work in a language nobody read the export in, and it is a fact of the format rather than a guess: in every model table RFEM writes, the first column is the object's own number. What made it necessary is that **RFEM abbreviates exactly that header**, differently per language and not as the table is called — «Quersch. Nr.» where the sheet is «Querschnitte», «Last-\\nkombin.» where it is «Lastkombinationen», «Load Combs.» where it is «Load Combinations», «Comb.\\ncharges» in French. Chasing those abbreviations by alias lost the German sections and the German and English combinations outright, and would have lost the next language too.
    """
    return table.column(*COLUMNS[key]) or (table.columns[0] if table.columns else None)


def _rows(table, key, kind, skipped, problems):
    """The rows of a table that are objects: the number, the row, and the `where` a message names it by.

    ⚠️ This is where the empty numbered rows go. A row whose own number cannot be read is reported; one that has a number and nothing else is an object RFEM no longer holds and is counted in `skipped`, not reported — there are six of them in this model's node table and naming each would be noise.
    """
    found = []
    column = _identifier(table, key)
    for row in table.rows:
        no = _int(row.cells[column.index]) if column is not None and column.index < len(row.cells) else None
        if no is None:
            problems.append(engine.Note(
                "rfem_model_no_number",
                f"{table.name}: a row carries no {kind} number and is left out -- {row.cells[:3]}",
                where=table.name, kind=kind,
            ))
            continue
        if not any(_text(cell) for cell in row.cells[column.index + 1:]):
            skipped[kind] = skipped.get(kind, 0) + 1
            continue
        found.append((no, row, f"{kind[:1].upper()}{kind[1:]} {no}"))
    return found


def read_model(path):
    """The model one RFEM table export holds — an XLSX of every table, or a folder of one CSV per table.

    Every part is optional: a model with no surface, no hinge or no load is read without them, its table being absent or empty. A sheet this reader cannot find at all is an `engine.Note`, not a refusal, so an export missing one table still gives the rest.
    """
    source = _Source(path)
    problems, skipped = [], {}

    def table(kind):
        found = source.table(*SHEETS[kind])
        if found is None:
            problems.append(engine.Note(
                "rfem_model_no_table",
                f"{source.path}: no table of {kind} -- looked for {', '.join(f'«{a}»' for a in SHEETS[kind])}; "
                f"this export holds {', '.join(f'«{n}»' for n in source.names()[:8])}…",
                where=os.path.basename(source.path), kind=kind,
            ))
        return found

    # --- the geometry: member -> line -> nodes ----------------------------------------------------
    nodes = []
    node_table = table("nodes")
    if node_table is not None:
        for no, row, where in _rows(node_table, "node_no", "node", skipped, problems):
            nodes.append(Node(
                no,
                _length(node_table, row, "node_x", where=where, problems=problems),
                _length(node_table, row, "node_z", where=where, problems=problems),
                _meta(node_table, row, where),
            ))

    lines = {}
    line_table = table("lines")
    if line_table is not None:
        for no, row, where in _rows(line_table, "line_no", "line", skipped, problems):
            lines[no] = numbers(line_table.cell(row, *COLUMNS["line_nodes"]))

    members = []
    member_table = table("members")
    if member_table is not None:
        for no, row, where in _rows(member_table, "member_no", "member", skipped, problems):
            line = _int(member_table.cell(row, *COLUMNS["member_line"]))
            if line is not None and line not in lines:
                problems.append(engine.Note(
                    "rfem_model_no_line",
                    f"{where} is drawn on line {line}, which the line table does not hold -- it connects nothing",
                    where=where, line=line,
                ))
            members.append(Member(
                no, line, tuple(lines.get(line, ())),
                _text(member_table.cell(row, *COLUMNS["member_type"])),
                _int(member_table.cell(row, *COLUMNS["section_start"])),
                _int(member_table.cell(row, *COLUMNS["hinge_start"])),
                _int(member_table.cell(row, *COLUMNS["hinge_end"])),
                _length(member_table, row, "length", where=where, problems=problems),
                _meta(member_table, row, where),
            ))

    surfaces = []
    surface_table = source.table(*SHEETS["surfaces"])
    if surface_table is not None:
        for no, row, where in _rows(surface_table, "surface_no", "surface", skipped, problems):
            boundary = numbers(surface_table.cell(row, *COLUMNS["surface_lines"]))
            on = []
            for line in boundary:
                on.extend(lines.get(line, ()))
            surfaces.append(Surface(
                no, boundary, tuple(dict.fromkeys(on)),
                _length(surface_table, row, "surface_thickness", to="mm", where=where, problems=problems),
                _meta(surface_table, row, where),
            ))

    # --- what the members are made of -------------------------------------------------------------
    sections = []
    section_table = source.table(*SHEETS["sections"])
    if section_table is not None:
        for no, row, where in _rows(section_table, "cs_no", "section", skipped, problems):
            sections.append(Section(
                no,
                _text(section_table.cell(row, *COLUMNS["cs_name"])),
                _text(section_table.cell(row, *COLUMNS["cs_material"])),
                _length(section_table, row, "cs_b", to="mm", where=where, problems=problems),
                _length(section_table, row, "cs_h", to="mm", where=where, problems=problems),
                numbers(section_table.cell(row, *COLUMNS["cs_members"])),
                _meta(section_table, row, where),
            ))

    materials = []
    material_table = source.table(*SHEETS["materials"])
    if material_table is not None:
        for no, row, where in _rows(material_table, "material_no", "material", skipped, problems):
            materials.append(Material(no, _text(material_table.cell(row, *COLUMNS["material_name"])),
                                      _meta(material_table, row, where)))

    # --- how it is held ---------------------------------------------------------------------------
    def restraints(kind, role, key, nodes_key=None):
        found, restraint_table = [], source.table(*SHEETS[kind])
        if restraint_table is None:
            return found
        for no, row, where in _rows(restraint_table, key, kind[:-1] if kind.endswith("s") else kind, skipped, problems):
            found.append(Restraint(
                no, role,
                numbers(restraint_table.cell(row, *COLUMNS[nodes_key])) if nodes_key else (),
                number(_text(restraint_table.cell(row, *COLUMNS["spring_x"]))),
                number(_text(restraint_table.cell(row, *COLUMNS["spring_z"]))),
                number(_text(restraint_table.cell(row, *COLUMNS["spring_phi"]))),
                _meta(restraint_table, row, where),
            ))
        return found

    supports = restraints("supports", "support", "support_no", "support_nodes")
    hinges = restraints("hinges", "hinge", "hinge_no")

    # --- the loadings -----------------------------------------------------------------------------
    cases = []
    case_table = table("cases")
    if case_table is not None:
        column = _identifier(case_table, "case_no")
        for row in case_table.rows:
            case_id = _text(row.cells[column.index]) if column is not None and column.index < len(row.cells) else ""
            if not case_id:
                continue
            where = f"Load case {case_id}"
            cases.append(Case(
                case_id,
                _text(case_table.cell(row, *COLUMNS["case_name"])),
                _text(case_table.cell(row, *COLUMNS["case_category"])),
                _text(case_table.cell(row, *COLUMNS["case_duration"])),
                _meta(case_table, row, where),
            ))

    combinations = []
    combination_table = table("combinations")
    if combination_table is not None:
        # ⚠️ The factored cases are pairs of columns named «Facteur» and «n°», one pair per term, and their *group* is the localised «CC.1», «CC.2». So the pairs are found by the word for «Factor» and each is read with the column beside it, which needs one word rather than six.
        pairs = [column.index for column in combination_table.columns
                 if fold(column.name) in {fold(alias) for alias in COLUMNS["factor"]}]
        column = _identifier(combination_table, "combination_no")
        for row in combination_table.rows:
            combination_id = _text(row.cells[column.index]) if column is not None and column.index < len(row.cells) else ""
            if not combination_id:
                continue
            terms = []
            for index in pairs:
                factor = number(_text(row.cells[index])) if index < len(row.cells) else None
                case_id = _text(row.cells[index + 1]) if index + 1 < len(row.cells) else ""
                if factor is not None and case_id:
                    terms.append((factor, case_id))
            combinations.append(Combination(
                combination_id,
                _text(combination_table.cell(row, *COLUMNS["name"])),
                _text(combination_table.cell(row, *COLUMNS["combination_situation"])),
                _text(combination_table.cell(row, *COLUMNS["case_duration"])),
                terms,
                _meta(combination_table, row, f"Combination {combination_id}"),
            ))

    loads = []
    for case in cases:
        for kind, aliases in LOAD_SHEETS.items():
            load_table = source.prefixed(case.id + " - ", *aliases)
            if load_table is None:
                continue
            on_members = load_table.column(*COLUMNS["load_members"])
            on_nodes = load_table.column(*COLUMNS["load_nodes"])
            column = _identifier(load_table, "load_no")
            magnitude = next((c for c in load_table.columns if c.unit and c.index > (on_members or on_nodes or column).index), None)
            for row in load_table.rows:
                no = _int(row.cells[column.index]) if column.index < len(row.cells) else None
                if no is None:
                    continue
                where = f"{case.id} {kind.replace('_', ' ')} {no}"
                loads.append(Load(
                    no, kind, case.id,
                    numbers(row.cells[on_members.index]) if on_members is not None and on_members.index < len(row.cells) else [],
                    numbers(row.cells[on_nodes.index]) if on_nodes is not None and on_nodes.index < len(row.cells) else [],
                    _text(load_table.cell(row, *COLUMNS["load_type"])),
                    _text(load_table.cell(row, *COLUMNS["load_distribution"])),
                    _text(load_table.cell(row, *COLUMNS["load_direction"])),
                    number(_text(row.cells[magnitude.index])) if magnitude is not None and magnitude.index < len(row.cells) else None,
                    magnitude.unit if magnitude is not None else None,
                    _meta(load_table, row, where),
                ))

    for part in (nodes, members, surfaces, sections, materials, supports, hinges, cases, combinations, loads):
        for record in part:
            problems.extend(record.meta.problems)

    # The workbook is held open while its sheets are read one at a time, so it is let go here rather than left on a file handle for as long as the model lives.
    source.close()
    return Model(
        source.path, nodes=nodes, lines=lines, members=members, surfaces=surfaces,
        sections=sections, materials=materials, supports=supports, hinges=hinges,
        cases=cases, combinations=combinations, loads=loads, skipped=skipped, problems=problems,
    )
