"""The fields a position's section is typed in, the one widget the Positions tab and the position plan's pane share (calc/tools/section_fields.py; issue #9, REQ-008).

What is held: every type of domains/section.py has its fields, a type with several forms a form to choose, a CLT panel a field a layer that may be added and taken away; the fields read the text and write it back, and say so only when typed in; a text none of the type's forms reads is shown in no field.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import sys

from conftest import ROOT, Skip

from domains import section


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def test_every_type_has_its_fields_and_they_write_back_what_they_read():
    _qt()
    import section_fields
    fields = section_fields.DimensionFields("en")
    edited = []
    fields.edited.connect(lambda: edited.append(True))
    for code in section.CODES:
        assert fields.set_code(code, "") is True, code
        expected = section.dimension_forms(code)[0] if section.dimension_forms(code) else ("layer",) * section_fields.FIRST_LAYERS
        assert tuple(c.property("field") for c, _e in fields.edits) == expected, code
    assert not edited, "showing fields is no edit"
    # an unequal angle: its three-number form chosen by what the text holds, and written back as it was
    assert fields.set_code("L", "100x50x8") and fields.values() == ["100", "50", "8"] and fields.form_combo.count() == 2
    assert fields.text() == "100x50x8"
    fields.form_combo.setCurrentIndex(0)                     # a·t: the numbers that fit are kept
    assert [c.property("field") for c, _e in fields.edits] == ["a", "t"] and fields.values() == ["100", "50"] and edited
    # one field for a beam's size, captioned in the window's language
    assert fields.set_code("IPE", "IPE 200") and fields.values() == ["200"] and fields.edits[0][0].text() == "Size"
    # a CLT panel: a field a layer, as many as it has, one more and one less
    assert fields.set_code("clt", "40/20/40") and fields.values() == ["40", "20", "40"]
    fields.add_layer.click()
    fields.edits[-1][1].setText("20")
    assert fields.text() == "40/20/40/20"
    fields.remove_layer.click()
    assert fields.text() == "40/20/40" and [c.text() for c, _e in fields.edits] == ["Layer 1", "Layer 2", "Layer 3"]
    # what no form reads is shown in no field: the caller keeps it on its line
    assert fields.set_code("ROR", "101.6") is False and fields.edits == []
    assert fields.set_code("", "OSB") is False
