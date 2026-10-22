"""Woodcore's look, the website's in the window (calc/tools/theme.py, theme.json; v0.90, docs/ui/window.md §10quater).

Every colour of Woodcore is written once, in calc/tools/theme.json: website/build.py writes it into the site's style sheet and theme.py builds the window's palette and style sheet from it. The window follows Windows' light or dark theme unless the engineer chose one in *Fichier → Apparence*; the fonts are the site's as a browser resolves them -- Segoe UI and Cascadia Mono on Windows.

What is held here: the two readers read one file and nothing else states a colour; every text the window sets is readable in both schemes (4.5:1, WCAG AA); the style sheet parses; the choice is the engineer's, remembered, and every window is built again in it; and the text font carries the Greek, the indices and exponents and the relations a calculation is written with -- the engineer's one condition on the typography.

⚠️ Built off-screen. A test that changes the scheme puts the light one back, the one conftest seeds, so a colour another test reads is the colour it expects.
"""

import os
import re
import subprocess
import sys

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _theme():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    import theme
    return theme


def _luminance(colour):
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


# --- one file, two readers -----------------------------------------------------------------------------------

def test_the_two_schemes_name_the_same_tokens_and_every_colour_is_a_colour():
    theme = _theme()
    light, dark = theme.tokens("light"), theme.tokens("dark")
    assert set(light) == set(dark)
    for scheme, table in (("light", light), ("dark", dark)):
        for name, value in table.items():
            if name != "shadow":
                assert HEX.match(value), f"{scheme}.{name} = {value!r} is not #rrggbb"
    assert theme.families(theme.load()["font"])[0] == "Inter" and "Segoe UI" in theme.families(theme.load()["font"])
    assert "system-ui" not in theme.families(theme.load()["font"]), "a generic family is the browser's, never a family Qt is asked for"


def test_the_site_s_style_sheet_states_no_colour_and_the_build_writes_them_all_in():
    """assets/site.css carries one marker where its tokens were until v0.89, and website/build.py writes theme.json into it: the site and the window cannot come to show two teals."""
    theme = _theme()
    source = (ROOT / "website" / "assets" / "site.css").read_text(encoding="utf-8")
    assert source.count("/* @tokens") == 1
    assert not re.search(r"--(bg|ink|accent|wood|muted|line)[\w-]*\s*:", source), "site.css defines a colour token of its own again"
    code = (
        "import sys, importlib.util\n"
        "sys.modules['PySide6'] = None\n"   # the CI image has no Qt: the build must not reach for it, even indirectly
        f"spec = importlib.util.spec_from_file_location('website_build', r'{ROOT / 'website' / 'build.py'}')\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "sys.stdout.reconfigure(encoding='utf-8'); print(m.site_css())\n"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    assert done.returncode == 0, done.stderr[-2000:]
    css = done.stdout
    assert "@tokens" not in css and css.count("--topbar: 60px") == 1
    for scheme in theme.SCHEMES:
        for name, value in theme.tokens(scheme).items():
            assert f"--{name}: {value};" in css, f"the built site.css lacks the {scheme} --{name}"
    dark = css[css.index("@media (prefers-color-scheme: dark)"):]
    assert f"--bg: {theme.tokens('dark')['bg']};" in dark and "color-scheme: dark;" in dark
    assert f"--mono: {theme.load()['mono']};" in css


def test_no_module_of_the_window_states_a_colour_in_a_style_sheet_of_its_own():
    """Until v0.89 fifteen colours were written into setStyleSheet calls across six modules -- two oranges for one meaning, the banners in another system's colours. A colour of the window is a token, read with theme.colour() or named by a property the style sheet knows (`callout`, `primary`, `hot`)."""
    offenders = []
    for path in sorted(TOOLS.glob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "setStyleSheet(" in line and re.search(r"#[0-9a-fA-F]{3,6}\b", line):
                offenders.append(f"{path.name}:{number}: {line.strip()[:100]}")
    assert not offenders, "\n".join(offenders)


# What may still be written as a colour in calc/tools/ (issue #29): constants that *recognise* a colour rather than choose one, each with its reason.
COLOUR_ALLOWED = {
    ("plan_canvas_render.py", "#fff"): "_WHITE (split out of plan_canvas.py) recognises the white tint_svg must not tint -- what connector_svg and connection_svg write, not a colour chosen here",
    ("plan_canvas_render.py", "#ffffff"): "_WHITE again",
    ("statics_tab_build.py", "#ffffff"): "SWATCH_FILL recognises the white statics_svg fills a swatch with, to recolour it on a dark ground",
    ("svg_icons.py", "#000001"): "a sentinel of the swatch's recolouring (recolour, written once since v0.120, D3): written then replaced, never shown",
    ("svg_icons.py", "#000002"): "a sentinel of the swatch's recolouring",
}
_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_])")


