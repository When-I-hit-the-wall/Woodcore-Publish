"""Connectors (Verbindungsmittel): one source file each, written by Woodcore, calculated here (docs/domain/connectors.md §3.3nonies).

Until v0.68 a connector was a row of `Positionen.xlsx`'s `Positions Connectors` sheet and `calc/connectors.py` read it. It is now a file of its own, `000-Python/connectors/<id>.json`, written by Woodcore's «Connecteurs» tab and read by this module alone -- the arrangement of `connections/`, `plans/` and `statics/`, for the same reasons (section 13). **One connector is one file is one calculation**: to compare two layouts, duplicate the connector, which is what the engineer already did in Excel.

The record keeps two halves. The **descriptive** one is what the sheet carried and what `show-connector` prints -- type, assembly, diameter, length, dimension, steel, predrilling, elements -- and it is exported under exactly the keys schema 1.0 used, so `connector-summary` in `lib/calc-engine.typ` and `build_reference`'s Connectors sheet did not have to change for the move. The **calculation** half is the ordinary `{vars, steps, checks, tables, results}` of section 2 rule 2, read under the domain `connector`.

**A member's timber is a reference, resolved afresh at every export.** The member names an element of the schema, the element names a position, and the position gives `strength_class` and `moisture_class`; `material` is `null` (follow it) or `{"grade": "GL32h"}` (written over, and staying so). The static model's magnitude pattern (section 3.3octies), and for the same reason: the connector follows `Positionen.xlsx` by itself, so *Import données* is all it takes and there is no «Reprendre» button to forget to press.

**What warns and what stops.** A reference that no longer resolves, a type with no calculation module, a dowel pattern below the minimum spacings of Tabelle 24: each is a **warning**, the connector is still exported with its descriptive half, and the report refuses to print what could not be calculated. That is the v0.33 rule -- stopping would stop the positions' own export with it and leave Woodcore nothing to relink to. Anything that would produce a *wrong number* stops: an unknown type or assembly, a configuration SIA 265 gives no k_beta for, hardwood that is not predrilled, a missing thickness, a fastener count that contradicts the drawing.
"""

import copy
import json
import math
import re
from pathlib import Path

import validation
from domains import dowel
from domains import links  # a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
from norms import sia263, sia265, sn_en_14592

DOMAIN = "connector"
LABEL = "Verbindungsmittel"
ENGINE = "python"
SOURCE = "python:domains/connector.py"

SOURCE_SCHEMA_VERSION = "2.0"
# 2.1 is 2.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a connector following no variable is saved and exported as before
LINKED_SCHEMA_VERSION = "2.1"
# 2.2 is 2.1 with `plate`, the steel plate's thickness, end and edge distances and hole (spec 2026-10-12-audit-issues-47-48-49, D-14): written only by a Stahl-Holz connector that states one -- a superset of 2.1, so a plate may sit beside links. The versions are floors: links need 2.1 at least, a plate 2.2
PLATE_SCHEMA_VERSION = "2.2"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION, PLATE_SCHEMA_VERSION)
# The four lengths of the plate's bearing, SIA 263 Tabelle 16 (76): each {value, unit} in mm, or null while not stated
PLATE_FIELDS = ("t", "e1", "e2", "d0")
EXPORT_SCHEMA_VERSION = "3.0"
LINKED_EXPORT_VERSION = "3.1"

# The fields a variable of the export may fill (REQ-009, issue #42), with the unit each is written in: the connector's own -- the diameter, the dowel's f_u,k, the plate's four lengths (spec 2026-10-12-audit-issues-47-48-49) -- and each member's -- its angle, its thickness (a steel plate's b where the joint is Stahl-Holz), its spacing, its slot and its t₁/t₂. The kinds, the grades, the moisture class, the counts are lists or whole numbers, and take none.
LINKABLE = {
    links.SELF: {"diameter": "mm", "dowel.f_u_k": "N/mm²", "plate.t": "mm", "plate.e1": "mm", "plate.e2": "mm", "plate.d0": "mm"},
    "members": {"alpha": "°", "t": "mm", "a_1": "mm", "plates.slot": "mm", "plates.ratio": ""},
}

# What calc/tools/migrate_to_schemas.py converts, and this module deliberately does not: a source at one of these carries its own drawing, and turning that drawing into a schema means writing a second file, which a reader has no business doing silently.
LEGACY_SOURCE_VERSIONS = ("1.0", "1.1")

# The file data/connectors.json is written to.
EXPORT_FILE = "connectors.json"

# A connector id is the file name of its source and the string the report addresses it by, so it is kept to characters safe in both. The same pattern serves a schema's id, which is a file name too.
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

# The id of an element or a connector marker of the schema this connector is drawn on -- schema.ENTITY_ID, restated here rather than imported, since `schema` reads this module for TYPES and is taken lazily (see `figures`). tests/test_constants.py holds the two equal, as it already does for the kinds of fastener.
ENTITY_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

# The kinds of fastener, with the symbol an id of that kind starts with. This was `data_connector` in Positionen.xlsx; the sheet is retired, so the list lives here, which is now its only home.
TYPES = {
    "Stabdübel": "SD",
    "Passbolzen": "PB",
    "Bolzen": "B",
    "Vollgewindeschraube": "VGS",
    "Teilgewindeschraube": "TGS",
    "Nagel": "N",
    "Klammer": "K",
    "eingeklebte Gewindestange": "GS",
    "Dübel besonderer Bauart": "DB",
}

# Which module calculates which kind. A type with no entry is described and not calculated: the connector is exported, `calculated` is false, and the report says so rather than printing a number nobody produced.
MODULES = {dowel.TYPE: dowel}

# Every assembly the interface may offer, and whether SIA 265 gives it a k_beta. This was `data_assembly`.
ASSEMBLIES = dict(dowel.ASSEMBLIES)
UNCOVERED_ASSEMBLIES = dict(dowel.UNCOVERED_ASSEMBLIES)
ALL_ASSEMBLIES = tuple(list(ASSEMBLIES) + list(UNCOVERED_ASSEMBLIES))

ROLES = ("timber", "steel")
PLATE_ARRANGEMENTS = ("schlitzblech", "laschen")
VIEWS = ("h", "b")
MIN_MEMBERS, MAX_MEMBERS = 2, 6

# The block of a source that belongs to its kind of fastener. Exactly the one the type names must be present, and no other: that is what lets a second type add a block instead of widening the file.
TYPE_BLOCK = {"Stabdübel": "dowel"}

# Two fasteners closer than this (mm) are one point typed twice.
SAME_POINT = 1e-6

# Where a connector's drawings are written, under data/.
FIGURE_DIR = "connectors"

