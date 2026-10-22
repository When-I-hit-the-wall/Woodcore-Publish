"""The «Moments polaires» tab's identity and its folders (v0.75, v0.76; docs/domain/connections.md §3.3quinquies, docs/ui/window.md §10quater).

v0.75 gave a calculation a name and a variant beside its connector. v0.76 removed the connector altogether -- a polar moment distributes forces over points and has no use for what fastens them -- and the variant with it: the identity is **Schéma · Nom · Description · ID**, the id made from the name (`connection.id_from_name`) and writable over. A 3.0 or 3.1 file is read as 4.0: its connector and variant dropped, its name the one it states or else its id, its id kept as it is -- so one whose id carries a variant reads as written over.

The left pane is a `GroupedList` of the calculations, filed by their own `group`, which only a drop sets. The empty folders of every editor tab are kept in settings.json, which conftest points at a file of the run's own.

⚠️ A drop writes source files and exports, so the tests below give the tab a temporary folder and stub its export: nothing of the project's `connections/` or `data/` is touched.
"""

import json
import os
import sys

import conftest
from conftest import ROOT, Skip
from domains import connection
import validation


def _source(**fields):
    source = {
        "schema_version": "4.0", "id": "Nordanschluss", "group": "", "name": "Nordanschluss",
        "label": "", "norm": connection.DEFAULT_NORM, "norm_ref": "", "schema": "SD_01",
        "reference": 1, "members": [{"name": "", "element": "E1"}, {"name": "", "element": "E2"}],
        "fasteners": ["C1", "C2"], "center": {"mode": "centroid"}, "directions": {"N": 0, "V": 90},
    }
    source.update(fields)
    return {k: v for k, v in source.items() if v is not None}


# --- the model -------------------------------------------------------------------------

def test_the_id_is_made_from_the_name():
    assert connection.id_from_name("Nordanschluss") == "Nordanschluss"
    assert connection.id_from_name("  Anschluss Nord  ") == "Anschluss_Nord"
    assert connection.id_from_name("Élément 2") == "Element_2", "an accent is decomposed, not dropped"
    assert connection.id_from_name("SD_01-8mm") == "SD_01-8mm"
    assert connection.id_from_name("-/ Träger") == "Trager"
    assert connection.id_from_name("") == ""
    for name in ("Anschluss Nord", "Élément 2", "x/y+z"):
        made = connection.id_from_name(name)
        assert connection.ID_PATTERN.match(made), (name, made)


def test_a_3_x_file_is_read_as_4_0_and_keeps_its_id():
    """The two files this project had: a 3.0 calculation of SD_01 whose id carries its variant. Nothing is written by reading one."""
    old = _source(schema_version="3.0", id="SD_01-8mm", name=None, connector="SD_01")
    new = connection.upgrade_source(old)
    assert "connector" in old, "the file's own dictionary is not changed"
    assert new["schema_version"] == "4.0" and new["id"] == "SD_01-8mm" and new["name"] == "SD_01-8mm"
    assert "connector" not in new and "variant" not in new
    assert list(new)[:3] == ["schema_version", "id", "name"], "the name sits after the id, where the window shows it"
    connection.check_source(new, "SD_01-8mm.json")
    stated = connection.upgrade_source(_source(schema_version="3.1", id="SD_01-8mm", name="SD_01", variant="8mm", connector="SD_01"))
    assert (stated["id"], stated["name"]) == ("SD_01-8mm", "SD_01"), "a stated name is kept, and the id with it"
    assert connection.id_from_name(stated["name"]) != stated["id"], "which the window reads as written over"


def test_a_connector_or_a_variant_left_in_a_4_0_file_is_refused():
    """A field left over would be read by nothing and believed by whoever opens the file."""
    for field, value in (("connector", "SD_01"), ("variant", "V1")):
        try:
            connection.check_source(_source(**{field: value}), "Nordanschluss.json")
        except validation.ValidationError as exc:
            assert field in str(exc)
            continue
        raise AssertionError(f"a 4.0 source carrying {field!r} was accepted")
    try:
        connection.check_source(_source(schema_version="3.1"), "Nordanschluss.json")
    except validation.ValidationError as exc:
        assert "upgrade_source" in str(exc)
    else:
        raise AssertionError("a 3.1 source was checked as it stands, without being upgraded")


