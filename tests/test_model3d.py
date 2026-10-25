"""The 3D model, without Qt (calc/domains/model3d.py; spec 2026-10-23-onglet-vent-briques, ARCH-007, UI-008 to UI-017), on the wind's buildings (calc/domains/wind_geometry.py) where a building is needed.

What is held:

* **no Qt** in the module, and no word of a domain;
* **the scale** is the same at every rotation, the zoom bounded so that the building is between a quarter of the drawing and five times it, about its centre; Face A and Face C look square onto their face (UI-009);
* **what is not seen is not drawn**: in Face A of Tableau 32 only the letter A -- no E, F, G, H, m, n, no Q₁ seen end on, no φ = 0° (UI-010);
* **the strips lie in their face's plane**, a strip across a ridge cut in two, one a slope (UI-011);
* **the direction φ**: at 0° along Q₁, at 90° along Q₂, 360° the same as 0°, an arc from 0° (UI-012);
* **a face lit is drawn through the model**, a reference area alone (UI-013);
* **the forces** at the scale of the largest (UI-015); **the loads** a plane each, the faces neutral, the arrows by their sign, two planes on a face that carries a strip, no two values on one another, no value on its arrow (UI-016, UI-017).
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import math
import re

import conftest
from domains import model3d as m3
from domains import wind_forces, wind_geometry, wind_source

MODULE = conftest.ROOT / "calc" / "domains" / "model3d.py"


def _items(number, view, **options):
    return m3.render(wind_geometry.scene(number, **options), view)


def test_the_model_imports_no_qt_and_names_no_domain():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imported = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)} | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not {"PySide6", "PyQt5", "PyQt6"} & imported
    code = " ".join(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and not n.value.startswith(("A 3D model", "\n")))
    for word in ("wind", "vent", "cpe", "Tableau"):
        assert not re.search(r"\b" + word + r"\b", code), word


def test_the_scale_does_not_change_with_the_rotation_and_the_zoom_is_bounded():
    """UI-009: one scale for every yaw and pitch, computed on the sphere that holds the building, its forces and φ; the zoom kept between a quarter of the drawing's width and five times it, about the centre."""
    sc = wind_geometry.scene("36", phi=30)
    scales = {round(m3.projector(sc, m3.View(yaw=y, pitch=p)).scale, 9) for y, p in ((-131, 28), (0, 0), (75, 60), (-90, 90))}
    assert len(scales) == 1
    low, high = m3.projector(sc, m3.View(zoom=0.0001)), m3.projector(sc, m3.View(zoom=1000))
    assert low.zoom == low.zoom_min and high.zoom == high.zoom_max and math.isclose(high.zoom_max / low.zoom_min, 20)
    assert math.isclose(sc.width * low.scale * low.zoom, 0.25 * 460) and math.isclose(sc.width * high.scale * high.zoom, 5 * 460)
    view = m3.View(zoom=3)
    pr = m3.projector(sc, view)
    assert pr(sc.centre)[:2] == (view.width / 2, view.height / 2), "zoomed about the centre: the view does not move"


def test_face_a_and_face_c_look_square_onto_their_face():
    yaw, pitch = wind_geometry.VIEWS["A"]
    assert all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(m3.eye(m3.View(yaw=yaw, pitch=pitch)), (-1, 0, 0)))
    yaw, pitch = wind_geometry.VIEWS["C"]
    assert all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(m3.eye(m3.View(yaw=yaw, pitch=pitch)), (0, -1, 0)))


def test_what_is_seen_edge_on_or_from_behind_is_not_drawn():
    """UI-010: Tableau 32 in Face A -- the letter A alone of its surfaces, no roof, no strip, no Q₁ seen end on, no φ = 0° along the line of sight."""
    yaw, pitch = wind_geometry.VIEWS["A"]
    items = _items("32", m3.View(yaw=yaw, pitch=pitch), phi=0)
    shown = set(m3.texts(items))
    assert "A" in shown and not shown & {"E", "F", "G", "H", "m", "n", "Q₁", "φ = 0°", "B"}, shown
    assert {it["key"] for it in items if it["kind"] == "polygon" and it["key"]} <= {"A"}


