"""The report's own variables, read back out of a compiled report (calc/variables.py, calc/tools/variables_tab.py, docs/project/purpose.md §1, docs/ui/window.md §10quater, docs/typst/formulas.md §10quinquies).

What is held here, and why each of them is worth a test rather than care:

⚠️ **The state's key and its default are the engine's own**, character for character. A mismatched default is
not a wrong answer here, it is the value the *document's* own `update` functions are handed, so the report
stops compiling and the error surfaces inside `lib/formula.typ` -- a defect that reads as one of the engine's.
Planted (a default of another shape), the first test fails; planted and *shipped*, nothing here would have
said so. It is the rule `tests/test_distance.py` already holds for the files `lib/distance.typ` names.

⚠️ **The level does not change what is stored**, which is what lets one reading serve all three reports and
the cache key carry no level. It costs two compiles to hold, and it is held because the whole caching design
rests on it.

⚠️ **The PDF does not make a reading stale**, and a section or the export does. The PDF is written *by* the
compile a reading pays for, so a stamp that counted it would be stale the moment it was taken -- and again
after every *Exporter PDF*, which is the one moment an engineer would most expect the tab to be right.

And the tab: that it lists its domains in a pane of their own and the chosen one's variables flat beside it, with where each comes from, that its filters work on the name, the unit and the provenance, over one domain or every one, that it offers no
`#var` call for the report's own domain -- `#var("R_d")` alone can never work -- that it reads **once** rather
than on every showing, that it keeps what it had when a reading fails, that it edits nothing, and that it
speaks the window's three languages.
"""

import json
import os
import re
import shutil
import sys
import time

import conftest
from conftest import ROOT, Skip

import project
import variables as model

sys.path.insert(0, str(ROOT / "calc" / "tools")) if str(ROOT / "calc" / "tools") not in sys.path else None

import build_reference as ref  # noqa: E402

_WINDOW = {}


# ---------------------------------------------------------------- the engine's own declaration

def _engine_state(name):
    """`state("<name>", <default>)` as `lib/calc-engine.typ` declares it, the default read by balancing its parentheses -- a regular expression cannot, the default being `(stack: ("",), domains: (:))`."""
    source = conftest.engine_source()
    opening = source.index(f'state("{name}", ') + len(f'state("{name}", ')
    depth, end = 0, None
    for index in range(opening, len(source)):
        char = source[index]
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                end = index
                break
            depth -= 1
    assert end is not None, f"calc-engine.typ: state({name!r}) is not closed"
    return source[opening:end].strip()


def test_the_state_and_its_default_are_the_engine_own():
    """The one test this whole module rests on: a default that is not the engine's stops the *report* compiling."""
    declared = _engine_state(model.REGISTRY_STATE)
    assert model.REGISTRY_DEFAULT == declared, (
        f"variables.REGISTRY_DEFAULT is {model.REGISTRY_DEFAULT!r} and lib/calc-engine.typ declares "
        f"{declared!r} -- a mismatch does not give a wrong default, it breaks the report's own compile")


def test_the_expression_names_the_state_and_reads_the_whole_document():
    expression = model.expression()
    assert model.REGISTRY_STATE in expression
    assert model.REGISTRY_DEFAULT in expression
    # .final() and never .get(): what a tab lists is the whole document's, as show-load-summary reads it
    assert expression.endswith(".final()"), expression


def test_fmt_value_is_the_rule_the_engine_prints_with():
    """The same rule as `lib/calc-engine.typ`'s `fmt-decimals`, restated in Python because the tab that needs it is imported by woodcore_gui and cannot import it back (§10sexies). Four copies of it exist; this is what keeps them one rule.

    ⚠️ The **rule** is shared and the **number of decimals** is each surface's own: a detail schema prints 2
    (`schema.DIGITS`, millimetres), the report and the figures 3. So they are compared at one digit count,
    which is what «the same rule» means; comparing their defaults would be asserting that a schema prints as
    many decimals as a report, which it deliberately does not.
    """
    import woodcore_gui
    from domains import schema, statics
    for value in (1.7291232, 0.8, 438, 0.0, -0.2666, 157000, 2.0, 1e-9, -0.0004, -0.0):
        for digits in (0, 2, 3, 6):
            ours = model.fmt_value(value, digits)
            for name, other in (("statics", statics.fmt_number), ("schema", schema.fmt_number),
                                ("woodcore_gui", woodcore_gui.fmt_value)):
                assert ours == other(value, digits), (name, value, digits, ours, other(value, digits))
    # and the default here is the report's own, which is what a page prints
    assert model.fmt_value(1.7291232) == "1.729"
    assert model.fmt_value(438) == "438"
    assert model.fmt_value(0.800) == "0.8"
    assert model.fmt_value("Flachdach") == "Flachdach"   # a word passes through
    assert model.fmt_value(None) == ""


# ---------------------------------------------------------------- reading a real report

def _read_once():
    """One reading of the session project, made once for the whole file: it is a full compile."""
    if "registry" not in _WINDOW:
        if not conftest.have_typst():
            raise Skip("typst is not on the PATH")
        _WINDOW["registry"] = model.read(conftest.PROJECT)
    return _WINDOW["registry"]


def test_a_reading_gives_every_variable_by_domain():
    found = _read_once()
    assert found.count > 0, "the example report computes variables; none was read"
    assert found.domains, "a reading with no domain at all"
    # the report's own default domain is there and is keyed by the empty string
    assert model.REPORT_DOMAIN in found.domains
    for var in found.variables():
        assert var.key, var
        assert var.symbol, var          # a symbol is never empty: the key stands in where none was given
        assert isinstance(var.unit, str)
        assert var.domain in found.domains


def test_a_variable_carries_the_name_to_write_and_the_symbol_to_print():
    """The two are not the same word, which is the whole reason the tab has both columns (§10bis)."""
    found = _read_once()
    both = [v for v in found.variables() if v.symbol != v.key]
    assert both, "no variable whose printed symbol differs from its key -- the example report should have several"


def test_the_level_does_not_change_what_is_stored():
    """Two compiles, deliberately: it is the fact the cache key's having no level rests on."""
    if not conftest.have_typst():
        raise Skip("typst is not on the PATH")
    here = conftest.PROJECT
    import subprocess
    answers = []
    for level in (1, 3):
        done = subprocess.run(
            [project.typst_executable(), "eval", "--in", str(here.report_typ), "--root", str(here.typst_root),
             "--format", "json", "--input", f"level={level}", model.expression()],
            capture_output=True, cwd=str(here.typst_root), timeout=model.TIMEOUT_S)
        assert done.returncode == 0, done.stderr.decode("utf-8", "replace")[-800:]
        answers.append(done.stdout)
    assert answers[0] == answers[1], "a level changed what the registry stores -- the cache key then needs one"


def test_a_report_that_does_not_compile_is_a_coded_refusal():
    if not conftest.have_typst():
        raise Skip("typst is not on the PATH")
    here = conftest.PROJECT
    entry = here.report_typ
    keep = entry.read_text(encoding="utf-8")
    entry.write_text(keep + '\n#panic("deliberate, from tests/test_variables.py")\n', encoding="utf-8")
    try:
        try:
            model.read(here)
        except model.VariablesError as exc:
            assert exc.code == "compile_failed", exc.code
            assert "deliberate" in exc.detail.get("output", ""), exc.detail
        else:
            raise AssertionError("a report that panics was read without a word")
    finally:
        entry.write_text(keep, encoding="utf-8")


