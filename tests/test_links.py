"""A field that follows a variable of the export (calc/domains/links.py, spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, lot 1).

What is held:

* **units** (REQ-003, REQ-004, D-15): a variable fills a field of the same dimension by calc/units.py -- kN and N, kNm and Nmm, mm and m, kN/m² and N/mm² --, converted into the field's unit; ° only °, and a field without a unit only a variable without one, never rad;
* **resolution** (REQ-002, REQ-005, REQ-006): factor × variable + offset; a variable gone, not a number or of another dimension keeps the field's last value with a warning, never a stop; a load may name only another load or a «Formule» domain (ARCH-005, D-11);
* **the shape** (D-17): a link sits beside its field in `links`, and a key no field of the entry has, or a link that names no variable, is refused naming it;
* **the member checks**: a linked field takes the variable's value in the record, which says where it came from (REQ-012); a source with links is 1.1 and only then; the export writes 1.1 and passes its schema;
* **the static models**: a point's x follows a variable, a magnitude naming one keeps its `last` value where the variable is gone, and the export carries where each linked field came from;
* **the export's values**: built from the export in memory, the «Formule» domains computed against the loads just read and not the last export on the disk (ARCH-RISK-003);
* **the window's side** (D-14): `refresh` writes the value a variable gives now into the source, and leaves a field whose variable is gone as it is.
"""

import copy
import json

import conftest

import project
import validation
import variable_sources
from domains import links, member_check, statics

CALCULATIONS = {"domains": {
    "live-load": {"instances": {"A1": {"vars": {"Q_k": {"value": 2, "unit": "kN"}, "q_k": {"value": 2, "unit": "kN/m²"},
                                                "kategorie": {"value": "A1", "unit": ""}}}}},
    "snow-load": {"instances": {"SL": {"vars": {"L": {"value": 17.5, "unit": "m"}, "F": {"value": 12500, "unit": "N"}}}}},
}}
VALUES = links.index(CALCULATIONS, records=[("connection", {"VU-1": {"vars": {"N": {"value": 4, "unit": "kN"}}}})],
                     formulas={"poutre-p1": {"M_d": {"value": 14.0625, "unit": "kNm"}}})


def _refused(call, *words):
    try:
        call()
    except validation.ValidationError as exc:
        for word in words:
            assert word in str(exc), f"the refusal {exc} does not name {word!r}"
        return str(exc)
    raise AssertionError("accepted")


# --- units ---------------------------------------------------------------------------

def test_a_variable_fills_a_field_of_its_dimension_and_no_other():
    yes = [("N", "kN"), ("kN", "MN"), ("Nmm", "kNm"), ("m", "mm"), ("kN/m²", "N/mm²"), ("kN/m2", "kN/m²"), ("°", "°"), ("", "")]
    no = [("kNm", "kN"), ("mm", "kN"), ("kN/m", "kN/m²"), ("rad", "°"), ("rad", ""), ("", "rad"), ("", "kN"), ("kN", "")]
    for unit, field in yes:
        assert links.compatible(unit, field), f"{unit!r} should fill a field in {field!r}"
    for unit, field in no:
        assert not links.compatible(unit, field), f"{unit!r} should not fill a field in {field!r}"


def test_a_value_is_converted_into_the_field_s_unit():
    assert links.convert(12500, "N", "kN") == 12.5
    assert abs(links.convert(3e6, "Nmm", "kNm") - 3.0) < 1e-12
    assert links.convert(2.5, "m", "mm") == 2500
    assert abs(links.convert(2.4, "kN/m²", "N/mm²") - 2.4e-3) < 1e-15
    assert links.convert(7, "kN", "kN") == 7


# --- resolution ------------------------------------------------------------------------

def test_factor_and_offset_then_the_conversion():
    link = links.make("snow-load", "SL", "F", factor=1.5, offset=2)
    found = links.resolve(link, VALUES, "kN", last=0)
    assert not found["stale"] and not found["missing"]
    # 1.5 × 12500 N + 2 N, in kN: the offset is in the variable's own unit, as a static load's always was
    assert abs(found["value"] - (1.5 * 12500 + 2) / 1000) < 1e-12
    assert found["base_value"] == 12500 and found["base_unit"] == "N" and found["from"] == "snow-load/SL/F"


