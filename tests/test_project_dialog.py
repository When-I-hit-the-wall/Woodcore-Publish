"""«Nouveau projet» and «Propriétés du projet» (calc/tools/home_page.py, ProjectDialog): a project made from one **layout template** and three **content templates**, and its layout template switched from its properties (the engineer's decision of 06.10.2026, docs/ui/window.md §10quater).

What is held here: that «Nouveau projet» offers the layout templates («templates de forme», calc/forms.py), the settings' default first, each with its description, and one combo of content templates («templates de fond», calc/doc_templates.py) for each of the three documents -- the convention, the base and the report --, listed in the language chosen and again when it changes, the choice kept where it can be; that no project template and no style is offered any more, the people and the language coming from the settings' defaults; that the three documents' folders follow the language until typed into, each one folder and the three different; that what is chosen reaches the project made; that the properties show the layout template the project is written in -- or that its look is an old config.typ -- and that choosing another asks first and then switches it, the old one archived; and that every word is in three languages and never calls a template a «modèle».

Built off-screen; every message box a check would meet is replaced first, and every template goes into this process's own folder.
"""

import contextlib
import json
import os
import re
import shutil
import sys
import types

import conftest
from conftest import ROOT

import project

TOOLS = ROOT / "calc" / "tools"
MARK = "MODELEMARQUEUR"


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


@contextlib.contextmanager
def _sandbox(name, settings=None):
    """The settings file, the engineer's templates and the office's folder (named in the settings) redirected into a clean folder of this process for the length of a check. Yields `base`, `user` and `office`."""
    base = conftest.tmpdir(name)
    saved = {key: os.environ.get(key) for key in ("WOODCORE_SETTINGS", "WOODCORE_TEMPLATES")}
    os.environ["WOODCORE_SETTINGS"] = str(base / "settings.json")
    os.environ["WOODCORE_TEMPLATES"] = str(base / "user")
    written = {"lang": "en", "appearance": "light", "templates": {"shared_folder": str(base / "office")}}
    written.update(settings or {})
    (base / "settings.json").write_text(json.dumps(written), encoding="utf-8")
    try:
        yield types.SimpleNamespace(base=base, user=base / "user", office=base / "office")
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _doc_template(root, mode, folder, names, languages, marker=MARK):
    """A content template `root/documents/<mode>/<folder>` made from the builtin one -- the languages it has only, the names given, `marker` written into the first section of each language."""
    import doc_templates
    import structure
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
    if marker and mode != "rs":
        for lang in languages:
            first = structure.leaves(structure.read(target / lang / structure.FILE))[0][0]
            with open(target / lang / first["file"], "a", encoding="utf-8", newline="") as handle:
                handle.write(f"\n{marker}\n")
    return target


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


def _offered(dialog, mode):
    combo = dialog.doc_template_combos[mode]
    return [combo.itemData(i) for i in range(combo.count())]


# --- «Nouveau projet» -------------------------------------------------------------------------------

def test_the_dialog_offers_the_layout_templates_the_default_first_and_no_project_template_or_style():
    _qt()
    import forms
    import home_page
    with _sandbox("pd_forms", {"forms": {"default": "user:holzbau"}}) as ctx:
        _user_form(ctx.user, "holzbau", {"fr": "Holzbau", "en": "Timber"}, "Pour les halles")
        dialog = home_page.ProjectDialog(None, "en", "new", location=ctx.base)
        offered = [dialog.form_combo.itemData(i) for i in range(dialog.form_combo.count())]
        assert offered == [f.ref for f in forms.list_forms() if not f.error], offered
        assert dialog.form_combo.currentData() == "user:holzbau", "the settings' default layout template is not the one chosen first"
        assert dialog.form_combo.currentText() == "Timber — " + home_page.settings_dialog.place_label("en", "user")
        assert dialog.form_note.text() == "Pour les halles" and "Pour les halles" in dialog.form_combo.toolTip()
        assert home_page.STRINGS["en"]["proj_form_hint"] in dialog.form_combo.toolTip()
        dialog.form_combo.setCurrentIndex(dialog.form_combo.findData("builtin:bfh"))
        assert dialog.form_note.text() == forms.find("builtin:bfh").description("en") and dialog.values()["form"] == "builtin:bfh"
        for gone in ("template", "style_combo", "templates", "styles"):
            assert not hasattr(dialog, gone), f"{gone} is still in the dialog"
    with _sandbox("pd_forms_default"):
        dialog = home_page.ProjectDialog(None, "fr", "new")
        assert dialog.form_combo.currentData() == "builtin:neutral"