def test_the_attachment_name_is_the_engine_own():
    """`lib/calc-engine.typ` attaches under this name and this module reads it back by it; a drift would not fail, it would leave the window quietly compiling on every opening for want of finding it."""
    source = conftest.engine_source()
    declared = re.search(r'#let variables-attachment = "([^"]+)"', source)
    assert declared, "lib/calc-engine.typ no longer declares variables-attachment"
    assert model.ATTACHMENT == declared.group(1), (model.ATTACHMENT, declared.group(1))
    # and it is attached from woodcore-document, the rule every report already applies
    rule = source[source.index("#let woodcore-document("):]
    rule = rule[:rule.index("\n#let ")]
    assert "pdf.attach" in rule and "variables-attachment" in rule, "the attachment left woodcore-document"


def test_the_pdf_carries_the_same_registry_a_compile_gives():
    """The whole of the free route rests on this: `best()` chooses a **price** and never an answer.

    ⚠️ It is the one test here that compiles the report *and* reads its PDF, so it is the slow one — and it is
    the one that would catch the attachment drifting from what `var-registry.final()` holds, which no cheaper
    check could.
    """
    if not conftest.have_typst():
        raise Skip("typst is not on the PATH")
    here = conftest.PROJECT
    import subprocess
    # ⚠️ This writes into the session's shared copy of the example project, so it puts back **what it found
    # and nothing else** -- the discipline a peer session paid a full suite run to learn, its own cleanup
    # having globbed a folder and deleted the fixture's own file rather than only its own.
    kept = here.report_pdf.read_bytes() if here.report_pdf.is_file() else None
    try:
        done = subprocess.run(
            [project.typst_executable(), "compile", "--root", str(here.typst_root),
             str(here.report_typ), str(here.report_pdf)],
            capture_output=True, cwd=str(here.typst_root), timeout=model.TIMEOUT_S)
        assert done.returncode == 0, done.stderr.decode("utf-8", "replace")[-800:]

        from_pdf = model.from_pdf(here)
        assert from_pdf is not None, "the PDF this engine just wrote carries no attachment"
        compiled = model.read(here)
        shape = lambda reg: sorted(
            (v.domain, v.key, v.value, v.unit, v.symbol, v.label, v.description, v.norm, v.norm_ref)
            for v in reg.variables())
        assert shape(from_pdf) == shape(compiled), "the attached registry differs from the compiled one"
        assert from_pdf.count == compiled.count > 0
        # and `best` takes the free one while the PDF is newer than the sources
        assert model.pdf_is_current(here)
        assert model.best(here).count == compiled.count
    finally:
        if kept is None:
            here.report_pdf.unlink(missing_ok=True)
        else:
            here.report_pdf.write_bytes(kept)


def test_the_pdf_route_declines_rather_than_answering_stale():
    """A PDF older than any source is not the report's own any more, and `from_pdf` says so by giving back None — never a value one edit behind."""
    here = _stamped_project("variables-pdf-stale")
    here.report_pdf.parent.mkdir(parents=True, exist_ok=True)
    here.report_pdf.write_bytes(b"%PDF-1.7 not a real one\n")
    time.sleep(0.01)
    sections = sorted((here.document_dir("rs") / "Sections").glob("*.typ"))
    if not sections:
        raise Skip("the copied report has no Sections/*.typ")
    sections[0].write_text(sections[0].read_text(encoding="utf-8") + "\n// after the PDF\n", encoding="utf-8")
    assert not model.pdf_is_current(here)
    assert model.from_pdf(here) is None
    # no PDF at all is the same answer, and neither is an error
    here.report_pdf.unlink()
    assert not model.pdf_is_current(here)
    assert model.from_pdf(here) is None


def test_a_pdf_that_cannot_be_read_means_compile_instead_and_never_an_error():
    """Every failure of the free route is a reason to compile, not something to tell the engineer: a PDF being written as it is read, one pypdf cannot parse, one from an engine that attached nothing."""
    here = _stamped_project("variables-pdf-broken")
    here.report_pdf.parent.mkdir(parents=True, exist_ok=True)
    for content in (b"", b"not a pdf at all", b"%PDF-1.7\nbroken xref\n"):
        here.report_pdf.write_bytes(content)
        os.utime(here.report_pdf, (time.time() + 60, time.time() + 60))   # newer than every source
        assert model.pdf_is_current(here)
        assert model.from_pdf(here) is None, f"a broken PDF was read: {content[:20]!r}"


def test_the_attachment_adds_no_page_and_survives_a_png_target():
    """Two facts the whole design rests on, measured rather than assumed: the attachment is metadata, so no report gains a page by it; and it is silently ignored for a PNG or SVG target, so the 306 frozen example pages and the website's renders are untouched."""
    if not conftest.have_typst():
        raise Skip("typst is not on the PATH")
    import subprocess
    probe = conftest.probe_dir("variables-attach")
    (probe / "p.typ").write_text(
        '#let reg = state("var-registry", (stack: ("",), domains: (:)))\n'
        '= One page\n'
        f'#context pdf.attach("{model.ATTACHMENT}", bytes(json.encode(reg.final())), description: "x")\n',
        encoding="utf-8")
    for fmt, out in (("pdf", "p.pdf"), ("png", "p.png"), ("svg", "p.svg")):
        done = subprocess.run(
            [project.typst_executable(), "compile", "--format", fmt, "--root", str(conftest.TYPST_ROOT),
             str(probe / "p.typ"), str(probe / out)],
            capture_output=True, timeout=120)
        assert done.returncode == 0, (fmt, done.stderr.decode("utf-8", "replace")[-400:])
    from pypdf import PdfReader
    assert len(PdfReader(probe / "p.pdf").pages) == 1, "the attachment added a page"


def test_a_file_another_program_holds_is_not_a_report_that_does_not_compile():
    """The whole project sits in NextCloud, whose sync client holds a file open while it uploads it, and Typst then fails on Windows' own ERROR_SHARING_VIOLATION rather than on a diagnostic of its own. Saying «the report does not compile» there would be a false statement about the engineer's work, so it is tried once more and then said as what it is."""
    import subprocess
    import unittest.mock as mock

    here = conftest.PROJECT
    busy = subprocess.CompletedProcess(
        [], 1, stdout=b"", stderr=b"error: failed to load file (os error 32)\n")
    good = subprocess.CompletedProcess([], 0, stdout=b'{"stack":[""],"domains":{}}', stderr=b"")

    # held once, free the second time: the reading succeeds and nothing is said at all
    with mock.patch.object(model.subprocess, "run", side_effect=[busy, good]) as ran, \
            mock.patch.object(model.time, "sleep"):
        found = model.read(here)
    assert found.count == 0 and ran.call_count == 2, "a transient lock was not tried a second time"

    # held both times: its own code, never compile_failed
    with mock.patch.object(model.subprocess, "run", side_effect=[busy, busy]), \
            mock.patch.object(model.time, "sleep"):
        try:
            model.read(here)
        except model.VariablesError as exc:
            assert exc.code == "file_busy", exc.code
        else:
            raise AssertionError("a file held twice over was read")

    # ⚠️ and a real defect of the report is NOT retried: «file not found» is a picture the engineer has not
    # put there yet, and trying again would only say it twice
    missing = subprocess.CompletedProcess([], 1, stdout=b"", stderr=b"error: file not found (searched at Images/x.png)\n")
    with mock.patch.object(model.subprocess, "run", side_effect=[missing]) as ran:
        try:
            model.read(here)
        except model.VariablesError as exc:
            assert exc.code == "compile_failed", exc.code
            assert "file not found" in exc.detail["output"]
        else:
            raise AssertionError("a report that cannot find a file was read")
    assert ran.call_count == 1, "a real compile error was retried"


