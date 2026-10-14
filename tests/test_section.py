"""A position's section, read once (v0.94, docs/domain/positions.md §7): a position's `section_type` and `dimension` -- Woodcore's Positions tab's since v0.114, Positionen.xlsx's until then -- through domains/section.py and nothing else.

The engineer's rules, and what is held of each:

* **the type says how the dimension is read** -- `rec` b/h, `cir` d, `pla` t, `clt` its layers, and an SZS C5 code a steel designation's size, loosely, by its count of numbers; a timber dimension in mm, cm or m, stored in mm, a steel one in mm;
* **an empty type gives no section**, the dimension staying descriptive text -- except «b/h», read as `rec` with a warning naming the position, which is what a workbook written before the column existed carries;
* **an unknown type, or a dimension that does not fit its type, stops the export** naming the row and the cell;
* **one reader**: what the export writes into `data/positions/<id>.json` is what the window's summaries, a schema element's b and h and the report read -- a record exported before v0.94, with no `section`, is read by the same reader's deduction.
"""

import validation
from domains import section
from norms import szs_c5


def _refused(*args):
    try:
        section.parse(*args, where="Positions Element, S009")
    except validation.ValidationError as exc:
        return str(exc)
    raise AssertionError(f"section.parse{args!r} should have refused")


# --- the reader ---------------------------------------------------------------------

def test_every_type_reads_its_dimension():
    assert section.parse("rec", "100/200", "mm") == {"type": "rec", "kind": "timber", "text": "100/200 mm", "b": 100, "h": 200}
    assert section.parse("rec", "10 x 20", "cm") == {"type": "rec", "kind": "timber", "text": "10/20 cm", "b": 100, "h": 200}
    assert section.parse("REC", "0.1×0.2", "m")["b"] == 100, "a type is read whatever its case, a unit converted to mm"
    assert section.parse("rec", "100,5/200", "")["text"] == "100.5/200 mm", "an empty unit is mm; a decimal comma reads as a point"
    assert section.parse("cir", "200", "mm") == {"type": "cir", "kind": "timber", "text": "Ø 200 mm", "d": 200}
    assert section.parse("cir", "Ø 20", "cm")["d"] == 200
    assert section.parse("pla", "22", "mm") == {"type": "pla", "kind": "timber", "text": "22 mm", "t": 22}
    assert section.parse("clt", "20/30/20/30/20", "mm") == {"type": "clt", "kind": "timber", "text": "20/30/20/30/20 mm (120 mm)",
                                                          "layers": [20, 30, 20, 30, 20], "t": 120}
    assert section.parse("ROR", "101.6x10", "mm") == {"type": "ROR", "kind": "steel", "text": "ROR 101.6×10", "dims": [101.6, 10]}
    assert section.parse("ipe", "IPE 200", "") == {"type": "IPE", "kind": "steel", "text": "IPE 200", "dims": [200]}, "the code typed before the size is the designation's own form"
    assert section.parse("RRW", "200x100x8", "mm")["text"] == "RRW 200×100×8"
    assert section.parse("L", "100x10", "")["dims"] == [100, 10] and section.parse("L", "150x100x10", "")["dims"] == [150, 100, 10]
    assert section.parse("FLA", "100x10", "")["text"] == "FLA 100×10"


def test_an_empty_type_reads_b_over_h_as_rec_and_says_so_and_nothing_else():
    deduced = section.parse("", "100/200", "mm")
    assert deduced == {"type": "rec", "kind": "timber", "text": "100/200 mm", "b": 100, "h": 200, "deduced": True}
    # the engineer's own S002 before its type was written: a steel tube typed as «101.6/10» -- read as a rectangle, which the warning is there to catch
    assert section.parse(None, "101.6/10", "mm")["deduced"]
    for text, units in (("180", "mm"), ("", ""), ("100/200/300", "mm"), ("100/200", "in"), ("0/200", "mm"), ("abc", ""), (None, None)):
        assert section.parse("", text, units) is None, (text, units)


