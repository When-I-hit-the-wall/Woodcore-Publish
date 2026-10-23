"""Snow loads entered in Woodcore (calc/domains/snow_source.py, issue #36, spec docs/requirements/completed/2026-10-10-issues-github-35-a-39.md).

What is held, each value worked out here by hand from SIA 261:2020 (pp. 26-29, 115) rather than read back from the module:

* **REQ-003** -- equation (10) and its floor of 0.9 kN/m², h_ref = h_0 + Δh of Anhang D, C_e of 5.2.4; the five load models of the Belastungsannahmen workbook -- flat (and Figur 4 over 20 m), mono-pitch (5.3.2), duo-pitch, shed with mu_2m --; mu_1 = 0.8 where the sliding is hindered (5.3.4) on every side and **before** the half of model 2, which the workbook's N37/N38 forget (D-02); no snow above 60° where it slides (5.3.3);
* **REQ-004** -- the curved roof, the third column of Figur 3: 0.8 in model 1, mu_3 and mu_3/2 in model 2, mu_3 = 0.2 + 0.09 alpha up to 2.0 (Figur 2);
* **CON-001** -- every value read from calc/norms/sia261-2020-5.2-schnee.json, which names its edition and pages; above 2000 m the source is computed and `warnings` says so to the tab, nothing in the instance (5.1.4; spec 2026-10-14-neige-vent-affichage-altitude, REQ-003, REQ-004);
* the column of Figur 3 for the case's roof, drawn by one code for the tab and the export (`figure_svg`, spec 2026-10-22-onglet-neige-type, REQ-016, D-31, D-32: the drawing the spec 2026-10-14 kept out of the report, D-02, D-03, printed since) --, and the export beside a workbook's sheets.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json

import conftest
import line_levels
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
    # the pages are each edition's since the spec 2026-10-22-onglet-neige-type (ARCH-006): the chapter Ctrl+click opens, and each excerpt's own page (tests/test_norm_excerpts.py)
    from norms import excerpts
    assert excerpts.chapter(sia261_snow.SNOW, "fr")[1:] == (26, 29) and excerpts.chapter(sia261_snow.SNOW, "de")[1:] == (25, 28)
    assert excerpts.excerpt(sia261_snow.SNOW, "annexD", "fr").page == 115 and c["s_k"]["equation"] == "10"
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
    svg = snow_source.figure_svg(_src(roof="curved", alpha_1=10))
    # the two rows of model 2, each two triangles written «μ₃/2 = 0.55» and «μ₃ = 1.10» (a subscript is a <text> of its own: svg_text)
    assert svg.count(">/2 = 0.55<") == 2 and svg.count(">= 1.10<") == 2 and svg.count(">3<") >= 4 and ">0.80<" in svg


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


def test_a_height_step_is_said_not_computed_and_the_cornice_is_the_tabs():
    """REQ-003 (D-04, D-19): a roof whose source says `height_step` names the extra load of Figur 5 (5.3.6), a var with its clause and description, no load computed. The cornice of 5.3.7 left the file (spec 2026-10-22-onglet-neige-type, REQ-018, D-13): above 800 m the tab says it (`messages`), the instance holds no line of it -- the 800 m read from the norm file."""
    values, instance = _loads(_src(h_0=700))
    assert "hoehensprung" not in values and "schneeueberhang" not in values
    assert sia261_snow.clause()["cornice"]["min_altitude"] == 800
    values, instance = _loads(_src(h_0=900, height_step=True, schema_version="1.2"))
    step = instance["vars"]["hoehensprung"]
    assert step["norm_ref"] == "5.3.6" and "Figur 5" in step["description"] and "μ₁" in step["description"] and line_levels.level("snow-load", "hoehensprung") == 1 and "level" not in step
    assert "schneeueberhang" not in instance["vars"] and "cornice" in [m.code for m in snow_source.messages(_src(h_0=900))]
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


def test_the_export_carries_a_snow_source_and_its_figure():
    """REQ-016, D-31, D-32 (spec 2026-10-22-onglet-neige-type; D-02, D-03 of spec 2026-10-14 superseded): the instance declares one figure, the column of Figur 3 for its roof, under the snow's own Exports/Figures/, and hands the export its SVG -- the tab's drawing byte for byte, black and white, and with no word."""
    here = conftest.project_copy("snow_source_export")
    folder = here.sources_dir / snow_source.FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SN-01.json").write_text(json.dumps(_src(roof="curved", alpha_1=25)), encoding="utf-8")
    files = {}
    data = registry.build_calculations([], here, files)
    instance = data["domains"]["snow-load"]["instances"]["SN-01"]
    src = _src(roof="curved", alpha_1=25)
    assert instance["source_file"] == "loads/snow/SN-01.json" and "_files" not in instance
    [figure] = instance["figures"]
    assert figure["title"] == snow_source.FIGURE_TITLE[True] and figure["file"].endswith("/SN-01-fig3.svg")
    assert figure["file"] in files and files[figure["file"]] == snow_source.figure_svg(src), "the export's drawing is the tab's (ARCH-008)"
    import re
    assert set(re.findall(r'(?:fill|stroke)="([^"]+)"', files[figure["file"]])) <= {"none", "#ffffff", "#1f1f1f", "#8a8a8a"}, "black and white (T39)"
    assert "Lastmodell" not in files[figure["file"]] and "(2)" in files[figure["file"]], "no word in the report's drawing (D-31)"
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)


def test_the_written_out_snow_prints_its_figure_and_compiles_above_2000_m():
    """Issues #56, #57 (spec 2026-10-14-neige-vent-affichage-altitude, REQ-001, REQ-004), on the domains Woodcore writes out (spec 2026-10-21-commandes-typst-refonte, REQ-017; `#show-calc` until then): a site above 2000 m compiles with no word of the limit, its figure at the head of its file (spec 2026-10-22-onglet-neige-type, REQ-016); the wind's compiles too."""
    import subprocess
    from domains import wind_source
    if not conftest.have_typst():
        raise conftest.Skip("typst is not on the path")
    here = conftest.PROJECT
    snow = here.sources_dir / snow_source.FOLDER / "SN-77.json"
    wind = here.sources_dir / wind_source.FOLDER / "WI-77.json"
    kept = (here.data_dir / "calculations.json").read_bytes()

    def compile_(kind, rid, name):
        import project
        from domains import unfold
        data = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        with project.using(here):
            text = unfold.generate(unfold._module(kind).records(data)[rid], "de", kind)
        d = conftest.probe_dir(name)
        (d / "domain.typ").write_text(text, encoding="utf-8")
        (d / "probe.typ").write_text('#import "/000-Typst-Config/commands.typ": *\n#include "domain.typ"\n', encoding="utf-8")
        return subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(d / "probe.typ"), str(d / "probe.pdf")],
                              capture_output=True, text=True, encoding="utf-8"), text

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
        out, text = compile_("snow-load", "SN-77", "sn_written_out")
        assert out.returncode == 0, out.stderr
        assert "#figure(image(" in text and "SN-77-fig3.svg" in text and text.index("#figure(") < text.index("#var("), "the figure at the head of the file"
        out, _text = compile_("wind-load", "WI-77", "wi_written_out")
        assert out.returncode == 0, out.stderr
    finally:
        snow.unlink(missing_ok=True)
        wind.unlink(missing_ok=True)
        (here.data_dir / "calculations.json").write_bytes(kept)