def test_the_people_and_the_language_are_the_settings_defaults():
    _qt()
    import home_page
    with _sandbox("pd_people", {"defaults": {"company": "Büro Muster", "author": "M. Muster", "report_language": "fr"}}) as ctx:
        dialog = home_page.ProjectDialog(None, "en", "new", location=ctx.base)
        assert (dialog.fields["company"].text(), dialog.fields["author"].text(), dialog.fields["checker"].text()) == ("Büro Muster", "M. Muster", "")
        assert dialog.language.currentData() == "fr"


def test_a_new_project_names_its_three_documents_folders():
    """«Nouveau projet» offers the three documents' folders (the engineer's decision of 30.09.2026): each prefilled with calc/documents.py's names for the language chosen, following the language until the engineer types into it, each one folder and not a path, and the three different -- refused in the dialog, before anything is made."""
    _qt()
    import documents
    import home_page
    from PySide6.QtWidgets import QDialog, QLabel
    with _sandbox("pd_folders", {"defaults": {"report_language": "de"}}) as ctx:
        folder = ctx.base
        dialog = home_page.ProjectDialog(None, "en", "new", location=folder)
        typed = lambda: {mode: field.text() for mode, field in dialog.doc_folders.items()}  # noqa: E731
        assert list(dialog.doc_folders) == list(project.MODES)
        assert typed() == documents.MODE_FOLDERS["de"]
        dialog.language.setCurrentIndex(dialog.language.findData("fr"))
        assert typed() == documents.MODE_FOLDERS["fr"], "the folders did not follow the language"
        dialog.doc_folders["cu"].setText("NV Halle")
        dialog.language.setCurrentIndex(dialog.language.findData("de"))
        assert typed() == {**documents.MODE_FOLDERS["de"], "cu": "NV Halle"}, "a folder the engineer typed was overwritten"
        t = home_page.STRINGS["en"]
        dialog.doc_folders["bp"].setText("nv halle")
        assert dialog.folders_problem() == t["proj_doc_folders_same"].format(first=documents.mode_name("cu", "en"), second=documents.mode_name("bp", "en"))
        dialog.doc_folders["bp"].setText("a/b")
        assert "separator" in dialog.folders_problem()
        dialog.doc_folders["bp"].setText("  ")
        assert dialog.folders_problem() == t["proj_doc_folder_needed"].format(document=documents.mode_name("bp", "en"))
        dialog.fields["name"].setText("Halle")
        dialog.accept()
        band = dialog.findChild(QLabel, "dialogError")   # said in the dialog's own band since v0.117 (notices_ui.inline_error), no box
        assert band is not None and band.text() == t["proj_doc_folder_needed"].format(document=documents.mode_name("bp", "en")) and not band.isHidden()
        assert dialog.result() != QDialog.DialogCode.Accepted, "a folder without a name was accepted"
        dialog.doc_folders["bp"].setText("PB")
        assert dialog.folders_problem() is None
        assert dialog.values()["folders"] == {"cu": "NV Halle", "bp": "PB", "rs": documents.MODE_FOLDERS["de"]["rs"]}


