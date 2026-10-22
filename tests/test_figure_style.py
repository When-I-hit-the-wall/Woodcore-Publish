# -*- coding: utf-8 -*-
"""The three factors every figure is set with, and the factor one entry of a figure may state over them (v0.99, docs/domain/detail-schemas.md §3.3decies, docs/ui/window.md §10quater, docs/decisions.md §13).

Two halves. The first is `calc/domains/figure_style.py`, which is what the factors *are* -- their names, their range, **which of them each kind of entry may state**, and the arithmetic -- read by the plans, the static models and the detail schemas alike, so that a slider means one thing in every tab. The second is the detail schemas, which had no factors at all before v0.99 and now have the same three.

What every test here is built on, and what has to hold whatever else changes: **a schema that states no factor is drawn exactly as it was.** Every quantity the module used to write as a multiple of its font is now `on_line`, `on_point` or `on_text` of the drawing's own unit, which is that same font, so at factor 1 the number is the number it was -- and the only thing that moved in the figure at all is the ground behind a text, which is point 4's own business (`test_a_label_is_set_over_its_own_box_and_not_drawn_twice`).

⚠️ The decision table is held here rather than in each tab's tests, and in both directions: a collection the table does not name may state nothing, and a factor an entry is not drawn with is refused **naming the ones it may state**. That is what keeps `point` off a bar: a field nobody can see the effect of is the kind of field that acquires a value nobody checks (the argument that took `plates.thickness` out of a connector's source in v0.70).
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import json
import math
import re

import conftest
from conftest import ROOT
from domains import figure_style
from domains import schema
from domains import schema_svg
import project


def _source(**overrides):
    """A small, valid detail: two crossing pieces, two markers, a centre, a named point and a horizontal dimension -- enough that every collection has an entry with a label to draw."""
    source = schema.new_source("T_99")
    source["elements"] = [
        {"id": "E1", "kind": "linear", "points": [[0, 0], [300, 0]], "position": "T001", "h": 140},
        {"id": "E2", "kind": "linear", "points": [[150, -150], [150, 150]], "h": 80},
    ]
    source["connectors"] = [
        {"id": "C1", "kind": "Stabdübel", "x": 100, "z": 0},
        {"id": "C2", "kind": "Stabdübel", "x": 200, "z": 0},
    ]
    source["aids"] = [
        {"id": "A1", "kind": "centre", "x": 150, "z": 0},
        {"id": "A2", "kind": "point", "x": 60, "z": -60, "label": "Punkt A"},
    ]
    source["dimensions"] = [
        {"id": "D1", "kind": "horizontal", "from": {"x": 0, "z": 0}, "to": {"x": 300, "z": 0}, "offset": -80},
    ]
    source.update(overrides)
    return source


def _entry(source, collection, eid):
    return next(e for e in source[collection] if e["id"] == eid)


def _frame(drawing, collection, eid):
    return next(f for c, i, f in drawing["label_frames"] if (c, i) == (collection, eid))


def _refusal(source, message_holds):
    """What `check_source` says, and that it says it -- the refusal a defect in a file must raise rather than be drawn."""
    try:
        schema.check_source(copy.deepcopy(source), "T_99.json")
    except Exception as exc:                       # the module's own ValidationError
        text = str(exc)
        for piece in message_holds:
            assert piece in text, f"the refusal does not say {piece!r}: {text}"
        return text
    raise AssertionError(f"accepted, and should have been refused for {message_holds}")


# --- what the factors are ---------------------------------------------------------------


def test_the_three_factors_and_their_range_are_written_down_once():
    """Three names and one range, read by the three tabs' models rather than restated in each -- which is how they came to mean the same thing everywhere (docs/decisions.md §13)."""
    assert figure_style.KEYS == ("line", "point", "text")
    assert figure_style.RANGE == (0.25, 3.0)
    assert figure_style.DEFAULT == 1.0
    from domains import plan, statics
    for model in (plan, statics, schema):
        assert model.STYLE_KEYS == figure_style.KEYS, f"{model.__name__} has a list of its own"
        assert model.STYLE_RANGE == figure_style.RANGE, f"{model.__name__} has a range of its own"


