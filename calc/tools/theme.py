"""Woodcore's look (docs/ui/window.md §10quater, v0.90): the website's, in the window.

`theme.json` beside this module holds every colour of Woodcore, for a light and a dark scheme, with the two font stacks -- the website's CSS custom properties, which `website/build.py` writes into `assets/site.css` through `css_tokens()`, and what this module builds the window's palette and style sheet from. One file, two readers: the site and the window cannot come to show two teals.

The window follows Windows' light or dark theme unless the engineer chose one in *Fichier → Apparence* -- `appearance` in the user's settings, "system", "light" or "dark". The Qt style is Fusion, dressed by the palette and the style sheet built here, where it was Windows 11's own until v0.89: the same look on Windows 10 and 11, off screen in the tests, and a style sheet that reads the same everywhere.

The fonts are the site's as a browser resolves them: the first family of each stack that is installed. On Windows that is Segoe UI for the text and Cascadia Mono for the code -- what the site shows there, «Inter» and «JetBrains Mono» being named first in its style sheet and loaded by nothing (measured in the browser, v0.90). Cascadia Mono is Cascadia Code without its ligatures, which the site turns off: code shows what is typed, `<=` two characters.

⚠️ Nothing at the top of this module imports Qt: `website/build.py` imports it for `css_tokens()`, in a CI image that has no PySide6.
"""

import json
from pathlib import Path

import usersettings

HERE = Path(__file__).resolve().parent
TOKENS_FILE = HERE / "theme.json"
SCHEMA_VERSION = "1.0"
SCHEMES = ("light", "dark")
APPEARANCES = ("system", "light", "dark")
SETTING = "appearance"
# The interface's zoom (issue #85, the engineer, 21.10.2026: «Je valide la fonctionnalité de zoom de l'interface avec CTRL plus et CTRL moins»): a percentage kept in the user's settings and never in a project, from ZOOM_MIN to ZOOM_MAX by ZOOM_STEP, 100 the size Qt gives the screen.
ZOOM_SETTING = "ui_zoom"
ZOOM_MIN, ZOOM_MAX, ZOOM_STEP, ZOOM_DEFAULT = 70, 200, 10, 100
# How long the windows wait after the last step of the zoom before they are built again: a burst of Ctrl+wheel is one rebuild, which costs seconds (review ARCH-RISK-304).
ZOOM_REBUILD_MS = 300
# The project's name in the top bar, in points at 100 %: the font of a label the style sheet no longer sizes, so that it follows the zoom without the style sheet set again.
BRAND_POINTS = 13
# The CSS generic families: a browser's to resolve, never a family Qt could be asked for.
GENERIC = {"ui-sans-serif", "ui-serif", "ui-monospace", "system-ui", "-apple-system", "sans-serif", "serif", "monospace", "cursive", "fantasy"}

_tokens = None
_state = {"scheme": None, "appearance": None, "base_size": None, "listening": False, "applying": False, "zoom": None, "timer": None}


# --- the tokens -----------------------------------------------------------------------------------------------

def load():
    """theme.json, read once and checked: the same names in both schemes, each a string."""
    global _tokens
    if _tokens is None:
        data = json.loads(TOKENS_FILE.read_text(encoding="utf-8"))
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"{TOKENS_FILE.name}: schema_version {data.get('schema_version')!r}, expected {SCHEMA_VERSION!r}")
        for key in ("font", "mono", "radius", *SCHEMES):
            if key not in data:
                raise ValueError(f"{TOKENS_FILE.name}: no '{key}'")
        light, dark = set(data["light"]), set(data["dark"])
        if light != dark:
            raise ValueError(f"{TOKENS_FILE.name}: the schemes name different tokens -- light only {sorted(light - dark)}, dark only {sorted(dark - light)}")
        for scheme in SCHEMES:
            for name, value in data[scheme].items():
                if not isinstance(value, str) or not value:
                    raise ValueError(f"{TOKENS_FILE.name}: {scheme}.{name} is not a value")
        _tokens = data
    return _tokens


def tokens(scheme):
    """Every token of `scheme`, "light" or "dark", by its name (`bg-soft`, `accent`, `override`)."""
    if scheme not in SCHEMES:
        raise ValueError(f"unknown scheme {scheme!r} -- expected one of {SCHEMES}")
    return dict(load()[scheme])


