"""A position plan's stiffness centre S and mass centre M (calc/domains/plan_centres.py, plan.py, plan_svg.py; issue #54, spec docs/requirements/completed/2026-10-13-plan-positions-centre-rigidite-centre-masse.md).

The engineer, 12.10.2026: «calculer et dessiner le centre de rigidité S et le centre de masse M sur le plan de positions» -- S from the bracing walls (H, W), each a length to a power its construction mode fixes, by the method of the document «Centre de rigidité d'un étage — calcul mécanique général» (12.10.2026, the spec's Annexe A); M the area centroid of an outline he draws.

What is held: the document's own example and its own reference code, copied here as the judge; the four values of one plan under the four powers; that only H and W count and that a wall is a straight run; that S is there for one construction mode only and for no default; that turning, mirroring and scaling the plan turn, mirror and scale S and nothing else; and every case in which S or M is not there, said and never raised.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import json
import math
import re
import types

import conftest
import positions_store
import validation
from domains import plan as model
from domains import plan_centres
from domains import plan_pages
from domains import plan_svg


def _wall(a, b, mode="timber_frame", type_="W", label=None):
    element = {"type": type_, "label": label or f"{type_}101", "points": [list(a), list(b)]}
    if mode:
        element["construction"] = mode
    return element


def _plan(*elements, **fields):
    source = model.new_source("P90", floor="1")
    source["elements"] = list(elements)
    source.update(fields)
    return source


def _box(mode="timber_frame", **fields):
    """The spec's plan (REQ-004): 12 by 8, vertical walls of length 1 at x = 0 and 3 at x = 12, horizontal ones of length 2 at y = 0 and y = 8."""
    return _plan(_wall((0, 3.5), (0, 4.5), mode, label="W101"), _wall((12, 2.5), (12, 5.5), mode, label="W102"),
                 _wall((5, 0), (7, 0), mode, "H", "H101"), _wall((5, 8), (7, 8), mode, "H", "H102"), **fields)


def _s(source):
    found = plan_centres.state(source)["stiffness"]
    return None if found is None else found["point"]


def _near(p, q, tol=1e-9):
    return p is not None and math.dist(p, q) <= tol


# --- the document's section 11, copied as it is written there: the judge of the general case -------------------

def _reference(parois):
    from math import cos, radians, sin
    kxx = sum(k * cos(radians(a)) ** 2 for _, _, _, a, k in parois)
    kyy = sum(k * sin(radians(a)) ** 2 for _, _, _, a, k in parois)
    kxy = sum(k * sin(radians(a)) * cos(radians(a)) for _, _, _, a, k in parois)
    kxt = sum(k * cos(radians(a)) * (x * sin(radians(a)) - y * cos(radians(a))) for _, x, y, a, k in parois)
    kyt = sum(k * sin(radians(a)) * (x * sin(radians(a)) - y * cos(radians(a))) for _, x, y, a, k in parois)
    det = kxx * kyy - kxy ** 2
    return (kxx * kyt - kxy * kxt) / det, (kxy * kyt - kyy * kxt) / det


def test_the_documents_example_gives_s_at_9_and_4():
    # section 10: W1 and W2 in direction y at x = 0 and x = 12 (10 and 30 kN/mm), W3 and W4 in direction x at y = 0 and y = 8 (20 each)
    parts = [(0.0, 4.0, 0.0, 1.0, 10.0), (12.0, 4.0, 0.0, 1.0, 30.0), (6.0, 0.0, 1.0, 0.0, 20.0), (6.0, 8.0, 1.0, 0.0, 20.0)]
    assert _near(plan_centres.stiffness_centre(parts), (9.0, 4.0))
    # walls parallel to the axes: the barycentre of the stiffnesses, section 5
    assert _near(plan_centres.stiffness_centre(parts), ((10 * 0 + 30 * 12) / 40, (20 * 0 + 20 * 8) / 40))
    assert plan_centres.stiffness_centre([]) is None


def test_a_walls_stiffness_is_its_length_to_the_power_of_its_mode():
    assert _near(_s(_box("timber_frame")), (9.0, 4.0))
    assert _near(_s(_box("clt", clt_power=2)), (10.8, 4.0))
    assert _near(_s(_box("clt", clt_power=1.5)), (12 * 3 ** 1.5 / (1 + 3 ** 1.5), 4.0)) and abs(_s(_box("clt", clt_power=1.5))[0] - 10.063) < 5e-4
    assert _near(_s(_box("concrete")), (12 * 27 / 28, 4.0)) and abs(_s(_box("concrete"))[0] - 11.571) < 5e-4
    found = plan_centres.state(_box("clt", clt_power=2))["stiffness"]
    assert (found["construction"], found["power"], found["walls"]) == ("clt", 2.0, 4)
    # only the ratios count: the same plan with a scale and without one has the same S
    scaled = _box("concrete", scale={"mode": "calibration", "points": [[0, 0], [1, 0]], "length_m": 1.0})
    assert _near(_s(scaled), _s(_box("concrete")))
    assert plan_centres.MODES == ("timber_frame", "clt", "concrete") and plan_centres.POWERS["clt"] == (1.5, 2.0)


