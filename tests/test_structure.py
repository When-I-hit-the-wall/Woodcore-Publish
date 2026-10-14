"""The structure of a CU or BP document (calc/structure.py, schemas/structure.schema.json).

What is held here: the schema and every rule the schema walker cannot say -- an id of the right shape and unique in its document, a tree four levels deep and no deeper, a group or a leaf and never both, a leaf's file named after its id, no key the format does not know; the file written whole, in one shape, and read back; the generated block of an entry file -- a group as a heading of its depth, a leaf as an include at the offset its depth gives, a disabled section as a comment; `sync_entry` rewriting that block and **nothing else**, idempotently, in CRLF as in LF; the tag reader, which says an unclosed tag, a closing tag that does not match, a block inside one it may not stand in and an id used twice; and -- the proof the whole design rests on -- Typst itself giving the headings the level the structure means, a section's file being the same bytes whatever the depth it is included at.

And the tree the «Structure document» tab shows (work package 2.1): the heading scan -- found after an `#import`, in a content block, after a line break, and not in a comment, a raw block, a string or a formula, each checked against what Typst itself numbers; `tree` of a CU, a BP and a report, on the example project and on synthetic ones (a commented-out include, CRLF files, a file with no heading, a file that is missing, tags that cannot be read, sharing found from the tags); `set_enabled` and `set_title` in both kinds of document, round trips byte for byte in CRLF and in LF; `align` of the nodes to the bookmarks of a real compile, the engine's own headings skipped.

**Objects in the tree** (the rework of 01.10.2026): a file that carries object tags has its objects for children -- flat, in file order, every heading and every paragraph among them, with their label, their line, the shared block they stand in and the level a window indents them at --, a file with none keeps its headings nested as it always had, a half tagged one has both; `set_title` rewrites a heading object and refuses a paragraph; `align` maps a heading object like a heading and a paragraph to nothing. The operations on the catalogue are worked out on a small skeleton of a convention and a base de projet (`_small`), the example project's own two documents being the full templates.

Every file a check writes goes into this process's own temporary folder (conftest.tmpdir).
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import conftest
from conftest import Skip

import structure
import validation

LANGS = ("fr", "de", "en")


def _leaf(section_id, **extra):
    return {"id": section_id, "file": f"Sections/{section_id}.typ", "enabled": True, **extra}


def _group(section_id, *children, **extra):
    return {"id": section_id, "title": {lang: f"{lang.upper()} {section_id}" for lang in LANGS}, "enabled": True, "children": list(children), **extra}


def _sample():
    """Four levels deep, a shared leaf, every shape there is."""
    return {
        "schema_version": "1.0", "format": "woodcore-structure", "document": "cu",
        "sections": [
            _group("general",
                   _leaf("purpose"),
                   _group("loads",
                          _leaf("live-loads", shared_with=["bp"]),
                          _group("dead", _leaf("floors")),
                          _leaf("snow"))),
            _leaf("journal"),
        ],
    }


def _refused(source, what, where="structure.json"):
    try:
        structure.check_source(source, where)
    except validation.ValidationError as exc:
        assert what in str(exc), f"refused, but for another reason: {exc}"
        return str(exc)
    raise AssertionError(f"a structure with {what} was accepted")


# --- the schema and the rules beyond it ---------------------------------------------------------

def test_a_good_structure_passes_and_a_blank_one_too():
    structure.check_source(_sample())
    structure.check_source(structure.blank("cu"))
    structure.check_source(structure.blank("bp"))


def test_an_id_is_english_lower_case_and_hyphen_separated():
    for good in ("purpose", "live-loads", "a1", "snow-load-2", "x"):
        assert structure.ID_PATTERN.match(good), good
    for bad in ("Purpose", "live_loads", "live--loads", "-live", "live-", "1live", "", "live loads", "durée", "live.loads"):
        assert not structure.ID_PATTERN.match(bad), bad
        source = _sample()
        source["sections"][1] = _leaf("x")
        source["sections"][1]["id"] = bad
        source["sections"][1]["file"] = f"Sections/{bad}.typ"
        _refused(source, "is not an id")


def test_each_defect_of_a_structure_is_refused_naming_the_section():
    def edit(change):
        source = _sample()
        change(source)
        return source

    top = lambda source: source["sections"]
    _refused(edit(lambda s: s.update(schema_version="2.0")), "expected '1.0'")
    _refused(edit(lambda s: s.update(format="woodcore-template")), "expected 'woodcore-structure'")
    _refused(edit(lambda s: s.update(document="rs")), "expected one of")
    _refused(edit(lambda s: s.pop("sections")), "missing required field 'sections'")
    _refused(edit(lambda s: s.update(extra=1)), "carries 'extra'")
    # an id is unique in its document, groups and leaves alike
    message = _refused(edit(lambda s: top(s).append(_leaf("loads"))), "id of another section")
    assert "'loads'" in message
    # depth: a group at level 4 cannot hold a fifth
    deep = edit(lambda s: top(s)[0]["children"][1]["children"][1]["children"].append(_group("below", _leaf("too-deep"))))
    _refused(deep, "5 levels deep")
    # a group or a leaf, never both and never neither
    both = edit(lambda s: top(s)[1].update(children=[]))
    _refused(both, "both a group")
    neither = edit(lambda s: top(s)[1].pop("file"))
    _refused(neither, "neither a group")
    # a leaf takes its title from the first heading of its file
    titled = edit(lambda s: top(s)[1].update(title={lang: "T" for lang in LANGS}))
    _refused(titled, "takes its title from the first heading")
    # a leaf's file is named after its id
    _refused(edit(lambda s: top(s)[1].update(file="Sections/other.typ")), "named after its id")
    _refused(edit(lambda s: top(s)[1].update(file="Other/journal.typ")), "named after its id")
    # a group is titled in the three languages
    _refused(edit(lambda s: top(s)[0]["title"].pop("de")), "'de'")
    _refused(edit(lambda s: top(s)[0]["title"].update(fr="  ")), "title in fr")
    _refused(edit(lambda s: top(s)[0]["title"].update(en="two\nlines")), "control character")
    # sharing is a file's
    _refused(edit(lambda s: top(s)[0].update(shared_with=["bp"])), "shared_with belongs to a section file")
    _refused(edit(lambda s: top(s)[1].update(shared_with=["cu"])), "shared_with lists 'cu'")
    _refused(edit(lambda s: top(s)[1].update(shared_with=["xx"])), "'xx'")
    _refused(edit(lambda s: top(s)[1].update(shared_with=["bp", "bp"])), "twice")
    # no key it does not know, and an `enabled` that is a boolean
    _refused(edit(lambda s: top(s)[1].update(enable=False)), "carries 'enable'")
    _refused(edit(lambda s: top(s)[1].update(enabled="yes")), "expected boolean")
    _refused(edit(lambda s: top(s).append({"file": "Sections/x.typ"})), "missing required field 'id'")


def test_a_section_may_be_shared_with_the_report_but_not_with_itself():
    cu = dict(structure.blank("cu"), sections=[_leaf("journal", shared_with=["bp", "rs"])])
    structure.check_source(cu)
    bp = dict(structure.blank("bp"), sections=[_leaf("journal", shared_with=["cu", "rs"])])
    structure.check_source(bp)
    _refused(dict(bp, sections=[_leaf("journal", shared_with=["bp"])]), "shared_with lists 'bp'")


def test_the_tree_is_walked_in_document_order_with_its_depths():
    source = _sample()
    walked = [(n["id"], depth, parent["id"] if parent else None) for n, depth, parent in structure.walk(source)]
    assert walked == [("general", 1, None), ("purpose", 2, "general"), ("loads", 2, "general"), ("live-loads", 3, "loads"),
                      ("dead", 3, "loads"), ("floors", 4, "dead"), ("snow", 3, "loads"), ("journal", 1, None)], walked
    assert [(n["id"], d) for n, d in structure.leaves(source)] == [("purpose", 2), ("live-loads", 3), ("floors", 4), ("snow", 3), ("journal", 1)]
    assert structure.find(source, "dead")[1] == 3 and structure.find(source, "nope") is None
    assert structure.title_of(source["sections"][0], "de") == "DE general" and structure.title_of(source["sections"][1], "de") == ""


# --- the file ---------------------------------------------------------------------------------------

def test_the_file_is_written_whole_in_one_shape_and_read_back():
    folder = conftest.tmpdir("structure_write")
    path = folder / structure.FILE
    # keys in the wrong order, `enabled` left out, a title's languages shuffled, an empty shared_with
    scrambled = {"sections": [{"children": [{"file": "Sections/purpose.typ", "id": "purpose", "shared_with": []}],
                               "title": {"en": "General", "de": "Allgemeines", "fr": "Généralités"}, "id": "general"}],
                 "document": "cu", "format": "woodcore-structure", "schema_version": "1.0"}
    structure.write(path, scrambled)
    raw = path.read_bytes()
    assert b"\r" not in raw and raw.endswith(b"}\n"), "LF, one trailing newline, whatever the platform"
    text = raw.decode("utf-8")
    assert text == structure.dumps(scrambled)
    assert "\n  \"sections\": [\n    {\n      \"id\": \"general\"," in text, "two-space indent, id first"
    assert "Généralités" in text, "no \\u escapes"
    written = json.loads(text)
    assert list(written) == ["schema_version", "format", "document", "sections"]
    group = written["sections"][0]
    assert list(group) == ["id", "title", "enabled", "children"] and list(group["title"]) == ["fr", "de", "en"]
    assert group["enabled"] is True and group["children"][0]["enabled"] is True
    assert list(group["children"][0]) == ["id", "file", "enabled"], "an empty shared_with is left out"
    assert not (folder / (structure.FILE + ".tmp")).exists(), "written beside itself and moved into place"
    assert structure.read(path) == written
    # the same structure again writes the same bytes
    structure.write(path, structure.read(path))
    assert path.read_bytes() == raw


def test_a_shared_leaf_is_written_with_its_documents():
    folder = conftest.tmpdir("structure_shared")
    structure.write(folder / structure.FILE, _sample())
    written = json.loads((folder / structure.FILE).read_text(encoding="utf-8"))
    leaf = written["sections"][0]["children"][1]["children"][0]
    assert list(leaf) == ["id", "file", "enabled", "shared_with"] and leaf["shared_with"] == ["bp"]


def test_a_write_that_is_refused_leaves_the_old_file_as_it_was():
    folder = conftest.tmpdir("structure_refused")
    path = folder / structure.FILE
    structure.write(path, _sample())
    before = path.read_bytes()
    broken = _sample()
    broken["sections"].append(_leaf("journal"))
    try:
        structure.write(path, broken)
    except validation.ValidationError:
        pass
    else:
        raise AssertionError("a structure with a duplicate id was written")
    assert path.read_bytes() == before and not (folder / (structure.FILE + ".tmp")).exists()


def test_reading_a_missing_or_broken_file_is_an_error_naming_it():
    folder = conftest.tmpdir("structure_read")
    for name, content in (("missing.json", None), ("broken.json", "{not json"), ("wrong.json", '{"schema_version": "1.0"}')):
        path = folder / name
        if content is not None:
            path.write_text(content, encoding="utf-8")
        try:
            structure.read(path)
        except validation.ValidationError as exc:
            assert name in str(exc), exc
        else:
            raise AssertionError(f"{name} was read")


# --- the generated block --------------------------------------------------------------------------------

def test_the_block_writes_headings_for_groups_and_offsets_for_leaves():
    lines = structure.block_lines(_sample(), "fr")
    assert lines == [
        '#heading(level: 1, "FR general")',
        '#{ set heading(offset: 1); include "Sections/purpose.typ" }',
        '#heading(level: 2, "FR loads")',
        '#{ set heading(offset: 2); include "Sections/live-loads.typ" }',
        '#heading(level: 3, "FR dead")',
        '#{ set heading(offset: 3); include "Sections/floors.typ" }',
        '#{ set heading(offset: 2); include "Sections/snow.typ" }',
        '#include "Sections/journal.typ"',
    ], lines
    # the group's title is the document's language
    assert structure.block_lines(_sample(), "de")[0] == '#heading(level: 1, "DE general")'
    assert structure.block_lines(_sample(), "en")[2] == '#heading(level: 2, "EN loads")'


def test_a_disabled_section_is_a_comment_and_a_disabled_group_takes_its_subtree_with_it():
    source = _sample()
    source["sections"][0]["children"][1]["children"][1]["enabled"] = False      # the group `dead`
    assert structure.block_lines(source, "fr")[4:7] == ['// disabled: dead', '// disabled: floors (Sections/floors.typ)', '#{ set heading(offset: 2); include "Sections/snow.typ" }']
    source = _sample()
    source["sections"][0]["children"][0]["enabled"] = False                      # purpose
    assert '// disabled: purpose (Sections/purpose.typ)' in structure.block_lines(source, "fr")
    assert not any("purpose.typ\" }" in line for line in structure.block_lines(source, "fr"))
    source = _sample()
    source["sections"][0]["enabled"] = False                                      # the whole of `general`
    assert structure.block_lines(source, "fr") == [
        "// disabled: general", "// disabled: purpose (Sections/purpose.typ)", "// disabled: loads",
        "// disabled: live-loads (Sections/live-loads.typ)", "// disabled: dead", "// disabled: floors (Sections/floors.typ)",
        "// disabled: snow (Sections/snow.typ)", '#include "Sections/journal.typ"']


def test_a_title_with_a_quote_or_a_backslash_is_written_as_a_string():
    source = _sample()
    source["sections"][0]["title"]["fr"] = 'Le "bon" \\ titre $x$'
    assert structure.block_lines(source, "fr")[0] == '#heading(level: 1, "Le \\"bon\\" \\\\ titre $x$")'
    assert structure.typst_string("a\nb") == '"a\\nb"'


def test_the_block_of_a_blank_structure_is_empty_and_the_language_must_be_one():
    assert structure.block_lines(structure.blank("bp"), "fr") == []
    try:
        structure.block_lines(_sample(), "it")
    except structure.StructureError as exc:
        assert "'it'" in str(exc)
    else:
        raise AssertionError("an unknown language was accepted")
    text = structure.block_text(_sample(), "fr", newline="\r\n")
    assert text.startswith(structure.START_TAG + "\r\n") and text.endswith(structure.END_TAG + "\r\n") and "\n" not in text.replace("\r\n", "")


# --- sync_entry ----------------------------------------------------------------------------------------------

ENTRY_BEFORE = '// My own title page and settings.\n#import "/commands.typ": *\n#set-report-language("fr")\n\n// --- Sections ---\n'
ENTRY_AFTER = "\n// the engineer's own trailer\n#pagebreak()\n"


def _entry(name, ending="\n", between=("#include \"Sections/old.typ\"",), start_tag=structure.START_TAG):
    """An entry file with a structure block holding `between`, in `ending` line endings throughout."""
    text = ENTRY_BEFORE + start_tag + "\n" + "".join(line + "\n" for line in between) + structure.END_TAG + "\n" + ENTRY_AFTER
    path = conftest.tmpdir(name) / "Entry.typ"
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", ending))
    return path


def _bytes(path):
    return path.read_bytes().decode("utf-8")


def test_sync_entry_rewrites_the_block_and_nothing_else():
    path = _entry("sync_basic")
    before = _bytes(path)
    assert structure.sync_entry(path, _sample(), "fr") is True
    after = _bytes(path)
    head, _, rest = after.partition(structure.START_TAG + "\n")
    body, _, tail = rest.partition(structure.END_TAG + "\n")
    assert head == ENTRY_BEFORE and tail == ENTRY_AFTER, "the text outside the two tags was touched"
    assert body.splitlines() == structure.block_lines(_sample(), "fr")
    assert "old.typ" in before and "old.typ" not in after
    assert not path.with_name(path.name + ".tmp").exists()


def test_sync_entry_is_idempotent_and_writes_nothing_the_second_time():
    path = _entry("sync_idempotent")
    assert structure.sync_entry(path, _sample(), "fr") is True
    bytes_once, mtime = path.read_bytes(), path.stat().st_mtime_ns
    assert structure.sync_entry(path, _sample(), "fr") is False
    assert path.read_bytes() == bytes_once and path.stat().st_mtime_ns == mtime, "an unchanged block rewrote the file"
    # a change to the structure changes the block, and only it
    changed = _sample()
    changed["sections"][1]["enabled"] = False
    assert structure.sync_entry(path, changed, "fr") is True
    assert "// disabled: journal (Sections/journal.typ)" in _bytes(path)
    # a change of language rewrites the titles
    assert structure.sync_entry(path, changed, "de") is True and '"DE general"' in _bytes(path)


def test_sync_entry_keeps_crlf_and_lf_as_the_file_has_them():
    crlf = _entry("sync_crlf", ending="\r\n")
    assert structure.sync_entry(crlf, _sample(), "fr") is True
    data = crlf.read_bytes()
    assert data.count(b"\r\n") == data.count(b"\n") and b"\r\r" not in data, "a line was written with another ending than the file's"
    assert structure.sync_entry(crlf, _sample(), "fr") is False
    lf = _entry("sync_lf")
    assert structure.sync_entry(lf, _sample(), "fr") is True
    assert b"\r" not in lf.read_bytes()
    # the text outside the tags, CRLF included, is byte for byte what it was
    text = _bytes(crlf)
    assert text.startswith(ENTRY_BEFORE.replace("\n", "\r\n")) and text.endswith(ENTRY_AFTER.replace("\n", "\r\n"))
    # both files say the same thing modulo their endings
    assert _bytes(crlf).replace("\r\n", "\n") == _bytes(lf)


def test_sync_entry_leaves_the_start_tags_own_comment_to_the_engineer():
    path = _entry("sync_comment", start_tag="// woodcore:structure -- le texte que j'ai écrit moi-même")
    assert structure.sync_entry(path, _sample(), "fr") is True
    assert "// woodcore:structure -- le texte que j'ai écrit moi-même\n#heading" in _bytes(path)


def test_sync_entry_takes_a_path_to_a_structure_json_as_well_as_a_structure():
    folder = conftest.tmpdir("sync_path")
    structure.write(folder / structure.FILE, _sample())
    path = folder / "Entry.typ"
    path.write_text(structure.START_TAG + "\n" + structure.END_TAG + "\n", encoding="utf-8")
    assert structure.sync_entry(path, folder / structure.FILE, "en") is True
    assert '#heading(level: 1, "EN general")' in path.read_text(encoding="utf-8")


def test_sync_entry_refuses_an_entry_it_cannot_lay_out():
    def refused(text, what):
        folder = conftest.tmpdir("sync_refused")
        path = folder / "Entry.typ"
        path.write_text(text, encoding="utf-8")
        before = path.read_bytes()
        try:
            structure.sync_entry(path, _sample(), "fr")
        except structure.StructureError as exc:
            assert what in str(exc), exc
        else:
            raise AssertionError(f"an entry with {what} was synced")
        assert path.read_bytes() == before, "a refused sync still wrote"

    refused("#include \"x.typ\"\n", "has no `// woodcore:structure`")
    refused(structure.START_TAG + "\n#include \"x.typ\"\n", "never closed")
    refused(structure.END_TAG + "\n", "which is not open")
    twice = structure.START_TAG + "\n" + structure.END_TAG + "\n" + structure.START_TAG + "\n" + structure.END_TAG + "\n"
    refused(twice, "a structure block is used twice")
    # a tag problem anywhere in the file: it is one Woodcore does not rewrite
    refused(structure.START_TAG + "\n" + structure.END_TAG + "\n// woodcore:object doc-table loose\n", "never closed")
    refused(structure.START_TAG + "\n" + structure.END_TAG + "\n// woodcore:nonsense x\n", "not a kind of tag")
    try:
        structure.sync_entry(_entry("sync_language"), _sample(), "it")
    except structure.StructureError as exc:
        assert "'it'" in str(exc)
    else:
        raise AssertionError("an unknown language was accepted")


# --- the tags ---------------------------------------------------------------------------------------------------

def _problems(text, **kwargs):
    return structure.check_tags(text, **kwargs)


def test_a_well_formed_file_has_no_tag_problem_and_its_blocks_are_found():
    text = "\n".join([
        "= Live loads",
        "// woodcore:shared live-loads",
        "Some text.",
        "  // woodcore:object live-load-table loads-table",
        "#live-load-table()",
        "  // woodcore:/object loads-table",
        "// woodcore:object doc-field site",
        "#doc-field()",
        "// woodcore:/object site",
        "// woodcore:/shared live-loads",
        "// woodcore:object doc-choice class",
        "// woodcore:/object class",
    ]) + "\n"
    blocks, problems = structure.pair_tags(text)
    assert problems == []
    assert [(b.kind, b.id, b.type, b.start, b.end) for b in blocks] == [
        ("shared", "live-loads", None, 1, 9), ("object", "loads-table", "live-load-table", 3, 5),
        ("object", "site", "doc-field", 6, 8), ("object", "class", "doc-choice", 10, 11)], blocks


def test_a_tag_is_a_line_comment_alone_on_its_line_with_the_exact_prefix():
    for text in ("//woodcore:shared x\n", "// Woodcore:shared x\n", "x // woodcore:shared x\n", "/* // woodcore:shared x */\n",
                 "// see woodcore:shared x\n", "// woodcore :shared x\n"):
        tags, problems = structure.scan_tags(text)
        assert tags == [] and problems == [], text
    # but leading white space is allowed, and CRLF reads like LF
    tags, _ = structure.scan_tags("\t  // woodcore:shared x\r\n// woodcore:/shared x")
    assert [(t.line, t.kind, t.closing, t.id) for t in tags] == [(0, "shared", False, "x"), (1, "shared", True, "x")]


def test_an_unclosed_tag_is_said_where_it_opens():
    text = "a\n// woodcore:object doc-table one\nb\n"
    assert _problems(text) == ["line 2: object one is never closed"]
    text = "// woodcore:shared s\n// woodcore:object doc-table one\n// woodcore:/object one\n"
    assert _problems(text) == ["line 1: shared s is never closed"]


def test_a_closing_tag_that_does_not_match_is_said_and_one_slip_is_not_a_cascade():
    assert _problems("// woodcore:/object one\n") == ["line 1: closes object one, which is not open"]
    mismatched = "// woodcore:object doc-table one\n// woodcore:/object two\n"
    problems = _problems(mismatched)
    assert len(problems) == 2 and "object one is never closed" in problems[0] and "closes object two, which is not open" in problems[1], problems
    # a closing tag naming a block further out unwinds to it: the block it cuts short is reported once
    text = "// woodcore:shared s\n// woodcore:object doc-table one\n// woodcore:/shared s\n"
    assert _problems(text) == ["line 2: object one is never closed before line 3"]
    # a kind that matches and an id that does not
    assert any(p.startswith("line 2: closes shared b, which is not open") for p in _problems("// woodcore:shared a\n// woodcore:/shared b\n"))


def test_a_block_inside_one_that_may_not_hold_it_is_said():
    assert _problems("// woodcore:shared a\n// woodcore:shared b\n// woodcore:/shared b\n// woodcore:/shared a\n") == [
        "line 2: a shared tag cannot stand inside the shared block opened at line 1"]
    assert _problems("// woodcore:object doc-table a\n// woodcore:object doc-field b\n// woodcore:/object b\n// woodcore:/object a\n") == [
        "line 2: an object tag cannot stand inside the object block opened at line 1"]
    # an object straddling a shared block: its own closing tag finds the shared block innermost
    straddle = "// woodcore:shared s\n// woodcore:object doc-table o\n// woodcore:/shared s\n// woodcore:/object o\n"
    assert any("never closed" in p for p in _problems(straddle)) and any("closes object o" in p for p in _problems(straddle))
    # the generated structure block holds nothing
    assert _problems(structure.START_TAG + "\n// woodcore:shared s\n// woodcore:/shared s\n" + structure.END_TAG + "\n")[0].startswith("line 2: a shared tag cannot stand inside the structure block")


def test_an_id_used_twice_in_one_file_is_said():
    text = "// woodcore:object doc-table t\n// woodcore:/object t\n// woodcore:object doc-field t\n// woodcore:/object t\n"
    assert _problems(text) == ["line 3: the object id 't' is used twice in one file (first at line 1)"]
    text = "// woodcore:shared s\n// woodcore:/shared s\n// woodcore:shared s\n// woodcore:/shared s\n"
    assert _problems(text) == ["line 3: the shared id 's' is used twice in one file (first at line 1)"]
    # the same id as an object and as a shared block is two different things
    assert _problems("// woodcore:shared t\n// woodcore:object doc-table t\n// woodcore:/object t\n// woodcore:/shared t\n") == []


def test_a_tag_that_cannot_be_read_is_a_problem_and_no_tag():
    assert "not a kind of tag" in _problems("// woodcore:table x\n")[0]
    assert "reads `woodcore:object <type> <id>`" in _problems("// woodcore:object x\n")[0]
    assert "reads `woodcore:shared <id>`" in _problems("// woodcore:shared\n")[0]
    assert "reads `woodcore:/shared <id>`" in _problems("// woodcore:/shared a b\n")[0]
    assert "is not an id" in _problems("// woodcore:shared Not_An_Id\n")[0]
    assert "is not a parametric object" in _problems("// woodcore:object frobnicate x\n")[0]
    assert _problems("// woodcore:object frobnicate x\n// woodcore:/object x\n", object_types=None) == [], "object_types=None allows any call"
    assert any("carries nothing after it" in p for p in _problems(structure.START_TAG + "\n// woodcore:/structure extra\n"))


# --- Typst gives the headings the level the structure means --------------------------------------------------------

def _headings(root, entry):
    """[(level, title)] of the outlined headings of the document `entry`, as Typst itself numbers them (`typst eval` of the document's own `query`)."""
    done = subprocess.run(
        ["typst", "eval", "--root", str(root), "--in", str(entry),
         "query(heading.where(outlined: true)).map(it => (level: it.level, title: it.body.text))"],
        capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    return [(h["level"], h["title"]) for h in json.loads(done.stdout)]


def _document(root, name, source, language="fr"):
    """A throwaway document folder under `root`: an entry holding only the structure block, written from `source`, and a section file per leaf whose only line is its heading."""
    folder = root / name
    (folder / "Sections").mkdir(parents=True)
    for node, _depth in structure.leaves(source):
        (folder / node["file"]).write_text(f"= Title {node['id']}\n", encoding="utf-8")
    entry = folder / "Entry.typ"
    entry.write_text(structure.START_TAG + "\n" + structure.END_TAG + "\n", encoding="utf-8")
    structure.sync_entry(entry, source, language)
    return entry


def test_typst_gives_the_headings_the_level_the_structure_means():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    root = conftest.tmpdir("structure_levels")
    entry = _document(root, "1_Doc", _sample())
    assert _headings(root, entry) == [
        (1, "FR general"), (2, "Title purpose"),
        (2, "FR loads"), (3, "Title live-loads"),
        (3, "FR dead"), (4, "Title floors"),
        (3, "Title snow"),
        (1, "Title journal"),
    ]


def test_a_section_file_is_independent_of_the_depth_it_is_included_at():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    root = conftest.tmpdir("structure_independent")
    first = _document(root, "1_Deep", _sample())
    # the same leaf, at the top of another document
    flat = {"schema_version": "1.0", "format": "woodcore-structure", "document": "bp", "sections": [_leaf("floors"), _leaf("snow")]}
    second = _document(root, "2_Flat", flat)
    assert (first.parent / "Sections" / "floors.typ").read_bytes() == (second.parent / "Sections" / "floors.typ").read_bytes(), "the two copies of the file are not the same bytes"
    assert [h for h in _headings(root, first) if h[1] == "Title floors"] == [(4, "Title floors")]
    assert _headings(root, second) == [(1, "Title floors"), (1, "Title snow")]


def test_a_disabled_section_is_not_in_the_document_and_its_file_is_still_there():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    root = conftest.tmpdir("structure_disabled")
    source = _sample()
    entry = _document(root, "1_Doc", source)
    source["sections"][0]["children"][1]["children"][0]["enabled"] = False      # live-loads
    structure.sync_entry(entry, source, "fr")
    titles = [title for _level, title in _headings(root, entry)]
    assert "Title live-loads" not in titles and "Title floors" in titles
    assert (entry.parent / "Sections" / "live-loads.typ").is_file(), "a disabled section keeps its file"
    # a disabled group takes its subtree out
    source["sections"][0]["children"][1]["children"][1]["enabled"] = False      # dead
    structure.sync_entry(entry, source, "fr")
    titles = [title for _level, title in _headings(root, entry)]
    assert "FR dead" not in titles and "Title floors" not in titles and "Title snow" in titles


# --- the headings of a file ------------------------------------------------------------------------------------------

def _scan(text):
    return [(h.level, h.title, h.form) for h in structure.scan_headings(text)]


def test_markup_headings_and_heading_calls_are_found_and_nothing_else_is():
    text = "\n".join([
        "= One",
        "== Two <label>",
        "   === Three   // a comment",
        "#heading(level: 2, \"Four\")",
        "#heading(level: 3)[Five]",
        "#heading[Six]",
        "// = commented out",
        "/* = in a block comment",
        "== also in it */",
        "```",
        "= in a raw block",
        "```",
        "#let s = \"a",
        "= in a string",
        "b\"",
        "$ x",
        "= in a formula",
        "y $",
        "=not a heading",
        "==> not a heading",
        "text = not at the start",
        "= Seven",
        "",
    ])
    assert _scan(text) == [
        (1, "One", "markup"), (2, "Two", "markup"), (3, "Three", "markup"), (2, "Four", "call"),
        (3, "Five", "call"), (1, "Six", "call"), (1, "Seven", "markup"),
    ]


def test_a_heading_after_an_import_a_let_a_line_break_and_in_a_content_block_is_found():
    # the start of every section file: an #import, a blank line and the heading -- the lexer is in code mode when the newline comes, and the heading's line starts in markup
    assert _scan('#import "/commands.typ": *\n\n= Title\n') == [(1, "Title", "markup")]
    assert _scan('#import "/commands.typ": *\n= Title\n') == [(1, "Title", "markup")]
    assert _scan('#let x = 1\n== After a let\n') == [(2, "After a let", "markup")]
    assert _scan('#set page(paper: "a4")\n#show: conf\n= After two statements\n') == [(1, "After two statements", "markup")]
    assert _scan("text \\\n= after a line break\n") == [(1, "after a line break", "markup")]
    # a heading in a content block, which is in the document whenever the condition holds
    assert _scan("#if connector-ids().len() > 0 [\n  == Conditional\n  text\n]\n= After\n") == [(2, "Conditional", "markup"), (1, "After", "markup")]
    assert _scan("#[= Block start]\n") == [(1, "Block start", "markup")]
    # no newline at the end of the file, and an empty heading
    assert _scan("= Last") == [(1, "Last", "markup")]
    assert _scan("=\n") == [(1, "", "markup")]


def test_a_heading_call_is_read_with_its_level_its_title_and_where_the_title_is():
    text = ('#heading(level: 2, supplement: "S", "Quoted, with a comma")\n'
            '#heading(level: 3,\n  [Content (with) parens])\n'
            '#heading(depth: 4)[Trailing block]\n'
            '#heading(level: 2, title-variable)\n')
    found = structure.scan_headings(text)
    assert [(h.level, h.title, h.form) for h in found] == [
        (2, "Quoted, with a comma", "call"), (3, "Content (with) parens", "call"),
        (4, "Trailing block", "call"), (2, "title-variable", "call")]
    assert [text[slice(*h.span)] if h.span else None for h in found] == ["Quoted, with a comma", "Content (with) parens", "Trailing block", None]
    assert [h.line for h in found] == [0, 1, 3, 4]


def test_heading_titles_leave_out_a_label_and_a_comment_and_keep_the_markup_and_crlf_and_bom_are_read():
    found = structure.scan_headings("= Title <intro>\r\n== *Bold* and `raw` // note\r\n=== https://example.org/x\r\n")
    assert [h.title for h in found] == ["Title", "*Bold* and `raw`", "https://example.org/x"]
    assert [h.line for h in found] == [0, 1, 2]
    text = "= Title\r\n"
    [bom] = structure.scan_headings("\ufeff" + text)
    assert (bom.title, bom.level, bom.line) == ("Title", 1, 0)
    assert ("\ufeff" + text)[slice(*bom.span)] == "Title", "the span of a heading after a BOM is an offset into the text as read, BOM included"


def test_the_headings_of_the_examples_reports_match_the_ones_typst_numbers():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    # Typst is the judge of what a heading is: every outlined heading of the example's report is one the scan found, at the same level -- the ones a condition or a loop would print on top excepted
    here = conftest.PROJECT
    scanned = [(n.level, structure.plain_title(n.title)) for n in structure.flatten(structure.tree(here, "rs")) if n.active]
    assert len(scanned) > 30
    printed = _headings(here.typst_root, here.document_typ("rs"))
    assert [(level, structure.plain_title(title)) for level, title in printed] == scanned


# --- the tree --------------------------------------------------------------------------------------------------------

def _summary(nodes, depth=0):
    """[(depth, kind, id, level, title, enabled)] of a tree, for a test to compare against."""
    out = []
    for node in nodes:
        out.append((depth, node.kind, node.id, node.level, node.title, node.enabled))
        out += _summary(node.children, depth + 1)
    return out


def test_the_tree_of_the_example_report_is_its_include_lines_and_their_headings():
    here = conftest.PROJECT
    nodes = structure.tree(here, "rs")
    assert [n.id for n in nodes] == ["001-einleitung", "002-grundlagen", "003-baustoffe", "004-einwirkungen", "005-tragwerksanalyse", "006-nachweise", "007-literatur"]
    for node in nodes:
        assert (node.kind, node.level, node.separate_file, node.enabled, node.active, node.problems, node.parent) == ("file", 1, True, True, True, (), None)
        assert node.file == f"Sections/{node.id}.typ" and node.line == 2, "the file's heading follows its import and a blank line"
    assert [n.title for n in nodes] == ["Einleitung", "Grundlagen", "Baustoffe", "Einwirkungen", "Tragwerksanalyse", "Nachweise", "Literatur"]
    grundlagen = nodes[1]
    assert [(c.level, c.title) for c in grundlagen.children] == [(2, "Velo Unterstand"), (2, "Pavillon"), (2, "Gerätehaus"), (2, "Fluchttreppe")]
    assert all(c.kind == "heading" and not c.separate_file and c.file == grundlagen.file and c.parent == "002-grundlagen" for c in grundlagen.children)
    assert [(c.level, c.title) for c in grundlagen.children[0].children] == [(3, "Positionsplan"), (3, "Pläne")]
    assert grundlagen.children[0].children[0].id == "002-grundlagen#3" and grundlagen.children[0].children[0].parent == "002-grundlagen#2"
    # a heading inside a content block that only prints where there are connectors
    assert [(c.level, c.title) for c in nodes[2].children] == [(2, "Verbindungsmittel")]
    deep = [n for n in structure.flatten(nodes) if n.level == 4]
    assert [n.title for n in deep] == ["Tragsicherheit", "Polares Trägheitsmoment"]
    ids = [n.id for n in structure.flatten(nodes)]
    assert len(ids) == len(set(ids)), "an id is unique in its document"
    assert structure.flatten(nodes) == structure.flatten(structure.flatten(nodes)), "flatten of a flat list is itself"
    assert structure.find_node(nodes, "002-grundlagen#3").title == "Positionsplan" and structure.find_node(nodes, "nowhere") is None


def test_the_tree_of_a_cu_and_a_bp_is_their_structure_and_the_objects_of_their_files():
    """The example project's convention and base de projet are the full templates: every section a file, its heading and its paragraphs and its tables objects of it."""
    here = conftest.PROJECT
    for mode, first_group, leaves in (("cu", "introduction", ("purpose", "scope-and-limits")), ("bp", "general", ("purpose-of-basis-of-design", "scope-and-limits"))):
        nodes = structure.tree(here, mode)
        group = nodes[0]
        # a chapter is a file of its own, its heading a level-1 heading object after the import (06.10.2026)
        assert (group.kind, group.id, group.level, group.file, group.line, group.separate_file, group.parent, group.active) == ("group", first_group, 1, f"Sections/{first_group}.typ", 3, True, None, True), mode
        assert [c.id for c in group.children] == list(leaves) and all(c.kind == "file" and c.level == 2 and c.parent == first_group and c.separate_file for c in group.children)
        leaf = group.children[0]
        assert (leaf.file, leaf.line) == (f"Sections/{leaves[0]}.typ", 3), "the file's heading follows its import, a blank line and the tag of the heading object"
        assert [c.kind for c in leaf.children] == ["object"] * len(leaf.children) and leaf.children[0].object_type == "heading", "every heading of a tagged file is an object, the first among them"
        assert nodes[-1].id == "journal" and nodes[-1].level == 1 and nodes[-1].problems == () and nodes[-1].children[0].object_type == "heading"
        ids = [n.id for n in structure.flatten(nodes)]
        assert len(ids) == len(set(ids)), "an id is unique in its document"
    # a chapter's title is its file's, written in the document's own language like any heading: the language asked for no longer reaches it (06.10.2026)
    fr = structure.tree(here, "cu", language="fr")
    assert fr[0].title == "Zweck und Abgrenzung" and fr[0].children[0].title == "Zweck der Nutzungsvereinbarung"
    try:
        structure.tree(here, "cu", language="it")
    except structure.StructureError as exc:
        assert "it" in str(exc)
    else:
        raise AssertionError("an unknown language was accepted")


def test_the_language_of_a_document_is_its_config_typs_then_its_entrys_then_german():
    root = conftest.tmpdir("tree_language")
    here = _modes_project(root)
    assert structure.document_language(here, "cu") == "de"
    (root / "config.typ").write_text('#let doc-lang = "fr"\n', encoding="utf-8")
    assert structure.document_language(here, "cu") == "fr"
    (root / "config.typ").write_text("// no language\n", encoding="utf-8")
    here.document_typ("cu").write_text('#set-report-language(sys.inputs.at("lang", default: "en"))\n', encoding="utf-8")
    assert structure.document_language(here, "cu") == "en"


def test_a_project_laid_out_as_a_report_alone_has_no_cu_and_no_bp_to_show():
    import project
    root = conftest.tmpdir("tree_legacy")
    here = project.Project(root / "P.woodcore", {})
    assert here.modes == ("rs",)
    for mode in ("cu", "bp", "x"):
        try:
            structure.tree(here, mode)
        except structure.StructureError:
            pass
        else:
            raise AssertionError(f"a tree of {mode!r} was made for a report alone")


# A project in three documents under `root`, in memory: its folders made and nothing in them -- what a check then writes, byte for byte as it means it.

def _modes_project(root, language="de"):
    import documents
    import project
    here = project.Project(root / "P.woodcore", {"layout": documents.layout_for(language)})
    for mode in here.modes:
        here.document_dir(mode).mkdir(parents=True, exist_ok=True)
        (here.document_dir(mode) / "Sections").mkdir(exist_ok=True)
    return here


def _write(path, text, ending="\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", ending))
    return path


def _report(root, ending="\n"):
    """A report with a commented-out include, an indented one, and sections written in `ending`."""
    here = _modes_project(root)
    _write(here.document_typ("rs"), "\n".join([
        "// entry", '#set page(paper: "a4")', "",
        '#include "Sections/001-a.typ"',
        '// #include "Sections/002-b.typ"',
        '  #include "Sections/003-c.typ"',
        '#include "Sections/004-d.typ"', "",
    ]), ending)
    sections = here.document_dir("rs") / "Sections"
    _write(sections / "001-a.typ", '#import "/commands.typ": *\n\n= Alpha\n\ntext\n\n== Alpha one\n\n=== Alpha one one\n\n== Alpha two\n', ending)
    _write(sections / "002-b.typ", "= Beta\n\n== Beta one\n", ending)
    _write(sections / "003-c.typ", "== Gamma starts at two\n\n=== Gamma deeper\n\n= Gamma second top\n", ending)
    _write(sections / "004-d.typ", "No heading at all.\n", ending)
    return here


def test_a_report_with_a_commented_include_and_crlf_files_is_read_with_its_states():
    root = conftest.tmpdir("tree_report")
    for ending in ("\n", "\r\n"):
        here = _report(root / ("crlf" if ending == "\r\n" else "lf"), ending)
        nodes = structure.tree(here, "rs")
        assert [(n.id, n.enabled, n.active, n.level, n.title) for n in nodes] == [
            ("001-a", True, True, 1, "Alpha"),
            ("002-b", False, False, 1, "Beta"),
            ("003-c", True, True, 2, "Gamma starts at two"),
            ("004-d", True, True, 1, "004-d"),
        ], ending
        assert nodes[3].line is None and nodes[3].children == [], "a file with no heading is a node that takes its id for a title"
        assert [(c.level, c.title) for c in nodes[0].children] == [(2, "Alpha one"), (2, "Alpha two")]
        assert [(c.level, c.title) for c in nodes[0].children[0].children] == [(3, "Alpha one one")]
        # the headings of a disabled file are listed, and not printed
        assert [(c.title, c.enabled, c.active) for c in nodes[1].children] == [("Beta one", False, False)]
        # a file that starts at level 2 keeps a second level-1 heading inside itself
        assert [(c.level, c.title) for c in nodes[2].children] == [(3, "Gamma deeper"), (1, "Gamma second top")]
        assert all("\r" not in n.title for n in structure.flatten(nodes))


def test_the_file_a_structure_names_and_nobody_wrote_is_a_node_that_says_so():
    root = conftest.tmpdir("tree_missing")
    here = _modes_project(root)
    source = {"schema_version": "1.0", "format": "woodcore-structure", "document": "cu", "sections": [_leaf("present"), _leaf("absent")]}
    structure.write(here.structure_file("cu"), source)
    _write(here.document_dir("cu") / "Sections" / "present.typ", "= Here\n")
    present, absent = structure.tree(here, "cu")
    assert present.problems == () and absent.title == "absent" and absent.line is None
    assert len(absent.problems) == 1 and "Sections/absent.typ" in absent.problems[0] and "does not exist" in absent.problems[0]
    # a structure.json that is not there is an error and not an empty tree
    try:
        structure.tree(here, "bp")
    except validation.ValidationError as exc:
        assert "structure.json" in str(exc)
    else:
        raise AssertionError("a document without its structure.json was given a tree")


def test_a_file_whose_tags_cannot_be_read_says_so_in_its_node():
    root = conftest.tmpdir("tree_tags")
    here = _modes_project(root)
    structure.write(here.structure_file("cu"), {"schema_version": "1.0", "format": "woodcore-structure", "document": "cu", "sections": [_leaf("torn")]})
    _write(here.document_dir("cu") / "Sections" / "torn.typ", "= Torn\n// woodcore:shared a-block\ntext\n")
    [node] = structure.tree(here, "cu")
    assert any("never closed" in problem for problem in node.problems), node.problems


# --- shared -----------------------------------------------------------------------------------------------------------

def test_a_section_is_shared_with_what_structure_json_lists_and_with_the_documents_that_carry_its_tag():
    root = conftest.tmpdir("tree_shared")
    here = _modes_project(root)
    cu = {"schema_version": "1.0", "format": "woodcore-structure", "document": "cu",
          "sections": [_leaf("live-loads", shared_with=["bp"]), _leaf("listed-only", shared_with=["rs"]), _leaf("private")]}
    bp = {"schema_version": "1.0", "format": "woodcore-structure", "document": "bp", "sections": [_leaf("loads"), _leaf("other")]}
    structure.write(here.structure_file("cu"), cu)
    structure.write(here.structure_file("bp"), bp)
    shared = "= Loads\n\n// woodcore:shared live-load-table\ntext\n// woodcore:/shared live-load-table\n"
    _write(here.document_dir("cu") / "Sections" / "live-loads.typ", shared)
    _write(here.document_dir("cu") / "Sections" / "listed-only.typ", "= Listed\n")
    _write(here.document_dir("cu") / "Sections" / "private.typ", "= Private\n// woodcore:shared nobody-else\ntext\n// woodcore:/shared nobody-else\n")
    _write(here.document_dir("bp") / "Sections" / "loads.typ", "= Other name\n\n" + shared.split("\n\n", 1)[1])
    _write(here.document_dir("bp") / "Sections" / "other.typ", "= Other\n")
    live, listed, private = structure.tree(here, "cu")
    assert live.shared_ids == ("live-load-table",) and live.shared_with == ("bp",)
    assert listed.shared_with == ("rs",) and listed.shared_ids == ()
    assert private.shared_ids == ("nobody-else",) and private.shared_with == ()
    # BP did not list the share: it is found from the tag its file carries, which CU's file carries too
    loads, other = structure.tree(here, "bp")
    assert loads.shared_with == ("cu",) and other.shared_with == ()


# --- switching sections on and off -----------------------------------------------------------------------------------

def test_the_report_switches_a_section_off_by_commenting_its_include_and_back_byte_for_byte():
    root = conftest.tmpdir("enabled_report")
    for ending in ("\n", "\r\n"):
        here = _report(root / ("crlf" if ending == "\r\n" else "lf"), ending)
        entry = here.document_typ("rs")
        before = entry.read_bytes()
        assert structure.set_enabled(here, "rs", "001-a", False) is True
        text = entry.read_bytes().decode("utf-8")
        assert '// #include "Sections/001-a.typ"' in text and '#include "Sections/004-d.typ"' in text
        assert text.count("\n") == before.decode("utf-8").count("\n")
        assert text.count("\r\n") == (text.count("\n") if ending == "\r\n" else 0), "a line ending changed"
        assert [n.enabled for n in structure.tree(here, "rs")] == [False, False, True, True]
        assert structure.set_enabled(here, "rs", "001-a", False) is False, "already off"
        # the commented one goes on, with the indentation of the line beside it kept
        assert structure.set_enabled(here, "rs", "002-b", True) is True
        assert structure.set_enabled(here, "rs", "003-c", False) is True
        assert '  // #include "Sections/003-c.typ"' in entry.read_bytes().decode("utf-8")
        assert [n.enabled for n in structure.tree(here, "rs")] == [False, True, False, True]
        assert structure.set_enabled(here, "rs", "001-a", True) is True
        assert structure.set_enabled(here, "rs", "002-b", False) is True
        assert structure.set_enabled(here, "rs", "003-c", True) is True
        assert entry.read_bytes() == before, "switching every section back did not give the entry file back byte for byte"
        assert not entry.with_name(entry.name + ".part").exists()


def test_a_heading_is_no_section_and_an_unknown_one_is_refused_in_the_report():
    here = _report(conftest.tmpdir("enabled_report_refused"))
    before = here.document_typ("rs").read_bytes()
    for node_id in ("001-a#2", "nowhere", ""):
        try:
            structure.set_enabled(here, "rs", node_id, False)
        except structure.StructureError as exc:
            assert "001-a" in str(exc), "the message names the sections there are"
        else:
            raise AssertionError(f"{node_id!r} was switched off")
    assert here.document_typ("rs").read_bytes() == before


def test_the_report_gives_a_file_included_twice_one_id_per_line():
    root = conftest.tmpdir("enabled_twice")
    here = _report(root)
    entry = here.document_typ("rs")
    text = entry.read_bytes().decode("utf-8") + '#include "Sections/001-a.typ"\n'
    entry.write_bytes(text.encode("utf-8"))
    ids = [n.id for n in structure.tree(here, "rs")]
    assert ids == ["001-a", "002-b", "003-c", "004-d", "001-a#2"]
    assert structure.set_enabled(here, "rs", "001-a#2", False) is True
    assert [n.enabled for n in structure.tree(here, "rs")] == [True, False, True, True, False]


def _cu(name, ending="\n", language=None):
    """A CU with a group holding two leaves, a leaf of its own and the entry file carrying the generated block, written in `ending`."""
    root = conftest.tmpdir(name)
    here = _modes_project(root)
    if language:
        _write(root / "config.typ", f'#let doc-lang = "{language}"\n')
    source = {"schema_version": "1.0", "format": "woodcore-structure", "document": "cu",
              "sections": [_group("general", _leaf("purpose"), _leaf("scope")), _leaf("journal")]}
    structure.write(here.structure_file("cu"), source)
    _write(here.document_typ("cu"), "// entry\n#show: conf\n\n" + structure.START_TAG + "\n" + structure.END_TAG + "\n\n// trailer\n", ending)
    structure.sync_entry(here.document_typ("cu"), source, language or "de")
    for leaf, _depth in structure.leaves(source):
        _write(here.document_dir("cu") / leaf["file"], f'#import "/commands.typ": *\n\n= Title {leaf["id"]}\n\ntext\n\n== Sub {leaf["id"]}\n', ending)
    return here


def test_a_cu_switches_a_section_off_in_structure_json_and_in_its_entry_and_back_byte_for_byte():
    for ending in ("\n", "\r\n"):
        here = _cu("enabled_cu" + ("_crlf" if ending == "\r\n" else ""), ending)
        entry, path = here.document_typ("cu"), here.structure_file("cu")
        entry_before, structure_before = entry.read_bytes(), path.read_bytes()
        assert structure.set_enabled(here, "cu", "scope", False) is True
        assert '// disabled: scope (Sections/scope.typ)' in entry.read_bytes().decode("utf-8")
        assert structure.read(path)["sections"][0]["children"][1]["enabled"] is False
        assert [(n.id, n.enabled, n.active) for n in structure.flatten(structure.tree(here, "cu")) if n.kind != "heading"] == [
            ("general", True, True), ("purpose", True, True), ("scope", False, False), ("journal", True, True)]
        assert structure.set_enabled(here, "cu", "scope", False) is False
        assert structure.set_enabled(here, "cu", "scope", True) is True
        assert entry.read_bytes() == entry_before and path.read_bytes() == structure_before, "the round trip did not give both files back byte for byte"
        assert b"\r" not in path.read_bytes(), "structure.json is written LF, whatever the entry file has"
        # a disabled group takes its subtree with it: the leaves under it are not printed, whatever their own flag says
        assert structure.set_enabled(here, "cu", "general", False) is True
        shown = {n.id: (n.enabled, n.active) for n in structure.flatten(structure.tree(here, "cu"))}
        assert shown["general"] == (False, False) and shown["purpose"] == (True, False) and shown["scope"] == (True, False)
        assert shown["purpose#2"] == (True, False), "the headings under a leaf that is not printed are not printed"
        assert shown["journal"] == (True, True)
        assert "// disabled: general\n" in entry.read_bytes().decode("utf-8").replace("\r\n", "\n")
        assert structure.set_enabled(here, "cu", "general", True) is True
        assert entry.read_bytes() == entry_before and path.read_bytes() == structure_before


def test_a_cu_refuses_a_section_it_does_not_have_and_an_entry_it_cannot_lay_out_and_writes_nothing():
    here = _cu("enabled_cu_refused")
    entry, path = here.document_typ("cu"), here.structure_file("cu")
    before = entry.read_bytes(), path.read_bytes()
    try:
        structure.set_enabled(here, "cu", "purpose#2", False)
    except structure.StructureError as exc:
        assert "purpose#2" in str(exc)
    else:
        raise AssertionError("a heading was switched off as a section")
    # an entry whose tags Woodcore cannot read is not rewritten, and structure.json stays as it was
    torn = entry.read_bytes().decode("utf-8").replace(structure.END_TAG, "// woodcore:shared torn")
    entry.write_bytes(torn.encode("utf-8"))
    try:
        structure.set_enabled(here, "cu", "scope", False)
    except structure.StructureError:
        pass
    else:
        raise AssertionError("an entry with torn tags was rewritten")
    assert entry.read_bytes() == torn.encode("utf-8") and path.read_bytes() == before[1]


# --- naming ----------------------------------------------------------------------------------------------------------

def test_a_leafs_title_is_its_first_heading_rewritten_in_place_and_nothing_else_moves():
    here = _cu("title_leaf", "\r\n")
    leaf = here.document_dir("cu") / "Sections" / "purpose.typ"
    _write(leaf, '#import "/commands.typ": *\n\n= Old title <intro> // a note\n\ntext = with an equals\n\n== Second\n', "\r\n")
    before = leaf.read_bytes().decode("utf-8")
    structure_before = here.structure_file("cu").read_bytes()
    entry_before = here.document_typ("cu").read_bytes()
    assert structure.set_title(here, "cu", "purpose", "de", "New *title* with \"quotes\"") is True
    after = leaf.read_bytes().decode("utf-8")
    assert after == before.replace("= Old title <intro> // a note", '= New *title* with "quotes" <intro> // a note'), "only the heading's own text changed -- its label, its comment and the CRLF stayed"
    assert here.structure_file("cu").read_bytes() == structure_before and here.document_typ("cu").read_bytes() == entry_before
    assert structure.set_title(here, "cu", "purpose", "de", 'New *title* with "quotes"') is False
    assert structure.tree(here, "cu")[0].children[0].title == 'New *title* with "quotes"'
    # a heading of the file that is not its first, by its id
    assert structure.set_title(here, "cu", "purpose#2", None, "Renamed second") is True
    assert leaf.read_bytes().decode("utf-8").endswith("== Renamed second\r\n")


def test_a_reports_file_and_heading_are_named_in_the_report_too():
    here = _report(conftest.tmpdir("title_report"))
    assert structure.set_title(here, "rs", "001-a", "de", "Alpha renamed") is True
    assert structure.set_title(here, "rs", "001-a#4", "de", "Alpha two renamed") is True
    tree = structure.tree(here, "rs")
    assert tree[0].title == "Alpha renamed" and [c.title for c in tree[0].children] == ["Alpha one", "Alpha two renamed"]
    assert here.document_typ("rs").read_bytes().decode("utf-8").count("Alpha") == 0, "the entry file was not touched"


def test_a_heading_call_is_rewritten_inside_its_string_or_its_brackets():
    root = conftest.tmpdir("title_call")
    here = _modes_project(root)
    structure.write(here.structure_file("cu"), {"schema_version": "1.0", "format": "woodcore-structure", "document": "cu", "sections": [_leaf("called")]})
    leaf = _write(here.document_dir("cu") / "Sections" / "called.typ", '#heading(level: 1, "Old")\n\n#heading(level: 2)[Old block]\n\n#heading(level: 2, var)\n')
    assert structure.set_title(here, "cu", "called", "de", 'Say "hi"') is True
    assert leaf.read_text(encoding="utf-8").startswith('#heading(level: 1, "Say \\"hi\\"")\n')
    assert structure.tree(here, "cu")[0].title == 'Say "hi"'
    assert structure.set_title(here, "cu", "called#2", None, "New block") is True
    assert "#heading(level: 2)[New block]" in leaf.read_text(encoding="utf-8")
    for bad in ("Unbalanced ]", "Unbalanced ["):
        try:
            structure.set_title(here, "cu", "called#2", None, bad)
        except structure.StructureError as exc:
            assert "bracket" in str(exc)
        else:
            raise AssertionError(f"{bad!r} was written into a content block")
    try:
        structure.set_title(here, "cu", "called#3", None, "Text")
    except structure.StructureError as exc:
        assert "plain text" in str(exc)
    else:
        raise AssertionError("a title that is a variable was rewritten")


def test_a_groups_title_is_written_in_its_language_in_structure_json_and_the_entry_block_follows_the_documents():
    here = _cu("title_group", language="fr")
    entry, path = here.document_typ("cu"), here.structure_file("cu")
    assert '#heading(level: 1, "FR general")' in entry.read_bytes().decode("utf-8")
    assert structure.set_title(here, "cu", "general", "de", "Allgemeines neu") is True
    source = structure.read(path)
    assert source["sections"][0]["title"]["de"] == "Allgemeines neu" and source["sections"][0]["title"]["fr"] == "FR general"
    assert '#heading(level: 1, "FR general")' in entry.read_bytes().decode("utf-8"), "the document is written in French: a German title does not reach its block"
    assert structure.set_title(here, "cu", "general", "fr", "Généralités") is True
    assert '#heading(level: 1, "Généralités")' in entry.read_bytes().decode("utf-8")
    assert structure.tree(here, "cu")[0].title == "Généralités"
    assert structure.set_title(here, "cu", "general", "fr", "Généralités") is False
    try:
        structure.set_title(here, "cu", "general", "it", "Generale")
    except structure.StructureError as exc:
        assert "it" in str(exc)
    else:
        raise AssertionError("a group was given a title in a language the format does not have")


def test_a_title_that_cannot_be_written_is_refused_and_a_file_without_a_heading_has_none_to_rewrite():
    here = _cu("title_refused")
    leaf = here.document_dir("cu") / "Sections" / "scope.typ"
    before = leaf.read_bytes()
    for bad in ("", "   ", "two\nlines", None):
        try:
            structure.set_title(here, "cu", "scope", "de", bad)
        except structure.StructureError:
            pass
        else:
            raise AssertionError(f"{bad!r} was accepted as a title")
    assert leaf.read_bytes() == before, "a refused title changed the file"
    try:
        structure.set_title(here, "cu", "nowhere", "de", "Title")
    except structure.StructureError as exc:
        assert "nowhere" in str(exc)
    else:
        raise AssertionError("a title was set on a section that is not there")
    _write(leaf, "No heading here.\n")
    try:
        structure.set_title(here, "cu", "scope", "de", "Title")
    except structure.StructureError as exc:
        assert "no heading" in str(exc)
    else:
        raise AssertionError("a file with no heading was given a title")
    assert leaf.read_text(encoding="utf-8") == "No heading here.\n"


# --- the tree and the compiled PDF -----------------------------------------------------------------------------------

def test_titles_compare_without_numbering_markup_typography_or_case():
    norm = structure.normalize_title
    assert norm("1.2 Einleitung") == norm("Einleitung") == "einleitung"
    assert norm("  3)   A  B  ") == "a b" and norm("A. Title") == "title" and norm("IV. Title") == "title"
    assert norm("2 Zimmer") == norm("1.1 2 Zimmer") == "zimmer", "a title that starts with a number loses it on both sides"
    assert norm("*Bold* and `raw` and _emph_") == "bold and raw and emph"
    assert norm("Holz_Holz") == "holz_holz", "an underscore inside a word is a character"
    assert norm("Ein \\# Zeichen") == "ein # zeichen"
    assert norm("a -- b") == norm("a \u2013 b") == "a - b" and norm("x --- y") == norm("x \u2014 y")
    assert norm("\u201eQuoted\u201c it\u2019s") == norm('"Quoted" it\'s')
    assert norm("non\u00a0breaking~space") == "non breaking space"
    assert norm("Wait...") == norm("Wait\u2026")
    assert norm("") == "" and norm("12 ") == "12"


def _node(kind, node_id, level, title, active=True):
    return structure.Node(kind, node_id, title, level, active=active, enabled=active)


def test_align_matches_nodes_to_bookmarks_in_order_and_skips_what_the_engine_prints():
    nodes = [
        _node("group", "general", 1, "Allgemeines"),
        _node("file", "purpose", 2, "Zweck"),
        _node("heading", "purpose#2", 3, "Detail *one*"),
        _node("file", "gone", 1, "Hidden", active=False),
        _node("file", "journal", 1, "Änderungsverzeichnis"),
        _node("file", "absent", 1, "Not in the PDF"),
    ]
    nodes[1].children.append(nodes[2])
    nodes[0].children.append(nodes[1])
    tree = [nodes[0], nodes[3], nodes[4], nodes[5]]
    marks = [
        (1, "Inhaltsverzeichnis", 0, 780.0),          # printed by the engine
        (1, "1 Allgemeines", 1, 700.0),
        (2, "1.1 Zweck", 1, 650.0),
        (2, "Heading printed by a calculation", 1, 600.0),
        (3, "1.1.1 Detail one", 2, 500.0),
        (1, "2 Änderungsverzeichnis", 3, 700.0),
        (1, "Hidden", 4, 700.0),                       # a title the disabled node has, which it must not take
    ]
    found = structure.align(tree, marks)
    assert {k: (v.page, v.y) for k, v in found.items()} == {"general": (1, 700.0), "purpose": (1, 650.0), "purpose#2": (2, 500.0), "journal": (3, 700.0)}
    assert all(isinstance(v, structure.Bookmark) for v in found.values())
    assert "gone" not in found and "absent" not in found
    # the same answer for the flat list of the same nodes
    assert structure.align(structure.flatten(tree), marks) == found


def test_align_falls_back_on_the_title_at_another_level_where_typst_nests_a_heading_under_a_level_it_skipped():
    # `=` then `===`: the PDF's outline nests the second one at depth 2, the file says level 3
    tree = [_node("file", "a", 1, "Alpha")]
    tree[0].children.append(_node("heading", "a#2", 3, "Deep"))
    found = structure.align(tree, [(1, "1 Alpha", 0, 700.0), (2, "1.1 Deep", 0, 600.0)])
    assert set(found) == {"a", "a#2"} and found["a#2"].level == 2
    # the exact level wins where there is one, even after a bookmark of the same title at another
    tree = [_node("file", "x", 2, "Same")]
    found = structure.align(tree, [(1, "Same", 0, 10.0), (2, "Same", 1, 20.0)])
    assert found["x"].page == 1
    # matching is forward only: a bookmark before the last one matched is never taken again
    tree = [_node("file", "p", 1, "Two"), _node("file", "q", 1, "One")]
    found = structure.align(tree, [(1, "One", 0, 1.0), (1, "Two", 1, 1.0)])
    assert set(found) == {"p"} and found["p"].page == 1


def test_align_takes_the_panes_bookmarks_and_any_object_with_their_four_fields_as_well_as_its_own():
    from collections import namedtuple
    tree = [_node("file", "a", 1, "Alpha"), _node("file", "b", 1, "Beta")]
    facts = [(1, "1 Alpha", 0, 75.0), (1, "2 Beta", 1, 75.0)]
    Pane = namedtuple("Bookmark", "level title page y")          # calc/tools/pdf_pane.py's, a class of its own with the same four fields
    Plain = type("Plain", (), {})

    def plain(level, title, page, y):
        item = Plain()
        item.level, item.title, item.page, item.y = level, title, page, y
        return item

    expected = structure.align(tree, facts)
    assert structure.align(tree, [Pane(*f) for f in facts]) == expected
    assert structure.align(tree, [plain(*f) for f in facts]) == expected
    assert structure.align(tree, [structure.Bookmark(*f) for f in facts]) == expected
    assert structure.align(tree, [list(f) for f in facts]) == expected
    assert expected["b"] == structure.Bookmark(1, "2 Beta", 1, 75.0), "what comes back is a Bookmark, with its y as it was given"
    # a bookmark with no y at all
    class Bare:
        level, title, page = 1, "Alpha", 3
    assert structure.align(tree, [Bare()])["a"] == structure.Bookmark(1, "Alpha", 3, None)


def test_bookmarks_come_out_of_a_pdf_with_their_level_title_page_and_place():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    root = conftest.tmpdir("bookmarks_pdf")
    (root / "doc.typ").write_text('#set heading(numbering: "1.1")\n= First\n#lorem(400)\n== Second\n#pagebreak()\n= Third\n', encoding="utf-8")
    done = subprocess.run(["typst", "compile", "--root", str(root), str(root / "doc.typ"), str(root / "doc.pdf")], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    marks = structure.bookmarks_from_pdf(root / "doc.pdf")
    assert [(m.level, m.title) for m in marks] == [(1, "1 First"), (2, "1.1 Second"), (1, "2 Third")]
    assert [m.page for m in marks][0] == 0 and marks[-1].page == max(m.page for m in marks) >= 1
    assert all(isinstance(m.y, float) and 0 < m.y < 842 for m in marks)
    assert 50 < marks[0].y < 130, "the first heading is near the top of the page, y counted from the top edge as the pane's bookmarks are"
    assert marks[1].page != marks[0].page or marks[1].y > marks[0].y, "a heading further down the page has the larger y"
    from_bottom = structure.bookmarks_from_pdf((root / "doc.pdf").read_bytes(), from_bottom=True)
    assert all(abs((bottom.y + top.y) - 841.8898) < 0.01 for bottom, top in zip(from_bottom, marks)), "from_bottom measures from the other edge, as the PDF states it"
    assert [(m.level, m.title, m.page) for m in from_bottom] == [(m.level, m.title, m.page) for m in marks]
    # a PDF with no outline has no bookmarks, an open file works like a path and is let go
    (root / "plain.typ").write_text("Nothing to outline.\n", encoding="utf-8")
    subprocess.run(["typst", "compile", "--root", str(root), str(root / "plain.typ"), str(root / "plain.pdf")], check=True)
    assert structure.bookmarks_from_pdf(root / "plain.pdf") == []
    with open(root / "doc.pdf", "rb") as handle:
        assert structure.bookmarks_from_pdf(handle) == marks
    (root / "doc.pdf").unlink()    # nothing holds it


def test_align_on_a_real_compile_matches_every_printed_node_and_skips_the_engines_headings():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    root = conftest.tmpdir("align_real")
    here = _modes_project(root)
    _write(here.document_typ("rs"), "\n".join([
        '#set heading(numbering: "1.1")',
        '#outline()',
        '#include "Sections/001-a.typ"',
        '// #include "Sections/002-b.typ"',
        '#include "Sections/003-c.typ"', "",
    ]))
    sections = here.document_dir("rs") / "Sections"
    _write(sections / "001-a.typ", "#let engine-heading() = heading(level: 2)[Printed by a function]\n\n= Alpha\n\n== Alpha one\n\n#engine-heading()\n\n=== Alpha one one\n\n#pagebreak()\n\n== Alpha two\n")
    _write(sections / "002-b.typ", "= Beta\n\n== Beta one\n")
    _write(sections / "003-c.typ", "= Gamma\n\n=== Gamma skips a level\n\n= Delta\n")
    out = root / "rs.pdf"
    import documents
    done = subprocess.run(["typst", *documents.compile_args(here, "rs", [], target=out)], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    tree = structure.tree(here, "rs")
    printed = [n for n in structure.flatten(tree) if n.active]
    assert [(n.level, n.title) for n in printed] == [
        (1, "Alpha"), (2, "Alpha one"), (3, "Alpha one one"), (2, "Alpha two"), (1, "Gamma"), (3, "Gamma skips a level"), (1, "Delta")]
    # Typst's own count of the headings agrees with the scan, engine's heading and all
    assert [t for _l, t in _headings(root, here.document_typ("rs"))] == [
        "Alpha", "Alpha one", "Printed by a function", "Alpha one one", "Alpha two", "Gamma", "Gamma skips a level", "Delta"]
    marks = structure.bookmarks_from_pdf(out)
    assert len(marks) == 8
    found = structure.align(tree, marks)
    assert set(found) == {n.id for n in printed}, "every printed node has its bookmark"
    assert not any(n.id in found for n in structure.flatten(tree) if not n.active), "a disabled section is not in the PDF, so it has none"
    titles = {node_id: found[node_id].title for node_id in found}
    assert titles["001-a"] == "1 Alpha" and titles["001-a#2"] == "1.1 Alpha one" and titles["003-c#2"].endswith("Gamma skips a level")
    assert "Printed by a function" not in " ".join(titles.values()), "the engine's heading belongs to no node"
    pages = [found[n.id].page for n in printed]
    assert pages == sorted(pages), "the nodes come in the order of the pages"
    assert found["001-a#3"].page < found["001-a#4"].page, "the page break between two headings moves the second to another page"
    # a document order is also a vertical order within a page: a later heading is lower, so its y (from the top) is larger
    order = [(found[n.id].page, found[n.id].y) for n in printed]
    assert order == sorted(order), "the nodes are not in reading order"


def test_align_on_the_compiled_example_documents_matches_every_node():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    import documents
    here = conftest.PROJECT
    folder = conftest.tmpdir("align_example")
    for mode in ("cu", "bp", "rs"):
        out = folder / f"{mode}.pdf"
        done = subprocess.run(["typst", *documents.compile_args(here, mode, [], target=out)], capture_output=True, text=True, encoding="utf-8")
        assert done.returncode == 0, f"{mode}: {done.stderr}"
        tree = structure.tree(here, mode)
        found = structure.align(tree, structure.bookmarks_from_pdf(out))
        printed = [n.id for n in structure.flatten(tree) if n.active and (n.kind != "object" or n.object_type == "heading")]
        assert sorted(found) == sorted(printed), f"{mode}: unmatched {sorted(set(printed) - set(found))}"
        assert not [n.id for n in structure.flatten(tree) if n.object_type not in (None, "heading") and n.id in found], "an object that is no heading has no bookmark"
        pages = [found[i].page for i in printed]
        assert pages == sorted(pages), f"{mode}: the nodes are not in the order of the pages"


# --- objects in the tree -----------------------------------------------------------------------------------------

TAGGED = """#import "/commands.typ": *

// woodcore:shared intro
// woodcore:object heading title
= Einleitung
// woodcore:/object title

// woodcore:object text p1
Der *erste* Absatz, der lang genug ist, um im Baum gekürzt zu werden, weil niemand ihn dort ganz lesen will.
// woodcore:/object p1

// woodcore:object heading h2
== Unterabschnitt <unter>
// woodcore:/object h2

// woodcore:object doc-table liste
#doc-table(
  columns: (
    (id: "a", title: [A]),
  ),
  rows: (
    (a: [x]),
  ),
  caption: [Eine *Liste*],
)
// woodcore:/object liste

// woodcore:object text p2
Der zweite Absatz.
// woodcore:/object p2
// woodcore:/shared intro

// woodcore:object text outside
Ausserhalb des Blocks.
// woodcore:/object outside
"""


def _tagged_project(name, text=TAGGED, ending="\n"):
    """A convention of one tagged section file, `alpha`, and the journal."""
    here = _modes_project(conftest.tmpdir(name))
    source = {"schema_version": "1.0", "format": "woodcore-structure", "document": "cu", "sections": [_leaf("alpha", shared_with=["bp"])]}
    structure.write(here.structure_file("cu"), source)
    _write(here.document_typ("cu"), "// entry\n" + structure.block_text(source, "de"))
    _write(here.document_dir("cu") / "Sections" / "alpha.typ", text, ending)
    return here


def test_a_file_with_object_tags_has_its_objects_for_children():
    here = _tagged_project("tree_objects")
    (alpha,) = structure.tree(here, "cu")
    assert (alpha.kind, alpha.id, alpha.title, alpha.level, alpha.line, alpha.shared_ids) == ("file", "alpha", "Einleitung", 1, 4, ("intro",))
    kids = alpha.children
    assert [(c.id, c.kind, c.object_type, c.object_id) for c in kids] == [
        ("alpha/title", "object", "heading", "title"), ("alpha/p1", "object", "text", "p1"), ("alpha/h2", "object", "heading", "h2"),
        ("alpha/liste", "object", "doc-table", "liste"), ("alpha/p2", "object", "text", "p2"), ("alpha/outside", "object", "text", "outside")], "flat, in the order of the file"
    assert all(c.children == [] and c.parent == "alpha" and c.file == "Sections/alpha.typ" and not c.separate_file and c.state == "canonical" and c.problems == () for c in kids)
    # a short label: a heading's title (its label left out), the first words of a paragraph, a table's caption
    assert [c.title for c in kids][2:] == ["Unterabschnitt", "Eine Liste", "Der zweite Absatz.", "Ausserhalb des Blocks."] and kids[0].title == "Einleitung"
    assert kids[1].title.startswith("Der erste Absatz, der lang genug ist") and kids[1].title.endswith(chr(0x2026)) and len(kids[1].title) <= 61, kids[1].title
    # the line of the first line of the body -- a heading's own line -- and the lines of the two tags
    lines = TAGGED.split("\n")
    assert all(lines[c.line - 1].startswith("// woodcore:object") and lines[c.span[0]] == lines[c.line - 1] and lines[c.span[1]].startswith("// woodcore:/object") for c in kids)
    assert kids[0].line == alpha.line and lines[kids[2].line] == "== Unterabschnitt <unter>"
    # the level a heading is printed at; any other object sits one under the heading it follows
    assert [c.level for c in kids] == [1, 2, 2, 3, 3, 3]
    # the shared block an object stands in
    assert [c.shared for c in kids] == ["intro", "intro", "intro", "intro", "intro", None]
    assert alpha.shared_with == ("bp",)
    flat = structure.flatten([alpha])
    assert [n.id for n in flat] == ["alpha"] + [c.id for c in kids] and structure.find_node([alpha], "alpha/h2").title == "Unterabschnitt"
    as_dict = kids[1].as_dict()
    assert (as_dict["kind"], as_dict["object_type"], as_dict["object_id"], as_dict["state"], as_dict["shared"], as_dict["span"]) == ("object", "text", "p1", "canonical", "intro", kids[1].span)


def test_the_level_of_an_object_follows_where_the_file_is_included():
    here = _tagged_project("tree_object_levels")
    source = {"schema_version": "1.0", "format": "woodcore-structure", "document": "cu",
              "sections": [_group("general", _group("inner", _leaf("alpha")))]}
    structure.write(here.structure_file("cu"), source)
    alpha = structure.find_node(structure.tree(here, "cu"), "alpha")
    assert alpha.level == 3, "a leaf at the third level has its first heading at level 3"
    assert [c.level for c in alpha.children] == [3, 4, 4, 5, 5, 5]


def test_a_file_that_carries_no_tag_keeps_its_headings_and_a_file_half_tagged_has_both():
    here = _tagged_project("tree_half", text='#import "/commands.typ": *\n\n= Alpha\n\n== Alpha one\n\nText.\n')
    (alpha,) = structure.tree(here, "cu")
    assert [(c.kind, c.level, c.title) for c in alpha.children] == [("heading", 2, "Alpha one")] and alpha.children[0].object_type is None
    text = ('#import "/commands.typ": *\n\n// woodcore:object heading title\n= Alpha\n// woodcore:/object title\n\n== Untagged one\n\n'
            '// woodcore:object text p1\nTagged.\n// woodcore:/object p1\n\n=== Untagged two\n')
    here = _tagged_project("tree_half_two", text=text)
    (alpha,) = structure.tree(here, "cu")
    assert [(c.kind, c.id, c.level, c.title) for c in alpha.children] == [
        ("object", "alpha/title", 1, "Alpha"), ("heading", "alpha#2", 2, "Untagged one"), ("object", "alpha/p1", 3, "Tagged."), ("heading", "alpha#3", 3, "Untagged two")]
    assert alpha.children[1].parent == "alpha" and alpha.children[1].object_type is None


def test_the_objects_of_a_disabled_file_are_listed_and_not_printed_and_an_object_is_no_section():
    here = _tagged_project("tree_disabled")
    structure.set_enabled(here, "cu", "alpha", False)
    (alpha,) = structure.tree(here, "cu")
    assert not alpha.active and alpha.children and all(not c.enabled and not c.active for c in alpha.children)
    for call in (lambda: structure.set_enabled(here, "cu", "alpha/p1", True), lambda: structure.remove_section(here, "cu", "alpha/p1"),
                 lambda: structure.move_node(here, "cu", "alpha/p1", None, 0), lambda: structure.rename_section(here, "cu", "alpha/p1", "beta")):
        try:
            call()
        except structure.StructureError as exc:
            assert "alpha/p1" in str(exc) and (exc.code in ("not_a_section", "")), exc
        else:
            raise AssertionError("an object was taken for a section")


def test_set_title_rewrites_a_heading_object_and_refuses_a_paragraph():
    here = _tagged_project("tree_set_title", ending="\r\n")
    path = here.document_dir("cu") / "Sections" / "alpha.typ"
    before = path.read_bytes()
    assert structure.set_title(here, "cu", "alpha/h2", "de", "Neuer *Unterabschnitt*") is True
    after = path.read_bytes()
    assert after == before.replace(b"== Unterabschnitt <unter>", b"== Neuer *Unterabschnitt* <unter>"), "the marker, the label, the tags and every other byte are kept"
    assert structure.find_node(structure.tree(here, "cu"), "alpha/h2").title == "Neuer Unterabschnitt"
    assert structure.set_title(here, "cu", "alpha/h2", "de", "Neuer *Unterabschnitt*") is False
    # the file's own title is the first heading, which is an object as well
    assert structure.set_title(here, "cu", "alpha", "de", "Neue Einleitung") is True
    tree = structure.tree(here, "cu")
    assert tree[0].title == "Neue Einleitung" and tree[0].children[0].title == "Neue Einleitung"
    assert structure.set_title(here, "cu", "alpha/title", "de", "Noch eine") is True and structure.tree(here, "cu")[0].title == "Noch eine"
    for node_id in ("alpha/p1", "alpha/liste"):
        try:
            structure.set_title(here, "cu", node_id, "de", "x")
        except structure.StructureError as exc:
            assert "no title" in str(exc), exc
        else:
            raise AssertionError(f"{node_id} was given a title")


def test_align_maps_a_heading_object_like_a_heading_and_any_other_object_to_nothing():
    here = _tagged_project("tree_align")
    nodes = structure.tree(here, "cu")
    marks = [structure.Bookmark(1, "Einleitung", 0, 700.0), structure.Bookmark(2, "Unterabschnitt", 1, 40.0)]
    found = structure.align(nodes, marks)
    assert sorted(found) == ["alpha", "alpha/h2", "alpha/title"]
    assert found["alpha/title"] == found["alpha"] == marks[0], "the first heading of a file is the file's own: one bookmark for the two"
    assert found["alpha/h2"] == marks[1]
    # the engine's own headings that no node takes are passed over, an object that is no heading is never looked for
    engine = [structure.Bookmark(1, "Inhaltsverzeichnis", 0, 100.0)] + marks
    assert structure.align(nodes, engine) == found
    # a disabled file is not in the PDF
    structure.set_enabled(here, "cu", "alpha", False)
    assert structure.align(structure.tree(here, "cu"), marks) == {}


def test_a_report_file_tagged_by_tag_file_has_its_objects_and_its_headings_still_match_what_typst_prints():
    """The example's report, every section file tagged: a file's children are its objects, a heading that stands inside an `#if` outside every object is a heading node among them, and the PDF's outline is matched by the heading objects and those nodes alike."""
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    import documents
    import typst_objects
    here = _example("tree_report_tagged")
    for path in sorted((here.document_dir("rs") / "Sections").glob("*.typ")):
        path.write_bytes(typst_objects.tag_file(path.read_bytes().decode("utf-8")).encode("utf-8"))
    nodes = structure.tree(here, "rs")
    for file_node in nodes:
        assert file_node.children and file_node.children[0].object_type == "heading" and file_node.children[0].line == file_node.line, file_node.id
        assert all(c.kind in ("object", "heading") and c.children == [] for c in file_node.children), file_node.id
    baustoffe = nodes[2]
    assert [(c.kind, c.level, c.title) for c in baustoffe.children if c.kind == "heading"] == [("heading", 2, "Verbindungsmittel")], "a heading inside an #if stays a heading node"
    out = conftest.tmpdir("tree_report_tagged_pdf") / "rs.pdf"
    done = subprocess.run(["typst", *documents.compile_args(here, "rs", [], target=out)], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr[:2000]
    found = structure.align(nodes, structure.bookmarks_from_pdf(out))
    printed = [n.id for n in structure.flatten(nodes) if n.active and (n.kind != "object" or n.object_type == "heading")]
    assert sorted(found) == sorted(printed), sorted(set(printed) - set(found))
    wrong = [(n.id, n.level, found[n.id].level) for n in structure.flatten(nodes) if n.id in found and found[n.id].level != n.level]
    assert not wrong, wrong


# --- tagging a section's file ---------------------------------------------------------------------------------------

def test_tag_section_tags_the_file_of_a_node_and_a_second_run_writes_nothing():
    """«Baliser ce fichier» on the example report's files: the number of objects the file gains, from the id of the file, of a heading of it or of an object of it; a file tagged already is not written."""
    here = _example("tag_section")
    sections = here.document_dir("rs") / "Sections"
    before = (sections / "001-einleitung.typ").read_bytes()
    assert structure.tag_section(here, "rs", "001-einleitung") == 2
    after = (sections / "001-einleitung.typ").read_bytes()
    assert after != before and structure.tag_section(here, "rs", "001-einleitung") == 0 and (sections / "001-einleitung.typ").read_bytes() == after
    stripped = b"".join(line for line in after.splitlines(keepends=True) if not line.startswith((b"// woodcore:object", b"// woodcore:/object")))
    assert stripped == before, "the tags are comments: every other byte is the file's own"
    nodes = structure.tree(here, "rs")
    assert [(c.kind, c.object_type, c.title) for c in nodes[0].children][0] == ("object", "heading", "Einleitung") and len(nodes[0].children) == 2
    # by the id of a heading inside the file, and by the id of an object -- the whole file is tagged either way
    assert structure.tag_section(here, "rs", "002-grundlagen#3") == 13
    assert structure.tag_section(here, "rs", "002-grundlagen/grundlagen") == 0
    assert structure.tag_section(here, "rs", "003-baustoffe", ids="plain") == 2
    assert [c.id for c in structure.tree(here, "rs")[2].children if c.kind == "object"] == ["003-baustoffe/title", "003-baustoffe/p1"]
    # a section of a convention is tagged the same way
    assert structure.tag_section(here, "cu", "purpose") == 2 and structure.tag_section(here, "cu", "purpose") == 0


def test_tag_section_keeps_crlf_and_a_bom_and_refuses_what_it_must():
    here = _example("tag_section_refusals")
    path = here.document_dir("rs") / "Sections" / "001-einleitung.typ"
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    path.write_bytes(raw)
    assert structure.tag_section(here, "rs", "001-einleitung") == 2
    data = path.read_bytes()
    assert data.count(b"\r\n") == data.count(b"\n") and b"\r\r" not in data, "a line was written with another ending than the file's"
    path.write_bytes(b"\xef\xbb\xbf" + raw)
    assert structure.tag_section(here, "rs", "001-einleitung") == 2 and path.read_bytes().startswith(b"\xef\xbb\xbf#import"), "the byte order mark stays first"
    # a file whose tags cannot be read is left as it is, and the refusal names the file
    torn = here.document_dir("cu") / "Sections" / "purpose.typ"
    torn.write_bytes(b'#import "/commands.typ": *\n\n= Zweck\n\n// woodcore:object text p1\nOffen.\n')
    before = torn.read_bytes()
    error = _code("tags_unreadable", structure.tag_section, here, "cu", "purpose")
    assert "Sections/purpose.typ" in str(error) and error.values["file"] == "Sections/purpose.typ" and torn.read_bytes() == before
    _code("not_a_section", structure.tag_section, here, "cu", "general")
    _code("no_such_node", structure.tag_section, here, "cu", "nowhere")
    _code("no_such_node", structure.tag_section, here, "cu", None)
    _code("bad_mode", structure.tag_section, here, "xx", "purpose")


# --- the catalogue: adding, removing, moving and renaming sections (work package 3.3) -----------------------------------

SMALL = {"cu": "Diese Nutzungsvereinbarung legt für das Bauwerk die Anforderungen der Bauherrschaft und die Nutzungsbedingungen fest, auf denen der Entwurf des Tragwerks beruht (SIA 260).",
         "bp": "Diese Projektbasis legt die Annahmen, Grundlagen und Methoden fest, auf denen der Entwurf des Tragwerks beruht (SIA 260)."}


def _small(here):
    """The convention and the base de projet of `here` made the two-file skeleton the operations on the catalogue are tested on -- a chapter `general` holding `purpose`, then the `journal` -- in place of the example project's full templates: every file of `Sections/` replaced, structure.json written and the entry's block with it."""
    for mode in ("cu", "bp"):
        folder = here.document_dir(mode) / "Sections"
        for old in folder.glob("*.typ"):
            old.unlink()
        _write(folder / "purpose.typ", f'#import "/commands.typ": *\n\n= Zweck\n\n{SMALL[mode]}\n')
        _write(folder / "journal.typ", '#import "/commands.typ": *\n\n= Änderungsverzeichnis\n\n#show-journal()\n')
        source = structure.blank(mode)
        source["sections"] = [_group("general", _leaf("purpose")), _leaf("journal")]
        source["sections"][0]["title"] = {"fr": "Généralités", "de": "Allgemeines", "en": "General"}
        structure.write(here.structure_file(mode), source)
        structure.sync_entry(here.document_typ(mode), here.structure_file(mode), "de")
    return here


def _example(name):
    """A copy of the example project -- three documents, the engine synced -- in this process's own folder, as a Project: what an operation works on and a compile reads, its convention and its base de projet the small skeleton (`_small`). The committed example is never written."""
    import project
    target = conftest.tmpdir(name) / "p"
    shutil.copytree(conftest.PROJECT.file.parent, target, ignore=shutil.ignore_patterns(".probe", "_Archiv", "stamps"))
    return _small(project.Project.load(target / conftest.PROJECT.file.name))


def _files(here, mode):
    """{path relative to the document's folder: bytes} of every file in it -- sections and archives included, and what a failed write would leave beside them."""
    folder = here.document_dir(mode)
    return {path.relative_to(folder).as_posix(): path.read_bytes() for path in sorted(folder.rglob("*")) if path.is_file()}


def _no_leftovers(here, mode):
    left = [name for name in _files(here, mode) if name.endswith((".tmp", ".part"))]
    assert not left, f"a write left {left} beside the file"


def _compiles(here, mode):
    """The document compiles: Typst is the judge that what an operation wrote is a document."""
    import documents
    out = conftest.tmpdir("structure_ops_pdf") / f"{mode}.pdf"
    done = subprocess.run(["typst", *documents.compile_args(here, mode, [], target=out)], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, f"{mode} does not compile: {done.stderr}"


def _titles(here, mode):
    return _headings(here.typst_root, here.document_typ(mode))


def _code(code, what, *args, **kwargs):
    """`what(*args, **kwargs)` refuses with `code`: the StructureError, its code and its values."""
    try:
        what(*args, **kwargs)
    except structure.StructureError as exc:
        assert exc.code == code, f"refused with {exc.code!r}, not {code!r}: {exc}"
        assert str(exc), "a refusal says something"
        return exc
    raise AssertionError(f"{what.__name__}{args} was not refused with {code!r}")


def _unchanged(here, mode, before):
    assert _files(here, mode) == before, "a refused operation wrote"


GROUPS = {"fr": "Charges", "de": "Lasten", "en": "Loads"}
SKELETON = b'#import "/commands.typ": *\n\n= Nutzlasten\n\n'


def test_the_codes_are_the_ones_a_refusal_states_and_an_old_error_states_none():
    assert len(structure.CODES) == len(set(structure.CODES)) and all(isinstance(code, str) and code for code in structure.CODES)
    exc = structure.StructureError("plain")
    assert (exc.code, exc.values, str(exc)) == ("", {}, "plain"), "an error raised the old way carries no code"
    assert isinstance(structure.StructureError("x", "bad_id", id="a"), validation.ValidationError)
    # the older refusals a window may meet now state theirs where it is a choice of the window's to say them
    for call, code in ((lambda: structure.block_lines(_sample(), "it"), "bad_language"),
                       (lambda: structure.set_title(_cu("codes_old"), "cu", "scope", "de", ""), "bad_title")):
        _code(code, call)


def test_add_section_writes_the_file_the_structure_and_the_entry_and_remove_section_gives_them_back():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    here = _example("ops_add_remove")
    before = _files(here, "cu")
    edit = structure.add_section(here, "cu", "general", 1, "live-loads", "Nutzlasten")
    leaf = here.document_dir("cu") / "Sections" / "live-loads.typ"
    assert (edit.op, edit.mode, edit.id, edit.structure, edit.entry, edit.created, edit.archived, edit.renamed, edit.changed) == (
        "add_section", "cu", "live-loads", True, True, (leaf,), (), (), True)
    assert leaf.read_bytes() == SKELETON, "the import every section starts with, a blank line, the heading, a blank line"
    source = structure.read(here.structure_file("cu"))
    assert [c["id"] for c in source["sections"][0]["children"]] == ["purpose", "live-loads"]
    assert source["sections"][0]["children"][1] == {"id": "live-loads", "file": "Sections/live-loads.typ", "enabled": True}
    entry = here.document_typ("cu")
    assert '#{ set heading(offset: 1); include "Sections/live-loads.typ" }' in entry.read_text(encoding="utf-8")
    assert structure.sync_entry(entry, here.structure_file("cu"), "de") is False, "the entry's block is what the structure says"
    assert json.loads(json.dumps(edit.as_dict()))["created"] == [str(leaf)]
    node = structure.find_node(structure.tree(here, "cu"), "live-loads")
    assert (node.title, node.level, node.parent, node.problems) == ("Nutzlasten", 2, "general", ())
    _no_leftovers(here, "cu")
    _compiles(here, "cu")
    assert _titles(here, "cu") == [(1, "Allgemeines"), (2, "Zweck"), (2, "Nutzlasten"), (1, "Änderungsverzeichnis")]
    # and it is taken out again: everything byte for byte as it was, the file in archives
    out = structure.remove_section(here, "cu", "live-loads")
    [archived] = out.archived
    assert re.fullmatch(r"\d{6}-\d{6}-live-loads\.typ", archived.name) and archived.parent == here.document_dir("cu") / "Sections" / "archives"
    assert archived.read_bytes() == SKELETON and not leaf.exists(), "moved, not copied and not deleted"
    assert (out.op, out.structure, out.entry, out.created) == ("remove_section", True, True, ())
    after = _files(here, "cu")
    assert set(after) - set(before) == {f"Sections/archives/{archived.name}"}
    assert all(after[name] == data for name, data in before.items()), "structure.json, the entry and the sections are what they were"
    _no_leftovers(here, "cu")
    _compiles(here, "cu")


def test_the_same_holds_in_a_base_de_projet():
    here = _example("ops_bp")
    before = _files(here, "bp")
    structure.add_section(here, "bp", None, 0, "scope", "Umfang")
    assert [c["id"] for c in structure.read(here.structure_file("bp"))["sections"]] == ["scope", "general", "journal"]
    assert (here.document_dir("bp") / "Sections" / "scope.typ").read_bytes() == b'#import "/commands.typ": *\n\n= Umfang\n\n'
    assert structure.find_node(structure.tree(here, "bp"), "scope").level == 1
    structure.remove_section(here, "bp", "scope")
    after = _files(here, "bp")
    assert all(after[name] == data for name, data in before.items()) and len(after) == len(before) + 1


def test_a_section_is_written_in_the_line_ending_of_the_entry_and_structure_json_stays_lf():
    here = _example("ops_crlf")
    entry = here.document_typ("cu")
    entry.write_bytes(entry.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    crlf_entry = entry.read_bytes()
    structure.add_section(here, "cu", None, None, "annex", "Anhang")
    assert (here.document_dir("cu") / "Sections" / "annex.typ").read_bytes() == b'#import "/commands.typ": *\r\n\r\n= Anhang\r\n\r\n'
    data = entry.read_bytes()
    assert data.count(b"\r\n") == data.count(b"\n") and b"\r\r" not in data, "a line of the entry was written with another ending than the file's"
    assert data != crlf_entry and b'include "Sections/annex.typ"' in data
    raw = here.structure_file("cu").read_bytes()
    assert b"\r" not in raw, "structure.json is LF, whatever the entry has"
    structure.remove_section(here, "cu", "annex")
    assert entry.read_bytes() == crlf_entry, "the round trip gave the CRLF entry back byte for byte"
    # an LF entry stays LF and its sections are LF
    here = _example("ops_lf")
    structure.add_section(here, "cu", None, None, "annex", "Anhang")
    assert b"\r" not in (here.document_dir("cu") / "Sections" / "annex.typ").read_bytes() + here.document_typ("cu").read_bytes()


def test_add_section_takes_its_place_among_the_siblings_at_the_top_and_inside_a_group():
    here = _example("ops_positions")
    ids = lambda: [(n["id"], d) for n, d, _p in structure.walk(structure.read(here.structure_file("cu")))]
    structure.add_section(here, "cu", None, 0, "first", "First")
    structure.add_section(here, "cu", "general", 0, "intro", "Intro")
    structure.add_section(here, "cu", None, 2, "middle", "Middle")
    structure.add_section(here, "cu", None, None, "last", "Last")
    assert ids() == [("first", 1), ("general", 1), ("intro", 2), ("purpose", 2), ("middle", 1), ("journal", 1), ("last", 1)], ids()
    assert [n.id for n in structure.tree(here, "cu")] == ["first", "general", "middle", "journal", "last"]
    # the skeleton's heading is the title as given, markup and all
    structure.add_section(here, "cu", None, None, "markup", "The *bold* one")
    assert (here.document_dir("cu") / "Sections" / "markup.typ").read_bytes().endswith(b"= The *bold* one\n\n")


def test_add_group_and_nested_sections_have_the_levels_the_structure_means_in_typst():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    here = _example("ops_groups")
    before = _files(here, "cu")
    edit = structure.add_group(here, "cu", None, 1, "loads", GROUPS)
    assert (edit.op, edit.id, edit.structure, edit.entry, edit.created) == ("add_group", "loads", True, True, ()), "a group is no file"
    group = structure.find(structure.read(here.structure_file("cu")), "loads")[0]
    assert group == {"id": "loads", "title": GROUPS, "enabled": True, "children": []}
    assert '#heading(level: 1, "Lasten")' in here.document_typ("cu").read_text(encoding="utf-8")
    _compiles(here, "cu")
    structure.add_section(here, "cu", "loads", None, "live-loads", "Nutzlasten")
    _compiles(here, "cu")
    structure.add_group(here, "cu", "loads", None, "dead", {"fr": "Permanentes", "de": "Ständige", "en": "Dead"})
    structure.add_section(here, "cu", "dead", None, "floors", "Decken")
    _compiles(here, "cu")
    assert _titles(here, "cu") == [(1, "Allgemeines"), (2, "Zweck"), (1, "Lasten"), (2, "Nutzlasten"), (2, "Ständige"), (3, "Decken"), (1, "Änderungsverzeichnis")]
    # the same group, taken out again leaf by leaf and group by group: the document is what it was
    for node_id in ("floors", "dead", "live-loads", "loads"):
        structure.remove_section(here, "cu", node_id)
    after = _files(here, "cu")
    assert all(after[name] == data for name, data in before.items())
    assert len(set(after) - set(before)) == 2, "two files archived, and no other trace"
    _compiles(here, "cu")


def test_a_group_is_printed_in_the_documents_language_and_the_language_asked_for():
    here = _example("ops_group_language")
    structure.add_group(here, "cu", None, None, "loads", GROUPS)
    assert '#heading(level: 1, "Lasten")' in here.document_typ("cu").read_text(encoding="utf-8")
    structure.add_group(here, "cu", None, None, "others", {"fr": "Autres", "de": "Andere", "en": "Others"}, language="fr")
    text = here.document_typ("cu").read_text(encoding="utf-8")
    assert '#heading(level: 1, "Autres")' in text and '#heading(level: 1, "Charges")' in text, "the block is written in the language asked for"


def test_add_group_needs_its_title_in_all_three_languages_and_no_other():
    here = _example("ops_group_titles")
    before = _files(here, "cu")
    for lang in ("fr", "de", "en"):
        titles = {key: value for key, value in GROUPS.items() if key != lang}
        exc = _code("titles_missing", structure.add_group, here, "cu", None, None, "g", titles)
        assert exc.values["missing"] == [lang]
    exc = _code("titles_missing", structure.add_group, here, "cu", None, None, "g", {"fr": "a", "de": "  ", "en": "c"})
    assert exc.values["missing"] == ["de"]
    _code("titles_missing", structure.add_group, here, "cu", None, None, "g", None)
    _code("titles_missing", structure.add_group, here, "cu", None, None, "g", {})
    _code("titles_missing", structure.add_group, here, "cu", None, None, "g", {"fr": "a", "de": 3, "en": "c"})
    _code("bad_language", structure.add_group, here, "cu", None, None, "g", dict(GROUPS, it="Carichi"))
    _code("bad_title", structure.add_group, here, "cu", None, None, "g", dict(GROUPS, en="two\nlines"))
    _unchanged(here, "cu", before)


def test_add_section_refusals_name_their_code_and_write_nothing():
    here = _example("ops_add_refused")
    leaf_file = here.document_dir("cu") / "Sections" / "orphan.typ"
    leaf_file.write_text("= Someone's file\n", encoding="utf-8")
    before = _files(here, "cu")
    add = lambda **kw: structure.add_section(here, "cu", **{"parent_id": None, "position": None, "section_id": "fresh", "title": "Fresh", **kw})
    for bad in ("Bad_Id", "1abc", "", "a--b", "-a", "a-", "live loads", None, 5):
        _code("bad_id", add, section_id=bad)
    for taken in ("purpose", "general", "journal"):
        exc = _code("id_exists", add, section_id=taken)
        assert exc.values["id"] == taken
    exc = _code("file_exists", add, section_id="orphan")
    assert exc.values["file"] == "Sections/orphan.typ" and leaf_file.read_text(encoding="utf-8") == "= Someone's file\n", "nothing is overwritten"
    for bad in ("", "  ", "a\nb", "a\x00b", None, 3):
        _code("bad_title", add, title=bad)
    _code("no_such_node", add, parent_id="nowhere")
    _code("not_a_section", add, parent_id="purpose#2")
    _code("not_a_group", add, parent_id="purpose")
    for bad in (-1, 99, "x", True, 1.5):
        exc = _code("bad_position", add, position=bad)
        assert exc.values["count"] == 2
    _code("bad_position", add, parent_id="general", position=2)
    _code("bad_language", structure.add_section, here, "cu", None, None, "fresh", "Fresh", "it")
    _code("bad_mode", structure.add_section, here, "xx", None, None, "fresh", "Fresh")
    _unchanged(here, "cu", before)
    # the last place is one past the last sibling, and it is fine
    structure.add_section(here, "cu", "general", 1, "fresh", "Fresh")


def test_a_tree_goes_four_levels_deep_and_no_deeper():
    here = _example("ops_deep")
    titles = lambda n: {lang: f"{lang} {n}" for lang in ("fr", "de", "en")}
    structure.add_group(here, "cu", "general", None, "g2", titles("g2"))
    structure.add_group(here, "cu", "g2", None, "g3", titles("g3"))
    structure.add_section(here, "cu", "g3", None, "level4", "Level four")       # a section at level 4: the deepest there is
    structure.add_group(here, "cu", "g3", None, "g4", titles("g4"))              # a group at level 4: allowed, though it could hold nothing
    before = _files(here, "cu")
    exc = _code("too_deep", structure.add_section, here, "cu", "g4", None, "level5", "Level five")
    assert exc.values == {"depth": 5, "max": structure.MAX_DEPTH}
    _code("too_deep", structure.add_group, here, "cu", "g4", None, "g5", titles("g5"))
    _unchanged(here, "cu", before)


def test_a_project_laid_out_as_a_report_alone_has_no_cu_and_no_bp_to_work_on():
    import project
    root = conftest.tmpdir("ops_legacy")
    here = project.Project(root / "P.woodcore", {})
    for call in (lambda: structure.add_section(here, "cu", None, None, "x", "X"), lambda: structure.add_group(here, "bp", None, None, "x", GROUPS),
                 lambda: structure.remove_section(here, "cu", "x"), lambda: structure.move_node(here, "bp", "x", None, 0),
                 lambda: structure.rename_section(here, "cu", "x", "y"), lambda: structure.suggest_id(here, "cu", "x")):
        _code("no_such_document", call)


def test_an_entry_woodcore_cannot_lay_out_is_refused_before_anything_is_written():
    here = _example("ops_entry_refused")
    entry = here.document_typ("cu")
    torn = entry.read_bytes().decode("utf-8").replace(structure.END_TAG, "// woodcore:shared torn")
    entry.write_bytes(torn.encode("utf-8"))
    before = _files(here, "cu")
    for call in (lambda: structure.add_section(here, "cu", None, None, "fresh", "Fresh"),
                 lambda: structure.add_group(here, "cu", None, None, "fresh", GROUPS),
                 lambda: structure.remove_section(here, "cu", "journal"),
                 lambda: structure.move_node(here, "cu", "journal", None, 0),
                 lambda: structure.rename_section(here, "cu", "journal", "log")):
        exc = _code("entry_unreadable", call)
        assert exc.values["file"] == entry.name
    _unchanged(here, "cu", before)
    # an entry that is not there, and one with no block at all
    entry.unlink()
    _code("entry_unreadable", structure.add_section, here, "cu", None, None, "fresh", "Fresh")
    entry.write_bytes(b"#include \"x.typ\"\n")
    _code("entry_unreadable", structure.add_section, here, "cu", None, None, "fresh", "Fresh")
    assert not (here.document_dir("cu") / "Sections" / "fresh.typ").exists()


def test_a_write_that_fails_puts_back_what_was_written():
    here = _example("ops_write_failed")
    before = _files(here, "cu")
    original = structure.write

    def refuse(path, source):
        raise PermissionError(13, "Access is denied", str(path))
    structure.write = refuse
    try:
        exc = _code("write_failed", structure.add_section, here, "cu", None, None, "fresh", "Fresh")
        assert "structure.json" in str(exc) and "put back" in str(exc)
        _code("write_failed", structure.move_node, here, "cu", "journal", None, 0)
    finally:
        structure.write = original
    _unchanged(here, "cu", before)        # the new file is gone, the entry is as it was, structure.json never changed
    # the file move of a removal is the last step and fails alone: the structure and the entry are put back
    real_replace = structure._replace
    archives = here.document_dir("cu") / "Sections" / "archives"

    def flaky(source, target):
        if archives in Path(target).parents:
            raise PermissionError(13, "Access is denied", str(target))
        return real_replace(source, target)
    structure._replace = flaky
    try:
        _code("write_failed", structure.remove_section, here, "cu", "journal")
    finally:
        structure._replace = real_replace
    _unchanged(here, "cu", before)          # the structure and the entry are put back, and the archives folder holds no file
    assert (here.document_dir("cu") / "Sections" / "journal.typ").is_file()
    # a file that turns up where the new section's would be, between the check and the write, is not overwritten
    target = here.document_dir("cu") / "Sections" / "fresh.typ"
    do, _undo = structure._step_create(target, b"mine")
    target.write_bytes(b"someone else's")
    _code("file_exists", do)
    assert target.read_bytes() == b"someone else's"


def test_remove_section_archives_the_file_under_a_stamp_and_never_deletes():
    here = _example("ops_remove")
    folder = here.document_dir("cu")
    original = structure._stamp
    structure._stamp = lambda: "261001-120000"
    try:
        structure.add_section(here, "cu", None, None, "one", "One")
        structure.add_section(here, "cu", None, None, "two", "Two")
        (folder / "Sections" / "one.typ").write_bytes(b"one's own words\r\n")
        first = structure.remove_section(here, "cu", "one")
        assert first.archived == (folder / "Sections" / "archives" / "261001-120000-one.typ",)
        assert first.archived[0].read_bytes() == b"one's own words\r\n", "the file's bytes are kept as they were"
        # the same id again within the same second: the second archive gets a number
        structure.add_section(here, "cu", None, None, "one", "One again")
        second = structure.remove_section(here, "cu", "one")
        assert second.archived == (folder / "Sections" / "archives" / "261001-120000-one-2.typ",)
        assert sorted(p.name for p in (folder / "Sections" / "archives").iterdir()) == ["261001-120000-one-2.typ", "261001-120000-one.typ"]
    finally:
        structure._stamp = original
    assert re.fullmatch(r"\d{6}-\d{6}", structure._stamp()), "yymmdd-hhmmss"
    # a structure that names a file nobody has written is removed all the same, with nothing to archive
    structure.add_section(here, "cu", None, None, "ghost", "Ghost")
    (folder / "Sections" / "ghost.typ").unlink()
    edit = structure.remove_section(here, "cu", "ghost")
    assert edit.archived == () and edit.structure and "ghost" not in [n["id"] for n, _d, _p in structure.walk(structure.read(here.structure_file("cu")))]
    # a disabled section goes as well, and so does one shared with another document -- the copy there is that document's own file
    structure.set_enabled(here, "cu", "two", False)
    assert structure.remove_section(here, "cu", "two").archived
    source = structure.read(here.structure_file("cu"))
    structure.find(source, "purpose")[0]["shared_with"] = ["bp"]
    structure.write(here.structure_file("cu"), source)
    assert structure.remove_section(here, "cu", "purpose").archived and (here.document_dir("bp") / "Sections" / "purpose.typ").is_file()


def test_remove_section_refuses_a_group_that_is_not_empty_and_a_section_that_is_not_there():
    here = _example("ops_remove_refused")
    before = _files(here, "cu")
    exc = _code("group_not_empty", structure.remove_section, here, "cu", "general")
    assert exc.values == {"id": "general", "count": 1}
    _code("no_such_node", structure.remove_section, here, "cu", "nowhere")
    _code("no_such_node", structure.remove_section, here, "cu", "")
    _code("no_such_node", structure.remove_section, here, "cu", None)
    _code("not_a_section", structure.remove_section, here, "cu", "purpose#2")
    _code("bad_language", structure.remove_section, here, "cu", "journal", language="it")
    _unchanged(here, "cu", before)
    structure.remove_section(here, "cu", "purpose")
    structure.remove_section(here, "cu", "general")         # empty now
    assert [n["id"] for n in structure.read(here.structure_file("cu"))["sections"]] == ["journal"]


def _tall(name):
    """The example CU with `general` holding `a`, `b`, `c` and a group `inner` holding `d`, and a section `top` of its own: an order to move things in."""
    here = _example(name)
    for node_id, title in (("a", "A"), ("b", "B"), ("c", "C")):
        structure.add_section(here, "cu", "general", None, node_id, title)
    structure.add_group(here, "cu", "general", None, "inner", GROUPS)
    structure.add_section(here, "cu", "inner", None, "d", "D")
    structure.add_section(here, "cu", None, 0, "top", "Top")
    return here


def _shape(here, mode="cu"):
    """[(id, parent)] of the structure in document order."""
    return [(n["id"], p["id"] if p else None) for n, _d, p in structure.walk(structure.read(here.structure_file(mode)))]


def test_move_node_puts_a_section_at_a_place_counted_once_it_has_left_its_old_one():
    here = _tall("ops_move_position")
    order = lambda parent: [i for i, p in _shape(here) if p == parent]
    assert order("general") == ["purpose", "a", "b", "c", "inner"]
    structure.move_node(here, "cu", "purpose", "general", 2)
    assert order("general") == ["a", "b", "purpose", "c", "inner"], "among the siblings that are left: after b"
    structure.move_node(here, "cu", "purpose", "general", 0)
    assert order("general") == ["purpose", "a", "b", "c", "inner"]
    structure.move_node(here, "cu", "purpose", "general", None)
    assert order("general") == ["a", "b", "c", "inner", "purpose"]
    structure.move_node(here, "cu", "a", "general", 4)
    assert order("general") == ["b", "c", "inner", "purpose", "a"], "the last place is the number of siblings that are left"
    _no_leftovers(here, "cu")


def test_move_node_reparents_a_section_and_a_group_with_what_it_holds_and_moving_back_gives_the_files_back():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    here = _tall("ops_move_reparent")
    _compiles(here, "cu")
    before = _files(here, "cu")
    assert [t for t in _titles(here, "cu") if t[1] in ("Lasten", "D")] == [(2, "Lasten"), (3, "D")]
    edit = structure.move_node(here, "cu", "d", None, 1)           # a section out of its group to the top
    assert (edit.op, edit.structure, edit.entry, edit.created, edit.archived, edit.renamed) == ("move_node", True, True, (), (), ())
    assert ("d", None) in _shape(here) and [t for t in _titles(here, "cu") if t[1] == "D"] == [(1, "D")], "the file is independent of the depth it is included at"
    assert (here.document_dir("cu") / "Sections" / "d.typ").read_bytes() == before["Sections/d.typ"], "no file was touched"
    _compiles(here, "cu")
    structure.move_node(here, "cu", "d", "inner", 0)
    assert _files(here, "cu") == before, "moved back to where it was: every file byte for byte what it was"
    # a group with its subtree moves as one, and its sections take the levels of their new place
    structure.move_node(here, "cu", "inner", None, None)
    assert _shape(here)[-2:] == [("inner", None), ("d", "inner")]
    _compiles(here, "cu")
    assert [t for t in _titles(here, "cu") if t[1] in ("Lasten", "D")] == [(1, "Lasten"), (2, "D")]
    structure.move_node(here, "cu", "inner", "general", None)
    assert _files(here, "cu") == before


def test_moving_a_section_to_where_it_stands_writes_nothing():
    here = _tall("ops_move_nothing")
    before = _files(here, "cu")
    stamps = {p: p.stat().st_mtime_ns for p in (here.structure_file("cu"), here.document_typ("cu"))}
    for node_id, parent, at in (("b", "general", 2), ("top", None, 0), ("inner", "general", 4), ("d", "inner", None)):
        edit = structure.move_node(here, "cu", node_id, parent, at)
        assert not edit.changed and not edit.structure and not edit.entry, (node_id, parent, at)
    assert _files(here, "cu") == before and all(p.stat().st_mtime_ns == m for p, m in stamps.items())


def test_move_node_refusals_name_their_code_and_write_nothing():
    here = _tall("ops_move_refused")
    before = _files(here, "cu")
    _code("cycle", structure.move_node, here, "cu", "general", "general", 0)
    exc = _code("cycle", structure.move_node, here, "cu", "general", "inner", 0)
    assert exc.values == {"id": "general", "parent": "inner"}
    _code("cycle", structure.move_node, here, "cu", "a", "a", 0)
    _code("no_such_node", structure.move_node, here, "cu", "nowhere", None, 0)
    _code("no_such_node", structure.move_node, here, "cu", "a", "nowhere", 0)
    _code("not_a_section", structure.move_node, here, "cu", "purpose#2", None, 0)
    _code("not_a_group", structure.move_node, here, "cu", "a", "b", 0)
    for bad in (-1, 99, "x", True):
        _code("bad_position", structure.move_node, here, "cu", "a", "inner", bad)
    _code("bad_language", structure.move_node, here, "cu", "a", None, 0, language="it")
    _code("bad_mode", structure.move_node, here, "xx", "a", None, 0)
    _unchanged(here, "cu", before)
    # depth: `general` holds `inner` holds `d`, three levels; moved under a group at level 2 its deepest section would lie at level 5
    titles = lambda n: {lang: f"{lang} {n}" for lang in ("fr", "de", "en")}
    structure.add_group(here, "cu", None, None, "g1", titles("g1"))
    structure.add_group(here, "cu", "g1", None, "g2", titles("g2"))
    structure.add_group(here, "cu", "g2", None, "g3", titles("g3"))
    before = _files(here, "cu")
    exc = _code("too_deep", structure.move_node, here, "cu", "general", "g3", 0)
    assert exc.values == {"depth": 6, "max": 4}
    _code("too_deep", structure.move_node, here, "cu", "inner", "g3", 0)       # inner (2 levels) under g3 (level 3): its section at level 5
    _unchanged(here, "cu", before)
    structure.move_node(here, "cu", "a", "g3", 0)                              # a section under g3 lies at level 4: the deepest there is
    structure.move_node(here, "cu", "g3", "general", 0)                        # g3 with its section, under `general`: two levels from level 2 -- fine
    assert ("g3", "general") in _shape(here)


def test_rename_section_moves_the_file_and_changes_the_id_and_nothing_else():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    here = _tall("ops_rename")
    folder = here.document_dir("cu") / "Sections"
    (folder / "a.typ").write_bytes(b'#import "/commands.typ": *\r\n\r\n= Alpha\r\n\r\nthe engineer\'s own words\r\n')
    before = _files(here, "cu")
    edit = structure.rename_section(here, "cu", "a", "alpha")
    assert (edit.op, edit.id, edit.structure, edit.entry, edit.created, edit.archived) == ("rename_section", "alpha", True, True, (), ())
    assert edit.renamed == ((folder / "a.typ", folder / "alpha.typ"),)
    assert not (folder / "a.typ").exists() and (folder / "alpha.typ").read_bytes() == before["Sections/a.typ"], "the bytes are the engineer's and are kept"
    source = structure.read(here.structure_file("cu"))
    assert structure.find(source, "alpha")[0] == {"id": "alpha", "file": "Sections/alpha.typ", "enabled": True} and structure.find(source, "a") is None
    assert 'include "Sections/alpha.typ"' in here.document_typ("cu").read_text(encoding="utf-8") and '"Sections/a.typ"' not in here.document_typ("cu").read_text(encoding="utf-8")
    assert [n.id for n in structure.tree(here, "cu")[1].children] == ["purpose", "alpha", "b", "c", "inner"]
    assert structure.find_node(structure.tree(here, "cu"), "alpha").title == "Alpha"
    _no_leftovers(here, "cu")
    _compiles(here, "cu")
    # and back: every file what it was
    structure.rename_section(here, "cu", "alpha", "a")
    assert _files(here, "cu") == before
    # a group has no file and is no shared thing: its id alone changes
    edit = structure.rename_section(here, "cu", "inner", "nested")
    assert edit.renamed == () and edit.structure and ("nested", "general") in _shape(here) and ("d", "nested") in _shape(here)
    _compiles(here, "cu")
    # a section whose file nobody has written is renamed in the structure, with no file to move
    (folder / "b.typ").unlink()
    edit = structure.rename_section(here, "cu", "b", "beta")
    assert edit.renamed == () and ("beta", "general") in _shape(here) and not (folder / "beta.typ").exists()


def test_a_shared_section_keeps_its_id():
    here = _tall("ops_rename_shared")
    folder = here.document_dir("cu") / "Sections"
    # listed as shared in structure.json
    source = structure.read(here.structure_file("cu"))
    structure.find(source, "a")[0]["shared_with"] = ["bp"]
    structure.write(here.structure_file("cu"), source)
    before = _files(here, "cu")
    exc = _code("shared", structure.rename_section, here, "cu", "a", "alpha")
    assert exc.values["shared_with"] == ["bp"]
    # not listed, but the file carries a shared tag
    (folder / "b.typ").write_text('= B\n// woodcore:shared live-loads\ntext\n// woodcore:/shared live-loads\n', encoding="utf-8")
    before = _files(here, "cu")
    exc = _code("shared", structure.rename_section, here, "cu", "b", "beta")
    assert exc.values == {"id": "b", "shared_with": [], "shared_ids": ["live-loads"]}
    _unchanged(here, "cu", before)
    # stopping to share it frees the id
    (folder / "b.typ").write_text("= B\n", encoding="utf-8")
    assert structure.rename_section(here, "cu", "b", "beta").renamed


def test_rename_section_refusals_name_their_code_and_write_nothing():
    here = _tall("ops_rename_refused")
    folder = here.document_dir("cu") / "Sections"
    (folder / "taken.typ").write_text("= Taken\n", encoding="utf-8")
    before = _files(here, "cu")
    for bad in ("Bad_Id", "1a", "", "a--b", None):
        _code("bad_id", structure.rename_section, here, "cu", "a", bad)
    _code("same_id", structure.rename_section, here, "cu", "a", "a")
    for taken in ("b", "general", "inner", "journal"):
        exc = _code("id_exists", structure.rename_section, here, "cu", "a", taken)
        assert exc.values["id"] == taken
    exc = _code("file_exists", structure.rename_section, here, "cu", "a", "taken")
    assert exc.values["file"] == "Sections/taken.typ"
    _code("no_such_node", structure.rename_section, here, "cu", "nowhere", "x")
    _code("not_a_section", structure.rename_section, here, "cu", "purpose#2", "x")
    _code("bad_language", structure.rename_section, here, "cu", "a", "x", language="it")
    _unchanged(here, "cu", before)


def test_suggest_id_proposes_a_free_id_in_the_form_each_document_uses():
    here = _example("ops_suggest")
    assert structure.suggest_id(here, "cu", "Live loads") == "live-loads"
    assert structure.suggest_id(here, "cu", "Nutzlasten über 5 m") == "nutzlasten-uber-5-m", "accents taken off"
    assert structure.suggest_id(here, "cu", "2nd floor") == "section-2nd-floor", "an id starts with a letter"
    assert structure.suggest_id(here, "cu", "") == structure.suggest_id(here, "cu", "   "), "a title with no letters still gets an id"
    assert structure.ID_PATTERN.match(structure.suggest_id(here, "cu", "!!!"))
    structure.add_section(here, "cu", None, None, "live-loads", "Live loads")
    assert structure.suggest_id(here, "cu", "Live loads") == "live-loads-2"
    (here.document_dir("cu") / "Sections" / "live-loads-2.typ").write_text("= x\n", encoding="utf-8")
    assert structure.suggest_id(here, "cu", "Live loads") == "live-loads-3", "a file lying there counts as taken"
    assert structure.suggest_id(here, "cu", "Purpose") == "purpose-2"
    # the report's sections are numbered: the next number and the slug
    assert structure.suggest_id(here, "rs", "Brandschutz Nachweis") == "008-brandschutz-nachweis"
    _code("bad_mode", structure.suggest_id, here, "xx", "a")


# --- the report: the same operations on its #include lines ---------------------------------------------------------------

def _include_text(here):
    return here.document_typ("rs").read_bytes().decode("utf-8")


REPORT_LF = "\n".join([
    "// entry", '#set page(paper: "a4")', "",
    '#include "Sections/001-a.typ"',
    '// #include "Sections/002-b.typ"',
    '  #include "Sections/003-c.typ"',
    '#include "Sections/004-d.typ"', "",
])


def test_the_report_adds_a_section_by_the_include_lines_rule_and_keeps_the_rest_of_the_entry():
    for ending in ("\n", "\r\n"):
        here = _report(conftest.tmpdir("ops_rs_add") / ("crlf" if ending == "\r\n" else "lf"), ending)
        before = _include_text(here)
        assert before == REPORT_LF.replace("\n", ending)
        edit = structure.add_section(here, "rs", None, 2, "005-new", "New one")
        new = here.document_dir("rs") / "Sections" / "005-new.typ"
        assert (edit.op, edit.mode, edit.id, edit.structure, edit.entry, edit.created) == ("add_section", "rs", "005-new", False, True, (new,))
        assert new.read_bytes() == f'#import "/commands.typ": *{ending}{ending}= New one{ending}{ending}'.encode()
        # the include lines stay where they stand and each holds the next section: the commented one stays commented, the indentation stays with its place
        assert _include_text(here) == "\n".join([
            "// entry", '#set page(paper: "a4")', "",
            '#include "Sections/001-a.typ"',
            '// #include "Sections/002-b.typ"',
            '  #include "Sections/005-new.typ"',
            '#include "Sections/003-c.typ"',
            '#include "Sections/004-d.typ"', "",
        ]).replace("\n", ending)
        assert [(n.id, n.enabled) for n in structure.tree(here, "rs")] == [("001-a", True), ("002-b", False), ("005-new", True), ("003-c", True), ("004-d", True)]
        assert structure.find_node(structure.tree(here, "rs"), "005-new").title == "New one"
        # the end, and the front
        structure.add_section(here, "rs", None, None, "006-last", "Last")
        structure.add_section(here, "rs", None, 0, "000-first", "First")
        assert [n.id for n in structure.tree(here, "rs")] == ["000-first", "001-a", "002-b", "005-new", "003-c", "004-d", "006-last"]
        text = _include_text(here)
        assert text.count("\r\n") == (text.count("\n") if ending == "\r\n" else 0), "a line of the entry has another ending than the file's"
        _no_leftovers(here, "rs")


def test_the_report_of_a_project_laid_out_alone_imports_the_engine_as_it_always_did():
    import project
    root = conftest.tmpdir("ops_rs_legacy")
    here = project.Project(root / "P.woodcore", {})
    entry = here.document_typ("rs")
    _write(entry, '#include "Sections/001-a.typ"\n')
    _write(here.document_dir("rs") / "Sections" / "001-a.typ", "= A\n")
    assert here.modes == ("rs",)
    structure.add_section(here, "rs", None, None, "002-b", "B")
    assert (here.document_dir("rs") / "Sections" / "002-b.typ").read_bytes() == b'#import "../commands.typ": *\n\n= B\n\n'      # relative on purpose: the import add_section writes into a report laid out alone, which no probe compiles
    assert entry.read_bytes() == b'#include "Sections/001-a.typ"\n#include "Sections/002-b.typ"\n'
    structure.move_node(here, "rs", "002-b", None, 0)
    assert entry.read_bytes() == b'#include "Sections/002-b.typ"\n#include "Sections/001-a.typ"\n'
    assert structure.suggest_id(here, "rs", "C") == "003-c"


def test_the_report_moves_a_section_by_exchanging_the_sections_of_its_include_lines():
    for ending in ("\n", "\r\n"):
        here = _report(conftest.tmpdir("ops_rs_move") / ("crlf" if ending == "\r\n" else "lf"), ending)
        before = _include_text(here)
        files = _files(here, "rs")
        edit = structure.move_node(here, "rs", "001-a", None, 2)
        assert (edit.op, edit.structure, edit.entry, edit.created, edit.archived, edit.renamed) == ("move_node", False, True, (), (), ())
        assert _include_text(here) == "\n".join([
            "// entry", '#set page(paper: "a4")', "",
            '// #include "Sections/002-b.typ"',
            '#include "Sections/003-c.typ"',
            '  #include "Sections/001-a.typ"',
            '#include "Sections/004-d.typ"', "",
        ]).replace("\n", ending), "the commented include went with its section; the indentation stayed with the third line, whichever section stands there"
        assert [(n.id, n.enabled) for n in structure.tree(here, "rs")] == [("002-b", False), ("003-c", True), ("001-a", True), ("004-d", True)]
        assert {k: v for k, v in _files(here, "rs").items() if k.startswith("Sections/")} == {k: v for k, v in files.items() if k.startswith("Sections/")}, "no file was renamed"
        structure.move_node(here, "rs", "001-a", None, 0)
        assert _include_text(here) == before, "moved back: the entry file byte for byte as it was"
        assert not structure.move_node(here, "rs", "003-c", None, 2).changed and _include_text(here) == before
        structure.move_node(here, "rs", "004-d", None, 0)
        structure.move_node(here, "rs", "004-d", None, None)
        assert _include_text(here) == before


def test_the_report_removes_a_section_by_commenting_its_line_and_archiving_its_file():
    for ending in ("\n", "\r\n"):
        here = _report(conftest.tmpdir("ops_rs_remove") / ("crlf" if ending == "\r\n" else "lf"), ending)
        folder = here.document_dir("rs")
        original = structure._stamp
        structure._stamp = lambda: "261001-120000"
        try:
            edit = structure.remove_section(here, "rs", "003-c")
        finally:
            structure._stamp = original
        archived = folder / "Sections" / "archives" / "261001-120000-003-c.typ"
        assert (edit.op, edit.structure, edit.entry, edit.archived) == ("remove_section", False, True, (archived,))
        assert archived.read_bytes() == b"== Gamma starts at two\n\n=== Gamma deeper\n\n= Gamma second top\n".replace(b"\n", ending.encode()) and not (folder / "Sections" / "003-c.typ").exists()
        assert _include_text(here) == "\n".join([
            "// entry", '#set page(paper: "a4")', "",
            '#include "Sections/001-a.typ"',
            '// #include "Sections/002-b.typ"',
            '  // archived: Sections/003-c.typ (now Sections/archives/261001-120000-003-c.typ)',
            '#include "Sections/004-d.typ"', "",
        ]).replace("\n", ending), "the line is a comment and no include any more, in the indentation it had"
        assert [n.id for n in structure.tree(here, "rs")] == ["001-a", "002-b", "004-d"], "the tree shows the section gone, not a disabled one whose file is missing"
        # the commented-out one goes too, and a section included twice keeps its file while a line of it is left
        structure.remove_section(here, "rs", "002-b")
        entry = here.document_typ("rs")
        entry.write_bytes((_include_text(here) + f'#include "Sections/004-d.typ"{ending}').encode("utf-8"))
        assert [n.id for n in structure.tree(here, "rs")] == ["001-a", "004-d", "004-d#2"]
        twice = structure.remove_section(here, "rs", "004-d#2")
        assert twice.archived == () and (folder / "Sections" / "004-d.typ").is_file()
        assert [n.id for n in structure.tree(here, "rs")] == ["001-a", "004-d"]
        _no_leftovers(here, "rs")


def test_the_report_renames_a_file_and_every_include_line_that_names_it():
    for ending in ("\n", "\r\n"):
        here = _report(conftest.tmpdir("ops_rs_rename") / ("crlf" if ending == "\r\n" else "lf"), ending)
        folder = here.document_dir("rs") / "Sections"
        entry = here.document_typ("rs")
        entry.write_bytes((_include_text(here) + f'// #include "Sections/004-d.typ"{ending}').encode("utf-8"))
        before = _include_text(here)
        bytes_of_d = (folder / "004-d.typ").read_bytes()
        edit = structure.rename_section(here, "rs", "004-d", "040-dee")
        assert (edit.op, edit.id, edit.structure, edit.entry, edit.renamed) == ("rename_section", "040-dee", False, True, ((folder / "004-d.typ", folder / "040-dee.typ"),))
        assert not (folder / "004-d.typ").exists() and (folder / "040-dee.typ").read_bytes() == bytes_of_d
        assert _include_text(here) == before.replace("004-d.typ", "040-dee.typ"), "both lines, the commented-out one with its comment, and nothing else"
        assert [n.id for n in structure.tree(here, "rs")] == ["001-a", "002-b", "003-c", "040-dee", "040-dee#2"]
        structure.rename_section(here, "rs", "040-dee", "004-d")
        assert _include_text(here) == before and (folder / "004-d.typ").read_bytes() == bytes_of_d


def test_the_report_has_no_groups_and_no_nesting_and_refuses_what_it_cannot_do():
    here = _report(conftest.tmpdir("ops_rs_refused"))
    folder = here.document_dir("rs") / "Sections"
    _write(folder / "009-taken.typ", "= Taken\n")
    _write(folder / "010-shared.typ", "= S\n// woodcore:shared block\ntext\n// woodcore:/shared block\n")
    entry = here.document_typ("rs")
    entry.write_bytes(entry.read_bytes() + b'#include "Sections/010-shared.typ"\n')
    before = (_files(here, "rs"), entry.read_bytes())
    snap = lambda: (_files(here, "rs"), entry.read_bytes())
    _code("rs_no_groups", structure.add_group, here, "rs", None, None, "g", GROUPS)
    _code("rs_no_nesting", structure.add_section, here, "rs", "001-a", None, "011-x", "X")
    _code("rs_no_nesting", structure.move_node, here, "rs", "003-c", "001-a", 0)
    for bad in ("", "a b", "a/b", "a#2", "-a", None, "durée"):
        _code("bad_id", structure.add_section, here, "rs", None, None, bad, "X")
        _code("bad_id", structure.rename_section, here, "rs", "003-c", bad)
    _code("id_exists", structure.add_section, here, "rs", None, None, "001-a", "X")
    _code("id_exists", structure.add_section, here, "rs", None, None, "001-A", "X")
    _code("id_exists", structure.rename_section, here, "rs", "003-c", "004-d")
    exc = _code("file_exists", structure.add_section, here, "rs", None, None, "009-taken", "X")
    assert exc.values["file"] == "Sections/009-taken.typ"
    _code("file_exists", structure.rename_section, here, "rs", "003-c", "009-taken")
    _code("same_id", structure.rename_section, here, "rs", "003-c", "003-c")
    exc = _code("shared", structure.rename_section, here, "rs", "010-shared", "011-shared")
    assert exc.values["shared_ids"] == ["block"]
    _code("bad_title", structure.add_section, here, "rs", None, None, "011-x", "")
    for bad in (-1, 99, "x", True):
        _code("bad_position", structure.add_section, here, "rs", None, bad, "011-x", "X")
        _code("bad_position", structure.move_node, here, "rs", "003-c", None, bad)
    for call in (lambda: structure.remove_section(here, "rs", "nowhere"), lambda: structure.move_node(here, "rs", "nowhere", None, 0),
                 lambda: structure.rename_section(here, "rs", "nowhere", "x")):
        _code("no_such_node", call)
    for call in (lambda: structure.remove_section(here, "rs", "001-a#2"), lambda: structure.move_node(here, "rs", "001-a#2", None, 0),
                 lambda: structure.rename_section(here, "rs", "001-a#2", "x")):
        _code("not_a_section", call)
    assert snap() == before, "a refused operation on the report wrote"
    # an entry that is not there
    entry.unlink()
    _code("entry_unreadable", structure.add_section, here, "rs", None, None, "011-x", "X")


def test_the_reports_entry_still_compiles_after_each_operation_on_its_sections():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    here = _example("ops_rs_compile")
    structure.add_section(here, "rs", None, 3, "008-annex", "Anhang")
    _compiles(here, "rs")
    names = [title for _level, title in _titles(here, "rs")]
    assert names.index("Baustoffe") < names.index("Anhang") < names.index("Einwirkungen"), "the new section is the fourth of the report"
    structure.move_node(here, "rs", "008-annex", None, None)
    structure.rename_section(here, "rs", "008-annex", "009-annex")
    structure.remove_section(here, "rs", "001-einleitung")
    _compiles(here, "rs")
    assert [n.id for n in structure.tree(here, "rs")] == ["002-grundlagen", "003-baustoffe", "004-einwirkungen", "005-tragwerksanalyse", "006-nachweise", "007-literatur", "009-annex"]
    assert [t for _l, t in _titles(here, "rs")][-1] == "Anhang"


def test_every_code_is_fired_by_some_refusal_and_none_is_left_unsaid():
    here = _tall("ops_codes")
    (here.document_dir("cu") / "Sections" / "orphan.typ").write_text("= Orphan\n", encoding="utf-8")
    source = structure.read(here.structure_file("cu"))
    structure.find(source, "a")[0]["shared_with"] = ["bp"]
    structure.write(here.structure_file("cu"), source)
    import project
    alone = project.Project(conftest.tmpdir("ops_codes_alone") / "P.woodcore", {})
    fired = {}

    def fire(call):
        try:
            call()
        except structure.StructureError as exc:
            fired[exc.code] = fired.get(exc.code, 0) + 1
            return
        raise AssertionError("not refused")

    fire(lambda: structure.add_section(here, "xx", None, None, "x", "X"))
    fire(lambda: structure.add_section(alone, "cu", None, None, "x", "X"))
    fire(lambda: structure.add_section(here, "cu", None, None, "x", "X", "it"))
    fire(lambda: structure.add_section(here, "cu", None, None, "Bad", "X"))
    fire(lambda: structure.add_section(here, "cu", None, None, "purpose", "X"))
    fire(lambda: structure.add_section(here, "cu", None, None, "orphan", "X"))
    fire(lambda: structure.add_section(here, "cu", None, None, "x", ""))
    fire(lambda: structure.add_group(here, "cu", None, None, "x", {"fr": "a"}))
    fire(lambda: structure.add_section(here, "cu", "nowhere", None, "x", "X"))
    fire(lambda: structure.remove_section(here, "cu", "purpose#2"))
    fire(lambda: structure.add_section(here, "cu", "b", None, "x", "X"))
    titles = {lang: lang for lang in ("fr", "de", "en")}
    for parent, node in (("general", "g2"), ("g2", "g3"), ("g3", "g4")):
        structure.add_group(here, "cu", parent, None, node, titles)
    fire(lambda: structure.add_section(here, "cu", "g4", None, "x", "X"))
    fire(lambda: structure.add_section(here, "cu", None, 99, "x", "X"))
    fire(lambda: structure.remove_section(here, "cu", "general"))
    fire(lambda: structure.move_node(here, "cu", "general", "g2", 0))
    fire(lambda: structure.rename_section(here, "cu", "b", "b"))
    fire(lambda: structure.rename_section(here, "cu", "a", "alpha"))
    fire(lambda: structure.add_group(here, "rs", None, None, "x", titles))
    fire(lambda: structure.add_section(here, "rs", "001-einleitung", None, "x", "X"))
    entry = here.document_typ("cu")
    entry.write_bytes(entry.read_bytes().replace(structure.END_TAG.encode(), b"// woodcore:shared torn"))
    fire(lambda: structure.add_section(here, "cu", None, None, "x", "X"))
    entry.write_bytes(entry.read_bytes().replace(b"// woodcore:shared torn", structure.END_TAG.encode()))
    real = structure.write

    def refuse(path, source):
        raise PermissionError(13, "Access is denied", str(path))
    structure.write = refuse
    try:
        fire(lambda: structure.add_section(here, "cu", None, None, "x", "X"))
    finally:
        structure.write = real
    (here.document_dir("cu") / "Sections" / "purpose.typ").write_bytes(b"= Zweck\n\n// woodcore:object text p1\nOffen.\n")
    fire(lambda: structure.tag_section(here, "cu", "purpose"))
    assert sorted(fired) == sorted(structure.CODES), f"unfired: {sorted(set(structure.CODES) - set(fired))}, unknown: {sorted(set(fired) - set(structure.CODES))}"