def qcolor(name, alpha=None):
    """One token as a QColor, `alpha` (0-255) given where the canvas draws it translucent -- what a drawing surface paints with (v0.117, issue #29: its colours were written in its module). Qt imported here and not at the top: website/build.py imports this module without PySide6."""
    from PySide6.QtGui import QColor
    colour = QColor(colour_of(name))
    if alpha is not None:
        colour.setAlpha(alpha)
    return colour


def colour_of(name):
    """colour(), under a name a module can import beside its own `colour` variables."""
    return colour(name)


def scheme():
    """The scheme the window is dressed in: "light" until `apply()` has run."""
    return _state["scheme"] or "light"


def colour(name):
    """One token of the scheme in force -- what a widget that states a colour of its own reads, when it is built: the orange of a value written over, the ground of a cell that could not be read."""
    table = tokens(scheme())
    if name not in table:
        raise KeyError(f"{TOKENS_FILE.name} has no token '{name}'")
    return table[name]


def families(stack):
    """The named families of a CSS font stack, in order, their quotes taken off and the generic ones left out."""
    names = []
    for part in stack.split(","):
        name = part.strip().strip('"').strip("'")
        if name and name.lower() not in GENERIC:
            names.append(name)
    return names


def css_tokens():
    """The two `:root` blocks of the website's style sheet, every token a CSS custom property, the dark ones under `prefers-color-scheme: dark` -- what website/build.py writes into assets/site.css where its marker stands."""
    data = load()

    def block(scheme, indent):
        lines = [f"{indent}--{name}: {value};" for name, value in data[scheme].items()]
        if scheme == "light":
            lines += [f"{indent}--radius: {data['radius']};", f"{indent}--font: {data['font']};", f"{indent}--mono: {data['mono']};"]
        lines.append(f"{indent}color-scheme: {scheme};")
        return "\n".join(lines)

    return (
        ":root {\n" + block("light", "  ") + "\n}\n\n"
        "@media (prefers-color-scheme: dark) {\n  :root {\n" + block("dark", "    ") + "\n  }\n}\n"
    )


# --- the window's preference --------------------------------------------------------------------------------

def appearance():
    """What the engineer chose in *Fichier → Apparence*: "system" (the default), "light" or "dark"."""
    chosen = usersettings.read().get(SETTING)
    return chosen if chosen in APPEARANCES else "system"


def resolve(chosen):
    """The scheme an appearance comes to: "system" asks Windows, which answers dark or light -- and off screen, where there is no Windows to ask, light."""
    if chosen in SCHEMES:
        return chosen
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication.instance()
    if app is not None and app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
        return "dark"
    return "light"


# --- what Qt reads --------------------------------------------------------------------------------------------

def installed(stack):
    """The first family of `stack` this machine has, as a browser resolves the stack; None where it has none. Asked of each font itself -- QFontInfo -- rather than of the list of every family, which took a second on this machine (the window's own module, v0.64)."""
    from PySide6.QtGui import QFont, QFontInfo
    for name in families(stack):
        if QFontInfo(QFont(name)).family().lower() == name.lower():
            return name
    return None


def text_family():
    return installed(load()["font"])


def mono_font(point_size=None):
    """The font code is set in: the first installed family of the mono stack, Cascadia Mono on Windows -- the site's -- else Qt's own fixed font."""
    from PySide6.QtGui import QFont, QFontDatabase
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    name = installed(load()["mono"])
    if name:
        font.setFamily(name)
    font.setStyleHint(QFont.StyleHint.Monospace)
    if point_size and point_size > 0:
        font.setPointSizeF(point_size)
    return font


