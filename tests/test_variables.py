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
    """The Variables tab of a window built once, off-screen, on the report."""
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
        window.mode = "rs"
        window.apply_mode()
        found = [t for t in window.tabs if isinstance(t, variables_tab.VariablesTab)]
        assert found, "the window has no Variables tab -- is it in woodcore_gui.TABS?"
        _WINDOW["window"], _WINDOW["tab"] = window, found[0]
    return _WINDOW["tab"]


def _browser():
    return _tab().service("browser")


def _banner(b):
    """The type's banner the browser tells (issue #106: data_tab.ExportBanner, above the browser, no longer inside it)."""
    return b.ctx.host.service("banner").label


_EXPORT = {}


def _real_export():
    import variable_sources
    if "export" not in _EXPORT:
        found = variable_sources.read_export(conftest.PROJECT)
        assert not found.errors, [str(e) for e in found.errors]
        _EXPORT["export"] = found
    return _EXPORT["export"]


def _fill(browser, registry, export=None):
    """The tab listing `registry` as the report's reading and `export` as the export's -- the example's real export by default --, its filter, its choice and its field's choice cleared."""
    import variable_query as query
    browser.readings = {"rs": registry} if registry is not None else {}
    browser.errors = {}
    browser.export = export if export is not None else _real_export()
    browser.filter = query.Filter()
    browser.selection.chosen, browser.selection.focus, browser.selection.anchor = {}, None, None
    browser.search.blockSignals(True)
    browser.search.setText("")
    browser.search.blockSignals(False)
    browser.refresh()


def _sample():
    """A report's registry of the example's shape: its root domain, a domain it declares itself, and `SL`, which the export computes."""
    return model.Registry(stamp="pinned", domains={
        "": [model.Variable(key="R_d", domain="", value=2.655, unit="kN", symbol="R_d", label="Tragwiderstand")],
        "T001": [
            model.Variable(key="A", domain="T001", value=20000.0, unit="mm²", symbol="A"),
            model.Variable(key="eta_w", domain="T001", value=0.8, unit="", symbol="eta_w",
                           label="Feuchteklasse 2", norm="SIA 265", norm_ref="Tabelle 4"),
        ],
        "SL": [model.Variable(key="q_k1", domain="SL", value=1.115, unit="kN/m²", symbol="q_k1")],
    })


def _report(domain, name=None):
    return ("rs", domain, name)


def _export_key(calc, instance, name=None):
    return ("export", f"{calc} · {instance}", name)


def _side(browser):
    """The left pane's domains: [(origin, name)], in their order."""
    out = []
    for n in range(browser.domain_list.topLevelItemCount()):
        key = browser.domain_list.topLevelItem(n).data(0, 0x0100)
        if key is not None:
            out.append(tuple(key))
    return out


def _shown(browser):
    return browser.list.shown()


def _rows(browser):
    model_ = browser.list.list_model
    return [r for r in range(model_.rowCount()) if model_.key(r) is not None]


# ---------------------------------------------------------------- the panes and the shell (UI-001, ARCH-004, ARCH-009)

def test_the_tab_has_three_panes_and_one_view():
    """UI-001: the domains, the variables, the card -- and no «Données · Affichage» any more (D-4)."""
    import views
    tab = _tab()
    b = tab.service("browser")
    assert tab.splitter is b.splitter and b.splitter.count() == 3
    assert b.splitter.widget(0).isAncestorOf(b.domain_list) and b.splitter.widget(0).isAncestorOf(b.menu)
    assert b.splitter.widget(1).isAncestorOf(b.list) and b.splitter.widget(1).isAncestorOf(b.search_bar)
    assert b.splitter.widget(2) is b.detail
    assert views.declared(tab) == () and tab.VIEWS == () and not hasattr(tab, "display")   # VIEWS empty, the type «Données»'s (issue #106), where the shell of before had none
    assert not hasattr(tab, "install_display") and not hasattr(tab, "display_entries") and not hasattr(tab, "chosen")


