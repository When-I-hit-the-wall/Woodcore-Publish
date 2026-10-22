"""Woodcore's notices gathered in one place (calc/notifications.py; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-010, REQ-011, ARCH-001).

The engineer, 07.10.2026: «Toutes les erreurs doivent être centralisées dans le système global de notifications d'erreurs de Woodcore» · «Il faut distinguer : Message utilisateur, traduit … Informations techniques : conserver les informations techniques originales». Each test works on a store of its own, so nothing reported here reaches the process's own.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import threading

from conftest import ROOT

import engine
import notifications

WORDS = {
    "fr": {"notice_typst_error_title": "Compilation Typst impossible", "notice_typst_error": "Impossible de compiler le document : {message}",
           "notice_severity_warning": "Avertissement", "warn_missing": "Il manque {what}", "warn_thing": "la chose"},
    "de": {"notice_typst_error_title": "Typst-Kompilierung unmöglich", "notice_typst_error": "Das Dokument lässt sich nicht kompilieren: {message}",
           "notice_severity_warning": "Warnung", "warn_missing": "Es fehlt {what}", "warn_thing": "das Ding"},
    "en": {"notice_typst_error_title": "Typst compilation failed", "notice_typst_error": "The document cannot be compiled: {message}",
           "notice_severity_warning": "Warning", "warn_missing": "{what} is missing", "warn_thing": "the thing"},
}


def _translate(key, lang):
    return WORDS.get(lang, {}).get(key)


def test_the_core_imports_no_qt():
    for name in ("notifications.py", "typst_diagnostics.py"):
        tree = ast.parse((ROOT / "calc" / name).read_text(encoding="utf-8"))
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        assert not any(module.startswith("PySide6") for module in imported), (name, imported)


def test_the_same_trouble_counts_once_more_and_another_is_kept_apart():
    store = notifications.Store()
    seen = []
    store.listen(lambda: seen.append(1))
    first = notifications.report("calc_failed", "the calculation failed", notifications.CRITICAL, technical="ZeroDivisionError", source="loads", store=store)
    again = notifications.report("calc_failed", "the calculation failed", notifications.CRITICAL, technical="ZeroDivisionError", source="loads", store=store)
    other = notifications.report("calc_failed", "the calculation failed", notifications.CRITICAL, technical="KeyError: 'h'", store=store)
    assert again is first and first.count == 2 and other is not first
    assert store.counts() == {"critical": 2, "warning": 0, "info": 0, "success": 0}
    assert len(seen) == 3, "every change is announced"
    assert [n.id for n in store.items()] == [other.id, first.id], "the latest first"


def test_deleting_takes_one_out_or_every_one_of_a_kind_or_all():
    store = notifications.Store()
    a = notifications.report("a", "A", notifications.CRITICAL, store=store)
    notifications.report("b", "B", notifications.WARNING, store=store)
    notifications.report("c", "C", notifications.WARNING, store=store)
    assert store.remove(a.id) and not store.remove(a.id)
    assert store.counts()["critical"] == 0
    assert store.clear(notifications.WARNING) and store.items() == []
    notifications.report("d", "D", store=store)
    assert store.clear() and store.items() == [] and not store.clear()


def test_the_words_follow_the_language_and_the_technical_text_stays_as_it_was():
    notifications.configure(translate=_translate)
    store = notifications.Store()
    found = notifications.report_typst("error: unknown variable: foo\n  ┌─ report.typ:183:14\n", source="compile", root="C:/projet", store=store)
    (notice,) = found
    assert (notice.severity, notice.line, notice.column) == ("critical", 183, 14)
    assert notice.file.replace("\\", "/") == "C:/projet/report.typ" and notifications.OPEN_FILE in notice.actions
    assert notifications.title(notice, "fr") == "Compilation Typst impossible"
    assert notifications.message(notice, "fr") == "Impossible de compiler le document : unknown variable: foo"
    assert notifications.message(notice, "de").startswith("Das Dokument") and notifications.title(notice, "en") == "Typst compilation failed"
    assert "unknown variable: foo" in notice.technical, "Typst's own text is never translated"
    copied = notifications.copy_text(notice, "fr", {"Woodcore": "0.117.0"})
    for part in ("[critical]", "Compilation Typst impossible", "report.typ:183:14", "Woodcore: 0.117.0", "unknown variable: foo"):
        assert part in copied, (part, copied)


def test_a_domain_note_keeps_its_code_and_its_arguments_are_translated_too():
    notifications.configure(translate=_translate)
    store = notifications.Store()
    note = engine.Note("missing", "the thing is missing", what=engine.Note("thing", "the thing"))
    notice = notifications.report_note(note, source="export", store=store)
    assert notice.code == "missing" and notifications.message(notice, "fr") == "Il manque la chose"
    assert notifications.message(notice, "en") == "the thing is missing"
    assert notifications.title(notice, "de") == "Warnung", "a code with no title of its own takes its severity's"
    plain = notifications.report_note("a sentence", store=store)
    assert notifications.message(plain, "fr") == "a sentence", "a sentence without a code is shown as it is"


def test_an_exception_in_a_thread_is_reported_critical_with_its_traceback():
    store = notifications.Store()

    def work():
        try:
            {}["h"]
        except KeyError as exc:
            notifications.report_exception(exc, source="worker", store=store)
    thread = threading.Thread(target=work)
    thread.start()
    thread.join()
    (notice,) = store.items()
    assert notice.severity == notifications.CRITICAL and "KeyError" in notice.text
    assert "Traceback" in notice.technical and notice.file.endswith("test_notices.py") and notice.line


def test_typst_output_without_a_diagnostic_is_still_one_notice():
    store = notifications.Store()
    (notice,) = notifications.report_typst("typst: the process was killed after 15 s", store=store)
    assert notice.severity == notifications.CRITICAL and "killed" in notice.technical
    assert notifications.report_typst("", store=store) == []


def test_the_log_gets_every_notice_once_configured():
    import conftest
    log = conftest.tmpdir("notices-log") / "woodcore.log"
    saved = dict(notifications._config)
    try:
        notifications.configure(log=log)
        store = notifications.Store()
        notifications.report("typst_error", "Typst failed", notifications.CRITICAL, file="C:/p/report.typ", line=3, technical="error: x", store=store)
        text = log.read_text(encoding="utf-8")
        assert "--- Woodcore started" in text and "critical" in text and "C:/p/report.typ:3" in text and "error: x" in text
    finally:
        notifications._config.update(saved)


def test_nothing_is_logged_unless_configured():
    """Importing notices opens no log -- a test run writes none; only the window's start configures it. Asked of a fresh process, never by reloading the module this one shares."""
    import subprocess
    import sys
    done = subprocess.run([sys.executable, "-c", "import notifications; print(notifications._config['log'])"], cwd=ROOT / "calc", capture_output=True, text=True)
    assert done.stdout.strip() == "None", done.stdout + done.stderr