def test_only_the_bracing_walls_count():
    source = _box()
    before = _s(source)
    source["elements"] += [
        {"type": "V", "label": "V101", "points": [[0, 0], [0, 8]]},
        {"type": "B", "subtype": "wand", "label": "", "points": [[0, 0], [1, 0], [1, 8], [0, 8]]},
        {"type": "T", "label": "T101", "points": [[0, 0], [12, 8]]},
        {"type": "S", "label": "S101", "points": [[3, 3]]},
    ]
    assert _near(_s(source), before), "a bearing wall, a concrete area, a beam and a column move nothing"
    source["elements"].append(_wall((0, 0), (0, 8), label="H103", type_="H"))
    assert not _near(_s(source), before, 1e-3), "a bracing wall does"
    assert [wall["label"] for wall in plan_centres.walls(source)] == ["W101", "W102", "H101", "H102", "H103"]


def test_a_wall_is_a_straight_run():
    # a wall that turns a corner is two walls: the very walls two straight elements make
    corner = _plan({"type": "W", "label": "W101", "construction": "concrete", "points": [[0, 0], [6, 0], [6, 4]]}, _wall((0, 8), (2, 8), "concrete", "H", "H101"))
    apart = _plan(_wall((0, 0), (6, 0), "concrete", label="W101"), _wall((6, 0), (6, 4), "concrete", label="W102"), _wall((0, 8), (2, 8), "concrete", "H", "H101"))
    assert len(plan_centres.walls(corner)) == 3 and _near(_s(corner), _s(apart))
    # a straight wall drawn through a point on its way is one wall of its whole length: l³ and not l₁³ + l₂³
    through = _box("concrete")
    through["elements"][1]["points"] = [[12, 2.5], [12, 4.0], [12, 5.5]]
    assert len(plan_centres.walls(through)) == 4 and _near(_s(through), _s(_box("concrete")))
    # a point a hundredth of a sheet unit off the line -- what rounding a click gives -- still makes one wall, of the length between its ends
    rounded = plan_centres.walls(_plan({"type": "W", "label": "W101", "construction": "concrete", "points": [[100, 250], [100.01, 400], [100, 550]]}))
    assert len(rounded) == 1 and abs(rounded[0]["length"] - 300) < 1e-9
    # a wall that comes back on itself is not one run
    assert len(plan_centres.walls(_plan({"type": "W", "label": "W101", "points": [[0, 0], [100, 0], [40, 0]]}))) == 2
    # two elements end to end stay two walls
    split = _box("concrete")
    split["elements"][1] = _wall((12, 2.5), (12, 4.0), "concrete", label="W102")
    split["elements"].append(_wall((12, 4.0), (12, 5.5), "concrete", label="W103"))
    assert len(plan_centres.walls(split)) == 5 and not _near(_s(split), _s(_box("concrete")), 1e-3)


def test_one_construction_mode_and_no_default():
    mixed = _box()
    mixed["elements"][3]["construction"] = "concrete"
    found = plan_centres.state(mixed)
    assert found["stiffness"] is None and found["stiffness_note"].code == "plan_centres_mixed"
    assert found["stiffness_note"].args == {"plan": "P90", "timber_frame": 3, "clt": 0, "concrete": 1}
    mixed["elements"][3]["construction"] = "timber_frame"
    assert _near(_s(mixed), (9.0, 4.0))
    # no default: one wall without a mode is enough, and it is named
    bare = _box()
    del bare["elements"][2]["construction"]
    note = plan_centres.state(bare)["stiffness_note"]
    assert note.code == "plan_centres_no_mode" and note.args["labels"] == "H101" and note.args["count"] == 1 and "H101" in note
    # CLT waits for its power, and takes no other than the two
    waiting = _box("clt")
    assert plan_centres.state(waiting)["stiffness_note"].code == "plan_centres_no_power"
    assert plan_centres.power_of(_box("clt", clt_power=3), "clt") is None and plan_centres.power_of({}, "concrete") == 3.0
    # the power chosen for CLT is not read for another mode
    assert _near(_s(_box("timber_frame", clt_power=2)), (9.0, 4.0))


def _moved(source, f):
    out = copy.deepcopy(source)
    for element in out["elements"]:
        element["points"] = [list(f(x, y)) for x, y in element["points"]]
    for outline in out.get("outlines", []):
        outline["points"] = [list(f(x, y)) for x, y in outline["points"]]
    return out


