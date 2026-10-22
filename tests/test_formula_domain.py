"""A calculation domain of the «Formules» tab: its file, its keys, the formula typed, what it computes, how a report prints it, and its index (calc/domains/formula_domain.py; specs docs/requirements/completed/2026-10-08-onglet-formule-domaines.md and docs/requirements/completed/2026-10-08-onglet-formules-editeur-dossiers-include.md, issue #15).

What is held, requirement by requirement:

* REQ-005, REQ-014 (v0.117) and REQ-005, D-06, D-10 (issue #15) -- a domain is one `#domain("<id>", label: "<name>")`, printed by `#include "/Domains/<id>.typ"` with its title as a heading, and read further down with `#val(domain: "<id>")`;
* REQ-006 (issue #15) -- the engineer's own Typst between the commands, read back as typed, never computed; what Typst would compute and Python not, a tag line and unbalanced brackets refused before anything is written;
* REQ-004 (issue #15) -- the id is the file's name: an id changed renames the file and rewrites `#var-domain`, what cites the old one is listed; another id than the file's name is `misnamed`; a duplicate, an archive numbered rather than overwritten, a restore;
* REQ-006, ARCH-004, D-20 -- the file written reads back to the same model and the same bytes (`canonical`), a file written by hand in another form is `canonical` all the same and kept as written (since v0.119, ARCH-003 -- no state is `hand_edited` any more), one that does not parse `unreadable`; a write changes the body between the tags and nothing else; the tags are read by `structure.pair_tags`, and the ten commands of a document still refuse a positional argument;
* REQ-007, ARCH-003 -- a variable's call writes only what differs from the signature;
* REQ-008 -- a key made from the shown variable;
* REQ-009, D-17 -- `12 N / 3000 mm` typed is `(12 "N") / (3000 "mm")`, 4 N/m, and its output unit; an unknown unit refused;
* REQ-012 -- what the domain computes, and the reason a command the report would refuse is refused;
* REQ-015 -- a variable taken from the export or from another domain, a circle between two domains refused;
* a file changed on the disk since the domain was read is never written over by a save or a rename (`changed_on_disk`);
* the export: the index (2.0, by id), sorted, validated, seeded empty in a new project; two files declaring one `#var-domain`, and a file that cannot be read, stop it.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import conftest
from conftest import Skip

import project
import structure
import typst_objects
import units
import validation
from domains import formula_domain as fd

TYPST_ROOT = conftest.TYPST_ROOT
ROOT_CALC = conftest.ROOT / "calc"


def _domain(name="Poutre P1", fid="poutre-p1"):
    return fd.Domain(id=fid, name=name, commands=[
        fd.Command("var", key="q_d", value=4.5, unit="kN/m", options={"label": "Charge"}),
        fd.Command("var", key="l", value=5, unit="m"),
        fd.Command("eq", key="M_d", formula="q_d * l^2 / 8", unit="kNm"),
        fd.Command("var", key="M_Rd", symbol="M_(R,d)", value=20, unit="kNm", options={"level": 3}),
        fd.Command("verify", formula="M_d <= M_Rd"),
    ])


# --- keys and formulas -----------------------------------------------------------------------------

def test_a_key_is_made_from_the_shown_variable():
    assert fd.key_from_symbol("M_(y,d)") == "M_y_d"
    assert fd.key_from_symbol("gamma_M") == "gamma_M"
    assert fd.key_from_symbol("σ_(m,d)") == "sigma_m_d"
    assert fd.key_from_symbol("l_(k,y)") == "l_k_y"
    assert fd.key_from_symbol("F_Ed") == "F_Ed"
    # a key that reads as a unit is kept as typed (issue #32: lib/formula.typ leaves a quoted unit alone); a word a formula reads as an operation still takes _1
    assert [fd.key_from_symbol(s) for s in ("m", "l", "N", "M")] == ["m", "l", "N", "M"]
    assert [fd.key_from_symbol(s) for s in ("dot", "pi", "sqrt")] == ["dot_1", "pi_1", "sqrt_1"]
    assert fd.key_from_symbol("F_Ed", {"F_Ed"}) == "F_Ed_2" and fd.key_from_symbol("F_Ed", {"F_Ed", "F_Ed_2"}) == "F_Ed_3"
    for symbol in ("Δh", "2a", "max", "q_\"k,max\""):
        key = fd.key_from_symbol(symbol)
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) and "-" not in key and key not in ("max", "dot", "pi"), (symbol, key)
    # the symbol is written only where it is not the key itself (ARCH-RISK-107)
    assert fd.symbol_for("F_Ed", "F_Ed") == "" and fd.symbol_for("M_(y,d)", "M_y_d") == "M_(y,d)"


def test_a_formula_typed_is_written_as_eq_reads_it():
    names = [("q_d", ""), ("l", ""), ("M_y_d", "M_(y,d)")]
    assert fd.typst_formula("12 N / 3 m", names) == '(12 "N") / (3 "m")'
    assert fd.typst_formula("12 N/3000mm", names) == '(12 "N")/(3000 "mm")'
    assert fd.typst_formula("q_d * l^2 / 8", names) == "q_d * l^2 / 8"
    assert fd.typst_formula("M_(y,d) / 2,5 kNm", names) == 'M_y_d / (2.5 "kNm")'
    assert fd.typst_formula("1,35 × q_d", names) == "1.35 * q_d"
    assert fd.typst_formula("5 kN/m^2", names) == '(5 "kN/m²")'
    # and back, for the field it is edited in
    assert fd.display_formula('M_y_d / (2.5 "kNm")', names) == "M_(y,d) / 2.5 kNm"


def test_twelve_newtons_over_three_metres_or_three_thousand_millimetres_is_four_newtons_a_metre():
    for typed in ("12 N / 3 m", "12 N / 3000 mm"):
        q, _ops = units.evaluate("eq", fd.typst_formula(typed, []), {})
        assert abs(q.base - 4.0) < 1e-12 and q.dims == {"N": 1, "m": -1}, (typed, q)
        assert units.present("eq", "m", q, "N/mm")[:2] == (0.004, "N/mm")
        assert units.present("eq", "m", q, "N/m")[:2] == (4.0, "N/m")
    domain = fd.Domain("x", "X", [fd.Command("eq", key="m", formula=fd.typst_formula("12 Zork", []))])
    assert fd.compute(domain)[0].error, "a unit nobody can read was taken"


# --- the file ---------------------------------------------------------------------------------------

def test_the_file_reads_back_to_the_same_model_and_the_same_bytes():
    domain = _domain()
    text = fd.file_text(domain)
    # no tag since the unfolded checks (spec 2026-10-15, ARCH-006): the #var-domain call is what the file is found by
    assert "// woodcore:" not in text
    d = conftest.tmpdir("formula_file")
    path = d / "poutre-p1.typ"
    path.write_text(text, encoding="utf-8", newline="")
    read = fd.read(path)
    assert read.state == "canonical" and read.name == "Poutre P1" and read.id == read.declared == "poutre-p1", (read.state, read.problem)
    assert text.splitlines()[2] == '#domain("poutre-p1", label: "Poutre P1")['

    assert [(c.kind, c.key, c.symbol, c.value, c.unit, c.formula, c.options) for c in read.commands] == \
           [(c.kind, c.key, c.symbol, c.value, c.unit, c.formula, c.options) for c in domain.commands]
    assert fd.write_text(read) == text, "a domain written back unchanged changed its file"
    # the call writes what differs from the signature, and nothing else (ARCH-003)
    assert fd.to_call(fd.Command("var", key="R_k", value=7, unit="kN")) == '#var("R_k", 7, "kN")'
    assert fd.to_call(fd.Command("eq", key="M", formula="F * l")) == '#eq("M", `F * l`)'


def test_the_example_project_s_domain_reads_back_to_its_own_bytes():
    """REQ-006's criterion: the example's domain, written with no text between its commands, reads back canonical and is written back byte for byte."""
    path = conftest.ROOT / "tests" / "projet-exemple" / "Domains" / "poutre-p1.typ"
    read = fd.read(path)
    assert read.state == "canonical" and read.id == read.declared == "poutre-p1" and read.name == "Poutre P1", (read.state, read.problem)
    assert fd.write_text(read) == path.read_bytes().decode("utf-8")


def test_a_blank_line_beside_a_command_is_a_paragraph_and_is_kept():
    """D-05, D-07 (issue #40): a blank line beside a command -- after a text, before one, between two commands -- is Typst's paragraph and reads back as it was written, one at most, at the head or tail of the text, an empty text between two commands; blank lines at the start and the end of the body are none. Until then every one was left out, and two paragraphs ran into one. A file v0.117 wrote, with none, reads back to its own bytes."""
    d = conftest.tmpdir("formula_paragraphs")
    domain = fd.Domain(id="paragraphes", name="Paragraphes", commands=[
        fd.Command(fd.TEXT, raw="Kraft"), fd.Command("var", key="F", value=5, unit="kN"), fd.Command(fd.TEXT, raw="\nNeuer Absatz\n"),
        fd.Command("var", key="G", value=2, unit="kN"), fd.Command(fd.TEXT, raw=""), fd.Command("var", key="H", value=1, unit="kN")])
    text = fd.file_text(domain)
    body = text.split("[\n", 1)[1].split("\n]", 1)[0]
    assert body == 'Kraft\n  #var("F", 5, "kN")\n\nNeuer Absatz\n\n  #var("G", 2, "kN")\n\n  #var("H", 1, "kN")', body
    path = d / "paragraphes.typ"
    path.write_text(text, encoding="utf-8", newline="")
    read = fd.read(path)
    assert read.state == "canonical", (read.state, read.problem)
    assert [(c.kind, c.raw) for c in read.commands if c.is_text] == [(fd.TEXT, "Kraft"), (fd.TEXT, "\nNeuer Absatz\n"), (fd.TEXT, "")]
    assert fd.write_text(read) == text
    # two blank lines, written by hand: kept as written -- a form of the engineer's own is no longer rewritten (spec 2026-10-15, D-17, which reverses issue #40's «written back with one»)
    hand = text.replace('"kN")\n\nNeuer', '"kN")\n\n\nNeuer')
    path.write_text(hand, encoding="utf-8", newline="")
    read = fd.read(path)
    assert read.state == "canonical" and fd.write_text(read) == hand
    # the tidy form of what a tab hands over: no blank at the body's ends, two texts in a row one, an empty text only between two commands
    tidy = fd.tidy_items([fd.Command(fd.TEXT, raw="\n\nA\n"), fd.Command(fd.TEXT, raw="B\n\n\n"), fd.Command("var", key="F", value=1),
                          fd.Command(fd.TEXT, raw="\n\n"), fd.Command(fd.TEXT, raw="")])
    assert [(c.kind, c.raw) for c in tidy] == [(fd.TEXT, "A\n\nB\n"), ("var", "")], [(c.kind, c.raw) for c in tidy]


def test_plain_spans_names_the_lines_a_command_may_stand_on():
    """ARCH-004 (issue #40): the lines that begin in the body's own markup -- not inside an equation, a raw block, a string or a call."""
    markup = "Text\n$ a +\nb $\n```\nraw\n```\n#f(\n1)\nEnd"
    starts = [0] + [i + 1 for i, c in enumerate(markup) if c == "\n"]
    plain = fd.plain_spans(markup)
    lines = markup.split("\n")
    assert [lines[starts.index(o)] for o in plain] == ["Text", "$ a +", "```", "#f(", "End"], [lines[starts.index(o)] for o in plain]


def _layout_case():
    F = fd.Command("var", key="F", value=5, unit="kN")
    G = fd.Command("var", key="G", value=2, unit="kN", options={"label": "Gewicht"})
    M = fd.Command("eq", key="M", formula="F * 2")
    V = fd.Command("verify", formula="M <= F")
    return F, G, M, V


def test_the_pane_joins_a_command_printed_inline_into_its_sentence_and_reads_back():
    """REQ-002, REQ-003, ARCH-004 (issue #40): a text line, a command printed inline and the next line are one paragraph of the pane -- one sentence for Typst --, a blank line beside it the paragraph break, a heading, a command on a line of its own (`note: "line"`, `verify`) and a text's own lines a paragraph each; the pane's paragraphs give back the same items."""
    from domains import formula_layout as fl
    F, G, M, V = _layout_case()
    items = [fd.Command(fd.TEXT, raw="= Titre\nKraft"), F, fd.Command(fd.TEXT, raw="und danach"), M,
             fd.Command(fd.TEXT, raw="\nNeuer Absatz"), G, fd.Command(fd.TEXT, raw="Satz $a +\nb$ Ende"), V, fd.Command(fd.TEXT, raw="Schluss")]
    paragraphs = fl.to_paragraphs(items)
    shape = [[v if k == "text" else "#" + v.key for k, v in p] for p in paragraphs]
    assert shape == [["= Titre"], ["Kraft ", "#F", " und danach ", "#M"], ["Neuer Absatz ", "#G"], ["Satz $a +"], ["b$ Ende"], ["#", " Schluss"]], shape
    back = fl.from_paragraphs(paragraphs)
    assert [(c.kind, c.raw) for c in back] == [(c.kind, c.raw) for c in fd.tidy_items(items)], [(c.kind, c.raw) for c in back]
    assert fl.to_paragraphs(back) == paragraphs
    # Enter beside a pill is a new paragraph: the blank line that keeps the two apart for Typst (D-05)
    split = [[("text", "Kraft")], [("cmd", F), ("text", " und")]]
    written = fl.from_paragraphs(split)
    assert [(c.kind, c.raw) for c in written] == [("text", "Kraft\n"), ("var", ""), ("text", "und")], [(c.kind, c.raw) for c in written]
    assert fl.to_paragraphs(written) == [[("text", "Kraft")], [("cmd", F), ("text", " und")]]
    # two pills side by side are one sentence, a space between them; the v0.117 example reads into paragraphs and back unchanged
    assert fl.to_paragraphs([F, M]) == [[("cmd", F), ("text", " "), ("cmd", M)]]
    example = fd.read(conftest.ROOT / "tests" / "projet-exemple" / "Domains" / "poutre-p1.typ")
    # the body below its header: a domain made anew writes `#domain` (spec 2026-10-21-commandes-typst-refonte, REQ-008), the example's file keeps the `#var-domain` it was written with
    rebuilt = fd.body_of(fd.Domain(id=example.id, name=example.name, commands=fl.from_paragraphs(fl.to_paragraphs(example.commands))))
    assert rebuilt.split("\n", 1)[1] == fd.body_of(example).split("\n", 1)[1]


def test_a_pill_is_refused_where_it_would_change_the_text_or_its_reading():
    """REQ-004, D-06 (issue #40): no drop inside a heading, an equation, a raw block or a call (a string being one's); any other place of a sentence is one -- quotes in markup are words."""
    from domains import formula_layout as fl
    F, _G, _M, _V = _layout_case()
    paragraphs = [[("text", "= Titre")], [("text", "Kraft $a + b$ und `raw` ")], [("text", "Mit #f(1, 2) Ende")], [("text", "Ein \"string\" hier")]]
    assert fl.drop_refusal(paragraphs, (0, 0, 3))[0] == "apart"
    assert fl.drop_refusal(paragraphs, (1, 0, 5)) is None
    assert fl.drop_refusal(paragraphs, (1, 0, 9))[0] == "inside"
    assert fl.drop_refusal(paragraphs, (1, 0, 14)) is None
    assert fl.drop_refusal(paragraphs, (1, 0, 21))[0] == "inside"
    assert fl.drop_refusal(paragraphs, (2, 0, 8))[0] == "inside"
    assert fl.drop_refusal(paragraphs, (2, 0, 13)) is None
    assert fl.drop_refusal(paragraphs, (3, 0, 7)) is None, "quotes in markup are words, not a string"


def test_a_file_written_by_hand_is_kept_as_written_and_one_that_cannot_be_read_is_never_rewritten():
    """ARCH-003, ARCH-006, D-17 (spec 2026-10-15, reversing issue #15's canonical rewrite): a domain written by hand -- a call's spaces, a comment after it, an argument over two lines, CRLF, a word before the call, the tag of the old files -- is read as it is and written back byte for byte; changing a command changes the arguments that changed and nothing else -- an option changed, added or taken away in a call over two lines included. A file whose call cannot be read is never rewritten."""
    d = conftest.tmpdir("formula_hand")
    text = fd.file_text(_domain()).replace('  #var("l", 5, "m")', '  #var( "l" ,  5, "m")  // the span').replace(
        '  #var("q_d", 4.5, "kN/m", label: "Charge")', '  #var("q_d", 4.5, "kN/m",\n       label: "Charge")')
    assert '"kN/m",\n       label' in text
    # an old file: a word of the engineer's and the tag around the call, CRLF
    old = text.replace('#domain(', '// a word of the engineer\'s\n// woodcore:object formula-domain domain\n#domain(', 1) + "// woodcore:/object domain\n"
    crlf = old.replace("\n", "\r\n")
    path = d / "poutre-p1.typ"   # its own id: a file named otherwise is the one case still written back (another id than its file's name)
    path.write_bytes(crlf.encode("utf-8"))
    read = fd.read(path)
    assert read.state == "canonical" and len([c for c in read.commands if not c.is_text]) == 5, (read.state, read.problem)
    assert fd.STATES == ("canonical", "misnamed", "unreadable"), "a form of the engineer's own is no state any more (ARCH-006)"
    assert fd.write_text(read) == crlf, "a domain written back unchanged changed its file"
    # one value changed: that value alone is replaced -- the call's spaces and its comment stay (ARCH-003)
    changed = [fd.replace(c, value=6) if c.key == "l" else c for c in read.commands]
    written = fd.write_text(fd.replace(read, commands=changed))
    assert written == crlf.replace('  #var( "l" ,  5, "m")  // the span', '  #var( "l" ,  6, "m")  // the span'), written
    assert '#var("q_d", 4.5, "kN/m",\r\n       label: "Charge")' in written, "a call written over two lines and not changed was rewritten"
    # in a call over two lines: an option changed, one added and one taken away -- each argument alone, the line break kept
    q = next(c for c in read.commands if c.key == "q_d")
    for options, line in (({"label": "Last"}, '  #var("q_d", 4.5, "kN/m",\r\n       label: "Last")'),
                          ({"label": "Charge", "role": "result"}, '  #var("q_d", 4.5, "kN/m",\r\n       label: "Charge", role: "result")'),
                          ({}, '  #var("q_d", 4.5, "kN/m")')):
        changed = [fd.replace(c, options=options) if c is q else c for c in read.commands]
        written = fd.write_text(fd.replace(read, commands=changed))
        assert written == crlf.replace('  #var("q_d", 4.5, "kN/m",\r\n       label: "Charge")', line), (options, written)
        assert '#var( "l" ,  5, "m")  // the span' in written
    broken = d / "b.typ"
    broken.write_text(fd.file_text(_domain()).replace("#verify(`M_d <= M_Rd`)", "#verify(`M_d <= M_Rd`"), encoding="utf-8")
    read = fd.read(broken)
    assert read.state == "unreadable" and read.problem
    # no tag at all: read as any domain
    untagged = d / "c.typ"
    untagged.write_text('#domain("c")[]\n', encoding="utf-8")
    assert fd.read(untagged).state == "canonical"
    # no call: unreadable, and never rewritten
    empty = d / "e.typ"
    empty.write_text('Nothing here\n', encoding="utf-8")
    assert fd.read(empty).state == "unreadable"
    try:
        fd.write_text(fd.Domain("e", "X", [], path=empty, text=empty.read_text(encoding="utf-8")))
    except fd.DomainError as exc:
        assert exc.code == "unreadable"
    else:
        raise AssertionError("a file with no #domain call was rewritten")


def test_a_value_beside_domain_is_read_and_written_back():
    """REQ-001, REQ-003, D-14 on the Python side: `#var(key, value, unit, domain: …)` reads as a literal checked by domain: -- its value computed with, written back as it was --; an unfolded check's header carries `gen:` and its check's id as it is (`ZT-01`)."""
    d = conftest.tmpdir("formula_unfolded")
    path = d / "ZT-01.typ"
    path.write_text('#import "/000-Typst-Config/commands.typ": *\n\n#domain("ZT-01", label: "Zug")[\n'
                    '  #var("N_t_d", "N_(t,d)", 25, "kN", domain: ("check", "ZT-01"))\n  #var("A", 20000, "mm²")\n'
                    '  #eq("sigma", `N_t_d / A`, unit: "N/mm²")\n  #verify(`sigma <= 9 "N/mm²"`, id: "v-6")\n]\n', encoding="utf-8", newline="\n")
    read = fd.read(path)
    assert read.state == "canonical", (read.state, read.problem)
    n = read.commands[0]
    assert (n.value, n.unit, n.source) == (25, "kN", ("domain", ("check", "ZT-01")))
    assert fd.to_call(n) == '#var("N_t_d", "N_(t,d)", 25, "kN", domain: ("check", "ZT-01"))'
    assert read.commands[3].options == {"id": "v-6"}
    assert abs(fd.compute(read)[2].value - 1.25) < 1e-9, "a literal beside domain: is computed with as written"
    assert fd.write_text(read) == path.read_text(encoding="utf-8")
    assert fd.header_of(read) == '#domain("ZT-01", label: "Zug")['
    fd.check_id("ZT-01", [], unfolded=True)
    try:
        fd.check_id("ZT-01", [])
    except fd.DomainError as exc:
        assert exc.code == "id_invalid"
    else:
        raise AssertionError("a check's id was taken for a hand-written domain's")


def test_a_file_changed_on_the_disk_since_it_was_read_is_never_written_over():
    # the lines written in VS Code (or by an engine synced) while the tab held the domain were dropped by its next save: the domain held is older than the file
    here = conftest.project_copy("formula_changed_on_disk", data=True)
    held = fd.save(here, _domain("Poutre P1", "poutre-p1"))
    path = here.formulas_dir / "poutre-p1.typ"
    elsewhere = path.read_text(encoding="utf-8").replace('  #var("l", 5, "m")', '  #var("l", 5, "m")\n  #var("b", 120, "mm")')
    path.write_text(elsewhere, encoding="utf-8", newline="")
    held.commands = held.commands[:-1]   # a change made in the tab on the domain as it was read
    for attempt in (lambda: fd.save(here, held), lambda: fd.rename(here, held, "p2")):
        try:
            attempt()
        except fd.DomainError as exc:
            assert exc.code == "changed_on_disk", exc.code
        else:
            raise AssertionError("a domain older than its file was written over it")
        assert path.read_text(encoding="utf-8") == elsewhere and not (here.formulas_dir / "p2.typ").exists(), "the file changed elsewhere was touched"
    fresh = fd.read(path)
    assert any(c.key == "b" for c in fresh.commands if not c.is_text)
    assert fd.save(here, fresh).state == "canonical"   # read again, it saves
    try:
        fd.save(here, fd.Domain(id="poutre-p1", name="Autre", path=path))   # never read: may not take the place of a file that is there
    except fd.DomainError as exc:
        assert exc.code == "changed_on_disk"
    else:
        raise AssertionError("a domain never read was written over an existing file")


def test_a_document_command_still_refuses_a_positional_argument():
    for body in ('#doc-table("x")', "#doc-field(label: [x])[y]"):
        try:
            typst_objects.parse_call(body)
        except typst_objects.ParseError:
            continue
        raise AssertionError(f"{body} was read: the positional reading is a domain's alone")


# --- what it computes -----------------------------------------------------------------------------

def test_the_domain_computes_at_once_and_refuses_what_the_report_would():
    results = fd.compute(_domain())
    assert [r.error for r in results] == [""] * 5
    assert (results[2].value, results[2].unit) == (14.0625, "kNm")
    assert results[4].holds is True and results[4].op == "<="
    assert results[2].letters == "q_d dot l^2 / 8" and results[2].numbers == '"4.5 kN/m" dot "5 m"^2 / 8'
    assert [row[0] for row in fd.variables_of(_domain(), results)] == ["q_d", "l", "M_d", "M_Rd"]
    bad = fd.Domain("x", "X", [fd.Command("var", key="F", value=1, unit="kN"), fd.Command("var", key="l", value=2, unit="m"),
                               fd.Command("eq", key="s", formula="F + l"), fd.Command("eq", key="t", formula="F * nobody"),
                               fd.Command("verify", formula="F <= l"), fd.Command("eq", key="u", formula="sqrt(F)")])
    errors = [r.error for r in fd.compute(bad)]
    assert errors[:2] == ["", ""]
    assert "cannot add" in errors[2] and "nobody" in errors[3] and "comparing" in errors[4] and "sqrt" in errors[5], errors


def test_a_variable_taken_from_elsewhere_reads_its_value_there_and_a_circle_is_refused():
    here = project.current()
    calcs = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
    ce = calcs["domains"]["snow-load"]["instances"]["SL"]["vars"]["ce"]
    a = fd.Domain("a", "A", [fd.Command("var", key="ce", source=("var-of", 'var-of("snow-load", "SL", "ce")')),
                             fd.Command("var", key="x", value=2, unit="m")])
    # another domain of the tab is named by its id (D-06)
    b = fd.Domain("b", "B", [fd.Command("var", key="x", source=("domain", "a")), fd.Command("eq", key="y", formula="x * 2")])
    domains = [a, b]
    resolve = lambda c: fd.resolve_import(here, c, domains)   # noqa: E731
    got = fd.compute(a, resolve)
    assert got[0].value == ce["value"] and not got[0].error
    got = fd.compute(b, resolve)
    assert (got[1].value, got[1].unit) == (4, "m") or (abs(got[1].value - 4000) < 1e-9 and got[1].unit == "mm"), got[1]
    a.commands.append(fd.Command("var", key="z", source=("domain", "b")))
    b.commands.insert(0, fd.Command("var", key="z", source=("domain", "a")))
    circled = fd.compute(b, lambda c: fd.resolve_import(here, c, domains))
    assert fd.CIRCLE in circled[0].error, circled[0]
    assert fd.compute(fd.Domain("c", "C", [fd.Command("var", key="q", source=("domain", "Nowhere"))]), resolve)[0].error


# --- the engineer's own Typst between the commands (REQ-006, issue #15) ----------------------------

_TEXT_BODY = """#domain("x", label: "Essai")[
= Titre
La charge :
  #var("F", 5, "kN")
$ M = F l $
Le moment #val("F") vaut.
```
#var("Z", 1)
```
  #eq("M", `F * 2`)
// un commentaire
  #val("M")
]"""


def test_text_between_the_commands_reads_back_as_typed_and_is_never_computed():
    declared, title, items = fd.parse_body(_TEXT_BODY)
    assert (declared, title) == ("x", "Essai")
    assert [c.kind for c in items] == ["text", "var", "text", "eq", "text"]
    assert items[0].raw == "= Titre\nLa charge :"
    # a `#val` in a sentence -- a command retired, the export says (REQ-020) -- and a `#var` inside a raw block: text, as Typst reads them
    assert '#val("F") vaut' in items[2].raw and '#var("Z", 1)' in items[2].raw
    domain = fd.Domain(id="x", name="Essai", commands=items)
    assert fd.body_of(domain) == _TEXT_BODY, "a body with text did not write back to its own bytes"
    results = fd.compute(domain)
    assert len(results) == len(items) and results[0] == fd.Result() and (results[3].value, results[3].unit) == (10, "kN")
    assert [row[0] for row in fd.variables_of(domain, results)] == ["F", "M"]
    d = conftest.tmpdir("formula_text")
    path = d / "x.typ"
    path.write_text(fd.file_text(domain), encoding="utf-8")
    back = fd.read(path)
    assert back.state == "canonical" and [c.kind for c in back.commands] == [c.kind for c in items], (back.state, back.problem)


def test_what_a_text_may_not_hold_is_refused_and_nothing_is_written():
    # a computing command typed into a text of the pane is refused there: the pane makes it a pill
    for bad, code in (('Texte #var("Q", 1)', "text_command"), ("$ #eq(\"A\", `1`) $", "text_command"),
                      ('#var("Q", 1) ;', "text_command"), ('#box[#var("Q", 1)]', "text_command"),
                      ("// woodcore:object x y", "text_tag"), ("texte ] fin", "text_unbalanced")):
        domain = fd.Domain(id="x", name="E", commands=[fd.Command("text", raw=bad)])
        try:
            fd.write_text(domain)
        except fd.DomainError as exc:
            assert exc.code == code, (bad, exc.code)
        else:
            raise AssertionError(f"{bad!r} was written")
    # a hand-written file holding a computing command Python cannot cut out of its text cannot be read: Typst and Python would disagree
    d = conftest.tmpdir("formula_text_bad")
    path = d / "x.typ"
    for held in ('Texte #box[#eq("A", `1`)] ici', '#var("A", 1)[x]', '#var("A", 1).x', '$ #var("A", 1) $'):
        path.write_text(fd.file_text(fd.Domain(id="x", name="E")).replace('[\n]', '[\n' + held + '\n]'), encoding="utf-8")
        read = fd.read(path)
        assert read.state == "unreadable" and "#" in read.problem, (held, read.state)
    # `#var(...) ;`, refused until spec 2026-10-14-commandes-en-ligne-domaine (`text_trailing`), is a command glued to the text after it
    path.write_text(fd.file_text(fd.Domain(id="x", name="E")).replace('[\n]', '[\n  #var("b", 208, "mm") ;\n  #var("t", 8.5, "mm")\n]'), encoding="utf-8")
    read = fd.read(path)
    assert read.state == "canonical" and [(c.kind, c.raw, c.glued_after) for c in read.commands] == [("var", "", True), ("text", " ;", False), ("var", "", False)], (read.state, read.problem)


# --- commands written inside a line (spec 2026-10-14-commandes-en-ligne-domaine) ---------------------

_INLINE_BODY = """#domain("x", label: "Inline")[
  #var("b", 2, "m")

  #var("ak", 3, "kN/m") --- Auflast

- $0°$ bis $30°$: #eq("g_1", "g_(d,1)", `b*ak`)
    - Unter: #var("c", "c_(pe)", -1) $=>$ au besoin
Zwei: #var("x1", 1) #var("x2", 2) Ende
]"""


def test_a_command_written_inside_a_line_is_read_computed_and_written_back_on_its_line():
    """REQ-001, REQ-003, D-02: a computing command after a list's marker, before a text, or two on one line is a command, glued to what is beside it; it is computed, and the file is written back to its own bytes -- the command still in its list's item."""
    items = fd.split_items(_INLINE_BODY[_INLINE_BODY.index("[") + 1:-1])
    shape = [(c.kind, c.raw) if c.is_text else (c.key, c.glued_before, c.glued_after) for c in items]
    assert shape == [("b", False, False), ("text", ""), ("ak", False, True), ("text", " --- Auflast\n\n- $0°$ bis $30°$: "),
                     ("g_1", True, False), ("text", "    - Unter: "), ("c", True, True), ("text", " $=>$ au besoin\nZwei: "),
                     ("x1", True, True), ("text", " "), ("x2", True, True), ("text", " Ende")], shape
    domain = fd.Domain(id="x", name="Inline", commands=items)
    assert fd.body_of(domain) == _INLINE_BODY, fd.body_of(domain)
    results = fd.compute(domain)
    g = results[[c.key for c in items].index("g_1")]
    assert (g.value, g.error) == (6, ""), g
    path = conftest.tmpdir("formula_inline") / "x.typ"
    path.write_text(fd.file_text(domain), encoding="utf-8", newline="")
    read = fd.read(path)
    assert read.state == "canonical", (read.state, read.problem)
    assert fd.write_text(read) == path.read_text(encoding="utf-8")
    # an option changed on a glued command keeps it on its line; one moved to a line of its own is written there
    read.commands[2].options["label"] = "Auflast"
    assert '  #var("ak", 3, "kN/m", label: "Auflast") --- Auflast\n' in fd.write_text(read)
    read.commands[2].glued_after = False
    assert '  #var("ak", 3, "kN/m", label: "Auflast")\n --- Auflast\n' in fd.write_text(read)


def test_the_pane_keeps_a_command_written_inside_a_line_in_its_paragraph():
    """UI-001, D-02: the pane shows a glued command in the paragraph of the text beside it -- a list's item included, which `_joins` alone would part -- and its paragraphs give back the same items; a glued command moved to the start of a paragraph is glued to nothing before it."""
    from domains import formula_layout as fl
    items = fd.split_items(_INLINE_BODY[_INLINE_BODY.index("[") + 1:-1])
    paragraphs = fl.to_paragraphs(items)
    shape = [[v if k == "text" else "#" + v.key for k, v in p] for p in paragraphs]
    assert shape == [["#b"], ["#ak", "  --- Auflast"], [], ["- $0°$ bis $30°$:  ", "#g_1"], ["    - Unter:  ", "#c", "  $=>$ au besoin"],
                     ["Zwei:  ", "#x1", "   ", "#x2", "  Ende"]], shape
    back = fl.from_paragraphs(paragraphs)
    assert [fd.item_key(c) for c in back] == [fd.item_key(c) for c in items]
    c = next(i for i in items if i.key == "c")
    moved = fl.from_paragraphs(paragraphs[:4] + [[("text", "    - Unter:")], [("cmd", c), ("text", "  $=>$ au besoin")]] + paragraphs[5:])
    assert not c.glued_before and c.glued_after
    assert "    - Unter:\n  #var(\"c\", \"c_(pe)\", -1) $=>$ au besoin\n" in fd.body_of(fd.Domain(id="x", name="Inline", commands=moved))


def test_a_project_whose_domains_hold_commands_inside_lines_exports():
    """REQ-002: the export (formula_domain.prepare) reads such a domain -- the `export_failed` of one of the engineer's projects, 14.10.2026 --, and that project's domains folder, where `WOODCORE_INLINE_DOMAINS` names it on this machine, reads its every domain on a copy (CON-002). The folder is named by the environment, never written here: the repository names none of the engineer's projects (tests/test_no_third_party_name.py)."""
    here = conftest.project_copy("formula_inline_export", data=True)
    folder = here.formulas_dir
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "x.typ").write_text(fd.file_text(fd.Domain(id="x", name="Inline", commands=fd.split_items(_INLINE_BODY[_INLINE_BODY.index("[") + 1:-1]))), encoding="utf-8")
    data, _notes = fd.prepare(here)
    assert "x" in data["domains"], data
    named = os.environ.get("WOODCORE_INLINE_DOMAINS")
    dome = Path(named) if named else None
    if dome is None or not dome.is_dir():
        return
    copy = conftest.tmpdir("formula_inline_dome")
    for f in sorted(dome.glob("*.typ")):
        shutil.copy(f, copy / f.name)
        read = fd.read(copy / f.name)
        assert read.state != "unreadable", (f.name, read.problem)
        written = fd.write_text(read)
        (copy / f.name).write_text(written, encoding="utf-8", newline="")
        again = fd.read(copy / f.name)
        assert [fd.item_key(c) for c in again.commands] == [fd.item_key(c) for c in read.commands] and fd.write_text(again) == written, f.name


