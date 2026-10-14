"""The order the engineer gives the window's lists, and the «Formules» tab's folders -- `calc/list_order.py`, `Woodcore-Datei/lists.json` (issue #15, spec docs/requirements/completed/2026-10-08-onglet-formules-editeur-dossiers-include.md REQ-008, ARCH-001, ARCH-003, D-09, D-14, D-16).

Held: the file's place (beside the sources, never in the generated folder), its schema pinned and its refusals naming the field; an id it does not know last by id, one it no longer lists ignored; a drop placed above an entry, at the end of a folder, a hidden id keeping its slot; `groups` refused for a tab whose sources carry their own folder; a file that cannot be read said once, the lists then following the ids, the file left untouched and a drop refused; a project opened read only writes nothing; an id renamed, forgotten, inserted after another; nothing written where nothing changes; and the module Qt-free.
"""

import json
import subprocess
import sys

import conftest

import list_order
import project


def _copy(name):
    """A copy of the project with no lists.json of its own: the copy carries the one earlier tests of this process wrote (conftest.project_copy), and these tests start from none."""
    here = conftest.project_copy(name, data=False)
    here.lists_file.unlink(missing_ok=True)
    return here


def _store(here, said=None, read_only=False):
    return list_order.Store(lambda: here, lambda: read_only, warn=(said.append if said is not None else None))


def test_the_file_lies_beside_the_sources_never_in_the_generated_folder():
    here = project.current()
    assert here.lists_file == here.sources_dir / "lists.json"
    assert not str(here.lists_file.resolve()).startswith(str(here.generated_dir.resolve()))


def test_an_order_kept_is_applied_and_what_it_does_not_name_comes_last_by_id():
    entries = [{"id": i} for i in ("c", "a", "d", "b")]
    assert [e["id"] for e in list_order.ordered(entries, ["d", "gone", "b"])] == ["d", "b", "a", "c"]
    assert [e["id"] for e in list_order.ordered(entries, [])] == ["a", "b", "c", "d"]


def test_a_drop_lands_above_an_entry_or_at_the_end_of_its_folder_and_a_hidden_id_keeps_its_slot():
    groups = {"a": "", "b": "", "c": "F", "d": "F"}
    shown = ["c", "d", "a", "b"]
    # above an entry
    assert list_order.place([], shown, ["b"], groups.get, "", before="a") == ["c", "d", "b", "a"]
    # at the end of a folder: after its last entry shown
    assert list_order.place([], shown, ["a"], groups.get, "F", before=None) == ["c", "d", "a", "b"]
    # into a folder that shows nothing: at the end
    assert list_order.place([], shown, ["a"], groups.get, "G", before=None)[-1] == "a"
    # an id kept but hidden by a filter keeps its place between the others
    assert list_order.place(["c", "hidden", "d", "a", "b"], ["c", "d", "a", "b"], ["b"], groups.get, "", before="a") == ["c", "hidden", "d", "b", "a"]


def test_the_file_is_checked_and_its_refusals_name_the_field():
    data = list_order.empty()
    list_order.set_tab(data, "tab_schema", ["S-02", "S-01"])
    list_order.set_tab(data, "tab_formula", ["p1"], {"p1": "Toiture"})
    list_order.check(data)
    for broken, field in ((dict(data, schema_version="2.0"), "schema_version"), (dict(data, format="other"), "format"),
                          ({**data, "tabs": {"tab_schema": {"order": [1]}}}, "order")):
        try:
            list_order.check(broken)
        except list_order.ListOrderError as exc:
            assert field in str(exc), (field, str(exc))
        else:
            raise AssertionError(f"{field}: a malformed file was taken")
    # one folder, one place (D-16): a tab whose sources carry `group` keeps none here
    try:
        list_order.check({**data, "tabs": {"tab_schema": {"order": [], "groups": {"S-01": "Halle"}}}})
    except list_order.ListOrderError as exc:
        assert "tabs.tab_schema.groups" in str(exc)
    else:
        raise AssertionError("a schema's folder was kept in two places")
    # a tab left with nothing is not written
    assert "tab_x" not in list_order.set_tab(list_order.empty(), "tab_x", [])["tabs"]


def test_the_store_writes_reads_back_and_follows_an_id_renamed_forgotten_or_duplicated():
    here = _copy("list_order_store")
    store = _store(here)
    assert store.tab("tab_schema") == ([], {}) and not here.lists_file.exists()
    assert store.save("tab_schema", ["b", "a"])
    assert json.loads(here.lists_file.read_text(encoding="utf-8"))["tabs"]["tab_schema"] == {"order": ["b", "a"]}
    before = here.lists_file.stat().st_mtime_ns
    assert store.save("tab_schema", ["b", "a"]) and here.lists_file.stat().st_mtime_ns == before, "an unchanged order was written again"
    store.rename("tab_schema", "a", "z")
    assert store.tab("tab_schema")[0] == ["b", "z"]
    store.insert_after("tab_schema", "b2", "b")
    assert store.tab("tab_schema")[0] == ["b", "b2", "z"]
    store.forget("tab_schema", ["b"])
    assert store.tab("tab_schema")[0] == ["b2", "z"]
    # the folders of the «Formules» tab, here; another tab's never
    store.set_group("tab_formula", ["p1"], "Toiture")
    assert store.tab("tab_formula") == ([], {"p1": "Toiture"})
    store.rename("tab_formula", "p1", "p2")
    assert store.tab("tab_formula") == ([], {"p2": "Toiture"})
    store.save("tab_schema", ["z"], {"z": "Halle"})
    assert store.tab("tab_schema") == (["z"], {})


def test_a_file_that_cannot_be_read_is_said_once_left_as_it_is_and_refuses_a_drop():
    here = _copy("list_order_broken")
    here.lists_file.parent.mkdir(parents=True, exist_ok=True)
    here.lists_file.write_text('{"format": "woodcore-lists", "schema_version": "1.0", "tabs": {"tab_schema": {"order": "S-01"}}}\n', encoding="utf-8")
    text = here.lists_file.read_text(encoding="utf-8")
    said = []
    store = _store(here, said)
    assert store.tab("tab_schema") == ([], {})
    assert store.tab("tab_schema") == ([], {})
    assert len(said) == 1 and "lists.json" in said[0] and "order" in said[0], said
    assert not store.save("tab_schema", ["S-01"])
    assert len(said) == 2 and said[1] == said[0], "a drop refused did not say why in the same words"
    assert here.lists_file.read_text(encoding="utf-8") == text, "a file the engineer may have broken by hand was written over"
    here.lists_file.write_text("{ not json", encoding="utf-8")
    assert store.problem() and "lists.json" in store.problem()


def test_a_project_opened_read_only_writes_nothing():
    here = _copy("list_order_read_only")
    store = _store(here, read_only=True)
    assert not store.save("tab_schema", ["a"]) and not here.lists_file.exists()


def test_the_module_imports_without_qt():
    code = ("import sys; sys.modules['PySide6'] = None; sys.path[:0] = [r'%s']\n"
            "import list_order; print('ok')") % (conftest.ROOT / "calc")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr
