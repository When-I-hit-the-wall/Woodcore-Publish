"""What the wind's tab is described by (spec 2026-10-23-onglet-vent-briques, V5: UI-001 to UI-027, ARCH-003, ARCH-004): the declaration of its form in four sections, the fields a source shows, the results «Résultats» lists, the data of its blocks, the links of its elements' keys and Figure 9 as a chart -- read by the services of the type «Calcul» (calc/tools/calc_tab.py) through `wind_source`, which imports them. Every number out of `wind_forces.analysis`, every building out of `wind_geometry`, every coefficient out of `norms/sia261_wind`; no word here but the tab's keys (`wi_…`, calc/tools/wind_tab_words.py), the glossary's and the norm's. No Qt.

**The form** (UI-003 to UI-007): 1 the basic data -- q_p0 with Annexe E's map, the terrain category, b · d · h on one line, z «= h», c_d --; 2 the building -- the table of Annexe C, what it says, the figure of the norm and the model in 3D --; 3 the reduction and force coefficients -- c_red of Figur 9, the force coefficients coloured, the global forces Q_k per φ with their c_red and A_ref, formula (15), the result in 3D of the forces --; 4 the pressure coefficients -- c_pe and c_pi coloured, the openings' column chosen marked, ĉ_pe, the detail per φ, the openings on the line of their words, the formula of q_k, the result in 3D of the loads.

**The right pane** (UI-019, D-34): under the values of «Résultats», the global forces Q_k at their φ and the walls, the roof, the measuring points and the local areas, pressure max and suction max at their φ; the module «Bâtiment», the table's facts and its figure or its model, one at a time (`views`, D-35).

**The keys** (ARCH-004): a cell of the norm's table `cell:<column>:<row>` (wind_forces.cell), a cell of the forces `Q:<force>:<row>`, a cell of the detail `q:<surface>:<row>`, a reference area `aref:<bh|dh|db>`, a surface of the model `surf:<surface>`, a result `var:<name>`, an extreme of a surface in the right pane `qx:<surface>:<max|min>`. `key_links` says what each lights and frames.
"""

import math

from domains import wind_forces, wind_geometry
from domains.contracts import Block, Choice, Declaration, Field
from norms import sia261_wind

PREFIX = "wi_"
NORM = "sia261-2020-wind-excerpts"
OPENINGS = ("rep", "A", "B", "C", "D")
TERRAINS = ("II", "IIa", "III", "IV")
VIEWS = (("view_a", "A"), ("view_c", "C"), ("view_iso", "iso"), ("view_top", "top"))
# The tables of the right pane, a group of surfaces each (wind_forces.surface_group), in the prototype's order (UI-019)
GROUPS = (("walls", "wall"), ("roofs", "roof"), ("points", "pt"), ("locs", "loc"))