def test_a_reading_carries_no_wall_clock_value():
    """What is cached is compared against `stamp`, never against a time, and nothing here records how long a reading took: a duration in a record is a value that differs between two runs of an unchanged project, which is what `data/project.json` carries no date for (§12). The cache sits outside the project, so this is not that promise — it is the same reasoning applied before the field could grow into it."""
    found = model.Registry(domains={}, stamp="x")
    assert not hasattr(found, "read_at")
    fields = set(model.Registry.__dataclass_fields__)
    assert fields == {"domains", "stamp"}, fields
    source = (ROOT / "calc" / "variables.py").read_text(encoding="utf-8")
    saved = source[source.index("def save("):source.index("def cached(")]
    for word in ("time.time", "read_at", "seconds", "datetime"):
        assert word not in saved, f"save() writes {word!r} into the cache"


def test_a_project_with_no_report_is_refused_by_name():
    here = conftest.project_copy("variables-no-report")
    here.report_typ.unlink()     # project_copy copies each document's entry file since issue #90: the report taken away
    try:
        model.read(here)
    except model.VariablesError as exc:
        assert exc.code == "no_report", exc.code
        assert str(here.report_typ) in str(exc)
    else:
        raise AssertionError("a project with no report was read")


# ---------------------------------------------------------------- the stamp

def _stamped_project(name):
    """A copy of the session project carrying its report and its engine, for a stamp to be taken of -- its Typst root copied whole, which in three documents is the project's own folder: the three documents, what they share and the export. The report's sections are `document_dir("rs")`'s, the root holding none of its own. Not the probes other tests compiled under it, which are theirs."""
    here = conftest.project_copy(name)
    shutil.copytree(conftest.PROJECT.typst_root, here.typst_root, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".probe"))
    return here


def test_the_pdf_does_not_make_a_reading_stale():
    """The PDF is written by the very compile a reading pays for: counting it would make every reading stale at once, and again after every Exporter PDF."""
    here = _stamped_project("variables-stamp-pdf")
    before = model.stamp(here)
    here.report_pdf.parent.mkdir(parents=True, exist_ok=True)
    here.report_pdf.write_bytes(b"%PDF-1.7 pretend\n")
    assert model.stamp(here) == before, "writing the PDF moved the stamp"


def test_out_and_probe_are_not_read():
    here = _stamped_project("variables-stamp-out")
    before = model.stamp(here)
    for folder in ("out", ".probe", "archives"):
        (here.typst_root / folder).mkdir(parents=True, exist_ok=True)
        (here.typst_root / folder / "stray.typ").write_text("#let x = 1\n", encoding="utf-8")
    assert model.stamp(here) == before, "a build's own output folder moved the stamp"


def test_a_section_and_the_export_make_a_reading_stale():
    here = _stamped_project("variables-stamp-source")
    sections = sorted((here.document_dir("rs") / "Sections").glob("*.typ"))
    if not sections:
        raise Skip("the copied report has no Sections/*.typ")
    before = model.stamp(here)
    time.sleep(0.01)
    sections[0].write_text(sections[0].read_text(encoding="utf-8") + "\n// touched\n", encoding="utf-8")
    after = model.stamp(here)
    assert after != before, "a section edited did not move the stamp"
    # data/ counts too: var-of(...) reads the export, so a `#var` carrying a value out of it moves with it.
    # ⚠️ The file is made LONGER rather than rewritten with the same text: the stamp carries the newest
    # modification time, and two writes inside one tick of the clock's own resolution give the same one --
    # so a rewrite of the same bytes is a change this stamp can genuinely miss, and a test that asserted
    # otherwise would be asserting a resolution rather than the rule. The size is what makes it certain.
    data = sorted(here.data_dir.glob("*.json"))
    if data:
        data[0].write_text(data[0].read_text(encoding="utf-8") + "\n", encoding="utf-8")
        assert model.stamp(here) != after, "the export is not part of what a reading reads"


# ---------------------------------------------------------------- the cache

def test_the_cache_round_trips_and_says_whether_it_still_answers():
    here = _stamped_project("variables-cache")
    with project.using(here.file):
        found = model.Registry(
            domains={"": [model.Variable(key="R_d", domain="", value=2.655, unit="kN", symbol="R_d",
                                         label="Tragwiderstand", norm="SIA 265", norm_ref="6.2.1.1")]},
            stamp=model.stamp(here))
        model.save(found, here)
        back = model.cached(here)
        assert back is not None and back.count == 1
        var = next(back.variables())
        assert (var.key, var.value, var.unit, var.symbol) == ("R_d", 2.655, "kN", "R_d")
        assert var.citation == "SIA 265 6.2.1.1"
        assert model.is_current(back, here)
        # and it stops answering the moment the report moves under it
        sections = sorted((here.document_dir("rs") / "Sections").glob("*.typ"))
        if sections:
            time.sleep(0.01)
            sections[0].write_text(sections[0].read_text(encoding="utf-8") + "\n// moved\n", encoding="utf-8")
            assert not model.is_current(model.cached(here), here)


def test_a_cache_of_another_shape_is_ignored_rather_than_read_wrongly():
    here = _stamped_project("variables-cache-version")
    path = model.cache_file(here)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cache_version": model.CACHE_VERSION + 1, "domains": {"": {}}}), encoding="utf-8")
    assert model.cached(here) is None
    path.write_text("{ not json", encoding="utf-8")
    assert model.cached(here) is None


def test_a_citation_is_set_as_the_report_sets_one():
    """A clause, a table and an annex are set after the norm with no § (spec 2026-10-21-commandes-typst-refonte, UI-001) -- `norm-text`'s own rule (§10)."""
    def citation(norm, ref):
        return model.Variable(key="k", domain="", value=1, unit="", symbol="k", norm=norm, norm_ref=ref).citation
    assert citation("SIA 265", "4.2.1") == "SIA 265 4.2.1"
    assert citation("SIA 265", "Tabelle 8") == "SIA 265 Tabelle 8"
    assert citation("SIA 261", "Anhang D") == "SIA 261 Anhang D"
    assert citation("bauforumstahl", "") == "bauforumstahl"
    assert citation("", "4.2.1") == ""


# ---------------------------------------------------------------- domains

def test_domain_kind_reads_only_what_is_a_contract():
    assert model.domain_kind(model.REPORT_DOMAIN) == "report"
    assert model.domain_kind("S001-verify-compression") == "check"
    assert model.domain_kind("T001") == "named"
    assert model.domain_kind("VU-MP-1") == "named"
    assert model.domain_kind("S10 - 0.55 kN Ende") == "named"
    # the fragment a member check published its values under until the spec 2026-10-15 (D-14): a domain of a report written before is still read as a check's
    assert model.CHECK_MARK in "S001-verify-bending"


def test_the_units_of_a_reading_are_ordered_commonest_first():
    found = model.Registry(domains={"a": [
        model.Variable(key=f"v{n}", domain="a", value=n, unit=unit, symbol=f"v{n}")
        for n, unit in enumerate(["kN", "kN", "kN", "mm", "mm", ""])]})
    assert found.units() == ["kN", "mm", ""]