def test_the_shell_only_forwards_and_the_content_is_the_browser_s():
    """ARCH-004, ARCH-009; issue #106 (D-06): VariablesTab names its parameters and the names it exposes -- set by the type as redirections to its browser --, and nothing else."""
    import data_tab
    import variables_browser
    import variables_tab
    exposed = {"begin_pick", "end_pick", "pick_chosen", "selected_key", "selected_keys", "variable", "address", "select_key", "search", "domains", "pick_bar", "pick_label"}
    names = {n for n in vars(variables_tab.VariablesTab) if not (n.startswith("__") and n.endswith("__"))} - {"staticMetaObject"}
    assert names == {"KEY", "SERVICES", "EXPOSES"} | exposed, sorted(names)
    assert set(variables_tab.VariablesTab.EXPOSES) == exposed and all(isinstance(vars(variables_tab.VariablesTab)[n], data_tab.Exposed) for n in exposed)
    assert not any(base.__module__.startswith("PySide6") for base in variables_browser.VariablesBrowser.__mro__), "the content is a plain class (a service's shape)"
    source = (ROOT / "calc" / "tools" / "variables_browser.py").read_text(encoding="utf-8")
    assert "self.app.tabs" not in source, "the content reads no other tab"


def test_the_browser_alone_reads_filters_chooses_and_copies():
    """ARCH-009: the content built without its shell."""
    import variables_browser
    from PySide6.QtWidgets import QWidget
    window = _tab().app
    browser = variables_browser.VariablesBrowser(window)
    holder = QWidget(window)
    browser.mount().setParent(holder)
    _fill(browser, _sample())
    browser.search.setText("kn " + browser.t("tab_ac_snow").lower())   # «kn neige» in the window's language
    keys = _shown(browser)
    assert keys and all(browser.variable(k).unit.lower().startswith("kn") for k in keys)
    browser.list.gesture(browser.list.list_model.row_of(keys[0]), 1)
    assert browser.selected_key() == keys[0]
    copied = []
    browser.copy = copied.append
    browser.copy_chosen()
    assert copied and copied[0].startswith("#var(")
    holder.deleteLater()


def test_the_root_domain_of_a_document_is_neither_listed_nor_counted():
    """REQ-005, D-5: «R_d» of the report's own domain is in no pane."""
    b = _browser()
    _fill(b, _sample())
    assert ("rs", "") not in b.domains and _report("T001")[:2] in b.domains
    assert not any(k[1] == "" for k in _shown(b))
    count = sum(len(d.variables) for d in b.domains.values())
    assert b.state_label.text().startswith(b.t("vr_count", count=count, domains=len(b.domains)))


