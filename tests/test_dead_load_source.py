"""Permanent loads entered in Woodcore (issue #35, spec docs/requirements/completed/2026-10-10-issues-github-35-a-39.md): a build-up of layers, weighed with the three libraries of `domains/materials.py`, summed by the dead load's own arithmetic, drawn, and exported beside the sheets of a load workbook under the same domain (D-04).

What is held:

* **REQ-001** -- a build-up gives the sum the workbook's column K gives for the same layers, (1/H)·I·F·G/100, and a chosen value below it is refused naming the file and the field;
* **REQ-002** -- a layer moved from g_k to a_k moves its load from one sum to the other;
* **D-07** -- the three libraries: SIA 261 Anhang A in kN, Woodcore's materials library keyed by (Ebene, material), the project's own; a material none carries is refused by name;
* **UI-002, UI-003** -- the drawing: one band per layer, beside layers sharing one, the heights in the chain, the width and the spacing of battens above their band;
* **ARCH-003, ARCH-004** -- calculations 1.5: an instance computed from a source names it and no workbook; an id a sheet and a source both carry is refused; a domain with only sources is not warned about; the export writes the drawing under data/calculations/.
"""

TIER = "fast"  # tests/run_tests.py --fast

import io
import json
import sys
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import project
import engine
import io_excel
import registry
import validation
from domains import dead_load, dead_load_source, dead_load_svg, materials
from fixtures import workbook as fx


def _layer(**change):
    layer = dead_load_source.new_layer()
    layer.update(change)
    return layer


