"""What SN EN 14592:2022 asks of a Stabdübel, out of `calc/norms/sn-en-14592-2022-stabduebel-werkstoff.json` (docs/architecture/layout.md §11), and the f_u,k Woodcore calculates one with.

EN 14592:2022 Anhang G, G.4 and Tabelle G.9 (PDF p. 81) ask of a dowel's bar a minimum yield stress of 235 N/mm² and give **no** tensile strength. SIA 265 6.1.4.4 equation (87) reads f_u,k, so Woodcore takes it from the bar's steel grade in SIA 263:2013 Tabelle 1 (`sia263.f_u`) -- one value, one place (spec 2026-10-12-audit-issues-47-48-49, D-06, D-20). Until then the project credited 510 N/mm² to SN EN 14592+A1:2012, an edition not in the library; 510 is S355's f_u, and S355 stays the grade a new Stabdübel starts with.
"""

import json
from pathlib import Path

import validation
from norms import sia263

NAME = "sn-en-14592-2022-stabduebel-werkstoff"
PATH = Path(__file__).resolve().parent / (NAME + ".json")

_cache = {}


def _fail(what):
    raise validation.ValidationError("calc/norms/%s.json: %s" % (NAME, what))


def _read():
    if "data" in _cache:
        return _cache["data"]
    try:
        with PATH.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        _fail("not found at %s -- the values of SN EN 14592 live in calc/norms/" % PATH)
    except json.JSONDecodeError as exc:
        _fail("is not valid JSON: %s" % exc)
    if not data.get("edition"):
        _fail("no 'edition'")
    block = data.get("stabduebel")
    if not isinstance(block, dict):
        _fail("no 'stabduebel' block")
    value = block.get("min_yield")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        _fail("min_yield is %r -- expected a positive number" % (value,))
    for key in ("default_steel", "unit", "norm", "norm_ref", "label"):
        if not block.get(key):
            _fail("stabduebel has no '%s'" % key)
    if block["default_steel"] not in sia263.grades():
        _fail("default_steel %r is no grade of SIA 263 Tabelle 1" % block["default_steel"])
    _cache["data"] = data
    return data


def edition():
    """The edition read, "SN EN 14592:2022"."""
    return _read()["edition"]


def requirement():
    """Tabelle G.9's block: {norm, norm_ref, clause, page, min_yield, unit, min_elongation, default_steel, label}."""
    return dict(_read()["stabduebel"])


def default_steel():
    """The grade a new Stabdübel starts with, "S355"."""
    return _read()["stabduebel"]["default_steel"]


def dowel_grades():
    """The grades of SIA 263 Tabelle 1 a Stabdübel may be made of: those whose f_y meets Tabelle G.9's minimum, in the table's order."""
    floor = _read()["stabduebel"]["min_yield"]
    return tuple(name for name in sia263.grades() if sia263.steel(name)["f_y"] >= floor)


def f_u_k(grade=None):
    """f_u,k in N/mm² of a Stabdübel of `grade` (the default grade when None): SIA 263 Tabelle 1's f_u, thin band -- a dowel is at most 30 mm (SIA 265 6.2.1.1)."""
    grade = grade or default_steel()
    if grade not in dowel_grades():
        raise validation.ValidationError("steel %r -- a Stabdübel is made of %s (SN EN 14592 Tabelle G.9, SIA 263 Tabelle 1)" % (grade, ", ".join(dowel_grades())))
    return sia263.f_u(grade)


def tensile_strength(grade=None):
    """Where a Stabdübel's f_u,k comes from, for the window and the report: {steel, value, unit, norm, norm_ref, page} -- SIA 263:2013 Tabelle 1, p. 18, as the norm file's `f_u_from` names it."""
    grade = grade or default_steel()
    source = _read()["stabduebel"]["f_u_from"]
    return {"steel": grade, "value": f_u_k(grade), "unit": "N/mm²", "norm": source["norm"], "norm_ref": source["norm_ref"], "page": source["page"]}


def check_all():
    """Read and check the file."""
    dowel_grades()
    return edition()