# The languages a figure is drawn in. The **pattern** carries no legend, only data and, where a fastener is drawn larger than its d, one translated note; it is drawn once per language all the same, as a connection's figure is (docs/typst/language.md §4bis). The **section** carries only symbols (t_1, t_2, A, B, Ø) and numbers, so one file serves all three and the report falls back to it.
FIGURE_LANGUAGES = ("de", "fr", "en")


def _fail(where, message):
    raise validation.ValidationError("%s: %s" % (where, message))


def _quantity(entry, where, label, required=True):
    """A {value, unit} block as a number, or None."""
    if entry is None:
        if required:
            _fail(where, "%s is missing" % label)
        return None
    if not isinstance(entry, dict) or "value" not in entry:
        _fail(where, "%s must be a {value, unit} block, got %r" % (label, entry))
    value = entry["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(where, "%s is %r -- expected a number" % (label, value))
    return value


# --- the source ---------------------------------------------------------------

def source_paths(source_dir):
    """Every connector source in `source_dir`, in file-name order."""
    directory = Path(source_dir)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"))


def material_kind(material):
    """What a member's `material` says, in one word.

    "element"   -- null: the strength class FOLLOWS the member's element, and so its position, resolved afresh at every export
    "override"  -- {"grade": "GL24h"}: a class stated here, which wins over the element's and STAYS through the next import
    "invalid"   -- anything else

    ⚠️ Two shapes since schema 2.0, where there were three. The element is the position reference now
    (`connector-source.schema.json`), so "position" and "explicit" have collapsed into "element": there is
    one place a position is named, and `material` says only whether the class read from it is overridden.
    What did NOT change is why an override is its own state -- the engineer asked that an overridden value
    stay overridden through the next *Import données*, and that the field still say what the position holds
    so the difference can be seen and taken back (docs/decisions.md §13, v0.70).
    """
    if material is None:
        return "element"
    if not isinstance(material, dict):
        return "invalid"
    if material.get("position") is not None:
        return "invalid"
    return "override" if material.get("grade") else "invalid"


def member_position(member, detail):
    """The position a member's element names, or "" -- the one way a member reaches `Positionen.xlsx` since schema 2.0."""
    from domains import schema as schema_model   # lazy: schema reads this module for TYPES (see `figures`)
    eid = (member or {}).get("element", "")
    if not eid:
        return ""
    element = schema_model.entry_of(detail or {}, "elements", eid)
    return (element or {}).get("position", "") or ""


def upgrade_source(source):
    """A 1.0 source read as 1.1: the per-member moisture classes collapse into the connection's own.

    Until v0.69 each member carried a `moisture_class` inside its `material` and `analyse` took the worst of them. SIA 265 applies **one** eta_w to R_d,Verb, and the classeur states one class per sheet (`'Stabdübel (Holz-Holz)'!C13`, `'Stabdübel (Stahl-Holz)'!C35`), so there is one here too. The worst of a 1.0 file's classes is what its own calculation used, so this conversion changes no number (docs/domain/connectors.md §3.3nonies).
    """
    if not isinstance(source, dict) or source.get("schema_version") != "1.0":
        return source
    source = copy.deepcopy(source)
    classes = []
    for member in source.get("members") or []:
        material = member.get("material")
        if isinstance(material, dict) and material.get("moisture_class") is not None:
            classes.append(material.pop("moisture_class"))
        elif isinstance(material, dict):
            material.pop("moisture_class", None)
    source["moisture_class"] = max(classes) if classes else None
    source.setdefault("name", source.get("label", "") or source.get("id", ""))
    source.setdefault("variant", "")
    for member in source.get("members") or []:
        plates = member.get("plates")
        if isinstance(plates, dict):
            plates.pop("thickness", None)   # never read: the plate's bearing reads the connector's `plate.t` (schema 2.2)
    # 1.1 and not 2.0: a 1.0 file still carries its own drawing, and check_source sends a 1.1 to migrate_to_schemas.py by name. Relabelled 2.0, a real 1.0 slipped past that refusal and fell on «missing required field 'label'» (periodic audit 260916, AUD-7-120).
    source["schema_version"] = "1.1"
    return source


def check_source(source, where):
    """Everything the schema cannot say. Blocking, naming the file and the field."""
    # ⚠️ The version FIRST, before the structure: a source that still carries its own drawing fails the
    # 2.0 schema on a dozen fields at once, and the message that matters -- run the migration, once -- would
    # be buried under whichever of them the validator happened to reach first.
    version = source.get("schema_version") if isinstance(source, dict) else None
    if version in LEGACY_SOURCE_VERSIONS:
        _fail(where, "schema_version is %r -- it carries its own drawing; run `python calc/tools/migrate_to_schemas.py --write` once, which writes that drawing out as a schema under details/ and leaves this file naming it" % version)
    validation.validate_structure(source, "connector-source")
    if version not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version is %r -- expected %s"
              % (version, " or ".join(repr(v) for v in SOURCE_SCHEMA_VERSIONS)))
    if links.is_linked(source, LINKABLE) and version not in (LINKED_SCHEMA_VERSION, PLATE_SCHEMA_VERSION):
        _fail(where, "follows a variable at schema_version %r -- a connector with links is %r or %r" % (version, LINKED_SCHEMA_VERSION, PLATE_SCHEMA_VERSION))
    if source.get("plate") is not None:
        if version != PLATE_SCHEMA_VERSION:
            _fail(where, "carries a `plate` at schema_version %r -- a connector with a plate is %r" % (version, PLATE_SCHEMA_VERSION))
        for key in PLATE_FIELDS:
            if source["plate"].get(key) is not None and _quantity(source["plate"][key], where, "plate." + key) <= 0:
                _fail(where, "plate.%s = %s mm -- expected a positive length, or null while not stated" % (key, source["plate"][key]["value"]))
        d0, d = source["plate"].get("d0"), source.get("diameter") or {}
        if d0 is not None and d.get("value") and d0["value"] < d["value"]:
            _fail(where, "plate.d0 = %s mm is smaller than the dowel's diameter %s mm" % (d0["value"], d["value"]))
    links.check_all(source, LINKABLE, lambda message: _fail(where, message), "the connector", links.JOINTS)

    moisture = source.get("moisture_class")
    if moisture is not None and moisture not in validation.moisture_classes():
        _fail(where, "moisture class %r -- expected %s, or null to take it from the members' positions"
              % (moisture, ", ".join(str(c) for c in validation.moisture_classes())))

    cid = source.get("id", "")
    if not ID_PATTERN.match(cid or ""):
        _fail(where, "id %r -- letters, digits and _ . + - only, starting with a letter or digit" % cid)

    kind = source.get("type")
    if kind not in TYPES:
        _fail(where, "type %r -- the kinds of fastener are %s" % (kind, ", ".join(sorted(TYPES))))

    assembly = source.get("assembly")
    if assembly in UNCOVERED_ASSEMBLIES:
        _fail(where, "%r: %s Der Tragwiderstand ist nach SIA 265 6.1.1.11 versuchsmässig zu bestimmen."
              % (assembly, UNCOVERED_ASSEMBLIES[assembly]))
    if assembly not in ASSEMBLIES:
        _fail(where, "assembly %r -- SIA 265 Tabellen 45 und 46 give %s"
              % (assembly, ", ".join(sorted(ASSEMBLIES))))

    _quantity(source.get("diameter"), where, "diameter")
    _quantity(source.get("length"), where, "length", required=False)

    block = TYPE_BLOCK.get(kind)
    for name in set(TYPE_BLOCK.values()):
        present = source.get(name) is not None
        if name == block and not present:
            _fail(where, "type %r needs its own '%s' block" % (kind, name))
        if name != block and present:
            _fail(where, "carries a '%s' block, which belongs to another kind of fastener" % name)
    if block == "dowel":
        _quantity(source["dowel"].get("f_u_k"), where, "dowel.f_u_k")
        grade = source["dowel"].get("steel") or ""
        if grade and grade not in sia263.grades() and grade not in sia263.bolt_classes():
            _fail(where, "dowel.steel %r -- a grade of SIA 263 Tabelle 1 (%s), a class of Tabelle 2, or empty for a value typed with no table behind it"
                  % (grade, ", ".join(sia263.grades())))

    members = source.get("members") or []
    if not MIN_MEMBERS <= len(members) <= MAX_MEMBERS:
        _fail(where, "%d member(s) -- between %d and %d meet at a node" % (len(members), MIN_MEMBERS, MAX_MEMBERS))

    sid = source.get("schema", "")
    if not isinstance(sid, str):
        _fail(where, "schema %r -- expected the name of a file of details/" % (sid,))
    if sid and not ID_PATTERN.match(sid):
        _fail(where, "schema %r is not a schema id" % sid)

    timber = 0
    for index, member in enumerate(members, start=1):
        spot = "%s, member %d" % (where, index)
        if member.get("role") not in ROLES:
            _fail(spot, "role %r -- expected %s" % (member.get("role"), " or ".join(ROLES)))
        element = member.get("element")
        if not isinstance(element, str):
            _fail(spot, "element %r -- expected the id of an element of schema %s" % (element, sid or "(none named)"))
        if element and not ENTITY_ID.match(element):
            _fail(spot, "element %r is not an element id" % element)
        if member["role"] != "timber":
            continue
        timber += 1
        if isinstance(member.get("material"), dict) and member["material"].get("position") is not None:
            _fail(spot, "material names a position -- since schema 2.0 the member's element does, and naming one here as well would be a second place for the same fact")
        kind_of = material_kind(member.get("material"))
        if kind_of not in ("element", "override"):
            _fail(spot, "material must be null -- the strength class then follows the element's position -- or {\"grade\": ...}, which overrides it; got %r"
                  % (member.get("material"),))
        if isinstance(member.get("material"), dict) and member["material"].get("moisture_class") is not None:
            _fail(spot, "material carries a moisture class -- since schema 1.1 the connection has one, at the top of the source")
        if member.get("predrilled") is None:
            _fail(spot, "predrilled must be true or false for a timber member (SIA 265 Tabelle 22 gives a row per species and predrilling)")
        alpha = member.get("alpha")
        if alpha is None or not 0 <= alpha <= 90:
            _fail(spot, "alpha %r -- the angle between force and grain is folded into 0 to 90 degrees" % alpha)
        thickness = _quantity(member.get("t"), spot, "t")
        if thickness <= 0:
            _fail(spot, "t = %s mm -- expected a positive thickness" % thickness)
        n = member.get("n")
        if not isinstance(n, int) or n < 1:
            _fail(spot, "n = %r -- a row holds at least one fastener" % n)
        if n > 1:
            spacing = _quantity(member.get("a_1"), spot, "a_1")
            if spacing <= 0:
                _fail(spot, "a_1 = %s mm -- expected a positive spacing" % spacing)
        plates = member.get("plates")
        if plates is not None:
            if plates.get("arrangement") not in PLATE_ARRANGEMENTS:
                _fail(spot, "plates.arrangement %r -- expected %s"
                      % (plates.get("arrangement"), " or ".join(PLATE_ARRANGEMENTS)))
            count = plates.get("count")
            if not isinstance(count, int) or count < 1:
                _fail(spot, "plates.count = %r -- at least one plate" % count)
            _quantity(plates.get("slot"), spot, "plates.slot")
            # `plates.thickness` was here until schema 1.1 and nothing ever read it. The plate's bearing
            # check came with schema 2.2 (SIA 263 Tabelle 16, D-14), and reads the connector's one `plate`:
            # the same plate for every member, so its thickness is said once, there, and not per member.
            if plates.get("thickness") is not None:
                _fail(spot, "plates.thickness is not read -- the plate's thickness for its Lochleibung check (SIA 263 Tabelle 16) is the connector's plate.t, schema 2.2")

    needed = ASSEMBLIES[assembly]["members"]
    if timber < needed:
        _fail(where, "assembly %r needs %d timber member(s), %d given" % (assembly, needed, timber))
    if ASSEMBLIES[assembly]["family"] == "steel-timber":
        if not any(m.get("plates") for m in members if m.get("role") == "timber"):
            _fail(where, "assembly %r needs a timber member carrying its `plates` block" % assembly)

    # ⚠️ An EMPTY list is NOT a defect since schema 2.0. The coordinates are the schema's, so «no
    # marker ticked» is a state of the drawing and not of this file -- exactly as «no schema named» is --
    # and `build_record` says so with `calculated: false` and its reason. Refusing it here would make
    # «Nouveau» open on an error, which is what v0.70 fixed and what this rule would undo.
    fasteners = source.get("fasteners") or []
    seen_markers = []
    for i, marker in enumerate(fasteners, start=1):
        if not isinstance(marker, str) or not marker:
            _fail(where, "fastener %d is %r -- expected the id of a connector marker of the schema" % (i, marker))
        if not ENTITY_ID.match(marker):
            _fail(where, "fastener %d: %r is not a marker id" % (i, marker))
        if marker in seen_markers:
            _fail(where, "fastener %d: marker %s is named twice" % (i, marker))
        seen_markers.append(marker)

    total = source.get("n_tot") or {}
    value = total.get("value")
    if not isinstance(value, int) or value < 1:
        _fail(where, "n_tot = %r -- a connector holds at least one fastener" % value)
    # ... and only where the drawing HAS a pattern: with no marker ticked there is nothing for n_tot to
    # disagree with, and a fresh connector would otherwise open on a refusal.
    if fasteners and not total.get("override") and value != len(fasteners):
        _fail(where, "n_tot is %d and the drawing has %d fastener(s) -- set n_tot's override to say so deliberately"
              % (value, len(fasteners)))
    return source