# ---------------------------------------------------------------- the calls the tab copies

def test_the_calls_are_spelled_by_build_reference_alone():
    assert ref.call_var_registry("M", "S10 - 0.55 kN Ende") == '#var("M", domain: "S10 - 0.55 kN Ende")'
    assert ref.call_var_domain("snow-load", "SL", "s_k") == '#var("s_k", domain: ("snow-load", "SL"))'
    assert ref.call_find("T001") == '#find(object: "variable", domain: "T001")'
    assert ref.call_find() == '#find(object: "variable")'
    assert ref.call_find("T001", "name") == '#find(object: "variable", domain: "T001", type: "name")'


def test_a_var_call_without_a_domain_is_refused_rather_than_written_broken():
    """`#var("R_d")` reads its value from `domain:` or from a positional beside the key, so a call with neither can never work whatever is declared around it."""
    for empty in (None, ""):
        try:
            ref.call_var_registry("R_d", empty)
        except ValueError as exc:
            assert "var-domain" in str(exc), exc
        else:
            raise AssertionError(f"call_var_registry accepted domain={empty!r}")


# ---------------------------------------------------------------- the tab

def _tab():
    """The Variables tab of a window built once, off-screen."""
    if "tab" not in _WINDOW:
        conftest.exported("calculations.json")
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        import variables_tab
        import woodcore_gui
        QApplication.instance() or QApplication([])
        window = woodcore_gui.MainWindow()
        found = [t for t in window.tabs if isinstance(t, variables_tab.VariablesTab)]
        assert found, "the window has no Variables tab -- is it in woodcore_gui.TABS?"
        _WINDOW["window"], _WINDOW["tab"] = window, found[0]
    return _WINDOW["tab"]


def _fill(tab, registry, export=None):
    """The tab listing `registry` as the report's reading and `export` as the export's -- none by default, so that the rows are the sample's."""
    import variable_sources
    tab.readings = {"rs": registry} if registry is not None else {}
    tab.errors = {}
    tab.export = export if export is not None else variable_sources.Export()
    tab.domain_key = None
    tab.all_domains_box.setChecked(False)
    tab.results_box.setChecked(False)
    tab.search.setText("")
    tab.refresh()
    tab.unit_box.setCurrentIndex(0)
    tab.provenance_box.setCurrentIndex(0)


def _real_export():
    import variable_sources
    found = variable_sources.read_export(conftest.PROJECT)
    assert not found.errors, [str(e) for e in found.errors]
    return found


def _sample():
    return model.Registry(stamp="pinned", domains={
        "": [model.Variable(key="R_d", domain="", value=2.655, unit="kN", symbol="R_d", label="Tragwiderstand")],
        "T001": [
            model.Variable(key="A", domain="T001", value=20000.0, unit="mm²", symbol="A"),
            model.Variable(key="eta_w", domain="T001", value=0.8, unit="", symbol="eta_w",
                           label="Feuchteklasse 2", norm="SIA 265", norm_ref="Tabelle 4"),
        ],
        "S001-verify-compression": [
            model.Variable(key="eta", domain="S001-verify-compression", value=0.78, unit="", symbol="eta"),
        ],
    })


def _domains(tab):
    """The domain pane's rows: (caption, count, provenance)."""
    return [tuple(tab.domain_list.topLevelItem(n).text(c) for c in range(3)) for n in range(tab.domain_list.topLevelItemCount())]


def _rows(tab):
    """The variable list's rows: (domain caption, name to write) -- a flat list, which this asserts too."""
    import variables_tab
    out = []
    for index in range(tab.tree.topLevelItemCount()):
        row = tab.tree.topLevelItem(index)
        assert row.childCount() == 0, "a row under another: the list is flat since v0.117"
        out.append((row.text(variables_tab.DOMAIN), row.data(variables_tab.NAME, 0x0100)[2]))
    return out


def _report(domain, name=None):
    """A row's key: its origin -- the report's reading here -- its domain and its name."""
    return ("rs", domain, name)


def _export_key(calc, instance, name=None):
    return ("export", f"{calc} · {instance}", name)


def _calls(tab):
    """The calls the «Affichage» view offers for what is chosen, each at its options' defaults, and its import line (v0.117: the card of calls left the right pane)."""
    import display_view
    return [display_view.entry_call(entry) for entry in tab.display_entries()] + [tab.display.import_field.text()]


def _detail(tab, key):
    caption, cell = tab.rows[key]
    return cell.text() if not cell.isHidden() else ""


def test_the_tab_has_three_panes_and_the_display_a_fourth():
    """Issue 13: «trois colonnes : domaines | variables | détail»; «Affichage»'s options are a fourth pane, hidden in «Données», and its page takes the detail's place -- the domains and the variables stay (D-011)."""
    tab = _tab()
    assert tab.splitter.count() == 4
    assert tab.splitter.widget(0).isAncestorOf(tab.domain_list)
    assert tab.splitter.widget(1).isAncestorOf(tab.tree)
    assert tab.splitter.widget(2).isAncestorOf(tab.identity)
    assert tab.splitter.widget(3) is tab.display.right
    assert tab.view == "data" and tab.display.right.isHidden()


def test_the_domains_are_a_pane_of_their_own():
    tab = _tab()
    _fill(tab, _sample())
    rows = _domains(tab)
    assert [caption for caption, _n, _p in rows] == [tab.t("vr_domain_report"), "T001", "S001-verify-compression"]
    assert rows[1][1] == "2", "a domain says how many variables it holds"
    assert rows[1][2] == f"{tab.t('vr_prov_typst')} · RS"
    # a check domain says what it is
    assert tab.t("vr_kind_check") in tab.domain_list.topLevelItem(2).toolTip(0)
    # nothing chosen, nothing listed -- and the list says why
    assert tab.tree.topLevelItemCount() == 0 and tab.empty.text() == tab.t("vr_choose_domain")
    tab.select_key(_report("T001"))
    assert sorted(key for _d, key in _rows(tab)) == ["A", "eta_w"]


def test_the_filter_reaches_the_domain_chosen_or_every_domain():
    """T3: «choisir, quand on filtre, de filtrer toutes les variables et pas seulement celles du domaine sélectionné» -- the box «Tous les domaines» (D-005)."""
    import variables_tab
    tab = _tab()
    _fill(tab, _sample())
    try:
        tab.select_key(_report("T001"))
        tab.search.setText("R_d")
        assert _rows(tab) == [] and tab.empty.text() == tab.t("vr_filtered")
        assert tab.tree.isColumnHidden(variables_tab.DOMAIN)
        tab.all_domains_box.setChecked(True)
        assert _rows(tab) == [(tab.t("vr_domain_report"), "R_d")]
        assert not tab.tree.isColumnHidden(variables_tab.DOMAIN), "every domain listed: each row names its own"
        tab.search.setText("eta")
        assert sorted(k for _d, k in _rows(tab)) == ["eta", "eta_w"]
        # every word, in any order: what an engineer types when he half remembers a name
        tab.search.setText("feucht 265")
        assert _rows(tab) == [("T001", "eta_w")]
        tab.search.setText("")
        tab.unit_box.setCurrentIndex(tab.unit_box.findData("kN"))
        assert _rows(tab) == [(tab.t("vr_domain_report"), "R_d")]
        tab.unit_box.setCurrentIndex(0)
        tab.search.setText("zzzz")
        assert not tab.tree.isVisibleTo(tab) and tab.empty.text() == tab.t("vr_filtered")
        # and the count beside a domain is its whole count, whatever the filter (D-015)
        assert _domains(tab)[1][1] == "2"
    finally:
        _fill(tab, _sample())


