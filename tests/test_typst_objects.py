"""The parametric objects of a document's .typ files (calc/typst_objects.py, the three document modes, work package 4.1).

What is held: the literal grammar -- every kind of value read and written back, a string's escapes, a float in its shortest form, a length, an array of one, an empty dictionary, and **content read to its own closing bracket** past a nested bracket, a string, a formula, a raw block and an escape; the canonical form of every one of the ten commands, written by hand and read back to the byte; the three states -- canonical, edited by hand, unreadable -- and the diff the warning shows; `write_object` changing the body and nothing else, in LF and in CRLF, refusing what it must; `insert_object` and `remove_object`; every operation of every editor's model giving a call that reads back as itself; ORDER held equal to lib/document.typ's own signatures; every object the templates carry being canonical; and a document still compiling after its objects were written.

**Every heading and every paragraph is an object too** (the rework of 01.10.2026): their states, their models, writing them from a string or a model, inserting and removing them, their short label, `untagged` and `tag_file` -- on a file of every construct (a call with a blank line in its arguments, a raw block, a block comment, an `#if` printing a heading, CRLF, a BOM, a last line with no line ending) and on the files of the example report, compiled before and after.

**No ψ**: the live-load table has six known columns and a ψ column is no known column.

Every file a check writes goes into this process's own temporary folder (conftest.tmpdir).
"""

import re
import shutil
import subprocess
from pathlib import Path

import conftest
from conftest import ROOT, Skip

import project
import structure
import typst_objects as to
from typst_objects import AUTO, Call, Content, Expr, Length

BS = chr(92)        # a backslash, spelt so that no editor or shell turns it into anything else
DOCUMENT_TYP = ROOT / "lib" / "document.typ"
SHEET_TYP = ROOT / "lib" / "sheet.typ"


def _roundtrip(call):
    """The canonical form of `call`, which must read back as `call` and write the same text again."""
    text = to.serialize(call)
    back = to.parse_call(text)
    assert back.same_as(Call(call.type, {n: call.args[n] for n in to.arguments_of(call)})), (text, back)
    assert to.serialize(back) == text
    return text


def _model_roundtrip(model):
    """A model's call written, read back, and given to a fresh model, which gives the same call again."""
    call = model.to_call()
    text = _roundtrip(call)
    again = to.model_for(to.parse_call(text)).to_call()
    assert again.same_as(call), (text, to.serialize(again))
    return text


def _file(*objects, before="#import \"/commands.typ\": *\n\n= Titel\n\nText.\n\n", after="\nMehr Text.\n"):
    """A section file holding `objects`, each (type, id, body)."""
    parts = [before]
    for kind, oid, body in objects:
        parts.append(f"// woodcore:object {kind} {oid}\n{body}\n// woodcore:/object {oid}\n")
    parts.append(after)
    return "".join(parts)


# --- the commands' signatures ---------------------------------------------------------------------

def test_order_and_defaults_are_lib_documents_own_signatures():
    found = to.signatures_in(DOCUMENT_TYP.read_text(encoding="utf-8"))
    assert set(found) == set(to.CALL_TYPES), f"lib/document.typ defines {sorted(found)}"
    for kind, params in found.items():
        assert tuple(params) == to.ORDER[kind], f"{kind}: lib/document.typ's order is {tuple(params)}, ORDER says {to.ORDER[kind]}"
        for name, default in params.items():
            assert to.same(default, to.DEFAULTS[kind][name]), f"{kind}.{name}: lib says {to.inline(default)}, DEFAULTS {to.inline(to.DEFAULTS[kind][name])}"


def test_order_and_defaults_of_the_sheet_objects_are_lib_sheets_own_signatures():
    """The six objects of an export sheet (v0.114) as lib/sheet.typ declares them -- `sheet-page` being the show rule `sheet`, its document left out."""
    found = to.signatures_in(SHEET_TYP.read_text(encoding="utf-8"))
    assert set(found) == set(to.SHEET_TYPES), f"lib/sheet.typ defines {sorted(found)}"
    for kind, params in found.items():
        assert tuple(params) == to.ORDER[kind], f"{kind}: lib/sheet.typ's order is {tuple(params)}, ORDER says {to.ORDER[kind]}"
        for name, default in params.items():
            assert to.same(default, to.DEFAULTS[kind][name]), f"{kind}.{name}: lib says {to.inline(default)}, DEFAULTS {to.inline(to.DEFAULTS[kind][name])}"


def test_the_object_types_are_the_tag_readers_own():
    assert to.OBJECT_TYPES == structure.OBJECT_TYPES


def test_the_known_columns_are_lib_documents_own():
    text = DOCUMENT_TYP.read_text(encoding="utf-8")
    for kind, name in (("live-load-table", "live-load-columns"), ("dead-load-table", "dead-load-columns")):
        found = re.search(rf"#let {name} = \(([^)]*)\)", text)
        assert found, f"lib/document.typ has no {name}"
        ids = tuple(re.findall(r'"([^"]+)"', found.group(1)))
        assert ids == to.KNOWN_COLUMNS[kind], f"{name} is {ids}, KNOWN_COLUMNS says {to.KNOWN_COLUMNS[kind]}"
    for column, unit in to.KNOWN_UNITS.items():
        assert re.search(rf"\b{column}: \([^)]*unit: \"{unit}\"", text), f"lib/document.typ gives {column} another unit than {unit}"
    filled = re.search(r'#let live-load-filled = \(([^)]*)\)', text)
    assert filled and tuple(re.findall(r'"([^"]+)"', filled.group(1))) == to.LIVE_LOAD_FILLED == ("q_k", "Q_k")
    assert "psi" not in text.split("#let live-load-known")[1].split("/// **The live loads")[0] and "live-load-psi" not in text, "lib/document.typ knows a ψ column of the live loads"
    assert not hasattr(to, "PSI_COLUMNS") and not hasattr(to.LiveLoadTableModel, "psi_shown") and not hasattr(to.LiveLoadTableModel, "set_psi_shown")


# --- the literals -----------------------------------------------------------------------------------

LITERALS = [
    # (as written, the value, the canonical form)
    ('"Büro"', "Büro", '"Büro"'),
    ('"a' + BS + BS + 'b' + BS + '"c' + BS + 'nd"', "a" + BS + 'b"c\nd', '"a' + BS + BS + 'b' + BS + '"c' + BS + 'nd"'),
    ('"' + BS + 'u{41}' + BS + 't"', "A\t", '"A\t"'),
    ('"' + BS + 'q"', BS + "q", '"' + BS + BS + 'q"'),           # an escape Typst does not know is kept, backslash and all
    ("42", 42, "42"),
    ("-5", -5, "-5"),
    ("+3", 3, "3"),
    ("0x1F", 31, "31"),
    ("1.5", 1.5, "1.5"),
    ("2.0", 2.0, "2.0"),
    ("1e3", 1000.0, "1000.0"),
    (".5", 0.5, "0.5"),
    ("1e-07", 1e-7, "1e-7"),
    ("true", True, "true"),
    ("false", False, "false"),
    ("none", None, "none"),
    ("auto", AUTO, "auto"),
    ("80%", Length(80, "%"), "80%"),
    ("12pt", Length(12, "pt"), "12pt"),
    ("-2.5cm", Length(-2.5, "cm"), "-2.5cm"),
    ("1.0em", Length(1.0, "em"), "1.0em"),
    ("90deg", Length(90, "deg"), "90deg"),
    ("()", [], "()"),
    ("(:)", {}, "(:)"),
    ("( : )", {}, "(:)"),
    ('("x",)', ["x"], '("x",)'),
    ('("x")', "x", '"x"'),                                        # a value in parentheses is the value
    ("(1, 2, 3,)", [1, 2, 3], "(1, 2, 3)"),
    ('(a: 1, "b c": [x], only-checked: true)', {"a": 1, "b c": Content("x"), "only-checked": True}, '(a: 1, "b c": [x], only-checked: true)'),
    ('("none": 1)', {"none": 1}, '("none": 1)'),                 # a keyword is no bare key
    ("((id: \"a\"), (id: \"b\"))", [{"id": "a"}, {"id": "b"}], '((id: "a"), (id: "b"))'),
    ("[]", Content(""), "[]"),
    ("50% + 1cm", Expr("50% + 1cm"), "50% + 1cm"),
    ("calc.round(x, digits: 1)", Expr("calc.round(x, digits: 1)"), "calc.round(x, digits: 1)"),
    ("(5 - 3)", Expr("(5 - 3)"), "(5 - 3)"),
    ("my-rows", Expr("my-rows"), "my-rows"),
]


def test_every_literal_reads_and_writes_back():
    for written, value, canonical in LITERALS:
        found = to.parse_value(written)
        assert to.same(found, value), f"{written!r} read as {found!r}, expected {value!r}"
        assert to.inline(found) == canonical, f"{written!r} written as {to.inline(found)!r}, expected {canonical!r}"
        assert to.same(to.parse_value(canonical), value), f"{canonical!r} does not read back as {value!r}"


CONTENT = [
    "#doc-value(\"g_k\", domain: (\"dead-load\", \"D1\"))",
    "$q_k$ [kN/m²]",
    "Fassade [außen [Nord]]",
    "a " + BS + "] b",
    "`raw ]` x",
    "```typ #f(]```",
    "#\"]\"",
    "$[0, 1)$",
    "#val(\"q_k\", domain: (\"live-load\", \"A1\"), type: \"val\", level: 1)",
    "see https://www.sia.ch/[x] now",
    "Zeile 1\nZeile 2",
    "/* ] */ x",
    "#{ let x = \"]\"; x }",
    "",
]


def test_content_is_read_to_its_own_closing_bracket():
    for markup in CONTENT:
        for written in ("[" + markup + "]", "(a: [" + markup + "], b: 1)"):
            found = to.parse_value(written)
            cell = found if isinstance(found, Content) else found["a"]
            assert cell == Content(markup), f"{written!r} read as {cell!r}"
            if isinstance(found, dict):
                assert found["b"] == 1
        call = Call("doc-field", {"label": Content(markup), "value": 3})
        _roundtrip(call)


