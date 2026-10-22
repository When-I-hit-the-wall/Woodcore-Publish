"""The Reduktionsbeiwerte of SIA 260:2013 Tabelle 2 (calc/norms/sia260.py, docs/domain/loads.md §3.3septies, docs/architecture/layout.md §11).

What a load combination will scale a variable action by (SIA 260 4.4.3, equations (16) to (23)) is ψ0, ψ1 or ψ2 of Tabelle 2. **They are transcribed and checked here for the combinations to come, and shown nowhere for the live loads** (the engineer, 01.10.2026): no instance of the live-load domain carries them any more, and no live-load table prints them -- the last tests of this file hold that. What is held here is what decides each of the table's words:

* **the values are the page's.** Transcribed by hand from `SIA260-2013-DE.pdf` p. 33, so the table is written out a second time below, from the render of the page, and -- where the library is here -- read back out of the German, French and English editions' text layers, which print the same thirty-nine cells;
* **the checks fire.** Every guard of `sia260._check_table_2` is exercised against a planted defect: a guard that has never fired is a guard nobody has tested, and these ones only ever run on a file that is already right;
* **snow is a formula and is never evaluated** -- a number handed out for it would be a value the norm does not state;
* **a category of SIA 261 Tabelle 8 reaches its row** (A1 to A3 to A, C1 to C3 to C), every one of the twelve, category E included although it has no load;
* **no instance of the live-load domain carries the three factors**, the export still validating and the loads unchanged.

⚠️ The page check is skipped where the reference library is not beside the program.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import conftest
from conftest import ROOT, Skip
from domains import live_load
from i18n import strings as glossary
from norms import sia260, sia261
import validation

PROJECT = conftest.PROJECT
NAME = sia260.TAB02
LIBRARY = conftest.norms_library()  # the folder of the norms' PDFs, named by WOODCORE_NORMS_LIBRARY on a machine that has it (spec 2026-10-19-base-saine-nettoyage, REQ-004)

# Tabelle 2, p. 33, written out a second time from the render of the page (German edition): id, ψ0, ψ1, ψ2. Independent of the JSON on purpose -- a typo in one is caught by the other.
PAGE_33 = (
    ("A", 0.7, 0.5, 0.3),
    ("B", 0.7, 0.5, 0.3),
    ("C", 0.7, 0.7, 0.6),
    ("D", 0.7, 0.7, 0.6),
    ("E", 1.0, 0.9, 0.8),
    ("F", 0.7, 0.7, 0.6),
    ("G", 0.7, 0.5, 0.3),
    ("H", 0, 0, 0),
    ("wind", 0.6, 0.5, 0),
    ("temperature", 0.6, 0.5, 0),
    ("earth-pressure", 0.7, 0.7, 0.7),
    ("water-pressure", 0.7, 0.7, 0.7),
)

PSI = ("psi_0", "psi_1", "psi_2")


def _refuses(mutate, because):
    """`_check_table_2` on a doctored copy of the file must raise; returns the message."""
    data = copy.deepcopy(sia260._read(NAME, sia260._check_table_2))
    mutate(data["table_2"])
    try:
        sia260._check_table_2(NAME, data)
    except validation.ValidationError as exc:
        return str(exc)
    raise AssertionError("calc/norms/%s.json: the check passed a table %s -- it should have refused it" % (NAME, because))


def _row(table, row_id):
    return next(r for r in table["rows"] if r["id"] == row_id)


# --- the file -------------------------------------------------------------------

def test_the_file_reads_checks_and_names_its_edition():
    assert sia260.check_all() == "SIA 260:2013"
    assert sia260.edition() == "SIA 260:2013"
    assert NAME in sia260.FILES == (NAME,)
    assert (sia260.HERE / (NAME + ".json")).is_file()
    table = sia260.table_2()
    assert (table["number"], table["norm"], table["norm_ref"], table["annex"]) == ("2", "SIA 260", "Tabelle 2", "Anhang A")
    assert table["title"] == "Reduktionsbeiwerte für Gebäude"


def test_every_value_of_tabelle_2_is_the_pages():
    """All thirty-six numbers, against the table written out from the render of p. 33."""
    assert [r["id"] for r in sia260.rows()] == ["A", "B", "C", "D", "E", "F", "G", "H", "snow", "wind", "temperature",
                                                "earth-pressure", "water-pressure"], "the norm's own order"
    for row_id, psi0, psi1, psi2 in PAGE_33:
        got = sia260.psi(row_id)
        assert tuple(got) == PSI
        assert (got["psi_0"], got["psi_1"], got["psi_2"]) == (psi0, psi1, psi2), row_id
    assert len(PAGE_33) == 12, "twelve rows of numbers and the snow formula make the table's thirteen"


def test_the_groups_and_names_are_the_tables():
    groups = {r["id"]: r["group"] for r in sia260.rows()}
    assert {groups[c] for c in "ABCDE"} == {"Nutzlasten in Gebäuden"}
    assert {groups[c] for c in "FGH"} == {"Verkehrslasten in Gebäuden"}
    assert groups["snow"] is None and groups["wind"] is None and groups["temperature"] is None
    assert {groups["earth-pressure"], groups["water-pressure"]} == {"Einwirkungen aus dem Baugrund"}
    names = {r["id"]: r["name"] for r in sia260.rows()}
    assert names["A"] == "Wohnflächen" and names["E"] == "Lagerflächen" and names["H"] == "Dächer"
    assert names["G"] == "Fahrzeuge von 3.5 bis 16 t" and names["wind"] == "Windkräfte"


def test_the_symbols_carry_the_norms_own_words():
    """1.2.4 (p. 18): the three definitions, and the clauses 3.2.3.2 to 3.2.3.4 (p. 23) that say what each scales."""
    symbols = sia260.symbols()
    assert tuple(symbols) == PSI
    assert symbols["psi_0"]["label"] == "Reduktionsbeiwert für den seltenen Wert einer veränderlichen Einwirkung"
    assert symbols["psi_1"]["label"] == "Reduktionsbeiwert für den häufigen Wert einer veränderlichen Einwirkung"
    assert symbols["psi_2"]["label"] == "Reduktionsbeiwert für den quasi-ständigen Wert einer veränderlichen Einwirkung"
    assert [symbols[k]["defined_in"][-1] for k in PSI] == ["3.2.3.2", "3.2.3.3", "3.2.3.4"]


def test_a_reduktionsbeiwert_never_grows_from_psi_0_to_psi_2():
    """The rare value is never the smaller of the three: a property of the norm's own table, which a transcription error would break before any other."""
    for row in sia260.rows():
        if "variable" in row:
            continue
        a, b, c = (row[k] for k in PSI)
        assert 0 <= c <= b <= a <= 1, (row["id"], a, b, c)


