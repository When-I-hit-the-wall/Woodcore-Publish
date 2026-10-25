"""SIA 265/1:2018 as Woodcore reads it (calc/norms/sia265_1.py, spec docs/requirements/active/2026-10-24-onglet-materiaux.md, ARCH-002, D-14; issue #110).

What is held:

* every file read and checked: one edition, each product of Tableau 9 in a group of Tableau 6, each panel the shape of a material, each id once;
* **the transcription holds together**: every design value of a b table is the norm's own rounding of η_mod · f_k / γ_M from its a table -- 20 panels, both halves read off the page separately, agree;
* the values the issue checked (T29, T35): γ_M and η_mod of the prototype's twelve products, OSB/3's 18 → 10.5, 10 → 5.8, 1.0 → 0.6;
* a product the norm does not admit in a class («na», no row) refused, naming it.
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest  # noqa: F401  -- calc/ on the path
import validation
from norms import sia265_1


def test_every_file_is_read_and_held_together():
    assert sia265_1.check()
    assert sia265_1.edition() == "SIA 265/1:2018"
    assert len(sia265_1.panels()) == 20
    assert {p["table"] for p in sia265_1.panels()} == {str(n) for n in range(11, 24)}


def test_each_b_table_is_its_a_table_by_eta_mod_over_gamma_m():
    """Both halves of a page were read separately: a design value off by more than the norm's rounding (0.05, or 2 % of a small one) is a misread cell."""
    off = []
    for p in sia265_1.panels():
        gamma, eta = sia265_1.product_gamma_m(p["product"]), sia265_1.eta_mod(p["product"])
        for loading, rows in p["grid"].items():
            for key, cells in rows.items():
                if not key.endswith("_d"):
                    continue
                for direction, values in cells.items():
                    for i, d in enumerate(values):
                        k = rows[key[:-2] + "_k"][direction][i]
                        assert (d is None) == (k is None), (p["id"], loading, key, direction, i)
                        if d is not None and abs(eta * k / gamma - d) > 0.051 and abs(eta * k / gamma - d) / d > 0.02:
                            off.append((p["id"], loading, key, direction, i, k, d))
    assert not off, off