def test_the_decision_table_names_every_collection_of_the_three_sources():
    """Each collection of a plan, a static model, a schema and a fire-protection plan is in the table, and a collection it does not name may state nothing at all -- so a collection nobody has decided about is refused rather than quietly taking all three."""
    from domains import fire, plan, statics
    wanted = {("schema", c) for c in schema.ENTITIES}
    wanted |= {("statics", c) for c in statics.ENTITIES}
    wanted |= {("plan", "elements"), ("plan", "axes"), ("plan", "dimensions")}   # a plan's dimensions since issue #9
    wanted |= {("plan", "texts"), ("fire", "texts")}   # the Text tool's, issue #43 (fire.ENTRY_COLLECTIONS)
    # an emergency exit is in no row: its arrow is sized by its two points, which leaves no factor anything to scale
    wanted |= {("fire", c) for c in fire.COLLECTIONS if c != "exits"}
    assert wanted == set(figure_style.ENTRY_KEYS), (sorted(wanted ^ set(figure_style.ENTRY_KEYS)))
    for (kind, collection), keys in figure_style.ENTRY_KEYS.items():
        assert keys, f"{kind}/{collection} may state nothing -- leave it out of the table instead"
        assert set(keys) <= set(figure_style.KEYS), keys
    assert figure_style.allowed("statics", "points") == ("text",), "a node is never drawn in the report (v0.56)"
    assert figure_style.allowed("plan", "axes") == ("line", "text"), "an axis puts no symbol on a point"
    assert figure_style.allowed("schema", "invented") == (), "a collection the table does not name states nothing"


def test_only_the_factors_an_entry_states_are_read_back():
    """`stated` is what the window writes in orange and what «Reprendre» takes off; `entry_factors` fills the rest in with 1, and `product` is what the entry is drawn with."""
    assert figure_style.stated({}) == {}
    assert figure_style.stated(None) == {}
    assert figure_style.stated({"style": {}}) == {}
    assert figure_style.stated({"style": {"text": 2}}) == {"text": 2.0}
    assert figure_style.entry_factors({"style": {"text": 2}}) == {"line": 1.0, "point": 1.0, "text": 2.0}
    assert figure_style.product({"line": 1.5, "point": 1.0, "text": 1.0}, {"style": {"line": 2}}) == {
        "line": 3.0, "point": 1.0, "text": 1.0}
    assert figure_style.record({"style": {"text": 2}}) == {"text": 2.0}
    assert figure_style.record({}) is None, "an entry that states none carries no key at all"


def test_a_factor_an_entry_is_not_drawn_with_is_refused_naming_the_ones_it_may_state():
    """The rule in both directions, on every collection of a schema: what it may state passes, what it may not is refused **and the message says what to write instead** -- a refusal that only says «no» sends the engineer back to this file."""
    cases = [
        ("elements", "E1", "point", ("style.point", "line, text")),
        ("connectors", "C1", "line", ("style.line", "point, text")),
        ("dimensions", "D1", "point", ("style.point", "line, text")),
    ]
    for collection, eid, key, holds in cases:
        source = _source()
        _entry(source, collection, eid)["style"] = {key: 1.5}
        _refusal(source, holds + (eid,))
    # and every factor the table does allow is accepted
    for collection, eid in (("elements", "E1"), ("connectors", "C1"), ("aids", "A1"), ("dimensions", "D1")):
        source = _source()
        _entry(source, collection, eid)["style"] = {key: 1.5 for key in figure_style.allowed("schema", collection)}
        schema.check_source(source, "T_99.json")


