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
            tab.fields["h_0"].spin.setValue(850)
            assert tab.save(), tab.messages_
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
        assert tab.write_figure("figure:SN-01-fig3.svg", shown=False)
        line = next(l for l in _text(here).split("\n") if "SN-01-fig3.svg" in l)
        assert line.startswith("// #figure(")
        source = tab.display.source()
        assert "#show-masked.update(true)" in source and "set text(fill: luma(150))" in source and "(" + tab.t("ct_masked") + ")" in source
        assert "29.7cm" in source, "a page an A4 high: a note at its foot (UI-011)"
        assert tab.write_figure("figure:SN-01-fig3.svg", shown=True)


def test_the_page_compiles():
    tab, here = _tab()
    if not conftest.have_typst():
        raise conftest.Skip("typst is not on the path")
    import subprocess
    with project.using(here):
        tab.write_line_display("var:h_0", {"level": 0})
        tab.write_figure("figure:SN-01-fig3.svg", shown=False)
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
        tab.write_line_display("var:h_0", {"level": None})
        tab.write_figure("figure:SN-01-fig3.svg", shown=True)


def test_the_writers_of_affichage_are_guarded():
    import tab_guard
    for name in ("write_line_display", "write_figure", "write_domain_level"):
        assert name in tab_guard.WRITERS, name


def test_a_file_of_an_earlier_form_is_said_and_regenerated_from_affichage():
    """D-18: a case's file whose base records the form before «-fig3» says so in the card, and «Régénérer» writes it in today's form."""
    import json
    tab, here = _tab()
    from domains import unfold
    with project.using(here):
        where = unfold.base_path(here, "snow-load")
        base = json.loads(where.read_text(encoding="utf-8"))
        base["domains"]["SN-01"]["gen"]["form"] = base["domains"]["SN-01"]["gen"]["form"].removesuffix("-fig3")
        where.write_text(json.dumps(base, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        tab.display.rebuild()
        assert not unfold.status(here, "SN-01", kind="snow-load").matches
        tab.display.regenerate_button.click()
        assert unfold.status(here, "SN-01", kind="snow-load").matches
        assert "write_unfold_regenerate" in __import__("tab_guard").WRITERS