def test_the_dialog_offers_the_content_templates_of_the_three_documents_in_the_language_chosen_and_keeps_the_choice_where_it_can():
    _qt()
    import doc_templates
    import home_page
    from PySide6.QtCore import Qt
    with _sandbox("pd_content") as ctx:
        _doc_template(ctx.user, "cu", "courte", {"fr": "Convention courte"}, ("fr",))
        _doc_template(ctx.user, "bp", "kurz", {"de": "Kurze Basis"}, ("de",))
        _doc_template(ctx.office, "cu", "bureau", {"fr": "Convention du bureau", "en": "Office agreement"}, ("fr", "en"))
        _doc_template(ctx.user, "rs", "predim", {"fr": "Prédimensionnement"}, ("fr",))
        dialog = home_page.ProjectDialog(None, "en", "new", location=ctx.base)
        assert list(dialog.doc_template_combos) == ["cu", "bp", "rs"]

        def language(code):
            dialog.language.setCurrentIndex(dialog.language.findData(code))

        language("fr")
        assert _offered(dialog, "cu") == ["builtin:cu/standard", "user:cu/courte", "office:cu/bureau"], _offered(dialog, "cu")
        assert _offered(dialog, "bp") == ["builtin:bp/standard"], "a template written in German offered for a French project"
        assert _offered(dialog, "rs") == ["builtin:rs/standard", "user:rs/predim"], _offered(dialog, "rs")
        language("de")
        assert _offered(dialog, "cu") == ["builtin:cu/standard"] and _offered(dialog, "bp") == ["builtin:bp/standard", "user:bp/kurz"] and _offered(dialog, "rs") == ["builtin:rs/standard"]
        language("en")
        for mode, combo in dialog.doc_template_combos.items():
            assert combo.currentData() == f"builtin:{mode}/standard" and combo.isEnabled(), "the builtin standard template is not the one chosen at first"
        cu = dialog.doc_template_combos["cu"]
        assert [cu.itemText(i) for i in range(cu.count())] == ["Service criteria agreement — standard", "Office agreement — Shared"], [cu.itemText(i) for i in range(cu.count())]
        in_french = home_page.ProjectDialog(None, "fr", "new", location=ctx.base)
        in_french.language.setCurrentIndex(in_french.language.findData("fr"))
        fr_cu = in_french.doc_template_combos["cu"]
        assert [fr_cu.itemText(i) for i in range(fr_cu.count())] == ["Convention d'utilisation — standard", "Convention courte — Mes templates", "Convention du bureau — Partagés"]
        # the description is the tooltip, of the item and -- after what a content template is -- of the combo
        language("fr")
        cu.setCurrentIndex(cu.findData("user:cu/courte"))
        assert cu.itemData(cu.currentIndex(), Qt.ItemDataRole.ToolTipRole) == "Convention courte — description" and cu.toolTip().endswith("Convention courte — description")
        assert cu.toolTip().startswith(home_page.STRINGS["en"]["proj_content_hint"])
        # a choice stays where the language still offers it, and is the standard one where it does not
        cu.setCurrentIndex(cu.findData("office:cu/bureau"))
        language("en")
        assert cu.currentData() == "office:cu/bureau"
        language("de")
        assert cu.currentData() == "builtin:cu/standard"
        language("fr")
        assert cu.currentData() == "builtin:cu/standard"
        cu.setCurrentIndex(cu.findData("office:cu/bureau"))
        rs = dialog.doc_template_combos["rs"]
        rs.setCurrentIndex(rs.findData("user:rs/predim"))
        assert dialog.values()["document_templates"] == {"cu": "office:cu/bureau", "bp": "builtin:bp/standard", "rs": "user:rs/predim"}
        chosen = dialog.chosen_document_templates()
        assert set(chosen) == {"cu", "bp", "rs"} and all(isinstance(t, doc_templates.DocTemplate) for t in chosen.values())
        assert chosen["cu"].folder == ctx.office / "documents" / "cu" / "bureau" and chosen["cu"].place == "office"
        assert not hasattr(home_page.ProjectDialog(None, "en", "properties", data={"name": "X"}), "doc_template_combos")