def test_turning_mirroring_and_scaling_the_plan_do_the_same_to_s():
    source = _plan(_wall((1, 1), (4, 2), "concrete"), _wall((9, 0), (11, 5), "concrete", label="W102"), _wall((2, 7), (8, 9), "concrete", "H", "H101"), _wall((6, 3), (6, 5), "concrete", "H", "H102"))
    s = _s(source)
    c, n = math.cos(math.radians(30)), math.sin(math.radians(30))
    turned = _s(_moved(source, lambda x, y: (x * c - y * n, x * n + y * c)))
    assert _near(turned, (s[0] * c - s[1] * n, s[0] * n + s[1] * c), 1e-9) and abs(math.hypot(*turned) - math.hypot(*s)) < 1e-9
    # the sheet's frame has y down, the document's y up: mirrored, S is mirrored and nothing else
    assert _near(_s(_moved(source, lambda x, y: (x, -y))), (s[0], -s[1]))
    # a page in points and one in hundredths of a millimetre: no absolute threshold decides anything
    for k in (1000.0, 0.001):
        assert _near(_s(_moved(source, lambda x, y, k=k: (k * x, k * y))), (k * s[0], k * s[1]), 1e-9 * k)
    assert _near(_s(_moved(_box("concrete"), lambda x, y: (5000 + 1000 * x, 9000 + 1000 * y))), (5000 + 12000 * 27 / 28, 13000.0), 1e-6)


def test_inclined_walls_agree_with_the_documents_reference_code():
    ends = [((0, 0), (5, 1)), ((7, -2), (9, 6)), ((-3, 4), (2, 9)), ((4, 4), (4.5, 7)), ((10, 10), (14, 9))]
    for mode, power in (("timber_frame", 1.0), ("concrete", 3.0)):
        source = _plan(*[_wall(a, b, mode, label=f"W{101 + i}") for i, (a, b) in enumerate(ends)])
        parois = [(f"W{i}", (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), math.dist(a, b) ** power)
                  for i, (a, b) in enumerate(ends)]
        assert _near(_s(source), _reference(parois), 1e-9), mode


def test_no_stiffness_centre_is_said_and_never_raised():
    assert plan_centres.state(_plan())["stiffness_note"].code == "plan_centres_no_walls"
    # three parallel walls: one direction
    parallel = _plan(*[_wall((0, y), (5, y), label=f"W10{y}") for y in (0, 3, 8)])
    assert plan_centres.state(parallel)["stiffness_note"].code == "plan_centres_one_direction"
    # walls rounding leaves 0.01° off the parallel are one direction still, not an S a kilometre away
    nearly = _plan(_wall((0, 0), (500, 0)), _wall((0, 300), (500, 300.09), label="W102"))
    assert plan_centres.state(nearly)["stiffness_note"].code == "plan_centres_one_direction"
    # two walls that cross: S is where they cross, and the storey has no torsional stiffness
    cross = _plan(_wall((0, 4), (10, 4)), _wall((3, 0), (3, 9), label="W102"))
    found = plan_centres.state(cross)
    assert _near(found["stiffness"]["point"], (3.0, 4.0)) and [note.code for note in found["remarks"]] == ["plan_centres_no_torsion"]
    assert plan_centres.state(_box())["remarks"] == []
    # an elevation section has neither: nothing computed, nothing said
    section = _box(role="section", plan_type="section")
    found = plan_centres.state(section)
    assert found == {"applies": False, "outline": None, "mass": None, "mass_note": None, "stiffness": None, "stiffness_note": None, "remarks": []}
    # a draft with a point clicked twice, or an element of one point, is read and not raised on
    draft = _box()
    draft["elements"].append({"type": "W", "label": "W109", "construction": "timber_frame", "points": [[1, 1], [1, 1]]})
    draft["elements"].append({"type": "H", "label": "H109", "construction": "timber_frame", "points": [[2, 2]]})
    assert _near(_s(draft), (9.0, 4.0))


def test_the_mass_centre_is_the_area_centroid_of_the_outline():
    box = _plan(outlines=[{"points": [[0, 0], [12, 0], [12, 8], [0, 8]]}])
    found = plan_centres.state(box)
    assert _near(found["mass"]["point"], (6.0, 4.0)) and found["mass_note"] is None and len(found["outline"]) == 4
    # an L: the centroid of its area, which the mean of its six corners is not
    ell = [[0, 0], [10, 0], [10, 4], [4, 4], [4, 10], [0, 10]]
    area = 10 * 4 + 4 * 6
    expected = ((10 * 4 * 5 + 4 * 6 * 2) / area, (10 * 4 * 2 + 4 * 6 * 7) / area)
    m = plan_centres.state(_plan(outlines=[{"points": ell}]))["mass"]["point"]
    mean = (sum(p[0] for p in ell) / 6, sum(p[1] for p in ell) / 6)
    assert _near(m, expected) and not _near(m, mean, 0.1)
    # drawn the other way round: the same point
    assert _near(plan_centres.state(_plan(outlines=[{"points": ell[::-1]}]))["mass"]["point"], expected)
    assert plan_centres.state(_plan())["mass_note"].code == "plan_centres_no_outline"
    flat = plan_centres.state(_plan(outlines=[{"points": [[0, 0], [5, 5], [10, 10]]}]))
    assert flat["mass"] is None and flat["mass_note"].code == "plan_centres_flat_outline", "three points on a line enclose nothing -- and the mean of the corners is not given for a centroid"
    # M needs no wall and S no outline
    assert plan_centres.state(box)["stiffness"] is None and plan_centres.state(_box())["mass"] is None
    assert plan_centres.drawn(plan_centres.state(box)) and plan_centres.drawn(plan_centres.state(_box())) and not plan_centres.drawn(plan_centres.state(_plan()))


