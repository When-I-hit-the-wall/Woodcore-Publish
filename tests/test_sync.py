"""Keeping what the three documents share in step, one document at a time (calc/sync.py, the rework of 01.10.2026).

What is held here: an edit made outside Woodcore -- the file written as VS Code writes it -- showing **local** in its document and **incoming** in the others, and «Importer les modifications» bringing both back in step; both copies edited being a **conflict**, refused without a choice of version and taken with one («theirs», «mine», a document's name); «Ignorer» never importing, surviving a new reading, and «Réactiver» showing what is incoming again; an object changed inside a block showing **that object alone** incoming, and an object-level import rewriting that object's two tag lines and what lies between and **not one byte else**; an object added or taken out elsewhere imported where it stands; text outside the tags never touched; CRLF and LF kept; an import **all or nothing** when a write fails halfway; a project never synchronised before starting in step where its copies are equal and in conflict where they differ, and a Woodcore edit recorded as local there and not as a conflict; three documents -- one importing and staying local towards the third, two offering different versions and the newest taken; `share` and `stop_sharing` keeping the records; a record that cannot be read never rewritten; the record's own form; and what `status` costs on the full templates of the convention and the base de projet.

Every project is made here, in this process's own temporary folder (conftest.tmpdir), by project_template.create, and the sections a check synchronises are made by structure.add_section and shared by sharing.share: the checks do not depend on what the content templates hold, but for the one that times them.
"""

import json
import os
import time
from pathlib import Path

import conftest

import project_template
import sharing
import structure
import sync
import typst_paths
import validation

TITLES = {"fr": "Sondes", "de": "Sonden", "en": "Probes"}
PROBE = "sync-probe"
# The section's body after its heading: words, two parametric objects -- lists of norms with free lines, the one parametric command left (spec 2026-10-21-commandes-typst-refonte, REQ-019) -- and words again -- the text of the block around its objects, and two objects compared by id.
BODY = (
    "Einleitung im gemeinsamen Block.\n"
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
    "// woodcore:object show-norm-list probe-area\n"
    "#show-norm-list(\n"
    "  keys: (\n"
    "    [Fläche],\n"
    "    [120],\n"
    "  ),\n"
    ")\n"
    "// woodcore:/object probe-area\n"
    "\n"
    "Schluss im gemeinsamen Block.\n"
)
USE = "probe-use"
AREA = "probe-area"


def _project(name, targets=("bp",)):
    """A new project of three documents, a group `probes` in the convention and the base de projet, a section `sync-probe` in the convention holding BODY, shared into `targets`."""
    here = project_template.create(conftest.tmpdir(name) / "Halle", "Halle")
    for mode in ("cu", "bp"):
        structure.add_group(here, mode, None, None, "probes", TITLES)
    structure.add_section(here, "cu", "probes", None, PROBE, "Sondenabschnitt")
    path = _file(here, "cu")
    path.write_bytes(path.read_bytes() + BODY.encode("utf-8"))
    if targets:
        sharing.share(here, "cu", PROBE, list(targets))
    return here


def _file(here, mode, name=PROBE):
    return here.document_dir(mode) / "Sections" / f"{name}.typ"


def _text(path):
    return typst_paths.read_text(path)


def _write(path, text):
    """`text` written as an editor of the engineer's writes it -- in place, the line endings as given."""
    Path(path).write_bytes(text.encode("utf-8"))


def _edit(here, mode, old, new, name=PROBE):
    """A VS Code edit of document `mode`'s copy: `old` replaced by `new`, once."""
    path = _file(here, mode, name)
    text = _text(path)
    assert text.count(old) == 1, f"{mode}: {old!r} is not in the copy once"
    _write(path, text.replace(old, new))
    return path


def _block(here, mode, name=PROBE, shared_id=PROBE):
    [copy] = [c for c in sharing.copies(here, shared_id) if c.mode == mode and c.file.name == f"{name}.typ"]
    return copy


def _status(here, mode, item=PROBE, settle=True):
    found = sync.status(here, mode, settle=settle).item(item)
    assert found is not None, f"{mode}: no item {item!r}"
    return found


def _states(here, item=PROBE, modes=("cu", "bp")):
    return tuple(_status(here, mode, item).state for mode in modes)


def _snapshot(here):
    """{path from the project's folder: bytes} of every file of the project but the engine and the export: what a refusal must leave as it was."""
    root = here.root
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and "_woodcore" not in p.relative_to(root).parts}


