"""The paths a Typst file writes, found and rewritten when their targets move (calc/typst_paths.py, the three document modes, work package 1.3).

When a project's report folder moves from `<project>/Statischer Bericht (typst)/` to `<project>/3_Statischer Bericht/`, and its `config.typ`, `commands.typ`, `references.bib`, `Images/` and `_woodcore/` move up to the project folder, every string of the report's `.typ` files that names one of them has to follow, and Typst cannot be asked where a path leads without compiling. So what is held here is in two halves. The lexer finds the right strings and only those — checked on small cases, on a fuzz that must neither raise nor loop, and on every committed report and the engine's own `lib/*.typ` against an independent regular expression. And the rewrite writes a literal again only when it would stop reaching its target, keeps every other byte and says what it could not do — checked on a tree made for the purpose, before and after the moves, and then by the only judge there is: the rewritten report compiles, and prints what the old one printed, while the same report moved and not rewritten does not compile at all.

⚠️ The compile checks are skipped where `typst` is not on the path. The example's one migrates the example as it was laid out before it was itself migrated -- one report, its folder the Typst root -- which tests/fixtures/legacy_example.py rebuilds from the committed example, laid out in three documents since.
"""

import random
import re
import shutil
import subprocess
import time

import conftest
from conftest import ROOT, Skip

import project
import typst_paths as tp


def _found(text):
    return [(lit.kind, lit.value) for lit in tp.literals(text)]


# --- finding literals ------------------------------------------------------------------------

def test_the_three_kinds_of_literal():
    text = (
        '#import "../commands.typ": *\n'
        '#include "Sections/a.typ"\n'
        '#{ set heading(offset: 1); include "Sections/b.typ" }\n'
        '#image("../Images/x.png", width: 50%)\n'
        '#let d = json("../data/p.json")\n'
        '#let c = csv("a.csv", delimiter: ",")\n'
        '#yaml("a.yaml") #toml("a.toml") #xml("a.xml") #cbor("a.cbor")\n'
        '#let p = plugin("a.wasm")\n'
        '#read("n.txt", encoding: none)\n'
        '#show-bibliography(project: "references.bib", file: "f.txt")\n'
    )
    lits = tp.literals(text)
    assert [(lit.kind, lit.value) for lit in lits] == [
        ("import", "../commands.typ"),
        ("include", "Sections/a.typ"),
        ("include", "Sections/b.typ"),
        ("image", "../Images/x.png"),
        ("json", "../data/p.json"),
        ("csv", "a.csv"),
        ("yaml", "a.yaml"),
        ("toml", "a.toml"),
        ("xml", "a.xml"),
        ("cbor", "a.cbor"),
        ("plugin", "a.wasm"),
        ("read", "n.txt"),
        ("project", "references.bib"),
        ("file", "f.txt"),
    ]
    for lit in lits:
        assert lit.raw(text) == lit.value and text[lit.start - 1] == '"' == text[lit.end], f"the span of {lit.value!r} is not its content"
    assert [lit.start for lit in lits] == sorted(lit.start for lit in lits), "the literals are not in the order they are written"


def test_project_is_root_relative_and_the_others_are_not():
    lits = tp.literals('#show-bibliography(project: "references.bib")\n#image("a.png")\n#x(file: "f.txt")\n')
    assert [lit.root_relative for lit in lits] == [True, False, False]


def test_package_imports_are_not_paths():
    text = '#import "@preview/cetz:0.3.0": canvas\n#import "@local/x:1.0.0": *\n#import "a.typ"\n#import "b.typ" as b\n'
    assert _found(text) == [("import", "a.typ"), ("import", "b.typ")]


