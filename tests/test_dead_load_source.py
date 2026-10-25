"""Permanent loads entered in Woodcore (issue #35, spec docs/requirements/completed/2026-10-10-issues-github-35-a-39.md): a build-up of layers, weighed with the three libraries of `domains/materials.py`, summed by the dead load's own arithmetic, drawn, and exported under its domain (D-04; no load workbook read since issue #109).

What is held:

* **REQ-001** -- a build-up gives the sum the workbook's column K gives for the same layers, (1/H)·I·F·G/100, and a chosen value below it is refused naming the file and the field;
* **REQ-002** -- a layer moved from g_k to a_k moves its load from one sum to the other;
* **D-07** -- the three libraries: SIA 261 Anhang A in kN, Woodcore's materials library keyed by (Ebene, material), the project's own; a material none carries is refused by name;
* **UI-002, UI-003** -- the drawing: one band per layer, beside layers sharing one, the heights in the chain, the width and the spacing of battens above their band;
* **ARCH-003, ARCH-004** -- calculations 1.5, 1.9 since issue #109: an instance computed from a source names it and no workbook; a load workbook beside the sources is never read; the export writes the drawing in its Exports/Figures/.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import project
import engine
import registry
import validation
from domains import dead_load, dead_load_layers, dead_load_source, dead_load_svg, materials


def _layer(**change):
    layer = dead_load_source.new_layer()
    layer.update(change)
    return layer


def _old_layer(**change):
    """A layer as dead-load-source 1.x wrote it, read since issue #111 through dead_load_migrate."""
    layer = {"kind": "gk", "library": "sia261", "material": "holz_nadelhoelzer_allgemein", "ebene": "", "thickness": 27,
             "width": None, "spacing": None, "beside": False, "load": None}
    layer.update(change)
    return layer


def _old_roof(cid="DA-01", chosen=None):
    """The flat roof of `_roof` as a 1.0 source wrote it."""
    return {"schema_version": "1.0", "id": cid, "name": "Flachdach", "label": "", "group": "", "chosen": chosen, "layers": [
        _old_layer(kind="ak", library="belastungsannahmen", ebene="Abdichtung", material="Dachpappe", thickness=10),
        _old_layer(kind="gk", library="sia261", material="holz_nadelhoelzer_allgemein", thickness=27),
        _old_layer(kind="gk", library="sia261", material="holz_nadelhoelzer_allgemein", thickness=200, width=60, spacing=625),
        _old_layer(kind="ak", library="belastungsannahmen", ebene="Dämmung", material="Flumroc Typ 1", thickness=200, beside=True),
        _old_layer(kind="ak", library="direct", material="Installationen", load=0.5, thickness=None),
    ]}


def _roof(cid="DA-01", chosen=None):
    """A flat roof at 2.0: a membrane per surface, a board, rafters at a spacing linked with the insulation between them (full width, as 1.0 summed it), a load typed -- the shapes the workbook's layer table takes."""
    return {"schema_version": "2.0", "id": cid, "name": "Flachdach", "label": "", "group": "", "chosen": chosen, "layers": [
        _layer(kind="ak", pose="surface", material="ext:163", thickness=10),
        _layer(kind="gk", thickness=27),
        _layer(kind="gk", pose="spaced", thickness=200, width=60, spacing=625, link=True),
        _layer(kind="ak", material="ext:46", thickness=200, fill=False, width=1000, role="insulation"),
        _layer(kind="ak", pose="typed", material=None, label="Installationen", load=0.5, thickness=None),
    ]}


def _entry(ebene, material):
    for e in materials.workbook_library()["materials"]:
        if e["ebene"] == ebene and e["material"] == material:
            return e
    return None