# --- snow: a formula, transcribed as printed and never evaluated ----------------------

def test_snow_is_a_formula_in_h0_as_the_norm_prints_it():
    snow = sia260.snow()
    assert snow["name"] == "Schneelasten" and snow["group"] is None
    assert snow["variable"] == {"symbol": "h_0", "name": "Bezugshöhe gemäss der Norm SIA 261", "unit": "m",
                                "norm": "SIA 261", "norm_ref": "Anhang D"}
    assert [snow[k]["printed"] for k in PSI] == ["1 – 60/h0", "1 – 250/h0", "1 – 1000/h0"]
    assert [snow[k]["formula"] for k in PSI] == ["1 - 60 / h_0", "1 - 250 / h_0", "1 - 1000 / h_0"]
    assert [snow[k]["c"] for k in PSI] == [60, 250, 1000]


def test_snow_has_no_number_to_give():
    """`psi` refuses it saying so, rather than returning something the norm does not state."""
    try:
        sia260.psi("snow")
    except ValueError as exc:
        assert "formula" in str(exc) and "h_0" in str(exc), str(exc)
    else:
        raise AssertionError("sia260.psi('snow') returned a number")
    # and the reader offers no function that evaluates it: the only accessor of the row is the row as the norm prints it
    assert not [n for n in dir(sia260) if "snow" in n.lower() and n != "snow"], "the reader grew a second snow accessor"
    assert "eval(" not in (ROOT / "calc" / "norms" / "sia260.py").read_text(encoding="utf-8"), "the reader evaluates a string"


def test_an_unknown_row_lists_the_rows_there_are():
    try:
        sia260.row("hail")
    except KeyError as exc:
        assert "snow" in str(exc) and "water-pressure" in str(exc), str(exc)
    else:
        raise AssertionError("an unknown row was found")


# --- a category of SIA 261 Tabelle 8 reaches its row --------------------------------