def palette(t):
    """The palette of scheme `t`: the window white (dark in the dark scheme), the text ink, the highlight the accent -- what Fusion draws every widget the style sheet does not reach with."""
    from PySide6.QtGui import QColor, QPalette
    p = QPalette()
    c = lambda name: QColor(t[name])  # noqa: E731
    roles = {
        QPalette.ColorRole.Window: "bg", QPalette.ColorRole.WindowText: "ink",
        QPalette.ColorRole.Base: "bg", QPalette.ColorRole.AlternateBase: "bg-soft",
        QPalette.ColorRole.Text: "ink", QPalette.ColorRole.BrightText: "bg",
        QPalette.ColorRole.Button: "bg", QPalette.ColorRole.ButtonText: "ink",
        # a checked box, a selection, a slider: the primary teal with the ink the primary button reads in -- in the light scheme the stronger teal, the lighter one carrying white at 3.2:1 only
        QPalette.ColorRole.Highlight: "primary", QPalette.ColorRole.HighlightedText: "on-primary",
        QPalette.ColorRole.PlaceholderText: "muted",
        QPalette.ColorRole.Link: "accent-strong", QPalette.ColorRole.LinkVisited: "accent-strong",
        QPalette.ColorRole.ToolTipBase: "ink", QPalette.ColorRole.ToolTipText: "bg",
        QPalette.ColorRole.Light: "bg", QPalette.ColorRole.Midlight: "line",
        QPalette.ColorRole.Mid: "line-strong", QPalette.ColorRole.Dark: "line-strong",
        QPalette.ColorRole.Shadow: "line-strong",
    }
    for role, name in roles.items():
        p.setColor(QPalette.ColorGroup.All, role, c(name))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, role, c("muted"))
    for role in (QPalette.ColorRole.Base, QPalette.ColorRole.Button):
        p.setColor(QPalette.ColorGroup.Disabled, role, c("bg-soft"))
    return p


def _svgs(t):
    """The small pictures the style sheet names, in scheme `t`: the arrows of a combo box, a spin box and a split button, in the muted ink (and in the primary button's own); and the boxes of a check box and a radio button, which Fusion draws in lines too faint to find on the dark scheme -- outlined in the muted ink, filled with the primary teal once ticked, the site's own check."""
    arrow = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6" viewBox="0 0 10 6"><path d="{d}" fill="none" stroke="{ink}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    box = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><rect x="1" y="1" width="14" height="14" rx="3.5" fill="{fill}" stroke="{line}" stroke-width="1.4"/>{mark}</svg>'
    ring = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.8" fill="{fill}" stroke="{line}" stroke-width="1.4"/>{mark}</svg>'
    tick = '<path d="M4.3 8.3l2.5 2.5 5-5.4" fill="none" stroke="{ink}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
    dash = '<path d="M4.5 8h7" stroke="{ink}" stroke-width="1.8" stroke-linecap="round"/>'
    dot = '<circle cx="8" cy="8" r="3" fill="{ink}"/>'
    on, off_line, dim = t["primary"], t["muted"], t["line-strong"]
    return {
        "down": arrow.format(d="M1 1l4 4 4-4", ink=t["muted"]),
        "up": arrow.format(d="M1 5l4-4 4 4", ink=t["muted"]),
        "down-primary": arrow.format(d="M1 1l4 4 4-4", ink=t["on-primary"]),
        "box-off": box.format(fill=t["bg"], line=off_line, mark=""),
        "box-on": box.format(fill=on, line=on, mark=tick.format(ink=t["on-primary"])),
        "box-part": box.format(fill=on, line=on, mark=dash.format(ink=t["on-primary"])),
        "box-off-disabled": box.format(fill=t["bg-soft"], line=dim, mark=""),
        "box-on-disabled": box.format(fill=t["bg-soft"], line=dim, mark=tick.format(ink=t["muted"])),
        "radio-off": ring.format(fill=t["bg"], line=off_line, mark=""),
        "radio-on": ring.format(fill=t["bg"], line=on, mark=dot.format(ink=on)),
        "radio-off-disabled": ring.format(fill=t["bg-soft"], line=dim, mark=""),
        "radio-on-disabled": ring.format(fill=t["bg-soft"], line=dim, mark=dot.format(ink=t["muted"])),
    }


def images(t):
    """`_svgs(t)` as files -- a style sheet names an image by its path -- written once into Woodcore's caches (`%LOCALAPPDATA%\\Woodcore\\theme\\`), each named after its own content so a colour changed in theme.json is a file of its own. Returns their paths by name."""
    import hashlib
    folder = usersettings.cache_dir("theme")
    paths = {}
    for name, svg in _svgs(t).items():
        file = folder / f"{name}-{hashlib.sha256(svg.encode('utf-8')).hexdigest()[:10]}.svg"
        if not file.is_file():
            try:
                folder.mkdir(parents=True, exist_ok=True)
                file.write_text(svg, encoding="utf-8", newline="\n")
            except OSError:
                pass  # a picture not drawn is not worth stopping the window for; Fusion draws none then
        paths[name] = file.as_posix()
    return paths


