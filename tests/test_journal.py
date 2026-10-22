"""The report's revision journal (calc/journal.py, lib/calc-engine.typ, calc/tools/journal_tab.py, docs/domain/journal.md §3.3terdecies, v0.99).

What is held here: a source checked, an index taken refused, a date that is not a day refused; the export **newest first**, which is the promise `show-journal` and the PDF's keywords rest on; a project with no journal exported as an empty one and never as an error; the three forms compiled and read back at the three levels; the engineer's own words never sent through the glossary; the PDF's keywords naming the latest revision, and a record written before v0.99 still compiling; the tab driven off-screen -- an entry added, changed and deleted, each read back from the file -- a project opened read-only writing nothing, and the tab's words in three languages.

⚠️ The window is built off-screen on a copy of the example project (conftest.project_copy), whose journal is written here rather than copied: `project_copy` copies the SOURCE FOLDERS, and a journal is one file beside them. The message boxes are stubbed -- a modal off-screen never comes back.
"""

import contextlib
import json
import os
import subprocess
import sys

import conftest
from conftest import ROOT, Skip

import journal
import project
import validation

_STATE = {}

ENTRIES = [
    {"index": 1, "date": "2026-09-14", "name": "Max Muster", "initials": "MMB", "label": "Erstausgabe",
     "summary": "Erste Ausgabe des Berichts.", "description": "Positionen, Lastannahmen und statische Systeme."},
    {"index": 2, "date": "2026-09-21", "name": "Max Muster", "initials": "MMB", "label": "Schneelast nachgerechnet",
     "summary": "Bezugshöhe korrigiert.", "description": "Die Bezugshöhe war 200 m zu tief angesetzt."},
    {"index": 3, "date": "2026-09-25", "name": "Petra Prüfer", "initials": "PPA", "label": "Prüfung",
     "summary": "Bemerkungen eingearbeitet.", "description": ""},
]


def _source(entries=None):
    return {"schema_version": journal.SOURCE_SCHEMA_VERSION, "entries": [dict(e) for e in (entries if entries is not None else ENTRIES)]}


def _refused(entries, what):
    """journal.check_source refuses `entries`, and the message names `what`."""
    try:
        journal.check_source(_source(entries), "journal.json")
    except validation.ValidationError as exc:
        assert what in str(exc), f"refused, but for another reason: {exc}"
        return str(exc)
    raise AssertionError(f"a journal with {what} was accepted")


# --- the source ------------------------------------------------------------------------------

def test_a_journal_is_checked_field_by_field():
    journal.check_source(_source(), "journal.json")   # the good one passes
    _refused([dict(ENTRIES[0], index=0)], "1 or more")
    # an index of another type is refused one layer earlier, by the schema walker -- a bool being an int to Python is exactly what it guards (validation._check_type)
    _refused([dict(ENTRIES[0], index=1.5)], "expected integer")
    _refused([dict(ENTRIES[0], index=True)], "expected integer")
    _refused([dict(ENTRIES[0], date="27.09.2026")], "ISO")
    _refused([dict(ENTRIES[0], date="2026-02-30")], "ISO")     # a shape that reads and a day that does not exist
    _refused([dict(ENTRIES[0], name="  ")], "name must not be empty")
    _refused([dict(ENTRIES[0], initials="")], "initials must not be empty")
    _refused([dict(ENTRIES[0], initials="Muster Ingenieure AG")], "at most")
    _refused([dict(ENTRIES[0], label="")], "label must not be empty")
    _refused([{"date": "2026-09-14", "name": "M", "initials": "M", "label": "L"}], "missing required field 'index'")
    # the two descriptions are the ones an entry may leave out
    journal.check_source(_source([{k: v for k, v in ENTRIES[0].items() if k not in ("summary", "description")}]), "journal.json")


def test_two_entries_of_one_number_are_refused_naming_both():
    """«Rev. 3» printed twice, and a reader could not say which revision the report is at. The number is also what the journal is ordered by, so a duplicate would make the order depend on the file's own order."""
    message = _refused(ENTRIES + [dict(ENTRIES[0], label="Nochmals")], "index 1")
    assert "Erstausgabe" in message, message