def test_a_factor_outside_the_range_or_not_a_number_is_refused():
    """⚠️ What is *not a number at all* is caught by the JSON schema's own walker, which runs first and says so in its own words (`expected number, got str`); what this module refuses is the range. Both messages name the field, which is what the engineer needs. `figure_style.check` refuses a non-number too, for a caller with no JSON schema in front of it -- the window writing a factor, or a test calling it directly -- and that path is checked here rather than through a source."""
    for bad, holds in ((3.5, ("style.text", "from 0.25 to 3.0")), (0.1, ("style.text", "from 0.25 to 3.0")),
                       ("2", ("style.text",)), (True, ("style.text",))):
        source = _source()
        _entry(source, "elements", "E1")["style"] = {"text": bad}
        _refusal(source, holds)
    said = []
    figure_style.check({"text": "2"}, said.append)
    figure_style.check({"text": True}, said.append)
    assert len(said) == 2 and all("must be a number" in message for message in said), said
    source = _source(style={"text": 4})
    _refusal(source, ("style.text", "from 0.25 to 3.0"))
    source = _source(style={"nonsense": 1.0})
    _refusal(source, ("is not a factor",))
    source = _source(style=[1, 2])
    _refusal(source, ("style",))
    said = []
    figure_style.check([1, 2], said.append)
    assert said and "must be an object" in said[0], said


# --- a schema that states no factor is the schema it was ---------------------------------


def test_a_schema_that_states_no_factor_is_drawn_as_it_was():
    """The invariant the whole of point 3 rests on. The three quantities are the three the module has always computed -- the extent over 40, over 480, over 130 with its floor -- and a source that states nothing, one that states {} and one that states 1 for all three give one drawing to the byte."""
    source = _source()
    drawing = schema_svg.layout(source)
    size = drawing["size"]
    assert drawing["font"] == size / 40.0
    assert drawing["stroke"] == size / 480.0
    assert drawing["radius"] == max(size / 130.0, 3.5 * size / 480.0)
    # ⚠️ the floor under the radius is taken on the **scaled** stroke, deliberately: what it is for is that a marker is never lost among the lines round it, and a drawing whose strokes are set three times as heavy would lose it again if the floor were taken on the unscaled one
    heavy = schema_svg.layout(_source(style={"line": 3.0}))
    assert heavy["radius"] == 3.5 * heavy["stroke"] > size / 130.0
    bare = copy.deepcopy(source)
    bare.pop("style")
    svgs = {
        "absent": schema_svg.render(schema_svg.layout(bare)),
        "empty": schema_svg.render(schema_svg.layout(_source(style={}))),
        "ones": schema_svg.render(schema_svg.layout(_source(style={"line": 1.0, "point": 1.0, "text": 1.0}))),
    }
    assert len(set(svgs.values())) == 1, "the three say the same thing and must draw the same figure"


# The engineer's own detail (tests/projet-exemple), rendered with the lines that carry a label's ground taken out: the report's figure and the editor's. **These two digests are the v0.98 figure's**, taken from it with its halos removed before a line of v0.99 was written, and they are what says that nothing but the ground behind a text moved. Re-freezing one is a decision, like re-freezing an example page: it means a drawing has been allowed to move, and the reason belongs in CLAUDE.md.
# ⚠️ Taken again at v0.120 for one reason: the palette merged (lib/figure-palette.json, D5) -- with the old colours mapped onto the new, the figure before is this one byte for byte, checked first.
FROZEN = {
    False: "2f612ac661fe9864f6f583d2deb0c19aafd8e03b6a7480adc552b95748db4949",
    True: "1fc63c69fa55f2d378ab88392481209fcde5d92a9b4d162ace72a1c1a7f29a1a",
}