def _leftovers(here):
    return [p for p in here.root.rglob("*") if p.is_file() and p.suffix in (".tmp", ".part")]


def _code(code, what, *args, **kwargs):
    """`what(*args, **kwargs)` refuses with `code`: a SyncError, its code and an English sentence."""
    try:
        what(*args, **kwargs)
    except sync.SyncError as exc:
        assert exc.code == code, f"refused with {exc.code!r}, not {code!r}: {exc}"
        assert exc.code in sync.CODES and str(exc), "a refusal says something, by a code of CODES"
        return exc
    raise AssertionError(f"{getattr(what, '__name__', what)}{args} was not refused with {code!r}")


def _outside(here, mode, name=PROBE, shared_id=PROBE):
    """(what lies before a copy's block, what lies after it) in its file."""
    copy = _block(here, mode, name, shared_id)
    text = _text(copy.file)
    return text[:copy.start], text[copy.end:]


def _object_lines(text, object_id):
    """(lines before the object's start tag, the object's lines, lines after its end tag) of a file's text, line endings kept."""
    lines = sync._lines(text)
    start = next(i for i, line in enumerate(lines) if line.rstrip("\r\n") == f"// woodcore:object show-norm-list {object_id}")
    end = next(i for i, line in enumerate(lines) if line.rstrip("\r\n") == f"// woodcore:/object {object_id}")
    return "".join(lines[:start]), "".join(lines[start:end + 1]), "".join(lines[end + 1:])


# --- the codes, the states and the record ------------------------------------------------------------------------

def test_the_codes_states_and_the_error():
    assert len(sync.CODES) == len(set(sync.CODES)) and len(sync.PROBLEMS) == len(set(sync.PROBLEMS))
    assert sync.STATES == ("in_sync", "ignored", "local", "incoming", "conflict", "problem"), "the order of severity a file and a block show the worst of"
    exc = sync.SyncError("plain", "needs_choice", items=["x"])
    assert isinstance(exc, sharing.SharingError) and isinstance(exc, structure.StructureError) and isinstance(exc, validation.ValidationError)
    assert (exc.code, exc.values, str(exc)) == ("needs_choice", {"items": ["x"]}, "plain")
    assert sync.item_key("live-loads") == "live-loads" and sync.item_key("live-loads", "table") == "live-loads/table"
    assert sync.split_key("live-loads/table") == ("live-loads", "table") and sync.split_key(("a", None)) == ("a", None)
    for bad in ("Live Loads", "a/", "a/b/c", "/b", 3):
        _code("bad_item", sync.split_key, bad)
    assert sync.digest("a\r\nb\r\n") == sync.digest("a\nb\n") and len(sync.digest("x")) == 16, "a hash does not see line endings"


def test_share_records_both_sides_in_step_and_the_record_is_canonical():
    here = _project("sync_share")
    for mode in ("cu", "bp"):
        block = _status(here, mode)
        assert (block.state, block.text_state, [o.state for o in block.objects]) == ("in_sync", "in_sync", ["in_sync", "in_sync"])
        assert block.modes == ("cu", "bp") and block.file == _file(here, mode) and block.rel == f"Sections/{PROBE}.typ"
        assert [o.id for o in block.objects] == [USE, AREA] and all(o.type == "show-norm-list" and o.present for o in block.objects)
        path = sync.state_file(here, mode)
        assert path == here.document_dir(mode) / "sync.json" and path.is_file(), "share writes the record of both sides"
        raw = path.read_bytes()
        assert b"\r" not in raw and raw.endswith(b"\n"), "LF, whatever the platform"
        data = json.loads(raw)
        assert (data["format"], data["schema_version"], data["document"]) == ("woodcore-sync", "1.0", mode)
        entry = data["blocks"][PROBE]
        assert len(entry["text"]) == 16 and set(entry["objects"]) == {USE, AREA} and "with" not in entry, "in step: a base, no relation standing apart from it"
        assert sync.dumps(mode, sync.check_source(data, mode)).encode("utf-8") == raw, "the record is written in its one form"
    assert not _leftovers(here)