def test_the_dialog_hands_the_chosen_templates_to_the_project_it_makes():
    """«Nouveau projet» as create_project runs it: the layout template and the office's convention d'utilisation chosen in French reach the project -- the layout template is the one it is written in, the convention's text is the template's -- and the base left as it was is the builtin one; the report's content template is handed over too."""
    _qt()
    import documents
    import forms
    import home_page
    import project_template
    import structure
    from PySide6.QtWidgets import QDialog
    with _sandbox("pd_create") as ctx:
        _doc_template(ctx.office, "cu", "bureau", {"fr": "Convention du bureau"}, ("fr",))
        _doc_template(ctx.user, "rs", "predim", {"fr": "Prédimensionnement"}, ("fr",))

        def accept(self):
            self.fields["name"].setText("Scheune")
            self.language.setCurrentIndex(self.language.findData("fr"))
            self.form_combo.setCurrentIndex(self.form_combo.findData("builtin:compact"))
            combo = self.doc_template_combos["cu"]
            combo.setCurrentIndex(combo.findData("office:cu/bureau"))
            report = self.doc_template_combos["rs"]
            report.setCurrentIndex(report.findData("user:rs/predim"))
            return QDialog.DialogCode.Accepted

        import functools
        handed = []
        real = project_template.create

        @functools.wraps(real)      # the signature the dialog reads (inspect follows __wrapped__)
        def create(*args, **kwargs):
            handed.append(kwargs)
            return real(*args, **kwargs)

        with _patched(home_page.ProjectDialog, exec=accept), _patched(project_template, create=create):
            file = home_page.create_project(None, "en", ctx.base / "projects")
        assert file is not None, "the creation failed"
        assert handed and handed[0]["document_templates"]["rs"].ref == "user:rs/predim", "the report's content template was not handed to create"
        assert handed[0]["document_language"] == handed[0]["report_language"] == "fr"
        assert "template" not in handed[0] and "style" not in handed[0], "a project template or a style is still handed over"
        here = project.Project.load(file)
        assert forms.current(here) is not None and forms.current(here).ref == "builtin:compact", "the layout template chosen is not the one the project is written in"
        first = lambda mode: structure.leaves(structure.read(here.structure_file(mode)))[0][0]["file"]  # noqa: E731
        assert MARK in (here.document_dir("cu") / first("cu")).read_text(encoding="utf-8"), "the content template chosen did not reach the project"
        assert MARK not in (here.document_dir("bp") / first("bp")).read_text(encoding="utf-8"), "the other document is not the builtin one"
        assert here.document_typ("cu").name == documents.ENTRY_NAMES["fr"]["cu"]


# --- «Propriétés du projet» ------------------------------------------------------------------------

def _new_project(name, **kwargs):
    import project_template
    kwargs.setdefault("document_language", "fr")
    kwargs.setdefault("report_language", "fr")
    return project_template.create(conftest.tmpdir(name) / "Halle", "Halle", author="L. Exempel", **kwargs)


def _accepting(form=None, **fields):
    """ProjectDialog.exec replaced by one that sets what it is told and accepts, as the engineer's clicks do."""
    from PySide6.QtWidgets import QDialog

    def accept(self):
        if form is not None:
            self.form_combo.setCurrentIndex(self.form_combo.findData(form))
        for key, value in fields.items():
            self.fields[key].setText(value)
        return QDialog.DialogCode.Accepted
    return accept


def test_the_properties_show_the_layout_template_the_project_has_or_its_old_config():
    _qt()
    import forms
    import home_page
    for lang in ("fr", "de", "en"):
        old = home_page.ProjectDialog(None, lang, "properties", data={"name": "Halle", "form": ""})
        assert old.form_combo.itemText(0) == home_page.STRINGS[lang]["proj_form_old"] and old.form_combo.currentData() == "" and old.values()["form"] == ""
        assert home_page.STRINGS[lang]["proj_form_switch_hint"] in old.form_combo.toolTip()
        written = home_page.ProjectDialog(None, lang, "properties", data={"name": "Halle", "form": "builtin:compact"})
        assert [written.form_combo.itemData(i) for i in range(written.form_combo.count())] == [f.ref for f in forms.list_forms() if not f.error]
        assert written.form_combo.currentData() == "builtin:compact" and written.values()["form"] == "builtin:compact"
    # a layout template no place holds any more is still listed as the project's own
    gone = home_page.ProjectDialog(None, "fr", "properties", data={"name": "Halle", "form": "user:verschwunden", "form_name": "Verschwunden"})
    assert gone.form_combo.currentData() == "user:verschwunden" and gone.form_combo.currentText() == "Verschwunden"


