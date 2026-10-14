"""Snow loads entered in Woodcore (calc/domains/snow_source.py, issue #36, spec docs/requirements/completed/2026-10-10-issues-github-35-a-39.md).

What is held, each value worked out here by hand from SIA 261:2020 (pp. 26-29, 115) rather than read back from the module:

* **REQ-003** -- equation (10) and its floor of 0.9 kN/m², h_ref = h_0 + Δh of Anhang D, C_e of 5.2.4; the five load models of the Belastungsannahmen workbook -- flat (and Figur 4 over 20 m), mono-pitch (5.3.2), duo-pitch, shed with mu_2m --; mu_1 = 0.8 where the sliding is hindered (5.3.4) on every side and **before** the half of model 2, which the workbook's N37/N38 forget (D-02); no snow above 60° where it slides (5.3.3);
* **REQ-004** -- the curved roof, the third column of Figur 3: 0.8 in model 1, mu_3 and mu_3/2 in model 2, mu_3 = 0.2 + 0.09 alpha up to 2.0 (Figur 2);
* **CON-001** -- every value read from calc/norms/sia261-2020-5.2-schnee.json, which names its edition and pages; above 2000 m the source is computed and `warnings` says so to the tab, nothing in the instance (5.1.4; spec 2026-10-14-neige-vent-affichage-altitude, REQ-003, REQ-004);
* the sketch of the disposition, the tab's alone (`sketch`, D-03) -- the export carries no drawing of the snow (D-02) --, and the export beside a workbook's sheets.
"""

import json

import conftest
import registry
import validation
from domains import snow_source
from norms import sia261_snow


def _src(**change):
    src = snow_source.new_source("SN-01")
    src.update(change)
    return src


def _loads(src):
    snow_source.check_source(src)
    instance = snow_source.build_instance(src)
    return {k: v["value"] for k, v in instance["vars"].items()}, instance


def _sk(h):
    return max(0.4 * (1 + (h / 350) ** 2), 0.9)


def test_the_norm_file_names_its_edition_and_pages_and_is_checked():
    c = sia261_snow.clause()
    assert c["pages"] == [26, 27, 28, 29, 115] and c["s_k"]["equation"] == "10"
    assert [e["value"] for e in c["exposure"]["choices"]] == [1.0, 0.8, 1.2]
    assert c["corrections"]["values"] == [-200, 0, 200, 400, 500]
    assert sia261_snow.curve(c["mu_1"]["points"], 45) == 0.4 and sia261_snow.curve(c["mu_1"]["points"], 70) == 0.0
    assert abs(sia261_snow.curve(c["mu_2"]["points"], 15) - 1.2) < 1e-12 and sia261_snow.curve(c["mu_2"]["points"], 50) == 1.6
    assert abs(sia261_snow.curve(c["mu_3"]["points"], 10) - 1.1) < 1e-12 and sia261_snow.curve(c["mu_3"]["points"], 40) == 2.0


def test_s_k_and_h_ref_follow_equation_10_and_anhang_d():
    v, _ = _loads(_src(h_0=438, correction=200))
    assert v["h_ref"] == 638 and abs(v["s_k"] - _sk(638)) < 1e-12
    v, _ = _loads(_src(h_0=150, correction=0))
    assert v["s_k"] == 0.9, "the floor of (10)"
    v, _ = _loads(_src(exposure="exposed", c_t=0.9))
    assert v["ce"] == 0.8 and v["ct"] == 0.9


def test_the_five_models_of_the_workbook():
    base = lambda src: {"normal": 1.0, "exposed": 0.8, "sheltered": 1.2}[src["exposure"]] * src["c_t"] * _sk(src["h_0"] + src["correction"])
    src = _src(roof="flat", length=15, width=12)
    v, inst = _loads(src)
    assert inst["results"] == ["q_k1"] and abs(v["q_k1"] - 0.8 * base(src)) < 1e-12
    src = _src(roof="flat", length=24, width=22)
    v, _ = _loads(src)
    assert abs(v["mu_1"] - (0.8 + 0.2 * 4 / 5)) < 1e-12, "Figur 4 between 20 and 25 m"
    src = _src(roof="flat", length=40, width=18)
    assert _loads(src)[0]["mu_1"] == 0.8, "Figur 4 only where both sides exceed 20 m (5.3.5)"
    src = _src(roof="mono", alpha_1=45)
    v, inst = _loads(src)
    assert abs(v["q_k1"] - 0.4 * base(src)) < 1e-12 and abs(v["q_k1h"] - 0.2 * base(src)) < 1e-12
    src = _src(roof="duo", alpha_1=20, alpha_2=40)
    v, inst = _loads(src)
    assert inst["results"] == ["q_k11", "q_k12", "q_k11h", "q_k12h"]
    assert abs(v["mu_12"] - 0.8 * 20 / 30) < 1e-12 and abs(v["q_k12h"] - v["mu_12"] / 2 * base(src)) < 1e-12
    src = _src(roof="shed", alpha_1=30, alpha_2=20)
    v, inst = _loads(src)
    assert abs(v["mu_2m"] - (0.8 + 0.8 * 25 / 30)) < 1e-12 and inst["results"][-1] == "q_k2m"


