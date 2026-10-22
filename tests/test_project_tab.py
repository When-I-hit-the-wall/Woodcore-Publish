"""The «Projet» tab (calc/tools/project_tab.py, issues #87, #88, #90; docs/ui/tab-project.md).

What is held: that it is the first row of the navigation in the three documents -- Ctrl+1 --, its words and its views' in three languages, and that the group once called «Projet» is «Données»; that the window opens on it and that its first view compiles nothing; that each card reads what the project files say -- the title page, the language greyed, the form, each document's content template («inconnu» where none is kept), the last export; that a title page saved writes only what changed, refuses an empty name, reports into data/project.json at once and names the project again in the top bar; that a project opened read-only shows the tab with nothing writable and its writers refused; that in a project whose documents are not made yet every other tab is greyed and out of Ctrl+n, and «Créer le document…» makes one; and that the «Templates» view previews a document in Woodcore's cache.

Built off-screen on copies of the example project and on skeletons made here; every question a check meets is answered first.
"""

import contextlib
import json
import os
import sys
import time

import conftest
from conftest import ROOT

import project

TOOLS = ROOT / "calc" / "tools"


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


@contextlib.contextmanager
def _patched(obj, **values):
    saved = {name: getattr(obj, name) for name in values}
    for name, value in values.items():
        setattr(obj, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            setattr(obj, name, value)


@contextlib.contextmanager
def _window(here):
    _qt()
    import woodcore_gui
    with project.using(here):
        window = woodcore_gui.MainWindow()
        try:
            yield window, window.tabs[window.project_index()]
        finally:
            for tab in window.tabs:
                if hasattr(tab, "dirty"):
                    tab.dirty = False
            conftest.dispose(window)


def _skeleton(name, language="fr"):
    import project_template
    return project_template.create_skeleton(conftest.tmpdir(name) / "P", "Probe", language, author="F. L.")


def test_the_tab_is_the_first_row_in_every_document_and_the_group_projet_is_donnees():
    _qt()
    import chrome
    import project_tab
    import views
    import woodcore_gui
    assert woodcore_gui.TABS[0] == ("tab_project", project_tab.ProjectTab) and "tab_project" in chrome.ICONS
    for mode, keys in woodcore_gui.MODE_TABS.items():
        assert keys[0] == "tab_project", mode
    assert project_tab.ProjectTab.VIEWS == ("details", "templates") and views.default(project_tab.ProjectTab) == "details"
    words = {"fr": ("Projet", "Données", "Informations", "Templates"), "de": ("Projekt", "Daten", "Angaben", "Vorlagen"), "en": ("Project", "Data", "Details", "Templates")}
    for lang, (tab, group, details, templates) in words.items():
        strings = woodcore_gui.STRINGS[lang]
        assert (strings["tab_project"], strings["nav_project"], strings["view_details"], strings["view_templates"]) == (tab, group, details, templates), lang
        assert set(project_tab.STRINGS[lang]) == set(project_tab.STRINGS["fr"]), lang
        titles = [strings[title] for title, _members in woodcore_gui.NAV_GROUPS]
        assert strings["tab_project"] not in titles, f"{lang}: a group of the navigation is still called {strings['tab_project']!r}"
    assert {"write_apply_form", "write_create_document"} <= set(woodcore_gui.WRITERS)


def test_the_window_opens_on_it_compiles_nothing_and_ctrl_1_is_it():
    import pdf_pane
    asked = []
    with _patched(pdf_pane.PdfPane, request=lambda self, *a, **k: asked.append(a), request_snippet=lambda self, *a, **k: asked.append(a)):
        with _window(conftest.project_copy("project_tab_open")) as (window, tab):
            assert window.tab_widget.currentIndex() == window.project_index() and tab.view == "details"
            window.show()
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            assert window.nav.order()[0] == window.project_index()
            assert not asked, f"opening the window asked Typst for {asked}"


def test_each_card_reads_what_the_project_files_say():
    import forms
    import templates
    here = conftest.project_copy("project_tab_cards")
    with _window(here) as (window, tab):
        assert tab.fields["name"].text() == here.name and tab.fields["client"].text() == here.detail("client")
        assert tab.language.currentData() == templates.project_language(here) and not tab.language.isEnabled(), "the language is shown greyed"
        current = forms.current(here)
        assert tab.form_combo.currentData() == (current.ref if current is not None else forms.default_ref())
        for mode in here.created_modes:
            text = tab.document_rows[mode]["template"].text()
            expected = tab._content_name(mode, here.content_template(mode))
            assert expected in text and (here.content_template(mode) or window.t("pj_unknown") in text), (mode, text)
            assert tab.document_rows[mode]["combo"].isHidden() and tab.document_rows[mode]["folder"].text() == here.rel(here.document_dir(mode))
        when, _engine = project.last_export(here)
        assert (when is None) == (tab.export_label.text() == window.t("pj_export_none"))


def test_a_title_page_saved_writes_what_changed_reports_into_the_export_and_names_the_project_again():
    here = conftest.project_copy("project_tab_save")
    with _window(here) as (window, tab):
        before = json.loads(here.file.read_text(encoding="utf-8"))
        tab.fields["client"].setText("Commune de Test")
        tab.fields["name"].setText("Hangar renommé")
        tab.mark_dirty()
        assert tab.dirty
        assert tab.save() is True and not tab.dirty
        after = json.loads(here.file.read_text(encoding="utf-8"))
        assert after["client"] == "Commune de Test" and after["name"] == "Hangar renommé"
        assert {k: v for k, v in after.items() if k not in ("client", "name")} == {k: v for k, v in before.items() if k not in ("client", "name")}, "a field not changed was written"
        info = json.loads((here.data_dir / "project.json").read_text(encoding="utf-8"))
        assert info["client"] == "Commune de Test" and info["name"] == "Hangar renommé"
        assert window.brand.text() == "Hangar renommé" and "Hangar renommé" in window.windowTitle()
        tab.fields["name"].setText("  ")
        tab.mark_dirty()
        import notices_ui
        with _patched(notices_ui, tell=lambda *a, **k: None):
            assert not tab.save()
        assert json.loads(here.file.read_text(encoding="utf-8"))["name"] == "Hangar renommé", "an empty name was written"
        tab.discard()
        assert tab.fields["name"].text() == "Hangar renommé" and not tab.dirty


def test_read_only_shows_the_tab_and_writes_nothing():
    here = conftest.project_copy("project_tab_read_only")
    with _window(here) as (window, tab):
        window.read_only = True
        tab.lock()
        assert not any(field.isEnabled() for field in tab.fields.values())
        assert not tab.save_button.isEnabled() and not tab.form_apply.isEnabled() and not tab.version.isEnabled()
        before = here.file.read_bytes()
        tab.fields["client"].setText("Ne s'écrit pas")
        tab.dirty = True
        import notices_ui
        with _patched(notices_ui, tell=lambda *a, **k: None):
            tab.save()
            tab.write_apply_form("builtin:bfh")
        assert here.file.read_bytes() == before, "a project opened read-only was written"
        window.read_only = False


def test_a_document_not_made_greys_every_other_tab_and_is_made_from_the_tab():
    _qt()
    import busy
    from PySide6.QtWidgets import QMessageBox
    here = _skeleton("project_tab_skeleton")
    with _window(here) as (window, tab):
        assert window.mode == "rs" and window.tab_widget.currentIndex() == window.project_index()
        assert window.nav.order() == [window.project_index()], "a tab of a document not made is reachable by Ctrl+n"
        assert not window.pdf_button.isEnabled()
        window.tab_widget.setCurrentIndex(window.project_index() + 1)
        assert window.tab_widget.currentIndex() == window.project_index(), "a door other than the navigation opened a tab of a document not made"
        assert all(row["template"].text() == window.t("pj_not_made") for row in tab.document_rows.values())
        row = tab.document_rows["rs"]
        assert not row["combo"].isHidden() and row["create"].isEnabled()
        with _patched(QMessageBox, question=staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)), \
                _patched(busy, run_in_thread=lambda _window, _text, work, detail="": work()):
            assert tab.write_create_document("rs", row["combo"].currentData())
        assert project.current().is_created("rs") and project.current().content_template("rs") == row["combo"].currentData()
        assert len(window.nav.order()) > 9 and window.pdf_button.isEnabled()
        assert window.tab_widget.currentIndex() == window.project_index()
        tab = window.tabs[window.project_index()]
        assert window.t("pj_content") in tab.document_rows["rs"]["template"].text() and tab.document_rows["rs"]["create"].isHidden()