def test_a_record_that_is_not_one_is_refused_by_name():
    for bad, words in (
        ({"schema_version": "1.0", "format": "woodcore-sync", "document": "bp", "blocks": {}, "x": 1}, "nothing else"),
        ({"schema_version": "1.0", "format": "woodcore-sync", "document": "cu", "blocks": {}}, "not of 'bp'"),
        ({"schema_version": "1.0", "format": "woodcore-sync", "document": "bp", "blocks": {"a": {"text": "xyz"}}}, "not a hash"),
        ({"schema_version": "1.0", "format": "woodcore-sync", "document": "bp", "blocks": {"a": {"objects": {}}}}, "beside a «text»"),
        ({"schema_version": "1.0", "format": "woodcore-sync", "document": "bp", "blocks": {"a": {"text": None, "with": {"bp": {}}}}}, "not another document"),
        ({"schema_version": "1.0", "format": "woodcore-sync", "document": "bp", "blocks": {"a": {"ignored_objects": ["x", "x"]}}}, "each once"),
    ):
        try:
            sync.check_source(bad, "bp")
        except ValueError as exc:
            assert words in str(exc), f"{exc} does not say {words!r}"
        else:
            raise AssertionError(f"{bad} was read")


# --- an edit outside Woodcore -----------------------------------------------------------------------------------

def test_an_edit_in_vscode_is_local_here_and_incoming_there_and_an_import_brings_them_in_step():
    here = _project("sync_vscode")
    bp = _file(here, "bp")
    _edit(here, "cu", "Einleitung im gemeinsamen Block.", "Neue Einleitung, in VS Code geschrieben.")
    cu_block, bp_block = _status(here, "cu"), _status(here, "bp")
    assert (cu_block.state, cu_block.text_state, cu_block.others) == ("local", "local", ("bp",)), "only this copy changed: the others will see it incoming"
    assert [o.state for o in cu_block.objects] == ["in_sync", "in_sync"], "the objects did not change"
    assert (bp_block.state, bp_block.text_state, bp_block.sources, bp_block.newest, bp_block.ambiguous) == ("incoming", "incoming", ("cu",), "cu", False)
    assert "Neue Einleitung" in bp_block.versions["cu"] and "Neue Einleitung" not in bp_block.versions["bp"], "each document's text, for a diff"
    status = sync.status(here, "bp")
    assert status.file(f"Sections/{PROBE}.typ").state == "incoming" and status.file(bp).state == "incoming", "a file shows the worst of its blocks"
    assert PROBE in status.incoming and status.conflicts == ()
    assert sync.status(here, "rs").block(PROBE) is None, "the report holds no copy"
    outside = _outside(here, "bp")
    result = sync.import_changes(here, "bp")
    assert result.imported == {PROBE: "cu"} and result.files == (bp,) and sync.state_file(here, "bp") in result.states
    assert _block(here, "bp").block_text == _block(here, "cu").block_text
    assert _outside(here, "bp") == outside, "only what lies between the tags changed"
    assert _states(here) == ("in_sync", "in_sync")
    again = sync.import_changes(here, "bp")
    assert (again.imported, again.files) == ({}, ()), "nothing left to import"
    assert not _leftovers(here)


def test_both_copies_edited_is_a_conflict_refused_without_a_choice_and_taken_with_one():
    here = _project("sync_conflict")
    _edit(here, "cu", "Schluss im gemeinsamen Block.", "Schluss aus der Nutzungsvereinbarung.")
    _edit(here, "bp", "Schluss im gemeinsamen Block.", "Schluss aus der Projektbasis.")
    assert _states(here) == ("conflict", "conflict")
    assert _status(here, "bp").text_state == "conflict" and _status(here, "bp").sources == ("cu",)
    snap = _snapshot(here)
    exc = _code("needs_choice", sync.import_changes, here, "bp", [PROBE])
    assert exc.values["items"] == [PROBE]
    assert _snapshot(here) == snap, "a refusal writes nothing"
    everything = sync.import_changes(here, "bp")
    assert (everything.imported, everything.conflicts, everything.files) == ({}, (PROBE,), ()), "everything incoming: a conflict waits for its choice"
    assert _snapshot(here) == snap
    _code("bad_choice", sync.import_changes, here, "bp", choices={PROBE: "rs"})
    _code("bad_choice", sync.import_changes, here, "bp", choices={PROBE: "bp"})
    _code("bad_choice", sync.import_changes, here, "bp", choices={PROBE: "yours"})
    result = sync.import_changes(here, "bp", choices={PROBE: "theirs"})
    assert result.imported == {PROBE: "cu"} and "Schluss aus der Nutzungsvereinbarung." in _text(_file(here, "bp"))
    assert _states(here) == ("in_sync", "in_sync")
    # a second round, «mine» in the base de projet: decided there, still a conflict in the convention
    _edit(here, "cu", "Schluss aus der Nutzungsvereinbarung.", "Zweiter Schluss NV.")
    _edit(here, "bp", "Schluss aus der Nutzungsvereinbarung.", "Zweiter Schluss PB.")
    kept = sync.import_changes(here, "bp", [PROBE], choices={PROBE: "mine"})
    assert kept.kept == (PROBE,) and kept.files == () and "Zweiter Schluss PB." in _text(_file(here, "bp"))
    assert _states(here) == ("conflict", "in_sync"), "the base de projet has seen the other version and kept its own"
    # the convention takes the base de projet's, by name
    sync.import_changes(here, "cu", choices={PROBE: "bp"})
    assert _states(here) == ("in_sync", "in_sync") and _block(here, "cu").block_text == _block(here, "bp").block_text
    # then the base de projet changes again: incoming in the convention, not a conflict
    _edit(here, "bp", "Zweiter Schluss PB.", "Dritter Schluss PB.")
    assert _states(here) == ("incoming", "local")