def declaration():
    fields = (
        Field("q_p0", "number", "kN/m²", excerpts=("annexE", "6.2.1.3"), minimum=0.0, maximum=10.0, decimals=2, step=0.05, linkable=True, var="qp0"),
        Field("terrain", "select", "", choices=tuple(Choice(c, PREFIX + "c_" + c) for c in TERRAINS), excerpts=("tab4", "6.2.1.2"), var="gelaendekategorie"),
        Field("b", "number", "m", excerpts=("fig22", "6.2.2.3"), minimum=0.0, maximum=1000.0, decimals=2, step=0.5, linkable=True, var="b"),
        Field("d", "number", "m", excerpts=("fig22",), minimum=0.0, maximum=1000.0, decimals=2, step=0.5, linkable=True, var="d"),
        Field("h", "number", "m", excerpts=("fig22",), minimum=0.0, maximum=1000.0, decimals=2, step=0.5, linkable=True, var="h"),
        Field("z", "number", "m", excerpts=("6.2.2.3", "6.2.1.2"), minimum=0.0, maximum=1000.0, decimals=2, step=0.5, linkable=True, special_word="z_h", var="z"),
        Field("c_d", "number", "", excerpts=("6.3.5",), minimum=0.0, maximum=3.0, decimals=2, step=0.05, linkable=True, var="cd"),
        Field("table", "select", "", choices=tuple(Choice(n, PREFIX + "c_t" + n) for n in sia261_wind.NUMBERS), excerpts=("fig22",), var="tabelle"),
        Field("openings", "select", "", choices=tuple(Choice(o, PREFIX + "c_" + o) for o in OPENINGS), excerpts=("6.2.2.1", "6.2.3.3")),
    )
    blocks = (
        Block("facts", "text"), Block("figure", "excerpt"), Block("model", "model3d", pinnable=True), Block("building_views", "views", children=("figure", "model")),
        Block("cred", "heat_table"), Block("cf", "heat_table", wide=True, min_width=240), Block("forces", "heat_table", wide=True, min_width=320),
        Block("forces_formula", "formula"), Block("forces3d", "model3d", pinnable=True),
        Block("cp", "heat_table", wide=True, min_width=420), Block("peak", "text"), Block("perphi", "heat_table", wide=True, min_width=420),
        Block("openings_row", "row_select", field="openings"), Block("pressure_formula", "formula"), Block("loads3d", "model3d", pinnable=True),
        Block("res_forces", "heat_table", wide=True, min_width=220),
        *(b for key, _g in GROUPS for b in (Block("res_%s_title" % key, "text"), Block("res_" + key, "heat_table", wide=True, min_width=220))),
    )
    sections = (("basic", ("q_p0", "terrain", ("b", "d", "h"), "z", "c_d")),
                ("building", ("table", "facts", "building_views")),
                ("reduction", ("cred", "cf", "forces", "forces_formula", "forces3d")),
                ("pressure", ("cp", "peak", "perphi", "openings_row", "pressure_formula", "loads3d")))
    modules = (("results", ("res_forces", *(k for key, _g in GROUPS for k in ("res_%s_title" % key, "res_" + key)))),
               ("building", ("facts", "building_views")))
    return Declaration(PREFIX, NORM, sections, fields, blocks, modules)


def _table(src):
    return sia261_wind.table(src["table"]) if src.get("table") in sia261_wind.NUMBERS else None


def visible_fields(src):
    """Every field, the openings only for a table that has openings' columns (REQ-006: Tableaux 46-50 take each surface's own c_pi, 57a-d, 63 and 64 none)."""
    table = _table(src)
    keep = [f.key for f in declaration().fields]
    if table is None or not any(c["group"] == "cpi_opening" for c in table["columns"]):
        keep.remove("openings")
    return keep


def results(instance):
    """What «Résultats» lists, never an input: c_h, q_p, the two c_red; the global forces and the local pressures at their φ come after them, in the blocks the declaration puts there (UI-019, D-34)."""
    return [n for n in ("ch", "qp", "cred_bh", "cred_dh") if n in instance["vars"]]


def _n(value, digits=2):
    return ("%.*f" % (digits, value)).replace("-", "−")


def _analysis(src):
    try:
        return wind_forces.analysis(src)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def blocks(src, instance):
    """The data of the blocks (calc/tools/calc_blocks.py's shapes): what the table says, its figure, the models in 3D, the coloured tables, the formulas -- {} for a block that has nothing to show yet."""
    table = _table(src)
    if table is None:
        return {}
    number = table["number"]
    out = {"figure": {"norm": NORM, "id": "fig" + number}}
    a = _analysis(src) if instance is not None else None
    entered = ""
    if all(isinstance(src.get(k), (int, float)) and src[k] > 0 for k in ("b", "d", "h")):
        entered = "%s : %s : 1" % (_n(src["h"] / src["d"]), _n(src["b"] / src["d"]))
    out["facts"] = {"word": "facts", "params": {"ref": number, "title": _title(number), "ratio": table["ratio"], "roof": table["roof"], "entered": entered or "—"}}
    out["building_views"] = {"views": True}
    if wind_geometry.building(number) is not None:
        out["model"] = _model3d(number, lambda state: wind_geometry.scene(number, phi=state.get("phi", 0.0), words={"phi": "φ = {phi}°"}), phi=True)
    if a is None:
        return out
    out["cred"] = _cred(a, src)
    out["cf"], out["forces"] = _forces_tables(a)
    out["forces_formula"] = {"formula": 'Q_k = c_"red" dot c_d dot c_f dot q_p dot A_"ref"', "values": 'c_"red" dot %s dot c_f dot %s dot A_"ref"' % (_n(a["c_d"]), _n(a["q_p"], 3)), "ref": "6.2.3.2 (15)"}
    out["cp"] = _cp(a)
    if a["cpe_peak"] is not None:
        out["peak"] = {"word": "peak", "params": {"peak": _n(a["cpe_peak"], 1), "value": _n(a["q_peak"])}}
    out["perphi"] = _perphi(a)
    out.update(_pane_tables(a, instance))
    out["openings_row"] = {"word": "openings_words"}
    out["pressure_formula"] = {"formula": 'q_k = q_p dot (c_d dot c_"pe" - c_"pi")', "values": '%s dot (%s dot c_"pe" - c_"pi")' % (_n(a["q_p"], 3), _n(a["c_d"])), "ref": "(13) (14) (17) (18)"}
    if wind_geometry.building(number) is not None:
        rows = [r["label"] for r in table["rows"]]

        def forces(state):
            direction = state.get("direction") or wind_forces.MAX
            q = wind_forces.forces_at(a, direction, state.get("sign", "+"))
            return wind_geometry.scene(number, phi=_angle(direction), forces={k: (v, _n(v, 1) + " kN") for k, v in q.items()}, words={"phi": "φ = {phi}°"})

        def loads(state):
            direction = state.get("direction") or wind_forces.MAX
            return wind_geometry.scene(number, phi=_angle(direction), loads=wind_forces.loads_at(a, direction, state.get("sign", "+")), show_forces=False, words={"phi": "φ = {phi}°"})
        out["forces3d"] = _model3d(number, forces, directions=rows, signs=(("+", "force_pos"), ("-", "force_neg")))
        out["loads3d"] = _model3d(number, loads, directions=rows, signs=(("+", "load_pos"), ("-", "load_neg")))
    return out