def test_the_templates_view_previews_a_document_in_the_cache_and_nothing_in_the_project():
    _qt()
    import pdf_pane
    import template_preview
    from PySide6.QtWidgets import QApplication
    here = _skeleton("project_tab_preview", "de")
    asked = []
    with _patched(pdf_pane.PdfPane, request=lambda self, there, mode: asked.append((there, mode))):
        with _window(here) as (window, tab):
            window.show()
            tab.set_view("templates", enter=False)
            assert not tab.workers, "the preview was built while the view was only set"
            tab.set_view("details", enter=False)
            before = sorted(p.relative_to(here.root).as_posix() for p in here.root.rglob("*"))
            tab.preview_document.setCurrentIndex(tab.preview_document.findData("cu"))
            window.on_view_chosen("templates")
            end = time.monotonic() + 120
            while time.monotonic() < end and not asked:
                QApplication.processEvents()
                time.sleep(0.05)
            assert asked, f"no preview was asked for: {tab.preview_banner.text()} {tab.preview_banner.toolTip()} visible={tab.isVisible()} view={tab.view} workers={len(tab.workers)}"
            shown, mode = asked[-1]
            assert mode == "cu" and project._is_within(shown.root, template_preview.folder_for(here)) and shown.is_created("cu")
            assert sorted(p.relative_to(here.root).as_posix() for p in here.root.rglob("*")) == before, "the preview wrote into the project"
            for worker in list(tab.workers):
                worker.wait(60000)


