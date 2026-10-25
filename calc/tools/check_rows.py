"""What the three services of a member check's head read alike -- «Élément» (check_member.py), «Sollicitation» (load_row.py), «Facteurs» (factors_row.py) -- written once (issue #112, ARCH-004): a number as the window writes it, the material a draft names, the value of the tab's quantity a material gives. No widget, no service: the services never import each other.
"""

from domains import member_check_material as mm
from norms import sia265


def decimal(value, lang, least=0):
    """A number as the window writes it: 9,6 in French and German, 9.6 in English -- `least` decimals at least (a factor 1,0)."""
    if value is None:
        return "—"
    text = ("%.3f" % value).rstrip("0")
    if least:
        whole, _dot, part = text.partition(".")
        text = whole + "." + part.ljust(least, "0")
    text = text.rstrip(".")
    return text.replace(".", ",") if lang in ("fr", "de") else text


def material_of(src, record):
    """The material of the library a draft names -- its `material`, its class of before (`grade`), else the position's class --, None where none is known."""
    from domains import member_check
    src = src or {}
    mid = src.get("material") or (("sia265:" + src["grade"]) if src.get("grade") else None)
    if mid is None and (record or {}).get("grade"):
        mid = "sia265:" + record["grade"]
    return member_check.find_material(mid) if mid else None


def material_value(material, tab):
    """The design value of the tab's quantity a member gives at η_w = η_t = 1 -- what its one loading bubble says --, None for a panel or no material."""
    quantity = mm.TAB_QUANTITY[tab]
    if not material or material.get("type") != "member":
        return None
    if material.get("origin") == "sia265":
        cell = sia265.grade(mm.grade_of(material["id"]))["f_%s_d" % mm.MEMBER_KEY[quantity]]
        return cell.get("generell") if isinstance(cell, dict) else cell
    from domains import materials_derive
    design = materials_derive.member_design(material, mm.MEMBER_KEY[quantity])
    return design.value if design else None