def test_every_category_of_tabelle_8_reaches_its_row():
    categories = [r["id"] for r in sia261.table_8()["categories"]]
    assert len(categories) == 12
    for category in categories:
        assert sia260.live_load_row(category) in sia260.LIVE_LOAD_ROWS, category
    assert [sia260.live_load_row(c) for c in ("A1", "A2", "A3")] == ["A"] * 3
    assert [sia260.live_load_row(c) for c in ("C1", "C2", "C3")] == ["C"] * 3
    assert [sia260.live_load_row(c) for c in ("B", "D", "E", "F", "G", "H")] == ["B", "D", "E", "F", "G", "H"]
    # a subcategory takes its category's factors, to the digit
    assert sia260.live_load_psi("A2") == sia260.psi("A") and sia260.live_load_psi("C3") == sia260.psi("C")
    assert sia260.live_load_psi("E") == {"psi_0": 1.0, "psi_1": 0.9, "psi_2": 0.8}


def test_a_category_the_table_has_no_row_for_is_refused_naming_the_rows():
    for bad in ("X", "snow", "a1", "", "1A", "AA", None):
        try:
            sia260.live_load_row(bad)
        except KeyError as exc:
            assert "A, B, C, D, E, F, G, H" in str(exc), str(exc)
        else:
            raise AssertionError("%r was given a row" % (bad,))


# --- the checks fire --------------------------------------------------------------

def test_the_checks_refuse_what_a_transcription_error_looks_like():
    def set_value(row_id, key, value):
        return lambda table: _row(table, row_id).__setitem__(key, value)

    cases = (
        (set_value("A", "psi_0", 1.2), "with a factor above 1", "between 0 and 1"),
        (set_value("A", "psi_2", -0.1), "with a negative factor", "between 0 and 1"),
        (set_value("A", "psi_1", 0.9), "whose ψ1 is larger than its ψ0", "never the smaller"),
        (set_value("wind", "psi_2", 0.9), "whose ψ2 is larger than its ψ1", "never the smaller"),
        (set_value("B", "psi_0", "0,7"), "with a factor that is text, not a number", "expected a number"),
        (set_value("C", "psi_1", True), "with a factor that is a boolean", "expected a number"),
        (set_value("H", "psi_0", None), "with a factor left out", "expected a number"),
    )
    for mutate, because, word in cases:
        message = _refuses(mutate, because)
        assert word in message, (because, message)


def test_the_checks_refuse_a_table_with_a_row_missing_or_twice():
    message = _refuses(lambda t: t["rows"].remove(_row(t, "wind")), "without its wind row")
    assert "wind" in message and "lacks" in message, message
    message = _refuses(lambda t: t["rows"].remove(_row(t, "E")), "without category E")
    assert "E" in message, message
    message = _refuses(lambda t: t["rows"].append(dict(_row(t, "A"))), "listing category A twice")
    assert "listed twice" in message, message
    message = _refuses(lambda t: _row(t, "B").__setitem__("name", ""), "with a nameless row")
    assert "no name" in message, message
    message = _refuses(lambda t: _row(t, "B").pop("group"), "with a row that does not say its group")
    assert "group" in message, message


def test_the_checks_refuse_snow_written_as_numbers_and_a_number_written_as_a_formula():
    def snow_as_numbers(table):
        row = _row(table, "snow")
        row.pop("variable")
        for k, v in zip(PSI, (0.9, 0.8, 0.5)):
            row[k] = v

    message = _refuses(snow_as_numbers, "carrying snow as three numbers")
    assert "formula" in message and "snow" in message, message

    def wind_as_formula(table):
        row = _row(table, "wind")
        row["variable"] = dict(_row(table, "snow")["variable"])
        for k in PSI:
            row[k] = dict(_row(table, "snow")[k])

    message = _refuses(wind_as_formula, "carrying wind as a formula")
    assert "wind" in message and "number" in message, message


def test_the_checks_refuse_a_snow_formula_that_contradicts_itself():
    message = _refuses(lambda t: _row(t, "snow")["psi_0"].__setitem__("c", 61), "whose constant is not the one its text says")
    assert "constant" in message and "1 - 60 / h_0" in message, message
    message = _refuses(lambda t: _row(t, "snow")["psi_1"].__setitem__("formula", "1 - 250 / h"), "whose formula names another variable")
    assert "1 - 250 / h_0" in message, message
    message = _refuses(lambda t: _row(t, "snow")["psi_2"].__setitem__("printed", "1 – 900/h0"), "whose printed text lacks its constant")
    assert "1000" in message and "printed" in message, message
    message = _refuses(lambda t: _row(t, "snow")["psi_0"].pop("c"), "with a formula cell that has no constant")
    assert "'c'" in message, message
    message = _refuses(lambda t: _row(t, "snow")["psi_1"].__setitem__("c", -250), "with a negative constant")
    assert "positive" in message, message


