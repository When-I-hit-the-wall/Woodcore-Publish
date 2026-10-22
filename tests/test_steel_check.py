"""The steel checks of lot 1: section class, tension, compression, bending, shear after SIA 263:2013 (issue #51, spec 2026-10-12-section-acier REQ-004 to REQ-006, REQ-013, D-09, D-17; calc/domains/steel_check.py, steel_section.py, steel_resistance.py, lib/steel.typ).

Every number below is worked out by hand from SZS C5's row and SIA 263's equations, never read back from the module -- an IPE 360 in S355 (A 7270 mm², W_pl,y 1020·10³ mm³, W_pl,z 191·10³ mm³, A_v 3514 mm², b 170, t_f 12.7, t_w 8, h 360, h_1 298; f_y 355, tau_y 205 N/mm², gamma_M1 1.05):

* (38) N_Rd = 355 · 7270 / 1.05 = 2457.95 kN -- the value the reference template prints in its Hilfstabelle Querschnittsklasse (`NRd,pl`, C6), to the digit;
* (40) M_y,Rd = 355 · 1020·10³ / 1.05 = 344.86 kNm, M_z,Rd = 64.58 kNm;
* (41) V_Rd = 205 · 3514 / 1.05 = 686.07 kN, and (42) (360 − 12.7)/8 = 43.4 ≤ sqrt(4 · 210000/355) = 48.6;
* (43) at V = 500 kN: 170·12.7·355·347.3/1.05 + 334.6²·8·355/(4·1.05)·(1 − (500/686.07)²) = 289.0 kNm;
* (48) at N = −300 kN, M_y 150, M_z 10 kNm: n = 0.122, a = (7270 − 2·170·12.7)/7270 = 0.406, M_y,N,Rd capped at M_y,Rd, n < a so M_z,N,Rd = M_z,Rd, beta = 1.1: (150/344.86)² + (10/64.58)^1.1 = 0.318.

Tabelle 5 for the same web, c/t = 298/8 = 37.25: class 4 in pure compression (42 epsilon = 34.17 with epsilon = 0.814 -- the reference template's H20 says 4 too), class 1 in pure bending (72 epsilon = 58.6), class 2 at N = 500 kN with M_y (alpha = (1 + 500·10³·1.05/(298·8·355))/2 = 0.810: 396 epsilon/(13 alpha − 1) = 33.8 < 37.25 ≤ 456 epsilon/(13 alpha − 1) = 38.9).
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import math
import subprocess

import conftest
from conftest import PROJECT, ROOT, TYPST_ROOT, Skip
from domains import steel_check, steel_section
import validation


def _close(a, b, rel=2e-3):
    assert abs(a - b) <= rel * max(abs(a), abs(b), 1e-9), (a, b)


def _src(kind, cid="X", **fields):
    src = steel_check.new_source(cid, kind)
    src.update(profile={"type": "IPE", "dimension": "360"}, grade="S355")
    src.update(fields)
    return steel_check.check_source(src)


def _run(kind, **fields):
    record = steel_check.resolve(_src(kind, **fields), {})
    assert record["calculable"], record["reason"]
    return steel_check.exported(record)


def _v(out, key):
    return out["vars"][key]["value"]


def test_the_section_class_follows_tabelle_5_and_the_reference_template():
    """REQ-005: the IPE 360's web under pure compression, pure bending, and compression with bending."""
    sec = steel_section.of_c5("IPE", [360])
    assert steel_section.classify(sec, 355, N=1)["class"] == 4
    web = [w for w in steel_section.classify(sec, 355, N=1)["walls"] if w["name"] == "Steg"][0]
    _close(web["ratio"], 37.25) and _close(web["limits"][2], 34.17)
    assert steel_section.classify(sec, 355, M_y=1e8)["class"] == 1
    mixed = steel_section.classify(sec, 355, N=500e3, M_y=1e8)
    web = [w for w in mixed["walls"] if w["name"] == "Steg"][0]
    _close(web["alpha"], 0.5 * (1 + 500e3 * 1.05 / (298 * 8 * 355)))
    assert mixed["class"] == 2
    flange = [w for w in mixed["walls"] if w["name"].startswith("Flansch")][0]
    _close(flange["ratio"], (170 - 8 - 2 * 18) / 2 / 12.7)
    assert flange["class"] == 1, "(a − r)/t_f = 4.96 ≤ 9 epsilon = 7.32"
    assert steel_section.classify(sec, 355)["class"] == 1, "a wall nowhere compressed is not classified"
    assert steel_section.classify(steel_section.of_c5("RND", [50]), 355, N=1e5)["class"] == 1
    tube = steel_section.classify(steel_section.of_c5("ROR", [323.9, 5.6]), 355, N=1e5)
    _close(tube["walls"][0]["ratio"], 323.9 / 5.6) and _close(tube["walls"][0]["limits"][2], 90 * 0.8136 ** 2)


