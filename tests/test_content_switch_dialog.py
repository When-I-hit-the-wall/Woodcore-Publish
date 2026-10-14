"""«Changer de template de fond…» (calc/tools/content_switch_dialog.py over calc/content_switch.py, the engineer's decision of 06.10.2026): a document compared with another content template in a tree, each section kept, taken or dropped.

What is held here is what the dialog adds to the comparison calc/content_switch.py makes and tests/test_content_switch.py holds: that the tree shows a project's chapters and sections with what each side holds said by a mark **and** a word in the theme's colours, the objects under a section greyed and offered no choice; that each section's combo offers what its status allows, at its default; that «Afficher seulement les différences» hides what is the same; that «Appliquer» asks first, listing what is replaced, removed and added, and then writes and archives; that a refusal is said in the banner in the window's words by its code -- every code of content_switch.CODES having a sentence in three languages; that a document whose headings are written with offsets is offered the conversion and compared again; that a project held read-only is shown the comparison and writes nothing; and that the structure tab opens the dialog in the three documents and reads its tree again after it.

Built off-screen; every question is answered by a method of the dialog or the tab replaced first: a modal off-screen never comes back.
"""

import contextlib
import os
import re
import shutil
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


def _base():
    if "base" not in _STATE:
        import project_template
        _STATE["base"] = project_template.create(conftest.tmpdir("csd_base") / "Halle", "Halle", document_language="fr", report_language="fr")
    return _STATE["base"]


def _project(name):
    base = _base()
    target = conftest.tmpdir(name) / "Halle"
    shutil.copytree(base.root, target, ignore=shutil.ignore_patterns("_Archiv", "stamps", "*.pdf"))
    return project.Project.load(target / base.file.name)


def _read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def _edited(name):
    """A project whose convention has `purpose` edited, `radon` removed and a section of the engineer's own, `my-own`, added after `purpose` -- the shapes tests/test_content_switch.py compares."""
    import structure
    here = _project(name)
    path = here.document_dir("cu") / "Sections" / "purpose.typ"
    text = _read(path)
    first = text.index("// woodcore:object text p1\n") + len("// woodcore:object text p1\n")
    end = text.index("// woodcore:/object p1", first)
    path.write_text(text[:first] + "Mon objet à moi.\n" + text[end:], encoding="utf-8", newline="")
    structure.remove_section(here, "cu", "radon")
    parent = structure.find(structure.read(here.structure_file("cu")), "purpose")[2]
    structure.add_section(here, "cu", parent["id"], 1, "my-own", "Ma section")
    return here


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


def _dialog(here, mode="cu", lang="fr", **kwargs):
    import content_switch_dialog
    return content_switch_dialog.ContentSwitchDialog(None, lang, here, mode, settings={}, **kwargs)


def test_the_tree_says_each_side_by_a_mark_and_a_word_and_offers_what_each_status_allows_at_its_default():
    _qt()
    import content_switch_dialog as csd
    import theme
    from PySide6.QtGui import QColor
    here = _edited("csd_tree")
    dialog = _dialog(here)
    t = csd.STRINGS["fr"]
    assert dialog.chosen_template().ref == "builtin:cu/standard" and dialog.combo.count() >= 1
    assert [dialog.tree.headerItem().text(i) for i in range(4)] == [t["cs_col_node"], t["cs_col_document"], t["cs_col_template"], t["cs_col_choice"]]
    rows = dialog.visible_rows()
    assert rows["purpose"] == (t["cs_side_differs"], t["cs_side_differs"], "keep"), rows["purpose"]
    assert rows["my-own"] == (t["cs_side_present"], t["cs_side_absent"], "keep")
    assert rows["radon"] == (t["cs_side_absent"], t["cs_side_present"], "take")
    # a mark and a word -- never a colour alone -- and the colour the theme names
    for key in ("cs_side_same", "cs_side_differs", "cs_side_present", "cs_side_absent"):
        assert re.match(r"^[=≠●○] \S", csd.STRINGS["en"][key]), key
    purpose = dialog.items["purpose"]
    assert purpose.foreground(1).color() == QColor(theme.colour("override"))
    assert dialog.items["radon"].foreground(2).color() == QColor(theme.colour("accent"))
    # the combos: what the status allows, in the window's words, at the default
    combo = dialog.choice_combos["purpose"]
    assert [combo.itemData(i) for i in range(combo.count())] == ["keep", "take", "drop"]
    assert [combo.itemText(i) for i in range(combo.count())] == [t["cs_choice_keep"], t["cs_choice_take"], t["cs_choice_drop"]]
    radon = dialog.choice_combos["radon"]
    assert [radon.itemData(i) for i in range(radon.count())] == ["take", "skip"] and radon.currentData() == "take"
    assert dialog.choices()["my-own"] == "keep"
    # the objects under a section: greyed, their status only, no choice
    objects = [purpose.child(i) for i in range(purpose.childCount())]
    assert objects and all(dialog.tree.itemWidget(row, 3) is None and not row.text(3) for row in objects)
    assert any(row.text(1) == t["cs_side_differs"] for row in objects), "the paragraph edited is not said to differ"
    assert all(row.foreground(0).color() == QColor(theme.colour("muted")) for row in objects)
    # the summary counts the sections
    counts = dialog.comparison.counts()
    assert dialog.summary.text() == t["cs_summary"].format(**counts) and counts["differs"] == 1
    # only the differences
    assert "intended-use" in dialog.visible_rows()
    dialog.only_differences.setChecked(True)
    shown = dialog.visible_rows()
    assert "intended-use" not in shown and {"purpose", "my-own", "radon"} <= set(shown), sorted(shown)
    dialog.only_differences.setChecked(False)
    assert "intended-use" in dialog.visible_rows()
    dialog.close()


