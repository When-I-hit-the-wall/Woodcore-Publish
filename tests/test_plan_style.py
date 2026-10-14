"""A position plan's entries, each drawn at a size of its own (v0.99, docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater).

The plan's three sliders are two levels since v0.99: the plan's own, and the factor one element or one axis states **over** them (`calc/domains/figure_style.py`). The file is written on the four rules that decision carries rather than on the arithmetic:

- **A plan on which nothing states a factor is drawn exactly as it was** -- byte for byte, `data/plans.json` unchanged -- which is the test that had to pass first and is held against a frozen SHA-256 taken before a line of it was written. That is what makes the whole lot additive: no `schema_version` moved, and no plan drawn before v0.99 needs migrating (the v0.69 rule for `group`).
- **A factor changes what that entry draws and nothing else.** Held by rendering the same plan twice and diffing the two drawings line by line, since an element's sizes reaching another element's symbol is the failure nobody would see on a page.
- **An entry may only state the factors it draws**: `point` on an axis is refused **naming what an axis may state**, an axis being a dash-dot line and the bubble its name is set in.
- **A factor the entry states is orange, with «Reprendre»**, and setting the slider back to 100 % does not take it off -- the b/h rule of v0.75, «typing the very value the position holds still writes it over».

⚠️ `number_frame` is the one function here that reads an element's factors **itself**: Woodcore's canvas hit-tests a click on a number with the plan's sizes and the export frames a detail round one with the plan's, so a scaling done anywhere but inside it would have been applied twice by one of the two -- a number's box 1.69 times its size, with nothing on the page saying so. `test_number_frame_grows_with_its_own_text_factor` and `test_the_scaling_is_never_applied_twice` are the two halves of that.
"""

import copy
import hashlib
import json
import os
import sys

import conftest
from conftest import ROOT
from domains import figure_style
from domains import plan
from domains import plan_svg

PLANS = ROOT / "tests" / "projet-exemple" / "Woodcore-Datei" / "plans"
TOOLS = ROOT / "calc" / "tools"

# The SVG of a plan carrying every kind of entry whose sizes the drawing reads, rendered **before** v0.99 touched
# plan_svg.py. A hash rather than a copy of the file: what is held is that not one byte moved, and a stored SVG
# would invite somebody to edit it into agreement.
# ⚠️ Taken again once, at v0.114, for one reason only: the opening's symbol was redrawn (a rectangle and a black wedge
# in its top right corner, plan_svg.opening_wedge, where it was a note with a folded corner) and `_rich` carries an
# opening. Its two <polygon> lines are the only lines of the drawing that moved -- checked by diffing the render of
# v0.113's plan_svg.py against this one's.
# ⚠️ Taken again at v0.117 for one reason: `_rich` states `show_lengths`, which now writes the length of a beam T and of
# each side of a slab D too (REQ-020) -- the render with `show_length: false` on its T and D hashes to 1d8725f0… exactly,
# checked first.
# ⚠️ Taken again for issue #9 for one reason: the lengths are drawn after every number, between `<!-- lengths -->`
# markers `show-plan(lengths: false)` takes out -- `_rich` states `show_lengths`. Checked by rendering it with the
# plan_svg.py of commit b462466: it gave d1bee5b5… (the hash before), and the two drawings hold the same lines, the
# new one adding the two markers and nothing else -- the length lines only moved.
FROZEN = "390c41a78bc905f084cbd853505557444075d15adc0c852ecf709e5fff1bfe44"

# Likewise for the example project's own four plans, one of them a 1.0 source (Pavillon).
FROZEN_EXAMPLE = {
    "Fluchttreppe.json": "38051bd9ccb1e17b4ad3788bf7931507ae5843265bc0ba61e110c37a181b8c45",
    "Geratehaus.json": "79a0700c18433dfd5859211ee94e976a7ddd3985025f0f31fb47fb52ac7498bf",
    "Pavillon.json": "4c35d494d4388cbce15cdd855f26975bb22ffb9498a68b1a3aae81b63f24020e",
    "Velo-Unterstand.json": "84266bbecd96aba48e7f78227849ff0bf7ecbf8defe2074808c2f53453420039",
}