def test_tension_and_compression_of_the_section():
    """REQ-006: (38), (39), and a compression refused in class 4, accepted on a stockier HEB 200."""
    out = _run("tension", N={"value": 1000, "unit": "kN"})
    _close(_v(out, "N_Rd"), 2457.95)
    _close(out["eta"], 1000 / 2457.95)
    assert out["ratio"] == "N_Ed / N_Rd" and "eta" not in out["vars"], "the verdict prints η, the rows do not"
    net = _run("tension", N={"value": 1000, "unit": "kN"}, A_net=6000)
    _close(_v(net, "N_Rd_net"), 0.9 * 510 * 6000 / 1.25 / 1000)
    _close(_v(net, "N_Rd"), min(2457.95, 0.9 * 510 * 6000 / 1.25 / 1000))
    record = steel_check.resolve(_src("compression", N={"value": -1000, "unit": "kN"}), {})
    out = steel_check.exported(record)
    assert not out["calculable"] and "class 4" in out["reason"] and "4.5.3" in out["reason"]
    heb = steel_check.exported(steel_check.resolve(_src("compression", N={"value": -1000, "unit": "kN"}, profile={"type": "HEB", "dimension": "200"}), {}))
    assert heb["calculable"] and heb["class"] == 1
    _close(_v(heb, "N_Rd"), 355 * 7810 / 1.05 / 1000)


