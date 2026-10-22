"""A project in three documents moved into the layout by folders (calc/project_migrate_folders.py, issue #64, spec 2026-10-15-structure-projet-dossiers REQ-012).

The example project as Woodcore laid out a project in three documents from 0.111 to 0.118 -- rebuilt from the committed one, which is laid out by folders since this migration, by moving it back (`_legacy_copy`) -- moved by the very command the engineer runs, proved against its own documents compiled before, and undone on request byte for byte; a failure in the middle undoes everything; and what stands in the way is refused by name before anything moves.
"""

import json
import os
import shutil
import stat
import subprocess
import sys

import conftest
from conftest import CALC

import project
import project_migrate as pm
import project_migrate_folders as folders


def _writable(function, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    function(path)


def _legacy_copy(name):
    """A copy of the example project laid out in three documents as 0.111 to 0.118 laid them out, rebuilt from the committed one by tests/fixtures/legacy_three.py."""
    from fixtures import legacy_three
    return legacy_three.build(conftest.tmpdir(name) / "Exemple", conftest.SAMPLE)


def _files(root):
    """{path from `root`: bytes} of every file a project's documents are written from -- the outputs a compile or an engine update writes left out."""
    out = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if not path.is_file() or path.suffix == ".pdf" or "/stamps/" in "/" + rel or rel.startswith(("_woodcore/lib/", "_woodcore/calc/")) or rel == "_woodcore/VERSION":
            continue
        if rel.startswith(("_Archiv/", "000-Woodcore/archives/")):
            continue
        out[rel] = path.read_bytes()
    return out


def _codes(notes):
    return {note.code for note in notes}


def test_the_plan_of_the_example_moves_what_the_layout_by_folders_moves():
    here = _legacy_copy("mf_plan")
    p = folders.plan(here)
    assert not p.refusals, [str(r) for r in p.refusals]
    moved = {pm._rel(here.root, m.source): pm._rel(here.root, m.target) for m in p.moves}
    assert moved["config.typ"] == "000-Typst-Config/config.typ" and moved["commands.typ"] == "000-Typst-Config/commands.typ"
    assert moved["_woodcore"] == "000-Woodcore" and moved["Woodcore-Datei"] == "000-Woodcore/sources"
    assert moved["1_Nutzungsvereinbarung"] == "100-Service criteria agreement" and moved["3_Statischer Bericht"] == "300-Statical report"
    assert moved["Woodcore-Datei/positions.json"] == "Positions/positions.json"
    assert moved["Formules/ZT-01.typ"] == "Timber-checks/Tension/ZT-01.typ" and moved["Formules"] == "Domains"
    order = [pm._rel(here.root, m.source) for m in p.moves]
    assert order.index("Woodcore-Datei/positions.json") < order.index("Woodcore-Datei") and order.index("Formules/ZT-01.typ") < order.index("Formules"), "a file is taken out of its folder before the folder moves"
    changes = {(c.old, c.new) for r in p.rewrites for c in r.changes}
    assert ("/commands.typ", "/000-Typst-Config/commands.typ") in changes
    assert p.layout["config"] == "000-Typst-Config" and json.loads(p.woodcore_text)["schema_version"] == "1.1"
    assert not (here.root / "000-Typst-Config").exists(), "a plan writes nothing"


def test_what_stands_in_the_way_is_refused_by_name():
    here = _legacy_copy("mf_refused")
    (here.root / "000-Woodcore").mkdir()
    assert "collision" in _codes(folders.plan(here).refusals)
    alone = project.write(conftest.tmpdir("mf_alone") / "A.woodcore", "A")
    assert _codes(folders.plan(alone).refusals) == {"not_three_documents"}
    import documents
    done = project.write(conftest.tmpdir("mf_done") / "D.woodcore", "D", documents.layout_for("de"))
    assert _codes(folders.plan(done).refusals) == {"already_folders"}


def test_the_example_is_migrated_by_the_command_proved_and_undone_on_request():
    """REQ-012's criterion: the example migrated by `woodcore-cli migrate`, its three documents printing what they printed, then `--rollback` giving back every byte the documents are written from."""
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    here = _legacy_copy("mf_run")
    before = _files(here.root)
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env.pop(project.ENV, None)
    run = subprocess.run([sys.executable, str(CALC / "cli.py"), "migrate", "--project", str(here.file), "--skip-data", "--update-engine"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    migrated = project.Project.load(here.file)
    assert migrated.has_folders and json.loads(here.file.read_text(encoding="utf-8"))["schema_version"] == "1.1"
    assert (here.root / "Timber-checks" / "Tension" / "ZT-01.typ").is_file() and (here.root / "Positions" / "Positions.xlsx").is_file()
    assert all(path.is_dir() for path in migrated.structure_folders())
    assert not (here.root / "_woodcore").exists() and not (here.root / "Formules").exists() and not (here.root / "1_Nutzungsvereinbarung").exists()
    workspaces = sorted(migrated.archives_dir.glob(folders.WORKSPACE_PREFIX + "*"))
    assert len(workspaces) == 1 and json.loads((workspaces[0] / pm.RESULT_FILE).read_text(encoding="utf-8"))["ok"]
    rollback = subprocess.run([sys.executable, str(CALC / "cli.py"), "migrate", "--project", str(here.file), "--rollback", str(workspaces[0])],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert rollback.returncode == 0, rollback.stdout + rollback.stderr
    after = _files(here.root)
    assert after == before, sorted(set(after) ^ set(before)) or [k for k in after if after[k] != before.get(k)][:5]


def test_a_failure_in_the_proof_undoes_everything():
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    here = _legacy_copy("mf_fail")
    before = _files(here.root)
    real = folders._verify
    folders._verify = lambda *args, **kwargs: ["planted: the report prints otherwise"]
    try:
        folders.run(here, skip_data=True, update_engine=True, log=None, archive=False)
    except pm.MigrationError as exc:
        assert exc.code == "failed" and "planted" in str(exc), exc
    else:
        raise AssertionError("a migration whose proof failed went through")
    finally:
        folders._verify = real
    assert _files(here.root) == before, "a failed migration left the project changed"
    assert not project.Project.load(here.file).has_folders
    kept = sorted((here.root / "_Archiv").glob(folders.WORKSPACE_PREFIX + "*"))
    assert len(kept) == 1 and json.loads((kept[0] / pm.RESULT_FILE).read_text(encoding="utf-8"))["rolled_back"]


def test_a_rollback_sets_aside_the_figures_the_proof_s_export_wrote_and_the_records_adopted_get_their_bytes_back():
    """Lot 2 (issue #64): the proof's export writes figures into the tabs' Exports/Figures/, which a rollback sets aside into the workspace (`figure_folders`), never deleting them, and the folders it made go with them; a record the migration rewrote to name a copy (plan_documents.adopt, annex.adopt) gets its bytes back from before.zip, and the copy it made is set aside."""
    root = conftest.tmpdir("mf_undo_figures") / "P"
    ws = root / ".woodcore-migration-folders-x"
    ws.mkdir(parents=True)
    figure = root / "Statics" / "Exports" / "Figures" / "M-de.svg"
    figure.parent.mkdir(parents=True)
    figure.write_text("<svg/>", encoding="utf-8")
    copy = root / "Appendix" / "rapport.pdf"
    copy.parent.mkdir(parents=True)
    copy.write_bytes(b"%PDF-1.7")
    record_file = root / "000-Woodcore" / "sources" / "annexes" / "sources" / "R.json"
    record_file.parent.mkdir(parents=True)
    record_file.write_text('{"schema_version": "1.1", "file": "rapport.pdf"}\n', encoding="utf-8")
    before = b'{"schema_version": "1.0"}\n'
    import zipfile
    with zipfile.ZipFile(ws / pm.BACKUP_FILE, "x") as z:
        z.writestr("000-Woodcore/sources/annexes/sources/R.json", before)
    record = {"created": ["Appendix/rapport.pdf"], "moves": [], "project": "P.woodcore",
              "rewritten": [{"file": "000-Woodcore/sources/annexes/sources/R.json", "from": "000-Woodcore/sources/annexes/sources/R.json", "state": "done", "sha256_after": pm._sha_file(record_file)}],
              "made_folders": ["Statics", "Statics/Exports", "Statics/Exports/Figures", "Appendix"],
              "figure_folders": ["Statics/Exports/Figures"],
              "generated_before": "000-Woodcore", "generated_after": "000-Woodcore", "archives_before": "000-Woodcore/archives", "archives_after": "000-Woodcore/archives"}
    assert folders._undo(ws, record, None) == []
    assert not (root / "Statics").exists() and not (root / "Appendix").exists(), "the folders made, emptied, are taken away"
    assert (ws / pm.ROLLED_BACK_DIR / "export" / "Statics" / "Exports" / "Figures" / "M-de.svg").is_file(), "a figure is set aside, never deleted"
    assert (ws / pm.ROLLED_BACK_DIR / "Appendix" / "rapport.pdf").is_file()
    assert record_file.read_bytes() == before
