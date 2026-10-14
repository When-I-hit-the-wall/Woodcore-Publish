"""The quantities of the position plans, by material and section (calc/domains/quantities.py; issue #9, REQ-013, REQ-014, ARCH-002, ARCH-005, D-008, Q-014).

What is held: an element is one row, measured with the plan's own length (plan.element_length_m) -- a beam's volume its length times b·h, a round one's π d²/4, a CLT slab's its area times t; a wall in CLT, a column and a steel profile have no volume; a position with no section is counted and said; openings, concrete and loads are not counted --; the rows of a scope add up by material then section, with a total per material; the report's data file states its version and its totals; and what the report adds up for chosen positions is what `summary` gives.
"""

import json
import subprocess

import conftest
from conftest import Skip
from domains import plan
from domains import quantities

ROWS = [
    {"position": "T101", "type": "Träger", "material": "Fichte", "strength_class": "C24", "section_type": "rec", "dimension": "100/200", "units": "mm"},
    {"position": "T102", "type": "Träger", "material": "Fichte", "strength_class": "C24", "section_type": "cir", "dimension": "200", "units": "mm"},
    {"position": "D101", "type": "Decke/Dach", "material": "BSP", "section_type": "clt", "dimension": "40/20/40", "units": "mm"},
    {"position": "V101", "type": "vertikal tragende Wand", "material": "BSP", "section_type": "clt", "dimension": "40/20/40", "units": "mm"},
    {"position": "S101", "type": "Stütze", "material": "Fichte", "strength_class": "GL24h", "section_type": "rec", "dimension": "140/140", "units": "mm"},
    {"position": "A101", "type": "Aussteifung, Stabilisierung Einzelstab", "material": "Stahl", "strength_class": "S235", "section_type": "ROR", "dimension": "60.3x4"},
    {"position": "H101", "type": "aussteifende Wand", "material": "OSB"},
]


