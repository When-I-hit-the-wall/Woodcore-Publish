"""*Fichier → Paramètres…* (calc/tools/settings_dialog.py; v0.94, one templates page and one «Enregistrer» since v0.113, the layout and the content templates told apart since 06.10.2026, docs/ui/window.md §10quater).

The dialog has four pages -- Templates, Valeurs par défaut, Langues, Apparence et mises à jour --, each opening on a sentence saying what it is for, and «Enregistrer» left of «Fermer» under them. These hold that **nothing is written until «Enregistrer»**, which writes every setting changed, hands the window its settings afresh, applies the appearance through theme.set_appearance and the window's language through the window's own switch, and closes; that «Fermer» with something pending asks; that the templates page's first switch tells the **layout templates** («templates de forme», calc/forms.py) from the **content templates** («templates de fond», calc/doc_templates.py) -- each kind named and explained in one sentence, never called «modèle» -- and that under «Fond» a second switch shows the content templates of the convention, the base and the report, grouped by place -- Intégrés, Partagés, Mes templates --, a pending shared folder already listed; that no template is made or edited by hand and no project template is offered any more; that *Supprimer* archives and never deletes, a builtin one never; that *Importer un dossier…* copies one template folder of the kind shown into «Mes templates», refuses the wrong kind saying what it is and replaces one of that name only on the engineer's word; that a project's layout is saved as a layout template; that the default layout template is a setting; that a refusal is said in the window's language by its code; and that the File menu offers the dialog with Ctrl+,. «Nouveau projet» and the properties of a project are tests/test_project_dialog.py's.

Built off-screen; every message box and folder dialog a check would meet is replaced first, and every template goes into this process's own folder.
"""

import contextlib
import json
import os
import re
import shutil
import sys

import conftest
from conftest import ROOT

import project
import project_template

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
def _sandbox(name, settings=None):
    """The settings file and the engineer's templates, both redirected into a clean folder of this process for the length of a check -- the suite's own settings file put back after."""
    folder = conftest.tmpdir(name)
    saved = {key: os.environ.get(key) for key in ("WOODCORE_SETTINGS", "WOODCORE_TEMPLATES")}
    os.environ["WOODCORE_SETTINGS"] = str(folder / "settings.json")
    os.environ["WOODCORE_TEMPLATES"] = str(folder / "user")
    (folder / "settings.json").write_text(json.dumps(settings or {"lang": "en", "appearance": "light"}), encoding="utf-8")
    try:
        yield folder
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _settings(folder):
    return json.loads((folder / "settings.json").read_text(encoding="utf-8"))


_MISSING = object()