def test_apply_asks_first_listing_what_changes_then_writes_and_archives():
    _qt()
    import content_switch_dialog as csd
    import doc_templates
    from PySide6.QtWidgets import QDialog
    here = _edited("csd_apply")
    folder = here.document_dir("cu")
    edited = _read(folder / "Sections" / "purpose.typ")
    dialog = _dialog(here)
    assert dialog.set_choice("purpose", "take") and dialog.set_choice("my-own", "drop") and dialog.set_choice("radon", "skip")
    assert not dialog.set_choice("radon", "keep"), "a choice the status does not allow was offered"
    asked = []
    with _patched(dialog, ask_confirm=lambda text: asked.append(text) or False):
        assert dialog.apply() is None
    t = csd.STRINGS["fr"]
    assert len(asked) == 1 and t["cs_confirm_archive"] in asked[0] and "Ma section" in asked[0]
    assert _read(folder / "Sections" / "purpose.typ") == edited and (folder / "Sections" / "my-own.typ").is_file(), "a no wrote something"
    with _patched(dialog, ask_confirm=lambda text: True):
        result = dialog.apply()
    assert result is not None and dialog.result_ is result and dialog.result() == QDialog.DialogCode.Accepted
    template = doc_templates.find("builtin:cu/standard").language_dir("fr") / "Sections" / "purpose.typ"
    assert _read(folder / "Sections" / "purpose.typ") == _read(template)
    assert not (folder / "Sections" / "my-own.typ").exists()
    archived = {to.name.split("-", 2)[2] for _from, to in result.archived}
    assert {"purpose.typ", "my-own.typ"} <= archived and all(to.parent == folder / "Sections" / "archives" for _f, to in result.archived)


def test_a_refusal_is_said_in_the_banner_by_its_code_and_every_code_has_a_sentence_in_three_languages():
    _qt()
    import content_switch
    import content_switch_dialog as csd
    for lang in ("fr", "de", "en"):
        table = csd.STRINGS[lang]
        for code in content_switch.CODES:
            assert table.get(f"cs_why_{code}"), f"{code} has no sentence in {lang}"
            exc = content_switch.ContentSwitchError("an English sentence", code, mode="cu", language="de", languages=["fr", "en"], ref="user:cu/x",
                                                    name="x", file="a.typ", error="boom", id="radon", choice="keep", allowed=["take", "skip"], depth=5, side="document")
            text = csd.error_text(lang, exc)
            assert text and "{" not in text and "English sentence" not in text, (lang, code, text)
        side = content_switch.ContentSwitchError("x", "legacy_headings", side="template")
        assert csd.error_text(lang, side) == table["cs_why_legacy_headings_template"]
        assert csd.error_text(lang, content_switch.ContentSwitchError("a new one", "not_a_code")) == "a new one"
        assert not [key for key in table if key.startswith("cs_why_") and key[len("cs_why_"):] not in content_switch.CODES and key != "cs_why_legacy_headings_template"]
        assert "ß" not in "".join(csd.STRINGS["de"].values()), "Swiss German writes no ß"
    # a write that fails is said in the window's words, nothing accepted
    here = _edited("csd_refused")
    dialog = _dialog(here, lang="en")

    def refuse(*args, **kwargs):
        raise content_switch.ContentSwitchError("disk full (English)", "write_failed", error="disque plein")

    with _patched(content_switch, apply=refuse), _patched(dialog, ask_confirm=lambda text: True):
        assert dialog.apply() is None
    assert dialog.banner.text() == csd.STRINGS["en"]["cs_why_write_failed"].format(error="disque plein") and not dialog.banner.isHidden()
    assert dialog.result_ is None and "English" not in dialog.banner.text()
    # a file changed under the comparison: refused, the comparison made again
    (here.document_dir("cu") / "Sections" / "purpose.typ").write_text("= Changé\n", encoding="utf-8")
    with _patched(dialog, ask_confirm=lambda text: True):
        assert dialog.apply() is None
    assert dialog.banner.text().startswith(csd.STRINGS["en"]["cs_why_changed_meanwhile"].split("{")[0]) and dialog.comparison is not None
    dialog.close()


