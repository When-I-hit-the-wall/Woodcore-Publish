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
from domains import connector, member_check
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
    # and the draft then names no position, which #member would refuse
    assert "position: none" in member_check.draft_typst(rec)


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
    assert data["schema_version"] == "1.2"
    assert (data["checks"]["FE-01"]["fire"]["duration"], data["checks"]["FE-01"]["fire"]["duration_from"]) == (60, "vkf")
    assert (data["checks"]["FE-02"]["fire"]["duration"], data["checks"]["FE-02"]["fire"]["duration_from"]) == (30, "stated")
    assert data["checks"]["FE-01"]["calculable"] and data["checks"]["FE-02"]["calculable"]


# --- the report ---------------------------------------------------------------------

def _compile(body, name="member_check"):
    """`body` compiled after the report's import; (pdf text, None) or (None, panic message or error)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    from pypdf import PdfReader
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        return None, conftest.panic_message(out.stderr) or out.stderr
    return "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages), None


def _text(body, name="member_check"):
    text, error = _compile(body, name)
    assert text is not None, f"did not compile:\n{error}"
    return text


def test_show_check_member_compiles_at_three_levels_and_prints_the_verdict():
    for level in (1, 2, 3):
        text = _text(f'#show-check-member("ZT-01", level: {level})')
        assert "T001" in text and "✔" in text, (level, text)
    text = _text('#show-check-member("ZT-02", level: 3)')
    assert "ZT-02" in text and "4.2.1.3" in text


def test_show_check_member_prints_what_the_draft_prints():
    data = conftest.exported(member_check.EXPORT_FILE)
    for cid, options in (("ZT-01", {}), ("ZT-02", {"level": 3, "member_level": 2, "unit": "%"}),
                         ("DR-01", {"level": 3}), ("DR-02", {"level": 2, "unit": "%"}),
                         ("BI-01", {"level": 3}), ("BI-02", {"level": 2}), ("BI-03", {"level": 3, "unit": "%"}),
                         ("KN-01", {"level": 3}), ("KI-01", {"level": 2}), ("KI-02", {"level": 3}), ("SC-01", {"level": 3}),
                         ("FE-01", {"level": 3}), ("FE-02", {"level": 2, "member_level": 2})):
        typst_args = ", ".join([f'"{cid}"'] + [
            {"level": f"level: {options.get('level')}", "member_level": f"member-level: {options.get('member_level')}", "unit": f'unit: "{options.get("unit")}"'}[k]
            for k in options])
        shown = _text(f"#show-check-member({typst_args})", "member_check_shown")
        drafted = _text(member_check.draft_typst(data["checks"][cid], **options), "member_check_draft")
        assert shown == drafted, f"{cid}:\n{shown}\n--- draft ---\n{drafted}"


def test_at_minus_one_show_check_member_prints_what_the_draft_prints_and_the_window_offers_what_it_accepts():
    """Issue #20 (CON-005, D-11, D-15): at level -1 the report's call and the window's draft print the same page, the member's keys to the member and the check's to the check; the keys the window offers for each check are keys `#show-check-member` accepts, the member's first, and every one of them compiles."""
    import shown_variables
    from tools import build_reference
    data = conftest.exported(member_check.EXPORT_FILE)
    for cid in ("ZT-02", "DR-01", "BI-01", "BI-03", "KN-01", "KI-02", "SC-01", "FE-01", "FE-02"):
        record = data["checks"][cid]
        offered = member_check.shown_keys(record)
        accepted = shown_variables.check_member_keys(record)
        assert offered and set(offered) <= set(accepted), (cid, sorted(set(offered) - set(accepted)))
        own = shown_variables.keys(shown_variables.check_command(record))
        first_own = next(i for i, k in enumerate(offered) if k in own)
        assert all(k in own for k in offered[first_own:]), (cid, offered)
        chosen = {key: 1 + i % 3 for i, key in enumerate(offered)}
        call = build_reference.call_show_check_member(cid, level=-1, shown=chosen)
        shown = _text(call, "member_check_minus1")
        drafted = _text(member_check.draft_typst(record, level=-1, shown=chosen), "member_check_minus1_draft")
        assert shown == drafted, f"{cid}:\n{shown}\n--- draft ---\n{drafted}"
    round_check = dict(data["checks"]["ZT-01"], section={"type": "cir", "d": 120})
    assert "W_z" not in member_check.shown_keys(round_check) and "W_z" in member_check.shown_keys(data["checks"]["ZT-01"])


