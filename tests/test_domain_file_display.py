"""«Affichage» of a calculation tab: the case's file set line by line (calc/tools/domain_file_display.py, spec 2026-10-22-onglet-neige-type, REQ-011 to REQ-016, UI-011, UI-012, D-7, D-8, D-23, D-28, D-30, ARCH-RISK-W06).

On a snow case saved in the «Neige» tab of a new project, off screen: the case's file is written at the save, «Affichage» names it and the command a section prints it by; one card holds the domain's level and «Éléments du fichier», each line with its 0 1 2 3, the domain's level dotted; a click on a level writes the line's `level:`, a second gives it back; the domain's level is written into its header; a line opened shows its arguments -- those of its display, read from lib/display-presets.json --, the line as written and the whole file; the figure is masked and shown from there; the page compiled shows what the report hides (`show-masked`) and the masked figure pale; every writer is refused in a project open read-only.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import sys

import conftest
import project
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
_STATE = {}


def _tab():
    if "tab" not in _STATE:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        if str(TOOLS) not in sys.path:
            sys.path.insert(0, str(TOOLS))
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise conftest.Skip(f"PySide6 is not installed ({exc})")
        QApplication.instance() or QApplication([])
        import project_template
        here = project_template.create(conftest.tmpdir("domain_file_display") / "Halle", "Halle")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
            tab = next(t for t in window.tabs if getattr(t, "KEY", None) == "tab_ac_snow")
            tab.new()
            tab.service("form").fields["h_0"].spin.setValue(850)
            assert tab.save(), tab.ctx.messages
            tab.set_view("display", enter=False)
        _STATE.update(tab=tab, here=here, window=window)
    return _STATE["tab"], _STATE["here"]


def _text(here):
    return (here.root / "Variable-loads" / "Snow" / "SN-01.typ").read_text(encoding="utf-8")


def test_the_case_is_written_at_its_save_and_named_with_its_command():
    tab, here = _tab()
    with project.using(here):
        display = tab.display
        assert display.path() is not None and display.path().name == "SN-01.typ", "written as the case is saved (REQ-015)"
        assert display.command() == '#include domain-file("snow-load", "SN-01")' and display.field.code == display.command()
        assert display.right.findChildren(type(display.card)).count(display.card) == 1, "one card (D-7)"


def test_each_line_has_its_levels_the_domains_dotted_and_a_click_sets_and_gives_back():
    tab, here = _tab()
    with project.using(here):
        display = tab.display
        assert [e["id"] for e in display.elements][:3] == ["domain", "figure:SN-01-fig3.svg", "var:h_0"]
        row = display.rows["var:h_0"]
        import domain_file_display
        buttons = row.findChild(domain_file_display._LevelButtons).buttons
        assert buttons[2].property("dotted") and not any(buttons[n].property("dotted") for n in (0, 1, 3)), "the report's level, followed"
        buttons[0].click()
        assert 'level: 0' in next(l for l in _text(here).split("\n") if '#var("h_0"' in l)
        buttons = display.rows["var:h_0"].findChild(domain_file_display._LevelButtons).buttons
        assert buttons[0].isChecked()
        buttons[0].click()
        assert "level:" not in next(l for l in _text(here).split("\n") if '#var("h_0"' in l), "a second click gives it back to the domain"
        display.level_buttons[3].click()
        assert next(l for l in _text(here).split("\n") if l.startswith("#domain(")).endswith(", level: 3)[")
        buttons = display.rows["var:h_0"].findChild(domain_file_display._LevelButtons).buttons
        assert buttons[3].property("dotted"), "the domain's level is the one a line follows"
        display.level_buttons[None].click()
        assert "level:" not in next(l for l in _text(here).split("\n") if l.startswith("#domain("))


def test_a_line_opened_shows_its_arguments_its_line_and_the_file():
    tab, here = _tab()
    with project.using(here):
        from PySide6.QtWidgets import QComboBox, QLabel, QPlainTextEdit
        import line_display
        display = tab.display
        display.open("eq:q_k11")
        box = next(w for w in display.card.findChildren(type(display.rows["eq:q_k11"])) if w.objectName() == "elementArguments")
        names = [l.text() for l in box.findChildren(QLabel)]
        for name in line_display.display_args("eq"):
            assert name == "level" or name in names, name
        for name in ("equation", "unit", "label", "descr"):
            assert name in names, name
        combo = next(c for c in box.findChildren(QComboBox) if c.findData("bold") >= 0)
        combo.setCurrentIndex(combo.findData("bold"))
        combo.activated.emit(combo.currentIndex())
        assert 'style: "bold"' in next(l for l in _text(here).split("\n") if '#eq("q_k11"' in l)
        texts = display.card.findChildren(QPlainTextEdit)
        assert any('#eq("q_k11"' in t.toPlainText() and t.isReadOnly() for t in texts), "the line as written, read only (D-28)"
        display.open("eq:q_k11")


def test_the_figure_is_masked_and_the_page_shows_it_pale():
    tab, here = _tab()
    with project.using(here):
        assert tab.service("display").write_figure("figure:SN-01-fig3.svg", shown=False)
        line = next(l for l in _text(here).split("\n") if "SN-01-fig3.svg" in l)
        assert line.startswith("// #figure(")
        source = tab.display.source()
        assert "#show-masked.update(true)" in source and "set text(fill: luma(150))" in source and "(" + tab.t("ct_masked") + ")" in source
        assert "29.7cm" in source, "a page an A4 high: a note at its foot (UI-011)"
        assert tab.service("display").write_figure("figure:SN-01-fig3.svg", shown=True)


def test_the_page_compiles():
    tab, here = _tab()
    if not conftest.have_typst():
        raise conftest.Skip("typst is not on the path")
    import subprocess
    with project.using(here):
        tab.service("display").write_line_display("var:h_0", {"level": 0})
        tab.service("display").write_figure("figure:SN-01-fig3.svg", shown=False)
        d = conftest.tmpdir("domain_file_display_page")
        probe = here.typst_root / "_display_probe.typ"
        probe.write_text(tab.display.source(), encoding="utf-8")
        try:
            run = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(d / "page.pdf")], capture_output=True, text=True, encoding="utf-8", errors="replace")
        finally:
            probe.unlink(missing_ok=True)
        assert run.returncode == 0, run.stderr[-2000:]
        from pypdf import PdfReader
        text = " ".join(page.extract_text() for page in PdfReader(str(d / "page.pdf")).pages)
        assert "ausgeblendet" in text or "masquée" in text or "hidden" in text, text[:400]
        tab.service("display").write_line_display("var:h_0", {"level": None})
        tab.service("display").write_figure("figure:SN-01-fig3.svg", shown=True)


def test_the_writers_of_affichage_are_guarded():
    import tab_guard
    for name in ("write_line_display", "write_figure", "write_table", "write_domain_level"):
        assert name in tab_guard.WRITERS, name


def test_a_file_of_another_form_is_regenerated_at_the_save_without_a_button():
    """D-4 of the spec 2026-10-23-neige-correctifs-issues-96-99 (reversing D-18): the roof changed from a duo-pitch to a curved one and the case saved, its file is written again in the new form -- μ₃ and q_k,1, q_k,3, no α₂ nor μ₁₁ any more --, the level set in «Affichage» on α₁ kept, the figure masked kept masked, a sentence of the engineer's kept; «Affichage» has no «Régénérer», and says nothing while the file is of the calculation's form. A file whose base records an earlier form is written again too."""
    import json
    tab, here = _tab()
    from domains import unfold
    with project.using(here):
        tab.service("display").write_line_display("var:alpha_1", {"level": 3})
        tab.service("display").write_figure("figure:SN-01-fig3.svg", shown=False)
        path = here.root / "Variable-loads" / "Snow" / "SN-01.typ"
        path.write_text(_text(here).rstrip().removesuffix("]").rstrip() + "\n  Phrase de l'ingénieur.\n]\n", encoding="utf-8", newline="\n")
        tab.set_view("calc", enter=False)
        tab.service("form").fields["roof"].buttons["curved"].click()
        assert tab.save(), tab.ctx.messages
        text = _text(here)
        assert '#var("mu_3"' in text and 'id: "q_k3"' in text and 'id: "q_k1"' in text, text
        assert '"alpha_2"' not in text and '"mu_11"' not in text, text
        alpha = next(l for l in text.splitlines() if '#var("alpha_1"' in l)
        assert "level: 3" in alpha, alpha
        assert "// #figure" in text or "//#figure" in text, "the figure stays masked (D-23): " + text[:900]
        assert "Phrase de l'ingénieur." in text, "a sentence of the engineer's is kept"
        assert unfold.status(here, "SN-01", kind="snow-load").matches
        tab.set_view("display", enter=False)
        tab.display.rebuild()
        assert not hasattr(tab.display, "regenerate_button") and not hasattr(tab, "write_unfold_regenerate")
        from PySide6.QtWidgets import QLabel
        assert all(label.text() != tab.t("ct_regenerate_failed") for label in tab.display.card.findChildren(QLabel))
        # a base recording an earlier form: written again at the next save
        where = unfold.base_path(here, "snow-load")
        base = json.loads(where.read_text(encoding="utf-8"))
        base["domains"]["SN-01"]["gen"]["form"] = base["domains"]["SN-01"]["gen"]["form"].removesuffix("-fig3")
        where.write_text(json.dumps(base, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        assert not unfold.status(here, "SN-01", kind="snow-load").matches
        tab.set_view("calc", enter=False)
        tab.service("form").fields["h_0"].spin.setValue(900)
        assert tab.save(), tab.ctx.messages
        assert unfold.status(here, "SN-01", kind="snow-load").matches
        # the case as the other tests of this file read it: a duo-pitch roof, the figure shown, α₁ at its level
        tab.service("form").fields["roof"].buttons["duo"].click()
        assert tab.save(), tab.ctx.messages
        tab.service("display").write_figure("figure:SN-01-fig3.svg", shown=True)
        tab.service("display").write_line_display("var:alpha_1", {"level": None})
        path.write_text(_text(here).replace("  Phrase de l'ingénieur.\n", ""), encoding="utf-8", newline="\n")
        tab.set_view("display", enter=False)


def test_switching_to_affichage_saves_the_case():
    """REQ-005, D-7 of the spec 2026-10-23-neige-correctifs-issues-96-99: «Calcul» left for «Affichage» with h₀ changed saves the case -- its source, the export and its file carry the new altitude --; a case with a red message is not saved, nor one of a project open read-only."""
    import json
    tab, here = _tab()
    source = here.sources_dir / "loads" / "snow" / "SN-01.json"
    with project.using(here):
        tab.set_view("calc", enter=False)
        tab.service("form").fields["h_0"].spin.setValue(870)
        assert tab.dirty
        tab.set_view("display", enter=False)
        assert not tab.dirty
        assert json.loads(source.read_text(encoding="utf-8"))["h_0"] == 870
        assert '#var("h_0", 870' in _text(here)
        # read-only: nothing written, nothing refused aloud
        tab.set_view("calc", enter=False)
        tab.service("form").fields["h_0"].spin.setValue(880)
        tab.app.read_only = True
        try:
            tab.set_view("display", enter=False)
        finally:
            tab.app.read_only = False
        assert tab.dirty and json.loads(source.read_text(encoding="utf-8"))["h_0"] == 870
        # a red message: not saved
        tab.set_view("calc", enter=False)
        tab.refresh(preview=False)
        from domains.contracts import Message
        tab.ctx.messages.append(Message("invalid", None, "error", {"error": "probe"}))
        tab.set_view("display", enter=False)
        assert tab.dirty and json.loads(source.read_text(encoding="utf-8"))["h_0"] == 870
        tab.set_view("calc", enter=False)
        tab.service("form").fields["h_0"].spin.setValue(850)
        assert tab.save(), tab.ctx.messages
        tab.set_view("display", enter=False)


def test_a_free_delta_h_is_typed_beside_the_map_s_buttons():
    """REQ-004 of the spec 2026-10-23-neige-correctifs-issues-96-99: right of Δh's five buttons a value of one's own, in metres, negative too -- the source says `correction: "custom"` and `delta_h`, the buttons none chosen; a button chosen again drops it."""
    tab, here = _tab()
    with project.using(here):
        tab.set_view("calc", enter=False)
        field = tab.service("form").fields["correction"]
        assert field.free.suffix().strip() == "m" and field.free.minimum() < 0
        field.free.setValue(-150)
        src = tab.draft()
        assert src["correction"] == "custom" and src["delta_h"] == -150
        assert not any(b.isChecked() for b in field.buttons.values())
        field.buttons[0].click()
        src = tab.draft()
        assert src["correction"] == 0 and "delta_h" not in src
        assert tab.save(), tab.ctx.messages
        tab.set_view("display", enter=False)


def test_the_snow_s_labels_set_their_subscripts():
    """UI-003 of the spec 2026-10-23-neige-correctifs-issues-96-99: C_e and C_T as C with e and T in subscript, in the form and in the sections' headers -- no «_» left in a label of the snow tab, in any language."""
    import re
    tab, here = _tab()
    with project.using(here):
        assert "C<sub>e</sub>" in tab.service("form").fields["exposure"].words.text() and "C<sub>T</sub>" in tab.service("form").fields["c_t"].words.text()
        for field in tab.service("form").fields.values():
            assert "_" not in re.sub(r"<[^>]+>", "", field.words.text()), field.words.text()
        assert "C<sub>e</sub>" in tab.service("form").sections["site"].summary.text()
    import woodcore_gui_words
    for lang in ("fr", "de", "en"):
        for key, text in woodcore_gui_words.STRINGS[lang].items():
            if key.startswith(("sn_f_", "sn_fs_")):
                import richtext
                assert "_" not in re.sub(r"<[^>]+>", "", richtext.subscripts(text)), (lang, key, text)


