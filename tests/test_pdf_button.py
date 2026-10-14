"""The window's two split buttons, «Importer Excel» and «Exporter PDF» (docs/ui/window.md §10quater, v0.62).

What these hold is the one thing the window shares with `woodcore-cli`: the command that builds the deliverable. Both compile the project's `report` into its `pdf` and take their `--input` flags from one function, `calc/cli.py`'s `input_args` (v0.82) -- until then the window spelled the arguments of a `build.ps1` it did not call, and these checks read the script to compare.

The rest is the menu's own rule: its entries are checks and not commands, so what reaches Typst is whatever is ticked when the button is clicked, and *tel qu'écrit* must pass no `--input` at all -- that absence is what makes the report come out with the base level and the language the document declares (sections 4, 4bis). An entry that quietly passed `level=1` instead would produce a client report from a button that says it changes nothing.

⚠️ Skipped where PySide6 is not installed or the export has never been run here, like every check that builds the window. It is built off-screen, and nothing here starts a process: no document is compiled, only the argument list its compile would start is read (`compile_command`). The export of one document or of the three, each passed over where its Typst did not change since its PDF, is tests/test_modes_window.py's.
"""

import os
import sys

import conftest
from conftest import ROOT, Skip

_window = None


def _main_window():
    """The window, built once, off-screen -- a test run must never open one."""
    global _window
    if _window is None:
        conftest.exported("calculations.json")
        path = str(ROOT / "calc" / "tools")
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        import woodcore_gui
        QApplication.instance() or QApplication([])
        _window = woodcore_gui.MainWindow()
        _window.lang = "fr"  # the window opens in whatever language was last chosen; these checks read the French labels
        _window.rebuild()
    return _window


def _entries(menu):
    """Every entry of a menu, a submenu's own included, by label."""
    found = {}
    for action in menu.actions():
        if action.menu() is not None:
            found.update(_entries(action.menu()))
        elif not action.isSeparator():
            found[action.text()] = action
    return found


def _choose(win, label):
    """Tick one entry of the PDF menu, the way a click does."""
    entry = _entries(win.pdf_button.menu()).get(label)
    assert entry is not None, f"the PDF menu has no entry {label!r}: {sorted(_entries(win.pdf_button.menu()))}"
    entry.trigger()


def test_the_window_and_the_command_line_build_the_same_deliverable():
    """The deliverable is one file, whichever route builds it (docs/conventions/build-and-release.md §12): the window and `woodcore-cli export` both compile the project's `report` into its `pdf`, the two paths its .woodcore names (v0.82, where build.ps1 and the Makefile each spelled them again until then)."""
    win = _main_window()
    import cli
    import proc
    import project
    here = project.current()
    assert here.report_typ.exists(), f"{here.report_typ} is not there"
    compiled = []
    saved = proc.subprocess.run   # the one place a child process is started (calc/proc.py), which calls the module's `run`
    proc.subprocess.run = lambda args, **kwargs: compiled.append(args) or __import__("types").SimpleNamespace(returncode=0, stdout="", stderr="")
    try:
        assert cli.compile_report(here, [], here.report_pdf) is None
    finally:
        proc.subprocess.run = saved
    assert compiled[0][-2:] == [str(here.report_typ), str(here.report_pdf)], compiled
    assert win.pdf_button is not None
    # and the window's own command line is the one spelling of a document's compile (documents.compile_args), with the Typst root stated and Typst told to say what it read: every compile of the window goes through it (30.09.2026)
    import documents
    import stamps
    flags = cli.input_args("level", 2, "fr")
    program, arguments, deps = win.compile_command(here, "rs", flags)
    assert deps == stamps.deps_file(here, "rs")
    assert arguments == documents.compile_args(here, "rs", flags, deps=deps), arguments
    assert arguments[-2:] == [str(here.document_typ("rs")), str(here.document_pdf("rs"))] == compiled[0][-2:], arguments
    assert arguments[arguments.index("--root") + 1] == str(here.typst_root), arguments
    assert program == __import__("project").typst_executable()


def test_the_flags_are_the_ones_the_command_line_passes():
    """--input level=, uniform= and lang=, spelt once (calc/cli.py input_args) and read by the window's menu, which is what keeps the two routes from drifting apart the way build.ps1 and the window could."""
    import cli
    win = _main_window()
    _choose(win, "Niveau 2")
    _choose(win, "Français")
    assert win.pdf_input_args() == cli.input_args("level", 2, "fr") == ["--input", "level=2", "--input", "lang=fr"]
    _choose(win, "Uniforme 3")
    assert win.pdf_input_args() == cli.input_args("uniform", 3, "fr")
    _choose(win, "Tel qu'écrit (document)")
    _choose(win, "Langue du document")
    assert cli.input_args() == [] == win.pdf_input_args()


def test_as_written_passes_no_input_at_all():
    """The absence is the feature: no --input means the document's own base level and language govern (docs/typst/report-engine.md §4, docs/typst/language.md §4bis)."""
    win = _main_window()
    _choose(win, "Tel qu'écrit (document)")
    _choose(win, "Langue du document")
    assert win.pdf_input_args() == [], f"«tel qu'écrit» forces something: {win.pdf_input_args()}"
    # the tooltip names the document the button exports (30.09.2026), and no setting while both are the document's own
    assert win.pdf_button.toolTip() == win.t("pdf_document", document=win.document_name()), win.pdf_button.toolTip()


