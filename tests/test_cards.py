"""Forms in cards, after the website (calc/tools/cards.py; v0.93, docs/ui/window.md §10quater): the second half of stage C, one tab at a time -- Moments polaires first.

What is held here: a card is a QGroupBox dressed by the style sheet, its title kept, so a tab's code and every test that finds a box by its title work as before; the style sheet dresses the card, its ground, its note and a member's badge, and theme.json carries the card's own token in both schemes; the card's title is set in semibold while what is in the card is not; in Moments polaires every box of the form and of the right pane is a card, the members are rows of one card with the reference beside them where a box each and a «Géométrie» box stood, the ✕ only where more than the fewest remain, and the form never cut at its right edge -- its column asks for its cards' width, in the three languages -- where it overflowed with a horizontal scroll bar under it until v0.93. Then the position plan's, the static models' and the schemas' properties and the connectors' form and preview: every box a card, a card's rows of «label field» putting the label above the field where the two do not fit side by side, a connector's two pieces side by side where the column has the room and one under the other where it does not (cards.Reflow), and neither column cut at its right edge.

⚠️ Built off-screen, in the scheme conftest seeds; a scheme is never changed here (test_theme.py runs that in a process of its own).
"""

import os
import sys

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
_WINDOW = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _polar():
    if "window" not in _WINDOW:
        app = _qt()
        import woodcore_gui
        from PySide6.QtCore import Qt
        window = woodcore_gui.MainWindow()
        window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        window.resize(1400, 820)
        window.show()
        _WINDOW["window"] = window
        _WINDOW["app"] = app
    window = _WINDOW["window"]
    import woodcore_gui
    tab = next(t for t in window.tabs if isinstance(t, woodcore_gui.PolarTab))
    window.tab_widget.setCurrentWidget(tab)
    _pump()
    tab.dirty = False   # a modal off-screen never comes back (tests/test_connectors.py's own warning)
    return tab


def _tab(kind):
    """Another tab of the same window, brought to the front: «PlanTab», «ConnectorsTab»."""
    _polar()
    window = _WINDOW["window"]
    tab = next(t for t in window.tabs if type(t).__name__ == kind)
    window.tab_widget.setCurrentWidget(tab)
    _pump()
    tab.dirty = False
    return tab


def _top_boxes(body):
    """The boxes laid straight into a column, not those inside them."""
    from PySide6.QtWidgets import QGroupBox
    layout = body.layout()
    return [layout.itemAt(i).widget() for i in range(layout.count()) if isinstance(layout.itemAt(i).widget(), QGroupBox)]


def _pump(rounds=6):
    from PySide6.QtCore import QCoreApplication, QEvent
    app = _WINDOW.get("app") or _qt()
    for _ in range(rounds):
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_a_card_is_a_group_box_the_style_sheet_dresses():
    _qt()
    import cards
    import theme
    from PySide6.QtWidgets import QGroupBox, QScrollArea
    box = cards.card("Identité")
    assert isinstance(box, QGroupBox) and box.title() == "Identité" and box.property("card") is True
    note = cards.note("<b>not HTML</b>")
    assert note.objectName() == "cardNote" and note.wordWrap() and note.textFormat().name == "PlainText"
    scroll, layout = cards.column()
    assert isinstance(scroll, QScrollArea) and scroll.widget().objectName() == "cardGround" and scroll.widget().layout() is layout
    from PySide6.QtCore import Qt
    assert scroll.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff, "a column of cards scrolls sideways"
    for rule in ('QWidget#cardGround', 'QGroupBox[card="true"]', 'QGroupBox[card="true"]::title', 'QLabel#cardNote', 'QLabel#cardBadge'):
        assert rule in theme.STYLE, f"the style sheet does not dress {rule}"
    assert "{card}" in theme.STYLE
    for scheme in theme.SCHEMES:
        assert "card" in theme.tokens(scheme), f"theme.json's {scheme} scheme has no card token"
    light, dark = theme.tokens("light"), theme.tokens("dark")
    assert light["card"] == light["bg"], "a light card is the site's white"
    assert _luminance(dark["card"]) > _luminance(dark["bg-soft"]), "a dark card is not lighter than the ground it is raised from"