def _colour_literals(path):
    """[(line, literal)] of every colour `path` writes in its code -- a #hex or rgba() in a string, a QColor built from numbers -- its comments and docstrings aside. A transparent QColor(0, 0, 0, 0) is no colour."""
    import io
    import tokenize
    found = []
    tokens = list(tokenize.generate_tokens(io.StringIO(path.read_text(encoding="utf-8")).readline))
    for index, token in enumerate(tokens):
        if token.type == tokenize.STRING:
            previous = tokens[index - 1] if index else None
            standalone = previous is None or previous.type in (tokenize.INDENT, tokenize.NEWLINE, tokenize.NL, tokenize.DEDENT)
            if standalone and token.string.lstrip("rRbBuU")[:3] in ('"' * 3, "'" * 3):
                continue   # a docstring
            found += [(token.start[0], m.group(0).lower()) for m in _HEX.finditer(token.string)]
            if re.search(r"rgba?\(", token.string):
                found.append((token.start[0], "rgba("))
        elif token.type == tokenize.NAME and token.string == "QColor" and index + 2 < len(tokens) and tokens[index + 1].string == "(" and tokens[index + 2].type == tokenize.NUMBER:
            call = "".join(t.string for t in tokens[index:index + 10]).split(")")[0] + ")"
            if call.replace(" ", "") != "QColor(0,0,0,0)":
                found.append((token.start[0], call))
    return found


def test_no_module_of_the_window_writes_a_colour_of_its_own():
    """Issue #29: 49 colours were written in calc/tools/ outside theme.py -- the canvases' selection, snap, track and grid among them. A colour the window draws with is a token of theme.json, named by its role (`plan-select`, `drawing-grid-fine`), read by theme.colour() or theme.qcolor(); what stays written is a constant that recognises a colour, listed in COLOUR_ALLOWED with its reason."""
    offenders, used = [], set()
    for path in sorted(TOOLS.glob("*.py")):
        if path.name == "theme.py":
            continue
        for line, literal in _colour_literals(path):
            if (path.name, literal) in COLOUR_ALLOWED:
                used.add((path.name, literal))
            else:
                offenders.append(f"{path.name}:{line}: {literal}")
    assert not offenders, "a colour written in a module of the window -- make it a token of theme.json:\n" + "\n".join(offenders)
    assert used == set(COLOUR_ALLOWED), f"allowed and no longer there: {set(COLOUR_ALLOWED) - used}"


def test_the_colour_guard_sees_a_colour_and_not_a_comment():
    folder = conftest.tmpdir("colour-guard")
    sample = folder / "sample.py"
    sample.write_text('"""A docstring naming #123456 is prose."""\n# a comment naming #abcdef is prose\nA = "#e67e22"\nB = QColor(198, 40, 40, 46)\nC = QColor(0, 0, 0, 0)\nD = "rgba(0, 0, 0, .5)"\nE = "issue #29"\n', encoding="utf-8")
    assert _colour_literals(sample) == [(3, "#e67e22"), (4, "QColor(198,40,40,46)"), (6, "rgba(")], _colour_literals(sample)