def test_the_name_is_free_text_and_the_id_is_what_must_be_safe():
    connection.check_source(_source(name="Anschluss Nord / Stütze"), "Nordanschluss.json")
    try:
        connection.check_source(_source(id="a b/c"), "a b-c.json")
    except validation.ValidationError as exc:
        assert "id" in str(exc)
    else:
        raise AssertionError("an id that is no file name was accepted")


# --- the tab ---------------------------------------------------------------------------

_window = None


def _tab():
    global _window
    conftest.exported("connectors.json")
    path = str(ROOT / "calc" / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    import woodcore_gui
    QApplication.instance() or QApplication([])
    if _window is None:
        _window = woodcore_gui.MainWindow()
    tab = next(t for t in _window.tabs if type(t).__name__ == "PolarTab")
    tab.dirty = False   # a modal off-screen never comes back (tests/test_connectors.py's own warning)
    return tab


def test_the_identity_is_schema_name_description_id_and_nothing_else():
    """bc's request, relayed (v0.76): the Identité box holds Schéma · Nom · Description · ID, in that order, and the separate «Schéma» box is gone."""
    tab = _tab()
    from PySide6.QtWidgets import QFormLayout, QGroupBox
    tab.load_first()
    boxes = [b for b in tab.findChildren(QGroupBox)]
    identity = next(b for b in boxes if b.title() == tab.t("polar_identity"))
    form = identity.layout()
    assert isinstance(form, QFormLayout)
    fields = [form.itemAt(r, QFormLayout.ItemRole.FieldRole).widget() for r in range(form.rowCount())]
    assert fields == [tab.schema_combo, tab.schema_info, tab.name_edit, tab.label_edit, tab.id_edit]
    assert not any(b.title() in ("Schéma", "Schema") for b in boxes if b is not identity), "no «Schéma» box beside it"
    for gone in ("group_edit", "connector_combo", "variant_edit", "norm_edit", "norm_ref_edit"):
        assert not hasattr(tab, gone), gone
    tab.dirty = False


def test_the_id_follows_the_name_and_a_written_over_id_stays():
    tab = _tab()
    tab.load_first()
    tab.id_overridden = False
    tab.name_edit.setText("Anschluss Nord")
    assert tab.id_edit.text() == "Anschluss_Nord"
    tab.id_edit.setText("Nordanschluss")
    tab.on_id_edited("Nordanschluss")
    assert tab.id_overridden
    tab.name_edit.setText("Anschluss Süd")
    assert tab.id_edit.text() == "Nordanschluss", "an id written over stays written over"
    draft = tab.draft()
    assert (draft["id"], draft["name"]) == ("Nordanschluss", "Anschluss Süd")
    assert "connector" not in draft and "variant" not in draft
    connection.check_source(draft, "Nordanschluss.json")
    tab.id_edit.setText("Anschluss_Sud")
    tab.on_id_edited("Anschluss_Sud")
    assert not tab.id_overridden, "an id that agrees with its name is made from it again"
    tab.dirty = False
    tab.load_first()


def test_the_folder_and_the_reference_travel_unseen():
    """Neither is in the form any more; both are in the source, as the file has them."""
    tab = _tab()
    tab.current_id = None
    tab.fill(_source(id="SD_01-V1", group="Halle Nord", norm="SIA 265", norm_ref="6.2.1", schema_version="3.1", connector="SD_01", variant="V1", name="SD_01"))
    draft = tab.draft()
    assert (draft["group"], draft["norm"], draft["norm_ref"]) == ("Halle Nord", "SIA 265", "6.2.1")
    assert tab.id_overridden, "a 3.1 id carrying its variant reads as written over"
    tab.fill(_source(norm=""))
    assert tab.draft()["norm"] == connection.DEFAULT_NORM, "a reference is never saved empty"
    tab.dirty = False
    tab.load_first()


def test_new_opens_on_a_schema_with_every_marker_ticked():
    tab = _tab()
    schemas = tab.schemas()
    if not schemas:
        raise Skip("no detail schema in details/")
    tab.dirty = False
    tab.new()
    draft = tab.draft()
    detail = schemas.get(draft["schema"])
    assert detail is not None, draft["schema"]
    markers = [m["id"] for m in detail.get("connectors", [])]
    points = [a["id"] for a in detail.get("aids", []) if a.get("kind") == "point" and a.get("connector")]
    assert draft["fasteners"] == (markers or points), "every marker, or every point ticked «connecteur» on a schema that carries none"
    assert draft["id"] == connection.id_from_name(draft["name"])
    assert draft["id"].lower() not in {cid.lower() for cid in tab.taken_ids()}
    connection.check_source(draft, f"{draft['id']}.json")
    tab.dirty = False
    tab.load_first()


def test_the_list_is_the_calculations_in_their_folders():
    tab = _tab()
    tab.load_first()
    ids = [cid for _item, cid in tab.list.rows()]
    assert ids and set(ids) <= {cid for cid, *_rest in __import__("woodcore_gui").list_connections()} | {"<new>"}


def _sandbox(name):
    """A copy of the project whose connections/ is empty, for a test to put its own calculation in: (the scope that makes it current, its connections folder)."""
    import project
    copied = conftest.project_copy(name)
    for old in copied.connections_dir.glob("*.json"):
        old.unlink()
    return project.using(copied), copied.connections_dir


def test_a_drop_files_a_calculation_and_never_renames_it():
    tab = _tab()
    import woodcore_gui
    scope, folder = _sandbox("polar_drop")
    source = _source(id="SD_01-V1", name="SD_01-V1")
    (folder / "SD_01-V1.json").write_text(json.dumps(source, indent=2), encoding="utf-8")
    exported = []
    tab.export, original_export = (lambda cid, text: exported.append(cid) or True), tab.export
    scope.__enter__()
    try:
        tab.current_id = "SD_01-V1"
        tab.on_moved(["SD_01-V1"], "Halle Nord")
        written = json.loads((folder / "SD_01-V1.json").read_text(encoding="utf-8"))
        assert written["group"] == "Halle Nord" and written["id"] == "SD_01-V1"
        assert [p.name for p in folder.glob("*.json")] == ["SD_01-V1.json"], "a folder is a field, never a directory"
        assert exported == [""], "a drop exports the connections naming none of them (export_listed)"
        assert tab.form_group == "Halle Nord", "the draft being edited is refiled with its file"
        tab.on_moved(["SD_01-V1"], "")
        assert "group" not in json.loads((folder / "SD_01-V1.json").read_text(encoding="utf-8"))
    finally:
        scope.__exit__(None, None, None)
        tab.export = original_export
        tab.dirty = False
        tab.load_first()


def test_enregistrer_writes_the_file_and_clears_the_dot():
    """The engineer, v0.77: «cliquer sur enregistrer n'enlève pas le point blanc». It wrote nothing: save() still read the fastener table as the typed x/z of v0.31 -- a tick and a marker id since v0.74 -- found every row bad, and raised a KeyError on a message long gone, which pythonw swallowed. Planted back, this test fails on that KeyError."""
    tab = _tab()
    import woodcore_gui
    scope, folder = _sandbox("polar_save")
    source = _source(id="SD_02-10mm", name="SD_02-10mm", schema="SD_02", fasteners=["C1", "C2", "C3", "C4"])
    (folder / "SD_02-10mm.json").write_text(json.dumps(source, indent=2), encoding="utf-8")
    exported = []
    tab.export, original_export = (lambda cid, text: exported.append(cid) or True), tab.export
    refused = []
    tab.fail, original_fail = (lambda text: refused.append(text) or False), tab.fail   # a modal off-screen never comes back
    scope.__enter__()
    try:
        tab.load("SD_02-10mm")
        assert tab.table.rowCount() >= 1, "the schema's markers are listed, ticked: the table a stale reader took for x/z"
        tab.label_edit.setText("Velo Unterstand, geändert")
        assert tab.dirty
        assert tab.save() is True, refused
        written = json.loads((folder / "SD_02-10mm.json").read_text(encoding="utf-8"))
        assert written["label"] == "Velo Unterstand, geändert" and written["fasteners"] == ["C1", "C2", "C3", "C4"]
        assert exported == ["SD_02-10mm"]
        assert not tab.dirty
        index = tab.app.tab_widget.indexOf(tab)
        assert tab.app.tab_widget.tabIcon(index).cacheKey() == tab.app.dirty_mark(False).cacheKey(), "the tab's dot is gone"
    finally:
        scope.__exit__(None, None, None)
        tab.export = original_export
        tab.fail = original_fail
        tab.dirty = False
        tab.load_first()


def test_an_empty_folder_survives_the_window_being_closed():
    """The audit's finding: an empty folder was kept for the session only, though grouped_list.py's own docstring said settings.json. Every editor tab keeps them -- in the project file since v0.83 (`gui.empty_folders`, `katalog.empty_folders` until v0.96), where one project's empty folders no longer show in every other's."""
    tab = _tab()
    import woodcore_gui
    import project
    here = project.current()
    assert str(here.file).startswith(str(ROOT / "tests")), "the tests must never write the engineer's own project"
    tab.list._empty.append("Leer_75")
    tab.list.foldersChanged.emit()
    try:
        stored = json.loads(here.file.read_text(encoding="utf-8"))
        assert "Leer_75" in stored[project.GUI_KEY]["empty_folders"]["tab_polar"]
        assert "folders" not in json.loads(open(os.environ["WOODCORE_SETTINGS"], encoding="utf-8").read()), "an empty folder went into the user's settings"
        again = woodcore_gui.MainWindow()
        for key, name in (("tab_polar", "PolarTab"),):
            reopened = next(t for t in again.tabs if type(t).__name__ == name)
            assert "Leer_75" in reopened.empty_folders
            folders = [reopened.list.topLevelItem(i).text(0) for i in range(reopened.list.topLevelItemCount())]
            assert "Leer_75" in folders
        for key in ("tab_plan", "tab_statics", "tab_connections", "tab_schema"):
            again.save_folder_settings(key, ["Leer_" + key])
            assert woodcore_gui.MainWindow().folder_settings(key) == ["Leer_" + key]
    finally:
        window = tab.app
        for key in ("tab_polar", "tab_plan", "tab_statics", "tab_connections", "tab_schema"):
            window.save_folder_settings(key, [])
        tab.list._empty = [n for n in tab.list._empty if n != "Leer_75"]
        stored = json.loads(project.current().file.read_text(encoding="utf-8"))
        assert not any((stored.get(key) or {}).get("empty_folders") for key in (project.GUI_KEY, project.KATALOG_KEY)), "no empty folder left, and the project file says nothing of them"


def test_the_fastener_list_offers_the_schema_s_construction_points():
    """«Moments polaires» reads connector markers AND the points ticked «connecteur» in «Schémas» (v0.77): such a point is listed beside the markers, not as a lost id, and says what it is; an unticked one is not offered."""
    tab = _tab()
    detail = {"schema_version": "1.1", "id": "PTS", "label": "", "elements": [], "connectors": [],
              "aids": [{"id": "A1", "kind": "point", "x": -60, "z": 0, "connector": True},
                       {"id": "A2", "kind": "point", "x": 60, "z": 0, "connector": True},
                       {"id": "A3", "kind": "centre", "x": 0, "z": 0},
                       {"id": "A4", "kind": "point", "x": 0, "z": 90}],
              "dimensions": []}
    original = tab.detail
    tab.detail = lambda: detail
    try:
        tab.fill_markers(["A2"])
        rows = [tab.table.item(r, 1).text() for r in range(tab.table.rowCount())]
        assert rows == ["A1", "A2"], rows
        assert tab.ticked_markers() == ["A2"]
        assert tab.table.item(0, 1).toolTip() == tab.t("polar_kind_point")
    finally:
        tab.detail = original
        tab.dirty = False
        tab.load_first()