def test_a_table_is_an_element_of_the_file_with_no_level_shown_or_not_with_its_title_and_note():
    """UI-024 (spec 2026-10-23-onglet-vent-briques, V2): the layers' table of a permanent load in «Affichage» -- a row `#table` with its title and no 0 1 2 3; opened, «Afficher le tableau», «Titre», «Note»; unticked, its line commented out in the file and the page drawing it pale; ticked again, as it was."""
    tab, here = _tab()
    with project.using(here):
        import domain_file_display
        from PySide6.QtWidgets import QCheckBox
        window = _STATE["window"]
        dead = next(t for t in window.tabs if getattr(t, "KEY", None) == "tab_ac_selfweight")
        dead.new()
        assert dead.save(), dead.ctx.messages
        dead.set_view("display", enter=False)
        display = dead.display
        display.rebuild()
        tables = [e for e in display.elements if e["kind"] == "table"]
        assert tables and tables[0]["id"] == "table:1" and tables[0]["title"] is True
        row = display.rows["table:1"]
        assert row.findChild(domain_file_display._LevelButtons) is None, "a table has no level"
        display.open("table:1")
        boxes = {b.text(): b for b in display.card.findChildren(QCheckBox)}
        assert {dead.t("ct_show_table"), dead.t("ct_table_title")} <= set(boxes)
        boxes[dead.t("ct_show_table")].setChecked(False)
        path = display.path()
        line = next(l for l in path.read_text(encoding="utf-8").split("\n") if "-table-1>" in l and "#table(" in l)
        assert line.startswith("// #from-level(3)[#table("), line[:60]   # the permanent loads' layers printed at level 3 (issue #111, REQ-013)
        assert "luma(150)" in display.source() and "-table-1>" not in display.source().split("luma(150)")[1].split("\n")[1]
        boxes = {b.text(): b for b in display.card.findChildren(QCheckBox)}   # still open: a write builds the card again with the line opened
        boxes[dead.t("ct_show_table")].setChecked(True)
        line = next(l for l in path.read_text(encoding="utf-8").split("\n") if "-table-1>" in l and "#table(" in l)
        assert line.startswith("#from-level(3)[#table("), line[:60]


def test_a_rebuild_deletes_the_rows_laid_out_in_a_layout_of_their_own():
    """Issue #112 (fix): the command's copy button and the domain's levels sit in rows of their own (a QHBoxLayout each); the card built again deletes them with their row, never leaving them behind. Taken out whole, a row was deleted with its items while its widgets stayed in the card and PySide kept wrappers of the freed items -- read again when Qt reused the address or tore the application down: an access violation about one run of test_member_check_tab in three."""
    tab, here = _tab()
    with project.using(here):
        import shiboken6
        from PySide6.QtWidgets import QPushButton
        display = tab.display
        display.rebuild()
        copy, level = display.copy_button, display.level_buttons[3]
        display.rebuild()
        display.rebuild()
        assert all(not shiboken6.isValid(w) or w.parent() is None for w in (copy, level)), "the rows of before taken out of the card (held here, they live on alone)"
        del copy, level
        assert [b for b in display.card.findChildren(QPushButton) if b.text() == display.copy_button.text()] == [display.copy_button]