# --- the id is the file's name (REQ-004, issue #15) -------------------------------------------------

def test_another_id_than_the_file_s_name_is_misnamed_and_written_back_under_its_own():
    d = conftest.tmpdir("formula_declared")
    path = d / "copie.typ"
    path.write_text(fd.file_text(_domain()), encoding="utf-8")      # poutre-p1's text, copied under another name
    read = fd.read(path)
    assert read.id == "copie" and read.declared == "poutre-p1" and read.state == "misnamed"
    assert '#domain("copie", label: "Poutre P1")[' in fd.write_text(read)


def test_an_id_changed_renames_the_file_and_lists_what_cites_the_old_one():
    here = conftest.project_copy("formula_rename", data=True)
    domain = fd.save(here, _domain("Renommé", "renomme"))
    fd.save(here, _domain("Autre", "autre"))
    section = here.typst_root / "probe-section.typ"
    section.write_text('#include "/Domains/renomme.typ"\nM = #val("M_d", domain: "renomme")\n', encoding="utf-8")
    for bad, code in (("P 2", "id_invalid"), ("Poutre", "id_invalid"), ("autre", "id_taken")):
        try:
            fd.rename(here, domain, bad)
        except fd.DomainError as exc:
            assert exc.code == code, (bad, exc.code)
        else:
            raise AssertionError(f"{bad!r} was taken as an id")
    assert (here.formulas_dir / "renomme.typ").is_file()
    renamed, cited = fd.rename(here, domain, "p2")
    assert not (here.formulas_dir / "renomme.typ").exists() and (here.formulas_dir / "p2.typ").is_file()
    assert renamed.id == renamed.declared == "p2" and renamed.state == "canonical" and renamed.name == "Renommé"
    assert [(f, n) for f, n, _line in cited] == [("probe-section.typ", 1), ("probe-section.typ", 2)], cited
    assert "p2" in json.loads((here.data_dir / fd.EXPORT_FILE).read_text(encoding="utf-8"))["domains"]
    assert "renomme.typ" in section.read_text(encoding="utf-8"), "a section was rewritten (D-11: listed, never rewritten)"


