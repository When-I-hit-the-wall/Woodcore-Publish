"""A connector from its source file to `data/connectors.json` -- `calc/domains/connector.py` (docs/domain/connectors.md §3.3nonies).

What this file is for is the seam, not the arithmetic: `test_dowel.py` holds the numbers, and here the question is whether a source is read, checked, resolved and exported the way the rest of the pipeline expects.

Three rules earn most of the tests, because each of them is a decision that could plausibly have gone the other way:

- **A member's timber is a reference, resolved afresh at every export.** Changing a position's `material` in Excel must change the resistance with no other action -- which is the whole reason it is a reference and not a copy, and which a copied value would silently break.
- **A reference that no longer resolves warns and does not stop.** The v0.33 rule: stopping would stop the positions' own export with it and leave the window nothing to relink the connector to. The record is still complete on its descriptive half, `calculated` is false, and it carries the reason the report refuses with.
- **The descriptive half survived the 1.0 -> 2.0 bump.** `connector-summary` in `lib/calc-engine.typ` and `build_reference`'s Connectors sheet read nine keys of it by name; keeping them buys that neither had to change when the connectors left Excel.

👉 The dangling reference was not invented for the test: `connectors/SD_01.json` named `D001` for a while, a position v0.59 swept out of `Positionen.xlsx`, and it is what the first export after the v0.68 migration warned about. v0.70 repaired that file, so the case is now made here rather than met in the project -- which is what a test is for.

Since schema 1.1 (v0.70) three more decisions are held here, each the kind that could have gone the other way: the connection carries **one** moisture class rather than one per member, a grade written beside a position **overrides it and stays overridden**, and `plates.thickness` is refused until the plate's own check exists.
"""

import copy
import json

import conftest
import line_levels
from conftest import ROOT, Skip, tmpdir
from domains import connector, dowel
from domains import schema
import validation

# the project the tests work on: the example project, copied for this run (conftest.PROJECT, v0.81)
SOURCES = conftest.PROJECT.connectors_dir
DATA = conftest.PROJECT.data_dir

# The nine keys the Typst side and the reference workbook read off a connector by name.
DESCRIPTIVE = ("position", "type", "assembly", "diameter", "length", "dimension",
               "steel", "predrilled", "elements", "description")


# What every probe of this file writes above its call: the report's own setup, read from the
# Typst root, so the directory's depth is the harness's and not this test's (tests/test_harness.py).
PROBE_PREAMBLE = ('#import "/000-Typst-Config/config.typ": conf\n'
                  '#import "/000-Typst-Config/commands.typ": *\n'
                  '#show: conf\n')