def _luminance(hex_):
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def test_a_cards_title_is_semibold_and_its_fields_are_not():
    tab = _polar()
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QGroupBox
    identity = next(b for b in tab.findChildren(QGroupBox) if b.title() == tab.t("polar_identity"))
    assert identity.font().weight() >= QFont.Weight.DemiBold, "the card's title is not set in semibold"
    assert tab.name_edit.font().weight() < QFont.Weight.DemiBold, "the card's fields took its title's weight"


def test_every_box_of_the_polar_tab_is_a_card():
    tab = _polar()
    from PySide6.QtWidgets import QGroupBox
    boxes = tab.findChildren(QGroupBox)
    titles = {b.title() for b in boxes}
    for key in ("polar_identity", "polar_members", "polar_fasteners", "polar_center", "polar_directions", "polar_figure", "polar_results", "polar_trial"):
        assert tab.t(key) in titles, f"no card «{tab.t(key)}»"
    # the calls left the right pane for the «Affichage» view in v0.117: cards there too
    assert {tab.t("ds_command"), tab.t("ds_call")} <= {b.title() for b in tab.display.right.findChildren(QGroupBox)}
    plain = [b.title() for b in boxes if b.property("card") is not True]
    assert not plain, f"boxes not dressed as cards: {plain}"
    import woodcore_gui
    assert all("polar_geometry" not in woodcore_gui.STRINGS[lang] for lang in woodcore_gui.LANGUAGES), "the «Géométrie» box is back"


def test_the_members_are_rows_of_one_card_with_the_reference_beside_them():
    tab = _polar()
    tab.load_first()
    from PySide6.QtWidgets import QGroupBox
    members = next(b for b in tab.findChildren(QGroupBox) if b.title() == tab.t("polar_members"))
    for widgets in tab.members:
        for key in ("badge", "name", "element"):
            assert members.isAncestorOf(widgets[key]), f"a member's {key} is not in the Éléments card"
    assert members.isAncestorOf(tab.reference_combo) and members.isAncestorOf(tab.add_member_button)
    assert all(w["remove"] is None for w in tab.members), "a ✕ where only the fewest members remain"
    count = len(tab.members)
    tab.add_member()
    _pump()
    assert len(tab.members) == count + 1 and all(w["remove"] is not None for w in tab.members)
    assert [w["badge"].text() for w in tab.members] == [str(i + 1) for i in range(count + 1)]
    tab.remove_member(len(tab.members) - 1)
    _pump()
    assert len(tab.members) == count and all(w["remove"] is None for w in tab.members)
    orphans = [w for group in tab.member_groups for w in group if not members.isAncestorOf(w)]
    assert not orphans, "a rebuilt row left the card"
    tab.load_first()
    tab.dirty = False


def test_the_form_is_never_cut_at_its_right_edge():
    """Until v0.93 the form was wider than its pane: a horizontal scroll bar under it, «Ajouter un élément» and the table cut at its right edge. A column of cards asks for its cards' width as its minimum (cards.Column), so the splitter never squeezes it below them -- in the three languages, and whatever the font: off-screen the text is drawn about twice as wide as on the engineer's screen, which is why nothing here is a number of pixels.

    And the rotation centre's choices are stacked, each with what it takes on the line under it: side by side they were what set the form's width (a radio's text cannot wrap)."""
    window = _polar().app
    import cards
    import woodcore_gui
    before = window.lang
    short = {}
    size = window.size()
    window.resize(2400, 900)   # room for every pane's minimum with the text drawn twice as wide as on screen: what is held is that the form's is its cards'
    try:
        for lang in woodcore_gui.LANGUAGES:
            window.language.setCurrentIndex(list(woodcore_gui.LANGUAGES).index(lang))
            tab = _polar()
            scroll = tab.splitter.widget(1).widget(0)   # the centre is a stack since v0.117: the form, and the «Affichage» view's page
            assert isinstance(scroll, cards.Column) and scroll.minimumWidth() == 0, "the form's column has a fixed minimum, which wins over its cards' width"
            needed = scroll.widget().minimumSizeHint().width()
            if scroll.viewport().width() < needed or scroll.minimumSizeHint().width() < needed:
                short[lang] = (scroll.viewport().width(), needed, _widest(scroll.widget()))
            x_cell = tab.link_fields["center.x"]   # the field with its variable button (issue #42), what the grid holds
            grid = x_cell.parentWidget().layout()
            rows = {name: grid.getItemPosition(grid.indexOf(widget))[0] for name, widget in (("manual", tab.manual_radio), ("x", x_cell), ("aid", tab.aid_radio), ("combo", tab.center_aid))}
            assert rows["manual"] != rows["x"] and rows["aid"] != rows["combo"], f"the centre's choices are side by side again: {rows}"
    finally:
        window.language.setCurrentIndex(list(woodcore_gui.LANGUAGES).index(before))
        window.resize(size)
    assert not short, f"the form is cut at its right edge: {short}"