def test_a_domain_is_duplicated_archived_without_overwriting_and_restored():
    here = conftest.project_copy("formula_archive", data=True)
    domain = fd.save(here, _domain("Original", "original"))
    copy = fd.duplicate(here, domain, "Original (copie)")
    assert copy.id == "original-copie" and copy.name == "Original (copie)" and copy.state == "canonical"
    assert [fd.to_call(c) for c in copy.commands] == [fd.to_call(c) for c in domain.commands]
    first = fd.remove(here, copy)
    again = fd.duplicate(here, domain, "Original (copie)")
    second = fd.remove(here, again)
    assert first != second and first.is_file() and second.is_file(), "a second removal in the same second overwrote the first"
    keys = [key for key, _d in fd.archived(here)]
    assert first.name in keys and second.name in keys
    restored = fd.restore(here, first.name)
    assert restored.id == "original-copie" and (here.formulas_dir / "original-copie.typ").is_file() and not first.exists()
    restored2 = fd.restore(here, second.name)
    assert restored2.id == "original-copie-2" and restored2.declared == "original-copie-2"
    fd.purge(here, "nothing-there.typ")
    assert {d.id for d in fd.list_domains(here)} >= {"original", "original-copie", "original-copie-2"}


def _compile(name, source, fmt="svg"):
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir(name)
    doc = d / "probe.typ"
    doc.write_text('#import "/000-Typst-Config/commands.typ": *\n' + source, encoding="utf-8")
    out = d / ("probe-{n}." + fmt)
    r = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(doc), str(out)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r, sorted(d.glob("probe-*." + fmt))


