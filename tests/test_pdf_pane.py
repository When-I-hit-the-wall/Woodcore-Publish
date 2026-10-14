"""The compiled page of a document beside what it is written from (calc/tools/pdf_pane.py): the centre pane of the «Structure document» tab, phase 2 of the three documents (the engineer's request of 30.09.2026).

What is held here is what the tab will rest on and cannot see for itself: that the pane holds no Windows handle on the PDF it shows -- the next compile writes that very file --; that it gives the PDF's outline as Typst wrote it and scrolls to a heading's page; that it keeps its place when a PDF is shown again; that three saves in a row are one compile and a request made while one runs is not lost; that a compile which fails says Typst's own words and leaves the page as it was; and that «Modifications non compilées» is said exactly while what is shown is not what the sources would give.

The documents compiled here are a project of their own, a few lines of Typst in each, so that no check waits on the example project's report -- which takes seconds a compile -- and none writes into it. The previews are compiled into a folder of the test's own, never into Woodcore's cache.
"""

import ast
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import conftest
from conftest import ROOT, Skip

TOOLS = ROOT / "calc" / "tools"

# A document of four pages whose headings stand where the outline must find them.
OUTLINED = """#set page(width: 10cm, height: 8cm)
= Allgemeines
Text.
== Zweck
Text.
#pagebreak()
= Nutzlasten
#pagebreak()
== Kategorie A
Text.
#heading(outlined: false)[Nicht im Inhalt]
#pagebreak()
= Schluss
"""


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdfWidgets  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdfWidgets is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _wait(app, condition, timeout=60, what="the pane"):
    from PySide6.QtCore import QEventLoop
    end = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > end:
            raise AssertionError(f"{what}: nothing after {timeout} s")
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        time.sleep(0.01)


def _pause(app, seconds):
    from PySide6.QtCore import QEventLoop
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)
        time.sleep(0.01)


def _blank_pdf(path, pages=1):
    from pypdf import PdfWriter
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=283, height=227)
    with open(path, "wb") as handle:
        writer.write(handle)
    return Path(path)


