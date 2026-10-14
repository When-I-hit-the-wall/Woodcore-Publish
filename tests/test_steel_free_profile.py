"""A free steel profile: rectangles, their section values, the models, the source file and the section type USR that names it (issue #50, spec 2026-10-12-section-acier REQ-003, REQ-004, D-10, D-11, D-12, D-16; calc/domains/profile.py, calc/domains/section.py).

The values are held against hand calculations, never against the module's own arithmetic: an I of three rectangles, 200 x 100, web 6, flanges 10 -- A = 2·100·10 + 180·6 = 3080 mm², I_y = 100·200³/12 − 94·180³/12 = 21 006 667 mm⁴, W_el,y = I_y/100, W_pl,y = 2·(100·10·95 + 6·90·45) = 238 600 mm³, I_z = 2·10·100³/12 + 180·6³/12 = 1 669 907 mm⁴, W_pl,z = 2·10·100²/4 + 180·6²/4 = 51 620 mm³. An L 100 x 50 x 10 drawn from two rectangles, its centroid and plastic axis found off the middle.
"""

import json

import conftest
from conftest import ROOT
from domains import profile, section
import project
import validation


def _raised(fn, *args):
    try:
        fn(*args)
    except (validation.ValidationError, ValueError) as exc:
        return str(exc)
    raise AssertionError("%s should have refused" % fn.__name__)


def _close(a, b, rel=1e-9):
    assert abs(a - b) <= rel * max(abs(a), abs(b), 1.0), (a, b)


def _i(h=200, b=100, tw=6, tf=10):
    return [{"name": "bottom", "y": 0, "z": 0, "b": b, "h": tf, "role": "outstand"},
            {"name": "web", "y": (b - tw) / 2, "z": tf, "b": tw, "h": h - 2 * tf, "role": "internal"},
            {"name": "top", "y": 0, "z": h - tf, "b": b, "h": tf, "role": "outstand"}]


def test_an_i_of_three_rectangles_gives_the_hand_values():
    """REQ-003: area, inertia, elastic and plastic moduli of a doubly symmetric I, by hand."""
    p = profile.properties(_i())
    _close(p["A"], 3080)
    _close(p["z_s"], 100) and _close(p["y_s"], 50)
    _close(p["I_y"], 100 * 200 ** 3 / 12 - 94 * 180 ** 3 / 12)
    _close(p["W_el_y"], p["I_y"] / 100)
    _close(p["W_pl_y"], 2 * (100 * 10 * 95 + 6 * 90 * 45))
    _close(p["I_z"], 2 * 10 * 100 ** 3 / 12 + 180 * 6 ** 3 / 12)
    _close(p["W_pl_z"], 2 * 10 * 100 ** 2 / 4 + 180 * 6 ** 2 / 4)
    _close(p["z_pl"], 100) and _close(p["y_pl"], 50)
    assert p["t_max"] == 10 and p["h"] == 200 and p["b"] == 100


def test_an_unsymmetric_section_finds_its_plastic_axis_where_the_area_halves():
    """An L 100 x 50 x 10 of two rectangles (a leg 10 x 100 standing, a leg 40 x 10 lying): A = 1400; the line that halves it about y lies at z = 70 (1000 + 400 below would be 700 at z = 70 -- 10·70 = 700); W_pl,y = 700·35 + 300·15 + ... checked by the halves' first moments."""
    parts = [{"name": "stand", "y": 0, "z": 0, "b": 10, "h": 100, "role": "outstand"},
             {"name": "lie", "y": 10, "z": 0, "b": 40, "h": 10, "role": "outstand"}]
    p = profile.properties(parts)
    _close(p["A"], 1400)
    _close(p["z_s"], (1000 * 50 + 400 * 5) / 1400)
    # below z: 10·z + 40·min(z, 10); at z = 10 that is 500 < 700, so 10·z + 400 = 700 gives z = 30
    _close(p["z_pl"], 30)
    below = 10 * 30 * 15 + 40 * 10 * 25
    above = 10 * 70 * 35
    _close(p["W_pl_y"], below + above)
    assert p["W_el_y"] == p["I_y"] / max(100 - p["z_s"], p["z_s"]), "the farther fibre"