def test_the_workbook_path_takes_c_e_and_the_corrections_from_the_norm_and_stops_on_a_table_that_disagrees():
    """REQ-003 (spec 2026-10-19-base-saine-nettoyage, lot 8): snow.py keeps the workbook's own labels and prints SIA 261's numbers, read from calc/norms/; a workbook table that says another number stops the import, naming the table."""
    import validation
    from domains import snow
    from norms import sia261_snow
    norm = sia261_snow.clause()
    pairs = [("normale Windexposition", 1), ("dem Wind stark ausgesetzte Lage", 0.8), ("vor Wind geschützte Lage", 1.2)]
    held = snow._held(pairs, [c["value"] for c in norm["exposure"]["choices"]], snow.EXPOSURE_TABLE, "5.2.4")
    assert [label for label, _ in held] == [label for label, _ in pairs] and [v for _, v in held] == [1.0, 0.8, 1.2]
    try:
        snow._held([("+300", 300)], norm["corrections"]["values"], snow.CORRECTION_TABLE, "Anhang D")
    except validation.ValidationError as exc:
        assert str(exc).startswith("Dropdowns!B30:C34: '+300' gives 300") and "Anhang D" in str(exc), exc
    else:
        raise AssertionError("a correction SIA 261 Anhang D does not give was read")