def test_the_checks_refuse_constants_that_do_not_grow():
    def swap(table):
        row = _row(table, "snow")
        row["psi_0"], row["psi_2"] = row["psi_2"], row["psi_0"]

    message = _refuses(swap, "whose snow constants fall from ψ0 to ψ2")
    assert "do not grow" in message, message


def test_the_checks_refuse_a_table_that_does_not_name_its_three_symbols():
    message = _refuses(lambda t: t["symbols"].pop("psi_1"), "naming two symbols")
    assert "psi_0, psi_1, psi_2" in message, message
    message = _refuses(lambda t: t.__setitem__("symbols", dict(reversed(list(t["symbols"].items())))), "naming them out of order")
    assert "in that order" in message, message
    message = _refuses(lambda t: t["symbols"]["psi_2"].__setitem__("label", " "), "with a symbol that has no label")
    assert "label" in message, message
    message = _refuses(lambda t: t["symbols"]["psi_0"].__setitem__("defined_in", []), "with a symbol that names no clause")
    assert "defined_in" in message, message


def test_the_checks_refuse_another_edition_or_no_table():
    data = copy.deepcopy(sia260._read(NAME, sia260._check_table_2))
    sia260._cache.pop("probe", None)
    data["edition"] = "SIA 260:2003"
    # the edition is checked where the file is read, not in the table's own check: write the doctored file aside and read it
    with tempfile.TemporaryDirectory() as tmp:
        original = sia260.HERE
        try:
            (Path(tmp) / "probe.json").write_text(json.dumps(data), encoding="utf-8")
            sia260.HERE = Path(tmp)
            try:
                sia260._read("probe", sia260._check_table_2)
            except validation.ValidationError as exc:
                assert "SIA 260:2003" in str(exc) and "SIA 260:2013" in str(exc), str(exc)
            else:
                raise AssertionError("another edition was accepted")
        finally:
            sia260.HERE = original
            sia260._cache.pop("probe", None)
    try:
        sia260._check_table_2(NAME, {"edition": "SIA 260:2013"})
    except validation.ValidationError as exc:
        assert "no 'table_2'" in str(exc)
    else:
        raise AssertionError("a file with no table was accepted")


# --- the pages themselves ------------------------------------------------------------

# How each edition's text layer names a row: the lines of Tabelle 2 open with these (p. 33), and end on the three factors.
WORDS = {
    "DE": ("SIA260-2013-DE.pdf", "Tabelle 3", {"wind": "Windkräfte", "temperature": "Temperatureinwirkungen",
                                               "earth-pressure": "Erddruck", "water-pressure": "Wasserdruck",
                                               "snow": "Schneelasten"}, "Kategorie"),
    "FR": ("SIA260-2013-FR.pdf", "Tableau 3", {"wind": "Forces dues au vent", "temperature": "Effets de la température",
                                               "earth-pressure": "Poussée des terres", "water-pressure": "Pression hydraulique",
                                               "snow": "Charges de neige"}, "Catégorie"),
    "EN": ("SIA260-2013-EN.pdf", "Table 3", {"wind": "Wind forces", "temperature": "Temperature actions",
                                             "earth-pressure": "earth pressure", "water-pressure": "water pressure",
                                             "snow": "Snow loads"}, "Category"),
}


def _page_33(filename, stop):
    """The lines of Tabelle 2 out of one edition's p. 33, whitespace collapsed -- the part before Tabelle 3 starts."""
    from pypdf import PdfReader
    reader = PdfReader(str(LIBRARY / filename))
    if reader.is_encrypted:
        reader.decrypt("")
    text = unicodedata.normalize("NFKC", reader.pages[32].extract_text())
    assert "33" in text.splitlines()[0], "p. 33 is not at index 32 of %s" % filename
    head = text[:text.index(stop)]
    return [re.sub(r"\s+", " ", line).strip() for line in head.splitlines()]


