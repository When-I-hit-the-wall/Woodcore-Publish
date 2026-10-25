"""The committed prints of the commands' values: examples/out/values/, one sheet a command and a language, and its map (calc/tools/build_examples.py render_values; spec 2026-10-24-onglet-commandes-pages, REQ-005, REQ-007, REQ-012, ARCH-004, ARCH-009, ARCH-010, CON-004).

The bubble of a value shows its call and what it prints, and prints it from a sheet cut at a rectangle -- nothing is compiled when a page opens (D-1). So every value of every page must have its print in each language, its rectangle inside its sheet, and the call it was compiled from must be the call the page writes now: a call edited and not compiled again is named here.
"""

import sys

import conftest
from conftest import ROOT, Skip

sys.path.insert(0, str(ROOT / "calc" / "tools"))

import build_examples as examples  # noqa: E402
import command_pages as pages  # noqa: E402
import validation  # noqa: E402

TIER = "fast"

INDEX = examples.values_index()
TABLE = pages.pages()
CEILING = 30 * 2**20   # CON-004: the engineer's ceiling for the committed sheets


def test_the_map_reads_against_its_schema():
    """ARCH-004: examples/out/values/index.json and examples/out/index.json each fit their schema."""
    validation.validate_structure(INDEX, "command-values", where="values/index.json")
    validation.validate_structure(examples.load_manifest(), "command-examples", where="out/index.json")


def test_every_value_has_its_print_in_every_language():
    """REQ-005, REQ-007: every value of every argument with values of every page, in fr, de and en, has an entry -- a rectangle, or `blank` -- compiled from the call the page writes now."""
    missing, stale = [], []
    for command, argument, value, lang, setup, call in examples.value_jobs(TABLE):
        entry = (INDEX["values"].get(examples.value_key(command, argument, value)) or {}).get(lang)
        if entry is None or not (entry.get("rect") or entry.get("blank")):
            missing.append(f"{command}|{argument}|{value} ({lang})")
        elif entry["hash"] != examples.value_hash(command, argument, value, setup, call, lang):
            stale.append(f"{command}|{argument}|{value} ({lang})")
    assert not missing, "values with no print -- run `python calc/tools/build_examples.py --values`:\n  " + "\n  ".join(missing[:20])
    assert not stale, "values whose call changed since its print -- run `python calc/tools/build_examples.py --values`:\n  " + "\n  ".join(stale[:20])


def test_every_rectangle_stands_inside_its_sheet():
    """ARCH-009: one sheet a command and a language, the map's size the file's own, every rectangle inside it; and no other file."""
    from PIL import Image
    files = {p.name for p in examples.VALUES.glob("*")}
    expected = {sheet["file"] for sheet in INDEX["sheets"].values()} | {"index.json"}
    assert files == expected, sorted(files ^ expected)
    for name, sheet in INDEX["sheets"].items():
        with Image.open(examples.VALUES / sheet["file"]) as image:
            assert list(image.size) == sheet["size"], name
        assert sheet["isolate"] is True
    for key, by_lang in INDEX["values"].items():
        command = key.split("|", 1)[0]
        for lang, entry in by_lang.items():
            if entry.get("blank"):
                continue
            top, width, height = entry["rect"]
            size = INDEX["sheets"][f"{lang}-{command}"]["size"]
            assert top >= 0 and width <= size[0] and top + height <= size[1], (key, lang, entry["rect"], size)


def test_nothing_printed_and_the_same_print_are_said():
    """REQ-005: `display: "none"` and `level: 0` print nothing; `level: auto` prints what level 2 prints, in every language."""
    for lang in pages.LANGS:
        assert INDEX["values"]['var|display|"none"'][lang].get("blank")
        assert INDEX["values"]["var|level|0"][lang].get("blank")
        assert "2" in INDEX["values"]["var|level|auto"][lang]["same"] and "auto" in INDEX["values"]["var|level|2"][lang]["same"]


def test_the_sheets_stay_under_the_ceiling():
    """CON-004: the committed sheets weigh less than 30 MB, measured after each category."""
    assert examples.values_weight() < CEILING, examples.values_weight()


def test_a_value_compiled_alone_prints_what_its_sheet_holds_and_a_setting_before_it_would_not():
    """ARCH-010, with a real compile: `var|display|auto` compiled again alone has the very ink the map recorded -- each value is a document of its own --, and the same call under a `#calc-defaults(scope: "document")` that a shared document would have put before it prints something else."""
    if not conftest.have_typst() or not (examples.EXAMPLES / "commands.typ").exists():
        raise Skip("typst is not on the path, or examples/ has no engine copy -- run build_examples.py")
    import hashlib
    examples.VALUES_WORK.mkdir(parents=True, exist_ok=True)
    call = '#var("M_d", 14.06, "kNm", display: auto)'
    _job, png, error = examples._compile_value(("var", "display", "auto", "fr", "", call))
    assert error is None, error
    alone = hashlib.sha256(examples._ink(png).tobytes()).hexdigest()[:16]
    assert alone == INDEX["values"]["var|display|auto"]["fr"]["ink"]
    _job, png, error = examples._compile_value(("var", "display", "auto", "fr", '#calc-defaults(display: "value-unit", scope: "document")', call))
    assert error is None, error
    assert hashlib.sha256(examples._ink(png).tobytes()).hexdigest()[:16] != alone, "a setting before the call changes its print: the calls of a sheet must not share a document"