# --- the contract: what a plan's file states, at which version, and what the export writes (plan.py) ----------

OUTLINE = [[0, 0], [12, 0], [12, 8], [0, 8]]


def _saved(source):
    """`source` as a writer of a plan writes it -- at the version it needs --, checked."""
    out = copy.deepcopy(source)
    out["schema_version"] = model.version_of(out)
    model.check_source(out, "P90.json")
    return out


def _refused(source, *words):
    try:
        _saved(source)
    except validation.ValidationError as exc:
        text = str(exc)
        assert "P90.json" in text and all(word in text for word in words), text
        return text
    raise AssertionError(f"accepted, expected a refusal naming {words}")


def test_a_plans_file_states_the_modes_the_outline_the_power_and_the_switch():
    source = _saved(_box("clt", clt_power=1.5, print_centres=True, outlines=[{"points": OUTLINE}]))
    assert source["schema_version"] == "1.8"
    assert [element["construction"] for element in source["elements"]] == ["clt"] * 4
    # a mode is a bracing wall's, and one of the three
    _refused(_plan({"type": "S", "label": "S101", "points": [[1, 1]], "construction": "clt"}), "element 1 (S)", "construction")
    _refused(_plan({"type": "V", "label": "V101", "points": [[1, 1], [5, 1]], "construction": "clt"}), "element 1 (V)", "H, W")
    _refused(_plan(_wall((0, 0), (5, 0), "masonry")), "construction", "masonry")
    # one outline, an area, without sizes of its own, and on no elevation section
    _refused(_plan(outlines=[{"points": OUTLINE}, {"points": OUTLINE}]), "one building outline", "2")
    _refused(_plan(outlines=[{"points": OUTLINE[:2]}]), "outline 1", "three points")
    _refused(_plan(outlines=[{"points": [[0, 0], [5, 0], [5, 0], [0, 5]]}]), "outline 1", "same point")
    _refused(_plan(outlines=[{"points": OUTLINE, "style": {"line": 2}}]), "outline 1", "style")
    _refused(_plan(outlines=[{"points": OUTLINE}], role="section", plan_type="section"), "outline", "floor plan")
    # the power is 1.5 or 2, the switch true or false
    _refused(_box("clt", clt_power=3), "clt_power")
    _refused(_plan(print_centres="yes"), "print_centres")
    # a file that carries them at an older version says so, rather than being read as that version
    stale = _box("clt")
    stale["schema_version"] = "1.6"
    try:
        model.check_source(stale, "P90.json")
    except validation.ValidationError as exc:
        assert "1.8" in str(exc) and "1.6" in str(exc)
    else:
        raise AssertionError("a construction mode at 1.6 was accepted")


def test_the_schemas_restate_the_modes_and_the_powers_and_nothing_else():
    source = validation.load_schema("plan-source")["properties"]
    assert tuple(source["elements"]["items"]["properties"]["construction"]["enum"]) == plan_centres.MODES
    assert tuple(float(p) for p in source["clt_power"]["enum"]) == plan_centres.POWERS["clt"]
    assert source["schema_version"]["enum"][-1] == model.CENTRES_SCHEMA_VERSION == model.SOURCE_SCHEMA_VERSIONS[-1]
    export = validation.load_schema("plans")["properties"]
    record = next(iter(export["plans"]["patternProperties"].values()))["properties"]
    assert tuple(record["centres"]["properties"]["stiffness"]["properties"]["construction"]["enum"]) == plan_centres.MODES
    assert export["schema_version"]["enum"] == [model.EXPORT_SCHEMA_VERSION, model.TEXT_EXPORT_VERSION, model.CENTRES_EXPORT_VERSION, model.ROOTED_EXPORT_VERSION]
    # S and M are computed and never stored: the source has no field for where they are
    assert not {"stiffness", "mass", "centres"} & set(source)


def test_the_versions_nest():
    text = {"points": [[5, 5]], "text": "note"}
    bare, texted = _plan(), _plan(texts=[text])
    outlined, both = _plan(outlines=[{"points": OUTLINE}]), _plan(outlines=[{"points": OUTLINE}], texts=[text])
    assert [model.version_of(s) for s in (bare, texted, outlined, both)] == ["1.6", "1.7", "1.8", "1.8"]
    for source in (bare, texted, outlined, both):
        _saved(source)
    # each of the four fields makes a 1.8 file, a wall's mode among them
    for source in (_box(), _plan(clt_power=2), _plan(print_centres=False), _plan(print_centres=True)):
        assert model.version_of(source) == "1.8" and _saved(source)
    # a text at 1.6 is still refused, and 1.7 without one of the new fields is still read
    wrong = dict(texted, schema_version="1.6")
    try:
        model.check_source(wrong, "P90.json")
    except validation.ValidationError as exc:
        assert "holds a text" in str(exc)
    else:
        raise AssertionError("a text at 1.6 was accepted")
    assert model.export_version_of({"P1": {}}) == "1.3" and model.export_version_of({"P1": {"texts": []}}) == "1.4"
    assert model.export_version_of({"P1": {"texts": []}, "P2": {"centres": {}}}) == "1.5"