def read_source(path):
    """One connector source, checked, and required to carry the id its file is named after."""
    p = Path(path)
    try:
        source = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(p.name, "is not valid JSON: %s" % exc)
    if source.get("id") != p.stem:
        _fail(p.name, "carries id %r -- a connector's id is its file name" % source.get("id"))
    return check_source(upgrade_source(source), p.name)


def new_source(cid, kind=dowel.TYPE, schema=""):
    """An empty connector, as Woodcore's «Nouveau» starts one -- naming a schema where one is given, and no fastener yet: the markers are ticked off the schema's own drawing."""
    block = TYPE_BLOCK.get(kind)
    source = {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "id": cid,
        "group": "",
        "name": "",
        "variant": "",
        "type": kind,
        "assembly": "Holz-Holz zweischnittig",
        "label": "",
        "description": "",
        "diameter": {"value": 12, "unit": "mm"},
        "length": None,
        "dimension": "",
        # A Holz-Holz joint has no plate, so no plate grade (v0.77)
        "steel": "",
        "elements": [],
        # A new connector STATES class 1 -- the commonest, and the classeur's own default -- so that
        # «Nouveau» opens on something that calculates rather than on a refusal. Setting it to «—» is
        # then a deliberate choice to follow the members' positions instead, the worst governing.
        "moisture_class": 1,
        "conditions": {"seismic": False, "truss": False},
        "n_tot": {"value": 1, "override": False},
        "schema": schema or "",
        "members": [_new_member(), _new_member()],
        "fasteners": [],
    }
    if block == "dowel":
        source["dowel"] = new_dowel()
    return source


