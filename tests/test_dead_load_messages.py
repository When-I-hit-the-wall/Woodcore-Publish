"""What a build-up of permanent loads says of itself (calc/domains/dead_load_messages.py; spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-007, P04, P11; issue #111).

What is held:

* **REQ-007** -- each message on a build-up that provokes it, with its layer and its severity: red where a layer stops, orange where a value was replaced or a layer asks a look, information, green where every layer has its weight;
* **P04** -- one evaluation: the export stops with the first red message's layer, the tab says them all;
* **P11, Q-006, T62** -- tiles weighed «inkl. Lattung» (SIA 261 Tabelle 29, and the workbook's tiles of the same weight) with battens under them: the warning gives the battens' load (AU-01: + 0.018 kN/m²) and the sum does not change; the flag held to the norm's headings.
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import validation
from domains import dead_load_messages, dead_load_source, materials_catalogue
from norms import sia261

WOOL = "ext:46"
TILES = "ext:147"   # the workbook's «Pfannenziegel», 47 kg/m², SIA 261 Tabelle 29 «Tonziegeldach inkl. Lattung, Pfannenziegel»


def _layer(**change):
    return dict(dead_load_source.new_layer(), **change)


def _src(layers, chosen=None):
    return {"schema_version": "2.0", "id": "AU-01", "name": "", "label": "", "group": "", "chosen": chosen, "layers": layers}


def _said(src):
    return [(m.code, m.field, m.severity) for m in dead_load_messages.messages(src)]


def test_each_red_message_names_its_layer_and_the_export_stops_with_the_first():
    """REQ-007, P04: no material, a material unknown, one without a weight, a thickness or a width missing, pieces as wide as their spacing, a level of three, a retained value below the sum."""
    cases = ((_layer(material=None, label="Holzfaser X"), "no_material"), (_layer(material="sia261:nothing"), "unknown_material"),
             (_layer(material="sia265-1:mdf-la"), "no_weight"), (_layer(thickness=None), "missing_thickness"),
             (_layer(pose="spaced", thickness=60, width=None, spacing=625), "missing_width_spacing"),
             (_layer(pose="spaced", thickness=60, width=700, spacing=625), "share_full"),
             (_layer(pose="typed", material=None, label="Installationen", load=None), "missing_load"))
    for layer, code in cases:
        src = _src([_layer(), layer])
        assert _said(src) == [(code, "layers[1]", "error")], (code, _said(src))
        try:
            dead_load_source.layer_rows(src, None, "loads/dead/AU-01.json")
        except validation.ValidationError as exc:
            assert "AU-01.json" in str(exc) and "layers[1]" in str(exc), (code, str(exc))
        else:
            raise AssertionError(code)
    three = _src([_layer(pose="spaced", thickness=200, width=60, spacing=625, link=True), _layer(material=WOOL, thickness=200, link=True), _layer()])
    assert ("level_three", "layers[1]", "error") in _said(three)
    below = _src([_layer(thickness=27)], chosen=0.1)
    assert _said(below) == [("chosen_below", "chosen", "error")]
    try:
        dead_load_source.build_instance(below, conftest.PROJECT)
    except validation.ValidationError as exc:
        assert "chosen" in str(exc) and "AU-01.json" in str(exc), str(exc)
    else:
        raise AssertionError("a retained value below the sum passed")
    # two problems: both said, the export stopping with the first
    two = _src([_layer(material=None), _layer(thickness=None)])
    assert [m[1] for m in _said(two)] == ["layers[0]", "layers[1]"]


def test_the_orange_and_the_information_and_the_green():
    """REQ-007: a load replaced (v in place of c), a retained value written (v, auto c), a line that fills thicker than its pieces, the air above one thinner; green with the sum where nothing stops."""
    plain = _src([_layer(thickness=27)])
    assert _said(plain) == [("all_weighed", None, "ok")]
    assert dead_load_messages.messages(plain)[0].params == {"total": 0.135}
    replaced = dead_load_messages.messages(_src([_layer(thickness=27, load=0.2)], chosen=0.5))
    assert [(m.code, m.field, m.severity) for m in replaced] == [("load_replaced", "layers[0]", "warning"), ("chosen_replaced", "chosen", "warning"), ("all_weighed", None, "ok")]
    assert replaced[0].params == {"layer": 1, "value": 0.2, "computed": 0.135} and replaced[1].params == {"value": 0.5, "auto": 0.2}
    thick = _src([_layer(pose="spaced", thickness=160, width=60, spacing=625, link=True), _layer(material=WOOL, thickness=200)])
    assert ("fill_thicker", "layers[1]", "warning") in _said(thick)
    thin = dead_load_messages.messages(_src([_layer(pose="spaced", thickness=200, width=60, spacing=625, link=True), _layer(material=WOOL, thickness=160)]))
    air = next(m for m in thin if m.code == "air")
    assert air.field == "layers[1]" and air.severity == "info" and air.params["air"] == 40


def test_battens_under_tiles_weighed_with_theirs_are_said_and_the_sum_kept():
    """P11, Q-006, T62: the workbook's Pfannenziegel weighs as SIA 261's «Tonziegeldach inkl. Lattung, Pfannenziegel»; roof battens under them warn with their load, AU-01's + 0.018 kN/m²; the sum is the same with or without the warning; battens of no batten role say nothing."""
    tiles = _layer(kind="gk", pose="surface", material=TILES, thickness=None)
    battens = _layer(pose="spaced", thickness=40, width=24, spacing=270, role="roof_battens")
    src = _src([tiles, battens])
    said = dead_load_messages.messages(src)
    warning = next(m for m in said if m.code == "battens_twice")
    rows = dead_load_source.layer_rows(src)
    assert warning.field == "layers[0]" and warning.severity == "warning" and warning.params["extra"] == round(rows[1]["load"], 3)
    assert abs(rows[1]["load"] - 0.0178) < 1e-4 and warning.params["extra"] == 0.018, "AU-01's battens, 24/40 every 270"
    total = sum(r["load"] for r in rows)
    assert abs(total - (0.47 + rows[1]["load"])) < 1e-12, "said, not taken out"
    assert "battens_twice" not in [m.code for m in dead_load_messages.messages(_src([tiles, dict(battens, role="battens")]))]
    assert "battens_twice" not in [m.code for m in dead_load_messages.messages(_src([_layer(pose="surface", material="ext:149", thickness=None), battens]))], "slates carry no battens"


def test_the_tiles_that_carry_their_battens_are_the_norms_lines_inkl_lattung():
    """P11: SIA 261 Tabelle 29's lines under a heading «… inkl. Lattung», and only those, carry the flag; each tile of the workbook that names one weighs as it does."""
    rows = sia261.table_29()["rows"]
    assert {r["id"] for r in rows if r.get("includes_battens")} == {r["id"] for r in rows if "inkl. Lattung" in (r.get("group") or "")} and len([r for r in rows if r.get("includes_battens")]) == 4
    named = materials_catalogue._catalogue()["includes_battens"]
    for workbook_name, norm_id in named.items():
        norm = materials_catalogue.find(norm_id)
        tile = next(m for m in materials_catalogue.catalogue() if m["id"].startswith("ext:") and m["names"]["de"] == workbook_name)
        assert norm["includes_battens"] and tile["includes_battens"], workbook_name
        assert abs(tile["weight"]["value"] - norm["weight"]["value"]) < 1e-9 and tile["weight"]["unit"] == norm["weight"]["unit"], (workbook_name, tile["weight"], norm["weight"])
