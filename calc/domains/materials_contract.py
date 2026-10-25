"""What a material is, written once (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, ARCH-010; issue #110).

One shape for every material Woodcore knows -- the engineer's own library (`materials_user`), the copy a project keeps of the ones it names (`materials_project`) and the ones Woodcore ships (`materials_catalogue`) --, so that the three never drift apart. A material is a dict:

* `id` -- stable (`u-<8 hex>` for the engineer's, `sia265:C24`, `sia265-1:<product>`, `sia261:<row>`, `ext:<row>` for the shipped ones);
* `type` -- `member` (a bar: solid timber, glulam, LVL), `panel` (a wood-based panel) or `other` (nothing load-bearing: a weight only);
* `names` -- {fr, de, en}, one at least; `category` -- one of `CATEGORIES`; `comment`;
* `weight` -- {value, unit, ref}, kN/m³ or kN/m², optional: what a layer of a permanent load is weighed with;
* `source` -- {kind, url, file, ref}: `none`, `url`, `pdf` (a copy in the library's `sources/`), `norm` or `book`;
* a member: `family` (`FAMILIES`) and `values` -- the six strengths, each `_k` and `_d` (`MEMBER_STRENGTHS`), and `MEMBER_STIFFNESS`;
* a panel: `product` (a row of SIA 265/1 Tabelle 9, `norms.sia265_1.products()`), `isotropic`, `columns` -- one per range of thickness, `[]` for one --, `thickness` (optional, mm), `rho_k` (one per column) and `grid` {loading: {key: {direction: [one value per column]}}}, the shape of SIA 265/1 Tabellen 11 to 23.

A characteristic value ends in `_k`, a design value in `_d`; a stiffness (`E_…_mean`, `G_mean`) and ρ_k are never deduced. The words a window shows for any of these are its own (`calc/tools/materials_tab_words.py`); the search vocabulary of a category is here, held to those words by tests/test_materials_domain.py. No Qt here.
"""

import re

import validation

TYPES = ("member", "panel", "other")

# The eleven categories, in the order the list shows them -- the same as the permanent loads' prototype (issue #110, T17) -- and the words each is found by, in the three languages (REQ-011).
CATEGORIES = ("wood", "board", "ins", "tile", "memb", "gyps", "conc", "metal", "floor", "fill", "direct")
CATEGORY_TERMS = {
    "wood": "bois holz timber wood",
    "board": "panneau panneaux platte platten board boards",
    "ins": "isolation isolant dämmung daemmung insulation",
    "tile": "couverture tuile bedachung dach roofing roof",
    "memb": "étanchéité etancheite lé membrane abdichtung bahn bahnen waterproofing",
    "gyps": "plâtre platre enduit gips putz plaster gypsum",
    "conc": "béton beton maçonnerie maconnerie mauerwerk concrete masonry",
    "metal": "acier métal metal métaux verre stahl metall metalle glas steel metals glass",
    "floor": "sol sols revêtement boden bodenbelag floor flooring",
    "fill": "granulat granulats lestage gravier schüttung kies beschwerung fill ballast gravel",
    "direct": "charge charges installation last lasten load loads",
}
TYPE_TERMS = {
    "member": "barre barres stab stäbe member members bar",
    "panel": "panneau panneaux platte platten panel panels",
    "other": "autre autres andere anderes other",
}

# A member's family gives γ_M/η_M (SIA 265 Tabelle 1, `sia265.gamma_m`) and the design values the norm sets rather than deduces (3.3.2.2, 3.4.2.4).
FAMILIES = ("softwood", "hardwood", "glulam")
# The six strengths of a member, f_<s>_k beside f_<s>_d (SIA 265 Tabellen 8 and 9), and what is never deduced.
MEMBER_STRENGTHS = ("m", "t_0", "c_0", "t_90", "c_90", "v")
MEMBER_STIFFNESS = ("E_0_mean", "E_90_mean", "G_mean", "rho_k")
MEMBER_KEYS = tuple(k for s in MEMBER_STRENGTHS for k in ("f_%s_k" % s, "f_%s_d" % s)) + MEMBER_STIFFNESS

# A panel's grid, as SIA 265/1 Tabelle 19a (and every table of 11 to 23) lays it out: the loading, then its rows. A strength `f_…` carries `_k` and `_d`; a modulus only its mean.
PANEL_GRID = {
    "plate": ("f_m", "f_c_90", "f_v", "E_m_mean", "G_mean"),
    "shear": ("f_m", "f_v", "E_m_mean", "G_mean"),
    "axial": ("f_t", "f_c", "E_tc_mean"),
}
DIRECTIONS = ("par", "perp")
ISOTROPIC = ("all",)

UNITS = ("kN/m³", "kN/m²")
SOURCE_KINDS = ("none", "url", "pdf", "norm", "book")
LANGS = ("fr", "de", "en")
USER_ID = re.compile(r"^u-[0-9a-f]{8}$")


def is_strength(key):
    return key.startswith("f_")


def panel_keys(loading):
    """The keys a panel's grid holds under one loading: each strength as `_k` and `_d`, each modulus as it is."""
    out = []
    for row in PANEL_GRID[loading]:
        out.extend((row + "_k", row + "_d") if is_strength(row) else (row,))
    return tuple(out)


def directions(material):
    return ISOTROPIC if material.get("isotropic") else DIRECTIONS


def column_count(material):
    return max(len(material.get("columns") or []), 1)