def test_a_variable_that_cannot_be_read_keeps_the_last_value_with_a_warning():
    cases = [
        (links.make("snow-load", "SL", "gone"), "link_missing"),
        (links.make("live-load", "A1", "kategorie"), "link_not_a_number"),
        (links.make("snow-load", "SL", "L"), "link_unit"),       # metres in a field in kN
    ]
    for link, code in cases:
        found = links.resolve(link, VALUES, "kN", last=9.5)
        assert found["stale"] and found["value"] == 9.5, found
        assert found["missing"].code == code and link["var"] in str(found["missing"])


def test_a_formula_domain_is_named_by_its_origin_and_its_id():
    link = links.from_choice(links.FORMULAS, "poutre-p1", "M_d", None)
    assert link == {"domain": links.FORMULAS, "instance": "poutre-p1", "var": "M_d", "origin": links.FORMULAS}
    assert links.resolve(link, VALUES, "kNm")["value"] == 14.0625
    assert links.link_text(link) == "formulas:poutre-p1/M_d"
    # the export's domain by its address; a document's registry by nothing (D-02)
    assert links.from_choice("export", "snow-load · SL", "L", ("snow-load", "SL")) == {"domain": "snow-load", "instance": "SL", "var": "L"}
    assert links.from_choice("rs", "Rapport", "x", None) is None


def test_a_load_follows_only_a_load_or_a_formula_domain():
    from_connection = links.make("connection", "VU-1", "N")
    assert links.resolve(from_connection, VALUES, "kN")["value"] == 4
    refused = links.resolve(from_connection, VALUES, "kN", last=1, consumer=links.LOADS)
    assert refused["stale"] and refused["missing"].code == "link_not_allowed"
    assert not links.resolve(links.make("live-load", "A1", "Q_k"), VALUES, "kN", consumer=links.LOADS)["stale"]
    assert not links.resolve(links.from_choice(links.FORMULAS, "poutre-p1", "M_d", None), VALUES, "kNm", consumer=links.LOADS)["stale"]


# --- the shape -----------------------------------------------------------------------

def test_a_link_beside_a_field_no_entry_has_or_naming_nothing_is_refused():
    def check(entry):
        def fail(message):
            raise validation.ValidationError(message)
        links.check_links(entry, {"N": None}, fail, "probe")
    check({"links": {"N": {"domain": "a", "instance": "b", "var": "c", "factor": 2}}})
    _refused(lambda: check({"links": {"M": {"domain": "a", "instance": "b", "var": "c"}}}), "'M'", "N")
    _refused(lambda: check({"links": {"N": {"domain": "a", "instance": "", "var": "c"}}}), "instance")
    _refused(lambda: check({"links": {"N": {"domain": "a", "instance": "b", "var": "c", "factor": "2"}}}), "factor")
    _refused(lambda: check({"links": {"N": {"domain": "a", "instance": "b", "var": "c", "what": 1}}}), "what")
    _refused(lambda: check({"links": []}), "links")


def test_a_plain_link_is_three_keys():
    assert links.make("d", "i", "v") == {"domain": "d", "instance": "i", "var": "v"}
    assert links.make("d", "i", "v", factor=1.5, offset=0) == {"domain": "d", "instance": "i", "var": "v", "factor": 1.5}


# --- the member checks -------------------------------------------------------------------

POSITIONS = {"T001": {"strength_class": "C24", "moisture_class": 2, "section": {"type": "rec", "kind": "timber", "text": "100/200 mm", "b": 100, "h": 200}}}


def _linked_check():
    src = member_check.new_source("ZT-L")
    src.update(position="T001", N={"value": 25, "unit": "kN"}, section={"type": "rec", "b": 120, "h": 240},
               links={"N": links.make("snow-load", "SL", "F", factor=1.5), "section.b": links.make("snow-load", "SL", "L")})
    return member_check.stamp_version(src)


