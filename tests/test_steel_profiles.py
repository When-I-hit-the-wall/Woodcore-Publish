"""The profile tables of SZS C5 (calc/norms/szs-c5-2018-profile-*.json, calc/norms/szs_c5.py) and the SIA 263 values of the steel checks (issue #50, spec 2026-10-12-section-acier REQ-001, REQ-002, ARCH-002).

The tables were read off renders of a scanned book, so three independent things hold them, none of which needs the scan's eyes:

* **the section's own mechanics**: i = sqrt(I/A), W_el = I/(h/2), A of an I section from h, b, t_w, t_f and r, a round tube's A, I, W_el and W_pl from D and t -- a digit misread in one column contradicts the others;
* **the reference extract** (tests/fixtures/steel-reference-profiles.json, the «Hilfstabelle Stahl-Profile» of the three steel check templates): every one of its values agrees with the table to its rounding, except the listed disagreements, each checked on a render of the page, where the page wins;
* **the reader's guards**: a table that names another edition, a row with a value missing or not above 0, a family that is no EDV code -- each planted and refused.
"""

import copy
import json
import math

import conftest
from conftest import ROOT
from norms import sia263, szs_c5
import validation

FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "steel-reference-profiles.json").read_text(encoding="utf-8"))
I_BEAMS = ("IPE", "IPEA", "HEA", "HEB", "HEM", "HD", "HL")
# the families whose h and b are the designation's numbers rather than a column of their table
DESIGNATED = ("ROR", "RND", "VKT", "RRK", "RRW", "L")


def _raised(fn, *args):
    try:
        fn(*args)
    except validation.ValidationError as exc:
        return str(exc)
    raise AssertionError("%s should have refused" % fn.__name__)


def _all():
    for code in szs_c5.tabulated():
        for size in szs_c5.sizes(code):
            yield code, size, szs_c5.profile(code, size.split("x"))


def test_every_family_is_tabulated_and_named_by_the_edv_list():
    """REQ-001: the twenty families of the three templates, each an EDV code, each table naming its page and the edition of the family list."""
    assert set(szs_c5.tabulated()) == {"IPE", "IPEA", "IPN", "UPE", "UPN", "HEA", "HEB", "HEM", "HD", "HL", "T", "IPET", "HEAT", "HEBT",
                                       "L", "RND", "VKT", "ROR", "RRK", "RRW"}
    assert set(szs_c5.tabulated()) <= set(szs_c5.codes())
    assert sum(len(szs_c5.sizes(code)) for code in szs_c5.tabulated()) == 1038
    for name in szs_c5.TABLE_NAMES:
        data = json.loads((ROOT / "calc" / "norms" / (name + ".json")).read_text(encoding="utf-8"))
        assert data["edition"] == szs_c5.edition() and "SZS-C5-2021.pdf" in data["_source"] and "PDF" in data["_source"], name


def test_a_profile_is_read_in_plain_mm_units():
    """The factor under each head is applied: IPE 360, p. 30 -- A 7270 mm², I_y 162,7·10⁶ mm⁴, W_pl,y 1020·10³ mm³, h_1 298 mm."""
    p = szs_c5.profile("IPE", [360])
    assert p["designation"] == "IPE 360" and p["A"] == 7270 and p["h_1"] == 298
    assert abs(p["I_y"] - 162.7e6) < 1e-3 and abs(p["W_pl_y"] - 1020e3) < 1e-6 and p["norm_ref"] == "pp. 30-31"
    assert szs_c5.profile("IPE", [361]) is None and szs_c5.profile("FLA", [100, 10]) is None