def _plans():
    """Two plans at 100 sheet units a metre: one with a 4 m beam, a 2 m round beam, a 3 × 4 m CLT slab, a 5 m CLT wall, a column, a 2.5 m steel tube, a wall with no section, an opening and a load; the other with a second 4 m beam T101."""
    first = plan.new_source("EG", floor="1")
    first["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1.0}
    first["elements"] = [
        {"type": "T", "label": "T101", "points": [[0, 0], [400, 0]]},
        {"type": "T", "label": "T102", "points": [[0, 100], [200, 100]]},
        {"type": "D", "subtype": "normal", "label": "D101", "points": [[0, 0], [300, 0], [300, 400], [0, 400]]},
        {"type": "V", "label": "V101", "points": [[0, 500], [500, 500]]},
        {"type": "S", "label": "S101", "points": [[600, 600]]},
        {"type": "A", "label": "A101", "points": [[0, 700], [250, 700]]},
        {"type": "H", "label": "H101", "points": [[0, 800], [100, 800]]},
        {"type": "Ö", "label": "", "points": [[10, 10], [20, 10], [20, 20]]},
    ]
    second = plan.new_source("OG", floor="2")
    second["scale"] = first["scale"]
    second["elements"] = [{"type": "T", "label": "T101", "points": [[0, 0], [0, 400]]}]
    return [first, second]


def test_every_element_is_one_row_measured_as_the_plan_measures_it():
    found, notes = quantities.rows(_plans(), ROWS)
    by = {(r["plan"], r["position"]): r for r in found}
    assert len(found) == 8, [r["position"] for r in found]
    beam = by[("EG", "T101")]
    assert beam["length_m"] == 4.0 and abs(beam["volume_m3"] - 4.0 * 0.1 * 0.2) < 1e-12 and beam["material"] == "Fichte C24" and beam["section"] == "100/200 mm"
    assert abs(by[("EG", "T102")]["volume_m3"] - 2.0 * 3.141592653589793 * 0.1 ** 2) < 1e-12, "a round section: π d²/4"
    slab = by[("EG", "D101")]
    assert slab["length_m"] is None and slab["area_m2"] == 12.0 and abs(slab["volume_m3"] - 12.0 * 0.1) < 1e-12, "a CLT slab: area × t"
    assert by[("EG", "V101")]["length_m"] == 5.0 and by[("EG", "V101")]["volume_m3"] is None, "a CLT wall has no height on a plan"
    assert by[("EG", "S101")]["length_m"] is None and by[("EG", "S101")]["volume_m3"] is None, "a column's height is not on a plan"
    assert by[("EG", "A101")]["length_m"] == 2.5 and by[("EG", "A101")]["volume_m3"] is None, "steel: a length, no volume (D-008)"
    assert by[("EG", "H101")]["volume_m3"] is None and any("H101" in n for n in notes), "no section: counted, and said"
    assert by[("EG", "T101")]["length_m"] == plan.element_length_m(_plans()[0]["elements"][0], plan.units_per_m(_plans()[0])), "the plan's own length"
    unscaled = _plans()
    del unscaled[0]["scale"]
    found, notes = quantities.rows(unscaled, ROWS)
    assert all(r["length_m"] is None for r in found if r["plan"] == "EG") and any("EG" in n and "no scale" in n for n in notes)


def test_a_scope_adds_up_by_material_then_section_with_a_total_per_material():
    found, _ = quantities.rows(_plans(), ROWS)
    groups, totals = quantities.summary(found)
    keys = [(g["material"], g["section"]) for g in groups]
    assert keys == sorted(keys, key=lambda k: (k[0].lower(), k[1].lower())), "by material, then section"
    beams = next(g for g in groups if g["section"] == "100/200 mm")
    assert beams["pieces"] == 2 and beams["length_m"] == 8.0 and abs(beams["volume_m3"] - 0.16) < 1e-12, "T101 on both plans"
    fichte = next(t for t in totals if t["material"] == "Fichte C24")
    assert fichte["pieces"] == 3 and abs(fichte["length_m"] - 10.0) < 1e-12
    steel = next(t for t in totals if t["material"] == "Stahl S235")
    assert steel["volume_m3"] is None and steel["length_m"] == 2.5
    one, _ = quantities.summary(found, "plans", plans=["OG"])
    assert [(g["section"], g["pieces"], g["length_m"]) for g in one] == [("100/200 mm", 1, 4.0)]
    chosen, chosen_totals = quantities.summary(found, "positions", positions=["D101", "V101"])
    assert [(g["material"], g["pieces"], g["area_m2"]) for g in chosen] == [("BSP", 2, 12.0)] and chosen_totals[0]["length_m"] == 5.0
    try:
        quantities.summary(found, "storey")
    except ValueError as exc:
        assert "storey" in str(exc)
    else:
        raise AssertionError("an unknown scope was accepted")


def test_the_report_s_data_states_its_version_rows_and_totals():
    import validation
    doc, _notes = quantities.document(_plans(), ROWS)
    validation.validate_structure(doc, "quantities")
    assert doc["schema_version"] == "1.0" and len(doc["rows"]) == 8 and set(doc["plans"]) == {"EG", "OG"}
    og, = doc["plans"]["OG"]["totals"]
    assert (og["material"], og["pieces"], og["length_m"], og["area_m2"]) == ("Fichte C24", 1, 4.0, None) and abs(og["volume_m3"] - 0.08) < 1e-12
    assert quantities.metres(None) == "—" and quantities.metres(12.3456) == "12.35" and quantities.metres(0.16, 3) == "0.160"


def _project(name):
    """A copy of the example project, its engine synced, its data/quantities.json the two plans' of this file."""
    import shutil
    import project
    root = conftest.tmpdir(name) / "Exemple"
    shutil.copytree(conftest.ROOT / "tests" / "projet-exemple", root, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv"))
    here = project.Project.load(root / "Exemple.woodcore")
    project.sync_engine(here)
    doc, _ = quantities.document(_plans(), ROWS)
    (here.data_dir / "quantities.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return here


def _text(here, body, lang):
    import unicodedata
    import project
    from pypdf import PdfReader
    probe = here.typst_root / f"probe-{lang}.typ"
    probe.write_text(f'#import "/commands.typ": *\n#set-report-language("{lang}")\n{body}\n', encoding="utf-8")
    out = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(probe.with_suffix(".pdf"))],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr
    return " ".join(unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(probe.with_suffix(".pdf"))).pages)).split())


