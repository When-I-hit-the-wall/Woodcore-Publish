"""A member's checks written in keyword lines, and the Typst they come to (calc/dsl.py, calc/tools/dsl_tab.py; v0.100, docs/domain/member-checks.md §3.3septdecies).

The engineer asked for «un onglet où le user peut écrire des formules de manières simples, non formatées en typst», was offered an AI for it and refused it, and agreed a **deterministic parser** suffices. So what is held here is what a parser gives and a model cannot: the same lines always give the same Typst, and a line outside the grammar is **refused naming the line** and listing what is understood.

⚠️ The check that matters most is the last one: **what the parser writes compiles**, and compiles to a page with the member's own name on it. A translator whose output does not compile is worse than no translator.
"""

import conftest

import dsl


def test_the_engineers_own_words_are_read():
    """His own example, in his own wording -- «Fais la vérification à: la compression» -- reaches the same checks as the short form, and a block is a position and everything written under it until the next one."""
    blocks, problems = dsl.parse('''# Halle Nord
Position: S001
N: -40 kN
l_k: 3000 mm
Fais la vérification à: la compression
M_y: 30 kNm
vérifier: flexion avec compression
''')
    assert problems == [], [str(p) for p in problems]
    assert len(blocks) == 1
    assert blocks[0].position == "S001"
    assert blocks[0].values == {"N": "-40 kN", "l_k": "3000 mm", "M_y": "30 kNm"}
    assert [check for check, _line in blocks[0].checks] == ["compression", "bending-normal"]


def test_a_keyword_is_read_in_three_languages_and_without_its_accents():
    """Every keyword has its French, German and English word, as an RFEM comment's `@key` does, and a word is matched folded -- so «Humidité», «humidite» and «Feuchteklasse» are one keyword."""
    for written in ("humidité: 2", "humidite: 2", "Feuchteklasse: 2", "moisture: 2"):
        blocks, problems = dsl.parse("position: T001\n" + written)
        assert problems == [], written
        assert blocks[0].values == {"moisture": "2"}, written
    for written in ("vérifier: compression", "Nachweis: Druck", "verify: compression", "verifier: LA COMPRESSION"):
        blocks, problems = dsl.parse("position: T001\n" + written)
        assert problems == [], written
        assert [c for c, _l in blocks[0].checks] == ["compression"], written


def test_a_line_outside_the_grammar_is_refused_naming_the_line():
    """The whole argument for a parser over a model: it cannot invent a command, and what it does not understand it says, with the line's number and what it could have said."""
    blocks, problems = dsl.parse('''position: T001
Hauteur 200
vérifier: le flambement de tout
inconnu: 3
vérifier:
N: -40 kN
''')
    numbers = [p.line for p in problems]
    assert numbers == [2, 3, 4, 5], [str(p) for p in problems]
    assert "carries no colon" in problems[0].message
    assert "not a check this engine makes" in problems[1].message and "bending" in problems[1].message
    assert "not a keyword" in problems[2].message and "position" in problems[2].message
    # and what *was* understood still stands, so the engineer corrects one line at a time
    assert blocks[0].values == {"N": "-40 kN"}


def test_a_value_before_any_position_is_refused():
    """A value states something about a member, so a «position: …» line comes first -- said rather than silently attached to nothing."""
    blocks, problems = dsl.parse("N: -40 kN\nposition: T001\n")
    assert blocks and blocks[0].values == {}
    assert len(problems) == 1 and problems[0].line == 1
    assert "comes before it" in problems[0].message


def test_a_level_is_one_of_the_four():
    blocks, problems = dsl.parse("position: T001\nniveau: 3\n")
    assert problems == [] and blocks[0].level == 3
    _blocks, problems = dsl.parse("position: T001\nniveau: 7\n")
    assert len(problems) == 1 and "0, 1, 2 or 3" in problems[0].message


def test_each_check_is_given_the_arguments_its_own_command_takes():
    """⚠️ The grammar knows each command's arguments (section 3.3undecies), so a length written in a block that also shears is handed to the buckling check and **not** to the shear check, which would refuse it."""
    blocks, _problems = dsl.parse('''position: T001
N: -40 kN
V: 24 kN
l_k: 3000 mm
vérifier: compression
vérifier: cisaillement
''')
    out = dsl.to_typst(blocks)
    compression = [line for line in out.splitlines() if "verify-compression" in line][0]
    shear = [line for line in out.splitlines() if "verify-shear" in line][0]
    assert "l-k-y" in compression and "l-k-z" in compression and "N:" in compression
    assert "l-k" not in shear and "V:" in shear, shear
    # one buckling length means both axes, which is what an engineer means by writing it once
    assert compression.count("3000 mm") == 2


def test_a_number_is_a_number_and_anything_else_is_a_string():
    """An action may be a bare number, a value with its unit, or the name of a variable declared above the line (section 3.3undecies), so what is written is passed as what it is."""
    blocks, _problems = dsl.parse("position: T001\nN: -40\nV: N_Ed\nvérifier: compression\nvérifier: cisaillement\n")
    out = dsl.to_typst(blocks)
    # -40 is a number and is passed as one; a name is passed as a string, which is what the checks read
    assert "N: -40)" in out, out
    assert 'V: "N_Ed")' in out, out


def test_what_is_missing_is_said_and_never_refused():
    """A warning and not a refusal: the engineer may mean to write the value in the report by hand, and the commands themselves say what they cannot compute."""
    blocks, _problems = dsl.parse("position: T001\nvérifier: compression\n")
    said = dsl.missing(blocks)
    assert any("states no N" in line for line in said), said
    assert any("no buckling length" in line for line in said), said


def test_the_typst_it_writes_compiles_and_prints_the_member():
    """⚠️ The check this whole thing rests on. A translator whose output does not compile is worse than none -- so the emitted calls are compiled against the project's own report, and the member's name is read back off the page."""
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    import subprocess
    import sys
    blocks, problems = dsl.parse('''position: T001
M_y: 26.9 kNm
a: 6000 mm
vérifier: flexion
V: 24 kN
vérifier: cisaillement
''')
    assert problems == []
    code = dsl.to_typst(blocks, level=2)
    probe = conftest.probe_dir("dsl") / "written.typ"
    probe.write_text('#import "/commands.typ": *\n\n' + code, encoding="utf-8")
    pdf = probe.with_suffix(".pdf")
    done = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(pdf)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert done.returncode == 0, done.stderr
    from pypdf import PdfReader
    text = "".join(page.extract_text() for page in PdfReader(str(pdf)).pages)
    assert "T001" in text, text[:400]
