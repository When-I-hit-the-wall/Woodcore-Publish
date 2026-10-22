"""Sharing a section between the three documents (calc/sharing.py, the three document modes, work package 5.1; keeping the copies in step is calc/sync.py's since the rework of 01.10.2026).

What is held here: `share` copying a section's whole file -- a heading standing for its file -- into a convention's, a base de projet's and the report's `Sections/`, wrapping its body in shared tags where it had none, writing the copy's import line, placing it at the end of the group of the same id (else the document), in the report after the last `#include` line, and writing `shared_with` on every side; a report's file shared under an id made from its stem; a path that would stop reaching its file written root-absolute, inside the block in every copy; every refusal with its code and nothing written; **the copies compiling in their documents**; `index` reading every copy of every block at once and naming the files whose tags cannot be read; the tags taking a file's own line ending and each copy saying its own; `share` writing the synchronisation records of both sides (calc/sync.py, whose own checks are tests/test_sync.py), and `plan_sync` and `apply_sync` -- the write into every copy the rework of 01.10.2026 replaced -- being gone; `stop_sharing` with two copies (both unshared) and three (two stay shared); `reconcile` writing back what the tags say after tags were taken off or put on by hand.

Every project is made here, in this process's own temporary folder (conftest.tmpdir), by project_template.create, and the sections a check shares are made by structure.add_section and add_group: the checks do not depend on what the content templates of the convention and the base de projet hold.
"""

import subprocess

import conftest
from conftest import Skip

import documents
import project_template
import sharing
import structure
import typst_paths
import validation

TITLES = {"fr": "Sondes", "de": "Sonden", "en": "Probes"}
PROBE = "shared-probe"
# The section's body after its heading: prose, a parametric object -- a list of norms with free lines (spec 2026-10-21-commandes-typst-refonte, REQ-019), which may stand inside a shared block -- and a sub-heading, which the tree gives an id of its own.
BODY = (
    "Sondentext im gemeinsamen Block.\n"
    "\n"
    "// woodcore:object show-norm-list probe-use\n"
    "#show-norm-list(\n"
    "  keys: (\n"
    "    [Nutzung],\n"
    "    [Büro],\n"
    "  ),\n"
    ")\n"
    "// woodcore:/object probe-use\n"
    "\n"
    "== Unterabschnitt\n"
    "\n"
    "Mehr Sondentext.\n"
)


def _project(name, groups=("cu", "bp")):
    """A new project of three documents, a group `probes` in each of `groups`, and in the convention a section `shared-probe` under it holding BODY."""
    here = project_template.create(conftest.tmpdir(name) / "Halle", "Halle")
    for mode in groups:
        structure.add_group(here, mode, None, None, "probes", TITLES)
    structure.add_section(here, "cu", "probes", None, PROBE, "Sondenabschnitt")
    path = _file(here, "cu")
    path.write_bytes(path.read_bytes() + BODY.encode("utf-8"))
    return here


def _file(here, mode, name=PROBE):
    return here.document_dir(mode) / "Sections" / f"{name}.typ"


def _text(path):
    return typst_paths.read_text(path)


def _snapshot(here):
    """{path from the project's folder: bytes} of every file of the project but the engine and the export: what a refusal must leave as it was."""
    root = here.root
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and "_woodcore" not in p.relative_to(root).parts}


def _leftovers(here):
    return [p for p in here.root.rglob("*") if p.is_file() and p.suffix in (".tmp", ".part")]


def _code(code, what, *args, **kwargs):
    """`what(*args, **kwargs)` refuses with `code`: the SharingError, its code and an English sentence."""
    try:
        what(*args, **kwargs)
    except sharing.SharingError as exc:
        assert exc.code == code, f"refused with {exc.code!r}, not {code!r}: {exc}"
        assert str(exc), "a refusal says something"
        return exc
    raise AssertionError(f"{what.__name__}{args} was not refused with {code!r}")


def _leaf(here, mode, section_id):
    found = structure.find(structure.read(here.structure_file(mode)), section_id)
    assert found is not None, f"{mode} has no section {section_id!r}"
    return found


def _node(here, mode, node_id):
    node = structure.find_node(structure.tree(here, mode), node_id)
    assert node is not None, f"{mode}: no node {node_id!r}"
    return node


