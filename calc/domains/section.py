"""A position's section, read once: Positionen.xlsx's `section type` and `dimension` (docs/domain/positions.md §7, v0.94).

Until v0.94 a position's `dimension` was descriptive text that nothing parsed but two lenient readers -- `schema.parse_section` in Python, for a detail's b and h, and `timber-section-of` in Typst, for `#member`'s -- each with its own regular expression for «b/h». The sheet now says what the text is: a `section type` column beside it names the shape, and this module is the **one** reader of the two cells. The export writes what it reads into each `data/positions/<id>.json` as a `section` record, and everything downstream -- the report's level-1 line, `#member`, a schema element's b and h, Woodcore's summaries -- reads that record and never the text.

The types, and how the dimension is written for each:

| type | what it is | dimension | stored, in mm |
|---|---|---|---|
| `rec` | a rectangular timber section | «b/h», «100/200» | b, h |
| `cir` | a round timber section | «d», «200» | d |
| `pla` | a plate -- OSB, a slab, a panel | «t», «22» or «180» | t |
| `clt` | cross-laminated timber | its layers, «20/30/20/30/20» | layers, and t their sum |
| an SZS C5 code | a steel profile, IPE … ZNP (calc/norms/szs-c5-2018-edv-kurzbezeichnungen.json) | the designation's size, «200» for IPE 200, «101.6x10» for ROR 101.6×10 | dims, as written |
| `USR` | a free steel profile, rectangles drawn in the «Profilés» tab (domains/profile.py, issue #50) | the profile's id, «PR-01» | id |

A timber dimension is in the row's `units` -- mm where it is empty, cm and m converted -- and a steel designation in mm, as SZS C5 writes it. A steel section carries its designation; **its values are SZS C5's tables'** (calc/norms/szs_c5.py `profile`, issue #50 -- until then no table was transcribed) and a free profile's are its rectangles' (domains/profile.py), both read by the steel checks and never written into the position's record. `#member` computes timber only.

An empty type gives no section and leaves the dimension descriptive text, with one exception for the workbooks written before the column existed: a dimension that reads as «b/h» is read as `rec`, and the export says so, naming the position (`deduced`). An unknown type, or a dimension that does not fit its type, is a defect in the sheet and stops the export naming the row and the cell (section 3.6).
"""

import math
import re

import validation
from norms import szs_c5

# The four timber shapes, in the order the sheet's dropdown offers them, each with what its dimension holds. Not a norm's list: the engineer's, and so written here rather than in calc/norms/.
TIMBER_TYPES = (
    {"code": "rec", "kind": "timber", "form": "b/h", "de": "Rechteckquerschnitt", "fr": "Section rectangulaire", "en": "Rectangular section"},
    {"code": "cir", "kind": "timber", "form": "d", "de": "Runder Querschnitt", "fr": "Section ronde", "en": "Round section"},
    {"code": "pla", "kind": "timber", "form": "t", "de": "Platte", "fr": "Plaque", "en": "Plate"},
    {"code": "clt", "kind": "timber", "form": "t_1/t_2/…", "de": "Brettsperrholz", "fr": "Bois lamellé-croisé", "en": "Cross-laminated timber"},
)
TIMBER_CODES = tuple(t["code"] for t in TIMBER_TYPES)

# A free steel profile (issue #50, spec 2026-10-12-section-acier D-12): its dimension is the id of a file of Woodcore-Datei/profiles/, which the export resolves -- this module only checks the id's form, staying pure. A third kind beside timber and steel: neither a catalogue designation nor a timber shape. The engineer's name, not a norm's.
USER_TYPE = {"code": "USR", "kind": "user", "form": "id", "de": "Freies Profil", "fr": "Profilé libre", "en": "Free profile"}
USER_CODE = USER_TYPE["code"]
USER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

