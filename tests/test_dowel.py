"""The shear resistance of a dowel connection, SIA 265:2021 6.2.1 -- `calc/domains/dowel.py`.

Three kinds of check, and the project has real oracles for all three.

**The engineer's own workbook.** `Verbindung.xlsm` computed these two connections -- the values below are those of the reference template «dowel connections», from which it was made, its own Holz-Holz sheet holding the project's VU-SD-10 today (periodic audit 260916) -- and the module was written from the norm alone; every intermediate below is the cell that workbook prints, to the last digit it prints. Where a cell is named in a docstring it is named exactly, so the next reader can open the sheet beside the test.

**The norm's own published answers.** Tabelle 21 tabulates k_red for 28 combinations of n and a_1, and Tabelle 45 prints a «Für beta_f = 1» short form of the very formulas the module implements in general. Both are checked, and neither needed anybody's arithmetic to produce.

**Invariants.** k_beta is continuous, non-decreasing, and exactly the norm's corner values at the corners -- which a swapped corner breaks and a merely wrong number does not.

👉 Two defects this file exists for, both found while it was being written, both in `Verbindung.xlsm` and both settled in favour of SIA 265:

- `'Stabdübel (Holz-Holz)'!O34` and `!P34` compute the *einschnittig* second member's t_2,i with sqrt(beta_f/(1+beta_f)), which is member 1's bracket; Tabelle 45 equations (125) use sqrt(1/(1+beta_f)). Invisible at beta_f = 1, which is every case that sheet has been used on. `test_the_norm_and_not_the_workbook_at_beta_f_other_than_one` holds it.
- `'Stabdübel (Holz-Holz)'!C33/D33` does not special-case n = 1, where equation (86) alone gives 0.915 at a_1 = 7d and Tabelle 21 gives 1.0. `'Stabdübel (Stahl-Holz)'!C31` does special-case it. `test_k_red_against_tabelle_21` holds it.
"""

TIER = "fast"  # tests/run_tests.py --fast

import math

from domains import dowel
from norms import sia265
import validation


def _close(a, b, rel=1e-9):
    assert abs(a - b) <= rel * max(1.0, abs(a), abs(b)), "%r != %r" % (a, b)


