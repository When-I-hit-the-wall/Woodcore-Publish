"""A static model's source as the export reads it (docs/domain/static-models.md §3.3octies): what it refuses, and what it only says.

Written for the periodic audit of 16.09.2026, whose finding AUD-7-424 was a decision the code contradicted: a release carrying a translational stiffness «keeps its degree of freedom and loses the stiffness» (section 13, v0.51), and the export refused it instead -- one such file stopped every model's export.
"""

import json
import re

from conftest import tmpdir


def _model(releases):
    from domains import statics
    source = statics.new_source("S97")
    source.update(
        points=[{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 3, "z": 0}],
        members=[{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}],
        supports=[{"id": "A1", "point": "P1", "type": "pinned"}, {"id": "A2", "point": "P2", "type": "roller"}],
        releases=releases,
    )
    return source


def test_a_translational_stiffness_on_a_release_is_dropped_with_a_warning():
    from domains import statics
    folder = tmpdir("statics_release")
    source = _model([{"id": "G9", "member": "B1", "end": "end", "dof": "shear", "stiffness": {"value": 500, "unit": "kN/m"}}])
    (folder / "S97.json").write_text(json.dumps(source), encoding="utf-8")
    data, _files, notes = statics.prepare(folder)
    release = data["models"]["S97"]["releases"][0] if "releases" in data["models"]["S97"] else None
    assert any("G9" in note and "stiffness" in note for note in notes), notes
    assert release is None or "stiffness" not in release, release


def test_a_moment_release_keeps_its_stiffness():
    from domains import statics
    folder = tmpdir("statics_release_moment")
    source = _model([{"id": "G1", "member": "B1", "end": "end", "dof": "moment", "stiffness": {"value": 800, "unit": "kNm/rad"}}])
    (folder / "S97.json").write_text(json.dumps(source), encoding="utf-8")
    _data, _files, notes = statics.prepare(folder)
    assert not any("G1" in note and "stiffness" in note for note in notes), notes


# --- a load's colour, a dimension's `show`, a negative number on a figure -----------------------------------
# The engineer's three requests for the figure: «il doit être possible de changer la couleur des charges (couleurs au choix: rouge actuel, vert, orange, bleu, violet)», «pour les cotations, de manière similaire aux charges, il faut pouvoir choisir entre afficher la valeur, le nom, les deux, ou rien», and a negative number set with the real minus sign.


def _loaded(**load):
    source = _model([])
    source["point_loads"] = [{"id": "F1", "point": "P1", "direction": "vertical", "label": "F", "show": "name+value",
                              "magnitude": {"value": 2.0, "unit": "kN"}, **load}]
    return source


def _figure(source):
    from domains import statics_svg
    return statics_svg.render(statics_svg.layout(source, {}, "de"))


def _texts(svg):
    """What the figure writes, its <text> elements' content only -- never a coordinate."""
    return re.findall(r"<text [^>]*>([^<]*)</text>", svg)


def test_a_load_is_drawn_in_the_colour_it_states_and_red_is_what_it_always_was():
    from domains import statics, statics_svg
    assert list(statics.LOAD_COLOURS) == ["red", "green", "orange", "blue", "violet"], statics.LOAD_COLOURS
    # the red every load was drawn in before the colour could be chosen, so a model saved then draws exactly as it did
    assert statics.LOAD_COLOURS[statics.DEFAULT_LOAD_COLOUR] == "#c0392b"
    plain = _figure(_loaded())
    assert plain == _figure(_loaded(color="red")), "a load stating red is drawn otherwise than one stating nothing"
    for name, ink in statics.LOAD_COLOURS.items():
        svg = _figure(_loaded(color=name))
        assert f'fill="{ink}"' in svg and f'stroke="{ink}"' in svg, f"{name}: the arrow is not drawn in {ink}"
        others = [other for other in statics.LOAD_COLOURS.values() if other != ink]
        assert not any(other in svg for other in others), f"{name}: another load colour is in the figure"
        # the label stays in the drawing's own ink, on its white box, whatever colour the arrows are
        assert f'fill="{statics_svg.LABEL}">F' in svg, f"{name}: the label left the drawing's own ink"
        record = statics.build_record(_loaded(color=name), {})
        assert record["loads"][0]["color"] == name, record["loads"][0]
    assert statics.build_record(_loaded(), {})["loads"][0]["color"] == "red"


def test_a_colour_the_list_does_not_have_is_refused_naming_the_five():
    from domains import statics
    try:
        statics.check_source(_loaded(color="pink"), "S97.json")
    except statics.validation.ValidationError as exc:
        message = str(exc)
    else:
        raise AssertionError("a load in pink passed the check")
    assert "pink" in message and all(name in message for name in statics.LOAD_COLOURS), message


def _dimensioned(**dim):
    source = _model([])
    source["dimensions"] = [{"id": "D1", "kind": "horizontal", "from": {"point": "P1"}, "to": {"point": "P2"}, "offset": 1.0, **dim}]
    return source