def test_choosing_another_layout_template_asks_first_and_then_switches_it_the_old_one_archived():
    _qt()
    import forms
    import home_page
    from PySide6.QtWidgets import QMessageBox
    here = _new_project("pd_switch")
    asked = []
    yes = staticmethod(lambda parent, title, message, *a, **k: asked.append(message) or QMessageBox.StandardButton.Yes)
    no = staticmethod(lambda parent, title, message, *a, **k: asked.append(message) or QMessageBox.StandardButton.No)
    before = forms.current(here)
    with project.using(here):
        # leaving it alone: nothing asked, nothing switched -- and the other properties written
        with _patched(QMessageBox, question=yes), _patched(home_page.ProjectDialog, exec=_accepting(author="P. Muster")):
            updated = home_page.edit_properties(None, "fr", here)
        assert updated is not None and updated.detail("author") == "P. Muster" and not asked
        assert (forms.current(here) is None) == (before is None)
        # another one refused: the look stays, the other properties are still written
        with _patched(QMessageBox, question=no), _patched(home_page.ProjectDialog, exec=_accepting(form="builtin:bfh", author="A. Beispiel")):
            updated = home_page.edit_properties(None, "fr", here)
        key = "proj_form_ask" if before is not None else "proj_form_ask_old"
        bfh = forms.find("builtin:bfh").name("fr")
        assert asked == [home_page.STRINGS["fr"][key].format(form=bfh)], asked
        assert updated.detail("author") == "A. Beispiel" and (forms.current(here) is None) == (before is None)
        # confirmed: the project is written in it, the old look archived, the language kept
        asked.clear()
        with _patched(QMessageBox, question=yes), _patched(home_page.ProjectDialog, exec=_accepting(form="builtin:bfh")):
            assert home_page.edit_properties(None, "fr", here) is not None
        assert len(asked) == 1 and forms.current(here).ref == "builtin:bfh"
        assert forms.is_form_config(here.config_typ) and '"fr"' in here.config_typ.read_text(encoding="utf-8")
        archived = [p for p in here.archives_dir.iterdir() if p.name.endswith("-" + forms.ARCHIVE_LABEL)]
        assert archived, "the old look was not archived"
        # and back to another: asked with the sentence of a project already written in a layout template
        asked.clear()
        with _patched(QMessageBox, question=yes), _patched(home_page.ProjectDialog, exec=_accepting(form="builtin:compact")):
            assert home_page.edit_properties(None, "fr", here) is not None
        assert asked == [home_page.STRINGS["fr"]["proj_form_ask"].format(form=forms.find("builtin:compact").name("fr"))] and forms.current(here).ref == "builtin:compact"


def test_a_refused_switch_is_said_in_the_window_s_words_and_the_other_properties_stay_written():
    _qt()
    import forms
    import home_page
    from PySide6.QtWidgets import QMessageBox
    here = _new_project("pd_switch_refused")
    said = []

    def refuse(*args, **kwargs):
        raise forms.FormError("disk full (English)", "write_failed", error="disque plein")

    with project.using(here), _patched(forms, apply=refuse), \
            _patched(QMessageBox, question=staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)), \
            conftest.notices_said(lambda notice: said.append(notice.text)), \
            _patched(home_page.ProjectDialog, exec=_accepting(form="builtin:bfh", author="Z. Zeta")):   # a critical notice since v0.117, no box
        updated = home_page.edit_properties(None, "en", here)
    import settings_dialog
    assert updated is not None and updated.detail("author") == "Z. Zeta"
    assert said == [home_page.STRINGS["en"]["proj_form_failed"].format(error=settings_dialog.STRINGS["en"]["prefs_form_err_write_failed"].format(error="disque plein"))], said


# --- the words --------------------------------------------------------------------------------------

def test_the_words_are_in_three_languages_and_never_call_a_template_a_modele():
    _qt()
    import home_page
    keys = [key for key in home_page.STRINGS["fr"] if key.startswith(("proj_form", "proj_content"))]
    assert len(keys) >= 12, keys
    for key in keys:
        texts = {lang: home_page.STRINGS[lang][key] for lang in ("fr", "de", "en")}
        assert all(texts.values()), key
        assert len(set(texts.values())) == 3, f"{key} is the same in two languages: {texts}"
        assert "ß" not in texts["de"], "Swiss German writes no ß"
    assert not [key for key, text in home_page.STRINGS["fr"].items() if re.search(r"mod[èe]le", text, re.I)], "a template is a «template» in French, never a «modèle»"
    for gone in ("proj_template", "proj_style", "proj_doc_template_cu"):
        assert gone not in home_page.STRINGS["fr"], gone
    t = home_page.STRINGS
    assert (t["fr"]["proj_form"], t["de"]["proj_form"], t["en"]["proj_form"]) == ("Template de forme", "Formvorlage", "Layout template")
    assert (t["fr"]["proj_content_rs"], t["de"]["proj_content_cu"], t["en"]["proj_content_bp"]) == ("Template de fond — rapport de statique", "Inhaltsvorlage — Nutzungsvereinbarung", "Content template — basis of design")
