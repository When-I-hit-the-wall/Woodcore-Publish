"""The text of every figure Woodcore draws: one table of Arial's advances, one way of cutting a label into its subscripts, one measure and one way of setting it (spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, D-19, ARCH-006).

The static models' own, moved here unchanged (statics_svg_layout and statics_svg import every name back), and since issue #43 the detail schemas' too: until then `schema_svg` carried a table of its own, which it called a copy of this one and was not -- «m» was 0.7222 em there and 0.833 here, and a subscript was placed differently --, so a word was measured one way on a schema and another on a static model. The engineer chose one engine, the schemas' labels moving slightly with it (D-19). The text object of the four drawing engines is set with it as well (calc/domains/figure_text.py).

Kept to what QtSvg (SVG Tiny 1.2) and resvg read alike: a subscript is a second `<text>` set smaller and lower, Tiny having neither baseline-shift nor a <tspan> both renderers read alike; `font-family` names one bare family. No Qt.
"""

from domains import svg_draw  # the one writer of an SVG number and text (D6)
import re
from xml.sax.saxutils import escape

# One family, not a list: QtSvg takes the whole font-family string as a single name (statics_svg.py's own finding, v0.87).
FONT = svg_draw.FONT

# Arial's own advance for each character, as a fraction of the font size, measured once from the font and grouped by width. It is `FONT`'s first family, and the metric-compatible substitute a machine without it falls back to (Liberation Sans) has the same advances -- so QtSvg in Woodcore and resvg in the report set these texts alike. A character not listed takes ARIAL_DEFAULT, the width of a digit and of most lowercase letters.
#
# French's accented letters are in here for the reason German's are: the notes under the drawing are set in the report's language (docs/typst/language.md §4bis), and a width taken from the default would size the frame around them wrongly. Arial keeps a letter's advance under its accents -- except the lowercase i, whose accented forms are as wide as a capital I.
_ARIAL_GROUPS = {
    0.1909: "'‘’",
    0.2222: 'ijl',
    0.2598: '|',
    0.2778: ' !,./:;I[\\]ftíìîïÎÏ',
    0.333: '()-`r²³·',
    0.334: '{}',
    0.355: '"',
    0.3892: '*',
    0.3999: '°',
    0.4692: '^',
    0.5: 'Jcksvxyzγç',
    0.5562: '#$0123456789?L_abdeghnopquäöü–àáâãåèéêëñòóôõùúû«»',
    0.5752: 'β',
    0.5762: 'μ',
    0.5781: 'α',
    0.584: '+<=>~×−',
    0.6108: 'FTZß',
    0.667: '&ABEKPSVXYÄÀÁÂÃÅÈÉÊË',
    0.7222: 'CDHNRUwÜÇÙÚÛ',
    0.7778: 'GOQÖØÒÓÔÕ',
    0.833: 'Mm',
    0.8892: '%',
    0.9438: 'W',
    1.0: '—…œ',
    1.0151: '@',
}


ARIAL_WIDTHS = {ch: width for width, chars in _ARIAL_GROUPS.items() for ch in chars}


ARIAL_DEFAULT = 0.5562


# What follows an underscore is a subscript: b_e is b with a small e under the line, q_k is q with a k, and a braced or bracketed group carries one of several characters (q_(k,11)).
SUBSCRIPT = re.compile(r"_(\{[^}]*\}|\([^)]*\)|[A-Za-z0-9]+)")


SUB_SCALE = 0.72


# How far below the line a subscript sits, as a share of the size.
SUB_DROP = 0.22


# A `*` the engineer types into a label is drawn as the multiplication dot a printed formula carries (v0.87). U+00B7, which Arial carries (682/2048, the 0.333 group above), and not the dot operator U+22C5, which it does not.
TYPED_TIMES = "*"


TIMES = "·"


def text_runs(text):
    """A label split into the pieces it is set in: `b_e` is [("b", False), ("e", True)], `q_(k,11)` is [("q", False), ("k,11", True)]. A typed `*` comes out as the dot it is drawn with (TIMES)."""
    text = text.replace(TYPED_TIMES, TIMES)
    runs, i = [], 0
    for m in SUBSCRIPT.finditer(text):
        if m.start() > i:
            runs.append((text[i:m.start()], False))
        body = m.group(1)
        if body[:1] in "{(":
            body = body[1:-1]
        if body:
            runs.append((body, True))
        i = m.end()
    if i < len(text):
        runs.append((text[i:], False))
    return runs or [("", False)]


