"""The metadata an RFEM comment carries (`calc/rfem_import/metadata_parser.py`).

Every case the engineer listed for it: the three comments of his own worked example, the seven keys, several entries in one comment, the three length units, an invalid value, an ordinary comment, quotes, several spaces -- and the rule that came out of the convention being settled: one sigil, `@`, and nothing here refuses.

⚠️ **Three of these tests carry strings RFEM itself produced**, on the engineer's own model over the gRPC API, and they are the reason the convention is what it is. RFEM reserves `#` for its own object tagging: it strips `#key` out of a comment, moves it to the end, eats the newline and orphans the value. Those strings are kept verbatim so that the day somebody proposes `#` again, a test says why not.

**What is deliberately not here**: that `@position "T999"` names a position which does not exist, and that a position may only be written on a member or a surface. Both need the model around the comment, so both are `validation.py`'s, and testing them here would test a module that cannot see what it is checking.
"""

import engine
from rfem_import import metadata_parser
from rfem_import.metadata_parser import (
    KEYS, MEMBER_OR_SURFACE_ONLY, REFERENCES, SIGIL, parse_metadata,
)


def _codes(md):
    return sorted(p.code for p in md.problems)


def _clean(md, where=""):
    assert not md.problems, f"{where or 'this comment'} should read without a problem, got {[str(p) for p in md.problems]}"


# --- the engineer's own example, as RFEM really stored it ------------------------------------------


def test_the_structure_comment_of_the_worked_example():
    """A node naming the structure: its id, its name and its description. This is the string read back out of the engineer's model, and out of the exported CSV, unchanged."""
    md = parse_metadata('@model "VU-gunstig"\n@label "Velo Unterstand mit gunstige Einwirkungen"\n@descr "gunstige Einwirkung mit reduzierte Einwirkungsbreite"')
    _clean(md, "the structure's node")
    assert md.values == {
        "model": "VU-gunstig",
        "label": "Velo Unterstand mit gunstige Einwirkungen",
        "descr": "gunstige Einwirkung mit reduzierte Einwirkungsbreite",
    }, f"the node's metadata came out as {md.values}"


def test_the_member_comment_of_the_worked_example():
    """A member naming the position it realises and its own influence width."""
    md = parse_metadata('@position "T001"\n@be 1.7m')
    _clean(md, "the member")
    assert md.values == {"position": "T001", "be": 1.7}, f"the member's metadata came out as {md.values}"


def test_the_line_load_comment_of_the_worked_example():
    """A load's width is the load's own property, and its note survives its apostrophes -- verified through the CSV export."""
    md = parse_metadata('@be 2m\n@note "la charge de neige ne peut s\'appliquer que depuis l\'avant-toit"')
    _clean(md, "the line load")
    assert md.values["be"] == 2.0, f"be came out as {md.values.get('be')}"
    assert md.values["note"] == "la charge de neige ne peut s'appliquer que depuis l'avant-toit", (
        f"the note came out as {md.values.get('note')!r} -- an apostrophe inside a double-quoted value is text, not a quote"
    )


def test_a_load_case_names_the_woodcore_instance_it_came_from():
    """`@load` is the second reference of the convention: a load case pointing at the calculation that produced its value."""
    md = parse_metadata('@load "snow-load/SL-Dach1"')
    _clean(md)
    assert md.values == {"load": "snow-load/SL-Dach1"}, f"came out as {md.values}"


# --- what RFEM does to `#`, measured --------------------------------------------------------------