# One style sheet for the whole window. Compact, as the engineer chose (v0.90): the rows keep about the height they had, the air is in the rounding, the lines and the colours. Every value is a token; nothing here is a colour of its own.
STYLE = """
QToolTip {{ color: {bg}; background: {ink}; border: none; padding: 4px 7px; border-radius: 6px; }}

QMenuBar {{ background: {bg}; border-bottom: 1px solid {line}; }}
QMenuBar::item {{ padding: 4px 10px; border-radius: 6px; background: transparent; }}
QMenuBar::item:selected {{ background: {bg_sunk}; }}
QMenu {{ background: {bg}; border: 1px solid {line_strong}; border-radius: 8px; padding: 4px; }}
QMenu::item {{ padding: 5px 24px 5px 26px; border-radius: 6px; }}
QMenu::item:selected {{ background: {accent_soft}; color: {ink}; }}
QMenu::item:disabled {{ color: {muted}; }}
QMenu::separator {{ height: 1px; background: {line}; margin: 4px 8px; }}

QTabWidget::pane {{ border: none; border-top: 1px solid {line}; top: -1px; }}
QTabBar::tab {{ background: transparent; color: {muted}; padding: 6px 12px 5px 12px; margin-right: 2px; border: none; border-bottom: 2px solid transparent; }}
QTabBar::tab:hover {{ color: {ink}; }}
QTabBar::tab:selected {{ color: {ink}; border-bottom: 2px solid {accent}; }}

QPushButton {{ background: {bg}; color: {ink}; border: 1px solid {line_strong}; border-radius: 6px; padding: 4px 10px; }}
QPushButton:hover {{ background: {bg_sunk}; }}
QPushButton:pressed {{ background: {bg_sunk}; border-color: {muted}; }}
QPushButton:checked {{ background: {accent_soft}; border-color: {accent}; }}
QPushButton:focus, QPushButton:default {{ border-color: {accent}; }}
QPushButton:disabled {{ color: {muted}; background: {bg_soft}; border-color: {line}; }}
QPushButton[primary="true"] {{ background: {primary}; color: {on_primary}; border-color: {primary}; font-weight: 600; }}
QPushButton[compact="true"] {{ padding: 3px 0; }}
QPushButton[primary="true"]:hover {{ background: {primary_hover}; border-color: {primary_hover}; }}

QToolButton {{ background: {bg}; color: {ink}; border: 1px solid {line}; border-radius: 6px; padding: 2px; }}
QToolButton:hover {{ background: {bg_sunk}; border-color: {line_strong}; }}
QToolButton:pressed {{ background: {bg_sunk}; }}
QToolButton:checked {{ background: {accent_soft}; border-color: {accent}; color: {ink}; }}
QToolButton:disabled {{ color: {muted}; background: {bg_soft}; border-color: {line}; }}
QToolButton[popupMode="1"] {{ border-color: {line_strong}; padding: 4px 28px 4px 12px; }}
QToolButton[popupMode="1"]::menu-button {{ border: none; border-left: 1px solid {line_strong}; width: 20px; }}
QToolButton::menu-arrow {{ image: url({img_down}); width: 10px; height: 6px; }}
QToolButton::menu-indicator {{ image: url({img_down}); width: 8px; height: 5px; subcontrol-origin: padding; subcontrol-position: bottom right; }}
QToolButton[primary="true"] {{ background: {primary}; color: {on_primary}; border-color: {primary}; font-weight: 600; }}
QToolButton[primary="true"]:hover {{ background: {primary_hover}; border-color: {primary_hover}; }}
QToolButton[primary="true"]::menu-button {{ border-left: 1px solid {on_primary}; }}
QToolButton[primary="true"]::menu-arrow {{ image: url({img_down_primary}); }}
QToolButton[primary="true"]:disabled {{ background: {bg_soft}; color: {muted}; border-color: {line}; }}
QFrame#toolSeparator {{ background: transparent; border: none; border-left: 1px solid {line_strong}; margin: 5px 5px 5px 5px; }}
QComboBox[compact="true"] {{ padding-left: 5px; padding-right: 2px; }}

QLineEdit, QAbstractSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{ background: {bg}; color: {ink}; border: 1px solid {line_strong}; border-radius: 6px; padding: 2px 6px; selection-background-color: {accent_soft}; selection-color: {ink}; }}
QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{ border-color: {accent}; }}
QLineEdit:read-only, QPlainTextEdit:read-only, QTextEdit:read-only {{ background: {bg_soft}; }}
QLineEdit:disabled, QAbstractSpinBox:disabled, QComboBox:disabled {{ background: {bg_soft}; color: {muted}; border-color: {line}; }}
QComboBox {{ padding-right: 22px; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right; width: 20px; border: none; }}
QComboBox::down-arrow {{ image: url({img_down}); width: 10px; height: 6px; }}
QComboBox QAbstractItemView {{ background: {bg}; border: 1px solid {line_strong}; border-radius: 6px; selection-background-color: {accent_soft}; selection-color: {ink}; outline: 0; }}
QAbstractSpinBox {{ padding-right: 18px; }}
QAbstractSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 16px; border: none; background: transparent; margin: 2px 2px 0 0; }}
QAbstractSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 16px; border: none; background: transparent; margin: 0 2px 2px 0; }}
QAbstractSpinBox::up-arrow {{ image: url({img_up}); width: 9px; height: 5px; }}
QAbstractSpinBox::down-arrow {{ image: url({img_down}); width: 9px; height: 5px; }}
QAbstractItemView QLineEdit, QAbstractItemView QAbstractSpinBox, QAbstractItemView QComboBox {{ border-radius: 0; padding-top: 0; padding-bottom: 0; }}

QAbstractItemView {{ background: {bg}; alternate-background-color: {bg_soft}; border: 1px solid {line}; border-radius: 8px; selection-background-color: {accent_soft}; selection-color: {ink}; outline: 0; }}
QAbstractItemView::item {{ padding: 1px 2px; }}
QAbstractItemView::item:hover {{ background: {bg_soft}; }}
QAbstractItemView::item:selected {{ background: {accent_soft}; color: {ink}; }}
QHeaderView {{ background: {bg}; border: none; }}
QHeaderView::section {{ background: {bg}; color: {muted}; font-weight: 600; padding: 4px 6px; border: none; border-bottom: 1px solid {line_strong}; border-right: 1px solid {line}; }}
QHeaderView::up-arrow {{ image: url({img_up}); width: 9px; height: 5px; }}
QHeaderView::down-arrow {{ image: url({img_down}); width: 9px; height: 5px; }}
QTableCornerButton::section {{ background: {bg}; border: none; border-bottom: 1px solid {line_strong}; }}

QGroupBox {{ background: {bg}; border: 1px solid {line}; border-radius: 8px; margin-top: 1.3em; padding: 0.35em 4px 4px 4px; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 8px; padding: 0 4px; color: {muted}; font-weight: 600; }}
QGroupBox[flat="true"] {{ border-color: transparent; background: transparent; }}
QGroupBox[hot="true"] {{ border-color: {lit_line}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {line_strong}; border-radius: 4px; min-height: 24px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {line_strong}; border-radius: 4px; min-width: 24px; margin: 2px; }}
QScrollBar::handle:hover {{ background: {muted}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: none; background: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QCheckBox::indicator, QRadioButton::indicator, QAbstractItemView::indicator, QGroupBox::indicator {{ width: 16px; height: 16px; }}
QCheckBox::indicator:unchecked, QAbstractItemView::indicator:unchecked, QGroupBox::indicator:unchecked {{ image: url({img_box_off}); }}
QCheckBox::indicator:checked, QAbstractItemView::indicator:checked, QGroupBox::indicator:checked {{ image: url({img_box_on}); }}
QCheckBox::indicator:indeterminate, QAbstractItemView::indicator:indeterminate {{ image: url({img_box_part}); }}
QCheckBox::indicator:unchecked:disabled, QAbstractItemView::indicator:unchecked:disabled {{ image: url({img_box_off_disabled}); }}
QCheckBox::indicator:checked:disabled, QAbstractItemView::indicator:checked:disabled {{ image: url({img_box_on_disabled}); }}
QRadioButton::indicator:unchecked {{ image: url({img_radio_off}); }}
QRadioButton::indicator:checked {{ image: url({img_radio_on}); }}
QRadioButton::indicator:unchecked:disabled {{ image: url({img_radio_off_disabled}); }}
QRadioButton::indicator:checked:disabled {{ image: url({img_radio_on_disabled}); }}

QSlider::groove:horizontal {{ height: 4px; background: {line_strong}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {bg}; border: 2px solid {accent}; width: 12px; height: 12px; margin: -6px 0; border-radius: 8px; }}

QStatusBar {{ background: {bg_soft}; border-top: 1px solid {line}; }}
QStatusBar::item {{ border: none; }}

QToolButton[segment="first"], QToolButton[segment="middle"], QToolButton[segment="last"] {{ border-radius: 0; padding: 3px 9px; font-weight: 600; color: {muted}; background: {bg}; border: 1px solid {line_strong}; margin: 0; }}
QToolButton[segment="middle"], QToolButton[segment="last"] {{ border-left: none; }}
QToolButton[segment="first"] {{ border-top-left-radius: 6px; border-bottom-left-radius: 6px; }}
QToolButton[segment="last"] {{ border-top-right-radius: 6px; border-bottom-right-radius: 6px; }}
QToolButton[segment="first"]:hover, QToolButton[segment="middle"]:hover, QToolButton[segment="last"]:hover {{ color: {ink}; background: {bg_soft}; }}
QToolButton[segment="first"]:checked, QToolButton[segment="middle"]:checked, QToolButton[segment="last"]:checked {{ background: {ink}; color: {bg}; border-color: {ink}; }}
QToolButton[segment][soft="true"] {{ padding: 1px 7px; font-weight: 500; }}
QToolButton[segment][soft="true"]:checked {{ background: {accent_soft}; color: {accent_strong}; border-color: {line_strong}; font-weight: 700; }}
QToolButton[chip="true"] {{ border-radius: 11px; padding: 2px 10px; background: {wood_soft}; border: 1px solid {wood}; color: {ink}; }}
QToolButton[chip="true"]:hover {{ background: {bg_sunk}; }}
QLabel#brand {{ color: {ink}; }}
QLabel#meta, QLabel#cardText {{ color: {muted}; }}
QLabel#eyebrow {{ color: {accent_strong}; font-weight: 700; }}
QLabel#cardTitle {{ font-weight: 600; color: {ink}; }}
QLabel#cardIcon {{ background: {accent_soft}; border-radius: 9px; }}
QListWidget#nav {{ background: {bg}; border: none; border-right: 1px solid {line}; border-radius: 0; padding: 6px 0; }}
QToolButton#fold {{ border: none; background: transparent; padding: 4px; }}
QToolButton#fold:hover {{ background: {bg_soft}; }}
QWidget#sizeGrip {{ border-bottom: 1px solid {line}; margin: 0 8px; }}
QWidget#sizeGrip:hover {{ border-bottom: 2px solid {accent}; }}
QTabWidget#modules::pane {{ border: none; }}
QFrame#card {{ background: {bg}; border: 1px solid {line}; border-radius: 10px; }}
QFrame#card:hover, QFrame#card:focus {{ border-color: {accent}; background: {bg_soft}; }}
QTreeWidget#recent {{ border: none; background: transparent; }}

QLabel#code {{ background: {code_bg}; color: {ink}; border: 1px solid {line}; border-radius: 6px; padding: 3px 7px; }}
QPlainTextEdit#code {{ background: {code_bg}; color: {ink}; border: 1px solid {line}; border-radius: 6px; padding: 2px 4px; }}
QPushButton[done="true"] {{ color: {accent_strong}; border-color: {accent}; background: {accent_soft}; }}

QWidget#cardGround {{ background: {bg_soft}; }}
QGroupBox[card="true"] {{ background: {card}; border: 1px solid {line}; border-radius: 10px; margin-top: 0; padding: 26px 2px 2px 2px; font-weight: 600; }}
QGroupBox[card="true"]::title {{ subcontrol-origin: padding; subcontrol-position: top left; left: 10px; top: 8px; padding: 0; color: {ink}; }}
QGroupBox[card="true"][hot="true"] {{ border-color: {lit_line}; }}
QLabel#cardNote {{ color: {muted}; }}
QLabel#cardBadge {{ background: {accent_soft}; color: {accent_strong}; border-radius: 11px; font-weight: 600; }}

QLabel[callout="info"] {{ background: {accent_soft}; color: {ink}; border: none; border-left: 3px solid {accent}; border-radius: 4px; padding: 5px 10px; }}
QLabel[callout="warning"] {{ background: {wood_soft}; color: {ink}; border: none; border-left: 3px solid {wood}; border-radius: 4px; padding: 5px 10px; }}
QLabel[callout="danger"] {{ background: {danger_soft}; color: {ink}; border: none; border-left: 3px solid {danger}; border-radius: 4px; padding: 5px 10px; }}
"""


