"""`woodcore-cli sync status|share|import|move` and what `check` says of sync.json (calc/cli_sync.py, docs/domain/documents.md §3.3octodecies; spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, REQ-33-01 to REQ-33-03, UI-33-01; issue #33).

Each command is run on a temporary copy of `tests/projet-exemple/`, in a process of its own as a terminal runs it, and the files it writes are compared **byte for byte** with what the domain function the window calls writes on a second copy: the CLI decides nothing, so the two must not differ by one byte. A conflict is refused without a choice and nothing is written; `status` and `check` write nothing; a sync.json that does not read stops `check` naming the file and the field.
"""

import json
import shutil
import subprocess
import sys

import conftest
from conftest import ROOT

import project
import sharing
import structure
import sync
import validation

SAMPLE = ROOT / "tests" / "projet-exemple" / "Exemple.woodcore"
CLI = ROOT / "calc" / "cli.py"


def _copy(name):
    """A copy of the example project, laid out as it is -- its three documents and their sections -- in this process's own temporary folder, **as the window leaves it once opened**: the example carries no sync.json, and the window's first reading settles the copies it finds equal (sync.status with `settle`), which writes each document's record. Without that an edit would show as a conflict, there being no record of who changed."""
    folder = conftest.tmpdir(name) / "projet"
    if folder.exists():
        shutil.rmtree(folder)
    shutil.copytree(SAMPLE.parent, folder, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv", "out"))
    file = folder / SAMPLE.name
    with project.using(file) as here:
        for mode in sync.SHARE_MODES:
            if mode in here.modes:
                sync.status(here, mode)
    return file


def _cli(file, *args, lang="en"):
    out = subprocess.run([sys.executable, str(CLI), *args, "--project", str(file), "--lang", lang] if args[0] == "sync" else [sys.executable, str(CLI), *args, "--project", str(file)],
                         capture_output=True, text=True, encoding="utf-8")
    return out.returncode, out.stdout, out.stderr


def _files(file):
    """{path from the project: bytes} of every sync.json, structure.json, entry and section file of the three documents -- what a share, an import or a move may write."""
    root = file.parent
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and (path.name in ("sync.json", "structure.json") or path.suffix == ".typ") and "_woodcore" not in path.parts:
            out[path.relative_to(root).as_posix()] = path.read_bytes()
    return out


def _domain(file, call):
    with project.using(file) as here:
        return call(here)


def _differences(a, b):
    fa, fb = _files(a), _files(b)
    return sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k))


def _edit_block(file, mode, shared_id, line):
    """The shared block `shared_id` of document `mode` given a line right after its opening tag -- an edit as VS Code writes it."""
    with project.using(file) as here:
        path = next(p for p in (here.document_dir(mode) / "Sections").glob("*.typ") if f"// woodcore:shared {shared_id}\n" in p.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace(f"// woodcore:shared {shared_id}\n", f"// woodcore:shared {shared_id}\n{line}\n", 1), encoding="utf-8")


# --- the contract: schemas/sync.schema.json ---------------------------------------------------------