def test_the_report_prints_the_export_s_summary_and_adds_up_chosen_positions_as_python_does():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    here = _project("quantities_report")
    found, _ = quantities.rows(_plans(), ROWS)
    groups, totals = quantities.summary(found, "positions", positions=["T101", "T102", "A101"])
    for lang, words in (("de", ("Ausmass", "Material", "Volumen")), ("fr", ("Métrés", "Matériau", "Volume")), ("en", ("Quantities", "Material", "Volume"))):
        text = _text(here, '#show-plan-quantities(scope: "positions", positions: ("T101", "T102", "A101"))', lang)
        assert all(w in text for w in words), (lang, text)
    # the numbers Python gives, at the summary's decimals: what the report added up itself
    for g in groups:
        assert quantities.metres(g["length_m"]) in text and quantities.metres(g["volume_m3"], 3) in text, (g, text)
    fichte = next(t for t in totals if t["material"] == "Fichte C24")
    assert quantities.metres(fichte["length_m"]) in text and "Total" in text
    assert "—" in text, "steel has no volume"
    # one plan: the export's own summary
    assert "4.00" in _text(here, '#show-plan-quantities(scope: "plans", plans: "OG", title: none)', "fr")
    # a plan the export does not know is refused, naming the plans there are
    import project
    probe = here.typst_root / "probe-bad.typ"
    probe.write_text('#import "/commands.typ": *\n#show-plan-quantities(scope: "plans", plans: "Nope")\n', encoding="utf-8")
    out = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(probe.with_suffix(".pdf"))], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert out.returncode != 0 and "EG, OG" in conftest.panic_message(out.stderr), out.stderr[:400]


def test_a_sheet_carries_the_quantities_of_its_plans():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import sheets
    import typst_objects as to
    here = _project("quantities_sheet")
    sheets.new_sheet(here)
    oid = sheets.add_quantities(here, "B01", 20, 30, width=150, plans="EG")
    assert oid and sheets.model(here, "B01", oid).get("width") is not None
    ok, message = sheets.compile(here, "B01")
    assert ok, message
    from pypdf import PdfReader
    text = " ".join("\n".join(p.extract_text() for p in PdfReader(str(sheets.pdf(here, "B01"))).pages).split())
    assert "Ausmass" in text and "BSP" in text and "Fichte C24" in text and "Total" in text, text   # the plan EG's own summary
    assert isinstance(sheets.model(here, "B01", oid), to.QuantitiesModel)


def test_the_length_of_a_position_is_its_elements_added_up_as_the_summary_adds_them():
    """Issue #14 (REQ-003): the Positions tab's length, `length_by_position`, is every element of the position on every plan -- T101's 4 m on EG and 4 m on OG -- and what `summary` gives for that position alone; a column and a slab have none."""
    found, _notes = quantities.rows(_plans(), ROWS)
    lengths = quantities.length_by_position(found)
    assert lengths["T101"] == 8.0 and lengths["V101"] == 5.0 and lengths["A101"] == 2.5
    assert lengths["S101"] is None and lengths["D101"] is None, "a column and a slab are drawn with no length"
    for pid, length in lengths.items():
        _groups, totals = quantities.summary(found, "positions", positions=[pid])
        added = None
        for total in totals:
            added = total["length_m"] if added is None else (added + total["length_m"] if total["length_m"] is not None else added)
        assert added == length, (pid, added, length)


def test_the_plans_measured_are_the_position_plans_and_never_a_section(tmp_path=None):
    """Issue #14 (ARCH-RISK-001): `position_plan_sources` is the one place that says which plans are measured -- the export's and the Positions tab's alike."""
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as folder:
        d = Path(folder)
        first, second = _plans()
        cut = plan.new_source("C1")
        cut["plan_type"] = "section"
        for source in (first, second, cut):
            (d / f"{source['id']}.json").write_text(json.dumps(source), encoding="utf-8")
        try:
            ids = [s["id"] for s in plan.position_plan_sources(d)]
        except Exception as exc:   # a section the checker refuses as a bare stub is not this test's subject
            if "section" not in str(exc):
                raise
            (d / "C1.json").unlink()
            ids = [s["id"] for s in plan.position_plan_sources(d)]
        assert ids == ["EG", "OG"], ids