def _typst(source, folder, name="doc"):
    """`source` compiled to a PDF in `folder`, or a Skip where no Typst is installed."""
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    typ = Path(folder) / f"{name}.typ"
    typ.write_text(source, encoding="utf-8")
    pdf = typ.with_suffix(".pdf")
    run = subprocess.run(["typst", "compile", str(typ), str(pdf)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    return pdf


def _tiny(name, body):
    """A project of three documents whose convention d'utilisation is `body` and nothing else: the layout a new project states (documents.layout_for), no engine, no export."""
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    import documents
    import project
    root = conftest.tmpdir(name)
    data = {"schema_version": project.SCHEMA_VERSION, "format": project.FORMAT, "name": "Probe", "layout": documents.layout_for("fr")}
    file = root / "Probe.woodcore"
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    here = project.Project.load(file)
    entry = here.document_typ("cu")
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text(body, encoding="utf-8")
    return here


def _pane(app, name, lang="fr"):
    import pdf_pane
    pane = pdf_pane.PdfPane(lang=lang)
    pane.preview_folder = conftest.tmpdir(name + "-cache")
    pane.resize(420, 340)
    pane.show()
    app.processEvents()
    return pane


def _record(pane):
    """What the pane said, signal by signal."""
    said = {"started": [], "compiled": [], "failed": [], "stale": []}
    pane.started.connect(lambda mode: said["started"].append(mode))
    pane.compiled.connect(lambda mode: said["compiled"].append(mode))
    pane.failed.connect(lambda mode, message: said["failed"].append((mode, message)))
    pane.staleChanged.connect(lambda stale: said["stale"].append(stale))
    return said


# --- the words ---------------------------------------------------------------------------

def test_the_pane_speaks_three_languages_with_its_own_keys():
    _qt()
    import pdf_pane
    reference = set(pdf_pane.STRINGS["fr"])
    for lang in ("fr", "de", "en"):
        assert set(pdf_pane.STRINGS[lang]) == reference, lang
        assert all(key.startswith("pp_") for key in pdf_pane.STRINGS[lang]), lang
    assert pdf_pane.STRINGS["fr"]["pp_stale"] == "Modifications non compilées"
    assert pdf_pane.STRINGS["de"]["pp_stale"] == "Nicht kompilierte Änderungen"
    assert pdf_pane.STRINGS["en"]["pp_stale"] == "Uncompiled changes"
    assert not [k for k, v in pdf_pane.STRINGS["de"].items() if "ß" in v], "Swiss German writes no ß"
    assert not [k for k, v in pdf_pane.STRINGS["fr"].items() if re.search(r"\S:", v)], "French puts a space before its colon"
    for key in reference:   # every hole is the same in the three
        holes = {lang: set(re.findall(r"\{(\w+)\}", pdf_pane.STRINGS[lang][key])) for lang in ("fr", "de", "en")}
        assert holes["fr"] == holes["de"] == holes["en"], (key, holes)


def test_the_pane_writes_no_colour_and_its_banners_are_callouts():
    text = (TOOLS / "pdf_pane.py").read_text(encoding="utf-8")
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", text), "a colour written in pdf_pane.py -- read it from the style sheet's callouts"
    assert 'setProperty("callout", "warning")' in text and 'setProperty("callout", "danger")' in text


def test_the_installed_program_carries_the_pdf_view():
    """Woodcore.exe freezes what calc/ imports from outside itself (packaging/woodcore.spec, `imported()`, which reads every import statement of calc/): QtPdfWidgets reaches it through this module's own import, and PyInstaller's hook for it brings Qt6PdfWidgets.dll with it -- nothing to add to the spec, as long as the import is written where `imported()` reads it."""
    import importlib.util
    spec = (ROOT / "packaging" / "woodcore.spec").read_text(encoding="utf-8")
    assert "hiddenimports=imported()" in spec and 'CALC.rglob("*.py")' in spec, "the spec no longer reads calc/'s imports"
    tree = ast.parse((TOOLS / "pdf_pane.py").read_text(encoding="utf-8"))
    modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level == 0}
    assert "PySide6.QtPdfWidgets" in modules and "PySide6.QtPdf" in modules, modules
    try:
        found = importlib.util.find_spec("PySide6.QtPdfWidgets")
    except ImportError:
        found = None
    if found is None:
        raise Skip("PySide6's QtPdfWidgets is not installed here")


# --- what is shown ---------------------------------------------------------------------------

def test_the_pdf_is_read_into_memory_and_its_file_may_be_replaced_while_it_is_shown():
    """`QPdfDocument.load(path)` keeps a handle on the file, and the next compile -- which writes that very file -- then fails on Windows' sharing error. Read into a QBuffer, the file is closed as soon as it is read."""
    app = _qt()
    folder = conftest.tmpdir("pdf_pane_replace")
    shown = _blank_pdf(folder / "shown.pdf", pages=3)
    other = _blank_pdf(folder / "other.pdf", pages=1)
    pane = _pane(app, "pdf_pane_replace")
    try:
        assert pane.load(shown)
        assert pane.page_count() == 3
        os.replace(other, shown)            # a rename over it, which a held file refuses
        shown.write_bytes(_blank_pdf(folder / "again.pdf", pages=2).read_bytes())
        shown.unlink()
        app.processEvents()
        assert pane.page_count() == 3, "the document shown went with its file"
        assert pane.document.status() == pane.document.Status.Ready
        assert pane.stack.currentWidget() is pane.view
        # bytes handed over as they are: shown the same way, no file behind them
        assert pane.load_bytes(_blank_pdf(folder / "bytes.pdf", pages=2).read_bytes())
        assert pane.page_count() == 2 and pane.showing and pane.shown is None
    finally:
        pane.stop()
        pane.deleteLater()


def test_a_file_that_is_no_pdf_leaves_the_pane_empty():
    app = _qt()
    folder = conftest.tmpdir("pdf_pane_bad")
    bad = folder / "bad.pdf"
    bad.write_bytes(b"not a pdf at all")
    pane = _pane(app, "pdf_pane_bad")
    try:
        assert not pane.load(bad)
        assert not pane.load(folder / "missing.pdf")
        assert pane.page_count() == 0 and pane.bookmarks() == []
        assert pane.stack.currentWidget() is pane.placeholder
        assert pane.placeholder.text() == "Pas encore d'aperçu"
        pane.jump(3)    # nothing to jump in, and nothing raised
    finally:
        pane.stop()
        pane.deleteLater()


def test_the_outline_is_the_pdf_s_own_flattened_in_order():
    app = _qt()
    pdf = _typst(OUTLINED, conftest.tmpdir("pdf_pane_outline"))
    pane = _pane(app, "pdf_pane_outline")
    try:
        assert pane.load(pdf)
        found = pane.bookmarks()
        assert [(b.level, b.title, b.page) for b in found] == [
            (1, "Allgemeines", 0), (2, "Zweck", 0), (1, "Nutzlasten", 1), (2, "Kategorie A", 2), (1, "Schluss", 3),
        ], found
        allgemeines, zweck = found[0], found[1]
        assert 0 < allgemeines.y < zweck.y < 8 / 2.54 * 72, (allgemeines, zweck)
        # shown again, the outline is the new PDF's
        pdf2 = _typst("= Eins\n#pagebreak()\n= Zwei\n", pdf.parent, name="doc2")
        pdf.write_bytes(pdf2.read_bytes())
        assert pane.load(pdf)
        assert [(b.level, b.title, b.page) for b in pane.bookmarks()] == [(1, "Eins", 0), (1, "Zwei", 1)]
    finally:
        pane.stop()
        pane.deleteLater()


def test_jump_scrolls_to_the_page_and_a_pdf_shown_again_keeps_its_place():
    app = _qt()
    pdf = _typst(OUTLINED, conftest.tmpdir("pdf_pane_jump"))
    pane = _pane(app, "pdf_pane_jump")
    try:
        assert pane.load(pdf)
        app.processEvents()
        assert pane.current_page() == 0
        heading = pane.bookmarks()[3]            # Kategorie A
        pane.jump(heading.page, heading.y)
        app.processEvents()
        assert pane.current_page() == 2, pane.current_page()
        place = pane.view.verticalScrollBar().value()
        assert place > 0
        pane.jump(99)                            # held to the pages there are
        app.processEvents()
        assert pane.current_page() == 3
        pane.jump(2)
        app.processEvents()
        place = pane.view.verticalScrollBar().value()
        # the same file shown again -- what a compile does: the place is kept
        assert pane.load(pdf)
        app.processEvents()
        assert pane.current_page() == 2 and pane.view.verticalScrollBar().value() == place
        # a PDF that lost the page it was at: its last
        _blank_pdf(pdf, pages=2)
        assert pane.load(pdf)
        app.processEvents()
        assert pane.page_count() == 2 and pane.current_page() == 1, pane.current_page()
        # another file: from the top
        other = _typst("= Eins\n#pagebreak()\n= Zwei\n#pagebreak()\n= Drei\n", pdf.parent, name="other")
        pane.jump(1)
        assert pane.load(other)
        app.processEvents()
        assert pane.current_page() == 0
    finally:
        pane.stop()
        pane.deleteLater()


# --- compiling ----------------------------------------------------------------------------

def test_three_quick_requests_are_one_compile_and_the_preview_is_shown():
    app = _qt()
    import pdf_pane
    import stamps
    here = _tiny("pdf_pane_debounce", "= Zweck\nText.\n#pagebreak()\n= Nutzlasten\n")
    pane = _pane(app, "pdf_pane_debounce")
    said = _record(pane)
    try:
        pane.set_document(here, "cu")
        assert pane.stack.currentWidget() is pane.placeholder     # nothing compiled yet
        assert pane.timer.interval() == pdf_pane.DEBOUNCE_MS == 800
        for _ in range(3):
            pane.request(here, "cu")
        assert said["started"] == [] and pane.is_pending()        # waiting for the next request
        _wait(app, lambda: said["started"], what="the debounce")
        assert not pane.busy_row.isHidden() and pane.busy_label.text() == "Compilation de l'aperçu…"
        _wait(app, lambda: said["compiled"], what="the compile")
        _pause(app, 1.2)                                           # no second compile follows
        assert said["started"] == ["cu"] and said["compiled"] == ["cu"] and said["failed"] == []
        assert pane.busy_row.isHidden() and not pane.is_pending()
        target = pdf_pane.preview_file(here, "cu", pane.preview_folder)
        assert target.is_file() and Path(pane.shown) == target and pane.shown_preview
        assert not here.document_pdf("cu").exists(), "a preview is compiled beside the deliverable, never over it"
        assert [b.title for b in pane.bookmarks()] == ["Zweck", "Nutzlasten"]
        stamp = stamps.read(here, "cu", preview=True)
        assert stamp is not None and stamp["inputs_from"] == stamps.FROM_DEPS and stamps.read(here, "cu") is None
    finally:
        pane.stop()
        pane.deleteLater()


def test_a_request_made_while_a_compile_runs_is_compiled_after_it_and_only_the_latest():
    app = _qt()
    here = _tiny("pdf_pane_queue", "= Eins\n")
    pane = _pane(app, "pdf_pane_queue")
    said = _record(pane)
    try:
        pane.request(here, "cu")
        pane.compile_now()
        assert said["started"] == ["cu"] and pane.is_busy()
        here.document_typ("cu").write_text("= Eins\n= Zwei\n", encoding="utf-8")
        pane.request()
        pane.compile_now()
        pane.request()                              # the latest: taken in place of the one before it
        pane.compile_now()
        assert said["started"] == ["cu"], "a second compile started beside the first"
        _wait(app, lambda: len(said["compiled"]) == 2, what="the second compile")
        _pause(app, 1.2)
        assert said["started"] == ["cu", "cu"] and said["failed"] == []
        assert [b.title for b in pane.bookmarks()] == ["Eins", "Zwei"]
    finally:
        pane.stop()
        pane.deleteLater()


def test_a_compile_stopped_tells_the_chip_it_is_over():
    """The chip at the top right says «Aperçu Typst» while Typst runs (tasks.activity, REQ-007): `stop` -- the window rebuilt for a language, a tab closed -- kills the compile with no `finished` to follow, and must take the activity back too, or the chip says it for the rest of the session (found by the full suite of 08.10.2026)."""
    app = _qt()
    import tasks
    here = _tiny("pdf_pane_stop_activity", "= Eins\n")
    pane = _pane(app, "pdf_pane_stop_activity")
    try:
        before = list(tasks.activity().keys())
        pane.request(here, "cu")
        pane.compile_now()
        assert pane.is_busy() and tasks.activity().keys() == before + ["activity_preview"]
    finally:
        pane.stop()
        pane.deleteLater()
    assert tasks.activity().keys() == before, "a compile stopped is still said to run"


def test_a_failing_compile_says_typst_s_own_words_and_leaves_the_page_shown():
    app = _qt()
    here = _tiny("pdf_pane_fail", "= Zweck\n#pagebreak()\n= Nutzlasten\n")
    pane = _pane(app, "pdf_pane_fail")
    said = _record(pane)
    try:
        pane.request(here, "cu")
        pane.compile_now()
        _wait(app, lambda: said["compiled"], what="the first compile")
        assert pane.error_banner.isHidden()
        here.document_typ("cu").write_text("= Zweck\n#nicht-definiert-xyz()\n", encoding="utf-8")
        pane.request()
        pane.compile_now()
        _wait(app, lambda: said["failed"], what="the failing compile")
        mode, message = said["failed"][0]
        assert mode == "cu" and "nicht-definiert-xyz" in message and "error" in message.lower(), message
        assert not pane.error_banner.isHidden()
        assert pane.error_banner.text().startswith("La compilation de l'aperçu a échoué :\n")
        assert "nicht-definiert-xyz" in pane.error_banner.text()
        assert pane.page_count() == 2 and pane.stack.currentWidget() is pane.view, "the page shown went with the failure"
        assert pane.busy_row.isHidden() and not pane.is_pending()
        # the stale banner says the page shown is not the sources' any more
        _wait(app, lambda: pane.stale is True, what="the check after the failure")
        assert not pane.stale_banner.isHidden()
        # mended: the banner goes, the new page comes
        here.document_typ("cu").write_text("= Zweck\n", encoding="utf-8")
        pane.request()
        pane.compile_now()
        _wait(app, lambda: len(said["compiled"]) == 2, what="the mended compile")
        assert pane.error_banner.isHidden() and pane.page_count() == 1
        pane.set_language("de")
        assert pane.stale_banner.text() == "Nicht kompilierte Änderungen" and pane.busy_label.text() == "Vorschau wird kompiliert…"
    finally:
        pane.stop()
        pane.deleteLater()


def test_a_typst_that_is_not_there_is_a_failure_and_not_a_hang():
    app = _qt()
    import pdf_pane
    import project
    here = _tiny("pdf_pane_no_typst", "= Eins\n")
    pane = _pane(app, "pdf_pane_no_typst")
    said = _record(pane)
    saved = project.typst_executable
    project.typst_executable = lambda: str(conftest.tmpdir("pdf_pane_no_typst-bin") / "no-typst-here.exe")
    try:
        pane.request(here, "cu")
        pane.compile_now()
        _wait(app, lambda: said["failed"], what="the compile that cannot start")
        assert said["failed"][0][0] == "cu" and said["failed"][0][1]
        assert not pane.is_pending() and not pane.error_banner.isHidden()
    finally:
        project.typst_executable = saved
        pane.stop()
        pane.deleteLater()
    assert pdf_pane.COMPILE_TIMEOUT_MS >= 60_000


def test_the_stale_banner_follows_the_sources_and_the_compile():
    """«Modifications non compilées» exactly while the page shown is not what the document's sources would give: said after a source is edited, gone once the compile of it is shown. Nothing is compiled to find out (stamps.changed)."""
    app = _qt()
    here = _tiny("pdf_pane_stale", "= Zweck\nText.\n")
    pane = _pane(app, "pdf_pane_stale")
    said = _record(pane)
    try:
        pane.request(here, "cu")
        pane.compile_now()
        _wait(app, lambda: said["compiled"], what="the compile")
        _wait(app, lambda: pane.stale is False, what="the check after the compile")
        assert pane.stale_banner.isHidden()
        assert pane.stale_reason.code == "stamp_unchanged"
        # a source edited: said, and why
        time.sleep(0.05)
        here.document_typ("cu").write_text("= Zweck\nAnderer Text.\n", encoding="utf-8")
        pane.check_stale()
        _wait(app, lambda: pane.stale is True, what="the check after the edit")
        assert not pane.stale_banner.isHidden() and pane.stale_banner.text() == "Modifications non compilées"
        assert pane.stale_reason.code == "stamp_input_changed", pane.stale_reason
        assert said["stale"][-1] is True
        # compiled: gone
        pane.request()
        pane.compile_now()
        _wait(app, lambda: len(said["compiled"]) == 2, what="the second compile")
        _wait(app, lambda: pane.stale is False, what="the check after the second compile")
        assert pane.stale_banner.isHidden() and said["stale"][-1] is False
        # the same bytes saved again -- an editor saving without a change, NextCloud setting a time -- change nothing
        entry = here.document_typ("cu")
        time.sleep(0.05)
        entry.write_bytes(entry.read_bytes())
        before = len(said["stale"])
        pane.check_stale()
        _pause(app, 0.1)
        _wait(app, lambda: pane.stale_reason is not None and pane.stale_reason.code == "stamp_unchanged", what="the check after an unchanged save")
        _pause(app, 1.0)
        assert pane.stale is False and pane.stale_banner.isHidden() and len(said["stale"]) == before
        # a pane opened again on the document shows its preview, current
        other = _pane(app, "pdf_pane_stale-2")
        other.preview_folder = pane.preview_folder
        try:
            other.set_document(here, "cu")
            assert other.shown_preview and other.page_count() == 1
            _wait(app, lambda: other.stale is not None, what="the second pane's check")
            assert other.stale is False and other.stale_banner.isHidden()
        finally:
            other.stop()
            other.deleteLater()
    finally:
        pane.stop()
        pane.deleteLater()


def test_until_a_preview_exists_the_document_s_own_pdf_is_shown_and_judged_by_its_own_stamp():
    app = _qt()
    import documents
    import project
    import stamps
    here = _tiny("pdf_pane_own", "= Zweck\n#pagebreak()\n= Nutzlasten\n#pagebreak()\n= Schluss\n")
    deps = stamps.deps_file(here, "cu")
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "cu", deps=deps)], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=here.typst_root)
    assert run.returncode == 0, run.stderr
    stamps.record(here, "cu", [], deps, here.document_pdf("cu"))
    pane = _pane(app, "pdf_pane_own")
    try:
        pane.set_document(here, "cu")
        assert not pane.shown_preview and Path(pane.shown) == here.document_pdf("cu") and pane.page_count() == 3
        _wait(app, lambda: pane.stale is not None, what="the check")
        assert pane.stale is False and pane.stale_banner.isHidden(), pane.stale_reason
        refused = False
        try:
            pane.set_document(here, "nope")
        except project.ProjectError:
            refused = True
        assert refused, "a document the project does not have was shown"
    finally:
        pane.stop()
        pane.deleteLater()