def test_the_strips_lie_in_their_face_and_one_across_the_ridge_is_cut_in_two():
    """UI-011: every corner of m, n, o in the plane of the face it lies on (lifted by a hair); Tableau 36's n along C from the middle stays on one slope, Tableau 33's strip along C across the ridge is two polygons, one a slope."""
    mdl = wind_geometry.model("36")
    for poly, _label in mdl.faces:
        if getattr(poly, "layer", 0) != 1:
            continue
        a = poly.points[0]
        for p in poly.points:
            assert abs(sum((p[k] - a[k]) * poly.normal[k] for k in range(3))) < 1e-9, poly.key
    across = [poly for poly, _l in wind_geometry.model("42").faces if getattr(poly, "key", "") == "n" and getattr(poly, "layer", 0) == 1]
    assert len(across) == 8, "Tableau 42's n along C across its four sheds: one polygon a slope"
    assert len({tuple(round(c, 6) for c in poly.normal) for poly in across}) == 2, "the steep slopes and the shallow ones"


def test_the_direction_turns_about_the_building_and_points_at_it():
    """UI-012: φ = 0° along +x, Q₁'s sense, φ = 90° along +y, Q₂'s; 360° is 0°; an arc from 0° to φ."""
    for phi, sense in ((0, (1, 0)), (90, (0, 1))):
        arrow = next(p for p in wind_geometry.scene("36", phi=phi).primitives if isinstance(p, m3.Arrow) and p.key == "phi")
        d = (arrow.head[0] - arrow.tail[0], arrow.head[1] - arrow.tail[1])
        length = math.hypot(*d)
        assert math.isclose(d[0] / length, sense[0], abs_tol=1e-9) and math.isclose(d[1] / length, sense[1], abs_tol=1e-9)
    same = [next(p for p in wind_geometry.scene("36", phi=a).primitives if isinstance(p, m3.Arrow) and p.key == "phi") for a in (0, 360)]
    assert same[0].tail == same[1].tail and same[0].label == same[1].label == "φ = 0°"
    arc = [p for p in wind_geometry.scene("36", phi=60).primitives if isinstance(p, m3.Line) and p.role == "direction" and not p.dash]
    assert len(arc) == 24 and not [p for p in wind_geometry.scene("36", phi=0).primitives if isinstance(p, m3.Line) and p.role == "direction" and not p.dash]


def test_a_face_lit_is_drawn_through_the_model_and_a_reference_area_lights_alone():
    """UI-013: wall B, behind the building in the iso view, lit -- drawn whole over everything; lit, only its own key."""
    view = m3.View()
    sc = wind_geometry.scene("36")
    plain = m3.render(sc, view)
    assert "B" not in {it["key"] for it in plain if it["kind"] == "polygon"}, "B is behind"
    lit = m3.render(sc, view, lit={"B"})
    over = [it for it in lit if it.get("lit")]
    assert over and {it["key"] for it in over} == {"B"} and lit[-1]["key"] == "B"


def test_the_forces_are_scaled_to_the_largest_with_their_value():
    """UI-015: Tableau 36's forces at every direction's extreme -- the longest arrow the largest force, the others in proportion (0.35 + 0.65 share), each labelled with its value in kN; a suction points away from its face."""
    src = wind_source.new_source("WL-01")
    src.update(table="36", b=24, d=12, h=6)
    result = wind_forces.analysis(src)
    q = wind_forces.forces_at(result, sign="-")
    forces = {k: (v, "%.1f kN" % v) for k, v in q.items()}
    arrows = {p.key: p for p in wind_geometry.scene("36", forces=forces).primitives if isinstance(p, m3.Arrow) and p.key.startswith("force:")}
    assert set(arrows) == {"force:f3"}, "Q₁ and Q₂ at nought: their label alone"
    lengths = {}
    q = wind_forces.forces_at(result)
    forces = {k: (v, "%.1f kN" % v) for k, v in q.items()}
    for p in wind_geometry.scene("36", forces=forces).primitives:
        if isinstance(p, m3.Arrow) and p.key.startswith("force:"):
            lengths[p.key[6:]] = math.dist(p.tail, p.head)
            assert p.label.endswith(" kN") and ("%.1f" % q[p.key[6:]]) in p.label
            assert p.role == ("pressure" if q[p.key[6:]] > 0 else "suction")
    bare = {p.key[6:]: math.dist(p.tail, p.head) for p in wind_geometry.scene("36").primitives if isinstance(p, m3.Arrow) and p.key.startswith("force:")}
    largest = max(abs(v) for v in q.values())
    for name, length in lengths.items():
        assert math.isclose(length / bare[name], 0.35 + 0.65 * abs(q[name]) / largest), name
    assert result["forces"][0]["max"]["Q"] == q["f1"], "the result's own Q_k"