SHEET = (1000.0, 700.0)


def _rich():
    """A plan carrying one of every kind of entry whose sizes the drawing reads: a dotted wall and a doubled one, a
    beam with its arrowheads and its number moved clear of it, a bracing member with its end dots, a column and an
    Abfangung placed on a point, a line Abfangung, a slab with its diagonals and its span arrow, a hatched concrete
    wall, an opening's folded corner, an Auflager with the square beside its number, the walls' lengths in metres,
    and two axes with their bubbles. Every branch of `_symbol`, in one source, so that «nothing moved» means it.
    """
    source = plan.new_source("Rich", floor="0")
    source["sheet"] = {"width": SHEET[0], "height": SHEET[1]}
    source["scale"] = {"mode": "calibration", "points": [[0.0, 0.0], [100.0, 0.0]], "length_m": 1.0}
    source["show_lengths"] = True
    source["style"] = {"line": 1.2, "point": 0.8, "text": 1.1}
    source["axes"] = [
        {"label": "A", "point": [120.0, 0.0], "angle": 90, "bubbles": "both"},
        {"label": "1", "point": [0.0, 120.0], "angle": 0, "bubbles": "start"},
    ]
    source["elements"] = [
        {"type": "V", "label": "V001", "points": [[120, 120], [520, 120]]},
        {"type": "W", "label": "W001", "points": [[120, 160], [520, 160]]},
        {"type": "T", "label": "T001", "points": [[120, 220], [520, 220]], "label_offset": [0, -70]},
        {"type": "A", "label": "A001", "points": [[560, 200], [700, 300]]},
        {"type": "S", "label": "S001", "points": [[620, 340]]},
        {"type": "L", "subtype": "punkt", "label": "L001", "points": [[760, 340]]},
        {"type": "L", "subtype": "linie", "label": "L002", "points": [[760, 380], [900, 380]]},
        {"type": "D", "subtype": "normal", "label": "D001",
         "points": [[140, 400], [520, 400], [520, 600], [140, 600]], "diagonal": 1},
        {"type": "B", "subtype": "wand", "label": "", "points": [[600, 440], [900, 440], [900, 540], [600, 540]]},
        {"type": "Ö", "label": "", "points": [[640, 60], [900, 60], [900, 200], [640, 200]]},
        {"type": "M", "subtype": "vh", "label": "M001", "points": [[140, 660], [520, 660]]},
        {"type": "H", "label": "H001", "points": [[560, 120], [560, 180]]},
    ]
    plan.check_source(source, "Rich.json")
    return source


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _at(source, index):
    return source["elements"][index]


# --- what must not have moved -------------------------------------------------------------

def test_a_plan_that_states_no_factor_is_drawn_byte_for_byte_as_it_was():
    """The invariant the whole version rests on. The frozen hash was taken from this very source before plan_svg.py
    was touched, so a difference of one decimal fails here -- and it is guaranteed rather than lucky: with nothing
    stated, `entry_sizes` gives back the plan's own `Sizes` **object**, not a copy of its three numbers.
    """
    source = _rich()
    assert _digest(plan_svg.render(source)) == FROZEN, "a plan stating no factor is no longer drawn as it was"
    sz = plan_svg.sizes_of(source)
    for element in source["elements"]:
        assert plan_svg.entry_sizes(sz, element) is sz, element.get("label") or element["type"]
    for axis in source["axes"]:
        assert plan_svg.entry_sizes(sz, axis) is sz, axis["label"]


def test_the_example_projects_plans_are_drawn_as_they_were():
    """The four plans the suite works on, one of them a 1.0 source: the same rule on files the engineer drew rather than on one written for a test."""
    for name, digest in FROZEN_EXAMPLE.items():
        source = json.loads((PLANS / name).read_text(encoding="utf-8"))
        assert _digest(plan_svg.render(source)) == digest, f"{name} is no longer drawn as it was"


