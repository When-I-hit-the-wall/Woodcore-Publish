"""The member checks Woodcore saves (calc/domains/member_check.py) and the command that computes one in the report, `#show-check-member` (lib/timber.typ).

What is held:

* **the source**: a good one passes, each malformed field is refused naming it, a kind that is not one and a kind not implemented yet each say so in words of their own, and an id that is not its file name is refused;
* **the resolution**: a value follows the position unless it is stated, and says which; a position gone is a warning and leaves the check uncalculable unless every value is stated; a missing section, strength class or moisture class, a force that is no tension, a steel position and C16 in tension (SIA 265 Tabelle 8 note 2) are `calculable: false` with a reason -- never a stop (the v0.33 rule);
* **the export**: schema-valid, reproducible to the byte, and seeded empty for a new project;
* **the report**: `#show-check-member` compiles at the three levels and prints the verdict, prints exactly what `draft_typst` prints, refuses an unknown id listing the valid ones and an uncalculable check with its reason, prints no member line with `member-level: none`, and the utilisation in percent with `unit: "%"`.

⚠️ The Typst checks are skipped where `typst` is not on the path.
"""

import copy
import json
import re
import subprocess

import conftest
from conftest import Skip

import export_all
import project
import validation
from domains import connector, member_check, unfold
from norms import sia265

TYPST_ROOT = conftest.TYPST_ROOT


def _good():
    src = member_check.new_source("ZT-99")
    src.update(position="T001", N={"value": 25, "unit": "kN"})
    return src


def _refused(src, *words):
    try:
        member_check.check_source(src, "checks/probe.json")
    except validation.ValidationError as exc:
        message = str(exc)
        for word in words:
            assert word in message, f"the refusal {message!r} does not name {word!r}"
        return message
    raise AssertionError(f"{src!r} was accepted")


POSITIONS = {
    "T001": {"strength_class": "C24", "moisture_class": 2, "section": {"type": "rec", "kind": "timber", "text": "100/200 mm", "b": 100, "h": 200}},
    "R001": {"strength_class": "GL24h", "moisture_class": 1, "section": {"type": "cir", "kind": "timber", "text": "Ø 200 mm", "d": 200}},
    "S002": {"strength_class": "S355", "moisture_class": 2, "section": {"type": "ROR", "kind": "steel", "text": "ROR 101.6×10", "dims": [101.6, 10]}},
    "W001": {"strength_class": "C24", "moisture_class": None, "section": {"type": "rec", "kind": "timber", "text": "60/160 mm", "b": 60, "h": 160}},
    "C001": {"strength_class": "C16", "moisture_class": 1, "section": {"type": "rec", "kind": "timber", "text": "60/160 mm", "b": 60, "h": 160}},
    "D001": {"strength_class": "C24", "moisture_class": 1, "section": None},
}


# --- the source -------------------------------------------------------------------

def test_a_good_source_passes():
    member_check.check_source(_good())
    assert member_check.new_source("A")["N"] == {"value": 10, "unit": "kN"}
    assert member_check.KINDS[0] == "tension" and member_check.IMPLEMENTED == ("tension", "compression", "bending", "shear", "buckling", "lateral-torsional")
    for kind in member_check.IMPLEMENTED:
        member_check.check_source(member_check.new_source("A", kind))
    assert "N" not in member_check.new_source("A", "shear")


def test_each_defect_is_refused_naming_the_field():
    cases = [
        ({"id": "-bad"}, "id"),
        ({"alpha": 120}, "alpha"),
        ({"alpha": -1}, "alpha"),
        ({"grade": "C99"}, "grade"),
        ({"section": {"type": "rec", "b": 0, "h": 200}}, "section.b"),
        ({"section": {"type": "cir", "d": -5}}, "section.d"),
        ({"section": {"type": "pla", "b": 10, "h": 10}}, "pla"),
        ({"section": {"type": "cir", "d": 200, "b": 100}}, "section.b"),
        ({"moisture_class": 4}, "moisture"),
        ({"N": 25}, "N"),
        ({"N": {"value": 25, "unit": "kg"}}, "unit"),
        ({"schema_version": "2.0"}, "schema_version"),
        ({"position": ""}, "position"),
        ({"impact": "yes"}, "impact"),
    ]
    for change, word in cases:
        src = _good()
        src.update(change)
        _refused(src, word)


def test_a_kind_not_known_and_one_not_implemented_are_refused_by_name():
    src = _good()
    src["kind"] = "earthquake"
    _refused(src, "earthquake", "kinds of member check")
    for kind in [k for k in member_check.KINDS if k not in member_check.IMPLEMENTED]:
        src = _good()
        src["kind"] = kind
        _refused(src, kind, "not implemented yet")


def test_a_source_whose_id_is_not_its_file_name_is_refused():
    d = conftest.tmpdir("member_check_read")
    path = d / "ZT-01.json"
    path.write_text(json.dumps(_good()), encoding="utf-8")
    try:
        member_check.read_source(path)
    except validation.ValidationError as exc:
        assert "file name" in str(exc)
    else:
        raise AssertionError("an id other than the file name was accepted")


# --- the resolution ---------------------------------------------------------------

def test_a_value_follows_its_position_unless_stated():
    rec = member_check.resolve(_good(), POSITIONS)
    assert rec["calculable"] and rec["reason"] == "" and rec["warnings"] == []
    assert (rec["grade"], rec["grade_from"]) == ("C24", "position")
    assert rec["section"] == {"type": "rec", "b": 100, "h": 200, "text": "100/200 mm"} and rec["section_from"] == "position"
    assert (rec["moisture_class"], rec["moisture_from"]) == (2, "position")
    src = _good()
    src.update(grade="GL28h", section={"type": "cir", "d": 180}, moisture_class=3)
    rec = member_check.resolve(src, POSITIONS)
    assert (rec["grade"], rec["grade_from"]) == ("GL28h", "stated")
    assert rec["section"]["text"] == "Ø 180 mm" and rec["section_from"] == "stated"
    assert (rec["moisture_class"], rec["moisture_from"]) == (3, "stated")
    round_one = _good()
    round_one["position"] = "R001"
    assert member_check.resolve(round_one, POSITIONS)["section"] == {"type": "cir", "d": 200, "text": "Ø 200 mm"}


def test_a_position_gone_warns_and_never_stops():
    src = _good()
    src["position"] = "T999"
    rec = member_check.resolve(src, POSITIONS)
    assert not rec["calculable"] and rec["reason"]
    assert rec["position_found"] is False
    codes = [note.code for note in rec["warnings"]]
    assert "check_position_missing" in codes and "check_not_calculable" in codes
    # every value stated: calculable all the same, the warning kept
    src.update(grade="C24", section={"type": "rec", "b": 100, "h": 200}, moisture_class=1)
    rec = member_check.resolve(src, POSITIONS)
    assert rec["calculable"] and [n.code for n in rec["warnings"]] == ["check_position_missing"]
    assert not rec["position_found"]


def test_what_the_project_lacks_is_not_calculable_with_its_reason():
    def reason(change):
        src = _good()
        src.update(change)
        rec = member_check.resolve(src, POSITIONS)
        assert not rec["calculable"], change
        assert rec["reason"]
        return rec["reason"]
    assert "moisture" in reason({"position": "W001"})
    assert "section" in reason({"position": "D001"})
    assert "steel" in reason({"position": "S002"})
    assert "tension" in reason({"N": {"value": 0, "unit": "kN"}})
    assert "tension" in reason({"N": {"value": -5, "unit": "kN"}})
    assert "Zugglieder" in reason({"position": "C001"})
    assert "section" in reason({"position": None})
    # C16 at an angle is not refused: the note is on f_t,0,d alone
    src = _good()
    src.update(position="C001", alpha=90)
    assert member_check.resolve(src, POSITIONS)["calculable"]


# --- the export ---------------------------------------------------------------------