def test_a_change_of_document_brings_projet_forward_and_compiles_nothing_of_a_structure_seen_once():
    """Issue #87: «Structure du document» shown once, then another document chosen from «Projet»: the «Projet» tab in front, and no page of the hidden Structure compiled (its on_mode compiled the whole document until 0.122)."""
    _qt()
    import pdf_pane
    import structure_tab
    from PySide6.QtWidgets import QApplication
    with _window(conftest.project_copy("project_tab_mode")) as (window, tab):
        window.show()
        structure = next(t for t in window.tabs if isinstance(t, structure_tab.StructureTab))
        asked = []
        with _patched(pdf_pane.PdfPane, request=lambda self, *a, **k: asked.append(a), request_snippet=lambda self, *a, **k: asked.append(a)):
            window.tab_widget.setCurrentWidget(structure)
            QApplication.processEvents()
            window.tab_widget.setCurrentIndex(window.project_index())
            QApplication.processEvents()
            asked.clear()
            select = window.nav.mode_select
            other = next(mode for mode in project.MODES if mode != window.mode and project.current().is_created(mode))
            select.setCurrentIndex(select.findData(other))
            QApplication.processEvents()
            assert window.mode == other and window.tab_widget.currentIndex() == window.project_index()
            assert not asked, f"a change of document compiled {asked}"


def test_an_existing_project_is_written_nothing_by_opening_and_by_the_tab():
    """REQ-023, CON-003: a project made before 0.122 -- its language and documents there, no `content_templates` -- opens as before: neither its project file nor data/project.json is rewritten, and its documents say «inconnu»."""
    here = conftest.project_copy("project_tab_existing")
    files = [here.file, here.data_dir / "project.json", here.config_typ]
    before = {str(p): p.read_bytes() for p in files if p.is_file()}
    with _window(here) as (window, tab):
        window.tab_widget.setCurrentIndex(window.project_index())
        tab.on_shown()
        assert all(window.t("pj_unknown") in tab.document_rows[mode]["template"].text() for mode in here.created_modes if not here.content_template(mode))
        tab.on_mode(window.mode)
    assert {str(p): p.read_bytes() for p in files if p.is_file()} == before, "opening an existing project rewrote it"


def test_a_document_not_made_is_out_of_reach_in_its_mode_and_read_only_makes_none():
    """REQ-017, REQ-020, REQ-021, UI-005: the report made alone -- in its standard folder --, the convention d'utilisation stays «pas encore créé»; shown, its mode greys every tab but «Projet», with the tab's words as their tooltip, and offers no «Exporter les trois»; in a project opened read-only «Créer le document…» is off and refused."""
    _qt()
    import busy
    import chrome
    import documents
    import woodcore_gui
    from PySide6.QtWidgets import QMessageBox
    here = _skeleton("project_tab_cu_alone")
    with _window(here) as (window, tab):
        with _patched(QMessageBox, question=staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)), \
                _patched(busy, run_in_thread=lambda _window, _text, work, detail="": work()):
            assert tab.write_create_document("rs", tab.document_rows["rs"]["combo"].currentData())
        here = project.current()
        assert here.document_typ("rs") == here.root / documents.MODE_FOLDERS["rs"] / documents.RS_ENTRY and here.document_typ("rs").is_file()
        tab = window.tabs[window.project_index()]
        assert tab.document_rows["cu"]["template"].text() == window.t("pj_not_made")
        select = window.nav.mode_select
        select.setCurrentIndex(select.findData("cu"))
        assert window.mode == "cu" and window.nav.order() == [window.project_index()]
        other = next(index for index, item in window.nav.rows.items() if index != window.project_index() and not item.isHidden())
        assert window.nav.rows[other].toolTip() == window.t("pj_not_made_tip") and window.nav.rows[other].data(chrome.OFF)
        assert not window.pdf_button.isEnabled()
        assert not any(a.text() == window.t("pdf_all") for a in window.pdf_button.menu().actions()), "«Exporter les trois» offered with one document made"
        window.read_only = True
        tab = window.tabs[window.project_index()]
        tab.lock()
        assert not tab.document_rows["cu"]["create"].isEnabled() and not tab.preview_create.isEnabled()
        import notices_ui
        with _patched(notices_ui, tell=lambda *a, **k: None), _patched(QMessageBox, question=staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)), \
                _patched(busy, run_in_thread=lambda _window, _text, work, detail="": work()):
            tab.write_create_document("cu", tab.document_rows["cu"]["combo"].currentData())
        assert not project.current().is_created("cu"), "a document was made in a project opened read-only"
        window.read_only = False