def test_every_source_is_listed_with_its_provenance():
    """T4: the Excel workbooks, Woodcore and Typst, each variable saying which (D-004, D-012)."""
    import variables_tab
    tab = _tab()
    export = _real_export()
    _fill(tab, _sample(), export)
    try:
        assert len(_domains(tab)) == 3 + len(export.domains)
        def provenance_of(key):
            tab.select_key(key)
            row = next(tab.tree.topLevelItem(n) for n in range(tab.tree.topLevelItemCount())
                       if tab.tree.topLevelItem(n).data(variables_tab.NAME, 0x0100) == key)
            return row.text(variables_tab.PROVENANCE)
        assert provenance_of(_export_key("snow-load", "SL", "h_0")) == "Excel"
        assert provenance_of(_export_key("dead-load", "EL+AL-Dach mit Wasser", "gk")) == "Woodcore"
        connector = next(d for d in export.domains if d.calculation == "connector" and any(v.source.startswith("woodcore:") for v in d.variables))
        woodcore = next(v for v in connector.variables if v.source.startswith("woodcore:"))
        assert provenance_of(("export", connector.name, woodcore.key)) == "Woodcore"
        assert provenance_of(_report("T001", "A")) == f"{tab.t('vr_prov_typst')} · RS"
        # the filter by provenance keeps one of them, over every domain
        tab.all_domains_box.setChecked(True)
        tab.provenance_box.setCurrentIndex(tab.provenance_box.findData(model.EXCEL))
        rows = [tab.tree.topLevelItem(n) for n in range(tab.tree.topLevelItemCount())]
        assert rows and {row.text(variables_tab.PROVENANCE) for row in rows} == {"Excel"}
        tab.provenance_box.setCurrentIndex(tab.provenance_box.findData(f"{model.TYPST}:rs"))
        assert sorted(k for _d, k in _rows(tab)) == ["A", "R_d", "eta", "eta_w"]
    finally:
        _fill(tab, _sample())


def test_a_result_is_marked_and_can_be_kept_alone():
    """D-007: ★ before a result of its calculation, and «Résultats seulement», unticked by default."""
    import variables_tab
    tab = _tab()
    export = _real_export()
    _fill(tab, _sample(), export)
    try:
        assert not tab.results_box.isChecked()
        snow = next(d for d in export.domains if d.address == ("snow-load", "SL"))
        tab.select_key(("export", snow.name, None))
        everything = _rows(tab)
        assert len(everything) == len(snow.variables)
        marked = [tab.tree.topLevelItem(n).text(variables_tab.NAME) for n in range(tab.tree.topLevelItemCount())]
        assert {text[len(variables_tab.RESULT_MARK):] for text in marked if text.startswith(variables_tab.RESULT_MARK)} == set(snow.results)
        tab.results_box.setChecked(True)
        assert sorted(k for _d, k in _rows(tab)) == sorted(snow.results)
    finally:
        _fill(tab, _sample())


def test_the_detail_carries_what_the_loads_tab_showed():
    """D-006: level, formula, choices, and the workbook, sheet and cell a value was read from."""
    tab = _tab()
    export = _real_export()
    _fill(tab, _sample(), export)
    try:
        tab.select_key(_export_key("snow-load", "SL", "h_0"))
        assert _detail(tab, "vr_provenance") == "Excel"
        assert _detail(tab, "vr_workbook") == "Belastungsannahmen.xlsm"
        assert _detail(tab, "vr_sheet") == "SL" and _detail(tab, "vr_cell") == "H10"
        assert _detail(tab, "vr_level") == "3"
        assert _detail(tab, "vr_source") == "excel:Belastungsannahmen.xlsm!SL!H10"
        assert not tab.open_button.isHidden()
        assert tab.open_button.isEnabled() == (conftest.PROJECT.root / "Belastungsannahmen.xlsm").exists()
        assert tab.open_button.toolTip() == tab.t("vr_open_workbook_tip"), "a disabled button says why"
        tab.select_key(_export_key("snow-load", "SL", "h_ref"))
        assert _detail(tab, "vr_formula") == 'h_"ref" = h_0 + Delta h'
        chosen = next((d, v) for d in export.domains for v in d.variables if v.choices)
        tab.select_key(("export", chosen[0].name, chosen[1].key))
        assert "▶" in _detail(tab, "vr_choices")
        # a value of a document carries none of it, and says it is untraced
        tab.select_key(_report("T001", "eta_w"))
        assert _detail(tab, "vr_workbook") == "" and tab.open_button.isHidden()
        assert not tab.untraced.isHidden()
    finally:
        _fill(tab, _sample())


def test_the_export_offers_the_calls_the_loads_tab_offered():
    """REQ-007, in the forms of the spec 2026-10-21-commandes-typst-refonte: a variable of the export -- `#var`, read live (REQ-009) --; a case -- its file included, the loop over its calculation's cases (REQ-017, UI-002) and the two load tables (Q-009) --; a polar moment its file and its loop, no load table."""
    tab = _tab()
    export = _real_export()
    _fill(tab, _sample(), export)
    try:
        tab.select_key(_export_key("snow-load", "SL", "h_0"))
        assert [e.key for e in tab.display_entries()] == ["var"]
        assert ref.call_var_domain("snow-load", "SL", "h_0") in _calls(tab)
        snow = next(d for d in export.domains if d.address == ("snow-load", "SL"))
        tab.select_key(("export", snow.name, None))
        keys = [e.key for e in tab.display_entries()]
        assert keys[0] == "file" and "loop" in keys and "summary" in keys and "line-summary" in keys, keys
        calls = _calls(tab)
        assert ref.call_include_domain("snow-load", "SL") in calls and ref.call_domain_loop("snow-load") in calls, calls
        assert tab.address(tab.selected_key()) == ("snow-load", "SL")
        # a polar moment is a calculation too, with no load table
        connection = next(d for d in export.domains if d.calculation == "connection")
        tab.select_key(("export", connection.name, None))
        keys = [e.key for e in tab.display_entries()]
        assert "file" in keys and "summary" not in keys, keys
    finally:
        _fill(tab, _sample())


def test_the_real_export_is_listed_domain_by_domain_in_its_own_order():
    """REQ-002 and REQ-003 on the example's own export, not a sample: one row per domain with its whole count, and a case's variables in the order calculations.json states them, flat."""
    import variables_tab
    tab = _tab()
    export = _real_export()
    _fill(tab, _sample(), export)
    try:
        counts = {(tab.domain_list.topLevelItem(n).data(0, 0x0100)): tab.domain_list.topLevelItem(n).text(1)
                  for n in range(tab.domain_list.topLevelItemCount())}
        assert len(counts) == tab.domain_list.topLevelItemCount() == len(tab.all_domains()), "one row per domain read"
        for domain in export.domains:
            assert counts[(domain.origin, domain.name)] == str(len(domain.variables)), domain.name
        data = json.loads((conftest.PROJECT.data_dir / "calculations.json").read_text(encoding="utf-8"))
        tab.select_key(_export_key("snow-load", "SL"))
        assert [key for _d, key in _rows(tab)] == list(data["domains"]["snow-load"]["instances"]["SL"]["vars"])
        # and a polar moment says it is Woodcore's
        connection = next(d for d in export.domains if d.calculation == "connection")
        tab.select_key(("export", connection.name, "I_p"))
        row = tab.tree.currentItem()
        assert row is not None and row.text(variables_tab.PROVENANCE) == "Woodcore"
    finally:
        _fill(tab, _sample())


