# -*- coding: utf-8 -*-
"""The three factors every figure Woodcore draws is set with -- the strokes, the symbols placed on a point, the texts -- and the factor one entry of a figure may state over them (v0.99, docs/domain/position-plans.md §3.3sexies, docs/domain/static-models.md §3.3octies, docs/domain/detail-schemas.md §3.3decies, docs/ui/window.md §10quater).

A slider means the same thing in every tab, which is why the three names, the range and the arithmetic are written here once and read by the plans, the static models, the detail schemas and the fire-protection plans alike:

- **`line`** scales what is drawn as a line: a stroke, a dash, an arrowhead, a witness line.
- **`point`** scales a symbol placed *on* a point: a column's square, a support's triangle, a hinge's circle, a fastener's marker.
- **`text`** scales what is written: a label, a number, a dimension's value, and so the box each of them is set in.

Two levels, and only two:

- **the drawing's own three**, which the tab shows as three sliders and the source carries in its `style` (`drawing_factors`);
- **an entry's own**, in that entry's `style`, which is a **factor multiplying the drawing's** and never a size (`entry_factors`, `product`). A size stated on an entry would be a length in a figure that has no length: a schema is a detail at its real size in millimetres and a static model a scale-free sketch normalised to 1000 figure units, so the same number would mean two different things in the two, and neither would survive the drawing being redrawn at another extent. A factor means the same in both, and an entry that states none simply follows its drawing.

⚠️ **An entry may only state the factors it is drawn with** (`ENTRY_KEYS`), and one it is not is refused **naming what it may state** (`check`): a bar draws no symbol on a point, so `point` on a bar would be a field nobody could see the effect of -- the kind of field that acquires a value nobody checks and a meaning nobody remembers (the argument that took `plates.thickness` out of a connector's source in v0.70). The table below is the whole of that decision, entry by entry, with what each entry actually draws:

| source | entry | `line` | `point` | `text` | what it draws |
|---|---|---|---|---|---|
| schema | `elements` | yes | -- | yes | a band or an outline, stroked, and its label |
| schema | `connectors` | -- | yes | yes | a filled dot at the marker's own radius, and its id beside it. Its white hairline and its halo are chrome that parts the dot from what lies under it, not a line the engineer drew |
| schema | `aids` | yes | yes | yes | a construction line (a stroke), or a centre's or a point's cross (a symbol on a point), and the aid's name |
| schema | `dimensions` | yes | -- | yes | witness lines, a dimension line, two heads, and its value |
| statics | `points` | -- | -- | yes | its label, and nothing else: **a node is never drawn in the report** (v0.56), so neither `line` nor `point` has anything to scale |
| statics | `members` | yes | -- | yes | its line, at its kind's own width, and its label. A spring's zigzag amplitude is the symbol's and follows the drawing's own `point` |
| statics | `supports` | yes | yes | yes | a triangle, its hatched wall, its rollers and its pin -- a symbol on a node, with strokes and a label |
| statics | `releases` | yes | yes | yes | a hinge's circle, a sleeve, a coil -- likewise |
| statics | `point_loads` | yes | -- | yes | an arrow and its label; its length is a `line` |
| statics | `line_loads` | yes | -- | yes | a band of arrows, its cap and its label |
| statics | `dimensions` | yes | -- | yes | as a schema's |
| plan | `elements` | yes | yes | yes | any of the eleven STE symbols: a wall is a line, a column and an Auflager are symbols on a point, and every one of them carries its position number |
| plan | `axes` | yes | -- | yes | a dash-dot line and the bubble its name is set in, which is sized from the text it holds |
| plan | `dimensions` | yes | -- | yes | a dimension's lines and ticks, and the value written beside it (issue #9) -- the static models' and the schemas' own rule |
| fire | `zones` | yes | -- | yes | a surface's outline and the hatching of one to be kept clear, and its name |
| fire | `walls` | yes | -- | -- | the band of its fire resistance, whose width is a `line`; it writes nothing |
| fire | `doors` | yes | -- | -- | the hairline round its shape, or the whole of a door without a fire resistance, which is drawn in outline. Its size is its two points' |
| fire | `routes` | yes | -- | yes | a thin arrow and its head, and the length written along it |
| fire | `widths` | -- | -- | yes | a figure, and nothing else |
| schema, statics, plan, fire | `texts` | -- | -- | yes | a text the engineer placed, and its variables (issue #43, `figure_text`): letters, and nothing else |

A fire-protection plan's emergency exits (`exits`) are in no row, and so state nothing: an exit is a filled arrow whose place, direction and size are its two points, which leaves no factor anything to scale.

⚠️ **`schema_version` does not move for any of it** (the v0.69 rule, docs/decisions.md §13): a field whose absence has a meaning -- here «follows the drawing» -- is additive, so no file needs migrating and a source written before v0.99 is read exactly as it was.

There is no Qt in this file: the export reads it, and so does the window, and neither has a copy of the arithmetic.
"""