def new_dowel(grade=None):
    """A Stabdübel block of `grade` (SN EN 14592's default, S355, when None): the grade and the f_u,k SIA 263 Tabelle 1 gives it -- read from calc/norms/, never written here. The grade only fills the value: f_u,k is what SIA 265 reads, and it stays writable (spec 2026-10-12-audit-issues-47-48-49, D-06, D-20)."""
    grade = grade or sn_en_14592.default_steel()
    return {"steel": grade, "f_u_k": {"value": sn_en_14592.f_u_k(grade), "unit": "N/mm²"}}


def dowel_steel(source):
    """The grade a Stabdübel's f_u,k is credited to, or "": a grade of SIA 263 Tabelle 1 a dowel may be made of, whose f_u is the value the block holds and which no variable fills. A grade beside another value is a label, as schema 2.0 had it, and the value is the engineer's own."""
    block = source.get("dowel") or {}
    grade = block.get("steel") or ""
    if grade not in sn_en_14592.dowel_grades() or "dowel.f_u_k" in (source.get("links") or {}):
        return ""
    return grade if abs((block.get("f_u_k") or {}).get("value", 0) - sn_en_14592.f_u_k(grade)) < 1e-9 else ""


def _new_member(element=""):
    member = {
        "name": "",
        "element": element,
        "role": "timber",
        "material": {"grade": "C24"},
        "predrilled": True,
        "alpha": 0,
        "t": {"value": 100, "unit": "mm"},
        "n": 1,
        "a_1": None,
        "plates": None,
    }
    return member


# --- resolving a member's timber against the positions -------------------------

def strength_class_of(record):
    """A position record's strength class (C24, GL24h, S355): its `strength_class`, the sheet's `resistance class` column. A record exported before that column existed carries none, and its `material` then IS the strength class -- which is what `material` held until the engineer split the two -- so it is read instead. A record that has the key and leaves it blank has no strength class; its material (Fichte) is never taken for one."""
    record = record or {}
    if "strength_class" in record:
        return (record.get("strength_class") or "").strip()
    return (record.get("material") or "").strip()


def position_dimension(record):
    """A position record's section as Woodcore's summaries print it -- «100/200 mm», «Ø 200 mm», «ROR 101.6×10» -- and where it has none, its dimension with its unit, «180» where no unit is typed; "" where the sheet states no dimension: facultative since v0.87, and its unit only qualifies it, so a unit left in the sheet beside a blank dimension is not printed on its own. The text is domains/section.py's, the one reader of a position's dimension (v0.94). (Not schema's or statics' `dimension_text`, which is what a drawn dimension writes.)"""
    from domains import section
    return section.display(record)


def known_positions(data_dir):
    """{id: {"material", "strength_class", "moisture_class", "type", "dimension", "units", "section"}} from the exported position records, or {} where nothing is exported yet -- the one reader of them Woodcore's tabs share. `section` (v0.94) is what a detail schema's element reads its b/h and its label off, and what the summaries print; a record exported before it carries none, and domains/section.py reads its `dimension` and `units` instead. `strength_class` is what a connector's timber is."""
    index = Path(data_dir) / "positions-index.json"
    if not index.is_file():
        return {}
    ids = json.loads(index.read_text(encoding="utf-8")).get("positions", [])
    out = {}
    for pid in ids:
        path = Path(data_dir) / "positions" / ("%s.json" % pid)
        if not path.is_file():
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        out[pid] = {"material": record.get("material", ""), "strength_class": strength_class_of(record),
                    "moisture_class": record.get("moisture_class"),
                    "type": record.get("type", ""), "dimension": record.get("dimension", ""),
                    "units": record.get("units", ""), **({"section": record["section"]} if "section" in record else {})}
    return out


def position_material(member, positions, detail=None):
    """What the position of the member's element says today: (grade, moisture class), or (None, None) where the element names none, or the schema or the position is gone.

    Read by Woodcore to say, beside an overridden field, what `Positionen.xlsx` holds -- which is what makes the orange line under an overridden value mean something and the «Reprendre» button possible.
    """
    pid = member_position(member, detail)
    if not pid or pid not in positions:
        return None, None
    return strength_class_of(positions[pid]), positions[pid].get("moisture_class")