def style_sheet(t):
    """The window's style sheet in scheme `t`."""
    pictures = {f"img_{name.replace('-', '_')}": path for name, path in images(t).items()}
    names = {name.replace("-", "_"): value for name, value in t.items()}
    return STYLE.format(**pictures, **names)


def apply(app=None, chosen=None):
    """Dresses the application in the scheme `chosen` comes to -- the engineer's appearance where none is given -- and returns that scheme. Every window of the process takes it at once: the palette, the fonts and the style sheet are the application's. A widget that stated a colour of its own when it was built states the old one until it is built again, which `retheme()` on each window is for."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication, QStyleFactory
    app = app or QApplication.instance()
    if app is None:
        return scheme()
    chosen = chosen if chosen in APPEARANCES else appearance()
    hints = QGuiApplication.styleHints()
    # The title bar and the native dialogs follow the scheme Qt is told of: the engineer's where he chose one, Windows' where he did not -- Unknown hands it back to Windows. Set before the palette, and with `applying` up, since the call sends colorSchemeChanged, which _system_changed would otherwise answer with a second apply.
    wanted = {"light": Qt.ColorScheme.Light, "dark": Qt.ColorScheme.Dark}.get(chosen, Qt.ColorScheme.Unknown)
    previous = _state["appearance"]
    _state["applying"] = True
    try:
        if hasattr(hints, "setColorScheme") and (chosen != "system" or previous not in (None, "system")):
            hints.setColorScheme(wanted)
    finally:
        _state["applying"] = False
    resolved = resolve(chosen)
    if resolved == _state["scheme"]:
        # already dressed in it: setting the style sheet again re-polishes every widget of every window for nothing -- seconds, with many windows open
        _state["appearance"] = chosen
        return resolved
    t = tokens(resolved)
    if _state["base_size"] is None:
        _state["base_size"] = app.font().pointSizeF()
        app.setStyle(QStyleFactory.create("Fusion"))
    app.setPalette(palette(t))
    font = app.font()
    family = text_family()
    if family:
        font.setFamily(family)
    if _state["base_size"] and _state["base_size"] > 0:
        font.setPointSizeF(_state["base_size"] * zoom() / 100)   # the zoom kept through a change of scheme (issue #85)
    app.setFont(font)
    app.setStyleSheet(style_sheet(t))
    _state.update(scheme=resolved, appearance=chosen)
    if not _state["listening"]:
        hints.colorSchemeChanged.connect(_system_changed)
        _state["listening"] = True
    return resolved


def ensure(app=None):
    """`apply()` once per process: what a window calls first, so that a window built without `main()` -- a test's -- is dressed as the engineer sees it."""
    if _state["scheme"] is None:
        apply(app)
    return scheme()