# The fields a type's dimension is typed in, form by form, each form in the order its text writes them -- the ONE table of what a dimension holds (v0.117 for rec, cir and pla; issue #9 for every other type). A type with several forms tells them apart by how many numbers its text has, so no form is ever guessed. The steel forms are SZS C5's own (revision 2018, reprinted 2021, SZS-C5-2021.pdf), read off the heads of its profile tables: HD «HD 260×114», h × m (p. 47), and h × b × m, «HD 260×260×114», which the head of its table allows too (PDF p. 51); T h, or h·b·t (p. 48); L a·t for an equal angle, a·b·t for an unequal one (pp. 50, 52); RND D (p. 54); VKT b (p. 55); ROR D·t (p. 60); RRK and RRW h·b·t (pp. 64-71), and a·t, the short form of a square tube the column already took; FLA b·t (p. 74); FLB and BLE b·t, BLE also t alone and b·l·t, a plate in stock (pp. 74-75); ZNP h (p. 78). The I, U and H beams and the half beams carry one number, the designation's size («IPE 200»), named `size`. HL keeps HD's two forms: its series letter (HLA, HL 1000 A) is no number, and stays out of the dimension as it always did. CLT is not here: a panel has as many layers as it has (`LAYERED`). The SZS C4 and C1 types are assemblies, not catalogue profiles, and are not types at all (issue #9).
FORMS = {
    "rec": (("b", "h"),), "cir": (("d",),), "pla": (("t",),),
    "IPE": (("size",), ("size", "m")), "IPEA": (("size",),), "IPN": (("size",),), "UPE": (("size",),), "UPN": (("size",),),
    "HEA": (("size",),), "HEB": (("size",),), "HEM": (("size",),), "HD": (("h",), ("h", "m"), ("h", "b", "m")), "HL": (("h",), ("h", "m")),
    "T": (("h",), ("h", "b", "t")), "IPET": (("size",),), "HEAT": (("size",),), "HEBT": (("size",),),
    "L": (("a", "t"), ("a", "b", "t")), "RND": (("D",),), "VKT": (("b",),), "ROR": (("D", "t"),),
    "RRK": (("h", "b", "t"), ("a", "t")), "RRW": (("h", "b", "t"), ("a", "t")),
    "FLA": (("b", "t"),), "FLB": (("b", "t"),), "BLE": (("t",), ("b", "t"), ("b", "l", "t")), "ZNP": (("h",),),
    "USR": (("id",),),
}

# The types whose dimension is a list of layers rather than a few fixed numbers: one field a layer, as many as the panel has.
LAYERED = ("clt",)


def _form_text(forms):
    """How a type's forms read to the eye, for a refusal: «D×t», «h or h×m», «t, b×t or b×l×t». The one-number size of a beam reads «h», as it always did."""
    texts = ["×".join("h" if field == "size" else field for field in form) for form in forms]
    return texts[0] if len(texts) == 1 else ", ".join(texts[:-1]) + " or " + texts[-1]


# How many numbers a steel designation's size carries, per family, and what it looks like to the eye -- both read off FORMS, never written beside it: «IPE 200» one, «ROR 101.6x10» two (D and t), «RRW 200x100x8» two or three, «L 100x100x10» two or three. Held equal to the SZS C5 list by tests/test_section.py.
STEEL_NUMBERS = {code: (min(len(f) for f in forms), max(len(f) for f in forms)) for code, forms in FORMS.items() if code not in TIMBER_CODES + (USER_CODE,)}
STEEL_FORMS = {code: _form_text(forms) for code, forms in FORMS.items() if code not in TIMBER_CODES + (USER_CODE,)}

# Every code the column takes, timber first, then SZS C5's in the file's order: what Woodcore's dropdown and the sheet's data validation list.
CODES = TIMBER_CODES + szs_c5.codes() + (USER_CODE,)

# Every code with its kind and its names, in that order.
TYPES = TIMBER_TYPES + tuple({"code": code, "kind": "steel", "form": STEEL_FORMS[code], **szs_c5.names(code)} for code in szs_c5.codes()) + (USER_TYPE,)

# A timber dimension's unit: millimetres, and centimetres and metres converted. What the sheet's `units` column may hold; an empty cell is mm.
UNIT_FACTORS = {"": 1.0, "mm": 1.0, "cm": 10.0, "m": 1000.0}

# A number as the sheet may hold it, a decimal comma read as a point (docs/typst/language.md §4bis: numbers are printed with a point in every language).
NUMBER = r"\d+(?:[.,]\d+)?"
# «b/h» -- and «b x h», «b×h», which the lenient readers before v0.94 took as well, so nothing that had a section loses it
TWO = re.compile(rf"^\s*({NUMBER})\s*[/x×]\s*({NUMBER})\s*$", re.IGNORECASE)
ONE = re.compile(rf"^\s*(?:[Øø]\s*)?({NUMBER})\s*$")
LAYERS = re.compile(rf"^\s*{NUMBER}(?:\s*/\s*{NUMBER})+\s*$")
STEEL = re.compile(rf"^\s*{NUMBER}(?:\s*[x×*/]\s*{NUMBER})*\s*$", re.IGNORECASE)