def _compiles(here, mode, name):
    """The document compiles -- Typst is the judge -- and the words its PDF prints."""
    from pypdf import PdfReader
    out = conftest.tmpdir(f"sharing_pdf_{name}_{mode}") / f"{mode}.pdf"
    done = subprocess.run(["typst", *documents.compile_args(here, mode, [], target=out)], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, f"{mode} does not compile: {done.stderr}"
    return " ".join(page.extract_text() or "" for page in PdfReader(str(out)).pages)


def _block_of(here, mode, shared_id=PROBE, name=PROBE):
    [copy] = [c for c in sharing.copies(here, shared_id) if c.mode == mode and c.file.name == f"{name}.typ"]
    return copy


# --- the codes ---------------------------------------------------------------------------------------------------

def test_the_codes_are_unique_and_a_refusal_is_a_structure_error():
    assert len(sharing.CODES) == len(set(sharing.CODES)) and all(isinstance(c, str) and c for c in sharing.CODES)
    exc = sharing.SharingError("plain", "no_copies", shared_id="x")
    assert isinstance(exc, structure.StructureError) and isinstance(exc, validation.ValidationError), "whatever catches the catalogue's refusals catches these"
    assert (exc.code, exc.values, str(exc)) == ("no_copies", {"shared_id": "x"}, "plain")


# --- sharing -----------------------------------------------------------------------------------------------------

def test_sharing_a_section_of_the_convention_into_the_base_de_projet_copies_its_whole_file():
    here = _project("share_cu_bp")
    source = _file(here, "cu")
    before = _text(source)
    # the sub-heading is what the engineer clicked: it stands for its whole file
    result = sharing.share(here, "cu", f"{PROBE}#2", "bp")
    copy = _file(here, "bp")
    assert result.copies == (("bp", copy),) and result.modes == ("bp",)
    assert (result.shared_ids, result.wrapped, result.source_changed) == ((PROBE,), True, True)
    after = _text(source)
    lines = after.splitlines()
    assert lines[0] == documents.import_line(here), "the import line stays outside the block"
    # the title is the document's own, at the level the section prints at there: the block opens right after it (06.10.2026)
    assert lines[1:5] == ["", "// woodcore:object heading title", "== Sondenabschnitt", "// woodcore:/object title"], lines[:6]
    assert lines[5] == f"// woodcore:shared {PROBE}", "the shared block does not open right after the title"
    assert lines[-1] == f"// woodcore:/shared {PROBE}" and lines[-2] == "Mehr Sondentext."
    assert after.replace(f"// woodcore:shared {PROBE}\n", "").replace(f"// woodcore:/shared {PROBE}\n", "") == before, "the tags added and nothing else"
    assert _text(copy) == after, "the copy is the file, byte for byte: the import line is the project's own already"
    assert structure.check_tags(after) == [], "the object stands inside the shared block, which may hold one"
    # the structures, on both sides
    leaf, depth, parent = _leaf(here, "bp", PROBE)
    assert (leaf, depth, parent["id"]) == ({"id": PROBE, "file": f"Sections/{PROBE}.typ", "enabled": True, "shared_with": ["cu"]}, 2, "probes")
    assert parent["children"][-1] is leaf, "at the end of the group of the same id"
    assert _leaf(here, "cu", PROBE)[0]["shared_with"] == ["bp"]
    assert f'#include "Sections/{PROBE}.typ"' in _text(here.document_typ("bp"))
    assert structure.sync_entry(here.document_typ("bp"), here.structure_file("bp"), structure.document_language(here, "bp")) is False, "the entry's block is what the structure says"
    assert here.document_typ("bp") in result.entries and here.structure_file("bp") in result.structures and here.structure_file("cu") in result.structures
    # what the tree and copies() see
    assert (_node(here, "cu", PROBE).shared_with, _node(here, "bp", PROBE).shared_with) == (("bp",), ("cu",))
    found = sharing.copies(here, PROBE)
    assert [(c.mode, c.file) for c in found] == [("cu", source), ("bp", copy)]
    for c in found:
        text = _text(c.file)
        assert text[c.start:c.end] == c.block_text and "Sondentext im gemeinsamen Block." in c.block_text and "Sondenabschnitt" not in c.block_text and c.newline == "\n"
    assert not [d for d in sharing.reconcile(here, write=False).changes if d.id == PROBE], "what share wrote is what the tags say"
    assert not _leftovers(here)


def test_a_copy_goes_at_the_end_of_the_document_where_the_target_has_no_such_group():
    here = _project("share_no_group", groups=("cu",))
    sharing.share(here, "cu", PROBE, ["bp"])
    source = structure.read(here.structure_file("bp"))
    assert source["sections"][-1] == {"id": PROBE, "file": f"Sections/{PROBE}.typ", "enabled": True, "shared_with": ["cu"]}


def test_sharing_into_the_report_adds_its_include_line_after_the_last_one():
    here = _project("share_cu_rs")
    entry = here.document_typ("rs")
    before = _text(entry)
    result = sharing.share(here, "cu", PROBE, ["rs"])
    copy = _file(here, "rs")
    assert result.copies == (("rs", copy),), "the id as the file's stem: no number in front of it"
    after = _text(entry)
    includes = [line for line in after.splitlines() if '#include "Sections/' in line]
    assert includes[-1] == f'#include "Sections/{PROBE}.typ"'
    assert after.replace(f'#include "Sections/{PROBE}.typ"\n', "", 1) == before, "one line added, nothing else of the entry moved"
    node = _node(here, "rs", PROBE)
    assert (node.kind, node.file, node.shared_with, node.shared_ids) == ("file", f"Sections/{PROBE}.typ", ("cu",), (PROBE,)), "one id in the three documents"
    assert _leaf(here, "cu", PROBE)[0]["shared_with"] == ["rs"]
    # and a third document afterwards: every copy it had learns of it
    sharing.share(here, "cu", PROBE, ["bp"])
    assert _leaf(here, "cu", PROBE)[0]["shared_with"] == ["bp", "rs"]
    assert _leaf(here, "bp", PROBE)[0]["shared_with"] == ["cu", "rs"]
    assert _node(here, "rs", PROBE).shared_with == ("cu", "bp")


def test_the_copies_compile_in_their_documents_and_print_the_shared_words():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    here = _project("share_compile")
    sharing.share(here, "cu", PROBE, ["bp", "rs"])
    for mode in ("cu", "bp", "rs"):
        words = _compiles(here, mode, "three")
        assert "Sondentext im gemeinsamen Block" in words and "Büro" in words, f"{mode} does not print the shared section"


def test_a_section_of_the_report_is_shared_under_an_id_made_from_its_stem():
    here = _project("share_rs")
    structure.add_section(here, "rs", None, None, "009-schneelast-probe", "Schneelast Sonde")
    rs_file = _file(here, "rs", "009-schneelast-probe")
    result = sharing.share(here, "rs", "009-schneelast-probe", ["cu", "bp"])
    assert sharing.id_from_stem("009-schneelast-probe") == "schneelast-probe" and sharing.id_from_stem("12_Dach") == "dach"
    assert sharing.id_from_stem("001-2d-plan") == "section-2d-plan", "an id starts with a letter"
    assert result.shared_ids == ("schneelast-probe",) and rs_file.is_file(), "the report's file keeps its name"
    assert "// woodcore:shared schneelast-probe" in _text(rs_file)
    for mode in ("cu", "bp"):
        leaf, depth, _parent = _leaf(here, mode, "schneelast-probe")
        assert depth == 1 and leaf["shared_with"] == [m for m in ("cu", "bp", "rs") if m != mode], "no group of the report: at the end of the document"
        assert _text(_file(here, mode, "schneelast-probe")) == _text(rs_file)
    assert _node(here, "rs", "009-schneelast-probe").shared_with == ("cu", "bp")
    # an id of one's own for a report's file; none for a convention's, whose id is its file's name
    structure.add_section(here, "rs", None, None, "010-wind-probe", "Wind Sonde")
    sharing.share(here, "rs", "010-wind-probe", "cu", section_id="wind-loads-probe")
    assert _file(here, "cu", "wind-loads-probe").is_file()
    snap = _snapshot(here)
    _code("bad_id", sharing.share, here, "cu", PROBE, "bp", section_id="another-id")
    _code("bad_id", sharing.share, here, "rs", "010-wind-probe", "bp", section_id="Wind Loads")
    assert _snapshot(here) == snap


def test_a_path_that_would_not_reach_its_file_from_the_other_document_is_written_root_absolute():
    here = _project("share_paths")
    report = here.document_dir("rs")
    (report / "probe-notiz.txt").write_text("Notiz aus dem Bericht", encoding="utf-8")
    structure.add_section(here, "rs", None, None, "009-notiz-probe", "Notiz Sonde")
    path = _file(here, "rs", "009-notiz-probe")
    # one read inside the shared block, one after it -- tagged by hand
    path.write_text(_text(path) + '// woodcore:shared notiz-probe\n#read("../probe-notiz.txt")\n// woodcore:/shared notiz-probe\n\n#read("../probe-notiz.txt")\n', encoding="utf-8", newline="")
    result = sharing.share(here, "rs", "009-notiz-probe", "cu")
    absolute = f'#read("/{report.name}/probe-notiz.txt")'
    source, copy = _text(path), _text(_file(here, "cu", "notiz-probe"))
    assert result.wrapped is False and result.shared_ids == ("notiz-probe",), "a file with shared tags keeps them, and its one id names the copy"
    assert source.count(absolute) == 1 and source.count('#read("../probe-notiz.txt")') == 1, "in the source only the one inside the block"
    assert copy.count(absolute) == 2, "in the copy both: outside the block for the copy alone"
    assert _block_of(here, "rs", "notiz-probe", "009-notiz-probe").block_text == _block_of(here, "cu", "notiz-probe", "notiz-probe").block_text, "the copies start identical between their tags"
    assert {p for p, _change in result.rewritten} == {path, _file(here, "cu", "notiz-probe")}
    if conftest.have_typst():
        for mode in ("rs", "cu"):
            assert "Notiz aus dem Bericht" in _compiles(here, mode, "paths")


def test_every_refusal_says_its_code_and_writes_nothing():
    here = _project("share_refused")
    sharing.share(here, "cu", PROBE, "bp")
    structure.add_section(here, "cu", "probes", None, "second-probe", "Zweite Sonde")
    structure.add_section(here, "bp", None, None, "taken-probe", "Belegt")
    structure.add_section(here, "cu", None, None, "taken-probe", "Belegt auch")
    stray = _file(here, "rs", "second-probe")
    stray.write_text('#import "/commands.typ": *\n\nfremd\n', encoding="utf-8")
    broken = _file(here, "cu", "second-probe")
    broken.write_text(_text(broken) + "// woodcore:shared never-closed\n", encoding="utf-8", newline="")
    entry = here.document_typ("rs")
    entry.write_text(_text(entry) + "\n= Anhang\n", encoding="utf-8", newline="")
    snap = _snapshot(here)
    for code, args in (
        ("bad_mode", ("xx", PROBE, "bp")),
        ("bad_mode", ("cu", PROBE, "xx")),
        ("no_targets", ("cu", PROBE, [])),
        ("same_document", ("cu", PROBE, ["cu", "bp"])),
        ("no_such_node", ("cu", "no-such-probe", "bp")),
        ("not_a_file", ("cu", "probes", "rs")),
        ("not_a_section", ("rs", "Statischer Rapport#1", "cu")),
        ("already_shared", ("cu", PROBE, "bp")),
        ("id_exists", ("cu", "taken-probe", "bp")),
        ("file_exists", ("cu", "taken-probe", "rs")),
        ("tags_unreadable", ("cu", "second-probe", "bp")),
    ):
        # file_exists: the report has no section taken-probe, but a file of that name is planted
        if code == "file_exists":
            _file(here, "rs", "taken-probe").write_text("fremd\n", encoding="utf-8")
            snap = _snapshot(here)
        _code(code, sharing.share, here, *args)
        assert _snapshot(here) == snap, f"a refusal ({code}) wrote"
    assert not _leftovers(here)


def test_a_document_the_project_lacks_is_refused():
    from fixtures import legacy_example
    legacy = legacy_example.build(conftest.tmpdir("share_legacy") / "p")
    first = next(n for n in structure.flatten(structure.tree(legacy, "rs")) if n.kind == "file")
    _code("no_such_document", sharing.share, legacy, "rs", first.id, "cu")
    _code("no_such_document", sharing.stop_sharing, legacy, "cu", "live-loads")


# --- the index, and what replaced the synchronising of phase 5 ----------------------------------------------------

def _three(name):
    here = _project(name)
    sharing.share(here, "cu", PROBE, ["bp", "rs"])
    return here


def test_writing_a_block_into_every_copy_is_gone():
    """The engineer's rework of 01.10.2026: a block edited in Woodcore is written into its own document's copy and the others see it incoming (calc/sync.py) -- the alert and the write into every copy of phase 5 are no more."""
    assert not hasattr(sharing, "plan_sync") and not hasattr(sharing, "apply_sync") and not hasattr(sharing, "SyncPlan")


def test_the_index_gives_every_copy_of_every_block_and_the_files_it_cannot_read():
    here = _three("sharing_index")
    found = sharing.index(here)
    assert [(c.mode, c.file) for c in found.copies[PROBE]] == [("cu", _file(here, "cu")), ("bp", _file(here, "bp")), ("rs", _file(here, "rs"))]
    assert [(c.mode, c.file) for c in sharing.copies(here, PROBE)] == [(c.mode, c.file) for c in found.copies[PROBE]]
    assert all(_text(f.path) == f.text for f in found.files if f.text is not None), "every section file read once, its text kept"
    bp = _file(here, "bp")
    bp.write_text(_text(bp) + "// woodcore:shared never-closed\n", encoding="utf-8", newline="")
    found = sharing.index(here)
    assert [c.mode for c in found.copies[PROBE]] == ["cu", "rs"], "a file whose tags cannot be read holds no copy"
    assert [(m, p) for m, p, _why in found.skipped[PROBE]] == [("bp", bp)] and "never-closed" in found.skipped
    # the records of files as an operation will make them stand for the disk
    records = [sharing._file(f.mode, f.path, f.text.replace("// woodcore:shared never-closed\n", "")) if f.path == bp else f for f in found.files]
    assert [c.mode for c in sharing.index(here, records).copies[PROBE]] == ["cu", "bp", "rs"]


def test_share_records_the_copies_in_step_on_both_sides():
    import sync
    here = _project("sharing_records")
    sharing.share(here, "cu", PROBE, "bp")
    for mode in ("cu", "bp"):
        assert sync.state_file(here, mode).is_file(), "share writes the synchronisation record of both sides"
        block = sync.status(here, mode).block(PROBE)
        assert block.state == "in_sync" and block.modes == ("cu", "bp")
    # a third document afterwards starts in step with the two
    sharing.share(here, "cu", PROBE, "rs")
    assert [sync.status(here, mode).block(PROBE).state for mode in ("cu", "bp", "rs")] == ["in_sync"] * 3


def test_a_shared_files_tags_take_its_own_line_ending_and_each_copy_says_its_own():
    here = _project("share_line_endings")
    source = _file(here, "cu")
    source.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))
    sharing.share(here, "cu", PROBE, ["bp", "rs"])
    cu, bp, rs = _file(here, "cu"), _file(here, "bp"), _file(here, "rs")
    assert b"\r\n" in cu.read_bytes() and cu.read_bytes().count(b"\n") == cu.read_bytes().count(b"\r\n"), "the tags added in the file's own line ending"
    # the base de projet's copy saved LF by an editor; the report's mixed: LF before its block, CRLF from the tag on
    bp.write_bytes(bp.read_bytes().replace(b"\r\n", b"\n"))
    raw = rs.read_bytes()
    at = raw.index(b"// woodcore:shared")
    rs.write_bytes(raw[:at].replace(b"\r\n", b"\n") + raw[at:])
    copies = {c.mode: c for c in sharing.copies(here, PROBE)}
    assert (copies["cu"].newline, copies["bp"].newline, copies["rs"].newline) == ("\r\n", "\n", "\r\n"), "the line ending of the opening tag's line"
    for mode, path in (("cu", cu), ("bp", bp), ("rs", rs)):
        assert _text(path)[copies[mode].start:copies[mode].end] == copies[mode].block_text