def test_the_verdicts_the_window_offers_are_exactly_those_the_page_prints():
    """ARCH-001, UI-002 (issue #58): for every kind of check, the verdicts `shown_keys` offers -- the keys of the utilisations, `eta`, `eta_s`, `eta_y`… -- are the verdicts `#show-check-member` prints: each one alone prints one verdict, all of the command's prints as many as are offered, none prints none; each is offered by its row's symbol."""
    import shown_variables
    from tools import build_reference
    data = conftest.exported(member_check.EXPORT_FILE)
    marks = lambda text: text.count("✔") + text.count("✘")
    for cid in ("ZT-01", "ZT-02", "DR-01", "DR-02", "BI-01", "BI-02", "BI-03", "KN-01", "KI-01", "KI-02", "SC-01", "FE-01"):
        record = data["checks"].get(cid)
        if record is None:
            continue
        own = shown_variables.keys(shown_variables.check_command(record))
        verdicts = [key for key in member_check.shown_keys(record) if key.startswith("eta") and key in own]
        assert verdicts, cid
        symbols = {key: math for key, _w, math in member_check.shown_choices(record) if key in verdicts}
        assert all(symbols[key] and symbols[key].startswith("eta") for key in verdicts), (cid, symbols)
        every = {key: 1 for key in own if key.startswith("eta")}
        text = _text(build_reference.call_show_check_member(cid, level=-1, shown=every), "member_check_verdicts_" + cid)
        assert marks(text) == len(verdicts), (cid, verdicts, text)
        for key in verdicts:
            text = _text(build_reference.call_show_check_member(cid, level=-1, shown={key: 1}), "member_check_verdict_" + cid)
            assert marks(text) == 1, (cid, key, text)
        assert marks(_text(build_reference.call_show_check_member(cid, level=-1, shown={}), "member_check_verdict_none")) == 0, cid


def test_an_unknown_id_and_an_uncalculable_check_are_refused():
    text, error = _compile('#show-check-member("NOPE")')
    assert text is None and "NOPE" in error and "ZT-01" in error
    path = project.current().data_dir / member_check.EXPORT_FILE
    kept = path.read_bytes()
    try:
        data = json.loads(kept)
        planted = copy.deepcopy(data["checks"]["ZT-01"])
        planted.update(id="ZT-X", calculable=False, reason="position T999 is gone")
        data["checks"]["ZT-X"] = planted
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        text, error = _compile('#show-check-member("ZT-X")', "member_check_refused")
        assert text is None and "T999 is gone" in error, error
        # the draft of an uncalculable record is the same refusal
        text, error = _compile(member_check.draft_typst(planted), "member_check_refused_draft")
        assert text is None and "T999 is gone" in error, error
    finally:
        path.write_bytes(kept)


def test_member_level_none_prints_no_member_line_and_unit_percent():
    text = _text('#show-check-member("ZT-01", member-level: none, level: 1)')
    assert "Träger" not in text and "✔" in text
    text = _text('#show-check-member("ZT-01", level: 3, unit: "%")')
    assert "%" in text
    text = _text('#show-check-member("ZT-01", member-level: none, level: 1)\n#val("eta", domain: "ZT-01-verify-tension", type: "expression")')
    assert "0.184" in text


