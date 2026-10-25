"""The values of SIA 265/1:2018 -- the wood-based panels -- out of the JSON files beside this module in `calc/norms/` (issue #110, spec docs/requirements/active/2026-10-24-onglet-materiaux.md, ARCH-002).

Built on `sia263.py`'s pattern: one file per table, `sia265-1-2018-<table>-<designation>.json`, each read off `norm-library/SIA265-1-2018-FR.pdf` -- the one edition the library ships -- at the page its `_source` names, and checked here before anything is built from it (docs/architecture/principles.md rule 13).

    sia265-1-2018-tab06-gamma-m.json          Tableau 6, γ_M of each group of panels (6.1.2.1), and note 1's γ_M = 1,0 in an accidental situation
    sia265-1-2018-tab07-08-kled.json          Tableaux 7 and 8, the load-duration classes (KLED) and the actions of SIA 261 in each (6.2.1.3), and 6.2.1.4
    sia265-1-2018-tab09-eta-mod.json          Tableau 9, η_mod by product, moisture class and KLED (6.2.1.4)
    sia265-1-2018-tab11 … tab23-*.json        Tableaux 11a/b to 23a/b, each panel's characteristic (a) and design (b) values

A panel of Tableaux 11 to 23 is stored in the shape of a material (`domains.materials_contract`): its columns -- one per range of thickness --, ρ_k per column, and its grid {plate|shear|axial: {key: {par|perp|all: [one per column]}}}. The b tables are the norm's design values for moisture class 1 and medium duration: Woodcore reads them, never deduces them; it deduces only what the engineer leaves empty in a panel of his own (`domains.materials_derive`).
"""

from pathlib import Path

import validation
from norms import _loader

HERE = Path(__file__).resolve().parent
EDITION = "SIA 265/1:2018"

TAB06 = "sia265-1-2018-tab06-gamma-m"
TAB09 = "sia265-1-2018-tab09-eta-mod"
TAB07 = "sia265-1-2018-tab07-08-kled"
PANEL_FILES = (
    "sia265-1-2018-tab11-contreplaque-f25-10",
    "sia265-1-2018-tab12-contreplaque-f40-f60",
    "sia265-1-2018-tab13-particules-p4",
    "sia265-1-2018-tab14-particules-p5",
    "sia265-1-2018-tab15-particules-p6",
    "sia265-1-2018-tab16-particules-p7",
    "sia265-1-2018-tab17-particules-ciment",
    "sia265-1-2018-tab18-osb2",
    "sia265-1-2018-tab19-osb3",
    "sia265-1-2018-tab20-osb4",
    "sia265-1-2018-tab21-fibres-hb-mbh",
    "sia265-1-2018-tab22-mdf-la",
    "sia265-1-2018-tab23-mdf-hls",
)
FILES = (TAB06, TAB07, TAB09) + PANEL_FILES

# The classes of load duration of Tableau 9's columns (Tableau 8) and the moisture classes it has rows for.
KLED = ("permanent", "long", "medium", "short", "very_short")
# What a design value of a panel of Tableaux 11b to 23b is given for, and what a panel of the engineer's own is deduced for (issue #110, T35).
DESIGN_CLASS, DESIGN_KLED = 1, "medium"

_cache = {}


def _read(stem):
    if stem not in _cache:
        data = _loader.load(HERE / ("%s.json" % stem))
        _loader.edition(stem, data, EDITION)
        _cache[stem] = data
    return _cache[stem]


def _table(stem):
    data = _read(stem)
    key = next((k for k in data if k.startswith("table_")), None)
    if key is None:
        _loader.fail(stem, "no table_<n> block")
    return data[key]


def edition():
    return EDITION


def groups():
    """Tableau 6's groups, by id: {id: {label, gamma_m}} -- γ_M is None where the norm leaves it to the product."""
    return {g["id"]: g for g in _table(TAB06)["groups"]}


def gamma_m(group):
    """γ_M of one group of Tableau 6 ("osb", "plywood"…). A group whose γ_M the norm leaves to the product stops, saying so."""
    found = groups().get(group)
    if found is None:
        _loader.fail(TAB06, "no group %r -- Tableau 6 gives %s" % (group, ", ".join(groups())))
    if found["gamma_m"] is None:
        _loader.fail(TAB06, "γ_M of %r is to be determined for the product (Tableau 6, note 2)" % group)
    return found["gamma_m"]


def accidental_gamma_m():
    """γ_M in an accidental design situation, earthquakes excepted -- Tableau 6, note 1 (issue #112, REQ-006)."""
    block = _table(TAB06).get("accidental")
    if not block or not isinstance(block.get("gamma_m"), (int, float)):
        _loader.fail(TAB06, "no accidental.gamma_m -- note 1 of Tableau 6 sets γ_M = 1,0 in an accidental design situation")
    return block["gamma_m"]