def test_a_type_or_a_dimension_that_does_not_fit_stops_naming_the_row_and_the_cell():
    message = _refused("XYZ", "100", "mm")
    assert "S009" in message and "section type" in message and "rec" in message and "ROR" in message, message
    assert "needs a dimension" in _refused("cir", "", "mm")
    for args, form in ((("rec", "180", "mm"), "b/h"), (("cir", "200/100", "mm"), "number"), (("pla", "t", "mm"), "thickness"),
                       (("clt", "120", "mm"), "layers"), (("ROR", "101.6", "mm"), "2 numbers"), (("HEA", "200x10", ""), "1 number"),
                       (("L", "100", ""), "2 or 3"), (("rec", "0/200", "mm"), "above 0")):
        message = _refused(*args)
        assert "S009" in message and "dimension" in message and form in message, (args, message)
    assert "units" in _refused("rec", "100/200", "in") and "units" in _refused("IPE", "200", "cm"), "a steel designation is in mm"


# --- one list of codes ----------------------------------------------------------------

def test_the_codes_are_the_timber_four_and_szs_c5_s():
    assert section.CODES == ("rec", "cir", "pla", "clt") + szs_c5.codes() + ("USR",), "and a free profile last (issue #50)"
    assert set(section.STEEL_NUMBERS) == set(szs_c5.codes()), "every SZS C5 family has its count of numbers, and no other"
    assert section.kind_of("USR") == "user" and section.name("USR", "fr") == "Profilé libre"
    assert [t["code"] for t in section.TYPES] == list(section.CODES)
    for entry in section.TYPES:
        assert all(entry[lang] for lang in ("de", "fr", "en")) and entry["kind"] == section.kind_of(entry["code"])
    assert section.name("ROR", "fr") == "Tubes ronds en acier sans soudure ou soudés"
    assert section.code_of("") == "" and section.code_of("hea") == "HEA" and section.code_of("Holz") is None


# --- what reads a record ------------------------------------------------------------

def test_a_record_is_read_by_its_section_and_an_older_one_by_the_same_deduction():
    new = {"section_type": "cir", "dimension": "200", "units": "mm", "section": section.parse("cir", "200", "mm")}
    steel = {"section": section.parse("ROR", "101.6x10", "mm"), "dimension": "101.6x10", "units": "mm"}
    old = {"dimension": "10/20", "units": "cm"}
    assert section.display(new) == "Ø 200 mm" and section.sides(new) == (200, 200)
    assert section.display(steel) == "ROR 101.6×10" and section.sides(steel) is None, "a steel profile gives no b and h"
    assert section.of_record(old)["deduced"] and section.sides(old) == (100, 200) and section.display(old) == "10/20 cm"
    assert section.display({"section": None, "dimension": "180", "units": "mm"}) == "180 mm"
    assert section.display({"dimension": "", "units": "mm"}) == "" and section.display(None) == "", "a unit is never printed alone"
    assert section.sides({"section": section.parse("clt", "20/30/20", "mm")}) == (70, 70)
    from domains import connector
    assert connector.position_dimension(new) == "Ø 200 mm", "the window's summaries print the section's text"


# --- the export ---------------------------------------------------------------------

def _row(**fields):
    row = {"position": "T001", "type": "Träger", "material": "Fichte", "strength_class": "C24", "section_type": "rec",
           "dimension": "100/200", "units": "mm", "moisture_class": 2, "description": ""}
    row.update(fields)
    return row


def test_the_export_writes_the_section_into_a_1_4_record():
    import export_all
    rows = [_row(), _row(position="S002", type="Stütze", material="Stahl", strength_class="S355", section_type="ROR", dimension="101.6x10", moisture_class=None),
            _row(position="D001", type="Decke", section_type="", dimension="180")]
    positions, notes = export_all._positions(rows)
    records = {p["position"]: p for p in positions}
    assert not notes, notes
    assert records["T001"]["schema_version"] == "1.4" and records["T001"]["section"]["b"] == 100
    assert records["S002"]["section"] == {"type": "ROR", "kind": "steel", "text": "ROR 101.6×10", "dims": [101.6, 10]}
    assert records["D001"]["section"] is None and records["D001"]["dimension"] == "180"
    assert records["S002"]["section_type"] == "ROR"
    for record in records.values():
        validation.validate_structure(record, "position")
        validation.validate_positions_business(record)


def test_a_position_without_a_section_type_still_exports_and_a_deduced_rec_is_said():
    import export_all
    (record,), notes = export_all._positions([_row(section_type="")])
    assert record["section"]["deduced"] and record["section_type"] == ""
    assert [n.code for n in notes] == ["position_deduced"] and "T001" in notes[0] and "rec" in notes[0], notes