def test_check_member_ids_lists_the_checks():
    text = _text('#metadata(check-member-ids()) <ids>\n#check-member-ids().join(", ")')
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
    # the report reads the same value: moisture class 1 and no impact, so f_c,90,d is the table's own
    body = "".join(member_check.draft_typst(rec, level=0, member_level=None)
                   + '\n%s: #val("f_c_90_d", domain: "%s-verify-compression-perp", type: "val", level: 1)\n\n' % (rec["id"], rec["id"]) for rec, _ in records)
    text = _text(body, "member_check_cases")
    for rec, value in records:
        assert "%s: %s" % (rec["id"], member_check._fmt(value)) in text, (rec["id"], value, text)


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
    assert "w: 80" in member_check.draft_typst(rec) and "l: 120" in member_check.draft_typst(rec)
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
    draft = member_check.draft_typst(rec)
    assert "#verify-compression(" in draft and "stability: false" in draft and "l-k" not in draft and 'N: "-18 kN"' in draft
    text = _text('#show-check-member("DR-02", level: 2)', "member_check_dr02")
    assert "Stabilität" not in text and "Knicken" not in text and "✔" in text and "4.2.2.1" in text
    # its utilisation is the section's, published as eta
    text = _text('#show-check-member("DR-02", member-level: none, level: 0)\n#val("eta", domain: "DR-02-verify-compression", type: "expression", level: 1)', "member_check_dr02_eta")
    n_mm = 60e3 / (140 * 140)                                    # N/A in N/mm²
    eta = n_mm / sia265.grade("GL24h")["f_c_0_d"]                # moisture class 1, no impact
    assert member_check._fmt(round(eta, 3)) in text, (eta, text)


def test_a_compression_at_an_angle_reads_equation_13():
    rec = member_check.resolve(_compression(alpha=30, case="mit_vorholz", moisture_class=1), POSITIONS)
    assert rec["calculable"] and rec["alpha"] == 30
    text = _text(member_check.draft_typst(rec, level=3), "member_check_alpha30")
    assert "4.2.2.3" in text and ("✔" in text or "✘" in text)
    text = _text('#show-check-member("DR-01", level: 3)', "member_check_dr01")
    assert "4.2.2.2" in text and "Endauflagerung" in text


def test_verify_compression_keeps_its_stability_by_default():
    text, error = _compile('#member("S", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-compression("S", N: -60)', "member_check_stab_default")
    assert text is None and "buckling lengths" in error, error
    text = _text('#member("S", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-compression("S", N: -60, l: 3000, level: 2)', "member_check_stab_on")
    assert "Stabilität" in text and "Knicken" in text
    text = _text('#member("S", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-compression("S", N: -60, stability: false, level: 2)', "member_check_stab_off")
    assert "Stabilität" not in text and "Knicken" not in text
    text, error = _compile('#member("S", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-compression("S", N: -60, stability: "no")', "member_check_stab_bad")
    assert text is None and "stability" in error, error


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


def test_a_bending_s_call_is_chosen_by_its_normal_force():
    pure = member_check.draft_typst(member_check.resolve(_bending(M_z=_kNm(-0.5)), POSITIONS))
    assert '#verify-bending("BI-99", M-y: "10 kNm", M-z: "0.5 kNm", alpha: 0, stability: false)' in pure, pure
    with_n = member_check.draft_typst(member_check.resolve(_bending(N={"value": -40, "unit": "kN"}), POSITIONS), level=2)
    assert '#verify-bending-normal("BI-99", N: "-40 kN", M-y: "10 kNm", alpha: 0, stability: false, level: 2)' in with_n, with_n
    angle = member_check.draft_typst(member_check.resolve(_bending(alpha=30, N={"value": 5, "unit": "kN"}), POSITIONS))
    assert "alpha: 30, stability: false" in angle and "M-z" not in angle