def test_a_page_turns_with_the_text_or_the_outline_its_plan_holds():
    here = types.SimpleNamespace(plans_dir=conftest.tmpdir("centres_pages"))
    # until issue #54 a plan was written at 1.6 here whatever it held, and one with a text was refused the turn of its own page
    for source, version in ((_plan(texts=[{"points": [[5, 5]], "text": "note"}]), "1.7"), (_box(outlines=[{"points": OUTLINE}]), "1.8"), (_plan(), "1.6")):
        turned = model.rotate_source(_saved(source), 1, (20.0, 10.0))
        _target, written = plan_pages._write_position(here, turned)
        assert written["schema_version"] == version
    # the outline turns with the page, and S and M with what they are computed from: (x, y) -> (height - y, x)
    source = _box(outlines=[{"points": OUTLINE}])
    turned = model.rotate_source(source, 1, (20.0, 10.0))
    assert turned["outlines"][0]["points"] == [[10, 0], [10, 12], [2, 12], [2, 0]]
    before, after = plan_centres.state(source), plan_centres.state(turned)
    assert _near(after["mass"]["point"], (10 - before["mass"]["point"][1], before["mass"]["point"][0]))
    assert _near(after["stiffness"]["point"], (10 - 4.0, 9.0))


def test_a_new_wall_takes_its_tools_mode_and_the_outline_is_moved_and_never_copied():
    wall = model.apply_defaults({"type": "W", "label": "W101", "points": [[0, 0], [5, 0]]}, {"construction": "clt"})
    assert wall["construction"] == "clt"
    assert "construction" not in model.apply_defaults({"type": "V", "label": "V101", "points": [[0, 0], [5, 0]]}, {"construction": "clt"})
    assert "construction" not in model.apply_defaults({"type": "W", "label": "W102", "points": [[0, 0], [5, 0]]}, {"construction": "brick"})
    source = _box(outlines=[{"points": OUTLINE}])
    copied = model.copy_entry(source, "element", 0, 1, 1, model.crop_of(source))
    assert source["elements"][copied[0]]["construction"] == "timber_frame", "a wall copied keeps its mode"
    model.translate_entry(source, "outline", 0, 2, 3)
    assert source["outlines"][0]["points"][0] == [2, 3] and _near(plan_centres.state(source)["mass"]["point"], (8.0, 7.0))
    try:
        model.copy_entry(source, "outline", 0, 1, 1, model.crop_of(source))
    except ValueError:
        pass
    else:
        raise AssertionError("a second outline was made")
    assert len(source["outlines"]) == 1 and model.ENTRY_LISTS["outline"] == "outlines"


def _codes(notes):
    return [note.code for note in notes if getattr(note, "code", "").startswith("plan_centres")]


def test_what_cannot_be_printed_is_a_warning_and_so_is_a_mode_against_its_positions_section():
    ids = ["W101", "W102", "H101", "H102"]
    mixed = _box(print_centres=True)
    mixed["elements"][3]["construction"] = "concrete"
    assert _codes(model.warnings(mixed, ids)) == ["plan_centres_mixed", "plan_centres_no_outline"]
    # the plan that does not ask for them to be printed is told nothing: the card of the window says it
    mixed["print_centres"] = False
    assert _codes(model.warnings(mixed, ids)) == []
    assert _codes(model.warnings(_box(print_centres=True, outlines=[{"points": OUTLINE}]), ids)) == []
    cross = _plan(_wall((0, 4), (10, 4)), _wall((3, 0), (3, 9), label="W102"), print_centres=True, outlines=[{"points": OUTLINE}])
    assert _codes(model.warnings(cross, ["W101", "W102"])) == ["plan_centres_no_torsion"]
    # a mode held against the section of its position (REQ-013): a CLT section drawn as timber frame
    rows = [{"position": "W101", "type": "Wand", "section_type": "clt", "dimension": "20/30/20"}, {"position": "W102", "type": "Wand", "section_type": "rec", "dimension": "60/160"}, {"position": "H101", "type": "Wand"}]
    sections = positions_store.section_types(rows)
    assert sections == {"W101": "clt", "W102": "rec"}
    notes = [note for note in model.warnings(_box(), ids, sections=sections) if getattr(note, "code", "") == "plan_centres_section"]
    assert len(notes) == 1 and notes[0].args["label"] == "W101" and notes[0].args["mode"].code == "plan_construction_timber_frame"
    assert "W101" in notes[0] and "CLT section" in notes[0] and "timber frame" in notes[0]
    # set right on either side, it is gone; a wall without a mode is the stiffness centre's own reason and not this one; the other way round is no contradiction
    assert _codes(model.warnings(_box("clt", clt_power=2), ids, sections=sections)) == []
    assert _codes(model.warnings(_box(), ids, sections={"W101": "rec"})) == []
    bare = _box()
    del bare["elements"][0]["construction"]
    assert _codes(model.warnings(bare, ids, sections=sections)) == []
    assert _codes(model.warnings(_box("clt", clt_power=2), ids, sections={"W101": "pla"})) == []
    # without the positions at hand the comparison is not made, and nothing is raised
    assert _codes(model.warnings(_box(), ids)) == []