def resolve_member(member, index, positions, where, moisture=None, detail=None):
    """One timber member's grade, density and species, with where each came from.

    Returns (resolved, warnings). A reference that no longer resolves, or a position that carries no
    strength class, leaves `resolved` incomplete and says so -- never raises, so the connector is still
    exported and Woodcore still has something to relink (the v0.33 rule).

    `moisture` is the **connection's** class, resolved once by the caller: SIA 265 applies one eta_w to
    R_d,Verb, and the classeur states one per sheet. It is carried on every member all the same, because
    that is the shape `dowel.analyse` reads and the Typst side prints.
    """
    warnings = []
    kind = material_kind(member.get("material"))
    grade, provenance = "", ""
    stated = (member.get("material") or {}).get("grade") or ""
    pid, held = member_position(member, detail), ""

    if pid:
        if pid not in positions:
            # Composed in the source language and translated where it is shown: the hole carries the
            # NUMBER, not «Bauteil 2», because a capture is data and is re-emitted untranslated (section 4bis).
            warnings.append("%s: Bauteil %d verweist auf Position %s, die das Register Positionen nicht mehr führt. "
                            "Wählen Sie ein Element des Schemas, dessen Position eine Festigkeitsklasse trägt, oder geben Sie die Festigkeitsklasse von Hand ein."
                            % (where, index, pid))
            grade = stated
            provenance = ("%s, im Verbindungsmittel festgelegt" % grade) if grade else ""
        elif kind == "override":
            grade = stated
            held = strength_class_of(positions[pid])
            provenance = "%s, im Verbindungsmittel festgelegt (Position %s: %s)" % (
                grade, pid, held or "ohne Festigkeitsklasse")
        else:
            grade = held = strength_class_of(positions[pid])
            provenance = "%s, aus Position %s" % (grade or "ohne Festigkeitsklasse", pid)
            if not grade:
                warnings.append("%s: Bauteil %d verweist auf Position %s, die keine Festigkeitsklasse trägt. "
                                "Wählen Sie ein Element des Schemas, dessen Position eine Festigkeitsklasse trägt, oder geben Sie die Festigkeitsklasse von Hand ein."
                                % (where, index, pid))
    else:
        # The element names no position -- a piece drawn without one, or an element the schema has lost.
        # An overridden class still calculates; nothing at all is a warning and an incomplete record.
        grade = stated
        provenance = ("%s, im Verbindungsmittel festgelegt" % grade) if grade else ""
        if not grade:
            warnings.append("%s: Bauteil %d ist keinem Element mit Position zugeordnet und trägt keine "
                            "Festigkeitsklasse. Wählen Sie ein Element des Schemas oder geben Sie die "
                            "Festigkeitsklasse von Hand ein." % (where, index))

    resolved = {
        "grade": grade,
        "moisture_class": moisture,
        "provenance": provenance,
        # What the provenance says, in parts, so that Woodcore can write the orange line under an
        # overridden field in its OWN language and offer «Reprendre». `provenance` stays the German
        # one-liner the report prints; a sentence with an id inside it is not a glossary key (section 4bis).
        "source_kind": kind,
        "position_id": pid,
        "position_grade": held,
        "alpha": member.get("alpha"),
        "t": _quantity(member.get("t"), where, "t", required=False),
        "predrilled": member.get("predrilled"),
        "n": member.get("n"),
        "a_1": _quantity(member.get("a_1"), where, "a_1", required=False),
        "plates": member.get("plates"),
    }

    if grade:
        try:
            resolved["rho_k"] = sia265.rho_k(grade)
            resolved["species"] = sia265.species(grade)
            resolved["table"] = "Tabelle 8" if sia265.grade(grade)["family"] == "Vollholz" else "Tabelle 9"
            resolved["norm_ref"] = "3.3.2.1" if resolved["table"] == "Tabelle 8" else "3.4.2.2"
        except validation.ValidationError as exc:
            warnings.append("%s: Bauteil %d -- %s" % (where, index, exc))
    return resolved, warnings


# --- the record ----------------------------------------------------------------

def resolve_moisture(source, positions, detail=None):
    """The connection's moisture class, and where it came from: (class, provenance, warnings).

    One per connection since schema 1.1: SIA 265 applies a single eta_w to R_d,Verb (Tabelle 4), and the classeur states one class per sheet. Stated in the source it wins; left null it is taken from the members' positions, **the worst governing** -- class 3 is the wettest and carries the smallest eta_w, so the worst is the safe reading of a connection whose two pieces sit in different ambiences.
    """
    warnings = []
    stated = source.get("moisture_class")
    found, seen = [], []
    for index, member in enumerate(source.get("members") or [], start=1):
        if member.get("role") != "timber":
            continue
        pid = member_position(member, detail)
        _grade, moisture = position_material(member, positions, detail)
        if moisture is not None:
            found.append(moisture)
            seen.append((index, pid, moisture))

    if stated is not None:
        held = sorted({m for _i, _p, m in seen})
        if held and held != [stated]:
            provenance = "Feuchteklasse %d, im Verbindungsmittel festgelegt (Positionen: %s)" % (
                stated, ", ".join("%s → %d" % (p, m) for _i, p, m in seen))
        else:
            provenance = "Feuchteklasse %d, im Verbindungsmittel festgelegt" % stated
        return stated, provenance, warnings

    if not found:
        return None, "", warnings
    worst = max(found)
    if len(set(found)) > 1:
        warnings.append(
            "Die Bauteile sind verschiedenen Feuchteklassen zugeordnet (%s); massgebend ist die ungünstigste, Klasse %d."
            % (", ".join(str(c) for c in sorted(set(found))), worst))
    named, sources = set(), []
    for _index, pid, m in seen:          # two members on one position name it once
        if m == worst and pid not in named:
            named.add(pid)
            sources.append(pid)
    return worst, "Feuchteklasse %d, aus Position %s" % (worst, ", ".join(sources)), warnings


def _predrilled(members):
    """The descriptive Ja/Nein of the whole connector: true when every timber member is predrilled, false when none is, null when they differ. Derived, so that show-connector keeps printing its word without the fact living twice."""
    values = [m.get("predrilled") for m in members if m.get("role") == "timber"]
    if not values or any(v is None for v in values):
        return None
    if all(values):
        return True
    if not any(values):
        return False
    return None


def _descriptive(source):
    """The half the retired sheet carried, under exactly the keys schema 1.0 used."""
    return {
        "position": source["id"],
        "type": source["type"],
        "assembly": source["assembly"],
        "diameter": source["diameter"],
        "length": source.get("length"),
        "dimension": source.get("dimension", ""),
        "steel": source.get("steel", ""),
        "predrilled": _predrilled(source["members"]),
        "elements": list(source.get("elements") or []),
        "description": source.get("description", ""),
        # The folder Woodcore files it in: a field of the source, never a directory, so the id stays the file name (grouped_list.py). Exported so that a reader -- the polar moments tab today, a grouped listing in the report one day -- need not open the source.
        "group": (source.get("group") or "").strip(),
    }