def test_hindered_sliding_takes_0_8_before_the_half_and_a_steep_roof_free_to_slide_carries_none():
    """5.3.4 on every side and before model 2 halves it -- the workbook's N37/N38 halve the raw mu_1(alpha) (D-02); 5.3.3 above 60°."""
    free = _loads(_src(roof="duo", alpha_1=50, alpha_2=50))[0]
    hindered = _loads(_src(roof="duo", alpha_1=50, alpha_2=50, sliding="hindered"))[0]
    assert hindered["mu_11"] == hindered["mu_12"] == 0.8
    assert abs(hindered["q_k11h"] - hindered["q_k11"] / 2) < 1e-12 and hindered["q_k11h"] > free["q_k11h"] * 2
    steep = _loads(_src(roof="mono", alpha_1=65))[0]
    assert steep["q_k1"] == 0.0
    assert _loads(_src(roof="mono", alpha_1=65, sliding="hindered"))[0]["mu_1"] == 0.8


def test_the_curved_roof_is_the_third_column_of_figur_3():
    """REQ-004 (D-01): model 1 uniform 0.8, model 2 the two triangles mu_3/2 and mu_3 -- the two results of model 2 and the one of model 1."""
    v, inst = _loads(_src(roof="curved", alpha_1=10))
    base = _sk(500)
    assert inst["results"] == ["q_k1", "q_k3", "q_k3h"]
    assert abs(v["q_k1"] - 0.8 * base) < 1e-12 and abs(v["mu_3"] - 1.1) < 1e-12 and abs(v["q_k3h"] - 0.55 * base) < 1e-12
    svg = snow_source.sketch(_src(roof="curved", alpha_1=10))
    assert svg.count("<polygon") >= 5 and "μ3/2" in svg and "μ3" in svg


def test_each_defect_is_refused_naming_the_field():
    for change, word in (({"height_step": "yes", "schema_version": "1.2"}, "height_step"), ({"height_step": True}, "1.2"), ({"correction": 100}, "Anhang D"), ({"exposure": "windy"}, "exposure"),
                         ({"c_t": 1.2}, "c_t"), ({"roof": "dome"}, "roof"), ({"roof": "flat"}, "length"), ({"alpha_1": 95}, "alpha_1"),
                         ({"sliding": "maybe"}, "sliding")):
        try:
            snow_source.check_source(_src(**change), "loads/snow/probe.json")
        except validation.ValidationError as exc:
            assert word in str(exc), (change, str(exc))
        else:
            raise AssertionError(change)


def test_the_2000_m_limit_reads_the_site_altitude():
    """SIA 261 5.1.4 (p. 25) speaks of works above 2000 m -- the site's h_0, not the reference height h_0 + Δh of Anhang D (spec 2026-10-12-audit-issues-47-48-49, REQ-002). Since spec 2026-10-14-neige-vent-affichage-altitude (REQ-003, REQ-004, which reverses that spec's refusal) a site above it is computed by equation (10) and `warnings` names it, the limit and the clause read from the norm file; the instance says nothing of it, the report printing no warning (D-04)."""
    values, instance = _loads(_src(h_0=1900, correction=200))
    assert values["h_ref"] == 2100 and abs(values["s_k"] - _sk(2100)) < 1e-12
    assert snow_source.warnings(_src(h_0=1900, correction=200)) == [] and snow_source.warnings(_src(h_0=2000)) == []
    high = _src(h_0=2100, correction=-200)
    values, instance = _loads(high)
    assert values["h_0"] == 2100 and values["h_ref"] == 1900 and abs(values["s_k"] - _sk(1900)) < 1e-12
    limit = sia261_snow.clause()["max_altitude"]
    assert snow_source.warnings(high) == [("above_limit", {"h_0": 2100, "limit": limit["value"], "ref": limit["norm_ref"]})]
    assert limit["value"] == 2000 and limit["norm_ref"] == "5.1.4"
    said = json.dumps(instance, ensure_ascii=False)
    assert "5.1.4" not in said and "above_limit" not in said, "the warning is the tab's, never the instance's"


def test_the_limit_is_read_from_the_norm_file():
    """CON-001: the limit `warnings` compares with is the norm file's, not a number of the module."""
    read = sia261_snow.clause
    clause = dict(read())
    clause["max_altitude"] = dict(clause["max_altitude"], value=1500)
    sia261_snow.clause = lambda: clause
    try:
        assert snow_source.warnings(_src(h_0=1600))[0][1]["limit"] == 1500
        assert snow_source.warnings(_src(h_0=1400)) == []
    finally:
        sia261_snow.clause = read