def test_the_example_counts_974_variables_in_76_domains_once_its_documents_are_read():
    """REQ-005, CON-005: measured on 25.10.2026 (935 in 78 with the three root domains, the issue's figures); 974 in 76 once the example's loads are sources (issue #109: the wind's six Q_k, its renamed cases)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the PATH")
    b = _browser()
    readings = {mode: model.best(conftest.PROJECT, mode=mode) for mode in conftest.PROJECT.created_modes}
    try:
        b.readings, b.errors, b.export = readings, {}, _real_export()
        b.refresh()
        count = sum(len(d.variables) for d in b.domains.values())
        assert (count, len(b.domains)) == (974, 76), (count, len(b.domains))
    finally:
        _fill(b, _sample())


# ---------------------------------------------------------------- the menu, the source, the tags (UI-002 to UI-004)

def test_the_menu_counts_in_the_source_and_greys_an_entry_at_zero():
    b = _browser()
    _fill(b, _sample())
    from PySide6.QtCore import Qt
    seismic = b.menu.item("tab_ac_seismic")
    assert seismic is not None and not (seismic.flags() & Qt.ItemFlag.ItemIsEnabled), "a reserved tab: zero, greyed"
    assert b.menu.item("tab_ac_snow").text(1) == str(b.catalogue.count("tab_ac_snow", "all"))
    assert b.menu.item("doc:rs") is not None, "the report's own domains under its entry (D-14)"
    b.choose_source("export")
    assert b.menu.item("tab_ac_snow").text(1) == str(b.catalogue.count("tab_ac_snow", "export"))
    assert b.menu.item("doc:rs").text(1) == "—"
    b.menu.choose("s:nav_actions:tab_ac_imposed")
    assert b.filter.menu == "s:nav_actions:tab_ac_imposed" and b.menu.text().startswith(b.t("nav_actions"))
    assert {b.catalogue.tab_title(b.domains[k]) for k in _side(b)} <= {b.t(k) for k in ("tab_ac_imposed", "tab_ac_snow", "tab_ac_wind", "tab_ac_seismic")}
    _fill(b, _sample())


def test_a_click_on_a_domain_chooses_it_a_second_lets_it_go_and_the_tag_follows():
    """UI-003, UI-004: the domain chosen on the left is a tag of the search bar; its × lets it go on the left too; ⌫ in an empty bar takes the tags off from the last."""
    b = _browser()
    _fill(b, _sample())
    sl = _export_key("snow-load", "SL")[:2]
    b.click_domain(sl)
    assert b.filter.domain == sl and b.search_bar.kinds() == ["domain"] and {k[:2] for k in _shown(b)} == {sl}
    b.click_domain(sl)
    assert b.filter.domain is None and b.search_bar.kinds() == []
    b.choose_menu("s:nav_actions:tab_ac_imposed")
    b.choose_source("export")
    b.click_domain(_export_key("live-load", "A1")[:2])
    assert b.search_bar.kinds() == ["menu", "source", "domain"]
    b.search_bar.close_button("domain").click()
    assert b.filter.domain is None and b.domain_list.currentItem() is None
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication
    QApplication.sendEvent(b.search, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier))
    assert b.search_bar.kinds() == ["menu"] and b.filter.source == "all" and b.source_switch.current_key() == "all"
    _fill(b, _sample())


def test_the_search_finds_every_word_in_the_filter_and_the_count_is_the_list_s():
    """UI-005: «kn neige»; «Résultats seulement»; the count beside the filters."""
    b = _browser()
    _fill(b, _sample())
    b.search.setText("kn " + b.t("tab_ac_snow").lower())   # «kn neige» in the window's language
    keys = _shown(b)
    assert keys and {b.catalogue.tab_title(b.domains[k[:2]]) for k in keys} == {b.t("tab_ac_snow")}
    assert b.count_label.text() == b.t("vr_list_count", count=len(keys), domains=len({k[:2] for k in keys}))
    b.search.setText("")
    b.results_box.setChecked(True)
    assert all(k[2] in b.domains[k[:2]].results for k in _shown(b))
    assert _export_key("live-load", "A1", "q_k") in _shown(b) and ("formulas", "A1", "q_k") in _shown(b), "REQ-004: a result in each source"
    b.results_box.setChecked(False)
    _fill(b, _sample())


# ---------------------------------------------------------------- the choice (UI-009, UI-010, REQ-007)

def test_ctrl_click_three_variables_the_last_is_selected_key_and_all_are_selected_keys():
    """REQ-007, UI-010: `selected_key()` the last one clicked, `selected_keys()` all in the order of the list; «Copier les 3 commandes» one line each in that order; a variable hidden by the filter stays chosen."""
    import build_reference as ref
    tab = _tab()
    b = tab.service("browser")
    _fill(b, _sample())
    b.search.setText("q_k")
    rows = _rows(b)
    picked = [rows[5], rows[0], rows[3]]
    b.list.gesture(picked[0], 1)
    b.list.gesture(picked[1], 1, ctrl=True)
    b.list.gesture(picked[2], 1, ctrl=True)
    keys = [b.list.list_model.key(r) for r in picked]
    assert tab.selected_key() == keys[2]
    assert tab.selected_keys() == [b.list.list_model.key(r) for r in sorted(picked)]
    assert not b.choice_bar.isHidden() and b.choice_label.text() == b.t("vr_selected", count=3)
    assert b.copy_button.text() == b.t("vr_copy_many", count=3)
    copied = []
    b.copy = copied.append
    b.copy_chosen()

    def call(k):
        domain = b.domains[k[:2]]
        return ref.call_var_domain(*domain.address, k[2]) if k[0] == "export" else ref.call_var_registry(k[2], k[1])
    assert copied[0].split("\n") == [call(k) for k in tab.selected_keys()]
    first = tab.selected_keys()[0]
    b.click_domain(keys[2][:2])   # a filter that hides the others
    assert len(b.selection) == 3 and b.selection.hidden(_shown(b)) == 2
    assert b.choice_label.text() == b.t("vr_selected_hidden", count=3, hidden=2)
    b.copy_chosen()
    assert copied[-1].split("\n")[0] == call(keys[2]) and copied[-1].split("\n")[1] == call(first), "the shown first, then the hidden in the order of the list"
    b.clear_choice()
    assert len(b.selection) == 0 and b.choice_bar.isHidden()
    _fill(b, _sample())


def test_a_sibling_s_button_chooses_the_same_variable_in_the_other_source():
    """UI-011: «Le même calcul ailleurs», a button per other source."""
    b = _browser()
    _fill(b, _sample())
    b.select_key(_export_key("snow-load", "SL", "q_k1"))
    texts = [button.text() for button in b.detail.sibling_buttons]
    assert len(texts) == 2 and "RS" in texts[-1], texts
    assert b.detail.computed.text() == b.t("vr_computed_here")
    b.detail.sibling_buttons[-1].click()
    assert b.selected_key() == _report("SL", "q_k1")
    assert b.detail.computed.text() == b.t("vr_computed_in", source=b.t("vr_badge_export"))
    _fill(b, _sample())


def test_the_card_of_a_variable_and_of_a_domain():
    """UI-011, UI-012: the head, the result's frame, «Vient de» in words, the command and what to include; a domain alone its whole file and its counts."""
    b = _browser()
    _fill(b, _sample())
    d = b.detail
    b.select_key(_export_key("snow-load", "SL", "q_k1"))
    assert not d.result_tag.isHidden() and "border" in d.head.value.styleSheet()
    assert d.command_field.text() == '#var("q_k1", domain: ("snow-load", "SL"))' and d.command_note.text() == b.t("vr_inc_export")
    b.select_key(_export_key("snow-load", "SL", "h_0"))
    assert d.result_tag.isHidden() and "border" not in d.head.value.styleSheet()
    assert d.rows["vr_came_from"][1].text() == b.t("vr_from_woodcore")   # typed in the snow tab (issue #109)
    b.select_key(("formulas", "SL", "q_k1"))
    assert d.command_note.text() == b.t("vr_inc_file", include='#include domain-file("snow-load", "SL")')
    b.select_key(_report("T001", "A"))
    assert d.command_note.text() == b.t("vr_inc_document", document=b.document_name("rs")) and not d.untraced.isHidden()
    b.select_key(_export_key("snow-load", "SL"))
    assert d.command_field.text() == '#include domain-file("snow-load", "SL")'
    domain = b.domains[_export_key("snow-load", "SL")[:2]]
    assert d.rows["vr_its_variables"][1].text() == b.t("vr_domain_counts", count=len(domain.variables), results=len(domain.results))
    assert d.result_tag.isHidden()
    _fill(b, _sample())