def test_a_level_and_a_language_combine():
    """The entries are checks and not commands, so the two axes hold at once -- which a menu of one-shot entries could not do (docs/decisions.md §13)."""
    win = _main_window()
    _choose(win, "Uniforme 2")
    _choose(win, "Français")
    assert win.pdf_input_args() == ["--input", "uniform=2", "--input", "lang=fr"], \
        f"«Uniforme 2» and «Français» ticked together give {win.pdf_input_args()}"
    assert win.pdf_button.toolTip() == f"Exporte : {win.document_name()}\nRéglages : Uniforme 2 · Français", \
        f"the tooltip does not name the document and what is ticked: {win.pdf_button.toolTip()!r}"
    _choose(win, "Niveau 1")
    assert win.pdf_input_args() == ["--input", "level=1", "--input", "lang=fr"], \
        f"a base level chosen after a uniform one gives {win.pdf_input_args()}"


def test_a_base_level_and_a_uniform_level_are_exclusive():
    """A base level and a uniform level are mutually exclusive, which woodcore-cli can only say by refusing when it is handed both. One QActionGroup over both submenus means the window cannot ask for both at all."""
    win = _main_window()
    _choose(win, "Uniforme 3")
    _choose(win, "Niveau 2")
    entries = _entries(win.pdf_button.menu())
    assert not entries["Uniforme 3"].isChecked(), "a uniform level stays ticked while a base level is chosen"
    assert entries["Niveau 2"].isChecked(), "the base level just chosen is not ticked"
    assert [a for a in win.pdf_input_args() if a.startswith("uniform=")] == [], \
        f"both a base and a uniform level reach Typst: {win.pdf_input_args()}"


def test_the_choice_survives_a_rebuild():
    """build() is played again on every language switch and every reload, and takes its widgets with it; the choice lives on the window for that reason."""
    win = _main_window()
    _choose(win, "Uniforme 1")
    _choose(win, "Deutsch")
    win.rebuild()
    assert win.pdf_input_args() == ["--input", "uniform=1", "--input", "lang=de"], \
        f"the choice was lost in the rebuild: {win.pdf_input_args()}"
    assert _entries(win.pdf_button.menu())["Uniforme 1"].isChecked(), "the menu was rebuilt without its tick"
    _choose(win, "Tel qu'écrit (document)")
    _choose(win, "Langue du document")


def test_both_buttons_carry_a_menu():
    """The import menu holds **one** entry: there is one way to import, and the arrow says so rather than suggesting there are others.

    ⚠️ Its text is no longer the button's own word alone. «Importer Excel» became «Import données» when the import took in the RFEM table exports as well (docs/ui/window.md §10quater; the RFEM import was retired in 0.117), and the entry now names what that one action takes in — «Import données — Excel et les dessins de Woodcore». What is held is the count and that the entry opens on the button's own word, which is the rule; the rest of the wording is the window's.
    """
    win = _main_window()
    from PySide6.QtWidgets import QToolButton
    for button in (win.export_button, win.pdf_button):
        assert button.popupMode() == QToolButton.ToolButtonPopupMode.MenuButtonPopup, \
            f"{button.text()!r} is not a split button: its own click must act, and only the arrow open the menu"
        assert button.menu() is not None, f"{button.text()!r} has no menu"
    actions = win.export_button.menu().actions()
    assert len(actions) == 1, f"the import menu holds more than one entry: {[a.text() for a in actions]}"
    assert actions[0].text().startswith(win.export_button.text()), \
        f"the one entry must open on the button's own word: {actions[0].text()!r} against {win.export_button.text()!r}"


def test_the_buttons_are_named_in_all_three_languages():
    """A renamed button leaves the messages that tell the engineer to click it pointing at nothing; these are the strings that name it."""
    win = _main_window()
    import woodcore_gui
    # «Importer Excel» became «Import données» when the import took in the RFEM table exports too -- the engineer's own rename (docs/open-questions.md §14): the one action reads the load workbooks, Positionen.xlsx and everything Woodcore drew (and the RFEM exports until 0.117), so a word that says «Excel» says less than the button does.
    names = {"fr": ("Import données", "Exporter PDF"), "de": ("Daten importieren", "PDF exportieren"),
             "en": ("Import data", "Export PDF")}
    for lang, (imported, pdf) in names.items():
        strings = woodcore_gui.STRINGS[lang]
        assert (strings["reexport"], strings["export_pdf"]) == (imported, pdf), \
            f"{lang}: the buttons read {strings['reexport']!r} and {strings['export_pdf']!r}"
        # Every word the button has ever carried: a message still naming one of them sends the engineer to a button that is not there. This is the check that caught «Importer Excel» in three of these strings when the button was renamed.
        gone = ("xcel neu exportieren", "Re-export from Excel", "Réexporter depuis Excel",
                "Importer Excel", "Aus Excel importieren", "Import from Excel")
        for key in ("stale", "polar_empty"):
            for word in gone:
                assert word not in strings[key], (
                    f"{lang}/{key} still sends the engineer to a button that no longer exists ({word!r}): {strings[key]!r}"
                )
    win.lang = "fr"


def test_the_command_line_refuses_a_level_and_a_uniform_level_together():
    """`--level` and `--uniform` are exclusive, as the menu's one exclusive group of seven entries makes them (docs/ui/window.md §10quater) -- the rule build.ps1 stated by throwing until v0.82."""
    import cli
    try:
        cli.parser().parse_args(["export", "--level", "1", "--uniform", "2"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("woodcore-cli took a base level and a uniform level at once")
    args = cli.parser().parse_args(["export", "--uniform", "2", "--lang", "en", "--all-levels"])
    assert (args.uniform, args.lang, args.all_levels, args.level) == (2, "en", True, None)