def test_the_export_is_schema_valid_and_reproducible():
    here = conftest.project_copy("member_check_export")
    with project.using(here):
        bad = _good()
        bad.update(id="ZT-BAD", position="T999")
        (here.checks_dir / "ZT-BAD.json").write_text(json.dumps(bad, indent=2), encoding="utf-8")
        data = member_check.export(here)
        first = (here.data_dir / member_check.EXPORT_FILE).read_bytes()
        member_check.export(here)
        assert (here.data_dir / member_check.EXPORT_FILE).read_bytes() == first
    validation.validate_structure(data, "checks")
    validation.validate_checks_business(data)
    assert set(data["checks"]) >= {"ZT-01", "ZT-02", "ZT-BAD"}
    assert data["checks"]["ZT-01"]["calculable"] and not data["checks"]["ZT-BAD"]["calculable"]
    assert all(isinstance(w, str) for w in data["checks"]["ZT-BAD"]["warnings"])
    assert member_check.warnings_of(data)
    # what is calculable without its values is refused by the business rules
    planted = copy.deepcopy(data)
    planted["checks"]["ZT-01"]["moisture_class"] = None
    try:
        validation.validate_checks_business(planted)
    except validation.ValidationError:
        pass
    else:
        raise AssertionError("a calculable check with no moisture class passed")


def test_a_new_project_is_seeded_an_empty_export():
    here = conftest.project_copy("member_check_seed", data=False)
    assert "checks" in project.SOURCE_FOLDERS and here.checks_dir.name == "checks"
    written = export_all.seed(here)
    assert member_check.EXPORT_FILE in written
    assert json.loads((here.data_dir / member_check.EXPORT_FILE).read_text(encoding="utf-8")) == member_check.empty()


def test_the_example_project_carries_its_checks_and_the_examples_their_snapshot():
    data = conftest.exported(member_check.EXPORT_FILE)
    assert data["checks"]["ZT-01"]["calculable"]
    frozen = json.loads((conftest.ROOT / "examples" / "data" / member_check.EXPORT_FILE).read_text(encoding="utf-8"))
    assert set(frozen["checks"]) >= {"ZT-01", "ZT-02", "DR-01", "DR-02", "BI-01", "BI-02", "BI-03"}
    assert data["checks"]["DR-01"]["calculable"] and data["checks"]["DR-02"]["calculable"]
    assert all(data["checks"][cid]["calculable"] for cid in ("BI-01", "BI-02", "BI-03"))
    assert all(data["checks"][cid]["calculable"] for cid in ("KN-01", "KI-01", "KI-02", "SC-01")), "issue #38: a buckling, two lateral torsional bucklings, a shear"
    # issue #46: a bending in the fire situation following VKF 15-15 for the example's building (medium height, housing: R 60), a buckling stating its own R 30
    # 1.3 since the unfolded checks (spec 2026-10-15, ARCH-007), 1.5 since a duration VKF 15-15 requires is cited by it (spec 2026-10-20-indices-et-niveaux, REQ-001),
    # 1.6 since the spec 2026-10-21-commandes-typst-refonte: the checks printed unfolded with their `vars` and their file, and no `gen` (ARCH-011)
    assert data["schema_version"] == member_check.UNFOLDED_BASE_EXPORT_VERSION, "the example's checks are printed unfolded and name their file (issue #64)"
    assert data["checks"]["ZT-01"]["file"] and "gen" not in data["checks"]["ZT-01"], "1.6 holds 1.4's file and no gen"
    assert data["checks"]["FE-01"]["fire"].get("required"), "1.6 holds 1.5's fire.required"
    assert (data["checks"]["FE-01"]["fire"]["duration"], data["checks"]["FE-01"]["fire"]["duration_from"]) == (60, "vkf")
    assert (data["checks"]["FE-02"]["fire"]["duration"], data["checks"]["FE-02"]["fire"]["duration_from"]) == (30, "stated")
    assert data["checks"]["FE-01"]["calculable"] and data["checks"]["FE-02"]["calculable"]
    # REQ-001: a duration VKF 15-15 requires is cited by VKF 15-15 and the table it is read off; a duration stated cites nothing more than SIA 265
    assert data["checks"]["FE-01"]["fire"]["required"] == {"norm": "VKF 15-15", "norm_ref": "Tabelle 2"}
    assert data["checks"]["FE-02"]["fire"]["required"] is None


def test_a_duration_vkf_15_15_requires_is_cited_by_it_in_the_window_and_in_the_report():
    """REQ-001 (spec 2026-10-20-indices-et-niveaux, Q-004, base saine Q-017): FE-01 follows VKF 15-15 for the example's building (medium height, housing: R 60, Tabelle 2) -- its line t_fi cites «VKF 15-15 Tabelle 2» in the window's rows and in the report; FE-02 states its own R 30 and cites SIA 265 4.5.2."""
    data = conftest.exported(member_check.EXPORT_FILE)
    vkf = next(r for r in member_check.compute(data["checks"]["FE-01"])["rows"] if r["key"] == "t_fi")
    stated = next(r for r in member_check.compute(data["checks"]["FE-02"])["rows"] if r["key"] == "t_fi")
    assert (vkf["norm"], vkf["clause"]) == ("VKF 15-15", "Tabelle 2"), vkf
    assert (stated["norm"], stated["clause"]) == ("SIA 265", "4.5.2"), stated


# --- the report ---------------------------------------------------------------------