def _title(number):
    """The title of Tableau `number` in each edition, as the norm prints it after its number (D-35)."""
    from norms import excerpts
    out = {}
    for lang in ("fr", "de"):
        e = excerpts.excerpt(NORM, "tab" + number, lang)
        out[lang] = " ".join(e.text[len(e.ref):].split()).replace(" ,", ",")
    return out


def _at(value, unit, phi):
    return "%s %s (%s)" % (value, unit, phi) if unit else "%s (%s)" % (value, phi)


def _pane_tables(a, instance):
    """The right pane's tables (UI-019, D-34): each global force's largest and smallest with their φ -- Q_k in kN, q_k per m² where no area is known --, and for each group of surfaces the largest pressure and suction q_k with their φ, «—» where there is none; a cell hovered lights its surface and frames the c_pe and c_pi that gave it."""
    out = {}
    rows = []
    labels = [r["label"] for r in a["table"]["rows"]]
    for f in a["forces"]:
        if f["direct"] or f["max"] is None:
            continue
        per_area = f["area"] is not None
        cells = []
        for kind in ("max", "min"):
            x = f[kind]
            value = x["Q"] if per_area else x["q"]
            name = ("Qk_%s_%s" if per_area else "qk_%s_%s") % (kind, f["name"])
            cells.append({"value": value, "text": _at(_n(value, 1 if per_area else 2), "kN" if per_area else "kN/m²", labels[x["row"]]),
                          "id": "var:" + name if instance is None or name in instance["vars"] else "Q:%s:%d" % (f["name"], x["row"])})
        rows.append({"label": ("Q_k,%s" if per_area else "q_k,%s") % f["name"][2:], "cells": cells})
    if rows:
        out["res_forces"] = {"columns": [{"label": "max"}, {"label": "min"}], "legend": False, "rows": rows}
    for key, group in GROUPS:
        surfaces = [s for s in a["local"] if s["group"] == group and s["max"] is not None]
        if not surfaces:
            continue
        table_rows = []
        for s in surfaces:
            cells = []
            for kind, wanted in (("max", lambda q: q > 0), ("min", lambda q: q < 0)):
                x = s[kind]
                shown = wanted(x["q"])
                cells.append({"value": x["q"] if shown else None, "text": _at(_n(x["q"]), "", x["phi"]) if shown else "—",
                              "id": "qx:%s:%s" % (s["surface"], kind), "keys": ["surf:" + s["surface"]]})
            table_rows.append({"label": s["surface"], "cells": cells})
        out["res_%s_title" % key] = {"word": "res_" + key}
        out["res_" + key] = {"columns": [{"label": "Druck max [kN/m²]"}, {"label": "Sog max [kN/m²]"}], "legend": False, "rows": table_rows}
    return out


def _angle(direction):
    """The direction a result in 3D shows φ at: the row's own angle, none for «every direction»."""
    if direction == wind_forces.MAX:
        return None
    angle = sia261_wind.direction(direction)
    return angle