def test_in_affichage_the_domains_and_the_variables_stay():
    """D-011: the page takes the detail's place and the options are shown; the domains and the variables stay, so another variable can be chosen."""
    tab = _tab()
    _fill(tab, _sample())
    try:
        tab.set_view("display", enter=False)
        assert tab.panes.centre.currentIndex() == 1, "the page is where the detail was"
        assert not tab.display.right.isHidden(), "the options are a pane of their own"
        assert not tab.splitter.widget(0).isHidden() and not tab.splitter.widget(1).isHidden()
        tab.select_key(_report("T001", "A"))
        assert tab.selected_key() == _report("T001", "A")
    finally:
        tab.set_view("data", enter=False)
    assert tab.panes.centre.currentIndex() == 0 and tab.display.right.isHidden()


def test_building_and_showing_the_tab_writes_nothing():
    """ARCH-002 on the tab itself: built on a copy of the project and shown, it leaves every file of the project as it was."""
    import variables_tab
    here = conftest.project_copy("vt_readonly")
    _tab()
    before = {str(p.relative_to(here.root)): (p.stat().st_size, p.stat().st_mtime_ns) for p in here.root.rglob("*") if p.is_file()}
    with project.using(here):
        tab = variables_tab.VariablesTab(_WINDOW["window"])
        tab.setParent(_WINDOW["window"])
        tab.on_shown()
        tab.all_domains_box.setChecked(True)
    after = {str(p.relative_to(here.root)): (p.stat().st_size, p.stat().st_mtime_ns) for p in here.root.rglob("*") if p.is_file()}
    assert after == before


def test_the_tab_offers_no_var_call_for_the_report_own_domain():
    """`#var("R_d")` alone can never work, and a variable of the report's own domain has nothing to be carried out of."""
    tab = _tab()
    _fill(tab, _sample())
    tab.select_key(_report("", "R_d"))
    calls = _calls(tab)
    assert not [c for c in calls if c.startswith("#var(")], calls
    tab.select_key(_report("T001", "A"))
    calls = _calls(tab)
    assert '#var("A", domain: "T001")' in calls, calls
    assert ref.import_line() in calls
    assert tab.address(tab.selected_key()) is None


def test_a_domain_row_offers_the_find_calls():
    tab = _tab()
    _fill(tab, _sample())
    tab.select_key(_report("T001"))
    assert ref.call_find("T001") in _calls(tab)
    # «name» is an option of find's panel since v0.117, where it was a call of its own
    import display_view
    find = next(entry for entry in tab.display_entries() if entry.command == "find")
    assert display_view.entry_call(find, {"type": "name"}) == ref.call_find("T001", "name")


def test_the_tab_reads_on_its_first_showing_and_later_only_when_it_is_free():
    """The rule since v0.110, in both halves.

    A tab switch must not cost a **compile**, but it may well cost the half-second of opening a PDF that already
    carries the answer. So: the first showing reads whatever it costs, which is what the engineer asked for; a
    later one reads only where `pdf_is_current` says the report has been exported since, which is how an
    *Exporter PDF* on another tab is picked up by coming back.
    """
    import unittest.mock as mock

    import variables_tab
    _tab()
    tab = variables_tab.VariablesTab(_WINDOW["window"])
    tab.setParent(_WINDOW["window"])   # owned by the window, as a tab always is: an orphan tab outlived the application and crashed the interpreter's exit (v0.117)
    tab.readings = {}                        # nothing cached: the first showing should read
    # the suite turns the automatic reading off (conftest), so it is turned back on for these checks
    on = mock.patch.object(model, "auto_enabled", return_value=True)

    with on, mock.patch.object(model, "pdf_is_current", return_value=False), \
            mock.patch.object(tab, "reload") as spy:
        tab.on_shown()
        assert spy.called and spy.call_args.kwargs.get("automatic") is True, "the first showing did not read"
        spy.reset_mock()
        tab.on_shown()
        tab.on_shown()
        assert not spy.called, "a later showing paid for a compile"

    # and a PDF exported since is picked up, because reading it is free
    with on, mock.patch.object(model, "pdf_is_current", return_value=True), \
            mock.patch.object(tab, "reload") as spy:
        tab.on_shown()
        assert spy.called, "a PDF exported since was not picked up"


def test_the_export_is_read_again_at_every_showing():
    """D-014: a polar moment saved on another tab is here when one comes back -- the four files are read from disk, not from what the window loaded at startup."""
    import unittest.mock as mock

    import variable_sources
    tab = _tab()
    with mock.patch.object(variable_sources, "read_export", return_value=variable_sources.Export()) as spy:
        tab.on_shown()
        assert spy.called
    tab.on_shown()


def test_a_current_reading_is_not_read_again_on_the_first_showing():
    import unittest.mock as mock

    import variables_tab
    _tab()      # the window is built here, and it is what a second tab is built on
    tab = variables_tab.VariablesTab(_WINDOW["window"])
    tab.setParent(_WINDOW["window"])   # owned by the window, as a tab always is: an orphan tab outlived the application and crashed the interpreter's exit (v0.117)
    with mock.patch.object(model, "is_current", return_value=True), mock.patch.object(tab, "reload") as spy:
        tab.on_shown()
        assert not spy.called, "a reading that still answers was paid for again"


def test_the_tab_keeps_what_it_had_when_a_reading_fails():
    """And says where the failure is: Typst names the file and the line, which nothing in the window could."""
    import unittest.mock as mock

    import variable_sources
    tab = _tab()
    _fill(tab, _sample())
    before = tab.readings["rs"].count
    typst_said = "error: file not found (searched at Images/image.png)\n   ┌─ Sections/005.typ:90:4"
    tab.read_failed("rs", model.VariablesError("no", "compile_failed", exit_code=1, output=typst_said))
    try:
        with mock.patch.object(variable_sources, "read_export", return_value=variable_sources.Export()):
            tab.read_finished()
        assert tab.readings["rs"].count == before, "a failed reading threw away the values that were on screen"
        assert tab.reload_button.isEnabled()
        # the banner carries the reason AND Typst's own message, in the danger colour
        assert tab.t("vr_err_compile_failed") in tab.banner.text()
        assert "Sections/005.typ:90:4" in tab.banner.text(), "Typst's own message is not shown"
        assert tab.banner.property("callout") == "danger"
        # isVisibleTo, not isVisible: this window is never shown, so every child reads as hidden
        assert tab.banner.isVisibleTo(tab)
        # and the bar says what is on screen rather than repeating the banner's first line
        assert tab.t("vr_count", count=before, domains=len(tab.readings["rs"].domains)) == tab.state.text()
    finally:
        _fill(tab, _sample())


def test_a_file_of_the_export_that_cannot_be_read_is_named_in_the_banner():
    """ARCH-003: a defect of a file Woodcore wrote is said with its name; what the other files hold stays listed."""
    import variable_sources
    tab = _tab()
    broken = variable_sources.Export(errors=[model.VariablesError("x", "bad_file", file="connections.json", path="x", field="connections.VU-MP-1: boom")])
    _fill(tab, _sample(), broken)
    try:
        assert "connections.json" in tab.banner.text() and "boom" in tab.banner.text()
        assert tab.banner.property("callout") == "danger" and tab.banner.isVisibleTo(tab)
        assert len(_domains(tab)) == 3
    finally:
        _fill(tab, _sample())