def test_markup_that_does_not_close_where_it_ends_is_refused():
    for markup in ("a // b", "a ] b", "x " + BS, "[x", "$x", "`x"):
        try:
            Content(markup)
        except ValueError:
            continue
        raise AssertionError(f"[{markup}] was taken for one content block")
    for written in ('"abc', "(1, 2", "[x", "(a: 1, 2)", "(1, a: 2)", '(a: 1, a: 2)'):
        try:
            to.parse_value(written)
        except to.ParseError:
            continue
        raise AssertionError(f"{written!r} was read")


def test_a_float_is_written_in_its_shortest_form():
    for value, written in ((0.1, "0.1"), (7.5, "7.5"), (2.0, "2.0"), (1e-7, "1e-7"), (1e16, "1e16"), (-0.0, "-0.0"), (1 / 3, repr(1 / 3))):
        assert to.inline(value) == written, (value, to.inline(value))
        assert to.same(to.parse_value(written), value)
    for bad in (float("inf"), float("nan")):
        try:
            to.inline(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad} was written")


def test_same_tells_what_the_canonical_form_tells_apart():
    assert to.same([1, 2], (1, 2))
    assert not to.same(1, 1.0)
    assert not to.same(True, 1)
    assert not to.same({"a": 1, "b": 2}, {"b": 2, "a": 1})
    assert not to.same(Length(12, "pt"), Length(12.0, "pt"))
    assert to.same(AUTO, to.parse_value("auto"))


# --- the canonical form of every command -------------------------------------------------------------

CANONICAL = {
    "doc-table": """#doc-table(
  columns: (
    (id: "part", title: [Bauteil]),
    (id: "years", title: [Nutzungsdauer], unit: "Jahre", kind: "number"),
    (id: "remark", title: [Bemerkung], kind: "wide"),
  ),
  hidden: ("remark",),
  rows: (
    (part: [Tragwerk], years: 50, remark: [SIA 260, Ziffer 2.3.2]),
    (part: [Fassade [außen]], years: 25.5),
  ),
  caption: [Geplante Nutzungsdauer],
  notes: (
    [Erste Zeile.],
    [Zweite Zeile.],
  ),
  header: false,
)""",
    "live-load-table": """#live-load-table(
  columns: (
    (id: "area", title: [Teilbereich]),
    (id: "use", title: [Nutzung]),
    (id: "category", title: [Kategorie]),
    (id: "q_k", title: [$q_k$ [kN/m²]]),
    (id: "Q_k", title: [$Q_k$ [kN]]),
  ),
  hidden: ("area",),
  rows: (
    (area: [], use: [Büro], category: "B", q_k: auto, Q_k: auto),
    (area: [], use: [Archiv], category: "E", q_k: 7.5, Q_k: 7),
  ),
)""",
    "dead-load-table": """#dead-load-table(
  hidden: ("zone",),
  rows: (
    (storey: [EG], buildup: [Unterlagsboden 80 mm], load: 1.6),
    (storey: [Dach], buildup: [Begrünung], load: [#doc-value("gk_ak_gew", domain: ("dead-load", "EL+AL-Dach mit Wasser"))]),
  ),
  caption: [Auflasten],
  notes: [Ohne das Eigengewicht der tragenden Decke.],
)""",
    "doc-field": """#doc-field(
  label: [Nutzungsdauer],
  value: 50,
  unit: "Jahre",
)""",
    "doc-checklist": """#doc-checklist(
  label: [Akzeptierte Risiken],
  options: (
    (id: "ground", label: [Baugrundrisiko], checked: true, text: [Die Kostenfolgen gelten als akzeptiertes Risiko.]),
    (id: "vandalism", label: [Vandalismus], checked: false),
  ),
  only-checked: true,
)""",
    "doc-choice": """#doc-choice(
  label: [Nutzungsdauer des Tragwerks (SIA 260, Ziffer 2.3.2)],
  options: (
    (id: "replaceable", label: [Austauschbares Bauteil: bis 25 Jahre]),
    (id: "normal", label: [Gebäude von normaler Bedeutung: 50 Jahre]),
  ),
  selected: "normal",
)""",
    "doc-image": """#doc-image(
  file: "Images/profil.png",
  caption: [Geologisches Profil],
  width: 40%,
  placeholder: [Auszug aus dem geotechnischen Bericht],
)""",
    "doc-plan": """#doc-plan(
  plan: "Pavillon",
  highlight: ("T001", "S001"),
  detail: true,
  zoom: 1.5,
  width: 60%,
  caption: none,
)""",
    "doc-fire-plan": """#doc-fire-plan(
  plan: "Treppenhaus",
  legend: false,
  width: 70%,
  caption: [Brandschutzplan Regelgeschoss],
)""",
    "doc-extract": """#doc-extract(
  excerpt: "CO1-My",
  width: 70%,
  caption: [Biegemomente unter CO1],
)""",
    "doc-annexes": """#doc-annexes(
  heading: 3,
)""",
    "doc-signatures": """#doc-signatures(
  rows: (
    (group: [Bauherrschaft], role: [Bauherrschaft]),
    (group: [Projektverfassende], role: [Ingenieur:in], name: [[…]], place: [Bern]),
  ),
  place-date: false,
)""",
    "show-norm-list": """#show-norm-list(
  keys: (
    "SIA 260",
    "SIA 261",
    "SIA 265",
    [Lärmschutz-Verordnung (LSV)],
  ),
  project: "references.bib",
)""",
}

# The width rule: an array of plain values that is none of the lists of entries is inline while its line fits, one element per line once it does not.
LONG_HIGHLIGHT = """#doc-plan(
  plan: "Pavillon",
  highlight: (
    "T001",
    "T002",
    "T003",
    "T004",
    "T005",
    "T006",
    "T007",
    "T008",
    "T009",
    "T010",
    "T011",
    "T012",
  ),
)"""


def test_every_command_has_a_canonical_form_read_back_to_the_byte():
    assert set(CANONICAL) == set(to.CALL_TYPES)
    for kind, text in list(CANONICAL.items()) + [("doc-plan", LONG_HIGHLIGHT)]:
        call = to.parse_call(text)
        assert call.type == kind
        assert to.serialize(call) == text, f"{kind}: written back as\n{to.serialize(call)}"
        _model_roundtrip(to.model_for(call))
        assert to.serialize(to.model_for(call).to_call()) == text, f"{kind}: the model does not give the call back"


def test_a_call_with_no_argument_and_the_defaults_of_every_type():
    assert to.serialize(Call("doc-image", {})) == "#doc-image()"
    assert to.parse_call("#doc-image()").args == {}
    # a list of entries is one per line however short, a list of ids inline while it fits, an empty one always inline
    assert to.serialize(Call("show-norm-list", {"keys": ["SIA 260"]})) == '#show-norm-list(\n  keys: (\n    "SIA 260",\n  ),\n)'
    assert to.serialize(Call("doc-table", {"hidden": ["a"], "notes": []})) == '#doc-table(\n  hidden: ("a",),\n  notes: (),\n)'
    for kind in to.CALL_TYPES:
        _roundtrip(to.default_call(kind))
        _model_roundtrip(to.model_for(to.default_call(kind)))


def test_an_argument_the_command_does_not_take_is_left_out():
    call = to.parse_call('#doc-field(label: [X], colour: "red")')
    assert call.unknown() == ["colour"]
    assert "colour" not in to.serialize(call)
    assert to.serialize(to.model_for(call).to_call()) == "#doc-field(\n  label: [X],\n)"


# --- the three states ----------------------------------------------------------------------------------

HAND_EDITED = [
    # a comment
    '#doc-field(\n  label: [Nutzungsdauer], // SIA 260\n  value: 50,\n  unit: "Jahre",\n)',
    # the arguments out of order
    '#doc-field(\n  value: 50,\n  label: [Nutzungsdauer],\n  unit: "Jahre",\n)',
    # on one line
    '#doc-field(label: [Nutzungsdauer], value: 50, unit: "Jahre")',
    # no trailing comma
    '#doc-field(\n  label: [Nutzungsdauer],\n  value: 50,\n  unit: "Jahre"\n)',
    # a blank line before the call
    '\n#doc-field(\n  label: [Nutzungsdauer],\n  value: 50,\n  unit: "Jahre",\n)',
    # a number written otherwise
    '#doc-field(\n  label: [Nutzungsdauer],\n  value: 5e1,\n  unit: "Jahre",\n)',
    # a row broken over two lines
    '#doc-signatures(\n  rows: (\n    (group: [Bauherrschaft],\n     role: [Bauherrschaft]),\n  ),\n)',
    # an array of dictionaries inline
    '#doc-choice(\n  options: ((id: "i", label: [BWK I]), (id: "ii", label: [BWK II])),\n  selected: "ii",\n)',
    # an argument the command does not take
    '#doc-field(\n  label: [X],\n  colour: "red",\n)',
    # a value in parentheses
    '#doc-plan(\n  zoom: (2),\n)',
]

UNREADABLE = [
    "",                                                       # no call
    "Nur Text.",                                              # no call either
    '#doc-field(label: [X]',                                  # never closed
    '#doc-field([X])',                                        # a positional argument
    '#doc-field(label: [X])[Y]',                              # a content block after the call
    '#doc-field(label: [X])\n#doc-field(label: [Y])',         # two calls
    '#doc-field(label: [X], label: [Y])',                     # an argument twice
    '#doc-choice(label: [X])',                                # another command than the tag names
    '#doc-field (label: [X])',                                # a call is no call with a space before its parenthesis
    '#doc-field(label: [X // ])',                             # a comment eats the closing bracket
    '#doc-field(..args)',                                     # a spread
]