KEYS = ("line", "point", "text")
# What the sliders may do: from a quarter to three times. The plans' own range since v0.34, and the same in all three for the reason the names are.
RANGE = (0.25, 3.0)
DEFAULT = 1.0

# Which of the three each kind of entry may state, by (the source's own word for itself, the collection). The table in the docstring says why, entry by entry.
ENTRY_KEYS = {
    ("schema", "elements"): ("line", "text"),
    ("schema", "connectors"): ("point", "text"),
    ("schema", "aids"): ("line", "point", "text"),
    ("schema", "dimensions"): ("line", "text"),
    ("statics", "points"): ("text",),
    ("statics", "members"): ("line", "text"),
    ("statics", "supports"): ("line", "point", "text"),
    ("statics", "releases"): ("line", "point", "text"),
    ("statics", "point_loads"): ("line", "text"),
    ("statics", "line_loads"): ("line", "text"),
    ("statics", "dimensions"): ("line", "text"),
    ("plan", "elements"): ("line", "point", "text"),
    ("plan", "axes"): ("line", "text"),
    ("plan", "dimensions"): ("line", "text"),
    ("fire", "zones"): ("line", "text"),
    ("fire", "walls"): ("line",),
    ("fire", "doors"): ("line",),
    ("fire", "routes"): ("line", "text"),
    ("fire", "widths"): ("text",),
    # a text placed with the Text tool (issue #43): letters and nothing else, in every engine
    ("schema", "texts"): ("text",),
    ("statics", "texts"): ("text",),
    ("plan", "texts"): ("text",),
    ("fire", "texts"): ("text",),
}


def allowed(kind, collection):
    """The factors an entry of `collection` in a `kind` of source may state -- () for one that is in no row of the table, which is how a collection nobody has decided about is refused rather than quietly accepting all three."""
    return ENTRY_KEYS.get((kind, collection), ())


def drawing_factors(source):
    """The drawing's own three, `DEFAULT` where it states none."""
    style = source.get("style") or {}
    return {key: float(style.get(key, DEFAULT)) for key in KEYS}


def stated(entry):
    """Only the factors `entry` actually states, as floats: what the window writes in orange, what «Reprendre» takes back, and what the export records as having been drawn with. An entry that states none gives {}, which is «follows the drawing»."""
    style = (entry or {}).get("style") or {}
    return {key: float(style[key]) for key in KEYS if key in style and style[key] is not None}


def entry_factors(entry):
    """All three of `entry`'s factors, `DEFAULT` where it states none -- what multiplies the drawing's."""
    own = stated(entry)
    return {key: own.get(key, DEFAULT) for key in KEYS}


def product(drawing, entry):
    """The factors one entry is drawn with: the drawing's own times its own."""
    own = stated(entry)
    return {key: drawing[key] * own.get(key, DEFAULT) for key in KEYS}


def record(entry):
    """What an export carries of an entry's own factors: the ones it states, or nothing at all. A record then says what the figure was drawn with, which is the convention every other placed value here follows."""
    own = stated(entry)
    return {key: round(value, 4) + 0.0 for key, value in own.items()} or None


def check(style, fail, may=KEYS, what="style"):
    """`style` as a source states it, refused by `fail(message)` where it is not a set of factors this entry may carry.

    `fail` is the caller's own refusal -- `plan._fail`, `statics._fail`, `schema._fail` -- so the message names the file and the entry the way every other refusal of that module does, and this function knows nothing about where the entry came from.

    ⚠️ A factor the entry is not drawn with is refused **naming the ones it may state**, so the message says what to write instead of only that something is wrong; and an entry drawn with none of the three says so.
    """
    if style is None:
        return
    if not isinstance(style, dict):
        fail(f"{what} must be an object, got {style!r}")
        return
    for key, value in style.items():
        if key not in KEYS:
            fail(f"{what}.{key} is not a factor -- {', '.join(KEYS)}")
            continue
        if key not in may:
            fail(f"{what}.{key} means nothing here -- "
                 + (f"this entry is drawn with {', '.join(may)}" if may else "this entry states no factor of its own"))
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            fail(f"{what}.{key} must be a number, got {value!r}")
            continue
        if not RANGE[0] <= float(value) <= RANGE[1]:
            fail(f"{what}.{key} is {value} -- from {RANGE[0]} to {RANGE[1]}")