def _compile(body, name="member_check"):
    """`body` compiled after the report's import; (pdf text, None) or (None, panic message or error)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    from pypdf import PdfReader
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        return None, conftest.panic_message(out.stderr) or out.stderr
    return "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages), None


def _text(body, name="member_check"):
    text, error = _compile(body, name)
    assert text is not None, f"did not compile:\n{error}"
    return text


def test_check_member_ids_lists_the_checks():
    text = _text('#metadata(ids("check-member")) <ids>\n#ids("check-member").join(", ")')
    assert "ZT-01, ZT-02" in text


def test_the_positions_known_to_the_window_are_what_resolve_reads():
    # export() resolves against connector.known_positions -- the one reader of the exported positions -- so the window and the export agree
    here = project.current()
    positions = connector.known_positions(here.data_dir)
    rec = member_check.resolve(member_check.read_source(here.checks_dir / "ZT-01.json"), positions)
    assert rec["calculable"] and rec["grade"] == "C24" and rec["section"]["b"] == 100


# --- compression (SIA 265 4.2.2) ----------------------------------------------------

def _compression(**change):
    src = member_check.new_source("DR-99", "compression")
    src.update(position="T001", N={"value": 18, "unit": "kN"}, alpha=90, l=120)
    src.update(change)
    return src


def test_a_compression_source_is_checked_field_by_field():
    member_check.check_source(_compression())
    member_check.check_source(_compression(alpha=0, l=None))           # along the grain: no contact to state
    assert member_check.new_source("A", "compression")["case"] == "generell"
    assert "case" not in member_check.new_source("A")                   # a tension source carries none of it
    _refused(_compression(larger=True), "larger", "generell")
    _refused(_compression(case="generell", larger=True), "larger")
    _refused(_compression(case="vorholz"), "case")
    _refused(_compression(l=None), "l", "contact length")
    _refused(_compression(l=0), "l")
    _refused(_compression(w=-5), "w")
    _refused(_compression(larger="yes"), "larger")


def test_each_case_reads_its_f_c_90_d_of_the_table():
    expected = sia265.grade("C24")["f_c_90_d"]
    cases = (("generell", False, expected["generell"]),
             ("mit_vorholz", False, expected["mit_vorholz"]["value"]),
             ("mit_vorholz", True, expected["mit_vorholz"]["groessere_eindrueckungen"]),
             ("endauflagerung", False, expected["endauflagerung"]["value"]),
             ("endauflagerung", True, expected["endauflagerung"]["groessere_eindrueckungen"]))
    records = []
    for i, (case, larger, value) in enumerate(cases):
        src = _compression(id="DR-%d" % i, case=case, larger=larger, moisture_class=1)
        rec = member_check.resolve(src, POSITIONS)
        assert rec["calculable"], rec["reason"]
        assert (rec["case"], rec["larger"], rec["f_c_90_table"]) == (case, larger, value), rec
        assert rec["case_label"].startswith(member_check.CASE_WORDS[case]) and (member_check.LARGER_WORDS in rec["case_label"]) == larger
        records.append((rec, value))
    # the computation reads the same value: moisture class 1 and no impact, so f_c,90,d is the table's own
    for rec, value in records:
        rows = {row["key"]: row["value"] for row in member_check.compute(rec)["rows"]}
        assert rows["f_c_90_d"] == value, (rec["id"], value, rows["f_c_90_d"])


def test_a_bracketed_value_the_table_lacks_is_not_calculable():
    src = _compression(grade="D30", case="mit_vorholz", larger=True)
    rec = member_check.resolve(src, POSITIONS)
    assert not rec["calculable"] and "D30" in rec["reason"] and "bracketed" in rec["reason"]
    assert rec["f_c_90_table"] is None


def test_the_contact_width_follows_the_section_or_is_stated():
    rec = member_check.resolve(_compression(), POSITIONS)
    assert (rec["w"], rec["w_from"], rec["l"]) == (100, "section", 120)
    rec = member_check.resolve(_compression(w=80), POSITIONS)
    assert (rec["w"], rec["w_from"]) == (80, "stated")
    rows = {row["key"]: row["value"] for row in member_check.compute(rec)["rows"]}
    assert (rows["w_c"], rows["l_c"]) == (80, 120), rows
    # a round section has no width to follow
    rec = member_check.resolve(_compression(position="R001"), POSITIONS)
    assert not rec["calculable"] and "round" in rec["reason"] and rec["w"] is None
    rec = member_check.resolve(_compression(position="R001", w=120), POSITIONS)
    assert rec["calculable"] and rec["w_from"] == "stated"
    # along the grain the contact is not read at all
    rec = member_check.resolve(_compression(alpha=0, l=None, w=55, case="endauflagerung"), POSITIONS)
    assert rec["calculable"] and all(rec[k] is None for k in ("case", "larger", "l", "w", "w_from", "case_label", "f_c_90_table"))


def test_a_compression_that_is_no_positive_force_is_not_calculable():
    for value in (0, -5):
        rec = member_check.resolve(_compression(N={"value": value, "unit": "kN"}), POSITIONS)
        assert not rec["calculable"] and "magnitude" in rec["reason"]
    # C16 is refused in tension along the grain, not in compression
    assert member_check.resolve(_compression(position="C001", alpha=0, l=None), POSITIONS)["calculable"]


def test_a_compression_along_the_grain_is_the_section_alone():
    rec = member_check.resolve(_compression(alpha=0, l=None), POSITIONS)
    rows = {row["key"]: row for row in member_check.compute(rec)["rows"]}
    # the section alone: no buckling length, the clause of 4.2.2.1
    assert not any(key.startswith(("lambda", "k_c", "l_k")) for key in rows), sorted(rows)
    data = conftest.exported(member_check.EXPORT_FILE)
    rows = {row["key"]: row for row in member_check.compute(data["checks"]["DR-02"])["rows"]}
    n_mm = 60e3 / (140 * 140)                                    # N/A in N/mm²
    eta = n_mm / sia265.grade("GL24h")["f_c_0_d"]                # moisture class 1, no impact
    assert abs(rows["eta"]["value"] - eta) < 1e-9, (eta, rows["eta"])


def test_a_compression_at_an_angle_reads_equation_13():
    rec = member_check.resolve(_compression(alpha=30, case="mit_vorholz", moisture_class=1), POSITIONS)
    assert rec["calculable"] and rec["alpha"] == 30
    result = member_check.compute(rec)
    assert (result["clause"], result["equation"]) == ("4.2.2.3", "(12)/(13)"), (result["clause"], result["equation"])


# --- bending (SIA 265 4.2.3, 4.2.4) -------------------------------------------------

def _kNm(value):
    return {"value": value, "unit": "kNm"}


def _bending(**change):
    src = member_check.new_source("BI-99", "bending")
    src.update(position="T001")
    src.update(change)
    return src


def test_a_bending_source_is_checked_field_by_field():
    """A moment is a {value, unit} block or null; N is signed for a bending alone -- a negative one is a compression, 0 none."""
    src = member_check.new_source("BI-1", "bending")
    assert (src["N"], src["M_y"], src["M_z"]) == ({"value": 0, "unit": "kN"}, _kNm(10), None)
    member_check.check_source(_bending())
    member_check.check_source(_bending(N={"value": -40, "unit": "kN"}, M_z={"value": -2500, "unit": "Nm"}))
    no_moment = _bending()
    del no_moment["M_y"], no_moment["M_z"]
    member_check.check_source(no_moment)            # absent is no moment: resolve's to say, not a stop
    for change, words in (({"M_y": 5}, ("M_y",)), ({"M_y": {"value": "5", "unit": "kNm"}}, ("M_y",)),
                          ({"M_z": {"value": 1, "unit": "kN"}}, ("M_z.unit", "kNm")), ({"M_y": {"value": 1}}, ("M_y", "unit"))):
        _refused(_bending(**change), *words)


def test_what_a_bending_cannot_be_checked_with_is_not_calculable():
    """No moment, M_z at an angle (17)-(20) do not read, no M_y at an angle: `calculable: false` with the reason, never a stop. A tension's and a compression's N are refused below 0 as before; a bending's is any number."""
    def reason(**change):
        rec = member_check.resolve(_bending(**change), POSITIONS)
        assert not rec["calculable"] and rec["reason"], change
        return rec["reason"]
    assert "no moment" in reason(M_y=None)
    assert "no moment" in reason(M_y=_kNm(0), M_z=_kNm(0))
    assert "M_z" in reason(alpha=20, M_z=_kNm(1))
    assert "no moment" in reason(alpha=20, M_y=_kNm(0), M_z=None)
    for n in (-40, 0, 25):
        rec = member_check.resolve(_bending(N={"value": n, "unit": "kN"}), POSITIONS)
        assert rec["calculable"], (n, rec["reason"])
    # the moments are on a bending's record only, a moment of 0 being none -- a tension's record is as it was
    rec = member_check.resolve(_bending(M_z=_kNm(0)), POSITIONS)
    assert rec["M_y"] == _kNm(10) and rec["M_z"] is None
    assert "M_y" not in member_check.resolve(_good(), POSITIONS)
    assert "tension" in member_check.resolve({**_good(), "N": {"value": -5, "unit": "kN"}}, POSITIONS)["reason"]


def test_the_business_rules_take_a_bending_s_signed_n():
    data = {"schema_version": "1.0", "checks": {}}
    for cid, n in (("BI-A", -40), ("BI-B", 0), ("BI-C", 12)):
        rec = member_check.resolve(_bending(id=cid, N={"value": n, "unit": "kN"}), POSITIONS)
        rec["warnings"] = []
        data["checks"][cid] = rec
    validation.validate_structure(data, "checks")
    validation.validate_checks_business(data)
    for planted_change, word in (({"M_y": None}, "no moment"), ({"alpha": 30, "M_z": _kNm(1)}, "M_y alone")):
        planted = copy.deepcopy(data)
        planted["checks"]["BI-A"].update(planted_change)
        try:
            validation.validate_checks_business(planted)
        except validation.ValidationError as exc:
            assert word in str(exc)
        else:
            raise AssertionError("a calculable bending %r passed" % planted_change)
    tension = copy.deepcopy(data)
    tension["checks"]["BI-A"]["kind"] = "tension"
    try:
        validation.validate_checks_business(tension)
    except validation.ValidationError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("a calculable tension with a negative N passed")


# --- the instant calculation, held equal to the report's ---------------------------

def _kind(kind, **change):
    src = member_check.new_source("X-99", kind)
    src.update(position="T001")
    src.update(change)
    return src


def test_compute_gives_none_where_the_report_refuses():
    assert member_check.compute(None) is None
    rec = member_check.resolve(_compression(N={"value": 0, "unit": "kN"}), POSITIONS)
    assert member_check.compute(rec) is None
    rec = member_check.resolve(_good(), POSITIONS)
    result = member_check.compute(rec)
    assert set(result) == {"kind", "equation", "clause", "rows", "eta", "ok", "relation", "ratio"}
    assert all({"key", "symbol", "value", "unit"} <= set(row) for row in result["rows"])
    assert [row["key"] for row in result["rows"]][-1] == "eta" and result["rows"][-1]["value"] == result["eta"]