def test_the_models_set_their_roles_and_load_a_c5_profile():
    """D-10, D-11: every model's rectangles and roles; a C5 profile loaded as its model, its root radii left out, so a little below the book's row."""
    assert set(profile.TEMPLATES) == {"I", "U", "T", "L", "RHS", "plate"}
    i = profile.template("I", h=200, b=100, t_w=6, t_f=10)
    assert [p["role"] for p in i].count("outstand") == 4 and [p["role"] for p in i].count("internal") == 1
    walls = profile.walls(i)
    assert {(w["role"], w["c"], w["t"]) for w in walls} == {("outstand", 47, 10), ("internal", 180, 6)}
    _close(profile.properties(i)["A"], 3080)
    rhs = profile.template("RHS", h=200, b=100, t=10)
    assert all(p["role"] == "internal" for p in rhs) and profile.properties(rhs)["A"] == 2 * 100 * 10 + 2 * 180 * 10
    kind, params = profile.from_c5("HEA", [200])
    assert kind == "I" and params == {"h": 190, "b": 200, "t_w": 6.5, "t_f": 10}
    a = profile.properties(profile.template(kind, **params))["A"]
    assert 0.9 * 5380 < a < 5380, "no root radii: a little below SZS C5's 5380 mm²"
    assert profile.from_c5("ROR", [101.6, 10]) is None and profile.from_c5("RND", [20]) is None
    assert profile.from_c5("RRW", [200, 100, 10])[0] == "RHS" and profile.from_c5("L", [100, 50, 8])[0] == "L"
    assert "t_w must be below b" in _raised(lambda: profile.template("I", h=200, b=5, t_w=6, t_f=10))
    assert "no model" in _raised(profile.template, "Z")


def test_the_roles_are_the_schemas():
    schema = json.loads((ROOT / "schemas" / "profile-source.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["parts"]["items"]["properties"]["role"]["enum"] == list(profile.ROLES)
    assert schema["properties"]["schema_version"]["enum"] == [profile.SOURCE_SCHEMA_VERSION]


def test_a_malformed_source_is_refused_naming_the_field():
    """ARCH-003: the schema, an id, an id that reads as an SZS C5 designation, a unit, no part, a side of 0, a role outside ROLES, a name twice."""
    good = profile.new_source("PR-01")
    assert profile.check_source(good) is good
    for change, said in (({"schema_version": "2.0"}, "schema"), ({"id": "PR 01"}, "id"), ({"id": "HEA200"}, "SZS C5"),
                         ({"unit": "cm"}, "unit"), ({"parts": []}, "parts")):
        assert said in _raised(profile.check_source, dict(good, **change)), change
    bad = json.loads(json.dumps(good))
    bad["parts"][0]["b"] = 0
    assert "parts[0]" in _raised(profile.check_source, bad) and "b is 0" in _raised(profile.check_source, bad)
    bad = json.loads(json.dumps(good))
    bad["parts"][1]["role"] = "web"
    assert "role" in _raised(profile.check_source, bad)
    bad = json.loads(json.dumps(good))
    bad["parts"][1]["name"] = bad["parts"][0]["name"]
    assert "twice" in _raised(profile.check_source, bad)
    assert profile.is_free_id("PR-01") and profile.is_free_id("HEAVY") and not profile.is_free_id("IPE 200")


def test_a_position_names_a_free_profile_and_the_export_resolves_it():
    """REQ-003, REQ-004, ARCH-RISK-101: section type USR, dimension the id; the export writes a 1.5 record, warns where the file is missing, stops where it is malformed; a cited profile is listed by `cited_by` (D-16)."""
    import export_all
    here = conftest.project_copy("free_profile")
    (here.profiles_dir / "PR-01.json").unlink(missing_ok=True)   # the example's own free profile: this test writes its PR-01 itself
    with project.using(here):
        row ={"position": "S010", "type": "Stütze", "material": "Stahl", "strength_class": "S355", "section_type": "USR",
               "dimension": "PR-01", "units": "", "moisture_class": None, "description": ""}
        (record,), notes = export_all._positions([row])
        assert record["section"] == {"type": "USR", "kind": "user", "text": "USR PR-01", "id": "PR-01"} and record["schema_version"] == "1.5"
        assert [n.code for n in notes] == ["position_profile_missing"], notes
        validation.validate_structure(record, "position")
        validation.validate_positions_business(record)
        here.profiles_dir.mkdir(parents=True, exist_ok=True)
        (here.profiles_dir / "PR-01.json").write_text(json.dumps(profile.new_source("PR-01")), encoding="utf-8")
        _, notes = export_all._positions([row])
        assert not notes, notes
        assert profile.resolve("pr-01")["properties"]["A"] == 3080 and profile.resolve("PR-02") is None
        broken = profile.new_source("PR-01")
        broken["parts"][0]["role"] = "web"
        (here.profiles_dir / "PR-01.json").write_text(json.dumps(broken), encoding="utf-8")
        assert "profiles/PR-01.json" in _raised(export_all._positions, [row])
    assert profile.cited_by("pr-01", [dict(record, id="S010"), {"id": "T001", "section": section.parse("rec", "100/200", "mm")}]) == ["S010"]
    assert "profiles" in project.SOURCE_FOLDERS and "steel" in project.SOURCE_FOLDERS