# --- a snippet: the page of a part of a document (the rework of 01.10.2026) -----------------------------------------

def _snippet(heading, body="Text."):
    """The Typst source of a snippet the way calc/structure_preview.py writes one: its own page, as tall as it needs."""
    return f"#set page(width: 10cm, height: auto, margin: 1cm)\n= {heading}\n{body}\n"


def _page_words(pane):
    from pypdf import PdfReader
    return " ".join(page.extract_text() or "" for page in PdfReader(str(pane.shown)).pages)


def test_a_snippet_is_compiled_from_standard_input_shown_in_place_and_leaves_no_record():
    app = _qt()
    import pdf_pane
    import stamps
    here = _tiny("pdf_pane_snippet", "= Dokument\nText.\n")
    pane = _pane(app, "pdf_pane_snippet")
    said = _record(pane)
    keys = []
    pane.snippetCompiled.connect(keys.append)
    try:
        pane.request(here, "cu")
        pane.compile_now()
        _wait(app, lambda: said["compiled"], what="the document's compile")
        stamp = stamps.read(here, "cu", preview=True)
        document = Path(pane.shown)
        assert pane.shown_snippet is None and "Dokument" in _page_words(pane)
        pane.request_snippet(here, "cu", _snippet("Zweck"), "k1")
        assert pane.is_pending() and not said["started"][1:], "a snippet is compiled a moment from now, not at once"
        assert pane.snippet_timer.interval() == pdf_pane.SNIPPET_DEBOUNCE_MS < pdf_pane.DEBOUNCE_MS
        _wait(app, lambda: pane.shown_snippet == "k1", what="the snippet")
        target = pdf_pane.snippet_file(here, "cu", pane.preview_folder)
        assert Path(pane.shown) == target and target.is_file() and target != document and keys == ["k1"]
        words = _page_words(pane)
        assert "Zweck" in words and "Dokument" not in words, words
        from pypdf import PdfReader
        assert float(PdfReader(str(target)).pages[0].mediabox.height) < 200, "a snippet's page is as tall as it needs"
        assert said["failed"] == [] and pane.error_banner.isHidden() and not pane.is_pending()
        assert stamps.read(here, "cu", preview=True) == stamp, "a snippet writes no stamp: it is compiled from the sources as they are"
        assert not list(here.root.rglob("*.pdf")), "a preview is never written into the project"
        # the document's own page comes back, and where nothing was compiled for it, the pane says so
        pane.show_document()
        assert pane.shown_snippet is None and Path(pane.shown) == document and "Dokument" in _page_words(pane)
    finally:
        pane.stop()
        pane.deleteLater()