def test_comments_strings_and_raw_blocks_hide_what_they_hold():
    text = "\n".join([
        '// #import "no1.typ"',
        '/* #import "no2.typ" /* nested */ #import "no3.typ" */',
        '#import "yes.typ" // trailing #image("no4.png")',
        '/// a doc comment: #image("no5.png")',
        '#let s = "// not a comment"; #image("yes2.png")',
        '#let t = "#image(\\"no6.png\\")"',
        '`#image("no7.png")`',
        '```typ',
        '#import "no8.typ"',
        '```',
        'Two backticks are an empty raw, not a block: `` #image("yes0.png") ``',
        '````',
        '```',
        '#import "no10.typ"',
        '````',
        '#image("yes3.png")',
    ])
    assert _found(text) == [("import", "yes.typ"), ("image", "yes2.png"), ("image", "yes0.png"), ("image", "yes3.png")]


def test_a_quote_or_a_url_in_markup_does_not_put_the_lexer_out_of_step():
    """In markup a `"` is a smart quote and `//` inside `https://…` no comment: a lone one must not open a string that swallows the next literal."""
    text = "\n".join([
        'Er sagte 5" Rohr und dann',
        '#image("yes1.png")',
        'C\'est "ok.',
        '#include "yes2.typ"',
        'Siehe https://example.org/a//b, dann #image("yes3.png")',
        'Und (https://example.org/x_(y)) #image("yes4.png")',
        'Ein \\" und ein \\// und #image("yes5.png")',
    ])
    assert [value for _, value in _found(text)] == ["yes1.png", "yes2.typ", "yes3.png", "yes4.png", "yes5.png"]


def test_only_the_first_string_of_a_call_is_a_path():
    text = "\n".join([
        '#image(data, format: "png")',
        '#image("a.png", alt: "b.png")',
        '#my-image("x.png")',
        '#json.decode("x.json")',
        '#sheet.image("y.png")',
        '#std.image("z.png")',
        '#let shown = sys.inputs.at("read", default: "q.png")',
        '#set text(lang: "de")',
    ])
    assert _found(text) == [("image", "a.png"), ("image", "z.png")]


def test_a_path_continued_at_compile_time_is_partial():
    lits = tp.literals('#image("../Images/" + name + ".png")\n#image("a.png")\n#image("b.png" + "x")\n')
    assert [(lit.value, lit.partial) for lit in lits] == [("../Images/", True), ("a.png", False), ("b.png", True)]


def test_escapes_are_resolved_and_written_back():
    text = '#image("a\\"b.png")\n#image("\\u{e4}.png")\n'
    lits = tp.literals(text)
    assert [lit.value for lit in lits] == ['a"b.png', "\u00e4.png"]
    assert lits[0].raw(text) == 'a\\"b.png', "the span is what is written, escapes included"
    assert tp._escape('a"b\\c') == 'a\\"b\\\\c'


def test_code_inside_markup_inside_code():
    text = "\n".join([
        '#figure(image("a.png"), caption: [see #image("b.png") and "c"])',
        '#strong[#image("d.png")]',
        '$ x = #image("m.png") + "text" $',
        '#if true [ #image("e.png") ] else [ #image("f.png") ]',
        '#for x in (1, 2) { image("g.png") }',
        '#show heading: it => { image("h.png"); it }',
        '#show: conf',
        '#let f(x) = [ #image("i.png") ]',
        '#image("j.png")',
    ])
    assert [value for _, value in _found(text)] == [f"{c}.png" for c in "abdmefghij"]


def test_a_statement_ends_at_its_line_or_its_semicolon():
    """What follows `#set …` or `#let …; ` is markup again, where a `"` is a smart quote: a statement that did not end would take it for a string."""
    text = "\n".join([
        '#set text(lang: "de")',
        'Er sagte "Hallo" und #image("a.png")',
        '#let x = 1; "zitiert" #image("b.png")',
        '#import "c.typ": *',
        'Noch "ein Zitat" #image("d.png")',
    ])
    assert [value for _, value in _found(text)] == ["a.png", "b.png", "c.typ", "d.png"]


def test_the_root_and_empty_strings_are_found_and_nothing_breaks():
    assert _found('#read("/" + path)') == [("read", "/")]
    assert _found('#image("")') == [], "an empty string is no path"