def _member_record(member, index, resolved, detail=None):
    """One member as the report and Woodcore read it. Its section, its angle and how it is cut are gone with the member form (schema 2.0): the piece is the schema's element, and `element`/`position` are how the report names it."""
    record = {
        "name": member.get("name", ""),
        "element": member.get("element", ""),
        "position": member_position(member, detail),
        "role": member["role"],
    }
    if resolved is not None:
        record.update({
            "grade": resolved.get("grade", ""),
            "moisture_class": resolved.get("moisture_class"),
            "species": resolved.get("species", ""),
            "predrilled": resolved.get("predrilled"),
            "alpha": resolved.get("alpha"),
            "t": resolved.get("t"),
            "n": resolved.get("n"),
            "a_1": resolved.get("a_1"),
            "plates": resolved.get("plates"),
            "material_from": resolved.get("provenance", ""),
            "source_kind": resolved.get("source_kind") or "",
            "position_id": resolved.get("position_id", ""),
            "position_grade": resolved.get("position_grade", ""),
            "resolved": bool(resolved.get("rho_k")),
        })
    return record


def _places(detail):
    from domains import schema  # here, not at import: schema reads this module for TYPES
    return schema.fastener_places(detail)


def marker_points(source, detail):
    """The connector's fasteners as (x, z), read off the schema in the order the source names them -- its connector markers **and its points ticked «connecteur»** (`schema.fastener_places`, v0.77: a point is taken by every module, not by *Moments polaires* alone). One the schema no longer carries is skipped. A point has no kind, and nothing here needs one: the calculation reads the connector's own `type`."""
    places = _places(detail)
    return [places[mid] for mid in source.get("fasteners", []) if mid in places]


def _drawn_markers(source, detail):
    places = _places(detail)
    return [mid for mid in source.get("fasteners", []) if mid in places]


def missing_markers(source, detail):
    """The fastener ids the source names and the schema carries neither as a marker nor as a point ticked «connecteur»."""
    places = _places(detail)
    return [mid for mid in source.get("fasteners", []) if mid not in places]


def missing_elements(source, detail):
    """The element ids the members name and the schema does not carry, in order and without repeats."""
    known = {e.get("id") for e in (detail or {}).get("elements", [])}
    out = []
    for member in source.get("members", []):
        eid = member.get("element", "")
        if eid and eid not in known and eid not in out:
            out.append(eid)
    return out


def build_record(source, positions, detail=None):
    """One connector as it enters data/connectors.json: the descriptive half, the geometry read off the schema it names, and -- where the type has a module and everything resolved -- the calculation.

    Returns (record, warnings).
    """
    where = "connectors/%s.json" % source["id"]
    warnings = []
    record = _descriptive(source)
    record.update({
        "label": source.get("label", ""),
        # The two halves the default id is composed of, kept so that Woodcore can say whether an id was
        # composed or written over, and so that a listing can group by name across variants.
        "name": source.get("name", ""),
        "variant": source.get("variant", ""),
        "source": where,
        "schema": source.get("schema", ""),
        "fasteners": [{"id": mid, "x": x, "z": z} for mid, (x, z) in zip(_drawn_markers(source, detail), marker_points(source, detail))],
        "n_tot": source["n_tot"]["value"],
        "n_tot_override": bool(source["n_tot"].get("override")),
        "conditions": source["conditions"],
    })
    if record["n_tot_override"]:
        warnings.append("%s: $n_\"tot\"$ ist mit %d von Hand gesetzt; die Zeichnung zeigt %d Verbindungsmittel."
                        % (where, record["n_tot"], len(record["fasteners"])))

    def finish():
        """Every return goes through here: the record carries the warnings it earned, without the file name the export's own list puts in front (the reader already knows which connector is on the page)."""
        record["warnings"] = [w[len(where) + 2:] if w.startswith(where + ": ") else w for w in warnings]
        return record, warnings

    moisture, moisture_from, moisture_warnings = resolve_moisture(source, positions, detail)
    warnings.extend("%s: %s" % (where, message) for message in moisture_warnings)
    record["moisture_class"] = moisture
    record["moisture_from"] = moisture_from

    timber, member_records = [], []
    for index, member in enumerate(source["members"]):
        if member.get("role") != "timber":
            member_records.append(_member_record(member, index, None, detail))
            continue
        resolved, member_warnings = resolve_member(member, len(timber) + 1, positions, where, moisture, detail)
        warnings.extend(member_warnings)
        timber.append(resolved)
        member_records.append(_member_record(member, index, resolved, detail))
    record["members"] = member_records

    module = MODULES.get(source["type"])
    if module is None:
        record.update({"calculated": False,
                       "reason": "%s: für diese Art von Verbindungsmittel gibt es noch keine Berechnung."
                                 % source["type"],
                       "results": [], "tables": [], "vars": {}, "steps": [], "checks": []})
        warnings.append("%s: %s" % (where, record["reason"]))
        return finish()

    # What the schema no longer carries is said before «nothing is ticked», which it would otherwise be read as: a schema deleted leaves no marker, and one that lost a marker draws fewer than n_tot -- which stopped the export (periodic audit 260916, AUD-8-2).
    schema_id = source.get("schema", "")
    lost = missing_markers(source, detail) if detail is not None else []
    if schema_id and detail is None:
        record.update({"calculated": False,
                       "reason": "Das Schema %s gibt es nicht mehr; die Anordnung der Verbindungsmittel und der Tragwiderstand sind damit nicht bestimmt." % schema_id,
                       "results": [], "tables": [], "vars": {}, "steps": [], "checks": []})
        return finish()
    if lost:
        record.update({"calculated": False,
                       "reason": "Das Schema %s trägt die Verbindungsmittel %s nicht mehr; die Anordnung ist unvollständig und der Tragwiderstand wird nicht berechnet." % (schema_id, ", ".join(lost)),
                       "results": [], "tables": [], "vars": {}, "steps": [], "checks": []})
        return finish()

    if not record["fasteners"]:
        record.update({"calculated": False,
                       "reason": "Kein Verbindungsmittel des Schemas ist ausgewählt; ohne Bild der Anordnung "
                                 "sind weder die Mindestabstände noch n_tot bestimmt.",
                       "results": [], "tables": [], "vars": {}, "steps": [], "checks": []})
        return finish()

    missing = [t for t in timber if not t.get("rho_k")]
    if missing:
        record.update({"calculated": False,
                       "reason": "Ein Bauteil trägt keine auswertbare Festigkeitsklasse; "
                                 "der Tragwiderstand kann nicht berechnet werden.",
                       "results": [], "tables": [], "vars": {}, "steps": [], "checks": []})
        return finish()
    if any(t.get("moisture_class") is None for t in timber):
        record.update({"calculated": False,
                       "reason": "Die Verbindung trägt keine Feuchteklasse; eta_w nach SIA 265 Tabelle 4 "
                                 "ist damit nicht bestimmt. Wählen Sie eine Feuchteklasse, oder geben Sie "
                                 "den Bauteilen Positionen, die eine tragen.",
                       "results": [], "tables": [], "vars": {}, "steps": [], "checks": []})
        return finish()

    inputs = _inputs(source, record["n_tot"], timber)

    # A calculation that refuses -- hardwood the norm gives no embedment strength for, a thickness that
    # is not there -- marks the connector uncalculated with its own message, and does not stop the export.
    # The file itself is checked before this, by check_source: a malformed *source* still stops, because
    # that is a defect in the data. This is the difference between «the data is wrong» and «the norm
    # gives no answer for what you asked», and only the first is the export's to refuse (section 3.6).
    try:
        result = module.analyse(inputs)
    except validation.ValidationError as exc:
        record.update({"calculated": False, "reason": str(exc),
                       "results": [], "tables": [], "vars": {}, "steps": [], "checks": []})
        warnings.append("%s: %s" % (where, exc))
        return finish()
    warnings.extend("%s: %s" % (where, message) for message in result["warnings"])

    # The pattern the schema draws: the markers this connector ticked, in its own order. Read off the
    # record rather than off the source, which since schema 2.0 holds ids and not coordinates.
    drawn = record["fasteners"]
    alpha = timber[0].get("alpha", 0)
    spacings = module.check_spacings(drawn, inputs["d"], alpha)
    warnings.extend("%s: %s" % (where, message) for message in spacings["warnings"])
    rows = max((t.get("n") or 1) for t in timber)
    across = int(math.ceil(record["n_tot"] / float(rows))) if rows else 1
    lengths = module.connection_length(drawn, inputs["d"], rows, across)

    # The plates' bearing (SIA 263 Tabelle 16, 6.2.5; D-13, D-14, D-16): a Stahl-Holz joint whose plate is stated gets F_b,Rd beside R_d; one that does not is said, and nothing stops
    if "steel" in inputs and hasattr(module, "plate_bearing"):
        plate = source.get("plate") or {}
        missing = [key for key in PLATE_FIELDS if not (plate.get(key) or {}).get("value")]
        if not source.get("steel"):
            missing.append("steel")
        if missing:
            warnings.append("%s: Lochleibung der Stahlbleche nicht nachgewiesen (SIA 263 Tabelle 16): %s nicht angegeben." % (where, ", ".join(missing)))
        else:
            force = alpha   # the force runs at alpha to the grain, and the grain along the drawing's x (pattern_spacings)
            try:
                bearing = module.plate_bearing({
                    "d": inputs["d"], "t": plate["t"]["value"], "e1": plate["e1"]["value"], "e2": plate["e2"]["value"], "d0": plate["d0"]["value"],
                    "p1": module.pattern_rows(drawn, force)[1], "p2": module.pattern_rows(drawn, force + 90)[1],
                    # the plates a dowel bears on: both outer plates (one per shear plane), or every slotted plate
                    "count": module.shear_planes(inputs["assembly"]) if inputs["assembly"] == "Stahl-Holz, Bleche aussen" else inputs["steel"]["plates"],
                    "grade": source["steel"]})
            except validation.ValidationError as exc:
                warnings.append("%s: %s" % (where, exc))
            else:
                result["plate"] = bearing
                warnings.extend("%s: %s" % (where, message) for message in bearing["warnings"])

    record.update({"calculated": True, "reason": ""})
    record.update(module.record(source["id"], result, timber, spacings, lengths))
    return finish()