def _widest(body):
    """What sets a column's width: each card's minimum and its widest field -- what a failure names."""
    from PySide6.QtWidgets import QGroupBox, QWidget
    out = []
    for box in body.findChildren(QGroupBox):
        fields = [(max(w.minimumSizeHint().width(), w.minimumWidth()), type(w).__name__, (w.text() if hasattr(w, "text") and callable(w.text) else "")[:30])
                  for w in box.findChildren(QWidget)]
        out.append((box.title(), box.minimumSizeHint().width(), max(fields) if fields else None))
    return out


def test_the_plan_s_properties_are_cards_whose_labels_go_above_their_fields():
    """The position plan's properties, in cards: every box laid into the column is one, and a card's «label field» rows put the label above its field where the two do not fit side by side -- «Visibilité de l'arrière-plan» beside its slider set the pane's width as the sum of the two."""
    import cards
    from PySide6.QtWidgets import QFormLayout
    tab = _tab("PlanTab")
    # the right pane is a stack since v0.114 -- the plan's properties, a document's card, a sheet's options, the command builder's -- and the plan's are its first page
    scroll = tab.splitter.widget(2).widget(0).findChild(cards.Column)
    assert scroll is not None and scroll.hold, "the plan's properties are not a column of cards"
    boxes = _top_boxes(scroll.widget())
    assert boxes and all(box.property("card") for box in boxes), [box.title() for box in boxes if not box.property("card")]
    assert tab.selection_group in boxes
    forms = scroll.widget().findChildren(QFormLayout)
    assert forms and all(form.rowWrapPolicy() == QFormLayout.RowWrapPolicy.WrapLongRows for form in forms), "a card's form sets its label and its field side by side whatever the width"


def test_the_connectors_form_and_what_is_read_off_it_are_cards():
    """Moyens d'assemblage in cards: the boxes of the form, the figures, the results and the calls. A titled «Pièce» is a card inside its card; the untitled member of a Stahl-Holz joint stays a flat box, a card's room for a title being empty then."""
    import cards
    from PySide6.QtWidgets import QGroupBox
    tab = _tab("ConnectorsTab")
    columns = tab.findChildren(cards.Column)
    form = next((c for c in columns if c.hold), None)
    assert form is not None, "the connectors' form is not a column of cards"
    boxes = _top_boxes(form.widget())
    assert boxes and all(box.property("card") for box in boxes), [box.title() for box in boxes if not box.property("card")]
    for box in form.widget().findChildren(QGroupBox):
        if box not in boxes:
            assert bool(box.property("card")) == bool(box.title()), f"«{box.title()}»: a titled piece is a card, an untitled one a flat box"
    titles = {box.title() for box in tab.findChildren(QGroupBox) if box.property("card")}
    for key in ("cn_figures", "cn_results", "cn_types"):
        assert tab.t(key) in titles, f"«{tab.t(key)}» is not a card"
    assert tab.t("ds_call") in titles, "the calls are a card of the «Affichage» view since v0.117"