def _model3d(number, build, phi=False, directions=(), signs=()):
    data = {"build": build, "views": [(word, *wind_geometry.VIEWS[view]) for word, view in VIEWS], "phi": phi, "phi_label": "phi", "key_prefix": "surf:", "words": True}
    if directions:
        data.update(directions=list(directions), max="max", signs=list(signs))
    return data


def _cred(a, src):
    """c_red of Figur 9 for b·h and d·h, the oblique directions' and the roof's (6.3.2, 6.3.3), each row a reference area that lights its face (UI-013)."""
    cred = a["cred"]
    rows = [("b·h", "b/h = %s" % _n(src["b"] / src["h"]), cred["bh"], "aref:bh", "cred_bh"), ("d·h", "d/h = %s" % _n(src["d"] / src["h"]), cred["dh"], "aref:dh", "cred_dh"),
            ("schräg", "", cred["max"], "aref:oblique", "cred_oblique"), ("d·b", "", 1.0, "aref:db", "cred_roof")]
    return {"columns": [{"label": "β"}, {"label": "c_red"}], "colour": False,
            "rows": [{"label": area, "cells": [{"text": beta or "", "id": key}, {"value": round(value, 3), "id": key + ":c"}]} for area, beta, value, key, _w in rows]}


def _forces_tables(a):
    """The force coefficients of the table coloured, and the global forces Q_k per φ with their c_red, the extremes marked, A_ref under them (UI-006)."""
    forces = [f for f in a["forces"] if not f["direct"]]
    rows = a["table"]["rows"]
    cf = {"columns": [{"label": "c_" + f["name"][1:], "key": f["key"]} for f in forces], "legend": False,
          "rows": [{"label": row["label"], "cells": [{"value": a["table"]["rows"][r]["values"][[c["key"] for c in a["table"]["columns"]].index(f["key"])], "id": wind_forces.cell(f["key"], r)} for f in forces]}
                   for r, row in enumerate(rows)]}
    table_rows = []
    for r, row in enumerate(rows):
        cells = []
        for f in forces:
            values = f["rows"][r]["values"]
            numbers = [v["Q"] if f["area"] is not None else v["q"] for v in values]
            text = " / ".join(_n(x, 1 if f["area"] is not None else 2) for x in numbers) if numbers else "–"
            mark = any(v is f["max"] or v is f["min"] for v in values)
            cells.append({"value": max(numbers, key=abs) if numbers else None, "text": text + (" ◆" if mark else ""), "id": "Q:%s:%d" % (f["name"], r)})
        table_rows.append({"label": "%s · c_red %s" % (row["label"], _n(f["rows"][r]["c_red"], 3)) if forces else row["label"], "cells": cells})
    table_rows.append({"label": "A_ref", "cells": [{"text": ("%s = %s m²" % (_area_label(f), _n(f["area"], 1))) if f["area"] is not None else _area_label(f), "id": "Q:%s:aref" % f["name"]} for f in forces]})
    return cf, {"columns": [{"label": "Q_k,%s [%s]" % (f["name"][2:], "kN" if f["area"] is not None else "kN/m²")} for f in forces], "legend": True, "rows": table_rows}


def _area_label(f):
    factor = f["column"].get("area_factor")
    return ("%s·%s" % (("%g" % factor).replace(".", ","), f["column"]["area"])) if factor else f["column"]["area"]


def _cp(a):
    """The table of the norm's pressure coefficients in colour (UI-007): c_pe of every surface and the local ones, the openings' c_pi -- the column chosen marked -- or each surface's own."""
    table = a["table"]
    cols = [c for c in table["columns"] if c["group"] in ("cpe", "cpe_local", "cpi_opening", "cpi")]
    index = {c["key"]: i for i, c in enumerate(table["columns"])}
    label = lambda c: ("c_pi " + ("glm." if c["opening"] == "rep" else c["opening"])) if c["group"] == "cpi_opening" else (("c_pi " if c["group"] == "cpi" else "") + c["surface"])
    return {"columns": [{"label": label(c), "key": c["key"], "marked": c["key"] == a["opening_key"]} for c in cols], "legend": True,
            "rows": [{"label": row["label"], "cells": [{"value": row["values"][index[c["key"]]], "id": wind_forces.cell(c["key"], r),
                                                         "keys": [wind_forces.cell(c["key"], r, s) for s in (0, 1)] + ([("surf:" + c["surface"])] if c.get("surface") else [])}
                                                        for c in cols]}
                     for r, row in enumerate(table["rows"])]}