def design_gamma_m(product, accidental=False):
    """γ_M a design value of `product` is divided by: Tableau 6 through its group, or note 1's 1,0 in an accidental situation."""
    return accidental_gamma_m() if accidental else product_gamma_m(product)


def kled_classes():
    """Tableau 7: [{id, label, duration}] in Tableau 9's order -- the ids `KLED` names."""
    return _table(TAB07)["classes"]


def kled_actions():
    """Tableau 8: [{action, sia261, kled, note?}] -- what the choice of a KLED shows beside it."""
    return _read(TAB07)["table_8"]["rows"]


def admitted_classes(product):
    """The moisture classes Tableau 9 admits `product` in -- a row with at least one value (1, 2 for OSB/3; 1 alone for OSB/2)."""
    out = []
    for row in _table(TAB09)["rows"]:
        if product in row["products"] and any(v is not None for v in row["values"]) and row["class"] not in out:
            out.append(row["class"])
    return tuple(sorted(out))


def admitted_kled(product, moisture_class):
    """The KLED Tableau 9 gives a value of `product` for in `moisture_class` («na» left out: MDF.HLS in class 2 is short and very short only)."""
    for row in _table(TAB09)["rows"]:
        if product in row["products"] and row["class"] == moisture_class:
            return tuple(k for k, v in zip(KLED, row["values"]) if v is not None)
    return ()


def products():
    """Tableau 9's products, by id: {id: {group, label, standard}} -- what a panel's `product` names."""
    return _table(TAB09)["products"]


def product_gamma_m(product):
    """γ_M of a product, through its group of Tableau 6."""
    found = products().get(product)
    if found is None:
        raise validation.ValidationError("SIA 265/1: no product %r -- Tableau 9 gives %s" % (product, ", ".join(products())))
    return gamma_m(found["group"])


def eta_mod(product, moisture_class=DESIGN_CLASS, kled=DESIGN_KLED):
    """η_mod of Tableau 9 for one product, moisture class and KLED. A product the norm does not admit in that class -- no row, or «na» -- stops, naming them."""
    if kled not in KLED:
        raise validation.ValidationError("SIA 265/1 Tableau 9: KLED %r -- %s" % (kled, ", ".join(KLED)))
    for row in _table(TAB09)["rows"]:
        if product in row["products"] and row["class"] == moisture_class:
            value = row["values"][KLED.index(kled)]
            if value is None:
                break
            return value
    raise validation.ValidationError("SIA 265/1 Tableau 9: %r is not admitted in moisture class %s for KLED %s" % (product, moisture_class, kled))


def panel_tables():
    """Tableaux 11 to 23 as their files state them: [{number, title, title_b, page, fractile, products, notes}]."""
    return [_table(stem) for stem in PANEL_FILES]


def panels():
    """Every panel of Tableaux 11 to 23, one per product of the norm (a plywood of 3 plies and one of 5 are two): each the table's product, with `table` and `page` added."""
    out = []
    for stem, table in zip(PANEL_FILES, panel_tables()):
        for product in table["products"]:
            out.append(dict(product, table=table["number"], page=table["page"], file=stem))
    return out


def check():
    """Every file read and held together: one edition; each product of Tableau 9 in a group of Tableau 6; each panel naming a product of Tableau 9, its grid the shape of a material (`materials_contract`), its ρ_k one per column, and each id once. Raises naming the file and the field."""
    from domains import materials_contract as contract
    known = products()
    if tuple(c["id"] for c in kled_classes()) != KLED:
        _loader.fail(TAB07, "Tableau 7's classes %s are not Tableau 9's columns %s" % ([c["id"] for c in kled_classes()], list(KLED)))
    for row in kled_actions():
        if row["kled"] not in KLED:
            _loader.fail(TAB07, "Tableau 8: %r is in KLED %r -- %s" % (row["action"], row["kled"], ", ".join(KLED)))
    accidental_gamma_m()
    for pid, p in known.items():
        if p["group"] not in groups():
            _loader.fail(TAB09, "product %r is in group %r, not a group of Tableau 6" % (pid, p["group"]))
    for row in _table(TAB09)["rows"]:
        if len(row["values"]) != len(KLED):
            _loader.fail(TAB09, "row %r, class %s: %d values for %d KLED" % (row["label"], row["class"], len(row["values"]), len(KLED)))
    seen = set()
    for panel in panels():
        if panel["id"] in seen:
            _loader.fail(panel["file"], "panel %r is listed twice" % panel["id"])
        seen.add(panel["id"])
        material = dict(panel, type="panel", category="board", names={"fr": panel["label"]})
        for key in ("table", "page", "file", "label", "unavailable", "notes", "rho_k_is_minimum"):
            material.pop(key, None)
        contract.check_material(material, "calc/norms/%s.json: products" % panel["file"], set(known))
    return True
