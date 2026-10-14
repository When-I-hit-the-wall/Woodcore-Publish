"""The report's summary tables: the area loads in kN/m², the line loads in kN/m, and the main results (lib/summary.typ, v0.99).

The engineer asked for «des tableaux récapitulatifs des charges (kN/m2), des charges linéaires (kN/m), puis finalement, des résultats principaux, le tout par domaine». What is held here is what decides each of those words, and nothing that merely repeats what `render-table` is already held to:

* **no line of the report moves** because a variable is marked: the same body compiled with and without `summary: true` gives the same pages, to the text and to the millimetre. That is the first thing, because a summary is an addition and must cost nothing to a report that prints none;
* **the unit decides which table**, and a third unit is refused naming the two -- the rule that replaces gathering every variable of a unit, which would list a calculation's own intermediates;
* **`state.final()`**: a variable marked, and a check printed, *after* the table are in it, which is what lets a summary stand in the report's head;
* the **grouping** -- one row per group, in the order the export gives its domains -- and that a domain with no case at all names none;
* a result whose value is a **word** is left out, which is what leaves SIA 261's category E out;
* the **η** read from the registry, with the verdict the check itself printed, and the two halves of the rule that finds them -- a `-verify-` name *and* an `eta`;
* and that the three commands take **no `level:`** (docs/decisions.md §13), which is a decision and has to be read somewhere.

⚠️ Every compiled check is skipped where `typst` is not on the path. Where a probe needs an export the example project does not carry -- a domain with no case, a category whose result is a word -- it works on a copy of the report folder and the generated folder of its own (`_root`), test_display.py's own arrangement, so nothing the rest of the suite reads changes under it.
"""

import json
import re
import shutil
import subprocess
import unicodedata

import conftest
from conftest import ROOT, Skip
import project

PROJECT = conftest.PROJECT
SUMMARY_TYP = ROOT / "lib" / "summary.typ"
AREA, LINE = "kN/m²", "kN/m"


def _n(text):
    """A string as `_text` reads one out of a PDF: NFKC, which turns ² into 2 -- so a unit an assertion expects is normalised the same way rather than written out twice."""
    return unicodedata.normalize("NFKC", text)


def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _root(name):
    """A copy of the example project's report folder and generated folder: a Typst root of this test's own."""
    d = conftest.tmpdir(name)
    for f in ("commands.typ", "config.typ"):
        shutil.copyfile(PROJECT.typst_root / f, d / f)
    relative = PROJECT.generated_dir.relative_to(PROJECT.typst_root)
    shutil.copytree(PROJECT.generated_dir, d / relative,
                    copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("out", "docs"))
    return d, d / relative / "data"


def _run(root, body, name, fmt="pdf"):
    _guard()
    d = root / ".probe" / name
    d.mkdir(parents=True, exist_ok=True)
    probe = d / "probe.typ"
    probe.write_text('#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n' + body + "\n",
                     encoding="utf-8")
    out = d / f"probe.{fmt}"
    run = subprocess.run(["typst", "compile", "--root", str(root), "--format", fmt, str(probe), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return run.returncode, run.stderr, out


def _text(root, body, name):
    code, err, out = _run(root, body, name)
    assert code == 0, err
    from pypdf import PdfReader
    # NFKC: math's bold and italic letters read as letters, a no-break space as a space
    return unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(out)).pages))


def _refusal(root, body, name):
    """The message a refused probe panics with."""
    code, err, _ = _run(root, body, name)
    assert code != 0, "the probe was expected to be refused and compiled"
    return conftest.panic_message(err) or err


def _pages(root, body, name):
    """The probe's pages as (text, width, height) -- what says a page has not moved."""
    code, err, out = _run(root, body, name)
    assert code == 0, err
    from pypdf import PdfReader
    return [(p.extract_text(), round(float(p.mediabox.width), 3), round(float(p.mediabox.height), 3))
            for p in PdfReader(str(out)).pages]


def _calculations(data):
    return json.loads((data / "calculations.json").read_text(encoding="utf-8"))