def _inputs(source, n_tot, timber):
    """What a calculation module's `analyse` reads, from a checked source and its resolved timber members."""
    inputs = {
        "assembly": source["assembly"],
        "d": source["diameter"]["value"],
        "f_u_k": source["dowel"]["f_u_k"]["value"],
        "dowel_steel": dowel_steel(source),
        "n_tot": n_tot,
        "impact": bool(source["conditions"].get("seismic")),
        "truss": bool(source["conditions"].get("truss")),
        "members": timber,
    }
    plates = next((t["plates"] for t in timber if t.get("plates")), None)
    if plates is not None:
        inputs["steel"] = {
            "plates": plates["count"],
            "slot": plates["slot"]["value"],
            "ratio": plates.get("ratio", 0.5),
            "grade": source.get("steel", ""),
        }
    return inputs


def preview(source, positions, detail=None):
    """The pieces of equation (88) no marker enters -- p, k_beta, p · k_beta, M_u,k -- for Woodcore to show while the connector cannot be calculated yet (no marker ticked, no moisture class). {} where not even p is known.

    ⚠️ Shown and never exported: the record stays `calculated: false` until the pattern exists, so the report cannot print a resistance nobody produced. p depends on the assembly alone; k_beta also needs each member's grade and thickness, d and f_u,k, and is left out while one of them does not resolve.
    """
    module = MODULES.get(source.get("type"))
    if module is None or not hasattr(module, "preview"):
        return {}
    try:
        moisture, _from, _w = resolve_moisture(source, positions, detail)
        timber = []
        for member in source.get("members") or []:
            if member.get("role") == "timber":
                resolved, _w = resolve_member(member, len(timber) + 1, positions, "preview", moisture, detail)
                timber.append(resolved)
        return module.preview(_inputs(source, max(1, (source.get("n_tot") or {}).get("value") or 1), timber))
    except (validation.ValidationError, KeyError, TypeError, ValueError, ZeroDivisionError):
        return {}


# --- the export ----------------------------------------------------------------