def _factors(line):
    tokens = re.findall(r"\d(?:,\d)?", line)[-3:]
    return tuple(float(t.replace(",", ".")) for t in tokens)


def test_the_values_are_p_33_of_the_german_french_and_english_editions():
    """The three editions' text layers print the same thirty-six numbers as the file and the same three snow formulas -- the stronger of the two checks on a hand transcription, and the one that needs the reference library (docs/architecture/reference-library.md §11bis)."""
    if not (LIBRARY / "SIA260-2013-DE.pdf").is_file():
        raise Skip("no reference library here -- name the folder of the norms' PDFs in %s" % conftest.NORMS_ENV)
    for lang, (filename, stop, words, category) in WORDS.items():
        if not (LIBRARY / filename).is_file():
            raise Skip("%s is not in the reference library" % filename)
        lines = _page_33(filename, stop)
        for row_id, psi0, psi1, psi2 in PAGE_33:
            if len(row_id) == 1:
                prefix = "– %s %s " % (category, row_id)
            else:
                prefix = None
            candidates = [l for l in lines if (l.startswith(prefix) if prefix else
                                               (l.startswith(words[row_id]) or l.startswith("– " + words[row_id])))]
            assert len(candidates) == 1, (lang, row_id, candidates)
            assert _factors(candidates[0]) == (psi0, psi1, psi2), (lang, row_id, candidates[0])
        snow = [l for l in lines if l.startswith(words["snow"])]
        assert len(snow) == 1, (lang, snow)
        assert re.findall(r"1 – (\d+)/ ?h0", snow[0]) == ["60", "250", "1000"], (lang, snow[0])


def test_the_glossary_uses_the_norms_own_words_for_the_three_symbols():
    """SIA 260 1.2.4 (p. 18): «Reduktionsbeiwert für den seltenen / häufigen / quasi-ständigen Wert einer veränderlichen Einwirkung», in the French and English editions as well -- the glossary's fr and en quote them."""
    symbols = sia260.symbols()
    expected_fr = ("valeur rare", "valeur fréquente", "valeur quasi permanente")
    expected_en = ("occasional value", "frequent value", "quasi-permanent value")
    for key, fr, en in zip(PSI, expected_fr, expected_en):
        de = symbols[key]["label"]
        assert glossary.term(de, "fr").startswith("Coefficient de réduction pour la ") and fr in glossary.term(de, "fr"), key
        assert glossary.term(de, "fr").endswith("d’une action variable"), key
        assert glossary.term(de, "en") == "Reduction factor for the %s of a variable action" % en, key
    assert glossary.term("Reduktionsbeiwerte", "fr") == "Coefficients de réduction"
    assert glossary.term("Reduktionsbeiwerte", "en") == "Reduction factors"

    if not (LIBRARY / "SIA260-2013-FR.pdf").is_file():
        return
    from pypdf import PdfReader
    for lang, filename in (("fr", "SIA260-2013-FR.pdf"), ("en", "SIA260-2013-EN.pdf")):
        reader = PdfReader(str(LIBRARY / filename))
        if reader.is_encrypted:
            reader.decrypt("")
        page = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", reader.pages[17].extract_text())).lower()
        for key in PSI:
            label = glossary.term(symbols[key]["label"], lang).lower()
            assert label in page, "%s: the norm's p. 18 does not say %r" % (lang, label)


# --- the live-load domain does not carry them -----------------------------------------

def _instances():
    return live_load.build_instances()


def test_no_category_carries_a_psi_and_the_loads_are_the_norms():
    """ψ is never shown for live loads: an instance holds the category, what it is, its two loads -- and nothing of SIA 260 Tabelle 2. The values of SIA 261 Tabelle 8 are the ones they were."""
    instances = _instances()
    categories = [r["id"] for r in sia261.table_8()["categories"]]
    assert list(instances) == categories
    for category, instance in instances.items():
        names = list(instance["vars"])
        assert not [n for n in names if n.startswith("psi")], (category, names)
        assert all(v.get("group") != "psi" and v["source"] == "norm:SIA 261:2020, Tabelle 8" and v["norm"] == "SIA 261" for v in instance["vars"].values()), category
        assert not any("Reduktionsbeiwert" in str(v.get("label")) for v in instance["vars"].values()), category
        assert instance["results"] == (["hinweis"] if category == "E" else ["q_k", "Q_k"]), category
        assert names[-1] == ("hinweis" if category == "E" else "Q_k"), (category, names)
    a1 = instances["A1"]["vars"]
    assert (a1["q_k"]["value"], a1["Q_k"]["value"], a1["kategorie"]["value"]) == (2, 2, "A1")
    import line_levels   # a line carries no level since v0.120: lib/line-levels.json says it (UI-002)
    assert line_levels.level("live-load", "q_k") == 1 and line_levels.level("live-load", "nutzflaeche") == 2 and "level" not in a1["q_k"]
    e = instances["E"]["vars"]
    assert "q_k" not in e and "Q_k" not in e and "hinweis" in e


