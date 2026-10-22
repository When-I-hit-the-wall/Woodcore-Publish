"""The lists Woodcore writes once in raw Typst, each cell a `#sync` (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-017, UI-003, Q-008; calc/domains/list_files.py): the journal, the list of the positions, the quantities."""

TIER = "fast"  # tests/run_tests.py --fast

import json
import subprocess

import conftest
from conftest import Skip
import documents
import project
import typst_sync
from domains import list_files


def _copy(name):
    import shutil
    here = conftest.project_copy(name)
    shutil.copytree(conftest.PROJECT.config_dir, here.config_dir, dirs_exist_ok=True)
    project.sync_engine(here)
    return here


def test_each_list_is_written_once_compiles_and_holds_no_stale_cell():
    """Q-008: the journal, the list of the positions and the quantities are written, each a `#table` whose every cell is a `#sync` of its data, closed by its label; the export's check finds no cell that differs; a second `write` is refused -- the file is the engineer's; in a new project, exported, the three compile in its report."""
    here = _copy("lists_written")
    for kind in list_files.KINDS:
        list_files.path(here, kind).unlink(missing_ok=True)   # the example's own, written at its creation (export_all.seed): written again here
        target = list_files.write(here, kind)
        text = target.read_text(encoding="utf-8")
        assert text.rstrip().endswith(list_files.label(kind)) and "#sync(" in text, text[:300]
        assert list_files.missing(here, kind) == [], kind
        try:
            list_files.write(here, kind)
            raise AssertionError("a list already there is written over")
        except list_files.ListError as exc:
            assert "yours" in str(exc)
    assert typst_sync.check(here) == [], "a cell written from the data differs from it"
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import export_all
    import project_template
    fresh = project_template.create(conftest.tmpdir("lists_compiled") / "Halle", "Halle")
    with project.using(fresh):
        export_all.run()
    # the journal is the new project's already, written by export_all.seed and included by the report's journal section: the two other lists written and included here
    assert list_files.path(fresh, "journal").is_file()
    includes = [f'#include "{fresh.from_root(list_files.write(fresh, kind))}"' for kind in list_files.KINDS if kind != "journal"]
    probe = fresh.document_dir("rs") / "Sections" / "990-lists.typ"
    probe.write_text(documents.import_line(fresh) + "\n" + "\n".join(includes) + "\n", encoding="utf-8")
    entry = fresh.report_typ
    entry.write_text(entry.read_text(encoding="utf-8") + '\n#include "Sections/990-lists.typ"\n', encoding="utf-8")
    run = subprocess.run([project.typst_executable(), *documents.compile_args(fresh, "rs")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr[-2000:]


def test_a_cell_the_data_no_longer_says_is_warned_and_a_new_row_is_added_before_the_end():
    """ARCH-010, Q-008: a position whose type changed in the export is said at its file, line and id, nothing rewritten; a position added is proposed by `missing` and written by «Ajouter» before the table's end, every other byte of the file kept; a table whose label is gone is refused naming it."""
    here = _copy("lists_added")
    target = list_files.write(here, "position-list")
    position = here.data_dir / "positions" / "T001.json"
    record = json.loads(position.read_text(encoding="utf-8"))
    record["type"] = "Pfette"
    position.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    stale = [(here.rel(f), ident) for f, _line, ident, _content, _value in typst_sync.check(here)]
    assert (here.rel(target), "position/T001/type") in stale, stale
    assert "Pfette" not in target.read_text(encoding="utf-8"), "a warning rewrites nothing"
    index_path = here.data_dir / "positions-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    (here.data_dir / "positions" / "T099.json").write_text(json.dumps(dict(record, position="T099", description="neu"), ensure_ascii=False), encoding="utf-8")
    index["positions"].append("T099")
    index_path.write_text(json.dumps(index), encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    assert list_files.missing(here, "position-list") == ["T099"]
    assert list_files.add(here, "position-list") == ["T099"]
    after = target.read_text(encoding="utf-8")
    head, tail = before.rsplit(")) <position-list>", 1)
    assert after.startswith(head) and after.endswith(")) <position-list>" + tail) and '#sync("position/T099/id")[T099]' in after
    assert list_files.missing(here, "position-list") == [] and list_files.add(here, "position-list") == []
    target.write_text(after.replace("<position-list>", ""), encoding="utf-8")
    index["positions"].append("T098")
    (here.data_dir / "positions" / "T098.json").write_text(json.dumps(dict(record, position="T098")), encoding="utf-8")
    index_path.write_text(json.dumps(index), encoding="utf-8")
    try:
        list_files.add(here, "position-list")
        raise AssertionError("a table without its label is added to")
    except list_files.ListError as exc:
        assert "<position-list>" in str(exc)


def test_the_cells_ids_name_what_the_export_holds():
    """The ids are `domain/instance/variable`, read by `typst_sync.held` from the lists: a revision of a document's own journal, a position's field, a quantity of a material and section with a slash escaped."""
    here = conftest.PROJECT
    lists = list_files.sync_records(here)
    assert typst_sync.held({}, "position/T001/strength_class", lists)["value"] == "C24"
    assert typst_sync.held({}, "journal/1/index", lists)["value"] == 1
    quantity = next(i for i in lists["quantities"] if "/" in i)
    ident = typst_sync.make_id("quantities", quantity, "pieces")
    assert typst_sync.split_id(ident)[1] == quantity and typst_sync.held({}, ident, lists) is not None