def test_a_pane_of_snippets_only_never_shows_the_document_s_own_pdf():
    """Issue #21: the «Affichage» view's pane loaded the report's own PDF -- its title page -- while its first snippet compiled, and again at every leaving of the view. A pane of snippets only shows the placeholder until its snippet, keeps that snippet when the view is left, and never loads the document."""
    app = _qt()
    import documents
    import pdf_pane
    import project
    here = _tiny("pdf_pane_snippets_only", "= Titelseite\n")
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "cu")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    own = here.document_pdf("cu")
    assert own.is_file()
    pane = pdf_pane.PdfPane(lang="fr", snippets_only=True)
    pane.preview_folder = conftest.tmpdir("pdf_pane_snippets_only-cache")
    pane.resize(420, 340)
    pane.show()
    loaded = []
    original = pane.load
    pane.load = lambda path, keep_place=None: (loaded.append(Path(path)), original(path, keep_place=keep_place))[1]
    try:
        pane.set_document(here, "cu")
        assert not pane.showing and pane.stack.currentWidget() is pane.placeholder, "nothing before the first snippet"
        pane.request_snippet(here, "cu", _snippet("Zweck"), "k1")
        assert not pane.showing, "the document is not shown while the snippet compiles"
        _wait(app, lambda: pane.shown_snippet == "k1", what="the snippet")
        pane.show_document()          # the tab leaves «Affichage»
        assert pane.shown_snippet == "k1" and pane.showing, "the last snippet stays: the document never comes back in its place"
        pane.request_snippet(here, "cu", _snippet("Nutzlasten"), "k2")
        _wait(app, lambda: pane.shown_snippet == "k2", what="the second snippet")
        assert own not in loaded, f"the document's own PDF was loaded: {loaded}"
        assert "Titelseite" not in _page_words(pane)
    finally:
        pane.stop()
        pane.deleteLater()
    # the Structure tab's pane, built without the flag, still shows the document until a preview exists
    plain = _pane(app, "pdf_pane_snippets_only_plain")
    try:
        plain.set_document(here, "cu")
        assert Path(plain.shown) == own
    finally:
        plain.stop()
        plain.deleteLater()