def test_a_gap_in_the_numbers_is_never_refilled():
    """`next_index` is the largest plus one, as a revision block numbers on paper and as positions_workbook.propose_id numbers a position: Rev. 2 deleted out of 1, 2, 3 leaves 2 unused. The newest deleted gives its number back, which is right for one typed by mistake and taken out at once."""
    assert journal.next_index(_source([])) == 1
    assert journal.next_index(_source()) == 4
    assert journal.next_index(_source([e for e in ENTRIES if e["index"] != 2])) == 4, "a gap was refilled"
    assert journal.next_index(_source([e for e in ENTRIES if e["index"] != 3])) == 3, "the newest deleted did not give its number back"
    assert journal.next_index(_source([dict(ENTRIES[0], index=9)])) == 10


# --- the export ------------------------------------------------------------------------------

def test_the_export_is_newest_first_and_says_so():
    """The order is the export's promise: show-journal prints what it is given and never sorts, and journal.latest -- what the PDF's keywords name -- is simply the first entry."""
    data, notes = journal.prepare(_write_journal(conftest.tmpdir("journal_order") / "journal.json", _source([ENTRIES[1], ENTRIES[0], ENTRIES[2]])))
    assert notes == []
    assert [e["index"] for e in data["entries"]] == [3, 2, 1]
    assert journal.latest(data)["label"] == "Prüfung"
    # every field present, the descriptions "" where the entry has none
    assert set(data["entries"][0]) == set(journal.FIELDS)
    assert data["entries"][0]["description"] == ""


def test_the_export_refuses_a_journal_written_the_other_way_round():
    """validate_journal_business holds the order rather than trusting it: an export written oldest first would print the first revision as the current one."""
    data = {"schema_version": journal.EXPORT_SCHEMA_VERSION, "entries": [journal.record(e) for e in ENTRIES]}
    try:
        validation.validate_journal_business(data)
    except validation.ValidationError as exc:
        assert "newest first" in str(exc), exc
    else:
        raise AssertionError("an export written oldest first was accepted")


def test_a_project_with_no_journal_exports_an_empty_one():
    """A project that has never been revised is a journal with nothing in it -- never an error, the way a project with no load workbook is a warning (v0.89.1)."""
    missing = conftest.tmpdir("journal_missing") / "journal.json"
    data, notes = journal.prepare(missing)
    assert data == {"schema_version": journal.EXPORT_SCHEMA_VERSION, "entries": []} and notes == []
    assert journal.latest(data) is None
    validation.validate_structure(data, "journal")
    validation.validate_journal_business(data)


def test_the_export_writes_the_latest_revision_into_the_projects_record():
    """The PDF's keywords name it (woodcore-document), and it is passed to project.record rather than read there -- project.py knows nothing of the journal, and `seed()` writes a record without one."""
    here = conftest.project_copy("journal_record")
    with project.using(here):
        data, _notes = journal.prepare(_write_journal(here.journal_file, _source()))
        info = project.record(here, revision=journal.latest(data))
        assert info["revision"] == {"index": 3, "date": "2026-09-25", "label": "Prüfung", "initials": "PPA"}
        validation.validate_structure(info, "project")
        # a project with no revision writes no field at all, so a record of an older version is the same record
        assert "revision" not in project.record(here)
        validation.validate_structure(project.record(here), "project")


def test_the_export_seeds_a_journal_a_new_projects_report_can_read():
    """Sections/008-journal.typ reads data/journal.json at every compile, so a project made this morning must have one (export_all.seed, v0.86.1's rule)."""
    import export_all
    here = conftest.project_copy("journal_seed", data=False)
    with project.using(here):
        written = export_all.seed(here)
        assert journal.EXPORT_FILE in written, written
        data = json.loads((here.data_dir / journal.EXPORT_FILE).read_text(encoding="utf-8"))
        assert data["entries"] == []
        (here.data_dir / journal.EXPORT_FILE).write_text(json.dumps({"schema_version": "1.0", "entries": [journal.record(ENTRIES[0])]}), encoding="utf-8")
        assert journal.EXPORT_FILE not in export_all.seed(here), "seeding twice overwrote a journal that was there"


def _write_journal(path, source):
    journal.write_source(path, source)
    return path


# --- what the report prints --------------------------------------------------------------------