# ---------------------------------------------------------------- «Ouvrir l'onglet» (REQ-009)

def _open(b, key):
    b.select_key(key)
    return b.detail.open_button


def test_open_the_tab_brings_the_computing_tab_forward_on_its_case():
    """REQ-009: the snow from the export and from the report, a bending check, a check in the fire situation; Python forward without a case; greyed with its reason for a domain the report declares and a reserved tab."""
    import woodcore_gui
    tab = _tab()
    window = tab.app
    b = tab.service("browser")
    _fill(b, _sample())
    keys = [k for k, _f in woodcore_gui.TABS]
    try:
        for key, expected, case in ((_export_key("snow-load", "SL", "q_k1"), "tab_ac_snow", "SL"), (_report("SL", "q_k1"), "tab_ac_snow", "SL"),
                                    (("formulas", "BI-01", "eta"), "tab_mc_bending", "BI-01"), (("formulas", "FE-01", "eta"), "tab_mc_fire", "FE-01")):
            window.tab_widget.setCurrentWidget(tab)
            button = _open(b, key)
            assert button.isEnabled(), (key, button.toolTip())
            button.click()
            shown = window.tabs[window.tab_widget.currentIndex()]
            assert keys[window.tab_widget.currentIndex()] == expected, (key, keys[window.tab_widget.currentIndex()])
            node = b.assembly.node(b.domains[key[:2]])
            if shown.lists_object(node.split(":", 1)[1]):
                assert shown.current_id == case, (key, shown.current_id)   # the case opened where the tab lists it -- a case read from a workbook is listed by none
            else:
                assert expected.startswith("tab_ac_"), (key, "a check is a case its tab lists")
        window.tab_widget.setCurrentWidget(tab)
        _open(b, _export_key("script", "dreigelenk", "H_d")).click()
        assert keys[window.tab_widget.currentIndex()] == "tab_python"
        window.tab_widget.setCurrentWidget(tab)
        button = _open(b, _report("T001", "A"))
        assert not button.isEnabled() and button.toolTip() == b.t("vr_open_none_tip")
        button = _open(b, _export_key("live-load", "A1", "q_k"))
        assert not button.isEnabled() and button.toolTip() == b.t("open_tab_reserved", tab=b.t("tab_ac_imposed"), document=window.document_name())
    finally:
        window.tab_widget.setCurrentWidget(tab)
        _fill(b, _sample())