def test_three_quick_snippets_are_one_compile_and_the_latest_wins_while_one_runs_it_is_not_lost():
    app = _qt()
    here = _tiny("pdf_pane_snippet_queue", "= Dokument\n")
    pane = _pane(app, "pdf_pane_snippet_queue")
    said = _record(pane)
    keys = []
    pane.snippetCompiled.connect(keys.append)
    try:
        pane.set_document(here, "cu")
        for key, heading in (("a", "Aaa"), ("b", "Bbb"), ("c", "Ccc")):
            pane.request_snippet(here, "cu", _snippet(heading), key)
        assert said["started"] == []
        _wait(app, lambda: pane.shown_snippet == "c", what="the debounce and the compile")
        _pause(app, 0.8)
        assert said["started"] == ["cu"] and keys == ["c"] and "Ccc" in _page_words(pane)
        # one asked for while another runs waits for it, and the one it replaces is never shown
        keys.clear()
        pane.request_snippet(here, "cu", _snippet("Ddd"), "d")
        pane.compile_now()
        assert pane.is_busy() and said["started"] == ["cu", "cu"]
        pane.request_snippet(here, "cu", _snippet("Eee"), "e")
        pane.compile_now()
        assert said["started"] == ["cu", "cu"], "a second Typst started beside the first"
        _wait(app, lambda: pane.shown_snippet == "e" and not pane.is_pending(), what="the latest")
        assert said["started"] == ["cu", "cu", "cu"] and keys == ["e"] and "Eee" in _page_words(pane)
        assert said["failed"] == []
    finally:
        pane.stop()
        pane.deleteLater()