def test_the_canvas_tokens_keep_the_colours_they_replaced_in_both_schemes():
    """Issue #29, annex B of the spec: each token stands for the literal it replaced, so no colour on a canvas changed. Drawn on the sheet, which is paper-white in both schemes, a canvas token has one value in both -- which is also what makes reading it once, when its module is imported, right."""
    replaced = {
        "plan-select": "#e67e22", "plan-crop": "#1f5fbf", "plan-snap": "#d81b60", "plan-storey": "#c62828", "plan-storey-mark": "#d62828",
        "plan-track": "#2f8cff", "plan-align": "#7b1fa2", "plan-dimension": "#1f6feb", "plan-sheet-edge": "#b0b0b0", "plan-shade": "#282828",
        "drawing-grid-fine": "#e4e7ea", "drawing-grid-heavy": "#c9cfd5", "drawing-grid-axis": "#a8b1b9", "drawing-select": "#2f8cff",
        "drawing-hover": "#e67e22", "drawing-crop": "#c0392b", "drawing-crop-veil": "#787878", "drawing-track": "#2f8cff",
        "drawing-snap": "#e8841a", "drawing-readout": "#5a6570", "annex-frame": "#c2410c", "annex-title": "#ffd34d", "badge-ink": "#ffffff",
        "paper": "#ffffff",
    }
    import theme
    for scheme in theme.SCHEMES:
        table = theme.tokens(scheme)
        for name, value in replaced.items():
            assert table[name] == value, f"{scheme} {name}: {table[name]}, it replaced {value}"
    import plan_canvas
    import schema_canvas
    import statics_canvas
    import statics_tab
    from domains import statics_svg
    assert plan_canvas.STOREY_FILL.name() == "#c62828" and plan_canvas.STOREY_FILL.alpha() == 46, "QColor(198, 40, 40, 46), as it was"
    assert schema_canvas.CROP_VEIL.name() == "#787878" and schema_canvas.CROP_VEIL.alpha() == 60, "QColor(120, 120, 120, 60), as it was"
    assert plan_canvas.SELECT_COLOUR.name() == "#e67e22" and schema_canvas.HOVER_COLOUR == "#e67e22"
    assert schema_canvas.GRID_FINE == statics_canvas.GRID_FINE == "#e4e7ea" and statics_canvas.SNAP_COLOUR == "#e8841a"
    assert statics_tab.SWATCH_INK == statics_svg.BAR == "#1f1f1f", "the swatch's ink is the figure's own, read where it is written"


def test_every_text_the_window_sets_is_readable_in_both_schemes():
    """4.5:1 at least, WCAG AA for normal text -- the orange of a value written over included, which stays the report's own in the light scheme (4.7:1 on white) and is a lighter orange in the dark one."""
    theme = _theme()
    pairs = [("ink", "bg"), ("ink-soft", "bg"), ("muted", "bg"), ("muted", "bg-soft"), ("override", "bg"), ("warning", "bg"),
             ("danger", "bg"), ("ok", "bg"), ("ink", "accent-soft"), ("ink", "wood-soft"), ("ink", "danger-soft"), ("ink", "bg-sunk"),
             ("on-primary", "primary"), ("on-primary", "primary-hover"), ("lit-ink", "lit")]
    weak = []
    for scheme in theme.SCHEMES:
        table = theme.tokens(scheme)
        for ink, ground in pairs:
            ratio = _contrast(table[ink], table[ground])
            if ratio < 4.5:
                weak.append(f"{scheme}: {ink} on {ground} is {ratio:.2f}:1")
    assert not weak, "\n".join(weak)


# --- the window -------------------------------------------------------------------------------------------------
# ⚠️ Each check that changes the scheme runs in a process of its own, with one window. The application's style sheet is the whole process's: set again, it re-polishes every widget of every window alive -- and a full run of the suite leaves dozens of Woodcore's windows alive, so a change of scheme took minutes and the suite looked hung twice (v0.90, v0.91). The same checks in a process of their own take seconds, and the suite's own scheme is never touched.

PRELUDE = r"""
import json, os, sys
sys.path[:0] = [sys.argv[1], sys.argv[2]]
from PySide6.QtWidgets import QApplication
app = QApplication([])
import theme
"""


def _in_a_process_of_its_own(body):
    conftest.exported("calculations.json")   # the window reads the export
    settings = conftest.tmpdir("theme-process") / "settings.json"
    settings.write_text('{"lang": "en", "appearance": "light"}', encoding="utf-8")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", WOODCORE_SETTINGS=str(settings), WOODCORE_PROJECT=str(conftest.PROJECT.file), PYTHONIOENCODING="utf-8")
    done = subprocess.run([sys.executable, "-c", PRELUDE + body, str(TOOLS), str(ROOT / "calc")], capture_output=True, text=True, encoding="utf-8", env=env, timeout=300, cwd=str(ROOT))
    assert done.returncode == 0, (done.stdout + done.stderr)[-3000:]
    return done.stdout