def test_the_export_of_a_plan_that_states_no_factor_is_unchanged():
    """`data/plans.json` to the byte: no `style` on an element or an axis that states none, and `label_at` -- the one
    exported value a factor could move -- where it was.
    """
    record = plan.build_record(_rich(), SHEET)
    assert all("style" not in entry for entry in record["elements"]), "an element that states nothing carries a style"
    assert all("style" not in entry for entry in record["axes"]), "an axis that states nothing carries a style"
    # ⚠️ Taken again at v0.114, for two reasons and no other: the record gained `storey` and `role` (plans 1.3), and the
    # opening's legend swatch was redrawn with its symbol -- v0.113's record, with those two put back, hashes to
    # 6cde59fb… exactly, which was checked before the hash was changed.
    # ⚠️ Taken again at v0.116 for one reason: the record gained the plan's `name` (an export sheet heads a plan with it,
    # lib/sheet.typ's sheet-plan-title) -- the record with `name` popped hashes to 5e74341c… exactly, checked first.
    # ⚠️ Taken again at v0.117 for one reason: a legend line carries its `quantity` (the «métrés», REQ-020) -- the record
    # with every `quantity` popped hashes to a06f3b4b… exactly, checked first.
    assert _digest(json.dumps(record, sort_keys=True, ensure_ascii=False)) == \
        "56288d6e9481ad93d0ac983e87f299d09d914ad4606062028c371261380f4d0f", "the exported record moved"


# --- what a factor does, and to what --------------------------------------------------------

def _lines(source):
    return plan_svg.render(source).splitlines()


def test_a_factor_changes_what_its_own_entry_draws_and_nothing_else():
    """Line by line against the same plan without it: an element's own sizes reaching another element's symbol, or
    the axes, is the failure nobody would see on a finished page.
    """
    for index, key, factor in ((0, "line", 2.0), (4, "point", 2.0), (2, "text", 1.6), (7, "line", 0.5)):
        base = _rich()
        changed = copy.deepcopy(base)
        _at(changed, index)["style"] = {key: factor}
        plan.check_source(changed, "Rich.json")
        before, after = _lines(base), _lines(changed)
        assert before != after, f"element {index}: a {key} factor of {factor} drew the same SVG"
        assert len(before) == len(after), f"element {index}: the {key} factor changed how many shapes are drawn"
        moved = {i for i, (a, b) in enumerate(zip(before, after)) if a != b}
        # the element's own group, its leader, its number and its length are the only lines allowed to move
        own = {i for i in moved if _owned_by(before, i, index)}
        assert moved == own, f"element {index}: a {key} factor moved lines belonging to something else: {sorted(moved - own)}"


def _owned_by(lines, index, element):
    """Whether line `index` of a rendered plan belongs to element `element`: inside its `<g id="el-N">` group, or
    among the numbers, leaders and lengths that follow the groups -- which are drawn in the elements' own order, so a
    line after the last `</g>` is attributed by counting the numbers drawn before it.

    It is written as a rule about the drawing rather than as a list of line numbers, since the drawing's own order is
    what the rule is about: every element's symbol first, then every leader, then every number.
    """
    opened = None
    numbers = 0
    for i, line in enumerate(lines):
        if line.startswith('<g id="el-'):
            opened = int(line.split('"')[1].split("-")[1]) - 1
        elif line == "</g>":
            opened = None
        if i == index:
            return opened == element if opened is not None else True
        if opened is None and line.startswith("<text"):
            numbers += 1
    return True


def test_an_axis_takes_its_own_line_and_text_and_no_point():
    """An axis is a dash-dot line and the bubble its name is set in -- a radius that is already a text size -- and it
    places no symbol on a point, so `point` is refused **naming the two it may state** rather than only saying no.
    """
    assert figure_style.allowed("plan", "axes") == ("line", "text")
    base = _rich()
    for key in ("line", "text"):
        changed = copy.deepcopy(base)
        changed["axes"][0]["style"] = {key: 2.0}
        plan.check_source(changed, "Rich.json")
        assert plan_svg.render(changed) != plan_svg.render(base), f"an axis's {key} factor drew the same SVG"
    refused = copy.deepcopy(base)
    refused["axes"][0]["style"] = {"point": 2.0}
    message = _refusal(refused)
    assert "axis 1" in message and "style.point" in message and "line, text" in message, message