def test_a_buckling_and_a_lateral_torsional_buckling_reproduce_the_stuetzen_workbook():
    """REQ-007, REQ-008 (issue #38, D-02): «rectangular column» template, «Pendelstütze mit Knickhalterung», moisture class 1, recalculated by Excel on 11.10.2026 (a copy of the template). The workbook takes E_0,05 as 5/6 (glulam) or 2/3 (solid) of E_0,mean -- its matrix, columns 21 and 22 --, the norm reads it off Anhang B: its chain of cells F32 to F36, F55, F56 and D40, evaluated here with its own E_0,05, gives the numbers Excel printed, and with the norm's the numbers Woodcore computes."""
    import math

    def chain(l_k, b, h, f_c_0_k, e_0_05, beta_c):
        lam = l_k / math.sqrt(h * h / 12)                                       # F32 = l_k / sqrt(I/A), about the axis of h
        rel = lam / math.pi * math.sqrt(f_c_0_k / e_0_05)                         # F33
        k = 0.5 * (1 + beta_c * max(0, rel - 0.3) + rel ** 2)                     # F35
        return lam, rel, min(1 / (k + math.sqrt(k ** 2 - max(rel, 0.3) ** 2)), 1)  # F36

    def rows(kind, **change):
        return {row["key"]: row["value"] for row in member_check.compute(member_check.resolve(_kind(kind, moisture_class=1, **change), POSITIONS))["rows"]}

    # a buckling: C24 140/200, N_d 40 kN, l_k,y = l_k,z = 3.5 m -- Excel: lambda_y 60.6218, kc,y 0.665025 (F36), kc,z 0.390375 (M36), sigma_c/(kc,z f_c) 0.295120 (J40 with M_z 0)
    got = rows("buckling", grade="C24", section={"type": "rec", "b": 140, "h": 200}, N={"value": 40, "unit": "kN"}, l_y=3500, l_z=3500)
    for axis, depth, excel_kc in (("y", 200, 0.665024664675156), ("z", 140, 0.390375104897443)):
        lam, _, kc = chain(3500, 140 if axis == "y" else 200, depth, 21, 11000 * 2 / 3, 0.2)
        assert abs(kc - excel_kc) < 1e-12 and abs(got["lambda_" + axis] - lam) < 1e-9, (axis, kc, excel_kc)
        assert abs(chain(3500, 0, depth, got["f_c_0_k"], got["E_0_05"], got["beta_c"])[2] - got["k_c_" + axis]) < 1e-9, axis
    assert got["f_c_0_d"] == 12.4 and abs(got["sigma_c_0_d"] - 1.42857142857143) < 1e-12
    assert abs(1.42857142857143 / (0.390375104897443 * 12.4) - 0.295119672916017) < 1e-12 and abs(got["eta"] - got["sigma_c_0_d"] / (got["k_c_z"] * 12.4)) < 1e-9
    # a lateral torsional buckling with a compression: GL24h 120/240, N_d 60 kN, M_y,d 6 kNm, l_k,y = a = 3 m, l_k,z 1.5 m -- Excel: sigma_m,y 5.20833 (F27), lambda_rel,m 0.406940 (F55), k_m 1 (F56), k_h 1.095958 (F57), (37) 0.436365 (D40)
    got = rows("lateral-torsional", grade="GL24h", section={"type": "rec", "b": 120, "h": 240}, N={"value": -60, "unit": "kN"}, M_y={"value": 6, "unit": "kNm"}, a=3000, l_y=3000, l_z=1500)
    assert abs(got["sigma_m_y_d"] - 5.20833333333333) < 1e-12 and got["k_m"] == 1 and abs(got["k_h_y"] - 1.09595822638522) < 1e-12
    excel_m = 1.15 * math.sqrt(3000 * 240) / 120 * math.sqrt(24 / (11500 * 5 / 6))
    # the workbook's 1.15 is sqrt(1 / 0.75) = 1.1547 rounded: (41) sigma_m,crit = 0.75 E_0,05 b² / (a h), and (40) sqrt(f_m,k / sigma_m,crit)
    assert abs(excel_m - 0.406939798987516) < 1e-12 and abs(got["lambda_rel_m"] - math.sqrt(1 / 0.75) * math.sqrt(3000 * 240) / 120 * math.sqrt(got["f_m_k"] / got["E_0_05"])) < 1e-9
    _, _, kc_excel = chain(3000, 0, 240, 24, 11500 * 5 / 6, 0.1)
    assert abs(2.08333333333333 / (kc_excel * 16) + 5.20833333333333 / (1 * 17.5353316221635) - 0.436364816303239) < 1e-12
    _, _, kc_norm = chain(3000, 0, 240, got["f_c_0_k"], got["E_0_05"], got["beta_c"])
    assert abs(got["eta_y"] - (got["sigma_c_0_d"] / (kc_norm * got["f_c_0_d"]) + got["sigma_m_y_d"] / (got["k_m"] * got["f_m_y_d"]))) < 1e-9
    assert abs(got["eta_y"] - 0.436364816303239) < 1e-4, "within the E_0,05 difference"


def test_a_shear_reproduces_the_bemessungsbeispiele():
    """REQ-009 (issue #38): the joist of Bemessungsbeispiele zur Norm SIA 265 (Lignum), p. 114 -- GL24h 160/440 mm, moisture class 1, V_d = 41.4 kN: tau_d = 1.5 V_d / (b h) = 0.88 N/mm², f_v,d = 1.0 · 1.8 = 1.8 N/mm²."""
    src = _kind("shear", grade="GL24h", section={"type": "rec", "b": 160, "h": 440}, moisture_class=1, V_z={"value": 41.4, "unit": "kN"})
    rows = {row["key"]: row["value"] for row in member_check.compute(member_check.resolve(src, POSITIONS))["rows"]}
    assert round(rows["tau_z_d"], 2) == 0.88 and rows["f_v_d"] == 1.8, rows
    assert abs(rows["eta"] - 0.88 / 1.8) < 0.005, rows


def test_the_shear_factors_are_the_reports_and_mechanics():
    """ARCH-RISK-104 (issue #38): the largest shear stress at the centroid, 1.5 V/A for a rectangle and 4/3 V/A for a circle, is mechanics -- SIA 265 (23) states tau_d <= f_v,d and no factor -- and member_check.SHEAR_FACTORS holds the two."""
    assert member_check.SHEAR_FACTORS == {"rec": 1.5, "cir": 4 / 3}


def test_the_new_kinds_are_refused_or_not_calculable_with_their_reason():
    """Issue #38: a malformed buckling, lateral torsional buckling or shear stops naming the field; what the project lacks is calculable false with a reason."""
    for kind, change, word in (("buckling", {"l_y": -1}, "l_y"), ("buckling", {"beta_z": "x"}, "beta_z"), ("buckling", {"alpha": 30}, "along the grain"),
                               ("lateral-torsional", {"a": 0}, "a is"), ("lateral-torsional", {"a": 3000, "sigma_m_crit": 30}, "both given"),
                               ("shear", {"V_z": 10}, "V_z"), ("shear", {"V_y": {"value": 2, "unit": "kg"}}, "V_y.unit"), ("shear", {"pith": "yes"}, "pith")):
        _refused(_kind(kind, **change), word)
    for kind, change, words in (("buckling", {"l_z": None}, "no system length about z"),
                                ("lateral-torsional", {"a": None}, "neither a nor sigma_m_crit"),
                                ("lateral-torsional", {"M_y": None, "M_z": _kNm(2)}, "no M_y"),
                                ("lateral-torsional", {"section": {"type": "rec", "b": 300, "h": 100}, "M_z": _kNm(2), "a": None}, "neither a nor sigma_m_crit"),
                                ("lateral-torsional", {"position": "R001", "M_y": None, "a": None}, "no moment"),
                                ("lateral-torsional", {"N": {"value": -10, "unit": "kN"}}, "which (37) reads"),
                                ("shear", {"V_z": None}, "no shear force")):
        src = _kind(kind, **change)
        member_check.check_source(src)
        rec = member_check.resolve(src, POSITIONS)
        assert not rec["calculable"] and words in rec["reason"], (kind, rec["reason"])
    rec = member_check.resolve(_kind("shear"), POSITIONS)
    assert rec["calculable"] and rec["N"] is None and rec["V_z"] == {"value": 10, "unit": "kN"} and rec["pith"] is False
    # spec 2026-10-12-audit-issues-47-48-49: a round section's lateral torsional buckling is calculable with no a (D-10, D-15) -- it was refused until then
    rec = member_check.resolve(_kind("lateral-torsional", position="R001", a=None), POSITIONS)
    assert rec["calculable"], rec["reason"]