def test_a_check_s_linked_field_takes_the_variable_s_value_and_says_where_it_came_from():
    src = _linked_check()
    assert src["schema_version"] == member_check.LINKED_SCHEMA_VERSION
    member_check.check_source(src, "checks/ZT-L.json")
    src["links"]["section.b"] = links.make("snow-load", "SL", "F")    # newtons for a side in mm: kept, warned
    record = member_check.resolve(src, POSITIONS, VALUES)
    assert record["N"] == {"value": 18.75, "unit": "kN"}                # 1.5 × 12500 N, in kN
    assert record["section"]["b"] == 120                                 # its last value
    assert record["links"]["N"]["variable"]["var"] == "F" and not record["links"]["N"]["stale"]
    assert record["links"]["section.b"]["stale"]
    assert any("section.b" in str(w) for w in record["warnings"])
    # the source itself is not changed by the resolution
    assert src["N"] == {"value": 25, "unit": "kN"}


def test_a_check_without_links_stays_as_it_was_and_links_need_1_1():
    plain = member_check.stamp_version(member_check.new_source("ZT-P"))
    assert plain["schema_version"] == member_check.SOURCE_SCHEMA_VERSION and "links" not in plain
    linked = _linked_check()
    linked["schema_version"] = member_check.SOURCE_SCHEMA_VERSION
    _refused(lambda: member_check.check_source(linked, "checks/ZT-L.json"), "links", "1.1")
    stated_none = _linked_check()
    stated_none["section"] = None
    _refused(lambda: member_check.check_source(stated_none, "checks/ZT-L.json"), "section.b", "no section")
    wrong = _linked_check()
    wrong["links"]["moisture_class"] = links.make("a", "b", "c")         # a choice from a list takes no variable (T6)
    _refused(lambda: member_check.check_source(wrong, "checks/ZT-L.json"), "moisture_class")


def test_the_check_export_with_a_link_is_1_1_and_follows_the_variable():
    here = conftest.project_copy("links_checks")
    _without_fire(here)
    with project.using(here):
        src = _linked_check()
        (here.checks_dir / "ZT-L.json").write_text(json.dumps(src, indent=2), encoding="utf-8")
        data = member_check.prepare(here, POSITIONS, VALUES)
        assert data["schema_version"] == member_check.LINKED_EXPORT_VERSION
        validation.validate_structure(data, "checks")
        assert data["checks"]["ZT-L"]["N"]["value"] == 18.75
        # the variable changes: the next export follows it (REQ-002)
        changed = copy.deepcopy(CALCULATIONS)
        changed["domains"]["snow-load"]["instances"]["SL"]["vars"]["F"]["value"] = 20000
        again = member_check.prepare(here, POSITIONS, links.index(changed))
        assert again["checks"]["ZT-L"]["N"]["value"] == 30
        # no link anywhere: the export is the 1.0 it always was
        (here.checks_dir / "ZT-L.json").unlink()
        assert member_check.prepare(here, POSITIONS, VALUES)["schema_version"] == member_check.EXPORT_SCHEMA_VERSION


# --- the static models ------------------------------------------------------------------

def _model():
    source = statics.new_source("LK")
    source["points"] = [{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 4, "z": 0, "links": {"x": links.make("snow-load", "SL", "L")}}]
    source["members"] = [{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}]
    source["supports"] = [{"id": "A1", "point": "P1", "type": "pinned"}, {"id": "A2", "point": "P2", "type": "roller"}]
    source["point_loads"] = [{"id": "F1", "point": "P2", "direction": "vertical",
                              "magnitude": {"domain": "snow-load", "instance": "SL", "var": "gone", "last": {"value": 3, "unit": "kN"}},
                              "label": "", "show": "value"}]
    return statics.stamp_version(source)


def test_a_static_model_s_point_follows_a_variable_and_a_gone_load_keeps_its_last_value():
    source = _model()
    assert source["schema_version"] == statics.LINKED_SCHEMA_VERSION
    statics.check_source(source, "LK.json")
    followed, provenance, notes = statics.follow_links(source, VALUES)
    assert followed["points"][1]["x"] == 17.5 and source["points"][1]["x"] == 4
    assert provenance[0]["entry"] == "P2" and provenance[0]["field"] == "x" and not provenance[0]["stale"]
    assert not notes
    found = statics.resolve(source["point_loads"][0]["magnitude"], None, VALUES)
    assert found["value"] == 3 and found["unit"] == "kN" and found["missing"]
    # without its 1.2, a model following a variable is refused
    old = copy.deepcopy(source)
    old["schema_version"] = statics.SOURCE_SCHEMA_VERSION
    _refused(lambda: statics.check_source(old, "LK.json"), "1.2")