# --- ignoring ---------------------------------------------------------------------------------------------------

def test_an_ignored_object_is_never_imported_survives_a_new_reading_and_comes_back_on_reactivate():
    here = _project("sync_ignore")
    key = f"{PROBE}/{USE}"
    _edit(here, "cu", "[Büro],", "[Wohnen],")
    assert (_status(here, "bp", key).state, _status(here, "bp").state) == ("incoming", "incoming")
    result = sync.ignore(here, "bp", [key])
    assert result.changed == (key,)
    obj = _status(here, "bp", key)
    assert (obj.state, obj.underlying, obj.ignored) == ("ignored", "incoming", True)
    assert _status(here, "bp").state == "ignored" and _status(here, "bp").underlying == "incoming", "nothing else on offer: the block shows the ignored object"
    before = _file(here, "bp").read_bytes()
    assert sync.import_changes(here, "bp").imported == {} and _file(here, "bp").read_bytes() == before, "never imported"
    _code("ignored", sync.import_changes, here, "bp", [key])
    assert json.loads(sync.state_file(here, "bp").read_bytes())["blocks"][PROBE]["ignored_objects"] == [USE], "remembered in the document's record"
    # a later change of the other object is still on offer
    _edit(here, "cu", "[120],", "[140],")
    assert _status(here, "bp", f"{PROBE}/{AREA}").state == "incoming" and _status(here, "bp").state == "incoming"
    sync.import_changes(here, "bp")
    assert "[140]" in _text(_file(here, "bp")) and "[Büro]" in _text(_file(here, "bp"))
    assert _status(here, "bp", key).state == "ignored", "a new reading, the flag still there"
    assert sync.ignore(here, "bp", [key]).changed == (), "ignoring twice changes nothing"
    back = sync.reactivate(here, "bp", [key])
    assert back.changed == (key,) and _status(here, "bp", key).state == "incoming"
    sync.import_changes(here, "bp", [key])
    assert _states(here) == ("in_sync", "in_sync")
    # the whole block, ignored and reactivated
    _edit(here, "cu", "Schluss im gemeinsamen Block.", "Schluss, ignoriert.")
    sync.ignore(here, "bp", PROBE)
    block = _status(here, "bp")
    assert (block.state, block.underlying, block.ignored, block.text_state) == ("ignored", "incoming", True, "ignored")
    assert sync.import_changes(here, "bp").imported == {}
    _code("ignored", sync.import_changes, here, "bp", [PROBE])
    sync.reactivate(here, "bp", PROBE)
    assert _status(here, "bp").state == "incoming"
    _code("no_such_item", sync.ignore, here, "bp", "no-such-block")
    _code("no_such_item", sync.ignore, here, "bp", f"{PROBE}/no-such-object")
    _code("bad_item", sync.ignore, here, "bp", "Kein Id")


# --- objects ----------------------------------------------------------------------------------------------------