# --- spec 2026-10-22-onglet-neige-type, lot 3: the free C_e, the messages, the declaration -------------------------------


def test_a_free_c_e_is_schema_1_3_and_is_computed_without_a_message():
    """REQ-021, D-10: `exposure: "custom"` and `c_e` -- written at 1.3, the highest floor a field asks; computed with the number as it is, said by no message; a 1.2 source with a step and links is still read; a C_e written beside a choice of the norm, or at 0, is refused naming `c_e`."""
    src = snow_source.stamp_version(_src(exposure="custom", c_e=0.95, height_step=True))
    assert src["schema_version"] == "1.3"
    validation.validate_structure(src, snow_source.SOURCE_SCHEMA)
    values, instance = _loads(src)
    assert values["ce"] == 0.95 and "choices" not in instance["vars"]["ce"]
    base = _loads(_src())[0]
    assert abs(values["q_k11"] - base["q_k11"] * 0.95) < 1e-12
    assert [m for m in snow_source.messages(src) if m.field in ("exposure", "c_e")] == []
    # back to a button: the free number is not written, the version falls back
    src = snow_source.stamp_version(dict(src, exposure="normal"))
    assert "c_e" not in src and src["schema_version"] == "1.2"
    linked = _src(height_step=True, schema_version="1.2", links={"h_0": {"domain": "snow-load", "instance": "SN-02", "var": "h_0"}})
    snow_source.check_source(linked)
    for change, field in (({"exposure": "custom", "c_e": 0, "schema_version": "1.3"}, "c_e"), ({"c_e": 0.9, "schema_version": "1.3"}, "c_e"),
                          ({"exposure": "custom", "c_e": 0.9}, "1.3")):
        try:
            snow_source.check_source(_src(**change))
        except validation.ValidationError as exc:
            assert field in str(exc), (change, str(exc))
        else:
            raise AssertionError(change)


def test_the_messages_name_their_field_and_say_red_or_orange():
    """REQ-008, REQ-008b, D-19: an error per field the calculation cannot read, each naming its field; above 2000 m an info, the calculation made; else above 800 m the cornice; C_T under 1; a slope of 60° free to slide; a large flat roof; a height step -- every threshold and clause the norm file's."""
    from domains.contracts import Message
    c = sia261_snow.clause()

    def said(**change):
        return [(m.code, m.field, m.severity) for m in snow_source.messages(_src(**change))]
    assert said() == []
    assert said(h_0=2050) == [("above_limit", "h_0", "info")]
    assert snow_source.messages(_src(h_0=2050))[0] == Message("above_limit", "h_0", "info", {"h_0": 2050, "limit": 2000, "ref": "5.1.4"})
    assert said(h_0=850) == [("cornice", "h_0", "info")] and said(h_0=800) == []
    assert snow_source.messages(_src(h_0=850))[0].params == {"h_0": 850, "limit": c["cornice"]["min_altitude"], "ref": "5.3.7"}
    assert said(c_t=0) == [("c_t", "c_t", "error")] and said(c_t=0.9) == [("ct_low", "c_t", "info")]
    assert said(alpha_2=65) == [("steep", "alpha_2", "info")] and said(alpha_2=65, sliding="hindered") == []
    assert said(roof="flat", length=30, width=25) == [("large_flat", "length", "info")]
    assert said(roof="flat", length=0, width=25) == [("dimension", "length", "error")]
    assert said(alpha_1=95) == [("alpha", "alpha_1", "error")] and said(h_0=-5) == [("h_0", "h_0", "error")]
    assert said(height_step=True, schema_version="1.2") == [("height_step", "height_step", "info")]
    # the export says only what it said before: the site above the limit
    assert snow_source.warnings(_src(h_0=850)) == [] and [code for code, _p in snow_source.warnings(_src(h_0=2050))] == ["above_limit"]