def test_the_three_states():
    text = _file(("doc-field", "canonical", CANONICAL["doc-field"]))
    (found,) = to.objects(text)
    assert (found.type, found.id, found.state, found.diff()) == ("doc-field", "canonical", "canonical", "")
    for body in HAND_EDITED:
        (found,) = to.objects(_file((to.parse_call(body).type, "edited", body)))
        assert found.state == "hand_edited", f"{body!r} is {found.state}"
        assert found.call is not None and found.error is None
        diff = found.diff()
        assert diff.startswith("--- as written\n+++ as Woodcore writes it"), diff
        assert found.canonical == to.serialize(found.call)
    for body in UNREADABLE:
        (found,) = to.objects(_file(("doc-field", "broken", body)))
        assert found.state == "unreadable", f"{body!r} is {found.state}"
        assert found.call is None and found.error, found
        assert found.canonical == to.serialize(to.default_call("doc-field"))
        assert found.diff()


def test_a_parse_error_says_where():
    try:
        to.parse_call('#doc-table(\n  rows: (\n    (a: [x],\n  ),\n')
    except to.ParseError as exc:
        assert exc.line >= 1 and exc.column >= 1 and "never closed" in exc.reason, exc
    else:
        raise AssertionError("an unclosed call was read")
    try:
        to.parse_call("#doc-field(\n  label: [X],\n  [Y],\n)")
    except to.ParseError as exc:
        assert (exc.line, exc.column) == (3, 3) and "named arguments only" in exc.reason, exc
    else:
        raise AssertionError("a positional argument was read")


def test_objects_are_found_in_order_with_where_they_are():
    text = _file(("doc-field", "one", CANONICAL["doc-field"]), ("doc-choice", "two", CANONICAL["doc-choice"]))
    one, two = to.objects(text)
    assert (one.id, two.id) == ("one", "two")
    for found in (one, two):
        lines = text.splitlines(keepends=True)
        assert lines[found.start].startswith(f"// woodcore:object {found.type} {found.id}")
        assert lines[found.end].startswith(f"// woodcore:/object {found.id}")
        begin, finish = found.body_span
        assert text[begin:finish] == found.body == CANONICAL[found.type]
    assert to.find(text, "two") == two and to.find(text, "three") is None


def test_an_object_inside_a_shared_block_names_it():
    text = "Text.\n// woodcore:shared live-loads\n" + _file(("doc-field", "f", CANONICAL["doc-field"]), before="", after="") + "// woodcore:/shared live-loads\n"
    (found,) = to.objects(text)
    assert found.shared == "live-loads" and found.state == "canonical"


def test_a_file_whose_tags_cannot_be_read_is_read_and_not_rewritten():
    text = _file(("doc-field", "f", CANONICAL["doc-field"])) + "// woodcore:object doc-field g\n#doc-field()\n"
    found, problems = to.scan(text)
    assert [o.id for o in found] == ["f"] and problems
    for write in (lambda: to.write_object(text, "f", to.default_call("doc-field")),
                  lambda: to.insert_object(text, 0, "doc-field", "h"),
                  lambda: to.remove_object(text, "f")):
        try:
            write()
        except to.ObjectError as exc:
            assert exc.code == "tags", exc
        else:
            raise AssertionError("a file with a tag problem was rewritten")


# --- writing an object back -------------------------------------------------------------------------------

def _split_around(text, found):
    begin, finish = found.body_span
    return text[:begin], text[finish:]


def test_write_object_changes_the_body_and_nothing_else():
    text = _file(("doc-field", "a", CANONICAL["doc-field"]), ("doc-choice", "b", CANONICAL["doc-choice"]))
    target = to.find(text, "b")
    model = to.model_for(target.call)
    model.select("replaceable")
    new = to.write_object(text, "b", model.to_call())
    after = to.find(new, "b")
    assert after.state == "canonical" and after.call.args["selected"] == "replaceable"
    assert _split_around(new, after) == _split_around(text, target)
    assert to.write_object(new, "b", model.to_call()) == new     # a second write writes the same text
    assert to.find(new, "a").body == CANONICAL["doc-field"]


def test_write_object_keeps_a_crlf_file_crlf():
    lf = _file(("doc-table", "t", CANONICAL["doc-table"]), ("doc-field", "f", CANONICAL["doc-field"]))
    crlf = lf.replace("\n", "\r\n")
    found = to.find(crlf, "t")
    assert found.state == "canonical" and "\r\n" in found.body
    model = to.model_for(found.call)
    model.add_row(values={"part": "Dach", "years": 30})
    model.hide_column("years")
    new = to.write_object(crlf, "t", model.to_call())
    assert "\n" not in new.replace("\r\n", ""), "a line ending other than CRLF was written"
    assert _split_around(new, to.find(new, "t")) == _split_around(crlf, found)
    assert new.replace("\r\n", "\n") == to.write_object(lf, "t", model.to_call())
    assert to.find(new, "t").state == "canonical"


def test_a_file_with_mixed_line_endings_keeps_each_one():
    text = "Kopf\r\n" + _file(("doc-field", "f", CANONICAL["doc-field"]), before="", after="Fuss\n")
    new = to.write_object(text, "f", Call("doc-field", {"label": Content("Neu")}))
    assert new.startswith("Kopf\r\n// woodcore:object doc-field f\n#doc-field(\n  label: [Neu],\n)\n// woodcore:/object f\nFuss\n")


def test_an_object_with_no_body_is_given_one():
    text = "A\n// woodcore:object doc-image pic\n// woodcore:/object pic\nB\n"
    (found,) = to.objects(text)
    assert found.body == "" and found.state == "unreadable"
    new = to.write_object(text, "pic", to.default_call("doc-image"), force=True)
    assert new == "A\n// woodcore:object doc-image pic\n#doc-image()\n// woodcore:/object pic\nB\n"


def test_write_object_refuses_what_it_must():
    text = _file(("doc-field", "hand", HAND_EDITED[0]), ("doc-field", "broken", UNREADABLE[2]), ("doc-field", "fine", CANONICAL["doc-field"]))
    good = Call("doc-field", {"label": Content("X")})
    refusals = [
        ("hand_edited", lambda: to.write_object(text, "hand", good)),
        ("unreadable", lambda: to.write_object(text, "broken", good)),
        ("no_such_object", lambda: to.write_object(text, "nothing", good)),
        ("type_mismatch", lambda: to.write_object(text, "fine", Call("doc-choice", {}))),
        ("changed", lambda: to.write_object(text, "fine", good, expected="#doc-field()")),
        ("tag_in_body", lambda: to.write_object(text, "fine", Call("doc-field", {"label": Content("x\n// woodcore:/object fine\ny")}))),
        ("not_written", lambda: to.write_object(text, "fine", {"label": "x"})),
    ]
    for code, write in refusals:
        try:
            write()
        except to.ObjectError as exc:
            assert exc.code == code, f"{code}: refused as {exc.code}: {exc}"
            if code in ("hand_edited", "unreadable", "changed"):
                assert exc.object is not None and exc.object.id in ("hand", "broken", "fine")
        else:
            raise AssertionError(f"{code}: written")
    # the warning said, the engineer's version is overwritten -- a hand-edited one in Woodcore's form, an unreadable one by the defaults
    forced = to.write_object(text, "hand", to.find(text, "hand").call, force=True)
    assert to.find(forced, "hand").body == CANONICAL["doc-field"]
    forced = to.write_object(text, "broken", to.find(text, "broken").replacement(), force=True)
    assert to.find(forced, "broken").body == to.serialize(to.default_call("doc-field"))
    assert to.write_object(text, "fine", good, expected=CANONICAL["doc-field"].replace("\n", "\r\n"))


# --- inserting and removing -----------------------------------------------------------------------------

def test_insert_object_puts_its_three_parts_where_it_is_told():
    text = "#import \"/commands.typ\": *\n\n= Titel\n\nText."       # no line ending at the end
    new = to.insert_object(text, 4, "doc-field", "f", Call("doc-field", {"label": Content("A")}))
    assert new == text + "\n// woodcore:object doc-field f\n#doc-field(\n  label: [A],\n)\n// woodcore:/object f\n"
    first = to.insert_object(new, -1, "show-norm-list", "norms")
    assert first.startswith("// woodcore:object show-norm-list norms\n#show-norm-list(\n  keys: (),\n)\n// woodcore:/object norms\n#import")
    middle = to.insert_object(first, 7, "doc-table", "t")
    assert [(o.id, o.state) for o in to.objects(middle)] == [("norms", "canonical"), ("t", "canonical"), ("f", "canonical")]
    crlf = to.insert_object(text.replace("\n", "\r\n"), 2, "doc-image", "pic")
    assert "\r\n// woodcore:object doc-image pic\r\n#doc-image()\r\n// woodcore:/object pic\r\n" in crlf
    # and taken out again, the file is what it was
    assert to.remove_object(to.remove_object(middle, "t"), "norms") == new
    assert to.remove_object(crlf, "pic") == text.replace("\n", "\r\n")


def test_insert_object_refuses_what_it_must():
    text = _file(("doc-field", "f", CANONICAL["doc-field"])) + "// woodcore:structure -- x\n#include \"a.typ\"\n// woodcore:/structure\n"
    start = to.find(text, "f").start
    refusals = [
        ("id_exists", lambda: to.insert_object(text, 0, "doc-field", "f")),
        ("bad_id", lambda: to.insert_object(text, 0, "doc-field", "Bad_Id")),
        ("bad_type", lambda: to.insert_object(text, 0, "doc-thing", "x")),
        ("type_mismatch", lambda: to.insert_object(text, 0, "doc-field", "x", Call("doc-choice", {}))),
        ("inside_block", lambda: to.insert_object(text, start, "doc-field", "x")),
        ("inside_block", lambda: to.insert_object(text, start + 3, "doc-field", "x")),
        ("inside_block", lambda: to.insert_object(text, len(text.splitlines()) - 2, "doc-field", "x")),
        ("bad_line", lambda: to.insert_object(text, 999, "doc-field", "x")),
        ("bad_line", lambda: to.insert_object(text, -2, "doc-field", "x")),
    ]
    for code, write in refusals:
        try:
            write()
        except to.ObjectError as exc:
            assert exc.code == code, f"{code}: refused as {exc.code}: {exc}"
        else:
            raise AssertionError(f"{code}: inserted")
    end = to.find(text, "f").end
    assert to.find(to.insert_object(text, end, "doc-field", "g"), "g").state == "canonical"   # right after an object's closing tag is outside it