def test_an_object_changed_inside_a_block_is_that_object_alone_and_its_import_touches_it_alone():
    here = _project("sync_object")
    _edit(here, "cu", "[120],", "[140],")
    # the base de projet writes its own words around the objects meanwhile: its text is local
    _edit(here, "bp", "Einleitung im gemeinsamen Block.", "Einleitung der Projektbasis.")
    block = _status(here, "bp")
    assert (block.state, block.text_state) == ("incoming", "local")
    assert [(o.id, o.state) for o in block.objects] == [(USE, "in_sync"), (AREA, "incoming")]
    assert block.object(AREA).sources == ("cu",) and block.object(AREA).others == ("cu",)
    path = _file(here, "bp")
    head, _old, tail = _object_lines(_text(path), AREA)
    result = sync.import_changes(here, "bp", [f"{PROBE}/{AREA}"])
    assert result.imported == {f"{PROBE}/{AREA}": "cu"}
    new_head, new_object, new_tail = _object_lines(_text(path), AREA)
    assert (new_head, new_tail) == (head, tail), "not one byte outside the object's two tags and what lies between"
    assert "[140]," in new_object
    block = _status(here, "bp")
    assert (block.state, block.text_state, block.object(AREA).state) == ("local", "local", "in_sync"), "the words around stay this document's own"
    assert _status(here, "cu").text_state == "incoming"


def test_an_object_added_or_taken_out_elsewhere_is_imported_where_it_stands():
    here = _project("sync_object_added")
    new_object = (
        "\n"
        "// woodcore:object show-norm-list probe-height\n"
        "#show-norm-list(\n"
        "  keys: (\n"
        "    [Höhe],\n"
        "  ),\n"
        ")\n"
        "// woodcore:/object probe-height\n"
    )
    _edit(here, "cu", "// woodcore:/object probe-use\n", "// woodcore:/object probe-use\n" + new_object)
    block = _status(here, "bp")
    height = block.object("probe-height")
    assert (height.state, height.present, block.text_state) == ("incoming", False, "incoming"), "a new object, and the place it takes in the text"
    sync.import_changes(here, "bp", [f"{PROBE}/probe-height"])
    assert _block(here, "bp").block_text == _block(here, "cu").block_text, "put after the object it follows there, separated as it is there"
    assert _states(here) == ("in_sync", "in_sync")
    # taken out in the base de projet: incoming in the convention, its import takes it out
    path = _edit(here, "bp", new_object, "")
    assert _status(here, "cu", f"{PROBE}/probe-height").state == "incoming" and not _status(here, "bp", f"{PROBE}/probe-height").present
    sync.import_changes(here, "cu", [f"{PROBE}/probe-height"])
    assert "probe-height" not in _text(_file(here, "cu")) and _states(here) == ("in_sync", "in_sync"), "taken out with what parted it from the object before"
    assert structure.check_tags(_text(path)) == []
    # an object added together with other words: the object imported alone leaves the words incoming -- never a conflict of this document's making
    _edit(here, "cu", "// woodcore:/object probe-use\n", "// woodcore:/object probe-use\n" + new_object)
    _edit(here, "cu", "Schluss im gemeinsamen Block.", "Schluss mit neuer Höhe.")
    sync.import_changes(here, "bp", [f"{PROBE}/probe-height"])
    block = _status(here, "bp")
    assert (block.text_state, block.object("probe-height").state, block.state) == ("incoming", "in_sync", "incoming")
    sync.import_changes(here, "bp")
    assert _states(here) == ("in_sync", "in_sync") and _block(here, "bp").block_text == _block(here, "cu").block_text


def test_a_whole_block_import_keeps_this_documents_own_changes_to_other_objects():
    here = _project("sync_merge")
    _edit(here, "cu", "[120],", "[140],")            # the convention changes the area
    _edit(here, "bp", "[Büro],", "[Labor],")          # the base de projet the use
    block = _status(here, "bp")
    assert [(o.id, o.state) for o in block.objects] == [(USE, "local"), (AREA, "incoming")] and block.text_state == "in_sync"
    sync.import_changes(here, "bp", [PROBE])
    text = _text(_file(here, "bp"))
    assert "[140]," in text and "[Labor]," in text, "what is incoming taken, what is this document's own kept"
    assert _status(here, "bp").state == "local" and _status(here, "cu", f"{PROBE}/{USE}").state == "incoming"


# --- what is never touched --------------------------------------------------------------------------------------

def test_text_outside_the_tags_is_never_touched():
    here = _project("sync_outside")
    tag, end = f"// woodcore:shared {PROBE}\n", f"// woodcore:/shared {PROBE}\n"
    _edit(here, "bp", tag, "Nur in der Projektbasis.\n\n" + tag)
    _edit(here, "bp", end, end + "\nNach dem Block, nur hier.\n")
    _edit(here, "cu", "Einleitung im gemeinsamen Block.", "Andere Einleitung.")
    assert _status(here, "bp").state == "incoming", "what lies outside the tags is no difference"
    outside = _outside(here, "bp")
    sync.import_changes(here, "bp")
    assert _outside(here, "bp") == outside
    text = _text(_file(here, "bp"))
    assert "Nur in der Projektbasis.\n\n" + tag in text and text.endswith(end + "\nNach dem Block, nur hier.\n") and "Andere Einleitung." in text