def test_the_style_sheet_parses_and_the_application_is_dressed_in_it():
    _qt()
    _in_a_process_of_its_own(r"""
from PySide6.QtCore import qInstallMessageHandler
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QPushButton
complaints = []
qInstallMessageHandler(lambda _kind, _context, message: complaints.append(message))
for scheme in ("dark", "light"):
    theme.apply(app, scheme)
    button = QPushButton("x")
    button.ensurePolished()   # a style sheet is parsed when a widget is polished
    assert theme.scheme() == scheme
    assert app.palette().color(QPalette.ColorRole.Window).name() == theme.tokens(scheme)["bg"]
    assert app.palette().color(QPalette.ColorRole.PlaceholderText).name() == theme.tokens(scheme)["muted"]
    assert theme.tokens(scheme)["accent"] in app.styleSheet()
bad = [m for m in complaints if "style" in m.lower() and "parse" in m.lower()]
assert not bad, bad
""")


def test_every_property_the_window_names_has_its_rule():
    theme = _theme()
    for rule in ('QLabel[callout="info"]', 'QLabel[callout="warning"]', 'QLabel[callout="danger"]',
                 'QPushButton[primary="true"]', 'QToolButton[primary="true"]', 'QPushButton[compact="true"]', 'QGroupBox[hot="true"]'):
        assert rule in theme.STYLE, rule
    used = set()
    for path in TOOLS.glob("*.py"):
        used |= set(re.findall(r'setProperty\("callout", "(\w+)"\)', path.read_text(encoding="utf-8")))
    assert used and used <= {"info", "warning", "danger"}, used


def test_the_choice_is_remembered_and_every_window_is_built_again_in_it():
    _qt()
    _in_a_process_of_its_own(r"""
import usersettings
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

class Window(QWidget):
    rebuilt = 0
    def retheme(self):
        Window.rebuilt += 1

window = Window()
window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
window.show()
theme.apply(app)
assert theme.scheme() == "light"
theme.set_appearance("dark", app)
assert usersettings.read()["appearance"] == "dark" and theme.appearance() == "dark" and theme.scheme() == "dark"
assert Window.rebuilt == 1, Window.rebuilt
theme.set_appearance("dark", app)
assert Window.rebuilt == 1, "the same scheme again builds nothing again"
theme.set_appearance("system", app)   # off screen, Windows answers nothing: light
assert theme.appearance() == "system" and theme.scheme() == "light" and Window.rebuilt == 2, Window.rebuilt
try:
    theme.set_appearance("sepia", app)
except ValueError as exc:
    assert "sepia" in str(exc)
else:
    raise AssertionError("an unknown appearance was accepted")
""")


def test_the_view_menu_offers_the_three_appearances_in_every_language():
    _qt()
    theme = _theme()
    import woodcore_gui
    for lang in ("fr", "de", "en"):
        words = [woodcore_gui.STRINGS[lang][f"file_appearance_{value}"] for value in theme.APPEARANCES]
        assert len(set(words)) == 3 and all(words), (lang, words)
    _in_a_process_of_its_own(r"""
import woodcore_gui
window = woodcore_gui.MainWindow()
menu = window.menuBar().actions()[1].menu()   # «Affichage» since issue #85, «Fichier» until then
sub = next(a.menu() for a in menu.actions() if a.menu() is not None and a.text() == window.t("file_appearance"))
entries = sub.actions()
assert [a.data() for a in entries] == list(theme.APPEARANCES)
assert all(a.isCheckable() for a in entries) and [a.isChecked() for a in entries] == [False, True, False], "the settings say «light»"
assert entries[0].actionGroup() is not None and entries[0].actionGroup().isExclusive()
# the window's own colours are the scheme's, and retheme() takes the new ones
assert window.muted == theme.tokens("light")["muted"]
theme.apply(app, "dark")
window.retheme()
assert window.muted == theme.tokens("dark")["muted"]
assert window.pdf_button.property("primary") is True
for tab in window.tabs:
    if hasattr(tab, "dirty"):
        tab.dirty = False
""")


# --- the fonts ----------------------------------------------------------------------------------------------------
# Asked of Windows' own fonts, in a process of its own on the platform the window runs on: the off-screen platform the suite builds its windows on has no font at all (and pointed at C:\Windows\Fonts it would still not see Cascadia, which Windows Terminal shares with every program without putting it there). The process shows no window.

