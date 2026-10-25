"""What each layer weighs, and every build-up at a glance (calc/domains/dead_load_layers.py `contributions`, dead_load_overview.py; spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-008, REQ-011, Q-007; issue #111).

What is held:

* **REQ-008** -- three lists, g_k alone, a_k alone, the two: each layer's load and its part, the parts adding up to the whole and the loads to the sum;
* **REQ-011, Q-007 A** -- a line per build-up: its id, name, number of layers, g_k, a_k, the sum, the retained value and whether it was written, «complete» or the number of red messages to correct with those messages, a malformed file named; nothing written.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import project
from domains import dead_load_layers, dead_load_overview, dead_load_source


def _layer(**change):
    return dict(dead_load_source.new_layer(), **change)


def _src(cid, layers, chosen=None, name=""):
    return {"schema_version": "2.0", "id": cid, "name": name, "label": "", "group": "", "chosen": chosen, "layers": layers}


def test_the_contributions_add_up_to_the_sums():
    """REQ-008 (T11): g_k alone, a_k alone, the two."""
    src = _src("AU-01", [_layer(thickness=27), _layer(kind="ak", pose="spaced", thickness=200, width=60, spacing=625, link=True),
                         _layer(kind="ak", material="ext:46", thickness=200), _layer(kind="ak", pose="typed", material=None, label="Installationen", load=0.5)])
    rows = dead_load_source.layer_rows(src)
    lists, totals = dead_load_layers.contributions(rows)
    assert [c["number"] for c in lists["gk"]] == [1] and [c["number"] for c in lists["ak"]] == [2, 3, 4] and len(lists["all"]) == 4
    for key in ("gk", "ak", "all"):
        assert abs(sum(c["load"] for c in lists[key]) - totals[key]) < 1e-12 and abs(sum(c["share"] for c in lists[key]) - 1.0) < 1e-12, key
    assert abs(totals["all"] - sum(r["load"] for r in rows)) < 1e-12
    empty, zero = dead_load_layers.contributions([r for r in rows if r["kind"] == "gk"])
    assert empty["ak"] == [] and zero["ak"] == 0


def test_the_overview_gives_a_line_per_build_up():
    """REQ-011, Q-007 A: a complete build-up, one with a value written, one with two red messages, a malformed file -- in the order of the files, nothing written."""
    here = conftest.project_copy("dead_load_overview")
    folder = dead_load_source.folder(here)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.json"):   # the example's own build-ups (issue #109): the overview of these five alone
        old.unlink()
    files = {"AU-01": _src("AU-01", [_layer(thickness=27)], name="Dach"),
             "AU-02": _src("AU-02", [_layer(thickness=27)], chosen=0.5),
             "AU-03": _src("AU-03", [_layer(material=None), _layer(thickness=None)])}
    for cid, src in files.items():
        (folder / ("%s.json" % cid)).write_text(json.dumps(src), encoding="utf-8")
    (folder / "AU-04.json").write_text(json.dumps(dict(_src("AU-04", [_layer()]), schema_version="9.9")), encoding="utf-8")
    (folder / "AU-05.json").write_text("{not json", encoding="utf-8")
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    with project.using(here):
        lines = dead_load_overview.overview(here)
    assert [l["id"] for l in lines] == ["AU-01", "AU-02", "AU-03", "AU-04", "AU-05"]
    one, two, three, four, five = lines
    assert one["name"] == "Dach" and one["layers"] == 1 and abs(one["gk"] - 0.135) < 1e-12 and one["ak"] == 0 and one["retained"] == 0.2
    assert one["state"] == "complete" and not one["replaced"] and [l.number for l in one["model"]] == [1]
    assert two["retained"] == 0.5 and two["replaced"]
    assert three["state"] == "to_fix" and three["to_fix"] == 2 and [(m.code, m.field) for m in three["problems"]] == [("no_material", "layers[0]"), ("missing_thickness", "layers[1]")]
    assert three["total"] is None and three["model"] == []
    assert four["state"] == "malformed" and "schema_version" in four["malformed"] and "AU-04.json" in four["malformed"]
    assert five["state"] == "malformed" and "JSON" in five["malformed"]
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before, "nothing written"
