"""The window of a project written as three documents (the engineer's request of 30.09.2026; calc/tools/woodcore_gui.py, chrome.py, journal_tab.py, variables_tab.py, migrate_dialog.py).

A project laid out in three documents -- the convention d'utilisation, the base de projet and the report, which is simply the third -- is written one document at a time: a drop-down at the top of the navigation chooses which, and the modules shown change with it (MODE_TABS: the report every module, the two others what they are written from). The journal is the document's own, the variables tab lists the three and the export, and «Exporter PDF» exports the document shown -- «Exporter les trois» the three -- each passed over where its Typst did not change since its PDF (calc/stamps.py). A project still laid out as one report shows no drop-down and is offered its migration as it opens (migrate_dialog.py).

What is held here: the drop-down and its three entries, the modules each document shows and the group titles hidden with their last row, Ctrl+1 … Ctrl+9 counting only what is shown, the document remembered per project, a journal half written keeping the engineer on its document, the folded navigation's number, the journal following the document, the PDF button naming it, an unchanged document neither compiled nor archived, «Exporter les trois», the window's command line compiling a document for real and its stamp saying so, and the migration offered, put off, forced, and run.

⚠️ Built off-screen, and every modal a check would meet is replaced first: a modal off-screen never comes back. The project in three documents is made once, by `project_template.create`, in this process's own temp folder.
"""

import contextlib
import os
import shutil
import subprocess
import sys

import conftest
from conftest import ROOT

import project

TOOLS = ROOT / "calc" / "tools"
_STATE = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _modes_project():
    """A project in three documents, French, made once for the file."""
    if "here" not in _STATE:
        import project_template
        base = conftest.tmpdir("modes_window")
        _STATE["here"] = project_template.create(base / "Halle", "Halle", document_language="fr", report_language="fr", author="L. Exempel")
    return _STATE["here"]


def _window():
    """One window on that project, built once, off-screen, in French."""
    if "window" not in _STATE:
        _qt()
        here = _modes_project()
        import woodcore_gui
        with project.using(here):
            window = woodcore_gui.MainWindow()
            window.lang = "fr"
            window.mode = "rs"
            window.rebuild()
        _STATE["window"] = window
    return _STATE["window"], _STATE["here"]