# --- stopping the sharing -------------------------------------------------------------------------------------------

def test_stop_sharing_between_two_copies_unshares_both():
    here = _project("stop_two")
    sharing.share(here, "cu", PROBE, "bp")
    cu, bp = _file(here, "cu"), _file(here, "bp")
    inside = _block_of(here, "bp").block_text
    result = sharing.stop_sharing(here, "bp", f"{PROBE}#2")
    assert result.file == bp and result.shared_ids == (PROBE,)
    assert result.also_unshared == (("cu", cu, PROBE),), "the one copy left shares with nobody, and says so"
    for path in (cu, bp):
        text = _text(path)
        assert "woodcore:shared" not in text and inside in text, "the tags off, what was between them kept"
        assert "// woodcore:object show-norm-list probe-use" in text, "the object's own tags stay"
    for mode in ("cu", "bp"):
        assert "shared_with" not in _leaf(here, mode, PROBE)[0]
        assert _node(here, mode, PROBE).shared_with == ()
    assert set(result.structures) == {here.structure_file("cu"), here.structure_file("bp")}
    assert sharing.copies(here, PROBE) == []
    import sync
    for mode in ("cu", "bp"):
        assert sync.status(here, mode).block(PROBE) is None
        assert f'"{PROBE}"' not in sync.state_file(here, mode).read_text(encoding="utf-8"), "the records of the copies unshared are dropped"
    snap = _snapshot(here)
    _code("not_shared", sharing.stop_sharing, here, "bp", PROBE)
    _code("not_a_file", sharing.stop_sharing, here, "cu", "probes")
    assert _snapshot(here) == snap