def test_the_domain_module_does_not_read_sia_260_and_the_norm_file_is_still_read_by_its_own_module():
    """The Reduktionsbeiwerte stay transcribed (the load combinations read them), but not through the live loads."""
    source = (ROOT / "calc" / "domains" / "live_load.py").read_text(encoding="utf-8")
    assert "psi_" not in source, "live_load.py names a psi variable"
    assert not re.search(r"^\s*(from|import) .*sia260", source, re.M), "live_load.py imports norms/sia260"
    assert "sia260-2013-tab02-reduktionsbeiwerte" in sia260.FILES


def test_snow_is_not_a_live_load_and_is_not_on_any_category():
    for category, instance in _instances().items():
        assert not [n for n in instance["vars"] if "snow" in n.lower() or "schnee" in n.lower()], category
    # its formula stays in the norm file, unevaluated, for the snow-load calculation to read
    assert sia260.snow()["psi_0"]["c"] == 60


def test_the_export_still_validates_without_the_factors():
    data = {"schema_version": "1.4", "domains": {live_load.DOMAIN: {
        "label": live_load.LABEL, "action": live_load.ACTION, "engine": live_load.ENGINE,
        "sheet_prefix": "", "instances": _instances()}}}
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)


def test_the_example_projects_frozen_export_carries_no_psi():
    """tests/projet-exemple's calculations.json is the export the other tests read: its live-load domain is what the domain module builds now."""
    frozen = conftest.exported("calculations.json")["domains"]["live-load"]["instances"]
    fresh = _instances()
    assert list(frozen) == list(fresh)
    for category in fresh:
        assert frozen[category] == fresh[category], category


def test_no_live_load_command_prints_a_psi():
    """A category of Tabelle 8 as Woodcore writes it out (spec 2026-10-21-commandes-typst-refonte, REQ-017; `#show-calc("live-load", …)` until then) has no row of Reduktionsbeiwerte at level 3."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.tmpdir("sia260_none")
    for f in ("commands.typ", "config.typ"):   # where the project keeps them: 000-Typst-Config/ laid out by folders (issue #64)
        source = PROJECT.config_dir / f
        target = d / source.relative_to(PROJECT.typst_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    relative = PROJECT.generated_dir.relative_to(PROJECT.typst_root)
    shutil.copytree(PROJECT.generated_dir, d / relative, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("out", "docs"))
    probe = d / ".probe" / "probe.typ"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text('#import "/000-Typst-Config/config.typ": conf\n#import "/000-Typst-Config/commands.typ": *\n#show: conf\n#calc-defaults(level: 3, scope: "document")\n'
                     + (PROJECT.root / "Variable-loads" / "Live" / "A1.typ").read_text(encoding="utf-8").split("\n", 1)[1], encoding="utf-8")
    out = d / ".probe" / "probe.pdf"
    run = subprocess.run(["typst", "compile", "--root", str(d), str(probe), str(out)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    from pypdf import PdfReader
    text = unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(out)).pages))
    assert "ψ" not in text and "Reduktionsbeiwert" not in text and "SIA 260" not in text, text


def test_the_snow_factors_note_says_where_they_turn_negative_and_the_reading_retained():
    """Spec 2026-10-12-audit-issues-47-48-49, REQ-005: the snow cells of Tabelle 2 stay as printed, and the note says that ψ1 is negative below 250 m and ψ2 below 1000 m, and that the reading retained for the combinations is max(0, 1 − c/h0) -- the workbook's, not the norm's."""
    note = json.loads((ROOT / "calc" / "norms" / "sia260-2013-tab02-reduktionsbeiwerte.json").read_text(encoding="utf-8"))["_note"]
    for words in ("ψ1 below 250 m", "ψ2 below 1000 m", "max(0, 1 − c/h0)", "not a rule of SIA 260"):
        assert words in note, words
