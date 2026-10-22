"""SZS C5 in this program: the profile families a steel position may name, and their profile tables (docs/domain/positions.md §7, docs/domain/steel.md, docs/architecture/layout.md §11).

**The families.** `calc/norms/szs-c5-2018-edv-kurzbezeichnungen.json`: the short designations of the page «Kurzbezeichnungen für EDV-Anwendungen» (SZS C5, revision 2018, printed p. 154) that the engineer chose for Positionen.xlsx's `section type` column -- IPE, HEA, ROR, RRW ... -- each with the page's German and French name, and an English one that is a translation and not the norm's. A steel position's dimension is the designation's size as it is written, and domains/section.py is what reads it.

**The profile tables** (issue #50, 12.10.2026; spec 2026-10-12-section-acier D-04). Until then «no profile table is transcribed» (docs/decisions.md); the engineer: «Relire SZS C5, Excel en contrôle». `calc/norms/szs-c5-2018-profile-<file>.json`, one file per table of the book (`TABLE_FILES`), hold each family's «Statische Werte» and «Profilmasse» **as printed** -- each column's factor under its head (×10⁶, ×10³) stated in the file's `columns` and applied here, so that `profile()` answers in plain mm units. Twenty families: IPE, IPEA, IPN, UPE, UPN, HEA, HEB, HEM, HD, HL, T, IPET, HEAT, HEBT, L, RND, VKT, ROR, RRK, RRW (FLA, FLB, BLE and ZNP are not tabulated: a flat or a plate is a rectangle). The scan was read off renders of its pages and held against the mechanics of each section and against the reference extract (tests/test_steel_profiles.py); eight values of the book contradict the rest of their row and are kept as printed (`ANOMALIES`).

A halved profile (IPET, HEAT, HEBT) takes its t_w, t_f and r from its parent (`PARENTS`), as the page says; a tube or a bar, whose table prints one I, W_el, W_pl and i, has them about both axes, and its h, b, t or D come from its designation.
"""

from pathlib import Path

import validation
from norms import _loader  # how every reader of calc/norms/ opens its files (G3)

NAME = "szs-c5-2018-edv-kurzbezeichnungen"
PATH = Path(__file__).resolve().parent / (NAME + ".json")

# The three languages every name is given in: the page's two, and English, which the file says is a translation.
LANGUAGES = ("de", "fr", "en")

_cache = {}


def _fail(what):
    raise validation.ValidationError("calc/norms/%s.json: %s" % (NAME, what))


def _read():
    if "data" in _cache:
        return _cache["data"]
    data = _loader.load(PATH)
    _loader.edition(NAME, data)
    codes = data.get("codes")
    if not isinstance(codes, list) or not codes:
        _fail("no 'codes' list")
    seen = set()
    for entry in codes:
        code = entry.get("code") if isinstance(entry, dict) else None
        # a code is what is typed into the sheet and printed before the size («IPE 200»): capitals and nothing else, which is the page's own form
        if not isinstance(code, str) or not code.isalpha() or not code.isupper():
            _fail("a code is %r -- expected capitals, as the page writes them" % (code,))
        if code in seen:
            _fail("%s is listed twice" % code)
        seen.add(code)
        for lang in LANGUAGES:
            if not isinstance(entry.get(lang), str) or not entry[lang].strip():
                _fail("%s has no %s name" % (code, lang))
    _cache["data"] = data
    return data


def edition():
    """The edition the list belongs to, "SZS C5:2018"."""
    return _read()["edition"]


def codes():
    """The short designations, in the file's order -- the engineer's, grouped by family."""
    return tuple(entry["code"] for entry in _read()["codes"])


def names(code):
    """{de, fr, en} of one code; KeyError for a code the list does not carry."""
    for entry in _read()["codes"]:
        if entry["code"] == code:
            return {lang: entry[lang] for lang in LANGUAGES}
    raise KeyError(code)


def check_all():
    """Read and check the family list and every profile table."""
    check_tables()
    return edition()


# --- the profile tables (issue #50) --------------------------------------------

# One file per table of the book, in the book's order.
TABLE_FILES = ("ipe", "ipn", "upe", "upn", "hea", "heb", "hem", "hd-hl", "t", "l", "rnd", "vkt", "ror", "rrk", "rrw")
TABLE_NAMES = tuple("szs-c5-2018-profile-%s" % stem for stem in TABLE_FILES)