def advance(text, size):
    """How far a run of text carries the pen, by Arial's own advances. It has to be right rather than close: a subscript is a `<text>` of its own, placed where the run before it ends, so every character's error accumulates into the gap before it."""
    return size * sum(ARIAL_WIDTHS.get(ch, ARIAL_DEFAULT) for ch in text)


def text_width(text, size):
    """How wide a label is set, subscripts counted small -- what a label's box and the figure's frame are sized by."""
    return sum(advance(chunk, size * (SUB_SCALE if sub else 1.0)) for chunk, sub in text_runs(text))


_f = svg_draw.number_at(3)   # a coordinate at 3 decimals (svg_draw.py, D6)


def draw(out, point, content, size, colour, anchor="middle", bold=False, rotate=None, halo=None, halo_colour=svg_draw.colour("ground"), raw=False):
    """A text, its subscripts set smaller and lower, centred on `point` vertically as well -- SVG Tiny has no dominant-baseline, so it is lowered by a third of its size, and no baseline-shift, so a subscript is a <text> of its own. `rotate` turns it about `point`, in degrees; `halo` draws it first in `halo_colour`, `halo` wide, so it reads over whatever is behind it; `raw` sets it as it is written, no subscript cut."""
    weight = ' font-weight="bold"' if bold else ""
    x, y = point
    runs = [(content, False)] if raw else text_runs(content)
    width = sum(advance(chunk, size * (SUB_SCALE if sub else 1.0)) for chunk, sub in runs)
    start = {"middle": -width / 2.0, "end": -width, "start": 0.0}[anchor]
    transform = f' transform="translate({_f(x)},{_f(y)}) rotate({_f(rotate)})"' if rotate else ""
    ox, oy = (0.0, 0.35 * size) if rotate else (x, y + 0.35 * size)
    cursor = start
    pieces = []
    for chunk, sub in runs:
        if not chunk:
            continue
        chunk_size = size * SUB_SCALE if sub else size
        drop = SUB_DROP * size if sub else 0.0
        # a <text> drops the spaces at its own ends, so a run's leading space is measured rather than written: without this, `q_k = 3.458 kN/m` comes out as `q_k= 3.458 kN/m`
        lead = chunk[: len(chunk) - len(chunk.lstrip())]
        body = chunk.strip()
        if body:
            pieces.append((cursor + advance(lead, chunk_size), drop, body, chunk_size))
        cursor += advance(chunk, chunk_size)
    for shaded in ((True, False) if halo else (False,)):
        for offset, drop, chunk, chunk_size in pieces:
            common = (
                f'x="{_f(ox + offset)}" y="{_f(oy + drop)}" font-family="{FONT}" '
                f'font-size="{_f(chunk_size)}" text-anchor="start"{weight}{transform}'
            )
            if shaded:
                out.append(
                    f'<text {common} fill="{halo_colour}" stroke="{halo_colour}" stroke-width="{_f(halo)}" '
                    f'stroke-linejoin="round">{escape(chunk)}</text>'
                )
            else:
                out.append(f'<text {common} fill="{colour}">{escape(chunk)}</text>')


def plain(out, x, y, content, size, colour, number, anchor="middle", extra=""):
    """A text written as it is -- no subscript cut, set on its baseline, its anchor an attribute -- as the connectors', the dead loads' and the snow's drawings write theirs: the one writer of the three, each handing its own number format (`number`, its precision) and what it adds after the anchor (`extra`: a weight, a turn) (spec 2026-10-20-indices-et-niveaux, ARCH-004). Their bytes are those they wrote; the snow's text is escaped now, as the other two always were."""
    out.append('<text x="%s" y="%s" font-family="%s" font-size="%s" fill="%s" text-anchor="%s"%s>%s</text>'
               % (number(x), number(y), FONT, number(size), colour, anchor, extra, svg_draw.escape(content)))
