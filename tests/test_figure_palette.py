"""The figures' colours and font are lib/figure-palette.json's, and nobody else's (spec 2026-10-19-base-saine-nettoyage, D5, Q-015).

Until v0.120 each drawing engine wrote its own colours -- some sixty values, five blacks among them -- and the report's Typst wrote a copy of some (a connection's arrows, a position's STE letter), held equal to Python by a test that compared two lists of hex values. One file now: calc/domains/svg_draw.py reads it for the engines, lib/calc-engine-core.typ for the report (`figure-colour`), and the engine copies it into a project with its .typ files. Held here: no engine writes a colour or a font of its own, every token named on either side is one the palette holds, and the file is the engine's.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import json
import re

import conftest
from conftest import ROOT

PALETTE = ROOT / "lib" / "figure-palette.json"
HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
# what draws a figure and reads its colours from the palette: every *_svg module and the two domain modules that name a load's or a superposition's ink
ENGINES = sorted((ROOT / "calc" / "domains").glob("*svg*.py")) + [ROOT / "calc" / "domains" / "statics.py", ROOT / "calc" / "domains" / "plan.py"]


def _strings(path):
    """[(line, text)] of every string of `path`'s code -- its docstrings aside, which are prose."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)) and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            docs.add(id(node.body[0].value))
    return [(n.lineno, n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]


def test_the_palette_is_colours_by_token_and_one_font():
    data = json.loads(PALETTE.read_text(encoding="utf-8"))
    assert isinstance(data["font-family"], str) and "," not in data["font-family"], "one family, not a list: QtSvg takes the whole string as one name"
    for token, value in data["colours"].items():
        assert re.fullmatch(r"#[0-9a-f]{6}", value), f"{token}: {value!r} is not #rrggbb in lower case"
    for name, values in data["lists"].items():
        assert values and all(re.fullmatch(r"#[0-9a-f]{6}", v) for v in values), name
        assert len(set(values)) == len(values), f"the rotation {name} repeats a colour"
    assert len(set(data["colours"].values())) == len(data["colours"]), "two tokens of one colour: merged in Q-015, they are one token"


def test_no_drawing_engine_writes_a_colour_or_a_font_of_its_own():
    offenders = []
    for path in ENGINES:
        for line, text in _strings(path):
            if HEX.search(text) or "Arial" in text:
                offenders.append(f"{path.name}:{line}: {text[:80]!r}")
    assert not offenders, "a colour or a font written in a drawing engine -- name a token of lib/figure-palette.json (svg_draw.colour):\n" + "\n".join(offenders)


def test_every_token_named_is_one_the_palette_holds():
    data = json.loads(PALETTE.read_text(encoding="utf-8"))
    named = set()
    for path in ENGINES:
        named |= set(re.findall(r'svg_draw\.colour\("([a-z-]+)"\)', path.read_text(encoding="utf-8")))
    typst = conftest.engine_source() + (ROOT / "lib" / "positions.typ").read_text(encoding="utf-8")
    named_typst = set(re.findall(r'figure-colour\("([a-z-]+)"\)', typst))
    assert named and named_typst, "the palette is named nowhere -- the patterns of this test no longer match the code"
    assert not (named | named_typst) - set(data["colours"]), f"tokens the palette does not hold: {sorted((named | named_typst) - set(data['colours']))}"
    from domains import plan
    assert set(plan.SUPERPOSITION_INKS.values()) <= set(data["colours"].values()), "a superposition's ink is not the palette's"
    lists = set(re.findall(r'svg_draw\.colours\("([a-z-]+)"\)', "".join(p.read_text(encoding="utf-8") for p in ENGINES)))
    assert lists and not lists - set(data["lists"]), sorted(lists - set(data["lists"]))


def test_python_and_typst_read_the_one_file_and_the_engine_copies_it():
    import project
    from domains import svg_draw
    assert svg_draw.PALETTE_FILE == PALETTE
    assert 'json("figure-palette.json")' in conftest.engine_source(), "the report reads its colours from elsewhere"
    assert "lib/figure-palette.json" in project.ENGINE_FILES, "a project's engine would compile without its palette"
    data = json.loads(PALETTE.read_text(encoding="utf-8"))
    assert svg_draw.FONT == data["font-family"] and svg_draw.colour("ink") == data["colours"]["ink"]
