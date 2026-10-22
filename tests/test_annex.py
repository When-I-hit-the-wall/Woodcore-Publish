"""The annexes (docs/domain/annexes.md §3.3undevicies, v0.115): the documents a report draws on from outside -- a FEM program's print report first -- and the excerpts it shows of them.

What is held, and against what:

* **The anchor is a bookmark.** The engineer's own RFEM export draws its headings as vector paths and carries no text for them, but one bookmark per heading with the page and the height (measured, calc/domains/annex.py). The fixture, tests/fixtures/annex_pdf.py, carries exactly that and nothing else.
* **A new version is followed**: the fixture's version 2 has a chapter added in front, every heading renumbered, one page more and the moments' diagram moved to another page and height -- an excerpt placed on version 1 must find it there, its frame at the same place under its title.
* **A title used twice** («Charges de barre», once under each load case) is told apart by its path.
* **What cannot be found is refused**, with a reason the report prints (the engineer's answer C9), and a source without bookmarks is followed by nothing -- its excerpts refused until confirmed again.
* **The page is cropped by the export**, never by Typst, which draws a page made of clipped tiles wrongly away from the origin; and the PDF the export writes declares 1.7, Typst refusing a PDF 2.0 -- which is what RFEM writes -- in a report exported as 1.7.
"""

import io
import json
import shutil
import subprocess
import sys

import conftest
from conftest import ROOT, Skip

import project
import validation
from domains import annex

sys.path.insert(0, str(ROOT / "tests"))
from fixtures import annex_pdf  # noqa: E402


def _pdf(version=1, bookmarks=True):
    from pypdf import PdfReader
    return PdfReader(io.BytesIO(annex_pdf.build(version, bookmarks)))


def _excerpt(eid, anchor, frame=None, source="Rapport", **extra):
    return {"schema_version": "1.0", "id": eid, "name": eid, "label": "", "source": source,
            "anchor": anchor, "frame": frame or {"x": 50, "y": -4, "w": 495, "h": 258}, **extra}


def _mark(pdf, key):
    return next(m for m in annex.outline(pdf) if m["key"] == key)


# --- the outline ------------------------------------------------------------------------

def test_a_title_is_compared_without_its_chapter_number():
    """A print report renumbers its chapters as soon as one is added -- «5.16» was «6.4» in the engineer's previous version of the same report -- so the number is left out, and nothing else of the title."""
    assert annex.title_key("5.16 CO1: Efforts internes M_y , En direction -Y") == "co1: efforts internes m_y, en direction -y"
    assert annex.title_key("6.4 CO1: Efforts internes M_y, En direction -Y") == annex.title_key("5.16 CO1: Efforts internes M_y , En direction -Y")
    assert annex.title_key("3.1.1 Charges de barre") == "charges de barre"
    assert annex.title_key("A Modèle - Position") == "modèle - position"
    # a title that opens on something else than a chapter keeps it: «CO1» is part of the title
    assert annex.title_key("CO1 - Avec neige") == "co1 - avec neige"
    assert annex.title_key("5.4") == "5.4", "a title that is nothing but a number is kept"


def test_the_outline_gives_every_bookmark_its_page_its_height_and_its_path():
    marks = annex.outline(_pdf(1))
    assert len(marks) == 9
    moments = next(m for m in marks if m["key"] == "co1: efforts internes m_y")
    assert (moments["page"], moments["top"]) == (3, 440.0)
    assert moments["keys"] == ["résultats", "co1: efforts internes m_y"]
    assert annex.outline(_pdf(1, bookmarks=False)) == []


def test_a_click_names_the_bookmark_standing_just_above_it():
    marks = annex.outline(_pdf(1))
    # the title of the moments is drawn under its bookmark at 440 pt: a click on it, or anywhere down its diagram, names it
    assert annex.bookmark_at(marks, 3, 452)["key"] == "co1: efforts internes m_y"
    assert annex.bookmark_at(marks, 3, 600)["key"] == "co1: efforts internes m_y"
    assert annex.bookmark_at(marks, 3, 200)["key"] == "co1: efforts internes n"
    assert annex.bookmark_at(marks, 3, 30) is None, "above the first bookmark of the page there is nothing to name"