def test_a_document_with_offsets_is_offered_the_conversion_and_compared_again():
    _qt()
    import content_switch_dialog as csd
    import structure
    here = _project("csd_legacy")
    path = here.structure_file("bp")
    source = structure.read(path)
    headings = source.pop("headings")
    structure.write(path, source)
    converted = []

    def convert():
        """The tab's conversion, as far as the dialog can tell: the structure says its headings are at their level again (the files were never moved: only the key was taken out)."""
        converted.append(1)
        structure.write(path, dict(structure.read(path), headings=headings))
        return True

    dialog = _dialog(here, mode="bp", convert=convert)
    assert dialog.comparison is None and dialog.banner.text() == csd.STRINGS["fr"]["cs_why_legacy_headings"]
    assert not dialog.convert_button.isHidden() and not dialog.apply_button.isEnabled()
    dialog.convert_button.click()
    assert converted and dialog.comparison is not None and dialog.banner.isHidden() and dialog.apply_button.isEnabled()
    dialog.close()


def test_a_project_held_read_only_is_shown_the_comparison_and_writes_nothing():
    _qt()
    import content_switch_dialog as csd
    here = _edited("csd_read_only")
    dialog = _dialog(here, read_only=True)
    assert dialog.comparison is not None and not dialog.apply_button.isEnabled()
    assert dialog.apply_button.toolTip() == csd.STRINGS["fr"]["cs_read_only"]
    assert not dialog.choice_combos["purpose"].isEnabled()
    with _patched(dialog, ask_confirm=lambda text: (_ for _ in ()).throw(AssertionError("asked"))):
        assert dialog.apply() is None
    assert (here.document_dir("cu") / "Sections" / "my-own.typ").is_file()
    dialog.close()


def test_the_report_switches_too_and_the_structure_tab_opens_the_dialog_and_reads_its_tree_again():
    _qt()
    import content_switch_dialog as csd
    import structure_tab
    import structure_words
    import woodcore_gui  # noqa: F401 -- guards the tab's writers
    here = _edited("csd_tab")
    report = _dialog(here, mode="rs")
    assert report.comparison is not None and report.chosen_template().ref == "builtin:rs/standard"
    report.close()

    class App:
        lang, mode, read_only = "fr", "cu", False
        views = {}

        def __init__(self):
            from PySide6.QtGui import QFont
            self.bold_font = QFont()
            self.statuses, self.refused = [], 0

        def t(self, key, **values):
            text = structure_words.STRINGS[self.lang][key]
            return text.format(**values) if values else text

        def current_document(self):
            return self.mode

        def set_status(self, text):
            self.statuses.append(text)

        def refuse_read_only(self):
            self.refused += 1

    app = App()
    with project.using(here):
        tab = structure_tab.StructureTab(app)
        try:
            button = tab.buttons["switch_template"]
            assert button.isEnabled() and button.text() == app.t("st_switch_template") and button.toolTip() == app.t("st_switch_template_tip")
            assert tab.buttons["save_template"].isEnabled()
            ran = []

            def ask():
                dialog = csd.ContentSwitchDialog(tab, "fr", here, "cu", settings={})
                dialog.set_choice("my-own", "drop")
                with _patched(dialog, ask_confirm=lambda text: True):
                    ran.append(dialog.apply())
                return dialog.result_

            with _patched(tab, ask_switch=ask):
                assert tab.on_switch_template()
            assert ran and ran[0].changed
            assert app.statuses[-1] == app.t("st_switch_done", written=len(ran[0].written), archived=len(ran[0].archived))
            assert tab.tree.row("my-own") is None, "the tree was not read again"
            # cancelled: nothing said, nothing read
            with _patched(tab, ask_switch=lambda: None):
                assert tab.on_switch_template() is False
            # in the three documents
            for mode in ("bp", "rs"):
                app.mode = mode
                tab.on_mode(mode)
                assert tab.buttons["switch_template"].isEnabled(), mode
                assert tab.buttons["save_template"].isEnabled(), f"{mode}: the report saves its content template too"
            # held read-only: refused, the window saying why
            app.read_only = True
            tab.update_buttons()
            assert not tab.buttons["switch_template"].isEnabled() and tab.buttons["switch_template"].toolTip() == app.t("st_read_only")
            with _patched(tab, ask_switch=lambda: (_ for _ in ()).throw(AssertionError("opened"))):
                assert tab.on_switch_template() is False
            assert app.refused >= 1
        finally:
            tab.stop_watching()
            tab.pane.stop()
            tab.deleteLater()


def test_the_words_carry_the_same_keys_and_never_call_a_template_a_modele():
    _qt()
    import content_switch_dialog as csd
    keys = set(csd.STRINGS["fr"])
    assert all(set(csd.STRINGS[lang]) == keys for lang in ("de", "en"))
    assert not [k for k, v in csd.STRINGS["fr"].items() if re.search(r"\bmodèle", v, re.I)], "a template is a «template» in French, never a «modèle»"
    assert not re.search(r"setStyleSheet\([^)]*#[0-9a-fA-F]{3,6}", (TOOLS / "content_switch_dialog.py").read_text(encoding="utf-8"))