def test_free_id():
    text = _file(("doc-table", "table", CANONICAL["doc-table"]), ("doc-table", "table-2", CANONICAL["doc-table"]))
    assert to.free_id(text, "table") == "table-3"
    assert to.free_id(text, "live-loads") == "live-loads"


# --- the editors' models --------------------------------------------------------------------------

def test_a_table_model_edits_rows_columns_and_cells():
    model = to.model_for(to.parse_call(CANONICAL["doc-table"]))
    assert [c.id for c in model.columns] == ["part", "years", "remark"]
    assert model.hidden == ["remark"] and model.row_count == 2
    steps = [
        lambda: model.add_row(values={"part": "Keller", "years": 80}),
        lambda: model.add_row(0, {"remark": "Oben *fett*"}),
        lambda: model.move_row(0, -1),
        lambda: model.remove_row(1),
        lambda: model.add_column("material", title="Material", index=1),
        lambda: model.set_cell(0, "material", "Holz [BSH]"),
        lambda: model.set_cell(1, "material", Content("$f_(m,k)$")),
        lambda: model.set_cell(2, "years", 12.5),
        lambda: model.set_cell(2, "remark", None),
        lambda: model.clear_cell(2, "remark"),
        lambda: model.move_column("material", 0),
        lambda: model.set_column("years", unit="a", kind="text"),
        lambda: model.set_column("years", unit=None),
        lambda: model.hide_column("material"),
        lambda: model.show_column("remark"),
        lambda: model.remove_column("years"),
        lambda: model.set_caption("Neu"),
        lambda: model.set_notes(["Eins", "Zwei"]),
        lambda: model.set_header(True),
    ]
    for step in steps:
        step()
        _model_roundtrip(model)
    assert [c.id for c in model.columns] == ["material", "part", "remark"]
    assert model.hidden == ["material"]
    rows = model.rows
    assert rows[0] == {"material": Content("Holz [BSH]"), "part": Content("Tragwerk"), "remark": Content("SIA 260, Ziffer 2.3.2")}
    assert all("years" not in r for r in rows)
    assert model.cell(1, "part") == Content("Keller") and model.cell(2, "remark") is None
    text = model.serialize()
    assert '(part: [Tragwerk], material: [Holz [BSH]], remark: [SIA 260, Ziffer 2.3.2]),' in text   # a new cell took its column's place when it was set, and keeps it
    assert "header: true," in text        # present in the call, kept although it is the default now


def test_a_table_model_refuses_what_the_command_would():
    model = to.model_for(to.parse_call(CANONICAL["doc-table"]))
    refusals = [
        ("id_exists", lambda: model.add_column("part", title="X")),
        ("bad_id", lambda: model.add_column("1x", title="X")),
        ("bad_id", lambda: model.add_column("none", title="X")),
        ("no_title", lambda: model.add_column("zone")),
        ("no_column", lambda: model.set_cell(0, "nothing", "x")),
        ("no_auto", lambda: model.set_cell(0, "part", AUTO)),
        ("bad_value", lambda: model.set_cell(0, "part", "unbalanced ]")),
        ("bad_value", lambda: model.set_cell(0, "part", True)),
        ("bad_index", lambda: model.remove_row(7)),
        ("bad_value", lambda: model.set_column("part", kind="huge")),
    ]
    for code, step in refusals:
        try:
            step()
        except to.ModelError as exc:
            assert exc.code == code, f"{code}: refused as {exc.code}: {exc}"
        else:
            raise AssertionError(f"{code}: done")
    assert model.serialize() == CANONICAL["doc-table"], "a refused operation changed the model"


def test_the_live_load_table_model():
    model = to.model_for(to.default_call("live-load-table"))
    assert isinstance(model, to.LiveLoadTableModel)
    assert [c.id for c in model.columns] == list(to.KNOWN_COLUMNS["live-load-table"]) and all(c.known for c in model.columns)
    assert model.hidden == [], "nothing is hidden by default: there is no ψ column to hide"
    # the engineer's own example: the first column hidden, a use written, a category picked -- q_k and Q_k then follow it
    model.hide_column("zone")
    model.add_row()
    model.set_cell(0, "use", "Büro")
    model.set_category(0, "B")
    assert model.cell(0, "q_k") is AUTO and not model.is_override(0, "q_k")
    text = _model_roundtrip(model)
    assert text == """#live-load-table(
  hidden: ("zone",),
  rows: (
    (use: [Büro], category: "B"),
  ),
)""", text
    model.override(0, "q_k", 5)
    assert model.is_override(0, "q_k") and '(use: [Büro], category: "B", q_k: 5),' in _model_roundtrip(model)
    model.clear_override(0, "q_k")
    assert model.cell(0, "q_k") is AUTO and "q_k: auto" in _model_roundtrip(model)
    assert model.hidden == ["zone"] and "columns" not in model.to_call().args     # auto columns kept
    model.set_category(0, None)
    assert "category" not in model.rows[0]
    for code, step in (("not_filled", lambda: model.override(0, "use", 3)), ("bad_value", lambda: model.override(0, "q_k", "3")),
                       ("bad_value", lambda: model.set_cell(0, "category", Content("B")))):
        try:
            step()
        except to.ModelError as exc:
            assert exc.code == code, exc
        else:
            raise AssertionError(code)


def test_a_live_load_table_has_no_psi_column_to_add_and_its_own_columns_move_freely():
    model = to.model_for(to.parse_call("""#live-load-table(
  columns: (
    (id: "use", title: [Nutzung]),
    (id: "category"),
    (id: "q_k"),
    (id: "Q_k"),
  ),
  hidden: (),
  rows: (
    (use: [Wohnen], category: "A1", q_k: auto, Q_k: auto),
  ),
)"""))
    for column in ("psi_0", "psi_1", "psi_2"):
        try:
            model.add_column(column)
        except to.ModelError as exc:
            assert exc.code == "no_title", exc
        else:
            raise AssertionError(f"{column} is a known column")
        try:
            model.override(0, column, 0.7)
        except to.ModelError as exc:
            assert exc.code == "not_filled", exc
        else:
            raise AssertionError(f"{column} is filled from the category")
    model.add_column("psi_0", title="$psi_0$", kind="math")     # a column of the engineer's own, with a title of its own, is his to add
    model.remove_column("psi_0")
    model.move_column("use", 3)
    model.add_column("storey", index=0)
    assert [c.id for c in model.columns] == ["storey", "category", "q_k", "Q_k", "use"]
    _model_roundtrip(model)


def test_the_plan_example_of_the_live_loads_round_trips():
    model = to.model_for(to.parse_call(CANONICAL["live-load-table"]))
    assert model.is_override(1, "q_k") and model.cell(1, "Q_k") == 7 and model.cell(0, "q_k") is AUTO
    assert model.serialize() == CANONICAL["live-load-table"]


def test_a_dead_load_cell_takes_a_value_of_the_variables_tab():
    model = to.model_for(to.default_call("dead-load-table"))
    model.add_row(values={"storey": "EG", "load": 1.6})
    model.add_row(values={"storey": "Dach", "load": to.variable_cell("gk_ak_gew", ("dead-load", "EL+AL-Dach mit Wasser"))})
    model.add_row(values={"storey": "OG", "load": to.variable_cell("g_k")})
    text = _model_roundtrip(model)
    assert '(storey: [Dach], load: [#doc-value("gk_ak_gew", domain: ("dead-load", "EL+AL-Dach mit Wasser"))]),' in text
    assert '(storey: [OG], load: [#doc-value("g_k")]),' in text
    assert to.variable_cell("F", "Ende") == Content('#doc-value("F", domain: "Ende")')
    try:
        model.set_cell(0, "load", AUTO)
    except to.ModelError as exc:
        assert exc.code == "no_auto"
    else:
        raise AssertionError("auto was written into a dead-load cell")


def test_the_choice_and_checklist_models():
    choice = to.model_for(to.parse_call(CANONICAL["doc-choice"]))
    for step in (lambda: choice.add_option("major", "Übergeordnet: 100 Jahre"), lambda: choice.select("major"),
                 lambda: choice.move_option("major", 0), lambda: choice.set_option_label("normal", "Normal"),
                 lambda: choice.set_other("Eigene *Antwort*"), lambda: choice.set_only_selected(True),
                 lambda: choice.select("replaceable"), lambda: choice.remove_option("replaceable"), lambda: choice.set_label(None)):
        step()
        _model_roundtrip(choice)
    assert choice.option_ids() == ["major", "normal"] and choice.selected is None and choice.other is None
    assert choice.to_call().args["label"] is None and choice.only_selected is True     # present in the call, kept as none
    for code, step in (("no_option", lambda: choice.select("gone")), ("id_exists", lambda: choice.add_option("major", "X"))):
        try:
            step()
        except to.ModelError as exc:
            assert exc.code == code
        else:
            raise AssertionError(code)
    checklist = to.model_for(to.parse_call(CANONICAL["doc-checklist"]))
    for step in (lambda: checklist.add_option("fire", "Brand", checked=True, text="Nach VKF."), lambda: checklist.set_checked("vandalism"),
                 lambda: checklist.set_option_text("vandalism", "Nicht bemessen."), lambda: checklist.set_option_text("ground", None),
                 lambda: checklist.move_option("fire", 0), lambda: checklist.remove_option("ground"), lambda: checklist.set_only_checked(False)):
        step()
        _model_roundtrip(checklist)
    assert checklist.option_ids() == ["fire", "vandalism"] and checklist.is_checked("vandalism")
    assert checklist.options[1] == {"id": "vandalism", "label": Content("Vandalismus"), "checked": True, "text": Content("Nicht bemessen.")}