def _probe(name, body, lang="de"):
    """One .typ compiled against the project the tests work on, its text read back."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    folder = conftest.probe_dir(name)
    source = folder / f"{name}.typ"
    source.write_text(
        '#import "/000-Typst-Config/commands.typ": *\n'
        '#set page(width: 18cm, height: auto, margin: 1cm)\n'
        '#number-digits.update(3)\n'
        f'#set-report-language("{lang}")\n' + body,
        encoding="utf-8")
    out = folder / f"{name}.txt"
    run = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(source), str(out), "--format", "html", "--features", "html"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if run.returncode != 0:
        return None, run.stderr
    return out.read_text(encoding="utf-8"), ""


def _pdf_text(name, body, lang="de"):
    """The same probe compiled to a PDF and read back as text -- `show-journal` uses `layout`, which the HTML export does not run."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise Skip(f"pypdf is not installed ({exc})")
    folder = conftest.probe_dir(name)
    source = folder / f"{name}.typ"
    source.write_text(
        '#import "/000-Typst-Config/commands.typ": *\n'
        '#set page(width: 18cm, height: auto, margin: 1cm)\n'
        '#number-digits.update(3)\n'
        f'#set-report-language("{lang}")\n' + body,
        encoding="utf-8")
    out = folder / f"{name}.pdf"
    run = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(source), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if run.returncode != 0:
        return None, run.stderr
    return "\n".join(page.extract_text() for page in PdfReader(str(out)).pages), ""


@contextlib.contextmanager
def _exported(entries):
    """The project the tests work on carrying `entries` in its data/journal.json, put back afterwards."""
    here = project.current()
    path = here.data_dir / journal.EXPORT_FILE
    before = path.read_bytes() if path.exists() else None
    data = {"schema_version": journal.EXPORT_SCHEMA_VERSION, "entries": [journal.record(e) for e in journal.entries({"entries": entries})]}
    validation.validate_journal_business(data)
    journal.write(data, here.data_dir)
    try:
        yield
    finally:
        if before is None:
            path.unlink()
        else:
            path.write_bytes(before)


def test_journal_entries_reads_the_export_newest_first():
    with _exported(ENTRIES):
        text, error = _probe("journal_access", "#journal-entries().map(e => str(e.index)).join(\"-\")\n")
        assert text is not None, error
        assert "3-2-1" in text, text


def test_the_pdf_keywords_name_the_latest_revision():
    """And a project record written before v0.99, which carries no `revision`, still compiles: `woodcore-document` reads it with a default, because a `set document` rule cannot ask whether a second file is there."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise Skip(f"pypdf is not installed ({exc})")
    here = project.current()
    record = here.data_dir / "project.json"
    before = record.read_bytes()
    folder = conftest.probe_dir("journal_keywords")
    try:
        for revision, wanted in (({"index": 3, "date": "2026-09-25", "label": "Prüfung", "initials": "PPA"}, "Rev. 3 (2026-09-25)"), (None, None)):
            info = json.loads(before.decode("utf-8"))
            info.pop("revision", None)
            if revision is not None:
                info["revision"] = revision
            record.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            source = folder / "keywords.typ"
            source.write_text('#import "/000-Typst-Config/commands.typ": *\n#show: woodcore-document\nEin Bericht.\n', encoding="utf-8")
            out = folder / "keywords.pdf"
            run = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(source), str(out)],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert run.returncode == 0, run.stderr
            keywords = PdfReader(str(out)).metadata.get("/Keywords", "")
            if wanted is None:
                assert "Rev." not in keywords, keywords
            else:
                assert wanted in keywords, keywords
    finally:
        record.write_bytes(before)


# --- one journal per document (the convention d'utilisation, the base de projet, the statical report) -------

CU_ENTRIES = [
    {"index": 1, "date": "2026-09-28", "name": "Anna Nutzer", "initials": "ANU", "label": "Nutzungsentwurf",
     "summary": "Nutzlasten und Nutzungsdauer vereinbart.", "description": "Nur die Nutzungsvereinbarung."},
    {"index": 2, "date": "2026-09-29", "name": "Petra Prüfer", "initials": "PPA", "label": "Nutzung bestätigt",
     "summary": "Bauherr hat unterschrieben.", "description": ""},
]
BP_ENTRIES = [
    {"index": 1, "date": "2026-09-30", "name": "Bruno Basis", "initials": "BBA", "label": "Projektbasisentwurf",
     "summary": "Normen und Materialien festgelegt.", "description": ""},
]
RS_LABELS = ("Erstausgabe", "Schneelast nachgerechnet", "Prüfung")
CU_LABELS = ("Nutzungsentwurf", "Nutzung bestätigt")


@contextlib.contextmanager
def _journals(**by_document):
    """The project the tests work on carrying a journal per document in its data/: `rs=ENTRIES, cu=CU_ENTRIES` writes data/journal.json and data/journal-cu.json, `bp=None` takes data/journal-bp.json away -- whatever was there is put back afterwards.

    The Python side that writes `data/journal-cu.json` and `data/journal-bp.json` is another package's (calc/journal.py, at the export); what is held here is what the **engine** reads, so the files are written the way the export writes one -- `journal.record` for every entry, newest first, the shape `validation.validate_journal_business` holds.
    """
    here = project.current()
    names = {"rs": "journal.json", "cu": "journal-cu.json", "bp": "journal-bp.json"}
    before = {}
    try:
        for document, entries in by_document.items():
            path = here.data_dir / names[document]
            before[document] = path.read_bytes() if path.exists() else None
            if entries is None:
                if path.exists():
                    path.unlink()
                continue
            data = {"schema_version": journal.EXPORT_SCHEMA_VERSION, "entries": [journal.record(e) for e in journal.entries({"entries": entries})]}
            validation.validate_journal_business(data)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        yield
    finally:
        for document, content in before.items():
            path = here.data_dir / names[document]
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(content)


def _compile(name, body, lang="de"):
    """One .typ compiled to a PDF against the project the tests work on, at a fixed creation time so that two compiles of the same text are the same bytes: `(pdf path, stderr)`, the path None where the compile failed."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    folder = conftest.probe_dir(name)
    source = folder / f"{name}.typ"
    source.write_text(
        '#import "/000-Typst-Config/commands.typ": *\n'
        '#set page(width: 18cm, height: auto, margin: 1cm)\n'
        '#number-digits.update(3)\n'
        f'#set-report-language("{lang}")\n' + body,
        encoding="utf-8")
    out = folder / f"{name}.pdf"
    run = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(source), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace",
                         env={**os.environ, "SOURCE_DATE_EPOCH": "1700000000"})
    return (out if run.returncode == 0 else None), run.stderr