def test_include_prints_the_domain_with_its_title_and_var_reads_it_by_its_id():
    """REQ-005 (issue #15): `#include "/Domains/<id>.typ"` prints the domain where it stands -- its title a heading under the section's --, and `#var(key, domain: "<id>")` reads a value it computes."""
    r, _pages = _compile("formula_include", '= Section\n#include "/Domains/poutre-p1.typ"\nM = #var("M_d", domain: "poutre-p1", level: 1)\n', "pdf")
    assert r.returncode == 0, r.stderr
    r, pages = _compile("formula_include_svg", '= Section\n#include "/Domains/poutre-p1.typ"\n')
    assert r.returncode == 0, r.stderr
    # the same page as the domain's body written in the section by hand: the include prints its title and its five commands, nothing more, nothing less
    domain = next(d for d in fd.list_domains(project.current()) if d.id == "poutre-p1")
    assert len([c for c in domain.commands if not c.is_text]) == 5
    r2, written = _compile("formula_include_inline", '= Section\n' + fd.body_of(domain) + "\n")
    assert r2.returncode == 0, r2.stderr
    strip = lambda p: re.sub(r'id="[^"]*"|href="#[^"]*"', "", p.read_text(encoding="utf-8"))   # noqa: E731 -- glyph ids differ, what is drawn does not
    assert [strip(p) for p in pages] == [strip(p) for p in written], "#include printed something else than the domain"
    assert fd.include_call(fd.Domain(id="poutre-p1", name="Poutre P1")) == '#include "/Domains/poutre-p1.typ"'