def test_the_export_writes_the_centres_a_plan_prints_and_nothing_for_one_that_prints_none():
    sheet = (float(model.BLANK_SHEET["width"]), float(model.BLANK_SHEET["height"]))
    quiet = _saved(_box(outlines=[{"points": OUTLINE}]))
    assert "centres" not in model.build_record(quiet, sheet), "drawn in the window, not printed: the record is the one of a plan without"
    printed = _saved(_box("clt", clt_power=2, print_centres=True, outlines=[{"points": OUTLINE}]))
    centres = model.build_record(printed, sheet)["centres"]
    assert centres["source"] == "python:domains/plan_centres.py" and "sections 5 et 9" in centres["reference"] and centres["unit"] == "sheet"
    assert centres["stiffness"] == {"point": [10.8, 4], "construction": "clt", "power": 2, "walls": 4}
    assert centres["mass"] == {"point": [6, 4]} and centres["outline"] == OUTLINE
    # asked for and nothing to print: no block, the warning alone
    assert "centres" not in model.build_record(_saved(_plan(print_centres=True)), sheet)
    # through the export itself, with the sections of the positions: the record validates at 1.5 and the warning comes out
    root = conftest.tmpdir("centres_export")
    plans_dir, data_dir = root / "plans", root / "data"
    plans_dir.mkdir()
    data_dir.mkdir()
    (plans_dir / "P90.json").write_text(json.dumps(printed), encoding="utf-8")
    other = _saved(dict(_box(), id="P91"))
    (plans_dir / "P91.json").write_text(json.dumps(other), encoding="utf-8")
    data, files, notes = model.prepare(plans_dir, root, data_dir, ["W101", "W102", "H101", "H102"], sections={"W101": "clt"})
    assert data["schema_version"] == "1.5" and "centres" in data["plans"]["P90"] and "centres" not in data["plans"]["P91"]
    assert [note.args["plan"] for note in notes if getattr(note, "code", "") == "plan_centres_section"] == ["P91"]
    # and the drawings: the plan that prints them carries them between their markers, the other is drawn without a trace of them
    assert plan_svg.CENTRES_OPEN in files["plans/P90.svg"] and plan_svg.CENTRES_OPEN not in files["plans/P91.svg"]
    assert [line["key"] for line in data["plans"]["P90"]["legend"] if line.get("centres")] == list(plan_svg.CENTRE_KEYS)
    assert not any(line.get("centres") for line in data["plans"]["P91"]["legend"])


def test_the_exports_that_read_the_project_hand_its_positions_sections_to_the_plans():
    """ARCH-009, the callers themselves: `plan.prepare` compares a wall's mode with its position's section only where it is handed the sections, so a caller that forgot them would lose the warning without a word. Held here for the two that read the project -- the plans' own export (`plan_pages.export_drawings`, what a layer switched and a page turned run) and the whole export (`export_all.run`)."""
    import export_all
    import project
    import test_plan_types_v0116 as types
    here = types._project("plan_centres_callers")
    rows = positions_store.read(here)
    rows.append(positions_store.check_row({"position": "W101", "type": "Wand", "section_type": "clt", "dimension": "20/30/20", "units": "mm"}))
    positions_store.write(here, rows)
    source = _saved(dict(_plan(_wall((200, 300), (200, 500), label="W101"), _wall((300, 200), (500, 200), type_="H", label="H101")), id="C97"))
    types._write(here, source)

    def said(notes):
        return [note.args["label"] for note in notes if getattr(note, "code", "") == "plan_centres_section"]

    assert said(plan_pages.export_drawings(here)) == ["W101"]
    printed = []
    warn = export_all._warn
    export_all._warn = printed.append
    try:
        with project.using(here):
            export_all.run()
    finally:
        export_all._warn = warn
    assert said(printed) == ["W101"], [str(note)[:80] for note in printed]
    # set right, neither says it any more
    source["elements"][0]["construction"] = "clt"
    source["clt_power"] = 2
    types._write(here, source)
    assert said(plan_pages.export_drawings(here)) == []


# --- the drawing (plan_svg.py) ------------------------------------------------------------------------------