def test_a_bending_saved_in_woodcore_prints_the_section_alone():
    """`#show-check-member` of a bending: the section's check, no «Stabilität» part and no note on lateral torsional buckling (REQ-006); at an angle with a normal force the note that the norm does not write it."""
    text = _text('#show-check-member("BI-01", level: 2)\n#show-check-member("BI-02", level: 2)', "member_check_bending")
    assert "Stabilität" not in text and "Kippen" not in text and "✔" in text, text
    assert "4.2.3.1" in text and "4.2.4.2" in text
    text = _text('#show-check-member("BI-03", level: 2)', "member_check_bending_angle")
    assert "nur in Faserrichtung" in text and "4.2.4.1" in text, text


def test_a_bending_that_cannot_be_checked_is_refused_by_the_report_with_its_reason():
    """REQ-007: a bending exported `calculable: false` -- no moment, or M_z at an angle -- is refused by `#show-check-member` with the reason `resolve` gave, and its draft by the very same panic."""
    path = project.current().data_dir / member_check.EXPORT_FILE
    kept = path.read_bytes()
    try:
        data = json.loads(kept)
        for cid, change, words in (("BI-X1", {"M_y": None}, "no moment"), ("BI-X2", {"alpha": 20, "M_z": _kNm(1)}, "read M_y alone")):
            rec = member_check.resolve(_bending(id=cid, **change), POSITIONS)
            assert not rec["calculable"] and words in rec["reason"], rec["reason"]
            rec["warnings"] = [str(note) for note in rec["warnings"]]
            rec["position_found"] = True
            data["checks"][cid] = rec
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        for cid, words in (("BI-X1", "no moment"), ("BI-X2", "read M_y alone")):
            text, error = _compile('#show-check-member("%s")' % cid, "member_check_bending_refused")
            assert text is None and cid in error and words in error, error
            text, error = _compile(member_check.draft_typst(data["checks"][cid]), "member_check_bending_refused_draft")
            assert text is None and words in error, error
    finally:
        path.write_bytes(kept)


# --- the instant calculation, held equal to the report's ---------------------------

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


def _kind(kind, **change):
    src = member_check.new_source("X-99", kind)
    src.update(position="T001")
    src.update(change)
    return src


def _registry(records, name):
    """The variable registry the report ends on, for the drafts of `records` compiled at level 0 -- read with `typst eval`, as calc/variables.py reads a report's."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import variables
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/commands.typ": *\n' + "".join(member_check.draft_typst(r, level=0, member_level=None) for r in records), encoding="utf-8")
    out = subprocess.run(["typst", "eval", "--in", str(probe), "--root", str(TYPST_ROOT), "--format", "json", variables.expression()],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)["domains"]


def test_compute_gives_none_where_the_report_refuses():
    assert member_check.compute(None) is None
    rec = member_check.resolve(_compression(N={"value": 0, "unit": "kN"}), POSITIONS)
    assert member_check.compute(rec) is None
    rec = member_check.resolve(_good(), POSITIONS)
    result = member_check.compute(rec)
    assert set(result) == {"kind", "equation", "clause", "rows", "eta", "ok", "relation", "ratio"}
    assert all({"key", "symbol", "value", "unit"} <= set(row) for row in result["rows"])
    assert [row["key"] for row in result["rows"]][-1] == "eta" and result["rows"][-1]["value"] == result["eta"]


def test_compute_in_the_fire_situation_is_what_the_report_computes():
    """Issue #46, ARCH-004: the window's rows of a check in the fire situation -- the residual section, d_ef, beta_n, k_fi, then the check on it -- are the report's, within 1e-6, for the example's FE-01, FE-02 and ten synthetic cases."""
    data = conftest.exported(member_check.EXPORT_FILE)
    seen = _held_equal([data["checks"][cid] for cid in ("FE-01", "FE-02")] + _synthetic_fire(), "member_check_compute_fire")
    assert {"t_fi", "beta_n", "d_char_n", "d_red", "d_ef", "b", "h", "k_fi", "f_m_y_d", "tau_d", "k_c_z", "sigma_t_0_d", "sigma_c_0_d"} <= seen, seen


