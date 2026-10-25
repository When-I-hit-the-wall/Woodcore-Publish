"""The cells of the table of layers and the way the keyboard goes through them (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, UI-001, T28, T47, T50, P08; issue #111).

One row a layer, its columns `COLUMNS`: its number, its material, its thickness, the spacing and the width of its pieces, g_k or a_k, its load in kN/m². **Which cells serve** a layer is its pose's (`used`): a spaced layer has a spacing and a width, a line that fills between pieces has the width it was given where it does not fill (`fill` false) -- the width it fills, computed, is shown in italics and not typed --, a load typed has no thickness. **Tab** goes from the material to the thickness, the spacing, the width, g/a, then the kN/m², skipping a cell that does not serve; after the last cell, to the material of the next line (`next_cell`, pure: tested without Qt). No Qt here, no word: the table's widgets are layer_table's.
"""

from domains import dead_load_layers

COLUMNS = ("number", "material", "thickness", "spacing", "width", "kind", "load")
# The cells Tab goes through, in its order (T50): the number is never one
CHAIN = COLUMNS[1:]


def fills(layers, row):
    """Whether the layer of `row` is a line that fills between pieces linked to it, its width computed (`fill`, the default)."""
    return dead_load_layers.fill_width(layers, row)[1]


def beside_pieces(layers, row):
    """Whether the layer of `row` shares its level with a spaced layer: what makes its width a width on 1 m."""
    level = next((lv for lv in dead_load_layers.levels(layers) if row in lv), [row])
    return any(layers[j].get("pose") == "spaced" for j in level if j != row)


def used(layers, row, column):
    """Whether the cell `column` of the layer of `row` serves its pose (T50): greyed and skipped where it does not."""
    layer = layers[row]
    pose = layer.get("pose")
    if column == "number":
        return False
    if column in ("material", "kind", "load"):
        return True
    if column == "thickness":
        return pose != "typed"
    if column == "spacing":
        return pose == "spaced"
    if column == "width":
        return pose == "spaced" or (pose != "typed" and beside_pieces(layers, row) and not layer.get("fill", True))
    return False


def next_cell(layers, row, column, forward=True):
    """(row, column) of the cell Tab (`forward`) or Shift+Tab goes to from `column` of `row`: the next cell of the chain that serves, else the material of the next line (the last cell of the line before); None past the last line or before the first."""
    order = list(CHAIN)
    at = order.index(column) if column in order else -1
    step = 1 if forward else -1
    r, i = row, at + step
    while 0 <= r < len(layers):
        while 0 <= i < len(order):
            if used(layers, r, order[i]):
                return r, order[i]
            i += step
        r += step
        i = 0 if forward else len(order) - 1
    return None