def _inside(svg):
    """What a drawing holds between its centres' markers, each pair's part."""
    return [part.split(plan_svg.CENTRES_CLOSE)[0] for part in svg.split(plan_svg.CENTRES_OPEN)[1:]]


def test_the_window_always_draws_them_and_the_export_only_where_the_plan_says_so():
    source = _saved(_box(outlines=[{"points": OUTLINE}]))
    drawn = plan_svg.render(source, centres=True)
    assert drawn.count(plan_svg.CENTRES_OPEN) == drawn.count(plan_svg.CENTRES_CLOSE) == 2
    outline, marks = _inside(drawn)
    assert "stroke-dasharray" in outline and plan_svg.OUTLINE_COLOUR in outline and ">S<" not in outline
    assert ">S</text>" in marks and ">M</text>" in marks and plan_svg.STIFFNESS_COLOUR in marks and plan_svg.MASS_COLOUR in marks
    # the outline lies under the symbols and the two centres over the numbers
    assert drawn.index(plan_svg.CENTRES_OPEN) < drawn.index('<g id="el-1">') < drawn.rindex(plan_svg.CENTRES_OPEN)
    # not asked for -- the export of a plan that does not print them, another plan shown over the open one --: the very drawing of a plan that has none
    stripped = copy.deepcopy(source)
    stripped.pop("outlines")
    for element in stripped["elements"]:
        element.pop("construction")
    assert plan_svg.render(source) == plan_svg.render(stripped) and plan_svg.CENTRES_OPEN not in plan_svg.render(source)
    assert plan_svg.legend_items(source) == plan_svg.legend_items(stripped)
    # each of the three only where it is there: no S on mixed modes, no M without an outline, and no marker for nothing
    walls_only = plan_svg.render(_box(), centres=True)
    assert walls_only.count(plan_svg.CENTRES_OPEN) == 1 and ">S</text>" in walls_only and ">M</text>" not in walls_only
    assert plan_svg.CENTRES_OPEN not in plan_svg.render(_plan(print_centres=True), centres=True)
    assert plan_svg.CENTRES_OPEN not in plan_svg.render(_box(role="section", plan_type="section"), centres=True)
    # S follows the drawing: a wall moved, S has moved, nothing saved
    moved = copy.deepcopy(source)
    model.translate_entry(moved, "element", 1, -3, 0)
    assert _inside(plan_svg.render(moved, centres=True))[1] != marks


def test_the_legend_lists_what_the_plan_prints_and_marks_it():
    printed = _box(print_centres=True, outlines=[{"points": OUTLINE}])
    lines = {line["key"]: line for line in plan_svg.legend_items(printed)}
    assert [key for key in lines if lines[key].get("centres")] == list(plan_svg.CENTRE_KEYS)
    assert all(lines[key]["swatch"].startswith("<svg") for key in plan_svg.CENTRE_KEYS)
    assert ">S</text>" in lines["Steifigkeitszentrum"]["swatch"] and ">M</text>" in lines["Massenzentrum"]["swatch"] and "stroke-dasharray" in lines["Umriss"]["swatch"]
    assert not any("centres" in line for key, line in lines.items() if key not in plan_svg.CENTRE_KEYS)
    # only what is drawn: no outline, no line for it nor for M; nothing computable, none of the three and the warning alone
    assert plan_svg.centre_keys(_box(print_centres=True)) == ("Steifigkeitszentrum",)
    mixed = _box(print_centres=True)
    mixed["elements"][0]["construction"] = "concrete"
    assert plan_svg.centre_keys(mixed) == () and plan_svg.centre_keys(_box(outlines=[{"points": OUTLINE}])) == ()
    # the three lines are worded in the three languages by the glossary, under the key the export carries
    from i18n import strings
    assert [strings.text("plan.legend.Steifigkeitszentrum", lang) for lang in strings.LANGUAGES] == ["Steifigkeitszentrum", "Centre de rigidité", "Stiffness centre"]
    assert [strings.text("plan.legend.Massenzentrum", lang) for lang in strings.LANGUAGES] == ["Massenzentrum", "Centre de masse", "Mass centre"]
    assert [strings.text("plan.legend.Umriss", lang) for lang in strings.LANGUAGES] == ["Gebäudeumriss", "Contour du bâtiment", "Building outline"]
    # the German the export carries is the glossary's own, as every other line's
    assert all(lines[key]["text"] == strings.text(f"plan.legend.{key}", "de") for key in plan_svg.CENTRE_KEYS)
    assert plan_svg.swatch("Umriss").startswith("<svg") and "stroke-dasharray" in plan_svg.swatch("Umriss")


# --- the report (lib/calc-engine.typ, document.typ, sheet.typ) ----------------------------------------------------

def _lines(svg):
    return [line for line in svg.split("\n") if line]