def test_bending_alone_and_with_a_normal_force():
    """REQ-006: (40) alone; (48) with its alpha 2 and beta max(5 n, 1.1) for a doubly symmetric I; (44) for a U."""
    out = _run("bending", M_y={"value": 200, "unit": "kNm"})
    _close(_v(out, "M_y_Rd"), 344.857)
    _close(out["eta"], 200 / 344.857)
    out = _run("bending", N={"value": -300, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"}, M_z={"value": 10, "unit": "kNm"})
    _close(_v(out, "M_y_N_Rd"), 344.857) and _close(_v(out, "M_z_N_Rd"), 64.576)
    n = 300 / 2457.95
    _close(out["eta"], (150 / 344.857) ** 2 + (10 / 64.576) ** max(5 * n, 1.1))
    assert out["ratio"].startswith("(M_y_Ed / M_y_N_Rd)^2 + (M_z_Ed / M_z_N_Rd)^")
    upe = _run("bending", profile={"type": "UPE", "dimension": "200"}, N={"value": -100, "unit": "kN"}, M_y={"value": 30, "unit": "kNm"})
    assert upe["ratio"] == "abs(N_Ed) / N_Rd + M_y_Ed / M_y_Rd"
    _close(upe["eta"], 100 / (355 * 2900 / 1.05e3) + 30 / (355 * 220e3 / 1.05e6))


def test_shear_and_its_interaction_with_bending():
    """REQ-006: (41), (42), and (43) beyond 0.5 V_Rd."""
    out = _run("shear", V_z={"value": 500, "unit": "kN"})
    _close(_v(out, "V_z_Rd"), 205 * 3514 / 1.05 / 1000)
    _close(_v(out, "web_slenderness"), 347.3 / 8) and _close(_v(out, "web_limit"), math.sqrt(4 * 210000 / 355))
    out = _run("shear", V_z={"value": 500, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"})
    v_rd = 205 * 3514 / 1.05
    m_v = 170 * 12.7 * 355 * 347.3 / 1.05 + 334.6 ** 2 * 8 * 355 / (4 * 1.05) * (1 - (500e3 / v_rd) ** 2)
    _close(_v(out, "M_V_Rd") * 1e6, m_v)
    _close(out["eta"], max(500e3 / v_rd, 150e6 / m_v))
    low = _run("shear", V_z={"value": 100, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"})
    assert "M_V_Rd" not in low["vars"], "at most 0.5 V_Rd the bending resistance stands (5.1.5.1)"
    tube = _run("shear", profile={"type": "ROR", "dimension": "101.6x10"}, V_z={"value": 50, "unit": "kN"})
    assert "Schubbeulen nach 4.5.4 nicht nachgewiesen (5.1.4.2)." in tube["notes"]


def test_a_check_follows_its_position_and_says_what_it_lacks():
    """REQ-004: the profile and the grade follow the position unless stated; a missing input is a reason, never a stop."""
    positions = {"S010": {"position": "S010", "section": {"type": "HEA", "kind": "steel", "text": "HEA 200", "dims": [200]}, "strength_class": "S235"}}
    src = steel_check.new_source("ST-01", "bending")
    src.update(position="S010")
    record = steel_check.resolve(src, positions)
    assert record["calculable"] and record["designation"] == "HEA 200" and record["grade"] == "S235"
    assert (record["profile_from"], record["grade_from"]) == ("position", "position")
    src.update(grade="S355", profile={"type": "HEB", "dimension": "200"})
    record = steel_check.resolve(src, positions)
    assert (record["profile_from"], record["grade_from"]) == ("stated", "stated") and record["designation"] == "HEB 200"
    for change, said in (({"position": "S999"}, "no profile"), ({"position": None}, "no profile")):
        bare = steel_check.new_source("ST-02", "bending")
        bare.update(change)
        record = steel_check.resolve(bare, positions)
        assert not record["calculable"] and said in record["reason"], record["reason"]
    timber = {"T001": {"position": "T001", "section": {"type": "rec", "kind": "timber", "text": "100/200 mm", "b": 100, "h": 200}, "strength_class": "C24"}}
    bare = steel_check.new_source("ST-03", "bending")
    bare.update(position="T001")
    record = steel_check.resolve(bare, timber)
    assert not record["calculable"] and "not a steel section" in record["reason"]
    assert [n.code for n in record["warnings"]] == ["steel_not_calculable"]
    bare.update(grade=None, profile={"type": "IPE", "dimension": "200"}, position=None)
    assert "no steel grade" in steel_check.resolve(bare, {})["reason"]
    wrong = dict(bare, profile={"type": "IPE", "dimension": "999"}, grade="S355")
    assert "not in the tables" in steel_check.resolve(wrong, {})["reason"]


def test_a_malformed_source_is_refused_naming_the_field():
    good = _src("bending")
    for change, said in (({"schema_version": "2.0"}, "schema_version"), ({"id": "A B"}, "id"), ({"kind": "torsion"}, "kind"),
                         ({"kind": "buckling"}, "not implemented"), ({"grade": "S999"}, "grade"), ({"profile": {"type": "rec", "dimension": "100/200"}}, "not a steel one"),
                         ({"profile": {"type": "IPE", "dimension": "abc"}}, "IPE"), ({"N": {"value": 1, "unit": "kNm"}}, "N"), ({"A_net": 0}, "A_net")):
        try:
            steel_check.check_source(dict(good, **change))
        except validation.ValidationError as exc:
            assert said in str(exc), (change, str(exc))
        else:
            raise AssertionError("accepted %r" % (change,))


def _export(*sources):
    here = PROJECT
    here.steel_dir.mkdir(parents=True, exist_ok=True)
    for old in here.steel_dir.glob("*.json"):
        old.unlink()
    for src in sources:
        (here.steel_dir / ("%s.json" % src["id"])).write_text(json.dumps(src), encoding="utf-8")
    data = steel_check.prepare(here, {})
    steel_check.write(data, here.data_dir)
    return data


def _compile(body, name="steel_check"):
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    from pypdf import PdfReader
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        return None, conftest.panic_message(out.stderr) or out.stderr
    return "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages), None


def test_the_export_is_valid_and_the_report_prints_it():
    """REQ-013, D-17: data/steel.json against its schema; the check's domain as Woodcore writes it out (spec 2026-10-21-commandes-typst-refonte, REQ-017; `#show-check-steel` until then) printed at levels 1 to 3 with its verdict; a check not calculable written out by nothing."""
    import project
    from domains import steel_check, unfold
    data = _export(_src("bending", "ST-01", M_y={"value": 200, "unit": "kNm"}), _src("shear", "ST-02", V_z={"value": 500, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"}),
                   _src("compression", "ST-03", N={"value": -1000, "unit": "kN"}), _src("class", "ST-04", N={"value": -500, "unit": "kN"}, M_y={"value": 100, "unit": "kNm"}))
    validation.validate_structure(data, "steel")
    assert set(data["checks"]) == {"ST-01", "ST-02", "ST-03", "ST-04"} and not data["checks"]["ST-03"]["calculable"]
    records = unfold._module("steel").records(data)
    assert not steel_check.is_unfolded(records["ST-03"]), "a check not calculable is said by its reason and printed by nothing"

    def written(rid):
        with project.using(conftest.PROJECT):
            return unfold.generate(records[rid], "de", "steel").split("\n", 1)[1]

    for level in (1, 2, 3):
        text, error = _compile('#calc-defaults(level: %d, scope: "document")\n' % level + written("ST-01"))
        assert text is not None, error
        assert "ST-01" in text and "IPE 360" in text and "✔" in text, (level, text)
    text, _ = _compile('#calc-defaults(level: 3, scope: "document")\n' + written("ST-01"))
    assert "344" in text, "M_y,Rd at level 3"
    for rid in ("ST-02", "ST-04"):
        text, error = _compile(written(rid))
        assert text is not None, (rid, error)
    text, error = _compile('#ids("check-steel").join(", ")')
    assert text is not None and "ST-04" in text, error


def test_every_word_of_the_rows_is_in_the_glossary():
    """ARCH-RISK-204: every label, step name, table title, column and note the export writes is a term of calc/i18n/strings.json (fr, en), and every engine key lib/steel.typ prints is there too."""
    words = json.loads((ROOT / "calc" / "i18n" / "strings.json").read_text(encoding="utf-8"))
    terms, engine = words["terms"], words["engine"]
    # every kind, and every branch that adds words of its own: (39), (48) of an I and of a rolled RHS, (43), a tube's note
    data = _export(_src("tension", "W-1", A_net=6000), _src("compression", "W-2", N={"value": -500, "unit": "kN"}, profile={"type": "HEB", "dimension": "200"}),
                   _src("bending", "W-3", N={"value": -300, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"}, M_z={"value": 10, "unit": "kNm"}),
                   _src("bending", "W-4", N={"value": -100, "unit": "kN"}, M_y={"value": 20, "unit": "kNm"}, M_z={"value": 5, "unit": "kNm"}, profile={"type": "RRW", "dimension": "200x100x10"}),
                   _src("shear", "W-5", V_z={"value": 500, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"}),
                   _src("shear", "W-6", V_z={"value": 50, "unit": "kN"}, profile={"type": "ROR", "dimension": "101.6x10"}),
                   _src("class", "W-7", N={"value": -500, "unit": "kN"}, M_y={"value": 100, "unit": "kNm"}))
    assert all(r["calculable"] for r in data["checks"].values()), {k: r["reason"] for k, r in data["checks"].items() if not r["calculable"]}
    seen = set()
    for record in data["checks"].values():
        for v in record.get("vars", {}).values():
            seen.add(v["label"])
        for st in record.get("steps", []):
            seen.add(st["name"])
        for t in record.get("tables", []):
            seen.add(t["title"]) or seen.add(t["note"])
            seen |= {c["label"] for c in t["columns"] if c["label"] not in ("c", "t", "c/t")}
            seen |= {row[0] for row in t["rows"]}
        seen |= set(record.get("notes", []))
    missing = sorted(w for w in seen if w not in terms and w)
    assert not missing, missing
    for kind in steel_check.IMPLEMENTED:
        assert "steel.kind.%s" % kind in engine
    for kind in ("tension", "compression", "bending", "shear"):
        assert "summary.verify.steel-%s" % kind in engine