# The multiplication sign a steel designation is printed with, «ROR 101.6×10».
TIMES = "×"


def _number(text):
    return float(text.replace(",", "."))


def _clean(value):
    """A number as the record stores it: a whole number as an int, so that 100 is written 100 and not 100.0, and anything else to six decimals."""
    value = round(float(value), 6)
    return int(value) if value.is_integer() else value


def fmt(value):
    """A number as a section's text prints it: at most six decimals, trailing zeros dropped -- 100, 101.6, 12.5."""
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _unit(units, where, code):
    unit = str(units or "").strip().lower()
    if unit not in UNIT_FACTORS:
        raise validation.ValidationError(
            f"{where}: units is {units!r} -- a {code} section is written in mm, cm or m (empty is mm)")
    return unit or "mm", UNIT_FACTORS[unit]


# The fields a type's dimension is typed in are FORMS' (v0.117; the engineer: «lorsque le type de section est donné, une section "Dimension" avec des textbox différentes: "rec" => largeur, hauteur; "plaque" => épaisseur»; issue #9: «tous les types de section existants sont repris»). No type at all has none, and its dimension stays a line of text.


def dimension_forms(code):
    """The forms the dimension of type `code` is typed in, each a tuple of field names in the order its text writes them -- `(("b", "h"),)` for `rec`, `(("a", "t"), ("a", "b", "t"))` for `L` --, `()` for a layered type (`is_layered`) and for no type or an unknown one."""
    return FORMS.get(code or "", ())


def dimension_fields(code):
    """The fields of the type's first form -- `("b", "h")` for `rec`, `("d",)` for `cir`, `("size",)` for `IPE`, `("h", "b", "t")` for `RRW` --, `()` for a layered type and for none."""
    forms = dimension_forms(code)
    return forms[0] if forms else ()


def is_layered(code):
    """Whether the type's dimension is its layers, one field each, as many as there are (`clt`)."""
    return code in LAYERED


def form_of(code, count):
    """The form of type `code` that has `count` fields, or None: a type's forms never share a count, so the numbers typed say which form they are."""
    for form in dimension_forms(code):
        if len(form) == count:
            return form
    return None


def _steel_size(code, text):
    # «IPE 200» typed whole is the designation's own form: the code before the size is taken off, as `parse` does
    return re.sub(rf"^\s*{re.escape(code)}(?![A-Za-z])", "", str(text or ""), flags=re.IGNORECASE).strip()


def split_dimension(code, text):
    """The numbers a dimension text holds, as typed, in the order of the form they make -- «100/200» and «100 x 200» give ("100", "200") for `rec`, «101.6x10» ("101.6", "10") for `ROR`, «20/30/20» ("20", "30", "20") for `clt` --, or None where the text does not read as one of the type's forms (the dimension then stays the text it was: a descriptive one, a section typed otherwise). Reads what `parse` reads, with the same expressions; `form_of(code, len(values))` names the form."""
    text = str(text or "").strip()
    if is_layered(code):
        return tuple(part.strip() for part in text.split("/")) if LAYERS.match(text) else None
    if not dimension_forms(code):
        return None
    if code in TIMBER_CODES:
        match = (TWO if code == "rec" else ONE).match(text)
        return tuple(match.groups()) if match else None
    if code == USER_CODE:
        return (text,) if USER_ID.match(text) else None
    size = _steel_size(code, text)
    if not size or not STEEL.match(size):
        return None
    values = tuple(re.split(r"\s*[x×*/]\s*", size, flags=re.IGNORECASE))
    return values if form_of(code, len(values)) else None


def join_dimension(code, values):
    """The dimension text the fields `values` write: «100/200» for `rec`, the number for a type with one, «101.6x10» for a steel form of two -- the `x` SZS C5's designations are typed with --, «20/30/20» for a CLT panel's layers -- what the dimension cell holds. Nothing typed is "", and a field left empty leaves its place («100/»), so that what is typed is not lost while it is being typed and `parse` says what is missing. Raises ValueError for a count of values that is none of the type's forms."""
    if not (is_layered(code) or form_of(code, len(values))):
        counts = " or ".join(str(len(form)) for form in dimension_forms(code)) or "no"
        raise ValueError(f"{code!r} has {counts} dimension field(s), not {len(values)}")
    typed = [str(value or "").strip() for value in values]
    if not any(typed):
        return ""
    if code == USER_CODE:
        return typed[0]
    return ("/" if code in TIMBER_CODES else "x").join(typed)