def test_lateral_torsional_buckling_tips_about_the_strong_axis():
    """Spec 2026-10-12-audit-issues-47-48-49, REQ-011, REQ-012 (D-09, D-10, D-17), against SIA 265 by hand -- a reference neither implementation produced (ARCH-RISK-M04). GL24h 600/120, class 1, a = 6000 mm, M_z = 40 kNm: the section is wider than high, so it tips about z and (41) reads h²/(a·b): sigma_m,crit = 0.75 · 9600 · 120² / (6000 · 600) = 28.8 N/mm²; lambda_rel,m = sqrt(24 / 28.8); k_m of (39); (38) sigma_m,z,d / (k_m · f_m,z,d). Bent about y alone the same section tips about nothing: k_m = 1, eta = eta_s. A round section reads either moment with k_m = 1."""
    from norms import sia265
    lateral = sia265.lateral_buckling()
    ch = sia265.characteristic("GL24h")
    src = _kind("lateral-torsional", grade="GL24h", section={"type": "rec", "b": 600, "h": 120}, moisture_class=1, M_y=None, M_z=_kNm(40), a=6000)
    rec = member_check.resolve(src, POSITIONS)
    assert rec["calculable"], rec["reason"]
    rows = {r["key"]: r["value"] for r in member_check.compute(rec)["rows"]}
    crit = lateral["sigma_m_crit_factor"] * ch["E_0_05"] * 120 ** 2 / (6000 * 600)
    assert abs(crit - 28.8) < 1e-9 and abs(rows["sigma_m_crit"] - crit) < 1e-9
    assert rows["f_m_k"] == 24, "GL24h, Tabelle 9"
    lam = (24 / crit) ** 0.5
    assert abs(rows["lambda_rel_m"] - lam) < 1e-9
    k_m = rows["k_m"]
    sigma_z = 40e6 / (120 * 600 ** 2 / 6)
    assert abs(rows["eta_m"] - sigma_z / (k_m * rows["f_m_z_d"])) < 1e-9
    weak = member_check.resolve(_kind("lateral-torsional", grade="GL24h", section={"type": "rec", "b": 600, "h": 120}, moisture_class=1, M_y=_kNm(1), a=None), POSITIONS)
    assert weak["calculable"], weak["reason"]
    rows = {r["key"]: r["value"] for r in member_check.compute(weak)["rows"]}
    assert "k_m" not in rows and "sigma_m_crit" not in rows and rows["eta"] == rows["eta_s"]
    assert member_check.strong_axis({"type": "rec", "b": 100, "h": 100}) == "y" and member_check.strong_axis({"type": "cir", "d": 200}) is None


def test_the_pith_halves_solid_timber_only():
    """REQ-010 (D-02): SIA 265 Tabelle 8 note 6 halves f_v,d of solid timber cut from the pith; Tabelle 9 has no such note. A glulam with `pith` keeps its f_v,d and the record says why; C24 halves it."""
    glulam = member_check.resolve(_kind("shear", grade="GL24h", section={"type": "rec", "b": 120, "h": 240}, moisture_class=1, pith=True), POSITIONS)
    plain = member_check.resolve(_kind("shear", grade="GL24h", section={"type": "rec", "b": 120, "h": 240}, moisture_class=1, pith=False), POSITIONS)
    assert member_check.compute(glulam)["eta"] == member_check.compute(plain)["eta"]
    assert any(getattr(w, "code", "") == "check_pith_glulam" for w in glulam["warnings"]), glulam["warnings"]
    solid = member_check.resolve(_kind("shear", pith=True), POSITIONS)
    keys = {r["key"] for r in member_check.compute(solid)["rows"]}
    assert "f_v_d_p" in keys and not any(getattr(w, "code", "") == "check_pith_glulam" for w in solid["warnings"])


# --- what an unfolded check is written from (spec 2026-10-15-calculs-deplies-balises-figures-natives, ARCH-007, ARCH-008) ---

def test_a_tension_s_rows_carry_their_formula_in_keys_their_clause_and_their_table():
    """ARCH-008: every derived row of a tension carries `keys` -- the formula as `#eq` computes it, in the registry's keys -- and a design value the value of SIA 265's table it is computed from (`table`), so that the unfolded file writes no value of the norm inside a formula. Found on the review: the formulas carried the table's value as a literal (`eta_w dot eta_t dot 14`)."""
    for alpha in (0, 30, 90):
        rec = member_check.resolve(_kind("tension", alpha=alpha), POSITIONS)
        rows = member_check.compute(rec)["rows"]
        for row in rows:
            if row["key"] in ("N_t_d", "alpha", "eta_w", "eta_t"):
                assert "keys" not in row, (alpha, row)
                continue
            assert row.get("keys"), (alpha, row["key"])
            assert not re.search(r"(?<![A-Za-z_])\d+\.\d", row["keys"]), ("a value of the norm in a formula", alpha, row)
            if row["key"] in ("f_t_0_d", "f_t_90_d"):
                assert row["table"]["key"] == row["key"] + "_tab" and row["clause"] == "Tabelle %s" % sia265.grade_table(rec["grade"])
        names = {row["key"] for row in rows} | {row["table"]["key"] for row in rows if row.get("table")} | {"b", "h", "d", "pi", "dot", "sin", "cos"}
        for row in rows:
            for name in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", row.get("keys", "")):
                assert name in names, (alpha, row["key"], name)


def test_an_unfolded_check_publishes_its_inputs_and_its_form():
    """ARCH-007: a calculable tension carries `vars` -- its section, its inputs and its tables' values -- and `gen`, its form; the export is then 1.3 and holds its schema. A check of another kind, or in the fire situation, carries neither (D-11, D-15)."""
    rec = member_check.resolve(_kind("tension", alpha=0), POSITIONS)
    assert member_check.form_of(rec) == {"kind": "tension", "form": "(6)", "version": unfold.GENERATOR_VERSION}
    published = member_check.published_vars(rec)
    assert {"b", "h", "N_t_d", "eta_w", "eta_t", "f_t_0_d_tab"} <= set(published), sorted(published)
    assert published["f_t_0_d_tab"]["norm"] == "SIA 265" and published["f_t_0_d_tab"]["value"] == sia265.grade(rec["grade"])["f_t_0_d"]
    assert member_check.form_of(member_check.resolve(_kind("tension", alpha=30), POSITIONS))["form"] == "(8)/(9)"
    # every kind computed is printed unfolded since the spec 2026-10-21-commandes-typst-refonte (REQ-017)
    assert member_check.form_of(member_check.resolve(_kind("compression"), POSITIONS))["kind"] == "compression"
    data = member_check.prepare(conftest.PROJECT, connector.known_positions(conftest.PROJECT.data_dir))
    # 1.6 since the spec 2026-10-21-commandes-typst-refonte: the vars of a check printed unfolded, no `gen` -- its form is the regeneration base's (ARCH-011)
    assert data["schema_version"] == member_check.UNFOLDED_BASE_EXPORT_VERSION
    calculable = [r for r in data["checks"].values() if r["calculable"]]
    assert calculable and all("vars" in r and "gen" not in r for r in calculable)


