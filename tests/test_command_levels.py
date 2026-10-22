"""Every command that prints takes `level:` -- 1 the figure, the table or the list alone, 2 with its legend and its titles, 3 with its sources and its citations (spec 2026-10-20-indices-et-niveaux, UI-003, ARCH-003, D-03, D-04, D-07, D-08).

The engineer, 19.10.2026: «Commandes sans niveau : corrige, il faut des niveaux pour toutes les commandes» -- the commands that print (`distance`, the lists of the norms and the bibliography, the annexes; the `show-*`, `verify-*`, `doc-*` and `sheet-*` until the spec 2026-10-21-commandes-typst-refonte retired them), not the accessors (Q-007 of the base saine); a level 2 that prints what a document printed until then (Q-002 revised), a level 1 that leaves the legend, the titles and the scale bar out, and a level 3 that adds what the command can cite or, where it has nothing, says so in `build_reference_lib.LEVELS_CONFOUNDED`. A form's field, a document's table and a sheet's text print what the engineer wrote and take none (Q-003 revised, `NO_LEVEL`).

These hold the registries to the engine both ways, and compile each command at 1, 2 and 3 from the example project, its pages compared: level 1 differs from level 2, and level 2 from level 3 unless the command is named as confounded there. That the documents' own level 2 did not move is tests/test_report_golden.py's to hold.
"""

import subprocess
import sys

import conftest
from conftest import ROOT, Skip

import build_reference_lib as lib

sys.path.insert(0, str(ROOT / "calc" / "tools"))
import command_docs  # noqa: E402

# One call of each command that took no level before v0.120, from the example project: the one compiled at 1, 2 and 3.
CALLS = {
    "show-norm-list": '#show-norm-list(keys: ("SIA 260", "SIA 261"), level: {L})',
    "show-bibliography": '#cite-norm(norm: "SIA 265", norm-ref: "4.2.1")\n#show-bibliography(data: false, level: {L})',
    "distance": '#distance(12, "dowel", level: {L})',
}


def _takes_level():
    """{public command: whether its signature or its /// block names `level`}."""
    out = {}
    for record in lib.lib_bindings(ROOT):
        if record["category"] == lib.INTERNAL:
            continue
        out[record["name"]] = command_docs.takes_level(record, lib.parse_doc_block(record["doc_lines"]))
    return out


def test_every_public_command_takes_a_level_or_says_why_not():
    takes = _takes_level()
    public = {name for _, names in lib.CATEGORIES for name in names}
    missing = sorted(name for name in public if not takes.get(name) and name not in lib.NO_LEVEL)
    both = sorted(name for name in lib.NO_LEVEL if takes.get(name))
    unknown = sorted(set(lib.NO_LEVEL) - public)
    assert not missing, "commands that print and take no level: %s" % missing
    assert not both, "named in NO_LEVEL and taking a level: %s" % both
    assert not unknown, "NO_LEVEL names no public command: %s" % unknown
    assert all(reason.strip() for reason in lib.NO_LEVEL.values())
    stale = sorted(name for name in lib.LEVELS_CONFOUNDED if not takes.get(name))
    assert not stale, "LEVELS_CONFOUNDED names a command taking no level: %s" % stale
    for name, (levels, reason) in lib.LEVELS_CONFOUNDED.items():
        assert set(levels) <= {1, 2, 3} and len(levels) >= 2 and reason.strip(), name


def _pages(body, name):
    """The SVG of every page `body` compiles to in the example project, as one text."""
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    for old in d.glob("page-*.svg"):
        old.unlink()
    out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(d / "page-{p}.svg")],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, "%s did not compile:\n%s" % (name, out.stderr)
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(d.glob("page-*.svg")))


def test_each_command_prints_differently_at_each_level_unless_it_says_why_not():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    flat = []
    for command, call in CALLS.items():
        if call is None:
            continue
        one, two, three = (_pages(call.replace("{L}", str(level)), "levels_%s_%d" % (command, level)) for level in (1, 2, 3))
        same = set(lib.LEVELS_CONFOUNDED.get(command, ((), ""))[0])
        if (one == two) != ({1, 2} <= same):
            flat.append("%s: level 1 %s level 2" % (command, "is" if one == two else "differs from"))
        if (two == three) != ({2, 3} <= same):
            flat.append("%s: level 2 %s level 3" % (command, "is" if two == three else "differs from"))
    assert not flat, flat


# The sheet commands, placed on a sheet as a sheet places them (a sheet prints at level 2 unless --input level= says otherwise), and the annexes after an excerpt the document shows: compiled at 1, 2 and 3 as the commands above.
SHEET_CALLS = {
    "show-annexes": '#figure(image-extract("CO1-My"), kind: image, caption: [A])\n#show-annexes(level: {L})',
}


def test_the_sheets_and_the_annexes_print_differently_at_each_level_unless_they_say_why_not():
    """UI-003 for the commands a section does not call bare: the objects of a sheet, on a sheet, and the annexes, after an excerpt the document shows. `show-annexes` and `doc-annexes` have no -L1/-L3 page: their examples are ```typ-dry, every page of a source being a page of its own (docs/decisions.md), and command_docs.example_levels renders no such fence -- this compile is their proof. `show-check` needs a domain carrying checks, which the example has none of; it prints the same at every level (LEVELS_CONFOUNDED)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    flat = []
    for command, call in SHEET_CALLS.items():
        one, two, three = (_pages(call.replace("{L}", str(level)), "levels_%s_%d" % (command, level)) for level in (1, 2, 3))
        same = set(lib.LEVELS_CONFOUNDED.get(command, ((), ""))[0])
        if (one == two) != ({1, 2} <= same):
            flat.append("%s: level 1 %s level 2" % (command, "is" if one == two else "differs from"))
        if (two == three) != ({2, 3} <= same):
            flat.append("%s: level 2 %s level 3" % (command, "is" if two == three else "differs from"))
    assert not flat, flat


def test_a_level_written_survives_the_objects_round_trip():
    """ARCH-003: a `level:` written by hand in a section -- on a document's plan, a sheet's viewport -- is read by the object models and written back as it was (calc/typst_objects_parse.py SIGNATURES)."""
    import typst_objects as to
    for call in ('#show-norm-list(keys: ("SIA 260",), level: 1)',):
        model = to.model_for(to.parse_call(call))
        assert model.get("level") in (1, 3), call
        assert "level: " + str(model.get("level")) in model.serialize(), (call, model.serialize())