def _text_and_keywords(pdf):
    """The text of a PDF and its keywords. A narrow prose column of the journal's table is hyphenated (show-journal), and the soft hyphen and the line break it leaves would cut a word a test looks for in two."""
    import re
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    text = "\n".join(page.extract_text() for page in reader.pages)
    return re.sub("\u00ad\\s*", "", text), reader.metadata.get("/Keywords", "")


def _need_pypdf():
    try:
        import pypdf  # noqa: F401
    except ImportError as exc:
        raise Skip(f"pypdf is not installed ({exc})")


def test_the_pdf_keywords_of_a_convention_name_its_own_latest_revision():
    """For «cu» and «bp» the revision comes from data/journal-<document>.json, not from project.json: that file is the statical report's, and a revision of the convention written into it would make the statical report look changed -- and be compiled again -- every time the convention is revised. So the two documents of one project carry two different «Rev.» in their own properties."""
    _need_pypdf()
    here = project.current()
    record = here.data_dir / "project.json"
    before = record.read_bytes()
    try:
        info = json.loads(before.decode("utf-8"))
        info["revision"] = {"index": 3, "date": "2026-09-25", "label": "Prüfung", "initials": "PPA"}
        record.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with _journals(rs=ENTRIES, cu=CU_ENTRIES, bp=BP_ENTRIES):
            keywords = {}
            for document in ("rs", "cu", "bp"):
                pdf, error = _compile(f"journal_kw_{document}", f'#show: woodcore-document.with(document: "{document}")\nEin Dokument.\n')
                assert pdf is not None, error
                keywords[document] = _text_and_keywords(pdf)[1]
            assert "Rev. 3 (2026-09-25)" in keywords["rs"], keywords
            assert "Rev. 2 (2026-09-29)" in keywords["cu"] and "Rev. 3" not in keywords["cu"], keywords
            assert "Rev. 1 (2026-09-30)" in keywords["bp"], keywords
            # the program and Typst are still named, for every document
            assert all("Woodcore" in k and "Typst" in k for k in keywords.values()), keywords
        # a convention whose journal has nothing in it carries no revision, as a project record with none does -- it is not an error
        with _journals(cu=[]):
            pdf, error = _compile("journal_kw_cu_empty", '#show: woodcore-document.with(document: "cu")\nEin Dokument.\n')
            assert pdf is not None, error
            assert "Rev." not in _text_and_keywords(pdf)[1]
    finally:
        record.write_bytes(before)