FONT_PROBE = r"""
import json, sys
from pathlib import Path
# calc/tools/ and calc/, as the window has them: theme reads usersettings, in calc/ since v0.120 (G6)
sys.path[:0] = [sys.argv[1], str(Path(sys.argv[1]).parent)]
from PySide6.QtGui import QFont, QFontInfo, QRawFont
from PySide6.QtWidgets import QApplication
app = QApplication([])
import theme
family = theme.text_family()
mono = theme.mono_font(9)
wanted = sys.argv[2]
raw = QRawFont.fromFont(QFont(family)) if family else None
previous = QRawFont.fromFont(QFont("Segoe UI Variable"))
theme.apply(app, "light")
print(json.dumps({
    "family": family,
    "applied": QFontInfo(app.font()).family(),
    "mono": QFontInfo(mono).family(),
    "mono_fixed": QFontInfo(mono).fixedPitch(),
    "missing": [c for c in wanted if raw is None or not raw.supportsCharacter(ord(c))],
    "rare": {c: [raw.supportsCharacter(ord(c)) if raw else None, previous.supportsCharacter(ord(c)) if previous.familyName() == "Segoe UI Variable" else None] for c in "⩽⩾✔✘⊕⧉"},
}))
"""
# The Greek, the subscript and superscript digits and letters, the relations and operators a calculation is written with.
CALCULATION = "αβγδηλμρστφψωΔΣΦ₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹ₐₑₖⱼ−√·×≤≥≠≈∑∞°‰"