def test_a_section_that_does_not_read_is_a_warning_and_exported_without_a_section():
    """It stopped the export until v0.114; Woodcore's Positions tab is the one source of positions since, and a value it holds is never a blocking error -- the position is written with `section: null` and the export says why, naming it (the engineer, 06.10.2026)."""
    import export_all
    for fields, words in (({"section_type": "Holz"}, "section type"), ({"section_type": "ROR", "dimension": "101.6"}, "dimension")):
        (record,), notes = export_all._positions([_row(**fields)])
        assert record["section"] is None, fields
        assert [n.code for n in notes] == ["position_section"] and "T001" in notes[0] and words in notes[0], notes


def test_a_section_the_list_does_not_have_is_refused_by_the_business_rules():
    record = {"position": "T001", "type": "Träger", "moisture_class": None, "section": {"type": "XYZ", "kind": "steel", "text": "XYZ 1"}}
    try:
        validation.validate_positions_business(record)
    except validation.ValidationError as exc:
        assert "XYZ" in str(exc)
    else:
        raise AssertionError("a section of a type the list does not have must be refused")


# --- the fields a dimension is typed in (v0.117) ---------------------------------------------------------

def test_a_type_has_the_fields_its_dimension_is_typed_in_and_the_text_is_read_and_written_back_from_them():
    """v0.117, the engineer: «lorsque le type de section est donné, une section "Dimension" avec des textbox différentes: "rec" => largeur, hauteur; "plaque" => épaisseur». The reading is `parse`'s own expressions, so what a box can hold is what the export reads."""
    assert section.dimension_fields("rec") == ("b", "h") and section.dimension_fields("cir") == ("d",) and section.dimension_fields("pla") == ("t",)
    for none in ("clt", "", None, "XYZ"):
        assert section.dimension_fields(none) == (), none
    assert section.split_dimension("rec", "100/200") == ("100", "200")
    assert section.split_dimension("rec", " 100 x 200 ") == ("100", "200") and section.split_dimension("rec", "100×200") == ("100", "200")
    assert section.split_dimension("rec", "100,5/200") == ("100,5", "200"), "a decimal comma is read as typed"
    assert section.split_dimension("cir", "Ø 200") == ("200",) and section.split_dimension("pla", "22") == ("22",)
    for text in ("100", "100/", "/200", "Pavillon", "", "100/200/300", "20/30/20"):
        assert section.split_dimension("rec", text) is None, text
    assert section.split_dimension("pla", "100/200") is None and section.split_dimension("", "100/200") is None
    assert section.join_dimension("rec", ("100", "200")) == "100/200" and section.join_dimension("rec", (" 100,5 ", "200")) == "100,5/200"
    assert section.join_dimension("pla", ("22",)) == "22" and section.join_dimension("cir", ("200",)) == "200"
    assert section.join_dimension("rec", ("", "")) == "" and section.join_dimension("rec", ("100", "")) == "100/", "nothing typed is nothing; half typed keeps its place"
    try:
        section.join_dimension("rec", ("100",))
    except ValueError:
        pass
    else:
        raise AssertionError("one value for two fields was accepted")
    # what the boxes write is what the export reads
    for code, values, expected in (("rec", ("100", "200"), {"b": 100, "h": 200}), ("cir", ("200",), {"d": 200}), ("pla", ("22",), {"t": 22}), ("rec", ("12,5", "30"), {"b": 12.5, "h": 30})):
        parsed = section.parse(code, section.join_dimension(code, values))
        assert all(parsed[key] == value for key, value in expected.items()), (code, values, parsed)


# --- every type has its fields (issue #9) ----------------------------------------------------------------