@contextlib.contextmanager
def _patched(obj, **values):
    """`obj`'s attributes set to `values` for the length of a block, and put back after -- taken away again where `obj` had none (`sys.frozen`)."""
    saved = {name: getattr(obj, name, _MISSING) for name in values}
    for name, value in values.items():
        setattr(obj, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is _MISSING:
                delattr(obj, name)
            else:
                setattr(obj, name, value)


def _said_in_band(said):
    """`notices_ui.inline_error` kept, every text it shows handed to `said` too: a refusal in a modal dialog is said in its own band since v0.117, no box."""
    import notices_ui
    real = notices_ui.inline_error
    return _patched(notices_ui, inline_error=lambda dialog, text: (said.append(text) if text else None, real(dialog, text))[1])


def _dialog(lang="en", here=None, parent=None):
    import settings_dialog
    return settings_dialog.SettingsDialog(parent, lang, here=here)


# --- the frame -------------------------------------------------------------------------------------

def test_the_dialog_has_its_four_pages_each_saying_what_it_is_for_in_three_languages():
    _qt()
    import settings_dialog
    from PySide6.QtWidgets import QLabel
    keys = set(settings_dialog.STRINGS["fr"])
    for lang in ("de", "en"):
        assert set(settings_dialog.STRINGS[lang]) == keys, lang
    assert not any("ß" in text for text in settings_dialog.STRINGS["de"].values()), "Swiss German writes no ß"
    for key, text in settings_dialog.STRINGS["fr"].items():
        assert not re.search(r"\w[:;?!](\s|$)", text), f"French puts a space before a colon: {key} {text!r}"
    notes = {"templates": "prefs_templates_note", "defaults": "prefs_defaults_page_note", "languages": "prefs_languages_page_note", "appearance": "prefs_appearance_page_note"}
    with _sandbox("prefs_frame"):
        for lang in ("fr", "de", "en"):
            dialog = _dialog(lang)
            assert dialog.nav.count() == len(settings_dialog.PAGES) == 4
            assert [dialog.nav.item(i).text() for i in range(4)] == [settings_dialog.STRINGS[lang][f"prefs_page_{key}"] for key in settings_dialog.PAGES]
            for key in settings_dialog.PAGES:
                dialog.show_page(key)
                assert dialog.page() == key and dialog.pages.currentIndex() == settings_dialog.PAGES.index(key)
                said = [label.text() for label in dialog.pages.currentWidget().findChildren(QLabel)]
                assert settings_dialog.STRINGS[lang][notes[key]] in said, f"the page {key} does not say what it is for"
            # a caller of before v0.113 asking for a page that is now on the templates page
            for old in ("documents", "paths"):
                dialog.show_page(old)
                assert dialog.page() == "templates"
            # «Enregistrer» stands left of «Fermer»
            assert dialog.save_button.text() == settings_dialog.STRINGS[lang]["prefs_save"] and dialog.close_button.text() == settings_dialog.STRINGS[lang]["prefs_close"]
            row = dialog.layout().itemAt(1).layout()
            assert 0 <= row.indexOf(dialog.save_button) < row.indexOf(dialog.close_button), "«Enregistrer» is not left of «Fermer»"
            dialog.close()


def test_no_template_is_made_or_edited_by_hand_and_no_project_template_is_offered_any_more():
    _qt()
    with _sandbox("prefs_no_editor"):
        dialog = _dialog()
        for gone in ("props", "editor", "files", "new_button", "duplicate_button", "template_tabs", "section_buttons", "doc_tree", "save_project_button"):
            assert not hasattr(dialog, gone), f"{gone} is still in the dialog"
        import settings_dialog
        assert not [key for key in settings_dialog.STRINGS["fr"] if key.startswith("prefs_tpl_err_")], "the project templates' refusals are still there"
        dialog.close()


def test_a_template_is_never_a_modele_and_each_kind_is_named_and_explained():
    """The engineer's words of 06.10.2026: «template de forme» and «template de fond», never «modèle»; «Formvorlage» and «Inhaltsvorlage»; «layout template» and «content template» -- and one sentence saying what each kind is where it is chosen."""
    _qt()
    import settings_dialog
    fr, de, en = (settings_dialog.STRINGS[lang] for lang in ("fr", "de", "en"))
    assert not [key for key, text in fr.items() if re.search(r"mod[èe]le", text, re.I)], [key for key, text in fr.items() if re.search(r"mod[èe]le", text, re.I)]
    assert (fr["prefs_kind_form"], fr["prefs_kind_content"]) == ("Template de forme", "Template de fond")
    assert (de["prefs_kind_form"], de["prefs_kind_content"]) == ("Formvorlage", "Inhaltsvorlage")
    assert (en["prefs_kind_form"], en["prefs_kind_content"]) == ("Layout template", "Content template")
    assert [fr[f"prefs_place_{p}"] for p in ("builtin", "shared", "user")] == ["Intégrés", "Partagés", "Mes templates"]
    assert [de[f"prefs_place_{p}"] for p in ("builtin", "shared", "user")] == ["Integriert", "Geteilt", "Meine Vorlagen"]
    assert [en[f"prefs_place_{p}"] for p in ("builtin", "shared", "user")] == ["Built-in", "Shared", "My templates"]
    assert "aucune donnée" in fr["prefs_kind_form_note"] and "sections, objets et textes" in fr["prefs_kind_content_note"]
    assert "Chemins" not in "".join(fr.values()), "a page that is gone is still named"


# --- nothing written until «Enregistrer» ----------------------------------------------------------

def _user_form(root, folder, names, description="Ma forme"):
    """A layout template `root/forms/<folder>` made from the builtin neutral one, named `names`."""
    import forms
    target = root / "forms" / folder
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(forms.place_dir("builtin") / "neutral", target)
    meta = json.loads((target / forms.FILE).read_text(encoding="utf-8"))
    meta["name"] = names
    meta["description"] = {lang: description for lang in names}
    (target / forms.FILE).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def test_nothing_is_written_until_save_and_save_writes_everything_and_closes():
    app = _qt()
    import theme
    from PySide6.QtWidgets import QDialog
    with _sandbox("prefs_settings", {"lang": "en", "appearance": "light", "updates": {"skipped": "0.99.0"}}) as folder:
        _user_form(folder / "user", "Holzbau", {"fr": "Holzbau", "de": "Holzbau", "en": "Holzbau"})
        before = _settings(folder)
        parent = type("Window", (), {"settings": {}})()
        dialog = _dialog()
        dialog.window_ = parent
        assert not dialog.dirty()
        dialog.default_fields["author"].setText("L. Exempel")
        dialog.default_fields["company"].setText("Büro Muster")
        assert dialog.default_combo.findData("user:Holzbau") >= 0, [dialog.default_combo.itemData(i) for i in range(dialog.default_combo.count())]
        dialog.default_combo.setCurrentIndex(dialog.default_combo.findData("user:Holzbau"))
        dialog.report_language.setCurrentIndex(dialog.report_language.findData("fr"))
        dialog.updates_box.setChecked(False)
        dialog.appearance.button(theme.APPEARANCES.index("dark")).click()
        dialog.set_shared(str(folder / "office"))
        assert dialog.dirty() and _settings(folder) == before, "a setting was written before «Enregistrer»"
        dialog.default_fields["company"].setText("")
        assert ("defaults", "company") not in dialog.pending
        chosen = []
        with _patched(theme, set_appearance=lambda value, app=None: chosen.append(value)):
            assert dialog.save()
            app.processEvents()
        settings = _settings(folder)
        assert settings["defaults"] == {"author": "L. Exempel", "report_language": "fr"}, settings
        assert settings["forms"] == {"default": "user:Holzbau"} and settings["templates"] == {"shared_folder": str(folder / "office")}, settings
        assert settings["updates"] == {"skipped": "0.99.0", "enabled": False}, "a version set aside was lost, or the update check stayed on"
        assert chosen == ["dark"], "the appearance was not set through theme.set_appearance"
        assert parent.settings == settings, "the window was not handed its settings afresh"
        assert dialog.result() == QDialog.DialogCode.Accepted and not dialog.dirty(), "«Enregistrer» did not close the dialog"
        # again: the update check back on, neutral the default layout template again -- each taken out of the settings rather than written
        dialog = _dialog()
        dialog.updates_box.setChecked(True)
        dialog.default_combo.setCurrentIndex(dialog.default_combo.findData("builtin:neutral"))
        dialog.save()
        settings = _settings(folder)
        assert settings["updates"] == {"skipped": "0.99.0"} and "forms" not in settings, settings


def test_close_with_something_pending_asks_and_without_closes_at_once():
    _qt()
    from PySide6.QtWidgets import QDialog, QMessageBox
    with _sandbox("prefs_close") as folder:
        before = _settings(folder)
        asked = []

        def answer(button):
            return lambda *args, **kwargs: asked.append(args[2]) or button

        dialog = _dialog()
        dialog.show()
        with _patched(QMessageBox, question=answer(QMessageBox.StandardButton.Cancel)):
            dialog.reject()   # nothing pending: closed, nothing asked
        assert not asked and not dialog.isVisible() and dialog.result() == QDialog.DialogCode.Rejected
        import settings_dialog
        dialog = _dialog()
        dialog.show()
        dialog.default_fields["author"].setText("L. Exempel")
        with _patched(QMessageBox, question=answer(QMessageBox.StandardButton.Cancel)):
            dialog.close_button.click()
        assert asked == [settings_dialog.STRINGS["en"]["prefs_unsaved_ask"]] and dialog.isVisible(), "the engineer chose to stay and the dialog closed"
        with _patched(QMessageBox, question=answer(QMessageBox.StandardButton.Discard)):
            dialog.close()   # the title bar's ×
        assert not dialog.isVisible() and _settings(folder) == before, "«Ne pas enregistrer» wrote something"
        dialog = _dialog()
        dialog.show()
        dialog.default_fields["author"].setText("L. Exempel")
        with _patched(QMessageBox, question=answer(QMessageBox.StandardButton.Save)):
            dialog.reject()   # Escape
        assert not dialog.isVisible() and _settings(folder)["defaults"] == {"author": "L. Exempel"}


def test_the_window_language_goes_through_the_window_s_own_switch_on_save():
    app = _qt()
    import chrome
    import settings_dialog
    from PySide6.QtWidgets import QWidget
    with _sandbox("prefs_language") as folder:
        window = QWidget()
        window.language = chrome.LanguageSwitch(settings_dialog.LANGUAGE_NAMES, "en")
        switched = []
        window.language.currentIndexChanged.connect(lambda index: switched.append(window.language.itemData(index)))
        dialog = _dialog("en", parent=window)
        dialog.show_page("languages")
        dialog.window_language.setCurrentIndex(dialog.window_language.findData("de"))
        app.processEvents()
        assert switched == [] and dialog.dirty(), "the window changed its language before «Enregistrer»"
        dialog.window_language.setCurrentIndex(dialog.window_language.findData("en"))
        assert not dialog.dirty(), "the window's own language is pending"
        dialog.window_language.setCurrentIndex(dialog.window_language.findData("de"))
        dialog.save()
        app.processEvents()
        assert switched == ["de"], "the window's own switch was not moved"
        assert "lang" not in _settings(folder) or _settings(folder)["lang"] == "en", "the dialog wrote the language the window's switch writes"
        alone = _dialog("en")
        alone.window_language.setCurrentIndex(alone.window_language.findData("fr"))
        assert _settings(folder)["lang"] == "en"
        alone.save()
        assert _settings(folder)["lang"] == "fr"


# --- the templates: Forme | Fond, the three documents, three places ------------------------------------

def _office(folder):
    """The settings naming `folder/office` the office's shared folder, written."""
    settings = {"lang": "en", "appearance": "light", "templates": {"shared_folder": str(folder / "office")}}
    (folder / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    return settings


def test_the_switch_shows_the_layout_templates_and_the_content_templates_of_each_document_grouped_by_place():
    _qt()
    import doc_templates
    import documents
    import forms
    import settings_dialog
    import theme
    from PySide6.QtGui import QColor
    with _sandbox("prefs_switch") as folder:
        _office(folder)
        office, user = folder / "office", folder / "user"
        _user_form(user, "holzbau", {"fr": "Holzbau"})
        _user_form(office, "bureau", {"fr": "Forme du bureau"})
        _doc_template(user, "cu", "courte", {"fr": "Convention courte", "de": "Kurze Vereinbarung"}, ("fr", "de"))
        _doc_template(user, "bp", "kurz", {"de": "Kurze Basis"}, ("de",))
        _doc_template(office, "cu", "bureau", {"fr": "Convention du bureau", "en": "Office agreement"}, ("fr", "en"))
        _doc_template(user, "rs", "predim", {"fr": "Rapport de prédimensionnement"}, ("fr",))
        broken = user / "documents" / "bp" / "kaputt"
        broken.mkdir(parents=True)
        (broken / doc_templates.FILE).write_text("{}", encoding="utf-8")
        dialog = _dialog("fr")
        t = settings_dialog.STRINGS["fr"]
        builtin, shared, own = t["prefs_place_builtin"], t["prefs_place_shared"], t["prefs_place_user"]
        # the kinds: the layout templates first, each kind said in one sentence, no document switch
        assert [dialog.kind_buttons[k].text() for k in settings_dialog.KINDS] == [t["prefs_kind_form"], t["prefs_kind_content"]]
        assert dialog.kind == "form" and dialog.kind_buttons["form"].isChecked() and dialog.kind_note.text() == t["prefs_kind_form_note"]
        assert dialog.document_box.isHidden() and not dialog.save_form_button.isHidden()
        neutral = forms.find("builtin:neutral").name("fr")
        listed = dialog.groups()
        assert listed[builtin][0] == t["prefs_default_mark"].format(name=neutral) and len(listed[builtin]) == len([f for f in forms.list_forms({}) if f.place == "builtin"]), listed
        assert listed[shared] == ["Forme du bureau"] and listed[own] == ["Holzbau"], listed
        assert list(listed) == [builtin, shared, own], "the places are not in the engineer's order"
        assert dialog.choose("user:holzbau") and dialog.details["languages"].text() == t["prefs_lang_any"] and dialog.details["place"].text() == own
        # the content templates: the documents' switch, the convention first
        dialog.kind_buttons["content"].click()
        assert dialog.kind == "content" and dialog.kind_note.text() == t["prefs_kind_content_note"] and not dialog.document_box.isHidden() and dialog.save_form_button.isHidden()
        assert [dialog.document_buttons[mode].text() for mode in settings_dialog.DOCUMENTS] == [documents.mode_name(mode, "fr") for mode in ("cu", "bp", "rs")]
        assert dialog.document == "cu" and dialog.groups() == {builtin: ["Convention d'utilisation — standard"], shared: ["Convention du bureau"], own: ["Convention courte"]}, dialog.groups()
        dialog.document_buttons["bp"].click()
        assert dialog.document == "bp" and dialog.groups() == {builtin: ["Base de projet — standard"], shared: [], own: ["kaputt", "Kurze Basis"]}, dialog.groups()
        assert dialog.tree.topLevelItem(1).child(0).text(0) == t["prefs_place_empty"]
        bad = dialog.tree.topLevelItem(2).child(0)
        assert doc_templates.read(broken, "bp", "user").error in bad.toolTip(0) and bad.foreground(0).color() == QColor(theme.colour("muted"))
        assert dialog.choose("user:bp/kaputt") and not dialog.detail_error.isHidden() and "kaputt" in dialog.details["name"].text()
        # the report has content templates of its own
        dialog.document_buttons["rs"].click()
        assert dialog.groups() == {builtin: ["Rapport de statique — standard"], shared: [], own: ["Rapport de prédimensionnement"]}, dialog.groups()
        rows = {dialog.tree.topLevelItem(g).child(c).text(0): dialog.tree.topLevelItem(g).child(c).text(1) for g in range(3) for c in range(dialog.tree.topLevelItem(g).childCount())}
        assert rows["Rapport de prédimensionnement"] == "fr", rows
        dialog.document_buttons["cu"].click()
        rows = {dialog.tree.topLevelItem(g).child(c).text(0): dialog.tree.topLevelItem(g).child(c).text(1) for g in range(3) for c in range(dialog.tree.topLevelItem(g).childCount())}
        assert rows["Convention courte"] == "fr, de" and rows["Convention du bureau"] == "fr, en", rows
        assert dialog.choose("user:cu/courte")
        details = {key: label.text() for key, label in dialog.details.items()}
        assert details["name"] == "Convention courte" and details["place"] == own and details["folder"] == str(user / "documents" / "cu" / "courte"), details
        # a caller asking for the content templates of a document opens on them
        report = settings_dialog.SettingsDialog(None, "fr", document="rs", kind="content")
        assert report.kind == "content" and report.document == "rs"
        report.close()
        dialog.close()


def test_a_pending_shared_folder_lists_its_templates_and_writes_nothing():
    _qt()
    import settings_dialog
    with _sandbox("prefs_shared") as folder:
        office = folder / "office"
        _user_form(office, "bureau", {"en": "Office layout"})
        _doc_template(office, "cu", "bureau", {"fr": "Convention du bureau"}, ("fr",))
        before = _settings(folder)
        dialog = _dialog()
        t = settings_dialog.STRINGS["en"]
        shared = t["prefs_place_shared"]
        assert dialog.groups()[shared] == [] and dialog.tree.topLevelItem(1).child(0).text(0) == t["prefs_place_unset"]
        dialog.set_shared(str(office))
        assert dialog.groups()[shared] == ["Office layout"] and _settings(folder) == before, "the shared folder was written before «Enregistrer»"
        assert "shared:bureau" in [dialog.default_combo.itemData(i) for i in range(dialog.default_combo.count())], "the default combo does not see the pending folder"
        dialog.set_document("cu")
        assert dialog.kind == "content" and dialog.groups()[shared] == ["Convention du bureau"]
        dialog.set_shared(str(folder / "nowhere"))
        assert dialog.tree.topLevelItem(1).text(0) == t["prefs_place_missing"].format(place=shared)
        dialog.set_shared("")
        assert not dialog.dirty(), "a folder taken out again is still pending"
        dialog.close()


def test_a_template_is_deleted_into_its_place_s_archives_and_a_builtin_one_cannot_be():
    _qt()
    import doc_templates
    import forms
    import settings_dialog
    from PySide6.QtWidgets import QMessageBox
    with _sandbox("prefs_delete") as folder:
        settings = _office(folder)
        user, office = folder / "user", folder / "office"
        _doc_template(user, "cu", "courte", {"fr": "Convention courte"}, ("fr",))
        _doc_template(office, "cu", "bureau", {"fr": "Convention du bureau"}, ("fr",))
        dialog = _dialog("fr")
        dialog.set_document("cu")
        t = settings_dialog.STRINGS["fr"]
        assert not dialog.delete_button.isEnabled() and dialog.delete_button.toolTip() == t["prefs_pick"] and not dialog.folder_button.isEnabled()
        assert dialog.choose("builtin:cu/standard")
        assert not dialog.delete_button.isEnabled() and dialog.delete_button.toolTip() == t["prefs_read_only"] and dialog.folder_button.isEnabled()
        assert dialog.delete_template(confirm=False) is None and doc_templates.find("builtin:cu/standard").folder.is_dir()
        assert dialog.choose("user:cu/courte") and dialog.delete_button.isEnabled() and dialog.delete_button.toolTip() == ""
        with _patched(QMessageBox, question=lambda *args, **kwargs: QMessageBox.StandardButton.No):
            assert dialog.delete_template() is None
        assert (user / "documents" / "cu" / "courte").is_dir(), "a template was moved though the engineer said no"
        with _patched(QMessageBox, question=lambda *args, **kwargs: QMessageBox.StandardButton.Yes):
            archived = dialog.delete_template()
        assert archived.parent == user / "documents" / "archives" and (archived / doc_templates.FILE).is_file() and not (user / "documents" / "cu" / "courte").exists()
        assert "Convention courte" in dialog.status.text() and str(archived) in dialog.status.text(), "the engineer is not told where it went"
        assert dialog.choose("office:cu/bureau") and dialog.delete_template(confirm=False).parent == office / "documents" / "archives"
        # a layout template is archived too, never deleted -- and where it was the default, neutral is again, at once
        mine = _user_form(user, "holzbau", {"fr": "Holzbau"})
        (folder / "settings.json").write_text(json.dumps(dict(settings, forms={"default": "user:holzbau"})), encoding="utf-8")
        dialog = _dialog("fr")
        assert dialog.kind == "form" and dialog.choose("builtin:neutral") and not dialog.delete_button.isEnabled()
        assert dialog.choose("user:holzbau")
        gone = dialog.delete_template(confirm=False)
        assert gone.parent == user / "forms" / forms.ARCHIVES and (gone / forms.FILE).is_file() and not mine.exists()
        assert "forms" not in _settings(folder), "the default archived stayed the default"
        assert not dialog.dirty()
        dialog.close()


def test_a_folder_is_imported_into_my_templates_as_a_template_of_the_kind_shown():
    _qt()
    import settings_dialog
    from PySide6.QtWidgets import QFileDialog, QMessageBox
    with _sandbox("prefs_import") as folder:
        _office(folder)
        office = folder / "office"
        form_source = _user_form(office, "bureau", {"en": "Office layout"})
        doc_source = _doc_template(office, "cu", "bureau", {"fr": "Convention du bureau", "en": "Office agreement"}, ("fr", "en"))
        dialog = _dialog("en")
        t = settings_dialog.STRINGS["en"]
        assert dialog.import_button.toolTip() == t["prefs_import_tip_form"]
        warned = []
        with _patched(QFileDialog, getExistingDirectory=lambda *args, **kwargs: ""):
            assert dialog.import_template() is None
        with _patched(QFileDialog, getExistingDirectory=lambda *args, **kwargs: str(form_source)):
            made = dialog.import_template()
        assert made.ref == "user:bureau" and made.place == "user" and dialog.current_ref() == made.ref
        assert dialog.groups()[t["prefs_place_user"]] == ["Office layout"] and dialog.status.text() == t["prefs_import_done"].format(name="Office layout")
        assert "user:bureau" in [dialog.default_combo.itemData(i) for i in range(dialog.default_combo.count())]
        # the wrong kind: refused, saying what it is
        with _said_in_band(warned):
            assert dialog.import_template(str(doc_source)) is None
            dialog.set_document("cu")
            assert dialog.import_button.toolTip() == t["prefs_import_tip_content"]
            assert dialog.import_template(str(form_source)) is None
        assert warned[0] == t["prefs_import_failed"].format(error=t["prefs_form_err_no_form"].format(folder=doc_source)), warned[0]
        assert warned[1].startswith(t["prefs_import_failed"].split("{")[0]) and "English" not in warned[1], warned[1]
        made = dialog.import_template(str(doc_source))
        assert made.ref == "user:cu/bureau" and dialog.groups()[t["prefs_place_user"]] == ["Office agreement"]
        # one of that folder's name there already: asked, kept on a no, replaced and archived on a yes
        dialog.set_kind("form")
        mine = folder / "user" / "forms" / "bureau"
        (mine / "marker.txt").write_text("old\n", encoding="utf-8")
        asked = []
        with _patched(QMessageBox, question=lambda *args, **kwargs: asked.append(args[2]) or QMessageBox.StandardButton.No):
            assert dialog.import_template(str(form_source)) is None
        assert asked == [t["prefs_import_replace_ask"].format(folder="bureau")] and (mine / "marker.txt").is_file()
        with _patched(QMessageBox, question=lambda *args, **kwargs: QMessageBox.StandardButton.Yes):
            again = dialog.import_template(str(form_source))
        assert again.ref == "user:bureau" and not (again.folder / "marker.txt").exists()
        assert not dialog.dirty(), "an import is an action on files, not a setting"
        dialog.close()


def test_a_project_s_layout_is_saved_as_a_layout_template_from_the_dialog():
    _qt()
    import forms
    import settings_dialog
    from PySide6.QtWidgets import QMessageBox
    with _sandbox("prefs_save_form") as folder:
        here = project_template.create(folder / "Quelle", "Quelle", company="Büro Muster")
        alone = _dialog()
        assert not alone.save_form_button.isEnabled() and alone.save_form_button.toolTip() == settings_dialog.STRINGS["en"]["prefs_no_project"], "offered where no project is open"
        if forms.current(here) is None:
            # a project whose look is still one config.typ: refused, saying so in the window's words
            dialog = _dialog(here=here)
            said = []
            with _patched(QMessageBox, warning=lambda *args, **kwargs: said.append(args[2])):
                assert dialog.save_form("Aus Quelle") is None
            assert said == [settings_dialog.STRINGS["en"]["prefs_failed"].format(error=settings_dialog.STRINGS["en"]["prefs_form_err_no_project_form"])], said
            forms.apply(here, forms.find("builtin:bfh"))
        dialog = _dialog(here=here)
        dialog.set_document("bp")
        assert dialog.save_form_button.isHidden() and dialog.save_form_button.isEnabled()
        made = dialog.save_form("Aus Quelle")
        assert made.ref.startswith("user:") and made.name("en") == "Aus Quelle" and dialog.kind == "form" and dialog.current_ref() == made.ref
        assert (made.folder / forms.TEMPLATE_FILE).is_file() and (made.folder / forms.TITLE_FILE).is_file() and not dialog.dirty()
        assert dialog.status.text() == settings_dialog.STRINGS["en"]["prefs_saved_form"].format(name="Aus Quelle")
        dialog.close()


# --- the refusals ----------------------------------------------------------------------------------

def _doc_template(root, mode, folder, names, languages):
    """A content template `root/documents/<mode>/<folder>` made from the builtin one, with the languages and names given."""
    import doc_templates
    builtin = doc_templates.find(f"builtin:{mode}/standard")
    target = root / "documents" / mode / folder
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(builtin.folder, target)
    for lang in doc_templates.LANGUAGES:
        if lang not in languages:
            shutil.rmtree(target / lang)
    meta = {"schema_version": "1.0", "format": doc_templates.FORMAT, "mode": mode,
            "name": {lang: names[lang] for lang in doc_templates.LANGUAGES if lang in languages},
            "description": {lang: f"{names[lang]} — description" for lang in doc_templates.LANGUAGES if lang in languages},
            "languages": [lang for lang in doc_templates.LANGUAGES if lang in languages]}
    (target / doc_templates.FILE).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def test_a_refused_deletion_is_said_in_the_window_s_language_by_its_code():
    _qt()
    import doc_templates
    import settings_dialog
    from PySide6.QtWidgets import QMessageBox
    with _sandbox("prefs_documents_refused") as folder:
        _doc_template(folder / "user", "cu", "courte", {"fr": "Convention courte"}, ("fr",))
        for lang in ("fr", "de", "en"):
            dialog = _dialog(lang)
            dialog.set_document("cu")
            assert dialog.choose("user:cu/courte")
            said = []

            def refuse(*args, **kwargs):
                raise doc_templates.DocTemplateError("disk full (English)", "write_failed", error="disque plein")

            with _patched(doc_templates, delete=refuse), _said_in_band(said):
                assert dialog.delete_template(confirm=False) is None
            expected = settings_dialog.STRINGS[lang]["prefs_failed"].format(error=settings_dialog.STRINGS[lang]["prefs_doc_err_write_failed"].format(error="disque plein"))
            assert said == [expected], (lang, said)
            assert "English" not in said[0], "the exception's English sentence reached the window"
            assert (folder / "user" / "documents" / "cu" / "courte").is_dir() and dialog.current_ref() == "user:cu/courte"
            dialog.close()


def test_every_refusal_code_of_the_layout_templates_has_a_sentence_in_three_languages():
    _qt()
    import forms
    import settings_dialog
    for lang in ("fr", "de", "en"):
        table = settings_dialog.STRINGS[lang]
        assert {key[len("prefs_form_err_"):] for key in table if key.startswith("prefs_form_err_")} == set(forms.CODES)
        for code in forms.CODES:
            exc = forms.FormError("an English sentence", code, place="x", ref="user:x", name="x", folder="x", error="boom")
            for text in (settings_dialog.form_error_text(lang, exc), settings_dialog.import_error_text(lang, exc)):
                assert text and "{" not in text and "English sentence" not in text, (lang, code, text)
        assert settings_dialog.form_error_text(lang, forms.FormError("only English", "")) == "only English"
    try:
        forms.archive(forms.find("builtin:neutral"))
    except forms.FormError as exc:
        assert exc.code == "read_only" and settings_dialog.form_error_text("fr", exc) == settings_dialog.STRINGS["fr"]["prefs_form_err_read_only"]
    else:
        raise AssertionError("a builtin layout template was archived")


def test_every_refusal_code_of_the_document_templates_has_a_sentence_in_three_languages():
    """`doc_error_text` reads a DocTemplateError by its `code` -- every code of doc_templates.CODES has a sentence in French, German and English, formatted with the values the refusal states, a list written as its items; an exception that states no code, or one the table does not know, is the English sentence itself. The real refusals of `find`, `delete` and `instantiate` are read by it."""
    _qt()
    import doc_templates
    import settings_dialog
    for lang in ("fr", "de", "en"):
        table = settings_dialog.STRINGS[lang]
        for code in doc_templates.CODES:
            assert table.get(f"prefs_doc_err_{code}"), f"{code} has no sentence in {lang}"
        assert not [key for key in table if key.startswith("prefs_doc_err_") and key[len("prefs_doc_err_"):] not in doc_templates.CODES], "a sentence for a code the module does not state"
        assert "ß" not in "".join(v for k, v in table.items() if k.startswith("prefs_doc")), "Swiss German writes no ß"
        for code in doc_templates.CODES:
            exc = doc_templates.DocTemplateError("an English sentence", code, mode="cu", language="de", languages=["fr", "en"], place="user", folder="x", ref="user:cu/x",
                                                 name="x", files=["a.typ", "b.typ"], file="e.typ", error="boom")
            text = settings_dialog.doc_error_text(lang, exc)
            assert text and "{" not in text and "English sentence" not in text, (lang, code, text)
        bare = doc_templates.DocTemplateError("only English", "")
        assert settings_dialog.doc_error_text(lang, bare) == "only English"
        assert settings_dialog.doc_error_text(lang, doc_templates.DocTemplateError("a new refusal", "not_a_code")) == "a new refusal"
        assert settings_dialog.doc_error_text(lang, ValueError("not ours")) == "not ours"
        listed = settings_dialog.doc_error_text(lang, doc_templates.DocTemplateError("x", "section_missing", files=["a.typ", "b.typ"]))
        assert "a.typ, b.typ" in listed, listed
    for lang in ("fr", "de", "en"):
        try:
            doc_templates.delete("builtin:cu/standard")
        except doc_templates.DocTemplateError as exc:
            assert exc.code == "read_only" and settings_dialog.doc_error_text(lang, exc) == settings_dialog.STRINGS[lang]["prefs_doc_err_read_only"]
        else:
            raise AssertionError("a builtin template was deleted")
        try:
            doc_templates.find("nirgendwo", "cu")
        except doc_templates.DocTemplateError as exc:
            assert exc.code == "no_such_template" and "nirgendwo" in settings_dialog.doc_error_text(lang, exc)
        else:
            raise AssertionError("a template that does not exist was found")
    with _sandbox("prefs_documents_codes") as folder:
        only_french = doc_templates.read(_doc_template(folder / "user", "cu", "nur-fr", {"fr": "Nur französisch"}, ("fr",)), "cu", "user")
        try:
            doc_templates.instantiate("cu", "de", folder / "target", template=only_french)
        except doc_templates.DocTemplateError as exc:
            assert exc.code == "language_missing"
            for lang in ("fr", "de", "en"):
                text = settings_dialog.doc_error_text(lang, exc)
                assert "user:cu/nur-fr" in text and "fr" in text and "de" in text, text
        else:
            raise AssertionError("a French template was made into a German document")


# --- the File menu -------------------------------------------------------------------------------

def test_the_file_menu_offers_the_settings_with_ctrl_comma():
    conftest.exported("calculations.json")
    _qt()
    import woodcore_gui
    import settings_dialog
    from PySide6.QtGui import QKeySequence
    window = woodcore_gui.MainWindow()
    try:
        menu = window.menuBar().actions()[0].menu()
        action = next((a for a in menu.actions() if a.text() == settings_dialog.menu_text(window.lang)), None)
        assert action is not None, [a.text() for a in menu.actions()]
        assert action.shortcut() == QKeySequence("Ctrl+,")
        opened = []
        with _patched(settings_dialog, open_dialog=lambda parent, lang, here=None, page="templates", **kwargs: opened.append((parent, lang, here))):
            action.trigger()
        assert opened == [(window, window.lang, project.current())]
    finally:
        conftest.dispose(window)