def test_cards_read_side_by_side_go_one_under_the_other_where_the_column_is_narrower():
    """cards.Reflow: side by side from the two cards' width up, one under the other below it, and never asking for more than one card's width -- a connector's two pieces were cut at the column's right edge in a window of 1440 px."""
    _qt()
    import cards
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QBoxLayout, QLabel, QVBoxLayout
    row = cards.Reflow()
    row.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    for n in (1, 2):
        box = cards.card(f"Pièce {n}")
        QVBoxLayout(box).addWidget(QLabel("Angle entre la direction de l'effort et le fil"))
        row.addWidget(box)
    one = max(card.minimumSizeHint().width() for card in row.cards())
    assert row.minimumSizeHint().width() == one, "a row of cards asks for more than one card's width"
    row.show()
    row.resize(row.side_by_side() + 40, 400)
    _pump()
    first, second = row.cards()
    assert row.row.direction() == QBoxLayout.Direction.LeftToRight and first.y() == second.y(), "two cards with the room are not side by side"
    row.resize(one + 10, 400)
    _pump()
    assert row.row.direction() == QBoxLayout.Direction.TopToBottom and second.y() > first.y(), "two cards without the room are not one under the other"
    row.resize(row.side_by_side() + 40, 400)
    _pump()
    assert row.row.direction() == QBoxLayout.Direction.LeftToRight, "the cards do not come back side by side"
    row.close()
    tab = _tab("ConnectorsTab")
    rows = [r for r in tab.findChildren(cards.Reflow) if len(r.cards()) == 2]
    assert rows, "a connector's two pieces are not a row of cards"


def test_no_column_of_cards_is_cut_at_its_right_edge():
    """As the polar moment's form: a column of cards asks for its cards' width and is given it, in the three languages -- the plan's, the static models' and the schemas' properties and the connectors' form, which overflowed their panes with a horizontal scroll bar before v0.95."""
    window = _polar().app   # first: it puts calc/tools on the path, which this test may be the first of its file to need
    import cards
    import woodcore_gui
    before = window.lang
    size = window.size()
    short = {}
    window.resize(2400, 900)
    try:
        for lang in woodcore_gui.LANGUAGES:
            window.language.setCurrentIndex(list(woodcore_gui.LANGUAGES).index(lang))
            for kind in ("PlanTab", "ConnectorsTab", "StaticsTab", "SchemaTab"):
                tab = _tab(kind)
                for scroll in tab.findChildren(cards.Column):
                    if not scroll.hold or not scroll.isVisible():
                        continue
                    assert scroll.minimumWidth() == 0, f"{kind}: a column of cards has a fixed minimum, which wins over its cards' width"
                    needed = scroll.widget().minimumSizeHint().width()
                    if scroll.viewport().width() < needed:
                        short[(lang, kind)] = (scroll.viewport().width(), needed, _widest(scroll.widget()))
    finally:
        window.language.setCurrentIndex(list(woodcore_gui.LANGUAGES).index(before))
        window.resize(size)
    assert not short, f"a form is cut at its right edge: {short}"


def test_the_static_models_and_the_schemas_properties_are_cards():
    """Modèles statiques and Schémas, once their tool bars were in (v0.95): every box of the properties is a card in a column of cards, the selection's own boxes -- a support, a release, a load's look and intensity -- cards inside its card, and the rows of «label field» wrapping."""
    import cards
    from PySide6.QtWidgets import QFormLayout, QGroupBox
    for kind, selection in (("StaticsTab", ("point_loads", "F1")), ("SchemaTab", None)):
        tab = _tab(kind)
        if selection is not None:
            tab.canvas.select(selection)
            _pump()
        columns = [c for c in tab.findChildren(cards.Column) if c.hold and not tab.display.right.isAncestorOf(c)]   # not the «Affichage» view's (v0.117)
        assert columns, f"{kind}: the properties are not a column of cards"
        body = columns[0].widget()
        boxes = _top_boxes(body)
        assert boxes and all(box.property("card") for box in boxes), (kind, [box.title() for box in boxes if not box.property("card")])
        inner = [box for box in body.findChildren(QGroupBox) if box not in boxes]
        assert all(box.property("card") for box in inner), (kind, [box.title() for box in inner if not box.property("card")])
        if selection is not None:
            assert inner, f"{kind}: a selected load shows no card inside the selection's card"
        forms = body.findChildren(QFormLayout)
        assert forms and all(form.rowWrapPolicy() == QFormLayout.RowWrapPolicy.WrapLongRows for form in forms), f"{kind}: a card's form sets its label and its field side by side whatever the width"
