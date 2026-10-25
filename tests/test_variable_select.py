"""The choice of variables «comme dans Windows» (calc/variable_select.py; spec 2026-10-24-onglet-variables-groupes, UI-009, UI-010, REQ-007, REQ-008, D-15).

⚠️ **A range runs across the domains and never takes a title line**: the list gives the keys of its variables
in its order, and a title line has none.

⚠️ **A choice survives a filter** (D-15): a variable chosen then hidden stays chosen, and «Copier» puts it after
the variables shown.
"""

TIER = "fast"  # tests/run_tests.py --fast

from variable_select import Selection

# two domains, the list's order: SL's two variables, then A1's three -- the title lines are no keys
SL = [("export", "snow-load · SL", k) for k in ("s_k", "q_k1")]
A1 = [("export", "live-load · A1", k) for k in ("q_k", "Q_k", "psi_0")]
SHOWN = SL + A1


def test_a_click_takes_one_variable_alone_and_is_the_last_clicked():
    s = Selection()
    s.click(SL[0], SHOWN)
    s.click(A1[1], SHOWN)
    assert s.keys(SHOWN) == [A1[1]] and s.focus == A1[1]


def test_ctrl_or_the_box_adds_or_takes_away():
    s = Selection()
    s.click(SL[0], SHOWN)
    s.click(A1[0], SHOWN, ctrl=True)
    s.click(A1[2], SHOWN, box=True)
    assert s.keys(SHOWN) == [SL[0], A1[0], A1[2]] and s.focus == A1[2]
    s.click(A1[0], SHOWN, ctrl=True)
    assert s.keys(SHOWN) == [SL[0], A1[2]] and s.focus == A1[0], "taken away, and still the last clicked"


def test_shift_takes_the_range_across_the_domains_from_the_last_clicked():
    s = Selection()
    s.click(SL[1], SHOWN)
    s.click(A1[1], SHOWN, shift=True)
    assert s.keys(SHOWN) == [SL[1], A1[0], A1[1]], "across the two domains, no title line"
    assert s.anchor == SL[1] and s.focus == A1[1]
    # a second Shift+click starts again from the same anchor, and replaces the range
    s.click(SL[0], SHOWN, shift=True)
    assert s.keys(SHOWN) == [SL[0], SL[1]]


def test_ctrl_shift_adds_the_range_to_what_is_chosen():
    s = Selection()
    s.click(A1[2], SHOWN)
    s.click(SL[0], SHOWN, ctrl=True)
    s.click(SL[1], SHOWN, ctrl=True, shift=True)
    assert s.keys(SHOWN) == [SL[0], SL[1], A1[2]]


def test_the_header_s_box_takes_every_variable_shown_or_lets_all_go():
    s = Selection()
    s.set_all(SHOWN, True)
    assert s.keys(SHOWN) == SHOWN and s.all_shown(SHOWN)
    s.set_all(SHOWN, False)
    assert len(s) == 0 and not s.all_shown(SHOWN)


def test_a_variable_chosen_then_hidden_stays_chosen_and_is_copied_after_the_shown():
    s = Selection()
    s.click(A1[0], SHOWN)
    s.click(SL[0], SHOWN, ctrl=True)
    s.click(A1[2], SHOWN, ctrl=True)
    filtered = A1           # a filter hides SL
    assert SL[0] in s and s.hidden(filtered) == 1
    assert s.copy_order(filtered, SHOWN) == [A1[0], A1[2], SL[0]]
    # unfiltered, the order of the list, not the order of the clicks
    assert s.copy_order(SHOWN, SHOWN) == [SL[0], A1[0], A1[2]]


def test_clear_lets_everything_go_and_keeps_the_card():
    s = Selection()
    s.click(A1[0], SHOWN)
    s.clear()
    assert len(s) == 0 and s.focus == A1[0]


def test_the_keyboard_follows_the_mouse():
    s = Selection()
    s.step(SHOWN, +1)
    assert s.keys(SHOWN) == [SL[0]], "an arrow in a list where nothing is chosen takes the first"
    s.step(SHOWN, +1)
    assert s.keys(SHOWN) == [SL[1]] and s.focus == SL[1], "an arrow is a click"
    s.step(SHOWN, +1, shift=True)
    s.step(SHOWN, +1, shift=True)
    assert s.keys(SHOWN) == [SL[1], A1[0], A1[1]] and s.anchor == SL[1], "Shift+arrow is a Shift+click, across the domains"
    s.space(SHOWN)
    assert s.keys(SHOWN) == [SL[1], A1[0]], "Space is the box of the last one"
    s.set_all(SHOWN, True)   # Ctrl+A
    assert s.keys(SHOWN) == SHOWN
    s.step(SHOWN, -10)
    assert s.keys(SHOWN) == [SL[0]], "an arrow stops at the first"


def test_while_a_field_is_linked_one_value_and_the_choice_of_before_comes_back():
    """REQ-008, D-8: a field follows one value -- Ctrl+click does not take two, the header's box takes nothing --; the field's choice ended, the boxes come back with what was chosen."""
    s = Selection()
    s.click(SL[0], SHOWN)
    s.click(A1[0], SHOWN, ctrl=True)
    s.begin_single()
    s.click(A1[1], SHOWN)
    s.click(A1[2], SHOWN, ctrl=True)
    assert s.keys(SHOWN) == [A1[2]] and s.focus == A1[2]
    s.click(SL[0], SHOWN, shift=True)
    assert s.keys(SHOWN) == [SL[0]]
    s.set_all(SHOWN, True)
    assert len(s) == 1
    s.end_single()
    assert s.keys(SHOWN) == [SL[0], A1[0]] and not s.single