def _perphi(a):
    """q_k of each surface at each direction, coloured, its largest and smallest where a pair gives two (UI-007): always shown, as wide as the pane, scrolling below its width."""
    surfaces = a["local"]
    rows = []
    for r, row in enumerate(a["table"]["rows"]):
        cells = []
        for s in surfaces:
            qs = [v["q"] for v in s["rows"][r]["values"]]
            if not qs:
                cells.append({"value": None, "id": "q:%s:%d" % (s["surface"], r)})
                continue
            hi, lo = max(qs), min(qs)
            cells.append({"value": max(qs, key=abs), "text": _n(hi) if math.isclose(hi, lo) else "%s / %s" % (_n(hi), _n(lo)), "id": "q:%s:%d" % (s["surface"], r), "keys": ["surf:" + s["surface"]]})
        rows.append({"label": row["label"], "cells": cells})
    return {"columns": [{"label": s["surface"]} for s in surfaces], "legend": True, "rows": rows}


def key_links(src, instance):
    """What each element of the tab lights and frames (ARCH-004, UI-021): a cell of the detail per φ its surface on the model and the c_pe and c_pi that gave it, framed; a cell of the forces its column and its results; a result Q_k its column, its extreme framed; a reference area its face; a surface of the model its column of coefficients and its row of the detail."""
    a = _analysis(src)
    if a is None:
        return {}
    out = {}
    rows = a["table"]["rows"]
    for s in a["local"]:
        surf = "surf:" + s["surface"]
        column = [wind_forces.cell(s["key"], r) for r in range(len(rows))]
        out[surf] = {"lit": column + ["q:%s:%d" % (s["surface"], r) for r in range(len(rows))]}
        for r, row in enumerate(s["rows"]):
            keys = [k for v in row["values"] for k in v["keys"]]
            out["q:%s:%d" % (s["surface"], r)] = {"lit": [surf], "emphasis": keys}
        for kind in ("max", "min"):
            if s[kind] is not None:
                out["qx:%s:%s" % (s["surface"], kind)] = {"lit": [surf, "q:%s:%d" % (s["surface"], s[kind]["row"])], "emphasis": s[kind]["keys"]}
    for f in a["forces"]:
        if f["direct"]:
            continue
        cells = ["Q:%s:%d" % (f["name"], r) for r in range(len(rows))]
        names = [n for n in ("Qk_max_" + f["name"], "Qk_min_" + f["name"], "qk_max_" + f["name"], "qk_min_" + f["name"]) if instance is None or n in instance["vars"]]
        for cell in cells:
            out[cell] = {"lit": cells + ["var:" + n for n in names]}
        for kind in ("max", "min"):
            extreme = f[kind]
            for n in ("Qk_%s_%s" % (kind, f["name"]), "qk_%s_%s" % (kind, f["name"])):
                out["var:" + n] = {"lit": cells, "emphasis": ["Q:%s:%d" % (f["name"], extreme["row"])] if extreme else []}
    roof = sorted({s["surface"] for s in a["local"] if wind_forces.surface_group({"group": "cpe", "surface": s["surface"]}) == "roof"})
    out["aref:bh"] = {"lit": ["surf:A"]}
    out["aref:dh"] = {"lit": ["surf:C"]}
    out["aref:db"] = {"lit": ["surf:" + s for s in roof]}
    return out


def chart(src):
    """Figur 9 as the interactive chart of the right pane: c_red against h along each curve of β, and the case's two facades marked."""
    clause = sia261_wind.clause()["c_red"]
    series = [{"name": "β = %g" % curve["beta"], "points": [(p[0], p[1]) for p in curve["points"]]} for curve in clause["curves"]]
    marks = []
    if all(isinstance(src.get(k), (int, float)) and src[k] > 0 for k in ("b", "d", "h")):
        h = min(src["h"], 100.0)
        for area, side in (("b·h", "b"), ("d·h", "d")):
            beta = src[side] / src["h"]
            marks.append({"label": "h", "x": h, "y": sia261_wind.c_red(src["h"], beta), "series": area})
    return {"x": {"min": 0.0, "max": 100.0, "label": "h", "unit": "m", "step": 20.0}, "y": {"min": 0.5, "max": 1.0, "label": "c_red", "unit": "", "step": 0.1},
            "series": series, "marks": marks}