def test_crlf_and_lf_copies_keep_their_line_endings():
    here = _project("sync_line_endings")
    bp = _file(here, "bp")
    bp.write_bytes(bp.read_bytes().replace(b"\n", b"\r\n"))
    assert _states(here) == ("in_sync", "in_sync"), "line endings are no difference"
    _edit(here, "cu", "Einleitung im gemeinsamen Block.", "LF-Einleitung.")
    _edit(here, "cu", "[120],", "[99],")
    outside = _outside(here, "bp")
    sync.import_changes(here, "bp", [f"{PROBE}/{AREA}"])
    raw = bp.read_bytes()
    assert raw.count(b"\n") == raw.count(b"\r\n") and b"[99]," in raw, "an object written into a CRLF file is CRLF"
    sync.import_changes(here, "bp")
    raw = bp.read_bytes()
    assert raw.count(b"\n") == raw.count(b"\r\n") and b"LF-Einleitung." in raw, "a block written into a CRLF file is CRLF"
    assert _outside(here, "bp") == outside
    assert b"\r" not in _file(here, "cu").read_bytes()
    assert _states(here) == ("in_sync", "in_sync")


def test_an_import_is_all_or_nothing_when_a_write_fails_halfway():
    here = _project("sync_failure")
    _edit(here, "cu", "Einleitung im gemeinsamen Block.", "Geänderte Einleitung.")
    snap = _snapshot(here)
    real, calls = sharing._put, []

    def failing(path, data):
        calls.append(Path(path))
        if len(calls) == 2:
            raise PermissionError(13, "held by another program", str(path))
        real(path, data)

    sharing._put = failing
    try:
        exc = _code("write_failed", sync.import_changes, here, "bp")
    finally:
        sharing._put = real
    assert "put back" in str(exc) and len(calls) >= 3, "the section file was written, and written back"
    assert _snapshot(here) == snap, "every file is what it was: the section and both records"
    assert not _leftovers(here)
    sync.import_changes(here, "bp")
    assert _states(here) == ("in_sync", "in_sync")


# --- a project never synchronised, and Woodcore's own edits ------------------------------------------------------

def _forget(here):
    for mode in ("cu", "bp", "rs"):
        path = sync.state_file(here, mode)
        if path.exists():
            path.unlink()


def test_a_project_never_synchronised_starts_in_step_where_equal_and_in_conflict_where_not():
    here = _project("sync_first_time")
    _forget(here)
    assert _states(here, modes=("bp", "cu")) == ("in_sync", "in_sync")
    assert sync.state_file(here, "bp").is_file() and sync.state_file(here, "cu").is_file(), "the bases initialised from the copies"
    _edit(here, "bp", "Schluss im gemeinsamen Block.", "Schluss PB.")
    assert _states(here) == ("incoming", "local"), "once initialised, an edit is an edit"
    _forget(here)
    assert _states(here) == ("conflict", "conflict"), "no record: who changed is not known"
    assert [o.state for o in _status(here, "bp").objects] == ["in_sync", "in_sync"], "only what differs"
    # with settle=False nothing is written
    _forget(here)
    sync.status(here, "bp", settle=False)
    assert not sync.state_file(here, "bp").exists()