def _raised(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except validation.ValidationError as exc:
        return str(exc)
    raise AssertionError("%s should have raised a ValidationError" % getattr(fn, "__name__", fn))


def _member(rho=385, species="Nadelholz", alpha=0, t=100, predrilled=True, n=1, a_1=None, moisture=1):
    return {"rho_k": rho, "species": species, "alpha": alpha, "t": t, "predrilled": predrilled,
            "n": n, "a_1": a_1, "moisture_class": moisture}


# The two connections Verbindung.xlsm computes, as its cells give them.
HOLZ_HOLZ = {
    "assembly": "Holz-Holz zweischnittig",
    "d": 14.0, "f_u_k": 510.0, "n_tot": 8, "impact": False, "truss": False,
    "members": [_member(t=70, n=4, a_1=100), _member(t=100, n=4, a_1=100)],
}

STAHL_HOLZ = {
    "assembly": "Stahl-Holz, Schlitzbleche",
    "d": 12.0, "f_u_k": 510.0, "n_tot": 9, "impact": False, "truss": False,
    "members": [_member(alpha=90, t=200, n=3, a_1=60)],
    "steel": {"plates": 2, "slot": 12.0, "ratio": 0.5, "grade": "S235"},
}


# --- the workbook, cell by cell ----------------------------------------------

def test_holz_holz_reproduces_the_workbook():
    """Verbindung.xlsm, sheet «Stabdübel (Holz-Holz)»: GL24h on GL24h, d = 14 mm, zweischnittig, t = 70/100 mm, 8 dowels in rows of 4 at a_1 = 100 mm."""
    r = dowel.analyse(dict(HOLZ_HOLZ))
    _close(r["f_h_1_k"], 27.150199999999998)            # C25
    _close(r["f_h_2_k"], 27.150199999999998)            # D25
    _close(r["beta_f"], 1.0)                            # L34
    _close(r["corners"][0]["t_1"], 26.885267629189244)  # M34
    _close(r["corners"][0]["t_2"], 76.989630029041933)  # N34
    _close(r["corners"][1]["t_2"], 63.780297840232137)  # P35
    _close(r["corners"][0]["k_beta"], 1.33529963863802)   # Q34
    _close(r["corners"][1]["k_beta"], 1.4142135623730951)  # R35
    _close(r["k_beta"], 1.33529963863802)               # C40
    _close(r["M_u_k"], 146091.28987309814)              # C37
    _close(r["k_red"], 0.8003169075899752)              # min(C33, D33)
    assert r["p"] == 2                                   # C39
    _close(r["R_d_Verb"], 93.013559040219036)           # C44
    _close(r["R_d"], 11.626694880027379)                # C43
    _close(r["K_ser"]["K_ser"], 5227.201961826735)      # C59
    _close(r["K_ser"]["K_ser_Verb"], 83635.23138922776)  # C62
    assert r["K_ser"]["slip"] == 0.5                     # C61
    assert r["warnings"] == []


def test_the_workbook_s_holz_holz_sheet_is_the_project_s_connector_cell_by_cell():
    """`Verbindung.xlsm` itself, read rather than restated: its Holz-Holz sheet holds the project's own connector (SD-10, VU-SD-10 until 17.09.2026) -- C24 on C24, d = 10 mm, zweischnittig, t = 50/100 mm, moisture class 2, 4 dowels in rows of 2 at a_1 = 120 mm. `test_holz_holz_reproduces_the_workbook` holds the template's own case, which the project copy no longer carries (periodic audit 260916, AUD-2-7).

    ⚠️ **The force-grain angles are read, not assumed** (20.09.2026). They were 0° in both members until the engineer entered 50.2° and 39.8°, and the case restated that zero: every result moved and this test went red while Python was right -- with the angles put in, k_beta, R_d and R_d,Verb reproduce the sheet to the digit. What the case still states is what *names* the connector; anything the sheet can change without ceasing to be that connector is taken from the cells.

    ⚠️ **k_red is one per member** and the calculation reads the smaller (C33, D33). While both angles were 0° the two were equal and comparing against C33 alone was right by accident; with 50.2° against 39.8° it is member 2 that governs, and comparing the governing value against member 1's is what this test did until it was caught.

    K_ser,Verb included: the engineer carried the stiffness column of SIA 265 Tabelle 4 (0.9 in moisture class 2) into C62 on 17.09.2026, as the norm and this module have it (AUD-2-3). Skipped where the workbook is not there.
    """
    from conftest import Skip
    from fixtures import verbindung
    cell = verbindung.frozen()["holz_holz"]      # frozen from the workbook on 19.09.2026 (tests/fixtures/verbindung.json, v0.81)
    case = (cell["C12"], cell["C13"], cell["C15"], cell["C20"], cell["D20"], cell["C23"], cell["D23"], cell["C29"], cell["C30"], cell["C32"])
    if case != (10, 2, "zweischnittig", "C24", "C24", 50, 100, 4, 2, 120):
        raise Skip("Verbindung.xlsm no longer holds the project's connector: %r" % (case,))
    r = dowel.analyse({
        "assembly": "Holz-Holz zweischnittig", "d": cell["C12"], "f_u_k": cell["C36"], "n_tot": cell["C29"],
        "impact": cell["C14"] != "Nein", "truss": False,
        "members": [
            _member(rho=cell["C22"], species=cell["C21"], alpha=cell["C19"], t=cell["C23"],
                    predrilled=cell["C24"] == "Ja", n=cell["C30"], a_1=cell["C32"], moisture=cell["C13"]),
            _member(rho=cell["D22"], species=cell["D21"], alpha=cell["D19"], t=cell["D23"],
                    predrilled=cell["D24"] == "Ja", n=cell["D30"], a_1=cell["D32"], moisture=cell["C13"]),
        ],
    })
    _close(r["f_h_1_k"], cell["C25"])
    _close(r["f_h_2_k"], cell["D25"])
    _close(r["k_red"], min(cell["C33"], cell["D33"]))
    _close(r["M_u_k"], cell["C37"])
    _close(r["k_beta"], cell["C40"])
    _close(r["R_d"], cell["C43"])
    _close(r["R_d_Verb"], cell["C44"])
    _close(r["K_ser"]["K_ser_Verb"], cell["C62"])


def test_the_workbook_still_holds_the_frozen_cells():
    """The cells above are frozen (tests/fixtures/verbindung.json, v0.81): the workbook is the project's, and a clone of the code has none. On the engineer's own machine the workbook is read again and must still give them -- a cell changed in it is a value to freeze again, deliberately (fixtures/verbindung.freeze). Skipped where the workbook is not there."""
    import conftest
    from fixtures import verbindung
    book = conftest.real_project().root / "Verbindung.xlsm"
    if not book.exists():
        raise conftest.Skip("Verbindung.xlsm is not in the engineer's project")
    assert verbindung.read(book) == verbindung.frozen(), "Verbindung.xlsm no longer holds the frozen cells -- freeze them again if the change is meant"


def test_stahl_holz_reproduces_the_workbook():
    """Verbindung.xlsm, sheet «Stabdübel (Stahl-Holz)»: GL24h, d = 12 mm, two slotted plates in a 200 mm member, alpha = 90°, 9 dowels in rows of 3 at a_1 = 60 mm."""
    r = dowel.analyse(dict(STAHL_HOLZ))
    _close(r["f_h_1_k"], 18.157908496732027)            # C40
    _close(r["geometry"]["t_1"], 44.0)                  # C18
    _close(r["geometry"]["t_2"], 88.0)                  # C19
    _close(r["planes"][0]["t_1"], 34.433976593548742)   # L24
    _close(r["planes"][0]["t_2"], 97.498450579486303)   # M24
    _close(r["planes"][0]["k_beta"], 1.3213491248157794)  # C21 via P24
    _close(r["planes"][1]["k_beta"], 1.8051568917653185)  # C22 via P25
    assert r["p"] == 4                                   # C27
    _close(r["p_k_beta"], 6.2530120331621957)           # C23
    _close(r["k_red"], 1.0)                             # C31
    _close(r["M_u_k"], 97850.41469084358)               # C44
    _close(r["R_d"], 21.077397910774859)                # C46
    _close(r["R_d_Verb"], 189.69658119697374)           # C47
    _close(r["K_ser"]["K_ser"], 4022.1636589882673)     # C63
    _close(r["K_ser"]["K_ser_Verb"], 144797.89172357763)  # C66
    assert r["warnings"] == []


def test_the_truss_value_is_a_second_answer_not_a_factor_on_the_first():
    """Verbindung.xlsm C45 = C44 · 0.75. SIA 265 5.3.6.2.2 is narrower than the word «truss» -- it is the connections of the Ausfachungsstäbe under the simplified calculation of 5.3.6.1.2 -- so R_d,Verb keeps its own value and the reduced one stands beside it."""
    plain = dowel.analyse(dict(HOLZ_HOLZ))
    truss = dowel.analyse(dict(HOLZ_HOLZ, truss=True))
    _close(truss["R_d_Verb"], plain["R_d_Verb"])
    _close(truss["R_d_Verb_truss"], 69.760169280164277)
    _close(truss["truss_factor"], 0.75)
    assert "R_d_Verb_truss" not in plain


# --- the norm's own published answers ----------------------------------------

# SIA 265 Tabelle 21 (6.1.4.2), read off page 63: k_red at alpha = 0, by a_1 and n.
TABELLE_21 = {
    7: {1: 1.0, 2: 0.85, 3: 0.82, 4: 0.80, 5: 0.78, 10: 0.73, 15: 0.70},
    8: {1: 1.0, 2: 0.88, 3: 0.85, 4: 0.82, 5: 0.81, 10: 0.75, 15: 0.72},
    10: {1: 1.0, 2: 0.93, 3: 0.90, 4: 0.87, 5: 0.85, 10: 0.79, 15: 0.76},
    12: {1: 1.0, 2: 0.98, 3: 0.94, 4: 0.91, 5: 0.89, 10: 0.83, 15: 0.80},
}


def test_the_dowels_steel_gives_f_u_k_and_s235_is_weaker():
    """Spec 2026-10-12-audit-issues-47-48-49, REQ-007 (D-06, D-20): SN EN 14592:2022 Tabelle G.9 asks only f_y >= 235 N/mm² of a dowel's bar, so f_u,k is read from the grade in SIA 263 Tabelle 1 -- S355 510 N/mm², S235 360. An S235 dowel carries R_d × √(360/510) wherever the dowel yields (every failure mode of Tabellen 45/46 reads √(f_u,k)); the record credits the grade and the table."""
    from norms import sn_en_14592
    assert sn_en_14592.f_u_k() == 510 and sn_en_14592.f_u_k("S235") == 360 and sn_en_14592.default_steel() == "S355"
    assert sn_en_14592.requirement()["min_yield"] == 235 and sn_en_14592.edition() == "SN EN 14592:2022"
    weak = dowel.analyse(dict(HOLZ_HOLZ, f_u_k=360.0, dowel_steel="S235"))
    strong = dowel.analyse(dict(HOLZ_HOLZ))
    _close(weak["M_u_k"] / strong["M_u_k"], 360 / 510)
    assert weak["R_d_Verb"] < strong["R_d_Verb"]
    record = dowel.record("SD_T", weak, HOLZ_HOLZ["members"])
    var = record["vars"]["f_u_k"]
    assert var["norm"] == "SIA 263" and var["norm_ref"] == "Tabelle 1" and var["description"] == "Stahl S235"
    assert dowel.record("SD_T", strong, HOLZ_HOLZ["members"])["vars"]["f_u_k"]["norm"] == "SIA 265", "a value with no grade is the engineer's"


def test_k_red_against_tabelle_21():
    """All 28 cells the norm publishes, to the two decimals it prints them at. d = 10 mm; the formula depends on a_1/d only, so the diameter cancels.

    The n = 1 column is the interesting one: equation (86) alone gives 0.915 at a_1 = 7d, and Tabelle 21 gives 1.0. One dowel in a row has nothing in front of it to be reduced by. `'Stabdübel (Holz-Holz)'!C33` does not guard that; this module does.
    """
    d = 10.0
    for factor, column in sorted(TABELLE_21.items()):
        for n, expected in sorted(column.items()):
            got = dowel.reduction(n, factor * d, d, 0)
            assert abs(got - expected) < 0.005, (
                "k_red(n=%d, a_1=%d·d) = %.4f, SIA 265 Tabelle 21 prints %.2f" % (n, factor, got, expected))


def test_k_red_is_one_at_ninety_degrees():
    """At alpha = 90 equation (86) collapses to 90/90 = 1: a force across the grain is not reduced by dowels behind one another."""
    _close(dowel.reduction(5, 70.0, 10.0, 90), 1.0)


def test_beta_f_one_collapses_to_the_norms_own_short_form():
    """SIA 265 Tabelle 45 prints a «Für beta_f = 1» column -- equations (122), (123), (126) and (127): 0.75, 2.15, 1.78 and k_beta = sqrt(2).

    It carries no information the general form does not (0.44·(1/sqrt(2)+1) = 0.751, 1.26·(1/sqrt(2)+1) = 2.151, 2.52/sqrt(2) = 1.782), so only the general form is implemented -- and this is what says the two agree. It is also the check that would have caught the short form being mistaken for Tabelle 46's steel row.
    """
    r = dowel.analyse({
        "assembly": "Holz-Holz zweischnittig",
        "d": 10.0, "f_u_k": 500.0, "n_tot": 2, "impact": False, "truss": False,
        "members": [_member(t=1000), _member(t=1000)],
    })
    base = math.sqrt(500.0 / r["f_h_1_k"]) * 10.0 ** 0.8
    assert abs(r["corners"][0]["t_1"] / base - 0.75) < 0.002   # equation (122)
    assert abs(r["corners"][0]["t_2"] / base - 2.15) < 0.002   # equation (122)
    assert abs(r["corners"][1]["t_2"] / base - 1.78) < 0.003   # equation (123)
    _close(r["k_beta_max"], math.sqrt(2))


def test_the_steel_corners_are_tabelle_46():
    """Tabelle 46, read off page 96 as an image -- the two-column formula tables do not extract as text.

    Equation (128), plates outside: the Mittelholz curve, from the origin to (1.78·sqrt(f_u,k/f_h,k)·d^0.8, sqrt(2)). Equations (129)/(130), a side timber against a slotted plate: (0.89·…, 1.2) then (2.52·…, 2). Equation (131), a middle timber between two slotted plates: the origin then (2.52·…, 2).
    """
    outer = dowel.analyse({
        "assembly": "Stahl-Holz, Bleche aussen",
        "d": 12.0, "f_u_k": 510.0, "n_tot": 4, "impact": False, "truss": False,
        "members": [_member(alpha=90, t=160, n=2, a_1=90)],
        "steel": {"plates": 2, "grade": "S235"},
    })
    base = math.sqrt(510.0 / outer["f_h_1_k"]) * 12.0 ** 0.8
    plane = outer["planes"][0]
    assert plane["t_1"] == 0 and plane["k_1"] == 0          # the lower corner is the origin
    _close(plane["t_2"], 1.78 * base)
    _close(plane["k_2"], math.sqrt(2))
    assert outer["p"] == 2

    slotted = dowel.analyse(dict(STAHL_HOLZ))
    a, b = slotted["planes"]
    base = math.sqrt(510.0 / slotted["f_h_1_k"]) * 12.0 ** 0.8
    _close(a["t_1"], 0.89 * base)
    assert a["k_1"] == 1.2 and a["k_2"] == 2.0
    _close(a["t_2"], 2.52 * base)
    assert b["t_1"] == 0 and b["k_1"] == 0
    _close(b["t_2"], 2.52 * base)
    assert b["k_2"] == 2.0
    # p · k_beta = 2 · k_beta1 + (p-2) · k_beta2, SIA 265 6.2.1.1 -- and not A.1.1, whose line misprints the second index
    _close(slotted["p_k_beta"], 2 * a["k_beta"] + 2 * b["k_beta"])


def test_one_slotted_plate_has_only_A_planes():
    """With a single plate there is no middle timber, so equation (131) has nothing to apply to and p = 2."""
    r = dowel.analyse({
        "assembly": "Stahl-Holz, Schlitzbleche",
        "d": 12.0, "f_u_k": 510.0, "n_tot": 6, "impact": False, "truss": False,
        "members": [_member(alpha=90, t=200, n=3, a_1=60)],
        "steel": {"plates": 1, "slot": 12.0, "ratio": 0.5, "grade": "S235"},
    })
    assert r["p"] == 2 and len(r["planes"]) == 1
    _close(r["geometry"]["t_1"], (200 - 12) / 2.0)
    assert r["geometry"]["t_2"] == 0


# --- the defect the workbook carries -----------------------------------------

def test_the_norm_and_not_the_workbook_at_beta_f_other_than_one():
    """Tabelle 45 equations (125): the *einschnittig* second member's corners carry sqrt(1/(1+beta_f)) + 1, member 2's own bracket.

    `Verbindung.xlsm!'Stabdübel (Holz-Holz)'!O34/P34` write sqrt(beta_f/(1+beta_f)) + 1 there -- member 1's. The two are equal only at beta_f = 1. Here C24 (rho_k 350) meets D30 (rho_k 530), so beta_f is about 1.51 and the difference is real: the module must give the norm's value, which is the *smaller* required thickness, and must differ from the workbook's by more than rounding.
    """
    r = dowel.analyse({
        "assembly": "Holz-Holz einschnittig",
        "d": 12.0, "f_u_k": 510.0, "n_tot": 6, "impact": False, "truss": False,
        "members": [
            _member(rho=sia265.rho_k("C24"), species=sia265.species("C24"), t=60, n=3, a_1=80),
            _member(rho=sia265.rho_k("D30"), species=sia265.species("D30"), t=80, n=3, a_1=80),
        ],
    })
    beta_f = r["beta_f"]
    assert beta_f > 1.2, "the two grades must actually differ for this test to say anything"

    base_2 = math.sqrt(510.0 / r["f_h_2_k"]) * 12.0 ** 0.8
    norm_bracket = math.sqrt(1 / (1 + beta_f)) + 1        # equation (125)
    workbook_bracket = math.sqrt(beta_f / (1 + beta_f)) + 1  # what O34/P34 use

    _close(r["corners"][1]["t_1"], 0.44 * norm_bracket * base_2)
    _close(r["corners"][1]["t_2"], 1.26 * norm_bracket * base_2)
    assert abs(norm_bracket - workbook_bracket) > 0.05, (
        "the two brackets must be far enough apart for the assertion above to mean something")


# --- invariants --------------------------------------------------------------

def test_k_beta_is_continuous_and_monotone():
    """Figur 45's shape: 0 at t = 0, k_1 at t_1, k_2 at t_2, flat beyond, and never decreasing in between. A swapped corner breaks this; a merely wrong coefficient does not, which is why it is worth checking separately from the values."""
    corner = (30.0, 0.6 * math.sqrt(2), 80.0, math.sqrt(2))
    previous = -1.0
    for step in range(0, 241):
        t = step * 1.0
        value = dowel._bilinear(t, *corner)
        assert value >= previous - 1e-12, "k_beta dipped at t = %s" % t
        previous = value
    _close(dowel._bilinear(0.0, *corner), 0.0)
    _close(dowel._bilinear(30.0, *corner), 0.6 * math.sqrt(2))
    _close(dowel._bilinear(80.0, *corner), math.sqrt(2))
    _close(dowel._bilinear(800.0, *corner), math.sqrt(2))


def test_f_h_k_interpolates_across_the_angle():
    """Tabelle 22's footnote: «Bei einem Kraftangriff schräg zur Faserrichtung dürfen die Werte linear interpoliert werden»."""
    at_0 = dowel.embedment_strength(385, 12, 0, "Nadelholz", True)
    at_90 = dowel.embedment_strength(385, 12, 90, "Nadelholz", True)
    at_45 = dowel.embedment_strength(385, 12, 45, "Nadelholz", True)
    _close(at_0["f_h_alpha_k"], at_0["f_h_0_k"])
    _close(at_90["f_h_alpha_k"], at_90["f_h_90_k"])
    _close(at_45["f_h_alpha_k"], (at_0["f_h_0_k"] + at_0["f_h_90_k"]) / 2)


def test_an_undrilled_hole_has_one_value_in_both_directions():
    """Tabelle 22's second row gives 0.082 · d^-0.3 · rho_k for both directions, so the angle does not enter."""
    for alpha in (0, 45, 90):
        f = dowel.embedment_strength(385, 12, alpha, "Nadelholz", False)
        _close(f["f_h_alpha_k"], 0.082 * 12 ** -0.3 * 385)


def test_the_slices_add_up_to_the_member():
    """A slotted member is two side pieces, (n-1) middle pieces and n slots, and nothing else."""
    for plates, ratio in ((1, 0.5), (2, 0.5), (3, 0.4), (4, 0.6)):
        g = dowel.steel_geometry(300.0, 10.0, plates, ratio)
        total = 2 * g["t_1"] + (plates - 1) * g["t_2"] + plates * 10.0
        _close(total, 300.0)


def test_a_thick_timber_reaches_the_plateau():
    """Past t_i,2 the resistance stops growing with the thickness -- the dowel yields first."""
    thin = dowel.analyse(dict(HOLZ_HOLZ, members=[_member(t=1000, n=4, a_1=100), _member(t=1000, n=4, a_1=100)]))
    thicker = dowel.analyse(dict(HOLZ_HOLZ, members=[_member(t=5000, n=4, a_1=100), _member(t=5000, n=4, a_1=100)]))
    _close(thin["R_d_Verb"], thicker["R_d_Verb"])
    _close(thin["k_beta"], math.sqrt(2))


# --- the warnings ------------------------------------------------------------

def test_a_spacing_below_tabelle_24_warns_and_does_not_stop():
    """SIA 265 6.2.1.1 makes equation (88) conditional on the minimum distances being kept, so a pattern that breaks one is said loudly -- and still calculated, because the fix is a layout the engineer moves, not a defect in the data (the v0.33 rule)."""
    pattern = [{"x": -60, "z": -60}, {"x": 60, "z": -60}, {"x": -60, "z": 60}, {"x": 60, "z": 60}]
    generous = dowel.check_spacings(pattern, 8.0, 0)   # 7·8 = 56 mm needed, 120 mm there
    assert generous["warnings"] == []
    assert generous["rows"][0]["ok_parallel"] is True

    # at d = 20 the two directions part company: 7·20 = 140 mm is not there, 3·20 = 60 mm is
    tight = dowel.check_spacings(pattern, 20.0, 0)
    assert len(tight["warnings"]) == 1, tight["warnings"]
    assert "Faserrichtung" in tight["warnings"][0]
    assert "Tabelle 24" in tight["warnings"][0] and "6.2.1.1" in tight["warnings"][0]
    assert tight["rows"][0]["ok_parallel"] is False
    assert tight["rows"][0]["ok_perpendicular"] is True

    # and at d = 45 neither is: 7·45 = 315 mm and 3·45 = 135 mm against 120 mm
    both = dowel.check_spacings(pattern, 45.0, 0)
    assert len(both["warnings"]) == 2, both["warnings"]


def test_the_validity_conditions_of_the_multi_plate_equations_are_checked():
    """Tabelle 46 prints «wenn t_2 >= 2 · t_1» over equation (130) and «wenn t_1 >= 0,35 · t_2» over (131). The workbook enforces them only through the data validation of its cell C20 (0.35 <= t_1/t_2 <= 0.5), which a typed-over value bypasses; here the condition is reported, with the two thicknesses, and the number is still given."""
    r = dowel.analyse({
        "assembly": "Stahl-Holz, Schlitzbleche",
        "d": 12.0, "f_u_k": 510.0, "n_tot": 6, "impact": False, "truss": False,
        "members": [_member(alpha=90, t=200, n=3, a_1=60)],
        "steel": {"plates": 2, "slot": 12.0, "ratio": 0.9, "grade": "S235"},
    })
    assert any("(130)" in w for w in r["warnings"]), r["warnings"]
    assert r["R_d_Verb"] > 0, "the resistance is still given -- only the condition is reported"
    # the workbook's own ratio of 0.5 sits exactly on the boundary and earns no warning
    assert dowel.analyse(dict(STAHL_HOLZ))["warnings"] == []


def test_members_in_different_moisture_classes_warn_and_the_worst_governs():
    r = dowel.analyse(dict(HOLZ_HOLZ, members=[_member(t=70, n=4, a_1=100, moisture=2),
                                               _member(t=100, n=4, a_1=100, moisture=1)]))
    assert r["moisture_class"] == 2 and r["eta_w"] == 0.8
    assert any("Feuchteklasse" in w for w in r["warnings"]), r["warnings"]
    plain = dowel.analyse(dict(HOLZ_HOLZ))
    _close(r["R_d_Verb"], plain["R_d_Verb"] * 0.8)


def test_a_diameter_outside_the_norms_range_warns():
    """6.2.1.1 states equation (88) for d = 6 to 30 mm."""
    r = dowel.analyse(dict(HOLZ_HOLZ, d=36.0))
    assert any("6.2.1.1" in w for w in r["warnings"]), r["warnings"]


def test_seismic_raises_by_the_norms_factor():
    plain = dowel.analyse(dict(HOLZ_HOLZ))
    quake = dowel.analyse(dict(HOLZ_HOLZ, impact=True))
    assert quake["eta_t"] == 1.4
    _close(quake["R_d_Verb"], plain["R_d_Verb"] * 1.4)


# --- the refusals ------------------------------------------------------------

def test_hardwood_without_predrilling_is_refused():
    """Tabelle 22 gives Laubholz one row only, «vorgebohrt». Reading the softwood row for it would be an answer the norm does not give."""
    message = _raised(dowel.embedment_strength, 530, 12, 0, "Laubholz", False)
    assert "Tabelle 22" in message


def test_a_configuration_the_norm_does_not_cover_says_why():
    """Tabelle 45 covers ein- and zweischnittig, Tabelle 46 zwei- and mehrschnittig. For anything else 6.1.1.11 sends the engineer to testing -- which is a different answer from «unknown assembly»."""
    for assembly in ("Holz-Holz mehrschnittig", "Stahl-Holz, Blech aussen, einschnittig", "Holz-Beton"):
        message = _raised(dowel.analyse, dict(HOLZ_HOLZ, assembly=assembly))
        assert "6.1.1.11" in message, message


def test_an_unknown_assembly_lists_the_four():
    message = _raised(dowel.analyse, dict(HOLZ_HOLZ, assembly="Holz-Holz dreischnittig"))
    for assembly in dowel.ASSEMBLIES:
        assert assembly in message


def test_a_member_without_a_moisture_class_is_refused():
    message = _raised(dowel.analyse, dict(HOLZ_HOLZ, members=[_member(t=70, n=1, moisture=None),
                                                              _member(t=100, n=1)]))
    assert "Tabelle 4" in message


def test_a_row_of_two_without_a_spacing_is_refused():
    """k_red needs a_1 as soon as two dowels follow one another; with one there is nothing to ask for."""
    assert "a_1" in _raised(dowel.reduction, 3, None, 12.0, 0)
    _close(dowel.reduction(1, None, 12.0, 0), 1.0)


def test_no_dowels_is_refused():
    assert "at least one dowel" in _raised(dowel.analyse, dict(HOLZ_HOLZ, n_tot=0))


def test_a_member_swallowed_by_its_slots_is_refused():
    assert "no timber is left" in _raised(dowel.steel_geometry, 20.0, 12.0, 2, 0.5)


def test_the_einschnittig_row_and_outer_plates_reproduce_the_workbook():
    """v0.77: «k_beta est calculé d'après une formule -- vérifie avec l'excel que tes calculs fonctionnent toujours». The rows of Verbindung.xlsm the zweischnittig test does not read: «Stabdübel (Holz-Holz)» row 34, einschnittig, and «Stabdübel (Stahl-Holz)» row 23, seitliche Stahllaschen -- which the workbook evaluates at t_1 = C18 = 44 mm. k_beta is interpolated on Figur 45 between the corners of Tabellen 45/46, never a fixed number: 1.335 here because t_1 = 70 mm lies between t_1,1 = 26.9 and t_1,2 = 77.0 mm."""
    r = dowel.analyse(dict(HOLZ_HOLZ, assembly="Holz-Holz einschnittig"))
    _close(r["corners"][0]["t_1"], 26.885267629189244)  # M34
    _close(r["corners"][0]["t_2"], 76.98963002904193)   # N34
    _close(r["corners"][1]["t_1"], 26.885267629189244)  # O34
    _close(r["corners"][1]["t_2"], 76.98963002904193)   # P34
    _close(r["corners"][0]["k_beta"], 1.33529963863802)  # Q34
    _close(r["corners"][1]["k_beta"], 1.4142135623730951)  # R34
    _close(r["k_beta"], 1.33529963863802)               # S34
    assert r["p"] == 1
    outer = dict(STAHL_HOLZ, assembly="Stahl-Holz, Bleche aussen", members=[_member(alpha=90, t=44, n=3, a_1=60)])
    plane = dowel.analyse(outer)["planes"][0]
    _close(plane["t_2"], 68.86795318709748)             # O23
    _close(plane["k_beta"], 0.9035464808336167)         # P23
    # k_beta moves with the thickness: the same joint 10 mm thinner reads a smaller value off the same line
    thinner = dowel.analyse(dict(HOLZ_HOLZ, members=[_member(t=60, n=4, a_1=100), _member(t=100, n=4, a_1=100)]))
    assert thinner["k_beta"] < r["k_beta"]


def test_the_k_beta_table_carries_one_curve_per_thickness():
    """Figur 45 at level 3 (v0.77): the k_beta table states the line each thickness is read off -- t_1 and t_2 of a Holz-Holz joint, Scherfuge A and B of slotted plates -- a Mittelholz with its lower corner at the origin."""
    two = dowel._k_beta_figures(dowel.analyse(dict(HOLZ_HOLZ)))["curves"]
    assert [(c["index"], c["label"], c["role"]) for c in two] == [(1, "Bauteil 1", "Seitenholz"), (2, "Bauteil 2", "Mittelholz")]
    one = dowel._k_beta_figures(dowel.analyse(dict(HOLZ_HOLZ, assembly="Holz-Holz einschnittig")))["curves"]
    assert [c["role"] for c in one] == ["Seitenholz", "Seitenholz"]
    steel = dowel._k_beta_figures(dowel.analyse(dict(STAHL_HOLZ)))["curves"]
    assert [(c["index"], c["label"], c["role"]) for c in steel] == [(1, "Scherfuge A", "Seitenholz"), (2, "Scherfuge B", "Mittelholz")]
    for c in two + steel:
        _close(dowel._bilinear(c["t"], c["t_1"], c["k_1"], c["t_2"], c["k_2"]), c["k_beta"])


def test_the_truss_reduction_states_its_condition_once():
    """Spec 2026-10-12-audit-issues-47-48-49, REQ-009 (D-08): SIA 265 5.3.6.2.2 (p. 51) fixes 0.75 only for the connections of the infill members with a high bending stiffness, under the simplified calculation of 5.3.6.1.2. The norm file states that condition in one sentence, the report prints it under R_d,Fachwerk, and the glossary translates it -- which the window shows under its box."""
    from i18n import strings
    condition = sia265.clause("truss_reduction")["condition"]
    assert "grosser Biegesteifigkeit" in condition and "Ausfachungsstäbe" in condition and "5.3.6.1.2" in condition
    r = dowel.analyse(dict(HOLZ_HOLZ, truss=True))
    record = dowel.record("SD_T", r, HOLZ_HOLZ["members"])
    assert record["vars"]["R_d_Fachwerk"]["description"] == condition
    for lang in ("fr", "en"):
        assert strings.translate(condition, lang) != condition, lang


def _plate(**change):
    plate = {"d": 12.0, "t": 8.0, "e1": 24.0, "e2": 18.0, "d0": 12.0, "p1": None, "p2": None, "count": 2, "grade": "S235"}
    plate.update(change)
    return plate


def test_the_plates_bearing_is_sia_263_tabelle_16_capped_as_a_bolzen():
    """Spec 2026-10-12-audit-issues-47-48-49, REQ-008 (D-13, D-16): SIA 263:2013 Tabelle 16 (76), p. 67, F_b,Rd = 0.85 · e1/d0 · f_u · d · t / gamma_M2 <= 2.4 · f_u · d · t / gamma_M2, capped by 6.2.5 (p. 70) at 1.5 · f_y · d · t / gamma_M2, gamma_M2 = 1.25 (4.1.3). By hand, S235 (f_u 360, f_y 235), d 12, t 8, d0 12: e1 24 gives (76) 47.0016 kN, the bound 66.3552 kN and the Bolzen's cap 27.072 kN, which governs -- two plates, 54.144 kN per dowel; e1 12 gives (76) 23.5008 kN, which governs."""
    r = dowel.plate_bearing(_plate())
    _close(r["F_76"], 0.85 * 24 / 12 * 360 * 12 * 8 / 1.25 / 1000)
    _close(r["F_max"], 2.4 * 360 * 12 * 8 / 1.25 / 1000)
    _close(r["F_pin"], 1.5 * 235 * 12 * 8 / 1.25 / 1000)
    _close(r["F_b_Rd"], 2 * 27.072)
    assert r["warnings"] == [] and not r["tight"]
    _close(dowel.plate_bearing(_plate(e1=12.0))["F_b_Rd"], 2 * 23.5008)


def test_a_tight_p1_replaces_e1_and_a_narrow_pattern_warns():
    """Tabelle 16: with p1 < e1 + d0/2, p1 − d0/2 stands for e1 in (76); e2 < 1.0 d0 and p2 < 2.0 d0 lie outside (76)'s premise and warn, nothing stops. A hole smaller than the dowel is refused."""
    r = dowel.plate_bearing(_plate(p1=24.0, e2=10.0, p2=20.0))
    assert r["tight"] and r["e1_eff"] == 18.0
    _close(r["F_76"], 0.85 * 18 / 12 * 360 * 12 * 8 / 1.25 / 1000)
    assert len(r["warnings"]) == 2 and "$e_2$" in r["warnings"][0] and "$p_2$" in r["warnings"][1]
    _raised(dowel.plate_bearing, _plate(d0=10.0))


def test_the_plates_bearing_is_a_result_beside_r_d():
    """D-13: F_b,Rd is a result of its own, printed with its steps under SIA 263, and R_d is untouched."""
    plain = dowel.analyse(dict(STAHL_HOLZ))
    with_plate = dict(plain, plate=dowel.plate_bearing(_plate()))
    record = dowel.record("SD_P", with_plate, STAHL_HOLZ["members"])
    assert record["results"][-1] == "F_b_Rd" and abs(record["vars"]["F_b_Rd"]["value"] - 54.144) < 1e-9
    assert record["vars"]["F_b_Rd"]["norm"] == "SIA 263" and record["vars"]["f_u_pl"]["description"] == "Stahl S235"
    assert record["vars"]["R_d"]["value"] == dowel.record("SD_P", plain, STAHL_HOLZ["members"])["vars"]["R_d"]["value"]
    assert "F_b_Rd" not in dowel.record("SD_P", plain, STAHL_HOLZ["members"])["vars"]