def set_appearance(chosen, app=None):
    """The engineer's choice in *Fichier → Apparence*: written into the settings, applied, and every window built again in it."""
    if chosen not in APPEARANCES:
        raise ValueError(f"unknown appearance {chosen!r} -- expected one of {APPEARANCES}")
    settings = usersettings.read()
    settings[SETTING] = chosen
    usersettings.write(settings)
    before = _state["scheme"]
    apply(app, chosen)
    if _state["scheme"] != before:
        retheme_windows(app)


# --- the interface's zoom (issue #85) ----------------------------------------------------------------------------

def clamp_zoom(percent):
    """`percent` brought onto the steps between ZOOM_MIN and ZOOM_MAX; ZOOM_DEFAULT for what is not a number."""
    try:
        percent = float(percent)
    except (TypeError, ValueError):
        return ZOOM_DEFAULT
    if percent != percent:   # NaN
        return ZOOM_DEFAULT
    stepped = int(round(percent / ZOOM_STEP)) * ZOOM_STEP
    return max(ZOOM_MIN, min(ZOOM_MAX, stepped))


def zoom():
    """The interface's zoom in percent, as the user's settings keep it -- read once per process, then what `set_zoom` made it."""
    if _state["zoom"] is None:
        _state["zoom"] = clamp_zoom(usersettings.read().get(ZOOM_SETTING, ZOOM_DEFAULT))
    return _state["zoom"]