# --- the export ------------------------------------------------------------------------------------

def test_the_index_is_sorted_validated_and_seeded_and_two_files_of_one_name_stop_it():
    here = conftest.project_copy("formula_index", data=True)
    folder = here.formulas_dir
    folder.mkdir(parents=True, exist_ok=True)
    for name, fid in (("Zeta", "zeta"), ("Alpha", "alpha")):
        (folder / f"{fid}.typ").write_text(fd.file_text(_domain(name, fid)), encoding="utf-8")
    data, notes = fd.prepare(here)
    assert list(data["domains"]) == ["alpha", "zeta"], list(data["domains"])
    assert data["domains"]["alpha"] == {"title": "Alpha", "file": "Domains/alpha.typ"} and data["schema_version"] == "2.0"
    assert not notes
    validation.validate_structure(data, "formulas")
    wrong = dict(data, schema_version="1.0")
    try:
        validation.validate_structure(wrong, "formulas")
    except validation.ValidationError as exc:
        assert "schema_version" in str(exc), str(exc)
    else:
        raise AssertionError("an index of 1.0 was taken for 2.0")
    # two files may bear one name (the id tells them apart), never declare one #var-domain
    (folder / "other.typ").write_text(fd.file_text(_domain("Alpha", "other")), encoding="utf-8")
    assert fd.prepare(here)[0]["domains"]["other"]["title"] == "Alpha"
    (folder / "other.typ").write_text(fd.file_text(_domain("Alpha", "alpha")), encoding="utf-8")
    try:
        fd.prepare(here)
    except validation.ValidationError as exc:
        assert "alpha.typ" in str(exc) and "other.typ" in str(exc)
    else:
        raise AssertionError("two files declaring one domain were exported")
    (folder / "other.typ").write_text("// woodcore:object formula-domain domain\n#var-domain(\n// woodcore:/object domain\n", encoding="utf-8")
    try:
        fd.prepare(here)
    except validation.ValidationError as exc:
        assert "other.typ" in str(exc)
    else:
        raise AssertionError("a domain that cannot be read was exported")
    # another file of Formules/ that stops the index never makes a save fail: the file is written and the reason given back, never raised (an «Erreur inattendue» in the window)
    saved = fd.save(here, _domain("Beta", "beta"))
    assert (folder / "beta.typ").is_file() and saved.state == "canonical"
    assert "other.typ" in saved.index_problem, saved.index_problem
    assert fd.save(here, fd.read(folder / "beta.typ")).index_problem != ""   # still said while other.typ is broken
    import export_all
    seeded = conftest.tmpdir("formula_seed")
    fresh = project.write(seeded / "N.woodcore", "N")
    shutil.rmtree(fresh.data_dir, ignore_errors=True)
    assert fd.EXPORT_FILE in export_all.seed(fresh)
    assert json.loads((fresh.data_dir / fd.EXPORT_FILE).read_text(encoding="utf-8")) == fd.empty()