def test_an_element_takes_all_three():
    """Any of the eleven STE symbols is a line, or a symbol on a point, and every one of them carries its position
    number -- so an element may state all three, and an Abfangung placed on a point draws with all three at once: a
    white square at its `point` size, stroked and crossed at its `line` size, with its number at its `text` size.

    ⚠️ Not every element draws with every factor, and that is the point of the rule being the *collection's*: a
    column is a filled square with no stroke, so a `line` factor on one changes nothing on the page. `ENTRY_KEYS`
    says what an element may state, not what each one happens to use.
    """
    assert figure_style.allowed("plan", "elements") == ("line", "point", "text")
    base = _rich()
    for key in figure_style.KEYS:
        changed = copy.deepcopy(base)
        _at(changed, 5)["style"] = {key: 2.0}     # L001, an Abfangung on a point
        plan.check_source(changed, "Rich.json")
        assert plan_svg.render(changed) != plan_svg.render(base), f"an element's {key} factor drew the same SVG"


def _refusal(source):
    try:
        plan.check_source(source, "Rich.json")
    except Exception as exc:
        return str(exc)
    raise AssertionError("the source was accepted")


def test_a_factor_outside_the_range_is_refused_naming_it():
    """From a quarter to three times, on an entry as on the plan (figure_style.RANGE), and the entry named the way
    every other refusal of the module names one.

    ⚠️ A factor that is not a number at all is refused by the schema first, which names its path
    (`plan-source.elements[0].style.line`) rather than the entry: two readers, one field, and the earlier one wins --
    which is the arrangement `check_source` has always had (`validate_structure`, then the rules a schema cannot
    state). What matters is that it is refused and that the message names the field.
    """
    for value in (0.1, 3.5, -1):
        source = _rich()
        _at(source, 0)["style"] = {"line": value}
        message = _refusal(source)
        assert "element 1 (V): style.line" in message and "0.25" in message, message
    for value in ("1.2", None, [1.2]):
        source = _rich()
        _at(source, 0)["style"] = {"line": value}
        assert "style.line" in _refusal(source), value
    source = _rich()
    source["axes"][0]["style"] = {"text": 4.0}
    assert "axis 1: style.text" in _refusal(source)
    source = _rich()
    _at(source, 0)["style"] = {"lines": 1.2}       # a misspelt factor is one the engineer set and nothing draws
    assert "style.lines is not a factor" in _refusal(source)


def test_the_plans_own_three_are_still_checked_the_way_they_were():
    """The plan's `style` goes through the same reader now, and says the same thing: v0.99 must not have loosened it."""
    source = _rich()
    source["style"] = {"line": 5.0}
    assert "style.line is 5.0 -- from 0.25 to 3.0" in _refusal(source)


# --- the export ---------------------------------------------------------------------------

def test_the_export_carries_the_factors_an_entry_states_and_no_others():
    """The record says what the figure beside it was drawn with -- the convention every other placed value of this export follows -- and it says nothing where nothing was stated."""
    source = _rich()
    _at(source, 4)["style"] = {"point": 1.5, "text": 0.8}
    source["axes"][1]["style"] = {"line": 2.25}
    plan.check_source(source, "Rich.json")
    record = plan.build_record(source, SHEET)
    assert record["elements"][4]["style"] == {"point": 1.5, "text": 0.8}
    assert record["axes"][1]["style"] == {"line": 2.25}
    assert "style" not in record["elements"][0] and "style" not in record["axes"][0]
    assert record["style"] == {"line": 1.2, "point": 0.8, "text": 1.1}, "the plan's own three are still exported whole"