def test_a_woodcore_edit_is_local_here_and_incoming_there_even_on_a_project_never_synchronised():
    here = _project("sync_local")
    _forget(here)
    loaded = _block(here, "cu").block_text
    new = loaded.replace("Einleitung im gemeinsamen Block.", "Einleitung, in Woodcore geschrieben.")
    before_bp = _file(here, "bp").read_bytes()
    result = sync.write_local(here, "cu", PROBE, new, loaded)
    assert result.file == _file(here, "cu") and _block(here, "cu").block_text == new
    assert _file(here, "bp").read_bytes() == before_bp, "a Woodcore edit writes this document's copy alone"
    assert _states(here) == ("local", "incoming"), "not a conflict"
    _code("changed_meanwhile", sync.write_local, here, "cu", PROBE, new, loaded)
    _code("bad_block", sync.write_local, here, "cu", PROBE, "// woodcore:shared inner\nx\n// woodcore:/shared inner\n", new)
    _code("no_such_item", sync.write_local, here, "rs", PROBE, new, new)
    _code("bad_block", sync.write_local, here, "cu", PROBE, "// woodcore:object show-norm-list open\n#show-norm-list()\n", new)
    # an object id the copy uses outside the block, brought into it: the file's tags would no longer read
    cu = _file(here, "cu")
    _write(cu, _text(cu) + "\n// woodcore:object show-norm-list outside\n#show-norm-list()\n// woodcore:/object outside\n")
    snap = _snapshot(here)
    exc = _code("bad_block", sync.write_local, here, "cu", PROBE, new + "// woodcore:object show-norm-list outside\n#show-norm-list()\n// woodcore:/object outside\n", new)
    assert exc.values["file"] == str(cu) and _snapshot(here) == snap
    # a file written by the caller itself, then recorded
    _forget(here)
    sync.import_changes(here, "bp", choices={PROBE: "theirs"})
    _forget(here)
    loaded = _block(here, "bp").block_text
    _edit(here, "bp", "[Büro],", "[Archiv],")
    sync.record_local_edit(here, "bp", PROBE, before=loaded)
    assert _states(here) == ("incoming", "local")
    assert _status(here, "cu", f"{PROBE}/{USE}").state == "incoming" and _status(here, "cu").text_state == "in_sync"


# --- three documents --------------------------------------------------------------------------------------------

def test_three_documents_an_import_stays_local_towards_the_third_and_the_newest_version_is_taken():
    here = _project("sync_three", targets=("bp", "rs"))
    assert _states(here, modes=("cu", "bp", "rs")) == ("in_sync",) * 3
    _edit(here, "cu", "Einleitung im gemeinsamen Block.", "Einleitung NV.")
    assert _states(here, modes=("cu", "bp", "rs")) == ("local", "incoming", "incoming")
    sync.import_changes(here, "bp")
    bp = _status(here, "bp")
    assert (bp.state, bp.others) == ("local", ("rs",)), "in step with the convention, changed towards the report"
    rs = _status(here, "rs")
    assert rs.state == "incoming" and set(rs.sources) == {"cu", "bp"} and not rs.ambiguous, "two documents offer one version"
    sync.import_changes(here, "rs")
    assert _states(here, modes=("cu", "bp", "rs")) == ("in_sync",) * 3
    # two documents changed differently: the third is offered both, the newest first
    cu_path = _edit(here, "cu", "Einleitung NV.", "Einleitung NV, zweite.")
    bp_path = _edit(here, "bp", "Einleitung NV.", "Einleitung PB, zweite.")
    now = time.time()
    os.utime(cu_path, (now - 60, now - 60))
    os.utime(bp_path, (now, now))
    rs = _status(here, "rs")
    assert (rs.state, rs.sources, rs.newest, rs.ambiguous) == ("incoming", ("bp", "cu"), "bp", True)
    assert _states(here, modes=("cu", "bp")) == ("conflict", "conflict")
    sync.import_changes(here, "rs", choices={PROBE: "cu"})
    assert "Einleitung NV, zweite." in _text(_file(here, "rs")) and _status(here, "rs").state == "in_sync", "a document's version, by name; the other seen and set aside"
    sync.import_changes(here, "rs", choices={PROBE: "theirs"})
    assert "Einleitung NV, zweite." in _text(_file(here, "rs")), "nothing left on offer"
    os.utime(cu_path, (now + 60, now + 60))
    assert _status(here, "bp").newest == "cu"


def test_sharing_into_a_third_document_inherits_the_standing_of_the_source():
    here = _project("sync_third")
    _edit(here, "cu", "Einleitung im gemeinsamen Block.", "Einleitung NV, noch nicht übernommen.")
    sharing.share(here, "cu", PROBE, ["rs"])
    assert _states(here, modes=("cu", "bp", "rs")) == ("local", "incoming", "local"), "the report's copy is the convention's block: ahead of the base de projet as the convention is"
    rs = _status(here, "rs")
    assert rs.others == ("bp",) and rs.versions["rs"] == rs.versions["cu"]
    assert set(_status(here, "bp").sources) == {"cu", "rs"} and not _status(here, "bp").ambiguous
    assert _status(here, "cu").others == ("bp",), "in step with the copy made from it"
    _edit(here, "bp", "Einleitung im gemeinsamen Block.", "Einleitung PB.")
    assert _status(here, "rs").state == "conflict", "the report stands with the base de projet as the convention does"


# --- sharing and stopping ----------------------------------------------------------------------------------------