def test_the_statics_export_carries_where_a_linked_field_came_from():
    folder = conftest.tmpdir("links_statics")
    (folder / "LK.json").write_text(json.dumps(_model(), indent=2), encoding="utf-8")
    data, _files, notes = statics.prepare(folder, VALUES)
    assert data["schema_version"] == statics.LINKED_EXPORT_VERSION
    assert data["models"]["LK"]["links"][0]["variable"]["var"] == "L"
    assert any("gone" in str(note) for note in notes)


def test_a_model_following_nothing_is_saved_at_1_1():
    source = statics.new_source("PL")
    assert statics.stamp_version(source)["schema_version"] == statics.SOURCE_SCHEMA_VERSION


# --- the export's values ------------------------------------------------------------------

def test_the_export_s_values_are_built_in_memory_formula_domains_included():
    here = project.current()          # read only: a copy carries no Formules/ folder
    calculations = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
    formulas = json.loads((here.data_dir / "formulas.json").read_text(encoding="utf-8"))
    # the loads handed over, not the ones on the disk
    changed = copy.deepcopy(calculations)
    changed["domains"]["snow-load"]["instances"]["SL"]["vars"]["L"]["value"] = 20.0
    values = variable_sources.export_values(here, changed, formulas=formulas)
    assert values["snow-load"]["SL"]["L"]["value"] == 20.0
    assert values[links.FORMULAS_KEY]["poutre-p1"]["M_d"]["value"] == 14.0625
    assert "connection" not in values      # nothing handed over, nothing listed
    known = variable_sources.known_values(here.data_dir)
    assert known["snow-load"]["SL"]["L"]["value"] == 17.5 and links.FORMULAS_KEY in known


# --- the window's side ------------------------------------------------------------------------

def test_refresh_writes_the_value_a_variable_gives_now_and_leaves_a_gone_one():
    entry = {"x": 4, "z": 1, "links": {"x": links.make("snow-load", "SL", "L"), "z": links.make("snow-load", "SL", "gone")}}
    links.refresh(entry, VALUES, {"x": "m", "z": "m"})
    assert entry["x"] == 17.5 and entry["z"] == 1
    block = {"N": {"value": 1, "unit": "kN"}, "links": {"N": links.make("snow-load", "SL", "F")}}
    links.refresh(block, VALUES, {"N": None})
    assert block["N"] == {"value": 12.5, "unit": "kN"}


def test_the_module_is_qt_free():
    source = conftest.module_source(conftest.CALC / "domains" / "links.py")
    assert "PySide" not in source and "QtWidgets" not in source


# --- the whole export --------------------------------------------------------------------------

def _without_fire(here):
    """The example's checks in the fire situation (issue #46) taken out of a copy: they make the export 1.2, the version above 1.1, and what these tests hold is the version a link alone gives."""
    for path in here.checks_dir.glob("FE-*.json"):
        path.unlink()


def _export_copy(name):
    """A copy of the example project with its «Formules» folder and its plans' documents, which project_copy leaves out, exported by export_all.run as the window's «Import données» runs it."""
    import shutil
    here = conftest.project_copy(name)
    real = project.current()
    shutil.copytree(real.typst_root / "Formules", here.typst_root / "Formules")
    # the plans' backgrounds, which the export reads and project_copy leaves out (a plan on a missing document stops the export)
    for folder in real.root.iterdir():
        if folder.is_dir() and folder.name.startswith("01_"):
            shutil.copytree(folder, here.root / folder.name)
    return here


def test_a_project_without_a_link_exports_its_checks_and_models_as_before():
    """ARCH-004: nothing follows a variable, and data/checks.json comes out byte for byte as the example project's export holds it, data/statics.json at 1.1 with no `links`. (The example's committed statics.json still carries a model «VU» whose source is gone, so its bytes are not the baseline.)"""
    import export_all
    here = _export_copy("links_export_same")
    before = (here.data_dir / "checks.json").read_bytes()
    with project.using(here):
        export_all.run()
    assert (here.data_dir / "checks.json").read_bytes() == before, "checks.json changed although nothing follows a variable"
    models = json.loads((here.data_dir / "statics.json").read_text(encoding="utf-8"))
    assert models["schema_version"] == statics.EXPORT_SCHEMA_VERSION
    assert not any("links" in record for record in models["models"].values())