# --- the verification's first round (spec §15): what was realised and not proved ------------------

def _levels_domain():
    """A domain with every command of the palette and a command stating its own level -- saved into this process's copy of the example, so that `#include` finds it."""
    domain = fd.Domain(id="niveaux", name="Niveaux", commands=[
        fd.Command("var", key="F", value=12, unit="kN"),
        fd.Command("var", key="l_1", symbol="l", value=3, unit="m", options={"level": 3}),
        fd.Command("eq", key="M", formula="F * l_1", unit="kNm"),
        fd.Command("var-unit", key="F", unit="N"),
        fd.Command("val", key="M"),
        fd.Command("verify", formula='M <= 100 "kNm"'),
    ])
    here = project.current()
    existing = next((d for d in fd.list_domains(here) if d.id == "niveaux"), None)
    if existing is None:
        fd.save(here, domain)
    return next(d for d in fd.list_domains(here) if d.id == "niveaux")


def test_the_domain_modules_import_without_qt():
    """ARCH-001: the domain, the algebra and the Greek names are Qt-free -- what the export and a test without a window import."""
    import sys
    code = ("import sys; sys.modules['PySide6'] = None; sys.path[:0] = [r'%s', r'%s']\n"
            "from domains import formula_domain, formula_layout; import units, greek; print('ok')") % (ROOT_CALC, ROOT_CALC / "tools")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr



def test_an_answer_given_another_unit_without_conversion_keeps_its_number_and_says_so():
    """Spec 2026-10-21-commandes-typst-refonte, REQ-003, Q-004: `as-unit:` gives the answer another unit without converting it -- the number kept -- and the window says so beside the line, never the report."""
    _declared, _title, items = fd.parse_body('#domain("x", label: "X")[\n  #var("M_d", 4.2, "kNm")\n  #eq("q", `M_d / (100 "mm")`, as-unit: "kN/m")\n]')
    results = fd.compute(fd.Domain(id="x", name="X", commands=items))
    q = results[-1]
    assert q.error in (None, "") and q.unit == "kN/m" and q.warning and q.warning["as_unit"] and q.warning["wanted"] == "kN/m", q
    assert abs(q.value - 42) < 1e-9, "4.2 kNm over 100 mm is 42 kN, the number kept"