def test_the_tab_of_each_domain_is_the_one_whose_lists_object_answers():
    """REQ-001, REQ-009, ARCH-RISK-001: for every domain of the example that has a node, the tab of `Domain.tab` is the one that lists that node -- the tables of variable_calc held to the real tabs."""
    import woodcore_gui
    tab = _tab()
    window = tab.app
    b = tab.service("browser")
    _fill(b, _sample())
    keys = [k for k, _f in woodcore_gui.TABS]
    checked = 0
    for domain in b.domains.values():
        node = b.assembly.node(domain)
        if node is None:
            continue
        kind, ident = node.split(":", 1)
        listing = [keys[i] for i, t in enumerate(window.tabs) if getattr(t, "GRAPH_KIND", None) == kind and t.lists_object(ident)]
        if listing:
            assert domain.tab in listing, (domain.origin, domain.name, domain.tab, listing)
            checked += 1
        else:
            # listed by no tab: a case read from a workbook (no case of Woodcore's), a «Domaines» or a script domain (no GRAPH_KIND, Q-002) -- never a tab of another kind that lists it
            assert not any(getattr(t, "GRAPH_KIND", None) == kind and t.lists_object(ident) for t in window.tabs), (domain.origin, domain.name)
    assert checked >= 15, checked   # the checks, the connector and the polar moment of the example, in their two sources


# ---------------------------------------------------------------- «Choisir pour un champ» (REQ-008)

def test_choosing_for_a_field_offers_one_value_of_what_the_field_takes():
    """REQ-008: a field in kN -- no document's domain, only numbers of its dimension counted, no two values, «Ouvrir l'onglet» greyed; «Importer» gives the key; the choice ended, everything is offered again and the choice of before comes back."""
    import variable_sources
    from domains import links
    tab = _tab()
    window = tab.app
    b = tab.service("browser")
    _fill(b, _sample())
    b.search.setText("q_k")
    rows = _rows(b)
    b.list.gesture(rows[0], 1)
    b.list.gesture(rows[1], 1, ctrl=True)
    before = list(b.selection.chosen)
    b.search.setText("")
    accept = lambda var, domain: variable_sources.linkable(var, domain, "kN", links.ANY)   # noqa: E731
    got = []
    window.tab_widget.setCurrentWidget(window.tabs[0])
    assert window.begin_variable_pick(got.append, "N de ZT-01 [kN]", accept)
    try:
        assert not b.pick_bar.isHidden() and window.picking
        assert not any(k[0] == "rs" for k in _side(b)), "a document's domain is not offered"
        for node, n in b.catalogue.menu_rows("all", accept):
            assert b.menu.item(node.id).text(1) == (str(n) if n else "—")
        keys = _shown(b)
        assert keys and all(accept(b.variable(k), b.domains[k[:2]]) for k in keys)
        b.list.gesture(b.list.list_model.row_of(keys[0]), 1)
        b.list.gesture(b.list.list_model.row_of(keys[1]), 1, ctrl=True)
        assert list(b.selection.chosen) == [keys[1]], "one value"
        assert b.choice_bar.isHidden()
        button = b.detail.open_button
        assert not button.isEnabled() and button.toolTip() == b.t("open_tab_picking", tab=b.t(b.domains[keys[1][:2]].tab), document=window.document_name())
        assert not b.detail.pick_box.isHidden() and b.detail.pick_import.isEnabled()
        b.detail.pick_import.click()
    finally:
        if window.picking:
            b.end_pick(None)
    assert got and got[0] is not None and got[0][:2] == keys[1][:2] and got[0][2].key == keys[1][2]
    assert b.pick_bar.isHidden() and list(b.selection.chosen) == before, "the choice of before is back"
    assert any(k[0] == "rs" for k in _side(b)), "everything is offered again"
    _fill(b, _sample())


# ---------------------------------------------------------------- what the tab kept from before

def test_building_and_showing_the_tab_writes_nothing():
    import variables_tab
    here = conftest.project_copy("vt_readonly")
    _tab()
    before = {str(p.relative_to(here.root)): (p.stat().st_size, p.stat().st_mtime_ns) for p in here.root.rglob("*") if p.is_file()}
    with project.using(here):
        tab = variables_tab.VariablesTab(_WINDOW["window"])
        tab.setParent(_WINDOW["window"])
        tab.on_shown()
        tab.service("browser").search.setText("q")
    after = {str(p.relative_to(here.root)): (p.stat().st_size, p.stat().st_mtime_ns) for p in here.root.rglob("*") if p.is_file()}
    assert after == before