def test_stop_sharing_among_three_copies_leaves_the_other_two_shared():
    here = _three("stop_three")
    result = sharing.stop_sharing(here, "bp", PROBE)
    assert result.also_unshared == ()
    assert "woodcore:shared" not in _text(_file(here, "bp"))
    assert [c.mode for c in sharing.copies(here, PROBE)] == ["cu", "rs"]
    assert _leaf(here, "cu", PROBE)[0]["shared_with"] == ["rs"]
    assert "shared_with" not in _leaf(here, "bp", PROBE)[0]
    assert _node(here, "rs", PROBE).shared_with == ("cu",)
    assert not [d for d in sharing.reconcile(here, write=False).changes if d.id == PROBE]
    # the two left then stop too: the last one is unshared with it
    last = sharing.stop_sharing(here, "rs", PROBE)
    assert last.also_unshared == (("cu", _file(here, "cu"), PROBE),)
    assert sharing.copies(here, PROBE) == [] and "shared_with" not in _leaf(here, "cu", PROBE)[0]


# --- reconciling -----------------------------------------------------------------------------------------------

def test_reconcile_writes_back_what_the_tags_say():
    here = _project("reconcile")
    sharing.reconcile(here)                  # whatever the templates carry, settled first
    sharing.share(here, "cu", PROBE, "bp")
    bp = _file(here, "bp")
    tags = (f"// woodcore:shared {PROBE}\n", f"// woodcore:/shared {PROBE}\n")
    bp.write_text(_text(bp).replace(tags[0], "").replace(tags[1], ""), encoding="utf-8", newline="")
    look = sharing.reconcile(here, write=False)
    assert set(look.changes) == {sharing.Difference("cu", PROBE, ("bp",), ()), sharing.Difference("bp", PROBE, ("cu",), ())} and look.written == ()
    assert _leaf(here, "cu", PROBE)[0]["shared_with"] == ["bp"], "a look writes nothing"
    done = sharing.reconcile(here)
    assert set(done.changes) == set(look.changes) and set(done.written) == {here.structure_file("cu"), here.structure_file("bp")}
    assert "shared_with" not in _leaf(here, "cu", PROBE)[0] and "shared_with" not in _leaf(here, "bp", PROBE)[0]
    assert sharing.reconcile(here).changes == (), "a second pass finds nothing"
    # tags put on by hand, in the convention and in the report: shared from then on
    structure.add_section(here, "rs", None, None, "009-hand-probe", "Von Hand")
    for path in (_file(here, "cu"), _file(here, "rs", "009-hand-probe")):
        path.write_text(_text(path) + "// woodcore:shared hand-probe\nGemeinsam von Hand.\n// woodcore:/shared hand-probe\n", encoding="utf-8", newline="")
    assert sharing.reconcile(here).changes == (sharing.Difference("cu", PROBE, (), ("rs",)),)
    # a leaf whose tags cannot be read keeps what it said, and the result says why
    cu = _file(here, "cu")
    cu.write_text(_text(cu) + "// woodcore:shared never-closed\n", encoding="utf-8", newline="")
    unread = sharing.reconcile(here)
    assert unread.changes == () and any(PROBE in problem and "cannot be read" in problem for problem in unread.problems)
    assert _leaf(here, "cu", PROBE)[0]["shared_with"] == ["rs"]