def test_the_signatures_norm_list_field_image_and_plan_models():
    signatures = to.model_for(to.parse_call(CANONICAL["doc-signatures"]))
    for step in (lambda: signatures.add_row(role="Architekt:in", group="Projektverfassende"), lambda: signatures.set_field(0, "name", "M. Muster"),
                 lambda: signatures.set_field(1, "place", None), lambda: signatures.move_row(2, 1), lambda: signatures.remove_row(0),
                 lambda: signatures.set_place_date(True)):
        step()
        _model_roundtrip(signatures)
    assert signatures.rows == [{"group": Content("Projektverfassende"), "role": Content("Architekt:in")},
                               {"group": Content("Projektverfassende"), "role": Content("Ingenieur:in"), "name": Content(to.PLACEHOLDER)}]
    norms = to.model_for(to.parse_call(CANONICAL["show-norm-list"]))
    for step in (lambda: norms.select("SIA 263"), lambda: norms.select("SIA 261", False), lambda: norms.add_text("Eigene Zeile", 0),
                 lambda: norms.move(0, -1), lambda: norms.add_key("VKF 14-15", 1), lambda: norms.remove(0), lambda: norms.set_project(None)):
        step()
        _model_roundtrip(norms)
    assert norms.keys == ["VKF 14-15", "SIA 265", Content("Lärmschutz-Verordnung (LSV)"), "SIA 263", Content("Eigene Zeile")]
    assert "project" in norms.to_call().args      # present in the call, kept at its default
    field = to.model_for(to.parse_call(CANONICAL["doc-field"]))
    for step in (lambda: field.set_value("[…] offen"), lambda: field.set_value(-2.5), lambda: field.set_unit(None), lambda: field.set_label("Wert")):
        step()
        _model_roundtrip(field)
    image = to.model_for(to.default_call("doc-image"))
    for step in (lambda: image.set_file("Images/a.png"), lambda: image.set_width("60%"), lambda: image.set_caption("Bild"),
                 lambda: image.set_placeholder(None), lambda: image.set_width(Expr("50% + 1cm")), lambda: image.set_width("100%")):
        step()
        _model_roundtrip(image)
    assert image.serialize() == '#doc-image(\n  file: "Images/a.png",\n  caption: [Bild],\n)'     # back to the default, not written
    plan = to.model_for(to.parse_call(CANONICAL["doc-plan"]))
    for step in (lambda: plan.set_plan("Fluchttreppe"), lambda: plan.set_highlight("T001"), lambda: plan.set_zoom(2),
                 lambda: plan.set_axes(False), lambda: plan.set_legend(False), lambda: plan.set_scale_bar(False),
                 lambda: plan.set_caption(AUTO), lambda: plan.set_detail(False), lambda: plan.set_highlight(["T001", "T002"])):
        step()
        _model_roundtrip(plan)
    assert plan.serialize().splitlines()[1:] == ['  plan: "Fluchttreppe",', '  highlight: ("T001", "T002"),', "  detail: false,", "  zoom: 2,",
                                                 "  axes: false,", "  legend: false,", "  scale-bar: false,", "  width: 60%,", "  caption: auto,", ")"]


def test_the_fire_plan_object_and_the_two_fire_objects_of_a_sheet_have_their_models():
    """`doc-fire-plan`, `sheet-fire-viewport` and `sheet-fire-legend` (v0.115): the models of a document's fire plan and of a sheet's fire viewport and legend, each written back to the call it was read from, a viewport with one size at a time."""
    fire = to.model_for(to.parse_call(CANONICAL["doc-fire-plan"]))
    for step in (lambda: fire.set_plan("Pavillon-EG"), lambda: fire.set_legend(True), lambda: fire.set_scale_bar(False),
                 lambda: fire.set_caption(AUTO), lambda: fire.set_width("100%")):
        step()
        _model_roundtrip(fire)
    # an argument the call had stays written, even set back to its default (the model's rule)
    assert fire.serialize() == '#doc-fire-plan(\n  plan: "Pavillon-EG",\n  legend: true,\n  scale-bar: false,\n  width: 100%,\n  caption: auto,\n)'
    assert to.model_for(to.default_call("doc-fire-plan")).serialize() == "#doc-fire-plan()"
    viewport = to.model_for(to.default_call("sheet-fire-viewport"))
    viewport.set_plan("Treppenhaus")
    viewport.set_scale(100)
    viewport.set_legend(False)
    _model_roundtrip(viewport)
    viewport.set_width(120)
    assert viewport.get("scale") is None and viewport.get("width") == to.Length(120, "mm"), "a drawing has one size"
    assert viewport.serialize().splitlines()[1:] == ['  plan: "Treppenhaus",', "  x: 20mm,", "  y: 40mm,", "  width: 120mm,", "  legend: false,", ")"]
    legend = to.model_for(to.default_call("sheet-fire-legend"))
    legend.set_width(90)
    legend.set_plans("Treppenhaus")
    legend.move_to(250, 30)
    _model_roundtrip(legend)
    assert legend.serialize().splitlines()[1:] == ['  plans: "Treppenhaus",', "  x: 250mm,", "  y: 30mm,", "  width: 90mm,", ")"]
    for kind in ("sheet-fire-viewport", "sheet-fire-legend", "doc-fire-plan"):
        assert kind in to.OBJECT_TYPES and kind in structure.OBJECT_TYPES


def test_a_model_keeps_an_expression_it_does_not_edit_and_refuses_one_it_would():
    model = to.model_for(to.parse_call('#doc-image(\n  file: "a.png",\n  width: 50% + 1cm,\n)'))
    model.set_caption("Bild")
    assert "  width: 50% + 1cm," in _model_roundtrip(model)
    for body in ("#doc-table(\n  rows: my-rows,\n)", '#doc-checklist(\n  options: (my-option,),\n)', "#show-norm-list(\n  keys: my-keys,\n)"):
        try:
            to.model_for(to.parse_call(body))
        except to.ModelError as exc:
            assert exc.code == "not_editable", exc
        else:
            raise AssertionError(f"{body!r} was taken for editable")


def test_a_model_of_the_wrong_type_is_refused():
    try:
        to.TableModel(to.default_call("doc-field"))
    except to.ModelError as exc:
        assert exc.code == "wrong_type"
    else:
        raise AssertionError("a field was edited as a table")


# --- a heading and a paragraph are objects too -------------------------------------------------------------

BOM = chr(0xFEFF)
ELLIPSIS = chr(0x2026)


def _one(kind, body):
    """The object `kind` holding `body` between its tags."""
    (found,) = to.objects(f"// woodcore:object {kind} x\n{body}\n// woodcore:/object x\n")
    return found


def test_a_heading_and_a_paragraph_are_objects_the_tag_reader_knows():
    assert to.MARKUP_TYPES == ("heading", "text") and to.DOCUMENT_TYPES == to.CALL_TYPES + to.MARKUP_TYPES
    # a document's objects, then an export sheet's (lib/sheet.typ, v0.114), which a section does not hold
    assert to.OBJECT_TYPES == to.DOCUMENT_TYPES + to.SHEET_TYPES
    assert structure.OBJECT_TYPES[len(to.CALL_TYPES):len(to.DOCUMENT_TYPES)] == ("heading", "text")
    text = "// woodcore:object heading title\n= Titel\n// woodcore:/object title\n\n// woodcore:object text p1\nEin Absatz.\n// woodcore:/object p1\n"
    blocks, problems = structure.pair_tags(text)
    assert not problems and [(b.type, b.id) for b in blocks] == [("heading", "title"), ("text", "p1")]
    for kind in to.MARKUP_TYPES:
        try:
            to.default_call(kind)
        except to.ObjectError as exc:
            assert exc.code == "bad_type" and "markup" in str(exc), exc
        else:
            raise AssertionError(f"{kind} has a call")
    assert to.default_body("heading") == "= " + to.PLACEHOLDER and to.default_body("text") == to.PLACEHOLDER
    try:
        to.default_body("doc-field")
    except to.ObjectError as exc:
        assert exc.code == "bad_type", exc
    else:
        raise AssertionError("a call has a body")


def test_the_states_of_a_heading_and_a_paragraph():
    """canonical where the body is the form Woodcore writes; hand_edited where a model can be made of it and it is not that form (a heading written as the call, a paragraph with blank lines round it); unreadable where no model can be made -- nothing, more than a heading, more than one paragraph -- and then the body is **kept** by `canonical`, never replaced by a default."""
    for kind, body in (("heading", "= Titel"), ("heading", "=== Ein Titel <label>"), ("text", "Ein Satz."), ("text", "- eins\n- zwei\n  - tief"),
                       ("text", "Mit $x^2$ und #cite-norm(norm: \"SIA 260\") darin.")):
        found = _one(kind, body)
        assert found.state == "canonical" and found.call is None and found.markup and found.diff() == "", (kind, body, found.state, found.error)
        assert found.model().to_body() == body and found.canonical == body
    for kind, body in (("heading", "#heading(level: 2, \"Titel\")"), ("heading", "  = Titel  "), ("heading", "\n= Titel\n"), ("text", "\nEin Satz.\n"), ("text", "Ein Satz.   ")):
        found = _one(kind, body)
        assert found.state == "hand_edited" and found.call is None and found.error is None, (kind, body, found.state)
        assert found.diff().startswith("--- as written"), found.diff()
        assert found.canonical == found.model().to_body() == found.replacement() and found.canonical != found.written
    for kind, body, why in (("heading", "", "empty"), ("heading", "Kein Titel", "not_a_heading"), ("heading", "= Titel\nund mehr", "several"),
                            ("heading", "= Titel\n= Noch einer", "several"), ("text", "", "empty"), ("text", "Eins.\n\nZwei.", "several"),
                            ("text", "Text\n= Titel", "heading_in_text"), ("text", "Offen #foo(", "unbalanced"), ("text", "Roh `nie zu", "unbalanced")):
        found = _one(kind, body)
        assert found.state == "unreadable" and found.call is None and found.error, (kind, body, found.state)
        assert found.canonical == body and found.replacement() == body, "the body of an object that cannot be read is kept, not replaced by a default"
        try:
            found.model()
        except to.ModelError as exc:
            assert exc.values.get("reason") == why, (kind, body, exc.code, exc.values)
        else:
            raise AssertionError((kind, body))