def test_the_loads_are_planes_held_by_arrows_by_their_sign_and_their_values_never_overlap():
    """UI-016, UI-017: Tableau 36's largest suctions -- the faces neutral, a plane and arrows per surface seen, the arrows pointing away from the face (a suction) in the suction's colour, two planes on the roof part that carries a strip, no two values on one another, no value on an arrow."""
    src = wind_source.new_source("WL-01")
    src.update(table="36", b=24, d=12, h=6)
    loads = wind_forces.loads_at(wind_forces.analysis(src), sign="-")
    sc = wind_geometry.scene("36", loads=loads, show_forces=False, phi=None)
    items = m3.render(sc, m3.View())
    faces = [it for it in items if it["kind"] == "polygon" and it["key"]]
    assert all(it["role"] in ("face", "roof", "strip") for it in faces), "no face coloured"
    planes = [p for p in sc.primitives if isinstance(p, m3.Polygon) and p.layer == 2]
    assert all(p.role == "suction" for p in planes) and len(planes) >= len(loads)
    keyed = {(p.layer, round(p.points[0][0], 6)) for p in sc.primitives if isinstance(p, m3.Polygon) and p.key in ("m", "G") and p.layer in (0, 1)}
    assert "m" in loads and "G" in loads and len([p for p in planes]) >= 2, "a strip's plane beside its face's"
    for poly in [p for p in sc.primitives if isinstance(p, m3.Polygon) and p.layer == 2]:
        assert poly.opacity < 0.2, "a plane, not a coloured face"
    suction = [p for p in sc.primitives if isinstance(p, m3.Arrow) and p.width == 1.3]
    assert suction and all(p.role == "suction" and p.hide_owner is not None and sum((p.head[k] - p.tail[k]) * p.hide_owner[k] for k in range(3)) > 0 for p in suction), "away from the face"
    values = [it for it in items if it["kind"] == "text" and it["text"].endswith("kN/m²")]
    boxes = [m3.text_box(it["x"], it["y"], it["text"], it["size"], it["anchor"]) for it in values]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert not m3._overlap(a, b), (a, b)
    # an arrow's label stands beyond its far end, never on its shaft
    for it in items:
        if it["kind"] == "text" and it.get("arrow"):
            box = m3.text_box(it["x"], it["y"], it["text"], it["size"], it["anchor"])
            (x1, y1), (x2, y2) = it["arrow"]
            for t in [i / 20 for i in range(21)]:
                x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                assert not (box[0] < x < box[0] + box[2] and box[1] < y < box[1] + box[3]), it["text"]


def test_the_svg_holds_what_is_seen_and_a_point_picks_the_face_on_top():
    view = m3.View()
    items = _items("36", view, phi=30)
    svg = m3.to_svg(items, view)
    assert svg.startswith("<svg") and 'data-key="A"' in svg and 'data-key="B"' not in svg
    face_a = next(it for it in items if it["kind"] == "polygon" and it["key"] == "A")
    x = sum(p[0] for p in face_a["points"]) / len(face_a["points"])
    y = sum(p[1] for p in face_a["points"]) / len(face_a["points"])
    assert m3.pick(items, x, y) in ("A", "o")
