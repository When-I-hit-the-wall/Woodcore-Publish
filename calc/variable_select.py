"""The choice of variables in the «Variables» tab, «comme dans Windows» (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, UI-009, UI-010, REQ-007, REQ-008, D-8, D-15; docs/ui/tab-variables.md).

The engineer's prototype (`pick`, `copySel`): a click takes this variable alone; Ctrl+click or a click on its
box adds it or takes it away; Shift+click the range from the last one clicked, **across the domains**,
Ctrl+Shift adding it to what is chosen; the header's box takes every variable shown or lets them all go. The
boxes and the choice are one notion: what the list paints is what this holds.

⚠️ **Not Qt's own selection** (ARCH-007, D-16): Qt's range takes the domains' title lines, knows no «last one
clicked», and forgets a choice the filter hides. Here a range runs over the keys of the variables shown --
never a title line, which is no key --, the last one clicked is the anchor of the next range and the variable
the card shows (`focus`, what `selected_key()` answers), and a choice survives a filter: «Copier» takes the
variables shown first, in the order of the list, then those hidden, in the order of the whole list, and the
bar counts them apart.

⚠️ **One value while a field is linked** (REQ-008, D-8): a field follows one variable, so the choice is
single -- no box, a click choosing one --, and what was chosen before is kept aside and comes back with the
boxes when the choice for the field ends.

No Qt: the list gives the clicks, their modifiers and the keys; it paints what this says.
"""


class Selection:
    """The variables chosen, in the order they were taken, the last one clicked (`focus`) and the anchor of a range. Keys are (origin, domain, name)."""

    def __init__(self):
        self.chosen = {}        # key -> True, in the order taken (a dict keeps it)
        self.anchor = None
        self.focus = None
        self.single = False
        self._kept = None       # the choice of before a field's choice began (REQ-008)

    # -- what it holds --

    def __contains__(self, key):
        return tuple(key) in self.chosen

    def __len__(self):
        return len(self.chosen)

    def keys(self, shown):
        """The keys chosen, in the order of `shown` -- the list -- those hidden by the filter after them."""
        shown = [tuple(k) for k in shown]
        visible = [k for k in shown if k in self.chosen]
        return visible + [k for k in self.chosen if k not in set(visible)]

    def hidden(self, shown):
        """How many of the variables chosen the filter hides (UI-010: «dont k masquée(s)»)."""
        shown = {tuple(k) for k in shown}
        return sum(1 for k in self.chosen if k not in shown)

    def copy_order(self, shown, everything):
        """The order «Copier les n commandes» puts the lines in (UI-009, D-15): the variables shown, in the order of the list, then those hidden, in the order of the whole list (`everything`, every key unfiltered)."""
        shown = [tuple(k) for k in shown]
        visible = [k for k in shown if k in self.chosen]
        seen = set(visible)
        rest = [tuple(k) for k in everything if tuple(k) in self.chosen and tuple(k) not in seen]
        rest += [k for k in self.chosen if k not in seen and k not in set(rest)]   # a key no longer listed at all, last
        return visible + rest

    def all_shown(self, shown):
        """Whether every variable shown is chosen: the header's box ticked."""
        shown = [tuple(k) for k in shown]
        return bool(shown) and all(k in self.chosen for k in shown)

    # -- the gestures --

    def click(self, key, shown, ctrl=False, shift=False, box=False):
        """A click on the variable `key` of the list `shown` (the keys in the order of the list). A click: it alone. Ctrl or its box: added or taken away, and the anchor. Shift: the range from the anchor in the order shown, replacing the choice -- added to it with Ctrl --, the anchor kept. In every case the last one clicked (`focus`)."""
        key = tuple(key)
        shown = [tuple(k) for k in shown]
        if self.single:
            self.chosen = {key: True}
            self.anchor = self.focus = key
            return
        if shift and self.anchor is not None and self.anchor in shown and key in shown:
            a, b = shown.index(self.anchor), shown.index(key)
            if not ctrl:
                self.chosen = {}
            for k in shown[min(a, b):max(a, b) + 1]:
                self.chosen[k] = True
        elif ctrl or box:
            if key in self.chosen:
                del self.chosen[key]
            else:
                self.chosen[key] = True
            self.anchor = key
        else:
            self.chosen = {key: True}
            self.anchor = key
        self.focus = key

    def set_all(self, shown, on):
        """The header's box: every variable shown taken, or -- unticked -- the whole choice let go (as the prototype does)."""
        if self.single:
            return
        if on:
            for k in shown:
                self.chosen[tuple(k)] = True
        else:
            self.chosen = {}

    def clear(self):
        """«Tout désélectionner»: nothing chosen; the card keeps the last one clicked."""
        self.chosen = {}

    def focus_on(self, key):
        """`key` chosen alone by the program -- `select_key`, a sibling's button --: as a click, without the list."""
        key = tuple(key) if key is not None else None
        self.chosen = {key: True} if key is not None else {}
        self.anchor = self.focus = key

    # -- the keyboard (the gesture of the mouse: arrows a click, Shift+arrow a Shift+click, Space the box, Ctrl+A every variable shown) --

    def step(self, shown, delta, shift=False, ctrl=False):
        """An arrow: the next variable (`delta` +1) or the previous (-1) after the last one clicked, as a click -- with Shift, as a Shift+click. Returns the key reached, None in an empty list."""
        shown = [tuple(k) for k in shown]
        if not shown:
            return None
        if self.focus in shown:
            index = max(0, min(len(shown) - 1, shown.index(self.focus) + delta))
        else:
            index = 0 if delta > 0 else len(shown) - 1
        key = shown[index]
        if shift and not self.single:
            anchor = self.anchor
            self.click(key, shown, ctrl=ctrl, shift=True)
            self.anchor = anchor if anchor is not None else key
        else:
            self.click(key, shown)
        return key

    def space(self, shown):
        """Space: the box of the last one clicked."""
        if self.focus is not None and self.focus in [tuple(k) for k in shown]:
            self.click(self.focus, shown, box=True)

    # -- one value while a field is linked (REQ-008) --

    def begin_single(self):
        """A field's choice begins: the choice of before kept aside, one value at a time."""
        if not self.single:
            self._kept = (dict(self.chosen), self.anchor, self.focus)
            self.single = True
            self.chosen = {self.focus: True} if self.focus is not None else {}

    def end_single(self):
        """The field's choice ended (imported or given up): the choice of before back, the boxes with it."""
        if self.single:
            self.single = False
            if self._kept is not None:
                self.chosen, self.anchor, self.focus = self._kept
            self._kept = None