def _fonts():
    if sys.platform != "win32":
        raise conftest.OtherSystem("the fonts asked of are Windows'")
    try:
        import PySide6  # noqa: F401
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    import json
    env = {k: v for k, v in os.environ.items() if k not in ("QT_QPA_PLATFORM", "QT_QPA_FONTDIR")}
    env["PYTHONIOENCODING"] = "utf-8"
    done = subprocess.run([sys.executable, "-c", FONT_PROBE, str(TOOLS), CALCULATION], capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_the_fonts_are_the_site_s_as_a_browser_resolves_them():
    """The first installed family of each stack -- Segoe UI for the text on Windows, and for the code Cascadia Mono where Windows Terminal shares it, else Consolas -- «Inter» and «JetBrains Mono» being named first and loaded by nothing: what the site shows on the same machine (measured in the browser, v0.90)."""
    found = _fonts()
    assert found["family"] == "Segoe UI", found
    assert found["applied"] == "Segoe UI", found
    assert found["mono_fixed"] and found["mono"] in ("Cascadia Mono", "Consolas"), found


def test_the_text_font_carries_what_a_calculation_is_written_with():
    """The engineer's one condition on the typography (v0.90): indices, exponents and the language of mathematics. Segoe UI carries Greek, the subscript and superscript digits and letters, and the relations and operators -- and for the rarer signs (⩽ ⩾ ✔ ✘ ⊕ ⧉) exactly what Segoe UI Variable, the window's font until v0.89, carried: neither has them, and Windows draws them from Segoe UI Symbol or Cambria Math as it did."""
    found = _fonts()
    assert not found["missing"], f"Segoe UI lacks {''.join(found['missing'])}"
    for sign, (ours, before) in found["rare"].items():
        if before is not None:
            assert ours == before, f"{sign}: Segoe UI and Segoe UI Variable differ"


# --- the interface's zoom (issue #85) -----------------------------------------------------------------------------

def test_the_zoom_goes_by_steps_of_ten_between_seventy_and_two_hundred():
    theme = _theme()
    assert (theme.ZOOM_MIN, theme.ZOOM_MAX, theme.ZOOM_STEP, theme.ZOOM_DEFAULT) == (70, 200, 10, 100)
    assert [theme.clamp_zoom(p) for p in (100, 104, 106, 69, 30, 201, 500, "x", None, float("nan"))] == [100, 100, 110, 70, 70, 200, 200, 100, 100, 100]


def test_the_zoom_is_kept_in_the_user_s_settings_survives_a_change_of_scheme_and_builds_the_windows_once():
    _qt()
    _in_a_process_of_its_own(r"""
import time
import usersettings
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

class Window(QWidget):
    rezoomed = 0
    def rezoom(self):
        Window.rezoomed += 1

window = Window()
window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
window.show()
theme.apply(app)
base = app.font().pointSizeF()
assert theme.zoom() == 100
for _ in range(5):   # a burst of Ctrl+ is one rebuild
    theme.zoom_in(app)
assert theme.zoom() == 150 and usersettings.read()["ui_zoom"] == 150
assert abs(app.font().pointSizeF() - base * 1.5) < 0.01, (base, app.font().pointSizeF())
assert Window.rezoomed == 0, "built again at every step"
end = time.monotonic() + 2
while time.monotonic() < end and not Window.rezoomed:
    app.processEvents()
    time.sleep(0.02)
assert Window.rezoomed == 1, Window.rezoomed
theme.apply(app, "dark")   # a change of scheme keeps the zoom
assert abs(app.font().pointSizeF() - base * 1.5) < 0.01, app.font().pointSizeF()
assert abs(theme.brand_font().pointSizeF() - theme.BRAND_POINTS * 1.5) < 0.01
for _ in range(20):
    theme.zoom_in(app)
assert theme.zoom() == 200
for _ in range(30):
    theme.zoom_out(app)
assert theme.zoom() == 70
theme.zoom_reset(app)
assert theme.zoom() == 100 and abs(app.font().pointSizeF() - base) < 0.01 and usersettings.read()["ui_zoom"] == 100
theme._state["zoom"] = None   # read again from the settings, as at the next start
assert theme.zoom() == 100
""")


def test_the_view_menu_holds_the_zoom_and_the_appearance_and_the_window_takes_the_zoom():
    _qt()
    import woodcore_gui
    for lang in ("fr", "de", "en"):
        words = [woodcore_gui.STRINGS[lang][key] for key in ("view_menu", "zoom_in", "zoom_out", "zoom_reset", "zoom_status")]
        assert all(words) and "{percent}" in words[-1], (lang, words)
    assert woodcore_gui.STRINGS["fr"]["view_menu"].replace("&", "") == "Affichage" and woodcore_gui.STRINGS["de"]["view_menu"].replace("&", "") == "Ansicht" and woodcore_gui.STRINGS["en"]["view_menu"].replace("&", "") == "View"
    _in_a_process_of_its_own(r"""
import woodcore_gui
from PySide6.QtGui import QKeySequence
window = woodcore_gui.MainWindow()
menus = [a.menu() for a in window.menuBar().actions()]
titles = [m.title() for m in menus]
assert titles[:2] == [window.t("file_menu"), window.t("view_menu")], titles
file_menu, view = menus[0], menus[1]
assert not any(a.menu() is not None and a.text() == window.t("file_appearance") for a in file_menu.actions()), "«Apparence» still in «Fichier»"
assert any(a.menu() is not None and a.text() == window.t("file_appearance") for a in view.actions())
keys = {a.text(): [k.toString() for k in a.shortcuts()] for a in view.actions() if a.text()}
assert keys[window.t("zoom_in")] == ["Ctrl++", "Ctrl+="] and keys[window.t("zoom_out")] == ["Ctrl+-"] and keys[window.t("zoom_reset")] == ["Ctrl+0"], keys
assert window.zoom_status.isHidden(), "«Zoom 100 %» said"
title = window.title_font.pointSizeF()
next(a for a in view.actions() if a.text() == window.t("zoom_in")).trigger()
assert theme.zoom() == 110
window.rezoom()
assert abs(window.title_font.pointSizeF() - title * 1.1) < 0.05, (title, window.title_font.pointSizeF())
assert not window.zoom_status.isHidden() and window.zoom_status.text() == window.t("zoom_status", percent=110), window.zoom_status.text()
for tab in window.tabs:
    if hasattr(tab, "dirty"):
        tab.dirty = False
""")


def test_the_start_page_takes_the_zoom_s_keys_too():
    _qt()
    _in_a_process_of_its_own(r"""
import home_page
page = home_page.HomeWindow(lambda file: None)
keys = sorted(k.toString() for a in page.centralWidget().actions() for k in a.shortcuts())
assert keys == sorted(["Ctrl++", "Ctrl+=", "Ctrl+-", "Ctrl+0"]), keys
""")