def test_the_export_validates_with_a_factor_on_an_entry():
    """Against schemas/plans.schema.json and validation's own rules, since the field is new in both."""
    import validation
    source = _rich()
    _at(source, 2)["style"] = {"text": 2.0}
    source["axes"][0]["style"] = {"line": 0.5}
    plan.check_source(source, "Rich.json")
    record = plan.build_record(source, SHEET)
    record["unknown"] = []
    data = {"schema_version": plan.EXPORT_SCHEMA_VERSION, "plans": {"Rich": record}}
    validation.validate_structure(data, "plans")
    validation.validate_plans_business(data)


# --- the number's box, which a click reads ------------------------------------------------

def test_number_frame_grows_with_its_own_text_factor():
    """A click on a position number, the leader back to its symbol and the export's `label_at` all read this one box
    (`plan_svg.number_frame`), and every one of them asks for it with the **plan's** sizes: so it applies the
    element's own factors itself, or a number drawn twice its size could not be clicked on where it is drawn.
    """
    base = _rich()
    plain = plan_svg.number_frame(_at(base, 2), plan_svg.sizes_of(base))
    changed = copy.deepcopy(base)
    _at(changed, 2)["style"] = {"text": 2.0}
    plan.check_source(changed, "Rich.json")
    grown = plan_svg.number_frame(_at(changed, 2), plan_svg.sizes_of(changed))
    assert abs(grown["hw"] / plain["hw"] - 2.0) < 1e-9, (plain["hw"], grown["hw"])
    assert abs(grown["hh"] / plain["hh"] - 2.0) < 1e-9, (plain["hh"], grown["hh"])
    # a click that lands on the grown box and would have missed the plain one
    corner = (grown["at"][0] + 1.5 * plain["hw"], grown["at"][1])
    assert plan_svg.on_number(grown, corner) and not plan_svg.on_number(plain, corner)
    # every number of every element, asked of the whole plan, carries its own element's factor
    frames = dict(plan_svg.number_frames(changed))
    assert abs(frames[2]["hw"] - grown["hw"]) < 1e-9 and abs(frames[0]["hw"] - plain["hw"]) < 1e-9


def _font_size(lines, body):
    """The `font-size` the drawing sets on the text whose body is `body` -- a position number, a wall's length."""
    for line in lines:
        if line.endswith(f">{body}</text>"):
            return float(line.split('font-size="')[1].split('"')[0])
    raise AssertionError(f"no text reads {body!r}")


def test_a_number_and_its_box_grow_together():
    """The box `number_frame` gives and the glyphs `_text` sets are one thing. An element's `text` factor reaching the
    box alone -- which is what happens the moment `render` hands `_number` the plan's sizes and lets `number_frame`
    do the scaling by itself -- draws a number rattling around in a box twice too big for it, and leaves a wall's
    length in metres at the plan's size altogether. Held on the `font-size` the drawing writes, the box being held
    above.
    """
    base = _rich()
    changed = copy.deepcopy(base)
    _at(changed, 11)["style"] = {"text": 2.0}       # H001, a bracing wall: its number and its length in metres
    plan.check_source(changed, "Rich.json")
    for body in ("H001", "0.60 m"):
        before, after = _font_size(_lines(base), body), _font_size(_lines(changed), body)
        assert abs(after / before - 2.0) < 1e-9, f"{body}: {before} -> {after}"


def test_a_number_grown_breaks_a_slabs_diagonals_over_its_own_box():
    """A slab's diagonals are cut behind its number wherever it is (v0.42), so its own `text` factor has to reach that cut as well as the number -- one drawing, one box."""
    base = _rich()
    changed = copy.deepcopy(base)
    _at(changed, 7)["style"] = {"text": 2.5}
    plan.check_source(changed, "Rich.json")
    before = [line for line in _lines(base) if line.startswith("<line")]
    after = [line for line in _lines(changed) if line.startswith("<line")]
    assert before != after, "the slab's diagonals were cut behind the number's old box"