def test_a_shear_off_and_a_shear_across_the_grain_are_computed_in_python():
    """Spec 2026-10-21-commandes-typst-refonte, REQ-021, Q-010: the shear-off of SIA 265 4.2.6 and the shear with a stress perpendicular to the grain of 4.2.7.1, until then `#verify-shear-off` and `#verify-shear-perp` alone, are variants of a shear check computed in Python -- the values `tests/test_timber.py` holds the Typst to, each value of the norm read through `norms.sia265`. A sheared length under the clause's, or a missing stress, is no check and says why."""
    import math
    off = member_check.resolve(_kind("shear", variant="shear-off", F={"value": 20, "unit": "kN"}, l=200, w=None), POSITIONS)
    result = member_check.compute(off)
    eta_w = sia265.eta_w(off["moisture_class"], "resistance")
    f_v = eta_w * sia265.grade(off["grade"])["f_v_d"]
    width = off["section"]["b"]
    assert result["equation"] == "(26)" and math.isclose(result["eta"], 20e3 / (200 * width) / (0.6 * f_v), rel_tol=1e-12), result
    short = member_check.resolve(_kind("shear", variant="shear-off", F={"value": 20, "unit": "kN"}, l=120), POSITIONS)
    assert not short["calculable"] and "150" in short["reason"], short["reason"]
    c = sia265.shear_transverse()
    for s90, k in ((-1.2, c["k_t_90"]["querdruck"]), (0.05, c["k_t_90"]["querzug"])):
        perp = member_check.resolve(_kind("shear", variant="shear-perp", V_z={"value": 12, "unit": "kN"}, sigma_90=s90), POSITIONS)
        result = member_check.compute(perp)
        g = sia265.grade(perp["grade"])
        factor = sia265.eta_w(perp["moisture_class"], "resistance")
        fc, ft, fv = factor * g["f_c_90_d"]["generell"], factor * g["f_t_90_d"], factor * g["f_v_d"]
        tau = 1.5 * 12e3 / (perp["section"]["b"] * perp["section"]["h"])
        r = fc / (fc + k * ft)
        want = ((fc + s90) / (fc + k * ft)) ** 2 + (tau / fv) ** 2 * (1 - r ** 2)
        rows = {row["key"]: row["value"] for row in result["rows"]}
        assert result["equation"] == "(28)" and rows["k_t_90"] == k and math.isclose(result["eta"], want, rel_tol=1e-12), (s90, result["eta"], want)
    missing = member_check.resolve(_kind("shear", variant="shear-perp", V_z={"value": 12, "unit": "kN"}), POSITIONS)
    assert not missing["calculable"] and "sigma_90" in missing["reason"]
    try:
        member_check.check_source(_kind("bending", variant="shear-off"))
    except Exception as exc:
        assert "variant" in str(exc)
    else:
        raise AssertionError("a variant is a shear check's alone")


# --- the published worked examples, held against the export's own computation (spec 2026-10-21-commandes-typst-refonte, REQ-017) ---
# Until the verify-* commands were retired the examples were held against lib/timber.typ (tests/test_timber.py), and member_check.compute against it; the computation is Python's alone now, so the examples are held against it here.

ORACLES = conftest.ROOT / "tests" / "fixtures" / "timber-oracles.json"
_kN = lambda v: {"value": v, "unit": "kN"}
_rec = lambda b, h: {"type": "rec", "b": b, "h": h}
# case id -> (kind, grade, section, the source's own fields, {key of member_check's rows: key of the oracle}) -- each case of the fixture that carries a call
ORACLE_RECORDS = {
    "bb-shear-p114": ("shear", "GL24h", _rec(160, 440), {"V_z": _kN(41.4)}, {"tau_z_d": "tau_d", "f_v_d": "f_v_d"}),
    "bb-shear-p73": ("shear", "C24", _rec(100, 240), {"V_z": _kN(6.6)}, {"tau_z_d": "tau_d", "f_v_d": "f_v_d"}),
    "bb-shear-p87": ("shear", "GL24h", _rec(140, 280), {"V_z": _kN(46.4)}, {"tau_z_d": "tau_d"}),
    "bb-bending-p72": ("bending", "C24", _rec(100, 240), {"M_y": _kNm(5.87)}, {"W_y": "W_y", "sigma_m_y_d": "sigma_m_y_d", "f_m_y_d": "f_m_y_d"}),
    # k_h_y is in f_m_y_d, which the rows carry
    "bb-bending-p87": ("bending", "GL24h", _rec(140, 280), {"M_y": _kNm(25.8)}, {"sigma_m_y_d": "sigma_m_y_d", "f_m_y_d": "f_m_y_d"}),
    "bb-bending-biaxial-p166": ("bending", "C24", _rec(120, 220), {"M_y": _kNm(6.82), "M_z": _kNm(2.1)}, {"sigma_m_y_d": "sigma_m_y_d", "sigma_m_z_d": "sigma_m_z_d", "eta": "eta_s"}),
    "bb-bending-biaxial-p167": ("bending", "C24", _rec(100, 220), {"M_y": _kNm(5.86), "M_z": _kNm(1.81)}, {"sigma_m_y_d": "sigma_m_y_d", "sigma_m_z_d": "sigma_m_z_d", "eta": "eta_s"}),
    "bb-lateral-buckling-p143": ("lateral-torsional", "GL28c", _rec(180, 1440), {"M_y": _kNm(1035), "a": 5000},
                                 {"sigma_m_y_d": "sigma_m_y_d", "lambda_rel_m": "lambda_rel_m", "k_m": "k_m", "f_m_y_d": "f_m_y_d"}),
    "bb-buckling-p122": ("buckling", "C24", _rec(120, 120), {"N": _kN(40), "l_y": 3950, "l_z": 3950},
                         {"sigma_c_0_d": "sigma_c_0_d", "lambda_z": "lambda_z", "lambda_rel_z": "lambda_rel_z", "k_c_z": "k_c_z"}),
    "bb-buckling-p125": ("buckling", "C24", _rec(80, 140), {"N": _kN(25.1), "l_y": 5200, "l_z": 0}, {"sigma_c_0_d": "sigma_c_0_d", "lambda_rel_y": "lambda_rel_y", "k_c_y": "k_c_y"}),
    "bb-compression-perp-p263": ("compression", "C24", _rec(120, 300), {"N": _kN(30), "alpha": 90, "l": 160, "case": "mit_vorholz"}, {"f_c_90_d": "f_c_90_d", "A_c": "A_c"}),
    "bb-compression-perp-p265": ("compression", "D30", _rec(120, 300), {"N": _kN(30), "alpha": 90, "l": 160, "case": "mit_vorholz"}, {"f_c_90_d": "f_c_90_d"}),
    "tpl-unterzug-c24-100x1120": ("bending", "C24", _rec(100, 1120), {"M_y": _kNm(294.006)}, {"W_y": "W_y", "eta": "eta_s"}),
    "tpl-unterzug-c24-120x1000": ("bending", "C24", _rec(120, 1000), {"M_y": _kNm(294.006)}, {"eta": "eta_s"}),
    # the stresses alone: the template takes E_0,05 = 2/3 E_0,mean (7333 N/mm² for C24), SIA 265 Anhang B gives 7400 -- the norm's is the export's (lambda_rel 0.339 against 0.341)
    "tpl-rundstuetze-c24-d200": ("lateral-torsional", "C24", {"type": "cir", "d": 200}, {"N": _kN(-386), "M_y": _kNm(0.0625), "a": 1000, "l_y": 1000, "l_z": 1000},
                                 {"sigma_c_0_d": "sigma_c_0_d", "sigma_m_y_d": "sigma_m_y_d"}),
}
# the cases a call carries that no check of Woodcore computes, and why
ORACLE_NOT_COMPUTED = {
    "bb-shear-torsion-p114": "torsion (SIA 265 (25)) is no check of Woodcore's: #verify-shear computed it in the report until it was retired",
    "bb-torsion-p114": "torsion (SIA 265 (25)) is no check of Woodcore's: #verify-shear computed it in the report until it was retired",
}