def test_a_title_used_twice_is_told_apart_by_its_path():
    marks = annex.outline(_pdf(1))
    both = [m for m in marks if m["key"] == "charges de barre"]
    assert len(both) == 2
    anchors = [annex.anchor_for(marks, m) for m in both]
    assert all(a["occurrence"] == 1 for a in anchors), "the path alone tells them apart"
    found = [annex.candidates(marks, [annex.title_key(t) for t in a["path"]]) for a in anchors]
    assert [f[0]["top"] for f in found] == [130.0, 450.0]
    # only the title given, both are candidates, and the rank is what tells them apart
    assert len(annex.candidates(marks, ["charges de barre"])) == 2


# --- where an excerpt lies ------------------------------------------------------------------

def test_an_excerpt_follows_the_next_version_of_its_source():
    """Placed on version 1, found in version 2: renumbered, one page more, and the diagram on another page at another height -- the frame keeps its place under its title."""
    v1, v2 = _pdf(1), _pdf(2)
    ex = _excerpt("My", annex.anchor_for(annex.outline(v1), _mark(v1, "co1: efforts internes m_y")))
    first, second = annex.resolve(ex, v1, "a"), annex.resolve(ex, v2, "b")
    assert first["ok"] and second["ok"]
    assert (first["page"], first["rect"][1]) == (3, 436.0)
    assert (second["page"], second["rect"][1]) == (5, 146.0)
    assert second["title"] == "3.2 CO1: Efforts internes M_y"
    assert first["rect"][2:] == second["rect"][2:] == [495, 258]


def test_a_title_that_is_gone_is_refused_with_its_reason():
    v1 = _pdf(1)
    ex = _excerpt("X", {"kind": "bookmark", "path": ["9 Résultats", "9.9 CO7: Efforts internes N"], "occurrence": 1})
    where = annex.resolve(ex, v1, "a")
    assert not where["ok"] and where["note"].code == "annex_not_found"
    assert "CO7" in str(where["note"])
    twice = _excerpt("Y", {"kind": "bookmark", "path": ["Charges de barre"], "occurrence": 3})
    where = annex.resolve(twice, v1, "a")
    assert where["note"].code == "annex_occurrence" and where["note"].args["count"] == 2


def test_a_source_without_bookmarks_follows_nothing_and_asks_to_be_confirmed():
    printed = _pdf(1, bookmarks=False)
    by_title = _excerpt("T", {"kind": "bookmark", "path": ["2.2 CO1: Efforts internes M_y"]})
    assert annex.resolve(by_title, printed, "sha")["note"].code == "annex_no_bookmarks"
    by_page = _excerpt("P", {"kind": "page", "page": 3}, frame={"x": 50, "y": 436, "w": 495, "h": 258}, confirmed="sha")
    assert annex.resolve(by_page, printed, "sha")["ok"]
    replaced = annex.resolve(by_page, printed, "another")
    assert not replaced["ok"] and replaced["note"].code == "annex_unconfirmed"
    gone = _excerpt("G", {"kind": "page", "page": 9}, confirmed="sha")
    assert annex.resolve(gone, printed, "sha")["note"].code == "annex_page_gone"


def test_a_frame_running_past_its_page_is_refused():
    v1 = _pdf(1)
    anchor = annex.anchor_for(annex.outline(v1), _mark(v1, "co1: efforts internes m_y"))
    tall = _excerpt("T", anchor, frame={"x": 50, "y": 0, "w": 495, "h": 600})
    assert annex.resolve(tall, v1, "a")["note"].code == "annex_outside"


def test_the_export_crops_the_page_and_declares_pdf_1_7():
    """The page IS the frame -- its MediaBox and CropBox moved onto it -- so Typst sets it at the origin; and it declares 1.7 whatever its source declared, RFEM writing 2.0."""
    from pypdf import PdfReader
    v1 = _pdf(1)
    data = annex.crop(v1, 3, [50, 436.0, 495, 258])
    assert data.startswith(b"%PDF-1.7")
    page = PdfReader(io.BytesIO(data)).pages[0]
    height = annex_pdf.HEIGHT
    assert [round(float(v), 2) for v in page.mediabox] == [50.0, round(height - 436 - 258, 2), 545.0, round(height - 436, 2)]
    assert [round(float(v), 2) for v in page.cropbox] == [round(float(v), 2) for v in page.mediabox]
    assert annex.pages_of(v1, [1, 3]).startswith(b"%PDF-1.7")