def test_the_scaling_is_never_applied_twice():
    """`entry_sizes` is idempotent by construction (`Sizes.drawing`), and this is why it has to be: `number_frame` is
    asked with the plan's sizes by Woodcore's canvas and the export, and with the element's own by `_number`,
    `_leader` and `_slab` while they draw it. A factor applied twice would be a box 1.69 times its size, quietly.
    """
    source = _rich()
    element = _at(source, 2)
    element["style"] = {"text": 1.3}
    plan.check_source(source, "Rich.json")
    plan_sizes = plan_svg.sizes_of(source)
    own = plan_svg.entry_sizes(plan_sizes, element)
    assert abs(own.tf / plan_sizes.tf - 1.3) < 1e-12
    assert plan_svg.entry_sizes(own, element).tf == own.tf, "asked of its own sizes, the factor was applied again"
    assert plan_svg.number_frame(element, own)["hw"] == plan_svg.number_frame(element, plan_sizes)["hw"]
    # and asked of one entry's sizes for another, it answers that other's
    other = _at(source, 0)
    assert plan_svg.entry_sizes(own, other) is plan_sizes


def test_a_warning_about_a_number_out_of_the_frame_reads_its_own_factor():
    """`plan.warnings` frames a moved number with `number_frame` too: a number grown out of the crop is cut off in the report, and must be said so."""
    source = _rich()
    source["crop"] = {"x": 100.0, "y": 100.0, "w": 500.0, "h": 400.0}
    _at(source, 2)["label_offset"] = [0.0, -108.0]     # inside the frame at the plan's own text size, out of it at three times
    plan.check_source(source, "Rich.json")
    assert not [n for n in plan.warnings(source, ["T001"]) if "T001" in str(n) and "moved out" in str(n)]
    _at(source, 2)["style"] = {"text": 3.0}
    plan.check_source(source, "Rich.json")
    assert [n for n in plan.warnings(source, ["T001"]) if "T001" in str(n) and "moved out" in str(n)], \
        "a number grown out of the frame is not reported"


# --- the window --------------------------------------------------------------------------

_WINDOW = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _tab():
    """The plan tab of a window of this test's own, off-screen, on a copy of the example project."""
    if "tab" not in _WINDOW:
        conftest.exported("plans.json")
        app = _qt()
        from PySide6.QtCore import Qt
        import woodcore_gui
        window = woodcore_gui.MainWindow()
        window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        window.resize(1500, 850)
        window.show()
        tab = next(t for t in window.tabs if type(t).__name__ == "PlanTab")
        window.tab_widget.setCurrentWidget(tab)
        app.processEvents()
        _WINDOW.update(app=app, window=window, tab=tab)
    tab = _WINDOW["tab"]
    tab.dirty = False        # a modal off-screen never comes back (tests/test_connectors.py's own warning)
    return tab


def _select_element(tab):
    """The tab on the rich plan, its beam selected -- and not dirty, so a window closed on the way out asks nothing."""
    tab.replace_source(_rich())
    tab.canvas.select(("element", 2))
    _WINDOW["app"].processEvents()
    tab.dirty = False
    return tab.source["elements"][2]


def _rows(tab):
    return tab.entry_style.rows


def test_the_selections_card_offers_the_factors_that_entry_may_state():
    """One row per factor, those the collection allows shown and the others hidden altogether: a factor the entry does not draw is not a field it could be typed into."""
    from PySide6.QtWidgets import QGroupBox
    tab = _tab()
    _select_element(tab)
    card = next((b for b in tab.selection_group.findChildren(QGroupBox) if b.title() == tab.t("plan_style_own")), None)
    assert card is not None, "the selection carries no card of its own factors"
    assert card.property("card"), "it is not a card"
    assert all(_rows(tab)[key]["name"].isVisibleTo(card) for key in figure_style.KEYS), "an element may state all three"
    tab.canvas.select(("axis", 0))
    _WINDOW["app"].processEvents()
    assert not _rows(tab)["point"]["name"].isVisibleTo(tab.selection_group), "an axis offers a point factor"
    assert _rows(tab)["line"]["name"].isVisibleTo(tab.selection_group)