def _synthetic():
    """Records over the angles, the cases and the grades: each resolved as the export resolves it, against POSITIONS."""
    out = []
    def add(src):
        rec = member_check.resolve(src, POSITIONS)
        assert rec["calculable"], (src, rec["reason"])
        # a position of POSITIONS the example project does not export is a member that is none, as #member would refuse it
        rec["position_found"] = rec["position"] in ("T001", "S001")
        out.append(rec)
    for i, (alpha, grade, impact) in enumerate(((0, "GL28h", False), (90, "C30", False), (35, "D30", True), (60, "GL24h", False))):
        src = _good()
        src.update(id="ZS-%d" % i, alpha=alpha, grade=grade, impact=impact)
        add(src)
    src = _good()
    src.update(id="ZS-R", position="R001", N={"value": 120, "unit": "kN"})
    add(src)
    for i, (alpha, case, larger, grade) in enumerate(((90, "generell", False, "C24"), (90, "mit_vorholz", True, "C24"), (90, "endauflagerung", True, "GL28h"),
                                                       (30, "mit_vorholz", False, "GL24h"), (75, "endauflagerung", False, "D30"))):
        add(_compression(id="DS-%d" % i, alpha=alpha, case=case, larger=larger, grade=grade, w=90 + i))
    add(_compression(id="DS-A", alpha=0, l=None, grade="C24", N={"value": 0.25, "unit": "MN"}))
    add(_compression(id="DS-R", alpha=0, l=None, position="R001", impact=True))
    # bending: (14) about one and two axes, glulam under and over 600 mm (k_h), a round section, (15)/(16), (17)-(20), (21), (22), and (21)/(22) at an angle
    glulam = {"grade": "GL24h", "section": {"type": "rec", "b": 120, "h": 280}, "moisture_class": 1}
    for i, change in enumerate((
        {"M_y": _kNm(4), "M_z": _kNm(0.5)},
        {**glulam, "M_y": _kNm(8), "M_z": _kNm(-1)},
        {"grade": "GL28h", "section": {"type": "rec", "b": 200, "h": 640}, "moisture_class": 2, "M_y": _kNm(50), "M_z": _kNm(2)},
        {"position": "R001", "M_y": _kNm(3), "M_z": _kNm(1)},
        {"M_y": None, "M_z": _kNm(0.8), "impact": True},
        {**glulam, "alpha": 90, "M_y": _kNm(0.5)},
        {**glulam, "alpha": 25, "M_y": _kNm(6)},
        {"position": "R001", "alpha": 15, "M_y": _kNm(1.5)},
        {"N": {"value": 30, "unit": "kN"}, "M_y": _kNm(4), "M_z": _kNm(0.4)},
        {"N": {"value": -0.04, "unit": "MN"}, "M_y": {"value": 3000, "unit": "Nm"}},
        {**glulam, "N": {"value": -60, "unit": "kN"}, "M_y": _kNm(5), "M_z": {"value": 0.0012, "unit": "MNm"}},
        {**glulam, "alpha": 30, "N": {"value": 20, "unit": "kN"}, "M_y": _kNm(2)},
        {"alpha": 30, "N": {"value": -30, "unit": "kN"}, "M_y": _kNm(1), "impact": True},
        {**glulam, "alpha": 90, "N": {"value": 5, "unit": "kN"}, "M_y": _kNm(0.2)},
        {"position": "R001", "alpha": 15, "N": {"value": -10, "unit": "kN"}, "M_y": _kNm(1)},
    )):
        add(_bending(id="BS-%d" % i, **change))
    # issue #38 -- buckling: solid and glulam, moisture classes 1 to 3, lambda_rel on either side of 0.3, an axis held (l = 0), a round section
    glulam_sq = {"grade": "GL24h", "section": {"type": "rec", "b": 140, "h": 140}, "moisture_class": 1}
    for i, change in enumerate((
        {"N": {"value": 30, "unit": "kN"}, "l_y": 3000, "l_z": 3000},
        {**glulam_sq, "N": {"value": 60, "unit": "kN"}, "l_y": 3200, "l_z": 3200, "beta_z": 0.7},
        {"N": {"value": 20, "unit": "kN"}, "l_y": 300, "l_z": 300},
        {"position": "R001", "N": {"value": 50, "unit": "kN"}, "l_y": 2500, "l_z": 2500},
        {"grade": "C30", "moisture_class": 3, "N": {"value": 15, "unit": "kN"}, "l_y": 4000, "l_z": 0, "impact": True},
    )):
        add(_kind("buckling", id="KS-%d" % i, **change))
    # lateral torsional buckling: the three branches of k_m, a given sigma_m,crit, M_z, a tension (38), a compression (37)
    for i, change in enumerate((
        {"M_y": _kNm(4), "a": 3000},
        {"grade": "GL28h", "section": {"type": "rec", "b": 160, "h": 800}, "moisture_class": 1, "M_y": _kNm(150), "a": 8000},
        {"grade": "GL28h", "section": {"type": "rec", "b": 100, "h": 800}, "moisture_class": 2, "M_y": _kNm(40), "a": 10000},
        {"M_y": _kNm(5), "M_z": _kNm(0.5), "a": None, "sigma_m_crit": 40},
        {"N": {"value": 20, "unit": "kN"}, "M_y": _kNm(4), "a": 4000},
        {**glulam, "N": {"value": -40, "unit": "kN"}, "M_y": _kNm(3), "M_z": _kNm(0.3), "a": 3000, "l_y": 3000, "l_z": 3000},
        {"N": {"value": -15, "unit": "kN"}, "M_y": _kNm(2), "a": 500, "l_y": 2000, "l_z": 1000, "beta_y": 1, "beta_z": 1},
        # spec 2026-10-12-audit-issues-47-48-49: wider than high, tipping about z (D-09) -- alone, with a tension, with a compression, with a given sigma_m,crit; bent about y alone, nothing tips (D-17); a round section, either moment, no a (D-10, D-15)
        {"grade": "GL24h", "section": {"type": "rec", "b": 600, "h": 120}, "moisture_class": 1, "M_y": _kNm(1), "M_z": _kNm(40), "a": 6000},
        {"grade": "GL24h", "section": {"type": "rec", "b": 600, "h": 120}, "moisture_class": 1, "N": {"value": 20, "unit": "kN"}, "M_z": _kNm(30), "a": 5000},
        {"grade": "GL24h", "section": {"type": "rec", "b": 400, "h": 100}, "moisture_class": 2, "N": {"value": -20, "unit": "kN"}, "M_y": _kNm(0.5), "M_z": _kNm(10), "a": 4000, "l_y": 3000, "l_z": 4000},
        {"section": {"type": "rec", "b": 300, "h": 100}, "M_z": _kNm(8), "a": None, "sigma_m_crit": 25},
        {"section": {"type": "rec", "b": 300, "h": 100}, "M_y": _kNm(1.5), "a": None},
        {"position": "R001", "M_y": _kNm(3), "M_z": _kNm(1), "a": None},
        {"position": "R001", "N": {"value": -60, "unit": "kN"}, "M_z": _kNm(2), "a": None, "l_y": 3000, "l_z": 3000},
        # REQ-012: the Rundquerschnitte workbook's column, C24 Ø200, N + M saved, computed and printed
        {"grade": "C24", "section": {"type": "cir", "d": 200}, "moisture_class": 1, "N": {"value": -120, "unit": "kN"}, "M_y": _kNm(4), "a": None, "l_y": 3500, "l_z": 3500},
    )):
        add(_kind("lateral-torsional", id="KI-%d" % i, **change))
    # shear: one plane, two planes, the pith, a round section, glulam in moisture class 3
    for i, change in enumerate((
        {"V_z": {"value": 10, "unit": "kN"}},
        {"V_z": {"value": 8, "unit": "kN"}, "V_y": {"value": -3000, "unit": "N"}, "pith": True},
        {"position": "R001", "V_z": None, "V_y": {"value": 5, "unit": "kN"}},
        {"grade": "GL24h", "section": {"type": "rec", "b": 120, "h": 400}, "moisture_class": 3, "V_z": {"value": 40, "unit": "kN"}, "impact": True},
        {"grade": "GL24h", "section": {"type": "rec", "b": 120, "h": 240}, "moisture_class": 1, "V_z": {"value": 12, "unit": "kN"}, "pith": True},
    )):
        add(_kind("shear", id="SS-%d" % i, **change))
    return out