def test_a_project_not_exported_says_so():
    import variable_sources
    tab = _tab()
    missing = variable_sources.Export(missing=[name for name, _s, _r in variable_sources.FILE_SOURCES])
    _fill(tab, None, missing)
    try:
        assert tab.t("vr_no_export") in tab.empty.text()
    finally:
        _fill(tab, _sample())


def test_a_first_reading_that_fails_leaves_the_bar_saying_so():
    """There is then nothing on screen for the bar to describe, so it carries the failure itself."""
    import unittest.mock as mock

    import variable_sources
    tab = _tab()
    try:
        _fill(tab, None)
        tab.read_failed("rs", model.VariablesError("no", "no_typst"))
        with mock.patch.object(variable_sources, "read_export", return_value=variable_sources.Export()):
            tab.read_finished()
        assert tab.t("vr_err_no_typst") in tab.state.text()
        # the document is named: of three, the bar says which could not be read
        assert tab.document_name("rs") in tab.state.text()
        assert tab.banner.isVisibleTo(tab) and tab.banner.property("callout") == "danger"
    finally:
        _fill(tab, _sample())


def test_every_refusal_the_module_can_raise_has_a_sentence_in_three_languages():
    """A code the window has no sentence for would reach the engineer as Python's own message."""
    import variables_tab
    codes = set()
    for module in ("variables.py", "variable_sources.py"):
        source = (ROOT / "calc" / module).read_text(encoding="utf-8")
        codes |= set(re.findall(r'VariablesError\(\s*(?:f?"[^"]*"|f?"""|[^,]+?),\s*"([a-z_]+)"', source))
        codes |= set(re.findall(r'"([a-z_]+)"\)\s*from exc', source))
    codes = {c for c in codes if c}
    assert codes and "bad_file" in codes, codes
    for lang, texts in variables_tab.STRINGS.items():
        for code in codes:
            assert f"vr_err_{code}" in texts, f"{lang}: no sentence for the refusal {code!r}"


def test_the_tab_speaks_the_window_three_languages():
    import variables_tab
    reference = set(variables_tab.STRINGS["fr"])
    for lang, texts in variables_tab.STRINGS.items():
        assert set(texts) == reference, (lang, reference ^ set(texts))
        assert texts["tab_variables"], lang
        for key, text in texts.items():
            assert text.strip(), f"{lang}: {key} is empty"
    # Swiss German, never an ß (§4bis)
    assert "ß" not in "".join(variables_tab.STRINGS["de"].values())
    # the raw `source` is «Source» and the column «Provenance»: two words for two things (review ARCH-RISK-012)
    assert variables_tab.STRINGS["fr"]["vr_source"] != variables_tab.STRINGS["fr"]["vr_provenance"]


def test_the_tab_carries_its_view_through_a_rebuild():
    tab = _tab()
    _fill(tab, _sample())
    try:
        tab.all_domains_box.setChecked(True)
        tab.results_box.setChecked(False)
        tab.search.setText("eta")
        tab.unit_box.setCurrentIndex(tab.unit_box.findData(""))
        tab.provenance_box.setCurrentIndex(tab.provenance_box.findData(f"{model.TYPST}:rs"))
        tab.select_key(_report("T001", "eta_w"))
        state = tab.view_state()
        _fill(tab, _sample())
        tab.restore(state)
        assert tab.search.text() == "eta"
        assert tab.unit_box.currentData() == ""
        assert tab.provenance_box.currentData() == f"{model.TYPST}:rs"
        assert tab.all_domains_box.isChecked()
        assert tuple(tab.selected_key()) == _report("T001", "eta_w")
    finally:
        _fill(tab, _sample())


def test_a_view_of_the_tree_s_time_is_read_without_harm():
    """Before v0.117 the splitter had three panes and the filter a document: three sizes laid on four panes would squeeze the detail to nothing, so they are not applied, and the rest is read (review ARCH-RISK-001)."""
    tab = _tab()
    _fill(tab, _sample())
    before = tab.splitter.sizes()
    try:
        tab.restore({"splitter": [500, 300, 0], "search": "", "unit": None, "document": "rs",
                     "source": "rs", "domain": "T001", "name": "A", "opened": False})
        assert tab.splitter.sizes() == before
        assert tuple(tab.selected_key()) == _report("T001", "A")
    finally:
        _fill(tab, _sample())


def test_the_tab_edits_nothing():
    """It reads and copies; it carries no unsaved changes and is in none of the window's writers.

    ⚠️ It does have a `confirm_leave`, which every other tab has in order to *refuse* a close: here it only
    waits for a reading's thread and always answers True, that being the one hook the window offers a tab on
    its way out (`closeEvent`). So a tab that saves nothing has one, and what is asserted is that it never
    refuses rather than that it has none.
    """
    import woodcore_gui
    tab = _tab()
    assert not hasattr(tab, "save")
    assert tab.confirm_leave() is True
    for name in woodcore_gui.WRITERS:
        assert not hasattr(tab, name), f"the Variables tab has a writer named {name!r}"
    # ⚠️ And no `dirty`: it is what tells an editor from a browser, and `tests/test_window.py` takes every tab
    # that has one for an editor and calls `update_list_marker()` on it. A `dirty` always False would owe that
    # walk a marker this tab has no list to mark -- which is how the four errors in test_window read today.
    assert not hasattr(tab, "dirty"), "the Variables tab is a browser: a `dirty` puts it among the editors"
    for browser in ("CommandsTab",):
        other = [t for t in _WINDOW["window"].tabs if type(t).__name__ == browser]
        if other:
            assert not hasattr(other[0], "dirty"), f"{browser} gained a dirty: the convention moved"


def test_a_disabled_reload_button_says_why():
    """v0.47's rule, which tests/test_window.py holds for every tab: a button shown disabled with no tooltip cannot be told from a broken one. Held here too, on the one button that is ever disabled, so a failure names this tab rather than the whole window."""
    tab = _tab()
    tab.set_reading(True)
    try:
        assert not tab.reload_button.isEnabled()
        assert tab.reload_button.toolTip() == tab.t("vr_reading")
    finally:
        tab.set_reading(False)
    assert tab.reload_button.isEnabled()
    # and an enabled one says what it will cost, a reading being a compile of some seconds
    assert tab.reload_button.toolTip() == tab.t("vr_reload_hint")


def test_the_automatic_reading_is_turned_off_for_the_suite():
    """`WOODCORE_VARIABLES_READ=0`, as conftest sets it -- and «Relire» is unaffected, what is turned off being reading without being asked."""
    assert not model.auto_enabled(), "conftest no longer turns the automatic reading off"
    import unittest.mock as mock

    import variables_tab
    _tab()
    tab = variables_tab.VariablesTab(_WINDOW["window"])
    tab.setParent(_WINDOW["window"])   # owned by the window, as a tab always is: an orphan tab outlived the application and crashed the interpreter's exit (v0.117)
    tab.readings = {}
    with mock.patch.object(tab, "reload") as spy:
        tab.on_shown()
        assert not spy.called, "a suite run paid for a compile by opening a tab"
    with mock.patch.object(model, "auto_enabled", return_value=True), mock.patch.object(tab, "reload") as spy:
        tab.opened = False
        tab.on_shown()
        assert spy.called, "with the automatic reading on, the first showing does not read"