def test_the_tab_reads_on_its_first_showing_and_later_only_when_it_is_free():
    """The rule since v0.110: the first showing reads whatever it costs; a later one only where the PDF already carries the answer."""
    import unittest.mock as mock

    import variables_tab
    _tab()
    tab = variables_tab.VariablesTab(_WINDOW["window"])
    tab.setParent(_WINDOW["window"])   # owned by the window, as a tab always is
    b = tab.service("browser")
    b.readings = {}
    on = mock.patch.object(model, "auto_enabled", return_value=True)
    with on, mock.patch.object(model, "pdf_is_current", return_value=False), mock.patch.object(b, "reload") as spy:
        tab.on_shown()
        assert spy.called and spy.call_args.kwargs.get("automatic") is True, "the first showing did not read"
        spy.reset_mock()
        tab.on_shown()
        tab.on_shown()
        assert not spy.called, "a later showing paid for a compile"
    with on, mock.patch.object(model, "pdf_is_current", return_value=True), mock.patch.object(b, "reload") as spy:
        tab.on_shown()
        assert spy.called, "a PDF exported since was not picked up"


def test_the_export_is_read_again_at_every_showing():
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
    _tab()
    tab = variables_tab.VariablesTab(_WINDOW["window"])
    tab.setParent(_WINDOW["window"])
    with mock.patch.object(model, "is_current", return_value=True), mock.patch.object(tab.service("browser"), "reload") as spy:
        tab.on_shown()
        assert not spy.called, "a reading that still answers was paid for again"


def test_the_tab_keeps_what_it_had_when_a_reading_fails():
    """And says where the failure is: Typst names the file and the line."""
    import unittest.mock as mock

    import variable_sources
    b = _browser()
    _fill(b, _sample())
    before = b.readings["rs"].count
    typst_said = "error: file not found (searched at Images/image.png)\n   ┌─ Sections/005.typ:90:4"
    b.read_failed("rs", model.VariablesError("no", "compile_failed", exit_code=1, output=typst_said))
    try:
        with mock.patch.object(variable_sources, "read_export", return_value=_real_export()):
            b.read_finished()
        assert b.readings["rs"].count == before, "a failed reading threw away the values that were on screen"
        assert b.reload_button.isEnabled()
        assert b.t("vr_err_compile_failed") in _banner(b).text() and "Sections/005.typ:90:4" in _banner(b).text()
        assert _banner(b).property("callout") == "danger" and _banner(b).isVisibleTo(b.ctx.host)
        count = sum(len(d.variables) for d in b.domains.values())
        assert b.t("vr_count", count=count, domains=len(b.domains)) == b.state_label.text()
    finally:
        _fill(b, _sample())


def test_a_file_of_the_export_that_cannot_be_read_is_named_in_the_banner():
    import variable_sources
    b = _browser()
    broken = variable_sources.Export(errors=[model.VariablesError("x", "bad_file", file="connections.json", path="x", field="connections.VU-MP-1: boom")])
    _fill(b, _sample(), broken)
    try:
        assert "connections.json" in _banner(b).text() and "boom" in _banner(b).text()
        assert _banner(b).property("callout") == "danger" and _banner(b).isVisibleTo(b.ctx.host)
        assert set(b.domains) == {_report("T001")[:2], _report("SL")[:2]}
    finally:
        _fill(b, _sample())


def test_a_project_not_exported_says_so():
    import variable_sources
    b = _browser()
    missing = variable_sources.Export(missing=[name for name, _s, _r in variable_sources.FILE_SOURCES])
    _fill(b, None, missing)
    try:
        assert b.t("vr_no_export") in b.empty.text() and b.list.isHidden()
    finally:
        _fill(b, _sample())


def test_a_first_reading_that_fails_leaves_the_bar_saying_so():
    import unittest.mock as mock

    import variable_sources
    b = _browser()
    try:
        _fill(b, None, variable_sources.Export())
        b.read_failed("rs", model.VariablesError("no", "no_typst"))
        with mock.patch.object(variable_sources, "read_export", return_value=variable_sources.Export()):
            b.read_finished()
        assert b.t("vr_err_no_typst") in b.state_label.text() and b.document_name("rs") in b.state_label.text()
        assert _banner(b).isVisibleTo(b.ctx.host) and _banner(b).property("callout") == "danger"
    finally:
        _fill(b, _sample())