def _synthetic_fire():
    """Issue #46 -- the fire situation, held apart from `_synthetic` so that each compile stays well under the runner's 300 s: every kind it takes, three and four faces and one, softwood, glulam (no k_h), oak and cladding, a moisture class 2, a normal force either way."""
    out = []

    def add(src):
        rec = member_check.resolve(src, POSITIONS)
        assert rec["calculable"], (src, rec["reason"])
        rec["position_found"] = rec["position"] in ("T001", "S001")
        out.append(rec)

    def fire(duration, *sides, wood=None):
        return {"duration": duration, "sides": {s: s in sides for s in ("bottom", "top", "left", "right")}, "wood": wood, "top_level": False}
    for i, (kind, change) in enumerate((
        ("bending", {"grade": "C24", "section": {"type": "rec", "b": 140, "h": 200}, "moisture_class": 1, "M_y": _kNm(2), "fire": fire(60, "bottom", "left", "right")}),
        ("bending", {"grade": "GL24h", "section": {"type": "rec", "b": 160, "h": 320}, "moisture_class": 2, "M_y": _kNm(20), "M_z": _kNm(1), "fire": fire(30, "bottom")}),
        ("bending", {"grade": "GL24h", "section": {"type": "rec", "b": 160, "h": 240}, "moisture_class": 1, "N": {"value": 20, "unit": "kN"}, "M_y": _kNm(5), "fire": fire(30, "bottom", "top", "left", "right")}),
        ("bending", {"grade": "GL24h", "section": {"type": "rec", "b": 160, "h": 280}, "moisture_class": 1, "N": {"value": -30, "unit": "kN"}, "M_y": _kNm(3), "fire": fire(30, "bottom", "left", "right", wood="cladding")}),
        ("shear", {"grade": "C24", "section": {"type": "rec", "b": 140, "h": 240}, "moisture_class": 1, "V_z": {"value": 10, "unit": "kN"}, "fire": fire(60, "bottom", "left", "right")}),
        ("shear", {"grade": "D30", "section": {"type": "rec", "b": 160, "h": 200}, "moisture_class": 2, "V_z": {"value": 8, "unit": "kN"}, "V_y": {"value": 2, "unit": "kN"}, "fire": fire(30, "bottom", "left", wood="oak")}),
        ("buckling", {"grade": "D30", "section": {"type": "rec", "b": 140, "h": 240}, "moisture_class": 1, "N": {"value": 185, "unit": "kN"}, "l_y": 2400, "l_z": 2400, "fire": fire(30, "bottom", "top", "left", "right", wood="oak")}),
        ("buckling", {"grade": "GL24h", "section": {"type": "rec", "b": 200, "h": 200}, "moisture_class": 2, "N": {"value": 100, "unit": "kN"}, "l_y": 3000, "l_z": 3000, "fire": fire(60, "bottom", "top", "left", "right")}),
        ("compression", {"grade": "C24", "section": {"type": "rec", "b": 160, "h": 160}, "moisture_class": 1, "N": {"value": 50, "unit": "kN"}, "fire": fire(30, "left", "right")}),
        ("tension", {"grade": "GL24h", "section": {"type": "rec", "b": 140, "h": 200}, "moisture_class": 1, "N": {"value": 40, "unit": "kN"}, "fire": fire(30, "bottom", "top", "left", "right")}),
    )):
        src = _kind(kind, id="FE-S%d" % i, **change)
        member_check.stamp_version(src)
        member_check.check_source(src, "FE-S%d" % i)
        add(src)
    return out


def _oracle_rows(kind, grade, section, fields):
    src = member_check.new_source("X-1", kind)
    src.update(position=None, grade=grade, section=section, moisture_class=1, **fields)
    rec = member_check.resolve(src, {})
    assert rec["calculable"], (kind, rec["reason"])
    return {row["key"]: row["value"] for row in member_check.compute(rec)["rows"]}


def test_the_worked_examples_of_the_oracles():
    """Every case of tests/fixtures/timber-oracles.json that carries a call, computed by member_check as the export computes it, to the digits its source prints (the case's tolerance) -- each held here or said not computed, with its reason."""
    cases = [c for c in json.loads(ORACLES.read_text(encoding="utf-8"))["cases"] if c.get("typst")]
    assert {c["id"] for c in cases} == set(ORACLE_RECORDS) | set(ORACLE_NOT_COMPUTED), "a case of the fixture neither held nor said not computed"
    failures = []
    for case in cases:
        if case["id"] in ORACLE_NOT_COMPUTED:
            continue
        kind, grade, section, fields, keys = ORACLE_RECORDS[case["id"]]
        rows = _oracle_rows(kind, grade, section, fields)
        tol = case["typst"].get("tolerance", 0.005)
        for ours, theirs in keys.items():
            want = case["typst"]["expected"][theirs]
            if abs(rows[ours] - want) > tol * max(1.0, abs(want)):
                failures.append(f"{case['id']} {ours}: {rows[ours]} against {want} ({case['source']})")
    assert not failures, "\n  ".join(failures)


def test_a_simple_compression_and_a_simple_bending_have_no_eta_s_row():
    """Spec 2026-10-22-retrait-niveau-manuel, REQ-007: the `eta_s` row a compression along the grain and a bending carried for the level of detail -1 (issue #58), the verdict printed twice, is gone -- at normal temperature and in the fire situation; a buckling and a lateral torsional buckling keep theirs, a verdict among several that `eta` is the largest of."""
    def keys(kind, section, fields):
        return [row["key"] for row in member_check.compute(member_check.resolve(dict(member_check.new_source("X-1", kind), position=None, grade="C24", section=section, moisture_class=1, **fields), {}))["rows"]]
    for kind, section, fields in (("compression", _rec(120, 120), {"N": _kN(40), "alpha": 0}),
                                  ("compression", _rec(120, 300), {"N": _kN(30), "alpha": 90, "l": 160, "case": "mit_vorholz"}),
                                  ("bending", _rec(100, 240), {"M_y": _kNm(5.87)}),
                                  ("bending", _rec(120, 220), {"M_y": _kNm(6.82), "M_z": _kNm(2.1)}),
                                  ("bending", _rec(120, 220), {"M_y": _kNm(3), "N": _kN(20)}),
                                  ("bending", _rec(120, 220), {"M_y": _kNm(3), "N": _kN(-20)})):
        rows = keys(kind, section, fields)
        assert "eta_s" not in rows and rows[-1] == "eta", (kind, fields, rows)
    assert "eta_s" in keys("buckling", _rec(120, 120), {"N": _kN(40), "l_y": 3950, "l_z": 3950})
    assert "eta_s" in keys("lateral-torsional", _rec(180, 1440), {"M_y": _kNm(1035), "a": 5000})
    fire = {rec["kind"]: [row["key"] for row in member_check.compute(rec)["rows"]] for rec in reversed(_synthetic_fire())}
    assert "eta_s" not in fire["compression"] and "eta_s" not in fire["bending"], fire
    assert "eta_s" in fire["buckling"]


def test_the_buckling_tables_of_the_holzbautabellen():
    """Lignum HBT 1, p. 53 (C24) and p. 58 (GL24h): k_c · f_c,0,d against lambda_rel -- each row reached with the length that gives its lambda_rel exactly -- computed by member_check's buckling."""
    cases = [c for c in json.loads(ORACLES.read_text(encoding="utf-8"))["cases"] if "typst_table" in c]
    assert cases, "no HBT table in the oracles"
    failures = []
    for case in cases:
        t = case["typst_table"]
        member = dict(re.findall(r'([a-z-]+): "?([^",)]+)"?', t["member"]))
        for row in t["rows"]:
            rows = _oracle_rows("buckling", member["grade"], _rec(float(member["b"]), float(member["h"])), {"N": _kN(10), "l_y": row["l_k_mm"], "l_z": row["l_k_mm"]})
            value = rows["k_c_z"] * rows["f_c_0_d"]
            if abs(rows["lambda_rel_z"] - row["lambda_rel"]) > 1e-6 or abs(value - row["k_c_f_c_0_d"]) > t["tolerance"] * row["k_c_f_c_0_d"]:
                failures.append(f"{case['id']} lambda_rel {row['lambda_rel']}: {value:.4f} against {row['k_c_f_c_0_d']}")
    assert not failures, "\n  ".join(failures)
