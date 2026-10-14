# Figure style factors

> The three factors a figure is drawn with, and an entry's own over them.
>
> Moved verbatim from CLAUDE.md (§3.3quaterdecies) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

### 3.3quaterdecies The three factors a figure is drawn with, and an entry's own over them (v0.99)

A plan and a static model have carried **three factors** since v0.34 and v0.51 — `line` on the strokes, `point` on the symbols placed on a point, `text` on the texts, each from 0.25 to 3 — and a detail schema carried none. The engineer asked for one thing of all three: **a slider means the same thing in every tab, and a single entry may be drawn heavier or lighter than the drawing it is in.** `calc/domains/figure_style.py` is what the factors *are* — the three names, the range, the arithmetic, and **which of them each kind of entry may state** — read by the three domains and by the three `*_svg.py` alike, so none of them keeps a copy; `calc/tools/stylefactors.py` is how they are typed, and the three tabs build their rows from it as they already build their identity rows from `identity.py`.

⚠️ **An entry states a factor multiplying the drawing's, never a size.** A schema is a detail at its real size in millimetres and a static model a scale-free sketch normalised to 1000 figure units, so one number stated on an entry would mean two different things in the two, and neither would survive the drawing being redrawn at another extent. A factor means the same in both, and an entry that states none simply follows its drawing — which is what makes the field additive and what left every `schema_version` where it was (the v0.69 rule, §13).

⚠️ **An entry may state only the factors it is drawn with**, and one it is not is refused **naming the ones it may state** (`figure_style.ENTRY_KEYS`, `figure_style.check`). A bar draws no symbol on a node, so `point` on a bar would be a field nobody could see the effect of — the kind of field that acquires a value nobody checks and a meaning nobody remembers, which is the argument that took `plates.thickness` out of a connector's source in v0.70. The table, entry by entry, with what each entry draws:

| source | entry | `line` | `point` | `text` | what it draws |
|---|---|---|---|---|---|
| schema | `elements` | yes | — | yes | a band or an outline, stroked, and its label |
| schema | `connectors` | — | yes | yes | a dot at the marker's own radius and its id beside it. ⚠️ A **diameter it states is a length in millimetres and is never scaled**: a Ø 8 dowel is 8 mm across whatever the sliders say, `point` moving the radius of a marker that states none and the floor under a very small one. `line` is refused, the dot's white hairline being what parts it from what lies under it rather than a line the engineer drew |
| schema | `aids` | yes | yes | yes | a construction line, or a centre's or a named point's cross, and the aid's name |
| schema | `dimensions` | yes | — | yes | witness lines, a dimension line, two heads, and the value written over it |
| statics | `points` | — | — | yes | its label, and nothing else: **a node is never drawn in the report** (v0.56) |
| statics | `members` | yes | — | yes | its line at its kind's own width, and its label |
| statics | `supports` · `releases` | yes | yes | yes | a symbol on a node, with strokes and a label |
| statics | `point_loads` · `line_loads` | yes | — | yes | an arrow or a band of arrows, and its label; a point load's **length** is a `line` |
| statics | `dimensions` | yes | — | yes | as a schema's |
| plan | `elements` | yes | yes | yes | any of the eleven STE symbols: a wall is a line, a column and an Auflager are symbols on a point, and every one carries its position number |
| plan | `axes` | yes | — | yes | a dash-dot line and the bubble its name is set in, which is sized from the text it holds |
| plan | `dimensions` | yes | — | yes | a dimension's lines and ticks, and the value written beside it (issue #9) — the static models' and the schemas' own rule |

**Both renderers honour them, because they are the one SVG**: each `*_svg.py` works the pair of factors out once per entry (`entry_sizes`) and hands it down as that entry's own sizes, so the symbol, the room its own box takes in the frame, its label and the halo the report may put under it all come out at one size — in Woodcore's canvas and in the exported figure alike.

**The export says what the figure was drawn with**: the drawing's own three on the record, and each entry's own beside its placed geometry where it states any (`figure_style.record`). Nothing in the report reads it; what it is for is that one export can be read against another when a slider has moved, which is the convention every other placed value here follows.

⚠️ **What stays the drawing's, and why.** Three things are deliberately not an entry's, each written down where it happens: a static model's **break at a node** (`statics_svg._release_cuts`) — both member ends meeting there are drawn back by the same amount, which is v0.55's own repair, and a break taken from each member's own factor would be wider on one side of one node than on the other; a **spring's zigzag amplitude**, which is the symbol's size and follows the drawing's `point`, a member stating none; and a schema's **arc radius of an angle dimension**, which is the offset the third click wrote, in millimetres, and no size at all.
