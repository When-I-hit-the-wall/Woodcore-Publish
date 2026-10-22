"""«Nouveau projet» (calc/tools/home_page.py, ProjectDialog) since issue #90: the name, the place and the language, and nothing else -- the title page, the form and each document's content template are the «Projet» tab's (project_tab.py) --, and the form applied from that tab (home_page.apply_form, issue #88). Until 0.121 the dialog also offered a layout template, three content templates and three folders, and «Propriétés du projet» was a dialog of its own (the engineer's decision of 06.10.2026, docs/ui/window.md §10quater).

What is held here: that the dialog asks the name, the place and the language and nothing else, the language the settings' at first and the folder shown before it is made; that a project without a name is refused in the dialog; that the project made is the skeleton -- its language, its people and its form the settings', no document; that a layout template is applied only once the engineer agrees; and that every word is in three languages and never calls a template a «modèle».

Built off-screen; every message box a check would meet is replaced first, and every template goes into this process's own folder.
"""

import contextlib
import json
import os
import re
import sys
import types

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


# --- «Nouveau projet» -------------------------------------------------------------------------------

def test_the_dialog_asks_the_name_the_place_and_the_language_and_nothing_else():
    """Issue #90 (the engineer, 21.10.2026): «uniquement demander le nom du projet, qui sera le nom du dossier créé, ainsi que l'endroit»; the language too (22.10.2026: «le choix de la langue se fait lors de la création du projet»), the settings' report language at first. The folder is shown before it is made."""
    _qt()
    import home_page
    from PySide6.QtWidgets import QComboBox, QLineEdit
    with _sandbox("pd_minimal", {"defaults": {"company": "Büro Muster", "report_language": "fr"}}) as ctx:
        dialog = home_page.ProjectDialog(None, "en", location=ctx.base)
        assert len(dialog.findChildren(QLineEdit)) == 2 and len(dialog.findChildren(QComboBox)) == 1, "the dialog asks more than the name, the place and the language"
        for gone in ("form_combo", "doc_template_combos", "doc_folders", "fields", "version"):
            assert not hasattr(dialog, gone), f"{gone} is still in the dialog"
        assert dialog.language.currentData() == "fr"
        dialog.name.setText("Halle Nord")
        assert dialog.folder.text() == str(ctx.base / "Halle Nord")
        assert dialog.values() == {"name": "Halle Nord", "language": "fr"}


def test_a_project_without_a_name_is_refused_in_the_dialog():
    _qt()
    import home_page
    from PySide6.QtWidgets import QDialog, QLabel
    with _sandbox("pd_no_name") as ctx:
        dialog = home_page.ProjectDialog(None, "en", location=ctx.base)
        dialog.accept()
        band = dialog.findChild(QLabel, "dialogError")   # said in the dialog's own band (notices_ui.inline_error), no box
        assert band is not None and band.text() == home_page.STRINGS["en"]["proj_name_needed"] and not band.isHidden()
        assert dialog.result() != QDialog.DialogCode.Accepted


def test_the_project_made_has_its_language_its_people_and_its_form_and_no_document():
    """«Nouveau projet» makes the skeleton (project_template.create_skeleton): in the language chosen, the title page's people and the form the settings' defaults, no document -- each made later from the «Projet» tab."""
    _qt()
    import busy
    import forms
    import home_page
    import templates
    from PySide6.QtWidgets import QDialog
    with _sandbox("pd_made", {"defaults": {"company": "Büro Muster", "author": "M. Muster", "report_language": "de"}, "forms": {"default": "builtin:bfh"}}) as ctx:
        def accepting(dialog):
            dialog.name.setText("Halle Nord")
            dialog.language.setCurrentIndex(dialog.language.findData("fr"))
            return QDialog.DialogCode.Accepted
        with _patched(home_page.ProjectDialog, exec=accepting), _patched(busy, run_in_thread=lambda _window, _text, work, detail="": work()):
            file = home_page.create_project(None, "en", location=ctx.base)
        here = project.Project.load(file)
        assert here.root == ctx.base / "Halle Nord" and here.name == "Halle Nord"
        assert here.created_modes == () and here.modes == project.MODES
        assert templates.project_language(here, fallback="") == "fr"
        assert (here.detail("company"), here.detail("author"), here.detail("checker")) == ("Büro Muster", "M. Muster", "")
        assert forms.current(here).ref.endswith("bfh"), forms.current(here).ref


def test_a_layout_template_is_applied_once_the_engineer_agrees():
    """«Appliquer au projet…» of the «Projet» tab (home_page.apply_form, issue #88): a question first; «Non» changes nothing, «Oui» puts the form in place, the old one archived."""
    _qt()
    import forms
    import home_page
    import project_template
    from PySide6.QtWidgets import QMessageBox
    with _sandbox("pd_apply"):
        here = project_template.create_skeleton(conftest.tmpdir("pd_apply_project") / "P", "Probe", "de")
        before = forms.current(here)
        bfh = forms.find("builtin:bfh")
        with _patched(QMessageBox, question=staticmethod(lambda *a, **k: QMessageBox.StandardButton.No)):
            assert home_page.apply_form(None, "en", here, bfh, before) is False
        assert forms.current(here).ref == before.ref
        asked = []
        with _patched(QMessageBox, question=staticmethod(lambda *a, **k: asked.append(a[2]) or QMessageBox.StandardButton.Yes)):
            assert home_page.apply_form(None, "en", here, bfh, before) is True
        assert forms.current(here).ref.endswith("bfh") and bfh.name("en") in asked[0]


def test_the_words_are_in_three_languages_and_never_call_a_template_a_modele():
    _qt()
    import home_page
    keys = [key for key in home_page.STRINGS["fr"] if key.startswith("proj_")]
    assert len(keys) >= 12, keys
    for key in keys:
        texts = {lang: home_page.STRINGS[lang][key] for lang in ("fr", "de", "en")}
        assert all(texts.values()), key
        assert "ß" not in texts["de"], "Swiss German writes no ß"
    assert not [key for key, text in home_page.STRINGS["fr"].items() if re.search(r"mod[èe]le", text, re.I)], "a template is a «template» in French, never a «modèle»"
    for gone in ("proj_template", "proj_style", "proj_doc_template_cu", "proj_props_title", "proj_content_rs", "proj_doc_folder"):
        assert gone not in home_page.STRINGS["fr"], gone