def test_every_type_has_its_forms_and_the_steel_counts_and_wording_are_read_off_them():
    """Issue #9: «choisir un type de section, puis saisir ses dimensions dans des champs séparés. Tous les types de section existants sont repris». FORMS is the one table: STEEL_NUMBERS and STEEL_FORMS are read off it, so the count `parse` accepts and the fields a box offers cannot drift apart. The steel forms are SZS C5's (pp. 47-78 of the 2018 tables): HD «260×114», ROR D·t, L a·t / a·b·t, RRW h·b·t."""
    assert set(section.FORMS) | set(section.LAYERED) == set(section.CODES), "every type has its fields, and no other"
    for code, forms in section.FORMS.items():
        counts = [len(form) for form in forms]
        assert len(set(counts)) == len(counts), f"{code}: two forms of one count could not be told apart"
        if code not in section.TIMBER_CODES + (section.USER_CODE,):
            assert section.STEEL_NUMBERS[code] == (min(counts), max(counts)), code
    # IPE 750 x 134 ... is written h x m, as SZS C5 writes it (p. 30, issue #50)
    assert section.STEEL_NUMBERS["ROR"] == (2, 2) and section.STEEL_NUMBERS["BLE"] == (1, 3) and section.STEEL_NUMBERS["IPE"] == (1, 2)
    assert section.STEEL_FORMS["ROR"] == "D×t" and section.STEEL_FORMS["L"] == "a×t or a×b×t" and section.STEEL_FORMS["BLE"] == "t, b×t or b×l×t"
    assert section.STEEL_FORMS["IPE"] == "h or h×m" and section.STEEL_FORMS["HEA"] == "h", "a beam's one number reads «h», as it always did"
    assert section.dimension_fields("IPE") == ("size",) and section.dimension_fields("RRW") == ("h", "b", "t")
    assert section.form_of("L", 3) == ("a", "b", "t") and section.form_of("L", 1) is None
    assert section.is_layered("clt") and not section.is_layered("rec") and section.dimension_forms("clt") == ()
    for code in ("T4", "C4", "C1", "Kasten"):
        assert section.code_of(code) is None, "no SZS C4 or C1 assembly is a type"


def test_each_form_reads_back_what_it_writes_and_the_export_reads_it():
    """join ∘ split is the identity on what the boxes write, for every form of every type, and `parse` -- the export's reader -- reads it as the same numbers."""
    for code, forms in section.FORMS.items():
        if code == section.USER_CODE:
            continue   # its one field is an id, below
        for form in forms:
            values = tuple(str(10 + 5 * i) for i in range(len(form)))
            text = section.join_dimension(code, values)
            assert section.split_dimension(code, text) == values, (code, form, text)
            parsed = section.parse(code, text, "mm")
            if code not in section.TIMBER_CODES:
                assert parsed["dims"] == [10 + 5 * i for i in range(len(form))], (code, parsed)
    assert section.join_dimension("ROR", ("101.6", "10")) == "101.6x10", "the x the designations are typed with"
    # a free profile (issue #50): its dimension is its id, read for its form only, the file being the export's to find
    assert section.split_dimension("USR", section.join_dimension("USR", ("PR-01",))) == ("PR-01",)
    assert section.parse("USR", "PR-01", "") == {"type": "USR", "kind": "user", "text": "USR PR-01", "id": "PR-01"}
    assert section.split_dimension("USR", "PR 01") is None
    assert section.split_dimension("ROR", "ROR 101.6×10") == ("101.6", "10"), "the designation typed whole"
    assert section.split_dimension("HD", "260x114") == ("260", "114") and section.split_dimension("HD", "260") == ("260",)
    assert section.split_dimension("ROR", "101.6") is None, "a count of no form stays the line of text it is"
    # a T of two numbers is read by the export, which never refused it, and has no form: it stays text
    assert section.parse("T", "50x6", "")["dims"] == [50, 6] and section.split_dimension("T", "50x6") is None
    # a CLT panel: one field a layer, as many as it has
    assert section.split_dimension("clt", "20/30/20") == ("20", "30", "20")
    assert section.join_dimension("clt", ("40", "20", "40", "20", "40")) == "40/20/40/20/40"
    assert section.parse("clt", section.join_dimension("clt", ("40", "20", "40")), "mm")["t"] == 100
    try:
        section.join_dimension("ROR", ("101.6",))
    except ValueError as exc:
        assert "2" in str(exc)
    else:
        raise AssertionError("one value for ROR's two fields was accepted")


def test_a_section_s_area_is_known_for_a_rectangle_and_a_circle_only():
    """The volume of a position (the plan's quantities, issue #9) is its length times this area: a plate or a CLT panel has a thickness and no section area, and a steel profile's area is in SZS C5 and in no file of this program."""
    def record(code, dimension, units="mm"):
        return {"section": section.parse(code, dimension, units)}
    assert section.area_mm2(record("rec", "100/200")) == 20000
    assert abs(section.area_mm2(record("cir", "200")) - 31415.9265) < 1e-3
    assert section.area_mm2(record("rec", "10/20", "cm")) == 20000, "in mm², whatever the row's units"
    for code, dimension in (("pla", "22"), ("clt", "20/30/20"), ("IPE", "200")):
        assert section.area_mm2(record(code, dimension)) is None, code
    assert section.area_mm2(None) is None and section.area_mm2({}) is None