# A halved profile's parent, whose t_w, t_f and r it keeps (the T page's reference to the IPE, HEA and HEB pages).
PARENTS = {"IPET": "IPE", "HEAT": "HEA", "HEBT": "HEB"}

# The families whose table prints one I, W_el, W_pl and i: the same about y and z.
SYMMETRIC = ("RND", "VKT", "ROR")

# Values of the book that disagree with the rest of their row, kept as printed: (code, size, key) -> what is wrong. A check that reads one says so.
ANOMALIES = {
    ("HD", "320x74", "I_z"): "SZS C5 prints I_z = 45,59·10⁶ mm⁴ where its own W_el,z and i_z give about 49,6·10⁶",
    ("HD", "400x216", "W_y_bar"): "SZS C5 prints W̄_y = 4010·10³ mm³ where I_y/((h−t_f)/2) gives 4097·10³",
    ("HD", "400x1086", "A_v"): "SZS C5 prints A_v = 29 580 mm², smaller than its own A_w = 34 600 mm²",
    ("IPN", "550", "i_z"): "SZS C5 prints i_z = 40,2 mm where sqrt(I_z/A) of its own row gives 40,6",
    ("UPN", "320", "i_y"): "SZS C5 prints i_y = 121 mm where sqrt(I_y/A) of its own row gives 119,7",
    ("ROR", "457x11", "i"): "SZS C5 prints i = 156 mm where sqrt(I/A) of its own row gives 157,8",
    ("RRW", "500x200x12.5", "i_z"): "SZS C5 prints i_z = 85 mm where sqrt(I_z/A) of its own row gives 84,4",
    ("ROR", "610x60", "W_pl"): "SZS C5 prints W_pl = 18 000·10³ mm³ where (D³ − d³)/6 gives 18 222·10³",
}

_tables = {}


def _fail_table(name, what):
    raise validation.ValidationError("calc/norms/%s.json: %s" % (name, what))


def _read_tables():
    """Every table file, read and checked once: {code: {"columns", "rows", "factors", "units", "file", "norm_ref"}}."""
    if "families" in _tables:
        return _tables["families"]
    families = {}
    for name in TABLE_NAMES:
        path = PATH.parent / (name + ".json")
        data = _loader.load(path)
        if data.get("edition") != edition():
            _fail_table(name, "edition %r -- the family list is %r, and two editions of one book would be two books" % (data.get("edition"), edition()))
        if not str(data.get("_source", "")).strip() or not data.get("norm_ref"):
            _fail_table(name, "no '_source' or 'norm_ref' -- every table names the page it was read off")
        columns = data.get("columns") or {}
        for fam, table in (data.get("families") or {}).items():
            if fam not in codes():
                _fail_table(name, "%s is no family of the EDV list" % fam)
            if fam in families:
                _fail_table(name, "%s is tabulated twice" % fam)
            cols = table.get("columns") or []
            for col in cols:
                if col != "series" and col not in columns:
                    _fail_table(name, "%s: column %r has no unit in 'columns'" % (fam, col))
            rows = table.get("rows") or {}
            if not rows:
                _fail_table(name, "%s has no rows" % fam)
            for size, row in rows.items():
                if not isinstance(row, list) or len(row) != len(cols):
                    _fail_table(name, "%s %s: %d values for %d columns" % (fam, size, len(row) if isinstance(row, list) else 0, len(cols)))
                for col, value in zip(cols, row):
                    if col in ("typ", "series") or value is None:
                        continue
                    if not isinstance(value, (int, float)) or value <= 0:
                        _fail_table(name, "%s %s: %s is %r -- expected a number above 0" % (fam, size, col, value))
            families[fam] = {"columns": cols, "rows": rows, "file": name, "norm_ref": data["norm_ref"],
                             "factors": {col: columns[col].get("factor", 1) for col in cols if col in columns},
                             "units": {col: columns[col]["unit"] for col in cols if col in columns}}
    for child, parent in PARENTS.items():
        if child in families and parent not in families:
            _fail_table("szs-c5-2018-profile-t", "%s's parent %s is not tabulated" % (child, parent))
    _tables["families"] = families
    return families