def test_halves_tubes_bars_and_angles_complete_their_rows():
    """A halved profile takes its parent's t_w, t_f, r; a round tube, a bar and a square tube have one I about both axes; an equal angle typed a×a×t is its a×t row, and its y and z are one column."""
    heat = szs_c5.profile("HEAT", [200])
    assert (heat["t_w"], heat["t_f"], heat["r"]) == (6.5, 10, 18) and heat["h"] == 95
    ror = szs_c5.profile("ROR", [101.6, 10])
    assert ror["I_y"] == ror["I_z"] and (ror["D"], ror["t"]) == (101.6, 10) and abs(ror["W_pl_z"] - 84.2e3) < 1e-6
    assert szs_c5.profile("ROR", [457, 6.3])["W_pl_y"] is None, "■: no plastic method"
    rect = szs_c5.profile("RRW", [200, 100, 5])
    assert abs(rect["I_y"] - 14.9e6) < 1 and abs(rect["I_z"] - 5.05e6) < 1, "a rectangular tube keeps its two axes"
    sq = szs_c5.profile("RRW", [200, 10])
    assert sq == szs_c5.profile("RRW", [200, 200, 10]) and sq["I_y"] == sq["I_z"] and (sq["h"], sq["b"], sq["t"]) == (200, 200, 10)
    eq = szs_c5.profile("L", [100, 100, 10])
    assert eq == szs_c5.profile("L", [100, 10]) and eq["I_z"] == eq["I_y"] and eq["a"] == eq["b"] == 100
    uneq = szs_c5.profile("L", [100, 50, 8])
    assert abs(uneq["I_z"] - 0.197e6) < 1e-6 and uneq["e_z"] == 11.3


def test_the_rows_agree_with_the_sections_mechanics():
    """i = sqrt(I/A) in every family; W_el = I/(h/2) and A from the plates for the I beams; a round tube's A, I, W_el, W_pl from D and t; a bar's from its side. Within the rounding of the print, a few per thousand; the values of `ANOMALIES` are the book's and are skipped where they are concerned."""
    checked = 0
    for code, size, p in _all():
        skip = set(p["anomalies"])
        for I, i in (("I_y", "i_y"), ("I_z", "i_z")):
            if p.get(I) and p.get(i) and I not in skip and i not in skip:
                rel = 0.6 * 10 ** (math.floor(math.log10(p[i])) - 2) / p[i] + 0.004
                printed = 0.5 if float(p[i]).is_integer() else 0   # a radius the page prints whole (RRW 500×200: «85», «83»)
                assert abs(p[i] - math.sqrt(p[I] / p["A"])) <= max(rel * p[i], printed) + 0.06, (code, size, i)
                checked += 1
        if code in I_BEAMS:
            h, b, tw, tf, r = p["h"], p["b"], p["t_w"], p["t_f"], p["r"]
            area = 2 * b * tf + (h - 2 * tf) * tw + (4 - math.pi) * r ** 2
            assert abs(p["A"] - area) <= 0.01 * area, (code, size, "A")
            assert abs(p["W_el_y"] - p["I_y"] / (h / 2)) <= 0.012 * p["W_el_y"], (code, size, "W_el_y")
        if code == "ROR":
            D, t = p["D"], p["t"]
            d = D - 2 * t
            assert abs(p["A"] - math.pi / 4 * (D ** 2 - d ** 2)) <= 0.012 * p["A"], (code, size)
            assert abs(p["I_y"] - math.pi / 64 * (D ** 4 - d ** 4)) <= 0.012 * p["I_y"], (code, size)
            if p["W_pl_y"] is not None and "W_pl" not in p["anomalies"]:
                assert abs(p["W_pl_y"] - (D ** 3 - d ** 3) / 6) <= 0.012 * p["W_pl_y"], (code, size)
    assert checked > 1500


