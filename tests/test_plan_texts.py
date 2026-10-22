"""A text placed on a drawing, in each engine's own data (spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, lot 3, REQ-011, ARCH-004, ARCH-007, ARCH-RISK-107).

What is held, without a window:

* **live** (REQ-011, ARCH-007): the same text drawn against other values prints the new value, in the four engines' renders;
* **a variable gone** prints its last value with a `text_stale` warning in the engine's export warnings, and the export goes on (D-06);
* **a drawing without a text** draws exactly as before: a plan, a fire-protection plan and a static model render the same SVG with no `texts` as with an emptied one, and a text adds only its own lines;
* **moved, copied, turned, renamed, removed**: a plan's text by `translate_entry`, `copy_entry` and `rotate_source`, a schema's by `modify` and `duplicate`, a static model's by `rename` and `remove`.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy

import conftest  # noqa: F401 -- puts calc/ on the path

from domains import fire, fire_svg, links, plan, plan_svg, schema, schema_edit, schema_svg, statics, statics_svg

LINK = {"domain": "snow-load", "instance": "SL", "var": "L", "show": "value"}


def _values(length):
    return links.index({"domains": {"snow-load": {"instances": {"SL": {"vars": {"L": {"value": length, "unit": "m", "symbol": "L"}}}}}}})


def _plan():
    source = plan.new_source("TX1")
    source["texts"] = [{"points": [[200, 150]], "text": "L = {1}", "vars": {"1": dict(LINK)}}]
    return source


def _model():
    source = statics.new_source("TX1")
    source.update(points=[{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 3, "z": 0}],
                  members=[{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}],
                  supports=[{"id": "A1", "point": "P1", "type": "pinned"}, {"id": "A2", "point": "P2", "type": "roller"}])
    return source


def _schema():
    source = schema.new_source("TX1")
    source["connectors"] = [{"id": "C1", "kind": "Nagel", "x": 0, "z": 0}]
    return source


def _fire_frame():
    return {"sheet": dict(plan.BLANK_SHEET), "style": {}}


def test_a_text_prints_the_value_its_variable_gives_now_in_every_engine():
    texts = [{"id": "T1", "x": 1, "z": -1, "text": "L = {1}", "vars": {"1": dict(LINK)}}]
    model = {**_model(), "texts": copy.deepcopy(texts)}
    detail = {**_schema(), "texts": [{**copy.deepcopy(texts[0]), "x": 40, "z": 25}]}
    sheet = _plan()
    burning = {"id": "F1", "zones": [], "texts": [{**copy.deepcopy(sheet["texts"][0]), "id": "X1"}]}
    for length in (17.5, 21):
        values, wanted = _values(length), f">L = {length} m<"
        assert wanted in statics_svg.render(statics_svg.layout(model, values))
        assert wanted in schema_svg.render(schema_svg.layout(detail, values=values))
        assert wanted in plan_svg.render(sheet, values=values)
        assert wanted in fire_svg.render(burning, _fire_frame(), values=values)


def test_a_variable_gone_prints_its_last_value_with_a_warning_and_the_export_goes_on(tmp=None):
    import json
    import tempfile
    from pathlib import Path
    model = {**_model(), "texts": [{"id": "T1", "x": 1, "z": -1, "text": "L = {1}",
                                    "vars": {"1": {**LINK, "last": {"value": 12, "unit": "m", "symbol": "L"}}}}]}
    statics.stamp_version(model)
    with tempfile.TemporaryDirectory(dir=conftest.TMP if conftest.TMP.is_dir() else None) as folder:
        (Path(folder) / "TX1.json").write_text(json.dumps(model), encoding="utf-8")
        data, files, notes = statics.prepare(folder, links.index({"domains": {}}))
    assert data["models"]["TX1"]["texts"][0]["lines"] == ["L = 12 m"] and data["models"]["TX1"]["texts"][0]["links"][0]["stale"]
    assert any(getattr(n, "code", "") == "text_stale" and "TX1" in n for n in notes), notes
    assert ">L = 12 m<" in files["statics/TX1-de.svg"]


def test_a_drawing_without_a_text_draws_as_before():
    values = _values(17.5)
    bare = plan.new_source("TX1")
    assert plan_svg.render(bare, values=values) == plan_svg.render({**bare, "texts": []}, values=values) == plan_svg.render(bare)
    with_text = plan_svg.render(_plan(), values=values).split("\n")
    assert [line for line in with_text if line not in plan_svg.render(bare).split("\n")] and \
        all("<text" in line for line in with_text if line not in plan_svg.render(bare).split("\n")), "a text adds its own lines and nothing else"
    burning = {"id": "F1", "zones": []}
    assert fire_svg.render(burning, _fire_frame(), values=values) == fire_svg.render({**burning, "texts": []}, _fire_frame()) == fire_svg.render(burning, _fire_frame())
    model = _model()
    assert statics_svg.render(statics_svg.layout(model, values)) == statics_svg.render(statics_svg.layout({**model, "texts": []}))
    assert statics.stamp_version(copy.deepcopy(model))["schema_version"] == statics.SOURCE_SCHEMA_VERSION
    assert plan.version_of(bare) == plan.SOURCE_SCHEMA_VERSION and fire.version_of(burning) == fire.SOURCE_SCHEMA_VERSION


def test_a_plan_s_text_is_moved_copied_and_turned_with_its_page():
    source = _plan()
    plan.translate_entry(source, "text", 0, 10, -5)
    assert source["texts"][0]["points"] == [[210, 145]]
    index, _renames = plan.copy_entry(source, "text", 0, 20, 0, plan.crop_of(source))
    assert index == 1 and source["texts"][1]["points"] == [[230, 145]] and source["texts"][1]["vars"] == source["texts"][0]["vars"]
    sheet = (float(source["sheet"]["width"]), float(source["sheet"]["height"]))
    turned = plan.rotate_source(source, 1, sheet)
    assert turned["texts"][0]["points"] == [[sheet[1] - 145, 210]]
    source["schema_version"] = plan.version_of(source)
    plan.check_source(source, "TX1.json")


def test_a_schema_s_text_is_moved_turned_and_duplicated_and_a_model_s_renamed_and_removed():
    detail = {**_schema(), "texts": [{"id": "T1", "x": 40, "z": 25, "text": "a"}]}
    schema_edit.modify(detail, ["T1"], schema_edit.translation(10, 5))
    assert (detail["texts"][0]["x"], detail["texts"][0]["z"]) == (50, 30)
    schema_edit.modify(detail, ["T1"], schema_edit.rotation((0, 0), 90))
    made = schema_edit.duplicate(detail, ["T1"], schema_edit.translation(0, 0))
    assert made == ["T2"] and len(detail["texts"]) == 2
    schema.stamp_version(detail)
    schema.check_source(detail, "TX1.json")
    model = {**_model(), "texts": [{"id": "T1", "x": 1, "z": -1, "text": "a"}]}
    statics.rename(model, "texts", "T1", "Note")
    assert model["texts"][0]["id"] == "Note"
    removed = statics.remove(model, "texts", "Note")
    assert removed and not model["texts"]
    assert statics.stamp_version(model)["schema_version"] == statics.SOURCE_SCHEMA_VERSION and "texts" not in model