def test_every_refusal_the_module_can_raise_has_a_sentence_in_three_languages():
    import variables_words
    codes = set()
    for module in ("variables.py", "variable_sources.py"):
        source = (ROOT / "calc" / module).read_text(encoding="utf-8")
        codes |= set(re.findall(r'VariablesError\(\s*(?:f?"[^"]*"|f?"""|[^,]+?),\s*"([a-z_]+)"', source))
        codes |= set(re.findall(r'"([a-z_]+)"\)\s*from exc', source))
    codes = {c for c in codes if c}
    assert codes and "bad_file" in codes, codes
    for lang, texts in variables_words.STRINGS.items():
        for code in codes:
            assert f"vr_err_{code}" in texts, f"{lang}: no sentence for the refusal {code!r}"


def test_the_tab_speaks_the_window_three_languages_and_marks_no_star():
    """ARCH-006, UI-008: the words in fr/de/en, no ß; the ★ of before gone from the tab's code."""
    import variables_words
    reference = set(variables_words.STRINGS["fr"])
    for lang, texts in variables_words.STRINGS.items():
        assert set(texts) == reference, (lang, reference ^ set(texts))
        for key, text in texts.items():
            assert text.strip(), f"{lang}: {key} is empty"
    assert "ß" not in "".join(variables_words.STRINGS["de"].values())
    for name in ("variables_tab.py", "variables_browser.py", "variables_list.py", "variables_detail.py", "variables_words.py"):
        assert "★" not in (ROOT / "calc" / "tools" / name).read_text(encoding="utf-8"), name


def test_the_tab_carries_its_view_through_a_rebuild():
    """UI-007: the filter, the widths and the choice kept; `source`, `domain`, `name` are the variable chosen; the segment is `origin_filter`."""
    b = _browser()
    _fill(b, _sample())
    try:
        b.choose_menu("g:nav_actions")
        b.choose_source("export")
        b.click_domain(_export_key("snow-load", "SL")[:2])
        b.search.setText("q")
        b.list.header.resizeSection(1, 200)
        b.select_key(_export_key("snow-load", "SL", "q_k1"))
        state = b.state()
        assert (state["source"], state["domain"], state["name"]) == _export_key("snow-load", "SL", "q_k1")
        assert state["origin_filter"] == "export" and state["menu"] == "g:nav_actions" and state["widths"]["symbol"] == 200
        _fill(b, _sample())
        b.restore(state)
        assert b.filter.menu == "g:nav_actions" and b.filter.source == "export" and b.source_switch.current_key() == "export"
        assert b.list.widths()["symbol"] == 200 and b.selected_key() == _export_key("snow-load", "SL", "q_k1")
        assert b.filter.domain == _export_key("snow-load", "SL")[:2]
    finally:
        _fill(b, _sample())


def test_a_view_of_before_is_read_without_harm_and_sets_no_source():
    """UI-007, ARCH-RISK-006: a state of v0.117 -- `provenance`, `all_domains`, a `source` that is an origin -- chooses its variable again and sets no source filter; with no widths, the defaults."""
    import theme
    from variables_list import DEFAULT_WIDTHS, SYMBOL
    b = _browser()
    _fill(b, _sample())
    before = b.splitter.sizes()
    try:
        b.restore({"splitter": [500, 300, 0, 0], "search": "", "unit": None, "provenance": "typst:rs", "all_domains": True,
                   "source": "rs", "domain": "T001", "name": "A", "opened": False})
        assert b.splitter.sizes() == before
        assert b.selected_key() == _report("T001", "A") and b.filter.source == "all"
        assert b.list.widths()["symbol"] == theme.scaled(DEFAULT_WIDTHS[SYMBOL])
        # a view kept while the provenance «Excel» still was (issue #109, UI-003): read without harm
        b.restore({"provenance": "excel", "source": "export", "domain": "snow-load · SL", "name": "h_0"})
        assert b.filter.source == "all"
    finally:
        _fill(b, _sample())


def test_the_panes_sizes_are_no_longer_kept_under_the_view_data():
    """ARCH-RISK-006 (c): with «Données» gone, the window keeps the panes under (tab_variables, -, panes)."""
    tab = _tab()
    assert tab.app.layout_bindings["tab_variables"].key() == ("tab_variables", "-", "panes")