# --- the sources' checks ---------------------------------------------------------------------

def test_a_source_and_an_excerpt_are_checked():
    good = annex.new_source("Rapport", "Rapport", "", "r.pdf")
    annex.check_source(good, "Rapport.json")
    for bad, words in ((dict(good, id="-x"), "id"), (dict(good, mode="some"), "mode")):
        try:
            annex.check_source(bad, "x.json")
        except validation.ValidationError as exc:
            assert words in str(exc)
        else:
            raise AssertionError(f"{bad} was accepted")
    ok = _excerpt("E", {"kind": "bookmark", "path": ["T"], "occurrence": 1})
    annex.check_excerpt(ok, "E.json")
    for bad in (dict(ok, frame={"x": 0, "y": 0, "w": 2, "h": 50}),
                dict(ok, anchor={"kind": "bookmark", "path": []}),
                dict(ok, anchor={"kind": "page"}),
                dict(ok, anchor={"kind": "text"})):
        try:
            annex.check_excerpt(bad, "E.json")
        except validation.ValidationError:
            pass
        else:
            raise AssertionError(f"{bad} was accepted")


def test_an_unresolved_excerpt_that_says_nothing_is_refused_by_the_export_rules():
    data = annex.empty()
    data["excerpts"]["E"] = {"name": "", "label": "", "source": "R", "resolved": False, "reason": "",
                             "page": None, "title": "", "file": "", "size": None, "rect": None}
    try:
        validation.validate_annexes_business(data)
    except validation.ValidationError as exc:
        assert "nothing says why" in str(exc)
    else:
        raise AssertionError("an unresolved excerpt with no reason passed")


# --- the export --------------------------------------------------------------------------

def _project_with(name, versions=1, bookmarks=True):
    """A copy of the project the tests work on, carrying one source (the fixture) and two excerpts on it."""
    copied = conftest.project_copy(name)
    with project.using(copied):
        here = project.current()
        # emptied file by file: the folders copied from a project in OneDrive carry its read-only attribute, which a removal of the folder itself stops on
        for folder in (annex.sources_dir(here), annex.excerpts_dir(here)):
            folder.mkdir(parents=True, exist_ok=True)
            for old in folder.iterdir():
                if old.is_file():
                    old.unlink()
        path = annex_pdf.write(annex.pdf_path(here, "Rapport"), versions, bookmarks)
        source = annex.new_source("Rapport", "Rapport EF", "", "r.pdf")
        source["sha256"] = annex.file_hash(path)
        annex.write_source(here, source)
        pdf = annex.reader(path)
        marks = annex.outline(pdf)
        for eid, key in (("My", "co1: efforts internes m_y"), ("N", "co1: efforts internes n")):
            if marks:
                anchor = annex.anchor_for(marks, next(m for m in marks if m["key"] == key))
                annex.write_excerpt(here, _excerpt(eid, anchor))
    return copied


