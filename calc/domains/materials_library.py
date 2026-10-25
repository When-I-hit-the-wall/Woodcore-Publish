"""The materials as the «Matériaux» tab lists them, one place (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-005 to REQ-007; issue #110): what `library_tab.LibraryTab` asks of its `STORE`.

The entries are Woodcore's -- read only, read at their source (`materials_catalogue`) -- followed by the engineer's own (`materials_user`); a library that cannot be read leaves Woodcore's listed and says why (`entries` returns the error), and nothing of it is written while it cannot be read. A new material, a duplicate, a save and a delete are `materials_user`'s; the words are the tab's. No Qt here.
"""

import validation
from domains import materials_catalogue, materials_contract, materials_user

# The words of a shipped material's origin, the norms' own names written as they are; the two others are the tab's (mat_src_ext, mat_src_user)
ORIGIN_TAGS = {"sia265": "SIA 265", "sia265-1": "SIA 265/1", "sia261": "SIA 261"}


def entries():
    """(every material, an error or "") -- Woodcore's, then the engineer's."""
    shipped = list(materials_catalogue.catalogue())
    try:
        return shipped + materials_user.materials(), ""
    except validation.ValidationError as exc:
        return shipped, str(exc)


def editable(m):
    return not m.get("origin")


def name(m, lang):
    return materials_contract.name(m, lang)


def tag(m):
    """What the label of a material's source says: a norm's name, `ext` or `user` for the tab's words."""
    return ORIGIN_TAGS.get(m.get("origin")) or ("ext" if m.get("origin") == "ext" else "user")


def new(kind):
    return materials_user.blank(kind)


def duplicate(m):
    """A copy of the engineer's own, «← SIA 265» or «← <name>» in its comment."""
    label = ORIGIN_TAGS.get(m.get("origin")) or ("Classeur Belastungsannahmen" if m.get("origin") == "ext" else name(m, "fr"))
    out = materials_user.duplicate(m, label)
    for key in ("origin", "excerpt", "stored", "rows", "unavailable", "rho_k_is_minimum"):
        out.pop(key, None)
    if out.get("type") == "panel":
        out.setdefault("thickness", None)
    return out


def save(m):
    return materials_user.save(m)


def delete(material_id):
    return materials_user.delete(material_id)


def stored(m):
    """Where a material is saved: the engineer's library file, or the file of calc/ it is read from."""
    return str(materials_user.library_file()) if editable(m) else m.get("stored", "")