def scaled(px):
    """`px`, a size of the window's frame stated at 100 %, at the zoom in force: the navigation's width and rows, the buttons of the frame (issue #85). The other fixed sizes of the tabs stay as they are."""
    return int(round(px * zoom() / 100))


def brand_font(base=None):
    """The font of the project's name in the top bar, and of «Woodcore» on the start page: bold, BRAND_POINTS at 100 %, following the zoom."""
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication
    font = QFont(base if base is not None else QApplication.font())
    font.setBold(True)
    font.setPointSizeF(BRAND_POINTS * zoom() / 100)
    return font


def set_zoom(percent, app=None):
    """The interface zoomed to `percent` (brought onto the steps): kept in the user's settings, the application's font set at once -- which every widget that inherits it follows --, and every window built again `ZOOM_REBUILD_MS` after the last step, for what took a copy of the font when it was built. The style sheet is not set again, which would re-polish every widget for seconds. Returns the zoom now in force."""
    from PySide6.QtWidgets import QApplication
    percent = clamp_zoom(percent)
    if percent == zoom():
        return percent
    settings = usersettings.read()
    settings[ZOOM_SETTING] = percent
    usersettings.write(settings)
    _state["zoom"] = percent
    app = app or QApplication.instance()
    if app is None:
        return percent
    ensure(app)
    if _state["base_size"] and _state["base_size"] > 0:
        font = app.font()
        font.setPointSizeF(_state["base_size"] * percent / 100)
        app.setFont(font)
    _rezoom_later(app)
    return percent