def test_the_libraries_are_read_and_a_material_none_carries_is_refused():
    """D-07: SIA 261 Anhang A from calc/norms, the workbook's library from calc/libraries with its sources, the project's own -- and a name nobody lists refused."""
    lib = materials.workbook_library()["materials"]
    assert len(lib) == 236 and all(e["unit"] in materials.UNITS for e in lib)
    value, unit, label, source = materials.weight({"library": "sia261", "material": "holz_nadelhoelzer_allgemein"})
    assert unit == "kN/m³" and value > 0 and "Tabelle 28" in source
    assert materials.weight({"library": "belastungsannahmen", "ebene": "Fussboden", "material": "Parkett Hartholz"})[:2] == (800, "kg/m³")
    projects = {"schema_version": "1.0", "materials": [{"id": "OSB-X", "name": "OSB Hersteller X", "value": 6.2, "unit": "kN/m³", "source": "Datenblatt"}]}
    materials.check_project(projects)
    assert materials.weight({"library": "project", "material": "OSB-X"}, projects)[0] == 6.2
    for layer, words in (({"library": "sia261", "material": "nothing"}, "Tabelle 28 or 29"),
                         ({"library": "belastungsannahmen", "ebene": "", "material": "nothing"}, "not in Woodcore's materials library"),
                         ({"library": "belastungsannahmen", "ebene": "x", "material": "Gartenplatten"}, "name its Ebene")):
        try:
            materials.weight(layer)
        except validation.ValidationError as exc:
            assert words in str(exc), (layer, str(exc))
        else:
            raise AssertionError(layer)


def test_the_aluminium_entries_the_norm_contradicts_carry_the_norms_value():
    """Spec 2026-10-12-audit-issues-47-48-49, REQ-006 (D-05): four aluminium entries of the Belastungsannahmen library contradicted SIA 261 -- Aluwellblech 40 kg/m² against Tabelle 29's 0.04 kN/m², Blech Aluminium 3500 kg/m³ against Tabelle 28's 27 kN/m³, Blech Aluminium 2mm 8 kg/m² against 27 kN/m³ × 2 mm. Each now carries the norm's value (kg at g = 10 m/s², the library's own conversion), names the table as its source and keeps the workbook's value in its note -- held here against the norm files, so the copy cannot age without saying so."""
    norms = Path(__file__).resolve().parents[1] / "calc" / "norms"
    tab28 = {r["id"]: r for r in json.loads((norms / "sia261-2020-tab28-raumlasten-baustoffe.json").read_text(encoding="utf-8"))["table_28"]["rows"]}
    tab29 = {r["id"]: r for r in json.loads((norms / "sia261-2020-tab29-flaechenlasten-bedachungen.json").read_text(encoding="utf-8"))["table_29"]["rows"]}
    alu = tab28["aluminium"]["raumlast"]
    expected = {("Dachhaut", "Aluwellblech"): (tab29["profilbleche_hoehe_80_mm_dicke_0_8_mm_aluminiumblech"]["flaechenlast"] * 100, "kg/m²", "Tab 29"),
                ("Fassade", "Blech Aluminium"): (alu * 100, "kg/m³", "Tab 28"),
                ("Beschichtung", "Blech Aluminium 2mm"): (alu * 0.002 * 100, "kg/m²", "Tab 28"),
                ("Schutzbahn/Dachhaut", "Blech Aluminium 2mm"): (alu * 0.002 * 100, "kg/m²", "Tab 28")}
    library = {(e["ebene"], e["material"]): e for e in materials.workbook_library()["materials"]}
    for key, (mass, unit, table) in expected.items():
        entry = library[key]
        assert abs(entry["mass"] - mass) < 1e-9 and entry["unit"] == unit, (key, entry)
        assert entry["quelle"] == "SIA 261 " + table and "Arbeitsblatt gibt" in entry["info"], (key, entry)


def test_the_glass_and_the_scobalit_the_workbook_got_wrong_carry_their_value():
    """Spec 2026-10-24-poids-propre-repense, REQ-012 (D-06, D-09, Q-004): the workbook's «Glas» (rows 150, 234: 5000 kg/m³, twice the density of glass) carries SIA 261 Tabelle 28's «Glasbausteine, voll», held here to the norm file; its «Scobalit» of the façade (row 235: 0, refused before) carries row 151's 500 kg/m³; each keeps the workbook's value in its note, and the two Scobalit rows are now one material."""
    norms = Path(__file__).resolve().parents[1] / "calc" / "norms"
    tab28 = {r["id"]: r for r in json.loads((norms / "sia261-2020-tab28-raumlasten-baustoffe.json").read_text(encoding="utf-8"))["table_28"]["rows"]}
    library = {(e["ebene"], e["material"]): e for e in materials.workbook_library()["materials"]}
    for key in (("Dachhaut", "Glas"), ("Fassade", "Glas")):
        entry = library[key]
        assert (entry["mass"], entry["unit"]) == (tab28["mauerwerk_unverputzt_glasbausteine_voll"]["raumlast"] * 100, "kg/m³") and entry["quelle"] == "SIA 261 Tab 28", entry
        assert "5000 kg/m³" in entry["info"], entry
    assert (library[("Fassade", "Scobalit")]["mass"], library[("Fassade", "Scobalit")]["unit"]) == (library[("Dachhaut", "Scobalit")]["mass"], "kg/m³") == (500, "kg/m³")
    assert "0 kg/m³" in library[("Fassade", "Scobalit")]["info"]
    assert materials.weight({"library": "belastungsannahmen", "ebene": "Fassade", "material": "Scobalit"})[:2] == (500, "kg/m³")
    from domains import materials_catalogue
    assert materials_catalogue.find("ext:151")["rows"] == [151, 235] and materials_catalogue.find("ext:150")["weight"]["value"] == 25