def test_the_heading_model():
    model = to.HeadingModel.from_body("== Die Bemessung")
    assert (model.level, model.title, model.to_body(), model.serialize()) == (2, "Die Bemessung", "== Die Bemessung", "== Die Bemessung")
    model.set_level(3)
    model.set_title("  Neuer *Titel*  ")
    assert model.to_body() == "=== Neuer *Titel*"
    assert to.HeadingModel.from_body(model.to_body()).to_body() == model.to_body()
    # a label of the engineer's is part of the title and is never dropped by an edit of the level
    kept = to.HeadingModel.from_body("= Einleitung <intro>")
    kept.set_level(2)
    assert kept.to_body() == "== Einleitung <intro>"
    # the call form is read, and written as markup
    call = to.HeadingModel.from_body('#heading(level: 2, "Titel")')
    assert (call.level, call.title, call.to_body()) == (2, "Titel", "== Titel")
    assert to.HeadingModel().to_body() == "= " + to.PLACEHOLDER
    assert to.model_for_body("heading", "= X").type == "heading" and to.model_of(_one("heading", "= X")).to_body() == "= X"
    for step in (lambda: model.set_level(0), lambda: model.set_level(7), lambda: model.set_level("2"), lambda: model.set_level(True),
                 lambda: model.set_title(""), lambda: model.set_title("   "), lambda: model.set_title("zwei\nZeilen"), lambda: model.set_title(5),
                 lambda: model.set_title("offen #foo("), lambda: model.set_title("offen $x")):
        try:
            step()
        except to.ModelError as exc:
            assert exc.code == "bad_value", exc
        else:
            raise AssertionError("a bad heading was accepted")
    assert model.to_body() == "=== Neuer *Titel*", "a refused change changed the model"


def test_the_paragraph_model():
    model = to.TextModel.from_body("Erste Zeile\nzweite Zeile mit $x$.")
    assert model.text == "Erste Zeile\nzweite Zeile mit $x$." and model.to_body() == model.text == model.serialize()
    model.set_text("\n\nNeu.  \n\n")
    assert model.to_body() == "Neu."
    model.set_text("- eins\n- zwei")                       # a list is one paragraph
    assert model.to_body() == "- eins\n- zwei"
    model.set_text("  eingerückt")
    assert model.to_body() == "  eingerückt", "the indentation of the first line is the engineer's"
    model.set_text(to.Content("als Inhalt"))
    assert model.to_body() == "als Inhalt"
    for step, reason in ((lambda: model.set_text(""), "empty"), (lambda: model.set_text("  \n "), "empty"), (lambda: model.set_text("Eins.\n\nZwei."), "several"),
                         (lambda: model.set_text("Satz\n== Titel"), "heading_in_text"), (lambda: model.set_text("Satz\n// woodcore:object text x"), "tag_in_body"),
                         (lambda: model.set_text("Satz\n// woodcore:/object x"), "tag_in_body"), (lambda: model.set_text("#f(offen"), "unbalanced"),
                         (lambda: model.set_text("$offen"), "unbalanced"), (lambda: model.set_text("```nie"), "unbalanced"), (lambda: model.set_text("/* nie"), "unbalanced"),
                         (lambda: model.set_text(5), "type")):
        try:
            step()
        except to.ModelError as exc:
            assert exc.values.get("reason") == reason, (reason, exc.code, exc.values, str(exc))
        else:
            raise AssertionError(f"{reason}: accepted")
    assert model.to_body() == "als Inhalt", "a refused change changed the model"
    assert to.TextModel().to_body() == to.PLACEHOLDER
    # what looks like the file's own markup, where it is not, is a paragraph
    odd = "Ein `=` im Roh und `// woodcore:` auch"
    assert to.TextModel(odd).to_body() == odd


def test_write_object_writes_a_heading_and_a_paragraph_from_a_string_or_a_model():
    text = ("#import \"/commands.typ\": *\n\n// woodcore:object heading title\n= Alt\n// woodcore:/object title\n\n"
            "// woodcore:object text p1\nAlter Text.\n// woodcore:/object p1\n\nSchluss.\n")
    title = to.find(text, "title")
    for new in (to.write_object(text, "title", "== Neu"), to.write_object(text, "title", to.HeadingModel(2, "Neu"))):
        found = to.find(new, "title")
        assert found.state == "canonical" and found.written == "== Neu"
        assert _split_around(new, found) == _split_around(text, title)
        assert to.write_object(new, "title", "== Neu") == new          # a second write writes the same text
    new = to.write_object(text, "p1", "Zeile eins\nZeile zwei")
    assert to.find(new, "p1").written == "Zeile eins\nZeile zwei" and to.find(new, "title").body == "= Alt"
    assert new.endswith("\nSchluss.\n") and new.startswith(text[:to.find(text, "p1").body_span[0]])
    # a body that is not what the tag names is refused, and says so
    for call, code in ((to.default_call("doc-field"), "type_mismatch"), ("", "bad_body"), ("kein Titel", "bad_body"), (5, "not_written"), (to.TextModel("x"), "type_mismatch")):
        try:
            to.write_object(text, "title", call)
        except to.ObjectError as exc:
            assert exc.code == code, (call, exc.code, str(exc))
        else:
            raise AssertionError(f"{call!r} was written as a heading")
    for call, code in (("Eins.\n\nZwei.", "bad_body"), (to.HeadingModel(1, "x"), "type_mismatch"), (to.default_call("doc-field"), "type_mismatch")):
        try:
            to.write_object(text, "p1", call)
        except to.ObjectError as exc:
            assert exc.code == code, (call, exc.code)
            if code == "bad_body":
                assert exc.values["reason"] == "several", exc.values
        else:
            raise AssertionError(f"{call!r} was written as a paragraph")
    # a body Woodcore reads as hand-edited is rewritten only on a yes
    edited = text.replace("= Alt", "#heading(level: 1, \"Alt\")")
    assert to.find(edited, "title").state == "hand_edited"
    try:
        to.write_object(edited, "title", "= Neu")
    except to.ObjectError as exc:
        assert exc.code == "hand_edited", exc
    else:
        raise AssertionError("a hand-edited heading was rewritten without a word")
    assert to.find(to.write_object(edited, "title", "= Neu", force=True), "title").written == "= Neu"
    # `expected` still tells that the body changed under the editor
    try:
        to.write_object(text, "p1", "Neu.", expected="etwas anderes")
    except to.ObjectError as exc:
        assert exc.code == "changed", exc
    else:
        raise AssertionError("a changed body was overwritten")
    assert to.find(to.write_object(text, "p1", "Neu.", expected="Alter Text."), "p1").written == "Neu."


def test_write_object_keeps_a_crlf_file_crlf_for_a_paragraph_of_several_lines():
    text = "#import \"/commands.typ\": *\r\n\r\n// woodcore:object text p1\r\nEins.\r\n// woodcore:/object p1\r\n"
    new = to.write_object(text, "p1", "Zeile eins\nZeile zwei")
    assert new == "#import \"/commands.typ\": *\r\n\r\n// woodcore:object text p1\r\nZeile eins\r\nZeile zwei\r\n// woodcore:/object p1\r\n"
    assert to.find(new, "p1").written == "Zeile eins\nZeile zwei"


def test_a_heading_and_a_paragraph_are_inserted_and_removed_like_any_object():
    text = "#import \"/commands.typ\": *\n\n= Titel\n\nText.\n"
    with_heading = to.insert_object(text, 3, "heading", "h2", "== Unter")
    with_text = to.insert_object(with_heading, 3, "text", "p1")
    assert [(o.type, o.id, o.written, o.state) for o in to.objects(with_text)] == [("text", "p1", to.PLACEHOLDER, "canonical"), ("heading", "h2", "== Unter", "canonical")]
    first = to.insert_object(text, -1, "text", "p9", to.TextModel("Zuerst."))
    assert first.startswith("// woodcore:object text p9\nZuerst.\n// woodcore:/object p9\n#import")
    assert to.remove_object(with_text, "p1") == with_heading and to.remove_object(with_heading, "h2") == text
    for args, code in (((3, "text", "p1", to.default_call("doc-field")), "type_mismatch"), ((3, "heading", "h2", "Kein Titel"), "bad_body"),
                       ((3, "text", "t", "Eins.\n\nZwei."), "bad_body"), ((3, "banner", "b"), "bad_type")):
        try:
            to.insert_object(text, *args)
        except to.ObjectError as exc:
            assert exc.code == code, (args, exc.code)
        else:
            raise AssertionError(args)
    assert to.free_id(with_text, "p1") == "p1-2" and to.free_id(text, "p1") == "p1"


def test_an_objects_short_label():
    text = ("// woodcore:object heading title\n== Die *Bemessung* der Träger <bem> // Notiz\n// woodcore:/object title\n"
            "// woodcore:object text p1\nLes charges utiles admissibles dépendent de #cite-norm(norm: \"SIA 261\") et de l'affectation prévue sur le sol de l'étage concerné.\n// woodcore:/object p1\n"
            "// woodcore:object text p2\n#cite-norm(norm: \"SIA 260\")\n// woodcore:/object p2\n"
            "// woodcore:object doc-table t1\n#doc-table(\n  caption: [Les *documents* de référence],\n)\n// woodcore:/object t1\n"
            "// woodcore:object doc-field f1\n#doc-field(\n  label: [Nutzungsdauer],\n)\n// woodcore:/object f1\n"
            "// woodcore:object doc-image i1\n#doc-image(\n  file: \"Images/Profil.png\",\n)\n// woodcore:/object i1\n"
            "// woodcore:object doc-signatures s1\n#doc-signatures()\n// woodcore:/object s1\n"
            "// woodcore:object text bad\nEins.\n\nZwei.\n// woodcore:/object bad\n")
    found = to.objects(text)
    labels = {o.id: to.object_title(o) for o in found}
    assert labels["title"] == "Die Bemessung der Träger", labels["title"]
    assert labels["p1"].startswith("Les charges utiles admissibles dépendent de et") and labels["p1"].endswith(ELLIPSIS) and len(labels["p1"]) <= 61, labels["p1"]
    assert labels["p2"] == "p2", "a paragraph that is only a call says nothing readable: its id"
    assert labels["t1"] == "Les documents de référence" and labels["f1"] == "Nutzungsdauer" and labels["i1"] == "Images/Profil.png"
    assert labels["s1"] == "doc-signatures" and labels["bad"] == "Eins. Zwei."
    assert to.object_title(found[1], limit=12) == "Les charges" + ELLIPSIS