def area_mm2(record):
    """A position's cross-section area in mm², where its section has one this module can tell: a rectangle's b·h, a round section's π·d²/4. None for a plate and a CLT panel, which have a thickness and no section area (their volume is an area times t), for a steel profile and a free one -- their area is SZS C5's table's (calc/norms/szs_c5.py) or their rectangles' (domains/profile.py), which the steel checks read and this module, which never reads the norms' tables nor the project, does not --, and where there is no section."""
    section_ = of_record(record)
    if not section_:
        return None
    if section_.get("type") == "rec":
        return float(section_["b"]) * float(section_["h"])
    if section_.get("type") == "cir":
        return math.pi * float(section_["d"]) ** 2 / 4
    return None


def code_of(section_type):
    """The code a `section type` cell names, as the list spells it -- «ipe» is IPE, «REC» is rec -- or "" for an empty cell; None for a type the list does not carry."""
    text = str(section_type or "").strip()
    if not text:
        return ""
    for code in CODES:
        if code.lower() == text.lower():
            return code
    return None


def kind_of(code):
    """"timber", "steel" (an SZS C5 designation) or "user" (a free profile, USR) for a code of the list."""
    return "timber" if code in TIMBER_CODES else "user" if code == USER_CODE else "steel"


def name(code, lang="de"):
    """A code's name in one of the three languages, «Rechteckquerschnitt», «Runde Stahlrohre, nahtlos oder geschweisst»."""
    for entry in TYPES:
        if entry["code"] == code:
            return entry[lang]
    raise KeyError(code)


def _refuse(where, code, text, form):
    raise validation.ValidationError(
        f"{where}: dimension {text!r} does not read as a {code} section -- write it {form}")


def _timber(code, text, units, where):
    unit, factor = _unit(units, where, code)
    if code == "rec":
        match = TWO.match(text)
        if not match:
            _refuse(where, code, text, "b/h, «100/200»")
        b, h = _number(match.group(1)), _number(match.group(2))
        if b <= 0 or h <= 0:
            _refuse(where, code, text, "b/h with b and h above 0")
        return {"type": code, "kind": "timber", "text": f"{fmt(b)}/{fmt(h)} {unit}", "b": _clean(b * factor), "h": _clean(h * factor)}
    if code in ("cir", "pla"):
        match = ONE.match(text)
        if not match or _number(match.group(1)) <= 0:
            _refuse(where, code, text, "as one number above 0, «200»" if code == "cir" else "as its thickness, «22»")
        value = _number(match.group(1))
        if code == "cir":
            return {"type": code, "kind": "timber", "text": f"Ø {fmt(value)} {unit}", "d": _clean(value * factor)}
        return {"type": code, "kind": "timber", "text": f"{fmt(value)} {unit}", "t": _clean(value * factor)}
    # clt: the layers, outermost first, and their sum
    if not LAYERS.match(text):
        _refuse(where, code, text, "as its layers, «20/30/20/30/20»")
    layers = [_number(part) for part in text.split("/")]
    if any(layer <= 0 for layer in layers):
        _refuse(where, code, text, "as its layers, each above 0")
    total = sum(layers)
    return {"type": code, "kind": "timber", "text": f"{'/'.join(fmt(layer) for layer in layers)} {unit} ({fmt(total)} {unit})",
            "layers": [_clean(layer * factor) for layer in layers], "t": _clean(total * factor)}


def _steel(code, text, units, where):
    unit = str(units or "").strip().lower()
    if unit not in ("", "mm"):
        raise validation.ValidationError(
            f"{where}: units is {units!r} -- a steel designation is written in mm, as SZS C5 writes it; leave units empty or mm")
    # «IPE 200» typed whole into the dimension is the designation's own form: the code before the size is taken off, not refused
    size = _steel_size(code, text)
    low, high = STEEL_NUMBERS[code]
    form = STEEL_FORMS[code]
    if not STEEL.match(size):
        _refuse(where, code, text, f"as the designation's size, {form} («{code} {'101.6x10' if code == 'ROR' else '200'}»)")
    dims = [_number(part) for part in re.split(r"\s*[x×*/]\s*", size.strip(), flags=re.IGNORECASE)]
    if not low <= len(dims) <= high:
        count = f"{low}" if low == high else f"{low} or {high}" if high == low + 1 else f"{low} to {high}"
        _refuse(where, code, text, f"as {count} number{'s' if high > 1 else ''}, {form}")
    if any(d <= 0 for d in dims):
        _refuse(where, code, text, f"with every number above 0, {form}")
    return {"type": code, "kind": "steel", "text": f"{code} {TIMES.join(fmt(d) for d in dims)}", "dims": [_clean(d) for d in dims]}


