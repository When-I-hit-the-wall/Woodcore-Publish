"""The materials Woodcore ships (calc/domains/materials_catalogue.py, spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-003, REQ-005, ARCH-004, ARCH-008; issue #110).

What is held:

* **REQ-005** -- the classes of SIA 265 Tabellen 8 and 9, the panels of SIA 265/1, every row with a value of SIA 261 Tabellen 28 to 30 and the workbook's library merged by name and weight, each read at its source and each a material the contract accepts;
* **REQ-003** -- the shipped ids, written down here: a version of Woodcore that drops one fails this test, since a project's layer may name it; every workbook row stays an id of its own;
* **ARCH-004** -- `materials-catalogue.json` holds names and categories, no number, no orphan, and every shipped material has its entry;
* **ARCH-008** -- the weight of a class or a panel is the line the catalogue names: C24 weighs SIA 261's «Nadelhölzer allgemein», OSB/3 the workbook's 680 kg/m³ beside its ρ_k of 550 (T46).
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest  # noqa: F401  -- calc/ on the path
from domains import materials_catalogue as catalogue, materials_contract as contract
from norms import sia261, sia265, sia265_1


# The shipped ids of this version, by kind -- what projects may name. Grow it; never shrink it.
GRADES = {"C16", "C24", "C30", "D30", "GL20h", "GL24h", "GL28h", "GL32h"}
PANELS = {"plywood-f25-10-5", "plywood-f25-10-3", "plywood-f40-40-5", "plywood-f40-40-3", "plywood-f50-25-5", "plywood-f50-25-3", "plywood-f60-10-5", "plywood-f60-10-3",
          "particle-p4", "particle-p5", "particle-p6", "particle-p7", "cement", "osb2", "osb3", "osb4", "hb", "mbh", "mdf-la", "mdf-hls"}


def test_every_shipped_material_is_read_at_its_source_and_accepted():
    products = set(sia265_1.products())
    for m in catalogue.catalogue():
        contract.check_material(m, "catalogue", products)
        assert m["origin"] in catalogue.ORIGINS
    by_origin = {}
    for m in catalogue.catalogue():
        by_origin.setdefault(m["origin"], []).append(m)
    assert {m["id"].split(":")[1] for m in by_origin["sia265"]} == set(sia265.grades())
    assert len(by_origin["sia265-1"]) == 20
    rows = [r for t in (sia261.table_28(), sia261.table_29(), sia261.table_30()) for r in t["rows"]
            if isinstance(r.get("raumlast", r.get("flaechenlast")), (int, float))]
    assert len(by_origin["sia261"]) == len(rows) == 94


def test_the_ids_of_this_version_are_still_shipped():
    ids = set(catalogue.ids())
    assert {"sia265:" + g for g in GRADES} <= ids
    assert {"sia265-1:" + p for p in PANELS} <= ids
    workbook = json.loads(catalogue.WORKBOOK_FILE.read_text(encoding="utf-8"))["materials"]
    assert {"ext:%d" % e["row"] for e in workbook} <= ids          # every row, merged or not
    assert catalogue.find("ext:130")["id"] == catalogue.find("ext:62")["id"] == "ext:62"   # OSB3 under two Ebenen, one material


def test_the_catalogue_holds_names_and_no_number():
    data = json.loads(catalogue.CATALOGUE_FILE.read_text(encoding="utf-8"))

    def numbers(node, at):
        if isinstance(node, dict):
            for k, v in node.items():
                yield from numbers(v, at + "." + k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from numbers(v, "%s[%d]" % (at, i))
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            yield at
    assert not list(numbers(data, "catalogue"))
    shipped = catalogue.by_id()
    for rid, entry in data["sia261"].items():
        assert "sia261:" + rid in shipped, rid                       # no orphan
        assert entry["category"] in contract.CATEGORIES and entry["fr"] and entry["en"]
    for pid in data["panels"]:
        assert "sia265-1:" + pid in shipped, pid
    for target in data["weights"].values():
        assert shipped[target].get("weight"), target
    for m in catalogue.catalogue():
        assert all(m["names"].get(lang) for lang in contract.LANGS), m["id"]


def test_a_class_and_a_panel_weigh_the_line_the_catalogue_names():
    c24 = catalogue.find("sia265:C24")
    assert c24["weight"]["value"] == next(r["raumlast"] for r in sia261.table_28()["rows"] if r["id"] == "holz_nadelhoelzer_allgemein")
    assert c24["values"]["f_m_d"] == 14.1 and c24["values"]["f_c_90_d"] == 1.8 and c24["family"] == "softwood"
    assert catalogue.find("sia265:GL24h")["family"] == "glulam" and catalogue.find("sia265:D30")["family"] == "hardwood"
    osb = catalogue.find("sia265-1:osb3")
    assert osb["rho_k"] == [550, 550, 550] and osb["weight"]["value"] == 6.8 and "Kronospan" in osb["weight"]["ref"]
    assert catalogue.find("sia261:feinkiesauflage_pro_10_mm_dicke")["weight"] == {"value": 20.0, "unit": "kN/m³", "ref": "SIA 261:2020, Tabelle 29 (0,20 kN/m² pro 10 mm)"}


def test_the_old_keys_of_a_layer_find_their_row():
    assert catalogue.ext_id("OSB3", "Beplankung") == "ext:62"
    assert catalogue.ext_id("Gartenplatten", "") is None          # two weights, no Ebene: as materials.weight refuses it
    assert catalogue.ext_id("Gartenplatten", "Beschwerung") is not None