def test_a_note_written_by_another_process_comes_back_with_its_code_and_its_arguments():
    """ARCH-008: the export started by the window writes its warnings as structured lines; the window reads them back as notes, never parsing an English sentence -- and what else the process wrote is one warning, as it was."""
    import io
    notifications.configure(translate=_translate)
    out = io.StringIO()
    notifications.emit(engine.Note("missing", "the thing is missing", what=engine.Note("thing", "the thing")), source="export", stream=out)
    assert out.getvalue().startswith(notifications.STRUCTURED_PREFIX)
    store = notifications.Store()
    found = notifications.read_output(out.getvalue() + "Traceback (most recent call last):\n  File x\nKeyError: 'h'\n", source="export", store=store)
    note, rest = found
    assert (note.code, note.source) == ("missing", "export") and notifications.message(note, "fr") == "Il manque la chose"
    assert rest.code == "process_output" and "KeyError" in rest.technical
    assert notifications.read_output('woodcore-notice {"schema_version": "9.0", "text": "x"}\n', store=notifications.Store())[0].code == "process_output", "an unknown version is not taken for one"


def test_the_export_started_by_the_window_writes_structured_warnings():
    """The real export, as the window starts it (STRUCTURED_ENV): a warning it has -- a position file left behind -- arrives as a structured line, and nothing else is on standard error."""
    import json
    import os
    import subprocess
    import sys
    import conftest
    here = conftest.project_copy("notices-export")
    # the copy carries no backgrounds (conftest.project_copy), and a plan drawn on a file that is not there stops the export: drawn on an empty sheet here, as tests/test_plan_tab_rework.py does
    for path in here.plans_dir.glob("*.json"):
        source = json.loads(path.read_text(encoding="utf-8"))
        source.pop("background", None)
        path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    stale = here.data_dir / "positions" / "ZZ999.json"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text(json.dumps({"position": "ZZ999"}), encoding="utf-8")
    env = dict(os.environ, **{notifications.STRUCTURED_ENV: "1", "PYTHONIOENCODING": "utf-8"})
    done = subprocess.run([sys.executable, str(ROOT / "calc" / "cli.py"), "export", "--data-only", "--project", str(here.file)],
                          capture_output=True, text=True, encoding="utf-8", env=env, cwd=ROOT, timeout=600)
    assert done.returncode == 0, done.stderr[-2000:]
    store = notifications.Store()
    found = notifications.read_output(done.stderr, source="export", store=store)
    assert any("ZZ999" in n.text and n.code != "process_output" for n in found), done.stderr
    assert not [n for n in found if n.code == "process_output"], done.stderr
