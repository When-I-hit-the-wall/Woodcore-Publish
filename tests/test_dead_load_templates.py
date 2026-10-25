"""Templates of build-ups of permanent loads (calc/domains/dead_load_templates.py, calc/libraries/dead-load-templates.json; spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-010, REQ-014, D-08; issue #111).

What is held:

* **REQ-010** -- the eight Lignum templates, each with its names in three languages, its page and its assumptions; the joisted floor with sand: 1.258 kN/m² with the sand filling between the battens, 1.333 across the full width; with a cement screed 1.475 kN/m²; each within a tenth of the book's weight where the book gives one;
* **REQ-014** -- every material a template names is one Woodcore ships, and every template computes: the compact flat roof's Foamglas, which the book does not weigh, is a flat-roof stone wool of the library;
* **D-08** -- «Mes modèles»: a build-up kept as a template in the engineer's folder, listed, made a build-up again with the same sum, removed; a file that cannot be read named and left alone; Woodcore's read only.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import validation
from domains import dead_load_source, dead_load_templates as dt, materials_catalogue


def _by_id():
    return {t["id"]: t for t in dt.shipped()}


def test_the_eight_lignum_templates_are_read_and_each_names_its_page():
    templates = dt.shipped()
    assert len(templates) == 8 and len({t["id"] for t in templates}) == 8
    for t in templates:
        assert all(t["names"].get(lang) for lang in ("fr", "de", "en")), t["id"]
        assert all(t["assumptions"].get(lang) for lang in ("fr", "de", "en")), t["id"]
        assert "Holzbau mit System" in t["reference"]["book"] and isinstance(t["reference"]["page"], int) and t["kind"] in dt.KINDS, t["id"]


def test_the_floors_weigh_what_the_spec_and_the_book_say():
    """REQ-010: 1.258 (sand that fills), 1.333 (sand across the full width), 1.475 (cement screed) kN/m²; the book's 127 and 150 kg/m² within a tenth."""
    by_id = _by_id()
    sand, screed = by_id["lignum-c7-abb13-2"], by_id["lignum-c7-abb12-2"]
    assert round(dt.summary(sand)["total"], 3) == 1.258
    full = dict(sand, layers=[dict(l, fill=False) if l["material"] == "sia261:erdauflasten_und_gleisschotter_sand" else l for l in sand["layers"]])
    assert round(dt.summary(full)["total"], 3) == 1.333
    assert round(dt.summary(screed)["total"], 3) == 1.475
    for t in (sand, screed):
        s = dt.summary(t)
        assert abs(s["total_kg"] - t["book_weight"]["value"]) / t["book_weight"]["value"] < 0.1, (t["id"], s["total_kg"])
        assert s["layers"] == len(t["layers"]) and s["retained"] == round(s["total"] + 0.05, 1) and len(s["model"]) == len(t["layers"])


def test_every_material_a_template_names_is_shipped_and_every_template_computes():
    """REQ-014: no material of the engineer's own in a template, each one computed; the compact flat roof's Foamglas, which the book does not weigh (p. 389 gives its λ only), replaced by a walkable flat-roof stone wool of the library (the engineer, 24.10.2026), said in its assumptions."""
    for t in dt.shipped():
        for i, layer in enumerate(t["layers"]):
            if layer["pose"] != "typed":
                assert materials_catalogue.find(layer["material"]) is not None, (t["id"], i, layer["material"])
        s = dt.summary(t)
        assert s["total"] is not None and not s["problems"], (t["id"], s["problems"])
    flat = _by_id()["lignum-c5-tab13"]
    assert flat["layers"][3]["material"] == "ext:59" and all("Foamglas" in flat["assumptions"][lang] for lang in ("fr", "de", "en"))


def test_a_template_becomes_a_build_up_of_the_project():
    """UI-004: «Créer depuis ce modèle» -- the layers copied, the name and the reference; a source that passes its check; the template untouched."""
    t = _by_id()["lignum-c7-abb12-2"]
    before = json.dumps(t, sort_keys=True)
    src = dt.to_source(t, "AU-07", "de")
    dead_load_source.check_source(src)
    assert src["name"] == "Holzbalkendecke, Zementestrich" and "S. 415" in src["label"] and src["layers"] == t["layers"] and src["layers"] is not t["layers"]
    src["layers"][0]["thickness"] = 60
    assert json.dumps(t, sort_keys=True) == before


def test_my_templates_are_kept_listed_and_removed():
    """D-08: «Enregistrer comme modèle» writes a file in the engineer's folder; it is listed, gives the same sum, and goes; a broken file is named and left alone; Woodcore's cannot be removed."""
    src = dt.to_source(_by_id()["lignum-c7-abb12-2"], "AU-08")
    src["chosen"] = 1.6
    kept = dt.save_mine(src, "Ma dalle", "fr")
    assert dt.MINE_ID.match(kept["id"]) and (dt.folder() / ("%s.json" % kept["id"])).is_file()
    templates, problems = dt.mine()
    assert [t["id"] for t in templates] == [kept["id"]] and problems == [] and dt.name(templates[0], "de") == "Ma dalle"
    assert dt.summary(templates[0])["retained"] == 1.6
    again = dt.to_source(templates[0], "AU-09")
    assert again["chosen"] == 1.6 and again["layers"] == src["layers"]
    broken = dt.folder() / "t-00000000.json"
    broken.write_text("{not json", encoding="utf-8")
    templates, problems = dt.mine()
    assert [t["id"] for t in templates] == [kept["id"]] and len(problems) == 1 and "t-00000000.json" in problems[0]
    assert broken.read_text(encoding="utf-8") == "{not json", "never written over"
    broken.unlink()
    dt.delete_mine(kept["id"])
    assert dt.mine() == ([], [])
    try:
        dt.delete_mine("lignum-c7-abb12-2")
    except validation.ValidationError as exc:
        assert "read only" in str(exc)
    else:
        raise AssertionError("a template of Woodcore's removed")


def test_a_template_with_a_defect_is_refused_naming_the_field():
    t = dict(_by_id()["lignum-c7-abb12-2"])
    for change, word in ((dict(schema_version="9"), "schema_version"), (dict(names=None), "names"), (dict(layers=[]), "layers is empty"),
                         (dict(layers=[dict(t["layers"][0], pose="laid")]), "pose")):
        try:
            dt.check(dict(t, **change), "probe.json")
        except validation.ValidationError as exc:
            assert word in str(exc) and "probe.json" in str(exc), (word, str(exc))
        else:
            raise AssertionError(word)