def test_a_build_up_sums_as_the_workbooks_column_k_does():
    """REQ-001: each layer's load is the workbook's own K, (1/H)·I·F·G/100 for a weight in kg, γ·F·G/H for one in kN; the sums, the chosen value and the table follow."""
    src = _roof(chosen=2.0)
    dead_load_source.check_source(src)
    instance = dead_load_source.build_instance(src, conftest.PROJECT)
    bitumen, mineral = _entry("Abdichtung", "Dachpappe"), _entry("Dämmung", "Flumroc Typ 1")
    assert bitumen and mineral, "the library carries the two materials the test names"
    gamma = materials.weight({"library": "sia261", "material": "holz_nadelhoelzer_allgemein"})[0]

    def k(mass, unit, f, g=1, h=1):
        per = f if unit.endswith("³") else 1
        return (mass / 100 if unit.startswith("kg") else mass) * per * g / h

    gk = k(gamma, "kN/m³", 0.027) + k(gamma, "kN/m³", 0.2, 0.06, 0.625)
    ak = k(bitumen["mass"], bitumen["unit"], 0.01) + k(mineral["mass"], mineral["unit"], 0.2) + 0.5
    v = instance["vars"]
    assert abs(v["gk"]["value"] - gk) < 1e-9 and abs(v["ak"]["value"] - ak) < 1e-9, (v["gk"]["value"], gk, v["ak"]["value"], ak)
    assert instance["results"] == ["gk_ak_gew"] and v["gk_ak_gew"]["value"] == 2.0
    table = instance["tables"][0]
    assert table["title"] == "Schichtaufbau" and len(table["rows"]) == 5 and table["note"] == dead_load_source.NOTE
    # chosen null: the tenth above the sum is the result (issue #111, REQ-005)
    open_one = dead_load_source.build_instance(_roof(chosen=None), conftest.PROJECT)
    assert open_one["results"] == ["gk_ak_gew"] and open_one["vars"]["gk_ak_gew"]["value"] == dead_load_layers.retained(v["gk_ak"]["value"])
    # the same roof as 1.0 wrote it: the same sums (CON-001)
    old = dead_load_source.build_instance(_old_roof(chosen=2.0), conftest.PROJECT)["vars"]
    assert all(abs(old[k]["value"] - v[k]["value"]) < 1e-12 for k in ("gk", "ak", "gk_ak", "gk_ak_gew"))