def test_the_export_writes_every_excerpt_and_the_pages_its_source_carries():
    here = _project_with("annex_export")
    with project.using(here):
        assert annex.export(here) == []
        data = json.loads((here.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
        validation.validate_structure(data, "annexes")
        assert data["excerpts"]["My"]["resolved"] and data["excerpts"]["My"]["page"] == 3
        assert data["sources"]["Rapport"]["annex"]["pages"] == [3], "used: the pages an excerpt is taken from, and only those"
        excerpts = here.exports_dir("annex")   # Appendix/Exports/, the project being laid out by folders (issue #64, D-19)
        files = sorted(p.name for p in excerpts.iterdir())
        assert files == ["My.pdf", "N.pdf", "Rapport-annex.pdf"]
        # every page, then none
        for mode, pages in (("all", [1, 2, 3]), ("none", None)):
            source = annex.read_source(annex.sources_dir(here) / "Rapport.json")
            annex.write_source(here, dict(source, mode=mode))
            annex.export(here)
            data = json.loads((here.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
            got = data["sources"]["Rapport"]["annex"]
            assert (got["pages"] if got else None) == pages, mode
        assert "Rapport-annex.pdf" not in [p.name for p in excerpts.iterdir()], "a file no longer needed is swept"


def test_a_new_version_of_the_source_is_followed_by_the_export():
    here = _project_with("annex_new_version")
    with project.using(here):
        annex.export(here)
        annex_pdf.write(annex.pdf_path(here, "Rapport"), 2)
        assert annex.export(here) == []
        data = json.loads((here.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
        assert data["excerpts"]["My"]["page"] == 5 and data["excerpts"]["My"]["title"].startswith("3.2 ")
        assert data["sources"]["Rapport"]["annex"]["pages"] == [4, 5]


def test_an_unchanged_excerpt_is_not_written_again():
    here = _project_with("annex_kept")
    with project.using(here):
        annex.export(here)
        target = here.exports_dir("annex") / "My.pdf"
        target.write_bytes(target.read_bytes() + b"%kept\n")   # a byte that proves the file was kept rather than rewritten
        annex.export(here)
        assert target.read_bytes().endswith(b"%kept\n")


def test_what_cannot_be_found_is_a_warning_at_the_export_and_a_reason_in_the_record():
    here = _project_with("annex_missing")
    with project.using(here):
        annex.write_excerpt(here, _excerpt("Gone", {"kind": "bookmark", "path": ["CO9: Efforts"], "occurrence": 1}))
        annex.write_excerpt(here, _excerpt("Orphan", {"kind": "bookmark", "path": ["X"], "occurrence": 1}, source="Nobody"))
        notes = annex.export(here)
        assert sorted(n.code for n in notes) == ["annex_not_found", "annex_source_gone"]
        data = json.loads((here.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
        assert not data["excerpts"]["Gone"]["resolved"] and "CO9" in data["excerpts"]["Gone"]["reason"]


def test_a_new_project_has_an_empty_export_of_its_annexes():
    import export_all
    copied = conftest.project_copy("annex_seed", data=False)
    written = export_all.seed(copied)
    assert annex.EXPORT_FILE in written
    assert json.loads((copied.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8")) == annex.empty()


def test_the_annexes_folder_is_a_source_folder():
    """So the archive of every export holds the PDFs, and a new project and a test's copy have the folder."""
    assert "annexes" in project.SOURCE_FOLDERS
    assert project.current().annexes_dir == project.current().sources_dir / "annexes"


# --- the report ----------------------------------------------------------------------------

def _compile(name, body, pages=False):
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    folder = conftest.probe_dir(name)
    source = folder / f"{name}.typ"
    source.write_text('#import "/000-Typst-Config/commands.typ": *\n#report-level.update(2)\n#set page(paper: "a4")\n' + body, encoding="utf-8")
    out = folder / f"{name}.pdf"
    run = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(source), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return run, out


def test_an_excerpt_is_a_figure_linked_to_its_annex_page_and_back():
    from pypdf import PdfReader
    run, out = _compile("annex_links", '#figure(image-extract("CO1-My"), kind: image, caption: [Biegemomente unter CO1])\n#pagebreak()\n= Anhänge\n#show-annexes()\n')
    assert run.returncode == 0, run.stderr
    reader = PdfReader(str(out))
    text = reader.pages[0].extract_text()
    assert "Biegemomente unter CO1" in text, "the figure's caption is the document's own (spec 2026-10-21-commandes-typst-refonte, REQ-014)"
    ids = {p.indirect_reference.idnum: i for i, p in enumerate(reader.pages)}

    def targets(page):
        found = []
        for a in page.get("/Annots", []):
            a = a.get_object()
            dest = a.get("/Dest") or a.get("/A", {}).get("/D")
            if a.get("/Subtype") == "/Link" and dest is not None and not isinstance(dest, str):
                found.append(ids.get(dest[0].idnum))
        return found

    last = len(reader.pages) - 1
    assert last in targets(reader.pages[0]), "the excerpt does not lead to its annex page"
    assert 0 in targets(reader.pages[last]), "the annex page's frame does not lead back to the excerpt"
    size = [round(float(v)) for v in reader.pages[last].mediabox[2:]]
    assert size == [595, 842], "the annex page is not printed at its own size"


def test_an_annex_page_the_report_shows_no_excerpt_of_is_left_out():
    run, out = _compile("annex_none", '= Anhänge\n#show-annexes()\n')
    assert run.returncode == 0, run.stderr
    from pypdf import PdfReader
    assert len(PdfReader(str(out)).pages) == 1, "a source whose excerpts the report does not show carries no page"


def test_an_excerpt_the_export_could_not_find_stops_the_report_with_its_reason():
    here = project.current()
    path = here.data_dir / annex.EXPORT_FILE
    before = path.read_bytes()
    try:
        data = json.loads(before)
        data["excerpts"]["CO1-My"].update(resolved=False, reason="its source no longer has the title «CO1»", file="")
        path.write_text(json.dumps(data), encoding="utf-8")
        run, _out = _compile("annex_refused", '#image-extract("CO1-My")\n')
        assert run.returncode != 0
        assert "no longer has the title" in (conftest.panic_message(run.stderr) or run.stderr)
    finally:
        path.write_bytes(before)
    run, _out = _compile("annex_unknown", '#image-extract("Nope")\n')
    # an unknown id is refused by an assert, whose message is on the error line itself and not a panic's
    assert run.returncode != 0 and "valid excerpts: CO1-My" in run.stderr, run.stderr


# --- the tab -------------------------------------------------------------------------------

def _tab(copied):
    import os
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    app = QApplication.instance() or QApplication([])
    import woodcore_gui
    window = woodcore_gui.MainWindow()
    tab = next(t for t in window.tabs if type(t).__name__ == "AnnexTab")
    return app, window, tab


def test_the_tab_sits_in_the_project_group_of_all_three_documents_and_lists_its_two_folders():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        import woodcore_gui
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    # the engineer's place for it (06.10.2026): the «Projet» group, after the journal, and in the convention, the base and the report alike
    assert "tab_annexes" in dict(woodcore_gui.NAV_GROUPS)["nav_project"]
    for mode in ("cu", "bp", "rs"):
        assert "tab_annexes" in woodcore_gui.mode_tabs(mode), mode
    assert woodcore_gui.WRITERS.count("add_annex_source") == 1 and "replace_annex_source" in woodcore_gui.WRITERS
    # WRITERS is applied by method NAME to every editor tab: a name another tab uses for something else would refuse it in a read-only project -- «replace_source» is the plan's and the static models' undo/redo helper, which must keep working there
    assert "replace_source" not in woodcore_gui.WRITERS and "add_source" not in woodcore_gui.WRITERS
    import annex_tab
    others = [cls for cls in (woodcore_gui.plan_tab.PlanTab, woodcore_gui.positions_tab.PositionsTab, woodcore_gui.journal_tab.JournalTab, woodcore_gui.python_tab.PythonTab,
                              woodcore_gui.statics_tab.StaticsTab, woodcore_gui.schema_tab.SchemaTab, woodcore_gui.connectors_tab.ConnectorsTab, woodcore_gui.PolarTab)]
    for name in ("add_annex_source", "replace_annex_source"):
        assert name in vars(annex_tab.AnnexTab) and not any(name in vars(cls) for cls in others), name
    copied = _project_with("annex_tab_list")
    with project.using(copied):
        app, window, tab = _tab(copied)
        try:
            folders = [tab.list.topLevelItem(i).text(0) for i in range(tab.list.topLevelItemCount())]
            assert folders == [tab.t("ax_sources"), tab.t("ax_excerpts")]
            assert sorted(key for _item, key in tab.list.rows()) == [("excerpt", "My"), ("excerpt", "N"), ("source", "Rapport")]
        finally:
            tab.dirty = False
            conftest.dispose(window)
def test_an_excerpt_is_made_by_a_click_on_its_title_and_a_drag_over_the_page():
    from PySide6.QtWidgets import QMessageBox
    copied = _project_with("annex_tab_make")
    with project.using(copied):
        app, window, tab = _tab(copied)
        warn = QMessageBox.warning
        QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
        try:
            tab.load("source", "Rapport")
            assert tab.new()
            assert not tab.save(), "an excerpt with no title and no frame is not written"
            tab.page_spin.setValue(3)
            tab.on_page_click(100, 452)
            assert tab.draft["anchor"]["path"][-1] == "2.2 CO1: Efforts internes M_y"
            tab.on_page_drag(50, 436, 495, 258)
            assert tab.draft["frame"] == {"x": 50, "y": -4, "w": 495, "h": 258}, "the frame is kept relative to its title"
            tab.excerpt_identity.name.setText("Moments neu")
            assert tab.save()
            saved = annex.read_excerpt(annex.excerpts_dir(copied) / "Moments_neu.json")
            assert saved["source"] == "Rapport" and saved["frame"]["y"] == -4
            data = json.loads((copied.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
            assert data["excerpts"]["Moments_neu"]["resolved"], "saving exports the annexes"
        finally:
            QMessageBox.warning = warn
            tab.dirty = False
            conftest.dispose(window)
def test_replacing_the_pdf_says_how_many_excerpts_were_found_again():
    copied = _project_with("annex_tab_replace")
    with project.using(copied):
        app, window, tab = _tab(copied)
        try:
            tab.load("source", "Rapport")
            v2 = conftest.tmpdir("annex_v2") / "v2.pdf"
            annex_pdf.write(v2, 2)
            assert tab.replace_with(v2, ask=False)
            data = json.loads((copied.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
            assert data["excerpts"]["My"]["page"] == 5
            assert annex.read_source(annex.sources_dir(copied) / "Rapport.json")["original"] == "v2.pdf"
        finally:
            tab.dirty = False
            conftest.dispose(window)


# --- three ways to extract (issue #16) ------------------------------------------------------

def test_the_frames_drawn_in_a_page_are_found_however_they_are_drawn():
    """REQ-007 (D-007, pypdf alone): a `re` under a matrix, four sides closed by `h`, a filled rectangle inside a form and its `/Matrix`, a form that calls itself followed once -- and never a clip, a curve, a rectangle too small or the page's own ground; in points from the top-left corner, the smallest first."""
    from pypdf import PdfReader
    pdf = PdfReader(io.BytesIO(annex_pdf.build_frames()))
    top = annex_pdf.HEIGHT
    found = annex.find_rects(pdf, 1)
    expected = [[400.0, round(top - 640, 2), 60.0, 40.0], [300.0, round(top - 360, 2), 80.0, 60.0],
                [50.0, round(top - 110, 2), 100.0, 60.0], [100.0, round(top - 580, 2), 120.0, 80.0]]
    assert found == expected, found
    assert annex.find_rects_in(annex_pdf.build_frames(), 1) == found, "the same off the window's thread, from the bytes"
    # the RFEM-like report: its two diagrams' boxes under their titles, at 1 pt
    boxes = annex.find_rects(_pdf(), 3)
    for down in (100, 440):
        wanted = [60.0, down + annex_pdf.BOX_GAP, 470.0, annex_pdf.BOX_HEIGHT]
        assert any(all(abs(a - b) <= 1 for a, b in zip(box, wanted)) for box in boxes), (wanted, boxes)
    # under a point: every frame that holds it, the smallest first
    assert annex.rects_at([[10, 10, 20, 20], [0, 0, 100, 100], [200, 200, 5, 5]], 15, 15) == [[10, 10, 20, 20], [0, 0, 100, 100]]


def test_a_frame_drawn_anchors_on_the_title_above_it_or_on_its_page():
    """REQ-005, REQ-006: a frame drawn with nothing chosen before it is anchored on the lowest bookmark of its page above its top, measured from it; on its page, confirmed, where no bookmark stands above -- and a page whole is a page-anchored excerpt framed by the page."""
    pdf = _pdf()
    marks = annex.outline(pdf)
    made = annex.frame_excerpt(marks, 3, [50, 436, 495, 258], "SHA")
    assert made["anchor"]["path"][-1] == "2.2 CO1: Efforts internes M_y" and made["frame"] == {"x": 50.0, "y": -4.0, "w": 495.0, "h": 258.0} and "confirmed" not in made
    assert annex.excerpt_name(marks, made, "p.") == "CO1: Efforts internes M_y", "the title without its chapter number"
    above = annex.frame_excerpt(marks, 1, [10, 20, 100, 100], "SHA")   # above the cover's only title
    assert above["anchor"] == {"kind": "page", "page": 1} and above["confirmed"] == "SHA" and above["frame"]["y"] == 20.0
    assert annex.excerpt_name(marks, above, "p.") == "p. 1"
    whole = annex.page_excerpt(pdf, 2, "SHA")
    assert whole["anchor"] == {"kind": "page", "page": 2} and whole["frame"]["x"] == 0 and abs(whole["frame"]["w"] - annex_pdf.WIDTH) < 0.1
    excerpt = _excerpt("P2", whole["anchor"], whole["frame"], confirmed="SHA")
    annex.check_excerpt(excerpt, "P2.json")
    assert annex.resolve(excerpt, pdf, "SHA", marks)["ok"], "a page whole resolves on its page"
    assert annex.free_id("Rapport-p. 2", ["Rapport-p.-2"]) == "Rapport-p.-2-2" and annex.free_id("---", []) == "Annexe"


def test_the_tab_extracts_by_frame_by_pages_and_by_frame_found():
    """UI-008, UI-009, REQ-005 to REQ-007 in the tab: the source's pages all laid out -- three or more side by side zoomed out --; «Extraire» and its three modes; a frame drawn, a range of two pages and a frame found each written as excerpts, checked and exported once."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QMessageBox
    import annex_tab
    copied = _project_with("annex_tab_extract")
    with project.using(copied):
        app, window, tab = _tab(copied)
        warn = QMessageBox.warning
        QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
        try:
            window.resize(1500, 900)
            window.show()
            window.tab_widget.setCurrentWidget(tab)
            tab.load("source", "Rapport")
            app.processEvents()
            view = tab.view
            assert view.doc is not None and len(view.rects) == 3, "every page of the source laid out"
            view.set_zoom(view.min_zoom())
            app.processEvents()
            assert view.pages_per_row() >= 3, f"zoomed out, {view.pages_per_row()} page(s) a row"
            assert set(tab.mode_buttons) == {"frame", "pages", "found"} and tab.mode == "frame"
            # «Cadre»: a frame drawn on page 3, under «M_y»
            before = set(tab.excerpts)
            view.page = 3
            view.modifiers = Qt.KeyboardModifier.NoModifier
            tab.on_page_drag(50, 436, 495, 258)
            made = set(tab.excerpts) - before
            assert len(made) == 1, made
            new = tab.excerpts[made.pop()]
            assert new["source"] == "Rapport" and new["anchor"]["path"][-1] == "2.2 CO1: Efforts internes M_y" and new["frame"]["y"] == -4
            # «Pages»: pages 1 to 2, each its own excerpt
            tab.mode_buttons["pages"].setChecked(True)
            tab.load("source", "Rapport")
            tab.from_spin.setValue(1)
            tab.to_spin.setValue(2)
            before = set(tab.excerpts)
            assert tab.extract_annex_pages()
            made = sorted(set(tab.excerpts) - before)
            assert len(made) == 2 and {tab.excerpts[e]["anchor"]["page"] for e in made} == {1, 2}, made
            data = json.loads((copied.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
            assert all(data["excerpts"][e]["resolved"] for e in made), "written, exported, and found"
            # «Cadre trouvé»: the frames of page 2 found, the one under the pointer clicked
            tab.mode_buttons["found"].setChecked(True)
            tab.load("source", "Rapport")
            tab.page_spin.setValue(2)
            rects = annex.find_rects(tab.pdf_of("Rapport").reader, 2)
            tab.on_found(tab.view.doc.sha, 2, rects)
            view.page = 2
            view.hover = (2, annex.rects_at(rects, 100, 200))
            assert view.hover[1], "a frame under the point"
            before = set(tab.excerpts)
            tab.on_page_click(100, 200)
            made = set(tab.excerpts) - before
            assert len(made) == 1 and tab.excerpts[made.pop()]["anchor"]["path"][-1] == "1.1.1 Charges de barre"
            for key in ("ax_extract", "ax_mode_frame", "ax_mode_pages", "ax_mode_found", "ax_extract_pages", "ax_found_pick"):
                assert all(key in annex_tab.STRINGS[lang] for lang in ("fr", "de", "en")), key
        finally:
            QMessageBox.warning = warn
            tab.dirty = False
            window.close()


def test_a_project_opened_read_only_refuses_every_way_of_extracting():
    """Review ARCH-RISK-007: the three ways write excerpts, and are guarded by name like every other writer of the tab in a project opened read-only."""
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        import woodcore_gui
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    import annex_tab
    for name in ("extract_annex_pages", "extract_annex_rects", "write_extracted"):
        assert woodcore_gui.WRITERS.count(name) == 1 and name in vars(annex_tab.AnnexTab), name


# --- Appendix/: the annexes' PDFs under their own names (issue #64, D-11, D-19) ------------------

def test_laid_out_by_folders_a_pdf_added_lies_in_appendix_under_its_own_name_and_its_excerpts_in_its_exports():
    """REQ-009: the PDF copied into Appendix/ as the engineer named it, the record at 1.1 naming it; the export's excerpts and annex in Appendix/Exports/, named from the Typst root; a 1.0 record is read with its PDF beside it."""
    here = _project_with("annex_appendix")
    with project.using(here):
        assert here.has_folders
        legacy = annex.pdf_path(here, "Rapport")
        assert legacy == annex.sources_dir(here) / "Rapport.pdf", "a 1.0 record finds its PDF beside it"
        chosen = conftest.tmpdir("annex_chosen") / "Rapport EF v1.pdf"
        shutil.copyfile(legacy, chosen)
        legacy.unlink()
        source = annex.copy_pdf(here, annex.read_source(annex.sources_dir(here) / "Rapport.json"), chosen)
        annex.write_source(here, source)
        record = json.loads((annex.sources_dir(here) / "Rapport.json").read_text(encoding="utf-8"))
        assert record["schema_version"] == "1.1" and record["file"] == "Rapport EF v1.pdf" and record["original"] == "Rapport EF v1.pdf"
        assert annex.pdf_path(here, "Rapport") == here.typst_root / "Appendix" / "Rapport EF v1.pdf"
        assert annex.export(here) == []
        data = json.loads((here.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.1" and data["excerpts"]["My"]["file"] == "/Appendix/Exports/My.pdf"
        assert sorted(p.name for p in here.exports_dir("annex").iterdir()) == ["My.pdf", "N.pdf", "Rapport-annex.pdf"]
        assert not (here.data_dir / annex.EXPORT_FOLDER).exists(), "data/ keeps the JSON alone"
        # a second source whose file has the same name gets its id's
        other = annex.copy_pdf(here, annex.new_source("Zweit", "Zweit"), chosen)
        assert other["file"] == "Zweit.pdf"


def test_a_pdf_written_over_in_appendix_is_read_again_and_its_excerpts_followed():
    """D-11: a new version written over the PDF of the same name from outside Woodcore -- its SHA-256 brought up to date and said, every excerpt looked for in it at the export."""
    here = _project_with("annex_written_over")
    with project.using(here):
        assert [r.name for r, _made in annex.adopt(here)] == ["Rapport.json"], "a source added before is adopted into Appendix/"
        assert annex.adopt(here) == [], "adopting twice copies nothing"
        assert annex.refresh_sources(here) == ([], [])
        annex.export(here)
        annex_pdf.write(annex.pdf_path(here, "Rapport"), 2)
        changed, notes = annex.refresh_sources(here)
        assert changed == ["Rapport"] and [n.code for n in notes] == ["annex_pdf_replaced"]
        assert annex.read_source(annex.sources_dir(here) / "Rapport.json")["sha256"] == annex.file_hash(annex.pdf_path(here, "Rapport"))
        annex.export(here)
        data = json.loads((here.data_dir / annex.EXPORT_FILE).read_text(encoding="utf-8"))
        assert data["excerpts"]["My"]["page"] == 5 and data["sources"]["Rapport"]["annex"]["pages"] == [4, 5]


def test_a_pdf_written_over_in_appendix_is_read_again_as_the_tab_is_shown_and_not_read_only():
    """Issue #64, D-11: the «Annexes» tab shown reads a PDF written over in Appendix/ again (`write_refresh_sources`, one of WRITERS) -- except in a project open read-only, where showing a tab writes nothing."""
    copied = _project_with("annex_tab_refresh")
    with project.using(copied):
        annex.adopt(copied)
        app, window, tab = _tab(copied)
        try:
            import woodcore_gui
            assert "write_refresh_sources" in woodcore_gui.WRITERS and "write_refresh_documents" in woodcore_gui.WRITERS
            record = annex.sources_dir(copied) / "Rapport.json"
            annex_pdf.write(annex.pdf_path(copied, "Rapport"), 2)
            fresh = annex.file_hash(annex.pdf_path(copied, "Rapport"))
            window.read_only = True
            tab.on_shown()
            assert annex.read_source(record)["sha256"] != fresh, "read-only: nothing written"
            window.read_only = False
            tab.on_shown()
            assert annex.read_source(record)["sha256"] == fresh
        finally:
            window.read_only = False
            tab.dirty = False
            conftest.dispose(window)