def _raised(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except validation.ValidationError as exc:
        return str(exc)
    raise AssertionError("%s should have raised a ValidationError" % getattr(fn, "__name__", fn))


def _detail(positions=("T001", "S001"), **overrides):
    """The detail schema a connector is drawn on since v0.74: two pieces crossing at the origin, and four
    markers at the corners of a 120 x 120 square. Its elements ARE the members and its markers the
    fasteners, so everything geometric a connector used to carry is here instead."""
    detail = {
        "schema_version": schema.SOURCE_SCHEMA_VERSION,
        "id": "D_99",
        "label": "Testdetail",
        "elements": [
            {"id": "E1", "kind": "linear", "points": [[-230, 0], [230, 0]], "view": "h", "h": 200},
            {"id": "E2", "kind": "linear", "points": [[0, -100], [0, 230]], "view": "h", "h": 200},
        ],
        "connectors": [
            {"id": "C1", "kind": "Stabd\u00fcbel", "x": -60, "z": -60},
            {"id": "C2", "kind": "Stabd\u00fcbel", "x": 60, "z": -60},
            {"id": "C3", "kind": "Stabd\u00fcbel", "x": -60, "z": 60},
            {"id": "C4", "kind": "Stabd\u00fcbel", "x": 60, "z": 60},
        ],
        "aids": [{"id": "A1", "kind": "centre", "x": 0, "z": 0}],
        "dimensions": [],
    }
    for element, pid in zip(detail["elements"], positions):
        if pid:
            element["position"] = pid
    detail.update(overrides)
    return detail


DETAIL = _detail()


def _source(**overrides):
    """A connector that calculates, drawn on `DETAIL`, with its timber stated rather than followed."""
    source = connector.new_source("SD_99", schema=DETAIL["id"])
    source["assembly"] = "Holz-Holz zweischnittig"
    source["diameter"] = {"value": 14, "unit": "mm"}
    source["fasteners"] = ["C1", "C2", "C3", "C4"]
    source["n_tot"] = {"value": 4, "override": False}
    source["moisture_class"] = 1        # one per connection since schema 1.1, not one per member
    for index, member in enumerate(source["members"]):
        member["element"] = "E%d" % (index + 1)
        member["material"] = {"grade": "GL24h"}
        member["t"] = {"value": 70 if index == 0 else 100, "unit": "mm"}
        member["n"] = 2
        member["a_1"] = {"value": 120, "unit": "mm"}
        member["alpha"] = 0
    source.update(overrides)
    return source


def _record(source, positions=None, detail=None):
    """build_record with the schema the fixture draws on -- the one extra argument every call needs since v0.74."""
    return connector.build_record(source, positions if positions is not None else {},
                                  DETAIL if detail is None else detail)


POSITIONS = {
    "T001": {"material": "C24", "moisture_class": 2},
    "S001": {"material": "GL24h", "moisture_class": 1},
    "S002": {"material": "S355", "moisture_class": 2},
}


# --- the source ---------------------------------------------------------------

def test_a_new_source_passes_its_own_checks():
    """«Nouveau» must produce something the checks accept, or the tab opens on an error."""
    connector.check_source(connector.new_source("SD_01"), "SD_01.json")


def test_an_id_that_is_not_the_file_name_is_refused():
    """A connector's id is the string the report addresses it by; the file is how it is found."""
    path = tmpdir("connectors") / "SD_77.json"
    source = _source(id="SD_78")
    path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
    assert "its file name" in _raised(connector.read_source, path)


def test_a_configuration_the_norm_does_not_cover_is_refused_with_the_reason():
    message = _raised(connector.check_source, _source(assembly="Holz-Holz mehrschnittig"), "SD_99.json")
    assert "6.1.1.11" in message


def test_the_fastener_count_must_agree_with_the_drawing_unless_it_says_otherwise():
    source = _source()
    source["n_tot"] = {"value": 9, "override": False}
    assert "override" in _raised(connector.check_source, source, "SD_99.json")
    source["n_tot"] = {"value": 9, "override": True}
    connector.check_source(source, "SD_99.json")   # said deliberately, so it passes


def test_one_marker_ticked_twice_is_refused():
    """Two markers at one POINT is the schema's own check now; what this file can still say is that one
    marker must not be ticked twice, which would count a fastener twice over."""
    source = _source()
    source["fasteners"] = ["C1", "C1"]
    source["n_tot"] = {"value": 2, "override": False}
    assert "twice" in _raised(connector.check_source, source, "SD_99.json")


def test_a_connector_naming_no_marker_is_a_draft_and_not_a_defect():
    """⚠️ Since schema 2.0 the coordinates are the schema's, so «no marker ticked» is a state of the
    DRAWING and not of this file: `check_source` lets it through -- «Nouveau» would otherwise open on an
    error, which is what v0.70 fixed -- and the record says it could not be calculated, with its reason.
    """
    source = _source()
    source["fasteners"] = []
    source["n_tot"] = {"value": 1, "override": False}
    connector.check_source(source, "SD_99.json")
    record, _warnings = _record(source, POSITIONS)
    assert record["calculated"] is False
    assert record["reason"], "the report prints the reason instead of a resistance"


def test_a_block_belonging_to_another_kind_of_fastener_is_refused():
    """Exactly the type's own block, and no other -- which is what lets a second kind add a block instead of widening the file."""
    source = _source()
    source["nail"] = {"something": 1}
    connector.TYPE_BLOCK["Nagel"] = "nail"
    try:
        assert "another kind" in _raised(connector.check_source, source, "SD_99.json")
    finally:
        del connector.TYPE_BLOCK["Nagel"]


def test_hardwood_that_is_not_predrilled_is_refused_by_the_calculation():
    """SIA 265 Tabelle 22 gives hardwood one row only. The source may state it; the calculation refuses it."""
    source = _source()
    source["members"][0]["material"] = {"grade": "D30", "moisture_class": 1}
    source["members"][0]["predrilled"] = False
    record, _warnings = _record(source)
    assert not record["calculated"] or "Laubholz" in record.get("reason", "")


# --- resolving the timber -------------------------------------------------------

def test_a_position_reference_is_resolved():
    source = _source()
    source["moisture_class"] = None      # follow the positions, which is what is under test here
    # both members from the same position, so the only thing under test is the resolution itself
    for member in source["members"]:
        member["material"] = None                  # follow the element's position
    record, warnings = _record(source, POSITIONS, _detail(("T001", "T001")))
    assert warnings == [], warnings
    member = record["members"][0]
    assert member["grade"] == "C24" and member["moisture_class"] == 2
    assert member["material_from"] == "C24, aus Position T001"
    assert member["resolved"] is True


def test_the_reference_is_resolved_afresh_at_every_export():
    """The point of a reference rather than a copy: a strength class changed in Excel reaches the resistance with nothing else to do -- «Importer Excel» and no “Reprendre” button.

    Here the same untouched source is built twice against two different position records, and the density the calculation used must follow.
    """
    source = _source()
    for member in source["members"]:
        member["material"] = None                  # follow the element's position

    both = _detail(("T001", "T001"))
    soft, _ = _record(copy.deepcopy(source), {"T001": {"material": "C24", "moisture_class": 1}}, both)
    strong, _ = _record(copy.deepcopy(source), {"T001": {"material": "GL32h", "moisture_class": 1}}, both)

    assert soft["vars"]["rho_k_1"]["value"] == 350
    assert strong["vars"]["rho_k_1"]["value"] == 440
    assert strong["vars"]["R_d_Verb"]["value"] > soft["vars"]["R_d_Verb"]["value"], (
        "a denser timber must give a larger resistance, or nothing was re-resolved")


def test_a_reference_that_no_longer_resolves_warns_and_does_not_stop():
    """The v0.33 rule. connectors/SD_01.json is the real instance: its second member names D001, which Positionen.xlsx has not carried since v0.59."""
    source = _source()
    source["members"][1]["material"] = None
    record, warnings = _record(source, POSITIONS, _detail(("T001", "D001")))
    assert any("D001" in w for w in warnings), warnings
    assert record["calculated"] is False
    assert record["reason"], "the report prints the reason instead of a resistance"
    assert record["results"] == [] and record["vars"] == {}
    # and the descriptive half is still whole, so the window has something to relink
    for key in DESCRIPTIVE:
        assert key in record


def test_a_position_that_is_not_timber_warns():
    """S002 carries S355 -- a steel column. There is no rho_k to take from it, so the connector is described and not calculated."""
    source = _source()
    source["members"][0]["material"] = None
    record, warnings = _record(source, POSITIONS, _detail(("S002", "S001")))
    assert record["calculated"] is False
    assert any("S002" in w or "S355" in w for w in warnings) or "Festigkeitsklasse" in record["reason"]


def test_the_worst_moisture_class_governs_and_is_said():
    """One class for the connection, taken from the members' positions: the worst wins, and the record says which."""
    source = _source()
    source["moisture_class"] = None                            # follow the positions
    for member in source["members"]:
        member["material"] = None          # T001 is class 2, S001 class 1
    record, warnings = _record(source, POSITIONS, _detail(("T001", "S001")))
    assert record["moisture_class"] == 2
    assert record["vars"]["eta_w"]["value"] == 0.8
    assert any("Feuchteklasse" in w for w in record["warnings"]), record["warnings"]


def test_the_connection_carries_one_moisture_class_and_a_member_may_not():
    """SIA 265 applies one eta_w to R_d,Verb (Tabelle 4) and the classeur states one per sheet. A 1.0 source's per-member class is a defect once the file says it is 1.1."""
    source = _source()
    source["members"][0]["material"]["moisture_class"] = 2
    assert "the connection has one" in _raised(connector.check_source, source, "SD_99.json")


def test_a_member_may_not_name_a_position_beside_its_element():
    """Since schema 2.0 the element is the one place a position is named."""
    source = _source()
    source["members"][0]["material"] = {"position": "T001", "grade": "GL24h"}
    assert "second place" in _raised(connector.check_source, source, "SD_99.json")


def test_a_stated_moisture_class_wins_over_the_positions():
    source = _source()
    source["moisture_class"] = 3                               # stated here
    for member in source["members"]:
        member["material"] = None                              # the positions say 1
    record, _warnings = _record(source, POSITIONS, _detail(("S001", "S001")))
    assert record["moisture_class"] == 3
    assert "festgelegt" in record["moisture_from"], record["moisture_from"]
    assert "S001" in record["moisture_from"], "the line must still say what the position holds"


# --- the record -----------------------------------------------------------------

def test_a_type_with_no_module_is_described_and_not_calculated():
    source = _source()
    source["type"] = "Nagel"
    source.pop("dowel", None)
    record, warnings = _record(source)
    assert record["calculated"] is False
    assert "Nagel" in record["reason"]
    assert record["type"] == "Nagel" and record["assembly"] == source["assembly"]
    assert any("Nagel" in w for w in warnings)


def test_the_descriptive_half_survived_the_version_bump():
    """The nine keys `connector-summary` (lib/calc-engine.typ) and build_reference's Connectors sheet read by name, with the types schema 1.0 gave them. Keeping them is what bought the Typst side not having to change when the connectors left Excel."""
    record, _ = _record(_source())
    for key in DESCRIPTIVE:
        assert key in record, "the descriptive half lost %r" % key
    assert record["position"] == record["position"]
    assert isinstance(record["elements"], list)
    assert isinstance(record["dimension"], str) and isinstance(record["steel"], str)
    assert record["predrilled"] in (True, False, None)
    assert set(record["diameter"]) == {"value", "unit"}


def test_predrilling_is_derived_from_the_members():
    source = _source()
    record, _ = _record(source)
    assert record["predrilled"] is True
    source["members"][1]["predrilled"] = False
    record, _ = _record(source)
    assert record["predrilled"] is None, "members that disagree leave the descriptive word open"


def test_an_overridden_count_travels_to_the_record_and_warns():
    source = _source()
    source["n_tot"] = {"value": 6, "override": True}
    record, warnings = _record(source)
    assert record["n_tot"] == 6 and record["n_tot_override"] is True
    # the symbol is written between dollars since v0.77, so the report and the window set it as n with «tot» below
    assert any('$n_"tot"$' in w for w in warnings)
    assert any('$n_"tot"$' in w for w in record["warnings"]), "the report prints it too"


def test_a_spacing_below_tabelle_24_warns_without_stopping():
    source = _source()
    source["diameter"] = {"value": 20, "unit": "mm"}   # 7 · 20 = 140 mm needed, 120 mm there
    record, warnings = _record(source)
    assert record["calculated"] is True, "a layout to move is not a defect in the data"
    assert any("Tabelle 24" in w for w in warnings), warnings


def test_the_minimum_spacings_are_laid_out_as_the_classeur_lays_them_out():
    """v0.77, the engineer: «le tableau des distances doit ressembler à celui dans excel» -- 'Stabdübel (Holz-Holz)'!A47:E53: a row per distance, its value and its multiple of d in the grain direction and across it, and the minimum length under them. No «vorhanden» and no «Nachweis»: the check stays a warning (the test above), not a column."""
    record, _ = _record(_source())
    titles = [t["title"] for t in record["tables"]]
    assert "Lage der Verbindungsmittel" not in titles, "the fasteners' positions left the report (the pattern figure shows them)"
    table = next(t for t in record["tables"] if t["title"] == "Minimale Abstände")
    labels = [c["label"] for c in table["columns"]]
    assert "vorhanden" not in labels and "Nachweis" not in labels and "Richtung" not in labels
    d = record["vars"]["d"]["value"]
    # v0.84, the engineer: the cell that was empty names the diameter every cell below is a multiple of
    assert table["columns"][0]["group"] == "$d$ = %g mm" % d
    assert [c.get("group") for c in table["columns"][1:]] == ["in Faserrichtung", "in Faserrichtung",
                                                             "senkrecht zur Faserrichtung", "senkrecht zur Faserrichtung"]
    rows = {row[0]: row[1:] for row in table["rows"]}
    assert list(rows) == ["von Stabdübel zu Stabdübel", "vom beanspruchten Rand", "vom unbeanspruchten Rand"]
    assert rows["von Stabdübel zu Stabdübel"] == [7 * d, "$7 d$", 3 * d, "$3 d$"]
    assert rows["vom beanspruchten Rand"][1] == "$7 d$ (min. 80 mm)" and rows["vom beanspruchten Rand"][0] == max(7 * d, 80)
    assert table["totals"] and table["totals"][0][0] == "min. Länge der Verbindung"
    assert isinstance(table["totals"][0][1], (int, float)) and isinstance(table["totals"][0][3], (int, float)), "both directions, as B53 and D53"
    assert table["level"] == 1


def test_the_slip_modulus_is_a_formula_and_not_a_table():
    """v0.84, the engineer: Tabelle 25's own formula in the report, where a table of its results stood.

    Three things the formula has to carry that the table could not. eta_w is **inside** it, on each
    member's own K_ser rather than on the connection's -- the product is the same and this is where the
    report can say it. K_ser,Verb is `n_tot dot p dot K_ser`, a formula and no longer a totals row. And
    it is level 1: show-connector-resistance prints it under R_d,Verb at every level, an engineer
    reading a resistance wanting the stiffness beside it.
    """
    record, _ = _record(_source())
    titles = [t["title"] for t in record["tables"]]
    assert "Verschiebungsmodul" not in titles, "the table became the formulas above it"
    steps = {st["result"]: st for st in record["steps"]}
    assert 'eta_(w,"Steif")' in steps["K_ser_1"]["formula"], "eta_w belongs inside Tabelle 25's formula"
    assert steps["K_ser_Verb"]["formula"] == 'K_("ser","Verb") = n_"tot" dot p dot K_"ser"'
    assert line_levels.level("connector", "K_ser_Verb") == 1   # lib/line-levels.json's, a line carrying no level since v0.120 (UI-002)
    assert record["vars"]["K_ser_Verb"]["norm_ref"] == "6.2.1.4"
    # it is not one of the `results`: those are the resistances a verification reads
    assert "K_ser_Verb" not in record["results"]


def test_the_norms_own_formulas_are_written_out_rather_than_tabulated():
    """v0.84, the engineer: «au lieu de faire un tableau qui n'affiche que les résultats, reprends les formules ... et écris-les dans le rapport», for Tabelle 22, for the thicknesses and k_beta, and for Tabelle 25.

    ⚠️ The formulas written out are Tabellen **45 and 46**'s and not Tabelle 23's, which the engineer named: Tabelle 23 is the simplified k_beta of 6.2.1.1 and this module has computed the more accurate Anhang A form since v0.68, at his own choice -- printing Tabelle 23 would put formulas on the page that do not produce the numbers beside them.
    """
    record, _ = _record(_source())
    titles = [t["title"] for t in record["tables"]]
    assert "Lochleibungsfestigkeit" not in titles and "Verschiebungsmodul" not in titles
    steps = {st["result"]: st for st in record["steps"]}
    # Tabelle 22, both directions and the interpolation between them
    assert "0.082" in steps["f_h_0_1"]["formula"] and "1.35" in steps["f_h_90_1"]["formula"]
    assert steps["f_h_1"]["norm_ref"] == "6.1.4.3"
    # Tabelle 45: the corners of Figur 45, each as the row it was read off
    for name in ("t_c_1_1", "k_beta_1_1", "t_c_1_2", "k_beta_1_2", "k_beta_1", "t_c_2_2", "k_beta_2"):
        assert name in steps, name
        assert steps[name]["norm_ref"] == "A.1.1", name
    assert "0.44" in steps["t_c_1_1"]["formula"] and "1.26" in steps["t_c_1_2"]["formula"]
    assert "2.52" in steps["t_c_2_2"]["formula"], "the Mittelholz's own factor, equation (121)"
    # Tabelle 25's own formula, and its eta_w inside it (tests/test_norms.py holds that not one of
    # these coefficients is written into dowel.py: each is composed from calc/norms/)
    assert 'eta_(w,"Steif")' in steps["K_ser_1"]["formula"]


def test_the_short_formulas_are_set_on_one_line():
    """v0.84, the engineer: «rend les calculs moins étalés verticalement». A step says whether its
    formula is short enough to be read across one line -- its letters, its numbers and its answer
    joined -- and equation (88) deliberately does not, being the long one.
    """
    record, _ = _record(_source())
    for step in record["steps"]:
        if step["result"] == "R_d":
            assert not step.get("inline"), "equation (88) is the long one and stays on two rows"
        else:
            assert step.get("inline"), "%s is short and reads on one row" % step["result"]


def test_a_truss_node_reduces_both_answers():
    """v0.84, the engineer: «il faut calculer un R_d,Verb,Fachwerk ainsi qu'un R_d,Fachwerk». The report
    gives both resistances, so 5.3.6.2.2 reduces both; neither is ever folded into the other, where a
    reader could not see it.
    """
    source = _source()
    source["conditions"] = {"seismic": False, "truss": True}
    record, _ = _record(source)
    assert record["results"] == ["R_d", "R_d_Verb", "R_d_Fachwerk", "R_d_Verb_Fachwerk"]
    v = record["vars"]
    assert v["R_d_Fachwerk"]["value"] < v["R_d"]["value"]
    assert v["R_d_Verb_Fachwerk"]["value"] < v["R_d_Verb"]["value"]
    for name in ("R_d_Fachwerk", "R_d_Verb_Fachwerk"):
        assert v[name]["norm_ref"] == "5.3.6.2.2"


def _written_out(folder, cid):
    """The connector `cid` of the export written out as Woodcore writes its file (calc/domains/unfold.py), into `folder`/connector.typ."""
    import conftest
    import project
    from domains import unfold
    data = json.loads((DATA / "connectors.json").read_text(encoding="utf-8"))
    with project.using(conftest.PROJECT):
        text = unfold.generate(unfold._module("connector").records(data)[cid], "de", "connector")
    (folder / "connector.typ").write_text(text, encoding="utf-8")


def test_the_report_prints_the_tables_and_the_two_figures_as_asked():
    """v0.77, end to end on the project's own export: the connector's domain as Woodcore writes it out (spec 2026-10-21-commandes-typst-refonte, REQ-017; `#show-connector-resistance` until then) at level 3, compiled and read back out of the PDF. The two figures, each with its caption; no «Lage der Verbindungsmittel», no «vorhanden»/«Nachweis»; the slip modulus's value where the var's name was; and no symbol printed with a bare underscore (`Hilfswert k_β` was, before the title learned `$k_beta$`)."""
    import re
    import subprocess
    import conftest
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    exported = json.loads((DATA / "connectors.json").read_text(encoding="utf-8")).get("connectors", {})
    cid = next((k for k, v in exported.items() if v.get("calculated")), None)
    if cid is None:
        raise Skip("no calculated connector in data/connectors.json -- export first")
    d = conftest.probe_dir("connector_report")
    probe = d / "probe.typ"
    # absolute imports, read from the Typst root: the directory's depth is the harness's, not this test's (tests/test_harness.py)
    _written_out(d, cid)
    probe.write_text('#import "/000-Typst-Config/config.typ": conf\n#import "/000-Typst-Config/commands.typ": *\n#show: conf\n'
                     '#calc-defaults(level: 3, scope: "document")\n#include "connector.typ"\n', encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    from pypdf import PdfReader
    raw = "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
    text = re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", raw))
    assert "Anordnung der Verbindungsmittel" in text and "Schnitt durch die Verbindung" in text, "the two captions"
    assert "Lage der Verbindungsmittel" not in text
    assert "vorhanden" not in text and "Nachweis" not in text
    assert "senkrecht zur Faserrichtung" in text
    assert "K_ser_Verb" not in text and "K_ser,Verb" not in text, "the slip modulus's totals print a value"
    assert "k_β" not in text and "k_red" not in text and "eta_w" not in text, "a symbol printed with its underscore"


def test_the_inputs_and_the_factors_are_each_one_row():
    """v0.84: a run of single values is one row -- the inputs, the two members' material, their
    thicknesses, and the factors of equation (88), each a `group` the display joins with a semicolon.

    Every one of them carries `keep`, because every one is an operand of some step and would otherwise
    be absorbed into that step's substituted formula and vanish from the page (the rule show-calc has
    always applied to an intermediate step's operands).
    """
    record, _ = _record(_source())
    v = record["vars"]
    groups = {}
    for name, entry in v.items():
        if entry.get("group"):
            groups.setdefault(entry["group"], []).append(name)
    assert groups["input"] == ["d", "n_tot", "f_u_k"]
    # what each piece is made of, and -- a block of its own since the headings came in -- how thick it is
    assert groups["material"] == ["rho_k_1", "alpha_1", "rho_k_2", "alpha_2"]
    assert groups["thickness"] == ["t_1", "t_2"]
    assert groups["factors"][:4] == ["k_beta", "p", "p_k_beta", "k_red"]
    assert groups["factors"][-3:] == ["k_alpha", "eta_w", "eta_t"]
    for name in groups["input"] + groups["factors"] + ["rho_k_1", "t_1", "rho_k_2", "t_2"]:
        assert v[name].get("keep"), "%s is an operand and would be absorbed without `keep`" % name
    # the second member names itself inside the row it joins, so one line says both -- by what it is as
    # well as by its number, which is the form the Figur 45 plates are captioned with
    assert v["rho_k_1"]["group_label"] == "Bauteil 1 \u2014 Seitenholz"
    assert v["rho_k_2"]["group_label"] == "Bauteil 2 \u2014 Mittelholz"
    assert v["t_1"]["group_label"] == "Bauteil 1 \u2014 Seitenholz"
    # alpha is NOT kept: it shows where it acts, inside f_h,alpha,k and inside k_red
    assert not v["alpha_1"].get("keep")


def test_the_dowel_layout_comes_before_the_dowels():
    """v0.84, the engineer: «l'encadré Disposition des broches doit se trouver avant l'encadré Broche
    (renommer en Broches)». The pattern is drawn first and the count is read off it, so the box that
    settles the count stands before the box that spends it.
    """
    tab = _tab()
    boxes = [tab.form.itemAt(i).widget() for i in range(tab.form.count())]
    order = [b for b in boxes if b in (tab.layout_group, tab.dowel_group)]
    assert order == [tab.layout_group, tab.dowel_group], "the layout box comes after the dowels box"
    # and the box has a name in all three languages, being plural since v0.84
    from tools import connectors_tab as ct
    for lang in ("fr", "de", "en"):
        assert ct.STRINGS[lang]["cn_box_dowel"], "the dowels box has no name in %s" % lang


def test_the_dowels_box_takes_its_count_from_the_layout():
    """v0.84: n_tot shows the count of ticked markers and is read-only while it follows it.

    `draft()` has read n_tot off the drawing since v0.74 while the field showed whatever was loaded, so
    the form said one thing and the calculation used another -- and a field one may type into that is
    then ignored is worse than a field one may not. The override is the one way the two ever differ.
    """
    tab = _tab()
    _load_calculated(tab)
    assert tab.n_tot_box.isReadOnly(), "n_tot is typed into while it follows the drawing"
    assert not tab.n_tot_override.isChecked()
    assert tab.n_tot_box.value() == len(tab.draft()["fasteners"]), "the count shown is not the count ticked"
    tab.n_tot_override.setChecked(True)
    assert not tab.n_tot_box.isReadOnly(), "the override does not free the field"


def test_hovering_a_member_rings_its_piece_on_the_section():
    """v0.84, the engineer: hovering «Pièce 1» or «Pièce 2» lights that member on the section as well as
    on the pattern. Which piece that is, is the assembly's own answer and not a rule about left and
    right -- a Seitenholz of a zweischnittig joint is **two** pieces, and a Stahl-Holz joint enters one
    member, so every timber piece is its.
    """
    from domains import connector_svg
    # (kind, t, base, sub): the parts connector_svg.section lays out, as it numbers their members
    two_sided = [("timber", 50, 0, "1"), ("timber", 100, 0, "2"), ("timber", 50, 0, "1")]
    assert connector_svg.highlighted_pieces("Holz-Holz zweischnittig", two_sided, 1) == {0, 2}
    assert connector_svg.highlighted_pieces("Holz-Holz zweischnittig", two_sided, 2) == {1}
    one_sided = [("timber", 50, 0, "1"), ("timber", 100, 0, "2")]
    assert connector_svg.highlighted_pieces("Holz-Holz einschnittig", one_sided, 1) == {0}
    assert connector_svg.highlighted_pieces("Holz-Holz einschnittig", one_sided, 2) == {1}
    # a steel joint enters one member: every timber piece is that member's, the plates none of it
    steel = [("timber", 50, 0, "1"), ("plate", 12, 0, None), ("timber", 100, 0, "1")]
    assert connector_svg.highlighted_pieces("Stahl-Holz, Schlitzbleche", steel, 1) == {0, 2}
    assert connector_svg.highlighted_pieces("Stahl-Holz, Schlitzbleche", steel, 2) == set()
    # nothing hovered rings nothing
    assert connector_svg.highlighted_pieces("Holz-Holz zweischnittig", two_sided, None) == set()


# --- the level-3 layout, after the Bemessungsbeispiele (v0.84) ----------------
# The engineer: «le level 3 est trop brouillon», copy p. 291 of the Bemessungsbeispiele zur SIA 265 --
# a line naming what is being calculated before each run of formulas, and the pieces named on their own.

def _heading_member(grade="C24", **kwargs):
    entry = {"rho_k": 385, "species": "Nadelholz", "alpha": 0, "t": 100, "predrilled": True,
             "n": 4, "a_1": 100, "moisture_class": 1, "grade": grade}
    entry.update(kwargs)
    return entry


# One of each assembly the norm gives a k_beta row for, so a heading is checked on every shape the
# record takes: two timber members, one timber member with slots, and one between outer plates.
HEADING_CASES = {
    "Holz-Holz zweischnittig": [_heading_member(t=70), _heading_member(t=100)],
    "Holz-Holz einschnittig": [_heading_member(t=70, n=2), _heading_member(t=100, n=2)],
    "Stahl-Holz, Schlitzbleche": [_heading_member(alpha=90, t=200, n=3)],
    "Stahl-Holz, Bleche aussen": [_heading_member(t=120, n=3)],
}


def _heading_record(assembly):
    inputs = {"assembly": assembly, "d": 12.0, "f_u_k": 510.0, "n_tot": 8,
              "impact": False, "truss": False,
              "members": copy.deepcopy(HEADING_CASES[assembly])}
    if assembly.startswith("Stahl-Holz"):
        inputs["steel"] = {"plates": 2, "slot": 12.0 if "Schlitzbleche" in assembly else 0.0,
                           "ratio": 0.5, "grade": "S235"}
    return dowel.record("X", dowel.analyse(inputs), inputs["members"])


def _headings(record, level=3):
    """The headings `show-calc` would print, and the ones it would drop -- its own row rule, restated.

    A heading is printed where its var's first row is printed, so it follows both of the rules that
    decide whether that row exists at all: the var's level, and the one that absorbs an intermediate
    step's operand into the substituted formula that already shows it.
    """
    results, steps = record["results"], record["steps"]
    shown = {s["result"]: s for s in steps if line_levels.level("connector", s["result"], "step", own=s.get("level")) <= level}
    produced = {s["result"] for s in steps}
    absorbed = set()
    for s in shown.values():
        if s["result"] not in results and not s.get("bold"):
            absorbed.update(s["uses"])
    printed, dropped, last_group = [], [], None
    for name, v in record["vars"].items():
        if name in shown:
            row, last_group = True, None
        elif name in produced:
            row = line_levels.level("connector", name, own=v.get("level")) <= level
            last_group = None if row else last_group
        elif (name not in absorbed or v.get("keep")) and line_levels.level("connector", name, own=v.get("level")) <= level:
            group = v.get("group")
            row, last_group = not (group is not None and group == last_group), group
        else:
            row = False
        if v.get("heading"):
            (printed if row else dropped).append("%s (on %s)" % (v["heading"], name))
    return printed, dropped


def test_every_heading_a_dowel_record_carries_is_printed():
    """v0.84: a run of formulas is announced by a line of its own, on every assembly the norm covers.

    ⚠️ The trap this holds is the mechanism's own. A heading is printed where its var's first row is
    printed, so one hung on a var the level hides -- or on a var absorbed into an intermediate step's
    substituted formula -- is dropped without a word and its run goes unnamed. It happened three times
    while this was written (`n_1`, `eta_(w,"Steif")`, and the first place tried for the reduction
    factor), each time leaving a block of formulas with nothing over it.
    """
    for assembly in HEADING_CASES:
        record = _heading_record(assembly)
        printed, dropped = _headings(record)
        assert not dropped, "%s: headings that would never reach the page: %s" % (assembly, dropped)
        # the blocks the engineer named, in the book's own order
        assert printed[0].startswith("Charakteristische Lochleibungsfestigkeiten für C24"), printed
        assert any(h.startswith("Holzdicken") for h in printed), printed
        assert any(h.startswith("Erforderliche Holzdicken und Hilfswert") for h in printed), printed
        assert any(h.startswith("Bemessungswert des Tragwiderstands") for h in printed), printed
        if assembly.startswith("Holz-Holz"):
            assert any(h.startswith("Verhältnis der Lochleibungsfestigkeiten") for h in printed), printed
            # the piece each run is about, named as the Figur 45 plates caption it
            assert any(h.startswith("Bauteil 1") for h in printed), printed
            assert any(h.startswith("Bauteil 2") for h in printed), printed


def test_a_piece_is_named_by_its_role_only_where_that_tells_the_two_apart():
    """«Bauteil 1 — Seitenholz» where the roles differ, «Bauteil 1» where both pieces are Seitenhölzer.

    A einschnittig joint has two of them (Tabelle 45), so the word would name neither and the drawing's
    own number is all there is to say. Both forms go through the glossary -- the second is a term, the
    first the template the Figur 45 captions are composed with.
    """
    def labels(assembly):
        record = _heading_record(assembly)
        return [v.get("group_label") for v in record["vars"].values() if v.get("group_label")]

    two = labels("Holz-Holz zweischnittig")
    assert "Bauteil 1 — Seitenholz" in two and "Bauteil 2 — Mittelholz" in two, two
    one = labels("Holz-Holz einschnittig")
    assert "Bauteil 1" in one and "Bauteil 2" in one, one
    assert not any("—" in label for label in one), "both pieces are Seitenhölzer: the role says nothing"


def test_every_heading_is_a_word_of_the_glossary():
    """A heading is printed text, so it follows the report's language like every other sentence the data
    carries (docs/typst/language.md §4bis): each is a term of `calc/i18n/strings.json`, or the template it was
    composed from -- «... für C24», whose grade is a designation and passes through."""
    from i18n import strings
    for assembly in HEADING_CASES:
        record = _heading_record(assembly)
        for name, v in record["vars"].items():
            head = v.get("heading")
            if not head:
                continue
            for lang in ("fr", "en"):
                assert strings.translate(head, lang) != head, \
                    "%s: «%s» is printed as it stands in %s" % (name, head, lang)


def test_the_headings_reach_the_page():
    """The words of the connector, printed by its domain as Woodcore writes it out (spec 2026-10-21-commandes-typst-refonte, REQ-017): the titles of its tables and its figures' captions.

    It exports the project's connectors into this run's own copy of the data first, because nothing
    else in the suite writes `data/` -- the committed example carries whatever export it was frozen
    with, and compiling against that would be testing the record of another version.
    """
    import re
    import subprocess
    import conftest
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    if not connector.source_paths(SOURCES):
        raise Skip("no connector sources in connectors/")
    connector.export(SOURCES, DATA)
    exported = json.loads((DATA / "connectors.json").read_text(encoding="utf-8"))["connectors"]
    cid = next((k for k, v in exported.items() if v.get("calculated")), None)
    if cid is None:
        raise Skip("no calculated connector in the project")
    d = conftest.probe_dir("connector_headings")
    probe = d / "probe.typ"
    _written_out(d, cid)
    probe.write_text(PROBE_PREAMBLE + '#calc-defaults(level: 3, scope: "document")\n#include "connector.typ"\n', encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe),
                          str(d / "probe.pdf")], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    from pypdf import PdfReader
    raw = "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
    text = re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", raw))
    # its labels follow the domain's presets, «block» (Q-014): the titles of its tables are printed, and its figures' captions
    for head in ("Hilfswert", "Minimale Abstände", "Anordnung der Verbindungsmittel", "Schnitt durch die Verbindung"):
        assert head in text, "the page carries no «%s»: %s" % (head, text[:1200])
    # and the two Figur 45 plates the engineer asked to keep are still under it
    assert "Bauteil 1 – Seitenholz" in text and "Bauteil 2 – Mittelholz" in text


def test_the_record_carries_no_checks():
    """There is no design force here: the report states F_d and the verification itself, with #verify reading var-of("connector", id, "R_d")."""
    record, _ = _record(_source())
    assert record["checks"] == []
    # v0.84: R_d is computed first and R_d,Verb from it -- equation (88) without n_tot is the
    # resistance of one fastener, which is what an engineer reads off the page.
    assert record["results"] == ["R_d", "R_d_Verb"]


def test_a_truss_node_gets_a_second_answer():
    source = _source()
    source["conditions"] = {"seismic": False, "truss": True}
    record, _ = _record(source)
    assert "R_d_Verb_Fachwerk" in record["results"]
    assert record["vars"]["R_d_Verb_Fachwerk"]["value"] < record["vars"]["R_d_Verb"]["value"]


# --- the export -------------------------------------------------------------------

def test_the_project_exports_and_validates():
    """Every source under connectors/, built and validated against the schema and the business rules."""
    if not connector.source_paths(SOURCES):
        raise Skip("no connector sources in connectors/")
    data, images, warnings = connector.prepare(SOURCES, connector.known_positions(DATA), schema.read_sources(conftest.PROJECT.details_dir))
    assert data["schema_version"] == connector.LEVELS_EXPORT_VERSION   # 3.3 since v0.120: no line carries a level (UI-002)
    assert data["connectors"], "the sources produced no records"
    for cid, record in data["connectors"].items():
        assert record["source"] == "connectors/%s.json" % cid
    # every drawing named in a record is one the export actually produced
    for record in data["connectors"].values():
        for kind, by_language in record.get("figures", {}).items():
            for name in by_language.values():
                assert name in images, "a record names %r, which was not drawn" % name


def test_a_connection_names_no_connector():
    """v0.76: a polar moment distributes forces over points and has no use for what fastens them, so the link v0.33 made -- and which this test held through the move out of Excel -- is gone. The connections export without the connectors, and their records carry no `connector`."""
    from domains import connection
    details = schema.read_sources(conftest.PROJECT.details_dir)
    records, _figures, warnings = connection.prepare(conftest.PROJECT.connections_dir, details, connector.known_positions(DATA))
    assert not [w for w in warnings if "connector " in w.lower() and "marker" not in w.lower()], warnings
    for cid, record in records["connections"].items():
        assert "connector" not in record, cid


def test_two_ids_differing_only_in_case_are_refused():
    """The file system does not tell them apart, so neither may the export."""
    directory = tmpdir("connectors-case")
    for cid in ("SD_50", "sd_50"):
        source = _source(id=cid)
        (directory / ("%s.json" % cid)).write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
    if len(list(directory.glob("*.json"))) < 2:
        raise conftest.OtherSystem("this file system does not keep two names differing only in case")   # Windows' and macOS' own: nothing is missing from the machine
    assert "case" in _raised(connector.prepare, directory, {})


# --- schema 1.1: the identity, the override, the plate thickness that went ------

def test_a_grade_beside_a_position_overrides_it_and_stays():
    """The engineer's own rule: a value written over a reference **stays** written over through the next «Importer Excel», and the line still says what the position holds so it can be taken back."""
    source = _source()
    for member in source["members"]:
        member["material"] = {"grade": "GL32h"}                        # T001 says C24
    record, warnings = _record(source, POSITIONS, _detail(("T001", "T001")))
    assert record["members"][0]["grade"] == "GL32h"
    assert record["vars"]["rho_k_1"]["value"] == 440, "the override did not reach the density"
    assert "T001" in record["members"][0]["material_from"], \
        "an overridden field must still name the position, or nothing can offer to take the override back"
    assert "C24" in record["members"][0]["material_from"], \
        "and it must say what that position holds, or the orange line says nothing"


def test_material_kind_tells_the_two_shapes_apart():
    """Two since schema 2.0, where there were three: the ELEMENT is the position reference now, so
    `material` says only whether the class read from it is overridden (docs/domain/connectors.md §3.3nonies)."""
    assert connector.material_kind(None) == "element"
    assert connector.material_kind({"grade": "C24"}) == "override"
    assert connector.material_kind({"nothing": 1}) == "invalid"
    assert connector.material_kind({"position": "T001"}) == "invalid", (
        "naming a position here would be a second place for what the element already says")


def test_a_members_plate_thickness_is_refused_the_connectors_plate_carries_it():
    """It was in the source from v0.68 and nothing ever read it. The plate's bearing check (SIA 263 Tabelle 16, schema 2.2) reads the connector's one `plate.t`, so a member's `plates.thickness` stays refused, naming where the thickness goes (spec 2026-10-12-audit-issues-47-48-49, D-14)."""
    source = _source(assembly="Stahl-Holz, Schlitzbleche")
    source["members"][0]["plates"] = {
        "arrangement": "schlitzblech", "count": 1,
        "slot": {"value": 8, "unit": "mm"}, "thickness": {"value": 8, "unit": "mm"}, "ratio": 0.5,
    }
    assert "plate.t" in _raised(connector.check_source, source, "SD_99.json")


def test_a_1_0_source_is_read_as_1_1_and_sent_to_the_migration():
    """A 1.0 source carries its own drawing, as a 1.1 does, and both are converted once by migrate_to_schemas.py. `upgrade_source` relabelled a 1.0 as **2.0** without converting its geometry, so a real 1.0 file slipped past the migration's refusal and fell on «missing required field 'label'» (periodic audit 260916, AUD-7-120) -- this test used to build a 1.0 in the 2.0 shape, which never existed. The collapse of its per-member classes stays: the worst is what its own calculation used, and it is what the migration copies."""
    old = _source()
    old["schema_version"] = "1.0"
    old.pop("moisture_class")
    old.pop("name", None)
    old.pop("variant", None)
    old["members"][0]["material"] = {"grade": "GL24h", "moisture_class": 1}
    old["members"][1]["material"] = {"grade": "GL24h", "moisture_class": 3}
    old["members"][0]["plates"] = None
    fresh = connector.upgrade_source(old)
    assert fresh["schema_version"] == "1.1", fresh["schema_version"]
    assert fresh["moisture_class"] == 3, "the worst class is what the 1.0 calculation used"
    assert "moisture_class" not in fresh["members"][0]["material"]
    message = _raised(connector.check_source, fresh, "SD_99.json")
    assert "0.119" in message and "before v0.74" in message, message


def test_the_identity_travels_to_the_export():
    source = _source(name="Velo Unterstand", variant="8mm")
    record, _warnings = _record(source, POSITIONS)
    assert record["name"] == "Velo Unterstand" and record["variant"] == "8mm"


def test_n_quer_is_the_classeurs_own_roundup():
    """ROUNDUP(n_tot / n) -- 'Stabdübel (Holz-Holz)'!C31. Nothing in equation (88) reads it; it is the count across the grain the rows imply, and the engineer checks the drawing against it."""
    source = _source()                       # n_tot = 4, n = 2 per member
    record, _warnings = _record(source, POSITIONS)
    assert record["vars"]["n_quer_1"]["value"] == 2
    source["n_tot"] = {"value": 5, "override": True}
    record, _warnings = _record(source, POSITIONS)
    assert record["vars"]["n_quer_1"]["value"] == 3, "5 over 2 rows is 3 across, rounded up"


# --- the form the engineer types into (v0.70) -----------------------------------

def _tab():
    """The window's «Connecteurs» tab, built once off-screen. A test run must never open a window."""
    import os
    import sys as _sys
    path = str(ROOT / "calc" / "tools")
    if path not in _sys.path:
        _sys.path.insert(0, path)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    import woodcore_gui
    QApplication.instance() or QApplication([])
    global _window
    try:
        _window
    except NameError:
        _window = woodcore_gui.MainWindow()
    tab = next(t for t in _window.tabs if type(t).__name__ == "ConnectorsTab")
    # ⚠️ Left dirty by whatever ran before, `new()` and `load()` call `confirm_leave()`, which opens a
    # MODAL -- and a modal off-screen never comes back: the run hangs with no output at all. Every test
    # here starts from a tab with nothing unsaved, which is also the state a reader assumes it is in.
    tab.dirty = False
    return tab


def test_the_id_is_composed_of_the_name_and_the_variant():
    """And an accent is decomposed rather than dropped: «Élément» gives «Element», not «lment», which is what an engineer writing French would otherwise be handed."""
    from connectors_tab import slug_id
    assert slug_id("Velo Unterstand", "8mm") == "Velo_Unterstand-8mm"
    assert slug_id("Élément Café", "V2") == "Element_Cafe-V2"
    assert slug_id("Träger Süd", "") == "Trager_Sud"
    assert slug_id("", "") == ""
    import re
    from domains.connector import ID_PATTERN
    for name, variant in (("Halle Nord", "12mm"), ("Élément", ""), ("1 Halle", "V1")):
        made = slug_id(name, variant)
        assert ID_PATTERN.match(made), "%r is not a usable id" % made


def test_an_id_written_over_stays_written_over():
    tab = _tab()
    tab.new()
    tab.name_edit.setText("Halle Nord")
    assert tab.id_edit.text() == "Halle_Nord", "a name must recompose the id «Nouveau» handed out"
    tab.id_edit.setText("SD_TEST")
    tab.name_edit.setText("Halle Sud")
    assert tab.id_edit.text() == "SD_TEST", "an id typed by hand is the engineer's and must not be recomposed"


def test_every_assembly_builds_its_form_and_calculates():
    """The four boxes are rebuilt per assembly, so each one has to be walked: a form that fails to build is a tab that opens empty."""
    tab = _tab()
    tab.new()
    for name in dowel.ASSEMBLIES:
        tab.assembly_box.setCurrentIndex(tab.assembly_box.findData(name))
        expected = 2 if dowel.ASSEMBLIES[name]["family"] == "timber-timber" else 1
        assert len(tab.member_fields) == expected, "%s: %d member column(s)" % (name, len(tab.member_fields))
        assert tab.record is not None, "%s does not calculate: %s" % (name, tab.reason)


def _load_calculated(tab, following=False):
    """Opens the first saved connector that calculates -- and, with `following`, one whose members follow a position -- and returns its id. The tests below read a calculated connector's form; which one is the project's to say -- they named `SD_02` until the engineer renamed it `VU-SD-10` (v0.77), and five of them then failed on a file that had simply changed name."""
    for cid in tab._taken():
        tab.dirty = False
        tab.load(cid)
        if tab.record is None:
            continue
        if following and not any(tab.element_position(w["element"].currentData() or "") for w in tab.member_fields):
            continue
        return cid
    raise Skip("no saved connector calculates" + (" with a member following a position" if following else ""))


def test_a_new_connector_calculates():
    """«Nouveau» opening on a refusal is «Nouveau» that looks broken. It states moisture class 1, the classeur's own default."""
    tab = _tab()
    tab.new()
    assert tab.record is not None, tab.reason
    assert tab.draft()["moisture_class"] == 1


def test_the_results_carry_real_subscripts_and_the_minimum_spacings():
    """Two of the engineer's own points: `R_d` written flat is not what the norm calls it, and the table equation (88) is conditional on was in the report and nowhere on screen."""
    tab = _tab()
    _load_calculated(tab)
    html = tab.results.text()
    assert "R<sub>d,Verb</sub>" in html and "k<sub>β</sub>" in html
    assert "<sub>" in html and html.count("<sub>") >= 8
    assert tab.t("cn_min_spacings") in html, "the minimum spacings are not under the numbers"
    # v0.84: K_ser and K_ser,Verb are two rows of the results, which is what the Verschiebungsmodul
    # table showed; the table went with the one in the report, its numbers written out as formulas.
    assert "K<sub>ser,Verb</sub>" in html and "K_ser_Verb" not in html
    assert "$" not in html, "a symbol between dollars reached the window unset"


def test_hovering_a_box_lights_the_results_it_produces():
    tab = _tab()
    _load_calculated(tab)
    import theme  # the lit ground and ink are the scheme's since v0.90 (theme.json: lit, lit-ink)
    tab.set_hot(None)
    assert theme.colour("lit") not in tab.results.text()
    tab.set_hot(tab.dowel_group)
    html = tab.results.text()
    assert theme.colour("lit") in html, "the Stabdübel box lights k_red and M_u,k"
    # v0.84, the engineer: «orange clair sur blanc ne se lit pas bien» -- a lit row sets its ink too,
    # or the palette's own text is near-white on it in a dark theme and pale on it in a light one.
    assert theme.colour("lit-ink") in html, "a lit result leaves its ink to the palette"
    tab.set_hot(None)


def test_every_row_of_the_form_carries_a_unit():
    """«–» where the quantity has none, so that a missing unit is a decision somebody took."""
    tab = _tab()
    ids = tab._taken()
    if not ids:
        raise Skip("no connector saved in this project")
    tab.load(ids[0])     # the project's first connector, whatever the engineer has named it (SD_01 was renamed)
    from PySide6.QtWidgets import QLabel
    blanks = [w for w in tab.findChildren(QLabel)
              if w.minimumWidth() == 52 and not w.text().strip()]
    assert not blanks, "%d field(s) carry no unit at all" % len(blanks)


# --- v0.75: what the audit of the five plans found ----------------------------------------

def test_outer_plates_show_the_engineers_own_list_and_a_steel_joint_no_ignored_t():
    """«Bleche aussen» is d · Feuchteklasse · Festigkeitsklasse · α · b · t₁ · k_β, the engineer's list; until v0.75 it also showed the slot, the plate count, t₂, t₁/t₂, k_β,₂ and p·k_β, and every Stahl-Holz form showed a member t that draft() never read (b is what it saves)."""
    tab = _tab()
    tab.new()
    tab.assembly_box.setCurrentIndex(tab.assembly_box.findData("Stahl-Holz, Bleche aussen"))
    hidden = (tab.plate_fields["slot"], tab.plate_fields["count"], tab.plate_fields["ratio"],
              tab.computed["t_2"], tab.computed["k_beta_2"], tab.computed["p_k_beta"],
              tab.member_fields[0]["t"])
    for widget in hidden:
        assert widget.row_cell.isHidden(), "a field outer plates do not read is still shown"
    for widget in (tab.plate_fields["b"], tab.computed["t_1"], tab.computed["k_beta"], tab.diameter_box):
        assert not widget.row_cell.isHidden()
    assert tab.record is not None, tab.reason
    tab.assembly_box.setCurrentIndex(tab.assembly_box.findData("Stahl-Holz, Schlitzbleche"))
    assert not tab.plate_fields["slot"].row_cell.isHidden(), "slotted plates keep their slot"
    assert tab.member_fields[0]["t"].row_cell.isHidden()
    tab.assembly_box.setCurrentIndex(tab.assembly_box.findData("Holz-Holz zweischnittig"))
    assert not tab.member_fields[0]["t"].row_cell.isHidden(), "a timber joint's member t is its thickness"
    tab.dirty = False


def test_what_outer_plates_hide_does_not_change_their_resistance():
    """Hiding a field is only honest if nothing reads it: the slot, the plate count and t₁/t₂ moved for outer plates must leave R_d where it was."""
    source = _source(assembly="Stahl-Holz, Bleche aussen")
    source["members"][0]["plates"] = {"arrangement": "laschen", "count": 1, "slot": {"value": 8, "unit": "mm"}, "ratio": 0.5}
    source["members"][1]["role"] = "steel"
    for member in source["members"]:
        member["material"] = {"grade": "GL24h"}
    first, _w = _record(source)
    if not first["calculated"]:
        raise Skip("the fixture does not calculate as outer plates: %s" % first["reason"])
    for slot, count, ratio in ((2, 1, 0.2), (12, 3, 1.5)):
        source["members"][0]["plates"] = {"arrangement": "laschen", "count": count, "slot": {"value": slot, "unit": "mm"}, "ratio": ratio}
        again, _w = _record(source)
        assert again["vars"]["R_d"]["value"] == first["vars"]["R_d"]["value"], (slot, count, ratio)


def test_taking_a_grade_back_follows_the_element_again():
    """The v0.74 regression: «Reprendre» read `widgets["position"]`, which left with the member form, and raised a KeyError the moment it was clicked."""
    import cards
    tab = _tab()
    _load_calculated(tab)
    widgets = tab.member_fields[0]
    widgets["overridden"] = True
    tab.take_back(0)
    assert widgets["overridden"] is False
    pid = tab.element_position(widgets["element"].currentData() or "")
    held = (connector.known_positions(DATA).get(pid) or {}).get("strength_class")
    if held:
        assert widgets["grade"].currentData() == held
        assert widgets["grade"].currentText() == cards.followed(held, pid), "a grade that follows says where from in its own field"
        assert widgets["note_row"].isHidden(), "and no line under it"
    tab.dirty = False


def test_the_moisture_class_has_its_own_take_back():
    tab = _tab()
    _load_calculated(tab, following=True)   # «Reprendre» takes back what the members' positions hold
    tab.moisture_box.setCurrentIndex(tab.moisture_box.findData(3))
    tab.fill_material_notes()
    assert not tab.moisture_back.isHidden(), "a class written over offers «Reprendre»"
    tab.take_back_moisture()
    assert tab.moisture_box.currentData() is None and tab.moisture_back.isHidden()
    tab.dirty = False


def test_a_hovered_marker_row_is_lit_on_the_pattern():
    tab = _tab()
    _load_calculated(tab)
    assert tab.table.rowCount() > 0
    tab.on_marker_hover(0)
    marker = tab.table.item(0, 0).data(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.ItemDataRole.UserRole)
    assert tab.marked() == ("connectors", marker)
    tab.on_marker_hover(-1)
    assert tab.marked() != ("connectors", marker) or tab.table.selectedIndexes()
    tab.dirty = False


def test_a_dowel_too_thin_to_see_is_drawn_larger_and_the_pattern_says_so():
    from domains import connector_svg
    thin = connector_svg.pattern_of(_source(diameter={"value": 1, "unit": "mm"}), DETAIL, lang="fr")
    thick = connector_svg.pattern_of(_source(diameter={"value": 12, "unit": "mm"}), DETAIL, lang="fr")
    assert "Ø 1 mm" in thin and "Agrandi" in thin, "the floor bit and nothing says so"
    assert "Ø 12 mm" not in thick
    import re
    radii = [float(r) for r in re.findall(rf'<circle cx="[^"]*" cy="[^"]*" r="([^"]*)" fill="{re.escape(connector_svg.FASTENER_FILL)}"', thick)]
    assert radii and all(abs(r - 6.0) < 1e-6 for r in radii), radii


def test_the_advice_names_an_element_not_a_list_of_positions():
    source = _source()
    source["members"][0]["material"] = None
    _record_, warnings = _record(source, POSITIONS, _detail(("T001", "GONE")))
    source["members"][1]["material"] = None
    _record_, warnings = _record(source, POSITIONS, _detail(("T001", "GONE")))
    said = " ".join(warnings)
    assert "Element des Schemas" in said and "Position aus der Liste" not in said, said


# --- a value that follows says so in its field; a line under it only when written over --------

from norms import sia265  # noqa: E402 -- the grades a member's combo offers

OVERRIDE = "#b35c00"      # connectors_tab.OVERRIDE_COLOR: every line under a field is orange, or there is none

def test_the_grade_and_the_moisture_class_say_where_they_come_from_in_their_own_field():
    """The engineer's rule: «C24, repris de T001» and «2, repris de S001, T001» in the field, no line under it -- a line, in orange, only when the value is written over."""
    import cards
    tab = _tab()
    ids = tab._taken()
    if not ids:
        raise Skip("no connector saved in this project")
    tab.load(ids[0])
    positions = connector.known_positions(DATA)
    widgets = tab.member_fields[0]
    pid = tab.element_position(widgets["element"].currentData() or "")
    if pid not in positions or not positions[pid].get("strength_class"):
        raise Skip("the first member names no position with a strength class")
    tab.moisture_box.setCurrentIndex(0)
    widgets["overridden"] = False
    tab.fill_material_notes()
    held = positions[pid]["strength_class"]
    assert widgets["grade"].currentText() == cards.followed(held, pid)
    assert widgets["note_row"].isHidden()
    if tab.moisture_box.itemText(0) != "—":
        assert ", " in tab.moisture_box.currentText() and tab.moisture_line.isHidden()
    other = next(g for g in sia265.grades() if g != held)
    widgets["grade"].setCurrentIndex(widgets["grade"].findData(other))
    assert widgets["overridden"] and widgets["grade"].currentText() == other
    assert not widgets["note_row"].isHidden() and OVERRIDE in widgets["grade_note"].styleSheet()
    assert tab.draft()["members"][0]["material"] == {"grade": other}, "the override reaches the source by the item's data, never its text"
    tab.moisture_box.setCurrentIndex(tab.moisture_box.findData(3))
    tab.fill_material_notes()
    if tab.moisture_box.itemText(0) != "—":
        assert not tab.moisture_line.isHidden() and OVERRIDE in tab.moisture_note.styleSheet()
    tab.dirty = False
    tab.load(ids[0])
    tab.dirty = False


def test_a_member_shows_its_material_and_density_without_a_calculation():
    """«Essence» is the position's material (Positionen.xlsx) and ρ_k SIA 265's 5 % fractile -- neither waits for the resistance to be calculable. ⚠️ No mean unit weight (SIA 261 Tabelle 28): the engineer, «INUTILE pour les calculs» (v0.77)."""
    tab = _tab()
    ids = tab._taken()
    if not ids:
        raise Skip("no connector saved in this project")
    tab.load(ids[0])
    tab.record = None
    tab.fill_computed()
    tab.fill_member_values()
    positions = connector.known_positions(DATA)
    widgets = tab.member_fields[0]
    pid = tab.element_position(widgets["element"].currentData() or "")
    material = (positions.get(pid) or {}).get("material") or "—"
    grade = widgets["grade"].currentData()
    assert tab.computed["species_1"].text() == material
    assert tab.computed["rho_k_1"].text() == "%g" % sia265.rho_k(grade)
    assert "gamma_mean_1" not in tab.computed, "the mean unit weight is back in the form"
    tab.dirty = False


def test_p_and_k_beta_are_shown_before_a_marker_is_ticked():
    """p is 1 for Holz-Holz einschnittig and 2 for zweischnittig, and k_β is Tabelle 45's -- neither depends on a marker, so neither waits for one (the engineer: «p vaut 1 ... et 2 ...», v0.77). Never exported: the record stays uncalculated."""
    tab = _tab()
    ids = tab._taken()
    if not ids:
        raise Skip("no connector saved in this project")
    tab.load(ids[0])
    positions = connector.known_positions(DATA)
    for assembly, planes in (("Holz-Holz einschnittig", 1), ("Holz-Holz zweischnittig", 2)):
        source = tab.draft()
        source["assembly"] = assembly
        source["fasteners"] = []
        preview = connector.preview(source, positions, tab.detail())
        assert preview.get("p") == planes, (assembly, preview)
        tab.record, tab.preview_values = None, preview
        tab.fill_computed()
        assert tab.computed["p"].text() == str(planes)
        if "k_beta" in preview:
            assert tab.computed["k_beta"].text() not in ("", "—"), "k_β is known and not shown"
        record, _warnings = connector.build_record(source, positions, tab.detail())
        assert not record["calculated"] and not record["vars"], "a preview must never reach the export"
    tab.dirty = False
    tab.load(ids[0])
    tab.dirty = False


def test_a_dowel_carries_its_steel_and_a_timber_joint_no_plate():
    """The dowel's steel fills f_u,k from SIA 263 Tabelle 1 and stays a choice: a value typed over it sets the grade back to «—» (spec 2026-10-12-audit-issues-47-48-49, D-06, D-20). A Holz-Holz joint has no plate (the engineer, v0.77)."""
    tab = _tab()
    ids = tab._taken()
    if not ids:
        raise Skip("no connector saved in this project")
    tab.load(ids[0])
    from norms import sn_en_14592
    note = tab.f_u_k_note.text()
    assert "SIA 263" in note and "235" in note and "G.9" in note
    tab.dowel_steel_box.setCurrentIndex(tab.dowel_steel_box.findData("S235"))
    assert tab.f_u_k_box.value() == sn_en_14592.f_u_k("S235") and tab.draft()["dowel"]["steel"] == "S235"
    tab.f_u_k_box.setValue(400)
    assert tab.dowel_steel_box.currentData() == "" and tab.draft()["dowel"] == {"steel": "", "f_u_k": {"value": 400, "unit": "N/mm²"}}
    timber = dowel.ASSEMBLIES.get(tab.assembly_box.currentData() or "", {}).get("family") == "timber-timber"
    if timber:
        assert tab.steel_box.parentWidget().isHidden(), "a Holz-Holz joint shows a plate grade"
        assert tab.draft()["steel"] == ""
    new = connector.new_source("X_01")
    assert new["dowel"] == {"steel": "S355", "f_u_k": {"value": 510, "unit": "N/mm²"}} and new["steel"] == ""
    assert connector.dowel_steel(new) == "S355" and connector.dowel_steel(dict(new, dowel={"steel": "S355", "f_u_k": {"value": 500, "unit": "N/mm²"}})) == ""
    tab.dirty = False


def test_figur_45_is_drawn_for_each_thickness_and_set_under_its_table():
    """v0.77, the engineer: level 3 of a dowel's resistance draws SIA 265 Figur 45, «toujours 2 graphiques: 1 qui relate t_1 et 1 qui relate t_2», the values written on it as «variable = valeur + unité». One file per thickness, no word in it, named on the k_beta table the report sets it under -- and the numbers stay the table's rows, so the curves are not exported twice."""
    source = _source()
    record, _warnings = _record(source, POSITIONS)
    names, files = connector.figures(source, DETAIL, POSITIONS, record)
    table = next(t for t in record["tables"] if "figures" in t)
    assert "curves" not in table and table["title"] == "Hilfswert $k_beta$"
    assert [(f["index"], f["role"]) for f in table["figures"]] == [(1, "Seitenholz"), (2, "Mittelholz")]
    # v0.84: the numbers became the formulas above the plate, so the plate is its title, its note and
    # its figures and has no grid at all -- the thickness each curve is read at is the record's own var.
    assert table["rows"] == [] and table["columns"] == []
    for figure in table["figures"]:
        svg = files[figure["file"]]
        assert figure["file"] == "connectors/SD_99-kbeta-%d.svg" % figure["index"]
        assert svg.startswith("<svg") and "mm" in svg
        t = record["vars"]["t_%d" % figure["index"]]["value"]
        # «t_1 = 70 mm» is set as three runs, the subscript its own <text>: the value is the run after it
        assert ">= %s mm<" % ("%g" % t) in svg, "the thickness read, %s mm, is not written on %s" % (t, figure["file"])
        assert "stroke-dasharray" in svg
        assert not any(word in svg for word in ("Seitenholz", "Mittelholz", "bois", "member")), "a word on a figure drawn once for three languages"
    # the second is a Mittelholz: its line is drawn dashed from the origin, and it has no lower corner to name
    assert "t_(2,1)" not in files[table["figures"][1]["file"]] and ">2,1<" not in files[table["figures"][1]["file"]]
    assert ">1,1<" in files[table["figures"][0]["file"]], "t_1,1 and k_beta1,1 are written on the Seitenholz's figure"
    # a record that carries no calculation has no curve to draw
    draft = _source(fasteners=[])
    empty, _w = _record(draft, POSITIONS)
    _names, drawn = connector.figures(draft, DETAIL, POSITIONS, empty)
    assert not [name for name in drawn if "kbeta" in name]


def test_choosing_another_connector_opens_no_window():
    """v0.77: «lorsque je passe d'un fichier connecteur à un autre, des fenêtres blanches s'ouvrent l'espace de moins d'1 s». The rows of «Géométrie et matériau» and «Stabdübel» rebuilt for the next connector were detached shown, and a shown widget with no parent is a top-level window: six of them, titled with the application's name, each time. Watched here through every Show event of a window that is not the main window; planted by taking `hide()` out of `_clear`, it fails naming six."""
    from PySide6.QtCore import QEvent, QObject
    from PySide6.QtWidgets import QApplication, QWidget
    tab = _tab()
    ids = tab._taken()
    if len(ids) < 2:
        raise Skip("fewer than two connectors saved in this project")
    window = tab.window()
    window.show()
    window.tab_widget.setCurrentWidget(tab)
    app = QApplication.instance()
    app.processEvents()

    class Watch(QObject):
        shown = []

        def eventFilter(self, obj, event):
            if (event.type() == QEvent.Type.Show and isinstance(obj, QWidget) and obj.isWindow()
                    and obj is not window and type(obj).__name__ not in ("QMenu", "QTipLabel")):
                Watch.shown.append("%s %dx%d" % (type(obj).__name__, obj.width(), obj.height()))
            return False

    watch = Watch()
    app.installEventFilter(watch)
    try:
        for cid in ids[:2] * 2:
            tab.dirty = False
            tab.on_list_change(cid)
            app.processEvents()
    finally:
        app.removeEventFilter(watch)
        tab.dirty = False
    assert Watch.shown == [], "top-level windows shown while switching connectors: %s" % Watch.shown


def test_a_point_ticked_connecteur_is_offered_under_disposition_des_broches():
    """v0.77: A12 to A15 of VU-Skizze were ticked «connecteur» and could not be chosen here. The list is the schema's markers and its points ticked «connecteur» (schema.fastener_places), a point saying what it is in its tooltip; a point left unticked is not offered."""
    from PySide6.QtCore import Qt
    tab = _tab()
    detail = _detail(connectors=[], aids=[{"id": "A1", "kind": "centre", "x": 0, "z": 0},
                                         {"id": "A2", "kind": "point", "x": -60, "z": -60, "connector": True},
                                         {"id": "A3", "kind": "point", "x": 60, "z": 60, "connector": True},
                                         {"id": "A4", "kind": "point", "x": 60, "z": -60}])
    tab.source = _source(fasteners=["A2"])
    tab.detail = lambda: detail
    try:
        tab.fill_markers()
        rows = [(tab.table.item(r, 1).text(), tab.table.item(r, 0).checkState()) for r in range(tab.table.rowCount())]
        assert rows == [("A2", Qt.CheckState.Checked), ("A3", Qt.CheckState.Unchecked)], rows
        assert tab.table.item(0, 1).toolTip() == tab.t("cn_kind_point")
        assert tab.markers_note.isHidden(), "a schema carrying points to tick is said to carry nothing"
        assert tab.ticked_markers() == ["A2"]
    finally:
        del tab.detail
        tab.dirty = False


def test_the_forms_warnings_speak_the_windows_language():
    """The warnings under the pattern were taken with the file name in front of each («connectors/VU-SD-10.json: ...»), which no template of the glossary can match, so a French window printed them in German even where the glossary had the sentence (periodic audit 260916, AUD-4-3)."""
    import copy
    tab = _tab()
    ids = tab._taken()
    if not ids:
        raise Skip("no connector saved in this project")
    tab.load(ids[0])
    source = tab.draft()
    source["n_tot"] = {"value": source["n_tot"]["value"] + 5, "override": True}
    language = tab.app.lang
    tab.draft = lambda: copy.deepcopy(source)
    tab.app.lang = "fr"
    try:
        tab.refresh()
        text = tab.message.text()
        assert "à la main" in text and "von Hand" not in text, text
    finally:
        del tab.draft
        tab.app.lang = language
        tab.dirty = False
        tab.load(ids[0])
        tab.dirty = False


def test_the_tooltip_of_an_uncovered_assembly_speaks_the_windows_language():
    """The three assemblies SIA 265 gives no k_beta for are shown disabled, their tooltip saying why -- in German whatever the window's language (periodic audit 260916, AUD-4-5)."""
    tab = _tab()
    from PySide6.QtCore import Qt
    window = tab.app
    language = window.lang
    window.lang = "fr"
    window.rebuild()
    try:
        french = next(t for t in window.tabs if type(t).__name__ == "ConnectorsTab")
        tips = [french.assembly_box.itemData(i, Qt.ItemDataRole.ToolTipRole) for i in range(french.assembly_box.count())]
        tips = [t for t in tips if t]
        assert tips and not any("gibt" in t or "behandelt" in t for t in tips), tips
    finally:
        for t in window.tabs:
            if hasattr(t, "dirty"):
                t.dirty = False
        window.lang = language
        window.rebuild()


def test_the_section_says_what_it_had_to_resize_in_the_reader_s_language():
    """The section is declared word-free, one file for the three languages -- and wrote «Ø vergrössert/verkleinert, nicht massstäblich» where the diameter could not be drawn to scale, in German in every report (periodic audit 260916, AUD-3-8). The export now draws it without the note and says in `section_scaled` what was resized; the report and the window write the note in their own language."""
    from domains import connector_svg
    from i18n import strings
    thin = _source(diameter={"value": 30, "unit": "mm"})
    for member in thin["members"]:
        member["t"] = {"value": 20, "unit": "mm"}
    thick = _source(diameter={"value": 2, "unit": "mm"})
    for member in thick["members"]:
        member["t"] = {"value": 400, "unit": "mm"}
    assert connector_svg.section_state_of(thin) == "reduced", connector_svg.section_state_of(thin)
    assert connector_svg.section_state_of(thick) == "enlarged", connector_svg.section_state_of(thick)
    assert connector_svg.section_state_of(_source()) is None
    for source, state in ((thin, "reduced"), (thick, "enlarged")):
        record, _warnings = _record(source)
        names, files = connector.figures(source, DETAIL, {}, record)
        section = files[names["section"]["de"]]
        assert "massstäblich" not in section and "Ø %s" % ("vergrössert" if state == "enlarged" else "verkleinert") not in section, "the exported section still carries a German note"
        assert record["section_scaled"] == state, record.get("section_scaled")
        note = {"enlarged": strings.text("connector.section_enlarged", "fr"), "reduced": strings.text("connector.section_reduced", "fr")}
        assert note[state] in connector_svg.section_of(source, note=note), "the window's preview does not say it"


def test_a_tab_just_built_opens_a_connector_carrying_the_assembly_the_list_opens_on():
    """A tab just built loads its first connector, and that connector may carry the very assembly the list opens on. Choosing it then changes nothing, so `on_assembly` does not run and «Broches» -- which `fill_members` builds -- is not there yet when the markers are filled.

    Until v0.118 `sync_n_tot`, which `fill_markers` ends on, read that box's check all the same: «'ConnectorsTab' object has no attribute 'n_tot_override'», and Woodcore did not start (Gian's project, 2026-10-06, and again on 0.117.0 on 2026-10-12). It had been there since v0.84 and nothing here could show it: the example project's one connector is «Holz-Holz zweischnittig», the second of the list, so choosing it built the box by accident before the markers were filled.
    """
    tab = _tab()
    import connectors_tab
    first = next(iter(dowel.ASSEMBLIES))
    assert tab.assembly_box.itemData(0) == first, "the list no longer opens on the first assembly of dowel.ASSEMBLIES: this test plants the wrong one"
    app = tab.app
    views, real = app.views, connector.read_source
    app.views = {key: value for key, value in views.items() if key != "tab_connections"}   # a tab built with no state of its own loads its first connector
    connector.read_source = lambda path: {**real(path), "assembly": first}
    fresh = None
    try:
        fresh = connectors_tab.ConnectorsTab(app)
        assert fresh.current_id is not None, "the tab opened on no connector: nothing was loaded, so nothing was tested"
        assert fresh.assembly_box.currentData() == first
        assert fresh.n_tot_box.value() == max(1, len(fresh.ticked_markers())), "«Broches» does not show the count of the markers ticked"
        assert fresh.n_tot_box.isReadOnly() and not fresh.n_tot_override.isChecked()
    finally:
        connector.read_source = real
        app.views = views
        if fresh is not None:
            fresh.dirty = False
            fresh.hide()
            fresh.deleteLater()


def _steel_source(plate=None, steel="S235"):
    source = _source(assembly="Stahl-Holz, Schlitzbleche", steel=steel)
    source["members"][0]["plates"] = {"arrangement": "schlitzblech", "count": 1, "slot": {"value": 10, "unit": "mm"}, "ratio": 0.5}
    source["members"][0]["t"] = {"value": 160, "unit": "mm"}
    source["members"][1]["role"] = "steel"
    source["members"][1]["material"] = None
    if plate is not None:
        source["plate"] = {key: ({"value": value, "unit": "mm"} if value else None) for key, value in plate.items()}
    return connector.stamp_version(source)


def test_a_steel_joint_states_its_plate_and_gets_the_plates_bearing():
    """Spec 2026-10-12-audit-issues-47-48-49, REQ-008 (D-13, D-14, D-16): a Stahl-Holz connector carrying `plate` (schema 2.2) gets F_b,Rd of SIA 263 Tabelle 16 beside R_d, p1 and p2 read off the drawing (120 mm apart both ways); one without is calculated as before and says the bearing is not checked."""
    source = _steel_source({"t": 10, "e1": 40, "e2": 30, "d0": 14})
    assert source["schema_version"] == "2.2"
    connector.check_source(source, "SD_99.json")
    record, warnings = _record(source)
    assert record["calculated"] and "F_b_Rd" in record["results"], (record.get("reason"), warnings)
    assert record["vars"]["p_1"]["value"] == 120 and record["vars"]["p_2"]["value"] == 120
    expected = dowel.plate_bearing({"d": 14, "t": 10, "e1": 40, "e2": 30, "d0": 14, "p1": 120, "p2": 120, "count": 1, "grade": "S235"})["F_b_Rd"]
    assert abs(record["vars"]["F_b_Rd"]["value"] - expected) < 1e-9
    bare = _steel_source()
    assert bare["schema_version"] == "2.0"
    record, warnings = _record(bare)
    assert record["calculated"] and "F_b_Rd" not in record["results"]
    assert any("Lochleibung der Stahlbleche nicht nachgewiesen" in w and "t, e1, e2, d0" in w for w in warnings), warnings


def test_a_plate_is_versioned_and_checked():
    """D-14: `plate` lives at schema 2.2 only; a hole smaller than the dowel is refused naming the field; a 2.0 file without one reads as before."""
    source = _steel_source({"t": 10, "e1": 40, "e2": 30, "d0": 14})
    source["schema_version"] = "2.1"
    assert "2.2" in _raised(connector.check_source, source, "SD_99.json")
    source = _steel_source({"t": 10, "e1": 40, "e2": 30, "d0": 12})
    assert "plate.d0" in _raised(connector.check_source, source, "SD_99.json")
    validation.validate_structure(_steel_source({"t": 10, "e1": None, "e2": 30, "d0": 14}), "connector-source")