def test_the_declaration_is_read_from_the_norm_and_cites_excerpts_that_exist():
    """ARCH-002, ARCH-006, UI-004: the snow tab's form -- the building first, C_e's buttons sheltered, normal, exposed with a free value, the five roofs as tiles --, every choice read off the norm file or this module's words, and every excerpt an ⓘ cites one of the norm file's (the prototype's FIELD_NORM)."""
    from domains import contracts
    from norms import excerpts
    assert isinstance(snow_source, contracts.CalcTabDomain)
    d = snow_source.declaration()
    assert [s for s, _keys in d.sections] == ["building", "site", "roof"] and d.sections[0][1] == ("length", "width")
    exposure = d.field("exposure")
    assert [(c.id, c.value) for c in exposure.choices] == [("sheltered", 1.2), ("normal", 1.0), ("exposed", 0.8)]
    assert exposure.free_id == "custom" and exposure.free_key == "c_e"
    assert [c.value for c in d.field("correction").choices] == sia261_snow.clause()["corrections"]["values"]
    roof = d.field("roof")
    assert roof.kind == "tiles" and [c.id for c in roof.choices] == list(snow_source.ROOFS)
    assert {c.id: c.excerpts for c in roof.choices} == {"flat": ("5.3.5", "fig4"), "mono": ("5.3.2", "fig3"), "duo": ("fig3",), "shed": ("fig3",), "curved": ("fig3",)}
    assert d.field("height_step").excerpts == ("5.3.6", "fig5") and d.field("correction").excerpts == ("annexD",)
    known = set(excerpts.ids(d.norm))
    for f in d.fields:
        assert set(f.excerpts) <= known, f.key
        for c in f.choices:
            assert set(c.excerpts) <= known, (f.key, c.id)
    assert {f.key for f in d.fields if f.linkable} | {f.free_key for f in d.fields if f.free_key} == set(snow_source.LINKABLE[snow_source.links.SELF]), "every number may follow a variable, a free C_e too (issue #42)"
    assert all(f.kind in contracts.FIELD_KINDS for f in d.fields)


def test_the_form_shows_the_slopes_a_roof_has_and_always_the_building():
    assert "alpha_2" not in snow_source.visible_fields(_src(roof="mono")) and "alpha_1" in snow_source.visible_fields(_src(roof="mono"))
    assert {"alpha_1", "alpha_2"}.isdisjoint(snow_source.visible_fields(_src(roof="flat")))
    for roof in snow_source.ROOFS:
        assert {"length", "width", "h_0", "exposure", "roof", "sliding", "height_step"} <= set(snow_source.visible_fields(_src(roof=roof)))


def test_the_results_are_what_is_computed_never_an_input():
    """REQ-009: h_ref, s_k, the μ and the q_k -- never h_0 or Δh."""
    _values, instance = _loads(_src(h_0=900))
    shown = snow_source.results(instance)
    assert shown[:4] == ["h_ref", "s_k", "mu_11", "mu_12"], shown
    assert {"h_ref", "s_k", "mu_11", "mu_12", "q_k11", "q_k12", "q_k11h", "q_k12h"} <= set(shown)
    assert not set(shown) & set(snow_source.INPUTS)


def test_a_french_file_prints_no_german_word_and_mu_as_mu():
    """REQ-019: «Figur 3», «Anhang D», the symbol «Dachform» and «mu_1» are the three defects the engineer found in a French file; written in French they are «Figure 3», «Annexe D», «Forme de la toiture», μ₁."""
    from domains import unfold
    for roof in ("duo", "flat"):
        src = _src(roof=roof, length=30, width=25, sliding="hindered")
        record = dict(snow_source.build_instance(src), id="SN-01", kind="snow-load", domain_label="Schneelast")
        text = unfold._generate_load(record, "fr")
        for german in ("Figur ", "Anhang", '"Dachform"', "Abgleiten des Schnees", "toiture mu_1"):   # the description's mu_1, not the key mu_11
            assert german not in text, (roof, german)
        assert "Figure " in text and "Annexe D" in text and "Forme de la toiture" in text and "μ₁" in text


def test_a_source_1_0_read_and_written_again_is_the_same_bytes():
    """REQ-021: a source that uses nothing of 1.1 to 1.3 keeps its version and its bytes through the window's draft (stamp_version) and its writer."""
    import engine
    src = _src(roof="duo")
    path = conftest.tmpdir("snow_bytes") / "SN-01.json"
    engine.write_json(path, src)
    before = path.read_bytes()
    again = snow_source.stamp_version(json.loads(before.decode("utf-8")))
    engine.write_json(path, again)
    assert path.read_bytes() == before and again["schema_version"] == "1.0"