def test_the_example_project_s_own_schema_is_drawn_as_it_was_but_for_its_labels_grounds():
    """The engineer's own detail, rendered before v0.99 and after it: **every line but a text and the ground behind it is identical**, in the report's figure and in the editor's alike. (The texts themselves left the comparison in issue #43: the schemas set them with the one text engine of every figure since, svg_text, which the engineer chose knowing their labels would move slightly -- D-19 of spec 2026-10-11-variables-liees-champs-et-textes; these digests were taken before and after that change and are the same.)

    That is the whole of what point 3 was allowed to change in an existing drawing -- nothing -- and it is checked on a real source rather than on one written here, because what could have moved is the float arithmetic of the three quantities (the extent over 40, over 480, over 130 with a floor), and a synthetic source with round numbers would hide a last-bit difference that a real one shows.
    """
    import hashlib
    path = project.Project.load(conftest.SAMPLE).details_dir / "VU-Skizze.json"
    source = schema.upgrade_source(json.loads(path.read_text(encoding="utf-8")))
    ground = f'fill-opacity="{schema_svg.LABEL_GROUND_OPACITY}"'
    for editing, digest in FROZEN.items():
        svg = schema_svg.render(schema_svg.layout(source, editing=editing))
        assert ground in svg, "no text is set over a box -- the test would compare the whole figure and say less"
        rest = [line for line in svg.splitlines() if ground not in line and "<text" not in line]
        assert hashlib.sha256(("\n".join(rest) + "\n").encode()).hexdigest() == digest, (
            f"editing={editing}: the drawing moved, and not only the grounds behind its texts")


# --- what a factor does, and to what ------------------------------------------------------


def test_the_drawing_s_three_factors_reach_the_three_things_they_name():
    """`text` the font and so every box a text is set in, `line` the stroke, `point` the radius a marker with no diameter is drawn at."""
    base = schema_svg.layout(_source())
    text = schema_svg.layout(_source(style={"text": 2.0}))
    line = schema_svg.layout(_source(style={"line": 2.0}))
    point = schema_svg.layout(_source(style={"point": 2.0}))
    assert text["font"] == 2 * base["font"] and text["stroke"] == base["stroke"]
    assert line["stroke"] == 2 * base["stroke"] and line["font"] == base["font"]
    assert point["radius"] == 2 * base["radius"] and point["font"] == base["font"]
    # the box a label is set in follows the text, which is what makes the frame grow with it
    assert _frame(text, "elements", "E1")["hw"] == 2 * _frame(base, "elements", "E1")["hw"]
    assert text["bbox"][2] - text["bbox"][0] > base["bbox"][2] - base["bbox"][0]
    # and the three reach the figure itself: a heavier stroke is written into it
    assert f'stroke-width="{schema_svg._f(1.3 * line["stroke"])}"' in schema_svg.render(line)


def test_a_factor_stated_on_one_entry_reaches_that_entry_and_no_other():
    """What «a factor multiplying the drawing's» has to mean: the piece that states it is drawn with it, the piece beside it with the drawing's own."""
    source = _source()
    _entry(source, "elements", "E1")["style"] = {"text": 2.0}
    drawing = schema_svg.layout(source)
    base = schema_svg.layout(_source())
    assert _frame(drawing, "elements", "E1")["hw"] == 2 * _frame(base, "elements", "E1")["hw"]
    assert _frame(drawing, "elements", "E2")["hw"] == _frame(base, "elements", "E2")["hw"], "its neighbour moved with it"
    # a marker's own `point` moves its own dot and not the drawing's
    source = _source()
    _entry(source, "connectors", "C1")["style"] = {"point": 2.0}
    drawing = schema_svg.layout(source)
    dots = {c["id"]: c["r"] for c in drawing["connectors"]}
    assert dots["C1"] == 2 * dots["C2"]
    assert drawing["radius"] == base["radius"], "the drawing's own radius moved with one marker's"