def test_what_rfem_returns_when_a_hash_line_was_written():
    """⚠️ This is verbatim what RFEM 6.15 stored after being sent three `#` lines on the engineer's node 36.

    Sent:
        #model "VU-gunstig"
        #label "Velo Unterstand mit gunstige Einwirkungen"
        #descr "gunstige Einwirkung mit reduzierte Einwirkungsbreite"

    RFEM kept the values, threw away the newlines, and moved the three keys to the end. Nothing here can recover which value belonged to which key, so the parser must not guess: it extracts nothing and names every tag it finds.
    """
    mangled = '"VU-gunstig" "Velo Unterstand mit gunstige Einwirkungen" "gunstige Einwirkung mit reduzierte Einwirkungsbreite" #model #label #descr'
    md = parse_metadata(mangled, where="Node 36")
    assert md.values == {}, f"nothing may be guessed from a mangled comment, got {md.values}"
    assert _codes(md) == ["rfem_meta_hash"] * 3, f"each lost key must be named, got {[str(p) for p in md.problems]}"
    said = " ".join(str(p) for p in md.problems)
    assert "@model" in said and "value is lost" in said, f"the report must say what to write and that the value is gone: {said}"


def test_the_nine_sigils_rfem_was_sent():
    """⚠️ Verbatim from RFEM: of nine sigils on nine lines, every one survived but `#`.

    Sent    `@a 1 / &b 2 / $c 3 / >d 4 / !e 5 / +f 6 / :g 7 / ~h 8 / #i 9` on separate lines,
    stored  the same, except the last two lines came back as the single line `~h 8 9 #i`.

    So the line structure is safe for every sigil but that one, which is why `@` is the convention and why a leftover `#` is a diagnosis rather than a curiosity.
    """
    stored = '@a 1\n&b 2\n$c 3\n>d 4\n!e 5\n+f 6\n:g 7\n~h 8 9 #i'
    md = parse_metadata(stored, where="Member 27")
    assert "rfem_meta_hash" in _codes(md), f"the surviving #i must be reported, got {_codes(md)}"
    # None of a..h is a real key, so each is reported as unknown; and `h` takes the whole rest of its line -- the orphaned `9` and the moved `#i` included, which is exactly the damage being recorded.
    assert md.values == {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5", "f": "6", "g": "7", "h": "8 9 #i"}, f"got {md.values}"


def test_a_hash_on_an_unknown_name_is_still_reported():
    """RFEM's own tags are legitimate -- an engineer may tag objects for his own filtering. The report says so without claiming a value was lost, since no metadata key was involved."""
    md = parse_metadata("un commentaire ordinaire #Halle", where="Member 5")
    assert md.values == {}
    assert _codes(md) == ["rfem_meta_hash"]
    assert "value is lost" not in str(md.problems[0]), "no metadata key was involved, so nothing was lost"


# --- one sigil ------------------------------------------------------------------------------------


def test_there_is_one_sigil_and_it_is_the_at_sign():
    assert SIGIL == "@", "the engineer chose a single sigil, and RFEM only tolerates this one"
    assert metadata_parser.RFEM_TAG_SIGIL == "#"


def test_the_keys_declare_which_of_them_refer():
    """One sigil no longer distinguishes a reference from a property, so `KEYS` and `REFERENCES` carry it -- and `validation.py` reads them."""
    assert REFERENCES == {"position", "load"}, f"got {REFERENCES}"
    assert REFERENCES <= set(KEYS), "every reference must be a known key"
    assert MEMBER_OR_SURFACE_ONLY == {"position"}, (
        "the engineer's rule: a position is only ever written on a member or a surface, never on a node, a support or a load"
    )
    assert MEMBER_OR_SURFACE_ONLY <= set(KEYS)


def test_another_sigil_is_read_and_reported():
    """`>position` and `&be` are read -- the intent is plain -- and the report says to write `@`."""
    for written, expected in (('>position "T001"', {"position": "T001"}), ("&be 1.5m", {"be": 1.5})):
        md = parse_metadata(written)
        assert md.values == expected, f"«{written}» came out as {md.values}"
        assert _codes(md) == ["rfem_meta_sigil"], f"«{written}» gave {[str(p) for p in md.problems]}"
        assert "@" in str(md.problems[0])


# --- the units ------------------------------------------------------------------------------------


def test_the_three_units_are_one_width():
    """«@be 1500mm», «150cm» and «1.5m» must be the same value -- the engineer's own requirement, and the reason a length is normalised at all."""
    widths = {unit: parse_metadata(f"@be {written}").values["be"] for unit, written in (("mm", "1500mm"), ("cm", "150cm"), ("m", "1.5m"))}
    assert set(widths.values()) == {1.5}, f"the three spellings gave {widths}"


def test_a_width_with_no_unit_is_metres():
    """Documented rather than refused: a structural drawing is in metres, and catching «@be 1500» as a mistake needs a notion of what is plausible, which is validation's."""
    assert parse_metadata("@be 1.5").values["be"] == 1.5


def test_a_comma_is_a_decimal_separator():
    """The keyboard this is typed on is Swiss. Accepting it costs one character and saves a width read as text."""
    assert parse_metadata("@be 1,5m").values["be"] == 1.5


def test_a_millimetre_width_keeps_its_precision():
    assert parse_metadata("@be 1727mm").values["be"] == 1.727


# --- what a value may look like -------------------------------------------------------------------


def test_an_unquoted_value_may_carry_spaces():
    """One entry per line is what buys this: everything after the key is the value, so a name needs no quotes."""
    md = parse_metadata("@label Velo Unterstand mit Vordach")
    _clean(md)
    assert md.values["label"] == "Velo Unterstand mit Vordach", f"came out as {md.values.get('label')!r}"


def test_several_spaces_a_colon_and_an_equals_are_accepted():
    """A comment is typed by hand into a window with no completion, so the parser forgives the spellings the convention was itself first written in (`@descr: "..."`)."""
    for written in ('@descr "x"', '@descr: "x"', '@descr = "x"', '@   descr:    "x"', '  @descr "x"  '):
        md = parse_metadata(written)
        _clean(md, repr(written))
        assert md.values == {"descr": "x"}, f"«{written}» came out as {md.values}"


def test_a_key_is_read_whatever_its_case():
    assert parse_metadata('@Label "x"').values == {"label": "x"}


def test_quotes_keep_a_sigil_inside_a_value():
    """A value is text, not a second line of metadata -- otherwise a note mentioning «@position» would be parsed."""
    md = parse_metadata('@note "voir @position T001 et @model"')
    _clean(md)
    assert md.values["note"] == "voir @position T001 et @model"


# --- ordinary prose -------------------------------------------------------------------------------


def test_an_ordinary_comment_is_kept_and_not_parsed():
    """The comments already in the engineer's model are pure prose, on five materials and four sections. An import reading the same field must not lose them."""
    md = parse_metadata("Eigenschaften manuel geändert")
    assert md.values == {}, f"prose is not metadata, got {md.values}"
    assert md.text == "Eigenschaften manuel geändert", f"the prose must come back as text, got {md.text!r}"
    _clean(md)


def test_prose_and_metadata_in_one_comment():
    md = parse_metadata('Gem. Lignatec 2021\n@model "VU-gunstig"\nAchtung! E-Modul geprüft')
    _clean(md)
    assert md.values == {"model": "VU-gunstig"}
    assert md.text == "Gem. Lignatec 2021\nAchtung! E-Modul geprüft", f"got {md.text!r}"


def test_an_empty_comment_holds_nothing():
    for empty in (None, "", "   ", "\n\n"):
        md = parse_metadata(empty)
        assert md.values == {} and md.text == "" and not md.problems, f"{empty!r} came out as {md!r}"
        assert not md, "an empty comment is falsy, so a caller can test it"


# --- what is reported, and never refused ----------------------------------------------------------


def test_an_invalid_width_is_reported_and_no_value_is_kept():
    """The engineer's own example of a bad value: «@be abc». A width that cannot be read must not reach a calculation as 0 or as text."""
    md = parse_metadata("@be abc")
    assert md.values == {}, f"nothing should be kept, got {md.values}"
    assert _codes(md) == ["rfem_meta_number"], f"got {[str(p) for p in md.problems]}"
    assert "abc" in str(md.problems[0]), "the report must quote what could not be read"


def test_a_width_in_an_unknown_unit_is_reported():
    md = parse_metadata("@be 5 Fuss")
    assert md.values == {}
    assert _codes(md) == ["rfem_meta_unit"], f"got {[str(p) for p in md.problems]}"


def test_an_unknown_key_is_reported_and_its_value_kept():
    """A typo must be named -- «@bee 1.5m» does nothing, and nobody would know. The value is kept so that nothing is lost while it is corrected."""
    md = parse_metadata("@bee 1.5m")
    assert _codes(md) == ["rfem_meta_unknown_key"], f"got {[str(p) for p in md.problems]}"
    assert md.values == {"bee": "1.5m"}, f"got {md.values} -- an unknown key has no known kind, so its value stays as written"
    assert "be" in str(md.problems[0]), "the report lists the valid keys, so the typo is obvious"


def test_a_key_given_twice_keeps_the_first_and_says_so():
    md = parse_metadata("@be 1.5m\n@be 2m")
    assert md.values["be"] == 1.5, "the first value is kept"
    assert _codes(md) == ["rfem_meta_duplicate"], f"got {[str(p) for p in md.problems]}"


def test_unclosed_quotes_are_reported():
    md = parse_metadata('@label "Velo Unterstand')
    assert md.values == {}
    assert _codes(md) == ["rfem_meta_quote"], f"got {[str(p) for p in md.problems]}"


def test_a_key_with_no_value_is_reported():
    md = parse_metadata("@be")
    assert md.values == {}
    assert _codes(md) == ["rfem_meta_empty"], f"got {[str(p) for p in md.problems]}"


def test_an_empty_quoted_value_is_a_value():
    """`@descr ""` says «no description», deliberately, and is not the same as forgetting the value."""
    md = parse_metadata('@descr ""')
    _clean(md)
    assert md.values == {"descr": ""}


def test_a_comment_full_of_mistakes_still_yields_what_it_can():
    """Nothing here refuses: one bad line must not cost the three good ones, or a typo would stop the export of sixty members."""
    md = parse_metadata('@model "VU-gunstig"\n@be abc\n@bee 2m\n@position "T001"\n@label Velo')
    assert md.values == {"model": "VU-gunstig", "bee": "2m", "position": "T001", "label": "Velo"}, f"got {md.values}"
    assert _codes(md) == ["rfem_meta_number", "rfem_meta_unknown_key"], f"got {[str(p) for p in md.problems]}"


# --- the shape of what comes back -----------------------------------------------------------------


def test_a_problem_is_a_note_the_window_can_translate():
    """Every problem carries a code and its arguments, so Woodcore writes its own sentence rather than parsing an English one back into parts (docs/typst/language.md §4bis, AUD-4-11)."""
    md = parse_metadata("@be abc", where="Member 24")
    problem = md.problems[0]
    assert isinstance(problem, engine.Note), f"a problem must be an engine.Note, got {type(problem)}"
    assert problem.code == "rfem_meta_number"
    assert problem.args["where"] == "Member 24" and problem.args["key"] == "be", f"got {problem.args}"
    assert "Member 24" in str(problem), f"the English sentence names the object: {problem}"


def test_where_names_the_object_in_every_report():
    md = parse_metadata("@be abc\n@bee 1m\n@be 2m", where="Node 15")
    assert all(p.args.get("where") == "Node 15" for p in md.problems), f"got {[p.args for p in md.problems]}"


def test_metadata_reads_as_a_mapping():
    md = parse_metadata('@be 1.5m\n@model "S1"')
    assert md["be"] == 1.5 and "model" in md and md.get("nothing") is None and len(md) == 2
    values, text, problems = md
    assert values == {"be": 1.5, "model": "S1"} and text == "" and problems == []


def test_every_key_declares_a_kind():
    """The contract the parser reads its own table by: a key added without one would be read as text whatever it holds."""
    for key, kind in KEYS.items():
        assert kind in ("text", "length"), f"«{key}» has the kind {kind!r}"


def test_the_length_units_are_metres_per_unit():
    assert metadata_parser.LENGTH_UNITS == {"mm": 0.001, "cm": 0.01, "m": 1.0}
    assert metadata_parser.DEFAULT_LENGTH_UNIT in metadata_parser.LENGTH_UNITS
