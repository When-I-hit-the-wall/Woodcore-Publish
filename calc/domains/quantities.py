"""The quantities of what the position plans draw, by material and by section (issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, REQ-013, REQ-014, ARCH-002, ARCH-005, D-008; Q-014).

The engineer, 08.10.2026: «Afficher le résumé (les métrés) sur le plan : par matériau et par section, longueurs et volumes, avec le même périmètre au choix que dans *Positions* (tout ce qui est dessiné dans le document, un seul plan, ou des positions choisies).» -- and, asked: totals by material and section (Matériau · Section · Pièces · Longueur [m] · Volume [m³]), a total line per material, the volume of the timber alone.

Two steps, both pure -- no project, no file: `rows` reads every element a plan draws that carries a position into one row (its plan, its position, its material, its section, its length, its area, its volume), and `summary` adds the rows of a scope up by material and section. The export writes the rows and the totals of the whole project and of each plan (data/quantities.json); the report prints them, and adds up itself only the rows of the positions a call names, which tests/test_quantities.py holds equal to `summary`.

**What is measured, and how** -- one length per element, plan.element_length_m's, which the drawing writes beside it:

| element | length | area | volume |
|---|---|---|---|
| a line (a wall, a beam, a bracing member, a line Auflager or Abfangung) | along it | -- | rec: length × b × h; cir: length × π d²/4; a plate or a CLT panel on a line has no height on a plan: none |
| an area (a slab) | -- | its outline | a plate or a CLT panel: area × t; any other: none |
| a point (a column, a point Auflager) | -- (its height is not on a plan) | -- | none |

A steel profile is counted in length and has no volume: its area is in SZS C5's tables and in no file of this program (D-008). A position with no section is counted, with no volume, and said. Openings, concrete and loads carry no position and are not counted. A plan without a scale measures nothing and is said; its elements still count as pieces.
"""

import math

import validation

from domains import plan as plan_model
from domains import section

SCOPES = ("all", "plans", "positions")


def _material(row):
    """The material as the summary groups it: its name and its strength class as one, «Fichte C24» -- position-line's own -- or "" where neither is stated."""
    return " ".join(part for part in (str(row.get("material") or "").strip(), str(row.get("strength_class") or "").strip()) if part)


def rows(plan_sources, position_rows):
    """One row for every element the plans draw that carries a position of the project, in the plans' order and then the drawing's: {plan, position, kind, material, section, section_type, length_m, area_m2, volume_m3}, None where a value cannot be had -- and the notes of what could not be measured, (rows, notes)."""
    by_id = {row["position"]: row for row in position_rows}
    out, notes = [], []
    for source in plan_sources:
        pid = source.get("id", "")
        per_m = plan_model.units_per_m(source)
        if not per_m and any(plan_model.labelled(e["type"]) and not plan_model.is_load(e["type"]) for e in source.get("elements", [])):
            notes.append(f"plan {pid}: no scale -- its elements are counted, and nothing is measured")
        for element in source.get("elements", []):
            type_, label = element["type"], element.get("label", "")
            if plan_model.is_load(type_) or not plan_model.labelled(type_) or not label:
                continue
            position = by_id.get(label)
            if position is None:
                continue   # a number the project has no position of: the plan's own warning says so
            kind = plan_model.element_kind(element)
            try:
                shape = section.parse(position.get("section_type"), position.get("dimension"), position.get("units"), where=label)
            except validation.ValidationError:   # a section that does not read: no quantity, the position's own check says why
                shape = None
            length = plan_model.element_length_m(element, per_m) if kind == "line" else None
            area = plan_model.ring_area(element["points"]) / (per_m * per_m) if kind == "poly" and per_m else None
            volume = None
            code = (shape or {}).get("type")
            if kind == "line" and length is not None and code in ("rec", "cir"):
                volume = length * section.area_mm2({"section": shape}) / 1e6
            elif kind == "poly" and area is not None and code in ("pla", "clt"):
                volume = area * float(shape["t"]) / 1000.0
            if shape is None:
                notes.append(f"{label}: no section -- counted, with no volume")
            out.append({"plan": pid, "position": label, "kind": kind, "material": _material(position),
                        "section": section.display(position), "section_type": code or "",
                        "length_m": length, "area_m2": area, "volume_m3": volume})
    return out, list(dict.fromkeys(notes))


def _add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return a + b


def summary(all_rows, scope="all", plans=(), positions=()):
    """The rows of a scope added up: `all` every row, `plans` those of the plans named, `positions` those of the positions named. A list of groups, by material then section, each {material, section, pieces, length_m, area_m2, volume_m3} -- a value None where no row of the group has one --, and one total per material, {material, pieces, length_m, area_m2, volume_m3}: (groups, totals)."""
    if scope not in SCOPES:
        raise ValueError(f"scope {scope!r} -- expected one of {', '.join(SCOPES)}")
    if scope == "plans":
        chosen = [r for r in all_rows if r["plan"] in set(plans)]
    elif scope == "positions":
        chosen = [r for r in all_rows if r["position"] in set(positions)]
    else:
        chosen = list(all_rows)
    groups = {}
    for r in chosen:
        group = groups.setdefault((r["material"], r["section"]), {"material": r["material"], "section": r["section"], "pieces": 0,
                                                                 "length_m": None, "area_m2": None, "volume_m3": None})
        group["pieces"] += 1
        for key in ("length_m", "area_m2", "volume_m3"):
            group[key] = _add(group[key], r[key])
    ordered = [groups[key] for key in sorted(groups, key=lambda k: (k[0].lower(), k[1].lower()))]
    totals = {}
    for group in ordered:
        total = totals.setdefault(group["material"], {"material": group["material"], "pieces": 0, "length_m": None, "area_m2": None, "volume_m3": None})
        total["pieces"] += group["pieces"]
        for key in ("length_m", "area_m2", "volume_m3"):
            total[key] = _add(total[key], group[key])
    return ordered, list(totals.values())


def document(plan_sources, position_rows):
    """data/quantities.json: its rows, and the summary of the whole project and of each plan -- what the report prints, never computing them again. (document, notes)."""
    found, notes = rows(plan_sources, position_rows)
    groups, totals = summary(found)
    by_plan = {}
    for source in plan_sources:
        pid = source.get("id", "")
        g, t = summary(found, "plans", plans=[pid])
        by_plan[pid] = {"groups": g, "totals": t}
    return {"schema_version": "1.0", "rows": found, "all": {"groups": groups, "totals": totals}, "plans": by_plan}, notes


def length_by_position(all_rows):
    """The length every position is drawn with, all its elements on every plan added up -- {position: metres, or None where none of its elements has a length (a point, a slab, a plan without a scale)}. What the Positions tab lists beside each position (issue #14); `summary(rows, "positions", positions=[p])` gives the same, `tests/test_quantities.py` holds them equal."""
    out = {}
    for r in all_rows:
        out[r["position"]] = _add(out.get(r["position"]), r["length_m"])
    return out


def metres(value, digits=2):
    """A length or an area as the summary prints it, «12.34», or «—» where there is none."""
    return "—" if value is None or (isinstance(value, float) and math.isnan(value)) else f"{value:.{digits}f}"