def test_a_truncated_file_never_raises():
    for text in ['', '#', '#image("a.png"', '#image("a.png', '/* open', '`raw', '```\n#image("a.png")', '$ #image("a.png")', '#import "x', '#{', '#[', '#(', '#image(', '\\']:
        tp.literals(text)
    assert _found('#image("a.png"') == [("image", "a.png")]


def test_a_fuzz_of_special_characters_neither_raises_nor_loops():
    rng = random.Random(260930)
    alphabet = '"#$`[](){}/*\\\n ;:.,+-imagecludpthjson@<>'
    started = time.time()
    for _ in range(3000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
        for lit in tp.literals(text):
            assert 0 <= lit.start <= lit.end <= len(text) and tp._unescape(lit.raw(text)) == lit.value, text
    assert time.time() - started < 30, "the lexer is far too slow on short inputs: does it loop?"


# --- the lexer against an independent reading ------------------------------------------------

# A regular expression that knows nothing of modes, used as a second opinion on lines that are not comments. A name continued by `-` (`sia265-json(`, `my-image(`) is not the function, which is exactly what a lexer knows and a regex has to be told.
_NAIVE = re.compile(
    r'(?<![\w.-])(?P<fn>image|read|json|csv|yaml|toml|xml|cbor|plugin|bibliography)\(\s*"(?P<v>[^"]*)"'
    r'|(?<![\w.-])(?P<kw>import|include)\s+"(?P<v2>[^"]*)"'
    r'|(?<![\w.-])(?P<named>project|file):\s*"(?P<v3>[^"]*)"'
)


def _without_comment(line):
    """A line up to the `//` that starts its comment: one inside quotes, or in a URL, is not."""
    start = 0
    while True:
        j = line.find("//", start)
        if j < 0:
            return line
        if line[:j].count('"') % 2 == 0 and not line[:j].endswith(":"):
            return line[:j]
        start = j + 2


def _naive(text):
    found = []
    for line in text.split("\n"):
        line = _without_comment(line)
        for m in _NAIVE.finditer(line):
            kind = m.group("fn") or m.group("kw") or m.group("named")
            value = m.group("v") if m.group("fn") else m.group("v2") if m.group("kw") else m.group("v3")
            if value and not value.startswith("@"):
                found.append((kind, value))
    return sorted(found)


def _typ_files(base):
    return sorted(p for p in base.rglob("*.typ") if not {"_woodcore", ".probe"} & set(p.relative_to(base).parts))


def test_the_committed_reports_are_read_whole():
    """The example project and the template, file by file: the lexer and a regular expression agree, and every path resolves — the engine's copy excepted, which is generated and not committed."""
    seen = 0
    for base in (ROOT / "tests" / "projet-exemple", ROOT / "templates" / "projet"):
        for file in _typ_files(base):
            text = tp.read_text(file)
            lits = tp.literals(text)
            assert sorted((lit.kind, lit.value) for lit in lits) == _naive(text), f"{file}: the lexer and the regular expression disagree"
            root = next((p for p in file.parents if (p / "commands.typ").exists()), file.parent)   # the Typst root: where commands.typ lies
            for lit in lits:
                if "_woodcore/lib/" in lit.value:
                    continue
                target = tp._target(lit, lit.value, file.parent, root)
                assert target.exists(), f"{file}: {lit.kind} {lit.value!r} resolves to {target}, which does not exist"
                seen += 1
    assert seen > 20, "the committed reports were found to hold hardly any path: is something not being read?"


def test_the_engines_own_lib_files_are_read_whole():
    """The engine's files are the largest real Typst there is here — code, markup, math and raw, `///` comments, a hundred functions — and what they hold is known: the norm tables and the export, read by `json(`."""
    jsons = 0
    for file in sorted((ROOT / "lib").glob("*.typ")):
        text = tp.read_text(file)
        lits = tp.literals(text)
        assert sorted((lit.kind, lit.value) for lit in lits) == _naive(text), f"{file.name}: the lexer and the regular expression disagree"
        for lit in lits:
            if lit.kind == "json":
                # the export, the norms -- or a data file of the engine's own beside it, copied with it (lib/units.json, v0.117)
                assert lit.value.startswith(("../data/", "../calc/")) or f"lib/{lit.value}" in project.ENGINE_FILES, f"{file.name}: json({lit.value!r}) is not read from the export, the norms or the engine"
                jsons += 1
    assert jsons >= 10, f"only {jsons} json literals were found in lib/"


# --- rewriting -------------------------------------------------------------------------------

def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _tree(name, files):
    """A fresh directory with `files` in it: `{relative path: text}`."""
    d = conftest.tmpdir(name)
    for rel, text in files.items():
        _write(d / rel, text)
    return d


MOVABLE = ("_woodcore", "Images", "config.typ", "commands.typ", "references.bib")


def _migrate(top, old_name, new_name):
    """The moves of the migration, by rename, as it does them: what the shared files are moves up to `top`, then the report folder takes its new name. Returns the old folder, the new one, and the map the rewrite is given."""
    old = top / old_name
    moved = {}
    for name in MOVABLE:
        if (old / name).exists():
            shutil.move(str(old / name), str(top / name))
            moved[old / name] = top / name
    new = top / new_name
    shutil.move(str(old), str(new))
    moved[old] = new
    return old, new, moved


def _old_of(path, top, old, new):
    """Where a file lay before the moves: under the old report folder, which is also where the shared ones at the top came from."""
    return old / path.relative_to(new) if new in path.parents else old / path.name


def _own_typ(top, new):
    """The `.typ` files a report owns once moved: the renamed folder's and the shared ones at the top of the project."""
    files = _typ_files(new)
    files += [top / name for name in ("config.typ", "commands.typ") if (top / name).exists()]
    return files


def _rewrite_all(top, old, new, moved):
    changes, unresolved = [], []
    for file in _own_typ(top, new):
        c, u = tp.rewrite_file(file, _old_of(file, top, old, new), old, top, moved)
        changes += [(file, x) for x in c]
        unresolved += [(file, x) for x in u]
    return changes, unresolved


SECTION = (
    '#import "../commands.typ": *\n'
    '#image("../Images/pic.svg")\n'
    '#show-bibliography(project: "references.bib")\n'
    '#read("notes.txt")\n'
)
ENTRY = (
    '#import "config.typ": conf\n'
    '#import "commands.typ": *\n'
    '#include "Sections/a.typ"\n'
    '#image("Images/pic.svg"); #image("Images/pic.svg", width: 50%)\n'
)
SOURCES = {
    "Bericht (typst)/Entry.typ": ENTRY,
    "Bericht (typst)/config.typ": "",
    "Bericht (typst)/commands.typ": "",
    "Bericht (typst)/references.bib": "",
    "Bericht (typst)/Images/pic.svg": "",
    "Bericht (typst)/Sections/a.typ": SECTION,
    "Bericht (typst)/Sections/notes.txt": "",
}


def test_a_moved_target_is_written_root_absolute_and_the_rest_is_left():
    top = _tree("tp_moved", SOURCES)
    old, new, moved = _migrate(top, "Bericht (typst)", "3_Bericht")
    section, entry = new / "Sections" / "a.typ", new / "Entry.typ"

    text, changes, unresolved = tp.rewrite(tp.read_text(section), old / "Sections" / "a.typ", section, old, top, moved)
    assert not unresolved
    assert text == (
        '#import "/commands.typ": *\n'
        '#image("/Images/pic.svg")\n'
        '#show-bibliography(project: "references.bib")\n'     # root-relative, and references.bib is at the top of the new root as it was of the old
        '#read("notes.txt")\n'                                # moved along with the section, so it still reaches it
    ), text
    assert [(c.old, c.new) for c in changes] == [("../commands.typ", "/commands.typ"), ("../Images/pic.svg", "/Images/pic.svg")]

    text, changes, unresolved = tp.rewrite(tp.read_text(entry), old / "Entry.typ", entry, old, top, moved)
    assert not unresolved
    assert text == (
        '#import "/config.typ": conf\n'
        '#import "/commands.typ": *\n'
        '#include "Sections/a.typ"\n'                         # the entry and its Sections moved together
        '#image("/Images/pic.svg"); #image("/Images/pic.svg", width: 50%)\n'   # two on one line: the spans do not slide over each other
    ), text
    assert len(changes) == 4
    assert all(c.new_target.exists() for c in changes), "a target given as it now lies does not exist"

    # What was written is read back as the same literals with the new values: the spans were right.
    assert [value for _, value in _found(text)] == ["/config.typ", "/commands.typ", "Sections/a.typ", "/Images/pic.svg", "/Images/pic.svg"]


def test_the_rewrite_is_the_same_before_the_moves_as_after_them():
    """The migration may rewrite before or after it moves: a target is looked for where it was and where it is going, so the answer does not depend on which."""
    top = _tree("tp_dry", SOURCES)
    old = top / "Bericht (typst)"
    new = top / "3_Bericht"
    moved = {old / name: top / name for name in MOVABLE if (old / name).exists()}
    moved[old] = new
    before = {}
    for rel in ("Entry.typ", "Sections/a.typ"):
        file_old = old / rel
        before[rel] = tp.rewrite(tp.read_text(file_old), file_old, new / rel, old, top, moved)
    assert all(not u for _, _, u in before.values()), "a dry run reports a target that is there as missing"
    _, _, moved_map = _migrate(top, "Bericht (typst)", "3_Bericht")
    for rel in ("Entry.typ", "Sections/a.typ"):
        file = new / rel
        after = tp.rewrite(tp.read_text(file), old / rel, file, old, top, moved_map)
        assert after[0] == before[rel][0], f"{rel} is rewritten differently before and after the moves"
        assert [c.new for c in after[1]] == [c.new for c in before[rel][1]]


def test_a_file_that_moves_alone_gets_root_absolute_paths():
    """The target stays and the file goes: the string no longer reaches it from the new place, so it is written from the root."""
    top = _tree("tp_alone", {"data.json": "{}", "old/a.typ": '#json("../data.json")\n#image("pic.svg")\n', "old/pic.svg": ""})
    file_new = top / "deep" / "er" / "a.typ"
    moved = {top / "old" / "a.typ": file_new}
    text, changes, unresolved = tp.rewrite(tp.read_text(top / "old" / "a.typ"), top / "old" / "a.typ", file_new, top, top, moved)
    assert text == '#json("/data.json")\n#image("/old/pic.svg")\n', text
    assert not unresolved and len(changes) == 2


def test_a_root_absolute_literal_follows_a_root_that_moves():
    """`"/Images/x.png"` is read from the root, and the root is now the project: what moved to the top of it is still reached, what moved with the report folder is not."""
    top = _tree("tp_root", {
        "Bericht (typst)/Sections/b.typ": '#import "/commands.typ": *\n#image("/Images/pic.svg")\n#read("/notes2.txt")\n#read("/" + path)\n',
        "Bericht (typst)/commands.typ": "",
        "Bericht (typst)/Images/pic.svg": "",
        "Bericht (typst)/notes2.txt": "",
    })
    old, new, moved = _migrate(top, "Bericht (typst)", "3_Bericht")
    file = new / "Sections" / "b.typ"
    text, changes, unresolved = tp.rewrite(tp.read_text(file), old / "Sections" / "b.typ", file, old, top, moved)
    assert text == '#import "/commands.typ": *\n#image("/Images/pic.svg")\n#read("/3_Bericht/notes2.txt")\n#read("/" + path)\n', text
    assert [c.old for c in changes] == ["/notes2.txt"] and not unresolved


def test_a_folder_a_path_is_continued_from_keeps_its_slash():
    top = _tree("tp_partial", {"Bericht (typst)/Sections/a.typ": '#image("../Images/" + name)\n', "Bericht (typst)/Images/pic.svg": ""})
    old, new, moved = _migrate(top, "Bericht (typst)", "3_Bericht")
    file = new / "Sections" / "a.typ"
    text, changes, unresolved = tp.rewrite(tp.read_text(file), old / "Sections" / "a.typ", file, old, top, moved)
    assert text == '#image("/Images/" + name)\n' and not unresolved, text


def test_project_is_left_when_its_file_moves_to_the_top_and_written_when_it_goes_elsewhere():
    """`project: "references.bib"` is read from the root whatever it starts with: it stays as it is while references.bib is at the top of the root, and follows it when it is not."""
    top = _tree("tp_project", {"Bericht (typst)/Sections/l.typ": '#show-bibliography(project: "references.bib")\n', "Bericht (typst)/references.bib": ""})
    old, new, moved = _migrate(top, "Bericht (typst)", "3_Bericht")
    file = new / "Sections" / "l.typ"
    text, changes, _ = tp.rewrite(tp.read_text(file), old / "Sections" / "l.typ", file, old, top, moved)
    assert text == '#show-bibliography(project: "references.bib")\n' and not changes

    # the same file, with the bibliography filed under a folder of the project instead: the value names it without the slash the engine adds
    moved_elsewhere = dict(moved)
    moved_elsewhere[old / "references.bib"] = top / "Literatur" / "references.bib"
    (top / "Literatur").mkdir()
    shutil.move(str(top / "references.bib"), str(top / "Literatur" / "references.bib"))
    text, changes, _ = tp.rewrite(tp.read_text(file), old / "Sections" / "l.typ", file, old, top, moved_elsewhere)
    assert text == '#show-bibliography(project: "Literatur/references.bib")\n', text


def test_a_literal_that_names_nothing_is_left_and_reported():
    top = _tree("tp_missing", {
        "Bericht (typst)/Sections/a.typ": '#image("../Images/missing.png")\n#image("../Images/pic.svg")\n#image("../Images/Plan-" + n)\n#import "gone.typ"\n',
        "Bericht (typst)/Images/pic.svg": "",
    })
    old, new, moved = _migrate(top, "Bericht (typst)", "3_Bericht")
    file = new / "Sections" / "a.typ"
    text, changes, unresolved = tp.rewrite(tp.read_text(file), old / "Sections" / "a.typ", file, old, top, moved)
    assert text == '#image("../Images/missing.png")\n#image("/Images/pic.svg")\n#image("../Images/Plan-" + n)\n#import "gone.typ"\n', text
    assert [u.literal.value for u in unresolved] == ["../Images/missing.png", "../Images/Plan-", "gone.typ"]
    assert all("names nothing" in u.reason for u in unresolved) and "compile time" in unresolved[1].reason
    assert [c.old for c in changes] == ["../Images/pic.svg"]


def test_a_target_that_leaves_the_new_root_is_reported():
    top = _tree("tp_outside", {"root/a.typ": '#read("x.txt")\n#read("y.txt")\n', "root/x.txt": "", "root/y.txt": ""})
    elsewhere = conftest.tmpdir("tp_outside_away") / "x.txt"
    shutil.move(str(top / "root" / "x.txt"), str(elsewhere))
    moved = {top / "root" / "x.txt": elsewhere}
    text, changes, unresolved = tp.rewrite(tp.read_text(top / "root" / "a.typ"), top / "root" / "a.typ", top / "root" / "a.typ", top / "root", top / "root", moved)
    assert text == '#read("x.txt")\n#read("y.txt")\n' and not changes
    assert len(unresolved) == 1 and unresolved[0].literal.value == "x.txt" and "outside the new root" in unresolved[0].reason


def test_line_endings_are_kept():
    top = _tree("tp_crlf", {"Bericht (typst)/Sections/a.typ": "", "Bericht (typst)/commands.typ": "", "Bericht (typst)/Images/pic.svg": ""})
    text = '#import "../commands.typ": *\r\n#image("../Images/pic.svg")\r\nplain text\nlast line without a break #image("../Images/pic.svg")'
    old, new, moved = _migrate(top, "Bericht (typst)", "3_Bericht")
    file = new / "Sections" / "a.typ"
    tp.write_text(file, text)
    assert tp.read_text(file) == text, "read_text and write_text do not keep the line endings"
    assert file.read_bytes() == text.encode("utf-8")
    changes, _ = tp.rewrite_file(file, old / "Sections" / "a.typ", old, top, moved)
    assert len(changes) == 3
    assert file.read_bytes() == text.replace("../commands.typ", "/commands.typ").replace("../Images", "/Images").encode("utf-8"), "a byte outside a literal changed"
    assert file.read_bytes().count(b"\r\n") == 2 and b"\r\n" not in file.read_bytes().replace(b"\r\n", b"")


def test_rewrite_file_writes_only_a_change():
    top = _tree("tp_untouched", {"Bericht (typst)/Entry.typ": '#include "Sections/a.typ"\n', "Bericht (typst)/Sections/a.typ": ""})
    old, new, moved = _migrate(top, "Bericht (typst)", "3_Bericht")
    file = new / "Entry.typ"
    before = file.stat().st_mtime_ns
    time.sleep(0.05)
    changes, unresolved = tp.rewrite_file(file, old / "Entry.typ", old, top, moved)
    assert not changes and not unresolved
    assert file.stat().st_mtime_ns == before, "an unchanged file was written"
    assert not list(new.glob("*.part")), "a temporary file was left behind"


# --- the judge: the rewritten report compiles ------------------------------------------------

def _typst(root, entry, out):
    return subprocess.run(["typst", "compile", "--root", str(root), str(entry), str(out)], capture_output=True, text=True, encoding="utf-8")


def _pdf_text(path):
    from pypdf import PdfReader
    return "\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)


def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


LEGACY = {
    "Bericht (typst)/Statischer Rapport.typ": (
        '#import "config.typ": conf\n#import "commands.typ": *\n#show: conf\n\n= Bericht\n\n'
        '#include "Sections/a.typ"\n#{ set heading(offset: 1); include "Sections/b.typ" }\n#image("Images/pic.svg", width: 1cm)\n'
    ),
    "Bericht (typst)/config.typ": '#let conf(doc) = {\n  set page(paper: "a4")\n  doc\n}\n',
    "Bericht (typst)/commands.typ": (
        '#import "_woodcore/lib/engine.typ": engine-value\n'
        '#let shout(body) = strong(body)\n'
        '#let cited(project: none) = read("/" + project)\n'       # what lib/bibliography.typ does with `project:`
        '#let values = engine-value\n'
    ),
    "Bericht (typst)/references.bib": "Sherpa ETA-12/0197\n",
    "Bericht (typst)/Images/pic.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>\n',
    "Bericht (typst)/_woodcore/lib/engine.typ": '#let engine-value = json("../data/values.json")\n',
    "Bericht (typst)/_woodcore/data/values.json": '{"answer": 42}\n',
    "Bericht (typst)/Sections/a.typ": (
        '#import "../commands.typ": *\n== Alpha\n#shout[alpha] #values.answer\n#image("../Images/pic.svg", width: 1cm)\n'
        '#cited(project: "references.bib")\n#read("notes.txt")\n'
    ),
    "Bericht (typst)/Sections/notes.txt": "a note\n",
    "Bericht (typst)/Sections/b.typ": '#import "/commands.typ": shout\n== Bravo\n#shout[bravo] #read("/notes2.txt")\n',
    "Bericht (typst)/notes2.txt": "a second note\n",
}


def test_a_small_report_compiles_and_reads_the_same_after_the_migration():
    _guard()
    d = conftest.tmpdir("tp_small")
    before_dir, after_dir = d / "before", d / "after"
    for top in (before_dir, after_dir):
        for rel, text in LEGACY.items():
            _write(top / rel, text)
    old_rs = before_dir / "Bericht (typst)"
    done = _typst(old_rs, old_rs / "Statischer Rapport.typ", d / "before.pdf")
    assert done.returncode == 0, f"the legacy report does not compile:\n{done.stderr}"

    old, new, moved = _migrate(after_dir, "Bericht (typst)", "3_Bericht")
    entry = new / "Statischer Rapport.typ"
    broken = _typst(after_dir, entry, d / "broken.pdf")
    assert broken.returncode != 0, "the report compiles moved and not rewritten: the rewrite proves nothing"

    changes, unresolved = _rewrite_all(after_dir, old, new, moved)
    assert not unresolved, [(f.name, u.literal.value, u.reason) for f, u in unresolved]
    assert changes, "nothing was rewritten"
    done = _typst(after_dir, entry, d / "after.pdf")
    assert done.returncode == 0, f"the rewritten report does not compile:\n{done.stderr}"
    assert _pdf_text(d / "after.pdf") == _pdf_text(d / "before.pdf"), "the rewritten report prints something else"
    printed = _pdf_text(d / "after.pdf")
    assert "42" in printed and "a second note" in printed and "a note" in printed and "Sherpa ETA-12/0197" in printed, printed
    # the engine moved whole and is not rewritten: its own relative paths still hold
    lib = after_dir / "_woodcore" / "lib" / "engine.typ"
    assert lib.read_text(encoding="utf-8") == LEGACY["Bericht (typst)/_woodcore/lib/engine.typ"]


def _example_copy(name):
    """The example project laid out as one report -- as it was committed before it was itself migrated, rebuilt from the committed one by tests/fixtures/legacy_example.py -- in a directory of its own, its engine copied in as the tests' own copy of it is. A short name: the example's files already go deep."""
    from fixtures import legacy_example
    work = conftest.tmpdir(name)
    here = legacy_example.build(work / "p", conftest.SAMPLE)
    project.sync_engine(here)
    return here


def test_the_example_projects_report_migrates_compiles_and_reads_the_same():
    """The whole thing on the committed example: its report folder moved into the new layout by rename, every `.typ` rewritten, then compiled with the project as root — and the pages say what the old report's did."""
    _guard()
    here = _example_copy("tp_ex")
    top = here.file.parent
    old_rs = here.report_typ.parent
    assert old_rs != top and here.typst_root == old_rs, "the example is not the legacy shape this check starts from"
    d = top.parent
    done = _typst(old_rs, here.report_typ, d / "before.pdf")
    assert done.returncode == 0, f"the example does not compile as written:\n{done.stderr}"

    old, new, moved = _migrate(top, old_rs.name, "3_Statischer Bericht")
    assert (top / "config.typ").is_file() and (top / "commands.typ").is_file() and (top / "Images").is_dir() and (top / "_woodcore").is_dir()
    entry = new / here.report_typ.name
    broken = _typst(top, entry, d / "broken.pdf")
    assert broken.returncode != 0, "the example compiles moved and not rewritten"

    changes, unresolved = _rewrite_all(top, old, new, moved)
    assert not unresolved, [(f.name, u.literal.value, u.reason) for f, u in unresolved]
    assert {c.literal.kind for _, c in changes} <= {"import", "image"}, sorted({c.literal.kind for _, c in changes})
    assert any(c.old == "../commands.typ" and c.new == "/commands.typ" for _, c in changes)
    for file in _own_typ(top, new):
        for lit in tp.literals(tp.read_text(file)):
            target = tp._target(lit, lit.value, file.parent, top)
            assert target.exists(), f"{file.name}: {lit.kind} {lit.value!r} no longer reaches anything from its new place ({target})"
            if lit.kind == "include":
                assert not lit.value.startswith("/"), f"{file.name}: an include was made root-absolute though it moved with its entry"

    # the engine moved whole: not one of its files is changed by the rewrite
    for file in sorted((top / "_woodcore" / "lib").glob("*.typ")):
        _, c, _ = tp.rewrite(tp.read_text(file), old / "_woodcore" / "lib" / file.name, file, old, top, moved)
        assert not c, f"{file.name} of the engine would be rewritten: {[(x.old, x.new) for x in c]}"

    done = _typst(top, entry, d / "after.pdf")
    assert done.returncode == 0, f"the migrated example does not compile:\n{done.stderr}"
    assert _pdf_text(d / "after.pdf") == _pdf_text(d / "before.pdf"), "the migrated example prints something else"