# --- tagging a file that has no tags --------------------------------------------------------------------------

UNTAGGED = """#import "/commands.typ": *
#set text(lang: "de")

= Grundlagen

Der erste Absatz,
über zwei Zeilen.

// ein Kommentar, den niemand beachten muss
Der zweite Absatz mit #cite-norm(norm: "SIA 260") mittendrin.

- ein Punkt
- noch ein Punkt

== Unterabschnitt

#figure(
  image("/Images/x.png"),

  caption: [Ein Bild mit einer Leerzeile in seinen Argumenten.],
)
#v(1em)
#show-plan("Plan", width: 50%)

#cite-norm(norm: "SIA 261") beginnt einen Absatz, der mit Worten weitergeht.

```
= kein Titel, ein Rohblock

mit Leerzeile
```

#if true [
  === Im Inhaltsblock
  Auch kein Absatz des Dokuments.
]

$ x = 1 $

/* ein Blockkommentar
= auch kein Titel */
Letzter Absatz ohne Zeilenende"""

# What the file's own markup holds: (kind, the first line), in file order.
UNTAGGED_FOUND = [("heading", "= Grundlagen"), ("text", "Der erste Absatz,"), ("text", 'Der zweite Absatz mit #cite-norm(norm: "SIA 260") mittendrin.'),
                  ("text", "- ein Punkt"), ("heading", "== Unterabschnitt"), ("text", '#cite-norm(norm: "SIA 261") beginnt einen Absatz, der mit Worten weitergeht.'),
                  ("text", "$ x = 1 $"), ("text", "Letzter Absatz ohne Zeilenende")]
# Never the file's own: code, comments, a raw block, what a construct holds.
NOT_THE_FILES_OWN = ("#set text", "#figure(", "#v(1em)", "#show-plan(", "// ein Kommentar", "```", "#if true [", "=== Im Inhaltsblock", "Auch kein Absatz", "/* ein Blockkommentar", "= auch kein Titel")


def _tag_lines_taken_out(text):
    return "".join(line for line in text.splitlines(keepends=True) if not line.startswith(("// woodcore:object", "// woodcore:/object")))


def test_untagged_finds_the_headings_and_the_paragraphs_of_the_files_own_markup():
    found = to.untagged(UNTAGGED)
    lines = UNTAGGED.split("\n")
    assert [(u.kind, u.text.split("\n")[0]) for u in found] == UNTAGGED_FOUND
    assert all(lines[u.start] == u.text.split("\n")[0] and "\n".join(lines[u.start:u.end + 1]) == u.text for u in found)
    assert [u.level for u in found if u.kind == "heading"] == [1, 2] and all(u.level is None for u in found if u.kind == "text")
    assert found[1].text == "Der erste Absatz,\nüber zwei Zeilen." and found[3].text == "- ein Punkt\n- noch ein Punkt"
    assert to.untagged("") == [] and to.untagged("\n\n") == [] and to.untagged('#import "/commands.typ": *\n') == []


def test_tag_file_wraps_every_untagged_heading_and_paragraph_and_nothing_else():
    new = to.tag_file(UNTAGGED)
    found = to.objects(new)
    assert [(o.type, o.written.split("\n")[0]) for o in found] == UNTAGGED_FOUND and all(o.state == "canonical" for o in found)
    assert [o.id for o in found] == ["grundlagen", "der-erste-absatz-uber", "der-zweite-absatz-mit", "ein-punkt", "unterabschnitt", "beginnt-einen-absatz-der",
                                     "x-1", "letzter-absatz-ohne-zeilenende"]
    assert not structure.check_tags(new), structure.check_tags(new)
    # the file without its tag lines is the file it was -- the tags are comments, every other byte is kept (the last line, which had no line ending, has one now)
    assert _tag_lines_taken_out(new) == UNTAGGED + "\n"
    # a second run writes the same text -- it is the very string that comes back
    assert to.tag_file(new) is new and to.untagged(new) == []
    # nothing was wrapped that is code, a comment, a raw block, a call alone on its lines, or what a construct holds
    new_lines = new.split("\n")
    for needle in NOT_THE_FILES_OWN:
        k = next(i for i, line in enumerate(new_lines) if line.lstrip().startswith(needle))
        assert not any(o.start <= k <= o.end for o in found), needle


def test_tag_file_ids():
    plain = to.tag_file(UNTAGGED, ids="plain")
    assert [o.id for o in to.objects(plain)] == ["title", "p1", "p2", "p3", "h2", "p4", "p5", "p6"]
    assert [(o.type, o.written.split("\n")[0]) for o in to.objects(plain)] == UNTAGGED_FOUND
    # an id already in the file is not given twice, and the ids a first run chose are not chosen again
    text = ("// woodcore:object text p1\nSchon da.\n// woodcore:/object p1\n\n// woodcore:object heading title\n= Da\n// woodcore:/object title\n\n"
            "Noch ein Absatz.\n\n= Zweiter Titel\n")
    new = to.tag_file(text, ids="plain")
    assert [o.id for o in to.objects(new)] == ["p1", "title", "p1-2", "title-2"] and to.tag_file(new, ids="plain") == new
    assert [o.id for o in to.objects(to.tag_file("Wiederholt.\n\nWiederholt.\n"))] == ["wiederholt", "wiederholt-2"]
    # an id is made of the words, and starts with a letter whatever the words start with
    new = to.tag_file("= 2026 Übersicht & Ausblick\n\n5 Dinge zuerst\n\n$x$ und 5 Dinge\n\n#cite-norm(norm: \"X\") steht vorn.\n\n= !!!\n")
    assert [o.id for o in to.objects(new)] == ["heading-2026-ubersicht-ausblick", "text-5-dinge-zuerst", "und-5-dinge", "steht-vorn", "heading"]
    try:
        to.tag_file(UNTAGGED, ids="numbers")
    except to.ObjectError as exc:
        assert exc.code == "bad_id", exc
    else:
        raise AssertionError("an id style that does not exist was accepted")


def test_tag_file_keeps_the_line_endings_and_a_last_line_with_none():
    crlf = UNTAGGED.replace("\n", "\r\n")
    new = to.tag_file(crlf)
    assert "\n" not in new.replace("\r\n", "") and "\r" not in new.replace("\r\n", ""), "a line ending changed"
    assert new.count("\r\n") == crlf.count("\r\n") + 2 * 8, "sixteen tag lines, each with the file's own ending but the last, and the last paragraph's own"
    assert len(to.objects(new)) == 8 and all(o.state == "canonical" for o in to.objects(new))
    assert _tag_lines_taken_out(new) == crlf + "\r\n" and to.tag_file(new) == new
    # the last paragraph had no line ending: its end tag follows it on a line of its own and has none either
    assert not UNTAGGED.endswith("\n") and not new.endswith("\r\n") and new.endswith("// woodcore:/object letzter-absatz-ohne-zeilenende")
    assert new.split("\r\n")[-2] == "Letzter Absatz ohne Zeilenende"
    # a file saved with LF keeps LF, one that ends with a line ending ends with one
    lf = to.tag_file("= Titel\n\nText.\n")
    assert lf == "// woodcore:object heading titel\n= Titel\n// woodcore:/object titel\n\n// woodcore:object text text\nText.\n// woodcore:/object text\n"
    # a byte order mark stays the first character of the file
    bom = to.tag_file(BOM + "= Titel\n\nText.\n")
    assert bom == BOM + lf and [o.id for o in to.objects(bom)] == ["titel", "text"]


def test_tag_file_leaves_what_is_tagged_alone_and_tags_the_rest_around_it():
    text = ("#import \"/commands.typ\": *\n\n// woodcore:shared live-loads\n= Charges\n\nAvant.\n\n"
            "// woodcore:object doc-field f\n#doc-field(\n  label: [Nutzungsdauer],\n)\n// woodcore:/object f\n\n"
            "// woodcore:object text mine\nDéjà balisé.\n// woodcore:/object mine\n\nAprès.\n// woodcore:/shared live-loads\n")
    new = to.tag_file(text)
    found = to.objects(new)
    assert [(o.type, o.id) for o in found] == [("heading", "charges"), ("text", "avant"), ("doc-field", "f"), ("text", "mine"), ("text", "apres")]
    assert all(o.shared == "live-loads" for o in found), "an object tagged inside a shared block is inside it"
    assert not structure.check_tags(new), structure.check_tags(new)
    added = ("// woodcore:object heading charges\n", "// woodcore:/object charges\n", "// woodcore:object text avant\n", "// woodcore:/object avant\n",
             "// woodcore:object text apres\n", "// woodcore:/object apres\n")
    stripped = new
    for line in added:
        assert stripped.count(line) == 1, line
        stripped = stripped.replace(line, "")
    assert stripped == text, "an object that was there is byte for byte what it was"