def zoom_in(app=None):
    return set_zoom(zoom() + ZOOM_STEP, app)


def zoom_out(app=None):
    return set_zoom(zoom() - ZOOM_STEP, app)


def zoom_reset(app=None):
    return set_zoom(ZOOM_DEFAULT, app)


def _rezoom_later(app):
    """The windows built again once the zoom has stopped moving: one timer for the process, started again at every step."""
    from PySide6.QtCore import QTimer
    timer = _state["timer"]
    if timer is None:
        timer = QTimer()
        timer.setSingleShot(True)
        timer.setInterval(ZOOM_REBUILD_MS)
        timer.timeout.connect(lambda: rezoom_windows(app))
        _state["timer"] = timer
    timer.start()


def rezoom_windows(app=None):
    """Every top-level window that knows how to take the zoom (`rezoom`), or else to build itself again (`retheme`), does so."""
    from PySide6.QtWidgets import QApplication
    app = app or QApplication.instance()
    if app is None:
        return
    for window in app.topLevelWidgets():
        rebuild = getattr(window, "rezoom", None) or getattr(window, "retheme", None)
        if callable(rebuild):
            rebuild()


def retheme_windows(app=None):
    """Every top-level window that knows how to build itself again (`retheme`) does so: a widget that stated a colour of its own -- the orange of a value written over -- states the new scheme's."""
    from PySide6.QtWidgets import QApplication
    app = app or QApplication.instance()
    if app is None:
        return
    for window in app.topLevelWidgets():
        rebuild = getattr(window, "retheme", None)
        if callable(rebuild):
            rebuild()


def _system_changed(*_args):
    """Windows switched between light and dark: followed where the engineer left the appearance to the system."""
    if _state["appearance"] != "system" or _state["applying"]:
        return
    before = _state["scheme"]
    apply(None, "system")
    if _state["scheme"] != before:
        retheme_windows()