def test_the_whole_export_resolves_a_check_from_a_script_and_a_model_from_a_formula_domain_and_a_connection():
    """ARCH-005, REQ-002, REQ-006, REQ-012 end to end: a member check's N follows a script's variable, another's a variable gone, a static model's point a «Formule» domain's and a connection's; export_all.run computes the scripts and the «Formule» domains before them, in memory, and the records carry each value with where it came from."""
    import export_all
    here = _export_copy("links_export_all")
    _without_fire(here)
    check_path = here.checks_dir / "ZT-01.json"
    check = json.loads(check_path.read_text(encoding="utf-8"))
    check["links"] = {"N": links.make("script", "dreigelenk", "V_d")}
    member_check.stamp_version(check)
    check_path.write_text(json.dumps(check, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    gone_path = here.checks_dir / "ZT-02.json"
    gone = json.loads(gone_path.read_text(encoding="utf-8"))
    gone["links"] = {"N": links.make("script", "dreigelenk", "gone")}
    member_check.stamp_version(gone)
    gone_path.write_text(json.dumps(gone, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    model_path = here.statics_dir / "Bankli-Fall1.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    for point in model["points"]:
        if point["id"] == "P3":
            point["links"] = {"x": links.make(links.FORMULAS, "poutre-p1", "l", origin=links.FORMULAS)}
        if point["id"] == "P1":
            point["links"] = {"z": links.make("connection", "VU-MP-1", "z_c")}
    statics.stamp_version(model)
    model_path.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with project.using(here):
        export_all.run()
    checks = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))
    assert checks["schema_version"] == member_check.LINKED_EXPORT_VERSION
    record = checks["checks"]["ZT-01"]
    assert abs(record["N"]["value"] - 19.2) < 1e-9 and record["N"]["unit"] == "kN", record["N"]
    assert record["links"]["N"]["variable"]["domain"] == "script" and not record["links"]["N"]["stale"]
    # a variable gone: the last value kept, the record stale and the warning in the report's list (REQ-006, D-06)
    kept = checks["checks"]["ZT-02"]
    assert kept["N"]["value"] == gone["N"]["value"] and kept["links"]["N"]["stale"]
    assert any("N keeps its last value" in w and "dreigelenk/gone" in w for w in kept["warnings"]), kept["warnings"]
    models = json.loads((here.data_dir / "statics.json").read_text(encoding="utf-8"))
    assert models["schema_version"] == statics.LINKED_EXPORT_VERSION
    found = {(p["entry"], p["field"]): p for p in models["models"]["Bankli-Fall1"]["links"]}
    assert found[("P3", "x")]["base_value"] == 5 and found[("P3", "x")]["base_unit"] == "m" and not found[("P3", "x")]["stale"]
    assert found[("P1", "z")]["base_unit"] == "mm" and not found[("P1", "z")]["stale"]
    # the source is not touched by the export (D-14): P3 holds the number it held
    assert json.loads(model_path.read_text(encoding="utf-8")) == model


# --- lot 2: the loads, the connectors, the polar moments -------------------------------------

def _write(folder, name, source):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_a_load_follows_another_load_and_a_formula_domain_in_the_order_its_links_ask():
    """ARCH-005, D-11, REQ-012: a snow load's h_0 follows a wind load's b, a wind load's b a «Formule» domain's length and another's q_p0 a dead load's; built after what they follow, whatever their file order, each instance carrying where its value came from, at calculations 1.6. A variable gone keeps the last value with a warning; a load naming a script is a defect of the file, refused (D-11)."""
    import registry
    from domains import snow_source, wind_source
    here = _export_copy("links_loads")
    wind_dir, snow_dir = here.sources_dir / wind_source.FOLDER, here.sources_dir / snow_source.FOLDER
    wi = wind_source.new_source("WI-01")
    wi["links"] = {"b": links.make(links.FORMULAS, "poutre-p1", "l", origin=links.FORMULAS)}
    _write(wind_dir, "WI-01.json", wind_source.stamp_version(wi))
    sn = snow_source.new_source("SN-01")
    sn["links"] = {"h_0": links.make("wind-load", "WI-01", "b", factor=100)}
    _write(snow_dir, "SN-01.json", snow_source.stamp_version(sn))
    # a wind load's q_p0 following a dead load built in Woodcore -- the «charge permanente» of ARCH-005
    from domains import dead_load_source
    au = dead_load_source.new_source("AU-01")
    _write(here.sources_dir / dead_load_source.FOLDER, "AU-01.json", au)
    wi2 = wind_source.new_source("WI-02")
    wi2["links"] = {"q_p0": links.make("dead-load", "AU-01", "gk_ak")}
    _write(wind_dir, "WI-02.json", wind_source.stamp_version(wi2))
    # a load naming a script, or the snow load SN-02 naming a variable since gone, written by hand
    bad = snow_source.new_source("SN-02")
    bad["links"] = {"h_0": links.make("script", "dreigelenk", "H_d")}
    _refused(lambda: snow_source.check_source(snow_source.stamp_version(bad)), "dreigelenk", "may not follow")
    bad["links"] = {"h_0": links.make("wind-load", "WI-01", "gone")}
    _write(snow_dir, "SN-02.json", snow_source.stamp_version(bad))
    notes = []
    with project.using(here):
        data = registry.build_calculations([], here, {}, notes)
        graph = registry.load_graph(here)
    assert data["schema_version"] == registry.LINKED_SCHEMA_VERSION
    validation.validate_structure(data, "calculations")
    wind = data["domains"]["wind-load"]["instances"]["WI-01"]
    snow = data["domains"]["snow-load"]["instances"]["SN-01"]
    assert wind["vars"]["b"]["value"] == 5 and wind["links"][0]["variable"]["origin"] == links.FORMULAS
    assert snow["vars"]["h_0"]["value"] == 500 and snow["links"][0]["field"] == "h_0"
    kept = data["domains"]["snow-load"]["instances"]["SN-02"]
    assert kept["vars"]["h_0"]["value"] == bad["h_0"] and kept["links"][0]["stale"]
    assert any("SN-02" in str(n) and "h_0" in str(n) for n in notes), notes
    gk = data["domains"]["dead-load"]["instances"]["AU-01"]["vars"]["gk_ak"]["value"]
    assert data["domains"]["wind-load"]["instances"]["WI-02"]["vars"]["qp0"]["value"] == gk
    assert list(data["domains"]["snow-load"]["instances"]) == ["SN-01", "SN-02"], "file-name order kept"
    assert graph[("snow-load", "SN-01")] == {("wind-load", "WI-01")} and graph[("wind-load", "WI-01")] == set()


def test_loads_that_follow_each_other_in_a_circle_stop_the_export_naming_the_chain():
    """REQ-007: two loads following each other, directly or through a third, stop the export naming the chain -- a defect of files Woodcore wrote -- and `links.find_cycle` finds what the window refuses."""
    import registry
    from domains import snow_source, wind_source
    here = _export_copy("links_loads_circle")
    wi = wind_source.new_source("WI-09")
    wi["links"] = {"b": links.make("snow-load", "SN-09", "h_0")}
    _write(here.sources_dir / wind_source.FOLDER, "WI-09.json", wind_source.stamp_version(wi))
    sn = snow_source.new_source("SN-09")
    sn["links"] = {"h_0": links.make("wind-load", "WI-09", "b")}
    _write(here.sources_dir / snow_source.FOLDER, "SN-09.json", snow_source.stamp_version(sn))
    with project.using(here):
        message = _refused(lambda: registry.build_calculations([], here, {}, []), "SN-09", "WI-09", "circle")
        graph = registry.load_graph(here)
    assert "→" in message
    # and through a third: a dead load following the wind load, the snow load following the dead load
    from domains import dead_load_source
    au = dead_load_source.new_source("AU-09")
    au["chosen"] = 1.0
    au["links"] = {"chosen": links.make("wind-load", "WI-08", "qp0")}
    _write(here.sources_dir / dead_load_source.FOLDER, "AU-09.json", dead_load_source.stamp_version(au))
    wi8 = wind_source.new_source("WI-08")
    wi8["links"] = {"q_p0": links.make("snow-load", "SN-08", "s_k")}
    _write(here.sources_dir / wind_source.FOLDER, "WI-08.json", wind_source.stamp_version(wi8))
    sn8 = snow_source.new_source("SN-08")
    sn8["links"] = {"h_0": links.make("dead-load", "AU-09", "gk")}
    _write(here.sources_dir / snow_source.FOLDER, "SN-08.json", snow_source.stamp_version(sn8))
    (here.sources_dir / wind_source.FOLDER / "WI-09.json").unlink()
    (here.sources_dir / snow_source.FOLDER / "SN-09.json").unlink()
    with project.using(here):
        message = _refused(lambda: registry.build_calculations([], here, {}, []), "SN-08", "WI-08", "AU-09", "circle")
        chain = links.find_cycle(registry.load_graph(here), ("snow-load", "SN-08"))
    assert len(chain) == 4 and chain[0] == chain[-1], chain
    assert links.find_cycle(graph, ("snow-load", "SN-09")) in ([("snow-load", "SN-09"), ("wind-load", "WI-09"), ("snow-load", "SN-09")],)
    assert links.find_cycle({"a": ["b"], "b": ["c"]}, "a") is None and links.find_cycle({"a": ["a"]}, "a") == ["a", "a"]
    assert links.find_cycle({"a": ["b"], "b": ["c"], "c": ["a"]}, "a") == ["a", "b", "c", "a"]


def test_a_connector_and_a_polar_moment_follow_a_formula_domain_and_a_script_but_no_joint():
    """REQ-009 (lot 2), D-12, ARCH-005: a connector's diameter follows a «Formule» domain's length, converted and scaled; a polar moment's trial force a script's variable, `trial` being data of the source; a joint naming a joint is a defect of its file, refused. The exports carry `links` at connectors 3.1 and connections 4.2."""
    import export_all
    from domains import connection, connector
    here = _export_copy("links_joints")
    path = next(here.connectors_dir.glob("*.json"))
    source = json.loads(path.read_text(encoding="utf-8"))
    source["links"] = {"diameter": links.make(links.FORMULAS, "poutre-p1", "l", factor=0.002, origin=links.FORMULAS)}
    source["members"][0]["links"] = {"alpha": links.make("connection", "VU-MP-1", "alpha_N")}
    connector.stamp_version(source)
    _refused(lambda: connector.check_source(source, path.name), "VU-MP-1", "may not follow")   # a connector names no polar moment (D-18): a defect of the file
    del source["members"][0]["links"]
    connector.stamp_version(source)
    connector.check_source(source, path.name)
    path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    cpath = here.connections_dir / "VU-MP-1.json"
    calc = json.loads(cpath.read_text(encoding="utf-8"))
    calc["trial"] = {"N": 5, "V": 3, "M": 1}
    calc["links"] = {"trial.N": links.make("script", "dreigelenk", "V_d")}
    connection.stamp_version(calc)
    connection.check_source(calc, cpath.name)
    cpath.write_text(json.dumps(calc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with project.using(here):
        export_all.run()
    data = json.loads((here.data_dir / "connectors.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == connector.LINKED_EXPORT_VERSION
    record = data["connectors"][source["id"]]
    found = {(p["entry"], p["field"]): p for p in record["links"]}
    assert found[("self", "diameter")]["base_value"] == 5 and not found[("self", "diameter")]["stale"]
    assert record["diameter"]["value"] == 10, record["diameter"]
    joints = json.loads((here.data_dir / "connections.json").read_text(encoding="utf-8"))
    assert joints["schema_version"] == connection.LINKED_EXPORT_VERSION
    assert abs(joints["connections"]["VU-MP-1"]["links"][0]["base_value"] - 19.2) < 1e-9
    # a trial that is no {N, V, M} is refused, naming it
    calc["trial"] = {"N": 5, "T": 1}
    _refused(lambda: connection.check_source(calc, cpath.name), "trial")