def name(material, lang="fr"):
    """The name in `lang`, else the first the material has -- a material named in one language is shown so in the others."""
    names = material.get("names") or {}
    return names.get(lang) or next((names[l] for l in LANGS if names.get(l)), material.get("id", ""))


def _number(value, at, positive=False):
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise validation.ValidationError("%s: %r -- a number" % (at, value))
    if positive and value <= 0:
        raise validation.ValidationError("%s: %r -- a number above 0" % (at, value))


def check_material(m, where, products=None):
    """The business rules of one material, whatever file holds it -- a defect stops, naming `where` and the field. `products` is the set of SIA 265/1 products a panel may name (`sia265_1.products()`); None leaves it unchecked."""
    at = "%s[%s]" % (where, m.get("id") if isinstance(m, dict) else m)
    if not isinstance(m, dict):
        raise validation.ValidationError("%s: a material is an object" % at)
    if not str(m.get("id") or "").strip():
        raise validation.ValidationError("%s: no id" % at)
    if m.get("type") not in TYPES:
        raise validation.ValidationError("%s.type: %r -- %s" % (at, m.get("type"), ", ".join(TYPES)))
    if m.get("category") not in CATEGORIES:
        raise validation.ValidationError("%s.category: %r -- %s" % (at, m.get("category"), ", ".join(CATEGORIES)))
    names = m.get("names") or {}
    if not any(str(names.get(l) or "").strip() for l in LANGS):
        raise validation.ValidationError("%s.names: a name in fr, de or en" % at)
    weight = m.get("weight")
    if weight is not None:
        if weight.get("unit") not in UNITS:
            raise validation.ValidationError("%s.weight.unit: %r -- %s" % (at, weight.get("unit"), ", ".join(UNITS)))
        if weight.get("value") is None:
            raise validation.ValidationError("%s.weight.value: missing -- a weight above 0, or no weight at all" % at)
        _number(weight.get("value"), at + ".weight.value", positive=True)
    source = m.get("source") or {"kind": "none"}
    if source.get("kind") not in SOURCE_KINDS:
        raise validation.ValidationError("%s.source.kind: %r -- %s" % (at, source.get("kind"), ", ".join(SOURCE_KINDS)))
    if source.get("kind") == "pdf" and not source.get("file"):
        raise validation.ValidationError("%s.source.file: a PDF source names its copy" % at)
    if m["type"] == "member":
        if m.get("family") not in FAMILIES:
            raise validation.ValidationError("%s.family: %r -- %s" % (at, m.get("family"), ", ".join(FAMILIES)))
        values = m.get("values") or {}
        for key, value in values.items():
            if key not in MEMBER_KEYS:
                raise validation.ValidationError("%s.values.%s: not a value of a member -- %s" % (at, key, ", ".join(MEMBER_KEYS)))
            _number(value, "%s.values.%s" % (at, key), positive=True)
    elif any(k in m for k in ("family", "values")):
        raise validation.ValidationError("%s: a %s has no family nor member values" % (at, m["type"]))
    if m["type"] == "panel":
        if products is not None and m.get("product") is not None and m["product"] not in products:   # a panel of one's own may name no product: it then has no design value deduced
            raise validation.ValidationError("%s.product: %r -- a product of SIA 265/1 Tabelle 9: %s" % (at, m.get("product"), ", ".join(sorted(products))))
        n = column_count(m)
        for i, column in enumerate(m.get("columns") or []):
            _number(column.get("t_min"), "%s.columns[%d].t_min" % (at, i))
            _number(column.get("t_max"), "%s.columns[%d].t_max" % (at, i))
        _number(m.get("thickness"), at + ".thickness", positive=True)
        rho = m.get("rho_k") or [None] * n
        if len(rho) != n:
            raise validation.ValidationError("%s.rho_k: %d values for %d columns" % (at, len(rho), n))
        for i, value in enumerate(rho):
            _number(value, "%s.rho_k[%d]" % (at, i), positive=True)
        dirs = directions(m)
        for loading, rows in (m.get("grid") or {}).items():
            if loading not in PANEL_GRID:
                raise validation.ValidationError("%s.grid.%s: not a loading -- %s" % (at, loading, ", ".join(PANEL_GRID)))
            for key, cells in rows.items():
                if key not in panel_keys(loading):
                    raise validation.ValidationError("%s.grid.%s.%s: not a value of that loading -- %s" % (at, loading, key, ", ".join(panel_keys(loading))))
                for direction, values in cells.items():
                    if direction not in dirs:
                        raise validation.ValidationError("%s.grid.%s.%s.%s: %s" % (at, loading, key, direction, "an isotropic panel has one direction, «all»" if m.get("isotropic") else "∥ «par» or ⊥ «perp»"))
                    if len(values) != n:
                        raise validation.ValidationError("%s.grid.%s.%s.%s: %d values for %d columns" % (at, loading, key, direction, len(values), n))
                    for i, value in enumerate(values):
                        _number(value, "%s.grid.%s.%s.%s[%d]" % (at, loading, key, direction, i), positive=True)
    elif any(k in m for k in ("product", "grid", "columns")):
        raise validation.ValidationError("%s: a %s has no panel grid" % (at, m["type"]))


def check_ids_unique(materials, where):
    """Two materials of one file with one id stop the read, naming both."""
    seen = set()
    for m in materials:
        if m["id"] in seen:
            raise validation.ValidationError("%s: id %r is listed twice" % (where, m["id"]))
        seen.add(m["id"])