def test_reference_extract_agrees_except_where_the_page_was_read_again():
    """REQ-001: every value of the templates' extract equals the table's to its rounding (1.2 %), but for the disagreements the fixture lists -- each read again on the page, which wins. A listed disagreement that no longer differs is stale and fails too."""
    rounding = FIXTURE["rounding"]
    listed = {k for k in FIXTURE["disagreements"] if not k.startswith("_")}
    family_of = {"PEA": "IPEA", "INP": "IPN", "UNP": "UPN", "HHD": "HD", "LNP": "L"}
    seen, compared, differing = set(), 0, set()
    for name, values in FIXTURE["profiles"].items():
        code, size = name.split(" ", 1)
        if name in listed:
            continue
        p = szs_c5.profile(code, size.split("x"))
        assert p is not None, "%s: in the templates, not in the tables" % name
        for key, value in values.items():
            if key in ("h", "b") and code in DESIGNATED:
                continue   # not a column of the table: the designation's own numbers
            mine = p.get(key)
            if mine is None:
                continue
            compared += 1
            if abs(mine - value) > rounding * abs(mine) + 1e-9:
                wild = "%s * %s" % (code, key)
                exact = "%s %s" % (name, key)
                assert wild in listed or exact in listed, "%s %s: templates %s, SZS C5 %s" % (name, key, value, mine)
                differing.add(wild if wild in listed else exact)
        seen.add(name)
    assert compared > 10000
    stale = {k for k in listed if " " in k and "*" not in k.split(" ", 1)[1] and len(k.split()) == 3} - differing
    assert not stale, "listed but no longer differing: %s" % sorted(stale)
    assert not family_of.keys() & {n.split()[0] for n in FIXTURE["profiles"]}, "the fixture is written in EDV codes"


def test_the_book_anomalies_are_said_where_they_are_read():
    p = szs_c5.profile("HD", [400, 1086])
    assert "A_v" in p["anomalies"] and p["A_v"] == 29580
    assert szs_c5.profile("HEA", [200])["anomalies"] == {}


def test_a_defective_table_is_refused_naming_the_file():
    """ARCH-002: another edition, a value missing or not above 0, a family that is no EDV code."""
    good = copy.deepcopy(json.loads((ROOT / "calc" / "norms" / "szs-c5-2018-profile-ipe.json").read_text(encoding="utf-8")))
    probe = conftest.tmpdir("szs_c5_tables")
    original = szs_c5.PATH

    def refused(doc):
        target = probe / "szs-c5-2018-profile-ipe.json"
        target.write_text(json.dumps(doc), encoding="utf-8")
        for name in szs_c5.TABLE_NAMES:
            if name != "szs-c5-2018-profile-ipe":
                (probe / (name + ".json")).write_text((original.parent / (name + ".json")).read_text(encoding="utf-8"), encoding="utf-8")
        (probe / original.name).write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
        szs_c5.PATH = probe / original.name
        szs_c5._cache.clear(), szs_c5._tables.clear()
        try:
            return _raised(szs_c5.check_tables)
        finally:
            szs_c5.PATH = original
            szs_c5._cache.clear(), szs_c5._tables.clear()

    doc = copy.deepcopy(good)
    doc["edition"] = "SZS C5:2005"
    assert "szs-c5-2018-profile-ipe" in refused(doc) and "edition" in refused(doc)
    doc = copy.deepcopy(good)
    doc["families"]["IPE"]["rows"]["200"][1] = 0
    assert "IPE 200" in refused(doc)
    doc = copy.deepcopy(good)
    doc["families"]["IPE"]["rows"]["200"].pop()
    assert "IPE 200" in refused(doc)
    doc = copy.deepcopy(good)
    doc["families"]["XYZ"] = doc["families"].pop("IPEA")
    assert "XYZ" in refused(doc)


def test_sia263_gives_the_steel_members_values():
    """REQ-002: E, G (3.2.2.3), gamma_M1 (4.1.3), gamma_M2 (Tabelle 16's file), epsilon of Tabelle 5 for each grade, and the thick band of Tabelle 1 above 40 mm -- HEM 1000's flange is 40 mm, HD 400×1086's 125 mm."""
    assert sia263.material()["E"] == 210000 and sia263.material()["G"] == 81000
    assert sia263.gamma_M1()["value"] == 1.05 and sia263.gamma_M2()["value"] == 1.25
    assert abs(sia263.epsilon(355) - 0.814) < 5e-4
    assert sia263.table_5()["internal"]["compression"] == [33, 38, 42] and sia263.table_5()["outstand"]["compression"] == [9, 10, 14]
    assert sia263.band_for(szs_c5.profile("HEM", [1000])["t_f"]) == "thin"
    assert sia263.band_for(szs_c5.profile("HD", [400, 1086])["t_f"]) == "thick"
    assert sia263.steel("S355", 125)["f_y"] < sia263.steel("S355", 40)["f_y"]