def test_journal_entries_defaults_to_the_statical_report_and_follows_the_document_on_request():
    """`journal-entries` returns an array, so it cannot ask a state and works outside a `context`: its default is «rs» -- what it always read -- and `document:` names another, or `auto` the document being compiled, which only a `context` can tell."""
    with _journals(rs=ENTRIES, cu=CU_ENTRIES):
        pdf, error = _compile("journal_entries_docs", "\n".join((
            '#show: woodcore-document.with(document: "cu")',
            '#let ids(es) = es.map(e => str(e.index)).join("-")',
            '#ids(journal-entries()) \\',                                   # outside a context: the statical report's, 3-2-1
            '#ids(journal-entries(document: "cu")) \\',                     # named: the convention's, 2-1
            '#context ids(journal-entries(document: auto)) \\',             # the document being compiled: the convention's
            '#context ids(journal-entries())',                              # the default does not follow the state
            "")))
        assert pdf is not None, error
        lines = [l.strip() for l in _text_and_keywords(pdf)[0].splitlines() if l.strip()]
        assert lines == ["3-2-1", "2-1", "2-1", "3-2-1"], lines


def test_a_document_the_project_has_no_journal_for_is_refused_listing_the_ones_it_has():
    with _journals(rs=ENTRIES):
        pdf, error = _compile("journal_bad_document", '#show: woodcore-document.with(document: "xx")\nx\n')
        assert pdf is None
        assert "no document" in error and "rs, cu, bp" in error, error
        pdf, error = _compile("journal_bad_entries", '#journal-entries(document: "zz").len()\n')
        assert pdf is None
        assert "no journal for the document" in error and "rs, cu, bp" in error, error
        pdf, error = _compile("journal_bad_type", "#journal-entries(document: 3).len()\n")
        assert pdf is None and "no journal for the document" in error, error


def test_a_convention_with_no_exported_journal_stops_naming_the_file():
    """The one limit of reading a journal for the PDF's keywords, and a documented one: Typst cannot ask whether a file is there, so the export must always write `data/journal-cu.json` and `data/journal-bp.json` (`export_all.seed` seeds every document's journal, as it has seeded `journal.json` since v0.99). A project whose export never ran stops on the missing file, **naming it** -- which is the message a person can act on -- and the statical report, which reads `project.json`, is unaffected."""
    with _journals(rs=ENTRIES, bp=None):
        pdf, error = _compile("journal_bp_missing", '#show: woodcore-document.with(document: "bp")\nx\n')
        assert pdf is None
        assert "journal-bp.json" in error and "file not found" in error, error
        pdf, error = _compile("journal_rs_without_bp", "#show: woodcore-document\nx\n")
        assert pdf is not None, error


def test_the_journal_files_the_engine_reads_are_the_ones_the_export_writes():
    """`journal-files` in lib/calc-engine.typ names the file each document's journal is exported to. Held against the Python side: the statical report's is `journal.EXPORT_FILE`, and once `calc/documents.py` exists its `JOURNAL_FILES` is the whole table -- two lists of three file names that agree by being held equal, not by being remembered."""
    import re
    source = conftest.engine_source()
    found = re.search(r"#let journal-files = \(([^)]*)\)", source)
    assert found, "the table of journal files is gone from lib/calc-engine.typ"
    table = dict(re.findall(r'(\w+): "([^"]+)"', found.group(1)))
    assert table == {"rs": journal.EXPORT_FILE, "cu": "journal-cu.json", "bp": "journal-bp.json"}, table
    try:
        import documents
    except ImportError:
        return
    if hasattr(documents, "JOURNAL_FILES"):
        assert table == dict(documents.JOURNAL_FILES), (table, documents.JOURNAL_FILES)


# --- the tab ------------------------------------------------------------------------------------

def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    """One window on one copy of the example project, for the whole file. Its journal is written here: project_copy copies the source FOLDERS, and a journal is one file beside them."""
    if "window" not in _STATE:
        _qt()
        here = conftest.project_copy("journal_tab")
        journal.write_source(here.journal_file, _source())
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            # A window opens on the convention d'utilisation where the user's settings keep no document for the project (01.10.2026), whose journal is not the report's -- the file this one writes. The report is put in front, as the window of tests/test_modes_window.py is.
            window.mode = "rs"
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window):
    import journal_tab
    return next(t for t in window.tabs if isinstance(t, journal_tab.JournalTab))


