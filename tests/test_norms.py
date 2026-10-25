"""The norm values of `calc/norms/`, and the checks that stand between them and the export.

**Since v0.77 every value a Python calculation takes from a norm is a JSON file directly in `calc/norms/`, named `<norm>-<year>-<table or clause>-<designation>.json`** (`sia265-2021-tab08-vollholz.json`), read by one module per norm beside it (`sia265.py`, `sia263.py`, `sia261.py`, `sn_en_14592.py`) -- the coefficients inside SIA 265's formulas included, which until then stayed in `domains/dowel.py`. The engineer's rule is that no norm value is written twice; `test_every_norm_file_is_named_and_read` and `test_dowel_py_writes_no_coefficient_of_the_norm` hold it.

These files are the one place in the pipeline where a number is transcribed by hand rather than read (docs/architecture/layout.md §11), so two things have to hold and neither is self-evident.

**The values are the norm's.** Spot values below were read off `SIA265-2021-DE.pdf` pages 25, 27 and 66, as images -- the two-column tables do not extract as text. `test_grades_match_the_workbook` is the stronger check: the engineer's `Verbindung.xlsm` carries an independent transcription of the same two tables, and 89 of its 90 values agree with these to the digit. The one that does not is D30's bracketed `f_c,90,d`, which the norm does not give and the workbook fills with the unbracketed value -- so the disagreement is expected and is asserted, rather than left to be rediscovered.

**The checks fire.** Every guard is exercised against a planted defect. A guard that has never fired is a guard nobody has tested, and these ones only ever run on files that are already correct.

Since v0.70 the same two questions are asked of **SIA 263**, the steel tables. Both of its tables are graphics in the PDF and were read off a render of pages 18 and 19, which is the one case where «read from the norm» means read with the eyes -- so the checks that do not need eyes matter more, not less: a bolt class is named after its own two numbers, and a thick section of a steel is never stronger than a thin one.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import io
import json
import re
import tokenize

import conftest
from conftest import ROOT, Skip
from norms import norms as norm_names, sia260, sia261, sia261_snow, sia261_wind, sia263, sia265, sn_en_14592, szs_c5, vkf
import validation

NORMS = ROOT / "calc" / "norms"
CALC = NORMS.parent


def _raised(fn, *args, **kwargs):
    """The message of the ValidationError `fn` must raise. No pytest: the runner is standard library only (docs/conventions/testing.md §11ter)."""
    try:
        fn(*args, **kwargs)
    except validation.ValidationError as exc:
        return str(exc)
    raise AssertionError("%s%r should have raised a ValidationError" % (getattr(fn, "__name__", fn), args))


def _close(a, b, rel=1e-12):
    assert abs(a - b) <= rel * max(abs(a), abs(b), 1.0), "%r != %r" % (a, b)


def _refuses(name, table, data=None, because=""):
    """The check of one file, run on a doctored copy, must raise. Returns the message."""
    try:
        sia265._CHECKS[name](name, table, data if data is not None else {})
    except validation.ValidationError as exc:
        return str(exc)
    raise AssertionError(
        "calc/norms/%s.json: the check passed a table that %s -- it should have refused it" % (name, because))


def _good(name):
    return copy.deepcopy(sia265._read(name))


# --- calc/norms/ as a whole ---------------------------------------------------

# <norm>-<year>-<table or clause>-<designation>.json: sia265-2021-tab08-vollholz, sia265-2021-6.2.1.1-k-alpha, sn-en-14592-2022-stabduebel-werkstoff, szs-c5-2018-edv-kurzbezeichnungen (v0.94: a page of the SZS's tables, named by what it is headed, «EDV»)
FILE_NAME = re.compile(r"^(sia\d{3}(-\d)?|sn-en-\d{4,5}|szs-c\d+|vkf)-(19|20)\d{2}-(tab\d{2}|\d+(\.\d+)+|[a-z]+)-[a-z0-9-]+\.json$")


# The one file of the folder that carries no value of a norm but the **name** of one -- the designation, the
# title, the edition and the publisher of every document the engine cites, for the report's bibliography
# (norms.py, lib/bibliography.typ, v0.99). It covers thirteen documents at once, so no
# <norm>-<year>-<table>-<designation> name could fit it, and it is exempted here by name rather than by
# loosening the pattern every other file is held to.
CATALOGUE = norm_names.NAME + ".json"


def test_every_norm_file_is_named_and_read():
    """Every JSON of calc/norms/ is named after its norm, year and table or clause, sits directly in the folder, and is read by a module -- a file nobody reads is a second copy of something waiting to disagree. The one exception is CATALOGUE, which names documents rather than transcribing values."""
    on_disk = {p.name for p in NORMS.glob("*.json")}
    for name in sorted(on_disk - {CATALOGUE}):
        assert FILE_NAME.match(name), "calc/norms/%s: not <norm>-<year>-<table or clause>-<designation>.json" % name
    assert not [p for p in NORMS.iterdir() if p.is_dir() and p.name != "__pycache__"], "calc/norms/ holds a subfolder -- every norm file sits directly in it"
    read = {n + ".json" for n in sia265.FILES}
    read |= {n + ".json" for n in sia260.FILES}
    read |= {n + ".json" for n in sia263.FILES}
    read |= {n + ".json" for n in (sia261.TAB08, sia261.TAB28, sia261.TAB29, sia261.TAB30)}
    read |= {n + ".json" for n in sia261_snow.FILES}
    read |= {n + ".json" for n in sia261_wind.FILES}
    from domains import wind_geometry
    read.add(wind_geometry.GEOMETRY + ".json")   # the 37 buildings of Annexe C as numbers (spec 2026-10-23-onglet-vent-briques, D-23)
    read.add("sia261-2020-wind-excerpts.json")   # the wind's excerpts, read by norms/excerpts.py for the wind's tab (spec 2026-10-23-onglet-vent-briques, ARCH-012)
    from norms import sia265_1
    read |= {n + ".json" for n in sia265_1.FILES}   # SIA 265/1, the wood-based panels (issue #110)
    read |= {n + ".json" for n in ("sia265-2021-materials-excerpts", "sia261-2020-materials-excerpts", "sia265-1-2018-materials-excerpts")}   # the excerpts the «Matériaux» tab shows as a material's source (issue #110, UI-008)
    read.add(sn_en_14592.NAME + ".json")
    read.add(szs_c5.NAME + ".json")
    read |= {n + ".json" for n in szs_c5.TABLE_NAMES}   # the profile tables (issue #50)
    read.add(vkf.NAME + ".json")
    read.add(vkf.REQUIREMENT_NAME + ".json")   # VKF 15-15's resistances of the load-bearing structure (issue #46)
    from norms import excerpts
    read |= {n + ".json" for n in excerpts.CITABLE}   # the excerpts a domain's line cites, found by its citation (issue #113, REQ-014)
    read.add(CATALOGUE)
    assert on_disk == read, "read by no module: %s; named by a module, not on disk: %s" % (sorted(on_disk - read), sorted(read - on_disk))


def _numbers_in_code(path):
    """The numeric literals of a Python file, comments and strings left out."""
    tokens = tokenize.generate_tokens(io.StringIO(path.read_text(encoding="utf-8")).readline)
    return {tok.string for tok in tokens if tok.type == tokenize.NUMBER}


def test_dowel_py_writes_no_coefficient_of_the_norm():
    """The coefficients of Tabelle 22, equations (86) to (88) and Tabellen 45/46 are read from calc/norms/, not written in the module that evaluates them (v0.77, the engineer's rule).

    Planted by hand when written: `FH_FACTOR = 0.082` put back in dowel.py fails here naming 0.082.
    """
    written = _numbers_in_code(CALC / "domains" / "dowel.py")
    coefficients = {"0.082", "0.01", "0.3", "0.015", "1.35", "0.90", "0.9", "2.6", "0.1", "0.25", "0.8", "0.44", "0.6",
                    "1.26", "2.52", "1.78", "0.89", "1.2", "0.35", "0.73", "0.75", "510",
                    # SIA 263 Tabelle 16 (76), 6.2.5 and 4.1.3, the plate's bearing (spec 2026-10-12-audit-issues-47-48-49)
                    "0.85", "2.4", "1.5", "1.25"}
    assert not written & coefficients, "dowel.py writes %s -- read them from calc/norms/" % sorted(written & coefficients)


def test_the_formula_coefficients_are_the_norms():
    """Read off the renders of pp. 63, 64, 95 and 96 of SIA265-2021-DE.pdf."""
    t22 = sia265.embedment()
    assert (t22["factor"], t22["predrilled_slope"], t22["undrilled_exponent"], t22["f_90_diameter_term"]) == (0.082, 0.01, -0.3, 0.015)
    assert t22["f_90_divisor"] == {"Nadelholz": 1.35, "Laubholz": 0.9} and t22["undrilled_species"] == ["Nadelholz"]
    assert (sia265.yield_moment()["factor"], sia265.yield_moment()["exponent"]) == (0.3, 2.6)
    red = sia265.reduction()
    assert (red["n_exponent"], red["spacing_reference"], red["spacing_exponent"], red["single_fastener"]) == (-0.1, 10, 0.25, 1.0)
    t45 = sia265.table_45()
    assert (t45["seitenholz"]["t_1_factor"], t45["seitenholz"]["k_1_share"], t45["seitenholz"]["t_2_factor"], t45["mittelholz"]["t_2_factor"]) == (0.44, 0.6, 1.26, 2.52)
    t46 = sia265.table_46()
    assert t46["mittelholz_bleche_aussen"]["t_2_factor"] == 1.78 and t46["mittelholz_bleche_aussen"]["k_2_root"] == 2
    assert (t46["seitenholz_scherfuge_a"]["t_1_factor"], t46["seitenholz_scherfuge_a"]["k_1"]) == (0.89, 1.2)
    assert t46["conditions"] == {"equation_130_t2_over_t1": 2, "equation_131_t1_over_t2": 0.35}
    assert sia265.constant("k_alpha") == 0.73 and sia265.resistance_diameters()["min"] == 6
    assert sia265.constant("truss_reduction") == 0.75


def test_the_moisture_classes_and_species_are_read_not_restated():
    assert sia265.moisture_class_ids() == (1, 2, 3)
    assert sia265.species_names() == ("Nadelholz", "Laubholz")


def test_sn_en_14592_gives_the_dowels_tensile_strength():
    """SN EN 14592:2022 Tabelle G.9 asks a dowel's bar f_y >= 235 N/mm² and gives no f_u: f_u,k is SIA 263 Tabelle 1's for the grade, S355 (510 N/mm²) by default (spec 2026-10-12-audit-issues-47-48-49, D-20)."""
    assert sn_en_14592.f_u_k() == 510 == sia263.f_u("S355")
    assert sn_en_14592.tensile_strength() == {"steel": "S355", "value": 510, "unit": "N/mm²", "norm": "SIA 263", "norm_ref": "Tabelle 1", "page": 18}
    assert sn_en_14592.edition() == "SN EN 14592:2022" and sn_en_14592.requirement()["norm_ref"] == "Tabelle G.9"
    assert sn_en_14592.dowel_grades() == ("S235", "S275", "S355", "S460")


def test_szs_c5_gives_the_profile_families_a_steel_position_may_name():
    """SZS C5, revision 2018, p. 154 «Kurzbezeichnungen für EDV-Anwendungen»: the 24 families the engineer chose, in his order, each with the page's German and French name -- read off a render of the page -- and an English one the file says is a translation (v0.94, docs/domain/positions.md §7)."""
    assert szs_c5.codes() == ("IPE", "IPEA", "IPN", "UPE", "UPN", "HEA", "HEB", "HEM", "HD", "HL", "T", "IPET", "HEAT", "HEBT",
                              "L", "RND", "VKT", "ROR", "RRK", "RRW", "FLA", "FLB", "BLE", "ZNP")
    assert szs_c5.edition() == "SZS C5:2018"
    assert szs_c5.names("ROR") == {"de": "Runde Stahlrohre, nahtlos oder geschweisst", "fr": "Tubes ronds en acier sans soudure ou soudés",
                                   "en": "Circular steel tubes, seamless or welded"}
    assert szs_c5.names("HEA")["de"] == "Breitflanschträger HE A" and szs_c5.names("VKT")["fr"] == "Carrés"
    assert "translation" in szs_c5._read()["_note"], "the file says its English is a translation"
    assert not any("ß" in szs_c5.names(code)["de"] for code in szs_c5.codes())


def test_szs_c5_refuses_what_is_not_a_code_list():
    """A code twice, a code in lower case, a name left out: each stops the reader, naming the file."""
    import json
    import conftest
    good = copy.deepcopy(szs_c5._read())
    probe = conftest.tmpdir("szs_c5") / "codes.json"
    path = szs_c5.PATH
    try:
        for doctored, because in (
            ({**good, "codes": good["codes"] + [good["codes"][0]]}, "listed twice"),
            ({**good, "codes": [{**good["codes"][0], "code": "ipe"}]}, "capitals"),
            ({**good, "codes": [{k: v for k, v in good["codes"][0].items() if k != "fr"}]}, "no fr name"),
        ):
            probe.write_text(json.dumps(doctored), encoding="utf-8")
            szs_c5.PATH = probe
            szs_c5._cache.clear()
            message = _raised(szs_c5.codes)
            assert because in message and szs_c5.NAME in message, message
    finally:
        szs_c5.PATH = path
        szs_c5._cache.clear()


def test_every_file_reads_and_checks():
    """check_all() reads and validates every SIA 265 file, and they agree on one edition."""
    assert sia265.check_all() == "SIA 265:2021"


def test_every_file_names_the_same_edition():
    """A file naming another edition would be another norm pretending to be this one."""
    assert sia265.edition() == "SIA 265:2021"


# --- Tabelle 8 and 9, the strength classes -----------------------------------

def test_the_eleven_grades_sia265_gives():
    """SIA 265 gives four solid-timber classes and seven glulam ones, and no more. GL40h and the CLT classes belong to SN EN 14080 resp. SIA 265/1, whose editions are not in the library (docs/architecture/principles.md §2 rule 13)."""
    assert list(sia265.grades()) == [
        "C16", "C24", "C30", "D30",
        "GL20h", "GL24c", "GL24h", "GL28c", "GL28h", "GL32c", "GL32h",
    ]


def test_a_grade_the_norm_does_not_give_says_which_norm_would():
    try:
        sia265.grade("GL40h")
    except validation.ValidationError as exc:
        assert "EN 14080" in str(exc) and "GL40h" in str(exc)
    else:
        raise AssertionError("grade('GL40h') should have failed: SIA 265 does not give it")


def test_spot_values_of_tabelle_8():
    """C24 and D30, read off page 25."""
    c24 = sia265.grade("C24")
    assert (c24["f_m_k"], c24["E_m_mean"], c24["rho_k"]) == (24, 11000, 350)
    assert (c24["f_m_d"], c24["f_t_0_d"], c24["f_c_0_d"], c24["f_t_90_d"]) == (14.1, 8.5, 12.4, 0.1)
    assert c24["f_c_90_d"]["generell"] == 1.8
    assert c24["f_c_90_d"]["mit_vorholz"] == {"value": 2.3, "groessere_eindrueckungen": 2.9}
    assert c24["f_c_90_d"]["endauflagerung"] == {"value": 1.8, "groessere_eindrueckungen": 2.9}
    assert (c24["f_v_d"], c24["E_0_mean"], c24["E_90_mean"], c24["G_mean"]) == (1.5, 11000, 370, 690)

    d30 = sia265.grade("D30")
    assert d30["rho_k"] == 530 and d30["f_v_d"] == 1.8
    # the norm prints 7,0 and 5,3 with no bracket at all for Buche/Eiche
    assert d30["f_c_90_d"]["mit_vorholz"]["groessere_eindrueckungen"] is None


def test_spot_values_of_tabelle_9():
    """GL24h and GL32h, read off page 27."""
    gl24h = sia265.grade("GL24h")
    assert (gl24h["f_m_d"], gl24h["f_t_0_d"], gl24h["f_c_0_d"]) == (16.0, 12.8, 16.0)
    assert (gl24h["rho_k"], gl24h["E_0_mean"], gl24h["G_mean"]) == (385, 11500, 650)
    gl32h = sia265.grade("GL32h")
    assert (gl32h["f_m_d"], gl32h["f_t_0_d"], gl32h["f_c_0_d"], gl32h["rho_k"]) == (21.3, 17.1, 21.3, 440)


def test_species_is_the_norms_own_column():
    """Which branch of Tabelle 22 a Lochleibungsfestigkeit is read from is a property of the grade, so nothing asks the engineer for it. D30 is the norm's Buche/Eiche column."""
    assert sia265.species("C24") == "Nadelholz"
    assert sia265.species("GL32h") == "Nadelholz"
    assert sia265.species("D30") == "Laubholz"


def test_grades_match_the_workbook():
    """The engineer's Verbindung.xlsm carries an independent transcription of Tabellen 8 and 9.

    Two transcriptions agreeing is what says neither has a typo. The one disagreement is D30's bracketed f_c,90,d: the norm gives none, the workbook repeats the unbracketed 7.0 there. Asserted, so that it stays a known difference rather than a surprise.
    """
    from fixtures import verbindung
    daten = verbindung.frozen()["daten"]   # the Daten sheet, frozen on 19.09.2026 (tests/fixtures/verbindung.json, v0.81); test_dowel says the workbook still holds it
    known = sia265.grades()
    compared, differences = 0, []
    for gid, cell in daten.items():
        if gid not in known:
            continue
        grade = known[gid]
        pairs = (
            ("f_m_d", grade["f_m_d"], cell["f_m_d"]),
            ("f_t_0_d", grade["f_t_0_d"], cell["f_t_0_d"]),
            ("f_c_0_d", grade["f_c_0_d"], cell["f_c_0_d"]),
            ("f_c_90_d generell", grade["f_c_90_d"]["generell"], cell["generell"]),
            ("f_c_90_d mit Vorholz", grade["f_c_90_d"]["mit_vorholz"]["value"], cell["mit_vorholz"]),
            ("f_c_90_d Endauflagerung", grade["f_c_90_d"]["endauflagerung"]["value"], cell["endauflagerung"]),
            ("f_c_90_d bracket", grade["f_c_90_d"]["mit_vorholz"]["groessere_eindrueckungen"], cell["bracket"]),
            ("f_v_d", grade["f_v_d"], cell["f_v_d"]),
            ("E_0_mean", grade["E_0_mean"], cell["E_0_mean"]),
            ("rho_k", grade["rho_k"], cell["rho_k"]),
        )
        for label, ours, theirs in pairs:
            compared += 1
            if ours is None and theirs is None:
                continue
            if ours is None or theirs is None or abs(float(ours) - float(theirs)) > 1e-9:
                differences.append("%s %s: norms=%r Daten=%r" % (gid, label, ours, theirs))

    assert compared >= 80, "only %d values compared -- the Daten sheet has moved" % compared
    assert differences == ["D30 f_c_90_d bracket: norms=None Daten=7"], (
        "the two transcriptions of SIA 265 Tabellen 8/9 disagree somewhere new:\n  " + "\n  ".join(differences))


# --- Tabelle 4 and clause 2.2.6 ----------------------------------------------

def test_eta_w_and_eta_t():
    assert sia265.eta_w(1) == 1.0 and sia265.eta_w(1, "stiffness") == 1.0
    assert sia265.eta_w(2) == 0.8 and sia265.eta_w(2, "stiffness") == 0.9
    assert sia265.eta_w(3) == 0.6 and sia265.eta_w(3, "stiffness") == 0.75
    assert sia265.eta_t() == 1.0 and sia265.eta_t(True) == 1.4


def test_an_unknown_moisture_class_lists_the_three():
    assert "1, 2, 3" in _raised(sia265.eta_w, 4)


# --- Tabelle 1 ---------------------------------------------------------------

def test_gamma_m_ratios():
    assert sia265.gamma_m("solid") == 1.7
    assert sia265.gamma_m("glulam") == 1.5
    assert sia265.gamma_m("connection") == 1.7
    assert sia265.gamma_m("connection_ductile") == 1.5


# --- Tabelle 24 --------------------------------------------------------------

def test_dowel_spacings_are_multiples_of_d():
    """The Stahl-Holz sheet of Verbindung.xlsm prints these for d = 12 mm."""
    s = sia265.dowel_spacings(12)
    assert s["fastener"] == {"parallel": 84, "perpendicular": 36}
    assert s["loaded_edge"] == {"parallel": 84, "perpendicular": 48}
    assert s["unloaded_edge"] == {"parallel": 60, "perpendicular": 36}


def test_the_loaded_end_carries_an_absolute_floor():
    """«7 · d (min. 80 mm)» -- so a small dowel does not get a small end distance. At d = 8, 7·d is 56 and the floor decides."""
    assert sia265.dowel_spacings(8)["loaded_edge"]["parallel"] == 80
    assert sia265.dowel_spacings(14)["loaded_edge"]["parallel"] == 98


# --- Tabelle 25 --------------------------------------------------------------

def test_kser_reproduces_the_workbook():
    """The Holz-Holz sheet computes K_ser,0 = 5227.201961826735 and K_ser,90 = 2613.6009809133675 for d = 14 mm and rho_k = 385."""
    _close(sia265.kser("timber-timber", 385, 14, 0), 5227.201961826735)
    _close(sia265.kser("timber-timber", 385, 14, 90), 2613.6009809133675)
    # halfway between, as 6.2.1.4 interpolates
    _close(sia265.kser("timber-timber", 385, 14, 45), (5227.201961826735 + 2613.6009809133675) / 2)


def test_kser_of_a_steel_timber_joint_is_twice_the_timber_one():
    """Tabelle 25 gives 6 and 3 against 3 and 1.5."""
    _close(sia265.kser("steel-timber", 385, 12, 0), 2 * sia265.kser("timber-timber", 385, 12, 0))
    _close(sia265.kser("steel-timber", 385, 12, 90), 2 * sia265.kser("timber-timber", 385, 12, 90))


def test_slip_is_half_a_millimetre():
    assert sia265.slip()["value"] == 0.5 and sia265.slip()["unit"] == "mm"


# --- the guards, each against a planted defect -------------------------------

def test_a_grade_listed_twice_is_refused():
    data = _good(sia265.TAB08)
    table = data["table_8"]
    table["grades"].append(copy.deepcopy(table["grades"][1]))
    assert "listed twice" in _refuses(sia265.TAB08, table, data, because="lists C24 twice")


def test_a_property_that_is_not_a_number_is_refused():
    data = _good(sia265.TAB08)
    table = data["table_8"]
    table["grades"][1]["rho_k"] = "350"
    assert "expected a number" in _refuses(sia265.TAB08, table, data, because="gives rho_k as text")


def test_a_missing_property_is_refused():
    data = _good(sia265.TAB09)
    table = data["table_9"]
    del table["grades"][2]["f_v_d"]
    assert "f_v_d" in _refuses(sia265.TAB09, table, data, because="leaves f_v_d out")


def test_an_unknown_species_is_refused():
    data = _good(sia265.TAB08)
    table = data["table_8"]
    table["grades"][0]["species"] = "Bambus"
    assert "species" in _refuses(sia265.TAB08, table, data, because="names a species Tabelle 22 has no branch for")


def test_a_bracket_below_its_own_value_is_refused():
    """Footnote 4's parenthesised value is the higher one; below it, the transcription has swapped two cells."""
    data = _good(sia265.TAB08)
    table = data["table_8"]
    table["grades"][1]["f_c_90_d"]["mit_vorholz"]["groessere_eindrueckungen"] = 1.0
    assert "higher one" in _refuses(sia265.TAB08, table, data, because="has a bracket below its own value")


def test_a_bracket_left_out_entirely_is_refused():
    """null says the norm gives none; a missing key says nobody looked."""
    data = _good(sia265.TAB08)
    table = data["table_8"]
    del table["grades"][1]["f_c_90_d"]["mit_vorholz"]["groessere_eindrueckungen"]
    assert "write null" in _refuses(sia265.TAB08, table, data, because="omits the bracket key")


def test_a_footnote_referenced_but_not_written_is_refused():
    data = _good(sia265.TAB08)
    table = data["table_8"]
    table["grades"][0]["notes"] = {"f_t_0_d": ["9"]}
    assert "footnote" in _refuses(sia265.TAB08, table, data, because="refers to a footnote it does not carry")


def test_a_moisture_class_out_of_range_is_refused():
    data = _good(sia265.TAB04)
    table = data["table_4"]
    table["classes"][2]["id"] = 4
    assert "has 1, 2, 3" in _refuses(sia265.TAB04, table, data, because="numbers a class 4")


def test_an_eta_w_above_one_is_refused():
    data = _good(sia265.TAB04)
    table = data["table_4"]
    table["classes"][1]["resistance"] = 1.2
    assert "at most 1" in _refuses(sia265.TAB04, table, data, because="raises a resistance above class 1")


def test_feuchteklasse_1_must_be_unity():
    data = _good(sia265.TAB04)
    table = data["table_4"]
    table["classes"][0]["resistance"] = 0.95
    assert "Feuchteklasse 1" in _refuses(sia265.TAB04, table, data, because="gives class 1 an eta_w below 1")


def test_a_gamma_m_below_one_is_refused():
    data = _good(sia265.TAB01)
    table = data["table_1"]
    table["entries"][0]["value"] = 0.9
    assert "not below 1" in _refuses(sia265.TAB01, table, data, because="divides a resistance by less than 1")


def test_a_missing_spacing_row_is_refused():
    data = _good(sia265.TAB24)
    table = data["table_24"]
    table["rows"].pop()
    assert "expected exactly" in _refuses(sia265.TAB24, table, data, because="drops a row of Tabelle 24")


def test_a_spacing_floor_left_out_is_refused():
    data = _good(sia265.TAB24)
    table = data["table_24"]
    del table["rows"][0]["parallel"]["min"]
    assert "write null" in _refuses(sia265.TAB24, table, data, because="omits the absolute floor key")


def test_a_missing_kser_family_is_refused():
    data = _good(sia265.TAB25)
    table = data["table_25"]
    table["families"].pop()
    assert "expected exactly" in _refuses(sia265.TAB25, table, data, because="drops the Stahl-Holz column")


def test_a_slip_without_a_value_is_refused():
    assert "slip" in _refuses(sia265.SLIP, {"unit": "mm"}, because="carries no slip value")


def test_tabelle_22_naming_an_undrilled_species_it_has_no_row_for_is_refused():
    data = _good(sia265.TAB22)
    table = data["table_22"]
    table["undrilled_species"] = ["Bambus"]
    assert "Bambus" in _refuses(sia265.TAB22, table, data, because="lets a species with no row go undrilled")


def test_tabelle_45_corners_the_wrong_way_round_are_refused():
    data = _good(sia265.TAB45)
    table = data["table_45"]
    table["seitenholz"]["t_1_factor"], table["seitenholz"]["t_2_factor"] = 1.26, 0.44
    assert "lower corner" in _refuses(sia265.TAB45, table, data, because="swaps the two corners of Tabelle 45")


def test_a_k_red_exponent_that_does_not_reduce_is_refused():
    data = _good(sia265.K_RED)
    entry = data["clause"]
    entry["n_exponent"] = 0.1
    assert "negative" in _refuses(sia265.K_RED, entry, data, because="makes more dowels in a row stronger")


def test_kser_outside_zero_to_ninety_is_refused():
    """The angle between force and grain is folded into 0-90 before it gets here."""
    assert "0 to 90" in _raised(sia265.kser, "timber-timber", 385, 12, 120)


# --- SIA 265, the minimum distances and timber thicknesses of each fastener (v0.87) ---------------

def _cells(number):
    """{row id: {column id: cell}} of one table of distances."""
    table = sia265.distance_table(number)
    return {row["id"]: {c["id"]: row[c["id"]] for c in table["columns"]} for row in table["rows"]}


def test_the_distance_tables_are_the_norms():
    """Read off renders of pp. 66, 68, 71, 74, 75, 76 and 80 of SIA265-2021-DE.pdf -- the tables do not extract as text in their columns, so each cell below was read on the page."""
    t24 = _cells(24)
    assert (t24["fastener"]["parallel"]["factor"], t24["fastener"]["perpendicular"]["factor"]) == (7, 3)
    assert (t24["loaded_edge"]["parallel"]["factor"], t24["loaded_edge"]["parallel"]["min"], t24["loaded_edge"]["perpendicular"]["factor"]) == (7, 80, 4)
    assert (t24["unloaded_edge"]["parallel"]["factor"], t24["unloaded_edge"]["perpendicular"]["factor"]) == (5, 3)
    t28 = _cells(28)
    assert [c["factor"] for c in t28["fastener"]["parallel"]["cases"]] == [10, 12]
    assert t28["fastener"]["parallel"]["cases"][0]["d_max"] == 4 and t28["fastener"]["perpendicular"]["factor"] == 5
    assert (t28["loaded_edge"]["parallel"]["factor"], t28["loaded_edge"]["perpendicular"]["factor"]) == (15, 10)
    assert [c["factor"] for c in t28["unloaded_edge"]["parallel"]["cases"]] == [7, 9]
    assert t28["unloaded_edge"]["perpendicular"] == {"factor": 10, "notes": ["1"]}
    t33 = _cells(33)
    assert [[t33[r][c]["factor"] for c in ("parallel", "perpendicular")] for r in ("fastener", "loaded_edge", "unloaded_edge")] == [[7, 4], [12, 6], [7, 4]]
    t38 = _cells(38)
    assert [c["factor"] for c in t38["fastener"]["parallel"]["cases"]] == [8, 10] and t38["fastener"]["perpendicular"]["factor"] == 5
    assert (t38["loaded_edge"]["parallel"]["factor"], t38["loaded_edge"]["perpendicular"]["factor"]) == (13, 8)
    assert [c["factor"] for c in t38["unloaded_edge"]["parallel"]["cases"]] == [6, 7.5]
    assert t38["fastener"]["parallel"]["cases"][0]["printed"] == "d = 4 mm", "the page prints «d = 4 mm», where Tabelle 28 prints «d ≤ 4 mm»"
    t39 = _cells(39)
    assert [[t39[r][c]["factor"] for c in ("parallel", "perpendicular")] for r in ("fastener", "loaded_edge", "unloaded_edge")] == [[6, 3.5], [10, 5], [6, 3.5]]
    t40 = _cells(40)
    assert [t40[r]["value"]["factor"] for r in ("a_1", "a_2", "a_1_CG", "a_2_CG")] == [7, 5, 10, 4]
    t41 = _cells(41)
    assert t41["fastener"]["parallel"]["alpha"] == {"coefficient": [4, 3], "base": [3, 2], "divisor": 180}
    assert t41["fastener"]["perpendicular"]["factor"] == [4, 3] and t41["unloaded_edge"]["perpendicular"]["factor"] == [2, 3]
    assert (t41["loaded_edge"]["parallel"]["factor"], t41["loaded_edge"]["perpendicular"]["factor"], t41["unloaded_edge"]["parallel"]["factor"]) == (1.8, 0.8, 0.8)
    for number, minimum in ((27, {"factor": 7}), (32, {"factor": 4, "min": 24}), (36, {"factor": 7}), (37, {"factor": 4, "min": 24})):
        cells = _cells(number)["timber"]
        assert cells["required"] == {"factor": 9} and cells["minimum"] == minimum, number
    pages = {n: sia265.distance_table(n)["page"] for n in (24, 27, 28, 32, 33, 36, 37, 38, 39, 40, 41)}
    assert pages == {24: 66, 27: 68, 28: 68, 32: 71, 33: 71, 36: 74, 37: 75, 38: 75, 39: 75, 40: 76, 41: 80}


def test_a_distance_is_its_multiple_of_d_and_its_floor():
    """The arithmetic lib/distance.typ does, in Python: the case d falls in, Tabelle 41's angle, the 80 mm and 24 mm floors."""
    t28 = _cells(28)
    assert sia265.distance(t28["fastener"]["parallel"], 4) == 40 and sia265.distance(t28["fastener"]["parallel"], 4.2) == 12 * 4.2
    ring = _cells(41)["fastener"]["parallel"]
    _close(sia265.distance(ring, 80), 160)                  # 2 d along the grain
    _close(sia265.distance(ring, 80, alpha=90), 80 * 4 / 3)  # 4/3 d across it
    assert sia265.distance(_cells(24)["loaded_edge"]["parallel"], 10) == 80, "7 d = 70 mm is below the 80 mm floor"
    assert sia265.distance(_cells(37)["timber"]["minimum"], 5) == 24 and sia265.distance(_cells(37)["timber"]["minimum"], 8) == 32
    assert "0 to 90" in _raised(sia265.distance, ring, 80, alpha=120)
    assert sia265.dowel_spacings(12)["loaded_edge"] == {"parallel": 84, "perpendicular": 48}, "domains/dowel.py still reads Tabelle 24's rows"


def test_the_diameter_ranges_are_the_clauses():
    """6.4.1.1 (p. 67): nails from 1.9 to 8.5 mm; 6.5.2.2 / 6.5.2.3.1 (pp. 73-74): screws of Tabellen 34 to 37 from 6 to 12 mm; 6.2.1.1: dowels from 6 to 30 mm."""
    assert sia265.diameter_scope(sia265.NAIL_DIAMETERS) == {"min": 1.9, "max": 8.5, "unit": "mm"}
    assert sia265.diameter_scope(sia265.SCREW_DIAMETERS) == {"min": 6, "max": 12, "unit": "mm"}
    assert sia265.diameter_scope(sia265.K_ALPHA)["max"] == 30
    kinds = {n: [f["fastener"] for f in sia265.distance_table(n)["fasteners"]] for n in (24, 27, 28, 32, 33, 36, 37, 38, 39, 40, 41)}
    assert kinds[24] == ["dowel", "bolt"] and kinds[28] == ["nail", "screw"] and kinds[41] == ["ring"]
    assert "33" in _raised(sia265.distance_table, 99)


def test_a_distance_table_split_at_two_diameters_is_refused():
    """d ≤ 4 in one case and d > 5 in the other leaves a nail of 4.5 mm in neither."""
    data = _good(sia265.TAB28)
    table = data["table_28"]
    table["rows"][0]["parallel"]["cases"][1]["d_above"] = 5
    assert "one diameter" in _refuses(sia265.TAB28, table, data, because="splits its cases at 4 and at 5 mm")


def test_a_footnote_no_cell_refers_to_is_refused():
    data = _good(sia265.TAB38)
    table = data["table_38"]
    del table["rows"][2]["perpendicular"]["notes"]
    assert "nothing refers to" in _refuses(sia265.TAB38, table, data, because="lost the mark of footnote 2")


def test_a_distance_cell_with_two_multiples_is_refused():
    data = _good(sia265.TAB33)
    table = data["table_33"]
    table["rows"][0]["parallel"]["cases"] = [{"d_max": 4, "factor": 7}, {"d_above": 4, "factor": 8}]
    assert "exactly one" in _refuses(sia265.TAB33, table, data, because="gives a cell a factor and cases")


def test_tabelle_41_turned_the_wrong_way_is_refused():
    """4/3 · (1/2 - alpha/60°) · d is nothing at 30° and negative at 90° -- base and divisor swapped in transcription."""
    data = _good(sia265.TAB41)
    table = data["table_41"]
    table["rows"][0]["parallel"]["alpha"].update(base=[1, 2], divisor=60)
    assert "wrong way round" in _refuses(sia265.TAB41, table, data, because="makes the ring spacing negative at 90°")


def test_a_distance_table_for_a_fastener_without_one_is_refused():
    """SIA 265 gives staples no table (6.6 sends them to SIA 265/1), so no table may claim them."""
    data = _good(sia265.TAB27)
    table = data["table_27"]
    table["fasteners"][0]["fastener"] = "staple"
    assert "staple" in _refuses(sia265.TAB27, table, data, because="claims a staple")


# --- SIA 263, the steel tables (v0.70) -----------------------------------------

def test_the_sia263_files_are_read_and_checked():
    assert sia263.check_all() is True
    assert sia263.edition() == "SIA 263:2013"


def test_tabelle_1_is_the_workbooks_own_transcription_and_one_row_more():
    """`Verbindung.xlsm`'s Daten sheet carries S235, S275 and S355 with the same six numbers each -- and NOT S460, which the norm gives.

    That missing row is the whole argument for section 2 rule 13 in one line: a value read from a workbook's restatement of a norm is a value that is right until the day the norm has one the workbook never copied.
    """
    expected = {
        "S235": ({"f_y": 235, "tau_y": 135, "f_u": 360}, {"f_y": 215, "tau_y": 124, "f_u": 340}),
        "S275": ({"f_y": 275, "tau_y": 160, "f_u": 430}, {"f_y": 255, "tau_y": 147, "f_u": 410}),
        "S355": ({"f_y": 355, "tau_y": 205, "f_u": 510}, {"f_y": 335, "tau_y": 193, "f_u": 490}),
        "S460": ({"f_y": 460, "tau_y": 265, "f_u": 550}, {"f_y": 430, "tau_y": 248, "f_u": 530}),
    }
    assert set(sia263.grades()) == set(expected)
    for name, (thin, thick) in expected.items():
        assert sia263.steel(name) == thin, name
        assert sia263.steel(name, 60) == thick, name
    assert sia263.f_u("S355") == 510


def test_a_thickness_picks_its_band():
    assert sia263.band_for(None) == "thin"       # not stated: the common plate
    assert sia263.band_for(40) == "thin"         # the limit belongs to the thin band
    assert sia263.band_for(40.1) == "thick"


def test_tabelle_2_classes_are_named_after_their_own_numbers():
    """8.8 is f_ub = 800 and f_yb = 0.8 · f_ub. `check_all` asserts it for every row, which is a transcription check no second reader is needed for."""
    assert sia263.bolt("8.8")["f_ub"] == 800 and sia263.bolt("8.8")["f_yb"] == 640
    assert sia263.bolt("10.9")["f_ub"] == 1000 and sia263.bolt("10.9")["f_yb"] == 900
    assert sia263.bolt("4.8")["common"] is False, "SIA 263 marks it not usual in Switzerland"
    assert sia263.bolt("8.8")["common"] is True


def test_the_fastener_list_carries_the_table_each_grade_came_from():
    """A plain round Stabdübel is a structural steel and a Bolzen is a Schraube: a report citing the wrong table would cite a number the norm does not give for that fastener."""
    entries = {e["name"]: e for e in sia263.fastener_grades()}
    assert entries["S355"]["table"] == "Tabelle 1" and entries["S355"]["f_u"] == 510
    assert entries["8.8"]["table"] == "Tabelle 2" and entries["8.8"]["f_u"] == 800
    assert entries["5.8"]["note"], "a class SIA 263 calls unusual here must carry its footnote"
    assert not entries["S235"]["note"]


def test_an_unknown_grade_is_refused_by_name():
    assert "S500" in _raised(sia263.grade, "S500")
    assert "12.9" in _raised(sia263.bolt, "12.9")


def test_a_thick_band_stronger_than_a_thin_one_is_refused():
    """The bands swapped is the transcription error this table invites, and it reads as a steel that grows stronger with thickness."""
    table = sia263._load("sia263-2013-tab01-baustaehle")
    keep = copy.deepcopy(table)
    try:
        table["table_1"]["grades"][0]["thick"]["f_u"] = 999
        assert "swapped" in _raised(sia263.check_all)
    finally:
        sia263._cache["sia263-2013-tab01-baustaehle"] = keep


def test_a_bolt_class_that_contradicts_its_name_is_refused():
    table = sia263._load("sia263-2013-tab02-schrauben")
    keep = copy.deepcopy(table)
    try:
        table["table_2"]["classes"][5]["f_ub"] = 900     # 8.8 carries 800
        assert "8.8" in _raised(sia263.check_all)
    finally:
        sia263._cache["sia263-2013-tab02-schrauben"] = keep


# --- SIA 261:2020 Anhang A, Tabellen 28 to 30 (calc/norms/sia261-2020-tab28..30-*.json) ------------

def test_sia261_anhang_a_reads_one_file_per_table():
    from norms import sia261
    sia261.check_all()
    assert (len(sia261.table_28()["rows"]), len(sia261.table_29()["rows"]), len(sia261.table_30()["rows"])) == (39, 19, 37), "every line of the three tables that carries a value, and Leichtbeton"
    assert sia261.edition() == "SIA 261:2020"


def test_sia261_spot_values_read_off_pages_77_and_78():
    """Checked against a render of the pages, the text layer interleaving each table's two columns."""
    from norms import sia261
    t28, t29, t30 = sia261.table_28(), sia261.table_29(), sia261.table_30()
    assert sia261.row(t28, "baustahl")["raumlast"] == 78.5
    assert sia261.row(t28, "holz_laubhoelzer_allgemein")["raumlast"] == 7.5
    assert sia261.row(t28, "leichtbeton_im_einzelfall_zu_bestimmen")["raumlast"] is None
    assert sia261.row(t28, "bituminoese_belaege_bituminoeser_belag_hmt")["raumlast"] == 24
    assert sia261.row(t29, "tonziegeldach_inkl_lattung_biberschwanz_doppeldeckung")["flaechenlast"] == 0.75
    assert sia261.row(t29, "betonziegeldach_inkl_lattung_pfannenziegel")["flaechenlast"] == 0.48
    assert sia261.row(t30, "erdauflasten_und_gleisschotter_erde_nass")["schuettwinkel"] == [20, 25]
    assert sia261.row(t30, "brennstoffe_holz_in_scheitern_laubholz_nass") == {
        "id": "brennstoffe_holz_in_scheitern_laubholz_nass", "group": "Brennstoffe", "subgroup": "Holz in Scheitern",
        "name": "Laubholz, nass", "raumlast": 10, "schuettwinkel": 45}
    assert sia261.row(t30, "stallmist_verrottet")["group"] is None, "Stallmist stands at the top level, not under Futtermittel"


def test_a_sia261_line_listed_twice_or_without_a_value_is_refused():
    from norms import sia261
    table = copy.deepcopy(sia261.table_28())
    table["rows"].append(copy.deepcopy(table["rows"][0]))
    try:
        sia261._check_annex(sia261.TAB28, {"table_28": table})
    except validation.ValidationError as exc:
        assert "twice" in str(exc)
    else:
        raise AssertionError("a line listed twice passed")
    table = copy.deepcopy(sia261.table_28())
    sia261.row(table, "baustahl")["raumlast"] = None
    try:
        sia261._check_annex(sia261.TAB28, {"table_28": table})
    except validation.ValidationError as exc:
        assert "baustahl" in str(exc)
    else:
        raise AssertionError("a line with no value passed, where only Leichtbeton may")
    table = copy.deepcopy(sia261.table_30())
    sia261.row(table, "erdauflasten_und_gleisschotter_erde_trocken")["schuettwinkel"] = [45, 40]
    try:
        sia261._check_annex(sia261.TAB30, {"table_30": table})
    except validation.ValidationError as exc:
        assert "backwards" in str(exc)
    else:
        raise AssertionError("a Schüttwinkel range running backwards passed")


# --- chapter 4.2, the member checks: Anhang B and the clause constants lib/timber.typ reads ---

def test_anhang_b_gives_every_grade_of_tabelle_8_and_9():
    """Tabellen 47 and 48 carry exactly the eleven strength classes, in the order of Tabellen 8 and 9."""
    assert [g["id"] for g in sia265.table_47()["grades"]] == ["C16", "C24", "C30", "D30"]
    assert [g["id"] for g in sia265.table_48()["grades"]] == ["GL20h", "GL24c", "GL24h", "GL28c", "GL28h", "GL32c", "GL32h"]
    assert sia265.table_47()["norm_ref"] == sia265.table_48()["norm_ref"] == "Anhang B"


def test_spot_values_of_anhang_b():
    """Read off the render of p. 98 of SIA265-2021-DE.pdf."""
    assert [(g["f_c_0_k"], g["E_0_05"]) for g in sia265.table_47()["grades"]] == [(17, 5400), (21, 7400), (24, 8000), (24, 9200)]
    assert [(g["f_c_0_k"], g["E_0_05"]) for g in sia265.table_48()["grades"]] == [
        (20, 7000), (21.5, 9100), (24, 9600), (24, 10400), (28, 10500), (24.5, 11200), (32, 11800)]
    assert sia265.characteristic("C24")["f_c_0_k"] == 21 and sia265.characteristic("GL24h")["E_0_05"] == 9600


def test_anhang_b_governs_over_the_footnotes_ratio():
    """Tabelle 8's footnote 5 (2/3 of E_0,mean for Nadelholz) and Tabelle 9's footnote 4 (5/6) come within 2 % of Anhang B's E_0,05 but are not it: the calculation reads Anhang B."""
    for gid, ratio in (("C16", 2 / 3), ("C24", 2 / 3), ("C30", 2 / 3), ("D30", 5 / 6), ("GL24h", 5 / 6), ("GL32h", 5 / 6)):
        derived = ratio * sia265.grade(gid)["E_0_mean"]
        assert abs(derived / sia265.characteristic(gid)["E_0_05"] - 1) < 0.02, gid
    assert sia265.characteristic("C24")["E_0_05"] != round(2 / 3 * 11000)


def test_an_unknown_grade_has_no_characteristic_values():
    assert "EN 14080" in _raised(sia265.characteristic, "GL40h")


def test_the_simplified_slenderness_is_the_anhang_b_ratio():
    """(35)/(36) and (43)/(44) are pi/sqrt(f_c,0,k/E_0,05) and 1.15 · sqrt(f_m,k/E_0,05) with a Nadelholz ratio taken as constant: C16 to C30 bracket 57, GL24h to GL32h round to 60, and 0.07 / 0.06."""
    import math
    buck = sia265.buckling()
    kipp = sia265.lateral_buckling()
    solid = [math.pi / math.sqrt(sia265.characteristic(g)["f_c_0_k"] / sia265.characteristic(g)["E_0_05"]) for g in ("C16", "C24", "C30")]
    assert min(solid) < buck["simplified_divisors"]["Vollholz"] < max(solid)
    glulam = math.pi / math.sqrt(24 / 9600)
    assert abs(glulam - buck["simplified_divisors"]["Brettschichtholz"]) / glulam < 0.06
    c24 = kipp["lambda_rel_m_factor"] * math.sqrt(sia265.grade("C24")["f_m_k"] / sia265.characteristic("C24")["E_0_05"])
    gl24 = kipp["lambda_rel_m_factor"] * math.sqrt(sia265.grade("GL24h")["f_m_k"] / sia265.characteristic("GL24h")["E_0_05"])
    assert round(c24, 2) == kipp["simplified_factors"]["Vollholz"] and round(gl24, 2) == kipp["simplified_factors"]["Brettschichtholz"]


def test_the_clause_constants_of_chapter_4_2():
    """Read off the renders of pp. 27, 33, 34, 35 and 36 of SIA265-2021-DE.pdf."""
    kh = sia265.k_h()
    assert (kh["reference_height"], kh["exponent"], kh["maximum"], kh["equation"]) == (600, 0.1, 1.1, "5")
    assert kh["families"] == ["Brettschichtholz"] and {n["norm_ref"] for n in kh["not_with"]} == {"3.4.2.2", "4.5.2.5"}
    ab = sia265.shear_off()
    assert ab["factor"] == {"Vollholz": 0.6, "Brettschichtholz": 0.8} and ab["min_shear_length"] == 150
    assert sia265.shear_transverse()["k_t_90"] == {"querzug": 1.0, "querdruck": 4.0}
    kn = sia265.buckling()
    assert kn["beta_c"] == {"Vollholz": 0.2, "Brettschichtholz": 0.1}
    assert (kn["k_factor"], kn["lambda_rel_offset"], kn["lambda_rel_limit"]) == (0.5, 0.3, 0.3)
    assert (kn["slenderness_limits"]["secondary"]["value"], kn["slenderness_limits"]["primary"]["value"]) == (200, 150)
    assert kn["simplified_divisors"] == {"Vollholz": 57, "Brettschichtholz": 60}
    ki = sia265.lateral_buckling()
    assert ki["k_m"] == {"lower_bound": 0.75, "upper_bound": 1.4, "intercept": 1.56, "slope": 0.75}
    assert (ki["sigma_m_crit_factor"], ki["lambda_rel_m_factor"]) == (0.75, 1.15)
    assert ki["simplified_factors"] == {"Vollholz": 0.07, "Brettschichtholz": 0.06}


def test_k_h_at_its_reference_height_is_one():
    kh = sia265.k_h()
    assert (kh["reference_height"] / kh["reference_height"]) ** kh["exponent"] == 1
    assert min((kh["reference_height"] / 300) ** kh["exponent"], kh["maximum"]) < kh["maximum"]  # 1.072 at h = 300 mm
    assert min((kh["reference_height"] / 100) ** kh["exponent"], kh["maximum"]) == kh["maximum"]  # capped at h = 100 mm


def test_an_anhang_b_row_missing_is_refused():
    table = _good(sia265.TAB47)["table_47"]
    table["grades"] = [g for g in table["grades"] if g["id"] != "C30"]
    assert "C30" in _refuses(sia265.TAB47, table, because="leaves C30 out")


def test_an_anhang_b_grade_tabelle_9_does_not_give_is_refused():
    table = _good(sia265.TAB48)["table_48"]
    table["grades"].append({"id": "GL40h", "family": "Brettschichtholz", "f_c_0_k": 30, "E_0_05": 12000})
    assert "GL40h" in _refuses(sia265.TAB48, table, because="carries a class Tabelle 9 does not give")


def test_an_e005_above_the_mean_is_refused():
    table = _good(sia265.TAB47)["table_47"]
    table["grades"][1]["E_0_05"] = 11400
    assert "fractile" in _refuses(sia265.TAB47, table, because="puts C24's E_0,05 above its E_0,mean")


def test_an_anhang_b_grade_in_the_wrong_family_is_refused():
    table = _good(sia265.TAB48)["table_48"]
    table["grades"][0]["family"] = "Vollholz"
    assert "family" in _refuses(sia265.TAB48, table, because="files GL20h under Vollholz")


def test_a_k_h_that_lowers_is_refused():
    clause = _good(sia265.K_H)["clause"]
    clause["maximum"] = 0.9
    assert "above 1" in _refuses(sia265.K_H, clause, because="caps k_h below 1")


def test_an_abscheren_factor_above_one_is_refused():
    clause = _good(sia265.SHEAR_OFF)["clause"]
    clause["factor"]["Brettschichtholz"] = 8
    assert "at most 1" in _refuses(sia265.SHEAR_OFF, clause, because="multiplies f_v,d by 8")
    clause = _good(sia265.SHEAR_OFF)["clause"]
    del clause["factor"]["Vollholz"]
    assert "Vollholz" in _refuses(sia265.SHEAR_OFF, clause, because="gives no Vollholz factor")


def test_k_t_90_swapped_is_refused():
    clause = _good(sia265.SHEAR_TRANSVERSE)["clause"]
    clause["k_t_90"] = {"querzug": 4.0, "querdruck": 1.0}
    assert "querdruck" in _refuses(sia265.SHEAR_TRANSVERSE, clause, because="swaps Querzug and Querdruck")


def test_beta_c_swapped_is_refused():
    clause = _good(sia265.BUCKLING)["clause"]
    clause["beta_c"] = {"Vollholz": 0.1, "Brettschichtholz": 0.2}
    assert "beta_c" in _refuses(sia265.BUCKLING, clause, because="swaps the two families' beta_c")
    clause = _good(sia265.BUCKLING)["clause"]
    clause["slenderness_limits"]["primary"]["value"] = 250
    assert "primary" in _refuses(sia265.BUCKLING, clause, because="lets a main member be more slender than a bracing")


def test_a_k_m_branch_that_does_not_join_is_refused():
    """The misprint risk of equation (39): a middle branch with a mistyped coefficient no longer meets its neighbours."""
    clause = _good(sia265.LATERAL_BUCKLING)["clause"]
    clause["k_m"]["intercept"] = 1.65
    assert "middle branch" in _refuses(sia265.LATERAL_BUCKLING, clause, because="types 1.65 for 1.56")
    clause = _good(sia265.LATERAL_BUCKLING)["clause"]
    clause["lambda_rel_m_factor"] = 1.5
    assert "(42)" in _refuses(sia265.LATERAL_BUCKLING, clause, because="breaks (42) away from (41)")


# --- the VKF sheet of symbols for fire-protection plans ------------------------------

def test_the_fire_resistances_are_the_sheets_with_the_colour_it_gives_each():
    """Read off «BS-Symbole.pdf» / «pictogrammes PI.pdf», page 1, column «Farbcode RGB» / «code couleur RJB» (16.12.2016), and found again as the true colour of each pictogram's DXF file in both language sets. Colour is the only code a plan carries for a wall's resistance, so a colour off by one here is a wall read as another class."""
    assert vkf.resistance_keys() == ["REI 60-180", "EI 90-RF1", "EI 60-RF1", "EI 30-RF1", "EI 90", "EI 60", "EI 30", "E 60", "E 30", "RF1"]
    assert vkf.resistance("EI 30")["rgb"] == [255, 191, 0] and vkf.resistance("EI 60")["rgb"] == [223, 113, 0]
    assert vkf.resistance("EI 60-RF1")["rgb"] == [3, 101, 221] and vkf.resistance("EI 30-RF1")["rgb"] == [127, 191, 255]
    assert vkf.resistance("EI 90-RF1")["rgb"] == [127, 0, 255] and vkf.resistance("EI 90")["rgb"] == [125, 95, 0]
    assert vkf.resistance("E 30")["rgb"] == [250, 186, 252] and vkf.resistance("E 60")["rgb"] == [197, 101, 227]
    assert vkf.resistance("REI 60-180") == {"key": "REI 60-180", "label": "Brandmauer REI 60 bis REI 180", "rgb": [0, 0, 0]}
    assert vkf.resistance("RF1")["rgb"] == [121, 243, 243]
    assert vkf.escape("length") == {"label": "Fluchtweglänge", "rgb": [0, 153, 0]}
    assert vkf.escape("horizontal")["rgb"] == [202, 254, 150] and vkf.escape("vertical")["rgb"] == [0, 153, 0]
    assert vkf.colour([0, 153, 0]) == "#009900"
    assert len({tuple(row["rgb"]) for row in vkf.resistances()}) == 10, "two resistances share a colour: the plan could not tell them apart"
    assert vkf.edition() == "VKF Symbole Brandschutzpläne 16.12.2016"
    for call in (lambda: vkf.resistance("EI 45"), lambda: vkf.escape("door")):
        try:
            call()
        except validation.ValidationError as exc:
            assert "expected one of" in str(exc)
        else:
            raise AssertionError("an entry the sheet does not have was given")


def test_the_doors_are_the_sheets_four_and_the_two_shapes_its_pictograms():
    """Group 2.2 «Abschlüsse» / «Fermetures» of the same page: a swing door and a sliding one, each EI 30 and E 30, in the colour of that resistance. The two shapes are the proportions of «Sortie de secours.jpeg» (825 x 590 px) and «Porte coulissante EI 30.jpeg» (1771 x 296 px), measured on the files."""
    assert vkf.DOOR_KINDS == ("swing", "slide") and vkf.door_classes() == ["EI 30", "E 30"]
    assert vkf.door("swing", "EI 30") == {"class": "EI 30", "label": "Türe / Tor EI 30", "rgb": [255, 191, 0]}
    assert vkf.door("swing", "E 30") == {"class": "E 30", "label": "Türe / Tor / Abschluss E 30", "rgb": [250, 186, 252]}
    assert vkf.door("slide", "EI 30")["label"] == "Schiebetüre / Schiebetor EI 30" and vkf.door("slide", "E 30")["label"] == "Schiebetüre / Schiebetor E 30"
    # a door is drawn in the colour of its resistance: the sheet's own two agree with the walls'
    for kind in vkf.DOOR_KINDS:
        for cls in vkf.door_classes():
            assert vkf.door(kind, cls)["rgb"] == vkf.resistance(cls)["rgb"], (kind, cls)
    exit_shape, slide = vkf.shape("exit"), vkf.shape("slide")
    assert abs(exit_shape["shaft_length"] - 500 / 825) < 1e-3 and abs(exit_shape["shaft_width"] - 200 / 825) < 1e-3 and abs(exit_shape["head_width"] - 590 / 825) < 1e-3
    assert abs(slide["head_length"] - 354 / 1771) < 1e-3 and abs(slide["head_height"] - 296 / 1771) < 1e-3 and abs(slide["bar"] - 118 / 1771) < 1e-3
    assert exit_shape["shaft_width"] < exit_shape["head_width"] and slide["bar"] < slide["head_height"], "an arrow whose head is no wider than its shaft"
    for call in (lambda: vkf.door("revolving", "EI 30"), lambda: vkf.door("swing", "EI 60"), lambda: vkf.shape("door")):
        try:
            call()
        except validation.ValidationError as exc:
            assert "expected one of" in str(exc)
        else:
            raise AssertionError("an entry the sheet does not have was given")


def test_a_defective_vkf_file_is_refused():
    """Six planted defects: a resistance listed twice, a colour that is no colour, an escape entry missing, a door of a class the file has no resistance for, a swing door and a sliding one in different classes, a shape that is no share of its pictogram."""
    good = copy.deepcopy(vkf._read())
    path = conftest.tmpdir("vkf") / "vkf.json"
    real = vkf.PATH

    def refused(data, word):
        path.write_text(json.dumps(data), encoding="utf-8")
        vkf._cache.clear()
        vkf.PATH = path
        try:
            vkf.resistances()
        except validation.ValidationError as exc:
            assert word in str(exc), str(exc)
        else:
            raise AssertionError("accepted -- expected a refusal naming %r" % word)
        finally:
            vkf.PATH = real
            vkf._cache.clear()

    twice = copy.deepcopy(good)
    twice["resistances"].append(dict(twice["resistances"][2]))
    refused(twice, "listed twice")
    colour = copy.deepcopy(good)
    colour["resistances"][0]["rgb"] = [0, 0, 300]
    refused(colour, "rgb")
    escape = copy.deepcopy(good)
    del escape["escape"]["clear"]
    refused(escape, "escape")
    door = copy.deepcopy(good)
    door["doors"]["swing"][0]["class"] = "EI 45"
    refused(door, "no fire resistance of this file")
    uneven = copy.deepcopy(good)
    del uneven["doors"]["slide"][1]
    refused(uneven, "same classes")
    shape = copy.deepcopy(good)
    shape["shapes"]["exit"]["head_width"] = 1.4
    refused(shape, "share of the pictogram")
    assert vkf.resistance_keys()[0] == "REI 60-180" and vkf.door_classes() == ["EI 30", "E 30"]