def test_compute_is_what_the_report_computes():
    data = conftest.exported(member_check.EXPORT_FILE)
    records = [data["checks"][cid] for cid in ("ZT-01", "ZT-02", "DR-01", "DR-02", "BI-01", "BI-02", "BI-03")] + _synthetic()
    seen = _held_equal(records, "member_check_compute")
    _branches(records, seen)


def _held_equal(records, name):
    """Each record's `compute` against the registry Typst ends on for its draft: every row within 1e-6, the relation and the ratio in the registry's keys, the ratio worked out on the registry equal to eta. Gives the row keys compared."""
    domains = _registry(records, name)
    seen = set()
    for rec in records:
        result = member_check.compute(rec)
        import shown_variables
        command = shown_variables.check_command(rec)    # the one place Python decides it (ARCH-RISK-101); the registry below is what Typst decided
        check = domains["%s-%s" % (rec["id"], command)]
        member = domains[rec["id"]]
        assert result["equation"] and result["clause"]
        # the relation is the norm's, in the registry's keys -- a stress against a strength, or a sum of ratios
        names = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", result["relation"])) - {"dot"}
        assert names and all(name in check or name in member for name in names), (rec["id"], result["relation"])
        for row in result["rows"]:
            held = check.get(row["key"]) or member.get(row["key"])   # a check copies its member's values; a value of its own is in its domain
            assert held is not None, (rec["id"], row["key"])
            value = held["value"]
            if row["key"].startswith("eta") and held.get("unit") == "%":   # every verdict's utilisation, eta_s… too (issue #58)
                value /= 100
            # a force is kept in the unit the call wrote it in; compute gives kN
            value *= {"N": 1e-3, "MN": 1e3}.get(held.get("unit"), 1) if row["unit"] == "kN" else 1
            value *= {"Nm": 1e-3, "MNm": 1e3}.get(held.get("unit"), 1) if row["unit"] == "kNm" else 1
            assert abs(value - row["value"]) <= 1e-6 * max(1, abs(row["value"])), (rec["id"], row["key"], value, row["value"], held.get("unit"))
            seen.add(row["key"])
        assert result["ok"] == (result["eta"] <= 1 + 1e-9)
        # issue #12: the ratio the window prints is the one the report prints -- its symbols the report's own, and its value, worked out on the report's registry, the utilisation
        expr = re.sub(r"([A-Za-z]+)_\(([^)]*)\)", lambda m: m.group(1) + "_" + m.group(2).replace(",", "_"), result["ratio"])
        names = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr)) - {"dot"}
        assert names and all(name in check or name in member for name in names), (rec["id"], result["ratio"])
        values = {name: (check.get(name) or member.get(name))["value"] for name in names}
        worked = eval(re.sub(r"[A-Za-z_][A-Za-z0-9_]*", lambda m: "*" if m.group(0) == "dot" else repr(values[m.group(0)]), expr).replace("^", "**"))   # noqa: S307 -- the engine's own formula, numbers only
        assert abs(worked - result["eta"]) <= 1e-6 * max(1, result["eta"]), (rec["id"], result["ratio"], worked, result["eta"])
    return seen