@contextlib.contextmanager
def _boxes(question=None):
    from PySide6.QtWidgets import QMessageBox
    shown = []

    def ask(_parent, _title, text, *args, **kwargs):
        shown.append(text)
        return question(text) if question else QMessageBox.StandardButton.Yes

    def warn(_parent, _title, text, *args, **kwargs):
        shown.append(text)
        return QMessageBox.StandardButton.Ok

    saved = {name: QMessageBox.__dict__[name] for name in ("question", "warning", "information")}
    QMessageBox.question = staticmethod(ask)
    QMessageBox.warning = staticmethod(warn)
    QMessageBox.information = staticmethod(warn)
    try:
        with conftest.notices_said(lambda notice: shown.append(notice.text)):   # what was a box is a notice since v0.117
            yield shown
    finally:
        for name, value in saved.items():
            setattr(QMessageBox, name, value)


def _fresh(tab, here):
    journal.write_source(here.journal_file, _source())
    tab.dirty = False
    tab.on_shown()
    tab.load_first()


def _saved(here):
    return {e["index"]: e for e in journal.read(here.journal_file)["entries"]}


def test_the_tab_lists_the_revisions_newest_first_in_the_projects_group():
    window, here = _window()
    import chrome
    import woodcore_gui
    keys = [key for key, _factory in woodcore_gui.TABS]
    # «Métré» stands between them since the spec 2026-10-21-commandes-typst-refonte (UI-003): what the positions' plans draw, under «Positions»
    assert keys[keys.index("tab_positions") + 1] == "tab_metre" and keys[keys.index("tab_metre") + 1] == "tab_journal", keys
    # ⚠️ A **relative** ordering, and deliberately not the exact tuple this line held until v0.100: what this check is
    # about is that *Journal* sits in «Projet» right after *Positions*, not how many modules that group holds. The exact
    # form had to be updated twice in two versions -- v0.99 for the journal itself, v0.100 for *Python* -- each time going
    # red for somebody whose change had nothing to do with the journal, while catching nothing about the journal's own
    # place. It is also the shape this codebase states as its own convention: tests/test_chrome.py pins the orderings
    # inside «Structure» «as an order between two rows and not a fixed position, so that a module added to the group later
    # does not make them false», and asserts on top of that that every tab is in exactly one group -- so nothing is lost
    # by letting this group grow.
    group = dict(woodcore_gui.NAV_GROUPS)["nav_project"]
    assert "tab_journal" in group, group
    assert group.index("tab_positions") + 2 == group.index("tab_journal"), group
    assert "tab_journal" in chrome.ICONS
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        assert tab.list.indices() == [3, 2, 1], tab.list.indices()
        item = tab.list.item_of(3)
        assert [item.text(i) for i in range(tab.list.columnCount())] == ["3", "2026-09-25", "Petra Prüfer", "PPA", "Prüfung"]
        assert tab.current == 3 and tab.label_edit.text() == "Prüfung"
        tab.search.setText("prüfer")
        assert [i for item, i in tab.list.rows() if not item.isHidden()] == [3]
        tab.search.setText("")


def test_an_entry_is_added_changed_and_deleted_and_read_back_from_the_file():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        # added: the next index proposed, the name and the short form of the entry before it
        assert tab.new()
        assert tab.current is None and tab.index_edit.value() == 4
        assert tab.name_edit.text() == "Petra Prüfer" and tab.initials_edit.text() == "PPA", "the entry before it is not what prefills"
        tab.date_edit.setText("2026-09-27")
        tab.date_edit.textEdited.emit("2026-09-27")
        tab.label_edit.setText("Verbindungsmittel ergänzt")
        tab.label_edit.textEdited.emit("Verbindungsmittel ergänzt")
        with _boxes() as shown:
            assert tab.save() is True, shown
        assert tab.current == 4 and not tab.dirty
        assert _saved(here)[4]["label"] == "Verbindungsmittel ergänzt"
        # the export followed at once, so the report sees it
        exported = json.loads((here.data_dir / journal.EXPORT_FILE).read_text(encoding="utf-8"))
        assert [e["index"] for e in exported["entries"]] == [4, 3, 2, 1]
        # changed
        tab.summary_edit.setPlainText("Die Stabdübel des Vordachs.")
        with _boxes() as shown:
            assert tab.save() is True, shown
        assert _saved(here)[4]["summary"] == "Die Stabdübel des Vordachs."
        # deleted, after a yes naming its number
        with _boxes() as shown:
            assert tab.delete() is True, shown
        assert "4" in shown[0], shown
        assert 4 not in _saved(here) and tab.current == 3
        # a gap is what is never refilled: Rev. 2 taken out leaves 2 unused
        with _boxes():
            tab.load(2)
            assert tab.delete() is True
        assert journal.next_index(journal.read(here.journal_file)) == 4, "a gap was refilled"