def tabulated():
    """The codes that have a profile table, in the book's order."""
    return tuple(_read_tables())


def sizes(code):
    """The sizes of one family's table as its designations write them after the code -- «200», «260x114», «100x10», «101.6x10» --, in the table's order; () for a family without a table."""
    table = _read_tables().get(code)
    return tuple(table["rows"]) if table else ()


def _fmt(value):
    text = ("%.6f" % float(value)).rstrip("0").rstrip(".")
    return text or "0"


def key_of(code, dims):
    """The key a designation's numbers have in its table: «101.6x10» for ROR (101.6, 10), «100x10» for an equal angle typed (100, 100, 10), «200x200x10» for a square tube typed (200, 10)."""
    dims = [float(d) for d in dims]
    if code == "L" and len(dims) == 3 and dims[0] == dims[1]:
        dims = [dims[0], dims[2]]
    if code in ("RRK", "RRW") and len(dims) == 2:
        dims = [dims[0], dims[0], dims[1]]
    return "x".join(_fmt(d) for d in dims)


def _same_about_both_axes(out):
    for axis in ("y", "z"):
        out["I_" + axis], out["W_el_" + axis], out["W_pl_" + axis], out["i_" + axis] = out["I"], out["W_el"], out["W_pl"], out["i"]


def profile(code, dims):
    """One profile's values out of its table, in plain mm units -- {"designation", "code", "size", "edition", "norm_ref", "file", "anomalies", <column>: value} -- or None for a designation the table does not carry (the caller says so: a missing input warns).

    The keys are the tables' own: m kg/m; A, A_v, A_w mm²; I_y, I_z, K mm⁴; W_el_y, W_y_bar, W_pl_y, W_el_z, W_pl_z mm³; i_y, i_z, h, b, t_w, t_f, r, h_1 ... mm. A halved profile adds its parent's t_w, t_f and r; a bar or a round or square tube its one I, W_el, W_pl, i about both axes; a tube, a bar or an angle the dimensions its designation states. A value the page prints as ■ (no plastic method, ROR) is None."""
    table = _read_tables().get(code)
    if not table:
        return None
    size = key_of(code, dims)
    row = table["rows"].get(size)
    if row is None:
        return None
    out = {"designation": "%s %s" % (code, size.replace("x", "×")), "code": code, "size": size, "edition": edition(),
           "norm_ref": table["norm_ref"], "file": table["file"]}
    for col, value in zip(table["columns"], row):
        if col in ("typ", "series"):
            out[col] = value
        else:
            out[col] = None if value is None else value * table["factors"].get(col, 1)
    if code in PARENTS:
        parent = profile(PARENTS[code], [size])
        for col in ("t_w", "t_f", "r"):
            out[col] = parent[col]
    numbers = [float(part) for part in size.split("x")]
    if code in SYMMETRIC or (code in ("RRK", "RRW") and out.get("I") is not None):
        _same_about_both_axes(out)
    if code == "ROR":
        out["D"], out["t"] = numbers
        out["h"] = out["b"] = numbers[0]
    elif code in ("RND", "VKT"):
        out["h"] = out["b"] = numbers[0]
        if code == "RND":
            out["D"] = numbers[0]
    elif code in ("RRK", "RRW"):
        out["h"], out["b"], out["t"] = numbers
    elif code == "L":
        out["a"], out["t"] = numbers[0], numbers[-1]
        out["b"] = numbers[1] if len(numbers) == 3 else numbers[0]
        out["h"] = out["a"]
        if out.get("I_z") is None:   # an equal angle: the page prints one column for y and z, and one e
            out["I_z"], out["W_el_z"], out["i_z"] = out["I_y"], out["W_el_y"], out["i_y"]
            out["e_y"] = out["e_z"] = out.get("e")
    out["anomalies"] = {}
    for (c, s, key), why in ANOMALIES.items():
        if c == code and s == size:
            # a value printed once for both axes is wrong about both
            for name in ((key, key + "_y", key + "_z") if key in ("I", "W_el", "W_pl", "i") else (key,)):
                out["anomalies"][name] = why
    return out


def check_tables():
    """Read and check every table file."""
    return tabulated()