def test_an_entry_s_factor_multiplies_the_drawing_s_rather_than_replacing_it():
    """A factor and never a size (v0.99's own decision): a drawing at 1.5 with an entry at 2 draws that entry at 3."""
    source = _source(style={"text": 1.5})
    _entry(source, "elements", "E1")["style"] = {"text": 2.0}
    drawing = schema_svg.layout(source)
    bare = schema_svg.layout(_source())
    assert _frame(drawing, "elements", "E1")["hw"] == 3 * _frame(bare, "elements", "E1")["hw"]
    assert _frame(drawing, "elements", "E2")["hw"] == 1.5 * _frame(bare, "elements", "E2")["hw"]


def test_a_marker_s_stated_diameter_is_a_length_and_is_never_scaled():
    """A schema is a detail at its real size: a dowel 24 mm across is drawn 24 mm across whatever the sliders say. What `point` moves is the radius of a marker that states no diameter, and the floor under a very small one."""
    source = _source()
    _entry(source, "connectors", "C1")["diameter"] = {"value": 24.0, "unit": "mm"}
    _entry(source, "connectors", "C1")["style"] = {"point": 2.0}
    drawn = {c["id"]: c["r"] for c in schema_svg.layout(source)["connectors"]}
    assert drawn["C1"] == 12.0, "a stated diameter was scaled by a slider"


def test_the_export_says_what_the_figure_was_drawn_with():
    """The drawing's own three, and every entry's own beside its placed geometry -- the convention the plans' and the static models' records already follow. An entry that states none carries no key, so data/schemas.json does not move for a schema that uses none."""
    source = _source(style={"line": 1.5})
    _entry(source, "dimensions", "D1")["style"] = {"text": 2.0}
    record = schema.build_record(source)
    assert record["style"] == {"line": 1.5, "point": 1.0, "text": 1.0}
    assert record["dimensions"][0]["style"] == {"text": 2.0}
    assert "style" not in record["elements"][0]
    bare = schema.build_record(_source())
    assert bare["style"] == {"line": 1.0, "point": 1.0, "text": 1.0}
    assert all("style" not in entry for collection in ("elements", "connectors", "aids", "dimensions")
               for entry in bare[collection])


# --- point 4: a text over its own box, and what gives way to it ---------------------------


def test_a_label_is_set_over_its_own_box_and_not_drawn_twice():
    """The engineer, on a schema: the halo puts a cloud round every letter. Every text the schema writes -- a piece's label, a marker's id, a point's name, a dimension's value -- is set over one white rectangle, its own box, and no text is drawn a second time with a wide white stroke (statics_svg's own finding of v0.77, made here for the four kinds of text at once)."""
    source = _source()
    source["dimensions"][0]["show"] = "value"
    svg = schema_svg.render(schema_svg.layout(source))
    # ⚠️ a <text> with a white stroke, and not any white stroke: a marker's dot carries a white hairline of its own, which parts it from what lies under it and is no halo
    haloed = [line for line in svg.splitlines() if line.startswith("<text") and 'stroke="#ffffff"' in line]
    assert not haloed, f"a text is still drawn twice with a white stroke: {haloed[0]}"
    grounds = svg.count(f'fill-opacity="{schema_svg.LABEL_GROUND_OPACITY}"')
    assert grounds == 6, f"{grounds} grounds for six texts: two pieces, two markers, a point's name, a value"
    assert 0.5 < schema_svg.LABEL_GROUND_OPACITY < 1.0, (
        "a schema's label sits ON its piece: an opaque ground would take a bite out of the piece's own fill")


def test_a_label_that_writes_nothing_gets_no_box():
    """A dimension whose `show` writes nothing has no value to set over anything, so there is no box either -- one would be a white patch on the drawing with nothing in it."""
    source = _source()
    source["dimensions"][0]["show"] = "none"
    bare = schema_svg.render(schema_svg.layout(source))
    source["dimensions"][0]["show"] = "value"
    written = schema_svg.render(schema_svg.layout(source))
    ground = f'fill-opacity="{schema_svg.LABEL_GROUND_OPACITY}"'
    assert bare.count(ground) + 1 == written.count(ground)