def test_the_tab_is_named_once_in_the_navigation_and_has_an_icon():
    import chrome
    import woodcore_gui
    keys = [key for key, _factory in woodcore_gui.TABS]
    assert "tab_variables" in keys
    named = [group for group, members in woodcore_gui.NAV_GROUPS if "tab_variables" in members]
    assert named == ["nav_reference"], named
    assert "tab_variables" in chrome.ICONS


def test_the_variables_tab_sits_between_the_formulas_and_the_commands():
    """Where it is in *Référence* is a decision and not an accident: «Formule» is what to write, «Variables»
    what there is to name in what you write, «Commandes» what there is to call — this project's own values
    before the engine's surface, the more specific first. It also fixes Ctrl+n for the three.

    ⚠️ A **relative** ordering and not the exact tuple `test_journal.py` pins `nav_project` with. Four sessions
    add tabs to this file at once, so an exact tuple is a test that fails for everyone who adds a neighbour
    while catching nothing about *this* tab; the ordering catches a reorder and survives a newcomer. It is
    `test_chrome.py`'s own shape for `nav_structure` («Schémas» right under «Modèles statiques»).
    """
    import woodcore_gui
    reference = dict(woodcore_gui.NAV_GROUPS)["nav_reference"]
    # «Formule» since 0.117 -- the tab that writes calculation domains, in the place of v0.100's «Formules» (keyword lines), retired then (archive/formules-dsl/)
    for key in ("tab_formula", "tab_variables", "tab_commands"):
        assert key in reference, (key, reference)
    assert reference.index("tab_formula") < reference.index("tab_variables") < reference.index("tab_commands"), reference


# ---------------------------------------------------------------- one reading per document (the three documents, 30.09.2026)
#
# ⚠️ A project laid out in three documents compiles each from the **project's own folder**, which is its Typst root
# -- so what a reading of one document is stamped with must never be a walk of that root: it would take the other
# two documents, the workbooks, the archives and the export's own stamps for sources of this one's variables, and
# a compile of any document would make a reading of every other stale. It is calc/stamps.py's enumeration of what
# the document reads instead (`_sources`).

def _three_documents(name):
    """A new project in three documents, as «Nouveau projet» makes one."""
    import project_template
    return project_template.create(conftest.tmpdir(name) / "Halle", "Halle")


def _compile_and_stamp(here, mode):
    """Document `mode` compiled into its own PDF and stamped, as `woodcore-cli export` does it (calc/cli.py)."""
    import subprocess

    import documents
    import stamps
    deps = stamps.deps_file(here, mode)
    done = subprocess.run([project.typst_executable(), *documents.compile_args(here, mode, deps=deps)],
                          capture_output=True, timeout=model.TIMEOUT_S, cwd=here.typst_root)  # in the Typst root, as every compile of Woodcore's
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")[-800:]
    stamps.record(here, mode, [], deps, here.document_pdf(mode))


def test_each_document_has_a_cache_of_its_own_and_the_report_keeps_its_name():
    """The report's cache keeps the name it had before the three documents, so a reading made then is still found; the two others are named after their document."""
    here = _three_documents("variables-cache-names")
    names = {mode: model.cache_file(here, mode).name for mode in here.modes}
    assert names["rs"] == model.cache_file(here).name and "-" not in names["rs"], names
    assert names["cu"].endswith("-cu.json") and names["bp"].endswith("-bp.json"), names
    assert len(set(names.values())) == 3, names


def test_a_document_stamp_reads_its_own_folder_and_not_the_whole_project():
    here = _three_documents("variables-stamp-documents")
    rs, cu = model.stamp(here, "rs"), model.stamp(here, "cu")
    time.sleep(0.01)
    # what lies at the top of the project and is no source of the report: another document, the workbook, the architect's plans, the export's own stamps and variants
    section = sorted((here.document_dir("cu") / "Sections").glob("*.typ"))[0]
    section.write_text(section.read_text(encoding="utf-8") + "\n// only the CU\n", encoding="utf-8")
    for stray in (here.root / "01_Pläne" / "Grundriss.pdf", here.stamps_dir / "rs.json", here.generated_dir / "out" / "report-1.pdf",
                  here.archives_dir / "older.zip", here.root / "notes.typ"):
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_text("x", encoding="utf-8")
    here.positions_book.write_bytes(b"a stray workbook")   # no Positionen.xlsx is made since v0.114: one left at the top is no source of the report either
    import positions_store
    positions_store.create_blank(here, None, "Träger")     # nor are the project's positions, which the report reads through the export
    assert model.stamp(here, "rs") == rs, "the report's reading moved with what is not the report"
    assert model.stamp(here, "cu") != cu, "the CU's own section edited did not move the CU's reading"
    # and what the three share moves all three
    before = {mode: model.stamp(here, mode) for mode in here.modes}
    here.config_typ.write_text(here.config_typ.read_text(encoding="utf-8") + "\n// shared\n", encoding="utf-8")
    assert all(model.stamp(here, mode) != before[mode] for mode in here.modes), "config.typ is read by every document"


def test_a_reading_is_the_document_s_own_and_its_pdf_is_judged_by_its_stamp():
    if not conftest.have_typst():
        raise Skip("typst is not on the PATH")
    here = _three_documents("variables-documents")
    section = sorted((here.document_dir("cu") / "Sections").glob("*.typ"))[0]
    section.write_text(section.read_text(encoding="utf-8") + '\n#var("x_cu", 7, "kN")\n', encoding="utf-8")

    cu, rs = model.read(here, mode="cu"), model.read(here, mode="rs")
    assert ("", "x_cu") in {(v.domain, v.key) for v in cu.variables()}, "the CU's own variable is not in its reading"
    assert "x_cu" not in {v.key for v in rs.variables()}, "the CU's variable reached the report's reading"
    assert model.cached(here, "cu").count == cu.count and model.is_current(model.cached(here, "cu"), here, "cu")

    # the PDF, compiled and stamped: current, and it carries the same registry a compile gives
    _compile_and_stamp(here, "cu")
    assert model.pdf_is_current(here, "cu")
    shape = lambda reg: sorted((v.domain, v.key, v.value, v.unit) for v in reg.variables())
    attached = model.from_pdf(here, "cu")
    assert attached is not None and shape(attached) == shape(cu), "the CU's PDF does not carry the CU's registry"
    assert shape(model.best(here, mode="cu")) == shape(cu)
    assert not model.pdf_is_current(here, "bp"), "a document never compiled has a current PDF"

    # a time alone changes nothing -- the stamp is a digest -- where the rule of modification times said «stale»
    later = time.time() + 5
    os.utime(section, (later, later))
    assert model.pdf_is_current(here, "cu"), "a section saved again with the same bytes made the PDF stale"
    # the bytes changed: stale
    section.write_text(section.read_text(encoding="utf-8") + "\n// edited\n", encoding="utf-8")
    assert not model.pdf_is_current(here, "cu"), "a section edited left the PDF current"
    assert model.from_pdf(here, "cu") is None
    # a PDF another route wrote since, which the stamp was not taken of: judged by its time, as before the stamps
    pdf = here.document_pdf("cu")
    pdf.write_bytes(pdf.read_bytes() + b"\n")
    os.utime(pdf, (later + 10, later + 10))
    assert model.pdf_is_current(here, "cu"), "a PDF newer than every source, written by a route that stamps nothing, is not current"