def test_the_marker_python_writes_is_the_one_typst_takes_out():
    """`centres: false` is a regular expression over the drawing: what Typst removes is held here to what Python writes, so that renaming a marker on one side cannot leave the centres printed where a call asked for none."""
    pattern = f"(?s){plan_svg.CENTRES_OPEN}.*?{plan_svg.CENTRES_CLOSE}"
    engine = conftest.engine_source()
    assert f'overlay.replace(regex("{pattern}"), "")' in engine
    source = _saved(_box(outlines=[{"points": OUTLINE}]))
    drawn = plan_svg.render(source, centres=True)
    assert len(re.findall(pattern, drawn)) == 2, "both pairs: the outline under the symbols, the two centres over the numbers"
    assert _lines(re.sub(pattern, "", drawn)) == _lines(plan_svg.render(source)), "taken out, the drawing is the one without them"
    # the legend's lines go by the mark the export writes, and no key is written a second time in Typst
    assert 'lines.filter(l => not l.at("centres", default: false))' in engine and not any(key in engine for key in plan_svg.CENTRE_KEYS)
    # a sheet's plan view hands the argument on (the calculation block and the document's plan, which did too, are retired: spec 2026-10-21-commandes-typst-refonte)
    assert "lengths: lengths, centres: centres)" in (conftest.ROOT / "lib" / "calc-engine-drawings.typ").read_text(encoding="utf-8")   # a sheet's plan view, its primitive moved there (lot 17)


def test_the_report_prints_them_where_the_plan_says_so_and_a_call_may_leave_them_out():
    """Compiled: the plan whose switch is on prints S, M and the outline with their three lines of legend, in the report's language; `centres: false` leaves out the symbols and the lines; a calculation block's detail prints none; a plan whose switch is off prints none."""
    import test_plan_types_v0116 as types
    here = types._project("plan_centres_report")
    walls = [("W101", (200, 375), (200, 425)), ("W102", (800, 325), (800, 475)), ("H101", (450, 200), (550, 200)), ("H102", (450, 600), (550, 600))]
    elements = [{"type": label[0], "label": label, "construction": "timber_frame", "points": [list(a), list(b)]} for label, a, b in walls]
    # a beam through both centres, a position the example project has: what a calculation block frames its detail around
    elements.append({"type": "T", "label": "T001", "points": [[480, 400], [670, 400]]})
    outline = [[200, 200], [800, 200], [800, 600], [200, 600]]
    printed = _saved(dict(_plan(*elements, outlines=[{"points": outline}], print_centres=True), id="C99"))
    quiet = _saved(dict(_plan(*copy.deepcopy(elements), outlines=[{"points": outline}]), id="C98"))
    found = plan_centres.state(printed)
    assert _near(found["stiffness"]["point"], (650.0, 400.0)) and _near(found["mass"]["point"], (500.0, 400.0))
    for source in (printed, quiet):
        types._write(here, source)
    model.export(here.plans_dir, here.root, here.data_dir, model.known_positions(here.data_dir) + [label for label, _a, _b in walls])
    data = json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == ("1.6" if here.has_folders else "1.5") and "centres" in data["plans"]["C99"] and "centres" not in data["plans"]["C98"]
    # the two letters made words a page's text can be searched for
    for pid in ("C99", "C98"):
        overlay = conftest.figure(here, data["plans"][pid]["overlay"])
        svg = overlay.read_text(encoding="utf-8")
        assert (plan_svg.CENTRES_OPEN in svg) == (pid == "C99")
        overlay.write_text(svg.replace(">S</text>", ">SCENTRE</text>").replace(">M</text>", ">MCENTRE</text>"), encoding="utf-8")
    words = {"de": ("Steifigkeitszentrum", "Massenzentrum", "Gebäudeumriss"), "fr": ("Centre de rigidité", "Centre de masse", "Contour du bâtiment"),
             "en": ("Stiffness centre", "Mass centre", "Building outline")}
    for lang, expected in words.items():
        text = types._run(here, '#image-positions-plan("C99")', f"centres_{lang}", lang)
        assert "SCENTRE" in text and "MCENTRE" in text and all(word in text for word in expected), (lang, text)
    # one call leaves them out, the symbols and their lines of the legend -- and the rest of the legend stays
    hidden = types._run(here, '#image-positions-plan("C99", detail-figure: ("length", "axes", "dimensions"))', "centres_off", "fr")
    assert "SCENTRE" not in hidden and "MCENTRE" not in hidden and not any(word in hidden for word in words["fr"]), hidden
    assert "Poutre" in hidden, "the beam's line of the legend is still there"
    # a detail around the beam shows both
    detail = types._run(here, '#image-positions-plan("C99", highlight: "T001", frame: "highlight", detail-legend: "none")', "centres_detail", "fr")
    assert "SCENTRE" in detail and "MCENTRE" in detail, detail
    # the plan whose switch is off prints none, and its legend has no line for them
    off = types._run(here, '#image-positions-plan("C98")', "centres_quiet", "fr")
    assert "SCENTRE" not in off and not any(word in off for word in words["fr"]), off
    assert not any(line.get("centres") for line in data["plans"]["C98"]["legend"])