def test_a_flat_roof_gives_what_the_workbooks_flachdach_sheet_gives():
    """REQ-001: the sheet «Flachdach» of «load workbook» template filled with these nine layers and recalculated by Excel (11.10.2026, a copy of the template) gives K25 = 0.804, gk (J27) = 0.397 and ak (J28) = 0.407 kN/m² -- the ebene, the material, F, G and H of each row below as typed into rows 11 to 21; a weight per m² entered there with F = 1."""
    rows = (("ak", "Abdichtung", "Dachpappe", 10, None, None), ("ak", "Dämmung", "Flumroc Typ 1", 200, None, None),
            ("ak", "Gefällslattung", "C24", 60, 80, 600), ("gk", "Beplankung", "3-Schichtplatte", 27, None, None),
            ("gk", "Konstruktion", "C24", 200, 100, 625), ("ak", "Dämmung", "Flumroc Typ 1", 200, None, None),
            ("gk", "Beplankung", "OSB3", 15, None, None), ("ak", "Rostung", "C24", 30, 50, 500), ("ak", "Bekleidung", "Rigips", 12.5, None, None))
    layers = [_old_layer(kind=kind, library="belastungsannahmen", ebene=ebene, material=material, thickness=t, width=w, spacing=s) for kind, ebene, material, t, w, s in rows]
    src = {"schema_version": "1.0", "id": "DA-09", "name": "Flachdach", "label": "", "group": "", "chosen": None, "layers": layers}
    dead_load_source.check_source(src)
    v = dead_load_source.build_instance(src, conftest.PROJECT)["vars"]
    assert abs(v["gk"]["value"] - 0.397) < 1e-9 and abs(v["ak"]["value"] - 0.407) < 1e-9 and abs(v["gk_ak"]["value"] - 0.804) < 1e-9, (v["gk"], v["ak"], v["gk_ak"])
    assert v["gk_ak_gew"]["value"] == 0.9, "read through dead_load_migrate (issue #111, REQ-002): the same sum, retained at the tenth above it"


def test_the_load_modules_import_without_qt():
    """ARCH-001 (issues #35-#37): the three loads, their drawings and the libraries are Qt-free -- what the export and woodcore-cli import."""
    import subprocess
    code = ("import sys; sys.modules['PySide6'] = None; sys.path[:0] = [r'%s']\n"
            "from domains import materials, dead_load_source, dead_load_svg, snow_source, snow_svg, wind_source\n"
            "from norms import sia261_snow, sia261_wind; print('ok')") % (conftest.ROOT / "calc")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr


def test_each_load_source_is_its_schemas_and_versioned():
    """ARCH-003: a new source of each load, and the project's materials, pass their own schemas/*.schema.json, which pin schema_version; a field of the wrong type is refused by the schema, naming it."""
    from domains import snow_source, wind_source
    for module, name in ((dead_load_source, "dead-load-source"), (snow_source, "snow-source"), (wind_source, "wind-source")):
        assert module.SOURCE_SCHEMA == name
        schema = json.loads((conftest.ROOT / "schemas" / (name + ".schema.json")).read_text(encoding="utf-8"))
        assert "schema_version" in schema["required"] and "schema_version" in schema["properties"], name
        src = module.new_source("XX-01")
        validation.validate_structure(src, name)
        bad = dict(src, name=12)
        try:
            validation.validate_structure(bad, name)
        except validation.ValidationError as exc:
            assert "name" in str(exc), (name, str(exc))
        else:
            raise AssertionError(name + ": a name of the wrong type passed")
    validation.validate_structure({"schema_version": "1.0", "materials": [{"id": "M1", "name": "OSB", "value": 6.2, "unit": "kN/m³", "source": "Datenblatt"}]}, materials.PROJECT_SCHEMA)


def test_a_chosen_value_below_the_sum_is_refused_naming_the_file_and_the_field():
    try:
        dead_load_source.build_instance(_roof(chosen=0.5), conftest.PROJECT)
    except validation.ValidationError as exc:
        assert "loads/dead/DA-01.json" in str(exc) and "chosen" in str(exc), str(exc)
    else:
        raise AssertionError("a chosen value below the sum passed")


def test_a_layer_moved_from_gk_to_ak_moves_its_load():
    """REQ-002 (T4): each layer is the engineer's to class, poids propre or surcharge."""
    first = dead_load_source.build_instance(_roof(), conftest.PROJECT)["vars"]
    src = _roof()
    src["layers"][1]["kind"] = "ak"
    second = dead_load_source.build_instance(src, conftest.PROJECT)["vars"]
    moved = first["gk"]["value"] - second["gk"]["value"]
    assert moved > 0 and abs((second["ak"]["value"] - first["ak"]["value"]) - moved) < 1e-12
    assert abs(first["gk_ak"]["value"] - second["gk_ak"]["value"]) < 1e-12