def test_a_dimension_writes_what_its_show_asks_for():
    """Nothing, its name, what it measured, or `name = value` -- a load's own four, with a load's own rule where the name is missing: `name` writes nothing, `name+value` the value alone."""
    from domains import statics
    cases = [
        ({"show": "value", "label": "l"}, "3 m"),
        ({"show": "name", "label": "l"}, "l"),
        ({"show": "name+value", "label": "l"}, "l = 3 m"),
        ({"show": "none", "label": "l"}, ""),
        ({"show": "name"}, ""),
        ({"show": "name+value"}, "3 m"),
        # saved before `show` existed: a label took the value's place, and without one the value was written
        ({"label": "l"}, "l"),
        ({}, "3 m"),
    ]
    for fields, want in cases:
        source = _dimensioned(**fields)
        statics.check_source(source, "S97.json")
        dim = source["dimensions"][0]
        assert statics.dimension_text(source, dim) == want, (fields, statics.dimension_text(source, dim))
        record = statics.build_record(source, {})["dimensions"][0]
        assert record["text"] == want and record["show"] == statics.dimension_show(dim), (fields, record)
        # what was measured stays measured, whatever the figure writes: the window's «valeur» column
        assert statics.dimension_value_text(source, dim) == "3 m"
        texts = _texts(_figure(source))
        assert (want in texts or not want) and any("3 m" in t for t in texts) == ("3 m" in want), (fields, texts)


def test_a_dimension_that_writes_nothing_has_no_label_to_hit():
    from domains import statics_svg
    source = _dimensioned(show="none", label="l")
    frames = statics_svg.label_frames(source, {})
    assert not [f for f in frames if f[0] == "dimensions"], frames
    # its line is still drawn, and still marked for `dimensions: false`
    svg = _figure(source)
    assert svg.count(statics_svg.DIMS_OPEN) == 2 and "<line" in svg.split(statics_svg.DIMS_OPEN)[1]


def test_a_show_the_list_does_not_have_is_refused():
    from domains import statics
    try:
        statics.check_source(_dimensioned(show="both"), "S97.json")
    except statics.validation.ValidationError as exc:
        assert "both" in str(exc) and "name+value" in str(exc), str(exc)
    else:
        raise AssertionError("a dimension showing 'both' passed the check")


def test_a_negative_number_is_drawn_with_the_minus_sign_and_never_a_hyphen():
    """A hyphen is a letter's stroke and reads as a dash beside a number; the figure sets U+2212, as the report's math does. A coordinate keeps its hyphen -- it is read by the renderer, not by an engineer."""
    from domains import statics
    source = _loaded(magnitude={"value": -2.5, "unit": "kN"})
    source["line_loads"] = [{"id": "q1", "member": "B1", "shape": "linear", "direction": "vertical", "label": "q", "show": "name+value",
                             "magnitude": {"value": -1.5, "unit": "kN/m"}, "magnitude_end": {"value": 3.0, "unit": "kN/m"}}]
    texts = _texts(_figure(source))
    assert any("\u22122.5" in t for t in texts), texts
    assert any("\u22121.5" in t for t in texts), texts
    assert not any(re.search(r"(^|[\s=(])-\d", t) for t in texts), texts
    record = statics.build_record(source, {})
    assert "\u22122.5" in record["loads"][0]["text"], record["loads"][0]
    # a value the engineer types back into a list keeps the hyphen a program reads
    assert statics.fmt_number(-2.5) == "-2.5" and statics.figure_number(-2.5) == "\u22122.5" and statics.figure_number(0) == "0"


def test_the_minus_sign_is_measured_at_arial_s_own_advance():
    """1196 units of Arial's 2048 (its `minus` glyph, the width of its plus and its equals), in both figures' tables: a width taken from the default would size a label's box for a character a hyphen's width narrower."""
    from domains import schema_svg, statics_svg
    advance = 1196 / 2048
    for module in (statics_svg, schema_svg):
        assert abs(module.ARIAL_WIDTHS["\u2212"] - advance) < 1e-3, (module.__name__, module.ARIAL_WIDTHS.get("\u2212"))


# --- the same choices in the window's «Modèles statiques» tab -------------------------------------------------


