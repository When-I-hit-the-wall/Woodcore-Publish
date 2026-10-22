"""How every drawing engine writes SVG: a number of a coordinate, a text escaped, a colour of the figures' palette (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, D5 and D6).

Nine modules wrote their own `_f` -- six bodies for one idea, at three precisions -- and two their own `_escape`. Written once here; a drawing keeps the precision it always had (`_f = svg_draw.number_at(2)`), since a coordinate is not a number shown to the engineer (the display's rule, UI-003, is not its) and a figure that moved by a digit would be a figure changed (tests/test_figure_golden.py). `svg_text.py` stays what measures and sets a text.

The colours and the font are lib/figure-palette.json's, which the report's own drawings read too: an engine names a colour by its token (`colour("ink")`) and writes none of its own.
"""

import json
from pathlib import Path

import number_text

# lib/figure-palette.json: one file for the drawing engines and the report (D5, Q-015)
PALETTE_FILE = Path(__file__).resolve().parent.parent.parent / "lib" / "figure-palette.json"
_PALETTE = json.loads(PALETTE_FILE.read_text(encoding="utf-8"))
# One family, not a list: QtSvg takes the whole font-family string as a single name, so a list matched nothing and Woodcore set the numbers in a fallback face (statics_svg.py's own finding, v0.87).
FONT = _PALETTE["font-family"]


def colour(token):
    """The colour the palette names `token` («ink», «ground», «orange»…), as `#rrggbb`; a token it does not hold is a KeyError naming it."""
    return _PALETTE["colours"][token]


def colours(name):
    """A rotation of the palette (`wood`, `layers`): distinct colours a figure takes one after the other."""
    return tuple(_PALETTE["lists"][name])


def number(value, digits):
    """`value` with at most `digits` decimals, its trailing zeros and point taken off, never «-0»: 1.250 → «1.25», -0.0004 → «0» -- calc/number_text.py's `trimmed`, the one copy (UI-003)."""
    return number_text.trimmed(value, digits)


def number_at(digits):
    """The writer of a number at `digits` decimals, which a drawing names `_f`."""
    def _f(value):
        return number(value, digits)
    return _f


def escape(text):
    """A text set in SVG: `&`, `<`, `>` and the quote escaped, so that it stands as well in an element as in an attribute."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