def test_a_height_step_and_a_cornice_are_said_not_computed():
    """REQ-003 (D-04, D-19): a roof whose source says `height_step` names the extra load of Figur 5 (5.3.6); works above 800 m name the cornice of 5.3.7 -- each a var with its clause and description, no load computed, the 800 m read from the norm file."""
    values, instance = _loads(_src(h_0=700))
    assert "hoehensprung" not in values and "schneeueberhang" not in values
    assert sia261_snow.clause()["cornice"]["min_altitude"] == 800
    values, instance = _loads(_src(h_0=900, height_step=True, schema_version="1.2"))
    step, cornice = instance["vars"]["hoehensprung"], instance["vars"]["schneeueberhang"]
    assert step["norm_ref"] == "5.3.6" and "Figur 5" in step["description"] and step["level"] == 1
    assert cornice["norm_ref"] == "5.3.7" and "nicht berechnet" in cornice["description"]
    assert instance["results"] == _loads(_src(h_0=900))[1]["results"], "nothing more is computed"


def test_the_schema_version_is_a_floor():
    """D-19: 1.2 is 1.1 with `height_step`, written only when the roof has one. A source without a step is saved as before (1.0, or 1.1 with links); a false step is dropped, not written; a step at 1.0 or 1.1 is refused."""
    src = snow_source.stamp_version(_src())
    assert src["schema_version"] == "1.0" and "height_step" not in src
    src = snow_source.stamp_version(_src(height_step=False))
    assert src["schema_version"] == "1.0" and "height_step" not in src
    src = snow_source.stamp_version(_src(height_step=True))
    assert src["schema_version"] == "1.2" and src["height_step"] is True
    snow_source.check_source(src)
    validation.validate_structure(src, snow_source.SOURCE_SCHEMA)


def test_the_export_carries_a_snow_source_and_no_drawing():
    """D-02, D-03: the instance declares no figure and hands the export no file -- the report prints no drawing of the snow, and no svg is written beside it."""
    here = conftest.project_copy("snow_source_export")
    folder = here.sources_dir / snow_source.FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SN-01.json").write_text(json.dumps(_src(roof="curved", alpha_1=25)), encoding="utf-8")
    files = {}
    data = registry.build_calculations([], here, files)
    instance = data["domains"]["snow-load"]["instances"]["SN-01"]
    assert instance["source_file"] == "loads/snow/SN-01.json" and "figures" not in instance and "_files" not in instance
    assert not [name for name in files if "snow-load" in name], files
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)


def test_show_calc_prints_no_drawing_of_the_snow_and_takes_the_manual_selection():
    """Issues #56, #57 (spec 2026-10-14-neige-vent-affichage-altitude, REQ-001, REQ-002, REQ-004): `show-calc("snow-load", id)` prints no drawing at any level, and `figure-1` is no key of it; `level: -1, shown:` picks the snow's and the wind's vars -- the call «Affichage» writes; a site above 2000 m compiles with no word of the limit."""
    import subprocess
    from domains import wind_source
    if not conftest.have_typst():
        raise conftest.Skip("typst is not on the path")
    here = conftest.PROJECT
    snow = here.sources_dir / snow_source.FOLDER / "SN-77.json"
    wind = here.sources_dir / wind_source.FOLDER / "WI-77.json"
    kept = (here.data_dir / "calculations.json").read_bytes()

    def compile_(body, name):
        d = conftest.probe_dir(name)
        (d / "probe.typ").write_text('#import "/commands.typ": *\n' + body + "\n", encoding="utf-8")
        return subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(d / "probe.typ"), str(d / "probe.svg")],
                              capture_output=True, text=True, encoding="utf-8"), d / "probe.svg"

    try:
        for path in (snow, wind):
            path.parent.mkdir(parents=True, exist_ok=True)
        src = _src(h_0=2100, roof="duo", alpha_1=20, alpha_2=30)
        src["id"] = "SN-77"
        snow.write_text(json.dumps(src, ensure_ascii=False), encoding="utf-8")
        w = wind_source.new_source("WI-77")
        w.update(table="45", h=9)
        wind.write_text(json.dumps(w, ensure_ascii=False), encoding="utf-8")
        registry.export(here)
        for level in (1, 2, 3):
            out, svg = compile_('#show-calc("snow-load", "SN-77", level: %d)' % level, "sn_show_%d" % level)
            assert out.returncode == 0, out.stderr
            assert "<image" not in svg.read_text(encoding="utf-8"), "no drawing of the snow at level %d" % level
        out, _svg = compile_('#show-calc("snow-load", "SN-77", level: -1, shown: (s_k: 1, q_k11: 2))', "sn_show_m1")
        assert out.returncode == 0, out.stderr
        out, _svg = compile_('#show-calc("snow-load", "SN-77", level: -1, shown: (figure-1: 2))', "sn_show_fig")
        assert out.returncode != 0 and "figure-1" in out.stderr, "the snow has no drawing to name"
        out, _svg = compile_('#show-calc("wind-load", "WI-77", level: -1, shown: (qp: 1))', "wi_show_m1")
        assert out.returncode == 0, out.stderr
    finally:
        snow.unlink(missing_ok=True)
        wind.unlink(missing_ok=True)
        (here.data_dir / "calculations.json").write_bytes(kept)