def _branches(records, seen):
    # every kind of row was compared at least once
    assert {"A", "A_c", "f_t_alpha_d", "f_c_alpha_d", "f_c_90_d", "sigma_c_0_d", "sigma_t_90_d", "eta"} <= seen, seen
    assert {"W_y", "W_z", "k_h_y", "k_h_z", "f_m_y_d", "f_m_z_d", "M_y_d", "M_z_d", "sigma_m_y_d", "sigma_m_z_d", "sigma_m_90_d", "sigma_m_alpha_d",
            "k_mc_alpha", "k_mt_alpha", "eta_m_t", "eta_m_c", "N_t_d", "N_c_d", "sigma_t_0_d", "sigma_t_alpha_d", "sigma_c_alpha_d"} <= seen, seen
    # issue #38: buckling, lateral torsional buckling and shear, every branch
    assert {"i_y", "i_z", "eta_w_E", "E_0_05", "f_c_0_k", "beta_c", "l_k_y", "l_k_z", "lambda_y", "lambda_rel_y", "k_y", "k_c_y", "k_c_z", "eta_s", "eta_y", "eta_z",
            "a", "sigma_m_crit", "f_m_k", "lambda_rel_m", "k_m", "eta_m", "V_z_d", "V_y_d", "tau_z_d", "tau_y_d", "tau_d", "f_v_d", "f_v_d_p"} <= seen, seen
    branches = set()
    for rec in records:
        keys = {row["key"]: row["value"] for row in member_check.compute(rec)["rows"]} if rec["kind"] == "lateral-torsional" else {}
        if "lambda_rel_m" in keys:   # a round section, or a wide one bent about its weak axis alone, tips about nothing (D-10, D-17)
            k_m, lam = keys["k_m"], keys["lambda_rel_m"]
            branches.add(0 if lam <= 0.75 else 1 if lam <= 1.4 else 2)
    assert branches == {0, 1, 2}, "k_m on each of the three branches of (39): %s" % branches


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
    """ARCH-RISK-104 (issue #38): the largest shear stress at the centroid, 1.5 V/A for a rectangle and 4/3 V/A for a circle, is mechanics -- SIA 265 (23) states tau_d <= f_v,d and no factor -- and lib/timber.typ writes the two factors member_check.SHEAR_FACTORS holds."""
    source = (conftest.ROOT / "lib" / "timber.typ").read_text(encoding="utf-8")
    assert member_check.SHEAR_FACTORS == {"rec": 1.5, "cir": 4 / 3}
    assert '"1.5 dot " + force + " / A"' in source and '"4/3 dot " + force + " / A"' in source
    assert "der Faktor 1.5 von Gleichung (23)" not in source


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


def _verdict_text(call, level, name):
    """The text of one verify-* command compiled alone at `level`, a member stated in the call (`_text`)."""
    return _text('#member("X", b: 100, h: 200, grade: "C24", moisture-class: 1, level: 0)\n' + call.replace("LEVEL", str(level)), name)


def test_the_verdict_is_the_ratio_against_one_and_never_eta():
    """Issue #12 (REQ-001, D-006, D-009, D-010): every verify-* prints the ratio of the action to the resistance against 1 -- at level 1 its symbols and its value, at 2 and 3 its symbols, numbers and value -- and neither the utilisation η nor the stress against the resistance; in percent the ratio in percent and nothing after it."""
    calls = {"tension": '#verify-tension("X", N: 25, level: LEVEL)',
             "compression": '#verify-compression("X", N: -40, l-k-y: 3000, l-k-z: 3000, level: LEVEL)',
             "bending": '#verify-bending("X", M-y: 5, stability: false, level: LEVEL)',
             "shear": '#verify-shear("X", V: 10, level: LEVEL)'}
    for kind, call in calls.items():
        for level in (1, 2, 3):
            text = _verdict_text(call, level, "verdict_%s_%d" % (kind, level))
            assert "η" not in text, (kind, level, text)
            assert "⩽" in text and re.search(r"⩽\s*1", text), (kind, level, text)
            assert not re.search(r"⩽\s*[fkτσ]", text), f"{kind} at level {level} prints a stress against a resistance: {text}"
            if level == 1:
                assert re.search(r"=\s*0\.\d+\s*⩽\s*1", text), f"{kind}: level 1 prints the ratio's value: {text}"
    text = _verdict_text('#verify-tension("X", N: 25, unit: "%", level: LEVEL)', 2, "verdict_percent")
    assert "%" in text and "100" not in text and "η" not in text, text


def test_eta_is_still_stored_and_read_where_nothing_prints_it():
    """REQ-002 (D-006): η stays the registry's value, read by #val and the summary of the checks, at every level."""
    for level in (0, 1, 3):
        text = _verdict_text('#verify-tension("X", N: 25, level: LEVEL)\n#val("eta", domain: "X-verify-tension")', level, "verdict_val_%d" % level)
        assert re.search(r"0\.\d+", text), (level, text)



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
