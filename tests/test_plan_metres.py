"""A column turned, the lengths written element by element, and the plan's quantities in its legend (calc/domains/plan.py, plan_svg.py; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-013, REQ-020).

The engineer, 07.10.2026: «pouvoir tourner les poteaux» -- «un carré comme aujourd'hui, qu'il est possible de tourner (e.g. 30°)» · «on doit pouvoir activer ou désactiver le fait que la longueur des éléments soient indiqués (longueur de chaque mur, chaque T, longueur de chaque côté de dale). En sélectionnant un unique objet, on doit pouvoir activer ou désactiver cet affichage pour un unique élément. Ensuite, dans légende, il doit y avoir en plus, sous le descriptif des symboles, les métrés totaux par type d'objet.» The decimal is a point in the three languages (docs/decisions.md, v0.52).
"""

import copy
import re

import validation
from domains import fire
from domains import plan as model
from domains import plan_svg


def _plan():
    """A plan calibrated at 100 sheet units a metre, with two walls of 4.00 m and 2.50 m, a beam of 3.00 m, a slab of 3 x 4 m and two columns."""
    source = model.new_source("P99", floor="0")
    source["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1.0}   # a blank sheet is calibrated; 1:n is a PDF's
    m = model.units_per_m(source)
    source["elements"] = [
        {"type": "V", "label": "V001", "points": [[0, 0], [4 * m, 0]]},
        {"type": "V", "label": "V002", "points": [[0, 10 * m], [0, 12.5 * m]]},
        {"type": "T", "label": "T001", "points": [[5 * m, 5 * m], [8 * m, 5 * m]]},
        {"type": "D", "subtype": "normal", "label": "D001", "points": [[20 * m, 0], [23 * m, 0], [23 * m, 4 * m], [20 * m, 4 * m]]},
        {"type": "S", "label": "S001", "points": [[30 * m, 30 * m]]},
        {"type": "S", "label": "S002", "points": [[31 * m, 30 * m]], "angle": 30},
    ]
    return source


def test_a_column_turns_about_its_centre_and_a_plan_without_an_angle_is_drawn_as_before():
    source = _plan()
    model.check_source(source, "P99.json")
    svg = plan_svg.render(source)
    assert re.search(r'<rect [^>]*transform="rotate\(30[ .0-9]* ', svg), "the column turned by 30° is drawn turned"
    plain = copy.deepcopy(source)
    del plain["elements"][5]["angle"]
    assert 'transform="rotate(30' not in plan_svg.render(plain)
    # a turn is for a column or a point Auflager only
    wall = copy.deepcopy(source)
    wall["elements"][0]["angle"] = 10
    try:
        model.check_source(wall, "P99.json")
    except validation.ValidationError as exc:
        assert "may be turned" in str(exc)
    else:
        raise AssertionError("a wall took an angle")


def test_a_plan_of_1_3_is_read_as_it_is_and_one_saved_is_1_4():
    source = _plan()
    del source["elements"][5]["angle"]
    source["schema_version"] = "1.3"
    model.check_source(source, "P99.json")
    assert model.new_source("P98")["schema_version"] == "1.6" == model.SOURCE_SCHEMA_VERSION   # 1.5 since issue #9: a plan's dimensions; 1.6 since issue #18: its construction aids


def test_the_lengths_follow_the_plan_unless_an_element_says_otherwise():
    source = _plan()
    wall, beam, slab = source["elements"][0], source["elements"][2], source["elements"][3]
    assert not any(model.shows_length(source, e) for e in source["elements"]), "off by default"
    source["show_lengths"] = True
    assert model.shows_length(source, wall) and model.shows_length(source, beam) and model.shows_length(source, slab)
    assert not model.shows_length(source, source["elements"][4]), "a column has no length"
    svg = plan_svg.render(source)
    assert "4.00 m" in svg and "3.00 m" in svg, "a wall's and a beam's length, the decimal a point"
    assert svg.count("4.00 m") >= 2 and "3.00 m" in svg, "each side of the slab"
    wall["show_length"] = False
    assert "4.00 m" in plan_svg.render(source) and not model.shows_length(source, wall)
    source["show_lengths"] = False
    beam["show_length"] = True
    svg = plan_svg.render(source)
    assert "3.00 m" in svg and "2.50 m" not in svg, "the beam alone, as it says"
    model.check_source(source, "P99.json")
    no_scale = copy.deepcopy(source)
    no_scale.pop("scale")
    assert not model.shows_length(no_scale, no_scale["elements"][2]), "nothing is measured without a scale"


def test_the_legend_carries_the_quantities_by_kind_of_symbol():
    source = _plan()
    measured = model.quantities(source)
    assert measured["V"] == {"value": 6.5, "unit": "m"}, measured
    assert measured["T"] == {"value": 3.0, "unit": "m"}
    assert measured["D:normal"] == {"value": 12.0, "unit": "m2"}
    assert measured["S"] == {"value": 2, "unit": "pcs"}
    items = {item["key"]: item for item in plan_svg.legend_items(source)}
    assert items["V"]["quantity"] == {"value": 6.5, "unit": "m"}
    validation.validate_structure({"schema_version": model.EXPORT_SCHEMA_VERSION, "plans": {}}, "plans")
    no_scale = copy.deepcopy(source)
    no_scale.pop("scale")
    assert model.quantities(no_scale) == {} and all("quantity" not in i for i in plan_svg.legend_items(no_scale))


def test_one_measure_of_a_length_is_read_by_the_drawing_the_export_and_the_quantities():
    """Issue #9 (REQ-012): a wall's length is computed once, `plan.element_length_m`, and written the one way, `plan.metres_text` -- the export's `length_m`, the text beside it and the legend's total cannot disagree by a rounding."""
    source = _plan()
    source["elements"][0]["points"][1][0] = 412.3456     # 4.123456 m: a length the rounding would tell apart
    source["show_lengths"] = True
    per_m = model.units_per_m(source)
    wall = source["elements"][0]
    assert model.element_length_m(wall, per_m) == model.distance_m(*wall["points"], per_m) == 4.123456
    assert model.element_length_m(source["elements"][4], per_m) is None and model.element_length_m(wall, None) is None
    assert model.element_length_m(source["elements"][3], per_m) == 14.0, "a slab's is its perimeter"
    record = model.build_record(source, (4000.0, 4000.0))
    by_label = {e["label"]: e for e in record["elements"]}
    assert by_label["V001"]["length_m"] == 4.123456
    assert model.metres_text(4.123456) in plan_svg.render(source)
    assert model.quantities(source)["V"]["value"] == round(4.123456 + 2.5, 2)


def test_one_rule_says_what_turns_and_one_writes_its_angle():
    """Issue #9 (REQ-002): `is_rotatable`, `set_element_angle` and `snap_angle` are the one rule and the one normalisation the source's check, the angle field and the circle a selected column turns by all read -- 180° is 180°, wherever it was typed or dragged."""
    column = {"type": "S", "label": "S101", "points": [[0, 0]]}
    point_m, line_m = {"type": "M", "subtype": "vert", "points": [[0, 0]]}, {"type": "M", "subtype": "vert", "points": [[0, 0], [9, 0]]}
    assert model.is_rotatable(column) and model.is_rotatable(point_m) and not model.is_rotatable(line_m)
    assert not model.is_rotatable({"type": "T", "points": [[0, 0], [1, 0]]})
    assert model.set_element_angle(column, 30) and column["angle"] == 30
    assert not model.set_element_angle(column, 390), "390° is 30°: nothing changed"
    assert model.set_element_angle(column, -180) and column["angle"] == 180
    assert model.set_element_angle(column, 360) and "angle" not in column, "0 takes the field off: the plan reads as one never turned"
    assert model.snap_angle(37) == 30 and model.snap_angle(38) == 45 and model.snap_angle(-172) == -165 and model.snap_angle(-173) == 180 and model.snap_angle(8, 45) == 0


def test_a_tool_s_defaults_give_a_new_element_only_what_it_may_carry():
    """Issue #9 (REQ-015): what the right pane was set to while a tool was active is the next element's -- and only what that element may carry, so a source written so is one the export accepts."""
    defaults = {"subtype": "vh", "angle": 45, "show_length": True, "span": 30, "diagonal": 1, "style": {"line": 2, "point": 0.5, "bogus": 3}}
    column = model.apply_defaults({"type": "S", "label": "S101", "points": [[0, 0]]}, defaults)
    assert column["angle"] == 45 and "subtype" not in column and "show_length" not in column and "span" not in column
    assert column["style"] == {"line": 2, "point": 0.5}
    m_point = model.apply_defaults({"type": "M", "label": "M101", "points": [[0, 0]]}, defaults)
    assert m_point["subtype"] == "vh" and m_point["angle"] == 45
    m_line = model.apply_defaults({"type": "M", "label": "M102", "points": [[0, 0], [100, 0]]}, defaults)
    assert m_line["subtype"] == "vh" and "angle" not in m_line, "an Auflager drawn with two points is not turned"
    slab = model.apply_defaults({"type": "D", "label": "D101", "points": [[0, 0], [100, 0], [100, 100]]}, {**defaults, "subtype": "normal"})
    assert slab["subtype"] == "normal" and slab["span"] == 30 and slab["diagonal"] == 1 and slab["show_length"] is True
    wall = model.apply_defaults({"type": "V", "label": "V101", "points": [[0, 0], [100, 0]]}, defaults)
    assert wall["show_length"] is True and "subtype" not in wall and "angle" not in wall
    source = model.new_source("P98", floor="1")
    source["elements"] = [column, m_point, m_line, slab, wall]
    model.check_source(source, "P98.json")
    assert model.apply_defaults({"type": "T", "points": [[0, 0], [1, 0]]}, None) == {"type": "T", "points": [[0, 0], [1, 0]]}


def test_the_fire_plans_measure_their_zones_with_the_plan_s_own_area():
    assert fire.ring_area is model.ring_area, "one area, not two"
    assert model.ring_area([[0, 0], [3, 0], [3, 4], [0, 4]]) == 12.0


def test_the_report_lists_the_quantities_under_the_symbols_in_its_language():
    """The legend compiled: «Métrés» under the symbols, the walls «6.50 m», the slab «12.00 m²», the columns «2 pce» -- the decimal a point, in French as in German."""
    import test_plan_types_v0116 as types
    here = types._project("plan_metres_report")
    source = _plan()
    source["id"] = "M99"
    types._write(here, source)
    model.export(here.plans_dir, here.root, here.data_dir, model.known_positions(here.data_dir) + ["V001", "V002", "T001", "D001", "S001", "S002"])
    french = types._run(here, '#show-plan-legend("M99")', "metres_fr", "fr")
    for part in ("Métrés", "6.50 m", "3.00 m", "12.00 m2", "2 pce"):   # «m²», read back through NFKC as «m2»
        assert part in french, (part, french)
    german = types._run(here, '#show-plan-legend("M99")', "metres_de", "de")
    assert "Ausmass" in german and "6.50 m" in german and "2 Stk." in german, german