def test_the_schema_is_the_contract_sync_py_reads_and_its_constants_are_sync_py_s():
    schema = json.loads((ROOT / "schemas" / "sync.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["const"] == sync.SCHEMA_VERSION
    assert schema["properties"]["format"]["const"] == sync.FORMAT
    assert tuple(schema["properties"]["document"]["enum"]) == tuple(sync.SHARE_MODES)
    assert set(schema["required"]) == {"schema_version", "format", "document", "blocks"}
    entry = schema["properties"]["blocks"]["patternProperties"][".*"]
    assert set(entry["properties"]) == set(sync._ENTRY_KEYS), "the schema's entry and sync._ENTRY_KEYS name the same keys"
    assert set(entry["properties"]["with"]["properties"]) == set(sync.SHARE_MODES)
    # every record the window writes for the example project reads, through the schema and then sync.py's own rules
    found = sorted(_copy("cli-sync-schema").parent.rglob("sync.json"))
    assert len(found) >= 2, found
    for path in found:
        record = json.loads(path.read_text(encoding="utf-8"))
        validation.validate_structure(record, "sync", path.name)
        sync.check_source(record, record["document"], path.name)


def test_a_malformed_record_is_refused_naming_the_file_and_the_field():
    good = {"schema_version": "1.0", "format": "woodcore-sync", "document": "cu", "blocks": {"intro": {"text": "0123456789abcdef"}}}
    sync.check_source(good, "cu", "sync.json")
    cases = [
        ({**good, "schema_version": "2.0"}, "sync.json.schema_version"),
        ({**good, "document": "xx"}, "sync.json.document"),
        ({**good, "blocks": {"intro": {"text": 12}}}, "sync.json.blocks.intro.text"),
        ({**good, "blocks": {"intro": {"text": "0123456789abcdef", "with": {"bp": {"text": {"own": "0123456789abcdef"}}}}}}, "sync.json.blocks.intro.with.bp.text"),
        ({**good, "blocks": {"intro": {"ignored": "yes"}}}, "sync.json.blocks.intro.ignored"),
        ({**good, "blocks": {"intro": {"text": "not-a-hash"}}}, "sync.json.blocks.intro.text"),
        ({**good, "blocks": {"intro": {"text": "0123456789abcdef", "colour": "red"}}}, "sync.json.blocks.intro"),
    ]
    for record, field in cases:
        try:
            sync.check_source(record, "cu", "sync.json")
        except ValueError as exc:
            assert field in str(exc), (field, str(exc))
        else:
            raise AssertionError(f"accepted: {record}")


def test_check_stops_on_a_record_that_does_not_read_naming_it_and_writes_nothing():
    file = _copy("cli-sync-check")
    before = _files(file)
    code, out, err = _cli(file, "check")
    assert code in (0, 1)   # what the dry export says of the example project is not this test's; what follows is
    record = file.parent / "2_Projektbasis" / "sync.json"
    data = json.loads(record.read_text(encoding="utf-8"))
    first = next(iter(data["blocks"]))
    data["blocks"][first]["text"] = 12
    record.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    with project.using(file) as here:
        import cli_sync
        said = []
        assert cli_sync.check(here, lang="en", out=said.append, err=said.append) == 1
    assert any("2_Projektbasis/sync.json" in s and f"blocks.{first}.text" in s for s in said), said
    assert _files(file) == {**before, "2_Projektbasis/sync.json": record.read_bytes()}, "check wrote something"


def test_check_names_the_blocks_a_document_is_out_of_step_on():
    """A document out of step is a warning naming its blocks, each with its state, and not a count alone (spec REQ-33-03)."""
    file = _copy("cli-sync-check-blocks")
    _edit_block(file, "bp", "accepted-risks", "Eine Zeile aus der Projektbasis.")
    before = _files(file)
    with project.using(file) as here:
        import cli_sync
        said = []
        assert cli_sync.check(here, lang="en", out=said.append, err=said.append) == 0, said
    assert any("accepted-risks (incoming change)" in s for s in said), said
    assert _files(file) == before, "check wrote something"


# --- the commands, against the domain functions the window calls ----------------------------------

def test_status_says_where_each_block_stands_in_three_languages_and_writes_nothing():
    file = _copy("cli-sync-status")
    _edit_block(file, "bp", "accepted-risks", "Eine Zeile aus der Projektbasis.")
    before = _files(file)
    for lang, word in (("en", "incoming change"), ("fr", "modification entrante"), ("de", "eingehende Änderung")):
        code, out, err = _cli(file, "sync", "status", "--document", "cu", lang=lang)
        assert code == 0, err
        assert "accepted-risks" in out and word in out, (lang, out)
    assert _files(file) == before, "status wrote something"


def test_share_writes_what_the_window_s_share_writes():
    a, b = _copy("cli-sync-share-a"), _copy("cli-sync-share-b")
    code, out, err = _cli(a, "sync", "share", "--document", "cu", "--section", "accepted-risks", "--to", "rs")
    assert code == 0, err
    _domain(b, lambda here: sharing.share(here, "cu", "accepted-risks", ["rs"]))
    assert not _differences(a, b), _differences(a, b)
    assert "accepted-risks" in out
    # refused: the same again, said with its code, nothing more written
    before = _files(a)
    code, _out, err = _cli(a, "sync", "share", "--document", "cu", "--section", "accepted-risks", "--to", "rs")
    assert code == 1 and "already_shared" in err, err
    assert _files(a) == before


def test_import_writes_what_the_window_s_import_writes():
    a, b = _copy("cli-sync-import-a"), _copy("cli-sync-import-b")
    for file in (a, b):
        _edit_block(file, "bp", "accepted-risks", "Eine Zeile aus der Projektbasis.")
    code, out, err = _cli(a, "sync", "import", "--document", "cu")
    assert code == 0, err
    _domain(b, lambda here: sync.import_changes(here, "cu"))
    assert not _differences(a, b), _differences(a, b)
    assert "Eine Zeile aus der Projektbasis." in (a.parent / "1_Nutzungsvereinbarung" / "Sections" / "accepted-risks.typ").read_text(encoding="utf-8")


def test_a_conflict_is_refused_without_a_choice_writing_nothing_and_taken_with_one():
    a, b = _copy("cli-sync-conflict-a"), _copy("cli-sync-conflict-b")
    for file in (a, b):
        _edit_block(file, "bp", "accepted-risks", "Fassung der Projektbasis.")
        _edit_block(file, "cu", "accepted-risks", "Fassung der Nutzungsvereinbarung.")
    before = _files(a)
    code, _out, err = _cli(a, "sync", "import", "--document", "cu")
    assert code == 1 and "accepted-risks" in err and "--choice" in err, err
    assert _files(a) == before, "a conflict without a choice wrote something"
    code, _out, err = _cli(a, "sync", "import", "--document", "cu", "--choice", "accepted-risks")
    assert code == 1 and "--choice" in err, "a choice without its value is refused"
    code, out, err = _cli(a, "sync", "import", "--document", "cu", "--choice-all", "theirs")
    assert code == 0, err
    _domain(b, lambda here: sync.import_changes(here, "cu", None, {c: "theirs" for c in sync.status(here, "cu", settle=False).conflicts}))
    assert not _differences(a, b), _differences(a, b)


def test_move_writes_what_the_window_s_move_writes():
    a, b = _copy("cli-sync-move-a"), _copy("cli-sync-move-b")
    with project.using(b) as here:
        tree = structure.tree(here, "cu")
        first = tree[0]
    code, out, err = _cli(a, "sync", "move", "--document", "cu", "--section", first.id, "--position", "1")
    assert code == 0, err
    _domain(b, lambda here: structure.move_node(here, "cu", first.id, None, 1))
    assert not _differences(a, b), _differences(a, b)


def test_the_words_are_in_three_languages_and_every_one_used_is_there():
    data = json.loads((ROOT / "calc" / "i18n" / "cli.json").read_text(encoding="utf-8"))
    keys = set(data["en"])
    for lang in ("fr", "de"):
        assert set(data[lang]) == keys, (lang, keys ^ set(data[lang]))
    import re
    used = set(re.findall(r'say\("([a-z_]+)"', (ROOT / "calc" / "cli_sync.py").read_text(encoding="utf-8")))
    used |= {"state_" + s for s in sync.STATES}
    assert used <= keys, used - keys
    assert "ß" not in json.dumps(data["de"], ensure_ascii=False), "Swiss German writes ss"