@contextlib.contextmanager
def _patched(obj, **values):
    missing = object()
    saved = {name: getattr(obj, name, missing) for name in values}
    for name, value in values.items():
        setattr(obj, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is missing:
                delattr(obj, name)
            else:
                setattr(obj, name, value)


def _choose(window, mode):
    """The document chosen in the navigation's drop-down, the way a click does."""
    select = window.nav.mode_select
    select.setCurrentIndex(select.findData(mode))


def _keys(window):
    """The TABS keys of the rows the navigation shows, in its order."""
    import woodcore_gui
    return [woodcore_gui.TABS[index][0] for index in window.nav.order()]


def _ctrl_n(window):
    from PySide6.QtGui import QShortcut
    return sorted(s.key().toString() for s in window.centralWidget().findChildren(QShortcut)
                  if s.key().toString().startswith("Ctrl+") and s.key().toString()[5:].isdigit())


# --- the drop-down and the modules it shows --------------------------------------------------

def test_the_navigation_offers_the_three_documents_and_a_report_alone_none():
    window, here = _window()
    import documents
    from PySide6.QtWidgets import QComboBox
    assert here.has_modes
    select = window.nav.mode_select
    assert select is not None and select.objectName() == "modeSelect"
    assert window.centralWidget().findChild(QComboBox, "modeSelect") is select
    assert [select.itemData(i) for i in range(select.count())] == list(project.MODES), "three documents, in their order"
    assert [(select.itemData(i), select.itemText(i)) for i in range(select.count())] == documents.mode_choices("fr")
    # above the first group: the drop-down comes before the list in the navigation's own column
    column = window.nav.layout()
    assert column.itemAt(0).layout() is not None and column.itemAt(0).layout().indexOf(select) >= 0
    assert column.indexOf(window.nav.list) > 0
    # a project laid out as one report: no drop-down at all
    with _legacy_window() as legacy:
        assert not project.current().has_modes
        assert legacy.nav.mode_select is None and legacy.centralWidget().findChild(QComboBox, "modeSelect") is None
        assert legacy.current_document() == "rs"


def test_each_document_shows_its_own_modules():
    window, here = _window()
    import woodcore_gui
    with project.using(here):
        try:
            assert _keys(window) == [k for k in _keys(window) if k in woodcore_gui.MODE_TABS["rs"]]
            assert "tab_combinations" in _keys(window) and "tab_statics" in _keys(window), "the report shows every module"
            for mode in ("cu", "bp"):
                _choose(window, mode)
                assert window.mode == mode and window.nav.mode() == mode
                shown = _keys(window)
                assert set(shown) == set(woodcore_gui.mode_tabs(mode)), (mode, shown)
                assert {"tab_plan", "tab_positions", "tab_journal", "tab_variables", "tab_commands"} <= set(shown)
                assert "tab_combinations" not in shown and "tab_polar" not in shown
                # a group whose every row is hidden hides its title too; one with a row shown keeps it
                for head, members in window.nav.groups:
                    assert head.isHidden() == all(item.isHidden() for item in members), head.text()
                assert any(head.isHidden() for head, _members in window.nav.groups), "«Actions» should be hidden"
                # the module in front is one the document shows
                assert window.tab_widget.currentIndex() in window.nav.order()
                # Ctrl+1 … Ctrl+n for the modules shown and no other
                assert _ctrl_n(window) == [f"Ctrl+{n}" for n in range(1, min(9, len(shown)) + 1)], _ctrl_n(window)
            _choose(window, "rs")
            assert len(window.nav.order()) == len(woodcore_gui.mode_tabs("rs"))
            assert _ctrl_n(window) == [f"Ctrl+{n}" for n in range(1, min(9, len(window.nav.order())) + 1)]
        finally:
            _choose(window, "rs")


def test_the_document_is_remembered_per_project_and_survives_a_rebuild():
    window, here = _window()
    import usersettings
    import woodcore_gui
    with project.using(here):
        try:
            _choose(window, "bp")
            kept = usersettings.read().get("document_modes", {})
            assert kept.get(woodcore_gui.mode_key(here.file)) == "bp", kept
            window.rebuild()
            assert window.mode == "bp" and window.nav.mode() == "bp" and "tab_combinations" not in _keys(window)
            other = woodcore_gui.MainWindow()
            try:
                assert other.mode == "bp", "a window opened again forgets the document it was on"
            finally:
                other.close()
        finally:
            _choose(window, "rs")
    # a project laid out as one report is always on its report, whatever the settings keep for it
    with _legacy_window() as legacy:
        assert legacy.mode == "rs"


def _opened_on(here, kept=None):
    """(the window's `mode`, its `current_document()`) for a window opened on project `here` when the user's settings keep `kept` -- {project file: document} -- for projects, and nothing else: a window built, read and closed, the settings put back as they were."""
    import usersettings
    import woodcore_gui
    saved = usersettings.read()
    settings = dict(saved)
    settings.pop("document_modes", None)
    if kept is not None:
        settings["document_modes"] = {woodcore_gui.mode_key(file): mode for file, mode in kept.items()}
    usersettings.write(settings)
    try:
        with project.using(here):
            window = woodcore_gui.MainWindow()
            try:
                return window.mode, window.current_document()
            finally:
                conftest.dispose(window)
    finally:
        usersettings.write(saved)


def test_a_new_project_opens_on_the_convention_d_utilisation():
    """The engineer's request of 01.10.2026: a project begun in three documents is begun with its first, the convention d'utilisation -- where it used to open on the report, the last of the three. «Begun» is a project the user's settings have no document for."""
    _qt()
    import project_template
    import woodcore_gui
    base = conftest.tmpdir("modes_default")
    fresh = project_template.create(base / "Neu", "Neu", document_language="fr", report_language="fr", author="L. Exempel")
    assert fresh.has_modes and fresh.modes == project.MODES
    assert _opened_on(fresh) == ("cu", "cu"), "a project with no remembered document opened on its report"
    # what it shows is that document's modules, not the report's
    with project.using(fresh):
        window = woodcore_gui.MainWindow()
        try:
            window.lang = "fr"
            window.rebuild()
            assert window.mode == "cu" and window.nav.mode() == "cu" and window.nav.mode_select.currentData() == "cu"
            assert set(_keys(window)) == set(woodcore_gui.mode_tabs("cu")), _keys(window)
            assert "tab_combinations" not in _keys(window)
        finally:
            conftest.dispose(window)
def test_a_remembered_document_is_kept_the_report_and_the_base_de_projet_included():
    """Only a project with nothing remembered opens on the convention d'utilisation: one the user was on keeps its document, whichever it was -- and a value the project does not have (a document of an older layout, a hand-edited settings file) is no memory at all."""
    _qt()
    import project_template
    base = conftest.tmpdir("modes_kept")
    fresh = project_template.create(base / "Gespeichert", "Gespeichert", document_language="fr", report_language="fr")
    for kept in ("bp", "rs", "cu"):
        assert _opened_on(fresh, {fresh.file: kept}) == (kept, kept), kept
    for nonsense in ("xx", "", None, 3):
        assert _opened_on(fresh, {fresh.file: nonsense}) == ("cu", "cu"), nonsense
    # what is kept for another project says nothing about this one
    other = project_template.create(base / "Anderes", "Anderes", document_language="fr", report_language="fr")
    assert _opened_on(fresh, {other.file: "bp"}) == ("cu", "cu")
    assert _opened_on(other, {other.file: "bp", fresh.file: "rs"}) == ("bp", "bp")


def test_a_project_laid_out_as_one_report_stays_on_its_report():
    """Its only document: nothing remembered, or a document it does not have remembered -- the convention d'utilisation of a project it was once migrated and unmigrated from -- opens on the report."""
    _qt()
    with _legacy_window() as legacy:
        legacy.close()
    legacy_project = _STATE["legacy"]
    assert not legacy_project.has_modes and legacy_project.modes == ("rs",)
    assert _opened_on(legacy_project) == ("rs", "rs")
    for kept in ("cu", "bp", "rs"):
        assert _opened_on(legacy_project, {legacy_project.file: kept}) == ("rs", "rs"), kept


def test_something_unsaved_in_the_journal_keeps_the_engineer_on_his_document():
    window, here = _window()
    import journal_tab
    tab = next(t for t in window.tabs if isinstance(t, journal_tab.JournalTab))
    with project.using(here):
        try:
            _choose(window, "cu")
            asked = []
            with _patched(tab, confirm_leave=lambda: asked.append(True) or False):
                _choose(window, "bp")
            assert asked, "the journal was not asked about what it holds unsaved"
            assert window.mode == "cu" and window.nav.mode() == "cu" and window.nav.mode_select.currentData() == "cu"
        finally:
            _choose(window, "rs")


def test_folded_the_navigation_shows_the_document_s_number():
    window, here = _window()
    nav = window.nav
    with project.using(here):
        try:
            nav.set_collapsed(True)
            assert nav.mode_select.isHidden() and not nav.mode_button.isHidden()
            assert nav.mode_button.text() == "3" and nav.mode_button.toolTip() == window.document_name("rs")
            action = next(a for a in nav.mode_button.menu().actions() if a.data() == "bp")
            action.trigger()
            assert window.mode == "bp" and nav.mode_button.text() == "2"
        finally:
            nav.set_collapsed(False)
            _choose(window, "rs")
        assert not nav.mode_select.isHidden() and nav.mode_button.isHidden()


# --- the tabs that read one document -----------------------------------------------------------

def test_the_journal_follows_the_document():
    window, here = _window()
    import journal
    import journal_tab
    from PySide6.QtWidgets import QMessageBox
    tab = next(t for t in window.tabs if isinstance(t, journal_tab.JournalTab))
    with project.using(here):
        try:
            _choose(window, "cu")
            assert tab.file() == here.journal_file_for("cu") and tab.file().name == "journal-cu.json"
            assert tab.title.text() == window.t("jo_list", document=window.document_name("cu"))
            before = here.journal_file_for("rs").read_bytes() if here.journal_file_for("rs").exists() else None
            tab.open_draft({"date": "2026-09-30", "name": "L. Exempel", "initials": "LEX", "label": "Erstausgabe"})
            with _patched(QMessageBox, warning=staticmethod(lambda *a, **k: None), information=staticmethod(lambda *a, **k: None)):
                assert tab.save() is True
            assert [e["label"] for e in journal.read(here.journal_file_for("cu"))["entries"]] == ["Erstausgabe"]
            exported = here.data_dir / journal.EXPORT_FILES["cu"]
            assert "Erstausgabe" in exported.read_text(encoding="utf-8"), "the document's own journal was not exported"
            after = here.journal_file_for("rs").read_bytes() if here.journal_file_for("rs").exists() else None
            assert after == before, "an entry of the convention d'utilisation reached the report's journal"
            _choose(window, "rs")
            assert tab.file() == here.journal_file_for("rs") and "Erstausgabe" not in [tab.list.item_of(i).text(4) for i in tab.list.indices() if i != -1]
        finally:
            tab.dirty = False
            _choose(window, "rs")


def test_the_variables_tab_marks_each_value_with_where_it_comes_from():
    """Since v0.117 (issue 13) a column of provenance -- Excel, Woodcore, or Typst and the document's letters -- where the Document column said Export, CU, BP or RS."""
    window, here = _window()
    import variable_sources
    import variables
    import variables_tab
    tab = next(t for t in window.tabs if isinstance(t, variables_tab.VariablesTab))
    with project.using(here):
        reading = variables.Registry(stamp="pinned", domains={"": [variables.Variable(key="R_d", domain="", value=2.5, unit="kN", symbol="R_d")]})
        tab.readings = {"cu": reading, "rs": reading}
        tab.errors = {}
        tab.export = variable_sources.read_export(here)
        tab.domain_key = None
        tab.refresh()
        provenances = [tab.domain_list.topLevelItem(i).text(2) for i in range(tab.domain_list.topLevelItemCount())]
        typst = tab.t("vr_prov_typst")
        assert provenances[0] == f"{typst} · RS" and f"{typst} · CU" in provenances, provenances
        assert not provenances[-1].startswith(typst), "the export's domains come last"
        # the export's values are named by their calculation and its instance, as `val` reads them
        domain = next(d for d in tab.export.domains if d.variables)
        var = domain.variables[0]
        tab.select_key((variables_tab.EXPORT, domain.name, var.key))
        import display_view
        calls = [display_view.entry_call(entry) for entry in tab.display_entries()]   # the «Affichage» view's since v0.117
        import build_reference as ref
        calc, instance = tab.address(tab.selected_key())
        assert ref.call_val(var.key, domain=calc, instance=instance) in calls, calls
        # one document alone, over every domain
        tab.all_domains_box.setChecked(True)
        tab.provenance_box.setCurrentIndex(tab.provenance_box.findData(f"{variables.TYPST}:cu"))
        assert {tab.tree.topLevelItem(i).text(variables_tab.PROVENANCE) for i in range(tab.tree.topLevelItemCount())} == {f"{typst} · CU"}
        tab.provenance_box.setCurrentIndex(0)
        tab.all_domains_box.setChecked(False)


# --- the PDF ------------------------------------------------------------------------------------

def test_the_pdf_button_names_the_document_and_offers_the_three():
    window, here = _window()
    import woodcore_gui
    with project.using(here):
        try:
            _choose(window, "bp")
            assert window.pdf_button.toolTip().splitlines()[0] == window.t("pdf_document", document=window.document_name("bp"))
            window.rebuild()
            texts = [a.text() for a in window.pdf_button.menu().actions()]
            assert window.t("pdf_all") in texts, texts
        finally:
            _choose(window, "rs")
    with _legacy_window() as legacy:
        assert legacy.t("pdf_all") not in [a.text() for a in legacy.pdf_button.menu().actions()], "a report alone has no three to export"


def _stamps_saying(changed_modes):
    """stamps.changed answering «changed» for `changed_modes` and «unchanged» for the others."""
    import engine

    def changed(here, mode, flags, ignore_flags=False, preview=False):
        if mode in changed_modes:
            return True, engine.Note("stamp_input_changed", f"{mode} changed", document=mode, file="x")
        return False, engine.Note("stamp_unchanged", f"the {mode} document is unchanged since its PDF", document=mode)
    return changed


def test_an_unchanged_document_is_neither_compiled_nor_archived_and_its_pdf_is_opened():
    window, here = _window()
    import stamps
    import woodcore_gui
    compiled, archived, opened = [], [], []
    pdf = here.document_pdf("cu")
    pdf.write_bytes(b"%PDF-1.7\n")   # a PDF the stamp says is current
    with project.using(here), \
            _patched(stamps, changed=_stamps_saying(())), \
            _patched(window, compile_document=lambda h, mode: compiled.append(mode)), \
            _patched(woodcore_gui.archive_export, run=lambda *a, **k: archived.append(k.get("mode"))), \
            _patched(woodcore_gui.QDesktopServices, openUrl=staticmethod(lambda url: opened.append(url.toLocalFile()))):
        try:
            _choose(window, "cu")
            window.pdf_modes = ["cu"]
            window.compile_flags = []
            window.start_compiles()
            assert compiled == [] and archived == [], "an unchanged document was compiled or archived"
            assert window.status.text() == window.t("doc_stamp_unchanged", document=window.document_name("cu")), window.status.text()
            assert [os.path.normcase(p) for p in opened] == [os.path.normcase(str(pdf))], "a single document's PDF is opened"
            assert window.pdf_button.isEnabled() and window.export_button.isEnabled()
        finally:
            pdf.unlink(missing_ok=True)
            _choose(window, "rs")


def test_export_all_three_compiles_only_those_that_changed_and_opens_none():
    window, here = _window()
    import stamps
    import woodcore_gui
    asked, compiled, recorded, archived, opened = [], [], [], [], []

    def fake_compile(h, mode):
        compiled.append(mode)
        window.compile_mode, window.compile_deps = mode, None
        window.compile_done(0, "", "")

    with project.using(here), \
            _patched(window, reexport=lambda chain_pdf=False: asked.append(chain_pdf)), \
            _patched(stamps, changed=_stamps_saying(("bp",)), record=lambda *a, **k: recorded.append(a[1])), \
            _patched(window, compile_document=fake_compile), \
            _patched(woodcore_gui.archive_export, run=lambda *a, **k: archived.append(k.get("mode"))), \
            _patched(woodcore_gui.QDesktopServices, openUrl=staticmethod(lambda url: opened.append(url.toLocalFile()))):
        window.pdf_level, window.pdf_lang = ("uniform", 2), None
        try:
            window.export_pdf(modes=here.modes)
            assert asked == [True] and window.pdf_modes == list(project.MODES), (asked, window.pdf_modes)
            assert window.compile_flags == ["--input", "uniform=2"], "the flags are fixed when the button is clicked"
            window.start_compiles()
        finally:
            window.pdf_level = (None, None)
    assert compiled == ["bp"] == recorded == archived, (compiled, recorded, archived)
    assert opened == [], "three documents exported open no PDF"
    status = window.status.text()
    for mode in ("cu", "rs"):
        assert window.t("doc_stamp_unchanged", document=window.document_name(mode)) in status, status
    assert window.document_name("bp") in status


def test_the_window_compiles_a_document_and_its_stamp_says_so():
    """The window's own command line, run for real: a document of a project in three documents compiles from the project's folder (documents.compile_args states the root), Typst writes what it read, and the stamp recorded after it calls the document unchanged -- so the next export passes it over."""
    if not conftest.have_typst():
        raise conftest.Skip("typst is not installed")
    window, here = _window()
    import stamps
    with project.using(here):
        program, arguments, deps = window.compile_command(here, "cu", [])
        # started in the Typst root, as the window starts it (woodcore_gui_export.py): the deps file's relative paths are from there
        done = subprocess.run([program, *arguments], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, cwd=here.typst_root)
        assert done.returncode == 0, done.stderr
        assert here.document_pdf("cu").is_file() and deps.is_file()
        stamps.record(here, "cu", [], deps, here.document_pdf("cu"))
        changed, why = stamps.changed(here, "cu", [])
        assert not changed, why
        assert window.stamp_text(why, "cu") == window.t("doc_stamp_unchanged", document=window.document_name("cu"))


# --- the migration of a project laid out as one report ---------------------------------------

def _legacy_copy(name):
    """The example project laid out as one report -- as it was committed before it was itself migrated into three documents, rebuilt by tests/fixtures/legacy_example.py, report included, which the migration's plan reads -- with the engine synced into it. Without its PDFs, as conftest.project_copy leaves them out: a plan's background would be held open by the plan tab's renderer of a window built on the copy, which Windows then refuses to let the run delete; the migration's plan reads the report's .typ and none of them."""
    from fixtures import legacy_example
    here = legacy_example.build(conftest.tmpdir(name) / "Exemple", conftest.SAMPLE)
    for pdf in here.root.rglob("*.pdf"):
        pdf.unlink()
    project.sync_engine(here)
    return here


@contextlib.contextmanager
def _legacy_window():
    """A window on the example laid out as one report (`_legacy_copy`, made once for the file), built off-screen as the project current while it is built and closed -- the example the suite works on being laid out in three documents."""
    import woodcore_gui
    if "legacy" not in _STATE:
        _STATE["legacy"] = _legacy_copy("modes_legacy")
    with project.using(_STATE["legacy"]):
        window = woodcore_gui.MainWindow()
        try:
            yield window
        finally:
            conftest.dispose(window)
def test_a_project_laid_out_as_one_report_is_offered_its_migration_and_it_can_be_put_off():
    _qt()
    import documents
    import migrate_dialog
    here = _legacy_copy("migrate_offer")
    asked, ran = [], []
    with _patched(migrate_dialog, ask=lambda parent, lang, text, details, can_migrate: asked.append((text, details, can_migrate)) or "later",
                  run=lambda *a, **k: ran.append(k) or (True, "")):
        try:
            assert migrate_dialog.offer(None, "fr", here) == "later"
            text, details, can_migrate = asked[0]
            assert can_migrate, text
            plan = migrate_dialog.prepare(here)[0]
            for mode in project.MODES:
                assert documents.MODE_FOLDERS[plan.language][mode] in text, (mode, text)
            assert "Migration of" in details, "the migration's own description is behind «Afficher les détails»"
            assert migrate_dialog.postponed(here) and not ran
            # put off: not asked again at the next opening -- the banner says it instead
            assert migrate_dialog.offer(None, "fr", here) == "postponed" and len(asked) == 1
            # the banner's «Migrer…» asks again
            assert migrate_dialog.offer(None, "fr", here, forced=True) == "later" and len(asked) == 2
        finally:
            migrate_dialog.set_postponed(here, False)
    assert not migrate_dialog.postponed(here)


def test_migrer_maintenant_runs_the_command_line_with_the_window_s_lock():
    _qt()
    import migrate_dialog
    here = _legacy_copy("migrate_now")
    import positions_store
    positions_store.path(here).unlink()   # neither its positions.json (v0.114) nor a Positionen.xlsx: nothing an export would compare
    ran, told = [], []
    with _patched(migrate_dialog, ask=lambda *a, **k: "now", run=lambda parent, lang, h, **k: ran.append(k) or (True, ""),
                  tell=lambda parent, lang, text, warning=False: told.append((text, warning))):
        assert migrate_dialog.offer(None, "de", here) == "migrated"
    assert ran and ran[0]["skip_data"] is True, "a project with no positions has no export to compare"
    assert told and not told[0][1] and here.name in told[0][0]
    assert not migrate_dialog.postponed(here)
    # and a migration that failed is said, and remembered as put off, the project staying as it was
    with _patched(migrate_dialog, ask=lambda *a, **k: "now", run=lambda *a, **k: (False, "migrate: refused"),
                  tell=lambda parent, lang, text, warning=False: told.append((text, warning))):
        assert migrate_dialog.offer(None, "de", here, forced=True) == "failed"
    assert told[-1][1] and "migrate: refused" in told[-1][0]
    migrate_dialog.set_postponed(here, False)
    # the command line: woodcore-cli migrate, the project, this process as the lock's owner, and what the engine and the data need
    program, arguments = migrate_dialog.command(here, update_engine=True, skip_data=True)
    assert arguments[arguments.index("migrate"):] == ["migrate", "--project", str(here.file), "--lock-owner", str(os.getpid()), "--update-engine", "--skip-data"], arguments
    # a migration that cannot run says why and offers nothing to agree to
    (here.root / documents_folder(here, "cu")).mkdir()
    shown = []
    with _patched(migrate_dialog, ask=lambda parent, lang, text, details, can_migrate: shown.append((text, can_migrate)) or "later"):
        assert migrate_dialog.offer(None, "fr", here, forced=True) == "refused"
    assert shown and not shown[0][1] and migrate_dialog.STRINGS["fr"]["mg_refused"] in shown[0][0]
    migrate_dialog.set_postponed(here, False)


def documents_folder(here, mode):
    import migrate_dialog
    return migrate_dialog.prepare(here)[0].folders[mode]


def test_open_project_offers_the_migration_before_seeding_and_says_so_in_a_banner():
    app = _qt()
    import export_all
    import migrate_dialog
    import woodcore_gui
    from PySide6.QtWidgets import QPushButton
    here = _legacy_copy("migrate_open")
    order = []
    seed = export_all.seed

    def offer(parent, lang, h, forced=False):
        order.append(("offer", forced))
        return "later"

    with project.using(conftest.PROJECT), \
            _patched(migrate_dialog, offer=offer), \
            _patched(export_all, seed=lambda h=None: order.append(("seed",)) or seed(h)), \
            _patched(woodcore_gui.MainWindow, check_engine=lambda self: None, check_dependencies=lambda self: None), \
            _patched(woodcore_gui.typst_gui, check_at_start=lambda window: None), \
            _patched(woodcore_gui.stallwatch, install=lambda app: None), \
            _patched(woodcore_gui.notices_ui, install_hooks=lambda: None):
        window = woodcore_gui.open_project(app, here.file, migrate=True)
        try:
            assert window is not None
            assert order[:2] == [("offer", True), ("seed",)], order
            assert window.migration_banner
            button = next((b for b in window.centralWidget().findChildren(QPushButton) if b.text() == window.t("mg_banner_button")), None)
            assert button is not None and button.toolTip(), "the banner offers «Migrer…», saying what it does"
            started = []
            with _patched(window, switch_to=lambda args: started.append(args)):
                button.click()
            assert started == [["--project", str(here.file), "--migrate"]], started
            app.processEvents()
        finally:
            conftest.dispose(window)
            woodcore_gui._WINDOWS.remove(window)
    # quiet -- --self-test -- is never asked
    order.clear()
    with project.using(conftest.PROJECT), _patched(migrate_dialog, offer=offer), \
            _patched(woodcore_gui.stallwatch, install=lambda app: None), _patched(woodcore_gui.notices_ui, install_hooks=lambda: None):
        window = woodcore_gui.open_project(app, here.file, quiet=True)
        try:
            assert window is not None and ("offer", False) not in order and ("offer", True) not in order
            assert not window.migration_banner
        finally:
            conftest.dispose(window)
            woodcore_gui._WINDOWS.remove(window)


def test_the_migration_s_words_are_the_same_keys_in_three_languages():
    import migrate_dialog
    reference = set(migrate_dialog.STRINGS["fr"])
    for lang, table in migrate_dialog.STRINGS.items():
        assert set(table) == reference, (lang, sorted(set(table) ^ reference))
        assert all(text.strip() for text in table.values()), lang
        assert all(key.startswith("mg_") for key in table), lang
    assert "ß" not in "".join(migrate_dialog.STRINGS["de"].values()), "the German is Swiss"
    # every refusal the migration can give a project the window offers it to has a sentence, or falls back to the migration's own English
    import engine
    note = engine.Note("collision", "x is there already", path="3_Rapport de statique")
    assert "3_Rapport de statique" in migrate_dialog.refusal_text(note, "fr")
    assert migrate_dialog.refusal_text(engine.Note("unheard_of", "said in English"), "de") == "said in English"