def test_every_value_transcribed_is_on_its_page():
    """ARCH-002: every number of Tableaux 11 to 23 -- ρ_k and each cell of a and b -- is among the numbers of its page's text layer, so that a value typed wrong in a file shows (the halves holding each other, above, would not catch a misread repeated in both)."""
    import re
    import conftest
    pdf = conftest.norms_library() / "SIA265-1-2018-FR.pdf"
    if not pdf.is_file():
        raise conftest.Skip("SIA265-1-2018-FR.pdf is not in norm-library/")
    from pypdf import PdfReader
    pages = PdfReader(str(pdf)).pages
    missing = []
    for p in sia265_1.panels():
        text = pages[p["page"] - 1].extract_text(extraction_mode="layout").replace("\u202f", " ")
        found = {round(float(t.replace(",", ".")), 3) for t in re.findall(r"(?<![\w,])\d+(?:,\d+)?(?![\w])", text)}
        for run in re.findall(r"\d{4,}", text):   # cells of one value side by side the layer writes as one run: «505050505050» is six cells of 50 (Tableaux 18a to 20a, G_mean)
            for k in (2, 3):
                if len(run) % k == 0 and run == run[:k] * (len(run) // k):
                    found.add(float(run[:k]))
        values = [v for v in p["rho_k"] if v is not None]
        for rows in p["grid"].values():
            for cells in rows.values():
                for column in cells.values():
                    values += [v for v in column if v is not None]
        missing += [(p["id"], v) for v in values if round(float(v), 3) not in found]
    assert not missing, "not on the page: %s" % missing[:20]


def test_the_prototypes_factors_are_the_norms():
    """T29: the table the issue proposed, read again on Tableaux 6 and 9 (class 1, medium duration)."""
    expected = {"swp": (1.3, 0.80), "clt": (1.25, 0.80), "lvl": (1.2, 0.80), "plywood": (1.2, 0.80), "p4": (1.3, 0.65), "p5": (1.3, 0.65), "p6": (1.3, 0.70), "p7": (1.3, 0.70),
                "cement": (1.3, 0.65), "osb2": (1.2, 0.65), "osb3": (1.2, 0.70), "osb4": (1.2, 0.70), "hb": (1.3, 0.65), "mbh": (1.3, 0.60), "mdf_la": (1.3, 0.60), "mdf_hls": (1.3, 0.60)}
    for product, (gamma, eta) in expected.items():
        assert (sia265_1.product_gamma_m(product), sia265_1.eta_mod(product)) == (gamma, eta), product


def test_osb3_is_the_prototypes():
    osb3 = next(p for p in sia265_1.panels() if p["id"] == "osb3")
    plate = osb3["grid"]["plate"]
    assert plate["f_m_k"]["par"] == [18.0, 16.4, 14.8] and plate["f_m_d"]["par"] == [10.5, 9.6, 8.6]
    assert plate["f_c_90_d"]["par"] == [5.8] * 3 and plate["f_v_d"]["perp"] == [0.6] * 3
    assert osb3["rho_k"] == [550] * 3 and osb3["page"] == 42
    assert [(c["t_min"], c["t_max"]) for c in osb3["columns"]] == [(6, 10), (10, 18), (18, 25)]


def test_a_product_not_admitted_is_refused_naming_it():
    assert sia265_1.eta_mod("mdf_hls", 2, "short") == 0.45
    for product, cls, kled in (("mdf_hls", 2, "medium"), ("osb2", 2, "medium"), ("osb3", 3, "short")):
        try:
            sia265_1.eta_mod(product, cls, kled)
        except validation.ValidationError as exc:
            assert product in str(exc)
        else:
            raise AssertionError((product, cls, kled))
    try:
        sia265_1.gamma_m("gypsum_fibre")
    except validation.ValidationError as exc:
        assert "to be determined" in str(exc)
    else:
        raise AssertionError("γ_M of gypsum fibre boards guessed")


def test_the_kled_and_the_accidental_gamma_m_are_the_norms():
    """Issue #112, REQ-006: Tableaux 7 and 8 (p. 27) and note 1 of Tableau 6 -- the classes in Tableau 9's order, snow ≤ 1000 m short and above medium, impacts and earthquakes very short, γ_M = 1,0 accidental; OSB/3 admitted in classes 1 and 2, MDF.HLS in class 2 for short and very short only."""
    assert tuple(c["id"] for c in sia265_1.kled_classes()) == sia265_1.KLED
    assert [c["duration"] for c in sia265_1.kled_classes()][-1] is None, "the norm leaves «très courte» blank"
    by_action = {(r["action"], r["sia261"]): r["kled"] for r in sia265_1.kled_actions()}
    assert by_action[("Neige pour une altitude de référence h0 ≤ 1000 m", "5")] == "short"
    assert by_action[("Neige pour une altitude de référence h0 > 1000 m", "5")] == "medium"
    assert by_action[("Actions accidentelles: Choc", "14")] == by_action[("Actions accidentelles: Séisme", "16")] == "very_short"
    assert by_action[("Poids propre et surcharges", "2")] == "permanent" and by_action[("Vent", "6")] == "short"
    assert sia265_1.accidental_gamma_m() == 1.0
    assert sia265_1.design_gamma_m("osb3") == 1.2 and sia265_1.design_gamma_m("osb3", accidental=True) == 1.0
    assert sia265_1.admitted_classes("osb3") == (1, 2) and sia265_1.admitted_classes("osb2") == (1,)
    assert sia265_1.admitted_kled("mdf_hls", 2) == ("short", "very_short") and sia265_1.admitted_kled("osb3", 3) == ()


def test_the_kled_tables_are_on_their_page():
    """Every word of Tableaux 7 and 8 transcribed is in the text layer of p. 27, and «Tableau 6» note 1 on p. 26 (ARCH-002: held to the PDF)."""
    import conftest
    import json
    pdf = conftest.norms_library() / "SIA265-1-2018-FR.pdf"
    if not pdf.is_file():
        raise conftest.Skip("SIA265-1-2018-FR.pdf is not in norm-library/")
    from pypdf import PdfReader
    pages = PdfReader(str(pdf)).pages
    page = " ".join(pages[26].extract_text().replace("’", "'").split())
    data = json.loads((sia265_1.HERE / (sia265_1.TAB07 + ".json")).read_text(encoding="utf-8"))
    for c in data["table_7"]["classes"]:
        assert c["label"] in page and (c["duration"] is None or c["duration"] in page), c
    for r in data["table_8"]["rows"]:
        last = r["action"].split(": ")[-1].replace("h0", "h0").split(" pour ")[0]
        assert last in page, r
    assert "fixé à 1,0 pour les situations" in " ".join(pages[25].extract_text().split())