def _user(text, units, where):
    """A free profile: the dimension is its id, checked for its form only -- whether the file exists is the export's to say (a missing input warns), this module never reading the project."""
    if str(units or "").strip().lower() not in ("", "mm"):
        raise validation.ValidationError(f"{where}: units is {units!r} -- a free profile is drawn in mm; leave units empty or mm")
    if not USER_ID.match(text):
        _refuse(where, USER_CODE, text, "as the id of a free profile of the «Profilés» tab, «PR-01»")
    return {"type": USER_CODE, "kind": "user", "text": f"{USER_CODE} {text}", "id": text}


def deduce(dimension, units=""):
    """The section an EMPTY type reads as: `rec`, marked `deduced`, where the dimension is «b/h» in mm, cm or m -- the exception for a workbook written before the column existed -- and None otherwise, the dimension then staying descriptive text. Never raises."""
    text = str(dimension or "").strip()
    unit = str(units or "").strip().lower()
    match = TWO.match(text)
    if not match or unit not in UNIT_FACTORS:
        return None
    if _number(match.group(1)) <= 0 or _number(match.group(2)) <= 0:
        return None
    section = _timber("rec", text, units, "")
    section["deduced"] = True
    return section


def parse(section_type, dimension, units="", where="section"):
    """The section a row's `section type`, `dimension` and `units` state, as the export writes it into the position's record: {type, kind, text, ...} with b and h (rec), d (cir), t (pla), layers and t (clt) in mm, or dims (steel); None where the type is empty and the dimension is not «b/h» (see `deduce`).

    Raises a ValidationError naming `where` -- the sheet and the position -- and the cell, for a type the list does not carry, a type with no dimension, and a dimension that does not fit its type.
    """
    text = str(dimension or "").strip()
    code = code_of(section_type)
    if code == "":
        return deduce(text, units)
    if code is None:
        raise validation.ValidationError(
            f"{where}: section type {section_type!r} is not one of {', '.join(CODES)} -- or leave it empty for a dimension that is descriptive text")
    if not text:
        raise validation.ValidationError(f"{where}: section type {code} needs a dimension")
    if code == USER_CODE:
        return _user(text, units, where)
    return _timber(code, text, units, where) if code in TIMBER_CODES else _steel(code, text, units, where)


def of_record(record):
    """A position record's section: the one the export wrote (`section`, v0.94), or, for a record exported before the column existed, the one its dimension reads as by the same deduction the export applies -- so a project not exported again since still has its b/h. None where there is no section."""
    if not record:
        return None
    if "section" in record:
        return record.get("section")
    return deduce(record.get("dimension", ""), record.get("units", ""))


def sides(record):
    """(b, h) in mm where a side is needed -- a schema element's band, its label: a rectangle's own two, a round section's diameter for both, a plate's or a CLT panel's thickness for both; None for a steel profile and a free one, whose b and h are their tables' or their rectangles' and not this module's, and where there is no section."""
    section = of_record(record)
    if not section:
        return None
    kind = section.get("type")
    if kind == "rec":
        return float(section["b"]), float(section["h"])
    if kind == "cir":
        return float(section["d"]), float(section["d"])
    if kind in ("pla", "clt"):
        return float(section["t"]), float(section["t"])
    return None


def display(record):
    """What a summary prints of a position's section: its text -- «100/200 mm», «Ø 200 mm», «ROR 101.6×10» -- and, where the record has no section, its dimension as typed with its unit, «180 mm», «180» where no unit is typed; "" where the sheet states no dimension, a unit never being printed alone."""
    if not record:
        return ""
    section = of_record(record)
    if section:
        return section["text"]
    dimension = str(record.get("dimension") or "").strip()
    return f"{dimension} {str(record.get('units') or '').strip()}".strip() if dimension else ""