def test_a_segment_is_cut_at_the_boxes_it_crosses_and_at_no_other():
    """`cut_at_labels`, the arithmetic every cut of point 4 is made with: a segment that crosses no box is itself, one that crosses a box comes back in two pieces that stop at it, and one wholly inside a box comes back as nothing at all."""
    drawing = schema_svg.layout(_source())
    frame = _frame(drawing, "elements", "E1")
    (x, z), hw, hh = frame["at"], frame["hw"], frame["hh"]
    across = schema_svg.cut_at_labels((x - 400, z), (x + 400, z), [frame])
    assert len(across) == 2, "a line straight through a box is two pieces"
    left, right = across
    assert math.isclose(left[1][0], x - hw, abs_tol=1e-6) and math.isclose(right[0][0], x + hw, abs_tol=1e-6)
    away = ((x - 400, z + 10 * hh), (x + 400, z + 10 * hh))
    assert schema_svg.cut_at_labels(away[0], away[1], [frame]) == [away], "a line that misses every box is itself"
    assert schema_svg.cut_at_labels((x - hw / 2, z), (x + hw / 2, z), [frame]) == [], "a line inside a box is nothing"
    # a box turned with its text is clipped in its own frame, not in an upright one round it
    turned = _frame(drawing, "elements", "E2")
    assert turned["angle"], "E2's label is turned with its piece, which is what this checks"
    assert len(schema_svg.cut_at_labels((turned["at"][0], turned["at"][1] - 400),
                                        (turned["at"][0], turned["at"][1] + 400), [turned])) == 2


def test_a_shown_construction_line_is_cut_at_the_labels_it_crosses():
    """The point of it: the aids are drawn over everything, the labels included (v0.77's rule, which stands), so a shown line ran straight through a piece's number and no ground behind the text could mend it. The line gives way -- it stops at the box and starts again beyond it -- so a line the figure drew in one piece is drawn in several."""
    source = _source()
    label_z = _frame(schema_svg.layout(source), "elements", "E1")["at"][1]
    source["aids"].append({"id": "A3", "kind": "horizontal", "x": 0, "z": label_z, "angle": 0, "shown": True})
    dashed = [line for line in schema_svg.render(schema_svg.layout(source)).splitlines() if "stroke-dasharray" in line]
    assert len(dashed) >= 2, "the line crossing a label is still drawn in one piece"
    # a line nothing crosses is still one piece, and still reaches the frame's edges
    source["aids"][-1]["z"] = label_z + 3 * _frame(schema_svg.layout(source), "elements", "E1")["hh"]
    whole = [line for line in schema_svg.render(schema_svg.layout(source)).splitlines() if "stroke-dasharray" in line]
    assert len(whole) == 1, "a line that crosses nothing was cut all the same"
    x0, _z0, x1, _z1 = schema_svg.layout(source)["bbox"]
    assert f'x1="{schema_svg._f(x0)}"' in whole[0] and f'x2="{schema_svg._f(x1)}"' in whole[0], (
        "the line no longer runs to the edges of the frame (v0.77)")


def test_a_dimension_s_line_is_cut_under_its_own_value():
    """A value dragged onto its own dimension line is read against the line, so the line is broken under it -- the drawing office's answer, and the engineer's own choice over making the value's ground opaque. Nothing is cut while the value floats clear of the line, which is where it is put by default."""
    source = _source()
    source["dimensions"][0]["show"] = "value"

    def dimension_lines(src):
        svg = schema_svg.render(schema_svg.layout(src))
        return [line for line in svg.splitlines()
                if line.startswith("<line") and f'stroke="{schema_svg.DIMENSION}"' in line]

    base = dimension_lines(source)
    frame = _frame(schema_svg.layout(source), "dimensions", "D1")
    # the value dragged back onto the line it measures
    source["dimensions"][0]["label_offset"] = [0.0, round(frame["anchor"][1] - frame["home"][1], 3)]
    assert len(dimension_lines(source)) == len(base) + 1, "the dimension line was not broken under its value"