def test_a_snippet_asked_for_while_the_document_compiles_ends_that_compile_without_a_failure():
    app = _qt()
    here = _tiny("pdf_pane_snippet_kill", "= Dokument\n" + "Text.\n" * 20)
    pane = _pane(app, "pdf_pane_snippet_kill")
    said = _record(pane)
    try:
        pane.request(here, "cu")
        pane.compile_now()
        assert pane.is_busy() and said["started"] == ["cu"]
        pane.request_snippet(here, "cu", _snippet("Zweck"), "k")
        _wait(app, lambda: pane.shown_snippet == "k" and not pane.is_pending(), what="the snippet after the document's compile")
        assert said["failed"] == [], "a compile ended on purpose is no failure"
        assert pane.error_banner.isHidden() and "Zweck" in _page_words(pane)
        assert not pane.killed
    finally:
        pane.stop()
        pane.deleteLater()


def test_a_failing_snippet_says_typst_s_own_words_and_leaves_the_page_shown_and_a_mended_one_clears_them():
    app = _qt()
    here = _tiny("pdf_pane_snippet_fail", "= Dokument\n")
    pane = _pane(app, "pdf_pane_snippet_fail")
    said = _record(pane)
    try:
        pane.set_document(here, "cu")
        pane.request_snippet(here, "cu", _snippet("Gut"), "good")
        _wait(app, lambda: pane.shown_snippet == "good", what="the first snippet")
        assert pane.error_banner.isHidden()
        pane.request_snippet(here, "cu", _snippet("Schlecht", "#nicht-definiert-xyz()"), "bad")
        _wait(app, lambda: said["failed"], what="the failing snippet")
        mode, message = said["failed"][0]
        assert mode == "cu" and "nicht-definiert-xyz" in message and "error" in message.lower(), message
        assert not pane.error_banner.isHidden() and "nicht-definiert-xyz" in pane.error_banner.text()
        assert pane.shown_snippet == "good" and "Gut" in _page_words(pane), "the page shown went with the failure"
        assert not pane.is_pending()
        pane.request_snippet(here, "cu", _snippet("Besser"), "better")
        _wait(app, lambda: pane.shown_snippet == "better", what="the mended snippet")
        assert pane.error_banner.isHidden() and "Besser" in _page_words(pane)
    finally:
        pane.stop()
        pane.deleteLater()