def test_stop_sharing_drops_the_records_of_the_copies_it_unshares():
    here = _project("sync_stop")
    sync.ignore(here, "bp", f"{PROBE}/{USE}")
    sharing.stop_sharing(here, "bp", PROBE)
    for mode in ("cu", "bp"):
        path = sync.state_file(here, mode)
        assert PROBE not in json.loads(path.read_bytes())["blocks"], f"{mode} keeps no record of a block it no longer shares"
        assert sync.status(here, mode).block(PROBE) is None


# --- what cannot be read ------------------------------------------------------------------------------------------

def test_a_record_that_cannot_be_read_is_said_and_never_rewritten():
    here = _project("sync_corrupt")
    path = sync.state_file(here, "bp")
    path.write_bytes(b"{ not json")
    _edit(here, "cu", "Einleitung im gemeinsamen Block.", "Andere Einleitung.")
    status = sync.status(here, "bp")
    assert any(p.code == "state_unreadable" for p in status.problems)
    assert status.block(PROBE).state == "conflict", "read as never synchronised"
    assert sync.status(here, "cu").block(PROBE).state == "local"
    assert path.read_bytes() == b"{ not json", "never rewritten, by its own document's reading or another's"
    _code("state_unreadable", sync.import_changes, here, "bp", choices={PROBE: "theirs"})
    _code("state_unreadable", sync.ignore, here, "bp", PROBE)
    assert path.read_bytes() == b"{ not json"


def test_a_copy_whose_tags_cannot_be_read_is_a_problem_and_left_out():
    here = _project("sync_unreadable", targets=("bp", "rs"))
    rs = _file(here, "rs")
    _write(rs, _text(rs) + "// woodcore:shared never-closed\n")
    status = sync.status(here, "rs")
    assert status.block(PROBE).state == "problem" and any(p.code == "unreadable_copy" for p in status.problems)
    _code("unreadable_copy", sync.import_changes, here, "rs", [PROBE])
    assert _status(here, "bp").modes == ("cu", "bp", "rs") and _status(here, "bp").state == "in_sync", "the others compare without it"


def test_the_refusals_of_the_documents_and_the_items():
    here = _project("sync_refusals")
    _code("bad_mode", sync.status, here, "xx")
    _code("bad_mode", sync.import_changes, here, "xx")
    _code("no_such_item", sync.import_changes, here, "bp", ["no-such-block"])
    _code("no_such_item", sync.import_changes, here, "rs", [PROBE])
    _code("no_such_item", sync.import_changes, here, "bp", [f"{PROBE}/no-such-object"])
    _code("bad_item", sync.import_changes, here, "bp", ["Kein Id"])
    _code("no_such_item", sync.import_changes, here, "bp", choices={"no-such-block": "mine"})
    unchanged = sync.import_changes(here, "bp", [f"{PROBE}/{USE}"])
    assert unchanged.unchanged == (f"{PROBE}/{USE}",) and unchanged.files == (), "asked for, nothing on offer"
    from fixtures import legacy_example
    legacy = legacy_example.build(conftest.tmpdir("sync_legacy") / "p")
    _code("no_such_document", sync.status, legacy, "cu")
    assert sync.status(legacy, "rs").blocks == (), "a report alone shares nothing"


# --- what it costs ------------------------------------------------------------------------------------------------

def test_status_on_the_full_templates_of_the_convention_and_the_base_de_projet():
    here = project_template.create(conftest.tmpdir("sync_cost") / "Halle", "Halle")
    started = time.perf_counter()
    first = sync.status(here, "bp")
    settled = time.perf_counter() - started
    started = time.perf_counter()
    second = sync.status(here, "bp")
    reading = time.perf_counter() - started
    started = time.perf_counter()
    sync.status(here, "cu", settle=False)
    pure = time.perf_counter() - started
    print(f"    status of the base de projet on the full templates: {len(first.blocks)} shared blocks, "
          f"{sum(len(b.objects) for b in first.blocks)} objects -- first reading {settled:.3f} s (records written), "
          f"next {reading:.3f} s, the convention without settling {pure:.3f} s")
    assert first.blocks, "the templates share blocks between the convention and the base de projet"
    assert all(b.state != "problem" for b in first.blocks), [b.shared_id for b in first.blocks if b.state == "problem"]
    assert [b.shared_id for b in first.blocks] == [b.shared_id for b in second.blocks]
    assert max(settled, reading, pure) < 5.0, "a reading is fast enough to colour the tree at every save"