def _statics_tab(source=None):
    """The static models' tab, off-screen, on a model carrying one load of each kind and a dimension -- or on `source`, where a test brings its own."""
    import os
    import sys
    from conftest import ROOT, Skip
    path = str(ROOT / "calc" / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    import woodcore_gui
    window = woodcore_gui.MainWindow()
    window.show()
    tab = next(t for t in window.tabs if type(t).__name__ == "StaticsTab")
    tab.window_ref = window
    if source is None:
        source = _dimensioned(label="l")
        source["point_loads"] = _loaded()["point_loads"]
        source["line_loads"] = [{"id": "q1", "member": "B1", "shape": "uniform", "direction": "vertical", "label": "q",
                                 "show": "name+value", "magnitude": {"value": 1.5, "unit": "kN/m"}}]
    tab.open_source(source, None, False)
    return tab


def _column(tab, collection, title):
    return next(i for i, c in enumerate(tab.table_specs[collection]["columns"]) if c["title"] == title)


def test_a_load_s_colour_is_chosen_in_its_list_and_in_its_panel():
    from PySide6.QtWidgets import QComboBox
    tab = _statics_tab()
    try:
        for collection in ("point_loads", "line_loads"):
            table = tab.table_widgets[collection]
            combo = table.cellWidget(0, _column(tab, collection, "st_col_colour"))
            assert [combo.itemData(i) for i in range(combo.count())] == ["red", "green", "orange", "blue", "violet"]
            assert combo.currentData() == "red" and combo.currentText() == tab.t("st_colour_red")
            steps = len(tab.undo_stack)
            combo.setCurrentIndex(combo.findData("green"))
            assert tab.source[collection][0]["color"] == "green", tab.source[collection][0]
            assert len(tab.undo_stack) == steps + 1, "a colour chosen is one step of «Annuler»"
            # red is stated by stating nothing, so a model left red is saved as it was
            combo = table.cellWidget(0, _column(tab, collection, "st_col_colour"))
            combo.setCurrentIndex(combo.findData("red"))
            assert "color" not in tab.source[collection][0], tab.source[collection][0]
        # the panel carries the same choice
        tab.canvas.select(("line_loads", "q1"))
        panel = [c for c in tab.selection_group.findChildren(QComboBox) if c.count() == 5 and c.itemData(0) == "red"]
        assert len(panel) == 1, "the load's panel carries one colour combo"
        panel[0].setCurrentIndex(panel[0].findData("violet"))
        assert tab.source["line_loads"][0]["color"] == "violet"
        tab.undo()
        assert "color" not in tab.source["line_loads"][0]
    finally:
        tab.dirty = False


def test_a_dimension_s_show_is_chosen_in_its_list_and_its_value_is_still_listed():
    from PySide6.QtWidgets import QComboBox
    tab = _statics_tab()
    try:
        table = tab.table_widgets["dimensions"]
        combo = table.cellWidget(0, _column(tab, "dimensions", "st_col_show"))
        # saved with a label and no `show`, it reads as it was drawn then: the name
        assert combo.currentData() == "name", combo.currentData()
        combo.setCurrentIndex(combo.findData("none"))
        assert tab.source["dimensions"][0]["show"] == "none"
        value = table.item(0, _column(tab, "dimensions", "st_col_dim_value")).text()
        assert value == "3 m", f"the list says what was measured whatever the figure writes, not {value!r}"
        tab.canvas.select(("dimensions", "D1"))
        panel = [c for c in tab.selection_group.findChildren(QComboBox) if c.count() == 4 and c.itemData(0) == "none"]
        assert len(panel) == 1 and panel[0].currentData() == "none", "the dimension's panel carries the same choice"
        panel[0].setCurrentIndex(panel[0].findData("name+value"))
        assert tab.source["dimensions"][0]["show"] == "name+value"
    finally:
        tab.dirty = False


# --- a typed `*` is drawn as a multiplication dot (v0.87) -------------------------------------------------------
# The engineer: «un * tapé dans l'étiquette d'une charge d'un modèle statique s'imprime tel quel».


def test_a_typed_star_is_drawn_as_a_multiplication_dot_and_kept_in_the_source():
    """In a load's label, its description, its b_e's name and a dimension's name -- every text of the figure goes through text_runs, so the dot is drawn and measured alike, and what was typed stays in the source."""
    import copy
    from domains import schema_svg, statics, statics_svg
    source = _model([])
    source["line_loads"] = [{"id": "q1", "member": "B1", "shape": "uniform", "direction": "vertical",
                             "label": "Q_(1,Ed) = 1.35*G_(1,k) + 1.5*Q_(1,k)", "show": "name+value",
                             "magnitude": {"domain": "snow-load", "instance": "SL", "var": "q_k", "factor": 1.35, "description": "1.35*g_k"},
                             "width": {"value": 2.5, "unit": "m", "label": "b*_e", "description": "Achse 2*3"}}]
    source["dimensions"] = [{"id": "D1", "kind": "horizontal", "from": {"point": "P1"}, "to": {"point": "P2"}, "offset": 1.0,
                             "show": "name+value", "label": "2*l"}]
    values = {"snow-load": {"SL": {"q_k": {"value": 1.2, "unit": "kN/m²", "symbol": "q_k"}}}}
    typed = copy.deepcopy(source)
    statics.check_source(source, "S97.json")
    texts = _texts(statics_svg.render(statics_svg.layout(source, values, "de")))
    assert not any("*" in t for t in texts), texts
    written = " ".join(texts)
    for piece in ("1.35·G", "1.5·Q", "1.35·g", "b·", "Achse 2·3", "2·l = 3 m"):
        assert piece in written, (piece, texts)
    assert source == typed, "the source lost what was typed"
    # measured at the dot's own advance, Arial's 682/2048, so a label's box fits what it shows
    size = 10.0
    for module in (statics_svg, schema_svg):
        assert module.text_runs("a*b") == [("a·b", False)], module.__name__
        assert abs(module.ARIAL_WIDTHS["·"] - 682 / 2048) < 1e-3, module.__name__
        assert abs(module.text_width("a*b", size) - module.text_width("a·b", size)) < 1e-9, module.__name__


def test_a_typed_star_in_a_schema_s_labels_is_drawn_as_a_dot_too():
    """A schema's labels go through its own text_runs, which applies the same rule."""
    from domains import schema_svg
    out = []
    schema_svg._text(out, (0.0, 0.0), "2*F_(k,1)", 10.0, "#000000")
    written = re.findall(r"<text [^>]*>([^<]*)</text>", "".join(out))
    assert written[0] == "2·F" and not any("*" in t for t in written), written


# --- one entry's own thickness factors (v0.99) ------------------------------------------------------------------
# Every entry of a drawing may state a factor of its own over the drawing's three sliders (docs/domain/static-models.md §3.3octies,
# §10quater; calc/domains/figure_style.py): a factor MULTIPLYING the drawing's, never a size -- a static model
# being a scale-free sketch normalised to 1000 figure units, a size stated on one entry would mean nothing the
# next time the model is redrawn at another extent. What each collection may state is figure_style.ENTRY_KEYS.


def _sink():
    """One model carrying one of everything the figure draws: three kinds of member, three kinds of support, three kinds of release, both kinds of load, both kinds of dimension, an influence width and a colour.

    Its numbers are whole and its labels are plain on purpose: this model is what the frozen hash below is taken of, so nothing in it may depend on a font's rounding or on a value the export computes.
    """
    from domains import statics
    s = statics.new_source("SINK")
    s["label"] = "Bank"
    s["width"] = {"value": 2.5, "unit": "m", "label": "b_e", "description": "Achse 2-3", "show": True}
    s["points"] = [{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 4, "z": 0},
                   {"id": "P3", "x": 8, "z": 0, "label": "Firstpunkt"},
                   {"id": "P4", "x": 8, "z": 3}]
    s["members"] = [{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2", "label": "Traeger"},
                    {"id": "B2", "kind": "bar", "p1": "P2", "p2": "P3"},
                    {"id": "B3", "kind": "spring", "p1": "P3", "p2": "P4",
                     "stiffness": {"value": 1200.0, "unit": "kN/m"}}]
    s["supports"] = [{"id": "A1", "point": "P1", "type": "pinned", "label": "Auflager"},
                     {"id": "A2", "point": "P3", "type": "roller", "hinge": "through"},
                     {"id": "A3", "point": "P4", "type": "fixed", "angle": 30.0}]
    s["releases"] = [{"id": "G1", "member": "B2", "end": "start", "dof": "moment",
                      "stiffness": {"value": 900.0, "unit": "kNm/rad"}},
                     {"id": "G2", "member": "B2", "end": "end", "dof": "shear"},
                     {"id": "G3", "member": "B1", "end": "start", "dof": "normal"}]
    s["point_loads"] = [{"id": "F1", "point": "P2", "direction": "vertical", "label": "F_Ed",
                         "show": "name+value", "magnitude": {"value": 12.0, "unit": "kN"}},
                        {"id": "F2", "point": "P3", "direction": "angle", "angle": 135.0,
                         "label": "F_2", "show": "value", "color": "blue",
                         "magnitude": {"value": 3.0, "unit": "kN"}}]
    s["line_loads"] = [{"id": "q1", "member": "B1", "shape": "uniform", "direction": "vertical",
                        "label": "q_k", "show": "name+value",
                        "magnitude": {"value": 4.0, "unit": "kN/m2"}},
                       {"id": "q2", "member": "B2", "shape": "linear", "direction": "vertical",
                        "label": "q_s", "show": "name+value", "color": "green",
                        "magnitude": {"value": 0.0, "unit": "kN/m"},
                        "magnitude_end": {"value": 6.0, "unit": "kN/m"}}]
    s["dimensions"] = [{"id": "D1", "kind": "horizontal", "from": {"point": "P1"}, "to": {"point": "P3"},
                        "offset": 2.0, "label": "l", "show": "name+value"},
                       {"id": "D2", "kind": "angle", "from": {"member": "B2"}, "to": {"member": "B3"},
                        "offset": 1.4, "bearing": 45.0, "show": "value"}]
    return s


# The figure `_sink()` drew the day before the per-entry factors were written, one hash per language. A source that
# states no factor of its own must draw byte for byte as it did: an entry's own factor is an addition, and an
# addition that moved every figure already exported would be a change to every report.
FROZEN_SINK = {
    "de": "89e3e2f9f478ec34e3c2bf1d33586b3340cdf3f0b1706e058d349359b42d4258",
    "fr": "ffb8ca46ca27ac9b306bd71852f1c87cb230a9027547809f2bc0884448214288",
    "en": "e8b3b0c3027970a74a592d487110885280d1a2de2acd9188cd26b383026ef14d",
}


def _svg(source, lang="de"):
    from domains import statics_svg
    return statics_svg.render(statics_svg.layout(source, {}, lang))


def _drawing(source, lang="de"):
    from domains import statics_svg
    return statics_svg.layout(source, {}, lang)


def _placed(drawing):
    """What the layout placed, entry by entry and label by label, as text -- everything a factor stated on ONE entry must leave alone on every other. The sizes themselves (`sz`, `style`) are left out: they are what the factor changes."""
    import json
    out = {}
    for collection in ("points", "members", "supports", "releases", "dimensions", "loads"):
        for entry in drawing[collection]:
            out[(collection, entry["id"])] = json.dumps(
                {key: value for key, value in entry.items() if key not in ("sz", "style")},
                sort_keys=True, default=str)
    for frame in drawing["labels"]:
        out[("label", frame["collection"], frame["owner"])] = json.dumps(
            {key: value for key, value in frame.items() if key != "sz"}, sort_keys=True, default=str)
    return out


def test_a_model_that_states_no_own_factor_is_drawn_exactly_as_it_was():
    """The frozen figure of `_sink()`, in all three languages.

    ⚠️ When this moves, the figure moved: read the change, and re-freeze FROZEN_SINK only once it is the change that was wanted -- `python -c` on statics_svg.render prints the hash. Every static model already exported is a figure a report sets, so a size that shifts by a tenth of a unit shifts a page.
    """
    import hashlib
    source = _sink()
    for lang, wanted in FROZEN_SINK.items():
        svg = _svg(source, lang)
        got = hashlib.sha256(svg.encode("utf-8")).hexdigest()
        assert got == wanted, f"the {lang} figure moved: {got} ({len(svg)} characters), frozen at {wanted}"


def test_an_entry_that_states_no_factor_and_one_that_states_them_all_at_one_draw_alike():
    """The invariant behind the frozen hash, and the one that never goes stale: an empty `style`, and a `style` holding 1 for every factor that entry may state, both draw the figure the source draws without any. The second is the arithmetic itself -- `Sizes.scaled` builds a new object there -- so a factor of 1 that moved a coordinate would be a multiplication that is not exact."""
    import copy
    from domains import figure_style, statics
    plain = _svg(_sink())
    empty = copy.deepcopy(_sink())
    ones = copy.deepcopy(_sink())
    for collection in statics.ENTITIES:
        may = figure_style.allowed(statics.STYLE_KIND, collection)
        for entry in empty.get(collection, []):   # `texts` only where a text was placed (issue #43)
            entry["style"] = {}
        for entry in ones.get(collection, []):
            entry["style"] = {key: 1.0 for key in may}
    for name, source in (("an empty style", empty), ("every factor at 1", ones)):
        statics.check_source(source, "SINK.json")
        assert _svg(source) == plain, f"{name} moved the figure"


def test_an_own_line_factor_widens_that_entry_s_stroke_and_leaves_every_other_entry_alone():
    """A member drawn at twice the drawing's `line`: its own stroke is written at twice the width, its label steps twice as far clear of it, and nothing else the layout placed moves -- neither the other members' lines nor the supports, the releases, the loads or the dimensions.

    Its own placed geometry does not move either, and that is the point: where a member's ends are drawn is the model's, and how heavy its pen is is the factor's.
    """
    import copy
    from domains import statics, statics_svg
    plain, heavy = _sink(), copy.deepcopy(_sink())
    heavy["members"][0]["style"] = {"line": 2.0}
    statics.check_source(heavy, "SINK.json")
    before, after = _drawing(plain), _drawing(heavy)
    width = before["sz"].line(statics_svg.MEMBER_WIDTH["bar"])
    assert f'stroke-width="{statics_svg._f(2 * width)}"' in _svg(heavy), "the member's own stroke did not widen"
    assert f'stroke-width="{statics_svg._f(2 * width)}"' not in _svg(plain), "the doubled width was already there"
    assert after["members"][0]["sz"].line(statics_svg.MEMBER_WIDTH["bar"]) == 2 * width
    assert after["members"][1]["sz"] is after["sz"], "a member stating nothing was handed sizes of its own"
    moved = {key for key, value in _placed(after).items() if _placed(before).get(key) != value}
    assert moved == {("label", "members", "B1")}, moved


def test_an_own_text_factor_grows_that_label_and_the_frame_that_holds_it():
    """A point's label at two and a half times the drawing's `text`: its own box grows, no other label's does, and the figure's own frame widens to take it in -- which is what keeps a label the engineer asked to be read from running off the page."""
    import copy
    from domains import statics
    plain, big = _sink(), copy.deepcopy(_sink())
    big["points"][2]["style"] = {"text": 2.5}
    statics.check_source(big, "SINK.json")
    before, after = _drawing(plain), _drawing(big)
    grown = {f["owner"]: f for f in after["labels"] if f["collection"] == "points"}["P3"]
    was = {f["owner"]: f for f in before["labels"] if f["collection"] == "points"}["P3"]
    assert grown["hw"] > was["hw"] and grown["hh"] > was["hh"], (was["hw"], grown["hw"])
    others = {key for key, value in _placed(after).items() if _placed(before).get(key) != value}
    assert others == {("label", "points", "P3")}, others
    assert after["view"]["w"] >= before["view"]["w"] and after["view"]["h"] >= before["view"]["h"]


def test_two_loads_of_one_magnitude_draw_different_arrows_where_one_states_its_own_line():
    """Deliberately (docs/decisions.md §13): a figure whose arrow lengths are in proportion to their magnitudes is what a load stating nothing gives, and the exception is said out loud -- the engineer asked for one load to stand out and this is what he asked for. The scale is still the drawing's; the factor multiplies the length that scale gave."""
    import copy
    import math
    from domains import statics
    source = _model([])
    source["point_loads"] = [
        {"id": "F1", "point": "P1", "direction": "vertical", "show": "none", "magnitude": {"value": 5.0, "unit": "kN"}},
        {"id": "F2", "point": "P2", "direction": "vertical", "show": "none", "magnitude": {"value": 5.0, "unit": "kN"}},
    ]
    plain = {load["id"]: math.dist(*load["arrows"][0]) for load in _drawing(source)["loads"]}
    assert plain["F1"] == plain["F2"], plain
    louder = copy.deepcopy(source)
    louder["point_loads"][0]["style"] = {"line": 2.0}
    statics.check_source(louder, "S97.json")
    drawn = {load["id"]: math.dist(*load["arrows"][0]) for load in _drawing(louder)["loads"]}
    assert abs(drawn["F1"] - 2 * plain["F1"]) < 1e-9 and drawn["F2"] == plain["F2"], drawn


def test_a_factor_an_entry_does_not_draw_is_refused_naming_the_ones_it_may_state():
    """A point draws its label and nothing else, a member draws no symbol on a node, an arrow is not one either: a factor an entry cannot show is a field that would acquire a value nobody checks and a meaning nobody remembers, which is the argument that took `plates.thickness` out of a connector's source in v0.70."""
    import copy
    from domains import figure_style, statics
    for collection, key in (("points", "line"), ("points", "point"), ("members", "point"),
                            ("point_loads", "point"), ("line_loads", "point"), ("dimensions", "point")):
        bad = copy.deepcopy(_sink())
        bad[collection][0]["style"] = {key: 1.5}
        try:
            statics.check_source(bad, "SINK.json")
        except statics.validation.ValidationError as exc:
            message = str(exc)
        else:
            raise AssertionError(f"a {collection} entry stating {key} passed the check")
        may = figure_style.allowed(statics.STYLE_KIND, collection)
        assert bad[collection][0]["id"] in message and f"style.{key}" in message, message
        assert all(name in message for name in may), (message, may)
    # and a factor that is no factor at all says which three there are
    worse = copy.deepcopy(_sink())
    worse["members"][0]["style"] = {"stroke": 2.0}
    try:
        statics.check_source(worse, "SINK.json")
    except statics.validation.ValidationError as exc:
        assert all(name in str(exc) for name in figure_style.KEYS), str(exc)
    else:
        raise AssertionError("a member stating 'stroke' passed the check")


def test_a_factor_outside_the_range_is_refused_naming_the_range():
    """The drawing's own three and an entry's own share one range, `figure_style.RANGE`, so that a slider means the same thing wherever it stands.

    A factor that is not a number at all is refused by the schema walk first, which names the field and the row it stands in rather than the entry's own id -- `check_source` runs `validate_structure` before every rule a schema cannot state, and either way the source does not pass.
    """
    import copy
    from domains import figure_style, statics
    assert (statics.STYLE_KEYS, statics.STYLE_RANGE) == (figure_style.KEYS, figure_style.RANGE)
    for factor in (0.1, 3.5):
        bad = copy.deepcopy(_sink())
        bad["supports"][0]["style"] = {"point": factor}
        try:
            statics.check_source(bad, "SINK.json")
        except statics.validation.ValidationError as exc:
            assert "A1" in str(exc) and "style.point" in str(exc), str(exc)
            assert str(figure_style.RANGE[1]) in str(exc), str(exc)
        else:
            raise AssertionError(f"a support stating point = {factor!r} passed the check")
    for factor in (True, "2", None):
        bad = copy.deepcopy(_sink())
        bad["supports"][0]["style"] = {"point": factor}
        try:
            statics.check_source(bad, "SINK.json")
        except statics.validation.ValidationError as exc:
            assert "style.point" in str(exc), (factor, str(exc))
        else:
            raise AssertionError(f"a support stating point = {factor!r} passed the check")
    # the drawing's own three are checked the same way, and name no entry
    whole = copy.deepcopy(_sink())
    whole["style"]["text"] = 4.0
    try:
        statics.check_source(whole, "SINK.json")
    except statics.validation.ValidationError as exc:
        assert "style.text" in str(exc) and "3.0" in str(exc), str(exc)
    else:
        raise AssertionError("a drawing stating text = 4 passed the check")


def test_the_export_carries_the_factors_an_entry_states_and_nothing_where_it_states_none():
    """A record says what each part of the figure was drawn with, which is the convention every other placed value here follows -- and carries no `style` key at all for an entry that follows the drawing, so a record written before the factors existed is unchanged."""
    import copy
    import json
    from domains import statics
    from conftest import tmpdir
    source = copy.deepcopy(_sink())
    source["members"][0]["style"] = {"line": 2.0, "text": 0.5}
    source["supports"][0]["style"] = {"point": 1.5}
    source["point_loads"][0]["style"] = {"line": 0.75}
    source["dimensions"][0]["style"] = {"line": 1.25}
    source["points"][2]["style"] = {"text": 2.0}
    folder = tmpdir("statics_style_export")
    (folder / "SINK.json").write_text(json.dumps(source), encoding="utf-8")
    data, _files, notes = statics.prepare(folder)      # validated against schemas/statics.schema.json on the way out
    record = data["models"]["SINK"]
    assert not notes, notes
    assert record["members"][0]["style"] == {"line": 2.0, "text": 0.5}
    assert record["supports"][0]["style"] == {"point": 1.5}
    assert record["loads"][0]["style"] == {"line": 0.75}
    assert record["dimensions"][0]["style"] == {"line": 1.25}
    assert record["points"][2]["style"] == {"text": 2.0}
    for collection, index in (("members", 1), ("supports", 1), ("loads", 1), ("dimensions", 1), ("points", 0)):
        assert "style" not in record[collection][index], record[collection][index]
    # the drawing's own three stay where they were, beside them
    assert record["style"] == {"line": 1.0, "point": 1.0, "text": 1.0}


def test_a_halo_grows_with_the_part_it_marks():
    """A ring thinner than the symbol under it marks nothing, so a halo is carried by the factor that widened what it marks: `line` for a member, an arrow or a dimension line, `point` for a symbol on a node."""
    import copy
    from domains import statics_svg
    plain, heavy = _sink(), copy.deepcopy(_sink())
    heavy["members"][0]["style"] = {"line": 2.0}
    heavy["releases"][0]["style"] = {"point": 2.0}
    heavy["point_loads"][0]["style"] = {"line": 2.0}
    widths = lambda source, ids: [float(w) for w in re.findall(
        r'stroke-width="([\d.]+)"', statics_svg.halo(_drawing(source), ids))]
    radii = lambda source, ids: [float(r) for r in re.findall(
        r'<circle [^>]*r="([\d.]+)"', statics_svg.halo(_drawing(source), ids))]
    for ids, measure in (("B1", widths), ("F1", widths), ("G1", radii)):
        before, after = measure(plain, ids), measure(heavy, ids)
        assert before and after and all(b < a for b, a in zip(before, after)), (ids, before, after)
    # a point draws nothing of its own to mark, so its halo is the drawing's whatever it states
    text = copy.deepcopy(_sink())
    text["points"][2]["style"] = {"text": 3.0}
    assert radii(text, "P3") == radii(plain, "P3")


def test_the_break_a_release_opens_keeps_the_drawing_s_own_factors():
    """The accepted price of the cut belonging to the node (statics_svg._release_cuts): both member ends meeting there are drawn back by the same amount, which a cut taken from each member's own `line` would break -- the very thing v0.55 repaired. So a heavier release is a heavier symbol standing in the break the drawing sizes."""
    import copy
    from domains import statics_svg
    plain, heavy = _sink(), copy.deepcopy(_sink())
    heavy["releases"][1]["style"] = {"point": 3.0}       # G2, the shear release on B2's far end
    heavy["members"][1]["style"] = {"line": 3.0}         # and the member it cuts
    before, after = _drawing(plain), _drawing(heavy)
    runs = lambda drawing: {m["id"]: m["runs"] for m in drawing["members"]}
    assert runs(after) == runs(before), "the break moved with a factor of its own"
    extent = lambda drawing, rid: statics_svg._release_extent(
        next(r for r in drawing["releases"] if r["id"] == rid), statics_svg._own(
            next(r for r in drawing["releases"] if r["id"] == rid), drawing["sz"]))
    assert extent(after, "G2") == 3 * extent(before, "G2"), "the symbol itself did not grow"


# --- the same factors in the window's «Modèles statiques» tab ----------------------------------------------------


def _style_source():
    source = _model([{"id": "G1", "member": "B1", "end": "end", "dof": "moment"}])
    source["points"][0]["label"] = "N"
    source["members"][0]["label"] = "B"
    source["point_loads"] = [{"id": "F1", "point": "P2", "direction": "vertical", "label": "F",
                              "show": "name+value", "magnitude": {"value": 2.0, "unit": "kN"}}]
    source["line_loads"] = [{"id": "q1", "member": "B1", "shape": "uniform", "direction": "vertical",
                             "label": "q", "show": "name+value", "magnitude": {"value": 1.5, "unit": "kN/m"}}]
    source["dimensions"] = [{"id": "D1", "kind": "horizontal", "from": {"point": "P1"}, "to": {"point": "P2"},
                             "offset": 1.0, "show": "value"}]
    return source


def test_the_selection_s_card_shows_the_factors_that_entry_may_state_and_no_others():
    """One card, «Épaisseurs de cet élément», with a row per factor the selected entry is drawn with and no row at all for one it is not -- a factor an entry cannot show is not a field it could be typed into."""
    from PySide6.QtWidgets import QGroupBox
    from domains import figure_style, statics
    tab = _statics_tab(_style_source())
    try:
        for collection, eid in (("points", "P1"), ("members", "B1"), ("supports", "A1"), ("releases", "G1"),
                                ("point_loads", "F1"), ("line_loads", "q1"), ("dimensions", "D1")):
            tab.canvas.select((collection, eid))
            cards_shown = [b for b in tab.selection_group.findChildren(QGroupBox)
                           if b.title() == tab.t("st_style_own")]
            assert len(cards_shown) == 1, (collection, [b.title() for b in tab.selection_group.findChildren(QGroupBox)])
            shown = tuple(key for key, row in tab.style_rows.rows.items()
                          if row["name"].isVisibleTo(cards_shown[0]))
            assert shown == figure_style.allowed(statics.STYLE_KIND, collection), (collection, shown)
            assert all(row["slider"].value() == 100 for row in tab.style_rows.rows.values()), collection
    finally:
        tab.dirty = False


def test_a_factor_set_in_the_panel_is_one_step_of_annuler_and_reprendre_takes_it_off():
    """Set, the row is orange with «Reprendre» beside it -- an overridden b/h's own form (v0.75). Taken back, the factor leaves the entry, and the whole `style` goes with the last of them, so an entry that overrides nothing is saved exactly as it was."""
    tab = _statics_tab(_style_source())
    try:
        tab.canvas.select(("members", "B1"))
        row = tab.style_rows.rows["line"]
        assert not row["back"].isVisibleTo(tab.selection_group), "«Reprendre» is offered before anything is written over"
        steps = len(tab.undo_stack)
        row["slider"].setValue(200)
        assert tab.source["members"][0]["style"] == {"line": 2.0}, tab.source["members"][0]
        assert len(tab.undo_stack) == steps + 1, "a factor set is one step of «Annuler»"
        assert "color:" in row["name"].styleSheet() and "color:" in row["readout"].styleSheet()
        assert row["back"].isVisibleTo(tab.selection_group), "«Reprendre» is not offered on a factor written over"
        assert row["readout"].text() == "200 %"
        # the text row beside it is untouched, and says so
        text = tab.style_rows.rows["text"]
        assert text["slider"].value() == 100 and not text["back"].isVisibleTo(tab.selection_group)
        row["back"].click()
        assert "style" not in tab.source["members"][0], tab.source["members"][0]
        tab.undo()
        assert tab.source["members"][0].get("style") == {"line": 2.0}, tab.source["members"][0]
        tab.undo()
        assert "style" not in tab.source["members"][0], tab.source["members"][0]
    finally:
        tab.dirty = False


def test_a_dragged_slider_makes_one_step_of_annuler_and_none_where_it_ends_where_it_began():
    """A drag arrives one pixel at a time: the step is pushed when the slider is taken hold of and dropped again where nothing moved, which is `edit`'s own rule. ⚠️ The drawing's own three sliders still leave a drag outside the history altogether (`on_style`), which is a separate thing."""
    tab = _statics_tab(_style_source())

    def drag(*values):
        """A slider taken hold of, moved through `values` in per cent, and let go. The row is looked up afresh each time: «Annuler» rebuilds the panel, and a widget read across it is one Qt has deleted."""
        tab.canvas.select(("members", "B1"))
        slider = tab.style_rows.rows["line"]["slider"]
        tab.style_drag_begin()
        for value in values:
            slider.setValue(value)
        tab.style_drag_end()

    try:
        steps = len(tab.undo_stack)
        drag(110, 140, 175)
        assert tab.source["members"][0]["style"] == {"line": 1.75}, tab.source["members"][0]
        assert len(tab.undo_stack) == steps + 1, f"a drag made {len(tab.undo_stack) - steps} steps"
        # a drag that ends on the factor it began from leaves none
        steps = len(tab.undo_stack)
        drag(150, 175)
        assert len(tab.undo_stack) == steps, "a drag that changed nothing left a step behind"
        assert tab.source["members"][0]["style"] == {"line": 1.75}, tab.source["members"][0]
        # ⚠️ dragged back to 100 % it states 1, and that is one step: the b/h rule of v0.75, «typing the very
        # value the position holds still writes it over». «Reprendre» is what takes a factor off.
        drag(100)
        assert tab.source["members"][0]["style"] == {"line": 1.0}, tab.source["members"][0]
        assert len(tab.undo_stack) == steps + 1
        tab.undo()
        tab.undo()
        assert "style" not in tab.source["members"][0], tab.source["members"][0]
    finally:
        tab.dirty = False


def test_the_card_s_words_are_written_in_the_three_languages():
    """`st_style_own`, its note and «Reprendre», in French, German and English -- and the German is Swiss, which is to say it carries no ß (docs/typst/language.md §4bis)."""
    import sys
    from conftest import ROOT, Skip
    path = str(ROOT / "calc" / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        import statics_tab
    except ImportError as exc:
        raise Skip(f"the tab cannot be imported here ({exc})")
    for key in ("st_style_own", "st_style_own_note", "st_style_take_back"):
        said = {lang: statics_tab.STRINGS[lang][key] for lang in ("fr", "de", "en")}
        assert all(said.values()), (key, said)
        assert len(set(said.values())) == 3, (key, said)
        assert "ß" not in said["de"], (key, said["de"])