def test_each_defect_of_a_source_of_before_is_still_refused_naming_the_field():
    """A 1.x source is checked as it was written (the 2.0 defects: test_dead_load_layers)."""
    for change, word in ((lambda s: s.update(id="-x"), "id"), (lambda s: s.update(layers=[]), "layers is empty"),
                         (lambda s: s["layers"][0].update(kind="qk"), "kind"), (lambda s: s["layers"][0].update(library="x"), "library"),
                         (lambda s: s["layers"][2].update(spacing=None), "width and spacing go together"),
                         (lambda s: s["layers"][2].update(width=700), "above the spacing"),
                         (lambda s: s["layers"][0].update(beside=True), "first layer"),
                         (lambda s: s["layers"][4].update(load=0), "load"), (lambda s: s.update(chosen=-1), "chosen"),
                         (lambda s: s["layers"][1].update(thickness=0), "thickness")):
        src = _old_roof()
        change(src)
        try:
            dead_load_source.check_source(src, "loads/dead/probe.json")
        except validation.ValidationError as exc:
            assert word in str(exc) and "probe.json" in str(exc), (word, str(exc))
        else:
            raise AssertionError(word)
    src = _roof()
    src["layers"][1]["thickness"] = None
    try:
        dead_load_source.build_instance(src, conftest.PROJECT)
    except validation.ValidationError as exc:
        assert "layers[1]" in str(exc) and "thickness" in str(exc), str(exc)
    else:
        raise AssertionError("a weight per volume with no thickness passed")


def test_the_section_is_drawn_at_its_true_proportion():
    """UI-002, UI-003; REQ-009 of issue #111: one metre at the scale of the heights -- the strip as wide to its height as 1000 to the build-up's millimetres --, the rafters at their spacing with the insulation linked to them filling the gaps from the bottom, each band's height, the whole height, «1000», the width of one rafter and the spacing; a load typed drawn nowhere; no band held at a minimum height."""
    model = dead_load_source.layers_of(dead_load_source.layer_rows(_roof(), None))   # the model of layers the drawing reads (spec 2026-10-23-onglets-types-et-services, ARCH-007)
    assert [(kind, [l.number for l in group]) for kind, group in dead_load_svg.bands(model)] == [("level", [1]), ("level", [2]), ("level", [3, 4])]
    svg = dead_load_svg.render(model)
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>") and svg == dead_load_svg.render(model, dead_load_svg.EXPORT_WIDTH)
    texts = [t.split(">", 1)[1].split("<", 1)[0] for t in svg.split("<text")[1:]]
    for value in ("200", "237", "1000", "60", "e = 625"):
        assert value in texts, (value, texts)
    assert "10" not in texts and "27" not in texts, "a height written only where it fits: 10 and 27 mm are too thin at this scale"
    assert "Installationen" not in svg, "a load typed has no thickness to draw"
    g = dead_load_svg._layout(model)
    assert abs(g["strip"] / (g["bottom"] - g["top"]) - 1000 / 237) < 1e-9, "1 m at the scale of the heights"
    boxes = dead_load_svg.hit_boxes(model)
    rafters = [b for b in boxes if b[0] == 3]
    wool = [b for b in boxes if b[0] == 4]
    k = g["k"]
    assert all(abs(b[3] - 60 * k) < 1e-9 for b in rafters) and len(rafters) == 2 and abs(rafters[1][1] - rafters[0][1] - 625 * k) < 1e-9
    assert abs(sum(b[3] for b in wool) - (1000 - 2 * 60) * k) < 1e-9, "the wool between the two rafters of the metre, from edge to edge"
    thin = [b for b in boxes if b[0] == 1][0]
    assert abs(thin[4] - 10 * k) < 1e-9, "the membrane at its 10 mm, no minimum"
    # AU-01's 311.5 mm: three times as wide as it is high, 1000/311.5 to the pixel (REQ-009)
    au01 = dead_load_source.layers_of(dead_load_source.layer_rows({**_roof(), "layers": [_layer(thickness=11.5), _layer(thickness=100), _layer(thickness=200)]}, None))
    g = dead_load_svg._layout(au01)
    assert abs(g["strip"] / (g["bottom"] - g["top"]) - 1000 / 311.5) < 1e-9
    # the legend mode under 560 units: the names listed under the drawing, a number beside each layer
    narrow = dead_load_svg.render(model, 500)
    narrow_texts = [t.split(">", 1)[1].split("<", 1)[0] for t in narrow.split("<text")[1:]]
    assert dead_load_svg._layout(model, 500)["legend"] and "4  Flumroc Typ 1" in narrow_texts and "4" in narrow_texts
    # a name too long for the column is cut, the whole name its title
    import dataclasses
    long = [dataclasses.replace(model[0], label="Dachpappe " * 8)] + model[1:]
    cut = dead_load_svg.render(long)
    assert "…" in cut and "<title>%s</title>" % ("Dachpappe " * 8) in cut