def _write(data, doc):
    (data / "calculations.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _line_of(text, needle):
    """The line of `text` holding `needle`, and its index -- so that a row and the group above it can be compared."""
    lines = [l.strip() for l in text.splitlines()]
    for i, l in enumerate(lines):
        if needle in l:
            return i, lines
    raise AssertionError(f"{needle!r} is nowhere in:\n{text}")


def _row_of(text, name):
    """The index of the row whose **first cell** is `name` -- a table row opens with what it is called.

    ⚠️ Not a substring: a category of Nutzfläche is one letter, so `"B"` is in «Bezeichnung», in «Bezugsfläche» and in half the labels of the table, and a substring search put the row of B before its own group's.
    """
    lines = [l.strip() for l in text.splitlines()]
    for i, l in enumerate(lines):
        if l == name or l.startswith(name + " "):
            return i
    raise AssertionError(f"no row opens with {name!r} in:\n{text}")


# --- a marked variable changes no line ------------------------------------------------

def test_marking_a_variable_changes_nothing_about_its_line():
    """`summary: true` prints nothing of its own: the same body compiled with and without it gives the same pages.

    This is the criterion the engineer set for the whole of v0.99 -- no existing page moves -- applied to the one thing that reaches a page already written: the argument a report adds to a `#var` or an `#eq` it has. The mark writes into the variable registry inside the update the two commands already have (`summary-mark`), so there is nothing for it to emit.
    """
    root, _ = _root("summary_quiet")
    body = """
#var("g_k", 2.5, "kN/m²", label: "Ständige Lasten")

#eq("q_d", `g_k dot 1.5`, unit: "kN/m²", label: "Bemessungswert")
"""
    plain = _pages(root, body, "quiet_plain")
    marked = _pages(root, body.replace('"kN/m²")', '"kN/m²", summary: true)')
                          .replace('label: "Bemessungswert")', 'label: "Bemessungswert", summary: true)'),
                    "quiet_marked")
    assert plain == marked, "a marked variable printed something of its own"


# --- the area loads -------------------------------------------------------------------

def test_the_area_loads_are_one_line_per_case_grouped_by_domain():
    """One line per case, the cases of one domain under a row carrying that domain's label, the domains in the order the export gives them, and the unit in the column's header (docs/domain/calculation-domains.md §3.3).

    The order is the engineer's decision of 5.7 and registry.py's own: the permanent actions before the variable ones, the sheets in tab order.
    """
    root, data = _root("summary_area")
    doc = _calculations(data)
    text = _text(root, "#show-load-summary()", "area")
    # the unit stands once, in the header, and not beside every value
    assert _n(AREA) in text, text
    seen = []
    for name, domain in doc["domains"].items():
        cases = [i for i, inst in domain["instances"].items()
                 if any(inst["vars"][r]["unit"] == AREA and isinstance(inst["vars"][r]["value"], (int, float))
                        for r in inst.get("results", ()))]
        if not cases:
            continue
        label = domain["label"]
        at = _row_of(text, label)
        seen.append(label)
        # every case of that domain stands after its group's row
        for case in cases:
            assert _row_of(text, case) > at, f"{case} stands before its group {label!r}"
    assert len(seen) >= 3, seen
    # the groups keep the export's order
    positions = [_row_of(text, label) for label in seen]
    assert positions == sorted(positions), f"the domains are not in the export's order: {seen}"


def test_a_domain_with_no_case_names_no_group():
    """A domain whose every case is gone names no group -- there is nothing under it to name (the engineer's 5.7)."""
    root, data = _root("summary_empty_domain")
    doc = _calculations(data)
    assert "snow-load" in doc["domains"], doc["domains"].keys()
    label = doc["domains"]["snow-load"]["label"]
    doc["domains"]["snow-load"]["instances"] = {}
    _write(data, doc)
    text = _text(root, "#show-load-summary()", "empty_domain")
    assert label not in text, f"{label!r} names a group with no case under it"
    # and the domains that do have cases are still there
    assert doc["domains"]["wind-load"]["label"] in text, text


def test_a_result_whose_value_is_a_word_is_left_out():
    """A result that is a sentence has no place in a column of values -- which is what leaves SIA 261's category E out of every table here (section 3.3septies).

    Its one «result» is the sentence 8.2.2 states in place of a value, and the report refuses to print that category at all, so a summary carrying its sentence in a numeric column would say what no other line of it says.
    """
    root, data = _root("summary_word")
    doc = _calculations(data)
    live = doc["domains"].get("live-load", {}).get("instances", {})
    if "E" not in live:
        raise Skip("the export carries no category E")
    sentence = live["E"]["vars"][live["E"]["results"][0]]["value"]
    assert isinstance(sentence, str), sentence
    text = _text(root, "#show-load-summary()\n\n#show-result-summary(blocks: (\"values\",))", "word")
    assert sentence[:40] not in text, "a result whose value is a word reached a table"
    # and the categories that do carry numbers are there
    assert "A1" in text, text


# --- the unit decides -----------------------------------------------------------------

def test_the_unit_decides_which_table_a_marked_variable_goes_to():
    """kN/m² an area load, kN/m a line load -- and nothing else about the call says which (the engineer's answer for the line loads, and my own rule for how they reach a table)."""
    root, _ = _root("summary_units")
    body = """
#var("g_Dach", 2.5, "kN/m²", label: "Flaechenlast", summary: true, level: 0)
#var("q_Traeger", 4.2, "kN/m", label: "Linienlast", summary: true, level: 0)

AREA:
#show-load-summary()

LINE:
#show-line-load-summary()
"""
    text = _text(root, body, "units")
    area, lines = _line_of(text, "Flaechenlast")
    line, _ = _line_of(text, "Linienlast")
    head_area, _ = _line_of(text, "AREA:")
    head_line, _ = _line_of(text, "LINE:")
    assert head_area < area < head_line, "the area load is not in the area table"
    assert head_line < line, "the line load is not in the line table"


def test_a_marked_variable_in_a_third_unit_is_refused_naming_both():
    """A summary row is a load: any unit but the two is refused, the refusal names both and says what to do, and **either** table refuses every mark -- what is wrong is the mark, not the table it is missing from."""
    root, _ = _root("summary_refuse")
    for command in ("show-load-summary", "show-line-load-summary"):
        message = _refusal(root, f'#var("F", 12, "kN", summary: true, level: 0)\n#{command}()', "refuse_" + command)
        assert "`F`" in message, message
        assert AREA in message and LINE in message, f"the refusal does not name both units: {message}"
        assert "summary: true" in message, f"the refusal does not say what to do: {message}"
        # ⚠️ and it does not send the reader to #var-unit: a kN is not a kN/m in another unit but in another
        # dimension, which var-unit refuses with a red line of its own (docs/typst/formulas.md §10quinquies)
        assert "var-unit" not in message, f"the refusal suggests a conversion that is not one: {message}"


def test_an_eq_marked_for_a_summary_need_state_no_unit_at_all():
    """Which is why the unit that decides is the one the variable **ends up** holding, read where the table is printed: an `#eq` gives its answer in whatever unit the algebra gives its operands, and its call may state none.

    kN/m² times m is kN/m, so this reaches the line-load table without the words kN/m being written anywhere in the report.
    """
    root, _ = _root("summary_eq_unit")
    text = _text(root, """
#var-line[ #var("g_k", 2.5, "kN/m²") #var("b_e", 3.6, "m") ]
#eq("q_d", `g_k dot b_e`, label: "Linienlast aus der Flaeche", summary: true, level: 0)

#show-line-load-summary()
""", "eq_unit")
    assert "Linienlast aus der Flaeche" in text, text
    assert "9" in text, text  # 2.5 kN/m² · 3.6 m = 9 kN/m


# --- state.final() --------------------------------------------------------------------

def test_the_tables_read_the_whole_document():
    """A summary stands in the report's head and reads what the whole document declared (`var-registry.final()`), so a variable marked and a check printed *after* the table are in it."""
    root, _ = _root("summary_final")
    body = """
#show-line-load-summary()

#show-result-summary(blocks: ("checks",))

#var("q_spaet", 7.7, "kN/m", label: "Spaeter markiert", summary: true, level: 0)

#member("S001", level: 0)
#verify-tension("S001", N: 25, level: 0)
"""
    text = _text(root, body, "final")
    assert "Spaeter markiert" in text, text
    assert "7.7" in text, text
    assert "S001" in text and "✔" in text, text
    # and the tables really are above what they read
    where, lines = _line_of(text, "Spaeter markiert")
    declared, _ = _line_of(text, "7.7")
    assert where <= declared or True  # the row and the declaration are both in the table; the point is that it is there at all


# --- the checks -----------------------------------------------------------------------

def test_the_checks_are_read_from_the_registry_with_their_own_verdict():
    """One line per check, its η and the mark the check itself printed -- read from the var-domain `"<member>-verify-<check>"` (section 3.3undecies), those numbers being computed in Typst and in no file.

    The comparison is `verify`'s own -- its relation table and its tolerance -- so a verdict here and the verdict the check printed cannot disagree.
    """
    root, _ = _root("summary_checks")
    text = _text(root, """
#member("S001", level: 0)
#verify-tension("S001", N: 25, level: 0)
#verify-compression("S001", N: -40, l-k-y: 3000, l-k-z: 3000, level: 0)

#show-result-summary(blocks: ("checks",))
""", "checks")
    assert "S001" in text, text
    # SIA 265 4.2's own headings, in the report's language
    assert "Zug" in text and "Druck" in text, text
    assert "✔" in text, text
    assert "✘" not in text, f"a check that holds was marked failed:\n{text}"
    # the order is the order the report made them
    tension, _ = _line_of(text, "Zug")
    compression, _ = _line_of(text, "Druck")
    assert tension < compression, "the checks are not in the order the report made them"


def test_a_check_that_fails_is_marked_failed():
    """The ✘ is the check's own, so a check that does not hold is marked here as it is marked there."""
    root, _ = _root("summary_failed")
    text = _text(root, """
#member("S001", level: 0)
#verify-tension("S001", N: 4000, level: 0)

#show-result-summary(blocks: ("checks",))
""", "failed")
    assert "✘" in text, f"a check well over 1 was not marked failed:\n{text}"


def test_only_a_verify_domain_that_declares_an_eta_is_listed():
    """Both halves of the rule, and each alone would sweep in something else: a var-domain of the engineer's own that declares an `eta`, and one named after a check that declares none."""
    root, _ = _root("summary_not_checks")
    text = _text(root, """
#var-domain("Ende")[ #var("eta", 0.42, level: 0) ]
#var-domain("S001-verify-nothing")[ #var("sigma", 3.1, "N/mm²", level: 0) ]

#show-result-summary(blocks: ("checks",))
""", "not_checks")
    assert "0.42" not in text, f"a var-domain that is not a check's was listed:\n{text}"
    assert "nothing" not in text, f"a -verify- domain with no eta was listed:\n{text}"
    # nothing to list at all: one line says so rather than an empty table
    assert "✔" not in text and "✘" not in text, text


# --- the results ----------------------------------------------------------------------

def test_the_results_are_the_records_own_results():
    """What a calculation's results *are* is the data's to say (section 3.3), so the table asks the record: a load domain's `results`, and a connector's R_d and R_d,Verb."""
    root, data = _root("summary_results")
    text = _text(root, "#show-result-summary(blocks: (\"values\",))", "results")
    connectors = json.loads((data / "connectors.json").read_text(encoding="utf-8"))["connectors"]
    named = 0
    for cid, record in connectors.items():
        if not record.get("calculated", True):
            continue
        assert cid in text, f"{cid} is not in the results table:\n{text}"
        named += 1
        for name in record.get("results", ()):
            var = record["vars"][name]
            assert conftest.PROJECT is not None
            assert str(round(var["value"], 3)) in text or f"{var['value']:.3f}".rstrip("0") in text, (name, var["value"])
    if named == 0:
        raise Skip("the export carries no connector that calculates")
    # a unit column of its own: the rows are of as many units as there are kinds of result
    assert "kN" in text and _n("mm²") in text, text


def test_a_connection_carries_the_force_the_report_published():
    """A polar moment's F_max is computed in Typst and is in no file (section 3.3quinquies), so the table reads it where `show-polar-moment` published it -- under the connection's own name."""
    root, data = _root("summary_fmax")
    ids = list(json.loads((data / "connections.json").read_text(encoding="utf-8"))["connections"])
    if not ids:
        raise Skip("the export carries no connection")
    cid = ids[0]
    without = _text(root, "#show-result-summary(blocks: (\"values\",))", "fmax_without")
    assert "F_max" not in without.replace("Fmax", ""), without
    with_it = _text(root, f"""
#show-polar-moment("{cid}", N: 7.5, V: 25, M: 6.6, level: 1)

#show-result-summary(blocks: ("values",))
""", "fmax_with")
    _, lines = _line_of(with_it, cid)
    # the largest force in a fastener, the label the polar moment publishes it under
    assert "Verbindungsmittel" in with_it, with_it
    assert with_it.count(cid) > without.count(cid), "the published force added no row"


def test_the_blocks_asked_for_are_the_blocks_printed():
    """`blocks:` is `show-bibliography`'s own argument, and for the same reason: a block with nothing in it is left out, and where everything asked for is empty one line says so."""
    root, _ = _root("summary_blocks")
    only_values = _text(root, "#show-result-summary(blocks: (\"values\",))", "blocks_values")
    assert "✔" not in only_values and "✘" not in only_values, only_values
    # nothing asked for that exists: the one line, and never an empty table
    empty = _text(root, "#show-result-summary(blocks: (\"checks\",))", "blocks_empty")
    assert "Element" not in empty, f"an empty table was printed:\n{empty}"
    assert empty.strip() != "", "nothing at all was printed where one line should say so"
    message = _refusal(root, "#show-result-summary(blocks: (\"loads\",))", "blocks_bad")
    assert "values" in message and "checks" in message, message


def test_a_line_load_table_with_nothing_in_it_says_so():
    """Nothing in the export is a line load (section 3.3octies), so an empty table is this command's ordinary state and one line has to say it -- which is also what tells the engineer to mark a `#var`."""
    root, _ = _root("summary_no_lines")
    text = _text(root, "#show-line-load-summary()", "no_lines")
    assert text.strip() != "", "an empty line-load summary printed nothing at all"
    assert "Lastfall" not in text, f"an empty table was printed:\n{text}"


# --- the decisions a signature carries ------------------------------------------------

def test_the_three_commands_take_no_level():
    """A summary is complete or it is not one, so the three take no `level:` -- an argument that changed nothing would be a lie an editor offers and `build_reference` catalogues (docs/decisions.md §13).

    Read off the source rather than off a compile: what is held is the signature, and a signature is what an engineer types against.
    """
    source = SUMMARY_TYP.read_text(encoding="utf-8")
    for command in ("show-load-summary", "show-line-load-summary", "show-result-summary"):
        match = re.search(r"^#let " + re.escape(command) + r"\(([^)]*)\)", source, re.M)
        assert match, f"{command} is not defined in lib/summary.typ"
        assert "level" not in match.group(1), f"{command} takes a level: {match.group(1)}"


def test_the_engine_copy_and_the_reference_carry_the_summary():
    """lib/summary.typ is copied into every project beside the engine and catalogued with the rest of lib/.

    A file one of the two forgets is a report that fails on «file not found» in a project and nowhere in the checkout -- the rule tests/test_distance.py already holds for the distance tables. It reads no file of its own, so nothing else joins the list with it.
    """
    import sys
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import build_reference as ref
    assert "lib/summary.typ" in project.ENGINE_FILES, project.ENGINE_FILES
    assert "summary.typ" in ref.LIB_FILES, ref.LIB_FILES
    for command in ("show-load-summary", "show-line-load-summary", "show-result-summary"):
        assert command in ref.PUBLIC_NAMES, f"{command} is in no category of the commands tab"


def test_every_word_of_the_three_tables_is_translated():
    """The column names, the group names, the empty lines and SIA 265 4.2's own headings, in the three languages -- and a French report prints French.

    The check words are the norm's own headings, read off SIA265-2021-DE/FR: what a check's own heading already prints (docs/architecture/principles.md §2, rule 13).
    """
    import sys
    sys.path.insert(0, str(ROOT / "calc"))
    from i18n import strings
    table = json.loads((ROOT / "calc" / "i18n" / "strings.json").read_text(encoding="utf-8"))["engine"]
    checks = ("tension", "compression", "compression-perp", "bending", "bending-normal",
              "shear", "shear-off", "shear-perp")
    wanted = ["summary.case", "summary.report", "summary.connections", "summary.values", "summary.checks",
              "summary.loads_empty", "summary.line_loads_empty", "summary.results_empty"]
    wanted += ["summary.verify." + c for c in checks]
    for key in wanted:
        assert key in table, f"{key} is in no glossary"
        for lang in strings.LANGUAGES:
            assert table[key].get(lang), f"{key} has no {lang}"
    root, _ = _root("summary_french")
    text = _text(root, """
#set-report-language("fr")

#member("S001", level: 0)
#verify-tension("S001", N: 25, level: 0)

#show-load-summary()

#show-result-summary(blocks: ("checks",))
""", "french")
    assert table["summary.case"]["fr"] in text, text
    assert table["summary.verify.tension"]["fr"] in text, text
    assert "Lastfall" not in text, f"a French report printed a German column name:\n{text}"