def test_a_slider_writes_the_factor_on_the_entry_as_one_step_of_undo():
    """The `edit` mechanic of every other change made through this form: one step back, and the plan marked unsaved."""
    tab = _tab()
    _select_element(tab)
    steps = len(tab.undo_stack)
    _rows(tab)["text"]["slider"].setValue(150)
    _WINDOW["app"].processEvents()
    assert tab.source["elements"][2]["style"] == {"text": 1.5}, tab.source["elements"][2].get("style")
    assert len(tab.undo_stack) == steps + 1, "the factor left no step of «Annuler»"
    assert tab.dirty, "the plan was not marked unsaved"
    tab.undo()
    _WINDOW["app"].processEvents()
    assert "style" not in tab.source["elements"][2], "«Annuler» did not take the factor off"


def test_a_factor_stated_is_orange_with_take_back_and_100_per_cent_does_not_take_it_off():
    """An overridden b/h's own form (v0.75): the row's name and its readout in `theme.colour("override")` with
    «Reprendre» beside them, and setting the slider back to 100 % is still writing the factor over -- typing the very
    value the plan holds is a decision, and «Reprendre» is the one way back.
    """
    tab = _tab()       # before `import theme`: it is calc/tools', which _qt() puts on the path
    import theme
    _select_element(tab)
    row = _rows(tab)["text"]
    assert not row["back"].isVisibleTo(tab.selection_group), "«Reprendre» is offered on a factor nobody stated"
    assert "color" not in row["name"].styleSheet()
    row["slider"].setValue(130)
    _WINDOW["app"].processEvents()
    orange = theme.colour("override")
    assert orange in _rows(tab)["text"]["name"].styleSheet(), _rows(tab)["text"]["name"].styleSheet()
    assert orange in _rows(tab)["text"]["readout"].styleSheet()
    assert _rows(tab)["text"]["back"].isVisibleTo(tab.selection_group), "«Reprendre» is not offered"
    _rows(tab)["text"]["slider"].setValue(100)
    _WINDOW["app"].processEvents()
    assert tab.source["elements"][2]["style"] == {"text": 1.0}, "100 % took the factor off rather than writing it over"
    _rows(tab)["text"]["back"].click()
    _WINDOW["app"].processEvents()
    assert "style" not in tab.source["elements"][2], "«Reprendre» left the factor on the element"
    assert not _rows(tab)["text"]["back"].isVisibleTo(tab.selection_group)


def test_taking_the_last_factor_back_leaves_the_entry_as_it_was_written_before():
    """The `style` goes with its last factor, so the source is byte for byte a pre-v0.99 one and its drawing does not move."""
    tab = _tab()
    _select_element(tab)
    before = plan_svg.render(tab.source)
    for key, percent in (("line", 200), ("text", 50)):
        _rows(tab)[key]["slider"].setValue(percent)
        _WINDOW["app"].processEvents()
    assert plan_svg.render(tab.source) != before
    for key in ("line", "text"):
        _rows(tab)[key]["back"].click()
        _WINDOW["app"].processEvents()
    assert "style" not in tab.source["elements"][2], tab.source["elements"][2].get("style")
    assert plan_svg.render(tab.source) == before, "the drawing did not come back"


def test_the_card_carries_its_words_in_the_three_languages():
    """Its title, its note and «Reprendre», each said once per language -- and «Reprendre» the word the connectors' tab and the schemas' already use for taking an override back (one word per notion)."""
    import woodcore_gui
    for lang in woodcore_gui.LANGUAGES:
        strings = woodcore_gui.STRINGS[lang]
        for key in ("plan_style_own", "plan_style_own_note", "plan_style_take_back"):
            assert strings[key].strip(), f"{lang}: {key} is empty"
        assert strings["plan_style_take_back"] == strings["cn_take_back"] == strings["sc_take_back"], lang
        assert "ß" not in strings["plan_style_own"] + strings["plan_style_own_note"], lang