def test_a_snippet_is_never_stale_and_the_document_asked_for_again_gives_the_page_back():
    app = _qt()
    here = _tiny("pdf_pane_snippet_stale", "= Dokument\n")
    pane = _pane(app, "pdf_pane_snippet_stale")
    said = _record(pane)
    try:
        pane.request(here, "cu")
        pane.compile_now()
        _wait(app, lambda: said["compiled"], what="the document's compile")
        pane.request_snippet(here, "cu", _snippet("Zweck"), "k")
        _wait(app, lambda: pane.shown_snippet == "k", what="the snippet")
        said_before = list(said["stale"])
        here.document_typ("cu").write_text("= Dokument\n= Neu\n", encoding="utf-8")
        pane.check_stale()
        _pause(app, 0.6)
        assert pane.stale_banner.isHidden() and said["stale"] == said_before, ("a snippet is compiled from the sources as they are", said["stale"])
        # the document asked for again takes the snippet's place when it is compiled
        pane.request(here, "cu")
        pane.compile_now()
        _wait(app, lambda: len(said["compiled"]) == 2, what="the document's second compile")
        assert pane.shown_snippet is None and "Neu" in _page_words(pane)
        # a snippet asked for and then given up is not shown
        pane.request_snippet(here, "cu", _snippet("Weg"), "gone")
        pane.show_document()
        _pause(app, 1.0)
        assert pane.shown_snippet is None and "Weg" not in _page_words(pane) and not pane.is_pending()
    finally:
        pane.stop()
        pane.deleteLater()


# --- the view -----------------------------------------------------------------------------------

def test_the_view_has_one_width_whether_the_page_is_taller_than_the_pane_or_not():
    """Fitted to the width, a page just taller than the pane brought the vertical bar, which narrowed the view, which shrank the page to fit again, which took the bar away: the page, rendered at each width in turn, showed blank (a chapter's snippet of the «Structure du document» tab, 01.10.2026). The bar is always there, so the width does not depend on the page."""
    app = _qt()
    from pypdf import PdfWriter
    from PySide6.QtCore import Qt

    def pdf_of(name, height):
        writer = PdfWriter()
        writer.add_blank_page(width=283, height=height)
        path = conftest.tmpdir("pdf_pane_width") / f"{name}.pdf"
        with open(path, "wb") as handle:
            writer.write(handle)
        return path

    pane = _pane(app, "pdf_pane_width")
    try:
        assert pane.view.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        widths = []
        for name, height in (("short", 60), ("tall", 1200), ("borderline", 330), ("short-again", 60)):
            assert pane.load(pdf_of(name, height))
            _pause(app, 0.15)
            widths.append(pane.view.viewport().width())
        assert len(set(widths)) == 1, widths
    finally:
        pane.stop()
        pane.deleteLater()