def test_the_export_carries_the_sources_and_reads_no_workbook():
    """ARCH-003, ARCH-004 (D-04), issue #109: a source's instance names its file and no workbook, its drawing is written in its Exports/Figures/; a load workbook beside it is never opened (bytes no workbook reader takes) and adds no case; an export of before 1.9 is refused by the schema."""
    here = conftest.project_copy("dead_load_source_export")
    folder = here.sources_dir / dead_load_source.FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "DA-01.json").write_text(json.dumps(_roof(chosen=2.0), ensure_ascii=False, indent=2), encoding="utf-8")
    (here.root / "Belastungsannahmen.xlsx").write_bytes(b"not a workbook: never opened")
    files = {}
    data = registry.build_calculations(here, files)
    place = engine.Figures(here.data_dir, "dead-load", here)   # Permanent-loads/Exports/Figures/ laid out by folders, data/calculations/ before (issue #64)
    assert data["schema_version"] == registry.SCHEMA_VERSION == "1.9"
    instances = data["domains"]["dead-load"]["instances"]
    assert "DA-01" in instances and all(i.get("source_file") for i in instances.values()), "every case is a source's"
    assert "sheet_prefix" not in data["domains"]["dead-load"]
    source = instances["DA-01"]
    assert source["engine"] == "python" and source["source_file"] == "loads/dead/DA-01.json" and "workbook" not in source and "sheet" not in source
    name = place.name("dead-load-DA-01.svg")
    assert source["figures"][0]["file"] == name and name in files
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)
    registry.write_files(files, here.data_dir)
    assert place.path(name).read_bytes().count(b"\r\n") == 0
    # an export of before, 1.8 and its sheets, is refused where it is read, saying what to do
    old = {"schema_version": "1.8", "domains": {}}
    try:
        validation.validate_structure(old, "calculations")
    except validation.ValidationError as exc:
        assert "schema_version" in str(exc) and "Import données" in str(exc), str(exc)
    else:
        raise AssertionError("an export at 1.8 passed")


def test_the_written_out_load_prints_the_drawing_of_the_case_entered_in_woodcore():
    """UI-002 in the report: the domain Woodcore writes out for a dead load entered in Woodcore (spec 2026-10-21-commandes-typst-refonte, REQ-017; `#show-calc("dead-load", id)` until then) carries its drawing, a figure with its caption, and prints it."""
    import subprocess
    from domains import unfold
    if not conftest.have_typst():
        raise conftest.Skip("typst is not on the path")
    here = conftest.PROJECT
    folder = here.sources_dir / dead_load_source.FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "DA-77.json"
    kept = (here.data_dir / "calculations.json").read_bytes()
    try:
        path.write_text(json.dumps(_roof("DA-77", chosen=2.0), ensure_ascii=False), encoding="utf-8")
        registry.export(here)
        data = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        with project.using(here):
            text = unfold.generate(unfold._module("dead-load").records(data)["DA-77"], "de", "dead-load")
        assert "#figure(image(" in text and "caption: [Schichtaufbau]" in text, text[:600]
        # issue #111, REQ-013: the section printed from level 2, the table of the layers from level 3
        assert "#from-level(2)[#figure(image(" in text, text[:800]
        table = [l for l in text.splitlines() if "#table(" in l]
        assert table and all(l.lstrip().startswith("#from-level(3)[") for l in table), table
        d = conftest.probe_dir("dl_written_out")
        (d / "domain.typ").write_text(text, encoding="utf-8")
        (d / "probe.typ").write_text('#import "/000-Typst-Config/commands.typ": *\n#report-level.update(3)\n#include "domain.typ"\n', encoding="utf-8")   # level 3: the section and the table (issue #111, REQ-013)
        out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(d / "probe.typ"), str(d / "probe.svg")],
                             capture_output=True, text=True, encoding="utf-8")
        assert out.returncode == 0, out.stderr
        assert "<image" in (d / "probe.svg").read_text(encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)
        (here.data_dir / "calculations.json").write_bytes(kept)