def test_a_bad_field_is_refused_under_its_own_field_and_nothing_is_written():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        before = here.journal_file.read_bytes()
        assert tab.new()
        tab.label_edit.setText("Ohne Datum")
        tab.label_edit.textEdited.emit("Ohne Datum")   # no date typed
        with _boxes() as shown:
            assert tab.save() is False
        assert tab.date_note.isVisibleTo(tab) and shown and "2026-09-27" in shown[0], shown
        # an index another entry holds
        tab.date_edit.setText("2026-09-27")
        tab.date_edit.textEdited.emit("2026-09-27")
        tab.index_edit.setValue(2)
        with _boxes() as shown:
            assert tab.save() is False
        assert tab.index_note.isVisibleTo(tab) and "2" in shown[0], shown
        assert here.journal_file.read_bytes() == before, "the journal was written by a refused save"
        tab.dirty = False
        tab.load_first()


def test_a_project_opened_read_only_writes_nothing():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        _fresh(tab, here)
        before = here.journal_file.read_bytes()
        window.read_only = True
        refused = []
        window.refuse_read_only = lambda *a, **k: refused.append(True)
        try:
            tab.label_edit.setText("Nicht gespeichert")
            assert tab.save() is False and tab.delete() is False
        finally:
            window.read_only = False
        assert len(refused) == 2, refused
        assert here.journal_file.read_bytes() == before
        tab.dirty = False
        tab.load_first()


def test_the_tabs_words_are_the_same_keys_in_three_languages():
    import journal_tab
    reference = set(journal_tab.STRINGS["fr"])
    for lang, table in journal_tab.STRINGS.items():
        assert set(table) == reference, f"{lang}: {sorted(set(table) ^ reference)}"
        assert all(text for text in table.values()), lang
    assert not [k for k in reference if k != "tab_journal" and not k.startswith("jo_")], sorted(reference)
    assert "ß" not in json.dumps(journal_tab.STRINGS["de"], ensure_ascii=False), "the German is Swiss"


def test_the_calls_the_tab_copies_are_the_one_place_a_call_is_spelled_out():
    import build_reference as ref
    # the journal written once in raw Typst beside its document, included by domain-file (spec 2026-10-21-commandes-typst-refonte, Q-008, ARCH-008)
    assert ref.call_include_domain("journal", "cu") == '#include domain-file("journal", "cu")'
    assert "journal-entries" in ref.PUBLIC_NAMES and "show-journal" not in ref.PUBLIC_NAMES
    assert ref.category_of("journal-entries") == "data"


def test_the_template_carries_the_journals_own_page():
    """The engineer's decision 6.8: the journal has a page of its own in the report. It is the last section, after the literature -- the sections editor of *Paramètres* moves it forward in one click (docs/domain/journal.md §3.3terdecies)."""
    report_dir = ROOT / "templates" / "projet" / "Statischer Bericht (typst)"
    section = report_dir / "Sections" / "008-journal.typ"
    assert section.is_file(), "the template has no journal section"
    body = section.read_text(encoding="utf-8")
    # The import line is asked of calc/documents.py's `import_line` and never spelt out here: it is the one place the line is written down (docs/typst/reference-workbook.md §10ter; build_reference.import_line delegates to it), so this follows the line if it ever moves. ⚠️ And spelling it out would fail `test_harness.test_a_probe_imports_by_a_path_its_depth_cannot_break`, whose grep cannot tell a relative import a test *reads* from one it *writes* -- which is also why this comment names neither.
    # It is the line of **no project** -- a report alone's, which is what the Standard template's sections carry, the template being laid out as one report on disk -- and not the line of the project the suite works on, which is laid out in three documents and whose sections import from the root.
    import documents
    assert '#include domain-file("journal", "rs")' in body and body.startswith(documents.import_line(None))
    entry = (report_dir / "Statischer Rapport.typ").read_text(encoding="utf-8")
    assert '#include "Sections/008-journal.typ"' in entry, "the journal section is not included"