def _roof(cid="DA-01", chosen=None):
    """A flat roof: a membrane per surface, a board, rafters at a spacing with the insulation between them, a ceiling -- the shapes the workbook's layer table takes."""
    return {"schema_version": "1.0", "id": cid, "name": "Flachdach", "label": "", "group": "", "chosen": chosen, "layers": [
        _layer(kind="ak", library="belastungsannahmen", ebene="Abdichtung", material="Dachpappe", thickness=10),
        _layer(kind="gk", library="sia261", material="holz_nadelhoelzer_allgemein", thickness=27),
        _layer(kind="gk", library="sia261", material="holz_nadelhoelzer_allgemein", thickness=200, width=60, spacing=625),
        _layer(kind="ak", library="belastungsannahmen", ebene="Dämmung", material="Flumroc Typ 1", thickness=200, beside=True),
        _layer(kind="ak", library="direct", material="Installationen", load=0.5, thickness=None),
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
                         ({"library": "belastungsannahmen", "ebene": "x", "material": "Gartenplatten"}, "name its Ebene"),
                         ({"library": "belastungsannahmen", "ebene": "Fassade", "material": "Scobalit"}, "project's library")):
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
    # chosen null: the sum is the result
    open_one = dead_load_source.build_instance(_roof(chosen=None), conftest.PROJECT)
    assert open_one["results"] == ["gk_ak"] and "gk_ak_gew" not in open_one["vars"]


def test_a_flat_roof_gives_what_the_workbooks_flachdach_sheet_gives():
    """REQ-001: the sheet «Flachdach» of «load workbook» template filled with these nine layers and recalculated by Excel (11.10.2026, a copy of the template) gives K25 = 0.804, gk (J27) = 0.397 and ak (J28) = 0.407 kN/m² -- the ebene, the material, F, G and H of each row below as typed into rows 11 to 21; a weight per m² entered there with F = 1."""
    rows = (("ak", "Abdichtung", "Dachpappe", 10, None, None), ("ak", "Dämmung", "Flumroc Typ 1", 200, None, None),
            ("ak", "Gefällslattung", "C24", 60, 80, 600), ("gk", "Beplankung", "3-Schichtplatte", 27, None, None),
            ("gk", "Konstruktion", "C24", 200, 100, 625), ("ak", "Dämmung", "Flumroc Typ 1", 200, None, None),
            ("gk", "Beplankung", "OSB3", 15, None, None), ("ak", "Rostung", "C24", 30, 50, 500), ("ak", "Bekleidung", "Rigips", 12.5, None, None))
    layers = [_layer(kind=kind, library="belastungsannahmen", ebene=ebene, material=material, thickness=t, width=w, spacing=s) for kind, ebene, material, t, w, s in rows]
    src = {"schema_version": "1.0", "id": "DA-09", "name": "Flachdach", "label": "", "group": "", "chosen": None, "layers": layers}
    dead_load_source.check_source(src)
    v = dead_load_source.build_instance(src, conftest.PROJECT)["vars"]
    assert abs(v["gk"]["value"] - 0.397) < 1e-9 and abs(v["ak"]["value"] - 0.407) < 1e-9 and abs(v["gk_ak"]["value"] - 0.804) < 1e-9, (v["gk"], v["ak"], v["gk_ak"])


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


def test_each_defect_of_a_source_is_refused_naming_the_field():
    for change, word in ((lambda s: s.update(id="-x"), "id"), (lambda s: s.update(layers=[]), "layers is empty"),
                         (lambda s: s["layers"][0].update(kind="qk"), "kind"), (lambda s: s["layers"][0].update(library="x"), "library"),
                         (lambda s: s["layers"][2].update(spacing=None), "width and spacing go together"),
                         (lambda s: s["layers"][2].update(width=700), "above the spacing"),
                         (lambda s: s["layers"][0].update(beside=True), "first layer"),
                         (lambda s: s["layers"][4].update(load=0), "load"), (lambda s: s.update(chosen=-1), "chosen"),
                         (lambda s: s["layers"][1].update(thickness=0), "thickness")):
        src = _roof()
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


def test_the_drawing_stacks_the_bands_and_dimensions_heights_widths_and_spacings():
    """UI-002, UI-003: one band per layer, the insulation beside the rafters sharing theirs; each band's height in the chain, the whole height, and the width of one rafter and their spacing; a typed load drawn nowhere."""
    rows = dead_load_source.layer_rows(_roof(), None)
    groups = dead_load_svg.bands(rows)
    assert [len(g) for g in groups] == [1, 1, 2], "membrane, board, rafters with the insulation beside them"
    svg = dead_load_svg.render(rows)
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    texts = [t.split(">", 1)[1].split("<", 1)[0] for t in svg.split("<text")[1:]]
    for value in ("10", "27", "200", "237", "60", "e = 625"):
        assert value in texts, (value, texts)
    assert "Installationen" not in svg, "a load typed has no thickness to draw"
    # the band heights to scale, the thinnest one held at MIN_BAND
    heights = [float(r.split('height="')[1].split('"')[0]) for r in svg.split("<rect")[1:]]
    assert max(heights) > min(heights) >= dead_load_svg.MIN_BAND


def test_the_export_carries_sources_beside_sheets_and_refuses_one_id_twice():
    """ARCH-003, ARCH-004 (D-04): calculations 1.5 -- a source's instance names its file and no workbook, its drawing is written under data/calculations/; an id a sheet carries too is refused naming both; a domain with sources and no sheet is not warned about."""
    here = conftest.project_copy("dead_load_source_export")
    folder = here.sources_dir / dead_load_source.FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "DA-01.json").write_text(json.dumps(_roof(chosen=2.0), ensure_ascii=False, indent=2), encoding="utf-8")
    built = fx.build(here.root / "Belastungsannahmen.xlsx", sheet="EL+AL-Test", layers=(fx.layer("gk", "Tragstruktur", "Kerto-Q", d=0.06),),
                     library=(("Tragstruktur", "Kerto-Q", 500, "kg/m3"),), chosen=0.3)
    workbooks = [io_excel.open_cells(built["path"])]
    files = {}
    err = io.StringIO()
    with redirect_stderr(err):
        data = registry.build_calculations(workbooks, here, files)
    place = engine.Figures(here.data_dir, "dead-load", here)   # Permanent-loads/Exports/Figures/ laid out by folders, data/calculations/ before (issue #64)
    assert data["schema_version"] == "1.8"   # every export since v0.120: no line carries a level, 1.8 holding 1.7's rooted drawings (UI-002)
    instances = data["domains"]["dead-load"]["instances"]
    assert list(instances) == ["EL+AL-Test", "DA-01"], "the sheets first, then the sources"
    source = instances["DA-01"]
    assert source["engine"] == "python" and source["source_file"] == "loads/dead/DA-01.json" and "workbook" not in source
    name = place.name("dead-load-DA-01.svg")
    assert source["figures"][0]["file"] == name and name in files
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)
    assert "dead-load" not in err.getvalue()
    registry.write_files(files, here.data_dir)
    assert place.path(name).read_bytes().count(b"\r\n") == 0
    # one id, two cases: refused, naming the source and the workbook
    (folder / "EL+AL-Test.json").write_text(json.dumps(_roof("EL+AL-Test")), encoding="utf-8")
    try:
        registry.build_calculations(workbooks, here, {})
    except validation.ValidationError as exc:
        assert "loads/dead/EL+AL-Test.json" in str(exc) and "Belastungsannahmen.xlsx" in str(exc), str(exc)
    else:
        raise AssertionError("one id in a sheet and a source passed")
    # a 1.4 export (no source) is still a valid one
    old = {"schema_version": "1.4", "domains": {}}
    validation.validate_structure(old, "calculations")


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
        d = conftest.probe_dir("dl_written_out")
        (d / "domain.typ").write_text(text, encoding="utf-8")
        (d / "probe.typ").write_text('#import "/000-Typst-Config/commands.typ": *\n#include "domain.typ"\n', encoding="utf-8")
        out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(d / "probe.typ"), str(d / "probe.svg")],
                             capture_output=True, text=True, encoding="utf-8")
        assert out.returncode == 0, out.stderr
        assert "<image" in (d / "probe.svg").read_text(encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)
        (here.data_dir / "calculations.json").write_bytes(kept)