def test_the_tab_edits_nothing():
    """It reads and copies; no unsaved changes, no writer, no `dirty` (what tells an editor from a browser)."""
    import woodcore_gui
    tab = _tab()
    assert not hasattr(tab, "save") and tab.confirm_leave() is True
    for name in woodcore_gui.WRITERS:
        assert not hasattr(tab, name), f"the Variables tab has a writer named {name!r}"
    assert not hasattr(tab, "dirty"), "the Variables tab is a browser: a `dirty` puts it among the editors"
    for browser in ("CommandsTab",):
        other = [t for t in _WINDOW["window"].tabs if type(t).__name__ == browser]
        if other:
            assert not hasattr(other[0], "dirty"), f"{browser} gained a dirty: the convention moved"


def test_a_disabled_reload_button_says_why():
    b = _browser()
    b.set_reading(True)
    try:
        assert not b.reload_button.isEnabled() and b.reload_button.toolTip() == b.t("vr_reading")
    finally:
        b.set_reading(False)
    assert b.reload_button.isEnabled() and b.reload_button.toolTip() == b.t("vr_reload_hint")


def test_the_automatic_reading_is_turned_off_for_the_suite():
    assert not model.auto_enabled(), "conftest no longer turns the automatic reading off"
    import unittest.mock as mock

    import variables_tab
    _tab()
    tab = variables_tab.VariablesTab(_WINDOW["window"])
    tab.setParent(_WINDOW["window"])
    b = tab.service("browser")
    b.readings = {}
    with mock.patch.object(b, "reload") as spy:
        tab.on_shown()
        assert not spy.called, "a suite run paid for a compile by opening a tab"
    with mock.patch.object(model, "auto_enabled", return_value=True), mock.patch.object(b, "reload") as spy:
        b.opened = False
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
    """A relative ordering, not an exact tuple: «Formule» what to write, «Variables» what there is to name, «Commandes» what there is to call."""
    import woodcore_gui
    reference = dict(woodcore_gui.NAV_GROUPS)["nav_reference"]
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


def test_show_tab_opens_the_case_where_the_tab_lists_it():
    """ARCH-010, REQ-009: `show_tab("tab_ac_snow", "load:snow-load/SL")` brings the snow forward and asks it to open `snow-load/SL` -- by the tab's own `open_object`, where its `lists_object` answers. The example's SL is read from the workbook and listed by no tab, so the tab is asked through stand-ins of the two calls it answers."""
    import unittest.mock as mock

    import woodcore_gui
    tab = _tab()
    window = tab.app
    keys = [k for k, _f in woodcore_gui.TABS]
    snow = window.tabs[keys.index("tab_ac_snow")]
    opened = []
    try:
        with mock.patch.object(snow, "lists_object", lambda ident: ident == "snow-load/SL"), mock.patch.object(snow, "open_object", opened.append):
            assert window.show_tab("tab_ac_snow", "load:snow-load/SL")
            assert window.tabs[window.tab_widget.currentIndex()] is snow and opened == ["snow-load/SL"]
            b = tab.service("browser")
            _fill(b, _sample())
            window.tab_widget.setCurrentWidget(tab)
            b.select_key(_report("SL", "q_k1"))   # chosen in the report that recalls it: the export's tab, its case
            b.detail.open_button.click()
            assert window.tabs[window.tab_widget.currentIndex()] is snow and opened[-1] == "snow-load/SL"
    finally:
        window.tab_widget.setCurrentWidget(tab)


def test_leaving_the_tab_waits_for_a_reading_in_its_thread():
    """Issue #106 (REQ-006): the tab's `confirm_leave` is the type's -- the phase `leave`, then True --, and the browser's `leave` waits for a reading in its thread, which cannot be cut short."""
    import tab_frame
    import variables_tab
    tab = _tab()
    assert "confirm_leave" not in vars(variables_tab.VariablesTab) and variables_tab.VariablesTab.confirm_leave is tab_frame.TabFrame.confirm_leave
    b = tab.service("browser")
    waited = []

    class Reader:
        modes = ["rs"]

        def wait(self, ms):
            waited.append(ms)
    b.reader = Reader()
    try:
        assert tab.confirm_leave() is True and len(waited) == 1 and waited[0] > 0
    finally:
        b.reader = None