def test_suggest_id_makes_an_id_of_the_words_and_never_gives_one_twice():
    text = "// woodcore:object text p1\nx\n// woodcore:/object p1\n// woodcore:object text die-bemessung\ny\n// woodcore:/object die-bemessung\n"
    assert to.suggest_id(text, "heading", "== Die Bemessung der Träger") == "die-bemessung-der-trager"
    assert to.suggest_id(text, "text", "Die Bemessung der Träger erfolgt nach SIA 265.") == "die-bemessung-der-trager"
    assert to.suggest_id(text, "text", "Die Bemessung erfolgt.") == "die-bemessung-erfolgt" and to.suggest_id(text, "text", "Die Bemessung") == "die-bemessung-2"
    assert to.suggest_id(text, "heading") == "heading" and to.suggest_id(text, "text") == "text" and to.suggest_id(text, "text", "$x$") == "x"
    assert to.suggest_id(text, "doc-table") == "doc-table" and to.suggest_id(text + "// woodcore:object doc-table doc-table\n#doc-table()\n// woodcore:/object doc-table\n", "doc-table") == "doc-table-2"
    assert to.suggest_id(text, "heading", "= 2026") == "heading-2026"
    try:
        to.suggest_id(text, "banner")
    except to.ObjectError as exc:
        assert exc.code == "bad_type", exc
    else:
        raise AssertionError("a kind that does not exist was accepted")
    assert to.insert_object(text, -1, "text", to.suggest_id(text, "text", "Neuer Absatz hier")).count("// woodcore:object text neuer-absatz-hier") == 1


def test_tag_file_refuses_a_file_whose_tags_cannot_be_read():
    text = "= Titel\n\n// woodcore:object text p1\nOffen.\n"
    for call in (to.tag_file, to.untagged):
        try:
            call(text)
        except to.ObjectError as exc:
            assert exc.code == "tags" and exc.values["problems"], exc
        else:
            raise AssertionError("a file with a tag problem was tagged")


def test_tag_file_on_the_files_of_the_example_report_gives_objects_that_all_read():
    """The section files of the example project's report -- headings at every level, paragraphs, calls, a grid with blank lines in its arguments, an `#if` printing a heading -- tagged: every object canonical, nothing of the file's own markup left outside, and a second run changing nothing."""
    folder = conftest.PROJECT.document_dir("rs") / "Sections"
    seen = 0
    for path in sorted(folder.glob("*.typ")):
        text = path.read_bytes().decode("utf-8")
        new = to.tag_file(text)
        assert to.tag_file(new) == new and not to.untagged(new), path.name
        assert not structure.check_tags(new), (path.name, structure.check_tags(new))
        found = to.objects(new)
        assert found and all(o.state == "canonical" for o in found), path.name
        headings = [o for o in found if o.type == "heading"]
        assert 1 <= len(headings) <= len(structure.scan_headings(text)), path.name
        seen += len(found)
    assert seen > 30, seen


def test_tag_file_never_breaks_a_compile_and_the_report_prints_what_it_printed():
    """Every section file of the example project's report tagged, in a copy of the project: it compiles, and the PDF says the same words as before -- the tags are comments."""
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    import documents
    import project
    from pypdf import PdfReader
    source = conftest.PROJECT
    target = conftest.tmpdir("tag_compile") / "Halle"
    shutil.copytree(source.root, target, ignore=shutil.ignore_patterns("_Archiv", "stamps", "1_*", "2_*"))
    here = project.Project.load(target / source.file.name)

    def printed():
        out = here.document_pdf("rs")
        run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "rs", target=out)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert run.returncode == 0, run.stderr[:2000]
        return "\n".join(p.extract_text() for p in PdfReader(str(out)).pages)

    before = printed()
    for path in sorted((here.document_dir("rs") / "Sections").glob("*.typ")):
        path.write_bytes(to.tag_file(path.read_bytes().decode("utf-8")).encode("utf-8"))
    after = printed()
    assert before.strip() and after == before, "the tags changed what the report prints"


# --- what the repository carries ---------------------------------------------------------------------------

def _fences(text):
    """The calls of the ten commands written in the ```typ fences of the `///` blocks of a .typ file."""
    calls, fence, inside = [], [], False
    for line in text.splitlines():
        if not line.startswith("///"):
            inside = False
            continue
        body = line[3:].removeprefix(" ")
        if body.startswith("```"):
            if inside:
                source = "\n".join(fence)
                for found in re.finditer(r"(?m)^#(" + "|".join(map(re.escape, to.CALL_TYPES)) + r")\(", source):
                    calls.append(to.parse_call_at(source, found.start())[0])
                fence = []
            inside = not inside and body.startswith("```typ")
            continue
        if inside:
            fence.append(body)
    return calls


def test_the_examples_of_lib_document_are_read():
    calls = _fences(DOCUMENT_TYP.read_text(encoding="utf-8"))
    assert {c.type for c in calls} == set(to.CALL_TYPES), sorted({c.type for c in calls})
    for call in calls:
        text = to.serialize(call)
        assert to.serialize(to.parse_call(text)) == text
        _model_roundtrip(to.model_for(call))


def _typst_files():
    folders = [ROOT / "templates" / "documents", ROOT / "tests" / "projet-exemple"]
    for folder in folders:
        for path in sorted(folder.rglob("*.typ")):
            # a calculation domain's file carries a tag of its own, read by calc/domains/formula_domain.py and held canonical by tests/test_formula_domain.py
            if "_woodcore" not in path.parts and project.FORMULAS_FOLDER not in path.parts:
                yield path


def test_every_object_the_repository_carries_is_canonical():
    """Every object in templates/documents and the example project: readable, and in the form Woodcore writes -- so that a first edit in Woodcore warns about nothing the engineer did."""
    bad, count = [], 0
    for path in _typst_files():
        text = path.read_bytes().decode("utf-8")
        found, problems = to.scan(text)
        rel = path.relative_to(ROOT).as_posix()
        if problems:
            bad.append(f"{rel}: tags: " + "; ".join(map(str, problems)))
        for obj in found:
            count += 1
            if obj.state == "unreadable":
                bad.append(f"{rel}: {obj.type} {obj.id} cannot be read: {obj.error}")
            elif obj.state == "hand_edited":
                bad.append(f"{rel}: {obj.type} {obj.id} is not in the canonical form:\n{obj.diff()}")
            elif obj.markup:
                assert obj.model().to_body() == obj.written, f"{rel}: {obj.type} {obj.id}"
            else:
                _model_roundtrip(to.model_for(obj.call))
    print(f"  {count} object(s) in the templates and the example project")
    assert not bad, "\n".join(bad)


# --- a document still compiles --------------------------------------------------------------------------------

def test_a_document_compiles_after_its_objects_are_written():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import project
    import project_template
    here = project_template.create(conftest.tmpdir("objects_compile") / "Halle", "Halle")
    section = here.document_dir("cu") / "Sections" / "objects-probe.typ"
    text = '#import "/commands.typ": *\r\n\r\n= Objekte\r\n\r\nText.\r\n'     # CRLF, as a file saved on Windows
    for kind in to.CALL_TYPES:
        text = to.insert_object(text, len(to._lines(text)) - 1, kind, to.free_id(text, kind))
    # every object edited through its model and written back
    edits = {
        "doc-table": lambda m: (m.set_caption("Nutzungsdauer"), m.add_row(values={"a": "Tragwerk", "b": 50})),
        "live-load-table": lambda m: (m.hide_column("zone"), m.add_row(values={"storey": "EG", "use": "Büro"}), m.set_category(0, "B"),
                                      m.add_row(values={"use": "Archiv"}), m.set_category(1, "E"), m.override(1, "q_k", 7.5), m.override(1, "Q_k", 7)),
        "dead-load-table": lambda m: (m.add_row(values={"storey": "OG", "buildup": "Unterlagsboden", "load": 1.6}),
                                      m.add_row(values={"storey": "Dach", "load": Content('#val("q_k", domain: ("live-load", "A1"), type: "val", level: 1)')})),
        "doc-field": lambda m: (m.set_label("Nutzungsdauer"), m.set_value(50), m.set_unit("Jahre")),
        "doc-checklist": lambda m: (m.set_label("Risiken"), m.add_option("ground", "Baugrund", checked=True, text="Akzeptiert.")),
        "doc-choice": lambda m: (m.add_option("i", "BWK I"), m.add_option("ii", "BWK II"), m.select("ii")),
        "doc-image": lambda m: (m.set_caption("Profil"), m.set_width("50%")),
        "doc-plan": lambda m: m.set_caption("Belastungsplan"),
        "doc-fire-plan": lambda m: (m.set_caption("Brandschutzplan"), m.set_legend(True), m.set_scale_bar(False)),
        "doc-extract": lambda m: (m.set_caption("Auszug aus dem Rapport"), m.set_width("50%")),
        "doc-annexes": lambda m: m.set_heading(None),
        "doc-signatures": lambda m: (m.add_row(group="Bauherrschaft", role="Bauherrschaft"), m.add_row(role="Ingenieur:in")),
        "show-norm-list": lambda m: (m.select("SIA 260"), m.select("SIA 261"), m.add_text("Eigene Grundlage")),
    }
    for obj in to.objects(text):
        model = to.model_for(obj.call)
        edits[obj.type](model)
        before = text
        text = to.write_object(text, obj.id, model.to_call())
        new = to.find(text, obj.id)
        assert new.state == "canonical"
        begin, finish = new.body_span
        old = to.find(before, obj.id).body_span
        assert text[:begin] == before[:old[0]] and text[finish:] == before[old[1]:]
    assert "\n" not in text.replace("\r\n", "")
    section.write_bytes(text.encode("utf-8"))
    entry = here.typst_root / "objects-probe.typ"
    entry.write_text('#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n#set-report-language("de")\n'
                     f'#include "/{section.relative_to(here.typst_root).as_posix()}"\n', encoding="utf-8")
    out = entry.with_suffix(".pdf")
    run = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(entry), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    from pypdf import PdfReader
    printed = "\n".join(p.extract_text() for p in PdfReader(str(out)).pages)
    for word in ("Tragwerk", "Büro", "Archiv", "7.5", "Unterlagsboden", "BWK II", "Baugrund", "Profil", "Belastungsplan", "Ingenieur:in", "Eigene Grundlage", "Nutzungsdauer"):
        assert word in printed, f"{word!r} is not on the page"