def figures(source, detail=None, positions=None, record=None):
    """A connector's drawings: {kind: {language: file name}} and {file name: svg}. `detail` is the schema source it is drawn on.

    The pattern is drawn per language because the drawing sizes its frame from its own words; the section is drawn once, carrying nothing but symbols and numbers.

    **Figur 45** (v0.77): where `record` carries a calculation, every table that states its `curves` -- the k_beta table, one curve per thickness -- has each drawn once (`connector_svg.k_beta_curve`, no word on it) and the curves replaced by `figures`, [{file, index, label, role}], which the report sets under that very table (render-table). The numbers are the table's own rows, so they are not kept twice.

    ⚠️ `connector_svg` is imported here and not at the top of the file. It reads `schema_svg`, which reads `schema`, which reads this module for `TYPES` -- a cycle that breaks on two of five import orders when the edge is at module level, and none when it is here. The module already takes `dowel` the same way round, for the same kind of reason.
    """
    from domains import connector_svg
    cid = source["id"]
    names, files = {}, {}
    section_name = "%s/%s-section.svg" % (FIGURE_DIR, cid)
    files[section_name] = connector_svg.section_of(source)
    names["section"] = {lang: section_name for lang in FIGURE_LANGUAGES}
    if record is not None:
        # the section is word-free: what it had to resize is said here, and the report writes it in its own language (audit 260916)
        record["section_scaled"] = connector_svg.section_state_of(source) or ""
    names["pattern"] = {}
    for lang in FIGURE_LANGUAGES:
        name = "%s/%s-pattern-%s.svg" % (FIGURE_DIR, cid, lang)
        files[name] = connector_svg.pattern_of(source, detail, lang=lang, positions=positions)
        names["pattern"][lang] = name
    for table in (record or {}).get("tables", []):
        curves = table.pop("curves", None)
        if not curves:
            continue
        table["figures"] = []
        for curve in curves:
            name = "%s/%s-kbeta-%d.svg" % (FIGURE_DIR, cid, curve["index"])
            files[name] = connector_svg.k_beta_curve(curve)
            table["figures"].append({"file": name, "index": curve["index"], "label": curve["label"], "role": curve["role"]})
    return names, files


def schema_warnings(source, detail, schemas, where):
    """What the schema a connector names does not carry, as warnings -- never as a stop (docs/decisions.md §13, the v0.33 rule): the report says the resistance could not be calculated, and Woodcore must still be able to open the connector and point it at another schema."""
    out = []
    sid = source.get("schema", "")
    listed = ", ".join(sorted(schemas)) or "none yet -- draw one in Woodcore's «Schémas» tab"
    if not sid:
        out.append("%s is drawn on no schema -- name one in the «Connecteurs» tab (schemas: %s)" % (where, listed))
        return out
    if detail is None:
        out.append("%s is drawn on schema %s, which the export does not list -- name one of %s" % (where, sid, listed))
        return out
    lost = missing_markers(source, detail)
    if lost:
        out.append("%s: schema %s no longer carries the connector marker(s) or point(s) %s -- tick the fasteners again; "
                   "they are left out of the pattern" % (where, sid, ", ".join(lost)))
    lost = missing_elements(source, detail)
    if lost:
        out.append("%s: schema %s no longer carries the element(s) %s -- choose the members' elements again"
                   % (where, sid, ", ".join(lost)))
    return out


def stamp_version(source):
    """The schema_version a source is saved at: 2.2 where it states a plate, 2.1 where a field follows a variable, 2.0 where neither -- what Woodcore's window calls before it writes one."""
    if source.get("plate") is not None:
        source["schema_version"] = PLATE_SCHEMA_VERSION
    else:
        source["schema_version"] = LINKED_SCHEMA_VERSION if links.is_linked(source, LINKABLE) else SOURCE_SCHEMA_VERSION
    return source


def prepare(source_dir, positions=None, schemas=None, values=None):
    """Every connector under `source_dir`, checked and built against the detail schemas `schemas` ({id: source}), with the warnings they earned. Nothing is written. A field that follows a variable takes the value `values` (`links.index`) give it now -- a load's, a script's, a «Formule» domain's, never a joint's (ARCH-005) --, one that cannot be read its last value with a warning; the record then carries `links`, where each came from (REQ-012)."""
    positions = positions or {}
    schemas = schemas if schemas is not None else {}
    connectors, warnings, images = {}, [], {}
    seen = {}
    for path in source_paths(source_dir):
        source = read_source(path)
        cid = source["id"]
        lower = cid.lower()
        if lower in seen:
            _fail(path.name, "id %r is also %s's -- ids differ by more than their case" % (cid, seen[lower]))
        seen[lower] = path.name
        provenance = []
        if values is not None:
            source, provenance, followed = links.follow(source, LINKABLE, values, "connectors/%s.json" % cid, links.JOINTS)
            warnings.extend(followed)
        detail = schemas.get(source.get("schema", ""))
        record, record_warnings = build_record(source, positions, detail)
        if provenance:
            record["links"] = provenance
        warnings.extend(schema_warnings(source, detail, schemas, "connectors/%s.json" % cid))
        try:
            record["figures"], drawings = figures(source, detail, positions, record)
            images.update(drawings)
        except Exception as exc:  # broad: a drawing that fails must not lose the calculation
            record["figures"] = {}
            for table in record.get("tables", []):
                table.pop("curves", None)
            warnings.append("connectors/%s.json: the drawing could not be made -- %s" % (cid, exc))
        connectors[cid] = record
        warnings.extend(record_warnings)

        symbol = TYPES.get(source["type"], "")
        if symbol and not cid.upper().startswith(symbol.upper()):
            warnings.append("connectors/%s.json: id %r does not start with %r, the symbol of a %s."
                            % (cid, cid, symbol, source["type"]))

    linked = any("links" in record for record in connectors.values())
    data = {"schema_version": LINKED_EXPORT_VERSION if linked else EXPORT_SCHEMA_VERSION, "connectors": connectors}
    validation.validate_structure(data, "connectors")
    validation.validate_connectors_business(data)
    return data, images, warnings


def write(data, images, data_dir):
    """data/connectors.json and the drawings under data/connectors/, with the files of a connector that is gone swept away -- connection.write's own arrangement."""
    import engine
    engine.write_json(Path(data_dir) / EXPORT_FILE, data)
    directory = Path(data_dir) / FIGURE_DIR
    if images:
        directory.mkdir(parents=True, exist_ok=True)
    for name, svg in images.items():
        (Path(data_dir) / name).write_text(svg, encoding="utf-8")
    if directory.is_dir():
        wanted = {Path(name).name for name in images}
        for path in directory.glob("*.svg"):
            if path.name not in wanted:
                path.unlink()


def export(source_dir, data_dir, positions=None, schema_dir=None, schemas=None, values=None):
    """prepare() then write() -- what Woodcore's window runs when a connector is saved, so that one connector can be exported without the load workbooks being read again. The detail schemas are read from `schema_dir` (details/ beside the connectors by default) unless `schemas` is handed over."""
    if positions is None:
        positions = known_positions(data_dir)
    if schemas is None:
        from domains import schema as schema_model    # lazy, as `figures` is and for the same reason
        schemas = schema_model.read_sources(schema_dir if schema_dir is not None else Path(source_dir).parent / "details")
    if values is None:
        import variable_sources   # the reader of data/'s variables, which imports this module: imported here
        values = variable_sources.known_values(Path(data_dir))
    data, images, warnings = prepare(source_dir, positions, schemas, values)
    write(data, images, data_dir)
    return data, warnings
