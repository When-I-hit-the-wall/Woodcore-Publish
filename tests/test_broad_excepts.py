"""What the broad excepts of calc/ became (spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, annex A, REQ-28-01 to REQ-28-03, UI-28-01; issue #28).

(a) A file that does not read stops, naming the file: an annex, a plan's background, a document of an export, a DXF. (b) What a tab leaves out is said: a schema that does not read is a warning notice naming the file and why, the tab going on with the others. (c) A handler narrowed to the exception it expects lets any other through: a defect is no longer turned into silence.
"""

import contextlib
import json
import shutil
import subprocess

import conftest
from conftest import ROOT, Skip

import validation
import content_switch
import project_lock
import sheets
import sync
from domains import annex, plan, plan_documents, quantities
from domains import schema as schema_model


@contextlib.contextmanager
def _patched(module, **names):
    saved = {name: getattr(module, name) for name in names}
    for name, value in names.items():
        setattr(module, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            setattr(module, name, value)


def _not_a_pdf(name):
    path = conftest.tmpdir("broad-excepts") / name
    path.write_bytes(b"this is not a PDF at all\n")
    return path


def _refused(call, *names):
    try:
        call()
    except validation.ValidationError as exc:
        text = str(exc) + " " + json.dumps(getattr(exc, "values", {}) or {}, default=str)
        for name in names:
            assert name in text, f"{name!r} not named in: {text}"
        return exc
    raise AssertionError("a file that does not read was read")


# --- (a): a file that does not read stops, naming it ----------------------------------------------

def test_an_annex_that_is_not_a_pdf_stops_naming_the_file():
    path = _not_a_pdf("annexe-3.pdf")
    _refused(lambda: annex.reader(path), "annexe-3.pdf", "could not be read as a PDF")


def test_a_plan_background_that_is_not_a_pdf_stops_naming_the_file_and_the_field():
    path = _not_a_pdf("Grundriss-EG.pdf")
    _refused(lambda: plan.sheet_of(path, "pdf", 1, where="plans/P01.json background"), "Grundriss-EG.pdf", "plans/P01.json background", "cannot be read as a PDF")


def test_a_document_of_an_export_that_is_not_a_pdf_stops_naming_the_file():
    path = _not_a_pdf("Coupe-A.pdf")
    exc = _refused(lambda: plan_documents._count_pdf(path), "Coupe-A.pdf")
    assert getattr(exc, "code", None) == "doc_unreadable"


def test_a_dxf_that_does_not_read_stops_naming_the_file():
    try:
        from domains import cad
        cad._ezdxf()
    except (ImportError, validation.ValidationError) as exc:
        raise Skip(f"ezdxf is not installed ({exc})")
    path = conftest.tmpdir("broad-excepts") / "Plan-architecte.dxf"
    path.write_text("0\nSECTION\n2\nNOT A DXF\n", encoding="utf-8")
    exc = _refused(lambda: cad.read_dxf(path), "Plan-architecte.dxf", "cannot be read as a DXF")
    assert getattr(exc, "code", None) == "dxf_unreadable"


# --- (b), UI-28-01: a schema that does not read is said, the others offered ------------------------

def _details_with_a_broken_schema():
    folder = conftest.tmpdir("broad-excepts-details")
    for old in folder.glob("*.json"):
        old.unlink()
    source = next(iter(schema_model.source_paths(conftest.PROJECT.details_dir)), None)
    if source is None:
        raise Skip("the example project has no detail schema")
    shutil.copyfile(source, folder / source.name)
    (folder / "S-broken.json").write_text('{"id": "S-broken", "schema_version": ', encoding="utf-8")
    return folder, source


def test_a_schema_that_does_not_read_is_left_out_with_its_reason_and_the_others_read():
    folder, good = _details_with_a_broken_schema()
    sources, problems = schema_model.readable_sources(folder)
    assert set(sources) == {json.loads(good.read_text(encoding="utf-8"))["id"]}, sources.keys()
    assert [p.name for p, _e in problems] == ["S-broken.json"], problems
    assert "S-broken.json" in str(problems[0][1]) and "could not be read" in str(problems[0][1])
    try:
        schema_model.read_sources(folder)
    except validation.ValidationError as exc:
        assert "S-broken.json" in str(exc), "the export still stops on it, naming it"
    else:
        raise AssertionError("the export read a folder with a schema that does not read")


def test_the_window_says_the_schema_it_left_out_in_a_warning_naming_the_file():
    import sys
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        import notices_ui
        import notifications
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    folder, _good = _details_with_a_broken_schema()
    _sources, problems = schema_model.readable_sources(folder)
    store = notifications.STORE
    before = len(store.items())
    notices_ui.tell_unreadable_schemas(problems)
    notices_ui.tell_unreadable_schemas(problems)
    said = [n for n in store.items() if n.code == "schema_unreadable"]
    try:
        assert len(store.items()) == before + 1, "the same schema left out twice is one notice, counted twice"
        notice = said[-1]
        assert notice.severity == notifications.WARNING and notice.count == 2
        assert notice.file.endswith("S-broken.json") and notice.args["file"] == "S-broken.json" and "could not be read" in notice.args["error"]
        import woodcore_gui
        for lang in ("fr", "de", "en"):
            for key in ("notice_schema_unreadable", "notice_schema_unreadable_title"):
                assert woodcore_gui.translate_notice(key, lang), (lang, key)
            assert "S-broken.json" in woodcore_gui.translate_notice("notice_schema_unreadable", lang).format(**notice.args)
    finally:
        for notice in said:
            store.remove(notice.id)


# --- (c): a handler narrowed to what it expects lets a defect through -------------------------------

def test_a_file_whose_tags_do_not_read_is_compared_whole_and_a_defect_is_not_swallowed():
    import typst_objects

    def unreadable(_text):
        raise typst_objects.ParseError("unclosed", 3, "x")

    def defect(_text):
        raise TypeError("a defect of the reader")

    with _patched(typst_objects, objects=unreadable):
        assert sync._top_objects("text") == [] and content_switch._objects("woodcore:object") == []
    for call in (lambda: sync._top_objects("text"), lambda: content_switch._objects("woodcore:object")):
        with _patched(typst_objects, objects=defect):
            try:
                call()
            except TypeError:
                pass
            else:
                raise AssertionError("a defect of the reader was swallowed as a file that does not read")


def test_who_holds_a_project_falls_back_only_where_the_user_cannot_be_named():
    import getpass

    def nobody():
        raise OSError("no user named")

    with _patched(getpass, getuser=nobody):
        assert project_lock.whoami()["user"]


def test_a_sheet_that_times_out_is_a_sentence():
    def slow(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("typst", 1)

    with _patched(sheets.proc, run=slow), _patched(sheets, read=lambda here, sheet_id: None, compile_args=lambda here, sheet_id, target=None: []):
        ok, message = sheets.compile(conftest.PROJECT, "B01")
    assert ok is False and "timed out" in message, message


def test_a_position_whose_section_does_not_read_has_no_quantity_and_nothing_else_is_caught():
    text = (ROOT / "calc" / "domains" / "quantities.py").read_text(encoding="utf-8")
    assert "except validation.ValidationError:" in text and "except Exception" not in text
